---
phase: P2
task_id: TAG0033
type: review
parent: P2-design.md
trace_id: TAG0033-P2-review-20260909
status: approved
created: 2026-09-09
agent: plan-eng-review
---

# P2-review — TAG0033 Codex 命令流适配器 + 平台接入（独立工程评审）

> 受评对象：`P2-design.md`（architect，452 行，`candidate_count: 3`，`dispatch_plan: static-batch`，
> `follows_existing_pattern: [agate/scripts/agate-cmdstream-adapters.py]`）
> 角色：`plan-eng-review`（`agent != main`）。C8 映射 domains=[backend] + risk_level=medium →
> 单评审角色，无组长汇总，本文件即 `P2-review.md`。
> 评审方式：不轻信 architect 自述——关键 grep / 读既有适配器与 detect/ir/gate 脚本 / 跑 `shlex.join`
> 自行核实（证据见每维度「独立核实」小节 + `P2-progress.md` 落盘）。

`[PROD_NOT_TOUCHED]`

## 结论

**status: approved**

零改动硬约束在独立核实下守住，8 项必核维度全部通过，方案已达 implementer 无需步骤计划即可自主实现的
就绪度。无 BLOCKER。留 4 条非阻塞观察（见文末），建议 P4 采纳但不阻断推进。

---

## 逐维度评审结论

### 维度 1 —— 零改动硬约束是否守住（P0 核心约束 2 / P1 §5 / BDD-21）

**结论：PASS（独立核实确认 architect「无范围外发现」属实）。**

`P2-design.md` §2.2「不改什么」显式且完整列出四项，每项配理由：
- `agate-cmdstream-detect.py` 检测引擎 + CLI（§2.2 第 1 行）
- `agate-cmdstream-ir.py` 的 `CommandRecord` dataclass 十字段（§2.2 第 2 行）
- `agate-cmdstream-detect.py` 阈值常量 `CALL_ALERT_FALLBACK` 等 / RM-AG0055 §3.4.3（§2.2 第 3 行）
- `ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` 三 class 体（§2.2 第 4 行）

**独立核实：**
- `agate-cmdstream-detect.py:96` `ADAPTERS = _load_adapters().ADAPTERS`；`:308/:312/:317`
  `choices=sorted(ADAPTERS.keys())`；`:328` `adapter = ADAPTERS[args.platform]`——全部动态取自注册表，
  无硬编码三键。加 `"codex": CodexAdapter()` 一行即自动纳入三个 CLI 子命令的 `choices`。detect.py 零改动成立。
- `detect(events, now, config)`（`agate-cmdstream-detect.py:161+`）消费的是 CLI 转换层（`:340-370`）从
  `CommandRecord` 派生的事件 dict（`{ts,kind,id,cmd,exit,out,truncated,expected}`），完全平台无关。
  CodexAdapter 只要产出合规 `CommandRecord`，detect 零改动消费。
- `agate-cmdstream-ir.py:31-44` `CommandRecord` 十字段足以表达 Codex（核 §4.2 映射表）：`exit` 直取
  `item.exit_code`（int，比 Claude/DSH 的文本前缀解析更干净）；`ts_start/ts_end` 直取
  `payload.started_at_ms/completed_at_ms`（epoch ms int）；`truncated` 取双信号。无需扩 schema。
- `detect()` 对 Codex 记录零改动可行：CLI `read-commands` / `detect` 子命令的 `--platform`/positional
  `platform` 均 `choices=sorted(ADAPTERS.keys())`——加第四键零改动生效（BDD-21 / P1 §3 S1 确认）。
- **加第四键对既有测试的影响面**：grep 全 `agate/tests/` 树，唯一会被第四键打破的精确等值断言 =
  `test_agate_cmdstream_adapters.py:317`（`test_bdd_6_detect_consumes_registry_zero_change` 的
  `assert registered == {"claude-code","opencode","dsh"}`）。`:298` 已是 `set(...) >= {...}` 包含式；
  `test_agate_cmdstream_detect.py:371` 是负向断言（断言输出不含平台词），加第四键不打破。
  `:317` 的修正由 BDD-19 覆盖、落在 P3 锁定的两测试文件之一内、语义（检测引擎零改动消费注册表）不变。

未发现任何设计点实际需要动这四项。architect 「未触发 P1 §5 逃生阀」的报告经独立核实成立。

### 维度 2 —— 5 个设计点的方案取舍是否成立（§5）

**结论：PASS（含 4 条非阻塞观察，见文末 N1-N4）。**

**设计点 1 —— probe（§5 设计点 1，定论 B）**
- basename 正则（`rollout-` 前缀 + `.jsonl` 后缀 + 排除 `.zstd`）+ 首行 `readline()` sniff
  `type=="session_meta"` 且 payload 含 codex 标记（`cli_version`/`originator`/`id`）。
- 只读一行足以区分：`agate/tests/fixtures/cmdstream/claude-code-session.jsonl` 首行为
  `{"type":"tool_use",...}`——无 `session_meta`。minimal_validation 证实 23 个真实 rollout 首行恒为
  `session_meta`（含 `cli_version=="0.153.4"`）。判据成立。
- 路径异常 / 首行非 JSON → 返回 `False` 不抛：`DSHAdapter.probe`（`agate-cmdstream-adapters.py:406-407`）
  是纯 `endswith` 无 I/O，CodexAdapter 因引入 `open`/`readline` 需自带 try/except——§5 已明确要求
  「绝不抛异常」，与既有适配器「probe 不抛」的隐含契约一致。
- **BDD-8「由构造天然排除」是否够稳**：够稳。独立核实——`probe` 在 `agate/scripts/` 下**未被任何代码调用**
  （仅 BDD 隔离测试用；CLI 走显式 `--platform`）。因此与 `ClaudeCodeAdapter.probe`（对任意 `.jsonl`
  返回 `True`）的重叠是**无害**的，不构成自动派发歧义。§5 候选 A/B/C 权衡与 R4 缓解对此有交代。

**设计点 2 —— 事件→IR 映射（§5 设计点 2）**
- `command = shlex.join(item.command)`：**已自行跑**
  `python3 -c "import shlex; print(shlex.join(['/bin/bash','-lc','echo hi']))"` →
  `/bin/bash -lc 'echo hi'`；`"echo hi" in "/bin/bash -lc 'echo hi'"` → **True**。BDD-4「`command` 含
  `"echo hi"`」判据满足——`shlex.join` 给内层加的单引号不破坏子串「包含」判定（`'echo hi'` 内含
  `echo hi`）。子决策 b=A 成立。元素逐个 `str()` 强转 + 非 list → `""` 的兜底与 `DSHAdapter._build_record`
  的 `str(command)` 风格一致。
- `tool = "exec"` 常量（子决策 a=A）：BDD-4 只要「非空字符串」；`DSHAdapter` 的 `tool` 来自 per-call
  `call_data.name`，Codex `CommandExecution` item 无等价 per-call 工具名字段——常量是自然对应。成立。
- `exit = item.exit_code`（BDD-5）：`isinstance(n, int) and not isinstance(n, bool)` 守卫，失败命令
  `exit_code==2` 如实映射不回落 None。与 `agate-cmdstream-ir.py:79` 的 `_is_int` 契约一致。P0_STALE ①
  已在 P1 §4.1.1 修正，此处落实无误。
- `exit_signal`（子决策 c=A）：完成有 exit_code → `f"exit_code={n}"`；完成无 → `item.status`；pending →
  `"pending"`。与 `ClaudeCodeAdapter`（`"Exit code N"`）/ `DSHAdapter`（`"Error:"`/`"pending"`）的
  「原始形态留档」惯例同构；BDD-6「pending 的 `exit_signal == "pending"` 精确等值」由特判满足。
- **BDD-8 非 shell 工具事件**：源过滤是 `it.get("type")=="CommandExecution"`——一个**单类型正向白名单**
  （不是黑名单），任何其它 item 类型（`FileChange`/`Extension`/未来新类型）一律不进映射。且
  `custom_tool_call`（`apply_patch`/`web__run`）是 `type=="response_item"`，在**第一层**
  `obj.get("type")=="event_msg"` 就被挡掉。双重保护，**不需要**再加显式 `item.type` 白名单分支。
  minimal_validation 已证 `apply_patch`→`FileChange` item、`web__run`→`Extension` item。稳。
- **BDD-9 畸形行**：§5 源过滤逐层 `isinstance` 守卫（`json.loads`/`ValueError` → 非 JSON；
  `isinstance(obj, dict)` → 非 dict / JSON 数组；`isinstance(p, dict)` → 缺 payload；
  `isinstance(it, dict)`）+ 顶层 try/except，粒度覆盖 §2.1 fixture 列的三类坏行。与
  `ClaudeCodeAdapter.read_commands`（`:150-162`）的 `skipped` 计数 + stderr 一行范式一致。

**设计点 3 —— session_id = `os.path.basename(session_path)`（§5 设计点 3，定论 A）**
- 独立核实：`ClaudeCodeAdapter.read_commands:141` `session_id = os.path.basename(session_path)`、
  `DSHAdapter.read_commands:499` 同——两个 `.jsonl` 同族适配器逐字如此。`follows_existing_pattern` 成立。
- BDD-10（同文件所有记录 session_id 一致）：basename 天然一致 ✔。
- BDD-12（子会话 session_id 指向子会话自身）：minimal_validation 证实子 rollout 文件名含**子自身** uuid，
  而 `session_meta.session_id` 对子会话 = **父** id（陷阱字段）。取 basename 绕开该陷阱。
- 「明确不取 `payload.session_id`」是否落到 §5 设计文字：**是**——§5 设计点 3 定论第 3 点
  （"**明确不取 `payload.session_id`**（那是父 id）"）+ §4.2 映射表 `session_id` 行备注 + §2.3 R5
  三处均写明，非仅 dispatch-context 口头。

**设计点 4 —— 截断双信号（§5 设计点 4，定论 A）**
- 结构对齐 `DSHAdapter._detect_truncated`（`agate-cmdstream-adapters.py:468-496`）：bool 键集 ∪
  文本标记集，任一命中 → `True`；非 dict → `False`。可并排评审。
- `_CODEX_TRUNC_BOOL_KEYS` / `_CODEX_TRUNC_TEXT_MARKERS` 无 minimal_validation 依据（P2 诚实标
  「未捕获截断样例」，最长 output 5442 字符无标记）——对 V4 未定形态采保守双信号是正确取舍，比单信号
  （候选 B/C）安全。
- 收敛面：1 个 classmethod + 2 个模块常量 + `# P5 V4 收敛锚` 注释，P5 实测后定向改这三处，不牵动
  `read_commands`/`_build_record`/契约。收敛面确实够小。
- `truncated=True ⇒ output_hash=None` 无条件强制（§5 + §4.2 + R2）。独立核实其必要性：
  `agate-cmdstream-detect.py` 无效重复检测（`:218-221`）`if r.get("truncated"): continue` 跳过截断记录，
  **同时** CLI 转换层（`:363`）传 `"out": r.output_hash`——若 `output_hash` 非 None 且 `truncated` 标志
  未随记录传播，全 None 的 `out` 组合仍可能坍缩触发 SPIN。故「flag 传播」与「output_hash=None」两者都
  必要，§5 两者都处理，BDD-17 满足。

**设计点 5 —— list_sessions（§5 设计点 5，定论 B）**
- 遍历骨架 `os.walk` + `name.startswith("rollout-") and name.endswith(".jsonl")`——照
  `DSHAdapter.list_sessions:409-416`。父子 rollout 同在扁平 `YYYY/MM/DD/` 目录，`os.walk` 天然同时枚举
  →「无需单独子会话发现代码」成立（BDD-3）。与 Claude Code/DSH「读主文件漏子记录」不同。
- **`cwd` 参数语义是否与既有 `ClaudeCodeAdapter`/`DSHAdapter` 一致**：既有两适配器把 `cwd` **直接**喂给
  `os.walk(cwd)`，无 `expanduser` fallback（独立核实 `agate-cmdstream-adapters.py:134` / `:412`）。CLI
  `list-sessions PLATFORM CWD` 的 `cwd` 是**必填位置参数**，恒为字符串。设计点 5 候选 B 是
  `root = cwd if cwd else expanduser("~/.codex/sessions")`——**当 `cwd` 有值时（CLI + 全部 BDD 测试）
  语义与既有适配器完全一致**；fallback 分支只在 `cwd` 为假值时触发，是**新增**而非**改变**。
  Codex 按 UTC 日期分层、不按 cwd 分层——传 `cwd` 仍有意义（BDD-2/BDD-3 需要 `cwd` 是诚实的遍历根，
  可测）。fallback 的「生产调用方 RM-AG0060 传 None」依据落在尚未构建的组件上——记为**非阻塞观察 N1**。
- **`sorted()` 按路径字符串是否等价于按时间排序**：Codex 文件名内嵌零填充 `YYYY/MM/DD/` +
  ISO8601 秒精度时间戳（`rollout-2026-09-08T21-01-55-<uuid>.jsonl`）——字典序 = 时间序，跨月
  （`09/30` < `10/01`）/ 跨年（`2026` < `2027`）单调。同秒内 uuid tiebreak 为确定性非时序（可接受，
  DSH 同）。**注**：§5 文字称「照 `DSHAdapter` 的 `sorted(names)`」，但 DSHAdapter 是在 `os.walk` 内
  **逐目录**对文件名排序，非全局路径排序；若 P4 实现为全局 `sorted()` 全路径（更确定，更好），与文字
  的「照 DSHAdapter」表述略不符——非阻塞观察 N2，不影响任何 BDD（BDD-2/3 是成员判定，与顺序无关）。
- 过滤 `.endswith(".jsonl")` 排除 `.jsonl.zstd`、返回 `os.path.join(root, name)` 绝对路径——成立。

### 维度 3 —— 影响面梳理节完整性（§2）

**结论：PASS。**
- 三部分齐：§2.1 改什么（逐文件 + 落到函数/小节 + 关联 BDD 编号）/ §2.2 不改什么（8 行，每行配理由）/
  §2.3 风险（R1-R10，每条配缓解）。
- 位置：§2 在候选方案 §5 **之前**。✔
- 客观证据：§2.1 末尾「grep 客观证据」列 detect.py 三处动态取法 + test 文件 `:298`/`:317`/`:371` 现状；
  §2.2 逐行引 grep / 消费方代码 / CHECK 锚点口径——非凭印象。独立复核这些行号引用全部准确。
- §2.3 R3（pending 形态未实测）缓解：双判据（`item_completed` 且 `status!="completed"` ∪「有
  `item_started` 无 `item_completed`」）+ fixture 手造（BDD-6 Given 明确允许）+ 写成 P5 易替换形式 +
  detect CLI 已跳过 `ts_start is None` 记录（独立核实 `agate-cmdstream-detect.py:344-346`）——可执行。
- §2.3 R5（子会话 session_id 陷阱）缓解：`session_id = basename` + 明确不取 `payload.session_id` +
  §5 设计点 3 详述——可执行，且已落到设计正文（见维度 2 设计点 3）。

### 维度 4 —— gate_commands 契约（§7）

**结论：PASS。**
- **`P3` 为裸键**：独立核实 `agate/scripts/agate-read-gate-commands.py:104` `elif key == "P3":`（精确等值，
  非 `startswith`）；`check-tdd-red.py` 经 `_read_gate_commands` → `agate-read-gate-commands.py` 只收集
  精确键。§7 无 `P3_xxx` 检测键。合规（P2 卡禁令 BDD-6）。
- **`P3` 锁定两测试文件是否会漏该红的测试**：不会。本任务新测试全在
  `test_agate_cmdstream_adapters.py`（CodexAdapter 解析 BDD-1~12 + `test_bdd_6:317` 断言改包含式）与
  `test_agate_cmdstream_detect.py`（Codex 三态确定性试验 BDD-13~17）两文件内；grep 确认加第四键唯一
  打破的精确断言 `:317` 也在其一。锁定范围覆盖全部该红的测试。可接受。
- **无 `&&` 串联**：§7 每校验独立 key（`P3`/`P5`/`P5_consistency`/`P5_shellcheck`）。✔
- **`P5_consistency` 用 worktree 自己的脚本**：`python3 agate/scripts/check-protocol-consistency.py
  --strict-errors-only`——worktree 相对路径，非 `~/.agate`。AGENTS.md line 54「`check-protocol-consistency.py`
  必须用 worktree 自己的」要求满足。独立核实该脚本存在（`agate/scripts/check-protocol-consistency.py`）。
- **`ui_affected: false` → 无 `P5_e2e` / 无 `P3_e2e`**：新测试全落单元层（适配器解析单测 + 虚拟时钟
  确定性试验），无端到端。合规。
- **timeout 档位**：`P5_timeout_seconds: 120`（单元，与 `AGATE_TDD_TIMEOUT` 默认对齐）/
  `P5_consistency_timeout_seconds: 120` / `P5_shellcheck_timeout_seconds: 60`——档位合理。
- 附核：`P5_shellcheck` 三个 hook 目标文件（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` /
  `pre-push-gate.sh`）均存在，`shellcheck` 已装。`check-protocol-consistency.py`
  `AUTHORITATIVE_VALUE_ANCHORS`（`:1055`）只含 `retry-max`，与 platform-notes.md 能力矩阵无关；
  `platform-notes.md` / `SETUP.md` 在 `_MD14_WHOLE_FILE_EXEMPT`（`:1183-1185`）整文件豁免——
  §2.2「本任务不新增 CHECK / 锚点」「新章仍过 0 ERROR」经独立核实成立。

### 维度 5 —— dispatch_plan 合法性（§11 / frontmatter）

**结论：PASS。**
- `mode: static-batch` + `parallel_limit: 2` + `batches: [{adapter-core, medium}, {protocol-docs, low}]`。
- batches 数 2 ≤ `parallel_limit` 2。✔
- 每批含 `id` + `complexity` ∈ {low, medium, high}。✔
- `adapter-core`（class + `ADAPTERS` 一行 + 新单测 + fixture + `test_bdd_6:317` 断言改包含式）作 TDD
  同批不可拆——成立：TDD 先红后绿，测试 / fixture / 实现 / 断言修正必须同批同上下文（否则 `:317`
  红灯与新测试红灯分裂在不同 commit，`check-tdd-red.py` 判据混乱）。
- `protocol-docs`（platform-notes + SETUP）标 P7 执行——与 P1 §9 裁剪说明一致（P7 不可裁：SELF-GATE +
  协议文档变更 + protocol-alignment-review）。§11 也注明「实际在 P7 执行，非与 adapter-core 物理并行」。
- 两批不共享改动文件（`adapter-core` 动 `agate/scripts/` + `agate/tests/`；`protocol-docs` 动
  `agate/*.md`）——无跨批重复改同一文件。

### 维度 6 —— minimal_validation 充分性（§10）

**结论：PASS。**
- 对真实 `~/.codex/sessions/` 23 个 rollout 文件跑 <20 行 python，`result: confirmed`。
- 关键断言逐条核（与 §4.2 / §5 设计一致）：
  - 行封套键 `{ordinal,payload,timestamp,type}`、每文件首行 `type=="session_meta"` ✔
  - `CommandExecution` item_completed：`payload` 含 `started_at_ms`/`completed_at_ms`（epoch ms int）；
    `item` 含 `command`（数组 `["/bin/bash","-lc",...]`）/ `exit_code`（int 0）/ `status`（`"completed"`）/
    `aggregated_output`（str）✔
  - 主会话 `id==session_id`；子会话（2 样例）`id`=子自身、`session_id`=父、`thread_source=="subagent"`、
    含 `parent_thread_id`/`forked_from_id`/`thread_spawn.depth==1`/`multi_agent_version=="v2"` ✔
    → 证实设计点 3「取 basename 不取 payload.session_id」
  - `apply_patch`→`FileChange` item / `web__run`→`Extension` item（非 CommandExecution）✔ → BDD-8 由构造保证
- **未捕获两项诚实标注**：① 截断样例（最长 output 5442 字符、无标记）标 `[未实测]` → 设计点 4 走 DSH
  兜底 + P5 V4 收敛路径；② `item_started` CommandExecution（pending 形态）标 `[未实测]` → 设计点 2 走
  `status!="completed"` ∪「有 item_started 无 item_completed」双判据 + 写成 P5 易收敛形式。两项均给 P5
  收敛路径，诚实且充分。
- `internal_deps` 写明依赖 `_sha1_hex`(line 68) / `_iso8601_to_epoch_ms`(line 73, 仅 fallback) /
  `CommandRecord` dataclass / detect() 消费字段——均不改。满足角色 checklist「纯代码逻辑须写明依赖」
  的精神（本项实为「有外部系统依赖」，且验证确对真实 rollout 执行——treatment 正确）。

### 维度 7 —— out-of-scope（§3）

**结论：PASS。**
- `codex exec --json` 实时流源「不做 / 后置」与 P1 §8 SUGGEST ②、P1 §4.5 实测一致：实时流事件
  **不带 per-item 时间戳**，而 `detect()` 需 `ts_start`/`ts_end`（独立核实 `agate-cmdstream-detect.py`
  冻结判定全依赖事件 `ts`）。§3 列 out-of-scope 并给未来路径（另立任务 + 自造时间戳）。合理。
- §3 其它条目（Codex 作宿主平台 onboarding / RM-AG0060 配置路由 / `spawn_agent` 嵌套深度结论 /
  新增 gate 脚本）均与 P0 out-of-scope、P1 §5 一致。

### 维度 8 —— SELF-GATE 预告（§6）

**结论：PASS。**
- §6 点明 P4（改 `agate-cmdstream-adapters.py` + `agate/tests/`）、P7（改 `agate/platform-notes.md` +
  `agate/SETUP.md`）均触发 SELF-GATE；commit message 须含 `self-gate-review:` 路径 或
  `self-gate-skip:` 理由（`commit-msg-self-gate.sh` hook）。
- §6 + §11 点明 P7 派 protocol-alignment-review（A1-A6 清单），产出 `agent != main`；
  `check-protocol-consistency.py --strict-errors-only` 记 0 ERROR。与 BDD-28 / BDD-20 一致。
- §9 env_constraints `self_gate` 字段亦复述该链路。

---

## 非阻塞观察（建议 P4 采纳，不阻断推进）

| # | 位置 | 观察 | 建议 |
|---|---|---|---|
| N1 | §5 设计点 5 / 定论 B | `list_sessions` 的 `cwd if cwd else expanduser("~/.codex/sessions")` fallback 是既有 `ClaudeCodeAdapter`/`DSHAdapter` 所无（它们 `cwd` 直接喂 `os.walk`），依据「生产调用方 RM-AG0060 传 None」落在**尚未构建**的组件上。CLI 的 `cwd` 恒为必填字符串，全部 BDD 测试也传显式树根——fallback 分支目前无测试覆盖。 | P4 给 fallback 加一行注释标注为「前瞻性 affordance」，**或**在 P3 新单测里补一条 `cwd=None` / `cwd=""` 触发 fallback 的用例，避免其成为未测死代码。 |
| N2 | §5 设计点 5 排序段 | 文字称「照 `DSHAdapter` 的 `sorted(names)`」，但 `DSHAdapter.list_sessions` 是在 `os.walk` 内**逐目录**对文件名排序，非全局路径排序。若 P4 实现为全局 `sorted()` 全路径（更确定，实际更好），与「照 DSHAdapter」表述略不符。 | 纯文字精度问题，不影响任何 BDD（BDD-2/3 是成员判定）。P4 实现时取全局 `sorted()` 全路径即可，无需回改设计。 |
| N3 | §2.3 R7 / `test_bdd_7_fixture_sanitized` | 既有脱敏正则 `\b(?:ses\|msg\|prt\|call)_[0-9a-f]{26}\b` **不匹配** Codex 连字符 uuid（`01a0811c-6076-7a00-...`）。R7 判断「用 `demo` 前缀 uuid 即满足既有 `assert "demo" in text` + `assert not re.search(...)`，无需改正则」正确，但结果是 Codex fixture 的**自动脱敏覆盖弱于**其它三平台（只剩 `demo` 子串正向检查 + 路径/密钥检查）。 | R7 已把「补 Codex uuid 形态负向断言」列为「同批可做、非零改动违规」。建议 P4 **实际补上**（而非留作可选），把 Codex 连字符 uuid 形态纳入 `test_bdd_7` 负向断言。 |
| N4 | §4.2 `ts_start` 行 | 设计把 `ts_start=None` 作最后兜底（`payload.started_at_ms` 缺 + 首行 `timestamp` fallback 也缺），但 `agate-cmdstream-ir.py:39` 字段类型提示为 `ts_start: int`（无默认值）。 | 非问题：`from_dict` 的严格校验在直接构造 `CommandRecord(...)` 时不生效，`DSHAdapter._build_record`（`:590`）已同样对 `ts_start` 传 `None`；`detect` CLI（`:344-346`）显式跳过 `ts_start is None` 记录。与既有 DSH 行为一致，仅此记录备查。 |

---

## 锁定决策（本次评审确定下来的技术方向）

1. `ADAPTERS` 注册表键名 `"codex"`；`CodexAdapter` 实现 `probe`/`list_sessions`/`read_commands` +
   `_detect_truncated` classmethod + `_build_record` + 2 个模块级截断常量。检测引擎 / IR / 阈值 /
   既有三适配器零功能改动——**独立核实确认可行**。
2. `probe` = basename 正则 + 首行 sniff（定论 B）；`session_id` = `os.path.basename(session_path)`
   （定论 A，明确不取 `payload.session_id`）；`command` = `shlex.join(item.command)`（定论 b=A，
   BDD-4「含 `echo hi`」判据已自行验证满足）；`tool` = 常量 `"exec"`；`exit` = 直取 `item.exit_code`；
   截断 = 保守双信号（定论 A，P5 V4 收敛锚 = 1 method + 2 常量）；`list_sessions` root =
   `cwd if cwd else ~/.codex/sessions`（定论 B，fallback 见 N1）。
3. `gate_commands`：`P3` 裸键锁定两测试文件；`P5` 全量单元；`P5_consistency` 用 **worktree** 脚本
   `--strict-errors-only`；`P5_shellcheck` 三 hook 薄壳；无 `P3_xxx` / 无 `&&` / 无 `P5_e2e`。
4. `dispatch_plan`：`static-batch` / `parallel_limit: 2` / `adapter-core`(medium, TDD 不可拆) +
   `protocol-docs`(low, P7 执行)。
5. `codex exec --json` 实时流源 = out-of-scope（实时流不带 per-item 时间戳）。
6. P4/P7 触发 SELF-GATE，commit message 须留痕；P7 派 protocol-alignment-review（`agent != main`）。

---

## 测试缺口

无阻塞级测试缺口。两处建议补强（均可同批 / 不违反零改动）：
- N1：`list_sessions` 的 `cwd` 假值 fallback 分支无测试覆盖——建议 P3 补一条 `cwd=None`/`""` 用例。
- N3：`test_bdd_7_fixture_sanitized` 对 Codex 连字符 uuid 无形态负向断言——建议 P4 补上。

---

## 覆盖声明

- **已覆盖**：dispatch-context 8 项必核维度全部逐项给结论 + 证据（见「逐维度评审结论」1-8）。
- **未覆盖**：无。真机验证清单 V1-V8 的实机执行属 P5/P6 范畴，本评审只核 §10 minimal_validation
  的既有执行结果与 §7 out-of-scope / §3 的一致性，未重跑真机验证（符合 P2 评审边界）。
- 视觉能力：本任务 `domains: [backend]` / `ui_affected: false`，无视觉能力需求，无
  `[CAPABILITY_GAP]`。

`[PROD_NOT_TOUCHED]`
