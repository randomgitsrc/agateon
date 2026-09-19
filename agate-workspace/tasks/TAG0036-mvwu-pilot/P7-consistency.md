---
phase: P7
task_id: TAG0036
type: consistency
parent: P2-design.md
trace_id: TAG0036-P7-20260919
status: draft
created: 2026-09-19
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0
deviation_count: 4
deviation_critical_count: 0
design_gap_count: 0
design_gap_reviewed_count: 0
---
# P7 一致性检查 — TAG0036 MVWU 阶段 1 试点（RM-AG0063）

[PROD_NOT_TOUCHED] 只读审查：未改任何代码/文档，未 git add/commit，未触碰 `~/.agate`；所有命令均带 `timeout`（或为瞬时只读 grep/git）。

**结论**：BLOCKER=0，DEVIATION-CRITICAL=0，DEVIATION=4（均非阻断，见 §9，含处置建议）；DESIGN_GAP 0 条（无待配对项）；无 SCOPE+。跨文件检查逐项引用了源文件节名（P1 BDD / P2§0.1 / P2§dispatch_plan / P2§packages / P4 implementation 各批 / P6 / P6.5）。

## 1. DESIGN_GAP 配对

- P4 implementation 记录（主文件 `P4-implementation.md` + 5 个批文件 `P4-implementation-{architect-batch-guidance,batch-evidence-landing,review-anchors-and-decision-recheck,mvwu-glossary-and-debt-log,mvwu-script-registry}.md`）与 `P4-progress.md` 中**无任何 DESIGN_GAP 声明**：
  - 搜索命令：`grep -nE '^\s*>?\s*-?\s*\[DESIGN_GAP' P4-implementation*.md P4-progress.md` → **0 命中**（gate 同款行首正则）。
  - 宽松搜索：`grep -n 'DESIGN_GAP' P4-implementation*.md P4-progress.md` → 6 命中，全部为「无 DESIGN_GAP / 本批无 `[DESIGN_GAP]`」的否定声明（`P4-implementation.md:30`、`P4-implementation-architect-batch-guidance.md:37`、`P4-progress.md:10/11/12/14`），无一为声明。
  - P4 implementation 主文件 §1 明言「未偏离 P2/P1，本批无 DESIGN_GAP / SCOPE+ / CLARIFY」。
- 结论：**P4 无 DESIGN_GAP**。`design_gap_count: 0` / `design_gap_reviewed_count: 0`，无需转抄与 REVIEWED 配对（本文正文不含行首 DESIGN_GAP / REVIEWED 标记，与 frontmatter 一致）。

## 2. SCOPE+ 闭环 与 BASELINE_CHANGE

- `grep -nE '^\s*>?\s*-?\s*\[SCOPE\+' P1-requirements.md` → **0 命中**：**无 SCOPE+**；P4 各批文件亦无 SCOPE+ 声明（见 §1）。P1 无 `[SCOPE_RESOLVED]` 属正常（无 SCOPE+ 则无需闭环；`check-gate.py` 内无 SCOPE 相关校验，已 grep 确认）。
- `[BASELINE_CHANGE]` 核对：
  - P1 留痕：`P1-requirements.md:505`（BDD-70 下方）正文含 `[BASELINE_CHANGE: P2 评审（plan-eng-review B1）实测 … 主 Agent 批准（2026-09-19）…]`；P1 §4.3 表（`P1-requirements.md:559`）该行由「本次不处理」改为「处理（P2 评审纠正）」。
  - P2 一致：`P2-design.md` §0.1 M18（`GATE_SCRIPT_EXEMPT` 加 `check-mvwu.py` 一行）、§0.2 中 `check-protocol-consistency.py` 行、§0.3 R2/R14、§8 均引用该批准，且 P2 §8 末明写「无 SCOPE+：M18 已被 P1 BASELINE_CHANGE 覆盖」。
  - 实际改动：`git diff efb113b -- agate/scripts/check-protocol-consistency.py` 仅 1 行新增（`"agate/scripts/check-mvwu.py",  # 观测脚本，不挂 gate`，位于 `GATE_SCRIPT_EXEMPT`），锚点表零改动 → 与 M18 逐字一致。
  - 为何不属 SCOPE+：它是 P2 评审阶段依实测发现的**既有测试约束**（`test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts` 对任何新增 `check-*.py` 的既有反应；P2 §0.3 R14 全仓 grep 佐证仅 2 处消费该 glob），并未引入新需求或改变任何 BDD 的 Given/When/Then（P1 原文明写「不改本 BDD 语义，仅补充达成条件」）；由主 Agent 批准并在 P1 留痕，走的是基线纠正而非 P4 增补流程。
- 结论：SCOPE+ 无；BASELINE_CHANGE 在 P1/P2/实际改动三处一致。

## 3. 数量对齐

| 项 | 来源 | 结果 |
|----|------|------|
| P1 `#### BDD-NN:` 标题数 | `grep -c '^#### BDD-' P1-requirements.md` = **71**，编号 1..71 连续无缺 | 71 |
| P6 验收条数 | `P6-acceptance.md` frontmatter `pass: 71 / fail: 0`；`grep -c '^- PASS BDD-\|^- FAIL BDD-'` = 71，编号 1..71 | 71 |
| P6.5 judge | `P6.5-judge-verdict.md` frontmatter `criteria_total: 71` / `criteria_passed: 71` / `status: passed`；逐条 `- PASS BDD-` 行 = 71 | 71 |
| P3 映射覆盖 | `P3-test-cases.md`（归属行第 15 行：docs 半边 = BDD-1、2、3、5-12、59-71；script 半边 = BDD-4、13-55、57、58；BDD-56 = P6 证据）+ `P3-test-cases-docs.md`；实测 `def test_bdd_NN` 覆盖 1..71 中除 56 外全部（唯一缺口 BDD-56 与 P3 声明一致，且由 `P6-evidence/bdd-56-observe-real-task.log` 补足） | 1..71 无遗漏 |

- 结论：P1 71 = P6 71 = P6.5 71；BDD-56 属 P6 证据（`P3-test-cases.md:87`）。P5 数字（1842 passed / 2 skipped）与 P6 `count-tests.log`、`tests/README.md` 相符（1668 + 111 + 65 = 1844 含 2 skipped 口径，见 §7 用例数项）。

## 4. P2 ↔ P4 ↔ 实际改动

**P2§0.1 M1-M18 逐项对 P4 implementation 与 `git show --stat 4ee499f`：**

| M | P2§0.1 声明 | P4 implementation 落点 | `4ee499f` 实际 | 结论 |
|---|------------|------------------------|-----------------|------|
| M1 | 新建 `scripts/check-mvwu.py` | `P4-implementation.md` §1（批 mvwu-verdict-observer） | `agate/scripts/check-mvwu.py` +484 | 对得上 |
| M2/M3/M4 | `phase-cards/P2-design.md` 三处新增 | `P4-implementation-architect-batch-guidance.md` §1 表 | `agate/phase-cards/P2-design.md` +46 | 对得上 |
| M5 | `architect.md` 批次设计末尾新增 | 同上 | `architect.md` +34（纯新增，P6 BDD-7 证硬规则 0 删除） | 对得上 |
| M6 | `phase-cards/P4-implementation.md` 新节 | `P4-implementation-batch-evidence-landing.md` | `P4-implementation.md`(卡) +18 | 对得上 |
| M7 | `task-files.md` 两处 | 同上 | `task-files.md` +2 | 对得上 |
| M8 | `role-system.md` 新节 | `P4-implementation-review-anchors-and-decision-recheck.md` | `role-system.md` +14 | 对得上 |
| M9 | `adr.md` 头部新节 | 同上 | `adr.md` +6 | 对得上 |
| M10 | `P7-consistency.md`(卡) 第 6 项 | 同上 | `P7-consistency.md` +1 | 对得上 |
| M11 | `CONTEXT.md` 追加恰 5 行 | `P4-implementation-mvwu-glossary-and-debt-log.md` | `CONTEXT.md` +5（MVWU / tests_filter / P4-evidence / 四态 verdict / boundary(I1)） | 对得上 |
| M12 | `tech-debt.md` 追加 DEBT0043 | 同上 | `tech-debt.md` +26；`grep DEBT0043` 命中 `## DEBT0043` | 对得上 |
| M13 | `scripts/README.md` 一行 | `P4-implementation-mvwu-script-registry.md` | `scripts/README.md` +1 | 对得上 |
| M14 | `tests/README.md` 新增测试文件行 | 同上 | `tests/README.md` +2（两行：`test_check_mvwu.py`、`test_mvwu_protocol_docs.py`） | 对得上 |
| M15 | `CHANGELOG.md [Unreleased]` 替换占位 | 同上 | `CHANGELOG.md` +15/-1 | 对得上（但见 D1） |
| M16 | P3 新建测试文件 | P3（`e0513d0`）非 P4 | `test_check_mvwu.py`/`test_mvwu_protocol_docs.py` 在 P3 建立；`4ee499f` 内二者仅小改（+17 / 1 行注释） | 见 D4 |
| M17 | `P4-protocol-alignment-review.md` | P4 收口产物 | `4ee499f` 含该文件（195 行） | 对得上 |
| M18 | `check-protocol-consistency.py` 加 1 行 | `P4-implementation.md` §1 | `check-protocol-consistency.py` +1 | 对得上 |

- **P2§dispatch_plan 的 6 个批 id**（`mvwu-verdict-observer` / `architect-batch-guidance` / `batch-evidence-landing` / `review-anchors-and-decision-recheck` / `mvwu-glossary-and-debt-log` / `mvwu-script-registry`）：与 P4 批文件名一一对应（主文件承载 `mvwu-verdict-observer`；其余 5 个 `P4-implementation-<id>.md`），且 `P4-implementation.md` §2 批次索引 6 行 id 与之逐字相同，含改名后的 `architect-batch-guidance`（P2§14 N2）。批产出面均 ≤3 文件，P2§6「同一文件不跨批」成立（各文件仅出现在一个批的 §1 表内）。
- **P2§packages**（`agate-scripts` / `agate-docs` / `agate-tests`）与实际改动面：`agate/scripts/*`（check-mvwu.py、README、consistency 一行）= agate-scripts；`agate/` 下 phase-cards / role-system / adr / CONTEXT / templates / architect.md、根 CHANGELOG、`tech-debt.md` = agate-docs；`agate/tests/*` = agate-tests。无落在三包之外的产品文件。
- **`git diff efb113b --stat`（104 文件）无 P2 未声明的文件**：产品面文件（`agate/` 下 16 个 + 根 `CHANGELOG.md` + `agate-workspace/debt/tech-debt.md`）全部在 M1-M18 内；其余均为任务目录 `agate-workspace/tasks/TAG0036-mvwu-pilot/` 下的过程产出。**唯一例外**：仓库根 `HANDOFF-TAG0036.md`（+174，来自基线之后、P0 之前的提交 `c93a02d docs: TAG0036 交接单`），P2 未声明，见 D3。
- **P4 §impl-path 与 P2 方案 A**：`check-mvwu.py` 单文件自包含，仅 `import agate_common`（`run_git` / `split_frontmatter` / `resolve_workspace`），与 P2§1「候选方案 A」及 §2.2 一致；P4 §1「关键设计选择」（六步流水线、`realpath` 包含性、永不执行 command、任何 verdict exit 0）逐条对应 P2§0.3 R9/R10 与 §2.2。

## 5. P0 完成判据 ↔ 交付物

（P0-brief「完成判据」表实为编号 1、2、3、3b、3c、4、5、6、7、8、9、10、11 共 13 行；逐行核对。）

| P0 判据 | 交付文件与位置 | 佐证 | 结论 |
|---------|----------------|------|------|
| 1 `tests_filter` 键可用 | `phase-cards/P2-design.md`「batches[] 可选键：tests_filter / output…」（M2）；`task-files.md` dispatch_plan 注释（M7②） | P6 BDD-1/2（`direct-bdd-1-2-4-tests-filter-gate.log`）：写入/读回/`_gate_p2_dispatch_plan` 放行；DEBT0043 登记 fail-open（M12） | 已交付 |
| 2 `P4-evidence/{batch}.log` 落点 | `phase-cards/P4-implementation.md`「批级证据 P4-evidence」节（M6）；`task-files.md` 阶段产出表 P4 行（M7①） | P6 BDD-10/11（`docs-bdd-10-11-evidence-landing.log`）；`grep P4-evidence agate/rules` = 0（BDD-12） | 已交付 |
| 3 `check-mvwu.py` 可用 | `agate/scripts/check-mvwu.py`（M1）；`scripts/README.md`（M13） | P6 BDD-13..46、`pytest-check-mvwu-verbose.log` 111 passed | 已交付 |
| 3b `--observe` 可用 | 同上（7 列表格行，见脚本 `--help` 与 `--observe` 段） | P6 BDD-43..55、`direct-bdd-45-huge-duration.log`、`direct-bdd-47-48-49-50-git-range.log` | 已交付 |
| 3c 字段落地路径 | `phase-cards/P2-design.md`（M2）+ `assets/execution-roles/architect.md`「批切分判据与 tests_filter 写法」（M5） | P6 BDD-6/7/8/9 | 已交付 |
| 4 Q2 结论在案（13%） | P0 判据表本身标「已完成（不需试点）」；`P1-requirements.md:76,610`（「Q2=13%（任务级 2/16）为引用结论」）；权威源为设计文档 `docs/design-notes/design-mvwu-protocol.md`（`:21`、`:150-153` §3.1 B 档 2/16=13%、`:172-178`） | `agate/` 下**无**文件复述 13%（`grep 13% agate/…` 0 命中）：P0 未要求交付物文件，判据本就是「已完成/引用」；`CONTEXT.md` MVWU、boundary(I1) 行的来源列指向该设计文档 | 已满足（引用式），非缺失；见 §9 INFO-1 |
| 5 Q1/Q3 采集流程就绪 | 同 3b（`--observe` 产出观察行） | 同 3b | 已交付 |
| 6 `--observe` 真实任务跑通 | `P6-evidence/bdd-56-observe-real-task.log`：在真实任务 `TAG0035-gate-robustness` 上实跑，exit 0，4 批 → 4 行、GFM 切分均为 7 列 | P6 BDD-56（唯一无单测的 BDD，P3 已声明由 P6 证据承担）；P6.5 复核 PASS | 已交付（样本为全 UNKNOWN 行，符合判据 6「工具跑通而非样本量」） |
| 7 ⑤-a 术语补录 | `agate/CONTEXT.md` 末尾 5 行（M11），三列格式 | P6 BDD-59（`docs-bdd-59-context-terms.log`）；行数 +5 且既有行零改动 | 已交付 |
| 8 ⑤-b Deep Modules 锚点 | `agate/role-system.md`「审查锚点：角色文件是否浅化接口（Deep Modules，TAG0036）」（M8） | P6 BDD-60（`docs-bdd-60-role-system-anchor.log`）；仅成文 | 已交付（成文） |
| 9 ⑤-c 三判据 | `P2-design.md`(卡)「批切分判据」判据一 Tracer Bullet / 二 Vertical Slice /「架构适应度检查」（M2/M3）+ `architect.md`（M5） | P6 BDD-61/63/64 | 已交付 |
| 10 ⑤-d Walking Skeleton | `P2-design.md`(卡) 判据一内一条：「骨架先跑通」**吸收**、部署/CI 部分**拒绝**（依据 `adr.md` ADR-003 不绑定技术栈；并与既有 `P2-skeleton.md` 消歧） | P6 BDD-62；无独立交付物，符合判据 | 已交付（成文） |
| 11 ⑤-e 决策复审 | `adr.md`「复审触发条件（过时不删）」（M9）；`P2-design.md`(卡)「项目侧架构决策（decisions/）」（M4）；`P7-consistency.md`(卡) 第 6 项（M10） | P6 BDD-65/66 | 已交付（成文） |

- **未被交付的项**：无。判据 4 无独立交付文件属 P0 设定（已完成，仅引用），不判 BLOCKER。

## 6. P0 范围 / out-of-scope 遵守

- **零内核**：`git diff efb113b --stat` 针对 `agate/scripts/check-gate.py`、`agate/rules/`（含 `phases.yaml`、`schema/`）、`agate/scripts/agate_common.py`、hook 三件套、`pre-commit-gate.py`、`agate-md-field-get.py`、`check-p6-provenance.py`、`agate-archive-stale-outputs.py`、`assets/review-roles/`（含 `judge.md`）、`dispatch-protocol.md`、`UPGRADING.md`、`WORKFLOW.md`、`.github/` → **全部空 diff**（`--name-only` 计数 0）。唯一被改的相邻文件是 `check-protocol-consistency.py`（M18，非零内核清单，有 P1 BASELINE_CHANGE 依据，见 §2）。`grep -rn P4-evidence agate/rules` = 0；`docs/` 空 diff（设计文档未回改，P2§0.2）。
- **不挂 gate**：`check-mvwu.py` 无任何 gate/hook/CI 登记（`GATE_SCRIPT_EXEMPT` 仅豁免 CHECK 9；`--help` 明写「不挂 gate、不挂 hook、不进 CI」，任何 verdict exit 0）。
- **不替用户裁决提交粒度**：P2§6「提交形态」明写「不依赖用户裁决 A/B，P2 不替用户选」；本任务产出无相关裁决文字；P4 提交形态为单个合并 commit `4ee499f`，属主 Agent 操作，未在文档中裁决。
- **不造样本**：任务目录无 `P4-evidence/`（`ls` 确认不存在）；P2§6 dogfooding 判断「不写 tests_filter/output」与实际一致；`BDD-68` 历史任务目录不变（`P5_history_untouched` 在 P6 `diff-p5-four-commands.log` exit 0）。
- **⑤-b/⑤-d 只成文不宣称生效**：抽查 P4 新增文档（`git diff efb113b` 于 `P2-design.md`(卡)、`role-system.md`、`architect.md`、`P4-implementation.md`(卡) 的新增行）对「已生效 / 已验证 / 已落地生效」grep → 0 命中；`role-system.md` Deep Modules 节与 `P2-design.md`(卡) Walking Skeleton 行均为判据式/「吸收 / 拒绝」措辞。

## 7. 既有一致性面

- **`agate/scripts/README.md` 的 `check-mvwu.py` 行 ↔ `--help`**：README 写「每批输出一行 `MVWU_RESULT: <VERDICT> batch=<id>`（PASS/FAIL/EXPECTED_RED/UNKNOWN）；`--observe`=7 列观察表行；仅观测不阻断；退出 0=任一 verdict、2=用法/目标错误」，与实测 `check-mvwu.py --help` 的契约行格式、四态、`--observe` 7 列（`| MVWU | tests_filter | 耗时 | evidence | commit 形态 | boundary | verdict |`）、退出码（0 / 2）逐项一致。
- **`agate/tests/README.md` 用例数 ↔ 实测**：`pytest --collect-only -q` 实测 `test_check_mvwu.py` = **111**、`test_mvwu_protocol_docs.py` = **65**；README 两行分别为 111 / 65 → 一致。
- **CHANGELOG `[Unreleased]` ↔ 实际交付**：条目（check-mvwu 观测器 / tests_filter 可选键 / P4-evidence 落点 / ⑤ 组成文与登记）与 M1-M15 一致，未写「机制已生效」；但其中 `test_check_mvwu.py` 用例数写 **109**，而实际已因评审后修复变为 **111** → **D1**。
- **`CONTEXT.md` 5 条新术语 ↔ `agate/` 内实际用法**：`MVWU`（来源设计文档）；`tests_filter`（双引号包裹、只覆盖本批、禁止全量、缺省 gate 行为不变——与 P2 卡 M2 契约一致）；`P4-evidence`（主 Agent 批 commit 前机械转录、不阻断——与 P4 卡 M6 一致）；`四态 verdict`（`UNKNOWN 不等价于 PASS`——与脚本 docstring 固定锚点一致）；`boundary(I1)`（定义句沿用设计文档 I1「PASS/FAIL」表述，末尾括注「`--observe` 列取值 `exact` / `mismatch` / `UNKNOWN`；不参与 verdict」，与脚本 `check-mvwu.py:395` 实际取值 `exact`/`mismatch`（per-batch）及 UNKNOWN 一致）——P4-protocol-alignment-review A2 的 NEEDS_HUMAN_REVIEW 已据此处置（见 §8）。术语来源列 `docs/design-notes/…` 为仓库根路径，与其他行的 `agate/` 相对路径写法不一致，见 INFO-2。
- **`decisions/` 落点三处一致（并实际执行 P7 卡第 6 项核对）**：
  - P2 卡（M4）：「项目内跨任务架构决策落 `{AGATE_WORKSPACE}/decisions/`；P2 开始前读取；写入时机 = P2 定稿后；前提被证伪就地标注『已过时 + 被什么取代』不删除」。
  - P7 卡（M10 第 6 项）：「核对 `decisions/` 落点与过时标注……仅核对，不 author 决策正文；缺失项记为待办，由提出方在下一次 P2 前补写」。
  - `adr.md`（M9）：「前提被证伪就地标注『已过时 + 被什么取代』，不删除；复审时机 = 新增 ADR 时 + P7 一致性检查」。
  - 三处均含「已过时 + 被什么取代」「不删除」；时机表述互补不冲突（P2 定稿后写 / P7 核对 / 下一次 P2 前补）。
  - **本次实核**：`{AGATE_WORKSPACE}/decisions/` 目录在本仓库检出中**不存在**（空目录不入 git；`SETUP.md:316` / `state-machine.md:42` 创建语句仍准确，P2§0.2 已论证不改）。本任务**无跨任务架构决策**需落 `decisions/`（M18 的 `GATE_SCRIPT_EXEMPT` 是任务内、已在 P1 BASELINE_CHANGE 与代码注释留痕的取舍；「MVWU 提交粒度取舍」按 P0 out-of-scope 须由用户裁决、本任务未做，属待裁决议题而非已作决策）。无需建议补写。

## 8. 未决项清零

- `grep -nE '^\[(NEED_CONFIRM|BLOCKER|DEVIATION-CRITICAL)' P1-requirements.md P2-design.md` → **0 命中**（P1 仅有行首 `[NO_NEED_CONFIRM]`，见 `P1-requirements.md:29,584`）。
- `P2-design.md`：无行首 `[SUGGEST` / `[NEED_CONFIRM]`（宽松搜索仅命中 §6 dogfooding 一条句中 `[SUGGEST: …]`，`P2-design.md:250`；该建议「本任务自身批不写 tests_filter/output」已被事实采纳——任务目录无 `P4-evidence/`，P4 各批亦未写 tests_filter；§8 明言「维持不变」）。`P2-review.md`（第 3 轮）`status: approved`，B1/B2/B3/N1-N4 全部闭合，「架构问题（阻塞级）：无」。
- `P4-review.md`：`status: approved`（0 BLOCKER）；其 MAJOR（`--observe` 耗时列遇超长数字吞行）**已处置**：`P4-implementation.md`「评审后修复」节记录三层修复，核实于代码——`check-mvwu.py:61` `DURATION_RE = [0-9]{1,15}(?:\.[0-9]{1,15})?`、`:146` `except (ValueError, OverflowError)`、`:438/458` per-row `internal error` 兜底；新增单测 `test_bdd_45_observe_huge_duration_does_not_drop_rows`，`--collect-only` 实测 111 = 109 + 2 参数化，P6 `direct-bdd-45-huge-duration.log` 有独立实跑。
- `P4-protocol-alignment-review.md`：`status: approved`，A1/A3-A7 ALIGNED，A2 一条 NEEDS_HUMAN_REVIEW（`boundary(I1)` 术语口径）**已处置**：`CONTEXT.md:42` 行末已补「（`--observe` 列取值 `exact` / `mismatch` / `UNKNOWN`；不参与 verdict）」，原措辞未删（`P4-implementation.md`「评审后修复」第 2 条），与脚本 `:395` 取值一致。
- P6.5 阶段的 judge dispatch-context 措辞误报已由 `P6-gate-diagnosis.md` 记录（纯措辞、判案范围未变），不产生未决项。

## 9. CODE-MAP / 骨架 与 偏差清单

**骨架**：项目未采用 `P2-skeleton.md`（任务目录无该文件；`P4-implementation.md` §3 亦如此声明）——骨架机制未采用，跳过。

**CODE-MAP**：与派发指引预设不同，`{AGATE_WORKSPACE}/agents/CODE-MAP.md` **存在**（96 行，TAG0007 起的 dogfooding 实例，末次更新 TAG0033），而 `P4-implementation.md` §3 写「本项目未采用……CODE-MAP（无 `agents/CODE-MAP.md`）」——该陈述与事实不符。P4「新增文件核对表」唯一新增文件 `agate/scripts/check-mvwu.py`，人工核对结论：

- 依赖方向：CODE-MAP「依赖方向」节允许 `phase-cards/templates → scripts` 与 scripts 消费公共库；`check-mvwu.py` 仅单向 import `agate_common`、无反向定义流程语义，未违反禁止项 → 方向合规。
- 记录同步：CODE-MAP「模块 / scripts」节按脚本族逐族登记（最近的按 TAG 追加了 ceremony/judge/推进侧/命令流各族），`check-mvwu.py`（观测族）**未登记**（`grep mvwu CODE-MAP.md` = 0）。
- 判定：`[CODE_MAP_DRIFT: agate/scripts/check-mvwu.py 为新增脚本，CODE-MAP.md 未记录（依赖方向合规，仅记录缺口）——WARNING 级，见 D2]`。gate 侧 `code_map_*` 两字段按派发指引不填，机制在 `check-gate.py` 中仅当两字段均声明才校验（同时 P4 无 `[CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT]` 标记，故不会触发转抄核对层），不阻断。

### 偏差清单（均非阻断；无 BLOCKER / DEVIATION-CRITICAL）

[DEVIATION D1] `CHANGELOG.md [Unreleased]` 写 `test_check_mvwu.py` 109 用例，实际（`pytest --collect-only`）与 `agate/tests/README.md` 均为 111（P4 评审后修复新增 2 个参数化用例，README 已同步 109→111，CHANGELOG 未同步）。处置建议：P8 发布准备前将 CHANGELOG 该处 109 改 111（一行文档修正，无需回派 P4；`P4-implementation-mvwu-script-registry.md` 亦写 109，属修复前快照，不必改）。

[DEVIATION D2] `P4-implementation.md` §3 声称项目无 `agents/CODE-MAP.md`，实际存在；且 `check-mvwu.py` 未登记进 CODE-MAP（`[CODE_MAP_DRIFT]` WARNING 级）。处置建议：主 Agent 二选一——① 于 P8 前在 `agents/CODE-MAP.md`「scripts」节追加一行 MVWU 观测族（新增 TAG0036：check-mvwu.py，只读观测、不挂 gate、单向依赖 agate_common），并顺带更正 P4 §3 措辞；② 若判定观测脚本不属 CODE-MAP 记录粒度，则在 P8 记录一句豁免理由。不影响 P5/P6 结论（无代码行为差异）。

[DEVIATION D3] 仓库根 `HANDOFF-TAG0036.md`（174 行，基线后提交 `c93a02d`，早于 P0）出现在 `git diff efb113b --stat` 中，P2§0.1/§0.2 未声明。它是任务交接单，非协议产品面，与 P2 packages 无关。处置建议：主 Agent 在 P8 / PR 前决定是否随本分支合入或移出（属提交范围决策，P7 不裁决）；不影响一致性结论。

[DEVIATION D4] 追溯缺口：`4ee499f` 内 P3 红灯基线文件被 P4 阶段小改——`test_check_mvwu.py` +17（`test_bdd_45_observe_huge_duration_does_not_drop_rows` 2 参数化，评审后修复，已在 `P4-implementation.md`「评审后修复」记录）与 `test_mvwu_protocol_docs.py` 1 行注释措辞（"testfix" 批，仅记于 `P4-progress.md`，`P4-implementation.md` §2 批次索引与「评审后修复」均未提及）；P2§0.1 M16 声明测试文件属 P3 新建。两处改动均为合理的评审后修复/规避 R4 平台扫描命中，P5/P6 已实测全绿，非行为偏离。处置建议：P8 或 P7 之后无需回派，仅在 P8 记录中如实带一句；若追求台账完备，可由主 Agent 在 `P4-implementation.md` 评审后修复节补一行 testfix（本审查不改文件）。

### INFO（不计入偏差）

- INFO-1：判据 4（Q2=13%）在 `agate/` 内无文字复述，仅存在于 P0/P1 与设计文档 §3.1；符合 P0「已完成（不需试点）」设定，仅提示后续若需 `agate/` 内自证，可在术语行来源处保留设计文档指向（现已有）。
- INFO-2：`CONTEXT.md` 新增 3 行来源列写 `docs/design-notes/design-mvwu-protocol.md`（仓库根 `docs/`，不在 `agate/` 发布包内），与既有行的 `agate/` 内相对路径风格不同；`check-protocol-consistency.py --strict-errors-only` 在 P5/P6 为 0 ERROR，不构成失败。
- INFO-3：派发指引把 P0 判据称作「11 条」，P0-brief 表实为 13 行（编号 1、2、3、3b、3c、4-11）；本审查按 13 行逐条核对。
- P8 提示：P2 packages 三值（`agate-scripts` / `agate-docs` / `agate-tests`）与 P8「从 P2 packages 逐包读取 version 文件」的对接由 P8 阶段核对，本轮无法提前验证（P8 未开始）。

## 10. 汇总

| 门槛项 | 结果 | 锚点 |
|--------|------|------|
| BLOCKER = 0 | 满足 | §1 DESIGN_GAP 0 命中（P4 implementation 全部批文件 + progress）；§2 SCOPE+ 0 命中；§8 未决项清零 |
| DEVIATION-CRITICAL = 0 | 满足 | §3 P1 BDD 71 = P6 71 = P6.5 71；§4 P2§0.1 M1-M18 / P2§dispatch_plan / P2§packages 与 `4ee499f` 对齐；§5 P0 13 行判据全部有交付 |
| DESIGN_GAP 配对 | 无待配对项 | §1，`design_gap_count: 0` |
| SCOPE+ 闭环 | 无 SCOPE+；BASELINE_CHANGE 三处一致 | §2 |
| DEVIATION（非阻断） | 4（D1-D4） | §9，均附处置建议 |
