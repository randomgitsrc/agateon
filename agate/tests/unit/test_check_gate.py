# tests/unit/test_check_gate.py — check-gate.py 阶段 gate 总闸
# （check-gate.bats 124 用例迁移，TAG0011 批次 8a：G0 / G1 / G3 / G4 / G_OTHER，11 用例；
#   批次 8b：G2 系列 + G_BDD1.1/9.1/10.1 + G_CMD_EXEC.1/2，29 用例；
#   批次 8c：G5 / G5.1 / G5_CMD.1-5，7 用例；
#   批次 8d：G6 系列 + G_BDD16.1 + test_bdd_1..8（TAG0002 refactor 口径），20 用例；
#   批次 8e：G7.1-9 + G_DG_ANCHOR.1/2 + bdd-11（TAG0004 M4 全角冒号），12 用例；
#   批次 8f：G8.1-10（gate_p8 分支），10 用例；
#   批次 8g：G_RETREAT.1-6 + G_NC_BINARY.1/2/3/5/6 + G_SUGGEST.1-4，15 用例；
#   批次 8h：D-drift-1/2/4/4b/5/6 + G-drift-1/2/3 + TAG0005 BDD-1/2/9/12/13/14/15，16 用例；
#   批次 8 补遗：PG.P2REVIEW / bdd-14 / bdd-28 / bdd-29，4 用例）
# 被测：agate/scripts/check-gate.py（PHASE TASK_DIR [OLD_PHASE]；exit 0 = 通过 / exit 1 = 未通过 /
#   exit 2 = 主 Agent 自判）。
# G0/G1/G3/G_OTHER 用 task_dir factory（create_task_dir 等价）；G4 系列需要 git_repo
#   （gate_p4 检查 git diff --cached 暂存区）+ shutil.copytree 把 task 目录复制进 repo，
#   run_cli(..., cwd=repo) 等价 bats `cd '$repo' && ...`。
# 8b（gate_p2 分支）：task_dir + add_p2_candidate_count / add_p2_review / add_p1_field
#   （conftest 纯函数，frontmatter 块写入，T001 v2.0 流 A）；P2-design.md 用 heredoc 原文覆写。
# 流语义：GATE 前缀消息一律 sys.stderr.write → 按 P2 §3.2 先判流归属，
#   本文件断言一律用合并流 result.output（与 bats $output 等价，BLOCKER-1）。
# create_python_shim_bin 退役（P2 §3.1）：pytest 直跑解释器，无需 harness shim。

import importlib.util
import re
import shutil
from pathlib import Path

import pytest

from conftest import add_p1_field, add_p2_candidate_count, add_p2_review


def _run_gate(agate_scripts, python_exe, run_cli, phase, task_arg, cwd=None, env=None, old_phase=None):
    """bats `'$PYTHON' '$AGATE_SCRIPTS/check-gate.py' PHASE TASK_DIR [OLD_PHASE]` 等价。

    old_phase 对应 bats 可选第 3 参数（G_RETREAT 系列，回退抵达检测）。
    """
    cmd = [
        python_exe,
        str(agate_scripts / "check-gate.py"),
        phase,
        task_arg,
    ]
    if old_phase is not None:
        cmd.append(old_phase)
    return run_cli(*cmd, cwd=cwd, env=env)


def _init_repo_with_task(git_repo, td):
    """bats `git_init + echo init > README.md + git_commit + cp -r task` 等价。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    shutil.copytree(td, repo / "task")


def _write_p4_review(repo, status, agent):
    """写 repo/task/P4-review.md（bats heredoc 等价）。"""
    (repo / "task" / "P4-review.md").write_text(
        f"---\nstatus: {status}\nagent: {agent}\n---\nreviewed.\n",
        encoding="utf-8",
    )


@pytest.mark.windows_smoke
def test_g0_p0_no_unknown_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P0", str(td))
    assert result.returncode == 2
    assert "未知" not in result.output


def test_g1_p1_missing_review_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "P1-review.md" in result.output


def test_g3_p3_checks_test_cases_md(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P3", str(td))
    assert result.returncode == 1
    assert "P3-test-cases.md 不存在" in result.output

    (td / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    result = _run_gate(agate_scripts, python_exe, run_cli, "P3", str(td))
    assert result.returncode == 2
    assert "check-tdd-red.py" in result.output


def test_g4_1_staged_only_md_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    (repo / "task" / "P4-implementation.md").write_text("doc\n", encoding="utf-8")
    git_repo.stage("task/P4-implementation.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 1


def test_g4_2_staged_py_exit_0(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0


def test_g4_3_staged_mixed_exit_0(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "task" / "P4-implementation.md").write_text("doc\n", encoding="utf-8")
    (repo / "src.py").write_text("code\n", encoding="utf-8")
    (repo / "config.yaml").write_text("yaml: 1\n", encoding="utf-8")
    git_repo.stage(".")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0


def test_g4_4_py_not_excluded_exit_0(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("code\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0


def test_g4_5_missing_review_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    (repo / "src.py").write_text("code\n", encoding="utf-8")
    git_repo.stage("src.py")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "P4-review.md" in result.output


def test_g4_6_review_not_approved_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "rejected", "reviewer-subagent")
    (repo / "src.py").write_text("code\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "非 approved" in result.output


def test_g4_7_review_agent_main_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "main")
    (repo / "src.py").write_text("code\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "agent=main" in result.output


def test_other_unknown_phase_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P9", str(td))
    assert result.returncode == 1  # 原为 2，TAG0035 BDD-1 fail-closed 修复后改为 1
    assert "未知阶段" in result.output


# ========== 8b: gate_p2 分支（G2 系列 + G_BDD1.1/9.1/10.1 + G_CMD_EXEC） ==========

_P2_TWO_CAND_BODY = (
    "# P2 design\n"
    "### 候选方案 A：方案一\n"
    "### 候选方案 B：方案二\n"
    "## 权衡\n"
    "A 更简单，B 更稳健。\n"
    "packages: [pkg-a]\n"
    "domains: [backend]\n"
    "ui_affected: false\n"
    "gate_commands: {}\n"
)


def _write_p2_design(td, body):
    (td / "P2-design.md").write_text(body, encoding="utf-8")


def test_g2_1_zero_candidates_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, "# P2 design\n## 设计\n无候选方案。\n")
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "需至少 2 个候选方案" in result.output


def test_g2_2_one_candidate_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, "# P2 design\n### 候选方案 A：方案一\n")
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1


def test_g2_3_two_candidates_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_4_h5_candidates_not_recognized_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td, "# P2 design\n##### 候选方案 A：方案一\n##### 候选方案 B：方案二\n"
    )
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1


def test_g2_25_h4_candidates_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "#### 候选方案 A：方案一\n"
        "#### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_26_fullwidth_colon_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 方案：方案一\n"
        "### 方案：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_27_missing_candidate_count_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "candidate_count" in result.output


def test_g2_5_missing_p2_file_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir(
        phases=["P0", "P1", "P3", "P4", "P5", "P6", "P7", "P8"]
    )  # P2 不在
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "P2-design.md" in result.output


def test_g2_8_two_candidates_no_tradeoff_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "权衡" in result.output


def test_g2_9_two_candidates_with_tradeoff_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "方案 A 更简单但性能差，方案 B 复杂但性能好。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_9a_design_trivial_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    add_p1_field(td, "design_trivial", "true")
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "## 权衡\n"
        "简单修改，无需多方案。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 1)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_9b_follows_existing_pattern_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "follows_existing_pattern", "[src/foo.py]")
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：照搬已有模式\n"
        "## 权衡\n"
        "照搬 src/foo.py 模式。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 1)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_10_review_rejected_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: test\nstatus: rejected\n---\n## 裁决\n未通过。\n",
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "非 approved" in result.output


def test_g2_10a_rejected_with_approved_literal_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: test\nstatus: rejected\n---\n## 裁决说明\n\n"
        "gate 规则要求 status: approved 才放行，本次评审未通过。\n",
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "非 approved" in result.output


def test_g2_11_review_approved_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: test\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_bdd1_1_four_fields_via_frontmatter_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "---\n"
        "phase: P2\n"
        "task_id: T001\n"
        "agent: architect\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "---\n"
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_13_missing_review_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "P2-review.md" in result.output


def test_cmd_exec_1_missing_cmd_warning_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands:\n"
        '  P3: "definitely-nonexistent-cmd --flag"\n'
        '  P5: "echo hi"\n',
    )
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: test\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2
    assert "definitely-nonexistent-cmd" in result.output


def test_cmd_exec_2_all_cmds_executable_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands:\n"
        '  P3: "true"\n'
        '  P5: "echo hi"\n',
    )
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: test\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2
    assert "不存在" not in result.output


def test_g2_14_candidate_with_space_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 方案 A\n"
        "### 方案 B\n"
        "## 权衡\n"
        "A 简单，B 稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_bdd10_1_frontmatter_count_wins_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n"
        "candidate_count: 1\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_17_selection_title_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "### 选择：方案 A\n"
        "**理由**：A 更简单。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_18_review_agent_subagent_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: subagent\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_19_review_agent_main_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nagent: main\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "agent=main" in result.output


def test_g2_20_review_missing_agent_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    (td / "P2-review.md").write_text(
        "---\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2
    assert "agent" in result.output


def test_g2_7_h2_candidates_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "## 候选方案 A\n"
        "## 候选方案 B\n"
        "## 权衡\n"
        "A 简单，B 稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_21_multiple_word_candidates_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 方案 Alpha\n"
        "### 方案 Beta\n"
        "## 权衡\n"
        "Alpha 简单，Beta 稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_bdd9_1_legacy_body_fields_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_g2_24_numeric_candidates_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "# P2 design\n"
        "### 方案 1\n"
        "### 方案 2\n"
        "## 权衡\n"
        "方案 1 简单，方案 2 稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n",
    )
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


# ========== 8c: gate_p5 分支（G5 / G5.1 / G5_CMD.1-5） ==========

def test_g5_p5_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2


def test_g5_1_multi_cmd_warning(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "---\n"
        "phase: P2\n"
        "task_id: T001\n"
        "agent: architect\n"
        "---\n"
        "\n"
        "gate_commands:\n"
        '  P5: "pytest -q --tb=no"\n'
        '  P5_e2e: "playwright test --reporter=line tests/e2e/"\n',
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert (
        "gate_commands.P5" in result.output
        or "子集" in result.output
        or "全量" in result.output
    )


def test_g5_cmd_1_p5_plus_e2e_counted(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    bullets = "".join(f"- 要点 {i}\n" for i in range(1, 21))
    _write_p2_design(
        td,
        "---\n"
        "phase: P2\n"
        "---\n"
        "\n"
        "候选方案：\n"
        f"{bullets}"
        "\n"
        "gate_commands:\n"
        '  P5: "pytest -q"\n'
        '  P5_e2e: "playwright test"\n',
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert "1 个主命令 + 1 个辅助命令" in result.output
    assert "共 2 条" in result.output
    assert "22 个" not in result.output


def test_g5_cmd_2_single_p5_no_warning(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    bullets = "".join(f"- 要点 {i}\n" for i in range(1, 11))
    _write_p2_design(
        td,
        "---\n"
        "phase: P2\n"
        "---\n"
        "\n"
        f"{bullets}"
        "\n"
        "gate_commands:\n"
        '  P5: "pytest -q"\n',
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert "gate_commands.P5 命令" not in result.output


def test_g5_cmd_3_no_gate_commands_no_warning(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(
        td,
        "---\n" "phase: P2\n" "---\n" "候选方案：无 gate_commands 声明\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert "gate_commands.P5 命令" not in result.output


def test_g5_cmd_4_p6_not_counted_as_p5(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(
        td,
        "---\n"
        "phase: P2\n"
        "---\n"
        "gate_commands:\n"
        '  P5: "pytest -q"\n'
        '  P6: "pytest tests/acceptance"\n',
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert "gate_commands.P5 命令" not in result.output


def test_g5_cmd_5_no_trailing_newline(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text(
        'gate_commands:\n  P5: "pytest"\n  P5_e2e: "playwright"',
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P5", str(td))
    assert result.returncode == 2
    assert "1 个主命令 + 1 个辅助命令" in result.output
    assert "共 2 条" in result.output


# ========== 8d: gate_p6 分支（G6 系列 + G_BDD16.1）+ TAG0002 refactor 口径（test_bdd_1..8） ==========
# P6-acceptance.md 用 write_text 覆写（等价 bats heredoc）；P6-evidence/ 目录存在性
# 由 gate_p6 判定（G6.4 断言其缺失）。refactor 系列用 add_p1_field 写 P1 frontmatter
# change_type（NO_FALLBACK_STRING_FIELDS，仅 frontmatter 生效）。


def _write_p6_acceptance(td, body):
    (td / "P6-acceptance.md").write_text(body, encoding="utf-8")


def _add_p6_evidence(td, filename, content="log\n"):
    (td / "P6-evidence").mkdir(parents=True, exist_ok=True)
    (td / "P6-evidence" / filename).write_text(content, encoding="utf-8")


_P6_REGRESSION_BODY = (
    "---\n"
    "phase: P6\n"
    "task_id: TAG0002\n"
    "agent: verifier\n"
    "pass: 1\n"
    "fail: 0\n"
    "ui_affected: false\n"
    "regression_pass: true\n"
    "---\n"
    "- PASS BDD-1: 全量回归全绿（重构后完整测试套件 0 失败）(P6-evidence/regression.log)\n"
)


def test_g6_1_fail_line_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- FAIL BDD-2\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "FAIL=" in result.output


def test_g6_3_all_pass_no_bdd_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6_acceptance(td, "无 BDD 条目\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "TOTAL=0" in result.output


def test_g6_4_no_evidence_dir_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- PASS BDD-2\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "P6-evidence" in result.output


def test_g6_5_evidence_nonempty_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- PASS BDD-2\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_g6_10_need_confirm_not_blocking_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- [NEED_CONFIRM] some text\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_g6_11_no_need_confirm_no_warning_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1 (result.log)\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2
    assert "NEED_CONFIRM" not in result.output


def test_g6_7_lowercase_fail_counted_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- fail: BDD-2 broken\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "FAIL=1" in result.output


def test_bdd16_1_frontmatter_summary_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6_acceptance(
        td,
        "---\n"
        "phase: P6\n"
        "task_id: T001\n"
        "agent: verifier\n"
        "pass: 1\n"
        "fail: 0\n"
        "ui_affected: false\n"
        "---\n"
        "逐条结果见 P6-evidence/ 详细记录（本文件正文不复述逐条 PASS/FAIL 行）。\n",
    )
    _add_p6_evidence(td, "result.json")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_g6_9_failure_not_counted_exit_2(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- failure mode detected\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2
    assert "FAIL=0" in result.output


def test_bdd_1_p1_gate_accepts_refactor_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    (td / "P1-review.md").write_text(
        "---\n"
        "status: approved\n"
        "agent: requirements-review\n"
        "---\n"
        "## BDD 评审\n"
        "- BDD-1: PASS\n",
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2
    assert "change_type" not in result.output


def test_bdd_2_p6_default_no_change_type_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6_acceptance(td, "- PASS BDD-1\n- PASS BDD-2\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_bdd_2b_p6_body_mentions_change_type_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    with open(td / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write(
            "\nchange_type: refactor 是可选字段，缺省为功能任务（本文档仅作说明，本任务不采用 refactor 口径）\n"
        )
    _write_p6_acceptance(td, "- PASS BDD-1\n- PASS BDD-2\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_bdd_3_p6_refactor_with_regression_evidence_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    _write_p6_acceptance(td, _P6_REGRESSION_BODY)
    _add_p6_evidence(td, "regression.log", "bats ... 0 failures\nEXIT_CODE: 0\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_bdd_4_p6_refactor_missing_regression_log_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    _write_p6_acceptance(td, _P6_REGRESSION_BODY)
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "regression.log" in result.output


def test_bdd_4b_p6_refactor_missing_regression_pass_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    _write_p6_acceptance(
        td,
        "---\n"
        "phase: P6\n"
        "task_id: TAG0002\n"
        "agent: verifier\n"
        "pass: 1\n"
        "fail: 0\n"
        "ui_affected: false\n"
        "---\n"
        "- PASS BDD-1: 全量回归全绿（重构后完整测试套件 0 失败）(P6-evidence/regression.log)\n",
    )
    _add_p6_evidence(td, "regression.log", "bats ... 0 failures\nEXIT_CODE: 0\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1
    assert "regression_pass" in result.output


def test_bdd_6_p6_no_behavior_change_not_waived_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    with open(td / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write("\nno_behavior_change: 预期无行为变更\n")
    _write_p6_acceptance(td, _P6_REGRESSION_BODY)
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 1


def test_bdd_6b_p6_no_behavior_change_with_evidence_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    with open(td / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write("\nno_behavior_change: 预期无行为变更\n")
    _write_p6_acceptance(td, _P6_REGRESSION_BODY)
    _add_p6_evidence(td, "regression.log", "bats ... 0 failures\nEXIT_CODE: 0\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_bdd_7_refactor_backfill_walk_p1_p3_p6(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    with open(td / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write(
            "\n#### BDD-2: 关键路径行为不变\n"
            "- Given 重构后的协议状态\n"
            "- When 执行关键路径\n"
            "- Then 行为与重构前一致\n"
        )
    (td / "P1-review.md").write_text(
        "---\n"
        "status: approved\n"
        "agent: requirements-review\n"
        "---\n"
        "## BDD 评审\n"
        "- BDD-1: PASS\n"
        "- BDD-2: PASS\n",
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2

    (td / "P3-test-cases.md").write_text(
        "## P3 test cases（回归测试口径，不新增功能行为断言）\n", encoding="utf-8"
    )
    result = _run_gate(agate_scripts, python_exe, run_cli, "P3", str(td))
    assert result.returncode == 2

    _write_p6_acceptance(
        td,
        "---\n"
        "phase: P6\n"
        "task_id: TAG0002\n"
        "agent: verifier\n"
        "pass: 2\n"
        "fail: 0\n"
        "ui_affected: false\n"
        "regression_pass: true\n"
        "---\n"
        "- PASS BDD-1: 全量回归全绿（重构后完整测试套件 0 失败）(P6-evidence/regression.log)\n"
        "- PASS BDD-2: 关键路径行为不变（重构前后关键路径结果一致）(P6-evidence/regression.log)\n",
    )
    _add_p6_evidence(td, "regression.log", "bats ... 0 failures\nEXIT_CODE: 0\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


def test_bdd_5_p6_card_docs_forbid_fake_bdd(agate_root):
    content = (agate_root / "phase-cards" / "P6-acceptance.md").read_text(encoding="utf-8")
    assert re.search(r"禁止.*伪造", content)


def test_bdd_8_p3_card_docs_regression_test_port(agate_root):
    content = (agate_root / "phase-cards" / "P3-tdd.md").read_text(encoding="utf-8")
    assert "回归测试口径" in content


# ========== 8e: gate_p7 分支（G7.1-9 + G_DG_ANCHOR.1/2 + bdd-11，12 用例） ==========
# P7-consistency.md 用 write_text 覆写（等价 bats heredoc）。gate_p7 输出
# （GATE P7: ... / GATE P7 WARNING / WARNING P7）一律 sys.stderr.write → 断言合并流
# result.output（P2 §3.2 流语义规则，BLOCKER-1）。
# bdd-11 需 env LC_ALL=C LANG=（M4 全角冒号总结行），经 _run_gate env= 透传 run_cli。


def _write_p7(td, body):
    (td / "P7-consistency.md").write_text(body, encoding="utf-8")


def test_g7_1_blocker_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [BLOCKER] arch flaw\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "BLOCKER=" in result.output


def test_g7_2_deviation_critical_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [DEVIATION-CRITICAL] ui break\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "DEVIATION-CRITICAL=" in result.output


def test_g7_3_design_gap_unpaired_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [DESIGN_GAP: P2 未指定错误处理]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "DESIGN_GAP" in result.output
    assert "未配对" in result.output


def test_g7_4_design_gap_paired_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [DESIGN_GAP: P2 未指定错误处理]\n- [DESIGN_GAP_REVIEWED: 已确认]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0


def test_g7_5_two_gaps_one_reviewed_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [DESIGN_GAP: A]\n- [DESIGN_GAP: B]\n- [DESIGN_GAP_REVIEWED: A 已确认]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1


def test_g7_6_empty_file_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0


def test_g7_7_p4_gap_not_copied_to_p7_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n- [DESIGN_GAP: P2 未指定错误处理]\n",
        encoding="utf-8",
    )
    _write_p7(td, "---\nagent: test\n---\n一致性检查完成。\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "P4" in result.output
    assert "DESIGN_GAP" in result.output
    assert "P7" in result.output


def test_g7_8_blocker_zero_declared_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p7(td, "- [BLOCKER]: 0 条\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0


def test_g7_9_blocker_zero_plus_real_blocker_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p7(td, "- [BLOCKER]: 0 条\n- [BLOCKER] arch flaw\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "BLOCKER=" in result.output


def test_dg_anchor_1_inline_gap_not_counted_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p7(td, "# P7 一致性检查\n检查了 [DESIGN_GAP: xxx] 的引用\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0


def test_dg_anchor_2_bol_gap_counted_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p7(td, "# P7 一致性检查\n- [DESIGN_GAP: xxx] 未配对\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "DESIGN_GAP" in result.output


def test_bdd_11_fullwidth_colon_blocker_summary_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p7(td, "- [BLOCKER]：3 条\n")

    result = _run_gate(
        agate_scripts,
        python_exe,
        run_cli,
        "P7",
        str(td),
        env={"LC_ALL": "C", "LANG": ""},
    )
    assert result.returncode == 0


# ========== 8f: gate_p8 分支（G8.1-10，10 用例） ==========
# P8 检查在 git repo 内进行：_init_repo_with_task 复制 task 目录后，写
# version/CHANGELOG 文件并 stage（bats `git -C "$repo" add ...` 等价），
# run_cli(..., cwd=repo) 等价 bats `cd '$repo' && ...`。P8 输出（GATE P8: /
# GATE P8 WARNING:）一律 sys.stderr.write → 断言合并流 result.output
# （P2 §3.2 流语义规则，BLOCKER-1）。G8.5 无 P8 文件分支不需要 git repo
# （bump_type 缺失提前 return 1，gate_p8 不触达 git 检查）。
# G8.6 用 env CHANGELOG_FILE=HISTORY.md 覆盖默认 CHANGELOG.md（bats
# `CHANGELOG_FILE="HISTORY.md" run bash -c ...` 等价）。


def _write_p8_release(td, body):
    (td / "P8-release.md").write_text(body, encoding="utf-8")


def _init_p8_repo(git_repo, td, files=None, tag=None):
    """bats G8 系列 git 前置等价：init + README commit + cp task + 写/暂存文件 + 可选 tag。"""
    repo = git_repo.path
    _init_repo_with_task(git_repo, td)
    for name, content in (files or {}).items():
        (repo / name).write_text(content, encoding="utf-8")
        git_repo.stage(name)
    if tag:
        git_repo.git("tag", tag)
    return repo


_P8_COMPLIANT = "bump_type: minor\ndebt_check: none\n"
_P8_UNRELEASED = "## [Unreleased]\n"
_P8_CHANGELOG_TAGGED = "## [Unreleased]\n\n## [0.2.0] - 2026-07-20\n"


def test_g8_1_missing_bump_type_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, "无 bump_type\n")
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "bump_type" in result.output


def test_g8_2_no_version_change_warning_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"some.md": "doc\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "WARNING" in result.output
    assert "version" in result.output


def test_g8_3_version_changed_no_changelog_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo, td, files={"package.json": "v0.1.0\n"}
    )  # CHANGELOG 没改 → WARNING

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "CHANGELOG" in result.output


def test_g8_4_full_compliance_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2


def test_g8_5_missing_p8_file_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir(phases=["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"])  # P8 不在

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", str(td))
    assert result.returncode == 1


def test_g8_6_changelog_file_env_override(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "HISTORY.md": _P8_UNRELEASED},
    )

    result = _run_gate(
        agate_scripts,
        python_exe,
        run_cli,
        "P8",
        "task",
        cwd=str(repo),
        env={"CHANGELOG_FILE": "HISTORY.md"},
    )
    assert result.returncode == 2


def test_g8_7_tag_missing_warning_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_CHANGELOG_TAGGED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "tag v0.2.0 不存在" in result.output


def test_g8_8_tag_exists_no_warning(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.2.0\n", "CHANGELOG.md": _P8_CHANGELOG_TAGGED},
        tag="v0.2.0",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "tag v0.2.0 不存在" not in result.output


def test_g8_9_missing_debt_check_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, "bump_type: minor\n")
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "debt_check" in result.output


def test_g8_10_debt_check_any_content_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "debt_check" not in result.output


# ========== TAG0023 RM-AG0043（BDD-5~7）：P8 roadmap 回写 done 校验 ==========
# 被测：check-gate.py gate_p8() 新增分支 _check_roadmap_done()（P2-design.md §2.2 候选 A，
#   尚未实现——gate_p8() 全函数目前无任何 roadmap.md 读取，这是本批红灯的来源）。
# 匹配算法（P2-design.md §2.2 D2）：按 task_id 精确匹配 roadmap.md「关联任务」列，全部
# 匹配行状态须为 done；无匹配行不误拦，继续走既有流程（最终 return 2，非新增的 exit 0）。


def _write_roadmap(repo, rows):
    """写 repo/agate-workspace/roadmap/roadmap.md（列顺序对齐真实文件：
    id|标题|状态|来源|关联任务|创建|更新）。rows 为 (id, status, task_id) 元组列表。"""
    roadmap_dir = repo / "agate-workspace" / "roadmap"
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |",
        "|----|------|------|------|----------|------|------|",
    ]
    for rm_id, status, task_id in rows:
        lines.append(
            f"| {rm_id} | 测试条目 | {status} | 测试 | {task_id} | 2026-08-24 | 2026-08-24 |"
        )
    (roadmap_dir / "roadmap.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_bdd_5_p8_roadmap_rm_not_done_blocked_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-5：task_id（默认 T001，create_task_dir 缺省值）在 roadmap.md 有关联 RM 记录且
    状态非 done → gate_p8() 阻断 exit 1，stderr 含该 RM 编号。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap(repo, [("RM-TEST01", "backlog", "T001")])

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "RM-TEST01" in result.output


def test_bdd_6_p8_roadmap_no_matching_rm_not_blocked_exit_2(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6 回归防呆：roadmap.md 存在记录但「关联任务」不等于当前 task_id（无匹配行）→
    不误拦，gate_p8() 继续既有流程最终 return 2（P2-design.md §4 完成标准表判据，非 exit 0）。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap(repo, [("RM-TEST02", "backlog", "TAG0999")])

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2


def test_bdd_7_roadmap_rm_ag0032_backfilled_done(agate_root):
    """BDD-7（历史修正，独立 BDD）：roadmap.md 中 RM-AG0032 当前两行状态为
    backlog/scheduled，均非 done（v0.59.0 已发布、PR #184 已合并，属记录缺口）。
    P8 阶段主 Agent 人工补记一行 done 状态后本用例才转绿；当前红灯反映补记尚未发生。"""
    roadmap_path = agate_root.parent / "agate-workspace" / "roadmap" / "roadmap.md"
    text = roadmap_path.read_text(encoding="utf-8")
    done_lines = [
        line
        for line in text.splitlines()
        if "RM-AG0032" in line and re.search(r"\|\s*done\s*\|", line)
    ]
    assert done_lines, "RM-AG0032 尚无 done 行记录（P8 阶段待人工补记，P2-design.md §2.2 末）"


# ========== TAG0024 DEBT0019/DEBT0020（BDD-20~24）：roadmap.md 列数完整性 + 仓库根锚定 ==========
# 被测：check-gate.py _check_roadmap_done()（现 len(cols) < 8 宽松判据 → 精确匹配
#   len(cols) != _ROADMAP_EXPECTED_COLS(=9)，P2-design.md §3.6）+ gate_p8() 的
#   roadmap_path 构造（现 CWD 相对 os.path.join("agate-workspace", ...) → git
#   rev-parse --show-toplevel 仓库根锚定，P2-design.md §3.7）。
# BDD-20/22/23 断言"修复后行为"，在当前未修复实现下应真实失败（TDD 红灯）；
# BDD-21/24 是既有合法场景的回归防呆（列数恰为 9 / CWD=仓库根本就是既有唯一调用路径），
# 修复前后判定结果应保持一致，不要求本身处于红灯（复用/参照 test_bdd_5/6/7 风格）。


def _write_roadmap_raw(repo, lines):
    """写 repo/agate-workspace/roadmap/roadmap.md 为给定原始行（不做列格式化）；
    供 BDD-20 构造含字面 `|` 的畸形行场景使用（_write_roadmap 只能生成规整 9 列行）。"""
    roadmap_dir = repo / "agate-workspace" / "roadmap"
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    (roadmap_dir / "roadmap.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_bdd_20_p8_roadmap_literal_pipe_in_title_not_misjudged(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-20：标题列含字面 `|`（"测试|条目"）导致 split("|") 产生 10 列（>= 8 但 != 9）。
    现有 `len(cols) < 8` 宽松判据不会跳过该行，错位取值后 cols[1]="RM-TEST20"（凑巧未变）、
    cols[3]="条目"（本应是 status="done"，被错位）、cols[5]="T001"（本应是"来源"列内容，
    这里刻意把来源列写成默认 task_id "T001" 以命中错位取值误判场景）——现有实现据此误判
    "关联记录状态非 done" 并阻断（exit 1）。修复后按精确列数 9 匹配，该行应被整行跳过，
    不产生任何取值，gate_p8() 不因此行阻断（exit 2，输出不含 RM-TEST20）。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap_raw(
        repo,
        [
            "| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |",
            "|----|------|------|------|----------|------|------|",
            "| RM-TEST20 | 测试|条目 | done | T001 | TAG0999 | 2026-08-24 | 2026-08-24 |",
        ],
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 2
    assert "RM-TEST20" not in result.output


@pytest.mark.parametrize(
    "status,related_task,expected_exit,rm_in_output",
    [
        pytest.param("backlog", "T001", 1, True, id="not_done_matched_blocked"),
        pytest.param("backlog", "TAG0999", 2, False, id="no_matching_row_not_blocked"),
        pytest.param("done", "T001", 2, False, id="done_matched_not_blocked"),
    ],
)
def test_bdd_21_regression_existing_valid_roadmap_unchanged(
    git_repo,
    task_dir,
    agate_scripts,
    python_exe,
    run_cli,
    status,
    related_task,
    expected_exit,
    rm_in_output,
):
    """BDD-21（回归，对应 test_bdd_5/6/7 三场景）：列数恰为精确 9 列的既有合法
    roadmap.md，DEBT0019 列数精确匹配修复（`!= 9` 替换 `< 8`）不改变其判定结果——
    三个规整场景（非 done 且匹配阻断 / 无匹配行不阻断 / done 且匹配不阻断）在修复前后
    完全一致。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap(repo, [("RM-TESTR1", status, related_task)])

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == expected_exit
    assert ("RM-TESTR1" in result.output) == rm_in_output


def test_bdd_22_p8_non_root_cwd_locates_roadmap(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-22：CWD 不是仓库根（本用例取 repo/task 子目录）。现有实现用
    os.path.join("agate-workspace", "roadmap", "roadmap.md") 相对 CWD 拼接，非根 CWD 下
    永远拼不到真实文件（_check_roadmap_done 静默返回 None，不阻断）。修复后改用 git
    rev-parse --show-toplevel 解析仓库根再拼接，应能在非根 CWD 下仍正确定位到
    roadmap.md 并执行状态检查——roadmap.md 含匹配当前 task_id 且非 done 的记录时应阻断
    （exit 1，输出含 RM 编号）。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap(repo, [("RM-TEST22", "backlog", "T001")])

    result = _run_gate(
        agate_scripts, python_exe, run_cli, "P8", ".", cwd=str(repo / "task")
    )
    assert result.returncode == 1
    assert "RM-TEST22" in result.output


def test_bdd_23_p8_repo_root_unavailable_distinct_warning(
    task_dir, agate_scripts, python_exe, run_cli, tmp_path
):
    """BDD-23：仓库根路径无法确定（非 git 仓库环境）时，gate_p8() 应输出区分性 stderr
    提示（说明"仓库根不可得"），而非现有实现的静默跳过（CWD 相对路径拼接找不到文件，
    _check_roadmap_done 静默返回 None，无任何提示）。用 GIT_CEILING_DIRECTORIES 把
    cwd 的父目录设为搜索边界，阻止 git 向上穿越找到外层（本 worktree）仓库，从而在
    cwd 本身无 .git 的前提下真实模拟"仓库根不可得"。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    non_git_cwd = tmp_path / "non_git_cwd"
    non_git_cwd.mkdir()

    result = _run_gate(
        agate_scripts,
        python_exe,
        run_cli,
        "P8",
        str(td),
        cwd=str(non_git_cwd),
        env={"GIT_CEILING_DIRECTORIES": str(tmp_path)},
    )
    assert "仓库根不可得" in result.output


def test_bdd_24_regression_existing_repo_root_cwd_unchanged(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-24（回归，与 BDD-21 对称）：CWD=仓库根是既有唯一调用路径（既有
    test_bdd_5/6/7 均在 cwd=str(repo) 下运行）。DEBT0020 仓库根锚定修复（改用 git
    rev-parse --show-toplevel）在 CWD 恰为仓库根时，解析结果与既有 CWD 相对拼接完全
    等价——判定结果（阻断行为/rm_id/status）保持不变。"""
    td = task_dir()
    _write_p8_release(td, _P8_COMPLIANT)
    repo = _init_p8_repo(
        git_repo,
        td,
        files={"package.json": "v0.1.0\n", "CHANGELOG.md": _P8_UNRELEASED},
    )
    _write_roadmap(repo, [("RM-TESTR4", "backlog", "T001")])

    result = _run_gate(agate_scripts, python_exe, run_cli, "P8", "task", cwd=str(repo))
    assert result.returncode == 1
    assert "RM-TESTR4" in result.output


# ========== 8g: G_RETREAT / G_NC_BINARY / G_SUGGEST（15 用例） ==========
# 子批 8g 覆盖 check-gate.bats 的 G_RETREAT.1-6（回退抵达检测，main() 可选第 3 参数
# OLD_PHASE）、G_NC_BINARY.1/2/3/5/6（P1 NEED_CONFIRM 三值分级）与 G_SUGGEST.1-4
# （SUGGEST 不阻塞 / typo 兜底）。
# G_RETREAT 系列：bats 用 `mkdir -p "$BATS_TEST_TMPDIR/g_retreatN"` 建空目录（非
# create_task_dir）→ pytest 用 tmp_path 建空目录；G_RETREAT.5 额外 git init + cwd
# （gate_p4 检查暂存区代码文件，空暂存区 exit 1）。
# G_NC_BINARY / G_SUGGEST 系列：bats 用 create_task_dir --no-state-yaml + heredoc
# 覆写 P1-requirements.md / P1-review.md → pytest 用 task_dir(no_state_yaml=True) +
# write_text 覆写。GATE P1 输出一律 sys.stderr.write → 断言合并流 result.output
# （P2 §3.2 流语义规则，BLOCKER-1）。


def test_g_retreat_1_no_old_phase_exit_1(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "g_retreat1"
    td.mkdir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1


def test_g_retreat_2_old_phase_p2_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "g_retreat2"
    td.mkdir()

    result = _run_gate(
        agate_scripts, python_exe, run_cli, "P1", str(td), old_phase="P2"
    )
    assert result.returncode == 2
    assert "回退抵达" in result.output


def test_g_retreat_3_old_phase_p6_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "g_retreat3"
    td.mkdir()

    result = _run_gate(
        agate_scripts, python_exe, run_cli, "P4", str(td), old_phase="P6"
    )
    assert result.returncode == 2
    assert "回退抵达" in result.output


def test_g_retreat_4_old_phase_p7_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "g_retreat4"
    td.mkdir()

    result = _run_gate(
        agate_scripts, python_exe, run_cli, "P6", str(td), old_phase="P7"
    )
    assert result.returncode == 2


def test_g_retreat_5_old_phase_p3_forward_exit_1(
    git_repo, agate_scripts, python_exe, run_cli
):
    # 正常推进方向（P4 ← P3，非回退）：暂存区无代码文件 → 仍 exit 1
    repo = git_repo.path

    result = _run_gate(
        agate_scripts,
        python_exe,
        run_cli,
        "P4",
        str(repo),
        cwd=str(repo),
        old_phase="P3",
    )
    assert result.returncode == 1


def test_g_retreat_6_same_phase_not_retreat_exit_1(
    tmp_path, agate_scripts, python_exe, run_cli
):
    td = tmp_path / "g_retreat6"
    td.mkdir()

    result = _run_gate(
        agate_scripts, python_exe, run_cli, "P1", str(td), old_phase="P1"
    )
    assert result.returncode == 1
    assert "回退抵达" not in result.output


_P1_MARKER_HEAD = (
    "---\n"
    "phase: P1\n"
    "task_id: T001-test\n"
    "status: draft\n"
    "agent: analyst\n"
    "---\n"
    "# Requirements\n"
    "- Given x When y Then z\n"
)

_P1_MARKER_REVIEW = (
    "---\n"
    "phase: P1\n"
    "task_id: T001-test\n"
    "status: approved\n"
    "agent: requirements-review\n"
    "---\n"
    "## BDD 评审\n"
    "- BDD-1: PASS\n"
)


def _write_p1_marker_task(td, req_body):
    (td / "P1-requirements.md").write_text(req_body, encoding="utf-8")
    (td / "P1-review.md").write_text(_P1_MARKER_REVIEW, encoding="utf-8")


def test_g_nc_binary_1_no_need_confirm_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_MARKER_HEAD + "- [NO_NEED_CONFIRM]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2


def test_g_nc_binary_2_need_confirm_bol_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td, _P1_MARKER_HEAD + "- [NEED_CONFIRM] z 的边界条件需确认\n"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "NEED_CONFIRM" in result.output


def test_g_nc_binary_3_inline_ref_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_MARKER_HEAD + "无 [NEED_CONFIRM] 需要确认\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "不合规" in result.output


def test_g_nc_binary_5_no_declaration_warning_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_MARKER_HEAD)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2
    assert "WARNING" in result.output


def test_g_nc_binary_6_no_need_confirm_with_desc_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td, _P1_MARKER_HEAD + "- [NO_NEED_CONFIRM] 确认无不可逆操作\n"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2


def test_g_suggest_1_suggest_no_blocker_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td, _P1_MARKER_HEAD + "- [SUGGEST: 推荐方案 A，理由是更安全]\n"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2
    assert "SUGGEST" in result.output
    assert "未解决的 NEED_CONFIRM 项（阻塞）" not in result.output


def test_g_suggest_2_suggest_plus_need_confirm_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td,
        _P1_MARKER_HEAD
        + "- [SUGGEST: 推荐方案 A，理由是更安全]\n"
        + "- [NEED_CONFIRM] 需用户决策的方向\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "阻塞" in result.output


def test_g_suggest_3_old_marker_rename_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_MARKER_HEAD + "- [NEED_CONFIRM倾向: 推荐方案 A]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "重命名为" in result.output


def test_g_suggest_4_missing_colon_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_MARKER_HEAD + "- [SUGGEST xxx]\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "SUGGEST 格式不符" in result.output


# ========== 8h: D-drift / G-drift / TAG0005 BDD（16 用例） ==========
# 子批 8h 覆盖 check-gate.bats 的文档/协议漂移守护用例（bats `grep -q ...` 等价，
# 非 run_cli）：D-drift-1/2/4/4b/5/6（dispatch 模板关键词）+ G-drift-1/2/3
# （dispatch-protocol 关键词 + implementer/verifier 反例）+ TAG0005 BDD-1/2/9/12/13/14/15
# （role-system / check-gate.py / dispatch-protocol 文档锚点 + scripts 扫描）。
# 等价映射：grep -q 'X' FILE → 读文件 text + `assert "X" in text`；`! grep -q` →
# `assert "X" not in text`；`grep -rl ... --include='*.md'` → rglob 收集 + 单文件断言；
# `grep -rnE '>&2;\s*exit 0' scripts/*.sh` → 逐行正则 + 每命中行必须含「跳过」。
# 全走 agate_root fixture（等价 $AGATE_ROOT），所有 read_text 显式 encoding="utf-8"
# （BDD-7）。此批无 create_task_dir / git_repo 依赖，纯文件内容断言。


def _read_text(path):
    return path.read_text(encoding="utf-8")


def test_drift_1_dispatch_prompt_contains_return_self_check(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-prompt.md")
    assert "返回前自检" in content


def test_drift_2_dispatch_prompt_contains_files_modified(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-prompt.md")
    assert "files_modified" in content


def test_drift_4_dispatch_context_xml_guide_sections(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-context.md")
    assert "<dispatch_guide>" in content
    assert "### 目标" in content
    assert "### 约束" in content


def test_drift_4b_dispatch_context_xml_markers(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-context.md")
    assert "<dispatch_guide>" in content
    assert "<objective_info>" in content


def test_drift_5_dispatch_prompt_contains_p3_self_check(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-prompt.md")
    assert "P3 自检" in content


def test_drift_6_dispatch_prompt_contains_fix_round_dispatch(agate_root):
    content = _read_text(agate_root / "assets/templates/dispatch-prompt.md")
    assert "修复轮派发追加" in content


def test_drift_g1_dispatch_protocol_self_check_neq_gate(agate_root):
    content = _read_text(agate_root / "dispatch-protocol.md")
    assert "自查≠gate" in content


def test_drift_g2_implementer_no_write_run_separation(agate_root):
    content = _read_text(agate_root / "assets/execution-roles/implementer.md")
    assert "写跑分离" not in content


def test_drift_g3_verifier_no_write_run_separation(agate_root):
    content = _read_text(agate_root / "assets/execution-roles/verifier.md")
    assert "写跑分离" not in content


def test_tag0005_bdd_1_backend_rows_plan_eng_review(agate_root):
    for rel in ("role-system.md", "rules/review-mapping.md", "phase-cards/P2-design.md"):
        content = _read_text(agate_root / rel)
        assert re.search(r"^\| backend \|.*plan-eng-review", content, re.M)


def test_tag0005_bdd_2_p2_review_unconditional_gate(agate_root):
    content = _read_text(agate_root / "scripts/check-gate.py")
    assert "P2-review.md 不存在（P2 评审不可裁剪" in content
    assert "P2-review.md frontmatter status 非 approved" in content


def test_tag0005_bdd_9_review_role_instruction_single_file(agate_root, tmp_path_factory):
    # TAG0022 RM-AG0041（P5→P4 回退修复轮）：basetemp 位置无关——pytest basetemp 位于
    # 协议目录内时（如 agate/.bt-fix），同会话其他测试渲染的 dispatch-prompt .md 产物
    # 会被 rglob 全树扫描误收；排除 basetemp 子树后断言协议目录内「Review 角色特别指令」
    # 恰 1 处（dispatch-prompt.md 模板），断言语义不变（P5 verifier 实测，unit.md 记录）。
    basetemp = Path(tmp_path_factory.getbasetemp())
    hits = []
    for p in agate_root.rglob("*.md"):
        try:
            p.relative_to(basetemp)
        except ValueError:
            if "Review 角色特别指令" in _read_text(p):
                hits.append(p)
    assert len(hits) == 1
    assert "assets/templates/dispatch-prompt.md" in str(hits[0])


def test_tag0005_bdd_12_empty_return_auto_retry_once(agate_root):
    content = _read_text(agate_root / "dispatch-protocol.md")
    assert "自动重试一次" in content


def test_tag0005_bdd_13_short_session_warning(agate_root):
    content = _read_text(agate_root / "dispatch-protocol.md")
    assert "会话时长异常短" in content
    assert "<1min" in content


def test_tag0005_bdd_14_retry_paused_unchanged(agate_root):
    content = _read_text(agate_root / "dispatch-protocol.md")
    assert "MAX_RETRY" in content
    assert "PAUSED 报告人工" in content


def test_tag0005_bdd_15_scripts_stderr_exit0_only_skip_semantics(agate_root):
    pattern = re.compile(r">&2;\s*exit 0")
    for sh in (agate_root / "scripts").glob("*.sh"):
        for line in _read_text(sh).splitlines():
            if pattern.search(line):
                assert "跳过" in line


# ========== 批次 8 补遗：PG.P2REVIEW / bdd-14 / bdd-28 / bdd-29（4 用例） ==========
# 8a-8h 按 P2 §5 子批表非穷举分区（`-k`）迁移后整文件核对，check-gate.bats 剩余 4 个
# @test（PG.P2REVIEW / bdd-14 / bdd-28 / bdd-29）此前未入 pytest（8h 偏离点已记录）。
# 本补遗补齐：PG.P2REVIEW = P2-review.md 不存在（exit 1，与 G2.13 差异在断言子串
# "P2-review.md 不存在"）；bdd-14 = P1 CRLF 行尾 frontmatter 提取（M6，exit 2，bats
# printf 写 CRLF 文本）；bdd-28/bdd-29 = 反引号包裹 [SUGGEST:]/[NEED_CONFIRM] 标记
# 仍被识别（RM-AG0001）。复用 8b `_P2_TWO_CAND_BODY` / `add_p2_candidate_count` 与
# 8g `_P1_MARKER_HEAD` / `_P1_MARKER_REVIEW` / `_write_p1_marker_task`。
# bdd-14 名称含平台关键词 CRLF → 按 P2 §5.2 加 @pytest.mark.windows_smoke（Windows
# checkout 的 CRLF review 文件是该用例验证的机制本身）。


def test_pg_p2review_not_found_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "P2-review.md 不存在" in result.output


@pytest.mark.windows_smoke
def test_bdd14_crlf_review_frontmatter_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    (td / "P1-review.md").write_text(
        "---\r\nphase: P1\r\ntask_id: T001-test\r\nstatus: approved\r\n"
        "agent: requirements-review\r\n---\r\n## BDD 评审\r\n- BDD-1: PASS\r\n",
        encoding="utf-8",
    )
    (td / "P1-requirements.md").write_text(
        "---\r\nagent: test\r\nrisk_level: medium\r\n"
        "phases: [P1,P2,P3,P4,P5,P6,P7,P8]\r\n---\r\n- [NO_NEED_CONFIRM]\r\n",
        encoding="utf-8",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2


def test_bdd28_backtick_suggest_warning_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td,
        _P1_MARKER_HEAD
        + "- [NO_NEED_CONFIRM]\n"
        + "- `[SUGGEST: 推荐 X，理由 Y]`\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2
    assert "SUGGEST" in result.output


def test_bdd29_backtick_need_confirm_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(
        td, _P1_MARKER_HEAD + "- `[NEED_CONFIRM]` z 的边界条件需确认\n"
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1
    assert "未解决的 NEED_CONFIRM" in result.output


# ========== 8i: TAG0006 UI/UX 机制——gate_p1 vision 三态 / 形态声明 + gate_p2 UI 设计节 ==========
# 新增检查（P4 实现后挂载于 check-gate.py）：
#   gate_p1：_gate_p1_vision_capability（domains 含 frontend → capability_requirements 视觉条目
#            三态必填，缺失/非法 status → exit 1，BDD-3）+ _gate_p1_ui_shape
#            （ui_render_shape/ui_ux_dimensions 声明合法性，BDD-16，§2.15.4）
#   gate_p2：_gate_p2_ui_design_section（ui_affected:true → ## UI 设计 节 + 形态声明 +
#            按形态 checklist + P1-P2 形态一致性交叉校验（规范值/同义映射归一化比对），BDD-4）
# P1 夹具复用 8g _P1_MARKER_HEAD/_P1_MARKER_REVIEW/_write_p1_marker_task；
# P2 夹具复用 8b _write_p2_design/add_p2_candidate_count/add_p2_review。
# 基准退出码：P1=2（approved + agent≠main + BDD 锚点）、P2=2（四字段 + 2 候选 + 权衡 + review）。
# 红绿灯语义：🔴 用例在 P4 前失败 = 新检查未实现（assertion 失败 B 类）；
#   🟢 用例为兼容回归/新行为正例（既有行为即期望行为，负分支由配对红灯用例承担）。

_P1_UI_BASE = _P1_MARKER_HEAD + "- [NO_NEED_CONFIRM]\n"


def _append_p1_capability(td, status):
    """P1 body 追加 capability_requirements yaml 代码围栏块（视觉条目 + 三态 status）。"""
    with (td / "P1-requirements.md").open("a", encoding="utf-8") as fh:
        fh.write(
            "\n```yaml\n"
            "capability_requirements:\n"
            "  - need: visual-analysis\n"
            f"    status: {status}\n"
            "```\n"
        )


def _run_p1_ui_ctx(
    task_dir,
    agate_scripts,
    python_exe,
    run_cli,
    domains="[frontend]",
    status="available",
    shape=None,
    dims=None,
    ext_bdd=None,
):
    """构造带 UI 语境（domains/形态字段/capability）的 P1 并跑 gate P1。

    status=None 表示不写能力声明（BDD-3 缺失场景）；shape/dims 控制形态声明字段。
    ext_bdd 非空时在 P1 body 追加含该词条的 UX 类别 BDD 标题（BDD-16 扩展维度已声明运用）。
    """
    td = task_dir(no_state_yaml=True)
    _write_p1_marker_task(td, _P1_UI_BASE)
    if domains:
        add_p1_field(td, "domains", domains)
    if shape is not None:
        add_p1_field(td, "ui_render_shape", shape)
    if dims is not None:
        add_p1_field(td, "ui_ux_dimensions", dims)
    if status is not None:
        _append_p1_capability(td, status)
    if ext_bdd:
        with (td / "P1-requirements.md").open("a", encoding="utf-8") as fh:
            fh.write(f"\n#### BDD-9: 渲染正确性：{ext_bdd}\n- Given x\n- When y\n- Then z\n")
    return _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))


def test_vision_1_frontend_missing_capability_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(task_dir, agate_scripts, python_exe, run_cli, status=None)
    assert result.returncode == 1
    assert "vision" in result.output


def test_vision_2_frontend_invalid_status_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir, agate_scripts, python_exe, run_cli, status="invalid"
    )
    assert result.returncode == 1
    assert "status" in result.output


def test_vision_3_frontend_valid_gap_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(task_dir, agate_scripts, python_exe, run_cli, status="GAP")
    assert result.returncode == 2


def test_vision_4_backend_no_vision_no_fail_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        domains="[backend]",
        status=None,
    )
    assert result.returncode == 2


def test_shape_1_shape_no_dimensions_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        status="available",
        shape="render_component",
        dims="[]",
    )
    assert result.returncode == 1


def test_shape_2_shape_with_valid_dims_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        shape="render_component",
        dims="[渲染正确性]",
    )
    assert result.returncode == 2


def test_shape_2b_shape_missing_dims_present_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        shape=None,
        dims="[渲染正确性]",
    )
    assert result.returncode == 2


def test_shape_3_no_shape_backend_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        domains="[backend]",
        status=None,
        shape=None,
        dims=None,
    )
    assert result.returncode == 2


def test_shape_4_extension_dim_declared_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        shape="render_component",
        dims="[自定义导出能力]",
        ext_bdd="自定义导出能力走参考图对比",
    )
    assert result.returncode == 2


def test_shape_4b_extension_dim_not_declared_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        shape="render_component",
        dims="[自定义导出能力]",
        ext_bdd=None,
    )
    assert result.returncode == 1


def test_shape_5_no_shape_fields_default_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p1_ui_ctx(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        status="available",
        shape=None,
        dims=None,
    )
    assert result.returncode == 2


_UI_P2_BASE = (
    "# P2 design\n"
    "### 候选方案 A：方案一\n"
    "### 候选方案 B：方案二\n"
    "## 权衡\n"
    "A 简单，B 稳健。\n"
    "packages: [pkg-a]\n"
    "domains: [frontend]\n"
    "ui_affected: true\n"
    "gate_commands: {}\n"
)

_UI_SECTION_LAYOUT_FULL = (
    "\n## UI 设计\n"
    "\n"
    "### 渲染形态声明\n"
    "- 渲染形态: layout（布局型）\n"
    "- 适用维度: 布局结构, 交互行为, 视觉呈现\n"
    "\n"
    "### 布局 checklist\n"
    "- [ ] 布局结构/页面分区已描述\n"
    "\n"
    "### 交互 checklist\n"
    "- [ ] 交互行为（键盘可达/输入态反馈）已覆盖\n"
    "\n"
    "### 视觉 checklist\n"
    "- [ ] 视觉呈现（颜色对比/字体层级）已说明\n"
)


def _run_p2_ui_case(
    task_dir, agate_scripts, python_exe, run_cli, section, p1_shape=None
):
    td = task_dir()
    if p1_shape is not None:
        add_p1_field(td, "ui_render_shape", p1_shape)
    _write_p2_design(td, _UI_P2_BASE + section)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)
    return _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))


def test_ui_design_1_ui_true_missing_section_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p2_ui_case(
        task_dir, agate_scripts, python_exe, run_cli, section=""
    )
    assert result.returncode == 1


def test_ui_design_2_ui_true_full_section_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    result = _run_p2_ui_case(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        section=_UI_SECTION_LAYOUT_FULL,
    )
    assert result.returncode == 2


def test_ui_design_3_ui_true_missing_keyword_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: layout（布局型）\n"
        "- 适用维度: 布局结构, 交互行为\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局结构已描述\n"
        "\n"
        "### 交互 checklist\n"
        "- [ ] 交互行为已覆盖\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 1


def test_ui_design_4_ui_false_no_section_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)
    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_ui_design_5_ui_true_render_comp_section_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: render_component（渲染组件型）\n"
        "- 适用维度: 渲染正确性, 动效时序\n"
        "\n"
        "### 渲染正确性 checklist\n"
        "- [ ] 渲染正确性：渲染输出对比参考图，diff 阈值量化\n"
        "\n"
        "### 动效时序 checklist\n"
        "- [ ] 动效时序：帧采样点与关键帧状态\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 2


def test_ui_design_6_ui_true_missing_shape_decl_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局结构已描述\n"
        "\n"
        "### 交互 checklist\n"
        "- [ ] 交互行为已覆盖\n"
        "\n"
        "### 视觉 checklist\n"
        "- [ ] 视觉呈现已说明\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 1


def test_ui_design_7_ui_true_p1_p2_shape_mismatch_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: layout（布局型）\n"
        "- 适用维度: 布局结构, 交互行为, 视觉呈现\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局结构\n"
        "\n"
        "### 交互 checklist\n"
        "- [ ] 交互行为\n"
        "\n"
        "### 视觉 checklist\n"
        "- [ ] 视觉呈现\n"
    )
    result = _run_p2_ui_case(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        section=section,
        p1_shape="render_component",
    )
    assert result.returncode == 1


def test_ui_design_8_ui_true_p1_p2_shape_canonical_match_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: render_component（渲染组件型）\n"
        "- 适用维度: 渲染正确性, 动效时序\n"
        "\n"
        "### 渲染正确性 checklist\n"
        "- [ ] 渲染正确性：渲染结果对比参考图\n"
        "\n"
        "### 动效时序 checklist\n"
        "- [ ] 帧时序采样点\n"
    )
    result = _run_p2_ui_case(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        section=section,
        p1_shape="render_component",
    )
    assert result.returncode == 2


def test_ui_design_9_ui_true_p1_p2_shape_synonym_match_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: 渲染组件型\n"
        "- 适用维度: 渲染正确性, 动效时序\n"
        "\n"
        "### 渲染正确性 checklist\n"
        "- [ ] 渲染正确性：渲染结果对比参考图\n"
        "\n"
        "### 动效时序 checklist\n"
        "- [ ] 帧时序采样点\n"
    )
    result = _run_p2_ui_case(
        task_dir,
        agate_scripts,
        python_exe,
        run_cli,
        section=section,
        p1_shape="render_component",
    )
    assert result.returncode == 2


# TAG0006 修复轮 INFO-1（I1）：维度不适用豁免按"维度"粒度——仅声明"布局不适用"只豁免布局锚点，
# 交互/视觉 仍须各出现关键词（修复前任一"不适用"一刀切豁免全部三维，偏宽松）。
def test_ui_design_10_layout_waived_but_interaction_visual_required_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: layout（布局型）\n"
        "- 适用维度: 布局结构（本维度不适用）\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局不适用\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 1


def test_ui_design_11_all_three_dimensions_waived_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: layout（布局型）\n"
        "- 适用维度: 布局结构, 交互行为, 视觉呈现\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局不适用\n"
        "\n"
        "### 交互 checklist\n"
        "- [ ] 交互不适用\n"
        "\n"
        "### 视觉 checklist\n"
        "- [ ] 视觉不适用\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 2


# TAG0006 修复轮 INFO-2（I2）：UI 设计 节标题改为前缀匹配——标题后附括号说明（如
# "## UI 设计（ui_affected: true 时必含）"）不再误拦（修复前要求 \s*$ 精确结尾）。
def test_ui_design_12_heading_prefix_with_suffix_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    section = (
        "\n## UI 设计（ui_affected: true 时必含本节）\n"
        "\n"
        "### 渲染形态声明\n"
        "- 渲染形态: layout（布局型）\n"
        "- 适用维度: 布局结构, 交互行为, 视觉呈现\n"
        "\n"
        "### 布局 checklist\n"
        "- [ ] 布局结构/页面分区已描述\n"
        "\n"
        "### 交互 checklist\n"
        "- [ ] 交互行为（键盘可达/输入态反馈）已覆盖\n"
        "\n"
        "### 视觉 checklist\n"
        "- [ ] 视觉呈现（颜色对比/字体层级）已说明\n"
    )
    result = _run_p2_ui_case(task_dir, agate_scripts, python_exe, run_cli, section=section)
    assert result.returncode == 2


# ========== 8j: TAG0007 骨架 + CODE-MAP 机制（BDD-1/3/4/7/8/9/10，12 用例） ==========
# 骨架/CODE-MAP 判定分支尚未实现（P4 未开始），本段用例目前应全部产出真红灯
# （AssertionError：实际 returncode/output 与断言不符），不是 SyntaxError/ImportError。
# gate_p2（BDD-1/3）：project_phase: bootstrap 驱动 P2-skeleton.md 存在性校验，字段
#   缺失/established 时行为须与改动前逐字节一致（回归，允许已绿）。
# gate_p4（BDD-4/7）：暂存代码文件 + 骨架/CODE-MAP 机制已采用 + 「新增文件核对表」标题
#   缺失 → WARNING（不阻断，exit 0）。
# gate_p7（BDD-8/9）：CODE-MAP pairing 两层硬校验——(a) 内部一致性
#   code_map_reviewed_count < code_map_new_files_count → exit 1；(b) 转抄核对 P4 实际
#   [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT] 标记数 > code_map_new_files_count（不是
#   code_map_reviewed_count）→ exit 1（P2-design.md §2.3/§5 已修正的字段对应关系）。
# BDD-10（refactor 不豁免）：change_type: refactor 声明下 gate_p4/gate_p7 判定逻辑
#   同样生效，不因该字段分支跳过。


def test_bdd_1_bootstrap_missing_skeleton_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "project_phase", "bootstrap")
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 1
    assert "P2-skeleton.md" in result.output


def test_bdd_1_bootstrap_with_skeleton_title_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "project_phase", "bootstrap")
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2


def test_bdd_3_field_missing_no_regression_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    # project_phase 字段完全不声明（缺省 = established），P2-skeleton.md 不存在，
    # 行为须与改动前逐字节一致（回归对照，参见既有 test_g2_3_two_candidates_exit_2）。
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2
    assert "P2-skeleton.md" not in result.output


def test_bdd_3_established_explicit_no_regression_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "project_phase", "established")
    _write_p2_design(td, _P2_TWO_CAND_BODY)
    add_p2_candidate_count(td, 2)
    add_p2_review(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P2", str(td))
    assert result.returncode == 2
    assert "P2-skeleton.md" not in result.output


def test_bdd_4_7_gate_p4_warning_when_table_missing(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")
    # P4-implementation.md 由 create_task_dir 生成为空文件（补 frontmatter 后无
    # "## 新增文件核对表" 标题）——满足"表缺失"条件。
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0  # WARNING 不阻断
    assert "WARNING" in result.output
    assert "新增文件核对表" in result.output


def test_bdd_4_7_gate_p4_no_warning_when_table_present(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n\n"
        "## 新增文件核对表\n\n"
        "| 文件 | 骨架归属 | CODE-MAP 处理 |\n"
        "|------|----------|----------------|\n"
        "| src.py | within src | [CODE_MAP_UPDATED] |\n",
        encoding="utf-8",
    )
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0
    assert "WARNING" not in result.output


def test_bdd_8_9_gate_p7_internal_consistency_mismatch_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    # 内部一致性层：code_map_reviewed_count(1) < code_map_new_files_count(2) → exit 1
    # （对应现有 dg_reviewed < dg_count 分支，P2-design.md §2.3/§5）。
    _write_p7(
        td,
        "---\ncode_map_new_files_count: 2\ncode_map_reviewed_count: 1\n---\n"
        "一致性检查进行中。\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "CODE_MAP" in result.output


def test_bdd_8_9_gate_p7_transcription_mismatch_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    # 转抄核对层：P4 实际 [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT] 标记数(3) >
    # P7 的 code_map_new_files_count(2)（不是 code_map_reviewed_count）→ exit 1。
    # code_map_reviewed_count 特意设为与 new_files_count 相等（2），隔离出只有转抄层
    # 失败、内部一致性层本身通过的场景（防止用例写反字段对应关系，P2 review 曾打回的错误点）。
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n"
        "- [CODE_MAP_UPDATED] src/foo.py\n"
        "- [CODE_MAP_UPDATED] src/bar.py\n"
        "- [CODE_MAP_EXEMPT: 仅测试文件] tests/test_foo.py\n",
        encoding="utf-8",
    )
    _write_p7(
        td,
        "---\ncode_map_new_files_count: 2\ncode_map_reviewed_count: 2\n---\n"
        "一致性检查完成。\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "CODE_MAP" in result.output


def test_bdd_8_9_gate_p7_paired_matches_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n"
        "- [CODE_MAP_UPDATED] src/foo.py\n"
        "- [CODE_MAP_EXEMPT: 仅测试文件] tests/test_foo.py\n",
        encoding="utf-8",
    )
    _write_p7(
        td,
        "---\ncode_map_new_files_count: 2\ncode_map_reviewed_count: 2\n---\n"
        "一致性检查完成，CODE-MAP 已同步。\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0


def test_bdd_8_9_gate_p7_mechanism_not_adopted_no_check(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    # code_map_new_files_count / code_map_reviewed_count 均未声明 → 机制未采用，
    # 两层 pairing 校验均不触发（回归对照，behavior 应与改动前一致）。
    _write_p7(td, "---\nagent: test\n---\n一致性检查完成（未采用 CODE-MAP 机制）。\n")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 0
    assert "CODE_MAP" not in result.output


def test_bdd_10_gate_p4_refactor_not_exempt_warning(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0
    assert "WARNING" in result.output
    assert "新增文件核对表" in result.output


def test_bdd_10_gate_p7_refactor_not_exempt_pairing_check(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    add_p1_field(td, "change_type", "refactor")
    _write_p7(
        td,
        "---\ncode_map_new_files_count: 2\ncode_map_reviewed_count: 1\n---\n"
        "一致性检查进行中（refactor 任务）。\n",
    )

    result = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td))
    assert result.returncode == 1
    assert "CODE_MAP" in result.output


# ─────────────────────────────────────────────
# TAG0020 增补：gate_p65（P6.5 强门槛子阶段，BDD-1/2/9/10；P2-design §3.5）
#   judge.enabled falsy（无 judge 字段 / 显式 false）→ 早退 exit 0（BDD-2 历史兼容）；
#   启用但缺 P6.5-judge-verdict.md → exit 1（BDD-1 fail-closed）；
#   否则依次调 check-judge-verdict / check-events，任一 exit 1 → exit 1（BDD-9）；
#   gate_p6 语义不变，judge 产物（P6.5-*）不干扰 P6 gate（BDD-10）。
# 未实现前 check-gate.py 对 "P6.5" 返回未知阶段 exit 2 → 本组新用例全部红灯（B 类）。


def _write_state_judge(td, enabled):
    """覆写 .state.yaml：phase=P6 + judge.enabled（BDD-1/2 judge 机制启用开关）。"""
    (td / ".state.yaml").write_text(
        "task_id: T001\nphase: P6\nstatus: active\nretries: {}\njudge:\n  enabled: "
        + str(enabled).lower()
        + "\n",
        encoding="utf-8",
    )


def _write_judge_pass_fixture(td):
    """gate_p65 通过路径所需合规产物：verdict(passed 1/1) + dispatch-context(白名单合规) + 证据。"""
    (td / "P6-evidence").mkdir(parents=True, exist_ok=True)
    (td / "P6-evidence" / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P6.5-judge-verdict.md").write_text(
        "---\nstatus: passed\ncriteria_total: 1\ncriteria_passed: 1\n"
        'verdict_evidence: ["e1.json"]\n---\n- PASS BDD-1: verified (e1.json)\n',
        encoding="utf-8",
    )
    (td / "P6.5-dispatch-context-judge.md").write_text(
        "---\nphase: P6.5\ntask_id: T001\n---\n\n"
        "### 输入文件\n- P1-requirements.md\n- P6-evidence/\n\n"
        "### 上游关联\n- gate-events.jsonl\n",
        encoding="utf-8",
    )


@pytest.mark.windows_smoke
def test_bdd_2_gate_p65_judge_disabled_early_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-2：judge.enabled: false（历史任务显式关）→ P6.5 早退 exit 0，不要求 judge 产物。"""
    td = task_dir()
    _write_state_judge(td, enabled=False)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6.5", str(td))
    assert result.returncode == 0
    assert "跳过" in result.output


def test_bdd_2_gate_p65_no_judge_field_early_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-2：.state.yaml 无 judge 字段（存量任务）→ 不要求 P6.5-judge-verdict/gate-events，早退 exit 0。"""
    td = task_dir()  # create_task_dir 默认 .state.yaml 无 judge 键

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6.5", str(td))
    assert result.returncode == 0
    assert "跳过" in result.output


def test_bdd_1_gate_p65_judge_enabled_verdict_missing_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-1：judge 启用 + verdict 缺失 → exit 1（P6→P7 阻断，fail-closed）。"""
    td = task_dir()
    _write_state_judge(td, enabled=True)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6.5", str(td))
    assert result.returncode == 1
    assert "P6.5-judge-verdict.md" in result.output


def test_bdd_9_gate_p65_judge_checks_fail_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9：judge 启用 + verdict 存在但机械核对失败（空 verdict）→ check-judge-verdict exit 1 → gate exit 1。"""
    td = task_dir()
    _write_state_judge(td, enabled=True)
    (td / "P6.5-judge-verdict.md").write_text("", encoding="utf-8")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6.5", str(td))
    assert result.returncode == 1


def test_bdd_9_gate_p65_all_pass_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-1/9 正向：judge 启用 + verdict/dispatch-context/证据合规 → check-judge-verdict 与
    check-events（账本缺失合法）均 exit 0 → gate_p65 exit 0（P6→P7 放行）。"""
    td = task_dir()
    _write_state_judge(td, enabled=True)
    _write_judge_pass_fixture(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6.5", str(td))
    assert result.returncode == 0


def test_bdd_10_gate_p6_unaffected_by_judge_artifacts_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-10：judge 启用 + P6.5 产物齐全时，gate_p6 行为与基线一致（exit 2 主 Agent 自判），
    P6.5-* 文件不被 P6 gate 误拦（参照 test_g6_5 基线形态）。"""
    td = task_dir()
    _write_state_judge(td, enabled=True)
    _write_judge_pass_fixture(td)
    _write_p6_acceptance(td, "- PASS BDD-1\n- PASS BDD-2\n")
    _add_p6_evidence(td, "result.log")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result.returncode == 2


# ─────────────────────────────────────────────
# TAG0022 增补：gate_p1 judge 启用强制化（RM-AG0039，BDD-6/7；P2 §4.3 + P2-review NB-4 推荐口径）
#   判据（P2-review 锁定决策 2 + NB-4）：judge 块 presence + P1 created（ISO）≥ judge_required_since
#   （rules/dispatch.yaml "2026-08-22"）：
#     - judge dict + enabled truthy → 放行（原 P1 判定 exit 2 语义不变）
#     - judge dict + enabled falsy → 与缺失同走 created 判据（falsy + created ≥ cutoff → exit 1；
#       falsy + pre-cutoff → 跳过）
#     - judge 缺失 → created ≥ cutoff → exit 1；否则（pre-cutoff / created 缺失或非 ISO）→ 跳过（fail-open）
#     - judge 非 dict（如 judge: true）→ 按缺失处理（fail-open）
#   P3 现状无该校验 → 机制后缺/未启用用例现为 exit 2 → 红灯（B 类）；历史兼容用例现即绿（回归守卫）。
#   既有 gate_p65 judge 三态用例（L2662-2735）语义不动（锁定决策 5），本组不触碰。


def _write_p1_review_approved(td):
    """gate_p1 前置合规 P1-review.md：status approved + agent≠main + 含 BDD 编号引用。"""
    (td / "P1-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nP1 review：BDD-1 已核对通过。\n",
        encoding="utf-8",
    )


def _write_state_yaml_p1(td, judge_block=None):
    """覆写 .state.yaml：phase=P1（P1 gate 上下文）；可选 judge 块（judge_block 为多行字符串）。"""
    lines = ["task_id: T001", "phase: P1", "status: active", "retries: {}"]
    if judge_block is not None:
        lines.append(judge_block)
    (td / ".state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_bdd_6_gate_p1_new_task_missing_judge_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6：机制后新任务（created 2026-08-22 ≥ judge_required_since）且 .state.yaml 无 judge 块 → exit 1。
    TDD：P3 现状无 judge 校验 → exit 2 → 红灯（B 类，行为未实现）。"""
    td = task_dir()
    _write_p1_review_approved(td)
    add_p1_field(td, "created", "2026-08-22")
    _write_state_yaml_p1(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1, result.output


def test_bdd_6_gate_p1_new_task_judge_enabled_true_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6 正向：机制后新任务含 judge.enabled: true → 放行（原 P1 判定 exit 2 语义不变）。
    回归守卫：P3 现状即绿。"""
    td = task_dir()
    _write_p1_review_approved(td)
    add_p1_field(td, "created", "2026-08-22")
    _write_state_yaml_p1(td, judge_block="judge:\n  enabled: true")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2, result.output


def test_bdd_6_gate_p1_judge_disabled_after_cutoff_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6：judge.enabled: false 且机制后（created ≥ cutoff）→ exit 1（NB-4：falsy 同走 created 判据）。
    TDD：P3 现状无校验 → exit 2 → 红灯（B 类）。"""
    td = task_dir()
    _write_p1_review_approved(td)
    add_p1_field(td, "created", "2026-08-22")
    _write_state_yaml_p1(td, judge_block="judge:\n  enabled: false")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 1, result.output


def test_bdd_7_gate_p1_historical_pre_cutoff_no_judge_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：历史任务（created 2026-08-19 < cutoff）无 judge 块 → 不被拦（exit 2）。
    回归守卫：P3 现状即绿。"""
    td = task_dir()
    _write_p1_review_approved(td)
    add_p1_field(td, "created", "2026-08-19")
    _write_state_yaml_p1(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2, result.output


def test_bdd_7_gate_p1_historical_no_created_fail_open_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：历史任务（无 created 字段）无 judge 块 → fail-open 不拦（exit 2）。
    回归守卫：P3 现状即绿。"""
    td = task_dir()
    _write_p1_review_approved(td)
    _write_state_yaml_p1(td)

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2, result.output


def test_bdd_7_gate_p1_judge_disabled_pre_cutoff_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：judge.enabled: false 且 pre-cutoff（created 2026-08-19）→ 跳过不拦（NB-4 推荐口径）。
    回归守卫：P3 现状即绿（P4 按 NB-4 实现后仍 exit 2）。"""
    td = task_dir()
    _write_p1_review_approved(td)
    add_p1_field(td, "created", "2026-08-19")
    _write_state_yaml_p1(td, judge_block="judge:\n  enabled: false")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2, result.output


def test_bdd_7_gate_p1_judge_non_dict_malformed_fail_open_exit_2(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7（TG-2）：.state.yaml judge 为 bool（judge: true，非 dict）→ 按缺失处理（fail-open 不拦）。
    断言口径：dispatch-context「judge 非 dict → 按缺失处理（fail-open）」；P1 created 缺失 → 更不会拦。
    回归守卫：P3 现状即绿。"""
    td = task_dir()
    _write_p1_review_approved(td)
    _write_state_yaml_p1(td, judge_block="judge: true")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td))
    assert result.returncode == 2, result.output


# ========== 8k: TAG0031 P3 gate-robustness 簇（DEBT0016/17/18，BDD-8~13/15） ==========
# 被测：check-gate.py 健壮性三条 DEBT——
#   DEBT0016（BDD-8/9）：gate_p4 的 CODE-MAP.md 路径改用 agate_common.resolve_workspace
#     权威解析函数，取代本地 dirname(dirname(task_dir)) 路径算术。
#   DEBT0017（BDD-10/11）：gate_p4「## 新增文件核对表」判定从子串 `in` 改为整行/标题级
#     re.MULTILINE 正则，消除自指/dogfooding 场景假阴性。
#   DEBT0018（BDD-12/13）：check-gate.py 的 agate_common import 降级 stub 中，
#     read_rules_yaml/count_p6_pass_fail/count_p7_markers/count_code_map_lines 四个
#     "关键读取器"改为显式 fail-closed（安装破损时 return 1 + 明确错误信息），不再静默
#     返回 0/None/空导致消费分支被判定为通过。
# P2-design.md §1.3 R2/R3 风险已在各用例 docstring 标注对应的构造约束（旧格式回退分支/
# resolve_workspace 双依赖降级路径）。
# BDD-15（六条 DEBT 登记闭合聚合检查）归属本簇——三簇中本簇最后完成，是收尾聚合检查的
# 天然位置（P3-dispatch-context-test-designer-gate-robustness.md 明确指派）。DEBT0007 的
# 登记闭合（BDD-7）由 test_debt_registry_closure.py 单独覆盖，不在本节范围内。
# BDD-14（同类未处理实例登记为新 DEBT）是 P8 阶段登记动作，非代码断言，不在本节写自动化
# 测试——验证方式见 P6/P8（详见 P3-test-cases-gate-robustness.md）。
#
# 测试技术选型说明：
#   - BDD-8/12 用白盒直连手法——importlib.util 直接把 check-gate.py 加载为独立模块对象
#     （_load_check_gate_direct，每次调用返回全新模块，测试间互不污染），再 monkeypatch
#     模块级函数名（resolve_workspace / read_rules_yaml / count_p6_pass_fail /
#     count_p7_markers / count_code_map_lines），直接调用 gate_p1/gate_p4/gate_p6/gate_p7。
#     选择这条路径是因为：① BDD-8 要验证的是"gate_p4 是否真的调用并使用了 resolve_workspace
#     的返回值"这一实现机制本身——标准两级嵌套场景下新旧路径算术结果恰好相同，纯黑盒行为无法
#     区分两者，必须靠依赖注入（redirect resolve_workspace 到一个可观测的不同位置）才能证明；
#     ② BDD-12 要模拟"agate_common 整体不可导入"，但 check-gate.py 与同目录的
#     agate-md-field-get.py 等辅助脚本是 subprocess 协作关系，把脚本复制到隔离目录会连带
#     破坏这些协作点，不是该场景的正确模拟手段——直接把四个消费函数替换为 ImportError 降级
#     stub 曾经/现在的返回值（0/None/空），等价于"agate_common 不可导入时这些名字在
#     check-gate.py 命名空间里的实际取值"，是更直接、更不脆弱的模拟。
#   - BDD-9/10/11/13/15 用黑盒 CLI 子进程手法（_run_gate，同本文件既有风格），因为这些场景
#     测的是端到端可观察行为（非标准嵌套下真实 .agate.env 解析结果 / 标题判定的最终文案 /
#     六条 debt 登记条目 status 字段），黑盒验证更贴近用户可观察契约、也更稳健。


def _load_check_gate_direct(agate_scripts):
    """importlib 直接加载 check-gate.py 为独立模块对象（同源手法：check-maintainability.py
    L174-190 / test_agate_cmdstream_*.py 系列既有先例）。

    每次调用都重新 exec_module，返回全新模块对象——测试之间互不共享/污染模块级 monkeypatch
    状态（不同于对已 import 模块打补丁需要手动 undo）。__name__ 与真实 CLI 入口不同
    （"check_gate_direct"），不会触发 `if __name__ == "__main__": main()`。
    """
    spec = importlib.util.spec_from_file_location(
        "check_gate_direct", str(agate_scripts / "check-gate.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_tag0031_bdd_8_gate_p4_code_map_uses_resolve_workspace(
    git_repo, agate_scripts, monkeypatch, capsys
):
    """BDD-8（DEBT0016，正常流）：gate_p4 的 CODE-MAP.md 路径解析改用
    agate_common.resolve_workspace，标准两级嵌套场景下不再本地执行
    dirname(dirname(...)) 路径算术。

    Given task_dir 处于标准两级嵌套（{repo}/agate-workspace/tasks/T001——本地
      dirname(dirname(task_dir)) 算术与 resolve_workspace 默认解析结果本会重合）
    When gate_p4 解析 CODE-MAP.md 路径
    Then 解析结果须来自真正调用 resolve_workspace(project_root) 并使用其返回值——
      用白盒依赖注入手法验证：monkeypatch 模块级 resolve_workspace 让它返回一个"重定向"
      workspace（与本地算术会推导出的路径不同），只在重定向位置放 CODE-MAP.md、本地算术
      位置刻意留空。若 gate_p4 真的调用了 resolve_workspace，就应在重定向位置找到文件并
      触发「新增文件核对表」WARNING；若仍在本地重新推导路径（忽略 monkeypatch），则两处
      都找不到文件，不触发 WARNING。

    现状（P3 设计时点）：gate_p4 未 import/调用 resolve_workspace，本地算术路径下无
    CODE-MAP.md 也无 P2-skeleton.md → 断言 FAIL（红灯，B 类 AssertionError）。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    task_dir_path = repo / "agate-workspace" / "tasks" / "T001"
    task_dir_path.mkdir(parents=True)

    # 本地 dirname(dirname(task_dir)) 算术会推导到这里（repo/agate-workspace）——刻意
    # 不放 CODE-MAP.md，用于区分"用了 resolve_workspace"还是"仍在本地算术"。
    redirected_dir = repo / "redirected-workspace"
    (redirected_dir / "agents").mkdir(parents=True)
    (redirected_dir / "agents" / "CODE-MAP.md").write_text("# CODE-MAP\n", encoding="utf-8")

    (task_dir_path / "P4-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nreviewed.\n",
        encoding="utf-8",
    )
    (task_dir_path / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n无核对表。\n", encoding="utf-8"
    )

    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")

    mod = _load_check_gate_direct(agate_scripts)
    mod.resolve_workspace = lambda project_root: (
        str(redirected_dir),
        str(redirected_dir / "tasks"),
    )

    monkeypatch.chdir(repo)
    result = mod.gate_p4(str(task_dir_path))
    captured = capsys.readouterr()

    assert result == 0, f"WARNING 不应阻断（期望 exit 0），实际 exit {result}，stderr={captured.err!r}"
    assert "新增文件核对表" in captured.err, (
        "期望 gate_p4 调用 resolve_workspace 并在重定向 workspace 找到 CODE-MAP.md 从而触发"
        f"「新增文件核对表」WARNING；实际未触发，说明仍在用本地 dirname(dirname(...)) 算术"
        f"（该算术推导到的位置未放文件）。stderr={captured.err!r}"
    )


def test_tag0031_bdd_9_gate_p4_non_standard_nesting_resolves_via_agate_env(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-9（DEBT0016，边界流）：非标准两级嵌套场景下 CODE-MAP.md 路径解析仍正确
    （DEBT0016 closure_criteria 第 2 条；P2-design.md §1.3 R3：只覆盖
    "非标准两级嵌套 + agate_common 可用"，不要求覆盖"agate_common 不可用"的组合场景）。

    Given task_dir 与 workspace 的层级关系非标准两级嵌套——经由 .agate.env 的
      AGATE_WORKSPACE= 覆盖工作区位置：真实 workspace 在 {repo}/custom-ws，而
      task_dir 只在 {repo}/task 一级（不满足 {workspace}/tasks/{task_id} 两级嵌套约定）。
      本地 dirname(dirname(task_dir)) 算术会错误地推导到 repo 的父目录（repo 外部，
      物理上不可能放着这个任务的 CODE-MAP.md）；权威 resolve_workspace(project_root)
      能正确识别 .agate.env 覆盖并解析到 {repo}/custom-ws。
    When gate_p4 解析 CODE-MAP.md 路径（经真实 CLI 子进程，agate_common 正常可导入）
    Then 解析结果仍与 resolve_workspace 权威函数结果一致，在 {repo}/custom-ws/agents/
      CODE-MAP.md 找到文件并触发「新增文件核对表」WARNING（不产出错误/不存在的路径）。

    现状（P3 设计时点）：本地算术推导到 repo 外部，找不到 CODE-MAP.md，也无
    P2-skeleton.md → 不触发 WARNING → 断言 FAIL（红灯，B 类）。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    (repo / ".agate.env").write_text("AGATE_WORKSPACE=custom-ws\n", encoding="utf-8")

    custom_ws = repo / "custom-ws"
    (custom_ws / "agents").mkdir(parents=True)
    (custom_ws / "agents" / "CODE-MAP.md").write_text("# CODE-MAP\n", encoding="utf-8")

    task = repo / "task"
    task.mkdir()
    (task / "P4-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nreviewed.\n",
        encoding="utf-8",
    )
    (task / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n无核对表。\n", encoding="utf-8"
    )

    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0, result.output  # WARNING 不阻断
    assert "新增文件核对表" in result.output, (
        "期望 gate_p4 经 resolve_workspace 解析 .agate.env 的 AGATE_WORKSPACE 覆盖后在 "
        "{repo}/custom-ws/agents/CODE-MAP.md 找到文件从而触发 WARNING；实际未触发，说明仍在"
        f"用本地 dirname(dirname(task_dir)) 算术（该算术会指向 repo 外部目录）。"
        f"output={result.output!r}"
    )


def test_tag0031_bdd_10_gate_p4_self_referential_prose_not_matched(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-10（DEBT0017，异常流，原假阴性场景）：自指场景下说明性文字不再被误判为
    已满足「新增文件核对表」要求。

    Given P4-implementation.md 只以说明性散文提及"新增了一个标题叫『## 新增文件核对表』的
      小节"（该字符串以叙述文本形式出现，非独立成行的标题）——现状子串 `in` 判定会命中这段
      散文里的字面子串，误判为已满足。
    When gate_p4 判定该文件是否已补充「新增文件核对表」
    Then 判定为未满足（触发 WARNING 提示补充），不再被子串 `in` 匹配误判为已满足。

    现状（P3 设计时点）：子串判定命中散文里的字面子串 → 不触发 WARNING → 断言 FAIL
    （红灯，B 类）。
    """
    td = task_dir()
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n"
        "本次改动给协议卡片模板新增了一个标题叫『## 新增文件核对表』的小节，"
        "用于登记新增文件的骨架归属与 CODE-MAP 处理方式。\n",
        encoding="utf-8",
    )
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0
    assert "WARNING" in result.output and "新增文件核对表" in result.output, (
        "期望自指散文不满足整行/标题级判定，应触发 WARNING；实际未触发，说明仍在用子串 `in`"
        f" 判定（散文中命中了字面子串）。output={result.output!r}"
    )


def test_tag0031_bdd_11_gate_p4_real_heading_trailing_text_satisfied(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-11（DEBT0017，正常流，防止整行判定引入新假阳性）：标题真实存在（标题行尾带
    附加说明文字）时判定通过。

    Given P4-implementation.md 含独立成行的「## 新增文件核对表」标题，行尾附加了额外说明
      文字（验证 re.MULTILINE 行首匹配不要求标题后必须无内容，只要求行首匹配 `^##\\s+新增
      文件核对表`）。
    When gate_p4 判定
    Then 判定为已满足，不触发 WARNING。

    回归守卫：现状子串判定本就能命中这行文字，本用例现状即绿；P4 改为整行/标题级正则后须
    继续保持绿（title-level 正则允许标题行尾有内容，不引入新假阳性）。
    """
    td = task_dir()
    (td / "P2-skeleton.md").write_text("## 骨架声明\n\n占位内容。\n", encoding="utf-8")
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n\n"
        "## 新增文件核对表（本次新增，逐文件标注）\n\n"
        "| 文件 | 骨架归属 | CODE-MAP 处理 |\n"
        "|------|----------|----------------|\n"
        "| src.py | within src | [CODE_MAP_UPDATED] |\n",
        encoding="utf-8",
    )
    _init_repo_with_task(git_repo, td)
    repo = git_repo.path
    _write_p4_review(repo, "approved", "reviewer-subagent")
    (repo / "src.py").write_text("def hello(): pass\n", encoding="utf-8")
    git_repo.stage("src.py")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0
    assert "WARNING" not in result.output


def test_tag0031_bdd_12_gate_p1_read_rules_yaml_missing_fail_closed(
    task_dir, agate_scripts, capsys
):
    """BDD-12（DEBT0018，异常流）：agate_common 不可导入时 gate_p1 消费
    read_rules_yaml 的分支须显式失败。read_rules_yaml 是无条件调用点（不像 P6/P7 的三个
    消费点只在旧格式回退分支触达，见 P2-design.md §1.3 R2），测试构造最直接，作为本 BDD
    的主力用例。

    Given 模拟 agate_common 整体不可导入：直接 import check-gate.py 模块，把
      read_rules_yaml 替换为 ImportError 降级 stub 的返回值（None——等价于 agate_common
      缺失时该名字在 check-gate.py 命名空间里的实际取值，见 check-gate.py:158-159）；
      task 的 .state.yaml 无 judge 块（judge 机制未启用，L684 条件必然为真，
      L687 read_rules_yaml 调用点无条件执行）。
    When check-gate.py 执行 gate_p1（judge 强制校验，消费 read_rules_yaml）
    Then 输出显式「安装破损：agate_common 不可导入」错误信息并 return 1，不再因
      read_rules_yaml 返回 None 导致 cutoff 判据被静默跳过（fail-open，误判为 PASS）。

    现状（P3 设计时点）：read_rules_yaml 返回 None → isinstance(cutoff, str) 为 False →
    整段 judge 强制校验被跳过（无 return）→ gate_p1 继续走到其余检查全部通过 → exit 2
    （PASS）→ 与期望的 exit 1 不符 → 断言 FAIL（红灯，B 类）。
    """
    mod = _load_check_gate_direct(agate_scripts)
    mod.read_rules_yaml = lambda rules_root, name: None  # ImportError 降级 stub 语义

    td = task_dir()
    _write_p1_review_approved(td)
    _write_state_yaml_p1(td)  # 无 judge 块

    result = mod.gate_p1(str(td))
    captured = capsys.readouterr()

    assert result == 1, (
        f"期望 agate_common 不可导入时 fail-closed（exit 1），实际 exit {result}"
        f"（stderr={captured.err!r}）"
    )
    assert "安装破损" in captured.err and "agate_common" in captured.err, (
        f"期望 stderr 含「安装破损」+「agate_common」的显式错误信息，实际: {captured.err!r}"
    )


def test_tag0031_bdd_12_gate_p6_count_pass_fail_missing_fail_closed(
    task_dir, agate_scripts, capsys
):
    """BDD-12（DEBT0018，异常流）：agate_common 不可导入时 gate_p6 消费
    count_p6_pass_fail 的分支须显式失败。

    Given 旧格式 P6-acceptance.md（frontmatter 无 pass/fail 计数字段——命中 P2-design.md
      §1.3 R2 描述的降级哨兵触达分支；新格式 frontmatter 声明时该函数根本不会被调用，见
      BDD-13），模拟 agate_common 不可导入：直接 import 后把 count_p6_pass_fail 替换为
      ImportError 降级 stub 的返回值 (0, 0)。
    When check-gate.py 执行 gate_p6（PASS/FAIL 计数）
    Then 输出显式「安装破损：agate_common 不可导入」错误信息并 return 1。

    现状（P3 设计时点）：(0, 0) 代入 `fail != 0 or total == 0` 恰好也会 return 1（total==0
    这一支凑巧撞对了 exit code），但输出消息是通用的「GATE P6: FAIL=0, TOTAL=0」，不含
    「安装破损」字样——无法让运维区分"这是真的 0 条 BDD"还是"安装破损导致的降级读数"。
    第二条消息断言 FAIL（红灯，B 类）。
    """
    mod = _load_check_gate_direct(agate_scripts)
    mod.count_p6_pass_fail = lambda text: (0, 0)  # ImportError 降级 stub 语义

    td = task_dir()
    _write_p6_acceptance(
        td, "---\nagent: test\n---\n- PASS BDD-1: ok (evidence.png)\n"
    )
    _add_p6_evidence(td, "evidence.png")

    result = mod.gate_p6(str(td))
    captured = capsys.readouterr()

    assert result == 1, f"期望 exit 1，实际 exit {result}（stderr={captured.err!r}）"
    assert "安装破损" in captured.err and "agate_common" in captured.err, (
        f"期望 stderr 含「安装破损」+「agate_common」的显式错误信息，实际: {captured.err!r}"
    )


def test_tag0031_bdd_12_gate_p7_count_markers_missing_fail_closed(
    task_dir, agate_scripts, capsys
):
    """BDD-12（DEBT0018，异常流）：agate_common 不可导入时 gate_p7 消费
    count_p7_markers（BLOCKER/DEVIATION 计数）的分支须显式失败。

    Given 旧格式 P7-consistency.md（frontmatter 无 blocker_count/deviation_critical_count
      字段——命中旧格式回退分支），模拟 agate_common 不可导入：count_p7_markers 替换为
      ImportError 降级 stub 的返回值 (0, 0)。
    When check-gate.py 执行 gate_p7
    Then 输出显式「安装破损：agate_common 不可导入」错误信息并 return 1。

    现状（P3 设计时点）：(0, 0) 代入 `blockers > 0 or devcrit > 0` 为 False，不触发该处
    return，继续往下走（DESIGN_GAP/CODE-MAP 相关字段均未声明，各分支均跳过）最终落到函数
    末尾 `return 0`（P7 的 exit 0 是"通过"语义）——真正的"静默判定为通过"（false-PASS），
    与期望的 exit 1 不符 → 断言 FAIL（红灯，B 类）。
    """
    mod = _load_check_gate_direct(agate_scripts)
    mod.count_p7_markers = lambda text: (0, 0)  # ImportError 降级 stub 语义

    td = task_dir()
    _write_p7(td, "---\nagent: test\n---\n一致性检查完成（旧格式，无 frontmatter 计数字段）。\n")

    result = mod.gate_p7(str(td))
    captured = capsys.readouterr()

    assert result == 1, f"期望 exit 1，实际 exit {result}（stderr={captured.err!r}）"
    assert "安装破损" in captured.err and "agate_common" in captured.err, (
        f"期望 stderr 含「安装破损」+「agate_common」的显式错误信息，实际: {captured.err!r}"
    )


def test_tag0031_bdd_12_gate_p7_count_code_map_lines_missing_fail_closed(
    task_dir, agate_scripts, capsys
):
    """BDD-12（DEBT0018，异常流）：agate_common 不可导入时 gate_p7 消费
    count_code_map_lines（CODE-MAP 转抄核对）的分支须显式失败。

    Given P7-consistency.md 声明 code_map_new_files_count/code_map_reviewed_count
      frontmatter 字段（CODE-MAP pairing 机制"已采用"，转抄核对层的
      count_code_map_lines 调用点在此条件下才会执行，见 check-gate.py:1212-1245），
      内部一致性层 cm_reviewed(2) >= cm_count(2) 先行通过，不提前 return；模拟
      agate_common 不可导入：count_code_map_lines 替换为 ImportError 降级 stub 的
      返回值 0。
    When check-gate.py 执行 gate_p7 的 CODE-MAP 转抄核对分支
    Then 输出显式「安装破损：agate_common 不可导入」错误信息并 return 1。

    现状（P3 设计时点）：0 代入 `p4_code_map_actual_count > cm_count` 为
    `0 > 2` = False，不触发该处 return，继续落到函数末尾 `return 0`（false-PASS）
    → 与期望的 exit 1 不符 → 断言 FAIL（红灯，B 类）。
    """
    mod = _load_check_gate_direct(agate_scripts)
    mod.count_code_map_lines = lambda text: 0  # ImportError 降级 stub 语义

    td = task_dir()
    _write_p7(
        td,
        "---\nagent: test\ncode_map_new_files_count: 2\ncode_map_reviewed_count: 2\n---\n"
        "一致性检查完成，CODE-MAP 已同步。\n",
    )
    (td / "P4-implementation.md").write_text(
        "---\nagent: test\n---\n无 CODE_MAP 标记。\n", encoding="utf-8"
    )

    result = mod.gate_p7(str(td))
    captured = capsys.readouterr()

    assert result == 1, f"期望 exit 1，实际 exit {result}（stderr={captured.err!r}）"
    assert "安装破损" in captured.err and "agate_common" in captured.err, (
        f"期望 stderr 含「安装破损」+「agate_common」的显式错误信息，实际: {captured.err!r}"
    )


def test_tag0031_bdd_13_gate_p6_p7_new_format_unaffected_regression(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-13（DEBT0018，回归，防止 fail-closed 改造引入新假阳性拒绝）：agate_common
    正常可导入时，P6/P7 新格式（frontmatter 计数字段已声明）行为逐字节不变——
    count_p6_pass_fail/count_p7_markers/count_code_map_lines 三个函数在新格式下根本
    不会被调用（P2-design.md §1.3 R2），fail-closed 改造不影响这条快速路径。

    Given agate_common 正常安装可导入（本 worktree 默认开发环境，真实 CLI 子进程，
      不做任何 monkeypatch）；P6-acceptance.md/P7-consistency.md 均用新格式 frontmatter
      声明计数字段。
    When 执行 gate_p6/gate_p7 全量既有判定路径
    Then 判定结果与改造前逐字节一致（P6 exit 2 PASS，P7 exit 0 PASS）。

    现状（P3 设计时点）：本用例即绿（regression baseline——尚未做任何改造，新格式快速路径
    本就不经过四个降级消费点）。P4 完成 fail-closed 改造后须继续保持绿，是本 BDD 的核心
    诉求（防止改造误伤新格式路径）。
    """
    td = task_dir()
    _write_p6_acceptance(
        td,
        "---\nagent: test\npass: 1\nfail: 0\n---\n"
        "逐条结果见 P6-evidence/（新格式，frontmatter 汇总判定）。\n",
    )
    _add_p6_evidence(td, "e.png")

    result_p6 = _run_gate(agate_scripts, python_exe, run_cli, "P6", str(td))
    assert result_p6.returncode == 2, result_p6.output

    td2 = task_dir()
    _write_p7(
        td2,
        "---\nagent: test\nblocker_count: 0\ndeviation_critical_count: 0\n"
        "design_gap_count: 0\ndesign_gap_reviewed_count: 0\n---\n"
        "一致性检查完成（新格式）。\n",
    )
    result_p7 = _run_gate(agate_scripts, python_exe, run_cli, "P7", str(td2))
    assert result_p7.returncode == 0, result_p7.output


def _tag0031_debt_block(text, debt_id):
    """从 tech-debt.md 中取出指定 DEBT id 的 yaml fence 内容（```yaml ... ``` 之间）。
    与 test_debt_registry_closure.py 的 _extract_debt_block 同构（不同测试文件，命名加
    tag0031 前缀避免与其他簇的同名私有辅助函数混淆，无实际 import 依赖）。
    """
    heading_pat = re.compile(r"^## " + re.escape(debt_id) + r"\s*$", re.MULTILINE)
    m = heading_pat.search(text)
    assert m is not None, f"{debt_id} 章节标题未在 tech-debt.md 中找到"
    rest = text[m.end():]
    fence_m = re.search(r"```yaml\n(.*?)\n```", rest, re.DOTALL)
    assert fence_m is not None, f"{debt_id} 章节下未找到 yaml fence 块"
    return fence_m.group(1)


def test_tag0031_bdd_15_six_debts_registry_closed(agate_root):
    """BDD-15：六条 DEBT（0002/0003/0004/0016/0017/0018）登记条目闭合，跨簇聚合收尾检查。

    本用例归属本簇（gate-robustness）产出——三簇（version-mgmt/test-isolation/
    gate-robustness）中本簇最后完成，是收尾聚合检查的天然位置（P3-dispatch-context-
    test-designer-gate-robustness.md §约束 明确指派）。DEBT0007 单独由
    test_debt_registry_closure.py 的 test_bdd_7_debt0007_status_closed_with_closure_fields
    覆盖，不在本用例范围内（避免重复断言同一条目，BDD-7 与 BDD-15 各自独立验收）。

    Given DEBT0002/0003/0004/0016/0017/0018 对应的代码/文档修复与各自 BDD
      （BDD-1/2、BDD-3、BDD-4/5、BDD-8/9、BDD-10/11、BDD-12/13）均已验证生效
    When 在 debt/tech-debt.md 逐条更新这六个条目
    Then 六条条目的 status 均由 open 改为 closed，各自追加 closed_at 与 closure 说明

    当前状态（P3 设计时点）：六条均为 open → 本用例预期全部 FAIL（真红灯，B 类）。
    收尾登记完成后，六条均改为 closed，本用例转绿。
    """
    path = agate_root.parent / "agate-workspace" / "debt" / "tech-debt.md"
    assert path.is_file(), f"tech-debt.md 未找到：{path}"
    text = path.read_text(encoding="utf-8")

    debt_ids = ["DEBT0002", "DEBT0003", "DEBT0004", "DEBT0016", "DEBT0017", "DEBT0018"]
    not_closed = []
    for debt_id in debt_ids:
        block = _tag0031_debt_block(text, debt_id)
        status_m = re.search(r"^status:\s*(\S+)\s*$", block, re.MULTILINE)
        assert status_m is not None, f"{debt_id} 条目缺少 status 字段"
        if status_m.group(1) != "closed":
            not_closed.append((debt_id, status_m.group(1)))

    assert not not_closed, (
        f"以下 DEBT 条目 status 仍非 closed（登记闭合动作尚未执行）：{not_closed}"
    )


# ============================================================
# TAG0035（gate 健壮性批，子批 A/B/C）：BDD-1/2/3/4/7/8/9/10
# 覆盖 check-gate.py 未知阶段 fail-closed（子批A）、回退检测非数字阶段名 fail-closed
# （子批B，check-gate.py 部分）、gate_p4 完整度判据放宽（子批C，DEBT0037）。
# 见 P2-design.md §3.1/§3.2-1/§3.3，P1-requirements.md 对应 BDD 原文。
# 命名沿用既有 test_tag0031_bdd_N 先例（跨任务共用 test_bdd_N 前缀会撞名，本文件同一
# 模块内函数名须全局唯一），本批统一加 tag0035 前缀。
# ============================================================


def test_tag0035_bdd_1_unknown_phase_fail_closed_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-1：未知阶段名（不在 handlers 字典中）fail-closed，exit 1（不再是 2，
    与 P0/P1/P2/P3/P5/P6/P8 的"通过"退出码不再撞车），stderr 含阶段名文本。"""
    td = task_dir()
    result = _run_gate(agate_scripts, python_exe, run_cli, "P99", str(td))
    assert result.returncode == 1, (
        f"未知阶段应 exit 1（fail-closed），实际 exit={result.returncode}, "
        f"output={result.output!r}"
    )
    assert "P99" in result.output


def test_tag0035_bdd_2_ci_backstop_exit_code_comparison_unaffected(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-2：ci-gate-backstop.py 的『记录值==重跑值』比对逻辑本身不因未知阶段退出码
    语义变化（2→1）而报错或行为异常——.gate-result.json 记录新语义下的 exit_code=1，
    CI 重跑（真实 check-gate.py 未知阶段）一致时应正确判定 PASS（backstop exit 0）。

    不需要真实 git 仓库：main() 在 phase 未知（P99）时，check-gate.py 不会访问
    task_dir 下任何文件（BDD-1 分支在 handlers.get 之后立即 exit，早于一切文件 I/O），
    ci-gate-backstop.py 自身除 timestamp 校验外也不依赖 git（timestamp 字段留空即跳过）。
    """
    import json

    repo = tmp_path
    (repo / ".state.yaml").write_text(
        "task_id: T001\nphase: P99\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    (repo / ".gate-result.json").write_text(
        json.dumps({"phase": "P99", "exit_code": 1}), encoding="utf-8"
    )

    result = run_cli(
        python_exe,
        str(agate_scripts / "ci-gate-backstop.py"),
        cwd=str(repo),
        env={"GITHUB_ACTIONS": "true"},
    )
    assert result.returncode == 0, (
        "未知阶段新语义（check-gate.py exit=1）下，.gate-result.json 记录值=1 应与 "
        f"CI 重跑值一致并判定 PASS；实际 backstop exit={result.returncode}, "
        f"output={result.output!r}"
    )


@pytest.mark.parametrize(
    "phase", ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P6.5", "P7", "P8"]
)
def test_tag0035_bdd_3_known_phase_not_routed_to_unknown_path(
    phase, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-3：10 个已知阶段名中任一个，正常执行 gate 检查时不应被路由到未知阶段的
    fail-closed 分支（回归不变性——子批 A 的修复只应影响真正未知的阶段名，不改变
    已知阶段既有的 0/1/2 判定语义）。"""
    td = task_dir()
    result = _run_gate(agate_scripts, python_exe, run_cli, phase, str(td))
    assert "未知阶段" not in result.output, (
        f"phase={phase} 是已知阶段，不应被判定为未知阶段。output={result.output!r}"
    )


@pytest.mark.parametrize(
    ("phase", "old_phase"),
    [
        pytest.param("P1", "p-alpha", id="old_phase_non_numeric"),
        pytest.param("p-alpha", "P3", id="phase_non_numeric"),
    ],
)
def test_tag0035_bdd_4_retreat_detection_non_numeric_phase_fail_closed(
    phase, old_phase, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-4：回退抵达检测的 old_phase/phase 任一为非数字阶段名时，不得静默短路直接
    放行（当前 `if old_num and new_num` 短路会吞掉 None 的情况），须 fail-closed：
    stderr 显式提示"无法解析阶段序号"，exit 1。"""
    td = tmp_path / "bdd4"
    td.mkdir()

    result = _run_gate(
        agate_scripts, python_exe, run_cli, phase, str(td), old_phase=old_phase
    )
    assert result.returncode == 1, (
        f"phase={phase!r} old_phase={old_phase!r}：无法解析阶段序号场景应 exit 1。"
        f"实际 exit={result.returncode}, output={result.output!r}"
    )
    assert "无法解析" in result.output, (
        f"phase={phase!r} old_phase={old_phase!r}：stderr 应含'无法解析'提示。"
        f"实际 output={result.output!r}"
    )


def test_tag0035_bdd_7_check_gate_numeric_retreat_detection_not_regressed(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-7（check-gate.py 部分）：标准数字阶段名的回退抵达检测行为不受 BDD-4
    修复影响——回退（old_phase 数字更大）仍 exit 2；正向推进且暂存区无代码文件仍
    exit 1（既有判据不因新增的"无法解析"分支而改变数字场景下的既有结果）。"""
    td = tmp_path / "bdd7_gate"
    td.mkdir()

    result = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td), old_phase="P2")
    assert result.returncode == 2
    assert "回退抵达" in result.output

    result2 = _run_gate(agate_scripts, python_exe, run_cli, "P1", str(td), old_phase="P0")
    assert result2.returncode == 1


def _tag0035_write_p4_task(task_dir_path, phase_val="P4", retries_yaml="retries: {}\n"):
    """写最小合规 P4 task_dir（.state.yaml + P4-review.md approved）供 BDD-8/9/10 用。
    不写 P2-skeleton.md / CODE-MAP.md，避免触发骨架 WARNING 分支干扰断言。"""
    task_dir_path.mkdir(parents=True, exist_ok=True)
    (task_dir_path / ".state.yaml").write_text(
        f"task_id: T001\nphase: {phase_val}\nstatus: active\n{retries_yaml}",
        encoding="utf-8",
    )
    (task_dir_path / "P4-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nreviewed.\n",
        encoding="utf-8",
    )


def test_tag0035_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-8（DEBT0037）：一个 P4 阶段跨多个 commit 交付，其中较早的 commit 已引入过
    非 md/yaml 代码 diff（commit message 含 `wf(T001-P4)` 标签），当前待检查 commit
    暂存区只含 md 文件——_gate_p4 不应仅凭"当前暂存区无代码文件"就判定 return 1。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    task = repo / "task"
    _tag0035_write_p4_task(task)
    (task / "app.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    git_repo.commit(
        "wf(T001-P4): initial code delivery",
        files=["task/.state.yaml", "task/P4-review.md", "task/app.py"],
    )

    # 第二个 P4 commit：跨 commit 交付，暂存区只含 md 文件
    (task / "P4-notes.md").write_text("additional notes\n", encoding="utf-8")
    git_repo.stage("task/P4-notes.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0, (
        "BDD-8：本 phase 历史 commit 已存在 wf(T001-P4) 代码 diff，第二次纯 md commit "
        f"不应再被 has_code_file 判据误判 return 1。实际 exit={result.returncode}, "
        f"output={result.output!r}"
    )


def test_tag0035_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-9（DEBT0037）：.state.yaml 的 retries[P4] 非空（发生过 P5→P4 回退）且此前
    已存在 `wf(T001-P4)` 代码 commit，本次回退修复 commit 暂存区只含 md/yaml——
    _gate_p4 应识别"回退后再推进"场景，不因该次修复 commit 无代码文件而 return 1。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    task = repo / "task"
    _tag0035_write_p4_task(task)
    (task / "impl.py").write_text("VALUE = 1\n", encoding="utf-8")
    git_repo.commit(
        "wf(T001-P4): first attempt with code",
        files=["task/.state.yaml", "task/P4-review.md", "task/impl.py"],
    )

    # 模拟 P5→P4 回退：retries[P4] 非空 + 本次修复 commit 暂存区只含 md
    (task / ".state.yaml").write_text(
        "task_id: T001\nphase: P4\nstatus: active\nretries:\n  P4:\n  - at: '2026-09-16'\n",
        encoding="utf-8",
    )
    (task / "P4-fix-notes.md").write_text("回退后修复说明\n", encoding="utf-8")
    git_repo.stage("task/.state.yaml")
    git_repo.stage("task/P4-fix-notes.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 0, (
        "BDD-9：retries[P4] 非空（回退后再推进）且历史已有 wf(T001-P4) 代码 commit，"
        f"回退修复 commit 暂存区只含 md/yaml 不应被误判 return 1。实际 "
        f"exit={result.returncode}, output={result.output!r}"
    )


def test_tag0035_bdd_10_gate_p4_pure_doc_no_history_still_blocks(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-10（红灯边界）：纯文档 commit，该 phase 此前既无代码 diff 历史、也不属于
    "回退后修复"场景——_gate_p4 仍应 return 1（放宽只在 BDD-8/9 声明的两种场景生效，
    其余场景维持原判据不放松，对应 known_risks"判据放宽不能削弱拦截力"）。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    task = repo / "task"
    _tag0035_write_p4_task(task)
    git_repo.stage("task/.state.yaml")
    git_repo.stage("task/P4-review.md")

    result = _run_gate(agate_scripts, python_exe, run_cli, "P4", "task", cwd=str(repo))
    assert result.returncode == 1, (
        "BDD-10：纯文档、无代码历史、非回退场景，仍应 return 1（放宽不应削弱此拦截）。"
        f"实际 exit={result.returncode}, output={result.output!r}"
    )
