[PROD_NOT_TOUCHED]

# P5-test-results/unit.md — TAG0035-gate-robustness

phase: P5
agent: verifier
task_id: TAG0035
HEAD (父提交): a87603c9ddad5130bb347e0cedc40860261a1690

本文件记录 gate_commands.P5 六条独立命令的逐条执行结果（严格按 P2-design.md §4 声明的命令，
各自独立跑，不用 `&&` 拼接）。执行环境：worktree `/home/kity/oclab/agateon/.worktrees/agate-TAG0035`，
python3 3.12.3 / pytest 9.0.3 / shellcheck 0.9.0，全部在本地文件系统 + 本地 git 仓库进行，
未触达任何生产环境/生产数据库/外部网络调用。

**未运行 E2E**：P2-design.md frontmatter 声明 `ui_affected: false`，无 `gate_commands.P5_e2e`，
本任务无 UI/E2E 覆盖需求，不产出 e2e.md（符合 dispatch-context 约束 8）。

---

## 命令1: `P5`

命令：`python3 -m pytest agate/tests/unit/ -q -n auto --tb=no`
exit code：0
耗时：21s（timeout 280s 内完成）

原始输出尾部：
```
........................................................................ [ 14%]
.........s.......s...................................................... [ 19%]
........................................................................ [ 23%]
........................................................................ [100%]
1507 passed, 2 skipped in 24.38s
```

判定：**PASS**（1507 passed, 2 skipped, 0 failed）

---

## 命令2: `P5_regression`

命令：`python3 -m pytest agate/tests/regression/ -q -n auto --tb=no`
exit code：0
耗时：1s（timeout 280s 内完成）

原始输出：
```
bringing up nodes...
...............................                                          [100%]
31 passed in 0.98s
```

判定：**PASS**（31 passed, 0 failed）

---

## 命令3: `P5_integration`

命令：`python3 -m pytest agate/tests/integration/ -q -n auto --tb=no`
exit code：0
耗时：12s（timeout 280s 内完成）

原始输出：
```
bringing up nodes...
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 10.65s
```

判定：**PASS**（96 passed, 0 failed）

**三分片合计**：1507 + 31 + 96 = **1634 passed, 2 skipped, 0 failed**（与 dispatch-context 中记录的
P4 阶段基线 `1634 passed, 2 skipped, 0 failed` 一致，独立重跑确认，非复用 P4 结果）。

---

## 命令4: `P5_consistency`

命令：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
exit code：0
耗时：2s（timeout 120s 内完成）

原始输出尾部：
```
仅有 365 个 WARNING，无 ERROR。
```

判定：**PASS**（0 ERROR；365 个 WARNING 为预存 WARNING，与本次改动无关——均为叙事文件/文档引用旧路径
类提示，dispatch-context 已声明与本任务无关，独立核对未见新增 WARNING 指向本任务改动的文件）

---

## 命令5: `P5_shellcheck`

命令：`shellcheck -S warning agate/scripts/*.sh`
exit code：0
耗时：0s（timeout 120s 内完成）

原始输出：
```
(无输出)
```

判定：**PASS**（无 warning/error；本批未改动任何 `.sh` 文件，属基线校验，确认无回归）

---

## 命令6: `P5_count_tests`

命令：`bash agate/tests/scripts/count-tests.sh`
exit code：0
耗时：1s（timeout 60s 内完成）

原始输出：
```
=== pytest 用例覆盖度自检 ===
总计：1658 个测试用例（pytest collect-only 口径）

目标：≥ 749（TAG0011 迁移基线，BDD-1）；迁移期数值单调逼近 749。
```

判定：**PASS**（1658 ≥ 749 基线阈值）

---

## 汇总

| key | exit | passed/failed | 判定 |
|---|---|---|---|
| P5 | 0 | 1507 passed, 2 skipped, 0 failed | PASS |
| P5_regression | 0 | 31 passed, 0 failed | PASS |
| P5_integration | 0 | 96 passed, 0 failed | PASS |
| P5_consistency | 0 | 0 ERROR / 365 WARNING（预存） | PASS |
| P5_shellcheck | 0 | 0 warning/error | PASS |
| P5_count_tests | 0 | 1658 用例（≥749 基线） | PASS |

**总计 failed = 0**（6/6 命令全部 exit 0，无新增失败，无预存失败发现于本轮执行范围）。

**预存失败**：本轮未发现任何预存失败（三分片测试与 P4 阶段基线数值完全一致：1634 passed, 2 skipped,
0 failed；consistency 365 WARNING 与 P4 记录数值一致，无新增）。不需要登记 `known-failures.md`。

**PASSED/FAILED 签名行（供 grep 校验，行首即测试运行器原始汇总格式，非人话摘要）**：
```
passed: 1507 (unit), 2 skipped, 0 failed
passed: 31 (regression), 0 failed
passed: 96 (integration), 0 failed
FAILED: 0 total across P5/P5_regression/P5_integration
```
