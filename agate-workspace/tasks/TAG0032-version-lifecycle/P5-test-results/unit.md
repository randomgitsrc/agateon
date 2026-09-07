---
phase: P5
task_id: TAG0032
parent: P4-implementation.md
trace_id: TAG0032-P5-20260907
agent: verifier
type: verification
status: draft
created: '2026-09-07'
---

# P5 技术验证结果 — TAG0032 版本管理生命周期可用性批

- 验证模式：只读技术验证（不改代码/测试/文档、不"顺手修复"、不 git 写操作、不启动任何环境）
- 执行目录：`/home/kity/oclab/agateon/.worktrees/agate-TAG0032`（worktree 根，HEAD `1d9a32226c7aadfb7b77c413c8fedf7b93f95fd0` = P4 实现 commit）
- 主 checkout `/home/kity/oclab/agateon` 未触碰 → `[PROD_NOT_TOUCHED]`
- 不可逆操作：无（纯脚本 + 文档 + 隔离 HOME fixture 测试）→ `[NO_NEED_CONFIRM]`
- 执行方式：P2-design §6 `gate_commands.P5*` 五键逐条独立执行（每条独立 bash 调用，无 `&&` 链）；外层 `timeout`（pytest 600s / consistency 120s / shellcheck + count-tests 60s）
- 环境：涉安装路径用例靠测试自身隔离 HOME fixture，未动真实 `~/.agate`

## failed 计数

- **failed = 1**（其中**预存失败 1**，新增失败 0）
- 预存失败：`agate/tests/unit/test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent`
  —— `-n auto` 并行 flaky，与本次改动无关，P1 基线口径已由 TAG0030 review 记录；已登记
  `agate-workspace/tasks/TAG0032-version-lifecycle/known-failures.md`

## 命令结果总览（各 gate_commands.P5 key 的 exit code）

| key | 命令 | exit code | 判定 |
|-----|------|-----------|------|
| P5 | `python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto` | run1=**1** / run2=**0** / run3=**1** | flaky（预存 flaky 1，非新增） |
| P5_consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 通过（0 ERROR / 329 WARNING） |
| P5_shellcheck | `shellcheck -S warning agate/scripts/*.sh` | **0** | 通过 |
| P5_shellcheck_root | `shellcheck -S warning install.sh` | **0** | 通过 |
| P5_counttests | `bash agate/tests/scripts/count-tests.sh` | **0** | 通过（1508 用例，≥749 基线，无漂移） |

汇总：P5_consistency / P5_shellcheck / P5_shellcheck_root / P5_counttests 4/4 exit 0；P5 pytest
仅 1 条预存并行 flaky（隔离单跑必过、全量重跑 run2 全绿），无新增失败、无回归。

---

## 1. P5 — 全量 pytest（unit + regression + integration，-n auto）

- 命令：`python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto`（外层 `timeout 600s`）
- 全量口径（非仅本任务用例）
- 三次实跑 + 一次隔离单跑：

| 轮次 | 结果 | exit |
|------|------|------|
| run1 | `1 failed, 1483 passed, 2 skipped in 35.78s` | 1 |
| run2 | `1484 passed, 2 skipped in 37.53s` | 0 |
| run3 | `1 failed, 1483 passed, 2 skipped in 36.83s` | 1 |
| 隔离单跑 `test_nc_cross_checkout_paths_hash_consistent` | `1 passed in 0.83s` | 0 |

run1 / run3 短摘要（原样）：

```
=========================== short test summary info ============================
FAILED agate/tests/unit/test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent
1 failed, 1483 passed, 2 skipped in 36.83s
```

run2 尾行（原样）：

```
1484 passed, 2 skipped in 37.53s
```

### 预存失败分析

- **三振记录**：FAIL / PASS / FAIL；隔离单跑 PASS → 判定 flaky（`-n auto` 并行 worker 间干扰）
- **既有记录**：`test_agate_next_card.py` 系列并行 flaky 已在
  `docs/reviews/agate-alignment-review-20260904-TAG0030.md:112` 与
  `docs/reviews/agate-alignment-20260904-TAG0030-01.progress.md` 记录为「next_card 并行干扰 flaky
  （单跑/全文件重跑通过），非回归」，同族用例 `test_nc_byte_stability_two_calls_sha256_equal`
- **相关性**：TAG0032 diff（`3f3cc01..1d9a322`）改动清单 = `agate/scripts/agate-install.py`、
  `agate/scripts/agate_common.py`、`agate/SETUP.md`、`agate/UPGRADING.md` + 新增 5 个测试文件
  （`test_agate_version_install.py` / `test_agate_version_resolve.py` / `test_hook_resolve_entry.py`
  / `test_upgrading_lifecycle.py` / `test_version_lifecycle_e2e.py`）——**完全不触碰
  `agate-next-card.py` 及其测试文件** → 与本次改动无关
- 处理：标注为预存失败 + 登记 `known-failures.md`，不擅自标 ✅；不阻断门槛（由主 Agent 区分）
- 原始输出落盘：`P5-test-results/unit.raw.log`（run1）/ `unit.rerun2.log` / `unit.rerun3.log`（各末行 `EXIT_CODE: <n>`）

## 2. P5_consistency — 协议一致性（worktree 自己的脚本）

- 命令：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（外层 `timeout 120s`）
- exit code：**0**
- 结果：`仅有 329 个 WARNING，无 ERROR。`（与基线一致，均既有叙事文件引用；`--strict-errors-only` 只按 ERROR 判失败）
- 落盘：`P5-test-results/consistency.log`（末行 `EXIT_CODE: 0`）

## 3. P5_shellcheck — agate/scripts/*.sh

- 命令：`shellcheck -S warning agate/scripts/*.sh`（外层 `timeout 60s`）
- exit code：**0**（无 warning/error 输出）
- 落盘：`P5-test-results/shellcheck.log`

## 4. P5_shellcheck_root — install.sh

- 命令：`shellcheck -S warning install.sh`（外层 `timeout 60s`）
- exit code：**0**（无 warning/error 输出）
- 落盘：`P5-test-results/shellcheck.log`（同文件，含两条 EXIT_CODE 行）

## 5. P5_counttests — 用例数自检

- 命令：`bash agate/tests/scripts/count-tests.sh`（外层 `timeout 60s`）
- exit code：**0**
- 输出（原样关键行）：

```
=== pytest 用例覆盖度自检 ===
总计：1508 个测试用例（pytest collect-only 口径）
目标：≥ 749（TAG0011 迁移基线，BDD-1）；迁移期数值单调逼近 749。
```

- 无漂移告警；≥ 749 基线
- TAG0032 相关 5 个测试文件单跑复核：`43 passed in 5.87s`（只增不减）
- 落盘：`P5-test-results/counttests.log`（末行 `EXIT_CODE: 0`）

---

## test runner 输出签名行（主 Agent N5 校验用；`grep -cE '^(PASSED|FAILED|passed|failed)'` 计数须 >0）

FAILED agate/tests/unit/test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent
failed 1 (预存 flaky, 非新增)
passed 1484 (run2 全绿口径) / 1483 (run1·run3, 1 flaky)
passed 43 (TAG0032 相关 5 文件单跑)
passed 1508 collect-only (count-tests.sh)

## 门槛结论（verifier 视角，非 gate 判定）

- gate_commands.P5* 五条命令全部跑完，各有 exit code 记录 + 原始输出落盘
- failed=1，全部为预存并行 flaky（`test_nc_cross_checkout_paths_hash_consistent`），与 TAG0032 改动无关，已登记 known-failures.md
- 新增失败 = 0；P5_consistency / P5_shellcheck / P5_shellcheck_root / P5_counttests 全 exit 0
- 是否放行（预存 flaky 不阻断 vs 视为环境问题）由主 Agent 判定；本报告不声称「P6 已过」「验收通过」
