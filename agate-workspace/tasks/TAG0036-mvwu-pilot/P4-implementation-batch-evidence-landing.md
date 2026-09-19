---
phase: P4
task_id: TAG0036
parent: P3-test-cases.md
trace_id: TAG0036-P4-20260919
type: implementation
created: '2026-09-19'
status: draft
agent: implementer
implementation_dir: agate/
---

# P4 实现记录 — batch-evidence-landing（波 2）

## 本批摘要

| 文件 | 落点 | BDD |
|------|------|-----|
| `agate/phase-cards/P4-implementation.md`（M6） | `## 产出规格` 之后、`## 新增文件核对表` 之前新增 `## 批级证据 P4-evidence（MVWU 阶段 1，不阻断，TAG0036）`：路径/filename-safe、机械转录、键集（含可选 failed_tests）、node id + 双引号编码、`check-mvwu.py` 用法指针（观测不阻断、UNKNOWN 不等价 PASS）、不进 judge 白名单 | BDD-10 |
| `agate/assets/templates/task-files.md`（M7） | ① 阶段产出表 `{implementation_dir}/` 行后加 `P4-evidence/{batch}.log` 行；② `# dispatch_plan:` 注释后加 tests_filter/output 可选键说明注释（示例不含裸 python3） | BDD-11 |

BDD-12 负向：未触及 rules/、dispatch-protocol.md、judge.md，测试绿。

## 自查（非 gate）

- `test_mvwu_protocol_docs.py`：BDD-10、11、12 用例通过；其余 25 个失败属其他批（BDD-5/6/7/8/9/59-66/69/71），未动。
- `check-protocol-consistency.py --strict-errors-only`：无 ERROR，CHECK9-coverage 无命中。
- `git diff --stat`：本批仅动上述 2 文件。

## 新增文件核对表

无新增文件（本批产出记录文件除外）。
