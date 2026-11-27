#!/usr/bin/env python3
"""Task checkpoints for resuming after a limit, crash or new session.

Usage:
  python checkpoint.py save --task "..." [--done "a;b"] [--next "c;d"] [--notes "..."] [--root DIR]
  python checkpoint.py resume [--root DIR]     latest checkpoint + what changed in git since
  python checkpoint.py list [--root DIR]
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from security_scan import redact  # noqa: E402


def cp_dir(root):
    d = Path(root) / ".omnis" / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def git(root, *a):
    p = subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.stdout.strip() if p.returncode == 0 else None


def status_lines(root):
    # OMNIS's own state dir is not a user change
    return [l for l in (git(root, "status", "--short") or "").splitlines() if ".omnis/" not in l][:40]


def save(root, task, done=(), nxt=(), notes=""):
    data = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"), "task": redact(task),
        "done": [redact(x) for x in done], "next": [redact(x) for x in nxt], "notes": redact(notes),
        "git_head": git(root, "rev-parse", "--short", "HEAD"),
        "git_status": status_lines(root),
    }
    # microseconds keep names unique and lexically sortable even for saves in the same second
    p = cp_dir(root) / f"{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def latest(root):
    files = sorted(cp_dir(root).glob("*.json"))
    return (files[-1], json.loads(files[-1].read_text(encoding="utf-8"))) if files else (None, None)


def render_resume(root):
    p, d = latest(root)
    if not d:
        return "no checkpoint found"
    out = [f"RESUME — checkpoint {d['time']}", f"Task: {d['task']}"]
    if d["done"]:
        out.append("Done:\n" + "\n".join(f"  ✓ {x}" for x in d["done"]))
    if d["next"]:
        out.append("Next:\n" + "\n".join(f"  → {x}" for x in d["next"]))
    if d["notes"]:
        out.append(f"Notes: {d['notes']}")
    head = git(root, "rev-parse", "--short", "HEAD")
    if d.get("git_head") and head and head != d["git_head"]:
        out.append(f"Commits since checkpoint:\n{git(root, 'log', '--oneline', d['git_head'] + '..HEAD') or '  (unknown)'}")
    now = status_lines(root)
    if now != d.get("git_status"):
        out.append("Working tree changed since checkpoint:\n  " + ("\n  ".join(now[:20]) or "(clean)"))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["save", "resume", "list"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--task", default="")
    ap.add_argument("--done", default="")
    ap.add_argument("--next", default="")
    ap.add_argument("--notes", default="")
    a = ap.parse_args(argv)
    if a.cmd == "save":
        if not a.task:
            ap.error("--task is required")
        split = lambda s: [x.strip() for x in s.split(";") if x.strip()]
        print(f"checkpoint saved: {save(a.root, a.task, split(a.done), split(a.next), a.notes)}")
    elif a.cmd == "resume":
        print(render_resume(a.root))
    else:
        for f in sorted(cp_dir(a.root).glob("*.json"))[-15:]:
            d = json.loads(f.read_text(encoding="utf-8"))
            print(f"{d['time']}  {d['task'][:80]}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
