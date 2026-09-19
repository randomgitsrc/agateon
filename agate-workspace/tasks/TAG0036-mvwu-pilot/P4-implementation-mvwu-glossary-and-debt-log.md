---
phase: P4
task_id: TAG0036
parent: P3-test-cases.md
trace_id: TAG0036-P4-20260919
type: implementation
created: '2026-09-19'
status: draft
implementation_dir: agate/
agent: implementer
---
# P4 实现记录：批 mvwu-glossary-and-debt-log（波 3）

## 本批摘要

- M11：`agate/CONTEXT.md` 术语表末尾只追加 5 行三列（MVWU / tests_filter / P4-evidence / 四态 verdict / boundary(I1)），首次定义位置依 P2 §0.1 落点：`docs/design-notes/design-mvwu-protocol.md`（MVWU、boundary）、`phase-cards/P2-design.md`、`phase-cards/P4-implementation.md`、`scripts/check-mvwu.py`；既有行未动。
- M12：`agate-workspace/debt/tech-debt.md` 文末追加 DEBT0043（status open，`check-gate.py::_gate_p2_dispatch_plan` 三处 `return None` 静默放行，evidence 含实测行号 767 / 769-770 / 772-774 / 775-776 / 调用点 919-922）；只登记，`check-gate.py` 未改。

## 自查结果（非 gate）

- `check-debt.py agate-workspace/debt/tech-debt.md`：exit 0。
- `test_mvwu_protocol_docs.py`：64 passed / 1 failed；BDD-5（2 用例）、BDD-59（3 用例）全绿；唯一失败 `test_bdd_71_*`（缺 P4-protocol-alignment-review.md）属 P4 收口产物，不在本批。
- `check-protocol-consistency.py --strict-errors-only`：无 ERROR（仅 WARNING）。
- `git diff --stat`：本批只动 `agate/CONTEXT.md`、`agate-workspace/debt/tech-debt.md`（其余文件差异来自并行批 / 前序波）。

## 新增文件核对表

无新增文件（本记录文件除外）。

## 标记

[PROD_NOT_TOUCHED]
