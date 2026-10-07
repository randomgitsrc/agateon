# agate/tests/integration/test_tag0050_state_set.py
# TAG0050 批 A3（state-set 与状态事实）红灯测试。
#
# 映射：BDD-36..BDD-39（P1-requirements.md §4；设计 §2.7、§10）。
# 平台无关：tmp_path / git_repo；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_STATE_SET = "agate-state-set.py"


@pytest.mark.windows_smoke
def test_bdd_36_state_set_rejects_illegal_transition(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-36：agate-state-set phase 以 HEAD 为基准拒绝非法转换。"""
    assert (agate_scripts / _STATE_SET).is_file(), "BDD-36：须新增 agate-state-set.py"
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / _STATE_SET), str(d), "phase", "P8")
    assert r.returncode != 0, f"BDD-36：非法转换须被拒绝，实际 rc={r.returncode}"


def test_bdd_37_retreat_writes_retries(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-37：回退时同时写入 retries。"""
    assert (agate_scripts / _STATE_SET).is_file(), "BDD-37：须新增 agate-state-set.py"
    d = h.init_task_via_conftest(tmp_path)
    run_cli(python_exe, str(agate_scripts / _STATE_SET), str(d), "phase", "P3")
    state = (d / ".state.yaml").read_text(encoding="utf-8")
    assert "retries" in state and "P3" in state, "BDD-37：回退须写入 retries[...]"


def test_bdd_38_entering_ready_paused_writes_event(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-38：进入 READY/PAUSED 写 state_transition；agate-next 不再写。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("task p5")
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: PAUSED\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/.state.yaml")
    h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    ledger = task / "gate-events.jsonl"
    assert ledger.is_file(), "BDD-38：进入 PAUSED 须写入 state_transition 事件"
    assert "state_transition" in ledger.read_text(encoding="utf-8"), (
        "BDD-38：账本须含 state_transition（进入 PAUSED 随本次提交入库）"
    )
    # agate-next 不再追加事件
    next_r = run_cli(python_exe, str(agate_scripts / "agate-next.py"), str(task))
    assert "state_transition" not in next_r.output, "BDD-38：agate-next 通过时不应再追加事件"


def test_bdd_39_non_legacy_status_written_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-39：非 legacy 任务写 status 判 ERROR；读取方现算。"""
    d = h.init_task_via_conftest(tmp_path)
    state = d / ".state.yaml"
    state.write_text(
        state.read_text(encoding="utf-8").rstrip("\n") + "\nstatus: active\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-state-yaml.py"), str(state))
    assert r.returncode != 0, f"BDD-39：非 legacy 写 status 须 ERROR，实际 rc={r.returncode}"
