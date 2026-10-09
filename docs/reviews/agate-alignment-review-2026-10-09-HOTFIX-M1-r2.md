---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: HOTFIX/M-1-state-machine 第 2 轮复审——前向跨阶判据收敛到 check_transition（含 P1 不可裁）、非 legacy 缺 P7 产出拦截、resolver 去绝对路径；第 1 轮 P0-1/P0-2/P0-3 均已修
files_changed:
  - CHANGELOG.md
  - agate/rules/state-transitions.md
  - agate/scripts/agate-state-set.py
  - agate/scripts/agate-task-init.py
  - agate/scripts/check-gate.py
  - agate/scripts/check-state-transition.py
  - agate/state-machine.md
  - agate/tests/integration/test_pre_commit_hook.py
  - agate/tests/unit/test_check_state_transition.py
  - agate/tests/unit/test_tag0050_declarations.py
---

# 协议-脚本对齐审查（第 2 轮）

**审查对象**：分支 `hotfix/M-1-state-machine`（工作区未提交，`git diff` 10 文件；第 1 轮为 6 文件）。
**意图**：修复 TAG0050 外部实施评审 M-1（非 legacy 任务前向跨阶在提交期不受约束）+ m-5（`resolver` 写绝对路径）+ 非 legacy 缺 P7 产出拦截。第 1 轮报告见 `agate-alignment-review-2026-10-09-HOTFIX-M1.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（含 1 处残余不对称，见 A1-3） |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（含 1 条留痕建议，见 A3b） |
| A4 | 测试覆盖 | **ALIGNED**（全量实跑：1 failed[环境] / 2872 passed；含 3 处覆盖缺口建议） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（UPGRADING 延后至发布可接受，含 1 条措辞建议） |
| A6 | 锚点表覆盖 | **NEEDS_HUMAN_REVIEW** |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW** |
| A8 | 声称-命令绑定 | **ALIGNED** |

> **与第 1 轮对比**：第 1 轮的 3 个 P0（P0-1/P0-2/P0-3）**均已修复并经独立验证**（见下节）。第 1 轮 A1/A2/A4/A5 的 MISALIGNED 已闭合；A6/A7 的两条人工裁决项**部分保留**（A6 未补锚点；A7 的 `judge_crossed` 张力已消除，但新出现一处「不可裁剪集」判据双份）。

---

## 第 1 轮 P0 逐条核实结论（独立验证，不采信作者说法）

### P0-1：`_gate_p7_structured` 缺 `P7-consistency.md` 早退 `return 1` —— ✅ 已修

- **代码**（`agate/scripts/check-gate.py:1836-1838`）：早退已就位：
  ```python
  if not os.path.isfile(p7_file):
      sys.stderr.write("GATE P7: P7-consistency.md 不存在（非 legacy 任务须有 P7 产出）\n")
      return 1
  ```
  调用点 `gate_p7:1994-1995` 仅 `task_level(task_dir) is not None`（非 legacy）时进入 `_gate_p7_structured`；legacy 走 `_md_field_get` 旧路径，**不受影响**。
- **测试**：4 个第 1 轮失败用例（`test_tag0050_declarations.py` 的 bdd_62/bdd_64/minor4_verdict/minor4_basis）已补最小 P7 产出（`:41`、`:74`、`:138`）。实跑该文件 + `test_check_state_transition.py` → **72 passed**。
- **早退语义仍生效（实测，scratch 一次性副本，未污染仓库）**：
  - 非 legacy + 无 `P7-consistency.md` → `check-gate.py P7` **rc=1**，stderr `P7-consistency.md 不存在（非 legacy 任务须有 P7 产出）`；
  - 非 legacy + 最小 P7 → **rc=0**（`成对声明聚合判据通过`）。
- **回归风险核查（P7 已裁剪任务）**：`pre-commit-gate.py:540-565` 的规则 7「按被暂存产出所属阶段重跑 gate」只对**暂存的 `P[0-8]-*.md`** 重跑（`_staged_output_phases`）。P7 已裁剪的任务不产出 `P7-*.md`、phase 走 P6→P8，**永不触发 gate_p7**；若遗留陈旧 `P7-*.md` 则由 `check-pruning.py` 检查 9（P2.9）拦截。**无回归**。
- **结论**：P0-1 **RESOLVED**。覆盖缺口：缺文件分支仍**无专门用例**（见 A4）。

### P0-2：`judge_crossed` 误伤合法 `P6→P8`（P7 已裁剪）—— ✅ 已修

- **代码**：`check-state-transition.py` 已**无** `judge_crossed`、**无** `requirement_active` 导入（`grep` 命中 0）。检查 5（`:439-476`）只判 `_NON_PRUNABLE` / `still_declared` / `not_pruned`。
- **P6→P8 放行（实测）**：`check_transition("P6","P8", task{phases 含 P6/P8, pruned 含 P7})` → `ALLOWED`；单测 `test_st_3b`（此前零覆盖）通过。
- **「不存在跨过 P6.5 而不跨 P6 的路径」核查**：P6.5 是**挂载于 P6→P7 的强门槛子阶段**、`.state.yaml` phase 保持 P6（`state-machine.md:74-78/151-155`）。因 P6 ∈ `_NON_PRUNABLE`，任何进入 ≥P7 的转移必从 P6 出发（`P5→P7`/`P5→P8` 跨 P6 → 实测被拒）。故前向判据**不需要**处理 P6.5——P6.5 由 `check-gate.py P6.5`（`gate_p65:1727-1759`）+ `agate-next._p6_judge_advance`（`agate-next.py:256-296`）+ commit-time 硬边界（`pre-commit-gate.py:951-961`）单独承载。**删除 `judge_crossed` 不产生 P6.5 绕过面。**
- **结论**：P0-2 **RESOLVED**。

### P0-3：`_NON_PRUNABLE` 漏 P1 —— ✅ 已修（含 1 处残余，见 A1-3）

- **代码**（`check-state-transition.py:455`）：`_NON_PRUNABLE = {"P1", "P2", "P4", "P5", "P6"}`。
- **P0→P2（裁 P1）被拦（实测）**：`check_transition("P0","P2", …)` → `前向跨阶 P0→P2 被拒绝（被跨过：P1）：不可跳过阶段 P1…`。
- **文档同步**：`state-machine.md` 删除「跳过 P2（无设计阶段）→ P1--[P1 gate]-->P3/P4」与「跳过 P6（无验收）→ P5--[P5 gate]-->P7」两行；PAUSED 举例改为「声明跳过 P3 但 P4 gate 发现仍需红灯变绿」。
- **删两行是否正确（点名核查）**：**正确**。`check-pruning.py:233-253` 检查 2/3/4/5 对 P2/P4/P5/P6 一律「不可裁剪（无例外口）」；`WORKFLOW.md:239`「核心阶段（不可跳）：P1/P2/P4/P5/P6/P6.5」；`phase-cards/P1:4`「P1 不可裁剪」。**无任何其它机制允许跳过 P2/P6**（`change_type: refactor` 的 P6 是「换口径 ≠ 裁 P6」）。原两行与同文档「裁剪条件」块及 `check-pruning` 冲突，属陈旧条目。
- **文档块与 `check-pruning.py` 一致性**：`state-machine.md:201-208`「裁剪条件（hook 验证，见 check-pruning.py）」列 P2/P3/P4/P5/P6/P7/P8 → 与 `check-pruning.py` 检查 2-9 逐条对应；「可跳过的阶段」块（`:218-222`）现只列 P3/P7/P8 → 与 `check-pruning` 允许裁剪集（P3 low-risk、P7 条件、P8 internal_only）一致。**一致**。
- **结论**：P0-3 **RESOLVED**。残余：`check-pruning.py` 本身**不校验 P1 裁剪**（见 A1-3）。

### 第 1 轮非 P0 项核实

| 项 | 修法 | 核实结论 |
|---|---|---|
| A3 反向传播 | 新增 `rules/state-transitions.md`「前向跨阶规则」节（`:89-96`）+ `CHANGELOG.md [Unreleased]`（`:15-25`） | ✅ 已补；内容与脚本语义一致 |
| A5 legacy state-set 前向跳由拦变放行 | `state-machine.md:403` 注明「与 hook 统一为同一判据（判据单源）」 | ✅ 已注明；仍无单测（见 A4） |
| m-5 `_resolver_label` | 「AGATE_HOME 相对路径 → 版本目录+basename → basename」 | ✅ 实测无绝对路径泄漏，且保留版本上下文（`v0.80.1/agate`） |
| 新增单测 st_3a/3b/3c | P2→P4 放行 / **P6→P8 放行** / P2→P5 拦截 | ✅ 全部通过；st_3b 填补第 1 轮指出的「零覆盖」 |
| UPGRADING 延后至发布 | 本次不加版本节 | ✅ **可接受**（见 A5；CHECK 13 通过），但 CHANGELOG「详见 agate/UPGRADING.md」当前悬空 |

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

#### A1-1 前向跨阶主规则 — ALIGNED

**文档声明**（`agate/state-machine.md:403`）：
> 注意：**前向跨阶（delta ≥ 2）对非 legacy 任务同样由 `check_transition` 检查**……被跨过的阶段须已从 P1 `phases` 移除并在 `pruned` 中声明，且不得跨过**不可跳过的阶段**（P1/P2/P4/P5/P6，见上文「阶段跳过转移规则」）。**legacy 任务维持不检查**……

**文档声明**（`agate/rules/state-transitions.md:91-96`）：同口径 + 列举合法前向跳 `P2→P4`、`P6→P8`。

**脚本实现**（`agate/scripts/check-state-transition.py:439-476`）：
- 触发条件（`:441-442`）：`old_phase` 非空且非控制态、`new_phase` 非控制态、`new_num` 可解析；
- legacy 门（`:443-449`）：`task_level(task_dir)` 为 `None` → 跳过；
- `delta >= 2`（`:449`）、被跨集 `skipped`（`:450`）、`_NON_PRUNABLE={"P1","P2","P4","P5","P6"}`（`:455`）；
- 三闸（`:456-462`）：`non_prunable` / `still_declared`（skipped ∩ P1 `phases`）/ `not_pruned`（skipped − P1 `pruned`）；
- `_p1_pruned_and_declared`（`:280-312`）**读结构化 frontmatter**（`split_frontmatter`），不用正文正则。

**形态覆盖（实测）**：块式 `phases` + 内联 `pruned`、内联 `phases` + 空格串、无 frontmatter → `(None,None)`（fail-closed 拦截）。**两种形态均覆盖**，满足 M-1「读结构化 frontmatter」要求。

**结论**：ALIGNED。

#### A1-2 `check-gate.py` P7 缺产出拦截 — ALIGNED

**文档声明**：`WORKFLOW.md:359`（check-gate P7 判定面）+ `state-machine.md` P7 转移条件；非 legacy 任务的 P7 产出为 `P7-consistency.md`。
**脚本**（`check-gate.py:1836-1838` + `gate_p7:1994-1995`）：非 legacy 缺文件 → exit 1；legacy 路径不变。
**结论**：ALIGNED（早退落在 `_gate_p7_structured` 内、仅非 legacy 分支，与「非 legacy 须有 P7 产出」一致）。

#### A1-3 残余不对称：`check-pruning.py` 不校验 P1 裁剪 — 见 A3b 说明

`phase-cards/P1:4` 声明「P1 不可裁剪」，但 `check-pruning.py` 的检查 2-5 只覆盖 P2/P4/P5/P6，**无 P1 项**（实测：`pruned:[P1,P3]`（low）→ `check-pruning.py` **rc=0**）。P1 的不可裁**只在转移期**由 `check_transition._NON_PRUNABLE` 兜底（`P0→P2` 被拒）。即：**一个「声明裁 P1」的非法声明能通过裁剪校验，只在推进时撞墙**。

- 这**不是**「文档声明 check-pruning 校验 P1 而脚本没做」的直接矛盾（`state-machine.md:201-208` 的「hook 验证」块确实未列 P1），故 A1 主结论仍 ALIGNED；
- 但按 ADR-014「判据单源」精神，P1 的不可裁应在**裁剪声明期**就机械拒绝（更早、报错更清晰）。**建议**：`check-pruning.py` 增一条「P1 不可裁剪」检查（或把不可裁集下沉到契约 `level-1.yaml`，两脚本共读——见 A7）。

### A2: 脚本→文档对齐 — ALIGNED

- 新增脚本逻辑（前向跨阶三闸 + P1 不可裁 + P7 缺产出拦截）均已在 `state-machine.md:403`、`rules/state-transitions.md:89-96`、`CHANGELOG.md:15-25` 同步；`state-machine.md` 陈旧条目已删。第 1 轮 A2-1/A2-2 已闭合。
- `agate-state-set.py` 删除自带 `_forward_multi_jump_error`/`_declared_phases`（`:141-180`），改复用 `check_transition`；无悬挂引用（`grep` 命中 0），`re` 仍被 `_PHASE_RE` 使用（ruff 全绿）。
- 结论：ALIGNED。

### A3: 一致性连锁 + 反向传播 — ALIGNED

**A3a（连锁）**：`agate-state-set.py` 前向判据从「自带副本」收敛到 `check_transition` 单源（`agate-state-set.py:174-182` 删除 `fwd` 分支），符合 ADR-014 判据单源。ALIGNED。

**A3b（反向传播：应被影响但未在 diff 的文件，逐一验证）**

| 应被影响文件 | 现状 | 判定 |
|---|---|---|
| `agate/rules/state-transitions.md` | 已新增「前向跨阶规则」节（`:89-96`） | ✅ 已闭合（第 1 轮缺口） |
| `CHANGELOG.md` `[Unreleased]` | 已补 3 条（M-1 / P7 缺产出 / resolver） | ✅ 已闭合（第 1 轮缺口） |
| `agate/phase-cards/P7-consistency.md:4` | 「裁剪跳阶 → 确认 P1 phases 不含 P7 + 源文件数≤5 + 无 implicit_coupling + 有 coupling_checklist」——与 `check-pruning` 检查 7 及**现放行的 P6→P8** 一致 | ✅ 已一致（`judge_crossed` 删除后不再冲突） |
| `agate/phase-cards/P1-requirements.md:4` | 「P1 不可裁剪」——与 `_NON_PRUNABLE` 含 P1 一致（但 `check-pruning` 不校验 P1，见 A1-3） | ✅ 语义一致，残余见 A1-3 |
| `agate/WORKFLOW.md:239` | 「核心阶段（不可跳）：P1/P2/P4/P5/P6/P6.5」——与 `_NON_PRUNABLE` 一致 | ✅ 无需改 |
| `agate/WORKFLOW.md:359` / `agate/scripts/README.md:77` | check-state-transition 描述为「状态转移合法性 + 重试上限」（泛述，未列「前向跨阶」） | 可选（泛述已覆盖；非必须） |
| `agate/tests/README.md:60` | 映射未变（check-state-transition → unit/test_check_state_transition.py） | ✅ 无需改 |
| `agate/dispatch-protocol.md` / `orchestrator-template.md` / `LIMITATIONS.md` / `role-system.md` / `loop-orchestration.md` | 均不涉前向跨阶执行语义 | ✅ 无需改 |
| `agate/UPGRADING.md` | 未加版本节（CHANGELOG 称「详见 agate/UPGRADING.md」→ **当前悬空**） | 见 A5 |
| CHECK 9 锚点表 | 无「前向跨阶」锚点 | 见 A6 |
| `TAG0050-task-data-contract/P7-consistency.md:66-67` + `P4-implementation-G1.md:70` | 其 REVIEWED-ACCEPTED 的 DESIGN_GAP（「前向规则只在 state-set、不加入 check_transition」）**已被本修复反转**，但 frozen 快照未回改、亦无 roadmap/retrospective 留痕 | **留痕建议**（见下） |

**留痕建议（非阻断）**：TAG0050 的 P7 DESIGN_GAP 是**已被外部评审证伪**的偏离（其接受理由「否则破坏既有前向跳用例」实为「既有用例把缺陷固化为期望」——本 diff 已把 `test_it9` 的 `P2→P5` 改为 `P2→P4`）。按 `adr.md` 的复审触发惯例，建议在 `agate-workspace/roadmap/` 或任务 retrospective 加一行「该 DESIGN_GAP 被 M-1 修复取代」，避免后来者据旧记录复刻缺陷。**frozen 快照可不回改**。

**结论**：A3 主结论 ALIGNED（hotfix 自身反向传播已闭合）；上述留痕建议供主 Agent 决定。

### A4: 测试覆盖 — ALIGNED

**最近一次全量 pytest 实跑**（后台 job + `-n auto`；跑前/跑后 `git status --porcelain` 逐字节一致，**未污染**）：
```
$ python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
1 failed, 2872 passed, 2 skipped, 1 rerun in 84.96s (0:01:24)
```
唯一失败：
```
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
  ERROR Unknown subcommand "agent" for "opencode debug"（本机 opencode CLI 无该子命令）
```
**归因**：环境/工具版本问题，与 diff 无关（第 1 轮同一失败）。**第 1 轮由本 diff 引入的 4 个 TAG0050 失败用例已全部转绿**（定向实跑 `test_tag0050_declarations.py` + `test_check_state_transition.py` → 72 passed；`test_pre_commit_hook.py -k "it9 or m1"` → 5 passed）。

**新增/变更测试**：
- 单测 `test_st_3a`（P2→P4 裁 P3 放行）、`test_st_3b`（**P6→P8 裁 P7 放行**，第 1 轮零覆盖）、`test_st_3c`（P2→P5 未裁拦截）；
- 集成 `test_m1_forward_jump_p0_to_p5_blocked` / `_p0_to_p7_blocked` / `_p2_to_p5_blocked`；`test_it9_pruning_skip_low_passes` 由 `P2→P5` 改为 `P2→P4`；
- 4 个 TAG0050 用例补最小 P7 产出。

**边界行为核查（实测 scratch，未污染仓库）**：
| 场景 | 结果 | 判定 |
|---|---|---|
| `old_phase` 空（`--adopt`/首次） | `''→P5` 放行（`:441` 的 `old_phase and …` 为假） | ✓ |
| 控制态 `old`（PAUSED） | 跳过前向检查（`:441` 条件为假）；PAUSED→Pn 恢复不误拦 | ✓（设计如此） |
| 控制态 `new`（PAUSED/READY/DONE） | `:386-388` 提前 return | ✓ |
| `old_num=0`（P0） | P0→P2（裁 P1）拒、P0→P5 拒 | ✓ |
| legacy（`task_level=None`） | P0→P2 放行（不检查） | ✓ |
| 无 `P1-requirements.md` / 无 frontmatter | `(None,None)` → `not_pruned=skipped` → 拒（fail-closed） | ✓ |

**残留覆盖缺口（建议，非阻断）**：
1. `_gate_p7_structured` **缺文件分支无专门用例**（该分支本身仅由 4 个用例的「补产出」间接反证）；
2. `_resolver_label()` **无单测**（空 root / 有 HOME / 无 HOME / 非父路径 各分支）；
3. legacy 经 `agate-state-set` 的前向跳行为变更（拦→放行）**无单测**；`still_declared`/`not_pruned` 分支（可裁阶段「跳过但仍声明」）无专门用例。

**结论**：ALIGNED（新逻辑主干与 P6→P8 边界均有覆盖；上述为可选的补强项）。

### A5: 下游影响 + 文档传播 — ALIGNED

**行为变更**：
1. **非 legacy 任务**：前向跨阶（≥2）由「不检查」变「按三闸拦截」——M-1 的预期收紧。
2. **legacy 经 `agate-state-set` 的前向跳**：由「拦」变「放行」（与 hook 统一）。已在 `state-machine.md:403` 注明；属消除两通道不一致，非破坏性。
3. **`resolver` 字段语义**：改记相对路径，**无消费方/校验器**读取（`grep` 全仓仅 `agate-task-init.py` 写入），零下游影响。

**文档传播**：
- `CHANGELOG.md [Unreleased]` **已补**（第 1 轮缺口闭合）。
- `agate/UPGRADING.md` **未加版本节**——按本仓发布清单（`AGENTS.md`「版本发布清单」第 2/3 条：发布时 CHANGELOG [Unreleased]→版本号 + UPGRADING 新增章节），**延后至发布可接受**；`check-protocol-consistency.py` **CHECK 13（CHANGELOG↔UPGRADING 章节对应）通过**，证明 [Unreleased] 不受该检查约束。
- **措辞建议（非阻断）**：CHANGELOG 条目末「详见 `agate/UPGRADING.md`」在发布前**悬空**（UPGRADING 现无对应节）。发布时补节即消解；若想在此之前零悬空，可改为「将在发布时补充 `agate/UPGRADING.md` 章节」。

**结论**：ALIGNED（CHANGELOG 已传播、UPGRADING 延后符合发布惯例；一条措辞建议）。

### A6: 锚点表覆盖 — NEEDS_HUMAN_REVIEW

**现状**（`check-protocol-consistency.py:608-622`）：`check-state-transition.py` 已有 3 条锚点（`MAX_RETRY` / 回退跳变 `["diff","phase_num"]` / `RM-AG0042`）。**本 diff 未新增锚点**——「前向跨阶」仍无锚点。`check_anchor_coverage`（`:928`）按**脚本粒度**判覆盖，`check-state-transition.py` 已被覆盖，故**不触发机械 WARNING**。

**判断**：新增的「前向跨阶拦截」与既有「回退跳变检测」锚点**对称**，建议补一条 `keywords: ["前向跨阶"]` 锚点，使「规则存在于脚本」可机械守护。是否必补属团队取舍（非机械门禁强制）。

**[HUMAN_CONFIRMED: 2026-10-09 用户裁决：补锚点。已实施——`check-protocol-consistency.py` 新增锚点 `desc: "前向跨阶检测（非 legacy：被跨阶段须已裁剪且不可跳过阶段不得跨，TAG0050 评审 M-1）"` / `script: agate/scripts/check-state-transition.py` / `keywords: ["前向跨阶"]`，与「回退跳变检测」锚点对称。]**

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

逐条核对相关 ADR（`agate/adr.md`）：

| ADR | 相关性 | 判定 |
|---|---|---|
| ADR-002 可判定性 | 前向跨阶判据为 `check_transition` 纯函数 + exit code，机器可判定 | **ALIGNED** |
| ADR-014 判据单一权威源 | 前向规则已从 `agate-state-set.py`+`check_transition` 两处**收敛为一处** ✓；**但**「不可裁剪阶段集」现**双份存在**：`check-pruning.py:233-253`（P2/P4/P5/P6，逐条）与 `check-state-transition.py:455`（P1/P2/P4/P5/P6，集合），且**已分叉（P1 只在后者）** | **NEEDS_HUMAN_REVIEW** |
| ADR-011 引导型工具非安全边界 | 前向判据下沉到 hook/CI 共用 gate，正合「真正边界在 gate 链」 | **ALIGNED** |
| ADR-015 门禁只用于实质错误 | 第 1 轮 `judge_crossed` 的过度拦截（ADR-015 张力）**已删除**；剩余前向判据只拦「未裁剪/不可裁剪」的实质错误 | **ALIGNED**（张力已消解） |
| ADR-004 安全网分层 | 前向判据进入 hook/CI 共用函数，多层防线 | **ALIGNED** |

**NEEDS_HUMAN_REVIEW 的具体问题**：`check-pruning.py` 与 `check-state-transition.py` **各存一份「哪些阶段不可裁剪」**，且当前已**不一致**（P1 只在前者缺）。ADR-015 明确把「判据散在多处→改一处漏其余」列为**实质错误类**。建议将不可裁集**单源**（如下沉到契约 `rules/task-data/level-1.yaml` 新增键，两脚本共读），或至少让 `check-pruning.py` 补 P1 项、两处逐字一致并加等价守护。是否现在做属设计取舍。

**[HUMAN_CONFIRMED: 2026-10-09 用户裁决：现在只做**最小对齐**，**下沉契约单源**另立条目。已实施——① `check-pruning.py` 新增 P1 不可裁剪项、并把 P1/P2/P4/P5/P6 的判据改为模块级 `NON_PRUNABLE_PHASES` + `_NON_PRUNABLE_REASONS` 驱动；② `check-state-transition.py` 的 `_NON_PRUNABLE` 提升为模块级 `NON_PRUNABLE_PHASES`（两处逐字一致）；③ 等价守护测试 `agate/tests/unit/test_non_prunable_phases_guard.py`；④ 下沉契约单源登记为 **RM-AG0110**。]**

### A8: 声称-命令绑定 — ALIGNED

逐条列本批**结论类声称**及其产出命令（均在只读 scratch / 只读命令下复现）：

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | 「前向跨阶规则改前只在 `agate-state-set.py`，未进入 `check_transition`」（`CHANGELOG.md:16`、`test_pre_commit_hook.py:932-933`） | `git show HEAD:agate/scripts/agate-state-set.py \| grep -c _forward_multi_jump_error` → **2**；`git show HEAD:agate/scripts/check-state-transition.py \| grep -c 前向` → **0** | 成立 |
| 2 | 「原用例 `P2→P5` 把缺陷固化为期望」（`test_pre_commit_hook.py:896-897`） | `git show HEAD:agate/tests/integration/test_pre_commit_hook.py \| grep -c "skip to P5"` → **1** | 成立 |
| 3 | 「`gate_p5` 兜底返回 2」（`CHANGELOG.md:18`） | `sed -n '/^def gate_p5/,/^def /p' check-gate.py \| grep -n "return 2"` → 命中（`:24/:56`） | 成立 |
| 4 | 「`_gate_p7_structured` 对缺产出放行（假 PASS）」（`CHANGELOG.md:22-23`） | `git show HEAD:agate/scripts/check-gate.py \| grep -c "P7-consistency.md 不存在"` → **0**（改前无早退；`_read_text` 空→计数 0→return 0） | 成立 |
| 5 | 「非 legacy 缺 P7 产出 ⇒ FAIL（exit 1）」（`CHANGELOG.md:23`） | scratch：无 P7 → `check-gate.py P7` **rc=1**；有 P7 → rc=0 | 成立 |
| 6 | 「前向跨阶（delta≥2）对非 legacy 由 `check_transition` 检查」（`state-machine.md:403`） | scratch：`check_transition("P0","P5")` 非空；`("P6","P8")` 空 | 成立 |
| 7 | 「不得跨过不可跳过阶段（P1/P2/P4/P5/P6）」（`state-machine.md:403`） | `grep -n "_NON_PRUNABLE" check-state-transition.py` → `:455 {"P1","P2","P4","P5","P6"}` | 成立 |
| 8 | 「legacy 任务维持不检查」（`state-machine.md:403`） | scratch：legacy `check_transition("P0","P2")` → 空（放行）；`test_st_3` 全量通过 | 成立 |
| 9 | 「`resolver` 不记绝对路径」（`CHANGELOG.md:24-25`、`agate-task-init.py:82`） | scratch：`AGATE_ROOT=/home/kity/.agate/v0.80.1/agate` → `v0.80.1/agate`；dev checkout → `agate`；空 → `''`（无绝对路径） | 成立 |
| 10 | 「`check-pruning` 检查 2/3 对 P2/P6 无例外口」（本报告 P0-3 结论） | `grep -n "检查 2：P2\|检查 3：P6" check-pruning.py` → `:233/:241`（文案「无例外口」） | 成立 |

**无据声称**：未发现需删除的无据声称。**结论：ALIGNED**。

---

## 附：风险面专项核查结论（任务点名项）

1. **删 `state-machine.md` 两行（跳过 P2 / 跳过 P6）是否正确**：**正确**。P2/P6 由 `check-pruning.py` 检查 2/3「无例外口」硬拦，`WORKFLOW.md:239`、`phase-cards/*` 一致；无其它机制允许跳过。PAUSED 举例改 P3 合理（P3 裁后 P4 gate 不要求红灯变绿）。
2. **新规则边界（空 `old_phase` / 控制态 / P0 / legacy）**：均正确（见 A4 边界表）。控制态 `old`（PAUSED）不检查属设计（PAUSED→Pn 恢复不误拦）——**残余**：`PAUSED→P7` 这类手改跨阶不受前向检查约束（`old` 在控制态）；此属既有设计（`old_num` 对控制态取 0），**非本 diff 引入**，供人工知悉。
3. **`_p1_pruned_and_declared` 覆盖两形态**：**是**（块式/内联 `phases`、块式/内联 `pruned`、无 frontmatter fail-closed 均实测正确）。
4. **`_gate_p7_structured` 早退**：仅非 legacy 分支；legacy 走旧路径不受影响；不误伤 P7 已裁剪任务（规则 7 不重跑无产出阶段）。
5. **P0-2 语义**：`P6→P8`（裁 P7）现放行；不存在「跨 P6.5 而不跨 P6」的路径（P6 不可跳 + P6.5 由 judge 链单独承载）。

---

## 闭环建议（按优先级）

| 优先级 | 项 | 动作 |
|---|---|---|
| — | 第 1 轮 P0-1/P0-2/P0-3 | ✅ 已验证修复，无需再动 |
| P2 | A6 | 人工确认是否补 CHECK 9「前向跨阶」锚点 |
| P2 | A7 | 人工裁决「不可裁剪阶段集」是否下沉契约单源（当前两脚本双份且 P1 分叉） |
| P3 | A1-3 | 建议 `check-pruning.py` 补「P1 不可裁剪」检查（更早、报错更清晰） |
| P3 | A4 | 建议补 3 处覆盖：缺 P7 分支、`_resolver_label`、legacy state-set 前向跳 |
| P3 | A3b/A5 | 建议在 roadmap/retrospective 留痕「TAG0050 DESIGN_GAP 被 M-1 取代」；发布时补 `UPGRADING.md` 版本节（消解 CHANGELOG 悬空引用） |

**注**：本报告为**只读**审查，未修改任何协议/脚本/测试文件，未 commit；全量 pytest 为后台 job，跑前/跑后 `git status` 一致（无污染）。留痕文件见 `docs/reviews/agate-alignment-2026-10-09-HOTFIX-M1-02.progress.md`。
