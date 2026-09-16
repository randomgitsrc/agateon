---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0035
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P8 首次派发（非重试）。你是 releaser（implementer P8 模式）。**只产出 P8-release.md，不要执行 git commit/tag，不要直接编辑 README.md/CHANGELOG.md/agate-workspace/roadmap/roadmap.md/agate-workspace/debt/tech-debt.md/agate/UPGRADING.md**——这些文件的实际编辑由主 Agent 在你的 P8-release.md 通过 gate 检查后亲自执行。

### 目标

产出 `P8-release.md`，为本任务（TAG0035 gate 健壮性批）的发布做准备：确定版本 bump 类型、确认技术债清单、列出需要更新的文件清单及具体文本内容（供主 Agent 直接采用，不用主 Agent 自己重新构思）。

### 约束

1. **bump_type 判定**：本任务是纯 bug 修复批（把 gate/check-script 的 fail-open/静默失效改为 fail-closed），不新增功能、不改变任何符合规范调用方的既有行为（未知阶段/非数字阶段名/纯文档无历史场景等边界输入的行为变化，均是修正 bug 而非破坏 API 契约）。按 P8 版本 bump 判定口径"修 bug / 不改 API 行为 → patch"，判定为 **patch**（当前版本 v0.71.0 → v0.71.1）。请你独立核实这个判断是否成立（读一遍 P1-requirements.md 的 14 条 BDD，确认是否存在任何"新增功能/新增对外可见能力"性质的条目——据你核实，全部是判据修复类，应为 patch），若你判断应为其他类型需给出理由。
2. **debt_check 字段**：`{AGATE_WORKSPACE}/debt/tech-debt.md` 中 DEBT0037/DEBT0038 两条与本任务直接相关（本任务即为它们的修复批）。你需要：
   - 读这两条完整登记（`## DEBT0037`/`## DEBT0038` 两个代码块），确认 `closure_criteria` 是否已被本任务满足（对照 P4/P5/P6/P7 的实际产出逐条核对，不要假设）
   - 在 P8-release.md 中写 `debt_check: reviewed`，并列出 DEBT0037/DEBT0038 各自的 closure_criteria 逐条核对结果（满足/不满足 + 证据引用，如 `P6-evidence/bdd-8.log`/`P4-implementation-C.md` 等）
   - 明确给出结论："两条 DEBT 的 closure_criteria 已满足，建议状态改为 closed" 或给出不满足的具体原因
3. **CHANGELOG.md 内容（只写文本，不要编辑文件）**：在 P8-release.md 中给出一段可直接复制进 `CHANGELOG.md` `## [Unreleased]` 位置的新版本条目文本（格式参照 `CHANGELOG.md` 现有的 `## [0.71.0] - 2026-09-10` 条目风格），概述本批 4 个子批（A/B/C/D）的用户可见变化（未知阶段 fail-closed、三处非数字阶段名判据修复、gate_p4 完整度判据放宽、judge 黑白名单假阳性修复），标注来源 `TAG0035：RM-AG0062`。
4. **README.md / README.zh-CN.md 版本徽章更新文本**：给出具体的 diff 描述（第几行、旧值 `v0.71.0`→新值 `v0.71.1`），不需要自己去改文件，只需在 P8-release.md 中写清楚。
5. **roadmap.md 更新确认**：`agate-workspace/roadmap/roadmap.md` 的 `RM-AG0062` 条目当前 `状态` 列为 `scheduled`，`关联任务` 列已是 `TAG0035`——本任务完成后应回写为 `done`（P8 gate RM-AG0043 硬校验）。在 P8-release.md 中确认这一点（不需要自己编辑该文件）。
6. **UPGRADING.md 内容（只写文本）**：参照 `agate/UPGRADING.md` §3「已知破坏性变更（按版本）」现有条目风格（尤其是 `### v0.67.2` TAG0031 那条"无破坏性变更、零迁移动作"的写法），给出一段适用于本次 v0.71.1 的条目文本草稿（说明本批 4 处修复对"合规调用方"（标准数字阶段名、已知阶段、真实自述场景等正常路径）零影响，只影响此前会静默出错的边界/异常输入路径）。
7. **临时资源清单**：本任务全程无临时服务/进程/数据库启动，无开发安装，写"无临时资源"。
8. **P5 验证复用确认**：主 Agent 已跑 `check-p6-provenance.py --audit7-only` 确认 `AUDIT7_RESULT: reuse_allowed`（P5 通过点到当前无非任务工作区文件改动），可复用现有 `P5-test-results/`，不需要你重新跑全量测试；但你仍需在 P8-release.md 中确认"从 P2 packages 读取的每包发布检查命令"这一项——本任务是协议本体单包（无独立发布检查命令，`agate-scripts`/`agate-tests`/`agate-docs` 均属同一 Agateon 协议仓库，无 per-package build/test 命令），说明这一点即可，不需要虚构命令去跑。

### 上游关联

- P2-design.md（packages 声明：agate-scripts/agate-tests/agate-docs）
- {AGATE_WORKSPACE}/debt/tech-debt.md（DEBT0037/DEBT0038 完整登记）
- {AGATE_WORKSPACE}/roadmap/roadmap.md（RM-AG0062 条目）
- CHANGELOG.md（现有格式风格参照）
- agate/UPGRADING.md（现有格式风格参照，尤其 TAG0031 v0.67.2 条目）
- P4-implementation.md / P4-implementation-{B,C,D}.md（4 子批实现摘要，供撰写 CHANGELOG 文案）
- P6-acceptance.md（14 条 BDD 验收结果，供 debt_check 核对 closure_criteria）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P2-design.md
- {AGATE_WORKSPACE}/debt/tech-debt.md
- {AGATE_WORKSPACE}/roadmap/roadmap.md
- /home/kity/oclab/agateon/.worktrees/agate-TAG0035/CHANGELOG.md
- /home/kity/oclab/agateon/.worktrees/agate-TAG0035/agate/UPGRADING.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-B.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-C.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P4-implementation-D.md
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P6-acceptance.md
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
- 环境：worktree 分支 feat/TAG0035-gate-robustness；当前版本 README.md badge = v0.71.0
- 主 Agent 已跑 `check-p6-provenance.py --audit7-only` → `AUDIT7_RESULT: reuse_allowed`（可复用 P5-test-results/，无需重跑全量测试）
- 当前 git HEAD：841614b（P7 commit），工作树干净
- CHANGELOG.md 当前 `## [Unreleased]` 为空（"（暂无——下个版本的变更在此累积。）"）
</objective_info>
