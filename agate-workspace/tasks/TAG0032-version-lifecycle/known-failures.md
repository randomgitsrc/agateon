---
task_id: TAG0032
generated_by: verifier
---
# 已知失败登记

> **语义边界**：本文件只登记**预存失败**（P5 之前就存在的、与当前任务无关的失败）。
> 当前任务引入的失败用 P5-test-results/ 记录，不写本文件。

## 预存失败（非本任务引入）

| # | 测试文件 | 失败数 | 根因 | 与本任务相关 | 处理计划 |
|---|---------|--------|------|-------------|---------|
| 1 | `agate/tests/unit/test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent` | 1（flaky，非稳定复现） | `test_agate_next_card.py` 系列在 `-n auto` 并行下的 worker 间干扰 flaky（隔离单跑必过；同族既有记录 `test_nc_byte_stability_two_calls_sha256_equal`）。P5 三振：run1 FAIL / run2 PASS / run3 FAIL。已在 `docs/reviews/agate-alignment-review-20260904-TAG0030.md:112` 与 `docs/reviews/agate-alignment-20260904-TAG0030-01.progress.md` 记录为并行 flaky，非回归 | 否（TAG0032 diff `3f3cc01..1d9a322` 只改 agate-install.py / agate_common.py / SETUP.md / UPGRADING.md + 新增 5 个版本生命周期测试文件，完全不触碰 `agate-next-card.py` 及其测试） | 推迟（历史既有 flaky，主 Agent 判定修复成本 vs 推迟成本；根治需 next-card 测试并行隔离加固，超出本任务范围） |
