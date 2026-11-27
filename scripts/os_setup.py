#!/usr/bin/env python3
"""OMNIS Developer OS for Claude Code: one command does audit → plan → install → validate → report (Turkish).

  os_setup.py audit              what is installed, duplicates, conflicts (read-only)
  os_setup.py setup [--dry-run]  back up, then install agents, commands, hooks, MCP, automation; validate; report
  os_setup.py durum              health check
  os_setup.py rollback [TS]      undo a setup run (latest if TS omitted); `list` shows runs

Everything changed is recorded in ~/.claude/omnis/backups/<ts>/manifest.json. Existing files that OMNIS did not
create are never overwritten. CLAUDE.md is only appended to (marker block), never rewritten.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

MARK = "<!-- omnis-managed -->"
MD_BEGIN, MD_END = "<!-- omnis:begin -->", "<!-- omnis:end -->"
BUILTIN_CMDS = {"add-dir", "agents", "bug", "clear", "compact", "config", "context", "cost", "debug", "doctor", "docs", "export",
                "feedback", "help", "hooks", "ide", "init", "login", "logout", "mcp", "memory", "model", "permissions", "plan",
                "pr-comments", "release-notes", "resume", "review", "rewind", "security-review", "code-review", "simplify",
                "status", "statusline", "terminal-setup", "todos", "upgrade", "usage", "vim", "loop", "schedule", "run",
                "ship", "steward", "plugin", "skills", "fast", "effort", "theme"}
MCP_SERVERS = {  # no credentials, pinned versions (>= 2 weeks old when chosen)
    "context7": ["npx", "-y", "@upstash/context7-mcp@4.6.0"],
    "playwright": ["npx", "-y", "@playwright/mcp@0.0.84"],
}
PY = "python" if os.name == "nt" else "python3"


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def skill_dir():
    return claude_home() / "skills" / "omnis"


def backups_root():
    return claude_home() / "omnis" / "backups"


def _json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _claude(*args, timeout=60):
    exe = shutil.which("claude")
    if not exe or os.environ.get("OMNIS_NO_CLAUDE_CLI"):
        return 127, "claude CLI not found"
    try:
        p = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def _frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


# ------------------------------------------------------------------ audit

def plugin_agents_and_commands():
    names = {"agents": set(), "commands": set()}
    pc = claude_home() / "plugins" / "cache"
    if pc.is_dir():
        for kind in names:
            names[kind] |= {p.stem for p in pc.glob(f"**/{kind}/*.md")}
    return names


def audit():
    h = claude_home()
    settings = _json(h / "settings.json", {}) or {}
    import skill_registry
    rows = skill_registry.rows(h)
    pa = plugin_agents_and_commands()
    user_agents = sorted(p.stem for p in (h / "agents").glob("*.md")) if (h / "agents").is_dir() else []
    user_cmds = sorted(p.stem for p in (h / "commands").glob("*.md")) if (h / "commands").is_dir() else []
    code, ver = _claude("--version")
    hooks = settings.get("hooks", {})
    rep = {
        "claude_version": ver if code == 0 else "bulunamadı",
        "settings_ok": (h / "settings.json").exists() and _json(h / "settings.json") is not None,
        "guard_hook": "guard.py" in json.dumps(hooks),
        "hook_events": {k: len(v) for k, v in hooks.items()},
        "claude_md": (h / "CLAUDE.md").is_file(),
        "plugins": [k for k, v in settings.get("enabledPlugins", {}).items() if v],
        "skills_user": sum(1 for r in rows if r["where"] == "user"),
        "skills_plugin": sum(1 for r in rows if r["where"] == "plugin"),
        "skill_duplicates": skill_registry.dupes(rows),
        "agents_user": user_agents, "agents_plugin": sorted(pa["agents"]),
        "commands_user": user_cmds, "commands_plugin": sorted(pa["commands"]),
        "mcp": _claude("mcp", "list", timeout=90)[1].splitlines()[1:] if shutil.which("claude") else [],
    }
    conflicts = []
    groups = {}
    for name, srcs in rep["skill_duplicates"].items():
        groups.setdefault(" + ".join(sorted(srcs)), []).append(name)
    for srcs, names in groups.items():
        conflicts.append(f"{len(names)} skill iki yerde birden ({srcs}): {', '.join(names[:8])}{' …' if len(names) > 8 else ''}"
                         + (" — iki eklenti aynı depoyu kuruyor; birini kapatmak yeterli" if len(names) > 5 else ""))
    if "deep-research" in {r["name"] for r in rows if r["where"] == "user"}:
        conflicts.append("skill 'deep-research' (user, ECC) needs firecrawl/exa MCP which are not installed; anthropic-skills:deep-research is the working one")
    rep["conflicts"] = conflicts
    return rep


def render_audit(rep):
    L = ["## Denetim",
         f"- Claude Code: {rep['claude_version']}",
         f"- settings.json: {'geçerli' if rep['settings_ok'] else 'YOK/BOZUK'}; OMNIS güvenlik kancası: {'var' if rep['guard_hook'] else 'yok'}",
         f"- Kanca olayları: {', '.join(f'{k}×{v}' for k, v in rep['hook_events'].items()) or '-'}",
         f"- Eklentiler: {', '.join(rep['plugins']) or '-'}",
         f"- Skill'ler: kullanıcı {rep['skills_user']}, eklenti {rep['skills_plugin']}",
         f"- Ajanlar: kullanıcı {len(rep['agents_user'])}, eklenti {', '.join(rep['agents_plugin']) or '-'}",
         f"- Komutlar: kullanıcı {len(rep['commands_user'])}, eklenti {len(rep['commands_plugin'])}",
         f"- MCP: {len(rep['mcp'])} sunucu"]
    if rep["conflicts"]:
        L.append(f"- Çakışmalar ({len(rep['conflicts'])}):")
        L += [f"  - {c}" for c in rep["conflicts"][:25]]
    return "\n".join(L)


# ------------------------------------------------------------------ setup pieces

class Run:
    def __init__(self, dry):
        self.dry = dry
        self.ts = time.strftime("%Y%m%d-%H%M%S")
        self.dir = backups_root() / self.ts
        self.manifest = {"ts": self.ts, "created": [], "replaced": [], "backed_up": [], "mcp_added": [], "tasks_added": [], "notes": []}
        self.log = []

    def backup(self, path):
        path = Path(path)
        if self.dry or not path.exists():
            return
        dest = self.dir / "files" / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(path, dest)
        self.manifest["backed_up"].append({"src": str(path), "copy": str(dest)})

    def write_managed(self, path, text):
        path = Path(path)
        if path.exists():
            old = path.read_text(encoding="utf-8", errors="replace")
            if MARK not in old:
                self.log.append(f"atlandı (senin dosyan): {path.name}")
                return "skipped"
            if old == text:
                return "same"
            if not self.dry:
                self.backup_file_into(path)
                path.write_text(text, encoding="utf-8")
            self.manifest["replaced"].append(str(path))
            return "updated"
        if not self.dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest["created"].append(str(path))
        return "created"

    def backup_file_into(self, path):
        dest = self.dir / "managed" / path.parent.name / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        self.manifest["backed_up"].append({"src": str(path), "copy": str(dest)})

    def save(self):
        if self.dry:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "manifest.json").write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def O():
    return f'{PY} "{(skill_dir() / "scripts" / "omnis.py").as_posix()}"'


def render_agents(run):
    spec = _json(ROOT / "os" / "agents.json")["agents"]
    pa = plugin_agents_and_commands()["agents"]
    counts = {"created": 0, "updated": 0, "same": 0, "skipped": 0}
    for name, a in spec.items():
        if name in pa:
            run.log.append(f"ajan '{name}' bir eklentide zaten var — atlandı")
            counts["skipped"] += 1
            continue
        text = (f"---\nname: {name}\ndescription: {a['description']}\ntools: {a['tools']}\nmodel: {a['model']}\n---\n{MARK}\n\n"
                + a["body"].replace("{O}", O()) + "\n\nRules: stay in your scope; never edit files another agent owns in this task; "
                "never print secrets; finish with VERIFIED / NOT VERIFIED.\n")
        counts[run.write_managed(claude_home() / "agents" / f"{name}.md", text)] += 1
    return counts


def render_commands(run):
    spec = _json(ROOT / "os" / "commands.json")["commands"]
    taken = BUILTIN_CMDS | plugin_agents_and_commands()["commands"]
    counts = {"created": 0, "updated": 0, "same": 0, "skipped": 0}
    for name, c in spec.items():
        if name in taken:
            run.log.append(f"komut '/{name}' zaten var (yerleşik/eklenti) — atlandı")
            counts["skipped"] += 1
            continue
        text = (f"---\ndescription: {c['desc']}\nargument-hint: {json.dumps(c['hint'])}\n---\n{MARK}\n\n"
                + c["body"].replace("{O}", O()) + "\n")
        counts[run.write_managed(claude_home() / "commands" / f"{name}.md", text)] += 1
    return counts


def hook_entries():
    s = (skill_dir() / "scripts" / "os_hooks.py").as_posix()
    c = lambda mode: f'{PY} "{s}" {mode}'  # noqa: E731
    return {
        "PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{"type": "command", "command": c("protect"), "timeout": 10}]}],
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": c("post-edit"), "timeout": 60}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": c("prompt"), "timeout": 5}]}],
        "Stop": [{"hooks": [{"type": "command", "command": c("stop"), "timeout": 200}]}],
        "SessionStart": [{"matcher": "startup|resume|compact", "hooks": [{"type": "command", "command": c("session"), "timeout": 20}]}],
        "PreCompact": [{"hooks": [{"type": "command", "command": c("precompact"), "timeout": 20}]}],
    }


def merge_hooks(settings, remove=False):
    hooks = settings.setdefault("hooks", {})
    for event, groups in hook_entries().items():
        cur = [g for g in hooks.get(event, []) if "os_hooks.py" not in json.dumps(g)]
        if not remove:
            cur += groups
        if cur:
            hooks[event] = cur
        else:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks", None)
    return settings


def install_hooks(run):
    p = claude_home() / "settings.json"
    data = _json(p, None)
    if data is None and p.exists():
        run.log.append("settings.json okunamadı — kancalar eklenmedi")
        return False
    data = data or {}
    before = json.dumps(data, sort_keys=True)
    merge_hooks(data)
    if json.dumps(data, sort_keys=True) == before:
        return True
    if not run.dry:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run.manifest["notes"].append("hooks merged into settings.json")
    return True


def claude_md_block():
    return (f"{MD_BEGIN}\n# OMNIS\n"
            "Developer OS: `/omnis setup` (kur/onar), `/omnis durum` (sağlık), `/omnis geri-al` (geri al). "
            "Workflow komutları: /analyze /omnis-plan /implement /omnis-debug /audit /omnis-security /omnis-review /test /optimize "
            "/refactor /omnis-docs /release /deploy /cleanup /research /project-onboard /task-report. "
            "Küçük işte ajan kullanma; iki ajan aynı dosyayı düzenlemesin. Sorvia kuralları yukarıda ve önceliklidir.\n"
            f"{MD_END}\n")


def install_claude_md(run):
    p = claude_home() / "CLAUDE.md"
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    block = claude_md_block()
    if MD_BEGIN in old:
        new = re.sub(re.escape(MD_BEGIN) + ".*?" + re.escape(MD_END) + r"\n?", lambda _: block, old, flags=re.S)
    else:
        new = old.rstrip("\n") + "\n\n" + block if old else block
    if new == old:
        return
    if not run.dry:
        p.write_text(new, encoding="utf-8")
    run.manifest["notes"].append("CLAUDE.md: OMNIS block appended (rest untouched)")


def install_mcp(run):
    out = {}
    for name, cmd in MCP_SERVERS.items():
        code, _ = _claude("mcp", "get", name, timeout=60)
        if code == 0:
            out[name] = "zaten var"
            continue
        if run.dry:
            out[name] = "eklenecek"
            continue
        code, msg = _claude("mcp", "add", "-s", "user", name, "--", *cmd, timeout=60)
        out[name] = "eklendi" if code == 0 else f"HATA: {msg[:120]}"
        if code == 0:
            run.manifest["mcp_added"].append(name)
    return out


def install_automation(run):
    import automation
    tasks = automation.load()
    if any(t["kind"] == "skill-update-check" for t in tasks.values()):
        return "zaten var"
    if run.dry:
        return "eklenecek (skill-update-check, her 5 saatte)"
    rc = automation.main(["add", "skill-update-check", "--every", "5h"] + (["--no-schedule"] if os.environ.get("OMNIS_NO_SCHED") else []))
    tid = next(k for k, t in automation.load().items() if t["kind"] == "skill-update-check")
    run.manifest["tasks_added"].append(tid)
    return "eklendi" if rc == 0 else "eklendi ama zamanlayıcı HATA"


def install_skill_copy(run):
    dest = skill_dir()
    if dest.resolve() == ROOT.resolve() or run.dry:
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("omnis_install", ROOT / "install.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.copy_payload(dest, True, lambda: _mk(run.dir / "skill"))


def _mk(d):
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------ validate / status

def validate():
    h = claude_home()
    res = []
    ok = lambda name, cond, detail="": res.append((name, bool(cond), detail))  # noqa: E731
    ok("settings.json geçerli JSON", _json(h / "settings.json") is not None)
    code, ver = _claude("--version")
    ok("claude --version", code == 0, ver)
    hooks_py = skill_dir() / "scripts" / "os_hooks.py"
    guard_py = skill_dir() / "scripts" / "guard.py"

    def fire(script, args, payload):
        p = subprocess.run([sys.executable, str(script), *args], input=json.dumps(payload), capture_output=True, text=True,
                           encoding="utf-8", timeout=60, env=dict(os.environ, OMNIS_NO_TOAST="1"))
        return p.returncode, p.stdout.strip()
    _, out = fire(guard_py, [], {"tool_name": "Bash", "tool_input": {"command": "rm -rf " + "/"}})
    ok("guard: felaket komutu engelliyor", '"deny"' in out)
    _, out = fire(hooks_py, ["protect"], {"tool_name": "Write", "tool_input": {"file_path": "x/.env"}})
    ok("koruma: .env için onay istiyor", '"ask"' in out)
    _, out = fire(hooks_py, ["protect"], {"tool_name": "Write", "tool_input": {"file_path": "x/app.ts"}})
    ok("koruma: normal dosyaya karışmıyor", out == "")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "c.py"
        f.write_text('API_KEY = "sk-ant-' + "x1" * 15 + '"\n', encoding="utf-8")
        _, out = fire(hooks_py, ["post-edit"], {"tool_name": "Write", "tool_input": {"file_path": str(f)}, "cwd": d, "session_id": "omnis-validate"})
        ok("düzenleme sonrası gizli bilgi taraması", "secret scan" in out)
        _, out = fire(hooks_py, ["stop"], {"session_id": "omnis-validate", "cwd": d, "stop_hook_active": False})
        ok("Stop kancası sessiz ve döngüsüz", out == "")
    bad = []
    for f in (h / "agents").glob("*.md"):
        t = f.read_text(encoding="utf-8", errors="replace")
        if MARK in t:
            fm = _frontmatter(t)
            if not fm or not fm.get("name") or not fm.get("description"):
                bad.append(f.name)
    ok("ajan dosyaları geçerli", not bad, ", ".join(bad))
    return res


def status_text():
    h = claude_home()
    lines = ["## OMNIS durum"]
    for name, good, detail in validate():
        lines.append(f"- {'✓' if good else '✗'} {name}" + (f" ({detail})" if detail and not good else ""))
    agents = [p.stem for p in (h / "agents").glob("*.md") if MARK in p.read_text(encoding="utf-8", errors="replace")] if (h / "agents").is_dir() else []
    cmds = [p.stem for p in (h / "commands").glob("*.md") if MARK in p.read_text(encoding="utf-8", errors="replace")] if (h / "commands").is_dir() else []
    lines.append(f"- OMNIS ajanları: {len(agents)}; OMNIS komutları: {len(cmds)}")
    import automation
    tasks = automation.load()
    lines.append(f"- Otomasyonlar: {len(tasks)} ({', '.join(f'{k}: {v.get('last_result', 'henüz çalışmadı')}' for k, v in tasks.items()) or '-'})")
    runs = sorted(p.parent.name for p in backups_root().glob("*/manifest.json")) if backups_root().is_dir() else []
    lines.append(f"- Geri alınabilir kurulumlar: {', '.join(runs[-3:]) or '-'}")
    return "\n".join(lines)


# ------------------------------------------------------------------ main flows

def setup(dry=False):
    run = Run(dry)
    rep = audit()
    print(render_audit(rep))
    print("\n## Plan\n- Yedek al → OMNIS skill'ini güncelle → 14 uzman ajan → workflow/skill/otomasyon komutları → kancalar "
          "→ CLAUDE.md'ye kısa OMNIS notu → MCP (context7, playwright) → otomasyon (skill güncelleme kontrolü, 5 saatte bir) → doğrula")
    if not dry:
        for p in (claude_home() / "settings.json", claude_home() / "CLAUDE.md"):
            run.backup(p)
        install_skill_copy(run)
    a = render_agents(run)
    c = render_commands(run)
    hk = install_hooks(run)
    install_claude_md(run)
    mcp = install_mcp(run)
    auto = install_automation(run)
    run.save()
    print("\n## Kurulum" + (" (deneme — hiçbir şey değişmedi)" if dry else ""))
    print(f"- Ajanlar: {a}\n- Komutlar: {c}\n- Kancalar: {'tamam' if hk else 'HATA'}\n- MCP: {mcp}\n- Otomasyon: {auto}")
    for l in run.log:
        print(f"  · {l}")
    if not dry:
        task = run.manifest["tasks_added"][:1]
        if task:
            import automation
            automation.run(task[0])
        print("\n" + status_text())
        print(f"\nGeri almak için: /omnis geri-al  (ya da: omnis rollback {run.ts})")
        print("Yeni ajan/komut/kancaların devreye girmesi için Claude Code'u yeniden başlat.")
    return 0


def rollback(ts=None):
    runs = sorted(p.parent.name for p in backups_root().glob("*/manifest.json")) if backups_root().is_dir() else []
    if ts == "list":
        print("\n".join(runs) or "kayıtlı kurulum yok")
        return 0
    if not runs:
        print("geri alınacak kurulum yok")
        return 1
    ts = ts or runs[-1]
    d = backups_root() / ts
    m = _json(d / "manifest.json")
    if not m:
        print(f"bulunamadı: {ts}")
        return 1
    for f in m.get("created", []):
        p = Path(f)
        if p.exists() and MARK in p.read_text(encoding="utf-8", errors="replace"):
            p.unlink()
    for b in m.get("backed_up", []):
        if Path(b["copy"]).is_file():
            shutil.copy2(b["copy"], b["src"])
    for name in m.get("mcp_added", []):
        _claude("mcp", "remove", "-s", "user", name)
    if m.get("tasks_added"):
        import automation
        for tid in m["tasks_added"]:
            automation.main(["remove", tid] + (["--no-schedule"] if os.environ.get("OMNIS_NO_SCHED") else []))
    (d / "manifest.json").rename(d / "manifest.rolled-back.json")
    print(f"geri alındı: {ts} (settings.json ve CLAUDE.md yedekten, eklenen ajan/komut/MCP/otomasyonlar kaldırıldı)")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = argv[0] if argv else "durum"
    if cmd == "audit":
        rep = audit()
        print(json.dumps(rep, indent=2, ensure_ascii=False) if "--json" in argv else render_audit(rep))
        return 0
    if cmd == "setup":
        return setup(dry="--dry-run" in argv)
    if cmd in ("durum", "status"):
        print(status_text())
        return 0
    if cmd in ("rollback", "geri-al"):
        return rollback(argv[1] if len(argv) > 1 else None)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
