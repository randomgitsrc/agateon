---
phase: P6
task_id: TAG0036
type: exit2-resolution
parent: .state.yaml
created: 2026-09-19T10:42:29Z
agent: main-agent
---
# P6 exit2-resolution

## 触发
- 时间: 2026-09-19T10:42:29Z
- 触发命令: check-gate.py P6（exit 2）
- gate 输出摘要: check-gate.py P6 exit 2（证据目录非空，FAIL=0，NC=0，P6_TOTAL=71）；agate-next 随后判定 check-p6-provenance 未过（exit 2）而暂停，未推进 P7

## 客观证据
- check-p6-provenance.py 输出仅一条提示：`P6-gate-diagnosis.md 缺 agent 字段（协作规范，不阻塞）`，退出码 2；此前（P6.5 诊断文件写入前）同一脚本 exit 0。
- 根因：主 Agent 在 P6.5 阶段写的 `P6-gate-diagnosis.md` frontmatter 缺 `agent` 字段，属主 Agent 自己的文件缺陷，与 P6 证据/验收内容无关。

## 解决
- 解决人: 主 Agent
- 结论: 修正后重验（继续）：给 `P6-gate-diagnosis.md` 补 `agent: main`，重跑 check-p6-provenance.py 应 exit 0，再由 agate-next 推进 P7
- 依据: P6 三道 gate（check-gate.py P6 / check-p6-evidence.py / check-p6-provenance.py）此前均通过；P6.5 judge passed 71/71；仅 provenance 因诊断文件缺字段变为 exit 2
