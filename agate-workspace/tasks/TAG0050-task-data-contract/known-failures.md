---
task_id: TAG0050
generated_by: verifier
---
# 已知失败登记

> **语义边界**：本文件只登记**预存失败**（P5 之前就存在的、与当前任务无关的失败）。
> 当前任务引入的失败用 P5-test-results/ 记录，不写本文件。

## 预存失败（非本任务引入）

| # | 测试文件 | 失败数 | 根因 | 与本任务相关 | 处理计划 |
|---|---------|--------|------|-------------|---------|
| 1 | `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` | 1 | 本机 opencode CLI 子命令漂移：测试断言 `opencode debug agent <name>`（单数），实际 CLI 为 `opencode debug agents`（复数，报 `Unknown subcommand "agent"`）。属本机环境漂移，与 TAG0050 改动无关（P3 已登记）。 | 否 | 推迟（本机环境问题，非协议缺陷） |

> 说明：P5 全量套件仅此 1 个失败，其余全绿（详见 `P5-test-results/unit.md`）。
