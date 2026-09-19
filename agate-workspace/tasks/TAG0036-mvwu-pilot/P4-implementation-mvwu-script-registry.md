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

# P4 实现记录 — mvwu-script-registry（波 3）

## 本批摘要

新脚本登记面同步（BDD-69），3 文件：
- M13 `agate/scripts/README.md`：脚本表 `check-debt.py` 行后新增 `check-mvwu.py` 行（观测、不阻断、`--observe`、exit 0=任一 verdict / 2=用法/目标错误）。
- M14 `agate/tests/README.md`：映射表 `check-platform-assumptions.py` 行后新增 `test_check_mvwu.py`（109）与 `test_mvwu_protocol_docs.py`（65）两行；计数为 `--collect-only` 实测。
- M15 `CHANGELOG.md`：`[Unreleased]` 占位句替换为 `### 新增（TAG0036：…）` 小节，未写"机制已生效"。

## 自查结果（非 gate）

- `test_mvwu_protocol_docs.py`：61 绿 4 红；BDD-69 三条全绿。剩余红为非本批（BDD-5 DEBT、BDD-59 术语 x2、BDD-71 对齐审查）。
- `count-tests.sh` 总数 1842 = 1668 + 109 + 65。
- consistency `--strict-errors-only`：0 ERROR，`CHECK9-coverage` 0 条。
- 本批仅改上述 3 文件。

## 新增文件核对表

无新增文件。
