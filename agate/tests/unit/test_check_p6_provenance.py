# tests/unit/test_check_p6_provenance.py — P6 验收客观行为审计（check-p6-provenance.py）
# （check-p6-provenance.bats 36 用例迁移，TAG0011 批次 9b）
# 被测：agate/scripts/check-p6-provenance.py TASK_DIR（exit 0 = 通过 / exit 1 = 审计不通过 /
#   exit 2 = WARNING 不阻塞）。
# 流语义（P2 BLOCKER-1）：GATE PROVENANCE 消息一律 sys.stderr.write → 断言一律用合并流
#   result.output（等价 bats $output），未映射 .stdout。
# 依赖：conftest task_dir factory（create_task_dir 等价）+ add_p1_bdd（conftest 纯函数）。
#   P3 §4「fixtures/ 静态夹具」备注不适用本批——check-p6-provenance.bats 全 36 用例自建
#   task_dir + heredoc，无 load_fixture 引用（与 9a check-p6-evidence.bats 同形态）。
# PV_BDD19.1 / PV_BDD20.1 是 check-gate.py P7 集成用例（bats 同文件放置，迁移保留，
#   以 _run_gate_p7 调用）。
# 随机字节证据文件用 os.urandom + write_bytes（平台无关，不写字面命中行，BDD-5）。

import importlib.util
import os
import re
import sys

import pytest

from conftest import GitRepo, add_p1_bdd


def _run_prov(agate_scripts, python_exe, run_cli, td):
    return run_cli(python_exe, str(agate_scripts / "check-p6-provenance.py"), str(td))


def _run_gate_p7(agate_scripts, python_exe, run_cli, td):
    return run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(td))


def _write_p6(td, text):
    (td / "P6-acceptance.md").write_text(text, encoding="utf-8")


def _append_p6(td, text):
    with (td / "P6-acceptance.md").open("a", encoding="utf-8") as fh:
        fh.write(text)


def _add_evidence(td, rel_path, size=5000):
    full = td / "P6-evidence" / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(os.urandom(size))


@pytest.mark.windows_smoke
def test_pv_1_no_p6_file_exit_0(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "task"
    td.mkdir()
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_2_missing_ref_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (ghost.png)\n")
    (td / "P6-evidence").mkdir()
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "证据文件不存在" in result.output


def test_pv_3_vision_stripped_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("---\nagent: test\n---\nui_affected: true\n", encoding="utf-8")
    (td / "vision.yaml").write_text("vision_analysis:\n  summary:\n    blocker_count: 0\n", encoding="utf-8")
    _append_p6(td, "- PASS BDD-1 (screenshots/login.png) (vision: vision.yaml)\n")
    _add_evidence(td, "screenshots/login.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_4_both_parens_are_refs_missing_one_blocks(task_dir, agate_scripts, python_exe, run_cli):
    """**决策 C2**：一行内**全部**纯路径组都是引用 ⇒ 缺 `a.png` 应拦。

    原用例名 `test_pv_4_last_paren_taken_exit_0`、断言 exit 0，记录的是**旧语义**
    「只取末组」（故 `a.png` 缺失被忽略）。2026-10-03 按普查规则改为「**全部纯路径组**」，
    本用例随之反转断言。

    **C2 的存量差分**（独立评审代做，我采纳其结论选 C1 于**其它**方面）：
      · C2（全路径组）相对旧规则的**新增拦截 = 7 行 / 6 任务**
      · 其中**新假红 6 行**（`agate_common.py`×2、`protocol-tests.yml`、三个 URL）、
        **旧规则漏检的真违规 1 行**（T047:33 引用源码 `src/utils.py`）
      · 而 C2 换来的覆盖**同样是 0 个真实证据**
    ⇒ 最终裁决为 **C2**（全部纯路径组的并集）：两仓 main 与 C2 的差异行 **265**（我复核一致），
      而 C1（按 main 做法）与 C2 差 **107 行 / 多 140 引用**（裁决实测）⇒ **C2 变动面更小**。
      本用例的形态：`(a.png) (b.png)` **两组都是路径**，
      不属"非末组多为命令注记"（那是 65% 多括号行的主流，但**不是全部**）。
      两组皆路径时全取是普查规则的直接结论；真实数据中该形态 0 例，不产生存量影响。
    """
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (a.png) (b.png)\n")
    _add_evidence(td, "b.png", 1000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, "a.png 不存在 ⇒ 应拦（两组都是路径形态）"


def test_pv_4c_both_parens_exist_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """**正例**（F8）：两个括号组的文件**都存在** ⇒ 通过（与 pv_4 构成一对）。"""
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (a.png) (b.png)\n")
    _add_evidence(td, "a.png", 1000)
    _add_evidence(td, "b.png", 2000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_4b_all_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (a.png) (b.png)\n")
    (td / "P6-evidence").mkdir()
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_pv_bdd19_1_gate_p7_blocker_count_zero_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P7-consistency.md").write_text(
        "---\n"
        "phase: P7\n"
        "task_id: T001\n"
        "agent: consistency-reviewer\n"
        "blocker_count: 0\n"
        "deviation_count: 0\n"
        "deviation_critical_count: 0\n"
        "design_gap_count: 0\n"
        "design_gap_reviewed_count: 0\n"
        "---\n"
        "- [BLOCKER] 历史记录：早期草案曾有架构缺陷，已在本轮修订中解决，frontmatter blocker_count 已归零\n",
        encoding="utf-8",
    )
    result = _run_gate_p7(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_5b_shared_evidence_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    lines = "".join(f"- PASS BDD-{i} (e{1 + (i - 1) % 8}.json)\n" for i in range(1, 15))
    _write_p6(td, "---\nagent: test\n---\n" + lines)
    ev = td / "P6-evidence"
    ev.mkdir()
    for i in range(1, 9):
        (ev / f"e{i}.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_6_unreferenced_evidence_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (r1.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "r1.json").write_text("log\n", encoding="utf-8")
    (ev / "extra.json").write_text("filler\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未被" in result.output


def test_pv_7_gitkeep_hidden_excluded_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _append_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / ".gitkeep").touch()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_8_dispatch_context_prejudged_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P6-dispatch-context-subtask.md").write_text("- PASS BDD-1 pre-judged\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "P6-dispatch-context" in result.output


def test_pv_9_bdd_count_gt_p6_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    add_p1_bdd(td, "second scenario")
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "挑验" in result.output


def test_pv_10_no_standard_bdd_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    p1 = td / "P1-requirements.md"
    text = p1.read_text(encoding="utf-8")
    kept = [line for line in text.splitlines() if not re.match(r"^#### BDD-", line)]
    p1.write_text("\n".join(kept) + "\n", encoding="utf-8")
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未使用标准" in result.output


def test_pv_bdd_count_1_three_bdd_three_pass_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_bdd(td, "second")
    add_p1_bdd(td, "third")
    _append_p6(td, "- PASS BDD-1 (a.json)\n- PASS BDD-2 (b.json)\n- PASS BDD-3 (c.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    for name in ("a.json", "b.json", "c.json"):
        (ev / name).write_text("x\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_bdd_count_4_examples_table_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    with (td / "P1-requirements.md").open("a", encoding="utf-8") as fh:
        fh.write("\n| existing | result |\n|----------|--------|\n| 0        | 201    |\n| 5        | 400    |\n")
    _append_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("x\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_bdd_count_5_gap_numbering_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    with (td / "P1-requirements.md").open("a", encoding="utf-8") as fh:
        fh.write("\n#### BDD-3: third (skipped BDD-2 numbering on purpose)\n- Given x\n- When y\n- Then z\n")
    _append_p6(td, "- PASS BDD-1 (a.json)\n- PASS BDD-3 (b.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "a.json").write_text("x\n", encoding="utf-8")
    (ev / "b.json").write_text("x\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_11_ui_missing_vision_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("ui_affected: true\n", encoding="utf-8")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n")
    _add_evidence(td, "screenshots/login.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "缺 vision" in result.output


def test_pv_12_vision_yaml_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("ui_affected: true\n", encoding="utf-8")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png) (vision: vision/missing.yaml)\n")
    _add_evidence(td, "screenshots/login.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "vision YAML 引用的文件不存在" in result.output


def test_pv_13_vision_blocker_nonzero_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("ui_affected: true\n", encoding="utf-8")
    (td / "vision.yaml").write_text("vision_analysis:\n  summary:\n    blocker_count: 1\n", encoding="utf-8")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png) (vision: vision.yaml)\n")
    _add_evidence(td, "screenshots/login.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "blocker_count=" in result.output


def test_pv_14_missing_agent_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 2


def test_pv_15_high_risk_p2_review_main_agent_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(risk_level="high")
    (td / "P2-review.md").write_text("---\nagent: main\n---\nreview done\n", encoding="utf-8")
    _append_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_17_dispatch_context_task_section_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(risk_level="high")
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: verified (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    (td / "P6-dispatch-context-subtask.md").write_text(
        "## 客观信息（主 Agent 已查证）\n"
        "- 环境状态：debug server 运行中\n"
        "\n"
        "## 任务上下文（主 Agent 从 P0-brief + gate + 摘要积累）\n"
        "- 目标：逐条 BDD 验收\n"
        "- 关注点：P2 声明 ui_affected: true\n"
        "- 上游关键决策：architect 选择了方案 B\n"
        "- 上游结构化字段：\n"
        "  - packages: [pkg-a]\n"
        "  - ui_affected: true\n",
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_18_nested_parens_is_no_reference(task_dir, agate_scripts, python_exe, run_cli):
    """**决策 A1**：组内容是「path — 注释」⇒ 整组不是路径 ⇒ 该行「无引用」。

    原用例名 `..._exit_0`、断言 exit 0（旧规则把该组当引用）。2026-10-03 改为断言
    新语义：新任务（fixture 默认 created=截止日）⇒ **exit 1**，文案「未能提取证据引用」。
    A1 依据：两仓含内层括号的括号组 26 处，逐一 isfile **26/26 命中 0**（裁决复核一致）。
    """
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (screenshots/b07.png — element: .katex nth(1))\n")
    _add_evidence(td, "screenshots/b07.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, "A1：注释组不构成引用 ⇒ 新任务应报无引用"
    assert "未能提取证据引用" in result.output


def test_pv_19_nested_parens_vision_is_no_reference(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("---\nagent: test\n---\nui_affected: true\n", encoding="utf-8")
    (td / "vision.yaml").write_text("vision_analysis:\n  summary:\n    blocker_count: 0\n", encoding="utf-8")
    _write_p6(
        td,
        "---\nagent: test\n---\n- PASS BDD-1 (screenshots/b07.png — element: .katex nth(1)) (vision: vision.yaml)\n",
    )
    _add_evidence(td, "screenshots/b07.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    # A1：嵌套注释组不构成引用（vision 组已被剥离，剩下的仍是注释组）
    assert result.returncode == 1
    assert "未能提取证据引用" in result.output


def test_pv_20_nested_parens_missing_path_is_no_reference(task_dir, agate_scripts, python_exe, run_cli):
    """**裁决 §5.1 #4 明确**：期望值改为「无引用」报错，**不再是**「文件不存在」。

    原因：A1 下该组整体不被提取 ⇒ 根本走不到"查存在性"那一步。
    """
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (screenshots/missing.png — element: .katex nth(1))\n")
    (td / "P6-evidence" / "screenshots").mkdir(parents=True)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未能提取证据引用" in result.output, "A1：该组不构成引用 ⇒ 报无引用（而非文件不存在）"


def test_pv_21_log_exit_code_1_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (logs/test.log)\n")
    log = td / "P6-evidence" / "logs" / "test.log"
    log.parent.mkdir(parents=True)
    log.write_text("=== Test Results ===\ntotal: 3, passed: 2, failed: 1\nEXIT_CODE: 1\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert ("EXIT_CODE" in result.output) or ("矛盾" in result.output)


def test_pv_22_log_exit_code_0_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (logs/test.log)\n")
    log = td / "P6-evidence" / "logs" / "test.log"
    log.parent.mkdir(parents=True)
    log.write_text("=== Test Results ===\ntotal: 3, passed: 3, failed: 0\nEXIT_CODE: 0\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_23_log_no_exit_code_warning_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (logs/test.log)\n")
    log = td / "P6-evidence" / "logs" / "test.log"
    log.parent.mkdir(parents=True)
    log.write_text("=== Test Results ===\ntotal: 3, passed: 3, failed: 0\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert ("EXIT_CODE" in result.output) or ("跳过" in result.output)


def test_prov_multi_1_two_files_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: works (screenshots/file1.png, screenshots/file2.png)\n")
    _add_evidence(td, "screenshots/file1.png", 5000)
    _add_evidence(td, "screenshots/file2.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_prov_multi_2_one_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: works (screenshots/file1.png, screenshots/file2.png)\n")
    _add_evidence(td, "screenshots/file1.png", 5000)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "证据文件不存在" in result.output
    assert "screenshots/file2.png" in result.output


def test_pv_bdd20_1_gate_p7_design_gap_unpaired_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P7-consistency.md").write_text(
        "---\n"
        "phase: P7\n"
        "task_id: T001\n"
        "agent: consistency-reviewer\n"
        "blocker_count: 0\n"
        "deviation_count: 0\n"
        "deviation_critical_count: 0\n"
        "design_gap_count: 2\n"
        "design_gap_reviewed_count: 1\n"
        "---\n"
        "- [DESIGN_GAP_REVIEWED: 其中一项已确认]\n",
        encoding="utf-8",
    )
    result = _run_gate_p7(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "DESIGN_GAP" in result.output


def test_pv_dp1_dispatch_prompt_excluded_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(
        td,
        "---\n"
        "phase: P6\n"
        "task_id: T001-test\n"
        "type: acceptance\n"
        "parent: P5-test-results.md\n"
        "trace_id: T001-test-P6-20260725\n"
        "status: draft\n"
        "created: 2026-07-25\n"
        "agent: verifier\n"
        "---\n"
        "- PASS BDD-1: works (result.json)\n",
    )
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    (td / "P4-dispatch-prompt-implementer.md").write_text(
        "> render product\n你是 P4 阶段的 implementer 子 Agent。\n", encoding="utf-8"
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "dispatch-prompt" not in result.output


def test_pv_24_evidence_json_fail_vs_pass_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text(
        '{\n  "bdd_results": [\n    {"id": "BDD-1", "status": "fail"}\n  ]\n}\n',
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "evidence JSON 与 P6-acceptance.md 声明不一致" in result.output


def test_pv_25_evidence_json_all_pass_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text(
        '{\n  "bdd_results": [\n    {"id": "BDD-1", "status": "pass"}\n  ]\n}\n',
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_26_evidence_json_non_standard_skip_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text('{\n  "some_other_field": "value"\n}\n', encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_27_p6_fail_matches_json_fail_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    add_p1_bdd(td, "second scenario")
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (result.json)\n- FAIL BDD-2 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text(
        '{\n  "bdd_results": [\n'
        '    {"id": "BDD-1", "status": "pass"},\n'
        '    {"id": "BDD-2", "status": "fail"}\n'
        "  ]\n}\n",
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_pv_28_missing_agent_not_short_circuit_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text(
        '{\n  "bdd_results": [\n    {"id": "BDD-1", "status": "fail"}\n  ]\n}\n',
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "evidence JSON 与 P6-acceptance.md 声明不一致" in result.output


# ========== 批次 9d：TAG0006 UI/UX 机制 R1b GAP 放宽 + 无声明默认 available 语义（BDD-9） ==========
# 新增行为（P4 实现后落于 check-p6-provenance.py 审计 4）：
#   * P1 vision 三态读取：status=GAP 时 R1b 放宽"截图 PASS 必须引 vision YAML"——
#     改为要求"人工复核记录"被 PASS 引用（`manual-review: <file>`），文件存在（§2.8）
#   * 无视觉能力声明（capability_requirements 无 need 含 visual/vision）→ 默认 available 语义：
#     R1b 强制 + blocker_count 语义保持，不落入 GAP 放行（test_vision_none_1 兼容回归守卫）
# P1 夹具含 `#### BDD-1` 标准标题（审计 3 BDD 总数对照需 p1_bdd ≥ 1）。
# 平台无关：tmp_path 由 task_dir 提供；截图证据 os.urandom + write_bytes（5000→>1KB）。


def _write_vision_bdd_p1(td, status):
    """P1-requirements.md：标准 BDD-1 标题 + capability_requirements yaml 围栏块。status=None 表示无能力声明。"""
    body = (
        "---\nagent: test\nphase: P1\n---\n\n"
        "#### BDD-1: ui rendering\n- Given ui\n- When rendered\n- Then ok\n"
    )
    if status is not None:
        body += (
            "\n```yaml\n"
            "capability_requirements:\n"
            "  - need: visual-analysis\n"
            f"    status: {status}\n"
            "```\n"
        )
    (td / "P1-requirements.md").write_text(body, encoding="utf-8")


def _write_ui_gap_case(td, review_line=False, review_file=False):
    """ui_affected=true + 截图 PASS +（可选）manual-review 引用行与文件。

    夹具自带 agent 字段（P2/P6）——B1 修复后 GAP 分支不再整体 sys.exit(0)，
    而是继续跑审计 5/6 与协作规范 agent 字段检查；一个"完全合规"的 GAP 任务
    （vision 降级但 agent 字段齐全、审计 5/6 干净）应仍以 exit 0 通过。
    """
    (td / "P2-design.md").write_text("---\nagent: test\n---\nui_affected: true\n", encoding="utf-8")
    if review_line:
        _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (screenshots/login.png) (manual-review: review-gap.md)\n")
    else:
        _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (screenshots/login.png)\n")
    _add_evidence(td, "screenshots/login.png", 5000)
    if review_file:
        (td / "review-gap.md").write_text(
            "复核人: 张三\n复核时间: 2026-08-17\n结论: 人工复核通过\n", encoding="utf-8"
        )


def test_vision_gap_prov_1_gap_manual_review_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_bdd_p1(td, "GAP")
    _write_ui_gap_case(td, review_line=True, review_file=True)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_vision_gap_prov_2_gap_missing_review_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_bdd_p1(td, "GAP")
    _write_ui_gap_case(td, review_line=False, review_file=False)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "人工复核" in result.output


def test_vision_avail_1_ui_available_no_vision_yaml_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_bdd_p1(td, "available")
    _write_ui_gap_case(td, review_line=False, review_file=False)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "缺 vision" in result.output


def test_vision_none_1_no_decl_default_available_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_bdd_p1(td, None)
    _write_ui_gap_case(td, review_line=False, review_file=False)
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "缺 vision" in result.output


# B1 回归（TAG0006 修复轮）：GAP 分支修复后不再整体 sys.exit(0)——审计 5（日志
# EXIT_CODE 一致性，exit 1 硬检查）对 GAP 任务同样生效，不能因 vision 降级被静默跳过。
def test_vision_gap_prov_3_gap_audit5_log_mismatch_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_bdd_p1(td, "GAP")
    _write_ui_gap_case(td, review_line=True, review_file=True)
    _append_p6(td, "- PASS BDD-2 (logs/test.log)\n")
    log = td / "P6-evidence" / "logs" / "test.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("=== Test Results ===\ntotal: 3, passed: 2, failed: 1\nEXIT_CODE: 1\n", encoding="utf-8")
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert ("EXIT_CODE" in result.output) or ("矛盾" in result.output)


# ========== 审计 7：P6 引用 P5 证据的无改动校验（TAG0016 RM-AG0026 BDD-12/13）==========
# 被测：check-p6-provenance.py 新增函数 audit7_p5_evidence_reuse(task_dir, state_yaml)
#   （P2-design.md §3.5 伪代码：state_yaml 为已解析的 .state.yaml dict，读取可选字段
#   p5_pass_commit；返回三态字符串之一）：
#     "no_reuse_claim_possible" — p5_pass_commit 字段缺失（存量任务兼容，静默回退强制重跑）
#     "reuse_blocked"           — 检测到 p5_pass_commit..HEAD 间存在非产出文件改动（BDD-13）
#     "reuse_allowed"           — 排除 agate-workspace/tasks/ 前缀后 diff 为空（BDD-12）
# 审计 7 函数尚未实现（TAG0016 P4 落地）——本批次测试当前预期红灯：
#   AttributeError: module 'cpp_mod' has no attribute 'audit7_p5_evidence_reuse'
# （B 类：项目内属性/函数不存在）。
# 用真实 git 仓库（GitRepo fixture）构造 commit 历史而非 mock，贴近 §3.5 的 git diff 实现路径；
# EXCLUDE_PRODUCE_PREFIX = "agate-workspace/tasks/"（P2 minimal_validation 已用真实 git 命令验证
# 该前缀不匹配任何源码路径）。


def _load_prov_module(agate_scripts):
    path = os.path.join(str(agate_scripts), "check-p6-provenance.py")
    spec = importlib.util.spec_from_file_location("cpp_mod", path)
    cpp_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpp_mod)
    return cpp_mod


def _init_repo_with_p5_commit(tmp_path, task_rel="agate-workspace/tasks/T001-test"):
    """构造一个真实 git 仓库：先提交一份 P5 产出（模拟 P5 gate 通过 commit），
    返回 (repo, task_dir 绝对路径, p5_pass_commit 哈希)。"""
    repo = GitRepo(tmp_path)
    task_dir = tmp_path / task_rel
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-test-results.md").write_text(
        "pytest 916 passed, 0 failed\n", encoding="utf-8"
    )
    repo.commit("wf(T001-test-P5): baseline 916 全绿")
    p5_commit = repo.git("rev-parse", "HEAD").stdout.strip()
    return repo, task_dir, p5_commit


def test_bdd_12_audit7_no_changes_reuse_allowed(agate_scripts, tmp_path):
    """P6 验收发起时点距 P5 通过 commit 之间只有产出文件改动 → 判定可复用（reuse_allowed）。"""
    cpp_mod = _load_prov_module(agate_scripts)
    repo, task_dir, p5_commit = _init_repo_with_p5_commit(tmp_path)
    (task_dir / "P6-acceptance.md").write_text(
        "---\nagent: test\n---\n- PASS BDD-1 (result.json)\n", encoding="utf-8"
    )
    repo.commit("wf(T001-test-P6): acceptance draft")

    result = cpp_mod.audit7_p5_evidence_reuse(str(task_dir), {"p5_pass_commit": p5_commit})
    assert result == "reuse_allowed"


def test_bdd_13_audit7_non_produce_change_reuse_blocked(agate_scripts, tmp_path):
    """BDD-13：模拟 P6→P4 修复后重到 P6——P5 通过点之后又出现了非产出文件（真实源码）改动，
    必须拦截声明"引用 P5 证据"，强制重跑（返回 reuse_blocked）。"""
    cpp_mod = _load_prov_module(agate_scripts)
    repo, task_dir, p5_commit = _init_repo_with_p5_commit(tmp_path)
    src = tmp_path / "agate" / "scripts" / "some-fixed-script.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("print('P4 修复')\n", encoding="utf-8")
    repo.commit("wf(T001-test-P4): 修复 P6 退回的 bug")

    result = cpp_mod.audit7_p5_evidence_reuse(str(task_dir), {"p5_pass_commit": p5_commit})
    assert result == "reuse_blocked"


def test_bdd_12_audit7_missing_field_no_reuse_claim_possible(agate_scripts, tmp_path):
    """存量任务兼容：.state.yaml 无 p5_pass_commit 字段 → 静默回退强制重跑，不报错。"""
    cpp_mod = _load_prov_module(agate_scripts)
    _repo, task_dir, _p5_commit = _init_repo_with_p5_commit(tmp_path)

    result = cpp_mod.audit7_p5_evidence_reuse(str(task_dir), {})
    assert result == "no_reuse_claim_possible"


def test_bdd_13_audit7_only_produce_dirs_excluded_active_tasks_board(agate_scripts, tmp_path):
    """边界（P2 minimal_validation 附注）：跨任务共享看板文件 agate-workspace/tasks/active-tasks.md
    同样落在 EXCLUDE_PRODUCE_PREFIX 前缀下，应被排除、不误判为非产出文件改动。"""
    cpp_mod = _load_prov_module(agate_scripts)
    repo, task_dir, p5_commit = _init_repo_with_p5_commit(tmp_path)
    board = tmp_path / "agate-workspace" / "tasks" / "active-tasks.md"
    board.write_text("- T001-test: P6\n", encoding="utf-8")
    repo.commit("wf(T001-test-P6): 更新共享看板")

    result = cpp_mod.audit7_p5_evidence_reuse(str(task_dir), {"p5_pass_commit": p5_commit})
    assert result == "reuse_allowed"


def test_p4_review_critical1_git_diff_command_fails_fail_closed_reuse_blocked(
    agate_scripts, tmp_path, capsys
):
    """P4-review CRITICAL-1：p5_pass_commit 是 git diff 无法解析的伪造哈希（历史被 rebase/
    squash 移除、.state.yaml 手工写错、CI 浅克隆导致该 commit 不在本地历史）时，git diff
    命令本身失败（非 0 返回码 + 空 stdout）。修复前会被误判为"无改动"→ reuse_allowed；
    修复后须 fail-closed 判定为 reuse_blocked，且 stderr 诊断信息要点出"git 命令本身失败"
    （与"确实检测到改动"是不同性质的失败，不应混在同一条消息里）。"""
    cpp_mod = _load_prov_module(agate_scripts)
    _repo, task_dir, _p5_commit = _init_repo_with_p5_commit(tmp_path)
    fake_commit = "a" * 40  # 40 位十六进制格式合法，但仓库历史里不存在的伪造哈希

    result = cpp_mod.audit7_p5_evidence_reuse(str(task_dir), {"p5_pass_commit": fake_commit})
    assert result == "reuse_blocked"

    stderr = capsys.readouterr().err
    assert "git" in stderr
    assert "命令本身执行失败" in stderr or "命令本身失败" in stderr
    # 不应把"命令失败"误报成"检测到非产出文件改动"那条消息
    assert "检测到非产出文件改动" not in stderr


# ========== --audit7-only CLI 模式（TAG0016 SELF-GATE 修复轮 A1-c）==========
# 被测：check-p6-provenance.py --audit7-only TASK_DIR
#   只跑审计 7，三态结果打印到 stdout，一行 `AUDIT7_RESULT: <state>`；
#   exit code：reuse_allowed → 0；reuse_blocked → 1；no_reuse_claim_possible → 0。


def test_audit7_only_reuse_allowed_stdout_and_exit0(agate_scripts, python_exe, run_cli, tmp_path):
    repo, task_dir, p5_commit = _init_repo_with_p5_commit(tmp_path)
    (task_dir / ".state.yaml").write_text(f"p5_pass_commit: {p5_commit}\n", encoding="utf-8")
    repo.commit("wf(T001-test-P6): write state yaml")

    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-provenance.py"),
        "--audit7-only", str(task_dir),
    )
    assert result.returncode == 0
    assert "AUDIT7_RESULT: reuse_allowed" in result.stdout


def test_audit7_only_reuse_blocked_stdout_and_exit1(agate_scripts, python_exe, run_cli, tmp_path):
    repo, task_dir, p5_commit = _init_repo_with_p5_commit(tmp_path)
    (task_dir / ".state.yaml").write_text(f"p5_pass_commit: {p5_commit}\n", encoding="utf-8")
    repo.commit("wf(T001-test-P6): write state yaml")
    src = tmp_path / "agate" / "scripts" / "some-fixed-script.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("print('P4 修复')\n", encoding="utf-8")
    repo.commit("wf(T001-test-P4): 修复 P6 退回的 bug")

    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-provenance.py"),
        "--audit7-only", str(task_dir),
    )
    assert result.returncode == 1
    assert "AUDIT7_RESULT: reuse_blocked" in result.stdout


def test_audit7_only_p4_review_critical1_fake_commit_git_fails_exit1(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """P4-review CRITICAL-1 CLI 覆盖：--audit7-only 模式下伪造哈希导致 git diff 命令本身
    失败，同样须 fail-closed 走 reuse_blocked → exit 1（而非把失败误判成 reuse_allowed →
    exit 0）。"""
    repo, task_dir, _p5_commit = _init_repo_with_p5_commit(tmp_path)
    fake_commit = "b" * 40
    (task_dir / ".state.yaml").write_text(f"p5_pass_commit: {fake_commit}\n", encoding="utf-8")
    repo.commit("wf(T001-test-P6): write state yaml with bogus commit")

    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-provenance.py"),
        "--audit7-only", str(task_dir),
    )
    assert result.returncode == 1
    assert "AUDIT7_RESULT: reuse_blocked" in result.stdout


def test_audit7_only_missing_field_no_reuse_claim_possible_exit0(agate_scripts, python_exe, run_cli, tmp_path):
    _repo, task_dir, _p5_commit = _init_repo_with_p5_commit(tmp_path)
    # 无 .state.yaml → no_reuse_claim_possible（静默回退，不算失败退出码）

    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-provenance.py"),
        "--audit7-only", str(task_dir),
    )
    assert result.returncode == 0
    assert "AUDIT7_RESULT: no_reuse_claim_possible" in result.stdout


def test_audit7_only_missing_task_dir_arg_exit1(agate_scripts, python_exe, run_cli):
    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-provenance.py"),
        "--audit7-only",
    )
    assert result.returncode == 1


# ---- 奇数 `---` 不得吞掉尾部区间（RM-AG0077 子批 C，2026-09-29）----
#
# 缺陷：剥离 frontmatter 用「遇 `---` 就向后配对下一个 `---`」——**奇数个 `---`** 时
# 最后一个 `---` 之后直到 EOF 全被删除 ⇒ 尾部区间**静默逃过审计 2**（行首 PASS/FAIL
# 预判扫描），**同一违规因位置不同判定相反**。
# 爆炸半径实测：706 个存量 dispatch-context 中 11 个含奇数 `---`，修复后新增命中 0。


def test_pv_odd_dashes_tail_still_audited(task_dir, agate_scripts, python_exe, run_cli):
    """剥离 CARD 后含**奇数**个 `---` 时，尾部区间仍须参与审计 2（修复前漏检）。"""
    td = task_dir()
    (td / "P6-dispatch-context-subtask.md").write_text(
        "---\nphase: P6\n---\n"   # 顶部 frontmatter（第一对）
        "正文\n"
        "---\n"                    # 第 3 个 `---` ⇒ 奇数（旧实现从这里吞到 EOF）
        "- PASS BDD-99: 尾部违规\n",
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, f"尾部区间被吞掉（漏检）：{result.output[:300]}"
    assert "P6-dispatch-context" in result.output


def test_pv_odd_dashes_no_violation_no_false_prejudge(task_dir, agate_scripts, python_exe, run_cli):
    """负向对照：奇数 `---` 但**无判定词** ⇒ 审计 2 **不得**误报。

    只断言审计 2 的结论（不绑整体 exit code）：本夹具刻意最小化，其他审计（证据引用等）
    可能各自判红，与本修复无关——绑 rc 会把无关审计的失败误读成本修复的误报。
    """
    td = task_dir()
    (td / "P6-dispatch-context-subtask.md").write_text(
        "---\nphase: P6\n---\n正文\n---\n- 正常的说明行，不是判定词\n",
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert "验收结论预判" not in result.output, f"审计 2 误报：{result.output[:300]}"


def test_pv_unclosed_frontmatter_not_stripped(task_dir, agate_scripts, python_exe, run_cli):
    """起始 `---` 无闭合对 ⇒ **不剥离**并告警（宁可多审，不可吞正文）。"""
    td = task_dir()
    (td / "P6-dispatch-context-subtask.md").write_text(
        "---\nphase: P6\n- PASS BDD-99: 无闭合对时的违规\n",
        encoding="utf-8",
    )
    result = _run_prov(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, f"未闭合 frontmatter 吞掉了正文：{result.output[:300]}"
    assert "无闭合对" in result.output


# ── X4（TAG0042 批0）：复用声明改由**结构化字段**判定 ─────────────────────────
#
# 缺陷：`p6_declares_reuse` 用 `re.search(r"引用\s*P5\s*证据")` 判 —— 只认一种中文正序，
#   实测本仓 5 个真声明里**只命中 1 个**（其余写「P5 证据复用」倒序）。
#   而"加宽词表"方向已被第五轮评审否决：会命中否定式（TAG0033「**不走**「复用 P5 证据」口径」）
#   与描述文字 ⇒ 误报 ⇒ 又碰上"P5 后改过代码"就判 reuse_blocked ⇒ 把没复用的任务拦下。
# ⇒ 改为**以字段为准**（ADR-015 手段①：让错误不可能），关键词只在字段缺失时兜底 + WARNING。

def _load_prov_module(agate_scripts):
    """加载被测模块；**须把 scripts/ 放进 sys.path**——该脚本按「与 agate_common 同目录」
    直接 import（正常执行时脚本目录自动在 sys.path 上），importlib 加载则不会。

    同时断言 `_fm_field_value` 已就位：若 agate_common 导入失败会落到 ImportError 兜底
    （值为 None），那样字段类断言会**假失败**且看不出原因。
    """
    import importlib.util
    scripts_dir = str(agate_scripts)
    added = scripts_dir not in sys.path
    if added:
        sys.path.insert(0, scripts_dir)
    try:
        spec = importlib.util.spec_from_file_location(
            "prov_mod", str(agate_scripts / "check-p6-provenance.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if added:
            sys.path.remove(scripts_dir)
    assert mod._fm_field_value is not None, "agate_common 未导入成功（字段类断言会假失败）"
    return mod


def test_x4_field_true_is_declaration(tmp_path, agate_scripts):
    """① 字段 `p5_evidence_reuse: true` ⇒ 判为声明（即使正文无任何关键词）。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(tmp_path, "---\nagent: verifier\np5_evidence_reuse: true\n---\n无任何关键词\n")
    assert mod.p6_declares_reuse(str(tmp_path)) is True


def test_x4_field_false_overrides_keywords(tmp_path, agate_scripts):
    """② 字段 `false` ⇒ **正文出现任何关键词也不算声明**（TAG0033 型否定式归此列）。

    ⚠️ 本用例的正文**必须用兜底能识别的形态**（粗体独立声明），否则「字段 false 时
    不翻案」这段逻辑被删掉测试照样绿——**空转测试**（TAG0042 批0 评审 m-1 实测踩过：
    原正文用非粗体否定句，兜底本就认不出 ⇒ 删掉 false 分支仍全绿）。
    """
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\np5_evidence_reuse: false\n---\n"
        "- **P5 证据复用**：不走该口径（正文为粗体声明形态，兜底本可命中）\n",
    )
    assert mod.p6_declares_reuse(str(tmp_path)) is False, (
        "字段 false 时正文关键词不得翻案（否则误报 ⇒ reuse_blocked 拦下未复用的任务）"
    )


def test_x4_missing_field_falls_back_with_warning(tmp_path, agate_scripts, capsys):
    """③ 字段缺失 ⇒ 关键词兜底命中 + **WARNING 提示改用字段**（迁移期语义）。

    兜底只认**粗体独立声明**（实测本仓真声明即该形态）；见下方反例用例。
    """
    mod = _load_prov_module(agate_scripts)
    _write_p6(tmp_path, "---\nagent: verifier\n---\n- **P5 证据复用**：引用 ../P5-test-results/unit.md\n")
    assert mod.p6_declares_reuse(str(tmp_path)) is True
    err = capsys.readouterr().err
    assert "p5_evidence_reuse" in err, "字段缺失走关键词兜底时须提示改用结构化字段"


def test_x4_missing_field_reversed_phrasing_also_recognized(tmp_path, agate_scripts):
    """③ 补充：字段缺失时**倒序写法**（实测本仓主流写法「P5 证据复用」）也须识别。

    改前：正则只认「引用 P5 证据」⇒ 该写法静默漏判（实测本仓真声明 2 个全为倒序）。
    """
    mod = _load_prov_module(agate_scripts)
    _write_p6(tmp_path, "---\nagent: verifier\n---\n- **P5 证据复用（审计 7）**：无改动\n")
    assert mod.p6_declares_reuse(str(tmp_path)) is True, "倒序写法「P5 证据复用」须被识别"


def test_x4_negation_and_headings_are_not_declarations(tmp_path, agate_scripts):
    """兜底词表**不得**命中否定式/节标题（实测本仓 3 例误报，逐条固化为反例）。

    误报有害：audit 7 会据此判 reuse_blocked，把**根本没复用**的任务拦下。
    """
    mod = _load_prov_module(agate_scripts)
    cases = {
        "TAG0033 型（节标题 + 正文否定式）":
            "### 2.6 P5 证据复用判定\n\n- 本任务**不走「复用 P5 证据」口径**（非 refactor）。\n",
        "TAG0019 型（否定式说明）":
            "> 引用 P5 证据说明：本任务是功能任务，证据全部实测产出；**未在本报告作\"复用\"声明**。\n",
        "TAG0018 型（描述审计跑了）":
            "- `check-p6-provenance.py <task_dir>` → exit 0（… P5 证据复用判定均通过）\n",
    }
    for label, body in cases.items():
        _write_p6(tmp_path, "---\nagent: verifier\n---\n" + body)
        assert mod.p6_declares_reuse(str(tmp_path)) is False, (
            f"{label} 不得被判为复用声明（否则误报 ⇒ 拦下未复用的任务）"
        )


def test_x4_descriptive_literals_not_treated_as_declaration(tmp_path, agate_scripts):
    """禁用描述性字面：`reuse_allowed` / `reuse_blocked` 是**审计三态名**，不是复用声明。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\n---\n审计 7 判定 reuse_allowed；此前曾因改动判 reuse_blocked。\n",
    )
    assert mod.p6_declares_reuse(str(tmp_path)) is False, (
        "描述性字面（审计状态名）不得被当成复用声明"
    )


# ── X4 M-2（TAG0042 批0 评审）：结构性信号补召回 ────────────────────────────
#
# 缺陷：纯关键词判定漏判「实际复用了 P5 证据、但没写粗体声明」的任务（实测两仓 6 个：
#   TAG0003/0007/0027/0028 + peekview T083/T086 在 PASS 行里直接引用 P5-test-results）。
#   漏判是 **fail-open**：审计 7 只在 `reuse_blocked and p6_declares_reuse` 时才拦。
# 修法：字段缺失时，PASS 行引用 `P5-test-results` = **事实复用**（结构性信号，不看措辞）。

def test_x4_missing_field_pass_line_referencing_p5_is_declared(tmp_path, agate_scripts, capsys):
    """结构信号：字段缺失 + PASS 行引用 P5-test-results ⇒ 判为已声明 + WARNING。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\n---\n"
        "- PASS BDD-1 无改动（P5-test-results/unit.log）\n",
    )
    assert mod.p6_declares_reuse(str(tmp_path)) is True
    assert "P5-test-results" in capsys.readouterr().err


def test_x4_missing_field_negation_without_p5_ref_not_declared(tmp_path, agate_scripts):
    """否定式（不引用 P5 结果）不得被结构信号误判为声明（TAG0033/TAG0019 型）。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\n---\n"
        "### 2.6 P5 证据复用判定\n\n- 本任务**不走「复用 P5 证据」口径**（非 refactor）。\n"
        "- PASS BDD-1 已实测（P6-evidence/local.log）\n",
    )
    assert mod.p6_declares_reuse(str(tmp_path)) is False


def test_x4_explicit_false_with_p5_ref_is_conflict(tmp_path, agate_scripts):
    """自相矛盾：显式 `false` 但 PASS 行引用 P5 结果 ⇒ `p6_reuse_declaration_conflict` 为真。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\np5_evidence_reuse: false\n---\n"
        "- PASS BDD-1 无改动（P5-test-results/unit.log）\n",
    )
    assert mod.p6_reuse_declaration_conflict(str(tmp_path)) is True
    # 且 p6_declares_reuse 仍为 False（矛盾由独立函数处理，不混入声明判定）
    assert mod.p6_declares_reuse(str(tmp_path)) is False


def test_x4_explicit_false_without_p5_ref_not_conflict(tmp_path, agate_scripts):
    """显式 `false` 且 PASS 行不引用 P5 结果 ⇒ 无矛盾。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\np5_evidence_reuse: false\n---\n"
        "- PASS BDD-1 已实测（P6-evidence/local.log）\n",
    )
    assert mod.p6_reuse_declaration_conflict(str(tmp_path)) is False


# ── X4 M-2 召回补强（TAG0042 批0 独立评审 I-1）──────────────────────────────
#
# 缺陷：初版结构信号只经 `extract_evidence_refs` 判定，而该抽取器①先剥离反引号
#   code span、②只取「整组都是裸路径」的括号组 ⇒ **反引号包裹**与**裸引用**两种
#   真实形态提取不到，仍逃逸（实测 TAG0016/TAG0020 漏判）。修法：改为原始 PASS 行
#   正则（`P5-test-results/<file>.<ext>`），两路取并集。

@pytest.mark.parametrize(
    "line,label",
    [
        ("- PASS BDD-1 见 `P5-test-results/unit.md`（反引号包裹）", "backtick-wrapped"),
        ("- PASS BDD-1 复用 P5-test-results/unit.md（裸引用）", "bare"),
        ("- PASS BDD-1（证据：P5-test-results/unit.md）", "paren"),
        ("- PASS BDD-1 (P5-test-results/unit.md)", "ascii-paren"),
    ],
)
def test_x4_pass_line_p5_ref_shapes_are_caught(tmp_path, agate_scripts, line, label):
    """反射式逃逸回归：反引号包裹 / 裸引用 / 括号三种形态**都须**命中结构信号。

    独立评审 I-1 实测：反引号与裸引用两形态在旧实现下漏判（signal=False）⇒ fail-open 残留。
    本用例把它们逐条固化为回归（删掉原始行正则即变红）。
    """
    mod = _load_prov_module(agate_scripts)
    _write_p6(tmp_path, "---\nagent: verifier\n---\n" + line + "\n")
    assert mod.p6_declares_reuse(str(tmp_path)) is True, f"{label} 形态须命中结构信号（I-1）"


def test_x4_pass_line_dir_name_only_not_a_ref(tmp_path, agate_scripts):
    """判别力反例：PASS 行只出现**目录名** `P5-test-results/`（无扩展名）**不**算证据引用。

    实测本仓 TAG0020 BDD-4 的 `P5-test-results/`（黑名单串扫描的描述）即此形态——
    若正则不要求扩展名，会把「描述扫描路径」误判为复用声明。
    """
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\n---\n"
        "- PASS BDD-4 黑名单串扫描（P6-acceptance.md / P5-test-results/，大小写不敏感）\n",
    )
    assert mod.p6_declares_reuse(str(tmp_path)) is False, (
        "仅提及目录名（无 .ext）不得被当成 P5 证据引用"
    )


def test_x4_negation_with_backtick_p5_ref_not_declared(tmp_path, agate_scripts):
    """否定句即使提到反引号包裹的 P5 结果也**不**构成复用声明（保持 M-2 反例约束）。"""
    mod = _load_prov_module(agate_scripts)
    _write_p6(
        tmp_path,
        "---\nagent: verifier\n---\n"
        "### 2.6 P5 证据复用判定\n\n"
        "- 本任务**不走「复用 P5 证据」口径**（非 refactor）；`P5-test-results/unit.md` 仅作历史旁证。\n",
    )
    # 该行不是 PASS 行 ⇒ 结构信号不触发；正文为否定式 ⇒ 关键词兜底也不命中
    assert mod.p6_declares_reuse(str(tmp_path)) is False
