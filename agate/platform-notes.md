# Platform Notes — 各平台适配说明

> 职责边界：平台适配权威源——各 Agent 平台（OpenCode / Claude Code / Codex / DSH 等）能力矩阵、Windows 原生安装指南（详见职责声明表，P2-design.md §0）。
> **接入步骤**见 `SETUP.md` 步骤 2（或其推荐形式：一条命令 `python3 ~/.agate/scripts/agate-setup.py`）；本文只做**能力差异与平台特性**说明，不重复接入命令。
> **结构**：「平台速览」→ 各平台详情 → 「受限 harness 通用约束」（沙箱写权限 + 进程存活）→ 「Windows 原生」（运行环境）→ 「跨平台通用机制」两节（gate 平台无关性 / 跨 CLI 判成败）。

不同 Agent 平台对 agate 的支持程度不同，本文记录已知情况。

---

## 平台速览

| 平台 | 身份接入物 | 派发 subagent | 适用阶段 |
|------|-----------|--------------|---------|
| **OpenCode** | `.opencode/agents/orchestrator.md`（或全局同名路径）| `task` 工具 | 完整 P0-P8 |
| **Claude Code** | `.claude/agents/orchestrator.md`（或全局同名路径）| `Task` 工具 | 完整 P0-P8 |
| **Codex** | `~/.agents/skills/agate-protocol/SKILL.md`（无 agent 注册机制，身份靠 skill）| 原生 `spawn_agent` | 完整 P0-P8 |
| **DSH** | agent-preset **声明块**（写进 profile 的 `cordis.patch.yml`；由 `agent.cordis.yml` + `preset.yml` 生成）+ `SKILL.md` | `subagent` / `subagent_fork` | 完整 P0-P8 |
| **Claude Project 会话**（claude.ai） | —（纯对话环境，无身份接入与派发）| ❌ 无 | 仅 P0-P2 |

> 与既有文档的关系：`README.md`「支持的平台」给的是**新用户视角**的推荐矩阵；本文是**能力细节**的权威源；`SETUP.md` 步骤 2 是**接入命令**的权威源。

---

## OpenCode

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具派发 subagent | ✅ 可用 | 使用方法 B（general subagent + prompt 注入角色文件）|
| 自定义角色（`--custom-role`）| ❌ 不可用 | issue #29616，subagent 无法加载自定义角色 |
| 本地开发环境 | ✅ 完整 | P3-P8 全部阶段可执行 |

**推荐方式（方法 B）**：派发时在 prompt 里直接写入角色定义文件路径，让 subagent 自己读取。不使用 `--custom-role` 参数。

**验证记录**（2026-06-12，派发机制首次验证）：

- Phase 1（方法 B 派发）✅
- Phase 2（方法 A 自定义角色）❌（issue #29616）
- Phase 3（上下文隔离）✅

完整验证报告存档：`archived/validation-report.md`

---

## Claude Code

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具派发 subagent | ✅ 可用 | Task tool 支持独立上下文 |
| 本地开发环境 | ✅ 完整 | P3-P8 全部阶段可执行 |
| 推理档（effort，与 model 正交）| ⚠ 按能力探测 | `claude` CLI 的 `--effort <low\|medium\|high>` flag——**2.1.266 [实测] 有** / **2.1.263 [实测] 无** / **引入版本未核实**。派发路由（TAG0034）按 `claude --help` 是否含 `--effort` 做**能力探测**分流：含则映射 `--effort <e>`、不含（旧版本）则省略该 flag、不报错。**不硬编码版本号**。`--effort bogus` 实测仅 Warning 不失败 |

---

## Claude Project 会话（claude.ai）

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具 | ❌ 不可用 | 纯对话环境，无 task 工具 |
| 本地开发环境 | ❌ 受限 | 网络受限，npm/pip 安装受影响 |

**适用范围**：仅适合 P0-P2（设计规划阶段）。P3-P8 需交接给 OpenCode / Claude Code 执行。

**典型工作方式**：用 Claude Project 完成 P0-P2 并 push 到 main，再切换到 OpenCode 执行 P3-P8。

---

## Codex

> 接入步骤见 `SETUP.md`「步骤 2-Codex」。已实机验证（**2026-09**，codex-cli **0.153.4**，**ChatGPT 登录**账号，本机 Linux/WSL2）——新兴平台，机制随版本变化快，落地前须在目标版本上 `codex features list` + `codex exec --help` 复核（比照本文 DSH 章 / OpenCode 章「新兴平台需持续复核」惯例）。涉及账号类型差异的项（尤其 model 阵容）本机为 ChatGPT 账号，API-key 账号环境本质不可得，标「待有该环境时补（非阻塞）」。

**平台形态**：Rust CLI（`@openai/codex`，`npm i -g`）；非交互入口 `codex exec`；会话记录为 rollout JSONL，落 `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO8601 秒精度>-<uuid>.jsonl`（按 UTC 日期分层，非 cwd 分层）。认证 `codex login`（ChatGPT 或 API key，账号类型影响可用 model）。

### 能力矩阵

| 能力 | 状态 | 说明 |
|------|------|------|
| 非交互入口 | ✅ 可用 | `codex exec '<prompt>'`（别名 `codex e`），prompt 作参数或 stdin。子命令 `resume` / `fork` / `review` |
| 本地开发环境 | ✅ 完整 | P0-P8 全部阶段可执行（`WORKFLOW.md`「已知适用环境」表已登记）|
| model 指定（子进程）| ✅ | `-m` / `--model <MODEL>` 或 `-c model="..."`（TOML 覆盖 `~/.codex/config.toml`）|
| 推理档（与 model 正交）| ✅ | `-c model_reasoning_effort=<low\|medium\|high>`（`spawn_agent` 侧为 `reasoning_effort` 参数，另含 `xhigh`/`max`/`ultra` 档）；启动 banner 有独立 `reasoning effort` 行 |
| 权限 / 沙箱绕过（最高档）| ✅ | `--dangerously-bypass-approvals-and-sandbox`（跳过全部确认 + 无沙箱执行，仅用于外层已隔离环境；实测真能拆掉工作区边界）|
| 权限 / 沙箱（中间档）| ✅ | `-s` / `--sandbox <read-only\|workspace-write\|danger-full-access>` + `--approve-for-me`（把审批走自动 review）。**注：`--full-auto` / `-a` 已从 `codex exec` 移除**——旧资料里「`-a never -s workspace-write` 折中」写法已过期 |
| 非 git 仓库运行 | 默认拒绝 | 需 `--skip-git-repo-check` |
| 结构化输出 | ✅ | `--json`（JSONL 事件流：`thread.started` / `turn.started` / `item.started` / `item.completed` / `turn.completed` / `turn.failed`）；`-o` / `--output-last-message <FILE>`；`--output-schema <FILE>` 约束最终响应 JSON Schema |
| 退出码可靠性 | ⚠ **不可靠** | 未认证（banner 后对 `wss://api.openai.com/.../responses` 反复 401 重试）与「账号不支持所配 model」（真派发才 `turn.failed{status:400}`）两类失败都可能落在 `exit 0` 的进程里——**退出码不可靠，须解析 `--json` 事件流**（`turn.failed` / `item.type=="error"`）判成败。此结论只针对 **turn 级失败**；per-command shell 执行的退出码见下「命令流适配」小节（rollout item 带数字 `exit_code`）|
| 会话续接（子进程）| ✅ | `codex exec resume <uuid> '<新 prompt>'` / `--last`；rollout JSONL 存 `~/.codex/sessions/`。属「读 transcript 重放重建」非「模型状态冻结」（官方明示）——实测续接确带上下文 |
| 会话续接（native）| ✅ | `followup_task`（对既有 spawned agent 追发；`send_message` 是 agent 间通信、非续接）|
| 原生子代理派发 | ✅ 见下 | 会话内工具 `spawn_agent`（`collaboration` 工具族）——顶层 CLI 无「派子代理」子命令 |

### model 阵容（随账号类型变）

- **ChatGPT 登录账号（本机验证环境）**：`codex exec -m` 默认 `gpt-5.6-terra`，实测可用；`-m gpt-5` / `-m gpt-5-codex` **被 API 400 拒**（`"The 'gpt-5' model is not supported when using Codex with a ChatGPT account."`）。model 白名单见 `~/.codex/models_cache.json`。
- **`spawn_agent` 的 `model` 枚举**（`[自述]`——运行中模型报告，非逐字 schema dump）：`gpt-5.6-terra` / `gpt-5.6-luna` / `gpt-5.5` / `gpt-5.4-mini`（比 `codex exec -m` 的可用集更宽）。`reasoning_effort` 枚举 `low|medium|high|xhigh|max|ultra`。
- **API-key 账号 model 阵容**：本会话未核实——本机为 ChatGPT 账号，API-key 账号环境本质不可得。**待有该环境时补（非阻塞）**（`codex exec --json -m gpt-5 <<< "hi"` + `spawn_agent(model=…)` 各枚举跑一遍；`verification_env_budget` 止损轮次 2）。

### 子代理派发（`spawn_agent`）与既有「Codex 兼容性」注记的时效

- **⚠️ 行为默认值 ≠ 能力开关**：能力上 `spawn_agent` 可用（见下条 feature flag），但会话上下文含 `<multi_agent_mode>`——「**除非用户或适用的 AGENTS.md / skill 指令显式要求，否则不要派发子 agent**」（实测 `codex debug prompt-input`，2026-09-21，0.153.4）。**Agateon 的模型建立在主 Agent 派发之上**，故在 Codex 上必须显式要求派发，否则**静默不派发**、P0-P8 失效。适配层 `assets/templates/codex/SKILL.md` 已写明该要求。
- backing feature flag：`multi_agent` = **stable / effective true**（实测 `codex features list`，0.153.4）——`spawn_agent` 无需任何 `--enable` 即可用。命名有变更史：`collaboration_modes` / `multi_agent_mode` 已 `removed`，`multi_agent_v2` stable 但 false（子会话 `session_meta` 却见 `multi_agent_version: "v2"` 字样——内部版本仍在演进）。**目标版本上 `codex features list` 复核一次**。
- `spawn_agent` 子会话是**独立的 `rollout-*.jsonl` 文件**（非父文件内嵌事件），与父文件同目录；子文件 `session_meta` 含 `parent_thread_id` / `thread_source=="subagent"` / `source.subagent.thread_spawn.depth`。**单层 `spawn_agent` 已实测可用**（P5 V3）；**嵌套深度（`spawn_agent` 内再 `spawn_agent`）P6 V7 已两次独立实测 `depth=2` 可用**（TAG0033，2026-09；`source.subagent.thread_spawn.depth == 2` 的孙会话）。
- **与 §4.1「gate 机制的平台无关性」节「Codex 兼容性」注记的交叉引用 + 时效**：那条 `Codex subagent max_depth=1` /「Codex 单层任务工具无法再派发」注记**写于 subagent workflows 默认启用之前**——按当前实测，`multi_agent` flag 已 stable/true、单层派发已实测可用；既有 `max_depth=1` 结论已经 P6 V7 复核**推翻**：嵌套 `spawn_agent` 实测 `depth=2` 可用（TAG0033，两次独立证实）。既有注记那几行事实内容不删（本节只做时效指针），全文档以本小节为该维度的时效口径，**不存在**「一处说无法再派发、另一处说已支持多层」的未标时效对立陈述。

### `spawn_agent` 参数 schema —— 证据强度 `[自述]`

`spawn_agent(task_name, message, model?, reasoning_effort?, fork_turns?)`：`task_name`（必，小写字母/数字/下划线）、`message`（必）、`fork_turns`（`"none"|"all"|正整数串`，默认 `"all"`）、`model`（枚举见上）、`reasoning_effort`（6 档）。

此 schema 为 **`[自述]`**（运行中模型报告自己的工具参数）——**不是**逐字 tool JSON schema dump（P1 spike 实测：令模型逐字输出内部 tool schema 被**模型受训拒绝**）。因此「未见 `background` / `timeout` / `permission` 字段」**只能表述为「`[自述]` 未提及」，不得升级为「这些字段一定不存在」的断言**。「穷尽 `spawn_agent` 参数 schema 直接实测」是**真机验证清单 V2 待执行项**（P5-P6，**换法**：读 codex 二进制 `strings` / 内省包内 schema 定义 / 或跨大量真实调用归纳 `function_call.arguments` 键并集），P6 归纳键并集后如实回写本段。

### 命令流适配（RM-AG0055 / CodexAdapter）

- `agate/scripts/agate-cmdstream-adapters.py` 的 **`CodexAdapter`（TAG0033 落地，2026-09）** 覆盖 Codex 平台的 subagent 存活 / 卡死检测。数据源 = `~/.codex/sessions/**/rollout-*.jsonl`（rollout JSONL），`ADAPTERS` 注册表键 `"codex"`；检测引擎 / 阈值 / `CommandRecord` IR / 既有三适配器零改动。
- **per-command 退出码**：rollout 的 `CommandExecution` item **带数字 `exit_code` 字段**（实测观察 `0` / 非 0）——`CommandRecord.exit` 直取，比 Claude Code / DSH 干净。上方「退出码不可靠」只针对 **turn 级失败**（`turn.failed{status:400}` / `item.type=="error"`），对 per-command shell 执行不成立。
- **`payload.item.status` 真机取值集**（P6 V6 实测，DEBT0035）：`completed`（成功终态）/ `failed`（**已结束但非 0 退出**——仍携带完整 `exit_code`（如 `2` / `137`）+ `payload.completed_at_ms` + `aggregated_output`；`sleep` 被 SIGINT 也落 `failed` + `exit_code=137`）/ `in_progress`（未结束）。`CodexAdapter` 以「有终态信号」判已结束——`status ∈ {completed, failed}` **或** 有 `completed_at_ms` **或** 有数字 `exit_code`（`_codex_is_finished`）；仅真·未结束（`item_started` 无 `item_completed`，或 `item_completed` 但三信号皆缺）才映射 `exit_signal="pending"`。旧口径 `status != "completed"` 会把真机 `failed` 终态误判为 pending 而丢失 `exit_code` + `output_hash`（P6 V6 修正 / DEBT0035）。
- **输出截断标记实测形态**（P5 V4）：item 上**无**布尔截断字段；截断标记出现在 `formatted_output`——`Warning: truncated output (original token count: N)` + 省略号包夹的 `…N tokens truncated…`（U+2026 省略号字符，非三个点）。`CodexAdapter` 截断检测据此（`_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"` 子串命中）→ `truncated=True` + `output_hash=None`。供未来复核 / RM-AG0055 §3.4.2 差异点 4 的 Codex 侧记录。

### 验证记录（Codex）

| 项 | 结论 | 阶段 |
|---|---|---|
| rollout JSONL 目录结构 / `CommandExecution` 字段形态 | 与解析假设一致（V1 PASS）| P5 |
| `spawn_agent` 子会话独立文件 + 父子关联字段 | 独立 `rollout-*.jsonl`，`thread_source=="subagent"` + `parent_thread_id`（V3 PASS）| P5 |
| 输出截断标记确切形态 | `formatted_output` 的 `Warning: truncated output ...` + `…N tokens truncated…`（V4 命中）| P5 |
| `multi_agent` feature flag | stable / true（V5 PASS）| P5 |
| 检测引擎对真实 Codex 会话判三态 | 归 P6（V6）| P6 |
| `spawn_agent` 嵌套深度 + `spawn_agent` schema 穷尽 | V7：嵌套 `depth=2` 实测可用；V2：跨 9 次真实调用键并集实测（P6 PASS，TAG0033）| P6 ✅ |
| API-key 账号 model 阵容 | 待有该环境时补（非阻塞，budget 轮次 2）| 待环境 |

验证环境：codex-cli **0.153.4**、**ChatGPT** 登录账号、本机 Linux（WSL2），验证日期 **2026-09**。

---

## DSH（deepseek-harness）

> 接入步骤见 `SETUP.md`「步骤 2-DSH」（接入命令单一真相源，本条目只做能力差异说明）；preset / skill 模板文件在 `assets/templates/dsh/`。已实机验证（2026-08-21，DSH v0.1.0-rc.8）——新兴平台，机制可能随版本变化。最近复核（2026-09-01，DSH v0.1.2-alpha.3，实机核验通过）：工具面（subagent / subagent_fork / workflow / ralph / goal）、preset 工具行包名与 delegation 组、skill 发现机制、`sampleOverCapGlobResults` 挂载关键字段均未漂移，与当前 DSH 标准 preset 结构逐行一致。**2026-09-24 修正**：preset 的**载体**变了——DSH ≥ **0.1.7-alpha.1** 起不再读目录式 `$DSH_HOME/.agent-presets/<id>/`，改为读 profile 自己 patch 文件里的声明行（见下「已知注意」）。

**平台形态**：pnpm monorepo + cordis 插件框架；身份注册用 **agent-preset**——声明行由 `agent.cordis.yml`（插件行列表）+ `preset.yml`（`name` / `description` / `order`）两个模板生成，写进 **profile 自己的 patch 文件** `~/.dsh/profiles/<profile>/cordis.patch.yml` 的托管块（定界符之间的整段，卸载按定界符精确摘除）；skill 是打包/分发单元（`SKILL.md` + frontmatter，自动进会话技能目录）。

**能力差异（与 OpenCode / Claude Code 对照）**：

| 能力 | OpenCode / Claude Code | DSH |
|------|---------------------|-----|
| orchestrator 身份注册 | agent md 文件软链（`mode: primary`）| agent-preset 声明行（`persona.prefix` + 工具行），写进 profile 的 `cordis.patch.yml` |
| 派发 subagent | task 工具 | `subagent` / `subagent_fork`（spawn / fork 两种上下文模式）|
| 批量并行派发 | 手工多路 task | **workflow 脚本**（agent / pipeline / parallel / phase）|
| 独立复核（judge）| 手工保证 fresh context | **ralph**（每轮全新 agent + bounded handoff）|
| 跨轮续跑 | 手动重开会话 | **goal**（持久化目标，自动续轮）|
| 实时 gate | 仅 git hook（commit 时）| 另可挂 **session hooks**（PostToolUse 每步触发）|

**已知注意**：

- 沙箱默认 workspace-write，协议本体目录可能只读（写仓库内文件 Errno 30）——任务工作区放可写位置
- DSH **无** `.claude/agents/*.md` 等价物——不要试图把 `orchestrator-template.md` 软链进 DSH 目录，用 preset（**且必须是声明行**：DSH ≥ 0.1.7-alpha.1 起目录式 preset 已不被读取）
- **目录式 preset 已死**（DSH ≥ **0.1.7-alpha.1**，commit `d1e22a7e24`）：`$DSH_HOME/.agent-presets/<id>/` 不再被任何代码读取（上游 skill 原文："Nothing reads that directory any more."）。旧的 `~/.dsh/.agent-presets/agate/` **留着无害但会误导**——看起来像"已接入"，而会话选择器里没有「Agateon 编排者」；本机实测其代价是 2026-09-20 22:25 之后再无一个会话用上 agate preset（全部落 `standard`）。现行载体 = profile patch 的托管声明块，`agate-setup.py --list` / `agate-summary.py` 检查的正是该位置
- **插件包改名（激活失败陷阱）**：`@deepseek-ai/dsh-workflow-worker-thread` 在 0.1.7 已不存在 → 现名 **`@deepseek-ai/dsh-workflow-ptc`**。手抄旧 preset 而不改这一行会让 preset **挂载/激活失败**；`agate_common.dsh_preset_block()` 生成时自动替换（上游要求逐个核对包名，理由即此）
- **`agent-team` 组合包：默认关闭；agateon 会话不建议启用（启用会形成两套并存的委派面）**。上游 README（`packages/experimental/agent-team-profile/README.zh.md`）原文：*「普通 subagent 委派及名称重叠的 global child control 会被禁用；Workflow 仍可创建 fresh 子代理。本包随 dsh 安装提供，**默认关闭**」*。
  **⚠️ 冲突的确切形态（同 README「已知限制」原文，勿升级为「preset 会失效」）**：该组合包作用在**顶层**——注册 team 工具（`spawn_teammate` / `wait_agent` / `team_task_*` + Web 成员与任务看板）并禁用**顶层**的 subagent 控件；而本 preset 把 `subagent` / `subagent_fork` / `list_agents` / child control 挂在**预设作用域**（`config.plugins`），上游「已知限制」明确写：*「Web 预设仍可在预设作用域挂载 continuable Subagent 控件；**顶层组合包不会替换这些注册**」*。
  ⇒ **实际后果是「两套委派面并存」**（team 工具 + preset 内 subagent），而非「agateon 工具映射失效」；
  - **本仓曾把这一条写错两次**，留存备查：① 最初（RM-AG0076 原始登记）称「本机 profile 已挂该 bundle、两套工具**同时可见**、`disabled` 未生效」——**事实前提为假**（本机 `dsh.profile.bundles` 未含该包；「同时可见」是**启用后**才会出现的状态，不是当前状态）；② 更正 v1 又写成「启用后 preset 工具映射**整体失效**」——**与上游「已知限制」直接冲突**（预设作用域不受顶层 disable 影响）。**正确表述只有上面这一种**：默认关闭 → 若启用则两套并存。
  - **代价（为何仍不建议启用）**：编排者面对两套面须自行判断用哪套；团队任务板与 `.state.yaml` 形成**第二个协调基质**，与「单一权威 + 阶段门禁 + 单一作者」竞争。**agateon 已有等价能力**：批量并行 = `workflow`；独立 fresh 复核 = `ralph`；跨轮续跑 = `goal`。
  - **可执行的检测（不是纯文档声明）**：`agate-setup.py` 在注册 DSH preset 时读同目录 `package.json` 的 `dsh.profile.bundles`，若含 agent-team 则打印冲突告警（**仅提示、不阻断**——那是用户对自身 profile 的选择）。自查：`python3 ~/.agate/scripts/agate-setup.py`，或直接看 `~/.dsh/profiles/<profile>/package.json`。本机 2026-09-29 实测 = `@deepseek-ai/dsh-base` + `@deepseek-ai/dsh-web-app`，**未含**该包。
- **本节第一条（沙箱只读）与长驻服务的完整口径** → 见上文「受限 harness 通用约束」（跨平台权威源）

---

## Hermes / OpenClaw 等

待补充——如有使用经验，欢迎 PR。

---

## 受限 harness 通用约束（沙箱写权限 + 进程存活）

> 适用**所有**默认限制写权限的 agent 平台（DSH `workspace-write`、Codex `-s workspace-write` 等），**不止 DSH**。两条都是**环境事实**，不是可绕过的配置——agent 的产物落点与长驻服务设计必须适配它们。本节是权威源；各平台详情见上文章节。
>
> ⚠️ **适用全部角色，含评审 / 验收角色**（2026-09-29 补，RM-AG0081）：本条初版只写给执行角色，评审角色未继承 ⇒ SELF-GATE 评审踩了同一个坑并造成**数据丢失**。评审角色的**只读纪律**（禁破坏性 git、scratch 正确用法）见 `assets/templates/dispatch-prompt.md` 中给评审/验收角色的那一节（**唯一权威源**，本节只做指针，不复述）。

### 一、临时产物：`<项目根>/.agate-tmp/`（canonical）

**为什么需要约定**：两条环境事实叠加 ⇒ agent 落 scratch 的实际可行位置只有**项目树内**：

1. **工作区外不可写**（沙箱 `workspace-write` 只覆盖会话工作区）；
2. **`/tmp` 是 per-call tmpfs**——**可写，但每次调用都挂一份全新空 tmpfs**，上一个调用写的文件下一个调用读不到。
   - **机制出处（DSH 源码，非推断）**：`sandbox/src/roots.ts::writableRoots()` 在 `workspace-write` 下返回 `[workspaceRoot, '/tmp', tmpdir()]`（**`/tmp` 确在可写白名单内**）；而 `sandbox-local/src/profiles.ts::bwrapProfileArgs()` 为 `workspace-write` 加 `--tmpfs /tmp` ⇒ **每次执行挂一份私有空 tmpfs**。
   - **本机实测**（2026-09-29，workspace-write 会话）：一次 bash 调用写入 `/tmp/_xcall_*` 成功；**下一次调用该文件已不存在，`/tmp` 为空**。
   - **实际代价**：某任务 `make debug-stop` 报「服务已停止」而端口仍监听——因 `/tmp` 里的 pidfile 对当前调用不可见 ⇒ 排查不到真正的持有者。

> ⚠️ **更正**：本仓既有文档（`assets/templates/dsh/SKILL.md` 平台注意第 2 条）与本节初稿都写作「`/tmp` **只读**」——**与事实不符**：`~/.dsh/env.md` 明标 `/tmp` **✅ 可写**（用途「调试数据/日志/PID，如 peekview-debug 全套」），实测 `touch /tmp/...` 亦成功。**结论（用 `.agate-tmp/`）不变**，但正确论据是「**per-call tmpfs / 跨调用不可见**」，而非「只读」。

没有约定时各项目自行发明，并反复踩三个坑（均有实测代价）：

| 踩到的坑 | 实测代价 |
|---|---|
| 目录**未被 VCS 忽略** | 某任务 `.agate-tmp/` 涨到 76 MB、含 **10 个明文 token/cookie**；release 流程的 `git add -A` 会 stage 158 条 → **凭证入 git 历史不可逆** |
| 探针文件名**命中测试收集面** | 并行评审写入的 `.agate-tmp/*.spec.ts` 被 vitest 默认收集 → 基线 **110 → 115** files，且**静默推翻**另一评审刚作出的「不影响基线」结论 |
| 无清理时点 | 临时物随任务结束留在工作区（含旧凭证） |

**约定（四项；②③ 由 `check-gate.py P8` 机械校验，① 是它们共同依据的常量，④ 由 P8 卡收尾检查单承载）**：

1. **名称固定** = `<项目根>/.agate-tmp/`（与 `.agate-version` 同族命名；`AGATE_TMP_DIR` 可覆盖，供既有项目沿用旧名）
2. **强制被 VCS 忽略**：`git check-ignore -q .agate-tmp` 必须为真。片段见 `assets/templates/gitignore-fragment.txt`；`check-gate.py P8` 对「该目录存在却未被忽略」出 **WARNING**（不阻断）。**触发条件是「目录存在」**——即它只在项目采纳本约定后才可能响，不会对未采纳的存量项目产生噪声；而该触发条件**历史上真实发生过**（某任务 `.agate-tmp/` 未被忽略 + 含明文凭证，见上表）
3. **排除出测试收集面**：该目录内**不得**出现匹配常见收集模式的文件名——`*.spec.*` / `*.test.*` / `test_*.py` / `*_test.py` / `*_test.go`（`check-gate.py P8` 同样出 **WARNING**）。**理由**：它在项目树内，会被测试框架的默认 `include` 扫到。**实测实例**：某项目 `vitest.config.ts` 只设了 `exclude: ['e2e/**','node_modules/**']`、**未设 `include`** ⇒ 走 vitest 默认 include （`**/*.{test,spec}.?(c|m)[jt]s?(x)`）⇒ 落在 `.agate-tmp/` 下的 `*.spec.ts` 被收集，基线 `Test Files` 由 110 抬到 115（**5 failed**，因是加载失败而非用例失败）
4. **清理时点** = P8/READY 收尾 —— **复用** P8 卡既有「临时资源清单」机制，不另造（该步由收尾检查单承载，非脚本判据）
5. **跨调用不保留 ⇒ 建 / 用 / 清必须同一次调用**（2026-09-29 补，RM-AG0081）：凡用**工作区外**的临时目录（`/tmp/...`、`$TMPDIR`）做 scratch，**必须把「创建目录 → 操作 → 清理」放在同一次 bash 调用内**。分两次调用时第二次会看到**已消失的目录**。
   - **事故实例（数据丢失，非仅麻烦）**：某次 SELF-GATE 评审在**第一次**调用里 `mkdir /tmp/<dir>` 落空，**第二次**调用发现目录不在，遂在**被评审的仓库内**执行 `git checkout -- .`——**丢弃了尚未提交的改动集**，并产生游离提交；主 Agent 据 `git reflog` 才定位，且恢复不完整（事故后新增的 3 处改动一并丢失）。
   - **正确做法**：① 优先 `<项目根>/.agate-tmp/`（约定 1，在本工作区内，跨调用**保留**）；② 确需工作区外时，单次调用内完成建/用/清；③ 需要跨调用保留的隔离副本用 `git worktree`（落在工作区内）。

> **本仓已自应用**：agateon 自己的 `.gitignore` 已忽略 `.agate-tmp/`（协议定义者先遵守自己的约定）。

**与 P4 卡「基础设施隔离」的关系（不冲突，是两层）**：

| 产物类型 | 落点 | 依据 |
|---|---|---|
| **批内产出 / 证据**（要进 git、要可审计） | `{AGATE_WORKSPACE}/tasks/{Txxx}/P4-implementation/{pkg}/` | P4 卡「临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录」 |
| **探针 / 一次性脚本 / 抓取物**（scratch，不进 git） | `<项目根>/.agate-tmp/` | 本节 |

**并行时 scratch 同样要按批隔离**：`<项目根>/.agate-tmp/<batch-id>/`（`batch-id` 用 P2 `dispatch_plan` 的批 id）。
理由与 P4 卡「各 subagent 写入独立目录」完全相同——**否则两个并行 subagent 会在同一 scratch 目录里互相覆盖**；区别只是根落在 gitignored 的 scratch 下而非任务产出目录。**两条规则不冲突**：P4 管「要入库的批次产出」，本节管「不入库的 scratch」，各自按批隔离。

### 二、长驻服务：存活跟随「发起它的那次调用」

**事实（DSH 实测，权威源 `~/.dsh/env.md`「已知环境限制或坑」）**：DSH 的 bash 调用 / 后台 job 结束时**回收其派生的整个进程树**——`&` / `nohup` / `setsid` detach **均不保活**（与普通 shell 不同）。**其他平台是否有同样回收未经验证，勿假设通用**。

**⚠️ 反模式：靠加长 `sleep` 托底**。某任务为保活 debug 服务，把托底时长逐次加长 **7200 → 14400 → 28800 → 43200 s（12 h）**，仍被跨越 **4 次**——每次都表现为 subagent 拿到 `ConnectTimeout` / `FATAL: 调试服务未运行`，**白跑一整轮**。根因是「**依赖持有者存活**」这个前提本身不可靠；延长只是把失效概率推后。

**可移植做法（四步，不依赖任何平台细节）**：

1. **单一责任方持有**：服务由主 Agent（或 P0-brief `debug_env` 声明的责任方）启动，**subagent 不自行启动**——既有机制见 P5 卡「环境准备职责边界」与 `dispatch-protocol.md`「verification_env 失败处理协议」
2. **每次使用前探活**：判据是**端口 / 健康检查**（`curl -sf <health>` 或 `ss -ltn`），**不是 pidfile 存在**——出处：某项目 `AGENTS.md` 记录的实测「`/tmp/<svc>.pid` 有值但 `ss -ltn` 无监听」；另有任务记录「per-call tmpfs 下 pidfile 根本不可见 ⇒ `debug-stop` 看不到进程」
3. **掉线即重启**：服务可重建，重启成本（秒级）远低于「整轮 subagent 白跑」（分钟级）⇒ **探活失败 → 重启 → 复验**，而不是报错退出
4. **收尾即清理**：DSH 下 **job kill = 进程清理**（确定性），据此写 P8 卡的「临时资源清单」

**DSH 的具体持有方式**：把服务挂在**持续 running 的后台 job** 下（如 `( make debug-start; sleep 3600 )` 提交为后台 job）——job 活多久服务活多久。**但仍须执行上面第 2/3 步**：job 仍可能到期，托底时长不是可靠性保证。

---

## Windows 原生（Git for Windows，不用 WSL）

> agate 的 gate 脚本已全部 Python 化（`.py`），不再依赖 bash + GNU coreutils——TAG0010 起**无 bash 环境（纯 cmd / PowerShell）成为可行选项**：脚本可直接 `python3` 运行。仅 3 个 git hook 入口保留 `.sh` 薄壳（定位 `AGATE_ROOT` + python 探测 + exec 对应 `.py` 主程序），需要 **Git for Windows** 自带的 sh 执行。以下按 Git for Windows 全功能方式说明。

### 前置条件

| 依赖 | 安装方式 | 说明 |
|------|---------|------|
| **Git for Windows** | https://git-scm.com/download/win （独立安装包，不依赖 GitHub 账号） | 提供 git + `sh`（hook 薄壳执行需要）。gate 脚本本体已不依赖其 bash / coreutils |
| **Python 3.8+** | https://www.python.org/downloads/ | 安装时勾选「Add to PATH」。全部 gate 脚本需要，**pyyaml 为强制依赖**（`pip install pyyaml`）|
| **pyyaml** | `pip install pyyaml` | **强制**。所有 py gate 脚本的 YAML 解析依赖（`agate_common.py` / 各状态读取工具），缺失时 fail-closed 阻断 |
| **Pillow（可选）** | `pip install Pillow` | 仅 `check-p6-evidence.py` 的像素方差 / ahash 检测需要。未装时自动跳过（WARNING 不阻断）|
| **ruff（可选）** | `pip install ruff` | 仅开发者跑 `ruff check agate/` 时需要（替代 shellcheck，含 tests）。使用者不需要 |
| **pytest（仅开发者）** | `pip install pytest` | 使用者不需要跑测试；开发者跑 `python3 -m pytest agate/tests/`（Bats 已退役，TAG0011）|

### 前置环境配置（git 用户身份，**新环境必做**）

agate 协议脚本不读 git 用户配置，但 git 本身在 `git commit` 时若未设 `user.email` / `user.name` 会**直接拒绝 commit**（`fatal: unable to auto-detect email address`）——这是 git 自身行为，不是 agate 的问题。新环境**首次使用前**必须配置：

```bash
git config --global user.email "you@example.com"
git config --global user.name  "Your Name"
```

> 项目级 / 用户级 / 环境变量均可（`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL`），global 是最少侵入的入口。若仅个别项目需要不同身份，改用 `git config user.email ...`（项目级，不带 `--global`）即可，不影响其他项目。

### 安装

**装 Git for Windows**：下载安装包，全程默认即可。它会在 `C:\Program Files\Git\` 安装 git + sh。

**验证 sh 可用（hook 薄壳执行需要）**：打开「Git Bash」（开始菜单），运行 `bash --version`，应输出版本号。

**装 Python + pyyaml**：

```bash
python --version    # 应 3.8+
pip install pyyaml
```

**装 agate 本体到版本管理布局**——`~/.agate` 是**版本管理根目录**（实体目录，不是软链），两种方式：

方式 A：**portable（推荐用于 Windows 无 git 场景）**——从 GitHub Release 下载 `agateon-vX.Y.Z.tar.gz` + `SHA256SUMS`，按 `UPGRADING.md`「portable 安装」节解压 + `--adopt`（该节含完整命令与校验步骤）。

方式 B：**有 git 时**在 Git Bash 里跑 `install.sh --versions`（进入版本管理布局并装首个版本），再按需 `python3 ~/.agate/scripts/agate-install.py latest` 更新。

> 无符号链接权限时，`latest` / `current` 指针会**退化为文本指针文件**（见下「指针形态」小节），不影响使用。

**在项目仓库里装接入 + hook**：

```bash
cd /path/to/your/project
python3 ~/.agate/scripts/agate-setup.py
```

> 该命令一条完成「平台身份注册 + 装 hook」。Windows 无符号链接权限时，配置物以**复制模式**安装（输出含「复制模式」提示）。**升级 agate 后需重跑此命令**刷新（复制不自动跟随源文件）。

**验证**：

```bash
python3 ~/.agate/scripts/agate-summary.py
```

应输出版本号 + 防护状态。

### 已知限制（Windows 原生）

| 限制 | 影响 | 规避 |
|------|------|------|
| 符号链接退化为复制 | 身份配置物与 hook 不随 agate 升级自动更新 | 升级 agate 后重跑 `python3 ~/.agate/scripts/agate-setup.py`（该命令内含 hook 安装）；或开 Windows「开发者模式」启用真符号链接。**身份配置物会被检测**：`agate-summary.py` 对四平台接入产物给两级信号——指向不在任何已装版本树内 → 警告「漂移」；指向已装但非 current 的版本 → 信息级「版本落后」（复制形态则比对内容，与任何已装版本都不一致时提示「已过期」）；均附修复命令（hook 走另一路 `.agate-root` / resolve-entry，不在该检测内）|
| `core.autocrlf` CRLF 污染 | 3 个 hook 薄壳 `.sh` 报 `\r` 语法错；py 文件已显式 `encoding="utf-8"` 读写（免疫），仅卡片 sha256 校验受 hash 影响 | 仓库已含 `.gitattributes` 强制 LF；若 clone 旧版本无此文件，手动 `git config core.autocrlf false`。已 clone 且已物化 CRLF 的工作区需 `git add --renormalize .` 重规范化 |
| pytest 需安装 | 开发者无法跑 `python3 -m pytest` 测试 | `pip install pytest`（Windows 原生 python 直接可用）；或用 WSL 跑测试（使用不受影响） |
| CI 仅 ubuntu | Windows 本地行为无 CI 兜底 | 靠本地验证；protocol-tests.yml 的 pytest job 已加 `windows-latest` matrix（`-m windows_smoke` 冒烟，见 `AGENTS.md` 测试约定） |
| 路径分隔符 | MSYS2 自动转换 `/c/Users/` ↔ `C:\Users\`，但极少数硬编码路径可能出问题 | 遇到时用 `cygpath -w` 转换 |
| Windows Store `python3.exe` 占位符 | 部分 Windows 安装（未关闭「应用执行别名」）下，PATH 上的 `python3`（有时 `python`）解析到 Microsoft Store 的占位符可执行文件——`command -v` / `where` 能找到它、有执行位，但实际执行任意命令一律非零退出，不解释传入的脚本 | 3 个 hook 薄壳（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh`）的探测循环已改为逐候选先做一次可执行性小测试（通用 exit code 判据），命中占位符会跳过并继续尝试下一候选；也可设置 `AGATE_PYTHON` 环境变量显式指定真实 Python 解释器的完整路径，直接跳过整个探测循环 |

> **DEBT0014 验证边界说明**：以上 Store 占位符现象与 `AGATE_PYTHON` 机制的修复，验证方式是静态代码修复 + Linux 环境下用模拟 stub 复现「`command -v` 命中但执行非零退出」症状特征做的回归测试 + CI protocol-tests.yml 的 `windows-latest` matrix 冒烟——本仓库开发环境是 Linux，未在真实 Windows 环境下触发过 Store 占位符场景本身，上述描述是已知机制的静态修复说明，不代表已在 Windows 环境中复现并验证通过。

### 指针形态（无符号链接权限时，TAG0008 版本管理）

`~/.agate` 版本管理根目录里的 `latest` / `current` 是**纯指针**：Linux / macOS 用 POSIX 符号链接（`latest → v0.48.0`），Windows 无符号链接权限（或 `AGATE_HOOK_COPY_MODE=1`）时**退化为文本指针文件**——文件内容为指向的版本目录名（如 `v0.48.0`），解析时按内容恢复目标路径（`agate_common.py` 的指针链解析兼容两形）。`.agate-root` 标记先例沿用：复制模式下安装的 hook / orchestrator 副本写 `.agate-root` 记录安装根，解析入口（`resolve-entry.py`）据此恢复 `AGATE_ROOT`。行为不变：解析失败回退 `current`，绝不静默禁用 gate。

`install.sh --versions`（新机一键进入版本管理布局）保持 POSIX shell（无 bash 扩展）。决策 B1 下根 `~/.agate/scripts/` 用**拷贝**（`shutil.copytree`）建立，恰好规避 Windows 符号链接权限问题——比符号链接更平台无关，也没有 `latest` / `current` 指针那样的文本退化形态。

### 无 bash 环境（纯 cmd / PowerShell）

- **TAG0010 起可行**——gate 脚本已全部 Python 化，`python3 ~/.agate/scripts/xxx.py` 可直接运行（P0-P8 全程可执行）。
- **唯一受限**：git hook 入口薄壳仍需 sh 执行，无 bash 时 hook 不触发——可用 CI backstop 兜底 `--no-verify` 场景（见「Hardening-roadmap 跨平台适配」节）。
- **Cygwin（非 MSYS2）**：理论上可行但未测，不保证。推荐 Git for Windows。

---

## Hardening-roadmap 跨平台适配（自 v0.4 引入，持续生效）

核心 gate 机制（pre-commit hook + CI backstop）是 **git 协议级**的，自 v0.4 起所有平台统一可用。但配套能力有平台差异：

| 机制 | OpenCode | Claude Code | Codex | 说明 |
|------|---------|-------------|-------|------|
| pre-commit hook | ✅ 全功能 | ✅ 全功能 | ✅ 全功能 | git 机制本身，与平台无关 |
| `check-p6-provenance.py` 审计 | ✅ | ✅ | ✅ | 纯 Python + 文件系统 |
| `agent:` 字段协作规范 | ✅ | ✅ | ✅ | 文件级 metadata |
| `risk=high` 自审 WARNING | ✅ | ✅ | ✅ | hook 输出 exit 2 |
| CI backstop（gate 重跑 + provenance 重跑 + git blame WARNING）| ⚠️ 自实现 | ⚠️ 自实现 | ⚠️ 自实现 | GitHub Actions / GitLab CI / Gitea Actions 提供开箱实现（⚠️ Gitea 未实测） |
| 独立 git author 追踪（P2.10 根治）| ❌ | ❌ | ❌ | Phase 3 平台功能未实现 |
| `~/.agate` 版本管理根 / 版本目录 | ✅ | ✅ | ✅ | 文件系统级，无平台差异；TAG0008 起为版本管理根（实体目录 + 指针），无符号链接权限时指针退化为文本文件 |

**CI 兜底说明**：`.github/workflows/protocol-tests.yml` 的 `gate-backstop` job 用 GitHub Actions 实现。`agate-ci-verify.py` **平台无关**（不探测任何 CI 平台环境变量），在任何环境直接调用都会**实际重跑** `check-gate.py` 判定。在自建 CI（Jenkins / 本地）跑 agate 时：

- 需要等价实现：`git push` 后调用 `agate-ci-verify.py`（无参数，cwd = 项目根；它实际重跑 `scripts/check-gate.py` 判定）
- 不实现 CI 兜底也能用——只是失去 `--no-verify` 绕过 hook 的兜底审计

**Codex 兼容性**（历史注记，时效见 §2 Codex「子代理派发」小节）：Codex subagent `max_depth=1` 与 P2.1 强制派发独立 subagent（`risk=high`）的兼容性：

- Codex 单层任务工具无法"再派发"——这种情况下 P2 review 必须由主 Agent 自己跑（`agent=main`）
- `check-gate.py` P2 对 `agent=main` 硬拦截（exit 1，不可自行批准评审）
- 升级到 Codex 多层派发（待官方发布）后兼容自动生效

> ↑ 上述 `max_depth=1` /「无法再派发」记于 subagent workflows 默认启用之前；时效更新见 §2 Codex 章「子代理派发（`spawn_agent`）」小节（`multi_agent` flag 实测 stable/true、`spawn_agent` 单层已实测可用、嵌套深度经 P6 V7 复核实测 `depth=2` 可用——`max_depth=1` 结论已推翻）。

## 跨 CLI 子进程结构化输出判成败字段（派发路由 / TAG0034）

> 派发路由（`agate dispatch route`）以子进程形式派 `claude-code` / `codex` / `opencode` 时，用各平台结构化输出流判「这次派发成功 / 基础设施失败 / 无可解析产出」三态（`agate_dispatch_route.classify_outcome`）。素材 = 本机真机样本（2026-09-09，Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11），夹具在 `agate/tests/fixtures/tag0034_{claude_code,codex,opencode}/`。**判据只到 presence 级**——产出文件非空 + frontmatter 可解析 + 必需锚点在即算「有产出」，内容完整度 / 质量一律交 gate（走同候选 retry，不换候选）。

| 平台 | 命令 | HAS_OUTPUT（成功 → 停回落、交 gate） | INFRA_ERROR（→ 回落 `infra_error`） | NO_PARSEABLE_OUTPUT（→ 回落 `no_parseable_output`） |
|---|---|---|---|---|
| Claude Code | `claude -p --output-format json` | `stop_reason == "end_turn"` + `result` 非空 + 约定产出文件非空且骨架可解析。`modelUsage` 的 key 可核实实际 model（如 `claude-haiku-4-5-20251001`，非父继承） | 启动即报未登录 / `api_error_status` 非 null（如 `401`）/ `stop_reason == "error"` / 挂死被杀（`wait(pid)` 超时 / `kill -0` 探测失活） | `stop_reason == "end_turn"` 但 `result` 空 **且** 约定产出文件缺失或空 |
| Codex | `codex exec --json` | 事件流含 `{"type":"turn.completed"}` 且**无** `{"type":"turn.failed"}`、**无**顶层 `{"type":"error"}` + 约定产出文件非空且骨架可解析。**退出码不可靠**——以 turn 层事件为准（本版 `turn.failed` → exit 1，研究记 auth 循环 → exit 0，两向都不稳） | `{"type":"turn.failed"}` 或顶层 `{"type":"error","status":...}`（如 model 不被账号支持 → `status:400`）/ 挂死被杀 | 有 `turn.completed` 但无任何 `agent_message` text **且** 约定产出文件缺失或空 |
| OpenCode | `opencode run --format json` | `step_finish` 且 `part.reason == "stop"` + 有 `text` part + 约定产出文件非空且骨架可解析 | 顶层 `{"type":"error","error":{"name":"ProviderAuthError",...}}`（→ `infra_error`）/ 挂死被杀 | 纯空返回（无 `step_finish`、无 `text` part、无 `error` 事件）/ `{"type":"error","error":{"name":"UnknownError",...}}` / 约定产出文件缺失或空 |

**Codex 两层 `status`（turn 层为准）**：item 级 `payload.item.status == "failed"`（携 `exit_code`，= agent 内部某条 shell 命令非 0 退出）**永不触发换候选**——只要整轮 `turn.completed` 即 `HAS_OUTPUT`。这与「产出质量不是回落信号」（R1）一致。per-command 退出码的可靠性见 §2 Codex「命令流适配」小节（rollout item 带干净数字 `exit_code`），与 turn 级退出码不可靠是两回事。

**routed-away judge 的 verdict 落点**：P6.5 judge 被路由到 codex / opencode 子进程时，其 transcript 落 `~/.codex/sessions/` 等非 `~/.claude/` 位置，但 **verdict + 证据仍写 `TASK_DIR`**（铁律 2/3 不变）。`check-judge-verdict.py` / `check-p6-provenance.py` 纯 `TASK_DIR` 文件解析、不读平台 transcript 路径——本任务**零改动**这两个脚本，跨平台产出照常平台无关通过（`agate_dispatch_route.routed_away_verdict_location(cli)` 恒 `"TASK_DIR"`）。
