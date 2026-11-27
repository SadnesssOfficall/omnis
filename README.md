<div align="center">

<sub><b>English</b> · <a href="README.tr.md">Türkçe</a> · <a href="README.de.md">Deutsch</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ar.md">العربية</a></sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-light.svg"><img src="assets/readme/hero-dark.svg" width="100%" alt="OMNIS — one context-efficient, safe engineering layer for every AI coding tool" /></picture>

<sub><b><a href="#what">WHAT</a> &nbsp;·&nbsp; <a href="#features">FEATURES</a> &nbsp;·&nbsp; <a href="#demo">DEMO</a> &nbsp;·&nbsp; <a href="#tools">TOOLS</a> &nbsp;·&nbsp; <a href="#start">START</a> &nbsp;·&nbsp; <a href="#commands">COMMANDS</a> &nbsp;·&nbsp; <a href="#numbers">NUMBERS</a> &nbsp;·&nbsp; <a href="#safety">SAFETY</a> &nbsp;·&nbsp; <a href="#faq">FAQ</a></b></sub>

<br/><br/>

**OMNIS** is an engineering layer that sits under your AI coding tool.<br/>
It reads less, filters noise, remembers what it learned, checks its own work and asks before anything dangerous.<br/>
<sub>Python 3.8+ · standard library only · MIT · v1.2.0</sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="what"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-what-light.svg"><img src="assets/readme/title-what-dark.svg" width="100%" alt="WHAT" /></picture>

</div>

AI coding agents burn most of their context on orientation: whole-file reads, `grep` floods, 3,000-line test logs. OMNIS gives them cheaper ways to get the same answer, plus the parts a long-running agent needs to stay trustworthy.

- **Claude Code first.** A skill (`SKILL.md`, about 60 lines, always loaded) routes each task to FAST, STANDARD, DEEP or DEBUG mode and loads workflows and engines only when needed.
- **Every other tool through MCP.** One shared engine in `~/.omnis/app`, exposed by a stdlib MCP server, wired into Codex, Gemini CLI, Cursor, VS Code Copilot and more by one installer.
- **One entry point.** `python scripts/omnis.py <command>`. No dependencies, no build step, no network calls unless you ask for a skill install.
- **Per-project state** lives in `<project>/.omnis/` (gitignore it).

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="features"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-features-light.svg"><img src="assets/readme/title-features-dark.svg" width="100%" alt="FEATURES" /></picture>

<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-map-light.svg"><img src="assets/readme/card-map-dark.svg" width="49%" alt="Map, find, outline, deps" /></picture></a>
<a href="docs/BENCHMARKS.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-filter-light.svg"><img src="assets/readme/card-filter-dark.svg" width="49%" alt="Output filter" /></picture></a>
<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-memory-light.svg"><img src="assets/readme/card-memory-dark.svg" width="49%" alt="Memory and known bugs" /></picture></a>
<a href="workflows/deep.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-checkpoint-light.svg"><img src="assets/readme/card-checkpoint-dark.svg" width="49%" alt="Checkpoints" /></picture></a>
<a href="engines/automation.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-usage-light.svg"><img src="assets/readme/card-usage-dark.svg" width="49%" alt="Usage and reminders" /></picture></a>
<a href="docs/SECURITY.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-security-light.svg"><img src="assets/readme/card-security-dark.svg" width="49%" alt="Security scan and guard hook" /></picture></a>
<a href="config/skill-catalog.json"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-skills-light.svg"><img src="assets/readme/card-skills-dark.svg" width="49%" alt="Skill manager and registry" /></picture></a>
<a href="docs/tr/MCP.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-mcp-light.svg"><img src="assets/readme/card-mcp-dark.svg" width="49%" alt="MCP server" /></picture></a>
<a href="install.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-install-light.svg"><img src="assets/readme/card-install-dark.svg" width="49%" alt="Multi-tool installer" /></picture></a>
<a href="docs/tr/GENEL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-os-light.svg"><img src="assets/readme/card-os-dark.svg" width="49%" alt="Developer OS" /></picture></a>
<a href="scripts/gateway_filter.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-gateway-light.svg"><img src="assets/readme/card-gateway-dark.svg" width="49%" alt="9Router gateway filter" /></picture></a>
<a href="workflows/debug.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-verify-light.svg"><img src="assets/readme/card-verify-dark.svg" width="49%" alt="Verify" /></picture></a>

<sub>Every card opens its docs or source.</sub>

</div>

<details>
<summary><b>What each piece does</b> &nbsp;<sub>one line per feature</sub></summary>
<br/>

| Feature | What it does |
|---|---|
| **map** | Cached project map: languages, frameworks, package managers, run/build/test commands, entry points, tests. Monorepo-aware. Never reads `.env` contents. |
| **find · outline · deps** | Incremental symbol index. Python via AST (confidence `high`), JS/TS/Go/Rust/Java/C#/PHP/Ruby via regex (`medium`). `deps` shows imports and who imports a file. |
| **filter** | Runs a command, shows only errors, traces, locations and summaries, saves the full log and keeps the exit code. |
| **verify** | Changed files → related tests → checks. With `--run` it runs them and reports VERIFIED or FAILED. Flags secret-like files. |
| **memory** | Project facts (decisions, conventions, architecture) with expiry and source checks, plus a bug-pattern store: `memory bug match "<error>"`. |
| **checkpoint** | Saves task, done and next steps; `resume` in a new session also shows git changes since the save. |
| **usage · reminder** | Real token usage from local Claude Code transcripts, a heuristic 5h window, limit messages. Recurring reminders with quiet hours, max count and expiry, via CronCreate, `/schedule` or the OS scheduler. |
| **security · guard** | Secret detection with redaction, command risk classes, and an optional PreToolUse hook that denies catastrophic commands and asks before risky ones. |
| **skills · audit · registry** | Curated catalog (30 skills, 8 presets) installed from pinned commits after a static audit, with a lock file, conflict check, update and removal. |
| **MCP server** | `scripts/mcp_server.py`: stdlib JSON-RPC over stdio, or loopback streamable HTTP with a bearer token. Output is always secret-redacted. |
| **installer** | `install.py --target …` for 12 tools. Dry run by default, backs up every file, idempotent, keeps foreign entries, has `--uninstall`. |
| **Developer OS** | `/omnis setup` for Claude Code: 14 specialist agents, 30 commands, cheap hooks, read-only automation, pinned MCP servers, one-step rollback. |
| **gateway filter** | `scripts/gateway_filter.py`: an opt-in OpenAI/Anthropic-compatible proxy in front of 9Router that masks secrets in outgoing messages. |

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="demo"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-demo-light.svg"><img src="assets/readme/title-demo-dark.svg" width="100%" alt="DEMO" /></picture>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/demo-light.svg"><img src="assets/readme/demo-dark.svg" width="100%" alt="Terminal: omnis map, find, deps, filter and security classify on a small Next.js sample project" /></picture>

<sub>Real output on a 5-file Next.js sample project. Only the absolute path is shortened to <code>~/shop</code>.</sub>

</div>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="tools"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-tools-light.svg"><img src="assets/readme/title-tools-dark.svg" width="100%" alt="TOOLS" /></picture>

</div>

One engine, exposed as a Claude Code skill and as an MCP server for everything else. MCP tools: `map`, `find`, `outline`, `deps`, `filter`, `verify`, `doctor`, `security_scan`, `security_classify`, `memory_get`/`memory_add`, `checkpoint_save`/`checkpoint_resume`, `usage`. `filter` refuses risky commands.

**Status legend:** **Tested** = covered by the test suite and used · **Config tested** = the installer's file changes are tested against a temp home; the live client was not checked · **Written, not tested** = built from the tool's docs only.

| Tool | What works | Where OMNIS writes | Shell guard | Status |
|---|---|---|---|---|
| Claude Code | Everything: skill, CLI, Developer OS | `~/.claude/skills/omnis` | PreToolUse hook: deny + ask | Tested |
| Codex CLI / app | MCP tools, global guidance | `~/.codex/config.toml`, `~/.codex/AGENTS.md` | `rules/omnis.rules` (prefix match) + PreToolUse hook (deny only) | Config tested |
| Gemini CLI | MCP tools, guidance | `~/.gemini/settings.json`, `GEMINI.md` | BeforeTool hook: deny only | Config tested |
| Antigravity | MCP tools, global rules | `~/.gemini/antigravity/mcp_config.json` | none (no hook API) | Config tested |
| Cursor | MCP tools, project rule | `~/.cursor/mcp.json`, `.cursor/rules/omnis.mdc` | `hooks.json` beforeShellExecution | Config tested |
| VS Code Copilot | MCP tools (agent mode), instructions | `Code/User/mcp.json`, `prompts/omnis.instructions.md` | none (Copilot's own confirmation) | Config tested |
| Windsurf | MCP tools, global rules | `~/.codeium/windsurf/mcp_config.json` | none | Config tested |
| Cline / Roo | MCP tools | their `mcp_settings.json` | none (their own approval UI) | Written, not tested |
| OpenCode | MCP tools, guidance | `~/.config/opencode/opencode.json`, `AGENTS.md` | none (use its `permission` config) | Config tested |
| Continue | MCP tools | `~/.continue/mcpServers/omnis.yaml` | none | Config tested |
| Any AGENTS.md tool | Rules text | `--target agents --project DIR` | text only | Tested |
| ChatGPT web / desktop | **Not directly.** Connectors need a remote MCP over HTTPS | `mcp_server.py --http`: loopback only, bearer token, Origin check, `filter` off unless `--allow-exec` | n/a | Written, not tested |
| 9Router gateway | Secret masking for clients that opt in | `gateway_filter.py` on `:20129` in front of `:20128` | masks outgoing secrets | Tested (proxy unit test) |

<details>
<summary><b>Why a separate proxy for 9Router</b></summary>
<br/>

9Router (0.5.123) has no general MCP hub: its MCP plugins are a hard-coded list and its "managed MCP" list is only pushed into Claude Cowork config. It has no system-prompt injection or request-filter plugin API. So OMNIS doesn't patch 9Router (an npm update would wipe the patch). It runs `gateway_filter.py` as a separate, opt-in proxy: clients that want secret masking use `http://127.0.0.1:20129/v1` instead of `:20128/v1`.

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="start"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-start-light.svg"><img src="assets/readme/title-start-dark.svg" width="100%" alt="START" /></picture>

</div>

Clone the repo, then pick your tool. Use `python` on Windows, `python3` on macOS/Linux. Every target is a **dry run** until you add `--yes`.

```bash
python3 install.py --yes                      # Claude Code skill → ~/.claude/skills/omnis
python3 install.py --with-hook --yes          # + safety hook in ~/.claude/settings.json (backed up first)
python3 install.py --os --yes                 # Claude Code Developer OS (same as /omnis setup)
python3 install.py --list-targets             # what is detected on this machine
python3 install.py --target codex --yes       # one tool: codex, gemini, antigravity, cursor, vscode,
                                              #   windsurf, cline, roo, opencode, continue, chatgpt
python3 install.py --target all --yes         # every detected tool
python3 install.py --target agents --project DIR --yes   # AGENTS.md block in one repo
python3 install.py --verify                   # run the test suite on the installed copy
```

Inside Claude Code, after a restart:

```text
/omnis setup      audit → plan → backup → install → validate → report (Turkish)
/omnis durum      health check
/omnis geri-al    roll back the last setup   (omnis rollback list · omnis rollback <ts>)
/omnis map        start working
```

**Rolling back.** Each `/omnis setup` saves `settings.json`, `CLAUDE.md` and a `manifest.json` to `~/.claude/omnis/backups/<ts>/`. Rollback restores those two files, deletes OMNIS-marked agents and commands, removes the MCP servers and scheduled jobs it added, and leaves your own files alone. For other tools: `install.py --target <tool> --uninstall --yes`. Backups stay in `~/.omnis/backups/<ts>/`.

<sub>Windows: designed for it (stdlib only, UTF-8 console, `schtasks`, PowerShell rules in the guard), see <a href="docs/WINDOWS.md">docs/WINDOWS.md</a>.</sub>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="commands"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-commands-light.svg"><img src="assets/readme/title-commands-dark.svg" width="100%" alt="COMMANDS" /></picture>

</div>

<details>
<summary><b>CLI</b> &nbsp;<sub><code>python scripts/omnis.py …</code></sub></summary>
<br/>

| Command | What it does |
|---|---|
| `map [ROOT] [--refresh]` | Project map (cached) |
| `find NAME` · `outline FILE` · `deps FILE` | Symbol lookup, file outline, import graph |
| `index [ROOT]` | Build or refresh the symbol index |
| `filter "<cmd>"` | Run a command, show only what matters |
| `verify [--run]` | Checks for the current changes |
| `doctor` | OS, shell, tools, disk; env var names only |
| `security scan\|diff\|classify` | Secrets and command risk |
| `memory add\|search\|inspect\|cleanup` · `memory bug add\|match` | Project memory and bug patterns |
| `checkpoint save\|resume\|list` | Task checkpoints |
| `usage [status\|report\|setup\|limits]` | Token usage from local transcripts |
| `reminder add\|list\|pause\|resume\|set\|remove\|cron\|os-install` | Recurring reminders |
| `skills presets\|search\|plan\|install\|list\|conflicts\|update\|remove` | External skill catalog and installer |
| `audit PATH` | Static security audit of a skill folder |
| `benchmark repo\|filter\|sessions` | Measure savings |
| `setup` · `durum` · `geri-al [TS]` | Developer OS: install + validate, health, rollback |
| `os-audit` | What is installed, duplicates, conflicts |
| `registry [--dupes]` | Skill registry |
| `adapt [ROOT]` | Stack detection and relevant skills |
| `automation …` | Read-only scheduled jobs with a notification |
| `clean [ROOT]` | Delete this project's caches (keeps memory and checkpoints) |

</details>

<details>
<summary><b>Claude Code slash commands</b> &nbsp;<sub>installed by <code>/omnis setup</code></sub></summary>
<br/>

Names that collide with built-in or plugin commands get an `omnis-` prefix. Files you wrote yourself are never touched.

| Command | What it does |
|---|---|
| `/analyze` | Understand an area before changing it |
| `/omnis-plan` | A plan where every step is verifiable (DEEP mode) |
| `/implement` | End to end: plan, edit, test, verify |
| `/omnis-debug` | Root cause, fix, regression test, save the bug to memory |
| `/audit` | General health audit, changes nothing |
| `/omnis-security` | Security review of a diff or area |
| `/omnis-review` | Review the diff with the code-reviewer agent |
| `/test` | Run only the tests the change touches |
| `/optimize` | Measure, fix, measure again |
| `/refactor` | Restructure without changing behaviour |
| `/omnis-docs` | Write docs from the real code |
| `/release` · `/deploy` | Prepare a release / deploy, both ask first |
| `/cleanup` | List dead code and files, delete only on approval |
| `/research` | Answer from official sources, with citations |
| `/project-onboard` | Detect the stack, suggest skills and agents |
| `/task-report` | Report status and save a checkpoint |
| `/skills-discover` `/skills-install` `/skills-update` `/skills-audit` `/skills-remove` `/skills-list` | Skill catalog and registry |
| `/automation-status` `/automation-add` `/automation-pause` `/automation-resume` `/automation-remove` `/automation-config` `/automation-run` | Automation manager |

</details>

<details>
<summary><b>Agents, hooks and automation</b> &nbsp;<sub>Developer OS</sub></summary>
<br/>

**Agents** (`~/.claude/agents/`, skipped if a plugin or your own file has the same name)
- Read-only: architect, security-auditor, code-reviewer, debugger, performance, ui-ux, research.
- Editing: developer, frontend, backend, database, docs, qa (test files only), devops (config only, never deploys).
- No agents for small tasks; two agents never edit the same file; code-reviewer runs after code is written, security-auditor too when auth, payments, files or shell code changed.

**Hooks** (`scripts/os_hooks.py`; a failing hook never breaks the session)

| Event | What it does |
|---|---|
| PreToolUse Bash/PowerShell | `guard.py`: block catastrophic commands, ask before risky ones |
| PreToolUse Edit/Write | Ask before writing `.env*`, key and lock files |
| PostToolUse Edit/Write | Scan the edited file for secrets; run prettier/eslint if the project has them |
| Stop | `tsc --noEmit` if .ts/.tsx changed (blocks a turn at most once); notification after long tasks |
| SessionStart · PreCompact | Restore / save the task checkpoint |

**Automation** (`scripts/automation.py`, Windows Task Scheduler as `OMNIS\<id>`): `skill-update-check`, `dependency-advisories`, `repo-health`. Intervals 1, 2, 3, 5 (default), 8, 12 or 24 h. Jobs only read, write a report to `~/.omnis/reports/` and show a notification.

**MCP servers** added by setup (no credentials, pinned): `@upstash/context7-mcp@4.6.0`, `@playwright/mcp@0.0.84`.

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="numbers"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-numbers-light.svg"><img src="assets/readme/title-numbers-dark.svg" width="100%" alt="NUMBERS" /></picture>

</div>

From [docs/BENCHMARKS.md](docs/BENCHMARKS.md) (2026-11-27, Linux, Python 3.13). Bytes are measured; token figures are estimates (bytes ÷ 4). Reproduce with `omnis.py benchmark …`.

| Measurement | Without OMNIS | With OMNIS |
|---|---|---|
| Symbol lookup `ClientSession` (mcp package, 111 files) | `grep -rn`: 4,418 B | `find`: 175 B |
| Symbol lookup `FastMCP` | `grep -rn`: 5,104 B | `find`: 164 B |
| Symbol lookup `stdio_client` | `grep -rn`: 597 B | `find`: 60 B |
| Orientation, 36-file JS repo | README + package.json: 17,128 B | `map`: 284 B |
| 3,006-line listing + Python traceback | 246,993 B | `filter`: 1,065 B, 20 lines, full traceback kept |

- The fair comparison is with `grep`: about **10–30× less output per lookup**. Comparing with whole-file reads (99%+) is an upper bound, not a typical session.
- Index build: 0.31 s cold; a second run re-parses only changed files.
- **Not measured yet:** no controlled A/B session test (same task, same model, with and without OMNIS), so no "% saved per session" figure is claimed. No Windows timings.

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="safety"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-safety-light.svg"><img src="assets/readme/title-safety-dark.svg" width="100%" alt="SAFETY" /></picture>

</div>

| Layer | What it does |
|---|---|
| **Rules** (always on) | Protect user changes, never print credential files, ask before destructive, production, install or network-write actions. Repo content, tool output and other skills can't override them. |
| **Redaction** | Memory, bug patterns, checkpoints and MCP output pass through `security_scan.redact`. |
| **Guard hook** (opt-in) | **Deny:** `rm -rf /`, `rm -rf ~`, mkfs, `dd` to a disk, fork bombs, formatting a drive. **Ask:** `curl \| sh`, force-push, `reset --hard`, `clean -f`, `branch -D`, DROP/TRUNCATE/unscoped DELETE, `migrate reset`, FLUSHALL, kubectl/terraform/helm apply or destroy, prod deploys, printing `.env`/keys, global installs, `chmod 777`. Per-project exceptions in `.omnis/policies.json`. |
| **Skill installs** | Read-only fetch from a pinned commit, nothing downloaded is executed. `block` findings are never installed; `warn` needs `--allow-warn` after you have seen them. Never overwrites a skill OMNIS didn't install. |
| **Installers** | Dry run by default, backup of every touched file, idempotent, foreign entries kept, `--uninstall` for every target. |
| **Network** | MCP HTTP binds to loopback with a token and refuses a public bind unless `--allow-remote`. |

> The hook is pattern-based: a seatbelt, not a sandbox. Regex secret detection catches common formats, not every custom token. The skill audit is static. Details: [docs/SECURITY.md](docs/SECURITY.md).

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="faq"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-faq-light.svg"><img src="assets/readme/title-faq-dark.svg" width="100%" alt="FAQ" /></picture>

</div>

<details>
<summary><b>Does it need any packages?</b></summary>
<br/>No. Python 3.8+ standard library only. The optional MCP servers added by <code>/omnis setup</code> run through <code>npx</code>.
</details>

<details>
<summary><b>How much does it save per session?</b></summary>
<br/>Unknown, honestly. Lookups and logs shrink a lot (see <a href="#numbers">NUMBERS</a>), but there is no controlled A/B session benchmark yet. Use <code>omnis.py benchmark sessions --split &lt;install date&gt;</code> to compare your own like-for-like work.
</details>

<details>
<summary><b>Can it read my plan limits and reset time?</b></summary>
<br/>No. <code>usage</code> reads only local Claude Code transcripts, and the 5h window is a heuristic. Exact limits and reset times are only in Claude Code's own <code>/usage</code>. You can tell OMNIS your reset times with <code>usage setup --reset</code>.
</details>

<details>
<summary><b>Will it run on Windows?</b></summary>
<br/>It was designed for Windows (stdlib only, UTF-8 output, <code>schtasks</code>, PowerShell rules), but development and the test suite ran on Linux. Run <code>python install.py --verify</code> before relying on it.
</details>

<details>
<summary><b>How accurate is <code>find</code> outside Python?</b></summary>
<br/>Python uses the AST (<code>high</code>). Other languages use regex (<code>medium</code>), so confirm with a narrow read before a risky edit. <code>deps</code> can't resolve path aliases or dynamic imports.
</details>

<details>
<summary><b>Why can't ChatGPT use it directly?</b></summary>
<br/>ChatGPT connectors need a remote MCP server over HTTPS. OMNIS ships a loopback-only HTTP mode with a token; exposing it to the internet is your decision and your risk.
</details>

<details>
<summary><b>Do reminders work when Claude Code is closed?</b></summary>
<br/>In-session reminders need the session open. OS reminders work with it closed but only send a notification; they don't drive Claude. Cron can't do an exact 5h cycle across midnight.
</details>

<details>
<summary><b>How do I remove everything?</b></summary>
<br/><code>/omnis geri-al</code> for the Developer OS, <code>install.py --uninstall --yes</code> for the skill and hook, <code>install.py --target &lt;tool&gt; --uninstall --yes</code> for each other tool, <code>omnis.py clean</code> for a project's caches.
</details>

<details>
<summary><b>What's next?</b></summary>
<br/>A/B benchmark harness · Windows CI · tree-sitter parsers for TS/Go · test-impact selection from coverage data · more catalog sources after audit.
</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<sub>Docs: <a href="SKILL.md">SKILL.md</a> · <a href="docs/BENCHMARKS.md">BENCHMARKS</a> · <a href="docs/SECURITY.md">SECURITY</a> · <a href="docs/WINDOWS.md">WINDOWS</a> · <a href="docs/ECOSYSTEM_RESEARCH.md">ECOSYSTEM_RESEARCH</a> · <a href="docs/tr/GENEL.md">docs/tr</a> · <a href="CHANGELOG.md">CHANGELOG</a></sub>

<sub><a href="LICENSE">MIT License</a> · SVG art is generated by <a href="tools/readme_assets.py">tools/readme_assets.py</a></sub>

</div>
