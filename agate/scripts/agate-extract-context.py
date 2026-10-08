#!/usr/bin/env python3
"""agate-extract-context.py — 从上游产出提取结构化字段，注入 dispatch-context 上游关联节（P4 批次 1b）

从 agate-extract-context.sh 迁移（TAG0010 批次 1b）。用法：
  agate-extract-context.py PHASE TASK_DIR           # 输出到 stdout
  agate-extract-context.py PHASE TASK_DIR --write    # 追加到 dispatch-context 文件

PHASE 取值 P1-P8；TASK_DIR 是任务目录路径（含 P0-brief.md 等）。
exit 0：成功；exit 1：参数错误；exit 2：phase 不在 P1-P8 范围或任务目录不存在。

迁移说明：grep 管道 → 逐行正则等价。sh 版 `grep -c ... || echo 0` 在无匹配时产生
双行 "0\n0"（grep 打印 0 且 exit 1）——为保 CLI 契约逐字节等价，此 quirk 原样保留。
"""

import contextlib
import glob
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import agate_common
except ImportError:  # pragma: no cover - 安装破损时降级
    agate_common = None

_BDD_HEAD = re.compile(r"^#### BDD-")
_BDD_LIST = re.compile(r"^#### (BDD-[^:]+):")


def _is_non_legacy(task_dir):
    if agate_common is None:
        return False
    try:
        return agate_common.task_level(task_dir, __file__) is not None
    except Exception:
        return False


def _read_field(file_path, op):
    """经 agate-md-field-get.py 读字段（env FILE）；失败回退 ""。"""
    env = dict(os.environ)
    env["FILE"] = file_path
    script = os.path.join(SCRIPT_DIR, "agate-md-field-get.py")
    try:
        proc = subprocess.run(
            [sys.executable, script, op],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _infer_phase(task_dir):
    """单参形式：从 .state.yaml 的 phase 推断（非 legacy 任务）；否则 None。"""
    if agate_common is None:
        return None
    state_file = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(state_file):
        return None
    try:
        phase = agate_common.read_state_phase(state_file)
    except Exception:
        return None
    return phase if isinstance(phase, str) and phase else None


def _read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def _grep(lines, pattern):
    """grep -E 等价：返回整行匹配列表（无匹配返回空串，即 sh 的 || true 语义）。"""
    return [line for line in lines if re.search(pattern, line)]


def _grep_count(lines, pattern):
    """grep -cE 等价：匹配行数；无匹配时复刻 sh 的 "0\\n0" 双行 quirk。"""
    count = sum(1 for line in lines if re.search(pattern, line))
    if count == 0:
        return "0\n0"
    return str(count)


def _grep_after(lines, pattern, after=5, limit=6):
    """grep -A5 | head -6 等价：逐匹配组输出匹配行 + 其后 after 行，组间 "--" 分隔，
    累计到 limit 行即停（head 截断语义）。"""
    out = []
    matches = [i for i, line in enumerate(lines) if re.search(pattern, line)]
    for k, idx in enumerate(matches):
        if k > 0:
            out.append("--")
        out.append(lines[idx])
        out.extend(lines[idx + 1:idx + 1 + after])
        if len(out) >= limit:
            break
    return out[:limit]


def _sum_failed(task_dir):
    """grep -rh '^\\s*failed:' P5-test-results/ | grep -oE '[0-9]+' | awk 求和 等价。"""
    results_dir = os.path.join(task_dir, "P5-test-results")
    if not os.path.isdir(results_dir):
        return None
    total = 0
    for root, _dirs, files in os.walk(results_dir):
        for fn in sorted(files):
            path = os.path.join(root, fn)
            try:
                for line in _read_lines(path):
                    if re.search(r"^\s*failed:", line):
                        total += sum(int(m) for m in re.findall(r"[0-9]+", line))
            except OSError:
                pass
    return total


def _grep_rh_impl_dirs(task_dir):
    """grep -rh '^implementation_dir:' P4-implementation.md P4-implementation/ 等价。"""
    out = []
    p4 = os.path.join(task_dir, "P4-implementation.md")
    if os.path.isfile(p4):
        out.extend(_grep(_read_lines(p4), r"^implementation_dir:"))
    p4dir = os.path.join(task_dir, "P4-implementation")
    if os.path.isdir(p4dir):
        for root, _dirs, files in sorted(os.walk(p4dir)):
            for fn in sorted(files):
                path = os.path.join(root, fn)
                with contextlib.suppress(OSError):
                    out.extend(_grep(_read_lines(path), r"^implementation_dir:"))
    return out


def extract(phase, task_dir):
    output = ""
    num = phase[1:]

    if phase == "P1":
        p0 = os.path.join(task_dir, "P0-brief.md")
        if os.path.isfile(p0):
            output += "### P0-brief 关键字段" + "\n"
            lines = _read_lines(p0)
            # `task:` 的值在同一行 ⇒ `_grep`（只取键行）足够；
            # `known_risks:` 是**跨行列表** ⇒ 必须 `_grep_after`（与下方 env_constraints 同口径）。
            # 此前这里用 `_grep`，只回带裸键行、列表项全丢 ⇒ 注入的 known_risks 恒为空
            # （RM-AG0080：同一函数内两种口径即缺陷来源）。
            task_line = _grep(lines, r"^task:")
            if task_line:
                output += "- " + "\n".join(task_line) + "\n"
            risks = _grep_after(lines, r"^known_risks:")
            if risks:
                output += "- known_risks:" + "\n" + "\n".join(risks) + "\n"
            env = _grep_after(lines, r"^env_constraints:")
            if env:
                output += "- env_constraints:" + "\n" + "\n".join(env) + "\n"
            # 可见性（与 RM-AG0077 子批 A 同哲学：静默的"空"会被读成"没问题"）：
            # P0-brief 存在却一个字段都取不到 → 显式告警，而非只输出一个空标题。
            # 实测先例：TAG0037 用 markdown 标题（`## task`）书写 ⇒ 注入长期为空且零提示。
            if not (task_line or risks or env):
                sys.stderr.write(
                    "WARNING: agate-extract-context: P0-brief 存在但未取到 "
                    "task/known_risks/env_constraints —— 须用**行首键**书写"
                    "（`task:` / `known_risks:` / `env_constraints:`），"
                    "markdown 标题（`## task`）不被识别\n"
                )
    elif phase == "P2":
        p1 = os.path.join(task_dir, "P1-requirements.md")
        if os.path.isfile(p1):
            output += "### P1-requirements 关键字段" + "\n"
            lines = _read_lines(p1)
            domains = _grep(lines, r"^domains:")
            if domains:
                output += "- " + "\n".join(domains) + "\n"
            risk = _grep(lines, r"^risk_level:")
            if risk:
                output += "- " + "\n".join(risk) + "\n"
            output += "- BDD 条件数: " + _grep_count(lines, r"^#### BDD-") + "\n"
    elif phase == "P3":
        p2 = os.path.join(task_dir, "P2-design.md")
        if os.path.isfile(p2):
            output += "### P2-design 关键字段" + "\n"
            fields = _grep(_read_lines(p2), r"^(packages|domains|ui_affected|gate_commands):")
            if fields:
                output += "\n".join(fields) + "\n"
    elif phase == "P4":
        p2 = os.path.join(task_dir, "P2-design.md")
        if os.path.isfile(p2):
            output += "### P2-design 关键字段" + "\n"
            fields = _grep(_read_lines(p2), r"^(packages|domains|ui_affected|gate_commands|files_to_read):")
            if fields:
                output += "\n".join(fields) + "\n"
        p3 = os.path.join(task_dir, "P3-test-cases.md")
        if os.path.isfile(p3):
            output += "- P3 BDD 测试覆盖数: " + _grep_count(_read_lines(p3), r"^#### BDD-") + "\n"
    elif phase == "P5":
        p2 = os.path.join(task_dir, "P2-design.md")
        if os.path.isfile(p2):
            output += "### P2-design gate_commands" + "\n"
            gc = _grep_after(_read_lines(p2), r"^gate_commands:")
            if gc:
                output += "\n".join(gc) + "\n"
        impl_dirs = _grep_rh_impl_dirs(task_dir)
        if impl_dirs:
            output += "### implementation_dir" + "\n"
            for line in impl_dirs:
                output += "- " + line + "\n"
    elif phase == "P6":
        p1 = os.path.join(task_dir, "P1-requirements.md")
        if os.path.isfile(p1):
            output += "### P1 BDD 编号列表" + "\n"
            bdd_list = []
            for line in _read_lines(p1):
                m = _BDD_LIST.match(line)
                if m:
                    bdd_list.append(m.group(1))
            if bdd_list:
                for line in bdd_list:
                    output += "- " + line + "\n"
            else:
                output += "- (无 BDD 条件)" + "\n"
        failed = _sum_failed(task_dir)
        if failed is not None:
            output += f"- P5 failed 参考: {failed}（仅供参考，gate 以主 Agent 实跑为准）\n"
    elif phase == "P7":
        p2 = os.path.join(task_dir, "P2-design.md")
        if os.path.isfile(p2):
            output += "### P2-design packages" + "\n"
            pkgs = _grep(_read_lines(p2), r"^packages:")
            if pkgs:
                output += "- " + "\n".join(pkgs) + "\n"
        p6 = os.path.join(task_dir, "P6-acceptance.md")
        if os.path.isfile(p6):
            # TAG0050 批 D（设计 §5.1）：非 legacy 任务的计数经 md-field-get 读取
            # （`pass`/`fail` 为系统字段，按 `results` 现算），不再正文 grep。
            if _is_non_legacy(task_dir):
                pass_fm = _read_field(p6, "pass")
                fail_fm = _read_field(p6, "fail")
                if pass_fm != "" and fail_fm != "":
                    output += f"- P6 验收: {pass_fm} PASS, {fail_fm} FAIL\n"
                else:
                    lines = _read_lines(p6)
                    output += "- P6 验收: {} PASS, {} FAIL\n".format(
                        _grep_count(lines, r"^\s*- PASS"),
                        _grep_count(lines, r"^\s*- FAIL"),
                    )
            else:
                lines = _read_lines(p6)
                output += "- P6 验收: {} PASS, {} FAIL\n".format(
                    _grep_count(lines, r"^\s*- PASS"),
                    _grep_count(lines, r"^\s*- FAIL"),
                )
            gaps = _grep(_read_lines(p6), r"\[DESIGN_GAP:")
            if gaps:
                output += "- DESIGN_GAP 列表:" + "\n" + "\n".join(gaps) + "\n"
    elif phase == "P8":
        p2 = os.path.join(task_dir, "P2-design.md")
        if os.path.isfile(p2):
            output += "### P2-design packages" + "\n"
            pkgs = _grep(_read_lines(p2), r"^packages:")
            if pkgs:
                output += "- " + "\n".join(pkgs) + "\n"
        p7 = os.path.join(task_dir, "P7-consistency.md")
        if os.path.isfile(p7):
            # TAG0050 批 D：非 legacy 任务的 P7 计数经字段读取（系统字段）。
            blocker_fm = ""
            if _is_non_legacy(task_dir):
                blocker_fm = _read_field(p7, "blocker_count")
            lines = _read_lines(p7)
            if blocker_fm != "":
                output += f"- P7 BLOCKER 数: {blocker_fm}\n"
            else:
                output += "- P7 BLOCKER 数: " + _grep_count(lines, r"\[BLOCKER\]") + "\n"
            deviations = _grep(lines, r"\[DEVIATION")
            if deviations:
                output += "- DEVIATION 列表:" + "\n" + "\n".join(deviations) + "\n"

    diagnosis = os.path.join(task_dir, f"P{num}-gate-diagnosis.md")
    if os.path.isfile(diagnosis):
        output += "\n### gate-diagnosis 引用" + "\n"
        output += f"- 参见 P{num}-gate-diagnosis.md" + "\n"

    return output


def main():
    argv = sys.argv[1:]
    # TAG0050 批 D：也接受单参形式 `agate-extract-context.py TASK_DIR`
    # （非 legacy 任务按 .state.yaml 的 phase 推断）——供 BDD-60 的字段现算计数使用。
    if len(argv) == 1 and os.path.isdir(argv[0]):
        phase = _infer_phase(argv[0])
        if phase is None:
            sys.stderr.write(
                "agate-extract-context.py: 单参形式需任务目录含 .state.yaml 的 phase\n"
            )
            sys.exit(1)
        task_dir = argv[0]
        write_mode = ""
    else:
        if len(argv) < 2 or len(argv) > 3:
            sys.stderr.write("用法: agate-extract-context.py PHASE TASK_DIR [--write]\n")
            sys.exit(1)
        phase = argv[0]
        task_dir = argv[1]
        write_mode = argv[2] if len(argv) > 2 else ""

    if phase not in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"):
        sys.stderr.write(f"agate-extract-context.py: phase '{phase}' 不在 P1-P8 范围内\n")
        sys.exit(2)

    if not os.path.isdir(task_dir):
        sys.stderr.write(f"agate-extract-context.py: 任务目录不存在: {task_dir}\n")
        sys.exit(2)

    result = extract(phase, task_dir)

    if write_mode == "--write":
        pattern = os.path.join(task_dir, f"P{phase[1:]}-dispatch-context-*.md")
        dc_files = sorted(glob.glob(pattern))
        if dc_files:
            dc_file = dc_files[0]
            with open(dc_file, "a", encoding="utf-8") as f:
                f.write(f"\n{result}\n")
            print(f"已追加到 {dc_file}")
        else:
            sys.stderr.write(
                f"agate-extract-context.py: 未找到 P{phase[1:]}-dispatch-context-*.md，输出到 stdout\n"
            )
            sys.stdout.write(f"{result}\n")
    else:
        sys.stdout.write(f"{result}\n")


if __name__ == "__main__":
    main()
