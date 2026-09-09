---
phase: P1
task_id: TAG0033
type: problems
parent: P0-brief.md
trace_id: TAG0033-P1-20260909
status: draft
created: 2026-09-09
agent: analyst
risk_level: medium
ceremony: standard
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-scripts, agate-docs, agate-tests]
domains: [backend]
capability_requirements:
  - need: codex-cli-installed-authenticated
    why: read_commands 的 fixture 取真实 rollout 片段；真机验证清单 P5/P6 需真派 Codex 子代理 + 观察会话文件
    available:
      - "本机 codex-cli 0.153.4 + ChatGPT 登录已具备（P0-brief env_constraints / 客观查证 A）"
    status: available
verification_env: "codex-cli 0.153.4 + ChatGPT 登录（本机已就绪）；API-key 账号环境本机不可得"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；仅适用于 API-key 账号 model 阵容项，其余真机项本机可做"
---

# P1 需求基线 — TAG0033 Codex 命令流适配器 + 平台接入（RM-AG0061）

> parent：`P0-brief.md`（四交付面 / out-of-scope / known_risks 六条 / env_constraints）
> 设计依据：`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/` §3.4.2/§3.4.3/§3.4.4
> 机制事实：`docs/research/cross-platform-dispatch-mechanics.md`（Codex：§1.2/§2/§3/§4.2/§5/§6/§7/§8/§11 + 附录 A4-A8/A12/A17-A19）
> spike 现场勘查结论见 §4（本会话真机实测，codex-cli 0.153.4 + ChatGPT 登录，2026-09-09）

`[NO_NEED_CONFIRM]`
`[PROD_NOT_TOUCHED]`

---

## 1. 需求复述

给 RM-AG0055 命令流日志机制（`agate/scripts/agate-cmdstream-{adapters,detect,ir}.py`，TAG0028 已落地）
新增 **CodexAdapter**，使 subagent 存活/卡死检测覆盖 Codex 平台。范围严格锁定 P0-brief 四交付面：

1. **CodexAdapter**：`agate/scripts/agate-cmdstream-adapters.py` 新增 1 个 class + `ADAPTERS` 注册表加 1 行
   （键名建议 `"codex"`，`[SUGGEST: 注册表键名用 "codex"，与 CommandRecord.platform 标识、research 文档、CLI 名一致]`）。
   实现 `CommandStreamAdapter` 契约三方法 `probe(path)` / `list_sessions(cwd)` / `read_commands(session_path)`。
   数据源 = `~/.codex/sessions/**/*.jsonl`（rollout JSONL）。
2. **`agate/platform-notes.md` Codex 章**：`## Codex / Hermes / OpenClaw 等`（现 line 43-45「待补充」）补为
   完整能力矩阵 + 实机验证记录，注明验证 CLI 版本号（0.153.4）+ 账号类型（ChatGPT）。
3. **`agate/SETUP.md` Codex 小节**：安装 + `codex login`（ChatGPT vs API key 影响 model 访问）+ 自动化环境绕过 flag。
4. **测试 + 真机验证清单**：`agate/tests/unit/test_agate_cmdstream_adapters.py` 新增 CodexAdapter 解析单测
   （真实 Codex session 片段作 fixture）+ 检测引擎对 Codex 会话三态确定性试验；真机验证清单（P1 定 / P5-P6 执行）。

**零改动硬约束**：检测引擎（`agate-cmdstream-detect.py`）、阈值（RM-AG0055 §3.4.3）、`CommandRecord` IR
（`agate-cmdstream-ir.py` 十字段 dataclass）、既有三平台适配器（`ClaudeCodeAdapter` / `OpenCodeAdapter` /
`DSHAdapter`）——全部零功能改动。

## 2. 隐含需求识别（逐维度）

| 维度 | 识别结果 | 为什么必须 |
|---|---|---|
| 同类/影响面 | `ADAPTERS` 注册表被 `agate-cmdstream-detect.py` 消费（`_load_adapters` → CLI `choices=sorted(ADAPTERS.keys())`）；`test_agate_cmdstream_adapters.py::test_bdd_6_detect_consumes_registry_zero_change` 有**精确等值断言** `registered == {"claude-code","opencode","dsh"}`——加第四键会打破该断言 | 见 §3 同类扫描——不处理该断言会让"新增平台"直接红全片单测 |
| 数据（存量） | Codex rollout JSONL 是**外部只读**用户目录文件，无迁移问题；无既有 Codex fixture（`agate/tests/fixtures/cmdstream/` 现 3 个）需新增 | fixture 缺失则 CodexAdapter 单测无法写 |
| 前端 | 无用户可见页面产线（协议/工具链改造）——`domains: [backend]` | 无 UX BDD 需求 |
| 多端（MCP/CLI/API） | 检测引擎 CLI（`list-sessions` / `read-commands` / `detect` 子命令）通过 `sorted(ADAPTERS.keys())` 自动纳入新键，无需另改 CLI 代码 | 确认 CLI `choices` 不硬编码三键（已核实：动态取自注册表） |
| 边界 | ① 未结束命令（会话被杀在命令执行中）→ exit=None/ts_end=None/"pending"（IR 契约允许，比照既有适配器 CRITICAL-3）；② 畸形/非 JSON 行不崩溃（CRITICAL-4）；③ 截断输出 → truncated=True + output_hash=None（§3.4.3 截断排除）；④ 非 shell 工具事件（`apply_patch` / `web__run`）不产出 CommandRecord | 检测引擎消费坏数据会误判；截断误入哈希会误判 SPIN |
| 兼容 | Codex 无宿主平台 onboarding（out-of-scope）；`spawn_agent` 嵌套深度未测（登记不新造）；Codex 失败输出文本格式若变则解析规则需更新（同 Claude Code/DSH 既有已知局限，登记进 known-limitations，不新增机制） | 避免把已知局限当新缺陷造机制 |
| 证据强度 | `spawn_agent` 完整参数 schema 是 `[自述]`——「未见 `background`/`timeout`/`permission` 字段」≠「确认无」；P1 spike 已确认穷尽 schema 需换法（模型受训拒绝逐字输出内部 tool schema） | 外部评审 B1 教训——产出表述不得混同 `[自述]`/`[推断]`/`[已实测]` |

## 3. 同类扫描结论（强制节）

**扫描动作**：对关键符号 `ADAPTERS` / `CommandStreamAdapter` / 平台键三连 `claude-code`+`opencode`+`dsh` /
`platform-notes.md` 的 Codex 提及 / CHECK 12 跨文件一致性锚点 / `agate/tests/fixtures/cmdstream/`，
在 worktree 全仓 grep。命中清单 + 逐条处理判定：

| # | 命中位置 | 内容 | 判定 |
|---|---|---|---|
| S1 | `agate/scripts/agate-cmdstream-detect.py:96,308,312,317,328` | `ADAPTERS = _load_adapters().ADAPTERS`；CLI `choices=sorted(ADAPTERS.keys())` × 3；`adapter = ADAPTERS[args.platform]` | **本次不处理**（零改动）——CLI choices 动态取自注册表，加键自动生效，无硬编码三键。BDD-21 锁定 detect.py 无功能 diff |
| S2 | `agate/scripts/agate-cmdstream-adapters.py:623-627` | `ADAPTERS = {"claude-code":…, "opencode":…, "dsh":…}` | **本次处理**——加 `"codex": CodexAdapter()` 一行（P0-brief scope ①） |
| S3 | `agate/tests/unit/test_agate_cmdstream_adapters.py:298` | `assert set(adapters.ADAPTERS.keys()) >= {"claude-code","opencode","dsh"}` | **本次不处理**——`>=` 包含式，加第四键不破 |
| S4 | `agate/tests/unit/test_agate_cmdstream_adapters.py:317` | `assert registered == {"claude-code","opencode","dsh"}`（`test_bdd_6_detect_consumes_registry_zero_change`）**精确等值** | **本次处理**（BDD-19）——加 `"codex"` 键会让该断言失败。P4 改为含 `"codex"` 的集合或 `>=` 包含式；语义（检测引擎零改动消费注册表）不变 |
| S5 | `agate/tests/unit/test_agate_cmdstream_adapters.py:320` | `assert "ADAPTERS" in detect_src` | **本次不处理**——只断言引用存在，不受影响 |
| S6 | `agate/scripts/check-protocol-consistency.py:989-1123` CHECK 12 | 权威值锚点 `AUTHORITATIVE_VALUE_ANCHORS` 只含 `retry-max`（`state-machine.md` MAX_RETRY 表） | **本次不处理**——CHECK 12 锚点与 `platform-notes.md` 能力矩阵**无关**；新增 Codex 矩阵行不触发 CHECK12-authval。本任务不新增 CHECK/锚点（DEBT0025 只需扫描确认，已确认） |
| S7 | `agate/scripts/check-protocol-consistency.py:1184` CHECK 14/15 `_MD14_WHOLE_FILE_EXEMPT` | `agate/platform-notes.md` / `agate/SETUP.md` 是**整文件豁免**（平台适配权威源） | **本次不处理**——补 Codex 散文/能力矩阵不触发平台名污染 ERROR。确认新章仍需过 `check-protocol-consistency.py --strict-errors-only` 0 ERROR（BDD-20） |
| S8 | `agate/platform-notes.md:53-70` | Hardening-roadmap 跨平台适配表**已有 Codex 列**（机制维度：pre-commit hook / provenance / CI backstop 等）+ line 67-70「Codex 兼容性」注记（`Codex subagent max_depth=1`，写于 subagent workflows 默认启用之前） | **本次处理**（BDD-25）——新增 `## Codex` 章须与既有注记**交叉引用 + 更新时效状态**（spike 实测 `multi_agent` = stable/true、`spawn_agent` 单层已用、嵌套深度未测），不删除既有行，不产生自相矛盾陈述 |
| S9 | `agate/WORKFLOW.md:6,8,156` | `\| Codex \| ✅ \| ✅ \| 完整 P0-P8 \|`（「已知适用环境」表行，CHECK 14 表行豁免） | **本次不处理**——`WORKFLOW.md` 非本任务交付面；该行是环境适用性声明、与命令流适配器无关，已一致 |
| S10 | `agate/tests/fixtures/cmdstream/` | 现 `claude-code-session.jsonl` / `dsh-session.jsonl` / `opencode-part-state.json` | **本次处理**——新增 `codex-session.jsonl`（+ spawn_agent 子会话片段），字段结构取自真实 rollout、内容脱敏（demo 前缀、无 `/home/kity` 真实路径、无密钥、无真实 26 位 hex 会话标识——比照 BDD-7 既有脱敏约定）。P4 同步把 `agate/tests/fixtures/cmdstream/codex-session.jsonl` 加入 `test_agate_cmdstream_adapters.py::test_bdd_7_fixture_sanitized` 的脱敏校验清单（否则新 fixture 无自动脱敏校验） |
| S11 | `docs/research/cross-platform-dispatch-mechanics.md` / design-note v5 | `CommandStreamAdapter` 契约、CommandRecord IR 引用（文档） | **本次不处理**——只读参照，非改动面 |
| S12 | `agate/tests/unit/test_agate_cmdstream_detect.py:371` | `for platform_word in ("claude", "opencode", "dsh"):`（`test_bdd_24_output_platform_agnostic`）| **本次不处理**——负向断言（断言检测输出**不含**这些平台词），加第四键不打破；可选强化：元组加 `"codex"` 以断言 Codex 也不泄漏 |

**回归拦截**：新增平台适配器不是一次性存量——未来 Cursor 等平台同样按 §3.4.4 扩展。拦截手段 = 本任务
新增的 CodexAdapter 解析单测 + 三态确定性试验作为"新增平台必须配套的验证范式"沉淀（fixture 目录 +
测试文件已是模式）；`ADAPTERS` 注册表精确断言改为包含式后，第五个平台加入不再误红（BDD-19 顺带修的回归面）。
本任务**不新增 gate 脚本 / CHECK**（P0-brief 核心约束、DEBT0025）。

## 4. P1 必做 spike 现场勘查结论（真机实测，codex-cli 0.153.4 + ChatGPT 登录，2026-09-09）

> 证据强度标注：`[已实测]` = 本会话端到端跑过并观察；`[自述]` = 运行中模型报告自己的工具/参数；`[推断]` = 由观察综合推出。

### 4.1 `~/.codex/sessions/` 目录结构与 rollout JSONL 格式 `[已实测]`

- 目录布局：`~/.codex/sessions/YYYY/MM/DD/`（**按 UTC 年/月/日分层**，非 cwd 分层——与 Claude Code 的
  sanitized-cwd 目录、DSH 的 sanitized-cwd 目录**不同**）。本会话新派任务时自动创建 `2026/09/09/` 目录。
- 文件名：`rollout-<ISO8601 秒精度带 - 分隔>-<uuid>.jsonl`（如 `rollout-2026-09-08T21-01-55-01a0811c-6076-7a00-a369-9fcfae1c52fb.jsonl`）。
- 每行信封：`{"timestamp": "<ISO-8601 UTC ms>", "ordinal": int, "type": str, "payload": {...}}`。
  `type` ∈ `session_meta`(首行) / `event_msg` / `response_item` / `world_state` / `turn_context` /
  `token_usage_record` / `compacted` / `inter_agent_communication_metadata`。
- **shell 命令的最佳映射源** = `type=="event_msg"` 且 `payload.type=="item_completed"` 且
  `payload.item.type=="CommandExecution"`。该 item 含：
  - `item.command`：数组，形如 `["/bin/bash", "-lc", "<命令文本>"]`
  - `item.exit_code`：**数字**（`[已实测]` 观察到 `0`；失败时为对应非 0）——见 §4.1.1
  - `item.status`：`"completed"`（未结束时预期为 `"in_progress"` 或缺 completed 事件）
    - `[BASELINE_CHANGE: spike 取样未覆盖 "failed" 终态]` P6 V6 实测：真机 Codex 把已结束但非 0 退出的
      命令记为 `item.status == "failed"`，仍携带完整 `exit_code` + `payload.completed_at_ms`。真机
      `item.status` 取值集 = `completed`（成功终态）/ `failed`（已结束非 0 退出）/ `in_progress`（未结束）。
      `read_commands` 的「已结束」判据据此改口径（见 P2 §5 设计点 2 的 BASELINE_CHANGE / DEBT0035）。
      Given/When/Then 语义不变，仅补充真机事实。
  - `item.stdout` / `item.stderr` / `item.aggregated_output` / `item.formatted_output`
  - `item.parsed_cmd`：`[{type, cmd, name, path}]`（Codex 对命令的结构化解析）
  - `item.duration`：`{secs, nanos}`
  - `payload.started_at_ms` / `payload.completed_at_ms`：**epoch 毫秒 int**（时间戳来源）
- 另有一层 `type=="response_item"` 且 `payload.type=="custom_tool_call"` name=`"exec"`——是 JS 沙箱
  harness 调用（`input` 是 JS 源码：`tools.exec_command({cmd,workdir,yield_time_ms,max_output_tokens})` /
  `tools.apply_patch(...)` / `tools.web__run(...)`），配对 `custom_tool_call_output`（`output[].text` 以
  `"Script completed"` / `"Script failed"` + `"Wall time Xs"` + `"Output:\n"` 开头）。
  **只有 `tools.exec_command` 会派生 `CommandExecution` 子事件**；`apply_patch` / `web__run` 不派生。
- `event_msg` 的其它 `payload.type`：`task_started` / `task_complete`（含 `duration_ms` / `started_at` /
  `completed_at`）/ `token_count` / `thread_settings_applied` / `turn_aborted`。
- `response_item` 的其它 `payload.type`：`message`(role developer/user/assistant) / `reasoning`(encrypted) /
  `function_call` / `function_call_output` / `agent_message`。

**`read_commands` 映射判断**：从 `CommandExecution` item 映射 `CommandRecord`——
`platform="codex"`、`session_id`=会话标识（basename 或 `session_meta.id`，P2 定）、`tool`="exec"/"bash"、
`command`=`item.command` 拼接或末元素、`ts_start`=`started_at_ms`、`ts_end`=`completed_at_ms`、
`exit`=`item.exit_code`、`exit_signal`=原始形态留档（如 `"exit_code=0"` / `item.status`）、
`output_hash`=`_sha1_hex(aggregated_output)`（`truncated` 时 None）、`truncated`=截断信号（见 §4.1.2）。

### 4.1.1 Codex 有无数字 exit code `[已实测]` —— P0-brief 陈述需修正（轻微漂移）

P0-brief / 交接单称「Codex **无数字 exit code**——同 Claude Code/DSH，靠 `is_error` 布尔 + 失败输出文本前缀解析」。
**本会话实测：Codex rollout 的 `CommandExecution` item 携带 `exit_code` 数字字段**（观察到 `"exit_code": 0`），
比 Claude Code / DSH 干净。P0-brief 的「无数字 exit code」结论只对 **turn 级失败**（`turn.failed{status:400}`、
`item.type:error`——research §2.4/§6.2）成立，对 **per-command shell 执行**不成立。

**处理（轻微漂移，不阻塞）**：`[P0_STALE: P0-brief/交接单称 Codex 无数字 exit code，实测 rollout CommandExecution item 有 exit_code 数字字段；仅 turn 级失败无数字 exit]`——
已在本节记录并更新理解：`CommandRecord.exit` 对 Codex 直接取 `item.exit_code`（无需文本前缀解析），
`exit_signal` 仍留档原始形态。`read_commands` 无法拿到 exit（未结束 call / item 无 exit_code）时才回落 None。
P0-brief 其它前提（技术路线、env、known_risks）全部成立，判定为**轻微漂移**：目标方案本身（加一个适配器、
检测引擎零改动）不变，反而更简单（exit 映射更干净）。P2 设计据此写解析规则，platform-notes.md 如实记录。

### 4.1.2 截断标记形态 `[未实测 / 待定]`

本会话观察的 rollout 样本无超长输出，未捕获 Codex 的输出截断标记确切形态（`exec_command` 有
`max_output_tokens` 参数，截断可发生）。research §3.4.2 差异点 4 的「DSH 截断标记（实测最大 69KB）」是 DSH 结论、
不能直接套用。**处理**：截断标记形态列入真机验证清单（§7 项 V4）；P2 设计在拿到实测形态前，采用比照
`DSHAdapter._detect_truncated` 的**保守双信号**（item 上显式布尔字段 ∪ 输出文本字面量标记），实测后收敛。
`truncated=True` 时 `output_hash=None`（IR 契约）——不因形态未定而放宽此规则。

### 4.2 `spawn_agent` 子会话文件的层级标识与定位 `[已实测]`

**结论：`spawn_agent` 子会话是独立的 `rollout-*.jsonl` 文件，不是父文件内嵌事件。**（本会话现场派
`spawn_agent(task_name=probe_child)` 实测：`~/.codex/sessions/` 文件数 21→23，父会话 rollout +
子会话 rollout 各一个新文件。）

- 子会话文件 `session_meta`（首行 payload）含**明确父子关联字段**：
  - `parent_thread_id`：父会话 thread id
  - `forked_from_id`：父会话 id（观察到与 `parent_thread_id` 同值）
  - `session_id`：= 父会话 id；`id`：= 子会话自身 id（**注意：`session_id` 字段是父的，`id` 字段才是本文件的**）
  - `thread_source`：`"subagent"`（主会话为 `"user"` 或缺省）
  - `source.subagent.thread_spawn`：`{parent_thread_id, depth: 1, agent_path: "/root/<task_name>", agent_nickname, agent_role}`
  - 顶层另有 `agent_path` / `agent_nickname`；较新捕获还含 `multi_agent_version: "v2"` / `history_mode` / `git` 块
- 父会话文件里子代理的痕迹：
  - `response_item` / `function_call` name=`"spawn_agent"` namespace=`"collaboration"`（含 `call_id`、`arguments`——`message` 字段加密）
  - `event_msg` / `item_completed` `item.type=="SubAgentActivity"`（`kind`: `"started"` / `"completed"`，
    `agent_thread_id`=子会话 id，`agent_path`）
  - `response_item` / `agent_message`（`author` / `recipient` = `/root` ↔ `/root/<task_name>`）+ `inter_agent_communication_metadata`

**`list_sessions` 实现判断**：父子会话在**同一** `YYYY/MM/DD/` 扁平目录，`os.walk` 遍历 `rollout-*.jsonl`
**天然同时枚举父与子文件**——不存在 DSH/Claude Code 那种「读主文件会漏子代理记录」的问题（Codex 子代理本就是
独立文件）。子会话的**判定依据** = `session_meta.thread_source == "subagent"`（或 `parent_thread_id` 存在），
比照 DSH 的 `delegationDepth>0`。`read_commands(子文件)` 产出记录的 `session_id` 应指向**子会话自身**。

### 4.3 `spawn_agent` 完整参数 schema 直接实测 `[自述]`（穷尽实测：P1 确认路径不可用，转 P5-P6）

- 观察到的真实 `function_call.arguments` 键（多次 spawn 一致）：`task_name` / `model` / `fork_turns` /
  `message`（加密）/ `reasoning_effort`（部分调用）。**未见** `background` / `timeout` / `permission` 键——
  但**未证实不存在**。
- P1 直接实测尝试：派 `spawn_agent` 子代理令其逐字输出自己的 `spawn_agent` tool JSON schema——**模型受训
  拒绝**（两次尝试均拒："I can't provide verbatim internal tool schemas"）。→ **穷尽 schema 拿不到的方法边界
  已确认**：`[自述]`（research A12：`task_name`(必)/`message`(必)/`fork_turns`(`"none"|"all"|N`，默认`"all"`)/
  `model`(枚举 4)/`reasoning_effort`(6 档)）是当前证据上限。
- 穷尽 schema 登记为真机验证清单 §7 项 V2，P5-P6 执行，换法（读 codex 二进制/内省、或 API-key 账号跑
  `--json` 观察、或跨大量真实调用归纳字段全集）。落地代码按「schema 可能不全」处理（不假设已穷尽）。

### 4.4 `codex features list` 复核 `multi_agent` feature flag `[已实测]`

`codex features list`（exit 0）实测 0.153.4：
- `multi_agent` = `stable` / effective **`true`** —— 撑 `spawn_agent`，无需 `--enable`
- `collaboration_modes` = `removed` / `true`（历史名）
- `multi_agent_mode` = `removed` / `false`（历史名）
- `multi_agent_v2` = `stable` / `false`（子会话 `session_meta` 里却见 `multi_agent_version: "v2"` 字样——
  命名/内部版本仍在演进，**强化 platform-notes.md 版本注记纪律**）

与 research 附录 A17 一致。命名有变更史（`collaboration_modes` / `multi_agent_mode` 已 removed）——
platform-notes.md Codex 章须注明"目标版本上 `codex features list` 复核一次"。

### 4.5 实时事件流形态 `[已实测]`

`codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "..."`（exit 0）实测事件流：

```
{"type":"thread.started","thread_id":"..."}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"..."}}
{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"/bin/bash -lc 'echo hi'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"/bin/bash -lc 'echo hi'","aggregated_output":"hi\n","exit_code":0,"status":"completed"}}
{"type":"turn.completed","usage":{...}}
```

**`--json` 实时流 vs rollout JSONL 差异**（判断 `read_commands` 用哪个源）：

| 维度 | rollout JSONL（落盘，`~/.codex/sessions/`）| `--json` 实时流（stdout）|
|---|---|---|
| 行信封 | `{timestamp, ordinal, type, payload}` | 扁平 `{type, ...}` |
| 命令执行事件 | `event_msg`/`item_completed`，`item.type=="CommandExecution"`（**PascalCase**）| `item.started` / `item.completed`，`item.type=="command_execution"`（**snake_case**）|
| `command` 形态 | 数组 `["/bin/bash","-lc","..."]` | 字符串 `"/bin/bash -lc '...'"` |
| exit code | `item.exit_code`（数字）| `item.exit_code`（`in_progress` 时 `null`，`completed` 时数字）|
| **时间戳** | 行 `timestamp` + `payload.started_at_ms` / `completed_at_ms` | **✗ 事件本身不带 per-item 时间戳** |
| turn 失败 | `event_msg`/`turn_aborted` 等 | `turn.failed{error.message}` |

**判断**：`read_commands(session_path)` 以 **rollout JSONL 为源**（detect() 需要 `ts_start`/`ts_end`，
`--json` 流不带）。`--json` 实时流是"实时源可用"（P0-brief scope ①），本任务**不强制**实现，
若 P2 决定支持，需自造时间戳（如以行接收时刻）——建议列为 out-of-scope 或后置。

### 4.6 P0-brief 时效性质疑（强制节）

**已核对 P0-brief 时效性。判定：基本无漂移 + 1 处轻微漂移已记录。**

| 前提 | 核对结果 |
|---|---|
| worktree 存在、分支正确、`git status` clean | 成立（客观查证 A） |
| codex-cli **0.153.4** + ChatGPT 登录 | 成立（`~/.codex/version.json` latest_version=0.153.4；`auth.json` 存在；`codex features list` / `codex exec` 实测 exit 0） |
| cmdstream 三脚本齐全（adapters/detect/ir） | 成立（本会话逐个读过，契约与 P0-brief 客观查证 B/C 一致） |
| pytest 9.0.3 | 成立（交接单第 9 节） |
| known_risks 六条无一被他任务解决 | 成立——六条均为 Codex 机制自身特征 / 本任务内处理项 |
| 技术路线（RM-AG0055 §3.4.4「约一个文件、检测引擎零改动」）不变 | 成立——spike 证实 CommandRecord 十字段可干净映射，无需扩 IR/引擎/阈值 |
| **轻微漂移** | `[P0_STALE: P0-brief/交接单称「Codex 无数字 exit code」，实测 rollout CommandExecution item 有 exit_code 数字字段——仅 turn 级失败无数字 exit]`——见 §4.1.1。已更新理解，不阻塞；反使 exit 映射更简单。P2 据实测写解析规则 |

判据 1-3（目标方案不成立 / 平台前提不成立 / 已解决前提实际未解决）**均不命中**——按 P1 卡片"轻微漂移 → 记录后继续，不阻塞"。

## 5. 范围锁定核对（P0-brief 核心约束 6）

P1 分析**未发现**需超出四交付面的情形：

- `CommandRecord` IR 十字段（`platform` / `session_id` / `tool` / `command` / `ts_start` / `ts_end` /
  `exit` / `exit_signal` / `output_hash` / `truncated`）**足以表达 Codex 语义**——`exit` 直接取
  `item.exit_code`（数字，比 Claude Code/DSH 更干净）、`ts_start`/`ts_end` 取 `started_at_ms`/`completed_at_ms`、
  `truncated` 取截断信号。**无需扩 IR schema**。
- 检测引擎三态判据（调用冻结 / 活动冻结 / 无效重复）平台无关，消费 IR——**无需改 `agate-cmdstream-detect.py`**。
- 阈值（§3.4.3）平台无关——**无需改阈值**。
- 既有三平台适配器——**无需动**。
- **唯一改动** = `agate-cmdstream-adapters.py` 加 1 class + `ADAPTERS` 加 1 行 + `test_bdd_6` 精确断言改包含式
  （S4）+ 文档两处 + fixture + 新单测。

若 P2/P3/P4 发现必须扩 IR / 改检测引擎 / 改阈值 / 动既有适配器——**立即停下报告主 Agent**，不擅自扩范围（可能拆子任务）。

## 6. BDD 验收条件

> 每条可二值判定（PASS / FAIL），无中间态。行为视角（适配器解析出的字段值 / 检测引擎判定 /
> 协议文件是否含某锚文本 / check 脚本是否 exit 0），非"调用哪个函数"。

### 6.1 probe / list_sessions

#### BDD-1: probe 识别 Codex rollout JSONL，拒绝其它平台会话文件
- Given 路径指向一个 Codex rollout 文件（basename 形如 `rollout-<ts>-<uuid>.jsonl`、首行 `type=="session_meta"` 且 payload 含 codex 标记如 `cli_version`/`originator`），另给一个 Claude Code 转录 `.jsonl`（无 session_meta 首行）、一个 `.jsonl.zstd`、一个 `opencode.db`
- When 调用 `CodexAdapter().probe(path)`
- Then 对 Codex rollout 文件返回 `True`；对 Claude Code 转录 jsonl / `.jsonl.zstd` / `opencode.db` 均返回 `False`

#### BDD-2: list_sessions 枚举日期分层树下全部 rollout 文件
- Given 一个目录树含 `2026/09/08/rollout-A.jsonl` 与 `2026/09/09/rollout-B.jsonl`
- When 调用 `CodexAdapter().list_sessions(<树根>)`
- Then 返回列表同时包含 A、B 两个文件的绝对路径

#### BDD-3: list_sessions 不遗漏 spawn_agent 子会话文件
- Given 目录树含主会话 `rollout-P.jsonl`（`session_meta.thread_source` 为 `"user"`/缺省）与子会话 `rollout-C.jsonl`（`session_meta.thread_source=="subagent"`，含 `parent_thread_id`）
- When 调用 `list_sessions(<树根>)`
- Then 返回列表同时包含 `rollout-P.jsonl` 与 `rollout-C.jsonl`（子会话不被遗漏）

### 6.2 read_commands 字段映射

#### BDD-4: 从 CommandExecution 事件映射 CommandRecord 十字段
- Given 一个 Codex rollout fixture 含一条 `event_msg`/`item_completed`，`item.type=="CommandExecution"`，`item.command==["/bin/bash","-lc","echo hi"]`、`item.exit_code==0`、`item.aggregated_output=="hi\n"`、`payload.started_at_ms==T1`、`payload.completed_at_ms==T2`（T1<T2）
- When 调用 `read_commands(session_path)`
- Then 产出恰好 1 条 `CommandRecord`：`platform=="codex"`、`command` 含 `"echo hi"`、`tool` 非空字符串、`ts_start==T1`、`ts_end==T2`、`exit==0`、`exit_signal` 为非空原始形态留档、`truncated is False`、`output_hash == sha1("hi\n")`

#### BDD-5: 失败命令的 exit_code 非 0 如实映射，不回落 None
- Given rollout fixture 含一条 `CommandExecution`，`item.exit_code==2`、`item.status=="failed"`
  `[BASELINE_CHANGE: item.status 从 "completed" 改为 "failed"]` P6 V6 实测真机已结束非 0 退出命令记
  `status:"failed"`（DEBT0035）——Given 改用真机形态，Then 判定语义不变（仍是"失败命令 exit_code 非 0
  如实映射，不回落 None"），并加强断言 `ts_end`/`output_hash` 非 None（证明不被误判 pending）
- When `read_commands`
- Then 对应 `CommandRecord.exit == 2`（整数 2，非 None），`exit_signal` 留档原始形态（`"exit_code=2"`），
  `ts_end` 非 None、`output_hash` 非 None

#### BDD-6: 未结束命令 → exit=None / ts_end=None / exit_signal="pending"，不静默丢弃
- Given rollout fixture 含一条命令事件处于**真·未结束**状态（有 `item_started`/`item_updated` 无对应
  `item_completed`，且无 `completed_at_ms` / `exit_code`），同文件另有一条已完成命令
  `[BASELINE_CHANGE: "item.status != completed" 措辞收紧为"真·未结束"]` P6 V6 发现 `status:"failed"` 是
  已结束终态、不是未结束——pending 判据改为「无终态信号才算 pending」（`status ∉ {completed,failed}`
  且无 `completed_at_ms`/`exit_code`），见 P2 §5 设计点 2 BASELINE_CHANGE / DEBT0035。Then 语义不变
- When `read_commands`
- Then 未结束命令产出 1 条 `CommandRecord`，`exit is None`、`ts_end is None`、`exit_signal == "pending"`；已完成命令记录不受影响（`exit` 为其数字值）

#### BDD-7: 截断输出 → truncated=True 且 output_hash=None
- Given rollout fixture 含一条 `CommandExecution`，输出携带截断标记形态（P4 先用 §8 `[SUGGEST]` ③「比照 `DSHAdapter._detect_truncated` 保守双信号」兜底 fixture，P5 V4 实测后按 §4.1.2 收敛——不必等 V8/V4 产出才能写本 BDD 测试）
- When `read_commands`
- Then 对应 `CommandRecord.truncated is True` 且 `output_hash is None`

#### BDD-8: 非 shell 工具事件不产出 CommandRecord
- Given rollout fixture 含 `custom_tool_call` name=="exec" 但 `input` 为 `tools.apply_patch(...)` 与 `tools.web__run(...)`（无派生 `CommandExecution` 子事件）
- When `read_commands`
- Then 不为这两条非 shell 工具调用产出 `CommandRecord`（返回列表中无对应记录）

#### BDD-9: 畸形行不崩溃
- Given rollout fixture 含非 JSON 行、JSON 数组行（非 dict）、缺 `payload` 键的对象行，同文件另有合法 `CommandExecution` 事件
- When `read_commands`
- Then 不抛异常；坏行被跳过；合法命令记录照常产出

#### BDD-10: 同一会话文件的所有记录 session_id 一致且可定位
- Given 一个 Codex rollout fixture 含 ≥2 条 `CommandExecution` 事件
- When `read_commands`
- Then 所有产出记录的 `session_id` 相同、非空，且可据其定位回该会话文件

### 6.3 spawn_agent 子会话

#### BDD-11: 子会话记录可独立解析
- Given 一个 `spawn_agent` 子会话 rollout fixture（`session_meta.thread_source=="subagent"`，含该子代理执行的 `CommandExecution` 事件）
- When `read_commands(<子会话文件>)`
- Then 正常产出该子代理的 `CommandRecord`（`platform=="codex"`），不因缺父上下文而抛异常或返回空

#### BDD-12: 子会话的 session_id 指向子会话自身
- Given 子会话 rollout fixture，其 `session_meta` 中 `id`（子会话自身 id）≠ `session_id`（父会话 id）
- When `read_commands(<子会话文件>)`
- Then 产出记录的 `session_id` 解析为**子会话自身标识**（不是父会话标识）

### 6.4 检测引擎对 Codex 会话判三态（检测引擎零改动）

#### BDD-13: Codex 会话调用冻结 → FROZEN
- Given 一个 Codex 会话（fixture 或构造）含一条未结束命令、无 `expected` 声明，观察时刻距其 `ts_start` > 900s
- When 经 `read_commands` → `detect(events, now)`（或 CLI `detect --platform codex`）
- Then `verdict == "FROZEN"`，reasons 含"调用冻结"字样

#### BDD-14: Codex 会话活动冻结 → FROZEN
- Given 一个 Codex 会话所有命令均已结束，最后活动事件距观察时刻 > 300s
- When `detect`
- Then `verdict == "FROZEN"`，reasons 含"活动冻结"字样

#### BDD-15: Codex 会话无效重复 → SPIN
- Given 一个 Codex 会话窗口内同一 `(command, exit, output_hash)` 组合重复 ≥ 5 次（`exit_code` 与 `aggregated_output` 均不变、无截断）
- When `detect`
- Then `verdict == "SPIN"`

#### BDD-16: Codex 会话正常推进 → NORMAL（不误报）
- Given 一个 Codex 会话命令持续推进、结果签名（exit 或输出哈希）在变化、无未结束调用悬挂超阈值
- When `detect`
- Then `verdict == "NORMAL"`

#### BDD-17: Codex 会话截断输出不误判 SPIN
- Given 一个 Codex 会话同命令、同 exit、输出均被截断（`truncated=True`）重复 ≥ 5 次
- When `detect`
- Then `verdict != "SPIN"`（截断输出不参与哈希比对）

### 6.5 回归底线

#### BDD-18: 全量单测全绿（含新增 CodexAdapter 单测）
- Given 在 worktree 跑 `python3 -m pytest agate/tests/unit/ -q`
- When 运行完成
- Then 进程 exit 0，pytest 汇总 0 failed（既有 1361 passed 不减 + 新增 Codex 解析单测与三态试验全过；已知 xdist 偶发 flake `test_nc_symlink_script_readlink_resolves` 单独复跑全绿不算破损）

#### BDD-19: ADAPTERS 注册表精确等值断言已更新为包含式
- Given `test_agate_cmdstream_adapters.py::test_bdd_6_detect_consumes_registry_zero_change` 原有 `assert registered == {"claude-code","opencode","dsh"}`
- When 向 `ADAPTERS` 加入 `"codex"` 键后
- Then 该断言被改为包含 `"codex"`（四键集合或 `>=` 包含式），改后整片 `test_agate_cmdstream_adapters.py` pytest 全绿；断言语义（检测引擎零改动消费注册表）不变

#### BDD-20: 协议一致性 0 ERROR
- Given 在 worktree 跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
- When 运行完成
- Then 进程 exit 0，输出 0 ERROR（新增 Codex 章 / SETUP 小节不引入新 ERROR；存量 WARNING 不新增本质性条目）

#### BDD-21: 检测引擎 / IR / 阈值 / 既有三适配器零功能改动
- Given `git diff main..HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py`
- When 检查 diff
- Then `agate-cmdstream-ir.py` 的 `CommandRecord` dataclass 十字段定义无改动、`agate-cmdstream-detect.py` 的阈值常量（`CALL_ALERT_FALLBACK` 等）与 `detect()` 判定逻辑无改动（diff 为空或仅 docstring/注释）；`agate-cmdstream-adapters.py` 中 `ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` 三 class 体无改动，新增仅 `CodexAdapter` class + `ADAPTERS` 字典加一行

### 6.6 platform-notes.md Codex 章

#### BDD-22: Codex 章从「待补充」补为完整能力矩阵
- Given `agate/platform-notes.md` 的 `## Codex ...` 节
- When 阅读该节
- Then 不再含"待补充"字样；且逐项可 grep 命中：非交互 `codex exec`、`-m`/`--model`、`-c model_reasoning_effort=<low|medium|high>` 推理档、`--dangerously-bypass-approvals-and-sandbox`、中间档 `-s <read-only|workspace-write|danger-full-access>` + `--approve-for-me`（并注明 `--full-auto`/`-a` 已从 `codex exec` 移除）、`spawn_agent` 原生子派发、`--json` 结构化输出、`resume`、"退出码不可靠须解析 `--json`"

#### BDD-23: 验证 CLI 版本号与账号类型已注明
- Given Codex 章
- When 检索
- Then 含字符串 `0.153.4`，且注明验证账号类型为 ChatGPT 登录、验证日期（2026-09），并含"新兴平台需持续复核 / 目标版本上 `codex features list` 复核"意味的表述

#### BDD-24: spawn_agent schema 证据强度如实标注、不混同
- Given Codex 章中关于 `spawn_agent` 参数 schema 的段落
- When 阅读
- Then 明确标注为 `[自述]`（或等价措辞）；不把"未见 `background`/`timeout`/`permission` 字段"表述为"确认无这些字段"；并指明"穷尽 schema 直接实测"是真机验证清单待执行项

#### BDD-25: 新 Codex 章与既有 Codex 内容不自相矛盾
- Given `platform-notes.md` 既有 line 53-70 的 Codex 列（Hardening-roadmap 跨平台适配表）+ line 67-70「Codex 兼容性」注记（`Codex subagent max_depth=1`）
- When 新增 `## Codex` 章
- Then 新章对 `spawn_agent` / 多层派发的表述与既有注记**交叉引用并标注时效**（如"`multi_agent` flag 已 stable/true、`spawn_agent` 单层已实测可用、嵌套深度未测——既有 max_depth=1 注记写于 subagent workflows 默认启用前，待复核"）；全文档不存在"一处说 Codex 无法再派发、另一处说已支持多层"这类未标时效的对立陈述

#### BDD-26: model 阵容随账号类型的表述完整
- Given Codex 章 model 小节
- When 阅读
- Then 注明：ChatGPT 账号下 `codex exec -m` 默认 `gpt-5.6-terra`（`-m gpt-5`/`-m gpt-5-codex` 被 400 拒）；`spawn_agent` 的 `model` 枚举为 `gpt-5.6-terra`/`gpt-5.6-luna`/`gpt-5.5`/`gpt-5.4-mini`（`[自述]`）；API-key 账号 model 阵容登记为"待有该环境时补"（非阻塞）

### 6.7 SETUP.md Codex 小节

#### BDD-27: SETUP.md 新增 Codex 接入小节
- Given `agate/SETUP.md`
- When 检索
- Then 含独立 Codex 小节，覆盖：安装（`npm i -g @openai/codex` 或官方方式）、`codex login`（并说明 ChatGPT vs API key 影响可用 model）、自动化环境绕过 flag（`--dangerously-bypass-approvals-and-sandbox`、`--skip-git-repo-check`）

### 6.8 SELF-GATE 留痕

#### BDD-28: SELF-GATE commit 留痕 + 协议对齐评审存在
- Given 本任务改 `agate/scripts/agate-cmdstream-adapters.py` + `agate/platform-notes.md` + `agate/SETUP.md` + `agate/tests/`（触发 SELF-GATE）
- When 检查 P7/P8 的 commit message 与产出
- Then commit message 含 `self-gate-review:` 或 `self-gate-skip:` 前缀行；`check-protocol-consistency.py --strict-errors-only` 记录为 0 ERROR；protocol-alignment-review 产出存在且 `agent != main`

### 6.9 真机验证清单

#### BDD-29: 真机验证清单成形且逐项四要素可判定
- Given P1-requirements.md §7「真机验证清单」
- When 检查
- Then 每一项均写明「验证什么 / 怎么验（含具体命令）/ 在哪个阶段执行（P5 或 P6）/ 通过判据（可二值）」四要素；本机 ChatGPT 账号做不了的项（API-key 账号 model 阵容）显式标注"待有该环境时补（非阻塞）"并给出 `verification_env_budget` 轮次占位

#### BDD-30: spawn_agent schema 穷尽实测项已登记且方法边界已注明
- Given §7 真机验证清单
- When 检查
- Then 含一项"直接实测穷尽 `spawn_agent` 参数 schema（是否存在 `[自述]` 未提及的 `background`/`timeout`/`permission` 等字段）"，并注明 P1 已确认"令模型逐字输出内部 tool schema"此法不可用（模型拒绝），P5-P6 须换法（读 codex 二进制/内省、API-key 账号观察、或跨大量真实调用归纳），通过判据 = 给出字段全集并在 platform-notes.md 标 `[实测]`

## 7. 真机验证清单（P1 定 / P5-P6 执行，比照 RM-AG0055 三平台数据源验证严格度）

| 项 | 验证什么 | 怎么验（命令）| 阶段 | 通过判据（二值）| 本机可做？ |
|---|---|---|---|---|---|
| V1 | `~/.codex/sessions/` 目录结构与 rollout JSONL 格式与 fixture/解析假设一致 | 读若干真实 `rollout-*.jsonl` 头尾；核对 `CommandExecution` item 的 `command`/`exit_code`/`status`/`started_at_ms`/`completed_at_ms`/`aggregated_output` 字段存在且形态与 §4.1 描述一致 | P5 | fixture 字段结构逐项能在真实 rollout 找到对应；`read_commands` 对真实文件不抛异常、产出记录字段非空 | ✅ 已做（§4.1）；P5 复核为回归 |
| V2 | `spawn_agent` 完整参数 schema（穷尽——是否有 `background`/`timeout`/`permission` 等 `[自述]` 未提及字段）| 换法：`strings $(command -v codex)` / 读 codex 包内 schema 定义 / 或 API-key 账号跑 `codex exec --json` 观察 `function_call.arguments` 键全集 / 或跨 ≥20 次真实 `spawn_agent` 调用归纳键并集 | P5-P6 | 给出 `spawn_agent` 参数键全集 + 每键类型/枚举/默认；platform-notes.md 对应段从 `[自述]` 升级为 `[实测]` 或如实保留 `[自述]` + 已尽力说明 | ⚠️ 部分——本机可跨真实调用归纳（ChatGPT 账号）；`[自述]` 逐字 dump 已确认不可用（§4.3）|
| V3 | `spawn_agent` 子会话是独立 rollout 文件、父子关联字段稳定 | 现场派 `spawn_agent(task_name=X)`；`find ~/.codex/sessions -newermt "-2 min"`；核对新子文件 `session_meta` 含 `parent_thread_id` / `source.subagent.thread_spawn` / `thread_source=="subagent"` | P5 | 子会话为独立 `rollout-*.jsonl`；`list_sessions` 枚举到它；`read_commands` 产出 `session_id` 指向子会话自身 | ✅ 已做（§4.2）；P5 复核为回归 |
| V4 | Codex 输出截断标记的确切形态 | 构造超 `max_output_tokens` 的命令（如 `yes | head -c 500000`）经 `codex exec`；读落盘 rollout 的 `CommandExecution` item，找截断字段/文本标记 | P5 | 拿到确切截断标记形态；`CodexAdapter` 截断检测对该形态命中 → `truncated=True` + `output_hash=None`（BDD-7 fixture 用该形态）| ✅ 可做（本机 ChatGPT 账号足够）|
| V5 | `codex features list` 的 `multi_agent` flag 在目标版本仍 stable+on | `timeout 60s codex features list \| grep -iE "multi_agent\|spawn\|collab"` | P5/P6 | `multi_agent` = stable / true；platform-notes.md 版本注记与实测一致 | ✅ 已做（§4.4）；P6 复核 |
| V6 | 检测引擎对真实 Codex 会话（非 fixture）判三态正确 | 造真实卡死场景（`codex exec` 派一个跑 `sleep 1200` 的命令并中途 SIGTERM 会话）+ 正常会话 + 重复失败会话；各跑 `agate-cmdstream-detect.py detect <rollout> --platform codex --now <虚拟时刻>` | P6 | 卡死会话 → FROZEN；正常会话 → NORMAL；重复失败会话 → SPIN（与 BDD-13~17 一致）| ✅ 可做 |
| V7 | `spawn_agent` 嵌套深度（`spawn_agent` 内再 `spawn_agent`）| 派一个子代理并指示它再 `spawn_agent` 一个孙代理；观察 `~/.codex/sessions/` 是否生成孙会话文件、`session_meta.source.subagent.thread_spawn.depth` 值 | P6 | 得出嵌套是否生效 + `depth` 字段行为；platform-notes.md 如实记录（既有 max_depth=1 注记据此复核）| ✅ 可做（非阻塞——结论不改 CodexAdapter 契约，`list_sessions` 已按 `os.walk` 覆盖任意深度独立文件）|
| V8 | API-key 账号 model 阵容（`gpt-5` / `o3` 等是否可用、`spawn_agent` model 枚举是否更宽）| 在 API-key 账号环境跑 `codex exec --json -m gpt-5 <<< "hi"` 与 `spawn_agent(model=...)` 各种枚举 | P5/P6 | 得出 API-key 账号可用 model 集；platform-notes.md 补 API-key 账号一列 | ❌ **待有该环境时补（非阻塞）**——本机为 ChatGPT 账号。`verification_env_budget: 止损轮次 2`；主 Agent 在 P5/P6 dispatch-context 记录轮次 |

> V8 是唯一"环境不可得"项：按 P0-brief 核心约束 5 / research §11 #5，登记为 `verification_env` 类"待有该环境时补"，
> **不阻塞** P1-P8 推进；platform-notes.md 在 API-key 账号列显式写"本会话未核实，待补"。其余 V1-V7 本机可做。

## 8. 待确认清单

`[NO_NEED_CONFIRM]` —— 无真无方向、需人定夺的点。

倾向项（主 Agent 可直接采纳，不必问用户）：
- `[SUGGEST: ADAPTERS 注册表键名用 "codex"，理由：与 CommandRecord.platform 标识、research 文档命名、CLI 名一致；P2 可最终定]`
- `[SUGGEST: read_commands 只以 rollout JSONL（~/.codex/sessions/**/*.jsonl）为源，codex exec --json 实时流不强制实现，理由：--json 流不带 per-item 时间戳（§4.5），detect() 需要 ts_start/ts_end；如需实时源建议 P2 列 out-of-scope 或后置]`
- `[SUGGEST: 截断标记形态在 P5 V4 实测前，CodexAdapter 采用比照 DSHAdapter._detect_truncated 的保守双信号，理由：不阻塞 P2/P3，实测后收敛]`

## 9. 裁剪说明

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]` —— **全阶段保留，不裁剪**。

| 阶段 | 保留理由 |
|---|---|
| P1 | 核心阶段，不可裁 |
| P2 | 需设计：probe 判据（区分 Codex/Claude jsonl）、`read_commands` 事件→IR 映射规则、`session_id` 取法、截断信号、子会话判定——多个设计点 |
| P3 | 改脚本走 TDD（AGENTS.md「改脚本的工作流」），不可裁 |
| P4 | 实现 CodexAdapter + 改 `test_bdd_6` 断言，不可裁 |
| P5 | 真机验证清单 V1-V7 本机执行（§7），不可裁 |
| P6 | 检测引擎对真实 Codex 会话三态验收（V6）+ 嵌套深度（V7），不可裁 |
| P7 | 触发 SELF-GATE + 改协议文档（platform-notes/SETUP）→ `check-protocol-consistency.py` + protocol-alignment-review（A1-A6），P7 不可裁 |
| P8 | 对外发布面（协议本体变更 + roadmap 回写 RM-AG0061→done + 归档 HANDOFF），不可裁 |

`risk_level: medium` —— 新适配器完全增量（零改动检测引擎/IR/阈值/既有适配器）+ 强回归底线（全量 pytest +
consistency 0 ERROR），但改协议本体（platform-notes/SETUP）+ 触发 SELF-GATE，介于 low 与 high 之间取 medium。

`ceremony: standard` —— 不申请 thin（SELF-GATE + 协议文档变更，fail-closed 按 standard）。

## 10. 能力需求声明

见 frontmatter `capability_requirements`：
- `codex-cli-installed-authenticated`：**available**（本机 codex-cli 0.153.4 + ChatGPT 登录，`codex exec` /
  `codex features list` / `spawn_agent` 均已实测 exit 0）
- API-key 账号 model 阵容（§7 V8）是**运行环境不可得项**，不是 `capability_requirements` 条目——走 frontmatter
  `verification_env` + `verification_env_budget: 止损轮次 2` 声明（按 P1 卡片「verification_env vs supplementable
  边界判断树」：换谁来做都得先有 API-key 账号 → 环境问题）。非 GAP、非阻塞；由 §7 V8 + BDD-26 / BDD-29 承载。

无视觉能力需求（`domains: [backend]`，无用户可见页面 / 渲染产线）。
