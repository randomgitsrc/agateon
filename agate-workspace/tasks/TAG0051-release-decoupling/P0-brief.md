# P0-brief — 任务与发布解耦（P8 不再落 tag；Release 独立流程 + 发布门）

> 主 Agent 亲自填写（P0 产出）。
> **立项 2026-10-09；2026-10-11 落在新分支（`task/TAG0051-release-decoupling` @ origin/main）重启，
> 已做「P0-brief 时效性自检」（见文末节）与「同类/影响面预判」（见文末节）。**

```yaml
task: "任务与发布解耦：任务终态 = READY（成果已验证、可交付，不落 tag、不建 Release）；发布成为独立流程（需要时才跑，人工授权一次 + 机械发布门）"
goal: >-
  把**不可逆的对外发布动作**（tag → Release）从任务 P8 中移出。现状：P8 的 READY 推进条件含
  「git tag 已创建」，而 release.yml 以 tag push 为**唯一触发器** ⇒ 推 tag 即发 Release，
  tag 与 Release 不可分；且 tag 早于「合并后 main CI 绿」（TAG0050 事故：发布了 CI 红的提交，
  被迫补 v0.80.1）。目标：① 任务止于 READY（交付物 + CHANGELOG [Unreleased] 条目 + bump_type
  意图 + 交付收尾 + CI 全绿含 push 口径）；② Release = 独立流程（入口 workflow_dispatch；
  门 = 目标提交 CI success + tag↔提交一致 + CHECK 7/13 + roadmap RM done；动作 = 聚合
  [Unreleased] → 定版本 → 切版本节 + badge + UPGRADING → PR → merge → 等 main CI 绿 →
  tag → Release → G-5）；③ 配套：P8 卡移除 tag 条件、delivery 取值域定死、state-machine 显式
  发布授权、AGENTS.md 统一 tag 时点（现三处自相矛盾）。
known_risks:
  - "跨 5+ 个子系统（phase-cards / state-machine.md / rules{phases,obligations,state-transitions} / .github/workflows / agate/scripts / AGENTS.md）——反向传播面大，须逐子系统核对（SELF-GATE A3）"
  - "**同类/影响面预判（2026-10-11 实测）**：`grep -rn 'git tag'` 全仓 94 行命中（含 archived/docs 快照）；**活面 12 个文件**——`agate/phase-cards/P8-release.md`（:122/:156 两处勾选项）、`agate/state-machine.md`（:165 P8→READY 转移 + :177 READY 收尾）、`agate/rules/phases.yaml`（P8.gates 含 'version/CHANGELOG/tag 检查'）、`agate/rules/obligations.yaml`、`agate/rules/state-transitions.md`、`agate/scripts/check-gate.py`、`agate/scripts/agate-release.py`、`agate/scripts/check-protocol-consistency.py`、`agate/git-integration.md`、`agate/assets/execution-roles/implementer.md`、`agate/UPGRADING.md`、`AGENTS.md`。**只改 P8 卡是同类反模式**（本仓反复复发）"
  - "**同类/影响面预判·上下游消费方**：P8 语义有**机械注册面**——`agate/rules/obligations.yaml` 的 **OBL-P8-01..14** 共 14 条（anchor 指向 phases.yaml#P8.outputs / P8-release.md 各节 / state-machine.md#READY 收尾检查），其中 3 条有 enforcement 测试（`test_tag0050_obligations_enforcement.py`）+ 1 条行为测试；改 P8 须同步 obligations + anchor + 测试，否则锚点漂移/测试红"
  - "**同类/影响面预判·同类未来实例**：本条是**立规则**（不是修一处）——READY 的定义、`delivery` 取值域、发布门判据都会被后继任务照抄 ⇒ 必须留下机械拦截（obligations 条目 / gate 检查 / CHECK），不能只改文档措辞"
  - "`delivery` 字段取值域定死属**破坏性变更**（既有任务写自由文本）——须设计兼容或迁移路径（legacy 不受影响？）；OBL-P8-02 有行为测试（`test_obl_p8_02_delivery_missing_blocks`）"
  - "发布语义变更须证明 **legacy 任务行为不变**——用 R6 双向差分（`docs/design-notes/r6-differential.sh`，AGENTS.md 工作流 0a：只在副本上跑，跑前跑后核验原仓干净）"
  - "`release.yml` 加「tag 所指提交 CI 必须 success」门时，tag push 当下 main CI 可能仍在跑——须设计等待或前置顺序"
  - "人工门落点（state-machine 显式发布授权转移）与既有 PAUSED / NEEDS_CONFIRM 规则的关系须厘清，避免两套确认语义"
  - "P8 卡移除 tag 条件后，`check-gate.py` gate_p8 的 tag 检查须同步移除（**现状 tag 存在性已是 WARNING 不阻断**，但 P8→READY 条件与 READY 收尾检查仍写死「git tag 已创建」），否则 gate 与卡片不一致（A1/A2）"
  - "**分支保护是外部设置**（required 6 项）——若实现需改它，登记为需人工授权的步骤，不得由 agent 静默改动"
env_constraints:
  debug_env: "无长驻服务。本仓验证面 = `agate.config.yaml::verify.commands` 四条：`python3 agate/scripts/check-protocol-consistency.py` / `python3 -m pytest agate/tests/ -q -n auto` / `bash agate/tests/scripts/count-tests.sh` / `$HOME/.venvs/agate-dev/bin/ruff check agate/`"
  publish_env: "GitHub Actions（`release.yml` 以 tag push 为**唯一触发器**，无 workflow_dispatch）；分支保护 required 6 项（外部设置）"
executor_env:
  platform: "opencode"
  has_task_tool: true
  has_local_runtime: true
  network: "available"
```

## 备注

- **本任务是首个契约级任务**（账本首行 `task_created`，`contract_level: 1`）——由 TAG0050 交付的
  `agate-task-init` 创建（外部实施评审 M-2 的落地要求）。P0-brief 额外核对项（M-2 建议）：
  每阶段提交后用 `agate-md-field-get` 抽查系统字段；P8 时跑一次 `agate-ci-verify --base`。
- 关联 roadmap：**RM-AG0103**；发布事故来源：TAG0050 P8（2026-10-08/09）。
- 已先行落地的部分（本任务**不再重复**）：`agate-ci-verify --base` 必填 + PR 跑双口径 +
  `gate-backstop` 升 required（PR #415，v0.80.2）。
- **2026-10-11 重启时任务数据在旧分支**（`tag0051-stale-backup`，71 commit 落后 main）——
  已在新分支重建，只带 P0/P1 数据面；旧分支保留作 backup。

## P0-brief 时效性自检（2026-10-11）

**判定：轻微漂移**（不命中 P0 卡判据 1-3 任一条），已更新对应字段并标注，**不阻塞**。

严重漂移逐条排查（**全部不命中**）：

| 判据 | 实测 | 结论 |
|------|------|------|
| 1. `task` 目标方案是否已变化 | `.github/workflows/release.yml` 仍 `on: push: tags: ['v*']`、**无 `workflow_dispatch`**（:4-6）；`P8-release.md` 仍两处「git tag 已创建」；`state-machine.md` 仍写「+ git tag」且 READY 收尾含 tag | 前提成立 |
| 2. `executor_env` 平台/运行时前提 | opencode + task tool + 本地运行时均在；协议 v0.80.2 → **v0.81.0**（仍在 `~/.agate/current`） | 前提成立 |
| 3. `known_risks` 已解决前提/范围重叠 | 未发现本任务目标已被其他任务实现；`RM-AG0098` 相关（发布顺序边界）**已 done 但只解决「顺序被逼成唯一路径」，未解耦 tag/Release** | 前提成立 |

轻微漂移（记录 + 已更新字段）：

- `[P0_STALE: 协议版本 v0.80.2 → v0.81.0，AGATE_ROOT 路径随之变化]` → 已更新「客观查证信息」面。
- `[P0_STALE: 本仓 2026-10-11 新落地 agate.config.yaml 并声明 release.preset: semver-changelog-tag —— 发布检查自此有 config 声明层，本任务须纳入该面（此前只有硬编码逻辑）]` → 已写入 `known_risks`/`env_constraints`。
- `[P0_STALE: 2026-10-09..11 落地 RM-AG0116 协议分支中立（去 origin/main 硬编码 + default_branch() 单源 + pre-commit-local/pre-push-local 中立扩展点）、#445 命令采纳（agate-run --task）、#446 CLI 包装（agate-<x> 真命令形态）——与「AGENTS.md 统一 tag 时点/分支策略」相邻，须协调避免重复或冲突]` → 已写入 `known_risks`。
- `[P0_STALE: 先例设计件 docs/design-notes/design-release-order-boundary.md + docs/reviews/agate-design-review-2026-10-03-release-order.md + handoff-release-order-20261003.md 存在（10-03/04），是最近的前作，P1 必须读并判定重叠]` → 已交 P1 作为必读输入。

## 环境自检（2026-10-11）

- 无长驻服务（协议仓库）；`pyyaml 6.0.1` / `ruff 0.16.4` / `pytest 9.0.3` 可用 ✓
- 全量 pytest 基线：**2920 passed / 2 skipped / 1 failed**（唯一失败 `test_bdd_43` = 本机 opencode CLI `debug agent`→`agents` 环境漂移，与本任务无关）
- `check-protocol-consistency.py`：0 ERROR（432 frozen WARNING）✓
