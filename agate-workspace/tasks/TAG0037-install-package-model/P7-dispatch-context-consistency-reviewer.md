---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0037
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P7 一致性检查首次派发（ceremony: full，P7 不可裁）。

### 目标

对 P1–P6.5 全部产出与代码/文档实况做跨文件一致性审查，产出 `P7-consistency.md`（frontmatter 见 P7 卡片样例：`blocker_count`/`deviation_count`/`deviation_critical_count`/`design_gap_count`/`design_gap_reviewed_count`，及 `code_map_new_files_count`/`code_map_reviewed_count` 若适用；`agent: consistency-reviewer`——`agate-md-field-set` 拒写 `agent` 键时主 Agent 授权你手写该行）。只审不改，不改任何代码/测试/文档。

### 约束

1. **DESIGN_GAP 配对（gate 硬校验）**：把 `P4-implementation.md` 中每条 `[DESIGN_GAP: ...]` 逐条转抄到 P7-consistency.md，并各配一行含 `DESIGN_GAP_REVIEWED` 的核对结论（说明为何可接受/是否已被评审裁定：P4 评审 review + cso 均 approved 且已裁定）。另有 P3 阶段的 `[DESIGN_GAP: B1]`（对 P2 T-10 的合法例外：`test_bdd_2/3/6` 旧 worktree 形态断言改写；主 Agent 已采纳，见 `P3-test-cases.md` §8.2 (a)，其要求"P7 补 REVIEWED"）也须转抄并配 `DESIGN_GAP_REVIEWED`（计入 design_gap_count / design_gap_reviewed_count，两数相等）。
2. **跨文件一致性核对清单（每项写出源文件节名锚点，如 `P2§packages`、`P4§impl-path`，并给实测证据，禁裸"一致"）**：
   - P1 BDD 数 52 ↔ P6 验收数 52 ↔ P6.5 judge 52/52，且内容映射不错位（抽查 ≥8 条 BDD 的 P6 证据文件与该 BDD 的 Then 对应）。
   - P2 `packages`（agate-scripts、agate-docs、agate-tests、ci-workflows、install-sh）↔ P4 实际改动文件面（`git diff 75a8102..HEAD --stat` 归类）↔ P8 将 bump 的范围（发布物：README badge、CHANGELOG、UPGRADING v0.73.0）。
   - P2 §5 批次表（A/B1a/E/B1b/B2/C1/C2/F1a/F2）↔ P4 各批小节 ↔ 实际文件；P4 修复批 `t17-fixture-fix` 与 P2/P5 的关系（P5 重跑，p5_pass_commit 是否指向修复后提交）。
   - P1 各 `[BASELINE_CHANGE]` 注记（BDD-20 ④、BDD-43/45 的 G-1、BDD-50 P6 范围）↔ P6 验收对应条目 ↔ P3 §8.2 裁决记录，三处口径一致，无任一处与 BDD 正文相冲突。
   - P1 §7 SUGGEST 采纳（S-1…S-19）↔ P2 设计决策 ↔ 实际实现（抽查 S-1 tests 排除、S-3/S-4 顶层文件入包、S-13 旧 bundle 拒绝、S-15 exit 1、S-10 workflow 零第三方 action）。
   - P2 [SCOPE+]（升级自举缺口）主 Agent 已裁定"不做代码改动，仅文档化 + backlog"：核对 P2 §13/UPGRADING v0.73.0 节是否如实记载，未有残留半实现（`install.sh` 无 `git pull`）。P1 是否有需 `[SCOPE_RESOLVED]` 的 SCOPE+：无则明确写"P1 无 SCOPE+"。
   - 文档 ↔ 实现：`agate/UPGRADING.md` v0.73.0 节/迁移三步/退出码/环境变量废弃说明 ↔ 实际脚本行为；`CHANGELOG.md [Unreleased]` 条目 ↔ 实际改动；`agate/scripts/README.md` 登记 ↔ 新增脚本（`agate_package.py`、`agate-release.py`）；README/SETUP 的 `$AGATE_DIR` 口径 ↔ `agate_common`/`agate-resolve` 实际解析链（env → 项目声明 → current 三层）。
   - 兼容红线：`_protocol_root` 函数体零 diff；`resolve_hook_root` 兜底保留；BDD-46 out-of-scope 文件零 diff（以 `git diff 75a8102..HEAD -- <清单>` 实测）。
   - retries：`.state.yaml` 的 `retries.P1/P2` 记录与实际重试轮次一致；P3 收尾 / P4 修复批 / P5 重跑的历史在文档中有交代。
3. **未决项清零**：P1 无行首 `[NEED_CONFIRM]`/`[BLOCKER]`/`[DEVIATION-CRITICAL]`；P6 无遗留 FAIL；记录已知遗留（非 BLOCKER）：远端测试 tag `v0.73.0-tagtest.1` 及预发布 Release 待用户手动清理；BDD-50 ②–⑥、BDD-20 ④ 的 P8 复验项；t17 夹具修复在新版 git 上的真实确认待 PR CI。
4. **CODE-MAP 核对**：`{AGATE_WORKSPACE}/agents/CODE-MAP.md` 与 P4「新增文件核对表」逐条核对，新增文件（`agate_package.py`、`agate-release.py`、`release.yml`、`helpers_tag_repo.py` 等）是否需登记；发现偏离标 `[CODE_MAP_DRIFT: ...]`（WARNING，不阻断），如需在 P8 补登则在结论里列为待办。
5. **数据安全（用户强制）**：只读审查；除输出文件 `P7-consistency.md` 与 `P7-progress.md` 追加外不改仓库任何文件；禁止 `rm -rf`/删除文件；不 git add/commit/push/tag；不触碰真实 ~/.agate、开发 checkout、GitHub；实验用 scratchpad 新建带序号目录。
6. 产出不写行首 `- PASS`/`- FAIL`；发现分级 BLOCKER/DEVIATION/DEVIATION-CRITICAL；无则明确 `blocker_count: 0` 并给出实质锚点。返回：路径 + 一句话摘要（≤40 字，含 blocker 与 design_gap 计数）。

### 上游关联

P0-brief.md、P1-requirements.md、P2-design.md、P3-test-cases.md、P4-implementation.md、P5-test-results/、P6-acceptance.md、P6.5-judge-verdict.md

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/ 下的 P0-brief.md、P1-requirements.md、P2-design.md、P3-test-cases.md、P4-implementation.md、P5-test-results/、P6-acceptance.md、P6.5-judge-verdict.md、.state.yaml
- agate/UPGRADING.md、CHANGELOG.md、agate/scripts/README.md、agate/scripts/{agate_package,agate-release,agate_common,agate-resolve}.py、install.sh、.github/workflows/release.yml、{AGATE_WORKSPACE}/agents/CODE-MAP.md
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
