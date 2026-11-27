#!/usr/bin/env python3
"""Install / update / uninstall OMNIS. Idempotent; backs up anything it replaces. Dry run unless --yes.

Claude Code (the original target):
  python install.py --yes                 global install to ~/.claude/skills/omnis
  python install.py --project DIR --yes   install into DIR/.claude/skills/omnis instead
  python install.py --with-hook --yes     also register the OMNIS safety hook (PreToolUse) in settings.json
  python install.py --uninstall --yes     remove the skill and the hook (backups kept)
  python install.py --verify              run the test suite against the installed copy

Other AI tools (shared engine in ~/.omnis/app, MCP server + guidance + guard where the tool has hooks):
  python install.py --list-targets                    what is detected on this machine
  python install.py --target codex [--yes]            one tool (comma-separate several)
  python install.py --target all --yes                every detected tool
  python install.py --target agents --project DIR     write the AGENTS.md block into a repo
  python install.py --target codex --uninstall --yes  remove OMNIS from a tool

Targets: claude codex gemini antigravity cursor vscode windsurf cline roo opencode continue chatgpt agents
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
PAYLOAD = ["SKILL.md", "install.py", "README.md", "CHANGELOG.md", "LICENSE", "scripts", "workflows", "engines", "config", "docs", "tests", "adapters"]
HOOK_MARK = "omnis/scripts/guard.py"
MD_BEGIN, MD_END = "<!-- omnis:begin -->", "<!-- omnis:end -->"
TOML_BEGIN, TOML_END = "# >>> omnis >>>", "# <<< omnis <<<"
PY = "python" if os.name == "nt" else "python3"
STAMP = time.strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------- Claude Code (unchanged behaviour)

def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def backup_dir():
    d = claude_home() / "omnis" / "backups" / time.strftime("%Y%m%d-%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    return d


def hook_command(dest):
    return f'{PY} "{(dest / "scripts" / "guard.py").as_posix()}"'


def edit_settings(settings, dest, add, yes):
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except ValueError:
        print(f"! {settings} is not valid JSON — not touching it")
        return
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    kept = [g for g in pre if not any(HOOK_MARK in h.get("command", "").replace("\\", "/") for h in g.get("hooks", []))]
    if add:
        kept.append({"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": hook_command(dest), "timeout": 10}]})
    if kept == pre:
        print(f"= hook already {'present' if add else 'absent'} in {settings}")
        return
    data["hooks"]["PreToolUse"] = kept
    if not kept:
        del data["hooks"]["PreToolUse"]
    if not data["hooks"]:
        del data["hooks"]
    print(f"{'+' if add else '-'} safety hook {'into' if add else 'from'} {settings}")
    if yes:
        if settings.exists():
            shutil.copy2(settings, backup_dir() / settings.name)
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def copy_payload(dest, yes, backup):
    if dest.resolve() == SRC:
        sys.exit("source and destination are the same directory")
    action = "update" if dest.exists() else "install"
    print(f"{'~' if action == 'update' else '+'} {action} OMNIS → {dest}")
    if not yes:
        return
    staging = dest.parent / ".omnis.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for item in PAYLOAD:
        s = SRC / item
        if s.is_dir():
            shutil.copytree(s, staging / item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".omnis"))
        elif s.exists():
            shutil.copy2(s, staging / item)
    if dest.exists():
        b = backup()
        shutil.move(str(dest), str(b / dest.name))
    staging.rename(dest)


def claude_main(a):
    base = (Path(a.project) / ".claude") if a.project else claude_home()
    dest = base / "skills" / "omnis"
    settings = base / ("settings.local.json" if a.project else "settings.json")
    if a.verify:
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(dest / "tests"), "-q"]).returncode
    if a.uninstall:
        print(f"- remove {dest}")
        if a.yes and dest.exists():
            shutil.move(str(dest), str(backup_dir() / "omnis"))
        edit_settings(settings, dest, False, a.yes)
        print("done (backup kept)" if a.yes else "dry run — add --yes")
        return 0
    copy_payload(dest, a.yes, backup_dir)
    if a.with_hook:
        edit_settings(settings, dest, True, a.yes)
    if not a.yes:
        print("dry run — add --yes")
        return 0
    ok = (dest / "SKILL.md").is_file() and (dest / "scripts" / "omnis.py").is_file()
    print("verified: SKILL.md and scripts present" if ok else "! install incomplete")
    print("Start a new Claude Code session, then try: /omnis map")
    return 0 if ok else 1


# ---------------------------------------------------------------- multi-tool targets

class Ctx:
    """Paths and the change log for one run. `home` is overridable for tests (OMNIS_TARGET_HOME)."""

    def __init__(self, yes, project=None, home=None):
        self.yes = yes
        self.project = Path(project).resolve() if project else None
        self.home = Path(home or os.environ.get("OMNIS_TARGET_HOME") or Path.home())
        self.test_mode = bool(home or os.environ.get("OMNIS_TARGET_HOME"))
        self.changes = []

    # where things live
    @property
    def omnis_home(self):
        return Path(os.environ.get("OMNIS_HOME") or self.home / ".omnis") if not self.test_mode else self.home / ".omnis"

    @property
    def engine(self):
        return self.omnis_home / "app"

    def vscode_user(self, product="Code"):
        if os.name == "nt":
            base = Path(os.environ["APPDATA"]) if os.environ.get("APPDATA") and not self.test_mode else self.home / "AppData" / "Roaming"
        elif sys.platform == "darwin":
            base = self.home / "Library" / "Application Support"
        else:
            base = self.home / ".config"
        return base / product / "User"

    def mcp_cmd(self):
        return PY, [str((self.engine / "scripts" / "mcp_server.py").as_posix())]

    def guard_cmd(self, fmt):
        return f'{PY} "{(self.engine / "scripts" / "guard.py").as_posix()}" --format {fmt}'

    # safe writes
    def backup(self, path, target):
        if path.exists() and self.yes:
            d = self.omnis_home / "backups" / STAMP / target
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, d / path.name)

    def write(self, path, text, target, what):
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            print(f"  = {what}: already up to date ({path})")
            return
        print(f"  {'~' if old is not None else '+'} {what} → {path}")
        self.changes.append(str(path))
        if self.yes:
            self.backup(path, target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def remove(self, path, target, what):
        if not path.exists():
            print(f"  = {what}: absent ({path})")
            return
        print(f"  - {what} ← {path}")
        self.changes.append(str(path))
        if self.yes:
            self.backup(path, target)
            path.unlink()


def load_json(path):
    """JSON or JSONC (comments, trailing commas). Returns None if it can't be parsed safely."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except ValueError:
        pass
    stripped = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', lambda m: m.group(1) or "", text, flags=re.S)
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    try:
        return json.loads(stripped)
    except ValueError:
        return None


def json_edit(ctx, path, target, what, mutate):
    data = load_json(path)
    if data is None or not isinstance(data, dict):
        print(f"  ! {path} is not parseable JSON — not touching it ({what})")
        return
    before = json.dumps(data, sort_keys=True)
    mutate(data)
    if json.dumps(data, sort_keys=True) == before:
        print(f"  = {what}: already {'present' if not ctx.uninstalling else 'absent'} ({path})")
        return
    ctx.write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", target, what)


def set_key(container_key, name, value, uninstall):
    def mutate(data):
        box = data.setdefault(container_key, {}) if not uninstall else data.get(container_key)
        if uninstall:
            if isinstance(box, dict) and name in box:
                del box[name]
                if not box:
                    del data[container_key]
        else:
            box[name] = value
    return mutate


def block_edit(ctx, path, target, what, body, begin=MD_BEGIN, end=MD_END):
    """Insert/replace/remove a marker-delimited block in a text file (AGENTS.md, GEMINI.md, config.toml...)."""
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    rx = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
    if ctx.uninstalling:
        if not rx.search(old):
            print(f"  = {what}: absent ({path})")
            return
        new = rx.sub("", old).rstrip() + "\n"
        if not new.strip():
            return ctx.remove(path, target, what)
    else:
        block = f"{begin}\n{body.strip()}\n{end}\n"
        new = rx.sub(lambda _: block, old) if rx.search(old) else (old.rstrip() + "\n\n" + block if old.strip() else block)
    ctx.write(path, new, target, what)


def guidance():
    return (SRC / "adapters" / "AGENTS.md").read_text(encoding="utf-8")


def stdio_entry(ctx, **extra):
    cmd, args = ctx.mcp_cmd()
    return {"command": cmd, "args": args, **extra}


def hook_groups_edit(event, matcher, command, mark="guard.py"):
    """Claude-style hook groups: {"hooks": {event: [{matcher, hooks:[{type,command}]}]}}."""
    def mutate(data, uninstall):
        groups = data.get("hooks", {}).get(event, [])
        kept = [g for g in groups if not any(mark in str(h.get("command", "")).replace("\\", "/") and "omnis" in str(h.get("command", "")).replace("\\", "/")
                                             for h in g.get("hooks", []))]
        if not uninstall:
            kept.append({"matcher": matcher, "hooks": [{"type": "command", "command": command, "timeout": 10}]})
        if kept:
            data.setdefault("hooks", {})[event] = kept
        elif "hooks" in data:
            data["hooks"].pop(event, None)
            if not data["hooks"]:
                del data["hooks"]
    return mutate


# --- per-tool adapters. Each returns nothing; prints what it does. ctx.uninstalling is set by the caller.

def t_codex(ctx):
    d = ctx.home / ".codex"
    cmd, args = ctx.mcp_cmd()
    toml = (f'[mcp_servers.omnis]\ncommand = {json.dumps(cmd)}\nargs = {json.dumps(args)}\n'
            'startup_timeout_sec = 20\ntool_timeout_sec = 600\n')
    cfg = d / "config.toml"
    existing = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
    if not ctx.uninstalling and "[mcp_servers.omnis]" in re.sub(re.escape(TOML_BEGIN) + ".*?" + re.escape(TOML_END), "", existing, flags=re.S):
        print(f"  ! {cfg} already has an [mcp_servers.omnis] not managed by OMNIS — leaving it")
    else:
        block_edit(ctx, cfg, "codex", "MCP server", toml, TOML_BEGIN, TOML_END)
    block_edit(ctx, d / "AGENTS.md", "codex", "global AGENTS.md guidance", guidance())
    rules = d / "rules" / "omnis.rules"
    if ctx.uninstalling:
        ctx.remove(rules, "codex", "execpolicy rules")
    else:
        ctx.write(rules, (SRC / "adapters" / "omnis.rules").read_text(encoding="utf-8"), "codex", "execpolicy rules")
    m = hook_groups_edit("PreToolUse", "^(Bash|shell|local_shell|exec_command)$", ctx.guard_cmd("codex"))
    json_edit(ctx, d / "hooks.json", "codex", "PreToolUse guard hook", lambda data: m(data, ctx.uninstalling))


def t_gemini(ctx):
    d = ctx.home / ".gemini"
    m = hook_groups_edit("BeforeTool", "run_shell_command", ctx.guard_cmd("gemini"))

    def mutate(data):
        set_key("mcpServers", "omnis", stdio_entry(ctx, timeout=600000, trust=False), ctx.uninstalling)(data)
        m(data, ctx.uninstalling)
    json_edit(ctx, d / "settings.json", "gemini", "MCP server + BeforeTool guard hook", mutate)
    block_edit(ctx, d / "GEMINI.md", "gemini", "GEMINI.md guidance", guidance())


def t_antigravity(ctx):
    d = ctx.home / ".gemini"
    json_edit(ctx, d / "antigravity" / "mcp_config.json", "antigravity", "MCP server",
              set_key("mcpServers", "omnis", stdio_entry(ctx), ctx.uninstalling))
    block_edit(ctx, d / "GEMINI.md", "antigravity", "GEMINI.md global rules", guidance())


def t_cursor(ctx):
    d = ctx.home / ".cursor"
    json_edit(ctx, d / "mcp.json", "cursor", "MCP server", set_key("mcpServers", "omnis", stdio_entry(ctx), ctx.uninstalling))

    def hooks(data):
        lst = data.get("hooks", {}).get("beforeShellExecution", [])
        kept = [h for h in lst if "omnis" not in str(h.get("command", "")).replace("\\", "/")]
        if not ctx.uninstalling:
            data.setdefault("version", 1)
            kept.append({"command": ctx.guard_cmd("cursor")})
        if kept:
            data.setdefault("hooks", {})["beforeShellExecution"] = kept
        elif "hooks" in data:
            data["hooks"].pop("beforeShellExecution", None)
    json_edit(ctx, d / "hooks.json", "cursor", "beforeShellExecution guard hook", hooks)
    if ctx.project:
        rule = ctx.project / ".cursor" / "rules" / "omnis.mdc"
        if ctx.uninstalling:
            ctx.remove(rule, "cursor", "project rule")
        else:
            ctx.write(rule, "---\ndescription: OMNIS engineering and safety rules\nalwaysApply: true\n---\n\n" + guidance(), "cursor", "project rule")
    else:
        print("  i Cursor user rules live in Settings → Rules (not a file). Use --project DIR to write .cursor/rules/omnis.mdc")


def t_vscode(ctx):
    u = ctx.vscode_user()
    json_edit(ctx, u / "mcp.json", "vscode", "MCP server (Copilot agent mode)",
              set_key("servers", "omnis", stdio_entry(ctx, type="stdio"), ctx.uninstalling))
    instr = u / "prompts" / "omnis.instructions.md"
    if ctx.uninstalling:
        ctx.remove(instr, "vscode", "user instructions")
    else:
        ctx.write(instr, "---\napplyTo: '**'\ndescription: OMNIS engineering and safety rules\n---\n\n" + guidance(), "vscode", "user instructions")
    if ctx.project:
        block_edit(ctx, ctx.project / ".github" / "copilot-instructions.md", "vscode", "copilot-instructions.md", guidance())


def t_windsurf(ctx):
    d = ctx.home / ".codeium" / "windsurf"
    json_edit(ctx, d / "mcp_config.json", "windsurf", "MCP server", set_key("mcpServers", "omnis", stdio_entry(ctx), ctx.uninstalling))
    block_edit(ctx, d / "memories" / "global_rules.md", "windsurf", "global rules", guidance())


def _ext_settings(ctx, ext, fname):
    return ctx.vscode_user() / "globalStorage" / ext / "settings" / fname


def t_cline(ctx):
    json_edit(ctx, _ext_settings(ctx, "saoudrizwan.claude-dev", "cline_mcp_settings.json"), "cline", "MCP server",
              set_key("mcpServers", "omnis", stdio_entry(ctx, disabled=False), ctx.uninstalling))


def t_roo(ctx):
    json_edit(ctx, _ext_settings(ctx, "rooveterinaryinc.roo-cline", "mcp_settings.json"), "roo", "MCP server",
              set_key("mcpServers", "omnis", stdio_entry(ctx, disabled=False), ctx.uninstalling))


def t_opencode(ctx):
    d = ctx.home / ".config" / "opencode"
    cmd, args = ctx.mcp_cmd()
    json_edit(ctx, d / "opencode.json", "opencode", "MCP server",
              set_key("mcp", "omnis", {"type": "local", "command": [cmd, *args], "enabled": True}, ctx.uninstalling))
    block_edit(ctx, d / "AGENTS.md", "opencode", "global AGENTS.md guidance", guidance())


def t_continue(ctx):
    f = ctx.home / ".continue" / "mcpServers" / "omnis.yaml"
    cmd, args = ctx.mcp_cmd()
    if ctx.uninstalling:
        return ctx.remove(f, "continue", "MCP server")
    ctx.write(f, "name: OMNIS\nversion: 1.1.0\nschema: v1\nmcpServers:\n  - name: omnis\n"
                 f"    command: {json.dumps(cmd)}\n    args: {json.dumps(args)}\n", "continue", "MCP server")


def t_agents(ctx):
    if not ctx.project:
        print("  ! agents needs --project DIR (AGENTS.md lives in a repository)")
        return
    block_edit(ctx, ctx.project / "AGENTS.md", "agents", "AGENTS.md", guidance())


def t_chatgpt(ctx):
    print("  i ChatGPT (web/desktop) can't start local programs. Its connectors and developer mode only talk to a REMOTE\n"
          "    MCP server over HTTPS. OMNIS has a local streamable-HTTP mode:\n"
          f"      {PY} {(ctx.engine / 'scripts' / 'mcp_server.py').as_posix()} --http --port 8765 --root <project>\n"
          "    It binds 127.0.0.1 with a bearer token. ChatGPT would need a public HTTPS tunnel to it, which exposes your\n"
          "    machine. OMNIS does not set that up. Codex (CLI/IDE/app) is the supported OpenAI path: --target codex.")


def has(cmd):
    return shutil.which(cmd) is not None


TARGETS = {
    # name: (adapter, detect(ctx))
    "claude": (None, lambda c: (c.home / ".claude").is_dir() or has("claude")),
    "codex": (t_codex, lambda c: (c.home / ".codex").is_dir() or has("codex")),
    "gemini": (t_gemini, lambda c: (c.home / ".gemini" / "settings.json").is_file() or has("gemini")),
    "antigravity": (t_antigravity, lambda c: (c.home / ".gemini" / "antigravity").is_dir()),
    "cursor": (t_cursor, lambda c: (c.home / ".cursor").is_dir() or has("cursor")),
    "vscode": (t_vscode, lambda c: c.vscode_user().is_dir()),
    "windsurf": (t_windsurf, lambda c: (c.home / ".codeium" / "windsurf").is_dir()),
    "cline": (t_cline, lambda c: _ext_settings(c, "saoudrizwan.claude-dev", "x").parent.parent.is_dir()),
    "roo": (t_roo, lambda c: _ext_settings(c, "rooveterinaryinc.roo-cline", "x").parent.parent.is_dir()),
    "opencode": (t_opencode, lambda c: (c.home / ".config" / "opencode").is_dir() or has("opencode")),
    "continue": (t_continue, lambda c: (c.home / ".continue").is_dir()),
    "chatgpt": (t_chatgpt, lambda c: False),
    "agents": (t_agents, lambda c: False),
}


def ensure_engine(ctx):
    if ctx.uninstalling:
        return
    if ctx.engine.resolve() == SRC:
        return
    copy_payload(ctx.engine, ctx.yes, lambda: _mk(ctx.omnis_home / "backups" / STAMP))


def _mk(d):
    d.mkdir(parents=True, exist_ok=True)
    return d


def targets_main(a, home=None):
    ctx = Ctx(a.yes, a.project, home)
    ctx.uninstalling = a.uninstall
    names = [n.strip() for n in a.target.split(",") if n.strip()]
    if names == ["all"]:
        names = [n for n, (_, det) in TARGETS.items() if det(ctx)]
        print("detected: " + (", ".join(names) or "nothing"))
    bad = [n for n in names if n not in TARGETS]
    if bad:
        print(f"unknown target(s): {', '.join(bad)}. Known: {', '.join(TARGETS)}")
        return 2
    rc = 0
    if any(n != "claude" for n in names):
        ensure_engine(ctx)
    for n in names:
        print(f"[{n}]")
        if n == "claude":
            rc |= claude_main(a)
            continue
        TARGETS[n][0](ctx)
    if ctx.uninstalling and a.yes:
        print(f"  i shared engine kept at {ctx.engine} (delete it by hand when no tool uses it)")
    print(("done" + (f" ({len(ctx.changes)} file(s) changed, backups in {ctx.omnis_home / 'backups' / STAMP})" if ctx.changes else ""))
          if a.yes else "dry run — add --yes")
    return rc


def list_targets(home=None):
    ctx = Ctx(False, None, home)
    for n, (_, det) in TARGETS.items():
        print(f"  {'✓' if det(ctx) else '·'} {n}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project")
    ap.add_argument("--with-hook", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--target", help="comma-separated tool names, or 'all' for every detected tool")
    ap.add_argument("--list-targets", action="store_true")
    a = ap.parse_args(argv)
    if a.list_targets:
        return list_targets()
    if a.target:
        return targets_main(a)
    return claude_main(a)


if __name__ == "__main__":
    sys.exit(main())
