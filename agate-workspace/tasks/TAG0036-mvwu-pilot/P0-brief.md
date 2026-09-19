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
  - ⚠ **同类 fail-open（评审顺手发现，须登记）**：该函数在 `except ValueError: return None`（解析失败）与缺字段时也 **`return None` → 静默放行**，与 TAG0035 子批 A 同类。**本任务登记该发现，但不在本任务修**（属 TAG0035 范围）；若 TAG0035 未覆盖，另立 DEBT。
- **字段落地路径（交付物，独立评审 MUST-FIX）**：`tests_filter` 写在 `P2-design.md` frontmatter，**由 architect 角色产出**——若不同步更新角色/卡片，**无人会写该字段 → Q1/Q3 样本永不到来**（与判据 5 互相拆台）。故本任务交付物**必须含**：
  - `agate/phase-cards/P2-design.md`：说明 `batches[].tests_filter` 的写法与用途
  - `agate/assets/execution-roles/architect.md`：P2 产出时如何为该批选择 `tests_filter`
  - 二者均命中 SELF-GATE 触发面（`agate/**/*.md`）

**② `P4-evidence/{batch}.log` 证据落点（新目录约定）**

- **注意**：`P4-evidence/` **目前不存在**——现存的是 `P6-evidence/`、`P5-test-results/`、`P6.5-judge-evidence/`。本任务**新建**该目录，沿用既有 `P{phase}-{kind}/` 命名模式。

> **计数口径（独立评审 MUST-FIX）**：目录数以 `find agate-workspace -type d -name 'P6-evidence' | wc -l` 计（**全库口径**，含 archived）——`P6-evidence` = **37**、`P5-test-results` = **34**、`P6.5-judge-evidence` = **1**、`P4-evidence` = **0**。原稿的"42"**无任何口径可复现**（tasks-only 目录 = 35，文件数 = 679），已废弃。
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

> ⚠ **交付物补强（独立评审 MUST-FIX）**：原稿的六项检查（存在/可执行/证据/exit_code/HEAD/verdict）**不含**观察表的「耗时 / commit 形态 / boundary」三列——**观察行不会"自动产出"**。故本任务须交付 **`--observe` 模式**（见下），否则判据 5 无交付物支撑。

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

**`--observe` 模式（新增交付物，补齐观察表三列）**：

```bash
python3 agate/scripts/check-mvwu.py --observe <task_dir>
```
输出**可直接粘贴进 P0-brief 观察表**的一行，补齐六项检查未覆盖的三列：

| 列 | 来源（须明确，不可推断） |
|----|----------------------|
| `tests_filter` | P2-design frontmatter |
| **耗时** | `P4-evidence/{batch}.log` 的 `duration_seconds`（**故最小内容格式须增该字段**） |
| `evidence` | 日志文件存在性 |
| **commit 形态** | `git log --format=%H -- <batch 产出文件>` → 1 个 commit = 逐批；多批共享 = 合并 |
| **boundary** | 声明 `output`（如有）vs `git diff --name-only <commit>` 比对 → `exact` / `mismatch` / `UNKNOWN`（不可归属） |
| `verdict` | 六项检查结果 |

**`check-mvwu.py` 自身单测**：六项检查 + `--observe` 各需单测；**须用 `tmp_path`**（不得写仓库内真实账本/证据——DEBT0040 教训）；测试 fixture 必然合成，与"真实样本"是两件事（评审指出原稿未区分）。

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

**推进判据（v2 重写——独立评审指出原判据开箱即死）**：

原稿写 `Q1 ∧ Q2 ≥90%`，但 **Q2 实测 = 13%（任务级 2/16）**，远低于 90% —— **阶段 2 在当前提交形态下已不可达**，而原稿却把"Q2 结论在案"列为**已完成交付**（而非阻断性证伪），属于把证伪结果当成通过条件。

**修正后的判据（两个前置、一个决策）**：

| # | 判据 | 当前状态 |
|---|------|---------|
| 1 | **Q1 ≥ 90%**（`tests_filter` 在多数批上稳定可执行） | 待采样 |
| 2 | **提交粒度决策已裁决**（见下） | ⚠️ **待用户裁决**（Q2 = 13% 已证伪原门槛） |
| 3 | 上述两者均满足 → 才可进入阶段 2 | — |

**量纲澄清（评审指出原稿混用）**：Q2 的 **13% 是任务级**（2 个逐批 commit 任务 / 16 个多批任务）；原稿判据写"≥90% **批**"是**批级**——**两者量纲不同**。修正后：**Q2 不再作为推进门槛**（它已被证伪），改为**触发提交粒度决策**。

**提交粒度决策（Q2 的证伪结果直接导出，须用户裁决）**：

| 选项 | 收益 | 代价 |
|------|------|------|
| A. 保持合并 commit（现状） | 保留 `dispatch-protocol` 模式 3 的原子性 | I1 只覆盖 13%（其余退化 `UNKNOWN`） |
| B. 并行模式改逐批 commit | I1 可覆盖多数批 | 失去统一 commit 的原子性 |

> 协议对此**只有单边立场、从未讨论另一侧**（实测 `dispatch-protocol.md:618` 规定"汇总统一 commit"，无任何条文讨论逐批 commit 的权衡）。**本任务不自行决定**——须用户裁决后，阶段 2 的可行性才能确定。

**⑤ 四个方法学概念的落地（用户 2026-09-19 提出，并入本任务）**

> **背景**：用户提出「Ubiquitous Language / Deep Modules / Tracer Bullet / Walking Skeleton 是否应适用 agateon 的角色或场景」。逐项核实后判定：**两个已有对应、一个真缺口（与本任务同源）、一个有哲学张力**——故并入本任务一并处理（文件面与本任务高度重合）。

| 概念 | agateon 现状（实测核实） | 本任务处置 |
|------|------------------------|-----------|
| **Ubiquitous Language**（解决"叫什么"） | ✅ **已有**：`agate/CONTEXT.md`（29 条术语 + "首次定义位置"回溯列） | **不引入概念**；但**补本任务的新术语**（见下 ⑤-a） |
| **Deep Modules**（解决"怎么封装"） | ✅ **精神已内化**：`architect.md` 明写"不告诉你按什么顺序做"、`implementer.md` 明写"不要求按步骤脚本执行"；`role-system.md` 有「三层角色」结构 | **转为审查视角**（见下 ⑤-b）——非新机制 |
| **Tracer Bullet**（解决"怎么开始并快速反馈"） | ❌ **真缺口**：P1→P8 全串行，**P4 完成后才有 P5 验证**——中间无"先打通一条端到端路径"的机制 | **新增设计判据**（见下 ⑤-c）——与本任务 MVWU **同源** |
| **Walking Skeleton**（架构骨架 + 部署 + CI） | ❌ 无对应，**且与本协议边界冲突** | **部分吸收**（见下 ⑤-d）：仅取"骨架先跑通"，**拒绝部署/CI 部分** |

**⑤-a 术语表补录（Ubiquitous Language 的实际落地）**

- **实测缺口**：本任务引入的新术语（`MVWU` / `tests_filter` / `P4-evidence` / `四态 verdict` / `boundary(I1)`）**尚未进 `agate/CONTEXT.md`**（grep 计数 = 0）。
- **交付物**：在 `CONTEXT.md` 术语表补录本任务引入的术语，**沿用既有格式**（术语 / 定义 / 首次定义位置三列）。
- **理由**：CONTEXT.md 是协议术语的**权威入口**；新术语不入表 → 后续 agent 无法从统一入口理解 MVWU 相关概念（这正是 Ubiquitous Language 要解决的问题）。
- **边界**：**只补录本任务引入的术语**；不重构既有 29 条，不加机械校验（后者属独立议题，见 out-of-scope）。

**⑤-b Deep Modules → 角色文件审查视角**

- **判定依据（实测）**：agateon 已内化"深模块"哲学——`architect.md`：「实现导航（files_to_read）是资源地图，告诉你"去哪里找上下文"，**不告诉你"按什么顺序做"**」；`implementer.md`：「**不要求按步骤脚本执行**（那是 superpowers writing-plans 的模型）」。
- **本任务处置**：**不新增机制**，在 `role-system.md` 补一节**审查锚点**——审查角色文件/阶段卡片时问：
  > **该文件是否把"实现细节"写进了"接口"（浅化）？** 具体判据：是否规定了"第 1 步做 A、第 2 步做 B"式的执行顺序（而协议哲学是给"资源地图 + 判据"，不给步骤脚本）。
- **与 ⑤-c 的关系**：Deep Modules 管"**角色文件怎么写**"，Tracer Bullet 管"**批怎么切**"——两者正交，不可互相替代。

**⑤-c Tracer Bullet → 首个批的端到端判据（与 MVWU 同源）**

- **缺口（实测）**：P4 的 `dispatch_plan` 有 5 模式（`single`/`static-batch`/`parallel`/`recon-then-split`/`serial`），**全部是"完成所有批"语义**，无"先打通一条端到端路径、快速取得反馈"的表达。
- **与 MVWU 的同源性**：MVWU 要求每个批有 `tests_filter` + 证据落点；**若某个批的 `tests_filter` 是端到端路径，该批即 tracer bullet**。故**不新增机制**，而是给 `tests_filter` 补一条**设计判据**。
- **交付物**：
  - `agate/assets/execution-roles/architect.md`：补"**何时把首个批设计为端到端打通**"的判据（与既有 `tests_filter` 写法说明同处）
  - `agate/phase-cards/P2-design.md`：同判据的卡片侧表述
- **判据草案（P2 细化）**：
  > 当任务**包含 ≥2 个批**且**存在一条可端到端验证的关键路径**（如"输入→处理→输出"或"API 调用链"）时，**首个批应设计为端到端最小打通**（tracer bullet）：其 `tests_filter` 覆盖该路径的冒烟级验证，而非该批的完整单元测试。**目的**：在投入全部实现前取得"管道确实通"的反馈。
  - ⚠ **与 P3 红灯批的边界**：tracer bullet **不替代** P3 的完整红灯批；它是**首个批的切法**，后续批仍按常规 MVWU 设计。

**⑤-d Walking Skeleton → 仅吸收"骨架先跑通"，拒绝部署/CI 部分**

- **明确拒绝的部分（有协议依据）**：`agate/adr.md` 记载——agate「**不硬编码测试框架/语言/部署方式**，只定义**流程骨架**。技术栈相关的命令通过 P2-design.md 的 `gate_commands` 字段注入，由**项目自定义**」。故 Walking Skeleton 的"自动化部署 + CI 配置"部分**违反技术栈中立**，**不引入**。
- **吸收的部分**：仅取"**骨架必须先能跑通**"这一纪律——**并入 ⑤-c 的 tracer bullet 判据**（端到端最小打通 = 可运行的骨架）。
- **理由**：两概念在此重合点是"先可运行、再填功能"；但 agateon 只在**流程层**要求它，**不规定**骨架的技术形态。

**⑤ 的完成判据（并入下方总表）**：⑤-a 术语补录完成；⑤-b 审查锚点成文；⑤-c 判据落 `architect.md` + `P2-design.md` 卡片；⑤-d 仅以"拒绝理由 + 吸收点"记录（无独立交付物）。

### 完成判据与样本依赖（本任务边界的关键澄清）

> **本任务交付的是「工具 + 采集能力 + 已有结论」，不是「三问全答」。**

| # | 完成判据 | 状态 |
|---|---------|------|
| 1 | `batches[].tests_filter` 键可用（frontmatter 可写、可读、不破坏既有 P2 gate） | 本任务可完成 |
| 2 | `P4-evidence/{batch}.log` 落点约定生效（含最小内容格式） | 本任务可完成 |
| 3 | `check-mvwu.py` 可用（六项检查 + 四态 verdict + 不阻断） | 本任务可完成 |
| 3b | **`check-mvwu.py --observe` 可用**（补齐观察表「耗时/commit 形态/boundary」三列） | 本任务可完成 |
| 3c | **字段落地路径**：`phase-cards/P2-design.md` + `execution-roles/architect.md` 写明 `tests_filter` 写法 | 本任务可完成 |
| 4 | **Q2 结论在案**（13%，引用设计文档 §3.1 的实测） | **已完成**（不需试点） |
| 5 | **Q1/Q3 采集流程就绪**：`--observe` 能在任何多批任务上产出观察行（**由 3b 支撑**，不再是无交付物的承诺） | 本任务可完成 |
| 6 | **`--observe` 在至少 1 个任务上真实跑通**（**不要求该样本"多批"**——可在本任务自身或任意任务上验证工具可用性，产出 1 行观察记录） | 本任务可完成 |
| **7** | **⑤-a 术语补录**：`CONTEXT.md` 收本任务新术语（`MVWU` / `tests_filter` / `P4-evidence` / 四态 verdict / boundary(I1)），沿用三列格式 | 本任务可完成 |
| **8** | **⑤-b Deep Modules 审查锚点**成文（`role-system.md` 一节：判据 = 角色文件是否规定执行顺序而浅化接口） | 本任务可完成 |
| **9** | **⑤-c Tracer Bullet 判据**落 `architect.md` + `phase-cards/P2-design.md`（含"与 P3 红灯批的边界"） | 本任务可完成 |
| **10** | **⑤-d Walking Skeleton**：仅记录「拒绝部署/CI 部分 + 吸收"骨架先跑通"」（依据 `adr.md` 技术栈中立），无独立交付物 | 本任务可完成 |

> **判据 6 修正（评审指出"视交付方式"不是判据）**：原稿写"至少 1 个真实样本（若自身拆批提交，自身即样本）"——把判据与交付形态绑定，等于没判据。**修正为**：判据 6 = **工具在真实任务上跑通**（验证 `--observe` 能产出格式正确的行），**而非"拿到足以回答 Q1 的样本量"**；后者需自然样本累积，**不在本任务完成判据内**。

**为什么 Q1/Q3 需真实样本**：Q1 问"`tests_filter` 是否**稳定可执行**"——历史任务当时**没有**该字段，事后"推断一个当时该跑什么"**测不出当时的可执行性**；Q3 问"1 batch = 1 MVWU 是否成立"，需要真实的批产出与证据对应关系。**两者都无法从历史数据事后补出。**

**为什么不主动造样本（论证收窄，评审指出原稿过度）**：

原稿理由"避免自己验证自己"**方向对但过度**——因为它同时又说"本任务自身拆批提交，自身即样本"，**自相矛盾**（后者同样是自己验证自己）。修正后的准确表述：

| 概念 | 说明 | 本任务处理 |
|------|------|-----------|
| **工具自身单测** | 用**合成 fixture** 验证六项检查逻辑正确 | ✅ **本任务必做**（`tmp_path`，不污染真实账本） |
| **工具跑通验证** | 在**任意真实任务**上跑 `--observe`，验证能产出行 | ✅ **本任务必做**（判据 6） |
| **Q1 的样本量** | 需**多个自然多批任务**累积，才能判"稳定可执行" | ⚠️ **不在本任务完成判据内**（需自然供给） |

**关键区分**：合成 fixture 验证的是"**工具逻辑对不对**"；自然样本回答的是"**`tests_filter` 在实践中稳不稳定**"——**两者不可互相替代**，原稿把两者混为一谈（既说"不造样本"、又说"自身即样本"）。

**本任务的职责边界**：交付**工具 + 采集能力 + 字段落地路径**，使 Q1/Q3 的样本**一旦自然出现即可被采集**；**不负责制造 Q1 所需的样本量**（那需要项目自然产生多个多批任务）。

**与阶段 2 的衔接**：本任务完成后，状态为「**工具就绪 + Q2 已答 + Q1/Q3 待自然样本**」；阶段 2 的启动条件仍是 `Q1 ∧ Q2 ≥90%`，其中 **Q1 需等自然样本累积**。**在 Q1 有数据前不得进入阶段 2**（设计文档 §7.4 纪律）。

### out-of-scope

- **不做阶段 2**（批级 gate）——需 Q1 ≥90% **且**提交粒度决策已裁决（见推进判据）；**在阶段 1 数据出来前不得挂 gate**（设计文档 §7.4 纪律）
- **不做阶段 3**（`E_pipeline` 度量）——需阶段 1–2 数据
- **不改协议内核**：`.state.yaml` schema / `check-gate.py` gate 分支 / `phases.yaml` 状态机 / `agate/rules/schema/*.json` / hook 三件套 / `gate-events` 审计链——**一律不改**（阶段 1 的"零内核改动"性质；`check-mvwu.py` 是**独立脚本，不挂 gate**）
- **不改 P6.5**：`P4-evidence/` **不进 judge 白名单**（`dispatch-protocol.md:404` 只许 `P6-evidence/`，保持信息隔离）
- **不改 provenance 审计面**：`check-p6-provenance.py` 默认不扫 `P4-evidence/`
- **不改目录登记**：`pre-commit-gate.py` / `agate-archive-stale-outputs.py` 的目录登记不动（阶段 1 零内核改动的前提）
- **不主动造样本**：不专门构造试点任务（理由见「完成判据与样本依赖」）
- **不做**：DAG / Task Graph / Verification Graph（分析报告 §10 的架构方向，均为后续议题）
- **⑤-a 不重构既有术语表**：`CONTEXT.md` 只**追加**本任务新术语；既有 29 条不动，不新增术语一致性机械校验（后者属独立议题）
- **⑤-b 不改角色职责实质**：Deep Modules 只作为**审查视角**成文（`role-system.md` 一节），**不重写**任何既有角色文件的行为约定
- **⑤-d 不引入部署/CI 机制**：Walking Skeleton 的"自动化部署 + CI 配置"部分**明确拒绝**——`agate/adr.md` 记载本协议**技术栈中立**（不硬编码测试框架/语言/部署方式），技术栈相关命令由项目经 `gate_commands` 注入。仅吸收"骨架先跑通"并入 ⑤-c

### known_risks

- **I1 可归属率仅 13%（实测，本任务最大风险）**：16 个多批任务中仅 2 个为逐批 commit（`TAG0016` 用 `-P4a` 后缀、`TAG0034` 用中文"P4a 批"）；**87% 为合并 commit**（`TAG0012` 8 批→1 commit 等）。**合并提交形态下 boundary 必然判 `UNKNOWN`**——这不是缺陷而是**诚实标注**，但意味着 Q2 的结论很可能是"多数不可机械比对"。
  - **缓解**：把 Q2 的产出定义为**比例数据**（而非通过/失败）；若比例过低，触发设计文档 §11 问题 6 的**提交粒度取舍**（保持合并 commit 保原子性 vs 改逐批 commit 换可归属）——**该取舍须由用户裁决，本任务不自行决定**。
- **"批是否逐批 commit"无稳定命名约定**（实测）：`TAG0016` 用 `-P4a`、`TAG0034` 用中文"P4a 批"、多数任务不做任何批级标记。**即使批逐批提交，无标记也无法机械归属** → 本任务的 check 需容忍 `UNKNOWN`。
- **`tests_filter` 的平台中立性**：shell 字符串须遵循平台约束（Windows 常无 `make` → 应写 `python -m pytest`；不裸 `python3`，须遵循 `AGATE_PYTHON` 探测约定，见 DEBT0014）；`{batch}` 源自自由字符串 `id`，**须约束为 filename-safe 字符集**（`[A-Za-z0-9._-]+`）。
- **与 P3 TDD 红灯的冲突（设计文档 §5.1.1 实测）**：批级 commit **本身就带预期红灯**（`d1c2aca wf(TAG0034-P4): P4a 批 —— …（57 绿 / 3 批次边界红）`）。故 `tests_filter` 须有 **scoping 规则**（只覆盖该批交付面、禁止全量）+ `expected_red` 声明，否则红灯即判未完成是错的。
- **样本可得性（本任务最大不确定性）**：Q1/Q3 需**真实多批任务**样本，而**当前任务已全部完成**（以 `ls -d agate-workspace/tasks/TAG*/ | wc -l` 计），无在途多批任务。**缓解**：本任务的完成判据**不含**"Q1/Q3 已答"（见上方「完成判据与样本依赖」）——交付"采集能力就绪"，样本到来时自动产出观察行。
  - **不可用的方案（已排除）**：用历史任务"回填" `tests_filter` 来凑数——**回填的 `tests_filter` 是事后推断（推断当时该跑什么），既非当时的真实行为，也测不出"当时是否可执行"**（Q1 的定义），**属自欺**。历史数据**只用于只读统计**（如 Q2 的 13% 已是实测值，无需回填），**不改任何历史任务产物**。
- **⑤ 的"概念落地"易流于空谈（本任务新增风险）**：四个方法学概念中，**只有 ⑤-a（术语补录）与 ⑤-c（tracer bullet 判据）有可验证的交付物**；⑤-b 是"审查视角"（难以机械验证其生效）、⑤-d 只是"拒绝理由记录"。
  - **缓解**：完成判据 7-10 只要求"**成文到位**"（文件存在 + 内容含判据要点），**不宣称"机制已生效"**——生效性需后续任务实践检验（与 Q1 样本依赖同理）。**P5/P6 不应对 ⑤-b/⑤-d 做超出"成文"的断言**。
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
- **worktree**：`.worktrees/agate-TAG0036`（分支 `feat/TAG0036-mvwu-pilot`），构建流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0036.md` 按模板全 9 节填写
- **SELF-GATE 说明**：`check-mvwu.py`（`agate/scripts/*.py`）+ 两份卡片/角色文件（`agate/**/*.md`）均命中触发面 → 须走 `protocol-alignment-review` + 全量 pytest + consistency 0 ERROR
- **check-mvwu.py 自身单测**：六项检查 + `--observe` 各需单测，**须用 `tmp_path`**（DEBT0040 教训：不得写仓库内真实账本/证据）
