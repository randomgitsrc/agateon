---
phase: P2
task_id: TAG0051
type: design
parent: P1-requirements.md
trace_id: TAG0051-P2-20261011
status: draft
created: 2026-10-11
agent: architect
candidate_count: 3
packages:
- agate-cards
- agate-state-machine
- agate-rules
- agate-scripts
- agate-roles
- agate-dispatch
- agate-config
- agate-docs
- ci-workflows
domains:
- backend
- security
ui_affected: false
dispatch_plan:
  mode: static-batch
  parallel_limit: 8
  batches:
  - id: ready-no-tag
    complexity: high
    tests_filter: python -m pytest agate/tests/unit/test_tag0051_p8_gate.py -q
  - id: p8-surfaces
    complexity: high
  - id: p8-rules-roles
    complexity: medium
  - id: delivery-contract
    complexity: medium
  - id: obligations-sync
    complexity: medium
    tests_filter: python -m pytest agate/tests/unit/test_tag0050_obligations_enforcement.py
      agate/tests/unit/test_tag0050_obligation_behavior.py -q
  - id: release-gate
    complexity: high
    tests_filter: python -m pytest agate/tests/unit/test_release_gate.py -q
  - id: release-docs
    complexity: low
  - id: r6-harness
    complexity: low
    tests_filter: bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus
prod_touched: false
---

# P2 方案设计 — TAG0051 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

> **来源**：`P1-requirements.md`（23 条 BDD，**本文件的验收对照表**）+ `P0-brief.md`（环境约束 / 风险）。
> **承接**：`docs/design-notes/design-release-order-boundary.md` / `docs/reviews/agate-design-review-2026-10-03-release-order.md` / `docs/reviews/handoff/handoff-release-order-20261003.md`（RM-AG0098，已 `done`）。
> **性质**：改协议本体的跨子系统重构；本阶段**只给方案**（P4 才写代码）。**只改 agateon 本仓**，改 `agate/` 触 SELF-GATE。
> **状态标记**：`[PROD_NOT_TOUCHED]`——设计阶段为只读，未触发任何写操作（push / PR / merge / dispatch / tag / Release 一概未做）。
> **注**（工具缺口 + 受限编排细节，须主 Agent 知悉）：
> - `dispatch_plan` 无法经 `agate-md-field-set.py` 写入（工具把该键归入「追加/嵌套字段」并拒写：`ERROR: dispatch_plan 是追加/嵌套字段`），**超出已登记的 DEBT0067 面**（该债务记的是 `ceremony`/`delivery`/`debt_check` 等**读侧认写侧不认**）。本文件按 P2 卡「dispatch_plan 机器字段」节**直接在 frontmatter 落**（该键不入 `frontmatter-check` schema，gate 经 `agate-md-field-get` 读取后 `json.loads` 校验——已实测通过）。**如实上报，未静默绕过其它字段工具**。另：P2 卡允许的 `batches[].output` 因 `check-frontmatter.py` 的 `MAX_DEPTH=3` 而**写不进**（深度 4）⇒ 本文件省略该键，批产出面见 §4 表格（详见 §10「工具缺口 2」）。
> - `release.preset` 去 tag/version 后的 P8 语义（BDD-19）**未与** `[生产环境]` 挂钩——本任务不写生产。

---

## 0. 方案摘要与先例承接

**目标切法（承接 RM-AG0103 ①② + P1 §1）**：把**不可逆的对外发布动作**（tag → GitHub Release）从任务 P8 结构性移出 —— ① 任务终态 = **READY**（交付物 + `CHANGELOG [Unreleased]` 含本任务条目 + `bump_type` 意图 + 交付收尾 + CI 全绿含 push 口径；**不落 tag / 不建 Release / 不 bump 版本文件**）；② **Release = 独立流程**（`workflow_dispatch` 人工授权一次；发布门 = 目标提交 CI success + tag↔提交一致 + CHECK 7/13 + roadmap RM `done`；动作序列 = 聚合 `[Unreleased]` → 定版本 → 切版本节 + badge + UPGRADING → PR → merge → 等 main CI 绿 → tag → Release → G-5；失败处置 = 先评估回退重打、仅已被外部消费才出补丁）；③ 配套（`delivery` 取值域 / `state-machine` 授权 / `release.preset` 声明层 / `AGENTS.md` tag 时点统一）。

**承接 RM-AG0098（P1 §5 已判定边界，本方案不重复、不冲突）**：
- **已由 RM-AG0098 落地、本任务只要求「继续生效」**：CHECK 7 **tag 无关**（badge ↔ CHANGELOG 最新已发布版本）+ `release.yml`「Verify tag points to matching commit」步（:33-65）。⇒ 本方案**不改 CHECK 7 逻辑、不重写该步**，只在独立发布流程中**保留并继续调用**（BDD-11/12）。
- **RM-AG0098 未解、本任务承接（不重叠核心）**：P8→READY 移出 tag（BDD-1/2/3）；发布入口独立化 `workflow_dispatch`（BDD-8）；**创建 tag/Release 前**的机械发布门（BDD-9/10）；`AGENTS.md` 三处 tag 时点统一（BDD-14）；配套字段/授权/声明层（BDD-16/18/19）。
- **RM-AG0116（done）约束遵守**：方案**不新增**任何「假定主分支叫 main」的硬编码——发布门查询用 `git remote`/`gh` 自动解析仓库，不写死 `main`；不触碰分支策略（`.githooks/pre-commit-local` 属项目侧，不改）。
- **RM-AG0110 / RM-AG0115（相邻，本任务不负责）**：二者是「不可裁剪集下沉契约单源」与「阶段图数据化」。本任务**不触及**阶段图/裁剪集数据面；`level-2.yaml` 只新增 `delivery.method_enum`，**不动** `non_prunable_phases` / `phase_universe`（见 §1 不改什么）。

---

## 1. 影响面梳理（**强制节，写在候选方案之前**）

> 三部分：**改什么（Modify）/ 不改什么（Not Modify）/ 风险在哪（Risk）**。改动落点落到**文件 + 小节/函数**，关联 BDD 编号。P1 §4.9 已给「活面清单 15+ 文件」，本节做**候选方案级**细化。

### 1.1 改什么（Modify）—— 逐文件 + 落点 + 关联 BDD

| # | 文件 | 落点（小节 / 函数 / 行） | 改动 | 关联 BDD |
|---|------|--------------------------|------|----------|
| M1 | `agate/scripts/check-gate.py` | `gate_p8()` | **删** tag 存在性 WARNING 块（:2376-2389，含 `VERSION_TAG_PREFIX` 使用）；**删** version 双路径 WARNING 块（:2317-2337）；**删** CHANGELOG 暂存区 diff WARNING 块（:2339-2356——**定死为删**，见决策 5/NB-2；其载体改为 `check-changelog.py <task_id>`，该脚本已在 P8 必经路径 `pre-commit-gate.py:1086` 被调用，判据强度不降反升）；**删** 迁移期 `agate.config.yaml` 提示块（:2358-2374，其触发/文案基于已移除的 version/tag 痕迹）；**保留** `bump_type`（:2245-2247）/`debt_check`（:2249-2251）/结构化 `delivery`（:2255-2292）/RM-AG0043 反查（:2294-2315）；**新增** `delivery.method` 枚举校验（读快照 `delivery.method_enum`，缺省 no-op） | BDD-2/3/4/5/6/7/16/17/19 |
| M2 | `agate/phase-cards/P8-release.md` | 全文 P8 条件 / 动作面 | :12「同 commit + tag」→「同 commit（不 tag）」；:74「版本号变更确认」删；:75 CHANGELOG「→新版本号」→「`[Unreleased]` 写本任务条目」；:87-88 gate 规则删 version/CHANGELOG-diff 行；:122/:156 删两处「git tag 已创建」；:11/:37/:50/OBL 相关删 tag | BDD-1/2/3/4 |
| M3 | `agate/state-machine.md` | :165 P8→READY 转移；:177 READY 收尾 | 转移条件删「亲自执行 `git tag`」+ version 双路径检查；保留 bump/CHANGELOG；:177 删「git tag 已创建」；**新增**发布授权说明（独立流程 + `workflow_dispatch`，不新增阻塞语义） | BDD-1/2/3/18 |
| M4 | `agate/rules/state-transitions.md` | :54 P8→READY | 删「git tag 创建」；保留「version bump 确认→改为交付收尾确认 / CHANGELOG 非空」 | BDD-1/3 |
| M5 | `agate/rules/phases.yaml` | P8 节（:161-173） | :167 gates 措辞删「version/CHANGELOG/tag 检查」→「delivery/bump_type/debt_check 字段 + CHANGELOG `[Unreleased]` 检查」；**:169 删「先 tag 后重跑（DEBT0013）」**（DEBT0013 已由 CHECK 7 tag 无关消解，见 P8 卡 :99-103）；`task_fields` 保持 `[bump_type]` | BDD-1/3 |
| M6 | `agate/rules/obligations.yaml` | `OBL-P8-01..14` 全段（:717-828） | **十四条逐条过一遍**（结论表见 §1.1.1）：**OBL-P8-04 就地重挂**（version 文件变更 → `delivery.method_enum` 枚举校验，`disposition` 保持 **M**）⇒ **M 计数不变（56/121）、`baseline` 不动**；**OBL-P8-05/08/13 仅 statement 改述**（anchor 节仍在）；其余 **10 条保留不动**。**不删任何条目、不改判、不移出占比**——三条路均使 M 计数 −1 → `P5_obligations`（`check-obligations.py`）FAIL（§1.1.1 四条路径实测）| BDD-1/21 |
| M7 | `agate/tests/unit/test_tag0050_obligations_enforcement.py` | `M_IDS`（:61 附近）+ **新增** BDD-21 机械断言 | ① `M_IDS` **保持含 `"OBL-P8-04"`**——重挂后该条仍为 M，故**零 `M_IDS` 改动**；反向说明：**只有走「删条目」路才须同步删该 `M_IDS` 项**（否则 `test_obligation_enforced[OBL-P8-04]` 因 `assert m is not None` 转红）；② **新增**一条机械断言（**放本文件内，不新增文件**）：遍历 `OBL-P8-*` 的 statement，断言**不含** version/tag 期词汇（`新版本号` / `version 文件变更` / `双路径` / `bump 后` / `git tag`），并断言 `OBL-P8-04.disposition == "M"` 且 statement 含 `method_enum` ⇒ 把 BDD-21 的「语义一致」降为 **P5/P6 可机械判定**（补评审「测试缺口 #1」）。`test_tag0050_obligation_behavior.py`（OBL-P8-01/02/03）**不改**，仍在批 `tests_filter` 内作回归锁 | BDD-21 |
| M8 | `agate/rules/task-data/level-2.yaml`（**新增**） | 全文件 | `level: 2` / `extends: 1` / `delivery: {required: [method], none_requires_reason: true, non_none_requires_ref: true, method_enum: [release-notes, tag-release, none]}`——**注意 `load_contract` 按顶层键浅合并**，故 level-2 的 `delivery` 节须**重述完整规格**（不能只写 `method_enum`） | BDD-16/17 |
| M9 | `agate/rules/task-data/LEVELS.yaml` | 顶层列表 | 追加 `{level: 2, file: level-2.yaml, sha256: "<LF 归一值>"}`（**未登记即 consistency ERROR**） | BDD-16/19 |
| M10 | `agate/UPGRADING.md` | 新增版本章节 | 记录 `delivery.method` 收紧（**非破坏性**：仅非 legacy 任务生效，走快照 `level-2`）；同时记录 P8 去 tag/version 语义变更 | BDD-16/19 |
| M11 | `agate/scripts/agate-release.py` | 新增 `gate` 子命令（+ `_cmd_gate`） | **发布门**：① 复用 `check-gate.py P8 <task_dir>`（RM done / delivery / bump_type，判据单源）；② 目标提交 CI success（查 GitHub check-runs，可注入命令供测试）；③ `check-protocol-consistency.py` 0 ERROR（CHECK 7/13）；缺省 fail-closed。**不改**既有 `boundary/pyyaml-pin/notes/is-prerelease/build` 语义 | BDD-9/10/12/13 |
| M12 | `.github/workflows/release.yml` | `on:`（:4-6）+ 新增门步 | `on:` **加 `workflow_dispatch:`**（BDD-8 人工授权入口）；新增一步调 `agate-release.py gate`（tag push 路径的 **fail-closed backstop**）；**保留**「Verify tag points to matching commit」步（:33-65，BDD-11） | BDD-8/9/10/11/12/13 |
| M13 | `AGENTS.md` | 版本发布清单（:188-205） | **统一 tag 时点**：删「第 4 步先 push tag」，改为「先合 release PR → 合并后 main CI 绿 → 后打 tag（`workflow_dispatch`/本地门先过）→ Release → G-5」；第 6 步 G-5 与「release PR 必须普通 merge」条与新顺序对齐；**新增**「发布失败处置」小节（先评估回退 tag/Release 重打，仅当已被外部消费才出补丁） | BDD-14/15 |
| M14 | `agate/git-integration.md` | :185-188（release PR 普通 merge + G-5 tag 时点） | 与 `AGENTS.md` 统一 tag 时点表述（BDD-14 的两个判定对象之一） | BDD-14 |
| M15 | `agate/dispatch-protocol.md` | :881 P8→READY 行 | 删「+ tag 由主 Agent 亲自执行」；删 version 双路径检查提及；保留 bump_type/CHANGELOG/debt_check | BDD-1 |
| M16 | `agate/assets/execution-roles/implementer.md` | :101 | 「P8 模式禁止执行 `git commit` / `git tag`」→ 收为「不执行 `git commit`」（tag 移出 P8 语义） | BDD-1 |

> **M1 的枚举校验落点细节**：`gate_p8` 结构化 `delivery` 分支（`if task_level(task_dir) is not None:`）内，在现有 `required`/`none`/`ref` 三条之后追加：`_enum = _dspec.get("method_enum"); if isinstance(_enum, list) and _enum and _method not in _enum: return 1`。level-1 任务（含 TAG0051 自身）`_dspec` 无 `method_enum` → **no-op**，行为与现状一致（legacy 走 :2288 子串路径，完全不进此分支）。

#### 1.1.1 `OBL-P8-*` 十四条**逐条**结论（M6 的展开；**无未表态项**）

> P8 去 tag/version 后，逐条判定为 **保留 / 改述 / 重挂 / 删除（+reset）**。**结论：4 条动（均不删条目）、10 条保留；删除 0 条、`baseline.reset` 不写** ⇒ **M 计数 56 不变**。

| OBL | 现 disposition | 现状 statement（要点） | 去 tag/version 后结论 | 落点 / anchor |
|-----|---------------|------------------------|----------------------|---------------|
| OBL-P8-01 | M | `bump_type` 字段（major/minor/patch） | **保留**（与 tag/version 无关） | anchor `phases.yaml#P8.outputs` 不变；test 不变 |
| OBL-P8-02 | M | `delivery` 字段（交付方式声明） | **保留**（M1 另**增强**为 `method_enum` 枚举校验） | 结构化 `delivery` 分支保留；test 不变 |
| OBL-P8-03 | M | `debt_check` 字段 | **保留** | 不变 |
| **OBL-P8-04** | M | version 文件变更（暂存区 / 最近 5 commit，**双路径**） | **就地重挂**：statement → `delivery.method` 枚举校验（读快照 `delivery.method_enum`，缺省 no-op）；`disposition` **保持 M**；`enforced_at` → `{file: agate/scripts/check-gate.py, function: gate_p8}`；`test` **复用既有** `test_tag0050_obligations_enforcement.py::test_obligation_enforced[OBL-P8-04]`（该节点断言块内**有 `enforced_at`**，重挂后成立，且已引用 id ⇒ `check_test_node` 无需改文件） | anchor `P8-release.md#gate 规则` 不变（M2 后仍有该节） |
| **OBL-P8-05** | M | CHANGELOG `[Unreleased]` **→ 新版本号**（含 task_id） | **改述**：「CHANGELOG `[Unreleased]` 含 task_id（载体 `check-changelog.py`）」——ⓐ M2 把卡片该节「→新版本号」改为「写本任务条目」、删「版本号变更确认」⇒ 原语句**悬空**；ⓑ 载体本就是 `check-changelog.py`（非 gate_p8 暂存区 diff） | anchor `P8-release.md#gate 规则` 不变；`script`/`enforced_at` 不变 |
| OBL-P8-06 | M | roadmap 关联条目回写 done（RM-AG0043） | **保留** | RM 反查保留（M1 :2294-2315） |
| OBL-P8-07 | C | 从 P2 packages 逐包读取发布检查命令并执行 | **保留**（与 tag/version 无关） | 不变 |
| **OBL-P8-08** | C | **bump 后**重跑 P5（或审计 7 复用判定） | **改述**：「交付收尾后审计 7 复用/重跑判定」——任务 P8 **不再 bump**（决策 5）⇒「bump 后」前提消失 | anchor `P8-release.md#gate 规则` 不变；`script` 不变 |
| OBL-P8-09 | C | READY 收尾检查（清理临时资源 / 还原环境 / 生产无残留） | **保留** | anchor `state-machine.md#READY 收尾检查…` 仍在（M3 仅删其中 tag 行） |
| OBL-P8-10 | C | 提交前暂存面审查（防泄漏） | **保留** | 不变 |
| OBL-P8-11 | C | 干净 checkout 跑 consistency | **保留** | 不变 |
| OBL-P8-12 | C | 临时资源清单 | **保留** | 不变 |
| **OBL-P8-13** | R | releaser 不执行 `git commit` / `git tag` | **改述**：「不执行 `git commit`」（`git tag` 移出 P8 语义）；M2 同步删卡片该节 tag 措辞 | anchor `P8-release.md#如果是首次进入本阶段` 不变（该节仍在） |
| OBL-P8-14 | M | phase=P8 提交（READY 提交会让 P8 gate 从不运行） | **保留**（与 tag/version 无关） | 不变 |

**M 计数实测（`check-obligations.py` 四路径，一次性副本 `/tmp/opencode`；跑前/跑后真实仓库 `git status --porcelain` 不变）**：

| 处置路径 | 实测输出 | 判定 |
|---------|---------|------|
| 基线（不动） | `M 类占比: 56/121 = 0.4628` | OK / exit 0 |
| ① **删条目** | `55/120 = 0.4583` | **FAIL** / exit 1 |
| ② `M→C` 改判 | `55/121 = 0.4545` | **FAIL** / exit 1 |
| ③ `scope: protocol-repo` 移出占比 | `55/120 = 0.4583` | **FAIL** / exit 1 |
| ④ **就地重挂（本方案定死）** | `56/121 = 0.4628` | **OK** / exit 0 |

⇒ `obligations.yaml.baseline` 是**只增不减**棘轮（判据 = 整数交叉相乘 `current_m*base_total >= base_m*current_total`，`check-obligations.py:320`）：**M 计数 −1 即 FAIL，与走哪条路无关**。本方案**定死为 ④ 重挂**——**不删条目、不写 `baseline.reset`**（② 备选的 `baseline.reset.to` **弃用**：它会把「M 占比下降」合法化，本任务无需付该代价）。④ 的两项机械凭证已核：`gate_p8` 经 `_reachable_set` 在必经路径上（OBL-P8-01/02/03 用同一落点）、`test_obligation_enforced[OBL-P8-04]` 仍引用该 id。

### 1.2 不改什么（Not Modify）—— 显式边界（P4 implementer 的范围禁区）

| 范围 | 理由 |
|------|------|
| `check-protocol-consistency.py` 的 **CHECK 7 逻辑**（`check_version_badge`） | 已由 RM-AG0098 改为 tag 无关；**本任务不复改逻辑**。其**措辞**为**条件性**（仅当发布入口/流程名变化时触发——本方案发布入口即 `workflow_dispatch`，若证实措辞受影响则同步；其可判定性由 BDD-12「该脚本 0 ERROR」间接覆盖）。**禁止顺手改 CHECK 7 判据。** |
| `release.yml` 的「Verify tag points to matching commit」步 | BDD-11 明确「不要求重新实现，只要求继续生效」 |
| `agate-release.py` 既有 `boundary/pyyaml-pin/notes/is-prerelease/build` 语义 | 与发布门正交；仅**新增** `gate` 子命令 |
| `check-changelog.py` | 已实现 `[Unreleased]` 含 task_id（exit 0/1），即 BDD-4/5 载体，**不改** |
| `agate/rules/task-data/level-1.yaml` | **已发布冻结**：硬化签名（LEVELS.yaml 登记 sha256）不得改；收紧走新一级 `level-2.yaml` |
| `agate/tests/unit/test_check_protocol_consistency.py`（CHECK 7 测试） | CHECK 7 逻辑不动 ⇒ 其测试不动 |
| `agate/UPGRADING.md` **历史迁移章节** | BDD-1 显式排除（历史说明非现行规则）；只在 M10 追加**新**版本节 |
| `agate-workspace/tasks/*/P8-*.md`、`archived/**`、`docs/reviews/**`、`CHANGELOG.md` 发布产物 | frozen 快照；`docs/reviews/**` 是 RM-AG0098 的先例证据，**保留**（BDD-14 只统一活面文档） |
| `.githooks/pre-commit-local`、分支保护、`default_branch()` 单源 | 项目侧/外部设置；**分支保护改动须人工授权**（本方案**未预见**必须改分支保护——见 §7） |
| `check-gate.py` 的 P1..P7 各 gate、`check-obligations.py` 逻辑 | 与发布解耦无关 |
| `agate/rules/phases.yaml` 的 `non_prunable_phases` / `phase_universe`、`level-1.yaml` 阶段图面 | 属 RM-AG0110/0115，本任务不碰 |
| `agate.config.yaml` | **文件本身不改**——`release.preset: semver-changelog-tag` 是**纯信息性声明**（NB-1）：实测 `grep -rn preset agate/scripts/*.py` **无任何「读值」消费方**（三处命中分别是 `agate_common.py:919` 默认值字典、`agate-config.py:49` init 模板、`check-gate.py:2358-2374` 迁移期提示块——后者**只检查 config 文件是否存在**、**不读其值**）。⇒ 它**不是**「删了消费点才变死键」，而是**本就无消费方**。经主 Agent 裁定走 (b)：**保留为声明、不驱动逻辑**，已登记 **DEBT0069**（`agate-workspace/debt/tech-debt.md`，status open）——**新发布门 M11 不消费该键**（改用该键会超出 BDD-19 要求）。M1 删迁移期提示块后**无悬空提示** |
| `agate/WORKFLOW.md`、`agate/orchestrator-template.md`、`agate/assets/templates/*`（NB-4） | 实测三者 `git tag` **零命中**（评审已核）⇒ 不入改面**正确**；**显式点名**为范围禁区——「不改什么」是 P4 范围边界的**唯一依据**，点名可免 implementer 顺手改 |

### 1.3 风险在哪（Risk）—— 每条风险配一条缓解

| # | 风险 | 缓解（可执行判据） |
|---|------|-------------------|
| R1 | **跨 7 处 tag 条件不一致**（卡片 / 状态机 / 规则表 / gate / workflow / AGENTS / 角色文件）——本任务核心失败模式 | 影响面 M2-M6/M13-M16 逐面覆盖；**BDD-1 六文件语料 grep 零命中** + **P7 逐文件交叉核对** + consistency 0 ERROR |
| R2 | **legacy 行为漂移**（改 gate_p8 影响 43 个 legacy 任务） | 验收锚 **BDD-20**（R6 双向差分 `r6-differential.sh`，**只在 `/tmp/opencode` 副本上跑**，跑前/跑后核验真实仓库 `git status --porcelain` 一致）。gate_p8 保留的 `bump_type`/`debt_check`（exit 1）与 RM 反查（exit 1）**语义不变**；删除项均为 **WARNING**（不影响 `(rc, ERROR 集合)`）⇒ 预期 allowlist 无需新增规则 |
| R3 | **契约冻结**（改 level-1 触发 consistency ERROR） | 落 `level-2.yaml`（`extends: 1`）+ M9 登记 sha256；**只新增不改 level-1**；`load_contract` 顶层键浅合并 ⇒ M8 重述完整 `delivery` 节 |
| R4 | **新增脚本登记面**（SG.6 / CHECK9-coverage 转红） | **本方案不新增/不改名任何 `agate/scripts/` 文件**——发布门落在**既有** `agate-release.py`（`agate-*.py` 面，零触发）。复用 P1 §4.10 实测：新 `agate-*.py` → SG.6/CHECK9 **零触发**；新 `check-*.py` → SG.6 红 + 新增 CHECK9-coverage WARNING。**CHECK 10 方向相反**（只报「协议文档引用了不存在脚本」；本方案不改名/退役脚本 ⇒ 不触发）。三处点名齐（CHECK 9 / SG.6 / CHECK 10） |
| R5 | **obligations anchor 漂移 / 测试红**（BDD-21） | M6/M7 同步（OBL-P8-04 移除、OBL-P8-13 措辞）；跑 `check-obligations.py` + `test_tag0050_obligations_*`（现状 66 passed，见 P1 §4 客观查证） |
| R6 | **发布门竞态**：tag push / 跑门当下 main CI 可能仍在跑（P0-brief known_risks 第 4 条） | **fail-closed + 明示 pending 项**（见 §3 决策 3）；不引入无界等待（避免「长命令被误判失败」） |
| R7 | **发布门依赖 GitHub API**（check-runs 形状） | 见 §8 `minimal_validation`（已只读实测 API 形状）；门脚本走**可注入命令**（`--ci-cmd` / 环境变量）⇒ 本地 P5/P6 用 fixture/mock，CI 用真 `gh`（P1 §8 已判定属验证方式非能力缺口） |
| R8 | **不可逆外部动作**被写成 agent 自动执行 | §7 `env_constraints` + 方案正文：push/PR/merge/tag/Release/改分支保护 = **人工授权**，不进 agent 自动链；`workflow_dispatch` 由人工触发 |
| R9 | **`release.preset` 悬空提示**（BDD-19） | M1 删除基于 version/tag 痕迹的迁移期提示块 ⇒ 无悬空；该键**本就无值消费方**（NB-1），保留为信息性声明（**DEBT0069**）；consistency 0 ERROR 兜底 |
| R10 | **AGENTS.md 三处 tag 时点自相矛盾**（BDD-14 判定对象） | M13/M14 统一为「先合 PR → main CI 绿 → 后 tag」单一口径；P7 全文检索核无矛盾副本 |
| R11 | **跨项目破坏半径**（NB-5）：移除 `gate_p8` 的 version/tag 检查影响**所有用 agate 的项目**（不只本仓）及在途非 legacy 任务的 P8 语义 | 显式框定受众并区分两轴：**语义**上「P8 不再要求 version/tag」是**意图内的向前变更**（非破坏）；**机械**上二者皆 **WARNING** ⇒ `(rc, ERROR 集合)` 不变 ⇒ 对 legacy/其它项目**非破坏**（R2 依据同源）。避免读者把语义变更误读成 gate 破坏 |
| R12 | **level-2 快照与登记不同步**（CHECK 16） | `level-2.yaml`（M8）与 `LEVELS.yaml` 登记（M9）**必须同批落地**——只加 `level-2.yaml` 未登记 → `check-protocol-consistency.py::check_task_data_snapshot_freeze`（CHECK 16，:1498-1502「未登记到 LEVELS.yaml」）判 **ERROR**。缓解：M8/M9 同属 `delivery-contract` 批；`P5_consistency` 兜底 |

### 1.4 登记面实测（新增/改名 `agate/scripts/` 文件时必填）

**本方案不新增、不改名 `agate/scripts/` 下任何文件**（改 `check-gate.py`、**扩展** `agate-release.py`，二者均为既有文件）⇒ 按 `agate/scripts/README.md`「新增脚本登记面」节，**① CHECK 9 覆盖 / ② SG.6 / ③ CHECK 10 三处均无适用项**。沿用 P1 §4.10 的**实跑探针法**（不重做）：探针 `check-*.py` → CHECK9-coverage WARNING + SG.6 红；探针 `agate-*.py` → 零触发。本方案两个落点分属「改既有 `check-gate.py`」与「**既有** `agate-*.py`」，**零触发面**。

> **NB-3 的 R6 wrapper 同样零触发**：新文件 `docs/design-notes/r6-differential-prepare.sh`（见 §5）**不落在 `agate/scripts/` 下**。真门禁判据 `uncovered_gate_scripts()`（`check-protocol-consistency.py:906`）扫描面 = `agate/scripts/check-*.py` + `pre-commit-gate.{sh,py}`；CHECK 10 只报「协议文档引用了**不存在**的脚本」——wrapper 均不在其面内 ⇒ **CHECK 9 / SG.6 / CHECK 10 三处零触发**（沿 P1 §4.10 实测法判定）。

---

## 2. 候选方案（≥2）+ 权衡 + 选择理由

> **主轴**：**发布门落在哪**（派发指引「必须做出的关键设计决策」第 1 条 = 候选主轴）。三个候选在**可测性（P5/P6 本地能否验）/ 登记面 / CI 依赖**三维取舍不同。

### 候选 A（**推荐**）：发布门 = `agate-release.py` 新增 `gate` 子命令（**CLI**）
- **做法**：在既有 `agate/scripts/agate-release.py` 加 `gate` 子命令，串起「复用 `check-gate.py P8`（RM done/delivery/bump_type）+ 目标提交 CI success + `check-protocol-consistency.py` 0 ERROR」；`release.yml` 加一步调它做 backstop。
- **优点**：① **可测性高**——纯 CLI，本地 `pytest` 可直接 import/调用；CI 查询走**可注入命令** ⇒ 本地 fixture/mock（满足 P3 TDD「先红后绿」）；② **登记面为零**（既有 `agate-*.py`，SG.6/CHECK9/CHECK10 全不触）；③ **与先例一致**——`release.yml` 头注释明写「构建逻辑全在 `agate/scripts/agate-release.py`，本文件只做编排」「workflow 内零打包逻辑」；④ **可在 tag 前运行**（满足 BDD-9「创建 tag/Release 前」）。
- **代价**：需 `gh`/GITHUB_TOKEN（Actions 有；本地需 `gh auth`）；`git remote` 自动解析仓库（不写死 `main`，符合 RM-AG0116）。
- **CI 依赖**：中（门本体需 API；经注入可本地验）。

### 候选 B：发布门 = 新增 `agate/scripts/check-release-gate.py`（**check-\* 家族**）
- **做法**：新建 `check-*.py` 承载发布门逻辑；登记进 `SCRIPT_ALIGNMENT_ANCHORS` 或 `GATE_SCRIPT_EXEMPT`。
- **优点**：① 命名与「检查」语义一致；② 可测性高（同 A）；③ 与 `check-*` 家族风格统一。
- **代价**：① **触 SG.6（pytest 会红）**——须**额外登记**（锚点表或豁免集），多一个登记面动作（P1 §4.10 实测）；② 发布门**不是阶段 gate**，纳入 pre-commit 检查面语义不符；③ 落点需在 P4 额外维护 `README.md`/测试映射（团队约定项）。

### 候选 C：发布门 = `release.yml` 内**新增步**（不新增脚本）
- **做法**：直接在 `release.yml` 增一步内联 shell 查询 CI/跑一致性。
- **优点**：① 登记面为零（不新增脚本）；② 与 RM-AG0098 的「tag 指向校验」步形态一致。
- **代价**：① **可测性最低**——YAML 内联 shell，P5/P6 无法本地跑**触发器语义**，只能靠 CI 实证（违 TDD 精神）；② **时序不满足 BDD-9**：`release.yml` 以 tag push 触发 ⇒ 该步**在 tag 之后**才跑，无法充当「**创建 tag 前**的门」；③ 逻辑散进 YAML，违背「workflow 内零逻辑」先例。

### 选择理由（**权衡**见上）

**选 A**。三维度裁决：**可测性** A=B≫C；**登记面** A=C≫B（A/C 零触发，B 须登记）；**时序正确性** A≫C（A 可在 tag 前运行，C 不能）。A 唯一兼顾「可测 + 零登记 + 时序正确 + 合先例」。C 降级为 **A 的 backstop**（`release.yml` 内**调用** A 的 `gate`，而**不**内联逻辑）。B 被否仅因**多一个登记面且语义不符**，其可测性优势 A 已具备。**不选 C 作主载体**的关键：BDD-9 要求「创建 tag/Release 前」，C 物理上在 tag 后。

---

## 3. 必须做出的关键设计决策（逐条结论）

**决策 1 — 发布门落点**：**候选 A**（`agate-release.py gate` CLI）为主载体；`release.yml` 内**调用**该 CLI 作 tag-push 路径 backstop（**不内联逻辑**）。理由见 §2。

**决策 2 — `workflow_dispatch` 人工授权入口与「授权一次」语义**：
- `release.yml` 的 `on:` 追加 `workflow_dispatch:`（可带 `tag` 输入）。**「人工授权一次」= 人工触发 `workflow_dispatch` 这一动作本身**（Actions run 记录 = 可审计留痕）。
- **与既有 `PAUSED`/`[NEED_CONFIRM]` 划清界限（BDD-18）**：发布**不在任务状态机内**（任务止于 READY）⇒ **不新增**任何任务内阻塞标记/状态。授权载体 = `workflow_dispatch`（**唯一**入口）。若门判失败，复用**既有**「红灯 → 人工介入」路由（不发明新语义）。**明确：不引入第二套并行阻塞确认语义。**

**决策 3 — 发布门校「目标提交 CI success」的竞态**：选 **前置顺序为主 + fail-closed 兜底**，**拒绝无界等待**：
- 前置顺序：release runbook 规定「先合 PR → 等 main CI 绿 → 再跑门 → 打 tag」。
- fail-closed：门查目标提交的 required check-runs；**任一 required 检查非 `success`**（含 `in_progress`/`queued`）→ **非 0 退出并列出 pending/failed 项名**，提示「CI 未完成/失败，等待后重跑」。
- **不选「等待（poll）」**：无界轮询会挂住命令（违 AGENTS「长命令被误判失败」教训），且 runbook 排序已消解主要竞态。

**决策 4 — `delivery` 取值域**（BDD-16/17）：
- 枚举：`method_enum: [release-notes, tag-release, none]`（采纳 P1 §6 SUGGEST；`none` 须 `reason`——level-1 已含 `none_requires_reason`）。
- 契约落点：**新增 `level-2.yaml`（`extends: 1`）**，`delivery` 节**重述完整**（`required/none_requires_reason/non_none_requires_ref/method_enum`），因 `load_contract` 顶层键浅合并；**不改 level-1**；M9 登记 sha256；M10 `UPGRADING.md` 记录。
- 生效面：仅**非 legacy 且 task_level ≥ 2** 的新声明（`gate_p8` 的 `if task_level(task_dir) is not None` 分支，M1 施加枚举校验）；**legacy 走 :2288 子串路径，不受影响**（BDD-20 锚）。

**决策 5 — P8→READY 移出 tag 后三项检查何去何从**：
- **version 文件检查 → 移除**（M1/M2/M3/M5/M15；BDD-3）。
- **tag 存在性检查 → 移除**（M1 删 WARNING 块 + 删 `VERSION_TAG_PREFIX` 使用；BDD-2）。
- **CHANGELOG → 保留**（BDD-4/5），但**载体改为 `check-changelog.py <task_id>`**（`[Unreleased]` 含 task_id）。**据此定死（NB-2）**：`gate_p8:2339-2356` 的「CHANGELOG 暂存区 diff WARNING 块」**删**（不是改述——其判据与 `check-changelog.py` 重复、且更弱）。**判据强度不降**：该载体已在 P8 必经路径 `pre-commit-gate.py:1086-1091` 被调用（且与原块**同为 WARNING-only**，不改变 `(rc, ERROR 集合)`）；M2 卡 gate 规则以**一行 `check-changelog.py <task_id>`** 表达该要求的载体。
- **`bump_type` / `debt_check` / `delivery` / RM 反查 → 保留**（BDD-6/7/16/17/13）。
- **七处一致口径**：M2(P8 卡) / M3(state-machine) / M4(state-transitions) / M5(phases.yaml) / M15(dispatch-protocol) / M16(implementer.md) / M6+M7(obligations+测试)——**同一句**「READY 前置 = 交付物 + CHANGELOG `[Unreleased]` 含 task_id + `bump_type` 意图 + 交付收尾 + CI 全绿（含 push 口径）；**不含** version bump / tag」。BDD-1/14/21。

**决策 6 — `release.preset` 声明层处置**（BDD-19；**NB-1 已裁定**）：**删除** `gate_p8` 的迁移期提示块（M1，其存在性触发条件 `cached_version/recent_version/cached_changelog/recent_changelog` 与文案「version/CHANGELOG/tag 检查」均基于已移除项）⇒ **不留悬空提示**。`agate.config.yaml` 与 `agate_common` 默认值（:919）**保持**——**如实改述（NB-1）**：该键**无任何值消费方**（**不是**「旧唯一消费点被删才变死键」；三处 `grep` 命中均非「读值」，见 §1.2）；经主 Agent 裁定**保留为信息性声明、不驱动逻辑**，登记 **DEBT0069**；**M11 发布门不消费该键**（改用会超 BDD-19 要求）。收尾跑 consistency 0 ERROR 兜底。

**决策 7 — 批次划分**：见 §4。**8 批**，`parallel_limit: 8`（门禁 `len(batches) ≤ parallel_limit`），`mode: static-batch`；首批判据一 **Tracer Bullet**。

**决策 8 — R6 corpus 前置形态（NB-3）**：把 `P5_r6` 的「备 corpus」从**人记**改为**机械**——新增 wrapper `docs/design-notes/r6-differential-prepare.sh`（落在 `docs/design-notes/` 旁、**非** `agate/scripts/` ⇒ **零登记面**，见 §1.4）：**先 `cp -a` 建一次性整仓 corpus（保留 `.git`，供差分脚本 `git archive` 解析 before）+ 重置为干净工作树，再 `exec` 既有的 `r6-differential.sh --corpus <dst>`**。`P5_r6` 的 gate 命令改为**调该 wrapper**（见 §5）——运行者**无需记得先备 corpus**（wrapper 每次 `rm -rf` 重建 ⇒ 亦无陈旧 corpus 致假失败）。批归属 = §4 的 `r6-harness`。

---

## 4. 批次设计（dispatch_plan 对照）

- **编排模式**：`static-batch`（改动面按文件分组，组间低耦合，可静态切批）。
- **parallel_limit: 8**（= 批数；仅上界，不强制全并行）。
- **首批 = Tracer Bullet（判据一）**：`ready-no-tag` 先端到端打通「**READY/P8 不再要求 tag/version**」这条最小路径（gate 侧 + 冒烟测试），再铺文档/契约/工作流。
- **硬规则核对**：任一维度 high 的批已拆分（本任务整体 high，按文件面切成 **8** 批）；每批**产出 ≤3**（见下表）；**资源密集型批默认串行**——凡 `gate_commands.P5`（全量 pytest `-n auto`）/R6 差分，**串行**执行（不并入并行批）。

| 批 id | 复杂度 | 产出文件（≤3） | 交付能力（判据二·垂直切片） | tests_filter（批级绿灯） |
|-------|--------|----------------|------------------------------|--------------------------|
| `ready-no-tag` | high | `agate/scripts/check-gate.py` | **能力**：P8 gate 不再要求 version/tag，交付止于 READY | `python -m pytest agate/tests/unit/test_tag0051_p8_gate.py -q` |
| `p8-surfaces` | high | `agate/phase-cards/P8-release.md`、`agate/state-machine.md`、`agate/rules/state-transitions.md` | **能力**：P8/READY 卡片与状态机口径去除 tag/version 条件 | —（文档） |
| `p8-rules-roles` | medium | `agate/rules/phases.yaml`、`agate/dispatch-protocol.md`、`agate/assets/execution-roles/implementer.md` | **能力**：规则表/派发协议/角色文件与 READY 新语义一致 | —（文档/规则） |
| `delivery-contract` | medium | `agate/rules/task-data/level-2.yaml`、`agate/rules/task-data/LEVELS.yaml`、`agate/UPGRADING.md` | **能力**：`delivery.method` 取值域作为**新契约级**登记并冻结 | —（契约） |
| `obligations-sync` | medium | `agate/rules/obligations.yaml`、`agate/tests/unit/test_tag0050_obligations_enforcement.py`、`agate/tests/unit/test_tag0050_obligation_behavior.py` | **能力**：`OBL-P8-*` 十四条去 tag/version 语义收敛（04 重挂为 `method_enum`、05/08/13 改述、余保留）+ 新增 BDD-21 机械断言 ⇒ obligations/anchor/测试三者同步且**M 计数不降** | `python -m pytest agate/tests/unit/test_tag0050_obligations_enforcement.py agate/tests/unit/test_tag0050_obligation_behavior.py -q` |
| `release-gate` | high | `agate/scripts/agate-release.py`、`.github/workflows/release.yml`、`agate/tests/unit/test_release_gate.py` | **能力**：独立发布门（CI success + CHECK 7/13 + RM done）+ `workflow_dispatch` 入口 | `python -m pytest agate/tests/unit/test_release_gate.py -q` |
| `release-docs` | low | `AGENTS.md`、`agate/git-integration.md` | **能力**：本仓发布清单 tag 时点统一 + 失败处置显式 | —（文档） |
| `r6-harness` | low | `docs/design-notes/r6-differential-prepare.sh`（**新增**，NB-3） | **能力**：BDD-20 验收锚（R6 双向差分）**一键可跑**——wrapper 备 corpus → 调 `r6-differential.sh` | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus`（冒烟：不得 `corpus 不存在`） |

**批级 `expected_red` 说明**：`ready-no-tag` 批若 P3 红灯测试落在其 `tests_filter` 命中范围内（如 OBL-P8-04 相关用例属 `obligations-sync` 批面）→ 由运行者在 `P4-evidence/ready-no-tag.log` 的 `expected_red` 键声明，**不写进本文件**。批 `id` 均 `[A-Za-z0-9._-]+`（filename-safe）。

**跨批共享件**：`check-gate.py`（仅 `ready-no-tag` 批改）、`agate-release.py`（仅 `release-gate` 批改）——**同一文件不跨批改两轮**。契约 `level-2.yaml`（`delivery-contract` 批新增）在 `ready-no-tag` 批**之后**落地：`ready-no-tag` 的枚举钩子读不到 `method_enum` 时 **no-op**（向后兼容），故两批顺序无关但**建议 `delivery-contract` 先于其派生测试**。

> **`output` 键未写入 `dispatch_plan`（工具限制，如实登记）**：上面「产出文件」列以**表格正文**表达。可选的机器键 `output: [...]`（每批文件列表）**未落 frontmatter**——`agate-frontmatter-check.py` 的 `MAX_DEPTH = 3` 对**所有** frontmatter 字段做嵌套深度校验，而 `batches[].output`（列表套在批次对象内）深度达 **4** ⇒ `check-frontmatter.py` exit 1（实测：`dispatch_plan: 嵌套深度超过 3 层`）。`output` 仅供 `check-mvwu.py --observe` 读取、**不新增任何 gate 校验**（P2 卡明示「缺省、写错都不影响任何阶段 gate」），故省略不影响机械面，文件的批产出面以 §4 表格为准。`tests_filter`（字符串，不加深深度）已保留。

---

## 5. gate_commands

> 本仓 `agate.config.yaml::verify.commands` 四条为权威验证面；下表逐 key 拆开（**不用 `&&` 拼接**）。`P3` 走 `AGATE_TDD_TIMEOUT`（不受 `_timeout_seconds` 覆盖）。

gate_commands:
  P3: "python3 -m pytest agate/tests/ -q"
  P5: "python3 -m pytest agate/tests/ -q -n auto"
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py"
  P5_count: "bash agate/tests/scripts/count-tests.sh"
  P5_ruff: "$HOME/.venvs/agate-dev/bin/ruff check agate/"
  P5_obligations: "python3 agate/scripts/check-obligations.py"
  P5_sg6: "python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -q"
  P5_r6: "bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus"
  P5_timeout_seconds: 600
  P5_r6_timeout_seconds: 600
**说明**：
- `P5` = 全量回归（`-n auto`）；`P5_consistency`（CHECK 7/13 等 0 ERROR）= **架构适应度检查**（本任务的硬约束：跨文件判据一致性）；`P5_obligations`（obligations anchor 无悬空 + M 计数不降，BDD-21）；`P5_sg6`（脚本登记面无漂移，R4）；`P5_r6`（legacy 行为不变，BDD-20）。`P5_r6` 经 **wrapper**（NB-3）建 `/tmp/opencode` 一次性 corpus 后跑差分，**不触碰真实仓库**；wrapper 内含跑前/跑后原仓干净自核验。
- **架构适应度检查（判据三）**：本任务涉及的架构约束 = ①「判据单源」（`P5_consistency`/`P5_sg6` 覆盖）+ ②「legacy 兼容」（`P5_r6` 覆盖）+ ③「公共 API 稳定」（协议 gate 行为，`P5` 覆盖）。故无另配。
- **`P5_r6` 前置（NB-3：已机械化为 wrapper，不依赖人记）**：`docs/design-notes/r6-differential-prepare.sh`（批 `r6-harness` 新增，**非** `agate/scripts/` ⇒ 零登记面）依次做：① `rm -rf <dst>`；② `cp -a <src> <dst>`（**整仓**副本，保留 `.git`——`r6-differential.sh` 要 `git -C corpus archive <before> agate` 解析 before 协议）；③ `git -C <dst> checkout -- .` + `git -C <dst> clean -fdx`（定格为**干净工作树**，满足脚本 `git status --porcelain` 为空的自核验）；④ `exec` `r6-differential.sh --corpus <dst>`。⇒ 运行者**无需记得先备 corpus**，且每次重建 ⇒ **无陈旧 corpus 致假失败**。真实仓库只在 ① 被**只读**（`cp -a` 读取）⇒ 跑前/跑后 `git status --porcelain` 不变。
- **`_timeout_seconds` 档位**：`P5`（全量单测类）取 **600s**（本仓 2920 用例 + 双平台回归余量，宁高不误杀）；`P5_r6`（差分，遍历全量 legacy 任务）取 **600s**。`P3` 不声明（走环境变量机制）。

---

## 6. files_to_read（P4 implementer 上下文地图——只列确实要参考的）

files_to_read:
  - path: agate/scripts/check-gate.py
    why: gate_p8 改造落点（M1）；结构化 delivery 分支 :2255-2292、version :2317-2337、CHANGELOG :2339-2356、迁移期 :2358-2374、tag :2376-2389、RM 反查 :2294-2315
  - path: agate/scripts/agate-release.py
    why: 新增 gate 子命令（M11）；其 argparse 结构 :330-348 与既有子命令风格（不破坏 build/notes）
  - path: agate/scripts/agate_common.py
    why: load_contract（:含 extends 链浅合并）/ task_level / is_legal_gate_key / default_branch（发布门解析仓库用）
  - path: agate/rules/task-data/level-1.yaml
    why: 对照 delivery 契约节（:52-56）写 level-2；**不改本文件**
  - path: agate/rules/task-data/LEVELS.yaml
    why: 新快照登记格式（level/file/sha256）
  - path: agate/phase-cards/P8-release.md
    why: M2 落点（:11-12/:74-75/:87-88/:99-103/:122/:156）
  - path: agate/state-machine.md
    why: M3 落点（:165 转移 / :177 READY 收尾 / 新增授权说明）
  - path: agate/rules/phases.yaml
    why: M5 落点（P8 节 :161-173，gates :167/:169、task_fields :171）
  - path: agate/rules/obligations.yaml
    why: M6 落点（OBL-P8-01..14，:717-828）
  - path: .github/workflows/release.yml
    why: M12 落点（on :4-6 加 workflow_dispatch；保留 :33-65 校验步；新增 gate 步）
  - path: agate/dispatch-protocol.md
    why: M15 落点（:881 P8→READY 行）
  - path: agate/assets/execution-roles/implementer.md
    why: M16 落点（:101）
  - path: AGENTS.md
    why: M13 落点（版本发布清单 :188-205，三处 tag 时点）——本仓维护文档
  - path: agate/git-integration.md
    why: M14 落点（:185-188 release PR merge + G-5）
  - path: agate/tests/unit/test_tag0050_obligations_enforcement.py
    why: M7——OBL-P8-04 就地重挂后 `M_IDS` 保持含该 id；并**新增** BDD-21 机械断言（statement 无 version/tag 期词汇 + OBL-P8-04 仍为 M）
  - path: agate/tests/unit/test_tag0050_obligation_behavior.py
    why: M7 回归锁——OBL-P8-01/02/03 behavior 断言（**不改**，仍在批 tests_filter 内）
  - path: docs/design-notes/r6-differential.sh
    why: BDD-20 验收锚；批 `r6-harness` 在其旁新增 wrapper `r6-differential-prepare.sh`（NB-3）须复用其接口（`--corpus`/`--allow`、corpus 须为含 `.git` 的整仓、跑前/跑后自核验原仓干净）
  - path: docs/design-notes/r6-differential-prepare.sh
    why: 批 `r6-harness` **新增**（NB-3）：`cp -a` 整仓副本 → 重置干净工作树 → `exec` `r6-differential.sh`（P4 新写此文件）
  - path: agate/scripts/README.md
    why: 「新增脚本登记面」节（R4 判定依据，本方案零触发）

---

## 7. env_constraints（确认 / 细化 P0-brief；不得弱化）

env_constraints:
  debug_env: "无长驻服务。本仓验证面 = agate.config.yaml::verify.commands 四条（check-protocol-consistency.py / pytest -q -n auto / count-tests.sh / ruff check agate/）；沿用 P0-brief，无补充。"
  protocol_root: "AGATE_ROOT=/home/kity/.agate/v0.81.0/agate（全局 current）；本仓无 .agate-version。gate 工具用稳定版，check-protocol-consistency.py 用本 checkout。"
  isolation_check: "R6 差分（P5_r6）经 wrapper `docs/design-notes/r6-differential-prepare.sh`（NB-3）在 /tmp/opencode 一次性 corpus 上跑（判据脚本对账本有写副作用，会污染 append-only 哈希链——AGENTS.md 工作流 0a 事故记录）。wrapper 自建 corpus（cp -a 整仓 + 重置干净工作树）⇒ **不依赖运行者记忆**；真实仓库仅被只读（cp -a 读取）。跑前/跑后核验真实仓库 git status --porcelain 与开跑前一致。r6-differential.sh 自带跑前/跑后原仓干净自核验。"
  ci_dependency: "发布门（M11）查询目标提交 CI 结论需 GitHub API（Actions 运行时有 GITHUB_TOKEN / gh；本地需 gh auth）。本地 P5/P6 对该逻辑用可注入命令（--ci-cmd / 环境变量）+ fixture/mock 验证，不依赖真实 GitHub（P1 §8 判定属验证方式非能力缺口）。"
  branch_neutrality: "协议不得假设项目分支/流程（RM-AG0116）：发布门经 git remote / gh 解析仓库，不写死 main。"
  external_authorization: "不可逆外部动作（push / PR / merge / tag / Release / 改分支保护）须用户授权，不得由 agent 自动执行。workflow_dispatch 由人工触发。当前未预见必须改分支保护（required 6 项），若实现判定需要 → 登记为「需人工授权的一次性步骤」。"
  prod_env: "不写（生产环境不在 agate 范围内；[PROD_NOT_TOUCHED]）。"

> **边界提醒**：`env_constraints` 是**声明性字段**，不被自动执行。故上述可强制项已落到 `gate_commands`（`P5_r6` / `P5_consistency` / `P5_sg6` / `P5_obligations`）——R6 隔离、判据单源、登记面无漂移、obligations 无悬空均有 exit code 判据。

---

## 8. minimal_validation（结果 — 只读实测，2026-10-11）

> 卡强制：方案依赖**外部系统行为**（`workflow_dispatch` 语义、按 commit 查 CI 结论的 API 形状）⇒ 已做只读最小验证（`gh api` GET / `gh workflow list` / `gh run list`）。**未做任何写操作**。

minimal_validation:
  - assumption: "release.yml 可加 workflow_dispatch 与既有 push:tags 触发器并存（BDD-8 可行）"
    method: "读 .github/workflows/release.yml（:4-6 仅 push:tags）+ 对照仓库内既有 workflow_dispatch 先例 .github/workflows/deploy-pages.yml（on: push:branches + workflow_dispatch: 并存）+ `gh workflow list` 确认 Release workflow 存在（ID 362590833）"
    result: "confirmed"
    note: "deploy-pages.yml 实证「push + workflow_dispatch」并存可行；release.yml 当前无 workflow_dispatch，添加即可（workflow 文件随 PR 合并生效，无需外部设置）。"
  - assumption: "存在只读 API 可按「目标提交」查询 CI 结论（BDD-9/10 的载体）"
    method: "`gh api repos/randomgitsrc/agateon/commits/<origin/main sha>/check-runs`（GET）；`gh api repos/.../actions/runs?head_sha=<sha>`；`gh api repos/.../commits/<sha>/status`；`gh run list --commit <sha>`"
    result: "confirmed"
    note: "check-runs 返回 {name,status,conclusion}（本次 total=11，含 required 6：shellcheck×2/pytest×2/consistency/gate-backstop，全部 conclusion=success）；actions/runs?head_sha= 返回 workflow run 列表；**combined status API 返回 state=pending,total_count=0**（本仓无 legacy commit status）⇒ **发布门必须查 check-runs（或 GraphQL statusCheckRollup 合并），不能只查 combined status**。据此设计门按 required contexts 逐项要求 conclusion==success。"
  - assumption: "required contexts 集合（发布门应校验的检查面）"
    method: "`gh api repos/randomgitsrc/agateon/branches/main/protection --jq '{strict,contexts,enforce_admins}'`（GET）"
    result: "confirmed"
    note: "contexts = [shellcheck (ubuntu-latest), shellcheck (windows-latest), pytest (ubuntu-latest), pytest (windows-latest), consistency, gate-backstop]；strict=true；enforce_admins=true。发布门以该 6 项为「CI success」判据（与 P1 §8/P0 一致）。"
  - assumption: "竞态：跑门当下 CI 可能未完成（无法本地验证具体时点，只验证 API 能区分状态）"
    method: "`gh run list --workflow protocol-tests.yml`（观察 status ∈ {queued,in_progress,completed}）+ 读 P0-brief known_risks 第 4 条"
    result: "confirmed"
    note: "API 的 status 字段可区分未完成/完成 ⇒ 门可对非 success（含 in_progress/queued）fail-closed。**未在真实发布窗口触发竞态**（属运行时现象），按设计 3 以「前置顺序 + fail-closed」处理。"
  - assumption: "发布门落点登记的 SG.6 / CHECK9-coverage 触发面（R4）"
    method: "沿用 P1 §4.10 实跑探针法（`/tmp/opencode` 副本，探针后核验真实仓库干净）：探针 check-*.py → SG.6 红 + CHECK9-coverage WARNING；探针 agate-*.py → 零触发"
    result: "confirmed"
    note: "本方案**不新增/不改名** agate/scripts 文件（改既有 check-gate.py、扩展既有 agate-release.py）⇒ 三处（CHECK 9 / SG.6 / CHECK 10）均无适用项。P1 探针结论可复用。"
  - assumption: "dispatch_plan 字段可被 gate 解析（本文件已声明）"
    method: "`FILE=<probe> agate-md-field-get.py dispatch_plan`（frontmatter flow YAML → 输出 JSON）"
    result: "confirmed"
    note: "get 工具对 dict 字段输出 json.dumps；`check-gate.py::_gate_p2_dispatch_plan` 据此 json.loads 校验。**注**：`agate-md-field-set.py set dispatch_plan` 报「追加/嵌套字段不支持」——工具缺口，已在文首登记上报（超出 DEBT0067 面）。"

> 纯代码逻辑（内部函数/数据转换）部分：`gate_p8` 的枚举校验依赖 `_delivery_spec`/`load_contract`/`task_level`（`agate_common`）与 `split_frontmatter`；`load_contract` 的 extends 链浅合并语义已在 §决策 4/M8 说明（level-2 须重述完整 `delivery` 节）。此部分无外部系统依赖。

---

## 9. 完成标准与 BDD 覆盖映射（P3/P5 依此判定）

**实现完成的标志（可判定）**：
1. `check-gate.py P8 <fixture 无 tag>` → exit **2** 且 stderr **无** tag/version 告警（BDD-2/3）。
2. `check-changelog.py <task_id>` 在 `[Unreleased]` 含/不含 task_id 时分别 exit **0/1**（BDD-4/5，回归锁）。
3. 非 legacy 且 level ≥2 任务：`delivery.method` 合法枚举 → exit 2；枚举外非空 → exit 1（BDD-16/17）；缺 `bump_type` → exit 1（BDD-7）。
4. `release.yml` 的 `on:` 含 `workflow_dispatch`（BDD-8）；`agate-release.py gate` 对 CI 非 success / CHECK 7/13 ERROR / RM 非 done 均非 0（BDD-9/10/12/13）。
5. BDD-1 六文件语料检索「tag 作为 P8 条件/动作」**零命中**。
6. `AGENTS.md`/`git-integration.md` 全文 tag 时点**一致**，含失败处置（BDD-14/15）。
7. `check-obligations.py` 输出 `M 类占比: 56/121`（**不得低于基线**，exit 0）+ `test_tag0050_obligations_*` 全绿、anchor 无悬空（BDD-21）；`obligations.yaml` **无条目删除**、无 `baseline.reset.to`。
7a. **BDD-21 机械断言（新增）**：`test_tag0050_obligations_enforcement.py` 内遍历 `OBL-P8-*` statement，断言**不含** version/tag 期词汇（`新版本号`/`version 文件变更`/`双路径`/`bump 后`/`git tag`）且 `OBL-P8-04.disposition == "M"`、statement 含 `method_enum`（把「语义一致」降为可判定）。
8. R6 双向差分未匹配差异 **0 条**（经 wrapper `r6-differential-prepare.sh` 一键跑）+ 真实仓库跑前/跑后 `git status --porcelain` 一致（BDD-20）。
9. consistency **0 ERROR**（BDD-12/19）。

| BDD | 承接落点（本设计） |
|-----|-------------------|
| 1 | M2-M6/M15/M16 七处一致口径 + BDD-1 六文件语料 grep |
| 2 | M1（删 gate_p8 tag WARNING 块） |
| 3 | M1（删 version WARNING 块）+ M2/M3/M5/M15 |
| 4/5 | `check-changelog.py`（不改）为**唯一** CHANGELOG 载体（P8 必经路径 `pre-commit-gate.py:1086`）+ M1 **删** gate_p8 CHANGELOG diff WARNING 块（:2339-2356）+ M2 卡 gate 规则以 `check-changelog.py <task_id>` 行表达 |
| 6/7 | M1（保留 bump_type exit 1） |
| 8 | M12（release.yml 加 workflow_dispatch） |
| 9/10 | M11（`gate` 查 check-runs，非 success fail-closed） |
| 11 | M12（保留 release.yml「Verify tag points to matching commit」步，不重新实现） |
| 12 | M11（门跑 `check-protocol-consistency.py` 0 ERROR） |
| 13 | M11（门复用 `check-gate.py P8` 的 RM-AG0043 反查） |
| 14 | M13/M14（AGENTS.md + git-integration.md tag 时点统一） |
| 15 | M13（AGENTS.md 新增「发布失败处置」小节） |
| 16/17 | M1（枚举钩子）+ M8/M9/M10（level-2 契约）+ **P3 level-2 fixture（来源与构造见 §9.1）** |
| 18 | M3（state-machine.md 显式发布授权 + 不引第二套阻塞语义） |
| 19 | M1（删迁移期提示块）+ M10（UPGRADING 记录）+ consistency 0 ERROR |
| 20 | §5 `P5_r6`（wrapper `r6-differential-prepare.sh` 建副本 → `r6-differential.sh`，`r6-harness` 批） |
| 21 | M6/M7（`OBL-P8-*` 十四条逐条 + **BDD-21 机械断言** + `M_IDS` 保持）+ `P5_obligations`（M 计数 56/121 不降） |
| 22 | 每批改 `agate/` 的 commit message 含 `self-gate-review:`（SELF-GATE，逐批） |
| 23 | R4（落点 = 既有 `agate-*.py` ⇒ BDD-23 支②：零触发；`P5_sg6` 兜底） |

### 9.1 P3 所需 **level-2 fixture** 的来源与构造方式（补评审「测试缺口 #2」）

**问题**：BDD-16/17（`delivery.method` 枚举）只在「**非 legacy 且 `task_level ≥ 2`**」任务上生效（M1 的枚举钩子在 `gate_p8` 的 `if task_level(task_dir) is not None:` 分支内）；而本仓当前**唯一**非 legacy 任务是 TAG0051 自身（`contract_level` **1**，`level-1.yaml` 无 `method_enum` ⇒ **no-op**）⇒ **不构造 level-2 fixture 则红灯不成立**（P3 无法先红）。

**fixture 来源**（沿用既有黄金 fixture 形态，**不新造机制**）：
- 参照 `agate/tests/fixtures/task-data/level-1/{pass,fail}/gate-events.jsonl`（每目录一份账本，首行 `task_created`，字段 `{event,task_id,contract_level,prev_hash,ts}`，`prev_hash` = `sha256(b"")` GENESIS）。
- **P3 新增**（属 P3 测试面，不计入 §4 批产出）：`agate/tests/fixtures/task-data/level-2/pass/` 与 `level-2/fail/`，其 `gate-events.jsonl` 首行 `task_created` 的 **`contract_level: 2`**（可复用 `helpers_tag0050.py` 的账本构造：GENESIS 首行 + 逐行 sha256 链 + 单调 ts）。
- **等级判定链**：`agate_common.task_level(task_dir)`（:2084）读账本 `task_created.contract_level` / `task_upgraded.to_level` ⇒ fixture 账本即决定 `task_level`，**无需真实任务目录**。

**P3 用例构造方式**：以 `tmp_path` 复制 fixture 账本到临时任务目录（附最小 `P8-release.md` + `.state.yaml` + roadmap），令 `task_level == 2` 且 `delivery.method` 取值分档：合法枚举（`release-notes`）→ `check-gate.py P8` exit **2**；枚举外非空（如 `bogus`）→ exit **1**。经 `AGATE_ROOT` 指向本 checkout（与既有 TAG0050 用例同法）。
> ⚠️ 可选加固（非本任务必需）：`test_tag0050_fitness.py::test_task_data_golden_fixture_regression` 现仅硬编码校验 `level-1` 黄金 fixture；若要在 CI 覆盖 level-2 黄金 fixture，可扩展为遍历 `LEVELS.yaml` 已登记等级——**属 P3 决定**，P2 不预判（不写进 gate）。

---

## 10. [SCOPE+] 与登记缺口（如实上报）

- **无新增 BDD 需求**（本设计未发现 P1 未预见的必须动作）。
- **工具缺口 1（登记，非静默绕过）**：`agate-md-field-set.py` **拒写 `dispatch_plan`**（归「追加/嵌套字段」）——与 DEBT0067（`ceremony`/`delivery`/`debt_check` 读侧认写侧不认）**同簇但不同键**。本文件按 P2 卡「dispatch_plan 机器字段」节直接落（该键不入 schema，gate 经 `agate-md-field-get` 读后 `json.loads` 校验，已实测）。**建议主 Agent 评估是否并入 DEBT0067 面（本任务不处理，主题不同簇）。**
- **工具缺口 2（登记，非静默绕过）**：P2 卡「batches[] 可选键」节把 `output: [...]` 列为合法可选键，但 `agate-frontmatter-check.py::MAX_DEPTH = 3` 对**所有**字段做深度校验 ⇒ `batches[].output`（深度 4）致 `check-frontmatter.py` fail。二者口径**互相矛盾**（卡说可写，checker 说太深）。本文件按 **checker 为准**省略 `output`（`output` 无 gate 效力），并把批产出面写入 §4 表格。**建议登记为独立 DEBT**（卡文本 vs frontmatter-check 的 `MAX_DEPTH` 不一致，会影响后续所有用 `output` 的 P2）。
- **[PROD_NOT_TOUCHED]**：本阶段只读，未触发任何写操作。

---

> 完成 → 读 `phase-cards/P3-tdd.md`
