---
phase: P7
task_id: TAG0035
type: consistency
parent: P2-design.md
trace_id: TAG0035-P7-20260916
status: draft
created: 2026-09-16
agent: consistency-reviewer
blocker_count: 0
deviation_count: 0
deviation_critical_count: 0
design_gap_count: 2
design_gap_reviewed_count: 2
code_map_new_files_count: 0
code_map_reviewed_count: 0
---

# P7-consistency — TAG0035-gate-robustness

> 对照 P1-P6（含 P6.5）全部产出做跨文件一致性交叉检查。全部文件已逐一读取，见
> P7-progress.md 的逐条读取记录。

## 1. DESIGN_GAP 逐条转抄 + REVIEWED（本任务 2 条）

### DESIGN_GAP 1（子批 A，源文件 P4-implementation.md「自测结果」节）

[DESIGN_GAP: 全量跑第一次（改动前状态核对）时，`test_other_unknown_phase_exit_2`
（`agate/tests/unit/test_check_gate.py:199-204`，TAG0035 之前已存在的旧用例）断言未知
阶段 `P9` 应 `exit==2`，与本批新增的 BDD-1（同一场景应 `exit==1`）语义矛盾。经与主
Agent 确认：该矛盾判定明确，非业务分歧——这条存量用例断言的正是 BDD-1（P1-requirements.md
既定验收标准）要修复掉的旧行为本身，字面过时，需同步更新，不构成 `[BASELINE_CHANGE]`。
已同步修正：`test_other_unknown_phase_exit_2` 更名为 `test_other_unknown_phase_exit_1`，
断言值 `2`→`1`（加注释说明来由），未改动该测试之外的任何内容。]

[DESIGN_GAP_REVIEWED: 已核实 P4-review.md§约束2 第 1 条独立评审结论——"已读该测试
（`test_check_gate.py:199-204`），断言场景是'未知阶段 P9 应 exit=?'，这正是 BDD-1 要
修复的目标行为本身（未知阶段 fail-open→fail-closed），断言值从 2 改 1 是同一测试场景
对新行为的必然更新，不是误改了一条无关测试。判定：合理。"——该结论是独立复核（非
implementer 自证），临时还原判据未变，逐一核对无遗留矛盾，与 P1-requirements.md BDD-1
原文验收标准（未知阶段 exit=1，不再是 2）完全对应。判定：REVIEWED，无 BLOCKER。]

### DESIGN_GAP 2（子批 B，源文件 P4-implementation-B.md「2. check-state-transition.py」节）

[DESIGN_GAP: dispatch-context 约束 2 给出的判空条件原文（`old_phase and old_num is None`）
只特判了 `old_phase` 为空字符串这一种合法非数字场景，未覆盖 `old_phase` 为控制态
`PAUSED`/`READY`/`DONE`（`get_old_phase` 可合法返回这三者，对应 PAUSED 恢复等场景）。
按原文字面实现会让既有回归用例 `test_st_15_paused_to_p4_recovery_exit_0` /
`test_st_19_commit_gate_paused_recovery_skipped_exit_0` 从通过变为失败（新增回归）。
已将 `PAUSED`/`READY`/`DONE` 与空字符串同等对待为合法 `old_num=0`，不触发判空报错——
该三个字面量与本文件 L246 `new_phase` 特判用的是同一组控制态常量，处理方式对称。
BDD-5 的两个参数化子场景（`old_phase="p-alpha"`/`new_phase="p-alpha"`）不受影响，仍按
预期 fail-closed。]

[DESIGN_GAP_REVIEWED: 已核实 P4-review.md§约束2 第 2 条独立评审结论——"已独立验证：
临时把该扩展判据还原为仅判空字符串（`old_num = 0 if not old_phase else phase_num(old_phase)`），
重跑 `test_st_15_paused_to_p4_recovery_exit_0` 与 `test_st_19_commit_gate_paused_recovery_skipped_exit_0`，
两条既有回归测试确实从 pass 变为 fail（`AssertionError: assert 1 == 0`），随后已恢复
原文件并确认 47 个用例全部转回 pass。这不是'编出来的理由'，是真实存在的回归依赖，
扩展判据是必要的，处理恰当。"——该验证是红队式"临时还原→观察是否回归失败→再恢复"的
独立实测（非仅代码阅读），证明该扩展超出 dispatch-context 原始判空条件字面范围是必要
扩展而非擅自扩权。判定：REVIEWED，无 BLOCKER。]

## 2. SCOPE+ 闭环核实

已重新核对 P1-requirements.md 全文（第 1-262 行）：全文未出现 `SCOPE+` 或 `[SCOPE_RESOLVED]`
标记。本任务范围在 P0-brief/P1/P2 三阶段已多次收窄锁定（DEBT0040/DEBT0041 已在 P1 §1
「out-of-scope」段明确移出，`[SUGGEST: 子批 B 完整案...]`已转为独立议题建议而非
SCOPE+ 增补）。**结论：未发现 SCOPE+ 声明，无需闭环。**

## 3. 跨文件一致性核对（逐项给出具体锚点）

### 3.1 P1 的 14 条 BDD 编号 vs P6 的 14 条 PASS/FAIL 结果——数量匹配 + 编号一一对应

P1-requirements.md§3「BDD 验收条件」声明 BDD-1~BDD-14（4 子批依次编号，全局唯一，无跳号无重号，
逐条核对：BDD-1/2/3 子批A，BDD-4/5/6/7 子批B，BDD-8/9/10 子批C，BDD-11/12/13/14 子批D）。
P6-acceptance.md§「逐条 BDD 结果」逐条核对如下（源:结果，编号一一对应，非仅数量匹配）：

| BDD | P1 原文摘要 | P6 结果 |
|---|---|---|
| BDD-1 | 未知阶段名 fail-closed | PASS（手工 CLI + 单测双证据） |
| BDD-2 | 新增 regression 测试锁定未知阶段行为 | PASS |
| BDD-3 | 已知阶段行为不回归 | PASS（三分片全量 1634 passed） |
| BDD-4 | check-gate.py 回退检测非数字阶段名 fail-closed | PASS（2 参数化子场景） |
| BDD-5 | check-state-transition.py phase_num() 非数字阶段名 fail-closed | PASS（2 参数化子场景） |
| BDD-6 | pre-commit-gate.py 非常规阶段名产出文件 WARNING 不再无痕跳过 | PASS |
| BDD-7 | 三处判据修复对标准数字阶段名不回归 | PASS（三分片全量，含三个子测试） |
| BDD-8 | P4 跨多 commit 交付不误判 | PASS |
| BDD-9 | P5→P4 回退后修复 commit 不误判 | PASS |
| BDD-10 | 判据放宽红灯边界（纯文档/无历史/非回退仍拦截） | PASS |
| BDD-11 | 黑名单豁免协议阶段卡片路径（2 同构文件名） | PASS（2 参数化实例） |
| BDD-12 | 白名单补齐角色定义文件路径 | PASS（2 参数化实例） |
| BDD-13 | P6-evidence/ 裸文件名识别 | PASS |
| BDD-14 | 黑白名单加固后仍拦截真实自述（红灯边界） | PASS |

数量：P1 = 14 条，P6 = 14 条 PASS，0 FAIL（P6-acceptance.md「汇总」节 `Summary: 14/14 PASS, 0 FAIL`）；
P6.5-judge-verdict.md（`criteria_total: 14, criteria_passed: 14, status: passed`）对 14 条逐条独立复核
结论与 P6 完全一致（第 2 轮复核对 BDD-3/BDD-7 补证后改判 PASS，其余 12 条沿用第 1 轮结论）。
**结论：数量匹配（14=14），编号一一对应，内容映射正确（非"貌合神离"）。**

### 3.2 P2 声明的 packages 与 P4 实际改动文件是否落在声明范围内

P2-design.md frontmatter：`packages: [agate-scripts, agate-tests, agate-docs]`。

实测 `git diff --stat 33eaece~1 504f6b8 -- agate/scripts agate/tests agate/dispatch-protocol.md agate/phase-cards`
（P1 需求 commit 之前 vs P6.5 judge verdict commit，覆盖 P1-P6.5 全部改动，非仅 dispatch-context
摘要）：

```
agate/dispatch-protocol.md                          |  2 +-
agate/phase-cards/P6-acceptance.md                  |  2 +-
agate/scripts/check-gate.py                         | 34 +++-
agate/scripts/check-judge-verdict.py                | 49 ++++-
agate/scripts/check-state-transition.py             | 19 +-
agate/scripts/pre-commit-gate.py                    | 29 +++
agate/tests/fixtures/tag0034_regression_baseline.json | 10 +-
agate/tests/integration/test_pre_commit_hook.py     | 91 +++++++++
agate/tests/unit/test_check_gate.py                 | 225 ++++++++++++++++++++-
agate/tests/unit/test_check_judge_verdict.py        | 124 ++++++++++++
agate/tests/unit/test_check_state_transition.py     | 65 ++++++
```

核实：4 个脚本文件（`check-gate.py`/`check-judge-verdict.py`/`check-state-transition.py`/
`pre-commit-gate.py`）落在 `agate-scripts`；5 个测试/fixture 文件（`test_check_gate.py`/
`test_check_judge_verdict.py`/`test_check_state_transition.py`/`test_pre_commit_hook.py`/
`tag0034_regression_baseline.json`）落在 `agate-tests`（比 dispatch-context 摘要列出的
"`test_check_gate.py` 1 个"更多——已实测核实，实际新增/改动测试文件覆盖子批 B/D 各自的单测
文件与 integration 用例，属正常的"新增 regression 测试"范围，dispatch-context 摘要为简化
描述非字面穷举，不构成偏差）；2 个文档文件（`dispatch-protocol.md`/`P6-acceptance.md`）落在
`agate-docs`。**全部 11 个改动文件无一落在 `packages` 声明的 3 个 package 之外，无越界。**

### 3.3 P2§3.1-3.4 技术方案 vs P4-implementation*.md 实际实现路径是否吻合

已核实 P4-review.md§约束1「逐子批核对实现 vs 设计」的独立评审结论（非仅 implementer 自证）：

- 子批A：`check-gate.py:1517-1519` `sys.exit(2)`→`sys.exit(1)`，与 `P2§3.1` 逐字一致
- 子批B：`check-gate.py:1490-1496` 回退检测判空分支、`check-state-transition.py:212-216`
  `phase_num()` 返回 `Optional[int]`、`pre-commit-gate.py:87` 新增 `_P_OUTPUT_ANY_RE` +
  两处差集扫描（L307-316、L606-614），三处均与 `P2§3.2` 一致，三处消费语义各自独立未复用
  同一 patch
- 子批C：`_gate_p4_has_prior_code_commit`（`check-gate.py:214-235`）与 `P2§3.3` 完全一致，
  并已按 `P2-review.md` 约束3 建议加了收尾右括号定界
- 子批D：`check-judge-verdict.py` 六处改动与 `P2§3.4` 逐字一致，`dispatch-protocol.md`/
  `P6-acceptance.md` 文档同步已核实落地

结合本 P7 自己交叉核对 `P4-implementation.md`/`P4-implementation-B.md`/`P4-implementation-C.md`/
`P4-implementation-D.md`「改动清单」节的文字描述（见上文各节转抄），与 `P2-design.md§3.1-3.4`
逐子批技术方案（修复点/函数签名/返回值语义变化）描述**完全对应，无实现绕过设计自行发挥的情况**。
**结论：吻合。**

### 3.4 P1 risk_level: medium + phases: [P1..P8] 与实际执行阶段序列是否一致

P1-requirements.md frontmatter：`risk_level: medium`，`phases: [P1,P2,P3,P4,P5,P6,P7,P8]`
（不裁剪任何阶段，P1§6「裁剪说明」逐条列出 P2/P3/P4/P5/P6/P7/P8 均不可裁的理由）。

实测 `git log --oneline --grep="TAG0035"`（本 worktree 分支 `feat/TAG0035-gate-robustness`）：

```
504f6b8 wf(TAG0035-P6): P6.5 judge 复核通过（14/14），补齐 BDD-3/7 全量证据
b191307 wf(TAG0035-P6): 验收——14/14 BDD 通过
ffa0341 wf(TAG0035-P5): 技术验证——6/6 gate_commands 独立通过，0 failed
a87603c wf(TAG0035-P4): 任务看板同步——phase=P4
df55b9b wf(TAG0035-P4): 子批D
6d765a1 wf(TAG0035-P4): 子批C
50e5e46 wf(TAG0035-P4): 子批B
c9c6f5c wf(TAG0035-P4): 子批A
0c0d718 wf(TAG0035-P3): TDD 测试设计
cec88a7 wf(TAG0035-P2): 方案设计
33eaece wf(TAG0035-P1): 需求基线
```

实际执行阶段序列：P1→P2→P3→P4（4 个子批 commit + 1 个看板同步 commit，均标 phase=P4）→
P5→P6（含 P6.5 judge 复核，commit message 前缀仍为 `wf(TAG0035-P6)`，符合"P6.5 不单独
开新 phase commit 前缀"惯例）→当前 P7（本产出）。序列与 P1 声明的 `[P1..P8]` 前 7 段完全
一致（P8 尚未开始，属正常推进中状态，非跳阶）。`.state.yaml` 当前 `phase: P6`，`status: active`，
与 commit 历史一致（P7 完成后将推进为 P7/P8）。**结论：无阶段被跳过，序列一致。**

## 4. 未决项清零核对

已用 `grep -n "SCOPE+\|SCOPE_RESOLVED\|NEED_CONFIRM\|\[BLOCKER\]\|DEVIATION-CRITICAL" P1-requirements.md`
核对全文，唯一命中：第 156 行 `[NO_NEED_CONFIRM]`（P1 原文既有标记，非变化项）。**未发现残留
行首 `[NEED_CONFIRM]`、`[BLOCKER]`、`[DEVIATION-CRITICAL]`。本 P7 自身产出与 P4-review.md/
P6-acceptance.md/P6.5-judge-verdict.md 通读全文亦均无 `[BLOCKER]`/`[DEVIATION-CRITICAL]`
标记。结论：未决项已清零。**

## 5. CODE-MAP 核对（零新增文件）

本任务全部改动落在既有文件：`agate/scripts/check-gate.py`、`agate/scripts/check-state-transition.py`、
`agate/scripts/pre-commit-gate.py`、`agate/scripts/check-judge-verdict.py`（均为既有脚本文件，
本批只新增函数/分支，未新增文件）、`agate/tests/unit/test_check_gate.py` 等既有测试文件（同上，
只新增用例）、`agate/dispatch-protocol.md`/`agate/phase-cards/P6-acceptance.md`（既有协议文档，
只追加说明段落）。已用 §3.2 的 `git diff --stat` 结果核实：全部 11 个改动文件均为既有路径下的
修改（`git diff --stat` 无 `create mode`/新增文件标记）。`code_map_new_files_count: 0`，
`code_map_reviewed_count: 0`——两者对称为 0，P4 的"新增文件核对表"WARNING 因零新增文件本就
不适用，非缺陷，无需核对表。

## 6. 结论

- BLOCKER = 0，DEVIATION-CRITICAL = 0
- DESIGN_GAP = 2，均已 REVIEWED（见第 1 节，均引用 P4-review.md§约束2 的独立验证结论）
- SCOPE+ 闭环：无 SCOPE+ 声明，无需闭环
- 跨文件一致性 4 项均给出具体锚点（BDD 编号对应表 / `git diff --stat` 实测 / P4-review.md§约束1
  引用 / `git log` 实测），无裸"一致"表述
- 未决项清零：确认无残留 `[NEED_CONFIRM]`/`[BLOCKER]`/`[DEVIATION-CRITICAL]`
- CODE-MAP：零新增文件，核对通过

**本 P7 判定：通过（无 BLOCKER，可推进 P8）。**
