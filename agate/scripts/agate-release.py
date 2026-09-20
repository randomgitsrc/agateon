#!/usr/bin/env python3
"""agate-release.py — Release 构建 CLI（TAG0037 批 C1；P2 §3.6）

release workflow 内零打包逻辑：全部走本 CLI，因此本地（无 CI）可复现 CI 产物、可被单元测试直接调用。

子命令：
  boundary                          打印本体包边界规则（UPGRADING 契约块的生成源，== agate_package.boundary_lines()）
  pyyaml-pin                        打印 offline 包 / workflow 共用的 pyyaml 固定版本（agate_package.PYYAML_PIN）
  notes --tag T [--changelog F] --out FILE
                                    从 CHANGELOG 提取 T 的发布说明（正式 tag：缺段 / 段体为空 → exit 1 且不写文件；
                                    预发布 tag：取去后缀版本段，缺段回落 [Unreleased]，首行为预发布标注）
  is-prerelease T                   exit 0 = 预发布；exit 1 = 正式；exit 2 = 非法 tag
  build --tag T --repo R --outdir D --notes-out F [--expect-sha SHA] [--platforms p1,p2] [--skip-offline]
                                    确定性构建 agateon-<T>.tar.gz（本体）+ 每平台 offline 包 + SHA256SUMS + notes；
                                    先在暂存目录构建、全部成功后才落到 outdir（失败不留半成品）

契约：Python 3.8+；stdlib-only（agate_common 仅在 build 内延迟导入）；文本 I/O 显式 UTF-8；
SHA256SUMS 只防下载损坏、不认证发布者（notes 头部如实标注）。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

# 本脚本自身不产生字节码（D-13）：须先于任何 `import agate_*`。
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agate_package  # noqa: E402  stdlib-only

DEFAULT_PLATFORMS = ("linux-x86_64", "windows-x86_64")
_PACK_TIMEOUT = 900
_SECTION_HEAD_RE = re.compile(r"^## \[([^\]]+)\]")
_LINK_DEF_RE = re.compile(r"^\[[^\]]+\]:\s*\S")
_SHA_RE = re.compile(r"[0-9a-fA-F]{7,64}")


class ReleaseError(RuntimeError):
    """发布构建失败信号（main 转 stderr + exit 1）。"""


class NotesError(ReleaseError):
    """CHANGELOG 无可用段（正式 tag 缺段 / 段体为空；预发布回落后仍缺）。"""


# ---------------------------------------------------------------------------
# notes
# ---------------------------------------------------------------------------


def _split_sections(text):
    """CHANGELOG 文本 → {段名: [行]}（段名取 `## [名]` 的方括号内容；同名首次出现优先；不含标题行）。

    `## ` 开头的任何行都结束上一段（`###` 不结束）；非 `## [x]` 形式的 `## ` 行只做分隔。
    """
    sections = {}
    current = None
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith("## "):
            m = _SECTION_HEAD_RE.match(line)
            if m and m.group(1) not in sections:
                current = m.group(1)
                sections[current] = []
            else:
                current = None
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _clean_body(lines):
    """去首部空行、尾部空行与 Keep-a-Changelog 链接定义行；全空 → None。"""
    body = list(lines)
    while body and (not body[-1].strip() or _LINK_DEF_RE.match(body[-1])):
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
    return "\n".join(body) if body else None


def _lookup(sections, name):
    for key, lines in sections.items():
        norm = key[1:] if key.startswith("v") else key
        if norm == name:
            return _clean_body(lines)
    return None


def _header(tag, prerelease):
    lines = []
    if prerelease:
        lines += [f"预发布测试（{tag}）——非正式发布", ""]
    lines += [
        "## 下载与校验说明",
        "",
        f"- 推荐下载 `agateon-{tag}.tar.gz`（本体）：解压即得版本目录内容（`agate/` 与登记根文件）。",
        '- GitHub 自动生成的 "Source code" 压缩包是整仓（整个仓库的快照），不是安装包，请勿用于安装。',
        f"- `agateon-{tag}-offline-<平台>.tar.gz` 为离线安装包（含依赖 wheel），面向 Python 3.11。",
        "- `SHA256SUMS` 仅用于发现下载损坏，不认证发布者：它与资产同处一个 Release，发布者账号被攻破时无法防护；",
        "  需要更强保证请从 git tag 自行构建（`agate-release.py build`）后逐成员比对，或经第二渠道核对哈希。",
        "",
    ]
    return lines


def extract_notes(text, tag, wheels=None):
    """从 CHANGELOG 文本生成 `tag` 的发布说明（头部说明 + 版本段正文 [+ offline wheel 清单]）。

    正式 tag：取 `[X.Y.Z]` 段，缺段或段体为空 → NotesError（绝不回落 [Unreleased]）。
    预发布 tag：取去后缀版本段，缺段回落 `[Unreleased]`，仍缺 → NotesError；首行为预发布标注。
    `wheels`：{平台: [(wheel 文件名, sha256)]}，给出则附 offline 包内 wheel 清单。tag 非法 → ValueError。
    """
    strict, prerelease = agate_package.parse_release_ref(tag)
    sections = _split_sections(text)
    ver = strict[1:]
    body = _lookup(sections, ver)
    if body is None and prerelease:
        body = _lookup(sections, "Unreleased")
    if body is None:
        if prerelease:
            raise NotesError(f"CHANGELOG 既无 [{ver}] 段也无可用的 [Unreleased] 段（或均为空），预发布 tag {tag} 无法生成 notes")
        raise NotesError(f"CHANGELOG 缺少 [{ver}] 段（或段体为空），正式 tag {tag} 不可发布：请先在 CHANGELOG 写入该版本段")
    out = _header(tag, prerelease)
    out.append(body)
    if wheels:
        out += ["", "## offline 包内 wheel（文件名与 sha256）", ""]
        for plat in sorted(wheels):
            out.append(f"**{plat}**")
            out.append("")
            out += [f"- `{name}`  sha256 `{digest}`" for name, digest in sorted(wheels[plat])]
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def _write_text(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


def _rev_commit(repo, rev):
    return agate_package._git(repo, ["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"]).decode("ascii", "replace").strip()


def _check_expect_sha(repo, tag, sha):
    """两侧都剥成 commit：轻量 / 附注 tag、`GITHUB_SHA` 为 commit 或 tag 对象 SHA 均正确。"""
    if not _SHA_RE.fullmatch(sha):
        raise ReleaseError(f"--expect-sha 不是合法的十六进制 SHA: {sha!r}")
    try:
        tag_commit = _rev_commit(repo, f"refs/tags/{tag}")
        want_commit = _rev_commit(repo, sha)
    except agate_package.PackageError as exc:
        raise ReleaseError(f"无法解析 tag / SHA: {exc}") from exc
    if tag_commit != want_commit:
        raise ReleaseError(
            f"tag {tag} 指向提交 {tag_commit}，与 --expect-sha 提交 {want_commit} 不一致（tag 被移动，或来源与触发提交不一致）"
        )


def _sha256(path):
    from agate_common import compute_sha256  # 延迟导入：仅 build 需要（其顶层依赖 pyyaml）

    return compute_sha256(path)


def _build_offline(tag, repo, platform, work):
    """子进程调用 agate-pack-offline.py（-B + PYTHONDONTWRITEBYTECODE）；返回 bundle 目录。"""
    strict, _pre = agate_package.parse_release_ref(tag)
    out = os.path.join(work, f"pack-{platform}")
    os.mkdir(out)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agate-pack-offline.py")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B", script, strict, "--ref", tag, "--platform", platform, "--outdir", out, "--repo", str(repo)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=_PACK_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"offline 打包子进程失败（{platform}）: {exc}") from exc
    if proc.returncode != 0:
        raise ReleaseError(f"offline 打包失败（{platform}, rc={proc.returncode}）: {proc.stderr.strip()}")
    bundle = os.path.join(out, f"agate-{strict}-{platform}")
    if not os.path.isdir(bundle):
        raise ReleaseError(f"offline 打包未产出预期目录: {bundle}")
    return bundle


def _is_within(path, base):
    path = os.path.realpath(path)
    base = os.path.realpath(base)
    try:
        return os.path.commonpath([path, base]) == base
    except ValueError:
        return False


def build(tag, repo, outdir, notes_out, expect_sha=None, platforms=DEFAULT_PLATFORMS, skip_offline=False):
    """确定性构建全部发布资产；失败不留半成品（先暂存、全部成功后才落到 outdir 与 notes_out）。返回资产名列表。"""
    _strict, _pre = agate_package.parse_release_ref(tag)  # 非法 → ValueError
    if not skip_offline:
        for plat in platforms:
            if plat not in DEFAULT_PLATFORMS:
                raise ValueError(f"不支持的平台标签: {plat}（应为 {' / '.join(DEFAULT_PLATFORMS)}）")
    if _is_within(notes_out, outdir):
        raise ReleaseError("--notes-out 不得位于 --outdir 内（outdir 的全部文件会被公开为 Release 资产）")
    if os.path.lexists(outdir) and (os.path.islink(outdir) or not os.path.isdir(outdir) or os.listdir(outdir)):
        raise ReleaseError(f"--outdir 已存在且非空（或不是真实目录），拒绝覆盖: {outdir}")

    if expect_sha:
        _check_expect_sha(repo, tag, expect_sha)
    try:
        entries = agate_package.list_package(repo, tag)  # 畸形 tag 在此失败（先于任何写入）
        mtime = agate_package.commit_mtime(repo, tag)
        changelog = agate_package._git(repo, ["show", f"{tag}:CHANGELOG.md"]).decode("utf-8")
    except agate_package.PackageError as exc:
        raise ReleaseError(f"无法从 {tag} 取得构建输入: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ReleaseError(f"{tag} 的 CHANGELOG.md 不是合法 UTF-8: {exc}") from exc
    extract_notes(changelog, tag)  # fail-closed：缺段在产生任何文件前失败（wheel 清单稍后补入）

    work = tempfile.mkdtemp(prefix=".agate-release-")
    try:
        stage = os.path.join(work, "assets")
        os.mkdir(stage)
        names = []

        body_name = f"agateon-{tag}.tar.gz"
        pkg_dir = tempfile.mkdtemp(prefix="pkg-", dir=work)
        agate_package.materialize(repo, tag, pkg_dir, entries)
        agate_package.write_dir_tarball(pkg_dir, os.path.join(stage, body_name), mtime)
        names.append(body_name)

        wheels = {}
        if not skip_offline:
            for plat in platforms:
                bundle = _build_offline(tag, repo, plat, work)
                wheel_dir = os.path.join(bundle, "wheels")
                wheels[plat] = [
                    (f, _sha256(os.path.join(wheel_dir, f)))
                    for f in sorted(os.listdir(wheel_dir))
                    if f.lower().endswith(".whl")
                ]
                prefix = f"agateon-{tag}-offline-{plat}"
                agate_package.write_dir_tarball(bundle, os.path.join(stage, f"{prefix}.tar.gz"), mtime, arc_prefix=prefix)
                names.append(f"{prefix}.tar.gz")

        sums = "".join(f"{_sha256(os.path.join(stage, n))}  {n}\n" for n in sorted(names))
        _write_text(os.path.join(stage, "SHA256SUMS"), sums)
        names.append("SHA256SUMS")
        notes = extract_notes(changelog, tag, wheels=wheels)

        # 全部成功：落盘（outdir 此前不存在或为空目录）
        os.makedirs(outdir, exist_ok=True)
        for n in names:
            dst = os.path.join(outdir, n)
            shutil.move(os.path.join(stage, n), dst)
            os.chmod(dst, 0o644)  # mkstemp 产物为 0600
        _write_text(notes_out, notes)
        return sorted(names)
    finally:
        shutil.rmtree(work, ignore_errors=True)  # 仅本次 mkdtemp 创建的暂存目录


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_changelog():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "CHANGELOG.md")


def _cmd_notes(args):
    try:
        with open(args.changelog or _default_changelog(), "rb") as fh:
            text = fh.read().decode("utf-8")
        notes = extract_notes(text, args.tag)
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    except (OSError, NotesError) as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 1
    _write_text(args.out, notes)
    return 0


def _cmd_is_prerelease(args):
    try:
        _strict, pre = agate_package.parse_release_ref(args.tag)
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    return 0 if pre else 1


def _cmd_build(args):
    platforms = tuple(p for p in args.platforms.split(",") if p) if args.platforms else DEFAULT_PLATFORMS
    if not platforms:
        sys.stderr.write("agate-release: --platforms 为空\n")
        return 2
    try:
        names = build(
            args.tag, args.repo, args.outdir, args.notes_out,
            expect_sha=args.expect_sha, platforms=platforms, skip_offline=args.skip_offline,
        )
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    except (ReleaseError, agate_package.PackageError, OSError) as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 1
    for n in names:
        print(n)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agate-release", description="agate Release 构建 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("boundary", help="打印本体包边界规则")
    sub.add_parser("pyyaml-pin", help="打印 pyyaml 固定版本")
    p_notes = sub.add_parser("notes", help="从 CHANGELOG 提取发布说明")
    p_notes.add_argument("--tag", required=True)
    p_notes.add_argument("--changelog", default=None)
    p_notes.add_argument("--out", required=True)
    p_pre = sub.add_parser("is-prerelease", help="退出码：0 预发布 / 1 正式 / 2 非法")
    p_pre.add_argument("tag")
    p_build = sub.add_parser("build", help="确定性构建发布资产")
    p_build.add_argument("--tag", required=True)
    p_build.add_argument("--repo", required=True)
    p_build.add_argument("--outdir", required=True)
    p_build.add_argument("--notes-out", required=True)
    p_build.add_argument("--expect-sha", default=None)
    p_build.add_argument("--platforms", default=None)
    p_build.add_argument("--skip-offline", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "boundary":
        print("\n".join(agate_package.boundary_lines()))
        return 0
    if args.cmd == "pyyaml-pin":
        print(agate_package.PYYAML_PIN)
        return 0
    if args.cmd == "notes":
        return _cmd_notes(args)
    if args.cmd == "is-prerelease":
        return _cmd_is_prerelease(args)
    return _cmd_build(args)


if __name__ == "__main__":
    sys.exit(main())
