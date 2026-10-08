---
task_id: TAG0050
generated_by: implementer
---
# 维护性反模式登记

> **语义边界**：本文件登记**本次任务 diff 引入的**维护性反模式（god-file 跨越 / fuzzy-boundary
> 新增行），与 known-failures.md（登记预存失败）语义相反——这里登记的是"本任务自己造成的"问题。
> 登记 + 数量对齐 + P4 评审 approve 三者齐全才放行，登记本身不构成放行依据。
> 检测命令（P4 自查 / P6 非阻断复跑）：`python3 agate/scripts/check-maintainability.py $TASK_DIR`。

## 本次引入的反模式

| # | 文件 | 反模式类型 | 违规详情 | 理由 | P4 评审确认 |
|---|------|-----------|---------|------|------------|
| 1 | agate/scripts/pre-commit-gate.py | god-file 跨越 | before=998 after=1144 threshold=1000 | G2 的 T4 安全门（P2 §3.1）+ F10 接线（§3.6）为设计强制改动；后续可把 PROD_TOUCHED 扫描/F10 检查抽到独立模块以回落阈值以下 | 是 |

> 填写说明：每条 violation 一行，行首序号用数字（如 `| 1 |`，gate 按 `count_kf_entries`
> 对行首数字列计数，数量必须 ≥ 检测出的 violation 数）；「违规详情」抄检测器输出的
> before/after 行数或 diff 新增行号；样例行首为 `| # |` 不计入登记数。阈值为可配置项
> （`agate-workspace/maintainability.yaml`），默认值仅供参考。
