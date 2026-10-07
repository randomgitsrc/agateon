# agate/tests/helpers_tag0050.py — TAG0050（任务数据契约）P3 测试共享 helper。
#
# 设计原则：
#   * **不在模块级引用任何未实现符号**（避免 collection error 被判 A 类假红灯）——
#     未实现符号一律经 `agate_common_module()` / `init_task_via_conftest()` 在**运行期**取用，
#     缺失时以 AttributeError 表现（运行期失败 = B 类真红灯）。
#   * 平台无关：不裸 `python3`（用 `sys.executable` / `python_exe` fixture）、不写字面系统
#     临时目录（用 pytest `tmp_path`）、不硬编码 PATH。
#   * 账本构造与 `agate_common.append_event` 同源（首行 GENESIS、逐行 sha256 链、ts 单调），
#     供 A1 账本完整性用例复用。

import hashlib
import json
import os
import shutil
import sys

# 与 agate_common.GENESIS_HASH 同源（sha256(b"")）；硬编码是刻意的：
# helper 不得在模块级 import 被测模块。
GENESIS_HASH = hashlib.sha256(b"").hexdigest()


def install_pre_commit_hook(repo, agate_scripts):
    """安装 pre-commit hook 指向本 checkout 的 pre-commit-gate.sh。

    Linux 用 POSIX 软链；Windows（Git Bash ln 退化为复制）用复制。
    """
    hook = os.path.join(str(repo), ".git", "hooks", "pre-commit")
    src = str(os.path.join(str(agate_scripts), "pre-commit-gate.sh"))
    if sys.platform == "win32":
        shutil.copy2(src, hook)
    else:
        os.symlink(src, hook)
    os.chmod(hook, 0o755)


def commit_with_hook(run_cli, agate_root, repo, *args):
    """经 hook 提交（AGATE_ROOT 经 env 显式传给 hook）。"""
    return run_cli(
        "git",
        "-C",
        str(repo),
        "commit",
        *args,
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


def run_gate(run_cli, python_exe, agate_scripts, agate_root, script, *args, cwd=None):
    """直接运行协议脚本（不经 hook），AGATE_ROOT 显式传入。"""
    return run_cli(
        python_exe,
        str(os.path.join(str(agate_scripts), script)),
        *args,
        cwd=str(cwd) if cwd is not None else None,
        env={"AGATE_ROOT": str(agate_root)},
    )


def write_ledger(task_dir, events):
    """构造一条**哈希链合法**的 gate-events.jsonl（供账本事件规则用例）。

    返回写入路径。events 为事件 dict 列表；自动补 ts（单调）与 prev_hash。
    """
    lines = []
    prev = GENESIS_HASH
    for idx, ev in enumerate(events):
        row = dict(ev)
        row.setdefault("ts", f"2026-10-07T00:00:{idx:02d}.000000Z")
        row["prev_hash"] = prev
        line = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        lines.append(line)
        prev = hashlib.sha256(line.encode("utf-8")).hexdigest()
    path = os.path.join(str(task_dir), "gate-events.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def agate_common_module(agate_scripts):
    """运行期取用 agate_common（未实现的新符号在调用处以 AttributeError 表现）。"""
    sp = str(agate_scripts)
    if sp not in sys.path:
        sys.path.insert(0, sp)
    import agate_common

    return agate_common


def init_task_via_conftest(*args, **kwargs):
    """运行期取用 conftest.init_task（批 A1 交付物；当前缺失 → AttributeError 红灯）。"""
    import conftest

    return conftest.init_task(*args, **kwargs)


def make_git_repo(tmp_path, git_repo):
    """建一个含初始提交的 git 仓库，返回 repo 路径。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.stage("README.md")
    git_repo.commit("init")
    return repo
