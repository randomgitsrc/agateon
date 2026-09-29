# tests/integration/test_protocol_alignment_review.py — self-gate 机制测试
# （integration/protocol-alignment-review.bats 8 用例迁移，TAG0011 批次 14）
# 被测：agate/assets/review-roles/protocol-alignment-review.md（角色文件）+ 仓库根 SELF-GATE.md
#   + check-protocol-consistency.py 锚点表覆盖 + commit-msg-self-gate.sh 可执行。
# bats `$BATS_TEST_DIRNAME/../../../SELF-GATE.md` = 仓库根 SELF-GATE.md（= agate_root.parent）。
# windows_smoke：SG.1（文件首 @test，P3 §5.2 每文件第 1 用例打标）。

import importlib.util
import os
import re
from pathlib import Path

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


def test_sg_6_check9_anchor_table_covers_all_gate_scripts(agate_root, agate_scripts, tmp_path):
    """SG.6：CHECK 9 锚点表覆盖全部 gate 脚本（check-*.py + pre-commit-gate 薄壳）。

    每个 gate 脚本都应已在 CHECK 9 锚点表**或** GATE_SCRIPT_EXEMPT 豁免集中。

    ⚠️ 2026-09-29（DEBT0046）修正判据：旧版断言 `name in consistency_text` 是**子串**判定，
    与本节自称的「锚点表覆盖」不等价——在 check-protocol-consistency.py 里写一行**注释**
    提及脚本名即可让本测试变绿，而 CHECK9-coverage 仍告警（实测复现，两处结论相反）。
    现改为消费被测脚本自己导出的单一判据 `uncovered_gate_scripts()`，与 gate 共用同一函数，
    使「测试绿而 gate 告警」不可能再出现。

    ⚠️ 但「共用同一函数」引入新的**真空风险**（2026-09-29 负向实测发现）：若该函数被改成
    永远返回 `[]`，本测试会**静默变绿**。故先做**非真空自证**——在同构的合成树上确认判据
    确实能报出未登记脚本；判据被架空时本测试与
    `test_t43_3/4/5`（合成树负向）会一起红。
    """
    consistency_script = agate_scripts / "check-protocol-consistency.py"
    assert consistency_script.is_file()
    spec = importlib.util.spec_from_file_location("cpc_sg6", consistency_script)
    cpc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpc)
    assert hasattr(cpc, "uncovered_gate_scripts"), (
        "check-protocol-consistency.py 缺 uncovered_gate_scripts()——SG.6 与 CHECK9-coverage "
        "须共用同一判据，否则会再出现「本测试绿而 gate 告警」的矛盾（DEBT0046 实测）"
    )

    # —— 非真空自证：同构合成树上，未登记的 check-*.py 必须被判据报出 ——
    probe_root = Path(tmp_path)
    (probe_root / "agate" / "scripts").mkdir(parents=True)
    (probe_root / "agate" / "scripts" / "check-sg6probe.py").write_text("# probe\n", encoding="utf-8")
    assert "agate/scripts/check-sg6probe.py" in cpc.uncovered_gate_scripts(probe_root), (
        "uncovered_gate_scripts 对未登记脚本返回了空——判据被架空（真空），SG.6 本身就失去意义"
    )

    uncovered = cpc.uncovered_gate_scripts(Path(agate_root).parent)
    assert uncovered == [], (
        f"FAIL: 以下 gate 脚本既不在 CHECK 9 锚点表、也不在豁免集中：{uncovered}"
    )


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
