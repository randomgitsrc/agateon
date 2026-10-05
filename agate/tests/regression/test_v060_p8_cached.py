# tests/regression/test_v060_p8_cached.py — 回归测试：P8 gate 用 --cached 不是 HEAD~1
# （v060-p8-cached.bats 3 用例迁移，TAG0011 批次 11）
# 触发：7f4648d "fix: P8 gate HEAD~1 chicken-and-egg bug"
# 教训：v0.6 hardening R4 修了 P4/P7，但漏了 P8 → 本次评审发现并修复。
# 迁移：与批次 8f test_check_gate.py G8 系列同形态——git_repo + copytree task +
#   git_repo.stage（等价 bats `git -C "$repo" add ...`），run_cli(..., cwd=repo)
#   等价 bats `cd "$repo" && ...`。流语义：GATE P8 / GATE P8 WARNING 写 stderr →
#   断言用合并流 result.output（P2 §3.2，BLOCKER-1）。

import shutil

import pytest


def _init_p8_repo(git_repo, td, files=None):
    """bats `git_init + echo init > README.md && git_commit + cp -r task + git add ...` 等价。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    shutil.copytree(td, repo / "task")
    for name, content in (files or {}).items():
        (repo / name).write_text(content, encoding="utf-8")
        git_repo.stage(name)
    return repo


def _run_gate_p8(agate_scripts, python_exe, run_cli, repo):
    return run_cli(
        python_exe,
        str(agate_scripts / "check-gate.py"),
        "P8",
        "task",
        cwd=str(repo),
    )


_P8_RELEASE = "bump_type: minor\ndebt_check: none\ndelivery: package-release\n"
_P8_UNRELEASED = "## [Unreleased]\n"


@pytest.mark.windows_smoke
def test_r5_1_p8_cached_version_changelog_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P8-release.md").write_text(_P8_RELEASE, encoding="utf-8")
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate_p8(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 2
    assert "脚本化检查通过" in result.output


def test_r5_2_p8_cached_no_version_warning_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P8-release.md").write_text(_P8_RELEASE, encoding="utf-8")
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"some.md": "doc\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate_p8(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 2
    assert "WARNING" in result.output
    assert "version" in result.output


def test_r5_3_p8_cached_version_no_changelog_warning_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P8-release.md").write_text(_P8_RELEASE, encoding="utf-8")
    repo = _init_p8_repo(git_repo, td, files={"package.json": "v0.1.0\n"})

    result = _run_gate_p8(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 2
    assert "CHANGELOG" in result.output
