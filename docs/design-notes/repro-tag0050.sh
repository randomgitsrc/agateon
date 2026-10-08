#!/usr/bin/env bash
# TAG0050 设计 §0 的复现脚本：全部在临时副本上运行，不写真实仓库（AGENTS.md 工作流 0a）。
# 用法：bash repro-tag0050.sh <agateon 仓库根> [peekview 仓库根]
set -uo pipefail
R=$(cd "$1" && pwd); PV=${2:-}
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
cd "$W" && git init -q . && mkdir -p agate-workspace/tasks
export AGATE_ROOT="$R/agate"
S="$R/agate/scripts"; TK=agate-workspace/tasks/T
fresh(){ rm -rf "$TK"; cp -r "$R/agate-workspace/tasks/$1" "$TK"; }
gate(){ timeout 60 python3 "$S/check-gate.py" "$1" "$TK" 2>&1 | tail -1 | cut -c1-150; echo "  check-gate $1 rc=${PIPESTATUS[0]}"; }
prov(){ timeout 60 python3 "$S/check-p6-provenance.py" "$TK" 2>&1 | tail -1 | cut -c1-150; echo "  provenance rc=${PIPESTATUS[0]}"; }

echo "== F1-A：P6 正文 BDD-5 改 FAIL，frontmatter 仍 fail:0"
fresh TAG0001-tech-debt-closure; sed -i 's/^- PASS BDD-5:/- FAIL BDD-5:/' $TK/P6-acceptance.md; gate P6; prov
echo "== F1-B：删 BDD-5 行与其证据，frontmatter 仍 pass:20"
fresh TAG0001-tech-debt-closure; sed -i '/^- PASS BDD-5:/d' $TK/P6-acceptance.md; rm $TK/P6-evidence/bdd-05.log; gate P6; prov
echo "== F1-C：BDD-5 行改写为重复的 BDD-4（BDD-5 未验）"
fresh TAG0001-tech-debt-closure; sed -i 's/^- PASS BDD-5:/- PASS BDD-4:/' $TK/P6-acceptance.md; gate P6; prov

echo "== F2：P7 正文追加 BLOCKER，frontmatter 仍 blocker_count:0"
fresh TAG0037-install-package-model; echo "- [BLOCKER] 示例阻断项" >> $TK/P7-consistency.md; gate P7

echo "== F3a：judge 关闭后，回填/删除 P1 created 即跳过 judge 强制"
fresh TAG0037-install-package-model; sed -i 's/enabled: true/enabled: false/' $TK/.state.yaml
echo "  (原值)"; gate P1
sed -i "s/^created:.*/created: '2026-08-01'/" $TK/P1-requirements.md; echo "  (回填)"; gate P1
sed -i '/^created:/d' $TK/P1-requirements.md; echo "  (删除)"; gate P1

echo "== F3b：P6 阶段把 judge.enabled 改为 false，P6.5 即放行"
fresh TAG0037-install-package-model; rm -f $TK/P6.5-judge-verdict.md
echo "  (judge 开启、无裁决)"; gate P6.5
sed -i 's/enabled: true/enabled: false/' $TK/.state.yaml; echo "  (judge 关闭)"; gate P6.5

echo "== F4：PROD_TOUCHED 安全门正则对各写法的判定（True=拦截）"
python3 - <<'PY'
import re
p = re.compile(r"^\s*-?\s*\[PROD_TOUCHED\]")   # pre-commit-gate.py 现行判据
for s in ["- [PROD_TOUCHED] 已连生产库", "**[PROD_TOUCHED]** 已连生产库", "> [PROD_TOUCHED] 已连生产库",
          "* [PROD_TOUCHED] 已连生产库", "- [PROD_TOUCHED]: 无"]:
    print(f"  {bool(p.match(s))!s:5} {s}")
PY

echo "== F8：append_event 调用元数错误（pre-commit-gate.py PAUSED 留痕分支）"
python3 -c "
import sys; sys.path.insert(0, '$S'); import agate_common as a
try: a.append_event('$W', 'prod_touched_in_paused', {'task_id': 'x'})
except TypeError as e: print('  TypeError:', e)"

echo "== F5：语料中「否定写法被计为声明」（registry 判据 agate_markers.pattern）"
for repo in "$R" ${PV:+"$PV"}; do
python3 - "$repo" "$S" <<'PY'
import sys, glob, re
repo, s = sys.argv[1], sys.argv[2]; sys.path.insert(0, s)
import agate_markers as m
neg = re.compile(r"(无|none|n/?a|没有|不涉及|未触发)", re.I)
files = [f for f in glob.glob(f"{repo}/agate-workspace/tasks/*/P*.md") if "dispatch-" not in f]
print(f"  {repo.rsplit('/',1)[-1]}: {len(files)} 个产出文件")
for n in m.names():
    p = m.pattern(n); hits = negs = 0; ex = ""
    for f in files:
        for line in open(f, encoding="utf-8", errors="replace"):
            if p.search(line):
                hits += 1
                if neg.search(line.split("]", 1)[-1][:12]):
                    negs += 1; ex = ex or line.strip()[:60]
    print(f"    {n:20} 声明行={hits:4} 否定样={negs:3} {ex}")
PY
done

echo "== F9：P6-acceptance.md 引用的 .log 在克隆中缺失（任务目录或 P6-evidence/ 下均找不到）"
for repo in "$R" ${PV:+"$PV"}; do
python3 - "$repo" <<'PY'
import glob, re, os, sys
repo = sys.argv[1]; refs = miss = 0; tasks = set(); ex = None
for p6 in glob.glob(f"{repo}/agate-workspace/tasks/*/P6-acceptance.md"):
    td = os.path.dirname(p6)
    for tok in set(re.findall(r"[\w./-]+\.log\b", open(p6, encoding="utf-8", errors="replace").read())):
        refs += 1
        cands = [os.path.join(td, tok), os.path.join(td, "P6-evidence", tok), os.path.join(td, "P6-evidence", os.path.basename(tok))]
        if not any(os.path.isfile(c) for c in cands):
            miss += 1; tasks.add(td); ex = ex or os.path.relpath(os.path.join(td, "P6-evidence", os.path.basename(tok)), repo)
print(f"  {repo.rsplit('/',1)[-1]}: 引用 {refs}，缺失 {miss}，涉及任务 {len(tasks)}")
if ex: print("EX", ex)
PY
done > "$W/f9.txt"; grep -v '^EX' "$W/f9.txt"
if [ -n "$PV" ]; then
  ex=$(grep '^EX' "$W/f9.txt" | tail -1 | cut -c4-)
  echo "  peekview 缺失样例的忽略规则：$(cd "$PV" && git check-ignore -v "$ex" || echo 未忽略)"
fi

echo "== F12：P8 delivery 子串判定——删字段、正文提及即放行"
fresh TAG0042-config-and-enforcement 2>/dev/null && {
  python3 - "$TK/P8-release.md" <<'PY'
import sys, re; p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r"(?m)^delivery:.*\n", "", s); s += "\n> 备注：本任务暂不声明 delivery: 方式，待定。\n"
open(p, "w", encoding="utf-8").write(s)
PY
  gate P8; } || echo "  (该基线无 TAG0042，跳过)"

echo "== F13：obligations.yaml 中 M 项的 script 不在 hook/check-gate 调用集合内"
[ -f "$R/agate/rules/obligations.yaml" ] && python3 - "$R/agate" <<'PY' || echo "  (该基线无 obligations.yaml，跳过)"
import sys, yaml, re, os
a = sys.argv[1]; d = yaml.safe_load(open(f"{a}/rules/obligations.yaml", encoding="utf-8"))
src = open(f"{a}/scripts/pre-commit-gate.py", encoding="utf-8").read() + open(f"{a}/scripts/check-gate.py", encoding="utf-8").read()
invoked = set(re.findall(r'"([\w-]+\.py)"', src)) | {"check-gate.py", "pre-commit-gate.py", "commit-msg-self-gate.py", "pre-push-gate.py"}
m = [o for o in d["obligations"] if o["disposition"] == "M"]
off = [(o["id"], o["script"]) for o in m if not any(n in invoked for n in re.findall(r"[\w.-]+\.py", o.get("script") or ""))]
print(f"  M 项 {len(m)} 条，script 不在必经路径 {len(off)} 条: {off}")
PY

echo "== F15：agate-ci-verify 在多任务仓库上的行为"
if [ -f "$R/agate/scripts/agate-ci-verify.py" ]; then
  C=$(mktemp -d); git clone -q "$R" "$C/r" 2>/dev/null && ( cd "$C/r" && timeout 120 python3 agate/scripts/agate-ci-verify.py 2>&1 | grep -E "SKIP|PASS|FAIL" | head -1; echo "  rc=${PIPESTATUS[0]}  任务目录数=$(ls -d agate-workspace/tasks/*/ | wc -l)" ); rm -rf "$C"
else echo "  (该基线无 agate-ci-verify，跳过)"; fi

echo "== T1：存量语料中会被 T1 绊线命中的行（default 口径，正向标记，排除围栏/卡片/行内代码/反引号起首行）"
for repo in "$R" ${PV:+"$PV"}; do
python3 - "$repo" "$R/agate/rules/markers.yaml" <<'PY'
import sys, glob, re, os, yaml
repo, mk = sys.argv[1], sys.argv[2]
lead = yaml.safe_load(open(mk, encoding="utf-8"))["lead"]
pos = ["SCOPE+", "SCOPE_RESOLVED", "DESIGN_GAP", "DESIGN_GAP_REVIEWED", "NEED_CONFIRM", "SUGGEST", "PROD_TOUCHED",
       "BLOCKER", "DEVIATION-CRITICAL", "CODE_MAP_UPDATED", "CODE_MAP_EXEMPT"]
pat = re.compile(lead + r"\[(" + "|".join(re.escape(n) for n in pos) + r")[\]:]")
fence = re.compile(r"^\s*(```|~~~)"); hits = 0; tasks = set()
for f in glob.glob(f"{repo}/agate-workspace/tasks/*/**/*.md", recursive=True):
    b = os.path.basename(f)
    if not (re.match(r"P\d(\.5)?-", b) or "/P4-implementation/" in f): continue
    if re.search(r"dispatch-(context|prompt)|progress|exit2-resolution", b): continue
    inf = incard = False
    for line in open(f, encoding="utf-8", errors="replace"):
        if "AGATE_CARD_START" in line: incard = True; continue
        if "AGATE_CARD_END" in line: incard = False; continue
        if fence.match(line): inf = not inf; continue
        if inf or incard or line.lstrip().startswith("`"): continue
        if pat.match(re.sub(r"`[^`]*`", "", line)):
            hits += 1; tasks.add(f.split("/tasks/")[1].split("/")[0])
print(f"  {os.path.basename(repo.rstrip('/'))}: 命中 {hits} 行，涉及 {len(tasks)} 个任务")
PY
done

echo "== F3c：证据引用强制按 P1 created 判定——回填 created 即降为 WARNING"
if [ -d "$R/agate-workspace/tasks/TAG0042-config-and-enforcement" ]; then
  ev(){ out=$(timeout 60 python3 "$S/check-p6-evidence.py" "$TK" 2>&1); rc=$?; printf '%s\n' "$out" | grep -E "未能提取" | head -1 | cut -c1-110; echo "  check-p6-evidence rc=$rc（1=阻断，2=仅 WARNING）"; }
  fresh TAG0042-config-and-enforcement
  python3 - "$TK/P6-acceptance.md" <<'PY'
import sys, re; p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r"(?m)^(- PASS BDD-0?1:.*?)\s*\([^()]*\)\s*$", r"\1", s, count=1)   # 去掉 BDD-1 行尾的证据括号组
open(p, "w", encoding="utf-8").write(s)
PY
  echo "  (created 原值 2026-10-05)"; ev
  sed -i "s/^created:.*/created: 2026-10-01/" $TK/P1-requirements.md; echo "  (created 回填为 2026-10-01)"; ev
else echo "  (该基线无 TAG0042，跳过)"; fi

echo "== F15b：agate-ci-verify 单任务时按 tasks/<task_id> 拼路径 → 假 PASS"
if [ -f "$R/agate/scripts/agate-ci-verify.py" ]; then
  C=$(mktemp -d); git clone -q "$R" "$C/r" 2>/dev/null && (
    cd "$C/r"; for d in agate-workspace/tasks/*/; do case "$d" in *TAG0037*) ;; *) rm -rf "$d";; esac; done
    T37=$(ls -d agate-workspace/tasks/TAG0037*); sed -i 's/^phase:.*/phase: P7/' "$T37/.state.yaml"; rm -f "$T37/P7-consistency.md"
    echo "  ci-verify: $(timeout 120 python3 agate/scripts/agate-ci-verify.py 2>&1 | grep -E 'SKIP|PASS|FAIL' | head -1 | cut -c1-80)"
    timeout 60 python3 agate/scripts/check-gate.py P7 "$T37" >/dev/null 2>&1; echo "  check-gate P7 <真实目录> rc=$?"
    timeout 60 python3 agate/scripts/check-gate.py P7 agate-workspace/tasks/TAG0037 >/dev/null 2>&1; echo "  check-gate P7 tasks/TAG0037 rc=$?"
  ); rm -rf "$C"
fi

echo "== 协议文档中提及标记的行数（agate/**/*.md，上界口径）"
grep -rhcE "\[(SCOPE\+|SCOPE_RESOLVED|DESIGN_GAP|NEED_CONFIRM|SUGGEST:|NO_NEED_CONFIRM|PROD_TOUCHED|PROD_NOT_TOUCHED|BLOCKER|DEVIATION-CRITICAL|CODE_MAP_UPDATED|CODE_MAP_EXEMPT)" "$R/agate" --include=*.md | paste -sd+ | bc | sed 's/^/  行数 /'
grep -rlE "\[(SCOPE\+|SCOPE_RESOLVED|DESIGN_GAP|NEED_CONFIRM|SUGGEST:|NO_NEED_CONFIRM|PROD_TOUCHED|PROD_NOT_TOUCHED|BLOCKER|DEVIATION-CRITICAL|CODE_MAP_UPDATED|CODE_MAP_EXEMPT)" "$R/agate" --include=*.md | wc -l | sed 's/^/  文件数 /'
