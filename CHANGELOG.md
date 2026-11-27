# Changelog

## 1.0.0 — 2026-11-27
- Phase 0: ecosystem research (docs/ECOSYSTEM_RESEARCH.md)
- Phase 1: router SKILL.md, project map, symbol index, output filter, verify plan, env doctor
- Phase 2: memory + bug patterns, checkpoints/resume, debug & deep workflows
- Phase 3: curated catalog (30 skills, 8 presets), audit, installer with lock/backup/rollback, conflicts, update, remove
- Phase 4: usage intelligence from transcripts, reminder manager (CronCreate / /schedule / OS)
- Phase 5: security scan + PreToolUse guard hook, UI/DB/infra/research/agents engines
- Phase 6: benchmark tool and results

## 1.1.0 — multi-tool
- MCP server (`scripts/mcp_server.py`): stdio + loopback streamable HTTP with token.
- `install.py --target` for codex, gemini, antigravity, cursor, vscode, windsurf, cline, roo, opencode, continue, chatgpt (explanation), agents.
- guard.py `--format codex|gemini|cursor`; Codex execpolicy rules.
- `gateway_filter.py`: opt-in secret-masking proxy for AI gateways (9Router).
- 12 new tests (66 total).

## 1.2.0 — Claude Code Developer OS
- `/omnis setup|durum|geri-al` (os_setup.py), `install.py --os`: audit → backup → install → validate → Turkish report; rollback via manifest.
- 14 specialist agents, 30 commands (workflow, skills-*, automation-*), collision-safe names.
- os_hooks.py: protected files, post-edit secret scan + formatter, Stop typecheck (loop-safe) + toast, SessionStart checkpoint restore, PreCompact checkpoint.
- skill_registry.py, project_adapt.py (Minecraft/FiveM/Roblox/Discord/desktop/SaaS), automation.py (Task Scheduler + toast), toast.py.
- Turkish docs in docs/tr/. 8 new tests (74 total).
