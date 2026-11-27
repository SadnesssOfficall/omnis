#!/usr/bin/env python3
"""Pick verification checks for the current git changes.

Usage: python verify_plan.py [ROOT] [--base REF] [--run]

Lists changed/untracked files, maps them to likely tests, and proposes commands from
the project map. With --run it executes them through output_filter and reports
VERIFIED / FAILED / NOT RUN honestly.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_scan  # noqa: E402
import output_filter  # noqa: E402

SECRET_HINTS = (".env", "id_rsa", ".pem", ".key", "credentials", "secret", "token")


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.stdout if p.returncode == 0 else None


def changed_files(root, base=None):
    if git(root, "rev-parse", "--is-inside-work-tree") is None:
        return None
    out = set()
    diff = git(root, "diff", "--name-only", base) if base else git(root, "diff", "--name-only", "HEAD")
    if diff is None:  # no commits yet
        diff = git(root, "diff", "--name-only", "--cached") or ""
    out |= {l for l in diff.splitlines() if l}
    out |= {l for l in (git(root, "ls-files", "--others", "--exclude-standard") or "").splitlines() if l}
    return sorted(out)


def related_tests(changed, all_tests):
    hits = set()
    for f in changed:
        stem = Path(f).stem.replace(".test", "").replace(".spec", "")
        if stem in ("__init__", "index"):
            continue
        for t in all_tests:
            if stem.lower() in Path(t).stem.lower():
                hits.add(t)
    return sorted(hits | {f for f in changed if f in all_tests})


def plan(root, base=None):
    m = project_scan.scan(root)
    changed = changed_files(root, base)
    all_tests = [t for t in _all_tests(root)]
    checks = []
    for k in ("typecheck", "lint", "test", "build"):
        if k in m["commands"]:
            checks.append((k, m["commands"][k]))
    risky = [f for f in (changed or []) if any(h in f.lower() for h in SECRET_HINTS)]
    return {"changed": changed, "related_tests": related_tests(changed or [], all_tests), "checks": checks, "secret_like_files": risky}


def _all_tests(root):
    from omnis_cache import iter_files
    return [f for f in iter_files(root) if "/test" in "/" + f.lower() or ".test." in f or ".spec." in f]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--base")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    p = plan(a.root, a.base)
    if p["changed"] is None:
        print("not a git repository: cannot detect changed files")
    else:
        print(f"changed files ({len(p['changed'])}): " + (", ".join(p["changed"][:30]) or "none"))
    print("related tests: " + (", ".join(p["related_tests"]) or "none found"))
    if p["secret_like_files"]:
        print("⚠ secret-like files in change set: " + ", ".join(p["secret_like_files"]))
    if not p["checks"]:
        print("no check commands detected — verification must be done manually")
        return 0
    print("proposed checks: " + "; ".join(f"{k}: `{c}`" for k, c in p["checks"]))
    if not a.run:
        return 0
    results = []
    for k, cmd in p["checks"]:
        if cmd.startswith("make ("):
            continue
        r = subprocess.run(cmd, shell=True, cwd=a.root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = r.stdout.decode("utf-8", "replace")
        results.append((k, cmd, r.returncode))
        if r.returncode != 0:
            out, _ = output_filter.filter_text(text, 40)
            print(f"\n--- {k} FAILED (exit {r.returncode}) ---\n{out}")
    print("\nVERIFIED: " + (", ".join(f"{k}" for k, _, c in results if c == 0) or "none"))
    print("FAILED: " + (", ".join(f"{k}" for k, _, c in results if c != 0) or "none"))
    return 1 if any(c for *_, c in results) else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
