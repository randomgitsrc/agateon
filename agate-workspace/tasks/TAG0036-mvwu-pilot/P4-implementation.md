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

# P4 实现 — TAG0036 MVWU 阶段 1 试点（主文件）

## 1. 本批实现摘要（波 1 / 批 `mvwu-verdict-observer`）

| 落点 | 内容 |
|------|------|
| M1 | 新建 `agate/scripts/check-mvwu.py`：单文件自包含（方案 A），只读 `import agate_common`（`run_git` / `split_frontmatter` / `resolve_workspace`）；按 P2 §2.2 函数分区实现口径 A-H |
| M18 | `agate/scripts/check-protocol-consistency.py::GATE_SCRIPT_EXEMPT` 新增一行 `"agate/scripts/check-mvwu.py",  # 观测脚本，不挂 gate`；未动 `SCRIPT_ALIGNMENT_ANCHORS` |

关键设计选择：

- 判定流水线固定顺序 tests_filter → evidence → command → exit_code → git_head → expected_red，取首个命中（口径 B）；`exit_code: 0` 而 `failed_tests` 非空并入 exit_code 步（仅当 `failed_tests` 可解析）；重复 id 并入 evidence 步（P2 SUGGEST-A 归口）。
- 证据读取：仅对合规 id 拼 `P4-evidence/<id>.log`，`realpath` 包含性校验（符号链接逃逸不读取）、bytes 读 + 严格 utf-8 解码；逐行 `key: value`（重复键后者覆盖，CRLF 兼容）；`expected_red` / `failed_tests` 仅对值做 YAML flow 解析，元素须全为 `str`。
- 永不执行 `command` / `tests_filter`：只做 `shlex.split` + `shutil.which` / `os.access` 静态探测；首词语义按口径 F（跳过前导 `NAME=value`，`cd/export/set/source/.` 视为可解析）。
- `--observe`：commit 形态与 boundary 共用一次 `git log --no-merges --no-renames --name-only -z` 读取；默认分支基线依次 `origin/HEAD` → `main` → `master`，基线不可确定 / 区间为空时 stderr 输出含 `baseline` 的诊断，verdict 不受影响（BDD-42/50）；boundary 排除当前 workspace 的 tasks 前缀（`resolve_workspace`，BDD-52）。
- 只读 + exit 约定：除 stdout/stderr 外不写文件；任何 verdict exit 0，仅用法/目标目录错误 exit 2；意外异常落该批 `UNKNOWN reason=evidence` + stderr 一行，无 traceback。
- docstring / `--help` 逐字含 `仅检查首词`、`不比对 command 与 tests_filter`、`UNKNOWN 不等价于 PASS，不得作为放行依据`，并写明 exit code 约定与 `--observe` 用法。
- 未偏离 P2/P1，本批无 `[DESIGN_GAP]` / `[SCOPE+]` / `[CLARIFY]`。

自查结果（自查，非 gate；自查通过不等于 P5 gate 通过）：

| 命令 | 结果 |
|------|------|
| `python3 -m pytest agate/tests/unit/test_check_mvwu.py -q` | 109 passed |
| `python3 -m pytest agate/tests/unit/test_mvwu_protocol_docs.py -q --tb=no` | 27 failed / 38 passed（基线 28 红；`test_bdd_70_gate_script_exempt_contains_check_mvwu` 转绿；其余红均为文档类用例，由后续批负责） |
| `python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -q` | 8 passed（含 `test_sg_6_check9_anchor_table_covers_all_gate_scripts`） |
| `ruff check agate/scripts/check-mvwu.py agate/scripts/check-protocol-consistency.py` | All checks passed |
| `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | exit 0，无 ERROR；输出中无 `check-mvwu` 相关新增项（CHECK9-coverage 无新增 WARNING） |
| `python3 agate/scripts/check-mvwu.py --observe agate-workspace/tasks/TAG0036-mvwu-pilot`（只读冒烟） | exit 0，6 行 7 列（本任务尚无证据，全 UNKNOWN，符合预期） |

`[PROD_NOT_TOUCHED]`：未触碰生产环境；测试均在 pytest `tmp_path` 内。

## 2. 批次索引

| 批 id | 产出文件 | 状态 |
|------|---------|------|
| mvwu-verdict-observer（本批） | 本文件 `P4-implementation.md` | 本批已完成 |
| architect-batch-guidance | `P4-implementation-architect-batch-guidance.md` | 由对应批产出 |
| batch-evidence-landing | `P4-implementation-batch-evidence-landing.md` | 由对应批产出 |
| review-anchors-and-decision-recheck | `P4-implementation-review-anchors-and-decision-recheck.md` | 由对应批产出 |
| mvwu-glossary-and-debt-log | `P4-implementation-mvwu-glossary-and-debt-log.md` | 由对应批产出 |
| mvwu-script-registry | `P4-implementation-mvwu-script-registry.md` | 由对应批产出 |

## 3. 新增文件核对表

本项目未采用骨架（无 `P2-skeleton.md`）与 CODE-MAP（无 `agents/CODE-MAP.md`），本节按 P4 卡规格省略核对列；本批唯一新增文件：`agate/scripts/check-mvwu.py`。

## 评审后修复（TAG0036）

- MAJOR（P4-review）：`check-mvwu.py --observe` 耗时列遇超长数字时 `_fmt_duration` 抛 `ValueError`/`OverflowError`，致后续批行丢失。修复三层叠加：`DURATION_RE` 限长（整数/小数各 1-15 位，超出即不可解析落 `-`）；`_fmt_duration` 内捕获 `(ValueError, OverflowError)` 返回 `-`；观察表输出循环加 per-row 兜底（任何意外异常仅令该批输出一行 `UNKNOWN` 观察行，stderr 一行 `internal error`，每批恰一行）。既有耗时口径（`8s`/`8.5s`/缺失→`-`）不变。
- 新增单测 `test_bdd_45_observe_huge_duration_does_not_drop_rows`（参数化 2 例：5000 位整数、400 位 + `.5`），修前红（输出 2 行）→ 修后绿；`test_check_mvwu.py` 用例数 109 → 111，`tests/README.md` 同步。
- 术语（protocol-alignment-review A2）：`agate/CONTEXT.md` `boundary(I1)` 行末尾（定义句之后）补「（`--observe` 列取值 `exact` / `mismatch` / `UNKNOWN`；不参与 verdict）」，原措辞未删、仍三列。

## 新增文件核对表备注（收尾更正）

更正上文「项目未采用 CODE-MAP」的说法：`agate-workspace/agents/CODE-MAP.md` 存在，`check-mvwu.py` 已于本次收尾在其 scripts 节登记（`[CODE_MAP_UPDATED]`）。

## 测试注释小修（testfix，非批次）

P4 收口前发现 `test_mvwu_protocol_docs.py` 第 11 行注释含 `/tmp` 字面量，致 `test_check_platform_assumptions.py::test_bdd_8_clean_tree_zero_detection` 转红；仅改注释措辞（无任何断言/逻辑改动），详见 `P4-progress.md` 的 `[testfix]` 行。
