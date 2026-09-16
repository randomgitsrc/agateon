# Agateon MVWU Protocol — Design & Invariants

> **做什么**：把 agateon 既有的「批（batch）」实践升格为一等协议原语 **MVWU**（Minimum Verifiable Work Unit，最小可验证工作单元），定义其四个不变量、最小数据契约、消费点与实施次序。
>
> **为什么**：见 §1。核心是让「完成状态可机械验证」从任务级下沉到工作单元级——这是任何可验证并行（工作保持调度 / 任务级拆分 / 未来 DAG）的前置条件。
>
> **不做**：phase DAG（§8.1）；新建调度子系统（§8.2）；遥测作为状态权威（§8.3）；强制字段与全量声明（§8.4）。
>
> **性质**：设计提案（**未实现**）。本文只定义契约与不变量，不含实现。
>
> **平台**：协议数据面本身平台无关，但 `tests_filter` 是 shell 字符串——须遵循平台中立约定（Windows 常无 `make`、不裸 `python3`，见 §10；batch id 须 filename-safe）。
>
> **相关**：`agate/dispatch-protocol.md`（派发编排机制 / 五模式）、`agate/rules/dispatch.yaml`（`dispatch_plan` 机器字段）、`agate/scripts/check-p6-provenance.py`（七道 provenance 审计）、`agate/phase-cards/P4-implementation.md`（批级产出）、`docs/design-notes/design-dispatch-routing.md`（`resolve` 与 tier 轴）。
>
> **沿革**：由 `agateon-dag-orchestration-analysis` v5（分析§4.9 / 分析§11）导出——该分析实证了 MVWU 四不变量在既有实践中**已有机械锚点**，本文将其形式化。

---

## 1. 问题与动机

### 1.1 现状：批是执行切分，不是验证单元

`dispatch_plan.batches[]`（**`P2-design.md` 的 frontmatter 字段**；`agate/rules/dispatch.yaml` 只登记其 `field_readers`，**不含**该字段本身）目前只声明**执行**切分：批次 id 与复杂度。批的实际产物、验证证据、边界**没有结构化声明**。

但实证显示，**批在实践中已经承担了 MVWU 的全部职责**，只是以散文形式存在：

| 证据 | 内容 |
|------|------|
| 批级 commit 携带测试结果 | 实测 **26 条**（口径见下），如 `wf(TAG0034-P4): P4c 批 —— tmux 观测层（…pytest -k tag0034 = 90/0 全绿）` |
| 批自带测试文件 | `agate/tests/unit/test_tag0034_p4c.py`（221 行，P4c 批专属） |
| 批自带证据文件 | `TAG0034/P4-implementation-P4c.md`、`P4-dispatch-context-implementer-P4c.md` |
| 批边界可机械还原 | `git show --stat 92edcfc` 给出该批完整文件集 |

### 1.2 缺口：L0 验证是自律，不是机制

| 缺口 | 后果 |
|------|------|
| 批级证据在 commit message **散文**里 | 无结构、无标准位置、机器不可解析 |
| **没有任何 gate 消费**批级证据 | 批「完成」的判定完全依赖主 Agent 自觉（L0 验证 = 自律） |
| 批→测试映射 ad hoc | `pytest -k tag0034` 这类过滤器靠临场决定，无法预知、无法复用 |

### 1.3 为什么这比 DAG 更值得先做

- **DAG 的收益被三重天花板压缩**（真依赖 / 全量验证不可切片 / judge 全局屏障），实测关键路径弹性 ≈0（分析§4.5–4.8）
- 而「没有可流水的验证单元」正是天花板的根因——**MVWU 是解开它的钥匙**，且其锚点已存在（§3.5）
- 代价对比：MVWU **阶段 1 为零协议内核改动**（阶段 2 的批级 gate 才触及内核，见 §6 的「协议内核」边界定义）；DAG 则是协议内核重写（状态 schema + gate + hook + 审计链 + 破坏性变更迁移）

---

## 2. 定义

### 2.1 MVWU 定义

> **MVWU = 一个满足以下四个不变量的最小工作单元：明确的产出边界、可机械验证的完成证据、可追溯的 provenance、可组合性。**

它**不是**「一个 batch」的同义词——batch 只是当前的**载体**。

> **⚠ 1:1 假设的定位（重要）**：本文默认 **1 batch = 1 MVWU**，但这是**待试点证明的假设，不是协议先验规定**。
>
> - 现有证据只能支持：「既有实践中**反复出现 MVWU-like 模式**」（26 条批级 commit / 分母 47）
> - **不能**支持：「所有 batch 都已经是 MVWU」
> - 反向形态（1 batch 含多 MVWU / 1 MVWU 跨多 batch）**未被排除**，列入 §11 未决问题，由试点数据裁决
>
> 判定一个单元是否构成 MVWU，看它是否满足 §3 的四个不变量，**而非它的名字或数量关系**。

### 2.2 与既有概念的关系

| 概念 | 层级 | 与 MVWU 的关系 |
|------|------|--------------|
| **Task** | 人类意图 / feature | 由 1..N 个 MVWU 组成 |
| **Phase**（P0–P8） | 生命周期协议 | **正交**——MVWU 是执行粒度，phase 是阶段语义（§8.1） |
| **Batch** | 执行切分（现状） | MVWU 的**当前载体**；加声明后即为 MVWU |
| **Package** | 代码/模块边界 | MVWU 的**一种划分依据**（按包拆批），非唯一 |
| **Evidence** | 证明 | MVWU 的 I2 产出 |
| **Gate** | 可信判定 | MVWU 的消费点（§5），但 gate 不认谁生产（既有不变量） |

### 2.3 架构定位：MVWU 位于 Task 与 Agent Execution 之间

```
L1  Lifecycle Protocol   P0–P8
L2  Task Model           Intent / Task
L3  MVWU Layer           Executable + Verifiable Work   ← 当前缺失的一层
L4  Verification Layer   Evidence / Gate / Judge / Provenance
L5  Execution Layer      Claude / Codex / OpenCode / ...
```

**五个边界（守住则架构稳）**：

| 主体 | 不负责 |
|------|--------|
| Phase | 不负责拆工作 |
| Scheduler | 不负责证明正确 |
| Agent | 不负责宣布自己可信 |
| Telemetry | 不负责改变状态 |
| MVWU | 不负责成为新 runtime |

MVWU 回答的是一个此前没有名字的问题：**「Agent 应该被调度什么？」**——以前答案是 phase/batch/task，现在有了明确的最小单元。

### 2.4 最小默认原则（贯穿全文）

> **Minimal by default, explicit when risk requires it.**

- 未声明 MVWU = 沿用现状（batch 为隐含单元），**零新增字段**
- 仅当任务为**高风险 / 多切片 / 跨端**时，才要求显式声明边界与验证契约
- 任何新增字段必须有**消费方**（check 或 gate），否则不许加（§8.4）

---

## 3. 四个不变量

### 3.1 I1 — Boundary（边界）

> **声明边界必须与 git 实际 mutation set 机械一致**（`Declared Boundary = Actual Mutation`），而非"声明是实际的上位集"。

**为什么不是 ⊇**：若只要求"声明包含实际"，则 Agent 声明 `output: [src/auth/token.py]` 而实际改了 `config/production.yaml` 也算通过——`output` 就退化为 hint，I1 比 I2/I3 弱。故：

| 关系 | 判定 |
|------|------|
| 声明集 **=** 实际集（排除账本前缀后） | I1 **PASS** |
| 声明集 ⊂ 实际集（改了未声明的文件） | I1 **FAIL** |
| 实际集 ⊂ 声明集（声明了没改的） | I1 **WARN**（声明过宽，非越权） |
| 实际集含**声明允许的附带类别**（如测试文件、`CHANGELOG`） | I1 **PASS**（须显式声明 `allow_incidental`） |

**机械比对的可复用锚点**：`check-p6-provenance.py:64` 已有 `EXCLUDE_PRODUCE_PREFIX = "agate-workspace/tasks/"`——账本/证据路径由该前缀排除。**这同时解决了自指问题**：`P4-evidence/{batch}.log` 落在 `agate-workspace/tasks/` 下，自动不计入边界集。

**⚠ 可行性前提（实测发现，评审未覆盖）**：I1 的机械比对**要求该批有自己的 commit**。实测：

| 调度形态 | 实例 | commit 形态 | I1 可行性 |
|---------|------|------------|----------|
| **串行批**（`serial: true`） | `TAG0034` P4a/P4b/P4c | **每批一个独立 commit**（`92edcfc` = P4c 批） | ✅ **可机械比对** |
| **并行批**（`static-batch` 合并提交） | `TAG0023`「4批并行」→ `551e201` 单 commit；`TAG0031`「三簇并行」→ `9faf19a` 单 commit | **N 批共享 1 个 commit** | ❌ **git 无法按批归属文件集** |

**量化范围（同轴口径：frontmatter 批数 ≥2 的全部 16 个任务）**：

> **口径修正记录**：本节 v2 曾用「11 个 DAG 候选池任务」（分析 §4.6 的口径，轴 = **可并行**）来统计 I1 的 commit 粒度（轴 = **可归属**）——**两轴不同源，数字与实例均不成立**（其中 `TAG0019` 被误引为"2 批 2 commit"，实际其 `40a0a0c` 一个 commit 同时交付 core + docs-sync 两批）。现按同轴口径重算，并给出**三档可复现判据**：

| 判据 | 严格度 | 结果 | 说明 |
|------|-------|-----:|------|
| **A. 显式逐批**：commit subject 含 `-P4a`/`-P4b` 类子批后缀 | 最严（零歧义） | **1/16 = 6%** | 仅 `TAG0016`（`wf(TAG0016-P4a/P4b/P4c)`，3 批 3 commit） |
| **B. 人工核验逐批**：读 commit 与文件集，确认批↔commit 一一对应 | 中 | **2/16 = 13%** | A + `TAG0034`（`d1c2aca`/`99a4c19`/`92edcfc`，subject 用"P4a 批"中文形态） |
| **C. 宽松**：P4 commit 数 ≥ 批数 | 最宽（可能高估） | 6/16 = 38% | 含 `TAG0012`（8 批仅 1 commit）等**误判**，仅供参考 |

**采用 B 档（13%）作为结论依据**——A 档因命名习惯差异会低估（`TAG0034` 用中文"批"而非字母后缀），C 档会高估。

**已逐一核验的合并形态实例**（非抽样）：

| 任务 | 声明批数 | P4 commit | 关键证据 |
|------|---------:|----------:|---------|
| `TAG0012` | 8 | 1 | `27509a2` 单 commit（"12 个协议文件改动"） |
| `TAG0017` | 5 | 1 | `17a3a5d` "5 批并行" |
| `TAG0023` | 5 | 1 | `551e201` "4批并行"（subject 自述 4，frontmatter 5） |
| `TAG0007` | 4 | 1 | `1e9d74e` "4 批并行" |
| `TAG0027` | 4 | 3 | `57e5f1c` **B1+B2 合并** + B3a + 汇总 |
| `TAG0019` | 2 | 2 | `40a0a0c` **core + docs-sync 合并**；`c7a5355` 仅补 progress |
| `TAG0030` | 3 | 2 | `e39c897` 四 phase 单 commit + SELF-GATE 流程 commit |
| `TAG0008` / `TAG0024` / `TAG0031` / `TAG0032` / `TAG0021` / `TAG0022` | 2–4 | 1–2 | 均为合并/汇总形态 |

**一个额外的方法论发现**：**"批是否逐批 commit"在当前实践中没有稳定约定**——`TAG0034` 用"P4a 批"中文、`TAG0016` 用 `-P4a` 后缀、多数任务不做任何批级标记。这意味着 **I1 的机械校验不仅受 commit 粒度限制，还受命名约定缺失的限制**——即使批逐批提交，若无标记也无法机械归属。

**结论（定性结论经独立评审验证成立，量化已重算）**：

> **I1 的机械化在实测中只覆盖约 13% 的多批任务**（2/16，逐批 commit 形态）。**并行执行 ≠ 可独立归属。**

**因此 I1 的阶段 1 落地策略**：

| 形态 | 占比 | `output` 的语义 | verdict |
|------|-----:|----------------|---------|
| 逐批 commit | **13%**（2/16） | **可机械比对** | PASS / FAIL / WARN |
| 合并 commit | **87%**（14/16） | **自述边界**（无法机械验证） | **UNKNOWN**（诚实标注） |

**并且这为阶段 2 提出一个真实决策**：若要 I1 覆盖多数批，需推动「并行模式改为逐批提交」——但代价是失去统一 commit 的原子性（`dispatch-protocol` 模式 3 的现有语义）。**这是本设计不自行决定的取舍，交由试点数据 + 用户裁决**（列入 §11 未决问题）。

### 3.2 I2 — Verification（验证）

> **`tests_filter` 是「可执行的 verification selector」，不是 verification proof。**

一个 shell string 只回答"**跑了什么**"，不回答"**为什么这足以证明该单元正确**"。故 I2 不由 `tests_filter` 单独构成，而由**四段链**构成：

```
tests_filter（如何验证）
      ↓ 可复现执行
exit code + stdout/stderr + timestamp + git HEAD
      ↓ 落盘
P4-evidence/{batch}.log（验证实际发生了什么）
      ↓ 关联
git commit（验证针对哪个工作结果）
      ↓ 消费
Gate（验证这些是否满足协议）
```

| 概念 | 回答 | 载体 |
|------|------|------|
| `tests_filter` | 如何验证 | P2-design frontmatter |
| 证据日志 | 验证时实际发生了什么 | `P4-evidence/{batch}.log` |
| git commit | 针对哪个工作结果 | git |
| gate | 是否满足协议 | check（阶段 1 不阻断） |

**四者不得混同**——把"命令"当"证据"、或把"证据"当"放行依据"，都会重演既有失败模式（`gates` 字段沦为散文，分析 §5.1）。

**极简原则的体现**：不新增 `tests[{command,rationale,scope,expected}]` 这类重字段（那会突破 §4.2 的字段预算）；而是把**严谨性放在证据链**（可复现 + 可关联），而非放在声明字段上。

**既有锚点**：批自带测试文件（`test_tag0034_p4c.py`）+ 批级测试结果（commit message 实证 26 条）+ 批自带证据文件（`P4-implementation-P4c.md`）。

### 3.3 I3 — Provenance（可追溯）＝ linkage，不是 duplication

> **MVWU 不需要独立一套 provenance system**，只需能回答三问：
> 这个 evidence ← 来自哪次 execution ← 针对哪个 commit ← 属于哪个 MVWU。

**明确不做**：不为 MVWU 复制任务级 provenance（那会导出 `Task provenance` / `MVWU provenance` / `Batch provenance` / `Agent provenance` / `Test provenance` 的审计爆炸）。

| 层次 | provenance 形态 |
|------|----------------|
| Task | **成熟**——`check-p6-provenance.py` 七道审计（证据-结论对应 / BDD 总数对照 / 日志 EXIT_CODE 一致性 / P5 证据复用校验…） |
| MVWU | **最小 linkage**——evidence → execution → commit → MVWU 四元关联 |
| 未来 | 待数据证明需要，再下沉 provenance（**当前明确不下沉**） |

**既有锚点**：任务级七道审计 + `EXCLUDE_PRODUCE_PREFIX` 路径排除机制（`check-p6-provenance.py:64`）。

### 3.4 I4 — Composability（可组合）

> **多个 MVWU 可以组合成更大的 task。**

- **判据**：MVWU 之间可有向无环依赖，组合结果仍是一个合法 task
- **既有锚点**：任务级拆分实践（"写不出一句话 → 任务太大，考虑拆分"）+ 集成任务模式

### 3.5 不变量 ↔ 既有锚点映射（实证）

| 不变量 | 既有锚点 | 成熟度 | 缺口 |
|--------|---------|--------|------|
| **I1 Boundary** | 批级 commit 文件集（`git show --stat`） | 实证可用 | **未结构化声明** |
| **I2 Verification** | 批自带测试文件 + 批级测试结果 + 批级证据文件 | 部分结构化（文件在，结果在散文） | 结果无标准落点 |
| **I3 Provenance** | `check-p6-provenance.py` 七道审计 | **成熟**（任务级） | 未下沉到批级（可选） |
| **I4 Composability** | 任务级拆分实践 | 实践存在 | 无机械支持（可接受） |

> **核心结论**：四个不变量**都不是待建的新机制**。MVWU 的工作量在于「**把事实写成声明**」，而非发明子系统。

---

## 4. 数据契约（最小集）

### 4.1 声明位置

沿用既有载体，不新建文件：

| 声明 | 位置 |
|------|------|
| 单元清单 | `dispatch_plan.batches[]`（已有；位于 **`P2-design.md` frontmatter**，由 `agate-md-field-get.py` 的 `JSON_FIELDS` 读取，**仅 frontmatter、无正文回退**以防伪造） |
| 批→测试映射 | `batches[].tests_filter`（**新增，可选**） |
| 批级证据落点 | `P4-evidence/{batch}.log`（**新增约定**——沿用既有 `P{phase}-{kind}/` 命名模式，对照 `P6-evidence/` / `P5-test-results/`；**注意 `P4-evidence/` 目前不存在，是本次新建**） |

### 4.2 字段预算（硬约束）

> **显式 MVWU 声明 ≤ 5 个字段（含既有强制字段）。**

| 字段 | 必需性 | 消费方 | 来源 |
|------|--------|--------|------|
| `id` | **既有强制** | 批级 commit message / gate 定位 | `dispatch_plan.batches[]` 现状 |
| `complexity` | **既有强制** | `_gate_p2_dispatch_plan`（∈ low/medium/high） | 现状；**任何示例都不得省略** |
| `tests_filter` | 新增（可选） | I2：批级测试运行 | 本设计 |
| `output` | 新增（可选） | I1：与 git 文件集比对 | 本设计 |
| `risk` | 新增（可选） | 风险自适应（§5.3） | 本设计 |

**计数规则**：`id` + `complexity` 为既有的 2 个强制字段；本设计新增字段最多 3 个（`tests_filter` / `output` / `risk`），合计 ≤5。`deps` 因超出预算**不纳入**——且阶段 1/2 **明确禁止**（理由见 §11 问题 3）。

**超出即视为设计错误**——新增字段必须同时提交其消费方。

### 4.3 示例

**最小形态**（低风险任务，等价于现状 + `tests_filter`）：

```yaml
dispatch_plan:
  mode: static-batch
  batches:
    - id: auth-token-parser
      complexity: medium                       # 既有强制字段，不可省
      tests_filter: "pytest tests/auth/test_token.py"
    - id: session-store
      complexity: low
      tests_filter: "pytest tests/session/"
```

**高风险形态**（按需展开，仍 ≤5 字段）：

```yaml
dispatch_plan:
  mode: static-batch
  batches:
    - id: auth-token-parser
      complexity: high                         # 既有强制字段
      tests_filter: "pytest tests/auth/test_token.py"
      output: [src/auth/token.py]
      risk: high
```

---

## 5. 消费点

### 5.1 批级验证（阶段 1 的产物）

- **落点**：批级测试结果写入 `P4-evidence/{batch}.log`
- **消费**：主 Agent 在该批 commit 前运行 `tests_filter`，结果落盘 `P4-evidence/{batch}.log`（新建目录，随首个使用者出现）；commit message 保留一行摘要（人读）
- **性质**：**约定 + 一条 check**，不新增 gate 分支

### 5.1.1 `tests_filter` 失败时的语义（分阶段）

| 阶段 | `tests_filter` 非零退出 | 理由 |
|------|----------------------|------|
| **阶段 1（无 gate）** | **记录不阻断**——结果落 `P4-evidence/{batch}.log`，批仍可 commit；主 Agent 据证据决定是否继续 | 保持「零新增阻断面」；避免在无试点数据时引入新失败模式 |
| **阶段 2（批级 gate）** | **阻断该批完成**——需先修复或显式声明跳过 | 与既有「gate 判据只认产出 + exit code」一致 |

**与 P3 TDD 红灯的关系（评审 MUST-FIX 5，实测冲突）**：

实测批级 commit **本身就带预期红灯**——`d1c2aca wf(TAG0034-P4): P4a 批 —— 配置路由核心 + 引擎骨架 + 协议正文（**57 绿 / 3 批次边界红**）`。即批内可能存在**设计上应当红**的测试（属后续批的交付面）。因此：

| 规则 | 内容 |
|------|------|
| **scoping 规则** | `tests_filter` **只覆盖该批交付面**的测试（该批 `output` 涉及的测试文件），**不含**属后续批的测试 |
| **禁止全量** | `tests_filter` 不得写成全量套件（那是 P5 的职责，且会与分析§4.5 的全量屏障冲突） |
| **预期红声明** | 若该批确有设计上应红的测试（如为后续批预置的红灯），须在 `P4-evidence/{batch}.log` 显式声明 `expected_red: <测试名>`，否则红灯即批未完成 |
| **与 P3 的分工** | P3 `gate_commands.P3` = **任务级**红灯基线（保证"测试先于实现"）；`tests_filter` = **批级**交付面绿灯确认（保证"该批确实完成"）。层次不同、互不替代 |

**这使 §5.1.1 的"阶段 1 不阻断"更加必要**：在 `expected_red` 语义未落地前，批级红灯的判定不应阻断流程。

**MVWU verdict 四态定义（本节为权威定义，§7.2 的 check 实现据此）**：

| verdict | 触发条件 | 阶段 1 | 阶段 2 |
|---------|---------|--------|--------|
| `MVWU_RESULT: PASS` | 执行成功且无预期外红灯 | 记录 | 放行 |
| `MVWU_RESULT: FAIL` | 存在预期外红灯 | 记录 | **阻断** |
| `MVWU_RESULT: EXPECTED_RED` | 非零退出，但全部命中 `expected_red` 清单 | 记录 | 放行（附清单） |
| `MVWU_RESULT: UNKNOWN` | 命令不存在 / selector 解析失败 / 证据缺失或损坏 / 边界不可归属 / 超时 / 路径不安全 | **记录** | **阻断** |

> **`UNKNOWN` 不等价于 `PASS`，不得作为放行依据**（符合 agateon fail-closed 哲学）。
>
> **verdict 只观测、不改 `.state.yaml`**：`tests_filter → check → verdict ⇢ (observe only) ⇢ state`。这是「观测不得成为权威」（§8.3）在 MVWU 维度上的同一条原则。
>
> **实测含义**：因 §3.1 的 commit 粒度限制，合并提交形态的批 **boundary 必然判 `UNKNOWN`**——这不是缺陷，而是**诚实标注**；阶段 1 的职责正是**测出该比例**。

### 5.1.2 `P4-evidence/` 的消费方与登记点（评审 SHOULD-FIX 2）

新建目录**必须**回答"谁读它、在哪登记"，否则重演"声明了但无消费方"的失败模式。阶段 1 的答案须是**最小且明确**的：

| 问题 | 阶段 1 答案 |
|------|-----------|
| 谁读 | ① 主 Agent（commit 前查看，决定是否继续）② `P4-evidence/{batch}.log` 的**独立 check 脚本**（A2/A3 判据） |
| 在哪登记 | 不登记进 gate/hook 链（**不阻断**）；仅在文档约定 + check 脚本的默认扫描路径中 |
| 是否扩 judge 白名单 | **否**——`dispatch-protocol.md:404` 的 judge 输入白名单只许 `P6-evidence/`，**P4-evidence/ 不进白名单**（保持信息隔离不变）。**理由**：否则 implementer 自述的批级解释会直接污染 fresh-context judge |
| 未来边界（评审 §16） | judge 验证**结果**而非读取**过程**：`P4 MVWU evidence → P5/P6 aggregation → acceptance evidence → P6.5`，而非 `P4 evidence → P6.5`——fresh-context 的信任边界不变 |
| 是否进 provenance 审计面 | **否**（默认）——`check-p6-provenance.py` 是 P6 专用；如日后要纳入，须同步登记豁免/扫描规则 |
| 是否进目录登记 | **否**——`pre-commit-gate.py` / `agate-archive-stale-outputs.py` 的目录登记**不改**（阶段 1 零内核改动的前提） |

> **推论**：阶段 1 的 `P4-evidence/` 是**只增不挂**的旁路证据——这正是它零内核改动的原因，也是它的代价（无强制力，靠自律 + 事后 check）。

### 5.2 批级 gate（阶段 2，可选）

- 批完成判定 = 该批 `tests_filter` exit 0
- **注意**：这是**可选强化**，且必须遵守既有红线——「gate 判定只认产出文件 + exit code、不认谁生产的」

### 5.3 调度与路由输入（未来）

- **工作保持调度**：批完成即释放槽位（分析§9.2 路径 C）
- **风险自适应路由**：`risk` 字段可参与派发档位选择（与 `dispatch-routing.yaml` 的 tier 轴**正交**，不替代）

**但 `risk` 不是 authority（评审 §19-20）**：

| 允许 | 禁止 |
|------|------|
| `risk` 作为 **routing hint**（选档位/模型） | `risk: low` → 跳过 judge / 降低验证强度 |
| `declared_risk` 与 `evaluated_risk` 取 **max** | Agent 自述 `risk: low` 绕过 governance |

```
effective_risk = max(declared_risk, policy_risk, changed_surface_risk, production_scope_risk)
```

阶段 1/2 **只使用 `declared_risk`**；`evaluated_risk`（policy engine 推导）为未来位置保留。这与既有原则一致：**routing selection has no authority over correctness**。

---

## 6. 实施次序

**先定义「协议内核」边界**（本设计的成本论证以此为基准）：

> **协议内核** = `agate/` 下的协议本体与 gate 链：`.state.yaml` schema、`check-gate.py` 的 gate 分支、`phases.yaml`/状态机转移、`agate/rules/schema/*.json`、hook 三件套、`gate-events` 审计链。

| 阶段 | 内容 | 协议内核改动 | 非内核改动 | 前置 |
|------|------|-------------|-----------|------|
| **1** | `batches[].tests_filter`（**P2-design.md frontmatter 的可选键**）+ `P4-evidence/{batch}.log` 落点约定 | **无**（`_gate_p2_dispatch_plan` 不拒绝未知键，实测确认） | 一条**独立脚本** check（**不挂 gate、不阻断**）+ 约定文档 | 无 |
| **2**（可选） | 批级 gate（`tests_filter` exit 0 作为批完成判据） | **有**——需在 `check-gate.py` P4 分支或 hook 链登记 | — | 阶段 1 试点证据 |
| **3**（研究） | MVWU 级流水弹性度量 `E_pipeline` | **无**（只读分析脚本） | — | 阶段 1–2 数据 |

**自洽性修正**：v1 草稿把阶段 2 标为"改动：无"是**错的**——挂 gate 即是内核改动（须改 `check-gate.py` 分支或 hook 登记）。阶段 1 的"一条 check"是**独立脚本且不阻断**，故不构成内核改动；若要求它阻断，则自动升级为阶段 2 的成本。

> **本设计主张：先做阶段 1 试点（挑一个多批任务），再用试点证据决定阶段 2/3。**
>
> 理由：agateon 自身的演进路径是 `practice → evidence → invariant → protocol`。先写大而全的协议再落地，会重演「声明了但无消费方」的失败模式（对照 `phases.yaml` 的 `gates` 字段沦为散文，分析 §5.1）。

---

## 7. 试点方案（TAG-MVWU-001 的最小范围）

> **原则：Observe → Validate → Enforce**（不是 Design → Enforce）。

### 7.1 试点只做四件事

| # | 交付 | 不改 |
|---|------|------|
| 1 | `batches[].tests_filter`（**P2-design.md frontmatter 可选键**） | `.state.yaml` |
| 2 | `P4-evidence/{batch}.log` 落盘 | gate |
| 3 | `check-mvwu.py`——独立脚本，六项检查（见下） | P6.5 |
| 4 | 一个真实多批任务的试点记录 | scheduler |

### 7.2 `check-mvwu.py` 的六项检查（且仅此六项）

```
1. tests_filter 存在
2. command 可执行
3. evidence 存在
4. exit_code 可解析
5. git HEAD 可关联
6. verdict = PASS / FAIL / EXPECTED_RED / UNKNOWN
```

**输出 verdict，不改 state、不挂 gate、不阻断**（§5.1.1）。

### 7.3 试点观察表（跑 5–10 个多批任务）

| MVWU | tests_filter | 耗时 | evidence | commit 形态 | boundary | verdict |
|------|-------------|------|----------|------------|----------|---------|
| A | `pytest tests/a` | 8m | ✓ | 逐批 | exact | PASS |
| B | `pytest tests/b` | 12m | ✓ | 逐批 | exact | PASS |
| C | `pytest tests/c` | 5m | ✓ | 合并 | 不可归属 | **UNKNOWN** |
| D | … | 19m | ✗ | — | — | UNKNOWN |

> **注意 C 行**：合并 commit 形态下 boundary **必然** UNKNOWN（§3.1 实证：87% 的多批任务如此，14/16）。这不是失败，而是**诚实标注**——阶段 1 的职责是**测出这个比例**，而非假装可验证。

**要回答的三个问题**（决定是否进入阶段 2）：

| # | 问题 | 若答案否定 |
|---|------|-----------|
| Q1 | `tests_filter` 是否在多数批上稳定可执行？ | 停止，回炉设计 |
| Q2 | 边界（I1）是否在多数批上可机械比对？（**§3.1 实证：仅 13% 的多批任务为逐批 commit，2/16**） | I1 降级为自述 + UNKNOWN；并触发 §11 问题 6 的提交形态取舍决策 |
| Q3 | 1 batch = 1 MVWU（§2.1）是否成立？ | 修订 1:1 假设，考虑其他载体 |

### 7.4 阶段推进的判据

```
Q1 ∧ Q2 稳定成立（≥90% 批） →  进入阶段 2（批级 gate）
否则                        →  停在阶段 1，或回炉
```

**在阶段 1 数据出来前，不得进入 gate**——这是本设计的核心纪律。

## 8. 非目标与红线

### 8.1 不做 Phase DAG

Graph 属于 **Phase 之下**，不属于 Phase 之内。phase 同时承担 lifecycle / role / artifact / gate / retry / retreat / evidence / state 八重语义；让它成为 DAG 节点会导致协议复杂度爆炸。

### 8.2 不新建调度子系统

MVWU 是**既有 batch 的声明化**，不是新的执行引擎。调度仍由主 Agent 的编排模式（`dispatch-protocol` 五模式）承担。

### 8.3 遥测不得成为状态权威

| 遥测 → 允许 | 遥测 → 禁止 |
|------------|------------|
| 调度输入（该派谁、有无空闲槽位） | 直接判 phase 失败 |
| 调查触发器（FROZEN/SPIN → 核查） | 自动中止 / 改状态 |
| 统计与弹性计算 | 写入 gate 判定依据 |

**与 RM-AG0055 既有原则一致**：命令流检测输出「定位证据 + 触发核查、**不自动判死**」。观测与正确性必须分离。

### 8.4 反官僚化（硬约束）

| 规则 | 内容 |
|------|------|
| 最小默认 | 简单任务零新增字段 |
| 风险触发 | 仅高风险/多切片/跨端要求显式声明 |
| 字段预算 | 显式声明 ≤5 字段 |
| 消费方律 | 无消费方的字段不许加 |

---

## 9. 验收与度量

### 9.1 设计验收（可机械校验的判据）

| # | 判据 | 校验方式 |
|---|------|---------|
| A1 | `tests_filter` 字段存在时，`dispatch_plan` 校验通过 | **`check-gate.py:743 _gate_p2_dispatch_plan`**（`check-dispatch-routing.py` 只管 `dispatch-routing.yaml` 的 tier/routes，**不校验 `dispatch_plan`**；`agate/rules/*.yaml` 由 `check-yaml-schema.py` + `dispatch.schema.json` 守护）（`dispatch_plan` 的既有校验归属；注意 `check-dispatch-routing.py` 校验的是 `dispatch-routing.yaml` 路由配置，**非** `dispatch_plan`）。因该函数**不拒绝未知键**，阶段 1 **无需改校验器**；若日后要强校验 `tests_filter` 格式，在同一函数扩展 |
| A2 | 声明了 `tests_filter` 的批，其证据文件存在且非空 | 新增 check（对照 `P4-evidence/{batch}.log`） |
| A3 | 批级证据文件被该批 commit 引用 | 复用 provenance 审计模式（I3 下沉） |
| A4 | 未声明 `tests_filter` 时：`_gate_p2_dispatch_plan` 返回值与改动前**逐字节相同** + 既有 34 任务 P2 gate 全绿（可执行判据，替代原"逐字节一致"的模糊表述） | 回归测试 + 全量 P2 gate 复跑 |

### 9.2 流水弹性度量

$$E_{pipeline} = \frac{T_{barrier} - T_{optimal}}{T_{barrier}}$$

按 **MVWU 级**（非任务级）统计，按项目聚合。**11/34 这类任务级快照不作为决策公式**（分母会随 MVWU 落地而变）。

### 9.3 DAG 的 Research Trigger

```
if MVWU-level E_pipeline > threshold:  investigate DAG
else:                                  do not implement DAG
```

**DAG 不进 roadmap 功能列表**，而是条件触发的研究项。

---

## 10. 迁移与兼容

| 场景 | 行为 |
|------|------|
| 存量任务（34 个 + 下游项目） | **零动作**——未声明 MVWU = 沿用现状 |
| 新任务 | 默认可不声明；多批任务建议声明 `tests_filter` |
| 下游项目（如 PeekView） | 同上；`make test-quick` 等既有命令可直接作为 `tests_filter` 值 |
| 版本语义 | **非破坏性**——全为可选字段 + 新约定，不改 `.state.yaml` schema |
| 平台 | **需显式约束，不能简单称"平台无关"**（评审 SHOULD-FIX 4）：`tests_filter` 是 shell 字符串，但 ① Windows 常无 `make`（应写 `python -m pytest` 而非 `make test-quick`）② 不裸 `python3`（须遵循既有 `python3\|python` 探测约定，见 `DEBT0014` / `AGATE_PYTHON`）③ `P4-evidence/{batch}.log` 的 `{batch}` 源自自由字符串 `id`，**须约束为 filename-safe 字符集**（`[A-Za-z0-9._-]+`），否则路径注入/跨平台文件名风险 |
| 审计豁免 | 新建的 `P4-evidence/` 是否纳入 `check-p6-provenance.py` 扫描面，由阶段 1 试点决定；**默认不纳入**（避免扩大审计面）——如需纳入，须同步登记豁免规则（对照 `.heartbeat*` 的既有豁免先例） |

---

## 11. 未决问题

1. **`tests_filter` 的粒度**：一个批一个过滤器，还是一个批多个（单元/契约/静态）？后者更接近完整 MVWU，但字段预算（§4.2）需要重新论证。
2. **批级证据与 P6 provenance 的关系**：I3 是否要下沉到批级？任务级审计已成熟，下沉收益需试点数据支撑（避免为对称性而加复杂度）。
3. **`deps` 字段——阶段 1/2 明确禁止**（评审 §18 采纳，从"未决"升级为"禁止"）：一个 `deps` 字段会立刻打开半个 DAG 地狱（依赖类型 artifact/interface/test/execution/provenance × 跨任务与否 × 环检测 × 失败传播 × retry 传播 × 部分完成）。**仅当** MVWU 级 `E_pipeline` + 依赖需求 + 多任务证据三者同时达阈值，才研究 typed dependency model。
4. **E_pipeline 的 threshold**：阈值取值需要先有阶段 1–2 的实测分布，本文不预设。
5. **MVWU 的最小载体**：batch 是当前唯一载体；是否允许「一个 batch 含多个 MVWU」或「一个 MVWU 跨多个 batch」？本文默认 1:1（**待试点证明**，§2.1）。
6. **并行模式的提交形态（§3.1 实证驱动，需用户裁决）**：实测 **87% 的多批任务（14/16）是合并 commit**，导致 I1 无法机械验证。是否推动「并行模式改为逐批提交」？代价是失去统一 commit 的原子性（`dispatch-protocol` 模式 3 现有语义）；不推动则 I1 只覆盖 13% 的多批任务（2/16）。**本设计不自行决定**。

---

## 附录：证据索引

| 论断 | 证据 |
|------|------|
| 批级 commit 携带测试证据（**26 条**） | 命令：`git log --all --format=%s \| grep -E '^wf\(TAG00[23][0-9]-P[34]' \| grep -cE '绿\|passed\|通过\|测试'` → **26**（分母 47）。**口径声明**：subject 含测试结果语义词之一即计入；更宽口径（**全部** `wf(` 提交中含测试语义者）= **179**；全部 `wf(` 提交总数 = **490**（命令：`git log --all --format=%s \| grep -cE '^wf\\('`）。早期草稿的"25"来自一个未记录的临时正则，**不可复现，已废弃** |
| 批自带测试文件 | `agate/tests/unit/test_tag0034_p4c.py`（commit `92edcfc`） |
| 批自带证据文件 | `TAG0034/P4-implementation-P4c.md` / `P4-dispatch-context-implementer-P4c.md` |
| 批边界可机械还原 | `git show --stat 92edcfc` |
| provenance 七道审计 | `agate/scripts/check-p6-provenance.py:16-27` |
| `dispatch_plan` 权威位置 | **`P2-design.md` frontmatter**（`agate-md-field-get.py` `JSON_FIELDS={"dispatch_plan"}`；34 任务中 22 个含此字段）；`agate/rules/dispatch.yaml` 仅登记 `field_readers`/`gates`，**本身不含** `dispatch_plan`（grep 计数 0） |
| 误写位置的后果 | 若把 `dispatch_plan` 写进 `agate/rules/dispatch.yaml`，会被 `rules/schema/dispatch.schema.json`（`additionalProperties: false`）+ `check-yaml-schema.py` **拒绝** |
| `dispatch_plan` schema 契约 | `agate/scripts/check-gate.py:743` `_gate_p2_dispatch_plan`——校验 `mode` ∈ 5 模式 / `parallel_limit` ≥1 整数 / `batches` 为列表 / 批数 ≤ limit / 每批含 `id` 且 `complexity` ∈ {low,medium,high}；**不拒绝未知键**（故 `tests_filter` 为安全增量，无需改该校验器）；另注意 **`parallel_limit` 缺省时隐式上限 = 3**（`limit = parallel_limit if ... else 3`，`check-gate.py:767`） |
| gate 不认生产者 | `agate/dispatch-protocol.md`（派发编排机制） |
| 遥测不自动判死 | `agate/dispatch-protocol.md:1048`（RM-AG0055） |
| 关键路径弹性 ≈0 | `agateon-dag-orchestration-analysis` 分析§4.8 |
| 三重天花板 | 同上 分析§4.4–4.6 |
