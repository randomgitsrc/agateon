---
task_id: TAG0033
date: 2026-09-09
round: 3 (F1 fix after P5→P4 retreat)
reviewer: protocol-alignment-review (agent≠main)
review_date: 2026-09-09
change_summary: "CodexAdapter pending 判据 F1 修复（DEBT0035）——新增 _codex_is_finished(payload,item) helper + `pending = not _codex_is_finished(...)` + fixture 真机 status=failed 形态 + 测试 + platform-notes.md 1 bullet + P1/P2 BASELINE_CHANGE"
files_changed:
  - agate/scripts/agate-cmdstream-adapters.py
  - agate/tests/fixtures/cmdstream/codex-session.jsonl
  - agate/tests/unit/test_agate_cmdstream_adapters.py
  - agate/tests/unit/test_agate_cmdstream_detect.py
  - agate/platform-notes.md
  - agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md
  - agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md
  - agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md
  - agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-progress.md
  - agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl
---

# 协议-脚本对齐审查（TAG0033 第 3 轮 —— F1 / DEBT0035 修复面）

第 1 轮审 `adapter-core` 代码批（`agate-alignment-review-2026-09-09-TAG0033.md`，PASS），第 2 轮审
`protocol-docs` 文档批（`...-r2.md`，PASS）。本轮审 P6 真机 V6 发现 F1（DEBT0035）→ 回退 P5→P4
（`52fe210`）→ implementer 重试 #1 的定向修复面。HEAD = `9a7a1f9`。

`git diff HEAD` 改动面（`--stat` 实核）：`agate-cmdstream-adapters.py` +33 / `codex-session.jsonl` +8 /
`test_agate_cmdstream_adapters.py` +29 / `test_agate_cmdstream_detect.py` +21 / `platform-notes.md` +1 /
`P1-requirements.md` +19 / `P2-design.md` +15 / 任务 md（P4-implementation / P4-progress / gate-events.jsonl）。
**`agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` diff 空**（`git diff HEAD -- <两文件>` 无输出）——
零改动硬约束守住；`ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` / `CodexAdapter.probe` /
`list_sessions` / `_detect_truncated` / `_join_command` / `session_id` / `ADAPTERS` 均未触碰。

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（A3a ALIGNED / A3b 无遗漏文件）|
| A4 | 测试覆盖 | **ALIGNED**（1390 passed / 0 failed / 2 skipped，本审查实跑）|
| A5 | 下游影响 + 文档传播 | **ALIGNED**（附 P8 提示：CHANGELOG + 版本 bump 需覆盖 F1 + DEBT0035）|
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED**（保留 r1/r2 既有非阻塞观察：cmdstream 适配器模式仍未沉淀 ADR）|

**总结论：SELF-GATE 协议-脚本语义对齐轴 = PASS。全 7 项 ALIGNED，无 MISALIGNED，无新增 NEEDS_HUMAN_REVIEW。**

---

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

**helper 实现**（`agate-cmdstream-adapters.py:641-664`）：

```python
def _codex_is_finished(payload, item):
    if isinstance(item, dict):
        if item.get("status") in ("completed", "failed"):
            return True
        raw_exit = item.get("exit_code")
        if isinstance(raw_exit, int) and not isinstance(raw_exit, bool):
            return True
    return isinstance(payload, dict) and payload.get("completed_at_ms") is not None
```

消费点 `read_commands`（`:766`）：`pending = not _codex_is_finished(payload, item)`（原 `item.get("status") != "completed"`）。

**判据三元集 = 任一成立即「已结束」**：① `status ∈ {"completed","failed"}` ② `exit_code` 是 int 且非 bool
③ `payload.completed_at_ms` 非 None。

#### A1-①：`platform-notes.md` 新 bullet ↔ helper 逐字比对 — 一致

`platform-notes.md:88`（「命令流适配（RM-AG0055 / CodexAdapter）」小节，per-command 退出码 bullet 之后）：

> **`payload.item.status` 真机取值集**（P6 V6 实测，DEBT0035）：`completed`（成功终态）/ `failed`（**已结束但非 0 退出**——仍携带完整 `exit_code`（如 `2` / `137`）+ `payload.completed_at_ms` + `aggregated_output`；`sleep` 被 SIGINT 也落 `failed` + `exit_code=137`）/ `in_progress`（未结束）。`CodexAdapter` 以「有终态信号」判已结束——`status ∈ {completed, failed}` **或** 有 `completed_at_ms` **或** 有数字 `exit_code`（`_codex_is_finished`）；仅真·未结束（`item_started` 无 `item_completed`，或 `item_completed` 但三信号皆缺）才映射 `exit_signal="pending"`。旧口径 `status != "completed"` 会把真机 `failed` 终态误判为 pending 而丢失 `exit_code` + `output_hash`（P6 V6 修正 / DEBT0035）。

逐项对照：

| bullet 陈述 | helper 代码 | 一致？ |
|---|---|---|
| `status ∈ {completed, failed}` → 已结束 | `item.get("status") in ("completed", "failed")` | ✔ 逐字 |
| 有数字 `exit_code` → 已结束 | `isinstance(raw_exit, int) and not isinstance(raw_exit, bool)` | ✔（「数字」= int 非 bool，与 `_codex_int_or_none` 同口径）|
| 有 `completed_at_ms` → 已结束 | `payload.get("completed_at_ms") is not None` | ✔ |
| 「有终态信号」总口径 | 三分支 `or` | ✔ |
| 仅真·未结束才 `exit_signal="pending"` | `_build_record(..., pending=True)` 仅在 `not _codex_is_finished` 或 `started_ids - emitted_ids` 回填时 | ✔ |
| 旧口径误判 `failed` → 丢 `exit_code`+`output_hash` | `_build_record` pending 分支返回 `exit=None / output_hash=None` | ✔ |
| 真机取值集含 `in_progress`（未结束）| fixture `item-demo-3` `sleep 999` `status:"in_progress"` + item_started 无 item_completed | ✔ |
| `sleep` SIGINT → `failed` + `exit_code=137` | 归档 `real-machine-p6.md:34`「`sleep 600` item：`status="failed"`, `exit_code=137`」 | ✔（真机实证）|

`CodexAdapter` class docstring（`:678-681`）同步改口径：「`item_completed` 但无终态信号——status∉{completed,failed}
且缺 completed_at_ms/exit_code，`_codex_is_finished`」+「真机 status=="failed" 携 exit_code 属已结束，走非
pending 路径（DEBT0035 / P6 V6）」——与 helper 语义一致。

#### A1-②：`P1 §4.1` / `P2 §5` 的 BASELINE_CHANGE ↔ 代码 — 一致

- `P1-requirements.md:112-117` BASELINE_CHANGE：「真机 `item.status` 取值集 = `completed`（成功终态）/
  `failed`（已结束非 0 退出）/ `in_progress`（未结束）」+「`read_commands` 的『已结束』判据据此改口径」——
  与 helper + platform-notes bullet 三方一致。
- `P2-design.md:250-257` BASELINE_CHANGE：「**已结束** = `item.status ∈ {"completed","failed"}` **或**
  `payload.completed_at_ms` 非 None **或** `item.exit_code` 是 int 非 bool（三者任一）；`pending = not 已结束`。
  逻辑抽 `_codex_is_finished(payload, item)` helper 集中。」——与 `read_commands:766` 消费点 + helper 逐字一致
  （列举顺序与代码分支顺序不同，但 `or` 语义与顺序无关）。
- DEBT0035 `recommendation`（`tech-debt.md:1234`）：「status in ('completed','failed') 或存在
  completed_at_ms/exit_code → 走已完成路径」——与落地实现同口径。

#### A1-③：RM-AG0055 §3.4.2 差异点 4 / §3.4.3 阈值 — 未触碰，确认

`agate-cmdstream-detect.py` diff 空。SPIN 判据（`:220-239`）仍为「窗口内同 `(cmd, exit, out)` 组合 ≥
`SPIN_THRESHOLD`（5）」+「`if r.get("truncated"): continue`（截断不参与哈希比对，BDD-17）」。F1 修复不改
检测引擎任何阈值 / 冻结口径 / `truncated` 参与逻辑。`agate-cmdstream-ir.py` `CommandRecord` 十字段
dataclass（`:32-44`）diff 空。

**结论**：ALIGNED。文档三方（`platform-notes.md` / `P1 §4.1` / `P2 §5`）+ DEBT0035 recommendation 与
`_codex_is_finished` helper 逐字一致；detect.py / ir.py 零改动确认，RM-AG0055 §3.4.2/3.4.3 未受影响。

---

### A2: 脚本→文档对齐 —— ALIGNED

F1 修复所需文档同步：`platform-notes.md` 真机 `status` 取值集 bullet（已加，见 A1-①）+ BASELINE_CHANGE
回写 P1 §4.1 / P2 §5（已加，见 A1-② / BASELINE_CHANGE 核查表）。

doc-audit 实跑（本审查，`timeout 120s`）：

```
$ python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q
........                                                                 [100%]
8 passed in 0.03s
```

新 bullet 落在 `platform-notes.md` 既有「命令流适配」小节内，未破坏 `test_codex_platform_docs.py` 的既有
doc 锚点（8 passed / 0 failed）。

**结论**：ALIGNED。

---

### A3: 一致性连锁 + 反向传播 —— ALIGNED

#### A3a（连锁：已知衍生改动）— ALIGNED

`_codex_is_finished` 改口径 → 真机 `status="failed"` 的 `CommandExecution` item 从「pending 路径」
（`exit=None / ts_end=None / exit_signal="pending" / output_hash=None`）改走「已完成路径」
（`exit=<非0 int>` / `ts_end=<completed_at_ms>` / `exit_signal="exit_code=N"` / `output_hash=<真实哈希>`）。

detect.py 消费侧（**零改动即正确**）：

- CLI 转换层 `agate-cmdstream-detect.py:357`：`if r.exit is not None or r.ts_end is not None:` 才产出
  `kind=="result"` 事件（携 `exit` / `out=output_hash`）。旧口径下真机失败命令 `exit`/`ts_end` 全 None →
  **只有 `call` 事件、无 `result` 事件** → SPIN 窗口 `combo_counts` 拿不到 `(cmd, exit, out)` 签名 →
  判 FROZEN（调用冻结）/ NORMAL（P6 V6 ③ 实测）。
- 修复后失败命令产出 `result` 事件 → detect 算出重复结果签名 → `:229` `worst >= SPIN_THRESHOLD` → SPIN。

这是**恢复 IR 契约本意**（`CommandRecord.exit` 语义 = 「已结束 call 的真实退出码」，`ir.py:41` 注
`exit int|None`；`None` 专指「未结束 call」，`ir.py:55`）——旧 pending 判据把已结束的失败命令误标 None，
是违反契约的 bug。修 bug 不需要动 detect.py（它本就按「`exit`/`output_hash` 非 None 才算结果签名」运作）。
ALIGNED。

#### A3b（反向传播：主动推断应被影响文档）— 无遗漏文件

| # | 候选文件 | 是否需改 | 证据 |
|---|---|---|---|
| 1 | `docs/research/cross-platform-dispatch-mechanics.md` §2.4 | **否** | §2.4（`:72-78`）标题 =「非法 / 不可用 model 的失败形态」，讲的是 **model-metadata 退化**（`item.completed{item.type:error}` → `error{status:400}` + `turn.failed`），属 **turn 级 / model 可用性** 失败面，与本轮 **per-command `CommandExecution.status:"failed"`（正常 shell 非 0 退出终态）** 是**不同层级的概念**。§2.4 无需补 per-command `status:"failed"`——该事实的权威落点是「平台适配权威源」`platform-notes.md`（已补，A1-①）。L169「`CodexAdapter` 已补（TAG0033）」r2 已回写、本轮未过时。 |
| 2 | `docs/research/.../mechanics.md` L195「Codex：不可靠……必须解析 `--json` 事件流」 | **否** | 同 #1——该句限定「turn 级失败」（`turn.failed` / `item.type:error`），`platform-notes.md:87`「per-command 退出码」bullet 已双向分清适用边界（r2 A1 已核）。本轮新 bullet 承接该分界、不冲突。 |
| 3 | `agate/LIMITATIONS.md` | **否** | grep `codex\|cmdstream\|命令流\|退出码\|RM-AG0055\|pending\|SPIN` → 仅命中局限 3「弱测试」叙事（`:7` / `:28` / `:35`），与 Codex 适配器 / exit code 语义无关；无「Codex 无数字 exit code」旧表述、无适配器清单。与 r1 A3b #5 结论一致。 |
| 4 | DEBT0035 `closure_criteria`（`tech-debt.md:1235-1240`）| 本轮满足 4/5，剩 1 条待后续阶段（预期）| ① 「`status=="failed"` 带 exit_code → `exit=<非0 int>` / `ts_end` / `output_hash` 非 pending」= **满足**（helper + `test_bdd_5_*` + guard）；② 「P3 测试覆盖 `status=="failed"`；fixture 含真机 failed 样本」= **满足**（`test_bdd_5_codex_failed_exit_code_verbatim` 改真机形态 + `test_bdd_5_codex_failed_status_not_pending_guard` 新增 + fixture item-demo-2 及 r1..r6）；③ 「detect 对真机重复失败会话判 SPIN」= **满足**（P4-progress 记 V6 ③ 复验 → `VERDICT: SPIN`；fixture 侧 `detect ... --now 1788400887` → SPIN）；④ 「全量 pytest 全绿 + consistency 0 ERROR + **P5/P6 重新通过**」= pytest / consistency **满足**（见 A4 / A6），P5/P6 重跑属**后续阶段职责**（本轮 phase=P4 重试，回退卡片明确「已有代码基础上定向修复」，P5/P6 由主 Agent 后续派发）；⑤ 「`platform-notes.md` 含真机 status 取值集；P1 §4.1 补 'failed' 终态」= **满足**（A1-① / A1-②）。DEBT0035 `status: in_progress` 合理，闭合待 P5/P6 绿后由主 Agent 收口。|
| 5 | `agate-workspace/agents/CODE-MAP.md` | **否** | 本轮无新增文件（helper 是 `agate-cmdstream-adapters.py` 内模块级函数，非新文件）；r2 已同步 CODE-MAP 的 `CodexAdapter` 条目，本轮不触发文件级变更。 |
| 6 | `agate/adr.md` | **否** | 见 A7——无 ADR 冲突。 |
| 7 | `CHANGELOG.md` / 版本文件 | P8 统一处理（提示已升级）| 见 A5。 |
| 8 | RM-AG0055 设计笔记 §3.4.2/§3.4.4 | **否** | detect.py 零改动，差异点 4（`truncated`）/ §3.4.4「约一个文件」范式均未触碰；`_codex_is_finished` 落在「适配器内隔离平台差异」的既有范式内（A7）。 |

**A3b 无遗漏文件**——所有推断出的应被影响文档，要么已在 diff 中同步（`platform-notes.md` / `P1` / `P2`），
要么经核实无需改（研究叙事文档 §2.4 属不同概念层 / `LIMITATIONS.md` 无相关内容 / CODE-MAP 无文件级变更）。

**结论**：ALIGNED。

---

### A4: 测试覆盖 —— ALIGNED

**全量实跑**（本审查，`timeout 300s`，非引用 implementer 自述）：

```
$ python3 -m pytest agate/tests/unit/ -q --tb=short
........................................................................ [  5%]
  ... (中略) ...
........................                                                 [100%]
1390 passed, 2 skipped in 114.16s (0:01:54)
```

**passed / failed / skipped = 1390 / 0 / 2**——与派发预期（1390 passed / 0 failed / 2 skipped，1389 基线 +
1 守护）**逐字吻合**。

抽读断言体（确认为实校验、非占位）：

- **`test_bdd_5_codex_failed_exit_code_verbatim`**（`test_agate_cmdstream_adapters.py:790-805`）：Given 改
  `status="failed"`（fixture item-demo-2）；Then `r.exit == 2` / `r.exit is not None` / `r.exit_signal ==
  "exit_code=2"` / `r.ts_end is not None` / `r.output_hash is not None`。— 锁定「`failed` 终态不被当
  pending，exit/ts_end/output_hash 全落真实值」。
- **`test_bdd_5_codex_failed_status_not_pending_guard`**（`:808-828`，无新 BDD 编号，挂 BDD-5 名下）：
  `failed = [r for r in records if "ls /demo/nonexistent-xyz" in r.command]`；`assert len(failed) == 6`；
  逐条 `r.exit_signal != "pending"` / `r.exit == 2` / `r.ts_end is not None` / `r.output_hash is not None`。
  — 守护 6 条真机形态重复失败命令全部走已结束路径。docstring 明写「旧口径 `status != "completed"` 会把它
  误判 pending 丢失 exit_code + output_hash（→ detect 判不出 SPIN）」——守护意图明确。
- **`test_bdd_6_codex_unfinished_command_pending`**（`:833-850`，未动）：仍测 item-demo-3 `sleep 999`
  （item_started 无 item_completed）→ `p.exit is None` / `p.ts_end is None` / `p.exit_signal == "pending"`；
  且 `done[0].exit == 2`（`make build-docs` 现 `status="failed"` 走新已结束路径，断言仍成立）——真·未结束
  与已结束失败两条路径在同一 fixture 内交叉验证。
- **`test_bdd_15_codex_invalid_repeat_spin`**（`test_agate_cmdstream_detect.py:601-621`）：6 条
  `_cx_exec(..., exit_code=2, ..., status="failed")` → `CodexAdapter().read_commands` →
  `_records_to_events`（比照 detect.py CLI 转换层 `:343-369`，同 `r.exit is not None or r.ts_end is not
  None` 才产 result 事件）→ `detect(events, now=last+5)` → `assert verdict == "SPIN"`。— 真机形态贯通到
  detect SPIN 判定的端到端守护。
- **`_cx_exec` 签名**（`:503-513`）：新增可选参 `status="completed"`（默认不变，既有调用零回归），docstring
  注「真机把已结束但非 0 退出的命令记为 "failed"（DEBT0035 / P6 V6）」。

回归面：`--tb=short` 全量 0 failed，确认 helper + fixture 6 行追加 + `_cx_exec` 默认参未引入回归
（T027 教训——修复重跑全量已执行）。

**结论**：ALIGNED。F1 有对应测试（BDD-5 改真机形态 + 新守护 + BDD-15 真机形态 + BDD-6 边界保留），
覆盖「`failed` 终态 → 非 pending」「真·未结束 → pending」两侧边界；全量 1390 passed / 0 failed / 2 skipped
本审查实跑佐证。

---

### A5: 下游影响 + 文档传播 —— ALIGNED

- **gate 行为影响**：无。F1 修复 = 新增 1 个模块级 helper + 改 1 处判据表达式 + docstring 微调；不改任何
  `check-*.py`、不改 detect/ir、不改阈值、不新增 CLI 参数 / 子命令。已有项目的 cmdstream gate 行为不变
  （对真机 Codex `failed` 命令从「漏判 SPIN」变「如实判 SPIN」——是**修复既有缺陷**，方向是让检测更准，
  非破坏性变更）。
- **破坏性变更**：无。`CommandRecord` 契约不变（`ir.py` diff 空）；`exit`/`output_hash` 对真机失败命令由
  `None` 变真实值——恢复契约本意，不影响任何按契约消费的下游。
- **文档传播**：`platform-notes.md`（已同步，A2）；`WORKFLOW.md`「Pre-commit 检查总览」/ `dispatch-protocol.md`
  / `state-machine.md` / 角色文件——均无需改（不新增 / 不修改任何 pre-commit 检查行为）。
- **P8 提示（升级版）**：第 1 轮 A5 已提示「agate 本体 `CHANGELOG.md` + 版本 bump 需覆盖新增第四命令流
  适配器 Codex」，第 2 轮补「+ Codex 平台文档」。**本轮追加**：P8 的 CHANGELOG 条目 + 版本 bump 还须覆盖
  **F1 修复（`_codex_is_finished` pending 判据口径修正）+ DEBT0035**——真机 `status:"failed"` 终态识别是
  对 `CodexAdapter` 行为的实质修正，应在发布说明中可见；DEBT0035 待 P5/P6 重新通过后由主 Agent 收口为
  `status: resolved`。

**结论**：ALIGNED（附 P8 提示，非阻塞）。

---

### A6: 锚点表覆盖 —— ALIGNED

- 不新增 CHECK、不新增协议规则、不改 BDD 编号格式 / 功能分组 heading——CHECK 9 锚点表无需变更。
- `platform-notes.md` 新 bullet 属「平台适配权威源」内容：`check-protocol-consistency.py` 的
  `_MD14_WHOLE_FILE_EXEMPT`（`:1183-1184`）含 `"agate/platform-notes.md"`——**整文件豁免 CHECK 14**
  （markdown 叙述段落平台名扫描），新 bullet 不触发护栏 1。
- consistency 实跑（本审查，`--strict-errors-only`，`timeout 180s`）：

  ```
  仅有 329 个 WARNING，无 ERROR。
  EXIT=0
  ```

  329 WARNING 全为既有叙事文件对旧文件名 / 脚本名的引述（`postmortem-template.md`、
  `check-windows-smoke.sh` 等，与本轮无关），**0 ERROR**，与 implementer 自查一致。
- `ruff check agate/scripts/agate-cmdstream-adapters.py` → `All checks passed!`（本审查实跑）。

**结论**：ALIGNED。

---

### A7: 设计原则一致性 —— ALIGNED

- **`_codex_is_finished` 抽模块级 helper**：把「Codex 真机 `status` 语义 → 是否已结束」的平台特异判断
  集中到一处，`read_commands` 消费点收敛为一行 `pending = not _codex_is_finished(...)`。这符合既有三适配器
  「**平台差异隔离在适配器内**」的架构范式（RM-AG0055 设计笔记 §3.4.4「未来接入 Codex/Cursor：约一个
  文件……检测引擎/阈值零改动」——detect.py/ir.py diff 空，兑现）。与 DEBT0035 `recommendation`
  「逻辑抽 helper 集中」一致。
- **对照 `agate/adr.md`**：
  - ADR-001（隔离性——主 Agent 不写产出）：F1 修复由 implementer subagent 落地，主 Agent 只派发 + 验
    gate，本轮 SELF-GATE 由独立上下文 review 角色执行——不违反。
  - ADR-002（可判定性）：修复未引入任何主观 gate 判据；`_codex_is_finished` 是纯函数、可单测（已覆盖）。
  - ADR-005（改动性质决定流程——声明性/行为逻辑/机制交叉）：F1 = **行为逻辑** bug 修复
    （pending 判据口径），走 P3 红灯 → P4 实现 → 评审 → gate 的行为逻辑流程；BASELINE_CHANGE 经主 Agent
    批准回写 P1/P2 基线——与 ADR-005 对「行为逻辑 + 基线修正」的流程要求一致。
  - 无 ADR 与「适配器内隔离平台差异」冲突。
- **既有非阻塞观察（r1/r2 已记，本轮延续，非新增）**：「命令流适配器模式」的架构决策仅沉淀在 RM-AG0055
  设计笔记 §3.4.4，未转为 `adr.md` 条目（同 TAG0024 / TAG0028 / TAG0032 的 A7 观察）。可酌情由 RM-AG0055
  后续补 ADR，非本任务必办、非阻塞。

**结论**：ALIGNED（A7 无 MISALIGNED 态；既有 ADR 缺口观察延续，不升级为 NEEDS_HUMAN_REVIEW——属指导性
建议、非模糊裁决点）。

---

## BASELINE_CHANGE 恰当性核查表

主 Agent 在 P1/P2 加的 `[BASELINE_CHANGE: ...]` 注记，逐条核 (a) 如实反映改动 (b) **未改 BDD 的
Given/When/Then 判定语义** (c) DEBT0035 引用正确 (d) 行内 `[BASELINE_CHANGE: 具体理由]` 格式。

| # | 位置 | 注记要点 | (a) 如实反映 | (b) BDD 判定语义未改 | (c) DEBT0035 引用 | (d) 格式 | 判定 |
|---|---|---|---|---|---|---|---|
| B1 | `P1 §4.1` `item.status` 项（`:112-117`）| 真机 `status` 取值集 = completed/failed/in_progress；`read_commands`「已结束」判据据此改口径 | ✔ 与 helper + platform-notes 三方一致；末句自注「Given/When/Then 语义不变，仅补充真机事实」 | ✔ §4.1 是**数据形态描述节**、非 BDD；未触碰任何 Given/When/Then | ✔「见 P2 §5 设计点 2 的 BASELINE_CHANGE / DEBT0035」 | ✔ 行内 | **恰当** |
| B2 | `P1 §6 BDD-5 Given`（`:295-297`）| `item.status` 从 `"completed"` 改 `"failed"`；「Given 改用真机形态，Then 判定语义不变」+ 加强断言 `ts_end`/`output_hash` 非 None | ✔ 与 fixture item-demo-2 改动、`test_bdd_5_*` 断言一致 | ✔ **BDD-5 标题未改**（「失败命令的 exit_code 非 0 如实映射，不回落 None」）；**Then 核心判定未改**（仍「`CommandRecord.exit == 2`（整数 2，非 None），`exit_signal` 留档原始形态」）；新增的 `ts_end`/`output_hash` 非 None 是**同方向加强**（证明不被误判 pending），不改判定方向 | ✔「P6 V6 实测真机已结束非 0 退出命令记 `status:"failed"`（DEBT0035）」 | ✔ 行内 | **恰当** |
| B3 | `P1 §6 BDD-6 Given`（`:304-308`）| 「`item.status != completed`」措辞收紧为「真·未结束」（有 `item_started`/`item_updated` 无 `item_completed`，且无 `completed_at_ms`/`exit_code`）| ✔ 与 helper「三信号皆缺才 pending」一致 | ✔ **BDD-6 标题未改**；**Then 逐字未改**（diff 显示 BDD-6 的 `- Then` 行无改动：「未结束命令产出 1 条 `CommandRecord`，`exit is None`、`ts_end is None`、`exit_signal == "pending"`；已完成命令记录不受影响」）；仅 Given 场景**收窄**（排除被误分类的 `failed` 情形），判定语义不变 | ✔「P6 V6 发现 `status:"failed"` 是已结束终态、不是未结束……见 P2 §5 设计点 2 BASELINE_CHANGE / DEBT0035」 | ✔ 行内 | **恰当** |
| B4 | `P2 §5 设计点 2 pending`（`:250-257`）| pending 判据从「`status != completed`」收紧为「无终态信号才算 pending」；已结束三元集；抽 `_codex_is_finished` helper | ✔ 与 `read_commands:766` + helper 逐字一致（A1-②）| ✔ 设计点 2 是**方案设计节**、非 BDD；未触碰 BDD 判定 | ✔「P6 V6 实测（DEBT0035）」+ 正文 | ✔ 行内 | **恰当** |
| B5 | `P2 §11 R3 风险行`（`:117`）| R3「未结束/pending rollout 形态」判据更新为「无终态信号才算 pending」+「P6 补真机 `status:"failed"` 样本」| ✔ 与 fixture 追加 + helper 一致 | ✔ 风险登记行、非 BDD；未触碰 BDD 判定 | ✔「P6 V6 修正，见设计点 2 BASELINE_CHANGE / DEBT0035」 | ✔ 行内 | **恰当** |

**核查结论：5 条 BASELINE_CHANGE 注记全部恰当——无实质篡改 BDD 的 Given/When/Then 判定语义。**

- BDD-5 / BDD-6 的**标题与 Then 判定方向均保持原样**；BDD-5 Then 新增的 `ts_end`/`output_hash` 非 None
  是同方向加强断言（操作化「不被误判 pending」），BDD-6 Then 逐字未动、仅 Given 场景收窄以排除
  P1 spike 取样盲区（`status:"failed"` 被误当未结束）。
- 全部注记为「授权修正」（主 Agent 已批准，P6 实测发现 spike 取样未覆盖 `failed` 终态），非实现擅自
  扩范围。DEBT0035 引用逐条正确（DEBT0035 正是该 F1 的 retreat 债务条目，`source: retreat`，
  `evidence` 引 `52fe210`）。格式均为行内 `[BASELINE_CHANGE: 具体理由]`。

---

## A3b 反向传播清单（汇总）

| 应被影响的文件 | 处理 | 状态 |
|---|---|---|
| `agate/platform-notes.md` | diff 内已加真机 `status` 取值集 bullet | ✔ 已同步 |
| `P1-requirements.md §4.1` + BDD-5/BDD-6 | diff 内已加 BASELINE_CHANGE | ✔ 已同步 |
| `P2-design.md §5 设计点 2` + §11 R3 | diff 内已加 BASELINE_CHANGE | ✔ 已同步 |
| `docs/research/cross-platform-dispatch-mechanics.md` §2.4 | 不同概念层（turn 级 model 失败 ≠ per-command shell `status:"failed"`）；L169 r2 已回写 | ✔ 无需改 |
| `agate/LIMITATIONS.md` | grep 无 Codex 适配器 / exit code 语义相关内容 | ✔ 无需改 |
| `agate-workspace/agents/CODE-MAP.md` | 本轮无新文件（helper 是模块内函数）；r2 已同步 `CodexAdapter` 条目 | ✔ 无需改 |
| `agate/adr.md` | 无 ADR 冲突（A7）| ✔ 无需改 |
| `agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` | 消费侧按契约运作，修 bug 无需动 | ✔ 零改动确认（diff 空）|
| DEBT0035 `closure_criteria` | 4/5 满足；「P5/P6 重新通过」待后续阶段（预期，非本轮遗漏）| ✔ 已知，主 Agent 后续收口 |
| `CHANGELOG.md` / 版本文件 | P8 统一处理（提示已升级为覆盖 F1 + DEBT0035）| ⏳ P8 提示 |

**A3b 无遗漏文件。**

---

## A4 pytest 实跑输出（本审查执行，非引用）

**doc-audit（A2）**：
```
$ timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q
8 passed in 0.03s
```

**全量单测（A4）**：
```
$ timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=short
1390 passed, 2 skipped in 114.16s (0:01:54)
```
**passed / failed / skipped = 1390 / 0 / 2**（与派发预期逐字吻合）。

**consistency（A6）**：
```
$ timeout 180s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
仅有 329 个 WARNING，无 ERROR.
EXIT=0
```

**ruff（A6）**：
```
$ timeout 60s ruff check agate/scripts/agate-cmdstream-adapters.py
All checks passed!
```

---

## 附：非阻塞观察（不计入 NEEDS_HUMAN_REVIEW）

1. **P8 提示（A5，升级版）**：`CHANGELOG.md` + 版本 bump 需在 P8 覆盖「新增第四命令流适配器 Codex +
   Codex 平台接入文档 + **F1 修复（`_codex_is_finished` pending 判据口径修正）+ DEBT0035**」。
2. **helper 第三分支措辞（A1，纯 cosmetic）**：`_codex_is_finished` 第三分支为
   `payload.get("completed_at_ms") is not None`（原始 `is not None`，未过 `_codex_int_or_none`）。
   极端畸形数据（`completed_at_ms` 存在但非 int，且无其它终态信号、status 未知）会被判「已结束」，但
   `_build_record` 随后 `ts_end = _codex_int_or_none(...)` → None、`exit_code` → None，detect.py CLI
   转换层 `r.exit is not None or r.ts_end is not None` 为假 → **不产 result 事件、下游行为等同 pending**，
   无检测风险。docstring 措辞「有完成时刻」与「`is not None`（非『有效 int ms』）」有轻微不精确，属
   cosmetic，**非 MISALIGNED**——`_codex_int_or_none` 在 `_build_record` 落值时才是真正的类型闸。
3. **A7 观察（r1/r2 延续）**：「命令流适配器模式」架构决策仅在 RM-AG0055 设计笔记 §3.4.4、未沉淀
   `adr.md` 条目，可酌情由该 RM 后续补 ADR，非本任务必办。

---

## 总结论

**SELF-GATE 协议-脚本语义对齐轴：PASS。**

- **A1 / A2 / A3 / A4 / A5 / A6 / A7 全部 ALIGNED**，无 MISALIGNED，无新增 NEEDS_HUMAN_REVIEW。
- `_codex_is_finished` helper 与 `platform-notes.md` 新 bullet / `P1 §4.1` / `P2 §5` BASELINE_CHANGE /
  DEBT0035 recommendation **四方逐字一致**；`agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` /
  既有三适配器 **零改动硬约束守住**（diff 实核）。
- **5 条 BASELINE_CHANGE 注记全部恰当**——如实反映改动、DEBT0035 引用正确、行内格式；BDD-5 / BDD-6 的
  **标题与 Then 判定语义均未被篡改**（BDD-5 Then 仍「exit 非 0 如实映射不回落 None」并同方向加强；
  BDD-6 Then 逐字未动，仅 Given 场景收窄排除 spike 盲区）。
- **A3b 无遗漏文件**：应同步的 3 处文档已在 diff 内；研究叙事 §2.4（不同概念层）/ `LIMITATIONS.md`
  （无相关内容）/ CODE-MAP（无文件级变更）经核实无需改。
- **A4 全量 pytest：1390 passed / 0 failed / 2 skipped**（本审查实跑，与预期逐字吻合）；consistency
  0 ERROR / EXIT 0；ruff clean。
- DEBT0035 `closure_criteria` 本轮满足 4/5，剩「P5/P6 重新通过」属后续阶段职责，DEBT0035
  `status: in_progress` 合理，待 P5/P6 绿后由主 Agent 收口。

**闭环动作**：本 SELF-GATE 第 3 轮审查即闭环，P4 重试批可 commit（commit message 须含
`self-gate-review:` 指向本报告
`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033-r3.md`）。代码 / 文档 / 基线注记
本身无需任何修订。非阻塞项：P8 覆盖 CHANGELOG + 版本 bump（含 F1 + DEBT0035）。
