---
phase: P8
task_id: TAG0042
type: release
parent: P7-consistency.md
trace_id: TAG0042-P8-20261006
status: draft
created: '2026-10-06'
agent: implementer
bump_type: minor
debt_check: reviewed
delivery: PR 普通 merge（--no-ff，禁止 squash）+ tag v0.79.0 + GitHub Release（release.yml 自动构建；先合 PR、后打 tag）
---

# P8-release.md — TAG0042 项目形态命令化 + 规则脚本化 发布准备声明

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` /
> `git tag`**——这些由主 Agent 在 P8 gate 验证通过后亲自执行。
> 本轮实际编辑三个发布面文件：`README.md`（version badge）/ `CHANGELOG.md`
> （`## [Unreleased]` 下新增 `## [0.79.0]` 段）/ `agate/UPGRADING.md`
> （`### v0.79.0` 节内追加批 3/5/6 小节）——均为 P8 发布准备产出，非"留给主 Agent"。
> 状态标记 `[PROD_NOT_TOUCHED]`。

## 1. 版本号变更确认

**bump_type: minor（v0.78.3 → v0.79.0，2026-10-06）**

依据：

1. **向后兼容的功能新增**：声明层 `agate-config`（+ `project-config.schema.json` + 唯一读取
   函数 `read_project_config`）/ 执行层 `agate-run` / CI 与诊断 `agate-ci-verify` + `agate-doctor` /
   义务登记表 `rules/obligations.yaml` + `check-obligations.py`——均为纯增量能力。
2. **迁移期无破坏性变更**：关卡层分级（`phases.yaml` 新增 `gate_layer`）+ P8 语义改述为
   「交付收尾」（新增 `delivery` 字段）——缺 `agate.config.yaml` 声明的存量项目 `gate_p0` 只
   输出 WARNING、仍返回通过码；P8 gate 仍执行既有发版检查。硬切截止版本为 **v0.80.0**。
3. **既有任务数据格式未变**：`.state.yaml` schema、`gate-events.jsonl` 事件结构、既有任务
   数据均无需迁移。
4. 当前发布版 **v0.78.3**（CHANGELOG 顶部 `## [0.78.3] - 2026-10-05` + README badge
   `version-v0.78.3` 已核）→ 目标 **v0.79.0**。
5. 本仓为单一版本号仓库（agateon 整体一次 bump）；`P2§packages` 的 7 个包
   （`agate-config` / `agate-run` / `agate-config-schema` / `gate-layer` / `agate-ci-verify` /
   `agate-doctor` / `obligations-registry`）为**任务改动分域**，不各自独立版本号。

| 位置 | 文件 | 变更 | 本轮状态 |
|---|---|---|---|
| README badge（EN） | `README.md` L12 | `version-v0.78.3` → `version-v0.79.0` | 已改 |
| CHANGELOG | `CHANGELOG.md` | `## [Unreleased]` 下新增 `## [0.79.0] - 2026-10-06` 段（含 6 批条目 + task_id `TAG0042`） | 已改 |
| UPGRADING §3 | `agate/UPGRADING.md` | `### v0.79.0` 节内追加批 3 / 批 5 / 批 6 小节（批 1 / 2 / 4 原已写） | 已改 |

> **README.zh-CN.md 的 badge 为 `version-v0.78.0`**（v0.78.1–v0.78.3 亦未同步，属既有状态），
> 不在本次派发范围（派发指引只列 `README.md`）；`check-protocol-consistency.py` 的 CHECK 7
> 只读 `README.md`，故不构成一致性缺口，**非本次引入的回归，本轮不动**。

## 2. CHANGELOG 更新确认

- 保留顶部 `## [Unreleased]`（空），其下新增 `## [0.79.0] - 2026-10-06`（与既有版本节格式
  一致——比照 v0.78.1/v0.78.2/v0.78.3 的插入位置）。
- 本版本条目**含 `TAG0042`**（`check-changelog.py` 关键词校验口径）。
- 条目覆盖全部 6 批：
  批 1 phase 语义统一 / 批 2 声明层 `agate-config` / 批 3 执行层 `agate-run` /
  批 4 关卡层分级 + P8 交付收尾 / 批 5 `agate-ci-verify` + `agate-doctor` /
  批 6 obligations 登记表；另含「### 变更」节说明迁移截止版本 v0.80.0。
- 自查：`grep -c "^## \[0.79.0\]" CHANGELOG.md` → **1**；
  `grep -c "TAG0042" CHANGELOG.md` → ≥ 1。
- `check-changelog.py TAG0042`（normal 模式）报「无 [Unreleased] 区域」——**发布后预期态**
  （条目已从 `[Unreleased]` 迁入 `## [0.79.0]` 版本节），该检查在 pre-commit 的 P8 分支
  **仅 WARNING 不拦截**；`CHECK_CHANGELOG_MODE=post-bump` 模式 → **rc=0**（版本节非空）。

## 3. UPGRADING 覆盖确认（全 6 批）

`### v0.79.0 — TAG0042 批 1：统一 phase 语义（**无破坏性变更**）` 节现覆盖全 6 批行为变更：

| 批 | 小节标题 | 本轮动作 |
|---|---|---|
| 批 1 | `⚠️ 会改变你项目的一处（编排惯例）`（`agate-next` 不预写） | 原已写，未动 |
| 批 2 | `**批 2（声明层，TAG0042）— 项目声明 agate.config.yaml…**` | 原已写，未动 |
| 批 4 | `**批 4（关卡层分级，TAG0042）— P8 交付收尾 + 发版逻辑迁移 preset…**` | 原已写，未动 |
| 批 3 | `**批 3（执行层，TAG0042）— 项目验证命令统一执行 agate-run…**` | **本次追加** |
| 批 5 | `**批 5（CI 与诊断，TAG0042）— agate-ci-verify 替换 backstop + agate-doctor…**` | **本次追加** |
| 批 6 | `**批 6（义务登记表，TAG0042）— 规则义务三态归宿登记…**` | **本次追加** |

- 追加小节位于批 4 小节之后、`### v0.78.3` 历史节之前；**未改已写段落、未改历史版本节**。
- 自查：`grep -n "### v0.79.0" agate/UPGRADING.md` → 命中（CHECK 13 CHANGELOG 最新版 ↔
  UPGRADING §3 章节对应所必需）。

## 4. roadmap 实测（无需回写）

- 实测反查「关联任务」列（第 6 列）：
  `awk -F'|' '/^\| RM-/{gsub(/^ +| +$/,"",$6); print $6}' agate-workspace/roadmap/roadmap.md | grep TAG0042`
  → **无匹配**。
- TAG0042 **不在任何 RM 条目的「关联任务」列**——roadmap 中 3 处 `TAG0042` 字样均落在
  **描述 / 来源列**（RM-AG0068 / RM-AG0093 / RM-AG0098 的长描述），非关联任务列。
- ⇒ 按 RM-AG0043（P8 gate 按 `task_id` 反查「关联任务」列）口径，**本任务无需 roadmap 回写**。

## 5. debt_check（reviewed）——条目 id 清单

**debt_check: reviewed**。已读取 `agate-workspace/debt/tech-debt.md`，本任务相关条目：

| DEBT id | 标题（摘） | status | 本轮动作 |
|---|---|---|---|
| DEBT0050 | `agate-next` 的「真暂停」（exit ∉ pass_set 且 ≠ 1）分支经真实 gate 不可达——BDD-8 改直驱落盘函数后失去端到端覆盖 | `open`（low） | **本任务相关、非本任务范围**：由 TAG0042 批 0 的 X7 改动间接暴露，登记 `task_id: TAG0042-config-and-enforcement`；本任务未闭合，留 `open` 不动（不阻断发布）。 |
| DEBT0045 / DEBT0046 | （`TAG0042-debt-batch` 直改批次登记的条目） | `closed` | 与本 P0-P8 任务目录无关，已完成闭合，本轮不动。 |
| 其余存量债务 | — | — | 与本任务无关，未涉及。 |

- 本次**无新增关注项**（P7 记录的「后续增强候选 / 待办」为不阻断的观察项，未登记为新债务）。
- 自查：`python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → 见主 Agent 运行。

## 6. 临时资源清单（releaser → 主 Agent 交接）

核对本任务 P0-P8 全程启动的临时服务 / 进程 / 数据 / 开发安装：

- **启动的临时服务 / 进程**：无。无 debug server / 无临时 daemon / 无占用端口。
- **临时数据库**：无。
- **临时数据 / 目录**：R6 全量差分（爆炸半径）在 **`/tmp` 副本**上跑（遵循 `AGENTS.md`
  「爆炸半径必须在工作区副本上跑」纪律），跑完核验真实仓库 `git status --porcelain` 为空；
  仓库内**无**临时目录 / 账本污染残留。
- **开发安装**：无。用系统 `python3`，未新装 editable install / 全局包 / `pip install`。
- **canonical 临时产物目录** `<项目根>/.agate-tmp/`：本任务**未创建**。
- **结论：本任务临时资源清单 = 无**，主 Agent 无需清理。
- **状态标记**：`[PROD_NOT_TOUCHED]`。

## 7. Lessons Learned

> 类别 / 教训 / 来源任务 / 日期 —— 供主 Agent 汇入 `docs/notes/lessons.md`。

- **流程 | 发版时 CHANGELOG 的 `[Unreleased]` 保留、版本节插入其下（不要 rename `[Unreleased]`）**：
  `pre-commit-gate.py` 在 `phase == P8` 时会跑 `check-changelog.py`，其 normal 模式要求
  `[Unreleased]` 区域存在且含 task_id。若把 `## [Unreleased]` 直接改名为版本号，`[Unreleased]`
  区域消失、该检查退化为「无 [Unreleased] 区域」（当前仅 WARNING 不拦截，但属噪音）。
  本仓既有惯例（v0.78.1–v0.78.3 的 git 历史）为**保留空 `[Unreleased]` + 在其下插入版本节**。
  来源 TAG0042 / 2026-10-06。
- **流程 | UPGRADING 版本节可跨批次「增量追加小节」，标题沿用首个子批次的措辞**：TAG0042 的
  `### v0.79.0` 节由批 1 首次创建，批 2/4 各自追加小节，本 P8 又补批 3/5/6。为避免重写历史
  段落，追加时只在本节内加粗体小节标题，不动既有小节与历史版本节——CHECK 13 只要求
  `### v{版本}` 存在，不校验节内小节完整性，故「全 6 批覆盖」需靠人工自检（本文件 §3）。
  来源 TAG0042 / 2026-10-06。
- **流程 | 单版本号仓库的 `P2 packages` 是改动分域而非独立包**：TAG0042 的 7 个 package
  对应 6 批改动面，发布时只 bump agateon 一个版本号（v0.79.0），不必为每个 package 单独
  找 version 文件。P8-release.md 须显式写明该事实，避免下游误判「漏 bump」。来源 TAG0042 / 2026-10-06。

## 8. 主 Agent 待办（P8 gate 通过后亲自执行，releaser 不做）

1. `check-gate.py P8 $TASK_DIR`（`bump_type` + `debt_check` 字段 + 暂存区 version/CHANGELOG
   变更 + roadmap 关联 RM 反查——本任务无关联 RM，见 §4）。
2. `bump-version`（本仓为直接编辑 badge/CHANGELOG，已由 releaser 完成）+ `git commit` +
   `git tag v0.79.0`（同一 commit）。
3. P5 验证：先 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`；
   `reuse_allowed` → 复用 `P5-test-results/`；否则完整重跑 `gate_commands.P5`。
4. `git log v0.78.3..HEAD --oneline` 对照 CHANGELOG 无遗漏。
5. READY 收尾检查（临时资源清单见 §6——无 debug server / 无临时 DB / 无临时数据 /
   无开发安装；无需清理）。
6. 本任务改动触及 `agate/UPGRADING.md` 等 SELF-GATE 触发面，commit message 须带
   `self-gate-review:` 留痕（独立评审）。

## 9. 交付收尾（delivery）

**delivery: PR 普通 merge（--no-ff，禁止 squash）+ tag v0.79.0 + GitHub Release**
（release.yml 自动构建；**先合 PR、后打 tag**）。

交付方式与后续人工步骤（P8 gate 通过后由主 Agent 亲自执行）：

1. **合 PR**：改动经分支 → PR，用**普通 merge（`--no-ff`）合并**，**禁止 squash**——
   squash 会生成内容相同但 SHA 不同的新提交，tag 与 main 分叉、`git describe --abbrev=0`
   回退旧版（v0.31.0 事故；见 `AGENTS.md` 发布清单）。
2. **打 tag**：PR 合并到 main 后，在 main 上打 `git tag v0.79.0` 并推送
   （`git push` 不带 tag 默认不推送 tag）→ `git ls-remote --tags origin v0.79.0` 验证远端到达。
3. **出 Release**：tag 推送触发 `.github/workflows/release.yml` 自动构建并创建 GitHub Release；
   `gh release view v0.79.0` 须存在，资产含本体 tarball + 两平台 offline 包 + `SHA256SUMS`。
4. **G-5 最终验证**：`git fetch origin && git describe --tags --abbrev=0 origin/main` == `v0.79.0`
   （**`--abbrev=0` 不可省**）；`git merge-base --is-ancestor v0.79.0 origin/main` 返回 0；
   合并后 push 的 CI 全绿。

> 顺序要点：**先合 PR、后打 tag**——`check-protocol-consistency.py` 的 CHECK 7（README badge ↔
> CHANGELOG 最新已发布版本）已 tag 无关，bump 后、tag 前重跑不报错；tag 指向校验由
> `release.yml` 的「Verify tag points to matching commit」步承担。

---

> 注：本文件不含 PASS/FAIL 预判——所有结果均为 releaser 本轮自检的客观运行输出，
> gate 判定由主 Agent 亲自执行。

## 10. P5 重跑证据（audit7=reuse_blocked ⇒ 完整重跑）

- 触发：check-p6-provenance.py --audit7-only → AUDIT7_RESULT: reuse_blocked
  （P8 bump 改动 README/CHANGELOG/UPGRADING 属非产出文件改动，故须重跑而非复用）
- 运行 HEAD：33e4598
- 命令与结果（逐条独立跑）：
  - python3 -m pytest agate/tests/ -q --tb=no → exit 1；2668 passed / 1 failed / 2 skipped（214.75s）
    唯一失败 = 预存失败 test_bdd_43（opencode CLI 漂移，见 known-failures.md；非本任务回归）
  - check-protocol-consistency.py --strict-errors-only → exit 0（0 ERROR / 408 WARNING 冻结面）
  - check-structure-consistency.py → exit 0（S0-S6 OK）
  - ruff check agate/ → exit 0（All checks passed）
  - check-platform-assumptions.py → exit 0（0 命中）
- 结论：除已登记预存失败外全绿；本任务新增回归 = 0
