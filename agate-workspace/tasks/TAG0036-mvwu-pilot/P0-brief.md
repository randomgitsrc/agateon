# P0-brief — TAG0036 MVWU 试点（RM-AG0063 阶段 1）

> 主 Agent 亲自填写（P0 产出）。RM-AG0063（`agate-workspace/roadmap/roadmap.md`，backlog→scheduled）。
> **设计依据**：`docs/design-notes/design-mvwu-protocol.md`（v2.1，PR #319 已合并）——**本任务只做该设计的阶段 1**。
> **来源**：编排模型演进分析（`docs/design-notes/design-orchestration-evolution-analysis.md` v6.2）§4.9 / §11 + 三轮外部评审。
> **前置**：**无硬前置**（设计文档 §6：阶段 1 前置 = 无）。两个**软依赖**不阻塞本任务：① 活动遥测（本任务的 Q1 数据与遥测互补，非依赖）② TAG0035 fail-open（本任务阶段 1 **不挂 gate**，不受影响）。
> **与 TAG0035 的关系（已裁定）**：TAG0035 **先启动**（它先占住 `check-gate.py`，且是**本任务阶段 2** 的地基）；**两批文件面不重叠**——TAG0035 改既有脚本，本任务阶段 1 **新建 `check-mvwu.py`** + 改 frontmatter 约定，故**可并行**。
> **⚠ SELF-GATE 澄清**：本任务虽为"零**协议内核**改动"（不改 `.state.yaml`/gate/hook/审计链），但 `check-mvwu.py` 落在 `agate/scripts/*.py` → **仍命中 SELF-GATE 触发面**，须走 `protocol-alignment-review` + 全量 pytest + consistency。

## task

"在 agate 协议层做 **MVWU（最小可验证工作单元）阶段 1 试点**——把既有 batch 实践从『散文形态』升为『结构化声明』：新增 `batches[].tests_filter` 可选键与 `P4-evidence/{batch}.log` 证据落点，新建**不阻断**的独立 check 产出四态 verdict，并在真实多批任务上采集 Q1/Q2/Q3 数据。**不挂 gate、不改 `.state.yaml`、不改 P6.5、不改 scheduler。**"

### scope

**① `batches[].tests_filter`（P2-design.md frontmatter 可选键）**

- **位置**：`P2-design.md` 的 **frontmatter**（由 `agate-md-field-get.py` 的 `JSON_FIELDS` 读取，仅 frontmatter、无正文回退以防伪造）
- **形态**：
  ```yaml
  dispatch_plan:
    mode: static-batch
    batches:
      - id: auth-token-parser
        complexity: medium                       # 既有强制字段，不可省
        tests_filter: "pytest tests/auth/test_token.py"
  ```
- **零内核改动依据（实测）**：`check-gate.py:743 _gate_p2_dispatch_plan` 校验 `mode` ∈ 5 模式 / `parallel_limit` ≥1 整数 / `batches` 为列表 / 批数 ≤ limit / 每批含 `id` 且 `complexity` ∈ {low,medium,high}——**不拒绝未知键**，故新增 `tests_filter` 为安全增量。

**② `P4-evidence/{batch}.log` 证据落点（新目录约定）**

- **注意**：`P4-evidence/` **目前不存在**——现存的是 `P6-evidence/`（37 个）、`P5-test-results/`（34 个）、`P6.5-judge-evidence/`（1 个）。本任务**新建**该目录，沿用既有 `P{phase}-{kind}/` 命名模式。
- **最小内容**：
  ```
  command: pytest tests/auth/test_token.py      # 实际执行的 tests_filter
  exit_code: 0                                   # 机械校验锚点
  git_head: <sha>                                # 证据关联的工作结果（I3 linkage）
  timestamp: <ISO-8601>
  expected_red: []                               # 设计上应红的测试清单（默认空）
  ```
- **消费方与登记点（设计文档 §5.1.2）**：① 主 Agent（commit 前查看）② 独立 check 脚本。**不登记进 gate/hook 链**（不阻断）、**不进 judge 白名单**（保持信息隔离）、**不进 provenance 审计面**（默认）、**不改目录登记**（`pre-commit-gate.py` / `agate-archive-stale-outputs.py`）。

**③ `check-mvwu.py`（新建，独立脚本，不挂 gate）**

六项检查（**且仅此六项**）：
```
1. tests_filter 存在
2. command 可执行
3. evidence 存在
4. exit_code 可解析
5. git HEAD 可关联
6. verdict = PASS / FAIL / EXPECTED_RED / UNKNOWN
```
**四态 verdict 语义**（设计文档 §5.1.1）：`UNKNOWN` **不等价于 `PASS`，不得作为放行依据**；verdict **只观测、不改 `.state.yaml`**。

**④ 采集流程就绪（本任务**不**负责造样本，见下方「完成判据」）**

在**遇到真实多批任务**时运行并记录观察表：

| MVWU | tests_filter | 耗时 | evidence | commit 形态 | boundary | verdict |
|------|-------------|------|----------|------------|----------|---------|

**三问（决定是否进入阶段 2）**——各自的数据状态**不同**，须分开对待：

| # | 问题 | 当前数据状态 | 若否定的后果 |
|---|------|-------------|-------------|
| **Q1** | `tests_filter` 是否在多数批上稳定可执行？ | ⚠️ **需真实样本** | 停止，回炉设计 |
| **Q2** | 边界（I1）是否在多数批上可机械比对？ | ✅ **已有答案**：**13%**（16 个多批任务中 2 个逐批 commit——实测于设计文档 §3.1） | I1 降级为自述 + `UNKNOWN`；**并触发提交粒度取舍决策** |
| **Q3** | `1 batch = 1 MVWU`（设计文档 §2.1）是否成立？ | ⚠️ **需真实样本** | 修订 1:1 假设，考虑其他载体 |

**推进判据**：`Q1 ∧ Q2 稳定成立（≥90% 批）` → 才可进入阶段 2（批级 gate，**独立任务**）；否则停在阶段 1 或回炉。

### 完成判据与样本依赖（本任务边界的关键澄清）

> **本任务交付的是「工具 + 采集能力 + 已有结论」，不是「三问全答」。**

| # | 完成判据 | 状态 |
|---|---------|------|
| 1 | `batches[].tests_filter` 键可用（frontmatter 可写、可读、不破坏既有 P2 gate） | 本任务可完成 |
| 2 | `P4-evidence/{batch}.log` 落点约定生效（含最小内容格式） | 本任务可完成 |
| 3 | `check-mvwu.py` 可用（六项检查 + 四态 verdict + 不阻断） | 本任务可完成 |
| 4 | **Q2 结论在案**（13%，引用设计文档 §3.1 的实测） | **已完成**（不需试点） |
| 5 | **Q1/Q3 的采集流程就绪**：任何后续多批任务出现时，能**自动产出**观察表行 | 本任务可完成 |
| 6 | 至少 **1 个真实样本**的观察行（**若本任务自身拆批提交，自身即样本**） | 视交付方式 |

**为什么 Q1/Q3 需真实样本**：Q1 问"`tests_filter` 是否**稳定可执行**"——历史任务当时**没有**该字段，事后"推断一个当时该跑什么"**测不出当时的可执行性**；Q3 问"1 batch = 1 MVWU 是否成立"，需要真实的批产出与证据对应关系。**两者都无法从历史数据事后补出。**

**为什么不主动造样本**：专门构造试点任务会引入"自己验证自己"的偏差（测试为通过而写）。**样本应来自自然发生的多批任务**——本任务的职责是**保证样本出现时能采集**，而非制造样本。

**与阶段 2 的衔接**：本任务完成后，状态为「**工具就绪 + Q2 已答 + Q1/Q3 待自然样本**」；阶段 2 的启动条件仍是 `Q1 ∧ Q2 ≥90%`，其中 **Q1 需等自然样本累积**。**在 Q1 有数据前不得进入阶段 2**（设计文档 §7.4 纪律）。

### known_risks

- **I1 可归属率仅 13%（实测，本任务最大风险）**：16 个多批任务中仅 2 个为逐批 commit（`TAG0016` 用 `-P4a` 后缀、`TAG0034` 用中文"P4a 批"）；**87% 为合并 commit**（`TAG0012` 8 批→1 commit 等）。**合并提交形态下 boundary 必然判 `UNKNOWN`**——这不是缺陷而是**诚实标注**，但意味着 Q2 的结论很可能是"多数不可机械比对"。
  - **缓解**：把 Q2 的产出定义为**比例数据**（而非通过/失败）；若比例过低，触发设计文档 §11 问题 6 的**提交粒度取舍**（保持合并 commit 保原子性 vs 改逐批 commit 换可归属）——**该取舍须由用户裁决，本任务不自行决定**。
- **"批是否逐批 commit"无稳定命名约定**（实测）：`TAG0016` 用 `-P4a`、`TAG0034` 用中文"P4a 批"、多数任务不做任何批级标记。**即使批逐批提交，无标记也无法机械归属** → 本任务的 check 需容忍 `UNKNOWN`。
- **`tests_filter` 的平台中立性**：shell 字符串须遵循平台约束（Windows 常无 `make` → 应写 `python -m pytest`；不裸 `python3`，须遵循 `AGATE_PYTHON` 探测约定，见 DEBT0014）；`{batch}` 源自自由字符串 `id`，**须约束为 filename-safe 字符集**（`[A-Za-z0-9._-]+`）。
- **与 P3 TDD 红灯的冲突（设计文档 §5.1.1 实测）**：批级 commit **本身就带预期红灯**（`d1c2aca wf(TAG0034-P4): P4a 批 —— …（57 绿 / 3 批次边界红）`）。故 `tests_filter` 须有 **scoping 规则**（只覆盖该批交付面、禁止全量）+ `expected_red` 声明，否则红灯即判未完成是错的。
- **样本可得性（本任务最大不确定性）**：Q1/Q3 需**真实多批任务**样本，而**当前 34 个任务已全部完成**，无在途多批任务。**缓解**：本任务的完成判据**不含**"Q1/Q3 已答"（见上方「完成判据与样本依赖」）——交付"采集能力就绪"，样本到来时自动产出观察行。
  - **不可用的方案（已排除）**：用历史任务"回填" `tests_filter` 来凑数——**回填的 `tests_filter` 是事后推断（推断当时该跑什么），既非当时的真实行为，也测不出"当时是否可执行"**（Q1 的定义），**属自欺**。历史数据**只用于只读统计**（如 Q2 的 13% 已是实测值，无需回填），**不改任何历史任务产物**。
- **本任务自身是否作为试点样本**：TAG0036 若拆批提交，自身即是多批任务——**可作为首个样本**，但需注意"自己验证自己"的偏差（参照 P6 provenance 的单 author 警告），且**不足以单独支撑 Q1**（n=1）。

### env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`
- `check-mvwu.py` 命中 SELF-GATE 触发面（`agate/scripts/*.py`）→ 须 SELF-GATE 链
- 不改 `.state.yaml` schema、不改 gate 语义、不改 hook、不改审计链（**零协议内核改动**）
- 测试须平台无关（Windows 只跑 `-m windows_smoke`）

## executor_env

- 仓库：`/home/kity/oclab/agateon`（主 checkout 禁止改动；worktree 开发）
- 稳定版工具：`~/.agate/scripts/`（勿动）
- 设计依据：`docs/design-notes/design-mvwu-protocol.md`（v2.1，**§3.1 I1 可归属性实证 / §5.1.1 四态 verdict / §5.1.2 消费方与登记点 / §7 试点方案 / §11 未决问题**）
- 分析依据：`docs/design-notes/design-orchestration-evolution-analysis.md`（v6.2，§4.9 / §11）
- 评审记录：`docs/reviews/review-260915-2300.md` / `review-260615-2339.md` / `review-260916-0828.md`
- **明确不依赖**：分析报告 §3.2 的时长归因（该归因两次被证伪后仍未确定，见该节）
