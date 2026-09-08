---
phase: P2
task_id: TAG0033
type: design
parent: P1-requirements.md
trace_id: TAG0033-P2-20260909
status: draft
created: 2026-09-09
agent: architect
candidate_count: 3
packages:
- agate-scripts
- agate-docs
- agate-tests
domains:
- backend
ui_affected: false
follows_existing_pattern:
- agate/scripts/agate-cmdstream-adapters.py
dispatch_plan:
  mode: static-batch
  parallel_limit: 2
  batches:
  - id: adapter-core
    complexity: medium
  - id: protocol-docs
    complexity: low
---

# P2 方案设计 — TAG0033 Codex 命令流适配器 + 平台接入（RM-AG0061）

> parent：`P1-requirements.md`（已 approved，30 BDD + §4 spike 实测 + §3 同类扫描 + §5 范围锁定）
> 设计依据：`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/` §3.4.2/§3.4.3/§3.4.4
> 近亲实现范式：`agate/scripts/agate-cmdstream-adapters.py` 的 `DSHAdapter`（line 394-618）
>
> 本文在 P1 §4 既定 spike 事实上做**方案取舍与结构设计**，不重新调查。P1 §8 的 3 条 `[SUGGEST]`
> 已由主 Agent 采纳，本文作既定前提（见 §1）。

`[PROD_NOT_TOUCHED]`

---

## 0. 既定前提（P1 §8 SUGGEST，主 Agent 已采纳）

| # | 前提 | 本文如何落 |
|---|---|---|
| 1 | `ADAPTERS` 注册表键名 = `"codex"` | §4.2 M2 / §5 设计点 2、5；`CodexAdapter.platform = "codex"` |
| 2 | `read_commands` 只以 rollout JSONL（`~/.codex/sessions/**/*.jsonl`）为源；`codex exec --json` 实时流**不实现** | §3 out-of-scope；§5 设计点 2 源过滤 |
| 3 | 截断标记 P5 V4 实测前，比照 `DSHAdapter._detect_truncated` 保守双信号兜底 | §5 设计点 4 |

---

## 1. 目标与完成标志

**目标**：给 RM-AG0055 命令流机制新增 `CodexAdapter`，使 subagent 存活/卡死检测覆盖 Codex 平台，
检测引擎 / 阈值 / `CommandRecord` IR / 既有三适配器**零功能改动**。

**实现完成的标志**（供 P3 测试设计 / P5 验证）：

1. `CodexAdapter` 实现 `CommandStreamAdapter` 三方法，`ADAPTERS["codex"]` 可解析真实 rollout JSONL 不抛异常。
2. BDD-1~17 对应单测（解析 + 三态确定性试验）全绿；BDD-18 全量 `pytest agate/tests/unit/ -q` exit 0。
3. `git diff main..HEAD` 中 `agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` 无功能 diff；
   `agate-cmdstream-adapters.py` 仅新增 `CodexAdapter` class + `ADAPTERS` 一行（BDD-21）。
4. `test_bdd_6_detect_consumes_registry_zero_change`(:317) 精确等值断言改包含式，语义不变（BDD-19）。
5. `platform-notes.md` Codex 章 / `SETUP.md` Codex 小节补全，`check-protocol-consistency.py
   --strict-errors-only` exit 0（BDD-20/22~27）。
6. P4/P7 commit message 含 SELF-GATE 留痕；P7 protocol-alignment-review 产出存在且 `agent != main`（BDD-28）。

---

## 2. 影响面梳理（候选方案之前，强制节）

> P0「同类/影响面预判」给量级、P1 §3 同类扫描 12 行给清单、P1 §5 范围锁定给边界——本节在其上做
> **候选方案级**的影响域分析，客观证据 = 本次 grep 命中 + 读过的消费方代码 + minimal_validation。

### 2.1 改什么（Modify）

| 文件 | 改动点（落到函数/小节）| 关联 BDD |
|---|---|---|
| `agate/scripts/agate-cmdstream-adapters.py` | 新增 `class CodexAdapter(CommandStreamAdapter)`，插入位置 = `DSHAdapter` 之后、`# ---- 显式注册表` 之前（line 620 附近）。成员：`platform = "codex"`；`probe(self, path)`；`list_sessions(self, cwd)`；`read_commands(self, session_path)`；`@classmethod _detect_truncated(cls, item)`；`@staticmethod _build_record(...)`；模块级 2 个截断常量 `_CODEX_TRUNC_BOOL_KEYS` / `_CODEX_TRUNC_TEXT_MARKERS`（紧挨 class 上方，带 `# P5 V4 收敛锚` 注释） | BDD-1~12 |
| 同上 | `ADAPTERS` 字典（line 623-627）加 `"codex": CodexAdapter(),` 一行 | BDD-6 / BDD-19 |
| 同上 | 复用（**不改定义**）：`_sha1_hex`(line 68)、`_iso8601_to_epoch_ms`(line 73，仅 fallback 用)、基类 `CommandStreamAdapter`(line 95) | — |
| `agate/tests/unit/test_agate_cmdstream_adapters.py` | `test_bdd_6_detect_consumes_registry_zero_change`(line 317) `assert registered == {"claude-code","opencode","dsh"}` → 改为含 `"codex"` 的四键集合等值 **或** `>=` 包含式；注释保留"检测引擎零改动消费注册表"语义 | BDD-19 |
| 同上 | `test_bdd_7_fixture_sanitized`(line 331-342) 的 `for name in (...)` 元组加 `"cmdstream/codex-session.jsonl"`；确认脱敏正则对 Codex uuid 形态有效（见 §2.3 风险 R7） | S10 / BDD-7 |
| 同上 | 新增 `CodexAdapter` 解析单测：BDD-1~12 各一 test 函数，比照既有 `test_bdd_2_*`~`test_bdd_5_*` 范式（fixture 驱动 + 运行时构造边界样例） | BDD-1~12 |
| `agate/tests/unit/test_agate_cmdstream_detect.py` | 新增 Codex 会话三态确定性试验：调用冻结→FROZEN / 活动冻结→FROZEN / 无效重复→SPIN / 正常推进→NORMAL / 截断重复→非 SPIN，比照既有 `_run_detect` + `_ev` 虚拟时钟范式；**可选**：`test_bdd_24_output_platform_agnostic`(line 371) 元组加 `"codex"`（断言 Codex 词也不泄漏） | BDD-13~17 |
| `agate/tests/fixtures/cmdstream/codex-session.jsonl`（**新建**） | 字段结构取自真实 rollout（minimal_validation 已核）+ 内容脱敏（`demo` 前缀 / 无 `/home/kity` / 无密钥 / 无真实会话 uuid）。内容覆盖：≥2 条 `event_msg`/`item_completed` `CommandExecution`（exit 0 与非 0 各一）、1 条未结束命令、1 段 `spawn_agent` 子会话片段（`session_meta.thread_source=="subagent"`，`id`≠`session_id`）、非 shell 工具事件（`apply_patch`/`web__run` 的 `custom_tool_call`）、畸形行（非 JSON / 非 dict / 缺 payload）、截断兜底样例 | BDD-4~12 / BDD-7 |
| `agate/platform-notes.md`（**P7 阶段**）| `## Codex / Hermes / OpenClaw 等`（line 43-45「待补充」）→ 完整能力矩阵 + 实机验证记录（CLI 0.153.4 / ChatGPT 账号 / 2026-09）；与 line 53-70 既有 Codex 列 + line 67-70「Codex 兼容性」`max_depth=1` 注记**交叉引用 + 标时效**，不删既有行、不产生对立陈述 | BDD-22~26 |
| `agate/SETUP.md`（**P7 阶段**）| 新增独立 Codex 接入小节，比照 line 144 DSH 小节结构：安装（`npm i -g @openai/codex` 或官方方式）+ `codex login`（ChatGPT vs API key 影响 model）+ 自动化绕过 flag（`--dangerously-bypass-approvals-and-sandbox` / `--skip-git-repo-check`）| BDD-27 |

**grep 客观证据**（worktree 全仓）：

- `agate-cmdstream-detect.py`：`ADAPTERS = _load_adapters().ADAPTERS`(line 96)；CLI `choices=sorted(ADAPTERS.keys())`(line 308/312/317)；`adapter = ADAPTERS[args.platform]`(line 328)——**均动态取自注册表，无硬编码三键**。
- `test_agate_cmdstream_adapters.py`：`:298` 已是 `>=` 包含式（`test_bdd_6_adapter_registry_contract`）；`:317` 精确等值（`test_bdd_6_detect_consumes_registry_zero_change`）——**只有后者需改**。
- `test_agate_cmdstream_detect.py:371`：`for platform_word in ("claude", "opencode", "dsh")` 负向断言，加第四键不打破（可选强化）。

### 2.2 不改什么（Not Modify）

| 文件/范围 | 看起来该改 | 不改的理由（证据）|
|---|---|---|
| `agate/scripts/agate-cmdstream-detect.py`（检测引擎 + CLI）| "新平台接入检测" | CLI `choices` 与 `ADAPTERS[...]` 全部动态取注册表（见 §2.1 grep）；`detect()` 判据消费 `CommandRecord` IR、平台无关。**BDD-21 锁定 detect.py 零功能 diff**。加 `"codex"` 键即自动纳入 CLI `choices` |
| `agate/scripts/agate-cmdstream-ir.py` `CommandRecord` dataclass（line 31-44）| "Codex 语义要落字段" | 十字段足以表达 Codex：`exit`←`item.exit_code`（**数字**，比 Claude/DSH 更干净，无需文本前缀解析）、`ts_start/ts_end`←`payload.started_at_ms`/`completed_at_ms`（epoch ms int，直接取）、`truncated`←双信号。**无需扩 schema**（P1 §5 / BDD-21）|
| `agate-cmdstream-detect.py` 阈值常量（line 42-50 `CALL_ALERT_FALLBACK` / `SPIN_THRESHOLD` 等）| — | 阈值平台无关（RM-AG0055 §3.4.3）。BDD-21 |
| `ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` 三 class 体 | "重构提取公共逻辑" | **零改动硬约束**（P0 核心约束 2 / BDD-21）。`_sha1_hex` / `_iso8601_to_epoch_ms` 是模块级助手，`CodexAdapter` 直接调用即可，不动其定义、不做"顺手重构" |
| `test_agate_cmdstream_adapters.py:298`（`test_bdd_6_adapter_registry_contract`）| "也断言注册表键集" | 已是 `set(...) >= {...}` 包含式，加第四键不破（P1 §3 S3）|
| `check-protocol-consistency.py` CHECK 12 / 14 / 15 锚点 | "新增协议文档要登记锚点" | CHECK 12 `AUTHORITATIVE_VALUE_ANCHORS` 只含 `retry-max`，与 `platform-notes.md` 能力矩阵**无关**；`platform-notes.md` / `SETUP.md` 是 `_MD14_WHOLE_FILE_EXEMPT` **整文件豁免**（平台适配权威源）。**本任务不新增 CHECK / 锚点**（P0 核心约束 / DEBT0025，P1 §3 S6/S7 已扫描确认）|
| `agate/WORKFLOW.md:6,8,156` 的 Codex 行 | "提到 Codex" | 是「已知适用环境」环境适用性声明，与命令流适配器无关，已一致（P1 §3 S9）。非本任务交付面 |
| `codex exec --json` 实时事件流源 | "P0 scope 写了『实时源可用』" | P1 §4.5 实测：实时流事件**不带 per-item 时间戳**，`detect()` 需 `ts_start`/`ts_end` → 只以 rollout JSONL 为源（SUGGEST ②）。列 out-of-scope（§3）|
| `agate/tests/fixtures/cmdstream/` 既有 3 个 fixture | — | 只新增 `codex-session.jsonl`，不动既有 |

### 2.3 风险在哪（Risk，每条配缓解）

| # | 风险 | 缓解 |
|---|---|---|
| R1 | `ADAPTERS` 加第四键打破 `test_bdd_6`(:317) 精确等值断言 → 整片 `test_agate_cmdstream_adapters.py` 红 | P4 **同批**改断言为包含式（BDD-19）；`:298` 已是 `>=` 无需动；改后整片 pytest 复跑全绿是 P4 自检项 |
| R2 | 截断信号形态 `[未实测]`（V4 前）→ 双信号常量猜错 → 漏判 `truncated` → 截断输出参与哈希 → 误判 SPIN（违反 BDD-17）| 比照 `DSHAdapter._detect_truncated` 保守双信号（bool 键集 ∪ 文本标记集，任一命中即 True）；**收敛面收窄**为 `CodexAdapter._detect_truncated` 一个 classmethod + 上方 2 个模块常量 + `# P5 V4 收敛锚` 注释；P5 V4 实测后**定向改这三处**，不动其它。`truncated=True ⇒ output_hash=None` 在 `_build_record` 无条件强制（IR 铁律，不放宽）|
| R3 | 未结束 / pending 命令的 rollout 形态 `[未实测]`（minimal_validation 未捕获 `item_started` CommandExecution）→ BDD-6 映射规则可能与真机不符 | 双判据：`item_completed` 且 `item.status != "completed"` **∪**「同 `item.id` 有 `item_started`/`item_updated` 无 `item_completed`」；fixture 手造（BDD-6 Given 明确允许）；写成 P5 易替换形式；detect CLI 已能跳过 `ts_start is None` 记录 |
| R4 | `probe` 只看 basename → Claude Code 转录若命名近似 `rollout-*.jsonl` 误判 True（且 `ClaudeCodeAdapter.probe` 对同扩展名文件也返回 True，二者重叠）| basename 正则（`rollout-` 前缀 + `.jsonl` 后缀 + 非 `.zstd`）**+** 首行 `readline()` sniff `type=="session_meta"` 且 payload 含 codex 标记（`cli_version` / `originator` / `id`）。Claude Code 转录首行无 `session_meta` → False。BDD-1 覆盖（含 `.jsonl.zstd` / `opencode.db` 负例）|
| R5 | 子会话 `session_id` 误取 `session_meta.session_id`（minimal_validation 证实该字段对子会话 = **父** id）→ 违反 BDD-12 | `session_id = os.path.basename(session_path)`（照搬 `ClaudeCodeAdapter`/`DSHAdapter`）——子会话 rollout 文件名含**子自身** uuid；明确**不取** `payload.session_id`；§5 设计点 3 详述 |
| R6 | 改 adapters.py + tests/ + platform-notes.md + SETUP.md → 触发 SELF-GATE 未留痕 | P4/P7 commit message 强制 `self-gate-review:` 路径 或 `self-gate-skip:` 理由（`commit-msg-self-gate.sh` hook）；P7 派 protocol-alignment-review 走 A1-A6，产出 `agent != main`（BDD-28）。§6 SELF-GATE 预告 |
| R7 | fixture 含真实 `~/.codex/sessions/` 片段 → 泄露用户路径（`/home/kity/.codex/...`）/ 会话 uuid | 脱敏：`/home/kity/*` → `/demo/repo`；真实 uuid（`01a0811c-...` 8-4-4-4-12 hex 形态）→ `demo` 占位（如 `demo0000-0000-7000-a000-0000000000p0` / `demo0000-...-0000c0` 父子）；纳入 `test_bdd_7_fixture_sanitized` 清单。**注**：`test_bdd_7` 现有正则 `\b(?:ses\|msg\|prt\|call)_[0-9a-f]{26}\b` 不匹配 Codex 连字符 uuid → P4 用 `demo` 前缀 uuid 即可满足既有 `assert "demo" in text` + `assert not re.search(...)`；无需改正则（若 P4 认为需补 Codex uuid 形态断言，属 `test_bdd_7` 强化，同批可做，非零改动违规）|
| R8 | `check-protocol-consistency.py` 误用 `~/.agate` 稳定版 → 扫到主 checkout 的协议文件 | `P5_consistency` 命令固化为 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（**worktree 相对路径**）；AGENTS.md line 54 明载"gate 工具 ≠ 检查对象"纪律 |
| R9 | Codex CLI 版本漂移（session 格式 / flag 名 / model 阵容 / feature flag 命名史）| `platform-notes.md` Codex 章注明验证版本 `0.153.4` + 账号类型 + "目标版本 `codex features list` 复核一次"；`spawn_agent` schema 段标 `[自述]` 不混同 `[实测]`（BDD-23/24/25/26）|
| R10 | fixture 的 `spawn_agent` 子会话片段与主会话片段放**同一个** `.jsonl` 文件，但真机是**两个独立文件** | fixture 用**两个逻辑段**（同文件内注释分隔）或 P4 建 `codex-session.jsonl` + `codex-subagent-session.jsonl` 两文件——`test_bdd_7` 清单相应加两项。推荐后者（贴近真机、`read_commands` 单文件语义清晰）；文件数 +1 在 fixture 目录属常规，不触发范围外 |

---

## 3. out-of-scope（本任务不做 / 后置）

- `codex exec --json` 实时事件流作为 `read_commands` 源——实时流不带 per-item 时间戳（P1 §4.5），`detect()` 需 `ts_start`/`ts_end`。**后置**，如未来需要实时源，另立任务并自造时间戳（行接收时刻）。
- Codex 作**宿主平台**跑 Agateon 的完整 onboarding（预设模板 / 单 Agent 模式）——P0 out-of-scope。
- RM-AG0060 的配置路由 / 子进程派发 / tmux 层——本任务是其前置，不含其内容。
- `spawn_agent` 嵌套深度（孙代理）机制结论——真机验证清单 V7 观察即可，不改 `CodexAdapter` 契约（`list_sessions` 的 `os.walk` 已覆盖任意深度的独立文件）。
- 新增 gate 脚本 / CHECK / 权威值锚点——P0 核心约束 / DEBT0025。

---

## 4. 契约与数据流

### 4.1 数据流

```
list_sessions(cwd)                      read_commands(session_path)
  cwd truthy → os.walk(cwd)               open(session_path) 逐行
  else       → os.walk(~/.codex/sessions)   line → json.loads（坏行 skip 计数）
  收集 name.startswith("rollout-")          dict? type=="event_msg"? payload dict?
       and name.endswith(".jsonl")          payload.type in (item_completed, item_started/updated)?
  sorted(路径字符串)  → list[abs path]      payload.item.type == "CommandExecution"?
                                              ↓ 是
                                            _build_record → CommandRecord(platform="codex", ...)
                                              ↓
                                            pending 补齐（item_started 无 item_completed）
                                              ↓
                                            list[CommandRecord]  → 检测引擎（零改动消费 IR）
```

### 4.2 `CommandRecord` 十字段映射（M1，不改 IR）

| 字段 | Codex 取法 | 备注 |
|---|---|---|
| `platform` | 常量 `"codex"` | SUGGEST ① |
| `session_id` | `os.path.basename(session_path)` | 设计点 3；子会话 = 子文件名（含子 uuid）|
| `tool` | 常量 `"exec"` | 设计点 2；BDD-4 只要"非空字符串"|
| `command` | `shlex.join(item.command)`（元素逐个 `str()` 强转；非 list → `""`）| 设计点 2；BDD-4「含 `echo hi`」满足 |
| `ts_start` | `payload.started_at_ms`（int，非 bool）；缺 → fallback 首行封套 `timestamp` 经 `_iso8601_to_epoch_ms`；再缺 → `None` | epoch ms 直接取 |
| `ts_end` | `payload.completed_at_ms`（int）；pending → `None` | |
| `exit` | `item.exit_code`（int，非 bool）；pending / 无字段 → `None` | **无需文本前缀解析**（P0_STALE 已修正）|
| `exit_signal` | 完成有 exit_code → `f"exit_code={n}"`；完成无 exit_code → `item.status` 或 `"status=completed"`；pending → `"pending"` | BDD-4「非空原始形态留档」/ BDD-6「`=="pending"`」|
| `output_hash` | `_sha1_hex(item.aggregated_output or "")`；`truncated` → `None` | 复用既有助手 |
| `truncated` | `CodexAdapter._detect_truncated(item)` | 设计点 4 |

### 4.3 `CommandStreamAdapter` 契约方法签名（与基类 line 95-110 一致）

- `probe(self, path) -> bool`
- `list_sessions(self, cwd) -> list[str]`
- `read_commands(self, session_path) -> list[CommandRecord]`

---

## 5. CodexAdapter 5 个设计点（每点 候选方案 + 权衡 + 定论）

> `candidate_count: 3` —— 设计点 1 / 3 / 4 / 5 各给 3 候选；设计点 2 的三处字段子决策各给 2-3 候选。
> 解析骨架（逐行 `try/except` + `os.walk` 枚举 + basename `session_id`）声明
> `follows_existing_pattern: [agate/scripts/agate-cmdstream-adapters.py]`（照搬 `DSHAdapter`）。

### 设计点 1 —— `probe(path)` 判据

**候选**

| # | 方案 | 优点 | 风险 / 成本 |
|---|---|---|---|
| A | 只看 basename 正则（`^rollout-.*\.jsonl$` 且非 `.zstd`）| 零 I/O，最快 | `.jsonl` 扩展名与 Claude Code 转录共享；`ClaudeCodeAdapter.probe` 对同文件也 True（重叠）；被改名文件 / 非常规命名漏判反向不稳 |
| B | **basename 正则 + 首行 `readline()` sniff**（首行 JSON、`type=="session_meta"`、payload 含 codex 标记 `cli_version`/`originator`/`id` 任一）| 正向信号强（Claude Code 转录首行无 `session_meta`）；只读一行，大文件安全 | 一次 `open`+`readline`（可忽略）；首行畸形需兜底 |
| C | 只做首行 sniff（不看 basename）| 容忍改名 | 每个 `.jsonl` 都要开文件；specificity 低于 B（basename 是 Codex 的强约定）|

**定论：B**。basename 正则（`rollout-` 前缀 + `.jsonl` 后缀 + 排除 `.zstd`）作廉价门 + 首行
`readline()` 判 `type=="session_meta"` 且 payload 含 codex 标记。理由：`.jsonl` 与 Claude Code
碰撞，单靠 basename 不够"可靠区分"；首行 sniff 是 Claude Code 转录不具备的正向特征（minimal_validation
证实 23 文件首行恒为 `session_meta`，含 `cli_version=="0.153.4"` / `originator`）。**性能**：`with
open(path) as f: first = f.readline()` 只读第一行，不 `json.load` 整文件。**兜底**：路径不存在 /
非文件 / 不可读 / 首行非 JSON / 非 dict → 返回 `False`，绝不抛异常。

### 设计点 2 —— `read_commands` 事件→`CommandRecord` 映射规则

**源过滤**（定论，无候选）：逐行 `json.loads`（`except (ValueError): skipped+=1; continue`）→
`isinstance(obj, dict)` → `obj.get("type")=="event_msg"` → `p=obj.get("payload")`，`isinstance(p, dict)`
→ `p.get("type")` ∈ {`item_completed`（主）, `item_started`/`item_updated`（pending 判据）} →
`it=p.get("item")`，`isinstance(it, dict)` → `it.get("type")=="CommandExecution"`。
**非 shell 工具事件（BDD-8）由此天然排除**：minimal_validation 证实 `tools.apply_patch(...)` 派生
`FileChange` item、`tools.web__run(...)` 派生 `Extension` item，均非 `CommandExecution` → 不进映射，
无需额外过滤分支。**畸形行（BDD-9）**：上述每一层 `isinstance` 守卫 + 顶层 `try/except`；坏行
`continue` + `skipped` 计数 + stderr 一行（照 `ClaudeCodeAdapter` line 159-162）。

**子决策 a — `tool` 取值**

| # | 方案 | 权衡 |
|---|---|---|
| A | **常量 `"exec"`** | BDD-4 只要"非空字符串"；detect 引擎视 `tool` 为不透明（仅进 event id 组合 + 展示）；Codex 实际执行体恒为沙箱 shell，`"exec"` 与 Codex 自身工具名（`tools.exec_command`）一致；无畸形数组边界 |
| B | `os.path.basename(item.command[0])`（→ `"bash"`）| 更具信息量 | `item.command` 空 / 首元素非路径 → 需兜底；`DSHAdapter` 的 `tool` 来自 `call_data.name`（每 call 有名），Codex 的 `CommandExecution` item **无**等价 per-call 工具名字段 → 常量才是自然对应 |

**定论：a=A（常量 `"exec"`）**。

**子决策 b — `command` 拼接**

| # | 方案 | 权衡 |
|---|---|---|
| A | **`shlex.join(item.command)`** | stdlib、确定性、不假设 `-lc` 包裹形态；与 `--json` 实时流的字符串形（`"/bin/bash -lc 'echo hi'"`，P1 §4.5）一致；BDD-4「含 `echo hi`」满足（`'echo hi'` 含子串）|
| B | `" ".join(item.command)` | 更短 | 丢引号 → `echo hi` 无界，歧义 |
| C | `item.command[-1]`（末元素 = 真正命令文本）| 最贴近"人眼中的命令"、SPIN 去重语义最准 | 依赖 `["/bin/bash","-lc","<text>"]` 三元形；非此形（如直接 `["ls","-la"]`）截取错 |

**定论：b=A（`shlex.join`）**，元素逐个 `str()` 强转，`item.command` 非 list → `command=""`。
（C 的 SPIN 精度优势不足以抵消形态假设风险；A 已保留命令文本子串，detect 的 `(command, exit,
output_hash)` 组合去重仍有效。）

**子决策 c — `exit_signal` 留档形态**

| # | 方案 | 权衡 |
|---|---|---|
| A | **完成有 exit_code → `f"exit_code={n}"`；完成无 → `item.status`；pending → `"pending"`** | 与 `ClaudeCode`(`"Exit code N"`)/`DSH`(`"Error:"`/`"pending"`) 的"原始形态留档"惯例同构；BDD-4/BDD-6 均满足 |
| B | 恒取 `item.status`（`"completed"`/`"in_progress"`）| 更统一 | BDD-6 要求 pending `exit_signal == "pending"` 精确等值 → 需特判，B 不满足 |

**定论：c=A**。

**exit（BDD-5）**：`item.exit_code` 是数字 → `exit = n if isinstance(n, int) and not isinstance(n, bool) else None`。
失败命令 `exit_code==2` 如实映射为 `2`，**不回落 None**（P0_STALE 已修正，Codex 比 Claude/DSH 更干净）。

**pending（BDD-6）**：维护 `started_ids`（见过 `item_started`/`item_updated` 的 `item.id`）与 `completed_ids`；
`item_completed` 且 `status != "completed"` 直接产出 pending 记录；结束时对 `started_ids - completed_ids`
各补一条 `exit=None / ts_end=None / exit_signal="pending"` 记录（照 `DSHAdapter` line 556-560）。
已完成记录不受影响。

### 设计点 3 —— `session_id` 取法

**候选**

| # | 方案 | 主会话值 | 子会话值 | 权衡 |
|---|---|---|---|---|
| A | **`os.path.basename(session_path)`**（完整 `rollout-<ts>-<uuid>.jsonl`）| 该文件名 | **子文件名**（含子自身 uuid）| 照搬 `ClaudeCodeAdapter`(line 141)/`DSHAdapter`(line 499)；basename **即**定位符（BDD-10「可定位回该会话文件」最强满足）；`read_commands` 热路径无额外首行读；不依赖 `session_meta` 良构 |
| B | `session_meta.id`（读首行 `payload.id`）| 父 id（=`session_id`）| 子自身 id | 满足 BDD-12，但 `read_commands` 需多读/解析首行（多一处失败面）；"可定位回文件"需 id→文件反查，非直接 |
| C | 混合：优先 `session_meta.id`，坏则 basename | — | — | 两条码路，复杂度不划算 |

**定论：A（`os.path.basename(session_path)`，保留完整文件名）**。理由：
1. **`follows_existing_pattern`**——两个 `.jsonl` 同族适配器逐字如此。
2. **BDD-10**：basename 是文件的直接标识，"非空 + 可定位"无争议。
3. **BDD-12**：minimal_validation 证实子会话 rollout 文件名含**子自身** uuid（`rollout-2026-09-08T21-02-03-01a0811c-80c6-...jsonl`，其中 `01a0811c-80c6-...` = `session_meta.id`；而 `session_meta.session_id` = 父 `01a0811c-6076-...`）。取 basename 天然指向子会话自身，**绕开** `session_meta` 里 `id`/`session_id` 同名字段陷阱——**明确不取 `payload.session_id`**（那是父 id）。
4. 保留完整 basename（不剥到裸 uuid）：与同族一致，`ts+uuid` 比裸 uuid 更可定位。

### 设计点 4 —— 截断信号形态（P5 V4 前兜底）

**候选**

| # | 方案 | 权衡 |
|---|---|---|
| A | **双信号（bool 键集 ∪ 文本标记集，任一命中 → True），常量化收敛面** | 遵 SUGGEST ③ / BDD-7 Given；与 `DSHAdapter._detect_truncated`(line 468-496) 结构对齐，可并排评审；V4 收敛 = 改 1 method + 2 常量 |
| B | 单信号（只信 `item` 上显式 bool 字段）| 误报少 | 形态 `[未实测]`，若真机是文本-only → 漏判 → 截断输出参与哈希 → 误判 SPIN（违反 BDD-17）。太乐观 |
| C | 单信号（只扫输出文本标记）| — | 命令合法回显 "output truncated" → 误判 → `output_hash` 丢失 → 削弱 SPIN 检测 |

**定论：A**。落地形态：

- 模块级常量（紧挨 class 上方，带 `# P5 V4：实测后按 P1 §4.1.2 收敛此处` 注释锚）：
  - `_CODEX_TRUNC_BOOL_KEYS = ("truncated", "output_truncated", "is_truncated")` —— 在 `item` dict 上取，`isinstance(v, bool) and v`
  - `_CODEX_TRUNC_TEXT_MARKERS = ("[output truncated]", "output truncated", "tokens truncated", "[truncated]")` —— 对 `item.aggregated_output` / `item.formatted_output` 小写子串匹配
- `@classmethod _detect_truncated(cls, item) -> bool`：非 dict → `False`；先查 bool 键集，再查文本标记集；任一命中即 `True`（逻辑与 `DSHAdapter._detect_truncated` 同构）。
- **P5 V4 收敛接口**：实测拿到真形态后，**只改** `_detect_truncated` 方法体 + 上述 2 个常量，`read_commands`/`_build_record`/契约不动。
- **IR 铁律**：`_build_record` 中 `output_hash = None if truncated else _sha1_hex(...)`，`truncated=True ⇒ output_hash=None` **无条件**，不因形态未定放宽（BDD-7）。

### 设计点 5 —— 子会话判定 + `list_sessions` 实现

**遍历骨架**（`follows_existing_pattern`，1 候选）：`os.walk` + 收集
`name.startswith("rollout-") and name.endswith(".jsonl")`，照 `DSHAdapter.list_sessions`(line 409-416)。
minimal_validation 证实父子 rollout 同在 `YYYY/MM/DD/` 扁平目录 → `os.walk` **天然同时枚举父与子**，
**不存在** Claude Code/DSH「读主文件漏子记录」问题（Codex 子会话本就是独立文件）→ **无需单独的
子会话发现代码**。BDD-3「子会话不被遗漏」由此满足；`list_sessions` 不需要**区分**父/子（如需，
判据 = `session_meta.thread_source=="subagent"` 或 `parent_thread_id` 存在，比照 DSH `delegationDepth>0`）。

**遍历根目录**（有真实取舍，3 候选）：

| # | 方案 | 权衡 |
|---|---|---|
| A | 固定 `os.path.expanduser("~/.codex/sessions")`，忽略 `cwd` | 贴合 Codex「home 下 UTC 日期分层、非 cwd 分层」事实 | BDD-2/BDD-3 传临时树根 → 需测试特判，破坏与同族签名语义一致性 |
| B | **`cwd` truthy → walk `cwd`；否则 fallback `~/.codex/sessions`** | 与 `ClaudeCodeAdapter`/`DSHAdapter` 的「`cwd` = 待遍历根」语义一致（BDD-2/3 直接传树根可跑）；生产调用方（RM-AG0060）传 `None` → 命中真实固定目录 | 多一个 fallback 分支（一行）|
| C | `os.path.join(cwd, ".codex/sessions")` | 类比"每项目 codex 目录" | Codex 无每项目 session 目录 → 生产下找不到文件，模型错 |

**定论：B**。`root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`。理由：BDD-2/BDD-3
要求 `cwd` 参数是诚实的遍历根（与同族一致、可测）；生产调用方不关心时传空 → 适配器落到真实
Codex home——这是 Codex 与 cwd 分层同族**唯一合理差异**，用 fallback 编码此事实而不破坏共享签名。

- **过滤**：`startswith("rollout-")` **且** `.endswith(".jsonl")`（排除 `.jsonl.zstd` 及非 rollout `.jsonl`）。
- **排序**：`sorted()` 按路径字符串（文件名内嵌 ISO8601 秒精度时间戳 → 字典序 = 时间序），照
  `DSHAdapter` 的 `sorted(names)`；**不用 mtime**（`stat()` 非确定性、fixture 不稳）。
- **返回**：`os.path.join(root, name)` 绝对路径 list（root 为绝对路径时结果即绝对；测试传 `str(tmp_path)` 亦绝对）。

---

## 6. SELF-GATE 预告（下游既定要求，P2 不自做）

- **P4**（改 `agate-cmdstream-adapters.py` + `agate/tests/`）、**P7**（改 `agate/platform-notes.md` +
  `agate/SETUP.md`）均触发 SELF-GATE：commit message 须含 `self-gate-review:` 路径 或
  `self-gate-skip:` 理由（`commit-msg-self-gate.sh` hook 检查）。
- **P7** 派 protocol-alignment-review（A1-A6 清单），产出 `agent != main`；`check-protocol-consistency.py
  --strict-errors-only` 记录为 0 ERROR（BDD-20 / BDD-28）。

---

## 7. gate_commands（P2 固化，后续阶段不得改）

```yaml
gate_commands:
  P3: "python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py agate/tests/unit/test_agate_cmdstream_detect.py -q"
  P5: "python3 -m pytest agate/tests/unit/ -q --tb=no"
  P5_timeout_seconds: 120
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_consistency_timeout_seconds: 120
  P5_shellcheck: "shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh"
  P5_shellcheck_timeout_seconds: 60
```

- **`P3`**：测试运行器（供 `check-tdd-red.py` 精确键 `key=="P3"` 读取），范围锁定本任务两测试文件以加速红灯确认。
- **`P5`**：全量单元测试紧凑输出（BDD-18 回归底线）。
- **`P5_consistency`**：⚠️ **worktree 自己的脚本路径**（非 `~/.agate`）——检查对象是 worktree 里改的 `platform-notes.md` / `SETUP.md`（BDD-20，AGENTS.md line 54）。`--strict-errors-only`（仅 ERROR 判失败，DEBT0012）。
- **`P5_shellcheck`**：本任务不改 `.sh`，作结构性回归（3 个 hook 薄壳）。可选，非阻塞语义参照既有。
- **不声明 `P3_xxx` 检测键**（P2 卡禁令 BDD-6）；**不用 `&&` 串联**（每校验独立 key）；
  **`ui_affected: false` → 无 `P5_e2e` / 无 `P3_e2e`**（新增测试全落单元层，非 E2E）。

---

## 8. files_to_read（P4 implementer 上下文地图）

**P4 必读**：

```yaml
files_to_read:
  - path: agate/scripts/agate-cmdstream-adapters.py:391-627
    why: DSHAdapter 是 CodexAdapter 近亲——probe/list_sessions 结构、_detect_truncated 双信号(468-496)、
         未结束 call 补记录(556-560)、_build_record(565-618)；_sha1_hex(68) 助手；ADAPTERS 字典(623-627) 加一行
  - path: agate/scripts/agate-cmdstream-ir.py:31-44
    why: CommandRecord 十字段 dataclass + 类型契约（只读，零改动；映射规则见 P2 §4.2）
  - path: agate/tests/unit/test_agate_cmdstream_adapters.py:294-342
    why: test_bdd_6_detect_consumes_registry_zero_change(:317) 精确断言改包含式；
         test_bdd_7_fixture_sanitized(:326-342) 脱敏清单加 codex fixture；既有 test_bdd_2~5 单测范式
  - path: agate/tests/fixtures/cmdstream/dsh-session.jsonl
    why: fixture 结构 + 脱敏约定（demo 前缀 / 无真实路径）范式，照此建 codex-session.jsonl
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md
    why: §4 spike 实测事实（§4.1 事件形态 / §4.1.1 exit_code / §4.2 子会话 / §4.5 实时流对比）+ §6 BDD-1~21
  - path: agate/tests/unit/test_agate_cmdstream_detect.py:300-373
    why: 三态确定性试验范式（_run_detect / _ev 虚拟时钟）+ test_bdd_24 负向断言(:371) 可选加 "codex"
```

**P7 参考**（协议文档阶段）：

```yaml
  - path: agate/platform-notes.md:43-70
    why: Codex 章「待补充」(43-45) + 既有 Codex 列 & max_depth=1 注记(53-70) 交叉引用面；DSH 章(176+) 作新兴平台文档范式
  - path: agate/SETUP.md:144-175
    why: DSH 小节结构范式（安装 / 登录 / 版本敏感提示），照此建 Codex 小节
```

---

## 9. env_constraints（确认 / 细化 P0-brief，不弱化）

```yaml
env_constraints:
  debug_env: "系统 python3（/usr/bin/python3）跑 pytest + pyyaml；ruff 用 ~/.venvs/agate-dev/bin/ruff；
    codex-cli 0.153.4 + ChatGPT 登录（本机已就绪，真机验证清单 V1-V7 本机可做）。派发类工具用 ~/.agate 稳定版。"
  isolation_check: "只读访问 ~/.codex/sessions/ 用户目录（不写、不派新 Codex 会话去污染），开发全程不接触生产；
    fixture 内容脱敏（demo 前缀 / 无 /home/kity / 无密钥 / 无真实会话 uuid），纳入 test_bdd_7_fixture_sanitized 校验。
    check-protocol-consistency.py 必须用 worktree 自己的脚本路径（非 ~/.agate）。"
  self_gate: "P4 改 adapters.py + tests/、P7 改 platform-notes.md + SETUP.md → 触发 SELF-GATE：
    commit message 须含 self-gate-review: 或 self-gate-skip:；P7 派 protocol-alignment-review（A1-A6），agent != main。"
  verification_env: "API-key 账号 model 阵容项（P1 §7 V8）本机不可得 → 登记『待有该环境时补』，不阻塞
    （verification_env_budget: 止损轮次 2，主 Agent 在 P5/P6 dispatch-context 记录）。"
```

> 边界提醒：`env_constraints` 是声明性字段，不被自动执行。真正强制的是 §7 `gate_commands`
> （`P5_consistency` 跑 worktree 脚本）+ P4/P7 卡片 SELF-GATE checklist（commit-msg hook）。

---

## 10. minimal_validation（对真实 rollout JSONL 已执行）

```yaml
minimal_validation:
  assumption: "真实 Codex rollout JSONL 的 CommandExecution item 具备 command(数组)/exit_code(数字)/status
    + payload.started_at_ms/completed_at_ms(epoch ms)；session_meta 首行含 id/session_id/thread_source，
    主会话 id==session_id、子会话 id=自身而 session_id=父。"
  method: "对 ~/.codex/sessions/2026/09/{08,09}/rollout-*.jsonl（23 文件）跑 <20 行 python 扫描字段结构；
    主会话 1 个 + spawn_agent 子会话 2 个 各验一次（命令加 timeout 60s）。"
  result: confirmed
  observations:
    - "23 rollout 文件；行封套键恒为 {ordinal,payload,timestamp,type}；每文件首行 type=='session_meta'。"
    - "CommandExecution item_completed：payload 键 {completed_at_ms,item,started_at_ms,thread_id,turn_id,type}；
      started_at_ms/completed_at_ms 为 epoch ms int（样例 1788868081170 / 1788868081171）。"
    - "item 键 {aggregated_output,command,cwd,duration,exit_code,formatted_output,id,parsed_cmd,process_id,
      source,status,stderr,stdout,type}；command==['/bin/bash','-lc','sed -n ...']；exit_code==0(int)；
      status=='completed'；aggregated_output 为 str（样本最长 5442 字符，无截断标记出现 → 截断形态仍 [未实测]，走设计点 4 DSH 兜底）。"
    - "主会话 session_meta.payload：id==session_id==01a080d7-…；thread_source=='user'；cli_version=='0.153.4'；originator=='codex-tui'。"
    - "子会话 session_meta.payload（2 样例）：id=子自身(01a0811c-80c6-… / 01a081d2-486c-…)；session_id=父(01a0811c-6076-… / 01a081d2-27fd-…)；
      thread_source=='subagent'；含 parent_thread_id(=父)/forked_from_id(=父)/source.subagent.thread_spawn.depth==1/multi_agent_version=='v2'/originator=='codex_exec'
      → 证实设计点 3『取 basename 而非 payload.session_id』（后者对子会话是父 id）。"
    - "apply_patch → 派生 FileChange item；web__run → 派生 Extension item；均非 CommandExecution
      → 设计点 2 源过滤 item.type=='CommandExecution' 天然排除 → BDD-8 由构造保证。"
    - "未观察到 item_started 的 CommandExecution（样本命令均秒级完成）→ 未结束/pending 的 rollout 形态
      仍 [未实测]，设计点 2 按 status!='completed' ∪ 『有 item_started 无 item_completed』双判据，写成 P5 易收敛形式。"
  internal_deps: "复用 agate-cmdstream-adapters.py 的 _sha1_hex(line 68) / _iso8601_to_epoch_ms(line 73，仅 fallback)；
    CommandRecord dataclass（agate-cmdstream-ir.py:31-44）；detect() 消费 IR 的字段（platform/session_id/tool/
    command/ts_start/ts_end/exit/output_hash/truncated）——均不改。"
```

---

## 11. dispatch_plan（后续编排机器声明）

`dispatch_plan: {mode: static-batch, parallel_limit: 2, batches: [{id: adapter-core, complexity: medium}, {id: protocol-docs, complexity: low}]}`

| 批次 | 子任务（P1 §9 / dispatch-context 约束 5）| 阶段 | complexity | 说明 |
|---|---|---|---|---|
| `adapter-core` | ① `CodexAdapter` class + `ADAPTERS` 一行 ② 新单测（BDD-1~17 解析 + 三态试验）③ fixture（`codex-session.jsonl` + 子会话片段）⑥ `test_bdd_6`(:317) 断言改包含式 | P3（红）→ P4（绿）| medium | **强耦合、不可拆**：TDD 先红后绿，测试/fixture/实现/断言修正必须同批同上下文。输入文件 5 个但 implementer 按 §8 行号范围选读 |
| `protocol-docs` | ④ `platform-notes.md` Codex 章 ⑤ `SETUP.md` Codex 小节 | P7 | low | 文档面，独立批；与 P5/P6 真机验证记录（V1-V7 结论）合并回写；触发 SELF-GATE → 派 protocol-alignment-review |

- `mode: static-batch`——两批边界清晰（代码/测试 vs 协议文档），无需侦察。
- `parallel_limit: 2`；批数 2 ≤ 2。两批不共享改动文件（`adapter-core` 动 `agate/scripts/` + `agate/tests/`；`protocol-docs` 动 `agate/*.md`）→ 无跨批重复改同一文件。
- `protocol-docs` 实际在 P7 执行（协议文档阶段），非与 `adapter-core` 物理并行；此处按 dispatch-context「子任务面」口径声明编排结构。
- 无 high 复杂度维度 → 不强制更细拆分。

---

## 12. 范围外发现

**无**。P2 设计全程落在 P0 四交付面 / P1 §5 范围锁定内：`CommandRecord` 十字段可干净映射 Codex
语义（`exit` 直接取 `item.exit_code`）、检测引擎 / 阈值 / IR / 既有三适配器均无需改动。未触发 P1 §5
逃生阀（"必须扩 IR / 改检测引擎 / 改阈值 / 动既有适配器 → 立即停下报告主 Agent"）。
