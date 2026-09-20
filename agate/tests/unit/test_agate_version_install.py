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

import helpers_tag_repo as H


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
    # TAG0037（P2 §6 T-10 / eng N-1）：agate_common / agate-install 现依赖 agate_package.py——夹具拷贝清单须同时含它
    # （存在才拷：P4 落地前该文件尚不存在，夹具不得因此炸掉既有用例）。
    for name in ("agate-install.py", "agate_common.py", "agate_package.py"):
        if (_REAL_AGATE_SCRIPTS / name).is_file():
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


def test_bdd_2_version_dir_is_tag_body_not_worktree(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    """BDD-2（TAG0008）[DESIGN_GAP-B1，TAG0037 P3 组 B 改写，见 P3-test-cases.md §6]：原断言"版本目录是 tag 的 git worktree（登记在
    repo/ 的 worktree list 且 HEAD == tag 提交）"与 TAG0037 新契约（BDD-22 只装本体、D-1 git plumbing 构建器取代 git worktree add）直接矛盾。
    改写为等价的新契约断言：版本目录存在、**不是** worktree（无 .git、repo/ 的 worktree list 不含它）、其内容取自该 tag 的 blob。"""
    _tag_upstream(git_repo)
    home = tmp_path / "home"

    result = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=py_path(git_repo.path))
    assert result.returncode == 0

    version_dir = home / ".agate" / "v0.48.0"
    assert version_dir.is_dir()
    assert not (version_dir / ".git").exists()

    git_exe = shutil.which("git")
    assert git_exe
    repo_clone = home / ".agate" / "repo"
    wt = _worktree_porcelain(git_exe, repo_clone)
    assert os.path.normcase(str(version_dir)) not in os.path.normcase(wt)
    blob = _git(git_exe, "-C", str(repo_clone), "show", "v0.48.0:agate/scripts/README.md").stdout
    assert (version_dir / "agate" / "scripts" / "README.md").read_text(encoding="utf-8") == blob


def test_bdd_3_reinstall_idempotent(
    git_repo, python_exe, run_cli, agate_scripts, tmp_path, py_path
):
    _tag_upstream(git_repo)
    home = tmp_path / "home"
    url = py_path(git_repo.path)

    first = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=url)
    assert first.returncode == 0

    version_dir = home / ".agate" / "v0.48.0"
    before = H.snapshot_tree(version_dir, ignore_bytecode=False)

    result = _run_install(run_cli, python_exe, agate_scripts, home, "v0.48.0", repo_url=url)
    assert result.returncode == 0

    assert version_dir.is_dir()
    # [DESIGN_GAP-B1，TAG0037 P3 组 B 改写]：原末尾断言"repo/ 的 worktree list 中该版本目录恰出现 1 次"是旧 git worktree 形态的幂等判据，
    # 与新契约（版本目录不再是 worktree）矛盾。等价新判据：二次安装不改动版本目录（内容逐字节不变）、不重复建目录、不遗留工作容器。
    assert H.snapshot_tree(version_dir, ignore_bytecode=False) == before
    assert sorted(n for n in os.listdir(str(home / ".agate")) if n.startswith("v")) == ["v0.48.0"]
    assert not [n for n in os.listdir(str(home / ".agate")) if n.startswith((".agate-tmp-", ".agate-bak-"))]


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
    before_uninstall = H.snapshot_tree(home / ".agate" / "v0.43.0", ignore_bytecode=False)

    result = _run_install(run_cli, python_exe, agate_scripts, home, "--uninstall", "v0.43.0")
    assert result.returncode != 0
    assert "v0.43.0" in result.output
    assert ("myproject" in result.output) or (".agate-version" in result.output)
    assert (home / ".agate" / "v0.43.0").is_dir()
    # [DESIGN_GAP-B1，TAG0037 P3 组 B 改写]：原末尾断言"该版本目录仍登记在 repo/ 的 worktree list"是旧 worktree 形态的"未被卸载"判据，
    # 新契约下版本目录不再是 worktree。等价新判据：被拒绝卸载的版本目录内容逐字节不变。
    assert H.snapshot_tree(home / ".agate" / "v0.43.0", ignore_bytecode=False) == before_uninstall


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

    repo_root = _repo_root_from_scripts(agate_scripts)
    result = run_cli(
        bash, str(repo_root / "install.sh"), "--versions",
        env={
            "HOME": str(home),
            "USERPROFILE": str(home),
            "AGATE_REPO_URL": str(py_path(git_repo.path)),
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


# ============================================================
# DEBT0034：legacy 软链拒绝文案「双写漂移」守护
#
# 背景：同一份"三步迁移指引"在两侧各自维护——agate-install.py 的
# _LEGACY_SYMLINK_MSG（模块常量）与 install.sh 的 heredoc。原有 BDD-2 只测
# Python 侧（_run_install 跑 agate-install.py），**install.sh 侧漂移不被测**。
#
# 设计取舍（为何不"收敛到单一来源"）：
#   两条入口的**首句主体刻意不同**——各自说明是哪个命令穿透软链，这是有用的
#   上下文，不应强行统一。真正必须一致的是【三步迁移指引】——它是用户照做的
#   操作步骤，任一侧漂移都会误导用户。故本用例锁定指引部分，放开首句。
#
# 为何不用"install.sh 委托 agate-install.py 打印"：软链检测发生在 clone 之前，
# 此刻无 agate-install.py 可用（curl|bash 场景 SCRIPT_DIR 是 cwd）——委托不可行。
# ============================================================


def _migration_steps(text):
    """从拒绝文案中抽出三步迁移指引（三条命令片段）——两侧须一致。"""
    steps = {}
    m = re.search(r"mv\s+~?/?\.agate\s+\S*\.bak", text)
    steps["backup"] = m.group(0) if m else None
    m = re.search(r"mkdir\s+-p\s+~?/?\.agate", text)
    steps["mkdir"] = m.group(0) if m else None
    m = re.search(r"install\.sh\s+--versions", text)
    steps["install"] = m.group(0) if m else None
    return steps


def test_debt0034_migration_steps_consistent_across_entries(agate_scripts):
    """两步入口（agate-install.py / install.sh）的「三步迁移指引」须逐片段一致。"""
    repo_root = _repo_root_from_scripts(agate_scripts)
    py_text = (agate_scripts / "agate-install.py").read_text(encoding="utf-8")
    sh_text = (repo_root / "install.sh").read_text(encoding="utf-8")

    py_steps = _migration_steps(py_text)
    sh_steps = _migration_steps(sh_text)

    for key in ("backup", "mkdir", "install"):
        assert py_steps[key] is not None, f"Python 侧缺三步指引片段：{key}"
        assert sh_steps[key] is not None, f"install.sh 侧缺三步指引片段：{key}"
        assert py_steps[key] == sh_steps[key], (
            f"三步迁移指引漂移（{key}）：Python 侧 {py_steps[key]!r} "
            f"≠ install.sh 侧 {sh_steps[key]!r}——两处须同步（DEBT0034）"
        )


def test_debt0034_install_sh_heredoc_is_guarded(agate_scripts):
    """install.sh 的软链拒绝分支须是 heredoc 形态（防被改成不一致的动态拼接）。"""
    repo_root = _repo_root_from_scripts(agate_scripts)
    sh_text = (repo_root / "install.sh").read_text(encoding="utf-8")
    assert re.search(r"if\s+\[\s+-L\s+\"\$AGATE_VER_ROOT\"\s+\]", sh_text), (
        "install.sh 缺 `[ -L \"$AGATE_VER_ROOT\" ]` 软链检测（或变量名被改）"
    )
    assert "cat >&2 <<'EOF'" in sh_text, (
        "install.sh 的拒绝文案不再是 heredoc（引号形态变化会让变量被展开，"
        "进而与 Python 侧文案漂移）"
    )



# ============================================================
# TAG0037 P3 组 B（批 B1a）：在线安装只装本体（BDD-22 / 24）、幂等且不污染（BDD-26）、软链守卫 T-14（BDD-32 / 51②）、
#   迁移文案跨入口一致（BDD-35）、版本号 fullmatch。
#   被测：agate-install.py（P4 批 B1a：git plumbing 构建器取代 git worktree add；软链守卫规范化）。
#   夹具：合成上游 file:// bare 仓库（helpers_tag_repo，多 tag：正常 / 老 tag / 畸形 tag），隔离 AGATE_HOME / HOME；
#   上述既有 TAG0008 / TAG0032 / DEBT0034 用例的函数体未改（仅 `_tag_upstream` 夹具助手增拷 agate_package.py；
#   test_tag0032_bdd_5 清理已废弃旧变量的引用，见 P3-test-cases.md §6 修改登记）。
# ============================================================

_T14_VARIANTS = ["L", "L/", "L//", "L/.", "L/.."]
_T14_IDS = [f"t14-{i}-{v.replace('/', 's').replace('.', 'd')}" for i, v in enumerate(_T14_VARIANTS)]
_STEP_REGEXES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _online(agate_scripts, tmp_path, agate_home, synth, *args, extra_env=None):
    env = H.tool_env(tmp_path / "home", agate_home=agate_home, extra={"AGATE_REPO_URL": synth.url, **(extra_env or {})})
    return H.run_tool([sys.executable, agate_scripts / "agate-install.py", *args], env=env, cwd=tmp_path)


def _ptr(agate_home):
    out = {}
    for name in ("latest", "current"):
        p = Path(agate_home) / name
        out[name] = ("link", os.readlink(str(p))) if p.is_symlink() else (("file", p.read_text(encoding="utf-8")) if p.is_file() else None)
    return out


def _shape(agate_home):
    snap = H.snapshot_tree(agate_home)
    return {k: v for k, v in snap.items() if k != "repo" and not k.startswith("repo/")}


def _leftover_containers(agate_home):
    return sorted(n for n in os.listdir(str(agate_home)) if n.startswith((".agate-tmp-", ".agate-bak-")))


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针断言仅 POSIX")
def test_bdd_22_online_install_latest_installs_body_only(agate_scripts, tmp_path, synth):
    """BDD-22：`agate-install.py latest`——vX.Y.Z/ 文件集合 == F_pkg；agate-workspace / docs / site / archived / .github / HANDOFF-*.md 均不存在；
    无 .git 指针；AGATE_ROOT 为 vX.Y.Z/agate；根 scripts/ 仍由 _sync_root_scripts 建立；不遗留临时容器。"""
    agate_home = tmp_path / "ah"
    proc = _online(agate_scripts, tmp_path, agate_home, synth, "latest")
    assert proc.returncode == 0, proc.stderr
    vdir = agate_home / H.MAIN_TAG
    assert H.file_set(vdir) == synth.expected_package(H.MAIN_TAG)
    for noise in ("agate-workspace", "docs", "site", "archived", ".github", "HANDOFF-X.md", ".git", "README.md", "install.sh"):
        assert not (vdir / noise).exists(), f"{noise} 不应被安装"
    assert not (vdir / "agate" / "tests").exists()
    assert (agate_home / "repo" / ".git").exists(), "在线路径保留 repo/（用户决策 ②）"
    assert (agate_home / "scripts" / "agate-install.py").is_file()
    assert _leftover_containers(agate_home) == []
    res = H.run_tool([sys.executable, agate_home / "scripts" / "agate-resolve.py"], env=H.tool_env(tmp_path / "home", agate_home=agate_home), cwd=tmp_path)
    assert res.returncode == 0, res.stderr
    assert f"AGATE_ROOT={(vdir / 'agate').resolve()}" in res.stdout


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针断言仅 POSIX")
@pytest.mark.parametrize("tag", [H.OLD_TAG, H.NO_NOTICES_TAG], ids=["bdd24-1-old-tag-without-exclusion-config", "bdd24-2-old-tag-without-notices"])
def test_bdd_24_1_install_historical_tag_gets_body_only_and_pointers_unchanged(tag, agate_scripts, tmp_path, synth):
    """BDD-24 ①：版本根已有 repo/ 与 latest → vN；装更老的历史 tag（树内无任何排除机制文件 / 缺 NOTICES.md）——
    vX.Y.Z/ 文件集合 == 对该 tag 应用边界得到的 F_pkg（不因缺配置退回全量）；latest / current 指针不变；项目 .agate-version 钉版后 resolve 得该版本；repo/ 仍在。"""
    agate_home = tmp_path / "ah"
    first = _online(agate_scripts, tmp_path, agate_home, synth, "latest")
    assert first.returncode == 0, first.stderr
    ptr_before = _ptr(agate_home)
    proc = _online(agate_scripts, tmp_path, agate_home, synth, tag)
    assert proc.returncode == 0, proc.stderr
    assert H.file_set(agate_home / tag) == synth.expected_package(tag)
    assert _ptr(agate_home) == ptr_before, "`vX.Y.Z` 只预装不改指针（既有契约）"
    assert (agate_home / "repo" / ".git").exists()
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".agate-version").write_text(f"agate: {tag}\n", encoding="utf-8")
    res = H.run_tool([sys.executable, agate_home / "scripts" / "agate-resolve.py"], env=H.tool_env(tmp_path / "home", agate_home=agate_home), cwd=project)
    assert res.returncode == 0, res.stderr
    assert f"AGATE_VERSION={tag}" in res.stdout


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针断言仅 POSIX")
def test_bdd_24_2_malformed_tag_without_agate_scripts_fails_closed(agate_scripts, tmp_path, synth):
    """BDD-24 ②：树内无 agate/scripts/ 的畸形 tag → exit 1，stderr 指明缺 agate/scripts，不留半装版本目录 / 临时容器，指针不变。"""
    agate_home = tmp_path / "ah"
    first = _online(agate_scripts, tmp_path, agate_home, synth, "latest")
    assert first.returncode == 0, first.stderr
    ptr_before = _ptr(agate_home)
    versions_before = sorted(n for n in os.listdir(str(agate_home)) if n.startswith("v"))
    proc = _online(agate_scripts, tmp_path, agate_home, synth, H.MALFORMED_TAG)
    assert proc.returncode == 1, proc.stderr
    assert "agate/scripts" in proc.stderr
    assert not (agate_home / H.MALFORMED_TAG).exists()
    assert sorted(n for n in os.listdir(str(agate_home)) if n.startswith("v")) == versions_before
    assert _leftover_containers(agate_home) == []
    assert _ptr(agate_home) == ptr_before


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针断言仅 POSIX")
def test_bdd_26_online_reinstall_is_idempotent_and_does_not_pollute_source(agate_scripts, tmp_path, synth):
    """BDD-26：同一 AGATE_HOME 连续两次 `agate-install.py latest`，再 `agate-install.py <同版本>`——第二次起不报错、不重复建版本目录、指针幂等；
    源 checkout（脚本所在仓库）无 repo/ / vX.Y.Z/ / 临时容器产物。既有 test_bdd_3 / test_tag0032_bdd_3/4/5 / test_tag0032_bdd_13/14 保持通过（本文件其余用例）。"""
    agate_home = tmp_path / "ah"
    r1 = _online(agate_scripts, tmp_path, agate_home, synth, "latest")
    assert r1.returncode == 0, r1.stderr
    shape1, ptr1 = _shape(agate_home), _ptr(agate_home)
    r2 = _online(agate_scripts, tmp_path, agate_home, synth, "latest")
    assert r2.returncode == 0, r2.stderr
    r3 = _online(agate_scripts, tmp_path, agate_home, synth, H.MAIN_TAG)
    assert r3.returncode == 0, r3.stderr
    assert "已安装" in r3.stdout or "跳过" in r3.stdout
    assert _shape(agate_home) == shape1 and _ptr(agate_home) == ptr1
    root = agate_scripts.parent.parent
    porcelain = _git(shutil.which("git") or "git", "-C", str(root), "status", "--porcelain", "--untracked-files=all").stdout
    pat = re.compile(r"(^|/)(repo|v[0-9]+\.[0-9]+\.[0-9]+|\.agate-(tmp|bak)-[^/]*)(/|$)")
    assert not [ln for ln in porcelain.splitlines() if pat.search(ln[3:].strip())], "在线安装不得污染源仓库树"


@pytest.mark.parametrize("bad", ["v0.73.0\n", "v1.2", "../evil", "v0.73.0-tagtest.1"], ids=["bad-newline", "bad-two-part", "bad-traversal", "bad-prerelease-as-version"])
def test_online_install_rejects_invalid_version_strings(bad, agate_scripts, tmp_path, synth):
    """P2 §3.3 / cso F-9：`_VERSION_RE` 改 fullmatch 口径——结尾换行 / 两段 / 路径穿越 / 预发布后缀均拒（exit 2，"非法版本号"），不建任何版本目录。"""
    agate_home = tmp_path / "ah"
    proc = _online(agate_scripts, tmp_path, agate_home, synth, bad)
    assert proc.returncode == 2, proc.stderr
    assert "非法版本号" in proc.stderr
    if agate_home.exists():
        assert not [n for n in os.listdir(str(agate_home)) if n.startswith("v")]
    assert not (tmp_path / "evil").exists()


def _symlink_home_fixture(tmp_path):
    target = tmp_path / "src" / "agate"
    (target / "scripts").mkdir(parents=True)
    (target / "assets").mkdir()
    (target / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home-link"
    home.mkdir()
    link = home / ".agate"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    return link, target


@pytest.mark.parametrize("variant", _T14_VARIANTS, ids=_T14_IDS)
@pytest.mark.parametrize("args", [(), ("latest",), (H.MAIN_TAG,)], ids=["bdd32-1-no-args", "bdd32-2-latest", "bdd32-3-version"])
def test_bdd_32_t14_agate_install_symlink_home_fail_closed(args, variant, agate_scripts, tmp_path, synth):
    """BDD-32 + T-14（agate-install 入口）：AGATE_HOME 是软链（含 L/ L// L/. L/.. 变体）——无参 / latest / vX.Y.Z 三种调用均 exit 1，
    stderr 含三步迁移片段，软链目标（金丝雀）不被穿透污染（无 repo/、无 vX.Y.Z/），物理父目录不新增条目。"""
    link, target = _symlink_home_fixture(tmp_path)
    before = H.snapshot_tree(target)
    parent_listing = sorted(os.listdir(str(target.parent)))
    proc = _online(agate_scripts, tmp_path, str(link) + variant[1:], synth, *args)
    assert proc.returncode == 1, f"rc={proc.returncode}\n{proc.stderr}"
    for key, rx in _STEP_REGEXES.items():
        assert rx.search(proc.stderr), f"stderr 缺三步迁移片段 {key}: {proc.stderr}"
    assert H.snapshot_tree(target) == before
    assert not (target / "repo").exists()
    assert sorted(os.listdir(str(target.parent))) == parent_listing


def test_bdd_51_2_install_into_symlinked_full_version_root_is_refused_with_resolution_note(agate_scripts, tmp_path, synth):
    """BDD-51 ②：AGATE_HOME 是软链 → 完整版本根（含 vX.Y.Z/agate、latest、current）——`agate-install.py latest` 一律拒绝（exit 1，按 BDD-32），
    迁移文案同时说明"若 ~/.agate 是指向完整版本根的软链，解析仍可用，仅安装类命令需先改为实体目录或对软链目标直接执行安装"。"""
    real = tmp_path / "bigdisk" / "agate-root"
    (real / H.MAIN_TAG / "agate" / "scripts").mkdir(parents=True)
    os.symlink(H.MAIN_TAG, str(real / "latest"))
    os.symlink("latest", str(real / "current"))
    home = tmp_path / "home-link"
    home.mkdir()
    try:
        os.symlink(str(real), str(home / ".agate"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    before = H.snapshot_tree(real)
    proc = _online(agate_scripts, tmp_path, home / ".agate", synth, "latest")
    assert proc.returncode == 1, proc.stderr
    assert "解析仍可用" in proc.stderr
    assert H.snapshot_tree(real) == before


def test_bdd_35_migration_steps_consistent_across_all_entries(agate_scripts):
    """BDD-35（DEBT0034 守护延续）：迁移三步出现的全部入口——install.sh（heredoc）、agate-install.py、install-offline.py、agate_common.py（resolve 侧）、
    UPGRADING 迁移小节——用 `_migration_steps` 同款正则抽取三片段，逐一相等（既有 test_debt0034_* 保留，本用例扩展到新增入口）。"""
    root = _repo_root_from_scripts(agate_scripts)
    texts = {
        "install.sh": (root / "install.sh").read_text(encoding="utf-8"),
        "agate-install.py": (agate_scripts / "agate-install.py").read_text(encoding="utf-8"),
        "install-offline.py": (agate_scripts / "install-offline.py").read_text(encoding="utf-8"),
        "agate_common.py": (agate_scripts / "agate_common.py").read_text(encoding="utf-8"),
        "UPGRADING.md": (root / "agate" / "UPGRADING.md").read_text(encoding="utf-8"),
    }
    steps = {name: _migration_steps(text) for name, text in texts.items()}
    for name, st in steps.items():
        for key in ("backup", "mkdir", "install"):
            assert st[key] is not None, f"{name} 缺三步迁移片段 {key}"
    ref = steps["install.sh"]
    for name, st in steps.items():
        assert st == ref, f"三步迁移片段漂移（{name}）: {st} ≠ install.sh 侧 {ref}"


@pytest.mark.skipif(sys.platform == "win32", reason="软链断言仅 POSIX")
def test_bdd_35_runtime_stderr_steps_identical_between_installer_and_resolver(agate_scripts, tmp_path, synth):
    """BDD-35（运行时口径）：软链基址下 agate-install.py 的拒绝 stderr 与 agate-resolve.py 的迁移提示，抽出的三片段逐一相等。"""
    link, _target = _symlink_home_fixture(tmp_path)
    inst = _online(agate_scripts, tmp_path, link, synth, "latest")
    res = H.run_tool([sys.executable, agate_scripts / "agate-resolve.py"], env=H.tool_env(tmp_path / "home", agate_home=link), cwd=tmp_path)
    assert inst.returncode == 1 and res.returncode == 1
    assert _migration_steps(inst.stderr) == _migration_steps(res.stderr)
    assert all(v is not None for v in _migration_steps(res.stderr).values())
