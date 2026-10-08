---
phase: P5
task_id: TAG0050
type: test-results
parent: P2-design.md
trace_id: TAG0050-P5-20261009
status: draft
created: 2026-10-09
agent: verifier
failed: 1
pre_existing_failed: 1
new_failed: 0
---

# TAG0050 P5 技术验证 — 全量 gate_commands 结果

> **验证对象**：HEAD `3b0bd755`（G3 已提交，P4 全部批次交付完成），协议 v0.79.0。
> **验证方式**：verifier subagent 从 `P2-design.md` §6 `gate_commands` 读取命令并逐条执行；只读验证，未改任何被验证文件，未 `git add/commit`。
> **环境**：python 3.12.3 / pytest 9.0.3 / xdist 3.8.0 / `pytest-rerunfailures` 可用 / ruff `~/.venvs/agate-dev/bin/ruff` / shellcheck `/usr/bin/shellcheck`。
> **环境隔离**：`[PROD_NOT_TOUCHED]` 本阶段仅在本 checkout 与 `/tmp/opencode` 干净 clone 上跑测试，未接触生产环境。

## 签名行（test runner 输出签名）

PASSED: 2863
FAILED: 1
passed=2863
failed=1
skipped=2

## P5 全量测试（分片 + `-n auto` + `--reruns 1`）

口径对齐 `agate/tests/README.md`：CI 复现口径 `python3 -m pytest agate/tests/ --reruns 1 -n auto`。按 AGENTS.md「测试约定」分片执行，各片单条命令上限 600s（实测单片 < 50s）。

| 片 | 命令 | exit | passed | failed | skipped | 说明 |
|---|---|---|---|---|---|---|
| unit | `python3 -m pytest agate/tests/unit/ -q --tb=no -n auto --reruns 1` | **1** | 2564 | 1 | 2 | 唯一失败 = 预存失败 `test_bdd_43`（见下）；`1 rerun` = R2.4 已知 flaky `test_arch_4` 重跑后通过 |
| regression | `python3 -m pytest agate/tests/regression/ -q --tb=no -n auto --reruns 1` | 0 | 81 | 0 | 0 | |
| integration | `python3 -m pytest agate/tests/integration/ -q --tb=no -n auto --reruns 1` | 0 | 196 | 0 | 0 | |
| sanity | `python3 -m pytest agate/tests/test_sanity.py -q --tb=no -n auto --reruns 1` | 0 | 6 | 0 | 0 | 框架自检 |
| scripts | `python3 -m pytest agate/tests/scripts/ -q --tb=no -n auto --reruns 1` | 0 | 16 | 0 | 0 | 平台假设扫描器行为测试 |
| **合计** | | **1**（仅预存失败） | **2863** | **1** | **2** | `--collect-only` = 2866，与合计一致 |

原始日志：`P5-test-results/_raw/{unit,regression,integration,sanity,scripts}.log`。

## 失败清单

`P5-test-results/fail-list.txt`：

```
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```

### 失败根因

- **预存失败：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（与本次改动无关，P3 已登记）**
  - 根因：本机 opencode CLI 子命令漂移。测试调用 `opencode debug agent orchestrator`（单数），本机 CLI 实际为 `opencode debug agents`（复数），返回 `ERROR Unknown subcommand "agent" for "opencode debug"`，rc=1 → 断言 `assert 1 == 0` 失败。
  - 判定：**环境漂移（本机 CLI 版本），非 TAG0050 引入的缺陷**。已登记 `known-failures.md`。
- **新增失败：0**（除上述预存失败外，全量套件无任何失败）。
- **flaky**：unit 片 `1 rerun` —— 即 `agate/tests/README.md` 已知风险 R2.4 的 `test_arch_4`（秒级时间戳撞名），重跑后通过，非本任务回归。

## 其余 gate_commands 结果

| key | 命令 | exit | 汇总输出 |
|---|---|---|---|
| `P5_consistency` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 0 ERROR；410 WARNING（全为冻结文件：CHECK1-yaml 2 / CHECK10-scriptref 1 / CHECK2-refs 407）。与 P2 基线（0 ERROR / 410 WARNING）一致 |
| `P5_structure` | `python3 agate/scripts/check-structure-consistency.py` | **0** | S0–S6 全 OK |
| `P5_shellcheck` | `shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh` | **0** | 无输出（无 warning/error） |
| `P5_ruff` | `~/.venvs/agate-dev/bin/ruff check agate/` | **0** | `All checks passed!` |
| `P5_platform` | `python3 agate/scripts/check-platform-assumptions.py` | **0** | 无违规输出 |
| `P5_count` | `bash agate/tests/scripts/count-tests.sh` | **0** | 2866 用例（`collect-only` 口径）；下界判据「≥ 749」未击穿 |
| `P5_fitness_snapshot_freeze` | `python3 -m pytest agate/tests/ -k task_data_freeze -q` | **0** | 1 passed, 2865 deselected |
| `P5_fitness_golden_fixture` | `python3 -m pytest agate/tests/ -k task_data_golden -q` | **0** | 1 passed, 2865 deselected |
| `P5_fitness_schema_single_source` | `python3 -m pytest agate/tests/ -k schema_single_source -q` | **0** | 1 passed, 2865 deselected |

原始日志：`P5-test-results/_raw/{consistency,structure,shellcheck,ruff,platform,count,fitness_freeze,fitness_golden,fitness_schema}.log`。

## P5_r6_differential（需干净树）

| 运行 | 命令 | exit | 汇总 |
|---|---|---|---|
| 活 checkout（字面 gate 命令） | `bash docs/design-notes/r6-differential.sh --corpus .` | **1** | `corpus 原仓库不干净`——唯一原因是 P5 阶段本进程产物未提交（`.state.yaml` M + `P5-dispatch-context-verifier.md` / `P5-progress.md` / `P5-test-results/` 未跟踪）。**非代码缺陷，是脚本的干净树自核验按设计拦截**；脚本在拦截点即退出，未运行差分、未产生写副作用 |
| 干净 clone（同 HEAD，等价干净树） | `bash docs/design-notes/r6-differential.sh --corpus .`（cwd=`/tmp/opencode/tag0050-r6-clean`，HEAD=`3b0bd755`，origin/main=`720c97d3`） | **0** | `before=720c97d3 after=<clone>/agate`；**legacy 任务 39 个，差异 0 条，未匹配 0 条**；运行后 clone `git status --porcelain` 为空（无写副作用） |

- 判定：R6 双向差分**实质通过**（差异 0，未匹配 0），与 P4 记录（legacy 39，差异 0，exit 0）一致。
- 说明：活 checkout 无法满足脚本「原仓库 `git status --porcelain` 为空」的自核验（P5 阶段必然存在未提交的阶段产物）。按 P4 既有做法（`P4-implementation.md:183`「在干净 clone 上跑」），改在 `git clone` 干净副本上执行同一条命令；两份运行均如实记录。
- 原始日志：`P5-test-results/_raw/r6_differential.log`。

## 预存失败与门槛

- **预存失败：1**（`test_bdd_43`，环境漂移，见上）；已登记 `known-failures.md`。
- **新增失败：0**。
- 除 `P5`（分片）因预存失败 exit 1 外，其余 gate key 全部 exit 0；`P5` 的 failed 计数全部归因于预存失败。
- 未运行项：无（`gate_commands` 全量 key 均已执行；本任务 `ui_affected: false`，无 `P5_e2e`）。
- `[NO_NEED_CONFIRM]` 本阶段无数据删除/迁移等不可逆操作，无待确认项。

## 判定小结

- P5 全量：passed=2863 / failed=1（全部为预存）/ skipped=2。
- 各 key exit code：`P5`=1（仅预存失败）、`P5_consistency`=0、`P5_structure`=0、`P5_shellcheck`=0、`P5_ruff`=0、`P5_platform`=0、`P5_count`=0、`P5_r6_differential`=1（活树干净核验拦截）/0（干净 clone）、`P5_fitness_snapshot_freeze`=0、`P5_fitness_golden_fixture`=0、`P5_fitness_schema_single_source`=0。
