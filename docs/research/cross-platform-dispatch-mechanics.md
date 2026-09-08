# 跨平台派发 / CLI 调用机制调查

> **性质**：客观机制调查——CLI Agent 平台（Claude Code / Codex / OpenCode）的非交互调用、model 指定、子代理派发、返回与结果识别机制。**不含设计决策**；基于本报告的设计见 `docs/design-notes/design-dispatch-routing.md`。
> **调查方式**：每条结论标注证据强度——`[实测]` 端到端跑过、`[--help]` CLI 帮助逐条、`[文档]` 官方文档、`[自述]` 让运行中的模型报告自己的工具/参数、`[内省]` 读二进制或包、`[推断]` 由以上综合推出。
> **调查环境**：2026-09-08，本机 Linux（WSL2）。版本：**Claude Code 2.1.263**、**codex-cli 0.153.4**（ChatGPT 登录）、**opencode 1.18.11**（多 provider API key）。
> **时效性**：平台迭代快（比照 `agate/platform-notes.md` 惯例）。feature flag、model 阵容、flag 名都会变——落地前照 §10 清单逐平台复核。
> **DSH**：本轮不纳入，原因见 §9。

---

## 0. 速查矩阵

| 维度 | Claude Code | Codex | OpenCode |
|---|---|---|---|
| 非交互入口 | `claude -p '<prompt>'` | `codex exec '<prompt>'`（或 stdin） | `opencode run '<prompt>'` |
| model 指定（子进程） | `--model <alias或全ID>` | `-m/--model <MODEL>` 或 `-c model="..."` | `-m provider/model[#variant]` |
| 推理档（与 model 正交） | 无独立 flag（档位隐含在 model） | `-c model_reasoning_effort=<low\|medium\|high>` | `#variant` 后缀 或 `--variant <high\|max\|minimal>` |
| 权限/沙箱绕过 | `--dangerously-skip-permissions`（≡ `--permission-mode bypassPermissions`） | `--dangerously-bypass-approvals-and-sandbox`；中间档 `-s <mode>` + `--approve-for-me` | `opencode run --auto`（非默认，需显式传） |
| 原生子代理派发原语 | Task/Agent 工具 | `spawn_agent`（`collaboration` 工具族） | `task`(V1) / `subagent`(V2) 工具 |
| 子代理按次指定 model | **✅ 调用参数含 `model`** `[实测]` | **✅ 调用参数含 `model` + `reasoning_effort`** `[实测]` | **⚠ 调用无 model 参数**——改走命名 subagent 配置 `agents.<name>.model`；已 `[实测]` v1.18.11 生效（旧"被忽略"bug 不存在）|
| 结构化输出 | `--output-format json\|stream-json`（配 `--print`）`[实测]` | `--json`（JSONL 事件流）、`-o <FILE>`（最终消息） | `--format json`（JSONL）`[实测]`、`export`、`serve`/`acp` |
| 退出码可靠性 | 干净 `[实测 exit 0]` | **不可靠**——见 §6.2 | 失效 model 可能空返回或结构化 Error JSON `[实测]` |
| 完成/失败信号 | 正常：CLI 子进程=进程退出、native subagent=工具调用返回（§6.0）。均无内建 exec 超时；卡死判别归 RM-AG0055，非固定 timeout | ← 同 | ← 同 |
| 续接（子进程）| `-p --resume <id> '<prompt>'` | `codex exec resume <uuid> '<prompt>'` | `-s <id> '<prompt>'` / `-c` / `--fork` |
| 续接（native）| Task 续接原语未核实 | `followup_task`（`send_message` 是 agent 间通信，非续接）| `task(task_id=…, prompt=…)` |
| 认证 | login 或 API key，`~/.claude/` | `codex login`（ChatGPT vs API key，影响 model 访问），`~/.codex/` | 每 provider API key，`~/.local/share/opencode/auth.json` |

---

## 1. 非交互（headless）CLI 调用

### 1.1 Claude Code — `claude -p` `[--help]` `[实测]`
- `claude -p '<prompt>'`（`-p` = `--print`：打印响应并退出）。prompt 作参数或 stdin。
- `--output-format text|json|stream-json`、`--input-format text|stream-json`、`--include-partial-messages`（后两者仅配 `--print` + `stream-json`）。
- `--append-system-prompt <prompt>`、`--add-dir`、`--agents <json>`（内联定义自定义 agent）、`--restricted`（去掉 Bash 等执行类工具）。
- `--fallback-model <model>`：主 model 不可用时 CLI 自带的自动降级（与派发路由的候选链正交，可叠加）。
- `[实测]` `printf '...' | claude -p --model haiku --dangerously-skip-permissions` → 返回 `claude-haiku-4-5-20251001`、exit 0、非交互干净。

### 1.2 Codex — `codex exec` `[--help]` `[实测]`
- `codex exec '<prompt>'`（别名 `codex e`）。prompt 作参数或 stdin；stdin + 参数同给则 stdin 追加为 `<stdin>` 块。
- 子命令：`resume` / `fork` / `review`。
- 关键 flag：`-m/--model`、`-c key=value`（TOML 覆盖 `~/.codex/config.toml`，如 `-c model_reasoning_effort=high`）、`-s/--sandbox <read-only|workspace-write|danger-full-access>`、`--approve-for-me`、`--dangerously-bypass-approvals-and-sandbox`、`--json`、`-o/--output-last-message <FILE>`、`--output-schema <FILE>`（约束最终响应的 JSON Schema）、`--ephemeral`（不落 session 文件）、`--skip-git-repo-check`（默认拒绝在非 git 仓库运行）、`-C/--cd`、`--add-dir`。
- 启动打印 banner：`workdir` / `model` / `provider` / `approval` / `sandbox` / `reasoning effort` / `session id`。
- `[实测]` `codex exec --dangerously-bypass-approvals-and-sandbox` 端到端跑通，默认 model `gpt-5.6-terra` 正确应答、exit 0。

### 1.3 OpenCode — `opencode run` `[--help]` `[实测]`
- `opencode run '<message>'`。头行输出 `> <agent> · <model>`（如 `> build · deepseek-v4-flash`），之后是 assistant 回复。
- flag：`-m/--model provider/model`、`--agent <name>`、`--variant <effort>`、`--auto`（自动批准未显式拒绝的权限，官方标 dangerous）、`-c/--continue`、`-s/--session <id>`、`--fork`、`--share`、`--title`、**`--format <default|json>`**（`json` = "raw JSON events"）、`--print-logs`（日志到 stderr）、`--log-level <DEBUG|INFO|WARN|ERROR>`。
- 相关子命令：`opencode agent`（管理 agent）、`opencode models [provider]`（列可用 model）、`opencode auth` / `opencode providers`（凭证）、`opencode export [sessionID]`（session 全量 JSON）、`opencode serve`（headless server）、`opencode acp`（Agent Client Protocol server，结构化编程接口）。
- `[实测]` `opencode run --auto -m deepseek/deepseek-v4-flash` 端到端跑通。默认 model（`MiniMax-M3`）本机**空返回**——见 §2.2 / §6。

---

## 2. Model 指定

### 2.1 flag / 语法 `[--help]`
| 平台 | 写法 | 备注 |
|---|---|---|
| Claude Code | `--model haiku` / `--model claude-haiku-4-5-20251001` | alias 或完整 ID；alias `fable` < `haiku` < `sonnet` < `opus` |
| Codex | `-m gpt-5.6-terra` 或 `-c model="gpt-5.6-terra"` | 白名单见 `~/.codex/models_cache.json`；且 `codex exec -m` 与 `spawn_agent` 的可用集不同（§5.2） |
| OpenCode | `-m anthropic/claude-sonnet-4-5#high` | `provider/model` + 可选 `#variant`；provider 来自用户配置 |

### 2.2 model 可用性约束 `[实测]`
- **Codex——随账号类型变**：本机 ChatGPT 登录，默认 `gpt-5.6-terra` 可用；`-m gpt-5` 和 `-m gpt-5-codex` **均被 API 400 拒**（`"The 'gpt-5' model is not supported when using Codex with a ChatGPT account."`）。gpt-5 家族推测需 API key 账号。
- **OpenCode——配了不等于能用**：本机配了 MiniMax / DeepSeek / OpenRouter / xrouter 等多 provider，但默认 `MiniMax-M3` 空返回、`deepseek/deepseek-chat`（错误 id）报 `UnknownError`；`deepseek/deepseek-v4-flash`（`opencode models deepseek` 列出的有效 id）正常。**候选表里写的 model 必须是落地环境实际可用的**。

### 2.3 model 发现 `[--help]` `[内省]`
- Claude Code：alias 固定 4 档；完整 ID 见官方文档 / `--help` 里 `--model` 描述。
- Codex：`~/.codex/models_cache.json`（含 slug / display_name / `supported_reasoning_levels` / `visibility`）。
- OpenCode：`opencode models [provider]`；`~/.cache/opencode/models.json`。

### 2.4 非法 / 不可用 model 的失败形态 `[实测]`
| 平台 | 现象 |
|---|---|
| Codex | 先 `item.completed{item.type:error, message:"Model metadata ... not found"}`（退化警告），再 `error{status:400}` + `turn.failed`；进程可能仍 exit 0 |
| OpenCode | 结构化 `Error: {"name":"UnknownError","data":{"message":"...","ref":"err_..."}}`；或某些失效 provider 直接空返回 |
| Claude Code | 未单独测；`--model` 非法一般启动即报错 |

---

## 3. 推理档 / variant（与 model 正交的独立维度）

- **OpenCode** `[--help]` `[文档]`：`--variant <high|max|minimal>` 或 model 串里 `#high` 后缀（V2 用后缀，V1 的独立 `variant` 字段已合并进后缀）。官方描述 "provider-specific reasoning effort"。
- **Codex** `[实测]`：`-c model_reasoning_effort=<low|medium|high>`（子进程）；`spawn_agent(reasoning_effort=...)`（子代理）。启动 banner 有独立 `reasoning effort` 行。`~/.codex/models_cache.json` 列出某些 model 支持 `low/medium/high/xhigh/max`。
- **Claude Code**：无独立的 per-call reasoning-effort flag；档位隐含在 model 选择里。
- **结论**：`{cli, model}` 二元组不足以表达 OpenCode / Codex 的推理档，需要 `{cli, model, effort?}` 之类的三元。

---

## 4. 权限 / 沙箱绕过

**经验验证（本轮）**：cwd = 本仓库，让子进程往 `$HOME`（cwd 之外）写文件。
- Claude Code `[实测]`：`claude -p --dangerously-skip-permissions` → 成功写 `$HOME/...` 并读回。
- Codex `[实测]`：`--dangerously-bypass-approvals-and-sandbox` → 成功写 `$HOME/...`；**对照** `-s read-only`（无 bypass）→ "Couldn't create the file: the filesystem is read-only"（被沙箱拦）。
- OpenCode `[实测]`：`opencode run --auto` → 成功写 `$HOME/...`（`--auto` 自动批准了工作区外写）。
→ 三平台的绕过 flag 都真能拆掉工作区边界，且（Codex 已对照证明）不加 flag 时沙箱真会拦。

### 4.1 Claude Code `[--help]` `[实测]`
`--dangerously-skip-permissions`（≡ `--permission-mode bypassPermissions`）。另有 `--permission-mode <default|acceptEdits|bypassPermissions|plan|...>`、`--permission-prompts <host|none>`。

### 4.2 Codex `[--help]` `[实测]`
- **最高**：`--dangerously-bypass-approvals-and-sandbox`（"skip all confirmation prompts and execute commands without sandboxing. EXTREMELY DANGEROUS. Intended solely for ... externally sandboxed" 环境）。
- **中间档**：`-s/--sandbox <read-only|workspace-write|danger-full-access>` + `--approve-for-me`（"route approval requests through automatic review using the workspace-write sandbox"）。
- **已弃**：`--full-auto` / `-a` 已从 `codex exec` 移除；旧资料里"折中方案 `-a never -s workspace-write`"的写法过期。

### 4.3 OpenCode `[--help]` `[实测]`
`opencode run --auto`（"auto-approve permissions that are not explicitly denied"，官方标 dangerous）——**非默认行为，需显式传**。更细的控制在 `opencode.json` 的 `permissions` 规则（V2：ordered allow/deny/ask，`action` 如 `shell`/`edit`，按 resource glob 匹配）。

**为什么要拉平**（设计侧关注点）：跨 CLI 子进程若在该 CLI 的默认沙箱里做了权限妥协（某个该建的文件被拦），而验证环境（主 Agent 原生环境）更宽松，会导致"产出环境比验证环境严格"，gate 失真。

---

## 5. 原生子代理派发

### 5.1 有没有 / 叫什么
| 平台 | 原语 | 形态 |
|---|---|---|
| Claude Code | Task/Agent 工具 | 会话内工具，参数含 `subagent_type` + 可选 `model` |
| Codex | `spawn_agent` 等 `collaboration` 工具族：`spawn_agent` / `followup_task` / `send_message` / `interrupt_agent` / `list_agents` / `wait_agent` `[自述]` | 通用、prompt 驱动、**不限于预定义 skill-agent**。backing feature flag：`multi_agent` = stable / effective **true**（`codex features list`）；相关旧名 `collaboration_modes` / `multi_agent_mode` 已 `removed`、`multi_agent_v2` stable 但 false——**命名有变更史，目标版本上 `codex features list` 复核一次**。本轮 `spawn_agent` 无需任何 `--enable` 即可用 |
| OpenCode | `task`(V1) / `subagent`(V2) 工具 `[自述×2]` `[文档]` | 参数：`description` / `prompt` / `subagent_type`（`explore` \| `general` \| 用户配的命名 agent）/ `task_id`（续接）/ `command`。**无 model 参数** |

> 注：`codex` / `opencode` 顶层 CLI 子命令里没有"派子代理"这一项——子代理是**会话内工具**（跟 Claude Code 的 Task 工具一样），不能只看 `<cli> --help` 的子命令列表判断。

### 5.2 子代理的 model 怎么定
- **Claude Code** `[实测]`：Task 调用时传 `model` 参数。从 Sonnet 会话派 `model: haiku` → 子代理确为 `claude-haiku-4-5-20251001`。`.claude/agents/*.md` frontmatter 的 `model` 字段是另一条路径（曾有"被忽略、只单次传参才生效"的独立报告，未在本轮测；路由用途走单次传参，不依赖它）。
- **Codex** `[实测]`：`spawn_agent(task_name, message, model?, reasoning_effort?, fork_turns?)`。schema `[自述]`：`task_name`（必，小写字母/数字/下划线）、`message`（必）、`fork_turns`（`"none"|"all"|正整数串`，默认 `"all"` — 控制上下文 fork）、`model`（枚举，ChatGPT 账号下为 `gpt-5.6-terra | gpt-5.6-luna | gpt-5.5 | gpt-5.4-mini`——**比 `codex exec -m` 的可用集更宽**）、`reasoning_effort`（`low|medium|high|xhigh|max|ultra`）。实测：父 `reasoning effort: medium`，`spawn_agent(model="gpt-5.6-terra", reasoning_effort="high")` 起的子代理回报 `gpt-5.6-terra high`——**按次可指定 model + reasoning_effort**。
- **OpenCode** `[实测]` `[文档]`：工具调用**不传 model**。model 定在**命名 subagent 配置**：`agents.<name>.model`（V2：`"provider/model#variant"`；V1：`model` + 独立 `variant`）。**实测 v1.18.11**：项目 `opencode.json` 配 `agent.agate-child-pro = {mode: subagent, model: "deepseek/deepseek-v4-pro"}`，父会话 `-m deepseek/deepseek-v4-flash` 用 `task` 派 `subagent_type="agate-child-pro"` → 子代理回报 `deepseek/deepseek-v4-pro`（配置的 model，非父的）。**旧"bug ① model 被忽略"在本版本不存在**；自定义 `mode: subagent` agent 也正常出现在 `task` 可派列表（旧"bug ③"同不存在——之前只见 `explore`/`general` 是因为没配自定义 agent）。官方："A child session uses its subagent's configured model, or inherits the parent when none configured"；父 `opencode run -m` 切的是 session model、不改 agent 配的 model——对"子代理跑在它被指定的 model 上"反而正好。

### 5.3 深度 / 权限继承
- OpenCode `[文档]`：`subagent_depth` 默认 `1`（primary 可派 subagent，subagent 不能再派）；设 `2` 放开一层。子代理"currently uses its own configured permissions, not a restricted copy of the parent's"。
- Codex `[文档]` `[本轮未测]`：agate `platform-notes.md` 早期"兼容性观察记录"提过 `Codex subagent max_depth=1`（写于 subagent workflows 默认启用之前）。本轮 `spawn_agent` 单层验证生效、未测嵌套深度——落地前实测 `spawn_agent` 内再 `spawn_agent` 的行为。
- agate 协议侧另有约束（非平台）：`dispatch-protocol.md`「subagent 自主再派发」——子任务写权限是父权限的严格子集、不写 `.state.yaml`、不产生独立 phase。

### 5.4 predefined vs generic
- **Codex `spawn_agent`**：通用 prompt 定义，不限于预定义。
- **OpenCode**：只派**已注册的 agent**（内置 `explore` / `general` + 用户在 `agents` 配的）。`mode: primary|subagent|all`（缺省 `all`）；`hidden: true` 藏 `@` 菜单但 `task` 仍可 invoke；`permission.task`（V1）/ `subagent`（V2）glob 控制父能派哪些，`deny` 会把该 agent 从工具描述里整个删掉。本机 `"agent": {}` 未配自定义 agent，故 `task` 只列 `explore`/`general`（不是 bug，是没配）。
- **Claude Code**：`subagent_type` 选类型 + 单次 `model` 覆盖。

---

## 6. 返回 / 输出与结果识别

### 6.0 完成 / 失败信号 —— 正常情况不靠超时

**两条派发路的正常结束信号都是内在的，`timeout` 不是完成机制：**

| | 完成信号（正常） | 失败信号 | 谁在管 |
|---|---|---|---|
| **CLI 子进程**（`codex exec` / `claude -p` / `opencode run`）| **进程退出**——`exec`/`-p`/`run` 都是跑到完成才退出，进程结束即"done"。再解析结构化输出取细节（§6.1）| 见 §6.2 / §6.3——退出码对 Codex 失败不可靠，但结构化流里有（`turn.failed` / Error JSON / `stop_reason` 非 `end_turn`）| 调用方 `wait(pid)` |
| **native subagent**（Task / `spawn_agent`+`wait_agent` / `task`）| **工具调用返回**——平台阻塞该次调用直到子代理跑完，把结果返给父（本会话三平台各 `[实测]` 干净拿到子代理返回）| 工具调用返回 error → 父当候选失败、走下一候选 | 平台 |

**`timeout` 只是异常兜底**——进程/工具调用真卡死、结构化事件永不到来时的最后手段。**固定紧超时会误杀合法长任务**（本该 10min 的任务因 timeout=5min 被强杀），这不算异常处理、算违规处理，与协议自身防的"主 Agent 图省事强行中止在干活的 subagent"同类。因此：
- 若用外层 `timeout`，值必须**匹配任务预期**、宁宽勿紧，不拍脑袋。
- "卡死 vs 慢"的判别**直接复用 RM-AG0055 已落地的命令流日志机制**（下节）。
- 三平台 `[--help]` 确认均无内建 exec 超时参数；Codex `[实测]` SIGTERM 后无残留进程。

### 6.0.1 卡死检测：复用 RM-AG0055 命令流日志（不自造）

RM-AG0055（TAG0028，**已落地**——`agate/scripts/agate-cmdstream-{adapters,detect,ir}.py`）就是"subagent 是否卡死 / 在有效运行"的既有机制，派发路由**直接用，不新造超时**：

- **原理**：从平台会话记录**外部**读活动信号（不依赖 subagent 配合），统一为 `CommandRecord` IR，检测引擎平台无关。三类机械信号——**调用冻结**（未结束 tool/call 超 `expected×2`，兜底 300s/900s）、**活动冻结**（无未结束 call 且思考/输出/工具三类活动事件都超 60s/300s）、**逻辑空转**（同「命令+exit+输出哈希」在 10 条窗口内重复 ≥5）。定位是"**证据 + 触发核查，不自动判死**"。
- **适配器模式**：`CommandStreamAdapter` 基类（`probe` / `list_sessions` / `read_commands`）+ 注册表。**已实现：`claude-code`（`~/.claude/projects/**/​<sessionId>.jsonl`，子代理在 sidecar `subagents/agent-*.jsonl`）、`opencode`（SQLite `~/.local/share/opencode/opencode.db`）、`dsh`（`~/.dsh/sessions/**/*.jsonl.zstd`，子 agent 按 `delegationDepth` 独立文件）**。
- **对派发路由的映射**：

  | 路由形式 | 卡死检测覆盖 |
  |---|---|
  | `cli: native` / 子进程 · Claude Code | ✅ `ClaudeCodeAdapter` 直接覆盖（含 Task 子代理 sidecar）|
  | `cli: native`（命名 subagent）/ 子进程 · OpenCode | ✅ `OpenCodeAdapter` 直接覆盖 |
  | `cli: codex`（子进程）/ `spawn_agent`（`cli: native`）· Codex | ⚠ **缺 `CodexAdapter`**——数据源 `~/.codex/sessions/**/*.jsonl`（+ `codex exec --json` 事件流）；`spawn_agent` 子会话疑似同 DSH 的 `delegationDepth` 式独立文件。按 RM-AG0055 §3.4.4"未来接入 Codex/Cursor：约一个文件"——**只写一个适配器 + 注册表加一行，检测引擎/阈值零改动** |

- **落地时的集成点**：spawn 子进程 / 调 `spawn_agent` 时**捕获其 session id**，交给命令流监控用来定位该会话的记录文件。这是路由层要补的唯一衔接，不是新机制。

#### 6.0.2 CLI 子进程形式的存活性——比 native 更强、更便宜

RM-AG0055 的命令流机制是为"看不见进程"的原生派发（Task 工具黑盒、无 PID）设计的。**CLI 子进程形式多两层 native 没有的信号**：

| 层 | native subagent | CLI 子进程 |
|---|---|---|
| 完成 | 工具调用返回 | `wait(pid)` — 进程退出 + 退出状态 |
| **进程还活着吗**（崩溃 / OOM kill / 僵尸）| 只能由 RM-AG0055「活动冻结」间接推 | **`kill -0 pid` / `/proc/<pid>/stat` 状态位——直接、极便宜、立刻分辨崩溃**（对应 RM-AG0055 §3.4.1 表第一行"会话/进程被杀"，子进程形式不用推、直接看）|
| 卡在调用 / 逻辑空转 / 只思考不动 | RM-AG0055 命令流（读会话文件）| **同 RM-AG0055 命令流**，但源可直接取 **`--json` / `--format json` / `--output-format stream-json` 的 stdout 实时事件流**——不用去找/解会话文件；仍需把事件映射到 IR 与三信号 |
| 轮询时机 | 阻塞派发（Task 工具）主 Agent 被阻塞 → RM-AG0055 §3.4 降级为"中止前查一次" | 路由脚本 spawn 子进程后**不被阻塞**（§2.5）→ 拿到 RM-AG0055 §3.3 那种**主动轮询**能力（周期查 PID + tail stdout 流），不是降级路径。注：§3.3 原文机制是 DSH 后台任务的心跳文件；子进程形式是"同款轮询能力、换成 PID/stdout 实现" |

**结论**：CLI 子进程形式的存活性判定是三种路由形式里最好的——PID 给"死没死"的确定信号，`--json` stdout 给"卡没卡"的活动流，且不受阻塞派发限制。`kill -0` 与命令流两者互补：前者抓崩溃/OOM/僵尸（进程没了），后者抓"进程活着但卡住/空转"。

### 6.1 CLI 子进程输出形态
| 平台 | 默认 | 结构化 |
|---|---|---|
| Claude Code | `-p` 纯文本 | `--output-format json` `[实测]`：单 JSON，含 `stop_reason`（`end_turn` = 正常）、`session_id`、`total_cost_usd`、`usage`、`modelUsage`（**逐 model 用量——可据此确认实际跑了哪个 model**）。`stream-json` = 实时事件流。仅配 `--print` |
| Codex | banner + 文本；末尾复述 tokens used | `--json` → JSONL：`{"type":"thread.started",...}` / `item.completed`（`item.type` 可为 `error` 等）/ `turn.started` / `turn.completed` / `turn.failed`（`error.message` 结构化）。`-o <FILE>` 写最终消息 |
| OpenCode | 头行 `> <agent> · <model>` + assistant 回复 | `opencode run --format json` `[实测]`：JSONL，`type` 区分——`step_start` / `text`（`part.text` = 回复文本）/ `step_finish`（`part.reason:"stop"` = 正常结束，`part.tokens{total,input,output,reasoning,cache}` + `part.cost`）；均带 `sessionID`。另 `opencode export [sessionID]` 出 session 全量 JSON；`opencode serve` / `acp` 提供 headless/结构化编程接口 |

### 6.2 退出码可靠性 `[实测]`
- **Claude Code**：`-p` 实测 exit 0 干净，可信。
- **Codex：不可靠**。两种失败都可能落在一个 `exit 0` 的进程里：① 未认证 → 打 banner 后对 `wss://api.openai.com/v1/responses` 反复 401 重试；② 账号不支持所配 model → 先过"CLI 已认证"这层、真派发才 `turn.failed{status:400}`。**必须解析 `--json` 事件流**（`turn.failed` / `item.type:error`）判成败，不能只看退出码。
- **OpenCode**：失效 model 可能**空返回**（`MiniMax-M3` 实测：只有头行，无内容，exit 0）或**结构化 Error JSON**（`deepseek/deepseek-chat` → `Error: {"name":"UnknownError",...,"ref":"err_..."}`）。

### 6.3 失败特征签名
| 失败类型 | Claude Code | Codex | OpenCode |
|---|---|---|---|
| 未认证 | 启动即报未登录 | banner 后 `401` 重试循环（`wss://.../responses`） | provider 无凭证时报错 |
| model 不可用 | `--model` 非法启动报错 | `item error "metadata not found"` + `turn.failed{400}` | `UnknownError` 或空返回 |
| 空返回 | — | — | 头行有、内容空（失效 provider） |
| 卡死（真·无响应）| 正常完成靠进程退出/工具返回（§6.0），不靠超时；真卡死归 RM-AG0055 活动感知检测，外层 `timeout` 仅作宽松兜底 | | |

### 6.4 结果校验建议（呼应 agate D2「假完成校验」）
子进程返回后，调用方（脚本 / 主 Agent）应做：① 约定产出文件存在且非空、格式合法；② **对 Codex 解析 `--json` 的 `turn.completed` vs `turn.failed`**；③ 对 OpenCode 判空返回 + 结构化 Error；④ 亲跑 gate 命令验门槛，不信子进程自述。

---

## 7. 会话续接 / resume

### 7.1 CLI 子进程形式的续接 `[--help]` `[文档]`

| 平台 | 命令 | 机制 |
|---|---|---|
| Claude Code | `claude -p --resume <id> '<新 prompt>'` / `--continue` | 读 `~/.claude/projects/` 的 transcript 重建对话历史。已知 issue #43696："resume/continue 后上下文完全丢失"的独立报告（未确认是否已修） |
| Codex | `codex exec resume <uuid> '<新 prompt>'` / `--last` | JSONL rollout 存 `~/.codex/sessions/`。官方明说："What doesn't persist is the model's in-context state ... reads the transcript history to reconstruct context, rather than resuming from an actual saved model state" |
| OpenCode | `opencode run -s <id> '<新 prompt>'` / `-c` / `--fork` | SQLite `~/.local/share/opencode/`。同为"重建"非"恢复" |

三平台都支持"resume 到既有 session + 追加一条新 prompt"——正好是评审打回场景需要的形态。

**`[实测]`（Codex，2026-09-08）**：`codex exec` 埋一个 token `ZQ-4297-KX` → 拿 `thread_id` → `codex exec resume <id>` 无提示问"刚才让你记的 token 是什么" → 答 `ZQ-4297-KX`。**续接确实带上下文**。（Claude Code / OpenCode 子进程续接本轮未实测，仅据 `--help` + 文档。）

**"重放重建"不是"状态冻结"——属实，且对这几个工具是普遍情况，不是"某种情况"**：
- **架构层面**：底层 API（Anthropic Messages / OpenAI Responses）都是**无状态**的——每次请求带全量 message 数组，服务端不保留任何跨请求的模型推理状态。CLI 的"session"是**客户端的 transcript 文件**（Claude Code JSONL / Codex JSONL rollout / OpenCode SQLite）。resume = 读 transcript → 作为 context 重新发一遍。
- **Codex 官方原文**：见上表——明说"模型的 in-context state 不持久化，reopen 时读 transcript 重建，而非从保存的模型状态恢复"。
- **观察佐证**：上面 resume 那一轮，prior transcript 被重新计费（不是只算新增的问答）。
- **什么时候会和"没被打断过"不一样**（多数情况一致，以下才偏差）：① replay 有 bug（Claude Code #43696：resume 后模型看不到任何 prior context——独立报告、未确认已修）；② 原会话长到触发过 compaction/截断，resume 重放的是**压缩后**的 transcript，被summarize掉的细节丢了；③ transcript 存的是**最终产出 + tool 调用**，不存模型每轮的内部思考链——resume 后模型"记得做过什么/结论是什么"，但不记得"当初为什么在某个边界情况这么判"，得从产出物重新推。

### 7.2 native subagent 形式的续接 `[自述]`

| 平台 | 续接原语 | 依据 |
|---|---|---|
| Codex | `followup_task`（`collaboration` 工具族，A8）| 对既有 spawned agent 追发任务。（`send_message` 是多 agent 间通信、不是"续接已完成的子代理"，不算续接原语）|
| OpenCode | `task(task_id=<既有>, prompt=<新>)` | `task` schema 的 `task_id` 参数："optional, resumes a prior subagent session"（A9）|
| Claude Code | Task 工具是否有续接原语**未核实**（子进程形式用 `--resume`）| — |

### 7.3 用于评审打回循环（设计 1 → 评审打回 → 续 → 改 → 重交）

- **续接优先、重起兜底**：打回后若重做仍走同一 target（同 cli+model / 同 subagent），优先用上表的续接命令/原语，把评审意见作为新 prompt 传入——子代理保留自己"当初为什么这么设计"的上下文，比重起省一大截。session id 在 spawn 时已为存活监控捕获（§6.0.1），续接复用同一个，衔接成本很小。
- **续接是"重放重建"不是"状态冻结"**（本节 §7.1；三平台 + DSH 亦然）——所以**不假设续接必成功**：续接后上下文明显丢失 / 重做 fallback 到了不同 target → 旧 session 作废，退化为全新派发、prompt 里完整带回评审意见 + 必要上下文重申。等价于该候选探测失败走 §2.2 的降级逻辑，不需要额外机制。

---

## 8. 认证 / 配置位置 `[内省]`

| 平台 | 配置 | 认证 |
|---|---|---|
| Claude Code | `~/.claude/` | login 或 API key |
| Codex | `~/.codex/config.toml`（`model` / `model_reasoning_effort` / `projects.<path>.trust_level`）；`codex features list/enable/disable`；`~/.codex/{skills,memories,goals_*.sqlite,plugins}/` | `codex login`（ChatGPT）或 API key env——**账号类型影响可用 model**（§2.2） |
| OpenCode | `~/.config/opencode/opencode.json[c]`（`agents` / `provider` / `permissions` / `model` / `small_model` / `experimental.subagent_depth`）；`~/.config/opencode/{agents,skills,instructions}/` | 每 provider API key，存 `~/.local/share/opencode/auth.json`；`opencode auth list` 查 |

---

## 9. DSH（本轮不纳入）

- headless 能力需显式装 `dsh-headless` 插件，非内置。
- model 指定走配置文件（`$DSH_HOME/settings.yaml`），未确认支持单次调用临时覆盖。
- 结构化输出（JSON/JSONL）官方支持程度不明，已发现的相关能力是第三方社区扩展。
- Developer Preview，`platform-notes.md` 一贯列为"新兴平台，需持续复核"。
- 待其官方 headless CLI 能力成熟（文档化的结构化输出 + 单次 model 指定）后重新评估。

---

## 10. 版本与时效 —— 复核清单

平台迭代快，本报告结论有时效。落地前逐平台复核 §0 矩阵每格，重点：

1. **flag 名**：`--dangerously-*` 系列、`-s`/`--approve-for-me`、`--auto`、`--variant`、`--format`/`--output-format` 是否改名或语义变。
2. **Codex feature flag**：`multi_agent` / `spawn_agent` 在目标版本是否仍 stable+on（`codex features list`；命名有变更史）。
3. **model 阵容**：Codex 随账号类型（`codex exec --json` + `spawn_agent` 的 `model` 枚举各查一次）；OpenCode `opencode models <provider>` 实际可用清单（部分配置会失效）。
4. **子代理 model 传参**：Claude Code Task `model`、Codex `spawn_agent(model=)`、OpenCode 命名 agent `model` 各端到端跑一次（本轮三条均已通，版本升级后复跑）。
5. **退出码 vs 结构化事件**：Codex 仍需解析 `--json`（`turn.failed`）、OpenCode `--format json` 的 `step_finish.part.reason` 判成败、OpenCode 空返回判定仍成立。

---

## 11. 未尽项状态

按对派发路由设计的影响排序。本轮（2026-09-08）把阻断项都测掉了；剩下的是环境相关自查或低优。

| # | 项 | 状态 |
|---|---|---|
| 1 | **OpenCode `agents.<name>.model` 是否生效** | ✅ **已测通**——项目配 `agent.agate-child-pro={mode:subagent, model:"deepseek/deepseek-v4-pro"}`，父 `-m deepseek/deepseek-v4-flash` 派它 → 子回报 `deepseek/deepseek-v4-pro`。旧 bug ①/③ 在 v1.18.11 均不存在。**OpenCode `cli: native` 可行**（走命名 agent 间接路，§5.2） |
| 2 | **完成/失败信号 + 卡死处理** | ✅ **清楚**（§6.0 / §6.0.1）——正常完成：CLI 子进程 = 进程退出、native subagent = 工具调用返回，两条路内在可靠，不靠超时。卡死检测**直接复用 RM-AG0055 已落地的命令流日志**（`agate-cmdstream-*.py`）：Claude Code / OpenCode 适配器现成覆盖；**唯一缺口 = Codex 适配器**（按 RM-AG0055 §3.4.4"约一个文件"）。集成点 = spawn 时捕获 session id。固定紧 timeout 会误杀长任务=违规处理，不采用 |
| 3 | **权限对等经验验证** | ✅ **已测通**——三平台加绕过 flag 均能写 cwd 外（`$HOME`）；Codex 对照 `-s read-only` 确认沙箱真会拦（§4） |
| 4 | **Codex `spawn_agent` 完整 schema** | ✅ **已拿到**——`task_name`(必)/`message`(必)/`fork_turns`("none"\|"all"\|N，默认"all")/`model`(枚举 4 个)/`reasoning_effort`(6 档)（§5.2）。未见 background/timeout/permission 字段（模型自述称"complete"） |
| 5 | **Codex API-key 账号 model 阵容** | ⏸ **环境自查**——本机 ChatGPT 账号：`codex exec -m` 只 `gpt-5.6-terra`，但 `spawn_agent` 的 `model` 枚举有 `gpt-5.6-terra/gpt-5.6-luna/gpt-5.5/gpt-5.4-mini` 4 个。API-key 账号有无 `gpt-5`/`o3` 等需在那种环境跑 `codex exec --json` 试 |
| 6 | **OpenCode `--format json` 事件形态** | ✅ **已拿到**——`step_start`/`text`/`step_finish`（`reason:"stop"` + tokens + cost），§6.1 |
| 7 | **dispatch-context 文件可读性** | ✅ 隐含已验——§4 权限验证里各 CLI 子进程都能读写指定路径文件；且可 `--add-dir`/`-C` |
| 8 | **DSH** | ⏸ 本轮不纳入（§9），设计已排除 |
| 9 | **Claude Code frontmatter `model` 字段** | ⏸ 低优——路由器走单次传参不依赖它 |
| 10 | **续接**（§7）| ✅ 命令/原语齐全：子进程三平台 `--resume`/`resume`/`-s` + native 的 `followup_task`/`task_id`；⏸ 待核 = Claude Code native 续接原语、各平台续接后的实际上下文保真度（重放式，非冻结）。评审打回续跑设计见 `design-dispatch-routing.md` §2.4.1 |

---

## 附录：本轮实测记录

| # | 命令 | 观察 |
|---|---|---|
| A1 | Agent 工具 `model: haiku`（父 Sonnet 5 会话） | 子代理回报 `Haiku 4.5 / claude-haiku-4-5-20251001` — Claude Code 单次 model 覆盖生效 |
| A2 | `printf ... \| claude -p --model haiku --dangerously-skip-permissions` | 返回 `claude-haiku-4-5-20251001`，exit 0，非交互干净 |
| A3 | `tmux new-session -d` / `list-sessions` / `list-clients` / `kill-session`（tmux 3.4） | 全部按预期；本机已存在别的 session（`0`、用户的 `cc`）→ 会话名需命名空间 |
| A4 | `codex exec --dangerously-bypass-approvals-and-sandbox`（默认 model） | 端到端跑通，`gpt-5.6-terra` 应答，exit 0，banner 显示 `approval: never` / `sandbox: danger-full-access` |
| A5 | `codex exec -m gpt-5-codex` / `-m gpt-5`（ChatGPT 账号） | `turn.failed` `{status:400, "not supported ... with a ChatGPT account"}` |
| A6 | `codex exec -c model_reasoning_effort=high` | banner `reasoning effort: high` — 生效 |
| A7 | codex `spawn_agent(model="gpt-5.6-terra", reasoning_effort="high")`（父 `medium`） | 子代理回报 `gpt-5.6-terra high` — 按次 model + effort 生效 |
| A8 | codex `[自述]` 工具清单 | `functions.exec` `functions.wait` + `collaboration`: `spawn_agent` `followup_task` `send_message` `interrupt_agent` `list_agents` `wait_agent` |
| A9 | `opencode run --auto -m deepseek/deepseek-v4-flash`（self-report） | 工具：`bash read write edit glob grep todowrite task skill webfetch peeklink_*`；`task` 参数 `description/prompt/subagent_type(explore\|general)/task_id/command`，**无 model** |
| A10 | `opencode run`（默认 `MiniMax-M3`） / `-m deepseek/deepseek-chat` | 前者空返回；后者 `UnknownError` — 部分配置 model 失效 |
| A11 | OpenCode 官方文档 `opencode.ai/docs/agents` + `/v2/docs/agents` | 确认 model 走 `agents.<name>.model = "provider/model#variant"`；子用自己配的 model 或继承父；`mode`/`hidden`/`permission.task` 语义 |
| A12 | codex `[自述]` `spawn_agent` schema dump | `task_name`(必) / `message`(必) / `fork_turns`("none"\|"all"\|N，默认"all") / `model`(`gpt-5.6-terra`\|`gpt-5.6-luna`\|`gpt-5.5`\|`gpt-5.4-mini`) / `reasoning_effort`(low\|medium\|high\|xhigh\|max\|ultra) |
| A13 | 项目 `opencode.json` 配 `agent.agate-child-pro={mode:subagent, model:"deepseek/deepseek-v4-pro"}`；父 `-m deepseek/deepseek-v4-flash` 用 `task` 派 `subagent_type="agate-child-pro"` | 子代理回报 `deepseek/deepseek-v4-pro` — **命名 subagent 的 model 配置生效**（旧 bug ① 不存在）；自定义 subagent 出现在 `task` 可派列表（旧 bug ③ 不存在） |
| A14 | 权限对等：cwd=本仓库，令子进程写 `$HOME/agate-permtest-*.txt` | `claude -p --dangerously-skip-permissions` ✅ 写成功；`codex exec --dangerously-bypass-approvals-and-sandbox` ✅ 写成功、对照 `-s read-only` → "filesystem is read-only"（拦）；`opencode run --auto` ✅ 写成功 |
| A15 | `opencode run --format json 'say ok'` | JSONL：`step_start` / `text`(`part.text`) / `step_finish`(`part.reason:"stop"` + `part.tokens{...}` + `part.cost`) |
| A16 | `claude -p --output-format json` | 单 JSON：`stop_reason:"end_turn"` / `session_id` / `total_cost_usd` / `usage` / `modelUsage`（逐 model 用量） |
| A17 | `codex features list` | `multi_agent` = stable/on（撑 `spawn_agent`）；旧名 `collaboration_modes`/`multi_agent_mode` removed；`multi_agent_v2` stable/false |
| A18 | SIGTERM `codex exec` 子进程 | 无残留进程；三平台 `--help` 均无内建 exec 超时参数 |
| A19 | tmux 3.4 真人 attach 全链路（`new-session -d "{命令} \| tee {file}"` → 用户 attach）| 用户确认：pane 实时滚动 ✅；`Ctrl+b d` 干净 detach、会话继续 ✅；有 client attach 时 `kill-session` → client 干净退回系统 shell（无卡/花屏），但会把"切过去的工作 client"整个拽出 tmux → 佐证"有 attach 就延迟清理"必要；`\| tee` 令 pane 与 capture 文件同步（人看 pane / 脚本 tail 文件）；`printf\|<cli>` 系列已证非 tty 下输出正常 |
