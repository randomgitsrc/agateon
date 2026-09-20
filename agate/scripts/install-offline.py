#!/usr/bin/env python3
"""install-offline.py — 内网离线安装器（TAG0008 批次 offline，BDD-25~29；TAG0037 批 B2 重写）

在**内网**机器上安装 agate-pack-offline.py 打好的离线 bundle：
  1. 软链基址守卫（--dest-root / AGATE_HOME 规范化后是软链 → 三步迁移文案 exit 1）
  2. 读 manifest.json + 校验（version 严格 vX.Y.Z；组件 path 限 bundle 内）+ 平台核对（BDD-25）
  3. bundle 布局校验：旧格式（agate/agate/scripts 双层嵌套）拒绝（BDD-12）；软链 / 特殊文件拒绝；
     磁盘上 agate/** ∪ 登记根文件 与 manifest.files 逐项对账（多 / 少 / 改名 → exit 1）
  4. checksum 校验（不一致 → 拒绝安装 + 指明组件，BDD-26）
  5. 只把 manifest 已登记且已对账的**本体包集合 P** 拷进 `<dest>/.agate-tmp-…/pkg`（绝不拷 wheels/ manifest.json / python/）
  6. `pip install --no-index --find-links wheels/`（BDD-27；失败则丢弃临时目录，dest 不变）
  7. 换位：`vX.Y.Z/` 已存在则旧目录先移入带标记的备份容器（D-6），新目录就位
  8. 同目录兄弟 `agate-install.py --adopt vX.Y.Z` 写 latest / current 指针 + 同步根 scripts/；
     失败 → 还原版本目录与指针（旧版完整或新版完整）；成功 → 删除本次创建的备份容器

用法:
  python3 install-offline.py <bundle_dir> [--dest-root DIR] [--skip-python] [--skip-pillow]

- 缺省 dest = AGATE_HOME（缺省 ~/.agate），与版本解析同一实现。
- 嵌入式 python/ 组件（--include-python 打的包）不安装，仅打印一行说明。
- 不再写 `.installed-version` / `.agate-root`；`vX.Y.Z/` 顶层只含 agate/ 与登记根文件。

目录组件 sha256 约定（与 agate-pack-offline.py 一致）：对目录内全部文件按相对路径
字典序排序，逐一 sha256(file_bytes) 得 hex，拼为一条长串后整体 sha256（忽略字节码）。
"""

import contextlib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# 安装器自身不产生字节码（TAG0037 B-1）：真实用法是内网机器上直接运行 bundle/agate/scripts/install-offline.py，
# 若产生 pyc 会污染 bundle 的 agate 组件哈希。须先于 import agate_common / agate_package。
sys.dont_write_bytecode = True

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import agate_package  # noqa: E402  stdlib-only（不依赖 pyyaml）

# TAG0031 DEBT0002（R1，P2-design.md §1.3）：install-offline.py 刻意零外部依赖启动
# （可能跑在未装 pyyaml 的内网机器上），不能无条件 `from agate_common import
# compute_sha256`——agate_common.py 模块级 `import yaml` 失败会 sys.exit(1)，抢在
# "给它装 pyyaml"（install_wheels）之前就让安装器崩溃。这里先探测 yaml 是否已可用：
# 可用才顺带导入 agate_common，暴露同一个 compute_sha256 引用（供已装好环境下的直接
# 调用 / identity 检查，如全流程回归测试）；不可用时保持 None，运行时校验/安装改走
# `_ensure_agate_common`（先内联校验 pyyaml wheel checksum，通过才 pip install，见下）。
try:
    import yaml as _yaml_probe  # noqa: F401

    import agate_common as _agate_common_probe
except ImportError:
    _agate_common_probe = None

compute_sha256 = _agate_common_probe.compute_sha256 if _agate_common_probe else None

# 与 agate-install.py `_SYMLINK_HOME_MSG` 的三步迁移片段逐字相同（test_bdd_35 用同款正则抽取比对）。
_SYMLINK_HOME_MSG = (
    "错误: 版本根是软链，install-offline 会穿透软链把 vX.Y.Z/ 静默建进软链目标，已拒绝（fail-closed）。\n"
    "迁移到版本管理布局（三步）：\n"
    "  1. 备份软链:  mv ~/.agate ~/.agate.bak\n"
    "  2. 建目录根:  mkdir -p ~/.agate\n"
    "  3. 装版本:    install.sh --versions\n"
    "               # 迁移完成后亦可: python3 ~/.agate/scripts/agate-install.py latest\n"
    "若 ~/.agate 是指向完整版本根的软链，解析仍可用，仅安装类命令需先改为实体目录或对软链目标直接执行安装。\n"
)

_SUPPORTED_TOP = ("agate", "wheels", "manifest.json", "python", *agate_package.ROOT_FILES)


class BundleError(Exception):
    """bundle 布局 / 内容不合法（旧格式、软链、与 manifest.files 对账失败……）。"""


def load_manifest(manifest_path):
    """读 manifest.json 为 dict。"""
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def _has_control_chars(text):
    return any(ord(ch) < 32 or ord(ch) == 127 for ch in text)


def _validate_manifest(manifest, bundle_dir):
    """manifest 字段校验（CRITICAL-3，防路径穿越，fail-closed）。

    version 必须是严格 `vX.Y.Z`（fullmatch + ASCII；预发布后缀属于 source_ref，不进目录名）；
    source_ref（若有）须通过 parse_release_ref 且无控制字符，仅信息性、绝不参与路径拼接；
    每个组件 path 必须是 bundle 内相对路径（拒绝绝对路径与 '..'，断言 commonpath）。非法 → 抛 ValueError。
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest 不是 JSON 对象")
    version = manifest.get("version", "")
    if not isinstance(version, str) or not agate_package.is_strict_version(version):
        raise ValueError(f"manifest version 非法: {version!r}（应为严格 vX.Y.Z）")
    source_ref = manifest.get("source_ref")
    if source_ref is not None:
        try:
            ok = isinstance(source_ref, str) and not _has_control_chars(source_ref)
            if ok:
                agate_package.parse_release_ref(source_ref)
        except ValueError:
            ok = False
        if not ok:
            raise ValueError("manifest source_ref 非法（应为 vX.Y.Z[-预发布]，不含控制字符）")
    bundle = Path(bundle_dir).resolve()
    components = manifest.get("components", {})
    if not isinstance(components, dict):
        raise ValueError("manifest components 不是对象")
    for name, comp in components.items():
        raw = comp.get("path", "") if isinstance(comp, dict) else ""
        if not isinstance(raw, str) or not raw:
            raise ValueError(f"manifest 组件 {name!r} 缺 path 字段")
        p = Path(raw)
        if p.is_absolute():
            raise ValueError(f"manifest 组件 {name!r} path 为绝对路径: {raw!r}")
        if ".." in p.parts:
            raise ValueError(f"manifest 组件 {name!r} path 含 '..': {raw!r}")
        resolved = (bundle / p).resolve()
        try:
            if os.path.commonpath([str(bundle), str(resolved)]) != str(bundle):
                raise ValueError(f"manifest 组件 {name!r} path 越出 bundle: {raw!r}")
        except ValueError as exc:
            raise ValueError(f"manifest 组件 {name!r} path 越出 bundle: {raw!r}") from exc


def get_current_platform():
    """返回当前机器平台标签（linux-x86_64 / windows-x86_64）；main 经它核对平台。"""
    import platform as _platform

    machine = _platform.machine().lower()
    if sys.platform == "win32":
        return "windows-x86_64"
    if machine in ("x86_64", "amd64"):
        return "linux-x86_64"
    return f"linux-{machine}"


def check_platform(manifest_platform, current_platform):
    """平台核对纯逻辑；True = 匹配。"""
    return manifest_platform == current_platform


def _ensure_agate_common(bundle_dir, manifest):
    """引导获取 agate_common 模块引用（TAG0031 DEBT0002 R1 缓解设计，P2-design.md §1.3）。

    install-offline.py 刻意零外部依赖（可能在未装 pyyaml 的内网机器上跑），而
    agate_common.py 模块级 `import yaml` 失败即 sys.exit(1)——直接
    `from agate_common import compute_sha256` 会在"给它装 pyyaml"之前就让安装器崩溃。

    先探测 `import yaml` 是否可用：可用则直接 `import agate_common` 返回模块引用。
    不可用时分三步：①内联 `hashlib.sha256` 单独校验 manifest 中 pyyaml 组件的
    checksum；不匹配 → stderr 报错（指明 pyyaml）+ 返回 None，不执行 pip install（校验
    先于安装）；②校验通过后才 `pip install --no-index --find-links <bundle>/wheels
    pyyaml`（bundle 自带 wheel，不联网）；③成功后 `import agate_common` 返回模块引用。
    """
    try:
        import yaml  # noqa: F401
    except ImportError:
        pyyaml_comp = manifest.get("components", {}).get("pyyaml")
        if not pyyaml_comp:
            sys.stderr.write(
                "install-offline: yaml 不可用且 manifest 缺少 pyyaml 组件，无法引导 agate_common\n"
            )
            return None
        wheel_path = Path(bundle_dir) / pyyaml_comp.get("path", "")
        try:
            actual = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
        except OSError as exc:
            sys.stderr.write(f"install-offline: 读取 pyyaml wheel 失败: {exc}\n")
            return None
        if actual != pyyaml_comp.get("sha256"):
            sys.stderr.write(
                "install-offline: pyyaml checksum 校验失败（引导安装前置检查），"
                "组件与 manifest 记录不一致（损坏或被替换），拒绝安装\n"
            )
            return None

        wheels_dir = Path(bundle_dir) / "wheels"
        try:
            subprocess.run(
                ["pip", "install", "--no-index", "--find-links", str(wheels_dir), "pyyaml"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            sys.stderr.write(f"install-offline: 引导安装 pyyaml 失败: {exc}\n")
            return None

    import agate_common

    return agate_common


def verify_checksums(manifest, bundle_dir):
    """逐组件按 manifest path 定位、重算 sha256 比对；返回不匹配组件名列表（空 = 全过）。

    先 `_validate_manifest` 校验字段（version 严格 + 组件 path 限 bundle 内，CRITICAL-3）——
    拒绝篡改 manifest 用 `..`/绝对路径越界读 bundle 外文件（哈希比对作为可探测 oracle）。
    再经 `_ensure_agate_common` 引导拿到 agate_common 模块引用（TAG0031 DEBT0002 R1），
    hash 实现改为共享单实现 `agate_common.compute_sha256`（不再本地重复定义）。
    """
    _validate_manifest(manifest, bundle_dir)
    agate_common_mod = _ensure_agate_common(bundle_dir, manifest)
    if agate_common_mod is None:
        raise RuntimeError("agate_common 引导失败，无法执行 checksum 校验（见上方 stderr 详情）")
    bundle = Path(bundle_dir)
    mismatched = []
    for name, comp in manifest.get("components", {}).items():
        p = bundle / comp["path"]
        if not p.exists():
            mismatched.append(name)
            continue
        if agate_common_mod.compute_sha256(p) != comp["sha256"]:
            mismatched.append(name)
    return mismatched


def _short(paths, limit=8):
    paths = sorted(paths)
    text = ", ".join(paths[:limit])
    return text + (f" …（共 {len(paths)} 项）" if len(paths) > limit else "")


def _check_bundle_layout(bundle_dir, manifest):
    """bundle 布局校验（P2 §3.4 步骤 3）；返回告警列表（契约外顶层条目），不合法抛 BundleError。

    * `agate/agate/scripts` 是目录 → 旧格式（整仓检出双层嵌套），拒绝而非自动归一化（BDD-12）；
    * `agate/scripts` 不存在 → 缺本体；manifest 缺 `files` → fail-closed；
    * `agate/`、登记根文件逐项 lstat：软链 / 设备 / FIFO / socket 一律拒绝（不跟随软链）；
    * 对账：磁盘 `agate/**` ∪ 顶层登记根文件（忽略字节码）== manifest.files。
    """
    bundle = str(bundle_dir)
    agate_dir = os.path.join(bundle, agate_package.PKG_DIR)
    if os.path.isdir(os.path.join(agate_dir, agate_package.PKG_DIR, "scripts")):
        raise BundleError(
            "bundle 为旧格式（`agate/agate/scripts` 双层嵌套），"
            "请用新版 `agate-pack-offline.py` 重新打包"
        )
    if not os.path.isdir(os.path.join(agate_dir, "scripts")):
        raise BundleError("bundle 缺本体：agate/scripts/ 不存在")
    files = manifest.get("files")
    if not isinstance(files, list) or not files or not all(isinstance(f, str) for f in files):
        raise BundleError("manifest 缺 files 清单（旧版 pack 产物？），请用新版 `agate-pack-offline.py` 重新打包")
    for rel in files:
        if not agate_package.is_packaged(rel) or rel.startswith("/") or ".." in rel.split("/"):
            raise BundleError(f"manifest.files 含契约外路径: {rel!r}")

    try:
        st = os.lstat(agate_dir)
    except OSError as exc:
        raise BundleError(f"无法读取 bundle/agate: {exc}") from exc
    if not stat.S_ISDIR(st.st_mode):
        raise BundleError("bundle/agate 不是真实目录（软链不允许）")
    disk = set()
    for dirpath, dirnames, filenames in os.walk(agate_dir, followlinks=False):
        for name in [*dirnames, *filenames]:
            full = os.path.join(dirpath, name)
            mode = os.lstat(full).st_mode
            rel_display = os.path.relpath(full, bundle).replace(os.sep, "/")
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise BundleError(f"bundle 内含软链或特殊文件（不允许）: {rel_display}")
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), bundle).replace(os.sep, "/")
            if not agate_package._is_bytecode(rel):
                disk.add(rel)
    for name in agate_package.ROOT_FILES:
        path = os.path.join(bundle, name)
        try:
            mode = os.lstat(path).st_mode
        except OSError:
            continue  # 历史 tag 可缺登记根文件
        if not stat.S_ISREG(mode):
            raise BundleError(f"bundle 登记根文件不是普通文件（软链 / 特殊文件不允许）: {name}")
        disk.add(name)

    listed = set(files)
    extra, missing = disk - listed, listed - disk
    if extra or missing:
        parts = []
        if extra:
            parts.append(f"磁盘多出（manifest.files 未登记）: {_short(extra)}")
        if missing:
            parts.append(f"磁盘缺少（manifest.files 已登记）: {_short(missing)}")
        raise BundleError("bundle 内容与 manifest.files 不一致——" + "；".join(parts))

    return [
        f"bundle 顶层出现契约外条目 {name}，不会被安装（只安装 manifest.files 登记的本体包集合）"
        for name in sorted(os.listdir(bundle))
        if name not in _SUPPORTED_TOP
    ]


def install_wheels(bundle_dir, skip=()):
    """pip install --no-index --find-links <bundle>/wheels——安装清单从 manifest components 推导。

    有 "pillow" 组件才装 Pillow（无 Pillow bundle 默认流不再失败，CRITICAL-2）；
    "pyyaml" 组件必有 → 默认装 pyyaml。skip 只过滤已包含项（BDD-29）。
    """
    wheels_dir = Path(bundle_dir) / "wheels"
    manifest = load_manifest(Path(bundle_dir) / "manifest.json")
    components = manifest.get("components", {})
    cmd = ["pip", "install", "--no-index", "--find-links", str(wheels_dir)]
    for comp, pkg in (("pyyaml", "pyyaml"), ("pillow", "Pillow")):
        if comp in components and comp not in skip:
            cmd.append(pkg)
    try:
        subprocess.run(
            cmd, capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise RuntimeError(f"pip install 失败: {exc}") from exc


def _symlink_home_detail(raw):
    norm, _ambiguous = agate_package.normalize_home(raw)
    if os.path.islink(norm):
        with contextlib.suppress(OSError):
            return f"{norm} → {os.readlink(norm)}"
    return f"{norm}（原始路径 {raw} 含经软链解析的 '..'，物理位置 {os.path.realpath(raw)}）"


def _reject_symlink_dest(raw_dest, dest_root):
    """软链基址守卫（BDD-33 / T-14）：规范化后是软链、或原始路径经软链的 `..` 解析歧义 → 返回 True 并写 stderr。"""
    for candidate in (raw_dest, dest_root):
        if agate_package.is_symlink_base(candidate):
            sys.stderr.write(
                f"检测到的软链：{_symlink_home_detail(candidate)}；"
                "若它不是 ~/.agate，请把下列命令中的 ~/.agate 替换为它\n"
            )
            sys.stderr.write(_SYMLINK_HOME_MSG)
            return True
    return False


def _cleanup_own_container(dest_root, container):
    """只清理本次进程刚创建的工作容器（专属前缀 + 直属版本根 + 真实目录）；其余一律不碰。"""
    if not container:
        return
    name = os.path.basename(container)
    if (
        name.startswith(agate_package.TMP_PREFIX)
        and os.path.dirname(os.path.abspath(container)) == os.path.abspath(dest_root)
        and os.path.isdir(container)
        and not os.path.islink(container)
    ):
        shutil.rmtree(container, ignore_errors=True)


def _run_adopt(dest_root, version):
    """同目录兄弟 agate-install.py --adopt（M-2：bundle 版本与安装器版本解耦）；返回 CompletedProcess。"""
    installer = os.path.join(_SCRIPT_DIR, "agate-install.py")
    env = dict(os.environ)
    env["AGATE_HOME"] = dest_root
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", installer, "--adopt", version],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _install(bundle_dir, manifest, dest_root, skip):
    """校验通过后的安装事务（步骤 5~9）；返回 0 / 1。任何时刻旧版完整或新版完整。"""
    version = manifest["version"]
    files = manifest["files"]
    vdir = os.path.join(dest_root, version)

    agate_package.sweep_stale(dest_root)
    agate_package.recover_backups(dest_root)

    root_preexisted = os.path.isdir(dest_root)
    container = None
    try:
        container = agate_package.make_work_dir(dest_root, version)
        pkg = os.path.join(container, "pkg")
        os.mkdir(pkg, 0o700)
        agate_package.copy_files(bundle_dir, files, pkg)  # 只拷 manifest 已登记且已对账的文件
        problems = agate_package.verify_dir(pkg)
        if problems:
            raise BundleError("待安装内容不符合版本目录结构契约: " + "; ".join(problems))
        install_wheels(bundle_dir, skip=tuple(skip))  # 有系统副作用：排在拷贝之后、换位之前
    except (agate_package.PackageError, BundleError, RuntimeError, OSError) as exc:
        _cleanup_own_container(dest_root, container)
        if not root_preexisted:
            with contextlib.suppress(OSError):
                os.rmdir(dest_root)  # 仅当空（本次刚建）才成功
        sys.stderr.write(f"install-offline: 安装失败: {exc}\n")
        return 1

    snap = agate_package.snapshot_pointers(dest_root)
    try:
        backup = agate_package.swap_in(container, vdir)
    except (agate_package.PackageError, OSError) as exc:
        _cleanup_own_container(dest_root, container)
        sys.stderr.write(f"install-offline: 安装失败（换位未完成，旧版本保持原样）: {exc}\n")
        return 1

    try:
        proc = _run_adopt(dest_root, version)
        adopt_err = None if proc.returncode == 0 else (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
    except OSError as exc:
        proc, adopt_err = None, str(exc)
    if adopt_err is not None:
        try:
            agate_package.rollback_swap(backup, vdir)
            agate_package.restore_pointers(dest_root, snap)
        except (agate_package.PackageError, OSError) as exc:
            sys.stderr.write(f"install-offline: --adopt 失败且还原未完成，请人工检查 {dest_root}: {exc}\n")
            sys.stderr.write(f"--adopt 输出: {adopt_err}\n")
            return 1
        sys.stderr.write(f"install-offline: --adopt 失败: {adopt_err}\n")
        sys.stderr.write("版本目录与 latest/current 指针均已还原，请修复后重跑\n")
        return 1

    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)  # 例如根 scripts/ 同步的 WARNING
    if backup is not None:
        agate_package.discard_backup(backup)  # 仅本次自己创建的备份容器
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    bundle_dir = None
    dest_arg = None
    skip = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--dest-root":
            i += 1
            if i >= len(args):
                sys.stderr.write("install-offline: --dest-root 缺少取值\n")
                return 2
            dest_arg = args[i]
        elif a == "--skip-python":
            skip.append("python")
        elif a == "--skip-pillow":
            skip.append("pillow")
        elif a.startswith("--"):
            sys.stderr.write(f"install-offline: 未知选项 {a}\n")
            return 2
        else:
            bundle_dir = a
        i += 1

    if not bundle_dir:
        sys.stderr.write("install-offline: 缺少 bundle 目录参数\n")
        return 2

    # 1. dest 缺省 = AGATE_HOME；规范化后守卫软链基址（先于任何写入）
    if dest_arg is not None:
        raw_dest = dest_arg
    else:
        raw_dest = os.environ.get("AGATE_HOME", "") or os.path.join(os.path.expanduser("~"), ".agate")
    dest_root = agate_package.normalize_home(raw_dest)[0]
    if _reject_symlink_dest(raw_dest, dest_root):
        return 1

    # 2. manifest 读取 / 校验 + 平台核对
    manifest_path = Path(bundle_dir) / "manifest.json"
    try:
        manifest = load_manifest(manifest_path)
        _validate_manifest(manifest, bundle_dir)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"install-offline: 读取/校验 manifest 失败: {exc}\n")
        return 1

    manifest_platform = manifest.get("platform", "")
    current_platform = get_current_platform()
    if not check_platform(manifest_platform, current_platform):
        sys.stderr.write(
            f"install-offline: 平台不匹配——bundle 平台 {manifest_platform} "
            f"与本机平台 {current_platform} 不一致，拒绝安装\n"
        )
        return 1

    # 3. bundle 布局 / 对账（先于 checksum 与任何写入）
    try:
        warnings = _check_bundle_layout(bundle_dir, manifest)
    except (BundleError, OSError) as exc:
        sys.stderr.write(f"install-offline: {exc}\n")
        return 1
    for line in warnings:
        sys.stderr.write(f"install-offline: 警告: {line}\n")

    # 4. checksum
    try:
        mismatched = verify_checksums(manifest, bundle_dir)
    except RuntimeError as exc:
        sys.stderr.write(f"install-offline: {exc}\n")
        return 1
    if mismatched:
        sys.stderr.write(
            "install-offline: checksum 校验失败，以下组件与 manifest 记录不一致（损坏或被替换）: "
            + ", ".join(mismatched) + "\n"
        )
        return 1

    # 5~9. 事务化安装
    code = _install(bundle_dir, manifest, dest_root, skip)
    if code != 0:
        return code
    if "python" in manifest.get("components", {}):
        print("说明：嵌入式 python/ 组件不随本体安装（请使用系统 Python 3.8+），已忽略。")
    source_ref = manifest.get("source_ref")
    suffix = f"（源 ref: {source_ref}）" if isinstance(source_ref, str) and source_ref != manifest["version"] else ""
    print(f"已安装 {manifest['version']}{suffix} → {os.path.join(dest_root, manifest['version'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
