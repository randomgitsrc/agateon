#!/usr/bin/env python3
"""BDD-38 ③ / P3 §6.6: function-body (ast.dump) comparison between baseline 75a8102 and HEAD. Read-only."""
import ast, subprocess
REPO = "/home/kity/oclab/agateon/.worktrees/agate-TAG0037"
def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout
def funcs(rev, path):
    r = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"], capture_output=True, text=True)
    if r.returncode: return {}
    out = {}
    for n in ast.walk(ast.parse(r.stdout)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(n.name, []).append(ast.dump(n))
    return out
tests = [p for p in git("ls-tree", "-r", "--name-only", "HEAD", "agate/tests").splitlines() if p.endswith(".py")]
base_tests = [p for p in git("ls-tree", "-r", "--name-only", "75a8102", "agate/tests").splitlines() if p.endswith(".py")]
allp = sorted(set(tests) | set(base_tests))
print(f"# BDD-38 ③: functions whose name starts with test_bdd_30 (all agate/tests/**/*.py), 75a8102 vs HEAD")
n_same = 0; problems = []
seen_base = []
for p in allp:
    b, h = funcs("75a8102", p), funcs("HEAD", p)
    names = sorted({k for k in list(b) + list(h) if k.startswith("test_bdd_30")})
    for k in names:
        seen_base.append((p, k))
        if k in b and k in h:
            if b[k] == h[k]:
                n_same += 1; print(f"  SAME    {p}::{k}")
            else:
                problems.append((p, k, "changed")); print(f"  CHANGED {p}::{k}")
        elif k in b: problems.append((p, k, "removed-or-renamed")); print(f"  GONE    {p}::{k}   (in baseline, not at HEAD)")
        else: print(f"  NEW     {p}::{k}   (not in baseline)")
allowed = {"test_bdd_30_legacy_symlink_direct_root"}
bad = [x for x in problems if x[1] not in allowed]
print(f"identical={n_same}; problems={problems}")
print("VERDICT BDD-38 ③:", "PASS (only the rewritten test_bdd_30_legacy_symlink_direct_root differs)" if not bad else f"FAIL {bad}")
print()
print("# BDD-38 ①: the two rewritten legacy-direct tests: baseline vs HEAD names")
for p in ("agate/tests/unit/test_agate_version_resolve.py",):
    for rev in ("75a8102", "HEAD"):
        f = funcs(rev, p)
        print(f"  {rev}: legacy-named:", sorted(k for k in f if "legacy" in k.lower()), "| symlink_fail_closed:", sorted(k for k in f if "symlink" in k and "fail_closed" in k))
print("# BDD-38 ②: test_tag0032_bdd_1/2 assertions preserved? (compare ast bodies, names may differ)")
p = "agate/tests/unit/test_agate_version_install.py"
b, h = funcs("75a8102", p), funcs("HEAD", p)
for k in sorted(set(b) | set(h)):
    if k.startswith(("test_tag0032_bdd_1_", "test_tag0032_bdd_2_")):
        print(f"  {k}: baseline={'present' if k in b else 'absent'} HEAD={'present' if k in h else 'absent'} body-identical={b.get(k)==h.get(k)}")
print("# BDD-38 ④ / P3 §6.6 T-10 protected: test_bdd_7 / test_bdd_8 / test_tag0032_bdd_3/4/13/14 / test_debt0034_* bodies (INST/E2E)")
for p in ("agate/tests/unit/test_agate_version_install.py", "agate/tests/integration/test_version_lifecycle_e2e.py"):
    b, h = funcs("75a8102", p), funcs("HEAD", p)
    for k in sorted(set(b) | set(h)):
        if k.startswith(("test_bdd_7_", "test_bdd_8_", "test_tag0032_bdd_3_", "test_tag0032_bdd_4_", "test_tag0032_bdd_13_", "test_tag0032_bdd_14_", "test_debt0034_")):
            print(f"  {p.split('/')[-1]}::{k}: body-identical={b.get(k)==h.get(k)} (baseline={'y' if k in b else 'n'}, HEAD={'y' if k in h else 'n'})")
