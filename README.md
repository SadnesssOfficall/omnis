# OMNIS

An engineering layer for AI coding tools (Claude Code first; Codex, Gemini, Cursor, Copilot and others through MCP). It cuts wasted context, keeps work verifiable and safe, and adds memory, usage tracking, reminders and a vetted skill installer. Python 3.8+ stdlib only.

## Architecture

```
SKILL.md            router, always loaded (~70 lines). Picks FAST / STANDARD / DEEP / DEBUG
workflows/          debug.md, deep.md          (loaded on demand)
engines/            ui, database, research, security, infrastructure, agents, automation (on demand)
scripts/omnis.py    single entry point → the tools below
config/skill-catalog.json   curated, pinned external skills + presets
install.py          install / update / uninstall / hook / verify
tests/              54 tests
```

| Command (`python scripts/omnis.py …`) | What it does |
|---|---|
| `map` | Cached project map: languages, frameworks, package managers, run/build/test commands, entry points, tests. Monorepo-aware. Never reads `.env` contents |
| `find X` · `outline F` · `deps F` | Incremental symbol index. Python AST (high confidence), JS/TS/Go/Rust/Java/C#/PHP/Ruby regex (medium) |
| `filter "<cmd>"` | Runs the command and shows only errors, traces, locations and summaries. Saves the full log and keeps the exit code |
| `verify [--run]` | Changed files → related tests → checks. Runs them and reports VERIFIED/FAILED honestly. Flags secret-like files |
| `doctor` | OS, shell, tools, disk. Lists env var names only |
| `security scan\|diff\|classify` | Secret detection with redaction; command risk class |
| `memory add\|search\|inspect\|cleanup` · `memory bug add\|match` | Project facts with expiry and source checks; a "seen this error before?" bug-pattern store |
| `checkpoint save\|resume\|list` | Resume interrupted work, including git changes since the checkpoint |
| `usage [status\|report\|setup\|limits]` | Real token usage from local transcripts, a heuristic 5h window, limit messages, efficiency hints |
| `reminder add\|list\|pause\|resume\|set\|remove\|cron\|os-install` | Recurring reminders (default 5h) with quiet hours, max count and expiry. Uses CronCreate//loop, /schedule or the OS scheduler |
| `skills presets\|search\|plan\|install\|list\|conflicts\|update\|remove` | One-command install of curated skills: pinned commit → audit → plan → approval → install → lock file |
| `audit DIR` | Static security audit of any skill |
| `benchmark repo\|filter\|sessions` | Measures savings |
| `clean` | Removes this project's caches |

Optional hook: `guard.py` (PreToolUse) blocks catastrophic shell commands and asks before risky ones. See docs/SECURITY.md.

## Install
```bash
python3 install.py --yes                 # → ~/.claude/skills/omnis
python3 install.py --with-hook --yes     # + safety hook in ~/.claude/settings.json (backed up first)
python3 install.py --verify              # run tests on the installed copy
python3 install.py --uninstall --yes     # remove skill + hook (backups kept)
```
Then start a new Claude Code session and use `/omnis map`, `/omnis usage`, `/omnis skills install core`, …
Windows: see docs/WINDOWS.md (not yet tested on Windows).

## Other AI tools

One shared engine (`~/.omnis/app`), exposed through an MCP server (`scripts/mcp_server.py`, stdlib JSON-RPC, stdio).
Tools: map, find, outline, deps, filter, verify, doctor, security_scan, security_classify, memory_get/add,
checkpoint_save/resume, usage. Output is always secret-redacted; `filter` refuses risky commands.

```bash
python install.py --list-targets            # what is detected
python install.py --target all --yes        # every detected tool (dry run without --yes)
python install.py --target codex --uninstall --yes
python install.py --target agents --project DIR --yes   # AGENTS.md block in a repo
```

| Tool | What works | How | Guard (shell safety) |
|---|---|---|---|
| Claude Code | everything (skill + CLI) | `~/.claude/skills/omnis` | PreToolUse hook: deny + ask |
| Codex CLI / app | MCP tools, global guidance | `~/.codex/config.toml` `[mcp_servers.omnis]`, `~/.codex/AGENTS.md` | `rules/omnis.rules` (execpolicy: forbidden/prompt, prefix match only) + PreToolUse hook in `hooks.json` (deny only; Codex asks you to trust it in `/hooks`) |
| Gemini CLI | MCP tools, guidance | `~/.gemini/settings.json` `mcpServers`, `GEMINI.md` | BeforeTool hook: deny only (risky → Gemini's own confirmation). Untested here, built from docs |
| Antigravity | MCP tools, global rules | `~/.gemini/antigravity/mcp_config.json`, `~/.gemini/GEMINI.md` | none (no hook API); rules text only |
| Cursor | MCP tools, project rule | `~/.cursor/mcp.json`, `--project` → `.cursor/rules/omnis.mdc` | `~/.cursor/hooks.json` beforeShellExecution: allow/deny/ask. Untested here |
| VS Code Copilot | MCP tools (agent mode), instructions | `Code/User/mcp.json` `servers`, `prompts/omnis.instructions.md`, `--project` → `.github/copilot-instructions.md` | none from OMNIS; Copilot's own terminal confirmation |
| Windsurf | MCP tools, global rules | `~/.codeium/windsurf/mcp_config.json`, `memories/global_rules.md` | none ported |
| Cline / Roo | MCP tools | their `globalStorage/.../settings/*mcp_settings.json` | none ported (their own approval UI) |
| OpenCode | MCP tools, guidance | `~/.config/opencode/opencode.json` `mcp`, `AGENTS.md` | none ported (use its `permission` config) |
| Continue | MCP tools | `~/.continue/mcpServers/omnis.yaml` | none |
| Any AGENTS.md tool | rules text | `--target agents --project DIR` | text only |
| ChatGPT web/desktop | **not directly.** Connectors need a remote MCP over HTTPS | `mcp_server.py --http` = loopback-only streamable HTTP with bearer token (`~/.omnis/mcp-token`), Origin check, `filter` off unless `--allow-exec`; refuses public bind unless `--allow-remote`. Exposing it publicly is your decision and risk | n/a |
| AI gateway (9Router etc.) | secret masking + safety note for any client that opts in | `scripts/gateway_filter.py` OpenAI/Anthropic-compatible proxy in front of the gateway | masks secrets in outgoing messages; streams pass through |

Honest limits: `usage` only reads Claude Code transcripts. Hooks are pattern-based seatbelts, not sandboxes.
Codex execpolicy matches command prefixes only (`git push origin --force` is caught by the hook, not the rule).
Every installer target is dry-run by default, backs up each file to `~/.omnis/backups/<ts>/`, is idempotent, preserves
foreign entries (JSONC accepted for reading, written back as plain JSON) and has `--uninstall`.

### 9Router
9Router (0.5.123) has no general MCP hub: its MCP plugins are a hard-coded list (Browser MCP, Exa, Tavily), and its
"managed MCP" list is only pushed into Claude Cowork client config as remote URLs. It has no system-prompt injection or
request-filter plugin API. So OMNIS doesn't patch 9Router (an npm update would wipe a patch). It runs `gateway_filter.py`
as a separate opt-in proxy: clients that want secret masking use `http://127.0.0.1:20129/v1` instead of `:20128/v1`.

## Docs
ECOSYSTEM_RESEARCH · BENCHMARKS · SECURITY · WINDOWS (in `docs/`)

## Known limitations
- Symbol extraction outside Python uses regex. `deps` can't resolve path aliases or dynamic imports.
- The 5h usage window is a heuristic. Plan limits and exact reset times are only available in Claude Code's own `/usage`.
- In-session reminders need the session open. OS reminders send notifications and don't drive Claude.
- Cron can't do an exact 5h cycle across midnight (20:00 → 00:00 is a 4h gap).
- No controlled A/B session benchmark yet. Not tested on Windows or macOS.

## Roadmap
A/B benchmark harness · Windows CI · tree-sitter parsers for TS/Go · test-impact selection from coverage data · more catalog sources (skills.sh) after audit.
