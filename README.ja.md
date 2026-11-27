<div align="center">

<sub><a href="README.md">English</a> · <a href="README.tr.md">Türkçe</a> · <a href="README.de.md">Deutsch</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.ar.md">العربية</a></sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-light.svg"><img src="assets/readme/hero-dark.svg" width="100%" alt="OMNIS — あらゆる AI コーディングツールのための、コンテキスト効率が高く安全なエンジニアリング層" /></picture>

<sub><b><a href="#what">概要</a> &nbsp;·&nbsp; <a href="#features">機能</a> &nbsp;·&nbsp; <a href="#demo">デモ</a> &nbsp;·&nbsp; <a href="#tools">対応ツール</a> &nbsp;·&nbsp; <a href="#start">はじめに</a> &nbsp;·&nbsp; <a href="#commands">コマンド</a> &nbsp;·&nbsp; <a href="#numbers">数値</a> &nbsp;·&nbsp; <a href="#safety">安全性</a> &nbsp;·&nbsp; <a href="#faq">FAQ</a></b></sub>

<br/><br/>

**OMNIS** は、AI コーディングツールの下で動くエンジニアリング層です。<br/>
読む量を減らし、ノイズを取り除き、学んだことを覚え、自分の作業を検証し、危険な操作の前には必ず確認します。<br/>
<sub>Python 3.8+ · 標準ライブラリのみ · MIT · v1.2.0</sub>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="what"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-what-light.svg"><img src="assets/readme/title-what-dark.svg" width="100%" alt="概要" /></picture>

</div>

AI コーディングエージェントは、コンテキストの大半を状況把握に使っています。ファイル全体の読み込み、大量の `grep` 出力、3,000 行のテストログ。OMNIS は同じ答えをより安く得る手段と、長時間動くエージェントが信頼性を保つために必要な仕組みを提供します。

- **まず Claude Code。** 常に読み込まれる skill（`SKILL.md`、約 60 行）が各タスクを FAST・STANDARD・DEEP・DEBUG のいずれかのモードに振り分け、workflows と engines は必要なときだけ読み込みます。
- **ほかのツールはすべて MCP 経由。** `~/.omnis/app` にある共有エンジンを標準ライブラリだけで書いた MCP サーバーで公開し、1 つのインストーラーで Codex、Gemini CLI、Cursor、VS Code Copilot などに接続します。
- **入口は 1 つ。** `python scripts/omnis.py <コマンド>`。依存なし、ビルド不要。skill のインストールを頼まない限りネットワーク通信もしません。
- **プロジェクトごとの状態** は `<プロジェクト>/.omnis/` に保存されます（`.gitignore` に追加してください）。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="features"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-features-light.svg"><img src="assets/readme/title-features-dark.svg" width="100%" alt="機能" /></picture>

<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-map-light.svg"><img src="assets/readme/card-map-dark.svg" width="49%" alt="map・find・outline・deps" /></picture></a>
<a href="docs/BENCHMARKS.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-filter-light.svg"><img src="assets/readme/card-filter-dark.svg" width="49%" alt="出力フィルター" /></picture></a>
<a href="SKILL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-memory-light.svg"><img src="assets/readme/card-memory-dark.svg" width="49%" alt="メモリと既知のバグ" /></picture></a>
<a href="workflows/deep.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-checkpoint-light.svg"><img src="assets/readme/card-checkpoint-dark.svg" width="49%" alt="チェックポイント" /></picture></a>
<a href="engines/automation.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-usage-light.svg"><img src="assets/readme/card-usage-dark.svg" width="49%" alt="使用量とリマインダー" /></picture></a>
<a href="docs/SECURITY.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-security-light.svg"><img src="assets/readme/card-security-dark.svg" width="49%" alt="セキュリティスキャンと guard フック" /></picture></a>
<a href="config/skill-catalog.json"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-skills-light.svg"><img src="assets/readme/card-skills-dark.svg" width="49%" alt="skill マネージャーとレジストリ" /></picture></a>
<a href="docs/tr/MCP.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-mcp-light.svg"><img src="assets/readme/card-mcp-dark.svg" width="49%" alt="MCP サーバー" /></picture></a>
<a href="install.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-install-light.svg"><img src="assets/readme/card-install-dark.svg" width="49%" alt="マルチツール対応インストーラー" /></picture></a>
<a href="docs/tr/GENEL.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-os-light.svg"><img src="assets/readme/card-os-dark.svg" width="49%" alt="Developer OS" /></picture></a>
<a href="scripts/gateway_filter.py"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-gateway-light.svg"><img src="assets/readme/card-gateway-dark.svg" width="49%" alt="9Router ゲートウェイフィルター" /></picture></a>
<a href="workflows/debug.md"><picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/card-verify-light.svg"><img src="assets/readme/card-verify-dark.svg" width="49%" alt="Verify" /></picture></a>

<sub>各カードから該当するドキュメントやソースを開けます。</sub>

</div>

<details>
<summary><b>各機能の役割</b> &nbsp;<sub>1 機能につき 1 行</sub></summary>
<br/>

| 機能 | 内容 |
|---|---|
| **map** | キャッシュされるプロジェクトマップ：言語、フレームワーク、パッケージマネージャー、run/build/test コマンド、エントリーポイント、テスト。モノレポ対応。`.env` の中身は決して読みません。 |
| **find · outline · deps** | 差分更新のシンボルインデックス。Python は AST（信頼度 `high`）、JS/TS/Go/Rust/Java/C#/PHP/Ruby は正規表現（`medium`）。`deps` はファイルの import と、そのファイルを import している側を表示します。 |
| **filter** | コマンドを実行し、エラー・トレース・位置・サマリーだけを表示します。完全なログは保存し、終了コードも保持します。 |
| **verify** | 変更ファイル → 関連テスト → チェック。`--run` で実行し、VERIFIED か FAILED を報告します。シークレットらしきファイルも指摘します。 |
| **memory** | 有効期限と出典チェック付きのプロジェクト情報（決定事項、規約、アーキテクチャ）と、バグパターンのストア：`memory bug match "<エラー>"`。 |
| **checkpoint** | タスク、完了分、次の手順を保存します。新しいセッションで `resume` すると、保存以降の git の変更も表示します。 |
| **usage · reminder** | ローカルの Claude Code トランスクリプトから実際のトークン使用量、ヒューリスティックな 5 時間ウィンドウ、上限メッセージを集計。静音時間・最大回数・期限付きの定期リマインダーを CronCreate、`/schedule`、OS のスケジューラーで動かします。 |
| **security · guard** | マスキング付きのシークレット検出、コマンドのリスク分類、そして致命的なコマンドをブロックし危険なコマンドの前に確認する任意の PreToolUse フック。 |
| **skills · audit · registry** | 厳選カタログ（30 skill、8 プリセット）を静的監査のうえ固定コミットからインストール。ロックファイル、競合チェック、更新、削除に対応。 |
| **MCP サーバー** | `scripts/mcp_server.py`：標準ライブラリによる stdio の JSON-RPC、または bearer トークン付き loopback の streamable HTTP。出力は常にマスキングされます。 |
| **インストーラー** | 12 ツール向けの `install.py --target …`。既定はドライラン、全ファイルをバックアップ、冪等、他者の設定項目は保持、`--uninstall` あり。 |
| **Developer OS** | Claude Code 向けの `/omnis setup`：14 の専門エージェント、30 のコマンド、軽量なフック、読み取り専用の自動化、バージョン固定の MCP サーバー、ワンステップのロールバック。 |
| **ゲートウェイフィルター** | `scripts/gateway_filter.py`：9Router の前段に置く OpenAI/Anthropic 互換の任意プロキシで、送信メッセージ内のシークレットをマスクします。 |

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="demo"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-demo-light.svg"><img src="assets/readme/title-demo-dark.svg" width="100%" alt="デモ" /></picture>

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/demo-light.svg"><img src="assets/readme/demo-dark.svg" width="100%" alt="ターミナル：小さな Next.js サンプルプロジェクトでの omnis map、find、deps、filter、security classify" /></picture>

<sub>5 ファイルの Next.js サンプルプロジェクトでの実際の出力です。絶対パスだけ <code>~/shop</code> に短縮しています。</sub>

</div>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="tools"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-tools-light.svg"><img src="assets/readme/title-tools-dark.svg" width="100%" alt="対応ツール" /></picture>

</div>

エンジンは 1 つ。Claude Code では skill として、それ以外には MCP サーバーとして提供します。MCP ツール：`map`、`find`、`outline`、`deps`、`filter`、`verify`、`doctor`、`security_scan`、`security_classify`、`memory_get`/`memory_add`、`checkpoint_save`/`checkpoint_resume`、`usage`。`filter` は危険なコマンドを拒否します。

**ステータスの意味：** **テスト済み** = テストスイートでカバーされ、実際に使用中 · **設定をテスト済み** = インストーラーによるファイル変更を一時 home でテスト済み、実クライアントでは未確認 · **実装済み・未テスト** = ツールのドキュメントだけを元に作成。

| ツール | 使える機能 | OMNIS の書き込み先 | シェル保護 | ステータス |
|---|---|---|---|---|
| Claude Code | すべて：skill、CLI、Developer OS | `~/.claude/skills/omnis` | PreToolUse フック：ブロック + 確認 | テスト済み |
| Codex CLI / app | MCP ツール、グローバル指針 | `~/.codex/config.toml`、`~/.codex/AGENTS.md` | `rules/omnis.rules`（前方一致）+ PreToolUse フック（ブロックのみ） | 設定をテスト済み |
| Gemini CLI | MCP ツール、指針 | `~/.gemini/settings.json`、`GEMINI.md` | BeforeTool フック：ブロックのみ | 設定をテスト済み |
| Antigravity | MCP ツール、グローバルルール | `~/.gemini/antigravity/mcp_config.json` | なし（フック API がない） | 設定をテスト済み |
| Cursor | MCP ツール、プロジェクトルール | `~/.cursor/mcp.json`、`.cursor/rules/omnis.mdc` | `hooks.json` beforeShellExecution | 設定をテスト済み |
| VS Code Copilot | MCP ツール（エージェントモード）、指示 | `Code/User/mcp.json`、`prompts/omnis.instructions.md` | なし（Copilot 自身の確認） | 設定をテスト済み |
| Windsurf | MCP ツール、グローバルルール | `~/.codeium/windsurf/mcp_config.json` | なし | 設定をテスト済み |
| Cline / Roo | MCP ツール | それぞれの `mcp_settings.json` | なし（独自の承認 UI） | 実装済み・未テスト |
| OpenCode | MCP ツール、指針 | `~/.config/opencode/opencode.json`、`AGENTS.md` | なし（`permission` 設定を使用） | 設定をテスト済み |
| Continue | MCP ツール | `~/.continue/mcpServers/omnis.yaml` | なし | 設定をテスト済み |
| AGENTS.md を読む任意のツール | ルール文 | `--target agents --project DIR` | テキストのみ | テスト済み |
| ChatGPT Web / デスクトップ | **直接は不可。** コネクタには HTTPS 経由のリモート MCP が必要 | `mcp_server.py --http`：loopback のみ、bearer トークン、Origin チェック、`--allow-exec` なしでは `filter` 無効 | – | 実装済み・未テスト |
| 9Router ゲートウェイ | 利用を選んだクライアント向けのシークレットマスキング | `:20128` の前段 `:20129` で `gateway_filter.py` | 送信するシークレットをマスク | テスト済み（プロキシの単体テスト） |

<details>
<summary><b>9Router に別プロキシを使う理由</b></summary>
<br/>

9Router（0.5.123）には汎用の MCP ハブがありません。MCP プラグインはハードコードされた一覧で、「managed MCP」一覧も Claude Cowork の設定に送られるだけです。システムプロンプトの注入やリクエストフィルター用のプラグイン API もありません。そのため OMNIS は 9Router にパッチを当てず（npm の更新で消えてしまうため）、`gateway_filter.py` を独立した任意のプロキシとして動かします。マスキングが必要なクライアントは `:20128/v1` の代わりに `http://127.0.0.1:20129/v1` を使います。

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="start"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-start-light.svg"><img src="assets/readme/title-start-dark.svg" width="100%" alt="はじめに" /></picture>

</div>

リポジトリをクローンし、使うツールを選びます。Windows では `python`、macOS/Linux では `python3`。`--yes` を付けるまで、どのターゲットも**ドライラン**です。

```bash
python3 install.py --yes                      # Claude Code の skill → ~/.claude/skills/omnis
python3 install.py --with-hook --yes          # + ~/.claude/settings.json に安全フック（事前にバックアップ）
python3 install.py --os --yes                 # Claude Code Developer OS（/omnis setup と同じ）
python3 install.py --list-targets             # このマシンで検出されたもの
python3 install.py --target codex --yes       # 単一ツール：codex, gemini, antigravity, cursor, vscode,
                                              #   windsurf, cline, roo, opencode, continue, chatgpt
python3 install.py --target all --yes         # 検出されたすべてのツール
python3 install.py --target agents --project DIR --yes   # 1 つのリポジトリに AGENTS.md ブロック
python3 install.py --verify                   # インストール済みコピーでテストスイートを実行
```

Claude Code を再起動したあと：

```text
/omnis setup      監査 → 計画 → バックアップ → インストール → 検証 → レポート（トルコ語）
/omnis durum      ヘルスチェック
/omnis geri-al    直前のセットアップを元に戻す   (omnis rollback list · omnis rollback <ts>)
/omnis map        作業開始
```

**ロールバック。** `/omnis setup` を実行するたびに `settings.json`、`CLAUDE.md`、`manifest.json` が `~/.claude/omnis/backups/<ts>/` に保存されます。ロールバックはこの 2 ファイルを復元し、OMNIS の印が付いたエージェントとコマンドを削除し、追加した MCP サーバーとスケジュールタスクを取り除きます。あなた自身のファイルには触れません。ほかのツールは `install.py --target <ツール> --uninstall --yes`。バックアップは `~/.omnis/backups/<ts>/` に残ります。

<sub>Windows：Windows を想定して設計（標準ライブラリのみ、UTF-8 コンソール、<code>schtasks</code>、guard の PowerShell ルール）。<a href="docs/WINDOWS.md">docs/WINDOWS.md</a> を参照。</sub>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="commands"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-commands-light.svg"><img src="assets/readme/title-commands-dark.svg" width="100%" alt="コマンド" /></picture>

</div>

<details>
<summary><b>CLI</b> &nbsp;<sub><code>python scripts/omnis.py …</code></sub></summary>
<br/>

| コマンド | 内容 |
|---|---|
| `map [ROOT] [--refresh]` | プロジェクトマップ（キャッシュあり） |
| `find NAME` · `outline FILE` · `deps FILE` | シンボル検索、ファイルのアウトライン、import グラフ |
| `index [ROOT]` | シンボルインデックスの作成・更新 |
| `filter "<cmd>"` | コマンドを実行し、重要な部分だけ表示 |
| `verify [--run]` | 現在の変更に対するチェック |
| `doctor` | OS、シェル、ツール、ディスク。環境変数は名前のみ |
| `security scan\|diff\|classify` | シークレットとコマンドのリスク |
| `memory add\|search\|inspect\|cleanup` · `memory bug add\|match` | プロジェクトメモリとバグパターン |
| `checkpoint save\|resume\|list` | タスクのチェックポイント |
| `usage [status\|report\|setup\|limits]` | ローカルトランスクリプトからのトークン使用量 |
| `reminder add\|list\|pause\|resume\|set\|remove\|cron\|os-install` | 定期リマインダー |
| `skills presets\|search\|plan\|install\|list\|conflicts\|update\|remove` | 外部 skill のカタログとインストーラー |
| `audit PATH` | skill フォルダーの静的セキュリティ監査 |
| `benchmark repo\|filter\|sessions` | 削減量の計測 |
| `setup` · `durum` · `geri-al [TS]` | Developer OS：インストール + 検証、ヘルスチェック、ロールバック |
| `os-audit` | インストール済みのもの、重複、競合 |
| `registry [--dupes]` | skill レジストリ |
| `adapt [ROOT]` | スタック検出と関連 skill |
| `automation …` | 通知付きの読み取り専用スケジュールタスク |
| `clean [ROOT]` | このプロジェクトのキャッシュを削除（メモリとチェックポイントは残す） |

</details>

<details>
<summary><b>Claude Code のスラッシュコマンド</b> &nbsp;<sub><code>/omnis setup</code> がインストール</sub></summary>
<br/>

組み込みやプラグインのコマンドと名前が重なるものには `omnis-` が付きます。あなたが書いたファイルには決して触れません。

| コマンド | 内容 |
|---|---|
| `/analyze` | 変更前に対象領域を理解する |
| `/omnis-plan` | 各ステップを検証できる計画（DEEP モード） |
| `/implement` | 計画・編集・テスト・検証まで一貫して実施 |
| `/omnis-debug` | 根本原因、修正、回帰テスト、バグをメモリに保存 |
| `/audit` | 全体のヘルス監査。何も変更しない |
| `/omnis-security` | diff または特定領域のセキュリティレビュー |
| `/omnis-review` | code-reviewer エージェントで diff をレビュー |
| `/test` | 変更が影響するテストだけを実行 |
| `/optimize` | 計測し、直し、もう一度計測 |
| `/refactor` | 振る舞いを変えずに構造を整理 |
| `/omnis-docs` | 実際のコードからドキュメントを書く |
| `/release` · `/deploy` | リリース準備 / デプロイ。どちらも事前に確認 |
| `/cleanup` | 不要なコードやファイルを列挙し、承認後にだけ削除 |
| `/research` | 公式情報源から出典付きで回答 |
| `/project-onboard` | スタックを検出し、skill とエージェントを提案 |
| `/task-report` | 状況を報告し、チェックポイントを保存 |
| `/skills-discover` `/skills-install` `/skills-update` `/skills-audit` `/skills-remove` `/skills-list` | skill カタログとレジストリ |
| `/automation-status` `/automation-add` `/automation-pause` `/automation-resume` `/automation-remove` `/automation-config` `/automation-run` | 自動化マネージャー |

</details>

<details>
<summary><b>エージェント、フック、自動化</b> &nbsp;<sub>Developer OS</sub></summary>
<br/>

**エージェント**（`~/.claude/agents/`。プラグインやあなたのファイルに同名のものがあればスキップ）
- 読み取り専用：architect、security-auditor、code-reviewer、debugger、performance、ui-ux、research。
- 編集あり：developer、frontend、backend、database、docs、qa（テストファイルのみ）、devops（設定のみ、デプロイはしない）。
- 小さな作業ではエージェントを使わない。2 つのエージェントが同じファイルを編集しない。コードを書いたあとは code-reviewer、認証・決済・ファイル・シェルのコードが変わったら security-auditor も実行。

**フック**（`scripts/os_hooks.py`。フックが失敗してもセッションは壊れません）

| イベント | 内容 |
|---|---|
| PreToolUse Bash/PowerShell | `guard.py`：致命的なコマンドをブロックし、危険なコマンドの前に確認 |
| PreToolUse Edit/Write | `.env*`、鍵ファイル、ロックファイルへの書き込み前に確認 |
| PostToolUse Edit/Write | 編集したファイルのシークレットを検査。プロジェクトにあれば prettier/eslint を実行 |
| Stop | .ts/.tsx が変わったら `tsc --noEmit`（ターンのブロックは最大 1 回）。長いタスクのあとに通知 |
| SessionStart · PreCompact | タスクのチェックポイントを復元 / 保存 |

**自動化**（`scripts/automation.py`、Windows タスク スケジューラに `OMNIS\<id>` として登録）：`skill-update-check`、`dependency-advisories`、`repo-health`。間隔は 1、2、3、5（既定）、8、12、24 時間。タスクは読み取りのみで、`~/.omnis/reports/` にレポートを書き、通知を表示します。

**setup が追加する MCP サーバー**（認証情報不要、バージョン固定）：`@upstash/context7-mcp@4.6.0`、`@playwright/mcp@0.0.84`。

</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="numbers"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-numbers-light.svg"><img src="assets/readme/title-numbers-dark.svg" width="100%" alt="数値" /></picture>

</div>

出典：[docs/BENCHMARKS.md](docs/BENCHMARKS.md)（2026-11-27、Linux、Python 3.13）。バイト数は実測、トークン数は推定（バイト ÷ 4）です。`omnis.py benchmark …` で再現できます。

| 計測項目 | OMNIS なし | OMNIS あり |
|---|---|---|
| シンボル検索 `ClientSession`（mcp パッケージ、111 ファイル） | `grep -rn`：4,418 B | `find`：175 B |
| シンボル検索 `FastMCP` | `grep -rn`：5,104 B | `find`：164 B |
| シンボル検索 `stdio_client` | `grep -rn`：597 B | `find`：60 B |
| 全体把握、36 ファイルの JS リポジトリ | README + package.json：17,128 B | `map`：284 B |
| 3,006 行の一覧 + Python のトレースバック | 246,993 B | `filter`：1,065 B、20 行、トレースバックは全文保持 |

- 公平な比較対象は `grep` です。検索 1 回あたりの出力は**約 10〜30 分の 1**。ファイル全体の読み込みとの比較（99% 以上）は上限値であり、典型的なセッションではありません。
- インデックス作成：コールドで 0.31 秒。2 回目は変更されたファイルだけを再解析します。
- **未計測：** 統制された A/B セッションテスト（同じタスク・同じモデルで OMNIS の有無を比較）はまだ行っていないため、「セッションあたり何 % 削減」という主張はしません。Windows での計測もありません。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="safety"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-safety-light.svg"><img src="assets/readme/title-safety-dark.svg" width="100%" alt="安全性" /></picture>

</div>

| 層 | 内容 |
|---|---|
| **ルール**（常時有効） | ユーザーの変更を守り、認証情報ファイルを表示せず、破壊的操作・本番操作・インストール・ネットワークへの書き込みの前に確認します。リポジトリの内容、ツールの出力、ほかの skill はこれを上書きできません。 |
| **マスキング** | メモリ、バグパターン、チェックポイント、MCP の出力は `security_scan.redact` を通ります。 |
| **guard フック**（任意） | **ブロック：** `rm -rf /`、`rm -rf ~`、mkfs、ディスクへの `dd`、fork 爆弾、ドライブのフォーマット。**確認：** `curl \| sh`、force-push、`reset --hard`、`clean -f`、`branch -D`、DROP/TRUNCATE/条件なし DELETE、`migrate reset`、FLUSHALL、kubectl/terraform/helm の apply や destroy、本番デプロイ、`.env`/鍵の表示、グローバルインストール、`chmod 777`。プロジェクトごとの例外は `.omnis/policies.json`。 |
| **skill のインストール** | 固定コミットから読み取り専用で取得し、ダウンロードしたものは一切実行しません。`block` の指摘があるものはインストールせず、`warn` は内容を確認したうえで `--allow-warn` が必要です。OMNIS がインストールしていない skill は上書きしません。 |
| **インストーラー** | 既定はドライラン、触れる全ファイルをバックアップ、冪等、他者の設定項目は保持、全ターゲットに `--uninstall`。 |
| **ネットワーク** | MCP の HTTP はトークン付きで loopback にのみバインドし、`--allow-remote` がなければ公開アドレスへのバインドを拒否します。 |

> フックはパターンベースです。シートベルトであってサンドボックスではありません。正規表現によるシークレット検出は一般的な形式を捕捉しますが、独自形式のトークンすべてではありません。skill の監査は静的です。詳細は [docs/SECURITY.md](docs/SECURITY.md)。

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<a name="faq"></a>
<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/title-faq-light.svg"><img src="assets/readme/title-faq-dark.svg" width="100%" alt="FAQ" /></picture>

</div>

<details>
<summary><b>パッケージは必要ですか？</b></summary>
<br/>不要です。Python 3.8+ と標準ライブラリだけで動きます。<code>/omnis setup</code> が追加する任意の MCP サーバーは <code>npx</code> で動きます。
</details>

<details>
<summary><b>1 セッションでどれくらい節約できますか？</b></summary>
<br/>正直に言うと、まだわかりません。検索とログは大きく縮みます（<a href="#numbers">数値</a> を参照）が、統制された A/B セッションのベンチマークはまだありません。<code>omnis.py benchmark sessions --split &lt;インストール日&gt;</code> で、ご自身の同種の作業を比較してください。
</details>

<details>
<summary><b>プランの上限やリセット時刻を読み取れますか？</b></summary>
<br/>いいえ。<code>usage</code> が読むのはローカルの Claude Code トランスクリプトだけで、5 時間ウィンドウはヒューリスティックです。正確な上限とリセット時刻は Claude Code 自身の <code>/usage</code> にしかありません。リセット時刻は <code>usage setup --reset</code> で OMNIS に伝えられます。
</details>

<details>
<summary><b>Windows で動きますか？</b></summary>
<br/>Windows を想定して設計しています（標準ライブラリのみ、UTF-8 出力、<code>schtasks</code>、PowerShell ルール）が、開発とテストスイートの実行は Linux で行いました。使い始める前に <code>python install.py --verify</code> を実行してください。
</details>

<details>
<summary><b>Python 以外での <code>find</code> の精度は？</b></summary>
<br/>Python は AST（<code>high</code>）です。ほかの言語は正規表現（<code>medium</code>）なので、危険な編集の前に範囲を絞った読み込みで確認してください。<code>deps</code> はパスエイリアスや動的 import を解決できません。
</details>

<details>
<summary><b>なぜ ChatGPT からは直接使えないのですか？</b></summary>
<br/>ChatGPT のコネクタには HTTPS 経由のリモート MCP サーバーが必要です。OMNIS が提供するのはトークン付きの loopback 専用 HTTP モードで、インターネットに公開するかどうかはあなたの判断であり、リスクもあなたが負います。
</details>

<details>
<summary><b>Claude Code を閉じていてもリマインダーは動きますか？</b></summary>
<br/>セッション内のリマインダーはセッションが開いている必要があります。OS のリマインダーは閉じていても動きますが、通知を送るだけで Claude を操作はしません。cron では日付をまたぐ正確な 5 時間周期は作れません。
</details>

<details>
<summary><b>すべて削除するには？</b></summary>
<br/>Developer OS は <code>/omnis geri-al</code>、skill とフックは <code>install.py --uninstall --yes</code>、ほかの各ツールは <code>install.py --target &lt;ツール&gt; --uninstall --yes</code>、プロジェクトのキャッシュは <code>omnis.py clean</code> です。
</details>

<details>
<summary><b>今後の予定は？</b></summary>
<br/>A/B ベンチマーク基盤 · Windows CI · TS/Go 向け tree-sitter パーサー · カバレッジデータに基づくテスト選択 · 監査を経たカタログ取得元の追加。
</details>

<div align="center">

<picture><source media="(prefers-color-scheme: light)" srcset="assets/readme/divider-light.svg"><img src="assets/readme/divider-dark.svg" width="100%" alt="" /></picture>

<sub>ドキュメント：<a href="SKILL.md">SKILL.md</a> · <a href="docs/BENCHMARKS.md">BENCHMARKS</a> · <a href="docs/SECURITY.md">SECURITY</a> · <a href="docs/WINDOWS.md">WINDOWS</a> · <a href="docs/ECOSYSTEM_RESEARCH.md">ECOSYSTEM_RESEARCH</a> · <a href="docs/tr/GENEL.md">docs/tr</a> · <a href="CHANGELOG.md">CHANGELOG</a></sub>

<sub><a href="LICENSE">MIT ライセンス</a> · SVG イラストは <a href="tools/readme_assets.py">tools/readme_assets.py</a> で生成</sub>

</div>
