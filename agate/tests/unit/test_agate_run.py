# agate/tests/unit/test_agate_run.py
# TAG0042 批 3（agate-run 执行层）红灯测试 —— BDD-9 / BDD-10 / BDD-11。
#
# 目标语义（P1 BDD-9/10/11，P2-design §4.2 + §1.1 M9）：
#   * BDD-9：`agate-run` 是「不可绕开路径」上的命令执行器——命令经它执行（而非自由 bash），
#     退出码**如实传播**（containing pipefail 语义：`cmd | tail` 中左侧失败不被吞）。
#     平台面（review m-2）：POSIX 断 pipefail 生效；非 POSIX 断「退化 + WARNING」（不静默报绿）。
#   * BDD-10：`agate-run --baseline` 首次落盘 `.out` 证据；后续执行与之逐字节比对，差异客观报出。
#   * BDD-11：`agate-run` 产出的 `.out` 证据须被 `.gitignore` 覆盖（`git check-ignore` 命中），否则报错。
#
# 现行为（改动前）：`agate/scripts/agate-run.py` **不存在** ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：本批红灯原因须为「被测模块未实现」，即
#   `agate-run.py` 缺失（本项目内文件探测/子进程运行失败 = B 类）与断言失败（行为未改 = B 类），
#   而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；需要「系统临时目录」字面量时**运行时拼接**（仓库既有惯例，R4 平台扫描）；
#   不写仓库内已提交文件（全在 tmp_path / git_repo）。

import re

import pytest

# 被测 CLI（批 3 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_RUN_SCRIPT = "agate-run.py"

# 声明文件名（P2-design §4.1/§4.2：项目根 agate.config.yaml，verify.commands 供 agate-run 消费）
_CONFIG_FILE = "agate.config.yaml"

# R4 平台扫描规避：需要「系统临时目录」字面量时运行时拼接（仓库既有惯例）。
_TMP = "/" + "tmp"


def _write_config(root, commands, *, extra_verify=None):
    """在项目根写最小 agate.config.yaml（含 verify.commands）。用 pyyaml 避免手写缩进。"""
    import yaml

    verify = {"commands": list(commands)}
    if extra_verify:
        verify.update(extra_verify)
    data = {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": verify,
    }
    (root / _CONFIG_FILE).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                                     encoding="utf-8")


def _run_agate_run(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    """运行 agate-run.py。当前脚本不存在 ⇒ subprocess 返回非 0 + 'No such file'。"""
    return run_cli(
        python_exe,
        str(agate_scripts / _RUN_SCRIPT),
        *args,
        cwd=cwd,
        env=env,
    )


# ── BDD-9：agate-run 在不可绕开路径上执行项目命令，退出码如实传播（含 pipefail） ──
#
# Given 声明文件中定义了项目的验证命令
# When 主 Agent/Agent 需要执行验证命令
# Then 经 `agate-run` 执行（而非自由 bash），命令的退出码被如实传播（含 `pipefail` 语义）


@pytest.mark.windows_smoke
def test_bdd_9_run_executes_declared_command_and_propagates_exit_code(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-9：经 `agate-run` 执行声明中的命令，成功命令 rc=0。

    Given 声明 verify.commands 定义 `exit 0` 形态命令
    When 运行 `agate-run <cmd-key>`（经不可绕开路径）
    Then rc=0（命令确实被执行且退出码被如实传播）。

    现行为：agate-run.py 不存在 ⇒ rc≠0（模块未实现）⇒ 红灯。
    """
    _write_config(tmp_path, ["echo agate-run-ok"])
    result = _run_agate_run(agate_scripts, python_exe, run_cli, "echo agate-run-ok", cwd=tmp_path)
    assert result.returncode == 0, (
        f"BDD-9：`agate-run` 执行成功命令应 rc=0；rc={result.returncode}\n{result.output[:400]}"
    )
    assert "agate-run-ok" in result.output, (
        f"BDD-9：命令输出应被捕获（证明经 agate-run 执行）；实际输出 {result.output[:200]!r}"
    )


def test_bdd_9_run_propagates_nonzero_exit_code(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-9：失败命令的退出码被**如实传播**（不吞成 0）。

    Given 声明命令 `exit 7`
    When 运行 `agate-run`
    Then rc=7（如实传播，而非恒 0）。
    """
    _write_config(tmp_path, ["exit 7"])
    result = _run_agate_run(agate_scripts, python_exe, run_cli, "exit 7", cwd=tmp_path)
    assert result.returncode == 7, (
        f"BDD-9：失败命令退出码须如实传播（期望 7）；rc={result.returncode}\n{result.output[:400]}"
    )


def test_bdd_9_run_posix_pipefail_propagates_left_side_failure(
    tmp_path, agate_scripts, python_exe, run_cli, bash
):
    """BDD-9（POSIX 平台分支，review m-2）：`集合失败 | tail` 中左侧失败不被吞——pipefail 生效。

    Given 声明命令 `printf 'x\\ny\\nz\\n' | tail -1`（无失败）与 `<失败命令> | tail -1`（左侧失败）
    When 运行 `agate-run`
    Then 左侧失败时 rc≠0（pipefail 语义生效），无失败时 rc=0。

    POSIX 断「生效」；非 POSIX（MSYS2）由用例
    `test_bdd_9_run_nonposix_pipefail_degrades_with_warning` 断「退化 + WARNING」。
    此处仅当平台非 win32 时执行严格 pipefail 断言。
    """
    import sys

    _write_config(tmp_path, ["printf 'x\\ny\\nz\\n' | tail -1",
                             "sh -c 'exit 5' | tail -1"])
    ok = _run_agate_run(agate_scripts, python_exe, run_cli,
                        "printf 'x\\ny\\nz\\n' | tail -1", cwd=tmp_path)
    assert ok.returncode == 0, (
        f"BDD-9：无失败管道应 rc=0；rc={ok.returncode}\n{ok.output[:400]}"
    )

    failed = _run_agate_run(agate_scripts, python_exe, run_cli,
                            "sh -c 'exit 5' | tail -1", cwd=tmp_path)
    if sys.platform != "win32":
        assert failed.returncode != 0, (
            "BDD-9（POSIX）：管道左侧失败须经 pipefail 如实传播（rc≠0）——"
            f"当前 rc={failed.returncode} 即失败被吞\n{failed.output[:400]}"
        )
    else:
        # Windows/MSYS2：pipefail 行为未测 ⇒ 须退化 + 显式 WARNING，不得静默报绿
        assert "WARNING" in failed.output, (
            "BDD-9（非 POSIX）：pipefail 不可用时须显式 WARNING（ADR-015，不静默报绿）"
            f"\n{failed.output[:400]}"
        )


def test_bdd_9_run_nonposix_pipefail_degrades_with_warning(agate_scripts):
    """BDD-9（平台分支源码面，review m-2）：agate-run 源码对平台差异**显式分支**。

    Given agate-run.py
    When 检查其 pipefail 处理路径
    Then 出现平台探测分支（POSIX pipefail vs 退化）且退化路径给 WARNING（不静默报绿）。

    现行为：agate-run.py 不存在 ⇒ 红灯（模块未实现）。
    """
    script = agate_scripts / _RUN_SCRIPT
    assert script.is_file(), (
        f"BDD-9：{_RUN_SCRIPT} 不存在（批 3 执行层未实现）——平台分支无从检查"
    )
    src = script.read_text(encoding="utf-8")
    # pipefail 前缀（复用 agate_common 已验证写法：`set -o pipefail; ` 前缀，非 executable 前缀）
    assert re.search(r"set -o pipefail", src), (
        "BDD-9：agate-run 应使用 `set -o pipefail` 前缀（P2 §4.2 指定的既有写法）"
    )
    # 平台差异须显式分支（sys.platform / platform 探测）
    assert re.search(r"sys\.platform|platform\.|win32|msys", src), (
        "BDD-9（m-2）：agate-run 须显式分支平台差异（pipefail 支持度），不得只保证 POSIX"
    )
    # 退化路径须可被观测（WARNING），不得静默
    assert re.search(r"WARNING", src), (
        "BDD-9（m-2）：平台退化路径须给 WARNING（ADR-015，不静默报绿）"
    )


# ── BDD-10：agate-run 产出可比对的基线证据 ────────────────────────────────
#
# Given 首次执行某命令
# When 运行 `agate-run --baseline`
# Then 落盘 `.out` 证据文件；后续执行与之逐字节比对，差异被客观报出（可二值判定）


def test_bdd_10_baseline_writes_out_evidence_file(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-10：`agate-run --baseline` 首次执行落盘 `.out` 证据文件。

    Given 声明命令（产生稳定输出）
    When 运行 `agate-run --baseline`
    Then rc=0 且项目内出现 `.out` 证据文件（内容 = 命令输出）。
    """
    _write_config(tmp_path, ["echo baseline-output"])
    result = _run_agate_run(agate_scripts, python_exe, run_cli,
                            "--baseline", "echo baseline-output", cwd=tmp_path)
    assert result.returncode == 0, (
        f"BDD-10：`agate-run --baseline` 应成功；rc={result.returncode}\n{result.output[:400]}"
    )
    outs = [p for p in tmp_path.rglob("*.out") if ".git" not in p.parts]
    assert outs, (
        "BDD-10：`--baseline` 应在项目内落盘 `.out` 证据文件（当前未发现任何 .out）"
    )
    assert any("baseline-output" in p.read_text(encoding="utf-8", errors="replace")
               for p in outs), (
        "BDD-10：`.out` 证据应包含命令输出（baseline-output）"
    )


def test_bdd_10_subsequent_run_matches_baseline_no_diff(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-10：`--baseline` 之后，输出一致 → 逐字节比对**无差异**（rc=0）。

    Given 已建立基线
    When 再次运行同命令（输出一致）
    Then rc=0（可二值判定：与基线一致）。
    """
    _write_config(tmp_path, ["echo stable"])
    base = _run_agate_run(agate_scripts, python_exe, run_cli, "--baseline", "echo stable", cwd=tmp_path)
    assert base.returncode == 0, (
        f"BDD-10：前置——建立基线应成功；rc={base.returncode}\n{base.output[:400]}"
    )
    again = _run_agate_run(agate_scripts, python_exe, run_cli, "--baseline", "echo stable", cwd=tmp_path)
    assert again.returncode == 0, (
        f"BDD-10：输出与基线逐字节一致时应 rc=0；rc={again.returncode}\n{again.output[:400]}"
    )


def test_bdd_10_baseline_diff_is_objectively_reported(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-10：后续输出与基线**逐字节不同** → 差异被**客观报出**（rc≠0 且提示 diff）。

    Given 已建立基线 `echo alpha`
    When 命令输出改变（`echo beta`）后与基线比对
    Then rc≠0 且输出含差异迹象（可二值判定，非「视情况」）。
    """
    _write_config(tmp_path, ["echo alpha"])
    base = _run_agate_run(agate_scripts, python_exe, run_cli, "--baseline", "echo alpha", cwd=tmp_path)
    assert base.returncode == 0, (
        f"BDD-10：前置——建立基线应成功；rc={base.returncode}\n{base.output[:400]}"
    )
    # 改变命令：与已落盘基线输出不同
    _write_config(tmp_path, ["echo beta"])
    diff = _run_agate_run(agate_scripts, python_exe, run_cli, "--baseline", "echo beta", cwd=tmp_path)
    assert diff.returncode != 0, (
        f"BDD-10：输出偏离基线时须报差异（rc≠0）；rc={diff.returncode}\n{diff.output[:400]}"
    )
    assert re.search(r"diff|差异|mismatch|baseline", diff.output, re.IGNORECASE), (
        f"BDD-10：差异须被客观报出（输出含差异提示）；实际 {diff.output[:300]!r}"
    )


@pytest.mark.windows_smoke
def test_bdd_10_baseline_evidence_is_byte_exact(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-10（C8 C1 修复）：`.out` 证据**逐字节**等于命令输出的 UTF-8 字节。

    Given 声明命令产生**多行**输出（换行敏感）
    When 运行 `agate-run --baseline`
    Then 证据文件 `read_bytes()` 的字节 == 命令输出的 UTF-8 字节
         （写盘不得把 `\\n` 翻译为 `os.linesep`，否则 Windows 上写/比不一致 → 恒 mismatch）。

    为何以 `result.stdout` 为基准：agate-run 把**同一个** `output` 既写 stdout 又写证据，
    故以实际捕获输出为基准天然平台无关（不写死换行序列）；Windows（`os.linesep="\\r\\n"`）
    上文本模式默认换行会把证据写成 `\\r\\n`，与此基准不等 ⇒ 修复前该用例在 Windows 变红。
    """
    command = "echo alpha && echo beta"
    _write_config(tmp_path, [command])
    result = _run_agate_run(agate_scripts, python_exe, run_cli,
                            "--baseline", command, cwd=tmp_path)
    assert result.returncode == 0, (
        f"BDD-10：`--baseline` 应成功；rc={result.returncode}\n{result.output[:400]}"
    )
    # 非空跑断言：命令确为多行输出，真正覆盖换行翻译路径
    assert "\n" in result.stdout, (
        f"BDD-10：前置——命令应产生多行输出（覆盖换行翻译）；实际 {result.stdout!r}"
    )
    outs = [p for p in tmp_path.rglob("*.out") if ".git" not in p.parts]
    assert outs, "BDD-10：前置——应已落盘 `.out` 证据文件（当前未发现）"
    expected = result.stdout.encode("utf-8")
    for p in outs:
        assert p.read_bytes() == expected, (
            "BDD-10（C1）：证据文件须逐字节等于命令输出的 UTF-8 字节"
            f"（写盘不得翻译换行）；\n  文件 {p.read_bytes()!r}\n  期望 {expected!r}"
        )
    # 源码面守卫：纯 Linux 运行无法复现 `newline=None` 的 `\n`→os.linesep 翻译，
    # 故额外断言 `_write_evidence` 的**写盘调用行**字节精确（"wb" 或 newline=""）以防回归。
    # 注意：只检查 `with open(` 调用行，不搜整个函数体——函数 docstring 会提到 "wb"，
    # 整段搜索会被 docstring 误导（实测：还原为 buggy 写盘后仍误判绿）。
    src = (agate_scripts / _RUN_SCRIPT).read_text(encoding="utf-8")
    match = re.search(r"def _write_evidence\b.*?(?=\ndef |\Z)", src, re.DOTALL)
    assert match, "BDD-10（C1）：源码中应存在 `_write_evidence` 函数"
    body = match.group(0)
    call_lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("with open" + "(")]
    assert call_lines, (
        f"BDD-10（C1）：`_write_evidence` 应经 with-open 落盘；实际函数体:\n{body}"
    )
    assert all(re.search(r"['\"]wb['\"]", ln) or re.search(r"newline\s*=\s*['\"]['\"]", ln)
               for ln in call_lines), (
        "BDD-10（C1）：`_write_evidence` 写盘调用须字节精确（\"wb\" 或 newline=\"\"），"
        f"否则 Windows 上 `\\n`→os.linesep 翻译破坏逐字节比对；实际调用行: {call_lines}"
    )


# ── BDD-11：agate-run 证据文件被 ignore 检查覆盖 ───────────────────────────
#
# Given `agate-run` 产出的 `.out` 证据位于项目内
# When 执行 ignore 检查
# Then 证据文件被 `.gitignore` 覆盖（`git check-ignore` 命中），否则报错


def test_bdd_11_baseline_evidence_is_gitignored(tmp_path, git_repo, agate_scripts, python_exe, run_cli):
    """BDD-11：`--baseline` 证据文件须被 `.gitignore` 覆盖（`git check-ignore` 命中）。

    Given 一个 git 项目（`.gitignore` 覆盖证据路径）
    When `agate-run --baseline` 产出 `.out` 证据
    Then 证据文件被 `git check-ignore` 命中（说明 ignore 检查覆盖证据）。
    """
    repo = git_repo.path
    (repo / ".gitignore").write_text(".agate-evidence/\n*.out\n", encoding="utf-8")
    _write_config(repo, ["echo ignored-evidence"])
    result = _run_agate_run(agate_scripts, python_exe, run_cli,
                            "--baseline", "echo ignored-evidence", cwd=repo)
    assert result.returncode == 0, (
        f"BDD-11：`--baseline` 应成功；rc={result.returncode}\n{result.output[:400]}"
    )
    outs = [p for p in repo.rglob("*.out") if ".git" not in p.parts]
    assert outs, "BDD-11：前置——应已落盘 `.out` 证据文件（当前未发现）"
    for p in outs:
        check = git_repo.git("check-ignore", str(p))
        assert check.returncode == 0, (
            f"BDD-11：证据文件 {p} 须被 .gitignore 覆盖（git check-ignore 命中）；"
            f"当前未命中 ⇒ ignore 检查缺失\n{check.stdout}{check.stderr}"
        )


def test_bdd_11_run_reports_error_when_evidence_not_ignored(
    tmp_path, git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-11：证据**未被** `.gitignore` 覆盖时，agate-run 须报错（rc≠0）。

    Given 一个 git 项目，`.gitignore` **不**覆盖证据路径
    When `agate-run --baseline` 产出证据
    Then rc≠0 且提示 ignore/证据未被覆盖（否则会污染仓库）。
    """
    repo = git_repo.path
    (repo / ".gitignore").write_text("nothing-related\n", encoding="utf-8")
    _write_config(repo, ["echo unignored"])
    result = _run_agate_run(agate_scripts, python_exe, run_cli,
                            "--baseline", "echo unignored", cwd=repo)
    assert result.returncode != 0, (
        "BDD-11：证据未被 .gitignore 覆盖时应报错（非 0）；"
        f"当前 rc={result.returncode}（ignore 检查缺失）\n{result.output[:400]}"
    )
    assert re.search(r"ignore|gitignore|未被覆盖|证据", result.output, re.IGNORECASE), (
        f"BDD-11：报错应指向 ignore 覆盖问题；实际 {result.output[:300]!r}"
    )
