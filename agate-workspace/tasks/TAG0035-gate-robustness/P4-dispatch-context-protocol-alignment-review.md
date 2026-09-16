---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0035
role: protocol-alignment-review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 SELF-GATE 触发的协议-脚本对齐审查（变更触发模式，见 SELF-GATE.md）。本任务改动了 `agate/scripts/*.py`（4 个脚本）+ `agate/dispatch-protocol.md` + `agate/phase-cards/P6-acceptance.md`，命中 SELF-GATE 触发面，必须走本流程。

## 你的角色定义
读取并遵循：agate/assets/review-roles/protocol-alignment-review.md

## 第一步：意图分析
本次变更的意图：把 agate 协议层 gate/check-script 中会静默通过（未知/异常输入被判定为与"正常通过"相同的退出码）或静默失效（判据前提不成立时无声跳过）的判据改为响应式失败（fail-closed），并补齐多提交/回退场景下过窄的判据假设。四个独立子批：① `check-gate.py` 未知阶段 exit 2→1 ② 三处"阶段名含数字"假设的非数字阶段名 fail-closed（`check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`）③ `check-gate.py` 的 `gate_p4` 完整度判据放宽（识别跨commit/回退场景）④ `check-judge-verdict.py` 黑白名单假阳性修复 + 2 处文档同步。

## 第二步：反向传播——列出应被影响的文件
基于意图，主动推断这次改动应该传播到哪些文件。已知的 diff 范围（工作树未 commit）：
`agate/scripts/check-gate.py` / `check-state-transition.py` / `pre-commit-gate.py` / `check-judge-verdict.py` + `agate/dispatch-protocol.md` + `agate/phase-cards/P6-acceptance.md` + `agate/tests/unit/test_check_gate.py`（1条既有测试断言修正）。

请你独立判断是否还有遗漏的传播目标，重点核查：
- `agate/state-machine.md`（转移规则表）是否描述了 `check-state-transition.py` 的 `phase_num` 语义（0 vs None）？若有描述且未同步会造成文档-脚本不一致。
- `agate/WORKFLOW.md`（阶段总览）是否有提及 gate 退出码语义（如"未知阶段 exit 2"）需要同步成 exit 1？
- `agate/rules/dispatch.yaml`/`agate/rules/phases.yaml` 是否有依赖 `check-gate.py` 具体退出码数值的声明？
- P0-brief.md 提到的 out-of-scope（不做 phases.yaml 语义重构、不做 handlers 声明式化）是否被本次实现意外触碰？

## 第三步：实际审查范围
读以下文件全文：
- git diff 涉及的变更文件（`git diff` 命令自行获取，工作树未 commit）
- 第二步列出的应被影响文件
- 权威规则源：
  - agate/state-machine.md（裁剪表、重试表、转移规则）
  - agate/dispatch-protocol.md（gate 表、门槛表、「Judge 信息隔离」节——本次子批D改动处）
  - agate/WORKFLOW.md（风险矩阵、阶段总览）

## 配套文件提示
- 涉及 gate 检查逻辑（check-gate.py）：同时读 implementer.md / architect.md / verifier.md 是否有依赖具体退出码语义的描述
- 涉及 check-judge-verdict.py 的信息隔离逻辑：已读 dispatch-protocol.md「Judge 信息隔离」节（本次改动处，须确认新增说明与代码实现严格一致）

## 审查清单
逐项检查 A1-A7（见角色文件），A3 和 A5 必须包含反向传播的检查：
- A1 文档→脚本对齐（尤其：dispatch-protocol.md 新增的"角色定义文件路径不受白名单限制"表述，与 `check-judge-verdict.py` 的 `_ROLE_DIR_RE` 实现是否严格一致——正则匹配 `execution-roles/`/`review-roles/` 路径段，文档措辞是否准确对应）
- A2 脚本→文档对齐
- A3 一致性连锁 + 反向传播：列出应被影响但 diff 未列出的文件，逐一验证
- A4 测试覆盖（14 条 BDD 是否都有对应测试，测试文件是否与本次改动的函数对应）
- A5 下游影响 + 文档传播：CHANGELOG 是否需要标注（P8 阶段处理，本次不要求现在就改，但请指出）？
- A6 锚点表覆盖（若 dispatch-protocol.md 有 gate 表/门槛表列出各阶段 exit code 语义，是否需要同步子批A的 exit 2→1 变化）
- A7 设计原则一致性：变更是否符合已记录的 ADR（agate/adr.md）？逐条检查相关 ADR。本次"fail-closed 优先"的取向是否已有 ADR 记录，若无是否需要建议补充

若发现 A1/A2/A3 疑似不一致，先按角色文件"DESIGN_GAP 优先核查"原则查
`{AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation.md`/`P4-implementation-{B,C,D}.md` 是否已有相关说明，避免把已知偏离误判为新 MISALIGNED。

每项输出：
- 审查项编号
- 文档说了什么（引用原文 + 行号）
- 脚本/其他文件实现了什么（引用代码 + 行号）
- 结论：ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW
- 若 MISALIGNED：具体差异描述 + 建议修复方向

## 分阶段落盘（留痕文件，防空返回）
留痕文件：{AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/docs-reviews-agate-alignment-2026-09-16-TAG0035-01.progress.md
开始前先删除留痕文件（如已存在）：`rm -f` 该路径
每读完一个文件，立即用 bash 追加一行（不要整理、不格式化）：
  `echo "- [文件名] 关键逻辑摘要" >> {留痕文件路径}`
每完成一个对比判断或反向传播检查项，立即追加（原始记录，不整理）：
  `echo "- A{n}/{反向传播}: 文档说X / 实际是Y / 结论" >> {留痕文件路径}`
不要在留痕文件里做内容整理——那是成果文件的事。读一个写一个，判断一条写一条。

## 产出（成果文件，最终交付物）
{AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-protocol-alignment-review.md
审查完所有文件后，把结构化报告写入成果文件（覆盖写，不是追加）。
成果文件含 frontmatter（`agate-md-field-set` 填写：phase: P4, task_id: TAG0035, parent: P4-implementation.md, trace_id: TAG0035-P4-align-20260916, agent: protocol-alignment-review, type: review, created: 2026-09-16, status: draft→审查完改为 approved/rejected 等价值——本报告用 ALIGNED 汇总表的形式，Header status 字段：全 ALIGNED/NEEDS_HUMAN_REVIEW(已标注[HUMAN_CONFIRMED]) → approved；含未处理 MISALIGNED → rejected）+ A1-A7 结论汇总表（含反向传播检查）+ 逐项审查详情。
⚠️ 路径是硬约束：必须用 Write 工具写入此路径，不得将产出文件写入 /tmp、工作区根目录或其他路径。

## 命令超时兜底
执行任意 bash 命令前设 `timeout 60s <命令>`。

## 环境隔离
本任务纯本地验证：`[PROD_NOT_TOUCHED]`。

## 返回给我
只返回两行：
  1. 产出文件路径（P4-protocol-alignment-review.md）
  2. 一句话摘要（含最终 status 判定，不超过 40 字）
绝对不要返回文件全文。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P4

路径：phase-cards/P4-implementation.md
---
# P4 — 代码实现

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P4 且有合规理由（check-pruning.py 已检查）→ 跳过，读 P5 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。
   该步骤不会阻塞流程——任何 stderr 输出（含 WARNING）均可忽略，直接继续步骤 1，
   无需查看结果、无需判断、无需因为看到 WARNING 而停下来处理。

**创建型测试清理钩子（强制要求，与 P3 卡同源）**：实现含创建资源用例时，须落地清理钩子——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；只修 P3 卡不修本卡即复发，两处须同步。

1. 派发 implementer subagent → 产出代码文件
   1.1 写 P4-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 P2 的 gate_commands 跑单元测试（非 gate，只是自查）
3. 按 C8 映射表派发评审（见下方）
4. 预跑 check-gate.py P4（确认暂存区有代码文件）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/ + 代码文件（含 .state.yaml，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P4，不要提前写 P5——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P4): {摘要}"（phase=P4，P4 产出含 P4-implementation.md + 代码文件）
7. P4 commit 完成后进入 P5：**phase 推进 P5 随 P5 产出 commit 一起**（P5-test-results/ 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（来自 gate 输出 / review rejected 理由）
→ 只修复失败项，不重做已通过的部分
→ 修复后重跑全量测试（T027 教训：修复可能引入回归）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P4 MAX=3）

**若这次是从 P6（或其他更后的阶段）退回来的**：`{AGATE_WORKSPACE}/tasks/{Txxx}/` 下不会再有旧的 P6-acceptance.md（已被归档），但当初具体是哪条 BDD 失败、失败原因是什么，会摘要在 `{AGATE_WORKSPACE}/tasks/{Txxx}/.retreat-history.md` 里——**重新派发 implementer 时，dispatch-context 必须引用这份摘要**，不能让 implementer 只看到"现有代码"却不知道具体要修哪里。已有代码不会被撤销、也不需要重新实现，是在已有实现基础上定向修复。**回退落地后必须建 DEBT 条目**（`source: retreat`，`evidence` 引用 retreat 提交哈希，模板 `assets/templates/tech-debt-template.md`——TAG0001 强制，见 `agate/rules/state-transitions.md` 回退规则节）。

## 前置条件

- [ ] P2-design.md 存在且 files_to_read 字段完整（导航清单）
- [ ] P2-review.md status: approved（P2 不可裁剪）
- [ ] P3-test-cases.md 存在（测试已设计）
- [ ] check-tdd-red.py 确认红灯（测试先于实现）
- [ ] 未跳过 P4（如有裁剪理由，见上方裁剪跳阶）

## 派发

- **角色**：implementer（`{agate_root}/assets/execution-roles/implementer.md`）
- **输入**：P2-design.md（files_to_read 导航 + gate_commands）+ P3-test-cases.md + P0-brief.md（env_constraints）
- **输出**：代码文件（在 P4-implementation.md 声明的 implementation_dir 下）
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md` + 以下阶段特定追加：

```
## 上下文控制
读取代码文件以 P2-design.md 的 files_to_read 清单为准，按需读取（标了行号范围的只读片段）。
不要在项目里盲目搜索或整目录全读。

## 自查≠gate
写完代码后应自跑测试确认基本功能（自查），但自查通过 ≠ P5 gate 通过。
P5 由主 Agent 派发 verifier subagent 执行 gate_commands.P5，主 Agent 验 gate（检查产出 + failed 计数 + N5 最小校验）。
不要在返回中声称"P5 已过"或"全部测试通过"——只返回路径 + 摘要。
UI/前端等需构建任务：单元测试全绿不代表可用，implementer 在 P4 完成后应构建并确认 dist 等构建产物存在，不能只跑单元测试就认为完成。

## 生产环境隔离
任何写入生产环境/生产数据库/生产 API 的操作都必须先 PAUSED 报告人工。
```

## 产出规格

- P4-implementation.md 必须声明 `implementation_dir: {实际路径}`
- 代码文件在声明的目录下
- 遵守 P2-design.md 的方案设计 + 现有项目代码规范

## 新增文件核对表

> 仅当项目已采用骨架（`P2-skeleton.md` 存在）或 CODE-MAP（`{AGATE_WORKSPACE}/agents/CODE-MAP.md`
> 存在）机制时填写；未采用则本节可省略。

implementer 为本阶段**每个新增文件**填一行：

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| {path} | `within <dir>` / `[SKELETON_DEVIATION: 理由]` | `[CODE_MAP_UPDATED]` / `[CODE_MAP_EXEMPT: 理由]` |

- **骨架归属列**：新增文件落在骨架声明的目录内 → `within <dir>`；落在骨架外 → 标
  `[SKELETON_DEVIATION: 理由]`（不阻断，供 P7 核对）
- **CODE-MAP 处理列**：新增文件已同步更新 `agents/CODE-MAP.md` → `[CODE_MAP_UPDATED]`；判断
  该文件不需要更新 CODE-MAP（如临时/测试脚手架）→ `[CODE_MAP_EXEMPT: 理由]`

`change_type: refactor` 同样适用本表（不因换用回归口径而豁免）。

## 评审派发（C8 机械映射）

**在 P4 实现完成后、gate 前**，按 P1 声明的 domains 和 risk_level 派评审。C8 映射表是机械规则，不靠判断"需不需要"：

| domain | 派哪些评审 | 产出 |
|--------|----------|------|
| backend | review | P4-review.md |
| frontend | design-review | P4-review.md |
| mcp | review（关注 MCP 接口契约）| P4-review.md |
| security | cso | P4-review.md |
| risk=high | P4 实现评审（按 domains 派 review/design-review/cso；P2 plan-eng-review 已审方案，P4 实现评审不可省）| P4-review.md |
| full（tier=full 或声明 ceremony: full）| P4 实现评审（按 domains 派 review/design-review/cso，同 risk=high 不可省；P2 plan-eng-review 已审方案）+ cso（security 域）+ P7 不可裁（full 档任务 P7 为强制阶段）| P4-review.md |

多个评审角色 `专家组并行` → 所有返回后派组长汇总 → 统一 P4-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长产出：P4-review.md。**agent 字段必须非 main**（与 P2 评审同规则，check-gate.py 在 P2 分支硬拦截 agent=main 的 approved）
5. 组长规则：不发表新意见，只汇总；任何 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P4-review.md。

**评审 checklist（RM-AG0046）**：`agate/scripts/check-maintainability.py` 检出 violations 非空时，评审角色 approve 前必须读过任务目录 `known-violations.md` 的登记理由——"是否接受该反模式"的判断权在评审角色，登记与数量对齐不单独构成放行依据。

review 不通过 → implementer 修改代码 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 按包拆分并行（条件触发，需额外约束）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P4 可拆分并行，但**有额外约束**：

1. 每个 package 派一个 implementer subagent
2. **各 implementer 只改自己 package 目录下的文件**——跨包的共享文件（类型定义、接口、配置）由主 Agent 在所有并行 implementer 返回后统一处理
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit
5. 主 Agent 在所有 implementer 返回后，统一处理共享文件改动（如果有）

**冲突预防**：
- dispatch-context 约束节必须写明：`只改动 {pkg}/ 目录下的文件。共享文件（{列出}）不在本次改动范围内`
- 如果某个 implementer 必须改共享文件 → 该包不能并行，改为串行（主 Agent 先派其他包并行，再串行处理含共享改动的包）
- 无法确定是否有共享改动 → 串行（安全默认值）

**基础设施隔离（并行时强制）**：
- debug server 端口：每个 implementer 的 dispatch-context 约束节分配不同端口（如 pkg-a: 3001, pkg-b: 3002）
- 测试数据库：每个 implementer 用独立数据库路径（如 `test-{pkg}.db`），不共享同一 test.db
- 环境变量：dispatch-context 写明各 subagent 独立的环境变量值（如 `PORT=3001` vs `PORT=3002`）
- 临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录

主 Agent 在并行派发前**必须**为每个 subagent 的 dispatch-context 分配上述隔离参数。当前无 gate 脚本检查（已知缺口），但未分配导致运行时冲突（端口占用/数据库锁）时计为重试，不算环境问题。

## gate 规则（check-gate.py 会跑）

```bash
check-gate.py P4 $TASK_DIR
```

- **exit 0**：暂存区含非 md/yaml 代码文件（git diff --cached --name-only）
- **exit 1**：暂存区仅 .md/.yaml 文件（无实际代码变更）→ 不能推进
- **exit 1**（RM-AG0046 三重门槛）：检测 violations 非空时，`known-violations.md` 必须存在且登记条目数 ≥ violation 数（评审检查复用上方既有 exit 1 条件；violations 为空 / 检测未部署 / git 通道不可用时不阻断）
- WARNING（不改变 exit code）：骨架/CODE-MAP 机制已采用（P2-skeleton.md 或 agents/CODE-MAP.md 存在）但缺「新增文件核对表」标题

## 推进条件（全部满足才写 phase: P5）

- [ ] 暂存区含代码文件（非 .md/.yaml）
- [ ] 按 C8 映射表触发的评审全部完成：P4-review.md status: approved（所有任务都要求——risk=high 的 P2 plan-eng-review 审方案，P4 实现评审按 domains 另行派发，不可省）
- [ ] SCOPE+ 已处理（若本阶段产生）：P1-requirements.md 有 [SCOPE_RESOLVED]（行首声明格式）
- [ ] git commit 完成

## 常见错误

1. **不读 files_to_read，在项目里乱翻**：implementer 拿到 P2 的 files_to_read 清单后应按清单阅读，不要在项目里全文搜索或整目录全读——上下文会爆炸
2. **自行加范围外改动**：发现需要做但不在 P1 范围内的改动 → 标 [SCOPE+]（行首声明格式）而非直接做
3. **只跑单元测试不验证集成**：单元测试全绿 ≠ 功能可用。P5 会跑 gate_commands 做技术验证，但要确保实现时路径依赖的端点行为已验证
4. **先更新 .state.yaml 再 commit**：state 和产出在同一 commit 里——不要先 commit 产出再单独 commit state
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P5 验证依赖：P5 跑 gate_commands.P5 的命令（在 P2 声明），确保你的实现能通过
- P6 验收依赖：实现路径的端点行为必须可验证（确认 API 返回正确的 Content-Type、状态码等）
- 代码改动文件路径：P8 发布时确认版本文件变更需要知道你改动了哪些 package

> 完成 → 读 phase-cards/P5-verification.md

6. **修改 P1 文档**：P4 发现 BDD 矛盾时标 DESIGN_GAP，不直接改 P1-requirements.md。需变更 P1 时标 `[BASELINE_CHANGE: 理由]` 并经主 Agent 批准。
<!-- AGATE_CARD_END -->

<objective_info>
- 环境：worktree 分支 feat/TAG0035-gate-robustness；python3 3.12.3
- 已知的 2 处待处理事项（不在本次审查判定范围，属于机械后续步骤，评审员知悉即可）：① ruff PLW2901 已修复 ② TAG0034 的 `tag0034_regression_baseline.json` 零字节基线需要更新（`check-gate.py`/`check-state-transition.py` 哈希），将在本审查 ALIGNED 之后由主 Agent 处理——这属于"预期内的、有既定流程的基线更新"（该 JSON 文件本身的 `_note` 字段已写明"此后再次变化仍需经 SELF-GATE 审查"，本次审查通过即满足该前提条件），不是本次审查应判定的 MISALIGNED 项
</objective_info>
