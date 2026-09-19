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

# P4 实现 — 批 architect-batch-guidance（波 2）

## 1. 本批摘要

| 落点 | 文件 | 内容 | BDD |
|------|------|------|-----|
| M2 | `agate/phase-cards/P2-design.md` | 「dispatch_plan 机器字段」节末新增 `### batches[] 可选键：tests_filter / output 与批切分判据（TAG0036）`：tests_filter/output 权威契约（可选、双引号、禁止全量、expected_red、`P4-evidence/{batch}.log`、`[A-Za-z0-9._-]+`、缺省、`python -m pytest`、AGATE_PYTHON、--observe、不新增 gate 校验）+ 判据一（Tracer Bullet + Walking Skeleton 吸收/拒绝 + 与 P2-skeleton.md 消歧）+ 判据二（Vertical Slice）+ 判据三指针 | 6/8/9/61/62/63 |
| M3 | 同上 | 「gate_commands 声明」节内、`env_constraints 与 gate_commands 的边界` 之后新增 `### 架构适应度检查（Fitness Functions，TAG0036）`（4 个示例维度、由项目自选、本任务无架构适应度检查；不点名具体工具） | 64 |
| M4 | 同上 | 前置条件清单追加 1 条 checklist；「前置条件」之后新增 `## 项目侧架构决策（decisions/，TAG0036）`（读取既有决策、写入时机、已过时 + 被什么取代且不删；无 gate 表述） | 66（P2 卡侧） |
| M5 | `agate/assets/execution-roles/architect.md` | 「批次设计」节末、`## 返回给主 Agent` 之前新增 `### 批切分判据与 tests_filter 写法（TAG0036）`（三判据 + tests_filter 选取法 + output）；四条硬规则逐字未动 | 7/8/9/61/62/63/64 |

## 2. 自查结果（非 gate）

- `test_mvwu_protocol_docs.py -k "bdd_6/7/8/9/61/62/63/64/66"`：本批相关用例全绿；整文件仍红的 7 项（BDD-5/59/69/71）属其他批/后续批，未触碰。（BDD-66 P7 卡侧断言依赖并行批，自查时已绿。）
- `check-protocol-consistency.py --strict-errors-only`：0 ERROR；CHECK 14 PASS。
- `git diff --stat`（本批）：仅 P2-design.md 卡（+46）与 architect.md（+34），纯新增行。
- 未写"已生效/已验证"类断言；未改测试与 scripts。

## 3. 新增文件核对表

无新增文件（本批仅改 2 个既有文档；本记录文件为过程产出）。

## 4. 标记

无 `[DESIGN_GAP]`、无 `[SCOPE+]`、无 `[CLARIFY]`。
