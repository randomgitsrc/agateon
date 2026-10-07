---
review_date: 2026-10-07
reviewer: protocol-alignment-review
change_summary: TAG0050 批 A1——按等级冻结的任务数据契约快照、账本完整性七规则、agate-task-init、契约决定 judge/evidence_ref、R6 差分交付物
files_changed:
  - agate/rules/task-data/LEVELS.yaml（新）
  - agate/rules/task-data/level-1.yaml（新）
  - agate/scripts/agate-task-init.py（新）
  - agate/tests/fixtures/task-data/level-1/{pass,fail}/*（新）
  - docs/design-notes/r6-differential.sh（新）
  - docs/design-notes/r6-allowlist.yaml（新）
  - agate/scripts/agate_common.py
  - agate/scripts/check-events.py
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/check-gate.py
  - agate/scripts/check-state-transition.py
  - agate/scripts/agate-state-yaml-check.py
  - agate/scripts/check-protocol-consistency.py
  - agate/tests/conftest.py
  - agate/tests/integration/test_pre_commit_hook.py
  - agate/tests/unit/test_agate_state_yaml_check.py
  - agate/tests/unit/test_dispatch_context_warning.py
  - agate/scripts/README.md
  - agate/tests/README.md
  - docs/design-notes/README.md
---

# 协议-脚本对齐审查（TAG0050 批 A1 · SELF-GATE Layer 1 · 变更触发模式）

## 0. 意图分析与反向传播

**意图（为什么改）**：把「判定依据」从可随手改的开关 / 日期门槛 / agent 自报值，改为**按等级冻结的契约 + 机械核验**：任务以账本首行 `task_created` 记录契约等级（无创建事件即 legacy，走旧逻辑），要求项（judge / evidence_ref）由快照 `requires` 决定；同时把账本完整性收敛为 pre-commit 的七条规则，并交付 R6 双向差分把 §8「legacy 兼容承诺」变成可执行判据。

**反向传播——应被这次改动影响但不在 diff 中的文件**（按优先级）：

| 文件 | 被影响的理由 | 实际 |
|---|---|---|
| `agate/WORKFLOW.md` | 「Pre-commit 检查总览」自称是 pre-commit 检查集的**唯一事实源**；A1 新增「账本与新目录」步骤（规则 1/3/4/5/7），表内必须有该行 | **未改** ✗ |
| `SELF-GATE.md` | 新增 CHECK 16，正文两处写「当前 CHECK 1-15」 | **未改** ✗ |
| `agate/UPGRADING.md` | 设计 §8 要求写明「新任务一律用 `agate-task-init` 创建 + `--adopt`/`--upgrade` 用法」 | **未改** ✗（批次归属待人工确认） |
| `CHANGELOG.md` | 协议语义变更通常记 `[Unreleased]` | **未改** ✗（可能按发布时更新） |
| `agate/scripts/README.md` | 已加 `agate-task-init.py` 行；但 `pre-commit-gate.py` 描述「按顺序调度 9 项检查」未随新增步骤更新 | **部分** △ |
| `agate/state-machine.md` | 新增「legacy 从 READY/DONE 回 Pn → ERROR」的转移规则 | **未改** △（批次归属待人工确认） |
| `agate/scripts/check-p6-evidence.py` / `check-p6-provenance.py` | evidence_ref 改依契约——经 `agate_common.is_new_task_for_evidence_ref` 单点改，消费方自动跟随 | **无需改** ✓ |
| `agate-migrate-workspace.py` | 改名检测下 legacy 不受影响 | **不改代码** ✓ |
| 卡片 / 角色文件 / P0 卡 / orchestrator 模板 | 创建入口改为 `agate-task-init` | 设计 §11 归 **A3–F**，A1 可后置（不判） |
| `agate/rules/obligations.yaml` | 新增「必须」的登记 | 设计 §10 归 **A4**（不判） |

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED** |

> 核心问题三项（可复现）：① `agate-next.py` 的 judge 消费方**未按契约改**（且 P4 记录谎称已落地）；② pre-commit 规则 7 后半（非 legacy 按被暂存产出所属阶段重跑 gate）**未实现**；③ `check_ledger_events` 把「新任务等级 = 当前等级」实现成**对全部来源事件的恒等约束并进入 CI 路径**，协议升级后会**追溯**存量非 legacy 任务（与 §2.1 规则 3 直接冲突）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

#### A1-1 `agate-next.py:_p6_judge_advance` 未按契约改（设计 §2.5 消费方清单）

**文档声明**（`docs/design-notes/design-tag0050-task-data-contract.md:253` §2.5）：
> 对非 legacy 任务，`judge` 和 `evidence_ref` 是否生效由快照的 `requires` 决定，**不再读** `judge.enabled` 或 `created`。以下消费方统一改为调用 `requirement_active(task_dir, <name>, <phase>)`：
> | judge | `check-gate.py:767`、`gate_p65`（`:1219`）、`pre-commit-gate.py:157`、**`agate-next.py:266`** |

同一要求见 `P2-design.md:80`（§1.1 A1 行列出 `agate-next.py:_p6_judge_advance`）与 `P4-dispatch-context-implementer-A1.md:26`（交付物第 9 条）。

**脚本实现**（`agate/scripts/agate-next.py:273-278`，**未被本次 diff 触及**）：
> ```python
> judge = state.get("judge")
> judge_enabled = bool(isinstance(judge, dict) and judge.get("enabled"))
> if not judge_enabled:
>     # 历史任务 / judge 未启用 → gate_p65 早退 0 → 裁决成立，直推 P7
> ```

**结论**：MISALIGNED
**差异**：其余三个消费方（`check-gate.gate_p1`、`gate_p65`、`pre-commit._judge_enabled`）已改为 `requirement_active`，唯独 `agate-next.py:_p6_judge_advance` 仍读可被 agent 改写的 `judge.enabled`——修复 F3b 在 `agate-next` 推进路径上**未闭合**。
**复现证据**：
```
$ git status --porcelain | grep agate-next      # 空（文件未修改）
$ grep -n "requirement_active" agate/scripts/agate-next.py   # 无匹配
```
**建议**：`_p6_judge_advance` 改调 `requirement_active(task_dir, "judge", "P6")`（`None` → 走旧 `judge.enabled` 逻辑；非 `None` → 依契约）。

#### A1-2 pre-commit 规则 7 后半（按被暂存产出所属阶段重跑 gate）未实现

**文档声明**（设计 §2.3 规则 7，`design-tag0050-task-data-contract.md:169`）：
> 非 legacy 任务暂存了阶段产出、却没有改 phase 时，按**被暂存产出所属的阶段**重跑该阶段的 gate。该阶段必须不晚于 HEAD 的 phase；HEAD 为 READY 或 DONE 时同样执行。

同见 `P2-design.md:80`（§1.1 A1 行）与 `A1 验收锚⑧`（`design:661`）。

**脚本实现**（`agate/scripts/pre-commit-gate.py:371-376`，函数 `_scan_prod_touched_and_rerun` docstring）：
> 说明：规则 7 后半（非 legacy 任务按被暂存产出所属阶段重跑 gate）**本批未启用**——其语义…与既有 IT_PHASE_SPAN 用例冲突，而 P1/设计 §8 的例外清单未包含这些用例；语义待定后另批落地。

**结论**：MISALIGNED
**差异**：函数名 `_scan_prod_touched_and_rerun` 含 `rerun`，但实现只做 PROD_TOUCHED 扫描，**没有任何重跑逻辑**；A1 范围内该行为缺失。
**DESIGN_GAP 核查（角色原则 6）**：该偏离已登记在 `P4-implementation.md:138` 的 `[DESIGN_GAP: …]`，但任务**尚无 P7-consistency.md**（仍在 P4）→ 未获独立 `REVIEWED-ACCEPTED`，按角色定义仍按普通 MISALIGNED 处理。
**建议**：要么本批补齐（并按 §8 例外清单评估 IT_PHASE_SPAN 用例），要么把该行为显式移出 A1 验收锚（改 BDD-19 的口径），二者必居其一，不能留「验收锚要求、实现明说未做」的缺口。

#### A1-3 `check_ledger_events` 的「等级 = 当前等级」约束会追溯存量任务（与 §2.1 规则 3 / §2.2 冲突）

**文档声明**：
- §2.2 事件规则表（`design:136`）对 `task_created`：`contract_level` **必须是 LEVELS 中登记过的等级**（未要求 = 当前等级）。
- §2.3 规则 2（`design:164`）：**新任务**的等级必须是当前等级（**只在本地检查**）。
- §2.1 规则 3（`design:95`）：「新增或收紧要求时登记新一级，否则**在途任务会被追溯**」——等级机制的立意就是**不追溯**在途任务。

**脚本实现**（`agate/scripts/agate_common.py`，`_level_registration_errors`，被 `check_ledger_events` 用于 `task_created`/`task_adopted`/`task_upgraded`）：
> ```python
> if current is not None and lvl != current:
>     return [f"{event} 的等级 {lvl} ≠ 当前等级 {current}（新任务必须登记当前等级，第 {lineno} 行）"]
> ```

且 `check_ledger_events` 被 `check-events.py`（新增第 9 步）调用，而 `check-events.py` 又在 `check-gate.py P6.5`（CI/P6.5 路径）与 pre-commit 中被调用——**并非「只在本地检查」**。

**结论**：MISALIGNED
**差异**：把 §2.3 规则 2（本地、仅新任务）实现成对**所有**来源事件的**恒等约束**，并放进 CI 路径。后果：一旦登记 level 2（设计规定 B/C 等批要登记新一级），所有 level 1 的存量非 legacy 任务会被**追溯**判 ERROR。
**复现证据**（在仓外可丢弃副本上，`/tmp/opencode/tag0050_lvl`）：
```
# 模拟协议升级：登记 level-2.yaml（extends 1）使 current_level=2
$ AGATE_ROOT=$PWD/agate python3 agate/scripts/check-events.py <task: task_created contract_level=1>
GATE EVENTS: 契约等级事件规则违反：
  - task_created 的等级 1 ≠ 当前等级 2（新任务必须登记当前等级，第 1 行）
rc=1
```
（该任务在 level 1 时合法创建，按 §2.2/§2.1 规则 4 应当放行——只有「任务等级 > 协议最大等级」才 fail-closed。）
**建议**：`check_ledger_events` 只校验「等级已登记」（§2.2）；「= 当前等级」仅在 pre-commit 的**新建目录**分支对新任务单独判（§2.3 规则 2）。

#### A1-4（次要）PROD_TOUCHED 扫描面扫「全部暂存文件」而非「全部暂存 `*.md`」

**文档声明**（`P2-design.md:221` §3.1 第 2 点）：扫描**全部暂存 `*.md` 文件的新增行**。
**脚本实现**（`pre-commit-gate.py:386-399`）：`git diff --cached -M -- task_rel` 取该任务目录下**所有**暂存文件的新增行（未过滤 `*.md`）。
**结论**：NEEDS_HUMAN_REVIEW（低风险）
**说明**：规格写明 `*.md`，实现按「全部文件」扫描；安全门「宁可多拦」（`P2-design.md:158`），且既有 2g.0 段本就如此（A1 镜像它），实测新增误拦为 0。是否要求严格限 `*.md` 由人工裁决。
**建议**：若严格按规格，过滤到 `*.md`；若接受「宁可多拦」，在 §3.1 注明扫描面为「任务目录内全部暂存文件」。

---

### A2: 脚本→文档对齐 — MISALIGNED

#### A2-1 `WORKFLOW.md`「Pre-commit 检查总览」（唯一事实源）未收录新步骤

**文档自述**（`agate/WORKFLOW.md:347`）：
> **本表是「pre-commit 检查集」的唯一事实源**——其它文档只指针引用、不复制清单。

**脚本实现**：`pre-commit-gate.py:434-437` 在 2h.1b 之前新增 `_check_ledgers_and_new_dirs` + `_scan_prod_touched_and_rerun`（账本七规则 + 全局面 PROD_TOUCHED），且「每次提交都跑」。

**结论**：MISALIGNED
**差异**：唯一事实源表（`WORKFLOW.md:353-365`）**没有任何**「账本与新目录」行；「多任务适配」段（`:371`）仍写「扫描暂存区中所有变更的 `.state.yaml`」——这正是 A1 要扩到的「不依赖 `.state.yaml` 是否暂存」，也未更新。
**建议**：在表中新增一行（如 `1.1 账本与新目录`：触发条件「任意提交」，机制「新目录创建事件 / 账本只追加不可删 / 事件规则 / 全局面 PROD_TOUCHED」）。

#### A2-2 `SELF-GATE.md` 的 CHECK 范围未更新

**文档声明**（`SELF-GATE.md:5` 与 `:39`）：
> （不写死上界，当前 CHECK 1-15…）
> 确认结构 CHECK 全集（当前 1-15）无 ERROR

**脚本实现**：`check-protocol-consistency.py:1526` 新增 `("CHECK 16 任务数据契约快照冻结", check_task_data_snapshot_freeze)`。

**结论**：MISALIGNED
**差异**：CHECK 全集已到 16，`SELF-GATE.md` 两处仍写 1-15。（`agate/scripts/check-protocol-consistency.py:26` 的 docstring 已补 CHECK 16，说明脚本侧已更新，只有 SELF-GATE.md 漏了。）
**建议**：两处改为「当前 CHECK 1-16」。

#### A2-3（次要）`agate/scripts/README.md` 的 `pre-commit-gate.py` 描述未随新增步骤更新

`agate/scripts/README.md:67`：「hook 主程序：按顺序调度 9 项检查 + PROD_TOUCHED 检测 + …」。A1 新增「账本与新目录」步骤后，该描述（及「9 项」）已更不准。
**结论**：NEEDS_HUMAN_REVIEW（既有数字，A1 使其偏差增大）。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

反向传播清单见 §0，逐一验证结论：

| 应被影响文件 | 结论 |
|---|---|
| `agate/WORKFLOW.md`（pre-commit 表） | **未影响** → A2-1（MISALIGNED） |
| `SELF-GATE.md`（CHECK 范围） | **未影响** → A2-2（MISALIGNED） |
| `agate/UPGRADING.md`（task-init 用法） | **未影响**（A5，NEEDS_HUMAN_REVIEW：批次归属） |
| `CHANGELOG.md` | **未影响**（A5，NEEDS_HUMAN_REVIEW：批次归属） |
| `agate/scripts/README.md`（pre-commit 描述） | **部分影响**（索引行已加，描述未改） |
| `agate/state-machine.md`（legacy 重开 ERROR） | **未影响**（A5，NEEDS_HUMAN_REVIEW：A1 还是 A3） |
| `check-p6-evidence.py` / `check-p6-provenance.py` | **无需改**：`check-p6-evidence.py:187`、`check-p6-provenance.py:479` 均调 `is_new_task_for_evidence_ref`，后者已在 `agate_common.py` 单点改为调 `requirement_active` ✓ |
| `agate-migrate-workspace.py` | **不改代码**；`test_agate_migrate_workspace.py` 9 passed ✓ |
| 卡片 / 角色文件 / P0 卡 | 设计 §11 归 A3–F，A1 可后置 |
| `obligations.yaml` | 设计 §10 归 A4 |

**结论**：MISALIGNED（`WORKFLOW.md`、`SELF-GATE.md` 两处链条断裂；其余为批次归属待确认）。

---

### A4: 测试覆盖 — MISALIGNED

**最近一次全量 pytest 实跑**（仓外可丢弃副本 `/tmp/opencode/tag0050_git`，含 `.git`，`-n auto`）：
```
$ python3 -m pytest agate/tests/ -q --tb=no -n auto
40 failed, 2710 passed, 3 skipped in 64.46s
```
- 40 条失败**全部**落在后续批的既有红灯文件：`test_tag0050_{ci_replay(A2), state_set(A3), obligations(A4), write_tools(B), declarations(E), proxy_judgment(F), evidence(D), prod_touched(C), fitness(B)、cross_batch}`，外加 1 条环境漂移 `test_setup_agate_dir.py::test_bdd_43_…`。**A1 范围内 0 回归** ✓。
- A1 验收文件实跑：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q
24 passed in 4.05s
```
- 快照冻结 CHECK 负向实跑（仓外副本）：改已发布快照 / 新增未登记 `level-2.yaml` / 删除登记快照 → 均 `rc=1`；基线 `0 ERROR / 411 WARNING` ✓。

**缺口**：
1. **`agate-next.py:_p6_judge_advance` 无任何测试**：`grep -rn "_p6_judge_advance" agate/tests/` → 0 命中。A1-1 的实现缺失因此**不会被红灯发现**。
2. **BDD-19 名不副实**（`test_tag0050_a0_a1_ledger.py:320-326`）：用例只直接运行 `check-gate.py P6 <init_task>` 并断言 `rc != 0`，**没有**走 pre-commit、也没有构造「只暂存产出、未改 phase」的场景——即未测试规则 7 后半（A1-2）。该用例在规则 7 后半未实现时仍会通过，属「不会变红的测试」。
3. **A1-3 的追溯 bug 无测试**：没有 `current_level > 任务等级` 的场景（BDD-21 只用 level 1 = current）。

**结论**：MISALIGNED
**建议**：补 `agate-next` judge 依契约的用例；重写 BDD-19 为「经 pre-commit hook 提交只改产出、未改 phase」；补 `current=2 + 存量 level 1 任务应放行` 的用例。

**R6 交付物覆盖（附加）**：脚本可跑、负向用例与自核验成立（见 A8），但在 **agateon 真实语料上只比对到 1 个 legacy 任务**（43 个任务目录中 36 READY / 2 DONE / 4 P0 因 `phase not in PHASES` 被跳过）→ 对 §8 兼容承诺的实际覆盖面很小。
**结论**：NEEDS_HUMAN_REVIEW（是否应把 READY/DONE 任务纳入「相关 gate」由人工裁决）。

---

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- **破坏性变更**：无（legacy 任务走旧逻辑，§8 承诺未破；三个既有测试的改动经核在 §8 例外内——见 A8）。
- **文档传播缺口**：`WORKFLOW.md`、`SELF-GATE.md`（同 A2/A3，已判 MISALIGNED）；`UPGRADING.md`（`agate-task-init` 创建入口 / `--adopt` / `--upgrade` 用法）、`CHANGELOG.md`、`state-machine.md`（legacy 重开 ERROR）**未更新**。
- **判定理由**：A1 是 10 批中的一批（设计 §10「每批独立 PR」），`CHANGELOG`/`UPGRADING` 是否**逐批**更新属团队约定（设计 §10 只对 BDD-76 的义务基线重设明确要求写 CHANGELOG）；`state-machine.md` 的转移规则归属 A1 还是 A3 亦需人工裁决。故不判 MISALIGNED，标 NEEDS_HUMAN_REVIEW。

**建议**：明确 A1 是否需同步 `UPGRADING.md`（创建入口）与 `state-machine.md`（legacy 重开）；`CHANGELOG` 若按发布时更新则可豁免。

---

### A6: 锚点表覆盖 — ALIGNED

- 新增的 CHECK 16（`check-protocol-consistency.py:1445`）是**数据面结构 CHECK**（快照字节冻结），不是「文档声明规则 → 脚本关键词」的映射，不需要进入 `SCRIPT_ALIGNMENT_ANCHORS`（CHECK 9）。
- 新脚本 `agate-task-init.py` 属 `agate-*.py`，**不在** CHECK 9 / SG.6 覆盖的 `uncovered_gate_scripts()`（只 glob `check-*.py` + `pre-commit-gate.{sh,py}`）面内——与 P2 §1.4 实测结论一致。
- 新「必须」（如新目录须有创建事件）的 `obligations.yaml` 登记属 A4。

**结论**：ALIGNED

---

### A7: 设计原则一致性 — ALIGNED

- A1 的立意（判定只读结构化数据、正则只作绊线、一个事实一个源、新旧任务靠契约等级分流）与 **ADR-002（可判定性——gate 门槛机器可判定）**、**ADR-005（改动性质决定流程）** 一致，未见冲突。
- 未发现 A1 违反任何已记录 ADR。
- **建议（非阻塞）**：`agate/adr.md` 中尚无「契约按等级冻结 / 任务版本」的决策记录（`grep 契约等级|task-data|contract_level agate/adr.md` → 0 命中）。可考虑补一条 ADR（记录「判定依据从开关/日期改为契约快照」的取舍），与既有 `design-tag0050-task-data-contract.md` 形成索引关系。

**结论**：ALIGNED

---

### A8: 声称-命令绑定 — MISALIGNED

逐条列 `声称 → 命令 → 结论`：

| # | 声称（出处） | 产出它的命令 | 结论 |
|---|---|---|---|
| 1 | 「`agate-next.py:_p6_judge_advance` 改依契约（`requirement_active`）**已落地**」（`P4-implementation.md:42` §2 row 9；另 `:120` 列为「修改」文件） | `git status --porcelain \| grep agate-next`；`grep -n requirement_active agate/scripts/agate-next.py` | **证伪**：文件未修改，仍读 `judge.enabled`（A1-1） |
| 2 | 「全量 pytest → **2711 passed / 40 failed / 2 skipped**」（`P4-implementation.md:148`） | `python3 -m pytest agate/tests/ -q --tb=no -n auto` | **近似**：实测 `40 failed / 2710 passed / 3 skipped`（failed 一致；passed/skipped 各差 1，量级吻合，失败集合与所述「后续批红灯」一致） |
| 3 | 「`check-protocol-consistency.py --strict-errors-only` → **0 ERROR / 410 WARNING**」（`P4-implementation.md:153`） | 同命令（仓外副本） | **近似**：实测 `0 ERROR / 411 WARNING`（ERROR 一致；WARNING 多 1） |
| 4 | 「fitness 节点 `test_task_data_freeze_snapshot_sha256` / `test_task_data_golden_fixture_regression` **已落地**」（`P4-implementation.md:44`） | `ls agate/tests/unit/test_tag0050_fitness.py`；`grep -n test_task_data agate/tests/unit/test_tag0050_fitness.py` | **成立**（节点存在；其中 BDD-50 的 `schema_single_source` 为 B 批红灯，属预期） |
| 5 | 「R6 差分：干净 clone 上 exit 0；负向用例（删必需规则 / 弄脏 corpus）→ exit 1」（`P4-implementation.md:158`） | `bash docs/design-notes/r6-differential.sh --before <base> --corpus .`（仓外副本）；`--allow <删 D12 的副本>`；脏 corpus | **成立**：分别 exit 0 / exit 1 / exit 1 |
| 6 | 「`test_agate_migrate_workspace.py` 9 用例全绿」（`P4-implementation.md:147`） | `python3 -m pytest agate/tests/unit/test_agate_migrate_workspace.py -q` | **成立**：9 passed |
| 7 | 「`conftest.init_task()` … 写 `task_created`，等级 1」（`P4-implementation.md:46`） | 读 `agate/tests/conftest.py`（`_write_ledger_chain` + `init_task(contract_level=1)`） | **成立**：首行 `task_created`，哈希链合法，默认等级 1 |

**结论**：MISALIGNED（第 1 条为**无据且被证伪**的声称——须删除或补齐实现；第 2/3 条为近似值，建议按实测修正数字）。
**建议**：删除 `P4-implementation.md` §2 row 9 的「已落地」（或补齐 A1-1），并把 §6 的 pytest/consistency 数字改为实跑值。

---

## 附加核查（dispatch 重点逐项）

| 重点 | 结论 |
|---|---|
| 快照冻结 CHECK 能否拦「改已发布 / 新增未登记」且不误伤 | **成立**：负向三项均 rc=1；基线 0 ERROR。CHECK 16 仅扫 `agate/rules/task-data/`（DEBT0025 收窄）✓ |
| 账本七规则 vs 设计 §2.3 逐条对齐 | 规则 1/3/4/5 落地；**规则 2 实现走样**（A1-3）；**规则 7 后半缺失**（A1-2）；规则 7 前半（每个有暂存文件的任务目录都扫 PROD_TOUCHED，不依赖 `.state.yaml` 是否暂存）**已落地** ✓ |
| PROD_TOUCHED 扫描面按 P2 §3.1（全部暂存 `*.md` 新增行，只排除 `AGATE_CARD` 块） | 只排除 `AGATE_CARD` 块 ✓；但扫「全部暂存文件」而非「`*.md`」（A1-4，低风险） |
| legacy 兼容承诺（§8 十二项）守住 + 既有测试改动限例外 | 三个既有测试改动经核在 §8 例外内（见下）✓；R6 覆盖面偏小（A4 附加）△ |
| R6 可跑 + 负向用例变红 + 副本内自核验 `git status` 为空 | **全部成立** ✓（另见 A8-5） |
| `conftest.init_task()` 真写 `task_created`（等级 1） | **成立** ✓（A8-7） |

**三个既有测试改动是否在 §8 例外内**（dispatch 重点）：

| 文件 | 改动 | §8 依据 | 判定 |
|---|---|---|---|
| `test_pre_commit_hook.py` | `_write_state_yaml` 增写 `task_created` 首行 + `judge.enabled: true`；新增 `_seed_task_created` | §8 例外「§2.3 新建任务目录并提交的用例」+ 第 3 项（ID 放宽不涉及）；`judge.enabled` 是「非 legacy 任务 judge 由契约强制」的直接后果 | ✓ 在例外内 |
| `test_dispatch_context_warning.py` | 新任务目录补 `task_created` | §8 例外「新建任务目录并提交的用例」 | ✓ 在例外内 |
| `test_agate_state_yaml_check.py` | ID 正则放宽（`T001` 由拒绝变通过；新增 `T001a` 仍拒绝） | §8 第 3 项「任务 ID 正则统一，放宽」 | ✓ 在例外内 |

---

## 闭环建议（供主 Agent）

| 结论 | 项 | 动作 |
|---|---|---|
| MISALIGNED | A1-1 / A8-1 | 实现 `agate-next.py:_p6_judge_advance` 依契约；删除/更正 P4 记录的不实「已落地」 |
| MISALIGNED | A1-2 / A4-2 | 补齐 pre-commit 规则 7 后半，或调整 BDD-19 口径使之与实现一致 |
| MISALIGNED | A1-3 / A4-3 | 把「等级 = 当前」限缩为 pre-commit 的新任务分支；`check_ledger_events` 只校验「已登记」 |
| MISALIGNED | A2-1 / A2-2 / A3 | 更新 `WORKFLOW.md`「Pre-commit 检查总览」与 `SELF-GATE.md` 的 CHECK 范围 |
| MISALIGNED | A8-2 / A8-3 | 按实跑值修正 P4-implementation 的数字 |
| NEEDS_HUMAN_REVIEW | A1-4 / A2-3 / A4-附加 / A5 | 人工确认（附 `[HUMAN_CONFIRMED: …]`） |

> 环境隔离：本审查全程只读；所有变异/差分/pytest 均在仓外可丢弃副本（`/tmp/opencode/tag0050_{full,git,r6,lvl}`，`tar` 复制）上运行，未对被评审文件做任何写操作。
