#!/usr/bin/env python3
"""agate-pack-offline.py — 外网离线打包器（TAG0008 批次 offline，BDD-22~24；TAG0037 批 B2 重写）

在**外网**机器上把指定版本 tag 的 agate 本体 + 目标平台的依赖 wheels 打包成
离线部署 bundle，供内网机器经 install-offline.py 安装。

用法:
  python3 agate-pack-offline.py v0.48.0 [--platform linux-x86_64|windows-x86_64]
      [--outdir DIR] [--repo DIR] [--ref REF] [--include-python] [--include-pillow]

- 默认平台 linux-x86_64；默认 repo = `<AGATE_HOME>/repo`（AGATE_HOME 缺省 ~/.agate，
  与在线安装 / 版本解析同一实现）；默认 outdir 当前目录。
- `--ref REF`：内容取自该 git ref（如预发布 tag `v0.73.0-rc.1`）；manifest.version 恒为
  严格 `vX.Y.Z`，`source_ref` 原样记录 ref（仅信息性）。
- 产物：`<outdir>/agate-<version>-<platform>/`（= 版本目录布局 + 安装输入物），内含：
    agate/                    # 本体目录内容（agate_package.materialize，git plumbing，非整仓检出）
    CHANGELOG.md LICENSE NOTICES.md   # 登记根文件（历史 tag 缺则缺）
    wheels/                   # pip download 拉到的 pyyaml==PYYAML_PIN [Pillow] wheel
    manifest.json             # platform + version + source_ref + files + 各组件 {path, sha256}
- 失败路径（BDD-24）：tag 不存在 / 树内无 agate/scripts/ / pip download 网络失败 / wheel 缺失
  → 抛 PackOfflineError（main 捕获 → stderr + 非 0 退出），不产 manifest.json；
  构建发生在本工具专属的临时容器里，成功后才换位为最终目录（失败只清理本次创建的容器）。

目录组件 sha256 约定（与 install-offline.py 一致）：对目录内全部文件按相对路径
字典序排序，逐一 sha256(file_bytes) 得 hex，拼为一条长串后整体 sha256（忽略字节码）。
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 打包器自身不产生字节码（D-13）：须先于 import agate_common / agate_package。
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# TAG0031 DEBT0002：compute_sha256 共享单实现（agate_common）；agate_package 为 stdlib-only。
import agate_package  # noqa: E402
from agate_common import compute_sha256  # noqa: E402

# 平台标签 → pip --platform 值（P2 §7 minimal_validation 已实测可用）
_PIP_PLATFORMS = {
    "linux-x86_64": "manylinux_2_17_x86_64",
    "windows-x86_64": "win_amd64",
}


class PackOfflineError(RuntimeError):
    """打包失败信号（tag 不存在 / 无本体 / pip download 失败 / wheel 缺失）。"""


def _default_repo():
    """缺省 --repo：运行时取 `<AGATE_HOME>/repo`（BDD-10，与在线安装 / 解析同源）。"""
    return os.path.join(agate_package.agate_home(), "repo")


def _run(cmd, cwd=None):
    """subprocess.run 封装：非 0 退出抛 CalledProcessError（调用方转为 PackOfflineError）。"""
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=True,
    )


def build_manifest(version, platform, components, base=None, files=None, source_ref=None):
    """构造 manifest dict：components {name: Path} → {name: {path, sha256}}。

    path 为相对 bundle 根（`base`，缺省取各组件的公共祖先）的相对路径；目录组件用 compute_sha256 目录约定。
    `files`（包集合 P 的相对路径清单）/ `source_ref`（信息性）给出时写入。
    """
    comps = {}
    if base is None:
        base = os.getcwd()
        if components:
            base = os.path.commonpath([os.path.abspath(str(p)) for p in components.values()])
    for name, comp_path in components.items():
        cp = Path(comp_path)
        rel = os.path.relpath(os.path.abspath(str(cp)), str(base)).replace(os.sep, "/")
        comps[name] = {"path": rel, "sha256": compute_sha256(cp)}
    manifest = {"version": version, "platform": platform, "components": comps}
    if source_ref is not None:
        manifest["source_ref"] = source_ref
    if files is not None:
        manifest["files"] = list(files)
    return manifest


def _fetch_embedded_python(platform, bundle):
    """（可选）下载嵌入式 Python 到 bundle/python/。失败 → PackOfflineError。"""
    import urllib.request

    py_dir = bundle / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    if platform == "windows-x86_64":
        url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    else:
        url = "https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz"
    dest = py_dir / Path(url).name
    try:
        urllib.request.urlretrieve(url, str(dest))
    except Exception as exc:
        raise PackOfflineError(f"嵌入式 Python 下载失败: {exc}") from exc
    return dest


def _find_wheel(wheels_dir, prefix):
    """按分发名前缀大小写无关地找 wheel（pyyaml 6.0.2 的实际文件名是大写 `PyYAML-…`，cso F-2 / E-16）。"""
    want = prefix.lower() + "-"
    hits = sorted(
        p for p in Path(wheels_dir).iterdir()
        if p.is_file() and p.name.lower().startswith(want) and p.name.lower().endswith(".whl")
    )
    return hits[0] if hits else None


def _cleanup_own_container(out, container):
    """只清理本次进程刚创建的工作容器（专属前缀 + 直属输出目录 + 真实目录）；其余一律不碰。"""
    if not container:
        return
    name = os.path.basename(container)
    if (
        name.startswith(agate_package.TMP_PREFIX)
        and os.path.dirname(os.path.abspath(container)) == os.path.abspath(str(out))
        and os.path.isdir(container)
        and not os.path.islink(container)
    ):
        shutil.rmtree(container, ignore_errors=True)


def pack_offline(version, platform, out_dir, repo_dir, include_python=False, include_pillow=False, ref=None):
    """打包主流程，返回 bundle 目录 Path（out_dir/agate-{version}-{platform}）。

    `ref` 缺省 = version；`version` 若带预发布后缀（如 v0.73.0-rc.1）则 manifest.version 取其严格部分、ref 取原文。
    """
    try:
        strict_version, _pre = agate_package.parse_release_ref(version)
    except ValueError as exc:
        raise PackOfflineError(f"版本号非法: {version!r}（应为 vX.Y.Z[-预发布]）: {exc}") from exc
    if ref is None:
        ref = version
    version = strict_version

    pip_platform = _PIP_PLATFORMS.get(platform)
    if not pip_platform:
        raise PackOfflineError(f"不支持的平台标签: {platform}（应为 linux-x86_64 / windows-x86_64）")

    try:
        entries = agate_package.list_package(repo_dir, ref)
    except agate_package.PackageError as exc:
        raise PackOfflineError(f"版本 {ref} 无法构建本体包: {exc}") from exc

    out = Path(out_dir)
    bundle = out / f"agate-{version}-{platform}"
    if os.path.lexists(str(bundle)):
        raise PackOfflineError(f"输出目录已存在，拒绝覆盖: {bundle}（请换 --outdir 或自行移走）")

    container = None
    try:
        container = agate_package.make_work_dir(str(out), version)
        stage = Path(container) / "pkg"
        os.mkdir(str(stage), 0o700)
        agate_package.materialize(repo_dir, ref, str(stage), entries)

        wheels_dir = stage / "wheels"
        wheels_dir.mkdir()
        cmd = [
            "pip", "download", "--platform", pip_platform, "--python-version", "311",
            "--only-binary=:all:", "--no-deps", "-d", str(wheels_dir), f"pyyaml=={agate_package.PYYAML_PIN}",
        ]
        if include_pillow:
            cmd.append("Pillow")
        try:
            _run(cmd)
        except (subprocess.CalledProcessError, OSError) as exc:
            raise PackOfflineError(f"pip download 失败（网络或平台 wheel 不可得）: {exc}") from exc

        pyyaml_wheel = _find_wheel(wheels_dir, "pyyaml")
        if pyyaml_wheel is None:
            raise PackOfflineError(f"pyyaml wheel 缺失（--platform {pip_platform} 未拉到 wheel）")
        components = {"agate": stage / "agate"}
        for name in agate_package.ROOT_FILES:
            if (stage / name).is_file():  # 历史 tag 可缺登记根文件
                components[name] = stage / name
        components["wheels"] = wheels_dir
        components["pyyaml"] = pyyaml_wheel
        if include_pillow:
            pillow_wheel = _find_wheel(wheels_dir, "pillow")
            if pillow_wheel is None:
                raise PackOfflineError("Pillow wheel 缺失")
            components["pillow"] = pillow_wheel
        if include_python:
            components["python"] = _fetch_embedded_python(platform, stage)

        manifest = build_manifest(
            version, platform, components, base=stage, files=[e.path for e in entries], source_ref=ref,
        )
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        os.rename(str(stage), str(bundle))
        agate_package._release_container(container)  # 只剩本工具标记的空容器
    except PackOfflineError:
        _cleanup_own_container(out, container)
        raise
    except (agate_package.PackageError, OSError) as exc:
        _cleanup_own_container(out, container)
        raise PackOfflineError(f"打包失败: {exc}") from exc
    except BaseException:
        _cleanup_own_container(out, container)
        raise
    return bundle


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    version = None
    platform = "linux-x86_64"
    out_dir = os.getcwd()
    repo_dir = None
    ref = None
    include_python = False
    include_pillow = False
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--platform", "--outdir", "--repo", "--ref"):
            i += 1
            if i >= len(args):
                sys.stderr.write(f"agate-pack-offline: {a} 缺少取值\n")
                return 2
            if a == "--platform":
                platform = args[i]
            elif a == "--outdir":
                out_dir = args[i]
            elif a == "--repo":
                repo_dir = args[i]
            else:
                ref = args[i]
        elif a == "--include-python":
            include_python = True
        elif a == "--include-pillow":
            include_pillow = True
        elif a.startswith("--"):
            sys.stderr.write(f"agate-pack-offline: 未知选项 {a}\n")
            return 2
        else:
            version = a
        i += 1

    if not version:
        sys.stderr.write("agate-pack-offline: 缺少版本参数（如 v0.48.0）\n")
        return 2
    if repo_dir is None:
        repo_dir = _default_repo()

    try:
        bundle = pack_offline(
            version, platform, out_dir, repo_dir,
            include_python=include_python, include_pillow=include_pillow, ref=ref,
        )
    except PackOfflineError as exc:
        sys.stderr.write(f"agate-pack-offline: {exc}\n")
        return 1
    print(f"打包完成: {bundle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
