# agate/tests/unit/test_tag0051_self_gate.py — TAG0051 P3 红灯（SELF-GATE 留痕）
#
# 覆盖 BDD（P1-requirements.md）：22。
#   * BDD-22：本任务**每个改动 `agate/` 协议本体/脚本的提交**，commit message 须含
#     `self-gate-review:` 且其后路径**真实存在**（磁盘或 index），**或** `self-gate-skip:`
#     且理由非空（DEBT0073：与 commit-msg hook / `SELF-GATE.md` 轻量档同一口径——二者皆接受）。
#
# 现行为（改动前）：本分支（`origin/main..HEAD`）尚无改动 `agate/` 协议本体/脚本的提交
#   ——断言「至少一条协议提交存在」（本任务 M1-M16 **必然**改协议本体/脚本）⇒ 失败 = B 类红灯。
#   留痕完整性判据与既有 `test_selfgate_trailer_integrity.py` 同源（同一 hook 正则/规则），
#   本文件只补「本任务范围的协议提交必须带可兑现留痕」这一条。
#
# 平台无关：只读 git 事实 + helpers_tag_repo；不裸 python3；不写字面系统临时目录。

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import helpers_tag_repo as H

# 与 `commit-msg-self-gate.py::_SELF_GATE_RE` 同源（触发面）。
_TRIGGER_RE = re.compile(
    r"^(agate/scripts/.*\.(sh|py)|agate/[^/]+\.md|agate/.+/.*\.md"
    r"|agate/rules/[^/]+\.ya?ml|SELF-GATE\.md|README\.md|AGENTS\.md)$"
)

# 留痕正则的**唯一定义处 = hook**（DEBT0073「口径单源」）：`SELF-GATE.md` 明写
# 「权威源 = hook 实现」，故判据**导入** hook 的 `_REVIEW_RE` / `_SKIP_RE`，不再各自写字面量。
# 两份字面量即便「现在写得一样」也是分叉隐患——正是 DEBT0073 的成因：hook 用
# `^self-gate-skip:\s*\S+`（`\s` **含换行**），判据曾用只含空格/制表的写法 ⇒ 对
# 「`self-gate-skip:` 后换行再接理由」hook 接受、判据拒绝。**正则定义单源**后（`_SKIP_RE is
# hook._SKIP_RE`），该类**正则字面量**分叉结构上不可能；但**另有一层**既有逻辑差异（判据用
# 子串判在否、hook 用 `_REVIEW_RE.search`，以及 `skip` 优先与否），**不在本批**消除——见守护用例边界注。
_HOOK_FILENAME = "commit-msg-self-gate.py"
_HOOK = H.load_project_module(H.REAL_SCRIPTS, _HOOK_FILENAME, "commit_msg_self_gate_hook")
_HOOK_PATH = H.REAL_SCRIPTS / _HOOK_FILENAME
_REVIEW_RE = _HOOK._REVIEW_RE
_SKIP_RE = _HOOK._SKIP_RE


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
      * `violations` = 违规清单。

    留痕接受集（DEBT0073：**与 `commit-msg-self-gate.py` / `SELF-GATE.md` 轻量档同口径**）：
      1. `self-gate-review:` 在场 ⇒ 其后路径须在该提交中**真实存在**（既有行为，不变）；
      2. 否则 `self-gate-skip:` **理由非空**（strip 后 ≥1 字符）⇒ 正当留痕（轻量档）；
      3. 二者皆无（或 skip 理由空 / 纯空白）⇒ 违规。
    """
    prot = _protocol_commits(repo)
    violations = []
    for sha in prot:
        msg = _text(repo, "log", "-1", "--format=%B", sha)
        if "self-gate-review:" in msg:
            missing = _missing_trailer_paths(repo, sha)
            if missing:
                violations.append(f"{sha[:8]}：`self-gate-review:` 指向不存在的路径 {missing}")
            continue
        if _SKIP_RE.search(msg):
            continue
        violations.append(
            f"{sha[:8]}：缺可兑现的 `self-gate-review:` 路径或 `self-gate-skip:` 理由留痕"
        )
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


# ---------------------------------------------------------------------------
# DEBT0073 回归锁（留痕接受集单源：hook ↔ BDD-22 判据）
#
# 背景：`agate/scripts/commit-msg-self-gate.py`（hook）与 `SELF-GATE.md` 都接受
# 「`self-gate-review:` **或** `self-gate-skip:` 理由」，但 BDD-22 判据曾只认前者 ⇒
# 「轻量档 + 触发面」的改动（如发布提交 `ccb1c20f`）在 CI 上**必然红**（逃生通道不可用）。
# 修法：判据对齐约定（非反方向）——四条用例逐条锁定接受集与判别力。
# 合成仓库（`git_repo` + 合成提交）不依赖当前分支真实历史。
# ---------------------------------------------------------------------------


def test_debt0073_skip_with_reason_is_not_violation(git_repo):
    """① `self-gate-skip:` **理由非空** ⇒ 正当留痕，不违规（改前红、改后绿）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(
        git_repo,
        "agate/scripts/probe_skip_ok.py",
        "wf(TAG0051-P4): 改协议脚本（纯措辞）\n\nself-gate-skip: 纯措辞修正，无判据语义变化",
    )

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0073：判别力用例须先取到该协议提交"
    assert not violations, f"DEBT0073：带非空理由的 self-gate-skip: 应视为正当留痕，实际 {violations}"


@pytest.mark.parametrize("skip_line", ["self-gate-skip:", "self-gate-skip:   "])
def test_debt0073_skip_empty_reason_is_violation(git_repo, skip_line):
    """② `self-gate-skip:` 理由为空 / 纯空白 ⇒ 违规（判别力：防『有 key 就行』）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(
        git_repo,
        "agate/scripts/probe_skip_empty.py",
        f"wf(TAG0051-P4): 改协议脚本\n\n{skip_line}",
    )

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0073：判别力用例须先取到该协议提交"
    assert violations, f"DEBT0073：skip 理由为空（{skip_line!r}）须判违规"


def test_debt0073_review_missing_path_is_violation(git_repo):
    """③ `self-gate-review:` 指向**不存在**路径 ⇒ 违规（既有行为，不得回归）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(
        git_repo,
        "agate/scripts/probe_review_ghost.py",
        "wf(TAG0051-P4): 改协议脚本\n\nself-gate-review: agate/scripts/ghost_report.py",
    )

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0073：判别力用例须先取到该协议提交"
    assert violations, "DEBT0073：指向不存在路径的 review 留痕须仍被判违规"
    assert "ghost_report.py" in " ".join(violations), (
        f"DEBT0073：违规须点名不可兑现的路径，实际 {violations}"
    )


def test_debt0073_no_trailer_is_violation(git_repo):
    """④ 二者皆无 ⇒ 违规（既有行为，不得回归；与 DEBT0071 同名用例同口径）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(git_repo, "agate/scripts/probe_no_trailer_0073.py", "wf(TAG0051-P4): 改协议脚本")

    prot, violations = _bdd_22_violations(repo)
    assert sha in prot, "DEBT0073：判别力用例须先取到该协议提交"
    assert violations, "DEBT0073：既无 review 也无 skip 留痕的协议提交须仍被判违规"


# ---------------------------------------------------------------------------
# DEBT0073 口径单源守护（`skip` 正则定义真单源 + 5 组代表性样例对拍）
#
# 判据经 `_bdd_22_violations()` **端到端**跑（它消费 hook 导入的 `_SKIP_RE`，`is` 同一对象）；
# hook 侧经**真实子进程**跑 `commit-msg-self-gate.py`（触发面已 stage）——两侧取自不同执行路径。
# 若判据日后又写回本地字面量（如只含空格的写法），样例 ④/⑤ 立即分叉 ⇒ 本用例红。
#
# **边界（如实标注）**：本用例只证明下列 **5 组代表性样例**的 `skip` 接受集与 hook 一致，
# **不构成「接受集逐例一致」或「分叉结构上不可能」的穷尽证明**。实测另有 **3 类既有逻辑差异**
# 未消除（非本批引入，交独立债务 DEBT0075）：
#   ① `skip` + 幽灵 `review` 并存 ⇒ 判据更严（judge 拒 / hook 接受）；
#   ② `review` 留痕**非行首** ⇒ hook 更严（hook 拒 / judge 接受）；
#   ③ `review` 指向**不存在且非 `reviews/`** 的路径 ⇒ 判据更严（judge 拒 / hook 接受；
#      该路径若**真实存在**且非 `reviews/` ⇒ 双方一致接受）。
# ---------------------------------------------------------------------------

# 覆盖 ① 同行理由 / ② 冒号后空 / ③ 冒号后纯空格 / ④ 冒号后换行再接理由（本次分叉例）/ ⑤ 冒号后换行接非空行
_HOOK_AGREEMENT_SAMPLES = [
    "self-gate-skip: 同行理由",
    "self-gate-skip:",
    "self-gate-skip:   ",
    "self-gate-skip:\n\n理由在这里",
    "self-gate-skip:\n下一行是理由",
]


def _stage_trigger(git_repo):
    """在 repo 里 stage 一个**未提交**的触发面文件——使 hook 进入「已触发」分支。"""
    path = git_repo.path / "agate" / "scripts" / "staged_probe.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# staged probe\n", encoding="utf-8")
    git_repo.stage("agate/scripts/staged_probe.py")


def _hook_accepts(repo, message):
    """真实 hook（子进程）对 message 的接受集：stderr 无 `GATE SELF-GATE:` 告警行 = 接受。

    走子进程而非直接调 hook 函数——那才是「hook 的真实口径」这一 oracle 的来源。
    """
    msg_file = Path(repo) / "_commit_msg.txt"
    msg_file.write_text(message, encoding="utf-8")
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, str(_HOOK_PATH), str(msg_file)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    return "GATE SELF-GATE:" not in proc.stderr


@pytest.mark.parametrize("trailer", _HOOK_AGREEMENT_SAMPLES)
def test_debt0073_hook_and_judge_accept_sets_agree(git_repo, trailer):
    """`skip` 接受集对**下列 5 组代表性样例**与 hook 逐个相等（DEBT0073：正则定义单源的守护）。"""
    repo = git_repo.path
    _seed_baseline(git_repo)
    sha = _commit_protocol(
        git_repo,
        "agate/scripts/probe_agree.py",
        f"wf(TAG0051-P4): 改协议脚本\n\n{trailer}\n",
    )
    message = _text(repo, "log", "-1", "--format=%B", sha)
    _stage_trigger(git_repo)

    judge_accepts = not _bdd_22_violations(repo)[1]
    hook_accepts = _hook_accepts(repo, message)
    assert judge_accepts == hook_accepts, (
        f"DEBT0073：hook 与判据接受集**分叉**！样例 {trailer!r}\n"
        f"  hook_accepts={hook_accepts} / judge_accepts={judge_accepts}\n  message={message!r}"
    )
