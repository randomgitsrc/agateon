# tests/unit/test_agate_render_dispatch_prompt.py — dispatch-prompt 渲染工具
# （agate-render-dispatch-prompt.bats 20 用例迁移，TAG0011 批次 3）
# 被测：agate/scripts/agate-render-dispatch-prompt.py（PHASE ROLE TASK_DIR [--rollback]）
# 语义：渲染结果同时写 TASK_DIR/P{N}-dispatch-prompt-{role}.md 并打印 stdout；
#       appendix 选择按 phase/--rollback 分支；角色文件不存在 → exit 2 + stderr 报错
#       （bats $output 合并流断言，P2 BLOCKER-1）

import re
import shutil

import pytest


def _render(agate_scripts, python_exe, run_cli, phase, role, task_dir, extra=None, env=None):
    args = [
        str(agate_scripts / "agate-render-dispatch-prompt.py"),
        phase,
        role,
        str(task_dir),
    ]
    if extra:
        args.append(extra)
    return run_cli(python_exe, *args, env=env)


def _make_task_dir(tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    return task_dir


@pytest.mark.windows_smoke
def test_rp_1_rejects_missing_arguments(agate_scripts, python_exe, run_cli):
    result = run_cli(python_exe, str(agate_scripts / "agate-render-dispatch-prompt.py"))
    assert result.returncode == 1


def test_rp_2_rejects_invalid_phase(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P9", "architect", task_dir)
    assert result.returncode == 2


def test_rp_3_rejects_nonexistent_task_dir(agate_scripts, python_exe, run_cli):
    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", "/nonexistent")
    assert result.returncode == 2


def test_rp_4_placeholder_replacement_phase_role_task_id(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    assert "P2 阶段的 architect 子 Agent" in result.output
    assert "阶段 阶段" not in result.output
    assert task_dir.name in result.output
    assert "P2-dispatch-context-architect.md" in result.output
    assert "P{N}" not in result.output
    assert "{role}" not in result.output


def test_rp_5_p2_selects_p2_appendix(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    assert "P2 最小验证" in result.output
    assert "上下文控制" not in result.output
    assert "回退诊断" not in result.output


def test_rp_6_p4_without_rollback_selects_normal_appendix(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P4", "implementer", task_dir)
    assert result.returncode == 0
    assert "上下文控制" in result.output
    assert "回退诊断" not in result.output


def test_rp_7_p4_with_rollback_selects_rollback_appendix(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(
        agate_scripts, python_exe, run_cli, "P4", "implementer", task_dir, extra="--rollback"
    )
    assert result.returncode == 0
    assert "回退诊断" in result.output
    assert "上下文控制" not in result.output


def test_rp_8_p5_p6_share_same_appendix(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result_p5 = _render(agate_scripts, python_exe, run_cli, "P5", "verifier", task_dir)
    assert result_p5.returncode == 0
    assert "截图质量标准" in result_p5.output
    assert "上下文控制" not in result_p5.output
    result_p6 = _render(agate_scripts, python_exe, run_cli, "P6", "verifier", task_dir)
    assert result_p6.returncode == 0
    assert "截图质量标准" in result_p6.output


def test_rp_9_p8_selects_p8_appendix(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P8", "implementer", task_dir)
    assert result.returncode == 0
    assert "READY 收尾检查" in result.output
    assert "上下文控制" not in result.output


def test_rp_10_role_special_chars_safe_filename(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "design-review", task_dir)
    assert result.returncode == 0
    assert (task_dir / "P2-dispatch-prompt-design-review.md").is_file()


def test_rp_11_output_file_contains_render_product_header(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    out_text = (task_dir / "P2-dispatch-prompt-architect.md").read_text(encoding="utf-8")
    assert "渲染产物" in out_text
    assert "不是协议模板" in out_text


def test_rp_12_rollback_ignored_for_non_p4(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(
        agate_scripts, python_exe, run_cli, "P2", "architect", task_dir, extra="--rollback"
    )
    assert result.returncode == 0
    assert "P2 最小验证" in result.output
    assert "回退诊断" not in result.output


_RESIDUAL_WHITELIST = (
    "{上一阶段文件名}",
    "{project_conventions_file}",
    "{problems|design|review|test-cases|implementation|test-results|acceptance|consistency|release}",
)


def test_rp_13_no_residual_placeholders_except_whitelisted(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P4", "implementer", task_dir)
    assert result.returncode == 0
    residual = [
        m
        for m in re.findall(r"\{[a-zA-Z0-9_|： -]+\}", result.output)
        if m not in _RESIDUAL_WHITELIST
    ]
    assert residual == []


def test_rp_14_agate_root_replaced_with_actual_path(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P4", "implementer", task_dir)
    assert result.returncode == 0
    assert "{agate_root}" not in result.output
    assert "assets/execution-roles/implementer.md" in result.output


def test_rp_15_review_roles_detected_for_review_role(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "design-review", task_dir)
    assert result.returncode == 0
    assert "assets/review-roles/design-review.md" in result.output


def test_rp_16_p3_renders_p3_self_check_appendix(
    agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(
        agate_scripts,
        python_exe,
        run_cli,
        "P3",
        "test-designer",
        task_dir,
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert "P3 自检" in result.output


def test_rp_17_role_file_missing_exit_2(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "nonexistent-role", task_dir)
    assert result.returncode == 2
    assert "角色文件不存在" in result.output


def test_rp_18_execution_role_no_review_special_instructions(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    assert "Review 角色特别指令" not in result.output


def test_rp_19_review_role_contains_status_semantics(
    agate_scripts, python_exe, run_cli, tmp_path
):
    task_dir = _make_task_dir(tmp_path)
    result = _render(agate_scripts, python_exe, run_cli, "P2", "design-review", task_dir)
    assert result.returncode == 0
    assert "Review 角色特别指令" in result.output
    assert "approved" in result.output
    assert "rejected" in result.output
    assert "needs-revision" in result.output


def test_bdd_20_agate_root_with_ampersand_literal(
    agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    root = tmp_path / "x&y" / "agate"
    (root / "assets" / "templates").mkdir(parents=True)
    (root / "assets" / "execution-roles").mkdir(parents=True)
    shutil.copyfile(
        str(agate_root / "assets" / "templates" / "dispatch-prompt.md"),
        str(root / "assets" / "templates" / "dispatch-prompt.md"),
    )
    shutil.copyfile(
        str(agate_root / "assets" / "execution-roles" / "implementer.md"),
        str(root / "assets" / "execution-roles" / "implementer.md"),
    )
    task_dir = _make_task_dir(tmp_path)
    result = _render(
        agate_scripts,
        python_exe,
        run_cli,
        "P4",
        "implementer",
        task_dir,
        env={"AGATE_ROOT": str(root)},
    )
    assert result.returncode == 0
    assert "{agate_root}" not in result.output
    assert str(root) in result.output


# ===== TAG0023 RM-AG0045（BDD-11）：dispatch-prompt.md 新增"声明写时自检"小节 =====
# 被测：agate/assets/templates/dispatch-prompt.md「返回前自检」节新增子项（P2-design.md
# §2.4 候选 A：subagent 返回前若产出含 P1/P2 声明，须跑 check-frontmatter.py /
# check-routing.py 自检，非 0 退出须本回合内修正后再返回）。当前模板尚无此小节文本，
# 本用例红灯。


def test_bdd_11_dispatch_prompt_declares_write_time_selfcheck_section(agate_root):
    tmpl_path = agate_root / "assets" / "templates" / "dispatch-prompt.md"
    tmpl = tmpl_path.read_text(encoding="utf-8")
    assert "P1/P2 声明写时自检" in tmpl


# ── RM-AG0084 / DEBT0028：{AGATE_WORKSPACE} 改走 resolve_workspace（.agate.env 覆盖）─


def test_rm_ag0084_default_layout_workspace_placeholder(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """默认布局 `<root>/agate-workspace/tasks/T1` → {AGATE_WORKSPACE}=`<root>/agate-workspace`。"""
    root = tmp_path / "proj"
    task_dir = root / "agate-workspace" / "tasks" / "T1"
    task_dir.mkdir(parents=True)

    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    # 模板行 `读取并严格遵循：{AGATE_WORKSPACE}/tasks/{Txxx}/...` 渲染后须指向默认工作区。
    expected_ws = str((root / "agate-workspace").resolve())
    assert expected_ws + "/tasks/T1/P2-dispatch-context-architect.md" in result.output


def test_rm_ag0084_env_override_workspace_placeholder(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """`.agate.env` 的 AGATE_WORKSPACE=custom-ws 覆盖 → {AGATE_WORKSPACE}=`<root>/custom-ws`。

    回归核心：task_dir 物理上仍在 `<root>/agate-workspace/tasks/T1`，旧的两级 dirname
    推导会把占位符填成 `<root>/agate-workspace`，而非声明的工作区 `<root>/custom-ws`。
    """
    root = tmp_path / "proj"
    task_dir = root / "agate-workspace" / "tasks" / "T1"
    task_dir.mkdir(parents=True)
    (root / ".agate.env").write_text("AGATE_WORKSPACE=custom-ws\n", encoding="utf-8")

    result = _render(agate_scripts, python_exe, run_cli, "P2", "architect", task_dir)
    assert result.returncode == 0
    assert str((root / "custom-ws").resolve()) + "/tasks/T1/P2-dispatch-context-architect.md" in result.output
    assert (
        str((root / "agate-workspace").resolve())
        + "/tasks/T1/P2-dispatch-context-architect.md"
        not in result.output
    )
