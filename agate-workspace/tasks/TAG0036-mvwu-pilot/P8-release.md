---
phase: P8
task_id: TAG0036
parent: P7-consistency.md
trace_id: TAG0036-P8-20260919
type: release
created: '2026-09-19'
agent: implementer
status: draft
bump_type: minor
debt_check: reviewed
---

# P8-release — TAG0036 MVWU 阶段 1 观测（RM-AG0063 阶段 1）

`[PROD_NOT_TOUCHED]`

> 本文件由 releaser subagent（implementer P8 模式）产出。**不执行 git add/commit/tag/push、不执行 bump-version，
> 不直接编辑 README.md / README.zh-CN.md / CHANGELOG.md / agate/UPGRADING.md /
> agate-workspace/roadmap/roadmap.md / agate-workspace/debt/tech-debt.md**——以下各节只给出「主 Agent gate
> 验证通过后可直接采用」的文本与核实清单；实际文件编辑由主 Agent 亲自执行。
> 本文件**不声称**已发布 / 已 tag / 已合并（这些是主 Agent 与用户的后续动作）。

## 1. bump_type 判定

`bump_type: minor`（当前 `v0.71.1` → 建议 `v0.72.0`；最终版本号由主 Agent 采纳）

**核实过程**（逐条读 `P1-requirements.md` 的 71 条 `#### BDD-N:` 标题，`grep -nE '^#{2,4} .*BDD-[0-9]+'` 取得，
与 P7 §3「P1 71 = P6 71 = P6.5 71」一致）：

| 组 | BDD | 性质 | 是否破坏性 |
|---|---|---|---|
| A. `tests_filter` / `output` 可选键 | 1-4、9（9 = 写入说明，文档面） | 新增 `dispatch_plan.batches[]` **可选**键；BDD-3「缺省时既有 P2 gate 行为不变（回归）」、BDD-4「含/不含可混用」 | 否（可选、缺省不变） |
| B. 同类 fail-open 登记 | 5 | 只登记 DEBT0043、不修（零内核） | 否 |
| C. 协议文档新增节 | 6-8、10-12 | P2 卡 / architect.md / P4 卡 / task-files.md 新增写法说明与 `P4-evidence/{batch}.log` 落点约定；BDD-12「证据落点不改任何 gate/hook/审计/judge 登记面」 | 否（纯文档新增） |
| D. `check-mvwu.py` 新脚本 | 13-58 | **新建**独立观测脚本：六项检查 + 四态 verdict + `--observe`；BDD-36/37/38「任一 verdict 均 exit 0、只读、不阻断」 | 否（新增、不挂 gate） |
| E. ⑤ 组方法学概念成文 | 59-66 | CONTEXT.md +5 术语、role-system.md 审查锚点节、architect.md/P2 卡三判据 + Walking Skeleton 消歧、adr.md 复审触发条件、`decisions/` 落点 | 否（纯文档新增） |
| F. 零内核 / 回归 / 收口 | 67-71 | BDD-67「零协议内核改动（负向、可机械判定）」、BDD-68「不挂 gate、未触碰历史任务产物」、BDD-69 登记面同步、BDD-70/71 SELF-GATE 收口 | 否 |

**为何不是 `patch`**：`patch` 判据是「修 bug / 不改 API 行为」（先例 TAG0035 v0.71.1：14 条 BDD 无一新增能力）。
本任务恰相反——新增一个脚本（`agate/scripts/check-mvwu.py`，+484 行）、新增两个 frontmatter 可选键、新增
`P4-evidence/` 目录约定与多处协议文档节，均为**对外可见的新增能力**，故不能算 patch。先例对照：v0.71.0
（TAG0034 派发路由，新增子命令 + 新 helper + 新事件）判 `minor`，同属「新增、向后兼容」性质。

**为何不是 `major`**：逐项核实无破坏性变更——
- **零协议内核**：`P2-design.md` §0.2 逐条列出「不改什么」（`check-gate.py` 含 `_gate_p2_dispatch_plan`、`agate_common.py`、
  `rules/`（`phases.yaml`/`schema/`）、hook 三件套、`check-state-*`、`check-events.py`、`check-p6-provenance.py`、
  `check-judge-verdict.py`、`pre-commit-gate.py`、`assets/review-roles/judge.md`、`dispatch-protocol.md` 等）；
  P7 §6 用 `git diff efb113b --stat` 实测上述文件零 diff；P5 `P5_kernel_diff` / `P5_kernel_diff_wt` / `P5_roles_diff` /
  `P5_history_untouched` 均 rc=0（`P5-progress.md`）。
- **无 schema / 审计链 / gate 分支 / hook 改动**：未改 `.state.yaml` schema、3 个 hook 薄壳、`phases.yaml`。
- **新键为可选**：`tests_filter` / `output` 缺省时既有 34 个历史任务的 P2 gate 行为不变（BDD-3）；`_gate_p2_dispatch_plan` 不拒绝未知键
  （P0-brief 实测，P6 BDD-1/2 `direct-bdd-1-2-4-tests-filter-gate.log` 实跑）。
- **`check-mvwu.py` 不挂 gate/hook/CI**（BDD-36/68；`GATE_SCRIPT_EXEMPT` 仅豁免 CHECK 9，M18 一行 + P1 `[BASELINE_CHANGE]` 留痕）。
- 对既有项目**无需任何迁移动作**（见 §4）。

**结论**：向后兼容的新增 → **`minor`**。未发现应升 `major` 或降为 `patch` 的依据，与派发指引预判一致。

**版本号建议**：`v0.71.1` → `v0.72.0`。`git tag --sort=-v:refname | head -3` 实测最新 tag 为 `v0.71.1`（前为 `v0.71.0`、
`v0.70.0`），README 两处 badge 同为 `v0.71.1`。

> **附注（不影响 bump_type，供主 Agent 知悉）**：`git log v0.71.1..HEAD` 区间除本任务的 P0-P7 提交外，还含**已在分支基线
> `efb113b` 中的 main 提交**（DEBT0042 `AGATE_HOME` 基址覆盖、install 回退指引修复、DSH persona `text→prefix` 模板对齐、
> 测试 HOME 隔离、若干 docs）。这些**非 TAG0036 交付**，其中 `AGATE_HOME` 为**新增可选 env**（`AGATE_ROOT` 优先，层序不变）、
> 其余为 fix / docs / test，均**不改变本次 `minor` 判定**。但它们会随 `v0.72.0` 一并发布而 `[Unreleased]` 目前未收录——见 §3.3。

## 2. 版本号变更确认（需改文件与具体文本）

「version 文件面」= README 双语 badge（本仓库无独立 `VERSION` / `package.json`；与 TAG0035 先例一致，
`grep -rn '0\.71\.1'` 排除任务目录/CHANGELOG/UPGRADING/roadmap/tech-debt/HANDOFF 后，产品面仅命中两处 README badge；
`docs/guides/worktree-dogfooding-guide.md` 的 v0.71.1 出现均为「实测确认」历史叙述，**不应改**）。

P2 `packages: [agate-scripts, agate-docs, agate-tests]` 三值是产出分类标签，非独立发布单元（同 TAG0035 §8 结论），
本仓库单一 tag、单一 badge，**无 per-package 版本文件**；三包逐个核对如下。

| package | 旧版本 → 新版本 | 版本载体 | 包内本任务变更（`git diff --name-only main...HEAD -- . ':!agate-workspace/tasks'` 核实） | 验证命令（`P2-design.md` §gate_commands / P5） | 结果 |
|---|---|---|---|---|---|
| agate-scripts | v0.71.1 → v0.72.0 | 随仓库 tag | `agate/scripts/check-mvwu.py`（新，+484）、`agate/scripts/README.md`（+1 行）、`agate/scripts/check-protocol-consistency.py`（+1 行 `GATE_SCRIPT_EXEMPT`） | `gate_commands.P5` 中 pytest 三分片 / `P5_consistency` / `P5_ruff` / `P5_windows_smoke` | P5 全 rc=0（`P5-progress.md`：10/10；1842 passed / 2 skipped） |
| agate-docs | 同上 | 同上 | `agate/CONTEXT.md`、`agate/adr.md`、`agate/role-system.md`、`agate/phase-cards/{P2-design,P4-implementation,P7-consistency}.md`、`agate/assets/execution-roles/architect.md`、`agate/assets/templates/task-files.md`、`CHANGELOG.md`、`agate-workspace/debt/tech-debt.md`、`agate-workspace/agents/CODE-MAP.md`、`HANDOFF-TAG0036.md`（见 §9 D3） | `P5_consistency` / `P5_debt` | rc=0 |
| agate-tests | 同上 | 同上 | `agate/tests/unit/test_check_mvwu.py`（111 用例）、`agate/tests/unit/test_mvwu_protocol_docs.py`（65 用例）、`agate/tests/README.md`（+2 行） | `P5_count`（`count-tests.sh`：本次实测 `总计：1844 个测试用例` = 1668 + 111 + 65，含 2 skipped） | rc=0 |

`[SCOPE_GAP]` 核对：P2 声明的三个包均已在本节逐个处理，prompt 无遗漏 → **无 SCOPE_GAP**。

### 2.1 需改动的文件与文本（由主 Agent 执行）

| 文件 | 位置 | 旧 | 新 |
|---|---|---|---|
| `README.md` | 第 12 行 | `[![version](https://img.shields.io/badge/version-v0.71.1-blue)](https://github.com/randomgitsrc/agateon)` | `[![version](https://img.shields.io/badge/version-v0.72.0-blue)](https://github.com/randomgitsrc/agateon)` |
| `README.zh-CN.md` | 第 12 行 | 同上（`v0.71.1`） | 同上（`v0.72.0`） |
| `CHANGELOG.md` | `[Unreleased]` 节 + 新章节 | 见 §3 | 见 §3 |
| `agate/UPGRADING.md` | §3 「已知破坏性变更（按版本）」，插在 `### v0.71.1` 之前 | — | 见 §4 |
| `agate-workspace/roadmap/roadmap.md` | RM-AG0063 主表行 + 详情节 | 见 §5 | 见 §5 |
| `agate-workspace/debt/tech-debt.md` | 无需改（见 §6） | — | — |

仅 badge 中版本号字符串一处改动，其余徽章不动（与 TAG0035 先例同）。**不要**改 `docs/guides/worktree-dogfooding-guide.md`。

**CHECK 7 / DEBT0013 时序提醒**：bump badge 后、创建 tag 前跑 `check-protocol-consistency.py` 必报
`badge v0.72.0 != tag v0.71.1`（设计使然）。P5 复核请安排在 **commit + tag 之后**。

## 3. CHANGELOG 更新确认

### 3.1 现状核实

- `CHANGELOG.md` 第 11 行 `## [Unreleased]`，其下已有 `### 新增（TAG0036：MVWU 阶段 1 观测，RM-AG0063）`（含
  `check-mvwu.py` / `tests_filter` 可选键 / `P4-evidence/<id>.log` 落点 / ⑤ 组成文与登记四条 + 「来源：TAG0036（RM-AG0063）。」）；
  用例数已是 **111 / 65**（P7 D1 已由 `9e9e369` 修正，实测 `pytest --collect-only` 与 `count-tests.sh` 1844 = 1668 + 111 + 65 一致）。
- 最近已发布章节格式：`## [0.71.1] - 2026-09-16`（**无 `v` 前缀**，方括号内仅数字版本号）；`### 修复（…）` 子节；末尾 `来源：…`。
  `check-protocol-consistency.py` CHECK 13 的正则为 `^## \[(\d+\.\d+\.\d+)\]`，**带 `v` 的标题会被视为无已发布版本并跳过校验**，
  故务必用 `## [0.72.0]`（**与派发指引示例 `## [vX.Y.Z]` 不同——以既有章节格式与 CHECK 13 为准**）。
- 上一次发布（`ac2cc73`）后空 `[Unreleased]` 的写法为：`（暂无——下个版本的变更在此累积。）`（`git show ac2cc73:CHANGELOG.md` 实测）。

### 3.2 具体做法（Edit 级别）

把

```markdown
## [Unreleased]

### 新增（TAG0036：MVWU 阶段 1 观测，RM-AG0063）
```

改为

```markdown
## [Unreleased]

（暂无——下个版本的变更在此累积。）

## [0.72.0] - 2026-09-19

### 新增（TAG0036：MVWU 阶段 1 观测，RM-AG0063）
```

其余 TAG0036 小节正文**原样保留**（`来源：TAG0036（RM-AG0063）。` 之后紧接现有的 `## [0.71.1] - 2026-09-16`，中间保持一个空行）。
若采纳 §3.3 建议，则在「来源：TAG0036（RM-AG0063）。」之后、`## [0.71.1]` 之前追加相应小节。

### 3.3 `git log v0.71.1..HEAD` 与 CHANGELOG 遗漏核对

命令：`git log v0.71.1..HEAD --oneline`（共约 60 行，含 P0-P7 的 12 条 `wf(TAG0036-P*)` / `docs` 提交与 main 基线提交），
以及 `git log v0.71.1..HEAD --oneline -- CHANGELOG.md`（仅 `4ee499f`、`9e9e369` 两条改过 CHANGELOG，均为 TAG0036）。

- **本任务交付**：`CHANGELOG [Unreleased]` 四条与 P2 §0.1 M1-M18 / P7 §5 逐项对得上，**无遗漏**（`check-protocol-consistency.py` 的 M18
  一行、`tech-debt.md` 的 DEBT0043、CODE-MAP 一行属登记面同步，与 P7 §4 一致；DEBT0043 是否入 CHANGELOG 见 §3.4）。
- **[SUGGEST] 基线 main 提交（非 TAG0036 交付）未入 CHANGELOG**：`git diff v0.71.1..HEAD --stat` 显示以下产品面/文档改动落在
  本次发布区间内，但 `[Unreleased]` 无任何相关条目（`grep -c AGATE_HOME CHANGELOG.md` = 0）。派发指引限定「只需覆盖本任务交付」，
  故本节仅作 **[SUGGEST] 交主 Agent 决定是否补记**（不补也不影响 gate；若补，建议放在 TAG0036 小节之后的独立小节）：

  ```markdown
  ### 其他（随本版本发布的 main 基线变更，非 TAG0036 交付）

  - **`AGATE_HOME` 基址覆盖（DEBT0042）**：`agate_common._resolve_version_info` 与 `agate-install.py` 支持以 `AGATE_HOME`
    覆盖版本根基址（默认 `~/.agate`）；层序不变（`AGATE_ROOT` > `AGATE_HOME` > 项目 `.agate-version` > `current` > legacy 软链），
    未设置时行为不变。主要用途为测试隔离。
  - **修复**：`agate-install` 回退指引歧义（`UPGRADING.md` 拆为单项目 / 全局两场景，并补 DEBT0034 文案漂移护栏）；DSH 模板 persona
    必填 key `text` → `prefix`（对齐上游 schema）；`setup` 各平台接入命令的协议根路径（版本管理布局下断链）；测试 HOME 隔离（消除对本机
    `~/.agate` 状态的依赖）。
  - **文档**：`UPGRADING.md` 新增「路径层次与解析优先级」节；worktree dogfooding 指南补全发布/合并/收尾；AGENTS.md hotfix 通道与本机
    稳定版布局等。
  ```

  （文字取自 `git log v0.71.1..HEAD` 提交标题与 `agate/UPGRADING.md` 的 `git diff v0.71.1..HEAD`，未逐一读源码，主 Agent 采用前请自行核对措辞。
  **注意 DSH persona key 改名对使用旧 DSH 的用户是行为差异**——commit `de67937` 记「旧 DSH（rc.8）要 `text`」，若补记建议如实标出。）

### 3.4 DEBT0043 是否入 CHANGELOG

现有 TAG0036 小节未提 DEBT0043（fail-open 只登记未修）。P2 §0.1 M15 仅规定「替换占位」，无强制；不影响 gate。**[SUGGEST]**：不需要补，
债务登记面在 `tech-debt.md`，与 TAG0035 先例（CHANGELOG 不列债务登记动作）一致。

## 4. `agate/UPGRADING.md` 新章节文本

已读 §3 现状：第一条为 `### v0.71.1 — gate 健壮性批（…）`（第 215 行），其上为 `> 升级到新版本前，检查你的项目是否触及以下变更点。`。
新章节插在 `### v0.71.1` **之前**（最新在前）。CHECK 13 要求 `^### v0.72.0\b` 存在（CHANGELOG 最新版 `## [0.72.0]` ↔ 本章节）。
文本如下（仿 v0.71.1 / v0.71.0 结构）：

```markdown
### v0.72.0 — MVWU 阶段 1 观测（TAG0036：RM-AG0063 阶段 1）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 / `phases.yaml` / gate 分支
> （`check-gate.py` 零改动）/ 审计链（`gate-events.jsonl`、`check-p6-provenance.py`、`check-judge-verdict.py` 零改动）/
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局 `git pull` 即生效；Windows 复制模式
> 重跑 SETUP.md 步骤 2 的 `cp`）。

1. **新增 `agate/scripts/check-mvwu.py` 观测脚本——不挂 gate / hook / CI，任一 verdict 均 exit 0**：读取任务目录
   `P2-design.md` 的 `dispatch_plan.batches` 与 `P4-evidence/<id>.log`，对每批做六项静态检查并输出四态 verdict
   （`PASS` / `FAIL` / `EXPECTED_RED` / `UNKNOWN`；**`UNKNOWN` 不等价于 `PASS`，不得作为放行依据**）。只读、不改 `.state.yaml`、
   不执行 `tests_filter`。`--observe` 模式输出可粘贴进观察表的 7 列行。**既有项目不需要任何动作**；如想采集观察行，可对含
   `dispatch_plan.batches` 的任务运行 `python3 {agate_root}/scripts/check-mvwu.py --observe <task_dir>`。
2. **`dispatch_plan.batches[]` 新增两个可选键 `tests_filter` / `output`——缺省行为完全不变**：`tests_filter`（该批测试过滤表达式）
   与 `output`（该批声明的产出文件集，供 `--observe` 比对 boundary）均为**可选**；不写则既有任务的 P2 gate 结果与本版本前逐字节一致
   （`check-gate.py` 的 `_gate_p2_dispatch_plan` 不拒绝未知键，本任务未改它）。新任务由 architect 在 P2 按
   `agate/assets/execution-roles/architect.md` 新增节与 P2 阶段卡写法说明选择性填写（示例中 `python -m pytest` 仅示意，解释器名以本项目
   `AGATE_PYTHON` / `probe_python` 探测为准）。
3. **新增 `P4-evidence/{batch}.log` 证据落点约定——仅成文，不新增 gate 校验**：P4 阶段卡新节与 `task-files.md` 登记该目录与逐行
   `key: value` 格式（`command` / `exit_code` / `git_head` / `timestamp` / `expected_red` / `duration_seconds`，可选 `failed_tests`），
   由主 Agent 在批 commit 前**机械转录**测试运行结果。该目录**不进** judge 白名单 / provenance 审计面 / 目录登记（`grep P4-evidence
   agate/rules/` 0 命中）；既有项目**不需要**创建该目录，无 `P4-evidence/` 时 `check-mvwu.py` 判该批 `UNKNOWN`（reason=evidence），不报错。
4. **⑤ 组方法学概念成文——纯文档新增 / 补充**：`CONTEXT.md` 新增 5 个术语；`role-system.md` 新增「审查锚点（Deep Modules）」节；P2 卡 /
   `architect.md` 新增批切分判据（Tracer Bullet / Vertical Slice）、Walking Skeleton 吸收/拒绝说明（与既有 `P2-skeleton.md` 机制**同词
   不同义**，不动机制）、架构适应度检查（Fitness Functions，由项目自选、协议本体不提供检查）；`adr.md` 头部新增复审触发条件；P2 / P7
   卡新增 `decisions/` 落点与过时标注核对说明。**均只成文、不宣称机制已生效**，不改动既有阶段卡片判定逻辑、gate 脚本、状态机。
5. **`agate-workspace/decisions/` 目录**：仅当项目产生**跨任务架构决策**时才由项目自行创建并落笔（P2 卡写明「P2 开始前读取既有决策 /
   P2 定稿后写入」；P7 卡新增第 6 项为**核对**，缺失记为待办、不 author 决策正文）。**既有项目无需预先创建**；本仓库该目录当前不存在（`ls
   agate-workspace/decisions` 实测无此目录）。
6. **升级动作**：`git pull` 即完成；无迁移动作。老项目：无需动作；新项目：照常 `SETUP.md`，无新增步骤。（CHECK 13：CHANGELOG 最新版 ↔
   UPGRADING §3 章节一致。）
```

**[SUGGEST] 搭载项**：若主 Agent 采纳 §3.3 补记基线 main 变更，可在上述第 6 条之前追加一条「**`AGATE_HOME` 基址覆盖（DEBT0042，可选 env，
未设置时行为不变）**——详见本文件『路径层次与解析优先级』节」；该节已由基线提交 `80abcbe` 写入 `UPGRADING.md`，此处仅作指向，避免复述漂移。

## 5. roadmap 回写文本（RM-AG0063）

已读 `agate-workspace/roadmap/roadmap.md`：主表第 71 行 RM-AG0063（列：`id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新`），当前状态
`scheduled`、关联任务 `**TAG0036**`；详情节 `## RM-AG0063 详情` 起于第 606 行，末条为「⚠ SELF-GATE 澄清」（第 621 行），其后是 `---`。
`grep TAG0036 roadmap.md` 只命中该行与详情节，**无其它 RM 条目关联 TAG0036**。

P8 gate（RM-AG0043）要求：任务在 roadmap 有关联 RM 条目须先回写「状态」列为 `done`，否则阻断。本任务只完成设计文档**阶段 1**，
故按 TAG0035（RM-AG0062）先例——**标 `done` 的同时在标题格内标注范围收窄**，避免 `done` 被误读为整个 MVWU 落地完成。

### 5.1 主表行（Edit 级别，`old_string` 在文件内唯一）

- 状态列 + 范围收窄标注，把第 71 行中的

  ```
  阶段 1 零协议内核改动（旁路声明 + 证据 + 不阻断 check） | scheduled | 编排模型演进分析
  ```

  改为

  ```
  阶段 1 零协议内核改动（旁路声明 + 证据 + 不阻断 check）。**⚠ 范围收窄（2026-09-19，TAG0036 P8）：本条 `done` 仅指设计文档【阶段 1】交付（工具 + 采集能力 + 文档成文；Q1/Q3 样本待真实多批任务出现，未答）；阶段 2（批级 gate，触内核）与阶段 3（`E_pipeline` 弹性度量）未开工——前置为「Q1∧Q2 ≥90% 试点数据 + 提交粒度用户裁决」，均未满足，不因本条 done 而视为已解决。** | done | 编排模型演进分析
  ```

- 更新列，把该行行尾 `| **TAG0036** | 2026-09-16 | 2026-09-16 |` 改为 `| **TAG0036** | 2026-09-16 | 2026-09-19 |`。

（合并后该行「状态」列为 `done`，「关联任务」`TAG0036` 不变，满足 RM-AG0043 硬校验。）

### 5.2 详情节（在「⚠ SELF-GATE 澄清」条之后、`---` 之前新增一条）

```markdown
- **⚠ 状态变更（2026-09-19，TAG0036 P8）：阶段 1 已交付，阶段 2 / 3 未开工**——TAG0036 完成设计文档 §7 的**阶段 1**：① `batches[].tests_filter` /
  `output` 可选键（架构师写法成文于 P2 卡 + `architect.md`）② `P4-evidence/{batch}.log` 落点（P4 卡 + `task-files.md`）③ `agate/scripts/check-mvwu.py`
  观测器（六项检查 + 四态 verdict + `--observe`，不挂 gate/hook/CI）④ ⑤ 组 7 概念成文（CONTEXT / role-system / architect / P2 卡 / adr / P7 卡）；
  71 BDD 全部实跑取证（P6 71/71、P6.5 judge passed 71/71，P5 1842 passed / 2 skipped，零内核 diff 实测为空）。发布版本 v0.72.0。
  **完成判据 ④⑤ 的口径**：Q2 结论（13%）在案；Q1/Q3 **仅交付采集能力**（`--observe` 已在真实任务 TAG0035 上跑通，得 4 行全 UNKNOWN 的诚实样本），
  **Q1/Q3 未答**——需真实多批任务的 `P4-evidence` 样本，不造样本、不回填。本任务顺手登记 **DEBT0043**（`_gate_p2_dispatch_plan` 同类 fail-open，只登记未修，
  状态 open）。**阶段 2（批级 gate，触及 `check-gate.py` 内核）不在本任务内**：前置 = ① Q1∧Q2 ≥90% 的试点数据 ② 提交粒度决策（用户裁决）——均未满足；
  阶段 3 更依赖阶段 2。故本条 `done` **不等于**「MVWU 协议落地完成」。
```

### 5.3 `[SUGGEST]` 是否另立 RM 承接阶段 2（不替用户决定）

`[SUGGEST: 建议另登记一条 RM-AG0067「MVWU 阶段 2：批级 gate（触内核）」，状态 backlog、关联任务留空，前置写明 ①Q1∧Q2≥90% 试点数据 ②提交粒度用户裁决 ③（触 check-gate.py，须走 SELF-GATE）。理由：本条标 done 后 roadmap 看板上不再有 MVWU 的未完成项，阶段 2 会从规划层"消失"，只靠详情节文字提示易被遗忘；先例 RM-AG0065 就是为 TAG0035 移出项另立的承接条目。反方理由：阶段 2 的前置（试点样本 + 用户裁决）都未到，现在立项是预占位，且 RM-AG0067 尚不存在，登记与否属用户决策——不登记也可，只须保留 §5.1/§5.2 的范围收窄标注。roadmap 已实测 RM-AG0066 为当前最大编号，若采纳建议取 RM-AG0067（落笔时以文件末条为准）。请主 Agent / 用户裁决，releaser 不替其决定。]`

## 6. 债务核对（`debt_check: reviewed`）

已读 `agate-workspace/debt/tech-debt.md`（DEBT0001-DEBT0043）；`python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` 本次实测 **rc=0**。
另用 `grep -ohE 'DEBT00[0-9]{2}'` 扫 P0 / P1 / P2 / P4 / P5 / P6 / P7 产出，命中 id：0014、0025、0039、0040、0041、0042、0043，逐个核对如下：

| id | 状态（tech-debt.md） | 与本任务关系 | 结论 |
|---|---|---|---|
| **DEBT0043** | **open**（priority low，`task_id: null`） | **本任务新登记**：`check-gate.py::_gate_p2_dispatch_plan` 三处 `return None` 静默放行（fail-open），与 TAG0035 子批 A 同类；零内核硬约束下只登记不修（BDD-5、P2 M12）。`grep DEBT0043` 命中 `## DEBT0043`（行 1488）。`created_at: 2026-09-19` | 保持 open，**不应关闭**（未修）；closure_criteria 三条均待后续任务 |
| DEBT0042 | closed | 已由基线提交 `dcfbc3e`/`28293d8` 修复并落 `closed`；仅作 P2 M12 抄样式来源与 P0 P0_STALE 引用，与本任务无改动交集 | 无需动作（注：其修复内容随 v0.72.0 发布，见 §3.3 [SUGGEST]） |
| DEBT0041 | open（归属 RM-AG0065） | 与本任务**同字段族**（`agate-md-field-set` 字段集 vs `check-p6-provenance.py` 必备 frontmatter 字段集不同源）。**本任务复发同类症状**：P6→P7 时 `P6-gate-diagnosis.md`（主 Agent 写的诊断文件）缺 `agent` 字段致 `check-p6-provenance.py` exit 2（`P6-exit2-resolution.md`；修复提交 `1daa651`）。虽文件与 DEBT0041 原述的 `P3-test-cases.md` 不同，但同属「必备 frontmatter 字段集散落多处、无权威表」 | 仍 open，不应关闭；**[SUGGEST] 在 DEBT0041 `evidence` 追加一条本任务复发证据**（`ref: agate-workspace/tasks/TAG0036-mvwu-pilot/P6-exit2-resolution.md`），交主 Agent 决定 |
| DEBT0040 | open（归属 RM-AG0065） | P0/P0-brief 引用其教训（`check-mvwu.py` 单测须 `tmp_path`，不写仓库内账本）；本任务单测遵循。**注意**：`git status --porcelain` 现有 `M …/gate-events.jsonl`，为本任务自身 gate 流水追加（`git diff --stat` 显示 +3 行，属正常 P7/P8 阶段事件），**非**单测污染（`test_check_mvwu.py` 用 `tmp_path`，P5 `P5_history_untouched` rc=0） | 保持 open，无动作 |
| DEBT0039 | closed | P2 M10 引用其边界（P7 卡第 6 项为「核对不 author」） | 无动作 |
| DEBT0025 | closed | P2/P1 提及「新增 CHECK 上线前先全量扫描存量」教训（M18 `GATE_SCRIPT_EXEMPT` 取舍留痕） | 无动作 |
| DEBT0014 | open（Windows Store python3 占位符） | `tests_filter` 示例写 `python -m pytest`、不裸 `python3` 的成文依据（BDD-8）；本任务未修它 | 保持 open，无动作 |

**"应关闭却未关闭"核对**：逐条对照本任务交付范围——本任务**未修复**任何已 open 的 DEBT（仅新增 DEBT0043）；DEBT0040/0041/0014 均在本任务范围之外，
closure_criteria 未被满足；未发现应关闭却未关闭的债务。`tech-debt.md` **本次发布无需再改**（DEBT0043 已由 P4 落笔）；仅 §6 DEBT0041 一条 [SUGGEST] 供主 Agent 取舍。

## 7. 临时资源清单（实际核实，不凭记忆）

所有命令均带 shell 层 `timeout`（或为瞬时只读命令）；以下为**本次实测**输出摘要。

| 核实项 | 命令 | 输出 / 结论 |
|---|---|---|
| 工作区 | `git status --porcelain` | ` M agate-workspace/tasks/TAG0036-mvwu-pilot/gate-events.jsonl`、`?? …/P8-dispatch-context-implementer.md`、`?? …/P8-progress.md`（后两者为本阶段过程文件；除任务目录外**无**产品面改动：`git diff --name-only HEAD -- . ':!agate-workspace/tasks'` 输出为空） |
| worktree | `git worktree list` | 仅 2 个：`/home/kity/oclab/agateon [main]`、`…/.worktrees/agate-TAG0036 [feat/TAG0036-mvwu-pilot]`——**无残留临时 worktree** |
| stash | `git stash list` | 输出为空——**无 stash** |
| 进程 | `ps aux \| grep -Ei 'pytest\|debug\|http.server\|daemon\|check-mvwu\|tmux\|uvicorn\|flask'` | 命中均为**与本任务无关的系统/用户既有进程**（dbus-daemon、polkitd、playwright 的 headless chrome〔自 9 月 10-11 日起〕、tmux〔自 9 月 7 日起〕）；**无 pytest / check-mvwu / http.server / 调试服务进程** |
| 监听端口 | `ss -ltn` | 127.0.0.1:2019/8642/8643/18789/19097/5432、0.0.0.0:13003/19096、10.255.255.254:53——均非本任务启动（本任务各阶段验证在 pytest `tmp_path` / `mktemp` 中完成、无服务进程） |
| 开发安装 | `python3 -m pip list --editable` | 输出为空——**无 editable / 开发安装**；本任务无全局包安装 |
| 任务目录残留 | `ls agate-workspace/tasks/TAG0036-mvwu-pilot/P4-evidence`、`ls agate-workspace/decisions` | 均 `没有那个文件或目录`——本任务**未造** `P4-evidence` 样本（P0 out-of-scope，P7 §6 已核）、未预建 `decisions/` |
| 缓存 | `git check-ignore -v agate/scripts/__pycache__ .pytest_cache` | 均被 `.gitignore` 第 14 / 18 行忽略，不入库；属 pytest 标准产物，非需清理的临时资源 |
| **临时目录（需主 Agent 清理）** | `find /tmp -maxdepth 1 -name 'tmp.*' -newermt '2026-09-19 00:00'` + `ls -laR`（`/tmp` 下共 73 个历史 `tmp.*` 目录，绝大多数为更早任务残留，与本任务无关） | 当日新建、内容与 MVWU 验证一致的 **2 个疑似本任务遗留**：**`/tmp/tmp.0aw8chJGM9`**（2026-09-19 15:47-15:49；含 `audit.py`〔`sys.addaudithook` 监控 `subprocess.Popen`/`os.system` 等，对应 BDD-19「check-mvwu.py 绝不执行 command」验证〕、`gen_v.py`、`g/` `g2/` `g3/`、`outside.log`、`H`）；**`/tmp/tmp.QckafhrI1m`**（2026-09-19 18:00；含 `task/`：独立 `.git` + `P2-design.md` + `P4-evidence/`，为 `--observe` 类合成临时 git 仓库）。两者均为 `mktemp` 产物、**不在仓库内**、无进程引用。**归属为依据内容与时间窗的推断（未在任务文档中登记 `mktemp` 路径），主 Agent 清理前请自行确认后 `rm -rf`。** 本 releaser **未删除**（超出「只产出 P8-release.md」的权限） |

**汇总**：本任务无常驻服务 / 进程 / 端口 / 开发安装 / 仓库内临时数据。唯一需 READY 收尾清理的是 `/tmp` 下上述 2 个疑似遗留的 `mktemp` 目录
（不影响仓库、不影响 gate）。`/tmp/claude-1000/…/scratchpad` 为本会话隔离目录，本 releaser 仅写入 `agate-workspace/tasks/TAG0036-mvwu-pilot/P8-progress.md` 与本文件，未写 scratchpad。

## 8. P5 验证复用确认（供主 Agent gate 参考）

- 本 releaser 执行 `timeout 60 python3 agate/scripts/check-p6-provenance.py --audit7-only agate-workspace/tasks/TAG0036-mvwu-pilot`，
  实测 **`AUDIT7_RESULT: reuse_blocked`（exit 1）**。原因（实测核实）：`git diff --name-only e1ac29e..HEAD -- . ':!agate-workspace/tasks'`（P5 通过点 `e1ac29e` 之后）
  含 **`CHANGELOG.md`**（P7 D1：109→111）与 **`agate-workspace/agents/CODE-MAP.md`**（P7 D2：补登记）两个非任务文件——均为 `9e9e369` 的文档修正，
  不影响代码，但按 audit7 判据视为 P5 后有非任务工作区文件改动。
- **结论：主 Agent 须完整重跑 `gate_commands.P5`（exit 0 + failed==0）**，不得复用 `P5-test-results/`。
- **时序（DEBT0013）**：`gate_commands.P5` 含 `P5_consistency`（内含 CHECK 7 badge ↔ tag）；README bump 后、tag 创建前重跑必报
  `badge v0.72.0 != tag v0.71.1`。请安排在 **commit + 创建 tag 之后** 重跑；此前可先在未 bump 状态下自查（P5 现状 1842 passed / 2 skipped，consistency 0 ERROR）。
- **本 releaser 自查（≠ P5 gate）**：`check-debt.py` rc=0；`bash agate/tests/scripts/count-tests.sh` 总计 1844 = 1668 + 111 + 65。**不声称 P5 已过。**

## 9. P7 偏差 D1-D4 在发布面的收尾核对

| P7 偏差 | 发布面核对结果 |
|---|---|
| D1 CHANGELOG 109→111 | **已收尾**：`CHANGELOG.md` 现为 111 / 65（`9e9e369`），无需再改 |
| D2 CODE-MAP 缺 check-mvwu | **已收尾**：`agents/CODE-MAP.md` 第 34 行已含「MVWU 观测族（新增 TAG0036）：check-mvwu.py …」 |
| D3 `HANDOFF-TAG0036.md` 在仓库根、P2 未声明 | **未收尾，属提交/PR 范围决策**（P7 不裁决）：该文件为基线后提交 `c93a02d` 引入的交接单（174 行），出现在 `git diff --name-only main...HEAD` 中，将随本分支进入 PR 并随 `v0.72.0` 发布。**[SUGGEST]** 主 Agent / 用户在 PR 前决定：随 PR 合入或移出。不影响 bump_type |
| D4 P3 红灯文件被 P4 小改的追溯缺口 | 仅追溯性说明（`P4-progress.md` 已记），发布面无动作 |

## Lessons Learned

> 主 Agent 汇入 `docs/notes/lessons.md`（文件不存在则创建，含表头：类别/教训/来源任务/日期）。

1. **【流程】release 前的 CHANGELOG 用例数须由 `count-tests.sh` / `pytest --collect-only` 实测回填，且随 P4 评审后修复同步**：TAG0036 的
   CHANGELOG 在 P4 写 109，P4 评审后修复新增 2 个参数化用例致实测 111，README 已同步而 CHANGELOG 漏改，直到 P7 才被查出（D1）。同类「登记面同步」
   （CHANGELOG / tests README / CODE-MAP）应纳入 P4 收口自检而非留给 P7。—— 来源 TAG0036，2026-09-19
2. **【流程】主 Agent 自己写的过程文件也须满足 frontmatter 字段契约（DEBT0041 同族复发）**：P6.5 阶段主 Agent 写的 `P6-gate-diagnosis.md` 缺 `agent`
   字段，致 `check-p6-provenance.py` exit 2，`agate-next` 暂停并额外产生 `P6-exit2-resolution.md`。根因仍是「必备 frontmatter 字段集散落多处、无权威表」
   （DEBT0041）；在该债务修复前，主 Agent 写任何 `P*-*.md` 一律用 `agate-md-field-set.py` 或对照标准 header，而非手写。—— 来源 TAG0036，2026-09-19
3. **【架构】"标 done"与"范围收窄"必须同步写入 roadmap**：本任务 roadmap 条目跨三阶段而 TAG0036 只做阶段 1，若只把状态改 `done`，看板上 MVWU 阶段 2
   会从规划层消失（RM-AG0043 硬校验只认 `done`）。沿用 TAG0035/RM-AG0062 先例——`done` 的同时在标题格与详情节写明「范围收窄 + 未完成前置」，并在 `[SUGGEST]`
   中提示另立承接条目（RM-AG0065 先例），由用户决定是否登记。—— 来源 TAG0036，2026-09-19
4. **【测试】新增 `agate/scripts/check-*.py` 会触发既有登记面测试（P2 评审 B1）**：`test_sg_6_check9_anchor_table_covers_all_gate_scripts` 对任何新增 `check-*.py`
   都要求登记；「不挂 gate 的观测脚本」需在 `GATE_SCRIPT_EXEMPT` 显式豁免并留 `[BASELINE_CHANGE]` 痕迹。以后新增观测类脚本，P2 应先 grep 该 glob 的消费方，
   避免 P5 才发现。—— 来源 TAG0036，2026-09-19

## 产出文件字段核对（供 gate 检查）

- `bump_type: minor`（`v0.71.1` → 建议 `v0.72.0`）
- `debt_check: reviewed`（正文 §6 列出 DEBT0043 / 0042 / 0041 / 0040 / 0039 / 0025 / 0014）
- 版本号变更确认：由主 Agent 依 §2.1 修改 README / README.zh-CN 两处 badge（version 文件面）
- CHANGELOG `[Unreleased]` → `## [0.72.0] - 2026-09-19`：由主 Agent 依 §3.2 采用（**无 `v` 前缀**，CHECK 13）
- UPGRADING 新章节：由主 Agent 依 §4 插入 `### v0.72.0`（无破坏性变更 / 零迁移动作）
- roadmap RM-AG0063 回写 `done` + 范围收窄标注：由主 Agent 依 §5.1 / §5.2 采用；§5.3 `[SUGGEST]` 交主 Agent / 用户裁决
- 临时资源清单：无常驻资源；`/tmp` 下 2 个疑似遗留 `mktemp` 目录待主 Agent 确认后清理（见 §7）
- `[PROD_NOT_TOUCHED]`
