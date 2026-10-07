# agate/tests/unit/test_tag0050_cross_batch.py
# TAG0050 跨批通用验收红灯测试。
#
# 映射：BDD-73..BDD-77（P1-requirements.md §4；设计 §8、§10、§3.3）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest


@pytest.mark.windows_smoke
def test_bdd_73_each_batch_registers_snapshot(agate_root):
    """BDD-73：每批独立 PR/gate/评审并登记快照。"""
    levels = agate_root / "rules" / "task-data" / "LEVELS.yaml"
    assert levels.is_file(), "BDD-73：新增/收紧要求的批须登记新一级契约快照（LEVELS.yaml）"
    assert "level-1.yaml" in levels.read_text(encoding="utf-8"), (
        "BDD-73：LEVELS.yaml 须登记 level-1.yaml"
    )


def test_bdd_74_legacy_diff_allowlist_twelve(agate_root):
    """BDD-74：legacy 退出码与 ERROR 集合不变，差异仅限设计 §8 十二项。"""
    allow = agate_root.parent / "docs" / "design-notes" / "r6-allowlist.yaml"
    assert allow.is_file(), "BDD-74：须交付机器可读的 r6-allowlist.yaml"
    text = allow.read_text(encoding="utf-8")
    for n in range(1, 13):
        assert f"D{n:02d}" in text, f"BDD-74：allowlist 须含 D{n:02d}（设计 §8 第 {n} 项）"


def test_bdd_75_pytest_consistency_count(agate_root, agate_scripts, python_exe, run_cli):
    """BDD-75：每批 pytest 全绿 + consistency 0 ERROR + count-tests 一致（下界 749）。"""
    assert (agate_root / "rules" / "task-data" / "LEVELS.yaml").is_file(), (
        "BDD-75：快照冻结 CHECK 须落地（本批一致性口径的组成部分）"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-protocol-consistency.py"))
    assert r.returncode == 0, f"BDD-75：consistency 须 0 ERROR，实际 rc={r.returncode}"
    c = run_cli("bash", str(agate_root / "tests" / "scripts" / "count-tests.sh"))
    assert c.returncode == 0, f"BDD-75：count-tests 须可跑，实际 rc={c.returncode}"


def test_bdd_76_baseline_reset_in_changelog(agate_root):
    """BDD-76：义务基线一次性重设写入 CHANGELOG。"""
    changelog = agate_root.parent / "CHANGELOG.md"
    assert changelog.is_file(), "BDD-76：仓库根须有 CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    assert "baseline.reset" in text or "义务基线" in text, (
        "BDD-76：基线重设须写入 CHANGELOG（避免被误读为质量倒退）"
    )


def test_bdd_77_new_scripts_do_not_break_existing_tests(agate_scripts):
    """BDD-77：新增 agate/scripts 文件不触发既有测试转红。"""
    for name in ("agate-task-init.py", "agate-state-set.py", "agate_schema.py"):
        assert (agate_scripts / name).is_file(), f"BDD-77：{name} 须存在且不触发登记面门禁"
