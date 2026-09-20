# tests/unit/test_agate_release.py — Release CLI agate-release.py（TAG0037 P3 组 A，批 C1-release-cli）
# 被测：agate/scripts/agate-release.py（P4 批 C1 实现；当前不存在 → B 类红灯：加载抛 ModuleNotFoundError）。
# 覆盖：BDD-13 ⑤（资产名口径，T-13）/ 14（notes 提取 + 预发布回落）/ 15（本体 tarball 与 tag 一致、成员安全、确定性）/
#       16（offline tarball 可被 install-offline 直接消费）；T-9（notes）/ T-18（CI/本地一致、--expect-sha）/ T-22（is-prerelease
#       退出码）；D-13（不写字节码）；cso F-2/F-3/F-4/F-10 的 CLI 侧。
# 共享夹具：agate/tests/helpers_tag_repo.py（合成 tag 仓库；pip 用 PATH shim，不联网）。全部产物在 tmp_path 内，不触碰真实
# ~/.agate；不推 tag、不发 Release（BDD-20 的真实 CI 实跑属 P5/P6，不在 P3 写）。
# 资产口径（主 Agent 裁决 C-1，P2 T-13）：3 个 tarball 名 ⊆ 资产集合 且 SHA256SUMS ∈ 资产集合；本文件对合成 tag 的
# outdir 断言"恰为这 4 个"——因为 workflow 以 dist/* 上传，outdir 里的任何多余文件都会变成公开资产。

import json
import re
import sys
import tarfile
from types import SimpleNamespace

import pytest

import helpers_tag_repo as H

PLATFORMS = ("linux-x86_64", "windows-x86_64")
_POSIX_ONLY = pytest.mark.skipif(not H.posix_shim_supported(), reason="pip PATH shim 仅 POSIX（Windows CI 只跑 windows_smoke）")


def _cli(agate_scripts):
    path = agate_scripts / "agate-release.py"
    if not path.is_file():
        raise ModuleNotFoundError("No module named 'agate_release' (被测模块未实现: agate-release.py)")
    return path


def _run(agate_scripts, args, home, shim=None, log=None, extra_env=None, cwd=None, script=None):
    env = H.tool_env(home, shim_dir=shim, pip_log=log, extra=extra_env)
    return H.run_tool([sys.executable, script or _cli(agate_scripts), *args], env=env, cwd=cwd)


def _asset_names(tag):
    return {
        f"agateon-{tag}.tar.gz",
        f"agateon-{tag}-offline-linux-x86_64.tar.gz",
        f"agateon-{tag}-offline-windows-x86_64.tar.gz",
        "SHA256SUMS",
    }


def _kv(stdout):
    out = {}
    for line in stdout.splitlines():
        if "=" in line:
            k, _sep, v = line.partition("=")
            out[k] = v
    return out


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


@pytest.fixture(scope="module")
def pack_src(tmp_path_factory, synth):
    """build / pack 用的独立 bare 副本（旧 packer 会 worktree add，不污染共享夹具）。"""
    return H.clone_bare(synth.bare, tmp_path_factory.mktemp("release_src") / "src.git")


@pytest.fixture(scope="module")
def shim(tmp_path_factory):
    if not H.posix_shim_supported():
        pytest.skip("pip PATH shim 仅 POSIX")
    base = tmp_path_factory.mktemp("release_shim")
    return SimpleNamespace(dir=H.make_pip_shim(base / "bin"), log=base / "pip.log", home=base / "home")


def _build(agate_scripts, pack_src, shim, tmp_path_factory, tag, name, extra_args=(), skip_offline=False):
    out = tmp_path_factory.mktemp(name) / "dist"
    notes = out.parent / "notes.md"
    args = ["build", "--tag", tag, "--repo", str(pack_src), "--outdir", str(out), "--notes-out", str(notes), *extra_args]
    if skip_offline:
        args.append("--skip-offline")
    try:
        proc = _run(agate_scripts, args, shim.home, shim=shim.dir, log=shim.log)
    except ModuleNotFoundError as exc:  # 被测脚本未实现：留给用例断言处抛出（模块级 fixture 内不抛，避免变成 ERROR）
        return SimpleNamespace(proc=None, error=exc, out=out, notes=notes, tag=tag)
    return SimpleNamespace(proc=proc, error=None, out=out, notes=notes, tag=tag)


def _proc(build):
    """取 build 的子进程结果；被测脚本未实现时在此抛 ModuleNotFoundError（B 类红灯），而不是 AttributeError。"""
    if build.error is not None:
        raise build.error
    return build.proc


def _ok(build):
    if build.error is not None:
        raise build.error
    assert build.proc.returncode == 0, f"build 应成功: rc={build.proc.returncode} stderr={build.proc.stderr}"
    return build


@pytest.fixture(scope="module")
def main_build(agate_scripts, pack_src, shim, tmp_path_factory):
    """MAIN_TAG 的完整构建（含两平台 offline）。"""
    return _build(agate_scripts, pack_src, shim, tmp_path_factory, H.MAIN_TAG, "build_main")


@pytest.fixture(scope="module")
def main_build_again(agate_scripts, pack_src, shim, tmp_path_factory):
    """同 tag 第二次构建（确定性对比用）。"""
    return _build(agate_scripts, pack_src, shim, tmp_path_factory, H.MAIN_TAG, "build_main_again")


@pytest.fixture(scope="module")
def pre_build(agate_scripts, pack_src, shim, tmp_path_factory):
    """预发布测试 tag 的构建（只打 linux offline 以省时；CHANGELOG 仅 [Unreleased] + [0.72.0] → 走回落）。"""
    return _build(
        agate_scripts, pack_src, shim, tmp_path_factory, H.PRERELEASE_TAG, "build_pre", extra_args=("--platforms", "linux-x86_64")
    )


def _members(path):
    with tarfile.open(path, "r:gz", encoding="utf-8") as tf:
        return tf.getmembers()


# ---------------------------------------------------------------------------
# 1. extract_notes（库层，可在无 CI 下被直接调用）与 CLI 小命令
# ---------------------------------------------------------------------------


@pytest.mark.windows_smoke
def test_bdd_14_extract_notes_is_directly_callable_without_ci(agate_scripts):
    """BDD-14 Given：notes 提取逻辑可被测试直接调用（不只存在于 workflow 内联 shell）。"""
    mod = H.load_project_module(agate_scripts, "agate-release.py", "agate_release")
    assert callable(mod.extract_notes)
    text = H.changelog_text([("Unreleased", H.SENT_UNRELEASED), ("0.73.0", H.SENT_0_73_0), ("0.72.0", H.SENT_0_72_0)]).decode()
    body = mod.extract_notes(text, "v0.73.0")
    assert isinstance(body, str) and H.SENT_0_73_0 in body
    assert H.SENT_0_72_0 not in body
    text_b = H.changelog_text([("Unreleased", H.SENT_UNRELEASED), ("0.72.0", H.SENT_0_72_0)]).decode()
    fallback = mod.extract_notes(text_b, "v0.73.0-tagtest.1")
    assert H.SENT_UNRELEASED in fallback and H.SENT_0_72_0 not in fallback


def _notes(agate_scripts, tmp_path, changelog_text_bytes, tag, name="CHANGELOG.md"):
    cl = tmp_path / name
    cl.write_bytes(changelog_text_bytes)
    out = tmp_path / "notes-out.md"
    proc = _run(agate_scripts, ["notes", "--tag", tag, "--changelog", str(cl), "--out", str(out)], tmp_path / "home")
    return proc, out


_FIX_A = [("Unreleased", H.SENT_UNRELEASED), ("0.73.0", H.SENT_0_73_0), ("0.72.0", H.SENT_0_72_0)]
_FIX_B = [("Unreleased", H.SENT_UNRELEASED), ("0.72.0", H.SENT_0_72_0)]


def test_bdd_14_1_formal_tag_extracts_exactly_its_section(agate_scripts, tmp_path):
    """BDD-14 ①③：正式 tag 取 [0.73.0] 段；不含 [0.72.0] / [Unreleased] 内容；头部含下载指引与整仓 Source code 说明；
    Keep-a-Changelog 尾部链接定义行不入 notes。"""
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(_FIX_A), "v0.73.0")
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert H.SENT_0_73_0 in text
    assert H.SENT_0_72_0 not in text and H.SENT_UNRELEASED not in text
    assert "agateon-v0.73.0.tar.gz" in text
    assert "Source code" in text and "整仓" in text
    assert not re.search(r"^\[[^\]]+\]: https?://", text, re.M), "链接定义行不应进入 notes"
    assert not text.splitlines()[0].startswith("预发布测试"), "正式 tag 不带预发布标注"


def test_bdd_14_2_formal_tag_missing_section_fails_closed_without_output(agate_scripts, tmp_path):
    """BDD-14 ②：正式 tag 缺段 → exit 1，stderr 指明缺段，且不产生任何输出文件（不得创建空 notes 的 Release）。"""
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(_FIX_A), "v0.99.0")
    assert proc.returncode == 1
    assert "0.99.0" in proc.stderr
    assert not out.exists()


def test_bdd_14_2b_formal_tag_with_empty_section_body_also_fails_closed(agate_scripts, tmp_path):
    empty = b"# Changelog\n\n## [Unreleased]\n\n- x\n\n## [0.73.0] - 2026-09-20\n\n\n## [0.72.0]\n\n- y\n"
    proc, out = _notes(agate_scripts, tmp_path, empty, "v0.73.0")
    assert proc.returncode == 1
    assert not out.exists()


def test_bdd_14_3_real_changelog_v0_72_0(agate_scripts, tmp_path):
    """BDD-14 ③：对**真实** CHANGELOG 提取 v0.72.0：输出非空、含该段正文、不含下一段标题；头部含推荐下载说明。"""
    real = (H.REPO_ROOT / "CHANGELOG.md").read_bytes()
    proc, out = _notes(agate_scripts, tmp_path, real, "v0.72.0")
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert text.strip()
    real_text = real.decode("utf-8")
    m = re.search(r"^## \[0\.72\.0\][^\n]*\n(.*?)(?=^## \[)", real_text, re.S | re.M)
    assert m, "真实 CHANGELOG 应含 [0.72.0] 段"
    first_body_line = next(ln for ln in m.group(1).splitlines() if ln.strip())
    assert first_body_line in text
    nxt = re.search(r"^## \[0\.72\.0\][^\n]*\n.*?^(## \[[^\n]*)", real_text, re.S | re.M).group(1)
    assert nxt not in text
    assert "agateon-v0.72.0.tar.gz" in text


@pytest.mark.parametrize(
    "fixture,sections,expected,unexpected",
    [
        ("A", _FIX_A, H.SENT_0_73_0, H.SENT_0_72_0),
        ("B", _FIX_B, H.SENT_UNRELEASED, H.SENT_0_72_0),
    ],
    ids=["bdd14-4-A-has-0.73.0-section", "bdd14-4-B-only-unreleased-falls-back"],
)
def test_bdd_14_4_prerelease_tag_rule_and_fallback(agate_scripts, tmp_path, fixture, sections, expected, unexpected):
    """BDD-14 ④（[参数化]）：预发布 tag 取去后缀版本段；夹具 B（仅 [Unreleased]）回落取 [Unreleased]；首行为预发布标注；
    不含 [0.72.0] 段内容。"""
    tag = "v0.73.0-tagtest.1"
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(sections), tag)
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    first = text.splitlines()[0]
    assert "预发布测试" in first and tag in first and "非正式发布" in first, first
    assert expected in text and unexpected not in text


def test_bdd_14_4_prerelease_without_any_usable_section_fails_closed(agate_scripts, tmp_path):
    """回落规则只对预发布 tag 生效，且回落后仍缺（无 [0.73.0] 也无 [Unreleased]）→ exit 1 且不写文件。"""
    only_old = b"# Changelog\n\n## [0.72.0] - 2026-09-01\n\n- old\n"
    proc, out = _notes(agate_scripts, tmp_path, only_old, "v0.73.0-tagtest.1")
    assert proc.returncode == 1
    assert not out.exists()


def test_bdd_14_formal_tag_never_falls_back_to_unreleased(agate_scripts, tmp_path):
    """回落规则不得泄漏到正式 tag：夹具 B 上提取正式 v0.73.0 → exit 1（P8 前的 CHANGELOG 状态）。"""
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(_FIX_B), "v0.73.0")
    assert proc.returncode == 1
    assert not out.exists()


@pytest.mark.parametrize("tag", ["v0.73.0", "v0.73.0-tagtest.1"])
def test_t9_notes_header_states_integrity_limits(agate_scripts, tmp_path, tag):
    """T-9 / cso F-4：notes 头部如实标注 SHA256SUMS 只防下载损坏、不认证发布者；offline 面向 Python 3.11。"""
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(_FIX_A), tag)
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "SHA256SUMS" in text and "不认证发布者" in text and "损坏" in text
    assert "3.11" in text


@pytest.mark.parametrize("tag", ["v1.2", "vfoo", "v1.2.3-a..b"])
def test_t17_notes_rejects_invalid_tag_without_output(agate_scripts, tmp_path, tag):
    proc, out = _notes(agate_scripts, tmp_path, H.changelog_text(_FIX_A), tag)
    assert proc.returncode != 0
    assert not out.exists()


@pytest.mark.parametrize(
    "tag,rc",
    [("v0.73.0", 1), ("v0.73.0-tagtest.1", 0), ("v1.2.3-rc.1", 0), ("v1.2", 2), ("vfoo", 2), ("v1.2.3\n", 2), ("", 2)],
)
def test_t22_is_prerelease_exit_codes(agate_scripts, tmp_path, tag, rc):
    """T-22 / cso F-10：正式 exit 1、预发布 exit 0、非法 exit 2（workflow 的 case 三分支依赖这三个值）。"""
    proc = _run(agate_scripts, ["is-prerelease", tag], tmp_path / "home")
    assert proc.returncode == rc, (tag, proc.returncode, proc.stderr)


def test_boundary_subcommand_prints_library_lines(agate_scripts, tmp_path):
    """D-3：`boundary` 输出 == agate_package.boundary_lines()（UPGRADING 契约块的生成源）。"""
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    proc = _run(agate_scripts, ["boundary"], tmp_path / "home")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == list(pkg.boundary_lines())


def test_pyyaml_pin_subcommand_matches_library_constant(agate_scripts, tmp_path):
    """cso F-2：workflow 与 agate-pack-offline 同源取 PYYAML_PIN。"""
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    proc = _run(agate_scripts, ["pyyaml-pin"], tmp_path / "home")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == pkg.PYYAML_PIN


def test_d13_release_script_sets_dont_write_bytecode_before_agate_imports(agate_scripts):
    """D-13：入口最顶部（先于任何 `import agate_*`）设 sys.dont_write_bytecode = True。"""
    import ast

    path = _cli(agate_scripts)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assign_line = None
    first_agate_import = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Attribute) and t.attr == "dont_write_bytecode" for t in node.targets
        ):
            assign_line = node.lineno if assign_line is None else min(assign_line, node.lineno)
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        if any(n.startswith("agate_") for n in names):
            first_agate_import = node.lineno if first_agate_import is None else min(first_agate_import, node.lineno)
    assert assign_line is not None, "缺 sys.dont_write_bytecode = True"
    assert first_agate_import is None or assign_line < first_agate_import


# ---------------------------------------------------------------------------
# 2. build：资产口径 / 本体 tarball / offline tarball / SHA256SUMS / 确定性
# ---------------------------------------------------------------------------


@_POSIX_ONLY
def test_bdd_13_5_build_produces_exactly_the_documented_assets(main_build):
    """BDD-13 ⑤ / T-13（C-1）：3 个 tarball（本体 + 两平台 offline，名称含 tag 原样）+ SHA256SUMS；outdir 无其它文件
    （workflow 以 dist/* 上传）；notes 文件在 outdir 之外。"""
    _ok(main_build)
    names = {p.name for p in main_build.out.iterdir()}
    assert names == _asset_names(H.MAIN_TAG)
    assert main_build.notes.is_file() and main_build.notes.parent != main_build.out


@_POSIX_ONLY
def test_bdd_15_body_tarball_matches_tag_and_members_are_safe(main_build, synth):
    """BDD-15 ①②③④：文件名精确；解包集合 == F_pkg 且顶层无包裹目录；每个成员字节 == `git show <tag>:<path>`（含 .gitattributes
    eol=crlf 陷阱与二进制 CRLF）；所有成员为普通文件 / 目录，无绝对 / '..' / 链接 / 设备。"""
    _ok(main_build)
    tar_path = main_build.out / f"agateon-{H.MAIN_TAG}.tar.gz"
    assert tar_path.is_file()
    with tarfile.open(tar_path, "r:gz", encoding="utf-8") as tf:
        members = tf.getmembers()
        files = {m.name: m for m in members if m.isreg()}
        for m in members:
            assert m.isreg() or m.isdir(), (m.name, m.type)
            assert not (m.issym() or m.islnk() or m.isdev() or m.isfifo()), m.name
            assert not m.name.startswith(("/", "./")) and ".." not in m.name.split("/"), m.name
        assert set(files) == synth.expected_package(H.MAIN_TAG)
        assert {n.split("/")[0] for n in files} == H.ORACLE_TOP_LEVEL
        for name, m in files.items():
            assert tf.extractfile(m).read() == synth.blob(H.MAIN_TAG, name), name
        assert files["agate/scripts/run.sh"].mode & 0o777 == 0o755


@_POSIX_ONLY
def test_bdd_15_and_s11_tarball_metadata_is_deterministic(main_build, synth):
    """S-11 / R-5：mtime == tag 提交时间、uid/gid 归零、gzip 头无文件名无时间。"""
    _ok(main_build)
    tar_path = main_build.out / f"agateon-{H.MAIN_TAG}.tar.gz"
    for m in _members(tar_path):
        assert m.mtime == synth.commit_time(H.MAIN_TAG), m.name
        assert m.uid == 0 and m.gid == 0, m.name
    head = tar_path.read_bytes()[:10]
    assert head[3] & 0x08 == 0 and head[4:8] == b"\x00\x00\x00\x00"


@_POSIX_ONLY
def test_t18_two_builds_of_same_tag_have_identical_hashes(main_build, main_build_again):
    """T-18 / BDD-20 ③ 的本地对应：同 tag 同 Python 次版本两次构建，所有资产 SHA256 相同（含 offline，wheel 由同一 shim 产生）。"""
    _ok(main_build)
    _ok(main_build_again)
    for name in sorted(_asset_names(H.MAIN_TAG)):
        assert H.sha256_of(main_build.out / name) == H.sha256_of(main_build_again.out / name), name


@_POSIX_ONLY
def test_s11_sha256sums_is_verifiable_and_sorted(main_build):
    """S-11：SHA256SUMS 每行 `<hex>␣␣<name>`，按名字排序，覆盖除自身外的全部资产，哈希正确（可被 sha256sum -c 校验）。"""
    _ok(main_build)
    lines = (main_build.out / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    parsed = []
    for line in lines:
        m = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        assert m, f"格式不符: {line!r}"
        parsed.append((m.group(2), m.group(1)))
    names = [n for n, _h in parsed]
    assert names == sorted(names)
    assert set(names) == _asset_names(H.MAIN_TAG) - {"SHA256SUMS"}
    for name, digest in parsed:
        assert H.sha256_of(main_build.out / name) == digest, name


@_POSIX_ONLY
@pytest.mark.parametrize("platform", PLATFORMS)
def test_bdd_16_offline_tarball_layout_and_manifest(main_build, synth, tmp_path, platform):
    """BDD-16（[参数化]：每平台一个子场景）：解包目录（tag 原样的包裹目录）含 manifest.json + agate/（本体，非整仓）+ wheels/ +
    登记根文件；manifest 的 version / platform / files / 组件 sha256 正确。"""
    _ok(main_build)
    tar_path = main_build.out / f"agateon-{H.MAIN_TAG}-offline-{platform}.tar.gz"
    prefix = f"agateon-{H.MAIN_TAG}-offline-{platform}"
    with tarfile.open(tar_path, "r:gz", encoding="utf-8") as tf:
        for m in tf.getmembers():
            assert m.isreg() or m.isdir(), (m.name, m.type)
            assert m.name == prefix or m.name.startswith(prefix + "/"), f"应有 {prefix}/ 包裹目录: {m.name}"
            assert ".." not in m.name.split("/") and not m.name.startswith("/"), m.name
    bundle = H.extract_tar(tar_path, tmp_path / "x") / prefix
    assert {p.name for p in bundle.iterdir()} == {"agate", "wheels", "manifest.json", *H.ORACLE_TOP_LEVEL - {"agate"}}
    H.assert_real_bundle_layout(bundle)
    assert (bundle / "agate" / "scripts" / "agate-install.py").is_file()
    assert not (bundle / "agate" / "tests").exists()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == H.MAIN_TAG and manifest["platform"] == platform
    assert manifest["files"] == sorted(manifest["files"])
    assert set(manifest["files"]) == synth.expected_package(H.MAIN_TAG)
    assert any(w.name.lower().startswith("pyyaml-") for w in (bundle / "wheels").iterdir())
    for name, comp in manifest["components"].items():
        assert comp["sha256"] == H.expected_component_sha256(bundle / comp["path"]), name


@_POSIX_ONLY
def test_bdd_16_offline_tarball_install_and_resolve_end_to_end(main_build, synth, shim, tmp_path):
    """BDD-16：offline tarball 解包后，以**包内**入口 install-offline.py 直接安装（真实内网用法），随后
    agate-resolve.py exit 0；安装态满足契约（文件集合 == F_pkg，无 wheels/manifest.json，无 agate/agate）。"""
    plat = H.host_platform_label()
    if plat is None:
        pytest.skip("本机平台无对应 offline 资产")
    _ok(main_build)
    prefix = f"agateon-{H.MAIN_TAG}-offline-{plat}"
    bundle = H.extract_tar(main_build.out / f"{prefix}.tar.gz", tmp_path / "x") / prefix
    dest = tmp_path / "agate-home"
    env = H.tool_env(tmp_path / "home", shim_dir=shim.dir, pip_log=shim.log)
    proc = H.run_tool(
        [sys.executable, bundle / "agate" / "scripts" / "install-offline.py", bundle, "--dest-root", dest], env=env
    )
    assert proc.returncode == 0, proc.stderr
    vdir = dest / H.MAIN_TAG
    assert H.file_set(vdir) == synth.expected_package(H.MAIN_TAG)
    assert not (vdir / "wheels").exists() and not (vdir / "manifest.json").exists()
    assert not (vdir / "agate" / "agate").exists()
    res = H.run_tool(
        [sys.executable, dest / "scripts" / "agate-resolve.py"], env=H.tool_env(tmp_path / "home", agate_home=dest), cwd=tmp_path
    )
    assert res.returncode == 0, res.stderr
    kv = _kv(res.stdout)
    assert kv["AGATE_VERSION"] == H.MAIN_TAG
    assert kv["AGATE_ROOT"].replace("\\", "/").endswith(f"/{H.MAIN_TAG}/agate")


@_POSIX_ONLY
def test_bdd_14_and_15_build_notes_for_formal_tag(main_build):
    """BDD-14 / cso F-4：build 产出的 notes 取自该 tag 的 CHANGELOG 段，含 offline wheel 文件名清单，无预发布标注。"""
    _ok(main_build)
    text = main_build.notes.read_text(encoding="utf-8")
    assert H.SENT_0_73_0 in text and H.SENT_0_72_0 not in text and H.SENT_UNRELEASED not in text
    assert "pyyaml-" in text, "notes 应列出 offline 包内 wheel 的文件名与 sha256"
    assert not text.splitlines()[0].startswith("预发布测试")


@_POSIX_ONLY
def test_bdd_13_5_and_20_prerelease_build_uses_tag_verbatim_and_strict_manifest_version(pre_build, synth, tmp_path):
    """BDD-13 ⑤ / BDD-14 ④：预发布 tag——资产名含 tag 原样；notes 首行为预发布标注且回落 [Unreleased]；offline 包内
    manifest.version 恒为严格 v0.73.0，source_ref 为 tag 原样。"""
    _ok(pre_build)
    tag = H.PRERELEASE_TAG
    names = {p.name for p in pre_build.out.iterdir()}
    assert names == {
        f"agateon-{tag}.tar.gz",
        f"agateon-{tag}-offline-linux-x86_64.tar.gz",
        "SHA256SUMS",
    }
    notes = pre_build.notes.read_text(encoding="utf-8")
    assert "预发布测试" in notes.splitlines()[0] and tag in notes.splitlines()[0]
    assert H.SENT_UNRELEASED in notes and H.SENT_0_72_0 not in notes
    prefix = f"agateon-{tag}-offline-linux-x86_64"
    bundle = H.extract_tar(pre_build.out / f"{prefix}.tar.gz", tmp_path / "x") / prefix
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "v0.73.0"
    assert manifest["source_ref"] == tag
    assert set(manifest["files"]) == synth.expected_package(tag)


@_POSIX_ONLY
def test_bdd_15_skip_offline_builds_only_body_and_sums(agate_scripts, pack_src, shim, tmp_path_factory):
    b = _ok(_build(agate_scripts, pack_src, shim, tmp_path_factory, H.MAIN_TAG, "build_skip", skip_offline=True))
    assert {p.name for p in b.out.iterdir()} == {f"agateon-{H.MAIN_TAG}.tar.gz", "SHA256SUMS"}


@_POSIX_ONLY
@pytest.mark.parametrize(
    "case,tag,which,rc",
    [
        ("light-commit-sha", H.MAIN_TAG, "commit", 0),
        ("annotated-tag-object-sha", H.ANNOTATED_TAG, "tagobj", 0),
        ("annotated-commit-sha", H.ANNOTATED_TAG, "commit", 0),
        ("light-wrong-sha", H.MAIN_TAG, "other", 1),
        ("annotated-wrong-sha", H.ANNOTATED_TAG, "other", 1),
    ],
)
def test_t18_expect_sha_covers_lightweight_and_annotated_tags(
    agate_scripts, pack_src, shim, tmp_path_factory, synth, case, tag, which, rc
):
    """T-18 / cso F-3 / eng N-3：两侧都 `^{commit}` 剥壳——轻量 / 附注 tag、传 tag 对象 SHA 与 commit SHA 均判等；SHA 不符
    → exit 1 且不产出任何资产（tag 被移动 / 来源与触发提交不一致）。"""
    sha = {
        "commit": synth.commit_sha(tag),
        "tagobj": synth.tag_object_sha(tag),
        "other": synth.commit_sha(H.OLD_TAG),
    }[which]
    if which == "tagobj":
        assert sha != synth.commit_sha(tag), "夹具前提：附注 tag 的对象 SHA 与 commit SHA 不同"
    b = _build(agate_scripts, pack_src, shim, tmp_path_factory, tag, f"build_sha_{case}", extra_args=("--expect-sha", sha), skip_offline=True)
    assert _proc(b).returncode == rc, _proc(b).stderr
    if rc == 0:
        assert (b.out / f"agateon-{tag}.tar.gz").is_file()
    else:
        assert _proc(b).stderr.strip()
        assert not b.out.exists() or not list(b.out.glob("agateon-*"))
        assert not b.notes.exists()


@_POSIX_ONLY
def test_bdd_14_2_build_fails_closed_for_formal_tag_without_changelog_section(agate_scripts, pack_src, shim, tmp_path_factory):
    """BDD-14 ② 在 build 上的体现：正式 tag v0.49.0 的 CHANGELOG 无 [0.49.0] 段 → exit 1，不产出 notes 文件（不得发出空 notes 的 Release）。"""
    b = _build(agate_scripts, pack_src, shim, tmp_path_factory, H.NEWER_OLD_TAG, "build_nosec", skip_offline=True)
    assert _proc(b).returncode == 1
    assert "0.49.0" in _proc(b).stderr
    assert not b.notes.exists()


@_POSIX_ONLY
@pytest.mark.parametrize("tag", ["v1.2", "vfoo", "v1.2.3-a..b"])
def test_t17_build_rejects_invalid_tag_names(agate_scripts, pack_src, shim, tmp_path_factory, tag):
    b = _build(agate_scripts, pack_src, shim, tmp_path_factory, tag, "build_badtag", skip_offline=True)
    assert _proc(b).returncode != 0
    assert not b.notes.exists()


@_POSIX_ONLY
def test_bdd_24_2_build_of_malformed_tag_fails_without_assets(agate_scripts, pack_src, shim, tmp_path_factory):
    """BDD-24 ②（发布侧）：树内无 agate/scripts/ 的 tag 不得被打成包。"""
    b = _build(agate_scripts, pack_src, shim, tmp_path_factory, H.MALFORMED_TAG, "build_malformed", skip_offline=True)
    assert _proc(b).returncode != 0
    assert "agate/scripts" in _proc(b).stderr
    assert not b.out.exists() or not list(b.out.glob("agateon-*"))


@_POSIX_ONLY
def test_d13_build_from_script_copy_never_writes_bytecode(agate_scripts, pack_src, shim, tmp_path):
    """D-13 / eng B-1：从脚本目录副本运行 build（含 pack 子进程与 pip shim），事后副本内无 __pycache__ / *.pyc——运行不污染
    安装目录。环境不带 PYTHONDONTWRITEBYTECODE，靠脚本自身的 sys.dont_write_bytecode 与子进程 -B。"""
    _cli(agate_scripts)
    copy = H.copy_real_scripts(tmp_path / "scripts-copy")
    out = tmp_path / "dist"
    args = [
        "build",
        "--tag",
        H.MAIN_TAG,
        "--repo",
        str(pack_src),
        "--outdir",
        str(out),
        "--notes-out",
        str(tmp_path / "notes.md"),
        "--platforms",
        "linux-x86_64",
    ]
    proc = _run(agate_scripts, args, tmp_path / "home", shim=shim.dir, log=shim.log, script=copy / "agate-release.py")
    assert proc.returncode == 0, proc.stderr
    leftovers = [str(p) for p in copy.rglob("*") if p.name == "__pycache__" or p.suffix in (".pyc", ".pyo")]
    assert leftovers == []


@_POSIX_ONLY
def test_t18_real_tag_v0_72_0_body_tarball_matches_git_blobs(agate_scripts, shim, tmp_path):
    """T-18（真实历史 tag，不可变证据）：v0.72.0 的本体 tarball 逐成员字节 == `git show v0.72.0:<path>`；153 个成员；
    outdir 仅本体 + SHA256SUMS（--skip-offline，免联网）；正式 tag 的 notes 取自该 tag 内的 CHANGELOG。"""
    have = H.run_git(H.REPO_ROOT, "rev-parse", "--verify", "-q", "refs/tags/v0.72.0", check=False).returncode == 0
    assert have, "需要 tag v0.72.0（CI 的 pytest job 已 fetch-tags）"
    out = tmp_path / "dist"
    notes = tmp_path / "notes.md"
    proc = _run(
        agate_scripts,
        ["build", "--tag", "v0.72.0", "--repo", str(H.REPO_ROOT), "--outdir", str(out), "--notes-out", str(notes), "--skip-offline"],
        shim.home,
        shim=shim.dir,
        log=shim.log,
    )
    assert proc.returncode == 0, proc.stderr
    assert {p.name for p in out.iterdir()} == {"agateon-v0.72.0.tar.gz", "SHA256SUMS"}
    with tarfile.open(out / "agateon-v0.72.0.tar.gz", "r:gz", encoding="utf-8") as tf:
        files = [m for m in tf.getmembers() if m.isreg()]
        assert len(files) == 153
        for m in files:
            assert tf.extractfile(m).read() == H.git_blob(H.REPO_ROOT, "v0.72.0", m.name), m.name
    assert notes.read_text(encoding="utf-8").strip()
