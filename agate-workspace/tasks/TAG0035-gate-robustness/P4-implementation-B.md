---
phase: P4
task_id: TAG0035
parent: P2-design.md
trace_id: TAG0035-P4-B-20260916
agent: implementer
type: implementation
created: '2026-09-16'
status: draft
implementation_dir: agate/scripts
---
# P4-implementation-B — TAG0035 子批 B（三处数字序号假设致非数字阶段名静默失效）

## 改动清单

### 1. `agate/scripts/check-gate.py`（回退抵达检测，`main()` 内 `if old_phase:` 分支）

在既有 `old_num = re.search(...)` / `new_num = re.search(...)` 之后、既有回退比较之前，
新增判空分支：

```python
if old_num is None or new_num is None:
    sys.stderr.write(f"GATE {phase}: 无法解析阶段序号（old_phase={old_phase!r}）\n")
    sys.exit(1)
```

未改动子批 A 已落地的 `handlers.get(phase) is None → sys.exit(1)` 分支（第 1486-1489 行），
两处代码块不重叠。关联：BDD-4（新增判空报错）、BDD-7（数字阶段名回退检测行为不变）。

### 2. `agate/scripts/check-state-transition.py`

- `phase_num(text)`：无匹配返回值由 `0` 改为 `None`，docstring 同步为"无法解析回退 `None`"。
- `main()`：`old_phase`/`new_phase` 求值后新增判空分支（插入在既有检查 1 之前）：
  ```python
  old_num = 0 if (not old_phase or old_phase in ("PAUSED", "READY", "DONE")) else phase_num(old_phase)
  new_num = phase_num(new_phase)
  if new_num is None or (old_phase and old_phase not in ("PAUSED", "READY", "DONE") and old_num is None):
      sys.stderr.write(f"GATE STATE: 无法解析阶段序号（old_phase={old_phase!r}, new_phase={new_phase!r}）\n")
      sys.exit(1)
  ```
  判空分支之后 4 处既有 `old_num > 0 and new_num > 0` 比较逻辑未改动。

**[DESIGN_GAP: dispatch-context 约束 2 给出的判空条件原文（`old_phase and old_num is None`）
只特判了 `old_phase` 为空字符串这一种合法非数字场景，未覆盖 `old_phase` 为控制态
`PAUSED`/`READY`/`DONE`（`get_old_phase` 可合法返回这三者，对应 PAUSED 恢复等场景）。
按原文字面实现会让既有回归用例 `test_st_15_paused_to_p4_recovery_exit_0` /
`test_st_19_commit_gate_paused_recovery_skipped_exit_0` 从通过变为失败（新增回归）。
已将 `PAUSED`/`READY`/`DONE` 与空字符串同等对待为合法 `old_num=0`，不触发判空报错——
该三个字面量与本文件 L246 `new_phase` 特判用的是同一组控制态常量，处理方式对称。
BDD-5 的两个参数化子场景（`old_phase="p-alpha"`/`new_phase="p-alpha"`）不受影响，
仍按预期 fail-closed。]**

关联：BDD-5（两个参数化子场景 fail-closed）、BDD-7（数字阶段名转移判定不受影响）。

### 3. `agate/scripts/pre-commit-gate.py`

- 新增模块级常量（紧邻 `_P_OUTPUT_RE`/`_P_NUM_RE`）：
  ```python
  _P_OUTPUT_ANY_RE = re.compile(r"(?:^|/)[Pp][^/]*-.*\.md$")
  ```
- 2f 节（per-task 一致性检查）：在既有 `staged_outputs`/`staged_added` 判定循环之后，
  新增 2f.1 差集扫描——命中 `_P_OUTPUT_ANY_RE` 但未命中 `_P_OUTPUT_RE` 的文件逐个输出
  `GATE WARNING: 无法识别该产出文件的阶段号，一致性检查未覆盖: {f}`。
- 第 3 节（全局 `staged_all` 循环）：同样在既有循环之后新增 3.1 差集扫描，等价逻辑。
- 未改动 `_P_OUTPUT_RE`/`_P_NUM_RE`/`_phase_num` 本身的匹配范围或内部逻辑，
  两处新增块均为 WARNING，不影响 `main()` 末尾 `sys.exit(0)`。

关联：BDD-6（非标准阶段名产出文件触发差集 WARNING）、BDD-7（标准数字阶段名场景无额外 WARNING）。

## 自测结果

```
timeout 60 python3 -m pytest agate/tests/unit/test_check_gate.py -q -k "tag0035_bdd_4 or tag0035_bdd_7"
→ 3 passed

timeout 60 python3 -m pytest agate/tests/unit/test_check_state_transition.py -q
→ 47 passed（含 tag0035_bdd_5 两个参数化子用例 + tag0035_bdd_7）

timeout 60 python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q -k "tag0035"
→ 2 passed（bdd_6 + bdd_7）

timeout 120 python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_state_transition.py agate/tests/integration/test_pre_commit_hook.py -q --tb=line
→ 312 passed, 2 failed
  失败为 test_tag0035_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md /
  test_tag0035_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md——
  均属子批 C（`_gate_p4` 完整度判据）范围，dispatch-context 已明确标注为本批预期红，
  不在本子批修复范围内，未新增其他回归。
```

以上为自查结果，不代表 P5 gate 已过。

## 改动范围核对（`git diff --stat`）

```
agate/scripts/check-gate.py             |  5 ++++-
agate/scripts/check-state-transition.py | 19 ++++++++++++++++---
agate/scripts/pre-commit-gate.py        | 29 +++++++++++++++++++++++++++++
3 files changed, 49 insertions(+), 4 deletions(-)
```

三处改动均为局部插入（判空分支 / 差集扫描新增块），无跨函数大范围改动。
