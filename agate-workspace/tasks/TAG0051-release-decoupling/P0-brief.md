# P0-brief — 任务与发布解耦（P8 不再落 tag；Release 独立流程 + 发布门）

> 主 Agent 亲自填写（P0 产出）。

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
  - "跨 5 个子系统（phase-cards / state-machine.md / AGENTS.md / .github/workflows / agate/scripts）——反向传播面大，须逐子系统核对（SELF-GATE A3）"
  - "`delivery` 字段取值域定死属**破坏性变更**（既有任务写自由文本）——须设计兼容或迁移路径（legacy 不受影响？）"
  - "发布语义变更须证明 **legacy 任务行为不变**——用 R6 双向差分（AGENTS.md 工作流 0a：只在副本上跑）"
  - "`release.yml` 加「tag 所指提交 CI 必须 success」门时，tag push 当下 main CI 可能仍在跑——须设计等待或前置顺序"
  - "人工门落点（state-machine 显式发布授权转移）与既有 PAUSED / NEEDS_CONFIRM 规则的关系须厘清，避免两套确认语义"
  - "P8 卡移除 tag 条件后，`check-gate.py P8` 的 tag 检查须同步移除，否则 gate 与卡片不一致（A1/A2）"
env_constraints:
  debug_env: ""
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
