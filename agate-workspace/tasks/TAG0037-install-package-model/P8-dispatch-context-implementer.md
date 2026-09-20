---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0037
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P8 首次派发（releaser 模式：发布准备 + P7 遗留收尾；**你不执行 bump-version / git commit / git tag**，这些由主 Agent 在 gate 通过后亲自执行）。

### 目标

1. **收尾 P7 遗留 DEVIATION（文档面）**，均为文字/登记修正，不改脚本与测试：
   - DEVIATION-1：`agate/scripts/README.md`「版本管理」表中 `agate-install.py`、`agate-pack-offline.py`、`install-offline.py` 三行仍写旧机制（repo 单克隆 + worktree add tag、`--uninstall` = 删版本目录 + worktree remove 等），按实际实现（`agate_package` 单一构建器、只装本体、`--adopt`、`--check --portable`、离线 bundle 顶层 = `agate/`、清扫只处理带标记临时目录等）改写；不得重写整表，只改这三行及必要脚注。
   - DEVIATION-3：把用户可见的离线路径行为收紧补记到 `CHANGELOG.md [Unreleased]` 与 `agate/UPGRADING.md` 的 `### v0.73.0` 节（旧格式 offline bundle `agate/agate/scripts` 被拒绝并要求用新版 `agate-pack-offline.py` 重新打包；`vX.Y.Z/` 已存在时 install-offline 改为替换语义；pack 输出目录已存在时拒绝覆盖；`AGATE_REPO_DIR`/`AGATE_SYMLINK` 废弃 WARNING 等——以 P7-consistency.md §6 DEVIATION-3 与 P4-implementation.md 为准，事实先核对再写）。**不要**把 `[Unreleased]` 改名为 `[0.73.0]`（由主 Agent 在 gate 通过后做）。
   - DEVIATION-5：更新 `{AGATE_WORKSPACE}/agents/CODE-MAP.md`，登记新增文件 `agate/scripts/agate_package.py`、`agate/scripts/agate-release.py`（`.github/workflows/release.yml`、`agate/tests/helpers_tag_repo.py` 按 CODE-MAP 既有惯例判断是否需登记）；并在 P8-release.md 说明处理结果。
   - DEVIATION-2（`P3-test-cases.md` 第 120 行引用旧测试名）：属已提交的历史阶段产出，**不改**，在 P8-release.md 记录"已知陈旧引用，接受"。DEVIATION-4（retries 记录）已由主 Agent 补。
2. **backlog 登记**：在 `agate-workspace/roadmap/roadmap.md` 追加 2 条 backlog（先读该文件的条目格式与当前最大 RM 编号，编号顺延不复用）：(a) `install.sh` 重跑时对已存在 `repo/` 做 `git pull --ff-only`（升级自举缺口；P2 [SCOPE+] 主 Agent 裁定本任务不做）；(b) `agate-install.py latest` 从 Release asset 取包（roadmap 拟议模型第 2 项，P1 已声明不属本任务）。**不要改动 RM-AG0066 的状态行**（主 Agent 亲自回写 done）。
3. **产出 `P8-release.md`**：frontmatter（`phase: P8`、`task_id: TAG0037`、`type: release`、`parent: P7-consistency.md`、`trace_id: TAG0037-P8-20260920`、`status: draft`、`created: '2026-09-20'`、`agent: implementer`——agate-md-field-set 拒写的键主 Agent 授权你手写；`bump_type: minor`；`debt_check: reviewed` 并在正文附已核对的 `agate-workspace/debt/tech-debt.md` 相关条目 id 清单，没有则写 `none`）；正文含：版本号变更确认（v0.72.0 → **v0.73.0**，minor，BREAKING 标注；版本文件 = README.md 与 README.zh-CN.md 的 version badge，CHANGELOG `[Unreleased]`→`[0.73.0]` 由主 Agent 执行，此处写"待主 Agent 执行"及检查命令）、CHANGELOG 更新确认、上述 DEVIATION 处置表、**BDD-20 ④ 与 BDD-50 ②–⑥ 的 P8 复验清单**（每项的只读检查命令与判定：`gh -R randomgitsrc/agateon release list` 无 `v0.73.0-tagtest.1`；`git ls-remote --tags origin v0.73.0-tagtest.1` 为空；本地 `git tag -l 'v0.73.0*'`；README badge 非 1.0；PR 描述如实列出 release workflow 触发 `on: push tags v*`、权限 `contents: write`，以及测试 tag 连带触发的现有 workflow（Protocol Tests / Docs Check 因 CHECK 7 + t17 失败，Site Check 成功，deploy-pages 未触发）；roadmap RM-AG0066=done；HANDOFF-TAG0037.md 归档到 `agate-workspace/archived/plans/`；正式 v0.73.0 Release 含 3 个 tarball 资产 + SHA256SUMS）、**临时资源清单**（本任务启动的临时服务/进程/数据/开发安装：无常驻进程；scratchpad 下 agent 建立的实验目录（列出根目录与前缀即可）；远端测试 tag `v0.73.0-tagtest.1` 与其预发布 Release 待用户手动清理（精确名称）；`.agate/formatters/pytest.sh` 任务内覆盖文件的处置说明）。
4. 发布检查命令（P2 packages 的检查命令）：不需要你执行——主 Agent 亲自执行。

### 约束

- 只改：`agate/scripts/README.md`、`CHANGELOG.md`（[Unreleased] 内容）、`agate/UPGRADING.md`（v0.73.0 节）、`{AGATE_WORKSPACE}/agents/CODE-MAP.md`、`agate-workspace/roadmap/roadmap.md`（仅追加 2 条 backlog）、`P8-release.md`（新建）、`P8-progress.md`（追加）。其他文件一律不改。
- 改 `agate/*.md` 后跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 自己的脚本）确认 0 ERROR，并跑受影响的文档类测试（`agate/tests/unit/test_upgrading_lifecycle.py`、`test_upgrading_contract_doc.py`、`test_doc_sweep.py`、`regression/test_no_legacy_residue.py`）。
- **数据安全（用户强制）**：禁止 `rm -rf`/清空重建/删除任何文件；不 git add/commit/push/tag；不触碰真实 ~/.agate、开发 checkout、GitHub（不删除/不推送）；实验只用 scratchpad 新建带序号目录，设 `PYTHONDONTWRITEBYTECODE=1`。
- 不写行首 `- PASS`/`- FAIL`。返回：`P8-release.md` 路径 + 一句话摘要（≤40 字）+ 改动文件列表。

### 上游关联

P7-consistency.md（§6 DEVIATION）、P4-implementation.md、P2-design.md §13

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/P7-consistency.md、P4-implementation.md、P2-design.md
- agate/scripts/README.md、CHANGELOG.md、agate/UPGRADING.md、{AGATE_WORKSPACE}/agents/CODE-MAP.md、agate-workspace/roadmap/roadmap.md、agate-workspace/debt/tech-debt.md
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
