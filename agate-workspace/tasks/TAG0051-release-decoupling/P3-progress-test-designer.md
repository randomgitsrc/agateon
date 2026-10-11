
## P3 test-designer 进度（TAG0051）
- [start] 已读角色定义 test-designer.md（v0.81.0）+ P3-dispatch-context-test-designer.md（含 dispatch_guide 强制指令 + P3 卡片）。
- 关键约束记录：①红灯须 B 类（禁止 import 未存在符号，用 subprocess）；②平台假设扫描 0 命中（注释字面量也算）；③test_code_dir=agate/tests/unit/；④23 条 BDD 1:1 映射；⑤NB-6..NB-9 须体现；⑥BDD-16/17 需 level-2 夹具。
- [read] P1-requirements.md（23 BDD，1:1 映射来源）+ P2-design.md（方案/§9 覆盖映射/8 批 tests_filter）+ P2-review.md（approved，NB-6..NB-9 须体现）。下一步：读 P0-brief + conftest + 既有同类测试。
- [read] P0-brief.md；conftest.py（python_exe/run_cli/git_repo/agate_scripts fixtures）；既有同类测试 test_release_workflow.py / test_check_p8_delivery.py / test_check_changelog.py / test_tag0050_obligations_enforcement.py / test_selfgate_trailer_integrity.py；helpers_tag0050.py / helpers_tag_repo.py；check-gate.py gate_p8 + _check_roadmap_done + _delivery_spec；agate-release.py argparse；release.yml；r6-differential.sh；level-1.yaml/LEVELS.yaml；fixtures/task-data/level-1；commit-msg-self-gate.py 触发面；check-platform-assumptions.py 规则（R1 PATH=/usr|/bin；R2 裸 python3；R4 /tmp 字面量；R6 subprocess text 缺 encoding=）。
- [plan] 8 个测试文件：p8_gate（BDD-2/3/4/5/6/7/19）、docs_consistency（BDD-1/14/15）、state_machine（BDD-18）、delivery_contract（BDD-16/17）、obligations_sync（BDD-21）、r6_harness（BDD-20）、release_gate（BDD-8/9/10/11/12/13/23）、self_gate（BDD-22）。+ level-2 黄金 fixture。
- [write] agate/tests/unit/test_tag0051_p8_gate.py（BDD-2/3/4/5/6/7/19）。下一步：自跑该文件确认真红灯为 B 类（预计 <20s）。
- [write] agate/tests/unit/test_tag0051_docs_consistency.py（BDD-1/14/15）。下一步：自跑（预计 <10s）。
- [write] test_tag0051_state_machine.py（BDD-18）+ test_tag0051_delivery_contract.py（BDD-16/17）+ 新增 level-2 黄金 fixture（pass/fail 账本）。下一步：自跑 delivery+state_machine（预计 <20s）。
- [write] obligations_sync / r6_harness / release_gate / self_gate 四文件。下一步：自跑这批 + 平台假设扫描（预计 <60s）。
- [self-check] 平台假设扫描 + ruff。下一步：python3 /home/kity/.agate/v0.81.0/agate/scripts/check-platform-assumptions.py agate/tests/unit/ 与 ruff check（预计 <60s）。
- [self-check] ruff 修 1 处 PLW2901 → 全绿；平台假设扫描 0 命中。下一步：全量新用例一起跑 + consistency（确认新增 fixture 不引入 ERROR）+ 相关回归（预计 <180s）。
- [write] P3-test-cases.md（含 test_code_dir + 23 BDD 映射 + NB-6..NB-9 + 可测接缝）。下一步：最终自检三项（平台扫描 / B类红灯 / BDD 覆盖）（预计 <120s）。
- [self-check ①] check-platform-assumptions.py agate/tests/unit/ → 0 命中（exit=0）。
- [self-check ②] 8 新文件自跑 → 26 failed / 10 passed（exit=1）；A类 token（Traceback/SyntaxError/ImportError/ModuleNotFoundError）命中 0 → 红灯均 B 类。
- [self-check ③] BDD-1..23 每条均有测试名引用该编号（23/23）。
- [status] 产出：P3-test-cases.md（test_code_dir=agate/tests/unit/）+ 8 测试文件 + level-2 黄金 fixture。git status 仅新增测试/夹具/任务文档，未改任何协议/脚本/CI 文件。[PROD_NOT_TOUCHED]

## P3 test-designer 修复轮（retry 1，修测试自身 bug）
- [read] 角色定义 + P3-dispatch-context-test-designer-retry1.md。定位 2 处测试代码缺陷（非实现缺口）：
  ① `test_tag0051_obligations_sync.py::_obligations()` 顶层按列表假设 ⇒ 恒 0 条（实为 dict，列表在 `data["obligations"]`，
     与 check-obligations.py:258 同源口径）；② `test_release_gate.py` 用 `H.GENESIS_HASH`（helpers_tag_repo 无此常量，在 helpers_tag0050）。
- [fix] ① 取 `data["obligations"]`（最小改，仅列表来源）；② 增 `import helpers_tag0050 as H5` 并把该处 `H.GENESIS_HASH` → `H5.GENESIS_HASH`。未改任何断言语义、未改实现、未改 P1/P2 基线。
- [self-check ①] 8 文件自跑 → **1 failed / 35 passed**（修复前 8F/28P）。唯一红 = `test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review`：
  归因为「**实现缺口 / 设计性必红**」——BDD-22 要求改 `agate/` 的提交带 `self-gate-review:` 留痕，而该提交（P4 产出）尚未发生，断言 `prot == []` 成立即红。非测试 bug。
- [self-check ② 同类扫描] H/H5 全部属性引用已核对：`H.REPO_ROOT`/`H.run_git`（helpers_tag_repo 均导出）、`H5.GENESIS_HASH`（helpers_tag0050 导出）——无引用不存在的 helper。唯一 `parents[2]`（obligations_sync）解析到 `agate/`，层级正确；yaml.safe_load 另一处在 release_gate（release.yml 顶层映射，配合 `doc.get(True, doc.get("on"))` 处理 YAML1.1 `on`→True，语义正确）。无其它同族缺陷。
- [self-check ③] check-platform-assumptions.py agate/tests/unit/ → exit 0（0 命中）；ruff 两文件 → All checks passed。
- [status] 改动面：仅 2 文件（test_tag0051_obligations_sync.py +8/-1、test_release_gate.py +3/-1）。[PROD_NOT_TOUCHED]
