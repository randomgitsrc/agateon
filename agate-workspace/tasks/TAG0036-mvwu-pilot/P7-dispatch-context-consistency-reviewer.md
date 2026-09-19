---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P7 首次派发（非重试）。

### 目标

对照 P0-P6（含 P6.5）全部产出做**跨文件一致性审查**，产出 `P7-consistency.md`：逐条检查结果 + 实质锚点（源文件节名），无 `[BLOCKER]` / `[DEVIATION-CRITICAL]`（若真有则如实标注，不要压低）。

### 约束

1. **逐项检查（每项给结论 + 引用具体文件与节名，如 `P2§packages`、`P1 BDD-NN`、`P4§impl-path`；不接受裸"一致"）**：
   - **DESIGN_GAP 配对**：搜索 `P4-implementation*.md` 全部文件与 `P4-progress.md` 中的 `[DESIGN_GAP` 声明；每条须在 P7 产出中转抄并配 `[DESIGN_GAP_REVIEWED]`；若确无声明，写明"P4 无 DESIGN_GAP"及你的搜索命令与命中数（含 `design_gap_count: 0` / `design_gap_reviewed_count: 0`）。
   - **SCOPE+ 闭环**：`P1-requirements.md` 是否有行首 `[SCOPE+` 增补声明？若无，写明"无 SCOPE+"；同时核对 P1 内的 `[BASELINE_CHANGE]`（BDD-70 下方，主 Agent 批准的一处基线纠正）已在正文留痕、且 P2 §0.1 M18 与之一致，并说明它为何不属 SCOPE+（属 P2 评审发现的既有测试约束，非新需求）。
   - **数量对齐**：P1 `#### BDD-NN:` 标题数（71）= P6 验收的 71 条对照 = P6.5 judge 的 `criteria_total`；`P3-test-cases.md` / `P3-test-cases-docs.md` 映射覆盖 1..71 无遗漏（BDD-56 属 P6 证据）。
   - **P2 ↔ P4 ↔ 实际改动**：`P2-design.md` §0.1 的 M1-M18 与 `P4-implementation*.md`（主文件 + 5 个批文件）及 `git show --stat 4ee499f` 的实际改动文件**逐项对得上**；`P2§dispatch_plan` 的 6 个批 id（含改名后的 `architect-batch-guidance`）与 P4 批文件名、批索引一致；`P2§packages`（agate-scripts / agate-docs / agate-tests）与实际改动面一致；`git diff efb113b --stat` 无 P2 未声明的文件。
   - **P0 判据 ↔ 交付物**：`P0-brief.md` 的 11 条「完成判据」（1、2、3、3b、3c、4、5、6、7-11）逐条对照 P4/P6 的实际交付：判据 1-3c（tests_filter 键 / P4-evidence 落点 / check-mvwu.py / --observe / 字段落地路径）、4（Q2 结论在案：CONTEXT/文档中如何引用 13%）、5-6（采集能力就绪 / --observe 真实任务跑通，见 P6-evidence 对应证据）、7-11（⑤-a 至 ⑤-e）——每条指出交付文件与位置；未被交付的须标注（是否 BLOCKER 由你判断并说明）。
   - **P0 范围/out-of-scope 遵守**：不改协议内核（`git diff efb113b` 对 check-gate.py/phases.yaml/rules/schema/hook 三件套/agate_common.py 等空 diff）、不挂 gate、不替用户裁决提交粒度、不造样本；⑤-b/⑤-d 只成文不宣称生效——抽查 P4 新增文档措辞。
   - **既有一致性面**：`agate/scripts/README.md`、`agate/tests/README.md` 的 `check-mvwu.py` 行与脚本实际 `--help`、用例数（`pytest --collect-only` 实测）一致；`CHANGELOG.md [Unreleased]` 与实际交付一致；`CONTEXT.md` 5 条新术语与 `agate/` 内实际用法一致（含 `boundary(I1)` 取值口径 exact/mismatch/UNKNOWN）；`decisions/` 落点在 P2 卡、P7 卡、adr.md 三处表述互相一致（本卡 P7 卡新增第 6 项核对本身也应被你实际执行一次：`{AGATE_WORKSPACE}/decisions/` 目前是否有应落的跨任务决策——本任务无跨任务架构决策；如认为有，标注建议）。
   - **未决项清零**：`P1-requirements.md` 无残留行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]`；`P2-design.md` 无残留未决 `[SUGGEST` / `[NEED_CONFIRM]`；`P4-review.md` / `P4-protocol-alignment-review.md` 中的 NEEDS_HUMAN_REVIEW（A2 术语措辞）与 MAJOR（耗时吞行）**已处置**——用 P4 实现记录末节「评审后修复」与 `check-mvwu.py`/`CONTEXT.md` 实际内容核实。
   - **CODE-MAP / 骨架**：项目未采用 `P2-skeleton.md` 与 `{AGATE_WORKSPACE}/agents/CODE-MAP.md`（如有请核对，无则写明"机制未采用，跳过"）；`code_map_*` 计数字段不填。
2. **只审不改**：不修改任何代码/文档；不 git add/commit；发现问题写入 P7 产出并标 `[BLOCKER]`（阻断）或 `[DEVIATION]`（非阻断偏差，须给出处置建议），由主 Agent 决定回派。
3. **frontmatter**（用 `agate-md-field-set.py`；`agent` 键 set 不接受则 Edit 单行）：phase=P7 / task_id=TAG0036 / type=consistency / parent=P2-design.md / trace_id=TAG0036-P7-20260919 / status=draft / created=2026-09-19 / `agent: consistency-reviewer` / `blocker_count` / `deviation_count` / `deviation_critical_count` / `design_gap_count` / `design_gap_reviewed_count`（均为 int ≥0，须与正文标记一致）。正文中的行首标记保留为人类痕迹。
4. 产出含 `DESIGN_GAP_REVIEWED` 时须同时含跨文件引用关键词（`P1.*BDD` / `P2.*packages` / `P4.*implementation`）；若无 DESIGN_GAP，只需在正文明确写出搜索命令与"0 命中"。
5. 每读完一个文件往 `P7-progress.md` 用 `>>` 追加一行；所有 bash 加 `timeout`；尽早分阶段落盘。

### 上游关联

- 全部上游产出：`P0-brief.md` / `P1-requirements.md`（+`P1-review.md`）/ `P2-design.md`（+`P2-review.md`）/ `P3-test-cases.md`、`P3-test-cases-docs.md` / `P4-implementation.md` 及 `P4-implementation-*.md`、`P4-review.md`、`P4-protocol-alignment-review.md` / `P5-test-results/` / `P6-acceptance.md` + `P6-evidence/` / `P6.5-judge-verdict.md`

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/ 下 P0-P6.5 全部产出（见上）
- `git log --oneline`、`git show --stat 4ee499f`、`git diff efb113b --stat`
- agate/scripts/check-mvwu.py（仅 `--help` 与文件头）、agate/scripts/README.md、agate/tests/README.md、CHANGELOG.md、agate/CONTEXT.md（相关行）
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
- 提交序列：P0（`d46adbc`）/ P1（`84d90f7`）/ P2（`f8e0b13`）/ P3（`e0513d0`）/ P4（`4ee499f`）/ P5（`e1ac29e`）/ P6（`9279853`）/ P6.5 judge（`628db72`）；基线 `main` = `efb113b`。
- P5：10/10 命令 exit 0，1842 passed / 2 skipped；P6：71 条 BDD 71 通过 / 0 失败；P6.5 judge：status passed，criteria 71/71。
- 本任务 `.state.yaml` retries：P1 一次、P2 两次；`judge.judge_token_budget` 已覆盖为 400000（71 条 BDD）。
- P6.5 阶段曾因 judge dispatch-context 措辞被白名单正则误报，已改写并留 `P6-gate-diagnosis.md`。
</objective_info>
