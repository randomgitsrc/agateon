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
    """本任务（TAG0051）待校验提交 = 下列两者的**并集**（去重，区间在前）。

    1) `origin/main..HEAD`（或 `main..HEAD`）：特性分支上该区间 = 本任务提交，与既有守卫取法一致。
    2) 提交信息前缀回退 `--grep=wf(TAG0051-`：TAG0051 本任务提交的信息统一带 `wf(TAG0051-`
       前缀（如 `wf(TAG0051-P4)`）。

    **为何取并集（两种失效场景，均实测复现过；单独任一取法都不够）**：
    - **区间为空**：合并到 main 后 HEAD 与 `origin/main` 同一 ⇒ `git rev-list --count
      origin/main..HEAD` = 0 ⇒ 单靠 (1) 取不到任何提交（旧版「退回单个 HEAD」同样取不到本任务
      协议提交）⇒ `assert prot` 恒失败。
    - **区间非空但全是非触发面提交**：如 hotfix 分支只改 `agate/tests/**` + `agate-workspace/**`
      ⇒ 单靠 (1) 经触发面过滤后 `prot` 仍为 `[]` ⇒ 同样失败。

    并集是**超集** ⇒ 校验面只增不减；触发面过滤仍只挑出真正触及 `agate/` 协议面的提交。
    **不得**用裸 `TAG0051`（旧废弃分支的提交形如 `TAG0051 P0：…`，**不含** `wf(TAG0051-`）。
    """
    commits = []
    seen = set()

    def _add(items):
        for c in items:
            if c and c not in seen:
                seen.add(c)
                commits.append(c)

    for base in ("origin/main", "main"):
        # `check=False`：探测本意就是容忍缺失（`-q` 正是为此）；`run_git` 默认 check=True 会对
        # base 不存在 raise，而非返回 rc（CI 的 PR checkout 无本地 `main` ⇒ 本行必须容忍）。
        if H.run_git(repo, "rev-parse", "--verify", "-q", base, check=False).returncode != 0:
            continue
        _add(_text(repo, "log", "--no-merges", "--format=%H", f"{base}..HEAD").split())
    _add(_text(repo, "log", "--no-merges", "--format=%H", "--grep=wf(TAG0051-").split())
    return commits


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
            # `check=False`：本行本意即「探测该路径是否存在」（`-e` 正是为此）——路径不存在时须
            # 返回非零 rc 走 `missing.append`，而非让 `run_git` 默认 check=True 抛 RuntimeError。
            if H.run_git(repo, "cat-file", "-e", f"{sha}:{probe}", check=False).returncode != 0:
                missing.append(probe_token)
    return missing


def _bdd_22_violations(repo):
    """BDD-22 核心判据（单一源：实现测试与 DEBT0071 回归用例共用，避免判据分叉）。

    返回 `(prot, violations)`：
      * `prot` = 本任务改动 `agate/` 触发面的协议提交（空 = 本任务尚无协议提交）；
      * `violations` = 违规清单（协议提交缺 `self-gate-review:` 留痕，或留痕指向的路径
        在该提交中不存在）。
    """
    prot = _protocol_commits(repo)
    violations = []
    for sha in prot:
        msg = _text(repo, "log", "-1", "--format=%B", sha)
        if "self-gate-review:" not in msg:
            violations.append(f"{sha[:8]}：缺 `self-gate-review:` 留痕")
            continue
        missing = _missing_trailer_paths(repo, sha)
        if missing:
            violations.append(f"{sha[:8]}：`self-gate-review:` 指向不存在的路径 {missing}")
    return prot, violations


def test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review():
    """BDD-22：本任务的协议本体/脚本提交须带可兑现的 `self-gate-review:` 留痕。"""
    prot, violations = _bdd_22_violations(H.REPO_ROOT)
    assert prot, (
        "BDD-22：本分支尚无改动 `agate/` 协议本体/脚本的提交——本任务 M1-M16 必然改协议本体/脚本"
        "（P4 起这些提交须带 `self-gate-review:` 可兑现留痕）"
    )
    assert not violations, (
        "BDD-22：协议提交的自评审留痕缺失或不可兑现（虚假留痕）：\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# DEBT0071 回归锁（判据②）
#
# 不变量（两条，缺一不可）：
#   (a) 「区间为空」等价场景（main 上 / 已合并到 main，`HEAD == origin/main`）下
#       `_range_commits()` 仍**返回非空**（经 `wf(TAG0051-` 前缀回退）⇒ 判据**不恒红**；
#   (b) **判别力仍在**：区间为空时，触及触发面但**无可兑现 `self-gate-review:` 留痕**
#       的提交**仍被判 FAIL**。
#
# 合成仓库经 `git_repo`（tmp_path）构建；协议提交**有父提交**——`diff-tree`（无 `--root`）
# 对根提交不输出改动文件，故先落一个基线提交，避免误判触发面为空。
# 平台无关：`tmp_path` 派生 + helpers_tag_repo；不裸 python3；不写字面系统临时目录。
# ---------------------------------------------------------------------------

_BASE_MSG = "init baseline"  # 基线提交：不含 `wf(TAG0051-` 前缀、不改触发面


def _seed_baseline(git_repo):
    """落一个基线提交（使后续协议提交有父提交，`diff-tree` 能列出改动文件）。"""
    (git_repo.path / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit(_BASE_MSG)


def _commit_protocol(git_repo, rel, message):
    """写一个触及 self-gate 触发面的文件并提交（`add -A`），返回该提交 sha。"""
    path = git_repo.path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# probe\n", encoding="utf-8")
    git_repo.commit(message)
    return _text(git_repo.path, "rev-parse", "HEAD").strip()


def _mark_merged(git_repo):
    """把 `refs/remotes/origin/main` 指到 HEAD —— 复现「合并到 main 后」区间为空的真实形态。"""
    git_repo.git("update-ref", "refs/remotes/origin/main", "HEAD")


def _assert_empty_range(repo):
    """自证本用例确处「区间为空」场景（否则不构成对 DEBT0071 的复现）。"""
    assert _text(repo, "rev-list", "--count", "origin/main..HEAD").strip() == "0"


def test_debt0071_range_empty_still_selects_task_commits(git_repo):
    """(a) 区间为空时仍有非空校验对象：经 `wf(TAG0051-` 前缀回退取回本任务提交。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(git_repo, "agate/scripts/probe_p4.py", "wf(TAG0051-P4): 改协议脚本")
    _mark_merged(git_repo)
    _assert_empty_range(repo)

    commits = _range_commits(repo)
    assert sha in commits, (
        f"DEBT0071：区间为空时须经前缀回退取回本任务提交（判据不得恒红），实际 {commits}"
    )


def test_debt0071_empty_range_judgement_not_red(git_repo):
    """(a) 区间为空 + 可兑现留痕 ⇒ 核心判据**不判 FAIL**（无违规）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    _commit_protocol(
        git_repo,
        "agate/scripts/probe_ok.py",
        "wf(TAG0051-P4): 改协议脚本\n\nself-gate-review: agate/scripts/probe_ok.py",
    )
    _mark_merged(git_repo)
    _assert_empty_range(repo)

    prot, violations = _bdd_22_violations(repo)
    assert prot, "DEBT0071：区间为空时仍须取到协议提交（否则即判据恒红的旧缺陷回归）"
    assert not violations, f"DEBT0071：带可兑现留痕的协议提交不应违规，实际 {violations}"


def test_debt0071_empty_range_still_catches_unbacked_review(git_repo):
    """(b) 判别力仍在：区间为空时，留痕指向**不存在路径**的协议提交仍被判 FAIL。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(
        git_repo,
        "agate/scripts/probe_bad_path.py",
        "wf(TAG0051-P4): 改协议脚本\n\nself-gate-review: agate/scripts/does_not_exist.py",
    )
    _mark_merged(git_repo)
    _assert_empty_range(repo)

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0071：判别力用例须先取到该协议提交"
    assert violations, "DEBT0071：指向不存在路径的留痕须仍被抓（不得因并集取法而丢失判别力）"
    assert "does_not_exist.py" in " ".join(violations), (
        f"DEBT0071：违规须点名不可兑现的路径，实际 {violations}"
    )


def test_debt0071_empty_range_still_catches_missing_trailer(git_repo):
    """(b) 判别力仍在：区间为空时，**完全缺** `self-gate-review:` 留痕的协议提交仍被判 FAIL。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(git_repo, "agate/scripts/probe_no_trailer.py", "wf(TAG0051-P4): 改协议脚本")
    _mark_merged(git_repo)
    _assert_empty_range(repo)

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0071：判别力用例须先取到该协议提交"
    assert violations, "DEBT0071：缺留痕的协议提交须仍被判违规（判别力不得丢失）"
