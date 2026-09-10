# agate 架构决策记录（ADR）

> 本文件记录 agate 协议的核心架构决策：做了什么决定、为什么、有什么后果。
> 审查员在 A7（设计原则一致性）审查时引用本文件。

---

## ADR-001: 隔离性——主 Agent 不写产出

### 状态

已接受

### 语境

agate 是"主 Agent 编排、子 Agent 执行"的流程。主 Agent 拥有全局视野，能读所有文件、判断所有状态。如果主 Agent 同时负责执行（写代码、写文档），就会在执行遇到困难时倾向于自行解决而非触发安全网。

### 决策

主 Agent 只做四件事：读状态、派发 subagent、验 gate、更新状态。主 Agent 永远不自己写阶段产出（P1-requirements.md、P2-design.md、代码……）。

### 理由

自审不可信。三个独立案例证明主 Agent 遇到困难时倾向于自行解决而非触发安全网：
- T005/T006：生产环境数据污染，主 Agent 违规降级
- T016：3 次违反现成协议
- T019：误写生产 DB 后未标 PROD_TOUCHED、跨阶段回退未 PAUSED、SCOPE+ 未触发

同一个根因：主 Agent "解决问题"的冲动强于"报告问题"的冲动。隔离性是结构性约束，不依赖主 Agent 当时的判断力。

替代方案：允许主 Agent 在"简单任务"时写产出 → 被否决，因为"简单"的判断本身不可信（见 ADR-005）。

### 后果

- 每次 subagent 派发有固定开销（约 25 行派发 prompt），微任务成本可能超过收益
- 降级只在 `has_task_tool: false` 时允许，subagent 失败 ≠ 降级信号
- 主 Agent 的合法职责（P0-brief、dispatch-context、READY 收尾）不违反隔离性——这些是编排工作，不是阶段产出

---

## ADR-002: 可判定性——gate 门槛机器可判定

### 状态

已接受

### 语境

agate 的阶段推进依赖门槛检查（gate）。如果门槛由主 Agent 主观判断（如"方案足够好"），则主 Agent 可以在任何时候声称"通过"，gate 形同虚设。

### 决策

gate 通过/不通过由脚本 exit code 决定（0=通过，1=不通过，2=需人工判断），不依赖主 Agent 自我报告或主观判断。

### 理由

主 Agent 的"通过"不可信。T058 P5 verifier 返回摘要"28/28 E2E PASS"，主 Agent 亲自跑命令发现实际是 9 failed, 19 did not run（环境变量遗漏）。verifier 的结论碰巧正确，但验证过程不完整。

替代方案：允许主 Agent 用自然语言判断 gate → 被否决，因为自然语言判断不可审计、不可重复、不可强制执行。

### 后果

- 有些质量维度不可脚本化（如"设计是否优雅"），只能用 exit 2 标记"需人工判断"
- gate 脚本只能检查客观条件（文件存在、字段非空、exit code =0），不能检查语义正确性
- 语义正确性由 subagent 独立上下文 + review 角色保证（见 ADR-006）

---

## ADR-003: 最小约定——不绑定技术栈

### 状态

已接受

### 语境

agate 要适用于不同技术栈的项目（Python/Vue、Java/Spring、Rust/CLI、嵌入式 C 等）。如果硬编码测试框架、语言、部署方式，agate 的适用范围会急剧缩小。

### 决策

agate 不硬编码测试框架/语言/部署方式，只定义流程骨架。技术栈相关的命令通过 P2-design.md 的 `gate_commands` 字段注入，由项目自定义。

### 理由

不同项目技术栈差异大。硬编码 `pytest` 或 `npm test` 会让非 Python/JS 项目无法使用。流程骨架（需求→设计→实现→验证→验收）是跨技术栈通用的。

替代方案：为每种技术栈写专门模板 → 被否决，维护成本高且无法覆盖所有组合。

### 后果

- 项目首次使用时需要在 P2 声明 `gate_commands`，有初始配置成本
- agate 不能自动发现项目的测试/构建命令，依赖人工声明
- `check-gate.py` 的 P4 检查用通用模式（`grep -qvE '\.(md|yaml)$'`）而非语言特定规则

---

## ADR-004: 安全网分层——hook 兜底，主动验主流程

### 状态

已接受

### 语境

agate 的 gate 检查在多个时机执行：主 Agent 主动验、pre-commit hook、CI backstop。如果只依赖单一防线（如只靠 hook），则该防线被绕过（`--no-verify`）时整个安全网失效。

### 决策

多层防线，任何单层失效不致命：
1. 主 Agent 主动跑 `check-gate.py`（主流程）
2. pre-commit hook 自动跑（兜底）
3. CI backstop push 后重跑（最后防线）

### 理由

T019 证明单层防线会被绕过。主 Agent 可能遗忘主动验、可能用 `--no-verify` 绕过 hook，但三层同时失效的概率极低。

替代方案：只靠 CI → 被否决，CI 反馈周期太长（几分钟），不如 pre-commit 即时。只靠 hook → 被否决，`--no-verify` 可绕过。

### 后果

- hook 是 WARNING 不拦截时，CI backstop 是最终兜底（见 CON.1/CON.6 检查）
- 三层防线的内容有重叠（同一 gate 脚本跑三次），但这是刻意设计——重复是安全网的特性，不是缺陷
- 主 Agent 应该主动验，而不是等 hook 报错再修——hook 是兜底，主动验是主流程

---

## ADR-005: 改动性质决定流程——声明性/行为逻辑/机制交叉

### 状态

已接受

### 语境

判断"直接做"还是"走 agate"，传统方式按任务规模（微/小/中/大）。但任务规模是连续变量，边界模糊——"这个 bug 修复算微任务还是小任务？"不同人判断不同。

### 决策

判断"直接做"还是走 agate 的入口维度是**改动性质**而非任务规模：
- 声明性改动（不改变控制流）→ 可直接做
- 行为逻辑改动（改变控制流）→ 至少走裁剪 agate
- 机制交叉（≥2 个子系统交互）→ 必须走完整 agate

改动性质是离散分类，边界比连续的"规模"更清晰。

### 理由

v0.9.1 复盘证明"简单"判断本身是最高风险决策。Bug #3 看似"点击无反应"（简单 bug），实际涉及三个机制交叉（sticky header + absolute 定位 + click-outside），修复引入新 bug，形成挤牙膏模式。

改动性质比任务规模更适合做入口维度，因为：
- 任务规模（微/小/中/大）是连续变量，边界模糊
- 改动性质（声明性/行为逻辑/机制交叉）是离散分类，边界更清晰——判断方法："改前改后控制流是否相同？"

替代方案：只按风险等级判断 → 被否决，低风险的行为逻辑改动也可能引入 bug（如 v0.9.1 的 handleClickOutside）。风险等级和改动性质是两个维度，都需要考虑。

### 后果

- 高风险任务有覆盖规则：不论改动性质，至少走裁剪 agate
- "直接做"有最低要求：commit message 须声明改动性质 + 为什么安全
- 判断边界仍有灰区（如"改数据库连接字符串"是声明性但高风险），覆盖规则兜底

---

## ADR-006: 双层角色——执行角色 + 评审角色

### 状态

已接受

### 语境

如果执行者同时评审自己的产出，评审就退化为自审——自审不可信（见 ADR-001）。agate 需要一种机制保证评审的独立性。

### 决策

执行和评审由不同角色完成。评审角色 `agent≠main`，check-gate.py 对 `agent=main` 硬拦截（exit 1）。

### 理由

ADR-001 的推论：如果主 Agent 自审不可信，subagent 自审同样不可信。独立评审提供外部视角，能发现执行者因认知盲区遗漏的问题。

评审不是全量覆盖——P1 评审通用（所有任务都走），P2/P4 评审是 C8 域触发（见 role-system.md），二者不对称。

替代方案：允许自审 + 加密验证 → 被否决，技术复杂且不解决认知盲区问题。允许跳过评审 → 被否决，v0.13.0 已收紧 P1 评审不可裁。

### 后果

- 每个需要评审的阶段至少派发两个 subagent（执行者 + 评审者），增加开销
- P2/P4 评审不是全量触发——只有 C8 域命中时才派发，小任务可能无评审
- review-mapping.md 定义了域→评审角色的映射，避免评审角色选择的主观性

---

## ADR-007: 机器字段并入 frontmatter——单工具双读，不拆分独立事实文件

### 状态

已接受

### 语境

agate 协议里散落在正文的机器读取字段（P1/P2/P6/P7 共约 40+ 个）此前靠正则从全文 grep 提取，长期存在格式摩擦——全角冒号、缩进错误、总结行误判等问题，v0.30.2 → v0.35.0 连续 5 个版本打同类补丁仍未根治。v2.0 需要一种机制把这些字段变成可靠的机器可读格式。P2 设计阶段对比了两条候选路径，完整权衡矩阵与选择理由见 `agate-workspace/archived/tasks/T001-v2.0-structured/P2-design.md` §1（T001 已 READY，任务目录已归档）。

### 决策

机器字段并入产出物已有的 frontmatter 块（`---` 分隔），由单一双读工具 `agate-md-field-get.py` 统一提供"frontmatter 优先 + 正则回退"的读取语义；不引入独立的 `.yaml`/facts 元数据文件，读取层也不按阶段拆分成多个 facts 工具。

### 理由

核心论点：agate 的产出者是 **LLM subagent**，不是人类程序员。"独立 YAML 文件更整洁"是人类程序员的常识，但对 LLM 而言"写两个文件并保持同步"是比"在一个文件头写一段 YAML"高得多的失败率来源——这是可行性评估与 P2-design.md §1 权衡矩阵得出的共同结论。选定方案满足硬约束"双读兼容在途任务旧格式"，且 fixture 改造量最小：354 个既有测试换血已是本任务最大成本，独立文件方案会把该成本再放大一档。

替代方案：为 P1/P2/P6/P7 各建一个独立 `.yaml` 事实文件（或集中 `metadata.yaml`），由专门的 facts 工具写入/读取 → 被否决。该方案在"schema 校验最简单""机读/人读终极分层"两个维度确实优于选定方案，但双文件同步漂移是新的"假一致"来源，且向后兼容需要额外迁移工具，与既定的双读原则冲突，fixture 改造量也会因每个用例都要断言第二个文件而进一步放大。

子决策（并入 frontmatter 后，读取层是否按阶段拆分独立 facts 工具）：同样否决——本任务迁移字段仅 16 个（去重后 14 键），拆分是面向"未来字段爆炸"的架构，对当前规模是过度设计（YAGNI）。

### 后果

- 单一工具承担全部读取逻辑，读取路径统一，无跨文件同步风险；既有调用点接口不变，5 个调用点零改动
- `agate-md-field-get.py` 会随每次新增机器字段持续增长（每个字段一个 op），长期需要关注该文件是否变得过于臃肿
- 若未来 op 数量过多，可以考虑按 P1/P2/P6/P7 拆分成多个读取函数，但仍应留在同一工具/同一文件内而不是拆成独立文件——保留"单文件写入、单工具读取"的核心优势，不因规模增长退回到被否决的独立文件路径

---

## ADR-008: orchestrator-template.md 符号链接接入，项目特定信息分离到可选 project.md

### 状态

已接受

### 语境

> 实现注记：本段为平台接入细节的决策记录（orchestrator-template 注册为 OpenCode/Claude Code 可调用 agent 的方式与符号链接细节缺失问题），属实现注记，非协议语义定义。

`orchestrator-template.md` 此前的接入方式是逐项目拷贝到 `docs/agents/orchestrator.md` 后手改 `agate_root`/`project_root` 两个 frontmatter 字段和一段内联的"项目特定约束"正文。这带来两个问题：(1) agate 升级模板（比如给"你不能做的事"清单加一条新规则）后，已部署项目的拷贝不会自动跟上，需要人工发现并手动同步，实际上从未真正发生过；(2) 协议文档从未讲清楚"怎么把这份文件注册成 OpenCode/Claude Code 真正能调用的 agent"这一步——只有一句"设为角色提示词"，平台相关的符号链接/默认 agent 设置细节完全缺失，新用户只能自己摸索。

### 决策

> 实现注记：本段为平台接入细节的决策记录（文件级符号链接注册到平台 agent 目录 `.claude/agents` / `.opencode/agents`，及 Windows 无符号链接权限的复制模式退化），属实现注记，非协议语义定义。

`orchestrator-template.md` 改为对所有项目内容完全一致，不含任何需要逐项目编辑的字段；`agate_root`/`project_root` 改为会话开始时运行时解析（环境变量兜底默认值），不再是静态 frontmatter 字段。标准接入方式是**文件级符号链接**直接指向 `orchestrator-template.md`（`.claude/agents/orchestrator.md` / `.opencode/agents/orchestrator.md`），不是拷贝。项目特定信息（工作区规则、gate 命令、测试基线等）迁移到一个新的、可选的 `{project_root}/docs/agents/project.md` 文件，由项目侧维护，orchestrator 固定读取。新增 `agate/SETUP.md` 记录完整接入步骤（含 Windows 无符号链接权限的复制模式退化）。

### 理由

核心论点：orchestrator.md 一旦对所有项目内容一致，就可以用符号链接代替拷贝，agate 升级模板即时对所有已接入项目生效，和 `~/.agate` 软链接让 gate 脚本自动跟随升级是同一套机制，不再是两套不一致的行为。项目特定信息独立成 project.md 而不是合并进已有的 AGENTS.md/CLAUDE.md，是因为受众不同——AGENTS.md 面向任何贡献者/Agent，project.md 只面向 orchestrator 这一个角色，塞进同一份文件会让通用开发指引膨胀、边界不清。

文件级链接而非目录级链接（链接单个 `orchestrator.md` 文件到平台 agent 目录，而不是把整个目录链过去），是为了避免把项目自己的其他文档意外暴露给平台的 agent 发现机制，也避免项目以后想在同一目录下注册别的自定义 agent 时被迫和 agate 管理的文件耦合。

### 权衡

> 实现注记：本段为平台接入细节的决策记录（OpenCode/Claude Code frontmatter 字段兼容实测结论），属实现注记，非协议语义定义。

- Windows 无符号链接权限（无开发者模式/非管理员）时退化为复制，牺牲自动同步能力——`agate/SETUP.md` 已文档化此权衡和退化步骤，目前没有自动漂移检测（`agate-summary.py` 现有的漂移检测只覆盖 `scripts/` 目录副本，不覆盖这个文件），是已知的手动步骤缺口
- `permission`/`mode`/`color` 等 OpenCode 专属字段和 Claude Code 需要的 `name` 字段共存于同一份 frontmatter——经实测确认 Claude Code 会静默忽略不认识的字段（不报错），OpenCode 会把不认识的字段归入通用 `options` 桶保留（不报错），两边互不冲突；但 Claude Code 缺少必填的 `name` 字段会导致整个文件被静默跳过（无警告日志），是本次改造过程中发现的一个容易复发的坑，`orchestrator-template.md`/`agate/SETUP.md` 均已加提醒

### 后果

- 新接入项目的操作从"拷贝+改字段"简化为"建两条符号链接命令"，`agate/SETUP.md` 是唯一权威步骤来源
- 已部署项目（拷贝方式）升级到本版本需要手动迁移：删除旧拷贝，重新按 SETUP.md 建立符号链接，项目特定内容搬进新建的 project.md——这是一次性、破坏性变更，已在 CHANGELOG.md 标注迁移路径
- `check-protocol-consistency.py` 的 `PROTOCOL_FILES` 加入 `agate/SETUP.md`，纳入 CHECK 2/3 结构性检查覆盖范围
- **v0.50.0 论据复核**：ADR-008 的类比"和 `~/.agate` 软链让 gate 脚本自动跟随升级是同一套机制"在版本管理机制落地后改为——orchestrator 模板仍符号链接接入（文件级，机制不变），但 **gate 脚本的"自动跟随升级"改由 `resolve-entry.py` 固定解析入口 + 项目 `.agate-version` 解析承担**（而非软链自动跟随），语义等价（切版本/升级无需重装），见 ADR-009

---

## ADR-009: ~/.agate 版本管理根目录 + resolve-entry 固定解析入口（v0.50.0）

### 状态

已接受

### 语境

`~/.agate` 是单一软链 → 指向某 checkout 的 `agate/` 子目录。`git pull` 后所有用 `~/.agate` 的项目**全部被动升级**，进行中项目被打断；hook 通过软链自动跟随，无法按项目隔离版本。需求（TAG0008）：项目 A 锁旧版、项目 B 用新版互不干扰，切版本不用重装 hook，存量单软链用户不破坏。

### 决策

- `~/.agate` 升级为**版本管理根目录**：`repo/`（唯一主仓库，首次 clone）+ `vX.Y.Z/`（`git worktree add` 检出 tag）+ `latest`/`current` 纯指针（POSIX 软链 / Windows 文本指针）+ `scripts/`（版本管理工具本体）。
- hook 从"指向具体版本脚本"改为装**固定解析入口** `resolve-entry.py`：运行时读项目 `.agate-version`（asdf 模式 cwd 向上找，`agate: vX.Y.Z` 精确版本）→ 解析版本目录 → exec 对应版本 gate py。解析优先级：AGATE_ROOT env 最高 → 项目声明 → current → legacy 软链兜底（无版本目录时软链目标本身 = AGATE_ROOT）。
- 新增工具：`agate-install.py`（安装/卸载/环境探测）、`agate-resolve.py`（解析查询）、`agate-pack-offline.py` + `install-offline.py`（外网打包 → 内网离线安装，平台核对 + checksum 校验）。
- `agate_common.resolve_agate_root` 扩展四层解析语义，作为全部 gate 脚本统一解析入口。

### 理由

1. **解析逻辑单一入口（DRY）**：3 个 hook 共用 resolve-entry，summary/其他脚本复用同一套解析，不散落三份（否决了"hook 直接内联解析"候选——重复实现 + 违反 Python 路线）。
2. **向后兼容红线**：无 current/latest 指针的 legacy 单软链布局直接把软链目标解析为 AGATE_ROOT（BDD-30），存量用户不跑新工具行为不变。
3. **resolve 失败回退稳**：任何解析失败回退 current 并 stderr 警告，绝不静默禁用 gate（hook fail-closed）。
4. **离线闭环**：内网机器无网络也能装版本（bundle 复制目录 + 平台核对 + checksum 校验）。

### 权衡

- `~/.agate` 从单软链变目录，存量用户需要文档指引（UPGRADING v0.50.0 章节）；但 legacy 兜底使无迁移动作也可继续用。
- Windows 无符号链接权限时 latest/current 指针退化为文本文件，解析器须兼容两形（复用 TAG0004 `.agate-root` 复制模式先例）。
- `git worktree add` 重复添加同一路径 exit 128 → 幂等须程序先判存在（BDD-3 依赖预判）。

### 后果

- 项目可经 `.agate-version` 锁定版本，切版本不用重装 hook（BDD-18）。
- `agate-summary.py` 语义迁移：显示项目解析到的版本 + 原因（而非仓库自身 tag）。
- 3 个派发脚本（agate-inject-card / agate-next-card / agate-render-dispatch-prompt）内联解析统一归口 `agate_common.resolve_agate_root`。
- 存量单软链用户无迁移动作（BDD-30 红线，31 条 BDD 全 PASS 验证）。

---

## ADR-010: 受控例外——满足客观可判定条件时允许复用既有验证证据

### 状态

已接受

### 语境

TAG0016（RM-AG0026）发现 P5→P6→P8 三个阶段对同一份代码重复跑全量测试/回归套件的成本问题：
refactor 任务 P6 验收要求独立产出 `regression.log`，P8 发布前又要求重跑一次 `gate_commands.P5`，
即使 P5 通过之后代码毫无变化。ADR-004 已确立"完整重跑是安全网，重复是特性不是缺陷"的哲学，
但该哲学没有为"验证点之间确定无改动"这种场景留出复用证据的口子，导致本可省略的重复验证被
无差别执行。

### 决策

在满足**客观可判定条件**时，允许复用已有验证证据、不重新执行验证，而非无条件要求每个验证点
独立重跑。判定标准必须机器可判定（呼应 ADR-002：不依赖主 Agent/subagent 的主观声明去判断
"是否可以复用"），且判定过程不信任 subagent 的自我报告（呼应既有 C7 规则"subagent 自我报告
不可信"精神）——由 gate 脚本读取 `.state.yaml` 的 `p5_pass_commit` 字段，用真实 `git diff`
比对目标区间是否存在非产出文件改动来做判定，不采信 P6-acceptance.md/P8-release.md 里的文字
声明本身。

### 理由

- **失败方向保守**：`P2-design.md` §3.2 论证了该机制不会产生"应重跑却被误判为可复用、从而
  跳过应有验证"的安全漏洞——判定误差只会导致"本可复用的场景被误判为需要重跑"，即多跑一次，
  不会少跑该跑的验证，不威胁既有回归底线。
- **残余风险已识别并有操作纪律缓解**：`P2-design.md` R9 指出真实反例（`5bdcd90` P5 commit
  混入了非产出文件的真实修复），若复发会破坏"父提交哈希与 P5 commit 自身哈希等价"这一判定
  前提；缓解措施是 `P5-verification.md` 明确操作纪律"P5 commit 不得混入非产出文件改动"，
  属轻量缓解而非机制性根治，与判定方向保守性共同构成风险可接受的论证。
- 替代方案：不引入复用机制、维持每个验证点无条件重跑 → 被否决，重复测试成本随任务/包数量线性
  增长且不随代码是否变化而降低，与 RM-AG0026 的诉求相悖；允许 subagent 自行声明"我判断可以
  复用" → 被否决，违反 ADR-002 可判定性原则，等同于把安全边界交给不可信的自我报告。

### 后果

- 本次落地为 `check-p6-provenance.py` 审计 7（`audit7_p5_evidence_reuse`，BDD-12/13）+ P6/P8
  两处应用（P6-acceptance.md「引用 P5 证据、不重跑」节 + P8-release.md P5 验证步骤）。
- 未来任何类似"复用而非重跑"的设计都应参照本 ADR 的判定标准：判定条件必须机器可判定、失败
  方向必须保守（宁可多跑不可少跑）、且必须显式声明"什么情况下判定为不可复用"，不是可以自由
  发挥的口子。
- 判定权始终归主 Agent（跑 gate 脚本拿判定结果），执行角色（verifier/implementer）不自行判断
  是否满足复用条件，只能在主 Agent 告知判定结果后据此产出对应格式的验收记录。

---

## ADR-011: 引导型 CLI 工具的权限是早纠错，不是安全边界

### 状态

已接受

### 语境

TAG0024（RM-AG0048 一期）新增 `agate-md-field-set.py`——给 subagent 提供"写入即校验"的结构化字段写入工具，替代手写 frontmatter。设计阶段（`docs/design-notes/design-md-field-set.md` §7.1/§7.4）需要回答一个后续任何"引导型 CLI 工具"都会重新遇到的问题：这类工具做的角色/字段权限检查（如"implementer 角色不能写 `status: approved`"）到底是不是一道安全边界？TAG0024 的 SELF-GATE 语义对齐审查（`docs/reviews/agate-alignment-review-2026-08-25-TAG0024.md` A7）指出这条原则目前只停留在 design note 里，未沉淀为协议级架构决策，与 `agate/adr.md` 现有 ADR 群体（ADR-001/002/004 均在讨论"谁能改什么、怎么保证不被绕过"）主题高度相关，建议补一条 ADR，避免同类工具未来重新论证一遍。

### 决策

`agate-md-field-set.py` 的角色/阶段/文件三维权限检查（选项 A）是**引导与早纠错机制**，明确**不是安全边界**。真正的防造假安全边界永远在 gate 链（`status`/`agent` 字段检查 + 事件账本 + 独立 judge 复核，TAG0020），不因 set 端存在权限检查而削弱或替代。任何后续"引导型 CLI 工具"（写入前做格式/权限/枚举校验，帮 subagent 少犯错）都应遵循同一条界限：工具层的权限检查只对"愿意走该工具通道"的写入者生效，其价值是"把 gate 事后打回提前为写入时引导"，不是"防住恶意绕过"。

### 理由

- **bash 命令没有身份概念**：任何 agent（主或 sub）都能绕开 `agate-md-field-set.py` 直接手写 frontmatter（现状本就允许，gate 不查"谁写的"），工具端权限检查对此无能为力——这是物理事实，不是设计疏漏，写清楚比假装它能防造假更诚实。
- **防"无心"，不防"恶意"**：工具检查捕获的典型场景是"implementer 误 set 了本该由 review 角色填的 `status: approved`"，工具拒绝并提示"该字段由 review 角色填写"——这阻止的是无心之失产生的、注定会被 gate 打回的字段，不是有预谋的绕过行为。
- **与既有 ADR 群体一致**：ADR-001（隔离性）、ADR-002（可判定性）、ADR-004（安全网分层——hook 兜底，主动验主流程）共同确立"真正的强制力在机器可判定的 gate/hook 层，不在任何单一执行环节的自觉"这一原则；本决策是同一原则在"引导型 CLI 工具"这一新工具类型上的直接延伸，不是新论点。
- 替代方案：让 set 工具的权限检查承担实际防伪造职责（如拒绝执行而非仅提示、要求额外身份凭证）→ 未采纳——bash 环境不具备可靠身份认证的技术前提，伪装成本极低（改个 `agent:` 参数即可），承诺一个做不到的安全边界比不承诺更危险（虚假安全感）。

### 后果

- `agate-md-field-set.py` 的角色白名单（基于 `assets/review-roles/*.md` 目录动态推导）在文档/代码注释中必须明确标注"引导，非安全边界"，不得让后续维护者误以为这是防伪造机制。
- 后续任何新增的"写入前校验/引导型"工具（不限于 frontmatter 字段），设计时应直接引用本 ADR，不必重新论证"这道检查是不是安全边界"——默认不是，除非能证明具备可靠身份认证前提（当前 agate 的 bash 执行环境不具备）。
- 真正的防造假责任持续压在 gate 链（`agent` 字段检查 + 账本 + 独立 judge）一侧，任何工具层引导机制的增减都不改变这条责任边界。

---

## ADR-012: 版本目录两形态 `_protocol_root` 探测序 + 根 `~/.agate/scripts/` 单源副本（TAG0032）

### 状态

已接受

### 语境

ADR-009 落地的版本管理布局（`~/.agate` = `repo/` + `vX.Y.Z/` + `latest`/`current` 指针 + `scripts/`）隐含一个假设：`git worktree add` 检出 tag 得到的**版本目录本身即协议本体**（`vX.Y.Z/scripts/` 直接存在）。这对「从改造仓库检出 `agate/` 子目录作 tag」的部署成立，但 **GitHub 直装**（RM-AG0058 / TAG0032 断点二）得到的版本目录是 agateon **整仓**——协议在 `vX.Y.Z/agate/` 子目录，`_resolve_version_info` 返回仓库根 `vdir` 会让下游 gate 路径 `vdir/scripts/<gate>` 取不到。此外 ADR-009 §决策只写「`scripts/`（版本管理工具本体）」，未规定根 `~/.agate/scripts/` 的**建立方式**（副本 vs 软链）、刷新时机、被删影响——TAG0032 断点一（入口断链）要求它在新机稳定存在、`repo/` 被删也不失效。这两项是 ADR-009 未设想的形态与未定义的语义，`docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md` A7 建议补 ADR 固化，避免后续任务重新论证。

### 决策

**(a) 版本目录两形态 + `_protocol_root(vdir)` 探测序（TAG0032 决策 A1）**

`agate_common._resolve_version_info` 命中版本目录后，经新增 helper `_protocol_root(vdir)` 按固定顺序定位协议根：

1. **探测序 1**：`isdir(vdir/scripts)` → 返回 `vdir`（**「根即协议」形态**——`git worktree add` 出的版本目录本身即协议本体）。
2. **探测序 2**：`isdir(vdir/agate/scripts)` → 返回 `vdir/agate`（**「元仓库整仓」形态**——GitHub 直装，协议在 `agate/` 子目录）。
3. 两形态皆无 → 返回 `vdir` 原样，下游 `resolve-entry.py` 拼 `<root>/scripts/<gate>` 不存在时命中既有 fail-closed 分支（exit 1），不新增静默放行。

**探测序不可颠倒**（红线）：若先探 `vdir/agate/scripts`，某些「根即协议」且恰好含 `agate/` 子目录的既有部署方会被改判协议根 → 破坏 ADR-009 §理由 2 的向后兼容红线。「探测序 1 先」保证既有部署方零回归。消费方（`agate-resolve.py` / `agate-summary.py` 经 `resolve_version_root`；`resolve-entry.py` 经 `resolve_hook_root`）均经 `_resolve_version_info` 单点归口，自动受益，无旁路。`.agate-version` 格式、`AGATE_ROOT` env 覆盖契约、legacy 软链兜底分支均不改。current 链分支须**先** `version = os.path.basename(cur)` **再** `root = _protocol_root(cur)`，顺序倒置会让 `AGATE_VERSION` 从 `vX.Y.Z` 回归为 `agate`。

**(b) 根 `~/.agate/scripts/` = 单源副本（TAG0032 决策 B1）**

根 `~/.agate/scripts/` 是 `agate-install.py`（含 `latest` 别名）从当前 `current` 版本协议根（= `_protocol_root` 探测结果，`vdir` 或 `vdir/agate`）的 `scripts/` 目录 `shutil.copytree(..., dirs_exist_ok=True)` 出的**一份副本**，**非软链**；随每次安装 / 升级重建刷新。真实 agateon 每个发布 tag 的 `agate/scripts/` 恒含全套版本工具（`agate-install.py` / `agate_common.py` / `resolve-entry.py` 等），故单源 copytree 即覆盖全部入口命令。`repo/` 或某个 `vX.Y.Z/` 版本目录被删**不影响**已建立的副本可用性（独立实体，不回链）。该副本**不参与 hook 版本解析**——hook 经 `resolve-entry.py` 固定入口按项目 `.agate-version` 解析版本，切版本无需重跑 `agate-install.py`。

### 理由

- **纯解析侧增量（A1 vs A2）**：候选 A2（install 侧把 `vX/agate/` 提升为版本根）会破坏 `git worktree add --detach` 检出目录与 `repo/` 索引的一致性（卸载路径 `git worktree prune/remove` 依赖），且变形逻辑要在 `install-offline.py` / Windows 复制模式每条安装路径各复制一份，外溢 out-of-scope。A1 是 1 helper + 2 调用点的解析侧单点增量，回滚 = 删调用；离线包 / 复制模式解析侧经同一 `_resolve_pointer_chain` 自然受益。
- **副本 vs 软链（B1 vs B2）**：软链方案下 `repo/` 或被指向版本目录被删 → 软链悬空 → `~/.agate/scripts/agate-install.py` No such file，正是断点一要消灭的症状；且 Windows 退化为复制后又需升级期重跑 → 跨平台双口径。副本方案跨平台语义单一、`repo/` 被删不断入口，代价（升级期须重跑 `agate-install.py latest` 刷新）明确、可单测锁、已写入 `UPGRADING.md`。
- **方向契合 ADR-009**：两项决策都守住 ADR-009 的纯增量 / 向后兼容红线——「根即协议」部署方零回归，legacy 兜底与 fail-closed 分支不动，未新增静默放行路径。

### 权衡

- 每次解析多 1-2 次 `os.path.isdir`——解析非热路径，可忽略。
- 根 `scripts/` 副本在升级期须重跑 `agate-install.py latest` 才刷新到新版本工具；不重跑则停留在上次安装的版本。已在 `UPGRADING.md`「版本管理生命周期」节写明，并有 BDD-4 判据 2 单测锁。
- 副本可能被用户手改而漂移——非 TAG0032 范围，`agate-summary.py` 已有 `scripts/` 目录副本漂移检测思路。
- 「元仓库整仓形态」是本次修复 RM-AG0058 断点二的坏路径（此前 resolve 返回仓库根导致 gate 取不到），本决策是修复而非行为翻转。

### 后果

- `agate_common.py` 新增 `_protocol_root` helper（`_resolve_version_info` 前），`.agate-version` ok 分支与 current 链分支各一处调用；`resolve-entry.py` / `agate-resolve.py` / `agate-summary.py` 零改动（受益方）。
- `agate-install.py` 新增 `_sync_root_scripts`（单源 copytree）+ `latest` 显式别名 + `_ensure_repo` 已有 repo 分支 `git fetch --tags --force --prune`（fail-open，令重跑发现上游更高 tag）；`install.sh` 新增 `--versions` bootstrap 分支（POSIX shell）。
- `agate/UPGRADING.md`「版本管理生命周期」节为该两项语义的单一权威口径；`agate/scripts/README.md` / `agate/AGENTS.md` / `agate/platform-notes.md` 做框架 + 指针，不复制完整对照表。
- 本 ADR 扩展 ADR-009（版本管理根 + resolve-entry 固定入口），不替代；ADR-009 的四层解析优先级与 legacy 兜底红线继续有效。

---

## ADR-013: 派发路由 / gate 生产者无关性（gate 不认谁生产的）

### 状态

已接受（2026-09-09，TAG0034 / RM-AG0060）

### 语境

TAG0034 引入配置驱动的跨 CLI / model 派发（派发路由）：同一阶段的产出可能由
主 Agent 当前平台的原生派发工具生产，也可能由另一个 CLI（claude-code / codex /
opencode）的子进程、或同厂商换 model 的 native 调用生产。这套机制能成立的前提，
是 gate 判定不因「谁生产了这份产出」而改变。

### 决策

**gate 只认产出文件 + exit code，不认谁生产的。** `check-gate.py` /
`check-judge-verdict.py` / `check-p6-provenance.py` 及一切 gate 脚本对跨 CLI / 跨
model 派发的产出**零特殊处理** —— 产出文件落 TASK_DIR（铁律 2/3 不变）、
gate_commands 的 exit code 客观可判，谁跑出来的都一样评。**未来不得为跨 CLI 派发
定制 gate**（不得新增「若产自 codex 则……」式分支）。

派发路由自身的留痕（`dispatch_route` 事件）与 gate 判定解耦：回落理由码枚举只有
`launch_fail` / `infra_error` / `no_parseable_output` 三值，无 `gate_fail`；
`check-events.py` 第 8 条机械拒绝任何非三值理由码。gate FAIL → 同一候选正常阶段
retry，绝不触发换候选。

### 理由

- **与 ADR-002（可判定性）一致**：gate 门槛机器可判定、不依赖主观声明 —— 跨 CLI
  产出与本地产出走同一 exit-code 判定面，是同一原则的直接延伸。
- **与 ADR-006（同源盲区）互补**：ADR-006 记录「同源模型隔离是认知层非真正独立」
  这一上限；派发路由给角色隔离补 model / 厂商维度是其部分缓解（见 LIMITATIONS.md
  局限 2），而「gate 生产者无关」正是这一缓解能安全落地的结构前提。
- **防完整性洞**：若 gate 因生产者而异，「换个模型 / CLI 试到 gate 放行」就成了
  绕过质量门槛的出口。生产者无关 + 回落理由码无 `gate_fail` 两条一起，把这个洞
  机械封死。
- **散文承载不够稳**：该红线目前只写在 `dispatch-protocol.md`「派发编排机制」新节
  的散文里，容易在后续编辑中被稀释；沉淀为 ADR 使其显式、可被 CHECK / 评审引用。

### 后果

- 跨 CLI 派发的产出若质量差 / 不完整，走的是「同候选正常阶段 retry」，不是「换
  候选」——retry 预算、`state_transition`、PAUSED 语义全部不变。
- 新增 gate 脚本时，若其判定逻辑试图区分产出来源，应视为违反本 ADR。
- 关联：RM-AG0060（派发路由 epic）、ADR-002、ADR-006、LIMITATIONS.md 局限 2。
