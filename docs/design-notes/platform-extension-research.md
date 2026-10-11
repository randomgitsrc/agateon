# 主流 AI-agent CLI 运行时平台能力调研（第四运行时扩展素材）

> 调研目标：为 agate 协议扩展第四运行时提供素材。**未排期**（无当前需求驱动；仅当出现真实需求 / 首个用例时再评估）。
> 调研范围：Codex CLI（OpenAI）、Cursor（CLI / Agent）、Gemini CLI（Google）为主，Aider / Cline / Windsurf（Cascade）/ Goose 作候选评估。
> 资料来源：各平台官方文档线上版本（抓取于本次调研会话；平台迭代快，接入前请复核）。不确定项均标注「待官方确认」，未编造 API / 命令名。

---

## 1. 摘要

- **结论一：三个主候选平台（Codex / Cursor / Gemini CLI）全部具备 session hooks 与自定义 agent 身份机制**，且全部支持无头（headless / 非交互）执行——agate 的「git hooks 做 gate」在它们之上仍然成立（git hook 是 git 协议级、平台无关），因此第四平台接入不需要改造 agate 的 gate 机制本身。
- **结论二：Cursor 是接入成本最低的候选**——其自定义 subagent 同时兼容 `.claude/agents/`、`.codex/agents/` 两种格式，agate 现有的 `.claude/agents/orchestrator.md` 模板可直接复用，无需新写身份模板格式。
- **结论三：Codex 是机制契合度最高的候选**——hooks 事件最全（12 个，含 `SubagentStart` / `SubagentStop`）、沙箱语义最清晰可自动化（`codex exec --sandbox` 三级模式）、无头输出是 JSONL 事件流（适合回归测试断言）、且 roadmap 已点名。唯一的身份格式差异是自定义 agent 用 **TOML**（`.codex/agents/*.toml`），与 agate 现有的 markdown 模板体系不同，需新建模板。
- **结论四：Gemini CLI 是社区热度最高、全开源的候选**（Apache-2.0，约 10.7 万 stars，TypeScript），hooks v1 已于 2026-01 发布，沙箱后端选择最丰富（Seatbelt / 容器 / Windows 原生 / gVisor / LXC），但 hooks 生态相对新、无头 JSON 输出形态较简单，需评估。
- **结论五：Aider 与 agate 存在直接机制冲突**——Aider 默认以 `git commit --no-verify` 提交（跳过 pre-commit hooks），会绕过 agate 的 commit 级 gate；不建议作为第四平台，建议在文档中标注为「已知不兼容」。Cline / Goose / Windsurf 各自有 hooks 或接近 hooks 的能力，但 CLI 成熟度或官方支持状态不足，列为观察项。
- **结论六：`platform-notes.md` 中关于 Codex 的旧记录需复核**——原记录「Codex subagent max_depth=1 无法再派发」写于 subagent workflows 默认启用之前，本次调研确认官方文档已默认启用 subagent workflows，是否支持多层派发需实机验证（见 2.1 与 3 节）。

---

## 2. 逐平台能力表

### 2.1 总表：主候选平台能力一览

| 能力维度 | Codex CLI（OpenAI） | Cursor（CLI / Agent） | Gemini CLI（Google） |
|---|---|---|---|
| 开源 / 协议 | 是（Rust，Apache-2.0，约 11.7 万 stars）| 否（编辑器与 CLI 均闭源，需 Cursor 账号 / API key）| 是（TypeScript，Apache-2.0，约 10.7 万 stars）|
| subagent / 派发形态 | subagent workflows 默认启用；主线程收集结果；`/agent` 切换线程；内置 default / worker / explorer | Task tool 派发；前台 / 后台（`is_background`）；支持并行；内置多个 subagents | subagent 以同名工具暴露给主 agent；`@name` 强制语法；内置 codebase_investigator / cli_help / generalist / browser 等 |
| 自定义 agent 身份文件 | `.codex/agents/*.toml`（TOML，必填 name / description / developer_instructions）| `.cursor/agents/*.md`，**兼容 `.claude/agents/` 与 `.codex/agents/` 格式**（markdown + frontmatter）| `.gemini/agents/*.md`（markdown + YAML frontmatter，body 即 system prompt）|
| session hooks | ✅ 11 事件（SessionStart / SessionEnd / SubagentStart / SubagentStop / PreToolUse / PermissionRequest / PostToolUse / PreCompact / PostCompact / UserPromptSubmit / Stop）| ✅ 20+ 事件（sessionStart / sessionEnd / preToolUse / postToolUse / postToolUseFailure / subagentStart / subagentStop / beforeShellExecution / afterShellExecution / beforeMCPExecution / afterMCPExecution / beforeReadFile / afterFileEdit / beforeSubmitPrompt / preCompact / stop 等）| ✅ 11 事件（SessionStart / SessionEnd / BeforeAgent / AfterAgent / BeforeModel / AfterModel / BeforeToolSelection / BeforeTool / AfterTool / PreCompress / Notification）|
| hooks 配置位置 | `~/.codex/hooks.json`、`<repo>/.codex/hooks.json`、config.toml 内联 `[hooks]`、插件捆绑；managed hooks 经 requirements.toml | `<project>/.cursor/hooks.json`、`~/.cursor/hooks.json`；Cloud Agent 读取仓库内 `.cursor/hooks.json` 的命令 hooks | `settings.json` 分层：项目 `.gemini/settings.json` > 用户 `~/.gemini/settings.json` > 系统 `/etc/gemini-cli/settings.json` > 扩展 |
| hooks 执行契约 | JSON over stdin / stdout，exit code 判定 | JSON over stdin / stdout，exit code 判定；另有 prompt-based（LLM 评估）hooks | JSON over stdin / stdout（严格契约：stdout 只允许 JSON）；exit code：0=解析 JSON，2=System Block，其他=warning |
| 沙箱语义 | 平台原生强制（macOS Seatbelt / Linux+WSL2 bubblewrap / Windows 原生沙箱）；`sandbox_mode` 三级：`read-only` / `workspace-write` / `danger-full-access`；权限 profile（`:read-only` / `:workspace` / `:danger-full-access` 及自定义）；网络控制可配 | CLI 为二态开关：`--sandbox enabled|disabled` + 网络控制菜单（编辑器内另有 run modes）；粒度最粗 | 后端最丰富：macOS Seatbelt / Docker·Podman 容器 / Windows 原生 / Linux bubblewrap+seccomp / gVisor（runsc）/ LXC（实验）；支持 sandbox expansion（动态扩展到工作区外）与工具级隔离 |
| 无头 / 非交互模式 | `codex exec "<prompt>"`；`--sandbox` 覆盖（默认 read-only）；`--json` 输出 JSONL 事件流（thread.started / turn.started / item.* 等）；`-o` 落盘最终消息；`--ephemeral` 不落盘会话；支持 JSON schema 结构化输出 | `agent -p/--print`；`--force`（或 `--yolo`）才允许真实改文件；`--mode`（Agent / Plan / Ask）；`agent ls` / `agent resume` 会话管理；`&` 前缀交接 Cloud Agent | `-p/--prompt` 或非 TTY 环境触发；`--output-format json`（单对象：response / stats / error）或 streaming JSONL（init / message / tool_use / tool_result / error / result）；exit code：0 / 1 / 42 / 53 |
| 项目指令 / 上下文 | AGENTS.md 指令链（全局 `~/.codex/AGENTS.md` → 项目根向下逐目录合并，默认 32 KiB 上限）；execpolicy `.rules` 文件 | rules（`.cursor/rules` 项目 / 用户 / Team Rules）+ AGENTS.md；skills（`.cursor/skills`）| GEMINI.md 项目上下文文件；settings.json 分层配置；extensions（自定义命令）|
| 工具扩展 | MCP（含 `required = true` 强依赖语义）；skills；plugins | MCP；skills；plugins | MCP；extensions；Google Search grounding |
| 与 agate git-hook gate 的兼容 | ✅ git 协议级机制，天然可用 | ✅ 同左 | ✅ 同左 |
| 回归测试友好度 | 高（JSONL 事件流可断言工具调用与命令执行）| 中（`--output-format text` / 消息流）| 中（单对象 JSON 或 streaming JSONL）|

### 2.2 Codex CLI 要点（对应调研维度 1）

- **subagent / 工具调用形态**：官方文档确认当前版本 subagent workflows 默认启用（桌面 App / CLI / IDE 扩展），主 agent 可自动或按指示委托，主线程收集各 subagent 结果；内置 agent 为 `default` / `worker` / `explorer`。自定义 agent 是**独立 TOML 文件**（`~/.codex/agents/` 或 `<repo>/.codex/agents/`），必填 `name` / `description` / `developer_instructions`，可附加 `model` / `model_reasoning_effort` / `sandbox_mode` / `mcp_servers` / `skills.config` 等 config.toml 键；全局 `[agents]` 表控制 enabled / max_concurrent_threads_per_session / default_subagent_model 等。⚠️ `platform-notes.md` 旧记录「Codex subagent max_depth=1 无法再派发」需在接入时实机复核（该记录早于 subagent workflows 默认启用）。
- **hooks**：完整 session hooks（11 事件），位置含用户级与项目级 `hooks.json` 及 config.toml 内联。**信任机制是本平台特有**：非 managed hook 必须经 `/hooks` 命令 review + trust（按 hash 记录），变更后需重新 trust；自动化场景可用 `--dangerously-bypass-hook-trust` 一次性绕过；企业可用 requirements.toml 的 managed hooks（`allow_managed_hooks_only = true` 可强制只用 managed hooks）。
- **sandbox 隔离语义**：平台原生强制（macOS Seatbelt、Linux/WSL2 bubblewrap、Windows 原生沙箱），作用于所有 spawn 命令（git / 包管理器 / 测试运行器均继承边界）；`sandbox_mode` 三值（`read-only` / `workspace-write` / `danger-full-access`）+ 权限 profile + 网络控制。
- **无头模式**：`codex exec` 是 CI / 脚本入口，默认 read-only 沙箱；`--sandbox workspace-write|danger-full-access` 显式提权；`--json` 输出 JSONL 事件流（含 `command_execution` 等 item 类型），便于回归测试断言；`--ephemeral`、`-o/--output-last-message`、stdin 管道、JSON schema 结构化输出齐备。
- **身份 / 指令配置**：AGENTS.md 指令链 + 自定义 agent TOML + `.rules`（execpolicy，控制沙箱外可执行命令）。

### 2.3 Cursor 要点（对应调研维度 2）

- **CLI**：二进制 `agent`（macOS / Linux / WSL / Windows），交互模式 + `-p/--print` 非交互模式；**非交互下默认只提案不改文件，`--force`（或 `--yolo`）才允许真实修改**——这一点与 agate「subagent 产出文件」的协作方式直接相关，自动化脚本必须带 `--force`。模式三态：Agent（默认）/ Plan / Ask；会话管理（`agent ls` / `agent resume` / `--continue` / `--resume`）；`&` 前缀可将任务交接给云端 Cloud Agent。
- **agent 能力**：Task tool 派发 subagent，支持前台 / 后台（`is_background: true`）与并行执行；内置 subagents；自动委托。
- **hooks / 自定义命令机制**：`.cursor/hooks.json`（项目 / 用户两级），事件覆盖 session 生命周期、工具调用（pre / post / failure）、shell 执行、MCP 执行、文件读写、prompt 提交、压缩、停止等；**支持 command-based 与 prompt-based（LLM 评估）两种 hook 类型**；Cloud Agent 会读取仓库内 `.cursor/hooks.json` 的命令 hooks。另有 Tab hooks（补全）与 app 生命周期 hooks（`workspaceOpen`）。
- **配置方式**：rules（项目 / 用户 / Team Rules / AGENTS.md）、subagents（`.cursor/agents/` + 兼容目录）、settings、MCP、skills。
- **关键发现**：Cursor 的 subagent 文件位置显式兼容 `.claude/agents/` 与 `.codex/agents/`（Claude Code / Codex 兼容），同名冲突时 `.cursor/` 优先——agate 现有 `.claude/agents/orchestrator.md` 软链模板可直接被 Cursor 读取。
- **sandbox**：CLI 是二态开关（`--sandbox enabled|disabled`）+ 网络控制菜单；编辑器侧另有 run modes（安全文档 `agent/security/run-modes.md`，本次未展开核验，标「待官方确认」）。粒度明显粗于 Codex / Gemini。
- ⚠️ 闭源 + 订阅制：无头模式需要 Cursor 账号 / API key（官方文档 `Set API key for scripts`），可能影响 CI 环境落地。

### 2.4 Gemini CLI 要点（对应调研维度 3）

- **agent 能力**：subagent 作为工具暴露给主 agent（工具名 = agent 名）；自动委托 + `@name` 强制语法；内置 codebase_investigator、cli_help、generalist、browser / visual agent；**递归保护**（subagent 不能调用 subagent）；**工具隔离**（`tools` 白名单，支持 `*`、`mcp_*`、`mcp_server_*` 通配符）。
- **hooks**：v1 已于 2026-01 发布（feature request #9070 已关闭）；11 个事件，含 Codex / Claude Code 没有的 `BeforeModel`（改 prompt / 换模型 / mock 响应）与 `BeforeToolSelection`（过滤工具）；JSON-over-stdin 严格契约；exit code 语义（0=允许、2=System Block、其他=warning）；matcher（工具事件用正则，生命周期用精确字符串）；配置在 `settings.json` 四层合并（项目 > 用户 > 系统 > 扩展）。
- **配置**：settings.json 分层；GEMINI.md 项目上下文；extensions（自定义命令）；MCP。
- **是否开源**：是，`google-gemini/gemini-cli`（Apache-2.0，TypeScript，约 10.7 万 stars）。
- **sandbox**：后端最多样——macOS Seatbelt、Docker / Podman 容器、Windows 原生沙箱、Linux bubblewrap + seccomp、gVisor（runsc）、LXC / LXD（实验性）；`--sandbox` 命令行开关 / 环境变量 / settings.json `tools.sandbox` 三种启用方式；支持 sandbox expansion 与工具级 sandbox 开关。
- **无头模式**：`-p/--prompt` 或非 TTY 触发；`--output-format json` 返回单对象（response / stats / error），streaming JSONL 提供 `tool_use` / `tool_result` 事件（可支撑回归断言）；exit code 语义明确（0 / 1 / 42 / 53）。
- ⚠️ 认证：Google 账号 OAuth / Gemini API key / Vertex AI，CI 自动化需服务化认证（标「待官方确认」具体无头认证最佳实践）。

### 2.5 其他候选（各一段）

- **Aider**：Python 开源 CLI 结对编程工具（Apache-2.0，约 4.8 万 stars），`--architect` 模式是**双模型分工**（architect 负责推理、editor 负责落盘编辑），并非 subagent 派发；git 原生（每次改动自动 commit，Conventional Commits 由弱模型生成）。**与 agate 的直接冲突**：默认以 `--no-verify` 提交、**跳过 pre-commit hooks**（`--git-commit-verify` 可开启），会绕过 agate 的 commit 级 gate；无 session hooks。结论：机制契合度低，不建议纳入第四平台，建议在 agate 文档中标注「已知不兼容」。
- **Cline**：VS Code 扩展起家的开源自主 agent（Apache-2.0，约 6.7 万 stars），现提供独立 CLI（`cline`，交互 + headless 管道模式；`-p/--plan`、`--auto-approve`、`--json` NDJSON 消息流、`--thinking`、`-t/--timeout`、`CLINE_COMMAND_PERMISSIONS` 命令白名单 / 黑名单、ACP 协议支持可嵌入 Zed / JetBrains / Neovim）。官方 session hooks 页面未见（「待官方确认」）；规则机制是 `.clinerules` 与 MCP。结论：可观察，IDE 绑定色彩较重，优先级中低。
- **Windsurf / Cascade**：Codeium 出品的 IDE + Cascade agent，hooks 机制与 Claude Code 同源——`.windsurf/hooks.json`（工作区）+ 用户级 `~/.codeium/windsurf/hooks.json` + 系统级三处合并，事件含 pre_user_prompt / pre_read_code / pre_write_code / pre_run_command / pre_mcp_tool_use（预钩子可用 exit code 2 阻断）+ 后置钩子；规则在 `.windsurf/rules`。⚠️ CLI 无头模式与 hooks 在 CLI 下的触发行为「待官方确认」。结论：hooks 机制契合，但 CLI 成熟度 / 文档完整度不如三个主候选，列为观察项。
- **Goose（Block）**：Rust 微内核 agent（Apache-2.0，约 5.3 万 stars），架构核心是 blocks / extensions（developer、computer controller、memory 等），配置 `~/.config/goose/config.yaml`。曾有 PR #7411 提交「agent lifecycle hooks（Claude Code 兼容配置）」，但该 PR **未合并**（2026-02 关闭），官方 hooks 支持状态「待官方确认」。结论：架构有特色，但 hooks 未落地，优先级低。

---

## 3. 与 agate 现有 3 平台的机制对照

agate 现有运行时：OpenCode、Claude Code、DSH（deepseek-harness）。agate 的 gate 机制依赖三条腿：**git hooks**（pre-commit / commit-msg / pre-push，经 `install-hook.py` 软链安装）、**身份配置**（`.claude/agents/` 风格 / agent-preset）、**子代理派发**（方法 B：通用 subagent + prompt 注入角色文件）。对照如下：

| agate 机制 | OpenCode（现有）| Claude Code（现有）| DSH（现有）| Codex CLI | Cursor | Gemini CLI |
|---|---|---|---|---|---|---|
| gate 载体 | git hooks（pre-commit 等）| git hooks | git hooks + **session hooks**（PostToolUse 每步触发，platform-notes 记录）| git hooks 可用；另有 11 事件 session hooks | git hooks 可用；另有 20+ 事件 session hooks | git hooks 可用；另有 11 事件 session hooks |
| orchestrator 身份注册 | `.agents/orchestrator.md`（`--custom-role` 不可用，方法 B）| `.claude/agents/orchestrator.md` 软链（mode: primary）| agent-preset（`agent.cordis.yml` + `preset.yml`）| `.codex/agents/orchestrator.toml`（**需新建 TOML 模板**）| `.cursor/agents/orchestrator.md`，**可直接复用 `.claude/agents/` 模板** | `.gemini/agents/orchestrator.md`（**需新建，YAML frontmatter + body 即 system prompt**）|
| subagent 派发 | task 工具（方法 B）| task 工具 | `subagent` / `subagent_fork` / `workflow` / `ralph` | subagent workflows（默认启用；多层派发待实机复核）| Task tool（前台 / 后台 / 并行）| subagent 工具（递归保护：subagent 不可再调 subagent）|
| 无头回归测试 | 交互式为主 | `claude -p`（既有实践）| GUI / CLI 会话 | `codex exec --json`（JSONL 事件流，最友好）| `agent -p --force` | `gemini -p --output-format json` |
| 沙箱 | 无强沙箱（OS 级）| 无强沙箱（OS 级）| 文件沙箱（默认 workspace-write）| 三级 `sandbox_mode` + 平台原生强制 | 二态开关 | 多后端（Seatbelt / 容器 / gVisor / LXC 等）|

**关键差异总结（调研维度 5）**

1. **session hooks vs git hooks**：四个候选（Codex / Cursor / Gemini / Windsurf）**全部支持 session 级拦截**（工具调用前 / 后、subagent 生命周期、模型调用前后等），且全部是 JSON-over-stdin + exit code 契约（Claude Code hooks 系风格，Gemini 明确「mirrors Claude Code 契约」）。agate 目前只用 git hooks 做 gate——这不是平台限制（Claude Code / DSH 本就支持 session hooks），而是 agate 选择了「git 协议级、平台无关」的统一载体。**对该扩展的含义**：接入第四平台时 git-hook gate 零改动可用；session hooks 可作为后续增强（例如把「危险命令拦截」从 commit 时前置到工具执行时），但那是架构级扩展，建议单独立项，不塞进本次扩展。唯一需注意的反例是 Aider（默认 `--no-verify` 绕过 pre-commit，直接冲突）。
2. **沙箱语义差异**：Codex 与 Gemini 是「强沙箱 + 可编程授权」派（Codex 三级模式 + 权限 profile；Gemini 多后端 + expansion），Cursor 是「简单开关」派（二态）。对 agate 的影响集中在自动化参数上：`codex exec` 默认 read-only，必须显式 `--sandbox workspace-write` 让 subagent 能写工作区；Gemini 沙箱默认关闭、`--sandbox` 需显式开启（开启后跑测试命令的行为待实机验证）；Cursor `--force` 才是允许改文件的开关。这些都要写进各自 SETUP.md 的「自动化环境」小节。
3. **身份 / agent 配置机制差异**：主流收敛到「markdown + frontmatter」——Claude Code（`.claude/agents/*.md`）、Gemini（`.gemini/agents/*.md`）、Cursor（`.cursor/agents/*.md` 且**向下兼容 `.claude/` 与 `.codex/` 格式**）；Codex 特立独行用 TOML（`.codex/agents/*.toml`，`developer_instructions` 字段承载指令）。DSH 的 agent-preset（YAML）是另一极。**对该扩展的含义**：Cursor 接入几乎零模板成本；Codex / Gemini 各需新增一种身份模板（分别 TOML / markdown-frontmatter），模板内指令文本仍可复用 `orchestrator-template.md`（软链 / 拷贝引用的方式按各平台要求落位）。

---

## 4. 第四平台优先级建议

### 4.1 建议排序

| 优先级 | 平台 | 机制契合度 | 社区热度 | 接入成本 | 建议 |
|---|---|---|---|---|---|
| 1 | **Codex CLI** | 高（hooks 事件最全、无头 JSONL 事件流最适合作回归测试、沙箱三级可自动化）| 高（约 11.7 万 stars，OpenAI 官方持续投入）| 中（身份模板需新建 TOML 格式；`codex exec` 参数需进 SETUP；旧 max_depth 记录需复核）| **推荐作为第四平台首选**，与 roadmap 点名一致 |
| 2 | **Cursor** | 高（hooks 20+ 事件；subagent 兼容 `.claude/agents/` 格式）| 高（编辑器市场占有率大）| **最低**（身份模板零新建；`agent -p --force` 无头成熟）| 推荐紧随其后接入；扣分项：闭源 + 订阅 / API key、沙箱粒度粗 |
| 3 | **Gemini CLI** | 中高（hooks v1 已发布；subagent 递归保护与工具隔离是加分项）| **最高**（约 10.7 万 stars，全开源 Apache-2.0）| 中高（身份模板需新建；无头 JSON 输出较简单；认证需 Google 账号 / API key）| 推荐第三位接入；hooks 生态较新，接入前先做一轮实机冒烟 |
| 4 | Windsurf / Cascade | 中（hooks 与 Claude 同源，但 CLI 无头形态待确认）| 中 | 中高（文档与 CLI 成熟度不足）| 观察项，暂不立项 |
| — | Aider | **低（默认 `--no-verify` 绕过 pre-commit，与 agate gate 冲突）** | 中（约 4.8 万 stars）| — | **不建议接入**；在 agate 文档标注「已知不兼容」 |
| — | Cline / Goose | 低 / 中（Cline 官方 hooks 待确认；Goose hooks PR 未合并）| 中 / 中（6.7 万 / 5.3 万 stars）| — | 观察项，hooks 落地后再评估 |

### 4.2 推荐理由展开

- **Codex 第一的理由**：① 机制契合度最高——`SubagentStart / SubagentStop` 事件让 agate 可以观测 subagent 生命周期；`codex exec --json` 的 JSONL 事件流（含 `command_execution`、`file_changes` 等 item 类型）可直接用于回归测试断言「gate 是否按预期触发」；② roadmap 已点名，社区预期明确；③ 沙箱三级语义与 agate 的「subagent 只写任务工作区」约束天然对齐（`--sandbox workspace-write`）；④ 开源可审计，hooks 信任机制（hash + `/hooks`）是安全加分。**主要成本**：自定义 agent 是 TOML 格式，需在 `assets/templates/` 新增 `codex/` 身份模板；`platform-notes.md` 现有 Codex 兼容性段落需按新能力重写并实机复核 max_depth 限制。
- **Cursor 第二的理由**：① 接入成本全场最低——官方文档明确 subagent 兼容 `.claude/agents/`（以及 `.codex/agents/`），agate 现有的 orchestrator 软链模板可直接复用，`assets/templates/` 几乎零新增；② hooks 事件覆盖完整（含 subagentStart / subagentStop、beforeShellExecution）；③ 无头模式成熟（`agent -p` + `--force`，有 `--output-format`）。**扣分项**：闭源 + 订阅制（CI 落地受 API key / 账号约束）、沙箱粒度粗（二态）、Cloud Agent 交接（`&`）引入云执行边界，需在 SETUP 中写明数据边界。
- **Gemini 第三的理由**：① 全开源 + 社区热度最高（Apache-2.0，10.7 万 stars），符合「开源优先」的 agate 生态取向；② hooks v1 已发布且契约与 Claude Code 同源（迁移成本低）；③ subagent 的递归保护与工具隔离对 agate「角色文件隔离」是正向强化；④ 沙箱后端最丰富。**扣分项**：hooks 发布仅数月，生态与踩坑记录少；无头输出单对象 JSON 对回归断言稍弱（streaming JSONL 可补）；认证链路（Google OAuth / Vertex AI）在 CI 里比 API key 更重。

### 4.3 对本扩展交付物的落点建议

按任务给定的交付物拆解（每平台 = 身份模板 + SETUP.md 步骤 + platform-notes.md 条目 + 回归测试）：

| 交付物 | Codex CLI | Cursor | Gemini CLI |
|---|---|---|---|
| `assets/templates/` 身份模板 | 新增 `codex/`：`orchestrator.toml`（name / description / developer_instructions = orchestrator-template.md 内容）| 复用现有 `.claude/agents/orchestrator.md`（可加 `codex/` 兼容副本供 `.codex/agents/` 路径）| 新增 `gemini/`：`orchestrator.md`（YAML frontmatter + body 为 orchestrator 指令）|
| SETUP.md 步骤 | 安装 codex CLI；`codex exec --sandbox workspace-write` 无头跑法；hooks.json 信任流程（`/hooks` 或 `--dangerously-bypass-hook-trust`）；AGENTS.md 指令链位置 | `agent` CLI 安装 + API key；`agent -p --force` 无头跑法；`.cursor/agents/` 软链注册 | `gemini` 安装 + 认证；`gemini -p --output-format json` 无头跑法；`.gemini/agents/` 注册 |
| platform-notes.md 条目 | 重写「Codex」段（subagent workflows 现状、sandbox_mode、hooks 信任机制）；复核并更新旧 max_depth 记录 | 新增「Cursor」段（`.claude/agents` 兼容、`--force` 语义、二态沙箱、订阅制约束）| 新增「Gemini CLI」段（hooks v1 契约、settings.json 分层、沙箱后端、递归保护）|
| 回归测试 | `codex exec --json` 事件流断言（gate 触发、文件产出、exit code）| `agent -p --force` + 产物文件断言 | `gemini -p --output-format json` 单对象 / streaming JSONL 断言 |

> 补充建议：无论先接哪个，建议在本扩展内先做一轮「三平台无头冒烟」POC（各平台各跑一个最小 agate 任务，验证 git-hook gate 在无头模式下确实触发），用结果决定最终接入顺序——本调研的优先级排序基于文档能力，实机冒烟可能修正（尤其是 Codex max_depth 与 Gemini 沙箱默认行为两项）。

---

## 5. 来源与引用

### 5.1 Codex CLI（OpenAI）

- [openai/codex 官方仓库](https://github.com/openai/codex)（Apache-2.0，Rust）
- [Hooks（官方文档，learn.chatgpt.com）](https://learn.chatgpt.com/docs/hooks.md)
- [Sandbox（官方文档）](https://learn.chatgpt.com/docs/sandboxing.md)
- [Non-interactive mode / codex exec（官方文档）](https://learn.chatgpt.com/docs/non-interactive-mode.md)
- [Subagents 与自定义 agent（官方文档）](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [AGENTS.md 自定义指令（官方文档）](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)
- [Configuration Reference（sandbox_mode / 权限 profile，官方文档）](https://learn.chatgpt.com/docs/config-file/config-reference.md)
- [Codex 文档索引 llms.txt](https://learn.chatgpt.com/llms.txt)

### 5.2 Cursor

- [Using Headless CLI（官方文档）](https://cursor.com/docs/cli/headless.md)
- [CLI Overview（官方文档）](https://cursor.com/docs/cli/overview.md)
- [Hooks（官方文档）](https://cursor.com/docs/hooks.md)
- [Subagents（官方文档）](https://cursor.com/docs/subagents.md)
- [Rules（官方文档）](https://cursor.com/docs/rules.md)
- [Cursor 文档索引 llms.txt](https://cursor.com/llms.txt)

### 5.3 Gemini CLI（Google）

- [google-gemini/gemini-cli 官方仓库](https://github.com/google-gemini/gemini-cli)（Apache-2.0，TypeScript）
- [Hooks（官方文档）](https://www.geminicli.com/docs/hooks)
- [Subagents（官方文档）](https://www.geminicli.com/docs/core/subagents)
- [Sandboxing（官方文档）](https://www.geminicli.com/docs/cli/sandbox)
- [Headless mode reference（官方文档）](https://www.geminicli.com/docs/cli/headless)
- [Hooks 功能提案与落地 issue #9070](https://github.com/google-gemini/gemini-cli/issues/9070)

### 5.4 其他候选

- [Aider：Separating code reasoning and editing（architect 模式）](https://aider.chat/2024/09/26/architect.html)
- [Aider：Git integration（--no-verify 默认跳过 pre-commit）](https://aider.chat/docs/git.html)
- [Cline：CLI Overview](https://docs.cline.bot/usage/cli-overview)
- [cline/cline 官方仓库](https://github.com/cline/cline)
- [block/goose 官方仓库](https://github.com/block/goose)
- [goose PR #7411：agent lifecycle hooks（未合并）](https://github.com/aaif-goose/goose/pull/7411)
- [Windsurf：Cascade Hooks（官方文档）](https://docs.windsurf.com/zh/windsurf/cascade/hooks)

### 5.5 agate 内部依据

- [`agate/platform-notes.md`](../agate-copy/agate/platform-notes.md)（现有 3 平台机制记录、DSH 草稿段、Codex 兼容性旧记录）
- [`agate/SETUP.md`](../agate-copy/agate/SETUP.md)（Claude Code `.claude/agents/` 软链注册步骤、DSH 步骤 2）
- [`agate/git-integration.md`](../agate-copy/agate/git-integration.md)（git hooks gate 机制）
