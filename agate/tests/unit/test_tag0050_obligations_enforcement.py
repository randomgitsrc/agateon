# agate/tests/unit/test_tag0050_obligations_enforcement.py
# TAG0050 批 A4（义务执行方式机械核验，修复 F13）的 `test` 凭证载体。
#
# 每条 M 义务在 `rules/obligations.yaml` 的 `test:` 指向本文件的一个参数化节点
# （节点 id 含义务 id）。节点的职责：核验该义务确实登记了 `enforced_at`（机械落点）——
# 这样删掉 obligations.yaml 中的落点会使对应节点转红（负向控制的最小凭证）。
#
# ⚠️ G1-fix3（K2/K3）：本节点是**辅助的「登记存在」断言**，对「义务是否真被执行」不敏感
# （删掉义务的执行分支，本节点**不**转红）——故它是**登记凭证**而非行为凭证。抽样的 M 义务
# （OBL-P8-01/02/03、P1-10、P2-07、P2-10）的 `test:` 已改指**真实行为凭证**
# `test_tag0050_obligation_behavior.py`（删执行分支会转红，见 `test_bdd_42_negative_control_mutation`）。
# 其余未抽样义务仍以本节点为「登记存在」辅助断言（设计 §2.9 允许负向控制**抽样**执行）。
#
# 平台无关：只读仓库内 YAML 文本；不裸 python3；不写字面系统临时目录。

import re
from pathlib import Path

import pytest

_OBLIGATIONS = Path(__file__).resolve().parents[2] / "rules" / "obligations.yaml"

M_IDS = [
    "OBL-P1-01",
    "OBL-P1-02",
    "OBL-P1-05",
    "OBL-P1-10",
    "OBL-P1-11",
    "OBL-P1-12",
    "OBL-P2-01",
    "OBL-P2-02",
    "OBL-P2-04",
    "OBL-P2-07",
    "OBL-P2-08",
    "OBL-P2-10",
    "OBL-P2-12",
    "OBL-P3-03",
    "OBL-P4-01",
    "OBL-P4-03",
    "OBL-P4-06",
    "OBL-P4-08",
    "OBL-P5-02",
    "OBL-P5-04",
    "OBL-P6-01",
    "OBL-P6-02",
    "OBL-P6-03",
    "OBL-P6-04",
    "OBL-P6-05",
    "OBL-P6-08",
    "OBL-P6-09",
    "OBL-P6-10",
    "OBL-P6-11",
    "OBL-P6-13",
    "OBL-P7-01",
    "OBL-P7-02",
    "OBL-P7-03",
    "OBL-P7-05",
    "OBL-P8-01",
    "OBL-P8-02",
    "OBL-P8-03",
    "OBL-P8-04",
    "OBL-P8-05",
    "OBL-P8-06",
    "OBL-P8-14",
    "OBL-X-01",
    "OBL-X-02",
    "OBL-X-03",
    "OBL-X-04",
    "OBL-X-05",
    "OBL-X-06",
    "OBL-X-07",
    "OBL-X-08",
    "OBL-X-09",
    "OBL-X-10",
    "OBL-X-11",
    "OBL-X-12",
    "OBL-X-13",
    "OBL-X-14",
    "OBL-X-15",
    "OBL-X-16",
    "OBL-X-17",
    "OBL-X-18",
    "OBL-X-19",
]


def _read():
    return _OBLIGATIONS.read_text(encoding="utf-8")


@pytest.mark.parametrize("obl_id", M_IDS)
def test_obligation_enforced(obl_id):
    """M 义务须登记 enforced_at 机械落点（TAG0050 批 A4 / F13）。"""
    text = _read()
    m = re.search(r"- id:\s*" + re.escape(obl_id) + r"\b(.*?)(?=\n\s*-\s*id:|\Z)", text, re.S)
    assert m is not None, f"{obl_id} 未在 obligations.yaml 登记"
    block = m.group(1)
    assert "enforced_at" in block, f"{obl_id} 缺 enforced_at 机械落点（删掉落点本节点应转红）"
