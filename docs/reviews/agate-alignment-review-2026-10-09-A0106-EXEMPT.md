---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0106（DEBT0055+DEBT0056）「合法例外缺机械出口」——P6 卡新增「预存失败豁免口径」节 + check-maintainability.py docstring 明确「设计强制改动越阈」既定出口=known-violations 登记（不引入机械豁免）
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/phase-cards/P6-acceptance.md
  - agate/scripts/check-maintainability.py
---

# 协议-脚本对齐审查（A0106-EXEMPT）

> 分支 `hotfix/batch-a-exemption`（未提交，改动在工作区）。本报告只读代码、只写本文件与留痕文件，未改任何协议/脚本/测试，未 commit/push。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** — P6 卡把「实际失败集 − known-failures 集 = ∅」挂到 `check-judge-verdict.py`；该脚本**无此逻辑**（且 judge 隔离白名单**不含** `known-failures.md`，机制上读不到）|
| A2 | 脚本→文档对齐 | **ALIGNED**（docstring 改动为纯说明，无行为变更；与 `gate_p4`/P4 卡一致。仅字段名「依据（设计条目）」与模板「理由」措辞不一致，见 A3b）|
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** — 反向传播缺口：`judge.md` 未同步；`check-judge-verdict.py` 未同步且与白名单冲突；DEBT0056 证据误贴 P6 note；模板字段名不一致 |
| A4 | 测试覆盖 | **MISALIGNED** — 无回归测试；DEBT0055 `closure_criteria` #2（回归用例）未满足仍关单 |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **无既有用例转红 / 无夹具需更新**（实跑：`1 failed, 2906 passed, 2 skipped, 1 rerun`，唯一 failed 为先于本批存在的环境性 `test_bdd_43`）|
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW** — CHANGELOG 已标；`judge.md` 角色文件未传播（与 A3b 同源）|
| A6 | 锚点表覆盖 | **ALIGNED** — 无需新增 CHECK 9 锚点；**其缺席恰是 A1 缺实现的镜像**（协议规则无脚本可锚）|
| A7 | 设计原则一致性 | **ALIGNED** — ②「不引入 self-declaration 机械豁免」引 ADR-015 成立 |
| A8 | 声称-命令绑定 | **MISALIGNED** — 4 条数字声称全部复现 ✓；但「judge 按…机械复核」无命令/无实现（散布于 P6 卡/CHANGELOG/roadmap/debt），须删或改写 |

**是否可 commit：否**（A1/A3/A4/A8 为 MISALIGNED，按闭环规则须先修）。最小修复见文末「修复方向」。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**文档声明**（`agate/phase-cards/P6-acceptance.md:48-49`，本批新增）：
> - **judge 可复核**：`check-judge-verdict.py` / judge 角色按「**实际失败集 − known-failures 集 = ∅**」
>   核对，**不得**仅凭「有失败」判 needs-revision；

**脚本实现**（`agate/scripts/check-judge-verdict.py` 全文件已读）：校验链只有 9 步——verdict 存在性（1）、dispatch-context 存在性（2）、Header 字段（3/3b）、BDD 编号/计数对照（4）、passed 三数全等（5）、证据交叉核对（6）、信息隔离白名单（7）、预算交叉（8）、exit2-resolution（8.1）。**无任何一处读取测试失败集或 `known-failures.md`**（`grep -rn "known-failures" agate/scripts/` 仅命中 `check-gate.py` 的 `gate_p5`）。

**更硬的冲突**：`_WHITELIST_MD`（`:81-87`）= `{p1-requirements.md, p2-design.md, .state.yaml, gate-events.jsonl, p6.5-judge-verdict.md}`——**不含 `known-failures.md`**；`_check_whitelist_outside`（`:252-269`）对 judge dispatch-context 的『输入文件』『上游关联』两节做 `.md` 白名单外扫描 ⇒ 主 Agent 若把 `known-failures.md` 列入 judge 输入，`exit 1`（「白名单外任务路径引用」）。而 `judge.md:15` 明确 judge **禁读** `P6-acceptance.md`（PASS 行所在）。

⇒ 「judge 按 known-failures 集机械复核」既**无实现**，又与 judge 信息隔离机制**互斥**（judge 拿不到该文件，PASS 行也读不到）。

**结论**：MISALIGNED
**差异**：文档把一个人工口径（judge 需跨文件核对失败集）表述为 `check-judge-verdict.py` 的机械能力，且未解决与 judge 隔离白名单的冲突。
**建议**：二选一——(a) 若确要 judge 机械复核：把 `known-failures.md` 加入 `_WHITELIST_MD` + 要求 verifier 将失败集落 `P6-evidence/` + 同步 `judge.md` + 补回归测试（真代码改动）；(b) **最省且与本批 doc-only 自洽**：删去 `check-judge-verdict.py` 字样，改写为「**P6 的机械面在 P5**（`gate_p5` 的 baseline diff + `known-failures.md` 登记计数）；P6 judge 按『实际失败集 − known-failures 集 = ∅』**人工**复核」。同步改 CHANGELOG:92、roadmap RM-AG0106、DEBT0055/0056 的「机械复核」措辞。

### A2: 脚本→文档对齐 — ALIGNED（一处措辞不一致）

`check-maintainability.py:26-30` 新增 docstring 段是**纯注释**（脚本行为零变更，`git diff` 仅 docstring 块）。其描述的既定出口与既有实现一致：
- 机械面 = `check-gate.py::gate_p4`（`:1186-1214`）：violations 非空 → `known-violations.md` 存在（门槛 a）+ `count_kf_entries` 条目数 ≥ violation 数（门槛 b）+ P4 评审 approve（门槛 c）；
- 文档面 = `P4-implementation.md:134,172` 与 `known-violations-template.md`。

**结论**：ALIGNED。**唯一不一致**：docstring 新提字段名「**依据（设计条目）**」，而 `known-violations-template.md:14` 的列为 `# | 文件 | 反模式类型 | 违规详情 | 理由 | P4 评审确认`（对应列名是「理由」）。措辞未对齐（归入 A3b）。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（已知衍生改动）**：CHANGELOG（:89-95）、roadmap RM-AG0106（状态 backlog→done + 完成注）、tech-debt DEBT0055/0056（status→closed + 关单证据）三处已同步，✓。

**A3b（主动推断的应被影响但未列在 diff 的文件）**：

| 应被影响文件 | 理由 | 现状 | 判定 |
|---|---|---|---|
| `agate/assets/review-roles/judge.md` | P6 卡把复核口径归给 judge 角色；角色文件是该口径的权威落点 | **未改**（`:19-30` 白名单仍无 known-failures；正文无预存失败豁免口径）| 缺口 |
| `agate/scripts/check-judge-verdict.py` | RM-AG0106「修复」与 DEBT0055 recommendation 均点名此脚本为落点 | **未改**（且与白名单冲突，见 A1）| 缺口 |
| `agate/phase-cards/P5-verification.md` | P6 节自称「与 P5 一致」；P5 的 `pre-task-baseline.md`（机械区分预存/新增的**唯一依据**）未被 P6 节引用 | 未改 | 建议互引（非硬缺口）|
| `agate/assets/templates/known-failures-template.md` | P6 节引用了它 | 未改（模板本身够用）| 可接受 |
| `agate/assets/templates/known-violations-template.md` | docstring 新提「依据（设计条目）」字段 | 未改（列名为「理由」）| 措辞不一致 |
| `agate-workspace/debt/tech-debt.md` DEBT0056 | — | evidence 块**误贴** P6 豁免口径 note（`tech-debt.md:2224-2231`），与维护性越阈无关（复制粘贴残留）| 瑕疵 |

**结论**：MISALIGNED。**差异**：把口径归给 judge 角色却未同步 `judge.md`；把落点点名到 `check-judge-verdict.py` 却未改（且与之冲突）。
**建议**：按 A1 建议 (a)/(b) 决定后同步 `judge.md`；修正 DEBT0056 evidence；对齐模板字段名。

### A4: 测试覆盖 — MISALIGNED

本批为 doc-only + docstring，本身可无测试；但 **DEBT0055 自身 `closure_criteria` #2 = 「回归用例覆盖预存失败存在时的 P6/judge 判定」**（`tech-debt.md:2199`）明确要求回归用例，diff **未新增任何测试**（`grep -rn "预存失败豁免\|known-failures" agate/tests/` 无新用例）。DEBT0055 `recommendation` 落点亦含 `check-judge-verdict.py`（未动）。⇒ 以 `closed` 关单**未满足其自定关单条件**。

**实跑输出**（A4 硬要求）：
```
python3 -m pytest agate/tests/ --reruns 1 -n auto -q
→ 1 failed, 2906 passed, 2 skipped, 1 rerun in 138.70s
```

**结论**：MISALIGNED。**建议**：或补一条覆盖「预存失败存在时 P6/judge 判定」的回归用例，或改写 `closure_criteria` 并说明为何免测（hotfix 等价验证），二者留痕其一。

### A4b: 闭合后既有测试转红 + 夹具更新清单

**经实测无既有用例因本批转红；无需更新任何夹具。**

实跑（同上）：`1 failed, 2906 passed, 2 skipped, 1 rerun`。唯一 `FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——
- 该用例实跑真实 `opencode debug agent orchestrator`（`test_setup_agate_dir.py:298`），断言失败源于本机 opencode 只有 `debug agents` 子命令；
- 与本批改动的文件（P6 卡 / `check-maintainability.py` docstring）**无因果**，且为**先于本批存在**的环境性失败（`docs/reviews/agate-alignment-review-2026-10-09-A0109-ASSET.md:119,197` 同款基线）。

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- 无破坏性变更：P6 卡为**新增节**，`check-maintainability.py` 为**注释**，均不改 gate 行为（既有任务零影响）。
- CHANGELOG 已入 `[Unreleased]/### 修复`（:89-95）✓；CHECK 13（CHANGELOG↔UPGRADING）PASS ⇒ 无需 UPGRADING 章节。
- **文档传播缺口**：`judge.md`（角色文件）未随 P6 口径更新（与 A3b 同源）。是否需同步，取决于 A1 的 (a)/(b) 选择：选 (a) 必改；选 (b)（改为人工复核）也宜在 `judge.md` 留一句口径。
**结论**：NEEDS_HUMAN_REVIEW（需人裁 A1 方案后定传播面）。

### A6: 锚点表覆盖 — ALIGNED

`check-protocol-consistency.py` CHECK 9 锚点表无 P6 预存失败豁免条目，本批未新增 CHECK 9 锚点。因该口径**无对应脚本实现**（见 A1），故**无法也不应**加脚本锚点——锚点缺席本身是 A1 缺实现的镜像，不单独判 MISALIGNED。CHECK 9/10 实跑通过（CHECK 10 仅 1 条 frozen WARNING）。

### A7: 设计原则一致性 — ALIGNED

逐条核对相关 ADR：
- **ADR-015**（门禁只用于实质错误；优先「让错误不可能/可见」，少用「要求人做对」）：② 拒绝引入「设计强制」的 self-declaration 机械豁免，正落在「手段③ 应尽量少用」——无法从 diff 区分「设计强制」与「实现自选」，self-declaration 必被滥用。引 ADR-015 成立 ✓。
- **ADR-014**（判据单一权威源）：② 沿用既有 `known-violations.md` + `gate_p4` 单源，未新增分叉判据 ✓。
**结论**：ALIGNED。（本批不引入新架构决策，无需补 ADR。）

### A8: 声称-命令绑定

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | `check-protocol-consistency.py` **0 ERROR** | `python3 agate/scripts/check-protocol-consistency.py` | ✅ RC=0，0 ERROR（429 条 frozen WARNING）|
| 2 | **2906 passed** | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✅ `1 failed, 2906 passed, 2 skipped, 1 rerun`（1 failed 为环境性）|
| 3 | **`check-debt` rc=0** | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ RC=0 |
| 4 | **roadmap 0 异常** | RM 行全部 9 列（`_ROADMAP_EXPECTED_COLS=9`，`check-gate.py:2138`）；实测 111 条 RM 行均 9 列 | ✅ 0 异常 |
| 5 | **「judge 按『实际失败集 − known-failures 集 = ∅』机械复核」**（P6 卡:48 / CHANGELOG:92 / roadmap RM-AG0106 / DEBT0055-0056 关单证据）| **无命令**——`check-judge-verdict.py` 无该逻辑，且 judge 白名单不含 `known-failures.md` | ❌ **无据声称，须删或改写为「人工复核」** |

**结论**：MISALIGNED（第 5 条）。数字类声称全部可复现。

---

## 5 项重点结论

1. **① 口径 vs P5**：P6 节对 `known-failures.md` 的**定义**与 P5 一致（只登预存失败、模板位置、逐条引用）✓；但 **judge 侧无对应实现**——`check-judge-verdict.py` 不含该逻辑，且 judge 隔离白名单不含 `known-failures.md` ⇒ 「judge 可机械复核」是**声称**，须改写为「judge 按此口径**人工**复核」，或补齐实现+白名单。
2. **② 验收锚是否过宽**：是。把「既定出口 = known-violations 登记」称为「**机械可查**的豁免路径」**过宽**——登记是**人工**动作，机械面（`gate_p4`）只查「文件存在 + 条目数 ≥ violation 数」，不判定「是否确为设计强制」。**准确表述建议**：「两类合法例外均有机械可查的**登记/计数**路径 + 人工评审确认；『是否合法豁免』本身不机械化（ADR-015）」。其中 ① 的机械面实际在 **P5**（`gate_p5` 的 baseline diff），非 P6。
3. **self-declaration 滥用口**：② 未引入机械豁免 ⇒ 无新滥用口，与 ADR-015 一致 ✓。① 存在**残留软滥用口**：P6 节只要求「显式引用 + 列出条目」，无机械 parser，且未引用 P5 的 `pre-task-baseline.md`（机械区分「预存/本次引入」的唯一依据）——理论上可把**本次引入的失败**伪登记进 `known-failures.md` 蒙混（P5 gate 通常已拦，但 P6 口径自身无此防线）。建议 P6 节补一句「豁免项须与 `pre-task-baseline.md` 的预存失败集一致」。
4. **A4b**：`-n auto` 实跑 `1 failed, 2906 passed, 2 skipped, 1 rerun`——**无既有用例因本批转红**，唯一 failed 为先存环境性 `test_bdd_43`，**无夹具需更新**。
5. **A8**：`0 ERROR` / `2906 passed` / `check-debt rc=0` / `roadmap 0 异常` **逐条复现 ✓**；「judge 机械复核」**无据，须删或改写**。

---

## 修复方向（最小集，供主 Agent 派 implementer）

1. **P6 卡:48** 删去 `check-judge-verdict.py` 字样 → 「judge 角色按『实际失败集 − known-failures 集 = ∅』**人工**复核」；并补「P6 机械面在 P5（`gate_p5` baseline diff + 登记计数）」与「豁免项须与 `pre-task-baseline.md` 预存集一致」。
2. 同步改写 **CHANGELOG:92 / roadmap RM-AG0106 / DEBT0055-0056 关单证据**中的「机械复核」措辞（避免同一无据声称留在记录里，A8 原则）。
3. **`judge.md`** 增一句预存失败豁免口径（或明确「P6 豁免由 P5 机械面 + P6 judge 人工判定」）。
4. **DEBT0055**：补回归用例，或改写 `closure_criteria` #2 并说明（其 `recommendation` 落点含 `check-judge-verdict.py`，若选「人工复核」路线应同步删该落点）。
5. **DEBT0056 evidence**（`tech-debt.md:2224-2231`）：删去误贴的 P6 豁免口径 note。
6. **`known-violations-template.md`**：把「理由」列名与 docstring「依据（设计条目）」对齐（二选一）。

> 若采用「补齐 judge 机械实现」路线（A1 建议 a），则须改 `check-judge-verdict.py` + `_WHITELIST_MD` + 回归测试，并重跑本报告 A4/A4b。

---

## 闭环

| 结论 | 项 | 动作 |
|------|----|------|
| MISALIGNED | A1 / A3 / A4 / A8 | **必须修复**（修文档或脚本，修完重审）|
| NEEDS_HUMAN_REVIEW | A5 | 人工确认 A1 方案（人工复核 vs 补实现）后，附 `[HUMAN_CONFIRMED: …]` 方可 commit |
| ALIGNED | A2 / A6 / A7 / A4b | 通过 |
