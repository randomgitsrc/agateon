#!/usr/bin/env bash
# BDD-31/32/33 real-invocation evidence: 5 base variants x entries. Isolated under $W.
set -u
REPO=/home/kity/oclab/agateon/.worktrees/agate-TAG0037
W=$1; BUNDLE=$2
export PYTHONDONTWRITEBYTECODE=1
SHIM=/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/g1-04-offline/shim
mkdir -p "$W/bin" "$W/home"
# git wrapper that logs every invocation (proves no clone happened)
cat > "$W/bin/git" <<G
#!/usr/bin/env bash
echo "\$*" >> "$W/git-calls.log"
exec /usr/bin/git "\$@"
G
chmod +x "$W/bin/git"
snap() { (cd "$1" && find . -printf '%p %y %s\n' | sort); }
variants=(L 'L/' 'L//' 'L/.' 'L/..')
fail=0
run_case() { # name entry-cmd...
  local name=$1; shift
  for v in "${variants[@]}"; do
    local d="$W/case-$name-$(echo "$v" | tr '/.' '_d')"
    mkdir -p "$d/deep/target/scripts" "$d/deep/target/assets" "$d/home"
    echo canary > "$d/deep/target/scripts/canary.txt"
    ln -s "$d/deep/target" "$d/L"
    local base="$d/$v"
    snap "$d/deep" > "$d/before.txt"
    : > "$W/git-calls.log"
    local out rc
    out=$( cd "$d" && HOME="$d/home" AGATE_HOME="$base" AGATE_REPO_URL="file:///nonexistent-upstream-$$" PATH="$W/bin:$SHIM:$PATH" "$@" 2>&1 >/dev/null ); rc=$?
    snap "$d/deep" > "$d/after.txt"
    local same=YES; cmp -s "$d/before.txt" "$d/after.txt" || same=NO
    local gitn; gitn=$(wc -l < "$W/git-calls.log")
    local steps=NO; grep -q 'mv ~/.agate ~/.agate.bak' <<<"$out" && grep -q 'mkdir -p ~/.agate' <<<"$out" && grep -q 'install' <<<"$out" && steps=YES
    local dotdot=""; [ "$v" = 'L/..' ] && dotdot=" (L/.. : stderr mentions '..' = $(grep -c '\.\.' <<<"$out" | tr -d '\n') lines)"
    local ok=PASS; [ "$rc" = 1 ] && [ "$same" = YES ] && [ "$gitn" = 0 ] || ok=FAILX
    [ "$v" != 'L/..' ] && [ "$steps" != YES ] && ok=FAILX
    [ "$v" = 'L/..' ] && ! grep -q '\.\.' <<<"$out" && ok=FAILX
    echo "[$ok] $name AGATE_HOME=<L>${v#L}: rc=$rc target-and-parent-listing-unchanged=$same git-invocations=$gitn three-step-fragments=$steps$dotdot"
    [ "$ok" = PASS ] || fail=1
    if [ "$ok" != PASS ]; then echo "   stderr: $out" | head -8; fi
  done
}
echo "== BDD-31: install.sh =="
run_case 31-noargs bash "$REPO/install.sh"
run_case 31-versions bash "$REPO/install.sh" --versions
echo "== BDD-32: agate-install.py =="
run_case 32-noargs python3 "$REPO/agate/scripts/agate-install.py"
run_case 32-latest python3 "$REPO/agate/scripts/agate-install.py" latest
run_case 32-version python3 "$REPO/agate/scripts/agate-install.py" v0.72.0
echo "== BDD-33: install-offline.py (AGATE_HOME symlink) =="
run_case 33-agatehome python3 "$REPO/agate/scripts/install-offline.py" "$BUNDLE" --skip-python --skip-pillow
echo "== BDD-33: install-offline.py --dest-root symlink =="
run_case 33-destroot bash -c 'exec python3 "'"$REPO"'/agate/scripts/install-offline.py" "'"$BUNDLE"'" --skip-python --skip-pillow --dest-root "$AGATE_HOME"'
echo "== BDD-33 not-misfire: regular --dest-root (existing dir / new dir) =="
for k in existing new; do
  d="$W/reg-$k"; mkdir -p "$d/home"; [ $k = existing ] && mkdir -p "$d/dest"
  out=$(cd "$d" && HOME="$d/home" PATH="$SHIM:$PATH" python3 "$REPO/agate/scripts/install-offline.py" "$BUNDLE" --skip-python --skip-pillow --dest-root "$d/dest" 2>&1); rc=$?
  echo "[$( [ $rc = 0 ] && echo PASS || echo FAILX )] regular dest-root ($k): rc=$rc; dest listing: $(ls "$d/dest" | tr '\n' ' ')"
  [ $rc = 0 ] || { fail=1; echo "$out" | tail -5; }
done
echo "OVERALL_FAIL=$fail"
exit $fail
