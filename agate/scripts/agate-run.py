#!/usr/bin/env python3
"""agate-run.py — 执行层：在不可绕开路径上执行声明中的验证命令（TAG0042 批 3）。

职责（P1 BDD-9/10/11/12，P2-design §4.2）：
  * BDD-9  从 `agate.config.yaml` 的 `verify.commands` 取命令，经 bash 执行并**如实传播退出码**
           （POSIX 开 `pipefail`，避免 `cmd | tail` 吞掉左侧失败）；非 POSIX 平台显式退化 +
           WARNING（绝不静默报绿，ADR-015 手段②）。
  * BDD-10 `--baseline` 首次落盘 `.out` 证据；后续执行与之**逐字节比对**，差异客观报出（二值）。
  * BDD-11 证据文件须被 `.gitignore` 覆盖（`git check-ignore` 判定），否则报错（不落盘）。
  * BDD-12 执行后经 `agate_common.append_event`（**唯一写路径**）追加 `cmd_run` 事件；目标
           账本目录由 `AGATE_TASK_DIR` env 指定（不直接写 gate-events.jsonl，避免破链）。

命令解析：CLI 实参须**精确匹配** `verify.commands` 中的一条（不可绕开路径拒绝执行未声明命令）。
证据槽位：证据文件按命令在 `verify.commands` 中的**下标**命名（`{paths.evidence}/cmd-<n>.out`）——
下标在命令文本变更后保持稳定，故「同一验证槽位输出改变」可被客观比对（BDD-10）。

平台无关：仅标准库；无系统临时目录字面量；显式 encoding="utf-8"。
Python 3.8+（禁 match / str.removeprefix）。
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from agate_common import append_event, read_project_config  # noqa: E402

EVIDENCE_SUFFIX = ".out"
BASELINE_FLAG = "--baseline"
DEFAULT_EVIDENCE_DIR = ".agate-evidence"


def _usage_error(message):
    sys.stderr.write(message + "\n")
    return 2


def _resolve_command(cfg, arg):
    """把 CLI 实参解析为 (命令, 声明槽位下标)。未在 verify.commands 声明 → (None, -1)。"""
    verify = cfg.get("verify") if isinstance(cfg, dict) else None
    commands = verify.get("commands") if isinstance(verify, dict) else None
    if not isinstance(commands, list):
        return None, -1
    for index, command in enumerate(commands):
        if isinstance(command, str) and command == arg:
            return command, index
    return None, -1


def _evidence_path(cfg, project_root, index):
    """证据文件路径：{paths.evidence}/cmd-<index>.out（槽位下标稳定）。"""
    evidence_dir = DEFAULT_EVIDENCE_DIR
    paths = cfg.get("paths") if isinstance(cfg, dict) else None
    if isinstance(paths, dict) and isinstance(paths.get("evidence"), str) and paths["evidence"]:
        evidence_dir = paths["evidence"]
    if not os.path.isabs(evidence_dir):
        evidence_dir = os.path.join(project_root, evidence_dir)
    return os.path.join(evidence_dir, f"cmd-{index}{EVIDENCE_SUFFIX}")


def _run_command(cmd):
    """执行命令 → (退出码, 合并输出)。POSIX 开 pipefail；非 POSIX 退化 + WARNING。

    写法口径（P2 §4.2）：pipefail 用**前缀** `"set -o pipefail; " + cmd` + `executable="bash"`；
    **不能**写 `executable="bash -o pipefail"`（`executable` 是路径，实测 FileNotFoundError）。
    """
    if sys.platform == "win32":
        sys.stderr.write(
            "WARNING: 平台 win32（MSYS2）pipefail 行为未测，退化为不吞退出码的直执行"
            "（绝不静默报绿，ADR-015）\n"
        )
        try:
            proc = subprocess.run(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            return proc.returncode, proc.stdout or ""
        except OSError as exc:
            return 127, str(exc)
    try:
        proc = subprocess.run(
            "set -o pipefail; " + cmd, shell=True, executable="bash",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or ""
    except OSError as exc:
        return 127, str(exc)


def _is_ignored(project_root, path):
    """`git check-ignore` 判定 → True/False；无法判定（非 git 仓库 / git 不可用）→ None。"""
    rel = os.path.relpath(path, project_root)
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "--", rel],
            cwd=project_root, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _write_evidence(path, output):
    """证据落盘——**字节精确**（写盘字节 == `output.encode("utf-8")`，C8 C1 修复）。

    不能用文本模式默认换行：`open(..., "w")` 的 `newline=None` 会在写入时把 `\\n`
    翻译为 `os.linesep`，而比对侧（`:180`/`:182`）是字节精确（`_read_bytes` vs
    `output.encode("utf-8")`）——POSIX 重合，Windows（`os.linesep="\\r\\n"`）恒不一致
    → `--baseline` 后续执行恒报 mismatch。故用 `"wb"` 直接写 UTF-8 字节。
    """
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(output.encode("utf-8"))


def _record_cmd_run(cmd, exit_code):
    """经 append_event（唯一写路径）追加 cmd_run 事件；未指定 AGATE_TASK_DIR → 跳过。"""
    task_dir = os.environ.get("AGATE_TASK_DIR", "")
    if not task_dir:
        return
    try:
        append_event(task_dir, {
            "event": "cmd_run",
            "cmd": cmd,
            "exit": exit_code,
            "runner": "agate-run",
        })
    except Exception as exc:
        sys.stderr.write(f"agate-run WARNING: cmd_run 事件写入失败（不阻断）: {exc}\n")


def main(argv):
    args = list(argv)
    baseline = BASELINE_FLAG in args
    args = [a for a in args if a != BASELINE_FLAG]
    if len(args) != 1:
        return _usage_error("用法: agate-run [--baseline] <命令>")

    project_root = os.getcwd()
    cfg = read_project_config(project_root)
    command, index = _resolve_command(cfg, args[0])
    if command is None:
        sys.stderr.write(
            "agate-run: 命令未在 agate.config.yaml 的 verify.commands 中声明"
            f"（不可绕开路径拒绝执行）: {args[0]}\n"
        )
        return 1

    exit_code, output = _run_command(command)
    sys.stdout.write(output)
    sys.stdout.flush()

    evidence_path = _evidence_path(cfg, project_root, index)
    baseline_mismatch = False
    if baseline:
        ignored = _is_ignored(project_root, evidence_path)
        if ignored is False:
            sys.stderr.write(
                "agate-run: 证据文件未被 .gitignore 覆盖（ignore 检查失败，会污染仓库）: "
                f"{evidence_path}\n"
            )
            _record_cmd_run(command, exit_code)
            return 1
        if ignored is None:
            sys.stderr.write(
                "WARNING: 无法判定证据文件是否被 .gitignore 覆盖（非 git 仓库或 git 不可用），"
                "跳过 ignore 检查\n"
            )
        if not os.path.isfile(evidence_path):
            _write_evidence(evidence_path, output)
        elif _read_bytes(evidence_path) != output.encode("utf-8"):
            baseline_mismatch = True
    elif os.path.isfile(evidence_path) and _read_bytes(evidence_path) != output.encode("utf-8"):
        baseline_mismatch = True

    if baseline_mismatch:
        sys.stderr.write(
            "agate-run: baseline mismatch（证据与基线逐字节不一致，diff 已客观报出）: "
            f"{evidence_path}\n"
        )
        _record_cmd_run(command, exit_code)
        return 1

    _record_cmd_run(command, exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
