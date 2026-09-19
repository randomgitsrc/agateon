---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P8 首次派发（非重试），**releaser 模式（implementer P8 模式）**。

### 目标

产出 `P8-release.md`：发布准备的**提案与核实清单**（bump_type、版本号变更文本、CHANGELOG 版本化文本、UPGRADING 新章节文本、roadmap 回写文本、债务核对、临时资源清单）。**不执行** git commit / tag / bump-version，**不直接编辑** `README.md` / `README.zh-CN.md` / `CHANGELOG.md` / `agate/UPGRADING.md` / `agate-workspace/roadmap/roadmap.md` / `agate-workspace/debt/tech-debt.md`——这些由主 Agent 在 gate 验证通过后亲自执行；你只给出「主 Agent 可直接采用」的文本。

### 约束

1. **先读先例**：`agate-workspace/tasks/TAG0035-gate-robustness/P8-release.md`（结构与深度参照）、`git show --stat` 该任务的 `wf(TAG0035-P8)` 提交（改了哪些文件）、`AGENTS.md`「版本发布清单」。本任务的 P8 提交应覆盖同样的文件面：`README.md` + `README.zh-CN.md` version badge、`CHANGELOG.md`（`[Unreleased]` → 新版本号章节 + 日期）、`agate/UPGRADING.md`（新增本版本章节——无破坏性变更也须写"（无破坏性变更）"，v0.62.0 教训）、`agate-workspace/roadmap/roadmap.md`（RM-AG0063 状态回写，P8 gate 硬校验 RM-AG0043）、`agate-workspace/debt/tech-debt.md`（DEBT 状态核对）。
2. **bump_type 判定（须给核实过程，不凭印象）**：当前最新 tag / badge = `v0.71.1`。逐条读 `P1-requirements.md` 的 BDD 标题，判定本任务性质：新增脚本 + 新增可选键 + 协议文档新增节，**均为向后兼容的新增**，零协议内核改动、无破坏性变更 → 建议 `minor`（v0.71.1 → v0.72.0）；请核实是否存在应升 `major` 或仅 `patch` 的理由，并给出你的判定与理由（最终版本号由主 Agent 采纳；如你认为应为其他值须给依据）。
3. **CHANGELOG 版本化文本**：当前 `[Unreleased]` 已有 TAG0036 小节（含 111/65 用例数，已由主 Agent 核对）。给出「把 `[Unreleased]` 转为 `## [vX.Y.Z] - 2026-09-19`（与既有版本章节格式一致，先读 CHANGELOG 中最近一个已发布章节）并在其上保留空的 `[Unreleased]`」的具体做法；核对 `git log v0.71.1..HEAD --oneline` 与 CHANGELOG 无遗漏（该区间含 P0-P7 的 `wf(TAG0036-P*)` 提交与已在分支基线中的 main 提交；只需覆盖本任务交付）。
4. **UPGRADING.md 新章节文本**：仿 `### v0.71.1 — …` 章节结构写出 `### vX.Y.Z — MVWU 阶段 1 观测（TAG0036：RM-AG0063 阶段 1）`：说明「无破坏性变更、零迁移动作」（未改 `.state.yaml` schema / 3 个 hook / gate 分支 / 审计链）、新增内容对既有项目的影响（`tests_filter`/`output` 是**可选**键，缺省行为不变；`check-mvwu.py` 不挂 gate；⑤ 组只是文档补充；`agate-workspace/decisions/` 是否需要项目创建）、以及新项目/老项目各自要做什么（老项目：无需动作；如想采集观察行可用 `check-mvwu.py --observe`）。
5. **roadmap 回写文本**：`agate-workspace/roadmap/roadmap.md` 中 RM-AG0063（主表行 + 「RM-AG0063 详情」节）：本任务只完成设计文档的**阶段 1**；阶段 2（批级 gate）需 Q1 ≥90% 且提交粒度决策（用户裁决）已裁决，**不在本任务内**。按 P8 gate 要求「关联 RM 条目须回写状态为 done」给出：主表状态列改为 `done` 的具体一行文本，以及**如何在详情节如实标注"阶段 1 完成 / 阶段 2 待采样与用户裁决、另立"**（是否需要新登记一条 RM 承接阶段 2，请给出建议与理由，但**不要替用户决定是否登记**——标注为 `[SUGGEST: …]` 交主 Agent/用户）。先读该行与详情节的现有格式。
6. **债务核对**：读 `agate-workspace/debt/tech-debt.md`，写 `debt_check: reviewed` 并在正文列出与本任务相关的条目 id（至少：本任务新登记的 DEBT0043——`_gate_p2_dispatch_plan` 同类 fail-open，只登记未修，状态 open；以及 P4 评审 P1/P2 阶段提到的其他）；核对无遗漏的"应关闭却未关闭"债务。
7. **临时资源清单**（必含，即使为空也要显式写）：本任务是否启动过服务/进程/端口/开发安装/临时数据/临时 git 仓库/临时目录（本任务各阶段验证均在 `mktemp`/pytest `tmp_path` 中完成、无服务进程；请你用 `ps`、`git status --porcelain`、`git worktree list`、`git stash list`、`ls` 等**实际核实**并如实写命令与输出，不得凭记忆）。
8. **P8-release.md 必含字段**：frontmatter `bump_type`（major/minor/patch）、`debt_check`（none/reviewed）；正文含：版本号变更确认（列出全部需改文件与具体改动文本）、CHANGELOG 更新确认、UPGRADING 新章节文本、roadmap 回写文本、债务核对、临时资源清单。frontmatter 用 `agate-md-field-set.py`（phase=P8 / task_id=TAG0036 / parent=P7-consistency.md / trace_id=TAG0036-P8-20260919 / type=release / created=2026-09-19 / status=draft / `agent: implementer`（set 不接受则 Edit 单行）/ bump_type / debt_check）。
9. **只产出 `P8-release.md`（及 `P8-progress.md`）**：不改任何其他文件；不 git add/commit/tag；所有 bash 加 shell 层 `timeout`；分阶段落盘。
10. **不得声称**"已发布/已 tag/已合并"——那些是主 Agent 与用户后续动作。**不得擅自 push**。

### 上游关联

- `P7-consistency.md`（BLOCKER 0；DEVIATION 4 均已处置）；`P2-design.md`（§packages：agate-scripts / agate-docs / agate-tests）；`P6.5-judge-verdict.md`（passed 71/71）；`P0-brief.md`（完成判据与 out-of-scope）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P7-consistency.md、P2-design.md（packages 声明）、P1-requirements.md（BDD 标题）、P0-brief.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P8-release.md（先例）
- CHANGELOG.md、agate/UPGRADING.md、README.md、README.zh-CN.md（badge 行）、agate-workspace/roadmap/roadmap.md（RM-AG0063）、agate-workspace/debt/tech-debt.md
- AGENTS.md（「版本发布清单」）
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P8

路径：phase-cards/P8-release.md
---
# P8 — 发布

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P8 + internal_only: true + internal_only_reason 已声明 → 跳过，标记 READY
> ⑨ P8 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 releaser subagent（implementer P8 模式）执行发布准备
   1.1 写 P8-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. releaser subagent 产出 P8-release.md，**不执行 git commit/tag**
3. 主 Agent 执行 gate 验证 → 通过后执行 bump-version + CHANGELOG 更新 → 同一 commit + tag
4. 主 Agent 执行 READY 收尾检查（参考 P8-release.md 临时资源清单）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + P8-release.md，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 READY，不要提前写 DONE——phase = 本 commit 的产出阶段；终态 DONE 收尾随任务终态 commit 一起

## 如果是重试

→ 读 agate/rules/state-transitions.md 确认 retry 上限（P8 MAX=2）

## 执行方式

releaser subagent（implementer P8 模式）执行以下发布准备步骤：

1. 读取 P2-design.md packages 声明，确定需 bump 的包
2. 为每个 package 执行发布检查命令
3. 更新 CHANGELOG [Unreleased] → 版本号
4. 确认债务清单：读 `{AGATE_WORKSPACE}/debt/tech-debt.md`（若存在），在 P8-release.md 写入 `debt_check:` 字段（TAG0001 Phase 3）
5. 产出 P8-release.md（含 bump_type、版本号变更确认、CHANGELOG 更新确认、debt_check 字段、临时资源清单）

> **注意**：releaser subagent 不执行 bump-version / git commit / git tag，这些由主 Agent 在 gate 验证通过后亲自执行。

## 多包发布拆批（模式 2/3，条件触发）

> 仅当 P2 packages > 1 时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry 见 dispatch-protocol「派发编排机制」并行规则。

多包发布时 P8 可拆批并行（模式 2 静态拆批 / 模式 3 并行）：

1. 每个 package 派一个 releaser subagent（implementer P8 模式），各写 `P8-release-{pkg}.md`
2. 各 releaser 只处理自己包的发布准备（版本 bump 建议 + CHANGELOG 更新 + 发布检查命令）
3. 所有 releaser 返回后，主 Agent 派合并 subagent 整合唯一 P8-release.md
4. 合并 subagent 需交叉核对：各包版本号不冲突、bump_type 汇总一致、CHANGELOG 变更合并无遗漏
5. 主 Agent 在 gate 验证通过后统一执行 bump-version / git commit / git tag

**合并机制**：单包时 releaser 直接产出 P8-release.md（不走合并）；多包时各 releaser 产 P8-release-{pkg}.md，合并 subagent 整合唯一 P8-release.md 供 gate 检查。

## releaser→主 Agent 交接

P8-release.md 中的**临时资源清单**是 releaser→主 Agent 的交接文件：
- releaser subagent 负责写入临时资源清单（本任务启动的临时服务/进程/数据/开发安装）
- 主 Agent 使用该清单执行 READY 收尾检查中的清理工作
- P8-release.md 由 releaser subagent 产出，主 Agent 不直接编写

## 前置条件

- [ ] P7-consistency.md 通过（无 BLOCKER / DESIGN_GAP 已配对）
- [ ] P2-design.md packages 声明（决定哪些包需要 bump）

## 产出规格

P8-release.md 必须包含：
- `bump_type: major / minor / patch`
- `debt_check: none / reviewed`——债务清单确认留痕（TAG0001 Phase 3）：`none` = 本次无关注项（合法选项，不视为失败）；`reviewed` = 已核对，建议正文附条目 id 清单。只查留痕存在，不查内容达标、不阻断发布
- 版本号变更确认（version 文件已修改）
- CHANGELOG [Unreleased] → 新版本号
- 临时资源清单：本任务启动的临时服务/进程/数据/开发安装

## gate 规则

```bash
check-gate.py P8 $TASK_DIR
```

- bump_type 字段存在
- `debt_check` 字段存在（缺失 → exit 1；内容任意，含 `none` / 未关闭债务 → 不阻断，BDD-17）
- 暂存区有 version 文件变更
- 暂存区 CHANGELOG 有变更
- 若任务在 `agate-workspace/roadmap/roadmap.md` 有关联 RM 条目（按 `task_id` 反查「关联任务」列），须先回写「状态」列为 `done`，否则阻断（RM-AG0043）

主 Agent **必须亲自执行**以下验证（不可跳过、不可委托 subagent）：
- 从 P2 packages 逐包读取发布检查命令并执行 → 全部 exit 0
- **P5 验证（TAG0016 BDD-14 精简为条件化表述，底线不变——至少一次客观验证动作不可省）**：
  跑 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`，读 stdout 的
  `AUDIT7_RESULT: <reuse_allowed|reuse_blocked|no_reuse_claim_possible>` 行判定：
  - `AUDIT7_RESULT: reuse_allowed`（exit 0）→ 复用同一份 `P5-test-results/`（不重新执行命令）
  - `AUDIT7_RESULT: reuse_blocked`（exit 1）或 `AUDIT7_RESULT: no_reuse_claim_possible`
    （exit 0 但结果非 reuse_allowed）→ 完整重跑 `gate_commands.P5`（exit 0 + failed==0）
   - **⚠️ 时序注意（DEBT0013）**：若 `gate_commands.P5` 的链路包含
     `check-protocol-consistency.py` 的 CHECK 7（README version badge 与最新 git tag 一致性），
     P5 重跑应安排在 **commit + 创建 git tag 之后** 进行，而非 bump 版本文件后立即重跑——
     bump 已完成、tag 尚未创建的中间状态下，CHECK 7 必然报 `badge vX.Y.A != tag vX.Y.B` ERROR，
     这是设计使然（校验的是"发布完成态"），不是回归。先 tag 后重跑即 0 ERROR。
- `git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 无遗漏
- 从 P2 packages 验证 version 文件路径

## READY 收尾检查（P8 gate 通过后）— 主 Agent 亲自执行（不派发 subagent）

参考 P8-release.md 临时资源清单执行清理。以上检查项无 gate 脚本自动验证（已知缺口），**必须逐项实际执行检查命令**（如 `ps aux | grep debug` 确认服务已停止、`git status` 确认工作区干净），不得仅凭记忆打勾。

**状态与版本**：
- [ ] .state.yaml phase == READY
- [ ] {AGATE_WORKSPACE}/tasks/active-tasks.md 任务行状态已更新
- [ ] git 工作区干净
- [ ] git tag 已创建
- [ ] 若本任务触发复盘（异常模式 / 发现机制缺口 / 高价值任务），复盘产出
  `tasks/{Txxx}/retrospective.md` 基于 `agate/assets/templates/retrospective-template.md`
  模板撰写

**测试环境已清理**：
- [ ] 调试服务/进程已停止
- [ ] 临时数据已删除
- [ ] 测试占用的端口已释放

**开发环境已还原**：
- [ ] 开发安装已卸载
- [ ] 系统环境无污染
- [ ] 项目依赖恢复到发布版本

**协议一致性（改造协议自身的任务必做，TAG0001-0003 批次 D4 教训）**：
- [ ] **在干净 checkout 上跑一次 `check-protocol-consistency.py`**（`git clone` 到临时目录或 CI 兜底确认），0 ERROR
  - 原因：本地 worktree 的 `.worktrees` 路径过滤会掩盖任务产出文件的扫描问题，本地 0 ERROR ≠ CI 0 ERROR
  - 若无法干净 checkout，**至少确认 CI 的 consistency job 对本次 PR 通过**
- [ ] **确认任务产出目录（`docs/tasks/` 或 `{AGATE_WORKSPACE}/tasks/`）不被一致性检查器误扫**（若为 dogfooding 任务，任务产出应已在 `NARRATIVE_DIRS` 白名单）

**生产环境无残留**：
- [ ] 无 PROD_TOUCHED 标记（触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`）
- [ ] 生产数据/API 未被测试写入

## 推进条件（全部满足才写 phase: READY）

- [ ] bump-version 完成 + P5 验证全绿（重跑或复用 `P5-test-results/`，见上方「gate 规则」条件化表述）
- [ ] CHANGELOG 已更新
- [ ] git tag 已创建
- [ ] READY 收尾检查全部通过

## 常见错误

1. **不重跑 P5 gate**：bump-version 后直接 tag，不确认测试仍全绿
2. **CHANGELOG [Unreleased] 留在模板状态**：版本 bump 完但 CHANGELOG 没更新
3. **忘记清理测试环境**：debug server 还在跑、临时数据没删 → READY 不干净
4. **临时资源清单遗漏**：P4/P5 阶段启动的服务/安装的包没记录 → 清理时遗漏
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- READY → DONE：任务完成，代码可合并/发布
- 本任务是 agate 链条的终点——P8 完成后任务状态转为 DONE

> 完成 → 任务 DONE
<!-- AGATE_CARD_END -->

<objective_info>
- 分支 `feat/TAG0036-mvwu-pilot`；最新 tag `v0.71.1`（README badge 同）；本地 `main` = `7f3ef3b`（origin/main，已含 PR #344/#345 的 docs-site 提交，分支基线为 `efb113b`，落后 4 个 main 提交）。
- P5：1842 passed / 2 skipped；P6：71/71；P6.5：passed 71/71；P7：BLOCKER 0。
- 本任务新登记 `DEBT0043`（open）。
</objective_info>
