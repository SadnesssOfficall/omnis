#!/usr/bin/env python3
"""Discover, audit, install, update and remove external Claude Code skills — safely.

Usage:
  python skill_manager.py presets                       list curated presets
  python skill_manager.py search QUERY [--github]       search the catalog (and optionally GitHub)
  python skill_manager.py plan PRESET|NAME...           fetch (pinned commit), audit, detect conflicts — installs nothing
  python skill_manager.py install PRESET|NAME... [--scope global|project] [--yes] [--allow-warn]
  python skill_manager.py list [--scope ...]            installed skills, OMNIS-managed ones marked
  python skill_manager.py conflicts [--scope ...]       same-name skills across global/project/plugins
  python skill_manager.py update [--latest] [--yes]     re-audit managed skills; --latest moves to the source's newest commit
  python skill_manager.py remove NAME [--scope ...] [--yes]

Nothing downloaded is ever executed. Files are fetched read-only from the pinned commit,
audited, then copied. Skills whose audit is `block` are never installed; `warn` needs --allow-warn.
Existing skills not installed by OMNIS are never overwritten. Every install is recorded in
<skills dir>/.omnis-lock.json (source, commit, audit score) for update and rollback.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import skill_audit  # noqa: E402

CATALOG = HERE.parent / "config" / "skill-catalog.json"
UA = {"User-Agent": "omnis-skill-manager", "Accept": "application/vnd.github+json"}


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def skills_dir(scope, project="."):
    return (claude_home() / "skills") if scope == "global" else Path(project) / ".claude" / "skills"


def cache_root():
    d = claude_home() / "omnis" / "skill-cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_catalog(path=CATALOG):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve(cat, targets):
    """Expand presets (with @preset references) into an ordered unique list of skill names."""
    out, stack = [], list(targets)

    def expand(t, depth=0):
        if depth > 5:
            raise ValueError("preset nesting too deep")
        if t.startswith("@"):
            t = t[1:]
        if t in cat["presets"]:
            for x in cat["presets"][t]:
                expand(x, depth + 1)
        elif t in cat["skills"]:
            if t not in out:
                out.append(t)
        else:
            raise ValueError(f"unknown preset or skill: {t}")

    for t in stack:
        expand(t)
    return out


def http_json(url):
    headers = dict(UA)
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def repo_tree(repo, commit):
    p = cache_root() / f"{repo.replace('/', '_')}_{commit}.tree.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    t = http_json(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1")
    p.write_text(json.dumps(t), encoding="utf-8")
    return t


def fetch_skill(repo, commit, name, subdir="skills"):
    """Download skills/<name>/ at the pinned commit into the cache (idempotent). Returns the local dir."""
    dest = cache_root() / f"{repo.replace('/', '_')}_{commit[:12]}" / name
    marker = dest / ".omnis-complete"
    if marker.exists():
        return dest
    tree = repo_tree(repo, commit)
    prefix = f"{subdir}/{name}/"
    blobs = [x for x in tree["tree"] if x["path"].startswith(prefix) and x["type"] == "blob"]
    if not blobs:
        raise FileNotFoundError(f"{prefix} not found in {repo}@{commit[:8]}")
    tmp = Path(tempfile.mkdtemp(prefix="omnis-fetch-", dir=cache_root()))
    try:
        for b in blobs:
            rel = b["path"][len(prefix):]
            if rel.startswith("/") or ".." in Path(rel).parts or b.get("mode") == "120000":
                raise ValueError(f"unsafe path in source: {b['path']}")  # traversal or symlink
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://raw.githubusercontent.com/{repo}/{commit}/{b['path']}"
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]}), timeout=60) as r:
                target.write_bytes(r.read())
        (tmp / ".omnis-complete").write_text(time.strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp.rename(dest)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    return dest


def license_of(skill_dir, source):
    for n in ("LICENSE.txt", "LICENSE", "LICENSE.md"):
        f = Path(skill_dir) / n
        if f.exists():
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            for key in ("Apache License", "MIT License", "BSD", "Proprietary", "source-available", "All rights reserved"):
                if key.lower() in head.lower():
                    return key
            return "custom (see LICENSE)"
    return source.get("license", "unknown")


def installed_skills(project="."):
    """name -> list of (where, path) across global, project and plugin skill dirs."""
    found = {}
    places = [("global", claude_home() / "skills"), ("project", Path(project) / ".claude" / "skills")]
    for where, base in places:
        if base.is_dir():
            for d in base.iterdir():
                if (d / "SKILL.md").is_file():
                    found.setdefault(d.name, []).append((where, d))
    plug = claude_home() / "plugins"
    if plug.is_dir():
        for sm in plug.glob("**/skills/*/SKILL.md"):
            found.setdefault(sm.parent.name, []).append(("plugin", sm.parent))
    return found


def lock_path(scope, project="."):
    return skills_dir(scope, project) / ".omnis-lock.json"


def load_lock(scope, project="."):
    try:
        return json.loads(lock_path(scope, project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_lock(scope, data, project="."):
    p = lock_path(scope, project)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")


def build_plan(cat, names, scope, project="."):
    lock = load_lock(scope, project)
    existing = installed_skills(project)
    target_base = skills_dir(scope, project)
    rows = []
    for n in names:
        meta = cat["skills"][n]
        src = cat["sources"][meta["source"]]
        row = {"name": n, "source": meta["source"], "repo": src["repo"], "commit": src["commit"], "category": meta["category"],
               "overlap": meta.get("overlap"), "action": None, "reason": ""}
        try:
            local = fetch_skill(src["repo"], src["commit"], n)
        except (urllib.error.URLError, FileNotFoundError, ValueError, OSError) as e:
            row.update(action="fail", reason=f"fetch failed: {e}")
            rows.append(row)
            continue
        a = skill_audit.audit(local)
        row.update(local=str(local), audit=a, license=license_of(local, src))
        here = target_base / n
        managed = lock.get(n)
        others = [w for w, p in existing.get(n, []) if Path(p).resolve() != here.resolve()]
        if a["verdict"] == "block":
            row.update(action="skip", reason="audit BLOCK")
        elif here.exists() and not managed:
            row.update(action="skip", reason="a skill with this name already exists and was not installed by OMNIS — not overwriting")
        elif managed and managed.get("commit") == src["commit"]:
            row.update(action="keep", reason="already installed at this commit")
        elif managed:
            row.update(action="update", reason=f"managed; {managed.get('commit', '')[:8]} → {src['commit'][:8]}")
        else:
            row.update(action="install", reason="")
        if others:
            row["reason"] += f" (note: same name also in {', '.join(others)})"
        rows.append(row)
    return rows


def render_plan(rows, scope, project="."):
    out = [f"Target: {skills_dir(scope, project)}  ({scope})", ""]
    for r in rows:
        a = r.get("audit")
        audit_s = f"{a['verdict']} {a['score']}/100, ~{a['context_overhead']['always_tokens_est']} tok always" if a else "-"
        out.append(f"  {r['action'].upper():<8} {r['name']:<32} [{audit_s}] {r.get('license', '')}  {r['reason']}")
        if a:
            for f in a["findings"]:
                if f["severity"] != "info":
                    out.append(f"           · {f['severity']}: {f['rule']} at {f['where']} — {f['why']}")
        if r.get("overlap"):
            out.append(f"           · OMNIS overlap: {r['overlap']}")
    total_ctx = sum(r["audit"]["context_overhead"]["always_tokens_est"] for r in rows if r.get("audit") and r["action"] in ("install", "update"))
    counts = {}
    for r in rows:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    out += ["", f"Summary: {counts}. Added always-loaded context ≈ {total_ctx} tokens (estimate from descriptions)."]
    return "\n".join(out)


def do_install(rows, scope, allow_warn=False, project="."):
    base = skills_dir(scope, project)
    base.mkdir(parents=True, exist_ok=True)
    lock = load_lock(scope, project)
    backups = claude_home() / "omnis" / "backups" / time.strftime("%Y%m%d-%H%M%S")
    results = []
    for r in rows:
        if r["action"] not in ("install", "update"):
            results.append((r["name"], r["action"], r["reason"]))
            continue
        if r["audit"]["verdict"] == "warn" and not allow_warn:
            results.append((r["name"], "skipped", "audit WARN — rerun with --allow-warn after reviewing the findings"))
            continue
        dest = base / r["name"]
        staging = base / f".{r['name']}.omnis-staging"
        try:
            if staging.exists():
                shutil.rmtree(staging)  # leftover from an interrupted install
            shutil.copytree(r["local"], staging, ignore=shutil.ignore_patterns(".omnis-complete"))
            if dest.exists():
                backups.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest), str(backups / r["name"]))
            staging.rename(dest)
            if not (dest / "SKILL.md").is_file():
                raise RuntimeError("SKILL.md missing after copy")
            lock[r["name"]] = {"repo": r["repo"], "commit": r["commit"], "source": r["source"], "license": r.get("license"),
                               "audit_score": r["audit"]["score"], "audit_verdict": r["audit"]["verdict"],
                               "installed": time.strftime("%Y-%m-%d %H:%M")}
            save_lock(scope, lock, project)  # after each skill, so an interruption leaves an accurate lock
            results.append((r["name"], "installed" if r["action"] == "install" else "updated", "verified SKILL.md present"))
        except Exception as e:  # noqa: BLE001 — report and continue with the rest
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            if not dest.exists() and (backups / r["name"]).exists():
                shutil.move(str(backups / r["name"]), str(dest))  # roll back
            results.append((r["name"], "failed", str(e)))
    return results, (backups if backups.exists() else None)


def remove(name, scope, project=".", yes=False):
    lock = load_lock(scope, project)
    if name not in lock:
        return f"'{name}' was not installed by OMNIS in {scope} scope — refusing to remove it"
    d = skills_dir(scope, project) / name
    if not yes:
        return f"would remove {d} (add --yes)"
    if d.exists():
        bk = claude_home() / "omnis" / "backups" / ("removed-" + time.strftime("%Y%m%d-%H%M%S"))
        bk.mkdir(parents=True, exist_ok=True)
        shutil.move(str(d), str(bk / name))
    del lock[name]
    save_lock(scope, lock, project)
    return f"removed {name} (backup kept under {claude_home() / 'omnis' / 'backups'})"


def github_search(query):
    q = urllib.request.quote(f"{query} claude skill SKILL.md in:name,description,readme")
    d = http_json(f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=10")
    return [(x["full_name"], x["stargazers_count"], (x.get("license") or {}).get("spdx_id"), x["pushed_at"][:10], x.get("archived"),
             (x.get("description") or "")[:80]) for x in d.get("items", [])]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["presets", "search", "plan", "install", "list", "conflicts", "update", "remove"])
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--scope", choices=["global", "project"], default="global")
    ap.add_argument("--project", default=".")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--allow-warn", action="store_true")
    ap.add_argument("--github", action="store_true")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--catalog", default=str(CATALOG))
    a = ap.parse_args(argv)
    cat = load_catalog(a.catalog)

    if a.cmd == "presets":
        for p, items in cat["presets"].items():
            print(f"{p:<12} {len(resolve(cat, [p])):>2} skills: {', '.join(items)}")
    elif a.cmd == "search":
        q = " ".join(a.targets).lower()
        for n, m in cat["skills"].items():
            if q in n or q in m["category"] or q in (m.get("note") or "").lower():
                print(f"  {n:<32} {m['category']:<12} {cat['sources'][m['source']]['repo']}")
        if a.github:
            print("\nGitHub (unvetted — not installable until added to the catalog and audited):")
            try:
                for row in github_search(q):
                    print("  {} ★{} {} pushed {} {}  {}".format(row[0], row[1], row[2], row[3], "ARCHIVED" if row[4] else "", row[5]))
            except urllib.error.URLError as e:
                print(f"  GitHub search failed: {e}")
    elif a.cmd in ("plan", "install"):
        if not a.targets:
            ap.error("give a preset or skill names (see: presets)")
        try:
            names = resolve(cat, a.targets)
        except ValueError as e:
            sys.exit(str(e))
        rows = build_plan(cat, names, a.scope, a.project)
        print(render_plan(rows, a.scope, a.project))
        if a.cmd == "install":
            if not a.yes:
                print("\nNothing installed. Review the plan above, then rerun with --yes.")
                return 0
            results, bk = do_install(rows, a.scope, a.allow_warn, a.project)
            print("\nResult:")
            for n, st, why in results:
                print(f"  {st:<10} {n}  {why}")
            if bk:
                print(f"Replaced versions backed up to {bk}")
            print("Restart Claude Code (or start a new session) to load new skills.")
            return 1 if any(st == "failed" for _, st, _ in results) else 0
    elif a.cmd == "list":
        lock = load_lock(a.scope, a.project)
        base = skills_dir(a.scope, a.project)
        names = sorted(d.name for d in base.iterdir() if (d / "SKILL.md").is_file()) if base.is_dir() else []
        print(f"{base}:")
        for n in names:
            l = lock.get(n)
            print(f"  {n:<34} " + (f"OMNIS-managed  {l['repo']}@{l['commit'][:8]}  audit {l['audit_score']}" if l else "user-installed"))
        if not names:
            print("  (none)")
    elif a.cmd == "conflicts":
        dup = {n: w for n, w in installed_skills(a.project).items() if len(w) > 1}
        for n, w in dup.items():
            print(f"  {n}: " + ", ".join(f"{where} ({p})" for where, p in w))
        print(f"{len(dup)} name conflicts" if dup else "no name conflicts")
    elif a.cmd == "update":
        lock = load_lock(a.scope, a.project)
        if not lock:
            print("no OMNIS-managed skills")
            return 0
        if a.latest:
            for key, src in cat["sources"].items():
                if any(v["source"] == key for v in lock.values()):
                    newest = http_json(f"https://api.github.com/repos/{src['repo']}/commits?per_page=1")[0]["sha"]
                    print(f"{src['repo']}: {src['commit'][:8]} → {newest[:8]}")
                    src["commit"] = newest
        rows = build_plan(cat, [n for n in lock if n in cat["skills"]], a.scope, a.project)
        print(render_plan(rows, a.scope, a.project))
        if a.yes:
            results, bk = do_install(rows, a.scope, a.allow_warn, a.project)
            for n, st, why in results:
                print(f"  {st:<10} {n}  {why}")
        else:
            print("\nNothing changed. Rerun with --yes to apply.")
    elif a.cmd == "remove":
        if not a.targets:
            ap.error("name required")
        for n in a.targets:
            print(remove(n, a.scope, a.project, a.yes))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
