---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P4 首次派发，**波 2 / 批 `batch-evidence-landing`**（波 2 三批并行，**并发上限 ≤3**；三批**文件面互不重叠**，只改本批文件）。

### 目标

实现批 `batch-evidence-landing`：让主 Agent 知道往哪写、写什么批级证据——在 P4 卡片新增 `P4-evidence/{batch}.log` 落点节（M6，BDD-10），并在任务文件模板登记（M7，BDD-11）。

### 约束

1. **测试是规格，P1 是权威**：`agate/tests/unit/test_mvwu_protocol_docs.py`（P3 已提交）是本批验收规格，**不得修改任何测试文件**；发现测试与 P1/P2 矛盾 → 不改测试，在 `P4-progress.md` 记 `DESIGN_GAP` 并报告。**字面标记逐字取自 `P1-requirements.md` 对应 BDD 的"字面：…"**，不得改写；文本须真实成文（不是把关键词塞进注释凑断言）。
2. **只改本批文件**：`agate/phase-cards/P4-implementation.md`（M6）、`agate/assets/templates/task-files.md`（M7）——2 文件。**不改**其他任何文件——尤其不改 `agate/scripts/*`（`check-mvwu.py` 已由波 1 落库）、`check-gate.py`/`phases.yaml`/`rules/`/hook/审计链/`dispatch-protocol.md`/`assets/execution-roles/` 中本批之外的任何角色文件；不新增 `.sh`；不 git add/commit；并行的另外两批文件面见 `P2-design.md` §6 批表，**不要碰**。
3. **改动落点**（P2 §0.1，**插入位置以标题定位**，行号仅供参考）：
   - **M6** `phase-cards/P4-implementation.md`：`## 产出规格` 之后、`## 新增文件核对表` 之前新增 `## 批级证据 P4-evidence（MVWU 阶段 1，不阻断，TAG0036）`。须含证据日志**最小内容**（逐行 `key: value`：`command` / `exit_code` / `git_head` / `timestamp` / `expected_red` / `duration_seconds`，以及 P1 已采纳的可选键 `failed_tests`，列表编码与元素相等口径按 P1 口径 C：单行 flow 序列 + 双引号 pytest node id）、文件名规则（`{batch}` = 批 `id`，filename-safe `[A-Za-z0-9._-]+`）、`check-mvwu.py` 的用法指针（`python3 agate/scripts/check-mvwu.py <task_dir>` / `--observe`，**观测不阻断、UNKNOWN 不等价于 PASS**）；字面标记逐字取 P1 BDD-10。**不得**把 P4-evidence 写成 gate/hook/CI 的一部分
   - **M7** `assets/templates/task-files.md`：① 阶段产出表 P4 行组（`{implementation_dir}/` 行之后）加 `P4-evidence/{batch}.log` 行；② P2 frontmatter 样例中 `# dispatch_plan:` 注释行之后加 `tests_filter`/`output` 可选键说明注释（BDD-11；注意样例是 YAML 注释，不得破坏 `check-protocol-consistency.py` 对该样例的既有 YAML 检查）
4. **本批 BDD**：BDD-10、11（并保持 BDD-12 负向：P4-evidence 不进 rules/dispatch-protocol/judge 白名单）——逐条读 P1 原文（含 Given/When/Then 与字面锚点），文档内容须满足其 Then；⑤ 组只要求「成文到位」，**不得写"机制已生效/已验证有效"** 之类断言（BDD-60/62）。
5. **CHECK 14 平台词（P2 R3，硬约束）**：`agate/*.md` 顶层叙述面（含 `role-system.md`、`adr.md`、`CONTEXT.md`）不得出现裸词 `task` / `goal` / `workflow` / `DSH` / `OpenCode` / `Claude Code` / `ralph`（大小写不敏感，详见 P2 R3 与 `check-protocol-consistency.py` CHECK 14）；用"任务/目标/流程"等中文或既有替代词；写完用 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` 自查 0 ERROR。任何文档中出现 `check-mvwu.py` 引用须可解析（脚本已存在）。
6. **技术栈中立 / 边界**：不规定架构适应度工具、不强制垂直切分、不引入部署/CI 机制、不做决策自动过期 gate（P0-brief out-of-scope）；`tests_filter` 示例不得裸 `python3`（用 `python -m pytest` 示意或注明遵循 `AGATE_PYTHON` 探测，BDD-8）。
7. **本批不涉及 ⑤ 组判据**；只做证据落点与模板登记。`agate/rules/`、`dispatch-protocol.md`、`judge.md`、`pre-commit-gate.py`、`agate-archive-stale-outputs.py` 一律**不改**（BDD-12/67 的空 diff 断言）。
8. **验证（自查，非 gate）**：`timeout 240 python3 -m pytest agate/tests/unit/test_mvwu_protocol_docs.py -q --tb=short -p no:cacheprovider`，**本批相关用例须转绿**（BDD-10、11（并保持 BDD-12 负向：P4-evidence 不进 rules/dispatch-protocol/judge 白名单）；其余批的文档类用例仍红属预期，勿去改）；`timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` 0 ERROR 且 `CHECK9-coverage` 无新增；`git diff --stat` 确认只动了本批文件。自查通过 ≠ P5 gate 通过，返回里不得声称"P5 已过"。
9. **产出记录**：写 `P4-implementation-batch-evidence-landing.md`（frontmatter 用 `agate-md-field-set.py`：phase=P4 / task_id=TAG0036 / parent=P3-test-cases.md / trace_id=TAG0036-P4-20260919 / type=implementation / created=2026-09-19 / status=draft / `implementation_dir: agate/`；`agent: implementer` set 不接受则 Edit 单行），正文：本批摘要（各文件改动落点 + 对应 BDD）、自查结果、新增文件核对表（本批无新增文件则写"无新增文件"）。`P4-implementation.md`（主文件）由波 1 创建，**本批不改**。
10. 范围外需求标 `[SCOPE+]`（行首声明格式）写入 `P4-progress.md`（用 `>>` 追加，行首加 `[batch-evidence-landing]` 前缀，与并行批共用该文件）并报告，不直接做。

### 上游关联

- `P2-design.md`（§0.1 改什么表 / §0.3 风险 R3-R14 / §3 ⑤ 组落点（插入位置 + 字面标记）/ §6 批表 / §10 files_to_read）；`P1-requirements.md`（BDD-10、11（并保持 BDD-12 负向：P4-evidence 不进 rules/dispatch-protocol/judge 白名单） 及其字面锚点）；`P3-test-cases-docs.md`（BDD→用例映射）

### 输入文件（files_to_read）

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P2-design.md（§0.1 本批行、§3、§6）
- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P1-requirements.md（BDD-10、11（并保持 BDD-12 负向：P4-evidence 不进 rules/dispatch-protocol/judge 白名单））
- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P3-test-cases-docs.md
- agate/tests/unit/test_mvwu_protocol_docs.py（本批相关用例，只读）
- agate/phase-cards/P4-implementation.md、agate/assets/templates/task-files.md（本批两文件）
- agate/scripts/check-mvwu.py（仅读 docstring 用法段，文档指针须与之一致）
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
- 波 1 已完成：`agate/scripts/check-mvwu.py`（476 行）+ M18 落库；`test_check_mvwu.py` + `test_protocol_alignment_review.py` 117 passed；ruff 0；consistency 0 ERROR（--strict-errors-only）。
- 基线：`test_mvwu_protocol_docs.py` 波 1 后仍有 ~27 个文档类用例红（本批负责其中与 BDD-10、11（并保持 BDD-12 负向：P4-evidence 不进 rules/dispatch-protocol/judge 白名单） 相关者）。
- 稳定版协议根 `~/.agate/v0.71.1/agate`（勿改）。
</objective_info>
