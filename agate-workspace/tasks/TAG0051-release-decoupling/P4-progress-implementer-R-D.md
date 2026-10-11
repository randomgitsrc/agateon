
## P4 修复轮 R-D（retry 1）— r6-allowlist 记录本任务有意差异
- 2026-10-11 [PROD_NOT_TOUCHED] 读取 dispatch-context + implementer 角色文件
- 改动前基线复跑（wrapper --src . --dst /tmp/opencode/tag0051-r6-rd）: 差异 2 条，未匹配 2 条，exit 1
  - check-gate:P8 TAG0042-config-and-enforcement rc 2->2 added=1 removed=1
  - check-gate:P8 TAG0050-task-data-contract rc 2->2 added=1 removed=1
  - 被删句原文: ④ 从 P2 packages 验证 version 文件路径
- 追加 D13（kind: new_error, gate: "check-gate:P8", task_scope: legacy, patterns 用被删句原文）并把 D13 加进 required_ids
- 改动后复跑同命令: 差异 2 条，未匹配 0 条，exit 0 → [ALLOWED] x2
- 跑后核验真仓 git status --porcelain（排除本次目标文件）与开跑前逐字节一致 → wrapper 只读真仓
