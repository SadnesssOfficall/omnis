# Ecosystem research

Last checked: **2026-11-27**. Repository data (stars, license, last push, commit) fetched live from the GitHub API on that date. Nothing was installed during research.

## Skill collections

| Candidate | URL | Health (2026-11-27) | What it does | What OMNIS takes | Decision |
|---|---|---|---|---|---|
| Superpowers | github.com/obra/superpowers | ★327,887 · MIT · pushed 2026-11-26 | Methodology skills: brainstorming, plans, TDD, systematic debugging, verification, code review, worktrees | Its discipline skills are the **core** preset (pinned `22f0b46`). OMNIS defers to `systematic-debugging` when present and supplies tooling (index, filter, verify) the skills lack | **Install (curated subset)** |
| Anthropic skills | github.com/anthropics/skills | ★201,270 · per-skill license · pushed 2026-11-16 | Official example skills | `frontend-design`, `webapp-testing`, `mcp-builder` (Apache-2.0). docx/pdf/pptx/xlsx are source-available, and many users already have them via the Anthropic plugin | **Install subset**; exclude document skills |
| ECC (Everything Claude Code) | github.com/affaan-m/ECC | ★311,516 · MIT · pushed 2026-11-23 | ~300 skills + hooks, rules, memory, installers for many agents | 17 single-purpose skills without hooks (security, research, context, API/DB). Its own installer and hooks are **not** used: they change settings broadly and overlap with OMNIS | **Adapt subset**; reject the installer and hooks |
| GitHub Spec Kit | github.com/github/spec-kit | ★151,937 · MIT · pushed 2026-11-26 | Spec-driven development CLI (`specify`) with templates | The idea of spec → plan → tasks matches OMNIS DEEP mode. It's a CLI/workflow, not a drop-in skill | **Reject as a skill**; point users to it for greenfield SDD |
| gstack | github.com/garrytan/gstack | ★142,774 · MIT · pushed 2026-11-27 | 23 opinionated role tools plus a browser daemon (bun) | `context-save` / `context-restore` and `guard`/`careful` validate OMNIS checkpoint + guard ideas. Needs bun, a monolithic setup and a browser daemon | **Reject install**; ideas adopted |
| awesome-claude-code (hesreallyhim) | github.com/hesreallyhim/awesome-claude-code | ★58,903 · license NOASSERTION · active | Curated list | Discovery source for future catalog entries | **Reference** |
| awesome-claude-code (ianwieds) | github.com/ianwieds/awesome-claude-code | ★2 · CC0 · active | Curated list (new, small) | — | **Reference** (low signal) |
| awesome-claude-skills (travisvn) | github.com/travisvn/awesome-claude-skills | ★15,953 · pushed 2026-04-28 | Curated list | — | Reference; not updated for 7 months |
| skills.sh | skills.sh | not fetched (no API used) | Skill directory/installer | Could be a future discovery source | Not evaluated in depth |
| wshobson/agents | github.com/wshobson/agents | ★42,970 · MIT | Plugins/agents bundles | Plugin-format, not loose skills; would duplicate many entries | Reject for now |

## Context / token tools

| Candidate | URL | Health | What it does | Decision |
|---|---|---|---|---|
| sqz | github.com/ojuschugh1/sqz | ★680 · Apache-2.0 · 2026-11-12 | Compresses tool output before it enters context | Same goal as `output_filter.py`. OMNIS implements its own rule-based filter (stdlib, no proxy, keeps the full log). **Reject install** |
| chop | github.com/AgusRdz/chop | ★48 · MIT | CLI output compressor | Same reasoning; low adoption. **Reject** |
| squeezr | github.com/sergioramosv/squeezr | ★34 · no license | Proxy that uses Haiku to compress context | Routes traffic through a proxy, has no license and its LLM rewriting can drop details. **Reject** |
| graphify | github.com/Graphify-Labs/graphify | ★154,054 · Apache-2.0 | Turns a codebase into a knowledge graph | Heavier than OMNIS' index; worth evaluating for very large repos. **Later** |
| ccusage | (repo moved; not re-resolved) | — | Usage reports from local transcripts | OMNIS `usage_monitor.py` reads the same local data independently. **Not needed** |

## Claude Code capabilities relied on

- **Skills**: `~/.claude/skills/<name>/SKILL.md` (global) or `.claude/skills/` (project); frontmatter `name` and `description`. Only the description is always loaded; the body and other files load on demand. This is why OMNIS keeps SKILL.md small and splits engines into separate files.
- **Hooks**: PreToolUse hooks receive the tool call as JSON on stdin and can return `permissionDecision` of `allow`, `deny` or `ask`. Used by `guard.py`.
- **Scheduling**: the CronCreate tool and `/loop` are session-scoped (they need the session open). `/schedule` creates cloud routines. The OS scheduler is the fallback when Claude is closed.
- **Transcripts**: `~/.claude/projects/<project>/<session>.jsonl` records `message.usage` per API response. These are real token counts. Plan limits and server reset times are not in local data.

## Not verified

- Official docs pages were not fetched in this pass; the capabilities above are based on Claude Code behavior observed in this environment (transcript format inspected, tools available).
- skills.sh and ccusage were not re-checked.
