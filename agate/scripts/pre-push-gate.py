#!/usr/bin/env python3
"""pre-push-gate.py — pre-push hook 主程序（TAG0010 批次 3b）

迁移自 pre-push-gate.sh（28 行）：协议文件（agate/*.md）大改动自动提示 alignment-review。
由 install-hook 以软链方式安装到 .git/hooks/pre-push；git 以仓库根为 cwd 执行（同
pre-commit-gate），stdin 收 local_ref/local_sha/remote_ref/remote_sha。exit 0 = 不阻断 push；
仅提示。

sh 版将保留为薄壳（批次 3d），本 py 承载 pre-push 检查逻辑。
`AGATE_ALIGNMENT_REVIEW_THRESHOLD` 环境变量保留（默认 20，同 sh `${VAR:-20}` 语义；
非数字值回退默认 20——本 hook 是提示型永不阻断）。

CLI 契约：无参数；stdin 读推送行；提示写 stdout；exit 0（永不阻断）。

Python 3.8+（无 match / str.removeprefix）；所有文本读写显式 encoding="utf-8"。
"""

import os
import subprocess
import sys

try:
    from agate_common import git_hooks_dir, run_git
except (ImportError, SystemExit):
    git_hooks_dir = None
    # 同 commit-msg-self-gate.py：公共库依赖缺失时降级本地 subprocess 实现，保持永不阻断。
    def run_git(args, cwd=None):
        try:
            proc = subprocess.run(
                ["git", *args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=cwd,
            )
            return proc.returncode, proc.stdout
        except OSError:
            return 1, ""


_ZERO_SHA = "0" * 40


def _count_changed(remote_sha, local_sha):
    """git diff <remote>..<local> -- 'agate/*.md' 的改动行数。

    复刻 `git diff ... | grep -cE '^[+-]' || true`（+ tr -d 语义不需要：git 输出本身
    不来自 diff 的 --cached，无 CRLF 差异场景）。统计首字符为 + 或 - 的行（含
    `--- a/...` / `+++ b/...` 头行，与 grep 一致）；git 失败 → 0（sh `|| true` 语义）。
    """
    rc, diff = run_git(["diff", f"{remote_sha}..{local_sha}", "--", "agate/*.md"])
    if rc != 0:
        return 0
    count = 0
    for line in diff.splitlines():
        if line[:1] in ("+", "-"):
            count += 1
    return count


def _run_project_local_hook(repo_root, *args):
    """**项目本地 hook 扩展点**（pre-push 版，与 pre-commit 版同口径）：`<git-common-dir>/hooks/pre-push-local`
    存在且**可执行** ⇒ 先跑它（参数原样透传，stdin 未消费 ⇒ 它可自行读），**非 0 即中止 push**。

    与 pre-commit 版同一条分层原则：**协议不假设项目分支/流程**（有的项目允许直推 `main`）——
    「禁止直推 main」这类策略写在**项目自己的** `pre-push-local`；协议只给它机会跑。
    本 hook 自身的检查仍是**提示型永不阻断**（两者互不影响）。
    解析 hook 目录复用**单源** `agate_common.git_hooks_dir`（ADR-014）；不可用/不存在 ⇒ 跳过。
    """
    if git_hooks_dir is None:
        return 0
    try:
        hooks_dir = git_hooks_dir(repo_root)
    except Exception:
        return 0
    path = os.path.join(hooks_dir or "", "pre-push-local")
    if not (hooks_dir and os.path.isfile(path) and os.access(path, os.X_OK)):
        return 0
    try:
        return subprocess.run([path, *args], cwd=repo_root).returncode
    except OSError:
        return 0


def main():
    # 0. 项目本地 hook 扩展点（中立）：项目自己的 pre-push-local 存在则可执行先跑，非 0 即中止。
    rc, out = run_git(["rev-parse", "--show-toplevel"])
    _repo_root = out.strip() if rc == 0 and out.strip() else os.getcwd()
    if _run_project_local_hook(_repo_root, *sys.argv[1:]) != 0:
        sys.stderr.write(
            "GATE LOCAL: 项目本地 pre-push-local 未通过 ⇒ 本次 push 中止\n"
            "  （该策略由项目自定义；见 <git-common-dir>/hooks/pre-push-local）\n"
        )
        sys.exit(1)

    try:
        threshold = int(os.environ.get("AGATE_ALIGNMENT_REVIEW_THRESHOLD", "20"))
    except ValueError:
        # sh ${VAR:-20} 仅对空值兜底；非数字时 sh 的 -gt 会硬失败。本 hook 提示型
        # 永不阻断，回退默认 20 保持 push 不中断。
        threshold = 20

    # stdin 每行: local_ref local_sha remote_ref remote_sha（read -r 语义）
    for line in sys.stdin:
        fields = line.split()
        if len(fields) < 2:
            continue
        local_ref = fields[0]
        local_sha = fields[1]
        remote_sha = fields[3] if len(fields) > 3 else ""
        # remote_ref（fields[2]）为 pre-push stdin 格式占位，未使用（sh SC2034 同款）
        if not local_sha:
            continue
        if remote_sha == _ZERO_SHA:
            print("ℹ️  新分支首次推送，跳过 agate/*.md 改动量检测（无远端基线可比较）")
            continue
        changed = _count_changed(remote_sha, local_sha)
        if changed > threshold:
            print(f"⚠️  本次 push（{local_ref}）对 agate/*.md 的改动达 {changed} 行（阈值 {threshold}）")
            print("    建议先派发一次 protocol-alignment-review，确认改动未破坏协议文件间的语义一致性。")
            print("    忽略本提示继续 push：git push --no-verify")


if __name__ == "__main__":
    main()
