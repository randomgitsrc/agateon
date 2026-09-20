#!/usr/bin/env python3
"""Run mapped pytest ids for one BDD; write P6 g2 evidence log. Verification only."""
import re, subprocess, sys, os, time
REPO = "/home/kity/oclab/agateon/.worktrees/agate-TAG0037"
OUT = REPO + "/agate-workspace/tasks/TAG0037-install-package-model/P6-evidence/g2"
T = "agate/tests/"
F = dict(
    RES=T+"unit/test_agate_version_resolve.py", WS=T+"unit/test_agate_workspace_resolve.py",
    SH=T+"unit/test_install_sh.py", INST=T+"unit/test_agate_version_install.py",
    ADOPT=T+"unit/test_agate_install_adopt.py", OFF=T+"unit/test_install_offline.py",
    SUM=T+"unit/test_agate_summary.py", UL=T+"unit/test_upgrading_lifecycle.py",
    UC=T+"unit/test_upgrading_contract_doc.py", SD=T+"unit/test_setup_agate_dir.py",
    DS=T+"unit/test_doc_sweep.py", NLR=T+"regression/test_no_legacy_residue.py",
    OOS=T+"regression/test_tag0037_out_of_scope_untouched.py",
    HOOK=T+"unit/test_hook_resolve_entry.py", PCH=T+"integration/test_pre_commit_hook.py",
    DSH=T+"unit/test_dsh_preset.py",
)
ALL = r".*"
SPEC = {
 27: [("RES", r"test_bdd_27_|test_debt0042_agate_home_symlink_fail_closed")],
 28: [("RES", r"test_bdd_28_"), ("WS", r"test_bdd_28_")],
 29: [("SH", r"test_bdd_29_")],
 30: [("SH", r"test_bdd_30_")],
 31: [("SH", r"test_bdd_31_")],
 32: [("INST", r"test_bdd_32_|test_tag0032_bdd_1_|test_tag0032_bdd_2_"), ("ADOPT", r"test_t14_")],
 33: [("OFF", r"test_bdd_33_")],
 34: [("SUM", r"test_bdd_34_")],
 35: [("INST", r"test_bdd_35_|test_debt0034_")],
 36: [("SH", r"test_bdd_36_")],
 37: [("NLR", ALL)],
 38: [("RES", r"test_bdd_27_symlink_home_fail_closed|test_debt0042_agate_home_symlink_fail_closed"), ("INST", r"test_tag0032_bdd_1_|test_tag0032_bdd_2_"), ("UL", r"test_tag0032_bdd_10_"), ("UC", r"test_bdd_39_1_")],
 39: [("UC", r"test_bdd_39_"), ("DS", r"test_bdd_39_"), ("NLR", r"test_bdd_37_3_")],
 40: [("DS", r"test_bdd_40_"), ("SD", r"test_bdd_40_"), ("SUM", r"test_bdd_40_")],
 41: [("SD", r"test_bdd_41_")],
 42: [("SD", r"test_bdd_42_")],
 43: [("SD", r"test_bdd_43_")],
 44: [("SD", r"test_bdd_44_"), ("DSH", ALL)],
 45: [("SD", r"test_bdd_45_")],
 46: [("OOS", ALL)],
 47: [("HOOK", ALL), ("PCH", r"test_agate_root_self_locate_worktree"), ("WS", r"test_bdd_47_")],
 49: [("DS", r"test_bdd_49_4_")],
 50: [("UC", r"test_bdd_50_1_")],
 51: [("RES", r"test_bdd_51_"), ("SUM", r"test_bdd_51_"), ("INST", r"test_bdd_51_")],
 52: [("SUM", r"test_bdd_52_")],
}
def main():
    n = int(sys.argv[1])
    ids = [l.strip() for l in open(sys.argv[2]) if "::" in l]
    sel = []
    for key, rx in SPEC[n]:
        f = F[key]
        for i in ids:
            fp, name = i.split("::", 1)
            if fp == f and re.match(rx, name) and i not in sel:
                sel.append(i)
    log = f"{OUT}/bdd-{n:02d}-pytest.log"
    if not sel:
        open(log, "w").write("NO TESTS SELECTED\nEXIT_CODE: 5\n"); print(n, "NONE"); return
    cmd = ["timeout", "280s", sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider", "--no-header"] + sel
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    t0 = time.time()
    p = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    with open(log, "w") as fh:
        fh.write(f"# BDD-{n} pytest evidence (verifier g2)\n# selected {len(sel)} ids; cwd={REPO}\n")
        fh.write(f"# command: PYTHONDONTWRITEBYTECODE=1 timeout 280s python3 -m pytest -v -p no:cacheprovider --no-header <{len(sel)} node ids below>\n")
        for i in sel: fh.write("#   " + i + "\n")
        fh.write("# HEAD=" + subprocess.run(["git","rev-parse","--short","HEAD"],cwd=REPO,capture_output=True,text=True).stdout.strip() + " " + subprocess.run(["git","--version"],capture_output=True,text=True).stdout.strip() + "\n")
        fh.write(f"# elapsed {time.time()-t0:.1f}s\n\n")
        fh.write(p.stdout); fh.write(p.stderr)
        fh.write(f"\nEXIT_CODE: {p.returncode}\n")
    last = [l for l in p.stdout.splitlines() if l.strip()][-1:]
    print(f"BDD-{n}: selected={len(sel)} rc={p.returncode} :: {last}")
main()
