# tests/integration/test_version_lifecycle_e2e.py — TAG0032 端到端：
#   「全新机器 → 版本布局 → 项目钉版 → 更新」全链路（隔离 HOME + 本地元仓库形态 repo）
# BDD 映射（1:1，P1-requirements.md §3.4）：
#   BDD-13（全链路逐步 exit 符合期望 + 幂等复跑不重复建目录）
#   BDD-14（全链路不污染源仓库树 —— TAG0008 教训回归锁）
# 命名前缀 test_tag0032_bdd_N_。
#
# 被测行为由 P4 实现（M6 install.sh --versions + 决策 A1/B1 + agate-install.py latest 别名）
# —— P3 当前红灯（B 类）：install.sh 无 --versions 分支 → 首步 exit 非 0，断言失败。
#
# fixture 形态铁律（I-5，TAG0008 教训）：_tag_meta_upstream 构造「协议在 agate/ 子目录、
#   根无 scripts/」的元仓库形态，不用「根即协议」模拟 repo 代替。
# 平台无关（AGENTS.md）：隔离 HOME 用 HOME+USERPROFILE 双 env；install.sh 经 bash fixture 调用；
#   ~/.agate 为普通目录（非软链，无 os.symlink 依赖）；不用临时目录字面量（走 tmp_path fixture）；
#   python 用 python_exe fixture；git 路径用 shutil.which。
# CI 无网 fallback（I-6）：本地构造 fixture 即默认路径（不依赖 GitHub）；真实 GitHub clone
#   属可选增强，无网 → 该增强 pytest.skip + 本地隔离 HOME 记录补证 P6-evidence。

import re
import shutil
import subprocess

import pytest

from conftest import GitRepo  # 复用 conftest 的 git-helper 封装（同 test_check_pruning.py 模式）

_STUB_GATE = 'import sys\nsys.stdout.write("{marker}\\n")\n'
_VERSION_DIR_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def _repo_root(agate_scripts):
    return agate_scripts.parent.parent


def _tag_meta_upstream(upstream, agate_scripts, marker="E2E-GATE-050"):
    """构造元仓库形态版本源 repo：agate/ 子目录含真实 resolve 依赖 + stub gate，根无 scripts/。

    两次 commit + v0.43.0 / v0.50.0 tag（v0.50.0 最新）。
    """
    ag = upstream.path / "agate"
    (ag / "scripts").mkdir(parents=True)
    (ag / "rules").mkdir(parents=True)
    (ag / "rules" / ".keep").write_text("", encoding="utf-8")
    # agate/scripts/ 内放真实版本工具（贴近真实元仓库形态：每个 tag 的 agate/scripts/
    # 本就含全套版本工具，P1-requirements §3.4）——令 install.sh --versions 走
    # $AGATE_HOME/repo/agate/scripts/agate-install.py 主路径、_sync_root_scripts 单源 copytree。
    for name in ("agate_common.py", "resolve-entry.py", "agate-install.py"):
        shutil.copy2(str(agate_scripts / name), str(ag / "scripts" / name))
    (ag / "scripts" / "pre-commit-gate.py").write_text(
        _STUB_GATE.format(marker=marker), encoding="utf-8"
    )
    upstream.commit("meta base v0.43.0")
    upstream.git("tag", "v0.43.0")
    (ag / "scripts" / "VERSION.txt").write_text("v0.50.0\n", encoding="utf-8")
    upstream.commit("meta v0.50.0")
    upstream.git("tag", "v0.50.0")


def _version_dirs(agate_home):
    return sorted(p.name for p in agate_home.iterdir() if p.is_dir() and _VERSION_DIR_RE.match(p.name))


def _git(*args):
    git_exe = shutil.which("git") or "git"
    return subprocess.run(
        [git_exe, *[str(a) for a in args]], capture_output=True, text=True, encoding="utf-8"
    )


def _enter_version_layout(run_cli, bash, agate_scripts, home, upstream_url, prep_dir):
    """官方路径进入版本管理布局：install.sh --versions（AGATE_REPO_URL 注入本地元仓库）。"""
    return run_cli(
        bash,
        str(_repo_root(agate_scripts) / "install.sh"),
        "--versions",
        env={
            "HOME": str(home),
            "USERPROFILE": str(home),
            "AGATE_REPO_URL": str(upstream_url),
            "AGATE_REPO_DIR": str(prep_dir),
        },
    )


def _prep_fastfail_repo(tmp_path):
    """预置 git 仓库，令 pre-P4 legacy 分支走 `git pull` 快速失败（不触网络 clone）。"""
    prep = GitRepo(tmp_path / "prep-repo")
    (prep.path / "README.md").write_text("x\n", encoding="utf-8")
    prep.commit("prep")
    return prep.path


def test_tag0032_bdd_13_full_lifecycle_new_machine_to_update(
    run_cli, python_exe, bash, agate_scripts, tmp_path, py_path
):
    """BDD-13：全链路逐步 exit 均符合期望，最终 gate 路径存在且可执行，幂等复跑不重复建目录。"""
    if not shutil.which("git"):
        pytest.skip("端到端全链路需要 git")
    home = tmp_path / "home"
    (home / ".agate").mkdir(parents=True)  # 普通目录（非软链）
    upstream = GitRepo(tmp_path / "upstream")
    _tag_meta_upstream(upstream, agate_scripts, marker="E2E-GATE-050")
    agate_home = home / ".agate"

    # 1. 进入版本布局（官方路径）→ exit 0
    r1 = _enter_version_layout(
        run_cli, bash, agate_scripts, home, py_path(upstream.path), _prep_fastfail_repo(tmp_path)
    )
    assert r1.returncode == 0, "步骤1 install.sh --versions 应 exit 0"
    assert (agate_home / "repo").is_dir()
    assert (agate_home / "current").exists() and (agate_home / "latest").exists()

    # 2. agate-install.py（装版本）已由 --versions 内部完成 → 版本目录唯一 + 根 scripts/ 就位
    assert _version_dirs(agate_home) and len(_version_dirs(agate_home)) == 1
    root_entry = agate_home / "scripts" / "agate-install.py"
    assert root_entry.is_file(), "步骤2 根 ~/.agate/scripts/ 应就位"

    # 3. 项目写 .agate-version 钉版 → exit 0（文件写入）
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".agate-version").write_text("agate: v0.50.0\n", encoding="utf-8")
    assert (project / ".agate-version").is_file()

    # 4. resolve-entry.py pre-commit → exit 0（gate 路径存在并被 exec）
    r4 = run_cli(
        python_exe,
        str(agate_home / "scripts" / "resolve-entry.py"),
        "pre-commit",
        cwd=str(project),
        env={"AGATE_ROOT": "", "HOME": str(home), "USERPROFILE": str(home)},
    )
    assert r4.returncode == 0, "步骤4 resolve-entry pre-commit 应 exit 0，不因 gate 缺失 exit 1"
    assert "E2E-GATE-050" in r4.output

    # 5. 再次 agate-install.py latest（幂等复跑）→ exit 0，不重复建版本目录
    before = _version_dirs(agate_home)
    r5 = run_cli(
        python_exe,
        str(agate_home / "scripts" / "agate-install.py"),
        "latest",
        env={
            "HOME": str(home),
            "USERPROFILE": str(home),
            "AGATE_REPO_URL": str(py_path(upstream.path)),
        },
    )
    assert r5.returncode == 0, "步骤5 agate-install.py latest 幂等复跑应 exit 0"
    assert _version_dirs(agate_home) == before, "幂等：版本目录数量不变"


def test_tag0032_bdd_14_e2e_no_source_pollution(
    run_cli, python_exe, bash, agate_scripts, tmp_path, py_path
):
    """BDD-14：端到端全链路执行完毕后，worktree 源仓库树无新增 repo/ / vX.Y.Z/ / 非预期未跟踪条目。"""
    if not shutil.which("git"):
        pytest.skip("端到端全链路需要 git")
    home = tmp_path / "home"
    (home / ".agate").mkdir(parents=True)
    upstream = GitRepo(tmp_path / "upstream")
    _tag_meta_upstream(upstream, agate_scripts, marker="E2E-GATE-050")

    r1 = _enter_version_layout(
        run_cli, bash, agate_scripts, home, py_path(upstream.path), _prep_fastfail_repo(tmp_path)
    )
    assert r1.returncode == 0

    project = tmp_path / "proj"
    project.mkdir()
    (project / ".agate-version").write_text("agate: v0.50.0\n", encoding="utf-8")
    run_cli(
        python_exe,
        str(home / ".agate" / "scripts" / "resolve-entry.py"),
        "pre-commit",
        cwd=str(project),
        env={"AGATE_ROOT": "", "HOME": str(home), "USERPROFILE": str(home)},
    )
    run_cli(
        python_exe,
        str(home / ".agate" / "scripts" / "agate-install.py"),
        "latest",
        env={
            "HOME": str(home),
            "USERPROFILE": str(home),
            "AGATE_REPO_URL": str(py_path(upstream.path)),
        },
    )

    repo_root = _repo_root(agate_scripts)
    porcelain = _git("-C", str(repo_root), "status", "--porcelain").stdout
    offenders = [
        ln for ln in porcelain.splitlines()
        if "/repo/" in ln
        or ln.rstrip().endswith("/repo")
        or re.search(r"/v[0-9]+\.[0-9]+\.[0-9]+/", ln)
    ]
    assert not offenders, f"源仓库树被污染：{offenders}"
    assert not (repo_root / "agate" / "repo").exists(), "worktree agate/ 内不得出现 repo/ 主克隆"
    assert not any(
        _VERSION_DIR_RE.match(p.name)
        for p in (repo_root / "agate").iterdir()
        if p.is_dir()
    ), "worktree agate/ 内不得出现 vX.Y.Z/ worktree"
