# tests/unit/test_agate_package.py — 本体打包库 agate_package.py（TAG0037 P3 组 A，批 A-package-lib）
# 被测：agate/scripts/agate_package.py（P4 批 A 实现；当前不存在 → 加载抛 ModuleNotFoundError = B 类红灯）。
# 覆盖：BDD-1（常量 / 边界行）/ 2 / 3（①②）/ 15 ④（成员安全）/ 22（库层集合）/ 23 / 24 ②（畸形 tag 库层判定）；
#       T-6（tar 成员安全 + gzip 头）/ T-7（tripwire）/ T-17（表驱动 + 路径硬化）/ T-21（compute_sha256 字节码免疫）/
#       D-13（不写字节码）/ D-14（软链基址规范化守卫，库层）/ D-16（O_EXCL|O_NOFOLLOW 落盘）。
# 共享夹具：agate/tests/helpers_tag_repo.py（合成 tag 仓库 / 独立 oracle）。全部在 tmp_path 内，不触碰真实 ~/.agate。
# 「fixture 自守卫」小节（第 1 节末）是有意应绿的用例，保护共享夹具本身（eng N-1 / T-2）。

import ast
import os
import re
import sys
import tarfile
from pathlib import Path

import pytest

import helpers_tag_repo as H


def _pkg(agate_scripts):
    return H.load_project_module(agate_scripts, "agate_package.py", "agate_package")


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    """会话级合成上游仓库（只读）。"""
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _paths(entries):
    return [e.path for e in entries]


def _symlink_or_skip(target, link):
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("本平台不可创建符号链接")


# ---------------------------------------------------------------------------
# 1. is_packaged 纯函数（BDD-2 / BDD-3：默认拒绝 + 本体内显式排除）
# ---------------------------------------------------------------------------

_PACKED = [
    "agate/scripts/agate-install.py",
    "agate/scripts/agate_common.py",
    "agate/WORKFLOW.md",
    "agate/orchestrator-template.md",
    "agate/phase-cards/P1-requirements.md",
    "agate/rules/phases.yaml",
    "agate/assets/templates/dispatch-prompt.md",
    "agate/AGENTS.md",
    "agate/zz-new.md",  # BDD-3 ②：本体内新增文件自动入包
    "agate/zz-newdir/deep/x.txt",
    "agate/testsuite.md",  # 名字以 tests 开头但不是 tests/ 目录
    "CHANGELOG.md",
    "LICENSE",
    "NOTICES.md",
]
_NOT_PACKED = [
    "agate/tests/unit/test_x.py",
    "agate/tests/conftest.py",
    "agate/Tests/unit/test_x.py",  # casefold 比较
    "agate/TESTS/x.txt",
    "agate/scripts/__pycache__/agate_common.cpython-312.pyc",
    "agate/assets/deep/__pycache__/m.txt",  # 任意层级 __pycache__
    "agate/scripts/stale.pyc",
    "agate/scripts/old.pyo",
    "agate-workspace/tasks/TAG0001-x/P1-requirements.md",
    "docs/reviews/review-1.md",
    "site/index.md",
    "archived/old.md",
    ".github/workflows/ci.yml",
    "HANDOFF-X.md",
    "README.md",
    "README.zh-CN.md",
    "pyproject.toml",
    "SELF-GATE.md",
    "AGENTS.md",  # 根开发者指引（与 agate/AGENTS.md 是两个文件）
    "CLAUDE.md",
    "install.sh",
    ".gitignore",
    ".gitattributes",
    "zz-new/a.md",  # BDD-3 ①：未登记顶层内容默认不入包
    "zz-new.md",
]


@pytest.mark.windows_smoke
@pytest.mark.parametrize("path", _PACKED)
def test_bdd_2_is_packaged_true_for_body_and_registered_root_files(agate_scripts, path):
    """BDD-2 ①③ / BDD-3 ②：本体文件与登记根文件入包。"""
    pkg = _pkg(agate_scripts)
    assert pkg.is_packaged(path) is True


@pytest.mark.parametrize("path", _NOT_PACKED)
def test_bdd_2_is_packaged_false_for_excluded_and_unregistered(agate_scripts, path):
    """BDD-2 ②③ / BDD-3 ①：tests / 字节码 / 维护者产物 / 未登记顶层内容默认拒绝。"""
    pkg = _pkg(agate_scripts)
    assert pkg.is_packaged(path) is False


def test_bdd_1_constants_and_boundary_lines(agate_scripts):
    """BDD-1 (b)(c) / BDD-3 ③ 的库层部分：常量单一来源；目录名固定 agate/；边界行可被渲染进 UPGRADING。"""
    pkg = _pkg(agate_scripts)
    assert pkg.PKG_DIR == "agate"
    assert tuple(pkg.ROOT_FILES) == ("CHANGELOG.md", "LICENSE", "NOTICES.md")
    assert tuple(pkg.HIDDEN_METADATA) == ()
    assert set(pkg.TOP_LEVEL) == H.ORACLE_TOP_LEVEL
    assert re.fullmatch(r"\d+\.\d+\.\d+", pkg.PYYAML_PIN), f"PYYAML_PIN 应为精确版本: {pkg.PYYAML_PIN!r}"
    lines = pkg.boundary_lines()
    assert lines and all(isinstance(x, str) and x.strip() for x in lines)
    assert len(lines) == len(set(lines)), "边界行不得重复"
    assert lines == pkg.boundary_lines(), "boundary_lines 必须确定性"
    kinds = {ln.split()[0] for ln in lines}
    assert kinds <= {"include", "exclude", "root-file"}, kinds
    joined = "\n".join(lines)
    for token in ("agate/", "agate/tests/", "__pycache__", ".pyc", ".pyo", "CHANGELOG.md", "LICENSE", "NOTICES.md"):
        assert token in joined, f"边界行缺 {token}: {lines}"
    for forbidden in ("HANDOFF", "README", "pyproject", "site/", "docs/"):
        assert forbidden not in joined.replace("agate/", ""), f"边界行不应登记 {forbidden}（默认拒绝）"


def test_agate_package_is_stdlib_only_and_never_writes_bytecode(agate_scripts):
    """D-2 / D-13：agate_package 不得 import agate_common / yaml（pyyaml 缺失时安装器仍须可用），且模块顶部设不写字节码。"""
    path = agate_scripts / "agate_package.py"
    if not path.is_file():
        raise ModuleNotFoundError("No module named 'agate_package' (被测模块未实现: agate_package.py)")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "agate_common" not in imported and "yaml" not in imported, imported
    stdlib = getattr(sys, "stdlib_module_names", None)
    if stdlib is not None:
        assert imported <= set(stdlib), f"非 stdlib import: {imported - set(stdlib)}"
    src = path.read_text(encoding="utf-8")
    assert re.search(r"^sys\.dont_write_bytecode\s*=\s*True\s*$", src, re.M), "模块顶部须设 sys.dont_write_bytecode = True"


# --- fixture 自守卫（有意应绿）---


def test_fixture_guard_scripts_to_copy_includes_agate_package():
    """eng N-1：共享夹具拷真实脚本进合成 tag 时必须同时拷 agate_package.py。"""
    assert "agate_package.py" in H.SCRIPTS_TO_COPY
    assert "agate_common.py" in H.SCRIPTS_TO_COPY


def test_fixture_guard_synthetic_repo_shape(synth):
    """夹具自守卫：合成仓库含全部约定 tag / 附注 tag 对象 SHA 不等于 commit SHA / 老 tag 无 .gitattributes / 畸形 tag 无 scripts。"""
    tags = set(H.git_text(synth.bare, "tag", "-l").split())
    assert {H.MAIN_TAG, H.ANNOTATED_TAG, H.PRERELEASE_TAG, H.OLD_TAG, H.NEWER_OLD_TAG, H.NO_NOTICES_TAG, H.MALFORMED_TAG} <= tags
    assert synth.tag_object_sha(H.ANNOTATED_TAG) != synth.commit_sha(H.ANNOTATED_TAG)
    assert synth.tag_object_sha(H.MAIN_TAG) == synth.commit_sha(H.MAIN_TAG)
    assert ".gitattributes" not in synth.files(H.OLD_TAG)
    assert ".gitattributes" in synth.files(H.MAIN_TAG)
    assert not any(p.startswith("agate/scripts/") for p in synth.files(H.MALFORMED_TAG))
    assert "NOTICES.md" not in synth.files(H.NO_NOTICES_TAG)
    main_pkg = synth.expected_package(H.MAIN_TAG)
    assert "agate/scripts/agate-install.py" in main_pkg and "agate/scripts/run.sh" in main_pkg
    assert not any(p.startswith("agate/tests/") or "__pycache__" in p or p.endswith(".pyc") for p in main_pkg)


def test_fixture_guard_legacy_bundle_constructor_and_sentinel(tmp_path, synth):
    """T-2 变异测试的夹具前提：旧行为构造器产出真实 worktree 整仓检出，sentinel 对它必须 AssertionError。"""
    bundle = H.make_legacy_worktree_bundle(tmp_path, synth.bare, H.MAIN_TAG, "linux-x86_64")
    assert (bundle / "agate" / "agate" / "scripts").is_dir(), "旧格式应有 agate/agate/scripts 双层嵌套"
    assert (bundle / "agate" / "agate-workspace").is_dir()
    with pytest.raises(AssertionError):
        H.assert_real_bundle_layout(bundle)


def test_eng_n1_fixtures_that_copy_agate_common_also_copy_agate_package():
    """eng N-1 / P2 §6 T-10：凡把 agate_common.py 拷入合成目录的既有夹具，须同时拷 agate_package.py
    （agate_common 现 `from agate_package import agate_home`，漏拷即 ModuleNotFoundError）。
    红灯说明：这 5 个既有测试文件由 B / E 组在各自批次修改（增拷 agate_package.py）后转绿。"""
    tests_root = Path(__file__).resolve().parents[1]
    fixtures = (
        "unit/test_hook_resolve_entry.py",
        "integration/test_pre_commit_hook.py",
        "unit/test_dispatch_context_warning.py",
        "unit/test_agate_version_install.py",
        "integration/test_version_lifecycle_e2e.py",
    )
    missing = [f for f in fixtures if "agate_package.py" not in (tests_root / f).read_text(encoding="utf-8")]
    assert not missing, f"这些夹具拷 agate_common.py 却没拷 agate_package.py: {missing}"


# ---------------------------------------------------------------------------
# 2. list_package / materialize（BDD-2 / 22 / 24 ②）
# ---------------------------------------------------------------------------


def test_bdd_2_list_package_equals_expected_set_on_synthetic_tag(agate_scripts, synth):
    """BDD-2：合成 tag 上 F_pkg 逐项等于独立 oracle；①必须入包 ②金丝雀排除 ③基线值 ④顶层集合。"""
    pkg = _pkg(agate_scripts)
    entries = pkg.list_package(synth.bare, H.MAIN_TAG)
    paths = _paths(entries)
    assert paths == sorted(paths), "list_package 结果须按路径排序（确定性）"
    fpkg = set(paths)
    assert len(fpkg) == len(paths)
    assert fpkg == synth.expected_package(H.MAIN_TAG)
    # ① 必须入包
    for must in (
        "agate/scripts/agate-install.py",
        "agate/scripts/agate_common.py",
        "agate/WORKFLOW.md",
        "agate/orchestrator-template.md",
        "agate/phase-cards/P1-requirements.md",
        "agate/rules/phases.yaml",
        "agate/assets/templates/dispatch-prompt.md",
    ):
        assert must in fpkg, must
    # ② 金丝雀：维护者产物 / 任务数据 / 字节码
    for p in fpkg:
        assert not p.startswith(("agate-workspace/", "docs/", "site/", "archived/", ".github/")), p
        assert not re.fullmatch(r"HANDOFF-.*\.md", p), p
        assert "__pycache__" not in p.split("/") and not p.endswith((".pyc", ".pyo")), p
    # ③ 基线值
    assert "agate/tests/unit/test_x.py" not in fpkg and not any(p.startswith("agate/tests/") for p in fpkg)
    for must in ("agate/AGENTS.md", "LICENSE", "NOTICES.md", "CHANGELOG.md"):
        assert must in fpkg, must
    for gone in (
        "README.md",
        "README.zh-CN.md",
        "pyproject.toml",
        "SELF-GATE.md",
        "AGENTS.md",
        "CLAUDE.md",
        "install.sh",
        ".gitignore",
        ".gitattributes",
    ):
        assert gone not in fpkg, gone
    # ④ 顶层条目集合 == 登记集合
    assert {p.split("/")[0] for p in fpkg} == H.ORACLE_TOP_LEVEL
    # sha 与 git 一致
    for e in entries:
        assert e.sha == H.git_text(synth.bare, "rev-parse", f"refs/tags/{H.MAIN_TAG}:{e.path}")


@pytest.mark.parametrize(
    "scenario,files,expect_in,expect_out",
    [
        (
            "BDD-3.1 未登记顶层目录",
            {"zz-new/a.md": b"x", "zz-new/deep/b.txt": b"y", "zz-new.md": b"z"},
            set(),
            {"zz-new/a.md", "zz-new/deep/b.txt", "zz-new.md"},
        ),
        (
            "BDD-3.2 agate/ 内新增文件自动入包",
            {"agate/zz-new.md": b"x", "agate/zz-newdir/deep/x.txt": b"y"},
            {"agate/zz-new.md", "agate/zz-newdir/deep/x.txt"},
            set(),
        ),
    ],
    ids=["bdd3-1-unregistered-top-level", "bdd3-2-new-file-under-agate"],
)
def test_bdd_3_default_deny_and_auto_include(agate_scripts, tmp_path, scenario, files, expect_in, expect_out):
    """BDD-3 ①②（[参数化]：每个子场景独立判定）。"""
    pkg = _pkg(agate_scripts)
    base = {
        "agate/AGENTS.md": b"# a\n",
        "agate/tests/t.py": b"# t\n",
        "CHANGELOG.md": b"# c\n",
        "LICENSE": b"MIT\n",
    }
    repo = H.make_custom_tag_repo(tmp_path, {**base, **files})
    fpkg = set(_paths(pkg.list_package(repo.bare, H.MAIN_TAG)))
    assert expect_in <= fpkg, scenario
    assert not (expect_out & fpkg), scenario
    assert fpkg == repo.expected_package(H.MAIN_TAG), scenario


@pytest.mark.parametrize(
    "tag,missing_root",
    [(H.NO_NOTICES_TAG, "NOTICES.md"), (H.OLD_TAG, None)],
    ids=["old-tag-without-notices", "old-tag-without-any-exclusion-config"],
)
def test_bdd_24_historical_tags_only_get_body(agate_scripts, synth, tag, missing_root):
    """BDD-24 ① 库层：早于任何"排除机制文件"的老 tag 同样只得本体（不退回全量）；登记根文件缺失于历史 tag 时容忍。"""
    pkg = _pkg(agate_scripts)
    fpkg = set(_paths(pkg.list_package(synth.bare, tag)))
    assert fpkg == synth.expected_package(tag)
    assert not any(p.startswith(("docs/", "site/", "archived/", "agate-workspace/", "agate/tests/")) for p in fpkg)
    assert not any(re.fullmatch(r"HANDOFF-.*\.md", p) for p in fpkg)
    if missing_root:
        assert missing_root not in fpkg
    assert "agate/scripts/README.md" in fpkg


def test_bdd_24_malformed_tag_without_agate_scripts_is_rejected(agate_scripts, synth):
    """BDD-24 ②（库层）：树内无 agate/scripts/ 的畸形 tag → PackageError，信息指明缺 agate/scripts/。"""
    pkg = _pkg(agate_scripts)
    with pytest.raises(pkg.PackageError) as exc:
        pkg.list_package(synth.bare, H.MALFORMED_TAG)
    assert "agate/scripts" in str(exc.value)


def test_bdd_22_library_set_equals_materialized_directory(agate_scripts, synth, tmp_path):
    """BDD-22（库层）：materialize 落盘的文件集合 == F_pkg，且不含任何维护者产物 / `.git`。"""
    pkg = _pkg(agate_scripts)
    dest = tmp_path / "vX"
    dest.mkdir()
    returned = pkg.materialize(synth.bare, H.MAIN_TAG, dest)
    assert _paths(returned) == _paths(pkg.list_package(synth.bare, H.MAIN_TAG))
    on_disk = H.file_set(dest, ignore_bytecode=False)
    assert on_disk == synth.expected_package(H.MAIN_TAG)
    for gone in ("agate-workspace", "docs", "site", "archived", ".github", ".git"):
        assert not (dest / gone).exists(), gone
    assert not list(dest.glob("HANDOFF-*.md"))


def test_bdd_15_materialize_blob_bytes_exact_and_exec_bit(agate_scripts, synth, tmp_path):
    """BDD-15 ③（库层）：落盘字节 == git blob 字节；exec 位保留（POSIX）。"""
    pkg = _pkg(agate_scripts)
    dest = tmp_path / "v"
    dest.mkdir()
    pkg.materialize(synth.bare, H.MAIN_TAG, dest)
    authored = synth.files(H.MAIN_TAG)
    for rel in synth.expected_package(H.MAIN_TAG):
        data = (dest / rel).read_bytes()
        assert data == synth.blob(H.MAIN_TAG, rel), rel
        assert data == authored[rel], rel
    assert (dest / "agate" / "data.bin").read_bytes().count(b"\r\n") > 0, "二进制 blob 的 CRLF 必须原样保留"
    if sys.platform != "win32":
        assert os.stat(dest / "agate" / "scripts" / "run.sh").st_mode & 0o111
        assert not os.stat(dest / "agate" / "AGENTS.md").st_mode & 0o111


def test_bdd_15_materialize_ignores_autocrlf_and_eol_attributes(agate_scripts, synth, tmp_path, monkeypatch):
    """BDD-15 ③：强制 core.autocrlf=true（Windows 默认）且 tag 内带 `*.md text eol=crlf` 属性时，输出仍是 LF blob 字节
    （候选 B `git archive` 在此条件下输出 CRLF，是本方案的选择理由 E-2）。"""
    pkg = _pkg(agate_scripts)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.autocrlf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    dest = tmp_path / "v"
    dest.mkdir()
    pkg.materialize(synth.bare, H.MAIN_TAG, dest)
    wf = (dest / "agate" / "WORKFLOW.md").read_bytes()
    assert wf == synth.files(H.MAIN_TAG)["agate/WORKFLOW.md"]
    assert b"\r" not in wf


def test_d16_materialize_refuses_existing_files_and_never_follows_symlinks(agate_scripts, synth, tmp_path):
    """D-16：逐文件 O_EXCL|O_NOFOLLOW 创建——目的地已有同名文件 / 预置软链时报错，且软链目标（包外文件）不被写入。"""
    pkg = _pkg(agate_scripts)
    dest = tmp_path / "v"
    dest.mkdir()
    (dest / "LICENSE").write_text("pre-existing\n", encoding="utf-8")
    with pytest.raises((FileExistsError, OSError, pkg.PackageError)):
        pkg.materialize(synth.bare, H.MAIN_TAG, dest)
    assert (dest / "LICENSE").read_text(encoding="utf-8") == "pre-existing\n"

    if sys.platform == "win32":
        return
    outside = tmp_path / "outside.txt"
    outside.write_text("do-not-touch\n", encoding="utf-8")
    dest2 = tmp_path / "v2"
    dest2.mkdir()
    os.symlink(str(outside), str(dest2 / "CHANGELOG.md"))
    with pytest.raises((FileExistsError, OSError, pkg.PackageError)):
        pkg.materialize(synth.bare, H.MAIN_TAG, dest2)
    assert outside.read_text(encoding="utf-8") == "do-not-touch\n"


# ---------------------------------------------------------------------------
# 3. 路径硬化（T-17 / D-16 / BDD-15 ④ 的入包侧防线）
# ---------------------------------------------------------------------------

_BAD_MEMBERS = [
    ("dot-git-dir", {"agate/.git/config": b"x"}),
    ("dot-GIT-uppercase", {"agate/.GIT/y": b"x"}),
    ("dot-GiT-mixed-file", {"agate/sub/.GiT": b"x"}),
    ("gitmodules", {"agate/sub/.gitmodules": b"x"}),
    ("colon", {"agate/a:b": b"x"}),
    ("trailing-space", {"agate/tr ": b"x"}),
    ("trailing-dot", {"agate/dot.": b"x"}),
    ("control-char", {"agate/a\x01b": b"x"}),
    ("backslash", {"agate/a\\b": b"x"}),
    ("dotdot-segment", {"agate/../z": b"x"}),
    ("case-collision", {"agate/Foo.md": b"1", "agate/foo.md": b"2"}),
    ("non-utf8-name", {b"agate/\xffbad": b"x"}),
    ("symlink-member", {"agate/lnk": H.TreeEntry(b"target", "120000")}),
    ("submodule-member", {"agate/subm": H.TreeEntry(b"1" * 40, "160000")}),
    ("root-file-is-symlink", {"LICENSE": H.TreeEntry(b"agate/AGENTS.md", "120000")}),
]


@pytest.mark.parametrize("files", [f for _n, f in _BAD_MEMBERS], ids=[n for n, _f in _BAD_MEMBERS])
def test_t17_list_package_rejects_hostile_members(agate_scripts, tmp_path, files):
    """T-17 / D-16：入包区内的 .git* 分量 / ':' / 尾随空格或点 / 控制字符 / 反斜杠 / '..' / 大小写冲突 / 非 UTF-8 /
    软链 / 子模块 → PackageError（整个包判失败，而不是静默跳过）。"""
    pkg = _pkg(agate_scripts)
    repo = H.make_custom_tag_repo(tmp_path, {"agate/AGENTS.md": b"# a\n", "LICENSE": b"MIT\n", **files})
    with pytest.raises(pkg.PackageError):
        pkg.list_package(repo.bare, H.MAIN_TAG)


def test_t17_hostile_names_outside_package_region_are_ignored(agate_scripts, tmp_path):
    """T-17（不误伤）：同样的怪名字只在包区外（docs/ site/ …）时不影响打包，也不入包。"""
    pkg = _pkg(agate_scripts)
    files = {
        "agate/AGENTS.md": b"# a\n",
        "docs/.git/config": b"x",
        "site/a:b": b"x",
        "archived/tr ": b"x",
        "docs/lnk": H.TreeEntry(b"target", "120000"),
        "docs/subm": H.TreeEntry(b"1" * 40, "160000"),
    }
    repo = H.make_custom_tag_repo(tmp_path, files)
    assert set(_paths(pkg.list_package(repo.bare, H.MAIN_TAG))) == {"agate/AGENTS.md", "agate/scripts/README.md"}


def test_t17_tests_directory_excluded_case_insensitively(agate_scripts, tmp_path):
    """T-17：`agate/Tests/`、`agate/TESTS/` 与 `agate/tests/` 同样排除；`agate/testsuite.md` 不误伤。"""
    pkg = _pkg(agate_scripts)
    files = {
        "agate/AGENTS.md": b"# a\n",
        "agate/tests/a.py": b"x",
        "agate/Tests/b.py": b"x",
        "agate/TESTS/c.py": b"x",
        "agate/testsuite.md": b"keep\n",
    }
    repo = H.make_custom_tag_repo(tmp_path, files)
    fpkg = set(_paths(pkg.list_package(repo.bare, H.MAIN_TAG)))
    assert fpkg == {"agate/AGENTS.md", "agate/scripts/README.md", "agate/testsuite.md"}


# ---------------------------------------------------------------------------
# 4. parse_release_ref / is_strict_version（T-17 表驱动，BDD-13 ⑤ / cso F-9）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("v0.73.0", ("v0.73.0", False)),
        ("v0.73.0-tagtest.1", ("v0.73.0", True)),
        ("v1.2.3-rc.1", ("v1.2.3", True)),
        ("v10.20.30-0", ("v10.20.30", True)),
    ],
)
def test_t17_parse_release_ref_accepts(agate_scripts, tag, expected):
    pkg = _pkg(agate_scripts)
    assert tuple(pkg.parse_release_ref(tag)) == expected


@pytest.mark.parametrize(
    "tag",
    [
        "v1.2.3\n",  # `$` 会放过换行，fullmatch 不放过
        "v١.٢.٣",  # Unicode 数字（re.ASCII）
        "v1.2",
        "vfoo",
        "v1.2.3-",
        "v1.2.3-a..b",
        "v1.2.3-.a",
        "v1.2.3-a/b",
        "v1.2.3 ",
        " v1.2.3",
        "1.2.3",
        "",
        "v1.2.3-a\nb",
    ],
)
def test_t17_parse_release_ref_rejects(agate_scripts, tag):
    pkg = _pkg(agate_scripts)
    with pytest.raises(ValueError):
        pkg.parse_release_ref(tag)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("v0.73.0", True),
        ("v10.0.1", True),
        ("v0.73.0-tagtest.1", False),
        ("v1.2.3\n", False),
        ("v١.٢.٣", False),
        ("0.73.0", False),
        ("v1.2", False),
        ("", False),
    ],
)
def test_t17_is_strict_version(agate_scripts, value, expected):
    pkg = _pkg(agate_scripts)
    assert pkg.is_strict_version(value) is expected


# ---------------------------------------------------------------------------
# 5. commit_mtime / write_dir_tarball（T-6 / BDD-15 ④ / S-11）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", [H.MAIN_TAG, H.ANNOTATED_TAG], ids=["lightweight", "annotated"])
def test_s11_commit_mtime_dereferences_tag(agate_scripts, synth, tag):
    """commit_mtime 取 tag 指向的**提交**时间（附注 tag 也剥壳），用于确定性打包。"""
    pkg = _pkg(agate_scripts)
    assert pkg.commit_mtime(synth.bare, tag) == synth.commit_time(tag)


def _materialized(pkg, synth, tmp_path, name="src"):
    dest = tmp_path / name
    dest.mkdir()
    pkg.materialize(synth.bare, H.MAIN_TAG, dest)
    return dest


def test_t6_tarball_members_are_safe_regular_and_deterministic_metadata(agate_scripts, synth, tmp_path):
    """T-6 / BDD-15 ④②③：成员全为普通文件；无绝对 / '..' / 链接 / 设备；顶层无包裹目录；排序；mtime / uid / gid 归一；
    内容 == git blob；模式归一 0644 / 0755。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    (src / "agate" / "scripts" / "__pycache__").mkdir()
    (src / "agate" / "scripts" / "__pycache__" / "junk.cpython-312.pyc").write_bytes(b"\x00")
    out = tmp_path / "body.tar.gz"
    mtime = 1_700_123_456
    pkg.write_dir_tarball(src, out, mtime)
    with tarfile.open(out, "r:gz", encoding="utf-8") as tf:
        members = tf.getmembers()
        files = [m for m in members if m.isreg()]
        for m in members:
            assert m.isreg() or m.isdir(), f"非法成员类型: {m.name} type={m.type!r}"
            assert not (m.issym() or m.islnk() or m.isdev() or m.isfifo()), m.name
            assert not m.name.startswith(("/", "./")) and ".." not in m.name.split("/") and "\\" not in m.name, m.name
            assert m.mtime == mtime, m.name
            assert m.uid == 0 and m.gid == 0 and not m.uname and not m.gname, m.name
        names = [m.name for m in files]
        assert names == sorted(names), "成员须按路径排序"
        assert set(names) == synth.expected_package(H.MAIN_TAG), "字节码不入包，集合 == F_pkg"
        assert {n.split("/")[0] for n in names} == H.ORACLE_TOP_LEVEL, "顶层无包裹目录（解压即得契约形态）"
        for m in files:
            assert tf.extractfile(m).read() == synth.blob(H.MAIN_TAG, m.name), m.name
            assert (m.mode & 0o777) in (0o644, 0o755), (m.name, oct(m.mode))
        run_sh = next(m for m in files if m.name == "agate/scripts/run.sh")
        assert run_sh.mode & 0o777 == 0o755


def test_t6_tarball_extracts_to_contract_shape(agate_scripts, synth, tmp_path):
    """BDD-15 ②：`tar -xzf ... -C <空目录>` 得契约形态（agate/ + 登记根文件），与源目录逐文件相同。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    out = tmp_path / "body.tar.gz"
    pkg.write_dir_tarball(src, out, 1_700_000_000)
    dest = H.extract_tar(out, tmp_path / "unpacked")
    assert H.snapshot_tree(dest) == H.snapshot_tree(src)
    assert {p.name for p in dest.iterdir()} == H.ORACLE_TOP_LEVEL


def test_t6_tarball_arc_prefix_wraps_every_member(agate_scripts, synth, tmp_path):
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    out = tmp_path / "wrapped.tar.gz"
    pkg.write_dir_tarball(src, out, 1_700_000_000, arc_prefix="agateon-v0.73.0-offline-x")
    with tarfile.open(out, "r:gz", encoding="utf-8") as tf:
        names = tf.getnames()
    assert names and all(n == "agateon-v0.73.0-offline-x" or n.startswith("agateon-v0.73.0-offline-x/") for n in names)


def test_s11_tarball_is_byte_deterministic_across_rebuilds_and_source_mtimes(agate_scripts, synth, tmp_path):
    """S-11：同内容 + 同 mtime 参数 → 逐字节相同，与源文件 mtime / 构建时刻无关。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    out1, out2 = tmp_path / "a.tar.gz", tmp_path / "b.tar.gz"
    pkg.write_dir_tarball(src, out1, 1_700_000_000)
    for dirpath, _dirs, files in os.walk(src):
        for name in files:
            os.utime(os.path.join(dirpath, name), (1_000_000_000, 1_000_000_000))
    pkg.write_dir_tarball(src, out2, 1_700_000_000)
    assert H.sha256_of(out1) == H.sha256_of(out2)


def test_t6_gzip_header_leaks_neither_filename_nor_time(agate_scripts, synth, tmp_path):
    """cso T-3 / E-15：gzip 头 FNAME 位为 0、MTIME 为 0、OS 字节固定（255）。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    out = tmp_path / "some-distinct-name.tar.gz"
    pkg.write_dir_tarball(src, out, 1_700_000_000)
    raw = out.read_bytes()[:10]
    assert raw[:2] == b"\x1f\x8b"
    assert raw[3] & 0x08 == 0, "FNAME 位必须为 0（不得把输出文件名写进头）"
    assert raw[4:8] == b"\x00\x00\x00\x00", "MTIME 必须为 0"
    assert raw[9] == 255, "OS 字节须固定为 255（unknown）"


def test_t6_write_dir_tarball_refuses_symlink_before_writing(agate_scripts, synth, tmp_path):
    """BDD-15 ④：源目录含软链 → PackageError，且**先于任何写入**校验（不留半成品 tar）。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    _symlink_or_skip(tmp_path, src / "agate" / "lnk")
    out = tmp_path / "bad.tar.gz"
    with pytest.raises(pkg.PackageError):
        pkg.write_dir_tarball(src, out, 1_700_000_000)
    assert not out.exists()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="需要 os.mkfifo（POSIX）")
def test_t6_write_dir_tarball_refuses_special_files(agate_scripts, synth, tmp_path):
    """BDD-15 ④：设备 / FIFO / socket 类成员 → PackageError（这里用 FIFO 代表），且不留半成品。"""
    pkg = _pkg(agate_scripts)
    src = _materialized(pkg, synth, tmp_path)
    os.mkfifo(str(src / "agate" / "fifo"))
    out = tmp_path / "bad.tar.gz"
    with pytest.raises(pkg.PackageError):
        pkg.write_dir_tarball(src, out, 1_700_000_000)
    assert not out.exists()


# ---------------------------------------------------------------------------
# 6. verify_dir（契约验证：顶层集合 / tests / 软链 / 字节码口径）
# ---------------------------------------------------------------------------


def test_bdd_2_verify_dir_clean_materialized_tree_has_no_violation(agate_scripts, synth, tmp_path):
    pkg = _pkg(agate_scripts)
    root = _materialized(pkg, synth, tmp_path)
    assert list(pkg.verify_dir(root)) == []


def test_bdd_2_verify_dir_flags_unregistered_top_level_tests_and_symlinks(agate_scripts, synth, tmp_path):
    """BDD-1 (b)：未登记的顶层条目 = 违约；agate/tests/ 出现 = 违约；软链 = 违约。"""
    pkg = _pkg(agate_scripts)
    root = _materialized(pkg, synth, tmp_path)
    (root / "extra.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    violations = pkg.verify_dir(root)
    assert violations and any("extra.sh" in v for v in violations)
    (root / "extra.sh").unlink()

    (root / "agate" / "tests").mkdir()
    (root / "agate" / "tests" / "t.py").write_text("x\n", encoding="utf-8")
    assert any("tests" in v for v in pkg.verify_dir(root))
    (root / "agate" / "tests" / "t.py").unlink()
    (root / "agate" / "tests").rmdir()
    assert list(pkg.verify_dir(root)) == []

    _symlink_or_skip(tmp_path, root / "agate" / "lnk")
    assert any("lnk" in v for v in pkg.verify_dir(root))


def test_d13_verify_dir_bytecode_policy_and_extra_top(agate_scripts, synth, tmp_path):
    """D-13：默认忽略 __pycache__ / *.pyc（运行后态不算违约）；ignore_bytecode=False 才计；extra_top 放行登记的隐藏元数据。"""
    pkg = _pkg(agate_scripts)
    root = _materialized(pkg, synth, tmp_path)
    cache = root / "agate" / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "agate_common.cpython-312.pyc").write_bytes(b"\x00")
    assert list(pkg.verify_dir(root)) == []
    assert pkg.verify_dir(root, ignore_bytecode=False)
    (root / ".registered-meta").write_text("x\n", encoding="utf-8")
    assert pkg.verify_dir(root)
    assert list(pkg.verify_dir(root, extra_top=(".registered-meta",))) == []


# ---------------------------------------------------------------------------
# 7. 软链基址守卫规范化（D-14，库层；T-14 的参数化四入口测试由 B / E 组写）
# ---------------------------------------------------------------------------

_LINK_VARIANTS = ["{L}", "{L}/", "{L}//", "{L}/.", "{L}/./", "{L}/.."]


@pytest.fixture
def linked_home(tmp_path):
    src = tmp_path / "repo" / "agate"
    src.mkdir(parents=True)
    (src / "canary.txt").write_text("canary\n", encoding="utf-8")
    link = tmp_path / "L"
    _symlink_or_skip(src, link)
    return link


@pytest.mark.parametrize("variant", _LINK_VARIANTS, ids=["L", "L-slash", "L-2slash", "L-dot", "L-slash-dot", "L-dotdot"])
def test_d14_is_symlink_base_defeats_trailing_slash_and_dotdot_bypass(agate_scripts, linked_home, variant):
    """cso F-1（HIGH）：`os.path.islink("L/")` 为 False 的绕过——规范化后必须仍判为软链基址；经软链的 `..` 因物理 / 文本
    解析不一致同样被拒。"""
    pkg = _pkg(agate_scripts)
    raw = variant.format(L=str(linked_home))
    assert pkg.is_symlink_base(raw) is True, raw
    norm, ambiguous = pkg.normalize_home(raw)
    if variant.endswith("/.."):
        assert ambiguous is True
    else:
        assert norm == os.path.abspath(str(linked_home))
        assert ambiguous is False


@pytest.mark.parametrize("variant", ["{P}", "{P}/", "{P}//", "{P}/.", "{P}/../plain", "{N}/new/dir/"])
def test_d14_is_symlink_base_does_not_reject_legitimate_paths(agate_scripts, tmp_path, variant):
    """不误伤：真实目录（含尾斜杠 / 斜杠点 / 只经真实目录的 `..`）与尚不存在的新目录都不是软链基址。"""
    pkg = _pkg(agate_scripts)
    plain = tmp_path / "plain"
    plain.mkdir()
    raw = variant.format(P=str(plain), N=str(tmp_path))
    assert pkg.is_symlink_base(raw) is False, raw
    norm, ambiguous = pkg.normalize_home(raw)
    assert ambiguous is False
    assert norm == os.path.abspath(raw)


def test_d14_agate_home_is_single_source_and_normalized(agate_scripts, tmp_path, monkeypatch):
    """`agate_home()`：AGATE_HOME 优先并规范化（去尾斜杠 / 斜杠点）；未设时 `<HOME>/.agate`；同一实现供安装与解析共用。"""
    pkg = _pkg(agate_scripts)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.delenv("AGATE_HOME", raising=False)
    assert pkg.agate_home() == os.path.abspath(os.path.join(str(fake_home), ".agate"))
    target = tmp_path / "h"
    monkeypatch.setenv("AGATE_HOME", f"{target}//./")
    assert pkg.agate_home() == os.path.abspath(str(target))


def test_d14_agate_home_of_symlink_with_trailing_slash_is_still_symlink_base(agate_scripts, linked_home, monkeypatch):
    pkg = _pkg(agate_scripts)
    monkeypatch.setenv("AGATE_HOME", f"{linked_home}/")
    assert pkg.is_symlink_base(pkg.agate_home()) is True


# ---------------------------------------------------------------------------
# 8. compute_sha256 字节码免疫（T-21，eng B-1 (b)）
# ---------------------------------------------------------------------------


def _make_tree(root):
    (root / "sub").mkdir(parents=True)
    (root / "a.py").write_text("print('a')\n", encoding="utf-8")
    (root / "sub" / "b.txt").write_text("b\n", encoding="utf-8")
    return root


def test_t21_compute_sha256_directory_ignores_bytecode(agate_scripts, tmp_path):
    """T-21：同一目录树有 / 无 `__pycache__`、`*.pyc`、`*.pyo` 时目录哈希相同（否则运行一次脚本就使 offline 校验误报「被篡改」）。"""
    common = H.load_project_module(agate_scripts, "agate_common.py", "agate_common")
    root = _make_tree(tmp_path / "tree")
    plain = common.compute_sha256(root)
    assert plain == H.expected_component_sha256(root), "无字节码时必须与独立 oracle 一致（既有目录哈希约定不变）"
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "a.cpython-312.pyc").write_bytes(b"\x00pyc")
    (root / "sub" / "__pycache__").mkdir()
    (root / "sub" / "__pycache__" / "x.pyc").write_bytes(b"\x01")
    (root / "sub" / "old.pyo").write_bytes(b"\x02")
    assert common.compute_sha256(root) == plain


def test_t21_compute_sha256_still_detects_real_content_change(agate_scripts, tmp_path):
    """T-21 反面：非字节码文件内容变化 / 新增文件必须仍改变哈希。"""
    common = H.load_project_module(agate_scripts, "agate_common.py", "agate_common")
    root = _make_tree(tmp_path / "tree")
    before = common.compute_sha256(root)
    (root / "sub" / "b.txt").write_text("changed\n", encoding="utf-8")
    assert common.compute_sha256(root) != before
    (root / "sub" / "b.txt").write_text("b\n", encoding="utf-8")
    assert common.compute_sha256(root) == before
    (root / "new.txt").write_text("n\n", encoding="utf-8")
    assert common.compute_sha256(root) != before


# ---------------------------------------------------------------------------
# 9. 真实仓库上的库层验证（T-7 tripwire / BDD-23 真实基线）
# ---------------------------------------------------------------------------

_KNOWN_AGATE_TOP = {
    "AGENTS.md",
    "CONTEXT.md",
    "LIMITATIONS.md",
    "SETUP.md",
    "UPGRADING.md",
    "WORKFLOW.md",
    "adr.md",
    "assets",
    "dispatch-protocol.md",
    "git-integration.md",
    "loop-orchestration.md",
    "orchestrator-template.md",
    "phase-cards",
    "platform-notes.md",
    "role-system.md",
    "rules",
    "scripts",
    "state-machine.md",
    "tests",
}


def test_t7_tripwire_agate_top_level_entries_match_known_set():
    """T-7 / R-4：真实 HEAD 上 `agate/` 顶层条目集合与已知集合逐一比对——新增顶层文件 / 目录必须有意识地处理
    （入包则更新本集合；不该入包则在 agate_package 增排除规则并同步 UPGRADING 契约），不能悄悄进包。"""
    out = H.git_text(H.REPO_ROOT, "ls-tree", "--name-only", "HEAD", "agate/")
    top = {line.split("/", 1)[1] for line in out.splitlines() if line.strip()}
    assert top == _KNOWN_AGATE_TOP, f"新增: {top - _KNOWN_AGATE_TOP}；消失: {_KNOWN_AGATE_TOP - top}"


def test_bdd_23_real_head_package_is_small_and_clean(agate_scripts, tmp_path):
    """BDD-23 / BDD-2（真实树）：真实 HEAD 的包集合只含 agate/**（无 tests）+ 登记根文件，落盘字节 S ≤ 1.25×B（B 由独立
    oracle 按 git ls-tree -l 求和），且远小于整仓。"""
    pkg = _pkg(agate_scripts)
    entries = pkg.list_package(H.REPO_ROOT, "HEAD")
    fpkg = set(_paths(entries))
    sizes = H.ls_tree_sizes(H.REPO_ROOT, "HEAD")
    assert fpkg == {p for p, _s in sizes if H.oracle_in_package(p)}
    assert "agate/scripts/agate-install.py" in fpkg and "agate/AGENTS.md" in fpkg
    assert not any(p.startswith("agate/tests/") for p in fpkg)
    assert {p.split("/")[0] for p in fpkg} <= H.ORACLE_TOP_LEVEL
    dest = tmp_path / "vX"
    dest.mkdir()
    pkg.materialize(H.REPO_ROOT, "HEAD", dest)
    baseline = sum(s for p, s in sizes if H.oracle_in_package(p))
    total_repo = sum(s for _p, s in sizes)
    actual = H.total_bytes(dest)
    assert actual == baseline
    assert actual <= 1.25 * baseline
    assert actual < 0.25 * total_repo, "本体包应远小于整仓（冗余量化下降）"


def test_bdd_23_v0_72_0_baseline_matches_p1_numbers(agate_scripts, tmp_path):
    """BDD-23 / P1 T-1 基线（不可变历史证据）：tag v0.72.0 的包 B = 1,864,871 B，S ≤ 2,331,088 B（≈1.25×B）。"""
    pkg = _pkg(agate_scripts)
    have = H.run_git(H.REPO_ROOT, "rev-parse", "--verify", "-q", "refs/tags/v0.72.0", check=False).returncode == 0
    assert have, "需要 tag v0.72.0（CI 的 pytest job 已 fetch-tags；本地请 git fetch --tags）"
    entries = pkg.list_package(H.REPO_ROOT, "v0.72.0")
    sizes = dict(H.ls_tree_sizes(H.REPO_ROOT, "v0.72.0"))
    assert len(entries) == 153
    assert sum(sizes[e.path] for e in entries) == 1_864_871
    dest = tmp_path / "v0.72.0"
    dest.mkdir()
    pkg.materialize(H.REPO_ROOT, "v0.72.0", dest)
    assert H.total_bytes(dest) <= 2_331_088


def test_bdd_23_synthetic_ratio_uses_same_formula(agate_scripts, synth, tmp_path):
    """BDD-23（合成仓库口径）：同一判定式 S ≤ 1.25×B，且 S 远小于整 tag 字节和。"""
    pkg = _pkg(agate_scripts)
    dest = _materialized(pkg, synth, tmp_path)
    sizes = H.ls_tree_sizes(synth.bare, f"refs/tags/{H.MAIN_TAG}")
    baseline = sum(s for p, s in sizes if H.oracle_in_package(p))
    actual = H.total_bytes(dest)
    assert actual <= 1.25 * baseline
    assert actual < 0.5 * sum(s for _p, s in sizes)
