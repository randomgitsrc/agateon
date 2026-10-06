---
task_id: TAG0042
generated_by: verifier
---
# 已知失败登记

> **语义边界**：本文件只登记**预存失败**（P5 之前就存在的、与当前任务无关的失败）。
> 当前任务引入的失败用 P5-test-results/ 记录，不写本文件。

## 预存失败（非本任务引入）

| # | 测试文件 | 失败数 | 根因 | 与本任务相关 | 处理计划 |
|---|---------|--------|------|-------------|---------|
| 1 | `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` | 1 | 外部 opencode CLI 已把 `debug agent <name>` 改为 `debug agents`（实测 `opencode debug agent orchestrator` → `Unknown subcommand "agent"`）；`SETUP.md`「OpenCode」节的验证命令随外部 CLI 漂移过期 | 否 | 推迟（建议单独 hotfix：更新 `agate/SETUP.md` OpenCode 节验证命令 + 该测试断言到当前 CLI；不在 TAG0042 范围） |
