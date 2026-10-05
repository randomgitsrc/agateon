#!/usr/bin/env python3
"""agate-ci-verify.py — CI gate 重跑兜底（TAG0042 批 5，替换 ci-gate-backstop.py）

push / PR 时**实际重跑** gate 判定（`check-gate.py`），防 `git commit --no-verify`
绕过本地 hook。与已退役的 `ci-gate-backstop.py` 的关键差异（BDD-16）：

  * **不再依赖 CI 平台探测**——任何环境调用都执行判定，不因平台环境变量缺失而静默跳过；
  * 每个「跳过」面都**显式声明 `SKIP:` + 原因**（「跳过」与「通过」在输出上可区分），
    不再留「永远 SKIP 却显示绿」的假绿面（X3 整改）。

定位约定（P3 DESIGN_GAP-1 对齐）：无参数；cwd = 项目根。优先读仓库根 `.state.yaml`
（镜像 backstop 约定），其次扫描 `{tasks_dir}/*/.state.yaml`（兼容 agate 任务级状态）。

退出码：0 = 通过 / 显式跳过；1 = gate 判定失败（FAIL）。
平台无关：显式 utf-8；无系统临时目录字面量；Python 3.8+。
"""

import contextlib
import json
import subprocess
import sys
from pathlib import Path

_AGATE_ROOT = Path(__file__).resolve().parent.parent

# 无 gate 需对照的非推进态（与已退役 backstop 同口径）。
_NON_ADVANCING_PHASES = ("PAUSED", "READY", "DONE", "")


def _force_utf8():
    """子进程 stdout/stderr 强制 utf-8（防 cp1252 等窄编码下中文 print 崩溃）。"""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _run_python(args):
    return [sys.executable, *args]


def _run_gate(phase, task_dir):
    """实际重跑 `check-gate.py PHASE TASK_DIR` → (exit_code, 合并输出)。"""
    script = _AGATE_ROOT / "scripts" / "check-gate.py"
    if not script.exists():
        return 2, "check-gate.py not found"
    result = subprocess.run(
        _run_python([str(script), phase, task_dir]),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.returncode, result.stderr + result.stdout


def _skip(reason):
    """显式跳过：输出 `SKIP:` + 原因（与「通过」可区分），返回 0。"""
    print("=" * 66)
    print(f"SKIP: {reason}")
    print("  ⇒ 本次**未实际执行** gate 兜底（不是「跑了且通过」）")
    print("=" * 66)
    return 0


def _read_state(state_file):
    """读 .state.yaml → (phase, task_id)；不可读/非映射返回 None。"""
    try:
        import yaml
        with open(state_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return str(data.get("phase", "") or ""), str(data.get("task_id", "") or "")


def _tasks_dir(project_root):
    """经 agate_common 解析工作区 tasks 目录；不可用返回 None。"""
    try:
        import agate_common
    except ImportError:
        return None
    _workspace, tasks_dir = agate_common.resolve_workspace(project_root)
    return str(tasks_dir)


def _locate_state(project_root):
    """定位 (来源, phase, task_id)。来源 ∈ root/task/absent/unreadable/ambiguous。"""
    root_state = Path(project_root) / ".state.yaml"
    if root_state.is_file():
        parsed = _read_state(root_state)
        if parsed is None:
            return "unreadable", None, None
        return "root", parsed[0], parsed[1]

    tasks_dir = _tasks_dir(project_root)
    if tasks_dir and Path(tasks_dir).is_dir():
        candidates = sorted(Path(tasks_dir).glob("*/.state.yaml"))
        if len(candidates) == 1:
            parsed = _read_state(candidates[0])
            if parsed is None:
                return "unreadable", None, None
            return "task", parsed[0], parsed[1]
        if len(candidates) > 1:
            return "ambiguous", None, None
    return "absent", None, None


def main():
    _force_utf8()
    project_root = Path.cwd()
    found, phase, task_id = _locate_state(project_root)

    if found == "absent":
        return _skip("非 agate 项目（cwd 无 .state.yaml，tasks 下亦无任务级 .state.yaml）")
    if found == "unreadable":
        return _skip(".state.yaml 存在但无法解析/读取（数据损坏，不静默报绿）")
    if found == "ambiguous":
        return _skip("发现多个任务级 .state.yaml，无法唯一确定本次兜底对象")
    if not phase or phase in _NON_ADVANCING_PHASES:
        return _skip(f"phase={phase!r} 无 gate 需对照（非推进态）")
    if not task_id:
        return _skip("状态无 task_id，无法定位任务目录")

    tasks_dir = _tasks_dir(str(project_root))
    if tasks_dir is None:
        return _skip("agate_common 不可用，无法解析工作区 tasks 目录")
    task_dir = str(Path(tasks_dir) / task_id)

    ci_exit, ci_output = _run_gate(phase, task_dir)
    gate_result = project_root / ".gate-result.json"

    if not gate_result.exists():
        if ci_exit == 1:
            print(f"FAIL: gate 未通过（无 .gate-result.json，CI 重跑 exit={ci_exit}）")
            print(ci_output)
            return 1
        print(f"PASS: phase={phase} CI 重跑 exit={ci_exit}（无 .gate-result.json，--no-verify 场景）")
        return 0

    try:
        with open(gate_result, encoding="utf-8") as f:
            recorded = json.load(f)
    except Exception:
        print(f"FAIL: .gate-result.json 存在但无法解析（{gate_result}）")
        return 1

    if recorded.get("phase") != phase:
        print(f"FAIL: .gate-result.json phase={recorded.get('phase')} != .state.yaml phase={phase}")
        return 1
    if recorded.get("exit_code") != ci_exit:
        print(f"FAIL: .gate-result.json exit={recorded.get('exit_code')} != CI 重跑 exit={ci_exit}")
        print(ci_output)
        return 1

    print(f"PASS: phase={phase} exit_code={ci_exit} 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
