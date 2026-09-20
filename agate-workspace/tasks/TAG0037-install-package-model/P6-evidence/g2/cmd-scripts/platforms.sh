#!/usr/bin/env bash
# BDD-41..45 real SETUP.md command runs. Isolated version layout under $W; HOME real ONLY for opencode/codex reading their own config.
set -u
REPO=/home/kity/oclab/agateon/.worktrees/agate-TAG0037
W=$1; export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$W/home/.agate/v0.73.0" "$W/proj42" "$W/proj43" "$W/home44" "$W/nocur"
git -C "$REPO" archive HEAD agate | tar -x -C "$W/home/.agate/v0.73.0" --exclude='agate/tests'
ln -s v0.73.0 "$W/home/.agate/latest"; ln -s latest "$W/home/.agate/current"
echo "isolated layout: $(ls -A "$W/home/.agate" | tr '\n' ' ')  current -> $(readlink "$W/home/.agate/current") -> $(readlink "$W/home/.agate/latest")"
# extract literal command blocks from SETUP.md (only the block text, executed verbatim)
python3 - "$REPO/agate/SETUP.md" "$W" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read(); W = sys.argv[2]
def block_after(marker, nth=0):
    i = t.index(marker); m = list(re.finditer(r"```bash\n(.*?)```", t[i:], re.S))[nth]; return m.group(1)
open(f"{W}/b41.sh","w").write(block_after("## 先取协议根路径"))
open(f"{W}/b42.sh","w").write(block_after("### Claude Code（`.claude/agents/`）"))
open(f"{W}/b43.sh","w").write(block_after("### OpenCode（`.opencode/agents/`）"))
dsh = block_after("### 步骤 2-DSH")
open(f"{W}/b44.sh","w").write("\n".join(l for l in dsh.splitlines() if "install-hook" not in l))
open(f"{W}/b45.sh","w").write(block_after("**4. 验证接入**：") if "**4. 验证接入**：" in t else "")
PY
for n in 41 42 43 44 45; do echo "--- SETUP block b$n (verbatim):"; cat "$W/b$n.sh"; done
echo
echo "== command availability =="; for c in opencode codex claude; do printf '%s: ' $c; command -v $c || echo MISSING; done

echo; echo "===== BDD-41 ====="
( export HOME="$W/home"; unset AGATE_HOME AGATE_ROOT; bash -c "$(cat "$W/b41.sh"); echo AGATE_DIR=\$AGATE_DIR; [ \"\$AGATE_DIR\" = \"\$HOME/.agate/current/agate\" ] && echo '[PASS] AGATE_DIR == \$HOME/.agate/current/agate'" )
echo "fallback pattern '|| echo \"\$HOME/.agate\"' in SETUP first block: $(grep -c '|| echo "\$HOME/.agate"' "$W/b41.sh")"
echo "--- current missing (HOME without ~/.agate/current):"
( export HOME="$W/nocur"; unset AGATE_HOME AGATE_ROOT; bash -c "$(cat "$W/b41.sh"); echo \"AGATE_DIR after=\$AGATE_DIR\"" ) 2>&1

echo; echo "===== BDD-42 (agate side only; claude CLI not invoked here) ====="
( export HOME="$W/home" AGATE_DIR="$W/home/.agate/current/agate"; cd "$W/proj42"; bash -c "$(cat "$W/b42.sh")"; echo "block exit=$?"
  ls -l .claude/agents/orchestrator.md | sed 's/.* [0-9:]* //'
  test -r .claude/agents/orchestrator.md && echo "[PASS] link target readable"
  echo "link target realpath: $(readlink -f .claude/agents/orchestrator.md)"
  case "$(readlink -f .claude/agents/orchestrator.md)" in "$W"/home/.agate/*) echo "[PASS] target inside isolated AGATE_HOME";; *) echo "[FAILX] target outside isolated home";; esac
  python3 - <<'PY'
import yaml
t = open(".claude/agents/orchestrator.md", encoding="utf-8").read()
assert t.startswith("---"), "no frontmatter"
fm = yaml.safe_load(t.split("---", 2)[1])
print("frontmatter keys:", sorted(fm)); print("name =", repr(fm.get("name")))
print("[PASS] frontmatter yaml.safe_load OK and name: orchestrator" if fm.get("name") == "orchestrator" else "[FAILX] name != orchestrator")
PY
)

echo; echo "===== BDD-43 (real opencode; HOME real for its own config only; AGATE_DIR isolated) ====="
( export AGATE_DIR="$W/home/.agate/current/agate"; unset AGATE_HOME AGATE_ROOT; cd "$W/proj43"
  grep -v '^AGATE_DIR=' "$W/b43.sh" > /dev/null
  bash -c "$(cat "$W/b43.sh")"; echo "block (mkdir+ln) exit=$?"
  ls -l .opencode/agents/orchestrator.md | sed 's/.* [0-9:]* //'
  timeout 90s opencode --version; echo "opencode --version exit=$?"
  timeout 90s opencode debug agent orchestrator > "$W/oc.json" 2> "$W/oc.err"; rc=$?; echo "opencode debug agent orchestrator exit=$rc"
  python3 - "$W/oc.json" <<'PY'
import json, sys
raw = open(sys.argv[1], encoding="utf-8").read()
try:
    d = json.loads(raw)
except Exception as e:
    print("[FAILX] not JSON:", e, raw[:300]); sys.exit(0)
print("mode =", d.get("mode"), "| tools.task =", (d.get("tools") or {}).get("task"), "| name =", d.get("name"))
print("[PASS] mode==primary and tools.task is true" if d.get("mode") == "primary" and (d.get("tools") or {}).get("task") is True else "[FAILX] mode/tools.task mismatch")
PY
)

echo; echo "===== BDD-44 (isolated HOME; DSH CLI absent by design; install-hook line skipped) ====="
( export HOME="$W/home44"; export AGATE_DIR="$W/home/.agate/current/agate"; bash -c "$(cat "$W/b44.sh")"; echo "block exit=$?"
  for f in "$HOME/.dsh/.agent-presets/agate/agent.cordis.yml" "$HOME/.dsh/.agent-presets/agate/preset.yml" "$HOME/.dsh/skills/agate-protocol/SKILL.md"; do
    printf '%s -> ' "${f#$W/}"; readlink "$f" | sed "s#$W/##"; test -r "$f" && echo "   [PASS] readable" || echo "   [FAILX] unreadable"; done
  mkdir -p "$W/proj44"; cd "$W/proj44"
  env -u AGATE_ROOT -u AGATE_HOME HOME="$W/home44" python3 "$W/home/.agate/current/agate/scripts/agate-summary.py" > "$W/sum44.out" 2>&1; echo "agate-summary.py exit=$?"
  grep -nE 'DSH|漂移|drift|未安装' "$W/sum44.out" | head; echo "(grep above: lines mentioning DSH/drift; none = no drift warning)"; grep -qE '漂移|drift' "$W/sum44.out" && echo "[FAILX] drift warning present" || echo "[PASS] no DSH drift warning"
)

echo; echo "===== BDD-45 (real codex; HOME real for its own config only; AGATE_DIR isolated) ====="
( export AGATE_DIR="$W/home/.agate/current/agate"; unset AGATE_HOME AGATE_ROOT
  test -r "$AGATE_DIR/orchestrator-template.md" && echo "[PASS] template readable: ${AGATE_DIR#$W/}/orchestrator-template.md"
  timeout 60s codex --version; echo "codex --version exit=$?"
  timeout 60s codex features list > "$W/codex.out" 2> "$W/codex.err"; rc=$?; echo "timeout 60s codex features list exit=$rc"
  grep -iE 'multi_agent' "$W/codex.out"
  L=$(grep -iE '^multi_agent[[:space:]]' "$W/codex.out" | head -1)
  echo "$L" | grep -qiE '(stable|true)' && echo "[PASS] multi_agent line status is stable/true" || echo "[FAILX] multi_agent status not stable/true: $L"
)
