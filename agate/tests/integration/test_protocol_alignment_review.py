# tests/integration/test_protocol_alignment_review.py — self-gate 机制测试
# （integration/protocol-alignment-review.bats 8 用例迁移，TAG0011 批次 14）
# 被测：agate/assets/review-roles/protocol-alignment-review.md（角色文件）+ 仓库根 SELF-GATE.md
#   + check-protocol-consistency.py 锚点表覆盖 + commit-msg-self-gate.sh 可执行。
# bats `$BATS_TEST_DIRNAME/../../../SELF-GATE.md` = 仓库根 SELF-GATE.md（= agate_root.parent）。
# windows_smoke：SG.1（文件首 @test，P3 §5.2 每文件第 1 用例打标）。

import os
import re

import pytest


def _role_file(agate_root):
    return agate_root / "assets" / "review-roles" / "protocol-alignment-review.md"


def _selfgate_file(agate_root):
    return agate_root.parent / "SELF-GATE.md"


@pytest.mark.windows_smoke
def test_sg_1_role_file_exists_with_required_frontmatter(agate_root):
    """SG.1：角色文件 protocol-alignment-review.md 存在且含必需 frontmatter。"""
    role_file = _role_file(agate_root)
    assert role_file.is_file()
    text = role_file.read_text(encoding="utf-8")
    assert re.search(r"^role_id: protocol-alignment-review", text, re.MULTILINE)
    assert re.search(r"^type: review", text, re.MULTILINE)
    assert re.search(r"^phases:", text, re.MULTILINE)
    assert re.search(r"^agent:", text, re.MULTILINE)


def test_sg_2_role_file_has_a1_a6_checklist(agate_root):
    """SG.2：角色文件含 A1-A6 审查清单。"""
    text = _role_file(agate_root).read_text(encoding="utf-8")
    for marker in ("A1", "A2", "A3", "A4", "A5", "A6"):
        assert marker in text


def test_sg_3_role_file_has_needs_human_review_loop(agate_root):
    """SG.3：角色文件含 NEEDS_HUMAN_REVIEW 闭环规则 + HUMAN_CONFIRMED 标记。"""
    text = _role_file(agate_root).read_text(encoding="utf-8")
    assert "NEEDS_HUMAN_REVIEW" in text
    assert "HUMAN_CONFIRMED" in text


def test_sg_4_selfgate_has_dispatch_template(agate_root):
    """SG.4：SELF-GATE.md 含派发模板。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "protocol-alignment-review" in text
    assert "审查清单" in text
    assert "配套文件提示" in text


def test_sg_5_selfgate_has_checklist(agate_root):
    """SG.5：SELF-GATE.md 含检查清单。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "protocol-alignment-review" in text
    # 检查清单引用 check-protocol-consistency 的结构 CHECK 集（不写死上界——CHECK 数会增长）
    assert "check-protocol-consistency.py" in text
    assert "CHECK" in text
    assert "HUMAN_CONFIRMED" in text


def test_sg_6_check9_anchor_table_covers_all_gate_scripts(agate_scripts):
    """SG.6：CHECK 9 锚点表覆盖全部 gate 脚本（check-*.py + pre-commit-gate 薄壳）。

    每个 gate 脚本的 basename 都应出现在 check-protocol-consistency.py 锚点表中。
    """
    consistency_script = agate_scripts / "check-protocol-consistency.py"
    assert consistency_script.is_file()
    consistency_text = consistency_script.read_text(encoding="utf-8")

    script_names = sorted(
        {p.name for p in agate_scripts.glob("check-*.py")}
        | {p.name for p in agate_scripts.glob("pre-commit-gate.sh")}
        | {p.name for p in agate_scripts.glob("pre-commit-gate.py")}
    )
    for name in script_names:
        assert name in consistency_text, f"FAIL: {name} 不在 CHECK 9 锚点表中"


def test_sg_7_commit_msg_self_gate_exists_executable(agate_scripts):
    """SG.7：commit-msg-self-gate.sh 存在且可执行。"""
    hook_script = agate_scripts / "commit-msg-self-gate.sh"
    assert hook_script.is_file()
    assert os.access(hook_script, os.X_OK)


def test_sg_8_selfgate_has_recursion_termination(agate_root):
    """SG.8：SELF-GATE.md 含递归终止条件。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "递归终止" in text
    assert "ALIGNED" in text
