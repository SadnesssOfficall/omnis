#!/usr/bin/env python3
"""Recurring reminders (default every 5 hours) with quiet hours, max count and expiry.

The script stores reminder rules and decides whether a reminder should fire. It does
NOT schedule anything by itself; scheduling is done by one of:
  - Claude Code's CronCreate tool / /loop  (session-scoped: needs the session open)
  - /schedule cloud routines                (runs without your machine; needs account access)
  - the OS scheduler: `os-install` prints (or with --yes installs) a cron / Task Scheduler entry
Each fire should first call `should-fire ID`, which enforces quiet hours, pause, count and expiry.

Usage:
  python reminder_manager.py add [--every 5h] [--purpose usage-check] [--start HH:MM] [--tz Europe/Istanbul]
                                 [--quiet 23:00-08:00] [--max 20] [--until 2026-12-31]
  python reminder_manager.py list | pause ID | resume ID | remove ID | set ID --every 3h ...
  python reminder_manager.py should-fire ID        exit 0 = fire (and counts it), 1 = skip (prints why)
  python reminder_manager.py cron ID               cron expression + prompt for CronCreate / /loop
  python reminder_manager.py os-install ID [--yes] OS-level schedule (desktop notification / log)
  python reminder_manager.py os-remove ID [--yes]
"""
import argparse
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

PURPOSES = {
    "usage-check": "Check usage status (python {o}/usage_monitor.py status) and note whether the window changed.",
    "checkpoint": "Save a task checkpoint (python {o}/checkpoint.py save ...) with done/next steps.",
    "resume": "Show the latest checkpoint (python {o}/checkpoint.py resume) and continue the task.",
    "review": "Review progress against the plan and list what's left.",
    "break": "Remind the user to take a break.",
}
TAG = "# omnis-reminder:"


def store_path():
    p = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "omnis"
    p.mkdir(parents=True, exist_ok=True)
    return p / "reminders.json"


def load():
    try:
        return json.loads(store_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(d):
    p = store_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def parse_every(s):
    m = re.fullmatch(r"(\d+)\s*([mh])", s.strip().lower())
    if not m:
        raise ValueError("interval must look like 30m or 5h")
    n, unit = int(m.group(1)), m.group(2)
    minutes = n * 60 if unit == "h" else n
    if minutes < 10:
        raise ValueError("minimum interval is 10m (avoid spamming)")
    return minutes


def _tz(name):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name) if name else None
    except Exception:
        return None


def now_in(r, now=None):
    now = now or datetime.now().astimezone()
    tz = _tz(r.get("tz"))
    return now.astimezone(tz) if tz else now


def in_quiet(r, local):
    q = r.get("quiet")
    if not q:
        return False
    a, b = q.split("-")
    t = local.strftime("%H:%M")
    return (a <= t < b) if a <= b else (t >= a or t < b)


def check(r, now=None):
    """Return (fire: bool, reason)."""
    local = now_in(r, now)
    if r.get("paused"):
        return False, "paused"
    if r.get("until") and local.strftime("%Y-%m-%d") > r["until"]:
        return False, f"expired on {r['until']}"
    if r.get("max") and r.get("count", 0) >= r["max"]:
        return False, f"reached max count {r['max']}"
    if r.get("start_date") and local.strftime("%Y-%m-%d %H:%M") < r["start_date"]:
        return False, f"starts at {r['start_date']}"
    if in_quiet(r, local):
        return False, f"quiet hours {r['quiet']}"
    last = r.get("last_fired")
    if last and (local - datetime.fromisoformat(last)).total_seconds() < r["every_min"] * 60 * 0.8:
        return False, "fired recently (dedupe)"
    return True, "ok"


def cron_expr(r):
    m = r["every_min"]
    start_min = int(r.get("start", "00:00").split(":")[1]) if r.get("start") else 0
    if m % 60 == 0 and m < 24 * 60:
        h = m // 60
        start_h = int(r.get("start", "00:00").split(":")[0]) if r.get("start") else 0
        # explicit hour list when a start hour is set or h doesn't divide 24 (cron's */h always counts from 0)
        hours = sorted({(start_h + i * h) % 24 for i in range(24 // h + 1)}) if (24 % h or start_h) else None
        return f"{start_min} {','.join(map(str, hours)) if hours else '*/' + str(h)} * * *"
    if m < 60:
        return f"*/{m} * * * *"
    return f"{start_min} */{max(1, m // 60)} * * *"


def prompt_for(r, rid):
    o = Path(__file__).resolve().parent.as_posix()
    steps = PURPOSES.get(r["purpose"], r["purpose"]).format(o=o)
    return (f"OMNIS reminder {rid}. First run: python \"{o}/reminder_manager.py\" should-fire {rid} — "
            f"if it exits non-zero, stop silently. Otherwise: {steps} Keep the message to the user short.")


def os_entry(r, rid):
    o = Path(__file__).resolve().parent
    py = sys.executable
    if platform.system() == "Windows":
        hours = max(1, r["every_min"] // 60)
        action = f'"{py}" "{o / "reminder_manager.py"}" notify {rid}'
        return ["schtasks", "/Create", "/F", "/SC", "HOURLY", "/MO", str(hours), "/TN", f"OMNIS-{rid}", "/TR", action]
    return f'{cron_expr(r)} {shlex.quote(py)} {shlex.quote(str(o / "reminder_manager.py"))} notify {rid} {TAG}{rid}'


def notify(rid):
    d = load()
    r = d.get(rid)
    if not r:
        return 1
    fire, why = check(r)
    if not fire:
        return 1
    r["count"] = r.get("count", 0) + 1
    r["last_fired"] = now_in(r).isoformat()
    save(d)
    msg = f"OMNIS: {r['purpose']} reminder ({r['count']}{'/' + str(r['max']) if r.get('max') else ''})"
    log = store_path().parent / "reminders.log"
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {msg}\n")
    for cmd in (["notify-send", "OMNIS", msg], ["osascript", "-e", f'display notification "{msg}" with title "OMNIS"'],
                ["powershell", "-NoProfile", "-Command", f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')|Out-Null;[System.Windows.Forms.MessageBox]::Show('{msg}','OMNIS')"]):
        try:
            if subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0:
                break
        except (OSError, subprocess.TimeoutExpired):
            continue
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "list", "pause", "resume", "remove", "set", "should-fire", "cron", "os-install", "os-remove", "notify"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--every")
    ap.add_argument("--purpose")
    ap.add_argument("--start")
    ap.add_argument("--start-date", help="YYYY-MM-DD HH:MM")
    ap.add_argument("--tz")
    ap.add_argument("--quiet", help="HH:MM-HH:MM")
    ap.add_argument("--max", type=int)
    ap.add_argument("--until", help="YYYY-MM-DD")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    d = load()

    def need():
        if a.id not in d:
            sys.exit(f"no reminder '{a.id}' (see: list)")
        return d[a.id]

    def apply_opts(r):
        if a.every:
            r["every_min"] = parse_every(a.every)
        for k in ("purpose", "start", "tz", "quiet", "until", "start_date"):
            v = getattr(a, k)
            if v is not None:
                r[k] = v
        if a.max is not None:
            r["max"] = a.max
        if r.get("quiet") and not re.fullmatch(r"\d{2}:\d{2}-\d{2}:\d{2}", r["quiet"]):
            sys.exit("--quiet must be HH:MM-HH:MM")
        if r.get("tz") and not _tz(r["tz"]):
            sys.exit(f"unknown timezone {r['tz']}")

    if a.cmd == "add":
        rid = uuid.uuid4().hex[:6]
        r = {"every_min": 300, "purpose": "usage-check", "count": 0, "created": datetime.now().isoformat(timespec="minutes")}
        try:
            apply_opts(r)
        except ValueError as e:
            sys.exit(str(e))
        d[rid] = r
        save(d)
        print(f"reminder {rid} saved (every {r['every_min']} min, purpose {r['purpose']}). NOT scheduled yet — next: `cron {rid}` for CronCreate//loop, or `os-install {rid}`.")
    elif a.cmd == "list":
        for rid, r in d.items():
            fire, why = check(r)
            print(f"{rid}  every {r['every_min']}m  {r['purpose']:<12} fired {r.get('count', 0)}{'/' + str(r['max']) if r.get('max') else ''}"
                  f"  {'paused' if r.get('paused') else 'active'}  quiet={r.get('quiet') or '-'} until={r.get('until') or '-'}  now: {why}")
        if not d:
            print("no reminders")
    elif a.cmd in ("pause", "resume"):
        need()["paused"] = a.cmd == "pause"
        save(d)
        print(f"{a.id} {a.cmd}d")
    elif a.cmd == "remove":
        need()
        del d[a.id]
        save(d)
        print(f"{a.id} removed from OMNIS store (also delete its CronCreate job / OS entry if one exists)")
    elif a.cmd == "set":
        try:
            apply_opts(need())
        except ValueError as e:
            sys.exit(str(e))
        save(d)
        print(f"{a.id} updated")
    elif a.cmd == "should-fire":
        r = need()
        fire, why = check(r)
        if fire:
            r["count"] = r.get("count", 0) + 1
            r["last_fired"] = now_in(r).isoformat()
            save(d)
            print("fire")
            return 0
        print(f"skip: {why}")
        return 1
    elif a.cmd == "cron":
        r = need()
        print(json.dumps({"cron": cron_expr(r), "prompt": prompt_for(r, a.id), "recurring": True}, ensure_ascii=False, indent=1))
        if r.get("tz"):
            print(f"note: cron fields are in the scheduler's local time; reminder tz is {r['tz']}")
    elif a.cmd == "os-install":
        r = need()
        e = os_entry(r, a.id)
        if isinstance(e, list):
            print("will run: " + " ".join(e))
            if a.yes:
                p = subprocess.run(e, capture_output=True, text=True)
                print(p.stdout or p.stderr)
                return p.returncode
        else:
            print(f"crontab line: {e}")
            if a.yes:
                cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
                lines = [l for l in cur.splitlines() if not l.endswith(TAG + a.id)] + [e]
                p = subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, capture_output=True)
                ok = p.returncode == 0 and e in subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
                print("installed and confirmed in crontab" if ok else f"FAILED: {p.stderr}")
                return 0 if ok else 1
        if not a.yes:
            print("dry run — add --yes to install")
    elif a.cmd == "os-remove":
        if platform.system() == "Windows":
            cmd = ["schtasks", "/Delete", "/F", "/TN", f"OMNIS-{a.id}"]
            print("will run: " + " ".join(cmd))
            if a.yes:
                return subprocess.run(cmd).returncode
        else:
            cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            keep = [l for l in cur.splitlines() if not l.endswith(TAG + a.id)]
            print(f"will remove {len(cur.splitlines()) - len(keep)} crontab line(s)")
            if a.yes:
                subprocess.run(["crontab", "-"], input="\n".join(keep) + ("\n" if keep else ""), text=True)
    elif a.cmd == "notify":
        return notify(a.id)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
