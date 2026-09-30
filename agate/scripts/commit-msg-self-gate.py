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
# 取**整行值**而非首个 token：`(\S+)` 会在逗号前停下（实测 `r/a.md, r/b.md` 只捕获 `r/a.md,`），
# 而清单式写法是本仓既有形态（存量 8 条）。故匹配到行尾，再由 `_review_trailer_tokens` 切分。
_REVIEW_RE = re.compile(r"^self-gate-review:[ \t]*(.+)$", re.MULTILINE)


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


def _review_trailer_tokens(raw: str) -> list:
    r"""把 trailer 值切成 token 列表。

    **为何是全部 token 而不是首个**（2026-09-29 实测修正）：存量扫描发现 **8 条**历史写法是
    **被评审文件清单**而非报告路径，例如：
        `self-gate-review: README.md, README.zh-CN.md, CHANGELOG.md, agate/UPGRADING.md`
    旧实现用 `^self-gate-review:\s*(\S+)` 只取**首个 token** 并当路径判存在 ⇒ 对这类写法**误报**
    （"README.md 不存在"——荒谬）。改为取全部 token（按逗号/空白切分）后**任一存在即通过**：
    既兼容清单式写法（其条目通常都存在），又仍能抓住"一个都找不着"的真幽灵。
    """
    out = []
    for part in raw.replace("，", ",").split(","):
        for tok in part.split():
            # 只剥离**尾部的括号注记**（如 `agate/scripts/README.md（触发面 agate/scripts/*）`），
            # 不动 token 内部与首部——初版用 `.strip("（(")` 会误伤（实测丢掉一个 token）。
            cleaned = re.sub(r"[（(].*$", "", tok).strip().rstrip("：:")
            if cleaned:
                out.append(cleaned)
    return out


def _is_report_reference(token: str) -> bool:
    """该 token 是否**意在指向评审报告**（而非"被评审文件清单"里的一项）。

    **为何需要这个区分**（2026-09-29 独立评审 F4 实证）：为兼容本仓既有的**清单式**写法
    （如 `self-gate-review: README.md, CHANGELOG.md, ...`，存量 44 条），初版采用
    「**任一 token 存在即通过**」——但实测该规则**重新打开了原攻击**：
        `self-gate-review: README.md, <从未写过的幽灵报告>.md`  ⇒ **静默放行**
    （README.md 存在即可），幽灵留痕又可行了。

    正确做法不是"任一存在"，而是**先判这个 token 是不是报告指向**：
    实测**存量 44 条清单式 trailer 中，含 `reviews/` 的为 0 条** ——
    即「清单式」与「报告指向」在真实数据里是**两种互不重叠的用法**。
    ⇒ 只有**看起来像报告路径**的 token 才参与存在性判定；纯清单项（源码/文档路径）不参与。
    """
    tok = token.strip()
    if not tok:
        return False
    # 报告指向的形态：含 reviews/ 目录，或显式 .md 且位于 agate-workspace 下
    if "reviews/" in tok or "reviews\\" in tok:
        return True
    return tok.startswith("agate-workspace/") and tok.endswith(".md")


def _check_review_path(commit_msg: str, root: str) -> None:
    """对每个 self-gate-review: 做存在性校验；**全部 token 皆不存在**则告警（不拦截）。

    **时机**：本函数在 **commit-msg** 阶段运行——此时 message 已存在、且报告若与代码同处一个
    commit 则**已在 index**。这补上了 `test_selfgate_trailer_integrity.py`（后置守卫）的
    **pre-commit 盲窗**：那道守卫取 `origin/main..HEAD`，而 pre-commit 时该范围为空 ⇒
    只在**提交之后**生效（本缺陷已复犯 5 次）。两道防线**共用同一存在性判据**，只是时机不同。
    """
    for m in _REVIEW_RE.finditer(commit_msg):
        tokens = _review_trailer_tokens(m.group(1))
        # 只对**报告指向**的 token 判存在；纯清单项（源码/文档路径）不参与
        # ——修 F4：若对全部 token 用"任一存在即通过"，则 `README.md, 幽灵报告.md` 会放行。
        report_refs = [tok for tok in tokens if _is_report_reference(tok)]
        if not report_refs:
            continue
        missing = [tok for tok in report_refs if not _review_path_exists(tok, root)]
        if not missing:
            continue
        sys.stderr.write(
            "GATE SELF-GATE: commit message 的 self-gate-review: 指向的报告**不存在**：\n"
        )
        for tok in missing:
            sys.stderr.write(f"  {tok}\n")
        sys.stderr.write(
            "  这会造成**虚假留痕**（声称已过独立评审，却无证据可查）。\n"
            "  常见成因：报告写好了但**忘了 `git add`**（本仓评审报告应与代码同处一个 commit）。\n"
            "  请 `git add <报告>` 后重试；若本次确实无需 SELF-GATE，改用 self-gate-skip: <理由>。\n"
            "  （提示型检查：不拦截本次 commit，但请在推送前修正。见 RM-AG0081 / RM-AG0094。）\n"
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
