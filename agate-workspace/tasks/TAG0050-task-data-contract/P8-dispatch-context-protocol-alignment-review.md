---
phase: P8
generated_by: 主 Agent（P8 发布文档改动的 SELF-GATE 对齐审查）
task_id: TAG0050
role: protocol-alignment-review
batch: P8
---

<dispatch_guide>
> ⚠️ 审查对象 = **TAG0050 P8 的发布文档改动**（触发面：`README.md`、`agate/UPGRADING.md`）。聚焦审查，不重开全量。

### 目标
产出 `docs/reviews/agate-alignment-review-2026-10-09-TAG0050-P8.md`，逐条判 ALIGNED / MISALIGNED。

### 范围
1. **版本号与 CHANGELOG 归并**：
   - `README.md` badge `v0.79.0` → `v0.80.0`；`CHANGELOG.md` 顶部 `[Unreleased]`（空）+ `[0.80.0] - 2026-10-09`（迁入原 `[Unreleased]` 内容 + **逐批补 G1/G2/hotfix 条目**）。
   - 核 **CHANGELOG ↔ UPGRADING 覆盖对齐**（4 个批次节都有对应 CHANGELOG 条目）；`TAG0050` 关键词存在；`baseline.reset` 语义保留「一次性、非质量倒退」。
   - 核 `[0.79.0]` 历史节**未被改动**。
2. **UPGRADING 归并**：4 个「未发布 — TAG0050 批 …」节 → 单个 `### v0.80.0 — TAG0050 …` + 节内加粗小节的**结构正确性**；正文内容无丢失/串位；`^### v0.80.0` 存在；无残留 `未发布 — TAG0050` 标题。
3. **截止承诺更正（关键，主 Agent 裁定的核心变更）**：
   - 原 `agate/UPGRADING.md`（v0.79.0 节）与 `CHANGELOG.md`（0.79.0 节）**预告「截止版本 v0.80.0」** 的 config 声明硬切 + `release.preset` 迁移。
   - 本次处置：**UPGRADING 两处**改为「**未排期**（`RM-AG0102` 追踪），**落地时在实际所在版本的 UPGRADING 节公告**——**不预告实施版本号**」；**CHANGELOG `[0.79.0]` 历史节不动**，更正写入 `[0.80.0]` 的 `### 变更` 节。
   - **请独立裁定**：该处置是否**消除**了「给未排期能力预告未来版本号」的问题？是否留下**新的未兑现承诺**（尤其 `agate/**` 全文与 `CHANGELOG`）？是否与「迁移期行为不变」的既有事实一致？
4. **roadmap**：`RM-AG0099` / `RM-AG0101` → 状态列**恰为** `done`；新增 `RM-AG0102`（状态 `scheduled`，承接该欠账）；表列数格式正确（无字面 `|`）。
5. **SELF-GATE 清单**：`python3 agate/scripts/check-protocol-consistency.py`（0 ERROR）；`python3 -m pytest agate/tests/ -q --tb=no -n auto`（除既有环境漂移 1 条外 0 failed）。

### 产出
- 成果：`docs/reviews/agate-alignment-review-2026-10-09-TAG0050-P8.md`
- 留痕：`docs/reviews/agate-alignment-2026-10-09-TAG0050-P8-01.progress.md`（开始前 `rm -f`）

### 约束
- **只读纪律（强制）**：禁止任何破坏性/写仓命令；不得编辑被评审文件。验证只在**仓外可丢弃副本**上做。

### 输入文件
- `README.md`、`CHANGELOG.md`、`agate/UPGRADING.md`、`agate-workspace/roadmap/roadmap.md`
- `agate-workspace/tasks/TAG0050-task-data-contract/P8-release.md`
- 本次 diff（未提交）
- `SELF-GATE.md`、`{agate_root}/assets/review-roles/protocol-alignment-review.md`
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P8

路径：phase-cards/P8-release.md
---
# P8 — 交付收尾

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P8 + internal_only: true + internal_only_reason 已声明 → 跳过，标记 READY
> ⑨ P8 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 releaser subagent（implementer P8 模式）执行交付收尾
   1.1 写 P8-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. releaser subagent 产出 P8-release.md，**不执行 git commit/tag**
3. 主 Agent 执行 gate 验证 → 通过后执行 bump-version + CHANGELOG 更新 → 同一 commit + tag
4. 主 Agent 执行 READY 收尾检查（参考 P8-release.md 临时资源清单）——**含 canonical 临时产物目录 `<项目根>/.agate-tmp/`**（受限 harness 下的探针/一次性脚本；其四项约定与「存在却未被忽略」的 P8 告警见 `platform-notes.md`「受限 harness 通用约束」，忽略片段见 `assets/templates/gitignore-fragment.txt`）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + P8-release.md，若 .gitignore 忽略需 git add -f）
   ⚠️ **本次 commit 的 .state.yaml 须写 `phase: P8`**（phase = 本 commit 的产出阶段）——
   `pre-commit-gate` 对 `READY` 是跳过（不跑 `gate_p8`），**以 READY 提交会让 P8 gate 从不运行**。
   ⇒ **进入 READY 要单独再提交一次**（`phase: P8` 提交 P8 产出 → 再改 READY 单独提交）。
   `check-state-transition.py` 已机械校验「转 READY 时上一次已提交 phase 必须是 P8」
   （P1 声明 `internal_only` 从而合法裁剪 P8 时允许 P7）。
   ⚠️ 终态 DONE 收尾随任务终态 commit 一起，不要提前写 DONE
   （TAG0042 批 1：`agate-next` 亦**不预写**下一阶段，phase 一律由本 commit 的产出阶段写入。）

## 如果是重试

→ 读 agate/rules/state-transitions.md 确认 retry 上限（P8 MAX=2）

## 执行方式

releaser subagent（implementer P8 模式）执行以下交付收尾步骤：

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
2. 各 releaser 只处理自己包的交付收尾（版本 bump 建议 + CHANGELOG 更新 + 发布检查命令）
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
- `delivery` 字段——交付方式声明（P8 为**交付收尾**，须声明交付方式；缺失 → `check-gate.py P8` exit 1）。
  合法取值集合设计未定（见 P4-implementation-batch4.md `[DESIGN_GAP]`），当前只查留痕存在、内容任意放行
- `debt_check: none / reviewed`——债务清单确认留痕（TAG0001 Phase 3）：`none` = 本次无关注项（合法选项，不视为失败）；`reviewed` = 已核对，建议正文附条目 id 清单。只查留痕存在，不查内容达标、不阻断发布
- 版本号变更确认（version 文件已修改）
- CHANGELOG [Unreleased] → 新版本号
- 临时资源清单：本任务启动的临时服务/进程/数据/开发安装

## gate 规则

```bash
check-gate.py P8 $TASK_DIR
```

- bump_type 字段存在
- `delivery` 字段存在（缺失 → exit 1；交付收尾须声明交付方式）
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
   - **⚠️ 时序说明（原 DEBT0013，v0.78.2 起已消解）**：`check-protocol-consistency.py` 的 CHECK 7 已改为
     README badge ↔ **CHANGELOG 最新已发布版本**（**tag 无关**），故 bump 版本文件后、tag 创建前
     重跑不再报错——"发布进行中"（版本尚无对应 tag）判 **PASS + 提示**。
     ⇒ release PR **先合 PR、后打 tag**；tag 指向校验由 `.github/workflows/release.yml`
     的「Verify tag points to matching commit」步承担（tag 名须等于 tag 所指提交的 badge 版本）。
- `git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 无遗漏
- 从 P2 packages 验证 version 文件路径

## READY 收尾检查（P8 gate 通过后）— 主 Agent 亲自执行（不派发 subagent）

参考 P8-release.md 临时资源清单执行清理。以上检查项无 gate 脚本自动验证（已知缺口），**必须逐项实际执行检查命令**（如 `ps aux | grep debug` 确认服务已停止、`git status` 确认工作区干净），不得仅凭记忆打勾。

**提交前暂存面审查（凭证/临时物防泄漏，RM-AG0077⑤）**：
- [ ] **`git diff --cached --name-only` 已过目**，确认不含未忽略的临时目录/敏感文件
  - 背景：**项目侧** release 命令常直接 `git add -A`（如 `make bump-version`）。某任务实测它会 stage
    **162** 条路径、其中 **158** 条在未忽略的临时目录下、含 **10 个明文 token/cookie** ⇒
    **凭证入 git 历史不可逆**。协议侧无法改项目命令，故把这一步作为**提交前的显式检查**。
  - 若发现非预期路径：先补 `.gitignore`（片段见 `assets/templates/gitignore-fragment.txt`）再 `git reset` 重来，**不要**带着它们提交

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
- [ ] **canonical 临时产物目录 `<项目根>/.agate-tmp/` 已清理**（或确认无需保留物、已空）
  - 自查：`ls -A .agate-tmp 2>/dev/null`；含明文凭证/会话 token 的先删
  - 约束（受限 harness）：该目录须**已被 `.gitignore` 忽略**（`git check-ignore -q .agate-tmp`）、
    内部文件名**不得**匹配测试收集模式——两项均有 `check-gate.py P8` WARNING 兜底，
    完整约定见 `platform-notes.md`「受限 harness 通用约束」、忽略片段见 `assets/templates/gitignore-fragment.txt`

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
- **当前 HEAD**：`4e7ea04c`（P7 已提交）；P8 文档改动**未提交**
- **协议版本**：v0.79.0 → **v0.80.0**（本提交 bump）
- **P8 gate**：rc=0（3 条非阻塞 WARNING：无 version 文件 / 无 `agate.config.yaml` / tag 待建）
</objective_info>
