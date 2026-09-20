#!/usr/bin/env bash
# BDD-27/28/29/30/34/36/51 real-invocation evidence (isolated under $W). Verification only.
set -u
REPO=/home/kity/oclab/agateon/.worktrees/agate-TAG0037
W=$1
export PYTHONDONTWRITEBYTECODE=1
UP="file://$REPO"
step() { echo; echo "### $*"; }
res() { # HOME AGATE_HOME? -> run agate-resolve
  ( cd "$W/proj" && env -u AGATE_ROOT -u AGATE_HOME "$@" python3 "$REPO/agate/scripts/agate-resolve.py" ) ; }
mkdir -p "$W/proj"
git -C "$REPO" status --porcelain > "$W/checkout-status-before.txt"

step "Fixture: legacy-shaped symlink ~/.agate -> checkout-copy/agate (has scripts/ and assets/, no current)"
mkdir -p "$W/h27/oldco"; git -C "$REPO" archive HEAD agate | tar -x -C "$W/h27/oldco"
ln -s "$W/h27/oldco/agate" "$W/h27/.agate"
ls -ld "$W/h27/.agate"; ls "$W/h27/oldco/agate" | head -20 | tr '\n' ' '; echo
(cd "$W/h27/oldco" && find . -type f | sort | sha256sum) > "$W/h27/before.sha"

step "BDD-27: agate-resolve.py under symlink home (expect exit 1, no AGATE_ROOT= on stdout, three-step on stderr)"
res HOME="$W/h27" > "$W/h27/o.out" 2> "$W/h27/o.err"; rc=$?
echo "exit=$rc"; echo "--- stdout:"; cat "$W/h27/o.out"; echo "--- stderr:"; cat "$W/h27/o.err"
grep -q '^AGATE_ROOT=' "$W/h27/o.out" && echo "[FAILX] stdout has AGATE_ROOT=" || echo "[PASS] stdout has no AGATE_ROOT= line"
for f in 'mv ~/.agate ~/.agate.bak' 'mkdir -p ~/.agate' 'install.sh'; do grep -qF "$f" "$W/h27/o.err" && echo "[PASS] stderr has: $f" || echo "[FAILX] stderr lacks: $f"; done
[ $rc = 1 ] && echo "[PASS] exit code == 1" || echo "[FAILX] exit code $rc"
(cd "$W/h27/oldco" && find . -type f | sort | sha256sum) > "$W/h27/after.sha"; cmp -s "$W/h27/before.sha" "$W/h27/after.sha" && echo "[PASS] symlink target contents unchanged" || echo "[FAILX] target changed"

step "BDD-28: (a)(e) AGATE_ROOT env override still exit 0 (also with symlink AGATE_HOME); (d) terminal fail-closed; no 'legacy' in output"
mkdir -p "$W/envroot/scripts"; touch "$W/envroot/scripts/x" ; mkdir -p "$W/envroot/assets"
( cd "$W/proj"; HOME="$W/h27" AGATE_ROOT="$W/envroot" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "(a) HOME symlink + AGATE_ROOT: exit=$?" ) 2>&1
( cd "$W/proj"; env -u AGATE_ROOT HOME="$W/hnone" AGATE_HOME="$W/h27/.agate" AGATE_ROOT="$W/envroot" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "(e) AGATE_HOME symlink + AGATE_ROOT: exit=$?" ) 2>&1
mkdir -p "$W/hnone"; ( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/hnone" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "(d) nothing configured: exit=$?" ) 2>&1
python3 - <<PY
import sys, inspect
sys.dont_write_bytecode = True
sys.path.insert(0, "$REPO/agate/scripts")
import agate_common
sig = inspect.signature(agate_common._resolve_version_info)
print("signature:", sig)
print("[PASS] no use_legacy param" if "use_legacy" not in sig.parameters else "[FAILX] use_legacy present")
src = open("$REPO/agate/scripts/agate_common.py").read()
print("realpath(base) occurrences in agate_common.py:", src.count("realpath(base)"))
PY

step "Real online install into two isolated HOMEs: BDD-29 (no-args vs --versions), BDD-30 (deprecated env)"
for k in noargs versions; do
  mkdir -p "$W/h29-$k"
  if [ $k = noargs ]; then A=(); else A=(--versions); fi
  ( cd "$W/proj"; env -u AGATE_ROOT HOME="$W/h29-$k" AGATE_REPO_URL="$UP" bash "$REPO/install.sh" "${A[@]}" > "$W/h29-$k.out" 2> "$W/h29-$k.err" ); echo "install.sh ${A[*]:-<no args>} : exit=$?"
  [ -L "$W/h29-$k/.agate" ] && echo "[FAILX] ~/.agate is a symlink" || { [ -d "$W/h29-$k/.agate" ] && echo "[PASS] ~/.agate is a real directory"; }
  ls -A "$W/h29-$k/.agate" | tr '\n' ' '; echo
  ls -l "$W/h29-$k/.agate" | grep -E 'latest|current'
done
for k in noargs versions; do V=$(readlink "$W/h29-$k/.agate/latest"); echo "$k version dir: $V; scripts/agate-install.py: $(ls "$W/h29-$k/.agate/scripts/agate-install.py")"; done
diff <(cd "$W/h29-noargs/.agate/$(readlink "$W/h29-noargs/.agate/latest")" && find . -printf '%p %y %s\n' | sort) <(cd "$W/h29-versions/.agate/$(readlink "$W/h29-versions/.agate/latest")" && find . -printf '%p %y %s\n' | sort) && echo "[PASS] version-root trees identical (path/type/size)"
git -C "$REPO" status --porcelain > "$W/checkout-status-after29.txt"; cmp -s "$W/checkout-status-before.txt" "$W/checkout-status-after29.txt" && echo "[PASS] source checkout git status unchanged by install.sh" || { echo "[FAILX] checkout status changed"; diff "$W/checkout-status-before.txt" "$W/checkout-status-after29.txt"; }
echo "install.sh ln -s / LINK_NAME occurrences: $(grep -cE 'ln -s|LINK_NAME' "$REPO/install.sh")"
echo "unknown arg: $(bash "$REPO/install.sh" --bogus 2>&1 | head -2 | tr '\n' '|') exit=${PIPESTATUS[0]}"

step "BDD-30: AGATE_SYMLINK / AGATE_REPO_DIR set"
mkdir -p "$W/h30"
( cd "$W/proj"; env -u AGATE_ROOT HOME="$W/h30" AGATE_SYMLINK="$W/x30" AGATE_REPO_DIR="$W/y30" AGATE_REPO_URL="$UP" bash "$REPO/install.sh" > "$W/h30.out" 2> "$W/h30.err" ); echo "exit=$?"
grep -n 'WARNING' "$W/h30.err" | head -3
[ -e "$W/x30" ] && echo "[FAILX] x30 created" || echo "[PASS] AGATE_SYMLINK target not created"
[ -e "$W/y30" ] && echo "[FAILX] y30 created" || echo "[PASS] AGATE_REPO_DIR target not created"
echo "install.sh refs to deprecated names outside the WARNING line:"; grep -n 'AGATE_REPO_DIR\|AGATE_SYMLINK' "$REPO/install.sh"

step "BDD-34: agate-summary.py under symlink home"
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h27" python3 "$REPO/agate/scripts/agate-summary.py" > "$W/sum34.out" 2>&1 ); echo "exit=$?"
grep -nE 'AGATE_ROOT|agate.bak|Traceback|AGENTS.md' "$W/sum34.out"
grep -q Traceback "$W/sum34.out" && echo "[FAILX] traceback" || echo "[PASS] no Traceback"
grep -q 'mv ~/.agate ~/.agate.bak' "$W/sum34.out" && echo "[PASS] migration hint present" || echo "[FAILX] no migration hint"

step "BDD-36: walk the three migration steps (extracted from install.sh's own refusal text) on symlink home"
mkdir -p "$W/h36"; git -C "$REPO" archive HEAD agate | (mkdir -p "$W/h36/oldco" && tar -x -C "$W/h36/oldco"); ln -s "$W/h36/oldco/agate" "$W/h36/.agate"
( cd "$W/proj"; env -u AGATE_ROOT HOME="$W/h36" AGATE_REPO_URL="$UP" bash "$REPO/install.sh" --versions ) > "$W/h36-refuse.out" 2> "$W/h36-refuse.err"; echo "refusal exit=$?"; cat "$W/h36-refuse.err"
S1=$(grep -oE 'mv ~/\.agate ~/\.agate\.bak' "$W/h36-refuse.err" | head -1); S2=$(grep -oE 'mkdir -p ~/\.agate' "$W/h36-refuse.err" | head -1); S3=$(grep -oE 'install\.sh --versions' "$W/h36-refuse.err" | head -1)
echo "extracted: [1] $S1 [2] $S2 [3] $S3"
( cd "$W/proj"; export HOME="$W/h36"; unset AGATE_ROOT AGATE_HOME
  eval "$S1"; echo "step1 exit=$?"
  eval "$S2"; echo "step2 exit=$?"
  AGATE_REPO_URL="$UP" bash "$REPO/${S3}" > "$W/h36-s3.out" 2> "$W/h36-s3.err"; echo "step3 exit=$?" )
ls -A "$W/h36/.agate" | tr '\n' ' '; echo; ls -l "$W/h36/.agate" | grep -E 'latest|current'
[ -d "$W/h36/.agate" ] && [ ! -L "$W/h36/.agate" ] && echo "[PASS] ~/.agate is a real dir"
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h36" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "resolve exit=$?" )
[ -L "$W/h36/.agate.bak" ] && echo "[PASS] .agate.bak is still the original symlink -> $(readlink "$W/h36/.agate.bak")" || echo "[FAILX] .agate.bak not a symlink"
test -d "$W/h36/.agate.bak/scripts" && echo "[PASS] .agate.bak target intact (scripts/ present)"
echo "rollback via rename only (no deletion): mv ~/.agate ~/.agate.new36 && mv ~/.agate.bak ~/.agate"
mv "$W/h36/.agate" "$W/h36/.agate.new36" && mv "$W/h36/.agate.bak" "$W/h36/.agate" && { [ -L "$W/h36/.agate" ] && echo "[PASS] back to symlink state: $(ls -ld "$W/h36/.agate")"; }
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h36" python3 "$REPO/agate/scripts/agate-resolve.py" >/dev/null 2>&1; echo "post-rollback resolve exit=$? (expected 1: legacy shape no longer resolves)" )

step "BDD-51: symlink home -> COMPLETE version root (from step BDD-29 install): resolve exit 0 via current chain; install refused with resolution note"
mkdir -p "$W/h51"; ln -s "$W/h29-noargs/.agate" "$W/h51/.agate"; ls -ld "$W/h51/.agate"
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h51" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "resolve exit=$?" ) 2>&1
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h51" python3 "$REPO/agate/scripts/agate-install.py" latest; echo "install latest exit=$?" ) 2>&1 | sed -e 's/^/  /'
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h51" python3 "$REPO/agate/scripts/agate-summary.py" 2>&1 | grep -nE 'AGATE_ROOT|agate.bak' )
git -C "$REPO" status --porcelain > "$W/checkout-status-end.txt"; cmp -s "$W/checkout-status-before.txt" "$W/checkout-status-end.txt" && echo "[PASS] source checkout git status unchanged at end" || echo "[FAILX] checkout status changed"
