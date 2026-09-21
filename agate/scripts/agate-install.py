#!/usr/bin/env python3
"""agate-install.py — 安装 / 卸载 agate 版本 + 环境探测（TAG0008 批次 install）

版本管理根布局（TAG0037：在线安装只装本体，版本目录不再是 git worktree）：
  ~/.agate/
  ├── repo/          # 在线安装才有：唯一主仓库（git 对象库，装任意历史 tag 用）
  ├── v0.43.0/       # 本体：agate/ + CHANGELOG.md LICENSE NOTICES.md（由 agate_package 从 tag 构建）
  ├── v0.48.0/
  ├── latest         # 纯指针 → v0.48.0（POSIX 软链 / Windows 复制模式文本指针）
  └── current        # 默认指针 → latest

用法：
  python3 agate-install.py                       # 无参 = 装 latest 指针（最新发布 tag 的本体）+ current → latest
  python3 agate-install.py v0.48.0               # 装指定版本（幂等：版本目录已存在即跳过，BDD-3）
  python3 agate-install.py --uninstall v0.43.0   # 卸载：引用保护扫描 + 移除版本目录 + 指针清理（BDD-5/6）
  python3 agate-install.py --adopt v0.48.0       # 纳管已就位的版本目录：写 latest/current 指针 + 同步根 scripts/，不碰 git（BDD-17）
  python3 agate-install.py --check               # 环境探测 python3/pyyaml/git/bash，全齐 exit 0（BDD-7/8）
  python3 agate-install.py --check --portable    # opt-in：必需项仅 python3 + pyyaml，git/bash 缺失只提示（BDD-18）

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

# 安装器自身不产生字节码（TAG0037 D-13）：须先于 import agate_common / agate_package。
sys.dont_write_bytecode = True

import agate_package  # noqa: E402  stdlib-only，与 agate_common 不同不依赖 pyyaml

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
_VERSION_RE = agate_package.VERSION_RE  # 一律 fullmatch（拒结尾换行 / 两段 / 路径穿越 / 预发布后缀）
_DECL_RE = re.compile(r"^\s*agate\s*:\s*(v[0-9]+\.[0-9]+\.[0-9]+)\s*$")

# 卸载引用保护扫描的限流参数（P2 §4.5「限 ~ 深度，mtime 合理限流」）。
_SCAN_SKIP_DIRS = {".agate", ".git", ".hg", ".svn", "__pycache__", "node_modules"}
_SCAN_MAX_DEPTH = 4
_SCAN_MTIME_WINDOW = 365 * 24 * 3600


def _agate_home():
    """版本根目录：`AGATE_HOME` env 覆盖优先，否则 `~/.agate`（DEBT0042）；返回规范化路径。

    委托 `agate_package.agate_home()`——"装到哪"与"解析到哪"（agate_common）共用同一实现。
    """
    return agate_package.agate_home()


def _raw_home():
    """未规范化的版本根路径（软链基址守卫需要原始文本：`L/..` 这类变体规范化后会丢失歧义信息）。"""
    env_home = os.environ.get("AGATE_HOME", "")
    if env_home:
        return env_home
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
            ["git", "clone", "--", url, repo], capture_output=True, text=True,
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
        if _VERSION_RE.fullmatch(tag):
            return tag
    return None


def _cleanup_container(home, container):
    """只清理本次进程刚创建的工作容器（前缀 + 真实目录 + 直属版本根）；其余一律不碰。"""
    if not container:
        return
    name = os.path.basename(container)
    if (
        name.startswith(agate_package.TMP_PREFIX)
        and os.path.dirname(os.path.abspath(container)) == os.path.abspath(home)
        and os.path.isdir(container)
        and not os.path.islink(container)
    ):
        shutil.rmtree(container, ignore_errors=True)


def _install_version(agate_home, repo, version):
    """装指定版本本体（TAG0037：git plumbing 构建器取代 git worktree add，只装 agate/ + 登记根文件）。

    幂等（BDD-3）：程序先判版本目录/指针存在，存在即跳过（含旧 worktree 整仓形态），不依赖 git 报错。
    流程：sweep_stale / recover_backups → list_package（失败：未建任何目录）→ make_work_dir →
    materialize 到 <容器>/pkg → swap_in（rename 到 vX.Y.Z、删空容器）。异常只清理本次进程创建的容器。
    """
    version_dir = os.path.join(agate_home, version)
    agate_package.sweep_stale(agate_home)
    agate_package.recover_backups(agate_home)
    if os.path.lexists(version_dir):
        print(f"{version} 已安装，跳过（幂等）")
        return
    try:
        entries = agate_package.list_package(repo, version)
    except agate_package.PackageError as exc:
        sys.stderr.write(f"错误: 无法从 {version} 构建本体包：{exc}\n")
        sys.exit(1)
    container = None
    try:
        container = agate_package.make_work_dir(agate_home, version)
        pkg = os.path.join(container, "pkg")
        os.mkdir(pkg, 0o700)
        agate_package.materialize(repo, version, pkg, entries)
        agate_package.swap_in(container, version_dir)
    except (agate_package.PackageError, OSError) as exc:
        _cleanup_container(agate_home, container)
        sys.stderr.write(f"错误: 安装 {version} 失败：{exc}\n")
        sys.exit(1)
    except BaseException:
        _cleanup_container(agate_home, container)
        raise


def _newest_installed_version(agate_home):
    """~/.agate 下已安装版本目录中最新者（按版本号）；无则 None。"""
    candidates = []
    try:
        entries = os.listdir(agate_home)
    except OSError:
        return None
    for entry in entries:
        if _VERSION_RE.fullmatch(entry) and os.path.isdir(os.path.join(agate_home, entry)):
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


_SYMLINK_HOME_MSG = (
    "错误: 版本根是软链，agate-install 会穿透软链把 repo/ 与 vX.Y.Z/ 静默建进软链目标，已拒绝（fail-closed）。\n"
    "迁移到版本管理布局（三步）：\n"
    "  1. 备份软链:  mv ~/.agate ~/.agate.bak\n"
    "  2. 建目录根:  mkdir -p ~/.agate\n"
    "  3. 装版本:    install.sh --versions\n"
    "               # 迁移完成后亦可: python3 ~/.agate/scripts/agate-install.py latest\n"
    "若 ~/.agate 是指向完整版本根的软链，解析仍可用，仅安装类命令需先改为实体目录或对软链目标直接执行安装。\n"
)


def _symlink_home_detail(raw):
    """首行：检测到的软链（规范化路径 → readlink 目标；或含经软链 `..` 的歧义路径的物理位置）。"""
    norm, _ambiguous = agate_package.normalize_home(raw)
    if os.path.islink(norm):
        with contextlib.suppress(OSError):
            return f"{norm} → {os.readlink(norm)}"
    return f"{norm}（原始路径 {raw} 含经软链解析的 '..'，物理位置 {os.path.realpath(raw)}）"


def _reject_symlink_home(agate_home):
    """软链基址守卫（BDD-32 / T-14）：规范化后是软链、或原始路径经软链的 `..` 解析歧义 → stderr + exit 1。"""
    for candidate in (_raw_home(), agate_home):
        if agate_package.is_symlink_base(candidate):
            sys.stderr.write(
                f"检测到的软链：{_symlink_home_detail(candidate)}；"
                "若它不是 ~/.agate，请把下列命令中的 ~/.agate 替换为它\n"
            )
            sys.stderr.write(_SYMLINK_HOME_MSG)
            sys.exit(1)


def _sync_root_scripts(agate_home, version_dir):
    """建立/刷新根 ~/.agate/scripts/ 入口副本（TAG0032 决策 B1，单源 copytree，副本非软链）。

    源 = 刚装版本的协议 scripts/（_protocol_root 探测：version_dir 或 version_dir/agate）。
    真实元仓库每个 tag 的 agate/scripts/ 本就含全套版本工具（agate-install.py /
    agate_common.py / resolve-entry.py 等，P1-requirements §3.4）——单次 copytree
    （dirs_exist_ok=True）即可让新机 ~/.agate/scripts/ 入口命令可直接调用（断点一
    「入口断链」修复），并随重跑 agate-install.py latest 跟随 current 版本刷新
    （BDD-4 判据 2）。忽略 `__pycache__` / `*.pyc`；`symlinks=True` 复制链接自身而非目标。

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
        shutil.copytree(
            proto_scripts, dst, dirs_exist_ok=True, symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    except OSError as exc:
        sys.stderr.write(
            f"WARNING: 根入口副本同步失败（{proto_scripts} → {dst}）：{exc}；"
            f"~/.agate/scripts/ 可能缺版本工具，可重跑 agate-install.py latest\n"
        )


def _register(agate_home, version, move_pointers):
    """登记已装版本：`move_pointers` 时写 latest → version、current → latest（失败还原快照，exit 1）；
    恒调用 `_sync_root_scripts`（指针写入之后，失败仅 WARNING）。"""
    if move_pointers:
        snap = agate_package.snapshot_pointers(agate_home)
        try:
            _write_pointer(agate_home, "latest", version)
            _write_pointer(agate_home, "current", "latest")
        except OSError as exc:
            with contextlib.suppress(OSError, agate_package.PackageError):
                agate_package.restore_pointers(agate_home, snap)
            sys.stderr.write(f"错误: 写 latest/current 指针失败（已还原）：{exc}\n")
            sys.exit(1)
    _sync_root_scripts(agate_home, os.path.join(agate_home, version))


def _cmd_install(agate_home, version=None):
    if version is not None and not _VERSION_RE.fullmatch(version):
        sys.stderr.write(f"错误: 非法版本号 {version!r}（应为 vX.Y.Z）\n")
        sys.exit(2)
    _reject_symlink_home(agate_home)
    url = os.environ.get("AGATE_REPO_URL", "") or DEFAULT_REPO_URL
    repo = _ensure_repo(agate_home, url)
    if version is None:
        tag = _latest_tag(repo)
        if tag is None:
            sys.stderr.write("错误: 版本源仓库没有可用的 vX.Y.Z tag\n")
            sys.exit(1)
        _install_version(agate_home, repo, tag)
        _register(agate_home, tag, move_pointers=True)
        print(f"已安装 latest → {tag}")
    else:
        _install_version(agate_home, repo, version)
        _register(agate_home, version, move_pointers=False)
        print(f"已安装 {version}")
    # 装完即告知**装到哪**与**怎么卸**——位置可经 AGATE_HOME 覆盖，写死 ~/.agate 会误导；
    # 且没有卸载指引时用户只能 rm -rf，那会留下平台接入物与 hook 断链（hook 断链会让
    # `git commit` 直接失败）。2026-09-21。
    entry = os.path.join(agate_home, "scripts", "agate-setup.py")
    print(f"安装根: {agate_home}")
    print(f"接入平台: python3 {entry}            # 注册 orchestrator 身份 + 装 hook")
    print(f"完整卸载: python3 {entry} --uninstall --all-projects --purge")
    sys.exit(0)


def _cmd_adopt(agate_home, version):
    """纳管已就位的版本目录（TAG0037 §3.3 / BDD-17）：只写指针 + 同步根 scripts/，不碰 git、不改版本目录。

    执行主体 = 调用方所在目录的 agate-install.py（同目录兄弟安装器语义，eng M-2）。
    新形态目录（无 .git）先 verify_dir 契约校验（顶层多余条目 / tests / 软链 → exit 1）；
    旧 worktree 形态（含 .git）跳过校验，保持兼容。指针写入失败由 `_register` 还原快照（eng N-2）。
    """
    if not _VERSION_RE.fullmatch(version):
        sys.stderr.write(f"错误: 非法版本号 {version!r}（应为 vX.Y.Z）\n")
        sys.exit(2)
    _reject_symlink_home(agate_home)
    version_dir = os.path.join(agate_home, version)
    if not os.path.isdir(version_dir):
        sys.stderr.write(f"错误: 版本目录不存在: {version_dir}（--adopt 只纳管已就位的 {version}，不下载不构建）\n")
        sys.exit(1)
    if not os.path.lexists(os.path.join(version_dir, ".git")):
        problems = agate_package.verify_dir(version_dir)
        if problems:
            sys.stderr.write(f"错误: {version_dir} 不符合版本目录结构契约，拒绝纳管：\n")
            for line in problems:
                sys.stderr.write(f"  - {line}\n")
            sys.exit(1)
    proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")
    if not os.path.isdir(proto_scripts):
        sys.stderr.write(f"错误: {version_dir} 缺协议 scripts/（{proto_scripts}），无法纳管\n")
        sys.exit(1)
    _register(agate_home, version, move_pointers=True)
    print(f"已纳管 {version}：latest → {version}，current → latest")
    sys.exit(0)


def _cmd_uninstall(agate_home, version):
    if not _VERSION_RE.fullmatch(version):
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
    has_repo = os.path.isdir(repo)

    # 旧形态（git worktree 整仓，含 .git 指针）才走 `git worktree remove`；新形态本体目录直接移除。
    if has_repo and os.path.lexists(os.path.join(version_dir, ".git")):
        rc, _out = run_git(["worktree", "remove", version_dir], cwd=repo)
        if rc != 0:
            run_git(["worktree", "remove", "--force", version_dir], cwd=repo)
    if os.path.islink(version_dir):
        with contextlib.suppress(OSError):
            os.unlink(version_dir)
    elif os.path.lexists(version_dir):
        shutil.rmtree(version_dir, ignore_errors=True)
    if os.path.lexists(version_dir):
        sys.stderr.write(f"错误: 无法删除版本目录 {version_dir}\n")
        sys.exit(1)
    if has_repo:
        # 幂等：清掉被替换旧形态遗留的 repo/.git/worktrees/<vX.Y.Z> 登记（eng m-4）。
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


_PORTABLE_HINTS = {
    "git": "git 缺失（仅在线安装 / 装历史 tag / agate-changes.py 需要 git；portable 离线场景无需）",
    "bash": "bash 缺失（仅安装 hook 需要 bash；portable 离线场景无需）",
}


def _cmd_check(portable=False):
    """环境探测：python3 / pyyaml / git / bash。全齐 exit 0；缺项非 0 + 分平台修复指引。

    `portable=True`（opt-in，BDD-18）：必需项仅 python3 + pyyaml；git / bash 缺失只打印提示行，不计入缺项。
    默认口径不变（缺 git 仍 exit 1，BDD-7/8）。
    """
    missing = []
    hints = []
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
        (hints if portable else missing).append("git")

    bash_path = shutil.which("bash")
    items.append(f"bash: {bash_path if bash_path else '缺失'}")
    if not bash_path:
        (hints if portable else missing).append("bash")

    for line in items:
        print("✓ " + line)

    for item in hints:
        print("提示: " + _PORTABLE_HINTS[item])

    if not missing:
        if portable:
            print("portable 环境满足（python3 / pyyaml 可用）")
        else:
            print("环境完整（python3 / pyyaml / git / bash 全部可用）")
        sys.exit(0)

    print("\n缺少: " + ", ".join(missing))
    print("修复指引:")
    for item in missing:
        for line in _fix_guidance(item):
            print("  " + line)
    sys.exit(1)


def _usage():
    print("用法: agate-install.py [latest | vX.Y.Z | --adopt vX.Y.Z | --uninstall vX.Y.Z | --check [--portable]]")
    print("  无参 / latest    装 latest 指针（最新发布 tag 的本体）+ current → latest")
    print("  vX.Y.Z           装指定版本（幂等，已装则跳过）")
    print("  --adopt vX.Y.Z   纳管已就位的版本目录：写 latest/current 指针 + 同步根 scripts/（不碰 git）")
    print("  --uninstall vX   卸载指定版本（引用保护扫描 + 移除版本目录 + 指针清理）")
    print("  --check          环境探测 python3 / pyyaml / git / bash")
    print("  --check --portable  portable 口径：仅 python3 + pyyaml 必需，git / bash 缺失只提示")


def main():
    args = sys.argv[1:]
    agate_home = _agate_home()

    if not args or (len(args) == 1 and args[0] == "latest"):
        # `latest` = 无参安装的显式别名（装最新发布 tag + current→latest；幂等复跑）。
        _cmd_install(agate_home)
    elif args[0] == "--check":
        if len(args) == 1:
            _cmd_check()
        elif args == ["--check", "--portable"]:
            _cmd_check(portable=True)
        else:
            sys.stderr.write("用法: agate-install.py --check [--portable]\n")
            sys.exit(2)
    elif args[0] == "--adopt":
        if len(args) != 2:
            sys.stderr.write("用法: agate-install.py --adopt vX.Y.Z\n")
            sys.exit(2)
        _cmd_adopt(agate_home, args[1])
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
        sys.stderr.write("用法: agate-install.py [vX.Y.Z | --adopt vX.Y.Z | --uninstall vX.Y.Z | --check [--portable]]\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
