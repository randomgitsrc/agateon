# tests/integration/test_commit_msg_self_gate_integration.py — commit-msg hook 真环境
# （integration/commit-msg-self-gate.bats 6 用例迁移，TAG0011 批次 12）
# git hook 真环境：把 commit-msg-self-gate.sh 复制到 .git/hooks/commit-msg（等价 bats cp + chmod +x），
# git commit 时 hook 被 git 自动调用（subprocess 调 bash 薄壳，BDD-11）。
# 关键：hook 是复制非软链，AGATE_ROOT 靠环境变量传递（bats load.bash export 等价）——
#   复制模式下 wrapper 的 readlink -f 定位到 .git/hooks 目录，须 env AGATE_ROOT 指向真实 agate 根。
# 流语义（P2 BLOCKER-1）：hook WARNING 写 stderr，git 转发出现在合并流——断言用 result.output。

import shlex
import shutil

import pytest


def _setup_hook(git_repo, agate_scripts):
    """等价 bats setup：init commit + 复制 hook 到 .git/hooks/commit-msg + 建 repo/agate 目录。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.stage("README.md")
    git_repo.commit("init")

    hook = repo / ".git" / "hooks" / "commit-msg"
    shutil.copy2(str(agate_scripts / "commit-msg-self-gate.sh"), str(hook))
    hook.chmod(0o755)

    (repo / "agate" / "scripts").mkdir(parents=True)
    (repo / "agate" / "assets").mkdir(parents=True)
    shutil.copy2(
        str(agate_scripts / "commit-msg-self-gate.sh"),
        str(repo / "agate" / "scripts" / "commit-msg-self-gate.sh"),
    )
    return repo


def _commit(run_cli, bash, repo, agate_root, *args):
    """bash 包装 git（对照 test_bdd_19：Windows 直接 spawn git 时 hook 被静默跳过）。
    env 传 AGATE_ROOT（hook 复制模式依赖），经 bash 继承给 git/hook。"""
    msg = " ".join(shlex.quote(a) for a in args)
    return run_cli(
        bash,
        "-c",
        f"cd {shlex.quote(str(repo))} && git commit {msg}",
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


@pytest.mark.windows_smoke
def test_csg_1_readme_triggers_warning(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "README.md").write_text("change\n", encoding="utf-8")
    git_repo.stage("README.md")

    result = _commit(run_cli, bash, repo, agate_root, "-m", "update readme")
    assert result.returncode == 0
    assert "self-gate-review" in result.output


def test_csg_2_trigger_no_review_warning(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "SELF-GATE.md").write_text("# change\n", encoding="utf-8")
    git_repo.stage("SELF-GATE.md")

    result = _commit(run_cli, bash, repo, agate_root, "-m", "update self-gate")
    assert result.returncode == 0
    assert "self-gate-review" in result.output


def test_csg_3_trigger_with_review_no_warning(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "SELF-GATE.md").write_text("# change\n", encoding="utf-8")
    git_repo.stage("SELF-GATE.md")
    # 报告须真实存在（2026-09-29 起 hook 校验 trailer 路径存在性，RM-AG0081）：
    # 原用例引用不存在的占位报告，那正是被修掉的形态；建立真实文件以保持本用例原意。
    report = repo / "docs" / "reviews" / "agate-alignment-review-2026-07-02.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("---\nstatus: approved\n---\n", encoding="utf-8")

    result = _commit(
        run_cli,
        bash,
        repo,
        agate_root,
        "-m",
        "update self-gate",
        "-m",
        "self-gate-review: docs/reviews/agate-alignment-review-2026-07-02.md",
    )
    assert result.returncode == 0
    assert "self-gate-review" not in result.output


def test_csg_4_trigger_with_skip_no_warning(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "SELF-GATE.md").write_text("# change\n", encoding="utf-8")
    git_repo.stage("SELF-GATE.md")

    result = _commit(run_cli, bash, repo, agate_root, "-m", "fix typo", "-m", "self-gate-skip: typo")
    assert result.returncode == 0
    assert "self-gate-review" not in result.output


def test_csg_5_scripts_sh_triggers(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "agate" / "scripts" / "pre-commit-gate.sh").write_text("# change\n", encoding="utf-8")
    git_repo.stage("agate/scripts/pre-commit-gate.sh")

    result = _commit(run_cli, bash, repo, agate_root, "-m", "update gate script")
    assert result.returncode == 0
    assert "self-gate-review" in result.output


def test_csg_6_agate_md_triggers(git_repo, agate_scripts, agate_root, run_cli, bash):
    repo = _setup_hook(git_repo, agate_scripts)
    (repo / "agate" / "WORKFLOW.md").write_text("# change\n", encoding="utf-8")
    git_repo.stage("agate/WORKFLOW.md")

    result = _commit(run_cli, bash, repo, agate_root, "-m", "update workflow")
    assert result.returncode == 0
    assert "self-gate-review" in result.output
