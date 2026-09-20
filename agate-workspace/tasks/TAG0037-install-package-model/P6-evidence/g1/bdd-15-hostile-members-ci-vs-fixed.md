# BDD-15 addendum: T-17 hostile-member cases, CI failure at d6dd3cb vs pass at fixed HEAD 043181d (2026-09-20T18:55:24+08:00)

Test cases (member-safety half of BDD-15: package builder must reject hostile members):
test_t17_list_package_rejects_hostile_members[dot-git-dir | dot-GIT-uppercase | dot-GiT-mixed-file | dotdot-segment] and test_t17_hostile_names_outside_package_region_are_ignored (agate/tests/unit/test_agate_package.py).

## Observed on the real CI run at d6dd3cb (GitHub runner, git 2.55.0; run 35505427554 Protocol Tests)
These 5 cases FAILED (fixture construction, not product code):
FAILED agate/tests/unit/test_agate_package.py::test_t17_hostile_names_outside_package_region_are_ignored - RuntimeError: git fast-import --quiet 失败: fatal: invalid path 'docs/.git/config'
FAILED agate/tests/unit/test_agate_package.py::test_t17_list_package_rejects_hostile_members[dotdot-segment] - RuntimeError: git fast-import --quiet 失败: fatal: invalid path 'agate/../z'
FAILED agate/tests/unit/test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-git-dir] - RuntimeError: git fast-import --quiet 失败: fatal: invalid path 'agate/.git/config'
FAILED agate/tests/unit/test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-GiT-mixed-file] - RuntimeError: git fast-import --quiet 失败: fatal: invalid path 'agate/sub/.GiT'
FAILED agate/tests/unit/test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-GIT-uppercase] - RuntimeError: git fast-import --quiet 失败: fatal: invalid path 'agate/.GIT/y'

root cause: helpers_tag_repo.build_bare_repo used `git fast-import`, which git 2.55 rejects for paths containing .git / .. components (fatal: invalid path).

## Fix (commit 895a10c, agate/tests/helpers_tag_repo.py only; product scripts unchanged)
Fixtures with dangerous path components are now built by object-level plumbing (hash-object --literally / update-ref) instead of fast-import; fast-import failure also falls back to it. `git diff d6dd3cb..HEAD` non-task files: only agate/tests/helpers_tag_repo.py.

## Observed locally at fixed HEAD 043181d (git 2.43.0)
test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-git-dir] PASSED [ 46%]
test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-GIT-uppercase] PASSED [ 48%]
test_agate_package.py::test_t17_list_package_rejects_hostile_members[dot-GiT-mixed-file] PASSED [ 51%]
test_agate_package.py::test_t17_list_package_rejects_hostile_members[dotdot-segment] PASSED [ 66%]
test_agate_package.py::test_t17_hostile_names_outside_package_region_are_ignored PASSED [ 80%]
Full BDD-15 selection now 45 tests, all PASSED (g1/bdd-15-pytest.log).

## Limits of this verification (explicit)
- The fix is verified on git 2.43.0 ONLY. That the fixture now works on git 2.55 is ARGUED (hash-object --literally, tree/commit written as raw objects, update-ref do not run the path fsck that fast-import applies), NOT observed: no git 2.55 is available here and CI was not re-run on the fixed commit.
- Confirmation = the next PR CI run of Protocol Tests on the fixed branch.
EXIT_CODE: 0
