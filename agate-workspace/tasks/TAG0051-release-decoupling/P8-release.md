---
phase: P8
task_id: TAG0051
type: release
parent: P7-consistency.md
trace_id: TAG0051-P8-20261011
status: draft
created: '2026-10-11'
agent: implementer
bump_type: minor
debt_check: reviewed
delivery:
  method: release-notes
  ref:
  - CHANGELOG.md [Unreleased] 的 TAG0051 条目
  - agate/rules/task-data/level-2.yaml（已登记 LEVELS.yaml）
  reason: 本任务交付物 = 合并入 main 的协议改动（交付面见 §2），**不落 tag / 不建 Release**； 其对外呈现载体 = `CHANGELOG
    [Unreleased]` 条目，由独立发布流程稍后聚合生成发布说明 ⇒ 取 `release-notes`（非 `tag-release`：本任务不触发
    tag/Release；非 `none`：确有对外可发布的 协议改动）。
prod_touched: false
---

# P8-release.md — TAG0051 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` / `git push` /
> `git tag` / 建 Release**——这些由主 Agent 在 P8 gate 验证通过后处理（且本任务**无** tag/version 动作，
> 见 §1）。
> **本轮只改 3 个文件**：本文件（新建）、`CHANGELOG.md`（`[Unreleased]` 条目）、
> `agate-workspace/roadmap/roadmap.md`（RM-AG0103 回写）。**未改**任何代码/测试/协议文件、
> **未改** version 文件（README badge）、**未打 tag / 未建 Release**。
> 状态标记：`[PROD_NOT_TOUCHED]`（全程在 agateon 本 checkout 上工作，未接触生产环境）。
> **自查 ≠ gate**：本文件所有结果为 releaser 本轮自检的**客观运行输出**；gate 判定权在主 Agent。

## 0. 上游与基线

- **分支**：`task/TAG0051-release-decoupling`；**起点** `581369fc`（origin/main）。
- **提交链**：P4 `9771e76a` / P5 `c5bda4df` / P6 `03dcc1f7` / P6.5 `c810c19a` / P7 `da4ede21`。
- **上游结论**：P6 验收 `23/23 PASS`（`fail: 0`）；P6.5 judge `passed`（`criteria_total == criteria_passed == 23`）；
  P7 一致性 `blocker 0 / deviation_critical 0 / DESIGN_GAP 0-0 / CODE-MAP 4-4`。
- **本任务等级**：**首个非 legacy 任务**（账本首行 `task_created`，`contract_level: 1`）⇒ 走 `gate_p8`
  的**结构化 `delivery`** 分支（非 legacy 子串路径）。故本文件 `delivery` 必须为**结构化 dict**（见 §2）。
- **P2 `packages` 实测 = 9 项**：`agate-cards` / `agate-state-machine` / `agate-rules` / `agate-scripts` /
  `agate-roles` / `agate-dispatch` / `agate-config` / `agate-docs` / `ci-workflows`（与 P1 逐字一致）。
  本仓为**单一版本号仓库** ⇒ 9 个包是**改动分域**，**不各自独立 bump 版本号**（同 TAG0042/TAG0050 惯例）。

## 1. bump_type 论证（**意图声明**，非执行 bump）

**`bump_type: minor`**（意图；本任务**不**切版本号——发布由独立流程负责）。

正面处理难点——本任务对**新任务**是「**准入行为变化**」，对**既有任务/存量数据非破坏**：

1. **对新任务 = 准入行为变化（破**）：登记 `agate/rules/task-data/level-2.yaml` 后，协议**当前契约等级由 1 抬升为 2**
   （`LEVELS.yaml` 的最大已登记等级），而 `pre-commit-gate.py` 强制「新任务必须登记当前等级」
   ⇒ **此后所有非 legacy 新任务均须为等级 2**；`delivery.method` 随之由「任意非空」**收为三值枚举**
   （`release-notes` / `tag-release` / `none`），可能拦下原本合法的取值。另：P8 语义由「要求 version/tag」
   变为「止于 READY」。故**不是「无破坏性变更」**（与 `agate/UPGRADING.md`「未发布 — TAG0051」节口径一致）。
2. **对既有任务/存量数据 = 非破坏**：`gate_p8` 移除的三项（version 文件变更 / CHANGELOG 切版本节 /
   tag 存在性）**原本即为 WARNING 不阻断** ⇒ 移除后 legacy 任务的 `(退出码, ERROR 集合)` **不变**。
   R6 双向差分实测：legacy 39 个、差异 2 条（均 `[ALLOWED]`、`rc 2→2`）、**未匹配 0 条**（见 P5/P6.5 证据）。
   枚举收紧**只对「非 legacy 且等级 ≥ 2」生效**，legacy 走子串路径、level-1 任务无 `method_enum` ⇒ no-op。
3. **定 `minor` 而非 `major` 的依据（本仓 0.x 惯例）**：本项目处于 **0.x 阶段**，**破坏性/行为变更一律在
   `minor` 位**承载并以 **BREAKING** 醒目标注（先例：`v0.60.0` 结构化层「含破坏性变更」、`v0.73.0`
   版本目录布局「删除旧单软链布局」——**均 minor**；`v1.0.0` 之前未出现过 major）。同理 `TAG0037`
   P8 明确「按『破坏性变更 → major』字面应升 major，但 0.x 沿用既有惯例取 minor」。本任务与该先例同型。
4. **定 `minor` 而非 `patch` 的依据**：本任务新增能力（独立发布门 `agate-release.py gate` +
   `release.yml` 的 `workflow_dispatch` + 新契约级 `level-2.yaml`）并**改变面向新任务的准入语义**，
   属**功能/语义变更**而非缺陷修复 ⇒ 不取 `patch`。

> **意图去向**：`bump_type` 是**意图**，供后续独立发布流程聚合 `[Unreleased]` 条目时选定版本号使用；
> 本任务**不**改 `README.md` badge、**不**把 `[Unreleased]` 切成版本节（那是发布流程的事）。

### 生效边界（务必知悉）

本协议改动**只有在协议被发布/安装后才对使用者生效**：`gate_p8` 的 `delivery.method` 枚举校验读的是
**`AGATE_ROOT` 解析结果下的 `rules/task-data/`**——当前已安装稳定版 **v0.81.0 无 `level-2.yaml`**
⇒ 在该版本下枚举校验为 **no-op**（P6 验收时已用 `AGATE_ROOT=<工作树>/agate` 验证「确由本工作树
`level-2.yaml` 驱动、非真空」：不设 `AGATE_ROOT` 时 `rc=2`，设之则枚举外取值 `rc=1`）。同理，P8 去 tag/version
的语义也**只在新版本被安装后**对使用者的 gate 生效。⇒ 交接提醒见 §9。

## 2. delivery 交付面（结构化字段 + 说明）

```yaml
delivery:
  method: release-notes
  ref:
    - "CHANGELOG.md [Unreleased] 的 TAG0051 条目"
    - "agate/rules/task-data/level-2.yaml（已登记 LEVELS.yaml）"
```

- **取值理由**：枚举来自本任务新增的 `agate/rules/task-data/level-2.yaml`（`method_enum:
  [release-notes, tag-release, none]`）。本任务**交付面 = 合并入 `main` 的协议改动**（**不含 tag/Release**），
  其对外的可发布载体 = `CHANGELOG [Unreleased]` 条目（后续独立流程聚合生成发布说明）⇒ 取 **`release-notes`**。
  - **非 `tag-release`**：本任务**不**触发 tag → GitHub Release；恰是本次改动把该动作移出任务 P8。
  - **非 `none`**：本任务确有对外可发布的**协议改动**（P8 语义、发布门、契约级），并非「无对外交付」。
- **`method ≠ none` ⇒ `ref` 至少 1 项**（level-2 契约 `non_none_requires_ref: true`）：已给 2 项。
- **`reason`** 非必填（仅 `method: none` 时必填）；本处保留以说明「为何是 release-notes」。

## 3. CHANGELOG 更新确认

- **动作**：在 `CHANGELOG.md` 的 `## [Unreleased]` 下**新增 `### 变更` 条目**（含字符串 `TAG0051`）。
- **不改** `[Unreleased]` 这一行、**不动**其它既有条目、**不把** `[Unreleased]` 切成版本节。
- **自查（`check-changelog.py` 为 P8 必经载体）**：`TAG0051` 在 `[Unreleased]` 区域内，且其后紧跟空格
  （满足其 `(^|[^0-9])TAG0051( |:|$|,|-)` 关键词判定）。
- **概述内容**（如实）：发布与任务解耦（任务止于 READY）+ `release.yml` 加 `workflow_dispatch` 人工入口
  + 发布门（`agate-release.py gate`，backstop 于 `release.yml`）+ `delivery.method` 三值枚举（契约级）+
  `state-machine.md` 发布授权转移 + `AGENTS.md`/`git-integration.md` tag 时点统一 + R6 wrapper。

## 4. roadmap 回写确认（RM-AG0043 硬判据）

- 反查 `agate-workspace/roadmap/roadmap.md`「关联任务」列含 `TAG0051` 的行 = **RM-AG0103**（唯一一条）。
- **已回写**：状态列 `scheduled` → **`done`**，并在「更新」列注明（`2026-10-11`）本次交付收尾完成。
- **只改该行的状态列与更新列**，未动其它行、未动「范围（triage 依据）」节。
- **自查**：`awk -F'|' '/^\| RM-AG/ {if (NF!=9) c++} END{print c+0}' agate-workspace/roadmap/roadmap.md`
  → **0**（列数未被破坏）。

## 5. debt_check（reviewed）

**`debt_check: reviewed`**。核对 `agate-workspace/debt/tech-debt.md`：本任务过程中登记了 **4 条 open**：

| DEBT id | 标题（摘） | status | 与本次改动的关系 |
|---|---|---|---|
| DEBT0067 | `agate-md-field-set` 可写 key 白名单 vs `check-frontmatter.py` 认的合法字段**分叉**（工具写侧不认 `ceremony`/`delivery`/`debt_check`/`dispatch_plan` 等） | `open` | 本任务 P1/P2/P8 声明字段时触碰；**未闭合**（主题为工具口径统一） |
| DEBT0068 | P2 卡把 `batches[].output` 列为合法可选键，而 `MAX_DEPTH=3` 因该键（深度 4）判 ERROR——卡与 checker 矛盾 | `open` | 本任务 P2 触发实证；**未闭合** |
| DEBT0069 | `agate.config.yaml` 的 `release.preset` 声明**无值消费方**（设计内保留为信息性声明） | `open` | 本任务设计选择「保留为声明、不驱动逻辑」；**未闭合**（登记在案） |
| DEBT0070 | `r6-differential.sh::_error_lines` 实际比较口径比文件头自述更宽（成功提示变化被报成差异） | `open` | 本任务以 allowlist D13「登记不改守卫」处置；**未闭合** |

- **本次未新增债务条目**（DEBT0067–0070 已由本任务过程中的评审/P2 登记）。
- 以上 4 条均 `open`、**不阻断**（debt_check 只查留痕存在，不查内容达标、不阻断发布）。

## 6. ④ 交付前验证（**如实跑、如实写**）

本任务 P2 **未声明逐包发布命令** ⇒ 以 `agate.config.yaml::verify.commands` 的**四条**为准（逐字照跑，
releaser 本轮在 HEAD `da4ede21` 实跑）：

| # | 命令（`verify.commands` 逐字） | 实跑 exit | 关键输出 |
|---|---|---|---|
| 1 | `python3 agate/scripts/check-protocol-consistency.py` | **0** | `仅有 433 个 WARNING，无 ERROR。` |
| 2 | `python3 -m pytest agate/tests/ -q -n auto` | **1** | `1 failed, 2958 passed, 2 skipped in 156.48s`；唯一红 = **预存/环境性** `test_bdd_43`（见下） |
| 3 | `bash agate/tests/scripts/count-tests.sh` | **0** | `总计：2961 个测试用例（pytest collect-only 口径）` |
| 4 | `$HOME/.venvs/agate-dev/bin/ruff check agate/` | **0** | `All checks passed!` |

- **命令 2 的退出码 1 说明**：唯一失败 = `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
  ——本机 `opencode` CLI 的 `debug agent` 子命令已漂移为 `agents`（`Unknown subcommand "agent"`），
  **环境性预存失败、与本任务改动无关**，已登记 `known-failures.md`（P0 基线实测同一失败）。该命令的退出码
  不影响本任务判据（本任务 23 条 BDD 均不含「全量 pytest 全绿」）。
- **债务面核对**：见 §5（4 条 open，均不阻断）。
- 说明：本任务另在 P5/P6 阶段实跑过白名单外的判据（`check-obligations.py` = 0、`test_protocol_alignment_review.py`
  = 0、R6 wrapper = 0），**非本次 `verify.commands` 四条**，此处不重复展开（证据见 `P5-test-results/`、`P6-evidence/`）。

## 7. 临时资源清单（releaser → 主 Agent 交接）

- **启动的临时服务 / 进程**：**无**（无 debug server、无临时 daemon、无占用端口）。
- **临时数据库**：**无**。
- **临时数据 / 目录**（均在仓库外 `/tmp/opencode`，不影响 git 状态；本次 releaser 自建）：
  - `/tmp/opencode/tag0051-p8-consistency.log`、`tag0051-p8-pytest.log`、`tag0051-p8-count.log`、
    `tag0051-p8-ruff.log`：§6 四条命令的输出日志（仓库外，无需入库）。
  - `/tmp/opencode/tag0051-r6-corpus`：本任务 P5 的 R6 差分 corpus——由 **R6 wrapper 自管**（`git clone --local`
    重建、每次 `rm -rf` 覆盖）⇒ **清理状态：由 wrapper 自管，仓库外、不被提交**；主 Agent 若需彻底清理可直接
    `rm -rf /tmp/opencode/tag0051-r6-corpus`（**不影响仓库**）。
- **开发安装**：**无**（用系统 `python3`；ruff 用既有 `~/.venvs/agate-dev/bin/ruff`；未新装 editable / 全局包）。
- **canonical 临时产物目录 `<项目根>/.agate-tmp/`**：**未创建**（无残留）。
- **结论**：**无仓库内残留**；主 Agent 无需清理仓库内临时物（`/tmp/opencode` 项随会话生命周期/由 wrapper 自管）。
- **状态标记**：`[PROD_NOT_TOUCHED]`。

## 8. 交付收尾确认（CI / 债务 / 环境）

- **CHANGELOG**：`[Unreleased]` 已含 `TAG0051` 条目（§3）——满足 READY 前置。
- **bump_type 意图**：`minor`（§1）——已声明。
- **CI 口径**：主 Agent 须在提交本产出后跑**双口径**本地彩排（AGENTS.md 工作流 0b）并确保 CI 全绿：
  - PR 口径：`python3 agate/scripts/agate-ci-verify.py --base "$(git merge-base HEAD origin/main)"`
  - push 口径：`python3 agate/scripts/agate-ci-verify.py --push --base "$(git rev-parse origin/main)"`
  - 本 releaser **未**执行（属主 Agent 交付动作；且不得 `git commit`/`push`）。
- **debt_check**：`reviewed`（§5）。
- **环境**：`[PROD_NOT_TOUCHED]`；无仓库内临时残留（§7）。
- **生效边界**：见 §1「生效边界」——协议改动**发布/安装后才对使用者生效**（当前稳定版 v0.81.0 下为 no-op）。

## 9. 主 Agent 待办（P8 gate 通过后亲自执行，releaser 不做）

1. **跑 `check-gate.py P8 $TASK_DIR`**（硬判据：`bump_type` / 结构化 `delivery` / `debt_check` /
   roadmap 关联 RM `done` 反查；version/CHANGELOG/tag 三项在稳定版 v0.81.0 下为 WARNING、本任务改动后更不再要求）。
2. **P5 验证**（P8 卡条件化表述）：`python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`；
   `reuse_allowed` → 复用 `P5-test-results/`；否则完整重跑 `gate_commands.P5`。
3. **CI 双口径彩排**（§8）→ 全绿后提交。
4. **commit（本任务止于 READY，无 tag / 无 version bump）**：`git add` 任务目录（含 `.state.yaml` phase=P8 +
   P8-release.md）+ `CHANGELOG.md` + `roadmap.md`；本任务触及 `agate/` 协议本体/脚本 ⇒ commit message 须带
   `self-gate-review:` 留痕（SELF-GATE；仅 WARNING 不拦截，但本任务 P4 各批均已留痕）。
5. **READY 收尾**：`[PROD_NOT_TOUCHED]` 确认；按 §7 临时资源清单核对无仓库内残留；
   进入 READY 须单独再提交一次（phase=P8 提交 P8 产出 → 再改 READY 单独提交，见 P8 卡）。
6. **对外发布（tag → Release）不在本任务内**：由**独立发布流程**经 `workflow_dispatch` 人工授权触发，
   并先过发布门（`agate-release.py gate`）。**不可逆外部动作须用户授权**，不得由 agent 自动执行。

---

> 注：本文件不含 PASS/FAIL 预判——所有结果均为 releaser 本轮自检的**客观运行输出**，gate 判定由主 Agent 亲自执行。
