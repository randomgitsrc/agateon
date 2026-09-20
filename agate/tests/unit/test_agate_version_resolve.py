# tests/unit/test_agate_version_resolve.py — agate-resolve.py 版本解析语义（resolve-chain 批次）
# 被测：agate/scripts/agate-resolve.py（TAG0008 新组件，P4 实现）。P3 阶段该模块不存在 → 全部红灯（B 类）。
# BDD 映射：BDD-9~14（resolve 语义）+ BDD-30（TAG0037 起改写为软链基址 fail-closed）+ P2-review 测试缺口 1（终态 fail-closed）。
# 平台无关（AGENTS.md 测试约定）：
#   * 假 HOME 经 HOME+USERPROFILE env 指向 tmp_path（不碰真实 ~/.agate，不假设系统临时目录路径）
#   * current/latest 用文本指针（内容 = 目标名），Windows 复制模式指针形态，不假设 POSIX symlink
#   * BDD-30 的软链基址场景：os.symlink 失败（Windows 无权限）→ pytest.skip 声明跳过
# Given 契约（测试数据即 P4 实现的输入约束）：
#   ~/.agate/<vX.Y.Z>/ 版本目录存在即视为"已安装"；current→latest→<版本目录名> 文本指针链。

import inspect
import os
import re
import sys
from pathlib import Path

import pytest

import helpers_tag_repo as H

_STEP_RES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}


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
def test_bdd_27_symlink_home_fail_closed(run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-27（TAG0037 改写，BDD-38 ①）：原 `test_bdd_30_legacy_symlink_direct_root` 断言"软链 ~/.agate → 协议本体目录、无版本目录 / 指针"时
    软链目标被直接当 AGATE_ROOT 解析（exit 0）——该行为在 TAG0037 被彻底删除。本用例沿用同一 fixture 改写为 fail-closed 断言：
    exit 1；stdout 无 AGATE_ROOT= 行；stderr 含三步迁移片段；软链目标内容前后不变；任何输出不含 legacy 字样。
    （名字前缀 test_bdd_30 的撞名用例（spawn_agent / quoted node ids / formatter 等）与此无关，零改动。）"""
    legacy = tmp_path / "old-checkout" / "agate"
    (legacy / "scripts").mkdir(parents=True)
    (legacy / "assets").mkdir()
    (legacy / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    try:
        os.symlink(str(legacy), str(home / ".agate"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，软链布局无法构建")
    before = H.snapshot_tree(legacy)

    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    assert result.returncode == 1, f"软链基址（无版本指针）应 fail-closed exit 1: rc={result.returncode}\n{result.output}"
    assert "AGATE_ROOT=" not in result.stdout
    for rx in _STEP_RES.values():
        assert rx.search(result.stderr), f"stderr 缺三步迁移片段: {result.stderr}"
    assert H.snapshot_tree(legacy) == before
    assert "legacy" not in result.output.lower()


def test_resolve_terminal_failure_fail_closed(run_cli, python_exe, agate_scripts, tmp_path):
    """P2-review 测试缺口 1：无 current/latest 可用 root + 声明版本未装 → 终态 exit 非 0。

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
#   项目声明 > current 链（TAG0037 起软链兜底已删除，仅三层）。AGATE_HOME 只换"版本根在哪"，不改层序。
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


def test_debt0042_agate_home_symlink_fail_closed(run_cli, python_exe, agate_scripts, tmp_path):
    """DEBT0042（TAG0037 改写，BDD-38 ①）：原 `test_debt0042_agate_home_legacy_symlink` 断言"AGATE_HOME 指向软链 → 软链兜底解析成功（exit 0，输出含 legacy）"，
    与 TAG0037 新语义相反（软链兜底被删除）。改写为 fail-closed：AGATE_HOME 指向软链（目标是协议本体目录、无 current）→ exit 1，
    stderr 含迁移三步，stdout 无 AGATE_ROOT=，目标目录不变，输出不含 legacy。"""
    real = tmp_path / "protocol-body"
    (real / "scripts").mkdir(parents=True)
    (real / "assets").mkdir(parents=True)
    custom = tmp_path / "custom-home"
    custom.mkdir()
    link = custom / "body"
    try:
        os.symlink(str(real), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("该平台不支持符号链接（Windows 无权限）")
    before = H.snapshot_tree(real)
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
    assert result.returncode == 1, f"软链基址应 fail-closed：{result.output!r}"
    assert "AGATE_ROOT=" not in result.stdout
    for rx in _STEP_RES.values():
        assert rx.search(result.stderr), f"stderr 缺三步迁移片段: {result.stderr}"
    assert "legacy" not in result.output.lower()
    assert H.snapshot_tree(real) == before


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


# ============================================================
# TAG0037 P3 组 B（批 E）：legacy 软链兜底彻底删除后的解析语义
#   BDD-27（软链 fail-closed + 迁移三步；上方两个改写用例 + T-14 参数化）、BDD-28（解析链仅剩三层、旧兜底开关参数消失）、
#   BDD-51（软链 → 完整版本根：解析放行）、BDD-5 / BDD-7（已装旧形态 worktree 整仓版本目录仍可解析 / 与新形态共存；夹具显式构造）。
#   被测：agate_common._resolve_version_info / resolve_version_root、agate-resolve.py（P4 批 E）。
# ============================================================

_T14_VARIANTS = ["L", "L/", "L//", "L/.", "L/.."]
_T14_IDS = [f"t14-{i}-{v.replace('/', 's').replace('.', 'd')}" for i, v in enumerate(_T14_VARIANTS)]


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _symlink_home(tmp_path, with_versions=False):
    """<tmp>/home/.agate 软链 → <tmp>/src/agate（含 scripts/ assets/ 与金丝雀）；with_versions 时目标是完整版本根（BDD-51）。"""
    target = tmp_path / "src" / "agate"
    if with_versions:
        (target / "v0.73.0" / "agate" / "scripts").mkdir(parents=True)
        os.symlink("v0.73.0", str(target / "latest"))
        os.symlink("latest", str(target / "current"))
    else:
        (target / "scripts").mkdir(parents=True)
        (target / "assets").mkdir()
    (target / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home-link"
    home.mkdir()
    link = home / ".agate"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，软链布局无法构建")
    return home, link, target


def _kv(stdout):
    out = {}
    for line in stdout.splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k] = v
    return out


@pytest.mark.parametrize("variant", _T14_VARIANTS, ids=_T14_IDS)
def test_bdd_27_t14_resolve_symlink_home_fail_closed_with_migration_hint(variant, run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-27 + T-14（agate-resolve 入口）：AGATE_HOME 是软链（含 L/ L// L/. L/.. 变体；目标是协议本体、无 current）→ exit 1，
    stdout 无 AGATE_ROOT=，stderr 含三步迁移片段（`L/..` 因物理与文本解析不一致同样视为软链基址），软链目标内容不变。"""
    home, link, target = _symlink_home(tmp_path)
    before = H.snapshot_tree(target)
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(tmp_path),
        env={"AGATE_ROOT": "", "AGATE_HOME": str(link) + variant[1:], "HOME": str(home), "USERPROFILE": str(home)},
    )
    assert result.returncode == 1, f"rc={result.returncode}\n{result.output}"
    assert "AGATE_ROOT=" not in result.stdout
    for key, rx in _STEP_RES.items():
        assert rx.search(result.stderr), f"stderr 缺三步迁移片段 {key}: {result.stderr}"
    assert H.snapshot_tree(target) == before


def _bdd28_env(kind, tmp_path):
    """(env, cwd) for BDD-28 a–e；返回 (env, cwd, expected_reason_or_None)。"""
    if kind == "a-env-root":
        home = _make_home(tmp_path)
        custom = tmp_path / "custom-root"
        custom.mkdir()
        return {**_resolve_env(home), "AGATE_ROOT": str(custom)}, tmp_path, "AGATE_ROOT 环境变量覆盖"
    if kind == "b-project-declaration":
        home = _make_home(tmp_path)
        project = tmp_path / "project"
        project.mkdir()
        _write_version_decl(project, "v0.43.0")
        return _resolve_env(home), project, "引用 .agate-version"
    if kind == "c-current-only":
        home = _make_home(tmp_path)
        return _resolve_env(home), tmp_path, "全局 current"
    if kind == "d-nothing":
        home = tmp_path / "home"
        (home / ".agate").mkdir(parents=True)
        return _resolve_env(home), tmp_path, None
    home, link, _target = _symlink_home(tmp_path)
    custom = tmp_path / "custom-root"
    custom.mkdir()
    return {"AGATE_ROOT": str(custom), "AGATE_HOME": str(link), "HOME": str(home), "USERPROFILE": str(home)}, tmp_path, "AGATE_ROOT 环境变量覆盖"


@pytest.mark.parametrize(
    "kind",
    ["a-env-root", "b-project-declaration", "c-current-only", "d-nothing", "e-env-root-with-symlink-agate-home"],
    ids=["bdd28-a", "bdd28-b", "bdd28-c", "bdd28-d", "bdd28-e"],
)
def test_bdd_28_resolution_chain_has_only_three_layers(kind, run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-28 [参数化 a–e]：(a)(e) AGATE_ROOT 覆盖（软链 AGATE_HOME 下仍生效，开发 worktree 场景依赖）；(b) 项目声明；(c) 仅 current；
    (d) 三者皆无 → exit 1（终态 fail-closed）；AGATE_REASON 取值集合 ⊆ {三种}，任何输出不含 legacy。"""
    env, cwd, reason = _bdd28_env(kind, tmp_path)
    result = run_cli(python_exe, str(agate_scripts / "agate-resolve.py"), cwd=str(cwd), env=env)
    assert "legacy" not in result.output.lower()
    if reason is None:
        assert result.returncode == 1
        assert "AGATE_ROOT=" not in result.stdout
        return
    assert result.returncode == 0, result.output
    assert _kv(result.stdout)["AGATE_REASON"] == reason
    assert _kv(result.stdout)["AGATE_REASON"] in {"AGATE_ROOT 环境变量覆盖", "引用 .agate-version", "全局 current"}


def test_bdd_28_legacy_switch_param_is_gone_and_no_symlink_target_as_root_branch(agate_scripts):
    """BDD-28：`inspect.signature(agate_common._resolve_version_info)` 无旧兜底开关参数（BDD-37 永久 grep，名字在下方以拼接构造）；agate_common.py 中不存在"把软链目标当 AGATE_ROOT 返回"的分支
    （`realpath(base)` 作 root）——软链检测 + 迁移提示分支允许存在（BDD-27 / 34 需要），故不断言 islink 调用本身不存在。"""
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    removed_param = "use_" + "legacy"  # 拼接构造：BDD-37 全仓 grep 不许源码直接含该字面量
    assert removed_param not in inspect.signature(agate_common._resolve_version_info).parameters
    text = (agate_scripts / "agate_common.py").read_text(encoding="utf-8")
    assert removed_param not in text
    assert not re.search(r"realpath\(\s*base\s*\)", text), "不得存在把软链目标（realpath(base)）当协议根返回的分支"


def test_bdd_28_resolve_info_reports_symlink_base_including_env_branch(agate_scripts, tmp_path, monkeypatch):
    """P2 §3.7 / eng m-6：`_resolve_version_info` 返回 dict 恒含 `symlink_base` 键——含 AGATE_ROOT env 早返回分支（恒 False）；
    软链基址（BDD-51 / 27）为 True；普通目录基址为 False。"""
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    monkeypatch.setenv("AGATE_ROOT", str(tmp_path))
    assert agate_common._resolve_version_info()["symlink_base"] is False
    monkeypatch.delenv("AGATE_ROOT")
    plain = _make_version_root(tmp_path / "plain-root")
    monkeypatch.setenv("AGATE_HOME", str(plain))
    assert agate_common._resolve_version_info()["symlink_base"] is False
    _home, link, _target = _symlink_home(tmp_path / "sym", with_versions=True)
    monkeypatch.setenv("AGATE_HOME", str(link))
    info = agate_common._resolve_version_info()
    assert info["symlink_base"] is True
    assert info["root"] is not None and info["reason"] == "全局 current"


def test_bdd_51_1_symlink_to_full_version_root_resolves_via_current_chain(run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-51 ①：AGATE_HOME 是软链 → 完整版本根（含 vX.Y.Z/agate、latest → vX、current → latest；未设 AGATE_ROOT）——
    resolve exit 0（放行：被删除的只是"把软链目标直接当协议根"的分支），AGATE_REASON=全局 current，AGATE_ROOT 为目标内 vX.Y.Z/agate。"""
    home, link, target = _symlink_home(tmp_path, with_versions=True)
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-resolve.py"),
        cwd=str(tmp_path),
        env={"AGATE_ROOT": "", "AGATE_HOME": str(link), "HOME": str(home), "USERPROFILE": str(home)},
    )
    assert result.returncode == 0, result.output
    kv = _kv(result.stdout)
    assert kv["AGATE_REASON"] == "全局 current"
    assert kv["AGATE_ROOT"] == str((target / "v0.73.0" / "agate").resolve())
    assert kv["AGATE_VERSION"] == "v0.73.0"
    # 与 BDD-27 夹具互不矛盾：同一机制，目标是协议本体目录 / 无 current 时才 fail-closed（见上方 test_bdd_27_*）
    info_probe = tmp_path / "probe.py"
    info_probe.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(agate_scripts)!r})\n"
        "import agate_common\n"
        "print('SYMLINK_BASE=' + str(agate_common._resolve_version_info()['symlink_base']))\n",
        encoding="utf-8",
    )
    probe = run_cli(python_exe, str(info_probe), env={"AGATE_ROOT": "", "AGATE_HOME": str(link), "HOME": str(home), "USERPROFILE": str(home)})
    assert probe.returncode == 0, probe.output
    assert "SYMLINK_BASE=True" in probe.stdout


# ---- BDD-5 / BDD-7：旧形态（git worktree 整仓）版本目录——夹具显式构造并保留在测试中 ----

_OLD_FORM_FILES = {
    "agate/scripts/pre-commit-gate.py": 'import sys\nsys.stdout.write("OLD-FORM-GATE\\n")\n',
    "agate/WORKFLOW.md": "# workflow\n",
    "agate-workspace/tasks/TAG0001-x/P1.md": "# task\n",
    "docs/reviews/r.md": "# r\n",
    "site/index.md": "# s\n",
    "archived/a.md": "# a\n",
    "HANDOFF-X.md": "# h\n",
    "CHANGELOG.md": "# changelog\n",
    "LICENSE": "MIT\n",
    "NOTICES.md": "# notices\n",
}


def _old_form_home(tmp_path, tag="v0.71.1"):
    """旧安装器同款方式手工构造旧形态：`git worktree add --detach <home>/vX.Y.Z <tag>` 整仓检出 + latest → vX、current → latest。"""
    repo = H.make_custom_tag_repo(tmp_path, _OLD_FORM_FILES, tag=tag)
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    H.run_git(repo.bare, "worktree", "add", "--detach", str(agate_home / tag), tag)
    try:
        os.symlink(tag, str(agate_home / "latest"))
        os.symlink("latest", str(agate_home / "current"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    assert (agate_home / tag / ".git").exists() and (agate_home / tag / "docs").is_dir(), "Given：旧整仓形态"
    return agate_home


@pytest.mark.parametrize(
    "scenario",
    ["resolve-current", "resolve-declared", "hook-root", "summary"],
    ids=["bdd5-1-resolve", "bdd5-2-resolve-declared", "bdd5-3-hook-root", "bdd5-4-summary"],
)
def test_bdd_5_old_worktree_form_version_dir_still_resolves(scenario, run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-5 [参数化 ①–④]：旧形态 vX.Y.Z/{agate, agate-workspace, docs, …}——① agate-resolve（无声明）；② 项目 .agate-version 后 agate-resolve；
    ③ hook 解析（resolve_hook_root）得到的 <root>/scripts/pre-commit-gate.py 存在；④ agate-summary 输出「版本：vX.Y.Z」。均 exit 0。"""
    agate_home = _old_form_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    env = {"AGATE_ROOT": "", "AGATE_HOME": str(agate_home), "HOME": str(tmp_path / "home"), "USERPROFILE": str(tmp_path / "home")}
    expected_root = str((agate_home / "v0.71.1" / "agate").resolve())
    if scenario == "resolve-current":
        r = run_cli(python_exe, str(agate_scripts / "agate-resolve.py"), cwd=str(project), env=env)
        assert r.returncode == 0, r.output
        assert _kv(r.stdout)["AGATE_ROOT"] == expected_root
        assert _kv(r.stdout)["AGATE_REASON"] == "全局 current"
    elif scenario == "resolve-declared":
        _write_version_decl(project, "v0.71.1")
        r = run_cli(python_exe, str(agate_scripts / "agate-resolve.py"), cwd=str(project), env=env)
        assert r.returncode == 0, r.output
        assert _kv(r.stdout)["AGATE_ROOT"] == expected_root
        assert _kv(r.stdout)["AGATE_REASON"] == "引用 .agate-version"
    elif scenario == "hook-root":
        probe = tmp_path / "probe.py"
        probe.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(agate_scripts)!r})\n"
            "from agate_common import resolve_hook_root\n"
            "root, _w = resolve_hook_root(__file__)\n"
            "print('ROOT=' + str(root))\n",
            encoding="utf-8",
        )
        r = run_cli(python_exe, str(probe), cwd=str(project), env=env)
        assert r.returncode == 0, r.output
        root = _kv(r.stdout)["ROOT"]
        assert Path(root).resolve() == Path(expected_root)
        assert (Path(root) / "scripts" / "pre-commit-gate.py").is_file()
    else:
        r = run_cli(python_exe, str(agate_scripts / "agate-summary.py"), cwd=str(project), env=env)
        assert r.returncode == 0, r.output
        assert "版本：v0.71.1" in r.output


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针 / 真实 worktree 断言仅 POSIX")
@pytest.mark.parametrize("scenario", ["no-declaration", "declared-old-form"], ids=["bdd7-1-current-is-new-form", "bdd7-2-pinned-old-form"])
def test_bdd_7_old_and_new_form_versions_coexist(scenario, run_cli, python_exe, agate_scripts, tmp_path, synth):
    """BDD-7 [参数化 ①②]：版本根内已有旧形态 v0.72.5/（真实 git worktree 整仓）+ 用新安装器再装的新形态 v0.73.0/，current 指向新版——
    ① 无 .agate-version → AGATE_ROOT 为 v0.73.0/agate；② 项目 .agate-version 写 agate: v0.72.5 → AGATE_ROOT 为 v0.72.5/agate（旧形态被钉版正确命中）。"""
    agate_home = tmp_path / "ah"
    inst = H.run_tool(
        [sys.executable, agate_scripts / "agate-install.py", "latest"],
        env=H.tool_env(tmp_path / "home", agate_home=agate_home, extra={"AGATE_REPO_URL": synth.url}),
    )
    assert inst.returncode == 0, inst.stderr
    assert not (agate_home / H.MAIN_TAG / ".git").exists(), "Given：新安装器装出新形态（无 .git 指针）"
    H.run_git(agate_home / "repo", "worktree", "add", "--detach", str(agate_home / H.ANNOTATED_TAG), H.ANNOTATED_TAG)
    assert (agate_home / H.ANNOTATED_TAG / ".git").exists() and (agate_home / H.ANNOTATED_TAG / "docs").is_dir(), "Given：旧整仓形态"
    project = tmp_path / "project"
    project.mkdir()
    env = {"AGATE_ROOT": "", "AGATE_HOME": str(agate_home), "HOME": str(tmp_path / "home"), "USERPROFILE": str(tmp_path / "home")}
    if scenario == "declared-old-form":
        _write_version_decl(project, H.ANNOTATED_TAG)
        expected = (agate_home / H.ANNOTATED_TAG / "agate").resolve()
    else:
        expected = (agate_home / H.MAIN_TAG / "agate").resolve()
    r = run_cli(python_exe, str(agate_scripts / "agate-resolve.py"), cwd=str(project), env=env)
    assert r.returncode == 0, r.output
    assert _kv(r.stdout)["AGATE_ROOT"] == str(expected)
