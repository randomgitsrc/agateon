---
phase: A0-hotfix
generated_by: 主 Agent（A0 走 hotfix 通道，不占 TAG0050 的 P0–P8；P1 §8 判定）
task_id: TAG0050
role: implementer
batch: A0
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标（A0 hotfix）
按 TAG0050 的 **批 A0**（设计 §2.8 / §2.4；P1 §8 判为 hotfix 通道）实现两处**缺陷修复**，使 `agate/tests/integration/test_tag0050_a0_a1_ledger.py` 中 **BDD-01 / BDD-02** 的用例转绿：

1. **F8 修复**（`agate/scripts/pre-commit-gate.py:370`）：现以 **3 个参数**调用 **2 参数**的 `append_event`（`append_event(task_dir, "prod_touched_in_paused", {"task_id": task_id})`）→ 抛 TypeError 被吞掉 ⇒ PAUSED 时的生产接触留痕**从未写成功**。改为正确的 2 参形态：
   ```python
   append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})
   ```
   （以 `agate_common.append_event` 的实际签名为准——先读它的定义。）

2. **`check-gate` 对不存在的任务目录返回 1**（设计 §2.4 / P2 §10 G1）：实测现状**随 phase 不同**（P7→0 假 PASS、P5→2、其余→1）。改为**所有 phase 统一 rc=1**（含 P7/P5），落点在 `check-gate.py` 的 `main()` **单点早检**（分派之前）。

### 约束
- **只改这两处 + 必要的测试/CHANGELOG**；不改其它行为。
- **A0 是 hotfix**：不建 P0-P8 产物；但**碰 `agate/` 协议本体 ⇒ 触发 SELF-GATE**，提交信息须留 `self-gate-review:`（由主 Agent 在 commit 时写，你只需在 progress 说明改动面）。
- 不引入新行为、不顺手改其它。
- **平台无关**：新代码/测试不得有平台假设（裸 `python3` / 硬编码 PATH / 系统临时目录字面量；注释也算）。
- 只改 agateon 本仓。

### 输入文件
- `agate-workspace/tasks/TAG0050-task-data-contract/P1-requirements.md`（BDD-01/02 的 Given/When/Then）
- `agate-workspace/tasks/TAG0050-task-data-contract/P2-design.md`（§10 G1 裁决、§2.4）
- `agate/tests/integration/test_tag0050_a0_a1_ledger.py`（**验收测试**，BDD-01/02；当前红）
- `agate/scripts/pre-commit-gate.py`（F8 落点，约 `:370`）
- `agate/scripts/check-gate.py`（不存在目录的 rc 落点，`main()` 早检）
- `agate/scripts/agate_common.py`（`append_event` 签名）
- `{agate_root}/assets/execution-roles/implementer.md`（角色定义）
- `{project_root}/AGENTS.md`（约定）

### 完成判据
- `python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q` 中 **BDD-01 / BDD-02** 用例转绿（A1 的用例仍可红——它们属批 A1）。
- 手动验证：① PAUSED 场景下 `prod_touched_in_paused` 事件**真实落盘**（不是只打印）；② `check-gate.py P7/P5/P0 <不存在目录>` 均 rc=1。
</dispatch_guide>

<objective_info>
- **当前 HEAD**：`75b8add`（分支 `feat/TAG0050-task-data-contract`）
- **A0 是 hotfix**（P1 §8）：不占 TAG0050 的 P0–P8；碰协议本体 ⇒ SELF-GATE + `self-gate-review:` 留痕
- **协议版本**：v0.79.0（`AGATE_ROOT=/home/kity/.agate/v0.79.0/agate`）
- **F8 现状**：`pre-commit-gate.py:370` 3 参调用 2 参 `append_event`
- **check-gate 不存在目录现状**：P7→0 / P5→2 / 其余→1（P2 §10 G1）
</objective_info>
