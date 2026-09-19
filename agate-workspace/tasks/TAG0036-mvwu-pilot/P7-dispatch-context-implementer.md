---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P7 后的**文档收尾小修**（非批次）：处置 `P7-consistency.md` 的 3 条非阻断偏差（D1/D2/D4）。D3（`HANDOFF-TAG0036.md` 随分支合入）经主 Agent 核对 `HANDOFF-TAG0035.md` 已随其分支合入 main 的先例，裁定保持现状，**无需改动**。

### 目标

1. **D1**：`CHANGELOG.md` `[Unreleased]` 的 TAG0036 小节里写 `test_check_mvwu.py` **109** 用例，实测（`python3 -m pytest agate/tests/unit/test_check_mvwu.py --collect-only -q`）与 `agate/tests/README.md` 均为 **111**——把 CHANGELOG 中的 109 改为实测数（以命令输出为准），其余文字不动。同时核对同小节中 `test_mvwu_protocol_docs.py` 用例数（65）与实测一致。
2. **D2**：`agate-workspace/agents/CODE-MAP.md` 的「scripts」节（`agate/scripts/` 条目，已含 ceremony 路由族 / judge 机制族等按任务追加的族说明行）**追加一行**，格式与既有"新增 TAGxxxx"族说明行一致：`MVWU 观测族（新增 TAG0036）：check-mvwu.py（批级证据只读观测器——六项检查 + 四态 verdict + --observe 观察行；不挂 gate/hook/CI、不写任何文件；单向依赖 agate_common 的 run_git / split_frontmatter / resolve_workspace）。`同时在 `P4-implementation.md` 的「新增文件核对表」一带**追加一节备注**（只追加，不改既有文字）：更正"项目未采用 CODE-MAP"的说法——`agate-workspace/agents/CODE-MAP.md` 存在，`check-mvwu.py` 已于本次收尾在其 scripts 节登记（`[CODE_MAP_UPDATED]`）。
3. **D4**：在 `P4-implementation.md` 「评审后修复（TAG0036）」节之后**追加一小节**「测试注释小修（testfix，非批次）」：记录 P4 收口前发现 `test_mvwu_protocol_docs.py` 第 11 行注释含 `/tmp` 字面量致 `test_check_platform_assumptions.py::test_bdd_8_clean_tree_zero_detection` 转红，仅改注释措辞（无任何断言/逻辑改动），详见 `P4-progress.md` 的 `[testfix]` 行——补齐追溯（只追加，不改既有文字）。

### 约束

1. **只改**：`CHANGELOG.md`（仅 109→实测数）、`agate-workspace/agents/CODE-MAP.md`（仅追加一行）、`agate-workspace/tasks/TAG0036-mvwu-pilot/P4-implementation.md`（仅追加两处备注/小节）。不改其他任何文件；不 git add/commit；不改测试、脚本、协议文档。
2. 新增文字不得含 CHECK 14 裸词（task/goal/workflow/DSH/OpenCode/Claude Code/ralph；`CODE-MAP.md` 与 `CHANGELOG.md` 不在该叙述面但仍请避免）。
3. 自查：`timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` 0 ERROR；`python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0036-mvwu-pilot/P4-implementation.md` 通过；`git diff --stat` 仅上述 3 个文件；`timeout 200 python3 -m pytest agate/tests/unit/test_mvwu_protocol_docs.py -q -p no:cacheprovider` 全绿（含 BDD-69 CHANGELOG 用例）。不得声称"P5 已过"。
4. 在 `P7-progress.md` 用 `>>` 追加 `[fixes]` 前缀记录。

### 上游关联

- `P7-consistency.md`（D1-D4 原文与处置建议）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P7-consistency.md（§9 偏差清单）
- CHANGELOG.md（TAG0036 小节）、agate-workspace/agents/CODE-MAP.md（scripts 节）、{AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P4-implementation.md
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
- `P7-consistency.md`：blocker_count 0 / deviation_count 4 / deviation_critical_count 0；DESIGN_GAP 0。
- `pytest --collect-only` 用例数实测：`test_check_mvwu.py` 111；`test_mvwu_protocol_docs.py` 65；`count-tests.sh` 总计 1844。
</objective_info>
