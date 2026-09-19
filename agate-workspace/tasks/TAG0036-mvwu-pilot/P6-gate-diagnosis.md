---
phase: P6
date: 2026-09-19
trigger: gate_fail
---
# P6.5 Gate 诊断（judge 阶段）

- 触发：judge 产出 verdict 后，主 Agent 跑 `check-judge-verdict.py`，退出码 1，报「dispatch-context 两节含白名单外任务路径引用: p0/p1/p2/p3/p4/p5/」。
- 根因：`P6.5-dispatch-context-judge.md` 的 `objective_info` 节里，主 Agent 用 `P0/P1/P2/P3/P4/P5/P6` 这种斜杠连写描述阶段提交序列；脚本的路径正则把它当成任务目录路径。**纯措辞问题**：该行没有引用任何黑名单/白名单外文件，judge 也没有读到任何被隔离的信息。
- 处置：主 Agent 仅把该行改写为「各阶段（P0 至 P6，逐阶段）以 `wf(TAG0036-P{N}):` 前缀提交」，其余内容未动。这是对自身派发文件缺陷的修正，不是补写派发指引；judge 的判案范围与信息量不变。重跑 `check-judge-verdict.py` 与 `check-gate.py P6.5` 均 exit 0（criteria 71/71，账本 judge 轮次 1）。
- 后续建议：`objective_info` 也在脚本的「两节」扫描范围内，写作时避免斜杠连写的阶段序列。
