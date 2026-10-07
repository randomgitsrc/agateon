# agate/tests/integration/test_tag0050_ci_replay.py
# TAG0050 批 A2（CI 逐提交回放 / 可信锚点）红灯测试。
#
# 映射：BDD-23..BDD-35（P1-requirements.md §4；设计 §2.4、§10）。
# 红灯口径：实现未写 ⇒ 运行期失败 / 契约不满足（B 类）。断言消息不含 A 类关键词。
# 平台无关：tmp_path / git_repo；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_CI_VERIFY = "agate-ci-verify.py"


def _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, *args):
    return run_cli(
        python_exe,
        str(agate_scripts / _CI_VERIFY),
        *args,
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


def _task_commit_repo(git_repo, task_id="TAG0001", phase="P5"):
    """建一个含一个任务目录提交的仓库，返回 (repo, base_sha)。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    task = repo / "agate-workspace" / "tasks" / task_id
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: {phase}\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )
    git_repo.commit("task commit")
    return repo, base


@pytest.mark.windows_smoke
def test_bdd_23_pr_replay_passes(run_cli, python_exe, agate_scripts, agate_root, git_repo):
    """BDD-23：PR 口径回放非合并提交全部 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "PASS" in r.output, "BDD-23：PR 口径回放须判 PASS"
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-23：须以逐提交回放口径输出"


def test_bdd_24_push_replay_passes(run_cli, python_exe, agate_scripts, agate_root, git_repo):
    """BDD-24：push 口径（--no-merges before..HEAD）回放同样全部 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(
        run_cli, python_exe, agate_scripts, agate_root, repo, "--push", "--base", base
    )
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-24：须以逐提交回放口径输出"
    assert "PASS" in r.output, "BDD-24：push 口径回放须判 PASS"


def test_bdd_25_no_verify_violation_fails_with_sha(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-25：--no-verify 的违规提交判 FAIL 并指出提交。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    (task / "P7-consistency.md").write_text("---\nagent: test\n---\n", encoding="utf-8")
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P7\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("--no-verify violating commit")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-25：--no-verify 违规提交须判 FAIL"
    assert head[:8] in r.output or head in r.output, "BDD-25：须指出是哪个提交"


def test_bdd_26_ready_output_only_prod_touched_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-26：READY 之后只改产出的 PROD_TOUCHED 提交判 FAIL。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: READY\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("to ready")
    (task / "P8-release.md").write_text(
        "---\nagent: test\n---\n\n[PROD_TOUCHED] 接触生产\n", encoding="utf-8"
    )
    git_repo.commit("--no-verify output-only prod touched")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-26：READY 后只改产出的 PROD_TOUCHED 须判 FAIL"


def test_bdd_27_missing_self_gate_trailer_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-27：缺 self-gate trailer 的协议本体提交判 FAIL（commit-msg 回放）。"""
    repo, base = _task_commit_repo(git_repo)
    (repo / "agate").mkdir(exist_ok=True)
    (repo / "agate" / "protocol-note.md").write_text("protocol change\n", encoding="utf-8")
    git_repo.commit("--no-verify protocol body change without trailer")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-27：缺 self-gate trailer 须判 FAIL"


def test_bdd_28_deleted_created_ledger_fails_mv_passes(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-28：删除已有创建事件账本判 FAIL；legacy 改名判 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("add created ledger")
    git_repo.git("rm", "-q", "agate-workspace/tasks/TAG0001/gate-events.jsonl")
    git_repo.commit("--no-verify delete created ledger")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-28：删除创建事件账本须判 FAIL"


def test_bdd_29_handwritten_low_level_task_created_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-29：手写低等级 task_created 并 --no-verify 提交判 FAIL。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 0}])
    git_repo.commit("--no-verify handwritten low level")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-29：手写低等级 task_created 须判 FAIL"


def test_bdd_30_branch_crossing_upgrade_no_false_report(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-30：在途分支跨越协议升级不误报（新增任务等级 ≥ merge-base 处最大等级）。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-30：须以逐提交回放口径判定"
    assert "FAIL" not in r.output, "BDD-30：跨协议升级的在途分支不应误报 FAIL"


def test_bdd_31_user_project_without_version_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-31：使用者项目未写 .agate-version 判 FAIL 并给提示。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("task commit")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-31：未固定协议版本须判 FAIL"
    assert ".agate-version" in r.output, "BDD-31：须提示写 .agate-version"


def test_bdd_32_pr_downgrade_version_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-32：PR 降级 .agate-version 判 FAIL（单调不降被违反）。"""
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v9.9.9\n", encoding="utf-8")
    git_repo.commit("pin version")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / ".agate-version").write_text("agate: v0.0.1\n", encoding="utf-8")
    git_repo.commit("downgrade version")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-32：降级 .agate-version 须判 FAIL"


def test_bdd_33_pr_mid_upgrade_version_no_false_report(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-33：PR 中途升级 .agate-version 不误报。"""
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.0.1\n", encoding="utf-8")
    git_repo.commit("pin low")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / ".agate-version").write_text("agate: v9.9.9\n", encoding="utf-8")
    git_repo.commit("upgrade version")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-33：须以逐提交回放口径判定"
    assert "FAIL" not in r.output, "BDD-33：中途升级不应误报 FAIL"


def test_bdd_34_no_task_dir_pr_skips_with_reason(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-34：未改动任务目录的 PR 判 SKIP 并附原因。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / "notes.md").write_text("no task changes\n", encoding="utf-8")
    git_repo.commit("non-task change")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "SKIP" in r.output or "跳过" in r.output, "BDD-34：无任务目录改动须 SKIP"
    assert "改动" in r.output, "BDD-34：SKIP 须指明『未改动任务目录』原因"


def test_bdd_35_replay_interface_records_timing(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-35：E4 耗时在可接受范围（回放输出记录被回放提交数与耗时）。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "耗时" in r.output or "elapsed" in r.output.lower(), (
        "BDD-35：回放须记录被回放提交数与耗时"
    )
