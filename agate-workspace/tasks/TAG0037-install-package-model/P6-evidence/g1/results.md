# P6 verifier g1 results — BDD-1..26 (TAG0037)

Scope: P1 BDD-1 to BDD-26 (contract / legacy form / offline fix / Release / portable / online install). Verifier g1, re-verified at HEAD 043181d (P5 rerun after fixture fix 895a10c; first run was at d6dd3cb). All pytest evidence `g1/bdd-NN-pytest.log` was re-run at 043181d (logs record HEAD and git version); real-environment evidence stays valid because `git diff d6dd3cb..HEAD` outside the task dir touches only `agate/tests/helpers_tag_repo.py` (the BDD-12 real run, which builds its old-layout bundle through that helper, was re-run). Evidence paths in PASS/FAIL lines are relative to `P6-evidence/`.

Evidence conventions: every BDD has a `g1/bdd-NN-pytest.log` (pytest -v, node ids selected from P3 8.1 mapping, all sub-scenarios of parameterized BDDs PASSED, 0 skipped/failed, tail `EXIT_CODE: 0`) plus, where P3 7.5 / the dispatch requires, a real-environment log. Start/end `git status --short` comparison: `g1/git-status.txt`. Nothing was pushed, no tag/Release was deleted or created on GitHub, no local tag created (`git tag -l 'v0.73.0*'` empty); scratch clone tag creation happened only inside a scratchpad clone.

## BDD results

- PASS BDD-1: UPGRADING contract section (single section; a version-root tree, b top-level set + violation rule, c fixed `agate/` name, d single-source path) locked by 9 tests incl. boundary CLI == library (g1/bdd-01-pytest.log)
- PASS BDD-2: boundary list applied to package set on synthetic tag repo, 43 tests (must-include / must-exclude / baseline values / top-level set equality) plus online-install equality (g1/bdd-02-pytest.log)
- PASS BDD-3: default-deny for unregistered top-level dir, auto-include for new file under agate/, doc block == boundary_lines(), 5 tests both sub-scenarios PASSED (g1/bdd-03-pytest.log)
- PASS BDD-4: three paths H1 online / H2 offline / H3 portable produce same tree, H3 uses UPGRADING documented commands, 3 tests PASSED (g1/bdd-04-pytest.log, g1/bdd-17-portable-real-tarball.log)
- PASS BDD-5: old worktree-form version dir still resolves, 4/4 sub-scenarios (resolve, declared, hook root, summary) PASSED (g1/bdd-05-pytest.log)
- PASS BDD-6: probe-order tests PASSED, and AST comparison vs 75a8102 shows the two existing test functions and `_protocol_root` body identical (g1/bdd-06-pytest.log, g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-7: old-form and new-form coexist, current resolves new form, pinned resolves old form, 2/2 sub-scenarios PASSED (g1/bdd-07-pytest.log)
- PASS BDD-8: both `_protocol_root` implementations equal on 5 fixtures plus one-sided-change tripwire, 6 tests PASSED (g1/bdd-08-pytest.log)
- PASS BDD-9: real pack (git plumbing) -> bundle-internal install-offline -> resolve exit 0, no agate/agate nesting, `_protocol_root(vdir)` == vdir/agate; 25 pytest incl. real-tree smoke, plus manual e2e on tag v0.73.0-tagtest.1 content (g1/bdd-09-pytest.log, g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-10: only AGATE_HOME set (HOME separate, no --dest-root): install lands in AGATE_HOME, latest + current->latest + root scripts + `agate-install.py --check` rc 0, 2 tests plus manual e2e (g1/bdd-10-pytest.log, g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-11: fake-bundle helpers replaced by real-pack bundles, sentinel (scripts/ + WORKFLOW.md, no agate-workspace/docs/site), roundtrip ends with resolve, red-replay of old packer layout fails sentinel, 5 tests plus real bundle layout check (g1/bdd-11-pytest.log, g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-12: old-format bundle rejected exit 1 with the required stderr, dest unchanged, 2/2 sub-scenarios in pytest plus real run against a genuinely old-layout bundle (g1/bdd-12-pytest.log, g1/bdd-12-16-legacy-and-release-offline.log)
- PASS BDD-13: release.yml static contract (only push tags v*, only contents: write, no secrets, zero third-party actions, asset names, manifest version) 14 tests PASSED; existing 4 workflows `git diff 75a8102..HEAD` empty (g1/bdd-13-pytest.log, g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-14: notes extraction 16 tests (formal tag exact section, missing section fail-closed with no output, real CHANGELOG v0.72.0, prerelease A/B fallback with first-line marker); real CI notes first line also correct (g1/bdd-14-pytest.log, g1/bdd-20-real-ci.md)
- PASS BDD-15: body tarball name / no wrapper dir / members == F_pkg / blob-byte equality / member safety, 45 tests PASSED at 043181d incl. the 5 T-17 hostile-member cases that FAILED on the real CI run at d6dd3cb (git 2.55) and now pass locally on git 2.43 after fix 895a10c (fix verified on 2.43 only; 2.55 behaviour argued, not observed; next PR CI run confirms); real CI asset re-checked: 155 members byte-equal to git blobs of d6dd3cb (g1/bdd-15-pytest.log, g1/bdd-15-hostile-members-ci-vs-fixed.md, g1/bdd-20-real-ci.md)
- PASS BDD-16: offline tarball layout + manifest for both platforms (2/2) and bundle-internal install + resolve, 3 tests; real Release linux offline asset installed with pip shim, resolve exit 0, installed file set == body tarball set (g1/bdd-16-pytest.log, g1/bdd-12-16-legacy-and-release-offline.log)
- PASS BDD-17: real Release body tarball, PATH without git (asserted), UPGRADING portable commands run verbatim (only version substitution), adopt + resolve (AGATE_VERSION=v0.73.0) + summary + `--check --portable` all exit 0; 11 pytest PASSED (g1/bdd-17-pytest.log, g1/bdd-17-portable-real-tarball.log)
- PASS BDD-18: `--check --portable` without git exit 0, without pyyaml non-zero with guidance, default check without git exit 1, existing test_bdd_7/8 AST-identical to 75a8102 and PASSED, 5 tests (g1/bdd-18-pytest.log, g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-19: no zero-dependency claim in the four docs and portable section declares python3 + pyyaml + no-git caveat, 5 tests PASSED (g1/bdd-19-pytest.log)
- PASS BDD-20: scope per BASELINE_CHANGE (P1 annotation: item 4 cleanup is done manually by the user; P6 scope = items 1-3 + precise cleanup list; item 4 re-check at P8). Items 1-3 hold: run 35505427563 success (6/6 steps), prerelease + first-line marker + tag-verbatim asset names, 4 assets downloaded and `sha256sum -c` OK, body asset byte-identical to local build of d6dd3cb and to git blobs, offline manifest.version strictly v0.73.0 with components sha256 recomputed OK; cleanup list recorded; ④ re-check at P8 (g1/bdd-20-real-ci.md, g1/bdd-20-pytest.log)
- PASS BDD-21: release checklist has post-push `gh release view` with 3-asset check, remediation for tag-pushed-but-Release-missing, G-5 includes Release existence, asset set matches builder, 4 tests PASSED (g1/bdd-21-pytest.log)
- PASS BDD-22: online install (real `agate-install.py latest` from file:// worktree, v0.72.0) yields exactly the package set (153 files), no agate-workspace/docs/site/archived/.github/HANDOFF, root scripts synced, resolve OK; 5 pytest PASSED (g1/bdd-22-pytest.log, g1/bdd-22-23-online-real.log)
- PASS BDD-23: real repo measurement on isolated AGATE_HOME: S = 1,864,871 B (du -sb and file sum) vs B = 1,864,871 B (agate_package and independent oracle), S <= 1.25*B (limit 2,331,089), 94.8% below the 35.6MB whole-repo form; 3 pytest PASSED (g1/bdd-23-pytest.log, g1/bdd-22-23-online-real.log)
- PASS BDD-24: historical tags (no exclusion config / no NOTICES) get body only with pointers unchanged and pin resolves, malformed tag v0.1.0 fail-closed with no half install, 12 tests PASSED both sub-scenarios (g1/bdd-24-pytest.log)
- PASS BDD-25: uninstall for new form with repo/, new form without repo/, old worktree form, plus reference protection and re-pointing, 6 tests PASSED all three sub-scenarios (g1/bdd-25-pytest.log)
- PASS BDD-26: online reinstall idempotent and no source pollution (pytest + real second `latest` run "already installed, skipped", worktree status clean), install.sh rerun idempotent, existing tag0032 bdd_3/4/13/14 AST-identical and PASSED, 8 tests (g1/bdd-26-pytest.log, g1/bdd-22-23-online-real.log, g1/bdd-06-18-26-protected-tests.log)

**Summary**: 26 PASS, 0 FAIL

## BDD-20 detail

Scope: P1 BDD-20 carries a `[BASELINE_CHANGE]` annotation (added by this verifier on the orchestrator's authorization, annotation only, Given/When/Then untouched): Then item 4 (cleanup) is performed manually by the user; P6 scope is items 1-3 plus a precise cleanup list; item 4 is re-checked read-only before the PR in P8. Under that scope items 1-3 hold (see the PASS line), so BDD-20 is PASS with the note "scope per BASELINE_CHANGE; item 4 re-check at P8". This is NOT a claim that item 4 is satisfied: it is not yet.

Precise cleanup list (for the user; the verifier deleted nothing):
- GitHub Release `v0.73.0-tagtest.1` (prerelease; 4 assets: `agateon-v0.73.0-tagtest.1.tar.gz`, `agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz`, `agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz`, `SHA256SUMS`)
- remote tag `refs/tags/v0.73.0-tagtest.1` -> d6dd3cb007a414f7dd5011c4031aa44326335a00
- no local tag exists (`git tag -l 'v0.73.0*'` empty; `git describe --tags --abbrev=0` = `v0.72.0`, so local CHECK 7 is unaffected)
- suggested command for the user: `gh -R randomgitsrc/agateon release delete v0.73.0-tagtest.1 --cleanup-tag --yes`

Item 4 read-only re-check at P8 (before the PR; expected after cleanup): `gh release list` without the tag; `git ls-remote --tags origin v0.73.0-tagtest.1` empty; `git tag -l 'v0.73.0*'` empty; `git describe --tags --abbrev=0` = v0.72.0. Current state (recorded 18:55 +08:00): Release and remote tag still present.

Chained workflows triggered by the tag push on d6dd3cb (for the PR description): Release 35505427563 success; Site Check 35505427551 success; Docs Check 35505427522 FAILURE; Protocol Tests 35505427554 FAILURE (10 failed / 2276 passed / 8 skipped); deploy-pages not triggered. Root causes (also in `g1/bdd-20-real-ci.md` addendum):
1. Tag-induced (5 tests + Docs Check): CHECK 7 `README version badge v0.72.0 != latest tag v0.73.0-tagtest.1` (git describe has no semver filter; foreseen by P1). Disappears when the tag is removed.
2. Fixture (5 tests, T-17 hostile members): git 2.55 `fast-import` rejects `.git` / `..` path components in `helpers_tag_repo.py`; fixed by 895a10c; verified on git 2.43 only, git 2.55 behaviour argued not observed; the next PR CI run is the confirmation (see BDD-15).

## Non-pytest verification inventory

- BDD-6 / BDD-18(3) / BDD-26 protected source and BDD-13(6): `g1/bdd-06-18-26-protected-tests.log`
- BDD-9/10/11 real e2e (pack -> bundle-internal install-offline -> resolve; AGATE_HOME only; pip is a PATH shim, no network): `g1/bdd-09-10-11-16-offline-e2e.log`
- BDD-12 real old-layout bundle rejection and BDD-16 real Release offline asset install: `g1/bdd-12-16-legacy-and-release-offline.log`
- BDD-17 real Release tarball portable install without git: `g1/bdd-17-portable-real-tarball.log`
- BDD-20 real CI / Release / downloads / byte comparison / cleanup list / chained workflows: `g1/bdd-20-real-ci.md`
- BDD-15 hostile-member CI failure vs fixed HEAD: `g1/bdd-15-hostile-members-ci-vs-fixed.md`
- BDD-22/23 real online install and redundancy quantification: `g1/bdd-22-23-online-real.log`
- Substitution notes: BDD-17 replaced `agateon-vX.Y.Z.tar.gz` by the real asset name `agateon-v0.73.0-tagtest.1.tar.gz` and the remaining `vX.Y.Z` by `v0.73.0` (adopt requires strict semver; asset names keep the tag verbatim per BDD-13 item 5). The BDD-9/10/11 e2e packs from a scratchpad clone carrying tag `v0.73.0-tagtest.1` (created only in that clone, content = d6dd3cb) with `--ref` and strict version `v0.73.0`, so the bundle-internal entry is the current code. `actionlint` is not installed on this machine; BDD-13 static contract relies on the yaml-based tests and the real successful CI run.
- Environment residue check: all installs / bundles / downloads live under the session scratchpad (`g1-01` .. `g1-06`, `g1-02-release`); real `~/.agate`, the main checkout and repo refs untouched; no `__pycache__` created by this run under installed / bundle trees (checked in the logs).
