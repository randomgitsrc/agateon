#!/usr/bin/env python3
"""commit-msg-self-gate.py — commit-msg hook 主程序（TAG0010 批次 3b）

迁移自 commit-msg-self-gate.sh（37 行）：检测 self-gate 触发文件的改动，要求 commit
message 含 self-gate-review: 路径（或 self-gate-skip: 理由）。WARNING 不拦截——
遵循 hook 鲁棒性优先原则（exit 0）。

sh 版将保留为薄壳（批次 3d：AGATE_ROOT 自定位 + python 探测 + exec py），本 py 承载
self-gate 触发面 grep + WARNING 判定逻辑。

CLI 契约：`commit-msg-self-gate.py COMMIT_MSG_FILE`（缺参 → 用法错误 exit 1，同 sh
`${1:?}` 语义）；self-gate 提示写 stderr；exit 0（永不拦截）。

Python 3.8+（无 match / str.removeprefix）；所有文本读写显式 encoding="utf-8"。
"""

import os
import re
import subprocess
import sys

try:
    from agate_common import run_git
except (ImportError, SystemExit):
    # agate_common 缺 pyyaml（SystemExit，模块顶部 fail-closed）/ 本体缺失（ImportError）
    # 时降级为本地 subprocess 实现——本 hook 是提示型永不阻断（exit 0），公共库依赖缺失
    # 不能让 commit 失败（对比批次 3a pre-commit-gate.py 的 fail-closed：那是阻断型 gate）。
    def run_git(args, cwd=None):
        try:
            proc = subprocess.run(
                ["git", *args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=cwd,
            )
            return proc.returncode, proc.stdout
        except OSError:
            return 1, ""


_SELF_GATE_RE = re.compile(
    r"^(agate/scripts/.*\.(sh|py)|agate/[^/]+\.md|agate/.+/.*\.md"
    r"|agate/rules/[^/]+\.ya?ml|SELF-GATE\.md|README\.md|AGENTS\.md)$"
)
_SKIP_RE = re.compile(r"^self-gate-skip:\s*\S+", re.MULTILINE)
_REVIEW_RE = re.compile(r"^self-gate-review:\s*(\S+)", re.MULTILINE)


def _review_path_exists(path: str, root: str) -> bool:
    """self-gate-review: 的路径是否**真实存在**（磁盘 或 index）。

    为何要查（RM-AG0081 复犯机械化，2026-09-29）：本 hook 原先只检查 trailer **字面存在**，
    不查路径是否真的存在 ⇒ 可写一个不存在的报告路径而放行。该缺陷**连续两次**实际发生
    （PR #379 与 TAG0045 提交都引用了当时并不存在的评审报告），后果是**虚假留痕**——
    声称"已过独立评审"却无证据可查。

    查 index 而非仅查 HEAD 是必需的：本仓的正常形态是**评审报告与代码同处一个 commit**，
    提交时报告只在磁盘/index 上，不在 HEAD 里；只查 HEAD 会对正常工作流全面误报。
    """
    candidate = path if os.path.isabs(path) else os.path.join(root, path)
    if os.path.exists(candidate):
        return True
    # 在 index 中？（已 git add 但尚未 commit）
    rc, _out = run_git(["ls-files", "--error-unmatch", "--", path], cwd=root)
    return rc == 0


def _check_review_path(commit_msg: str, root: str) -> None:
    """对每个 self-gate-review: 路径做存在性校验；不存在则告警（**不拦截**）。"""
    for m in _REVIEW_RE.finditer(commit_msg):
        path = m.group(1)
        if _review_path_exists(path, root):
            continue
        sys.stderr.write(
            "GATE SELF-GATE: commit message 的 self-gate-review: 指向的路径**不存在**：\n"
            f"  {path}\n"
            "  这会造成**虚假留痕**（声称已过独立评审，却无证据可查）。\n"
            "  请先落盘评审报告再提交，或改用 self-gate-skip: <理由>。\n"
            "  （提示型检查：不拦截本次 commit，但请在推送前修正。见 RM-AG0081。）\n"
        )



def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: commit-msg-self-gate.py COMMIT_MSG_FILE\n")
        sys.exit(1)
    commit_msg_file = sys.argv[1]

    # 检查暂存区是否含 self-gate 触发文件
    # （git diff --cached --name-only 2>/dev/null | tr -d '\r' 逐行等价）
    rc, staged = run_git(["diff", "--cached", "--name-only"])
    triggered = False
    if rc == 0:
        for line in staged.splitlines():
            if _SELF_GATE_RE.match(line.rstrip("\r")):
                triggered = True
                break

    if not triggered:
        return

    # 检查 commit message 是否含 self-gate-skip: 理由 或 self-gate-review: 路径
    commit_msg = ""
    try:
        with open(commit_msg_file, encoding="utf-8", errors="replace") as f:
            commit_msg = f.read()
    except OSError:
        commit_msg = ""
    if _SKIP_RE.search(commit_msg):
        return
    if _REVIEW_RE.search(commit_msg):
        # trailer 字面在场 ≠ 报告真的存在：追加存在性校验（虚假留痕防线，RM-AG0081）
        _check_review_path(commit_msg, os.getcwd())
        return

    sys.stderr.write(
        "GATE SELF-GATE: 暂存区含 self-gate 触发文件（agate/scripts/*.sh / agate/scripts/*.py / agate/**/*.md / agate/rules/*.yaml / SELF-GATE.md / README.md / AGENTS.md），\n")
    sys.stderr.write("  但 commit message 未含 self-gate-review: 路径。\n")
    sys.stderr.write("  请先派发 protocol-alignment-review subagent，审查报告路径写入 commit message：\n")
    sys.stderr.write("    self-gate-review: docs/reviews/agate-alignment-review-{date}.md\n")
    sys.stderr.write("  或如果本次改动确实不需要 self-gate（如纯 typo），在 commit message 加：\n")
    sys.stderr.write("    self-gate-skip: 理由\n")


if __name__ == "__main__":
    main()
