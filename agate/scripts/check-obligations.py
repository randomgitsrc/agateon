#!/usr/bin/env python3
"""check-obligations.py — 义务三态归宿登记校验（TAG0042 批6；TAG0050 批 A4 机械核验）

读取 agate/rules/obligations.yaml（阶段义务三态归宿登记表），校验：

  1. 每条义务有明确三态归宿（M 脚本执行 / C 命令生成 / R 强制评审）——无「无归宿」项；
  2. M 类占比 ≥ 基线（只增不减，下降即 FAIL；支持一次性 `baseline.reset` 显式重设）；
  3. 每条义务有可追溯来源锚点（anchor 非空）与义务陈述（statement 非空）；
  4. **M 义务的执行方式由机械核验**（TAG0050 批 A4，修复 F13）：
     ① `enforced_at.function` 存在于 `file`（ast）；
     ② 该函数可从**必经路径**入口到达（`pre-commit-gate.py` / `commit-msg-self-gate.py` /
        `pre-push-gate.py` / `check-gate.py` 的 `main`，按字面量脚本名做闭包）；
     ③ 若填了 `call`，同一 `ast.Call` 节点参数须含全部字面量；
     ④ `test` 指向的 pytest 节点须存在且测试文件引用该义务 id；
     ⑤ R 义务的 `review_output` 须是合格评审产出（P1/P2/P4-review.md）。
  5. `scope: protocol-repo` 的义务（CI/手工执行）单独统计，**不计入 M 占比**；
     其执行方式性质为「—」（设计 §2.9）——**跳过** ①–④ 的必经路径/凭证核验。

判定：无归宿项为空 且 无 ERROR 且 M 类占比 ≥ 有效基线 → exit 0；否则 exit 1。
本脚本承载 gate 判定逻辑（有 exit code）⇒ 已登记进 check-protocol-consistency.py 的
SCRIPT_ALIGNMENT_ANCHORS 锚点表（锚点 keywords 定值：["obligations.yaml", "M 类占比",
"无归宿"]，三者须在本脚本文本中字面出现）。

用法：
  check-obligations.py            默认：读 AGATE_ROOT/rules/obligations.yaml

退出码：
  0 = 通过；1 = 不通过；2 = 用法或目标错误（obligations.yaml 缺失 / YAML 不可解析）

平台无关：纯文本读取 + pyyaml + ast；无裸解释器名、无硬编码 PATH、无临时目录字面量、
无软链假设；文本 I/O 显式 utf-8；Python 3.8+（无 match / str.removeprefix）。
"""

import ast
import contextlib
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("check-obligations.py: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(2)

VALID_DISPOSITIONS = ("M", "C", "R")
# 必经路径入口：hook 主程序 + check-gate（设计 §2.9）
_ENTRY_SCRIPTS = ("pre-commit-gate.py", "commit-msg-self-gate.py", "pre-push-gate.py",
                  "check-gate.py")
# 合格评审产出（check-gate 会校验其存在且 agent ≠ main）
_QUALIFIED_REVIEW_OUTPUTS = ("P1-review.md", "P2-review.md", "P4-review.md")
_SCRIPT_CALLERS = ("_run_script_rc", "_run_script_capture")
_PY_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+\.py$")
_SCOPE_PROTOCOL = "protocol-repo"


def _has_obligations(root):
    """root 下是否存在 rules/obligations.yaml。"""
    return bool(root) and os.path.isfile(os.path.join(root, "rules", "obligations.yaml"))


def _resolve_root():
    """定位协议根（含 rules/obligations.yaml）。

    候选顺序：AGATE_ROOT env → 脚本所在协议根（脚本上溯一层）→ 当前工作目录。
    脚本相对优先，保证开发 checkout 与安装版本布局都能定位到**本脚本同源的**登记表。
    """
    env_root = os.environ.get("AGATE_ROOT", "")
    if _has_obligations(env_root):
        return env_root

    script_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _has_obligations(script_root):
        return script_root

    cwd = os.path.abspath(os.getcwd())
    if _has_obligations(cwd):
        return cwd
    if _has_obligations(os.path.join(cwd, "agate")):
        return os.path.join(cwd, "agate")

    return script_root


def _load(path):
    """读 YAML（utf-8）；不可解析 → None。"""
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except OSError:
        return None
    except yaml.YAMLError:
        return None


def _is_int(value):
    """整数判定（bool 是 int 子类，须排除）。"""
    return isinstance(value, int) and not isinstance(value, bool)


# ---------- 必经路径可达性（ast 闭包） ----------

def _script_refs_in_node(node):
    """node 内字面量脚本引用：`_run_script_rc/_capture("x.py", …)` 首参 +
    `os.path.join(SCRIPT_DIR, "x.py")`。"""
    refs = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        fname = None
        if isinstance(sub.func, ast.Name):
            fname = sub.func.id
        elif isinstance(sub.func, ast.Attribute):
            fname = sub.func.attr
        if fname in _SCRIPT_CALLERS and sub.args:
            a0 = sub.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str) \
                    and _PY_NAME_RE.match(a0.value):
                refs.add(a0.value)
        # os.path.join(SCRIPT_DIR, "x.py")
        if (fname == "join" and len(sub.args) >= 2
                and isinstance(sub.args[0], ast.Name) and sub.args[0].id == "SCRIPT_DIR"
                and isinstance(sub.args[1], ast.Constant)
                and isinstance(sub.args[1].value, str)
                and _PY_NAME_RE.match(sub.args[1].value)):
            refs.add(sub.args[1].value)
    return refs


def _local_calls_in_node(node, local_names):
    """node 内引用的本地函数名：直接调用 + 作为 `handlers` 表等映射值/引用的 `Name`
    （设计 §2.9：`gate_pN` 经 `handlers` 表分派，故字典值引用也算可达）。"""
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in local_names:
            out.add(sub.id)
    return out


def _reachable_set(scripts_dir):
    """从必经路径入口做 ast 闭包 → 可达 (script_basename, function_name) 集合。

    规则：函数体内的 `_run_script_*("x.py")` / `os.path.join(SCRIPT_DIR, "x.py")` 视为
    调用 x.py 的 `main`；本地函数调用沿文件内调用图展开。字面量出现在**消息字符串**中
    不算调用（不是脚本执行参数）。
    """
    trees = {}
    funcs = {}       # basename -> {func_name: node}
    for name in sorted(os.listdir(scripts_dir)):
        if not name.endswith(".py"):
            continue
        try:
            with open(os.path.join(scripts_dir, name), encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src)
        except Exception:
            continue
        trees[name] = tree
        funcs[name] = {
            n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        }

    reachable = set()
    worklist = []
    for entry in _ENTRY_SCRIPTS:
        if entry in funcs and "main" in funcs[entry]:
            worklist.append((entry, "main"))
    while worklist:
        script, fn = worklist.pop()
        if (script, fn) in reachable:
            continue
        reachable.add((script, fn))
        node = funcs.get(script, {}).get(fn)
        if node is None:
            continue
        for ref in _script_refs_in_node(node):
            if ref in funcs:
                worklist.append((ref, "main"))
        for callee in _local_calls_in_node(node, set(funcs.get(script, {}))):
            worklist.append((script, callee))
    return reachable


def _check_enforced_at(item, oid, reachable, errors):
    """M 义务的 enforced_at：function 存在（ast）+ 可从必经路径到达 + call 字面量。"""
    ea = item.get("enforced_at")
    if not isinstance(ea, dict):
        errors.append(f"{oid}: M 义务缺 enforced_at（机械落点）")
        return
    fname = str(ea.get("file") or "")
    func = str(ea.get("function") or "")
    if not fname or not func:
        errors.append(f"{oid}: enforced_at 缺 file / function")
        return
    base = os.path.basename(fname)
    if (base, func) not in reachable:
        errors.append(
            f"{oid}: enforced_at 的 {base}::{func} 不在必经路径上（不可从 hook/check-gate 到达）")


def _check_test_node(item, oid, repo_root, errors):
    """M 义务的 test：pytest 节点存在 + 测试文件引用该义务 id。"""
    test = item.get("test")
    if not isinstance(test, str) or "::" not in test:
        errors.append(f"{oid}: M 义务缺 test（pytest 节点凭证）")
        return
    path_part, node_part = test.split("::", 1)
    fpath = os.path.join(repo_root, path_part)
    if not os.path.isfile(fpath):
        errors.append(f"{oid}: test 指向的测试文件不存在：{path_part}")
        return
    try:
        with open(fpath, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        errors.append(f"{oid}: test 文件不可读：{path_part}")
        return
    func_name = node_part.split("[", 1)[0]
    if func_name not in text:
        errors.append(f"{oid}: test 节点函数 {func_name} 不在 {path_part} 中")
    if oid not in text:
        errors.append(f"{oid}: test 文件未引用义务 id（{oid}）")


def _check_review_output(item, oid, errors):
    """R 义务的 review_output：须是合格评审产出。"""
    ro = item.get("review_output")
    if not ro:
        return  # 缺 review_output 的处置见 `_evaluate`（DEBT0062：仅「有产出可指」的阶段判 ERROR）
    if ro not in _QUALIFIED_REVIEW_OUTPUTS:
        errors.append(
            f"{oid}: review_output={ro!r} 不是合格评审产出（须为 "
            f"{'/'.join(_QUALIFIED_REVIEW_OUTPUTS)} 之一）")


def _effective_baseline(baseline):
    """有效基线 (m, total)：`baseline.reset.to` 优先（一次性重设），否则 baseline.m/total。"""
    reset = baseline.get("reset") if isinstance(baseline, dict) else None
    if isinstance(reset, dict) and isinstance(reset.get("to"), str) and "/" in reset["to"]:
        try:
            m_s, t_s = reset["to"].split("/", 1)
            return int(m_s), int(t_s)
        except ValueError:
            pass
    return baseline.get("m"), baseline.get("total")


def _evaluate(data, reachable, repo_root):
    """核心判定：返回 (ok, errors, warnings, summary)。"""
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return False, ["obligations.yaml 解析结果不是映射（对象）"], warnings, None
    if not _is_int(data.get("schema_version")):
        errors.append("缺 schema_version（整数）")

    obligations = data.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        errors.append("obligations 列表缺失或为空")
        return False, errors, warnings, None

    counts = dict.fromkeys(VALID_DISPOSITIONS, 0)
    unassigned = []
    for idx, item in enumerate(obligations):
        if not isinstance(item, dict):
            unassigned.append(f"obligations[{idx}]（非映射）")
            continue
        oid = item.get("id") or f"obligations[{idx}]"
        disposition = item.get("disposition")
        if disposition not in VALID_DISPOSITIONS:
            unassigned.append(f"{oid}（disposition={disposition!r}）")
            continue
        # scope: protocol-repo 的义务单独统计，不计入 M 占比（设计 §2.9）
        in_ratio = item.get("scope") != _SCOPE_PROTOCOL
        if in_ratio:
            counts[disposition] += 1
        if not str(item.get("anchor") or "").strip():
            errors.append(f"{oid}: 缺可追溯来源锚点 anchor")
        if not str(item.get("statement") or "").strip():
            errors.append(f"{oid}: 缺义务陈述 statement")
        if disposition == "M":
            # scope: protocol-repo（CI/手工执行）的义务：设计 §2.9 规定其执行方式性质为
            # 「—」——不核验必经路径可达性 / pytest 凭证（也不计入 M 占比，见上）。
            if in_ratio:
                _check_enforced_at(item, oid, reachable, errors)
                _check_test_node(item, oid, repo_root, errors)
        elif disposition == "R":
            # DEBT0062（2026-10-10）：判据**收窄到「该阶段存在合格评审产出」**——只有这些阶段
            # 才可能（也必须）给出 `review_output`，缺则判 **ERROR**（可行动）。
            # 其余阶段（P0/P3/P5/P6/P7/P8/X）协议**本就没有**评审产出文件 ⇒ 其 R 义务由
            # **主 Agent / 阶段纪律**强制，无产出可指 ⇒ 既不告警也不判错（原判据在此处
            # 一律提示「应改标为 C」——C 是「命令生成」，语义不符，属误判）。
            _ph = str(item.get("phase") or "")
            _has_artifact = any(a.startswith(_ph + "-") for a in _QUALIFIED_REVIEW_OUTPUTS)
            if _has_artifact:
                if not item.get("review_output"):
                    errors.append(
                        f"{oid}: {_ph} 阶段有合格评审产出，R 义务缺 review_output"
                        f"（须为 {'/'.join(a for a in _QUALIFIED_REVIEW_OUTPUTS if a.startswith(_ph + '-'))}）")
                else:
                    _check_review_output(item, oid, errors)

    total = sum(counts.values())
    if unassigned:
        errors.append("存在「无归宿」项（三态归宿 M/C/R 缺失或非法）: " + ", ".join(unassigned))

    baseline = data.get("baseline")
    if not isinstance(baseline, dict) or not _is_int(baseline.get("m")) \
            or not _is_int(baseline.get("total")):
        errors.append("baseline 缺 m / total 整数（无法度量 M 类占比基线）")
        return (not errors), errors, warnings, None

    base_m, base_total = _effective_baseline(baseline)
    if not _is_int(base_m) or not _is_int(base_total) or base_total <= 0:
        errors.append("有效基线（baseline / baseline.reset.to）非法")
        return False, errors, warnings, None

    # 整数交叉相乘比对 M 类占比：current_m / total >= base_m / base_total
    if total > 0 and counts["M"] * base_total < base_m * total:
        errors.append(
            "M 类占比低于基线："
            f"current={counts['M']}/{total} < baseline={base_m}/{base_total}"
        )

    summary = {
        "total": total,
        "counts": counts,
        "m": counts["M"],
        "baseline_m": base_m,
        "baseline_total": base_total,
    }
    return (not errors), errors, warnings, summary


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            with contextlib.suppress(OSError, ValueError):
                stream.reconfigure(encoding="utf-8", errors="replace")

    root = _resolve_root()
    path = os.path.join(root, "rules", "obligations.yaml")
    if not os.path.isfile(path):
        sys.stderr.write(f"check-obligations: 目标不存在: {path}\n")
        return 2

    data = _load(path)
    if data is None:
        sys.stderr.write(f"check-obligations: YAML 不可解析: {path}\n")
        return 2

    reachable = _reachable_set(os.path.join(root, "scripts"))
    repo_root = os.path.dirname(root)
    _ok, errors, warnings, summary = _evaluate(data, reachable, repo_root)

    for warn in warnings:
        sys.stdout.write(f"CHECK-OBLIGATIONS: WARNING {warn}\n")

    if summary is None:
        for err in errors:
            sys.stdout.write(f"CHECK-OBLIGATIONS: FAIL {err}\n")
        return 1

    counts = summary["counts"]
    ratio = summary["m"] / summary["total"] if summary["total"] else 0.0
    base_ratio = summary["baseline_m"] / summary["baseline_total"]
    sys.stdout.write(
        "M 类占比: {m}/{total} = {ratio:.4f}（基线 {bm}/{bt} = {bratio:.4f}）\n".format(
            m=summary["m"], total=summary["total"], ratio=ratio,
            bm=summary["baseline_m"], bt=summary["baseline_total"], bratio=base_ratio,
        )
    )
    sys.stdout.write(
        "归宿分布: M={M} C={C} R={R}（M=脚本执行 / C=命令生成 / R=强制评审）\n".format(
            M=counts["M"], C=counts["C"], R=counts["R"],
        )
    )
    if errors:
        for err in errors:
            sys.stdout.write(f"CHECK-OBLIGATIONS: FAIL {err}\n")
        return 1
    sys.stdout.write(
        "CHECK-OBLIGATIONS: OK（无「无归宿」项 + 无 ERROR + M 类占比不低于基线）\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
