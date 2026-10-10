# agate/tests/unit/test_tag0050_proxy_judgment.py
# TAG0050 批 F（代理判定，含 RM-AG0085、RM-AG0087、F12）红灯测试。
#
# 映射：BDD-67..BDD-72（P1-requirements.md §4；设计 §7、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h
from conftest import add_p1_field, add_p2_review


@pytest.mark.windows_smoke
def test_bdd_67_ui_dimension_na_without_reason_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-67：UI 维度标 na 却无理由判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    p2 = d / "P2-design.md"
    p2.write_text(
        "---\nagent: test\nui_affected: true\n"
        "ui_design:\n  shape: render_component\n  dimensions:\n"
        "    视觉: {status: na}\n---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P2", str(d))
    assert r.returncode != 0, f"BDD-67：na 无 reason 须 ERROR，实际 rc={r.returncode}"


def test_bdd_68_reviewed_bdds_mismatch_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-68：reviewed_bdds 不相等判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P1-review.md").write_text(
        "---\nagent: reviewer\nreviewed_bdds: []\n---\nreview\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P1", str(d))
    assert r.returncode != 0, f"BDD-68：reviewed_bdds 须等于 P1 BDD 集合，实际 rc={r.returncode}"


def test_bdd_69_skeleton_prose_not_treated_as_heading(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-69：骨架标题级判定回归（RM-AG0085）——散文提及不算标题。

    Given check-gate.py 的骨架判定改为标题级匹配
    When 正文仅以散文提及「## 骨架声明」而非标题行
    Then 不被误判为「标题已存在」（gate 判 FAIL）。
    """
    d = task_dir()
    add_p1_field(d, "project_phase", "bootstrap")
    add_p2_review(d)
    (d / "P2-design.md").write_text(
        "---\nagent: test\ncandidate_count: 2\npackages: [a]\ndomains: [backend]\n"
        'ui_affected: false\ngate_commands: {P5: "pytest"}\n---\n\ntradeoff: x\n',
        encoding="utf-8",
    )
    (d / "P2-skeleton.md").write_text("这是说明，参见 ## 骨架声明 一节。\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P2", str(d))
    assert r.returncode == 1, (
        f"BDD-69：散文提及不得当标题，gate 须判 FAIL（rc=1），实际 rc={r.returncode}"
    )


def test_gap5_ui_design_missing_required_dimension_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-5：ui_design 缺 `shape` 决定的必填维度 → ERROR（快照 ui_design.shape_dimensions）。"""
    d = h.init_task_via_conftest(tmp_path)
    add_p2_review(d)
    (d / "P2-design.md").write_text(
        "---\nagent: test\ncandidate_count: 2\npackages: [a]\ndomains: [backend]\n"
        'ui_affected: true\ngate_commands: {P5: "pytest"}\n'
        "ui_design:\n  shape: layout\n  dimensions:\n    视觉: {status: covered}\n"
        "---\n\n### 候选方案 A：x\n### 候选方案 B：y\n## 权衡\nA 简单 B 稳健\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P2", str(d))
    assert r.returncode == 1, f"GAP-5：layout 缺 布局/交互 必填维度须 ERROR，实际 rc={r.returncode}"
    assert "必填维度" in r.output, r.output


def test_bdd_70_phase_set_not_closed_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-70：阶段集合不闭合判 ERROR（RM-AG0087）。

    ⚠️ **2026-10-09 修正（批 A2 评审 r1 实测指出本用例原为「假绿灯」）**：原实现跑
    `check-gate.py P1` 并只断言 `rc != 0`——但 `check-gate.py` **不调用** `check-pruning.py`，
    其 rc=1 的真实原因是 **judge.enabled 缺失**，与本条声称的「阶段集合不闭合」**无关**。
    现改为**直接跑 `check-pruning.py`**（RM-AG0087 硬检的真实落点）+ 断言**具体缺陷消息**。
    删 **P8**（不在不可裁剪集、不触发 P3/P7 条件）——注意删任何阶段都会连带触发其**裁剪条件**
    检查（如 P8 需 `internal_only: true`），故本用例靠「**阶段全集** + P8」这条**只有硬检才会
    产生**的消息锁定判据（已 scratch 实测：抽掉硬检 ⇒ 本用例转红）。
    """
    d = h.init_task_via_conftest(tmp_path)
    p1 = d / "P1-requirements.md"
    txt = p1.read_text(encoding="utf-8")
    assert "phases: [P1, P2, P3, P4, P5, P6, P7, P8]\n" in txt
    p1.write_text(
        txt.replace("phases: [P1, P2, P3, P4, P5, P6, P7, P8]\n",
                    "phases: [P1, P2, P3, P4, P5, P6, P7]\n", 1),
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-pruning.py"), str(d))
    assert r.returncode == 1, (
        f"BDD-70：phases∪pruned 不等于 phase_universe 须判失败（check-pruning 硬检）；"
        f"实际 rc={r.returncode}\n{r.output[-400:]}"
    )
    assert "阶段全集" in r.output and "P8" in r.output, (
        f"BDD-70：须报出「阶段全集」缺失项（P8）；实际输出 {r.output[-400:]!r}"
    )


def test_bdd_71_t2_catches_nonconforming_bdd_heading(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-71：T2 拦下 `### BDD-1:`（非规范标题）。"""
    d = h.init_task_via_conftest(tmp_path)
    p1 = d / "P1-requirements.md"
    p1.write_text(
        "---\nagent: test\n---\n\n### BDD-1: 非规范\n- Given a\n- When b\n- Then c\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P1", str(d))
    assert "#### BDD-" in r.output or "统一格式" in r.output, (
        "BDD-71：T2 须命中并指向统一格式 #### BDD-N:"
    )


def test_bdd_72_p8_delivery_structured(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-72：按 F12 方式篡改 P8 delivery 转红（结构化字段，不再子串判定）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P8-release.md").write_text(
        "---\nagent: test\n---\n\n暂不声明 delivery: 方式\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P8", str(d))
    assert r.returncode != 0, f"BDD-72：delivery 缺失须转红，实际 rc={r.returncode}"
