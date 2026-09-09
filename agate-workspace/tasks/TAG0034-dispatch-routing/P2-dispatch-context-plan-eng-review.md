---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: plan-eng-review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

工程经理视角评审 `P2-design.md`（TAG0034 派发路由方案设计），产出 `P2-review.md`。**只审不写** —— 问题写进评审意见，由主 Agent 回派 architect 修改。Header `status:` 落 `approved` / `rejected`（需较大返工时可用 `needs-revision`，计入 P2 retry，MAX=3）。本任务 C8 映射只触发本角色（`domain: backend + risk_level: any`），单评审、直接产出 `P2-review.md`、无组长汇总。

### 约束

- **实质锚点**：结论不得是裸 `approved` / `BLOCKER=0`。按角色输出结构（架构问题阻塞级 / 非阻塞 / 测试缺口 / 锁定决策）逐条写，每条带文件/小节/函数定位 + 建议。
- **多方案探索（可判定项）**：§2 是否有 ≥2 候选方案 + 权衡 + 选择理由，且选择理由**自洽**（判据轴 = 「机器级档位绑定②是否拆出独立文件」，SUGGEST #3 明确留 P2 定）。不要求判「是否最优」，要求判「探索了 + 理由不是稻草人」。
- **实现就绪度**：方案是否清晰到 implementer 无需额外步骤计划即可自主实现每个批（P4a/P4b/P4c）；`§6 files_to_read` 是否覆盖实现所需全部上下文（含行号片段）；`§10 实现完成的标志` 13 条是否与 53 条 BDD 对得上。
- **minimal_validation（P2 卡强制）**：§5 是否为真机结果（非「纯代码逻辑」声明）—— MV1~MV11。重点核：
  - **MV3 / MV4**（Codex 退出码不可靠 + item 级 vs turn 级两层 status）：§3.3 / §3.7 定死「turn 层为准」是否被 MV3/MV4 真机样本支撑；「item 级 `status:failed` 永不触发换候选」与「产出质量非回落信号」（BDD-24）是否一致
  - **MV7**（OpenCode bug②）：结论标注为「[实测机制一致 + 交互式 TUI 切换路径推断]」是否诚实（用 `opencode run -s -m` 程序化覆盖近似、非逐字复现交互切换）—— 证据强度不得被写成「已完全实测」
  - **MV10 + 文件顶部 `[BASELINE_CHANGE]`**：BDD-10 由「Claude Code 无 effort 旋钮→静默忽略」改为「按 `claude --help` 能力探测分流映射 `--effort`」（用户 2026-09-09 批准）。核：判据是否 key off 能力探测而非硬编码版本号；§3.4 / §5 MV10 / §9 / §10.6 / M10 措辞是否统一、是否残留 `2.1.264+` 之类把中间版本当事实的表述
- **模型购物完整性洞（最高危，R1 / BDD-24~28）**：核设计是否机械强制 —— ① try-and-fall 回落**只**在 `launch_fail` / `infra_error` / `no_parseable_output` 三类信号触发（§3.7 循环 + 判定表）；② 收到任何 gate 能评产出即停止回落（BDD-25）；③ gate FAIL → 同一候选正常阶段 retry、`dispatch_route` 事件计数不增（BDD-26）；④ `dispatch_route` 理由码枚举**无 `gate_fail` 值**、`check-events.py` 第 8 条机械拒绝（§3.8 M6）。若任一环留了「产出质量差也回落」「gate FAIL 换候选」的口子 → 阻塞级。
- **回归硬约束（G / R-not-modify）**：§1.2「不改什么」是否覆盖 `phases.yaml` 结构+字段 / `check-gate.py` / `check-state-transition.py` / 状态机 / `check-events.py` 第 1-7 条 + 哈希链算法 / `check-judge-verdict.py` / `check-p6-provenance.py` / `agate-dispatch.py` 既有渲染路径 / RM-AG0055 命令流机制 / RM-AG0054 推进决策 —— 每条有无「看起来该改 vs 为什么不改」。BDD-39/40 的回归证明路径是否可执行。
- **数据流 / 错误边界（§3.1 / §3.7）**：`agate dispatch` ↔ `agate dispatch route` 串联两步是否清晰；`cli: native` / `default` / `subprocess` 三 `form` 的「驱动会话零判断」衔接是否真的零判断（会话只读 `agate dispatch route` 的 stdout JSON）；`outcome.kind` 四值分类是否穷尽异常路径（三平台结构化输出 → `outcome.kind` 判定表 §3.7）。
- **状态机完整性**：候选回落 ≠ 状态机 retry（BDD-28）—— 回落不写 `state_transition` / 不动 `retries[Pn]` / 不触发 PAUSED、只写 1 条 `dispatch_route`，设计是否落实；BDD-26（同阶段 gate-FAIL retry = 同候选、不重解析）vs BDD-51（P5→P4 跨阶段回退 = 机械重解析、无升档逻辑）§3.9 的区分是否在实现层可落地、互不干扰。
- **接口契约**：`dispatch_route` 事件 JSON（§3.8）字段是否与既有 `gate_run` / `state_transition` / `judge_verdict` 同构、复用 `append_event` 哈希链；`target` 描述 JSON（§3.1 step 2.6）作为 P4a→P4b/P4c 跨批共享件、契约是否「P4a 定、P4b/P4c 只增不改」。
- **测试策略（§3 M11 / §8 gate_commands）**：unit / 回归覆盖面是否与 53 条 BDD 对应；`gate_commands` 是否每校验独立 key（无 `&&` 串接短路）、`P5_e2e` 正确省略（`ui_affected: false`）、`{key}_timeout_seconds` 分档合理；`check-dispatch-routing.py` 不进 `gate_commands.P5` 是否恰当（该文件是项目级配置非测试对象）。
- **批次设计（§4）**：`dispatch_plan: {mode: static-batch, batches: [P4a,P4b,P4c], serial}` —— P4a `complexity: high` 是否应拆更细（P2 卡「high 复杂度必须拆分」；此处 P4a 内已按模块列 M1/M3/M4/M6/M7，是否够）；同文件 `agate-dispatch.py` P4a+P4b 两批的串行依赖 + 「P4a 定契约、P4b 只增不改」是否说清；DEBT0039 两处文档批标 **P4**（不是 P7）是否与 DEBT0039 根因自洽。
- **DEBT0039 边界措辞草稿（§4.3）**：草稿①（architect.md）+ 草稿②（dispatch-protocol.md）是否忠实承接 DEBT0039 `closure_criteria`、是否只做边界澄清（不扩其它 DEBT、不改脚本/gate）、是否引了 TAG0030/TAG0033 先例。
- **技术债格式**：若你要提「后续应重构 / 架构债」，**必须用标准 DEBT 条目格式**（模板 `agate/assets/templates/tech-debt-template.md`，`evidence` 必填，登记 `agate-workspace/debt/tech-debt.md`）。不强制提债，一旦提就用标准格式。
- **范围**：方案是否有越出 `P0-brief.md` scope / out-of-scope 的设计（out-of-scope 明确排除：动态选型 / 续接软信号根治 / 第三方终端工具作依赖 / DSH / 局限 3 / RM-AG0055 机制本身 / RM-AG0054 `agate next` 本身 / probe / 跨机可复现 / retry 故意换升档模型）。§11 声明「无 `[SCOPE+]`」是否成立。
- **格式**：约束节 / 评审正文避免行首 `- PASS` / `- FAIL`（`check-p6-provenance.py` provenance 预判检测）。

> 子派发能力：不启用子派发能力（review 类角色）。

### 上游关联

- P1 已 commit（`f75e129`）；P1-requirements.md 含**用户批准的 `[BASELINE_CHANGE]`**（BDD-10，2026-09-09，行首标记 + frontmatter `baseline_changes` 登记）—— P2-design 的 BDD-10 相关设计（§3.4 能力探测映射）据此。P1 仍 53 条 BDD、requirements-review approved（retry #1 后）。
- P2-design.md（architect 产出 + 一轮 BASELINE_CHANGE 对齐修订）：`candidate_count: 2`（选方案 A：MVP 双文件，机器级②不拆）；`dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [P4a:high, P4b:medium, P4c:low], serial: true}`；`ui_affected: false`；`domains: [backend, cli]`；`packages: [agate-scripts, agate-rules, agate-docs, agate-tests]`。`check-frontmatter.py` exit 0；主 Agent 预跑 `check-gate.py P2` = exit 2（回退抵达态，暂不做完成度校验，属预期）。
- 3 处「P2 定」留白已在 P2-design 定死：BDD-15/18（§3.3 `resolve` 算法 + `tier_bindings` 同名键 last-write-wins）/ BDD-35（§3.3 / §3.7「turn 层为准」，MV3/MV4 佐证）/ BDD-38（§3.10 余量 = 10s）。
- 6 条已采纳 SUGGEST（P1 frontmatter `suggest_resolved`）是 P2-design §0 的既定前提。
- 前置 TAG0033 已合并 v0.70.0：`CodexAdapter`（`agate-cmdstream-adapters.py` class line 666 / `ADAPTERS["codex"]` line 878）。
- `check-events.py` 现状（MV8 实测）：第 7 条「未知 event 不拦截」→ 含 `dispatch_route` 的账本 exit 0；本任务第 8 条理由码枚举校验是**追加链**。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（**评审对象**）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（53 BDD + §3 同类扫描 9 组 + §5 suggest_resolved + BDD-10 `[BASELINE_CHANGE]` + §7 裁剪/DEBT0037/DEBT0039 —— 核对 P2 每条设计能追到 BDD）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-review.md`（requirements-review 的逐条 BDD 验收意图）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（scope / out-of-scope / known_risks 12 条 —— 范围核对基准）
- `docs/design-notes/design-dispatch-routing.md`（设计意图来源；§2.1/§2.2 + 头部为待修订交付物，冲突以 P0-brief 2026-09-09 定案为准 —— P2 §9 是修订要点）
- `docs/research/cross-platform-dispatch-mechanics.md`（三平台机制 A1-A19 + §6 结构化输出 + §10 复核清单 —— 核 P2 §3.7 判定表 / §5 MV 与实测一致）
- `agate/assets/review-roles/plan-eng-review.md`（你的角色定义）
- `agate/scripts/check-maintainability.py`（`_load_config` line 88-148 —— P2 §3.3 全兜底加载器逐字参考对象，核范式一致）
- `agate/scripts/agate-dispatch.py` + `agate/scripts/check-events.py`（P2 M4/M5/M6 落点 —— 核「既有路径零改动」可行性）
- `agate/rules/phases.yaml` + `agate/scripts/check-gate.py`（回归对照基准「结构零改动」；`_gate_p2_dispatch_plan` 校验口径 line 734 起）
- `agate-workspace/debt/tech-debt.md`（DEBT0037 / DEBT0039 条目 + closure_criteria —— 核 §4.2 / §4.3 处理）
- `AGENTS.md`（gate 脚本分层、SELF-GATE、`--strict-errors-only` 定义、双工作区纪律）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P2-review.md agate-md-field-set --list` 查看应填字段；逐个 `agate-md-field-set <key> <value>` 写入（`status` 落 `approved` / `rejected` / `needs-revision`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P2

路径：phase-cards/P2-design.md
---
# P2 — 方案设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → P2 不可裁剪。design_trivial / follows_existing_pattern 可简化（1 个候选方案），不可省略。

## 如果是首次进入本阶段

1. 派发 architect subagent → 产出 P2-design.md
   1.1 写 P2-dispatch-context-architect.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 C8 映射表派评审（见下方）
3. 评审通过 → P2-review.md status: approved
4. 预跑 check-gate.py P2（脚本化检查）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P2，不要提前写 P3——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P2): {摘要}"（phase=P2，P2 产出含 P2-design.md + P2-review.md）
7. P2 commit 完成后进入 P3：**phase 推进 P3 随 P3 产出 commit 一起**（P3-test-cases.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（方案选择有误 / 候选方案不足 / 评审 rejected）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P2 MAX=3）

## 前置条件

- [ ] P1-requirements.md 含 domains / risk_level / phases 声明
- [ ] P0-brief.md env_constraints 可查阅

## 派发

- **角色**：architect（`{agate_root}/assets/execution-roles/architect.md`）
- **输入**：P1-requirements.md + P0-brief.md
- **输出**：P2-design.md
- **派发 prompt 追加**：

```
## P2 最小验证
方案设计前，先用最小验证确认关键假设（10 行 HTML 测试页 / curl 请求 / 20 行脚本）。
验证结果写入 P2-design.md 的 minimal_validation 字段。
- 方案依赖浏览器行为/安全模型/外部系统行为 → 必须做最小验证
- 纯代码逻辑 → 须在 minimal_validation 字段声明 `纯代码逻辑，无外部系统依赖`（须写明依赖了哪些内部函数/数据转换）
```

## 产出规格

P2-design.md 必须包含：
- **候选方案 ≥2** + 权衡 + 选择理由（design_trivial / follows_existing_pattern 时可只写 1 个，见下方）
- **`candidate_count: N` 必填**：本方案候选方案数（≥2，design_trivial/follows_existing_pattern 时可 1），gate 按此字段校验，不再解析标题。你写几个候选就填几个，与正文一致。
- **四字段**：`packages:` `domains:` `ui_affected:` `gate_commands:`
- **files_to_read**：实现时需要参考的文件清单（控制 P4 implementer 上下文）
- **env_constraints**：确认/细化 P0-brief 的环境约束
- **minimal_validation**：验证结果 或 声明"纯代码逻辑，无外部系统依赖"（声明时须附理由）

`candidate_count`/`packages`/`domains`/`ui_affected` 写在文件头 **frontmatter**（`---` 分隔块），
不写正文；`gate_commands:`/`files_to_read:`/`env_constraints:`/`minimal_validation:` 留正文。
**可直接复制的完整样例**：
```yaml
---
phase: P2
task_id: TAG0001           # 替换为实际任务编号
type: design
parent: P1-requirements.md
trace_id: T001-P2-20260101 # {task_id}-P2-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: architect
# ── v2.0 机器字段 ──
candidate_count: 2                # int ≥1，必填
packages: [pkg-a]                 # list，必填
domains: [backend, cli]           # list，必填
ui_affected: false                # bool，必填
ui_design_section: true           # bool，可选（presence 语义：ui_affected: true 时声明已含 UI 设计节）
---
```

**UI 设计节（`ui_affected: true` 时必含，P2 gate 校验）：** `ui_affected: true` 的 P2-design.md
正文必须包含 `## UI 设计` 节，节内含**渲染形态声明**（`渲染形态:` 声明行，复用 P1 frontmatter
`ui_render_shape` 的规范形态值 + 中文注释，gate 按规范化值比对校验 P1-P2 一致；无 P1 声明时按
布局型默认）+ **维度选择**（`适用维度:` 声明行）+ **按形态适配的 checklist**（常规布局型 =
布局/交互/视觉三类；渲染组件/时序特效型 = 渲染正确性/动效时序等适用维度 checklist；不适用的维度
显式声明"维度不适用"）。缺 UI 设计节 / 缺形态声明 / 缺按形态 checklist / P1-P2 形态声明不一致 →
P2 gate exit 1。结构规格见 `assets/execution-roles/architect.md`「UI 设计节」节（由 architect
兼任产出，不新增 designer 角色）。

**骨架产出（`project_phase: bootstrap` 时必含，P2 gate 校验）：** P1-requirements.md frontmatter
声明 `project_phase: bootstrap`（0→1 新项目；缺省 `established` 不触发）的任务，P2 architect 除
P2-design.md 外，还须在 task 目录下产出 `P2-skeleton.md`（须含 `## 骨架声明` 标题）。骨架内容以
「候选目录集合 + 项目侧声明」的参数化形式表达（不写死具体语言/框架目录名），模板见
`assets/templates/skeleton-template.md`，结构规格见 `assets/execution-roles/architect.md`
「骨架设计职责」节（由 architect 兼任产出，不新增专属角色）。`project_phase` 字段缺失或非
`bootstrap` 时不检查（向后兼容，行为与改动前一致）。

候选方案简化（须附理由，无理由视为无效声明，要求 ≥2 候选方案）：
- `design_trivial: true` + 理由（为什么 trivial）→ 可只写 1 个候选方案（P2 仍不可省略）
- `follows_existing_pattern: [src/foo.py]`（列出参照文件路径）→ 可只写 1 个候选方案，参照已有模式（P2 仍不可省略）

## dispatch_plan 机器字段（可选，TAG0014）

> 本字段是 P2 对**后续阶段编排方案**的机器声明（评估 + 编排模式，见 dispatch-protocol「派发编排机制」），由 architect 在"批次设计"节（execution-roles/architect.md）产出，P2 gate 校验其合法性。

方案含多个独立子任务（多包/多模块/high 复杂度）时，P2-design.md frontmatter 应声明 `dispatch_plan:`（单行 flow YAML，与 candidate_count 同级，**不入 frontmatter-check schema**，缺省不校验）：

```yaml
# ── v2.0 派发编排字段（可选）──
dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [{id: pkg-a, complexity: medium}, {id: pkg-b, complexity: low}]}
```

字段契约（gate 校验口径）：
- `mode` ∈ {single, static-batch, parallel, recon-then-split, serial}——编排模式（单发/静态拆批/并行/先理解后拆/串行链）
- `parallel_limit` 可选，≥1 整数——并行上限（缺省 3）
- `batches` 可选——mode ∈ {static-batch, parallel} 时每批须含 `id` + `complexity` ∈ {low, medium, high}；批数 ≤ parallel_limit
- 缺字段 / 坏 YAML → P2 gate 跳过校验，行为等同现状（向后兼容，不误拦）

## 影响面梳理（强制节）

**写候选方案之前**先做影响面梳理——方案的取舍取决于它牵动多大面，先设计再补影响面等于反过来给方案找理由。P0 卡片的「同类/影响面预判」给量级、P1 卡片的「同类扫描」给清单，P2 在这两者基础上做**候选方案级**的影响域分析，三处同源、逐级细化，不重复劳动。

P2-design.md 正文必须含影响面梳理节，覆盖三部分：

1. **改什么（Modify）**：逐文件/逐模块列出改动点 + 关联 BDD 编号；改动落点必须落到"哪个文件的哪个小节/函数"，不写"相关代码"这种模糊表述
2. **不改什么（Not Modify）**：显式列出**看起来该改但决定不改**的文件/范围 + 理由。这一栏比"改什么"更容易漏，也是 P4 implementer 判断范围边界的依据（避免"顺手改进"）
3. **风险在哪（Risk）**：每条风险配一条缓解措施；跨模块引用、双源同步（权威源 + 副本）、schema 变更、并发/资源竞争是高频风险项

梳理动作要有客观证据：grep/rg 命中清单、读过的消费方代码、既有 gate 脚本的校验口径——不是凭印象列。P1 已声明 `follows_existing_pattern` 的任务同样要做（沿用既有模式不等于影响面为零）。

## gate_commands 声明

gate_commands 在 P2 固化，后续阶段按此执行：

```yaml
gate_commands:
  P3: "pytest"                  # 可选：测试运行器（verbose 输出，供 check-tdd-red.py 自动读取）
  P5: "pytest -q --tb=no"       # 紧凑输出模式
  P5_e2e: "playwright test --reporter=line tests/e2e/"  # ui_affected: true 时必填
  P5_timeout_seconds: 120       # 可选：该 key 命令的预期耗时上限（秒），见下方字段规则
  P5_e2e_timeout_seconds: 300   # 可选：per-key 声明，不同命令类型各自取档
```

### `{key}_timeout_seconds` 字段规则

`timeout_seconds` 是 `gate_commands` 块内的**可选声明性字段**，用来给每条 gate 命令声明"预期耗时上限"，供跑命令的一方（主 Agent / subagent）据此设置 shell 层超时。四点规则：

1. **排除 P3**：`gate_commands.P3` 继续走既有 `AGATE_TDD_TIMEOUT` 环境变量机制（默认 120s，由 `agate_common.py` 的 `run_test_with_formatter()` 消费、`check-tdd-red.py` 读取，exit 124 → 超时 JSON，区分 A/B 类错误）。`timeout_seconds` **只服务 P5 / P6 / 其他非 P3 key**，不覆盖 P3。两层不合并：P3 层是运行时代码真实消费的超时，`timeout_seconds` 是给人和 subagent 读的静态声明
2. **per-key 声明**：写成 `{key}_timeout_seconds`（如 `P5_timeout_seconds` / `P5_e2e_timeout_seconds`），每条 key 各自声明，**不设整体共享默认**——单元测试与 E2E 的耗时差 2.5 倍以上，共享一个值起不到分类阈值的作用。命名与既有 `{key}_formatter` / `{key}_e2e` 的 per-key 惯例一致
3. **三档默认基准表**（**建议档位，需按命令类型手动声明，不是自动推断**——没有任何代码去"猜"命令属于哪一类）：

   | 命令类型 | 建议档位 | 依据 |
   |---------|---------|------|
   | 单元测试类（pytest / vitest 等） | 120s | 与 `AGATE_TDD_TIMEOUT` 默认值对齐，同类命令的既有锚点 |
   | E2E 类（Playwright / CDP） | 300s | 覆盖页面加载 + 多步操作；比脚本内部硬超时（HARD 90s/180s）更大——外层命令级预期时长必须留够内层完整走完的余量 |
   | 构建类（编译 / 安装依赖 / 打包） | 600s | 覆盖 `npm install` / 编译等长操作。宁可档位定高，也不要让长命令被误判失败（TPV0093 教训：`make test-quick` 挂 188 分钟） |

4. **向后兼容**：缺字段 → 行为等同现状（沿用 `dispatch_plan` 的"缺字段 / 坏 YAML → gate 跳过校验"先例），不新增强制阻断，老任务无需回填

与运行时超时纪律的关系：本字段是**静态声明**（层级 1），subagent 执行命令时真正去设 shell timeout 的是**层级 4** 的「命令超时兜底」（取值 = 预期耗时 ×1.5；本字段已声明时"预期耗时"直接取该值）。四层超时机制的完整分层见 dispatch-protocol.md「命令超时兜底与既有超时机制的分层关系」。

### env_constraints 与 gate_commands 的边界（不等价）

`env_constraints` 是**声明性字段**——它只做信息确认/注入（写清楚环境约束是什么，供 P4/P8 读取参考），本身不会被自动执行，也没有任何 gate 脚本会去校验 `env_constraints` 里写的条件是否真的成立。真正被执行的机制是 `gate_commands`：P5/P6 只会去跑 `gate_commands` 里声明的命令，不会去"执行" `env_constraints` 的内容。二者不等价，不能互相替代。

**因此**：任何需要被强制执行的约束，必须落到 `gate_commands`（有命令可跑、有 exit code 可判定），或者落到 P4/P8 阶段卡片里的明确 checklist 条目（有人工自查动作可执行）。只写进 `env_constraints` 而不落 `gate_commands`/checklist 的约束，等于没有强制力——architect 设计时若发现某条环境约束必须被强制执行，不要止步于写进 `env_constraints`。

### `--strict` 反模式：不要放进 `&&` 链路中间

`gate_commands` 的每个 key 声明的是**一条完整命令**，若把多个校验命令用 `&&` 拼接成一条命令串塞进同一个 key，会有短路问题——只要前一个命令非零退出，后面的命令（包括 `--strict` 校验）根本不会跑，看似"全部声明了"，实际后半段从未被执行过，问题被掩盖。

**反例（不要这样写）**：
```yaml
gate_commands:
  P5: "pytest -q --tb=no && check-protocol-consistency.py --strict && shellcheck scripts/*.sh"
```
上面这条命令一旦 `pytest` 失败就短路退出，`--strict` 校验和 `shellcheck` 都不会执行，历史上 TAG0004 等任务已经在这类写法上吃过亏。

**正确做法**：把每个校验拆成独立的 key 分别声明，各自独立跑、独立记录 pass/fail，不共享短路关系：
```yaml
gate_commands:
  P5: "pytest -q --tb=no"
  P5_consistency: "check-protocol-consistency.py --strict-errors-only"
  P5_shellcheck: "shellcheck scripts/*.sh"
```
`--strict-errors-only`（仅 ERROR 判失败）适合日常任务默认使用；`--strict`（WARNING-only 也判失败）保留给专门做 WARNING 债务清理的任务主动选用。

### `P3_xxx` 禁止声明（P2 卡禁令，BDD-6）

`gate_commands` 的测试命令键只允许裸 `P3`（`check-tdd-red.py` 只收集精确键
`key == "P3"`）。禁止声明 `P3_xxx` 检测键：旧解析器曾用 `startswith("P3")`
静默收集辅助键，致 TDD 误执行非测试命令。白名单后缀清单（不收集为检测命令）：
`_formatter` / `_timeout_seconds`（元键，`is_gate_meta_key` 豁免）+ `_e2e`
（E2E 形态，P5_e2e 消费，P3 永不收集）+ 历史 `_js` / `_html`（已退役，
不得复用为检测键；未来多栈回归走协议修订登记收集后缀，不走静默收集）。

### CHECK / 扫描面上线流程（DEBT0025：先全量扫描存量）

`check-platform-assumptions.py` 新增 CHECK / 扫描面上线时，先全量扫描存量
测试树登记命中清单，有命中先登记再启用常驻阻断，避免存量命中阻断正常开发。

## 评审派发（C8 机械映射）

按 P1 声明的 domains + risk_level 机械映射评审：

| domain | risk_level | 必须派的评审 |
|--------|------------|------------|
| backend | 任意 | plan-eng-review（P2 方案评审） |
| frontend | 任意 | plan-design-review |
| 任意 | high | plan-eng-review（硬规则，必须派独立 subagent） |
| 任意 | full（tier=full 或声明 ceremony: full）| plan-eng-review（硬规则，必须派独立 subagent）+ cso（security 域）+ P7 不可裁 |
| P1-requirements.md 含 [NEED_CONFIRM] 且涉及业务方向 | 任意 | plan-ceo-review |

> **去重说明**：同一任务命中多行且触发同一评审角色时，去重只派发一次（如 backend + high 均命中 plan-eng-review，只派 1 个 plan-eng-review，不重复派发）。

多个评审角色 `专家组并行` → 组长汇总 → P2-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件（示例非穷举，按 C8 映射表触发）：
   - plan-eng-review → P2-review-eng.md
   - plan-design-review → P2-review-design.md
   - plan-ceo-review → P2-review-ceo.md
   - cso → P2-review-cso.md
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长输入：所有评审文件路径
5. 组长产出：P2-review.md（统一 status: approved / rejected）。**组长 subagent 产出的 P2-review.md 的 Header agent 字段必须是组长角色名（非 main）——check-gate.py P2 硬拦截 agent=main 的 approved**
6. 组长规则：
   - 不发表新意见，只汇总
   - 任何专家标 BLOCKER → status: rejected
   - 多位专家分歧 → 标「专家组分歧」交人工
   - 全票无 BLOCKER → status: approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P2-review.md。

review 不通过 → architect 修改方案 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

**UI 测试选择器**：涉及前端时，P2 design 建议声明 UI 组件的稳定测试标识清单（如 `data-testid`，而非 class 命名）。P3 test-designer 用稳定标识定位元素，P4 implementer 按清单实现--class 命名可重构，稳定标识不变。具体方案由 P2 architect 决定。

## gate 规则

```bash
check-gate.py P2 $TASK_DIR
```

- 候选方案数 ≥2（design_trivial / follows_existing_pattern 时可只写 1 个）
- P2-review.md 存在且 status: approved（agent≠main）— 不存在 → gate exit 1
- 四字段齐全（packages/domains/ui_affected/gate_commands）
- gate_commands.P3 可选（非 pytest 项目建议声明，供 check-tdd-red.py 自动读取测试运行器）
- 候选方案 ≥2 时含权衡/选择理由

## 推进条件（全部满足才写 phase: P3）

- [ ] P2-design.md 候选方案 ≥2（或 design_trivial/follows_existing_pattern 须附理由时可只写 1 个）+ 四字段齐全
- [ ] 含「影响面梳理」节（改什么 / 不改什么 / 风险在哪 三部分齐全，且写在候选方案之前）
- [ ] P2-review.md 存在且 status: approved（agent≠main）
- [ ] gate_commands.P5_e2e 已声明（ui_affected: true 时）

## 常见错误

1. **忘了最小验证**：方案依赖外部系统行为（API MIME 类型、浏览器 CSP 等）但直接假设前提成立 → 到 P6 才发现不可行。跑一个 curl / 10 行 HTML 就能 5 分钟发现
2. **gate_commands.P5 只列单元测试**：UI 任务时缺少 P5_e2e → P5 不会跑端到端验证
3. **files_to_read 列太多文件**：把所有相关文件都列上 → P4 implementer 上下文爆炸。只列确实需要参考的
4. **忘了派评审**：按 C8 映射机械执行，不靠"觉得不需要"
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P4 依赖 files_to_read 导航代码阅读范围
- P5 依赖 gate_commands 执行验证命令
- P6 依赖 ui_affected 判断是否需要 vision-helper
- gate_commands 在 P2 固化后 P4-P6 不能改——设计阶段是声明验证契约的唯一窗口

> 完成 → 读 phase-cards/P3-tdd.md
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P1（P1 已 commit `f75e129`，phase→P2 随 P2 产出 commit 一起推进）/ judge.enabled=true
- P2-design.md 机械核查（主 Agent 已跑）：`check-frontmatter.py` exit 0；`candidate_count: 2` 与正文一致；§1 影响面梳理（1.1 改什么 12 项 / 1.2 不改什么 8 项 / 1.3 风险 11 条）写在 §2 候选方案之前；`dispatch_plan` 已过 `_gate_p2_dispatch_plan`；无残留 `[NEED_CONFIRM]` / `2.1.264+`
- `check-gate.py P2` 预跑 = exit 2（回退抵达态，主 Agent 自判，非失败）
- `check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` = exit 0（账本 5 行，哈希链完整，ts 单调）
- CLI 版本（本机实测）：Claude Code 2.1.266（P0-brief 记 2.1.263）/ codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- 评审结论若为 approved：`check-gate.py P2` 硬拦 `agent=main` 的 approved —— P2-review.md 的 Header `agent` 必须是本角色名（非 main）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
