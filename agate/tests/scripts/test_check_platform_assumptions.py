# tests/scripts/test_check_platform_assumptions.py — 平台假设静态扫描器行为测试
# （scripts/check-platform-assumptions.bats 16 用例迁移，TAG0011 批次 16）
# 被测对象：agate/scripts/check-platform-assumptions.py（TAG0010 自 bash 版迁移；TDD 红灯目标 =
# 命令不存在）。
# 扫描器契约（P2-design §2.1）：
#   R1 硬编码 PATH 字面（/usr 或 /bin 赋值）
#   R2 命令位置裸解释器（豁免 command -v 探测、env 形式、shebang、@test 标题、注释行、docstring 块）
#   R3 方括号形式 -L 单平台 symlink 断言
#   R4 临时目录字面量（豁免 BATS_TEST_TMPDIR 变量行与含 "# scan-exempt:" 标记的行）
#   R5 命令位置裸外部工具（bc 为已登记项；模式集可扩充 seq/timeout 等）
# 输出：命中行形如 `R{n} <file>:<line> <摘要>`（stderr）；无命中无输出。
# 退出：0 = 无命中；1 = 有命中；2 = 目标不存在。
# 本测试文件自身必须保持"干净"：fixture 内容全部运行时用 fragment 拼接法构造，
# 源码任何一行（含注释）都不出现 R1-R5 的字面命中，确保扫描器全树扫描本文件 0 命中（BDD-8）。
# windows_smoke：bdd-1（platform 关键词）+ bdd-4（symlink）+ bdd-9-r3-symlink（symlink）——共 3 处
# （P3 §5.2 表 W；每文件第 1 用例 bdd-1 已含 platform 关键词）。

import re

import pytest

_PATH_LEAD = 'PATH="'
_PATH_MID = "/usr/bin:"
_PATH_TAIL = '/bin"'

_PY = "python"
_VER = "3"

_BRACKET_OPEN = "[[ -"
_L_FLAG = "L"

_TMP_HEAD = "/tm"
_TMP_P = _TMP_HEAD + "p"

_BC_FIRST = "b"
_BC_FULL = _BC_FIRST + "c"


def _make_fixture(tmp_path, lines):
    """写一个 fixture 文件到 tmp_path 下（内容逐行给出，运行时写入）。"""
    fx = tmp_path / "fixture.txt"
    fx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fx


def _assert_hit(run_cli, python_exe, agate_scripts, fx, rule):
    """运行扫描器扫描 fixture，断言命中指定规则（exit 1 + 输出含规则号与文件路径）。"""
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx)
    )
    assert result.returncode == 1, result.output
    assert rule in result.output
    assert str(fx) in result.output


@pytest.mark.windows_smoke
def test_bdd_1_scanner_script_exists_platform_neutral(agate_scripts):
    """bdd-1：扫描器本体存在且无 GNU 专用特性（纯 re 引擎，无外部命令调用 / 无 --perl-regexp）。

    等价 bats：`[ -f ... ]` + `grep -nE 'subprocess|os.system|os.popen'`（无命中）+
    `grep -n -- '--perl-regexp'`（无命中）→ 映射为读文件后正则/子串断言。
    """
    scanner = agate_scripts / "check-platform-assumptions.py"
    assert scanner.is_file()
    text = scanner.read_text(encoding="utf-8")
    # RM-AG0105：原为**子串**断言（`subprocess|os.system|os.popen` 任一出现即失败）——
    # 但扫描器**必须**在 R6 规则里提到 `subprocess`（规则主语），子串判定无法区分
    # 「调用」与「提及」。改为断言**调用形态**（本测试本意 = 扫描器不得调用外部进程）。
    assert not re.search(r"subprocess\.\w+\s*\(|os\.system\s*\(|os\.popen\s*\(", text)
    assert "--perl-regexp" not in text


def test_bdd_2_scanner_detects_hardcoded_path(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-2：R1——fixture 含硬编码 PATH 字面 → 非零 + 报告 R1 与文件路径。"""
    line = _PATH_LEAD + _PATH_MID + _PATH_TAIL
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R1")


def test_bdd_3_scanner_detects_bare_python3(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-3：R2——fixture 含命令位置裸解释器（非探测形态）→ 非零 + 报告 R2。"""
    line = _PY + _VER + " -c 'print(1)'"
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R2")


@pytest.mark.windows_smoke
def test_bdd_4_scanner_detects_symlink_assertion(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-4：R3——fixture 含方括号形式 -L 断言 → 非零 + 报告 R3。"""
    line = _BRACKET_OPEN + _L_FLAG + ' "$repo/.git/hooks/pre-push" ]]'
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R3")


def test_bdd_5_scanner_detects_tmp_path(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-5：R4——fixture 含临时目录字面量逻辑路径（cd 用法）→ 非零 + 报告 R4。"""
    line = "cd " + _TMP_P
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R4")


def test_bdd_6_scanner_detects_bare_bc(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-6：R5——fixture 含命令位置的裸外部工具（bc 为已登记项）→ 非零 + 报告 R5。"""
    line = "echo 1 | " + _BC_FULL
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R5")


def test_bdd_8_clean_tree_zero_detection(agate_root, agate_scripts, python_exe, run_cli):
    """bdd-8：修复完成后 tests/ 全树扫描 0 命中（同类扫描闭环；P3 红灯 = 命令不存在）。"""
    result = run_cli(
        python_exe,
        str(agate_scripts / "check-platform-assumptions.py"),
        str(agate_root / "tests"),
    )
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_9_dirty_fixture_all_rules_reported(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：含全部 5 类假设的 fixture → 非零 + R1~R5 全部报告。"""
    lines = [
        _PATH_LEAD + _PATH_MID + _PATH_TAIL,
        _PY + _VER + " -c 'import sys'",
        _BRACKET_OPEN + _L_FLAG + ' "$f" ]]',
        "cd " + _TMP_P,
        "echo 1 | " + _BC_FULL,
    ]
    fx = _make_fixture(tmp_path, lines)
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx)
    )
    assert result.returncode == 1
    for rule in ("R1", "R2", "R3", "R4", "R5"):
        assert rule in result.output
    assert str(fx) in result.output


def test_bdd_9_clean_fixture_zero_report(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：干净 fixture（R2 全部豁免形态 + R4 天然豁免 BATS_TEST_TMPDIR）→ 零退出无报告。"""
    shebang = "#!/usr/bin/env " + _PY + _VER
    cmd_v = "command -v " + _PY + _VER + " || " + "command -v " + _PY
    env_form = "env " + _PY + _VER
    test_title = '@test "' + _PY + _VER + ' title"'
    comment = "# 说明 " + _PY + _VER
    tmp_var = "clean_dir=$BATS_TEST_TMPDIR/demo"
    fx = _make_fixture(tmp_path, [shebang, cmd_v, env_form, test_title, comment, tmp_var])
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx)
    )
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_9_directory_scan_respects_shell_extension_filter(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """bdd-9：目录目标——递归扫 .bats/.bash/.sh/.py，忽略其他扩展名。"""
    scan_dir = tmp_path / "scan-dir"
    scan_dir.mkdir()
    dirty = _PATH_LEAD + _PATH_MID + _PATH_TAIL
    (scan_dir / "ignored.txt").write_text(dirty + "\n", encoding="utf-8")
    (scan_dir / "dirty.bats").write_text(dirty + "\n", encoding="utf-8")
    (scan_dir / "dirty.py").write_text(dirty + "\n", encoding="utf-8")
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(scan_dir)
    )
    assert result.returncode == 1
    assert "R1" in result.output
    assert "dirty.bats" in result.output
    assert "dirty.py" in result.output
    assert "ignored.txt" not in result.output


def test_bdd_9_scan_exempt_exempts_r4_sample_text(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：负向——含 "# scan-exempt:" 标记的样例文本行（临时目录字面量）→ R4 豁免，零命中。"""
    line = (
        "echo imported from "
        + _TMP_P
        + "/demo/fixture.txt # scan-exempt: mock 输出样例文本（非路径假设）"
    )
    fx = _make_fixture(tmp_path, [line])
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx)
    )
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_9_scan_exempt_does_not_exempt_r1_path(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：负向——标记不豁免 R1（含标记的 PATH 命中行仍应被检出）。"""
    line = _PATH_LEAD + _PATH_MID + _PATH_TAIL + " # scan-exempt: 尝试用标记豁免 R1"
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R1")


def test_bdd_9_scan_exempt_does_not_exempt_r2_python(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：负向——标记不豁免 R2（含标记的命令位置裸解释器仍应被检出）。"""
    line = _PY + _VER + " -c 'print(1)' # scan-exempt: 尝试用标记豁免 R2"
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R2")


@pytest.mark.windows_smoke
def test_bdd_9_scan_exempt_does_not_exempt_r3_symlink(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：负向——标记不豁免 R3（含标记的方括号 -L 断言仍应被检出）。"""
    line = (
        _BRACKET_OPEN
        + _L_FLAG
        + ' "$repo/.git/hooks/pre-push" ]]# scan-exempt: 尝试用标记豁免 R3'
    )
    fx = _make_fixture(tmp_path, [line])
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R3")


def test_bdd_9_docstring_exempts_r2_python_sample(tmp_path, agate_scripts, python_exe, run_cli):
    """bdd-9：正向——docstring 块内裸解释器（文档非可执行代码，与 # 注释同类豁免）→ 零命中。

    BLOCKER-1（TAG0010 py 化新增）。
    """
    q = '"""'
    lines = [q, "    " + _PY + _VER + " -c 'print(1)'", q]
    fx = _make_fixture(tmp_path, lines)
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx)
    )
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_9_docstring_exemption_does_not_cover_bare_python3(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """bdd-9：负向——docstring 块外裸解释器（块外示例代码非 docstring）→ 仍命中 R2。

    BLOCKER-1（TAG0010 py 化新增）。
    """
    q = '"""'
    lines = [q, "    " + _PY + _VER + " -c 'print(1)'", q, _PY + _VER + " -c 'print(2)'"]
    fx = _make_fixture(tmp_path, lines)
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R2")


def test_rm_ag0105_r6_text_without_encoding_detected(tmp_path, agate_scripts, python_exe, run_cli):
    """RM-AG0105 / DEBT0058：R6——`subprocess` 文本模式（`text=True`）**缺 `encoding=`** → 命中。

    **调用级**判定：文本模式与 `encoding=` 常分行，行级判定会大面积误报（本批实测）。
    """
    fx = _make_fixture(
        tmp_path,
        [
            # 运行时拼接：避免源码出现 R6 的两个关键字面量
            # （否则本测试**自身**会被 R6 命中 ⇒ bdd_8 全树 0 命中失守）
            "import " + "subprocess",
            "r = sub" + "process.run(",
            '    ["git", "status"],',
            "    capture_output=True,",
            "    text" + "=True,",
            "    timeout=60,",
            ")",
        ],
    )
    _assert_hit(run_cli, python_exe, agate_scripts, fx, "R6")


def test_rm_ag0105_r6_with_encoding_not_detected(tmp_path, agate_scripts, python_exe, run_cli):
    """RM-AG0105 / DEBT0058（正向对照）：同一调用**含** `encoding=` → 不命中 R6。"""
    fx = _make_fixture(
        tmp_path,
        [
            "import " + "subprocess",
            "r = sub" + "process.run(",
            '    ["git", "status"],',
            "    capture_output=True,",
            "    text" + "=True,",
            '    encoding="utf-8",',
            "    timeout=60,",
            ")",
        ],
    )
    result = run_cli(python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(fx))
    assert "R6" not in result.output, (
        f"含 encoding= 不得命中 R6；实际输出 {result.output[:300]!r}"
    )
