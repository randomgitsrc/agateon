---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0035
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P7 首次派发（非重试）。

### 目标

对 P1-P6 全部产出做跨文件一致性交叉检查，产出 P7-consistency.md。

### 约束

1. **DESIGN_GAP 配对（本任务有 2 条，均需转抄 + REVIEWED）**：
   - 子批 A（P4-implementation.md）：`test_other_unknown_phase_exit_2` 更名为 `test_other_unknown_phase_exit_1`，断言值 2→1——该存量用例编码的正是 BDD-1 要修复的旧行为本身，P4-review.md 已独立验证此判断合理（临时还原判据未变，逐一核对无遗留矛盾）。
   - 子批 B（P4-implementation-B.md）：`check-state-transition.py` main() 把 `old_phase in ("PAUSED","READY","DONE")` 与空字符串同等处理为合法 `old_num=0`——超出 dispatch-context 原始判空条件字面范围的必要扩展，P4-review.md 已独立红队验证（临时还原该扩展会致 `test_st_15`/`test_st_19` 两条既有回归用例失败，证明扩展确属必要）。
   两条 DESIGN_GAP 均须在 P7-consistency.md 中逐条转抄原文 + 标注 `[DESIGN_GAP_REVIEWED: 理由]`，并引用 P4-review.md 中对应的独立验证结论作为佐证（引用源文件节名，如 `P4-review.md§约束2`）。
2. **SCOPE+ 闭环**：核实 P1-requirements.md 是否有 SCOPE+ 声明——按你自己重新核对全文，本任务范围在 P0-brief/P1/P2 三阶段已多次收窄锁定（DEBT0040/0041 移出），未发现新增 SCOPE+ 增补；若确认无 SCOPE+，在 P7-consistency.md 写明"未发现 SCOPE+ 声明，无需闭环"。
3. **跨文件一致性核对（逐项给出具体锚点，不能只写"一致"）**：
   - P1 的 14 条 BDD 编号 vs P6 的 14 条 PASS/FAIL 结果——数量匹配 + 编号一一对应（不是只比数量）
   - P2 声明的 `packages: [agate-scripts, agate-tests, agate-docs]` vs P4 实际改动文件（`agate/scripts/*.py` 4 个 + `agate/tests/unit/test_check_gate.py` 1 个 + `agate/dispatch-protocol.md`/`agate/phase-cards/P6-acceptance.md` 2 个文档）是否落在声明的 3 个 package 范围内
   - P2 §3.1-3.4 的技术方案 vs P4-implementation*.md 的实际实现路径是否吻合（引用 `P2§3.2`/`P4-implementation-B.md§改动清单` 这类源文件节名锚点）
   - P1 `risk_level: medium` + `phases: [P1..P8]`（全阶段不裁剪）与实际执行的阶段序列（P1→P2→P3→P4→P5→P6→P6.5→P7）是否一致，无阶段被跳过
4. **未决项清零**：核对 P1-requirements.md 全文，确认无残留行首 `[NEED_CONFIRM]`（P1 原文是 `[NO_NEED_CONFIRM]`，应无变化）、`[BLOCKER]`、`[DEVIATION-CRITICAL]`。
5. **CODE-MAP 核对**：本任务全部改动落在既有文件（`check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`/`check-judge-verdict.py`/`test_check_gate.py`/`dispatch-protocol.md`/`P6-acceptance.md`），**零新增文件**——`code_map_new_files_count: 0`，`code_map_reviewed_count: 0`（对称，无需核对表，P4 的"新增文件核对表"WARNING 本就因零新增文件而不适用，非缺陷）。
6. **frontmatter 计数字段**：`blocker_count: 0`、`deviation_count: 0`、`deviation_critical_count: 0`、`design_gap_count: 2`、`design_gap_reviewed_count: 2`（两条均需 REVIEWED）、`code_map_new_files_count: 0`、`code_map_reviewed_count: 0`。

### 上游关联

- P1-requirements.md（BDD 基线 + frontmatter 声明）
- P2-design.md（技术方案 + packages 声明）
- P4-implementation.md / P4-implementation-{B,C,D}.md（含 2 条 DESIGN_GAP 声明原文）
- P4-review.md（对 2 条 DESIGN_GAP 的独立验证结论，供你转抄引用）
- P6-acceptance.md（14 条 PASS 结果）
- P6.5-judge-verdict.md（独立复核，status: passed，14/14）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P1-requirements.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P2-design.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-B.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-C.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-D.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-review.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P6-acceptance.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P6.5-judge-verdict.md
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P7

路径：phase-cards/P7-consistency.md
---
# P7 — 一致性检查

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P7 + 源文件数 ≤5 + 无 implicit_coupling + 有 coupling_checklist（须列出至少 2 个已检查的耦合点，空清单不合规）→ 跳过，读 P8 卡片
> ⑨ P7 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 consistency-reviewer subagent 执行交叉检查
   1.1 写 P7-dispatch-context-consistency-reviewer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 对照 P1-P6 产出做跨文件一致性审查
3. 产出 P7-consistency.md
4. 预跑 check-gate.py P7
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P7，不要提前写 P8——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P7): {摘要}"（phase=P7，P7 产出含 P7-consistency.md）
7. P7 commit 完成后进入 P8：**phase 推进 P8 随 P8 产出 commit 一起**（P8-release.md 就绪后），不是单独 phase commit

## 如果是重试

→ 读 agate/rules/state-transitions.md 确认 retry 上限（P7 MAX=2）

## 前置条件

- [ ] P1-P6 全部产出文件就绪

## 执行方式

consistency-reviewer subagent 执行。检查清单：

1. **DESIGN_GAP 配对**：P4-implementation.md 中的 DESIGN_GAP 声明 → 必须在 P7-consistency.md 中逐条转抄 + 配 REVIEWED 标记。未配对 → gate 不通过
2. **SCOPE+ 闭环**：P1-requirements.md 有 [SCOPE_RESOLVED] 标记，确认所有 SCOPE+ 增补已纳入基线
3. **跨文件一致性**：P2 声明的 packages 与 P8 release 的 bump 范围一致？P1 的 BDD 和 P6 的验收结果数量匹配？P4 的实现路径和 P2 的方案设计吻合？
4. **未决项清零**：P1-requirements.md 无残留行首 [NEED_CONFIRM]（P6 不再有 NEED_CONFIRM）、[BLOCKER]、[DEVIATION-CRITICAL]
5. **CODE-MAP 核对**：对照 `{AGATE_WORKSPACE}/agents/CODE-MAP.md` 与 P4「新增文件核对表」逐条核对，发现依赖方向偏离标 `[CODE_MAP_DRIFT:]`（WARNING 级，不阻断）；核对通过标 `[CODE_MAP_SYNC:]`

## 实质锚点要求（N3⑨）

| gate 断言 | 实质锚点（P7 产出须包含） |
|-----------|--------------------------|
| BLOCKER=0 | DESIGN_GAP 配对项 + REVIEWED 标记 |
| CRITICAL=0 | 跨文件检查项 + 源文件节名 |
| SCOPE+ 闭环 | 条目 + SCOPE_RESOLVED |

gate 脚本校验说明：
- DESIGN_GAP_REVIEWED：P4 声明的每条 DESIGN_GAP 在 P7 产出中须有对应行含 `DESIGN_GAP_REVIEWED`
- 跨文件引用关键词：P7 产出中须含源文件节名（如 `P2§packages`、`P4§impl-path`），否则 WARNING

## 产出规格

- P7-consistency.md：一致性审查结论
- 逐条检查结果，无 [BLOCKER] 标记

`blocker_count`/`deviation_count`/`deviation_critical_count`/`design_gap_count`/
`design_gap_reviewed_count`/`code_map_new_files_count`/`code_map_reviewed_count` 写在文件头
**frontmatter**（`---` 分隔块），不写正文；正文
`[BLOCKER]`/`[DEVIATION-CRITICAL]`/`[DESIGN_GAP]`/`[DESIGN_GAP_REVIEWED]` 散文标记保留为
人类痕迹（不迁移），gate 判定改读 frontmatter 结构化计数。**可直接复制的完整样例**：
```yaml
---
phase: P7
task_id: TAG0001           # 替换为实际任务编号
type: consistency
parent: P2-design.md
trace_id: T001-P7-20260101 # {task_id}-P7-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0                  # int ≥0
deviation_count: 0                # int ≥0
deviation_critical_count: 0       # int ≥0
design_gap_count: 0                # int ≥0
design_gap_reviewed_count: 0       # int ≥0
code_map_new_files_count: 0        # int ≥0（可选，仅骨架/CODE-MAP 机制已采用时填）
code_map_reviewed_count: 0         # int ≥0（可选，语义对应 design_gap_reviewed_count）
---
```

## gate 规则

```bash
check-gate.py P7 $TASK_DIR
```

- [BLOCKER] 存在 → exit 1
- [DEVIATION-CRITICAL] 存在 → exit 1
- DESIGN_GAP 未配对（P4 有但 P7 无 REVIEWED）→ exit 1
- CODE-MAP 未配对（code_map_reviewed_count < code_map_new_files_count，或 P4 实际标记数 > code_map_new_files_count）→ exit 1（两字段均缺失时机制未采用，跳过）
- 含 DESIGN_GAP_REVIEWED 但缺跨文件引用关键词 → WARNING（不改变 exit code）
- 全部通过 → exit 0

BLOCKER → consistency-reviewer 修改 → 再验 gate → … → 通过（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 推进条件（全部满足才写 phase: P8）

- [ ] P7-consistency.md 存在
- [ ] 无 [BLOCKER] / [DEVIATION-CRITICAL]
- [ ] DESIGN_GAP 全部 REVIEWED 配对
- [ ] SCOPE+ 闭环（P1 有 [SCOPE_RESOLVED]）

## P7 输入文件数量

P7 是输入文件数量限制的例外（模式 1 单发 + 输入数量豁免特例，见 dispatch-protocol「派发编排机制」全阶段适用表），不拆分。原因：
1. 跨文件一致性比较需要全部源文件同时可见
2. 角色文件（consistency-reviewer）已列出所需输入清单
3. dispatch-context 为 subagent 提供摘要，无需逐文件全文注入

## 常见错误

1. **漏转抄 P4 的 DESIGN_GAP**：P4 implementer 声明了实现偏差但 P7 没转抄 → gate 拦截
2. **一致性检查只看标题不对内容**：P1 BDD 数 = 15，P6 PASS 数 = 15 → 数量对，但 BDD-8 的内容在 P6 里被映射到错误的验收结果
3. **裸 'BLOCKER=0' 不引用锚点**：未做实质交叉检查，只写 '一致' → gate WARNING 提醒

gate 不过 ≠ 你失败了。红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P8 发布前最后一道质量门——P7 通过后进入机械发布步骤

> 完成 → 读 phase-cards/P8-release.md
<!-- AGATE_CARD_END -->

<objective_info>
- 环境：worktree 分支 feat/TAG0035-gate-robustness；python3 3.12.3
- 当前 git HEAD：504f6b8（P6.5 judge verdict commit），工作树干净
- 本任务全部 6 个 phase commit 已落地：wf(TAG0035-P1)...wf(TAG0035-P6)（含 P6.5），无跳阶、无回退
