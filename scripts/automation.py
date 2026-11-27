#!/usr/bin/env python3
"""OMNIS automation manager. Recurring, read-only jobs run by the OS scheduler (Windows Task Scheduler;
cron line printed elsewhere). Claude Code does NOT need to be open: these jobs are plain scripts.

  automation.py status
  automation.py add KIND [--every 5h] [--repo DIR ...]     KIND: skill-update-check | dependency-advisories | repo-health
  automation.py pause ID | resume ID | remove ID
  automation.py config ID --every 12h [--repo DIR ...]
  automation.py run ID                                      run now (what the scheduler calls)

Intervals: 1h 2h 3h 5h (default) 8h 12h 24h, or custom like 30m / 6h.
Safety: jobs only read, report and notify. They never delete, deploy, push, buy or message anyone.
Reports: ~/.omnis/reports/. A Windows toast summarises each run.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
KINDS = ("skill-update-check", "dependency-advisories", "repo-health")


def home():
    return Path(os.environ.get("OMNIS_HOME") or Path.home() / ".omnis")


def store():
    return home() / "automation.json"


def load():
    try:
        return json.loads(store().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(d):
    store().parent.mkdir(parents=True, exist_ok=True)
    store().write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_every(s):
    m = re.fullmatch(r"(\d+)\s*([mh])", (s or "5h").strip().lower())
    if not m:
        raise ValueError(f"bad interval '{s}' (use e.g. 30m, 5h, 24h)")
    minutes = int(m.group(1)) * (60 if m.group(2) == "h" else 1)
    if not 15 <= minutes <= 7 * 24 * 60:
        raise ValueError("interval must be between 15m and 168h")
    return minutes


def schedule_args(minutes):
    if minutes % 1440 == 0:
        return ["/SC", "DAILY", "/MO", str(minutes // 1440)]
    if minutes % 60 == 0 and minutes // 60 <= 23:
        return ["/SC", "HOURLY", "/MO", str(minutes // 60)]
    return ["/SC", "MINUTE", "/MO", str(minutes)]


def task_name(tid):
    return f"OMNIS\\{tid}"


def _pyw():
    p = Path(sys.executable)
    w = p.with_name("pythonw.exe")
    return str(w if w.exists() else p)


def scheduler(action, tid, minutes=None, dry=False):
    """Register / enable / disable / delete the OS task. Returns (ok, message)."""
    if os.name != "nt":
        line = f"*/{minutes} * * * *" if minutes and minutes < 60 else f"0 */{(minutes or 300) // 60} * * *"
        return False, f"not Windows: add to crontab yourself → {line} {sys.executable} {HERE / 'automation.py'} run {tid}"
    if action == "create":
        tr = f'"{_pyw()}" "{HERE / "automation.py"}" run {tid}'
        cmd = ["schtasks", "/Create", "/TN", task_name(tid), "/TR", tr, *schedule_args(minutes), "/F"]
    elif action == "delete":
        cmd = ["schtasks", "/Delete", "/TN", task_name(tid), "/F"]
    else:
        cmd = ["schtasks", "/Change", "/TN", task_name(tid), "/ENABLE" if action == "enable" else "/DISABLE"]
    if dry:
        return True, " ".join(cmd)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="mbcs" if os.name == "nt" else "utf-8", errors="replace")
    return p.returncode == 0, (p.stdout or p.stderr).strip()


# ------------------------------------------------------------------ jobs (read-only)

def _run(cmd, cwd=None, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           shell=isinstance(cmd, str))
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def job_skill_update_check(task):
    code, out = _run([sys.executable, str(HERE / "skill_manager.py"), "update"], timeout=600)  # no --yes → report only
    pending = len(re.findall(r"^\s*(UPDATE|INSTALL)\b", out, re.M))
    return (f"{pending} skill güncellemesi bekliyor" if pending else "skill'ler güncel"), out


def job_dependency_advisories(task):
    lines, total = [], 0
    for repo in task.get("repos") or []:
        r = Path(repo)
        if (r / "package-lock.json").is_file():
            _, out = _run("npm audit --json --omit=dev", cwd=r, timeout=300)
            try:
                v = json.loads(out[out.index("{"):]).get("metadata", {}).get("vulnerabilities", {})
                n = sum(v.get(k, 0) for k in ("high", "critical"))
                total += n
                lines.append(f"{r.name}: high/critical={n} (toplam {sum(v.values()) if v else 0})")
            except (ValueError, AttributeError):
                lines.append(f"{r.name}: npm audit okunamadı")
        elif (r / "pnpm-lock.yaml").is_file():
            _, out = _run("pnpm audit --json --prod", cwd=r, timeout=300)
            n = len(re.findall(r'"severity":\s*"(high|critical)"', out))
            total += n
            lines.append(f"{r.name}: pnpm high/critical≈{n}")
        else:
            lines.append(f"{r.name}: desteklenen kilit dosyası yok")
    if not lines:
        return "izlenen repo yok (--repo ekleyin)", ""
    return (f"{total} yüksek/kritik açık" if total else "ciddi açık yok"), "\n".join(lines)


def job_repo_health(task):
    import security_scan
    lines, warn = [], 0
    for repo in task.get("repos") or []:
        r = Path(repo)
        if not (r / ".git").exists():
            lines.append(f"{r.name}: git deposu değil")
            continue
        _, st = _run(["git", "status", "--porcelain=v1", "-b"], cwd=r)
        dirty = [l for l in st.splitlines() if l and not l.startswith("##")]
        head = next((l for l in st.splitlines() if l.startswith("##")), "")
        _, age = _run(["git", "log", "-1", "--format=%cr"], cwd=r)
        secrets = security_scan.scan_diff(str(r)) or {}
        warn += bool(dirty) + bool(secrets) + ("ahead" in head)
        lines.append(f"{r.name}: {len(dirty)} değişmiş dosya, {head[3:]}, son commit {age.strip()}, diff'te gizli bilgi: {len(secrets)}")
    if not lines:
        return "izlenen repo yok (--repo ekleyin)", ""
    return (f"{warn} dikkat noktası" if warn else "repolar temiz"), "\n".join(lines)


JOBS = {"skill-update-check": job_skill_update_check, "dependency-advisories": job_dependency_advisories, "repo-health": job_repo_health}


def run(tid, notify=True):
    d = load()
    t = d.get(tid)
    if not t:
        print(f"no task {tid}")
        return 2
    if t.get("paused"):
        return 0
    summary, detail = JOBS[t["kind"]](t)
    rep = home() / "reports" / f"{tid}-{time.strftime('%Y%m%d-%H%M%S')}.txt"
    rep.parent.mkdir(parents=True, exist_ok=True)
    import security_scan
    rep.write_text(security_scan.redact(f"{t['kind']} — {summary}\n\n{detail}"), encoding="utf-8")
    t.update(last_run=time.strftime("%Y-%m-%d %H:%M"), last_result=summary, last_report=str(rep))
    save(d)
    if notify:
        try:
            import toast
            toast.show(f"OMNIS · {t['kind']}", summary)
        except Exception:  # noqa: BLE001
            pass
    print(f"{t['kind']}: {summary}\nrapor: {rep}")
    return 0


def status():
    d = load()
    if not d:
        print("Otomasyon yok. Örnek: automation add repo-health --every 5h --repo D:/proje")
        return 0
    for tid, t in d.items():
        every = t["minutes"] // 60 if t["minutes"] % 60 == 0 else t["minutes"]
        unit = "sa" if t["minutes"] % 60 == 0 else "dk"
        print(f"{tid}  {t['kind']:22} her {every} {unit}  {'DURAKLATILDI' if t.get('paused') else 'aktif':12} "
              f"son: {t.get('last_run', '-')} → {t.get('last_result', '-')}")
        for r in t.get("repos") or []:
            print(f"      repo: {r}")
    print("Not: bu işler Windows Görev Zamanlayıcı'da çalışır, Claude Code açık olmasa da.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["status", "add", "pause", "resume", "remove", "config", "run"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--every")
    ap.add_argument("--repo", action="append")
    ap.add_argument("--no-schedule", action="store_true", help="don't touch the OS scheduler (tests)")
    ap.add_argument("--no-notify", action="store_true")
    a = ap.parse_args(argv)
    d = load()
    if a.cmd == "status":
        return status()
    if a.cmd == "add":
        if a.arg not in KINDS:
            print(f"KIND must be one of: {', '.join(KINDS)}")
            return 2
        minutes = parse_every(a.every)
        tid = f"{a.arg}-{len(d) + 1}"
        while tid in d:
            tid += "x"
        d[tid] = {"kind": a.arg, "minutes": minutes, "repos": [str(Path(r).resolve()) for r in a.repo or []], "paused": False}
        save(d)
        ok, msg = (True, "skipped") if a.no_schedule else scheduler("create", tid, minutes)
        print(f"+ {tid} her {minutes} dk. Zamanlayıcı: {'tamam' if ok else 'HATA'} {msg if not ok else ''}".rstrip())
        return 0 if ok else 1
    tid = a.arg
    if tid not in d:
        print(f"no task {tid}")
        return 2
    if a.cmd == "run":
        return run(tid, notify=not a.no_notify)
    if a.cmd in ("pause", "resume"):
        d[tid]["paused"] = a.cmd == "pause"
        save(d)
        ok, msg = (True, "") if a.no_schedule else scheduler("disable" if a.cmd == "pause" else "enable", tid)
    elif a.cmd == "remove":
        del d[tid]
        save(d)
        ok, msg = (True, "") if a.no_schedule else scheduler("delete", tid)
    else:  # config
        if a.every:
            d[tid]["minutes"] = parse_every(a.every)
        if a.repo:
            d[tid]["repos"] = [str(Path(r).resolve()) for r in a.repo]
        save(d)
        ok, msg = (True, "") if a.no_schedule else scheduler("create", tid, d[tid]["minutes"])
    print(f"{a.cmd} {tid}: {'tamam' if ok else 'HATA ' + msg}")
    return 0 if ok else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
