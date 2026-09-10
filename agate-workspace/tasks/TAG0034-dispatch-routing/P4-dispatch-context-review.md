---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

偏执 Staff Engineer 视角评审 **P4a 批**的实现代码，产出 `P4-review.md`（Header `status:` = `approved` / `rejected` / `needs-revision`，`agent` 非 main —— `check-gate.py` 在评审分支硬拦 `agent=main` 的 approved）。**只审不写** —— 修复方向写进评审文件，由主 Agent 回派 implementer。本任务 C8 映射（`domain: backend`）只触发本角色，单评审、直接产出 `P4-review.md`、无组长汇总。

### 约束（本任务的高危项优先）

- **模型购物完整性洞（R1，known_risks 最高危 —— 首要审查项）**：逐条机械核对 `agate/scripts/agate_dispatch_route.py` + `agate/scripts/check-events.py`：
  - `classify_outcome` / `Outcome.kind` 的取值集**只**有 `LAUNCH_FAIL` / `INFRA_ERROR` / `NO_PARSEABLE_OUTPUT` / `HAS_OUTPUT`，**无 `GATE_FAIL` 之类**；`.reason` 只可能是 `launch_fail` / `infra_error` / `no_parseable_output` / `None`
  - `try_and_fall` 循环的 `continue`（回落）分支**只**在上述三类基础设施信号触发；产出质量差 / 内容不完整归 `HAS_OUTPUT`（`return`，不回落，交 gate）—— 核 `HAS_OUTPUT` 的「格式合法」判据是否被实现成 **presence 级骨架可解析**（frontmatter 可解析 + 必需锚点标题存在），**没有**掺入内容完整度 / BDD 覆盖度校验（P2-design §3.7 N7 定死点；若实现把结构完整度塞进 `NO_PARSEABLE_OUTPUT` 分支 → CRITICAL）
  - `check-events.py` 第 8 条：`dispatch_route` 事件的 `candidates_tried[].reason` 出现 `gate_fail`（或任何非三值）→ `exit 1`；合法三值 → 不影响判定。核这条是**追加**审计链、**没有**改动第 1-7 条 + 哈希链算法（`sha256(上一行原始文本)` / GENESIS / ts 单调 / judge 计数）
  - 结论：R1 三处（`kind` 枚举 / 回落信号 / `check-events` 拒 `gate_fail`）任一留口子 → `[CRITICAL]` + `rejected`
- **回归硬约束（BDD-39/40）**：核 `git diff` 确认 **未改** `agate/rules/phases.yaml`（结构 + 字段）/ `agate/scripts/check-gate.py` / `agate/scripts/check-state-transition.py` / `agate/state-machine.md` 结构化部分 / `check-judge-verdict.py` / `check-p6-provenance.py` / `agate-cmdstream-*.py`。`agate-dispatch.py` 的改动**只**是新增 `route` 分支（`args[0] == "route"` 在 `_PHASES` 校验前）+ `_route_main`，既有 `_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by` 逐字节不变（`git diff agate/scripts/agate-dispatch.py` 逐行看）。`agate/tests/regression/test_tag0034_zero_change.py` + `agate/tests/unit/test_check_events.py` + `test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` 零改动仍绿（主 Agent 已核 23 passed，你复核 diff）。
- **枚举新增后所有消费方**（Pass 1）：`cli` 枚举 `{native, claude-code, codex, opencode}` / `effort` 枚举 `{low, medium, high}` / `reason` 枚举三值 —— `check-dispatch-routing.py` 与 `agate_dispatch_route.py` 与 `check-events.py` 三处对这些枚举的定义是否一致（有没有一处漏了 `native`、一处多了 `xhigh`）。`dispatch-tiers.yaml` 的 `tiers` key 集与 `check-dispatch-routing.py` 交叉核的 tier 白名单是否一致。
- **`resolve` 算法正确性**（P2-design §3.3 / P2-review 锁定决策 2）：优先级序（项目级 `candidates:` > 项目级 `tier:` > `tier_bindings:` 展开 > `factory_defaults` → `standard`）；`(phase,role)` 命中优先于 `phase` 级；`standard` 短路（`form='default'` / `chain=None` / `model=current_model` / `effort=None`，**不经 `tier_bindings` 展开** —— 这是「不配置 = 逐字节现状」不变量锚，破坏即 CRITICAL）；`tier` 引用但 `tier_bindings` 缺该 tier → `form='default'`（机会式）；effort 合并（候选自带优先 / 否则 route 层）；**T1（N2）**：每条分支返回键集恒为 `{form, chain, model, effort}`。核 `resolve` **不 mutate 调用方传入的 `routes` / `tier_bindings`**（测试会复用同一 dict）。
- **全兜底加载器**（`load_config`，BDD-16/17）：逐字对照 `agate/scripts/check-maintainability.py:_load_config`（88-148 行）—— 目录/文件不存在 → `({}, {})`；`yaml` 不可导入 → `({}, {})` + stderr；非 dict / 某键类型坏（如 `routes:` 写成 list）→ 该键默认 + stderr WARNING、**不抛异常、不静默把整段路由跳过**。
- **`build_dispatch_command`（BDD-8/9/10/31/32）**：effort 映射 Codex `-c model_reasoning_effort=<e>` / OpenCode `--variant <e>`（或 `#<e>`）/ **Claude Code 按 `effort_supported` 布尔**——True 加 `--effort <e>`、False 省略不报错（BDD-10 `[BASELINE_CHANGE]`，判据 key off 能力探测、**代码里不得硬编码版本号**）；`model: null` → 不传 `--model`。核 `effort_supported` 参数确实由**调用方**传入（能力探测在调用侧、非 `build_dispatch_command` 内部写死）。
- **`write_dispatch_route_event`（BDD-28/29）**：复用 `agate_common.append_event`（不自造哈希链）；**不写 `state_transition`、不动 `retries`、不触发 PAUSED**；事件 JSON 结构与 `gate_run` / `judge_verdict` / `state_transition` 同构。
- **DESIGN_GAP 已核**：P4-implementation.md 的 `[DESIGN_GAP]`（P4a `_route_main` 只做 resolve + 输出路由计划 JSON、端到端 try-and-fall 交 P4b）已被主 Agent 标 `[DESIGN_GAP_REVIEWED: 已确认]`（与 P2-design §4.1 批次意图一致）。你核这个决策是否真的没在 P4a 引入「模型购物」路径（P4a 无 `dispatch_once`、无实际子进程派发，只输出路由计划 → 天然无回落循环运行 → R1 在 P4a 不可触发，交 P4b 落地循环时再验）。
- **代码健康**（Pass 2）：资源泄漏 / 错误被吞 / `subprocess` 无 timeout（P4a 若已有 spawn 骨架）/ 异常处理边界 / `sys.path` 注入副作用（helper 模块被 import 时）/ 循环导入（`agate-dispatch.py` import `agate_dispatch_route`，后者不应反向 import 前者）。
- **测试转绿核实**：主 Agent 已跑 `pytest -k tag0034` = 57 passed / 3 failed（3 红 = `test_bdd_42`（P4b）+ `test_bdd_37/38`（P4c），符合批次边界）。你抽查 2-3 个 P4a 目标测试的断言与实现是否真对应（不是实现被写得刚好骗过断言）。
- **技术债格式**：若提「后续应重构 / 架构债」必须用标准 DEBT 条目格式（模板 `agate/assets/templates/tech-debt-template.md`，`evidence` 必填，登记 `agate-workspace/debt/tech-debt.md`）。
- **RM-AG0046 checklist**：`python3 agate/scripts/check-maintainability.py` 检出 violations 非空时，approve 前须读任务目录 `known-violations.md` 登记理由（本任务大概率 violations 为空，先跑一次确认）。
- **格式**：约束节 / 评审正文避免行首 `- PASS` / `- FAIL`（`check-p6-provenance.py` provenance 预判检测）。

> 子派发能力：不启用子派发能力（review 类角色）。

### 上游关联

- P4a implementer 已产出（见 `P4-implementation.md` + `P4-progress.md`）。`.state.yaml` 现 phase=P4（P3 已 commit `c218026`）。
- 新增：`agate/rules/dispatch-tiers.yaml` / `agate/scripts/check-dispatch-routing.py` / `agate/scripts/agate_dispatch_route.py` / `agate-workspace/dispatch-routing.yaml`（scaffold）。修改：`agate/scripts/agate-dispatch.py`（`route` 分支）/ `agate/scripts/check-events.py`（第 8 条）/ `agate/dispatch-protocol.md`（新节 + DEBT0039②）/ `agate/assets/execution-roles/architect.md`（DEBT0039①）/ `agate/platform-notes.md`（effort 行）/ `docs/design-notes/design-dispatch-routing.md`（§2.1/§2.2 重写）/ `agate-workspace/roadmap/roadmap.md`（RM-AG0060 回写）。
- 主 Agent 自查（非 gate）：`pytest -k tag0034` 57 passed / 3 failed；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py <task dir>` exit 0（12 行哈希链完整）；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0；ruff 4 脚本 clean；既有 `test_check_events.py` + `test_tag0027_b2_*` 23 passed。
- 并行进行：`protocol-alignment-review`（SELF-GATE A1-A7，产出 `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`）—— 你与它并行、各审各的；你审「实现正确性 / R1 / 回归」，它审「协议-脚本语义对齐」。
- P2-design §3 是方案权威；P2-review 8 条锁定决策是实现预期权威。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md`（**改动清单 + DESIGN_GAP + 关键实现决策**）+ `P4-progress.md`
- 代码（评审对象）：`agate/scripts/agate_dispatch_route.py`（**核心，逐行**）、`agate/scripts/check-dispatch-routing.py`、`agate/scripts/check-events.py`（`git diff` 只看第 8 条追加）、`agate/scripts/agate-dispatch.py`（`git diff` 只看 `route` 分支）、`agate/rules/dispatch-tiers.yaml`、`agate-workspace/dispatch-routing.yaml`
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（§3.3 / §3.6 / §3.7 判定表 + N7 / §3.8 —— 实现正确性对照基准）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-review.md`（8 条锁定决策）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（BDD-1~53 判据；BDD-10 `[BASELINE_CHANGE]`）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（known_risks 最高危 = 模型购物完整性洞）
- 测试文件（验收契约）：`agate/tests/unit/test_tag0034_{schema,resolve,tryfall,events,native,interaction,docs}.py` + `agate/tests/regression/test_tag0034_zero_change.py`
- `agate/scripts/check-maintainability.py:88-148`（`_load_config` —— `load_config` 逐字对照对象）
- `agate/scripts/agate_common.py`（`append_event` —— 事件写入复用核实）
- `agate/assets/review-roles/review.md`（你的角色定义）
- `AGENTS.md`（gate 脚本分层、双工作区纪律）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P4-review.md agate-md-field-set --list` 查看应填字段；逐个写入（`status` 落 `approved` / `rejected` / `needs-revision`，`agent` = review 非 main）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
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
- 主 Agent 机械核查：`pytest -k tag0034` = 57 passed / 3 failed（3 红 = test_bdd_42 / test_bdd_37 / test_bdd_38，均 P4b/P4c）；`test_tag0034_zero_change.py` 2 passed；既有 `test_check_events.py` + `test_tag0027_b2_*` 23 passed；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0；ruff（agate_dispatch_route.py + check-dispatch-routing.py）clean
- P4-implementation.md 的 `[DESIGN_GAP]` 已被主 Agent 标 `[DESIGN_GAP_REVIEWED: 已确认]`
- CLI 版本（本机实测）：Claude Code 2.1.266（有 `--effort`）/ codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- 评审结论若 approved：`check-gate.py P4` 硬拦 `agent=main` 的 approved —— Header `agent` 必须是 `review`
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
