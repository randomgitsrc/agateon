# tests/integration/test_install_three_paths.py — 三条安装路径产出同一结构（TAG0037 P3 组 A，批 C1）
# 覆盖：BDD-4（H1 在线 / H2 离线 / H3 portable 三个独立 AGATE_HOME，装出的 vX.Y.Z/ 同构）、P2 §6 T-4（同构 + 运行后再比较）、
#       T-15 中属本批的部分（以 bundle 内入口执行 install-offline；真实树冒烟）。
# 依赖关系（允许暂时红灯，须写全）：H1 依赖批 B1a/E（只装本体）；H2 依赖批 A/B2；H3 依赖批 B1b（--adopt）+ C1（build）+
#   F1a（UPGRADING portable 小节，"文档即验收脚本"）——H3 相关用例只能在波次末（文档批之后）转绿。
# 隔离：全部在 tmp_path 下的 AGATE_HOME（H1/H2/H3）、file:// 合成上游、PATH 内 pip shim；不触碰真实 ~/.agate / 开发 checkout / origin。
# 比较口径：忽略 __pycache__ / *.pyc / *.pyo（D-13：契约约束"安装器交付的内容"，运行后态允许出现字节码）。
# 平台：POSIX 专用（pip shim / 软链指针 / bash 文档命令）；Windows CI 只跑 windows_smoke，本文件不带该标记。

import os
import re
import sys
from types import SimpleNamespace

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(not H.posix_shim_supported(), reason="三路径集成用例仅 POSIX（pip shim / 软链 / bash）")


def _kv(stdout):
    out = {}
    for line in stdout.splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k] = v
    return out


def _portable_block():
    """从 UPGRADING「portable 安装」小节取第一个 fenced 命令块（文档即验收脚本，BDD-17）。"""
    text = (H.REPO_ROOT / "agate" / "UPGRADING.md").read_text(encoding="utf-8")
    sec = re.search(r"^#{2,4}[^\n]*portable 安装[^\n]*\n(.*?)(?=^#{2,4} |\Z)", text, re.S | re.M)
    assert sec, "UPGRADING.md 缺「portable 安装」小节（批 F1a 待实现）"
    block = re.search(r"```(?:bash|sh)\n(.*?)```", sec.group(1), re.S)
    assert block, "「portable 安装」小节缺 bash 命令块"
    return block.group(1)


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


@pytest.fixture(scope="module")
def three(agate_scripts, bash, tmp_path_factory, synth):
    """构建 H1 / H2 / H3（各自独立 AGATE_HOME）。fixture 自身不断言（失败留给用例断言，保持红灯为断言失败）。"""
    base = tmp_path_factory.mktemp("three_paths")
    home = base / "home"
    home.mkdir()
    shim_dir = H.make_pip_shim(base / "bin")
    log = base / "pip.log"
    plat = H.host_platform_label()
    ns = SimpleNamespace(base=base, home=home, plat=plat, tag=H.MAIN_TAG, procs={}, log=log)
    pack_src = H.clone_bare(synth.bare, base / "pack-src.git")

    # H1：在线（agate-install.py latest，git 上游为本地 file://）
    ns.h1 = base / "H1"
    ns.procs["h1"] = H.run_tool(
        [sys.executable, agate_scripts / "agate-install.py", "latest"],
        env=H.tool_env(home, agate_home=ns.h1, extra={"AGATE_REPO_URL": synth.url}),
    )

    # H2：离线（真实 pack 的 git 步骤 + bundle 内入口的 install-offline；仅 pip 打桩）
    ns.h2 = base / "H2"
    if plat:
        out = base / "packs"
        env = H.tool_env(home, shim_dir=shim_dir, pip_log=log)
        ns.procs["pack"] = H.run_tool(
            [
                sys.executable,
                agate_scripts / "agate-pack-offline.py",
                H.MAIN_TAG,
                "--platform",
                plat,
                "--outdir",
                out,
                "--repo",
                pack_src,
            ],
            env=env,
        )
        ns.bundle = out / f"agate-{H.MAIN_TAG}-{plat}"
        ns.procs["h2"] = H.run_tool(
            [sys.executable, ns.bundle / "agate" / "scripts" / "install-offline.py", ns.bundle, "--dest-root", ns.h2], env=env
        )

    # H3：portable（本体 tarball + UPGRADING 文档所列命令逐条实跑，变量替换）
    ns.h3 = base / "H3"
    dist = base / "dist"
    ns.procs["build"] = H.run_tool(
        [
            sys.executable,
            agate_scripts / "agate-release.py",
            "build",
            "--tag",
            H.MAIN_TAG,
            "--repo",
            pack_src,
            "--outdir",
            dist,
            "--notes-out",
            base / "notes.md",
            "--skip-offline",
        ],
        env=H.tool_env(home, shim_dir=shim_dir, pip_log=log),
    )
    ns.dist = dist
    try:
        script = "set -euo pipefail\n" + _portable_block().replace("vX.Y.Z", H.MAIN_TAG)
    except AssertionError as exc:
        ns.procs["h3"] = None
        ns.h3_doc_error = str(exc)
    else:
        py3 = H.make_python3_wrapper(base / "py3bin")
        ns.h3_doc_error = None
        ns.procs["h3"] = H.run_tool([bash, "-c", script], env=H.tool_env(home, agate_home=ns.h3, shim_dir=py3), cwd=dist)
    return ns


def _need(ns, key):
    proc = ns.procs.get(key)
    assert proc is not None, f"{key} 未执行: {getattr(ns, 'h3_doc_error', None) or '前置条件缺失'}"
    assert proc.returncode == 0, f"{key} 应成功: rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"


def _resolve(ns, agate_home):
    """在隔离 AGATE_HOME 上跑根 scripts 的 agate-resolve.py（模拟真实使用后状态）。"""
    return H.run_tool(
        [sys.executable, agate_home / "scripts" / "agate-resolve.py"],
        env=H.tool_env(ns.home, agate_home=agate_home),
        cwd=ns.base,
    )


def _assert_conforming(ns, agate_scripts, synth, agate_home, label, expect_repo):
    """BDD-4 ①②③④ 的单路径断言（集合 / _protocol_root / 指针 + 根 scripts / resolve）。"""
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    common = H.load_project_module(agate_scripts, "agate_common.py", "agate_common")
    vdir = agate_home / ns.tag
    assert H.file_set(vdir) == synth.expected_package(ns.tag), f"{label}: 文件集合应 == F_pkg（不含 wheels / manifest.json / 维护者产物）"
    assert list(pkg.verify_dir(vdir)) == [], label
    assert os.path.realpath(common._protocol_root(str(vdir))) == os.path.realpath(str(vdir / "agate")), label
    assert os.readlink(agate_home / "latest") == ns.tag, label
    assert os.readlink(agate_home / "current") == "latest", label
    assert (agate_home / "scripts" / "agate-install.py").is_file(), f"{label}: 根 scripts/ 入口副本缺失"
    assert (agate_home / "repo").is_dir() is expect_repo, f"{label}: repo/ 仅在线安装存在"
    res = _resolve(ns, agate_home)
    assert res.returncode == 0, f"{label}: {res.stderr}"
    kv = _kv(res.stdout)
    assert kv["AGATE_VERSION"] == ns.tag, label
    assert os.path.realpath(kv["AGATE_ROOT"]) == os.path.realpath(str(vdir / "agate")), label


def test_bdd_4_h1_online_and_h2_offline_produce_same_structure(three, agate_scripts, synth):
    """BDD-4（H1 在线 vs H2 离线）：递归文件集合与内容逐一相等；两者各自满足契约；运行过 agate-resolve.py 之后再比较一次。"""
    _need(three, "h1")
    _need(three, "pack")
    _need(three, "h2")
    before1 = H.snapshot_tree(three.h1 / three.tag)
    before2 = H.snapshot_tree(three.h2 / three.tag)
    assert set(before1) == set(before2), f"仅 H1: {set(before1) - set(before2)}；仅 H2: {set(before2) - set(before1)}"
    assert before1 == before2
    _assert_conforming(three, agate_scripts, synth, three.h1, "H1", expect_repo=True)
    _assert_conforming(three, agate_scripts, synth, three.h2, "H2", expect_repo=False)
    assert H.snapshot_tree(three.h1 / three.tag) == H.snapshot_tree(three.h2 / three.tag), "使用后再比较（忽略字节码）仍须相等"


def test_bdd_4_all_three_paths_produce_same_structure_including_portable(three, agate_scripts, synth):
    """BDD-4 / T-4（H1 / H2 / H3）：portable 以 UPGRADING 文档命令解压 + --adopt；三处 vX.Y.Z/ 同构，H2 / H3 运行过
    agate-resolve.py 之后仍相等。波次末（批 F1a 之后）转绿。"""
    for key in ("h1", "pack", "h2", "build", "h3"):
        _need(three, key)
    snaps = {name: H.snapshot_tree(h / three.tag) for name, h in (("H1", three.h1), ("H2", three.h2), ("H3", three.h3))}
    assert snaps["H1"] == snaps["H2"] == snaps["H3"]
    _assert_conforming(three, agate_scripts, synth, three.h3, "H3", expect_repo=False)
    _assert_conforming(three, agate_scripts, synth, three.h2, "H2", expect_repo=False)
    again = {name: H.snapshot_tree(h / three.tag) for name, h in (("H1", three.h1), ("H2", three.h2), ("H3", three.h3))}
    assert again["H1"] == again["H2"] == again["H3"]


def test_bdd_4_online_install_matches_library_package_set(three, agate_scripts, synth):
    """BDD-4 ① / BDD-22：在线安装产物不含 wheels / manifest.json / 旧形态 `.git` 指针，且文件集合 == 库层 F_pkg。"""
    _need(three, "h1")
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    lib = {e.path for e in pkg.list_package(synth.bare, three.tag)}
    on_disk = H.file_set(three.h1 / three.tag)
    assert on_disk == lib
    assert not ({".git", "wheels", "manifest.json"} & {p.split("/")[0] for p in on_disk})


def test_t15_bundle_internal_entry_leaves_no_bytecode(three):
    """T-15 / eng B-1（本批部分）：以 bundle 内入口（真实内网机器的调用方式）执行 install-offline 成功（组件 checksum 通过），
    且执行前后 bundle/agate 与 vdir/agate 均无 __pycache__（否则 agate 组件哈希被 pyc 污染，误报被篡改）。"""
    _need(three, "pack")
    _need(three, "h2")
    for root in (three.bundle / "agate", three.h2 / three.tag / "agate"):
        assert [str(p) for p in root.rglob("__pycache__")] == [], f"{root} 出现 __pycache__"
        assert [str(p) for p in root.rglob("*.py[co]")] == [], f"{root} 出现字节码"
    assert not (three.h2 / three.tag / "agate" / "agate").exists()


def test_t15_pack_never_uses_worktree_metadata_in_bundle(three):
    """BDD-9 机理的反面：新 pack 产物的 bundle/agate 是本体目录（无 `.git` 指针、无整仓噪声）。"""
    _need(three, "pack")
    H.assert_real_bundle_layout(three.bundle)


def test_t15_real_tree_smoke_pack_install_resolve(agate_scripts, tmp_path):
    """T-15 第二部分「真实树冒烟」：把当前仓库 HEAD 以 `git clone --bare --local` 复制到 tmp、打临时 tag，走 pack →
    bundle 内 install-offline → agate-resolve.py，仅 pip 打桩——覆盖真实 agate/ 内容里未来出现的新顶层目录 / 新文件。
    注意：读取的是**已提交**的 HEAD（未提交的改动不在其中）。"""
    plat = H.host_platform_label()
    if plat is None:
        pytest.skip("本机平台无对应 offline 平台标签")
    real = H.clone_bare(H.REPO_ROOT, tmp_path / "real.git", hardlinks=True)
    tag = "v9.9.9"
    H.run_git(real, "tag", tag, "HEAD")
    shim_dir = H.make_pip_shim(tmp_path / "bin")
    home = tmp_path / "home"
    home.mkdir()
    env = H.tool_env(home, shim_dir=shim_dir, pip_log=tmp_path / "pip.log")
    out = tmp_path / "packs"
    pack = H.run_tool(
        [sys.executable, agate_scripts / "agate-pack-offline.py", tag, "--platform", plat, "--outdir", out, "--repo", real], env=env
    )
    assert pack.returncode == 0, pack.stderr
    bundle = out / f"agate-{tag}-{plat}"
    dest = tmp_path / "agate-home"
    inst = H.run_tool(
        [sys.executable, bundle / "agate" / "scripts" / "install-offline.py", bundle, "--dest-root", dest], env=env
    )
    assert inst.returncode == 0, inst.stderr
    vdir = dest / tag
    expected = {p for p, _s in H.ls_tree_sizes(real, tag) if H.oracle_in_package(p)}
    assert H.file_set(vdir) == expected
    assert not any(p.startswith("agate/tests/") for p in H.file_set(vdir))
    res = H.run_tool(
        [sys.executable, dest / "scripts" / "agate-resolve.py"], env=H.tool_env(home, agate_home=dest), cwd=tmp_path
    )
    assert res.returncode == 0, res.stderr
    kv = _kv(res.stdout)
    assert kv["AGATE_VERSION"] == tag
    assert os.path.realpath(kv["AGATE_ROOT"]) == os.path.realpath(str(vdir / "agate"))
