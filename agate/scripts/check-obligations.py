#!/usr/bin/env python3
"""check-obligations.py — 义务三态归宿登记校验（TAG0042 批6，BDD-13/18/19）

读取 agate/rules/obligations.yaml（阶段义务三态归宿登记表），校验：

  1. 每条义务有明确三态归宿（M 脚本执行 / C 命令生成 / R 强制评审）——无「无归宿」项；
  2. M 类（脚本执行）占比 ≥ 引入登记表时的基线（只增不减，下降即 FAIL）；
  3. 每条义务有可追溯来源锚点（anchor 非空）与义务陈述（statement 非空）。

判定：无归宿项为空 且 M 类占比 ≥ 基线 → exit 0；否则 exit 1。
本脚本承载 gate 判定逻辑（有 exit code）⇒ 已登记进 check-protocol-consistency.py 的
SCRIPT_ALIGNMENT_ANCHORS 锚点表（锚点 keywords 定值：["obligations.yaml", "M 类占比",
"无归宿"]，三者须在本脚本文本中字面出现）。

用法：
  check-obligations.py            默认：读 AGATE_ROOT/rules/obligations.yaml

退出码：
  0 = 通过（无「无归宿」项 + M 类占比 ≥ 基线）
  1 = 不通过（存在无归宿项 / M 类占比低于基线）
  2 = 用法或目标错误（obligations.yaml 缺失 / YAML 不可解析 / baseline 字段缺失）

平台无关：纯文本读取 + pyyaml；无裸解释器名、无硬编码 PATH、无临时目录字面量、
无软链假设；文本 I/O 显式 utf-8；Python 3.8+（无 match / str.removeprefix）。
"""

import contextlib
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("check-obligations.py: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(2)

VALID_DISPOSITIONS = ("M", "C", "R")


def _has_obligations(root):
    """root 下是否存在 rules/obligations.yaml。"""
    return bool(root) and os.path.isfile(os.path.join(root, "rules", "obligations.yaml"))


def _resolve_root():
    """定位协议根（含 rules/obligations.yaml）。

    候选顺序：AGATE_ROOT env → 脚本所在协议根（脚本上溯一层）→ 当前工作目录
    （含 `agate/` 前缀或直接含 `rules/`）。脚本相对优先，保证开发 checkout 与
    安装版本布局都能定位到**本脚本同源的**登记表，不受全局 current 指针影响。
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


def _evaluate(data):
    """核心判定：返回 (ok, errors, summary)。

    summary = {"total", "counts", "m", "baseline_m", "baseline_total"}。
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["obligations.yaml 解析结果不是映射（对象）"], None
    if not _is_int(data.get("schema_version")):
        errors.append("缺 schema_version（整数）")

    obligations = data.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        errors.append("obligations 列表缺失或为空")
        return False, errors, None

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
        counts[disposition] += 1
        if not str(item.get("anchor") or "").strip():
            errors.append(f"{oid}: 缺可追溯来源锚点 anchor")
        if not str(item.get("statement") or "").strip():
            errors.append(f"{oid}: 缺义务陈述 statement")

    total = sum(counts.values())
    if unassigned:
        errors.append("存在「无归宿」项（三态归宿 M/C/R 缺失或非法）: " + ", ".join(unassigned))

    baseline = data.get("baseline")
    if not isinstance(baseline, dict) or not _is_int(baseline.get("m")) or not _is_int(baseline.get("total")):
        errors.append("baseline 缺 m / total 整数（无法度量 M 类占比基线）")
        return (not errors), errors, None

    base_m = baseline["m"]
    base_total = baseline["total"]
    if base_total <= 0:
        errors.append("baseline.total 必须为正整数")
        return False, errors, None

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
    return (not errors), errors, summary


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

    _ok, errors, summary = _evaluate(data)
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
        "CHECK-OBLIGATIONS: OK（无「无归宿」项 + M 类占比不低于基线）\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
