#!/usr/bin/env python3
"""Independent BDD-37 scan (does NOT import the test): baseline 75a8102 vs HEAD. Read-only (git ls-tree / git show)."""
import re, subprocess, sys
REPO = "/home/kity/oclab/agateon/.worktrees/agate-TAG0037"
PATS = [re.compile(p, re.I) for p in (r"use_legacy", r"legacy[ _-]?(软链|symlink|layout)", "单软链", "软链兜底")]
LOCKS = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "uv.lock"}
SELF = "agate/tests/regression/test_no_legacy_residue.py"
W = {"CHANGELOG.md","agate/UPGRADING.md","agate/adr.md","agate-workspace/debt/tech-debt.md","install.sh","agate/scripts/agate-install.py","agate/scripts/install-offline.py","agate/scripts/agate_common.py","agate/scripts/agate-resolve.py","agate/scripts/agate-summary.py","agate/tests/unit/test_agate_version_install.py","agate/tests/unit/test_agate_version_resolve.py"}
R = ["AGENTS.md","README.md","README.zh-CN.md","agate/AGENTS.md","agate/SETUP.md","agate/WORKFLOW.md","agate/orchestrator-template.md","agate/platform-notes.md","agate/scripts/README.md","agate/tests/unit/test_dsh_preset.py","docs/guides/project-map.md","docs/guides/worktree-dogfooding-guide.md"]
def git(*a, text=True):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=text).stdout
def in_scope(rel):
    parts = rel.split("/")
    if "archived" in parts[:-1] or "node_modules" in parts: return False
    if rel.startswith(("agate-workspace/tasks/", "docs/reviews/", "docs/design-notes/")): return False
    if parts[-1] in LOCKS or rel == SELF: return False
    return True
def scan(rev):
    files = [f for f in git("ls-tree", "-r", "--name-only", rev).splitlines() if in_scope(f)]
    hits = {}
    for f in files:
        b = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{f}"], capture_output=True).stdout
        if b"\0" in b[:8000]: continue
        t = b.decode("utf-8", "replace")
        m = [sum(len(p.findall(t)) for p in [pt]) for pt in PATS]
        if any(m): hits[f] = m
    return files, hits
for rev in ("75a8102", "HEAD"):
    files, hits = scan(rev)
    print(f"=== {rev} ({git('rev-parse','--short',rev).strip()}): scanned {len(files)} files; files with any hit: {len(hits)}")
    for f, m in sorted(hits.items()):
        tag = "W" if f in W else ("R" if f in R else "OUTSIDE")
        print(f"  [{tag:7}] {f}  counts(use_legacy,legacy-symlink/layout,单软链,软链兜底)={m}")
    ul = {f for f, m in hits.items() if m[0]}
    print(f"  use_legacy hit files: {sorted(ul)}")
    r_left = [f for f in R if f in hits]; out = [f for f in hits if f not in W and f not in R]
    print(f"  R-set files still hit: {len(r_left)} {r_left}")
    print(f"  hit files not in W (excluding R): {out}")
    if rev == "HEAD":
        ok = (ul <= {"agate-workspace/debt/tech-debt.md"}) and not r_left and all(f in W for f in hits)
        print("  VERDICT HEAD:", "PASS (use_legacy only in closed-debt narrative; R cleared; all hits within W)" if ok else "FAIL")
    else:
        print(f"  baseline hit count = {len(hits)} (P1 expects 23)")
# original P0 grep
print("=== original P0 grep on HEAD tracked files (in scope) outside W: 'use_legacy|legacy 软链布局'")
files, _ = scan("HEAD")
rx = re.compile(r"use_legacy|legacy 软链布局")
bad = []
for f in files:
    if f in W: continue
    b = subprocess.run(["git","-C",REPO,"show",f"HEAD:{f}"],capture_output=True).stdout
    if rx.search(b.decode("utf-8","replace")): bad.append(f)
print("  residue files outside W:", bad)
