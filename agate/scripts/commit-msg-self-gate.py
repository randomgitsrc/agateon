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
_REVIEW_RE = re.compile(r"^self-gate-review:\s*\S+", re.MULTILINE)


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
