#!/usr/bin/env python3
"""agate-state-set.py — 任务状态写入工具（TAG0050 批 A3，设计 §2.7）

协议不再提供"手改 .state.yaml"的路径：phase / 元数据 / 取消标记一律经本工具写入。
写入前用 `check-state-transition.py` 的**纯函数** `check_transition` 做与 pre-commit
同源的转移校验（以 **HEAD 版本**为 old_state），因此"工具当时判定合法"与"提交时判定
合法"一致。

用法：
  agate-state-set.py <TASK_DIR> phase <Pn|PAUSED|READY|DONE>
  agate-state-set.py <TASK_DIR> meta.priority low
  agate-state-set.py <TASK_DIR> cancel --reason "…"
  agate-state-set.py <TASK_DIR> --list

写入方式：原子替换文件（临时文件 + os.replace），随后 `git add`（若在 git 仓库内）。
**不写事件**——state_transition 事件由 pre-commit 统一写入（设计 §2.7）。

平台无关：显式 utf-8；无系统临时目录字面量（用 tempfile）；解释器一律 sys.executable。
Python 3.8+（禁 match / str.removeprefix）。
"""

import argparse
import importlib.util
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-state-set: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(1)

try:
    from agate_common import run_git
except Exception:  # pragma: no cover - 安装破损时降级（git 操作 no-op）
    run_git = None

_PHASE_RE = re.compile(r"^(P[0-8]|PAUSED|READY|DONE)$")
_CONTROL = ("PAUSED", "READY", "DONE")
_STATE_NAME = ".state.yaml"
_LEDGER_NAME = "gate-events.jsonl"


def _load_check_transition():
    """从 check-state-transition.py 载入纯函数 check_transition（连字符文件名经 importlib）。"""
    path = os.path.join(SCRIPT_DIR, "check-state-transition.py")
    spec = importlib.util.spec_from_file_location("_agate_check_state_transition", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_transition


def _now_ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg, code=1):
    sys.stderr.write("agate-state-set: " + msg + "\n")
    sys.exit(code)


def _state_path(task_dir):
    return os.path.join(task_dir, _STATE_NAME)


def _read_state(task_dir):
    path = _state_path(task_dir)
    if not os.path.isfile(path):
        _die(f".state.yaml 不存在：{path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        _die(f".state.yaml 解析失败：{exc}")
    if not isinstance(data, dict):
        _die(".state.yaml 不是映射")
    return data


def _atomic_write(path, text):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _write_state(task_dir, data):
    path = _state_path(task_dir)
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    _atomic_write(path, text)
    _git_add(task_dir, path)


def _repo_root(task_dir):
    if run_git is None:
        return None
    rc, out = run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)
    return out.strip() if rc == 0 and out.strip() else None


def _git_add(task_dir, path):
    repo = _repo_root(task_dir)
    if repo is None:
        return
    rel = os.path.relpath(path, repo).replace(os.sep, "/")
    run_git(["add", rel], cwd=repo)


def _head_phase(task_dir):
    """HEAD 版本 `.state.yaml` 的 phase；不在 git 仓库 / HEAD 无该文件 → 回退当前文件。"""
    repo = _repo_root(task_dir)
    path = _state_path(task_dir)
    if repo is not None:
        rel = os.path.relpath(path, repo).replace(os.sep, "/")
        rc, shown = run_git(["show", "HEAD:" + rel], cwd=repo)
        if rc == 0 and shown:
            try:
                data = yaml.safe_load(shown)
                if isinstance(data, dict) and isinstance(data.get("phase"), str):
                    return data["phase"]
            except Exception:
                pass
    data = _read_state(task_dir)
    return str(data.get("phase", "") or "")


def _phase_num(phase):
    m = re.match(r"^P([0-8])$", phase or "")
    return int(m.group(1)) if m else None


def _declared_phases(task_dir):
    """读 P1-requirements.md 的 `phases: [...]`（frontmatter 或正文）→ set；读不到 → None。"""
    p1 = os.path.join(task_dir, "P1-requirements.md")
    if not os.path.isfile(p1):
        return None
    try:
        with open(p1, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.search(r"^phases:\s*\[([^\]]*)\]", text, re.M)
    if not m:
        return None
    items = [x.strip().strip("'\"") for x in m.group(1).split(",")]
    return {x for x in items if x}


def _forward_multi_jump_error(old_phase, new_phase, task_dir):
    """前向跨阶（delta ≥ 2）默认拒绝；仅当被跨过的阶段均**未**声明（已裁剪）时放行。

    与 pre-commit（`check-state-transition.py`）不同：提交期允许前向跳（裁剪合法，由目标
    阶段产出文件兜底，见 state-machine.md）；而 state-set 是**推荐写入路径**，对前向跨阶
    从严——要求被跨过的阶段已从 P1 `phases` 中裁掉，否则提示用阶段产出与 gate 兜底。
    """
    old_num = _phase_num(old_phase)
    new_num = _phase_num(new_phase)
    if old_num is None or new_num is None:
        return None
    if new_num - old_num < 2:
        return None
    declared = _declared_phases(task_dir)
    skipped = {f"P{i}" for i in range(old_num + 1, new_num)}
    if declared is not None and not (skipped & declared):
        return None  # 被跨阶段均已裁剪 → 放行
    return (
        f"前向跨阶 P{old_num}→P{new_num} 被拒绝：被跨过的阶段 "
        f"{'/'.join(sorted(skipped))} 仍在 P1 phases 中声明。若确为裁剪，请先从 P1 phases "
        f"移除对应阶段；否则请逐阶推进（P{old_num}→P{old_num + 1}）。"
    )


def _is_retreat(old_phase, new_phase):
    old_num = _phase_num(old_phase)
    new_num = _phase_num(new_phase)
    return old_num is not None and new_num is not None and new_num < old_num


def _retreat_retries(data, new_phase):
    retries = data.get("retries")
    if not isinstance(retries, dict):
        retries = {}
        data["retries"] = retries
    attempts = retries.get(new_phase)
    if not isinstance(attempts, list):
        attempts = []
    attempts.append({"attempt": len(attempts) + 1, "ts": _now_ts(), "reason": "retreat via agate-state-set"})
    retries[new_phase] = attempts


def _cmd_phase(task_dir, new_phase, check_transition):
    if not _PHASE_RE.match(new_phase or ""):
        _die(f"非法 phase 值：{new_phase!r}（合法：P0-P8 / PAUSED / READY / DONE）")
    data = _read_state(task_dir)
    old_phase = _head_phase(task_dir)
    # 构造**拟写入**状态（回退时含 retries），供 check_transition 的 retries 对应性校验使用。
    prospective = dict(data)
    prospective["phase"] = new_phase
    if _is_retreat(old_phase, new_phase):
        _retreat_retries(prospective, new_phase)
    errors = check_transition(
        old_phase, new_phase, task_dir,
        state_file=_state_path(task_dir), state_basename=_STATE_NAME,
        state_data=prospective,
    )
    fwd = _forward_multi_jump_error(old_phase, new_phase, task_dir)
    if fwd:
        errors = [*errors, fwd]
    if errors:
        for e in errors:
            sys.stderr.write("GATE STATE: " + str(e) + "\n")
        _die(f"phase 转换 {old_phase or '(无)'} → {new_phase} 被拒绝（{len(errors)} 条）")
    _write_state(task_dir, prospective)
    sys.stderr.write(f"agate-state-set: {old_phase or '(无)'} → {new_phase} 已写入\n")


def _cmd_meta(task_dir, key, value):
    data = _read_state(task_dir)
    parts = key.split(".")
    if len(parts) != 2 or parts[0] != "meta":
        _die(f"meta 写入须为 meta.<field>，实际 {key!r}")
    field = parts[1]
    if field not in ("title", "priority", "depends"):
        _die(f"未知 meta 字段：{field}（合法：title / priority / depends）")
    if field == "priority" and value not in ("high", "medium", "low"):
        _die(f"meta.priority 非法值：{value!r}（合法：high / medium / low）")
    meta = data.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    meta[field] = value
    data["meta"] = meta
    _write_state(task_dir, data)
    sys.stderr.write(f"agate-state-set: meta.{field} = {value} 已写入\n")


def _cmd_cancel(task_dir, reason):
    if not reason:
        _die("cancel 须提供 --reason")
    data = _read_state(task_dir)
    data["cancelled"] = {"reason": reason}
    _write_state(task_dir, data)
    sys.stderr.write(f"agate-state-set: 已标记 cancelled（{reason}）\n")


def _cmd_list():
    sys.stderr.write(
        "agate-state-set 用法：\n"
        "  agate-state-set.py <TASK_DIR> phase <Pn|PAUSED|READY|DONE>\n"
        "  agate-state-set.py <TASK_DIR> meta.priority low\n"
        "  agate-state-set.py <TASK_DIR> cancel --reason \"…\"\n"
        "  agate-state-set.py <TASK_DIR> --list\n"
        "字段：phase（agent 声明）/ meta.{title,priority,depends} / cancelled.reason；\n"
        "status 是系统字段（由 phase + cancelled 现算），不提供 setter。\n"
    )
    sys.exit(0)


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        _cmd_list()
    if argv[0] == "--list":
        _cmd_list()
    task_dir = argv[0]
    if not os.path.isdir(task_dir):
        _die(f"任务目录不存在：{task_dir}")
    rest = argv[1:]
    if not rest:
        _die("缺少子命令（phase / meta.<field> / cancel / --list）")
    cmd = rest[0]
    if cmd == "phase":
        if len(rest) < 2:
            _die("phase 须提供目标值")
        _cmd_phase(task_dir, rest[1], _load_check_transition())
    elif cmd == "cancel":
        ap = argparse.ArgumentParser()
        ap.add_argument("--reason", default="")
        ns = ap.parse_args(rest[1:])
        _cmd_cancel(task_dir, ns.reason)
    elif cmd.startswith("meta."):
        if len(rest) < 2:
            _die(f"{cmd} 须提供值")
        _cmd_meta(task_dir, cmd, rest[1])
    else:
        _die(f"未知子命令：{cmd!r}")
    sys.exit(0)


if __name__ == "__main__":
    main()
