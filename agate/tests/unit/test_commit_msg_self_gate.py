# tests/unit/test_commit_msg_self_gate.py — commit-msg-self-gate 正则消息文本
# （unit/commit-msg-self-gate.bats 4 用例迁移，TAG0011 批次 12）
# 被测：agate/scripts/commit-msg-self-gate.sh（bash 薄壳 exec commit-msg-self-gate.py）。
# 行为：staged 含 self-gate 触发文件（agate/scripts/*.sh|*.py / agate/*.md / SELF-GATE.md）时，
#   commit message 缺 self-gate-review:/self-gate-skip: → WARNING（stderr，exit 0 不阻断）。
# 追加（2026-09-29，RM-AG0081）：trailer **在场但路径不存在** → 亦告警（仍 exit 0）——
#   防「虚假留痕」（该缺陷曾连续两次实际发生：引用了当时并不存在的评审报告）。
# 流语义（P2 BLOCKER-1）：MSG.3 空断言基于合并流 .output（bats $output = stdout + stderr）。
# git 操作走 git_repo fixture（GitRepo 类，git -C repo 等价 bats cd + git add）。

import pytest


def _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg_file, repo):
    return run_cli(
        bash,
        str(agate_scripts / "commit-msg-self-gate.sh"),
        str(commit_msg_file),
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


@pytest.mark.windows_smoke
def test_cmsg_1_sh_file_triggers_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "agate" / "scripts").mkdir(parents=True)
    (repo / "agate" / "scripts" / "test-file.sh").write_text("test\n", encoding="utf-8")
    git_repo.stage("agate/scripts/test-file.sh")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert "self-gate" in result.output


def test_cmsg_2_py_file_triggers_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "agate" / "scripts").mkdir(parents=True)
    (repo / "agate" / "scripts" / "test-file.py").write_text("test\n", encoding="utf-8")
    git_repo.stage("agate/scripts/test-file.py")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert "self-gate" in result.output


def test_cmsg_3_non_agate_py_no_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "other").mkdir(parents=True)
    (repo / "other" / "test-file.py").write_text("test\n", encoding="utf-8")
    git_repo.stage("other/test-file.py")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert result.output == ""


def test_cmsg_4_review_path_clears_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "agate" / "scripts").mkdir(parents=True)
    (repo / "agate" / "scripts" / "test-file.sh").write_text("test\n", encoding="utf-8")
    git_repo.stage("agate/scripts/test-file.sh")

    # 报告须**真实存在**（2026-09-29 起 hook 校验 trailer 路径存在性，RM-AG0081）：
    # 原用例用不存在的占位路径 `docs/reviews/test.md`，那正是被修掉的缺陷形态——契约已变，
    # 故此处建出真实文件，保持本用例"合法 trailer → 通过"的原意。
    (repo / "docs" / "reviews").mkdir(parents=True)
    (repo / "docs" / "reviews" / "test.md").write_text("review\n", encoding="utf-8")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text(
        "feat: test\nself-gate-review: docs/reviews/test.md\n", encoding="utf-8"
    )
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0


# ── self-gate 触发面扩展用例（README/AGENTS/CHANGELOG），TAG0013（追加，不改既有） ──

def test_bdd_6_readme_triggers_self_gate_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "README.md").write_text("# agate\n", encoding="utf-8")
    git_repo.stage("README.md")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert "self-gate" in result.output


def test_bdd_7_agents_triggers_self_gate_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    git_repo.stage("AGENTS.md")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert "self-gate" in result.output


def test_bdd_8_changelog_exempt_no_output(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "CHANGELOG.md").write_text("# changelog\n", encoding="utf-8")
    git_repo.stage("CHANGELOG.md")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_9_agate_md_trigger_not_regressed(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "agate").mkdir(parents=True)
    (repo / "agate" / "WORKFLOW.md").write_text("# workflow\n", encoding="utf-8")
    git_repo.stage("agate/WORKFLOW.md")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert "self-gate" in result.output


def test_bdd_10_rules_yaml_triggers_self_gate_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """agate/rules/*.yaml（数据面权威源）改动应触发 self-gate 提示——与 SELF-GATE.md
    的触发条件、protocol-alignment-review.md 触发面、CHECK 15 数据面扫描对齐。"""
    repo = git_repo.path
    (repo / "agate" / "rules").mkdir(parents=True)
    (repo / "agate" / "rules" / "phases.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    git_repo.stage("agate/rules/phases.yaml")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text("feat: test\n", encoding="utf-8")
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert "self-gate" in result.output


def test_bdd_10b_rules_yaml_review_trailer_passes(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """rules/*.yaml 触发时，commit message 含 self-gate-review: 则静默通过。"""
    repo = git_repo.path
    (repo / "agate" / "rules").mkdir(parents=True)
    (repo / "agate" / "rules" / "dispatch-tiers.yaml").write_text("tiers: {}\n", encoding="utf-8")
    git_repo.stage("agate/rules/dispatch-tiers.yaml")

    # 报告须真实存在（契约已变，理由同 test_cmsg_4）：本用例断言**完全静默**，
    # 故更要给出真实路径——否则命中的是"路径不存在"告警，而非本用例要验的"缺 trailer"告警。
    (repo / "docs" / "reviews").mkdir(parents=True)
    (repo / "docs" / "reviews" / "x.md").write_text("review\n", encoding="utf-8")

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text(
        "feat: test\nself-gate-review: docs/reviews/x.md\n", encoding="utf-8"
    )
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert result.output == ""


# ── self-gate-review: 路径**存在性**校验（RM-AG0081 复犯机械化，2026-09-29） ──
#
# 缺陷形态（同一缺陷**连续两次**发生）：hook 原先只检查 commit message 里**有没有**
# `self-gate-review: <非空白>`，**不检查那个路径是否真的存在** ⇒ 作者可以写一个不存在的
# 报告路径而 hook 放行。实测两例：PR #379 与 TAG0045 提交都引用了当时并不存在的评审报告。
# 后果不是"少个文件"，而是**虚假留痕**——声称"已过独立评审"却无任何证据可查。
#
# 判据设计：**仍然是 WARNING 不拦截**（exit 0），与 hook 既有契约一致（提示型永不断 commit）；
# 但把"路径不存在"如实报出，使该缺陷**在提交时即可见**，而非等到事后评审才发现。

def _run_csg_msg(run_cli, bash, agate_scripts, agate_root, msg_text, repo, tmp_path):
    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text(msg_text, encoding="utf-8")
    return _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)


def _stage_trigger(git_repo):
    repo = git_repo.path
    (repo / "agate" / "scripts").mkdir(parents=True)
    (repo / "agate" / "scripts" / "test-file.sh").write_text("test\n", encoding="utf-8")
    git_repo.stage("agate/scripts/test-file.sh")
    return repo


def test_sg_path_1_nonexistent_review_path_warns(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """负向：trailer 指向**不存在**的报告 → 须告警（但 exit 0，不拦截）。"""
    repo = _stage_trigger(git_repo)
    result = _run_csg_msg(
        run_cli, bash, agate_scripts, agate_root,
        "feat: x\nself-gate-review: agate-workspace/reviews/does-not-exist-xyz.md\n",
        repo, tmp_path,
    )
    assert result.returncode == 0, "提示型 hook 不得拦截 commit"
    assert "不存在" in result.output, (
        f"trailer 指向不存在的报告却无告警（虚假留痕，两次复犯的根因）：{result.output!r}"
    )
    assert "does-not-exist-xyz" in result.output, "告警未回显那个不存在的路径（读者无法定位）"


def test_sg_path_2_existing_review_path_no_path_warning(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """正向：报告**真实存在**时不得出现存在性告警（防误报使告警变噪声）。"""
    repo = _stage_trigger(git_repo)
    report = repo / "agate-workspace" / "reviews" / "real.md"
    report.parent.mkdir(parents=True)
    report.write_text("---\nstatus: approved\n---\n", encoding="utf-8")

    result = _run_csg_msg(
        run_cli, bash, agate_scripts, agate_root,
        "feat: x\nself-gate-review: agate-workspace/reviews/real.md\n",
        repo, tmp_path,
    )
    assert result.returncode == 0
    assert "不存在" not in result.output, f"报告存在却误报：{result.output!r}"


def test_sg_path_3_staged_but_uncommitted_report_counts_as_existing(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """边界：报告**已暂存**（在 index 中，尚未 commit）须视为存在。

    这是本仓真实提交形态——评审报告与代码改动同处一个 commit，提交时它只在 index/磁盘上，
    不在 HEAD 里。若只查 HEAD 就会对本仓的正常工作流全面误报。
    """
    repo = _stage_trigger(git_repo)
    report = repo / "agate-workspace" / "reviews" / "staged.md"
    report.parent.mkdir(parents=True)
    report.write_text("---\nstatus: approved\n---\n", encoding="utf-8")
    git_repo.stage("agate-workspace/reviews/staged.md")

    result = _run_csg_msg(
        run_cli, bash, agate_scripts, agate_root,
        "feat: x\nself-gate-review: agate-workspace/reviews/staged.md\n",
        repo, tmp_path,
    )
    assert result.returncode == 0
    assert "不存在" not in result.output, f"已暂存的报告被误判为不存在：{result.output!r}"


def test_sg_path_4_skip_trailer_needs_no_path_check(
    git_repo, agate_scripts, agate_root, run_cli, bash, tmp_path
):
    """`self-gate-skip:` 是理由而非路径 ⇒ 不做存在性检查，且不得再报"缺 trailer"。"""
    repo = _stage_trigger(git_repo)
    result = _run_csg_msg(
        run_cli, bash, agate_scripts, agate_root,
        "chore: x\nself-gate-skip: 纯文案修正，无需 SELF-GATE\n",
        repo, tmp_path,
    )
    assert result.returncode == 0
    assert "未含 self-gate-review" not in result.output, (
        f"已给 self-gate-skip 却仍报缺 trailer：{result.output!r}"
    )
