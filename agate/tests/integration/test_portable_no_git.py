# tests/integration/test_portable_no_git.py — TAG0037 P3 组 C：portable 安装不依赖 git，解压即用（BDD-17，P2 T-5）
#
# BDD-17：PATH 目录 P 仅含 python3（含 pyyaml）与必要 coreutils（含 sha256sum / tar / gzip）的链接，`git` 在该 PATH 下**不存在**；
# 本体 tarball（agate-release.py build 的产物）→ 按 UPGRADING「portable 安装」小节**所列命令逐条实跑**（变量替换；不得另写测试专用命令，
# 文档即验收脚本）→ 全程 exit 0 且无 git 调用；agate-resolve.py exit 0 且 AGATE_VERSION=vX.Y.Z；agate-summary.py exit 0（无 CHANGELOG 探测崩溃）；
# `agate-install.py --check --portable` exit 0（口径细节 BDD-18 归 B 组 test_agate_install_adopt.py）。
# 与 A 组 integration/test_install_three_paths.py 的 H3 互补：H3 走带 git 的 PATH 验证三路径同构；本文件走**无 git 的 PATH** 验证依赖声明。
# 依赖（允许暂时红灯）：agate_package.py / agate-release.py（批 A / C1）、--adopt / --check --portable（批 B1b）、UPGRADING portable 小节（批 F1a）
# ——只能在波次末（文档批之后）转绿。红灯原因：agate-release.py 尚不存在 → build 失败，断言处报错（B 类）。
# 隔离：全部在 tmp_path 下（AGATE_HOME / HOME / 合成上游）；不触碰真实 ~/.agate / 开发 checkout / origin；不联网（--skip-offline，无 pip）。
# 平台：POSIX 专用（符号链接 PATH 目录 + bash 文档命令）；Windows CI 只跑 windows_smoke，本文件不带该标记。

import os
import re
import shutil
import sys
from types import SimpleNamespace

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(not H.posix_shim_supported(), reason="无 git PATH 用例仅 POSIX（符号链接 + bash）")

# portable 文档命令与 python 子进程需要的工具（存在才链；刻意不含 git）。含 bash：`--check` 把 bash 列为必备项（仅装 hook 需要，
# 与 SETUP 环境探测一致），BDD-17 要验证的变量是"无 git"，不是"无 bash"。
_TOOLS = (
    "bash", "sha256sum", "shasum", "tar", "gzip", "mkdir", "ln", "cat", "rm", "cp", "mv", "ls", "dirname", "basename", "readlink",
    "env", "sh", "sort", "uname", "head", "tail", "tr", "sed", "grep", "chmod", "find", "date", "id", "wc", "touch", "true",
    "false", "test", "realpath", "sleep", "printf", "echo", "pwd", "cut", "awk", "diff", "xargs", "tee",
)


def _kv(stdout):
    out = {}
    for line in stdout.splitlines():
        k, sep, v = line.partition("=")
        if sep:
            out[k] = v
    return out


def _portable_block():
    text = (H.REPO_ROOT / "agate" / "UPGRADING.md").read_text(encoding="utf-8")
    sec = re.search(r"^#{2,4}[^\n]*portable 安装[^\n]*\n(.*?)(?=^#{2,4} |\Z)", text, re.S | re.M)
    assert sec, "UPGRADING.md 缺「portable 安装」小节（批 F1a 待实现）"
    block = re.search(r"```(?:bash|sh)\n(.*?)```", sec.group(1), re.S | re.M)
    assert block, "「portable 安装」小节缺 bash 命令块"
    return block.group(1)


def _make_no_git_path(dest):
    """建仅含 python3 包装 + coreutils 链接的 PATH 目录（不含 git）。"""
    dest.mkdir(parents=True, exist_ok=True)
    H.make_python3_wrapper(dest)
    for name in _TOOLS:
        if name == "git":
            continue
        real = shutil.which(name)
        target = dest / name
        if real and not target.exists():
            os.symlink(real, str(target))
    return dest


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


@pytest.fixture(scope="module")
def portable(agate_scripts, bash, tmp_path_factory, synth):
    """构建本体 tarball（带 git 的正常环境）→ 在无 git 的 PATH 下逐条执行文档命令。fixture 自身不断言。"""
    base = tmp_path_factory.mktemp("portable_no_git")
    home = base / "home"
    home.mkdir()
    ns = SimpleNamespace(base=base, home=home, tag=H.MAIN_TAG, agate_home=base / "AGATE_HOME", procs={}, doc_error=None)
    src = H.clone_bare(synth.bare, base / "src.git")
    dist = base / "dist"
    ns.dist = dist
    ns.procs["build"] = H.run_tool(
        [sys.executable, agate_scripts / "agate-release.py", "build", "--tag", ns.tag, "--repo", src,
         "--outdir", dist, "--notes-out", base / "notes.md", "--skip-offline"],
        env=H.tool_env(home),
    )
    ns.path_dir = _make_no_git_path(base / "nogit-bin")
    ns.env = H.tool_env(home, agate_home=ns.agate_home, extra={"PATH": str(ns.path_dir)})
    try:
        script = "set -euo pipefail\n" + _portable_block().replace("vX.Y.Z", ns.tag)
    except AssertionError as exc:
        ns.doc_error = str(exc)
        ns.procs["doc"] = None
    else:
        # bash 用绝对路径：子进程 env 的 PATH 已被替换为无 git 的受限目录，裸 "bash" 不可解析
        ns.procs["doc"] = H.run_tool([shutil.which(bash) or bash, "-c", script], env=ns.env, cwd=dist)
    return ns


def _need(ns, key):
    proc = ns.procs.get(key)
    assert proc is not None, f"{key} 未执行: {ns.doc_error or '前置条件缺失'}"
    assert proc.returncode == 0, f"{key} 应成功: rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"


def test_bdd_17_test_path_really_has_no_git(portable):
    """BDD-17 前提（T-5）：受限 PATH 下 git 不可见，而 python3 可见（否则后续"无 git"结论不成立）。"""
    assert shutil.which("git", path=str(portable.path_dir)) is None
    assert shutil.which("python3", path=str(portable.path_dir)) is not None
    assert shutil.which("sha256sum", path=str(portable.path_dir)) is not None, "测试 PATH 须含 sha256sum（文档命令依赖）"


def test_bdd_17_documented_commands_run_without_git_and_produce_contract_layout(portable, synth):
    """BDD-17：按 UPGRADING portable 小节命令（变量替换后逐条实跑）在无 git 的 PATH 下全程 exit 0；结果满足契约（文件集合 == F_pkg，
    latest / current 指针在位，根 scripts/ 就位）。"""
    _need(portable, "build")
    _need(portable, "doc")
    vdir = portable.agate_home / portable.tag
    assert H.file_set(vdir) == synth.expected_package(portable.tag)
    assert os.readlink(portable.agate_home / "latest") == portable.tag
    assert os.readlink(portable.agate_home / "current") == "latest"
    assert (portable.agate_home / "scripts" / "agate-install.py").is_file()


def test_bdd_17_resolve_and_summary_work_without_git(portable):
    """BDD-17：无 git 的 PATH 下 agate-resolve.py exit 0 且 AGATE_VERSION=vX.Y.Z；agate-summary.py exit 0（无 CHANGELOG 探测崩溃）。"""
    _need(portable, "build")
    _need(portable, "doc")
    project = portable.base / "project"
    project.mkdir(exist_ok=True)
    scripts = portable.agate_home / "scripts"
    res = H.run_tool([sys.executable, scripts / "agate-resolve.py"], env=portable.env, cwd=project)
    assert res.returncode == 0, res.stderr
    kv = _kv(res.stdout)
    assert kv.get("AGATE_VERSION") == portable.tag
    assert kv.get("AGATE_ROOT", "").replace(os.sep, "/").endswith(f"{portable.tag}/agate")
    summ = H.run_tool([sys.executable, scripts / "agate-summary.py"], env=portable.env, cwd=project)
    assert summ.returncode == 0, summ.stderr
    assert "Traceback" not in summ.stderr and f"版本：{portable.tag}" in summ.stdout, summ.stdout + summ.stderr


def test_bdd_17_check_portable_passes_without_git(portable):
    """BDD-17：portable 口径 `agate-install.py --check --portable` 在无 git 的 PATH 下 exit 0（BDD-18 ① 的端到端证据；口径细节归 B 组）。"""
    _need(portable, "build")
    _need(portable, "doc")
    res = H.run_tool(
        [sys.executable, "-B", portable.agate_home / "scripts" / "agate-install.py", "--check", "--portable"],
        env=portable.env,
        cwd=portable.base,
    )
    assert res.returncode == 0, f"stdout={res.stdout}\nstderr={res.stderr}"
    assert "Traceback" not in res.stderr
