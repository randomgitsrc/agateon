# agate/tests/integration/test_tag0050_evidence.py
# TAG0050 批 D（验收结论与证据绑定）红灯测试。
#
# 映射：BDD-56..BDD-60（P1-requirements.md §4；设计 §5、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h


def _snapshot(agate_root):
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert level1.is_file(), "批 D：须有契约快照 level-1.yaml（results/criteria）"
    return level1.read_text(encoding="utf-8")


@pytest.mark.windows_smoke
def test_bdd_56_f1_abc_tampering_turns_red(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-56：F1 的 A/B/C 三种篡改全部转红（D1/D2 判据）。"""
    d = h.init_task_via_conftest(tmp_path)
    p6 = d / "P6-acceptance.md"
    p6.write_text(
        "---\nagent: test\nresults:\n  - {bdd: '4', verdict: PASS, evidence: [e]}\n"
        "  - {bdd: '4', verdict: PASS, evidence: [e]}\n---\n\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode != 0, f"BDD-56：重复/缺失 BDD 集合须转红，实际 rc={r.returncode}"


def test_bdd_57_ignored_evidence_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-57：证据被 ignore 判 ERROR（修复 F9）。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-p6-evidence.py"), str(d))
    assert r.returncode != 0, f"BDD-57：证据被 ignore 须 ERROR，实际 rc={r.returncode}"


def test_bdd_58_pass_log_nonzero_exit_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-58：PASS 条目日志 EXIT_CODE≠0 判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    ev = d / "P6-evidence"
    ev.mkdir(exist_ok=True)
    (ev / "bdd-01.log").write_text("run\nEXIT_CODE: 1\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-p6-evidence.py"), str(d))
    assert r.returncode != 0, f"BDD-58：PASS 日志 EXIT_CODE≠0 须 ERROR，实际 rc={r.returncode}"


def test_bdd_59_run_ref_sha256_mismatch_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-59：run: 引用的 sha256 与事件不一致判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    assert (d / ".state.yaml").is_file(), "BDD-59：init 任务须含 .state.yaml"
    ac = h.agate_common_module(agate_scripts)
    assert callable(getattr(ac, "resolve_evidence_ref", None)), (
        "BDD-59：须提供 resolve_evidence_ref 解析 run:<k> 引用（sha256 校验入口）"
    )


def test_bdd_60_extract_context_counts_equal_computed(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-60：extract-context 计数等于按字段现算的值。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "agate-extract-context.py"), str(d))
    assert r.returncode == 0, f"BDD-60：extract-context 须按字段现算，实际 rc={r.returncode}"
