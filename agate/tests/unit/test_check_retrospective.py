# tests/unit/test_check_retrospective.py — 复盘异常触发（gate 重试超限 / SCOPE+ / override）
# （check-retrospective.bats 10 用例迁移，TAG0011 批次 7）
# 被测：agate/scripts/check-retrospective.py（TASK_DIR [STATE_FILE]；总是 exit 0，只提醒）。
# GATE RETRO 提醒消息一律 sys.stderr.write → 按 P2 §3.2 先判流归属，本文件断言一律用
#   合并流 result.output（等价 bats $output，BLOCKER-1）。RT.1/RT.6/RT.7 三处
#   `[ -z "$output" ]` → 合并流空断言 result.output == ""。
# RT_BDD21.1 走 check-gate.py P1（need_confirm_resolved 结构化匹配，exit 2）。
# create_python_shim_bin 退役（P2 §3.1）：pytest 直跑解释器，无需 harness shim。

import pytest


def _run_retro(agate_scripts, python_exe, run_cli, td):
    return run_cli(
        python_exe,
        str(agate_scripts / "check-retrospective.py"),
        str(td),
        str(td / ".state.yaml"),
    )


def _run_gate_p1(agate_scripts, python_exe, run_cli, td):
    return run_cli(
        python_exe,
        str(agate_scripts / "check-gate.py"),
        "P1",
        str(td),
    )


def _insert_override_after_phases(p1_file):
    """等价 bats `sed -i '/^phases:/a override: P2 retained'`。"""
    lines = p1_file.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        out.append(line)
        if line.startswith("phases:"):
            out.append("override: P2 retained")
    p1_file.write_text("\n".join(out) + "\n", encoding="utf-8")


@pytest.mark.windows_smoke
def test_rt_1_no_anomaly_exit_0_empty_output(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert result.output == ""


def test_rt_2_retries_over_exit_0_warns(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / ".state.yaml").write_text(
        "task_id: T001\n"
        "phase: PAUSED\n"
        "status: active\n"
        "retries:\n"
        "  P2:\n"
        "    - attempt: 1\n"
        "    - attempt: 2\n"
        "    - attempt: 3\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "重试超限" in result.output


def test_rt_bdd21_1_need_confirm_resolved_not_blocking(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir(no_state_yaml=True)
    (td / "P1-requirements.md").write_text(
        "---\n"
        "phase: P1\n"
        "task_id: T001-test\n"
        "status: draft\n"
        "agent: analyst\n"
        'need_confirm_resolved: ["z 的边界条件需确认"]\n'
        "---\n"
        "# Requirements\n"
        "- Given x When y Then z\n"
        "- [NEED_CONFIRM] z 的边界条件需确认\n",
        encoding="utf-8",
    )
    (td / "P1-review.md").write_text(
        "---\n"
        "phase: P1\n"
        "task_id: T001-test\n"
        "status: approved\n"
        "agent: requirements-review\n"
        "---\n"
        "## BDD 评审\n"
        "- BDD-1: PASS\n",
        encoding="utf-8",
    )

    result = _run_gate_p1(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 2


def test_rt_dp1_dispatch_prompt_excluded_from_scope_scan(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P4-dispatch-prompt-implementer.md").write_text(
        "> render product\n- [SCOPE+] this should be ignored\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "SCOPE+" not in result.output


def test_rt_4_override_triggers(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _insert_override_after_phases(td / "P1-requirements.md")

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "override" in result.output


def test_rt_5_p3_two_retries_triggers_over(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / ".state.yaml").write_text(
        "task_id: T001\n"
        "phase: PAUSED\n"
        "status: active\n"
        "retries:\n"
        "  P3:\n"
        "    - attempt: 1\n"
        "    - attempt: 2\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "重试超限" in result.output


def test_rt_6_p3_one_retry_no_trigger_empty_output(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / ".state.yaml").write_text(
        "task_id: T001\n"
        "phase: P4\n"
        "status: active\n"
        "retries:\n"
        "  P3:\n"
        "    - attempt: 1\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert result.output == ""


def test_rt_7_inline_scope_plus_not_line_start_empty_output(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P2-design.md").write_text(
        "检查了 [SCOPE+] 的引用情况\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert result.output == ""


def test_retro_scope_dc_1_dispatch_context_excluded_from_scope_scan(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P6-dispatch-context-verifier.md").write_text(
        "- [SCOPE+] 发现：新增功能需重新验收\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "SCOPE+" not in result.output


def test_retro_scope_card_1_agate_card_block_excluded_from_scope_scan(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P2-design.md").write_text(
        "设计内容\n"
        "<!-- AGATE_CARD_START -->\n"
        "- [SCOPE+] 示例：范围扩展\n"
        "<!-- AGATE_CARD_END -->\n"
        "正常设计\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "SCOPE+" not in result.output


# ── DEBT/roadmap 登记提醒行用例，TAG0013（追加，不改既有） ───────────────────

def test_bdd_10_debt_roadmap_reminder_on_anomaly(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / ".state.yaml").write_text(
        "task_id: T001\n"
        "phase: PAUSED\n"
        "status: active\n"
        "retries:\n"
        "  P2:\n"
        "    - attempt: 1\n"
        "    - attempt: 2\n"
        "    - attempt: 3\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "DEBT" in result.output
    assert "roadmap" in result.output


def test_bdd_11_no_anomaly_empty_output(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert result.output == ""


# ── TAG0015 新增：路径文案同步（BDD-9）+ DEBT/roadmap 机制缺口信号（BDD-10）─────
# BDD-11（配套单测覆盖）由本组新增用例本身即构成实现，不单列测试函数（P2-design.md §5）。


def test_tag0015_bdd9_stderr_hint_points_to_task_dir(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9：异常提醒的路径提示改指向 tasks/{Txxx}/retrospective.md，不再提及 docs/releases。"""
    td = task_dir()
    (td / ".state.yaml").write_text(
        "task_id: T001\n"
        "phase: PAUSED\n"
        "status: active\n"
        "retries:\n"
        "  P2:\n"
        "    - attempt: 1\n"
        "    - attempt: 2\n"
        "    - attempt: 3\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "tasks/{Txxx}/retrospective.md" in result.output
    assert "docs/releases" not in result.output


def test_tag0015_bdd10_debt_signal_triggers_mechanism_gap_reminder(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-10：无 retry/SCOPE+/override 异常，但 debt/tech-debt.md 登记了本 task_id
    → 触发"发现机制缺口"提醒（与异常模式提醒文案可区分），exit code 仍为 0。

    fixture 隔离（P2-design.md env_constraints）：手搭两级嵌套目录
    tmp_path/agate-workspace/tasks/T001/（task_dir）+ tmp_path/agate-workspace/debt/
    （兄弟目录），不复用共享 task_dir fixture 的单层布局，避免向上两级推导落在
    tmp_path 本身。
    """
    workspace = tmp_path / "agate-workspace"
    td = workspace / "tasks" / "T001"
    td.mkdir(parents=True)
    (td / ".state.yaml").write_text(
        "task_id: T001\nphase: P4\nstatus: active\nretries: {}\n",
        encoding="utf-8",
    )
    debt_dir = workspace / "debt"
    debt_dir.mkdir(parents=True)
    (debt_dir / "tech-debt.md").write_text(
        '- task_id: "T001"\n  desc: 示例技术债\n',
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "发现机制缺口" in result.output
    assert "T001" in result.output
    # 与异常模式提醒文案（"检测到异常模式"）互相独立、可区分
    assert "检测到异常模式" not in result.output


def test_tag0015_bdd10_roadmap_signal_triggers_mechanism_gap_reminder(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-10 另一触发面：roadmap.md 关联任务表格命中本 task_id 同样触发提醒。"""
    workspace = tmp_path / "agate-workspace"
    td = workspace / "tasks" / "T001"
    td.mkdir(parents=True)
    (td / ".state.yaml").write_text(
        "task_id: T001\nphase: P4\nstatus: active\nretries: {}\n",
        encoding="utf-8",
    )
    roadmap_dir = workspace / "roadmap"
    roadmap_dir.mkdir(parents=True)
    (roadmap_dir / "roadmap.md").write_text(
        "| 关联任务 | 说明 |\n|------|------|\n| T001 | 示例条目 |\n",
        encoding="utf-8",
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "发现机制缺口" in result.output


# ── RM-AG0084 / DEBT0028：工作区推导改走 resolve_workspace（.agate.env 覆盖）────


def _make_nested_task(root, task_id="T1"):
    """建 `<root>/agate-workspace/tasks/<task_id>`（默认两级嵌套布局），返回 task_dir。"""
    td = root / "agate-workspace" / "tasks" / task_id
    td.mkdir(parents=True)
    (td / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: P4\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )
    return td


def test_rm_ag0084_default_layout_workspace_resolved(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """默认布局 `<root>/agate-workspace/tasks/T1` → 工作区 = `<root>/agate-workspace`。"""
    root = tmp_path / "proj"
    td = _make_nested_task(root)
    debt_dir = root / "agate-workspace" / "debt"
    debt_dir.mkdir(parents=True)
    (debt_dir / "tech-debt.md").write_text(
        '- task_id: "T1"\n  desc: 示例技术债\n', encoding="utf-8"
    )

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "发现机制缺口" in result.output


def test_rm_ag0084_env_override_workspace_resolved(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """`.agate.env` 的 AGATE_WORKSPACE=custom-ws 覆盖 → 工作区 = `<root>/custom-ws`。

    回归核心：task_dir 物理上仍在 `<root>/agate-workspace/tasks/T1`（旧的两级 dirname
    推导会得到 `<root>/agate-workspace`），而声明的工作区是 `<root>/custom-ws`——
    DEBT 只在 custom-ws 下，旧实现读不到信号。
    """
    root = tmp_path / "proj"
    td = _make_nested_task(root)
    (root / ".agate.env").write_text("AGATE_WORKSPACE=custom-ws\n", encoding="utf-8")
    debt_dir = root / "custom-ws" / "debt"
    debt_dir.mkdir(parents=True)
    (debt_dir / "tech-debt.md").write_text(
        '- task_id: "T1"\n  desc: 示例技术债\n', encoding="utf-8"
    )
    # 反向守护：默认位置**没有** debt 文件——若仍按旧 dirname 推导则读不到信号。
    assert not (root / "agate-workspace" / "debt").exists()

    result = _run_retro(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "发现机制缺口" in result.output
