# OMNIS

An engineering layer for Claude Code. It cuts wasted context, keeps work verifiable and safe, and adds memory, usage tracking, reminders and a vetted skill installer. Python 3.8+ stdlib only.

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
