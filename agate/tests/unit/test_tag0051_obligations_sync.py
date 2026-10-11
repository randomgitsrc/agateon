# agate/tests/unit/test_tag0051_obligations_sync.py — TAG0051 P3 红灯（obligations 同步）
#
# 覆盖 BDD（P1-requirements.md）：21。
#   * BDD-21：改 P8 语义时 `OBL-P8-01..14` 的 statement / anchor 无 version/tag 期残留，
#     且 `OBL-P8-04` 就地重挂为 `delivery.method_enum` 枚举校验（`disposition` 保持 **M**、
#     `enforced_at` → `gate_p8`），并断言 `M_IDS` 仍含该 id（≠删条目）。
#
# 现行为（改动前）：OBL-P8-04/05/08/13 的 statement 仍含 version/tag 期词汇、OBL-P8-04 仍挂
#   `main`（非 gate_p8）⇒ 断言失败 = B 类红灯。
#
# **判别力加固（NB-6）**：黑名单用**更宽的根词**（`版本号` / `tag` / `version` / `双路径` /
#   `最近 5 commit` / `bump 后`），**已对 OBL-P8-01..14 全量扫**确认对 10 条「保留」条目
#   **零误伤**（保留条目含 `bump_type`（OBL-P8-01），但**不**含上述谓词；故黑名单不含裸 `bump`）。
#
# 平台无关：只读仓库文本；不裸 python3；不写字面系统临时目录。

from pathlib import Path

import yaml

_OBLIGATIONS = Path(__file__).resolve().parents[2] / "rules" / "obligations.yaml"
_ENFORCEMENT = Path(__file__).resolve().parent / "test_tag0050_obligations_enforcement.py"

# version/tag 期词汇（黑名单根词；见文件头 NB-6 说明）。
_FORBIDDEN_TOKENS = ("版本号", "tag", "version", "双路径", "最近 5 commit", "bump 后")


def _obligations():
    # 顶层是映射（`schema_version` / `baseline` / `obligations`），条目列表在 `obligations` 键下
    # ——按 check-obligations.py 的同源口径取（:258 `data.get("obligations")`），不遍历顶层猜。
    data = yaml.safe_load(_OBLIGATIONS.read_text(encoding="utf-8"))
    return [
        o
        for o in data["obligations"]
        if isinstance(o, dict) and str(o.get("id", "")).startswith("OBL-P8-")
    ]


def _by_id(items, obl_id):
    for o in items:
        if o.get("id") == obl_id:
            return o
    return None


def test_bdd_21_obl_p8_statements_have_no_version_tag_residue():
    """BDD-21：OBL-P8-01..14 statement 无 version/tag 期词汇残留（NB-6 加固黑名单）。"""
    items = _obligations()
    assert len(items) == 14, f"BDD-21：OBL-P8 条目应为 14 条，实际 {len(items)}"
    violations = []
    for o in items:
        stmt = str(o.get("statement", ""))
        hits = [t for t in _FORBIDDEN_TOKENS if t in stmt]
        if hits:
            violations.append(f"{o.get('id')}: {hits} in {stmt!r}")
    assert not violations, (
        "BDD-21：OBL-P8-* statement 仍含 version/tag 期词汇（P8 去 tag/version 后应同步）：\n  "
        + "\n  ".join(violations)
    )


def test_bdd_21_obl_p8_04_remounted_to_method_enum():
    """BDD-21：OBL-P8-04 就地重挂为 `delivery.method_enum` 枚举校验（M 不变、落点 gate_p8）。"""
    o = _by_id(_obligations(), "OBL-P8-04")
    assert o is not None, "BDD-21：OBL-P8-04 不得删除（就地重挂）"
    assert o.get("disposition") == "M", (
        f"BDD-21：OBL-P8-04 disposition 须保持 M（不得改判 C/R），实际 {o.get('disposition')!r}"
    )
    stmt = str(o.get("statement", ""))
    assert "method_enum" in stmt, (
        f"BDD-21：OBL-P8-04 statement 须重挂为 delivery.method_enum 枚举校验，实际 {stmt!r}"
    )
    enforced_at = o.get("enforced_at") or {}
    assert isinstance(enforced_at, dict) and enforced_at.get("function") == "gate_p8", (
        f"BDD-21：OBL-P8-04 enforced_at 须指向 gate_p8，实际 {enforced_at!r}"
    )


def test_bdd_21_m_ids_keeps_obl_p8_04():
    """BDD-21：enforcement 测试的 `M_IDS` 仍含 `OBL-P8-04`（重挂后仍为 M，零增删）。"""
    text = _ENFORCEMENT.read_text(encoding="utf-8")
    assert '"OBL-P8-04"' in text, (
        "BDD-21：M_IDS 须保持含 OBL-P8-04（重挂后仍为 M）——删条目才须同步删该 id"
    )
