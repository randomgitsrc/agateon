---
review_date: 2026-09-09
task_id: TAG0033
reviewer: protocol-alignment-review (agent≠main)
status: approved
change_summary: TAG0033 P4 adapter-core 批——`agate-cmdstream-adapters.py` 新增 `CodexAdapter`（+225，probe/list_sessions/read_commands + `_join_command`/`_detect_truncated`/`_build_record` + 2 模块常量 + `_codex_int_or_none`）+ `ADAPTERS` 加 `"codex"` 键 + `import shlex`；`test_agate_cmdstream_adapters.py` 1 行断言由精确等值改包含式。
files_changed: [agate/scripts/agate-cmdstream-adapters.py, agate/tests/unit/test_agate_cmdstream_adapters.py]
---

# 协议-脚本对齐审查 — TAG0033 Codex 命令流适配器（P4 SELF-GATE）

> 触发：`agate/scripts/*.py` 改动（SELF-GATE）。本审查为**独立上下文**，与并行的 C8 `review`（审实现正确性）分工——本报告只审**语义对齐**：协议文档契约 vs 脚本实现一致性、改动的文档传播、锚点表覆盖、ADR 一致性。
> 关键背景：文档分批是 P2 dispatch_plan 明确的 `static-batch` 两批——`adapter-core`（P4，代码+测试）/ `protocol-docs`（P7，`platform-notes.md` Codex 章 + `SETUP.md` Codex 小节，P1 §9 P7 不可裁）。「代码已加 `CodexAdapter`、`platform-notes.md` Codex 章仍为待补充」是**排期内**，不判 MISALIGNED。零改动（`agate-cmdstream-detect.py` / `CommandRecord` dataclass / 既有三适配器）是 P0-brief 核心约束 2 + P1 §5 的硬约束。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **NEEDS_HUMAN_REVIEW**（文档同步已排期 P7；非遗漏、非 MISALIGNED）|
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW**（A3a 连锁 ALIGNED；A3b 2 项待 P7/P8 回写）|
| A4 | 测试覆盖 | **ALIGNED**（全量 1383 passed / 6 failed[P7 预期红] / 2 skipped）|
| A5 | 下游影响 + 文档传播 | **ALIGNED**（纯增量、无破坏性；CHANGELOG/版本 bump 由 P8 处理——提示）|
| A6 | 锚点表覆盖 | **ALIGNED**（不新增 CHECK/协议规则，锚点表无需变更）|
| A7 | 设计原则一致性 | **ALIGNED** |

**总结论：SELF-GATE 对齐轴 PASS（无 MISALIGNED）。** 附 2 项 `NEEDS_HUMAN_REVIEW`（均为 P7/P8 排期提示，非 P4 阻塞项，P4 代码无需改动）——见文末「主 Agent 人工确认清单」。

---

## 逐项审查

### A1：文档→脚本对齐 — ALIGNED

**文档声明 1 — `CommandStreamAdapter` 基类契约**（`agate/scripts/agate-cmdstream-adapters.py:97-113`）：
> `class CommandStreamAdapter:` `"""命令流适配器基类：定义 probe/list_sessions/read_commands 契约（P2 §3.1 M2）。"""`
> `probe(self, path)` — 「判断 path 是否为本平台会话文件。」
> `list_sessions(self, cwd)` — 「定位 cwd 下本平台会话文件（含子 agent 会话），返回绝对路径列表。」
> `read_commands(self, session_path)` — 「解析会话文件 → CommandRecord 列表。」

**文档声明 2 — 设计笔记 §3.4.4 适配器契约**（`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/design-subagent-liveness-and-self-dispatch-v5-with-cmdstream-validation.md:251-264`）：
> `def probe(self, path) -> bool` / `def list_sessions(self, cwd) -> list[str]` / `def read_commands(self, session_path) -> list[CommandRecord]`
> 「新增平台的扩展路径（例：未来接入 Codex/Cursor）：1. 实现 `CommandStreamAdapter`（探测 + 会话枚举 + 解析为 IR），**约一个文件**；2. 注册到适配器注册表；3. **检测引擎、阈值、检测逻辑零改动**——新增平台的全部成本收敛在适配器内」

**文档声明 3 — P2-design §4.2 十字段映射 + §5 五设计点定论**（`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md:157-171, 203-315`，P4-implementation.md 明确「§5 五设计点定论 = 实现权威」）。

**脚本实现**（`agate/scripts/agate-cmdstream-adapters.py:622-853` `class CodexAdapter`）：

| 契约点 | 文档要求 | 脚本实现 | 判定 |
|---|---|---|---|
| `probe -> bool` | 判断是否本平台会话文件，异常不抛（比照 `DSHAdapter.probe` / `ClaudeCodeAdapter.probe`）| L641-666：basename `startswith("rollout-")` ∧ `.jsonl` 非 `.jsonl.zstd` → 读首行 `json.loads` → `type=="session_meta"` ∧ `payload` 含 `cli_version`/`originator`/`id` 任一；`except (OSError, ValueError, TypeError): return False` | ALIGNED |
| `list_sessions -> list[str]`（含子 agent）| 定位 cwd 下会话文件含子会话，返回绝对路径列表；P2-review N1：`cwd` 为 `None`/`""` 都回落默认根 | L668-684：`root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`；`os.walk` 收 `rollout-*.jsonl`（排除 `.jsonl.zstd`）→ `sorted()` 绝对路径 list。子会话与父会话同目录独立 `rollout-*.jsonl` → `os.walk` 天然同时枚举（设计点 5） | ALIGNED |
| `read_commands -> list[CommandRecord]` | 逐行解析 rollout JSONL → IR；坏行不崩溃（比照 `ClaudeCodeAdapter`/`DSHAdapter` CRITICAL-4）；源过滤 `type=="event_msg"` ∧ `payload.type ∈ {item_completed(主), item_started/item_updated(pending 判据)}` ∧ `item.type=="CommandExecution"`（P2 §5 设计点 2 L206-208）| L686-756：外层 `type!="event_msg"` → skip；`payload` 非 dict → `skipped+=1`；`item.type!="CommandExecution"` → skip；`item_started`/`item_updated` 入 `started` dict；`item_completed` → `_build_record`；非 JSON/非 dict → `skipped+=1`+`continue`；`skipped` 时 stderr 一行（照 `ClaudeCodeAdapter`）| ALIGNED |
| `truncated ⇒ output_hash=None`（RM-AG0055 §3.4.2 差异点 4 / §3.4.3 截断排除）| 截断输出不参与无效重复检测哈希比对，对 `truncated=true` 采保守策略「输出变化不可判定」→ `output_hash=None`；只用于冻结检测 | L843-846：`output_hash = None if truncated else _sha1_hex(str(output or ""))`；pending 分支（L818-829）`output_hash=None` 硬编码；`_detect_truncated`（L766-787）双信号：`_CODEX_TRUNC_BOOL_KEYS` 显式布尔字段 ∪ `_CODEX_TRUNC_TEXT_MARKERS` 在 `aggregated_output`+`formatted_output` 小写子串——比照 `DSHAdapter._detect_truncated`（设计点 4，P5 V4 实测前兜底，代码含 `# P5 V4 收敛锚` 注释） | ALIGNED |
| `exit` 直取数字 exit_code（P1 §4.1.1 P0_STALE 更正：Codex rollout `CommandExecution` item 有 `exit_code` 数字字段，无需文本前缀解析）| `exit = n if isinstance(n, int) and not isinstance(n, bool) else None`；失败命令 `exit_code==2` 如实映射不回落 None（P2 §5 子决策）| L836-838：`exit_code = raw_exit if isinstance(raw_exit, int) and not isinstance(raw_exit, bool) else None` | ALIGNED |
| `exit_signal` 留档原始形态 | 完成有 exit_code → `f"exit_code={n}"`；完成无 → `item.status` 或 `"status=completed"`；pending → `"pending"`（P2 §5 子决策 c=A）| L839-843 完成分支 + L826 pending 分支 `exit_signal="pending"` | ALIGNED |
| `command` = `shlex.join(item.command)`，非 list → `""`（P2 §5 子决策 b=A）| 元素逐个 `str()` 强转 | L758-762 `_join_command`：`shlex.join(str(part) for part in command)`；`not isinstance(command, list) → return ""` | ALIGNED |
| `session_id` = `os.path.basename(session_path)`，**不取** `payload.session_id`（设计点 3：子会话该字段是父 id）| 照搬 `ClaudeCodeAdapter`/`DSHAdapter` | L687 `session_id = os.path.basename(session_path)`；无任何 `payload.session_id` 读取 | ALIGNED |
| `ts_start` fallback：`payload.started_at_ms` 缺 → 首行封套 `timestamp` 经 `_iso8601_to_epoch_ms` → 再缺 None（P2 §4.2）| — | L797-802：`ts_start = _codex_int_or_none(payload.get("started_at_ms"))`；`is None` → `_iso8601_to_epoch_ms(obj.get("timestamp", ""))`（`except (ValueError, TypeError): ts_start = None`）| ALIGNED |
| pending 双判据（P2 §5 设计点 2 L247-249 / R3）：`item_completed` 且 `status != "completed"` **∪**「有 `item_started`/`item_updated` 无 `item_completed`」回填 | 各补一条 `exit=None`/`ts_end=None`/`exit_signal="pending"`（照 `DSHAdapter` line 556-560）| L734-737：`pending = item.get("status") != "completed"`；L744-751：结束时 `for item_id ... if item_id in emitted_ids: continue` → 对 `started - emitted` 补 `pending=True` 记录 | ALIGNED |

**「约一个文件、检测引擎/阈值零改动」承诺兑现核实**：
- `git diff HEAD --stat`：`agate-cmdstream-adapters.py` 226 insertions / 1 deletion（0 removal 除测试断言外，纯增量）+ `test_agate_cmdstream_adapters.py` +1/-1。仅 2 文件。
- `git diff HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py` → **空**（`agate-cmdstream-detect.py` / `CommandRecord` dataclass 逐字节未改）。
- `CodexAdapter` class 加入既有 `agate-cmdstream-adapters.py`（`DSHAdapter` 之后、`ADAPTERS` 之前），`ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` class 体未改。
- **结论：§3.4.4 承诺兑现——新增平台成本收敛在 `CodexAdapter` class + `ADAPTERS` 一行 + `import shlex` + 2 模块常量 + 1 助手。**

**A1 判定：ALIGNED。** 三方法语义、十字段映射、pending 双判据、截断双信号、`truncated⇒output_hash=None`、`exit` 数字直取——`CodexAdapter` 实现逐条符合基类 docstring + design-note §3.4.4 + P2-design §4.2/§5 定论。
说明（非缺陷）：设计点 2 的事件类型形态（`event_msg`/`item_completed`/`CommandExecution`）与设计点 4 截断标记形态在 P2 中标 `[未实测]`/`[待定]`，设有 P5 V1/V4 收敛锚（P1 §7、代码 `# P5 V4 收敛锚` 注释）——这是 spike 已知边界的排期处理，脚本与 P2 定论一致，不影响 A1 对齐判定。

---

### A2：脚本→文档对齐 — NEEDS_HUMAN_REVIEW

新增 `CodexAdapter` 后**应当**同步的协议文档，逐一核查：

| 文档 | 现状（本次 diff 未含）| 判定 |
|---|---|---|
| `agate/platform-notes.md` `## Codex / Hermes / OpenClaw 等` 章（L43-45）| 仍为 `待补充——如有使用经验，欢迎 PR。` | **排期 P7**（P2 §11 dispatch_plan `protocol-docs` 批 / P1 §9「P7 不可裁」）。**不是 MISALIGNED**——代码先行、文档 P7 补是 dispatch_plan 的明确 `static-batch` 划分。→ NEEDS_HUMAN_REVIEW（提示 P7 必做）|
| `agate/scripts/README.md` | `grep -n "cmdstream\|adapter\|codex\|命令流\|适配器"` → **零命中**。该 README 从未维护 cmdstream 适配器清单。| ALIGNED——无适配器清单可同步，无需改动 |
| `agate/tests/README.md` | 同上，`grep` 零命中 | ALIGNED——无需改动 |
| `agate/SETUP.md` Codex 接入小节 | `grep -n "Codex"` → 零命中（`test_bdd_27` 红）| **排期 P7**（P2 §11 `protocol-docs` 批）→ 归入 NEEDS_HUMAN_REVIEW（同 platform-notes）|

**SELF-GATE 留痕要求**（P2 §6 SELF-GATE 预告 / R6 / `commit-msg-self-gate.sh` hook）：本次 P4 commit message 须含 `self-gate-review:` 指向本报告（`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md`，文件名含 `TAG0033` 满足 DEBT0011 防跨任务覆盖），并宜说明「Codex 协议文档同步排期 P7 protocol-docs 批」。

**A2 判定：NEEDS_HUMAN_REVIEW。** `platform-notes.md` Codex 章 + `SETUP.md` Codex 小节的文档同步已由 P2 dispatch_plan 明确排期 P7、P1 §9 声明 P7 不可裁——本次 P4 代码先行是排期内，非遗漏、非 MISALIGNED。主 Agent 需确认 P7 protocol-docs 批照排执行。`scripts/README.md` / `tests/README.md` 无需改动。

---

### A3：一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW（A3a ALIGNED；A3b 待 P7/P8 回写）

#### A3a 连锁（已知衍生改动）— ALIGNED

`ADAPTERS` 注册表加 `"codex": CodexAdapter()`（`agate-cmdstream-adapters.py:851`）→ `agate-cmdstream-detect.py` 是否需手动改？

**核查**：`agate-cmdstream-detect.py:96` `ADAPTERS = _load_adapters().ADAPTERS`（importlib 动态加载兄弟模块）；CLI 三处 `choices=sorted(ADAPTERS.keys())`（L308 `list` / L312 `read` / L317 `--platform` of `detect`）。→ `"codex"` 键随 `ADAPTERS` 字面量新增**自动纳入** CLI choices，`detect.py` **零改动生效**。`git diff` 证实 `detect.py` 未改。
测试佐证：`test_bdd_6_detect_consumes_registry_zero_change`（`test_agate_cmdstream_adapters.py:306`）断言由 `assert registered == {"claude-code","opencode","dsh"}` 改为 `assert {"claude-code","opencode","dsh"}.issubset(registered)` + `assert "codex" in registered` + `assert "ADAPTERS" in detect_src`——原语义（检测引擎零改动消费注册表）保留、不弱化（BDD-19）。

**A3a 判定：ALIGNED。** 检测引擎通过注册表消费新平台，无需手动改 `detect.py`。

#### A3b 反向传播（主动推断「应被本次改动影响但未在 diff 中」的文件）

| 候选文件 | 核查结果 | 判定 |
|---|---|---|
| `agate/platform-notes.md`（Codex 章）| 见 A2——排期 P7 | NEEDS_HUMAN_REVIEW（并入 A2）|
| `agate/SETUP.md`（Codex 小节）| 见 A2——排期 P7 | NEEDS_HUMAN_REVIEW（并入 A2）|
| `agate/scripts/README.md` | 无 cmdstream 适配器清单（grep 零命中）| ALIGNED——无需回写 |
| `agate/tests/README.md` | 无 cmdstream 适配器清单（grep 零命中）| ALIGNED——无需回写 |
| `agate/LIMITATIONS.md` | `grep -n "[Cc]odex\|exit_code\|数字 exit\|命令流\|cmdstream\|adapter"` → 仅命中局限 3 叙事中的 `exit code` 泛指，**无** 「Codex 无数字 exit code」类旧表述、**无** cmdstream 适配器清单。P1 §4.1.1 的 `[P0_STALE]`（P0-brief/交接单称 Codex 无数字 exit code）指向的是 **P0-brief / HANDOFF**，不是 `LIMITATIONS.md`——`LIMITATIONS.md` 无对应旧文需更新。| ALIGNED——无需回写 |
| `docs/research/cross-platform-dispatch-mechanics.md`（RM-AG0060/AG0061 立项依据，2026-09-08）| L169 `⚠ **缺 `CodexAdapter`**`；L286 `**唯一缺口 = Codex 适配器**`；L131/275 类似「本轮未测/落地前实测」表述。P4 落地 `CodexAdapter` 后，「缺 / 唯一缺口」表述**过时**。该文为**时效性研究叙事文档**（文首自声明「本报告结论有时效」「落地前逐平台复核」），非协议契约、无 gate 脚本消费、`check-protocol-consistency.py` 对叙事文件仅 WARNING。| **NEEDS_HUMAN_REVIEW**——建议 P7（protocol-docs 与 P5/P6 真机结论合并回写）或 P8（roadmap 回写 RM-AG0061→done 同批）补一行「`CodexAdapter` 已随 TAG0033 落地」回写 L169/L286。**非 P4 职责、非 MISALIGNED**（零改动硬约束外的叙事文档，本次不建议 implementer 动）|
| `docs/design-notes/260903-.../design-...-v5-with-cmdstream-validation.md` §3.4.4 / §6 事项 7 | §3.4.4「未来接入 Codex/Cursor」为前瞻示例，§6 事项 7「三平台各写一个适配器实现」为 RM-AG0055 落地待办。新增第四平台不与该设计笔记文字冲突（示例性表述，非契约计数）。| ALIGNED——设计笔记无需改（若欲留痕「Codex 已接入」可选，非必须；同属 RM-AG0055 血缘而非 TAG0033）|
| `agate/adr.md` | 见 A7 | ALIGNED |
| `CHANGELOG.md` / 版本文件 | 见 A5——P8 统一处理 | ALIGNED-with-note（P8 提示）|

**A3b 判定：NEEDS_HUMAN_REVIEW。** 2 项待回写：① `platform-notes.md` + `SETUP.md`（排期 P7，并入 A2）；② `docs/research/cross-platform-dispatch-mechanics.md` L169/L286 的「缺 CodexAdapter / 唯一缺口」过时表述（建议 P7 或 P8 回写，非 P4 阻塞）。其余候选（两个 README、`LIMITATIONS.md`、设计笔记）均 ALIGNED，无需回写。

**A3 综合判定：NEEDS_HUMAN_REVIEW**（A3a 连锁 ALIGNED；A3b 反向传播有 2 项 P7/P8 回写提示）。

---

### A4：测试覆盖 — ALIGNED

#### 全量 pytest 实跑输出（本审查自跑，2026-09-09）

命令：`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=line`

```
........................................................................ [ 87%]
........................................................................ [ 93%]
........................................................................ [ 98%]
.......................                                                  [100%]
=================================== FAILURES ===================================
E   AssertionError: Codex 章仍为「待补充」占位
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:49
E   AssertionError: 缺验证 CLI 版本号 0.153.4
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:73
E   AssertionError: Codex 章缺 spawn_agent 段落
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:87
E   AssertionError: 新 Codex 章未交叉引用既有 max_depth 注记
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:105
E   AssertionError: 缺 ChatGPT 账号默认 model gpt-5.6-terra
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:119
E   AssertionError: SETUP.md 无 Codex 小节
/home/kity/oclab/agateon/.worktrees/agate-TAG0033/agate/tests/unit/test_codex_platform_docs.py:133
=========================== short test summary info ============================
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_22_codex_chapter_capability_matrix
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_23_codex_chapter_version_and_account
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_25_codex_chapter_cross_reference_no_contradiction
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_26_codex_chapter_model_lineup
FAILED agate/tests/unit/test_codex_platform_docs.py::test_bdd_27_setup_md_codex_section
6 failed, 1383 passed, 2 skipped in 116.32s (0:01:56)
```

**passed / failed / skipped 计数：1383 passed / 6 failed / 2 skipped**（与 dispatch-context「客观查证信息」实测基线逐字一致）。

#### 6 条 failed 说明（预期红，P7 转绿）

全部为 `test_codex_platform_docs.py::test_bdd_22~27`——审查 `platform-notes.md` Codex 章 + `SETUP.md` Codex 小节的协议文档锚点。该文件头部注释（L4-16）明确：「被测（P7 才补，本文件 BDD-22~27 用例当前必须红）」「下游提示：gate_commands.P5 会扫到本文件 → BDD-22~27 的 6 条在 P4~P6 期间为 task-introduced 失败（P7 补文档后转绿）」。P2 §11 dispatch_plan `protocol-docs` 批 = P7。**这 6 条红是排期内、有账本记录的预期失败，不是 P4 回归。** P5 dispatch 须显式处理（`--deselect` 这 6 条 / 或按 P5 卡「预期在 P7 转绿的失败」登记）。

#### `CodexAdapter` 测试覆盖核查

| 边界 | 覆盖测试 |
|---|---|
| probe 识别 rollout / 拒绝非 Codex jsonl（claude 内容 / `.jsonl.zstd` / `opencode.db`）| `test_bdd_1_codex_probe_identifies_rollout` |
| list_sessions 枚举 `YYYY/MM/DD` 日期树 + `cwd` falsy（`None`/`""`）回落默认根 | `test_bdd_2_codex_list_sessions_enumerates_date_tree` / `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root` |
| 子会话同目录枚举 | `test_bdd_3_codex_list_sessions_includes_subagent` |
| 十字段映射（exit 0 / `exit_code=0` / `ts_start`/`ts_end` / `output_hash`）| `test_bdd_4_codex_read_commands_maps_ten_fields` |
| 失败 `exit_code==2` 如实映射不回落 None | `test_bdd_5_codex_failed_exit_code_verbatim` |
| pending 双判据（`item_started` 无 `item_completed` 回填 / 已完成记录不受影响）| `test_bdd_6_codex_unfinished_command_pending` |
| 截断双信号（bool 键 ∪ 文本标记）⇒ `truncated=True` ∧ `output_hash=None` | `test_bdd_7_codex_truncated_output_hash_none` |
| 非 shell 工具事件（`apply_patch`/`web__run`/`FileChange`/`Extension`）不产出记录 | `test_bdd_8_codex_non_shell_tool_events_no_record` |
| 畸形行（非 JSON / JSON 数组 / 缺 `payload`）不崩溃、`skipped` 计数 | `test_bdd_9_codex_malformed_lines_no_crash` |
| `session_id` = basename、唯一非空 | `test_bdd_10_codex_session_id_consistent_and_locatable` |
| 子会话独立解析（不因缺父上下文返回空）| `test_bdd_11_codex_subagent_session_parses_standalone` |
| `session_id` = 子文件名而非 `payload.session_id`（父 id）| `test_bdd_12_codex_subagent_session_id_is_child_not_parent` |
| IR 十字段 dataclass 未改 | `test_bdd_21_command_record_ten_fields_unchanged` |
| 检测引擎（平台无关）消费 Codex IR：调用冻结 / 活动冻结 / 无效重复 SPIN / 正常无误报 / 截断重复不误判 SPIN / 阈值未改 | `test_agate_cmdstream_detect.py::test_bdd_13~17_codex_*` + `test_bdd_21_detect_thresholds_unchanged` |

`test_agate_cmdstream_adapters.py` + `test_agate_cmdstream_detect.py` 定向复跑（P4-implementation.md §5 自述）：58 passed，P3 基线 19 failed → 0 failed，无回归。

**A4 判定：ALIGNED。** `CodexAdapter` 新逻辑边界（probe 拒绝、畸形行、pending 双判据、截断双信号、子会话 session_id）均有对应 pytest 且全绿；检测引擎侧 5 条 Codex 三态用例全绿。全量 6 failed 全为 P7 文档锚点预期红，非 P4 回归。
非阻塞提示（代码卫生）：`test_bdd_6_detect_consumes_registry_zero_change` 内注释（`test_agate_cmdstream_adapters.py:320-322`）仍为 P3 红灯期表述「现 ADAPTERS 尚无 codex 键 → 本行红；P4 加键 + 上一行改包含式后整片转绿」——P4 已加键，该注释现时态失真，建议 implementer 在 P4 收尾或 P7 顺手改为过去式。不影响测试语义、不阻塞。

---

### A5：下游影响 + 文档传播 — ALIGNED

- **gate 行为影响**：`CodexAdapter` 为**纯增量**新增（`git diff --stat`：226 insertions / 1 deletion；唯一 deletion 是 `test_bdd_6` 断言由精确等值改包含式，语义不弱化）。既有三适配器 class 体、`CommandRecord` dataclass、`agate-cmdstream-detect.py` 检测引擎/阈值均零改动 → 既有项目的 cmdstream gate 行为不变，无破坏性变更。新平台键仅在显式 `--platform codex` 时被消费。
- **`check-protocol-consistency.py`**：P4-implementation.md §5 自述 `--strict-errors-only` exit 0 / 0 ERROR（329 WARNING 全为既有叙事文件引用，与本改动无关）。A6 复核一致。
- **CHANGELOG.md / 版本 bump**：本次 P4 commit 不含。P2 §11 + 本任务 P8 阶段统一处理协议本体版本 bump + CHANGELOG + roadmap 回写 RM-AG0061→done + 归档 HANDOFF。→ **提示 P8 需覆盖 agate 协议本体 CHANGELOG（新增第四命令流适配器 Codex）。**
- **文档传播**：见 A2 / A3b（`platform-notes.md` + `SETUP.md` 排期 P7；research doc 建议 P7/P8 回写）。

**A5 判定：ALIGNED**（附 P8 提示：CHANGELOG + 版本 bump）。纯增量、无破坏性、不改既有 gate 行为。

---

### A6：锚点表覆盖 — ALIGNED

**文档/约束**：P0-brief 核心约束 + DEBT0025——本任务**不新增协议规则 / CHECK**。P1 §5 范围锁定：不扩 IR schema、不改检测引擎、不改阈值。

**脚本核查**（`agate/scripts/check-protocol-consistency.py`）：
- CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS`（L511+）= 「文档声明的规则 → 对应 **gate 脚本**（`check-*.py`）应含关键词」的白名单；`check_anchor_coverage`（L805+）反向兜底遍历对象为 `check-*.py` + `pre-commit-gate.{sh,py}` + `ci-gate-backstop.py`。
- `agate/scripts/agate-cmdstream-adapters.py` 是**机制库脚本**（liveness 检测数据源解析），非 gate 脚本，不落入锚点表 glob，锚点表中本就无 cmdstream 相关条目。
- CHECK 12（权威数值/规则跨文件一致性：重试上限表等）与命令流适配器无关。
- 新增 `CodexAdapter` 不引入任何 CHECK / 协议数值规则 / 锚点关键词 → **锚点表无需变更**。

**A6 判定：ALIGNED。** 不新增 CHECK/协议规则，CHECK 9 / CHECK 12 锚点表均无需更新；`check-protocol-consistency.py --strict-errors-only` 0 ERROR 佐证。

---

### A7：设计原则一致性 — ALIGNED

逐条对照 `agate/adr.md`（ADR-001 ~ ADR-012）：

| ADR | 相关性 | 对齐判定 |
|---|---|---|
| ADR-003 最小约定——不绑定技术栈 | **相关**：适配器模式的立意是把平台特定细节隔离在单个 class 内，检测引擎平台无关。`CodexAdapter` 将 Codex rollout JSONL 格式、`~/.codex/sessions` 布局、`exit_code` 数字字段、截断标记形态全部收敛在 class 内部，未向 `CommandRecord` / 检测引擎泄漏 Codex 概念。| ALIGNED——符合「平台差异隔离在适配器」原则 |
| ADR-005 改动性质决定流程——声明性/行为逻辑/机制交叉 | **相关**：改 `agate/scripts/*.py` 属「机制交叉」→ 触发 SELF-GATE（commit-msg hook + 本 A1-A7 审查 + P7 protocol-alignment-review，`agent != main`）。P2 §6 SELF-GATE 预告 + R6 已声明该流程。| ALIGNED——机制交叉改动的 SELF-GATE 流程照走 |
| ADR-001 / 002 / 004 / 006 隔离性·可判定性·安全网分层·双层角色 | 间接：本审查即「agate 改自己时的语义 gate」，独立上下文（`agent≠main`）执行，符合 ADR-006 独立评审。| ALIGNED |
| ADR-007~012（frontmatter / 版本管理根 / 复用验证证据 / 引导型 CLI 权限 / 版本目录探测）| 无相关性——本改动不涉及 frontmatter schema、版本管理、证据复用、引导型 CLI、版本目录布局。| N/A |

**未记录的架构决策观察**：「统一 IR + 每平台一个适配器 + 检测引擎平台无关」这一架构决策目前仅存于设计笔记 §3.4.4，**未沉淀为 `adr.md` 条目**——与 `agate-alignment-review-2026-08-25-TAG0024.md` A7、`agate-alignment-review-2026-09-07-TAG0032.md` A7 指出的同类模式（架构决策只停在 design note）一致。可考虑补一条「命令流适配器模式」ADR，但该决策属 **RM-AG0055 / TAG0028 血缘**（适配器模式落地任务），非 TAG0033 引入——**不作为本任务的 A7 阻塞或必办项**，仅记录供主 Agent 酌情转 RM-AG0055 后续。

**A7 判定：ALIGNED。** `CodexAdapter` 符合既有 ADR（ADR-003 技术栈隔离、ADR-005 机制交叉流程），无 ADR 与之冲突。适配器模式 ADR 缺口是 RM-AG0055 血缘的既有观察，非 TAG0033 新增，不阻塞。

---

## 反向传播清单逐一验证（A3b 汇总）

| # | 候选文件 | 应否受本次改动影响 | 现状 | 结论 |
|---|---|---|---|---|
| 1 | `agate/platform-notes.md` Codex 章 | 是（补完整能力矩阵 + 实机记录）| 仍「待补充」| **P7 排期**（P2 §11 protocol-docs / P1 §9 不可裁）→ NEEDS_HUMAN_REVIEW |
| 2 | `agate/SETUP.md` Codex 小节 | 是（安装 + 账号 vs model + 关键 flag）| 无 Codex 小节（`test_bdd_27` 红）| **P7 排期** → NEEDS_HUMAN_REVIEW |
| 3 | `agate/scripts/README.md` | 否——无 cmdstream 适配器清单 | grep 零命中 | ALIGNED（无需改）|
| 4 | `agate/tests/README.md` | 否——无 cmdstream 适配器清单 | grep 零命中 | ALIGNED（无需改）|
| 5 | `agate/LIMITATIONS.md` | 否——无「Codex 无数字 exit code」旧表述、无适配器清单（P0_STALE 指向 P0-brief/HANDOFF 而非此文）| grep 仅命中局限 3 泛指 `exit code` | ALIGNED（无需改）|
| 6 | `docs/research/cross-platform-dispatch-mechanics.md` | 宜（L169「⚠ 缺 CodexAdapter」/ L286「唯一缺口 = Codex 适配器」P4 后过时）| 未回写 | **NEEDS_HUMAN_REVIEW**——建议 P7/P8 加一行落地回写；时效性叙事文档、无 gate 消费、非 MISALIGNED、非 P4 职责 |
| 7 | 设计笔记 §3.4.4 / §6 事项 7 | 否——「未来接入 Codex」为前瞻示例，非契约计数 | 未改 | ALIGNED（可选留痕，属 RM-AG0055 血缘）|
| 8 | `agate/adr.md` | 否——无 ADR 冲突（见 A7）| 未改 | ALIGNED |
| 9 | `CHANGELOG.md` / 版本文件 | 是——但 P8 统一处理 | 未改 | ALIGNED-with-note（P8 提示）|
| 10 | `agate-cmdstream-detect.py` | 否——`choices=sorted(ADAPTERS.keys())` 动态纳入 codex（A3a）| 零改动（diff 空）| ALIGNED（连锁自动生效）|

---

## 主 Agent 人工确认清单（NEEDS_HUMAN_REVIEW，共 2 项）

> 均为 P7/P8 排期提示，非 P4 阻塞项，P4 代码无需改动、无 MISALIGNED。每项需主 Agent 附 `[HUMAN_CONFIRMED: 2026-09-09 确认：<理由>]` 后闭环。

**[NHR-1]（A2 + A3b #1/#2）** `agate/platform-notes.md` 的 `## Codex / Hermes / OpenClaw 等` 章仍为「待补充」占位，`agate/SETUP.md` 无 Codex 接入小节（`test_codex_platform_docs.py::test_bdd_22~27` 6 条预期红）。
- 依据：P2-design §11 dispatch_plan `static-batch` 两批——`adapter-core`（P4，本次）/ `protocol-docs`（P7，`platform-notes.md` Codex 章 + `SETUP.md` Codex 小节）；P1 §9「P7 不可裁」。
- 需主 Agent 确认：P7 protocol-docs 批照排执行，且本次 P4 commit message 含 `self-gate-review: agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md` 并注明「Codex 协议文档同步排期 P7」。
- `[HUMAN_CONFIRMED: ____-__-__ 确认：__________]`

**[NHR-2]（A3b #6）** `docs/research/cross-platform-dispatch-mechanics.md` L169「⚠ 缺 `CodexAdapter`」/ L286「唯一缺口 = Codex 适配器」在 `CodexAdapter` 落地后表述过时。
- 依据：该文为时效性研究叙事文档（文首自声明「本报告结论有时效」），非协议契约、无 gate 脚本消费、`check-protocol-consistency.py` 对叙事文件仅 WARNING。零改动硬约束外，本次不建议 implementer 改。
- 需主 Agent 确认：P7（与 P5/P6 真机结论合并回写时）或 P8（roadmap 回写 RM-AG0061→done 同批）补一行「`CodexAdapter` 已随 TAG0033 落地」回写 L169/L286；或明确接受该叙事文档时效性、不回写。
- `[HUMAN_CONFIRMED: ____-__-__ 确认：__________]`

## 附：非阻塞提示（不计入 NEEDS_HUMAN_REVIEW）

- **P8 提示**（A5）：agate 协议本体 `CHANGELOG.md` + 版本 bump 需在 P8 覆盖「新增第四命令流适配器 Codex（`CodexAdapter`）」。
- **代码卫生提示**（A4）：`agate/tests/unit/test_agate_cmdstream_adapters.py:320-322` 注释仍为 P3 红灯期时态（「现 ADAPTERS 尚无 codex 键 → 本行红」），P4 已加键，建议改过去式。不影响测试语义、不阻塞。
- **A7 观察**：命令流适配器模式的架构决策仅在设计笔记 §3.4.4、未沉淀为 `adr.md` 条目（同 TAG0024/TAG0032 A7 观察），属 RM-AG0055/TAG0028 血缘；可酌情转该 RM 后续补 ADR，非本任务必办。

## 总结论

**SELF-GATE 协议-脚本语义对齐轴：PASS（无 MISALIGNED）。**

- A1 / A4 / A5 / A6 / A7：**ALIGNED**。`CodexAdapter` 逐条符合基类 docstring + design-note §3.4.4 + P2-design §4.2/§5 契约；`truncated⇒output_hash=None` 兑现；「约一个文件、检测引擎零改动」兑现（`detect.py`/`ir.py` diff 空）；全量 1383 passed / 6 failed（P7 文档锚点预期红）/ 2 skipped；不新增 CHECK/协议规则、锚点表无需变更；无 ADR 冲突。
- A2 / A3：**NEEDS_HUMAN_REVIEW ×2**——均为 P7（`platform-notes.md` + `SETUP.md`）/ P7-P8（research doc 回写）的**排期内**文档同步提示，非遗漏、非 P4 阻塞。A3a 连锁（`detect.py` 零改动消费注册表）ALIGNED。

**闭环动作**：主 Agent 对 [NHR-1] / [NHR-2] 附 `[HUMAN_CONFIRMED]` 后，本 SELF-GATE 审查即闭环，P4 可 commit（commit message 须含 `self-gate-review:` 指向本报告）。P4 代码本身无需任何修订。
