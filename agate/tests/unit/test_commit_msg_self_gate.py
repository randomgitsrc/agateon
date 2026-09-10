# tests/unit/test_commit_msg_self_gate.py — commit-msg-self-gate 正则消息文本
# （unit/commit-msg-self-gate.bats 4 用例迁移，TAG0011 批次 12）
# 被测：agate/scripts/commit-msg-self-gate.sh（bash 薄壳 exec commit-msg-self-gate.py）。
# 行为：staged 含 self-gate 触发文件（agate/scripts/*.sh|*.py / agate/*.md / SELF-GATE.md）时，
#   commit message 缺 self-gate-review:/self-gate-skip: → WARNING（stderr，exit 0 不阻断）。
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

    commit_msg = tmp_path / "commit-msg"
    commit_msg.write_text(
        "feat: test\nself-gate-review: docs/reviews/x.md\n", encoding="utf-8"
    )
    result = _run_csg(run_cli, bash, agate_scripts, agate_root, commit_msg, repo)
    assert result.returncode == 0
    assert result.output == ""
