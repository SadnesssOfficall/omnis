#!/usr/bin/env python3
"""Project memory + bug-pattern store in <project>/.omnis/memory/ (JSON lines, redacted).

Usage:
  python memory.py add TYPE "fact" [--source FILE] [--ttl DAYS]
       TYPE: architecture|decision|convention|bug|preference|environment|research|task
  python memory.py search "query" [--type TYPE]
  python memory.py inspect                      counts + the most recent entries
  python memory.py cleanup [--dry-run]          drop expired, stale-source and duplicate entries
  python memory.py bug add --signature "TypeError: x is undefined" --cause "..." --fix "..." [--files a,b] [--test t]
  python memory.py bug match "<error text>"     find previously solved failures like this one
  python memory.py --root DIR ...               operate on another project
"""
import argparse
import json
import re
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from security_scan import redact  # noqa: E402

TYPES = {"architecture", "decision", "convention", "bug", "preference", "environment", "research", "task"}
DEFAULT_TTL = {"research": 90, "task": 30, "environment": 60}
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}|\d{3,}")
NOISE = {"the", "and", "for", "with", "from", "this", "that", "line", "file", "error", "at", "in"}


def mem_file(root, name):
    d = Path(root) / ".omnis" / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}.jsonl"


def load(root, name):
    p = mem_file(root, name)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue  # skip a corrupt line instead of losing the store
    return out


def write_all(root, name, items):
    p = mem_file(root, name)
    tmp = p.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")
    tmp.replace(p)


def append(root, name, item):
    with mem_file(root, name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def tokens(text):
    # normalise identifiers in errors: numbers, hex and quoted values vary between occurrences
    text = re.sub(r"0x[0-9a-f]+|'[^']*'|\"[^\"]*\"", " ", text.lower())
    return {w for w in WORD.findall(text) if w not in NOISE}


def score(query_toks, text):
    t = tokens(text)
    return len(query_toks & t) / (len(query_toks) or 1)


def add(root, mtype, text, source=None, ttl=None):
    if mtype not in TYPES:
        raise ValueError(f"unknown type {mtype}; use one of {sorted(TYPES)}")
    text = redact(text.strip())
    items = load(root, "facts")
    for i in items:
        if i["type"] == mtype and i["text"].lower() == text.lower():
            i["updated"] = time.strftime("%Y-%m-%d")
            write_all(root, "facts", items)
            return i, False
    ttl = ttl if ttl is not None else DEFAULT_TTL.get(mtype)
    item = {"id": uuid.uuid4().hex[:8], "type": mtype, "text": text, "source": source,
            "created": time.strftime("%Y-%m-%d"), "expires": _days_from_now(ttl) if ttl else None}
    append(root, "facts", item)
    return item, True


def _days_from_now(days):
    return time.strftime("%Y-%m-%d", time.localtime(time.time() + days * 86400))


def search(root, query, mtype=None, limit=10):
    q = tokens(query)
    items = [i for i in load(root, "facts") if not mtype or i["type"] == mtype]
    ranked = sorted(((score(q, i["text"] + " " + (i.get("source") or "")), i) for i in items), key=lambda x: -x[0])
    return [i for s, i in ranked if s > 0][:limit]


def cleanup(root, dry=False):
    today = time.strftime("%Y-%m-%d")
    items, keep, removed, seen = load(root, "facts"), [], [], set()
    for i in items:
        key = (i["type"], i["text"].lower())
        reason = None
        if i.get("expires") and i["expires"] < today:
            reason = "expired"
        elif i.get("source") and not (Path(root) / i["source"]).exists():
            reason = f"source {i['source']} no longer exists"
        elif key in seen:
            reason = "duplicate"
        seen.add(key)
        (removed if reason else keep).append((i, reason))
    if not dry:
        write_all(root, "facts", [i for i, _ in keep])
    return [(i["id"], i["text"][:60], r) for i, r in removed]


def bug_add(root, signature, cause, fix, files=None, test=None):
    item = {"id": uuid.uuid4().hex[:8], "signature": redact(signature), "cause": redact(cause), "fix": redact(fix),
            "files": files or [], "test": test, "date": time.strftime("%Y-%m-%d")}
    append(root, "bugs", item)
    return item


def bug_match(root, error_text, limit=5):
    q = tokens(error_text)
    ranked = sorted(((score(q, b["signature"]), b) for b in load(root, "bugs")), key=lambda x: -x[0])
    return [(round(s, 2), b) for s, b in ranked if s >= 0.3][:limit]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd")
    a_add = sub.add_parser("add"); a_add.add_argument("type"); a_add.add_argument("text")
    a_add.add_argument("--source"); a_add.add_argument("--ttl", type=int)
    a_s = sub.add_parser("search"); a_s.add_argument("query"); a_s.add_argument("--type")
    sub.add_parser("inspect")
    a_c = sub.add_parser("cleanup"); a_c.add_argument("--dry-run", action="store_true")
    a_b = sub.add_parser("bug"); bsub = a_b.add_subparsers(dest="bcmd")
    b_add = bsub.add_parser("add")
    for f in ("--signature", "--cause", "--fix"):
        b_add.add_argument(f, required=True)
    b_add.add_argument("--files", default=""); b_add.add_argument("--test")
    b_m = bsub.add_parser("match"); b_m.add_argument("text")
    a = ap.parse_args(argv)
    r = a.root
    if a.cmd == "add":
        item, new = add(r, a.type, a.text, a.source, a.ttl)
        print(("added " if new else "already known, refreshed ") + item["id"])
    elif a.cmd == "search":
        for i in search(r, a.query, a.type):
            print(f"[{i['type']}] {i['text']}" + (f"  (src: {i['source']})" if i.get("source") else "") + f"  #{i['id']} {i['created']}")
    elif a.cmd == "inspect":
        facts, bugs = load(r, "facts"), load(r, "bugs")
        counts = {}
        for i in facts:
            counts[i["type"]] = counts.get(i["type"], 0) + 1
        print(f"facts: {len(facts)} {counts} | bug patterns: {len(bugs)}")
        for i in facts[-10:]:
            print(f"  [{i['type']}] {i['text'][:100]}")
    elif a.cmd == "cleanup":
        rem = cleanup(r, a.dry_run)
        print(f"{'would remove' if a.dry_run else 'removed'} {len(rem)}")
        for x in rem:
            print("  ", *x)
    elif a.cmd == "bug" and a.bcmd == "add":
        print("saved bug pattern " + bug_add(r, a.signature, a.cause, a.fix, [f for f in a.files.split(",") if f], a.test)["id"])
    elif a.cmd == "bug" and a.bcmd == "match":
        hits = bug_match(r, a.text)
        if not hits:
            print("no similar past failures")
        for s, b in hits:
            print(f"similarity {s} (token overlap, heuristic) | {b['date']}\n  signature: {b['signature']}\n  cause: {b['cause']}\n  fix: {b['fix']}\n  files: {', '.join(b['files']) or '-'}")
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
