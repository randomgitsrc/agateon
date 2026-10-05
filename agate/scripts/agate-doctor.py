#!/usr/bin/env python3
"""agate-doctor.py — 项目接入状态诊断（TAG0042 批 5，BDD-17）

诊断项目接入 agate 的状态，逐维度给出**客观值**，并对异常项给出**可执行修复指引**：

  1. 声明文件：项目根 `agate.config.yaml`（经 `agate_common.read_project_config`
     **唯一读取函数**取值，不另写第二处声明解析——P2-design §4.1）。
  2. git hook：`pre-commit` / `commit-msg` / `pre-push` 是否存在。
  3. 版本解析：`AGATE_ROOT`（env 或脚本自定位）与项目 `.agate-version` 声明。
  4. 账本完整性：任务目录 `gate-events.jsonl` 的 append-only 哈希链（`prev_hash`）。

**退出码固定**：诊断正常完成 → rc=0（诊断工具报告问题 ≠ 自身执行失败，BDD-17）。
平台无关：显式 utf-8；无系统临时目录字面量；Python 3.8+。
"""

import contextlib
import hashlib
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_AGATE_ROOT = _SCRIPT_DIR.parent
_HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push")


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _genesis_hash():
    return hashlib.sha256(b"").hexdigest()


def _tasks_dir(project_root):
    try:
        import agate_common
        _workspace, tasks_dir = agate_common.resolve_workspace(str(project_root))
        return Path(tasks_dir)
    except Exception:
        return None


def _diagnose_declaration(project_root):
    """维度①：声明文件。返回 (ok, 状态行, 修复指引或 None)。"""
    try:
        import agate_common
        cfg = agate_common.read_project_config(str(project_root))
    except Exception as exc:
        return False, f"声明文件: 读取失败（{exc}）", \
            f"检查 {project_root / 'agate.config.yaml'} 的 YAML 语法"
    if cfg.get("present"):
        language = (cfg.get("project") or {}).get("language", "") or "unknown"
        return True, f"声明文件: 存在（agate.config.yaml，language={language}）", None
    return False, "声明文件: 缺失（agate.config.yaml 不存在）", \
        f"运行 {sys.executable} {_SCRIPT_DIR / 'agate-config.py'} init 生成声明"


def _diagnose_hooks(project_root):
    """维度②：git hook。返回 (ok, 状态行, 修复指引或 None)。"""
    hooks_dir = project_root / ".git" / "hooks"
    present = [n for n in _HOOK_NAMES if (hooks_dir / n).is_file()]
    if not hooks_dir.is_dir():
        return False, "hook: 未检测到 .git/hooks（非 git 仓库或未初始化）", \
            "确认项目为 git 仓库；再运行 agate-setup.py 安装 hook"
    missing = [n for n in _HOOK_NAMES if n not in present]
    if not missing:
        return True, f"hook: 已安装（{', '.join(_HOOK_NAMES)}）", None
    return False, f"hook: 缺失 {', '.join(missing)}（pre-commit 等未安装）", \
        f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-setup.py'} --scope project 安装 hook"


def _diagnose_version(project_root):
    """维度③：版本解析。返回 (ok, 状态行, 修复指引或 None)。"""
    env_root = os.environ.get("AGATE_ROOT", "")
    resolved = env_root or str(_AGATE_ROOT)
    ver_file = project_root / ".agate-version"
    declared = ""
    if ver_file.is_file():
        try:
            declared = ver_file.read_text(encoding="utf-8").strip()
        except OSError:
            declared = ""
    if not Path(resolved).is_dir():
        return False, f"版本解析: AGATE_ROOT 不可用（{resolved}）", \
            f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-resolve.py'} 查看解析链"
    declared_note = declared if declared else "（未声明，使用 current）"
    return True, f"版本解析: AGATE_ROOT={resolved}；项目 .agate-version={declared_note}", None


def _check_chain(ledger):
    """校验单个账本的 append-only 哈希链。返回 (ok, 说明)。"""
    try:
        raw_lines = ledger.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return False, f"无法读取（{exc}）"
    expected = _genesis_hash()
    for idx, raw in enumerate(raw_lines, 1):
        try:
            event = json.loads(raw)
        except ValueError:
            return False, f"第 {idx} 行非合法 JSON"
        if event.get("prev_hash") != expected:
            return False, f"第 {idx} 行 prev_hash 断链"
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return True, f"{len(raw_lines)} 条事件，链完整"


def _diagnose_ledger(project_root):
    """维度④：账本完整性。返回 (ok, 状态行, 修复指引或 None)。"""
    tasks_dir = _tasks_dir(project_root)
    if tasks_dir is None or not tasks_dir.is_dir():
        return True, "账本完整性: 未发现任务目录（无账本可审计）", None
    ledgers = sorted(tasks_dir.glob("*/gate-events.jsonl"))
    if not ledgers:
        return True, "账本完整性: 未发现 gate-events.jsonl（无账本可审计）", None
    problems = []
    for ledger in ledgers:
        ok, note = _check_chain(ledger)
        if not ok:
            problems.append(f"{ledger.parent.name}: {note}")
    if problems:
        return False, f"账本完整性: {len(problems)} 个账本异常（{'; '.join(problems)}）", \
            f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'check-events.py'} <任务目录> 定位断链"
    return True, f"账本完整性: {len(ledgers)} 个账本，链完整", None


def main():
    _force_utf8()
    project_root = Path.cwd()

    checks = (
        _diagnose_declaration,
        _diagnose_hooks,
        _diagnose_version,
        _diagnose_ledger,
    )
    print("=" * 66)
    print("agate-doctor — 项目接入状态诊断")
    print(f"项目根: {project_root}")
    print("=" * 66)

    guidance = []
    for check in checks:
        try:
            ok, line, fix = check(project_root)
        except Exception as exc:  # 单维度异常不得使诊断整体崩溃（退出码固定）
            ok, line, fix = False, f"{check.__name__}: 诊断异常（{exc}）", "请提交 issue 或人工排查"
        mark = "OK" if ok else "!!"
        print(f"[{mark}] {line}")
        if fix:
            guidance.append(fix)

    if guidance:
        print("-" * 66)
        print("修复建议（异常项的可执行动作）：")
        for item in guidance:
            print(f"  - {item}")
    else:
        print("全部维度正常（已接入）。")

    # BDD-17：诊断正常完成 → 退出码固定为 0（报告问题不等于自身执行失败）。
    return 0


if __name__ == "__main__":
    sys.exit(main())
