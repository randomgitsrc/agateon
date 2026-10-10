#!/usr/bin/env python3
"""agate-changes.py — 显示与指定 tag 之间的协议变更（commit + 受影响文件）

用法：
  python3 ~/.agate/scripts/agate-changes.py                    # 默认上一个 tag → HEAD
  python3 ~/.agate/scripts/agate-changes.py v0.4.0..v0.5.0    # 任意范围
  python3 ~/.agate/scripts/agate-changes.py --check-upstream   # 查远端是否有新版本

用途：agent 启动时快速掌握协议变化，对比'上次会话知道的版本'和当前版本
输出：commits + 受影响的协议文件 + 是否触及 Pre-commit 检查总览
exit 0：成功；exit 1：无法解析脚本路径 / 找不到 agate git 仓库 / 无效 ref。

从 agate-changes.sh 迁移（TAG0010 批次 1d）。迁移说明：readlink -f →
os.path.realpath；find .git 逐级上溯 → os.path 循环；git -C 调用 →
subprocess.run(cwd=...)；sed 's/^/  /' → 行前缀 join；`sort -u` → sorted(set(...))；
`head -N` → 列表切片；`wc -l` → 换行计数；grep -E 分类 → re.search 命中判断。
"""

import os
import re
import subprocess
import sys

try:
    from agate_common import default_branch as _default_branch
except Exception:  # pragma: no cover - 安装破损时降级（范围行退化为不显示）
    _default_branch = None

_CORE_FILES = (
    r"^agate/WORKFLOW\.md$|^agate/state-machine\.md$|^agate/dispatch-protocol\.md$"
)
_SCRIPT_FILES = r"^agate/scripts/.*\.sh$|^agate/scripts/.*\.py$"
_ROLE_DIRS = r"^agate/assets/execution-roles/|^agate/assets/review-roles/"
_ENTRY_FILES = r"^agate/AGENTS\.md$|^agate/orchestrator-template\.md$"
_DOC_FILES = r"^README\.md$|^CHANGELOG\.md$"
_HIGH_IMPACT = (
    r"^agate/(WORKFLOW|state-machine|dispatch-protocol|orchestrator-template|AGENTS)\.md$"
    r"|^agate/assets/execution-roles/"
    r"|^agate/assets/review-roles/"
    r"|^agate/scripts/.*\.(sh|py)$"
)


def _find_git_root(start):
    """从 start 逐级向上找含 .git 的目录（等价 sh 的 _find_git_root，不含根目录本身）。"""
    d = os.path.normpath(start)
    while d != os.path.sep:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return ""


def _run_git(repo, args):
    """git -C 等价：cwd=repo 调 subprocess，返回 proc；git 不可用时返回 None。"""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None


def _git_ok(repo, args):
    """git 命令成功与否（等价 `git ... >/dev/null 2>&1`）。"""
    proc = _run_git(repo, args)
    return proc is not None and proc.returncode == 0


def _git_stdout(repo, args, fallback=""):
    """git -C 等价：stdout 去尾换行，失败返回 fallback。"""
    proc = _run_git(repo, args)
    if proc is None or proc.returncode != 0:
        return fallback
    return (proc.stdout or "").rstrip("\n")


def _first_line(text):
    """`| head -1` 等价：取第一行。"""
    return text.split("\n", 1)[0]


def _line_count(text):
    """`| wc -l` 等价：按换行计数。"""
    if not text:
        return 0
    return len(text.split("\n")) - 1


def _indent_lines(lines, limit=None):
    """`sed 's/^/  /'` + `head -N` 等价：每行前缀两空格，跳过空行。"""
    out = []
    for line in lines.split("\n")[:limit] if limit is not None else lines.split("\n"):
        if line:
            out.append("  " + line)
    return out


def _check_upstream(repo):
    """--check-upstream：查远端是否有新版本。"""
    local_tag = _git_stdout(repo, ["describe", "--tags", "--abbrev=0"], "untagged")
    _run_git(repo, ["fetch", "--all", "--tags", "--quiet"])
    upstream_tag = _first_line(_git_stdout(repo, ["tag", "--sort=-version:refname"]))

    lines = []
    if local_tag == upstream_tag:
        lines.append(f"agate 已是最新版本：{local_tag}")
    else:
        lines.append(f"agate 有新版本可用：{upstream_tag}（本地 {local_tag}）")
        lines.append("更新方式：cd <agate 仓库> && git pull")
        lines.append(
            "如果持续落后，检查 git remote 是否指向 "
            "https://github.com/randomgitsrc/agateon.git"
        )
        # 协议**不假设项目默认分支**（有的项目用 master/develop/自定义）：经单源解析；
        # 解析不可用（安装破损）时退化为不显示变更清单，不阻断。
        _branch = _default_branch(repo) if _default_branch else None
        if _branch is None:
            proc = None
        else:
            upstream_range = f"{local_tag}..origin/{_branch}"
            proc = _run_git(repo, ["log", "--oneline", upstream_range])
        commit_count = _line_count(proc.stdout) if proc is not None and proc.returncode == 0 else 0
        if commit_count > 0:
            lines.append("")
            lines.append(f"自 {local_tag} 以来的变更（{commit_count} commits）：")
            lines.extend(_indent_lines(proc.stdout, limit=10))
            if commit_count > 10:
                lines.append(f"  ...（共 {commit_count} commits，省略）")
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))


def main():
    script_real = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_real)
    if not script_dir:
        sys.stderr.write("ERROR: 无法解析脚本路径\n")
        sys.exit(1)

    git_toplevel = _find_git_root(script_dir)
    if not git_toplevel:
        sys.stderr.write("ERROR: 无法找到 agate git 仓库——脚本不在 agate 仓库内？\n")
        sys.exit(1)

    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if arg == "--check-upstream":
        _check_upstream(git_toplevel)
        return

    range_spec = arg

    if not range_spec:
        current_tag = _git_stdout(git_toplevel, ["describe", "--tags", "--abbrev=0"])
        if not current_tag:
            sys.stderr.write(
                f"ERROR: 无法找到当前 tag——显式指定：python3 {sys.argv[0]} v0.4.0..HEAD\n"
            )
            sys.exit(1)
        prev_tag = _first_line(
            _git_stdout(
                git_toplevel,
                ["tag", "--sort=-version:refname", "--merged", f"{current_tag}^"],
            )
        )
        range_spec = f"{prev_tag if prev_tag else current_tag}..HEAD"

    if ".." not in range_spec:
        range_spec = f"{range_spec}..HEAD"

    start = range_spec.split("..", 1)[0]
    end = range_spec.rsplit("..", 1)[1]
    if not _git_ok(git_toplevel, ["rev-parse", start]):
        sys.stderr.write(f"ERROR: '{start}' 不是有效 ref（tag/commit）\n")
        sys.exit(1)
    if not _git_ok(git_toplevel, ["rev-parse", end]):
        sys.stderr.write(f"ERROR: '{end}' 不是有效 ref（tag/commit）\n")
        sys.exit(1)

    lines = ["=== agate 协议变化 ===", f"范围：{range_spec}", ""]

    lines.append("--- commits ---")
    lines.extend(_indent_lines(_git_stdout(git_toplevel, ["log", "--oneline", range_spec])))

    lines.append("")
    lines.append("--- 协议文件改动 ---")
    changed_files = sorted(
        line for line in set(
            _git_stdout(git_toplevel, ["diff", "--name-only", "--diff-filter=acm", range_spec]).split("\n")
        ) if line
    )
    if not changed_files:
        lines.append("  （无文件改动）")
    else:
        lines.extend("  " + line for line in changed_files)

    lines.append("")
    lines.append("--- 重要性分类 ---")
    if any(re.search(_CORE_FILES, line) for line in changed_files):
        lines.append("  ⚠️  触及核心流程文件——orchestrator 必须仔细读")
    if any(re.search(_SCRIPT_FILES, line) for line in changed_files):
        lines.append("  ⚙️  触及 gate 检查脚本——commit 时行为可能变化")
    if any(re.search(_ROLE_DIRS, line) for line in changed_files):
        lines.append("  🎭  触及角色定义——subagent 行为可能变化")
    if any(re.search(_ENTRY_FILES, line) for line in changed_files):
        lines.append("  📖  触及入口/模板——orchestrator 启动行为可能变化")
    if any(re.search(_DOC_FILES, line) for line in changed_files):
        lines.append("  📜  触及对外文档")

    lines.append("")
    lines.append("--- 快速决策 ---")
    high_impact = sum(1 for line in changed_files if re.search(_HIGH_IMPACT, line))
    if high_impact == 0:
        lines.append("  当前变更影响小（无核心文件改动）——可只读 CHANGELOG.md 即可")
    elif high_impact < 3:
        lines.append(f"  中等变更（{high_impact} 个核心文件）——查阅变更涉及的协议文件")
    else:
        lines.append(f"  重大变更（{high_impact} 个核心文件）——完整重读所有协议文件")

    lines.append("")
    lines.append("=== 完毕 ===")
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
