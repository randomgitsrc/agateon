# tests/unit/test_check_tdd_red_formatter.py — formatter 脚本输出归一化
# （check-tdd-red-formatter.bats 13 用例迁移，TAG0011 批次 10b）
# 被测：agate/assets/formatters/ 下 6 个 formatter 薄壳（仍为 sh，pytest.sh / vitest.sh /
#   go-test.sh / generic-tap.sh / generic-junit-xml.sh / generic-exit-only.sh）。
# 调用方式保持（P3 §4 批次 10 口径）：run_cli(bash, <formatter>.sh, <exit_code>, input=<输出>)
#   ——等价 bats `echo "<输出>" | bash "$FORMATTER_DIR/<name>.sh" <exit_code>`（bash 为 conftest fixture，
#   Windows 上解析到 Git Bash，避开 System32 WSL bash）。
# JSON 由 formatter 的 python 经 print 写 stdout → json.loads(result.stdout)。
# R4 平台无关（P2 §3.1）：FMT.8/9 的 vitest mock 输出样例含临时目录字面（bats 原文用
#   `# scan-exempt:` 行级豁免）——pytest 侧改运行时拼接，避免源码命中 R4（本注释不写该字面）。

import json

import pytest


def _run_formatter(agate_assets, bash, run_cli, formatter, output, exit_code):
    return run_cli(
        bash, str(agate_assets / "formatters" / formatter), str(exit_code), input=output
    )


def _json(result):
    return json.loads(result.stdout)


_VITEST_IMPORT_FROM = "/t" + "mp/test/foo.test.ts"


@pytest.mark.windows_smoke
def test_fmt_1_generic_exit_only_exit_1_empty_arrays(agate_assets, run_cli, bash):
    result = _run_formatter(agate_assets, bash, run_cli, "generic-exit-only.sh", "some output", 1)
    data = _json(result)
    assert data["exit_code"] == 1
    assert len(data["failed_tests"]) == 0
    assert len(data["import_errors"]) == 0
    assert len(data["syntax_errors"]) == 0


def test_fmt_2_generic_exit_only_exit_0(agate_assets, run_cli, bash):
    result = _run_formatter(agate_assets, bash, run_cli, "generic-exit-only.sh", "all good", 0)
    data = _json(result)
    assert data["exit_code"] == 0
    assert data["passed"] == 0
    assert data["failed"] == 0


def test_fmt_3_pytest_2_failed_5_passed(agate_assets, run_cli, bash):
    output = (
        "tests/test_a.py::test_one FAILED [ 50%]\n"
        "tests/test_b.py::test_two FAILED [100%]\n"
        "2 failed, 5 passed"
    )
    result = _run_formatter(agate_assets, bash, run_cli, "pytest.sh", output, 1)
    data = _json(result)
    assert data["failed"] == 2
    assert data["passed"] == 5
    assert data["errors"] == 0
    assert len(data["failed_tests"]) == 2


def test_fmt_4_pytest_b_class_import_error_module(agate_assets, run_cli, bash):
    output = "ERROR tests/test_x.py - ImportError: cannot import name 'Yyy' from 'myapp.foo'\n1 error"
    result = _run_formatter(agate_assets, bash, run_cli, "pytest.sh", output, 2)
    data = _json(result)
    assert data["import_errors"][0]["module"] == "myapp.foo"


def test_fmt_5_pytest_a_class_syntax_error(agate_assets, run_cli, bash):
    output = "ERROR tests/test_x.py - SyntaxError: invalid syntax\n1 error"
    result = _run_formatter(agate_assets, bash, run_cli, "pytest.sh", output, 2)
    data = _json(result)
    assert len(data["syntax_errors"]) == 1


def test_fmt_6_pytest_all_passed(agate_assets, run_cli, bash):
    result = _run_formatter(agate_assets, bash, run_cli, "pytest.sh", "5 passed", 0)
    data = _json(result)
    assert data["passed"] == 5
    assert data["failed"] == 0


def test_fmt_7_vitest_11_failed_6_passed(agate_assets, run_cli, bash):
    output = "Tests  11 failed | 6 passed\nTest Files  3 failed"
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", output, 1)
    data = _json(result)
    assert data["failed"] == 11
    assert data["errors"] == 0
    assert len(data["import_errors"]) == 0


def test_fmt_8_vitest_b_class_import_error_module(agate_assets, run_cli, bash):
    output = (
        "Failed Suites 1\n"
        f"Error: Cannot find module '../src/bar' imported from {_VITEST_IMPORT_FROM}"
    )
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", output, 1)
    data = _json(result)
    assert data["import_errors"][0]["module"] == "../src/bar"


def test_fmt_9_vitest_a_class_import_error_module(agate_assets, run_cli, bash):
    output = (
        "Failed Suites 1\n"
        f"Error: Cannot find module 'react' imported from {_VITEST_IMPORT_FROM}"
    )
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", output, 1)
    data = _json(result)
    assert data["import_errors"][0]["module"] == "react"


def test_fmt_10_go_test_cargo_failed_tests_contains(agate_assets, run_cli, bash):
    output = (
        "test foo::test_bar ... FAILED\n"
        "test foo::test_baz ... ok\n"
        "test foo::test_qux ... ok\n"
        "1 failed, 2 passed"
    )
    result = _run_formatter(agate_assets, bash, run_cli, "go-test.sh", output, 1)
    data = _json(result)
    assert data["failed"] == 1
    assert any("foo::test_bar" in str(x) for x in data["failed_tests"])


def test_fmt_11_generic_tap_passed_failed_contains(agate_assets, run_cli, bash):
    output = "TAP version 13\nok 1 - test alpha\nok 2 - test beta\nnot ok 3 - test gamma"
    result = _run_formatter(agate_assets, bash, run_cli, "generic-tap.sh", output, 1)
    data = _json(result)
    assert data["passed"] == 2
    assert data["failed"] == 1
    assert any("test gamma" in str(x) for x in data["failed_tests"])


def test_fmt_12_generic_junit_xml_total_failed_errors_passed(agate_assets, run_cli, bash):
    output = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuite name="suite" tests="3" failures="1" errors="1" skipped="0">\n'
        '<testcase name="test_one" classname="MyClass"/>\n'
        '<testcase name="test_two" classname="MyClass"><failure message="fail">expected true</failure></testcase>\n'
        '<testcase name="test_three" classname="MyClass"><error message="err">exception</error></testcase>\n'
        "</testsuite>"
    )
    result = _run_formatter(agate_assets, bash, run_cli, "generic-junit-xml.sh", output, 1)
    data = _json(result)
    assert data["total"] == 3
    assert data["failed"] == 1
    assert data["errors"] == 1
    assert data["passed"] == 1


def test_bdd_35f_pytest_name_errors_field(agate_assets, run_cli, bash):
    output = "ERROR tests/test_x.py - NameError: name 'compute' is not defined\n1 error"
    result = _run_formatter(agate_assets, bash, run_cli, "pytest.sh", output, 2)
    data = _json(result)
    assert len(data["name_errors"]) == 1


# ---- 大输出承载能力（RM-AG0077 子批 D，2026-09-29）----
#
# 缺陷形态（实测复现）：formatter 第 5-6 行 `OUTPUT="$(cat)"; export OUTPUT` 把整份
# 测试输出经**环境变量**交给 python3。本仓前端全量输出约 1.5 MB，超 execve 的
# MAX_ARG_STRLEN(131072) 逾 11 倍 → `参数列表过长`（E2BIG）→ formatter exit 126 →
# agate_common.run_test_with_formatter 回退 `_fallback_json(raw_output=全量)` →
# check-tdd-red 命中「exit_code==2 且 raw_output 含 matching」的 A 类分支 →
# **误判为假红灯**（exit 1）；且 ci-gate-backstop 对 tdd_exit==1 判 FAIL ⇒
# 本仓任何前端任务的 P3 在 CI 上都会被误判。
#
# 同族扫描：**6 个 formatter 全部**是同一形态（不止被报告的 vitest.sh）——
# 其中 5 个真的读 output，`generic-exit-only.sh` 不读却照样 export（即"白导出"，
# 但足以让 python3 的 execve 失败）。故本组测试覆盖全部 6 个。

_FORMATTERS_ALL = (
    "generic-exit-only.sh",
    "generic-junit-xml.sh",
    "generic-tap.sh",
    "go-test.sh",
    "pytest.sh",
    "vitest.sh",
)

# ≈1.83 MB：远超 MAX_ARG_STRLEN，量级与"本仓前端全量输出"同档
_LARGE_OUTPUT = "Tests  3 failed\n" + ("x" * 60 + "\n") * 30000 + "Tests  7 passed\n"


@pytest.mark.windows_smoke
@pytest.mark.parametrize("formatter", _FORMATTERS_ALL)
def test_fmt_large_output_survives_exec_arg_limit(agate_assets, bash, run_cli, formatter):
    """6 个 formatter 均须承载 ≥1.5MB 输出（不得因 E2BIG 崩掉）。

    判据：大输入下 exit 0 且 stdout 仍是可解析 JSON、exit_code 原样透传。
    """
    result = _run_formatter(agate_assets, bash, run_cli, formatter, _LARGE_OUTPUT, 2)
    assert result.returncode == 0, (
        f"{formatter} 未承载大输出（returncode={result.returncode}）：{result.stderr[:300]}"
    )
    assert _json(result)["exit_code"] == 2


def test_fmt_large_output_content_actually_parsed(agate_assets, bash, run_cli):
    """大输入下内容仍被**真正解析**——防「跳过解析也算通过」的假绿。

    负向对照意图：只断言"没崩"不足以证明输出送达了 python（丢弃输出后返回空
    JSON 同样"不崩"）。故此处断言解析出的计数与构造输入一致。
    """
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", _LARGE_OUTPUT, 1)
    data = _json(result)
    assert data["failed"] == 3
    assert data["passed"] == 7
    assert data["total"] == 10


# ---- 超长单行不得触发二次方退化（RM-AG0077 子批 D 连带发现）----
#
# 修好 E2BIG 后，输出**第一次真正到达 python**，随即暴露 5 处 `.*(?:X).*` 的
# 二次方退化（vitest/go-test/pytest 三个 formatter）：`.*` 在每个起点向前找 X → O(n²)。
# 实测量级：32KB 单行 2.1s（2× 尺寸 → 4× 耗时）⇒ 本仓 1.8MB 单行 ≈1.8 小时。
# 更糟的是 agate_common.run_test_with_formatter 调 formatter **没设超时**，
# 挂起即 gate 永久卡死（commit 卡住）。
#
# 判据分两层：① 内容仍被**正确解析**（防"改成跳过扫描"的假绿）；② 有界耗时。

_ONE_LONG_LINE = 150000  # 单行 150KB（> E2BIG 阈值，故旧 env 版本会先崩，见上组测试）


def test_fmt_single_long_line_marker_still_detected(agate_assets, bash, run_cli):
    """超长单行内的语法错误标记仍须被检出（验证逐行扫描未破坏「整行匹配」语义）。"""
    payload = "x" * _ONE_LONG_LINE + " SyntaxError: boom\n"
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", payload, 1)
    data = _json(result)
    assert len(data["syntax_errors"]) == 1
    # message 是**整行** strip 后的内容（与旧 `.*(?:X).*` 的 m.group(0).strip() 一致）
    assert data["syntax_errors"][0]["message"].endswith("SyntaxError: boom")


def test_fmt_single_long_line_is_linear_not_quadratic(agate_assets, bash, run_cli):
    """超长单行须**有界耗时**完成——二次方实现下本用例会超时（150KB ≈ 46s）。"""
    import time

    payload = "x" * _ONE_LONG_LINE + "\n" + "y" * _ONE_LONG_LINE + "\n"
    t0 = time.time()
    result = _run_formatter(agate_assets, bash, run_cli, "vitest.sh", payload, 0)
    elapsed = time.time() - t0
    assert _json(result)["exit_code"] == 0
    assert elapsed < 10, f"疑似二次方退化：150KB×2 单行耗时 {elapsed:.1f}s（线性实现应 <1s）"


# ---- formatter 挂起必须有界（RM-AG0077 子批 D 连带发现）----
#
# agate_common.run_test_with_formatter 调 formatter 时**未设 timeout** ——
# 一旦 formatter 挂起（上面那组二次方退化就是真实触发路径：1.8MB 单行 ≈1.8 小时），
# gate 会**永久卡死**（commit 卡住，无任何输出）。
# 设计：复用既有失败路径——超时即降级 `_fallback_json(raw_output=…)`，
# 与「formatter 退出非 0 / 无法启动」同语义，不新增分支。
# 超时秒数可由 `AGATE_FORMATTER_TIMEOUT` 覆盖（沿用仓库 `AGATE_*` env 惯例）。


def test_formatter_hang_is_bounded_not_infinite(python_exe, run_cli, agate_scripts, tmp_path):
    """假 formatter 睡 8s；设 AGATE_FORMATTER_TIMEOUT=2 ⇒ 须在 ~2s 内降级返回。

    负向对照：未加超时兜底时本用例耗时≈8s（假 formatter 睡满）且无 raw_output ⇒ 失败。
    """
    import time

    hang_fmt = tmp_path / "hang.sh"
    hang_fmt.write_text("#!/usr/bin/env bash\nsleep 8\n", encoding="utf-8")

    code = (
        "from agate_common import run_test_with_formatter;"
        f"print(run_test_with_formatter('echo x', {str(hang_fmt)!r}, timeout_secs=10))"
    )
    t0 = time.time()
    result = run_cli(
        python_exe, "-c", code,
        env={"PYTHONPATH": str(agate_scripts), "AGATE_FORMATTER_TIMEOUT": "2"},
    )
    elapsed = time.time() - t0

    assert result.returncode == 0, result.output[:400]
    assert "raw_output" in result.stdout, f"未降级到既有失败路径：{result.stdout[:300]}"
    assert elapsed < 6, f"formatter 挂起未被超时兜底：{elapsed:.1f}s"


def test_fmt_works_with_readonly_tmpdir(agate_assets, bash, run_cli, tmp_path):
    """formatter **不得依赖可写 TMPDIR**（受限沙箱：`/tmp` 只读）。

    回归来历（TAG0039 独立评审发现）：本批修 E2BIG 的**第一版**改用 `mktemp` 经临时文件
    传递，在只读 `TMPDIR` 下 `mktemp` 失败 + `set -e` → formatter `exit 1` → 上游回退
    `raw_output` → **复活了本批正要消灭的 A 类假红灯路径**（HEAD 原版在同样条件下反而
    `exit 0`）。而本机 `AGENTS.md` 已登记「受限 harness：`/tmp` 只读」，非纯理论。
    现实现改为**数据经 fd 3 直连 python 的 stdin**，无临时文件、无 TMPDIR 依赖。

    （Windows 上 chmod 不产生真实只读语义，本用例退化为普通调用，无害。）
    """
    ro = tmp_path / "readonly_tmp"
    ro.mkdir()
    ro.chmod(0o555)
    payload = "Tests  3 failed\nTests  7 passed\n"
    result = run_cli(
        bash, str(agate_assets / "formatters" / "vitest.sh"), "2",
        input=payload, env={"TMPDIR": str(ro)},
    )
    assert result.returncode == 0, f"只读 TMPDIR 下 formatter 失败：{result.stderr[:250]}"
    data = _json(result)
    assert data["failed"] == 3, f"只读 TMPDIR 下未能解析内容：{result.stdout[:200]}"
    assert data["passed"] == 7
