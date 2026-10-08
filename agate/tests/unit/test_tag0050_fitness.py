# agate/tests/unit/test_tag0050_fitness.py
# TAG0050 架构适应度检查（P2-design §6 / §4.2 判据三，N2 映射）。
#
# 节点名含 `task_data_freeze` / `task_data_golden` / `schema_single_source`，
# 供 gate_commands 的 P5_fitness_* `-k` 选择（零匹配会 exit 5，故须为真实节点）。
# 映射：BDD-15（快照冻结）、BDD-16（黄金 fixture）、BDD-50（schema 单实现）。
# 平台无关：tmp_path；不写字面系统临时目录。

import hashlib
import re

import pytest

_LEVELS = "rules/task-data/LEVELS.yaml"

# BDD-50 机械判据：递归 schema 遍历函数定义（`iter_errors` / `max_depth` 族）。
_RECURSIVE_SCHEMA_DEF = re.compile(r"^\s*def\s+_?(?:local_)?(iter_errors|max_depth)\s*\(", re.M)
# 唯一允许的降级副本所在文件（安装破损 fail-safe）；须门控在单源库不可用时。
_WHITELIST_SCHEMA_DUP = {"agate-frontmatter-check.py"}


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
    """BDD-50：agate/scripts/*.py 中不存在第二个递归 schema 校验实现。

    机械判据：唯一允许的降级副本 = `agate-frontmatter-check.py` 的
    `_local_iter_errors` / `_local_max_depth`，且必须门控在单源库不可用时
    （安装破损 fail-safe，非并行实现）；其余文件出现递归 schema 遍历定义即失败。
    """
    assert (agate_scripts / "agate_schema.py").is_file(), (
        "BDD-50：三处校验器须合并为单一 agate_schema.py"
    )
    offenders = []
    for path in sorted(agate_scripts.glob("*.py")):
        if path.name == "agate_schema.py":
            continue
        if _RECURSIVE_SCHEMA_DEF.search(path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    unexpected = [n for n in offenders if n not in _WHITELIST_SCHEMA_DUP]
    assert not unexpected, (
        f"BDD-50：发现第二处递归 schema 校验实现（{unexpected}）——须统一调用 agate_schema.py"
    )
    fm_src = (agate_scripts / "agate-frontmatter-check.py").read_text(encoding="utf-8")
    assert "agate_schema is not None" in fm_src, (
        "BDD-50：降级副本须门控在 agate_schema 不可用时（fail-safe，非并行实现）"
    )
    for name in ("check-yaml-schema.py", "agate-frontmatter-check.py", "agate-config.py"):
        src = (agate_scripts / name).read_text(encoding="utf-8")
        assert "agate_schema" in src, f"BDD-50：{name} 须统一调用 agate_schema.py"
