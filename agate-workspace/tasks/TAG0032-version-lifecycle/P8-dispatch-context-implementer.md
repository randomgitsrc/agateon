---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: implementer
mode: releaser (P8)
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

P8 发布准备（releaser = implementer P8 模式）：产出 `P8-release.md`（发布记录）。**不执行 `bump-version` / `git commit` / `git tag`**——这些由主 Agent 在 gate 验证通过后亲自执行。

### 版本与包

- agateon 单一版本号（非多包独立发布）。当前发布版 = **v0.68.0**（`git describe --tags` + README badge + CHANGELOG top 一致）。TAG0032 目标版本 = **v0.69.0**
- `bump_type: minor`——理由：加功能（`agate-install.py latest` 别名 / `install.sh --versions` 子命令 / 元仓库整仓形态 `_protocol_root` 解析 / 根 `~/.agate/scripts/` 副本）+ 一处对齐既有意图的行为收敛（legacy 软链布局 install **fail-closed 拒绝** + 三步迁移指引——**向后兼容红线守住**：legacy 单软链用户**不跑新工具**行为完全不变，纯增量红线经 BDD-7 + 全量回归锁定）。无破坏公共 API 行为的 major 变更
- P2-design.md `packages: [agate-scripts, agate-docs, agate-tests]` 是任务内部分类，非独立发布单元——agateon 整体 bump 一次

### 需要产出/更新的清单

1. **`CHANGELOG.md`**：CHANGELOG 顶部无 `[Unreleased]` 节，直接新增 `## [0.69.0] - 2026-09-07` 节（格式对齐既有 `## [0.68.0]` 节）。**须含以下 6 条语义变更**（协议对齐审查 A5 已确认的清单，`docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md` §A5）：
   1. `agate-install.py` 新增 `latest` 显式别名（= 无参 install，幂等）
   2. `install.sh --versions` 新增子命令——一键从零进入版本管理布局（建 `repo/` + 首个 `vX.Y.Z/` + `latest`/`current` 指针 + 根 `scripts/` 副本）
   3. `agate-install.py` / `install.sh --versions` 对 legacy 软链布局 `~/.agate` **fail-closed 拒绝**（**行为变化**：此前会穿透软链把 `repo/`·`vX.Y.Z/` 静默建进源仓库）——附三步迁移指引（`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions`）
   4. `agate-install.py` `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时新增 `git fetch --tags --force --prune`（fail-open）——令重跑 `latest` 跟随上游更高 tag
   5. resolve 链新增**元仓库整仓形态**版本目录支持（`_protocol_root`：`vdir/scripts` 先探、`vdir/agate/scripts` 后探）——GitHub 直装的整仓版本目录现可正确解析到协议子目录（RM-AG0058）
   6. 版本管理布局新增根 `~/.agate/scripts/` 入口副本（决策 B1，单源 copytree，随每次安装/升级刷新）
   - 关联：RM-AG0058、DEBT0034（三步迁移文案双写，本任务登记待后续收敛）
2. **`README.md` version badge**：`version-v0.68.0` → `version-v0.69.0`（L12）。`README.zh-CN.md` 若有同 badge 一并（先 grep 核实）
3. **`agate/UPGRADING.md` §编号章节**：AGENTS.md 发布清单 item 3 + CHECK 13（CHANGELOG 最新版本 ↔ UPGRADING §3 章节一致）——须新增 `### v0.69.0` 章节（对齐既有 `### v0.68.0` / `### v0.67.x` 格式）。**无破坏性变更时也写「（无破坏性变更）」**（v0.62.0 教训）；本版本实际有一处行为变化（install 软链 fail-closed 拒绝），须在该章节写明迁移动作（三步）+ 「legacy 单软链用户不跑 agate-install 行为不变」
4. **roadmap 回写**：`agate-workspace/roadmap/roadmap.md` 的 RM-AG0058 条目「状态」列 `scheduled` → `done`，「更新」列日期改 `2026-09-07`（RM-AG0043：P8 gate 硬校验，不回写 → 阻断）
5. **`debt_check` 字段**：读 `agate-workspace/debt/tech-debt.md`——本任务登记了 **DEBT0034**（三步迁移文案在 agate-install.py 与 install.sh 双写，`status: open`，`task_id: TAG0032`）。P8-release.md 写 `debt_check: reviewed` + 正文附条目 id 清单（DEBT0034 = 本任务新登记、未在本任务关闭，留后续收敛）

### P8-release.md 产出规格（P8 gate 校验）

- `bump_type: minor`
- `debt_check: reviewed`（+ 正文 DEBT0034 条目说明）
- 版本号变更确认（README badge / CHANGELOG / UPGRADING §3 三处 v0.69.0）
- CHANGELOG `[0.69.0]` 节内容（6 条语义变更 + 关联 RM/DEBT）
- **临时资源清单**（releaser→主 Agent 交接文件）：本任务执行期间——启动的临时服务/进程（无——纯脚本 + 文档 + 隔离 HOME 测试，无 debug server）/ 创建的临时数据（隔离 HOME `mktemp -d` 目录，各 subagent 已 `rm -rf`；pytest `tmp_path` 自动清理）/ 开发安装（无）。如实列，若确实无则写「无临时服务/数据/安装，隔离 HOME 已随各阶段清理」
- Lessons Learned（2-3 条关键教训）——如：P2 影响面梳理 §1.1 漏了 `agate/scripts/README.md` / `agate/AGENTS.md` / `agate/adr.md` 三处文档传播目标，靠 SELF-GATE Layer 1 兜住；fix-1 迁就 P3 fixture 导致 CRITICAL（install.sh `$SCRIPT_DIR` 在 curl|bash 断裂），教训 = fixture 须贴近真实形态

### 约束

- **releaser 不执行 `bump-version` / `git commit` / `git tag`**——只改文件 + 产出 P8-release.md；主 Agent gate 验证后亲自执行
- **CHANGELOG / UPGRADING §3 章节的实际编辑本轮做**（这是 P8 产出的一部分，不是"留给主 Agent"）；bump-version 脚本执行 + commit + tag 才是主 Agent 的
- **最小改动**：只动 CHANGELOG / README badge / UPGRADING §3 / roadmap / P8-release.md——不碰代码/测试/其它文档
- 不改 `agate/UPGRADING.md`「版本管理生命周期」节（self-gate fix-1 已定稿）
- 状态标记 `[PROD_NOT_TOUCHED]`

### 上游关联

P1 14 BDD → P6 14/14 PASS → P6.5 judge 14/14 passed → P7 consistency approved（BLOCKER=0，5 GAP REVIEWED）→ SELF-GATE Layer 1 复审全 ALIGNED（0 MISALIGNED，ADR-012 补齐）。DEBT0034 登记。commits：P4 `1d9a322` / P5 `2f50f4c` / P6 `af5bfe6` / P6.5 `5f08bf8` / P7 `2a01095` / self-gate `279c236`。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（packages 声明 + §6 gate_commands 发布检查命令）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 BDD——CHANGELOG 措辞交叉参考）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1/2 + fix-1 + self-gate fix-1——实际改了什么，CHANGELOG 依据）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P7-consistency.md（一致性结论）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md（§A5 = CHANGELOG 6 条清单 + P8 前提条件）
- {AGATE_WORKSPACE}/debt/tech-debt.md（DEBT0034——debt_check 依据）
- {AGATE_WORKSPACE}/roadmap/roadmap.md（RM-AG0058 回写对象，第 66 行附近）
- /home/kity/oclab/agateon/agate/assets/execution-roles/implementer.md（角色定义，稳定版——P8 模式 + 版本 bump 判定 + Lessons Learned + 临时资源清单）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/AGENTS.md（版本发布清单——README badge / CHANGELOG / UPGRADING 章节 / tag / 版本引用文件清单）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/CHANGELOG.md（改动对象——顶部新增 [0.69.0] 节）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/README.md 与 README.zh-CN.md（version badge）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（新增 ### v0.69.0 章节；CHECK 13）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息

- 解释器 `/usr/bin/python3`
- 当前发布版 v0.68.0（`git describe --tags --abbrev=0` 已核）；目标 v0.69.0
- `check-protocol-consistency.py` 用 worktree 自己的（改 CHANGELOG/UPGRADING 后自跑一次确认 CHECK 13 CHANGELOG↔UPGRADING §3 一致——注意 **CHECK 7（README badge ↔ git tag）在 tag 未创建前必然报 badge != tag ERROR，属设计使然**，releaser 只需确认 CHECK 13 通过，CHECK 7 的最终校验由主 Agent 在 tag 后重跑）
- 主 checkout 禁止改动；bash 外层 `timeout` 30-120s；单步串行
- 产出路径硬约束：`P8-release.md` 写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P8-release.md`；CHANGELOG/README/UPGRADING/roadmap 改 worktree 对应文件
- 分阶段落盘：追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P8-progress.md`
- P8-release.md frontmatter 用 `agate-md-field-set.py`（先 `--list`）；Header 成品值：`phase: P8` / `task_id: TAG0032` / `parent: P7-consistency.md` / `trace_id: TAG0032-P8-20260907` / `agent: implementer` / `type: release` / `status: draft` / `created: 2026-09-07`

### 返回

只返回两行：① P8-release.md 路径；② 一句话摘要（≤30 字：bump_type + v0.69.0 + CHANGELOG/UPGRADING/roadmap 已改）。

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
