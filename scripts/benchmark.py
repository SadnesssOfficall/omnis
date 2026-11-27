#!/usr/bin/env python3
"""Measure what OMNIS saves. Byte counts are exact; tokens are estimated as bytes/4 and labelled so.

Usage:
  python benchmark.py repo ROOT [--queries a,b,c]   orientation + symbol lookups: naive reads vs OMNIS output
  python benchmark.py filter LOGFILE                raw log vs filtered excerpt
  python benchmark.py sessions --split YYYY-MM-DD   real token usage per request before vs after a date
                                                    (e.g. the day OMNIS was installed) from local transcripts
"""
import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import omnis_cache as oc  # noqa: E402
import output_filter  # noqa: E402

ORIENT = re.compile(r"(^|/)(readme(\.\w+)?|package\.json|pyproject\.toml|requirements\.txt|go\.mod|cargo\.toml|makefile|dockerfile|docker-compose\.ya?ml|tsconfig\.json)$", re.I)


def est(b):
    return f"~{b // 4:,} tok (est.)"


def run_script(name, *args):
    t = time.perf_counter()
    p = subprocess.run([sys.executable, str(HERE / name), *args], capture_output=True)
    return p.stdout, time.perf_counter() - t


def bench_repo(root, queries):
    root = Path(root)
    files = list(oc.iter_files(root))
    orient = [f for f in files if ORIENT.search(f) and f.count("/") <= 2]
    naive_orient = sum((root / f).stat().st_size for f in orient)
    rows = []
    out, t1 = run_script("project_scan.py", str(root), "--refresh")
    _, t2 = run_script("project_scan.py", str(root))
    rows.append(("orientation", f"read {len(orient)} files: {naive_orient:,} B", f"project map: {len(out):,} B", naive_orient, len(out),
                 f"cold {t1:.2f}s / cached {t2:.2f}s"))
    _, ti = run_script("symbol_index.py", str(root))
    for q in queries:
        # naive: open every source file that mentions the name (what a grep-then-read pass costs)
        hits = []
        for f in files:
            try:
                if q in (root / f).read_text(encoding="utf-8", errors="ignore"):
                    hits.append(f)
            except OSError:
                pass
        naive = sum((root / f).stat().st_size for f in hits)
        o, _ = run_script("symbol_index.py", str(root), "--find", q)
        rows.append((f"find `{q}`", f"read {len(hits)} files: {naive:,} B", f"index answer: {len(o):,} B", naive, len(o), ""))
    lines = [f"Repo: {root} ({len(files)} files; index build {ti:.2f}s)", "",
             "| Task | Naive | OMNIS | Saved | Note |", "|---|---|---|---|---|"]
    for name, n, o, nb, ob, note in rows:
        saved = f"{(1 - ob / nb):.0%} ({est(nb - ob)})" if nb else "n/a"
        lines.append(f"| {name} | {n} | {o} | {saved} | {note} |")
    lines.append("\n'Naive' assumes whole-file reads; a careful agent reading line ranges would spend less, so treat savings as an upper bound.")
    return "\n".join(lines)


def bench_filter(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    out, st = output_filter.filter_text(text)
    return (f"{path}: {len(text.encode()):,} B / {st['total']} lines → {len(out.encode()):,} B / {st['kept']} lines "
            f"(saved {est(len(text.encode()) - len(out.encode()))})")


def bench_sessions(split):
    import usage_monitor as um
    cut = datetime.fromisoformat(split).replace(tzinfo=timezone.utc)
    evs, _ = um.load_events()
    before = [e for e in evs if e["time"] < cut and not e["sidechain"]]
    after = [e for e in evs if e["time"] >= cut and not e["sidechain"]]

    def stats(es):
        if not es:
            return "no data"
        t = um.total(es)
        ctx = (t["input"] + t["cache_write"] + t["cache_read"]) / len(es)
        sessions = len({e["session"] for e in es})
        return f"{len(es)} requests / {sessions} sessions, avg context {ctx:,.0f} tok/request, output {t['output'] / len(es):,.0f} tok/request, {t['all'] / sessions:,.0f} tok/session"
    return (f"Before {split}: {stats(before)}\nAfter  {split}: {stats(after)}\n"
            "These are real recorded tokens, but tasks differ between periods — compare like-for-like work before drawing conclusions.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["repo", "filter", "sessions"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("--queries", default="")
    ap.add_argument("--split")
    a = ap.parse_args(argv)
    if a.cmd == "repo":
        print(bench_repo(a.target or ".", [q for q in a.queries.split(",") if q]))
    elif a.cmd == "filter":
        print(bench_filter(a.target))
    else:
        if not a.split:
            ap.error("--split YYYY-MM-DD required")
        print(bench_sessions(a.split))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
