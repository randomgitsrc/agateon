---
phase: P2
date: 2026-10-05
trigger: review_rejected + gate_warning
---

# P2 评审打回诊断（retry #1）

## 补充（retry #1 复审通过后，主 Agent 跑 gate 发现的第 2 个问题）

**G1（gate WARNING + 会致 P3/P5 exit 127）**：`gate_commands` 用裸 `python` 与 `ruff`，
两者均不在当前环境 PATH（实测 `which python` 空、`which ruff` 空）。
- 实测：`/usr/bin/python3` 存在；`~/.venvs/agate-dev/bin/ruff` 存在（ruff 0.16.4，与 CI 锁版一致，AGENTS.md:162）。
- 后果：T075 教训——命令不存在 → P3/P5 gate exit 127，实现阶段假失败。
- 既有先例：TAG0036/0037 的 gate_commands 用 `python3 -m pytest ...`。
- 路由：**退回 P2 architect 修 gate_commands**（同阶段重试 #1 的一部分，review 已 approved 但 gate_commands 须可执行）。
- 修复方向：`python` → `python3`；`ruff` → `~/.venvs/agate-dev/bin/ruff`（或经 `AGATE_PYTHON`/probe 口径给出实际可执行路径）。

- 评审结果：plan-eng-review `status: rejected`；阻塞问题 1 个（B1）+ 非阻塞 4 个（N1-N4）+ 测试缺口 6 条（T1-T6）

## B1（阻塞）— tests_filter 全部指向不存在的测试文件，批级绿灯契约不可执行

- 现象：§6.1b 声明的 6 条 `tests_filter` 引用 10 个测试文件，实测全部不存在（pytest exit 4 = usage error，非测试红）。
- 根因：设计把「P3 未来才产出的测试文件」写成了「现在就能跑的绿灯命令」——语义混淆。batch1（tracer bullet）改既有 `agate-next.py`，既有测试已存在（`test_agate_next_card.py` / `test_tag0027_b1_agate_next_cli.py` / `test_check_state_transition.py`），却被错写成不存在的 `test_agate_next.py` / `test_state_transition.py`（漏 `check_` 前缀）。
- 路由：**退回 P2 architect 修订**（同一阶段内重试，非跨阶段回退）。
- 修复方向（采纳 review 方案 1，推荐）：§6.1b 增列「测试文件为 P3 计划产出」显式声明；batch1 的 tests_filter 改为既有真实文件名使 tracer bullet 当下可跑；batch2-6 标注「P3 产出后生效」。

## 非阻塞（本轮一并修，避免下轮再打回）

- **N1**：`parallel_limit` frontmatter（6）与 §6 正文（3）双值矛盾 → 统一（建议 3，与 dispatch-protocol「并行上限默认 3」一致，除非有隔离依据支持 6）。
- **N2**：gate_p0 返回值吸收 `validate` 退出码的口径须写清（迁移期 validate 非 0 但 gate_p0 仍返回 2）。
- **N3**：解释器口径两处不一致（裸 `python3` vs `AGATE_PYTHON`/probe）。
- **N4**：锚点 keywords 未定。

## 测试缺口（转 P3 输入）

- T1（阻塞关联）：批级绿灯命令不可执行 → 按 B1 修正。
- T2：BDD-8「文件缺失 → 行为与现状一致」负向用例未落具体断言。
- T3：N2 的 gate_p0 吸收 validate 退出码缺用例。
- T4：`cmd_run` 事件字段 schema 未定义。
- T5：BDD-20/R6 差分「新转红/告警面可解释」判据是人工判读 → P8 逐条列出。
- T6：平台分支（m-2/BDD-9）Windows 真机不可得，属已声明环境约束 → P3 按平台分支断言 + 模拟环境覆盖。
