---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: protocol-alignment-review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

对 **P4a 批**的 `agate/**` 改动做协议-脚本对齐审查（SELF-GATE 语义 gate，A1-A7），产出 `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`（frontmatter：`review_date` / `reviewer: protocol-alignment-review` / `change_summary` / `files_changed`；结论枚举 ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW，A7 只有 ALIGNED / NEEDS_HUMAN_REVIEW）。**只审不写** —— 修复由主 Agent 回派 implementer。`agent` 非 main。

### 触发原因

P4a 改动 `agate/scripts/*.py`（`agate-dispatch.py` / `check-events.py`）+ 新增 `agate/scripts/*.py`（`check-dispatch-routing.py` / `agate_dispatch_route.py`）+ 新增 `agate/rules/*.yaml`（`dispatch-tiers.yaml`）+ `agate/*.md`（`dispatch-protocol.md` / `platform-notes.md`）+ `agate/**/*.md`（`assets/execution-roles/architect.md`）+ `agate/tests/**` → SELF-GATE 触发。

### 审查重点（A1-A7 逐项，结论须引用文档原文行号 + 脚本代码行号）

- **A1 文档→脚本对齐**：
  - `dispatch-protocol.md` 新增子节「派发路由（查表 → 派首选 → 逐级回落 → 再派发）」声明的 try-and-fall 步骤、三类回落理由码、「gate 不认谁生产的」、两条完整性不变量 —— 对应脚本 `agate_dispatch_route.py`（`resolve` / `classify_outcome` / `try_and_fall`）+ `check-events.py`（第 8 条）语义是否一致（≤ vs < / 强制 vs 建议 / 拦截 vs 警告 的语义级核对，不只看关键词存在）
  - `dispatch-tiers.yaml` 的 `tiers` 语义画像（尤其 `standard` = 「继承主 Agent 当前 model 的原生派发、不经 tier_bindings 展开」）—— 与 `resolve` 的 `standard` 短路分支（`form='default'` / `chain=None` / `model=current_model`）是否逐字一致
  - `check-dispatch-routing.py` schema 校验口径（`cli`/`effort` 枚举、`tier`/`candidates` 互斥、`fallback` 非法、`model: null` 放行、`machine_routes:` 文档化保留字）—— 与 P2-design §3.6 + P1 BDD-1~6 声明是否一致
- **A2 脚本→文档对齐**：新增的 `route` 子命令、`agate dispatch route <phase> <role>` 用法、`dispatch_route` 事件 JSON 结构、`check-events.py` 第 8 条理由码枚举 —— 是否都在协议文档（`dispatch-protocol.md` 新节 / `platform-notes.md` / 可能 `scripts/README.md`）有对应描述；有没有「脚本做了但文档没写」的裸露行为
- **A3 一致性连锁 + 反向传播**：
  - A3a（连锁）：`dispatch_route` 是新事件类型 —— `state-machine.md` / `WORKFLOW.md` / `check-events.py` 消费方（15 脚本 + 4 测试，P1 §3 第 4 组列过）里，哪些提到「已知 event 类型」的地方需要同步补 `dispatch_route`？（至少 `check-events.py` 第 7 条注释）
  - A3b（反向传播）：列出「应被 P4a 改动影响但未在 diff 中的文件」逐一验证。参考路径表：改 `check-*.py` 脚本行为 → `scripts/README.md` / `tests/README.md` / 对应角色文件；改 `dispatch-protocol.md` → 角色文件 / 模板文件；新增 `check-dispatch-routing.py` pre-commit 触发行为（若有）→ `WORKFLOW.md`「Pre-commit 检查总览」+ CHECK 9 锚点表。**特别核**：`check-dispatch-routing.py` 是否被挂进 pre-commit / CI（P2-design §3.6 说「不进 gate_commands、SELF-GATE 链手动跑 + 可选 pre-commit」）—— 若实现把它挂了 pre-commit 而 `WORKFLOW.md` 没同步 → MISALIGNED
- **A4 测试覆盖**：`agate/tests/unit/test_tag0034_*.py` + `test_tag0034_zero_change.py` 是否覆盖新逻辑边界（schema 非法样本 / `resolve` 每分支 / try-and-fall 三类回落 / `gate_fail` 被拒 / 全兜底 / 回归零改动）。**必须附最近一次 pytest 全量实跑输出（含 passed/failed 计数）** —— 跑 `timeout 600 python3 -m pytest agate/tests/ -q --tb=no`（或分片），把尾部计数贴进报告。无实跑输出的 ✓ 视为无效（T026 教训）。
- **A5 下游影响 + 文档传播**：
  - 破坏性变更？`dispatch_route` 事件对既有 `check-events.py` 账本审计是否向后兼容（既有任务的 `gate-events.jsonl` 无 `dispatch_route` → 第 8 条不误伤；已 MV8 实测）
  - `CHANGELOG.md` 是否需要标注（P4a 是协议语义变更 —— 新增 `agate dispatch route` 子命令 + `dispatch_route` 事件 + `dispatch-tiers.yaml` 词表 + `dispatch-protocol.md` 新节）。**注意**：`CHANGELOG.md` 更新按本仓惯例可能留到 P8 发布批；核实是否 P4a 就该加、还是 P8 统一 —— 按仓库既有 SELF-GATE 任务惯例判定，如留 P8 则在报告注明「CHANGELOG 待 P8」而非判 MISALIGNED
  - 文档传播：`orchestrator-template.md` / `WORKFLOW.md` / `role-system.md` / 角色文件 / 模板文件 / `LIMITATIONS.md` 是否需要同步提到派发路由这一步（尤其 `LIMITATIONS.md` 局限 2「同源模型系统性盲区」—— 本任务是它的部分缓解，是否该在 `LIMITATIONS.md` 加一句指向）
- **A6 锚点表覆盖**：`check-protocol-consistency.py` CHECK 9 的锚点表是否需要加 `check-dispatch-routing.py`？新增的协议规则（`dispatch_route` 理由码枚举 / routing schema）是否需要进锚点表？
- **A7 设计原则一致性**：逐条检查相关 ADR（`agate/adr.md`）——尤其 ADR-006（同源模型无解，本任务是其部分缓解）；「gate 解耦（gate 不认谁生产的）」是否与既有 gate 设计原则一致、是否该补一条新 ADR 记录「派发路由 / gate 生产者无关性」这个架构决策。结论只 ALIGNED / NEEDS_HUMAN_REVIEW。
- **DESIGN_GAP 优先核查（原则 6）**：P4-implementation.md 有一条 `[DESIGN_GAP]`（P4a `_route_main` 只做 resolve + 输出路由计划 JSON、端到端 try-and-fall 交 P4b），已被主 Agent 标 `[DESIGN_GAP_REVIEWED: 已确认]`（尚无 P7 记录 —— 任务在 P4）。若某审查项本应 MISALIGNED 但差异点完全对应这条已确认的 DESIGN_GAP，按原则 6 记 ALIGNED + 追加 `[KNOWN_DEVIATION: 来源 TAG0034 P4-implementation.md DESIGN_GAP_REVIEWED，理由摘要]`；否则按正常 MISALIGNED 处理。
- **Write 前检查**：写 `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md` 前先 `ls` 确认——不存在则直接写；存在且是本任务（`TAG0034`）同日复核轮则可覆盖；是别的任务遗留则改用带 `TAG0034` 的新文件名或暂停报主 Agent。留痕文件（若你用）开始前 `rm -f` 从空开始。
- **不改代码**：只写审查报告 + 留痕文件。`[PROD_NOT_TOUCHED]` / `[PROD_TOUCHED]` 二值声明。

> 子派发能力：不启用子派发能力（review 类角色）。

### 上游关联

- P4a implementer 已产出。`.state.yaml` phase=P4（P3 commit `c218026`）。
- P4a 改动清单（`git diff --name-only` 应含）：新增 `agate/rules/dispatch-tiers.yaml` / `agate/scripts/check-dispatch-routing.py` / `agate/scripts/agate_dispatch_route.py` / `agate-workspace/dispatch-routing.yaml`；改 `agate/scripts/agate-dispatch.py` / `agate/scripts/check-events.py` / `agate/dispatch-protocol.md` / `agate/assets/execution-roles/architect.md` / `agate/platform-notes.md` / `docs/design-notes/design-dispatch-routing.md` / `agate-workspace/roadmap/roadmap.md`；新增 `agate/tests/unit/test_tag0034_*.py`（P3 已 commit）—— P3 测试文件本身在 `c218026`，本次 diff 主要是脚本 + 文档。
- 意图（SELF-GATE 第一步）：给角色隔离补模型维度、部分缓解 `LIMITATIONS.md` 局限 2（ADR-006 无解的同源盲区）；机制 = 配置驱动跨 CLI/model 派发 + try-and-fall + `dispatch_route` 事件留痕；**gate 解耦（gate 只认产出文件 + exit code、不认谁生产的）是设计成立的前提**。
- P2-design.md §3 是方案权威；P2-review.md 8 条锁定决策；P1 §3 同类扫描 9 组（含 `dispatch_route` 全仓 0 命中 = 新事件、`check-events.py` 15 消费方、routed-away judge 非真缺口独立核实）。
- BDD-10 `[BASELINE_CHANGE]`（用户 2026-09-09 批准）：effort 按 `claude --help` 能力探测，代码不硬编码版本号。
- 并行进行：C8 `review`（P4 实现评审，产出 `P4-review.md`）—— 你与它并行、各审各的；你审「协议-脚本语义对齐」，它审「实现正确性 / R1 / 回归」。

### 输入文件

- **改动代码 + 文档**（审查对象，`git diff` 逐项）：`agate/scripts/agate_dispatch_route.py`（新）/ `agate/scripts/check-dispatch-routing.py`（新）/ `agate/scripts/agate-dispatch.py`（diff）/ `agate/scripts/check-events.py`（diff）/ `agate/rules/dispatch-tiers.yaml`（新）/ `agate/dispatch-protocol.md`（diff，新子节）/ `agate/assets/execution-roles/architect.md`（diff，DEBT0039①）/ `agate/platform-notes.md`（diff，effort 行）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md` + `P4-progress.md`（实现决策 + DESIGN_GAP）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（§3 方案 + §3.6 schema + §3.7 判定表 + §3.8 事件 + §4.3 DEBT0039 草稿 + §9 design-note 修订要点 —— 对齐基准）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（BDD-1~53 + §3 同类扫描 9 组）
- `agate/assets/review-roles/protocol-alignment-review.md`（你的角色定义 + A1-A7 清单 + 反向传播路径表 + 闭环规则）
- `agate/adr.md`（ADR-006 等 —— A7）
- `agate/scripts/check-protocol-consistency.py`（CHECK 9 锚点表 —— A6）
- `agate/WORKFLOW.md`（「Pre-commit 检查总览」+ gate 表 —— A3b/A5）
- `agate/scripts/check-events.py`（第 7 条「已知 event 类型」注释 —— A3a）
- `agate/LIMITATIONS.md`（局限 2 —— A5/A7）
- `CHANGELOG.md`（A5 —— 是否 P4a 就该加）
- `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md`（TAG0033 SELF-GATE 先例 + DEBT0039 来源）
- `docs/reviews/agate-alignment-review-20260904-TAG0030.md`（同类报告格式参照）
- `AGENTS.md`（SELF-GATE 机制、gate 脚本分层、`--strict-errors-only` 定义）

### 产出文件字段

产出 `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`，frontmatter 按角色定义「输出格式」（`review_date` / `reviewer` / `change_summary` / `files_changed`）。用 `agate-md-field-set` 写 frontmatter；不要手写；失败照提示改，仍失败报告主 Agent。正文含 A1-A7 逐项结论 + 引用原文/代码行号 + 总结论 + （若有）NEEDS_HUMAN_REVIEW 项待人工确认标注。
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
- 环境状态：worktree `.worktrees/agate-TAG0034`；`.state.yaml` phase=P4（P3 commit `c218026`）/ judge.enabled=true
- 主 Agent 自查（非 gate）：`pytest -k tag0034` 57 passed / 3 failed（3 红 = test_bdd_42 / 37 / 38，P4b/P4c）；`test_tag0034_zero_change.py` 2 passed；既有 `test_check_events.py` + `test_tag0027_b2_*` 23 passed；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0（12 行哈希链完整）；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0；ruff（agate_dispatch_route.py + check-dispatch-routing.py）clean
- `git log`：P3=`c218026` / P2=`b851b1e` / P1=`f75e129`；分支 `feat/TAG0034-dispatch-routing`
- P4-implementation.md `[DESIGN_GAP]` 已被主 Agent 标 `[DESIGN_GAP_REVIEWED: 已确认]`（任务在 P4，尚无 P7 记录）
- 报告落盘目标：`docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`（当前不存在，直接写）
- commit-msg hook 会检查 `self-gate-review:` / `self-gate-skip:` trailer —— 主 Agent 会在 P4a commit message 用 `self-gate-review: docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
