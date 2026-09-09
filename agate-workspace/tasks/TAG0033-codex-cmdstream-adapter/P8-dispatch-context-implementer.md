---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: implementer
mode: releaser
---

<dispatch_guide>
> 以下派发指引是本次发布准备的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标（releaser，implementer P8 模式）

产出 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P8-release.md` + **实际编辑**发布面文件
（CHANGELOG / README badges / UPGRADING / roadmap / tech-debt）。**不执行** `git commit` / `git tag` /
`bump-version`——这些由主 Agent 在 P8 gate 验证通过后亲自执行。

### 版本判定

- 当前版本 **v0.69.0**（`README.md` L12 badge / `CHANGELOG.md` 顶部 `## [0.69.0]` / 最新 git tag `v0.69.0`）。
- 本任务 = 新增 `CodexAdapter`（纯增量）+ 补 Codex 平台文档 + F1 修复（DEBT0035）。**无破坏性变更**
  （`CommandRecord` IR / 检测引擎 / 阈值 / 既有三适配器零改动，P7 已核）。
- **bump_type: minor → v0.70.0**。

### 必做（逐项实际编辑）

1. **`CHANGELOG.md`**：顶部新增 `## [0.70.0] - 2026-09-09` 节（格式对齐现有 `## [0.69.0]`；顶部无
   `[Unreleased]` 节，直接新增）。内容覆盖：
   - **新增 `CodexAdapter`**（`agate/scripts/agate-cmdstream-adapters.py`，`ADAPTERS` 注册表键 `"codex"`）
     —— RM-AG0055 命令流机制新增 Codex 平台适配器，subagent 存活/卡死检测覆盖 Codex：解析
     `~/.codex/sessions/**/rollout-*.jsonl`（含 `spawn_agent` 子会话独立文件）为 `CommandRecord` IR；
     `probe` / `list_sessions` / `read_commands` 三方法。检测引擎 / 阈值（RM-AG0055 §3.4.3）/
     `CommandRecord` IR / 既有三平台适配器**零改动**（RM-AG0055 §3.4.4「约一个文件」扩展点兑现）。
   - **`agate/platform-notes.md` Codex 章**从「待补充」补为完整能力矩阵（非交互 `codex exec` / `-m` /
     `-c model_reasoning_effort` 推理档 / `--dangerously-bypass-approvals-and-sandbox` + 中间档 `-s` /
     `spawn_agent` 原生子派发 / `--json` / `resume`；退出码不可靠须解析 `--json`；model 阵容随账号类型变；
     `multi_agent` feature flag）+ 实机验证记录（codex-cli **0.153.4** + ChatGPT 登录，2026-09）。
   - **`agate/SETUP.md` 新增 Codex 接入小节**（`npm i -g @openai/codex` + `codex login` + 自动化环境绕过 flag）。
   - **F1 修复（DEBT0035，P5→P4 回退）**：`CodexAdapter` pending 判据从 `status != "completed"` 收紧为
     「无终态信号才算 pending」（新增 `_codex_is_finished` helper：`status ∈ {completed,failed}` ∪
     `completed_at_ms` 非 None ∪ `exit_code` int 非 bool）——修真机 Codex 把已结束非 0 退出命令记
     `status:"failed"` 时被误判 pending、丢真实 exit_code/output_hash 导致 detect 判不出 SPIN 的缺陷。
   - 若已有既有的「三平台命令流适配器 → 四平台」这类需在别处同步的措辞由 P4 protocol-docs 批已处理，无需重复。
2. **`README.md` L12 + `README.zh-CN.md` L12**：version badge `version-v0.69.0` → `version-v0.70.0`。
3. **`agate/UPGRADING.md` §3「已知破坏性变更（按版本）」**：新增 `### v0.70.0 — Codex 命令流适配器 +
   平台接入（TAG0033：RM-AG0061 + DEBT0035）` 章节，格式对齐 `### v0.69.0`。内容：**本版本无破坏性
   变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 / 3 个 hook 薄壳（无 `.sh` 改动）/
   `CommandRecord` IR / 检测引擎 / 既有三平台适配器；新增 `CodexAdapter` 为纯增量。（CHECK 13：CHANGELOG
   最新版 ↔ UPGRADING §3 章节一致。）
4. **`agate-workspace/roadmap/roadmap.md`**：`RM-AG0061` 行「状态」列 `scheduled` → **`done`**
   （P8 gate 硬校验 RM-AG0043，不回写则阻断）；「更新日期」列改 `2026-09-09`。
5. **`agate-workspace/debt/tech-debt.md`**：
   - **`DEBT0035`**：`status: in_progress` → **`closed`**；`evidence` 追加 `ref: "5f704a0"`（P5 r3 重验）/
     `ref: "49d3353"`（P6 重做）/ `ref: "f484895"`（P6.5 judge）；补 `closed_at: 2026-09-09`。P7
     consistency-reviewer 已核 5 条 `closure_criteria` 全满足（`P7-consistency.md` §6）。`task_id` 已是 `TAG0033`。
   - **新增 `DEBT0036`**（P7 consistency-reviewer 的 V7 措辞滞后路由建议 fallback (b)）：
     `id: DEBT0036` / `category: technical` / `title: "platform-notes.md Codex 章「spawn_agent 嵌套深度未测 /
     max_depth=1 待 V7 复核」措辞滞后——P6 V7 已两次实测 depth=2 可用"` / `status: open` / `priority: low` /
     `evidence`（引用 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6-evidence/real-machine-p6.md`
     + `P7-consistency.md` §5 的 `deviation_count: 1`）/ `impact`（权威源携带指向已实测事实的「未测」指针，
     误导读者；不影响 CodexAdapter 契约或 BDD-25——现「待复核」时效指针本身合规）/ `recommendation`
     （把「未测」收敛为「已实测 depth=2 可用」，保留 `max_depth=1` 事实行 + 交叉引用结构，回跑
     `test_bdd_25` + `check-protocol-consistency.py --strict-errors-only` 确认 BDD-25 不破）/
     `closure_criteria`（① platform-notes.md 措辞收敛为「已实测 depth=2」② `test_bdd_25` 绿 ③ consistency 0 ERROR）/
     `source: retrospective` / `created_at: 2026-09-09` / `task_id: null`。
     跑 `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` 确认 exit 0。

### P8-release.md 产出规格

必须含（P8 卡片产出规格）：
- `bump_type: minor`
- `debt_check: reviewed`——正文附条目 id 清单（DEBT0035 本任务关闭 / DEBT0036 本任务新登记未关闭 /
  其余存量债务与本任务无关）
- 版本号变更确认（README badge ×2 / CHANGELOG / UPGRADING §3 均已实际编辑——逐文件打勾表，比照 TAG0032 P8-release §4）
- CHANGELOG `[0.70.0]` 节内容（本轮已写入 CHANGELOG.md 本体，P8-release.md 里也贴一份供 gate/评审对照）
- roadmap 回写确认（RM-AG0061 → done）
- **临时资源清单**（releaser→主 Agent 交接）：本任务 P1-P6 期间启动的临时服务 / 进程 / 数据 / 开发安装——
  本任务真机验证跑过多次 `codex exec`（在 `~/.codex/sessions/` 生成了若干测试子会话 rollout 文件，
  属 Codex 正常产物、非 agate 生产环境残留，主 Agent 无需清理 codex 会话文件——但要在清单里如实列出
  「`~/.codex/sessions/2026/09/{08,09}/` 下本任务真机验证派生的 rollout 文件」+ 说明「只读观察产物，
  `~/.agate` / worktree git 未被污染」）；无 debug server / 无临时数据库 / 无开发安装（本任务用系统
  `python3` + 既有 `~/.venvs/agate-dev/bin/ruff`，未新装）。
- frontmatter：`phase=P8`、`task_id=TAG0033`、`type=release`（按 `--list` 提示）、`parent=P7-consistency.md`、
  `trace_id=TAG0033-P8-20260909`、`status=draft`、`created=2026-09-09`、`agent=implementer`、
  `bump_type=minor`、`debt_check=reviewed`（frontmatter 用 `agate-md-field-set.py`；`bump_type` /
  `debt_check` 若工具不接受可直接写 frontmatter，写完 `check-frontmatter.py` 确认）。

### 绝对不能做

1. **不执行** `git add` / `git commit` / `git tag` / 任何 `bump-version` 脚本——主 Agent 亲自做。
2. **不改** `agate/scripts/*.py` / `agate/tests/` / `agate/platform-notes.md` 正文 / `agate/SETUP.md` 正文
   （P4 已定稿，P7 已核；V7 措辞收敛走 DEBT0036 后续，本轮不动 platform-notes.md）/ P1-P7 任务产出基线。
3. **不新造** 版本号规则——minor = v0.70.0，就这一个。
4. 范围外改动标 `[SCOPE+]`。

### 自查（非 gate）

- `timeout 60s python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → exit 0
- `grep -c "^## \[0.70.0\]" CHANGELOG.md` → 1；`grep -c "version-v0.70.0" README.md README.zh-CN.md` → 2；
  `grep -c "### v0.70.0" agate/UPGRADING.md` → 1
- `grep -nE "RM-AG0061.*done" agate-workspace/roadmap/roadmap.md` → 命中
- **不重跑全量 pytest**（主 Agent 在 tag 后按 P8 gate「P5 验证」条件化重跑/复用）——你只做发布面文件编辑。

### 上游关联

- **P2-design.md**（frontmatter `packages: [agate-scripts, agate-docs, agate-tests]`——bump 范围 = agate
  协议本体，版本引用文件见 AGENTS.md「版本引用文件清单」：README badge / CHANGELOG / UPGRADING）
- **P4-implementation.md**（改动全貌——CHANGELOG 内容来源：adapter-core §1-3 + protocol-docs 批 + 重试#1 F1 修复）
- **P7-consistency.md**（§5 V7 措辞滞后 deviation_count=1 → DEBT0036；§6 DEBT0035 closure 5/5 全满足 →
  DEBT0035 → closed；packages 一致性确认）
- **DEBT0035**（`agate-workspace/debt/tech-debt.md`——F1 回退债，本轮关闭）
- **roadmap RM-AG0061**（`agate-workspace/roadmap/roadmap.md` line ~69——本轮回写 done）
- **AGENTS.md**「版本发布清单（教训浓缩）」+「版本引用文件清单」
- **TAG0032 P8-release.md**（`agate-workspace/tasks/TAG0032-*/P8-release.md`——格式范本：逐文件打勾表 /
  bump_type 判断依据 / CHANGELOG 节内容 / 债务清单节 / 临时资源清单）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P7-consistency.md`（§5 V7 / §6 DEBT0035 / packages 一致性）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（CHANGELOG 内容来源——三批改动）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§1 任务复述 + §5 范围 + §7 真机清单——CHANGELOG 措辞参照）
4. `CHANGELOG.md`（顶部 `## [0.69.0]` 格式范本——对齐新增 `## [0.70.0]`）
5. `README.md` + `README.zh-CN.md`（L12 badge）
6. `agate/UPGRADING.md`（§3 `### v0.69.0` / `### v0.68.0` 格式范本）
7. `agate-workspace/roadmap/roadmap.md`（RM-AG0061 行——回写 done）
8. `agate-workspace/debt/tech-debt.md`（DEBT0035 段 + 尾部——关闭 DEBT0035 + 新增 DEBT0036；DEBT0034/0035 格式范本）
9. `agate/assets/templates/tech-debt-template.md`（DEBT0036 字段表）
10. `agate-workspace/tasks/TAG0032-version-lifecycle/P8-release.md`（P8-release.md 格式范本）
11. `agate/assets/execution-roles/implementer.md`（角色定义——P8 releaser 模式）
12. `agate/phase-cards/P8-release.md`（本阶段卡片——产出规格 / gate 规则 / releaser→主 Agent 交接）
13. `AGENTS.md`（worktree 根——「版本发布清单」「版本引用文件清单」「release PR 必须普通 merge」）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P7（P8 产出 commit 随 P8-release.md
  推进 READY）/ judge.enabled=true。HEAD = `ba66919`（P7 commit）。当前版本 v0.69.0。
- **P7 结论**：`blocker_count: 0` / `deviation_critical_count: 0` / `deviation_count: 1`（V7 措辞，非阻塞）/
  DESIGN_GAP 0 / CODE-MAP `[CODE_MAP_SYNC]` / packages P1==P2==`[agate-scripts, agate-docs, agate-tests]`。
- **DEBT0035**（现 `status: in_progress`）：P7 §6 确认 5 条 closure_criteria 本任务 5/5 全满足——本轮关闭。
- **无破坏性变更**：`git diff v0.69.0..HEAD -- agate/scripts/agate-cmdstream-detect.py
  agate/scripts/agate-cmdstream-ir.py` 空；`CommandRecord` dataclass / 阈值 / 既有三适配器 class 体未动。
- **P8 gate 规则**（`check-gate.py P8`）：`bump_type` 字段存在 + `debt_check` 字段存在 + 暂存区有 version
  文件变更（README badge）+ 暂存区 CHANGELOG 有变更 + roadmap RM-AG0061 回写 `done`（RM-AG0043 硬校验）。
  releaser 只备好文件编辑，gate 由主 Agent 跑。

### 返回

返回：P8-release.md 路径 + bump_type + 版本号变更逐文件确认（README ×2 / CHANGELOG / UPGRADING §3）+
roadmap RM-AG0061 回写确认 + DEBT0035 关闭确认 + DEBT0036 新登记确认（`check-debt.py` exit 码）+
临时资源清单要点 + 是否有 `[SCOPE+]`。
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
