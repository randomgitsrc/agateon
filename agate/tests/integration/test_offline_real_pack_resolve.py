# tests/integration/test_offline_real_pack_resolve.py — TAG0037 P3 组 C：用真实 pack 产物结构离线安装后解析成功（BDD-9，P0 BUG 修复的直接判据）
#
# BDD-9：合成 tag 仓库（整仓树，含 agate/ 与噪声顶层目录）；agate-pack-offline.py 的 **git 步骤真实执行**（禁止"mock subprocess.run 凭空造
# bundle/agate/WORKFLOW.md"式假 bundle；唯一可 stub 的是 pip：PATH 内 pip shim，wheel 为本地占位文件）→ 以 **bundle 内入口**执行 install-offline.py
# （真实内网机器的调用方式，P2 T-15）→ `AGATE_HOME=<dest> agate-resolve.py`：
#   exit 0，AGATE_ROOT == <dest>/vX.Y.Z/agate 且 <AGATE_ROOT>/scripts/agate-resolve.py 存在；不存在 <dest>/vX.Y.Z/agate/agate/ 双层嵌套；
#   `_protocol_root(<dest>/vX.Y.Z)` 不再"原样返回 vdir"（P0 机理：原样返回 = 解析失效）。
# 与 A 组 integration/test_install_three_paths.py（H2 的同构断言）互补：本文件是 BDD-9 的**直接、独立**用例（用例名 / docstring 可追溯到 BDD-9）。
# BDD-11 的红灯回放 / sentinel 与 BDD-12 的旧格式拒绝归 B 组。
# 当前（P4 前）红灯原因：旧 pack 用 worktree 检出整仓 → 安装后 vX.Y.Z/agate/agate/scripts 双层嵌套 → 解析失效（断言失败，B 类）。
# 隔离：全部在 tmp_path 下（合成上游 / AGATE_HOME / HOME）；不触碰真实 ~/.agate / 开发 checkout / origin；无网络。
# 平台：POSIX 专用（pip shim）；host 平台无对应 offline 标签（非 x86_64）时 skip（平台限制，非缺 CLI）。

import os
import sys
from types import SimpleNamespace

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(not H.posix_shim_supported(), reason="离线真实 pack 用例仅 POSIX（pip shim）")


def _kv(stdout):
    out = {}
    for line in stdout.splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k] = v
    return out


@pytest.fixture(scope="module")
def offline(agate_scripts, tmp_path_factory):
    """真实 pack → bundle 内入口 install-offline → resolve。fixture 自身不断言（失败留给用例断言处）。"""
    plat = H.host_platform_label()
    if plat is None:
        pytest.skip("host 平台无对应 offline 标签（仅支持 linux-x86_64 / windows-x86_64）")
    synth = H.get_shared_synthetic_repo(tmp_path_factory)
    base = tmp_path_factory.mktemp("offline_real_pack")
    home = base / "home"
    home.mkdir()
    project = base / "project"
    project.mkdir()
    dest = base / "AGATE_HOME"
    shim = H.make_pip_shim(base / "bin")
    env = H.tool_env(home, shim_dir=shim, pip_log=base / "pip.log")
    src = H.clone_bare(synth.bare, base / "pack-src.git")
    ns = SimpleNamespace(base=base, home=home, dest=dest, tag=H.MAIN_TAG, procs={})
    ns.procs["pack"] = H.run_tool(
        [sys.executable, agate_scripts / "agate-pack-offline.py", ns.tag, "--platform", plat, "--outdir", base / "packs", "--repo", src],
        env=env,
    )
    ns.bundle = base / "packs" / f"agate-{ns.tag}-{plat}"
    ns.procs["install"] = H.run_tool(
        [sys.executable, ns.bundle / "agate" / "scripts" / "install-offline.py", ns.bundle, "--dest-root", dest], env=env
    )
    ns.procs["resolve"] = H.run_tool(
        [sys.executable, agate_scripts / "agate-resolve.py"], env=H.tool_env(home, agate_home=dest), cwd=project
    )
    return ns


def _ok(ns, key):
    proc = ns.procs[key]
    assert proc.returncode == 0, f"{key} 应成功: rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"


def test_bdd_9_real_pack_then_offline_install_resolves(offline):
    """BDD-9：真实 pack 产物离线安装后 agate-resolve.py exit 0，AGATE_ROOT == <dest>/vX.Y.Z/agate，其下 scripts/agate-resolve.py 存在。"""
    _ok(offline, "pack")
    _ok(offline, "install")
    _ok(offline, "resolve")
    kv = _kv(offline.procs["resolve"].stdout)
    root = kv.get("AGATE_ROOT", "")
    assert os.path.realpath(root) == os.path.realpath(str(offline.dest / offline.tag / "agate")), kv
    assert (offline.dest / offline.tag / "agate" / "scripts" / "agate-resolve.py").is_file()
    assert kv.get("AGATE_VERSION") == offline.tag


def test_bdd_9_no_double_nesting_and_protocol_root_not_returned_verbatim(offline, agate_scripts):
    """BDD-9：安装后不存在 <dest>/vX.Y.Z/agate/agate/ 双层嵌套；_protocol_root(<dest>/vX.Y.Z) 不再原样返回 vdir（解析失效的机理）。"""
    _ok(offline, "pack")
    _ok(offline, "install")
    vdir = offline.dest / offline.tag
    assert not (vdir / "agate" / "agate").exists(), "出现 vX.Y.Z/agate/agate/ 双层嵌套（P0 BUG）"
    common = H.load_project_module(agate_scripts, "agate_common.py", "agate_common")
    got = common._protocol_root(str(vdir))
    assert os.path.realpath(got) != os.path.realpath(str(vdir)), "_protocol_root 原样返回 vdir = 解析失效"
    assert os.path.realpath(got) == os.path.realpath(str(vdir / "agate"))
