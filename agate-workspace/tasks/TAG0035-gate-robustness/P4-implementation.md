---
phase: P4
task_id: TAG0035
parent: P2-design.md
trace_id: TAG0035-P4-A-20260916
agent: implementer
type: implementation
created: '2026-09-16'
status: draft
implementation_dir: agate/scripts
---

# P4-implementation — TAG0035 子批 A（gate 对未知阶段 fail-open 修复）

`[PROD_NOT_TOUCHED]`

本批 = 4 个子批中第 1 批（串行 dispatch_plan），仅修复 `agate/scripts/check-gate.py` 未知阶段
（`handlers.get(phase) is None`）分支的 fail-open 问题。子批 B（非数字阶段名回退检测）/ 子批 C
（`gate_p4` 完整度判据放宽）/ 子批 D（`check-judge-verdict.py` 白名单）均不在本批范围内，未改动。

## 改动清单

### 修改文件

| 文件 | 改动点 |
|---|---|
| `agate/scripts/check-gate.py` | `main()` 第 1489 行 `sys.exit(2)` → `sys.exit(1)`（`handlers.get(phase) is None` 分支，即真正未知的阶段名不再复用 P8 等已知阶段的"通过"退出码 2，改为 fail-closed 的 1）。stderr 文案 `f"未知阶段: {phase}\n"`（第 1488 行）未改，本就含阶段名文本，满足 BDD-1 断言。改动范围精确 1 行，未触碰 `handlers` 字典本身、`gate_p4` 或回退检测逻辑（`git diff` 确认加减各 1 行）。 |
| `agate/tests/unit/test_check_gate.py` | 存量用例 `test_other_unknown_phase_exit_2`（第 199-204 行）更名为 `test_other_unknown_phase_exit_1`，断言值 `returncode == 2` → `== 1`（见下「关联 BDD」矛盾核实与主 Agent 确认记录）。仅改这一处，未动该测试之外的任何断言。 |

无新增文件。

## 关联 BDD

- **BDD-1**（`test_tag0035_bdd_1_unknown_phase_fail_closed_exit_1`）：构造未知阶段 `P99`，断言 `exit==1` 且 stderr 含阶段名 `P99`。改动前红（exit=2），改动后绿。
- **BDD-2**（`test_tag0035_bdd_2_ci_backstop_exit_code_comparison_unaffected`）：验证 `ci-gate-backstop.py` 的"记录值==重跑值"纯相等比对逻辑不因退出码语义变化（2→1）而报错——`.gate-result.json` 记录 `exit_code=1` 时，backstop 判定 PASS（exit 0）。未改动 `ci-gate-backstop.py`（P1 已核实其只做相等比较，不特判具体数值）。改动前红，改动后绿。
- **BDD-3**（`test_tag0035_bdd_3_known_phase_not_routed_to_unknown_path`，10 个已知阶段参数化）：回归不变性——P0/P1/P2/P3/P4/P5/P6/P6.5/P7/P8 均不应被判定为"未知阶段"。改动前后均为绿（未受影响）。

## 自测结果

- 目标测试单独跑（`timeout 60 python3 -m pytest agate/tests/unit/test_check_gate.py -k "tag0035_bdd_1 or tag0035_bdd_2 or tag0035_bdd_3" -q`）：**13 passed**（BDD-1 ×1 + BDD-2 ×1 + BDD-3 参数化 ×10 + BDD-3 相关 1 例 = 13，均绿）。
- 全量跑第一次（改动前状态核对，`timeout 90 python3 -m pytest agate/tests/unit/test_check_gate.py -q`）：205 passed, 5 failed。其中 `test_other_unknown_phase_exit_2`（第 199-204 行，TAG0035 之前已存在的旧用例）断言未知阶段 `P9` 应 `exit==2`，与本批新增的 BDD-1（同一场景应 `exit==1`）语义矛盾。经与主 Agent 确认：该矛盾判定明确，非业务分歧——这条存量用例断言的正是 BDD-1（P1-requirements.md 既定验收标准）要修复掉的旧行为，字面过时，需同步更新，不构成 `[BASELINE_CHANGE]`。已按主 Agent 指示同步修正：`test_other_unknown_phase_exit_2` 更名为 `test_other_unknown_phase_exit_1`，断言值 `2`→`1`（加注释说明来由），未改动该测试之外的任何内容。
- 全量跑第二次（修正后，`timeout 90 python3 -m pytest agate/tests/unit/test_check_gate.py -q`）：**206 passed, 4 failed**。剩余 4 个失败均为本批范围外的预期红：
  - `test_tag0035_bdd_4_retreat_detection_non_numeric_phase_fail_closed`（2 个参数化子用例）：**子批 B** 范围（非数字阶段名回退检测），本批未实现。
  - `test_tag0035_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md` / `test_tag0035_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md`：**子批 C** 范围（`gate_p4` 完整度判据放宽），本批未实现。

## 验证

```
git diff agate/scripts/check-gate.py
```
确认改动仅 1 行（加 1 行减 1 行），未触及 `handlers` 字典及其他分支。
