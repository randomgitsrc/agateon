read dispatch-context start
read dispatch-context+role done; next P2 sec2/P1 rules
read P2 §2, P1 kouji A-H, BDD 13-58; next test file
read test file; next agate_common/style ref
M18 done (GATE_SCRIPT_EXEMPT +1); writing check-mvwu.py
wrote check-mvwu.py; running self-check tests
test_check_mvwu 109 passed; running other self-checks
ruff fixed; rerun tests
P4-implementation.md written; batch done
[batch-evidence-landing] M6/M7 完成：P4 卡新增 P4-evidence 节；task-files 登记行 + tests_filter 注释；BDD-10/11/12 用例绿，无 DESIGN_GAP/SCOPE+
[review-anchors-and-decision-recheck] M8/M9/M10 完成；BDD-66 P2 卡侧（decisions/ 落点、既有决策读取）不在本批，由 P2 卡所属批负责。无 DESIGN_GAP / SCOPE+。
[architect-batch-guidance] M2/M3/M4(P2卡)+M5(architect.md) 已落地；BDD-6/7/8/9/61-64/66 对应用例转绿；无 SCOPE+/DESIGN_GAP
[mvwu-script-registry] M13/M14/M15 完成；BDD-69 三用例绿；count-tests=1842
[mvwu-glossary-and-debt-log] M11(CONTEXT.md +5 行)与 M12(DEBT0043)完成；BDD-5/59 相关用例转绿；无 DESIGN_GAP / SCOPE+；[PROD_NOT_TOUCHED]
[testfix] test_mvwu_protocol_docs.py:11 注释措辞改为"不依赖固定临时目录路径字面量"，消除 R4 命中（仅注释）
[fixes] MAJOR: DURATION_RE 限长 {1,15}、_fmt_duration try/except、观察表输出循环 per-row 兜底(UNKNOWN 行+stderr internal error)；新增 test_bdd_45_observe_huge_duration_does_not_drop_rows 2 参数化：修前红(2 failed，输出2行)→修后绿；CONTEXT.md boundary(I1) 补句；tests/README check-mvwu 109→111；自查 192 passed、ruff/ast/consistency 0 ERROR（非 P5 gate）
