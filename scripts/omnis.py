#!/usr/bin/env python3
"""OMNIS single entry point: python omnis.py <command> [args]

  map [ROOT] [--refresh]        project map                    (project_scan.py)
  find NAME | outline FILE | deps FILE                          (symbol_index.py)
  index [ROOT]                  build/refresh symbol index
  filter "<cmd>"                run a command, show only what matters (output_filter.py --run)
  verify [--run]                checks for current changes      (verify_plan.py)
  doctor                        environment diagnosis           (env_doctor.py)
  security scan|diff|classify   secrets & command risk          (security_scan.py)
  memory ...                    project memory / bug patterns   (memory.py)
  checkpoint save|resume|list   task checkpoints                (checkpoint.py)
  usage [status|report|setup|limits]                            (usage_monitor.py)
  reminder ...                  recurring reminders             (reminder_manager.py)
  skills ...                    external skill catalog/installer (skill_manager.py)
  audit PATH                    audit a skill directory         (skill_audit.py)
  benchmark ...                 measure savings                 (benchmark.py)
  clean [ROOT]                  delete this project's .omnis caches (keeps memory & checkpoints)
"""
import runpy
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUTES = {
    "map": ("project_scan.py", []), "index": ("symbol_index.py", []),
    "find": ("symbol_index.py", [".", "--find"]), "outline": ("symbol_index.py", [".", "--file"]),
    "deps": ("symbol_index.py", [".", "--deps"]), "filter": ("output_filter.py", ["--run"]),
    "verify": ("verify_plan.py", []), "doctor": ("env_doctor.py", []), "security": ("security_scan.py", []),
    "memory": ("memory.py", []), "checkpoint": ("checkpoint.py", []), "usage": ("usage_monitor.py", []),
    "reminder": ("reminder_manager.py", []), "skills": ("skill_manager.py", []), "audit": ("skill_audit.py", []),
    "benchmark": ("benchmark.py", []),
}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "clean":
        root = Path(rest[0] if rest else ".")
        removed = []
        for sub in ("cache", "logs"):
            d = root / ".omnis" / sub
            if d.is_dir():
                shutil.rmtree(d)
                removed.append(str(d))
        print("removed: " + (", ".join(removed) or "nothing"))
        return 0
    if cmd not in ROUTES:
        print(f"unknown command '{cmd}'\n{__doc__}")
        return 2
    script, prefix = ROUTES[cmd]
    if cmd == "filter" and rest:
        rest = [" ".join(rest)]
    sys.argv = [script, *prefix, *rest]
    sys.path.insert(0, str(HERE))
    try:
        runpy.run_path(str(HERE / script), run_name="__main__")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
