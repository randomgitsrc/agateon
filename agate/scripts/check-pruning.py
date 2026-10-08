#!/usr/bin/env python3
"""check-pruning.py — 裁剪条件检查（P2.7-P2.9）

从 check-pruning.sh 迁移（TAG0010 批次 2c）。CLI 契约与 sh 版等价：
  check-pruning.py TASK_DIR
exit 0 = 通过; exit 1 = 裁剪条件不满足; exit 2 = 无 P1 文件

检查 P1-requirements.md 的 risk_level + phases 声明是否符合裁剪条件。
risk_level / phases 经 agate-md-field-get.py 读取（env FILE 传参，sys.executable
subprocess，$(...) 剥尾换行 → .rstrip("\n")）；P1 全文的 grep 语义 → re.search
（MULTILINE 锚定）；git diff --cached 的 tr -d '\r' 剥离 → 逐行 .rstrip("\r")；
realpath --relative-to → os.path.relpath；P2.9 产出文件 glob → glob + basename。
"""

import glob
import os
import re
import subprocess
import sys

try:
    from agate_common import run_git
except ImportError:
    run_git = None

try:
    import agate_common
except ImportError:  # pragma: no cover - 安装破损降级
    agate_common = None

try:
    from agate_common import (
        body_field_value,
        fm_field_value,
        reconcile_enabled,
        reconcile_field,
        reconcile_summary,
        split_frontmatter,
    )
except ImportError:
    # M1 对账辅助缺失 → 对账降级为关闭（对账是叠加层，不影响原判定语义）
    def reconcile_enabled():
        return False

    def reconcile_field(_op, _field, _grep_val, _structured_val):
        return True

    def reconcile_summary():
        return None

    def split_frontmatter(text):
        return (None, text)

    def body_field_value(body, field):
        return ""

    def fm_field_value(fm, field):
        return ""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FIELD_GET = os.path.join(SCRIPT_DIR, "agate-md-field-get.py")


def _md_field(op, p1_file):
    """调 agate-md-field-get.py op（env FILE），失败回退 ""（同 sh || echo ""）。"""
    env = dict(os.environ)
    env["FILE"] = p1_file
    try:
        proc = subprocess.run(
            [sys.executable, MD_FIELD_GET, op],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def _read_p1(p1_file):
    try:
        with open(p1_file, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _staged_source_count(task_dir):
    """裁剪 P7 的源码文件数（git diff --cached 排除任务产出后，同 sh 排除模式）。"""
    if run_git is None:
        return 0
    rc, out = run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)
    repo_root = out.rstrip("\n").strip() if rc == 0 else ""
    if not repo_root:
        return 0
    repo_root = os.path.realpath(repo_root)
    parent = os.path.dirname(task_dir) or "."
    try:
        tasks_base_rel = os.path.relpath(parent, repo_root).replace("\\", "/")
    except ValueError:
        return 0
    rc, out = run_git(["diff", "--cached", "--name-only"], cwd=task_dir)
    if rc != 0:
        return 0
    pattern = (
        "^docs/tasks/|^" + tasks_base_rel + "/|\\.state\\.yaml$"
        "|/P[0-8]-.*\\.md$|^\\\\.|CHANGELOG"
    )
    count = 0
    for raw_line in out.splitlines():
        line = raw_line.rstrip("\r")
        if not re.search(pattern, line):
            count += 1
    return count


def _reconcile_p1_fields(p1_text):
    """M1 对账（P2-design §3.4，BDD-6/7）：frontmatter（结构化）↔ 正文（grep）双读对账。

    risk_level/phases 字段：正文声明值 vs frontmatter 声明值不一致 → stderr
    `RECONCILE WARNING` + 计数汇总（可重定向进日志）；正文无该字段（仅 frontmatter 声明）
    或两值归一化等价（list 内联/块式 vs 空格连接）→ 不告警（BDD-8 归一化口径）。
    对账不改变本脚本退出码语义（原判定 0/1/2 不变）；任何异常 fail-open。
    """
    if not reconcile_enabled():
        return
    try:
        fm, body = split_frontmatter(p1_text)
        body_risk = body_field_value(body, "risk_level")
        if body_risk:
            reconcile_field("check-pruning", "risk_level", body_risk, fm_field_value(fm, "risk_level"))
        body_phases = body_field_value(body, "phases")
        if body_phases:
            reconcile_field("check-pruning", "phases", body_phases, fm_field_value(fm, "phases"))
        reconcile_summary()
    except Exception:
        pass


def _phase_universe(task_dir):
    """快照 `phase_universe`（阶段全集）→ set；不可用 → set()（跳过闭合检查）。"""
    if agate_common is None:
        return set()
    try:
        level = agate_common.task_level(task_dir, __file__)
        if level is None:
            level = agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
    except Exception:
        return set()
    universe = contract.get("phase_universe") if isinstance(contract, dict) else None
    if isinstance(universe, list):
        return {str(x) for x in universe}
    return set()


def _pruned_required_fields(task_dir):
    """快照 `pruned.required_fields`（`pruned` 条目必填字段）；不可用 → [phase]。"""
    if agate_common is None:
        return ["phase"]
    try:
        level = agate_common.task_level(task_dir, __file__)
        if level is None:
            level = agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
    except Exception:
        return ["phase"]
    spec = contract.get("pruned") if isinstance(contract, dict) else None
    fields = spec.get("required_fields") if isinstance(spec, dict) else None
    return [str(x) for x in fields] if isinstance(fields, list) and fields else ["phase"]


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-pruning.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    p1_file = os.path.join(task_dir, "P1-requirements.md")
    if not os.path.isfile(p1_file):
        sys.stderr.write(
            "GATE SKIP: check-pruning: 无 P1-requirements.md，裁剪条件未校验（exit 2，交人工）\n"
        )
        sys.exit(2)

    risk_level = _md_field("risk_level", p1_file)
    phases_declared = _md_field("phases", p1_file)
    p1_text = _read_p1(p1_file)
    has_override = len(re.findall(r"^override:", p1_text, re.MULTILINE))
    phases = phases_declared.split()

    _reconcile_p1_fields(p1_text)

    errors = []

    # TAG0050 批 F（RM-AG0087，设计 §7）：非 legacy 任务**恒检**——
    # `set(phases) ∪ set(pruned.phase)` 须等于快照 `phase_universe`，且两者不相交。
    # GAP-4 闭合（2026-10-08）：不再只在"声明了 pruned"时检查（`pruned` 缺省按空集处理）。
    if agate_common is not None and agate_common.task_level(task_dir, __file__) is not None:
        fm_p1, _body_p1 = split_frontmatter(p1_text)
        pruned = fm_p1.get("pruned") if isinstance(fm_p1, dict) else None
        pruned_list = pruned if isinstance(pruned, list) else []
        # pruned 条目必填字段（快照 pruned.required_fields：[phase, reason, risk]）。
        for _idx, item in enumerate(pruned_list):
            if not isinstance(item, dict):
                errors.append("pruned 条目须为映射（含 phase/reason/risk）")
                continue
            _missing = [f for f in _pruned_required_fields(task_dir) if not item.get(f)]
            if _missing:
                errors.append(f"pruned 条目缺必填字段：{_missing}")
        declared = set(phases)
        pruned_phases = {
            str(item.get("phase"))
            for item in pruned_list
            if isinstance(item, dict) and item.get("phase")
        }
        universe = _phase_universe(task_dir)
        if declared & pruned_phases:
            errors.append(
                f"phases 与 pruned.phase 相交：{sorted(declared & pruned_phases)}"
            )
        if universe and (declared | pruned_phases) != universe:
            errors.append(
                "phases ∪ pruned.phase != 阶段全集："
                f"缺={sorted(universe - (declared | pruned_phases))}, "
                f"多={sorted((declared | pruned_phases) - universe)}"
            )

    # 检查 1：risk_level 必须存在
    if not risk_level:
        errors.append("P1-requirements.md 缺 risk_level 字段")

    # 检查 2：P2 不可裁剪（无例外口）
    if "P2" not in phases:
        errors.append(
            "P2 不可裁剪——方案设计是必经阶段，P1 analyst 做需求分析不做方案设计，"
            "无法预知 P2 architect 会发现哪些隐含问题。design_trivial / "
            "follows_existing_pattern 可简化 P2（1 个候选方案），不可省略 P2"
        )

    # 检查 3：P6 不可裁剪（无例外口）
    if "P6" not in phases:
        errors.append(
            "P6 不可裁剪——验收是质量最后防线。no_behavior_change 可简化 P6（快速验收），不可省略 P6"
        )

    # 检查 4: P4 不可裁剪（交付底线——没有实现就没有可发布产物）
    if "P4" not in phases:
        errors.append("P4 不可裁剪——实现是交付底线，无实现则无可发布产物")

    # 检查 5: P5 不可裁剪（交付底线——没有验证就没有可发布产物）
    if "P5" not in phases:
        errors.append("P5 不可裁剪——验证是交付底线，无验证则无可发布产物")

    # 检查 6：裁剪 P3 的条件
    if "P3" not in phases and risk_level != "low":
        errors.append("P3 不可裁剪——仅 low 风险可裁剪 TDD 阶段（medium/high 必须走 TDD 红灯）")

    # 检查 7：裁剪 P7 的条件（R4：bug fix + implicit_coupling 维度）
    if "P7" not in phases:
        # R4(a) bug fix：补实现已文档化的文件数条件（--cached，不用 HEAD~1）
        source_count = _staged_source_count(task_dir)
        if source_count > 5:
            errors.append(f"裁剪 P7 需源码文件数 ≤ 5，实际={source_count}")

        # R4(b)：implicit_coupling 维度（self-declaration nudge）
        if re.search(r"^implicit_coupling:", p1_text, re.MULTILINE):
            errors.append("裁剪 P7 不可行：P1 声明了 implicit_coupling（隐式耦合维度）")
        # R4(c)：裁剪 P7 时，若未声明 implicit_coupling，须有 coupling_checklist
        elif not re.search(r"^coupling_checklist:\s*\[", p1_text, re.MULTILINE):
            errors.append(
                "裁剪 P7 需 coupling_checklist: [检查过的耦合点]（如 api-schema: checked, data-model: checked）"
            )

    # 检查 8：裁剪 P8 的条件（R5：internal_only 声明 + 理由）
    if "P8" not in phases:
        if not re.search(r"^internal_only:\s*true", p1_text, re.MULTILINE):
            errors.append("裁剪 P8 需声明 internal_only: true")
        elif not re.search(r"^internal_only_reason:", p1_text, re.MULTILINE):
            errors.append("裁剪 P8 需 internal_only: true + 理由（internal_only_reason: 字段缺失）")

    # 检查 9：裁剪理由必须含"跳过风险"评估（R3a：self-declaration nudge）
    # P4/P5 已被检查 4/5 硬拦，此处仍纳入条件以保持穷举
    if not all(p in phases for p in ("P2", "P3", "P4", "P5", "P6", "P7", "P8")) and "跳过风险:" not in p1_text:
        errors.append("裁剪声明缺'跳过风险:'评估（nudge：强制思考裁剪风险）")

    # P2.9 实际实现：对比 P1 phases 声明与文件系统中的产出文件
    pruned_with_output = ""
    for phase in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"):
        if phase == "P1":
            continue
        if phase in phases:
            continue
        for f in sorted(glob.glob(os.path.join(task_dir, phase + "-*.md"))):
            if os.path.isfile(f):
                pruned_with_output += f"{phase}:{os.path.basename(f)} "

    if pruned_with_output and has_override == 0:
        errors.append(f"裁剪声明与执行不一致（{pruned_with_output}），但 P1 无 override: 字段")

    if errors:
        sys.stderr.write("GATE PRUNING: 裁剪条件不满足：\n")
        for line in errors:
            sys.stderr.write(f"  - {line}\n")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
