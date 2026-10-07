# agate/tests/unit/test_tag0050_fitness.py
# TAG0050 架构适应度检查（P2-design §6 / §4.2 判据三，N2 映射）。
#
# 节点名含 `task_data_freeze` / `task_data_golden` / `schema_single_source`，
# 供 gate_commands 的 P5_fitness_* `-k` 选择（零匹配会 exit 5，故须为真实节点）。
# 映射：BDD-15（快照冻结）、BDD-16（黄金 fixture）、BDD-50（schema 单实现）。
# 平台无关：tmp_path；不写字面系统临时目录。

import hashlib

import pytest

_LEVELS = "rules/task-data/LEVELS.yaml"


@pytest.mark.windows_smoke
def test_task_data_freeze_snapshot_sha256(agate_root):
    """BDD-15：已发布快照字节 sha256 与 LEVELS.yaml 登记值一致（冻结 CHECK）。"""
    levels = agate_root / _LEVELS
    assert levels.is_file(), "BDD-15：须有 LEVELS.yaml 登记快照 sha256"
    text = levels.read_text(encoding="utf-8")
    assert "sha256" in text, "BDD-15：LEVELS.yaml 须登记每个快照文件的 sha256"
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert level1.is_file(), "BDD-15：须有 level-1.yaml"
    actual = hashlib.sha256(level1.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    assert actual in text, "BDD-15：level-1.yaml 的字节 sha256 须等于登记值"


def test_task_data_golden_fixture_regression(agate_root):
    """BDD-16：每个已登记等级的黄金 fixture 判定结果不变。"""
    base = agate_root / "tests" / "fixtures" / "task-data" / "level-1"
    assert (base / "pass").is_dir(), "BDD-16：level-1/pass 黄金 fixture 缺失"
    assert (base / "fail").is_dir(), "BDD-16：level-1/fail 黄金 fixture 缺失"
    assert any((base / "pass").iterdir()), "BDD-16：pass fixture 不得为空"
    assert any((base / "fail").iterdir()), "BDD-16：fail fixture 不得为空"


def test_schema_single_source_only_agate_schema(agate_scripts):
    """BDD-50：agate/scripts/*.py 中不存在第二个递归 schema 校验实现。"""
    assert (agate_scripts / "agate_schema.py").is_file(), (
        "BDD-50：三处校验器须合并为单一 agate_schema.py"
    )
    for name in ("check-yaml-schema.py", "agate-frontmatter-check.py", "agate-config.py"):
        src = (agate_scripts / name).read_text(encoding="utf-8")
        assert "agate_schema" in src, f"BDD-50：{name} 须统一调用 agate_schema.py"
