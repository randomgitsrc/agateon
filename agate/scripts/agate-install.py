#!/usr/bin/env python3
"""agate-install.py — 安装 / 卸载 agate 版本 + 环境探测（TAG0008 批次 install）

版本管理根布局（P2-design.md §2.1 候选方案 A）：
  ~/.agate/
  ├── repo/          # 唯一主仓库（首次 clone，之后只 worktree add tag）
  ├── v0.43.0/       # worktree 检出 tag
  ├── v0.48.0/
  ├── latest         # 纯指针 → v0.48.0（POSIX 软链 / Windows 复制模式文本指针）
  └── current        # 默认指针 → latest

用法：
  python3 agate-install.py                       # 无参 = 装 latest 指针（最新发布 tag 的 worktree）+ current → latest
  python3 agate-install.py v0.48.0               # 装指定版本（幂等：版本目录已存在即跳过，BDD-3）
  python3 agate-install.py --uninstall v0.43.0   # 卸载：引用保护扫描 + worktree remove + 指针清理（BDD-5/6）
  python3 agate-install.py --check               # 环境探测 python3/pyyaml/git/bash，全齐 exit 0（BDD-7/8）

AGATE_REPO_URL 环境变量 = 版本源仓库（测试隔离用，指向本地临时 repo）；未设置时用默认
上游仓库。HOME 环境变量重定向 ~（测试隔离防触碰真实 ~/.agate）。

契约：Python 3.8+（无 match / str.removeprefix）；文本读写显式 encoding="utf-8"；
失败路径 stderr + exit 非 0（--check 缺项非 0 + 分平台修复指引）。
"""

import contextlib
import os
import re
import shutil
import subprocess
import sys
import time

try:
    from agate_common import _protocol_root, probe_python, run_git
except (ImportError, SystemExit):
    # 公共库依赖（pyyaml）缺失时降级本地实现——--check 仍需能输出分平台修复指引。
    def _protocol_root(vdir):
        """agate_common._protocol_root 的降级副本（探测序 vdir/scripts 先、vdir/agate/scripts 后）。"""
        if os.path.isdir(os.path.join(vdir, "scripts")):
            return vdir
        sub = os.path.join(vdir, "agate")
        if os.path.isdir(os.path.join(sub, "scripts")):
            return sub
        return vdir

    def probe_python():
        for name in ("python3", "python"):
            path = shutil.which(name)
            if path:
                return path
        return None

    def run_git(args, cwd=None):
        try:
            proc = subprocess.run(
                ["git", *args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=cwd,
            )
            return proc.returncode, proc.stdout
        except OSError:
            return 1, ""


DEFAULT_REPO_URL = "https://github.com/randomgitsrc/agateon"
AGATE_DIRNAME = ".agate"
_VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
_DECL_RE = re.compile(r"^\s*agate\s*:\s*(v[0-9]+\.[0-9]+\.[0-9]+)\s*$")

# 卸载引用保护扫描的限流参数（P2 §4.5「限 ~ 深度，mtime 合理限流」）。
_SCAN_SKIP_DIRS = {".agate", ".git", ".hg", ".svn", "__pycache__", "node_modules"}
_SCAN_MAX_DEPTH = 4
_SCAN_MTIME_WINDOW = 365 * 24 * 3600


def _agate_home():
    return os.path.join(os.path.expanduser("~"), AGATE_DIRNAME)


def _version_key(version):
    return tuple(int(x) for x in version[1:].split("."))


def _write_pointer(agate_home, name, target_name):
    """写 latest/current 纯指针：POSIX 软链、Windows(nt) 复制模式文本指针。"""
    path = os.path.join(agate_home, name)
    if os.path.lexists(path):
        with contextlib.suppress(OSError):
            os.unlink(path)
    if os.name == "nt":
        with open(path, "w", encoding="utf-8") as f:
            f.write(target_name + "\n")
        return
    try:
        os.symlink(target_name, path)
    except OSError:
        with open(path, "w", encoding="utf-8") as f:
            f.write(target_name + "\n")


def _remove_pointer(agate_home, name):
    path = os.path.join(agate_home, name)
    if os.path.lexists(path):
        with contextlib.suppress(OSError):
            os.unlink(path)


def _resolve_pointer(agate_home, name):
    """指针链解析 → 最终版本目录路径（软链 / 文本指针，防环）；无法解析返回 None。

    先判 `os.path.islink` 再判 `os.path.isdir`：POSIX 软链指针（latest→v0.48.0 等）
    指向版本目录时 `os.path.isdir(p)` 恒为 True，若先判 isdir 会把软链路径自身当终态
    （返回 "~/.agate/latest" 而非版本目录），导致卸载指针修复分支永不触发（BDD-5 红线）。
    """
    seen = set()
    node = name
    for _ in range(8):
        p = os.path.join(agate_home, node)
        if os.path.islink(p):
            target = os.readlink(p)
            node = os.path.normpath(target if os.path.isabs(target) else os.path.join(agate_home, target))
            continue
        if os.path.isdir(p):
            return p
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    content = f.read().replace("\r", "").strip()
            except OSError:
                content = ""
            if content and content != node and content not in seen:
                seen.add(node)
                node = content
                continue
        return None
    return None


def _ensure_repo(agate_home, url):
    """repo 单克隆（首次）：已有 repo 直接复用；clone 失败 fail-closed exit 1。"""
    repo = os.path.join(agate_home, "repo")
    if os.path.isdir(os.path.join(repo, ".git")):
        # 已有 repo：拉取上游新 tag/commit，令重跑 latest 能跟随更高版本（BDD-4 判据 2）。
        # 离线/失败非致命——保留既有本地 tag 继续（fail-open on fetch）。
        run_git(["fetch", "--tags", "--force", "--prune", "origin"], cwd=repo)
        return repo
    os.makedirs(agate_home, exist_ok=True)
    try:
        proc = subprocess.run(
            ["git", "clone", url, repo], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError:
        sys.stderr.write("错误: git 不可用（可先运行 --check 查看环境修复指引）\n")
        sys.exit(1)
    if proc.returncode != 0 or not os.path.isdir(os.path.join(repo, ".git")):
        err = proc.stderr.strip() or proc.stdout.strip()
        sys.stderr.write(f"错误: git clone 失败（{url}）：{err}\n")
        sys.exit(1)
    return repo


def _latest_tag(repo):
    """版本源仓库里最新发布 tag（按版本号降序，过滤 vX.Y.Z）。"""
    rc, out = run_git(["tag", "--sort=-version:refname"], cwd=repo)
    if rc != 0:
        return None
    for line in out.splitlines():
        tag = line.strip()
        if _VERSION_RE.match(tag):
            return tag
    return None


def _worktree_add(repo, version_dir, tag):
    try:
        proc = subprocess.run(
            ["git", "-C", repo, "worktree", "add", "--detach", version_dir, tag],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        sys.stderr.write("错误: git 不可用（可先运行 --check 查看环境修复指引）\n")
        sys.exit(1)
    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip()
        sys.stderr.write(f"错误: git worktree add {version_dir} {tag} 失败：{err}\n")
        sys.exit(1)


def _install_version(agate_home, repo, version):
    """装指定版本。幂等（BDD-3）：程序先判版本目录/指针存在，存在即跳过，不依赖 git 报错。"""
    version_dir = os.path.join(agate_home, version)
    if os.path.lexists(version_dir):
        print(f"{version} 已安装，跳过（幂等）")
        return
    _worktree_add(repo, version_dir, version)


def _newest_installed_version(agate_home):
    """~/.agate 下已安装版本目录中最新者（按版本号）；无则 None。"""
    candidates = []
    try:
        entries = os.listdir(agate_home)
    except OSError:
        return None
    for entry in entries:
        if _VERSION_RE.match(entry) and os.path.isdir(os.path.join(agate_home, entry)):
            candidates.append(entry)
    if not candidates:
        return None
    candidates.sort(key=_version_key, reverse=True)
    return candidates[0]


def _pointer_targets(agate_home):
    """卸载前捕获 latest/current 指针解析到的版本名（目录还在，能解析出最终目标）。"""
    out = {}
    for name in ("latest", "current"):
        target = _resolve_pointer(agate_home, name)
        out[name] = os.path.basename(target) if target else None
    return out


def _repair_pointers(agate_home, removed_version, before):
    """卸载后指针清理/重指（BDD-5）：latest/current 曾指向被删版本 → 重指最新有效版本或清除（不留悬空）。"""
    for name in ("latest", "current"):
        if before.get(name) != removed_version:
            continue
        if name == "latest":
            valid = _newest_installed_version(agate_home)
            if valid:
                _write_pointer(agate_home, "latest", valid)
            else:
                _remove_pointer(agate_home, "latest")
        else:
            latest_after = _resolve_pointer(agate_home, "latest")
            if latest_after:
                _write_pointer(agate_home, "current", "latest")
            else:
                _remove_pointer(agate_home, "current")


def _find_references(home, version):
    """扫描 $HOME 下 .agate-version 声明指定版本的项目 → (refs, hit_limit) 二元组
    （TAG0031 DEBT0004，BDD-4/5）。

    限深度 + 跳过隐藏/.agate/.git 等目录 + mtime 窗口限流（P2 §4.5），避免整树无界扫描。
    `hit_limit` 标记本次扫描是否命中深度剪枝或 mtime 超窗跳过——命中即可能存在漏扫的
    引用，调用方（`_cmd_uninstall`）据此输出 WARNING，不把"扫不到"误判为"确实无引用"。
    """
    refs = []
    hit_limit = False
    home_abs = os.path.abspath(home)
    for root, dirs, files in os.walk(home_abs):
        rel = os.path.relpath(root, home_abs)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > _SCAN_MAX_DEPTH:
            dirs[:] = []
            hit_limit = True
            continue
        dirs[:] = [d for d in dirs if d not in _SCAN_SKIP_DIRS and not d.startswith(".")]
        if ".agate-version" not in files:
            continue
        vf = os.path.join(root, ".agate-version")
        try:
            if time.time() - os.path.getmtime(vf) > _SCAN_MTIME_WINDOW:
                hit_limit = True
                continue
        except OSError:
            continue
        try:
            with open(vf, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        m = _DECL_RE.match(content)
        if m and m.group(1) == version:
            refs.append(root)
    return refs, hit_limit


_LEGACY_SYMLINK_MSG = (
    "错误: ~/.agate 是 legacy 软链布局，agate-install 会穿透软链把 repo/ 与 vX.Y.Z/ "
    "静默建进源仓库，已拒绝（fail-closed）。\n"
    "迁移到版本管理布局（三步）：\n"
    "  1. 备份软链:  mv ~/.agate ~/.agate.bak\n"
    "  2. 建目录根:  mkdir -p ~/.agate\n"
    "  3. 装版本:    install.sh --versions\n"
    "               # 迁移完成后亦可: python3 ~/.agate/scripts/agate-install.py latest\n"
)


def _sync_root_scripts(agate_home, version_dir):
    """建立/刷新根 ~/.agate/scripts/ 入口副本（TAG0032 决策 B1，单源 copytree，副本非软链）。

    源 = 刚装版本的协议 scripts/（_protocol_root 探测：version_dir 或 version_dir/agate）。
    真实元仓库每个 tag 的 agate/scripts/ 本就含全套版本工具（agate-install.py /
    agate_common.py / resolve-entry.py 等，P1-requirements §3.4）——单次 copytree
    （dirs_exist_ok=True）即可让新机 ~/.agate/scripts/ 入口命令可直接调用（断点一
    「入口断链」修复），并随重跑 agate-install.py latest 跟随 current 版本刷新
    （BDD-4 判据 2）。

    copytree 失败不静默吞掉（DEBT0-B）：写一行 stderr 诊断，便于用户定位根入口缺失，
    而非事后在「No such file」处才发现。
    """
    dst = os.path.join(agate_home, "scripts")
    proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")
    if not os.path.isdir(proto_scripts):
        sys.stderr.write(
            f"WARNING: 版本协议 scripts/ 不存在（{proto_scripts}），"
            f"根 {dst} 入口副本未刷新——可重跑 agate-install.py latest\n"
        )
        return
    try:
        shutil.copytree(proto_scripts, dst, dirs_exist_ok=True)
    except OSError as exc:
        sys.stderr.write(
            f"WARNING: 根入口副本同步失败（{proto_scripts} → {dst}）：{exc}；"
            f"~/.agate/scripts/ 可能缺版本工具，可重跑 agate-install.py latest\n"
        )


def _cmd_install(agate_home, version=None):
    if os.path.islink(agate_home):
        sys.stderr.write(_LEGACY_SYMLINK_MSG)
        sys.exit(1)
    url = os.environ.get("AGATE_REPO_URL", "") or DEFAULT_REPO_URL
    repo = _ensure_repo(agate_home, url)
    if version is None:
        tag = _latest_tag(repo)
        if tag is None:
            sys.stderr.write("错误: 版本源仓库没有可用的 vX.Y.Z tag\n")
            sys.exit(1)
        _install_version(agate_home, repo, tag)
        _write_pointer(agate_home, "latest", tag)
        _write_pointer(agate_home, "current", "latest")
        _sync_root_scripts(agate_home, os.path.join(agate_home, tag))
        print(f"已安装 latest → {tag}")
    else:
        if not _VERSION_RE.match(version):
            sys.stderr.write(f"错误: 非法版本号 {version!r}（应为 vX.Y.Z）\n")
            sys.exit(2)
        _install_version(agate_home, repo, version)
        _sync_root_scripts(agate_home, os.path.join(agate_home, version))
        print(f"已安装 {version}")
    sys.exit(0)


def _cmd_uninstall(agate_home, version):
    if not _VERSION_RE.match(version):
        sys.stderr.write(f"错误: 非法版本号 {version!r}（应为 vX.Y.Z）\n")
        sys.exit(2)

    refs, hit_limit = _find_references(os.path.expanduser("~"), version)
    if hit_limit:
        sys.stderr.write(
            "WARNING: 引用扫描命中深度/时间窗口限流边界（超出可能未被完整扫描），"
            "卸载判定可能未覆盖全部引用该版本的项目\n"
        )
    if refs:
        sys.stderr.write(f"拒绝卸载: {version} 仍被 {len(refs)} 个项目引用（.agate-version）：\n")
        for r in refs:
            sys.stderr.write(f"  - {r}\n")
        sys.stderr.write("先移除这些项目的 .agate-version 声明再重试。\n")
        sys.exit(1)

    version_dir = os.path.join(agate_home, version)
    if not os.path.lexists(version_dir):
        print(f"{version} 未安装，无需卸载")
        sys.exit(0)

    before = _pointer_targets(agate_home)
    repo = os.path.join(agate_home, "repo")

    rc, _out = run_git(["worktree", "remove", version_dir], cwd=repo)
    if rc != 0:
        run_git(["worktree", "remove", "--force", version_dir], cwd=repo)
    if os.path.lexists(version_dir):
        shutil.rmtree(version_dir, ignore_errors=True)
    if os.path.lexists(version_dir):
        sys.stderr.write(f"错误: 无法删除版本目录 {version_dir}\n")
        sys.exit(1)
    run_git(["worktree", "prune"], cwd=repo)

    _repair_pointers(agate_home, version, before)
    print(f"已卸载 {version}")
    sys.exit(0)


def _fix_guidance(item):
    """分平台修复指引（BDD-8，I-13）：Linux pip / Windows Python/PATH/PYTHONUTF8/Git for Windows。"""
    win = sys.platform == "win32"
    if item == "python3":
        if win:
            return ["从 python.org 下载安装 Python，安装时勾选 'Add Python to PATH'，重开终端后重试"]
        return ["安装 python3（如: sudo apt install python3 / brew install python3）"]
    if item == "pyyaml":
        if win:
            return ["运行: python -m pip install pyyaml；若遇到编码/UTF-8 问题可设置环境变量 PYTHONUTF8=1"]
        return ["运行: pip install pyyaml（或 python3 -m pip install pyyaml）"]
    if item == "git":
        if win:
            return ["安装 Git for Windows（https://git-scm.com/download/win）"]
        return ["安装 git（如: sudo apt install git / brew install git）"]
    if item == "bash":
        if win:
            return ["安装 Git for Windows（自带 Git Bash: Git\\bin\\bash.exe）"]
        return ["bash 通常随系统自带（如: sudo apt install bash）"]
    return []


def _cmd_check():
    """环境探测：python3 / pyyaml / git / bash。全齐 exit 0；缺项非 0 + 分平台修复指引。"""
    missing = []
    items = []

    python_path = probe_python()
    items.append(f"python3: {python_path if python_path else '缺失'}")
    if not python_path:
        missing.append("python3")

    yaml_ok = False
    if python_path:
        try:
            proc = subprocess.run(
                [python_path, "-c", "import yaml"], capture_output=True,
                text=True, encoding="utf-8",
            )
            yaml_ok = proc.returncode == 0
        except OSError:
            yaml_ok = False
    items.append(f"pyyaml: {'可用' if yaml_ok else '缺失'}")
    if not yaml_ok:
        missing.append("pyyaml")

    git_path = shutil.which("git")
    items.append(f"git: {git_path if git_path else '缺失'}")
    if not git_path:
        missing.append("git")

    bash_path = shutil.which("bash")
    items.append(f"bash: {bash_path if bash_path else '缺失'}")
    if not bash_path:
        missing.append("bash")

    for line in items:
        print("✓ " + line)

    if not missing:
        print("环境完整（python3 / pyyaml / git / bash 全部可用）")
        sys.exit(0)

    print("\n缺少: " + ", ".join(missing))
    print("修复指引:")
    for item in missing:
        for line in _fix_guidance(item):
            print("  " + line)
    sys.exit(1)


def _usage():
    print("用法: agate-install.py [latest | vX.Y.Z | --uninstall vX.Y.Z | --check]")
    print("  无参 / latest    装 latest 指针（最新发布 tag 的 worktree）+ current → latest")
    print("  vX.Y.Z           装指定版本（幂等，已装则跳过）")
    print("  --uninstall vX   卸载指定版本（引用保护扫描 + worktree remove + 指针清理）")
    print("  --check          环境探测 python3 / pyyaml / git / bash")


def main():
    args = sys.argv[1:]
    agate_home = _agate_home()

    if not args or (len(args) == 1 and args[0] == "latest"):
        # `latest` = 无参安装的显式别名（装最新发布 tag + current→latest；幂等复跑）。
        _cmd_install(agate_home)
    elif args[0] == "--check":
        _cmd_check()
    elif args[0] == "--uninstall":
        if len(args) != 2:
            sys.stderr.write("用法: agate-install.py --uninstall vX.Y.Z\n")
            sys.exit(2)
        _cmd_uninstall(agate_home, args[1])
    elif args[0] in ("--help", "-h"):
        _usage()
        sys.exit(0)
    elif len(args) == 1:
        _cmd_install(agate_home, args[0])
    else:
        sys.stderr.write("用法: agate-install.py [vX.Y.Z | --uninstall vX.Y.Z | --check]\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
