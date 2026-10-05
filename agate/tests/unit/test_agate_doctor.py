# agate/tests/unit/test_agate_doctor.py
# TAG0042 批 5（CI 与诊断）红灯测试 —— BDD-17。
#
# 目标语义（P1 BDD-17，P2-design §4.4 + §1.1 M14）：
#   * BDD-17：`agate-doctor` 诊断项目接入状态（声明文件 / hook / 版本解析 / 账本完整性等），
#     对异常项给出**可执行的修复指引**，且**成功退出码固定**。
#
# 现行为（改动前）：`agate/scripts/agate-doctor.py` **不存在** ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：红灯原因须为「被测模块未实现」——脚本文件缺失（B 类）
#   与断言失败（行为未改 = B 类），而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 写入隔离：只用 pytest `tmp_path` / 既有 `git_repo` fixture；**绝不写仓库内已提交文件**。
#   诊断脚本若会写台账（如 `installed-projects.json`），把 `AGATE_HOME` 钉到 tmp_path 隔离目录
#   （参照 test_agate_config.py 的 `_isolated_agate_env` 先例），确保测试期间无真实写入。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；不写仓库内已提交文件（全在 tmp_path / git_repo 内）。

import re

# 被测 CLI（批 5 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_DOCTOR_SCRIPT = "agate-doctor.py"

# 声明文件名（批 2 引入；doctor 的「声明文件」诊断对象）
_CONFIG_FILE = "agate.config.yaml"


def _isolated_agate_env(tmp_path, agate_root):
    """把 `AGATE_HOME` 钉到 tmp 隔离目录，避免诊断脚本写真实 `installed-projects.json` 台账。

    返回 env dict：`AGATE_HOME` = tmp 下独立目录（任何台账写入落此），
    `AGATE_ROOT` = 传入的协议根（避免解析链受环境干扰）。
    """
    isolated_home = tmp_path / "isolated-agate-home"
    isolated_home.mkdir(parents=True, exist_ok=True)
    return {
        "AGATE_HOME": str(isolated_home),
        "AGATE_ROOT": str(agate_root),
    }


def _run_doctor(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    """运行 agate-doctor.py。当前脚本不存在 ⇒ subprocess 返回非 0 + 'No such file'。"""
    return run_cli(
        python_exe,
        str(agate_scripts / _DOCTOR_SCRIPT),
        *args,
        cwd=cwd,
        env=env,
    )


# ── BDD-17：agate-doctor 诊断项目接入状态 ──────────────────────────────────
#
# Given 一个已接入/未接入的项目
# When 运行 `agate-doctor`
# Then 输出客观接入状态（声明文件、hook、版本解析、账本完整性等），
#      并对异常项给出可执行的修复指引；成功退出码固定


def test_bdd_17_doctor_script_exists(agate_scripts):
    """BDD-17：批 5 新增 `agate-doctor.py`（诊断项目接入状态）。

    Given 批 5 的实现对象
    When 检查脚本文件
    Then `agate-doctor.py` 存在。

    现行为：脚本不存在 ⇒ 红灯（模块未实现）。
    """
    script = agate_scripts / _DOCTOR_SCRIPT
    assert script.is_file(), f"BDD-17：{_DOCTOR_SCRIPT} 不存在（批 5 未实现）"


def test_bdd_17_doctor_reports_declaration_status(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：doctor 输出**声明文件**接入状态（客观值，可被消费）。

    Given 一个未接入的项目（无 `agate.config.yaml`）
    When 运行 `agate-doctor`
    Then 输出含「声明文件」维度的状态（存在/缺失）。

    现行为：agate-doctor.py 不存在 ⇒ 无任何诊断输出（模块未实现）⇒ 红灯。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"声明|config|agate\.config", result.output, re.IGNORECASE), (
        "BDD-17：doctor 须输出「声明文件」接入状态；"
        f"实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_reports_hook_status(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：doctor 输出 **git hook** 接入状态。

    Given 一个未接入的项目（无 pre-commit hook）
    When 运行 `agate-doctor`
    Then 输出含「hook」维度的状态。

    现行为：agate-doctor.py 不存在 ⇒ 红灯（模块未实现）。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"hook|钩子|pre-commit", result.output, re.IGNORECASE), (
        f"BDD-17：doctor 须输出 hook 接入状态；实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_reports_version_resolution(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：doctor 输出**版本解析**状态（当前项目解析到的协议版本）。

    Given 一个项目
    When 运行 `agate-doctor`
    Then 输出含「版本解析」维度的状态。

    现行为：agate-doctor.py 不存在 ⇒ 红灯（模块未实现）。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"版本|version|resolve", result.output, re.IGNORECASE), (
        f"BDD-17：doctor 须输出版本解析状态；实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_reports_ledger_integrity(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：doctor 输出**账本完整性**状态（append-only 哈希链）。

    Given 一个项目
    When 运行 `agate-doctor`
    Then 输出含「账本完整性」维度的状态。

    现行为：agate-doctor.py 不存在 ⇒ 红灯（模块未实现）。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"账本|ledger|events", result.output, re.IGNORECASE), (
        f"BDD-17：doctor 须输出账本完整性状态；实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_gives_repair_guidance_for_unintegrated_project(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：对**异常项**（未接入）给出**可执行的修复指引**。

    Given 一个未接入的项目（声明文件 / hook 均缺失 = 异常项）
    When 运行 `agate-doctor`
    Then 输出含可执行的修复指引（如「运行 … 接入」），而非只报状态不给动作。

    现行为：agate-doctor.py 不存在 ⇒ 红灯（模块未实现）。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"修复|建议|运行|执行|安装|setup|install|如何", result.output, re.IGNORECASE), (
        "BDD-17：对异常项须给出**可执行的修复指引**；"
        f"实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_reports_integrated_project(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17（已接入项目）：声明文件存在时，doctor 如实报告「已接入」。

    Given 一个已接入的项目（存在 `agate.config.yaml`）
    When 运行 `agate-doctor`
    Then 输出把声明文件维度判为存在（正向标识，非缺失）。

    现行为：agate-doctor.py 不存在 ⇒ 红灯（模块未实现）。
    """
    (git_repo.path / _CONFIG_FILE).write_text(
        "schema_version: 1\nproject:\n  language: go\n", encoding="utf-8"
    )
    git_repo.commit("add declaration")
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert re.search(r"存在|present|已接入|OK|✓", result.output, re.IGNORECASE), (
        "BDD-17：已接入项目的声明文件维度须报「存在」；"
        f"实际输出 {result.output[:300]!r}"
    )


def test_bdd_17_doctor_success_exit_code_fixed(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """BDD-17：doctor **成功退出码固定**（诊断完成即成功，退出码确定）。

    Given 一个项目
    When 运行 `agate-doctor`（诊断正常完成）
    Then 退出码固定为 0（诊断工具报告问题但自身执行成功，退出码不漂移）。

    现行为：agate-doctor.py 不存在 ⇒ rc≠0（模块未实现）⇒ 红灯。
    """
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)
    assert result.returncode == 0, (
        "BDD-17：doctor 成功完成时退出码须固定为 0；"
        f"当前 rc={result.returncode}\n{result.output[:400]}"
    )
