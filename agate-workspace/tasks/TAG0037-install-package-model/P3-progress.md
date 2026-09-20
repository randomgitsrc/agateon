P3-A: read P2-design, P1(1-330), P0; next read existing test style
P3-A: read conftest, pack-offline; next install-offline + tests
P3-A: read agate-install.py, install-offline.py, pack-offline; next resolve deps, protocol-tests.yml, git env
P3-A: planned test files; next read role file + sample P3-test-cases + CI fetch-depth
P3-A: scratch exp: fast-import accepts odd paths (single-process fixture builder chosen); writing helpers_tag_repo.py next
P3-A: helpers_tag_repo.py written in full (resumed after rate limit); next smoke-test it then write 4 test files + P3-test-cases.md
P3-A: helper fixed+smoke ok (fast-import tag needs single LF); writing test_agate_package.py
P3-A: test_agate_package.py written; running ruff + red check
P3-A: wrote test_agate_release.py, test_release_workflow.py; next test_install_three_paths.py, P3-test-cases.md, ref-impl validation in scratchpad
P3-A: refs validated in scratchpad (pkg 128/129 pass w/ ref impl, release/three-paths/workflow pass w/ refs); running final red run + writing P3-test-cases.md
P3-A: DONE. P3-test-cases.md written (agent key rejected by md-field-set; reported)
P3-C: started; read dispatch/P3-test-cases/P1(1-617 next)
P3-B: read P2-design + role; next P1 BDDs, helpers, existing tests
P3-C: read P1+P2 (§3,5,6,14); next helpers/README/existing tests/real docs
P3-B: read P1 BDDs; next helpers + existing tests
P3-B: read helpers_tag_repo; next existing tests+scripts
P3-B: read install-offline/pack-offline + their tests; next roundtrip, agate-install.py, resolve tests
P3-B: read agate-install.py, roundtrip; next version_install tests, uninstall tests, resolve tests
P3-B: read version_install/uninstall tests, install.sh; next agate_common resolve, resolve/summary tests, hook fixtures
P3-B: read resolve tests; next e2e/summary/workspace_resolve/hook fixtures greps
P3-C: read summary/SETUP/AGENTS/CHANGELOG; verified opencode/codex CLIs work (13s). Plan files: unit/test_upgrading_contract_doc.py, unit/test_doc_sweep.py, unit/test_setup_agate_dir.py, integration/test_portable_no_git.py, regression/test_no_legacy_residue.py, regression/test_tag0037_out_of_scope_untouched.py + edit unit/test_upgrading_lifecycle.py::bdd_10
P3-C: wrote unit/test_upgrading_contract_doc.py
P3-B: finished reading all inputs; design decided (14 files); next check hook tests + UPGRADING migration text, then write files
P3-C: edited test_upgrading_lifecycle.py::bdd_10 (removed git pull legacy assertion, per BDD-38 4); next test_no_legacy_residue
P3-B: wrote regression/test_protocol_root_dual_impl.py; running it
P3-C: wrote regression/test_no_legacy_residue.py
P3-B: wrote unit/test_install_sh.py; running (timeout 280)
P3-C: wrote unit/test_setup_agate_dir.py
P3-B: wrote unit/test_agate_pack_offline.py; running
P3-C: wrote unit/test_doc_sweep.py, regression/test_tag0037_out_of_scope_untouched.py
P3-B: pack tests done (11 red/5 green); writing test_install_offline.py (largest)
P3-C: wrote integration/test_portable_no_git.py (BDD-17 no-git PATH gap)
P3-C: ref clone at scratchpad/c-ref-1/repo (scratch only) for validating C tests
P3-C: wrote integration/test_offline_real_pack_resolve.py (BDD-9 explicit)
P3-B: wrote unit/test_install_offline.py; running
P3-B: building reference impl in scratchpad/refB-1 to validate tests (not in repo)
P3-B: refB-1 reference impl written (scratchpad); running my tests against it via AGATE_ROOT/AGATE_TEST_SCRIPTS_SRC
P3-C: DONE. wrote §7 in P3-test-cases.md; 8 test files (95 tests: 52 red B-class / 43 intended green); ref clone 95/95 pass
P3-B: fixture edits done (version_install/_tag_upstream+bdd5 cleanup, e2e, 3 hook fixtures); next: append new tests to version_install, uninstall, resolve, summary, workspace, roundtrip, hook BDD-47
P3-B: version_install + uninstall tests done and validated vs refB; DESIGN_GAP-B1 found: TAG0008 test_bdd_2/3/6 assert git-worktree semantics, contradict new contract -> rewritten+flagged; next resolve/summary/workspace/roundtrip/BDD-47
P3-B: all test files written; validating protected bodies (ast vs HEAD), ruff, full runs
P3-B: all tests validated (REAL: 146 red/all B-class; REF impl: 250 pass); writing P3-test-cases.md section 6
P3-B: DONE. section 6 written; 12 test files (3 new + 9 modified) + 4 fixture-only edits; REAL: 146 red (B-class)/104 green; REF impl: 250/250 (static install.sh checks verified separately); DESIGN_GAP-B1 flagged (TAG0008 test_bdd_2/3/6 worktree assertions)
P3 finalization: started
P3 finalization: hygiene fixed, docs edited; running check-tdd-red
P3 finalization: DONE, check-tdd-red exit 0 (386 failed/1906 passed/2 skipped)
