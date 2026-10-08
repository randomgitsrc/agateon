---
phase: A0-hotfix
generated_by: 主 Agent（SELF-GATE Layer 1 · 变更触发模式）
task_id: TAG0050
role: protocol-alignment-review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令。本审查是 **SELF-GATE Layer 1**（`SELF-GATE.md`「变更触发模式」），对象是 TAG0050 批 **A0**（hotfix）的改动。

### 本次变更的意图（1–2 句）
**A0 是一次缺陷修复 hotfix**：① 修 `pre-commit-gate.py` 中 `append_event` 的**参数个数错误**（3 参调 2 参，TypeError 被吞）——该错误使 **PAUSED 时的生产接触留痕从未真正落盘**（F8）；② 让 `check-gate.py` 对**不存在的任务目录**在**所有 phase** 统一返回 `1`（此前 P7→0 假 PASS、P5→2、其余→1，F15b/§10 G1）。意图是「让两处**已在文档里声称成立**的保证，在实现层真正成立」。

### 第一步：意图分析（你要自行给出）
用 1–2 句话说清"为什么改"（不只是"改了什么"）。

### 第二步：反向传播——列出应被影响的文件
基于意图，推断这次改动**应该传播到哪些文件**（不只 git diff 里的）：
- 衍生改动（一致性连锁）：改了 `check-gate` 的缺失目录 rc、改了 PAUSED 留痕——哪些**文档/卡片/角色文件**的描述需要同步？（例：`state-machine.md` 的 PAUSED 语义、P0/P6 卡对"不存在目录"的表述、`pre-commit-gate` 的账本事件说明、`SELF-GATE.md`/`AGENTS.md` 的相关条文、CHANGELOG）
- 文档传播：协议 md 里是否有"不存在的目录返回 0/2"或"PAUSED 留痕只打印"之类的**现已失真**的表述？
- 角色/模板文件：脚本行为变了，提示词是否过时？

输出：应被影响的文件列表（按优先级）+ 每个的理由。

### 第三步：实际审查范围
本次 diff 涉及：
- `agate/scripts/pre-commit-gate.py`（F8，约 `:370`）
- `agate/scripts/check-gate.py`（`main()` 早检，约 `:1623`）
- 测试：`agate/tests/integration/test_tag0050_a0_a1_ledger.py`（BDD-01/02）

### 审查清单
按 `agate/assets/review-roles/protocol-alignment-review.md` 的 A1–A8 清单逐条审查；重点：**文档声称 vs 实现**是否对齐（尤其 `check-gate` 的 rc 语义在各处的表述、PAUSED 留痕的文档承诺）。

### 产出
- **成果文件**：`docs/reviews/agate-alignment-review-2026-10-07-TAG0050.md`（结构化报告，A1–A8；结论含 MISALIGNED / NEEDS_HUMAN_REVIEW / ALIGNED）
- **留痕文件**：`docs/reviews/agate-alignment-2026-10-07-TAG0050-01.progress.md`（开始前 `rm -f`；只追加原始痕迹，不整理）

### 约束
- **只读纪律（强制）**：禁止任何破坏性/写仓命令（`git checkout/restore/reset/stash/clean/add/commit/switch -f`）；不得编辑被评审文件。需要跑验证只在**仓外可丢弃副本**上做（`git worktree` 或「建→用→清」放同一次 bash 调用）。
- **MISALIGNED 必须给出可复现证据**（命令 + 输出）；NEEDS_HUMAN_REVIEW 需说明为何无法机械判定。

### 输入文件
- `SELF-GATE.md`（变更触发模式模板 + 文件约定）
- `{agate_root}/assets/review-roles/protocol-alignment-review.md`（角色定义 + A1–A8 清单）
- 本次 diff：`git diff -- agate/scripts/pre-commit-gate.py agate/scripts/check-gate.py`
- `agate/scripts/pre-commit-gate.py`、`agate/scripts/check-gate.py`
- `agate/scripts/agate_common.py`（`append_event` 签名）
- `agate/tests/integration/test_tag0050_a0_a1_ledger.py`
- `agate-workspace/tasks/TAG0050-task-data-contract/P1-requirements.md`（BDD-01/02）、`P2-design.md`（§10 G1）
- `agate-workspace/tasks/TAG0050-task-data-contract/A0-dispatch-context-implementer.md`
</dispatch_guide>

<objective_info>
- **当前 HEAD**：`75b8add`（分支 `feat/TAG0050-task-data-contract`）；A0 改动**未提交**（在工作区）
- **协议版本**：v0.79.0（`AGATE_ROOT=/home/kity/.agate/v0.79.0/agate`）
- **改动**：`pre-commit-gate.py:370` F8 参数修复；`check-gate.py main()` 缺失目录单点早检 → 所有 phase rc=1
- **验证**：BDD-01/02 4 passed；`check-gate P0/P5/P7 <不存在目录>` 均 rc=1
- **已知背景**：`check-gate` 缺失目录 rc 实测原为 P7→0 / P5→2 / 其余→1（P2 §10 G1）
- **注意**：全量 pytest 当前含 82 个**新增 TAG0050 测试**为红（P3 TDD 设计使然，非回归）——审查「无退化」时请区分
</objective_info>
