#!/usr/bin/env python3
"""Install / update / uninstall OMNIS. Idempotent; backs up anything it replaces.

  python install.py                       global install to ~/.claude/skills/omnis (dry run)
  python install.py --yes                 do it
  python install.py --project DIR --yes   install into DIR/.claude/skills/omnis instead
  python install.py --with-hook --yes     also register the OMNIS safety hook (PreToolUse) in settings.json
  python install.py --uninstall --yes     remove the skill and the hook (backups kept)
  python install.py --verify              run the test suite against the installed copy
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
PAYLOAD = ["SKILL.md", "README.md", "CHANGELOG.md", "LICENSE", "scripts", "workflows", "engines", "config", "docs", "tests"]
HOOK_MARK = "omnis/scripts/guard.py"


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def backup_dir():
    d = claude_home() / "omnis" / "backups" / time.strftime("%Y%m%d-%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    return d


def hook_command(dest):
    py = "python" if os.name == "nt" else "python3"
    return f'{py} "{(dest / "scripts" / "guard.py").as_posix()}"'


def edit_settings(settings, dest, add, yes):
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except ValueError:
        print(f"! {settings} is not valid JSON — not touching it")
        return
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    kept = [g for g in pre if not any(HOOK_MARK in h.get("command", "").replace("\\", "/") for h in g.get("hooks", []))]
    if add:
        kept.append({"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": hook_command(dest), "timeout": 10}]})
    if kept == pre:
        print(f"= hook already {'present' if add else 'absent'} in {settings}")
        return
    data["hooks"]["PreToolUse"] = kept
    if not kept:
        del data["hooks"]["PreToolUse"]
    if not data["hooks"]:
        del data["hooks"]
    print(f"{'+' if add else '-'} safety hook {'into' if add else 'from'} {settings}")
    if yes:
        if settings.exists():
            shutil.copy2(settings, backup_dir() / settings.name)
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project")
    ap.add_argument("--with-hook", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    base = (Path(a.project) / ".claude") if a.project else claude_home()
    dest = base / "skills" / "omnis"
    settings = base / ("settings.local.json" if a.project else "settings.json")

    if a.verify:
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(dest / "tests"), "-q"])
        return p.returncode
    if a.uninstall:
        print(f"- remove {dest}")
        if a.yes and dest.exists():
            shutil.move(str(dest), str(backup_dir() / "omnis"))
        edit_settings(settings, dest, False, a.yes)
        print("done (backup kept)" if a.yes else "dry run — add --yes")
        return 0

    if dest.resolve() == SRC:
        sys.exit("source and destination are the same directory")
    action = "update" if dest.exists() else "install"
    print(f"{'~' if action == 'update' else '+'} {action} OMNIS → {dest}")
    if a.yes:
        staging = dest.parent / ".omnis.staging"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        for item in PAYLOAD:
            s = SRC / item
            if s.is_dir():
                shutil.copytree(s, staging / item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".omnis"))
            elif s.exists():
                shutil.copy2(s, staging / item)
        if dest.exists():
            shutil.move(str(dest), str(backup_dir() / "omnis"))
        staging.rename(dest)
    if a.with_hook:
        edit_settings(settings, dest, True, a.yes)
    if not a.yes:
        print("dry run — add --yes")
        return 0
    ok = (dest / "SKILL.md").is_file() and (dest / "scripts" / "omnis.py").is_file()
    print("verified: SKILL.md and scripts present" if ok else "! install incomplete")
    print("Start a new Claude Code session, then try: /omnis map")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
