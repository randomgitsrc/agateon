#!/usr/bin/env bash
# BDD-36 walk-through (fixed step-3 invocation) + BDD-29 unknown-arg exit code. Isolated under $W.
set -u
REPO=/home/kity/oclab/agateon/.worktrees/agate-TAG0037
W=$1; export PYTHONDONTWRITEBYTECODE=1; UP="file://$REPO"
mkdir -p "$W/proj" "$W/h36/oldco"
git -C "$REPO" status --porcelain > "$W/status-before.txt"
git -C "$REPO" archive HEAD agate | tar -x -C "$W/h36/oldco"; ln -s "$W/h36/oldco/agate" "$W/h36/.agate"
echo "### fixture: ~/.agate -> old checkout agate/ (symlink)"; ls -ld "$W/h36/.agate" | sed 's/.*\.agate/.agate/'
( cd "$W/proj"; env -u AGATE_ROOT HOME="$W/h36" AGATE_REPO_URL="$UP" bash "$REPO/install.sh" --versions ) > "$W/refuse.out" 2> "$W/refuse.err"; echo "refusal exit=$?"
S1=$(grep -oE 'mv ~/\.agate ~/\.agate\.bak' "$W/refuse.err" | head -1); S2=$(grep -oE 'mkdir -p ~/\.agate' "$W/refuse.err" | head -1); S3=$(grep -oE 'install\.sh --versions' "$W/refuse.err" | head -1)
echo "extracted from install.sh refusal text: [1] $S1 | [2] $S2 | [3] $S3"
( cd "$W/proj"; export HOME="$W/h36"; unset AGATE_ROOT AGATE_HOME
  eval "$S1"; echo "step1 exit=$?"
  eval "$S2"; echo "step2 exit=$?"
  S3ARGS=${S3#install.sh }   # "--versions"
  AGATE_REPO_URL="$UP" bash "$REPO/install.sh" $S3ARGS > "$W/s3.out" 2> "$W/s3.err"; echo "step3 (install.sh $S3ARGS) exit=$?" )
echo "--- ~/.agate after step 3:"; ls -A "$W/h36/.agate" | tr '\n' ' '; echo; ls -l "$W/h36/.agate" | grep -E 'latest|current' | sed 's/.* [0-9:]* //'
[ -d "$W/h36/.agate" ] && [ ! -L "$W/h36/.agate" ] && echo "[PASS] ~/.agate is a real directory"
V=$(readlink "$W/h36/.agate/latest"); echo "version dir: $V"; ls -A "$W/h36/.agate/$V" | tr '\n' ' '; echo
[ -d "$W/h36/.agate/$V/agate/scripts" ] && [ ! -e "$W/h36/.agate/$V/agate/agate" ] && [ ! -e "$W/h36/.agate/$V/.git" ] && echo "[PASS] contract form: agate/scripts present, no agate/agate, no .git"
[ "$(readlink "$W/h36/.agate/current")" = latest ] && echo "[PASS] current -> latest"
[ -f "$W/h36/.agate/scripts/agate-install.py" ] && echo "[PASS] scripts/agate-install.py present"
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h36" python3 "$REPO/agate/scripts/agate-resolve.py"; echo "agate-resolve exit=$?" )
[ -L "$W/h36/.agate.bak" ] && echo "[PASS] .agate.bak is still the original symlink -> $(readlink "$W/h36/.agate.bak" | sed 's#.*/g2-05/##')"
test -f "$W/h36/.agate.bak/scripts/agate-install.py" && echo "[PASS] .agate.bak target intact (agate/scripts present through the link)"
echo "--- rollback by rename only (no deletion): mv ~/.agate ~/.agate.new36; mv ~/.agate.bak ~/.agate"
mv "$W/h36/.agate" "$W/h36/.agate.new36" && mv "$W/h36/.agate.bak" "$W/h36/.agate" && [ -L "$W/h36/.agate" ] && echo "[PASS] back to symlink state (rollback works)"
( cd "$W/proj"; env -u AGATE_ROOT -u AGATE_HOME HOME="$W/h36" python3 "$REPO/agate/scripts/agate-resolve.py" >/dev/null 2>&1; echo "post-rollback resolve exit=$? (1 = fail-closed on symlink shape, as designed)" )
echo "### BDD-29 unknown arg"
bash "$REPO/install.sh" --bogus > "$W/bogus.out" 2>&1; echo "install.sh --bogus exit=$?"; cat "$W/bogus.out"
git -C "$REPO" status --porcelain > "$W/status-after.txt"; cmp -s "$W/status-before.txt" "$W/status-after.txt" && echo "[PASS] source checkout git status unchanged"
