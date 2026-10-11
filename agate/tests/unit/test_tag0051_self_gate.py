# agate/tests/unit/test_tag0051_self_gate.py — TAG0051 P3 红灯（SELF-GATE 留痕）
#
# 覆盖 BDD（P1-requirements.md）：22。
#   * BDD-22：本任务**每个改动 `agate/` 协议本体/脚本的提交**，commit message 须含
#     `self-gate-review:` 且其后路径**真实存在**（磁盘或 index）。
#
# 现行为（改动前）：本分支（`origin/main..HEAD`）尚无改动 `agate/` 协议本体/脚本的提交
#   ——断言「至少一条协议提交存在」（本任务 M1-M16 **必然**改协议本体/脚本）⇒ 失败 = B 类红灯。
#   留痕完整性判据与既有 `test_selfgate_trailer_integrity.py` 同源（同一 hook 正则/规则），
#   本文件只补「本任务范围的协议提交必须带可兑现留痕」这一条。
#
# 平台无关：只读 git 事实 + helpers_tag_repo；不裸 python3；不写字面系统临时目录。

import re

import helpers_tag_repo as H

# 与 `commit-msg-self-gate.py::_SELF_GATE_RE` 同源（触发面）。
_TRIGGER_RE = re.compile(
    r"^(agate/scripts/.*\.(sh|py)|agate/[^/]+\.md|agate/.+/.*\.md"
    r"|agate/rules/[^/]+\.ya?ml|SELF-GATE\.md|README\.md|AGENTS\.md)$"
)
_REVIEW_RE = re.compile(r"^self-gate-review:[ \t]*(.+)$", re.MULTILINE)


def _text(repo, *args):
    return H.run_git(repo, *args).stdout.decode("utf-8", "replace")


def _range_commits(repo):
    """待校验提交：`origin/main..HEAD`；范围为空则退回 HEAD（同既有守卫取法）。"""
    for base in ("origin/main", "main"):
        if H.run_git(repo, "rev-parse", "--verify", "-q", base).returncode != 0:
            continue
        out = _text(repo, "log", "--no-merges", "--format=%H", f"{base}..HEAD")
        commits = [c for c in out.split() if c]
        if commits:
            return commits
    head = _text(repo, "rev-parse", "HEAD").strip()
    return [head] if head else []


def _changed_files(repo, sha):
    out = _text(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", sha)
    return [p for p in out.splitlines() if p]


def _protocol_commits(repo):
    """改动 `agate/` 协议本体/脚本（self-gate 触发面）的非合并提交。"""
    out = []
    for sha in _range_commits(repo):
        if any(_TRIGGER_RE.match(p) for p in _changed_files(repo, sha)):
            out.append(sha)
    return out


def _missing_trailer_paths(repo, sha):
    """该提交中 `self-gate-review:` 指向**不存在**的路径（空 = 留痕可兑现）。"""
    msg = _text(repo, "log", "-1", "--format=%B", sha)
    missing = []
    for raw in _REVIEW_RE.findall(msg):
        for token in re.split(r"[,\s]+", raw.strip()):
            probe_token = token.strip().rstrip(",。);）")
            if not probe_token:
                continue
            probe = probe_token.rstrip("/")
            if H.run_git(repo, "cat-file", "-e", f"{sha}:{probe}").returncode != 0:
                missing.append(probe_token)
    return missing


def test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review():
    """BDD-22：本任务的协议本体/脚本提交须带可兑现的 `self-gate-review:` 留痕。"""
    repo = H.REPO_ROOT
    prot = _protocol_commits(repo)
    assert prot, (
        "BDD-22：本分支尚无改动 `agate/` 协议本体/脚本的提交——本任务 M1-M16 必然改协议本体/脚本"
        "（P4 起这些提交须带 `self-gate-review:` 可兑现留痕）"
    )
    violations = []
    for sha in prot:
        msg = _text(repo, "log", "-1", "--format=%B", sha)
        if "self-gate-review:" not in msg:
            violations.append(f"{sha[:8]}：缺 `self-gate-review:` 留痕")
            continue
        missing = _missing_trailer_paths(repo, sha)
        if missing:
            violations.append(f"{sha[:8]}：`self-gate-review:` 指向不存在的路径 {missing}")
    assert not violations, (
        "BDD-22：协议提交的自评审留痕缺失或不可兑现（虚假留痕）：\n  " + "\n  ".join(violations)
    )
