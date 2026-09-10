# agate-md-field-set 结构化写入工具设计（RM-AG0048：字段写入通道）

> 状态：**RM-AG0048 一期已落地（TAG0024，v0.63.0，`agate-md-field-set`）；二期 backlog** ｜ 2026-08-25 用户拍板 Q1/Q2/D1
> 目标：给 subagent 提供"写入即校验"的结构化 set 工具，把协议字段填写从"手写 frontmatter"升级为"CLI 写入"——key 从 schema 白名单限定、value 写入时即校验、格式由工具保证，从机制上消灭"协议摩擦"类失败（P1-gate-diagnosis 实证），并作为防造假纵深的一环。
> 一句话：get 已有全套（agate-md-field-get.py / agate-state-get.py），set 完全缺失——本设计补齐"写"这一面，且用与 gate 同源（同一 schema + 同一校验值域）的方式实现，确保"官方 CLI 写出的东西天然过 gate"。

---

## 1. 问题定义

### 1.1 现状摩擦（实证，非假设）

`P1-gate-diagnosis.md`（TAG0023）记录了一起完全吻合的真实事故：主 Agent 派发 requirements-review subagent 时，prompt 里用 ``` 代码围栏展示 Header 示例，subagent 把示例里的围栏**字面复制**进产出文件，导致 `check-gate.py P1` 因 frontmatter 解析失败反复过不了。

根因不是"subagent 不认真"，而是**协议字段填写依赖 subagent 对协议的隐式理解**——它需要知道 frontmatter 是什么、key 叫什么、值合法范围是什么、格式长什么样。对 fresh-context、零协议知识的一次性 subagent 来说，这是结构性摩擦。

### 1.2 失败模式分类

手写 frontmatter 的失败可归为四类，全部可被工具消灭：

| 失败模式 | 示例 | 工具消灭方式 |
|---------|------|------------|
| 格式类 | ``` 围栏复制、缺 `---`、缩进错 | 工具自己生成标准 `---` 块（YAML 序列化）|
| 键名类 | `risks_level` vs `risk_level` | key 白名单拒绝 |
| 值类 | `status: Approve`、`risk_level: 高` | 写入时校验合法值域 |
| 一致性类（跨字段/跨文件）| P1 声明 render_component 但 P2 缺形态行 | 局部预检 + 剩余缺失报告（见 §5.4）|

### 1.3 设计目标

1. **消灭四类格式/键/值失败**：subagent 不再"写文本"，而是"调命令"。
2. **写入即校验**：set 写出的值 = 预校验过的值，天然过 gate（前提：与 gate 同源，见 §2.3）。
3. **自描述**：fresh-context subagent 只看工具输出就知道"怎么填、缺什么、怎么改"。
4. **不削弱防造假**：set 不得降低造假门槛（见 §7 权限定位），防造假仍以 gate 链为准。

### 1.4 非目标（明确不做，防范围蔓延）

- **不做内容评审**：set 只保证"字段合法"，不保证"正文设计得好"。内容质量由 review/judge 角色负责。
- **不替代正文产出**：subagent 仍用 Write 写正文，set 只负责 frontmatter——**唯一例外**是 gate_commands 正文 YAML 块（§5.1.1，经专用子命令整块替换，防半应用态）。
- **不做 .state.yaml 写入**（一期）：状态机语义更敏感，由 check-state-yaml + 状态转移脚本管理，set 化收益低、风险高。见 §8 二期边界。
- **不建立新安全边界**：set 的权限是"引导 + 早纠错"，不是 anti-tamper（见 §7）。

---

## 2. 核心洞察：这是"协议状态机的写入通道"，不是"文件编辑工具"

### 2.1 本质定位

把协议字段填写从"agent 手写文件、gate 事后校验"（自由文本通道）切换为"agent 通过工具写入、工具事前校验"（受控通道）。set 是**协议状态机写入端**的受控入口。

### 2.2 成败判据（一条）

> **一个零协议知识的 subagent，只看 dispatch-context 里的一行指令 + set 工具的输出提示，能否把字段填对。**

能 → 摩擦消除；不能 → 设计失败，无论功能多完备。所有接口决策都服务这条判据。

### 2.3 同源铁律（最重要设计约束）

set 的 **key 白名单、value 校验值域、frontmatter 格式**必须与 gate 读取端**同源**：

- key 白名单 ← `rules/phases.yaml` 的 `task_fields` ∪ `task-files.md` 通用 Header
- value 校验 ← 复用 `check-gate.py` / `agate_common` 的判定逻辑（不重写）
- 格式 ← 同一 YAML 序列化/解析约定

**推论**：如果 set 自建一套 schema 或校验，就制造了"set 说通过、gate 说不通过"的新不一致——**这正是 RM-AG0022 要消除的漂移，绝不能以新形式复活**。同源是通过 resolve-entry 版本解析链 + 共享 agate_common 读取器保证的（见 §6.3）。

---

## 3. 谁来用 / 如何知道用

### 3.1 直接使用者：被派发的 subagent

P1 analyst / P2 architect / P6 verifier 等在产出阶段调用。主 Agent 是间接使用者（gate 失败后可自己 set 修复，但它本就会手填，set 对它是省事不是必需）。

**边界声明**：set 只约束"**愿意走 set 通道**的 subagent"。绕开 set 直接手写 frontmatter 的行为（如主 Agent 或恶意者手动编辑文件）**set 完全管不到**——现状下主 Agent 手填就能过 gate（gate 只查 agent 字段≠main，不查"谁写的"）。因此 set 的角色权限只对"遵守协议的写入者"生效，这是"引导"定位的根本原因（见 §7.4）。

### 3.2 如何知道"用"：唯一通道是 dispatch-context，一行式

subagent 不会主动发现工具（它不看 agate/scripts/）。使用指令必须**显式写在 dispatch-context 里**，且是"照抄即用"形式：

```
产出文件字段：用 agate-md-field-set 填写（先 --list 看字段清单；set 失败就照提示改；不要手写 frontmatter）
```

**隐含要求**：dispatch-context 需同时写"gate 失败 = 报告主 Agent，不自己手改文件"。防止 subagent 遇 set 报错又退回手写——那就白做了。

### 3.3 派发 prompt 模板联动

`dispatch-prompt.md` 的"文件必须以这段 Header 开头（直接复制）"一节改为"字段用 set 填"。**把示例从 prompt 里拿走**——P1-gate-diagnosis 的根因正是"prompt 里的示例成了污染源"。

---

## 4. 范围框定：三层，不是一层

单层白名单不够，必须三层各司其职：

| 层 | 定义 | 谁决定 | 例子 |
|----|------|--------|------|
| **全局 schema 层** | 哪些 key 合法 + 值合法域（工具内置，随协议版本）| `rules/phases.yaml` task_fields + task-files 通用 Header | `status ∈ approved/rejected/draft`；`risk_level ∈ low/medium/high` |
| **任务/阶段层** | 本阶段**该填哪些**（阶段 schema 工具可知；任务语义不可知）| 阶段 schema ← phases.yaml task_fields；任务语义 ← dispatch-context | P2 阶段 schema 要求四字段齐全；"本任务 UI 是否受影响"是任务语义 |
| **文件/角色层** | 谁能 set 哪个文件的哪个字段 | 权限模型（§7）| review 角色才能 set P1-review.md status=approved |

**关键**：工具只做"全局层 + 阶段层"（key 存在吗、值合法吗、**本阶段 task_fields 该填哪些**），"任务层语义"（如"本任务 UI 是否受影响"）是 dispatch-context 的职责。两者不能混——工具从 `phases.yaml` 的 `task_fields` 能机械推导"P2 应含四字段"（这是阶段 schema，工具可知），但不知道"此任务具体声明什么值"（这是任务语义）。接口分工：dispatch-context 说"本任务是什么、要满足什么语义"，工具说"本阶段 schema 怎么填才合法"。

**为什么能报"剩余缺失"（§5.3）不矛盾**：set 读 `phases.yaml` 拿到该阶段 `task_fields`（如 P2 = candidate_count/packages/domains/ui_affected/gate_commands），对比当前文件已填字段即可报缺失——**这是阶段 schema 推导，不需要任务语义**。§4 表格中"任务/阶段层由 dispatch-context 决定"应精确理解为"任务语义层"；阶段 schema 层（该阶段有哪些字段、gate 要求哪些齐全）工具可知。

---

## 5. 工具接口设计（草案）

### 5.1 命令形态

沿用现有 get 工具的"环境变量传文件 + 子命令"惯例（与 agate-md-field-get 对称）：

```
agate-md-field-set <op> <value>            # 设置一个字段
agate-md-field-set --list                  # 列出本文件可填字段 + 当前值 + 缺失
agate-md-field-set <op> --help             # 该字段合法值 + 示例 + 当前值
```

- FILE 路径经环境变量传入（同 md-field-get / state-get 惯例，避免 shell 注入）
- 阶段判定：从文件 header 的 `phase` 字段读（或显式传参），确定可用 key 白名单（§4 阶段层）

### 5.1.1 list / 嵌套字段形态（一期边界）

不是所有字段都是标量。一期明确边界：

- **简单 list**（packages/domains/phases）：set 覆盖整个 list（`agate-md-field-set packages "foo bar"`，空格分隔，与 get 的 LIST_FIELDS 空格连接对称）。**不做 add/rm 增量**（一期增量无必要，覆盖即够）。
- **嵌套结构（gate_commands）**：**一期支持**（用户拍板 2026-08-25）。需区分两类形态：
  - **正文 YAML 块**（P2-design.md 的 gate_commands 块——`{P3: "cmd", P5: "cmd", P5_timeout_seconds: 300}`，在**正文**中，非 frontmatter，task-files.md §254 明确留正文）：用专用子命令 `agate-md-field-set-gate-commands FILE <yaml块>` 写整块（解析校验后替换正文块，经 `parse_gate_commands_block` 同源校验）；**不做逐 key 增量**（块级整体替换，防半应用态）。
  - **frontmatter dict**（P6/P7 等阶段的计数/汇总字段，如 `pass`/`fail`/`blocker_count`）：这些是证据字段（§5.10），一期 set **拒绝写入**（由验证脚本产生，见 §8 一期范围）。
- **int/bool 字段**（candidate_count / ui_affected）：set 做类型强校验（int 必须数字、bool 必须 true/false 小写），与 get 的 INT_FIELDS / BOOL_FIELDS 格式化约定对称。

### 5.2 自描述（成败关键，不是注释而是产品）

subagent 不知道 key 清单、不知道合法值。因此：

- `--list`：列出本文件应填字段 + 合法值 + 当前值 + 缺失项
- 错误信息**必须给出可用值和下一步**，而不是"非法"二字：

```
$ agate-md-field-set status Approve
ERROR: status 非法值 'Approve'，须 ∈ approved|rejected|draft（当前文件 status 未设置）
提示: P1-review.md 的 status 由 review 角色设置；其他角色无权填写
```

**设计原则：错误信息 = 可用值 + 归属角色 + 下一步。** 让 subagent"被引导着填"，不是"猜着填"。

### 5.3 写入即校验 + 剩余缺失报告

set 写完**立即跑该文件相关字段的局部校验**，exit 0 才算"可用"；通过时报告剩余缺失：

```
$ agate-md-field-set ui_affected true
OK: ui_affected=true 已写入 P2-design.md
剩余缺失: packages, domains, gate_commands（gate 会要求四字段齐全）
```

**为什么必须报告缺失**：subagent 在派发上下文里**看不到 gate 结果**（gate 是主 Agent commit 时跑的）。若 set 只报"写成功"，subagent 以为完成，主 Agent commit 时 gate 说"缺三字段"，又回到"来回改"——**正是要消灭的摩擦，绝不能以新形式复活**。

### 5.4 一致性类失败的预检（边界声明）

跨文件一致性（如 P1 ui_render_shape 与 P2 形态一致性）单文件 set 无法预检。诚实声明边界：

- set 的局部校验覆盖：**本文件内**的字段存在性、值合法性、阶段层字段齐全度
- 跨文件一致性：**不做**（由 gate 全量判定）
- 但 set 的 `--list` 应提示"该字段与 X 文件有跨文件一致性约束"（引导 agent 主动核对，而非假装预检）

### 5.5 原子写与失败模式

- **临时文件 + rename 原子写**：YAML 序列化失败/进程被杀不得留下损坏的 frontmatter（半途失败的 set 比手写更糟——agent 以为成功了）。
- 失败 → fail-closed：exit 非 0，**不落盘**，输出可操作错误。

### 5.6 文件不存在 / 无 frontmatter 的行为

subagent 可能先 set 字段再写正文（顺序不定），必须定义：

- **文件不存在**：set 创建文件（仅含 frontmatter 空壳 + 空正文占位），或拒绝并要求先 Write 正文？**建议拒绝**（set 不建文件，避免"set 建了个只有字段的空文件"被误当产出提交）——但 `--list` 在文件不存在时应输出"文件不存在，请先 Write 产出文件，再 set 字段"引导。
- **文件存在但无 frontmatter**：set 在文件头**插入** `---` 块（不破坏正文）；或拒绝并提示"请先按模板建 frontmatter"。**建议插入**（对旧格式文件，set 正好补齐 frontmatter，与 get 的"frontmatter 优先 + 正文回退"双读衔接）。
- **正文残留旧格式字段**：set 写入 frontmatter 后，get 双读优先读 frontmatter（语义正确），但正文残留旧字段会造成"一份文件两个值"的困惑。**建议 set 在写入时提示**"检测到正文含同名旧字段 `X`，frontmatter 优先，建议清理正文残留"（不自动删，防误伤）。

### 5.7 并发写同一文件

subagent 可能"Write 写正文"与"set 写字段"交替进行，也可能（异常时）两个进程同时操作同一文件：

- **set 的原子写（§5.5 临时文件+rename）天然防撕裂**：rename 是原子的，不会读到半写状态。
- **last-writer-wins**：set 只改 frontmatter，Write 只写正文——两者改不同区域，冲突概率低。但若 set 与 set 并发改同字段，后者覆盖前者（可接受，agate 单 subagent 单文件场景为主）。
- **set 不 hold 文件锁**（一期不做锁）：与"subagent 单写者"现实匹配，避免过度设计。二期若需多写者再评估。

### 5.8 set 后 gate 仍失败的处理（诚实预期管理）

set 消灭"格式/键/值"类失败，但**不保证 gate 全绿**——内容类、跨文件类检查（§5.4）仍需 gate 判定。预期管理：set 把"gate 失败原因"从"格式/字段"压缩到"内容/跨文件"，后者本就该由独立评审把关。**set 不是 gate 替代品，是摩擦削减器**——必须在 dispatch-context 写清"set 后仍可能 gate 失败（内容原因），报告主 Agent 而非继续改字段"。

### 5.9 set 与 git hooks / staging 的关系

set 只改工作区文件，**不自动 stage**（`git add` 是主 Agent / subagent 的显式行为，gate 在 commit 时跑）。明确：

- set 写完后文件处于 modified 未暂存状态，subagent 返回时主 Agent 统一 stage + commit → pre-commit 跑 gate。
- **set 不做任何 git 操作**（不 stage / 不 commit / 不 push）——保持单一职责，避免 set 意外提交半成品。
- 若 subagent 在 commit 前 stage 文件，gate 会先跑 `check-frontmatter.py`（§6.2）再跑 `check-gate.py`——set 生成的 frontmatter 必须过这两道（验收锚 1/7 覆盖）。

### 5.10 证据字段：一期拒绝写入（并入的"强制通道"半边）

**证据字段** = 由机械验证结果产生、不应被 agent 手写的字段：P6 `pass`/`fail`、P7 `blocker_count`/`deviation_count`/`design_gap_count` 等计数字段、P6.5 `criteria_total`/`criteria_passed`。

**一期行为**：set 对这些 key **直接拒绝**（`ERROR: pass 是证据字段，由验证脚本产出，不可手动填写`）——这是二期"证据字段强制通道"的**半边**（拒绝端），纯 set 侧约束、零风险，且比现状更安全（现状 agent 可以手写这些字段，gate 只校验格式不校验来源）。

**二期行为**（§8）：另一半——验证脚本运行后**自动落盘**这些字段（agent 不需要、也不允许手动写），这才是完整强制通道。

**为什么一期先做拒绝端**：零风险（不改任何 gate/账本判定）、立即消灭"agent 手写 pass/fail 造假或填错"的一类摩擦、且不阻塞二期。拒绝清单与 get 的 NO_FALLBACK_INT_FIELDS / NO_FALLBACK_BOOL_FIELDS 同源（§6.1）。

---

## 6. 与现有机制的关系

### 6.1 与 get 对称

`agate-md-field-set` ↔ `agate-md-field-get`（同一字段类型语义、同一 FILE 环境变量惯例、同一 agate_common 读取器）。

**精确化"set 的 key 白名单"**：不是 get 全部 ~40 个 op 的可写化——get 的 op 集含**读取专用**字段（如 `dispatch_plan` JSON、`mechanism_issues`/`execution_issues` 换行 list 等），set 只需覆盖**可写声明字段**子集。一期 set 白名单 = `task-files.md` 通用 Header（phase/task_id/type/parent/trace_id/status/created/agent）+ phases.yaml 各阶段 `task_fields`（risk_level/candidate_count/packages/domains/ui_affected/...）。类型语义与 get 对称（BOOL_FIELDS/LIST_FIELDS/INT_FIELDS/NO_FALLBACK_* 同源），保证"set 写的、get 读的、gate 判的"三者一致。

### 6.2 与 check-gate 同源

set 的 value 校验复用 check-gate.py 的判定（enum/int/bool/存在性）。**关键**：check-gate 的判定逻辑是"读端"，set 的校验是"写端"，两者共用同一 schema 源（phases.yaml + task-files），不各自实现。

**与 check-frontmatter 的兼容性（补充）**：set 生成的 frontmatter 必须能通过 `check-frontmatter.py` 的 schema 校验（pre-commit 会先跑它）。实现上 set 用 `yaml.safe_dump` 生成 frontmatter 块（`---` + YAML + `---`），与 get 的 `_read_frontmatter`（`yaml.safe_load`）及 check-frontmatter 的解析是同一 YAML 语义——**天然兼容，但需 BDD 验证**（验收锚 1 覆盖）。

### 6.3 版本一致性（防漂移）

agate 有 `.agate-version` + resolve-entry 按版本解析 gate py。**set 必须走同一 resolve-entry 版本解析链**——否则出现"set 按 v0.62 schema 写、gate 按 v0.63 读"的新不一致源，违反 RM-AG0022 消除漂移的目标。实现：set 复用 `agate_common.read_rules_yaml` + resolve-entry，与 check-gate 同版本解析。

### 6.4 与防造假链（gate-events 账本）的关系

- **一期**：set 不进账本。gate 账本保持现状（只记 gate 事件）。set 只是"写字段"，不改账本语义。
- **二期**（§8）：若做"证据字段强制通道"，set 的写入应生成结构化记录进账本（谁/何时/哪个文件/哪个字段/旧值→新值），作为防造假证据面。**这是二期，不是一期。**

---

## 7. 权限设计（定位：引导，不是安全边界）

### 7.1 必须诚实的定位

**bash 命令没有身份概念**。任何 agent（主或 sub）都能执行 `agate-md-field-set P1-review.md status approved`。所以 set 端权限**防不住恶意造假者**（恶意者可假装 judge 跑命令，或直接绕开 set 手写文件）。真正的安全边界在 gate（agent 字段检查 + 账本 + 独立 judge）——这一层不因 set 而削弱。

**必须讲透的空洞**：set 的权限只对"**愿意走 set 通道**的写入者"生效。任何 agent 绕过 set 直接手写 frontmatter（现状本就允许，gate 不查"谁写的"），set 完全管不到。因此 set 权限的真实价值**不是"防住谁"，而是"让遵守协议的 subagent 少制造注定被 gate 打回的字段"**——把"gate 事后打回"提前为"写入时引导"。

set 端权限做的是**防"无心"，不防"恶意"**：
- subagent 是 implementer 却 set `status: approved` → 工具拒绝："该字段由 review 角色填写" → **阻止它制造一个注定被 gate 打回的字段**。
- 这是 UX 层的引导 + 早纠错，**不是** anti-tamper 安全机制。

### 7.2 三维权限

1. **角色维度**：`status: approved` 只认 review/judge；`agent` 字段不可被 set 改写（防伪造身份）。
2. **阶段维度**：P1 阶段不能 set P2 字段（防越界污染）。
3. **文件维度**：P1-review.md 的 status 只能 set 进 review 文件，不能 set 进 requirements 文件。

**角色维度的实现方式（已决策：选项 A）**：纯 CLI 无法可靠知道"调用者是谁"（bash 无身份概念）。已决策采用：

- **选项 A（已决策 2026-08-25）**：从**文件现有 frontmatter 的 `agent` 字段**推断当前写入者——subagent 写文件 Header 时已带 `agent: {角色}`，set 读它做角色判定。局限：agent 可手写任意 agent 值（但那是它在文件里自己声明的身份，gate 同样以此判定——与 gate 同源，见 §7.3）。
- 选项 B（显式 `--as <role>`，任何人可传任意值，等同无校验）、选项 C（不做角色判定）——**否决**。

### 7.3 与 gate 端 agent 判定同源

建议 set 的"角色-字段"映射**复用 gate 端的 agent 判定语义**（check-gate 里 `agent=main 不可批准评审` 等），做到"set 说能填 ⇔ gate 说合法"——避免"set 允许、gate 拒绝"的二次不一致。

### 7.4 文档必须写明的声明

> set 权限是引导与早纠错，**不是安全边界**；防造假永远靠 gate 链（agent 字段 + 账本 + 独立 judge）。任何把 set 权限当安全边界的假设都是自欺。

---

## 8. 落地节奏（两阶段，2026-08-25 按用户拍板修正边界）

### 阶段一（本次）：完整写字段工具（自洽、安全、不动 gate/账本判定）

- set 服务**声明字段**：risk_level / ui_affected / candidate_count / status（status 绑定角色，Q1 已决策）/ 简单 list（packages/domains）/ **gate_commands 正文 YAML 块**（Q2 已决策，经 `agate-md-field-set-gate-commands` 块级替换，同源校验）
- **证据字段拒绝端**（§5.10）：pass/fail/blocker_count 等 set 直接拒绝——二期"强制通道"的安全半边，零风险
- `--list` / `--help` / 错误给合法值（自描述）
- 写入即局部校验 + 剩余缺失报告
- 角色/阶段/文件三维权限（角色维度用选项 A，§7.2 已决策）
- 原子写 + 版本一致 + 同源校验 + 跨文件约束"提示"（§5.4，不预检）
- dispatch-context 模板加一行式指令 + dispatch-prompt 改"用 set 填"
- BDD：含"零知识 subagent 照提示填对"的验收场景

**一期验收**：`check-gate.py` 与 `check-events.py` **判定零改动**（set 只写"gate 本就要校验的字段"，不改 gate 语义）；新增 `agate-md-field-set.py` + `agate-md-field-set-gate-commands.py` 两个工具 + 模板措辞 + BDD。

### 阶段二（后续，需单独 design note）：防造假机制演进

- **证据字段自动写入端**：验证脚本运行后自动落盘 pass/fail/blocker_count（agent 不允许手写）——与一期拒绝端合为完整强制通道
- **写入留痕进账本**（gate-events 新记录类型：谁/何时/哪个文件/哪个字段/旧值→新值）——**触碰 check-events.py 账本格式 + 哈希链兼容 + 审计语义，必须单独充分设计**
- 跨文件一致性预检（一期只做"提示"，二期评估是否升级为"预检"）
- `.state.yaml` set 化（评估后决定，倾向不做）

**边界理由**：一期是"写字段工具"，写的还是 gate 本就要校验的字段，gate/账本判定不变——所以安全。二期改变字段的**产生方式**（证据字段只能由脚本写）+ **记录谁改的**（账本），直接触碰防造假模型——这正是二期存在的真正理由，须单独设计 note。一期不碰 gate/账本，二期不阻塞在一期范围内。

---

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| set 建独立 schema → 与 gate 不一致 | 同源铁律（§2.3）：复用 phases.yaml + check-gate 判定 + resolve-entry 版本链 |
| set 权限被当安全边界 → 自欺 | §7.4 强制声明：引导非安全；防造假靠 gate 链 |
| 半途失败留损坏 frontmatter | §5.5 原子写 + fail-closed 不落盘 |
| subagent 报错后退回手写 | §3.2 dispatch-context 明写"报主 Agent 不手改" |
| set 报"写成功"但 gate 仍失败（跨文件）| §5.4 边界声明 + 剩余缺失报告，不假装预检跨文件一致性 |
| 版本漂移（set 按旧版 schema 写）| §6.3 走 resolve-entry 版本链 |
| 增加 subagent 行为契约复杂度 | 派发 prompt 讲清"何时 set / set 失败怎么办 / 谁负责最终校验" |

---

## 10. 验收锚

**阶段一验收锚**（供 BDD 使用）：

1. `agate-md-field-set P2-design.md packages "foo bar"` 写入成功，`agate-md-field-get` 能读回同值，`check-gate.py P2` 通过（该字段相关检查）。
2. 非法 key（`risks_level`）→ 拒绝 exit 非 0，输出"合法 key 清单"。
3. 非法值（`status Approve`）→ 拒绝，输出"合法值 + 归属角色 + 下一步"。
4. implementer 角色尝试 `status approved` → 拒绝，提示归属角色。
5. `--list` 输出本文件可填字段 + 当前值 + 缺失，与 phases.yaml task_fields 一致。
6. 零协议知识 subagent 场景（BDD 可测化）：构造一个**不含任何协议知识**的模拟调用序列——脚本只给 subagent 一条指令"用 set --list 看要填什么，照提示填"（模拟 dispatch-context 一行式），subagent 的"行为"即"按 set --list 输出逐项 set"；断言：最终 `--list` 无剩余缺失、`check-gate.py P2` 通过（该字段相关检查）。**此验收锚验证的是"set 的自描述输出足以引导填写"，而非真实派发 LLM**（真实 LLM 行为不可在 BDD 中确定性断言）。
7. set 写入后 `git diff` 只含 frontmatter 变更，无正文破坏；原子性（模拟失败不落盘）。
8. 文件不存在时 set → 拒绝 + 提示"先 Write 产出文件再 set"；文件无 frontmatter 时 set → 插入 `---` 块且不破坏正文（§5.6 两分支各一锚）。
9. 正文含同名旧字段时 set → 输出残留提示（不自动删）；`--list` 在文件不存在时输出引导而非报错（§5.6/§5.4）。
10. `agate-md-field-set-gate-commands` 写入合法块 → `parse_gate_commands_block` 能解析、`check-gate.py P2` 通过；非法块（未声明 key / 非法 `_timeout_seconds`）→ 拒绝 + 可操作报错（§5.1.1）。
11. set `pass`/`fail`/`blocker_count`（证据字段）→ 拒绝 + 提示"证据字段由验证脚本产出"（§5.10）。

---

## 11. 决策记录与开放问题（2026-08-25 更新）

**已决策**（用户拍板）：

1. **status 角色绑定：一期做**。它是"防造假前提"的最直接体现，gate 端 `agent=main 不可批准` 判定已存在，复用成本低。
2. **gate_commands：一期支持**（经 `agate-md-field-set-gate-commands` 块级替换，正文 YAML 块，同源校验）。
3. **dispatch-context 模板措辞**：具体设计实施阶段再定（需与"分阶段落盘/命令超时兜底"节协调）。
4. **与 DEBT0019/0020 同批推进**（工具链 batch）。
5. **角色权限实现：选项 A**（读文件 frontmatter agent 字段推断，§7.2）。
6. **文件不存在→拒绝 / 无 frontmatter→插入 / 正文残留→提示不删**（§5.6，D2-D4 按建议定）。

**遗留待决策**：

- **一期/二期边界**已按本轮分析定为：一期=完整写字段工具（含 gate_commands + 证据字段拒绝端 + 跨文件提示）；二期=证据字段自动写入 + 账本留痕 + 跨文件预检（须单独 design note）。**"能一起做么"结论：大部分能并入一期，但账本留痕（触碰 check-events 哈希链）不能——那是二期存在的真正理由。**
