# tests/unit/test_check_protocol_consistency.py — CHECK 9 锚点断言
# （check-protocol-consistency.bats 3 用例迁移，TAG0011 批次 10b）
# 被测：agate/scripts/check-protocol-consistency.py 的 SCRIPT_ALIGNMENT_ANCHORS 锚点表。
# bats 用 py_path（Windows 路径转换）+ 独立 python 进程加载模块；pytest 在测试进程内 importlib
#   等价加载（模块仅依赖 stdlib，无需 sys.path 注入；Windows 原生 Path 已是本机格式，
#   py_path 转换不再需要）。

import importlib.util
import os
from pathlib import Path

import pytest


def _load_cpc(agate_scripts):
    path = os.path.join(str(agate_scripts), "check-protocol-consistency.py")
    spec = importlib.util.spec_from_file_location("cpc", path)
    cpc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpc)
    return cpc


@pytest.mark.windows_smoke
def test_check_9_exit_code_anchor_exists(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    anchors = cpc.SCRIPT_ALIGNMENT_ANCHORS
    exit_code_anchors = [a for a in anchors if "EXIT_CODE" in a.get("keywords", [])]
    assert len(exit_code_anchors) >= 2, f"Expected >=2 EXIT_CODE anchors, got {len(exit_code_anchors)}"


def test_check_9_agate_alignment_review_threshold_anchor_exists(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    anchors = cpc.SCRIPT_ALIGNMENT_ANCHORS
    threshold_anchors = [
        a for a in anchors if "AGATE_ALIGNMENT_REVIEW_THRESHOLD" in a.get("keywords", [])
    ]
    assert len(threshold_anchors) >= 1, (
        f"Expected >=1 threshold anchor, got {len(threshold_anchors)}"
    )


def test_check_9_ci_gate_backstop_anchor_in_scan(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    anchors = cpc.SCRIPT_ALIGNMENT_ANCHORS
    cb_anchors = [a for a in anchors if "ci-gate-backstop.py" in a.get("script", "")]
    assert len(cb_anchors) >= 1, f"Expected >=1 ci-gate-backstop.py anchor, got {len(cb_anchors)}"


# ── CHECK 10（协议文档脚本名引用漂移）新增用例，TAG0013（追加，不改既有） ──────
# 夹具：最小假协议树（pytest tmp_path 下 agate/scripts/ 假脚本 + 协议文档面扫描文件），
#   直接调 check_script_name_refs(root, rep) 断言 rep.errors / rep.ok。
# 平台无关：不用 /tmp、不创建软链、文本 I/O 显式 utf-8。

_FAKE_SCAN_FILES = [
    "agate/WORKFLOW.md",
    "agate/dispatch-protocol.md",
    "agate/state-machine.md",
    "agate/role-system.md",
    "agate/loop-orchestration.md",
    "agate/git-integration.md",
    "agate/platform-notes.md",
    "agate/LIMITATIONS.md",
    "README.md",
    "agate/orchestrator-template.md",
    "agate/SETUP.md",
    "AGENTS.md",
    "agate/AGENTS.md",
    "agate/CONTEXT.md",
    "agate/UPGRADING.md",
    "agate/scripts/README.md",
    "CHANGELOG.md",
]

_FAKE_SCRIPT_FILES = [
    "agate/scripts/check-gate.py",
    "agate/scripts/agate_common.py",
    "agate/scripts/check-tdd-red.py",
    "agate/scripts/check-protocol-consistency.py",
    "agate/tests/scripts/count-tests.sh",
]


def _make_fake_protocol_tree(tmp_path):
    """构造最小假协议树：agate/scripts/ 假脚本 + 协议文档面扫描文件（默认空内容）。"""
    root = Path(tmp_path)
    for rel in _FAKE_SCAN_FILES + _FAKE_SCRIPT_FILES:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")
    return root


def _check10_errors(rep):
    return [e for e in rep.errors if e["check"] == "CHECK10-scriptref"]


def _check10_warnings(rep):
    return [w for w in rep.warnings if w["check"] == "CHECK10-scriptref"]


def test_bdd_1_checks_list_registers_check10(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    assert any(name.startswith("CHECK 10") for name, _ in cpc.CHECKS), (
        "CHECKS 未注册 CHECK 10（check_script_name_refs）"
    )


def test_bdd_1_check10_zero_drift_passes(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "WORKFLOW.md").write_text(
        "主 Agent 调用 check-gate.py 与 check-tdd-red.py 确认阶段推进。\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []
    assert "CHECK10-scriptref" in rep.passed


def test_bdd_2_check10_drift_error(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    phase_card = root / "agate" / "phase-cards" / "P3-tdd.md"
    phase_card.parent.mkdir(parents=True, exist_ok=True)
    phase_card.write_text("派发 check-nonexistent-script.py 确认红灯。\n", encoding="utf-8")

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    drift = _check10_errors(rep)
    assert len(drift) == 1, f"Expected 1 CHECK10 drift, got {len(drift)}"
    assert "check-nonexistent-script.py" in drift[0]["msg"]
    assert "P3-tdd.md" in drift[0]["loc"]


def test_bdd_2_blocker_check1_independent_when_check10_error(
    agate_scripts, tmp_path, monkeypatch, capsys
):
    """驱动 real main()：CHECK 10 报 ERROR 时 CHECK 1 状态行仍 ✅（BLOCKER-1，P2-review 缺口 8）。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    monkeypatch.setattr(cpc, "CHECKS", [
        ("CHECK 1  YAML 代码块可解析", lambda r, rep: None),
        ("CHECK 10 协议文档脚本名引用漂移", lambda r, rep: None),
    ])

    def _fake_run(root_, rep):
        rep.error(
            "CHECK10-scriptref",
            "引用了不存在的脚本: check-nonexistent-script.py",
            "agate/WORKFLOW.md:1",
        )

    monkeypatch.setattr(cpc, "run_all_checks", _fake_run)
    monkeypatch.setattr("sys.argv", ["check-protocol-consistency.py", "--root", str(root)])
    code = cpc.main()
    out = capsys.readouterr().out

    assert code == 1
    assert "✅ PASS  CHECK 1" in out
    assert "❌ FAIL  CHECK 10" in out
    # 回归根因锁定：旧逻辑 startswith("CHECK1") 会把 CHECK10-scriptref 误判给 CHECK 1
    assert "CHECK10-scriptref".startswith("CHECK1") is True


def test_bdd_2_blocker_check1_independent_when_check10_warning(
    agate_scripts, tmp_path, monkeypatch, capsys
):
    """驱动 real main()：CHECK 10 报 WARNING 时 CHECK 1 状态行仍 ✅（BLOCKER-1 双场景）。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    monkeypatch.setattr(cpc, "CHECKS", [
        ("CHECK 1  YAML 代码块可解析", lambda r, rep: None),
        ("CHECK 10 协议文档脚本名引用漂移", lambda r, rep: None),
    ])

    def _fake_run(root_, rep):
        rep.warn("CHECK10-scriptref", "CHANGELOG 历史脚本名（聚合提醒）", "CHANGELOG.md")

    monkeypatch.setattr(cpc, "run_all_checks", _fake_run)
    monkeypatch.setattr("sys.argv", ["check-protocol-consistency.py", "--root", str(root)])
    code = cpc.main()
    out = capsys.readouterr().out

    assert code == 0
    assert "✅ PASS  CHECK 1" in out
    assert "⚠️  WARN  CHECK 10" in out


def test_bdd_3_exempt_upgrading_whole_file(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "UPGRADING.md").write_text(
        "迁移：check-gate.sh → check-gate.py（对照表行）\n散文行含遗留 check-tdd-red.sh。\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []


def test_bdd_3_exempt_formatter_names_natural(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "WORKFLOW.md").write_text(
        "formatter 候选：pytest.sh / go-test.sh / my-runner.sh\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []


def test_bdd_3_exempt_hook_shells(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "WORKFLOW.md").write_text(
        "pre-commit-gate.sh 以软链方式安装。\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []


def test_bdd_3_exempt_count_tests_sh(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "WORKFLOW.md").write_text(
        "跑 bash agate/tests/scripts/count-tests.sh 防计数漂移。\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []


def test_bdd_3_exempt_scripts_readme_retired_names(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "agate" / "scripts" / "README.md").write_text(
        "退役：gate-result.sh / agate-workspace-resolve.sh / check-windows-smoke.sh\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []


def test_bdd_4_protocol_dirs_includes_phase_cards_rules(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    assert cpc.PROTOCOL_DIRS == (
        "agate/assets/",
        "agate/phase-cards/",
        "agate/rules/",
    )


def test_bdd_5_changelog_drift_aggregated_warning(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").write_text(
        "v0.30.0: 引入 check-gate.sh 统一 gate。\n",
        encoding="utf-8",
    )

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []
    assert len(_check10_warnings(rep)) == 1


def test_bdd_5_docs_dir_not_scanned(agate_scripts, tmp_path):
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    docs_file = root / "docs" / "superpowers" / "guide.md"
    docs_file.parent.mkdir(parents=True, exist_ok=True)
    docs_file.write_text("check-nonexistent-script.py 引用\n", encoding="utf-8")

    rep = cpc.Report()
    cpc.check_script_name_refs(root, rep)

    assert _check10_errors(rep) == []
    assert _check10_warnings(rep) == []


# ── CHECK 12（权威数值/规则跨文件一致性，防复发，TAG0016 RM-AG0025 BDD-9/10）────────
# 被测：AUTHORITATIVE_VALUE_ANCHORS 白名单锚点表 + check_authoritative_values(root, rep)。
# 设计依据：P2-design.md §2（候选 2：结构化权威锚点扫描，延续 CHECK 4/9/11 提取-比对模式）。
# CHECK 12 尚未实现（TAG0016 P4 落地）——本批次测试当前预期红灯：
#   AttributeError: module 'cpc' has no attribute 'AUTHORITATIVE_VALUE_ANCHORS' / 'check_authoritative_values'
# （B 类：项目内属性/函数不存在，不是测试代码自身语法错误）。
# 夹具用真实重试上限数值（P1=3/P2=3/P3=2/P4=3/P5=2/P6=2/P7=2/P8=2，P1-requirements.md §3.5
# 已核实），phase-cards 文件名用真实文件名（P3-tdd.md / P5-verification.md / P6-acceptance.md /
# P8-release.md 等），使夹具贴近迁移后的真实文档形态。

_RETRY_TABLE_MD = (
    "## 重试上限\n\n"
    "| 阶段 | MAX | 说明 |\n"
    "|------|-----|------|\n"
    "| P1 | 3 | 需求基线 |\n"
    "| P2 | 3 | 方案设计 |\n"
    "| P3 | 2 | TDD 红灯 |\n"
    "| P4 | 3 | 实现 |\n"
    "| P5 | 2 | 技术验证 |\n"
    "| P6 | 2 | 验收 |\n"
    "| P7 | 2 | 一致性 |\n"
    "| P8 | 2 | 发布 |\n"
)

_PHASE_CARD_NAMES = {
    "P1": "P1-requirements.md",
    "P2": "P2-design.md",
    "P3": "P3-tdd.md",
    "P4": "P4-implementation.md",
    "P5": "P5-verification.md",
    "P6": "P6-acceptance.md",
    "P7": "P7-consistency.md",
    "P8": "P8-release.md",
}

_AUTHORITATIVE_MAX = {"P1": 3, "P2": 3, "P3": 2, "P4": 3, "P5": 2, "P6": 2, "P7": 2, "P8": 2}


def _make_check12_tree(
    tmp_path, pointer_ok=True, mismatched_phase=None, redeclare_pointer=False,
    unrelated_table_outside_section=False,
):
    """构造 CHECK 12 最小假协议树：

    - agate/state-machine.md：权威重试上限表 + Pre-commit 指针句（既有正确模式，BDD-7/10 防误伤）
    - agate/rules/state-transitions.md：迁移后的纯指针句（或按参数还原为"仍复制完整表格"的
      迁移前状态 / 缺权威指针短语的占位状态）
    - agate/phase-cards/P{N}-*.md ×8：内联 MAX= 行（可注入一处与权威表不一致）
    - agate/dispatch-protocol.md、agate/git-integration.md：既有正确 Pre-commit 指针位置
      （P1 3.4 节已验证，只含指针句不含数值表，CHECK 12 锚点表物理上不扫描这两处的数值）
    """
    root = Path(tmp_path)
    sm = root / "agate" / "state-machine.md"
    sm.parent.mkdir(parents=True, exist_ok=True)
    sm.write_text(
        "# state-machine\n\n本表是重试上限的唯一权威源；`rules/state-transitions.md` 与 8 张阶段"
        "卡片均须与本表一致（CHECK 12 自动校验）。\n\n" + _RETRY_TABLE_MD
        + "\n## Pre-commit 检查全景\n"
        "完整清单见 `WORKFLOW.md`「Pre-commit 检查总览」——权威唯一来源，本文件不重复维护。\n",
        encoding="utf-8",
    )

    st = root / "agate" / "rules" / "state-transitions.md"
    st.parent.mkdir(parents=True, exist_ok=True)
    if redeclare_pointer:
        # 迁移前状态：文件头已声明"权威源"，但正文仍复制完整数值表（M11 待落地前的红灯基线）
        st.write_text(
            "> 权威源：`agate/state-machine.md`。\n\n" + _RETRY_TABLE_MD, encoding="utf-8"
        )
    elif pointer_ok:
        # 迁移后状态：纯指针句，不含数值表
        content = (
            "> 权威源：`agate/state-machine.md`。\n\n## 重试上限\n\n"
            "详见 `agate/state-machine.md`《重试上限》——权威唯一来源，本文件不重复维护。\n"
        )
        if unrelated_table_outside_section:
            # P4-review CRITICAL-2 误报防护用例：文件里另有一个与「## 重试上限」无关的
            # 小节，其表格行形状恰好命中 ≥3 组 (phase, value) 组合（P1=3/P2=3/P3=2，
            # 与权威表 _AUTHORITATIVE_MAX 一致），但语义上与重试上限完全无关（示意任务
            # 追踪表）。修复前（全文无范围扫描）会被误判为"重新声明了权威表格"；修复后
            # （小节限定扫描）不应触发。
            content += (
                "\n## 状态标记绑定（与重试上限无关的另一张表）\n\n"
                "| 阶段 | 计数 | 说明 |\n|------|-----|------|\n"
                "| P1 | 3 | 示例 |\n| P2 | 3 | 示例 |\n| P3 | 2 | 示例 |\n"
            )
        st.write_text(content, encoding="utf-8")
    else:
        # 缺权威指针短语的占位状态（边界：既不复制表格也不指向权威源）
        st.write_text("## 重试上限\n\n（占位内容，未声明来源）\n", encoding="utf-8")

    for phase, fname in _PHASE_CARD_NAMES.items():
        card = root / "agate" / "phase-cards" / fname
        card.parent.mkdir(parents=True, exist_ok=True)
        value = _AUTHORITATIVE_MAX[phase]
        if mismatched_phase == phase:
            value = 99
        card.write_text(f"# {fname}\n\n本阶段重试上限 MAX={value}\n", encoding="utf-8")

    # BDD-7/10：既有正确"权威源+指针"位置（Pre-commit 清单，P1 3.4 节已验证），
    # 不含权威数值表，CHECK 12 的 retry-max 锚点表不应扫描到这两处并误报。
    dp = root / "agate" / "dispatch-protocol.md"
    dp.parent.mkdir(parents=True, exist_ok=True)
    dp.write_text(
        "**Pre-commit 检查全景**：完整清单见 `WORKFLOW.md`「Pre-commit 检查总览」——"
        "权威唯一来源，本文件不重复维护。\n",
        encoding="utf-8",
    )
    gi = root / "agate" / "git-integration.md"
    gi.write_text(
        "阶段 commit 会触发 9 项 pre-commit 检查（详见 WORKFLOW.md「Pre-commit 检查总览」）。\n",
        encoding="utf-8",
    )

    return root


def test_bdd_9_checks_list_registers_check12(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    assert any(name.startswith("CHECK 12") for name, _ in cpc.CHECKS), (
        "CHECKS 未注册 CHECK 12（check_authoritative_values）"
    )


def test_bdd_9_authoritative_value_anchors_retry_max_registered(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    anchors = cpc.AUTHORITATIVE_VALUE_ANCHORS
    retry = [a for a in anchors if a.get("id") == "retry-max"]
    assert len(retry) == 1, f"Expected exactly 1 'retry-max' anchor, got {len(retry)}"
    anchor = retry[0]
    assert anchor["authoritative_file"] == "agate/state-machine.md"
    pointer_files = [pf["file"] for pf in anchor.get("pointer_files", [])]
    assert "agate/rules/state-transitions.md" in pointer_files
    inline_globs = [ivf["glob"] for ivf in anchor.get("inline_value_files", [])]
    assert "agate/phase-cards/P*-*.md" in inline_globs


def test_bdd_9_check12_mismatched_inline_max_reports_error(agate_scripts, tmp_path):
    """正报：8 张卡片中 P3 的内联 MAX 与权威表不一致 → CHECK 12 报 ERROR，消息含文件名与数值对。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path, mismatched_phase="P3")
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    errors = [e for e in rep.errors if e["check"] == "CHECK12-authval"]
    assert len(errors) == 1, f"Expected 1 CHECK12 mismatch error, got {len(errors)}"
    assert "P3-tdd.md" in errors[0]["msg"]
    assert "99" in errors[0]["msg"] and "2" in errors[0]["msg"]


def test_bdd_9_check12_consistent_values_zero_error(agate_scripts, tmp_path):
    """不误报：迁移后的一致状态（8 卡片值与权威表一致 + 指针文件为纯指针）应 0 ERROR。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path)
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    assert [e for e in rep.errors if e["check"] == "CHECK12-authval"] == []
    assert "CHECK12-authval" in rep.passed


def test_bdd_10_check12_no_false_positive_on_existing_precommit_pointers(agate_scripts, tmp_path):
    """BDD-10/BDD-7：既有正确 Pre-commit 权威源+指针位置（dispatch-protocol.md/git-integration.md/
    state-machine.md）不在 CHECK 12 的 retry-max 锚点扫描范围内，0 误报。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path)
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    assert [e for e in rep.errors if e["check"] == "CHECK12-authval"] == []


def test_bdd_5_check12_pointer_file_missing_phrase_reports_error(agate_scripts, tmp_path):
    """边界：rules/state-transitions.md 既不复制表格也不含权威指针短语 → 报 ERROR。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path, pointer_ok=False)
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    errors = [e for e in rep.errors if e["check"] == "CHECK12-authval"]
    assert len(errors) >= 1
    assert any("state-transitions.md" in e["msg"] for e in errors)


def test_bdd_5_check12_pointer_redeclares_table_reports_error(agate_scripts, tmp_path):
    """迁移前状态（M11 落地前的红灯基线）：rules/state-transitions.md 复制了完整数值表，
    即使文件头已声明"权威源"，仍应被判定为重新声明权威表格（BDD-5 的核心断言）。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path, redeclare_pointer=True)
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    errors = [e for e in rep.errors if e["check"] == "CHECK12-authval"]
    assert len(errors) >= 1
    assert any(
        "重新声明" in e["msg"] or "state-transitions.md" in e["msg"] for e in errors
    )


def test_p4_review_critical2_unrelated_table_outside_section_no_false_positive(
    agate_scripts, tmp_path
):
    """P4-review CRITICAL-2：指针文件里存在与「## 重试上限」无关的另一张表格，其行形状
    恰好命中 ≥3 组 (phase, value) 与权威表相同的组合，但语义上完全无关（不在「## 重试
    上限」小节内）。redeclares_table 修复前对全文做无范围扫描会误判为"重新声明了权威
    表格"；修复后须限定在「## 重试上限」小节内扫描，该小节本身仍是纯指针句，不应触发
    CHECK12-authval 误报。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_check12_tree(tmp_path, unrelated_table_outside_section=True)
    rep = cpc.Report()
    cpc.check_authoritative_values(root, rep)
    errors = [e for e in rep.errors if e["check"] == "CHECK12-authval"]
    assert errors == [], f"Expected 0 CHECK12 errors (false positive guard), got {errors}"
    assert "CHECK12-authval" in rep.passed


# ── BDD-9（DEBT0012 代码半）：`--strict-errors-only` 互斥模式 ──────────────
# TAG0017 P3（fg3-strict-mode-code 批次）新增。当前 main() 的 argparse 只定义了
# --root/--strict/--json，没有 --strict-errors-only，以下三个用例驱动 real main()
# （沿用 test_bdd_2_blocker_check1_independent_when_check10_error/warning 的既有
# 惯用法：monkeypatch CHECKS + run_all_checks 构造确定的 rep 状态，再用 sys.argv
# 注入 CLI flag 跑 real main()）。三个场景当前都应在 `code = cpc.main()` 这一行就
# 因 argparse "unrecognized arguments: --strict-errors-only" 而 SystemExit(2)
# 崩溃——这是预期的真红灯（B 类：CLI 接口缺失，不是测试代码写错），不要在这几个测
# 试里额外包一层 pytest.raises(SystemExit) 把它吞掉，否则会掩盖红灯语义。
#
# 命名说明：文件里已有的 test_bdd_9_* 前缀属于历史 CHECK9/12 任务，编号撞了但语义
# 无关；本批次改用 test_strict_errors_only_* 前缀避免撞名（dispatch-context 已指
# 明）。与既有 --strict 矩阵（test_bdd_2_blocker_check1_independent_when_check10_
# error/warning）并列，不修改那两个用例的行为。


def test_strict_errors_only_zero_error_zero_warning_exit_0(
    agate_scripts, tmp_path, monkeypatch, capsys
):
    """BDD-9 场景 1/3：0 ERROR + 0 WARNING → --strict-errors-only 应 exit 0。

    当前红灯来源：argparse 未定义 --strict-errors-only，main() 在解析 sys.argv 时
    直接 SystemExit(2)（unrecognized arguments），执行不到下面的断言。
    """
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    monkeypatch.setattr(cpc, "CHECKS", [
        ("CHECK 1  YAML 代码块可解析", lambda r, rep: None),
    ])

    def _fake_run(root_, rep):
        pass  # 不产出任何 ERROR / WARNING

    monkeypatch.setattr(cpc, "run_all_checks", _fake_run)
    monkeypatch.setattr(
        "sys.argv",
        ["check-protocol-consistency.py", "--root", str(root), "--strict-errors-only"],
    )

    code = cpc.main()
    out = capsys.readouterr().out

    assert code == 0
    assert "🎉" in out or "全部检查通过" in out


def test_strict_errors_only_zero_error_n_warning_exit_0_with_hint(
    agate_scripts, tmp_path, monkeypatch, capsys
):
    """BDD-9 场景 2/3：0 ERROR + N WARNING（N>0）→ --strict-errors-only 应 exit 0
    且打印提示信息（沿用现有非 JSON 分支已有的
    "仅有 {N} 个 WARNING，无 ERROR。" 提示行为，--strict-errors-only 不应压制它）。

    当前红灯来源：同上，argparse 未定义 --strict-errors-only，main() 解析
    sys.argv 阶段即 SystemExit(2)，执行不到下面的断言。
    """
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    monkeypatch.setattr(cpc, "CHECKS", [
        ("CHECK 1  YAML 代码块可解析", lambda r, rep: None),
    ])

    def _fake_run(root_, rep):
        rep.warn("CHECK1-yaml", "示例 WARNING 1", "agate/WORKFLOW.md:1")
        rep.warn("CHECK1-yaml", "示例 WARNING 2", "agate/WORKFLOW.md:2")
        rep.warn("CHECK1-yaml", "示例 WARNING 3", "agate/WORKFLOW.md:3")

    monkeypatch.setattr(cpc, "run_all_checks", _fake_run)
    monkeypatch.setattr(
        "sys.argv",
        ["check-protocol-consistency.py", "--root", str(root), "--strict-errors-only"],
    )

    code = cpc.main()
    out = capsys.readouterr().out

    assert code == 0
    assert "仅有 3 个 WARNING，无 ERROR。" in out


def test_strict_errors_only_n_error_exit_1(
    agate_scripts, tmp_path, monkeypatch, capsys
):
    """BDD-9 场景 3/3：N ERROR（N>0）→ --strict-errors-only 应 exit 1
    （与默认模式的 ERROR 判定一致，--strict-errors-only 不改变 ERROR 语义）。

    当前红灯来源：同上，argparse 未定义 --strict-errors-only，main() 解析
    sys.argv 阶段即 SystemExit(2)，执行不到下面的断言。
    """
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    monkeypatch.setattr(cpc, "CHECKS", [
        ("CHECK 1  YAML 代码块可解析", lambda r, rep: None),
    ])

    def _fake_run(root_, rep):
        rep.error("CHECK1-yaml", "示例 ERROR", "agate/WORKFLOW.md:1")

    monkeypatch.setattr(cpc, "run_all_checks", _fake_run)
    monkeypatch.setattr(
        "sys.argv",
        ["check-protocol-consistency.py", "--root", str(root), "--strict-errors-only"],
    )

    code = cpc.main()
    out = capsys.readouterr().out

    assert code == 1
    assert "示例 ERROR" in out


# ── CHECK 13（CHANGELOG 最新版本 ↔ UPGRADING 章节对应性）用例，RM-AG0052 ──────
# 背景：v0.62.0/v0.63.0 连续两次发布漏写 UPGRADING.md 版本章节（发布清单第 3 步纯人工兜底失效）。
# 夹具：_make_fake_protocol_tree 已含空 CHANGELOG.md 与 agate/UPGRADING.md。
# 平台无关：不用 /tmp、不创建软链、文本 I/O 显式 utf-8。

def _check13_errors(rep):
    return [e for e in rep.errors if e["check"] == "CHECK13-upgrading"]


def test_check13_checks_list_registers(agate_scripts):
    cpc = _load_cpc(agate_scripts)
    assert any(name.startswith("CHECK 13") for name, _ in cpc.CHECKS), (
        "CHECKS 未注册 CHECK 13（check_upgrading_section）"
    )


def test_check13_section_exists_zero_error(agate_scripts, tmp_path):
    """不误报：CHANGELOG 最新版本在 UPGRADING §3 有对应章节 → 0 ERROR。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").write_text(
        "# 变更日志\n\n## [0.63.0] - 2026-08-25\n\n### 新增\n\n- x\n\n## [0.62.0] - 2026-08-24\n",
        encoding="utf-8",
    )
    (root / "agate" / "UPGRADING.md").write_text(
        "## 3. 已知破坏性变更（按版本）\n\n### v0.63.0 — 工具链批（无破坏性变更）\n\ntext\n\n### v0.62.0 — 批\n",
        encoding="utf-8",
    )
    rep = cpc.Report()
    cpc.check_upgrading_section(root, rep)
    assert _check13_errors(rep) == []
    assert "CHECK13-upgrading" in rep.passed


def test_check13_section_missing_reports_error(agate_scripts, tmp_path):
    """正报：CHANGELOG 最新版本在 UPGRADING §3 无对应章节 → ERROR（v0.62.0/v0.63.0 事故场景）。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").write_text(
        "## [0.63.0] - 2026-08-25\n\n### 新增\n\n- x\n", encoding="utf-8",
    )
    (root / "agate" / "UPGRADING.md").write_text(
        "## 3. 已知破坏性变更（按版本）\n\n### v0.62.0 — 旧批（无 v0.63.0 章节）\n", encoding="utf-8",
    )
    rep = cpc.Report()
    cpc.check_upgrading_section(root, rep)
    errors = _check13_errors(rep)
    assert len(errors) == 1, f"Expected 1 CHECK13 error, got {len(errors)}"
    assert "0.63.0" in errors[0]["msg"]


def test_check13_unreleased_not_required(agate_scripts, tmp_path):
    """边界：[Unreleased] 区域不要求章节，只检查第一个已发布版本。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").write_text(
        "## [Unreleased]\n\n### 新增\n\n- y\n\n## [0.63.0] - 2026-08-25\n", encoding="utf-8",
    )
    (root / "agate" / "UPGRADING.md").write_text(
        "### v0.63.0 — 工具链批（无破坏性变更）\n", encoding="utf-8",
    )
    rep = cpc.Report()
    cpc.check_upgrading_section(root, rep)
    assert _check13_errors(rep) == []
    assert "CHECK13-upgrading" in rep.passed


def test_check13_no_changelog_silent_skip(agate_scripts, tmp_path):
    """边界：无 CHANGELOG.md → 静默跳过，0 ERROR 不崩溃。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").unlink()
    rep = cpc.Report()
    cpc.check_upgrading_section(root, rep)
    assert _check13_errors(rep) == []


def test_check13_no_released_version_warns(agate_scripts, tmp_path):
    """边界：CHANGELOG 只有 [Unreleased] 无已发布版本 → WARNING，不 ERROR。"""
    cpc = _load_cpc(agate_scripts)
    root = _make_fake_protocol_tree(tmp_path)
    (root / "CHANGELOG.md").write_text("## [Unreleased]\n\n- x\n", encoding="utf-8")
    rep = cpc.Report()
    cpc.check_upgrading_section(root, rep)
    assert _check13_errors(rep) == []
    assert any(w["check"] == "CHECK13-upgrading" for w in rep.warnings)


# ── canonical scratch 目录不得被扫描（2026-09-30 实测缺陷） ──
#
# 缺陷形态（本次实测，非推理）：评审/开发者按约定把 scratch 放进 `<项目根>/.agate-tmp/`
# （platform-notes「受限 harness 通用约束」约定 1），其中常含**整仓副本**（用于变异测试）。
# 而 `iter_md_files` 用 `root.rglob("*.md")` ⇒ 把那些副本里的 .md 一并扫入 ⇒
# 本机 consistency 报 **3072 ERROR**（引用不存在等），而 **CI（干净 checkout，无该目录）全绿**。
#
# ⇒ 这是「**本机环境决定红绿**」——与本仓在 `conftest._run_cli_impl` 里隔离 HOME 所对抗的
# 正是同一类问题。修法：按约定排除 scratch 目录（其内容按定义**必须被 VCS 忽略**、非协议正文）。


def test_bdd_scratch_dir_is_excluded_from_md_scan(agate_scripts, tmp_path):
    """`<root>/.agate-tmp/**/*.md` 不得被 iter_md_files 扫入。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    (root / "agate").mkdir(parents=True, exist_ok=True)
    (root / "keep.md").write_text("# keep\n", encoding="utf-8")
    scratch = root / ".agate-tmp" / "audit" / "base"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "CHANGELOG.md").write_text("# scratch copy\n", encoding="utf-8")
    (root / ".agate-tmp" / "probe.md").write_text("# probe\n", encoding="utf-8")

    rels = {str(f.relative_to(root)).replace(os.sep, "/") for f in cpc.iter_md_files(root)}
    assert "keep.md" in rels, "正常 .md 被误排除（判据过宽）"
    assert not any(r.startswith(".agate-tmp/") for r in rels), (
        f"scratch 目录被扫入 ⇒ 本机 consistency 会被 scratch 副本污染（CI 绿而本机红）：{sorted(rels)}"
    )


def test_bdd_scratch_dir_env_override_is_honored(agate_scripts, tmp_path, monkeypatch):
    """`AGATE_TMP_DIR` 覆盖 scratch 目录名时同样排除（约定 1 允许改名）。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    (root / "my-scratch" / "sub").mkdir(parents=True, exist_ok=True)
    (root / "my-scratch" / "sub" / "x.md").write_text("# x\n", encoding="utf-8")
    (root / "keep.md").write_text("# keep\n", encoding="utf-8")
    monkeypatch.setenv("AGATE_TMP_DIR", "my-scratch")

    rels = {str(f.relative_to(root)).replace(os.sep, "/") for f in cpc.iter_md_files(root)}
    assert "keep.md" in rels
    assert not any(r.startswith("my-scratch/") for r in rels), (
        f"AGATE_TMP_DIR 覆盖后未排除：{sorted(rels)}"
    )


# ── CHECK 7（§6 根治，TAG0042 批0 评审）：badge ↔ CHANGELOG 已发布版本（tag 无关）──
#
# 缺陷：原 CHECK 7 = 「badge ↔ 最新 git tag」⇒ 需要 tag 已存在；而 consistency 是单个
#   required job、CHECK 13 又需要 bump 已提交 ⇒ 逼出「先推 tag 再合 PR」。
# 修法：对标 CHANGELOG 最新已发布版本（与 CHECK 13 同源），不再要求 tag。

def _write_check7_tree(root, badge, changelog_body):
    (root / "README.md").write_text(
        f"[![version](https://img.shields.io/badge/version-v{badge}-blue)](x)\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(changelog_body, encoding="utf-8")


def test_check7_badge_matches_changelog_pass(agate_scripts, tmp_path):
    """badge == CHANGELOG 最新已发布版本 ⇒ PASS（不要求任何 tag）。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    _write_check7_tree(root, "1.2.3", "# CHANGELOG\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-01\n")
    rep = cpc.Report()
    cpc.check_version_badge(root, rep)
    assert not rep.errors
    assert "CHECK7-version" in rep.passed


def test_check7_badge_mismatch_changelog_error(agate_scripts, tmp_path):
    """badge != CHANGELOG 最新已发布版本 ⇒ ERROR + 指引。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    _write_check7_tree(root, "1.2.4", "# CHANGELOG\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-01\n")
    rep = cpc.Report()
    cpc.check_version_badge(root, rep)
    assert rep.errors, "badge 领先 CHANGELOG 应报 ERROR"
    assert rep.errors[0]["check"] == "CHECK7-version"


def test_check7_no_changelog_warns_not_errors(agate_scripts, tmp_path):
    """缺 CHANGELOG ⇒ WARNING（不假红）。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    (root / "README.md").write_text(
        "[![version](https://img.shields.io/badge/version-v1.0.0-blue)](x)\n", encoding="utf-8"
    )
    rep = cpc.Report()
    cpc.check_version_badge(root, rep)
    assert not rep.errors
    assert any(w["check"] == "CHECK7-version" for w in rep.warnings)
