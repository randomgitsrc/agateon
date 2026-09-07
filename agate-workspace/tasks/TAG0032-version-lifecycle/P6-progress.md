# P6-progress — TAG0032 版本管理生命周期可用性批（验收进度）

phase=P6 / agent=verifier / trace_id=TAG0032-P6-20260907
[PROD_NOT_TOUCHED] [NO_NEED_CONFIRM]

- 已读 dispatch-context / verifier.md（模式二）/ P0-brief / P1 §3（14 BDD）/ P3 映射 / P4-impl / P5 unit.md / known-failures.md
- .state.yaml: phase=P5, p5_pass_commit=1d9a322, judge.enabled=true
- P6-evidence/ 已建，开始逐条实跑

- BDD-1: PASS (bdd-1-install-symlink.log, EXIT 0)
- BDD-2: PASS (bdd-2-migration-hint.log, EXIT 0)
- BDD-3: PASS (bdd-3-plain-dir.log, EXIT 0)
- BDD-4: PASS (bdd-4-root-scripts.log 判据1/2 EXIT 0, bdd-4-doc-semantics.log 判据3 EXIT 0)
- BDD-5: PASS (bdd-5-install-sh-versions.log EXIT 0; bdd-5-curl-bash-transcript.txt 隔离HOME真实 cat install.sh|bash -s -- --versions EXIT 0, ~/.agate 含 repo/+v0.50.0/+指针+scripts/, --help EXIT 0, 无源污染, 隔离HOME已清理)
- BDD-6: PASS (bdd-6-meta-resolve.log, EXIT 0)
- BDD-7: PASS (bdd-7-rootproto-resolve.log, EXIT 0)
- BDD-8: PASS (bdd-8-hook-gate-path.log, EXIT 0)
- BDD-9: 全量套件运行中...
- BDD-9: PASS (bdd-9-full-suite.log, 1484 passed 2 skipped, EXIT 0)
- BDD-10: PASS (bdd-10-update-aligned.log, EXIT 0)
- BDD-11: PASS (bdd-11-lifecycle-section.log, EXIT 0)
- BDD-12: PASS (bdd-12-doc-converged.log 4 参数化 EXIT 0, bdd-12-consistency.log EXIT 0 / 0 ERROR)
- BDD-13: PASS (bdd-13-e2e-lifecycle.log, EXIT 0)
- BDD-14: PASS (bdd-14-no-pollution.log, EXIT 0)
- post-test 残留检查: worktree git status 仅 P6 产出（gate-events.jsonl / P6-* / P6-evidence/），隔离 HOME 已清理，真实 ~/.agate 仍为 legacy 软链未触碰

## 预检结果（返回主 Agent 前）
- check-p6-format.py --fix → exit 0
- check-p6-evidence.py → exit 0（14 条 BDD，证据目录非空）
- check-p6-provenance.py → exit 1：审计 2 命中 P6-dispatch-context-verifier.md **第 77 行**
  （`- PASS 行格式：...`，位于 AGATE_CARD_START(L83) 之前、未被卡片剥离）——正则
  `^\s*- (PASS|FAIL)\b` 误判该「格式说明行」为验收结论预判。**非 P6-acceptance.md 缺陷、非实现缺陷**。
  只读验收不改 dispatch-context（主 Agent 输入 + provenance 审计对象）→ 返回主 Agent：
  需主 Agent 改写该行使卡片外无以 `- PASS `/`- FAIL ` 开头的行（如去掉行首 `- ` 或改措辞）。
- check-gate.py P6 → exit 2，正文 `证据目录非空，FAIL=0，NC=0，P6_TOTAL=14`
- 14 条 BDD 全部实跑 PASS；证据文件齐全含实质 pytest -v 输出。
