---
phase: P6
task_id: TAG0035
type: acceptance
parent: P5-verification.md
trace_id: TAG0035-P6-20260916
status: draft
created: 2026-09-16
agent: verifier
pass: 14
fail: 0
ui_affected: false
---
# P6-acceptance — TAG0035-gate-robustness

本任务无 UI（`domains: [backend]`，`ui_affected: false`），不涉及 vision-analyst / 截图证据。全部
14 条 BDD 均为本地 pytest 精确函数级验证（`pytest -k tag0035_bdd_N`）+ BDD-1 额外的独立手工 CLI
验证，均实跑得到客观结果后据实记录，未预判。

## 逐条 BDD 结果

### 子批 A：未知阶段 fail-closed

- PASS BDD-1: `check-gate.py` 收到未知阶段 `P99` 时退出码为 1（不再是 2），stderr 含阶段名文本"未知阶段: P99"；手工 CLI 复现 `python3 agate/scripts/check-gate.py P99 <task_dir>` 输出 `exit=1` (bdd-1-manual-cli.log, bdd-batch-a.log)
- PASS BDD-2: 新增 regression 测试 `test_tag0035_bdd_2_ci_backstop_exit_code_comparison_unaffected` 锁定未知阶段行为——断言 `check-gate.py` 对未知阶段恒 exit=1 且 stderr 含阶段名，同时断言 `ci-gate-backstop.py` 的"记录值==重跑值"比对逻辑本身不因退出码语义变化（2→1）而报错或异常，实跑 PASSED (bdd-batch-a.log)
- PASS BDD-3: 10 个已知阶段名（P0/P1/P2/P3/P4/P5/P6/P6.5/P7/P8）参数化用例 `test_tag0035_bdd_3_known_phase_not_routed_to_unknown_path` 全部 PASSED，已知阶段未被路由到"未知阶段"分支，行为与修复前一致；P1 原文验证命令要求的三分片全量测试（`agate/tests/unit/` + `regression/` + `integration/`，不加 `-k` 过滤）已独立重跑确认全绿（1507+31+96=1634 passed, 2 skipped, 0 failed，与 P5 基线一致） (bdd-batch-a.log, bdd-3-7-full-suite.log)

### 子批 B：非数字阶段名三处静默失效（最小案）

- PASS BDD-4: `test_tag0035_bdd_4_retreat_detection_non_numeric_phase_fail_closed` 两个参数化子场景（`old_phase_non_numeric` / `phase_non_numeric`）均 PASSED——`check-gate.py` 回退抵达检测对非数字阶段名（如 `p-alpha`）不再静默短路为"未发生回退"，而是 stderr 显式提示"无法解析"并 exit=1 (bdd-batch-b.log)
- PASS BDD-5: `test_tag0035_bdd_5_phase_num_non_numeric_fail_closed` 两个参数化子场景（`new_phase_non_numeric` / `old_phase_non_numeric`）均 PASSED——`check-state-transition.py` 的 `phase_num()` 对非数字阶段名不再静默 `return 0`，而是 stderr 提示"无法解析"且脚本以非零退出码终止 (bdd-batch-b.log)
- PASS BDD-6: `test_tag0035_bdd_6_pre_commit_nonstandard_phase_output_warns` PASSED——`pre-commit-gate.py` 对非常规（非 `P[0-8]-` 前缀）阶段名产出文件的一致性检查不再 0 输出地悄然跳过，stderr 产生可观测提示 (bdd-batch-b.log)
- PASS BDD-7: 三个子测试均 PASSED——`test_tag0035_bdd_7_check_gate_numeric_retreat_detection_not_regressed`（check-gate.py 回退检测对标准数字阶段名行为不回归）、`test_tag0035_bdd_7_state_transition_numeric_phase_not_regressed`（check-state-transition.py phase_num 对数字阶段名行为不回归）、`test_tag0035_bdd_7_pre_commit_standard_phase_output_no_extra_warning`（pre-commit-gate.py 对标准阶段名产出无额外 WARNING），三处判据修复对 P0-P8 标准数字阶段名行为完全一致；P1 原文验证命令要求的三分片全量测试（`agate/tests/unit/` + `regression/` + `integration/`，不加 `-k` 过滤）已独立重跑确认全绿（1507+31+96=1634 passed, 2 skipped, 0 failed，与 P5 基线一致） (bdd-batch-b.log, bdd-3-7-full-suite.log)

### 子批 C：DEBT0037（_gate_p4 完整度判据）

- PASS BDD-8: `test_tag0035_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md` PASSED——一个 P4 阶段跨多个 commit 交付、当前暂存区只含 md/yaml 但更早 commit 已引入过代码 diff 时，`_gate_p4` 不再仅凭当前暂存区快照误判 `return 1`（历史扫描覆盖该 phase 的历史提交） (bdd-batch-c.log)
- PASS BDD-9: `test_tag0035_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md` PASSED——`.state.yaml` `retries[P4]` 非空（P5→P4 回退）且已存在 `wf(TAG0035-P4)` commit 场景下，本次纯 md/yaml 修复 commit 不再被 `_gate_p4` 误判 `return 1` (bdd-batch-c.log)
- PASS BDD-10: `test_tag0035_bdd_10_gate_p4_pure_doc_no_history_still_blocks` PASSED（红灯边界）——纯文档、该 phase 此前既无代码 diff 历史、也不属于回退后修复场景时，`_gate_p4` 仍然 `return 1`，判据放宽未越界削弱既有拦截力 (bdd-batch-c.log)

### 子批 D：DEBT0038（check-judge-verdict.py 黑白名单假阳性）

- PASS BDD-11: `test_tag0035_bdd_11_blacklist_exempts_phase_card_path_reference` 两个参数化子场景（`p6-acceptance.md`→`agate/phase-cards/P6-acceptance.md`、`p4-implementation.md`→`agate/phase-cards/P4-implementation.md`）均 PASSED——`_check_blacklist` 不再仅凭 basename 子串命中协议阶段卡片路径引用，两个同构文件名实例均已验证豁免生效 (bdd-batch-d.log)
- PASS BDD-12: `test_tag0035_bdd_12_whitelist_role_definition_file_path` 两个参数化子场景（`agate/assets/execution-roles/analyst.md`、`agate/assets/review-roles/plan-eng-review.md`）均 PASSED——`_check_whitelist_outside` 不再把角色定义文件路径判为"白名单外任务产出路径引用" (bdd-batch-d.log)
- PASS BDD-13: `test_tag0035_bdd_13_p6_evidence_bare_filename_recognized` PASSED——`P6-evidence/` 目录下真实产物的裸文件名引用（不含 `P6-evidence/` 前缀）不再被误报"白名单外" (bdd-batch-d.log)
- PASS BDD-14: `test_tag0035_bdd_14_self_referential_p6_acceptance_still_blocked` PASSED（防御性红灯边界）——`dispatch-context-judge.md` 直接引用任务自己产出的 `P6-acceptance.md`（verifier 自述场景，真实信息隔离违规）时仍判定黑名单命中并 exit 1，BDD-11/12/13 的加固未连带放宽对真实自述场景的拦截 (bdd-batch-d.log)

## post-test 环境残留检查（强制步骤）

本任务测试均为本地文件系统操作（`pytest` 临时 fixture 目录由 pytest 自身清理）+ 本地 git 命令（临时 repo fixture），无外部资源创建（无数据库/服务/网络连接/端口占用），无残留。

## 汇总

**Summary**: 14/14 PASS, 0 FAIL

- 全部 14 条 BDD 逐条实跑 PASS，0 FAIL
- 证据组织：4 个批次日志文件（bdd-batch-a/b/c/d.log，每个含具体测试函数名 + PASSED 字样可辨识对应到每条 BDD）+ 1 个 BDD-1 独立手工 CLI 验证日志（bdd-1-manual-cli.log）+ 1 个 BDD-3/BDD-7 三分片全量测试独立重跑日志（bdd-3-7-full-suite.log，不加 `-k` 过滤，1634 passed, 2 skipped, 0 failed）
- 未改动任何源代码，暂存区只含 `P6-evidence/` 下证据文件 + `P6-acceptance.md` 本身
- 与 P5-test-results/unit.md 记录的全量测试（1634 passed, 0 failed）一致，本阶段逐条 BDD 级独立验证未发现与 P4/P5 结论不符之处
