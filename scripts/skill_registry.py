#!/usr/bin/env python3
"""Skill registry: every skill Claude Code can see, with source, commit, date, audit status, category, enabled.

  python skill_registry.py [--json] [--dupes]

Built on skill_manager's lock file (.omnis-lock.json) plus the user skills dir and installed plugins.
Read-only. --dupes lists names that exist in more than one place (a plugin and the user dir, ...).
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE.parent / "config" / "skill-catalog.json"


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def categories():
    try:
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for preset, items in cat.get("presets", {}).items():
        if preset in ("all-safe", "engineering"):
            continue
        for n in items:
            if not n.startswith("@"):
                out.setdefault(n, preset)
    return out


def rows(home=None):
    home = Path(home or claude_home())
    cats = categories()
    out = []
    sd = home / "skills"
    try:
        lock = json.loads((sd / ".omnis-lock.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lock = {}
    if sd.is_dir():
        for p in sorted(sd.iterdir()):
            if not (p / "SKILL.md").is_file():
                continue
            l = lock.get(p.name)
            out.append({"name": p.name, "source": f"{l['repo']} (omnis)" if l else "user", "commit": (l or {}).get("commit", "")[:8],
                        "date": (l or {}).get("installed") or time.strftime("%Y-%m-%d", time.localtime((p / "SKILL.md").stat().st_mtime)),
                        "audit": f"{l.get('audit_verdict')} {l.get('audit_score')}" if l else "not audited",
                        "category": cats.get(p.name, "-"), "enabled": True, "where": "user"})
    try:
        settings = json.loads((home / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        settings = {}
    enabled = settings.get("enabledPlugins", {})
    try:
        installed = json.loads((home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8")).get("plugins", {})
    except (OSError, ValueError):
        installed = {}
    for pid, entries in installed.items():
        entry = entries[0] if isinstance(entries, list) and entries else (entries if isinstance(entries, dict) else {})
        path = Path(entry.get("installPath", ""))
        for sk in sorted(path.glob("**/skills/*/SKILL.md")) if path.is_dir() else []:
            out.append({"name": sk.parent.name, "source": f"plugin {pid}", "commit": str(entry.get("gitCommitSha", ""))[:8],
                        "date": str(entry.get("lastUpdated", entry.get("installedAt", "")))[:10], "audit": "plugin (not audited)",
                        "category": cats.get(sk.parent.name, "-"), "enabled": bool(enabled.get(pid)), "where": "plugin"})
    return out


def dupes(rs):
    by = {}
    for r in rs:
        by.setdefault(r["name"], []).append(r["source"])
    return {k: v for k, v in by.items() if len(v) > 1}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rs = rows()
    if "--json" in argv:
        print(json.dumps({"skills": rs, "duplicates": dupes(rs)}, indent=2))
        return 0
    if "--dupes" in argv:
        d = dupes(rs)
        print("\n".join(f"{k}: {', '.join(v)}" for k, v in d.items()) or "çakışma yok")
        return 0
    print(f"{'ad':34} {'kaynak':38} {'commit':8} {'tarih':16} {'denetim':20} {'kategori':10} açık")
    for r in rs:
        print(f"{r['name'][:34]:34} {r['source'][:38]:38} {r['commit']:8} {r['date'][:16]:16} {r['audit'][:20]:20} {r['category'][:10]:10} {'evet' if r['enabled'] else 'hayır'}")
    d = dupes(rs)
    if d:
        print("\nAynı adlı skill'ler: " + "; ".join(f"{k} ({', '.join(v)})" for k, v in d.items()))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
