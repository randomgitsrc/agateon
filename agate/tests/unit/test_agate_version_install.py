# tests/unit/test_agate_version_install.py — agate-install（安装/卸载/环境探测）TDD 测试
# （TAG0008 批次 install，BDD-1~8 1:1 映射）
# 被测：agate/scripts/agate-install.py（P3 阶段尚未实现 → 当前全部红灯，B 类：模块不存在）
# 接口契约（P3-test-cases-install.md §0）：
#   * agate-install [<version> | --uninstall <version> | --check]
#   * AGATE_REPO_URL env = 版本源仓库（测试指向本地临时 repo，含 v0.43.0 / v0.48.0 tag）
#   * HOME env 重定向 ~ 到 tmp_path，~/.agate = <home>/.agate（防触碰真实 ~/.agate）
# 平台分支（AGENTS.md 平台无关原则）：
#   * 指针断言 POSIX 软链 / Windows 文本指针分支；worktree 路径经 os.path.normcase 匹配
#   * python 一律用 conftest python_exe fixture，不写死 python3

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _run_install(run_cli, python_exe, agate_scripts, home, *args, repo_url=None, extra_env=None):
    env = {"HOME": str(home), "USERPROFILE": str(home)}
    if repo_url is not None:
        env["AGATE_REPO_URL"] = str(repo_url)
    if extra_env:
        env.update(extra_env)
    return run_cli(python_exe, str(agate_scripts / "agate-install.py"), *args, env=env)


# 真实 agate/scripts/ 目录（本测试文件位于 <root>/agate/tests/unit/）。
_REAL_AGATE_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _tag_upstream(git_repo):
    """建版本源 repo：两次 commit + v0.43.0 / v0.48.0 tag（v0.48.0 最新）。

    agate/scripts/ 内放真实 agate-install.py + agate_common.py（贴近真实元仓库形态：
    每个 tag 的 agate/scripts/ 本就含全套版本工具，P1-requirements §3.4）——令
    _sync_root_scripts 单源 copytree 即覆盖全部根入口命令。
    """
    scripts = git_repo.path / "agate" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "README.md").write_text("# agate upstream v0.43.0\n", encoding="utf-8")
    for name in ("agate-install.py", "agate_common.py"):
        shutil.copy2(str(_REAL_AGATE_SCRIPTS / name), str(scripts / name))
    git_repo.commit("base v0.43.0")
    git_repo.git("tag", "v0.43.0")
    (scripts / "README.md").write_text("# agate upstream v0.48.0\n", encoding="utf-8")
    git_repo.commit("bump v0.48.0")
    git_repo.git("tag", "v0.48.0")


def _resolve_pointer(agate_home, name):
    """解析 ~/.agate/{name} 指针链 → 最终路径（兼容软链 / 文本指针 / current→latest）。"""
    node = agate_home / name
    for _ in range(5):
        if node.is_symlink():
            target = Path(os.readlink(str(node)))
            node = target if target.is_absolute() else node.parent / target
            continue
        if node.is_file() and not node.is_dir():
            content = node.read_text(encoding="utf-8").strip()
            if content:
                p = Path(content)
                node = p if p.is_absolute() else agate_home / p
                continue
        break
    return node


def _git(git_exe, *args, cwd=None):
    return subprocess.run(
        [git_exe] + [str(a) for a in args],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _worktree_porcelain(git_exe, repo_clone):
    return _git(git_exe, "-C", str(repo_clone), "worktree", "list", "--porcelain").stdout


def _head_of(git_exe, worktree_dir):
    return _git(git_exe, "-C", str(worktree_dir), "rev-parse", "HEAD").stdout.strip()


def _tag_commit_of(git_exe, repo_clone, tag):
    return _git(git_exe, "-C", str(repo_clone), "rev-parse", tag).stdout.strip()


@pytest.mark.windows_smoke
def test_bdd_1_latest_pointer_after_noarg_install(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"

    result = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=py_path(git_repo.path))
    assert result.returncode == 0

    agate_home = home / ".agate"
    latest = agate_home / "latest"
    assert latest.exists()
    if sys.platform == "win32":
        assert not latest.is_dir()
    else:
        assert latest.is_symlink()
    target = _resolve_pointer(agate_home, "latest")
    assert target.is_dir()
    assert target.name == "v0.48.0"


def test_bdd_2_version_dir_worktree_of_tag(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"

    result = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=py_path(git_repo.path))
    assert result.returncode == 0

    version_dir = home / ".agate" / "v0.48.0"
    assert version_dir.is_dir()

    git_exe = shutil.which("git")
    assert git_exe
    repo_clone = home / ".agate" / "repo"
    wt = _worktree_porcelain(git_exe, repo_clone)
    assert os.path.normcase(str(version_dir)) in os.path.normcase(wt)
    assert _head_of(git_exe, version_dir) == _tag_commit_of(git_exe, repo_clone, "v0.48.0")


def test_bdd_3_reinstall_idempotent(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    url = py_path(git_repo.path)

    first = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=url)
    assert first.returncode == 0

    result = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=url)
    assert result.returncode == 0

    version_dir = home / ".agate" / "v0.48.0"
    assert version_dir.is_dir()
    git_exe = shutil.which("git")
    assert git_exe
    wt = _worktree_porcelain(git_exe, home / ".agate" / "repo")
    assert os.path.normcase(wt).count(os.path.normcase(str(version_dir))) == 1


def test_bdd_4_current_defaults_to_latest(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"

    result = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=py_path(git_repo.path))
    assert result.returncode == 0

    agate_home = home / ".agate"
    assert (agate_home / "current").exists()
    current = _resolve_pointer(agate_home, "current")
    latest = _resolve_pointer(agate_home, "latest")
    assert current == latest
    assert current.name == "v0.48.0"
    assert current.is_dir()


@pytest.mark.windows_smoke
def test_bdd_5_uninstall_removes_dir_and_clean_pointer(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    url = py_path(git_repo.path)

    latest_install = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=url)
    assert latest_install.returncode == 0
    older = _run_install(run_cli, python_exe, agate_scripts, home, "v0.43.0", repo_url=url)
    assert older.returncode == 0

    result = _run_install(run_cli, python_exe, agate_scripts, home, "--uninstall", "v0.43.0")
    assert result.returncode == 0
    assert not (home / ".agate" / "v0.43.0").exists()

    git_exe = shutil.which("git")
    assert git_exe
    wt = _worktree_porcelain(git_exe, home / ".agate" / "repo")
    assert os.path.normcase(str(home / ".agate" / "v0.43.0")) not in os.path.normcase(wt)

    agate_home = home / ".agate"
    for name in ("latest", "current"):
        if (agate_home / name).exists():
            target = _resolve_pointer(agate_home, name)
            assert target.is_dir(), f"指针 {name} 悬挂指向不存在的目录"


def test_bdd_5b_uninstall_pointed_version_repoints_symlink(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """rev2 CRITICAL-1：软链布局下卸载被 latest/current 指向的版本必须触发指针修复（BDD-5 红线）。

    回归用例：`_resolve_pointer` 先判 isdir 会对"软链→版本目录"短路，返回软链路径自身
    （basename="latest"/"current"），使 `_repair_pointers` 的 `before != removed_version`
    恒不匹配 → 卸载后指针悬空。本用例断言卸载后指针解析到剩余有效版本目录。
    """
    if os.name == "nt":
        pytest.skip("POSIX 软链指针布局仅在非 Windows 平台成立")
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    url = py_path(git_repo.path)

    latest_install = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=url)
    assert latest_install.returncode == 0
    older = _run_install(run_cli, python_exe, agate_scripts, home, "v0.43.0", repo_url=url)
    assert older.returncode == 0

    agate_home = home / ".agate"
    assert (agate_home / "latest").is_symlink()
    assert (agate_home / "current").is_symlink()

    result = _run_install(run_cli, python_exe, agate_scripts, home, "--uninstall", "v0.48.0")
    assert result.returncode == 0
    assert not (agate_home / "v0.48.0").exists()

    git_exe = shutil.which("git")
    assert git_exe
    wt = _worktree_porcelain(git_exe, home / ".agate" / "repo")
    assert os.path.normcase(str(home / ".agate" / "v0.48.0")) not in os.path.normcase(wt)

    for name in ("latest", "current"):
        target = _resolve_pointer(agate_home, name)
        assert target.is_dir(), f"指针 {name} 悬挂指向不存在的目录"
        assert target.name == "v0.43.0", f"指针 {name} 应重指到 v0.43.0，实际解析到 {target.name}"


def test_bdd_6_uninstall_rejected_when_referenced(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    install = _run_install(run_cli, python_exe, agate_scripts, home, "v0.43.0", repo_url=py_path(git_repo.path))
    assert install.returncode == 0

    project = home / "myproject"
    project.mkdir(parents=True)
    (project / ".agate-version").write_text("agate: v0.43.0\n", encoding="utf-8")

    result = _run_install(run_cli, python_exe, agate_scripts, home, "--uninstall", "v0.43.0")
    assert result.returncode != 0
    assert "v0.43.0" in result.output
    assert ("myproject" in result.output) or (".agate-version" in result.output)
    assert (home / ".agate" / "v0.43.0").is_dir()

    git_exe = shutil.which("git")
    assert git_exe
    wt = _worktree_porcelain(git_exe, home / ".agate" / "repo")
    assert os.path.normcase(str(home / ".agate" / "v0.43.0")) in os.path.normcase(wt)


@pytest.mark.windows_smoke
def test_bdd_7_env_check_all_present_exit_0(python_exe, run_cli, agate_scripts, tmp_path):
    home = tmp_path / "home"
    result = _run_install(run_cli, python_exe, agate_scripts, home, "--check")
    assert result.returncode == 0
    assert "git" in result.output
    assert "bash" in result.output
    assert "yaml" in result.output
    assert ("python3" in result.output) or ("python" in result.output)


@pytest.mark.windows_smoke
def test_bdd_8_env_check_missing_pyyaml_guidance(python_exe, run_cli, agate_scripts, tmp_path):
    venv = tmp_path / "noyaml"
    created = subprocess.run(
        [python_exe, "-m", "venv", str(venv)], capture_output=True, text=True, encoding="utf-8"
    )
    assert created.returncode == 0
    venv_bin = venv / ("Scripts" if os.name == "nt" else "bin")
    assert venv_bin.is_dir()

    home = tmp_path / "home"
    path = str(venv_bin) + os.pathsep + os.environ.get("PATH", "")
    result = _run_install(run_cli, python_exe, agate_scripts, home, "--check", extra_env={"PATH": path})
    assert result.returncode != 0
    assert "yaml" in result.output
    if sys.platform == "win32":
        assert ("PYTHONUTF8" in result.output) or ("Git for Windows" in result.output)
    else:
        assert "pip install" in result.output


# ============================================================
# TAG0032 版本管理生命周期可用性批 — 断点一：入口断链修复
#   BDD-1~5（1:1 映射 P1-requirements.md §3.1）
#   命名前缀 test_tag0032_bdd_N_（区分 TAG0008 既有 test_bdd_1..8）
#   被测行为由 P4 实现（M1 软链 fail-closed 守卫 / M2 根 scripts/ 副本 /
#   M6 install.sh --versions）——P3 当前全部红灯（B 类：断言失败）。
#   平台无关：os.symlink 失败 → pytest.skip（同 test_agate_version_resolve.test_bdd_30）；
#   隔离 HOME 用 HOME+USERPROFILE 双 env（_run_install）；install.sh 经 bash fixture 调用。
# ============================================================


def _repo_root_from_scripts(agate_scripts):
    """agate/scripts/ → 仓库根（install.sh 所在处）。"""
    return Path(agate_scripts).parent.parent


def _legacy_symlink_home(tmp_path):
    """构造 legacy 软链布局隔离 HOME：~/.agate 是软链 → 一棵 git 工作树目录。

    返回 (home, legacy_target)。os.symlink 失败（Windows 无权限）→ 调用方 pytest.skip。
    """
    legacy_target = tmp_path / "legacy-src" / "agate"
    (legacy_target / "scripts").mkdir(parents=True)
    (legacy_target / "assets").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    os.symlink(str(legacy_target), str(home / ".agate"))
    return home, legacy_target


_VERSION_DIR_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def _dir_has_version_subdir(path):
    return any(_VERSION_DIR_RE.match(p.name) for p in Path(path).iterdir() if p.is_dir())


def test_tag0032_bdd_1_legacy_symlink_install_fail_closed(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-1：legacy 软链布局下 install 被 fail-closed 拒绝，软链目标不被穿透污染。"""
    _tag_upstream(git_repo)
    try:
        home, legacy_target = _legacy_symlink_home(tmp_path)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，legacy 软链布局无法构建")

    result = _run_install(
        run_cli, python_exe, agate_scripts, home, repo_url=py_path(git_repo.path)
    )

    assert result.returncode != 0, "软链布局下 install 应 fail-closed（exit 非 0）"
    assert not (legacy_target / "repo").exists(), "拒绝后不得穿透软链建 repo/"
    assert not _dir_has_version_subdir(legacy_target), "拒绝后不得穿透软链建 vX.Y.Z/"


def test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-2：拒绝信息含可 grep 的三段命令片段级迁移指引，三者缺一即 FAIL。"""
    _tag_upstream(git_repo)
    try:
        home, _legacy_target = _legacy_symlink_home(tmp_path)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，legacy 软链布局无法构建")

    result = _run_install(
        run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=py_path(git_repo.path)
    )
    out = result.output

    # 1. 备份软链
    assert "mv ~/.agate" in out and (".bak" in out or ".old" in out), "缺『备份软链』指引"
    # 2. 建目录根
    assert "mkdir -p ~/.agate" in out or ("mkdir" in out and "~/.agate" in out), "缺『建目录根』指引"
    # 3. 装版本（带版本标识 latest / v<X.Y.Z> / --versions）
    assert (
        "install.sh --versions" in out
        or re.search(r"agate-install\.py\s+(latest|v[0-9]+\.[0-9]+\.[0-9]+)", out)
    ), "缺『装版本』指引（带版本标识）"


def test_tag0032_bdd_3_plain_dir_not_falsely_rejected(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-3：非软链（普通目录 / 全新）布局 install 不被新拒绝逻辑误伤。

    判据：exit 0 + 版本目录建立。附加 M2（根 scripts/ 副本两条安装路径都落地）——
    指定版本路径同样建立根入口命令，故一并断言（当前未建 → 红灯）。
    """
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    (home / ".agate").mkdir(parents=True)  # 普通目录，非软链

    result = _run_install(
        run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=py_path(git_repo.path)
    )

    assert result.returncode == 0, "普通目录布局不应被 fail-closed 误伤"
    assert (home / ".agate" / "v0.48.0").is_dir(), "版本目录应建立成功"
    assert (home / ".agate" / "scripts" / "agate-install.py").is_file(), (
        "M2：指定版本安装路径也应建立根 ~/.agate/scripts/ 入口副本"
    )


def test_tag0032_bdd_4_root_scripts_established_and_executable(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-4 判据 1：install 完成后 ~/.agate/scripts/agate-install.py 存在且 --help exit 0。"""
    _tag_upstream(git_repo)
    home = tmp_path / "home"

    result = _run_install(
        run_cli, python_exe, agate_scripts, home, repo_url=py_path(git_repo.path)
    )
    assert result.returncode == 0

    root_entry = home / ".agate" / "scripts" / "agate-install.py"
    assert root_entry.is_file(), "README 快速上手入口 ~/.agate/scripts/agate-install.py 应存在"

    helped = run_cli(
        python_exe, str(root_entry), "--help",
        env={"HOME": str(home), "USERPROFILE": str(home)},
    )
    assert helped.returncode == 0, "根入口命令 --help 应 exit 0（不再 No such file）"


def test_tag0032_bdd_4b_root_scripts_copy_refreshed_on_reinstall(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-4 判据 2：重跑 agate-install.py latest 后根 scripts/ 副本随 current 刷新
    （决策 B1 副本语义单测锁）。"""
    _tag_upstream(git_repo)  # v0.43.0 / v0.48.0
    home = tmp_path / "home"
    url = py_path(git_repo.path)

    first = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=url)
    assert first.returncode == 0
    root_scripts = home / ".agate" / "scripts"
    assert (root_scripts / "agate-install.py").is_file()

    # 新增更高版本 tag，协议 scripts/ 内含 sentinel
    (git_repo.path / "agate" / "scripts" / "SENTINEL_v0_49_0.txt").write_text(
        "refreshed\n", encoding="utf-8"
    )
    git_repo.commit("bump v0.49.0")
    git_repo.git("tag", "v0.49.0")

    second = _run_install(run_cli, python_exe, agate_scripts, home, repo_url=url)
    assert second.returncode == 0
    assert (root_scripts / "SENTINEL_v0_49_0.txt").is_file(), (
        "重跑 latest 后根 ~/.agate/scripts/ 副本应随 current 版本刷新"
    )


def test_tag0032_bdd_5_install_sh_versions_bootstrap(
    git_repo, python_exe, run_cli, agate_scripts, bash, tmp_path, py_path
):
    """BDD-5：新机器按 install.sh --versions 官方路径从零进入版本管理布局，
    且不在任何源仓库树内新建 repo/ / vX.Y.Z/。"""
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    (home / ".agate").mkdir(parents=True)  # 普通目录（非软链）

    # AGATE_REPO_DIR 指向预置 git 仓库，令 pre-P4 legacy 分支快速失败（不触网络 clone）
    prep = git_repo.__class__(tmp_path / "prep-repo")
    (prep.path / "README.md").write_text("x\n", encoding="utf-8")
    prep.commit("prep")

    repo_root = _repo_root_from_scripts(agate_scripts)
    result = run_cli(
        bash, str(repo_root / "install.sh"), "--versions",
        env={
            "HOME": str(home),
            "USERPROFILE": str(home),
            "AGATE_REPO_URL": str(py_path(git_repo.path)),
            "AGATE_REPO_DIR": str(prep.path),
        },
    )
    assert result.returncode == 0, "install.sh --versions 应成功进入版本管理布局"

    agate_home = home / ".agate"
    assert (agate_home / "repo").is_dir(), "应建立 repo/ 主克隆"
    assert _dir_has_version_subdir(agate_home), "应建立 vX.Y.Z/ 版本目录"
    assert (agate_home / "current").exists() and (agate_home / "latest").exists(), "应建立 current/latest 指针"
    assert (agate_home / "scripts" / "agate-install.py").is_file(), "应建立根 scripts/"

    porcelain = _git(
        shutil.which("git") or "git", "-C", str(repo_root), "status", "--porcelain"
    ).stdout
    bad = [
        ln for ln in porcelain.splitlines()
        if "/repo/" in ln or re.search(r"/v[0-9]+\.[0-9]+\.[0-9]+/", ln)
    ]
    assert not bad, f"install.sh --versions 不得污染源仓库树：{bad}"
