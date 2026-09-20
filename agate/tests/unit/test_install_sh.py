# tests/unit/test_install_sh.py — install.sh 行为（TAG0037 P3 组 B，批 E）
# 覆盖：BDD-29（无参 = --versions 别名，进入版本管理布局）、BDD-30（废弃 env AGATE_REPO_DIR / AGATE_SYMLINK 打 WARNING、
#       不创建其指向路径、脚本头注释不再引用）、BDD-31（遇软链 fail-closed；T-14 参数化 ["L","L/","L//","L/.","L/.."]）、
#       BDD-36（迁移三步在隔离环境真实可走通）、BDD-26（install.sh 重跑幂等、不污染源仓库树）。
# 被测：仓库根 install.sh（P4 批 E 重写）。P4 前：无参走"单软链"旧路径 → 断言失败 = B 类红灯。
# 隔离与安全：
#   * HOME / AGATE_HOME 均在 tmp_path 下；上游 = 合成 file:// bare 仓库（AGATE_REPO_URL）；
#   * PATH 前置一个 git 包装器：记录每次调用，并**拦截任何 http(s):// 克隆**（旧路径会去克隆真实 GitHub——红灯阶段也不许联网 / 落盘大仓库）；
#   * 不触碰真实 ~/.agate、开发 checkout、真实 origin；无 rm -rf（软链回滚验证用 os.rename，不删除任何内容）。
# 平台：POSIX 专用（bash + 软链）；Windows CI 只跑 windows_smoke，本文件不带该标记。

import os
import re
import shutil
import subprocess
import sys

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="install.sh 用例仅 POSIX（bash + 软链）")

_VARIANTS = ["L", "L/", "L//", "L/.", "L/.."]
_STEP_RES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _install_sh(agate_scripts):
    return agate_scripts.parent.parent / "install.sh"


def _git_guard(tmp_path):
    """PATH 前置 git 包装器：记录调用 + 拦截 http(s) 克隆。返回 (bin_dir, log_path)。"""
    real = shutil.which("git")
    assert real, "需要 git"
    bin_dir = tmp_path / "gitguard-bin"
    bin_dir.mkdir()
    log = tmp_path / "git-calls.log"
    script = bin_dir / "git"
    script.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *http://*|*https://*) echo "git guard: 网络克隆被拦截" >&2; exit 97;;\n'
        "esac\n"
        f'echo "$@" >> "{log}"\n'
        f'exec "{real}" "$@"\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir, log


def _env(home, guard_dir, synth, agate_home=None, extra=None):
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "AGATE_REPO_URL": synth.url,
        "PATH": str(guard_dir) + os.pathsep + os.environ.get("PATH", ""),
        "AGATE_ROOT": "",
    }
    if agate_home is not None:
        env["AGATE_HOME"] = str(agate_home)
    if extra:
        env.update(extra)
    return env


def _shape(agate_home):
    """版本根目录结构（忽略 repo/ 内部：git 对象库的文件名不保证跨克隆相同）。"""
    snap = H.snapshot_tree(agate_home)
    return {k: v for k, v in snap.items() if k != "repo" and not k.startswith("repo/")}


def _source_pollution(agate_scripts):
    """源 checkout 的 git status 中出现 repo/ vX.Y.Z/ 临时容器等本工具产物 → 返回违规行（不受并行编辑其它文件影响）。"""
    root = agate_scripts.parent.parent
    proc = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    pat = re.compile(r"(^|/)(repo|v[0-9]+\.[0-9]+\.[0-9]+|\.agate-(tmp|bak)-[^/]*)(/|$)")
    return [ln for ln in proc.stdout.splitlines() if pat.search(ln[3:].strip())]


def _assert_version_layout(synth, agate_home, label):
    assert agate_home.is_dir() and not agate_home.is_symlink(), f"{label}: ~/.agate 应为实体目录"
    assert (agate_home / "repo" / ".git").exists(), f"{label}: 缺 repo/"
    vdir = agate_home / H.MAIN_TAG
    assert vdir.is_dir(), f"{label}: 缺契约形态版本目录 {H.MAIN_TAG}"
    assert H.file_set(vdir) == synth.expected_package(H.MAIN_TAG), f"{label}: 版本目录应恰为本体包集合"
    assert (agate_home / "latest").exists() and (agate_home / "current").exists(), f"{label}: 缺 latest/current 指针"
    assert os.readlink(agate_home / "latest") == H.MAIN_TAG, f"{label}: latest → {H.MAIN_TAG}"
    assert os.readlink(agate_home / "current") == "latest", f"{label}: current → latest"
    assert (agate_home / "scripts" / "agate-install.py").is_file(), f"{label}: 缺根 scripts/agate-install.py"


def _symlink_home(tmp_path):
    """存量软链用户：<tmp>/home/.agate 是软链 → <tmp>/src/agate（含 scripts/ assets/ 与金丝雀文件）。"""
    target = tmp_path / "src" / "agate"
    (target / "scripts").mkdir(parents=True)
    (target / "assets").mkdir()
    (target / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    link = home / ".agate"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    return home, link, target


def _variant(link, variant):
    return str(link) + variant[1:]


# ---------------------------------------------------------------------------
# BDD-29：无参 / --versions 等价，进入版本管理布局
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("args", [(), ("--versions",)], ids=["bdd29-1-no-args", "bdd29-2-versions-alias"])
def test_bdd_29_install_sh_enters_version_layout(args, agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-29：无参与 --versions 均 exit 0，~/.agate 为实体目录，含 repo/、契约形态 vX.Y.Z/、latest/current 指针、根 scripts/。"""
    guard, _log = _git_guard(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    r = run_cli(bash, str(_install_sh(agate_scripts)), *args, env=_env(home, guard, synth), cwd=tmp_path)
    assert r.returncode == 0, f"install.sh {args} 应成功: {r.output}"
    _assert_version_layout(synth, home / ".agate", f"args={args}")
    assert not _source_pollution(agate_scripts), "install.sh 不得污染源 checkout"


def test_bdd_29_both_entries_produce_identical_tree(agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-29：两个隔离 HOME 下（无参 / --versions）得到的版本根目录结构树相等（忽略 repo/ 内部）。"""
    guard, _log = _git_guard(tmp_path)
    shapes = []
    for name, args in (("h-noarg", ()), ("h-versions", ("--versions",))):
        home = tmp_path / name
        home.mkdir()
        r = run_cli(bash, str(_install_sh(agate_scripts)), *args, env=_env(home, guard, synth), cwd=tmp_path)
        assert r.returncode == 0, r.output
        shapes.append(_shape(home / ".agate"))
    assert shapes[0] == shapes[1]
    assert shapes[0], "结构树不应为空"


def test_bdd_29_install_sh_has_no_symlink_logic():
    """BDD-29：install.sh 中不再含建软链逻辑（`ln -s` / `LINK_NAME` / `INSTALL_DIR` 不出现）。"""
    text = (H.REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    for token in ("ln -s", "ln -sfn", "LINK_NAME", "LINK_TARGET", "INSTALL_DIR"):
        assert token not in text, f"install.sh 仍含旧单软链逻辑: {token}"


def test_bdd_29_unknown_argument_rejected_with_usage_exit_2(agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-29：无参或 --versions 之外的参数 → 用法 + exit 2（旧实现会当无参走单软链路径）。"""
    guard, log = _git_guard(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    r = run_cli(bash, str(_install_sh(agate_scripts)), "--bogus", env=_env(home, guard, synth), cwd=tmp_path)
    assert r.returncode == 2, f"未知参数应 exit 2: rc={r.returncode} {r.output}"
    assert "--versions" in r.output, "用法提示应提到 --versions"
    assert not log.exists(), "拒绝未知参数前不应调用 git"
    assert not (home / ".agate").exists()


# ---------------------------------------------------------------------------
# BDD-30：废弃 env
# ---------------------------------------------------------------------------


def test_bdd_30_deprecated_env_warns_and_creates_nothing(agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-30：设置 AGATE_SYMLINK / AGATE_REPO_DIR → exit 0，stderr 含 WARNING 指明两变量已废弃且被忽略，其指向路径未被创建。"""
    guard, _log = _git_guard(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    x, y = tmp_path / "x", tmp_path / "y"
    env = _env(home, guard, synth, extra={"AGATE_SYMLINK": str(x), "AGATE_REPO_DIR": str(y)})
    r = run_cli(bash, str(_install_sh(agate_scripts)), env=env, cwd=tmp_path)
    assert r.returncode == 0, r.output
    assert "WARNING" in r.stderr
    assert "AGATE_SYMLINK" in r.stderr and "AGATE_REPO_DIR" in r.stderr
    assert "废弃" in r.stderr
    assert not x.exists() and not y.exists(), "废弃变量指向的路径不得被创建"
    _assert_version_layout(synth, home / ".agate", "deprecated-env")


def test_bdd_30_no_warning_when_deprecated_env_unset(agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-30 反面：未设置废弃变量时不打 WARNING（避免噪音）。"""
    guard, _log = _git_guard(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    r = run_cli(bash, str(_install_sh(agate_scripts)), env=_env(home, guard, synth), cwd=tmp_path)
    assert r.returncode == 0, r.output
    assert "AGATE_SYMLINK" not in r.stderr and "AGATE_REPO_DIR" not in r.stderr


def test_bdd_30_install_sh_header_and_usage_no_longer_reference_deprecated_names():
    """BDD-30：install.sh 头注释 / 末尾用法提示不再引用两变量（WARNING 文案是唯一出处）。"""
    lines = (H.REPO_ROOT / "install.sh").read_text(encoding="utf-8").splitlines()
    header = []
    for ln in lines:
        if ln.startswith("#") or not ln.strip():
            header.append(ln)
        else:
            break
    for name in ("AGATE_REPO_DIR", "AGATE_SYMLINK"):
        assert not any(name in ln for ln in header), f"头注释仍引用 {name}"
    for ln in lines:
        if ("AGATE_REPO_DIR" in ln or "AGATE_SYMLINK" in ln) and re.match(r"\s*(echo|printf)\b", ln):
            assert "WARNING" in ln or "废弃" in ln, f"用法提示 / 输出行仍把废弃变量当可用选项: {ln.strip()}"


def test_bdd_30_test_files_no_longer_reference_agate_repo_dir():
    """BDD-30：test_agate_version_install.py / test_version_lifecycle_e2e.py 中对 AGATE_REPO_DIR 的引用已清理（一次性交付项，
    仅对这两个文件的当前内容断言；新增 install.sh 用例引用它属于'设置废弃变量'的预期用法，不在本判定内）。"""
    for rel in ("unit/test_agate_version_install.py", "integration/test_version_lifecycle_e2e.py"):
        text = (H.REPO_ROOT / "agate" / "tests" / rel).read_text(encoding="utf-8")
        assert "AGATE_REPO_DIR" not in text, f"{rel} 仍引用已废弃的 AGATE_REPO_DIR"
        assert "pre-P4 legacy 分支" not in text, f"{rel} 仍含 'pre-P4 legacy 分支快速失败' 注释"


# ---------------------------------------------------------------------------
# BDD-31：遇软链 fail-closed（T-14 参数化）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", _VARIANTS, ids=[f"t14-{i}-{v.replace('/', 's').replace('.', 'd')}" for i, v in enumerate(_VARIANTS)])
@pytest.mark.parametrize("args", [(), ("--versions",)], ids=["bdd31-1-no-args", "bdd31-2-versions"])
def test_bdd_31_install_sh_symlink_home_fail_closed(args, variant, agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-31 + T-14：~/.agate 软链（含 L/ L// L/. L/.. 变体）→ exit 1；三步迁移片段；软链目标不新增 repo/ 与任何 vX.Y.Z/；未发生 git 调用。"""
    home, link, target = _symlink_home(tmp_path)
    guard, log = _git_guard(tmp_path)
    before = H.snapshot_tree(target)
    parent_listing = sorted(os.listdir(target.parent))
    r = run_cli(
        bash,
        str(_install_sh(agate_scripts)),
        *args,
        env=_env(home, guard, synth, agate_home=_variant(link, variant)),
        cwd=tmp_path,
    )
    assert r.returncode == 1, f"软链基址应 fail-closed exit 1: rc={r.returncode}\n{r.output}"
    if variant == "L/..":
        assert ".." in r.stderr, "含 `..` 分量应被拒绝并提示使用规范路径"
    else:
        for key, rx in _STEP_RES.items():
            assert rx.search(r.stderr), f"stderr 缺三步迁移片段 {key}: {r.stderr}"
    assert H.snapshot_tree(target) == before, "软链目标目录内容 / 金丝雀文件不得变化"
    assert not (target / "repo").exists()
    assert sorted(os.listdir(target.parent)) == parent_listing, "软链目标的物理父目录不得新增条目"
    assert not any(re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", n) for n in os.listdir(target))
    assert not log.exists(), "fail-closed 必须发生在任何 git 调用（clone）之前"


# ---------------------------------------------------------------------------
# BDD-36：迁移三步真实可走通
# ---------------------------------------------------------------------------


def test_bdd_36_migration_three_steps_walk_through(agate_scripts, bash, run_cli, python_exe, synth, tmp_path):
    """BDD-36：软链 ~/.agate → 旧 checkout；依次执行文案中的三步（备份 → 建目录根 → install.sh --versions）均 exit 0，
    结果满足 BDD-29 结构、agate-resolve exit 0，原软链（~/.agate.bak）完好且可回滚（以改名验证，不删除任何内容）。"""
    home, _link, target = _symlink_home(tmp_path)
    guard, _log = _git_guard(tmp_path)
    env = _env(home, guard, synth)
    # 三步命令取自 install.sh 自身的拒绝文案（文档即验收脚本）
    refuse = run_cli(bash, str(_install_sh(agate_scripts)), "--versions", env=env, cwd=tmp_path)
    assert refuse.returncode == 1
    cmds = {}
    for key, rx in _STEP_RES.items():
        m = rx.search(refuse.stderr)
        assert m, f"拒绝文案缺三步片段 {key}"
        cmds[key] = m.group(0)
    canary_before = H.snapshot_tree(target)

    steps = [
        cmds["backup"],
        cmds["mkdir"],
        f'{bash} "{_install_sh(agate_scripts)}" --versions',
    ]
    for cmd in steps:
        r = subprocess.run(
            [bash, "-c", cmd],
            env={**os.environ, **env},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
            cwd=str(tmp_path),
        )
        assert r.returncode == 0, f"迁移步骤失败: {cmd}\n{r.stdout}\n{r.stderr}"

    agate_home = home / ".agate"
    _assert_version_layout(synth, agate_home, "migration")
    res = run_cli(python_exe, str(agate_home / "scripts" / "agate-resolve.py"), cwd=tmp_path, env=env)
    assert res.returncode == 0, res.output
    assert f"AGATE_ROOT={(agate_home / H.MAIN_TAG / 'agate').resolve()}" in res.stdout

    bak = home / ".agate.bak"
    assert bak.is_symlink() and os.path.realpath(str(bak)) == os.path.realpath(str(target)), "原软链应完好"
    assert H.snapshot_tree(target) == canary_before, "迁移全程不得改动旧 checkout"
    # 可回滚：把新目录改名挪开、把 .bak 改名还原 → 回到软链态（等价 `rm -rf ~/.agate && mv ~/.agate.bak ~/.agate`，但不删任何内容）
    os.rename(str(agate_home), str(home / ".agate.migrated"))
    os.rename(str(bak), str(home / ".agate"))
    assert (home / ".agate").is_symlink()


# ---------------------------------------------------------------------------
# BDD-26：install.sh 重跑幂等、不污染源仓库树
# ---------------------------------------------------------------------------


def test_bdd_26_install_sh_rerun_is_idempotent_and_does_not_pollute_source(agate_scripts, bash, run_cli, synth, tmp_path):
    """BDD-26：同一 AGATE_HOME 连续两次 install.sh（无参）→ 第二次不报错、版本根结构不变、源 checkout 无新增 repo/ vX.Y.Z/ 产物。"""
    guard, _log = _git_guard(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    env = _env(home, guard, synth)
    r1 = run_cli(bash, str(_install_sh(agate_scripts)), env=env, cwd=tmp_path)
    assert r1.returncode == 0, r1.output
    shape1 = _shape(home / ".agate")
    r2 = run_cli(bash, str(_install_sh(agate_scripts)), env=env, cwd=tmp_path)
    assert r2.returncode == 0, r2.output
    assert _shape(home / ".agate") == shape1, "重跑后版本根结构应不变（幂等）"
    assert not _source_pollution(agate_scripts)
