<div align="center">

<sub><a href="README.md">English</a> · <a href="README.tr.md">Türkçe</a> · <a href="README.de.md">Deutsch</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.ru.md">Русский</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.ar.md">العربية</a></sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-light.svg"><img src="assets/readme/hero-dark.svg" width="100%" alt="OMNIS —— 面向所有 AI 编程工具的、节省上下文且安全的工程层" /></picture>

<sub><b><a href="#what">简介</a> &nbsp;·&nbsp; <a href="#features">功能</a> &nbsp;·&nbsp; <a href="#demo">演示</a> &nbsp;·&nbsp; <a href="#tools">工具支持</a> &nbsp;·&nbsp; <a href="#start">快速开始</a> &nbsp;·&nbsp; <a href="#commands">命令</a> &nbsp;·&nbsp; <a href="#numbers">数据</a> &nbsp;·&nbsp; <a href="#safety">安全</a> &nbsp;·&nbsp; <a href="#faq">FAQ</a></b></sub>

<br/><br/>

**OMNIS** 是一层位于 AI 编程工具之下的工程层。<br/>
它读得更少、过滤噪音、记住学到的东西、检查自己的工作，并在任何危险操作前先询问。<br/>
<sub>Python 3.8+ · 仅标准库 · MIT · v1.2.0</sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="what"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-what-light.svg"><img src="assets/readme/title-what-dark.svg" width="100%" alt="简介" /></picture>

</div>

AI 编程 agent 把大部分上下文花在“摸清情况”上：整文件读取、成片的 `grep` 输出、3,000 行的测试日志。OMNIS 用更便宜的方式拿到同样的答案，并补上长时间运行的 agent 保持可信所需的部件。

- **Claude Code 优先。** 一个常驻加载的 skill（`SKILL.md`，约 60 行）把每个任务分派到 FAST、STANDARD、DEEP 或 DEBUG 模式，只在需要时才加载 workflows 和 engines。
- **其他工具一律走 MCP。** `~/.omnis/app` 中只有一个共享引擎，通过纯标准库实现的 MCP 服务器对外提供，由同一个安装器接入 Codex、Gemini CLI、Cursor、VS Code Copilot 等。
- **唯一入口。** `python scripts/omnis.py <命令>`。无依赖、无构建步骤；除非你要求安装 skill，否则不发任何网络请求。
- **项目级状态** 存放在 `<项目>/.omnis/`（请加入 `.gitignore`）。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="features"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-features-light.svg"><img src="assets/readme/title-features-dark.svg" width="100%" alt="功能" /></picture>

<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-map-light.svg"><img src="assets/readme/card-map-dark.svg" width="49%" alt="Map、find、outline、deps" /></picture></a>
<a href="docs/BENCHMARKS.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-filter-light.svg"><img src="assets/readme/card-filter-dark.svg" width="49%" alt="输出过滤" /></picture></a>
<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-memory-light.svg"><img src="assets/readme/card-memory-dark.svg" width="49%" alt="记忆与已知 bug" /></picture></a>
<a href="workflows/deep.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-checkpoint-light.svg"><img src="assets/readme/card-checkpoint-dark.svg" width="49%" alt="检查点" /></picture></a>
<a href="engines/automation.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-usage-light.svg"><img src="assets/readme/card-usage-dark.svg" width="49%" alt="用量与提醒" /></picture></a>
<a href="docs/SECURITY.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-security-light.svg"><img src="assets/readme/card-security-dark.svg" width="49%" alt="安全扫描与 guard hook" /></picture></a>
<a href="config/skill-catalog.json"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-skills-light.svg"><img src="assets/readme/card-skills-dark.svg" width="49%" alt="Skill 管理器与注册表" /></picture></a>
<a href="docs/tr/MCP.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-mcp-light.svg"><img src="assets/readme/card-mcp-dark.svg" width="49%" alt="MCP 服务器" /></picture></a>
<a href="install.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-install-light.svg"><img src="assets/readme/card-install-dark.svg" width="49%" alt="多工具安装器" /></picture></a>
<a href="docs/tr/GENEL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-os-light.svg"><img src="assets/readme/card-os-dark.svg" width="49%" alt="Developer OS" /></picture></a>
<a href="scripts/gateway_filter.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-gateway-light.svg"><img src="assets/readme/card-gateway-dark.svg" width="49%" alt="9Router 网关过滤器" /></picture></a>
<a href="workflows/debug.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-verify-light.svg"><img src="assets/readme/card-verify-dark.svg" width="49%" alt="Verify" /></picture></a>

<sub>每张卡片都链接到对应的文档或源码。</sub>

</div>

<details>
<summary><b>各部分的作用</b> &nbsp;<sub>每个功能一行</sub></summary>
<br/>

| 功能 | 作用 |
|---|---|
| **map** | 带缓存的项目地图：语言、框架、包管理器、run/build/test 命令、入口点、测试。支持 monorepo。从不读取 `.env` 的内容。 |
| **find · outline · deps** | 增量符号索引。Python 用 AST（置信度 `high`），JS/TS/Go/Rust/Java/C#/PHP/Ruby 用正则（`medium`）。`deps` 显示一个文件的导入以及谁导入了它。 |
| **filter** | 运行命令，只显示错误、堆栈、位置和摘要，保存完整日志并保留退出码。 |
| **verify** | 改动的文件 → 相关测试 → 检查项。加 `--run` 会实际运行并报告 VERIFIED 或 FAILED。会标出疑似密钥的文件。 |
| **memory** | 带过期时间和来源校验的项目事实（决策、约定、架构），以及 bug 模式库：`memory bug match "<错误>"`。 |
| **checkpoint** | 保存任务、已完成和下一步；在新会话中 `resume` 还会显示此后的 git 变更。 |
| **usage · reminder** | 从本地 Claude Code 会话记录统计真实 token 用量、启发式 5 小时窗口、限额消息。支持免打扰时段、最大次数和截止时间的周期提醒，可通过 CronCreate、`/schedule` 或系统计划任务运行。 |
| **security · guard** | 带脱敏的密钥检测、命令风险分级，以及可选的 PreToolUse hook：拦截灾难性命令，对高风险命令先询问。 |
| **skills · audit · registry** | 精选目录（30 个 skill、8 个预设），经静态审计后从固定 commit 安装，带 lock 文件、冲突检查、更新和移除。 |
| **MCP 服务器** | `scripts/mcp_server.py`：基于标准库的 stdio JSON-RPC，或带 bearer token 的 loopback streamable HTTP。输出始终脱敏。 |
| **安装器** | `install.py --target …` 支持 12 个工具。默认演练模式，备份每个文件，幂等，保留他人配置项，提供 `--uninstall`。 |
| **Developer OS** | 面向 Claude Code 的 `/omnis setup`：14 个专职 agent、30 条命令、轻量 hook、只读自动化、固定版本的 MCP 服务器、一步回滚。 |
| **网关过滤器** | `scripts/gateway_filter.py`：置于 9Router 之前、兼容 OpenAI/Anthropic 的可选代理，对发出的消息中的密钥进行脱敏。 |

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="demo"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-demo-light.svg"><img src="assets/readme/title-demo-dark.svg" width="100%" alt="演示" /></picture>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/demo-light.svg"><img src="assets/readme/demo-dark.svg" width="100%" alt="终端：在一个小型 Next.js 示例项目上运行 omnis map、find、deps、filter 和 security classify" /></picture>

<sub>在 5 个文件的 Next.js 示例项目上的真实输出，仅将绝对路径缩写为 <code>~/shop</code>。</sub>

</div>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="tools"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-tools-light.svg"><img src="assets/readme/title-tools-dark.svg" width="100%" alt="工具支持" /></picture>

</div>

同一个引擎：在 Claude Code 中是 skill，对其他工具是 MCP 服务器。MCP 工具：`map`、`find`、`outline`、`deps`、`filter`、`verify`、`doctor`、`security_scan`、`security_classify`、`memory_get`/`memory_add`、`checkpoint_save`/`checkpoint_resume`、`usage`。`filter` 会拒绝高风险命令。

**状态说明：** **已测试** = 有测试覆盖且实际在用 · **配置已测试** = 安装器对文件的修改已在临时 home 中测试，未在真实客户端中验证 · **已编写，未测试** = 仅依据该工具文档实现。

| 工具 | 可用功能 | OMNIS 写入位置 | Shell 防护 | 状态 |
|---|---|---|---|---|
| Claude Code | 全部：skill、CLI、Developer OS | `~/.claude/skills/omnis` | PreToolUse hook：拦截 + 询问 | 已测试 |
| Codex CLI / app | MCP 工具、全局指引 | `~/.codex/config.toml`、`~/.codex/AGENTS.md` | `rules/omnis.rules`（前缀匹配）+ PreToolUse hook（仅拦截） | 配置已测试 |
| Gemini CLI | MCP 工具、指引 | `~/.gemini/settings.json`、`GEMINI.md` | BeforeTool hook：仅拦截 | 配置已测试 |
| Antigravity | MCP 工具、全局规则 | `~/.gemini/antigravity/mcp_config.json` | 无（没有 hook API） | 配置已测试 |
| Cursor | MCP 工具、项目规则 | `~/.cursor/mcp.json`、`.cursor/rules/omnis.mdc` | `hooks.json` beforeShellExecution | 配置已测试 |
| VS Code Copilot | MCP 工具（agent 模式）、指令 | `Code/User/mcp.json`、`prompts/omnis.instructions.md` | 无（使用 Copilot 自带确认） | 配置已测试 |
| Windsurf | MCP 工具、全局规则 | `~/.codeium/windsurf/mcp_config.json` | 无 | 配置已测试 |
| Cline / Roo | MCP 工具 | 各自的 `mcp_settings.json` | 无（使用其自带审批界面） | 已编写，未测试 |
| OpenCode | MCP 工具、指引 | `~/.config/opencode/opencode.json`、`AGENTS.md` | 无（请使用其 `permission` 配置） | 配置已测试 |
| Continue | MCP 工具 | `~/.continue/mcpServers/omnis.yaml` | 无 | 配置已测试 |
| 任何读取 AGENTS.md 的工具 | 规则文本 | `--target agents --project DIR` | 仅文本 | 已测试 |
| ChatGPT 网页版 / 桌面版 | **无法直接使用。** Connector 需要通过 HTTPS 访问的远程 MCP | `mcp_server.py --http`：仅 loopback、bearer token、Origin 校验，未加 `--allow-exec` 时关闭 `filter` | – | 已编写，未测试 |
| 9Router 网关 | 为主动接入的客户端做密钥脱敏 | 在 `:20128` 前的 `:20129` 上运行 `gateway_filter.py` | 对发出的密钥脱敏 | 已测试（代理单元测试） |

<details>
<summary><b>为什么 9Router 要用独立代理</b></summary>
<br/>

9Router（0.5.123）没有通用的 MCP hub：它的 MCP 插件是写死的列表，"managed MCP" 列表也只会推送到 Claude Cowork 的配置里；它也没有用于注入 system prompt 或过滤请求的插件 API。因此 OMNIS 不修补 9Router（npm 更新会抹掉补丁），而是把 `gateway_filter.py` 作为独立、可选的代理运行：需要脱敏的客户端把 `:20128/v1` 换成 `http://127.0.0.1:20129/v1` 即可。

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="start"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-start-light.svg"><img src="assets/readme/title-start-dark.svg" width="100%" alt="快速开始" /></picture>

</div>

克隆仓库，然后选择你的工具。Windows 用 `python`，macOS/Linux 用 `python3`。在加上 `--yes` 之前，每个目标都只是**演练**。

```bash
python3 install.py --yes                      # Claude Code skill → ~/.claude/skills/omnis
python3 install.py --with-hook --yes          # + 在 ~/.claude/settings.json 中加入安全 hook（先备份）
python3 install.py --os --yes                 # Claude Code Developer OS（等同于 /omnis setup）
python3 install.py --list-targets             # 本机检测到哪些工具
python3 install.py --target codex --yes       # 单个工具：codex, gemini, antigravity, cursor, vscode,
                                              #   windsurf, cline, roo, opencode, continue, chatgpt
python3 install.py --target all --yes         # 所有检测到的工具
python3 install.py --target agents --project DIR --yes   # 在单个仓库中写入 AGENTS.md 区块
python3 install.py --verify                   # 在已安装副本上运行测试套件
```

重启 Claude Code 后：

```text
/omnis setup      审计 → 计划 → 备份 → 安装 → 验证 → 报告（土耳其语）
/omnis durum      健康检查
/omnis geri-al    回滚上一次安装   (omnis rollback list · omnis rollback <ts>)
/omnis map        开始工作
```

**回滚。** 每次 `/omnis setup` 都会把 `settings.json`、`CLAUDE.md` 和 `manifest.json` 保存到 `~/.claude/omnis/backups/<ts>/`。回滚会恢复这两个文件，删除带 OMNIS 标记的 agent 和命令，移除它添加的 MCP 服务器和计划任务，不会动你自己的文件。其他工具：`install.py --target <工具> --uninstall --yes`。备份保留在 `~/.omnis/backups/<ts>/`。

<sub>Windows：按 Windows 设计（仅标准库、UTF-8 控制台、<code>schtasks</code>、guard 中的 PowerShell 规则），见 <a href="docs/WINDOWS.md">docs/WINDOWS.md</a>。</sub>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="commands"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-commands-light.svg"><img src="assets/readme/title-commands-dark.svg" width="100%" alt="命令" /></picture>

</div>

<details>
<summary><b>CLI</b> &nbsp;<sub><code>python scripts/omnis.py …</code></sub></summary>
<br/>

| 命令 | 作用 |
|---|---|
| `map [ROOT] [--refresh]` | 项目地图（带缓存） |
| `find NAME` · `outline FILE` · `deps FILE` | 符号查找、文件大纲、导入关系图 |
| `index [ROOT]` | 构建或刷新符号索引 |
| `filter "<cmd>"` | 运行命令，只显示要紧的内容 |
| `verify [--run]` | 针对当前改动的检查 |
| `doctor` | 操作系统、shell、工具、磁盘；只列环境变量名 |
| `security scan\|diff\|classify` | 密钥与命令风险 |
| `memory add\|search\|inspect\|cleanup` · `memory bug add\|match` | 项目记忆与 bug 模式 |
| `checkpoint save\|resume\|list` | 任务检查点 |
| `usage [status\|report\|setup\|limits]` | 基于本地会话记录的 token 用量 |
| `reminder add\|list\|pause\|resume\|set\|remove\|cron\|os-install` | 周期提醒 |
| `skills presets\|search\|plan\|install\|list\|conflicts\|update\|remove` | 外部 skill 目录与安装器 |
| `audit PATH` | 对 skill 目录做静态安全审计 |
| `benchmark repo\|filter\|sessions` | 测量节省量 |
| `setup` · `durum` · `geri-al [TS]` | Developer OS：安装 + 验证、健康检查、回滚 |
| `os-audit` | 已安装内容、重复项、冲突 |
| `registry [--dupes]` | Skill 注册表 |
| `adapt [ROOT]` | 技术栈识别与相关 skill |
| `automation …` | 带通知的只读计划任务 |
| `clean [ROOT]` | 删除本项目缓存（保留记忆和检查点） |

</details>

<details>
<summary><b>Claude Code 斜杠命令</b> &nbsp;<sub>由 <code>/omnis setup</code> 安装</sub></summary>
<br/>

与内置或插件命令重名的会加上 `omnis-` 前缀。你自己写的文件绝不会被改动。

| 命令 | 作用 |
|---|---|
| `/analyze` | 修改前先理解某个区域 |
| `/omnis-plan` | 每一步都可验证的计划（DEEP 模式） |
| `/implement` | 端到端：计划、修改、测试、验证 |
| `/omnis-debug` | 找根因、修复、写回归测试、把 bug 存入记忆 |
| `/audit` | 整体健康审计，不做任何修改 |
| `/omnis-security` | 对 diff 或某个区域做安全审查 |
| `/omnis-review` | 用 code-reviewer agent 审查 diff |
| `/test` | 只运行改动涉及的测试 |
| `/optimize` | 先测量、再修复、再测量 |
| `/refactor` | 在不改变行为的前提下重构 |
| `/omnis-docs` | 依据真实代码编写文档 |
| `/release` · `/deploy` | 准备发布 / 部署，两者都会先询问 |
| `/cleanup` | 列出无用代码和文件，经批准才删除 |
| `/research` | 依据官方来源回答，并附引用 |
| `/project-onboard` | 识别技术栈，推荐 skill 和 agent |
| `/task-report` | 汇报状态并保存检查点 |
| `/skills-discover` `/skills-install` `/skills-update` `/skills-audit` `/skills-remove` `/skills-list` | Skill 目录与注册表 |
| `/automation-status` `/automation-add` `/automation-pause` `/automation-resume` `/automation-remove` `/automation-config` `/automation-run` | 自动化管理 |

</details>

<details>
<summary><b>Agent、hook 与自动化</b> &nbsp;<sub>Developer OS</sub></summary>
<br/>

**Agent**（`~/.claude/agents/`；若插件或你自己的文件中已有同名 agent 则跳过）
- 只读：architect、security-auditor、code-reviewer、debugger、performance、ui-ux、research。
- 可编辑：developer、frontend、backend、database、docs、qa（仅测试文件）、devops（仅配置，从不部署）。
- 小任务不用 agent；两个 agent 不会编辑同一文件；写完代码后运行 code-reviewer，若改动涉及认证、支付、文件或 shell 代码，还会运行 security-auditor。

**Hook**（`scripts/os_hooks.py`；hook 出错不会中断会话）

| 事件 | 作用 |
|---|---|
| PreToolUse Bash/PowerShell | `guard.py`：拦截灾难性命令，对高风险命令先询问 |
| PreToolUse Edit/Write | 写入 `.env*`、密钥文件和 lock 文件前先询问 |
| PostToolUse Edit/Write | 扫描被编辑文件中的密钥；项目中有 prettier/eslint 时运行它们 |
| Stop | .ts/.tsx 有改动时运行 `tsc --noEmit`（每轮最多拦截一次）；长任务结束后发送通知 |
| SessionStart · PreCompact | 恢复 / 保存任务检查点 |

**自动化**（`scripts/automation.py`，在 Windows 任务计划程序中以 `OMNIS\<id>` 运行）：`skill-update-check`、`dependency-advisories`、`repo-health`。间隔可选 1、2、3、5（默认）、8、12 或 24 小时。任务只读取数据，将报告写入 `~/.omnis/reports/` 并显示通知。

**setup 添加的 MCP 服务器**（无需凭据，固定版本）：`@upstash/context7-mcp@4.6.0`、`@playwright/mcp@0.0.84`。

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="numbers"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-numbers-light.svg"><img src="assets/readme/title-numbers-dark.svg" width="100%" alt="数据" /></picture>

</div>

来自 [docs/BENCHMARKS.md](docs/BENCHMARKS.md)（2026-11-27，Linux，Python 3.13）。字节数为实测；token 数为估算（字节 ÷ 4）。可用 `omnis.py benchmark …` 复现。

| 测量项 | 不用 OMNIS | 使用 OMNIS |
|---|---|---|
| 查找符号 `ClientSession`（mcp 包，111 个文件） | `grep -rn`：4,418 B | `find`：175 B |
| 查找符号 `FastMCP` | `grep -rn`：5,104 B | `find`：164 B |
| 查找符号 `stdio_client` | `grep -rn`：597 B | `find`：60 B |
| 熟悉项目，36 个文件的 JS 仓库 | README + package.json：17,128 B | `map`：284 B |
| 3,006 行文件列表 + Python traceback | 246,993 B | `filter`：1,065 B，20 行，完整保留 traceback |

- 公平的对比对象是 `grep`：每次查找输出约**少 10–30 倍**。与整文件读取相比（99%+）只是上限，不代表典型会话。
- 索引构建：冷启动 0.31 秒；再次运行只重新解析改动过的文件。
- **尚未测量：** 还没有受控的 A/B 会话测试（同一任务、同一模型，有无 OMNIS），因此不声称任何“每会话节省百分比”。暂无 Windows 下的耗时数据。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="safety"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-safety-light.svg"><img src="assets/readme/title-safety-dark.svg" width="100%" alt="安全" /></picture>

</div>

| 层级 | 作用 |
|---|---|
| **规则**（始终开启） | 保护用户的改动，绝不打印凭据文件，在破坏性、生产环境、安装或网络写入操作前先询问。仓库内容、工具输出和其他 skill 都无法覆盖这些规则。 |
| **脱敏** | 记忆、bug 模式、检查点和 MCP 输出都经过 `security_scan.redact`。 |
| **Guard hook**（可选） | **拦截：** `rm -rf /`、`rm -rf ~`、mkfs、`dd` 写磁盘、fork 炸弹、格式化磁盘。**询问：** `curl \| sh`、force-push、`reset --hard`、`clean -f`、`branch -D`、DROP/TRUNCATE/无条件 DELETE、`migrate reset`、FLUSHALL、kubectl/terraform/helm 的 apply 或 destroy、生产部署、打印 `.env`/密钥、全局安装、`chmod 777`。项目级例外写在 `.omnis/policies.json`。 |
| **Skill 安装** | 从固定 commit 只读拉取，下载的内容一律不执行。有 `block` 结论的绝不安装；`warn` 需要你看过结论后加 `--allow-warn`。绝不覆盖非 OMNIS 安装的 skill。 |
| **安装器** | 默认演练，备份每个被改动的文件，幂等，保留他人配置项，每个目标都支持 `--uninstall`。 |
| **网络** | MCP HTTP 仅在 loopback 上监听并要求 token；未加 `--allow-remote` 时拒绝绑定公网地址。 |

> 该 hook 基于模式匹配：是安全带，不是沙箱。基于正则的密钥检测能识别常见格式，但不能识别所有自定义 token。Skill 审计是静态的。详情见 [docs/SECURITY.md](docs/SECURITY.md)。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="faq"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-faq-light.svg"><img src="assets/readme/title-faq-dark.svg" width="100%" alt="FAQ" /></picture>

</div>

<details>
<summary><b>需要安装依赖包吗？</b></summary>
<br/>不需要。只要 Python 3.8+ 和标准库。<code>/omnis setup</code> 添加的可选 MCP 服务器通过 <code>npx</code> 运行。
</details>

<details>
<summary><b>每个会话能省多少？</b></summary>
<br/>老实说，还不知道。查找和日志会大幅缩小（见 <a href="#numbers">数据</a>），但目前还没有受控的 A/B 会话基准。可用 <code>omnis.py benchmark sessions --split &lt;安装日期&gt;</code> 对比你自己的同类工作。
</details>

<details>
<summary><b>它能读取我的套餐限额和重置时间吗？</b></summary>
<br/>不能。<code>usage</code> 只读取本地 Claude Code 会话记录，5 小时窗口是启发式估计。准确的限额和重置时间只在 Claude Code 自己的 <code>/usage</code> 中。你可以用 <code>usage setup --reset</code> 告诉 OMNIS 你的重置时间。
</details>

<details>
<summary><b>能在 Windows 上运行吗？</b></summary>
<br/>它是按 Windows 设计的（仅标准库、UTF-8 输出、<code>schtasks</code>、PowerShell 规则），但开发和测试套件都在 Linux 上运行。在依赖它之前请先运行 <code>python install.py --verify</code>。
</details>

<details>
<summary><b>Python 以外的语言，<code>find</code> 准确吗？</b></summary>
<br/>Python 使用 AST（<code>high</code>）。其他语言使用正则（<code>medium</code>），因此在高风险修改前请做一次小范围读取确认。<code>deps</code> 无法解析路径别名和动态导入。
</details>

<details>
<summary><b>为什么 ChatGPT 不能直接使用？</b></summary>
<br/>ChatGPT 的 connector 需要通过 HTTPS 访问的远程 MCP 服务器。OMNIS 只提供带 token、仅限 loopback 的 HTTP 模式；是否暴露到公网由你决定，风险也由你承担。
</details>

<details>
<summary><b>关闭 Claude Code 后提醒还有效吗？</b></summary>
<br/>会话内提醒需要会话保持打开。系统级提醒在关闭后也能工作，但只发送通知，不会驱动 Claude。Cron 无法实现跨越午夜的精确 5 小时周期。
</details>

<details>
<summary><b>如何彻底移除？</b></summary>
<br/>Developer OS 用 <code>/omnis geri-al</code>，skill 和 hook 用 <code>install.py --uninstall --yes</code>，其他工具逐个用 <code>install.py --target &lt;工具&gt; --uninstall --yes</code>，项目缓存用 <code>omnis.py clean</code>。
</details>

<details>
<summary><b>接下来计划做什么？</b></summary>
<br/>A/B 基准测试框架 · Windows CI · 面向 TS/Go 的 tree-sitter 解析器 · 基于覆盖率数据的测试影响分析 · 审计后加入更多目录来源。
</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<sub>文档：<a href="SKILL.md">SKILL.md</a> · <a href="docs/BENCHMARKS.md">BENCHMARKS</a> · <a href="docs/SECURITY.md">SECURITY</a> · <a href="docs/WINDOWS.md">WINDOWS</a> · <a href="docs/ECOSYSTEM_RESEARCH.md">ECOSYSTEM_RESEARCH</a> · <a href="docs/tr/GENEL.md">docs/tr</a> · <a href="CHANGELOG.md">CHANGELOG</a></sub>

<sub><a href="LICENSE">MIT 许可证</a> · SVG 图形由 <a href="tools/readme_assets.py">tools/readme_assets.py</a> 生成</sub>

</div>
