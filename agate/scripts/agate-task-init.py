#!/usr/bin/env python3
"""agate-task-init.py — 任务初始化入口（TAG0050 批 A1，设计 §2.2）

新建任务必须经本工具：创建目录 + `.state.yaml` + P0-brief 骨架，并在账本**第 1 行**
写入 `task_created`（记录 contract_level = 当前契约等级）。存量任务迁移入口：

  agate-task-init.py <TASK_ID> --slug <slug> --title "<一句话>" [--priority high|medium|low] [--depends ID,ID]
  agate-task-init.py --existing <TASK_DIR>   # 目录已手工建好、账本未被 git 跟踪：前置写入创建事件并重建哈希链
  agate-task-init.py --adopt <TASK_DIR>      # 存量任务主动迁入当前等级（写 task_adopted）
  agate-task-init.py --upgrade <TASK_DIR>    # 非 legacy 任务升到当前等级（写 task_upgraded）

约定：TASK_ID 须匹配 `^[A-Z]+[0-9]+$`；tasks 目录下不得存在任何以 `{ID}-` 开头的目录。
所有文本读写显式 encoding="utf-8"；Python 3.8+（禁 match / str.removeprefix）。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from agate_common import (
        GENESIS_HASH,
        LEDGER_NAME,
        TASK_ID_RE,
        append_event,
        current_level,
        project_root,
        read_ledger_events,
        resolve_workspace,
        run_git,
        task_level,
    )
except Exception as exc:  # pragma: no cover - 安装破损时 fail-closed
    sys.stderr.write(f"agate-task-init: 无法加载 agate_common.py（需 Python 3 + pyyaml）: {exc}\n")
    sys.exit(1)


P0_BRIEF_SKELETON = (
    "# P0-brief — {title}\n\n"
    "> 主 Agent 亲自填写（P0 产出）。\n\n"
    "```yaml\n"
    'task: "{title}"\n'
    "known_risks: []\n"
    "env_constraints:\n"
    '  debug_env: ""\n'
    "executor_env:\n"
    '  platform: "unknown"\n'
    "  has_task_tool: false\n"
    "  has_local_runtime: false\n"
    '  network: "unknown"\n'
    "```\n"
)


def _now_ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _die(msg):
    sys.stderr.write("agate-task-init: " + msg + "\n")
    sys.exit(1)


def _state_text(task_id, phase):
    return f"task_id: {task_id}\nphase: {phase}\nretries: {{}}\n"


def _workspace_paths(start_dir):
    root = project_root(start_dir)
    _workspace, tasks_dir = resolve_workspace(root)
    return root, tasks_dir


def _rebuild_chain(events):
    """按事件列表重建哈希链（补 prev_hash/ts），返回账本文本行列表。"""
    lines = []
    prev = GENESIS_HASH
    for idx, ev in enumerate(events):
        row = dict(ev)
        row.pop("prev_hash", None)
        row.setdefault("ts", f"2026-10-07T00:00:{idx:02d}.000000Z")
        row["prev_hash"] = prev
        line = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        lines.append(line)
        prev = hashlib.sha256(line.encode("utf-8")).hexdigest()
    return lines


def _current_phase(task_dir):
    state = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(state):
        return "P0"
    try:
        import yaml
        with open(state, encoding="utf-8", errors="replace") as fh:
            data = yaml.safe_load(fh)
    except Exception:
        return "P0"
    if isinstance(data, dict) and isinstance(data.get("phase"), str) and data["phase"]:
        return data["phase"]
    return "P0"


def _git_has_path_in_head(repo_root, rel_path):
    rc, out = run_git(["ls-tree", "-r", "--name-only", "HEAD", "--", rel_path], cwd=repo_root)
    return rc == 0 and bool(out.strip())


def _staged_rename_targets(repo_root):
    """暂存区中作为改名目标的路径集合（`git diff --cached -M --name-status` 的 R 目标）。"""
    targets = set()
    rc, out = run_git(["diff", "--cached", "-M", "--name-status"], cwd=repo_root)
    if rc != 0:
        return targets
    for line in out.splitlines():
        parts = line.split("\t")
        if parts and parts[0].startswith("R") and len(parts) >= 3:
            targets.add(parts[2].strip())
    return targets


def _cmd_new(args):
    if not TASK_ID_RE.match(args.task_id or ""):
        _die(f"TASK_ID 非法：{args.task_id!r}（须匹配 {TASK_ID_RE.pattern}）")
    if not args.slug:
        _die("新建任务须提供 --slug")
    repo_root, tasks_dir = _workspace_paths(os.getcwd())
    if not os.path.isdir(tasks_dir):
        os.makedirs(tasks_dir)
    prefix = args.task_id + "-"
    for name in sorted(os.listdir(tasks_dir)):
        if name.startswith(prefix):
            _die(f"tasks 目录下已存在以 {prefix} 开头的目录：{name}")
    task_dir = os.path.join(tasks_dir, args.task_id + "-" + args.slug)
    if os.path.exists(task_dir):
        _die(f"目标目录已存在：{task_dir}")
    os.makedirs(task_dir)

    with open(os.path.join(task_dir, ".state.yaml"), "w", encoding="utf-8") as fh:
        fh.write(_state_text(args.task_id, "P0"))
    with open(os.path.join(task_dir, "P0-brief.md"), "w", encoding="utf-8") as fh:
        fh.write(P0_BRIEF_SKELETON.format(title=args.title or args.task_id))

    level = current_level(SCRIPT_DIR)
    append_event(task_dir, {
        "event": "task_created",
        "task_id": args.task_id,
        "contract_level": level if level is not None else 1,
        "agate_version": os.environ.get("AGATE_VERSION", ""),
        "resolver": os.environ.get("AGATE_ROOT", ""),
    })
    run_git(["add", os.path.relpath(task_dir, repo_root)], cwd=repo_root)
    sys.stderr.write(f"agate-task-init: 已创建 {task_dir}（等级 {level}）\n")
    sys.exit(0)


def _cmd_existing(args):
    task_dir = os.path.abspath(args.existing)
    if not os.path.isdir(task_dir):
        _die(f"--existing 目录不存在：{task_dir}")
    repo_root, _tasks_dir = _workspace_paths(task_dir)
    ledger = os.path.join(task_dir, LEDGER_NAME)
    rel_ledger = os.path.relpath(ledger, repo_root).replace(os.sep, "/")
    if _git_has_path_in_head(repo_root, rel_ledger):
        _die(f"--existing 拒绝：账本在 HEAD 中已存在（{rel_ledger}）")
    if rel_ledger in _staged_rename_targets(repo_root):
        _die(f"--existing 拒绝：账本是暂存区改名操作的目标（{rel_ledger}）")
    events = read_ledger_events(task_dir)
    for ev in events:
        if ev.get("event") in ("task_created", "task_adopted"):
            _die("--existing 拒绝：账本已含 task_created/task_adopted")
    level = current_level(SCRIPT_DIR)
    head = {
        "event": "task_created",
        "task_id": os.path.basename(task_dir).split("-", 1)[0],
        "contract_level": level if level is not None else 1,
        "agate_version": os.environ.get("AGATE_VERSION", ""),
        "resolver": os.environ.get("AGATE_ROOT", ""),
    }
    lines = _rebuild_chain([head, *events])
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    run_git(["add", rel_ledger], cwd=repo_root)
    sys.stderr.write(f"agate-task-init: 已为 {task_dir} 前置写入 task_created 并重建哈希链\n")
    sys.exit(0)


def _cmd_adopt(args):
    task_dir = os.path.abspath(args.adopt)
    if not os.path.isdir(task_dir):
        _die(f"--adopt 目录不存在：{task_dir}")
    for ev in read_ledger_events(task_dir):
        if ev.get("event") == "task_created":
            _die("--adopt 拒绝：账本已含 task_created（请用 --upgrade）")
        if ev.get("event") == "task_adopted":
            _die("--adopt 拒绝：账本已含 task_adopted")
    level = current_level(SCRIPT_DIR)
    append_event(task_dir, {
        "event": "task_adopted",
        "contract_level": level if level is not None else 1,
        "at_phase": _current_phase(task_dir),
    })
    sys.stderr.write(f"agate-task-init: 已迁入 {task_dir}（等级 {level}）\n")
    sys.exit(0)


def _cmd_upgrade(args):
    task_dir = os.path.abspath(args.upgrade)
    if not os.path.isdir(task_dir):
        _die(f"--upgrade 目录不存在：{task_dir}")
    from_level = task_level(task_dir, SCRIPT_DIR)
    if from_level is None:
        _die("--upgrade 拒绝：该任务是 legacy（无创建事件），请用 --adopt")
    level = current_level(SCRIPT_DIR)
    if level is None or level <= from_level:
        _die(f"--upgrade 拒绝：当前等级 {level} 未高于任务等级 {from_level}")
    append_event(task_dir, {
        "event": "task_upgraded",
        "from_level": from_level,
        "to_level": level,
        "at_phase": _current_phase(task_dir),
    })
    sys.stderr.write(f"agate-task-init: 已升级 {task_dir}（{from_level} → {level}）\n")
    sys.exit(0)


def main():
    ap = argparse.ArgumentParser(description="agate 任务初始化入口（TAG0050 批 A1）")
    ap.add_argument("task_id", nargs="?", help="任务 ID（^[A-Z]+[0-9]+$）")
    ap.add_argument("--slug", help="任务目录 slug（{ID}-{slug}）")
    ap.add_argument("--title", help="一句话任务标题")
    ap.add_argument("--priority", choices=["high", "medium", "low"], default=None)
    ap.add_argument("--depends", default=None, help="依赖的任务 ID，逗号分隔")
    ap.add_argument("--existing", help="目录已手工建好、账本未被 git 跟踪：前置写入创建事件")
    ap.add_argument("--adopt", help="存量任务主动迁入当前等级")
    ap.add_argument("--upgrade", help="非 legacy 任务升到当前等级")
    args = ap.parse_args()

    chosen = [x for x in (args.existing, args.adopt, args.upgrade) if x]
    if len(chosen) > 1:
        _die("--existing / --adopt / --upgrade 互斥，只能选一个")
    if args.existing:
        _cmd_existing(args)
    if args.adopt:
        _cmd_adopt(args)
    if args.upgrade:
        _cmd_upgrade(args)
    if not args.task_id:
        _die("缺少 TASK_ID（或使用 --existing/--adopt/--upgrade）")
    _cmd_new(args)


if __name__ == "__main__":
    main()
