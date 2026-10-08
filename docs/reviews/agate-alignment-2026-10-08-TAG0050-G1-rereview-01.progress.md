- start rereview; HEAD=b0a16c3a04368b4e806ac8acdcc5642b2a7a46a8; branch=feat/TAG0050-task-data-contract
- git status --porcelain:
 M .github/workflows/protocol-tests.yml
 M agate-workspace/tasks/TAG0050-task-data-contract/P3-test-cases.md
 M agate-workspace/tasks/TAG0050-task-data-contract/P4-progress.md
 M agate/UPGRADING.md
 M agate/WORKFLOW.md
 M agate/rules/obligations.yaml
 M agate/scripts/README.md
 M agate/scripts/agate-ci-verify.py
 M agate/scripts/agate-next.py
 M agate/scripts/agate-state-yaml-check.py
 M agate/scripts/check-obligations.py
 M agate/scripts/check-state-transition.py
 M agate/scripts/commit-msg-self-gate.py
 M agate/scripts/pre-commit-gate.py
 M agate/state-machine.md
 M agate/tests/README.md
 M agate/tests/integration/test_pre_commit_hook.py
 M agate/tests/integration/test_tag0050_a0_a1_ledger.py
 M agate/tests/integration/test_tag0050_ci_replay.py
 M agate/tests/integration/test_tag0050_state_set.py
 M agate/tests/unit/test_agate_ci_verify.py
 M agate/tests/unit/test_check_state_transition.py
 M agate/tests/unit/test_dispatch_context_warning.py
 M agate/tests/unit/test_tag0027_b1_agate_next_cli.py
 M agate/tests/unit/test_tag0050_obligations.py
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-implementer-A2.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-implementer-G1-fix.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-implementer-G1-test-fix.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-implementer-G1.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-protocol-alignment-review-G1-rereview.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-protocol-alignment-review-G1.md
?? agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G1.md
?? agate/scripts/agate-state-set.py
?? agate/tests/unit/test_tag0050_obligations_enforcement.py
?? docs/reviews/agate-alignment-2026-10-08-TAG0050-G1-01.progress.md
?? docs/reviews/agate-alignment-2026-10-08-TAG0050-G1-rereview-01.progress.md
?? docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1.md
- read P4-implementation-G1.md
 .github/workflows/protocol-tests.yml               |  24 +-
 .../TAG0050-task-data-contract/P3-test-cases.md    |   6 +
 .../TAG0050-task-data-contract/P4-progress.md      | 103 +++++
 agate/UPGRADING.md                                 |  81 ++++
 agate/WORKFLOW.md                                  |   2 +-
 agate/rules/obligations.yaml                       | 145 +++++-
 agate/scripts/README.md                            |   3 +-
 agate/scripts/agate-ci-verify.py                   | 513 ++++++++++++++++-----
 agate/scripts/agate-next.py                        |  28 +-
 agate/scripts/agate-state-yaml-check.py            |  22 +-
 agate/scripts/check-obligations.py                 | 238 ++++++++--
 agate/scripts/check-state-transition.py            | 297 ++++++------
 agate/scripts/commit-msg-self-gate.py              |   4 +
 agate/scripts/pre-commit-gate.py                   |  69 ++-
 agate/state-machine.md                             |  24 +-
 agate/tests/README.md                              |   5 +-
 agate/tests/integration/test_pre_commit_hook.py    |   8 +-
 .../tests/integration/test_tag0050_a0_a1_ledger.py |   3 +-
 agate/tests/integration/test_tag0050_ci_replay.py  |  36 ++
 agate/tests/integration/test_tag0050_state_set.py  |  34 ++
 agate/tests/unit/test_agate_ci_verify.py           |  28 +-
 agate/tests/unit/test_check_state_transition.py    |  50 ++
 agate/tests/unit/test_dispatch_context_warning.py  |   2 +-
 agate/tests/unit/test_tag0027_b1_agate_next_cli.py |  65 +--
 agate/tests/unit/test_tag0050_obligations.py       |  43 +-
 25 files changed, 1423 insertions(+), 410 deletions(-)
- F1: check-obligations.py rc=0 实测 EXIT=0（56/119 基线一致）；scope: protocol-repo 跳过 enforced_at/test 逻辑在 :282-287
- F2: 独立 scratch 真实 commit（/tmp/opencode）→ git show HEAD 账本含 gate_run + state_transition ✓；测试 test_gate_run_and_state_transition_committed_with_real_commit 1 passed
- F3: _strip_agate_card_blocks 落地（:64-84）+ 两向用例（test_check_state_transition.py 新增 2 个）
- F4/F7: agate-ci-verify.py docstring:21-26 + scripts/README.md:106 均降级为「未实现」；_resolve_protocol 不用 .agate-version ✓
- F5: agate-ci-verify.py:403-412 legacy PROD_TOUCHED 单独统计 + 测试 test_bdd_26b ✓
- F6: UPGRADING.md 新增未发布节 / WORKFLOW.md:369 / state-machine.md / protocol-tests.yml fetch-depth:0+--base 均改 ✓
- A4-3: test_bdd_42_negative_control_mutation 仍只读 YAML 文本（:70-77），无真变异；DESIGN_GAP 无 P7 REVIEWED-ACCEPTED（无 P7-consistency.md）
- A4-5: test_bdd_43 仍只断言文本含 review_output（:80-85）
- 新发现: platform-notes.md:342-344 / phase-cards/P3-tdd.md:28 / retrospective-template.md:144 / state-machine.md:154 仍称 agate-ci-verify '重跑 check-gate.py 判定'（A2 反向传播遗漏）
- 测试: 141 passed（ci_replay+state_set+obligations*+check_state_transition）；115 passed（pre_commit_hook+ci_verify+next_cli+dispatch_warning+ledger）；12 passed（state_yaml）
- consistency: 0 ERROR / 411 WARNING；platform-assumptions 0 命中；git status 前后一致（无写仓）
