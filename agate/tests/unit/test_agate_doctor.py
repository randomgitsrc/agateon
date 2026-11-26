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

import os
import re

import pytest

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


@pytest.mark.windows_smoke
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


# 回归（2026-11-26）：诊断对象是**效力**，不是**存在性** ────────────────────
#
# 三处「报的是自己以为的状态，不是 gate 实际用的状态」：
#
# ① **hook 效力**：`.git/hooks/<name>` 是文件 ≠ git 会执行它。实测（本机）
#    三个 hook 权限 0644 时 git **静默忽略**并让 commit 成功（仅打印提示），
#    而 doctor 报「已安装」+「全部维度正常」。同类失效模式本仓已踩过两次（复制模式
#    装出 0644），但都只修了**产生端**（install-hook 补 chmod +x），**消费端无人检查**。
# ② **hook 位置**：写死 `<repo>/.git/hooks`。链接 worktree 的 `.git` 是**文件**、
#    `core.hooksPath` 可覆盖——两种情形下 git 用的都不是这个目录。同仓
#    `agate_common.git_hooks_dir()` 早已用 `git rev-parse --git-path hooks` 解决。
# ③ **版本解析**：报「脚本自身所在的 AGATE_ROOT」，不跑解析链。声明未安装时
#    gate 实际回退 current，doctor 却把声明值当事实印出来。
#
# 断言一律落在**维度行的判定**与**与独立 oracle 的一致性**上（不用宽泛文本包含）。

_DIM_RE = re.compile(r"^\[(OK|!!)\]\s+(.*)$")


def _dim_line(output, keyword):
    """取某一维度行（`[OK] …` / `[!!] …`），按关键字定位维度。返回 (ok, 行文本)。"""
    for line in output.splitlines():
        m = _DIM_RE.match(line)
        if m and keyword in m.group(2):
            return m.group(1) == "OK", line
    raise AssertionError(f"未找到含 {keyword!r} 的维度行；输出为 {output[:600]!r}")


def _install_hooks(target_dir, mode):
    """在指定目录写三个 hook（内容故意 exit 1），并设权限位。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in ("pre-commit", "commit-msg", "pre-push"):
        hook = target_dir / name
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        os.chmod(hook, mode)
    return target_dir


def _write_config(project_root):
    """写一份合法声明，让「声明文件」维度为 OK——隔离出被测维度。"""
    (project_root / _CONFIG_FILE).write_text(
        "schema_version: 1\nproject:\n  language: go\n", encoding="utf-8"
    )


def test_doctor_reports_broken_when_hooks_not_executable(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """hook 全在位但**不可执行** ⇒ 必须判异常，且不得结论「全部维度正常」。

    Given 三个 hook 都在 git 的 hooks 目录，但权限 0644（git 静默忽略）
    When 运行 `agate-doctor`
    Then hook 维度为 `[!!]`，输出指明执行位，且**不出现**「全部维度正常」。

    修前实况：`[OK] hook: 已安装（pre-commit, commit-msg, pre-push）` +
    `全部维度正常（已接入）。`——同一环境下 `git commit` 成功且提示「钩子被忽略」。
    """
    if os.name == "nt":
        pytest.skip("Windows 无 POSIX 执行位语义（git 不使用该判据）")
    _write_config(git_repo.path)
    _install_hooks(git_repo.path / ".git" / "hooks", 0o644)
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    ok, line = _dim_line(result.output, "hook")
    assert not ok, f"hook 不可执行时须判异常，实际 {line!r}"
    assert re.search(r"不可执行|执行位|chmod", line), (
        f"须指明失效原因是执行位（而非笼统报错），实际 {line!r}"
    )
    assert "全部维度正常" not in result.output, (
        f"有维度异常时不得输出「全部维度正常」；实际输出 {result.output[:500]!r}"
    )


def test_doctor_executable_hooks_stay_ok(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """反向守护：hook 可执行 ⇒ 仍判 OK（别把修复做成永远报 Broken）。

    Given 三个 hook 都在且权限 0755
    When 运行 `agate-doctor`
    Then hook 维度为 `[OK]`。
    """
    if os.name == "nt":
        pytest.skip("Windows 无 POSIX 执行位语义（git 不使用该判据）")
    _write_config(git_repo.path)
    _install_hooks(git_repo.path / ".git" / "hooks", 0o755)
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    ok, line = _dim_line(result.output, "hook")
    assert ok, f"hook 可执行时应判 OK（防误报），实际 {line!r}"


def test_doctor_uses_git_hooks_dir_under_core_hookspath(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """`core.hooksPath` 指向别处时须查**那个**目录（git 只看它）。

    Given `core.hooksPath=<tmp>/custom-hooks`，三个 hook 装在那里，`.git/hooks` 为空
    When 运行 `agate-doctor`
    Then hook 维度判 OK——与 git 实际行为一致（gate 生效）。

    修前实况：写死 `.git/hooks` ⇒ 报「缺失 pre-commit, commit-msg, pre-push」。
    """
    _write_config(git_repo.path)
    custom = _install_hooks(tmp_path / "custom-hooks", 0o755)
    r = git_repo.git("config", "core.hooksPath", str(custom))
    assert r.returncode == 0, r.stderr
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    ok, line = _dim_line(result.output, "hook")
    assert ok, (
        "core.hooksPath 下的 hook 生效时须判 OK（不得因写死 .git/hooks 误报缺失）；"
        f"实际 {line!r}"
    )


def test_doctor_uses_git_hooks_dir_in_linked_worktree(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """链接 worktree 里 `.git` 是**文件**：须问 git，而不是拼 `.git/hooks`。

    Given 主仓已装 hook，另建一个链接 worktree（`.git` 为文件、hook 共享主仓）
    When 在 worktree 里运行 `agate-doctor`
    Then hook 维度判 OK——修前报「未检测到 .git/hooks（非 git 仓库或未初始化）」。

    worktree 正是本仓 dogfooding 的标准工作目录，误报会直接误导维护者。
    """
    import shutil
    import subprocess

    _write_config(git_repo.path)
    _install_hooks(git_repo.path / ".git" / "hooks", 0o755)
    git_repo.commit("base")
    wt = tmp_path / "wt"
    add = subprocess.run(
        ["git", "-C", str(git_repo.path), "worktree", "add", "-q", str(wt), "-b", "doctor-wt"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if add.returncode != 0:
        pytest.skip(f"环境不支持 git worktree: {add.stderr.strip()[:200]}")
    try:
        assert (wt / ".git").is_file(), "前置：链接 worktree 的 .git 应是文件"
        env = _isolated_agate_env(tmp_path, agate_root)
        result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=wt, env=env)
        ok, line = _dim_line(result.output, "hook")
        assert ok, f"worktree 里 hook 生效，须判 OK；实际 {line!r}"
    finally:
        subprocess.run(
            ["git", "-C", str(git_repo.path), "worktree", "remove", "--force", str(wt)],
            capture_output=True, text=True, encoding="utf-8",
        )
        shutil.rmtree(wt, ignore_errors=True)


def test_doctor_version_reports_what_gate_actually_resolves(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """版本维度须报**解析链的结果**：声明未安装 ⇒ 回退 current 并如实告警。

    Given `.agate-version` 声明 `v0.0.0-not-installed`；`AGATE_HOME` 下装了一个 v9.9.9
          且 `current` 文本指针指向它
    When 运行 `agate-doctor`（不设 AGATE_ROOT，让解析链真正生效）
    Then ① 输出含「未安装」告警；② 报出的 AGATE_ROOT 是**实际会被 gate 用的**那个
         （fake home 下的 v9.9.9），而不是脚本自身所在的目录。

    修前实况：`AGATE_ROOT=<脚本自定位目录>` + 声明值原样打印，解析链根本没跑——
    声明未安装（实际回退 current）这一事实被完全掩盖。
    """
    home = tmp_path / "fake-agate-home"
    (home / "v9.9.9" / "scripts").mkdir(parents=True)
    (home / "v9.9.9" / "assets").mkdir(parents=True)
    (home / "current").write_text("v9.9.9", encoding="utf-8")
    (git_repo.path / ".agate-version").write_text(
        "agate: v0.0.0-not-installed\n", encoding="utf-8"
    )
    _write_config(git_repo.path)
    # 关键：**不**设 AGATE_ROOT（设了会短路解析链，测不到链行为）
    env = {
        "AGATE_HOME": str(home),
        "HOME": str(tmp_path / "fake-home"),
        "USERPROFILE": str(tmp_path / "fake-home"),
    }
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    _ok, line = _dim_line(result.output, "版本")
    assert re.search(r"未安装|回退", line), (
        f"声明未安装时须如实告警（与 agate-resolve 同口径），实际 {line!r}"
    )
    assert "v9.9.9" in line, (
        "须报**实际会被 gate 用的**版本根（回退后的 current），而不是声明值或脚本自定位目录；"
        f"实际 {line!r}"
    )


def test_doctor_version_matches_hook_resolution_when_chain_unavailable(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """解析链无结果时，doctor 须报 **hook 实际会用的** root，而不是「无可用 AGATE_ROOT」。

    Given `AGATE_HOME` 指向不存在的目录（current 链解析不出任何版本），
          `AGATE_ROOT` 也未设——即 `resolve_version_root()` 返回 root=None
    When 运行 `agate-doctor`
    Then 版本维度仍须给出一个**可用的** AGATE_ROOT，且**不是** `[!!] 无可用 AGATE_ROOT`。

    为什么（独立评审 C1）：gate 由 `resolve-entry.py` → `resolve_hook_root()` 定位，它比
    `resolve_version_root()` **多一层兜底**（脚本路径上溯 + 复制模式 `.agate-root`），故 hook
    恒有 root。doctor 若只用 `resolve_version_root`，会在这类环境里报「无可用 AGATE_ROOT」，
    而 gate 其实跑得动——**报的不是 gate 实际用的状态**，正是本批要消灭的缺陷的镜像。
    """
    env = {
        "AGATE_HOME": str(tmp_path / "definitely-no-such-home"),
        "HOME": str(tmp_path / "fake-home"),
        "USERPROFILE": str(tmp_path / "fake-home"),
    }
    env.pop("AGATE_ROOT", None)
    _write_config(git_repo.path)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    _ok, line = _dim_line(result.output, "版本")
    assert "无可用 AGATE_ROOT" not in line, (
        "解析链无结果不等于 gate 无 root——hook 有脚本路径上溯兜底，doctor 不得报「无可用」；"
        f"实际 {line!r}"
    )
    assert "AGATE_ROOT=" in line, f"须给出实际会用的 root，实际 {line!r}"


def test_doctor_uses_installed_hook_entry_for_fallback_root(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """兜底时须从**真实安装的 hook 入口**上溯，不得用 doctor 自身所在 checkout。

    Given 解析链无结果（`AGATE_HOME` 不存在），hooks 目录里的 pre-commit 是一个
          **指向别处安装根**的软链（模拟 `~/.agate/scripts/pre-commit-gate.sh`）
    When 运行 `agate-doctor`
    Then 报出的 AGATE_ROOT 是**该安装根上溯出来的**那个，而不是 doctor 自身所在的 checkout。

    为什么（独立评审 C1 残余）：原实现把 `<本 checkout>/scripts/resolve-entry.py` 喂给
    `resolve_hook_root`，上溯得到的是「doctor 住在哪个 checkout」——在 multi-worktree 下
    又是「把『我住哪』当『gate 用哪个』」的同一个错。
    """
    if os.name == "nt":
        pytest.skip("Windows 复制模式无软链语义（该场景按复制模式另论）")
    fake_install = tmp_path / "fake-install"
    (fake_install / "scripts").mkdir(parents=True)
    (fake_install / "assets").mkdir(parents=True)
    fake_entry = fake_install / "scripts" / "pre-commit-gate.sh"
    fake_entry.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(fake_entry, 0o755)

    hooks_dir = git_repo.path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    link = hooks_dir / "pre-commit"
    try:
        link.symlink_to(fake_entry)
    except (OSError, NotImplementedError):
        pytest.skip("环境不支持创建软链")
    _write_config(git_repo.path)

    env = {
        "AGATE_HOME": str(tmp_path / "definitely-no-such-home"),
        "HOME": str(tmp_path / "fake-home"),
        "USERPROFILE": str(tmp_path / "fake-home"),
    }
    env.pop("AGATE_ROOT", None)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    _ok, line = _dim_line(result.output, "版本")
    assert str(fake_install) in line, (
        "兜底上溯须基于真实安装的 hook 入口（软链目标），而不是 doctor 自身所在 checkout；"
        f"实际 {line!r}"
    )


def test_doctor_reports_broken_symlink_hook(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """断链的 hook 软链 ⇒ 报「断链」，不得报「缺失」（原因不同、修法不同）。

    Given hooks 目录里 pre-commit 是指向不存在目标的软链
    When 运行 `agate-doctor`
    Then hook 维度为 `[!!]` 且状态行含「断链」——修前 `is_file()` 为 False 会报「缺失」，
         掩盖「装过但目标已被删/移」这一真实原因。
    """
    if os.name == "nt":
        pytest.skip("Windows 复制模式无软链语义")
    _write_config(git_repo.path)
    hooks_dir = _install_hooks(git_repo.path / ".git" / "hooks", 0o755)
    dangling = hooks_dir / "commit-msg"
    dangling.unlink()
    try:
        dangling.symlink_to(tmp_path / "no-such-target")
    except (OSError, NotImplementedError):
        pytest.skip("环境不支持创建软链")
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    ok, line = _dim_line(result.output, "hook")
    assert not ok, f"断链 hook 须判异常，实际 {line!r}"
    assert "断链" in line, f"须报「断链」而非笼统「缺失」，实际 {line!r}"


def test_doctor_does_not_claim_hook_content_blocks(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """空文件 hook 会被 git 执行但**不阻断**：doctor 不得声称它「能拦」。

    Given 三个 hook 都是 0 字节且 0755（git 会执行，但什么都不做，commit 照常成功）
    When 运行 `agate-doctor`
    Then 判定为 OK，但措辞**限于「可执行」**，并显式声明不含「内容是否真能阻断」。

    边界（独立评审 A4）：doctor 能证明的是「git 会不会执行它」；内容层效力要跑一次真实
    提交才知道。把「执行」说成「生效/能拦」就是过度声称——正是本批要消灭的那类问题。
    """
    if os.name == "nt":
        pytest.skip("Windows 无 POSIX 执行位语义")
    _write_config(git_repo.path)
    hooks_dir = git_repo.path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("pre-commit", "commit-msg", "pre-push"):
        hook = hooks_dir / name
        hook.write_bytes(b"")
        os.chmod(hook, 0o755)
    env = _isolated_agate_env(tmp_path, agate_root)
    result = _run_doctor(agate_scripts, python_exe, run_cli, cwd=git_repo.path, env=env)

    ok, line = _dim_line(result.output, "hook")
    assert ok, f"空文件 hook 仍会被 git 执行，此维度判 OK 是合理的，实际 {line!r}"
    assert "可执行" in line, f"措辞须限于「可执行」，实际 {line!r}"
    assert "不含" in line and "阻断" in line, (
        "须显式声明不判断内容能否阻断（否则等于替 git 下了没验过的结论）；"
        f"实际 {line!r}"
    )


def test_doctor_stays_green_exit_when_agate_common_aborts(
    git_repo, agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """`agate_common` 以 `sys.exit()` 中止时，doctor 仍须**跑完四个维度**且 **rc=0**。

    Given `agate_common` 在 import 时即 `sys.exit(1)`（其缺 pyyaml 时的真实行为）
    When 运行 `agate-doctor`
    Then ① 退出码仍为 0（BDD-17「退出码固定」）；② 四个维度都打印了（不被截断）；
         ③ `SystemExit` 的原因被还原成可读文案，而不是裸的退出码。

    为什么（独立评审 N-1）：`agate_common` 缺 pyyaml 时用 `sys.exit(1)`，抛的是
    `SystemExit`——它**不是** `Exception` 的子类。原代码的 3 处 `except Exception` 全都接不住，
    于是第一个维度就把整个诊断打断：只打印两行标题、rc=1、四个维度一个都没出。
    这违反 BDD-17 的核心契约（诊断完成即 rc=0），也让「对异常项给出修复指引」完全失效。
    """
    # 精确复刻「缺 pyyaml」：一个在 import 时就 `sys.exit(1)` 的 agate_common。
    # 不能用 PYTHONPATH 放同名 stub（真模块同目录、优先级更高），也不能用 sitecustomize
    # （在 site 初始化阶段抛 SystemExit 会让解释器本身崩掉，测的就不是 doctor 了）。
    # 做法：由一个很小的启动器先把假模块塞进 sys.modules，再 runpy 跑 doctor。
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    (stub_dir / "agate_common.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    launcher = tmp_path / "launcher.py"
    launcher.write_text(
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(stub_dir)!r})\n"
        "sys.argv = ['agate-doctor.py']\n"
        f"runpy.run_path({str(agate_scripts / _DOCTOR_SCRIPT)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    _write_config(git_repo.path)
    # 关键：必须在 `.git/hooks` 放**可执行** hook。否则回退后走的是「缺失」分支，
    # 测不到「回退且看似齐全」这条——那正是 N-1 假绿的触发路径（二轮评审实测：
    # core.hooksPath 指向空目录时 git 真哑，而 doctor 报「已安装且可执行」）。
    hooks_dir = git_repo.path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("pre-commit", "commit-msg", "pre-push"):
        hook = hooks_dir / name
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        os.chmod(hook, 0o755)
    env = {
        "HOME": str(tmp_path / "fake-home"),
        "USERPROFILE": str(tmp_path / "fake-home"),
    }
    result = run_cli(python_exe, str(launcher), env=env, cwd=git_repo.path)

    assert result.returncode == 0, (
        "agate_common 中止不得让 doctor 自身失败（BDD-17 退出码固定）；"
        f"rc={result.returncode}\n{result.output[:500]}"
    )
    for dim in ("声明文件", "hook", "版本", "账本"):
        assert dim in result.output, (
            f"维度「{dim}」未被打印——诊断被 SystemExit 中途打断；"
            f"实际输出 {result.output[:600]!r}"
        )
    assert "code=1" in result.output or "pyyaml" in result.output, (
        "须给出可读的中止原因（而非裸退出码 '1'）；"
        f"实际 {result.output[:600]!r}"
    )
    # 账本维度不得在「审计没跑」时报 OK（二轮评审指出的本批新引入假绿）：
    # 解析不出任务目录 ≠ 没有任务目录，前者须判异常。
    _ok, ledger_line = _dim_line(result.output, "账本")
    assert not _ok, (
        "agate_common 不可用时账本审计根本没执行，不得报 OK——"
        f"「解析失败」与「无任务」必须分开；实际 {ledger_line!r}"
    )
    # hook 维度同理：agate_common 挂掉时查的是回退目录，无法确认 git 真正会用的目录
    # （core.hooksPath 可能指向别处），不得判 OK（二轮评审 N-1：实测该组合下 git 真哑而
    # doctor 报绿）。
    _hook_ok, hook_line = _dim_line(result.output, "hook")
    assert not _hook_ok, (
        "agate_common 不可用时报的是回退目录，无法确认效力，不得判 OK；"
        f"实际 {hook_line!r}"
    )
    # 修复指引不得循环：agate-setup.py / agate-resolve.py / check-events.py /
    # agate-config.py **都 import agate_common**，同环境下同样跑不起来（二轮评审 M-2
    # 指出这些分流逻辑此前无守护，变异 M9/M11 全绿）。
    for circular in ("agate-setup.py", "agate-resolve.py", "check-events.py", "agate-config.py"):
        assert circular not in result.output, (
            f"不得建议运行同样依赖 agate_common 的 {circular}（该建议在本环境下必然失败）；"
            f"实际输出 {result.output[:800]!r}"
        )
    # 声明维度的指引不得误指路到 YAML 语法：本场景真因是 agate_common 不可用，
    # 让人去改声明文件的语法是彻头彻尾的误导（二轮评审 M-2 / M11）。
    assert "YAML 语法" not in result.output, (
        "agate_common 不可用时不得把修复方向指向声明文件的 YAML 语法；"
        f"实际输出 {result.output[:800]!r}"
    )
    # 多维度共享同一根因时建议须去重（二轮评审 M-2 / M10）。
    assert result.output.count("先让 agate_common 可用") == 1, (
        "同一条建议只该出现一次（去重生效）；"
        f"实际出现 {result.output.count('先让 agate_common 可用')} 次：{result.output[:800]!r}"
    )


@pytest.mark.parametrize("code", [None, 3, "boom", 0])
def test_exc_note_handles_any_systemexit_code(code, agate_scripts):
    """`_exc_note` 对任意 `SystemExit.code` 都须给出可读文案，不得抛异常。

    Given `SystemExit` 的 code 为 None / 整数 / 字符串 / 0
    When 调用 `_exc_note`
    Then 返回含可行动信息的字符串（不抛异常，也不只是裸退出码）。

    为什么（二轮评审 M-3）：`sys.exit()` 允许任意 code（None → 默认 0、字符串 → 作为消息）。
    诊断文案若在某种 code 上抛异常，就把「诊断工具不崩」这条底线自己破了。
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("doctor_under_test", agate_scripts / _DOCTOR_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    note = module._exc_note(SystemExit(code))
    assert isinstance(note, str) and note, f"code={code!r} 须返回非空文案"
    assert "agate_common" in note, f"code={code!r} 的文案须指明是 agate_common 中止：{note!r}"
    assert "pyyaml" in note, f"code={code!r} 的文案须给出可行动的下一步：{note!r}"


def test_exc_note_passes_through_plain_exception(agate_scripts):
    """普通异常仍返回 `str(exc)`（不被 `SystemExit` 文案污染）。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("doctor_under_test2", agate_scripts / _DOCTOR_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._exc_note(ValueError("boom")) == "boom"
