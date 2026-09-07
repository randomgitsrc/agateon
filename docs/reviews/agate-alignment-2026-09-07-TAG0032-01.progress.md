# TAG0032 protocol-alignment review progress
- 2026-09-07T21:30:18+08:00 start
- read role def protocol-alignment-review.md (A1-A7, backprop table, principle 6 DESIGN_GAP)
- read dispatch-context TAG0032: intent = fix 3 breakpoints of TAG0008 version mgmt v1 (entry broken link / meta-repo gap / no update entry)
- read AGENTS.md (dual workspace, gate layering, release checklist)
--- git diff stat 3f3cc01..HEAD ---
 HANDOFF-TAG0032.md                                 | 123 +++++++
 README.md                                          |   7 +-
 README.zh-CN.md                                    |   7 +-
 agate-workspace/debt/tech-debt.md                  |  23 ++
 .../tasks/TAG0032-version-lifecycle/.state.yaml    |  16 +-
 .../P1-dispatch-context-analyst-fix1.md            | 314 ++++++++++++++++
 .../P1-dispatch-context-analyst-fix2.md            | 292 +++++++++++++++
 .../P1-dispatch-context-analyst.md                 | 335 +++++++++++++++++
 .../P1-dispatch-context-requirements-review-re1.md | 305 +++++++++++++++
 .../P1-dispatch-context-requirements-review.md     | 311 ++++++++++++++++
 .../tasks/TAG0032-version-lifecycle/P1-progress.md |  34 ++
 .../TAG0032-version-lifecycle/P1-requirements.md   | 314 ++++++++++++++++
 .../P1-review-progress.md                          |  32 ++
 .../tasks/TAG0032-version-lifecycle/P1-review.md   |  96 +++++
 .../tasks/TAG0032-version-lifecycle/P2-design.md   | 407 +++++++++++++++++++++
 .../P2-dispatch-context-architect.md               | 379 +++++++++++++++++++
 .../P2-dispatch-context-plan-eng-review.md         | 351 ++++++++++++++++++
 .../tasks/TAG0032-version-lifecycle/P2-progress.md |  37 ++
 .../P2-review-progress.md                          |  31 ++
 .../tasks/TAG0032-version-lifecycle/P2-review.md   | 263 +++++++++++++
 .../P3-dispatch-context-test-designer.md           | 212 +++++++++++
 .../tasks/TAG0032-version-lifecycle/P3-progress.md |  44 +++
 .../TAG0032-version-lifecycle/P3-test-cases.md     | 145 ++++++++
 .../P4-dispatch-context-implementer-batch1.md      | 276 ++++++++++++++
 .../P4-dispatch-context-implementer-batch2.md      | 278 ++++++++++++++
 .../P4-dispatch-context-implementer-fix1.md        | 278 ++++++++++++++
 .../P4-dispatch-context-review-re1.md              | 254 +++++++++++++
 .../P4-dispatch-context-review.md                  | 282 ++++++++++++++
 .../TAG0032-version-lifecycle/P4-implementation.md | 233 ++++++++++++
 .../tasks/TAG0032-version-lifecycle/P4-progress.md |  83 +++++
 .../P4-review-progress.md                          |  69 ++++
 .../tasks/TAG0032-version-lifecycle/P4-review.md   | 159 ++++++++
 .../P5-dispatch-context-verifier.md                | 229 ++++++++++++
 .../tasks/TAG0032-version-lifecycle/P5-progress.md |  59 +++
 .../P5-test-results/consistency.log                | 353 ++++++++++++++++++
 .../P5-test-results/counttests.log                 |   7 +
 .../P5-test-results/fail-list.txt                  |   5 +
 .../P5-test-results/shellcheck.log                 |   8 +
 .../P5-test-results/unit.md                        | 135 +++++++
 .../P5-test-results/unit.raw.log                   |  28 ++
 .../P5-test-results/unit.rerun2.log                |  26 ++
 .../P5-test-results/unit.rerun3.log                |  28 ++
 .../TAG0032-version-lifecycle/P6-acceptance.md     |  83 +++++
 .../P6-dispatch-context-verifier.md                | 323 ++++++++++++++++
 .../P6-evidence/bdd-1-install-symlink.log          |  12 +
 .../P6-evidence/bdd-10-update-aligned.log          |  12 +
 .../P6-evidence/bdd-11-lifecycle-section.log       |  12 +
 .../P6-evidence/bdd-12-consistency.log             | 353 ++++++++++++++++++
 .../P6-evidence/bdd-12-doc-converged.log           |  15 +
 .../P6-evidence/bdd-13-e2e-lifecycle.log           |  12 +
 .../P6-evidence/bdd-14-no-pollution.log            |  12 +
 .../P6-evidence/bdd-2-migration-hint.log           |  12 +
 .../P6-evidence/bdd-3-plain-dir.log                |  12 +
 .../P6-evidence/bdd-4-doc-semantics.log            |  12 +
 .../P6-evidence/bdd-4-root-scripts.log             |  13 +
 .../P6-evidence/bdd-5-curl-bash-transcript.txt     |  78 ++++
 .../P6-evidence/bdd-5-install-sh-versions.log      |  12 +
 .../P6-evidence/bdd-6-meta-resolve.log             |  12 +
 .../P6-evidence/bdd-7-rootproto-resolve.log        |  12 +
 .../P6-evidence/bdd-8-hook-gate-path.log           |  12 +
 .../P6-evidence/bdd-9-full-suite.log               |  26 ++
 .../tasks/TAG0032-version-lifecycle/P6-progress.md |  36 ++
 .../P6.5-dispatch-context-judge.md                 |  71 ++++
 .../P6.5-judge-verdict.md                          |  51 +++
 .../TAG0032-version-lifecycle/P7-consistency.md    | 283 ++++++++++++++
 .../P7-dispatch-context-consistency-reviewer.md    | 215 +++++++++++
 .../tasks/TAG0032-version-lifecycle/P7-progress.md |  26 ++
 .../TAG0032-version-lifecycle/gate-events.jsonl    |  17 +
 .../TAG0032-version-lifecycle/known-failures.md    |  14 +
 agate-workspace/tasks/active-tasks.md              |   2 +-
 agate/SETUP.md                                     |   2 +
 agate/UPGRADING.md                                 |  50 ++-
 agate/scripts/agate-install.py                     |  67 +++-
 agate/scripts/agate_common.py                      |  23 +-
 .../integration/test_version_lifecycle_e2e.py      | 202 ++++++++++
 agate/tests/unit/test_agate_version_install.py     | 211 ++++++++++-
 agate/tests/unit/test_agate_version_resolve.py     |  96 +++++
 agate/tests/unit/test_hook_resolve_entry.py        |  47 +++
 agate/tests/unit/test_upgrading_lifecycle.py       | 141 +++++++
 install.sh                                         |  35 ++
 80 files changed, 9476 insertions(+), 16 deletions(-)
--- end stat ---
--- read core script diffs ---
- agate_common.py: +_protocol_root(vdir) probe order vdir/scripts then vdir/agate/scripts; _resolve_version_info wraps root in _protocol_root for both .agate-version path and current-chain path
- agate-install.py: +_protocol_root degraded copy; _ensure_repo adds git fetch --tags --force --prune (fail-open); +_LEGACY_SYMLINK_MSG; +_sync_root_scripts SINGLE copytree from _protocol_root(vdir)/scripts; _cmd_install islink guard fail-closed exit1; latest alias; usage text updated
- install.sh: +--versions branch (islink fail-closed, py probe, clone repo, exec agate-install.py latest); prefers repo copy installer over SCRIPT_DIR
- CRITICAL: UPGRADING 根scripts/维护语义 says 内容 = 安装器 scripts/ 叠加 current 协议 scripts/（后者覆盖前者，后拷贝者胜）— dual-layer. Code _sync_root_scripts does SINGLE copytree. Need P7 check.
- README.md/zh: install.sh --versions promoted as official path; latest alias documented; points to UPGRADING 版本管理生命周期
- SETUP.md: +更新口径 note pointing to UPGRADING
--- read P7-consistency.md ---
- P7 status=approved, blocker=0, deviation_count=1 (non-critical), design_gap 5/5 REVIEWED
- P7 §3.3 explicitly: UPGRADING 根scripts/维护语义段 describes fix-1-PRE dual copytree (叠加/后拷贝者胜/运行中安装器自带 scripts/) but code reverted to single-source copytree. deviation_count=1 non-critical. Recommend P8 fix. NOT a P7 rollback reason.
- => per role principle 6: this literal misalignment is P7 REVIEWED (DESIGN_GAP 1 REVIEWED + deviation_count=1 acknowledged). Do NOT judge MISALIGNED; mark KNOWN_DEVIATION source TAG0032 P7.
- P7 §3.1-3.4 cover A3/A5 reverse prop: packages match, resolve-entry.py not changed (beneficiary), BDD 14/14, pure-incremental redline locked
--- read P4-implementation.md ---
- 5 DESIGN_GAP: (1) dual copytree -> fix-1 reverted to single source; (2) latest alias; (3) install.sh exec path -> fix-1 repo-copy-first + SCRIPT_DIR fallback; (4) _ensure_repo git fetch fail-open; (5) v0.50.0 backtick micro-adjust
- P4 fix-1 verification: pytest -k tag0032 = 18 passed; unit+regression -n auto = 1390 passed 2 skipped; integration = 94 passed; consistency 0 ERROR
--- read agate_common.py _protocol_root L166-179, _resolve_version_info L182-214: matches P2 decision A1, probe order vdir/scripts then vdir/agate/scripts ---
--- read agate-install.py L281-345: _LEGACY_SYMLINK_MSG, _sync_root_scripts SINGLE copytree, _cmd_install islink guard + _sync calls, usage latest ---
--- scripts/README.md L5 mechanism blockquote + L70 agate-install.py desc: NOT updated by diff. L70 still '无参 = 装 latest 指针' no 'latest' arg token, no --versions, no root scripts copy, no _protocol_root meta form. Incomplete not contradictory. NOT in P2 M-table (M7-M11 = UPGRADING/README x2/SETUP). ---
--- tests/README.md L37-100 per-script table: does NOT list pre-existing test_agate_version_install/resolve/hook_resolve_entry either; count via count-tests.sh (not hardcoded). Not adding 2 new files = consistent with pre-existing non-exhaustive state. ---
--- adr.md ADR-009 (v0.50.0 版本管理根 + resolve-entry): decision lists repo/ vX.Y.Z/ latest/current pointers scripts/. Does NOT contemplate meta-repo whole-repo form nor _protocol_root probe nor root scripts copy-vs-symlink/refresh semantics. TAG0032 决策 A1/B1 are task-local, not in adr.md. => A7 recommend new ADR or ADR-009 后果 extension ---
--- platform-notes.md L165 pointer forms section: covers latest/current pointer text-file degradation. Does NOT mention install.sh --versions POSIX shell assumption nor decision B1 copy (non-symlink, no Windows degradation). ---
--- FULL pytest (unit+regression+integration -n auto): 1 failed, 1483 passed, 2 skipped in 36s ---
--- the 1 fail = test_nc_cross_checkout_paths_hash_consistent pre-existing parallel flaky (passes isolated 1 passed); documented known-failures.md + P5 + P7 §4; TAG0032 does not touch agate-next-card.py; NOT a regression ---
--- ~/.agate unchanged symlink -> /home/kity/oclab/agateon/agate ; [PROD_NOT_TOUCHED] ---
--- 18 tag0032 tests pass; full suite 1483 passed/1 flaky/2 skipped; consistency 0 ERROR ---
--- P1 §4 同类扫描(强制) 扫描4 enumerated doc-propagation locations WITHOUT agate/scripts/README.md; P1 §6 trigger list also excludes it ---
--- ADR-009 does not contemplate meta-repo form / _protocol_root probe / decision B1 copy semantics -> A7 recommend ADR ---
--- writing final report ---
--- DONE: report written to docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md ---
--- verdict: A1=ALIGNED(KNOWN_DEVIATION) A2=NHR A3=NHR A4=ALIGNED A5=NHR A6=ALIGNED A7=NHR ; MISALIGNED=0 ; NHR=4 ---
--- ~/.agate unchanged: lrwxrwxrwx 1 kity kity 30  9月  3 22:51 /home/kity/.agate -> /home/kity/oclab/agateon/agate ; [PROD_NOT_TOUCHED] ---
