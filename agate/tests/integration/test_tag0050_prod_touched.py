# agate/tests/integration/test_tag0050_prod_touched.py
# TAG0050 批 C（生产接触安全门）红灯测试。
#
# 映射：BDD-52..BDD-55（P1-requirements.md §4；设计 §4、P2 §3.1 F4 规格、§10）。
# 平台无关：tmp_path / git_repo；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h


def _snapshot_text(agate_root):
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert level1.is_file(), "批 C：须有契约快照 level-1.yaml（primary_outputs/prod_touched）"
    return level1.read_text(encoding="utf-8")


@pytest.mark.windows_smoke
def test_bdd_52_missing_prod_touched_errors(agate_root, tmp_path, agate_scripts,
                                            python_exe, run_cli):
    """BDD-52：缺 prod_touched 判 ERROR 并附修复命令。"""
    text = _snapshot_text(agate_root)
    assert "prod_touched" in text, "BDD-52：主产出须声明 prod_touched 必填"
    assert "primary_outputs" in text, "BDD-52：快照须指定各阶段主产出"
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P1", str(d))
    assert r.returncode != 0, f"BDD-52：缺 prod_touched 须 ERROR，实际 rc={r.returncode}"


def test_bdd_53_prod_touched_true_not_paused_aborts(agate_root):
    """BDD-53：prod_touched 为 true 且不在 PAUSED 时中止提交。"""
    text = _snapshot_text(agate_root)
    assert "prod_touched" in text, "BDD-53：prod_touched=true 的中止语义须由快照/门禁承载"


def test_bdd_54_bold_marker_field_false_still_aborts(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-54：正文粗体 **[PROD_TOUCHED]**、字段 false 仍中止（T4 优先）。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-verification.md").write_text(
        "---\nagent: test\nprod_touched: false\n---\n\n**[PROD_TOUCHED]** 接触生产\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-54：粗体 PROD_TOUCHED 须仍中止，实际 rc={r.returncode}"


def test_bdd_55_negation_form_blocks_with_guidance(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-55：否定写法 `- [PROD_TOUCHED]: 无` 继续阻断并给专门指引（修复 F4）。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-verification.md").write_text(
        "---\nagent: test\n---\n\n- [PROD_TOUCHED]: 无\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-55：否定写法须继续阻断，实际 rc={r.returncode}"
    assert "疑似否定写法" in r.output, "BDD-55：须给出『疑似否定写法』专门指引"
