#!/usr/bin/env python3
"""agate-run.py — 执行层：在不可绕开路径上执行声明中的验证命令（TAG0042 批 3）。

职责（P1 BDD-9/10/11/12，P2-design §4.2）：
  * BDD-9  从**声明**取命令（项目 `agate.config.yaml` 的 `verify.commands`；给了 `--task` 时**亦可**
           取自该任务 `P2-design.md` 的 `gate_commands` 块——RM-AG0102 采纳），经 bash 执行并**如实传播退出码**
           （POSIX 开 `pipefail`，避免 `cmd | tail` 吞掉左侧失败）；非 POSIX 平台显式退化 +
           WARNING（绝不静默报绿，ADR-015 手段②）。普通运行（无 `--baseline`）**只返回命令自身
           退出码**，不与 `.out` 证据比对（I-2 hotfix：陈旧证据不得致假失败）。
  * BDD-10 `--baseline` 首次落盘 `.out` 证据；后续执行与之**逐字节比对**，不一致时**实际打印
           逐行 diff** 再返回非 0（I-2 hotfix）。
  * BDD-11 证据文件须被 `.gitignore` 覆盖（`git check-ignore` 判定），否则报错（不落盘）。
  * BDD-12 执行后经 `agate_common.append_event`（**唯一写路径**）追加 `cmd_run` 事件；目标
           账本目录由 `AGATE_TASK_DIR` env 指定（不直接写 gate-events.jsonl，避免破链）。

命令解析：CLI 实参须**精确匹配** `verify.commands` 中的一条（不可绕开路径拒绝执行未声明命令）。
证据槽位：证据文件按命令在 `verify.commands` 中的**下标**命名（`{paths.evidence}/cmd-<n>.out`）——
下标在命令文本变更后保持稳定，故「同一验证槽位输出改变」可被客观比对（BDD-10）。

平台无关：仅标准库；无系统临时目录字面量；显式 encoding="utf-8"。
Python 3.8+（禁 match / str.removeprefix）。
"""

import difflib
import hashlib
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from agate_common import (  # noqa: E402
    append_event,
    is_gate_meta_key,
    parse_gate_commands_block,
    project_root,
    read_ledger_events,
    read_project_config,
    run_git,
    strip_paired_quotes,
)

EVIDENCE_SUFFIX = ".out"
BASELINE_FLAG = "--baseline"
TASK_FLAG = "--task"
DEFAULT_EVIDENCE_DIR = ".agate-evidence"
RUNS_DIRNAME = "runs"


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


def _resolve_from_task(task_dir, arg):
    """**任务源**：`P2-design.md` 的 `gate_commands` 块（`--task` 时的第二命令源）。

    **为什么需要**：P5 的验证命令在 **P2 声明**（`gate_commands.P5`，由 P5 卡规定执行），
    而项目级 `agate.config.yaml` 的 `verify.commands` 未必有。此前 `agate-run` **只认 config**
    ⇒ 零采纳（协议流程里没有入口）。本函数让 `agate-run --task <TASK_DIR> <cmd>` 同时认两处，
    使 P5 的执行能走「**白名单 + 证据（runs/<k>.log）+ 账本 cmd_run**」而不再只是自述。

    口径与 `agate-read-p5-commands.py` 一致：解析经 `agate_common.parse_gate_commands_block`
    （**同一共享解析，非重写**），槽位下标按**待执行命令**序号计（排除 `_formatter` /
    `_timeout_seconds` 元信息键，用 `agate_common.is_gate_meta_key`）。
    未命中 → (None, -1)。
    """
    p2 = os.path.join(str(task_dir), "P2-design.md")
    if not os.path.isfile(p2):
        return None, -1
    try:
        with open(p2, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None, -1
    has_block, items = parse_gate_commands_block(text)
    if not has_block:
        return None, -1
    index = 0
    for key, value in items:
        if is_gate_meta_key(key):
            continue
        # 与 `agate-read-p5-commands.py` **同一剥离口径**（成对引号才剥，RM-AG0092/DEBT0047）
        if strip_paired_quotes(value.strip()) == arg:
            return arg, index
        index += 1
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


def _baseline_diff(evidence_bytes, output):
    """由证据（基线）字节与本次输出生成**逐行 unified diff** 文本（I-2：实际打印 diff）。

    逐字节不同但逐行相同时（如尾行换行差异），unified diff 可能为空——此时给出字节级提示，
    保证「已比对出差异」的结论始终伴随可读证据（不回落为只写一行抽象字样）。
    """
    baseline_text = evidence_bytes.decode("utf-8", errors="replace")
    diff_lines = difflib.unified_diff(
        baseline_text.splitlines(),
        output.splitlines(),
        fromfile="baseline",
        tofile="current",
        lineterm="",
    )
    rendered = "\n".join(diff_lines)
    if rendered.strip():
        return rendered
    return (
        f"（逐行内容相同但逐字节不一致：基线 {len(evidence_bytes)} 字节，"
        f"本次 {len(output.encode('utf-8'))} 字节）"
    )


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


def _record_cmd_run(cmd, exit_code, task_dir=None, k=None, log=None, sha256=None):
    """经 append_event（唯一写路径）追加 cmd_run 事件；未指定任务目录 → 跳过。"""
    task_dir = task_dir or os.environ.get("AGATE_TASK_DIR", "")
    if not task_dir:
        return
    event = {
        "event": "cmd_run",
        "cmd": cmd,
        "exit": exit_code,
        "runner": "agate-run",
    }
    # TAG0050 批 D（设计 §5.3）：--task 时记录 run:<k> 引用所需的 k / log / sha256。
    if k is not None:
        event["k"] = k
    if log is not None:
        event["log"] = log
    if sha256 is not None:
        event["sha256"] = sha256
    try:
        append_event(task_dir, event)
    except Exception as exc:
        sys.stderr.write(f"agate-run WARNING: cmd_run 事件写入失败（不阻断）: {exc}\n")


def _next_run_index(task_dir):
    """下一个 run 编号 k（任务内自增；账本中 cmd_run.k 的最大值 + 1）。"""
    max_k = 0
    for ev in read_ledger_events(task_dir):
        if ev.get("event") != "cmd_run":
            continue
        try:
            max_k = max(max_k, int(ev.get("k", 0) or 0))
        except (TypeError, ValueError):
            continue
    return max_k + 1


def _git_head(task_dir):
    rc, out = run_git(["rev-parse", "HEAD"], cwd=task_dir)
    return out.strip() if rc == 0 else ""


def _write_run_log(task_dir, k, cmd, exit_code, output):
    """把本次运行写入 `<task>/runs/<k>.log`（头部 cmd/cwd/git_head/起止时间，尾行 EXIT_CODE）。

    返回 (绝对路径, sha256)。日志是任务证据，**必须入库**（未被 ignore）。
    """
    runs_dir = os.path.join(task_dir, RUNS_DIRNAME)
    os.makedirs(runs_dir, exist_ok=True)
    log_path = os.path.join(runs_dir, f"{k}.log")
    start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    head = _git_head(task_dir)
    body = (
        f"# cmd: {cmd}\n"
        f"# cwd: {os.getcwd()}\n"
        f"# git_head: {head}\n"
        f"# started: {start}\n"
        f"{output}"
        f"{'' if output.endswith(chr(10)) or output == '' else chr(10)}"
        f"EXIT_CODE: {exit_code}\n"
    )
    data = body.encode("utf-8")
    with open(log_path, "wb") as handle:
        handle.write(data)
    return log_path, hashlib.sha256(data).hexdigest()


def _run_with_task(task_dir, command, exit_code, output):
    """`--task`：写任务内 `runs/<k>.log` + cmd_run(k/log/sha256)，返回退出码。"""
    repo_root = project_root(task_dir)
    k = _next_run_index(task_dir)
    log_path, digest = _write_run_log(task_dir, k, command, exit_code, output)
    ignored = _is_ignored(repo_root, log_path)
    if ignored is True:
        sys.stderr.write(
            "agate-run: 任务内日志被 .gitignore 覆盖（证据须入库）: "
            f"{log_path}——请在 .gitignore 加取反规则 "
            "`!agate-workspace/tasks/**/runs/**`\n"
        )
        return 1
    log_rel = os.path.relpath(log_path, repo_root)
    _record_cmd_run(command, exit_code, task_dir=task_dir, k=k, log=log_rel, sha256=digest)
    sys.stderr.write(f"agate-run: 任务内日志 run:{k} → {log_rel}\n")
    return exit_code


def main(argv):
    args = list(argv)
    baseline = BASELINE_FLAG in args
    args = [a for a in args if a != BASELINE_FLAG]
    # TAG0050 批 D（设计 §5.3）：`--task <TASK_DIR>` 走任务内日志 run:<k> 路径。
    task_dir = ""
    if TASK_FLAG in args:
        idx = args.index(TASK_FLAG)
        if idx + 1 >= len(args):
            return _usage_error("用法: agate-run [--baseline] [--task <TASK_DIR>] <命令>")
        task_dir = args[idx + 1]
        del args[idx:idx + 2]
    if len(args) != 1:
        return _usage_error("用法: agate-run [--baseline] [--task <TASK_DIR>] <命令>")

    project_root_dir = os.getcwd()
    cfg = read_project_config(project_root_dir)
    command, index = _resolve_command(cfg, args[0])
    if command is None and task_dir:
        # RM-AG0102 采纳：`--task` 时同时认任务源（P2 的 gate_commands）——P5 的命令在此声明
        command, index = _resolve_from_task(task_dir, args[0])
    if command is None:
        _sources = "agate.config.yaml 的 verify.commands"
        if task_dir:
            _sources += " 或该任务 P2-design.md 的 gate_commands"
        sys.stderr.write(
            f"agate-run: 命令未在 {_sources} 中声明（不可绕开路径拒绝执行）: {args[0]}\n"
        )
        return 1

    exit_code, output = _run_command(command)
    sys.stdout.write(output)
    sys.stdout.flush()

    if task_dir:
        return _run_with_task(task_dir, command, exit_code, output)

    evidence_path = _evidence_path(cfg, project_root_dir, index)
    baseline_mismatch = False
    mismatch_diff = ""
    if baseline:
        ignored = _is_ignored(project_root_dir, evidence_path)
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
            mismatch_diff = _baseline_diff(_read_bytes(evidence_path), output)

    if baseline_mismatch:
        sys.stderr.write(
            "agate-run: baseline mismatch（证据与基线逐字节不一致）: "
            f"{evidence_path}\n"
        )
        sys.stderr.write(mismatch_diff + "\n")
        _record_cmd_run(command, exit_code)
        return 1

    _record_cmd_run(command, exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
