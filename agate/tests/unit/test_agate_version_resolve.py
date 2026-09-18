# tests/unit/test_agate_version_resolve.py — agate-resolve.py 版本解析语义（resolve-chain 批次）
# 被测：agate/scripts/agate-resolve.py（TAG0008 新组件，P4 实现）。P3 阶段该模块不存在 → 全部红灯（B 类）。
# BDD 映射：BDD-9~14（resolve 语义）+ BDD-30（legacy 软链兜底）+ P2-review 测试缺口 1（终态 fail-closed）。
# 平台无关（AGENTS.md 测试约定）：
#   * 假 HOME 经 HOME+USERPROFILE env 指向 tmp_path（不碰真实 ~/.agate，不假设系统临时目录路径）
#   * current/latest 用文本指针（内容 = 目标名），Windows 复制模式指针形态，不假设 POSIX symlink
#   * BDD-30 的 legacy 软链场景：os.symlink 失败（Windows 无权限）→ pytest.skip 声明跳过
# Given 契约（测试数据即 P4 实现的输入约束）：
#   ~/.agate/<vX.Y.Z>/ 版本目录存在即视为"已安装"；current→latest→<版本目录名> 文本指针链。

import os
from pathlib import Path

import pytest


def _resolve_env(home):
    """无 AGATE_ROOT env + HOME/USERPROFILE 指向假 home（平台无关的 ~/.agate 定位）。"""
    return {"AGATE_ROOT": "", "HOME": str(home), "USERPROFILE": str(home)}


def _make_home(tmp_path, versions=("v0.43.0", "v0.44.0"), current="latest", latest="v0.44.0"):
    """构造假 ~/.agate 布局：版本目录（存在即已安装）+ current/latest 文本指针。"""
    home = tmp_path / "home"
    for v in versions:
        (home / ".agate" / v).mkdir(parents=True, exist_ok=True)
    (home / ".agate" / "latest").write_text(latest + "\n", encoding="utf-8")
    (home / ".agate" / "current").write_text(current + "\n", encoding="utf-8")
    return home


def _write_version_decl(project, version):
    (project / ".agate-version").write_text(f"agate: {version}\n", encoding="utf-8")


@pytest.mark.windows_smoke
def test_bdd_9_project_lock(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.43.0")

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.43.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.43.0" in result.output


def test_bdd_10_walk_up_from_cwd(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    root = tmp_path / "projroot"
    root.mkdir()
    _write_version_decl(root, "v0.43.0")
    subdir = root / "a" / "b"
    subdir.mkdir(parents=True)

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(subdir),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.43.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.43.0" in result.output


def test_bdd_11_no_decl_fallback_current(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)  # current→latest→v0.44.0
    project = tmp_path / "project"
    project.mkdir()

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.44.0" in result.output
    assert "current" in result.output


def test_bdd_11b_symlink_pointer_shows_actual_version(run_cli, python_exe, agate_scripts, tmp_path):
    """rev2 CRITICAL-1：软链指针布局下解析必须落到实际版本目录名（BDD-11 current 回退语义）。

    回归用例：`_resolve_pointer_chain` 先判 isdir 会把"软链→版本目录"短路，返回
    current/latest 路径本身，`_resolve_version_info` 的 version=basename 变成
    "current"/"latest" 而非实际版本号（agate-resolve 显示错误版本）。
    """
    home = tmp_path / "home"
    for v in ("v0.43.0", "v0.44.0"):
        (home / ".agate" / v).mkdir(parents=True, exist_ok=True)
    try:
        os.symlink("v0.44.0", str(home / ".agate" / "latest"))
        os.symlink("latest", str(home / ".agate" / "current"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，软链指针布局无法构建")

    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "AGATE_VERSION=v0.44.0" in result.output, "软链布局下版本号应为实际版本，而非 current/latest"


def test_bdd_12_env_override(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.43.0")
    custom = tmp_path / "custom-agate"
    custom.mkdir()

    env = _resolve_env(home)
    env["AGATE_ROOT"] = str(custom)
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=env,
    )
    assert result.returncode == 0
    assert str(custom.resolve()) in result.output


def test_bdd_13_declared_not_installed_fallback(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)  # v0.43.0/v0.44.0 已装，current→latest→v0.44.0
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.99.0")  # 未安装

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.99.0" in result.output  # 警告指出声明的未安装版本，不静默
    assert "未安装" in result.output


@pytest.mark.parametrize("content", ["random text\n", "foo: bar\n", ""])
def test_bdd_14_invalid_format_fallback(content, run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    (project / ".agate-version").write_text(content, encoding="utf-8")  # 空文件归入非法格式

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "格式" in result.output


@pytest.mark.windows_smoke
def test_bdd_30_legacy_symlink_direct_root(run_cli, python_exe, agate_scripts, tmp_path):
    # legacy 布局：~/.agate 是软链 → 旧 checkout 的 agate/ 子目录；无版本目录、无 current/latest 指针
    legacy = tmp_path / "legacy-checkout" / "agate"
    (legacy / "scripts").mkdir(parents=True)
    (legacy / "assets").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    try:
        os.symlink(str(legacy), str(home / ".agate"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，legacy 软链布局无法构建")

    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    legacy_root = str(Path(legacy).resolve())
    assert result.returncode == 0
    assert legacy_root in result.output


def test_resolve_terminal_failure_fail_closed(run_cli, python_exe, agate_scripts, tmp_path):
    """P2-review 测试缺口 1：无 current/latest/legacy 可用 root + 声明版本未装 → 终态 exit 非 0。

    hook 场景下该终态阻断 commit（薄壳 fail-closed 语义），绝不静默放行 gate。
    """
    home = tmp_path / "home"
    (home / ".agate").mkdir(parents=True)  # 无版本目录、无指针、非软链
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.99.0")

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    assert result.returncode != 0
    assert "v0.99.0" in result.output  # 失败非静默：警告指出声明的未安装版本


# ============================================================
# TAG0032 版本管理生命周期可用性批 — 断点二：元仓库 gap 修复（RM-AG0058 本体）
#   BDD-6 / BDD-7（1:1 映射 P1-requirements.md §3.2）
#   命名前缀 test_tag0032_bdd_N_（区分 TAG0008 既有 test_bdd_9..14/30）
#   被测行为由 P4 实现（决策 A1：agate_common._protocol_root helper + _resolve_version_info
#   两处调用）——P3 当前红灯（B 类：resolve 返回 vdir 而非 vdir/agate；helper 未实现）。
#   fixture 铁律（I-5）：_make_home_meta 严格「协议在 agate/ 子目录、vX/scripts/ 不存在」，
#   不用「根即协议」模拟 repo 代替；_make_home_rootproto 作 BDD-7 对照。
# ============================================================


def _make_home_meta(tmp_path, version="v0.50.0"):
    """元仓库形态隔离 HOME：~/.agate/<version>/agate/scripts/ 存在，<version>/scripts/ 不存在。"""
    home = tmp_path / "home"
    vdir = home / ".agate" / version
    (vdir / "agate" / "scripts").mkdir(parents=True)
    (vdir / "agate" / "rules").mkdir(parents=True)
    (vdir / "agate" / "rules" / ".keep").write_text("", encoding="utf-8")
    return home


def _make_home_rootproto(tmp_path, version="v0.50.0"):
    """「根即协议」形态隔离 HOME：~/.agate/<version>/scripts/ 直接存在。"""
    home = tmp_path / "home"
    (home / ".agate" / version / "scripts").mkdir(parents=True)
    return home


def _import_agate_common(agate_scripts):
    import importlib
    import sys as _sys

    p = str(agate_scripts)
    if p not in _sys.path:
        _sys.path.insert(0, p)
    return importlib.import_module("agate_common")


def test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """BDD-6：resolve 对元仓库形态版本目录返回协议子目录 vdir/agate，版本号不回归。"""
    home = _make_home_meta(tmp_path, "v0.50.0")
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.50.0")

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    assert result.returncode == 0
    expected_root = str((home / ".agate" / "v0.50.0" / "agate").resolve())
    assert f"AGATE_ROOT={expected_root}" in result.output, (
        "元仓库形态应返回 vdir/agate（协议子目录），而非 vdir"
    )
    assert "AGATE_VERSION=v0.50.0" in result.output, "版本号不回归（I-1）"


def test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """BDD-7：「根即协议」部署方解析语义不变（纯增量红线）。

    _protocol_root 探测序 1（vdir/scripts）先命中 → 返回 vdir，不进入 vdir/agate 分支；
    AGATE_VERSION 仍为 vX.Y.Z（与 BDD-6 对称）。
    """
    agate_common = _import_agate_common(agate_scripts)
    assert hasattr(agate_common, "_protocol_root"), (
        "决策 A1：agate_common 应新增 _protocol_root helper（P4 未实现）"
    )
    unit_vdir = tmp_path / "unit" / "v0.50.0"
    (unit_vdir / "scripts").mkdir(parents=True)
    assert agate_common._protocol_root(str(unit_vdir)) == str(unit_vdir), (
        "探测序 1：vdir/scripts 存在 → 返回 vdir 本身（根即协议零回归）"
    )

    home = _make_home_rootproto(tmp_path, "v0.50.0")
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.50.0")
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    assert result.returncode == 0
    expected_root = str((home / ".agate" / "v0.50.0").resolve())
    assert f"AGATE_ROOT={expected_root}" in result.output
    assert f"AGATE_ROOT={expected_root}/agate" not in result.output
    assert "AGATE_VERSION=v0.50.0" in result.output


# ============================================================
# DEBT0042：AGATE_HOME 基址 env 覆盖
#
# 动机：_resolve_version_info 原先硬编码 `base = os.path.expanduser("~/.agate")`，
# 测试只能靠重定向 HOME 才能隔离（现有用例即如此）。加 AGATE_HOME 后基址可直接注入，
# 既让测试不必动 HOME，也让「多版本根并存」等场景可在同一 HOME 下并行验证。
#
# 优先级契约（不可倒）：AGATE_ROOT（直接指定协议根）> AGATE_HOME（版本根基址）>
#   项目声明 > current 链 > legacy 软链兜底。AGATE_HOME 只换"版本根在哪"，不改层序。
# ============================================================


def _make_version_root(base, versions=("v0.43.0", "v0.44.0"), current="latest", latest="v0.44.0"):
    """在 base 下直接建版本根（版本目录 + current/latest 文本指针），返回 base。"""
    for v in versions:
        (base / v).mkdir(parents=True, exist_ok=True)
    (base / "latest").write_text(latest + "\n", encoding="utf-8")
    (base / "current").write_text(current + "\n", encoding="utf-8")
    return base


def test_debt0042_agate_home_overrides_base(run_cli, python_exe, agate_scripts, tmp_path):
    """AGATE_HOME 指定版本根基址 → current 链在该基址下解析（不读真实 ~/.agate）。

    用【不存在的 HOME】反向证明：若实现仍读 ~/.agate，则解析必然失败。
    """
    vroot = _make_version_root(tmp_path / "custom-root")
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": str(vroot),
            "HOME": str(tmp_path / "nonexistent-home"),
            "USERPROFILE": str(tmp_path / "nonexistent-home"),
        },
    )
    assert result.returncode == 0, f"AGATE_HOME 未被采纳：{result.output!r}"
    expected = str((vroot / "v0.44.0").resolve())
    assert f"AGATE_ROOT={expected}" in result.output
    assert "AGATE_VERSION=v0.44.0" in result.output


def test_debt0042_agate_home_project_declaration(run_cli, python_exe, agate_scripts, tmp_path):
    """AGATE_HOME 与项目声明共存：声明命中版本根内的已安装版本（层序不变）。"""
    vroot = _make_version_root(tmp_path / "custom-root")
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.43.0")
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": str(vroot),
            "HOME": str(tmp_path / "nonexistent-home"),
            "USERPROFILE": str(tmp_path / "nonexistent-home"),
        },
    )
    assert result.returncode == 0, f"AGATE_HOME + 项目声明未生效：{result.output!r}"
    assert f"AGATE_ROOT={(vroot / 'v0.43.0').resolve()!s}" in result.output
    assert "AGATE_VERSION=v0.43.0" in result.output


def test_debt0042_agate_root_takes_precedence_over_agate_home(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """优先级：AGATE_ROOT（直接指定协议根）> AGATE_HOME（版本根基址）。"""
    vroot = _make_version_root(tmp_path / "custom-root")
    direct = tmp_path / "direct-root"
    (direct / "scripts").mkdir(parents=True)
    (direct / "assets").mkdir(parents=True)
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        env={
            "AGATE_ROOT": str(direct),
            "AGATE_HOME": str(vroot),
            "HOME": str(tmp_path / "nonexistent-home"),
            "USERPROFILE": str(tmp_path / "nonexistent-home"),
        },
    )
    assert result.returncode == 0
    assert f"AGATE_ROOT={direct}" in result.output
    # 正向断言：确认走的是 AGATE_ROOT 分支（而非间接反证）
    assert "AGATE_REASON=AGATE_ROOT 环境变量覆盖" in result.output
    assert "AGATE_VERSION=" in result.output


def test_debt0042_agate_home_empty_string_equals_unset(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """AGATE_HOME="" 等同未设（走默认 ~/.agate 基址，由 HOME 重定向决定）。"""
    home = _make_home(tmp_path)
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": "",
            "HOME": str(home),
            "USERPROFILE": str(home),
        },
    )
    assert result.returncode == 0
    assert f"AGATE_ROOT={(home / '.agate' / 'v0.44.0').resolve()!s}" in result.output


def test_debt0042_agate_home_legacy_symlink(run_cli, python_exe, agate_scripts, tmp_path):
    """AGATE_HOME 指向 legacy 软链布局 → 第 4 层（软链兜底）在该基址下生效。"""
    real = tmp_path / "protocol-body"
    (real / "scripts").mkdir(parents=True)
    (real / "assets").mkdir(parents=True)
    # 版本根布局但其中是 legacy 软链（无 vX.Y.Z 目录/无指针）
    custom = tmp_path / "custom-home"
    custom.mkdir()
    link = custom / "body"
    try:
        os.symlink(str(real), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("该平台不支持符号链接（Windows 无权限）")
    # 需要 base 自身是软链才走 legacy 分支——把 AGATE_HOME 直接指向软链
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": str(link),
            "HOME": str(tmp_path / "nonexistent-home"),
            "USERPROFILE": str(tmp_path / "nonexistent-home"),
        },
    )
    assert result.returncode == 0, f"legacy 软链兜底未在 AGATE_HOME 下生效：{result.output!r}"
    assert "legacy" in result.output


def test_debt0042_agate_home_expanduser(run_cli, python_exe, agate_scripts, tmp_path):
    """AGATE_HOME 含 `~` → 按 HOME 展开（expanduser 语义）。"""
    home = _make_home(tmp_path)
    vroot = home / ".agate"
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": "~/.agate",
            "HOME": str(home),
            "USERPROFILE": str(home),
        },
    )
    assert result.returncode == 0, f"AGATE_HOME 的 ~ 未展开：{result.output!r}"
    assert f"AGATE_ROOT={(vroot / 'v0.44.0').resolve()!s}" in result.output


def test_debt0042_agate_home_via_resolve_hook_root(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """第二消费者：resolve_hook_root（hook 解析入口）同样认 AGATE_HOME。"""
    vroot = _make_version_root(tmp_path / "custom-root")
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(agate_scripts)!r})\n"
        "from agate_common import resolve_hook_root\n"
        "root, warns = resolve_hook_root(__file__)\n"
        "print('ROOT=' + str(root))\n"
        "print('WARNS=' + ','.join(warns))\n",
        encoding="utf-8",
    )
    result = run_cli(
        python_exe,
        str(probe),
        env={
            "AGATE_ROOT": "",
            "AGATE_HOME": str(vroot),
            "HOME": str(tmp_path / "nonexistent-home"),
            "USERPROFILE": str(tmp_path / "nonexistent-home"),
        },
    )
    assert result.returncode == 0, f"resolve_hook_root 未认 AGATE_HOME：{result.output!r}"
    assert f"ROOT={(vroot / 'v0.44.0').resolve()!s}" in result.output
