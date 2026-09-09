---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: analyst
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

产出 `P1-requirements.md` —— TAG0034「派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）」的需求基线：把 P0-brief 的 scope 待确认项逐条转成可二值判定的 BDD 验收条件（P0-brief 计划 ≥22 条），能在 P1 定死的设计选择直接写进需求、真无方向的标 `[NEED_CONFIRM]`、有倾向的标 `[SUGGEST:]`。frontmatter 声明 domains/packages/risk_level/phases。

### 约束

- **范围锁定（P0-brief 核心约束 6，最高优先级）**：需求分析若发现需超出 `P0-brief.md` 的 scope / out-of-scope 边界，**立即停下，在 P1-requirements.md 行首写 `[NEED_CONFIRM: 具体超范围点]` 并报告主 Agent**，不要擅自扩范围。P0-brief 已经过两轮外部评审 + 2026-09-09 讨论定案，边界是刻意收紧的。
- **这是跨会话恢复任务**：读完 P0-brief 第一动作是时效性质疑。立项 2026-09-08 / 启动 2026-09-09，间隔约 1 天。主 Agent 已粗核：TAG0033/RM-AG0061 确已合并 v0.70.0（`CodexAdapter` 可用）、三 CLI 已装已认证、worktree 就绪 —— 无严重漂移。已知轻微偏移：Claude Code 本机实际 `2.1.266`（P0-brief/HANDOFF 记 `2.1.263`，patch bump，属 known_risks 已预期的「flag 名版本漂移」）。你须独立复核判据 1-3 并在正文写一行结论（「已核对 P0-brief 时效性，无严重漂移；轻微偏移 X 已记录」），不能只抄这段。
- **设计权威源**：需求必须对齐 `docs/design-notes/design-dispatch-routing.md`（终版，两轮外部评审 FAIL→PASS）+ `docs/research/cross-platform-dispatch-mechanics.md`（三平台机制实测 A1-A19 + §10 落地前复核清单 + §11 未尽项）+ 两份外部评审 `docs/reviews/review-dispatch-routing-external-{20260908,round2-20260908}.md`。**注意**：P0-brief §scope「design-note 修订」明确 design-note §2.1/§2.2 与头部**本身就是本任务待修订的交付物**（配置落点自相矛盾等 6 项），所以 design-note 是「设计意图来源」但**不是逐字对齐目标** —— 冲突处以 P0-brief 的 2026-09-09 定案为准。
- **BDD 规格**：每条 `#### BDD-NN:` 标题编号（连续不跳号）+ 单条 Given/When/Then，可二值判定（PASS/FAIL，无中间态）。P0-brief §scope「测试」节已列出必须覆盖的验收面，逐条转 BDD，至少覆盖：
  - schema 校验（`tier`/`effort` 两正交轴 / `tier` vs `candidates` 二选一 / `(phase,role)` key 且 role 可选）
  - 档位→跨 CLI 有序候选链展开 + `effort` 各平台映射（Codex `-c model_reasoning_effort=` / OpenCode `--variant` / **Claude Code CLI 无旋钮 → 静默忽略、不报错、`platform-notes.md` 注明**）
  - 解析顺序 `(phase,role)` → `phase` → 未配 = `standard`
  - 三层配置（① 协议本体档位词表+语义画像+出厂默认 走 SELF-GATE / ② 机器安装级档位→`{cli,model,effort}` 绑定 非版本控制 SETUP scaffold / ③ 项目级 `agate-workspace/dispatch-routing.yaml` `(phase,role)`→档位映射+直接值覆盖）优先级 + 合并语义 + 全兜底（缺失/损坏/类型坏 → 出厂默认 = 现状，不报错不静默跳过，复用 `check-maintainability.py:_load_config` 模式）
  - try-and-fall 逐级回落（**无 probe**）：`launch_fail`（起不来）/ `infra_error`（auth/网络/429/进程崩溃）/ `no_parseable_output`（跑了但无 gate 能评产出）各失败形态 → 逐级回落 → 全落空默认派发（同平台同 model，恒等于本机制未启用）
  - **完整性不变量（最高危，必须有专门 BDD）**：(a) 候选回落**只**在上述三类基础设施信号时发生；(b) 收到任何 gate 能评产出即停止回落；(c) gate 判 FAIL → 走正常阶段 retry（同一候选重跑），**绝不换候选**，gate FAIL 后 `dispatch_route` 事件计数不增；(d) `dispatch_route` 理由码枚举合法值只有 `launch_fail`/`infra_error`/`no_parseable_output`，**不存在 `gate_fail` 值**，由 `check-events.py` 机械拒绝
  - 候选回落 ≠ 状态机 retry：回落不写 `state_transition`、不动 `retries[Pn]`、不触发 PAUSED
  - `dispatch_route` 事件：`gate-events.jsonl` 写入端 + `check-events.py` 校验端认新事件类型（不判为非法未知 event）+ 复用既有哈希链
  - `cli: native` 各平台执行（Claude Code：Task 传 `model`，实测生效 / OpenCode：命名 subagent `agents.<name>.model` 间接路 + phase→预配命名 agent 映射 + 预注册）
  - 跨 CLI 子进程 spawn（`claude -p --output-format json --model X --dangerously-skip-permissions` / `codex exec --json -m X --dangerously-bypass-approvals-and-sandbox` / `opencode run --format json -m provider/model#variant --auto`）+ 结构化输出解析判成败（**Codex 退出码不可靠必须解析事件流**：`turn.completed` vs `turn.failed`，且 item 级 `status: "failed"` 与 `turn.failed` 是两层 —— TAG0033 F1/DEBT0035 教训，须构造真实终态样本）
  - tmux wrapper 生命周期（`which tmux` 成功则 `tmux new-session -d -s {命名空间-task-phase-ts} '{cmd} | tee {capture}'` 否则裸跑；退出倒计时 N≈15 可配；`list-clients` 非空不强杀让倒计时收尾；兜底 `N+余量` 强杀）—— P4c 低优先、可整体切除，BDD 也需标注「不通过不影响 P4a/P4b」
  - **回归证明**：`gate` / `check-gate.py` / `check-state-transition.py` / `phases.yaml` 结构 / 状态机 **零改动**；「不配置 = 逐字节现状」
- **证据强度诚实（外部评审 B1/B2 教训）**：`cli: native` 是**弱缓解**（同厂商换 model 盲区基本共享）；`effort` 轴在 Claude Code CLI **基本是空的**；OpenCode bug②（父会话交互式切 model 后子代理跟不跟）是**机制推断、本会话未直接复现**（P1 前置真机核实项）。BDD / 正文表述**不得把 `[自述]` / 推断混同为「已实测」**。
- **`standard` 语义钉死**：`standard` 档**恒等于「继承主 Agent 当前 model 的原生派发」** —— 否则出厂默认全 `standard` ≠ 现状、破坏「机会式启用」不变量。这条要作为显式需求写死。
- **gate 解耦是设计前提**：gate 只认产出文件 + exit code，**不认「谁生产的」**。需求里要声明 `dispatch-protocol.md` 新节须显式写这句（防未来有人误以为要为跨 CLI 派发定制 gate）。
- **同类扫描（强制节，缺失 requirements-review 打回）**：对关键符号 grep 全仓 —— `dispatch_route`（新事件，主 Agent 已确认当前 0 命中）/ `agate-dispatch.py`（RM-AG0054 已落地，有 `test_tag0027_b2_agate_dispatch.py` 等消费方）/ `check-events.py` 哈希链 / `agate-workspace/maintainability.yaml` + `check-maintainability.py:_load_config`（配置落点先例，命中即参考对象）/ `check-judge-verdict.py`（routed-away judge verdict 定位，P0-brief P4b 列为可能真缺口）/ `phases.yaml` 消费方。记录命中数 + 文件清单 + 逐条「本次处理 / 不处理 + 理由」，结论写进正文（"已确认只此一处"也要显式写）。
- **frontmatter 声明**：
  - `risk_level:` —— P0-brief 定「epic 拆走 Codex 接入后按五维评级 ≈ medium」，建议 `medium`（决定 P2 评审强度），如你判断不同须说明
  - `phases:` —— 本任务触发 SELF-GATE、改协议本体（`dispatch-protocol.md` / `agate-dispatch.py` / `SETUP.md` / `rules/` 档位词表）、`P7` 不可裁，建议 `[P1, P2, P3, P4, P5, P6, P7, P8]`（P4 内部 P4a/P4b/P4c 是 `dispatch_plan` 子批，不是 `phases` 里的独立项）
  - `packages:` / `domains:` —— 按实际受影响面声明（`domains` 无 frontend，主要是 backend/cli 类；agate 协议项目按其惯例取值）
  - `judge:` —— `.state.yaml` 已有 `judge.enabled: true`（P1 created ≥ 2026-08-22 机制强制），无需改，正文提一句「已启用」即可
  - `ceremony:` —— 本任务不适合薄化（改协议本体 + 完整性不变量高危），建议不声明（缺省 standard）或显式 `standard`
  - `dispatch_plan` 是 P2 architect 的产出字段，P1 不写，但需求正文可注明「P2 须声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial}`」
- **capability_requirements**：本任务需真机验证三 CLI（已装已认证 → `available`）；无 frontend/vision 需求。P0-brief P1 前置真机核实项（OpenCode bug② 直接复现测试 / Codex API-key 账号 model 阵容 V8 —— 本机 ChatGPT 账号环境不可得、非阻塞）按能力/环境判断树归类。
- **DEBT0037 预警**：本任务 `dispatch_plan` = static-batch 多提交阶段，P4a/P4b/P4c 分批 commit 会命中 `check-gate.py P4` 完整度判据 → `agate-next.py` 拒绝推进 → 需主 Agent 手动 `_advance`。需求/裁剪说明里注明这个已知手动步（P2 排期预留）。

> 子派发能力：启用（执行角色，按需）—— 若判断需求过于复杂需先侦察再拆，可派侦察 subagent；但 P0-brief 已高度结构化，优先自己完成。

### 上游关联

- 主 Agent 已写 `P0-brief.md`（25779 字节，含 2026-09-09 讨论定案），并已执行 P0→P1 状态跳变（`.state.yaml` phase=P1，`gate-events.jsonl` 已追加 `state_transition` P0→P1，哈希链干净）。
- 前置 TAG0033 / RM-AG0061 已于 2026-09-09 合并 main → v0.70.0（PR #298）：`agate-cmdstream-adapters.py` 含 `CodexAdapter`（`ADAPTERS["codex"]`），P4b `cli: codex` 子进程存活检测直接复用，无排期阻塞。
- TAG0033 复盘三条反馈落 DEBT0037（check-gate P4 多提交阶段判据，**与本任务直接相关**）/ DEBT0038（check-judge-verdict 信息隔离误判）/ DEBT0039（dispatch_plan 批次阶段标注）。
- 基线（HANDOFF §9 声明，主 Agent 未独立重跑全量）：unit 1390 passed + 2 skipped / regression 29 / integration 94 全绿；consistency `--strict-errors-only` 0 ERROR（329 存量 WARNING 为历史叙事文件死链，与本任务无关）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（**P1 主输入**：task / scope / out-of-scope / known_risks / env_constraints / executor_env）
- `docs/design-notes/design-dispatch-routing.md`（设计意图来源；§2.1/§2.2 + 头部是本任务待修订项，冲突以 P0-brief 2026-09-09 定案为准）
- `docs/research/cross-platform-dispatch-mechanics.md`（三平台机制实测 A1-A19 + §10 落地前复核清单 + §11 未尽项状态）
- `docs/reviews/review-dispatch-routing-external-20260908.md` + `docs/reviews/review-dispatch-routing-external-round2-20260908.md`（两轮外部评审，B1/B2 证据强度教训 / W2 tmux 环境代表性）
- `agate-workspace/roadmap/roadmap.md`（RM-AG0060 长描述 —— 旧 `rules/dispatch-routing.yaml` 措辞是本任务连带回写项）
- `agate/WORKFLOW.md`（尤其「需求与验收机制」一节）
- `AGENTS.md`（仓库权威开发指南：repo 布局、编排模型、gate 脚本分层、self-gate checklist、CI、release）
- `agate-workspace/maintainability.yaml` + `agate/scripts/check-maintainability.py`（配置落点先例：项目级、全兜底、非协议本体、不受 SELF-GATE —— 逐字参考）
- `agate/scripts/agate-dispatch.py`（决策 CLI 扩展落点，优先扩它）
- `agate/scripts/check-events.py`（`dispatch_route` 新事件校验端）
- `agate/dispatch-protocol.md`（新增一节的落点：铁律 1 之前的「查表 → 派首选 → 逐级回落 → 再派发」步 + 解耦声明 + 两条完整性不变量）
- `agate/rules/phases.yaml` + `agate/rules/dispatch.yaml`（回归证明「结构零改动」的对照基准；`judge_required_since` 在 dispatch.yaml）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md agate-md-field-set --list` 查看应填字段；逐个 `agate-md-field-set <key> <value>` 写入；失败照错误提示修正，不要手写 frontmatter；仍失败报告主 Agent。写完跑 `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md` 自检（非 0 先修再返回）。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P1

路径：phase-cards/P1-requirements.md
---
# P1 — 需求基线

> 当前状态：[首次 / 重试 #N]
> P1 不可裁剪（核心阶段）

## 如果是首次进入本阶段

1. 派发 analyst subagent → 产出 P1-requirements.md
   1.1 写 P1-dispatch-context-analyst.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 确认：BDD 验收条件 ≥1 条 + 无未决 NEED_CONFIRM
2.5 派发 requirements-review subagent（角色文件：{agate_root}/assets/review-roles/requirements-review.md）
     2.5.1 写 P1-dispatch-context-requirements-review.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
    输入：P1-requirements.md
    产出：P1-review.md（agent≠main，含 BDD 编号引用 + 覆盖维度标注）
    review 不通过 → analyst 修改 → 再 review → … → approved（⑩迭代循环）
3. 预跑 check-gate.py P1（exit 2，主 Agent 自判）
4. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P1，不要提前写 P2——phase = 本 commit 的产出阶段
5. git commit -m "wf({Txxx}-P1): {摘要}"（phase=P1，P1 产出含 P1-requirements.md + P1-review.md）
6. P1 commit 完成后进入 P2：**phase 推进 P2 随 P2 产出 commit 一起**（P2-design.md + P2-review.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（BDD 不完整 / domains 声明错 / NEED_CONFIRM 未处理）
→ review 不通过时：analyst 修改需求 → 重派 requirements-review → 共享 retry 预算
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P1 MAX=3）

## 前置条件

- [ ] P0-brief.md 完成（四字段齐全）

## 派发

- **角色**：analyst（`{agate_root}/assets/execution-roles/analyst.md`）
- **输入**：P0-brief.md（env_constraints / known_risks / executor_env）
- **输出**：P1-requirements.md
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 复杂需求编排（模式 4，条件触发）

需求复杂（多来源 / 多模块 / 无法预先拆清范围）时，P1 可先派**侦察 subagent**（模式 4 先理解后拆，见 dispatch-protocol「派发编排机制」）读全貌后再拆需求：

1. 侦察 subagent 读 P0-brief + 相关上下文，产出拆分方案（拆成哪些子需求、各子需求的输入/产出/依赖）
2. 按方案派 analyst（并行或串行）分别产出需求基线
3. 合并时定义**合并语义**（在侦察产出中声明，P7 一致性检查依赖）：
   - **BDD 全局编号**：各子需求承接的 BDD 编号全局唯一（`#### BDD-NN:`），不允许各子需求各自从 1 编号
   - **包归属去重**：每个 BDD 明确归属唯一包，跨包的共享件单独列出，不允许两个子需求各写一份

## 产出规格

P1-requirements.md 必须包含：
- BDD 验收条件（至少 1 条，Given/When/Then 格式）
- `domains:` 声明（backend / frontend / mcp / security）
- `packages:` 声明（受影响的包/模块）
- `risk_level:` 声明（low / medium / high）→ 决定 P2 评审强度
- `ceremony:` 声明（thin / standard / full）→ 仪式深度档位（可选，缺省 standard，fail-closed：不声明或声明要素不满足一律按 standard 处理，不做薄化）
- `phases:` 裁剪声明（跳过哪些阶段 + 理由）
- `judge:` 启用声明（RM-AG0039 强制）：机制后新任务（P1 `created` ≥ `judge_required_since`，见 `agate/rules/dispatch.yaml`）P1 初始化须在 `.state.yaml` 写 `judge.enabled: true`——check-gate P1 机械校验（缺失/未启用 → exit 1）；历史任务（created < 截止或未声明）缺块 → 跳过
- `capability_requirements:` 能力需求声明（available / supplementable / GAP 三态）
- 无未决 `[NEED_CONFIRM]`（有则 PAUSED）；无待确认项时写 `[NO_NEED_CONFIRM]`

`risk_level`/`phases`/`packages`/`domains` 写在文件头 **frontmatter**（`---` 分隔块），不写正文。
**可直接复制的完整样例**：
```yaml
---
phase: P1
task_id: TAG0001           # 替换为实际任务编号
type: problems
parent: P0-brief.md
trace_id: T001-P1-20260101 # {task_id}-P1-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: analyst
# ── v2.0 机器字段 ──
risk_level: low             # low / medium / high，必填
ceremony: standard          # thin / standard / full，可选；缺省 standard（fail-closed）
phases: [P1, P4, P5, P6, P8]   # list of P\d+，必填
packages: [pkg-a]           # list，必填
domains: [backend, frontend]  # list，必填
# 可选字段：override / implicit_coupling / coupling_checklist / internal_only /
# internal_only_reason / 跳过风险 / design_trivial / follows_existing_pattern
# ── RM-AG0039 judge 启用声明（写在 .state.yaml，非 P1 frontmatter）──
# 机制后新任务（P1 created ≥ judge_required_since，rules/dispatch.yaml "2026-08-22"）必须
# 在 .state.yaml 写 judge.enabled: true——check-gate P1 机械校验，缺失/未启用 → exit 1
# ── v2.0 refactor 任务类型声明（可选，缺省 = 功能任务）──
# change_type: refactor   # 当前仅支持 refactor；枚举非法值由 frontmatter schema 拦截
# ── TAG0007 项目阶段声明（可选，缺省 = established，向后兼容）──
# project_phase: bootstrap   # bootstrap（0→1 新项目）/ established（既有项目，缺省值）；
#                             # bootstrap 时 P2 architect 需额外产出 P2-skeleton.md（骨架声明）
# ── TAG0006 UI/UX 渲染形态声明（可选，presence 语义：缺失 = 常规布局型默认，不红基线）──
# ui_render_shape: render_component   # str，规范形态值：layout（布局型）/ render_component
#                                     # （渲染组件型，仅举例 OpenGL/WebGL/Canvas/图表/模型/特效/
#                                     #  地图/数字地球）/ temporal_effects（时序特效型）；开放集合可扩
# ui_ux_dimensions: [渲染正确性, 动效时序]  # list，从 UX 分类框架选适用维度；渲染组件/时序特效
#                                     # 类形态必填，常规布局型可省略
# ── v2.0 标记"已解决/已确认"状态（可选，仅标记存在时写）──
# need_confirm_resolved: []   # list[str]：已解决的 NEED_CONFIRM 项描述（逐条匹配正文）
# suggest_resolved: []        # list[str]：已采纳的 SUGGEST 项描述
# scope_resolved: []          # list[str]：已解决的 SCOPE+ 项描述
---
```

**UX 类别 BDD 与分类框架（domains 含 frontend 时必做）**：frontend 任务的 P1 必须含至少一条
UX 类别 BDD，并按实际 UI/渲染形态声明 `ui_render_shape` + 从 **UX 分类框架**（布局结构/
渲染正确性/交互行为/动效时序/视觉呈现等示例性开放集合）选 `ui_ux_dimensions` 维度，类别写入
BDD 标题后缀（如 `#### BDD-3: 渲染正确性：...`）。判据必须可量化（渲染正确性 → 渲染结果对比 +
diff 阈值或输出断言；时序 → 帧/时间戳对齐；动效 → 过渡/动画关键帧与结束状态断言；手势交互 →
动作输入的坐标/参数量化），禁主观词。缺失形态声明/维度选择/UX BDD → requirements-review 打回，
P1 gate 在"声明了形态但维度为空"或"维度不在分类框架且未在 BDD 标题声明"时 exit 1。

**人工体验路径验收（强制节）**：任务产出含**用户可见页面**且**页面内容受 seed 数据影响**时，
P1 必须追加一条**人工体验** BDD，句式强制为「Given seed 数据 → 页面有内容」（验证用户按文档 seed 后
页面在人工体验路径下确实渲染出内容）；不得只用 fixture 或单测断言替代人工体验路径验收。

**NEED_CONFIRM 分级**：
- `[SUGGEST: 推荐 X，理由 Y]` - 有倾向但求确认。主 Agent 可自行采纳倾向（除非涉及破坏性变更/业务方向），不必问用户
- `[NEED_CONFIRM]` - 真无方向需人定夺。阻塞推进，主 Agent 问用户

## ceremony fail-closed 声明 checklist（TAG0019，BDD-7/8/9）

`ceremony:` 声明仪式深度档位（thin / standard / full），缺省 standard（fail-closed——不声明或声明要素不满足一律按 standard 处理）。声明 **thin**（薄仪式）时，P1 必须连同以下四要素一起声明，缺一 → check-routing exit 1，档位回退 standard：

1. **申请**：`ceremony: thin` 显式声明
2. **逐信号 checklist**：`coupling_checklist: [...]` 流式声明（判据 `^coupling_checklist:\s*\[`，复用 check-pruning）
3. **跳过风险评估**：`跳过风险:` 声明（复用 check-pruning 判据）
4. **P5/P6 保留**：`phases` 含 P5 与 P6（薄化仪式不薄化验证，P5/P6 由 check-routing / check-pruning 双闸兜底）

不声明（存量/新任务缺 ceremony 字段）→ standard，不拦截。`ceremony: full` 的任务 `phases` 必须含 P7（P7 不可裁，缺失由 requirements-review 审声明拦截，BDD-14）。

### M3 验收锚度量协议（BDD-12，机制文档供提取）

thin 档跳过 LLM 评审的 M3 验收锚四要素：

1. **评审轮数**指标：任务在 P2/P4 阶段派发的 LLM 评审 subagent 轮数（含重试轮）
2. **真实发现数**指标：评审产出中被采纳或阻止了真实问题的条数（排除非阻塞建议、排除机械检查可抓项）
3. **TAG0018 基线值**：4 场 LLM 评审 ≈0 净收益（17 条非阻塞 + 1 条真实发现且机械检查可抓）
4. **不达标决策规则**：「LLM 评审真实发现 ≈ 0 且机械 gate 已覆盖 → 回滚 standard」

## 同类扫描（强制节）

需求基线必须含一次**同类扫描**结论——被报告的那一处几乎从来不是唯一的一处。P0 卡片的「同类/影响面预判」给出粗粒度量级，P1 在此基础上把清单做实：

1. **扫描动作**：对问题涉及的关键符号（函数名、字段名、配置键、协议节标题、错误文案）用 grep/rg 扫全仓，记录**命中数量 + 文件清单**
2. **逐条判定**：每个命中标"本次处理 / 本次不处理 + 理由"。本次不处理的同类实例要么进 roadmap，要么写清为何不构成同一问题
3. **回归拦截**：若同类问题未来还会新增（不是一次性修完的存量），需求里要声明拦截手段（新增测试 / gate 脚本 / 文档约定），并转成对应 BDD
4. **结论落盘**：扫描结论写进 P1-requirements.md 正文（不是只写在 progress 里）；即使结论是"已确认只此一处"也要显式写出，空白不算做过

同类扫描缺失 → requirements-review 打回（"只修被报告的那一处"是 agate 反复复发的反模式）。P2 的「影响面梳理」在本节结论上继续做候选方案级的影响域分析，三处（P0 预判 / P1 同类扫描 / P2 影响面梳理）同源、逐级细化，不重复劳动。

## verification_env vs supplementable 边界判断树

`capability_requirements` 三态（available / supplementable / GAP）和 `verification_env`（运行环境声明）经常被混用——TAG0009 的 11.7 小时就是把一个环境问题错标成 `supplementable` 导致的。P1 声明时按下面的判断树走：

```
先问：缺的是能力还是环境？
├─ 缺的是「agent 侧的能力」（看不见图 / 不会用某工具 / 没有某技能）
│   └─ 走 capability_requirements 三态：
│      ├─ 当前就有 ................................. available
│      ├─ 当前没有，但能通过派发子角色 / 注入 skill / 换工具补上 ... supplementable
│      │   （必须在需求里写清补充方式，否则等同 GAP）
│      └─ 当前没有且补不上 ......................... GAP（阻塞，PAUSED 交人工）
└─ 缺的是「运行环境」（服务没起 / 端口没通 / 数据库没建 / 依赖没装 / 平台不支持）
    └─ 走 verification_env 声明（不是 supplementable）：
       ├─ 环境可由主 Agent 用标准操作准备好 → P1 声明 verification_env，
       │   由主 Agent 按 dispatch-protocol.md「环境准备职责边界」统一准备
       └─ 环境本质不可得（权限/凭据/平台原生不支持）→ 这是不可重试类，
           按 dispatch-protocol.md「verification_env 失败处理协议」立即升级人工
```

**判别口诀**：换个更强的模型/角色就能做 → 能力问题（supplementable）；换谁来做都得先把服务起起来 → 环境问题（verification_env）。**把环境问题标成 `supplementable` 属于机制误用**，不算"环境故障"，不消耗验证轮次预算，应立即改正声明方式。

**环境验证轮次预算占位声明位**：声明了 `verification_env` 的任务，P1 需求里留一行轮次预算占位（默认止损轮次 = 2 轮，与阶段 `retries[Pn]` 独立计数），供 P5/P6 派发时由主 Agent 在 dispatch-context 中接续记录"当前第几轮 + 历次已排除假设"。数值与完整规则的权威定义在 dispatch-protocol.md「verification_env 失败处理协议」，本卡片不重写：

```yaml
verification_env: "debug server http://127.0.0.1:3001 + tests/fixtures/test.db"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

## P0-brief 时效性质疑

analyst 拿到 P0-brief 后不默认它仍然成立——立项与实际启动之间可能已经漂移（跨会话恢复、任务搁置后重启、从 PAUSED 恢复）。P1 阶段必须做一次时效性质疑，判据（严重 3 条 / 轻微 2 条）的权威定义见 P0 卡片「P0-brief 时效性自检（漂移判据）」，本节只定标记规则与处理方式：

**标记格式**（行首声明，一个漂移点一行，必须写出**具体漂移点**，不允许只写标记裸词）：

```
[P0_STALE: executor_env 声明的 CI 镜像已下线，当前实际跑在 ubuntu-24.04]
[P0_STALE: task 描述的 .sh 路线已全量 Python 化，目标方案本身不再成立]
```

**阻塞 / 记录二选一**（按漂移严重程度分流，不允许"既不阻塞也不记录"地含糊推进）：

| 漂移程度 | 处理 | 落盘 |
|---------|------|------|
| **严重**（命中 P0 卡判据 1-3 任一条） | **阻塞**：停止 P1，回 P0 重新立项 / 重做可行性分析 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 说明为何判定严重；主 Agent 按 PAUSED 或回 P0 流程处理 |
| **轻微**（不命中判据 1-3） | **记录**：更新 P0-brief 对应字段后继续 P1，不阻塞 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 已更新哪个字段 |
| 无间隔 / 已核对无漂移 | 继续 | 写一行"已核对 P0-brief 时效性，无漂移"，空白不算做过 |

## gate 规则

check-gate.py P1 → P1-review.md 存在 + status:approved + agent≠main + 含 BDD 编号锚点 → exit 2（BDD 编号格式为 `#### BDD-NN:`）；缺 P1-review.md / agent=main / 无锚点 → exit 1
P1 评审不可裁——所有任务都走独立 requirements-review，无例外

## 推进条件（全部满足才写 phase: P2）

- [ ] P1-requirements.md 含 BDD ≥1 条
- [ ] 含「同类扫描」结论（命中清单 + 逐条处理判定，"只此一处"也要写出）
- [ ] P0-brief 时效性已质疑：无漂移则记录已核对；有漂移则含 `[P0_STALE: 具体漂移点]` 且已按阻塞/记录二选一处理
- [ ] domains / packages / risk_level / phases 已声明
- [ ] 无 [NEED_CONFIRM] 标记
- [ ] 无 status: GAP（supplementable 不阻，GAP 阻）
- [ ] P1-review.md status: approved（agent≠main，含 BDD 编号锚点）

## 常见错误

1. **BDD 写成技术实现而非用户行为**：BDD 应该描述"用户能看到什么/系统应该做什么"，不是"调用哪个 API"
2. **domains 声明不全**：漏了某个受影响域 → P2 不派该域的评审 → 实现方向错误
3. **capability_requirements 漏声明**：P6 验收时才发现需要但不可用的能力 → 返工。**frontend 任务
   漏声明 vision 视觉能力条目（need 含 visual/vision）→ P1 gate exit 1 硬拦**（check-gate.py
   `_gate_p1_vision_capability`）；声明形态但漏选维度 / 形态声明与 UI/渲染形态不符 →
   同样 exit 1
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P2 设计依赖 domains + risk_level 决定评审角色
- P6 验收逐条对照 P1 的 BDD（PASS/FAIL 总数必须 ≥ P1 BDD 总数）
- P7 一致性检查依赖 packages 声明做跨文件交叉核对

## 评审

P1 评审通用必有（所有任务都走 requirements-review），P2/P4 评审是 C8 域触发（见 review-mapping.md）——二者在"是否通用"上不对称，仅在"独立 subagent、agent≠main"上类比。P1 评审不可裁剪。
review 不通过 → analyst 修改需求 → 再 review（⑩迭代循环），直至 approved。

> 完成 → 读 phase-cards/P2-design.md


## P1 基线保护

P1-requirements.md 是需求基线，后续阶段（P2-P8）不应直接修改。如需变更（如 P4 发现 BDD 矛盾需补充注释），必须：
1. 主 Agent 显式批准
2. 在变更处标注 `[BASELINE_CHANGE: 理由]`
3. 不改 BDD 的 Given/When/Then 语义（只补充注释/优先级说明）
4. **隐含扩展同样要授权**（TAG0025 教训）：P3/P4 的实现细节若事实上扩展了 P1 验收标准的范围（新增豁免条件、放宽/收紧某条 BDD 的判定边界等），即使当下未产生"矛盾"，也视为需要`[BASELINE_CHANGE]` 授权的情形——授权内容必须回写 P1-requirements.md 正文，不得只存在于下游阶段的 dispatch-context 口头引用中
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`），工作区 `agate-workspace/`；`.state.yaml` phase=P1 / status=active / judge.enabled=true
- CLI 版本（本机实测）：Claude Code 2.1.266（P0-brief 记 2.1.263）/ codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4；均已装已认证
- 工具链：python 3.12.3（`/usr/bin/python3`）/ pytest 9.0.3 / pyyaml 6.0.1 / ruff `~/.venvs/agate-dev/bin/ruff` / shellcheck
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名，非纯 TAG0034）
- 同类扫描预查（主 Agent 已跑，你须补全并写进正文）：
  - `dispatch_route`（新事件名）：agate/ 下 `.py`/`.md` **0 命中** —— 确为新增，无既有冲突
  - `agate-dispatch.py`：被 `agate/assets/templates/dispatch-context.md` / `check-p6-provenance.py` / `check-judge-verdict.py` / `test_tag0027_b2_agate_dispatch.py` / `test_tag0027_b2_audit2_dual_anchor.py` 等引用 —— 扩展不得破坏既有 dispatch-context 渲染路径
  - `agate-workspace/maintainability.yaml` 存在；`check-maintainability.py:_load_config`（line 88）为全兜底加载先例
  - `agate/rules/` 现有：`dispatch.yaml` / `phases.yaml` / `review-mapping.md` / `roles.yaml` / `state-transitions.md` / `schema/`
- 设计文档字节数：design-note 39769 / research 38501 / 外部评审 8864（round1）
- 基线绿信息来源：HANDOFF-TAG0034.md §9（committed 交接单声明，主 Agent 本会话未独立重跑全量）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
