---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

产出 `P3-test-cases.md`（用例清单，1:1 映射 P1 的 53 条 `#### BDD-NN` + P2-review 折入的 T1/T2/T3）+ 测试代码。**TDD：测试先写、当前必须红灯**。测试代码落 `agate/tests/`（本任务改 agate 自身，沿用既有测试树，非任务目录 `P3-test-code/`），文件名 `test_tag0034_*.py`。`P3-test-cases.md` 必须声明 `test_code_dir: agate/tests/`。

### 约束

- **1:1 BDD→测试**：P1 每条 `#### BDD-NN`（1~53）转一个测试用例，测试函数名含 BDD 编号（如 `test_bdd_1_tier_effort_two_axes`）。用例清单每条注明对应 BDD + 预期红灯原因（B 类：目标模块/子命令/审计链未实现）。
- **P2-review 折入的 3 条测试点**（P2-design §1 M11「必含 3 条（评审补）」+ §10 第 2/3/4 条），各写独立用例并在清单标注 T1/T2/T3：
  - **T1**：`resolve(phase, role)` 每条分支返回对象键集恒为 `{form, chain, model, effort}`、`form ∈ {'default','chain'}`、`form=='default'` 时 `chain is None`
  - **T2**：try-and-fall 用例集补「模拟 `wait(pid)` 超时 / RM-AG0055 命令流阈值触发 kill → `outcome.kind == INFRA_ERROR`、回落 `infra_error`」
  - **T3**：`check-events.py` 第 8 条参数化——`launch_fail` / `infra_error` / `no_parseable_output` 三值各构造一条合法账本断言 exit 0 + 混入第四值（如 `gate_fail`）断言 exit 1
- **红灯性质要求（check-tdd-red.py 会核）**：
  - **功能类 BDD**（schema 校验 / `resolve` / try-and-fall / `dispatch_route` 事件 / `cli:native` / 子进程 spawn / tmux wrapper —— 大部分）：红灯必须是 **B 类**（项目内 import 失败 / 模块或子命令不存在 / `AttributeError`）——因目标物尚未实现：`agate/scripts/check-dispatch-routing.py` 不存在、`agate-dispatch.py` 无 `route` 子命令、`check-events.py` 无第 8 条、`agate/rules/dispatch-tiers.yaml` 不存在、`agate-workspace/dispatch-routing.yaml` scaffold 待 P4a 建。**不得**是 A 类（SyntaxError / 第三方 import 失败 / 断言与 fixture 自相矛盾）。
  - **文档断言类 BDD**（BDD-41「gate 不认谁生产的」+ 两不变量 + 步位于铁律 1 前 / BDD-46「design-note 配置落点 + 核心循环」/ BDD-47「roadmap RM-AG0060 旧措辞回写」/ BDD-48「architect.md 批次设计节边界措辞」/ BDD-49「dispatch-protocol.md 派发编排机制节 author-P4-vs-一致性-P7」/ BDD-52「design-note 两轴 + key + 弱强缓解」/ BDD-53「design-note 两条完整性不变量 + per-machine」/ BDD-8/9/10 中 `platform-notes.md` 注明部分 / BDD-45「单 Agent 模式路由 no-op 显式声明」）：写成 **grep/字符串断言测试**（对目标文件搜关键措辞），当前红（措辞未写入），P4 author 正文后转绿 —— 这是 `agate/tests/unit/test_tag0030_assertions.py` 同款「doc-assertion 审计 P3 写红、正文 P4 补绿」模式（DEBT0039 / TAG0030 先例）。断言的关键串要**稳定**（锚定语义短语，不锚定会漂移的整句排版）。
  - **回归护栏类 BDD（BDD-39 / BDD-40）**：BDD-39 = `agate/rules/phases.yaml` / `agate/scripts/check-gate.py` / `agate/scripts/check-state-transition.py` / `agate/state-machine.md` 结构化部分逐字节不变 + `agate/tests/unit/test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` 零改动仍绿。**做法**：P3 现在捕获这些文件的基线 sha256（写进 fixture 常量或 `agate/tests/fixtures/tag0034_regression_baseline.json`），测试断言「当前内容 hash == 基线 hash」。这是**长期不变量护栏**（test-designer 卡片「永久回归测试判据」允许断言当前状态），**P3 时是绿的**——在 `P3-test-cases.md` 明确标注 BDD-39/40 为「回归护栏，P3 绿属预期，非 TDD 违规」。BDD-40「不配置 = 逐字节现状 + `dispatch_route` 事件条数 = 0」的**端到端部分**（跑完整 P1→P8 无配置）依赖路由机制存在 → 该部分红（B 类，`agate dispatch route` 不存在）；「无 `dispatch-routing.yaml` 时加载器返回出厂默认」部分同样红（加载器待建）。整体：BDD-40 至少一个断言红。
  - **check-tdd-red.py 整体判据**：功能类 + T1/T2/T3 的 B 类红灯足以让 `check-tdd-red.py $TASK_DIR` exit 0（真红灯）。回归护栏类（BDD-39 / BDD-40 基线部分）绿不影响整体判定（有红即真红）。
- **结构化输出 fixture（P2-design §3.7 判定表 + §5 MV1~MV11）**：子进程 spawn 解析类用例（BDD-33~36）的 fixture 用 P2 真机构造的样本收敛——architect 的样本在 scratchpad `mv/`（若可读则参考其结构；不可读则按 §5 MV note 的字段描述构造）。落 `agate/tests/fixtures/tag0034_*/`（committed fixture）：Claude Code `--output-format json`（`stop_reason=end_turn` 正常 + 空 result）；Codex `--json` 事件流（`turn.completed` 正常 + `turn.failed`+顶层`error` 失败 + item 级 `status:"failed"`+`turn.completed` 两层样本）；OpenCode `--format json`（`step_finish.part.reason=stop` 正常 + `ProviderAuthError` + 纯空返回）。fixture 是**静态样本文件**，不在 CI 里真调 CLI。
- **测试组织（对齐 P2 §4 三批，便于 P4 分批转绿）**：
  - `test_tag0034_schema.py` —— BDD-1~6（`check-dispatch-routing.py` schema 校验）
  - `test_tag0034_resolve.py` —— BDD-7~18 + T1（`resolve` 算法 / 三层优先级 / 全兜底 / tier 展开 / `standard` 短路 / `tier_bindings` last-write-wins / effort 合并）
  - `test_tag0034_tryfall.py` —— BDD-19~28 + T2（try-and-fall 逐级回落 / 完整性不变量 / 回落非 retry / 挂死→infra_error）
  - `test_tag0034_events.py` —— BDD-27/29/30 + T3（`dispatch_route` 事件写入 + `check-events.py` 第 8 条）
  - `test_tag0034_native.py` —— BDD-31/32 + BDD-8/9/10（`cli:native` 各平台 + effort 映射，平台层可 mock）
  - `test_tag0034_subprocess.py` —— BDD-33~36 + BDD-42（子进程 spawn + 结构化输出解析 + routed-away judge 平台无关性）
  - `test_tag0034_tmux.py` —— BDD-37/38（tmux wrapper 生命周期，可 mock tmux）
  - `test_tag0034_interaction.py` —— BDD-43/44/45/51（五模式并行 / 自主再派发不走表 / 单 Agent no-op / P5→P4 回退重解析）
  - `test_tag0034_docs.py` —— BDD-41/46/47/48/49/52/53（doc-assertion，grep 关键措辞）
  - `agate/tests/regression/test_tag0034_zero_change.py` —— BDD-39/40（回归护栏 + 基线 hash）
  组织可调整，但**每条 BDD 有且仅有一个归属测试**，测试名含 BDD 编号，`P3-test-cases.md` 给全量映射表。
- **不改被测物**：P3 只写测试，不实现任何 `agate/scripts/` / `agate/rules/` / `agate/*.md` 的目标改动（那是 P4）。不新建 `check-dispatch-routing.py` / `dispatch-tiers.yaml` / `dispatch-routing.yaml`。
- **gate_commands.P3**（P2-design §8 固化）= `python3 -m pytest agate/tests/ -q`（无 formatter → check-tdd-red 退化为 exit-code-only）。你交付前须自跑 `python3 -m pytest agate/tests/ -k tag0034 -q` 确认：新用例**全部失败或错误**（不是 collect error 级 A 类），且失败原因是「目标未实现」。
- **不得引入 A 类**：`test_tag0034_*.py` import 的第三方（pytest / pyyaml）必须已装（已确认）；对尚不存在的项目内模块用 `pytest.importorskip` 是**反模式**（会变 skip 不是红）——直接 `import` 让它 B 类失败，或用 `subprocess` 调 `python3 agate/scripts/check-dispatch-routing.py` 断言非 0 / FileNotFoundError。
- **环境基线**：主 Agent 已跑 `agate-capture-env-baseline.py`（无 formatter，未写文件，属正常，不阻塞）。
- **无创建型资源**：本任务测试不建团队 / 外部条目（纯脚本 + 文件断言 + mock），无清理钩子要求。
- **格式**：约束节 / 清单避免行首 `- PASS` / `- FAIL`（provenance 预判检测）。

> 子派发能力：启用（执行角色，按需）——53+ 用例工作量大，若判断需按测试文件拆可派子任务；优先自己完成，逐文件 progress 落盘。

### 上游关联

- P2 已 commit（`b851b1e`）：`P2-design.md`（candidate A：MVP 双文件 `agate/rules/dispatch-tiers.yaml` + `agate-workspace/dispatch-routing.yaml`）+ `P2-review.md`（plan-eng-review approved，0 阻塞，7 非阻塞 + 3 测试缺口已折入）。`.state.yaml` 现 phase=P3（P2→P3 已 transition，未 commit）。
- P1-requirements.md 含 BDD-10 `[BASELINE_CHANGE]`（用户 2026-09-09 批准）：effort 按 `claude --help` 能力探测分流映射 `--effort`——BDD-10 测试须覆盖「探测到 `--effort` → 命令含 `--effort <e>`」+「未探测到 → 命令不含 effort flag、不报错」两分支 + `platform-notes.md` 注明串（doc-assertion）。
- P2-design 关键设计锚（测试据此写预期）：
  - §3.3 `resolve` 算法（返回 `{form, chain, model, effort}`，`form ∈ {default, chain}`；优先级序：项目级 `candidates:` > 项目级 `tier:` > `tier_bindings:` 展开 > `FACTORY.defaults` → `standard`；`tier_bindings` 同名键 last-write-wins）
  - §3.6 schema：`cli ∈ {native, claude-code, codex, opencode}`；`effort ∈ {low, medium, high}`；`tier`/`candidates` 互斥；`(phase,role)` key（role 可选）；`fallback` 字段非法；`model: null` 放行；`machine_routes:` 为文档化保留字（校验器 exit 0 放行、不作语义）
  - §3.7 try-and-fall：`outcome.kind ∈ {LAUNCH_FAIL, INFRA_ERROR, NO_PARSEABLE_OUTPUT, HAS_OUTPUT}`；回落只在前三类；`HAS_OUTPUT`「格式合法」= presence 级骨架可解析（不含内容完整度）；挂死被杀 → INFRA_ERROR
  - §3.8 `dispatch_route` 事件 JSON（`candidates_tried[].reason ∈ {launch_fail, infra_error, no_parseable_output}`，无 `gate_fail`；`final` / `prev_hash` / `ts`；复用 `append_event` 哈希链）；`check-events.py` 第 8 条追加审计链
  - §3.9 BDD-26（同阶段 gate-FAIL retry = 同候选、不重跑 `agate dispatch route`、`dispatch_route` 计数不增）vs BDD-51（P5→P4 跨阶段回退 = 重跑 `agate dispatch route`、机械重解析、无升档逻辑）
  - §3.10 tmux：`which tmux` 决定包裹 / 裸跑；session 名 `agate-{task_id}-{phase}-{短时间戳}`；`N` 默认 15s + 余量 10s 兜底强杀；`has-session` 判断 + 容忍 exit 1
- 既有对照物（回归护栏 + 命名参照）：`agate/tests/unit/test_check_events.py`（BDD-30「既有用例零改动仍绿」的对象）、`test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py`（BDD-39「渲染产物零改动」的对象）、`test_tag0030_assertions.py`（doc-assertion 模式参照）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（**53 条 BDD —— 测试主来源**；BDD-10 `[BASELINE_CHANGE]`）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（**批准方案**：§3.3 `resolve` / §3.6 schema / §3.7 try-and-fall + `outcome.kind` 判定表 / §3.8 事件 + check-events 第 8 条 / §3.9 交互表 / §3.10 tmux / §4 批次 / §5 MV1~MV11 真机样本 / §6 files_to_read / §8 gate_commands / §10 实现完成的标志 13 条）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-review.md`（T1/T2/T3 折入点 + 锁定决策 8 条 —— 测试预期以锁定决策为准）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（env_constraints / known_risks —— 尤其「模型购物完整性洞」的回归用例要求）
- `agate/assets/execution-roles/test-designer.md`（你的角色定义，含「永久回归测试判据」）
- `agate/tests/conftest.py`（既有 fixture / helper —— 复用不重造）
- `agate/tests/unit/test_check_events.py`（BDD-30 对象 + `check-events.py` 账本构造范式）
- `agate/tests/unit/test_tag0030_assertions.py`（doc-assertion 审计测试模式参照）
- `agate/tests/unit/test_tag0027_b2_agate_dispatch.py` + `agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py`（BDD-39 回归护栏对象）
- `agate/scripts/check-events.py`（现状 7 条审计链 + 哈希链 —— T3 / BDD-29/30 构造合法账本据此）
- `agate/scripts/check-maintainability.py`（`_load_config` 88-148 —— BDD-16/17 全兜底测试的判据形态参照）
- `agate/scripts/agate-dispatch.py`（现状 `main()` 分派 —— BDD 里「`route` 子命令不存在」的当前事实）
- `agate/rules/phases.yaml` + `agate/scripts/check-gate.py` + `agate/scripts/check-state-transition.py` + `agate/state-machine.md`（BDD-39 基线 hash 捕获对象）
- `AGENTS.md`（测试约定、双工作区纪律）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P3-test-cases.md agate-md-field-set --list` 查看应填字段；逐个写入（须含 `test_code_dir: agate/tests/`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P3

路径：phase-cards/P3-tdd.md
---
# P3 — TDD 测试设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P3 + 有合规理由（risk=low + 跳过风险已声明）→ 跳过，读 P4 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。**必须执行**。
   该步骤不阻塞流程——脚本的 stderr 输出（含 WARNING）均可忽略，执行完直接继续步骤 1。

**创建型测试清理钩子（强制要求）**：测试含创建资源用例（建团队/条目等）时，须声明清理钩子要求——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；验收环境残留由清理钩子与 post-test 残留检查共同兜底（见 P6 卡）。

1. 派发 test-designer subagent → 产出 P3-test-cases.md + 测试代码目录
   1.1 写 P3-dispatch-context-test-designer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 跑 check-tdd-red.py 确认红灯
3. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P3，不要提前写 P4——phase = 本 commit 的产出阶段
4. git commit -m "wf({Txxx}-P3): {摘要}"（phase=P3，P3 产出含 P3-test-cases.md + 测试代码）
5. P3 commit 完成后进入 P4：**phase 推进 P4 随 P4 产出 commit 一起**（P4-implementation.md 就绪后），不是单独 phase commit

## refactor 任务：回归测试口径

> 适用：P1 frontmatter 声明 `change_type: refactor` 的任务（P2-design.md §3.4）。功能任务（缺省）走上方既有 TDD 口径，不受本节影响。

refactor 任务无新增功能行为可断言，P3 测试设计改用**回归测试口径**：

- **测试设计 = 回归测试口径**：复用/保留既有测试用例，标注每条回归用例覆盖了重构涉及的哪些文件/路径；**不新增功能行为断言**（无新行为可断言）。
- **跳过 check-tdd-red 红灯步骤**：重构无新功能断言，测试套件本就全绿，红灯语义不适用（check-tdd-red 对 refactor 任务会误报 exit 2 绿灯）。回归质量由 P5 全量回归（gate_commands.P5）+ P6 的 `regression.log`（全量回归重跑）兜底。CI backstop 对 refactor 任务同样跳过 check-tdd-red（ci-gate-backstop.py P3 分支 refactor 感知）。
- **P3 gate 不变**：仍为文件存在性检查——refactor 的 P3 产出是 P3-test-cases.md（回归口径声明 + 既有用例覆盖映射），文件存在即满足 gate。

## 如果是重试

确认上一轮失败原因（测试设计不合理 / 未覆盖关键 BDD / 非真红灯）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P3 MAX=2）

## 前置条件

- [ ] P2-design.md files_to_read 完整（测试设计需要知道实现导航）
- [ ] P2-review.md status: approved（P2 不可裁剪）

## 派发

- **角色**：test-designer（`{agate_root}/assets/execution-roles/test-designer.md`）
- **输入**：P2-design.md + P1-requirements.md（BDD 验收条件，每条 `#### BDD-NN` 对应一个测试用例）
- **输出**：P3-test-cases.md + test_code_dir/
- **派发 prompt**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 产出规格

- P3-test-cases.md 必须声明 `test_code_dir: {路径}`
- 每条测试用例对应一条 P1 的 `#### BDD-NN` 验收条件（1:1 映射）
- UI 任务（P2 ui_affected: true）：必须含 Playwright/E2E 用例

## gate 规则

**check-gate.py P3**（hook + 主 Agent 预跑，秒级文件检查）：
- exit 1：P3-test-cases.md 不存在
- exit 2：P3-test-cases.md 存在（TDD 红灯由 check-tdd-red.py 独立确认）

**check-tdd-red.py**（主 Agent 手动确认红灯 + CI backstop P3 兜底）：

```bash
check-tdd-red.py $TASK_DIR
```

- **exit 0**：真红灯（assertion 失败 / 项目内 import 失败 = B类错误）— 测试正确但因实现未写而失败
- **exit 1**：假红灯（SyntaxError / 第三方 import 失败 = A类错误）— 测试代码自身错误
- **exit 2**：绿了 — 实现先于测试，违反 TDD
- **exit 3**：无可用测试运行器

**技术栈无关**：check-tdd-red.py 通过 formatter 将测试输出标准化为 JSON，不直接解析任何框架的输出格式。formatter 在 gate_commands.P3_formatter 中声明（可选）。不提供 formatter 时退化为 exit-code-only（所有红灯 = 可推进）。

**探测链**：`$TEST_RUNNER` 环境变量 → `gate_commands.P3`（P2-design.md 声明）→ `which pytest` → exit 3。`$TEST_RUNNER` 始终优先（退化为 exit-code-only，无 formatter）。

**formatter 选择**：见 `assets/formatters/README.md` 速查表。常用：pytest → `pytest.sh`，vitest → `vitest.sh`，go test → `go-test.sh`，其他 → `generic-exit-only.sh`。

## 按包拆分并行（条件触发，非强制）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P3 可拆分并行：

1. 每个 package 派一个 test-designer subagent
2. 各自写各自的测试文件（不同目录）
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit

拆分判据（本阶段特定）：
- P2 packages > 1 且包间无数据依赖 → 可并行
- 单包或包间有依赖 → 串行（不拆分）
- P2 未声明 packages → 串行

每个 subagent 的 dispatch-context 必须明确其负责的 package 范围（约束节写"只写 {pkg} 目录下的测试"）。

## 推进条件（全部满足才写 phase: P4）

- [ ] check-tdd-red.py exit 0（真红灯确认）
- [ ] P3-test-cases.md 存在且含 test_code_dir
- [ ] 测试代码目录存在
- [ ] UI 任务：Playwright/E2E 用例存在

## 常见错误

1. **测试绿了才 commit**：测试已在 P4 之前通过 → 违反 TDD"测试先于实现"原则。P3 的 gate 要求红灯
2. **忘记声明 test_code_dir**：后续阶段找不到测试代码 → P5 跑 gate_commands 时找不到测试路径
3. **测试覆盖不全**：只为部分 BDD 写了测试 → P6 验收时那些 BDD 没有自动化验证
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。
5. **只覆盖交互路径，忽略前置状态**：测试设计应覆盖 BDD Given 隐含的前置状态，不只覆盖 When/Then 路径（详见 WORKFLOW.md §P3 测试设计指导）

## 下游影响

- P4 用测试驱动实现（implementer 看测试理解预期行为）
- P5 跑同一套测试验证实现正确性（gate_commands.P5）

> 完成 → 读 phase-cards/P4-implementation.md
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P3（P2 已 commit `b851b1e`，P2→P3 transition 已 git add 未 commit）/ judge.enabled=true
- 测试树：`agate/tests/{unit,integration,regression,fixtures}/`；命名惯例 `test_tagNNNN_*.py`；`conftest.py` 有既有 helper
- gate_commands（P2 §8 固化，P3-P6 不得改）：`P3 = python3 -m pytest agate/tests/ -q`（无 formatter）；`P5 = ... -q --tb=no`；`P5_consistency` / `P5_events` / `P5_routing_schema` 见 P2-design §8
- 目标物当前均不存在（红灯锚点）：`agate/scripts/check-dispatch-routing.py` 无 / `agate/rules/dispatch-tiers.yaml` 无 / `agate-workspace/dispatch-routing.yaml` 无 / `agate-dispatch.py` 无 `route` 子命令（`main()` 从 `phase = args[0]` + `_PHASES` 校验起）/ `check-events.py` 7 条审计链无第 8 条
- CLI 版本（本机实测）：Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4（fixture 是静态样本，CI 不真调）
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- P3 gate：`check-gate.py P3` = 文件存在性（P3-test-cases.md 存在 → exit 2）；红灯由 `check-tdd-red.py agate-workspace/tasks/TAG0034-dispatch-routing` 独立确认（exit 0 = 真红）
- 主 Agent 会在你返回后跑 `check-tdd-red.py`——功能类 + T1/T2/T3 的 B 类红灯须足以让它 exit 0
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
