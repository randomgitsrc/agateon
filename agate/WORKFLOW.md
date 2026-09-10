# agate — 子 Agent 编排工作流

> 职责边界：主流程入口——P0-P8 阶段总览、裁剪规则、核心原则、需求/验收机制骨架（详见职责声明表，P2-design.md §0）

> 实现注记：文档头部为文档元信息——「适用平台范围」声明本协议已验证的 Agent 平台（OpenCode /
> Claude Code / Codex 等）、版本行与版本策略为规则维护约定，均非协议语义定义；正文协议语义与
> 具体平台无关。
> 适用：OpenCode / Claude Code / Codex 等支持 subagent 的 Agent 平台
> 完整规则文档，从此文件开始阅读。
> 当前版本见 `git describe --tags` 或 README.md badge。
>
> 版本说明：规则新增/调整升 minor（v1.1.0），破坏性变更升 major（v2.0.0）

---

## agate 是什么

agate 是一套「主 Agent 编排、子 Agent 执行」的开发流程。主 Agent 不亲自写代码或文档，而是把每个阶段派发给独立上下文的 subagent，自己只做四件事：读状态、派发、验门槛、更新状态。任务状态全部落盘到文件，会话中断也能恢复。

agate 建立在两条主线上：

**编排主线（已被真实任务验证）**
- **P0 任务简报**：主 Agent 在派发任何 subagent 前亲自写 P0-brief.md，注入环境约束和风险判断
- 可执行的派发协议：用平台的派发工具派发 subagent，只传文件路径不传内容，门槛机器可判定，状态落盘
- 双层角色体系：执行角色（execution-roles）+ 评审角色（review-roles），收拢在 `assets/`
- 状态机落盘 + 可选的 /loop 自动编排

**需求与验收主线**
- **P1 需求基线**：先质疑需求、识别隐含依赖、用 BDD 写验收条件，建立一条"活的"需求基线
- **SCOPE+ 贯穿反馈**：任何阶段的 subagent 发现新的隐含需求，都能向上反馈、增补基线，而非憋着或擅自扩大
- **P6 验收**：把 BDD 条件逐条实际跑一遍，结果翻译成人能看懂的行为描述
- **NEED_CONFIRM 按需介入**：需求明确时 Agent 自走并始终产出可见文件；只有判断拿不准方向时才停下找人



---

## 目录结构

```
~/.agate/                        # 标准安装根：单软链 → 仓库 agate/ 子目录（legacy，兼容）；或版本管理目录（TAG0008 起：vX.Y.Z/ + latest/current 指针，经 agate-resolve 解析）
├── AGENTS.md                    # 协议本体入口指引（角色清单 + 升级/卸载）—— Agent 找路从这里开始
├── WORKFLOW.md                  # 本文件：主流程（入口）
├── dispatch-protocol.md         # 派发协议、gate 表、特殊事件处理
├── role-system.md               # 双层角色体系说明
├── loop-orchestration.md        # /loop 自动编排设计
├── state-machine.md             # 状态机落盘设计
├── git-integration.md           # git 持久化（多 agent 协作）
├── platform-notes.md            # 各平台适配说明
├── orchestrator-template.md     # 新项目接入模板
├── SETUP.md                     # 首次接入步骤
├── UPGRADING.md                 # 存量项目升级/迁移指引
├── LIMITATIONS.md               # 已知局限（使用前建议先读）
└── assets/
    ├── review-roles/            # 评审角色库（从 gstack 提取）
    │   ├── review.md            # /review 偏执 Staff Engineer
    │   ├── plan-ceo-review.md   # /plan-ceo-review 创始人/CEO
    │   ├── plan-eng-review.md   # /plan-eng-review 工程经理
    │   ├── design-review.md     # /design-review 高级设计师+前端
    │   ├── plan-design-review.md
    │   ├── qa.md                # /qa QA 工程师
    │   ├── investigate.md       # /investigate 调试专家
    │   ├── cso.md               # /cso 安全官
    │   └── judge.md             # /judge 验收独立裁判（P6.5，所有任务强制）
    ├── execution-roles/         # 执行角色库
    │   ├── analyst.md           # P1 需求分析师（需求质疑 + BDD 基线 + 能力预检）
    │   ├── architect.md         # P2 方案设计师（设计 + P7 一致性检查）
    │   ├── test-designer.md     # P3 测试设计师（TDD + E2E）
    │   ├── implementer.md       # P4 实现工程师（实现 + P8 多包发布）
    │   ├── verifier.md          # P5 技术验证 / P6 验收（BDD 实跑）
    │   ├── consistency-reviewer.md  # P7 一致性交叉检查
    │   └── vision-analyst.md    # UI 视觉结构分析（被 P6 verifier 按需派发）
    └── templates/
        ├── active-tasks-template.md # active-tasks.md 看板模板
        ├── custom-role.md       # 自定义角色模板
        ├── dispatch-prompt.md   # 派发 prompt 模板
        ├── roadmap-template.md  # roadmap 条目模板（新增）
        └── task-files.md        # 各阶段产出文件模板
```

---

## 工作区目录规范

agate 的所有**编排状态**统一落盘到工作区（默认 `{AGATE_WORKSPACE}` = 项目根下 `agate-workspace/`，可用 `.agate.env` 配置指向其他位置，解析见 `agate_common.py`），不再散布在项目 `docs/` 下。工作区根下固定 9 个子目录：

```
{AGATE_WORKSPACE}/                # 工作区根（默认 agate-workspace/）
├── roadmap/                      # 项目级任务规划看板（roadmap.md）
├── tasks/                        # 任务目录（active-tasks.md + 各 {Txxx}/ 任务）
├── agents/                       # agent 输入知识（project.md / memory）；也承载 CODE-MAP.md（项目架构全貌维护物，非任务产出，不新增第 10 个固定子目录）
├── debt/                         # 技术债登记（tech-debt.md，模板见 assets/templates/tech-debt-template.md）
├── archived/                     # 归档（已归档任务/阶段产出）
├── reviews/                      # 评审记录
├── decisions/                    # 决策记录
├── plans/                        # 计划
└── logs/                         # 运行日志（orchestrator-log 等）
```

### 内容边界判据（正式规则）

**问题**：什么文件应该进工作区，什么文件应该留在项目 `docs/`？

**判据**：某文件是否**由 agate 编排流程生成或消费**（任务产出、评审、决策、计划、日志、状态、看板、roadmap、agent 知识、归档）？
- **是** → 归入工作区 `{AGATE_WORKSPACE}/`。
- 该文件是否**描述产品/项目本身而非任务编排**（README、产品文档）？
- **是** → 留在项目 `docs/`。

**二值判定**：一个文件必须且只能归入一侧；两侧同时不适用 = 属项目文档。

**对偶自洽性**：同一判据对两类文件必须给出相反结论——任务验收记录（编排流程生成）→ 工作区；项目 README（描述产品本身）→ 项目 docs/。若发现某文件既像编排状态又像产品文档，优先问"这是谁生成、谁消费的"——由编排流程生成/消费 → 工作区。

### roadmap 循环

roadmap 是项目级任务规划层（单文件 `{AGATE_WORKSPACE}/roadmap/roadmap.md`，模板 `assets/templates/roadmap-template.md`），管理"新需求 → 任务 → 实施 → 回写"的闭环：

1. **新需求/讨论进入 roadmap**（BDD-14）：新需求或讨论 → 在 roadmap.md 追加一条 backlog 条目（含来源与日期）。
2. **条目拆分为任务**（BDD-15）：拆任务时在 `{AGATE_WORKSPACE}/tasks/` 建任务目录 + active-tasks.md「待开始」区写入任务行（任务行记录 `roadmap: <条目id>` 关联），条目状态 → `scheduled`。
3. **任务完成回写**（BDD-16）：任务完成（P8 gate + READY）→ 回写条目状态 `done`（或 `cancelled`），闭环可追溯。

条目状态：`backlog`（待规划）/ `scheduled`（已拆任务）/ `in_progress`（实施中）/ `done`（已完成）/ `cancelled`（取消）。状态机定义见 `assets/templates/roadmap-template.md`。

---

## 任务目录命名约定（重要）

任务目录名是 **`Txxx-描述`** 格式，不是纯编号。实际例子：
```
{AGATE_WORKSPACE}/tasks/TAG0001-mcp-namespace-map/
{AGATE_WORKSPACE}/tasks/TAG0002-fix-db-migration/
```

本文档及模板中的 `{Txxx}` / `{task_id}` 是占位简写，**实际拼路径时必须用完整目录名**（含描述后缀）。主 Agent 派发时，要先确认实际目录名（`ls {AGATE_WORKSPACE}/tasks/`），不要假设是纯 `T002`——按 `{AGATE_WORKSPACE}/tasks/T002/` 拼路径会找不到文件。

## 运行环境前提

> 实现注记：本节为平台运行前提的适配说明——「task 工具」是平台派发能力的具体实现命名（详见
> dispatch-protocol.md 铁律 1 注记，协议语义一律以"派发 subagent"为准）；「已知适用环境」表记录
> 本协议在哪些平台验证过、各平台能力差异与完整度，属平台适配元信息（平台名集中于此处是正确组织，
> 不构成语义定义）；「Claude Project 会话的定位/建议工作方式」是平台间交接的工作流建议；执行环境
> 在 P0-brief 的 `executor_env` 字段声明是跨平台约定（值为各平台枚举，非本协议语义定义）。

**agate 的完整执行依赖两个能力：**

| 能力 | 说明 | 缺失时的影响 |
|------|------|------------|
| `task` 工具 | 派发独立上下文的 subagent | 无法编排，所有阶段由主 Agent 直接执行 |
| 本地开发环境 | 语言运行时、测试框架、浏览器 | gate 命令无法执行，P5/P6 无法验证 |

**已知适用环境：**

| 平台 | task 工具 | 本地环境 | agate 完整度 |
|------|----------|---------|---------|
| OpenCode | ✅ | ✅ | 完整 P0-P8 |
| Claude Code | ✅ | ✅ | 完整 P0-P8 |
| DSH | ✅ | ✅ | 完整 P0-P8 |
| Codex | ✅ | ✅ | 完整 P0-P8 |
| Claude Project 会话 | ❌ | ❌（网络受限）| 仅 P0-P2 设计规划 |

> DSH / Codex 无 `.claude/agents/` 等价的 orchestrator 软链注册步骤（DSH 用 preset；Codex 经 CLI
> 登录 + 自动化 flag，仍跑完整 P0-P8、有原生 `spawn_agent` 派发），接入见 `SETUP.md` 步骤 2-DSH /
> 2-Codex。平台能力的权威源是 `platform-notes.md`。

**Claude Project 会话的定位：**
- 适合：P0-P2（设计决策、需求基线、方案评审）、代码审查
- 不适合：P3-P6 技术验证、E2E 测试、发布准备
- 建议工作方式：用 Claude Project 完成 P0-P2 并 push 到 main，再切换到 OpenCode/Claude Code 执行 P3-P8

**执行环境在 P0-brief 的 `executor_env` 字段里声明**（见 task-files 模板），后续所有阶段的 gate 判定和 subagent 派发以此为依据。

---

## 适用边界（agate 不适合什么）

> 实现注记：本节「任务类型建议」表中"Claude Project 会话"一行是平台间交接的工作流建议（在受限
> 平台做 P0-P2 设计规划、交接给完整平台执行 P3-P8），属平台适配说明，非协议语义定义；任务类型
> 分层判断（微/小/中/大）的协议语义与具体平台无关。

agate 的派发机制有固定开销——每次派发约需写 25 行派发 prompt。**只有当"被隔离的内容量" > "派发开销"时，走 agate 才划算。**

| 任务类型 | 建议 |
|----------|------|
| 微任务（声明性改动，见下方分层判断）| 直接做，不走 agate |
| 小任务（行为逻辑改动，单点）| 裁剪流程：P1 + P2 + P3 + P4 + P5 + P6，跳过 P7；P3 仅在满足可跳条件时才跳 |
| 中任务（行为逻辑改动，跨模块；或机制交叉）| 完整 P1-P8 |
| 中任务（Claude Project 会话）| P0-P2 设计 + 交接给 OpenCode/Claude Code 执行 P3-P8 |
| 大任务（跨模块重构）| P1 拆成多个子任务，各自走 P1-P8 |

### 改动性质判断（决定流程类型的入口）

**判断"直接做"还是走 agate，先看改动性质，再看影响范围和风险等级。**

第一步：改动性质（决定流程类型）
- **声明性改动**（不改变程序运行时控制流，只改变声明值）→ 可直接做
  判断方法：改前和改后，程序的控制流是否相同？相同→声明性，不同→行为逻辑
  示例：样式值、配置常量、文案 typo、连接字符串
- **行为逻辑改动**（条件分支、状态转换、数据处理）→ 至少走裁剪 agate
- **机制交叉**（≥2 个子系统交互、时序依赖、跨层影响）→ 必须走完整 agate

第二步：影响范围（调整裁剪程度）
- 单点（单文件/单模块内）→ 按性质判断
- 跨模块且有语义关联 → 性质升一级（声明性→裁剪 agate，行为逻辑→完整 agate）
- 跨模块但无语义关联（如两个文件各改一个 typo）→ 按单点处理

覆盖规则：高风险（安全/数据/权限）任务不论改动性质，至少走裁剪 agate

> 架构决策记录：ADR-005

### 规划层与执行层的关系（roadmap / plan / task 如何挂接）

> 实现注记：本节的 task 一词指协议的工作单元概念（`{Txxx}` 任务，与 roadmap/plan 同属规划层
> 概念），不是平台派发工具的命名；roadmap/plan/task 三规划工具的关系是协议语义，不绑定任何
> 平台。

**改动最终都走执行路径，但改动前的"登记与方案"分属两个规划工具——它们是输入，不是独立执行通道：**

| 规划工具 | 定位 | 与执行层的关系 |
|---------|------|--------------|
| **roadmap**（`{AGATE_WORKSPACE}/roadmap/roadmap.md`）| 需求登记簿（backlog → scheduled → done）| 所有改动都应留痕（RM 条目）；拆 task 时条目→scheduled；**微任务/直接做可"记录后直接改"不必拆完整 task** |
| **plan**（`{AGATE_WORKSPACE}/plans/`）| 某个 task 的实施方案（可选参考）| **不是独立执行通道**。走完整 task 时可作为 P1/P2 的参考输入；**有 plan ≠ 裁剪阶段**（task 仍走 P0-P8，P1/P2 产出自己的需求与设计，可引用 plan 不可跳过 gate） |

**三条执行路径（改动性质决定走哪条，roadmap/plan 只是前置登记与参考）：**

```
改动意图
  ├─→ 记录到 roadmap（RM 条目 backlog）
  │     ├─ 机制级/跨模块 → 拆 task（条目→scheduled）→ 完整 P0-P8（dogfooding 用 worktree 隔离）
  │     ├─ 行为逻辑单点 → 拆 task（裁剪流程）
  │     └─ 声明性改动 / 声明性缺陷修复（如 typo、配置值）→ 记录后直接改 + PR 提交流程
  └─（可选）写 plan → 作为上述完整 task 的参考输入，不替代 task
```

> **直接做只限声明性**：行为逻辑改动（含单点、含行为逻辑缺陷修复）一律至少走裁剪 agate（ADR-005）；「直接做」通道仅对声明性改动（控制流不变）开放。行为逻辑缺陷修复归入「行为逻辑单点 → 裁剪 agate」。

**plan 的定位警示**：plan 是"分析产物"，不是"批准产物"。即使 plan 经过独立评审（approved），它也只是 P1/P2 的**输入材料**——task 的 P1 需求基线和 P2 设计仍需独立产出并过 gate。原因：plan 评审审的是"方案"，task gate 验的是"本次任务的实际产出与验收"，两者不互换。RM-AG0016 的 stage 完整性声明是此规则的实例。

### 可裁剪的阶段

- **核心阶段（不可跳）**：P1 需求基线、P2 方案设计、P4 实现、P5 技术验证、P6 验收、P6.5 独立 Judge 复核
- **可选阶段（按需加）**：P7 一致性（多文件改动时）
- **ceremony 档位（thin / standard / full）**：P1 frontmatter 声明的仪式深度，缺省 standard（fail-closed）。
  `thin` 薄化 P2/P4 的 LLM 评审（须连同 `coupling_checklist` 流式 + 跳过风险 + `phases` 含 P5/P6 四要素
  声明，缺一回退 standard）；`full` 强制 P7 不可裁。**ceremony 不改状态机转移、不改 retry 上限、不薄化
  P5/P6**。完整 checklist 见 `phase-cards/P1-requirements.md`「ceremony fail-closed 声明 checklist」节
- **P2 不可裁剪**：方案设计是必经阶段。design_trivial / follows_existing_pattern 可简化 P2（1 个候选方案），不可省略。
  design_trivial 适用于纯 typo/文案/配置值修改；follows_existing_pattern 适用于照搬已有模式
- **P3 TDD 测试先行默认保留**：P3 不是「需要 TDD 时才加」，默认保留，有明确理由才跳过。
  可跳过的情形只有两种：
  ① 配置类任务——没有可测试的行为（如调整 CI/k8s/compose 配置文件）。注意：配置类任务仍是软件工作，只是测试策略不同（验证部署结果而非单元测试）
  ② 极小改动（≤3 行）且 P1 能明确指出哪条现有回归测试已覆盖该改动
  跳过 P3 须在 P1 裁剪说明里写明理由，由主 Agent 确认（「任务简单」不是合法理由）
  **单 Agent 模式**（`has_task_tool: false`）：P3 和 P4 由同一 Agent 执行，独立视角消失。
  此时 P3 的价值从「独立验证」变为「提前定义行为契约」——先写测试让自己明确"完成标准"，
  而不是边实现边定义。须在 P1 裁剪说明里声明 `single_agent_mode: true`。
- **P6 不可裁剪**：验收是质量最后防线。no_behavior_change 可简化 P6（快速验收），不可省略。仅微任务（直接做不走 agate）可免于 P6。`change_type: refactor` 的任务 P6 换用回归口径（行为不变 + 全量回归全绿 + 关键路径验收）——换口径 ≠ 裁 P6，P6 仍不可裁剪
- P8 发布准备：涉及发布的任务必做
- **裁剪必须附理由**：P1 分析师判定复杂度后，在 `P1-requirements.md` 的「裁剪说明」节写明每个跳过阶段的理由；主 Agent 按声明推进，不强制全 8 阶段
- **裁剪不等于跳过需求质疑**：无论任务大小，P1 的需求基线（哪怕一句话）都要建立，因为隐含需求的识别不依赖任务规模

### P3 测试设计指导

Given 不仅是"数据准备"，也是"系统处于某种状态"——这个状态本身需要被验证。例如：UI 项目验证页面首次加载时展示已有数据；后端项目验证服务启动后初始状态正确；嵌入式项目验证上电后外设处于已知状态。测试设计容易只覆盖 When/Then 触发的交互路径，忽略 Given 隐含的初始化路径。

### 裁剪风险维度（T005/T006 教训）

**裁剪决策必须同时考虑「复杂度」和「风险程度」。** 以下情况，无论任务看起来多简单，对应阶段均不可跳过：

**基本原则：开发全程在测试环境进行，生产环境不在 agate 编排范围内。**
生产部署属于 `make publish` 之后的运维范畴，不属于 P1-P8 流程。

| 风险特征 | 不可跳过的阶段 | 原因 |
|---------|--------------|------|
| 涉及数据 schema 变更或迁移（测试环境）| P6 验收 | 迁移逻辑需要完整验收，schema 问题在测试环境就要发现 |
| 涉及数据删除操作 | P6 验收 + `[NEED_CONFIRM]` 硬中断 | 即使在测试环境，批量删除也需人工确认范围 |
| 涉及安全相关改动（权限、认证、加密）| P6 + P7 | 安全改动的行为验收和一致性检查缺一不可 |
| 涉及 ≥2 个改动端（如 API + CLI + 客户端）| P6 + P7 | 多端联动行为需要整体验收 |
| 主 Agent 对任务范围有不确定感 | 默认走完整 P1-P8 | 不确定时保守是对的 |

**裁剪的最终拍板权在主 Agent，不是 P1 analyst。**
P1 analyst 可以建议裁剪，但主 Agent 必须结合 P0-brief.md 里声明的已知风险做独立判断，不能直接接受 P1 的裁剪建议。

### 风险矩阵

任务分类应该是"复杂度 × 风险"的矩阵，不是只看复杂度。**先用上方改动性质判断确定流程类型，再用本矩阵确定裁剪程度：**

| | 低风险 | 高风险（安全/数据/权限）|
|---|--------|----------------------|
| 微改动 | 直接做 | 精简 agate：P1 + P4 + P5 |
| 小改动 | 裁剪 agate：P1 + P3 + P4 + P5 | 完整 agate（至少到 P6）|
| 中改动 | 完整 P1-P8 | 完整 P1-P8 + P6 不可裁剪 |

"直接做"的最低要求：commit message 必须声明改了什么 + 改动性质（声明性/行为逻辑/机制交叉）+ 为什么安全。

### 测试/调试环境隔离原则（项目级责任）

agate 要求开发全程在测试环境进行，但「如何保证隔离」是项目的责任，不是 agate 硬编码的。每个项目应实现：

- **强制隔离**：测试运行时自动将存储路径重定向到临时目录，不依赖开发者手动配置（最强保障）
- **调试模式自动隔离**：启动调试环境的命令（如 `make debug` 或 `npm run dev:test`）自动使用独立的数据目录
- **启动前状态检查**：调试/测试启动脚本应检查生产数据是否存在异常（如近期记录数突变、含测试特征的数据），异常时阻止启动并警告
- **不依赖文档规则**：文档说明是最弱的隔离保障，上述三条才是真正可靠的机制

agate 在 P0-brief 的 `env_constraints.debug_env` 字段里要求写明测试环境命令，是项目实现上述隔离机制的约定读取点。
P5 gate 要求「测试环境隔离正常（无 [PROD_TOUCHED]）」，是流程层面的验证触发点。
具体隔离机制由项目自行实现，agate 不硬编码路径或检查方式。

---

## P1-P8 阶段总览

> 本表为角色/评审映射颗粒度；逐条可执行判定命令见 `dispatch-protocol.md`《可判定门槛规范》。

<!-- S1S2-ANCHOR-START：本表是 `check-structure-consistency.py` S-1（YAML→md）/S-2（md→YAML）双向一致性检查的 md 侧锚点（数据面 = `rules/phases.yaml`） -->
> **S-1/S-2 锚点**：表行三段式 `| P{N} | 名称 | 执行角色 | …`；S-1 比对 phases.yaml 的 id/name/exec_role + 第 4/5 列 next/retreat（第 1-3 列 = 既有比对列，`_TABLE_ROW_RE` 只消费前 3 列不受影响；第 4/5 列 = next/retreat 扩展比对列，YAML `null` ↔ 表 `—`/空 归一），S-2 只匹配 `P` 数字/P6.5 前缀行（READY 行与表外行排除）。新增/改名阶段须同步 `rules/phases.yaml`。

| 阶段 | 名称 | 执行角色 | next | retreat | 评审角色 | 门槛（进入下一阶段的条件）|
|------|------|----------|------|---------|----------|--------------------------|
| P0 | 任务简报 | **主 Agent 亲自写**（非 subagent）| P1 | — | — | P0-brief.md 完成，含 debug_env + known_risks |
| P1 | 需求基线 | analyst（需求质疑模式）| P2 | — | requirements-review（强制，不可裁，所有任务都走独立 review）| P1-requirements.md 存在，含 BDD 验收条件；`grep -cE '^\s*-?\s*\[NEED_CONFIRM\]'` → =0（仅计算阻塞项；倾向项 `[SUGGEST:]` WARNING 不阻塞）+ 无 `status: GAP`（supplementable 不阻塞）；P1-review.md status:approved + agent≠main + 含 `BDD-[0-9]` 锚点 |
| P2 | 方案设计层 | architect | P3 | — | plan-eng-review（risk_level=high 时必须派发独立 subagent，check-gate.py 对 agent=main 硬拦截 exit 1）/ plan-design-review（domains 含 frontend 时追加，审视觉/交互/渲染形态适配维度）/ plan-ceo-review（涉及商业模式判断时可选）| P2-review.md 的 status == approved；`grep -cE '^(packages|domains|ui_affected|gate_commands):' P2-design.md` → ≥4；`grep -qE '权衡|选择理由|取舍|考量|trade-?off' P2-design.md` → 命中（或含"选择"+理由/原因/因为组合）；不可裁（design_trivial / follows_existing_pattern 可简化，不可省略）；强制 ≥2 个候选方案（design_trivial/follows_existing_pattern 时可只写 1 个）；ui_affected: true → 含 UI 设计节（## UI 设计+形态声明+按形态 checklist，P2 gate 拦截缺失/不一致） |
| P3 | 测试设计 | test-designer | P4 | — | gate 自检（文件存在）+ TDD 红灯独立确认 | check-gate.py P3 exit 2（文件存在）+ scripts/check-tdd-red.py exit 0（主 Agent 手动 + CI backstop 兜底）|
| P4 | 代码实现 | implementer | P5 | — | review（改动跨 ≥3 个文件或涉及核心数据结构）/ cso（涉及认证、权限、密钥、用户输入处理、外部网络请求任一项）/ design-review（domains 含 frontend）；命中任一条件才派发，判断结果写入 .state.yaml | 暂存区含非 md/yaml 文件（`git diff --cached --name-only | grep -qvE '\.(md|yaml)$|^\.state'`）|
| P5 | 技术验证 | verifier（P5 模式，subagent 派发）| P6 | P4 | gate 自检 + N5 最小校验（test runner 输出签名）| P2 `gate_commands.P5` 命令 exit 0 AND failed==0；行首锚点扫描（主 Agent 参照 pre-commit 三步逻辑手动判断：正向→PAUSED / 不合规→修正 / 缺失→静默通过） |
| P6 | 验收 | verifier（验收模式）| P7 | P4 | — | `scripts/check-gate.py P6` exit 2（FAIL=0/NC=0/证据非空）；`scripts/check-p6-evidence.py` UI 截图 > 1KB（R1a 客观证据 barrier）+ 渲染形态证据形式匹配（帧序列/渲染输出对比/时序截图）+ avg-hash 雷同降级待复核；`scripts/check-p6-provenance.py` exit 0（证据-结论对应 + dispatch-context 审计 + BDD 总数对照由审计 3 自动执行 + R1b vision YAML 审计的 GAP 放宽）；UI 条件按 P1 vision 能力三态分档双证据（available/supplementable→vision YAML blocker_count==0；GAP→截图/帧序列+人工复核记录；证据形式按渲染形态选择）⚠️ self-authored（降级缓解：provenance 审计 + R1a 截图实质检查；**P6.5 judge 独立复核强化缓解**，机制见下） |
| P6.5 | 独立 Judge 复核 | judge（**强制，所有任务**；fresh context 逐条重验全部 BDD，只信证据与 git log）| —（gate_subphase: 通过→P7）| —（needs-revision→P6）| — | `P6.5-judge-verdict.md` 存在 + `scripts/check-judge-verdict.py` exit 0（Header 字段/criteria_total==P1 BDD 数/结论编号集零挑验/证据交叉核对/信息隔离白名单/预算交叉）+ `scripts/check-events.py` exit 0（事件账本哈希链/ts 单调/轮次计数）；历史任务（.state.yaml 无 `judge.enabled: true`）→ check-gate.py P6.5 早退跳过（BDD-2）；主 Agent 跑 `check-gate.py P6.5 $TASK_DIR` 判定 |
| P7 | 一致性检查 | consistency-reviewer（subagent 派发）| P8 | — | gate 自检 + N3⑨ 实质锚点（跨文件引用关键词）| `grep -E '^\s*-?\s*\[BLOCKER\]' P7-consistency.md | grep -cvE '\[BLOCKER\][:：]?\s*\d+\s*条?\s*$'` → =0；同理 DEVIATION-CRITICAL → =0 ⚠️ self-authored |
| P8 | 发布准备 | implementer（P8 模式/releaser，subagent 派发）| —（无自动后继：exit 0 后转 READY 由人/发布流程处理）| —（失败重试本阶段）| gate 自检（发布检查命令）| `scripts/check-gate.py P8` 脚本化部分通过（exit 2）；P2 `gate_commands` 逐包 exit 0；bump 后重跑 P5 `gate_commands.P5` exit 0；`git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 无遗漏；P2 `packages` 验证 version 文件路径；`grep -q 'bump_type:' P8-release.md` 命中；version 双路径检查（暂存区或最近 5 commit，WARNING）；CHANGELOG 双路径检查（暂存区或最近 5 commit，WARNING，`CHANGELOG_FILE` 环境变量可覆盖默认 CHANGELOG.md）；`check-pruning.py` 验证裁剪 P8 时有 `internal_only: true` 声明 |
| READY | 待发布 | — |  |  | — | 人手动 `make publish` → DONE |

<!-- S1S2-ANCHOR-END：阶段总览表 S-1/S-2 锚点终点（表行增删须同步 `rules/phases.yaml`，否则 check-structure-consistency.py S-1/S-2 报 ERROR） -->

**P1 与 P6 的关系**：P1 用 BDD（Given/When/Then）写下"做完之后应该表现成什么样"，P6 把这些条件逐条实际跑一遍、把结果翻译成人能看懂的行为描述。P1 是"约定"，P6 是"兑现验证"。

**P6 vs P7 的区别**：P6 验收是"行为对不对"（用户视角，BDD 条件是否满足）；P7 一致性是"实现和设计一致不一致"（技术视角，代码是否偏离 P2）。两者关注点不同，不可互相替代。

**P6.5 judge 复核（强制）**：P6 commit 完成后、P7 之前，主 Agent 派发 judge（所有任务强制）。judge 以 fresh context 逐条重验**全部** BDD（含 P6 已判 PASS 项，零挑验），只信 `P6-evidence/` 证据与 git log，**不阅读** P6-acceptance.md 与 implementer/verifier 的任何自述（信息隔离白名单）。产出 `P6.5-judge-verdict.md` 后，主 Agent 跑 `check-gate.py P6.5 $TASK_DIR`（= check-judge-verdict.py + check-events.py 双 exit 0，历史任务早退跳过）→ 通过才可写 phase: P7。judge verdict 是行为描述输入，**exit code 才是门槛**（哲学红线，BDD-9）；commit-time 由 pre-commit-gate 注入硬边界 + CI backstop 兜底。预算：轮次 ≤2 / token 100k（`judge_token_budget` 可覆盖）/ 时间 30min，超限诚实降级 `partial: true` → needs-revision（BDD-8）。

详细派发方式见 `dispatch-protocol.md`，角色定义见 `assets/`。

**评审被拒必须写 retries（RM-AG0042）**：任一阶段评审 `status: rejected` 触发重试时，主 Agent 必须同步在 `.state.yaml` 的 `retries[Pn]` 追加一条记录——`check-state-transition.py` 按重新派发评审角色产生的新编号 dispatch-context 文件名（`P{n}-dispatch-context-{role}-retryN.md`/`-revN.md`，见 `dispatch-protocol.md`「评审打回后的意见回流」）机械检测该阶段是否发生过评审重试，缺失对应 retries 记录时高优 WARNING（不阻断）。

---

## Pre-commit 检查总览

每次 `git commit` 触发 pre-commit hook，按以下顺序自动运行（任何 `exit 1` 中止 commit，`exit 2` 警告不阻塞）。
**本表是「pre-commit 检查集」的唯一事实源**——其它文档只指针引用、不复制清单。表中 `P1.x`/`P2.x` 括号
标签是历史锚号（沿革自早期硬工具化路线图），当前以脚本名 + 机制说明为准：

| # | 检查脚本 | 触发条件 | 阶段/机制 | 行为 |
|---|---------|---------|-----------|------|
| 0 | `check-state-yaml.py` | `.state.yaml` 暂存变更时（不依赖 phase 变）| 文件级 | 校验格式合法（必填字段、phase 取值、retries 结构）|
| 1 | `check-gate.py` | `.state.yaml` phase 变更或阶段产出文件变更 | 阶段级 | P1.1 gate 校验 |
| 1.2 | — | 全局，任意阶段 | 全局级 | `[PROD_TOUCHED]` 标记三步检测（正向声明→中止 / 声明格式不合规→中止 / 缺失声明→静默通过）|
| 1.6 | `check-changelog.py` | P8 phase 且 gate 通过后 | 文件级 | `[Unreleased]` 含本次 task_id（P1.6；P2.54：仅 P8 检查，P1-P7 不触发）|
| 1.7 | `check-p6-evidence.py` | 阶段 ∈ {P6, P7} | 阶段级 | P6-evidence/ 非空 + BDD 行数 ≥ 1 + md5 逐字节去重（阻断）+ 像素方差/average hash 检测（WARNING）|
| 2.1 | `check-p6-provenance.py` | gate 通过后 | 阶段级 | 六道客观审计（证据-结论对应 + dispatch-context 内容约束 + BDD 总数对照 + UI vision YAML 审计 [R1b] + EXIT_CODE 一致性 [审计5] + evidence JSON 与 PASS/FAIL 声明一致性 [审计6/P2.57]）+ agent 字段协作规范；exit 1 硬拦截，exit 2 WARNING（P2.1/P2.10 v2 降级方案）|
| 2.3 | `check-state-transition.py` | gate 通过后 | 阶段级 | 状态转移合法性 + 重试上限（P2.3-P2.5）+ 门槛失败事件 ↔ retries 对应性校验（RM-AG0042：单步回退未同步写 retries 阻断；评审被拒重派/子代理空返回重派未写 retries 高优 WARNING）|
| 2.7 | `check-pruning.py` | gate 通过后 | 阶段级 | 裁剪条件与实际执行一致性 + override 校验（P2.7-P2.9）|
| 2.7.1 | `check-routing.py` | gate 通过后 | 阶段级 | ceremony 路由校验（TAG0019）：声明 ceremony 与算分 tier 一致性（单向 fail-closed）+ thin 四要素 checklist（coupling_checklist 流式 / 跳过风险 / P5/P6 保留）缺一拦截；不声明 = standard 不拦截（BDD-7/8/9）|
| 2.11 | `check-scope-resolved.py` | gate 通过后 | 阶段级 | `[SCOPE+]` 必须有 `[SCOPE_RESOLVED:...]` 标记（P2.11）|
| 2.12 | `check-retrospective.py` | gate 任何结果 | 阶段级 | 异常模式提醒（重试超限/SCOPE+/override）→ 写复盘；另检测到 DEBT/roadmap 已登记本任务（机制缺口信号，TAG0015）→ 追加提醒；均不阻塞 commit（P2.12）|

**关键设计原则**：

- **0→1→1.6→1.7→2.* 顺序**：每个阶段有"关卡"——0 是格式关、1 是行为关、2.* 是合规/审计关。任何关卡失败 → 中止 commit。
- **agent 字段协作规范（P2.1/P2.10 v2 协作层）**：所有阶段产出文件 Header 含 `agent: <角色>`，缺字段 WARNING 不阻塞（向后兼容），`agent=main`（自审）被 check-gate.py 硬拦截 exit 1。
- **CI backstop（P1.3）**：push 后 CI 平台（GitHub Actions / GitLab CI / Gitea Actions）重跑 `check-gate.py` + `ci-gate-backstop.py`，捕获 `--no-verify` 绕过 hook 的恶意提交；provenance 审计重跑（check-p6-provenance.py）+ `P6-acceptance.md` 的 git blame 单 author WARNING 作为兜底审计。
- **降级方案**（Phase 3 平台接口未实现前的最优方案）：证据-结论对应是**客观行为审计**——造假 N 个证据文件的成本远高于填写一行 `agent: verifier` 自报字段。详见 `LIMITATIONS.md` 局限 3。

**多任务适配**：`pre-commit-gate.sh` 扫描暂存区中所有变更的 `.state.yaml`（根目录 + `{AGATE_WORKSPACE}/tasks/{Txxx}/`），对每个文件独立跑格式校验 + 状态转移 + gate。单任务架构（根 `.state.yaml`）向后兼容。

**三类 WARNING（均不阻断 commit）**：
- **phase-产出一致性**：暂存了 `P{n}-*.md` 产出但 `.state.yaml` 的 phase 不匹配 → WARNING。覆盖"产出了但忘改 phase"场景，下次 agent 接手时由「状态标记绑定规则」（见 state-machine.md）兜底。
- **dispatch-context 缺失**：暂存了阶段产出但 `P{N}-dispatch-context-*.md` 不存在 → WARNING。覆盖"产出已写但忘记先写 dispatch-context"场景。
- **非实现阶段代码暂存**：非 P4/P5/P6 阶段暂存了代码文件（非 .md/.yaml）→ WARNING。覆盖"主 Agent 在非实现阶段直接改代码"场景。

**Pre-push hook**：`git push` 时自动检测 `agate/*.md` 改动量，超过阈值（默认 20 行，可通过 `AGATE_ALIGNMENT_REVIEW_THRESHOLD` 环境变量配置）时提示建议先派发 protocol-alignment-review。不阻断 push（exit 0）。

---

## 核心原则

### 原则 1：主 Agent 只编排，不执行

主 Agent 的职责严格限定为四件事：
1. 读状态（`{AGATE_WORKSPACE}/tasks/active-tasks.md` + 当前阶段文件）
2. 派发 subagent（用派发工具，见 dispatch-protocol.md）
3. 检查门槛（可判定条件）
4. 更新状态

**主 Agent 永远不自己写阶段产出（P1-requirements.md、P2-design.md、代码……）。** 这些都由 subagent 在独立上下文里产出。

**主 Agent 的合法职责（非降级）：**
- 写 P0-brief.md（PM 视角的任务简报，四字段自查）
- 派发前查证客观信息（环境状态、URL、选择器等），落盘成 `P{N}-dispatch-context-{role}.md`（信息量 >10 行或同阶段复用时）
- P8 gate 通过后执行 READY 收尾检查（停止调试服务、清理临时数据、还原开发环境、确认生产无残留——见 state-machine.md）
- PAUSED 时写 `PAUSED-resolution.md` 记录人工决策

**降级的硬边界**：降级（主 Agent 亲自执行阶段产出）只在 `has_task_tool: false` 或 `has_local_runtime: false` 时发生。**subagent 执行失败 ≠ 降级信号**——失败时走 retry/PAUSED，不允许"subagent 做不好"为由降级。

### 原则 2：上下文隔离 = 只传路径

派发 subagent 时，prompt 里只写**文件路径**，不塞文件内容。subagent 在自己的上下文窗口里读文件、干活，主 Agent 的上下文只增加"路径 + 一句话摘要"。

这是解决上下文爆炸的核心机制。

### 原则 3：状态在文件里，不在记忆里

任务的当前状态（在哪个阶段、哪些门槛过了）落盘到 `{AGATE_WORKSPACE}/tasks/{Txxx}/` 和 `{AGATE_WORKSPACE}/tasks/active-tasks.md`。即使会话被压缩、中断、重启，主 Agent 重新读文件就能接着干。

**状态落盘必须配合 git 持久化**（见 git-integration.md）：每阶段门槛通过后主 Agent commit 一次，让状态真正持久、可恢复、可多 agent 共享。只写本地文件不 commit，崩溃就丢。

### 原则 4：门槛必须机器可判定

进入下一阶段的条件必须是文件里可读取的明确值（status==approved、failed==0），不能是"方案足够好"这类模糊判断。

### 原则 5：重试有上限

门槛不通过时打回重做，但有次数上限（按阶段 2-3 次，见 state-machine.md 重试上限表）。超限则停下来报告人工介入，避免无限循环。

**PAUSED 不是失败，是正确路由。**

agent 的责任是"走对流程"，不是"让 gate 变绿"。派了真 subagent、跑了真验证、gate 仍不过——这不是你的失败，红灯是工作/设计的问题，不是你没本事顶过去。伪造证据让它变绿，才是唯一的失败。

走正规途径仍不过 → PAUSED/问人类 = 正确行为、零追责
伪造证据过关 = 唯一失败

⚠️ 这是 L0 指导（协议文本语义翻转），非 L3 硬拦截。效果取决于语义翻转对 LLM 行为的实际影响，需实证验证。但它零脚本成本，且与 ①③ 协同——当 honest path 被疏通（①）且红灯正确路由（③）时，PAUSED 的语义翻转才有物质基础。

---

## 需求与验收机制（agate 核心）

agate 在编排之上加了一层"做对的事并持续校准"。三个机制贯穿全流程。

### 需求基线：活的、向前累加

P1 不是把需求一次性定死，而是建立一条**基线**：质疑原始需求、识别隐含依赖、用 BDD 写出验收条件。这条基线是"活的"——后续任何阶段都能向它增补，它永远是最新最全的需求真相源（写在 `P1-requirements.md`，后续增补也回写到这里）。

BDD 验收条件用 Given/When/Then 描述行为，例如：

```
Given 用户创建 entry 不指定过期时间
When  查询该 entry
Then  过期时间是创建时刻起 15 天后
```

写不出 BDD 条件，说明需求本身还不清楚——这本身就是需要 `[NEED_CONFIRM]` 的信号。

### [SCOPE+]：任何阶段都能向上反馈新需求（行首声明格式：`^\s*-?\s*\[SCOPE+\]`，句中引用不触发）

P1 不可能预见所有隐含需求。P2 设计、P4 实现时，subagent 常会发现"前序阶段没覆盖、但技术上必须做"的事。这时 subagent 在产出文件中标注：

```
[SCOPE+] 发现：createEntry 和 publishFiles 的 expires 参数类型不一致
         必须做的理由：不统一会导致 MCP 两个工具行为分叉
         影响：P1 基线需新增一条 BDD；涉及 packages: [pkg-b]
```

主 Agent 看到 `[SCOPE+]` → 把它翻译成 BDD 形式 → 增补进 P1 基线（标记 `[SCOPE+ from Pn]`）→ 按"定向回补"决定哪些已完成阶段需要局部更新。

**与 `[SCOPE_GAP]` 的区别**：`[SCOPE+]` 是"发现了所有人都没想到的新需求"（向上涨）；`[SCOPE_GAP]` 是"主 Agent 的 prompt 漏了 P2 已声明的东西"（向下漏，见 dispatch-protocol.md）。

### 定向回补：不全重跑，只补受影响的部分

`[SCOPE+]` 触发后，**不是回到 P1 重走一遍**，而是：

1. **基线增补**：新需求写进 P1-requirements.md（唯一真相源，永远最新）
2. **判断影响范围**：主 Agent 对照新需求，看已完成的阶段里哪些产出需要跟着改
3. **定向局部回补**：受影响的阶段**增量更新**对应文件，未受影响的阶段和未来阶段自然消费最新基线

回补深度由"这条新需求实际需要哪些阶段"决定，不机械从 P1 重来。回补的转移规则见 `state-machine.md`。

### [NEED_CONFIRM]：默认自走，拿不准才找人

需求明确时，Agent 自走，**但每个阶段的产出文件始终生成**（人随时可看）。只有当 subagent 或主 Agent 判断"拿不准方向"时，才标注 `[NEED_CONFIRM]` 停下问人。

触发 `[NEED_CONFIRM]` 的条件（写进角色定义，不靠临场感觉）：
- 原始需求有多种合理理解，选哪种会显著影响结果
- `[SCOPE+]` 的新需求改动较大、伤及已确认内容
- 隐含需求涉及业务方向决策（"这个功能到底要不要做"）
- 安全、数据迁移、外部资源等不可逆或高风险操作

**人确认的是"行为/方向对不对"（能判断），不是"代码/技术对不对"（Agent 负责）。** BDD 条件由 Agent 起草，人只做加/删/改。条件写漏是 Agent 的责任，不是确认人的责任。

---

## 三种使用方式

### 方式 A：手动逐阶段（最稳）

人工逐个触发每个阶段的派发。主 Agent 派发一个 subagent，检查门槛，等人确认后派发下一个。适合关键任务、需要人工把关的场景。

### 方式 B：半自动（推荐）

主 Agent 连续派发，每过一个门槛自动推进（推进这一步用 `agate next` 查表机械完成，见 `state-machine.md`
「主 Agent 的单步执行」），只在门槛失败或重试超限时停下来问人。详见 `loop-orchestration.md`。

### 方式 C：全自动 /loop（增强）

主 Agent 自动跑完 P1-P8，全程不需人工介入，只在最终发布前汇报。仅在方式 B 稳定后启用。每步即调用一次
`agate next`。详见 `loop-orchestration.md`。

> **相关可选机制**（正文各归其权威源）：subagent 存活/卡死可观测性 = 命令流日志机制（RM-AG0055，
> `docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`）；跨 CLI/model 派发路由 =
> `agate-workspace/dispatch-routing.yaml` + `agate dispatch route`（RM-AG0060，`dispatch-protocol.md`
> 「派发路由」节；不配置 = 逐字节现状）。

---

## 平台适配

不同 Agent 平台的 subagent 机制不同。详见 `platform-notes.md`《各平台适配说明》——权威唯一来源，本文件不重复维护。派发协议的具体调用方式见 `dispatch-protocol.md` 的平台适配章节。

---

*主流程文档，详细机制见同目录其他文件*
