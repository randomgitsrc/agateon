# tests/unit/test_selfgate_trailer_integrity.py — self-gate-review: 的**留痕完整性**
#
# 缺陷形态（本会话**复犯 3 次**，PR #379 / #380 / #381）：commit message 写了
# `self-gate-review: <path>`，但**那个文件在提交里并不存在** ⇒ 声称「已过独立评审」却无证据可查。
# 后果不是「少个文件」而是**虚假留痕**——审计链上出现一个无法兑现的断言。
#
# **为何现有三道防线都没拦住**（本会话实测）：
#   ① 开发版 hook `agate/scripts/commit-msg-self-gate.py` 有校验（`_review_path_exists`），
#      但**只 WARNING 不拦截**（其契约是提示型永不断 commit）；
#   ② 稳定版 hook `~/.agate/v0.76.0/agate/scripts/commit-msg-self-gate.py` **根本没有该校验**
#      （实测 `grep -c` = 0）——版本更新滞后是**结构性**的，故「靠 hook」必然有一段时间的窗口；
#   ③ 既有单测（`test_commit_msg_self_gate.py`）验证的是**机制的样例**（合成仓），
#      **从不去核真实提交里那些 trailer 指向的文件是否存在**。
#
# ⇒ 本文件补的正是 ③：**对真实仓库的真实提交做校验，且走 CI（不依赖任何 hook 版本）**。
#
# 判据核心：**「在那一提交里存在」，不是「现在存在」**——这是本条最容易被写错的地方
# （文件可能事后被删/改名，而提交当时的断言仍应成立；反之现在存在的文件也不能替当时的缺失背书）。

import importlib.util
import subprocess
from pathlib import Path

import pytest

import helpers_tag_repo as H

# **与 hook 同源**（2026-09-29 修正判据漂移）：
# 初版此处用 `(\S+)`（只取首个 token），而 `commit-msg-self-gate.py` 已改为取**整行值**再切 token
# ⇒ 两处对**清单式** trailer（本仓既有 8 条写法）会给出**相反结论**（首项不存在而后项存在时：
# 守卫误报、hook 不报）。本仓 DEBT0046 的教训正是「判据必须只有一份」，故改为**导入 hook 的实现**，
# 不再各写一份正则。
_HOOK_SPEC = importlib.util.spec_from_file_location(
    "csg_unified", str(Path(__file__).resolve().parents[2] / "scripts" / "commit-msg-self-gate.py")
)
_HOOK = importlib.util.module_from_spec(_HOOK_SPEC)
_HOOK_SPEC.loader.exec_module(_HOOK)
_TRAILER_RE = _HOOK._REVIEW_RE


def _run(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=H.git_env(),
        timeout=120,
    )


def trailer_paths(message: str) -> list:
    """提取 commit message 里全部 `self-gate-review:` 的 **token**（与 hook **同一实现**）。

    返回**逐 token**（而非整行）——这正是 hook 的语义：清单式写法应逐项判存在，
    **任一存在即通过**（见 `missing_trailer_paths`）。
    """
    out = []
    for raw in _TRAILER_RE.findall(message):
        out.extend(_HOOK._review_trailer_tokens(raw))
    return out


def missing_trailer_paths(repo, commit: str) -> list:
    """返回该提交里**不存在**的 trailer 路径（空 = 全部可兑现）。

    存在性判据 = `git cat-file -e <commit>:<path>`，即**在该提交的树里**存在。
    """
    msg = _run(repo, "log", "-1", "--format=%B", commit).stdout
    missing = []
    for path in trailer_paths(msg):
        # **与 hook 同一通过规则**：只判「报告指向」的 token（`_is_report_reference`），
        # 且**每一个**都必须存在。初版只共用了正则、没共用规则 ⇒ 两者对同一输入结论相反
        # （实测：`README.md, ghost.md` 下 hook 通过、守卫失败）——独立评审 F3 指出。
        if not _HOOK._is_report_reference(path):
            continue
        probe = path.rstrip("/")
        rc = _run(repo, "cat-file", "-e", f"{commit}:{probe}").returncode
        if rc != 0:
            missing.append(path)
    return missing


def commits_to_check(repo) -> list:
    """待校验的提交：优先「相对基线新增的提交」，为空则退回 HEAD。

    为何这样取：CI 上 pull_request 事件 checkout 的是 **merge ref**（HEAD 是合成合并提交），
    故不能只看 HEAD；而 push 到 main 时范围为空，此时校验 HEAD 自身仍是有意义的
    （保证本检查**永不真空**——与 SG.9 的教训一致：判据不能在目标缺失时静默通过）。
    """
    for base in ("origin/main", "main"):
        if _run(repo, "rev-parse", "--verify", "-q", base).returncode != 0:
            continue
        out = _run(repo, "log", "--format=%H", f"{base}..HEAD").stdout
        commits = [c for c in out.split() if c]
        if commits:
            return commits
    head = _run(repo, "rev-parse", "HEAD").stdout.strip()
    return [head] if head else []


# ---------------------------------------------------------------------------
# 1. 真实仓库：所有 trailer 必须可兑现
# ---------------------------------------------------------------------------


@pytest.mark.windows_smoke
def test_trailer_1_real_repo_trailers_point_to_existing_files():
    """真实仓库中待校验提交的 `self-gate-review:` 路径须**在各自提交里存在**。

    这是本组的主判据。它在 CI 上会校验收到的 PR 的全部提交；
    在本机 main 上校验 HEAD 自身（仍有意义：HEAD 的断言必须可兑现）。
    """
    repo = H.REPO_ROOT
    commits = commits_to_check(repo)
    assert commits, "无法确定任何待校验提交（git 异常）——本判据不应在目标缺失时静默通过"

    violations = []
    for c in commits:
        for path in missing_trailer_paths(repo, c):
            violations.append(f"{c[:8]} 声称 {path}（该提交中不存在）")
    assert not violations, (
        "以下 commit 的 self-gate-review: 指向**在该提交里不存在**的文件——"
        "这是虚假留痕（声称已过独立评审却无证据可查；本会话已复犯 3 次）：\n  "
        + "\n  ".join(violations)
        + "\n  修法：先把评审报告落盘并与代码同处一个提交，或改用 self-gate-skip: <理由>。"
    )


# ---------------------------------------------------------------------------
# 2. 判据自身非真空：合成仓上正/负向都验
# ---------------------------------------------------------------------------


_SEED_N = [0]


def _commit_with(git_repo, msg, files=None):
    """在合成仓提交一条消息；files = {相对路径: 内容}，随后返回提交 sha。

    ⚠️ **必须保证有内容可提交，且提交失败要响亮报错**——初版没做这件事，
    于是空仓上 `git commit` 静默失败 ⇒ HEAD 不存在 ⇒ trailer 解析为空 ⇒
    负向用例**"通过"成了真空**（本文件自身差点犯下它要防的那类错误）。
    故：每次写一个内容唯一的 seed 文件（保证有 diff），并断言提交真的成立。
    """
    payload = dict(files or {})
    _SEED_N[0] += 1
    payload.setdefault(f"seed-{_SEED_N[0]}.md", f"seed {_SEED_N[0]}\n")
    for rel, content in payload.items():
        p = git_repo.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    git_repo.commit(msg)
    r = _run(git_repo.path, "rev-parse", "HEAD")
    assert r.returncode == 0 and r.stdout.strip(), (
        f"合成仓提交未成立（测试前置失败，非判据结论）：stderr={r.stderr!r}"
    )
    return r.stdout.strip()


def test_trailer_2_phantom_trailer_is_reported(git_repo):
    """负向：trailer 指向不存在的文件 ⇒ 必须报出（否则判据真空）。"""
    sha = _commit_with(
        git_repo,
        "feat: x\n\nself-gate-review: agate-workspace/reviews/does-not-exist-zzz.md\n",
    )
    missing = missing_trailer_paths(git_repo.path, sha)
    assert missing == ["agate-workspace/reviews/does-not-exist-zzz.md"], (
        f"幽灵 trailer 未被报出（判据真空）：{missing}"
    )


def test_trailer_3_real_trailer_is_accepted(git_repo):
    """正向：报告真实存在于该提交 ⇒ 不报（防误报使判据变噪声）。"""
    sha = _commit_with(
        git_repo,
        "feat: x\n\nself-gate-review: agate-workspace/reviews/real.md\n",
        {"agate-workspace/reviews/real.md": "---\nstatus: approved\n---\n"},
    )
    assert missing_trailer_paths(git_repo.path, sha) == []


def test_trailer_4_existence_is_judged_at_that_commit_not_now(git_repo):
    """**核心语义**：判据是「在该提交里存在」，不是「现在存在」。

    构造：提交 A 带 trailer 且**不含**报告 → 之后提交 B 补上报告。
    核 A 时**必须**判为缺失（A 当时的断言不可兑现），
    即便此刻工作区/HEAD 里该文件已存在。
    """
    report = "agate-workspace/reviews/late.md"
    sha_a = _commit_with(git_repo, f"feat: a\n\nself-gate-review: {report}\n")
    assert missing_trailer_paths(git_repo.path, sha_a) == [report], (
        "提交 A 当时并无该报告，却因『现在存在』被判通过——判据用错了时间点"
    )
    sha_b = _commit_with(
        git_repo, "docs: add report", {report: "---\nstatus: approved\n---\n"}
    )
    assert missing_trailer_paths(git_repo.path, sha_b) == [], "补上报告后该提交应通过"


def test_trailer_5_skip_trailer_needs_no_path(git_repo):
    """`self-gate-skip:` 是理由而非路径 ⇒ 不产生缺失项。"""
    sha = _commit_with(git_repo, "chore: x\n\nself-gate-skip: 纯文案，无需 SELF-GATE\n")
    assert missing_trailer_paths(git_repo.path, sha) == []


def test_trailer_6_no_trailer_at_all_is_not_a_violation(git_repo):
    """无任何 trailer ⇒ 本判据不管（那条规则由 commit-msg hook 承担，非本文件职责）。"""
    sha = _commit_with(git_repo, "chore: 无 trailer 的普通提交\n")
    assert missing_trailer_paths(git_repo.path, sha) == []


def test_trailer_7_multiple_trailers_are_all_checked(git_repo):
    """一条消息里多个 trailer ⇒ **逐个**校验（漏查其一即留缺口）。"""
    sha = _commit_with(
        git_repo,
        "feat: x\n\n"
        "self-gate-review: agate-workspace/reviews/ok.md\n"
        "self-gate-review: agate-workspace/reviews/also-missing.md\n",
        {"agate-workspace/reviews/ok.md": "ok\n"},
    )
    assert missing_trailer_paths(git_repo.path, sha) == [
        "agate-workspace/reviews/also-missing.md"
    ]


# ---------------------------------------------------------------------------
# 3. 历史锚：本会话真实复犯过的 3 次提交——**用途是「非真空 + 可解析」，不是「抓住了」**
# ---------------------------------------------------------------------------
#
# 这 3 个提交是 PR #379 / #380 / #381 的 squash 合并提交（本缺陷的 3 次实例）。
#
# ⚠️ **诚实界定其作用（2026-09-29 由独立评审指出我初版框架过度声称）**：
# 实测这 3 个报告都是**在被引用的那个提交里首次加入**的（即当时已用 `--amend` 修好）
# ⇒ **本守卫在那 3 例上都会通过**。所以它们**不能**证明「守卫抓得住幽灵 trailer」。
# 它们的真实用途有两条（都仍有用）：
#   ① **非真空**：证明解析器在**真实数据**上确实读出了 trailer（否则本文件整体真空）；
#   ② **可兑现性回归**：证明这些历史断言的留痕**至今可核**（日后删改报告文件不影响——
#      判据是「在该提交里存在」）。
# 「守卫抓得住」的证据在别处：**本文件加入时它当场抓住了 c05055c 自己的幽灵 trailer**
# （第 4 次复犯），以及合成仓负向用例 test_trailer_2。
#
# 局限（据实说明）：硬编码 SHA 非 hermetic——浅克隆 / fork / rebase 会使其失效，
# 故下方对「提交不存在」**跳过而非断言失败**（避免把环境差异误报为留痕问题）。
_PHANTOM_INCIDENTS = ("59598d4", "7dee815", "61a2b4f")


def test_trailer_8_historical_anchors_parse_and_stay_verifiable():
    """历史 3 次实例的提交：须**确实解析出** trailer（非真空），且其留痕至今可兑现。"""
    repo = H.REPO_ROOT
    parsed_total = 0
    violations = []
    absent = []
    for c in _PHANTOM_INCIDENTS:
        if _run(repo, "rev-parse", "--verify", "-q", c).returncode != 0:
            # 非 hermetic：浅克隆 / fork / rebase 下这些 SHA 可能不存在。
            # 环境差异**不应**报成留痕违规；但若**全部**缺失则说明本锚已失效，下方会断言。
            absent.append(c)
            continue
        msg = _run(repo, "log", "-1", "--format=%B", c).stdout
        parsed = trailer_paths(msg)
        parsed_total += len(parsed)
        for path in missing_trailer_paths(repo, c):
            violations.append(f"{c} 声称 {path}（该提交中不存在）")

    if len(absent) == len(_PHANTOM_INCIDENTS):
        pytest.skip(
            "3 个历史锚提交全部不可达（浅克隆 / fork / rebase？）——"
            "非真空守护无法执行，跳过而非误报（本锚非 hermetic，见文件头注释）"
        )
    assert parsed_total > 0, (
        "在可达的历史锚提交上**一个 trailer 都没解析出**——"
        "说明解析器或范围取法失效，本文件的全部断言都会真空通过"
    )
    assert not violations, "历史锚提交的留痕现已不可兑现：\n  " + "\n  ".join(violations)
