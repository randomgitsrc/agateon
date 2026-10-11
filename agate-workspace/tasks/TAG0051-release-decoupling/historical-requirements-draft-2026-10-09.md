---
phase: P1
task_id: TAG0051
type: problems
parent: P0-brief.md
trace_id: TAG0051-P1-20261009
status: draft
created: 2026-10-09
agent: analyst
# ── v2.0 机器字段 ──
risk_level: high
ceremony: full
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-cards, agate-scripts, agate-rules, agate-protocol, agate-task-data, agate-tests, ci-workflows, docs-release]
domains: [backend, cli, security]
implicit_coupling: true
---

# P1 需求基线 — 任务与发布解耦（P8 不再落 tag；Release 独立流程 + 发布门）

> **来源**：`P0-brief.md`（主 Agent 任务简报）+ roadmap `RM-AG0103`（直接需求来源）。
> **范围**：只改 agateon 本仓；legacy 行为不变的验证用 R6 双向差分（`docs/design-notes/r6-differential.sh`），
> **只在 `/tmp` 副本上跑**，跑完核验真实仓库 `git status --porcelain` 为空。
> **本文件是活基线**：后续阶段新发现的隐含需求以 `[SCOPE+ from Pn]` 回写。
> **不重复已落地部分**：v0.80.2（PR #415）的 `agate-ci-verify --base` 必填 + `gate-backstop` PR 双口径 +
> `gate-backstop` 升 required 检查**已落地**，不在本需求范围。

---

## 0. P0-brief 时效性质疑

**已核对 P0-brief 时效性，无漂移。** 逐条排查严重 3 条判据（P0 卡「P0-brief 时效性自检」）：

1. **`task` 目标方案是否仍成立**：实测 `.github/workflows/release.yml` 的触发器仍为 `on: push: tags: ['v*']`、
   **无 `workflow_dispatch`**（`grep workflow_dispatch .github/` 仅命中 `deploy-pages.yml`）；P8→READY 推进条件
   仍含「git tag 已创建」（`agate/state-machine.md`、`agate/phase-cards/P8-release.md`、
   `agate/rules/state-transitions.md` 三处）；`check-gate.py::gate_p8` 仍有 tag 存在性检查（L2316-2328）。
   **目标方案未失效**。
2. **`executor_env` 平台前提是否仍成立**：P0-brief 声明 `platform: opencode` / `has_task_tool: true` /
   `has_local_runtime: true` / `network: available`——本会话实际运行于 opencode，有本地运行时与网络，
   **与声明一致**。
3. **`known_risks` 的「已解决前提」是否实际未解决或已被他任务解决**：6 条 risk 逐条实测——
   ① 跨 5 子系统反向传播面大 → 仍成立（本任务改动面实测覆盖 phase-cards / state-machine / AGENTS /
   workflows / scripts）；② `delivery` 取值域定死是否破坏性 → 仍是待判定项（见 §3 BDD-13/14 与 §2）；
   ③ legacy 行为不变须证 → 仍成立（R6 差分为验收锚）；④ `release.yml` 加「tag 所指提交 CI success」门
   与 main CI 竞态 → 仍成立（release.yml 现无该门）；⑤ 人工门落点与 PAUSED/NEEDS_CONFIRM 关系 → 仍成立；
   ⑥ P8 卡移除 tag 条件后 `check-gate.py P8` 须同步 → 仍成立（当前两者一致地都含 tag）。**无一条被他任务解决**。
4. **`env_constraints.debug_env`**：仍为空（本任务无调试服务依赖）→ 无漂移。

**结论**：不命中任何严重漂移；无轻微漂移。P0-brief 前提全部成立，继续 P1。

---

## 1. 需求复述

把**不可逆的对外发布动作**（tag → GitHub Release）从任务 P8 中移出，使「任务完成」与「对外发布」两件事
解耦。分三块：

1. **任务终态 = READY（不落 tag、不建 Release、不 bump 版本）**：任务 P8 收尾的产出 =
   交付物 + `CHANGELOG [Unreleased]` 段写入本任务条目 + 声明 `bump_type` **意图**（major/minor/patch）
   + 交付收尾（债务/临时资源/环境清理/干净 clone 一致性）+ **CI 全绿（含 push-to-main 口径）**。
   **不再要求 git tag 已创建，不再要求 version 文件 bump，不再要求 CHANGELOG 切版本节。**
2. **Release = 独立流程（需要时才跑）**：入口 `workflow_dispatch`（人工授权一次）；
   发布门 = 目标提交 CI success + tag↔提交一致（badge/CHANGELOG 节）+ CHECK 7/13 + roadmap 关联 RM done；
   动作序列 = 聚合 `[Unreleased]` → 定版本号 → 切版本节 + badge + UPGRADING → PR → merge →
   **等 main CI 绿** → tag → Release → G-5；失败处置 = 先评估回退 tag/Release 重打，
   仅当已被外部消费才出补丁。
3. **配套**：`P8-release.md` 卡移除 tag 条件且 `check-gate.py P8` 的 tag 检查同步移除；
   `delivery` 取值域定死；`state-machine.md` 显式发布授权转移；`AGENTS.md` 统一 tag 时点
   （消除现「第 4 步先 push tag」/「第 6 步才验合并后 CI 全绿」/「release PR 必须普通 merge：先合 PR、后打 tag」**三处自相矛盾**）。

**现状问题（实测）**：`release.yml` 以 tag push 为**唯一触发器** ⇒ 推 tag 即发 Release，tag 与 Release 不可分；
P8 的 READY 条件含 tag ⇒ 任务被迫在「合并后 main CI 绿」之前打 tag（TAG0050 P8 事故：2026-10-08/09
发布了 CI 红的提交，被迫补 v0.80.1）。

**这不是 bug 修复而是发布语义重构**：任务交付边界（READY）与对外发布边界（Release）需要显式分离，
发布需一次人工授权 + 一道机械发布门。

---

## 2. 隐含需求识别

> 逐维度过（数据 / 前端 / 多端 / 边界 / 兼容 / 安全），每条说明「为什么必须」。

1. **数据（legacy 任务不受影响）**：全仓 44 个任务目录中，仅 TAG0051 有账本 `task_created` 事件
   （唯一非 legacy）；其余 43 个均为 legacy（`agate_common.task_level` 返回 None → 走旧逻辑）。
   ⇒ 任何「非 legacy 才生效」的结构化收紧（如 `delivery` 取值域枚举）**默认不影响 43 个 legacy 任务**；
   但 P8 卡的 tag 条件 / `check-gate.py P8` 的 tag 检查是**对所有任务生效的正文/gate 逻辑**，
   移除它必须用 R6 双向差分证明 legacy 的 (rc, ERROR 集合) 不变。**为什么必须**：发布语义变更若
   动到 legacy 的 gate 判定，会让历史任务重跑时行为漂移。
2. **多端（CI / workflow / CLI / API 同步）**：
   - `.github/workflows/release.yml`（加 `workflow_dispatch` + 发布门）；
   - `agate/scripts/check-gate.py`（P8 tag 检查移除）；
   - `agate/scripts/agate-release.py`（Release 构建 CLI，可能承载发布门子命令）；
   - `agate/rules/phases.yaml`（P8 gates 措辞含 tag）；
   - `AGENTS.md` 版本发布清单（tag 时点统一）。
   **为什么必须**：tag 条件散落在协议卡 / 状态机 / 规则表 / gate 脚本 / CI 工作流五处，只改一处会
   造成「卡片说不用 tag、gate 仍要 tag」的不一致（P0-brief known_risks 第 6 条，A1/A2）。
3. **边界（回退 / 重打 / 授权）**：发布失败（tag 打错位置、Release 构建失败、CI 红的提交被发布）时
   的处置路径；tag 已推但 main CI 仍在跑时的等待或前置顺序（known_risks 第 4 条）；
   人工授权门与既有 PAUSED / NEEDS_CONFIRM 语义的关系（known_risks 第 5 条，避免两套确认语义）。
   **为什么必须**：发布是不可逆对外动作，边界路径无定义会导致「出问题时靠临场判断」。
4. **兼容（破坏性变更判定）**：`delivery` 取值域定死属**收紧**。按 `level-1.yaml` 冻结规则（§2.1 规则 3：
   「新增或收紧要求时登记新一级」），收紧须登记新一级快照（level-2.yaml，extends: 1），避免在途任务被追溯。
   **判定**：对 legacy 任务**非破坏性**（走子串路径，不读契约）；对非 legacy 任务，当前仅 TAG0051 自身
   受影响（其 P8 产出将按新枚举声明）⇒ **对既有任务整体非破坏性**，但需在 UPGRADING 记录该收紧。
   **为什么必须**：契约快照冻结是硬约束，直接改 level-1.yaml 会触发 consistency 冻结校验 ERROR。
5. **安全（不可逆对外动作 + 授权）**：发布（tag → Release）一旦执行对外可见且难撤回；「人工授权一次」
   的落点须显式（不能靠 agent 自判）；发布门须机械可查（不能靠人记得）。
   **为什么必须**：发布授权是安全门，须与既有 PAUSED/NEEDS_CONFIRM 区分且可审计。
6. **前端 / 数据迁移**：无（本任务无用户可见页面、无 schema/数据迁移）→ 不需要 frontend 域、无 UX BDD、
   无人工体验路径验收。

---

## 3. BDD 验收条件

> 编号全局连续；每条单一 Given/When/Then，可二值判定（PASS/FAIL）。
> 判定对象以「可观察行为」为准（gate 退出码 / 脚本输出 / 文件检索命中），不绑定内部实现细节。

### 功能组 1：任务终态 = READY（不落 tag / 不建 Release / 不 bump 版本）

#### BDD-1: P8→READY 推进条件不再要求 git tag
- Given 协议中描述 P8→READY 推进条件的三处（`agate/state-machine.md`、`agate/phase-cards/P8-release.md`、`agate/rules/state-transitions.md`）
- When 检索各处的 READY 推进条件 / READY 收尾检查项
- Then 三处均不以「git tag 已创建」作为 READY 的推进条件（「tag 已创建」在 READY 条件面零命中）

#### BDD-2: P8 gate 对缺失 tag 不再告警或拦截
- Given 一个非 legacy 任务的 `P8-release.md` 已声明 `bump_type`/`delivery`/`debt_check`，CHANGELOG 有变更，且本地无对应版本 tag
- When 运行 `check-gate.py P8 <task_dir>`
- Then stderr 不含「tag … 不存在」告警，且退出码为 P8 通过码 2

#### BDD-3: P8 gate 不再要求 version 文件变更
- Given 一个非 legacy 任务的 P8 产出（未修改任何 version 文件、CHANGELOG 仅 `[Unreleased]` 段有条目）
- When 运行 `check-gate.py P8 <task_dir>`
- Then stderr 不含「无 version 文件变更」类告警，且退出码为 2

#### BDD-4: CHANGELOG `[Unreleased]` 含本任务条目时通过
- Given CHANGELOG 的 `[Unreleased]` 段含 task_id
- When 运行 `check-changelog.py <task_id>`
- Then exit 0

#### BDD-5: CHANGELOG `[Unreleased]` 不含本任务条目时拦截
- Given CHANGELOG 的 `[Unreleased]` 段不含 task_id
- When 运行 `check-changelog.py <task_id>`
- Then exit 1

#### BDD-6: P8 产出声明 bump_type 意图
- Given `P8-release.md` 含 `bump_type: {major|minor|patch}`
- When 运行 `check-gate.py P8 <task_dir>`
- Then 退出码为 2；且 Given `P8-release.md` 缺 `bump_type` 时 Then 退出码为 1

### 功能组 2：Release = 独立流程

#### BDD-7: release.yml 提供 workflow_dispatch 人工授权入口
- Given `.github/workflows/release.yml`
- When 解析其 `on:` 触发器
- Then 含 `workflow_dispatch`（人工授权一次）

#### BDD-8: 发布门机械校验「tag 所指提交 CI success」
- Given 一个 tag，其指向提交的 CI 结论非 success
- When 运行发布门
- Then 判失败（非 0，提示指向该提交 CI 非 success）；且 Given 该提交 CI 为 success 时 Then 通过

#### BDD-9: 发布门校验 tag↔提交一致（badge / CHANGELOG 版本节）
- Given 一个 tag，其指向提交的 README badge 版本 ≠ tag 版本（或该提交 CHANGELOG 无对应版本节 / 版本节正文为空）
- When 运行发布门
- Then 判失败（非 0）

#### BDD-10: 发布门校验 CHECK 7 与 CHECK 13
- Given 待发布提交
- When 运行发布门
- Then CHECK 7（badge↔CHANGELOG 最新已发布版本）与 CHECK 13（CHANGELOG 最新版本↔UPGRADING §3 章节）均 0 ERROR；任一 ERROR 则门判失败

#### BDD-11: 发布门校验 roadmap 关联 RM 条目已 done
- Given 待发布任务在 `agate-workspace/roadmap/roadmap.md` 有关联 RM 条目，且其状态非 `done`
- When 运行发布门
- Then 判失败（非 0，提示须先回写 done）

#### BDD-12: Release 动作序列明确「先合 PR → 等 main CI 绿 → tag → Release」
- Given `AGENTS.md` 版本发布清单
- When 检查 tag 时点与 PR/CI 的先后关系
- Then 清单显式规定「release PR 合并 → 合并后 main CI 全绿 → 打 tag → Release」且全文无与之矛盾的 tag 时点表述

### 功能组 3：配套改动

#### BDD-13: `delivery.method` 取值域定死（有限枚举）
- Given 一个非 legacy 任务的 `P8-release.md` 的 `delivery.method` 取契约声明的合法枚举值
- When 运行 `check-gate.py P8 <task_dir>`
- Then 退出码为 2；且 Given `delivery.method` 取枚举外的任意值（非空字符串）时 Then 退出码为 1

#### BDD-14: `delivery` 取值域收紧不影响 legacy 任务
- Given 一个 legacy 任务的 `P8-release.md` 使用自由文本 `delivery:`
- When 运行 `check-gate.py P8 <task_dir>`
- Then 仍走子串判定（不因枚举收紧被拦截），退出码与改动前一致

#### BDD-15: `state-machine.md` 显式发布授权转移
- Given `agate/state-machine.md`
- When 检查 READY 及发布相关的状态/授权描述
- Then 显式声明「发布（tag → Release）由独立流程 + 人工授权（`workflow_dispatch` 一次）触发」，且与既有 PAUSED / NEEDS_CONFIRM 语义不重复（不引入第二套阻塞确认语义）

#### BDD-16: `AGENTS.md` tag 时点全文统一
- Given `AGENTS.md` 版本发布清单与「release PR 必须普通 merge」条
- When 检索全文 tag 时点表述
- Then 各处一致为「先合 PR、合并后 main CI 绿、后打 tag」，不再出现「先 push tag」与「先合 PR 后 tag」并存的矛盾

### 功能组 4：兼容性与机制约束

#### BDD-17: legacy 任务行为不变（R6 双向差分）
- Given 全部 legacy 任务与改动前协议（`before`）、改动后协议（`after`）
- When 在 `/tmp` 副本上运行 `bash docs/design-notes/r6-differential.sh`（`--before <merge-base>`、`--after <新协议 agate/>`）
- Then 输出「未匹配 0 条」且 exit 0（差异须全部被 `r6-allowlist.yaml` 覆盖）；运行前后真实仓库 `git status --porcelain` 为空

#### BDD-18: 改动 `agate/` 协议本体的提交含独立评审留痕
- Given 本任务每个改动 `agate/` 协议本体/脚本的提交
- When commit（commit-msg hook 检查）
- Then commit message 含 `self-gate-review:` 且其后路径真实存在（磁盘或 index）

#### BDD-19: 新增 `check-*.py` 时登记面通过（SG.6）
- Given 实现若新增/改名 `agate/scripts/` 下的 `check-*.py`
- When 运行 `python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py`（SG.6）
- Then 该脚本已登记（进 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表或 `GATE_SCRIPT_EXEMPT` 豁免集），SG.6 通过

---

## 4. 同类扫描结论

> 对问题涉及的关键符号全仓 grep，记录命中数量 + 文件清单，逐条判「本次处理 / 不处理 + 理由」。

### 4.1 `git tag 已创建`（P8→READY 推进条件）
命中 3 处（协议面）+ 1 处叙述（债务登记）：
- `agate/state-machine.md`（READY 收尾检查「git tag 已创建」+ P8 转移行含 `git tag`）→ **本次处理**（BDD-1）
- `agate/phase-cards/P8-release.md`（READY 收尾检查 + 推进条件两处「git tag 已创建」）→ **本次处理**（BDD-1）
- `agate/rules/state-transitions.md`（P8→READY「READY 收尾检查：… git tag 创建」）→ **本次处理**（BDD-1）
- `agate-workspace/debt/tech-debt.md`（叙述性引用，非推进条件）→ **本次不处理**（历史债务记录，非规则正文）

### 4.2 `git tag` / tag 检查（协议本体 + gate 脚本）
命中清单（协议面）：
- `agate/state-machine.md` L165（P8 转移条件含 `git tag -l "${VERSION_TAG_PREFIX}{version}" 存在`）→ **本次处理**（移除，BDD-1/2）
- `agate/phase-cards/P8-release.md` L37/L50（releaser 不执行 / 主 Agent 执行 `git tag`）→ **本次处理**（交付收尾不再含 tag）
- `agate/assets/execution-roles/implementer.md` L90（P8 模式禁止执行 git tag）→ **本次处理**（语义随 P8 去 tag 同步）
- `agate/scripts/check-gate.py` L2316-2328（tag 存在性 WARNING）→ **本次处理**（移除，BDD-2）
- `agate/rules/phases.yaml` L159（P8 gates 措辞含「tag 检查」）→ **本次处理**（措辞同步）
- `agate/dispatch-protocol.md` L881（P8→READY 条件含 `git tag`）→ **本次处理**（同步）
- `agate/git-integration.md` L188（引述「release PR 必须普通 merge」条，含 tag 时点）→ **本次处理**（与 AGENTS.md 统一后同步）
- `agate/WORKFLOW.md` L327（P8 行含 tag 检查描述）→ **本次处理**（同步）
- `AGENTS.md` L169/L174/L182（版本发布清单 tag 时点，三处）→ **本次处理**（BDD-16）
- `agate/UPGRADING.md` L138/L601（Release 完整性说明 / CHECK 7 历史）→ **本次不处理**（历史迁移章节，非现行规则）
- `agate/rules/obligations.yaml` OBL-P8 系列 → **本次处理**（若 tag 相关义务项存在则同步；`bump_type`/`delivery`/`debt_check` 义务保留）

### 4.3 `workflow_dispatch`
命中：`.github/workflows/deploy-pages.yml`（无关）；`release.yml` **无** → **本次处理**（BDD-7）。
（叙事/任务产出中的命中不计入规则面。）

### 4.4 `delivery`（P8 交付声明）
命中：`agate/phase-cards/P8-release.md`、`agate/rules/task-data/level-1.yaml`（delivery 契约：`required:[method]` / `none_requires_reason` / `non_none_requires_ref`）、
`agate/scripts/check-gate.py`（gate_p8 结构化判定）、`agate/UPGRADING.md`（v0.80.0 批 F 记录）、`agate/rules/obligations.yaml`（OBL-P8-02）。
→ **本次处理**（取值域定死，BDD-13/14）：`method` 现为任意非空字符串，须收紧为有限枚举；
按 `level-1.yaml` 冻结规则须**登记新一级快照**（level-2.yaml，extends: 1），不改已冻结的 level-1.yaml。

### 4.5 `VERSION_TAG_PREFIX`
命中：`agate/scripts/check-gate.py`（L2317/L2328）、`agate/state-machine.md`（L165）→ **本次处理**（随 tag 检查移除；若其他地方复用则保留）。

### 4.6 P8 版本 bump / CHANGELOG 切版本节
命中：`agate/phase-cards/P8-release.md`（bump-version + `[Unreleased]`→新版本号）、`agate/state-machine.md`（bump-version）、
`agate/rules/phases.yaml`（P8 gates 含 version/CHANGELOG 检查）、`agate/scripts/check-gate.py`（version 变更 WARNING + CHANGELOG 变更 WARNING）、
`agate/WORKFLOW.md`、`agate/dispatch-protocol.md`、`agate/rules/obligations.yaml`（OBL-P8-04/05）。
→ **本次处理**（BDD-3/4/5）：任务终态 READY 不 bump 版本、不切版本节；version 变更检查移除、CHANGELOG 检查改为「`[Unreleased]` 含 task_id」。

### 4.7 `protocol-tests.yml` 头部 required 注释（同类扫描附带发现）
实测分支保护 required checks = **6**（`gh api .../branches/main/protection`：shellcheck×2 / pytest×2 / consistency / gate-backstop）；
但 `protocol-tests.yml` 头部注释（2026-10-05，TAG0042 批0 m-3）称「required = 5，gate-backstop 已移出 required」——**已陈旧**
（v0.80.2 已将 `gate-backstop` 升回 required）。→ **本次处理**（本任务改 workflow，顺带同步该陈旧注释）。

### 4.8 结论
**本次处理的规则面清单 = {state-machine.md, phase-cards/P8-release.md, rules/state-transitions.md, rules/phases.yaml,
dispatch-protocol.md, WORKFLOW.md, git-integration.md, assets/execution-roles/implementer.md, scripts/check-gate.py,
rules/task-data（新增 level-2）, AGENTS.md, .github/workflows/release.yml, .github/workflows/protocol-tests.yml,
rules/obligations.yaml}**。**本次不处理** = {debt/tech-debt.md 叙述、UPGRADING.md 历史迁移章节、其他任务产出快照}。
**非「只此一处」**——tag 条件横跨 5 个子系统共 10+ 处，任一遗漏即产生卡片/gate 不一致（known_risks 第 6 条）。

### 4.9 新增/改名 `agate/scripts/` 文件的登记面**实测**（非推理）
本任务**可能**新增 `check-*.py`（发布门若落为独立脚本）。按 `agate/scripts/README.md`「新增脚本登记面」节，
在 `/tmp` 副本（`git clone` 本仓 task 分支）放入探针脚本实跑，**实测结果**：
- 放入 `agate/scripts/check-probe-surface.py` → `check-protocol-consistency.py` 报 **`CHECK9-coverage` WARNING**
  （consistency exit 0，415 WARNING 无 ERROR）；`test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts`
  **FAILED**（SG.6 红）——判据共用 `uncovered_gate_scripts()`。
- 放入 `agate/scripts/agate-probe-surface.py` → **零触发**（`agate-*.py` 不在门禁覆盖面内）。
- 实测后真实仓库 `git status --porcelain` 为空（探针只在 `/tmp` 副本）。
⇒ **结论**：若实现新增 `check-*.py`，须登记（进 `SCRIPT_ALIGNMENT_ANCHORS` 或 `GATE_SCRIPT_EXEMPT`）方使 SG.6 转绿（BDD-19）；
若落为 `agate-*.py` 或扩展现有 `agate-release.py`，无门禁触发。

---

## 5. 待确认清单

`[NO_NEED_CONFIRM]`

> 说明：目标切法、边界（回退/重打）、legacy 兼容判定均已在 `RM-AG0103` + `P0-brief` + 本文件明确；
> 无「真无方向」的业务决策点。`delivery` 取值域**具体枚举值**属设计细节（P2 定），不阻塞需求方向。

---

## 6. 裁剪说明

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]`——**全阶段，无裁剪**。

- 本任务跨 5 个子系统、改协议本体 + CI 工作流 + 发布语义，**risk_level: high**、**ceremony: full**。
- **P3 不裁**：发布门 / delivery 枚举 / P8 gate 行为变更须先有失败测试（TDD）。
- **P7 不裁**：跨文件一致性（卡片 / 状态机 / 规则表 / gate / workflow 五处 tag 条件的交叉核对）是本任务的核心风险，
  `ceremony: full` 亦要求 `phases` 含 P7。
- P2/P4/P5/P6 不可裁（核心阶段）。
- 无跳过阶段 ⇒ `pruned` 为空、`phases ∪ pruned == phase_universe`。

---

## 7. 能力需求声明

```yaml
capability_requirements: []
```

> 本任务为协议本体 + CI 工作流的机制重构，无浏览器 / 视觉 / 外部系统交互的**能力**需求。
> 发布门中「tag 所指提交 CI success」的查询在 **GitHub Actions 运行时**执行（CI 环境有网络）；
> 本地 P6 对该逻辑的验证用 fixture / mock（不依赖真实 GitHub）——属**验证方式**而非能力缺口，故不标三态。

**外部设置 / 人工授权步骤（登记，非 agent 能力缺口）**：
- `release.yml` 新增 `workflow_dispatch` 触发器——workflow 文件改动随 PR 合并即生效，无需额外人工设置。
- 若实现需**改动分支保护**（如把某新检查设为 required）——**须人工在 GitHub 仓库设置中授权**，
  登记为本任务 READY 后的人工步骤（不由 agent 自动执行）。当前未预见必须的分支保护改动；
  若 P2 判定需要，则在 P2 显式登记。
- 发布流程的**实际执行**（`workflow_dispatch` 触发一次）由人工在需要时发起，**不属于本任务的 P8 阶段**。

---

## 8. 兼容性与 SELF-GATE 声明

- **legacy 任务行为不变**：验收锚 = BDD-17（R6 双向差分，`/tmp` 副本，运行前后真实仓库干净）。
  判定依据：43 个 legacy 任务无 `task_created` 事件 → `delivery` 枚举收紧走子串路径不生效；
  P8 tag / version 检查的移除须经差分确认 (rc, ERROR 集合) 不变。
- **SELF-GATE**：本任务改 `agate/` 协议本体与脚本 ⇒ 触 SELF-GATE。**每批提交须独立评审 +
  提交信息写 `self-gate-review:`（其后路径真实存在）**——验收锚 = BDD-18。
- **契约级任务**：本任务为首个契约级任务（账本首行 `task_created`，`contract_level: 1`）——
  任务数据须走结构化写入工具（`agate-md-field-set` / `agate-state-set`），系统字段不得手写；
  每阶段提交后用 `agate-md-field-get` 抽查系统字段。
- **`delivery` 收紧落点**：按 `level-1.yaml` 冻结规则，收紧须登记新一级快照（level-2.yaml，extends: 1）；
  在 `UPGRADING.md` 记录该收紧（非破坏性，仅非 legacy 任务生效）。
