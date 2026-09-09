
## P3-progress — test-designer (session_014jKy7LxVHNa1uwrMxuZ1Mz)

### 输入读取完成 (2026-09-09)
- test-designer.md 角色定义 / P3-dispatch-context / AGENTS.md / P0-brief / P1-requirements (53 BDD) / P2-design (§0-§11) / P2-review (T1/T2/T3 + 8 锁定决策) — 全部读毕
- 既有对照物读毕: conftest.py (fixtures: task_dir/run_cli/python_exe/agate_scripts/agate_root) / test_check_events.py (_write_ledger 哈希链范式) / check-events.py (7 条审计链, 第 7 条未知 event 不拦) / test_tag0030_assertions.py (doc-assertion grep 范式) / agate-dispatch.py (main() 从 phase=args[0] + _PHASES 校验起, 无 route 子命令)

### 红灯锚点确认 (目标物均不存在)
- agate/scripts/check-dispatch-routing.py — 不存在 (subprocess → rc 2)
- agate/rules/dispatch-tiers.yaml — 不存在
- agate-workspace/dispatch-routing.yaml — 不存在
- agate-dispatch.py 无 route 子命令 (phase='route' → _PHASES 校验 exit 1)
- check-events.py 无第 8 条 dispatch_route 理由码校验 (grep 'dispatch_route' check-events.py → 0)
- design-note: 仍含 "按序探测" / "rules/dispatch-routing.yaml", 无 "try-and-fall" / "弱缓解" / "per-machine"
- dispatch-protocol.md: 无 "派发路由" 子节 / 无 "不认谁生产的" / 无 "author 文档内容 vs 一致性验证"
- architect.md 批次设计节: 无 "补协议文档正文 = P4"
- roadmap RM-AG0060 行: 仍含 "按序探测" + "rules/dispatch-routing.yaml"

### 测试接口契约 (P4 须提供)
- importable 模块 agate/scripts/agate_dispatch_route.py 暴露:
  - resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model) -> {"form","chain","model","effort"}
  - load_config(workspace_dir) -> (routes, tier_bindings)  全兜底
  - classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None) -> Outcome(.kind,.reason)
  - build_dispatch_command(candidate, *, ctx_path, effort_supported) -> list[str]
- check-dispatch-routing.py (schema 校验器, CLI: <yaml路径>, exit 0/1)
- check-events.py 第 8 条 (dispatch_route reason ∈ {launch_fail,infra_error,no_parseable_output})

### 测试文件落盘完成 (10 文件 + 4 组 fixture)
unit/: test_tag0034_{schema,resolve,tryfall,events,native,subprocess,tmux,interaction,docs}.py
regression/: test_tag0034_zero_change.py
fixtures/: tag0034_regression_baseline.json + tag0034_{claude_code,codex,opencode}/ 静态样本
  (从 scratchpad mv/ 收敛: mv1/mv10 → claude_code; mv2/mv3/mv4 → codex; mv5/mv6a/mv6b → opencode)

### 自跑确认 (2026-09-09)
- `python3 -m pytest agate/tests/ -k tag0034 -q`：**59 failed, 1 passed, 1537 deselected in 2.44s**
  - 1 passed = test_bdd_39 (回归护栏基线 hash，P3 绿属预期，已在 P3-test-cases.md 显式标注)
  - 59 failed 红灯类型分布：
    * ModuleNotFoundError: No module named 'agate_dispatch_route' —— B 类 (项目内模块 agate_* 未实现)：resolve/tryfall/native/subprocess/tmux/interaction 功能面 + BDD-29/40(a) 共约 40 条
    * subprocess check-dispatch-routing.py 返回码 2 (脚本不存在) —— B 类：schema BDD-1~6 (assert 2 == 0/1)
    * check-events.py 第 8 条未实现 —— B 类：BDD-27 (assert 0 == 1) / T3 (gate_fail 应 exit 1) / BDD-30 (grep 'dispatch_route' 源码 0 命中)
    * doc-assertion AssertionError (措辞未写入) —— BDD-41/45(doc)/46/47/48/49/51(doc)/52/53 + BDD-10 platform-notes
    * BDD-50: check-protocol-consistency --strict-errors-only exit 1 (见 [P2_DESIGN_YAML_FENCE])
  - 无 collection error / 无 A 类 (SyntaxError / 第三方 import 失败 / 断言与 fixture 自相矛盾)
- `python3 -m pytest agate/tests/ -q --tb=no` 全量：**64 failed, 1531 passed, 2 skipped in 166.97s**
  - 64 failed 全部为 test_tag0034_* (60 用例中 59 红 + docs/regression 子集核对一致；full-run 计数含 xdist 分片重复计，逐 id 去重 = 60 用例 59 红 1 绿)
  - 既有 1531 passed 未因新增文件变红 / collection error（下方 not-tag0034 全量二次确认）

### [P2_DESIGN_YAML_FENCE] —— P3 发现，报主 Agent
worktree 当前 HEAD (b851b1e) 跑 check-protocol-consistency.py --strict-errors-only 即 exit 1：
  ❌ YAML 代码块无法解析: mapping values are not allowed here [P2-design.md:364]
= P2-design.md §4.1 dispatch_plan 多行 flow ```yaml 代码块 (P2 产出、已 commit)。
与本 test-designer 新增文件无关 (新增前后同样 exit 1)。
影响 BDD-50 P3 红 (除 BDD-48/49 未就位外另叠加此既有 ERROR)。
建议主 Agent 决定 P4/P7 顺带修 (改单行 flow / ```text 围栏) 或登记独立 debt。
test-designer 不改 P2 产出 (P1 基线保护同理)。

### [PROD_NOT_TOUCHED]
仅在 worktree 内读 + 写 agate/tests/ (10 test 文件 + 4 组 fixture) + P3-test-cases.md + 本文件。
未触碰主 checkout /home/kity/oclab/agateon 与 ~/.agate。

### 卫生修正 (自跑二轮发现并修复)
全量 `-k "not tag0034"` 跑出 5 个非 tag0034 failed，逐个归因：
- **本 test-designer 引入 → 已修**：
  * `test_env_adapt_docs.py::test_bdd_34_...ruff` —— 我的文件 PLW2901（`for raw ...: raw = raw.strip()`）
    + C408/C416（`dict(...)` 调用 / dict 推导）。已改：zero_change.py 用 `stripped` 变量；
    events.py `dict(ev)`；resolve.py/interaction.py `dict(...)` → 字面量。`ruff check agate/` 现 All checks passed。
  * `test_check_platform_assumptions.py::test_bdd_8_clean_tree_zero_detection` —— 我的 native.py/tmux.py
    有 `/tmp/ctx.md` `/tmp/cap.log` 字面量（R4 硬编码 /tmp）。已改：`ctx/dispatch-context.md` /
    `cap/dispatch.log`。`check-platform-assumptions.py agate/tests` 现 exit 0 / 空输出。
  * 修复后二次单跑 `test_bdd_8` + `test_bdd_34` → **2 passed**。
  * 附带把 `try_and_fall` 契约签名补 `dispatch_context_path` 入参（BDD-19 ctx 断言需要），
    P3-test-cases.md 契约表同步。
- **既有失败（非本 test-designer 引入，worktree HEAD b851b1e 即红）**：
  * `test_consistency.py::test_con_1_check_1_yaml_parseable` —— `ERROR (` = P2-design.md:364 fence
  * `test_env_adapt_docs.py::test_bdd_25_consistency_zero_error` —— 同 P2-design.md:364 fence
  * `test_tag0027_b1_phases_transfer_fields.py::test_bdd_5_consistency_worktree_still_green_regression` —— 同
  → 3 条均 `[P2_DESIGN_YAML_FENCE]` 根因，见上节。与本 test-designer 新增文件无关。

### 最终自跑 (卫生修正后)
- `pytest agate/tests/ -k tag0034 -q`：**59 failed, 1 passed**（1 passed = BDD-39 回归护栏，预期）
- `ruff check agate/`：All checks passed
- `check-platform-assumptions.py agate/tests`：exit 0，空输出
- 全量 `pytest agate/tests/ -q --tb=no`：见下方 bjcyqm922 结果（非 tag0034 侧只余 3 条既有
  consistency 失败，均 P2-design.md:364 根因，非本次引入）

### 全量最终结果 (bjcyqm922)
`pytest agate/tests/ -q --tb=no` → **62 failed, 1533 passed, 2 skipped in 168s**
- 62 failed = 59 (tag0034 新用例，B 类 + doc-assertion + BDD-40 混合红) + 3 既有
- 既有 3 条失败全部 = `test_con_1_check_1_yaml_parseable` / `test_bdd_25_consistency_zero_error` /
  `test_bdd_5_consistency_worktree_still_green_regression` —— 同 `[P2_DESIGN_YAML_FENCE]` 根因
  （P2-design.md:364 fence，worktree HEAD b851b1e 即红，探索首跑 check-protocol-consistency 已复现），
  **非本 test-designer 新增文件引入**（卫生二轮修正后 `-k "not tag0034"` 侧只余这 3 条）
- BDD-39 = 唯一 tag0034 绿（回归护栏基线 hash，P3 绿属预期）

### 返回自检
- grep: 10 个 test_tag0034_*.py + regression 文件均落盘，含 `def test_bdd_NN_*` / `def test_tNN_*` 函数名共 60
- P3-test-cases.md 映射表: BDD-1~53 连续全覆盖 + T1/T2/T3；frontmatter `test_code_dir: agate/tests/`
- ruff check agate/ = All checks passed；check-platform-assumptions.py agate/tests = exit 0 空输出
