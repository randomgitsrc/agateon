# tests/unit/test_agate_install_uninstall.py — 卸载引用保护扫描限流提示（TAG0031 DEBT0004，BDD-4/5）
# 被测：agate/scripts/agate-install.py 的 `_find_references`（卸载引用保护扫描，限深度
# `_SCAN_MAX_DEPTH=4` + mtime 窗口 `_SCAN_MTIME_WINDOW=365 天`限流）与 `_cmd_uninstall`
# （消费点，命中限流边界时应 stderr 输出 WARNING）。
#
# 设计（P2-design.md §1.1 簇 A）：`_find_references` 返回值由现状「plain list」改为
# `(refs, hit_limit)` 二元组——`depth > _SCAN_MAX_DEPTH` 触发剪枝或 `.agate-version` 命中但
# mtime 超窗跳过时置 `hit_limit=True`；`_cmd_uninstall` 解包后，`hit_limit` 为真时立即 stderr
# 输出 WARNING（不论 refs 是否为空——WARNING 与卸载判定放行与否是两件独立的事）。
#
# 当前状态（迁移前）：`_find_references` 仍返回 plain list（不是二元组）——本文件用
# `refs, hit_limit = module._find_references(...)` 解包，1 元素 list 解包进 2 个变量触发
# `ValueError: not enough values to unpack`（真实的项目内运行时失败 = B 类红灯语义，非测试
# 代码自身语法错误）；`_cmd_uninstall` 当前无 WARNING 输出机制，行为层断言同样失败。
#
# 网络隔离：`run_git` 全程 monkeypatch（不调真实 git），HOME 环境变量重定向到 tmp_path（同
# agate-install.py 模块 docstring 既有测试隔离约定），不触碰真实 ~/.agate。

import importlib.util
import os
import sys

import pytest

import helpers_tag_repo as H


def _load_script_module(agate_scripts, module_name, filename):
    """从 agate/scripts/ 加载脚本为模块；被测模块未实现 → ModuleNotFoundError（B 类红灯）。"""
    path = agate_scripts / filename
    if not path.is_file():
        raise ModuleNotFoundError(f"No module named '{module_name}' (被测模块未实现: {filename})")
    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bdd_4_find_references_and_uninstall_warn_when_scan_limit_hit(
    tmp_path, agate_scripts, monkeypatch, capsys
):
    """BDD-4：限流边界命中时输出 WARNING。

    Given ~/.agate 卸载引用扫描的目标目录树中存在超出扫描边界（深度 > 4）的项目，该项目的
    .agate-version 声明了即将卸载的版本
    When 执行 agate-install.py uninstall <version>
    Then stderr 输出 WARNING，明确提示"扫描存在深度/时间窗口限流，可能未覆盖全部引用"，卸载
    判定不因此项目被漏扫而误判为"无引用可安全卸载"
    """
    module = _load_script_module(agate_scripts, "agate_install_bdd4", "agate-install.py")

    home = tmp_path / "home"
    version = "v1.2.3"
    # 深度 5（a/b/c/d/e）> _SCAN_MAX_DEPTH(4) —— os.walk 遍历到 'e' 时 depth=5 即触发
    # dirs[:] = [] + continue 剪枝，'e' 自身的 .agate-version 也不会被检查到（漏扫场景）。
    deep = home / "a" / "b" / "c" / "d" / "e"
    deep.mkdir(parents=True)
    (deep / ".agate-version").write_text(f"agate: {version}\n", encoding="utf-8")

    # 机制层：_find_references 返回值应为 (refs, hit_limit) 二元组，命中限流边界 → hit_limit=True
    refs, hit_limit = module._find_references(str(home), version)
    assert hit_limit is True
    assert refs == []  # 深度限流剪枝，扫不到该项目——这正是 BDD-4 描述的"漏扫"风险本身

    # 行为层：_cmd_uninstall 命中限流边界应输出 WARNING（不论 refs 是否为空都要提示）
    agate_home = home / ".agate"
    agate_home.mkdir(parents=True)
    monkeypatch.setattr(module, "run_git", lambda *a, **k: (0, ""))
    monkeypatch.setenv("HOME", str(home))

    with pytest.raises(SystemExit):
        module._cmd_uninstall(str(agate_home), version)

    err = capsys.readouterr().err
    assert "WARNING" in err


def test_bdd_5_find_references_no_warning_within_scan_bounds(
    tmp_path, agate_scripts, monkeypatch, capsys
):
    """BDD-5：未命中限流边界时不产生 WARNING 噪音（边界流，防止过度提示）。

    Given ~/.agate 卸载引用扫描范围内所有 .agate-version 文件均在深度 ≤4 且 mtime 365 天窗口内
    When 执行卸载扫描
    Then stderr 不输出限流 WARNING（仅在真实命中限流边界时才提示，避免噪音掩盖真实信号）
    """
    module = _load_script_module(agate_scripts, "agate_install_bdd5", "agate-install.py")

    home = tmp_path / "home"
    version = "v1.2.3"
    # 深度 1（home/proj），远在 _SCAN_MAX_DEPTH(4) 与 mtime 365 天窗口内 —— 正常可扫场景
    proj = home / "proj"
    proj.mkdir(parents=True)
    (proj / ".agate-version").write_text(f"agate: {version}\n", encoding="utf-8")

    # 机制层：未命中限流边界 → hit_limit=False，且该真实引用应被正常发现（refs 非空）
    refs, hit_limit = module._find_references(str(home), version)
    assert hit_limit is False
    assert refs == [str(proj)]

    # 行为层：_cmd_uninstall 应因真实引用拒绝卸载（与 WARNING 无关的独立判定），但不应有
    # 限流 WARNING 噪音——refs 非空触发的是"拒绝卸载"提示，不是限流 WARNING
    agate_home = home / ".agate"
    agate_home.mkdir(parents=True)
    monkeypatch.setattr(module, "run_git", lambda *a, **k: (0, ""))
    monkeypatch.setenv("HOME", str(home))

    with pytest.raises(SystemExit):
        module._cmd_uninstall(str(agate_home), version)

    err = capsys.readouterr().err
    assert "WARNING" not in err


# ============================================================
# TAG0037 P3 组 B（批 B1a）：BDD-25 卸载兼容新旧形态，repo/ 有无均可 [参数化 ①②③] + 引用保护 + 旧 worktree 登记清扫（eng m-4）
#   上方两个 TAG0031 既有用例未改动（in-process、run_git 打桩）。本节用真实 CLI + 隔离 AGATE_HOME / HOME + 合成 file:// 上游。
#   被测：agate-install.py --uninstall（P4：旧形态版本目录才 `git worktree remove`；只要 repo/ 存在即 `git worktree prune`；repo/ 缺失不报错）。
# ============================================================

_V_NEW, _V_OLD = "v0.73.0", "v0.72.5"


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _cli(agate_scripts, tmp_path, agate_home, *args, synth=None):
    extra = {"AGATE_REPO_URL": synth.url} if synth is not None else None
    return H.run_tool(
        [sys.executable, agate_scripts / "agate-install.py", *args],
        env=H.tool_env(tmp_path / "home", agate_home=agate_home, extra=extra),
        cwd=tmp_path,
    )


def _ptr(agate_home):
    out = {}
    for name in ("latest", "current"):
        p = agate_home / name
        out[name] = ("link", os.readlink(str(p))) if p.is_symlink() else None
    return out


def _worktree_list(agate_home):
    return H.run_git(agate_home / "repo", "worktree", "list", "--porcelain").stdout.decode("utf-8")


def _hand_new_form(agate_home, version):
    """手工搭新形态版本目录（uninstall 不校验契约，仅需目录存在）。"""
    scripts = agate_home / version / "agate" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "README.md").write_text(f"# {version}\n", encoding="utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针 / 真实 worktree 断言仅 POSIX")
def test_bdd_25_1a_uninstall_new_form_with_repo_unpointed_version(agate_scripts, tmp_path, synth):
    """BDD-25 ①（新形态 + repo/ 存在）：卸载未被指针指向的版本 → exit 0，目录被移除，指针不变，repo/ 的 worktree list 无残留条目。"""
    agate_home = tmp_path / "ah"
    assert _cli(agate_scripts, tmp_path, agate_home, "latest", synth=synth).returncode == 0
    assert _cli(agate_scripts, tmp_path, agate_home, _V_OLD, synth=synth).returncode == 0
    assert not (agate_home / _V_OLD / ".git").exists(), "Given：新形态（无 .git）"
    ptr = _ptr(agate_home)
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_OLD)
    assert proc.returncode == 0, proc.stderr
    assert not (agate_home / _V_OLD).exists()
    assert _ptr(agate_home) == ptr
    assert str(agate_home / _V_OLD) not in _worktree_list(agate_home)
    assert (agate_home / _V_NEW / "agate" / "scripts").is_dir(), "其它版本不受影响"


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针 / 真实 worktree 断言仅 POSIX")
def test_bdd_25_1b_uninstall_pointed_version_repoints_to_latest_valid(agate_scripts, tmp_path, synth):
    """BDD-25 ①：卸载 latest/current 曾指向的版本 → 重指最新有效版本（不悬空），resolve 仍成功。"""
    agate_home = tmp_path / "ah"
    assert _cli(agate_scripts, tmp_path, agate_home, "latest", synth=synth).returncode == 0
    assert _cli(agate_scripts, tmp_path, agate_home, _V_OLD, synth=synth).returncode == 0
    assert not (agate_home / _V_NEW / ".git").exists(), "Given：新形态（无 .git）"
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_NEW)
    assert proc.returncode == 0, proc.stderr
    assert not (agate_home / _V_NEW).exists()
    assert os.readlink(str(agate_home / "latest")) == _V_OLD
    assert os.readlink(str(agate_home / "current")) == "latest"
    res = H.run_tool([sys.executable, agate_home / "scripts" / "agate-resolve.py"], env=H.tool_env(tmp_path / "home", agate_home=agate_home), cwd=tmp_path)
    assert res.returncode == 0, res.stderr
    assert f"AGATE_VERSION={_V_OLD}" in res.stdout
    assert str(agate_home / _V_NEW) not in _worktree_list(agate_home)


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针断言仅 POSIX")
def test_bdd_25_2_uninstall_new_form_without_repo(agate_scripts, tmp_path):
    """BDD-25 ②（offline / portable 安装：版本根无 repo/）：卸载 → exit 0，目录被移除，指针重指 / 清除不悬空，且不创建 repo/。"""
    agate_home = tmp_path / "ah"
    for v in (_V_OLD, _V_NEW):
        _hand_new_form(agate_home, v)
    os.symlink(_V_NEW, str(agate_home / "latest"))
    os.symlink("latest", str(agate_home / "current"))
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_NEW)
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert not (agate_home / _V_NEW).exists() and (agate_home / _V_OLD).is_dir()
    assert os.readlink(str(agate_home / "latest")) == _V_OLD
    assert not (agate_home / "repo").exists()
    only = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_OLD)
    assert only.returncode == 0, only.stderr
    assert _ptr(agate_home) == {"latest": None, "current": None}, "最后一个版本卸载后指针应清除（不悬空）"


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针 / 真实 worktree 断言仅 POSIX")
def test_bdd_25_3_uninstall_old_worktree_form_leaves_no_registration(agate_scripts, tmp_path, synth):
    """BDD-25 ③（旧形态 git worktree 整仓版本目录）：卸载 → exit 0，目录被移除，指针清除，repo/ 的 `git worktree list --porcelain` 无残留条目。
    旧形态由「旧安装器同款方式」显式构造并保留在测试中（新安装器不再产出该形态）。"""
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    H.run_git(tmp_path, "clone", "-q", "--", synth.url, str(agate_home / "repo"))
    H.run_git(agate_home / "repo", "worktree", "add", "--detach", str(agate_home / _V_OLD), _V_OLD)
    os.symlink(_V_OLD, str(agate_home / "latest"))
    os.symlink("latest", str(agate_home / "current"))
    assert (agate_home / _V_OLD / ".git").exists() and (agate_home / _V_OLD / "docs").is_dir(), "Given：旧整仓形态"
    assert str(agate_home / _V_OLD) in _worktree_list(agate_home)
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_OLD)
    assert proc.returncode == 0, proc.stderr
    assert not (agate_home / _V_OLD).exists()
    assert _ptr(agate_home) == {"latest": None, "current": None}
    assert str(agate_home / _V_OLD) not in _worktree_list(agate_home)


@pytest.mark.skipif(sys.platform == "win32", reason="软链指针 / 真实 worktree 断言仅 POSIX")
def test_bdd_25_5_uninstall_prunes_stale_worktree_registration_of_replaced_dir(agate_scripts, tmp_path, synth):
    """eng m-4：被替换的旧形态版本目录遗留 `repo/.git/worktrees/<vX>` 登记（目录被换成新形态后登记悬空）——卸载时只要 repo/ 存在即 `git worktree prune`，
    `worktree list --porcelain` 不再含该路径。（构造：旧形态目录改名挪走 → 原位置放新形态目录；不删除任何内容。）"""
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    H.run_git(tmp_path, "clone", "-q", "--", synth.url, str(agate_home / "repo"))
    H.run_git(agate_home / "repo", "worktree", "add", "--detach", str(agate_home / _V_OLD), _V_OLD)
    os.rename(str(agate_home / _V_OLD), str(tmp_path / "moved-away-old-form"))
    _hand_new_form(agate_home, _V_OLD)
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_OLD)
    assert proc.returncode == 0, proc.stderr
    assert not (agate_home / _V_OLD).exists()
    assert str(agate_home / _V_OLD) not in _worktree_list(agate_home)


def test_bdd_25_4_uninstall_reference_protection_unchanged(agate_scripts, tmp_path):
    """BDD-25：引用保护语义不变——HOME 下某项目 .agate-version 引用该版本时 exit 1 拒绝，版本目录保留（新形态同样适用）。"""
    agate_home = tmp_path / "ah"
    _hand_new_form(agate_home, _V_OLD)
    project = tmp_path / "home" / "myproject"
    project.mkdir(parents=True)
    (project / ".agate-version").write_text(f"agate: {_V_OLD}\n", encoding="utf-8")
    before = H.snapshot_tree(agate_home / _V_OLD, ignore_bytecode=False)
    proc = _cli(agate_scripts, tmp_path, agate_home, "--uninstall", _V_OLD)
    assert proc.returncode == 1
    assert "myproject" in proc.stderr or ".agate-version" in proc.stderr
    assert H.snapshot_tree(agate_home / _V_OLD, ignore_bytecode=False) == before
