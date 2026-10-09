---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 修复 TAG0050 外部实施评审 M-1（前向跨阶规则从 agate-state-set.py 下沉到 check_transition，hook 与 CI 回放共用）+ m-5（task_created.resolver 不写绝对路径）+ 非 legacy 任务 P7 缺产出拦截
files_changed:
  - agate/scripts/agate-state-set.py
  - agate/scripts/agate-task-init.py
  - agate/scripts/check-gate.py
  - agate/scripts/check-state-transition.py
  - agate/state-machine.md
  - agate/tests/integration/test_pre_commit_hook.py
---

# 协议-脚本对齐审查

**审查对象**：分支 `hotfix/M-1-state-machine`（工作区未提交，`git diff` 6 文件）。
**意图**：修复 TAG0050 外部实施评审发现的 M-1 缺陷——「非 legacy 任务的前向跨阶在提交期不受约束」（改前前向跨阶规则只写在 `agate-state-set.py` 工具路径，未进入 hook/CI 共用的纯函数 `check_transition`，故手改 `.state.yaml` 可从 P0 直跳 P7）；附带修 m-5（`task_created.resolver` 写本机绝对路径）；并附一处非 legacy 任务 P7 缺产出拦截。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | **NEEDS_HUMAN_REVIEW** |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW** |
| A8 | 声称-命令绑定 | **ALIGNED** |

> **头号问题（必须先修）**：新增的 judge 跨阶判据（`judge_crossed`）会**误伤合法的 P7 裁剪路径 P6→P8**；`check-gate.py` 的 P7 缺产出拦截**破坏 4 个既有测试**（全量 pytest 实测 4 failed 归因于本 diff）。二者都需在 commit 前修复。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

本项核对「协议文档声明的规则，脚本是否语义一致地实现」。

#### A1-1 前向跨阶主规则：ALIGNED

**文档声明**（`agate/state-machine.md:405`，本 diff 新增行）：
> 注意：**前向跨阶（delta ≥ 2）对非 legacy 任务同样由 `check_transition` 检查**……被跨过的阶段须已从 P1 `phases` 裁掉并在 `pruned` 中声明，且不得跨过不可裁剪阶段（P2/P4/P5/P6；契约要求 judge 时 P6.5 亦不可跨）。**legacy 任务维持不检查**（历史任务行为不变）。

**脚本实现**（`agate/scripts/check-state-transition.py:440-481`）：
- 触发条件（442-443）：`old_phase` 非空且非控制态、`new_phase` 非控制态、`new_num` 可解析；
- legacy 门（444-450）：`task_level(task_dir)` 为 `None` → 跳过（与「legacy 不检查」一致）；
- `delta >= 2`（450）；被跨阶段 `skipped`（451）；不可裁剪集 `_NON_PRUNABLE = {"P2","P4","P5","P6"}`（452）；
- 被跨阶段须「不在 P1 `phases`」且「在 P1 `pruned`」（464-465，`_p1_pruned_and_declared` 281-313 只读 frontmatter，不用正文正则——符合 M-1 明确要求）。

主体规则与文档一致。**以下两个子项不一致。**

#### A1-2 【MISALIGNED】judge 跨阶判据误伤合法的 P6→P8（P7 已裁剪）

**文档声明**（`agate/state-machine.md:223`，未改动）：
> 跳过 P7（无一致性检查）→ P6--[P6 gate 通过]--> P8

**文档声明**（`agate/phase-cards/P7-consistency.md:4`，未改动）：
> 裁剪跳阶 → 确认 P1 phases 不含 P7 + 源文件数 ≤5 + 无 implicit_coupling + 有 coupling_checklist……→ 跳过，读 P8 卡片

**脚本实现**（`check-state-transition.py:454-459`）：
```python
if requirement_active is not None and requirement_active(task_dir, "judge", "P7"):
    judge_crossed = old_num <= 6 and new_num >= 7
```
`check-pruning.py:259-273` 对「裁剪 P7」只校验源码文件数 / `implicit_coupling` / `coupling_checklist`——**不因 judge 生效而禁止裁 P7**。因此一个**合法裁剪了 P7 的 judge 任务**，其唯一合法推进边就是 `P6→P8`（`state-machine.md:223`），但 `judge_crossed`（`old_num=6<=6 and new_num=8>=7`）会把它判为「跨 P6.5」而拦截。

**实测**（只读 scratch，`/tmp/opencode/m1scratch`，未触碰真实仓库）：
```
AGATE_ROOT=<checkout>/agate
requirement_active(task, "judge", "P7") = True
check_transition("P6","P8", task{phases:[P1,P2,P3,P4,P5,P6,P8], pruned:[P7]})
  → ['前向跨阶 P6→P8 被拒绝（被跨过：P7）：契约要求 judge（P6.5 不可跨）……']
```

**差异**：代码把「跨 P6.5」判为「`old_num<=6 且 new_num>=7`」，但 P6.5 是**挂在 P6→P7 转移上的子阶段**（`state-machine.md:74-78/152-155`），phase 保持 P6；当 P7 已裁剪时，`P6→P8` 正是承载 P6.5 的那条边。`judge_crossed` 无法区分「P6.5 尚未做」与「P6.5 已做、现去 P8」，于是**无条件拦截**——使合法裁剪 P7 的任务无路可走（`check-pruning` 放行、`check_transition` 堵死）。commit-time 的 judge 硬边界（`pre-commit-gate.py:956-961`）已单独校验 `P6.5-judge-verdict.md`，此判据属**过度拦截**。

**建议方向**（择一，由主 Agent/设计定）：
1. `judge_crossed` 增加「`P6.5-judge-verdict.md` 不存在」才拦的条件（把判据对齐 commit-time 硬边界）；
2. 或明确「judge 生效时 P7 不可裁剪」，并**同步** `check-pruning.py` 拒绝该组合（否则两脚本互相矛盾）；
3. 至少补一条 `P6→P8`（P7 已裁剪、judge 生效）的合法路径回归用例——当前**零覆盖**。

#### A1-3 【MISALIGNED】不可裁剪集漏 P1

**文档声明**（`agate/state-machine.md:226`，未改动）：
> 不可跳过的阶段：P1（需求基线）、P2（方案设计）、P4（实现）、P5（技术验证）、P6（验收）

**文档声明**（`agate/WORKFLOW.md:239`，未改动）：
> **核心阶段（不可跳）**：P1 需求基线、P2 方案设计、P4 实现、P5 技术验证、P6 验收、P6.5 独立 Judge 复核

**文档声明**（`agate/phase-cards/P1-requirements.md:4`）：
> P1 不可裁剪（核心阶段）

**脚本实现**（`check-state-transition.py:452`）：
```python
_NON_PRUNABLE = {"P2", "P4", "P5", "P6"}
```
`_NON_PRUNABLE` 与 `state-machine.md:202-208`「裁剪条件」节（只列 P2/P4/P5/P6）一致，但**漏掉 P1**——而 `226` / `WORKFLOW.md:239` / `phase-cards/P1` 三处都把 P1 列为不可裁/不可跳。后果：一个 `old_phase=P0` 的任务，若在 P1 `phases` 里移除 P1 并把它写进 `pruned`，`check-pruning.py:199-227` 的闭包（`declared ∪ pruned == phase_universe`，`phase_universe=[P1..P8]`，`level-1.yaml:36`）**不会拒绝**（该脚本未禁裁 P1），于是 `check_transition` 的 `still_declared`/`not_pruned` 两闸也都不命中 → `P0→P2` 放行。这正是 M-1 想堵的「手改 .state.yaml 跳阶段」的一个残留口。

**同时**：新增的 `state-machine.md:405` 写「不可裁剪阶段（P2/P4/P5/P6）」，与**同一文档** `226` 行的 P1 表述冲突（同文档内不自洽）。

**建议方向**：`_NON_PRUNABLE` 补 `"P1"`；并核对 `state-machine.md:405` 的列举与 `226` 行统一（要么都含 P1，要么说明 P1 的「不可跳」由别的机制承担）。

---

### A2: 脚本→文档对齐 — MISALIGNED

#### A2-1 【MISALIGNED】`check-gate.py` 新增「非 legacy 任务 P7 缺产出 → return 1」破坏 4 个既有测试

**脚本实现**（`agate/scripts/check-gate.py:1834-1838`，本 diff 新增）：
```python
def _gate_p7_structured(task_dir, p7_file):
    """非 legacy 任务的 P7 成对声明判据（设计 §6，含 F2）。返回 gate 退出码。"""
    if not os.path.isfile(p7_file):
        sys.stderr.write("GATE P7: P7-consistency.md 不存在（非 legacy 任务须有 P7 产出）\n")
        return 1
```
`gate_p7` 仅在 `task_level(task_dir) is not None` 时调用 `_gate_p7_structured`（`check-gate.py:1993-1995`），故对 legacy 任务无影响（风险面 4 的「只影响非 legacy 分支」**成立**）。

**问题**：4 个既有测试用 `init_task_via_conftest`（`conftest.py:263`，**不建 `P7-consistency.md`**）构造任务，再直接调 `check-gate.py P7 <task>`，期望到达 `design_gap_reviews` 的 `verdict`/`basis`/集合校验（这些校验读 P4 跨文件声明）。新早退**先于**这些校验触发，使测试拿到「P7-consistency.md 不存在」而非期望的「verdict 越界 / basis 越界 / 悬空」错误。

全量 pytest 实测（见 A4）失败清单：
- `test_tag0050_declarations.py::test_bdd_62_cross_file_declaration_aggregation`
- `test_tag0050_declarations.py::test_bdd_64_set_mismatch_or_dangling_errors`
- `test_tag0050_declarations.py::test_minor4_verdict_enum_out_of_range_errors`
- `test_tag0050_declarations.py::test_minor4_basis_enum_out_of_range_errors`

**差异**：脚本行为变更未同步更新其测试契约（这 4 个用例的判别面是「P4 跨文件声明校验」，与「P7 产出存在性」正交）。注：设计对「缺产出假 PASS」的既定修复是 `check-gate.py:2404-2409` 的 **main() 单点早检**（TAG0050 A0 §10 G1），本 diff 另在 `_gate_p7_structured` 内加了一道**更早**的出口，与既有设计落点不重合。

**建议方向**：或为这 4 个用例补最小 `P7-consistency.md`（使其仍能到达各自判别面），或把「P7 产出存在性」判定移到不与 `design_gap_reviews` 校验抢跑的位置。

#### A2-2 【MISALIGNED】`state-machine.md:405` 与同文档 `226` 行不自洽

见 A1-3。新增行把不可跨集写作「P2/P4/P5/P6」，与 `226` 行「不可跳过阶段：P1、P2、P4、P5、P6」冲突。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（连锁：diff 内的衍生改动）**：`agate-state-set.py` 删除自带前向规则、改为复用 `check_transition`（`agate-state-set.py:51-57,162-182`），与 `state-machine.md:411-413`「推荐用 state-set 使工具判定与提交判定一致」一致——**ALIGNED**（也符合 ADR-014 判据单源：前向判据从两处收敛到一处）。

**A3b（反向传播：应被影响但未出现在 diff 的文件，逐一验证）**

| 应被影响文件 | 现状 | 判定 |
|---|---|---|
| `agate/state-machine.md` | 已改 `405` 行；但 `223`（P6→P8 合法）与 `226`（P1 不可跳）未随语义对齐 | **未闭合**（见 A1-2/A1-3） |
| `agate/phase-cards/P7-consistency.md:4` | 仍写「裁剪 P7 → 跳过，读 P8 卡片」，与 `judge_crossed` 冲突 | **未同步** |
| `agate/phase-cards/P1-requirements.md:4` | 「P1 不可裁剪」——与 `_NON_PRUNABLE` 漏 P1 冲突 | **未同步** |
| `agate/rules/state-transitions.md` | 「回退规则」表只覆盖回退方向，**无前向跨阶条目**（该文件自称「提取跨阶段共用的转移规则」，权威源 `state-machine.md`） | **未传播**（摘要文件，建议补一行前向条目或明确「前向见 state-machine.md」） |
| `agate/WORKFLOW.md` | `239` 列 P1 为不可跳；无前向跨阶执行说明 | 与 A1-3 联动 |
| `agate/dispatch-protocol.md` | `1116-1117` 只讲裁剪理由审查，不涉前向执行 | 无需改 |
| `agate/orchestrator-template.md` | 只指向 `state-machine.md`（`:59/:116`） | 无需改 |
| `agate/scripts/README.md:77` | `check-state-transition.py` 条目为泛述「状态转移合法性 + 重试上限」 | 可选（不必逐一列规则） |
| `agate/tests/README.md:60/86` | 映射未变 | 无需改 |
| `CHANGELOG.md:11` `[Unreleased]` | **空**——协议语义变更未标注 | **未传播**（见 A5） |
| `agate/UPGRADING.md` | 未新增章节 | **未传播**（见 A5） |
| CHECK 9 锚点表 | 无「前向跨阶」锚点 | 见 A6 |

**结论**：反向传播**多处未闭合**（`phase-cards/P7`、`phase-cards/P1`、`state-machine.md:223/226`、`rules/state-transitions.md`、`CHANGELOG.md`）。

**关于 TAG0050 已接受偏离（原则 6 核查）**：`agate-workspace/tasks/TAG0050-task-data-contract/P7-consistency.md:66-67` 有已接受的 DESIGN_GAP：
> [DESIGN_GAP: A3 的 `agate-state-set phase` 对前向跨阶（delta≥2）从严拒绝，该规则只在 state-set 生效、不加入 `check_transition`（否则破坏既有前向跳用例）]
> [DESIGN_GAP_REVIEWED: verdict=accepted; …; basis=in_bdd; BDD-36 PASS]

本 diff **正是反转这条已接受偏离**。其接受理由「否则破坏既有前向跳用例」实为「既有用例把缺陷固化为期望」（diff 已把 `test_it9_pruning_skip_low_passes` 的 `P2→P5` 改为 `P2→P4`）。因此本改动**不应**按「已知偏离」放过——它是被外部评审证伪的偏离，属正当修复；但需注意 TAG0050 的 P7 记录现已**过时**（依 `adr.md` 复审触发条件，应留痕说明该 DESIGN_GAP 被 M-1 取代，frozen 快照可不回改，但应在 retrospective/roadmap 留痕）。

---

### A4: 测试覆盖 — MISALIGNED

**最近一次全量 pytest 实跑**（只读，工作区未污染，`git status` 与运行前一致）：
```
$ python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
5 failed, 2865 passed, 2 skipped, 5 rerun in 84.89s (0:01:24)
```
失败清单：
```
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED agate/tests/unit/test_tag0050_declarations.py::test_bdd_62_cross_file_declaration_aggregation
FAILED agate/tests/unit/test_tag0050_declarations.py::test_bdd_64_set_mismatch_or_dangling_errors
FAILED agate/tests/unit/test_tag0050_declarations.py::test_minor4_verdict_enum_out_of_range_errors
FAILED agate/tests/unit/test_tag0050_declarations.py::test_minor4_basis_enum_out_of_range_errors
```
**归因**：
- 后 4 个**由本 diff 引入**（`check-gate.py:1836` 早退先于 `design_gap_reviews` 校验；见 A2-1）。
- `test_bdd_43` 为**环境/工具版本**问题（`opencode debug agent` 子命令在本机 opencode CLI 不存在：`Unknown subcommand "agent" for "opencode debug"`），与本 diff 无关，**不计入本改动**。

**新增测试（`test_pre_commit_hook.py:896-1023`）**：`test_it9_pruning_skip_low_passes` 改为 `P2→P4`（只跳已裁 P3）✓；新增 `test_m1_forward_jump_p0_to_p5_blocked` / `_p0_to_p7_blocked` / `_p2_to_p5_blocked` ✓（全量跑通过）。这三条覆盖了 `non_prunable` 与 `still_declared` 分支。

**覆盖缺口**：
1. **`judge_crossed` 分支零覆盖**——无 `P6→P8`（P7 裁剪、judge 生效）用例；正因无覆盖，A1-2 的误伤未被任何测试发现。
2. **`_gate_p7_structured` 缺文件分支无专门用例**（且其副作用使 4 个既有用例转红）。
3. **legacy 任务经 `agate-state-set` 的前向跨阶行为变更无覆盖**（见 A5）。
4. **`_resolver_label()` 无单测**（空 `AGATE_ROOT` / 有 `AGATE_HOME` / 无 `AGATE_HOME` / 非父路径各分支）。

**边界行为核查（风险面 1）**：
- `old_phase` 空（`--adopt`/首次写入）：`442` 的 `old_phase and ...` 为假 → 跳过检查 5 ✓；
- 控制态：`new_phase ∈ {PAUSED, READY, DONE}` 已在 `363-388` 提前 `return`，`old_phase ∈ 控制态` 时 `442` 为假 → 跳过 ✓；
- `old_num=0`（P0）：`442` 通过（"P0" 非空非控制），`450` 用 `phase_num("P0")=0`，`skipped={P1..}` → 正确纳入 ✓；
- legacy（`test_st_3_forward_jump_p1_to_p3_exit_0`，P1→P3 跨 P2）：任务无 `gate-events.jsonl` → `task_level=None` → 检查 5 跳过 → 仍 exit 0 ✓（全量跑通过，未在失败清单）。

**风险面 3 核查**：`agate-state-set` 既有用例期望（`test_tag0050_state_set.py` BDD-36 `P4→P8` 被拒 / READY / DONE）——新共用函数 `check_transition` 覆盖：`P4→P8` 跨 P5/P6（`_NON_PRUNABLE`）→ 拒 ✓；READY/DONE 前序校验（`363-385`）✓。全量跑该文件**通过**。

**结论**：MISALIGNED（既有测试转红 + 新分支零覆盖）。

---

### A5: 下游影响 + 文档传播 — MISALIGNED

**破坏性/行为变更**：
1. **非 legacy 任务**：改前 `check_transition` 不检查前向跳，改后拦截——这是 M-1 的**预期**变更，但属 gate 行为收紧，存量在途非 legacy 任务若曾合法做「裁剪跳阶」需重新核对（尤其 A1-2 的 `P6→P8` 会被误拦）。
2. **legacy 任务经 `agate-state-set` 的前向跨阶**：改前 `agate-state-set._forward_multi_jump_error` **不判 `task_level`**（legacy 也拦）；改后共用 `check_transition` 的检查 5 **只对非 legacy**生效 → legacy 任务经 state-set 做前向跨阶由「拦」变「放行」。此行为变更**无测试、无文档**说明（`state-machine.md:405` 只声明「legacy 任务维持不检查」，未区分「提交期」与「工具期」两个通道）。

**文档传播缺口**：
- `CHANGELOG.md:11` `## [Unreleased]` **为空**——本批含协议语义变更（新 gate 拦截 + resolver 字段语义），按反向传播表「协议语义变更 + 未标注 = A5 不完整」应补条目。
- `agate/UPGRADING.md` 未新增章节说明前向跨阶收紧与 `resolver` 语义变化（存量项目升级前会读此文件）。

**结论**：MISALIGNED（CHANGELOG/UPGRADING 未传播 + legacy state-set 行为变更未留痕）。

---

### A6: 锚点表覆盖 — NEEDS_HUMAN_REVIEW

**现状**（`check-protocol-consistency.py:608-622`）：`check-state-transition.py` 已有 3 条锚点——「重试上限检查(MAX_RETRY)」「回退跳变检测(diff, phase_num)」「门槛失败事件↔retries 对应性(RM-AG0042)」。**无「前向跨阶」锚点**。`check_anchor_coverage`（`928`）按脚本粒度判覆盖，`check-state-transition.py` 已被覆盖，故**不触发机械 WARNING**。

**判断**：新增了一条实质协议规则（前向跨阶拦截），与既有「回退跳变检测」锚点**对称**，建议补一条 `keywords: ["前向跨阶"]` 锚点，使「规则存在于脚本」可机械守护。是否必须补属团队取舍（非机械门禁强制），故记 **NEEDS_HUMAN_REVIEW**。

**[HUMAN_CONFIRMED: 待人工确认——是否为本规则补 CHECK 9 锚点]**

---

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

逐条核对相关 ADR（`agate/adr.md`）：

| ADR | 相关性 | 判定 |
|---|---|---|
| ADR-002 可判定性 | 前向跨阶判据机器可判定（`check_transition` 纯函数、exit code） | **ALIGNED** |
| ADR-014 判据单一权威源 | 前向判据从 `agate-state-set.py` + `check_transition` 两处**收敛为一处**（删 state-set 自带规则） | **ALIGNED**（正面改进） |
| ADR-011 引导型工具非安全边界 | 前向判据下沉到 hook/CI 共用的 gate，正合「真正边界在 gate 链」 | **ALIGNED** |
| ADR-015 门禁只用于「会导致后续错误决策」的错误；优先「让错误不可能」 | `judge_crossed`（A1-2）**拦截了合法路径**（P7 裁剪的 P6→P8），属「加错门禁」——会把「合法推进」变成「红叉 + 绕过」，与 ADR-015 精神相抵 | **NEEDS_HUMAN_REVIEW** |
| ADR-004 安全网分层 | 前向判据进入 hook/CI 共用函数，正合多层防线 | **ALIGNED** |

**结论**：NEEDS_HUMAN_REVIEW（`judge_crossed` 的过度拦截是否可接受，需人工裁决；其余 ALIGNED）。

**[HUMAN_CONFIRMED: 待人工确认——`judge_crossed` 与 ADR-015「门禁只拦实质错误」的张力]**

---

### A8: 声称-命令绑定 — ALIGNED

逐条列本批的**结论类声称**及其产出命令：

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | 「前向跨阶规则改前只在 `agate-state-set.py`，未进入 `check_transition`」（`test_pre_commit_hook.py:932-933`） | `git show HEAD:agate/scripts/agate-state-set.py \| grep -n _forward_multi_jump_error`（命中 161/218）＋ `git show HEAD:agate/scripts/check-state-transition.py \| grep -n 前向`（空） | 成立 |
| 2 | 「原用例 `P2→P5` 把缺陷固化为期望」（`test_pre_commit_hook.py:896-897`） | `git show HEAD:agate/tests/integration/test_pre_commit_hook.py \| grep -n "skip to P5"`（命中 901） | 成立 |
| 3 | 「前向跨阶（delta ≥ 2）对非 legacy 任务由 `check_transition` 检查」（`state-machine.md:405`） | `grep -n "前向跨阶" agate/scripts/check-state-transition.py`（命中 476）＋ A1 实测 `check_transition("P0","P8",…)` 非空 | 成立 |
| 4 | 「不得跨过不可裁剪阶段（P2/P4/P5/P6）」（`state-machine.md:405`） | `grep -n "_NON_PRUNABLE" agate/scripts/check-state-transition.py`（命中 452） | 成立（但与 `226` 行 P1 表述冲突，见 A1-3） |
| 5 | 「契约要求 judge 时 P6.5 亦不可跨」（`state-machine.md:405`） | `grep -n "judge_crossed" agate/scripts/check-state-transition.py`（命中 454-459）＋ A1-2 实测 | 成立（但过度拦截，见 A1-2） |
| 6 | 「legacy 任务维持不检查」（`state-machine.md:405`） | `grep -n "task_level" agate/scripts/check-state-transition.py`（444-449）＋ `test_st_3` 全量跑通过 | 成立 |
| 7 | 「非 legacy 任务须有 P7 产出」（`check-gate.py:1837` 消息） | `grep -n "P7-consistency.md 不存在" agate/scripts/check-gate.py`（命中 1837） | 成立 |
| 8 | 「`_resolver_label` 不记绝对路径」（`agate-task-init.py:82-83`） | 只读实测：`AGATE_ROOT=/home/kity/.agate/v0.80.1/agate` → `'agate'`；`+AGATE_HOME` → `'v0.80.1/agate'`（无绝对路径） | 成立（但见 A5/A4 注记：无 `AGATE_HOME` 时退化为 `'agate'`，丢版本上下文） |

**无据声称**：未发现需删除的无据声称。**结论：ALIGNED**。

---

## 附：风险面专项核查结论（任务点名 5 项）

1. **检查 5 边界**：`old_phase` 空 / 控制态 / `old_num=0` / legacy 各自行为**正确**（见 A4 边界核查）；`test_st_3` 仍通过。**唯一问题**是 `judge_crossed` 的 P6→P8 误伤（A1-2）。
2. **不可裁剪集与裁剪表**：`_NON_PRUNABLE={P2,P4,P5,P6}` 与 `state-machine.md:202-208` 一致，但**漏 P1**（`226`/`WORKFLOW.md:239`/`phase-cards/P1` 均列 P1 不可裁）；`requirement_active(task_dir,"judge","P7")` 判据在 `AGATE_ROOT` 正确设置时返回 `True`（实测），语义可用，但用其驱动的 `judge_crossed` 过宽（A1-2）。
3. **`agate-state-set` 既有期望**：`P0→P8`（实为 `init_task` 的 `P4→P8`）/ READY / DONE 被拒均由共用 `check_transition` 保证，全量跑通过（A4）。
4. **`_gate_p7_structured` 缺文件 `return 1`**：**只在非 legacy 分支**被调用（`gate_p7:1993-1995`），legacy 走 `_md_field_get` 旧路径不受影响——**不影响合法 legacy 路径**；但会**破坏 4 个既有非 legacy 测试**（A2-1/A4）。
5. **`_resolver_label()` 边界**：空 `AGATE_ROOT`→`""`；有 `AGATE_ROOT` 无 `AGATE_HOME`→`basename="agate"`（丢版本）；`AGATE_HOME` 为父目录→`"vX.Y.Z/agate"`；非父路径→回退 `"agate"`；Windows 经 `replace(os.sep,"/")` 归一（未实测 Windows，逻辑无绝对路径泄漏）。**已消除绝对路径泄漏**，但典型 hook 运行不设 `AGATE_HOME`，字段多为 `"agate"`，调试价值下降——建议改用 `AGATE_ROOT` 父目录名参与（如 `vX.Y.Z/agate`）。

---

## 闭环建议（按优先级）

| 优先级 | 项 | 动作 |
|---|---|---|
| P0 | A2-1 / A4 | 修 `check-gate.py` 早退或补 4 个用例的 `P7-consistency.md`，使全量 pytest 转绿 |
| P0 | A1-2 | 修 `judge_crossed`（对齐 commit-time 硬边界 / 或明确禁裁 P7 并同步 `check-pruning`），补 `P6→P8` 合法路径用例 |
| P1 | A1-3 / A2-2 | `_NON_PRUNABLE` 补 P1；统一 `state-machine.md:405` 与 `226` 的列举 |
| P1 | A3 | 同步 `phase-cards/P7`、`phase-cards/P1`、`rules/state-transitions.md`（前向条目） |
| P1 | A5 | 补 `CHANGELOG.md` `[Unreleased]`；`UPGRADING.md` 说明行为收紧；留痕 legacy state-set 行为变更 |
| P2 | A4 | 补 `_resolver_label` 单测、`_gate_p7_structured` 缺文件单测 |
| P2 | A6/A7 | 人工确认是否补 CHECK 9 前向锚点、`judge_crossed` 与 ADR-015 的张力 |

**注**：本报告为**只读**审查，未修改任何协议/脚本/测试文件，未 commit。留痕文件见 `docs/reviews/agate-alignment-2026-10-09-HOTFIX-M1-01.progress.md`。
