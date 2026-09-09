---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: architect
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

产出 `P2-design.md` —— TAG0034 派发路由的方案设计：把 P1 的 53 条 BDD + 6 条已采纳 SUGGEST + 3 处「P2 定」留白，落成可实现的技术方案。**候选方案 ≥2 + 权衡 + 选择理由**（`candidate_count` 必填）；**影响面梳理节写在候选方案之前**（改什么 / 不改什么 / 风险在哪，基于 P1 §3 同类扫描 9 组逐级细化）；frontmatter 四字段（`packages` / `domains` / `ui_affected: false` / `gate_commands`）+ `dispatch_plan`；正文 `files_to_read` / `env_constraints` / `minimal_validation`。

### 约束

**A. 范围锁定（P0-brief 核心约束 6）**：方案不得超出 `P0-brief.md` 的 scope / out-of-scope。若设计中发现必须超范围，**停下、在 P2-design.md 行首写 `[NEED_CONFIRM: 具体超范围点]` 报告主 Agent**。P1 的 `[SCOPE+ from user-approval：DEBT0039 并入]` 是已批准的既有范围，不算超范围。

**B. P1 已采纳的 6 条 SUGGEST 是设计输入（frontmatter `suggest_resolved`），按它们设计、不要推翻**：
1. `tier` 三档命名 = `bulk` / `standard` / `deep`
2. `{cli: native, model: null}` 合法，`null` = 该 CLI 当前默认 model
3. MVP 单文件：协议本体档位词表①与项目级映射③合并为一个 YAML 文件 + 内联档位定义；机器级绑定②是否拆出独立文件 **由你 P2 判定**（判据：团队/多机可移植性是否真需求；倾向 MVP 不拆，但要给出判据和结论）
4. 三层配置优先级序 = 项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认
5. 决策落点 = 扩 `agate/scripts/agate-dispatch.py` 新增子命令（如 `agate dispatch route <phase> <role>`），与 RM-AG0054 已落地的 `agate dispatch`（渲染 dispatch-context）**串联为两步、不合并**；不新增 `agate-route.py`
6. routing schema 静态校验器 = 新增独立脚本 `agate/scripts/check-dispatch-routing.py`，不入 `agate/rules/schema` 协议 schema 体系；挂载时机由你 P2 定（倾向 SELF-GATE 链 + 可选 pre-commit）

**C. 必须在 P2 定死的 3 处「P2 定」留白**（P1 BDD 显式留给你，不定死会导致 P4/P6 缺锚点）：
- **BDD-15 / BDD-18**：三层配置的**精确合并语义** —— ① 完整优先级解析算法（含 role 层可选：`(phase,role)` → `phase` → `standard`）；② 机器级绑定出现同名档位键时取谁（后写覆盖先写 / 报 schema 错 —— 你选一个并写死）；③ 「机器级绑定与项目级映射冲突时取值确定」的具体规则，保证结果唯一、无运行时「取谁含糊」分支
- **BDD-35**：Codex `--json` 判成败时，`turn.failed` 与 item 级 `payload.item.status == "failed"` **取哪一层** —— 明确「turn 层为准 / item 层为准 / 两层如何叠加」，并说明与「Codex 退出码不可靠」如何共同作用得出稳定结论。**必须用真机构造的样本佐证**（见 minimal_validation）
- BDD-38：tmux wrapper 强杀兜底的「`N + 余量`」中**余量取具体秒数**（P1 建议 ≥10s，你定值）

**D. minimal_validation 必做（P1 §6 `requires_minimal_validation: true`）**：本方案重度依赖三平台外部行为，**不接受「纯代码逻辑」声明**。必须真机构造并记录以下终态样本（TAG0033 F1 / DEBT0035 教训：不能只读已有会话，要主动构造）：
- 三 CLI 各自的 **spawn + 结构化输出解析** 样本：Claude Code `claude -p --output-format json --model haiku --dangerously-skip-permissions`（正常 `stop_reason`）；Codex `codex exec --json -m <model> --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox`（正常 `turn.completed` + **构造一个 exit 0 但 `turn.failed` 的失败样本**，如不支持的 model）；OpenCode `opencode run --format json --auto`（正常 `step_finish.part.reason` + **构造失效 provider 的空返回样本**）
- Codex item 级 `status: "failed"` 样本（带 `exit_code`）与 turn 级 `turn.failed` 的区别（BDD-35 的实据）
- **OpenCode 旧 bug② 直接复现**（P1 前置真机核实项、外部评审 B2 教训）：配一个命名 agent → 父会话交互式切 model → 再派该 agent → 核对子代理实际跑的是配置 model 还是父的新 model。结论写进 P2-design.md，**如实标注实测 vs 推断**——不得把推断写成「已实测」。research §5.2 / §10 有具体步骤。
- `cli: native` on Claude Code 传 `model` 生效（Task 单次调用 / `claude -p --model`），`modelUsage` 字段可核实实际 model
- flag 名落地前照 `docs/research/cross-platform-dispatch-mechanics.md` §10 逐平台对最新官方文档复核（本机 Claude Code 已到 **2.1.266**，P0-brief 记 2.1.263）
- 所有命令加 shell 层 `timeout`，真机调用前在 progress 逐条落盘（要跑什么、预期多久）

**E. dispatch_plan 必声明**（P1 §7 强制）：`dispatch_plan: {mode: static-batch, batches: [{id: P4a, complexity: ...}, {id: P4b, complexity: ...}, {id: P4c, complexity: ...}], serial}`（P4a→P4b→P4c 串行依赖链，非并行）。每批 `complexity` 按「派发编排机制」工作量五维评估填。P4a = 配置路由核心 + `cli: native` + `dispatch_route` 事件 + 协议本体档位词表 + `dispatch-protocol.md` 新节；P4b = 跨 CLI 子进程 + 结构化输出解析 + routed-away judge 核实 + 续跑；P4c = tmux 观测层（低优先、可整体切除、不通过不影响 P4a/P4b）。**在「批次设计」节明确：DEBT0039 的两处纯文档修订（`architect.md`「批次设计」节 + `dispatch-protocol.md`「派发编排机制」节）= P4 author 工作，随对应批提交**（不是 P7）。

**F. DEBT0039 边界措辞（P1 §4.17 BDD-48/49/50，SCOPE+ 用户批准并入）**：在 P2-design.md 里**起草**两处纯文档的边界澄清措辞（P4 照此落地）：
- `agate/assets/execution-roles/architect.md`「批次设计（强制节，TAG0014）」节：加一句显式边界 —— 「补协议文档正文（`platform-notes.md` / `SETUP.md` / phase-cards 等）= P4 实现工作，批次执行阶段标 P4；P7 只做跨文件一致性验证、不 author 文档内容」
- `agate/dispatch-protocol.md`「派发编排机制」节：加一句显式区分 —— 「author 文档内容 = P4 / 跨文件一致性验证 = P7」
- 可引用两个先例（DEBT0039 evidence 指针）：TAG0030（doc-assertion 审计 P3 写红、正文 P4 补绿）+ TAG0033 复盘（protocol-docs 批被 architect 误标 P7、主 Agent 拉回 P4）
- **边界约束**：只做这两处措辞澄清，不扩到其它 DEBT、不改任何脚本 / gate 逻辑

**G. 回归硬约束（设计前提，known_risk 最高危）**：方案**不改** `check-gate.py` / `check-state-transition.py` / `phases.yaml` 结构 / 状态机。档位词表放 `agate/rules/` 下**新文件**（不扩 `phases.yaml` 字段）。`dispatch-protocol.md` 新节须写死「gate 只认产出文件 + exit code、不认谁生产的」。**模型购物完整性洞（最高危）**：设计里必须体现 —— 候选回落**只**在 `launch_fail` / `infra_error` / `no_parseable_output` 三类基础设施信号时发生；收到任何 gate 能评产出即停止回落；gate FAIL → 同一候选正常阶段 retry，绝不换候选；`dispatch_route` 理由码枚举**无 `gate_fail` 值**，由 `check-events.py` 机械拒绝。方案要说明 `check-events.py` 如何扩展识别新事件 + 理由码枚举校验，且**不动既有哈希链算法 / 不动第 1-6 条既有审计链**。

**H. SELF-GATE 面梳理（供 P4/P7 commit 规划）**：在影响面梳理或 env_constraints 里列出本任务触发 SELF-GATE 的文件面（`agate/dispatch-protocol.md` / `agate/scripts/agate-dispatch.py` / 可能 `agate/scripts/check-events.py` / 新增 `agate/scripts/check-dispatch-routing.py` / `agate/SETUP.md` / `agate/rules/` 档位词表新文件 / `agate/assets/execution-roles/architect.md` / `agate/tests/`），并注明：P4/P7 涉及 `agate/**` 的 commit 前主 Agent 须派 `protocol-alignment-review`（A1-A7），commit message 含 `self-gate-review:` / `self-gate-skip:`。`agate-workspace/dispatch-routing.yaml` + 机器级绑定文件新增**不触发** SELF-GATE（非协议本体，同 `maintainability.yaml`）。

**I. DEBT0037 预警**：`dispatch_plan` = static-batch 多提交阶段，P4a/P4b/P4c 分批 commit 会命中 `check-gate.py P4` 完整度判据 → `agate-next.py` 拒绝推进 → 需主 Agent 手动 `_advance` + 补 `state_transition` 事件。在批次设计节 / env_constraints 注明这个已知手动步（排期预留）。

**J. gate_commands 声明**（P2 固化，P4-P6 不能改）。至少覆盖：`P3`（测试运行器，`python3 -m pytest`）；`P5`（`python3 -m pytest agate/tests/ -q --tb=no` 或分片）；`P5_consistency`（`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`，用 worktree 自己的脚本）；`P5_events`（`python3 agate/scripts/check-events.py <TASK_DIR>/gate-events.jsonl`）；`P5_shellcheck`（若改 `.sh`，本任务大概率不改也可结构性声明）。**不要用 `&&` 串接**（短路反模式）—— 每个校验独立 key。按类型声明 `{key}_timeout_seconds`（单元测试类 ~120s；本任务全量分片可更长）。`ui_affected: false` → 不需要 `P5_e2e`。

**K. 决策 CLI 衔接细节**（P0-brief scope）：
- `agate dispatch route <phase> <role>` 与 RM-AG0054 `agate dispatch`（渲染 dispatch-context）串联方式：会话侧读什么文件、怎么保证「零判断」（`cli: native` 的「决策层算目标 model → 启动仍由驱动会话代发」衔接）
- retry / 回退路由：BDD-26（同阶段 gate-FAIL retry = 同一候选，不重解析）vs BDD-51（P5→P4 跨阶段回退 = 机械重新解析一次 `(phase,role)` 路由，无「升档」逻辑）—— 方案要让这两条在实现上互不干扰
- 与既有派发交互：BDD-43（五模式并行批，每个并行 subagent 各自独立解析路由）/ BDD-44（RM-AG0055 自主再派发不走路由表、继承父的 cli/model）/ BDD-45（单 Agent 模式 `has_task_tool:false` 路由 no-op、显式声明出范围）

**L. files_to_read**：给 P4 implementer 的精准清单（标行号范围的只读片段），不要列全仓。

**M. design-note / roadmap 修订（本任务交付物，BDD-46/47/52/53）**：P2 方案要包含 `docs/design-notes/design-dispatch-routing.md` 头部 + §2.1/§2.2 的修订要点（6 项：三层落点 / try-and-fall / 两轴 + `(phase,role)` key / 弱强缓解 + 自动化不对称 / 两条完整性不变量 / per-machine 机会式）+ `roadmap.md` RM-AG0060 长描述旧措辞回写。走 docs commit（非 SELF-GATE）。

**格式**：约束节 / 正文避免行首 `- PASS` / `- FAIL`（provenance 预判检测）。

> 子派发能力：启用（执行角色，按需）—— minimal_validation 的三平台真机构造工作量大，若判断需拆可派子任务；但优先自己完成，真机调用逐条 progress 落盘。

### 上游关联

- P1 已 commit（`f75e129`，phase 仍 P1，phase→P2 随本 P2 产出 commit 一起推进）：`P1-requirements.md` 53 条 BDD（连续 1~53）、`[NO_NEED_CONFIRM]`、`suggest_resolved` 6 条、requirements-review approved（retry #1 后）。
- P1 frontmatter：`risk_level: medium` / `ceremony: standard` / `phases: [P1..P8]` 全走 / `packages: [agate-scripts, agate-rules, agate-docs, agate-tests]` / `domains: [backend, cli]` / `judge.enabled: true`。
- C8 评审映射（P2）：`domain: backend + risk_level: any → plan-eng-review`（P2 方案评审，单评审角色，直接派发无组长）。`cli` 域不在 C8 表内（表外，你在设计里覆盖）。非 high / 非 full / 无业务 NEED_CONFIRM → 不触发 plan-ceo-review / cso。
- 前置 TAG0033 已合并 v0.70.0：`agate/scripts/agate-cmdstream-adapters.py` 含 `CodexAdapter`（`class` line 666 / `ADAPTERS["codex"]` line 878），P4b `cli: codex` 子进程存活检测直接复用。
- `check-events.py` 第 7 条：未知 event 类型不拦截（向后兼容）→ `dispatch_route` 不会被判「非法未知 event」，但理由码枚举校验 + 机械拒绝 `gate_fail` 是**必须新增的扩展**。
- `check-judge-verdict.py` / `check-p6-provenance.py` 经 P1 requirements-review 独立 grep 核实：纯 `TASK_DIR` 文件解析、不读平台 transcript → routed-away judge verdict **非真缺口**（BDD-42 作回归断言）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（**P2 主输入**：53 BDD + frontmatter + §3 同类扫描 9 组 + §5 suggest_resolved + §6 minimal_validation 要求 + §7 裁剪/DEBT0037/DEBT0039）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（task / scope / out-of-scope / known_risks 12 条 / env_constraints）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-review.md`（requirements-review 的逐条 BDD 判定 + 复核轮结论，理解每条 BDD 的验收意图）
- `docs/design-notes/design-dispatch-routing.md`（设计意图来源；§2.1/§2.2 + 头部是本任务待修订交付物，冲突以 P0-brief 2026-09-09 定案为准）
- `docs/research/cross-platform-dispatch-mechanics.md`（三平台机制 A1-A19 实测 + §5 子代理派发 + §6 存活检测 + §10 落地前复核清单 + §11 未尽项）
- `docs/reviews/review-dispatch-routing-external-20260908.md` + `docs/reviews/review-dispatch-routing-external-round2-20260908.md`（B1/B2 证据强度 / W2 tmux 环境代表性）
- `agate-workspace/maintainability.yaml` + `agate/scripts/check-maintainability.py`（`_load_config` line 88-148：全兜底加载先例，逐字参考 —— `dispatch-routing.yaml` 加载器照此）
- `agate/scripts/agate-dispatch.py`（决策 CLI 扩展落点，读懂既有 dispatch-context 渲染路径 + `generated_by` / CARD-SOURCE 锚点，不得破坏）
- `agate/scripts/check-events.py`（`dispatch_route` 新事件校验端 + 哈希链，读懂第 1-7 条审计链）
- `agate/scripts/agate-cmdstream-adapters.py`（`CodexAdapter` / `ADAPTERS`，P4b 子进程存活检测复用）
- `agate/dispatch-protocol.md`（「派发编排机制」节 line 502 起 = 新节落点 + DEBT0039 BDD-49 落点；「铁律 1」位置）
- `agate/assets/execution-roles/architect.md`（你的角色定义；「批次设计」节 line 209 起 = DEBT0039 BDD-48 落点；「minimal_validation」「dispatch_plan」相关节）
- `agate/rules/phases.yaml` + `agate/rules/dispatch.yaml`（回归对照基准「结构零改动」）
- `agate-workspace/debt/tech-debt.md`（DEBT0039 条目 + `closure_criteria` + evidence 指针 TAG0030 / TAG0033；`task_id` 现为空）
- `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md`（TAG0033 复盘 §一 `spawn_agent` 实测 + F1/DEBT0035 终态样本教训 + DEBT0039 来源）
- `agate/platform-notes.md`（三平台能力差异章：Codex `spawn_agent` schema 实测记录、effort flag 现状；BDD-10 的 Claude Code effort 注明落点）
- `agate/SETUP.md`（机器级档位绑定文件 scaffold 接入点，比照「步骤 2-Codex」per-platform onboarding）
- `AGENTS.md`（仓库权威：gate 脚本分层、SELF-GATE、双工作区纪律、CI、`--strict-errors-only` 定义）
- `agate/WORKFLOW.md`（「派发编排机制」工作量五维评估，dispatch_plan complexity 依据）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md agate-md-field-set --list` 查看应填字段；逐个 `agate-md-field-set <key> <value>` 写入（`candidate_count` / `packages` / `domains` / `ui_affected` 必填）；`dispatch_plan` 若 `agate-md-field-set` 不支持则按合法单行 flow YAML 手工加进 frontmatter 并用 `check-frontmatter.py` 验证。写完跑 `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（exit 0），非 0 先修再返回。
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
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P1（P1 已 commit `f75e129`）/ status=active / judge.enabled=true
- CLI 版本（本机实测）：Claude Code **2.1.266**（P0-brief 记 2.1.263）/ codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4；均已装已认证
- 工具链：python 3.12.3（`/usr/bin/python3`）/ pytest 9.0.3 / pyyaml 6.0.1 / ruff `~/.venvs/agate-dev/bin/ruff` / shellcheck
- 三 CLI 真机冒烟（P0-brief §4 已列）：
  `claude -p --output-format json --model haiku --dangerously-skip-permissions <<< "ok"`
  `codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "ok"`
  `opencode run --format json --auto <<< "ok"`
- 关键锚点：`agate-dispatch.py` 存在且当前仅渲染 dispatch-context（RM-AG0054）；`dispatch_route` 全仓 0 命中（新事件）；`check-maintainability.py:_load_config` line 88；`CodexAdapter` line 666 / `ADAPTERS["codex"]` line 878；`architect.md`「批次设计」节 line 209；`dispatch-protocol.md`「派发编排机制」节 line 502
- C8 评审（P2）：plan-eng-review 单角色（backend + any），直接派发无组长
- SELF-GATE：`protocol-alignment-review`（phases: pre-commit，insert_after P7）—— 改 `agate/**` 的 commit 前由主 Agent 派发；P2 只产任务目录 md，本次 P2 commit 不触发
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- 基线绿来源：HANDOFF §9（unit 1390+2skip / regression 29 / integration 94 / consistency 0 ERROR）—— 主 Agent 本会话未独立重跑全量
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
