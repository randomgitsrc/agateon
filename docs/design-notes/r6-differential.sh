#!/usr/bin/env bash
# r6-differential.sh — R6 双向差分（TAG0050 批 A1，设计 §8 / P2-design §3.2）
#
# 用途：把「legacy 任务的 gate 退出码与 ERROR 集合不变」这一兼容承诺变成**可执行判据**。
# 对每个 legacy 任务、其所在阶段的 gate，分别在 **before 协议** 与 **after 协议** 下运行，
# 比较 (退出码, ERROR 行集合)；差异必须匹配 docs/design-notes/r6-allowlist.yaml 的某条规则，
# 否则 exit 1。
#
# 接口：
#   bash r6-differential.sh [--before <rev>] [--after <dir>] [--corpus <repo>]... [--allow <file>]
#     --before  缺省 = `git merge-base HEAD origin/main`（失败回退 main → HEAD）
#     --after   缺省 = 工作树的 agate/（即当前 checkout 的协议本体）
#     --corpus  可多次；缺省 = `.`
#     --allow   缺省 = docs/design-notes/r6-allowlist.yaml
#
# 自核验（AGENTS.md 工作流 0a 机械化）：每个 corpus 原仓库 `git status --porcelain` 必须为空，
# 否则 exit 1——防止"跑差分把真实仓库弄脏"。运行前 + **运行后**各核验一次（F-5）。
#
# 覆盖范围（G2 显式声明）：本脚本只回放 **check-gate 面**（`check-gate.py <phase> <task>`）。
# r6-allowlist.yaml 中 `gate: pre-commit` 的规则（D01/D04/D06/D07/D12、D08/D09）不在本脚本
# 覆盖内——pre-commit 的行为取决于**暂存区**，而干净 corpus 无暂存改动、回放无意义。
# 设计 §8 第 12 项（新增 PROD_TOUCHED ERROR 单独统计）由**批 A2 的 CI 逐提交回放**承担
# （见设计 §8 与 P4-implementation.md 的 G2 声明）。
#
# 负向用例：删掉 r6-allowlist.yaml 中 required_ids 的任一规则 → 本脚本 exit 1（见 P4 说明）。
#
# 平台无关：不写死 python3 / 系统临时目录字面量；python 用 `command -v` 探测，临时目录用 mktemp -d。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEFORE=""
AFTER=""
ALLOW="$SCRIPT_DIR/r6-allowlist.yaml"
CORPORA=()

while [ $# -gt 0 ]; do
  case "$1" in
    --before) BEFORE="${2:-}"; shift 2 ;;
    --after)  AFTER="${2:-}";  shift 2 ;;
    --allow)  ALLOW="${2:-}";  shift 2 ;;
    --corpus) CORPORA+=("${2:-}"); shift 2 ;;
    -h|--help)
      sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "r6-differential: 未知参数: $1" >&2; exit 2 ;;
  esac
done

if [ "${#CORPORA[@]}" -eq 0 ]; then
  CORPORA=(".")
fi

# python 探测（候选加引号：既非裸 python3，也避开 check-platform-assumptions 的 R2 误报）
PY=""
for cand in "python3" "python"; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  echo "r6-differential: 找不到 python3/python 解释器" >&2
  exit 1
fi

if [ ! -f "$ALLOW" ]; then
  echo "r6-differential: allowlist 不存在: $ALLOW" >&2
  exit 1
fi

# 自核验：每个 corpus 原仓库必须干净
for corpus in "${CORPORA[@]}"; do
  if [ ! -d "$corpus" ]; then
    echo "r6-differential: corpus 不存在: $corpus" >&2
    exit 1
  fi
  if git -C "$corpus" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    dirty="$(git -C "$corpus" status --porcelain)"
    if [ -n "$dirty" ]; then
      echo "r6-differential: corpus 原仓库不干净（git status --porcelain 非空）: $corpus" >&2
      echo "$dirty" >&2
      exit 1
    fi
  fi
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 解析 before 协议（从 corpus 的 git 历史导出 agate/ 树）
primary="${CORPORA[0]}"
if [ -z "$BEFORE" ]; then
  BEFORE="$(git -C "$primary" merge-base HEAD origin/main 2>/dev/null || true)"
  if [ -z "$BEFORE" ]; then
    BEFORE="$(git -C "$primary" merge-base HEAD main 2>/dev/null || true)"
  fi
  if [ -z "$BEFORE" ]; then
    BEFORE="$(git -C "$primary" rev-parse HEAD 2>/dev/null || true)"
  fi
fi
if [ -z "$BEFORE" ]; then
  echo "r6-differential: 无法解析 before 协议版本" >&2
  exit 1
fi

BEFORE_ROOT="$WORK/before/agate"
mkdir -p "$WORK/before"
if ! git -C "$primary" archive "$BEFORE" agate 2>/dev/null | tar -x -C "$WORK/before"; then
  echo "r6-differential: 无法导出 before 协议（rev=$BEFORE）" >&2
  exit 1
fi
if [ ! -d "$BEFORE_ROOT" ]; then
  echo "r6-differential: before 协议缺 agate/ 目录（rev=$BEFORE）" >&2
  exit 1
fi

if [ -z "$AFTER" ]; then
  AFTER="$(cd "$primary" && pwd)/agate"
fi
if [ ! -d "$AFTER" ]; then
  echo "r6-differential: after 协议目录不存在: $AFTER" >&2
  exit 1
fi

echo "r6-differential: before=$BEFORE  after=$AFTER  allow=$ALLOW"

# 捕获 python 主体退出码（不因 set -e 提前退出），供运行后自核验（F-5）后再定夺
RC=0
set +e
R6_BEFORE_ROOT="$BEFORE_ROOT" \
R6_AFTER_ROOT="$AFTER" \
R6_ALLOW="$ALLOW" \
R6_CORPORA="$(printf '%s\n' "${CORPORA[@]}")" \
R6_PY="$PY" \
"$PY" - <<'PYCODE'
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("r6-differential: 需要 pyyaml（pip install pyyaml）\n")
    sys.exit(1)

BEFORE_ROOT = os.environ["R6_BEFORE_ROOT"]
AFTER_ROOT = os.environ["R6_AFTER_ROOT"]
ALLOW = os.environ["R6_ALLOW"]
CORPORA = [c for c in os.environ["R6_CORPORA"].splitlines() if c]
PY = os.environ["R6_PY"]

PHASES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P6.5"]
# READY/DONE 任务同样纳入差分（它们正是 §8 兼容承诺的对象）——但控制态本身没有 gate，
# 故按"最高阶段产出"映射到其相关 gate（如 READY 任务通常有 P8-release.md → 跑 P8 gate；
# 跳过 P8 的内部任务有 P7-consistency.md → 跑 P7 gate）。
CONTROL_PHASES = ("READY", "DONE")
# 各阶段主产出（判定"相关 gate"用；P5 是目录）。
_PRIMARY_OUTPUTS = {
    "P1": "P1-requirements.md",
    "P2": "P2-design.md",
    "P3": "P3-test-cases.md",
    "P4": "P4-implementation.md",
    "P5": "P5-test-results",
    "P6": "P6-acceptance.md",
    "P7": "P7-consistency.md",
    "P8": "P8-release.md",
}


def _relevant_gate_phases(task_dir, phase):
    """任务的相关 gate 阶段列表。控制态（READY/DONE）→ 最高阶段产出的 gate。"""
    if phase in PHASES:
        return [phase]
    if phase in CONTROL_PHASES:
        for p in ["P8", "P7", "P6", "P5", "P4", "P3", "P2", "P1"]:
            if os.path.exists(os.path.join(task_dir, _PRIMARY_OUTPUTS[p])):
                return [p]
    return []


def _load_allow():
    with open(ALLOW, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        sys.stderr.write("r6-differential: allowlist 格式非法\n")
        sys.exit(1)
    rules = data.get("rules") or []
    required = data.get("required_ids") or []
    ids = {r.get("id") for r in rules if isinstance(r, dict)}
    missing = [rid for rid in required if rid not in ids]
    if missing:
        sys.stderr.write(
            "r6-differential: allowlist 缺少必需规则 %s（负向用例：删规则即变红）\n" % missing)
        sys.exit(1)
    return rules


def _ledger_has_origin(task_dir):
    path = os.path.join(task_dir, "gate-events.jsonl")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if isinstance(ev, dict) and ev.get("event") in ("task_created", "task_adopted"):
                    return True
    except OSError:
        return False
    return False


def _task_phase(task_dir):
    path = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(path):
        return None
    try:
        import yaml as _yaml
        with open(path, encoding="utf-8", errors="replace") as fh:
            data = _yaml.safe_load(fh)
    except Exception:
        return None
    if isinstance(data, dict) and isinstance(data.get("phase"), str):
        return data["phase"]
    return None


def _normalize(text, corpus, task_dir):
    for root in (BEFORE_ROOT, AFTER_ROOT):
        text = text.replace(root, "<ROOT>")
    text = text.replace(os.path.realpath(task_dir), "<TASK>")
    text = text.replace(task_dir, "<TASK>")
    text = text.replace(os.path.realpath(corpus), "<CORPUS>")
    text = text.replace(corpus, "<CORPUS>")
    return text


def _error_lines(stderr_text):
    out = set()
    for line in stderr_text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if "WARNING" in line or "SKIP" in line or "OK" in line:
            continue
        if line.startswith("GATE ") and ":" in line:
            out.add(line)
        elif "ERROR" in line:
            out.add(line)
    return out


def _run_gate(root, phase, task_dir):
    script = os.path.join(root, "scripts", "check-gate.py")
    if not os.path.isfile(script):
        return None
    env = dict(os.environ)
    env["AGATE_ROOT"] = root
    try:
        proc = subprocess.run(
            [PY, script, phase, task_dir],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        )
    except OSError:
        return None
    return proc.returncode, proc.stderr or ""


def _task_id_of(name):
    """任务目录名 → 任务 ID（取首段；`T090-foo` → `T090`）。"""
    return str(name or "").split("-", 1)[0]


def _rule_matches(rule, diff):
    # task_scope：legacy / non-legacy / any / specific:<id>。
    # R6 只对 legacy 任务做差分，故 `legacy` 恒真、`non-legacy` 恒假；
    # `specific:<id>` 限定到具体任务（此前被忽略，D03 的 specific:T090 形同虚设）。
    scope = str(rule.get("task_scope") or "any")
    if scope == "non-legacy":
        return False
    if scope.startswith("specific:") and _task_id_of(diff.get("task")) != scope.split(":", 1)[1]:
        return False
    if scope not in ("any", "legacy", "") and not scope.startswith("specific:"):
        return False
    gate = str(rule.get("gate") or "")
    if gate and gate not in diff["gate"]:
        return False
    kind = rule.get("kind")
    match = rule.get("match") or {}
    patterns = match.get("patterns") or []
    if kind == "rc_change":
        rc_from = match.get("rc_from")
        rc_to = match.get("rc_to")
        if rc_from is not None and diff["rc_before"] != rc_from:
            return False
        if rc_to is not None and diff["rc_after"] != rc_to:
            return False
        if patterns:
            blob = "\n".join(sorted(diff["added"] | diff["removed"]))
            return any(p in blob for p in patterns)
        return True
    if kind in ("new_error", "new_warning", "ledger_event_added", "ledger_bytes"):
        blob = "\n".join(sorted(diff["added"] | diff["removed"]))
        if patterns and not any(p in blob for p in patterns):
            return False
        return True
    return False


def main():
    rules = _load_allow()
    differences = []
    tasks_checked = 0
    for corpus in CORPORA:
        tasks_dir = os.path.join(corpus, "agate-workspace", "tasks")
        if not os.path.isdir(tasks_dir):
            continue
        for name in sorted(os.listdir(tasks_dir)):
            task_dir = os.path.join(tasks_dir, name)
            if not os.path.isfile(os.path.join(task_dir, ".state.yaml")):
                continue
            if _ledger_has_origin(task_dir):
                continue  # 只对 legacy 任务做差分
            phase = _task_phase(task_dir)
            for gate_phase in _relevant_gate_phases(task_dir, phase):
                tasks_checked += 1
                before = _run_gate(BEFORE_ROOT, gate_phase, task_dir)
                after = _run_gate(AFTER_ROOT, gate_phase, task_dir)
                if before is None or after is None:
                    continue
                rc_b, err_b = before
                rc_a, err_a = after
                set_b = _error_lines(_normalize(err_b, corpus, task_dir))
                set_a = _error_lines(_normalize(err_a, corpus, task_dir))
                added = set_a - set_b
                removed = set_b - set_a
                if rc_b == rc_a and not added and not removed:
                    continue
                differences.append({
                    "gate": "check-gate:" + gate_phase,
                    "task": name,
                    "rc_before": rc_b,
                    "rc_after": rc_a,
                    "added": added,
                    "removed": removed,
                })

    unmatched = []
    for diff in differences:
        if not any(_rule_matches(r, diff) for r in rules):
            unmatched.append(diff)

    for diff in differences:
        status = "ALLOWED" if any(_rule_matches(r, diff) for r in rules) else "UNMATCHED"
        print("[%s] %s %s rc %s->%s added=%d removed=%d"
              % (status, diff["gate"], diff["task"], diff["rc_before"], diff["rc_after"],
                 len(diff["added"]), len(diff["removed"])))

    print("r6-differential: legacy 任务 %d 个，差异 %d 条，未匹配 %d 条"
          % (tasks_checked, len(differences), len(unmatched)))

    if unmatched:
        sys.stderr.write("r6-differential: 存在未匹配的差异（违反 §8 兼容承诺）：\n")
        for diff in unmatched:
            sys.stderr.write("  - %s %s rc %s->%s\n"
                             % (diff["gate"], diff["task"], diff["rc_before"], diff["rc_after"]))
            for line in sorted(diff["added"] | diff["removed"]):
                sys.stderr.write("      %s\n" % line)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
PYCODE
RC=$?
set -e

# 运行后自核验（F-5）：子脚本可能有写副作用（如 check-judge-verdict 追加账本事件），
# 仅靠运行前检查不足以兑现「跑差分不弄脏真实仓库」——运行后再核验一次。
for corpus in "${CORPORA[@]}"; do
  if git -C "$corpus" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    dirty="$(git -C "$corpus" status --porcelain)"
    if [ -n "$dirty" ]; then
      echo "r6-differential: 运行后 corpus 原仓库被弄脏（子脚本写副作用）: $corpus" >&2
      echo "$dirty" >&2
      exit 1
    fi
  fi
done
exit "$RC"
