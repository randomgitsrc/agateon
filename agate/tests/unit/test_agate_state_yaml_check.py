# tests/unit/test_agate_state_yaml_check.py — state-yaml 校验专用工具
# （agate-state-yaml-check.bats 3 用例迁移，TAG0011 批次 2）
# 被测：agate/scripts/agate-state-yaml-check.py（STATE_FILE env 输入，无错误输出空）
# 语义：T001 v2.0 流 D——task_id 正则硬切 ^T[A-Z]{2}\d+$（TAG0001 通过 / T001 拒绝，不兼容双格式）
# 流语义：SY.1 合法态空输出断言基于合并流 .output（bats $output = stdout + stderr，P2 BLOCKER-1）

import pytest


def _run_sy(agate_scripts, python_exe, run_cli, state_file):
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-state-yaml-check.py"),
        env={"STATE_FILE": str(state_file)},
    )


@pytest.mark.windows_smoke
def test_sy_1_new_format_tag0001_passes_lowercase_rejected(
    agate_scripts, python_exe, run_cli, tmp_path
):
    state_file = tmp_path / ".state.yaml"
    state_file.write_text(
        "task_id: TAG0001\nphase: P3\nstatus: active\nretries: {}\n",
        encoding="utf-8",
    )
    result = _run_sy(agate_scripts, python_exe, run_cli, state_file)
    assert result.returncode == 0
    assert result.output.strip() == ""

    # TAG0050 A1（设计 §8 第 3 项）：任务 ID 正则统一为 ^[A-Z]+[0-9]+$（放宽）——
    # T001 由"拒绝"变为"通过"（与 peekview 的 T090 同类）。
    state_file.write_text(
        "task_id: T001\nphase: P3\nstatus: active\nretries: {}\n",
        encoding="utf-8",
    )
    result = _run_sy(agate_scripts, python_exe, run_cli, state_file)
    assert result.returncode == 0
    assert result.output.strip() == ""

    state_file.write_text(
        "task_id: T001a\nphase: P3\nstatus: active\nretries: {}\n",
        encoding="utf-8",
    )
    result = _run_sy(agate_scripts, python_exe, run_cli, state_file)
    assert result.returncode == 0
    assert "task_id 格式错误" in result.output


def test_sy_2_missing_required_field(agate_scripts, python_exe, run_cli, tmp_path):
    state_file = tmp_path / ".state.yaml"
    state_file.write_text("task_id: TAG0001\n", encoding="utf-8")
    result = _run_sy(agate_scripts, python_exe, run_cli, state_file)
    assert result.returncode == 0
    assert "缺必填字段" in result.output


def test_sy_3_invalid_phase_value(agate_scripts, python_exe, run_cli, tmp_path):
    state_file = tmp_path / ".state.yaml"
    state_file.write_text(
        "task_id: TAG0001\nphase: ZZZ\nstatus: active\n",
        encoding="utf-8",
    )
    result = _run_sy(agate_scripts, python_exe, run_cli, state_file)
    assert result.returncode == 0
    assert "phase 非法值" in result.output
