# agate/tests/unit/test_tag0050_declarations.py
# TAG0050 批 E（成对声明）红灯测试。
#
# 映射：BDD-61..BDD-66（P1-requirements.md §4；设计 §6、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_MD_SET = "agate-md-field-set.py"


@pytest.mark.windows_smoke
def test_bdd_61_f2_blocker_count_not_covering_prose(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-61：F2 转红（P7 汇总值盖不住 BLOCKER）。"""
    d = h.init_task_via_conftest(tmp_path)
    p7 = d / "P7-consistency.md"
    p7.write_text(
        "---\nagent: test\nblocker_count: 0\n---\n\n- [BLOCKER] 未解决\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-61：计数为系统字段，不被汇总值盖住，实际 rc={r.returncode}"


def test_bdd_62_cross_file_declaration_aggregation(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-62：P2-review 与 P4 分文件中的声明都被聚合。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P2-review.md").write_text(
        "---\nagent: reviewer\nneed_confirm: []\n---\nreview\n", encoding="utf-8"
    )
    (d / "P4-implementation-batch1.md").write_text(
        "---\nagent: impl\ndesign_gaps:\n  - {id: DG1, text: x}\n---\nbody\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-62：跨文件聚合须覆盖 P4 分文件声明，实际 rc={r.returncode}"


def test_bdd_63_parallel_ids_no_collision(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-63：并行写入不撞号（ID = <相对路径去 .md>:<前缀><n>）。"""
    d = h.init_task_via_conftest(tmp_path)
    f = d / "P4-implementation-batch1.md"
    f.write_text("---\nagent: impl\n---\nbody\n", encoding="utf-8")
    r = run_cli(
        python_exe,
        str(agate_scripts / _MD_SET),
        "append",
        "design_gaps",
        "text=x",
        env={"FILE": str(f)},
    )
    assert r.returncode == 0, f"BDD-63：append 自动编号须可用，实际 rc={r.returncode}"
    assert "P4-implementation-batch1" in f.read_text(encoding="utf-8"), (
        "BDD-63：ID 须带相对路径前缀，每文件独立编号"
    )


def test_bdd_64_set_mismatch_or_dangling_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-64：集合不相等或悬空 id 判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-64：悬空 id/集合不等须 ERROR，实际 rc={r.returncode}"


def test_bdd_65_resolved_missing_evidence_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-65：resolved 缺证据判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-65：resolved 缺 resolution/evidence 须 ERROR，实际 rc={r.returncode}"


def test_bdd_66_followup_debt_backref_required(agate_scripts):
    """BDD-66：followup:DEBT<n> 中 DEBT 不存在或无回指判 ERROR。"""
    src = (agate_scripts / "agate-debt-check.py").read_text(encoding="utf-8")
    assert "source_ref" in src, (
        "BDD-66：tech-debt 须新增 source_ref 字段并校验双向回指（<task_id>:<DG id>）"
    )
