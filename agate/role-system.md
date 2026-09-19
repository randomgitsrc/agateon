# 双层角色体系

> agate，解决"角色库只有评审角色、没有执行角色、不支持自定义"的问题

---

## 为什么分两层

agate 的角色体系把角色分成两层：

```
执行角色（execution-roles）   ← 各阶段干活的，subagent 执行用
评审角色（review-roles）       ← 审查执行产出的，从 gstack 提取
```

加上**自定义角色模板**，让用户能按任务定义专门角色。

---

## 第一层：执行角色（assets/execution-roles/）

负责各阶段的实际产出。每个对应 P1-P8 的某些阶段：

| 角色 | 文件 | 负责阶段 | 职责 |
|------|------|----------|------|
| 需求分析师 | analyst.md | P1 | 需求质疑、建立 BDD 基线 |
| 方案设计师 | architect.md | P2、P7 | 写设计方案、一致性检查 |
| 测试设计师 | test-designer.md | P3 | 写测试用例和测试代码（TDD 红灯）|
| 实现工程师 | implementer.md | P4、P8 | 写代码、多包发布准备 |
| 验证工程师 | verifier.md | P5、P6 | P5 技术验证、P6 BDD 验收 |
| 视觉结构分析师 | vision-analyst.md | P6（按需）| UI 截图翻译成结构化 YAML，供 P6 验收和 design-review 使用 |

这些是 agate 新增的，gstack 里没有。

> **UI 设计节由 architect 兼任产出**（P2，`ui_affected: true` 时 P2-design.md 必含），**不新增 designer 角色**——保持角色清单最小化，UI 设计节的责任压在 architect 的 P2 产出规格上，由 P2 gate 校验。视觉分析仍由 vision-analyst 在 P6 按需承担（P1 声明 vision 能力 available/supplementable 时真实分析，GAP 时走降级链）。

## 第二层：评审角色（assets/review-roles/）

从 gstack 提取，负责审查执行角色的产出。在关键阶段插入：

| 角色 | 文件 | 插入阶段 | 审什么 |
|------|------|----------|--------|
| 偏执 Staff Engineer | review.md | P4 后 | 生产级 bug |
| 创始人/CEO | plan-ceo-review.md | P2 | 方向对不对 |
| 工程经理 | plan-eng-review.md | P2 | 架构对不对 |
| 高级设计师+前端 | design-review.md | P4 后（前端）| UI 问题 |
| 设计评审（计划阶段）| plan-design-review.md | P2（前端）| spec 交互完整性 + 交互状态覆盖 + 视觉设计 + 渲染形态适配（形态分组：布局型三组 = 布局/交互/视觉——交互状态覆盖/交互设计细节/可访问性/移动端/组件完整性/AI Slop/视觉设计；渲染组件型/时序特效型 = 渲染正确性与时序 + 动效时序）|
| QA 工程师 | qa.md | P5 | 功能跑通、找 bug |
| 调试专家 | investigate.md | 任意（出 bug 时）| 根因 |
| 安全官 | cso.md | P4 后（涉敏感）| 安全审计 |
| 验收独立裁判 | judge.md | P6.5（**所有任务强制**）| fresh context 逐条重验全部 BDD（含已 PASS 项，零挑验），只信证据与 git log，防 self-authored gate 锚定（TAG0020）|

### 评审角色机械映射（C8 — 不靠主 Agent 临场判断）

P1 在 requirements.md 声明 `domains:` 和 `risk_level:`，主 Agent **机械映射**评审角色，不靠"我觉得需要谁"：

| domain | risk_level | 自动触发的评审角色 |
|--------|------------|-------------------|
| backend | 任意 | plan-eng-review（P2 方案评审）+ review（P4 后）|
| frontend | 任意 | design-review（P4 后）+ plan-design-review（P2）|
| mcp | 任意 | review + 关注 MCP 接口契约（T005 教训：MCP 改动需专项评审）|
| security | 任意 | cso（P4 后）|
| 任意 | **high** | **plan-eng-review 必须派发**（P2.1 硬规则，check-gate.py 对 agent=main 硬拦截 exit 1）|
| 任意 | **full**（算分 tier=full 或声明 `ceremony: full`）| **plan-eng-review 必须派发**（P2，对齐 risk_level=high 硬规则）+ **cso**（security 域）+ **P7 不可裁**（full 档任务 P7 为强制阶段，去重规则同本表）|
| P1-requirements.md 含 [NEED_CONFIRM] 且涉及业务方向 | 任意 | plan-ceo-review（P1 后 / P2）|

**去重说明**：同一任务命中多行且触发同一评审角色时，去重只派发一次（如 backend + high 均命中 plan-eng-review，只派 1 个 plan-eng-review，不重复派发）。**full 档（tier=full 或 `ceremony: full`）与 risk_level=high 命中同一角色时同样只派 1 次**。

T005 漏 MCP 评审的根因：靠主 Agent 临场判断，它没有 MCP 评审意识。机械映射消除这个盲区。

**Hardening 对 mapping 表的影响**：
- **`risk_level: high` 是新增触发维度**——P2 review 必须派发独立 plan-eng-review，不再允许主 Agent 自己跑
- `agent:` 字段协作规范：所有评审产出文件（P2-review.md 等）Header 含 `agent: plan-eng-review` 等——主 Agent 在派发 prompt Header 里填好，subagent 复制即可
- 高频评审角色（hardening 后）排序变化：`plan-eng-review` 和 `cso` 因为 risk=high + security/权限触发率上升成为最高频

---

## 角色如何被使用

### 执行角色：派发 subagent 时注入

主 Agent 派发 subagent 时，在 prompt 里指定角色定义文件（**实际派发使用 `assets/templates/dispatch-prompt.md` 完整模板**——含分阶段落盘、环境隔离、PROD_TOUCHED（二值声明格式）、dispatch-context、阶段特定提示等。本节只展示最简骨架）：

```
你是 P2 阶段的 architect 子 Agent。
角色定义：读取 {agate_root}/assets/execution-roles/architect.md
并严格遵循其中的认知模式、输入输出规范、质量门槛。
```

subagent 读取角色文件，按角色定义的方式工作。

### 评审角色：在阶段门槛处插入

某些阶段产出后，主 Agent 派发一个评审 subagent：

```
你是 plan-eng-review 评审角色。
角色定义：读取 {agate_root}/assets/review-roles/plan-eng-review.md
评审对象：{AGATE_WORKSPACE}/tasks/{Txxx}/P2-design.md
产出：{AGATE_WORKSPACE}/tasks/{Txxx}/P2-review.md，Header 里 status 字段填 approved/rejected
```

评审产出的 `status` 字段就是门槛判定的依据。

### 门槛评审必须统一产出 status 字段

任何作为**阶段门槛**的评审角色，产出文件 Header 必须含统一的 `status` 字段，否则主 Agent 无法判定门槛。

评审角色的"结论"统一映射到 status：

| 评审角色的结论 | 映射到 status |
|----------------|---------------|
| 确认 / 通过 / PASS / approved | `approved` |
| 转向 / 打回 / HOLD / 有 BLOCKER / rejected | `rejected` |
| 需补充 / needs revision | `needs-revision`（计入重试）|

例如 plan-ceo-review 的结论是"转向"，映射为 `status: rejected`；plan-eng-review 的"approved"直接就是 `status: approved`。无论用哪个评审角色做门槛，主 Agent 都只读 `status` 字段判定，不需要理解各角色的具体结论语义。

**judge（P6.5）verdict 三值复用同一映射**（TAG0020）：`passed → approved`（P6→P7 放行）/ `needs-revision → needs-revision`（弹回 P6 重验，judge 轮次 +1）/ `rejected → rejected`（弹回 P6 或交人工）。judge 是**所有任务强制**的常态门槛评审（插入点固定为 P6 之后），**不进 C8 机械映射表**——C8 按 domain/risk 触发，与"强制所有任务"语义不同。

**非门槛评审**（如纯参考的方向建议）不强制 status，但也不参与门槛判定。

---

## 第三层（机制）：自定义角色

用户可以为特定任务定义专门角色，不必都套用通用角色。

### 自定义角色模板

见 `assets/templates/custom-role.md`（权威来源，含分阶段落盘 / dispatch-context / PROD_TOUCHED（二值声明格式）等现代角色必备节）。

本文件不重复模板内容，自定义角色按 custom-role.md 结构填写即可。

### 自定义角色怎么用

1. 按模板写一个 `assets/execution-roles/{role_id}.md` 或 `review-roles/{role_id}.md`
2. 平台注册（平台适配实现注记）：在有平台自定义 agent 机制时，把对应的 markdown 放到平台的 agent 目录（如 OpenCode/Claude Code 的 agent 目录），让平台能识别；无该机制时跳过此步，直接用下方方法 B
3. 派发时指定这个角色文件路径

> 实现注记：以上第 2 步属平台注册的适配说明（自定义 agent 的发现机制各平台不同），非协议语义定义——角色如何被平台识别是平台实现细节；协议层的角色机制语义见「第三层（机制）：自定义角色」开头两节与 custom-role.md。

### 自定义角色的平台坑位

> 实现注记：本节为平台自定义 agent 机制的坑位与规避说明（记录 OpenCode issue #29616 实测），属平台适配实现注记，非协议语义定义；平台无关的通用角色派发语义见「角色选择决策」与 dispatch-protocol.md。

⚠️ 平台坑位：某些平台以 jsonc/声明方式定义的自定义 subagent 可能无法被派发工具调起来（如 OpenCode 的 `opencode.jsonc` 里 `mode: "subagent"` 定义的自定义 agent，issue #29616）。

**规避方法（二选一）：**
- **方法 A**：用 markdown 文件方式定义（放平台 agent 目录，文件名即角色名），比 jsonc 可靠
- **方法 B（退路）**：用内置的 general subagent，把自定义角色定义文件的路径写进派发 prompt，让 general subagent 读取并遵循。角色行为靠 prompt 注入实现，不依赖平台的自定义 subagent 机制。

方法 B 是最稳的——它不依赖任何平台特性，只要平台能派发一个通用 subagent + 让它读文件就行。**推荐优先用方法 B**，因为它跨平台、不踩坑。

---

## 角色选择决策

主 Agent 按阶段自动选执行角色（固定映射，见 WORKFLOW.md 阶段总览）。评审角色的选择：

```
P2 方案设计后：
  - 涉及架构/技术方案 → plan-eng-review
  - 涉及产品方向/要不要做 → plan-ceo-review
  - 涉及前端 UI → 加 plan-design-review

P4 实现后：
  - 默认 → review（找 bug）
  - 涉及前端 → 加 design-review
  - 涉及认证/输入/敏感数据 → 加 cso

出现无法解释的 bug → investigate
```

主 Agent 根据任务内容判断需要哪些评审角色，可以串联多个。

### 专家组并行评审 + 组长汇总

P2 评审可同时派发多个评审角色（并行）：

```
主 Agent 同时派发 N 个评审（多个 task 调用）：
├── plan-eng-review   → P2-review-eng.md
├── plan-ceo-review   → P2-review-ceo.md
├── plan-design-review（前端任务时）→ P2-review-design.md
└── cso（涉安全时）   → P2-review-cso.md
```

所有评审返回后，派发组长汇总：
- 角色：review 角色 + 指定为「专家组组长」
- 输入：所有评审文件路径
- 任务：汇总、去重、归类（BLOCKER/建议/可忽略）、标注分歧
- 输出：P2-review.md（统一 status: approved/rejected）

**组长规则**：
- 组长不发表新意见，只汇总
- 任何专家标 BLOCKER → status: rejected
- 多位专家分歧 → 标「专家组分歧」交人工
- 全票无 BLOCKER → status: approved

P4 后评审同理（review + cso + design-review 并行）。

---

## 审查锚点：角色文件是否浅化接口（Deep Modules，TAG0036）

**审查对象**：角色文件（`assets/execution-roles/`、`assets/review-roles/`）与阶段卡片（`phase-cards/`）。

**核心问题**：是否把"实现细节"写进了"接口"——即**浅化**。一个深的模块用窄接口隐藏丰富实现；角色文件的"接口"是它对调用方承诺的输入、输出与判据，"实现"是子 Agent 自主完成的做法。把做法写进接口，接口就变浅：调用方被迫理解细节，子 Agent 失去自主决定实现的空间。

**判据**：审查角色文件或阶段卡片时问——是否规定了"第 1 步做 A、第 2 步做 B"式**执行顺序**？协议哲学是给**资源地图**（去哪里找上下文、读哪些文件）加**判据**（做到什么算完成），不给步骤脚本。出现执行顺序脚本即视为浅化信号，审查意见应建议改写为"资源地图 + 判据"。固定的流程性动作（如按序落盘、先红后绿）若属阶段间的协议约束而非某角色的实现做法，不在此列。

**与批切分判据的关系**：本锚点关注"单个角色文件/卡片的接口深浅"，与 `architect.md` 中的批切分判据（关注"批如何切"）**正交**，不可互相替代——批切得好不代表角色文件没有浅化，反之亦然。

**范围声明**：本节仅为审查视角的成文，不改动既有角色文件的行为约定，也不新增机械检查；其实际效果尚未做任何验证，不作有效性宣称。

---

## 子派发权限边界

> RM-AG0055（TAG0028）受控自主再派发：执行角色在授权范围内可自主派发子任务
> （子 subagent）。本节定义权限边界与例外；与五模式编排的关系、产出收敛语义见
> dispatch-protocol.md「subagent 自主再派发」节。

- **可被授予子派发权限的角色**：执行角色（analyst / architect / implementer / verifier）——
  在任务进行中需要局部拆解工作时，可被主 Agent 授予子派发能力（派发子任务 subagent）
- **硬边界 1（不写状态）**：子任务**不写** `.state.yaml` / `active-tasks.md`，不产生独立
  phase 状态——外部观感永远是"一个 subagent 在跑"，父汇总后仅以"路径+摘要"回报；
  子任务中间产出不计入 gate 判定对象（产出收敛见 dispatch-protocol.md）
- **硬边界 2（写权限严格子集）**：子任务写权限是**父权限的严格子集**——子任务只能触碰
  父在派子任务 prompt 中显式约束的目录内文件；权限**不自动继承**，父在派子任务 prompt
  中显式重申约束
- **judge 类角色例外**：judge 类角色（验收独立裁判，fresh context 信息隔离）**不适用
  子派发**——子派发决策路径本身是 judge 主观认知过程，开放子派发会破坏 fresh context
  信息隔离防线（信息隔离冲突，设计 §4.4）。judge 角色**不开放** Agent/subagent_fork
  工具权限；派发 judge 时在 dispatch-context 显式声明「不启用子派发能力」（模板声明位
  见 assets/templates/dispatch-context.md，M7）

---

## 与 gstack 的关系

review-roles 的角色原型（Staff Engineer / CEO / Engineering Manager / Senior Designer / QA / CSO / Debug Expert）受 gstack（Garry Tan 开源，MIT）的概念启发。agate 以独立的执行/评审分离模型重写了这些角色，**未捆绑、复制或链接 gstack 代码**——角色定义内容为 agate 独立创作。保留致谢而非捆绑代码的原因：

1. **自包含**：agate 不依赖外部文档，所有资产在 assets/ 下
2. **可定制**：角色定义按项目需要调整
3. **稳定**：外部仓库可能变动，独立实现不受影响

概念启发致谢：`NOTICES.md`（Inspirations 区）。

---

*角色定义文件在 assets/ 下，配合 dispatch-protocol.md 使用*
