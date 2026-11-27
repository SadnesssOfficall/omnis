#!/usr/bin/env python3
"""Shrink large command output while keeping what matters for diagnosis.

Usage:
  <command> 2>&1 | python output_filter.py [--max-lines 80] [--save DIR]
  python output_filter.py --run "npm test" [--max-lines 80]

Keeps errors, warnings, source locations, stack frames, summaries and the tail.
Drops ANSI codes, progress bars and repeated lines. Saves the full output to a file
whenever anything was dropped, so nothing is lost.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")
PROGRESS = re.compile(r"(\d{1,3}%\s*[|\[]|[█▓▒░#=]{8,}|^\s*[|/\\-]\s*$|\.{10,}|downloading .*\d+(\.\d+)?\s*[kmg]i?b)", re.I)
IMPORTANT = re.compile(
    r"(error|exception|traceback|fail(ed|ure)?|fatal|panic|assert|warn(ing)?|denied|refused|"
    r"not found|cannot|unable|undefined|segfault|timeout|timed out|errno|exit code|✗|✘|×)", re.I)
LOCATION = re.compile(r"(\b[\w./\\-]+\.(py|js|ts|tsx|jsx|go|rs|java|rb|php|cs|c|cpp|vue|svelte)[:(]\d+|File \".+\", line \d+|^\s+at .+\(.+:\d+:\d+\))")
BARE_PATH = re.compile(r"^\s*[\w.~:/\\-]+$")
SUMMARY = re.compile(r"(\d+ (passed|failed|tests?|errors?|warnings?|skipped)|tests? (passed|failed)|ran \d+ tests?|^ok\b|^FAILED|build (succeeded|failed)|compiled|done in|✓)", re.I)


def normalize(line):
    """Collapse numbers/hex so near-identical lines are treated as repeats."""
    return re.sub(r"0x[0-9a-f]+|\d+", "#", line.strip().lower())


def filter_text(text, max_lines=80, context=2, tail=15):
    raw = text.replace("\r\n", "\n")
    # carriage-return progress updates: keep only the last state of each line
    lines = [ANSI.sub("", l.split("\r")[-1]).rstrip() for l in raw.split("\n")]
    n = len(lines)
    if n <= max_lines:
        return "\n".join(lines).strip("\n"), {"total": n, "kept": n, "dropped": 0}

    score = [0] * n
    for i, l in enumerate(lines):
        if not l.strip() or PROGRESS.search(l):
            continue
        if BARE_PATH.match(l):  # a file listing like ".../errors.py" is not an error
            continue
        if IMPORTANT.search(l):
            score[i] = 3
        elif LOCATION.search(l):
            score[i] = 2
        elif SUMMARY.search(l):
            score[i] = 2
    keep = set()
    for i, s in enumerate(score):
        if s >= 2:
            keep.update(range(max(0, i - context), min(n, i + context + 1)))
    keep.update(range(max(0, n - tail), n))
    keep.update(range(min(5, n)))

    seen, out, prio, last = {}, [], [], -1
    for i in sorted(keep):
        l = lines[i]
        if not l.strip() or PROGRESS.search(l):
            continue
        k = normalize(l)
        seen[k] = seen.get(k, 0) + 1
        if seen[k] > 2 and score[i] < 3:
            continue
        if seen[k] > 5:
            continue
        if last != -1 and i - last > 1:
            out.append(f"  … [{i - last - 1} lines omitted]")
            prio.append(1)
        out.append(l)
        # context lines inherit their neighbour's score so a traceback stays together
        prio.append(max(score[max(0, i - context):i + context + 1]))
        last = i

    if len(out) > max_lines:
        # prefer the highest-signal lines but keep the original order
        # keep the highest-scoring lines (ties: the later ones, nearer the failure), original order
        idx = sorted(range(len(out)), key=lambda j: (-prio[j], -j))[:max_lines - 1]
        dropped_tail = len(out) - len(idx)
        out = [out[j] for j in sorted(idx)] + [f"  … [{dropped_tail} more filtered lines]"]
    return "\n".join(out), {"total": n, "kept": len(out), "dropped": n - len(out)}


def save_full(text, save_dir):
    d = Path(save_dir)
    d.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{hashlib.sha1(text.encode('utf-8', 'replace')).hexdigest()[:8]}.log"
    p = d / name
    p.write_text(text, encoding="utf-8", errors="replace")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-lines", type=int, default=80)
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--save", default=".omnis/logs", help="where full output is saved when trimmed")
    ap.add_argument("--run", help="run this shell command and filter its combined output")
    a = ap.parse_args(argv)

    code = None
    if a.run:
        p = subprocess.run(a.run, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text, code = p.stdout.decode("utf-8", "replace"), p.returncode
    else:
        text = sys.stdin.buffer.read().decode("utf-8", "replace")
    out, st = filter_text(text, a.max_lines, a.context)
    print(out)
    if st["dropped"]:
        path = save_full(text, a.save)
        print(f"\n[omnis-filter] {st['kept']}/{st['total']} lines shown; full output: {path}")
    if code is not None:
        print(f"[omnis-filter] exit code: {code}")
        return code
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
