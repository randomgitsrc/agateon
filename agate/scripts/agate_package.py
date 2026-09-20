#!/usr/bin/env python3
"""agate_package — 本体（`agate/` 目录）打包边界与构建的单一来源（TAG0037，RM-AG0066）。

三条交付路径（在线安装 / 离线 pack+install / Release workflow）共用本模块：
  git ref --list_package--> 包集合 P --materialize--> 目录 --write_dir_tarball--> 确定性 tar.gz

边界规则是本文件里的显式常量（默认拒绝：非 `agate/**` 且非登记根文件一律不入包），`boundary_lines()`
把它们渲染进 `agate/UPGRADING.md` 的契约小节；不读任何配置 / manifest / .gitattributes。

约束（P2 §3.2）：
  * stdlib-only（不 import agate_common——后者模块级 import yaml；安装器 `--check`、`install-offline`
    在 pyyaml 缺失时也必须可运行）。Python 3.8+，文本 I/O 显式 UTF-8。
  * 落盘一律 O_EXCL|O_NOFOLLOW 逐文件创建；路径硬化见 `_validate_relpath`。
  * 清扫 / 备份只认「本工具专属前缀 + 专属标记文件」，**绝不按名字模式删除**任何目录（cso N-1）。
"""

import collections
import contextlib
import errno
import hashlib
import io
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import zlib

sys.dont_write_bytecode = True

# ---------------------------------------------------------------------------
# 边界规则常量（单一来源；`boundary_lines()` 渲染，UPGRADING 契约块与之逐条对齐）
# ---------------------------------------------------------------------------

PKG_DIR = "agate"
ROOT_FILES = ("CHANGELOG.md", "LICENSE", "NOTICES.md")  # 登记根文件（可缺失于历史 tag）
HIDDEN_METADATA = ()  # 登记的隐藏元数据（当前为空）
EXCLUDE_PKG_SUBDIRS = ("tests",)  # agate/ 下整目录排除（casefold 比较）
EXCLUDE_DIR_NAMES = ("__pycache__",)  # 任意层级
EXCLUDE_SUFFIXES = (".pyc", ".pyo")
TMP_PREFIX = ".agate-tmp-"
BAK_PREFIX = ".agate-bak-"
MARKER_NAME = ".agate-installer-owned"
MARKER_MAGIC = "agate-package/1"
TOP_LEVEL = tuple(sorted((PKG_DIR, *ROOT_FILES, *HIDDEN_METADATA)))
VERSION_RE = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)  # 一律 fullmatch
RELEASE_REF_RE = re.compile(r"(v[0-9]+\.[0-9]+\.[0-9]+)(?:-([0-9A-Za-z][0-9A-Za-z.-]*))?", re.ASCII)
PYYAML_PIN = "6.0.3"  # workflow 与 agate-pack-offline 同源取值（agate-release.py pyyaml-pin）

STALE_TMP_SECONDS = 3600  # sweep_stale：标记 mtime 早于此才清扫（避开并发安装的活跃容器）
_GIT_TIMEOUT = 300
_OK_MODES = ("100644", "100755")
_POINTER_NAMES = ("latest", "current")

_O_BINARY = getattr(os, "O_BINARY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)

# 本进程创建的备份容器（discard_backup 只认它们，realpath 口径）
_CREATED_BACKUPS = set()


class PackageError(RuntimeError):
    """包集合 / 落盘 / 打包过程中的可预期失败（畸形 tag、危险成员、目的地被占用 …）。"""


PackageEntry = collections.namedtuple("PackageEntry", "path mode sha")


# ---------------------------------------------------------------------------
# 边界判定（纯函数）
# ---------------------------------------------------------------------------


def _is_bytecode(relpath):
    parts = relpath.replace("\\", "/").split("/")
    if any(p in EXCLUDE_DIR_NAMES for p in parts[:-1]) or (parts and parts[-1] in EXCLUDE_DIR_NAMES):
        return True
    return relpath.endswith(EXCLUDE_SUFFIXES)


def is_packaged(relpath):
    """相对路径（正斜杠）是否属于本体包。默认拒绝：非 `agate/**` 且非登记根文件 → False。"""
    if isinstance(relpath, bytes):
        relpath = relpath.decode("utf-8", "surrogateescape")
    parts = relpath.split("/")
    if len(parts) == 1:
        return relpath in ROOT_FILES or relpath in HIDDEN_METADATA
    if parts[0] != PKG_DIR:
        return False
    if len(parts) >= 2 and parts[1].casefold() in EXCLUDE_PKG_SUBDIRS:
        return False
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return False
    return not relpath.endswith(EXCLUDE_SUFFIXES)


def boundary_lines():
    """边界规则的确定性文本渲染（UPGRADING「版本目录结构契约」fenced 块的生成源）。"""
    lines = [f"include {PKG_DIR}/"]
    lines += [f"exclude {PKG_DIR}/{d}/" for d in EXCLUDE_PKG_SUBDIRS]
    lines += [f"exclude **/{d}/" for d in EXCLUDE_DIR_NAMES]
    lines += [f"exclude *{s}" for s in EXCLUDE_SUFFIXES]
    lines += [f"root-file {n}" for n in (*ROOT_FILES, *HIDDEN_METADATA)]
    return lines


def is_strict_version(s):
    return isinstance(s, str) and VERSION_RE.fullmatch(s) is not None


def parse_release_ref(tag):
    """`vX.Y.Z` 或 `vX.Y.Z-<预发布后缀>` → (严格版本, 是否预发布)；不合法 → ValueError。

    一律 fullmatch（`$` 会放过尾部换行），re.ASCII（拒绝 Unicode 数字）。
    """
    if not isinstance(tag, str):
        raise ValueError(f"发布 tag 必须是字符串: {tag!r}")
    m = RELEASE_REF_RE.fullmatch(tag)
    if m is None:
        raise ValueError(f"不是合法的发布 tag（应为 vX.Y.Z 或 vX.Y.Z-<后缀>）: {tag!r}")
    suffix = m.group(2)
    if suffix is not None and (".." in suffix or suffix.endswith(".") or suffix.endswith(".lock")):
        raise ValueError(f"预发布后缀不合法: {tag!r}")
    return m.group(1), suffix is not None


# ---------------------------------------------------------------------------
# 路径硬化
# ---------------------------------------------------------------------------


def _validate_relpath(path):
    """包内相对路径的硬化检查（D-16 / T-17）；违规 → PackageError。path 为 str（已通过严格 UTF-8 解码）。"""
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        raise PackageError(f"不安全的包内路径: {path!r}")
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        raise PackageError(f"不安全的包内路径（盘符）: {path!r}")
    for ch in path:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            raise PackageError(f"包内路径含控制字符: {path!r}")
    for seg in path.split("/"):
        if seg in ("", ".", ".."):
            raise PackageError(f"包内路径含空段 / '.' / '..': {path!r}")
        if ":" in seg:
            raise PackageError(f"包内路径分量含 ':': {path!r}")
        if seg.casefold() in (".git", ".gitmodules"):
            raise PackageError(f"包内路径含 .git / .gitmodules 分量: {path!r}")
        if seg.endswith((" ", ".")):
            raise PackageError(f"包内路径分量以空格或 '.' 结尾: {path!r}")


def _check_case_collisions(paths):
    seen = {}
    for p in paths:
        key = p.casefold()
        other = seen.get(key)
        if other is not None and other != p:
            raise PackageError(f"包内路径仅大小写不同（冲突）: {other!r} / {p!r}")
        seen[key] = p


# ---------------------------------------------------------------------------
# git plumbing
# ---------------------------------------------------------------------------


def _git_env():
    """去掉会改变仓库定位的 GIT_* 变量（如 hook 里的 GIT_DIR）；其余原样保留。"""
    drop = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    }
    return {k: v for k, v in os.environ.items() if k not in drop}


def _check_ref(ref):
    if not isinstance(ref, str) or not ref or ref.startswith("-") or "\x00" in ref or "\n" in ref:
        raise PackageError(f"不安全的 git ref: {ref!r}")


def _git(repo, args, timeout=_GIT_TIMEOUT):
    try:
        proc = subprocess.run(
            ["git", "-C", os.fspath(repo), *args],
            capture_output=True,
            env=_git_env(),
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise PackageError("未找到 git（本操作需要 git）") from exc
    except subprocess.TimeoutExpired as exc:
        raise PackageError(f"git {' '.join(args)} 超时") from exc
    if proc.returncode != 0:
        raise PackageError(f"git {' '.join(args)} 失败: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def list_package(repo, ref):
    """枚举 `ref` 上的包集合 P：排序后的 PackageEntry 列表。

    畸形（软链 / 子模块 / 危险路径 / 大小写冲突 / 非 UTF-8 / 缺 agate/scripts/）→ PackageError。
    不在包区（docs/ site/ …）的怪名字不影响结果。
    """
    _check_ref(ref)
    out = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", ref])
    entries = {}
    for rec in out.split(b"\x00"):
        if not rec:
            continue
        try:
            head, raw_path = rec.split(b"\t", 1)
            mode, otype, sha = head.decode("ascii").split(" ")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PackageError(f"无法解析 git ls-tree 输出: {rec[:80]!r}") from exc
        path = raw_path.decode("utf-8", "surrogateescape")
        if not is_packaged(path):
            continue
        try:
            path = raw_path.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PackageError(f"包内路径不是合法 UTF-8: {raw_path!r}") from exc
        if mode not in _OK_MODES or otype != "blob":
            raise PackageError(f"包内成员不是普通文件（mode={mode} type={otype}，软链 / 子模块不允许）: {path!r}")
        _validate_relpath(path)
        entries[path] = PackageEntry(path, mode, sha)
    ordered = [entries[p] for p in sorted(entries)]
    _check_case_collisions([e.path for e in ordered])
    if not any(e.path.startswith(f"{PKG_DIR}/scripts/") for e in ordered):
        raise PackageError(f"{ref} 的树内没有 {PKG_DIR}/scripts/，不是合法的 agate 发布 tag")
    return ordered


def _umask():
    mask = os.umask(0)
    os.umask(mask)
    return mask


def _mkdirs_exclusive(dest, rel_dir, created):
    """在 dest 下逐级 os.mkdir（不用 makedirs(exist_ok)）；只在本函数创建过的目录上继续，避免沿用预置的软链目录。"""
    cur = dest
    for seg in rel_dir.split("/"):
        cur = os.path.join(cur, seg)
        if cur in created:
            continue
        try:
            os.mkdir(cur)
        except FileExistsError as exc:
            raise PackageError(f"目的地已存在同名条目: {cur}") from exc
        created.add(cur)


def _check_within(dest, target):
    dest_abs = os.path.abspath(dest)
    target_abs = os.path.abspath(target)
    try:
        inside = os.path.commonpath([dest_abs, target_abs]) == dest_abs
    except ValueError:
        inside = False
    if not inside or dest_abs == target_abs:
        raise PackageError(f"成员越界: {target}")


def _write_new_file(path, data, executable):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW | _O_BINARY
    try:
        fd = os.open(path, flags, 0o755 if executable else 0o644)
    except OSError as exc:
        raise PackageError(f"无法创建文件（已存在或被占用）: {path}: {exc}") from exc
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def _dest_guard(dest):
    if os.path.islink(dest) or not os.path.isdir(dest):
        raise PackageError(f"目的地必须是真实目录（不是软链）: {dest}")


def _finish_dest(dest):
    with contextlib.suppress(OSError):
        os.chmod(dest, 0o777 & ~_umask())


def materialize(repo, ref, dest, entries=None):
    """把 `ref` 上的包集合按 blob 原始字节落盘到 `dest`（须是调用方刚创建的空目录）。返回 PackageEntry 列表。"""
    dest = os.fspath(dest)
    _dest_guard(dest)
    if entries is None:
        entries = list_package(repo, ref)
    entries = list(entries)
    try:
        proc = subprocess.Popen(
            ["git", "-C", os.fspath(repo), "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_git_env(),
        )
    except FileNotFoundError as exc:
        raise PackageError("未找到 git（本操作需要 git）") from exc
    created = set()
    try:
        for e in entries:
            proc.stdin.write(e.sha.encode("ascii") + b"\n")
            proc.stdin.flush()
            header = proc.stdout.readline().decode("ascii", "replace").split()
            if len(header) != 3 or header[1] != "blob":
                raise PackageError(f"git 对象不是 blob: {e.path!r}: {' '.join(header)}")
            size = int(header[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)  # 记录尾部的换行
            if len(data) != size:
                raise PackageError(f"读取 blob 不完整: {e.path!r}")
            algo = "sha256" if len(e.sha) == 64 else "sha1"
            if hashlib.new(algo, b"blob %d\x00" % size + data).hexdigest() != e.sha:
                raise PackageError(f"blob 校验和不符: {e.path!r}")
            target = os.path.join(dest, *e.path.split("/"))
            _check_within(dest, target)
            if "/" in e.path:
                _mkdirs_exclusive(dest, e.path.rsplit("/", 1)[0], created)
            _write_new_file(target, data, e.mode == "100755")
    finally:
        with contextlib.suppress(Exception):
            proc.stdin.close()
        with contextlib.suppress(Exception):
            proc.stdout.close()
        with contextlib.suppress(Exception):
            proc.wait(timeout=30)
    _finish_dest(dest)
    return entries


def copy_files(src_root, relpaths, dest):
    """离线安装用：把 `src_root` 下 `relpaths` 逐个拷进 `dest`。

    逐个 lstat：非普通文件（软链 / 设备 / FIFO / socket）→ PackageError；同样 O_EXCL|O_NOFOLLOW 落盘；
    命中 EXCLUDE_* 的字节码忽略。
    """
    src_root = os.fspath(src_root)
    dest = os.fspath(dest)
    _dest_guard(dest)
    created = set()
    for rel in sorted(relpaths):
        if _is_bytecode(rel):
            continue
        _validate_relpath(rel)
        cur = src_root
        segs = rel.split("/")
        for i, seg in enumerate(segs):
            cur = os.path.join(cur, seg)
            try:
                st = os.lstat(cur)
            except OSError as exc:
                raise PackageError(f"源文件缺失: {rel!r}: {exc}") from exc
            last = i == len(segs) - 1
            if last and not stat.S_ISREG(st.st_mode):
                raise PackageError(f"源成员不是普通文件（软链 / 设备 / FIFO 不允许）: {rel!r}")
            if not last and not stat.S_ISDIR(st.st_mode):
                raise PackageError(f"源成员的上级不是真实目录（软链不允许）: {rel!r}")
        try:
            fd = os.open(cur, os.O_RDONLY | _O_NOFOLLOW | _O_BINARY)
        except OSError as exc:
            raise PackageError(f"无法读取源文件: {rel!r}: {exc}") from exc
        with os.fdopen(fd, "rb") as fh:
            if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
                raise PackageError(f"源成员不是普通文件: {rel!r}")
            data = fh.read()
        target = os.path.join(dest, *segs)
        _check_within(dest, target)
        if len(segs) > 1:
            _mkdirs_exclusive(dest, "/".join(segs[:-1]), created)
        _write_new_file(target, data, bool(st.st_mode & 0o111))
    _finish_dest(dest)


def commit_mtime(repo, ref):
    """`ref` 指向的**提交**的 committer 时间（附注 tag 也剥壳），用于确定性打包。"""
    _check_ref(ref)
    out = _git(repo, ["log", "-1", "--format=%ct", ref, "--"]).decode("ascii", "replace").strip()
    try:
        return int(out)
    except ValueError as exc:
        raise PackageError(f"无法取得 {ref} 的提交时间: {out!r}") from exc


# ---------------------------------------------------------------------------
# 确定性 tar.gz
# ---------------------------------------------------------------------------


class _GzipSink(io.RawIOBase):
    """手写 gzip 容器：头 FNAME=0 / MTIME=0 / OS=255，与 Python 版本无关。"""

    def __init__(self, raw):
        self._raw = raw
        self._comp = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
        self._crc = 0
        self._size = 0
        self._pos = 0
        raw.write(b"\x1f\x8b\x08\x00" + b"\x00\x00\x00\x00" + b"\x02\xff")

    def writable(self):
        return True

    def tell(self):
        return self._pos

    def write(self, data):
        data = bytes(data)
        self._crc = zlib.crc32(data, self._crc)
        self._size += len(data)
        self._pos += len(data)
        chunk = self._comp.compress(data)
        if chunk:
            self._raw.write(chunk)
        return len(data)

    def finish(self):
        self._raw.write(self._comp.flush())
        self._raw.write(struct.pack("<II", self._crc & 0xFFFFFFFF, self._size & 0xFFFFFFFF))


def _collect_tar_members(src_dir, arc_prefix):
    """先于任何写入校验全部成员；返回按 arcname 排序的 [(arcname, abspath, mode)]。"""
    src_dir = os.fspath(src_dir)
    if os.path.islink(src_dir) or not os.path.isdir(src_dir):
        raise PackageError(f"源目录必须是真实目录: {src_dir}")
    prefix = arc_prefix.strip("/") if arc_prefix else ""
    if prefix:
        _validate_relpath(prefix)
    members = []

    def walk(abs_dir, rel_dir):
        with os.scandir(abs_dir) as it:
            children = sorted(it, key=lambda d: d.name)
        for child in children:
            rel = f"{rel_dir}/{child.name}" if rel_dir else child.name
            st = os.lstat(child.path)
            if stat.S_ISDIR(st.st_mode):
                if child.name in EXCLUDE_DIR_NAMES:
                    continue
                walk(child.path, rel)
            elif stat.S_ISREG(st.st_mode):
                if rel.endswith(EXCLUDE_SUFFIXES):
                    continue
                _validate_relpath(rel)
                members.append((f"{prefix}/{rel}" if prefix else rel, child.path, 0o755 if st.st_mode & 0o111 else 0o644))
            else:
                raise PackageError(f"源目录含非普通文件成员（软链 / 设备 / FIFO / socket 不允许）: {rel!r}")

    walk(src_dir, "")
    members.sort(key=lambda m: m[0])
    _check_case_collisions([m[0] for m in members])
    return members


def write_dir_tarball(src_dir, out_path, mtime, arc_prefix=""):
    """把目录打成确定性 tar.gz：仅普通文件、按 arcname 排序、mode 归一 0644/0755、uid/gid=0、无 uname/gname、
    PAX 格式、gzip 头不含文件名 / 时间。遇软链 / 特殊文件 → PackageError（先于任何写入）。"""
    members = _collect_tar_members(src_dir, arc_prefix)
    out_path = os.fspath(out_path)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    fd, tmp = tempfile.mkstemp(prefix=".agate-tarball-", suffix=".part", dir=out_dir)
    try:
        with os.fdopen(fd, "wb") as raw:
            sink = _GzipSink(raw)
            tf = tarfile.open(fileobj=sink, mode="w", format=tarfile.PAX_FORMAT, encoding="utf-8")
            try:
                for arcname, abspath, mode in members:
                    rfd = os.open(abspath, os.O_RDONLY | _O_NOFOLLOW | _O_BINARY)
                    with os.fdopen(rfd, "rb") as fh:
                        st = os.fstat(fh.fileno())
                        if not stat.S_ISREG(st.st_mode):
                            raise PackageError(f"源成员不是普通文件: {arcname!r}")
                        info = tarfile.TarInfo(arcname)
                        info.size = st.st_size
                        info.mtime = int(mtime)
                        info.mode = mode
                        info.type = tarfile.REGTYPE
                        info.uid = info.gid = 0
                        info.uname = info.gname = ""
                        tf.addfile(info, fh)
            finally:
                tf.close()
            sink.finish()
        os.replace(tmp, out_path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# 契约验证
# ---------------------------------------------------------------------------


def verify_dir(root, extra_top=(), ignore_bytecode=True):
    """纯文件系统检查：顶层 ⊆ TOP_LEVEL ∪ extra_top、无 agate/tests、无软链 / 特殊文件；返回违约描述列表。

    字节码（`__pycache__` / `*.pyc` / `*.pyo`）按 ignore_bytecode 忽略（运行后态不算违约，D-13）。
    """
    root = os.fspath(root)
    problems = []
    allowed = set(TOP_LEVEL) | set(extra_top)
    try:
        names = sorted(os.listdir(root))
    except OSError as exc:
        return [f"无法读取目录 {root}: {exc}"]

    def walk(abs_dir, rel_dir):
        try:
            children = sorted(os.listdir(abs_dir))
        except OSError as exc:
            problems.append(f"无法读取 {rel_dir}: {exc}")
            return
        for name in children:
            rel = f"{rel_dir}/{name}" if rel_dir else name
            path = os.path.join(abs_dir, name)
            st = os.lstat(path)
            if stat.S_ISLNK(st.st_mode):
                problems.append(f"软链不允许: {rel}")
            elif stat.S_ISDIR(st.st_mode):
                if name in EXCLUDE_DIR_NAMES:
                    if not ignore_bytecode:
                        problems.append(f"含字节码目录: {rel}")
                    continue
                if rel_dir == PKG_DIR and name.casefold() in EXCLUDE_PKG_SUBDIRS:
                    problems.append(f"不应存在的目录（tests 不入包）: {rel}")
                    continue
                walk(path, rel)
            elif stat.S_ISREG(st.st_mode):
                if name.endswith(EXCLUDE_SUFFIXES) and not ignore_bytecode:
                    problems.append(f"含字节码文件: {rel}")
            else:
                problems.append(f"非普通文件成员: {rel}")

    for name in names:
        path = os.path.join(root, name)
        if name not in allowed:
            problems.append(f"未登记的顶层条目: {name}")
            continue
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode):
            problems.append(f"软链不允许: {name}")
        elif stat.S_ISDIR(st.st_mode):
            walk(path, name)
        elif not stat.S_ISREG(st.st_mode):
            problems.append(f"非普通文件成员: {name}")
    return problems


# ---------------------------------------------------------------------------
# AGATE_HOME 规范化与软链基址守卫（D-14）
# ---------------------------------------------------------------------------


def normalize_home(path):
    """(规范化路径, 是否歧义)。

    norm = abspath(expanduser(path))（去尾 "/"、"/."、多余斜杠、文本 ".."）；
    ambiguous = 原始路径的物理解析（经软链的 ".."）与规范化文本路径的物理解析不一致。
    """
    expanded = os.path.expanduser(os.fspath(path))
    norm = os.path.abspath(expanded)
    ambiguous = os.path.realpath(expanded) != os.path.realpath(norm)
    return norm, ambiguous


def is_symlink_base(path):
    """`path`（原始或已规范化）是否是软链基址：规范化后是软链，或存在物理 / 文本解析歧义。"""
    norm, ambiguous = normalize_home(path)
    return os.path.islink(norm) or ambiguous


def agate_home():
    """版本根：`AGATE_HOME` 优先，否则 `~/.agate`；返回规范化路径（安装与解析共用同一实现）。"""
    env_home = os.environ.get("AGATE_HOME", "")
    if env_home:
        return normalize_home(env_home)[0]
    return normalize_home(os.path.join(os.path.expanduser("~"), ".agate"))[0]


# ---------------------------------------------------------------------------
# 工作 / 备份容器（专属前缀 + 专属标记；绝不按名字模式删除，R-8）
# ---------------------------------------------------------------------------


def _write_marker(container, kind, version):
    line = f"{MARKER_MAGIC} kind={kind} version={version} pid={os.getpid()}\n"
    fd = os.open(os.path.join(container, MARKER_NAME), os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW | _O_BINARY, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(line.encode("utf-8"))


def _marker_first_line(container):
    """标记文件首行；标记缺失 / 是软链 / 非普通文件 → None。不跟随软链。"""
    path = os.path.join(container, MARKER_NAME)
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            return None
        fd = os.open(path, os.O_RDONLY | _O_NOFOLLOW | _O_BINARY)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as fh:
        raw = fh.read(512)
    return raw.decode("utf-8", "replace").split("\n", 1)[0].strip()


def _marker_is(container, kind):
    line = _marker_first_line(container)
    if line is None:
        return False
    return line.split()[:2] == [MARKER_MAGIC, f"kind={kind}"]


def _is_real_dir(path):
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError:
        return False


def _release_container(container):
    """删除只剩本工具标记的空容器（不 rmtree）；容器里还有别的内容则原样保留。"""
    with contextlib.suppress(OSError):
        os.unlink(os.path.join(container, MARKER_NAME))
    with contextlib.suppress(OSError):
        os.rmdir(container)


def make_work_dir(root, version):
    """在版本根 `root` 内建专属工作容器 `.agate-tmp-<ver>-XXXX`（0700）并立即写标记；产物放 `<container>/pkg`。"""
    if not is_strict_version(version):
        raise PackageError(f"不合法的版本号: {version!r}")
    root = os.fspath(root)
    os.makedirs(root, exist_ok=True)
    container = tempfile.mkdtemp(prefix=f"{TMP_PREFIX}{version}-", dir=root)
    try:
        _write_marker(container, "tmp", version)
    except BaseException:
        with contextlib.suppress(OSError):
            os.rmdir(container)
        raise
    return container


def sweep_stale(root):
    """仅清理「`.agate-tmp-` 前缀 + 真实目录 + 标记有效(kind=tmp) + 标记 mtime 早于 1 小时」的容器。

    绝不按名字模式删除；不动 `.agate-bak-*` / `vX.Y.Z.bak-*` / 无标记目录 / 软链（cso N-1）。
    """
    try:
        names = os.listdir(os.fspath(root))
    except OSError:
        return
    now = time.time()
    for name in names:
        if not name.startswith(TMP_PREFIX):
            continue
        path = os.path.join(root, name)
        if not _is_real_dir(path) or not _marker_is(path, "tmp"):
            continue
        try:
            age = now - os.lstat(os.path.join(path, MARKER_NAME)).st_mtime
        except OSError:
            continue
        if age > STALE_TMP_SECONDS:
            with contextlib.suppress(OSError):
                shutil.rmtree(path)


def recover_backups(root):
    """只改名不删：`vX.Y.Z` 缺失时把备份容器内 `old/` 挪回；否则仅在 stderr 提示遗留备份路径。"""
    root = os.fspath(root)
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return
    for name in names:
        if not name.startswith(BAK_PREFIX):
            continue
        path = os.path.join(root, name)
        if not _is_real_dir(path) or not _marker_is(path, "bak"):
            continue
        version = name[len(BAK_PREFIX) :].rsplit("-", 1)[0]
        if not is_strict_version(version):
            continue
        old = os.path.join(path, "old")
        final = os.path.join(root, version)
        if os.path.lexists(final):
            print(f"提示：检测到遗留备份 {path}（{version} 已存在，未改动）；确认无用后可手动删除。", file=sys.stderr)
            continue
        if not _is_real_dir(old):
            continue
        try:
            os.rename(old, final)
        except OSError as exc:
            print(f"警告：无法从备份还原 {version}（{path}）: {exc}", file=sys.stderr)
            continue
        print(f"提示：{version} 缺失，已从备份 {path} 还原。", file=sys.stderr)
        _release_container(path)


def swap_in(container, final):
    """把 `<container>/pkg` 换位为 `final`；返回备份容器路径（final 原本不存在则 None）。

    final 已存在 → 先移入 `.agate-bak-<ver>-XXXX/old`（带标记）；第二步失败自动还原旧目录并删除本次备份容器。
    成功后删除已空的工作容器。
    """
    container = os.fspath(container)
    final = os.fspath(final)
    pkg_dir = os.path.join(container, "pkg")
    root = os.path.dirname(os.path.abspath(final))
    version = os.path.basename(final)
    backup = None
    if os.path.lexists(final):
        if not is_strict_version(version):
            raise PackageError(f"不合法的版本目录名: {version!r}")
        if os.path.islink(final):
            raise PackageError(f"版本目录是软链，拒绝换位: {final}")
        backup = tempfile.mkdtemp(prefix=f"{BAK_PREFIX}{version}-", dir=root)
        try:
            _write_marker(backup, "bak", version)
            os.rename(final, os.path.join(backup, "old"))
        except BaseException:
            _release_container(backup)
            raise
        _CREATED_BACKUPS.add(os.path.realpath(backup))
    try:
        os.rename(pkg_dir, final)
    except BaseException:
        if backup is not None:
            with contextlib.suppress(OSError):
                os.rename(os.path.join(backup, "old"), final)
            _CREATED_BACKUPS.discard(os.path.realpath(backup))
            _release_container(backup)
        raise
    _release_container(container)
    return backup


def rollback_swap(backup, final):
    """adopt 失败时：把已换位的新目录挪走（删除，属本进程刚建）并还原备份；backup 为 None 时只挪走新目录。"""
    final = os.fspath(final)
    if backup is None:
        if _is_real_dir(final):
            shutil.rmtree(final)
        return
    backup = os.fspath(backup)
    if not (_is_real_dir(backup) and _marker_is(backup, "bak") and os.path.realpath(backup) in _CREATED_BACKUPS):
        raise PackageError(f"拒绝回滚：不是本次创建的备份容器: {backup}")
    old = os.path.join(backup, "old")
    if not _is_real_dir(old):
        raise PackageError(f"备份容器内缺少 old/: {backup}")
    failed = os.path.join(backup, "failed-new")
    if os.path.lexists(final):
        os.rename(final, failed)
    os.rename(old, final)
    if _is_real_dir(failed):
        shutil.rmtree(failed)
    _CREATED_BACKUPS.discard(os.path.realpath(backup))
    _release_container(backup)


def discard_backup(backup):
    """仅删本次进程创建、标记与名字校验通过的备份容器；其余一律拒绝（返回 False，目录原样保留）。"""
    backup = os.fspath(backup)
    ok = (
        os.path.basename(backup).startswith(BAK_PREFIX)
        and _is_real_dir(backup)
        and _marker_is(backup, "bak")
        and os.path.realpath(backup) in _CREATED_BACKUPS
    )
    if not ok:
        print(f"警告：拒绝删除非本次创建的备份容器: {backup}", file=sys.stderr)
        return False
    shutil.rmtree(backup)
    _CREATED_BACKUPS.discard(os.path.realpath(backup))
    return True


# ---------------------------------------------------------------------------
# latest / current 指针快照与还原（adopt 事务化，eng N-2）
# ---------------------------------------------------------------------------


def snapshot_pointers(root):
    """记录 latest / current 的存在性与形态：`("link", 目标)` / `("file", 文本)` / `("other", None)`(目录等) / None。"""
    snap = {}
    for name in _POINTER_NAMES:
        path = os.path.join(os.fspath(root), name)
        try:
            st = os.lstat(path)
        except OSError:
            snap[name] = None
            continue
        if stat.S_ISLNK(st.st_mode):
            snap[name] = ("link", os.readlink(path))
        elif stat.S_ISREG(st.st_mode):
            with open(path, encoding="utf-8", newline="") as fh:
                snap[name] = ("file", fh.read())
        else:
            snap[name] = ("other", None)
    return snap


def restore_pointers(root, snap):
    """按快照还原（先删现状的软链 / 普通文件再重建）；目录形态不删不改。"""
    root = os.fspath(root)
    for name in _POINTER_NAMES:
        path = os.path.join(root, name)
        state = snap.get(name)
        if state is not None and state[0] == "other":
            continue
        try:
            st = os.lstat(path)
        except OSError:
            st = None
        if st is not None:
            if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                raise PackageError(f"无法还原指针 {name}：位置上是目录")
            os.unlink(path)
        if state is None:
            continue
        kind, value = state
        if kind == "link":
            try:
                os.symlink(value, path)
            except (OSError, NotImplementedError) as exc:
                if getattr(exc, "errno", None) == errno.EEXIST:
                    raise
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(value + "\n")
        else:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(value)
