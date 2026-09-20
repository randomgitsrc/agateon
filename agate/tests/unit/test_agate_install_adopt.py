# tests/unit/test_agate_install_adopt.py — `agate-install.py --adopt` 与 `--check --portable`（TAG0037 P3 组 B，批 B1b）
# 覆盖：BDD-17（portable 的 adopt 部分：不依赖 git、写指针 + 根 scripts/；文档命令部分归 C 组 / 三路径 H3）、
#       BDD-18 [参数化 ①②③]（--check --portable 口径；既有默认口径不变）、
#       T-20（adopt 失败路径：新形态版本目录含软链 / 顶层多余条目 / tests/ → exit 1；latest / current 位置是真实目录 → exit 1 无 Traceback）、
#       T-16（adopt 自身事务化：写指针失败须把已改写的指针还原）、T-14（adopt 入口的软链守卫，参数化 ["L","L/","L//","L/.","L/.."]）、
#       cso F-6 / F-13（版本号 fullmatch 校验；OSError 转 stderr + exit 1）、D-13（从版本目录内运行不写字节码）。
# 被测：agate/scripts/agate-install.py（P4 批 B1b 新增 --adopt / --check --portable；P4 前：--adopt 未识别 → 用法退出 2 = 断言失败 = B 类红灯）。
# 夹具：版本目录由测试**手工搭成新契约形态**（vX.Y.Z/{agate/, 登记根文件}），不经 agate_package——使本文件只在被测的 adopt 行为上变红。
# 隔离：AGATE_HOME / HOME 全在 tmp_path；PATH 用 git 绊线（记录并失败）/ 无 git 目录；不触碰真实 ~/.agate。
# 平台：POSIX 专用（软链指针 / shim）；Windows CI 只跑 windows_smoke，本文件不带该标记。

import os
import re
import shutil
import sys
import venv

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="adopt 用例仅 POSIX（软链指针 / PATH shim）")

_VERSION = "v0.73.0"
_OLDER = "v0.72.5"
_VARIANTS = ["L", "L/", "L//", "L/.", "L/.."]
_VARIANT_IDS = [f"t14-{i}-{v.replace('/', 's').replace('.', 'd')}" for i, v in enumerate(_VARIANTS)]
_STEP_RES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}


def _new_form_vdir(agate_home, version=_VERSION, extra=None):
    """手工搭新契约形态版本目录：vX.Y.Z/{agate/（含真实 scripts/）, CHANGELOG.md, LICENSE, NOTICES.md}。"""
    vdir = agate_home / version
    H.copy_real_scripts(vdir / "agate" / "scripts")
    (vdir / "agate" / "WORKFLOW.md").write_text("# workflow\n", encoding="utf-8")
    for name in H.ORACLE_ROOT_FILES:
        (vdir / name).write_text(f"# {name}\n", encoding="utf-8")
    for rel, text in (extra or {}).items():
        p = vdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return vdir


def _pointer_state(agate_home):
    out = {}
    for name in ("latest", "current"):
        p = agate_home / name
        if p.is_symlink():
            out[name] = ("link", os.readlink(str(p)))
        elif p.is_dir():
            out[name] = ("dir", tuple(sorted(os.listdir(str(p)))))
        elif p.is_file():
            out[name] = ("file", p.read_text(encoding="utf-8"))
        else:
            out[name] = None
    return out


def _seed_older(agate_home):
    """预置更老版本 + latest → older、current → latest（用于断言失败时指针不变）。"""
    _new_form_vdir(agate_home, _OLDER)
    os.symlink(_OLDER, str(agate_home / "latest"))
    os.symlink("latest", str(agate_home / "current"))


def _run_adopt(agate_scripts, tmp_path, agate_home, version=_VERSION, entry=None, path=None, extra_args=()):
    env = H.tool_env(tmp_path / "home", agate_home=agate_home)
    if path is not None:
        env["PATH"] = str(path)
    argv = [sys.executable, entry or (agate_scripts / "agate-install.py"), "--adopt", version, *extra_args]
    return H.run_tool(argv, env=env, cwd=tmp_path)


def _git_tripwire(tmp_path):
    """PATH 目录里的假 git：记录调用并失败（exit 97）。返回 (bin_dir, log)。"""
    d = tmp_path / "tripwire-bin"
    d.mkdir()
    log = tmp_path / "git-tripwire.log"
    g = d / "git"
    g.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\nexit 97\n', encoding="utf-8")
    g.chmod(0o755)
    return d, log


@pytest.fixture(scope="module")
def noyaml_bin(tmp_path_factory):
    """无 pyyaml 的 venv bin 目录（BDD-18 ②）。"""
    base = tmp_path_factory.mktemp("noyaml_venv")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(str(base))
    return base / "bin"


# ---------------------------------------------------------------------------
# BDD-17（adopt 部分）：不依赖 git，写 latest/current 指针 + 根 scripts/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["git-tripwire", "no-git-on-path"], ids=["bdd17-1-git-tripwire", "bdd17-2-no-git"])
def test_bdd_17_adopt_registers_pointers_and_root_scripts_without_git(mode, agate_scripts, tmp_path):
    """BDD-17：portable 场景下 `agate-install.py --adopt vX.Y.Z` 全程 exit 0、无 git 调用（PATH 内的 git 是绊线 / 或根本没有 git）；
    写 latest → vX、current → latest，同步根 scripts/；随后 agate-resolve.py exit 0 且 AGATE_VERSION=vX。"""
    agate_home = tmp_path / "ah"
    vdir = _new_form_vdir(agate_home)
    if mode == "git-tripwire":
        path_dir, log = _git_tripwire(tmp_path)
    else:
        path_dir, log = tmp_path / "empty-bin", None
        path_dir.mkdir()
        assert shutil.which("git", path=str(path_dir)) is None
    proc = _run_adopt(agate_scripts, tmp_path, agate_home, path=path_dir)
    assert proc.returncode == 0, f"adopt 应成功: {proc.stderr}"
    assert os.readlink(str(agate_home / "latest")) == _VERSION
    assert os.readlink(str(agate_home / "current")) == "latest"
    assert (agate_home / "scripts" / "agate-install.py").is_file()
    assert H.file_set(agate_home / "scripts") == H.file_set(vdir / "agate" / "scripts"), "根 scripts/ 应是协议 scripts/ 的副本"
    if log is not None:
        assert not log.exists(), "adopt 不得调用 git"
    assert not list(agate_home.rglob(".git")), "adopt 不碰 git，不得产生 .git"
    res = H.run_tool(
        [sys.executable, agate_home / "scripts" / "agate-resolve.py"],
        env={**H.tool_env(tmp_path / "home", agate_home=agate_home), "PATH": str(path_dir)},
        cwd=tmp_path,
    )
    assert res.returncode == 0, res.stderr
    assert f"AGATE_VERSION={_VERSION}" in res.stdout
    assert f"AGATE_ROOT={(vdir / 'agate').resolve()}" in res.stdout


def test_bdd_17_adopt_is_idempotent_and_does_not_modify_version_dir(agate_scripts, tmp_path):
    """BDD-17：重复 adopt 同一版本 exit 0、结果不变；版本目录内容逐字节不变（adopt 不改写它）。"""
    agate_home = tmp_path / "ah"
    vdir = _new_form_vdir(agate_home)
    before = H.snapshot_tree(vdir, ignore_bytecode=False)
    first = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert first.returncode == 0, first.stderr
    state = _pointer_state(agate_home)
    second = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert second.returncode == 0, second.stderr
    assert _pointer_state(agate_home) == state
    assert H.snapshot_tree(vdir, ignore_bytecode=False) == before


def test_d13_adopt_from_version_dir_entry_writes_no_bytecode(agate_scripts, tmp_path):
    """D-13 / eng B-1：文档命令是从版本目录内运行 `vdir/agate/scripts/agate-install.py --adopt`——即使不带 -B，安装器自身也不得往版本目录写 __pycache__。"""
    agate_home = tmp_path / "ah"
    vdir = _new_form_vdir(agate_home)
    before = H.snapshot_tree(vdir, ignore_bytecode=False)
    proc = _run_adopt(agate_scripts, tmp_path, agate_home, entry=vdir / "agate" / "scripts" / "agate-install.py")
    assert proc.returncode == 0, proc.stderr
    assert H.snapshot_tree(vdir, ignore_bytecode=False) == before, "从版本目录内运行 adopt 后，版本目录不得出现字节码"


def test_bdd_17_adopt_old_worktree_form_dir_skips_contract_verification(agate_scripts, tmp_path):
    """兼容：旧形态版本目录（git worktree 整仓形态，含 .git 指针文件与 docs/ 等顶层条目）adopt 跳过 verify_dir，照常写指针（不迁移、不归一化）。"""
    agate_home = tmp_path / "ah"
    vdir = _new_form_vdir(agate_home, extra={".git": "gitdir: /nonexistent\n", "docs/x.md": "# d\n", "HANDOFF-X.md": "# h\n"})
    proc = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert proc.returncode == 0, proc.stderr
    assert os.readlink(str(agate_home / "latest")) == _VERSION
    assert (vdir / "docs" / "x.md").is_file(), "旧形态目录不被改动"


# ---------------------------------------------------------------------------
# BDD-18 [参数化]：--check --portable
# ---------------------------------------------------------------------------


def _check(agate_scripts, tmp_path, path_dir, *flags, drop_pythonpath=False):
    env = H.tool_env(tmp_path / "home")
    env["PATH"] = str(path_dir)
    if drop_pythonpath:
        env.pop("PYTHONPATH", None)
    return H.run_tool([sys.executable, agate_scripts / "agate-install.py", "--check", *flags], env=env, cwd=tmp_path)


def test_bdd_18_1_portable_check_without_git_exit_0_with_hint(agate_scripts, tmp_path):
    """BDD-18 ①：无 git 环境跑 portable 口径 → exit 0，git 缺失仅提示"仅在线安装 / 装历史 tag 需要"。"""
    bin_dir = H.make_python3_wrapper(tmp_path / "py3bin")
    assert shutil.which("git", path=str(bin_dir)) is None
    proc = _check(agate_scripts, tmp_path, bin_dir, "--portable")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "git" in proc.stdout
    assert "在线安装" in proc.stdout and "历史 tag" in proc.stdout


def test_bdd_18_2_portable_check_missing_pyyaml_fails_with_fix_guidance(agate_scripts, tmp_path, noyaml_bin):
    """BDD-18 ②：缺 pyyaml 环境跑 portable 口径 → exit 非 0 并列出 pyyaml 修复指引。"""
    proc = _check(agate_scripts, tmp_path, noyaml_bin, "--portable", drop_pythonpath=True)
    assert proc.returncode != 0
    assert "yaml" in proc.stdout
    assert "pip install" in proc.stdout


def test_bdd_18_3_default_check_without_git_still_fails_listing_git(agate_scripts, tmp_path):
    """BDD-18 ③：无 git 环境跑**默认口径**（现行 --check）→ exit 1 且列出 git 缺失（既有 test_bdd_7 / test_bdd_8 源码不改，本用例锁 opt-in 语义）。"""
    bin_dir = H.make_python3_wrapper(tmp_path / "py3bin")
    proc = _check(agate_scripts, tmp_path, bin_dir)
    assert proc.returncode == 1
    assert "缺少" in proc.stdout and "git" in proc.stdout.split("缺少", 1)[1]


# ---------------------------------------------------------------------------
# T-20：adopt 失败路径
# ---------------------------------------------------------------------------


def _mutate_symlink_member(vdir):
    os.symlink(str(vdir / "agate" / "WORKFLOW.md"), str(vdir / "agate" / "link-to-workflow"))


def _mutate_extra_top(vdir):
    (vdir / "extra.sh").write_text("#!/bin/sh\n", encoding="utf-8")


def _mutate_tests_dir(vdir):
    (vdir / "agate" / "tests").mkdir()
    (vdir / "agate" / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")


@pytest.mark.parametrize(
    "mutate",
    [_mutate_symlink_member, _mutate_extra_top, _mutate_tests_dir],
    ids=["t20-1-symlink-member", "t20-2-extra-top-level-entry", "t20-3-tests-dir"],
)
def test_t20_adopt_rejects_non_conforming_new_form_dir(mutate, agate_scripts, tmp_path):
    """T-20：新形态版本目录含软链 / 顶层多余条目 / agate/tests/ → --adopt exit 1，stderr 指明违约，指针不变、不建根 scripts/。"""
    agate_home = tmp_path / "ah"
    _seed_older(agate_home)
    vdir = _new_form_vdir(agate_home)
    mutate(vdir)
    before_ptr = _pointer_state(agate_home)
    proc = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert proc.returncode == 1, f"违约应 exit 1: rc={proc.returncode} {proc.stderr}"
    assert "Traceback" not in proc.stderr
    assert proc.stderr.strip(), "应给出违约说明"
    assert _pointer_state(agate_home) == before_ptr
    assert not (agate_home / "scripts").exists()


@pytest.mark.parametrize("which", ["latest", "current"], ids=["t20-4-latest-is-dir", "t20-5-current-is-dir"])
def test_t20_adopt_pointer_position_is_real_directory_exit_1_no_traceback_and_restores(which, agate_scripts, tmp_path):
    """T-20 / T-16（eng N-2）：`latest` 或 `current` 位置已是真实目录 → exit 1 且无 Traceback（OSError 转 stderr）；
    adopt 自身事务化：此前已改写的另一指针被还原，真实目录原样。"""
    agate_home = tmp_path / "ah"
    _seed_older(agate_home)
    _new_form_vdir(agate_home)
    victim = agate_home / which
    os.unlink(str(victim))
    victim.mkdir()
    (victim / "keep.txt").write_text("keep\n", encoding="utf-8")
    before_ptr = _pointer_state(agate_home)
    before_dir = H.snapshot_tree(victim, ignore_bytecode=False)
    proc = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert proc.returncode == 1, proc.stderr
    assert "Traceback" not in proc.stderr
    assert _pointer_state(agate_home) == before_ptr, "另一指针必须已还原（adopt 事务化）"
    assert H.snapshot_tree(victim, ignore_bytecode=False) == before_dir


@pytest.mark.parametrize("bad", ["v0.73.0\n", "v1.2", "../evil", "v0.73.0-rc.1", "v٠.٧.٣"], ids=["bad-newline", "bad-two-part", "bad-traversal", "bad-prerelease", "bad-unicode"])
def test_adopt_rejects_invalid_version_strings(bad, agate_scripts, tmp_path):
    """cso F-6 / eng m-1：版本号 fullmatch 校验（结尾换行 / 两段 / 路径穿越 / 预发布后缀 / Unicode 数字均拒）：exit 2，"非法版本号"，不建任何目录 / 指针。"""
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    before = sorted(os.listdir(str(agate_home)))
    proc = _run_adopt(agate_scripts, tmp_path, agate_home, version=bad)
    assert proc.returncode == 2, proc.stderr
    assert "非法版本号" in proc.stderr
    assert sorted(os.listdir(str(agate_home))) == before
    assert not (tmp_path / "evil").exists()


def test_adopt_missing_version_dir_and_missing_protocol_scripts_exit_1(agate_scripts, tmp_path):
    """adopt 前置校验：版本目录不存在 → exit 1；版本目录缺协议 scripts/（`_protocol_root(vdir)/scripts`）→ exit 1；均不写指针。"""
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    missing = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert missing.returncode == 1 and _VERSION in missing.stderr
    (agate_home / _VERSION / "agate").mkdir(parents=True)
    (agate_home / _VERSION / "agate" / "README.md").write_text("no scripts\n", encoding="utf-8")
    noscripts = _run_adopt(agate_scripts, tmp_path, agate_home)
    assert noscripts.returncode == 1, noscripts.stderr
    assert "Traceback" not in noscripts.stderr
    assert not (agate_home / "latest").exists() and not (agate_home / "current").exists()


# ---------------------------------------------------------------------------
# T-14：adopt 入口的软链守卫（参数化）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", _VARIANTS, ids=_VARIANT_IDS)
def test_t14_adopt_symlink_home_fail_closed(variant, agate_scripts, tmp_path):
    """T-14（agate-install --adopt 入口）：AGATE_HOME 是软链（含 L/ L// L/. L/.. 变体）→ exit 1、三步迁移片段，
    软链目标目录（含其中已有的版本目录）内容不变，物理父目录不新增条目。"""
    target = tmp_path / "src" / "agate"
    _new_form_vdir(target)  # 目标里恰有合法版本目录：若守卫被绕过，adopt 会在目标里写指针 / 根 scripts/
    home = tmp_path / "home-link"
    home.mkdir()
    link = home / ".agate"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    before = H.snapshot_tree(target, ignore_bytecode=False)
    parent_listing = sorted(os.listdir(str(target.parent)))
    proc = _run_adopt(agate_scripts, tmp_path, str(link) + variant[1:])
    assert proc.returncode == 1, f"软链基址应 fail-closed exit 1: rc={proc.returncode}\n{proc.stderr}"
    for key, rx in _STEP_RES.items():
        assert rx.search(proc.stderr), f"stderr 缺三步迁移片段 {key}: {proc.stderr}"
    assert H.snapshot_tree(target, ignore_bytecode=False) == before, "软链目标不得被穿透写入（指针 / 根 scripts/）"
    assert sorted(os.listdir(str(target.parent))) == parent_listing
