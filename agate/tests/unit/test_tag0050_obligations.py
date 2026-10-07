# agate/tests/unit/test_tag0050_obligations.py
# TAG0050 批 A4（义务执行方式机械核验，修复 F13）红灯测试。
#
# 映射：BDD-40..BDD-44（P1-requirements.md §4；设计 §2.9、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import re

import pytest

_OBLIGATIONS = "agate/rules/obligations.yaml"


def _read_obligations(agate_root):
    return (agate_root / "rules" / "obligations.yaml").read_text(encoding="utf-8")


@pytest.mark.windows_smoke
def test_bdd_40_f13_four_m_items_error(agate_root, agate_scripts, python_exe, run_cli):
    """BDD-40：check-obligations 对 F13 的 4 条 M 报 ERROR。"""
    text = _read_obligations(agate_root)
    for obl_id in ("OBL-P2-12", "OBL-X-10", "OBL-X-17", "OBL-X-19"):
        assert obl_id in text, f"BDD-40：{obl_id} 应登记"
    assert "enforced_at" in text, "BDD-40：M 义务须带 enforced_at（ast 可达性核验）"
    r = run_cli(python_exe, str(agate_scripts / "check-obligations.py"))
    assert r.returncode != 0, f"BDD-40：F13 的 4 条 M 须报 ERROR，实际 rc={r.returncode}"


def test_bdd_41_missing_test_or_node_errors(agate_root):
    """BDD-41：M 项缺 test 或 test 节点不存在判 ERROR。"""
    text = _read_obligations(agate_root)
    assert re.search(r"^\s*test:\s*\S+::\S+", text, re.M), (
        "BDD-41：M 义务须带 test: <pytest 节点> 字段"
    )


def test_bdd_42_negative_control_mutation(agate_root):
    """BDD-42：负向控制——删掉判据分支使 test 转红（OBL-P8-02 及抽样 M 项）。"""
    text = _read_obligations(agate_root)
    m = re.search(r"id:\s*OBL-P8-02\b(.*?)(?=\n\s*-\s*id:|\Z)", text, re.S)
    assert m is not None, "BDD-42：须登记 OBL-P8-02"
    block = m.group(1)
    assert "test:" in block, "BDD-42：OBL-P8-02 须带可删改打红的 test 凭证"
    assert "enforced_at" in block, "BDD-42：OBL-P8-02 须带 enforced_at 落点"


def test_bdd_43_r_without_review_output_errors(agate_root):
    """BDD-43：缺 review_output 的 R 判 ERROR；找不到合格评审产出的 R 改标为 C。"""
    text = _read_obligations(agate_root)
    assert "review_output" in text, (
        "BDD-43：R 义务须带 review_output（check-gate 校验其存在且 agent ≠ main）"
    )


def test_bdd_44_baseline_reset_supported(agate_root):
    """BDD-44：改标并重设基线后转绿；之后 M 占比下降仍 FAIL。"""
    text = _read_obligations(agate_root)
    assert "baseline" in text, "BDD-44：须有基线声明"
    assert "reset" in text, "BDD-44：须支持 baseline.reset 一次性重设（写 CHANGELOG）"
