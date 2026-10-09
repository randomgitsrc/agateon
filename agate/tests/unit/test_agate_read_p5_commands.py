# tests/unit/test_agate_read_p5_commands.py — P5 gate_commands 解析器
# （agate-read-p5-commands.bats 4 用例迁移，TAG0011 批次 2）
# 被测：agate/scripts/agate-read-p5-commands.py（P2_DESIGN env 指向 md 文件，stdout 输出 JSON）
# 流语义：P5C.2 / P5C.3 空输出断言基于合并流 .output（bats $output = stdout + stderr，P2 BLOCKER-1）

import json

import pytest


def _run_p5c(agate_scripts, python_exe, run_cli, p2_file):
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-read-p5-commands.py"),
        env={"P2_DESIGN": str(p2_file)},
    )


@pytest.mark.windows_smoke
def test_p5c_1_p2_with_p5_and_formatters_output_commands(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text(
        "---\nagent: test\n---\ngate_commands:\n"
        "  P5: pytest\n"
        "  P5_formatter: pytest.sh\n"
        "  P5_js: vitest run\n"
        "  P5_js_formatter: vitest.sh\n",
        encoding="utf-8",
    )
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    assert '"cmd": "pytest"' in result.output
    assert '"formatter": "pytest.sh"' in result.output
    assert '"cmd": "vitest run"' in result.output
    assert '"commands"' in result.output


def test_p5c_2_p2_empty_gate_commands_output_empty(agate_scripts, python_exe, run_cli, tmp_path):
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text("---\nagent: test\n---\ngate_commands: {}\n", encoding="utf-8")
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    assert result.output.strip() == ""


def test_p5c_3_p2_no_gate_commands_block_output_empty(agate_scripts, python_exe, run_cli, tmp_path):
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text("---\nagent: test\n---\n无 gate_commands\n", encoding="utf-8")
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    assert result.output.strip() == ""


def test_p5c_5_bdd_1_3_timeout_seconds_not_treated_as_command(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """BDD-1/3: `P5_timeout_seconds: 120` 不得作为一条命令出现在 `commands` 输出中——
    当前脚本只排除 `_formatter` 键，`_timeout_seconds` 会被误判为一条 cmd="120" 的命令。"""
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text(
        "---\nagent: test\n---\ngate_commands:\n"
        "  P5: pytest -q\n"
        "  P5_timeout_seconds: 120\n",
        encoding="utf-8",
    )
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    assert '"cmd": "pytest -q"' in result.output
    assert '"cmd": "120"' not in result.output
    assert "timeout_seconds" not in result.output


def test_p5c_4_p5_quoted_values_stripped_with_formatter_link(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text(
        "---\nagent: test\n---\ngate_commands:\n"
        '  P5: "pytest -q"\n'
        "  P5_html_formatter: vitest.sh\n"
        '  P5_html: "npx vitest"\n',
        encoding="utf-8",
    )
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    assert '"cmd": "pytest -q"' in result.output
    assert '"cmd": "npx vitest"' in result.output
    assert '"formatter": "vitest.sh"' in result.output


# ========== RM-AG0092 / DEBT0047：只剥成对引号（值以引号结尾不被吞） ==========


def test_rm_ag0092_paired_quotes_only_trailing_quote_preserved(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """值整体加双引号但内部以单引号收尾（`"pytest -k 'foo'"`）→ 只剥外层成对双引号，
    末尾单引号须保留（原实现 `.strip('"').strip("'")` 各自剥首尾，会吞掉末尾 `'`）。"""
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text(
        "---\nagent: test\n---\ngate_commands:\n"
        "  P5: \"pytest -k 'foo'\"\n",
        encoding="utf-8",
    )
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    data = json.loads(result.output.strip())
    assert data["commands"][0]["cmd"] == "pytest -k 'foo'"


def test_rm_ag0092_unpaired_quote_preserved(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """首尾引号不成对（`'foo`）→ 原样保留，不剥任何引号。"""
    p2_file = tmp_path / "P2-design.md"
    p2_file.write_text(
        "---\nagent: test\n---\ngate_commands:\n"
        "  P5: 'foo\n",
        encoding="utf-8",
    )
    result = _run_p5c(agate_scripts, python_exe, run_cli, p2_file)
    assert result.returncode == 0
    data = json.loads(result.output.strip())
    assert data["commands"][0]["cmd"] == "'foo"
