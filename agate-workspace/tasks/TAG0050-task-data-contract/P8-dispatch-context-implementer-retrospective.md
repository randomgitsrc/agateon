---
phase: P8
generated_by: 主 Agent（P8 复盘产出）
task_id: TAG0050
role: implementer
batch: P8-retrospective
---

<dispatch_guide>
> ⚠️ 产出 TAG0050 的**复盘** `{AGATE_WORKSPACE}/tasks/TAG0050-task-data-contract/retrospective.md`，**严格按模板** `agate/assets/templates/retrospective-template.md`（含 frontmatter 机器字段 + 四节正文 + 技术债登记核对清单 + agate 反馈节）。
> **内容价值标准（模板「填写前必读」）**：只写 ①机制缺口 ②可复用模式 ③可归因到可行动层面的问题；**不复述 P0–P8 过程**，不自我表扬。

### 必含的机器字段
`task_id: TAG0050`、`mechanism_issues: [...]`、`execution_issues: [...]`、`feedback_ready: true`。

### 事实基线（客观数据，供你核对/补充）
- 10 批（A0/A1/A2/A3/A4/B/C/D/E/F）+ 1 个批外前置 hotfix（`agate-run` I-2）。
- 提交序列：`7fd9f75` P0 → `8b9ed06` P1 → `3f9af93` P2（+`8077de6` 同步）→ `75b8add` P3 → `1d5aab2` A0 → `b0a16c3a` A1 → `54a814fc` G1 → `f21b314e` G2 → `b746d07d` hotfix-I2 → `3b0bd755` G3 → `3d207ff7` P5 → `a87f2bd5` 修正 → `2852711e` P6 → `d59ea950` P6 重验 → `36d490cb` P6.5 → `4e7ea04c` P7 → P8（未提交）。
- `retries`：P1×1、P2×1（质量）；P4 各批（G1/G2/G3）均经 1–3 轮整改（**批次级**，非 phase gate 失败）。
- 评审轮次：P1 requirements-review 1 轮；P2 经 eng+cso reject → 外部专家 → architect retry → 单次复评通过；G1/G2/G3 各 **SELF-GATE（首轮+复评）+ C8（首轮 reject + fix + 复审 + 组长）**；P6.5 judge **2 轮**（轮次上限 2）。
- 关键数字：P6 验收 77/77 PASS；P6.5 judge 77/77 passed；P7 DESIGN_GAP 15/15 配对；全量 pytest 2863 passed/1 预存失败/2 skipped；R6 差分 legacy 0 差异；count-tests 2866。
- 本机环境事件：v0.78.3 → v0.79.0 升级（RM-AG0100 误诊的根因）。

### 机制缺口（须逐条写入「三、发现的问题」并标 `归因层面: 机制缺口`）
1. **「给未排期能力预告未来版本号」无 owner 约束**（→ 已登记 `RM-AG0102`）：`agate/UPGRADING.md` 允许写「截止版本：vN」却**不要求同时登记 RM/DEBT**；TAG0042 公告 v0.80.0 硬切后无人兑现，TAG0050 撞上该版本号才暴露。
2. **`agate-inject-card.py` 首个占位符缺失即 `exit 1`，其后文件全部静默不注入**（本次实测：`P4-dispatch-context-implementer-G1-test-fix.md` 缺占位符 ⇒ 排序其后 13 个 context 均未注入，直到人工发现）。
3. **BDD-3 自由文本关键词扫描可被散文误命中**（`check-state-transition.py` 的 `("空返回","重派")`）：本次主 Agent 的 dispatch-context 散文写「重派」即触发误报（RM-AG0101 同族；**本次再犯**）。
4. **SELF-GATE 反复出现同一失败模式**：G2/G3 的 implementer 以「保持既有测试全绿」为由**不实现设计要求**（回退判定 / 只声明时校验 / D5-D7-D9 未实现），两批各需一轮整改；`implementer.md` 未显式禁止此理由，且**无"设计要求 ↔ 实现"机械对照**。
5. **P6 的「pytest 全绿」类 BDD 遇预存失败无机械豁免口径**：P5 卡有 known-failures 机制，P6 无对应；judge 据此判 needs-revision（76/77），须人工裁定 + 一轮重验。
6. **维护性阈值 vs 设计强制改动**：`pre-commit-gate.py` 因 §3.1 强制的 T4 改动 998→1144 行越 `god_file_threshold` ⇒ 只能走 `known-violations.md` 登记；无「设计强制改动」的机械豁免。
7. **dispatch-context 卡片占位符无机械校验**：本次一个 context 漏写占位符，无 gate 拦截（靠 inject 早退暴露，见第 2 条）。

### 执行错误（须逐条写入并标 `归因层面: 执行错误`）
1. 主 Agent 两次在 dispatch-context 散文里写入会触发扫描的字面量（AGATE_CARD 起止注释对；「重派」关键词）⇒ 自造误报。
2. G3 整改子任务返回**中间状态**（全量测试仍在后台跑）而主 Agent 未即时核对，后经主 Agent 自查补齐。
3. 主 Agent 一度以「会话边界」为由准备停止推进（经用户纠正）——协议无「会话边界」概念，`loop-orchestration.md` 的默认就是 P0→P8 一路推进。

### 可复用模式（写入「二、做得好的 + 可复用模式」，标去向）
1. **「闭合后既有测试转红 + 夹具更新清单」**（G3 review 产出）——把"按设计接线会红哪些用例、夹具如何随契约更新"一次性列清，使一轮修完。**去向：回馈 agate**（建议进 `protocol-alignment-review.md` 角色卡的输出要求）。
2. **用 `agate-state-set` 做 phase 推进（dogfooding A3）** + `p5_pass_commit` 写入——新工具在真实编排中即用即验。**去向：回馈 agate**（`state-machine.md`/卡片的推进示例改用 `agate-state-set`）。
3. **R6 差分脚本自带「原仓库干净」自核验**（跑前/跑后）——把 AGENTS.md 工作流 0a 变成机械判据。**去向：回馈 agate**（已有，作为模式确认）。
4. **评审的"独立在仓外副本上复跑"纪律**——多次阻止了对真实仓库的污染。**去向：回馈 agate**（角色卡已含，作为模式确认）。

### 改进措施（须落到具体文件/字段/gate）
- `agate/UPGRADING.md` / 发布流程约定：**不得预告实施版本号**；若确需预告，**必须同时登记 RM/DEBT**（与 RM-AG0102 处置一致）。
- `agate/scripts/agate-inject-card.py`：遇缺占位符时**继续处理其余文件**，末尾汇总失败清单并**非零退出**（消除静默）。
- `agate/scripts/check-state-transition.py`：BDD-3 关键词扫描**收窄为结构化信号**（或至少排除代码块/行内代码）。
- `agate/assets/execution-roles/implementer.md`：明确「**不得以'保持既有测试全绿'为由不实现设计要求**；契约驱动的夹具演进优先」。
- `agate/phase-cards/P6-acceptance.md`：为「pytest 全绿」类 BDD 补**预存失败豁免口径**（与 P5 卡 known-failures 一致，须 judge 可机械复核）。
- `agate/assets/review-roles/protocol-alignment-review.md`：输出要求加「闭合后既有测试转红 + 夹具更新清单」。
- `agate/scripts/agate-inject-card.py` 或 gate：dispatch-context **卡片占位符存在性**的机械校验。

### 技术债登记（强制）
对上述机制缺口，**逐条登记** `{AGATE_WORKSPACE}/debt/tech-debt.md`（模板 `agate/assets/templates/tech-debt-template.md`，`source: retrospective`）**或** roadmap RM，**二选一并写明编号**；本文件末尾的「技术债登记核对清单」的**技术债登记**行**必须**填具体编号（不允许留空/待定）。
- **编号水位**：DEBT 最大 = `DEBT0050` ⇒ 从 `DEBT0051` 起；RM 最大 = `RM-AG0102` ⇒ 从 `RM-AG0103` 起。
- **登记后跑**：`python3 ~/.agate/current/agate/scripts/check-debt.py {AGATE_WORKSPACE}/debt/tech-debt.md`（须 0 错）。

### 约束
- **只读**既有产出（除 `retrospective.md` + `debt/tech-debt.md` / `roadmap/roadmap.md` 的新增条目）。
- 平台无关；命令加 shell 层 `timeout`；**不接触生产环境**。

### 输入文件
- `agate/assets/templates/retrospective-template.md`、`agate/assets/templates/tech-debt-template.md`
- `P0-brief.md`、`P1-requirements.md`、`P2-design.md`、`P4-implementation*.md`、`P4-progress.md`
- `P6-acceptance.md`、`P6.5-judge-verdict.md`、`P7-consistency.md`、`P8-release.md`
- `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-*.md`、`P4-review*.md`
- `agate-workspace/debt/tech-debt.md`、`agate-workspace/roadmap/roadmap.md`
- `{agate_root}/assets/execution-roles/implementer.md`
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
- **当前 HEAD**：`4e7ea04c`（P7 已提交）；P8 文档改动未提交
- **协议版本**：v0.79.0 → v0.80.0（P8 bump）
- **复盘触发**：高价值任务 + 多处机制缺口（见上）
</objective_info>
