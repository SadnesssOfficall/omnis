#!/usr/bin/env python3
"""Project adaptation: detect the stack (incl. Minecraft, FiveM, Roblox, Discord bots, desktop, SaaS) and
recommend only the skills, agents and commands that fit it. Read-only; never installs anything.

  python project_adapt.py [ROOT] [--json]
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SKIP = {".git", "node_modules", ".venv", "venv", "dist", "build", "target", ".next", "out", "__pycache__", ".omnis"}


def _files(root, limit=4000):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP and not d.startswith(".")]
        for f in fns:
            out.append(os.path.relpath(os.path.join(dp, f), root).replace("\\", "/"))
            if len(out) >= limit:
                return out
    return out


def _read(root, rel, n=200_000):
    try:
        return (Path(root) / rel).read_text(encoding="utf-8", errors="replace")[:n]
    except OSError:
        return ""


def detect(root):
    root = Path(root)
    files = _files(root)
    names = {Path(f).name.lower() for f in files}
    exts = {Path(f).suffix.lower() for f in files}
    dl = []
    for f in [f for f in files if Path(f).name == "package.json"][:40]:
        try:
            j = json.loads(_read(root, f))
            dl += list({**j.get("dependencies", {}), **j.get("devDependencies", {})}.keys())
        except ValueError:
            pass
    deps = " ".join(sorted(set(dl)))
    py = " ".join(_read(root, f, 50_000) for f in files if Path(f).name in ("requirements.txt", "pyproject.toml"))
    build = " ".join(_read(root, f, 50_000) for f in files if Path(f).name in ("pom.xml", "build.gradle", "build.gradle.kts"))[:400_000]
    csproj = " ".join(_read(root, f, 20_000) for f in files if f.endswith(".csproj"))
    st = []
    if names & {"plugin.yml", "paper-plugin.yml", "bungee.yml", "velocity-plugin.json"} or re.search(r"spigot|papermc|bukkit|velocity", build, re.I):
        st.append("minecraft-plugin")
    if names & {"fxmanifest.lua", "__resource.lua"}:
        st.append("fivem")
    if names & {"default.project.json", "wally.toml", "rokit.toml", "aftman.toml"} or ".luau" in exts:
        st.append("roblox")
    if re.search(r"\b(discord\.js|@discordjs/\w+|eris|oceanic\.js)\b", deps) or re.search(r"discord\.py|nextcord|py-cord|disnake|discord", py, re.I):
        st.append("discord-bot")
    if re.search(r"\belectron\b", deps) or "tauri.conf.json" in names or re.search(r"UseWPF|UseWindowsForms|Avalonia|WinUI", csproj):
        st.append("desktop")
    if re.search(r"\bnext\b|@remix-run|nuxt|@sveltejs/kit", deps):
        st.append("web-app")
    if re.search(r"stripe|iyzipay|@paddle|lemonsqueezy|next-auth|@auth/|clerk|better-auth", deps) or (re.search(r"prisma|drizzle", deps) and "web-app" in st):
        st.append("saas")
    if re.search(r"\b(express|fastify|@nestjs/core|hono|koa)\b", deps) or re.search(r"fastapi|django|flask", py, re.I):
        st.append("api")
    if re.search(r"prisma|drizzle|typeorm|sequelize|mongoose|knex", deps) or re.search(r"sqlalchemy|alembic|psycopg", py, re.I) or ".sql" in exts:
        st.append("database")
    if re.search(r"\b(react|vue|svelte|@angular/core|solid-js)\b", deps):
        st.append("frontend")
    if "dockerfile" in names or "docker-compose.yml" in names or "caddyfile" in names or (root / ".github").is_dir():
        st.append("infra")
    if "remotion" in deps:
        st.append("video")
    return st


# stack → skills (user skills dir / plugins / catalog). Only names that exist somewhere are shown.
RECOMMEND = {
    "minecraft-plugin": ["lisans-yap", "systematic-debugging", "test-driven-development"],
    "fivem": ["systematic-debugging", "security-audit"],
    "roblox": ["systematic-debugging"],
    "discord-bot": ["systematic-debugging", "api-design", "security-audit"],
    "desktop": ["systematic-debugging", "frontend-design", "verification-before-completion"],
    "web-app": ["nextjs-app-router-patterns", "vercel-react-best-practices", "web-perf", "web-design-guidelines", "webapp-testing"],
    "saas": ["security-audit", "api-design", "database-migrations", "seo"],
    "api": ["api-design", "security-audit", "test-driven-development"],
    "database": ["database-migrations", "supabase-postgres-best-practices"],
    "frontend": ["frontend-design", "web-design-guidelines", "vercel-composition-patterns"],
    "infra": ["gha-security-review", "bash-defensive-patterns", "mcp-dependency-review"],
    "video": ["remotion-best-practices"],
}
AGENTS = {
    "minecraft-plugin": ["developer", "debugger", "qa"], "fivem": ["developer", "security-auditor", "debugger"],
    "roblox": ["developer", "debugger"], "discord-bot": ["backend", "security-auditor", "debugger"],
    "desktop": ["frontend", "developer", "qa"], "web-app": ["frontend", "ui-ux", "performance"],
    "saas": ["architect", "security-auditor", "database", "backend"], "api": ["backend", "security-auditor", "qa"],
    "database": ["database"], "frontend": ["frontend", "ui-ux"], "infra": ["devops"], "video": ["frontend"],
}


def available_skills():
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    have = set()
    sd = home / "skills"
    if sd.is_dir():
        have |= {p.name for p in sd.iterdir() if (p / "SKILL.md").is_file()}
    pc = home / "plugins" / "cache"
    if pc.is_dir():
        have |= {p.parent.name for p in pc.glob("**/skills/*/SKILL.md")}
    return have


def recommend(root):
    st = detect(root)
    have = available_skills()
    skills, agents = [], []
    for s in st:
        skills += [k for k in RECOMMEND.get(s, []) if k not in skills]
        agents += [a for a in AGENTS.get(s, []) if a not in agents]
    return {"stack": st, "skills_installed": [k for k in skills if k in have],
            "skills_missing": [k for k in skills if k not in have], "agents": agents}


def session_hint(root):
    """One short line for SessionStart; cached per root so it costs nothing on repeat."""
    root = Path(root)
    if not (root / ".git").exists() and not (root / "package.json").exists():
        return ""
    cache = root / ".omnis" / "adapt.json"
    try:
        if cache.is_file() and cache.stat().st_mtime > time_ago(3600 * 12):
            r = json.loads(cache.read_text(encoding="utf-8"))
        else:
            r = recommend(root)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(r), encoding="utf-8")
    except (OSError, ValueError):
        return ""
    if not r["stack"]:
        return ""
    line = f"OMNIS project: {', '.join(r['stack'])}."
    if r["skills_installed"]:
        line += f" Relevant skills: {', '.join(r['skills_installed'][:6])}."
    if r["agents"]:
        line += f" Fitting agents (only for big tasks): {', '.join(r['agents'][:4])}."
    return line


def time_ago(sec):
    import time
    return time.time() - sec


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = next((a for a in argv if not a.startswith("--")), ".")
    r = recommend(root)
    if "--json" in argv:
        print(json.dumps(r, indent=2))
        return 0
    print("Yığın: " + (", ".join(r["stack"]) or "tanınmadı"))
    print("Kurulu ve uygun skill'ler: " + (", ".join(r["skills_installed"]) or "-"))
    if r["skills_missing"]:
        print("Önerilen ama kurulu değil: " + ", ".join(r["skills_missing"]) + "  (kurmak için: /skills-install <ad>)")
    print("Uygun ajanlar (yalnız büyük işlerde): " + (", ".join(r["agents"]) or "-"))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
