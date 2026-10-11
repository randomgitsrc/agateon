---
phase: P1
task_id: TAG0051
type: problems
parent: P0-brief.md
trace_id: TAG0051-P1-20261011
status: draft
created: '2026-10-11'
agent: analyst
risk_level: high
phases:
- P1
- P2
- P3
- P4
- P5
- P6
- P7
- P8
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
prod_touched: false
---
# P1 需求基线 — 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

> **来源**：`P0-brief.md`（主 Agent 任务简报）+ roadmap `RM-AG0103`（直接需求来源，状态 `scheduled`，关联任务 TAG0051）。
> **范围**：只改 agateon 本仓；**本阶段不实现任何东西**——只建立需求基线。
> **本轮是重启**（2026-10-09 立项停在 P0 → 2026-10-11 重建分支 `task/TAG0051-release-decoupling` @ origin/main，
> main 已推进 71 commit：v0.80.2 → **v0.81.0**）。`historical-requirements-draft-2026-10-09.md`（347 行 / 19 BDD）是
> **未评审草稿，为输入不是产出**——本文件**重新推导**，草稿中已被现状推翻的三处（tag 检查行号、协议版本、
> `agate.config.yaml` 是否存在）**逐条按本轮实测重写**，未整篇照抄。
> **本文件是活基线**：后续阶段新发现的隐含需求以 `[SCOPE+ from Pn]` 回写。
> **不重复已落地的部分**：v0.80.2（PR #415）的 `agate-ci-verify --base` 必填 + PR 双口径 + `gate-backstop` 升 required
> **已落地**，不在本需求范围；RM-AG0098（2026-10-05 落地）的 CHECK 7 去 tag 依赖 + `release.yml` 的
> 「Verify tag points to matching commit」步**也已落地**（见 §4 重叠判定）。

---

## 0. P0-brief 时效性质疑（独立复核）

> P0-brief 自带「P0-brief 时效性自检（2026-10-11）」节（判定：轻微漂移）。本节点**独立复核**，不默认其成立。

逐条排查 P0 卡「P0-brief 时效性自检（漂移判据）」的严重 3 条（**全部不命中**）：

| 判据 | 本轮实测 | 结论 |
|------|---------|------|
| 1. `task` 目标方案是否已变化 | `.github/workflows/release.yml` 仍 `on: push: tags: ['v*']`、**无 `workflow_dispatch`**（实测 :4-6，全 `.github/` 仅 `deploy-pages.yml` 有 `workflow_dispatch`）；`P8-release.md` 仍**两处**「git tag 已创建」（:122、:156）；`state-machine.md` :165 转移条件仍含 `git tag`、:177 READY 收尾仍含「git tag 已创建」；`state-transitions.md` :54 仍含「git tag 创建」 | 前提成立 |
| 2. `executor_env` 平台/运行时前提 | 实测 `agate-resolve.py` → `AGATE_ROOT=/home/kity/.agate/v0.81.0/agate`、`AGATE_VERSION=v0.81.0`、`AGATE_REASON=全局 current`；本仓无 `.agate-version` | 前提成立 |
| 3. `known_risks` 的「已解决前提」 | `RM-AG0098`（发布顺序边界）状态 `done`，但其**只**解决「CHECK 7 需 tag 与 CHECK 13 需 bump 挤在同一 required 单元」+「tag 指向无判据可察」两件事（见 §4），**未**解耦 tag/Release、**未**加 `workflow_dispatch`、**未**把发布独立化；本任务目标**未被其他任务实现** | 前提成立 |

**独立复核发现的轻微漂移（记录，不阻塞）**：

```
[P0_STALE: P0-brief 的 [P0_STALE] 清单引用「RM-AG0116 协议分支中立」，但本仓 roadmap 中不存在 RM-AG0116（最大为 RM-AG0115）——该 RM 归属无法反查]
> **主 Agent 处置（2026-10-11）**：复核属实。该编号只在 commit `717871a9`、`tech-debt.md`（DEBT0065 引用）
> 与 SELF-GATE 评审报告中被引用，**roadmap 从未登记**（属真实登记缺口）⇒ 已**补登记** RM-AG0116 入 roadmap
> （status `done`，关联 `hotfix-branch-neutral`），并已修正 P0-brief 该行的引用方式（改引提交号/机制名）。
> **本项现可反查，不再是漂移项。**
```

- 判定为**轻微**（不命中严重 1-3）：其**底层事实仍成立**——实测 `agate/scripts/agate-changes.py:25`、
  `agate-ci-verify.py:76` 确有 `default_branch()` 单源引用，`.githooks/pre-commit-local`（中立扩展点）存在；
  仅** RM 编号**不可反查。已据实记录，**已更新本文件 §0 与 §隐含需求 3（协调项）的指代**，不改任务前提。
- P0-brief 已有的 4 条轻微 `[P0_STALE]`（协议版本 v0.80.2→v0.81.0；`agate.config.yaml` 新落地并声明
  `release.preset: semver-changelog-tag`；分支中立机制落地；先例设计件三件存在）**本轮逐条复核均成立**，
  其中 `agate.config.yaml` 实测存在（`release.preset: semver-changelog-tag`，:16-17）。

**结论**：已核对 P0-brief 时效性，无严重漂移；1 条轻微漂移（RM-AG0116 编号不可反查）已记录，不阻塞。

---

## 1. 需求复述

把**不可逆的对外发布动作**（tag → GitHub Release）从任务 P8 中**结构性移出**，使「任务交付完成」与「对外发布」
成为两件可分别触发的事。三块：

1. **任务终态 = READY（不落 tag、不建 Release、不 bump 版本）**：任务 P8 收尾的产出 =
   交付物 + `CHANGELOG [Unreleased]` 段写本任务条目 + 声明 `bump_type` **意图**（major/minor/patch）
   + 交付收尾（债务/临时资源/环境清理）+ **CI 全绿（含 push-to-main 口径）**。
   **不再要求** version 文件 bump、CHANGELOG 切版本节、`git tag` 已创建。
2. **Release = 独立流程（需要时才跑）**：入口 `workflow_dispatch`（人工授权一次）；
   发布门 = 目标提交 CI success + tag↔提交一致（badge/CHANGELOG 版本节）+ CHECK 7/13 + roadmap 关联 RM done；
   动作序列 = 聚合 `[Unreleased]` → 定版本号 → 切版本节 + badge + UPGRADING → PR → merge →
   **等 main CI 绿** → tag → Release → G-5；失败处置 = 先评估**回退 tag/Release 重打**，仅当已被外部消费才出补丁。
3. **配套**：`P8-release.md` 卡移除 tag 条件且 `check-gate.py P8` 的 tag/version 检查同步移除；
   `delivery` 取值域定死（仅新声明生效）；`state-machine.md` 显式发布授权（复用既有确认语义）；
   `AGENTS.md` 统一 tag 时点（消除现「第 4 步先 push tag」/「第 6 步才验合并后 CI 全绿」/「release PR 必须普通
   merge」三处自相矛盾）；`agate.config.yaml` 的 `release.preset` 声明层消费点随 P8 去 tag/version 同步。

**现状问题（实测）**：`release.yml` 以 tag push 为**唯一触发器** ⇒ 推 tag 即发 Release，tag 与 Release 不可分；
P8→READY 条件含「git tag 已创建」（`state-machine.md` / `P8-release.md` / `state-transitions.md` 三处），
而 `check-gate.py::gate_p8` 的 tag 存在性检查已降级为 **WARNING 不阻断**（:2376-2389）⇒ **卡片/状态机与 gate
之间存在口径差**（卡片仍写死 tag，gate 已不阻断）。事故实证：TAG0050 P8（2026-10-08/09）tag 早于「合并后 main
CI 绿」，发布了 CI 红的提交，被迫补 v0.80.1。

**这不是 bug 修复而是发布语义重构**：任务交付边界（READY）与对外发布边界（Release）需要**显式分离**，
发布需一次人工授权 + 一道机械发布门。

---

## 2. 隐含需求识别

> 逐维度过（数据 / 前端 / 多端 / 边界 / 兼容 / 安全），每条说明「为什么必须」。**不掺方案设计**。

1. **数据（legacy 任务不受影响）**：全仓任务目录中，仅 TAG0051 有账本 `task_created` 事件（唯一非 legacy，
   `contract_level: 1`）；其余为 legacy（`agate_common.task_level` 返回 `None` → 走旧逻辑）。
   ⇒ 任何「非 legacy 才生效」的结构化收紧（如 `delivery` 取值域枚举）默认不影响 legacy；但 **P8 卡的 tag 条件 /
   `check-gate.py P8` 的 tag/version 检查是**对所有任务生效的正文/gate 逻辑**，移除它**必须**用 R6 双向差分证明
   legacy 的 `(rc, ERROR 集合)` 不变。**为什么必须**：发布语义变更若动到 legacy 的 gate 判定，会让历史任务
   重跑时行为漂移（`AGENTS.md` 工作流 0a 记录过对着真实仓库跑差异实验污染账本的事故）。
2. **多端（协议卡 / 状态机 / 规则表 / gate 脚本 / CI 工作流 / 发布清单 同步）**：tag 时点散落在
   `agate/phase-cards/P8-release.md`、`agate/state-machine.md`、`agate/rules/state-transitions.md`、
   `agate/rules/phases.yaml`、`agate/scripts/check-gate.py`、`agate/dispatch-protocol.md`、
   `agate/git-integration.md`、`AGENTS.md`、`.github/workflows/release.yml` **九处以上**。
   **为什么必须**：只改一处会造成「卡片说不用 tag、gate 仍要 tag」的不一致（P0-brief known_risks 第 2/6 条）。
3. **协调（与本轮相邻机制避免冲突/重复）**：`agate.config.yaml` 的 `release.preset: semver-changelog-tag`
   声明层（本仓 2026-10-11 填实）+ 分支中立机制（`default_branch()` 单源、`.githooks/pre-commit-local` 中立扩展点）
   ——本任务改 `AGENTS.md`/发布流程时须与它们协调，避免重复已落地项或产生相反口径。**为什么必须**：P0-brief
   已把二者列为相邻面（其引用的 RM-AG0116 编号不可反查，见 §0，但机制本身实测存在）。
4. **边界（回退 / 重打 / 授权 / 竞态）**：发布失败（tag 打错位置、Release 构建失败、CI 红的提交被发布）时的处置；
   tag 已推但 main CI 仍在跑时的**等待或前置顺序**（known_risks 第 4 条：`release.yml` 加「tag 所指提交 CI 必须
   success」门时 tag push 当下 main CI 可能仍在跑）；人工授权门与既有 `PAUSED` / NEED_CONFIRM 标记语义的关系
   （known_risks 第 5 条，避免两套确认语义）。**为什么必须**：发布是**不可逆对外动作**，边界路径无定义会导致
   「出问题时靠临场判断」。
5. **兼容（破坏性变更判定）**：`delivery.method` 取值域定死属**收紧**。按契约冻结规则（`level-1.yaml` 快照），
   收紧须登记新一级快照（`level-2.yaml`，`extends: 1`），**不改已冻结的 `level-1.yaml`**（否则触发 consistency
   冻结校验 ERROR）。**判定**：对 legacy 任务**非破坏性**（走子串路径，不读契约）；对非 legacy 任务，当前仅
   TAG0051 自身受影响。**为什么必须**：契约快照冻结是硬约束。
6. **安全（不可逆对外动作 + 授权）**：发布（tag → Release）一旦执行对外可见且难撤回；「人工授权一次」的落点须
   **显式**（不能靠 agent 自判）；发布门须**机械可查**（不能靠人记得）。**为什么必须**：发布授权是安全门，
   须与既有 `PAUSED`/NEED_CONFIRM 标记区分且可审计。
7. **前端 / 数据迁移 / 多模态**：无（本任务无用户可见页面、无 schema/数据迁移）⇒ `domains` 不含 frontend、
   无 UX 类别 BDD、无「人工体验路径」BDD（P1 卡「人工体验路径验收」条件不触发）。

---

## 3. BDD 验收条件

> 编号全局连续（`#### BDD-1:` … `#### BDD-23:`，无跳号、无字母后缀）；每条**恰一组** Given/When/Then，
> 可二值判定（PASS/FAIL）。判定对象以**可观察行为**为准（gate 退出码 / 脚本输出 / 文件检索命中 /
> 工作流触发器解析），不绑定内部实现细节。**正例与反例分别独立编号**（各自计分；反例不得内嵌在正例的
> `Then` 行内）。**条件式 BDD 的穷尽分支写在单条 `Then` 内**（如 BDD-23 覆盖三种互斥落点）——
> **始终可判、无中间态、无覆盖空洞**；P6 逐条记 PASS/FAIL。

### 功能组 1：任务终态 = READY（不落 tag / 不建 Release / 不 bump 版本）

#### BDD-1: P8/READY 语料面内 tag 条件零残留
- Given `agate/` 活面内描述 P8/READY 的语料（**六处**）：`agate/state-machine.md`、`agate/phase-cards/P8-release.md`、`agate/rules/state-transitions.md`、`agate/rules/phases.yaml`、`agate/dispatch-protocol.md`、`agate/assets/execution-roles/implementer.md`；**不含**（显式不处理项）`agate/UPGRADING.md` 历史迁移章节、`CHANGELOG.md` 发布产物、`agate-workspace/archived/**` 与 `docs/reviews/**` 快照，以及 `P8-release.md` 中描述**发布流程顺序 / CHECK 7 时序说明**的行（非 P8 条件面）
- When 检索上述六处语料中描述 **P8→READY 推进条件 / READY 收尾检查项 / P8 动作 / P8 gate 检查项**的行
- Then 「tag 作为 P8 条件或 P8 动作」的表述零命中（`git tag`、`tag 已创建`、`tag 检查`、`先 tag` 等字面均不存在——tag 语义已移出 READY/P8）

#### BDD-2: `check-gate.py P8` 对「无对应版本 tag」不再告警或拦截
- Given 一个非 legacy 任务的 P8 产出已声明 `bump_type`/`delivery`/`debt_check`，且本地无对应版本 tag
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then stderr 不含 tag 相关告警，且退出码为 P8 通过码 2

#### BDD-3: `check-gate.py P8` 不再要求 version 文件变更
- Given 一个非 legacy 任务的 P8 产出（未修改任何 version 文件）
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then stderr 不含 version 变更相关告警（刻意的口径收敛，非现状 WARNING），且退出码为 2

#### BDD-4: READY 前置保留「CHANGELOG `[Unreleased]` 含本任务条目」（回归锁）
- Given CHANGELOG 的 `[Unreleased]` 段含 task_id
- When 运行 `python3 agate/scripts/check-changelog.py <task_id>`
- Then exit 0

#### BDD-5: READY 前置对「CHANGELOG `[Unreleased]` 缺本任务条目」判失败（BDD-4 反例）
- Given CHANGELOG 的 `[Unreleased]` 段**不含** task_id
- When 运行 `python3 agate/scripts/check-changelog.py <task_id>`
- Then exit 1

#### BDD-6: P8 产出声明 `bump_type` 意图
- Given `P8-release.md` 含 `bump_type: {major|minor|patch}`
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then exit 2

#### BDD-7: P8 产出缺 `bump_type` 字段时判失败（BDD-6 反例）
- Given `P8-release.md` **缺** `bump_type` 字段
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then exit 1

### 功能组 2：Release = 独立流程（入口 + 发布门 + 动作序列 + 失败处置）

> **发布门判定载体（可判定性补强，非方案设计）**：BDD-9/10/11/13 的「发布门」= **创建 tag/Release 前的
> 一道可执行校验**；其**具体载体**（新增 `check-*.py` 或 `release.yml` 内新增步）**由 P2 定**，P6 按其
> 命令 exit code / 输出判定。P1 只要求该门**存在且机械可查**，不指定实现；BDD-12 自带替代载体
> `check-protocol-consistency.py`。
> **保护优先级（F-1）**：BDD-13（发布门校 roadmap RM `done`）与 `gate_p8` 既有 RM-AG0043 反查重叠；
> BDD-12（CHECK 7/13）与既有 CI required 重叠。**既有 CI required / `gate_p8` 是兜底（阶段/合并级，始终
> 生效）；发布门是创建 tag/Release 前的最终门，只叠加不放宽**——既有检查已红时发布门亦必判失败。

#### BDD-8: 发布流程提供 `workflow_dispatch` 人工授权入口
- Given 发布编排工作流 `.github/workflows/release.yml`
- When 解析其 `on:` 触发器
- Then 含 `workflow_dispatch`（人工授权一次，发布不再只能由 tag push 被动触发）

#### BDD-9: 发布门机械校验「目标提交 CI 结论为 success」
- Given 待发布的目标提交（合并后 main 上的提交）
- When 运行发布门
- Then 该提交 CI 结论非 success → 判失败（非 0，指出该提交 CI 非 success）；success → 通过

#### BDD-10: 发布门不把「PR 口径绿」当作「合并后绿」的等价替代（TAG0050 事故回归锁）
- Given 一个提交其 PR required checks 曾全绿、但合并后 push-to-main 口径的 CI run 失败
- When 运行发布门
- Then 判失败（不放过 push 口径失败——即「PR required 绿 ⇒ 合并后绿」须机械可查，而非默认成立）

#### BDD-11: 发布门校验「tag↔提交一致」（badge / CHANGELOG 版本节）
- Given 一个 tag，其指向提交的 README badge 版本 ≠ tag 版本，或该提交 CHANGELOG 无对应版本节 / 版本节正文为空
- When 运行发布门（tag 创建后）
- Then 判失败（非 0）
- 说明：该判据**已由 RM-AG0098 落地为 `release.yml`「Verify tag points to matching commit」步**（见 §4）；
  本 BDD **不要求重新实现**，只要求其在独立发布流程中**继续生效**。

#### BDD-12: 发布门校验 CHECK 7 与 CHECK 13 均 0 ERROR
- Given 待发布提交
- When 运行发布门（或 `python3 agate/scripts/check-protocol-consistency.py`）
- Then CHECK 7（README badge ↔ CHANGELOG 最新已发布版本）与 CHECK 13（CHANGELOG 最新版本 ↔ `UPGRADING.md` §3 章节）均 0 ERROR；任一 ERROR → 门判失败

#### BDD-13: 发布门校验 roadmap 关联 RM 条目已 done
- Given 待发布任务在 `agate-workspace/roadmap/roadmap.md` 有关联 RM 条目且其状态非 `done`
- When 运行发布门
- Then 判失败（非 0，提示须先回写 done）

#### BDD-14: tag 时点在发布文档中全文统一（无矛盾副本）
- Given `AGENTS.md` 版本发布清单 + 「release PR 必须普通 merge」条 + `agate/git-integration.md` 对应条
- When 检索全文 tag 时点表述
- Then 各处一致为「先合 release PR → 合并后 main CI 绿 → 后打 tag → Release」，不再出现「先 push tag」与
  「先合 PR 后 tag」并存的矛盾表述

#### BDD-15: 发布失败处置显式规定「先评估回退 tag/Release 重打」
- Given 发布流程文档（`AGENTS.md` 发布清单 / `release.yml` 注释 / 相关协议节）
- When 检索发布失败处置
- Then 显式规定「先评估回退 tag/Release 重打，仅当已被外部消费才出补丁」（顺序可二值判定）

### 功能组 3：配套改动（delivery 取值域 / 状态机授权 / config 声明层）

#### BDD-16: `delivery.method` 取值域定死为有限枚举（仅对新声明生效）
- Given 一个非 legacy 任务的 `P8-release.md` 的 `delivery.method` 取契约声明的合法枚举值
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then exit 2

#### BDD-17: `delivery.method` 取枚举外非空值时判失败（BDD-16 反例）
- Given 一个非 legacy 任务的 `P8-release.md` 的 `delivery.method` 取枚举外的任意非空字符串
- When 运行 `python3 agate/scripts/check-gate.py P8 <task_dir>`
- Then exit 1

#### BDD-18: `state-machine.md` 显式发布授权转移，且复用既有确认语义
- Given `agate/state-machine.md`
- When 检索发布（tag → Release）的触发/授权描述
- Then 显式声明「发布由独立流程 + 人工授权入口（当前实现为 `workflow_dispatch`）触发」，且**不引入**第二套与既有
  `PAUSED` / NEED_CONFIRM 标记并行的阻塞确认语义

#### BDD-19: `release.preset` 声明层消费点与去 tag/version 后的 P8 语义一致
- Given 本仓 `agate.config.yaml` 声明 `release.preset: semver-changelog-tag`
- When P8 移除 version/tag 检查后运行 `check-gate.py P8 <task_dir>`
- Then `check-gate.py` 中该声明层（迁移期 preset 提示/消费逻辑）与新 P8 语义一致——不再出现基于已移除的
  version/tag 痕迹触发的悬空提示，且 `check-protocol-consistency.py` 0 ERROR（无悬空引用）

### 功能组 4：兼容性与机制约束

#### BDD-20: legacy 任务行为不变（R6 双向差分）
- Given 全部 legacy 任务 + 改动前协议（`before`）与改动后协议（`after`）
- When 在 `/tmp` 副本上运行 `bash docs/design-notes/r6-differential.sh --corpus <副本> [--allow ...]`（差分 `(rc, ERROR 集合)`）
- Then 差异全部被 `r6-allowlist.yaml` 覆盖（未匹配 0 条），且运行前后**真实仓库** `git status --porcelain` 与开跑前一致

#### BDD-21: 改 P8 语义时 obligations / anchor / 测试三者同步
- Given `agate/rules/obligations.yaml` 的 OBL-P8-01..14（anchor 分别指向 `phases.yaml#P8.outputs`、
  `P8-release.md#产出规格`/`#gate 规则`/`#如果是首次进入本阶段`、`state-machine.md#READY 收尾检查`）
- When 改动 P8 语义后运行 `python3 agate/scripts/check-obligations.py` 与相关测试
- Then obligations 条目/anchor 无悬空（指向的节仍存在且语义一致），且挂靠 P8 的 enforcement/behavior 测试
  （`test_tag0050_obligations_enforcement.py` / `test_tag0050_obligation_behavior.py`）全绿

#### BDD-22: 改动 `agate/` 协议本体/脚本的提交含独立评审留痕
- Given 本任务每个改动 `agate/` 协议本体/脚本的提交
- When commit（commit-msg hook 检查）
- Then commit message 含 `self-gate-review:` 且其后路径真实存在（磁盘或 index）

#### BDD-23: 发布门三种落点（穷尽互斥）下 SG.6 与 CHECK9-coverage 判定正确
- Given 实现把发布门落为三种互斥落点之一：① 新增/改名 `agate/scripts/check-*.py`；② 落为 `agate/scripts/agate-*.py`（如扩展现有 `agate-release.py`）；③ `.github/workflows/release.yml` 内新增步（**不**新增 `agate/scripts/` 文件）
- When 运行 SG.6（`python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -q`）与 `python3 agate/scripts/check-protocol-consistency.py`（CHECK9-coverage）
- Then 按实际落点分别判定，三支穷尽、每支恒可判 PASS/FAIL——① 落 `check-*.py`：该脚本须已登记（进 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表或 `GATE_SCRIPT_EXEMPT` 豁免集）使 SG.6 通过（未登记则 SG.6 红，判 FAIL）；② 落 `agate-*.py`：SG.6 与 CHECK9-coverage 对该新文件**零触发**（SG.6 不红、无新增 WARNING、无 ERROR）判 PASS，反之 FAIL；③ 落 `release.yml` 内步：**无新增 `agate/scripts/` 文件**，SG.6 与 CHECK9-coverage 登记面无适用项、二者不产生**新增** WARNING / ERROR 判 PASS，反之 FAIL

---

## 4. 同类扫描结论

> 对问题涉及的关键符号全仓 grep/rg，记录命中数量 + 文件清单，逐条判「本次处理 / 本次不处理 + 理由」。
> **扫描面**：`agate/` + 仓库根 + `.github/` 的**活面**；`archived/`、`docs/reviews/`、`.worktrees/`、
> 历史任务产出（`agate-workspace/tasks/*/P8-*.md` 等）为 **frozen 快照**，不处理（见下）。

### 4.1 `git tag`（活面命中 —— 关键符号）

`grep -rn 'git tag'` 在排除 frozen 快照后，**活面命中集中在下列语料**（另有 `agate/tests/unit/test_check_protocol_consistency.py`
为 CHECK 7 既有测试、`CHANGELOG.md` 为发布产物）。逐条判定：

> **可追溯性（本轮修复 A 强制）**：下表**每行「本次处理」都标注其承接的 BDD 编号**——消除「§4.1 声明某文件由某 BDD
> 承接、但该 BDD 的判定面实际不含它」的不一致。

| 文件 | 命中 | 判定（承接 BDD） |
|------|------|------|
| `agate/phase-cards/P8-release.md` | :11/:12/:37/:50（releaser 不执行 tag + 主 Agent 统一执行 commit/tag）、**:122/:156 两处「git tag 已创建」** | **本次处理**（**BDD-1**：该卡全部 P8 条件/动作面纳入 BDD-1 判定面；移出 READY 条件/收尾） |
| `agate/state-machine.md` | :165（P8→READY 转移含 `git tag` + `git tag -l …`）、:167、**:177（READY 收尾「git tag 已创建」）** | **本次处理**（**BDD-1** 语料面；check-gate 侧 **BDD-2**） |
| `agate/rules/state-transitions.md` | :54（READY 收尾检查：… git tag 创建） | **本次处理**（**BDD-1**） |
| `agate/rules/phases.yaml` | :167（P8 gates 措辞「version/CHANGELOG/tag 检查」）、:169（「先 tag 后重跑（DEBT0013）」） | **本次处理**（**BDD-1** 语料面 tag 条件零残留；DEBT0013 已由 CHECK 7 去 tag 消解，见 §4.4） |
| `agate/rules/obligations.yaml` | OBL-P8-13（:815「releaser subagent 不执行 git commit / git tag」，anchor=P8-release.md#如果是首次进入本阶段） | **本次处理**（**BDD-21**：同步 statement/anchor；tag 自 P8 语料移除后措辞须更新） |
| `agate/scripts/check-gate.py` | :2376-2389（tag 存在性 WARNING + `VERSION_TAG_PREFIX`） | **本次处理**（**BDD-2**：移除 tag 检查） |
| `agate/scripts/check-protocol-consistency.py` | :493 CHECK 7（已 tag 无关）、:530-537（tag 缺失提示「先合 PR、推 tag 由 release workflow 校验 tag 指向」） | **本次处理（仅措辞，非逻辑）**（**BDD-12**：该文件的**门行为**由 BDD-12 承接——运行它须 CHECK 7/13 各 0 ERROR）。CHECK 7 逻辑**已 tag 无关**（RM-AG0098 落地），**不复改逻辑**；**措辞同步属条件性**（仅当发布入口/流程名变化时触发），触发时该提示句须与新独立发布流程口径一致，其可判定性由 **BDD-12 的门判定（该脚本 0 ERROR）间接覆盖** |
| `agate/scripts/agate-release.py` | 头注释/L2 提及 tag（构建 CLI） | **本次处理（视 P2）**（**BDD-9** 承接条件 = 发布门**若**落在此：该文件的发布门行为（目标提交 CI success 校验）由 BDD-9 承接；**若不落在此**：本行按「不改动」处理——其既有 tag 语义（按 tag 构建资产）**不变**，无协议变更、无需 BDD 承接。page 归属 `agate-scripts`） |
| `agate/git-integration.md` | :185-188（release PR 普通 merge + G-5 tag 时点） | **本次处理**（**BDD-14**：与 AGENTS.md 统一） |
| `agate/assets/execution-roles/implementer.md` | :101（「P8 模式禁止执行 git commit / git tag」） | **本次处理**（**BDD-1**：该角色文件纳入 BDD-1 语料面；语义随 P8 移除 tag 同步） |
| `agate/dispatch-protocol.md` | :881（P8→READY 行含「bump-version + commit + tag 由主 Agent 亲自执行」） | **本次处理**（**BDD-1**：该文件纳入 BDD-1 语料面，同步 P8→READY 条件） |
| `agate/UPGRADING.md` | 历史迁移章节（Release 完整性 / CHECK 7 历史） | **本次不处理**（历史迁移说明，非现行规则；**不承接 BDD**，BDD-1 已显式排除；新增版本节时另写） |
| `AGENTS.md` | :192（第 4 步 `git tag` + push）、:197（第 6 步合并后 G-5）、:205（「release PR 必须普通 merge」条） | **本次处理**（**BDD-14**：统一 tag 时点；page 归属 `agate-docs`） |
| `.github/workflows/release.yml` | 构建按 tag（`--branch "$TAG"`）；无 `git tag` 字面但发布入口即 tag | **本次处理**（**BDD-8**：加 `workflow_dispatch` 人工入口；发布门 BDD-9/10/12/13） |

### 4.2 `check-gate.py P8` 的 tag/version 检查（gate 与卡片口径差）

实测 `gate_p8`：**tag 存在性 = WARNING 不阻断**（:2376-2389，注释自陈「tag 通常在 gate 通过后才打」）；
**version 文件变更 = WARNING**（:2317-2337）；**CHANGELOG 变更 = WARNING**（:2339-2356）。
但 `P8-release.md`（:122/:156）、`state-machine.md`（:165/:177）、`state-transitions.md`（:54）仍写死 tag
⇒ **卡片/状态机与 gate 口径不一致**。**本次处理**（BDD-1/2/3：收敛为「READY 不含 tag、P8 不查 version/tag」）。

### 4.3 `workflow_dispatch`（发布入口）

实测：全 `.github/` 仅 `deploy-pages.yml` 有 `workflow_dispatch`；`release.yml` **无** ⇒ **本次处理**（BDD-8）。

### 4.4 `delivery`（P8 交付声明）

命中：`agate/phase-cards/P8-release.md#产出规格`、契约快照 `agate/rules/task-data/level-1.yaml`（`delivery` 契约：
`required:[method]` / `none_requires_reason` / `non_none_requires_ref`）、`check-gate.py::gate_p8`（:2255-2292 结构化判定）、
`agate/UPGRADING.md`（v0.80.0 批 F 记录）、`obligations.yaml#OBL-P8-02`。
⇒ **本次处理**（BDD-16）：`method` 现为任意非空字符串，须**收紧为有限枚举**；按 `level-1.yaml` 冻结规则须
**登记新一级快照**（`level-2.yaml`，`extends: 1`），不改已冻结的 `level-1.yaml`。

### 4.5 `VERSION_TAG_PREFIX`

命中：`agate/scripts/check-gate.py`（:2377/:2388）→ **本次处理**（随 tag 检查移除，BDD-2）。

### 4.6 P8 版本 bump / CHANGELOG 切版本节

命中：`agate/phase-cards/P8-release.md`（bump-version + `[Unreleased]`→新版本号）、`agate/state-machine.md`（bump-version）、
`agate/rules/phases.yaml`（P8 gates 含 version/CHANGELOG 检查）、`check-gate.py`（version/CHANGELOG 双路径 WARNING）、
`agate/dispatch-protocol.md`、`obligations.yaml`（OBL-P8-04/05）。
⇒ **本次处理**（BDD-3/4）：任务终态 READY 不 bump 版本、不切版本节；version 检查移除、
CHANGELOG 检查保留为「`[Unreleased]` 含 task_id」（`check-changelog.py` 已支持，回归锁见 BDD-4）。

### 4.7 `agate.config.yaml release.preset`（声明层）

命中：`agate.config.yaml`（:16-17 `release.preset: semver-changelog-tag`，2026-10-11 填实）、
`check-gate.py`（:2358-2374 迁移期分支：**未**采纳 config 的项目仍走 version/CHANGELOG/tag 检查并给提示）。
⇒ **本次处理**（BDD-19）：P8 去 tag/version 后，该声明层的迁移期消费逻辑（触发条件含 `cached_version`/`recent_version`）
须同步，否则「声明了 preset 却仍走已移除的 version/tag 检查」= 声明层悬空。

### 4.8 `protocol-tests.yml` 头注释（同类扫描附带发现 —— 复核草稿结论）

草稿 §4.7 称「头注释（2026-10-05）称 required=5，已陈旧」——**本轮实测推翻该结论**：
`protocol-tests.yml` 头注释 :22-24 **已有 2026-10-09 更正**：「gate-backstop 已重新加回 required（现 **6** 个）」。
⇒ **本次不处理**（该注释已是最新，非陈旧）。**这条是草稿「凭旧结论」的证伪**，据实修正。

### 4.9 结论

**本次处理的活面清单** = `{agate/phase-cards/P8-release.md, agate/state-machine.md, agate/rules/state-transitions.md,
agate/rules/phases.yaml, agate/rules/obligations.yaml, agate/scripts/check-gate.py, agate/scripts/check-protocol-consistency.py,
（视 P2）agate/scripts/agate-release.py, agate/git-integration.md, agate/assets/execution-roles/implementer.md,
agate/dispatch-protocol.md, agate/rules/task-data（新增 level-2）, agate.config.yaml, AGENTS.md, .github/workflows/release.yml}`。
**本次不处理** = `{agate/UPGRADING.md 历史迁移章节, agate-workspace/debt/tech-debt.md 叙述, roadmap RM 条目,
CHANGELOG 发布产物, agate/tests/unit/test_check_protocol_consistency.py（CHECK 7 不动）, 历史任务产出快照,
archived/ + docs/reviews/ 快照}`。
**非「只此一处」**——tag 条件横跨 5+ 子系统共 **15+ 处**，任一遗漏即产生卡片/gate/工作流不一致（known_risks 第 2/6 条）。
**包归属补全（本轮修复 E）**：根 `AGENTS.md` 与 `agate/git-integration.md`（**BDD-14** 的两个判定对象）归入 **`agate-docs`** package（frontmatter `packages` 已加），P7 据此跨文件交叉核不再漏面。

### 4.10 新增/改名 `agate/scripts/` 文件的登记面**实测**（非推理）

> P1 卡「同类扫描」/「机械门禁必须实测」：本任务**可能**新增 `check-*.py`（发布门若落为独立脚本）。
> 实测方法：`git clone --local` 本仓 task 分支到 `/tmp/opencode/tag0051-probe`，放入探针脚本实跑，**跑前跑后核验真实仓库
> `git status --porcelain` 一致**（本轮：开跑前/后均为「仅 2 个未跟踪的 P1 文件」）。

**实测结果（2026-10-11 本轮，重启后重新实测）**：
- 放入 `agate/scripts/check-probe-surface.py` → `check-protocol-consistency.py` **exit 0**（432→**433** WARNING，
  新增 `CHECK9-coverage` WARNING，无 ERROR）；`test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts`
  **FAILED**（SG.6 红，1 failed / 13 passed）。
- 放入 `agate/scripts/agate-probe-surface.py` → **零触发**（`check-protocol-consistency.py` 432 WARNING 无 ERROR；
  SG.6 **14 passed**）。
- 与 `agate/scripts/README.md`「新增脚本登记面」节一致：真门禁只有 ①`CHECK9-coverage` 与 ②`SG.6`，二者共用
  `uncovered_gate_scripts()`；③④⑤为约定/方向相反项。

⇒ **结论**：若实现新增 `check-*.py`，须登记（进 `SCRIPT_ALIGNMENT_ANCHORS` 或 `GATE_SCRIPT_EXEMPT`）方使 SG.6 转绿
（BDD-23）；若落为 `agate-*.py`（如扩展现有 `agate-release.py`），**无门禁触发**。**改动既有脚本**
（`check-gate.py` / `check-protocol-consistency.py`）不新增登记面动作，但须保持二者已在 `SCRIPT_ALIGNMENT_ANCHORS`。

### 4.11 写工具白名单缺口（本阶段实测发现，登记不处理/待评估）

写 P1 frontmatter 时实测：`agate-md-field-set.py` 的 key 白名单（`GENERIC_HEADER_KEYS ∪ phases.yaml 全部
task_fields`，见该脚本 :84-92）**不含** `ceremony` / `implicit_coupling` / `change_type` / `project_phase` /
`ui_render_shape` / `ui_ux_dimensions` / `need_confirm_resolved` 等字段——而 `agate-md-field-get.py`（:115-125）
与 `check-frontmatter.py`（:40-70 `SCHEMAS`）均把它们视为合法 P1 字段（frontmatter-only）。九处先例
（TAG0021/0022/0023/0024/0026/0028/0030/0032/0033/0034/0037 等的 `P1-requirements.md`）确有手写 `ceremony:`。
⇒ **本次处理**（限本任务）：按派发指引**不手写**，`ceremony` 取 fail-closed 默认 `standard`（功能等价，见 §7）。
⇒ **本次不处理（转评估）**：把 `ceremony` 等加进写工具白名单属**协议改动**，超出本任务单一主题——登记为
**待评估项**（若主 Agent 判定需要，可并入本任务配套或另立 hotfix/RM）。**不构成「只此一处」反模式**：缺口属
写工具面，与本任务的发布解耦主题不同簇。

> **主 Agent 处置（2026-10-11）**：已登记 **DEBT0067**（`agate-workspace/debt/tech-debt.md`，status: open，
> priority: medium）——并**扩大**了 analyst 报的面：除 `ceremony`/`implicit_coupling`/`change_type`/
> `project_phase`/`ui_render_shape` 外，**P8 的 `delivery`/`debt_check` 同样不在白名单**（而它们各有
> OBL-P8-02/03 行为测试）⇒ 缺口是「读侧认、写侧不认」的**口径分叉**，影响面跨 P1/P8。**不并入本任务**
> （主题不同簇），本任务按纪律不手写、档位取 fail-closed 默认。

---

## 5. 先例设计件重叠判定（RM-AG0098，dispatch-context「上游关联」强制项）

先例三件：`docs/design-notes/design-release-order-boundary.md`（14.5 KB）、
`docs/reviews/agate-design-review-2026-10-03-release-order.md`（39.9 KB）、
`docs/reviews/handoff/handoff-release-order-20261003.md`（9.7 KB），源自 **RM-AG0098「发布顺序被 CI 逼成唯一路径」（状态 `done`）**。
**须逐项判定「已由 RM-AG0098 解决 / 仍未解 / TAG0051 不重叠的部分」。**

**RM-AG0098 已解决（TAG0051 不重复）**：
- ① CHECK 7 改为**不依赖 tag**（badge ↔ CHANGELOG 最新已发布版本，与 CHECK 13 同源）——实测
  `check-protocol-consistency.py::check_version_badge`（:493）：tag 缺失只作提示、不判失败。
- ② `release.yml` 补「**Verify tag points to matching commit**」步（:33-65）：tag 名 == tag 所指提交 README badge +
  该提交 CHANGELOG 版本节非空 —— **tag 指向无判据可察**这一判据弱点已补。
- ③ 后续整改（v0.78.3）：§6 的 I-1/I-2/m-a/m-b 四项（原始行正则、5 处文档旧表述、tag 校验步实跑用例、pipefail 管道）。
⇒ TAG0051 **不重复**上述三条，BDD-11 只要求「该 tag↔提交一致校验在**独立发布流程**中继续生效」。

**RM-AG0098 未解决、TAG0051 承接（不重叠部分）**：
- **任务边界**：RM-AG0098 从未改 P8→READY 条件——任务仍**被迫**在「合并后 main CI 绿」之前打 tag
  （这正是 TAG0050 P8 事故的直接结构性成因）。TAG0051 的**核心不重叠点** = 把 tag 从 **P8/READY 条件**中移出
  （BDD-1/2/3），使「任务交付」与「对外发布」解耦。
- **入口独立化**：RM-AG0098 的方案（含外部评审第五方案）**保留 release.yml 以 tag push 为触发**；
  **未加 `workflow_dispatch`**。TAG0051 = 发布成为**独立、可人工授权一次触发**的流程（BDD-8）。
- **发布门前置「目标提交 CI success」**：RM-AG0098 的 tag↔提交一致校验发生在 **tag push 之后（release workflow 内）**，
  它**不阻止**「先打 tag 发 Release」；也**不校验**目标提交 CI 是否 success。TAG0051 = 在**创建 tag/Release 前**
  加一道机械发布门（BDD-9/10/12/13），其中 BDD-10 直接针对 TAG0050 事故根因（PR 口径 vs push 口径覆盖不同路径）。
- **RM-AG0098 §Q2「改本仓 AGENTS.md 补 tag 与 PR 的先后」**（handoff §5 建议 1）：**至今未落地**——实测
  `AGENTS.md` :192/:197/:205 三处 tag 时点仍自相矛盾。TAG0051 承接（BDD-14）。
- **配套面**（RM-AG0098 完全未涉及）：`delivery` 取值域收紧（BDD-16）、`state-machine.md` 显式发布授权（BDD-18）、
  `release.preset` 声明层同步（BDD-19）、obligations/anchor/测试同步（BDD-21）。

**边界声明**：TAG0051 **不重叠**于 RM-AG0098 的部分 = 「**任务终态解耦（READY 不含 tag）+ 发布流程独立化
（workflow_dispatch 人工授权）+ 发布门（创建 tag/Release 前的机械门）+ 配套字段/授权/声明层同步**」；
RM-AG0098 已覆盖的「CHECK 7 去 tag + tag 指向校验」TAG0051 **不再实现，只要求继续生效**。

---

## 6. 待确认清单

`[NO_NEED_CONFIRM]`

`[SUGGEST: `delivery.method` 枚举建议取值 `release-notes / tag-release / none / （项目自定义扩展）`，`none` 时 `reason` 必填；理由：与 `level-1.yaml` 既有 `none_requires_reason` 契约一致，属审计痕迹，主 Agent 可直接采纳。]`

> **说明**：目标切法（`RM-AG0103` 目标切法①②）、边界（回退/重打/竞态）、legacy 兼容判定均已在
> `RM-AG0103` + `P0-brief` + 本文件明确；**无「真无方向」的业务决策点**。dispatch-context「本阶段特有要求 1」
> 指出的 `delivery` 取值域**具体枚举值**属**技术取舍**（P2 定），不阻塞需求方向——已按「**legacy 不受影响**为硬约束、
> 取值域只对**新声明**生效」定稿（BDD-16/20），不标 NEED_CONFIRM 阻塞项。

---

## 7. 裁剪说明

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]`——**全阶段，无裁剪**（`pruned` 为空；`phases ∪ pruned == phase_universe`）。

- 本任务跨 5+ 子系统、改协议本体 + CI 工作流 + 发布语义 ⇒ `risk_level: high`（**已写入 frontmatter**）。
- **P3 不裁**：发布门 / `delivery` 枚举 / P8 gate 行为变更须先有失败测试（TDD）。
- **P7 不裁**：跨文件一致性（卡片 / 状态机 / 规则表 / gate / workflow / AGENTS 六处 tag 条件的交叉核对）是本任务
  核心风险。
- P2/P4/P5/P6 不可裁（核心阶段）。
- 无跳过阶段 ⇒ 无「跳过风险」需声明。
- ⚠️ **仪式档位声明受限（机制缺口，须主 Agent 知悉）**：本文件**未**声明 `ceremony`/`implicit_coupling`——
  实测 `agate-md-field-set.py` 的 key 白名单（`GENERIC_HEADER_KEYS ∪ phases.yaml 全部 task_fields`）
  **不含** `ceremony`/`implicit_coupling`（`set ceremony full` → `ERROR: 非法 key 'ceremony'`），
  而 `agate-md-field-get.py` 与 `check-frontmatter.py` 又把 `ceremony` 当作合法 P1 字段（frontmatter-only）。
  按派发指引「不要绕过 set 直接手改文件」⇒ **不手写**，档位 fail-closed 取默认 `standard`。**功能影响等价**：
  `risk_level: high` 已机械映射 `plan-eng-review`（P2）+ P4 域评审，`domains: security` 已映射 `cso`（P4），
  P7 已显式列入 `phases`（不可裁）——`ceremony: full` 在此任务上**不新增任何评审触发**（见
  `agate/rules/review-mapping.md` :23-24）。若主 Agent 要求字面 `ceremony: full`，须先扩写工具白名单（协议改动）。

---

## 8. 能力需求声明

```yaml
capability_requirements: []
```

> 本任务为协议本体 + CI 工作流的机制重构，无浏览器 / 视觉 / 外部系统交互的**能力**需求。
> 发布门中「目标提交 CI success」的查询在 **GitHub Actions 运行时**执行（CI 环境有网络）；**本地 P6 对该逻辑的
> 验证用 fixture / mock**（不依赖真实 GitHub）——属**验证方式**而非能力缺口，不标三态（判断树：换谁都需先把
> 外部服务接上才是环境问题；此处用 mock 即消解，非环境缺口）。

**外部设置 / 人工授权步骤（登记，非 agent 能力缺口）**：
- `release.yml` 新增 `workflow_dispatch`——workflow 文件改动随 PR 合并即生效，无需额外人工设置。
- 若实现需**改动分支保护**（如把某新检查设为 required，或调整 `strict`）——**须人工在 GitHub 仓库设置中授权**，
  登记为「需人工授权的一次性步骤」（**不由 agent 自动执行**）。当前**未预见**必须的分支保护改动；若 P2 判定需要，
  在 P2 显式登记。
- 发布流程的**实际执行**（`workflow_dispatch` 触发一次）由人工在需要时发起，**不属于本任务的 P8 阶段**。

---

## 9. 兼容性与 SELF-GATE 声明

- **legacy 任务行为不变**：验收锚 = BDD-20（R6 双向差分，`docs/design-notes/r6-differential.sh`，**只在 `/tmp` 副本上跑**，
  运行前后真实仓库 `git status --porcelain` 一致）。判定依据：legacy 任务无 `task_created` 事件 →
  `delivery` 枚举收紧走子串路径不生效（BDD-16）；P8 tag/version 检查的移除须经差分确认 `(rc, ERROR 集合)` 不变。
- **SELF-GATE**：本任务改 `agate/` 协议本体与脚本 ⇒ **触 SELF-GATE**。**每批提交须独立评审 + 提交信息写
  `self-gate-review:`（其后路径真实存在）**——验收锚 = BDD-22。
- **契约级任务**：本任务是首个契约级任务（账本首行 `task_created`，`contract_level: 1`）——任务数据须走结构化写入
  工具（`agate-md-field-set` / `agate-state-set`），系统字段不得手写；每阶段提交后用 `agate-md-field-get` 抽查系统字段。
- **`delivery` 收紧落点**：按契约冻结规则，收紧须登记新一级快照（`level-2.yaml`，`extends: 1`），
  并在 `UPGRADING.md` 记录该收紧（非破坏性，仅非 legacy 任务生效）。
- **不可逆外部动作保护**：push / PR / merge / tag / Release / 改分支保护**须用户授权**，需求中**不得**把
  它们写成 agent 自动执行的步骤；实现确需改分支保护时登记为「需人工授权的一次性步骤」（见 §8）。
- **环境隔离标记**：`[PROD_NOT_TOUCHED]`——本阶段（及全任务）不写生产环境、不改协议运行时；
  需实测的脚本（如 §4.10 登记面探针、R6 差分）**只在 `/tmp` 副本上跑**，跑前跑后核验真实仓库
  `git status --porcelain` 与开跑前一致。
