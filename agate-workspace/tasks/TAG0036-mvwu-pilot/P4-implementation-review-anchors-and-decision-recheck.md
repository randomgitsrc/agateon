---
phase: P4
task_id: TAG0036
parent: P3-test-cases.md
trace_id: TAG0036-P4-20260919
type: implementation
agent: implementer
created: 2026-09-19
status: draft
implementation_dir: agate/
---

# P4 批 review-anchors-and-decision-recheck 实现记录

## 本批摘要

| 文件 | 落点 | BDD |
|------|------|-----|
| `agate/role-system.md` (M8) | `### 专家组并行评审 + 组长汇总` 之后、`## 子派发权限边界` 之前新增 `## 审查锚点：角色文件是否浅化接口（Deep Modules，TAG0036）`（浅化 / 执行顺序 / 资源地图 / 正交；仅成文，不含"已生效"） | BDD-60 |
| `agate/adr.md` (M9) | 头部 `>` 引言块之后、首个 `---` 之前新增 `## 复审触发条件（过时不删）`（已过时+取代 / 不删除 / 新增 ADR 复核 / P7 复审）；既有 ADR 正文零删除 | BDD-65 |
| `agate/phase-cards/P7-consistency.md` (M10) | `## 执行方式` 清单末尾追加第 6 项「架构决策落点与过时标注核对」（仅核对 `decisions/`，不 author 正文） | BDD-66（P7 卡侧） |

## 自查结果（非 gate）

- `pytest test_mvwu_protocol_docs.py -k "bdd_60 or bdd_65 or bdd_66"`：7 passed / 1 failed。失败项 `test_bdd_66_p2_card_decisions_landing_and_reading` 断言 P2 卡（`phase-cards/P2-design.md`），属其他批文件面，本批不改，预期仍红。
- `check-protocol-consistency.py --strict-errors-only`：无 ERROR（CHECK 14 通过）。
- `git diff --stat`：本批仅动上述 3 文件（`task-files.md`、`P4-implementation.md` 卡片、`check-protocol-consistency.py` 的改动来自其他批/波 1）。

## 新增文件核对表

无新增文件。
