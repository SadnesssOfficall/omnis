#!/usr/bin/env python3
"""Compact project map: languages, frameworks, package managers, scripts, tests, entry points.

Usage: python project_scan.py [ROOT] [--json] [--refresh]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import omnis_cache as oc  # noqa: E402

EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".cs": "C#", ".php": "PHP", ".rb": "Ruby", ".swift": "Swift", ".c": "C", ".h": "C", ".cpp": "C++",
    ".vue": "Vue", ".svelte": "Svelte", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell", ".dart": "Dart",
}
MANIFESTS = {
    "package.json": "npm", "pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "bun.lockb": "bun",
    "requirements.txt": "pip", "pyproject.toml": "python-project", "poetry.lock": "poetry", "uv.lock": "uv",
    "Pipfile": "pipenv", "go.mod": "go", "Cargo.toml": "cargo", "composer.json": "composer",
    "Gemfile": "bundler", "pom.xml": "maven", "build.gradle": "gradle", "pubspec.yaml": "dart",
}
JS_FRAMEWORKS = {
    "next": "Next.js", "react": "React", "vue": "Vue", "svelte": "Svelte", "@angular/core": "Angular",
    "express": "Express", "fastify": "Fastify", "@nestjs/core": "NestJS", "vite": "Vite",
    "prisma": "Prisma", "drizzle-orm": "Drizzle", "mongoose": "Mongoose", "jest": "Jest",
    "vitest": "Vitest", "@playwright/test": "Playwright", "tailwindcss": "Tailwind", "electron": "Electron",
}
PY_FRAMEWORKS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "sqlalchemy": "SQLAlchemy",
    "pytest": "pytest", "pydantic": "Pydantic", "celery": "Celery",
}
INFRA = {
    "Dockerfile": "Docker", "docker-compose.yml": "Docker Compose", "compose.yaml": "Docker Compose",
    ".github/workflows": "GitHub Actions", "Caddyfile": "Caddy", "nginx.conf": "nginx",
    "vercel.json": "Vercel", "netlify.toml": "Netlify", "wrangler.toml": "Cloudflare Workers",
}
ENTRY_NAMES = {"main.py", "app.py", "manage.py", "server.js", "index.js", "main.ts", "index.ts",
               "server.ts", "main.go", "main.rs", "Program.cs", "wsgi.py", "asgi.py"}


def _read(root, rel):
    try:
        return (Path(root) / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def scan(root):
    files = list(oc.iter_files(root))
    langs = Counter()
    for f in files:
        lang = EXT_LANG.get(Path(f).suffix.lower())
        if lang:
            langs[lang] += 1
    names = set(files)
    # manifests at the root or up to two levels down (monorepos, nested apps)
    manifests = [f for f in files if Path(f).name in MANIFESTS and f.count("/") <= 2]
    pkg = sorted({MANIFESTS[Path(f).name] for f in manifests})
    pkg_json = min((f for f in manifests if f.endswith("package.json")), key=lambda f: f.count("/"), default=None)
    frameworks, scripts = set(), {}
    if pkg_json:
        try:
            pj = json.loads(_read(root, pkg_json))
            deps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
            frameworks |= {v for k, v in JS_FRAMEWORKS.items() if k in deps}
            scripts = pj.get("scripts", {})
        except ValueError:
            frameworks.add("(package.json unparseable)")
    py_text = "".join(_read(root, f) for f in manifests if Path(f).name in ("requirements.txt", "pyproject.toml")).lower()
    frameworks |= {v for k, v in PY_FRAMEWORKS.items() if k in py_text}
    infra = sorted({v for k, v in INFRA.items() if k in names or any(f.startswith(k + "/") for f in files)})
    tests = [f for f in files if "/test" in "/" + f.lower() or ".test." in f or ".spec." in f or f.endswith("_test.go")]
    entries = [f for f in files if Path(f).name in ENTRY_NAMES and f.count("/") <= 2]
    configs = [f for f in files if f.count("/") == 0 and (f.startswith(".env") or f.endswith((".toml", ".yaml", ".yml", ".ini", ".cfg")) or "config" in f.lower())]
    docs = [f for f in files if f.lower().endswith(".md") and f.count("/") <= 1]
    commands = _commands({Path(f).name for f in manifests} | names, scripts, pkg)
    if pkg_json and "/" in pkg_json:
        commands = {k: f"(cd {Path(pkg_json).parent.as_posix()}) {v}" for k, v in commands.items()}
    return {
        "root": str(Path(root).resolve()),
        "file_count": len(files),
        "languages": dict(langs.most_common(8)),
        "package_managers": pkg,
        "frameworks": sorted(frameworks),
        "infrastructure": infra,
        "commands": commands,
        "entry_points": entries[:15],
        "tests": {"count": len(tests), "sample": tests[:10]},
        # .env files are listed by name only; their contents are never read
        "config_files": configs[:20],
        "docs": docs[:15],
        "top_dirs": _top_dirs(files),
    }


def _commands(names, scripts, pkg):
    cmds = {}
    runner = "pnpm" if "pnpm" in pkg else "yarn" if "yarn" in pkg else "bun" if "bun" in pkg else "npm run"
    for k in ("dev", "start", "build", "test", "lint", "typecheck", "format"):
        if k in scripts:
            cmds[k] = f"{runner} {k}"
    if any(n in names for n in ("pyproject.toml", "requirements.txt", "setup.py")):
        cmds.setdefault("test", "pytest" if "pytest" in "".join(names) or "tests" in {n.split("/")[0] for n in names} else "python -m unittest")
    if "go.mod" in names:
        cmds.setdefault("test", "go test ./...")
        cmds.setdefault("build", "go build ./...")
    if "Cargo.toml" in names:
        cmds.setdefault("test", "cargo test")
        cmds.setdefault("build", "cargo build")
    if "Makefile" in names:
        cmds["make"] = "make (see Makefile targets)"
    return cmds


def _top_dirs(files):
    c = Counter(f.split("/")[0] for f in files if "/" in f)
    return dict(c.most_common(12))


def scan_cached(root, refresh=False):
    """Re-scan only if the set of files or any manifest changed."""
    files = list(oc.iter_files(root))
    key_files = [f for f in files if Path(f).name in MANIFESTS or f.count("/") == 0]
    sig = oc.hashlib.sha1(("\n".join(files) + "\n".join(oc.fingerprint(root, f) for f in key_files)).encode()).hexdigest()
    cached = oc.load(root, "project_map")
    if cached and not refresh and cached.get("_sig") == sig:
        cached["_cache"] = "hit"
        return cached
    data = scan(root)
    data["_sig"] = sig
    oc.save(root, "project_map", data)
    data["_cache"] = "miss"
    return data


def render(m):
    out = [f"# Project map: {m['root']}  ({m['file_count']} files, cache {m.get('_cache', '-')})"]
    def line(label, v):
        if v:
            out.append(f"- {label}: {v if isinstance(v, str) else ', '.join(f'{k} ({c})' if isinstance(v, dict) else str(k) for k, c in (v.items() if isinstance(v, dict) else ((x, None) for x in v)))}")
    line("Languages", m["languages"])
    line("Package managers", m["package_managers"])
    line("Frameworks/libs", m["frameworks"])
    line("Infra", m["infrastructure"])
    if m["commands"]:
        out.append("- Commands: " + "; ".join(f"{k} → `{v}`" for k, v in m["commands"].items()))
    line("Entry points", m["entry_points"])
    out.append(f"- Tests: {m['tests']['count']} files" + (f" (e.g. {', '.join(m['tests']['sample'][:4])})" if m["tests"]["count"] else ""))
    line("Config", m["config_files"])
    line("Docs", m["docs"])
    line("Top dirs", m["top_dirs"])
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    m = scan_cached(a.root, a.refresh)
    print(json.dumps(m, ensure_ascii=False, indent=1) if a.json else render(m))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
