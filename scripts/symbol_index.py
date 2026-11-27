#!/usr/bin/env python3
"""Incremental symbol index (functions, classes, types, imports).

Python uses the AST (confidence: high). JS/TS/Go/Rust/Java/C#/PHP/Ruby use regex
(confidence: medium) — they can miss or misread unusual syntax. Only files whose
fingerprint changed are re-parsed.

Usage:
  python symbol_index.py [ROOT]                 build/refresh, print summary
  python symbol_index.py [ROOT] --find NAME     where is NAME defined / imported
  python symbol_index.py [ROOT] --file PATH     outline of one file (no need to read it)
  python symbol_index.py [ROOT] --deps PATH     what PATH imports and who imports it
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import omnis_cache as oc  # noqa: E402

INDEX_VERSION = 2
REGEX_RULES = {
    (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte"): [
        ("function", r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)"),
        ("class", r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)"),
        ("function", r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*(?::[^=]+)?=>"),
        ("type", r"^\s*(?:export\s+)?(?:interface|type|enum)\s+([A-Za-z_$][\w$]*)"),
    ],
    (".go",): [("function", r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"), ("type", r"^type\s+([A-Za-z_]\w*)")],
    (".rs",): [("function", r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)"),
               ("type", r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)")],
    (".java", ".kt", ".cs"): [("class", r"^\s*(?:public|private|protected|internal|abstract|final|static|sealed|data|\s)*(?:class|interface|enum|record|object)\s+([A-Za-z_]\w*)"),
                              ("function", r"^\s+(?:public|private|protected|internal|static|async|override|virtual|final|suspend|fun|\s)+[\w<>\[\],?\s]*?\b([A-Za-z_]\w*)\s*\([^;]*$")],
    (".php",): [("class", r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait)\s+([A-Za-z_]\w*)"),
                ("function", r"^\s*(?:public|private|protected|static|\s)*function\s+([A-Za-z_]\w*)")],
    (".rb",): [("class", r"^\s*(?:class|module)\s+([A-Z]\w*)"), ("function", r"^\s*def\s+(?:self\.)?([a-z_]\w*[?!]?)")],
}
JS_IMPORT = re.compile(r"""(?:import\s[^'"]*?from\s*|import\s*\(\s*|require\s*\(\s*|^\s*import\s*)['"]([^'"]+)['"]""", re.M)
GO_IMPORT = re.compile(r'^\s*(?:import\s+)?"([^"]+)"', re.M)


def parse_python(text):
    tree = ast.parse(text)
    syms, imports = [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            syms.append([node.name, kind, node.lineno])
        elif isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append("." * node.level + (node.module or ""))
    return sorted(syms, key=lambda s: s[2]), imports


def parse_regex(text, rules, ext):
    syms = []
    compiled = [(k, re.compile(p)) for k, p in rules]
    skip = {"if", "for", "while", "switch", "catch", "return", "new", "else"}
    for i, line in enumerate(text.splitlines(), 1):
        for kind, rx in compiled:
            m = rx.match(line)
            if m and m.group(1) not in skip:
                syms.append([m.group(1), kind, i])
                break
    imports = JS_IMPORT.findall(text) if ext not in (".go",) else GO_IMPORT.findall(text)
    return syms, imports


def parse_file(root, rel):
    ext = Path(rel).suffix.lower()
    try:
        text = (Path(root) / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if ext == ".py":
        try:
            s, imp = parse_python(text)
            return {"symbols": s, "imports": imp, "confidence": "high"}
        except SyntaxError as e:
            return {"symbols": [], "imports": [], "confidence": "none", "error": f"syntax error line {e.lineno}"}
    for exts, rules in REGEX_RULES.items():
        if ext in exts:
            s, imp = parse_regex(text, rules, ext)
            return {"symbols": s, "imports": imp, "confidence": "medium"}
    return None


SUPPORTED = {".py"} | {e for exts in REGEX_RULES for e in exts}


def build(root):
    idx = oc.load(root, "symbols") or {}
    if idx.get("version") != INDEX_VERSION:
        idx = {"version": INDEX_VERSION, "files": {}}
    files = idx["files"]
    current = [f for f in oc.iter_files(root) if Path(f).suffix.lower() in SUPPORTED]
    stats = {"reparsed": 0, "reused": 0, "removed": 0}
    for rel in current:
        fp = oc.fingerprint(root, rel)
        old = files.get(rel)
        if old and old.get("fp") == fp:
            stats["reused"] += 1
            continue
        h = oc.file_hash(Path(root) / rel)
        if old and old.get("hash") == h:  # touched but unchanged
            old["fp"] = fp
            stats["reused"] += 1
            continue
        parsed = parse_file(root, rel)
        if parsed is not None:
            parsed.update(fp=fp, hash=h)
            files[rel] = parsed
            stats["reparsed"] += 1
    gone = set(files) - set(current)
    for rel in gone:
        del files[rel]
    stats["removed"] = len(gone)
    oc.save(root, "symbols", idx)
    return idx, stats


def find(idx, name):
    exact, partial = [], []
    for rel, info in idx["files"].items():
        for s, kind, line in info["symbols"]:
            if s == name:
                exact.append(f"{rel}:{line}  {kind} {s}  [{info['confidence']}]")
            elif name.lower() in s.lower():
                partial.append(f"{rel}:{line}  {kind} {s}")
    return exact, partial[:20]


def _resolve(importer, spec, files):
    """Best-effort map of an import string to a project file."""
    base = Path(importer).parent
    if spec.startswith("."):
        if Path(importer).suffix == ".py":
            dots = len(spec) - len(spec.lstrip("."))
            p = base
            for _ in range(dots - 1):
                p = p.parent
            cand = (p / spec.lstrip(".").replace(".", "/")).as_posix()
        else:
            cand = (base / spec).as_posix()
    else:
        cand = spec.replace(".", "/") if Path(importer).suffix == ".py" else spec
    cand = str(Path(cand).as_posix()).lstrip("./") if cand.startswith("./") else Path(cand).as_posix()
    for suffix in ("", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", "/index.ts", "/index.js", "/__init__.py"):
        if cand + suffix in files:
            return cand + suffix
    return None


def deps(idx, rel):
    files = idx["files"]
    if rel not in files:
        return None
    out_ = [(_resolve(rel, s, files) or f"(external) {s}") for s in files[rel]["imports"]]
    in_ = [f for f, info in files.items() if f != rel and any(_resolve(f, s, files) == rel for s in info["imports"])]
    return sorted(set(out_)), sorted(in_)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--find")
    ap.add_argument("--file")
    ap.add_argument("--deps")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    idx, st = build(a.root)
    if a.find:
        exact, partial = find(idx, a.find)
        print("\n".join(exact) or f"no exact definition of '{a.find}'")
        if partial:
            print("similar:\n  " + "\n  ".join(partial))
    elif a.file:
        rel = Path(a.file).as_posix()
        info = idx["files"].get(rel)
        if not info:
            print(f"{rel}: not indexed (unsupported type or excluded)")
            return 1
        print(f"{rel} [{info['confidence']}] imports: {', '.join(info['imports'][:15]) or '-'}")
        for s, kind, line in info["symbols"]:
            print(f"  {line:>5}  {kind:<8} {s}")
    elif a.deps:
        r = deps(idx, Path(a.deps).as_posix())
        if r is None:
            print("not indexed")
            return 1
        print("imports:\n  " + ("\n  ".join(r[0]) or "-"))
        print("imported by:\n  " + ("\n  ".join(r[1]) or "-"))
        print("(import resolution is best-effort; dynamic imports and path aliases are not resolved)")
    else:
        total = sum(len(i["symbols"]) for i in idx["files"].values())
        conf = {}
        for i in idx["files"].values():
            conf[i["confidence"]] = conf.get(i["confidence"], 0) + 1
        res = {"files": len(idx["files"]), "symbols": total, "confidence": conf, **st}
        print(json.dumps(res) if a.json else
              f"indexed {res['files']} files, {total} symbols | reparsed {st['reparsed']}, reused {st['reused']}, removed {st['removed']} | confidence {conf}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
