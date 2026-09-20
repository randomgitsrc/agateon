# tests/unit/test_agate_pack_offline.py — 离线打包器 agate-pack-offline.py（TAG0008 批次 offline，BDD-22~24；TAG0037 P3 组 B 修订）
# 被测：agate/scripts/agate-pack-offline.py。
# TAG0037 修订（P2 §6 T-1 / T-11 / BDD-11 ①）：原"mock subprocess.run 凭空造 bundle/agate/WORKFLOW.md"的假产物助手
#   （_fake_artifacts_side_effect）是"同源假设"缺陷的源头之一——本文件改为经**真实 pack 入口**（子进程运行 agate-pack-offline.py，
#   git 步骤真实执行于合成 file:// 上游的 bare 克隆）生成 bundle，仅 `pip download` 用 PATH 内 pip shim 打桩（占位 wheel，无网络）。
# 新增（B2 批）：BDD-9（本体而非整仓）/ BDD-10（缺省 --repo 与 AGATE_HOME 同源）/ BDD-11（sentinel）/ BDD-24（老 tag、畸形 tag）、
#   manifest `files` 清单、`--ref`（预发布 tag）、pyyaml 固定版本 + wheel 文件名大小写无关（eng / cso F-2）。
# 平台：pip shim 仅 POSIX；依赖 shim 的用例在 Windows 上 skip（windows_smoke 仅保留"不依赖 pip 的 tag 缺失"用例）。

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

import helpers_tag_repo as H

_posix_only = pytest.mark.skipif(sys.platform == "win32", reason="pip shim 仅 POSIX")
_PLAT = "linux-x86_64"  # 平台标签与宿主机无关（pack 只用它选 pip --platform 值与命名）


def _load_script_module(agate_scripts, module_name, filename):
    """从 agate/scripts/ 加载脚本为模块；被测模块未实现 → ModuleNotFoundError（B 类红灯）。"""
    return H.load_project_module(agate_scripts, filename, module_name)


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


@pytest.fixture
def pack_repo(tmp_path, synth):
    """每个用例独立的 bare 克隆（pack 的 git 步骤真实执行其上，不污染共享夹具）。"""
    return H.clone_bare(synth.bare, tmp_path / "pack-src.git")


def _pack(agate_scripts, tmp_path, repo, tag, platform=_PLAT, extra=(), pip_mode=None, wheel_case=None, home=None, agate_home=None, no_repo_arg=False):
    """真实 pack 入口：子进程运行 agate-pack-offline.py；pip 用 PATH shim。返回 (proc, bundle_dir, pip_log)。"""
    shim_dir = H.make_pip_shim(tmp_path / "pipbin")
    log = tmp_path / "pip.log"
    extra_env = {}
    if pip_mode:
        extra_env["AGATE_TEST_PIP_MODE"] = pip_mode
    if wheel_case:
        extra_env["AGATE_TEST_PIP_WHEEL_CASE"] = wheel_case
    env = H.tool_env(home or (tmp_path / "home"), agate_home=agate_home, shim_dir=shim_dir, pip_log=log, extra=extra_env)
    out = tmp_path / "out"
    argv = [sys.executable, agate_scripts / "agate-pack-offline.py", tag, "--platform", platform, "--outdir", out]
    if not no_repo_arg:
        argv += ["--repo", repo]
    argv += list(extra)
    proc = H.run_tool(argv, env=env)
    return proc, out / f"agate-{tag}-{platform}", log


@_posix_only
def test_bdd_22_bundle_manifest(agate_scripts, tmp_path, pack_repo):
    """BDD-22（TAG0008）：pack 产出 bundle/{agate,wheels,manifest.json}，manifest 平台 / 版本正确，组件 sha256 为 64 位十六进制。
    TAG0037：bundle 经真实 pack 入口生成（不再由 mock 凭空造文件）。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, "v0.48.0")
    assert proc.returncode == 0, proc.stderr
    assert (bundle / "manifest.json").is_file()
    assert (bundle / "agate" / "WORKFLOW.md").is_file()
    assert list((bundle / "wheels").glob("*.whl"))

    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["platform"] == _PLAT
    assert manifest["version"] == "v0.48.0"
    for comp in manifest["components"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", comp["sha256"])


@_posix_only
def test_bdd_23_manifest_fields_checksum(agate_scripts, tmp_path, pack_repo):
    """BDD-23（TAG0008）：manifest 的 pyyaml 组件 sha256 == wheel 字节哈希，且路径指向 bundle 内真实文件。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, "v0.48.0")
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["platform"] == _PLAT

    wheel = next((bundle / "wheels").glob("pyyaml-*.whl"))
    pyyaml_entry = manifest["components"]["pyyaml"]
    assert pyyaml_entry["sha256"] == _sha256_bytes(wheel.read_bytes())
    assert (bundle / pyyaml_entry["path"]).is_file()
    for name, comp in manifest["components"].items():
        assert comp["sha256"], f"component {name} sha256 为空"


@pytest.mark.windows_smoke
def test_bdd_24_fail_tag_missing(agate_scripts, tmp_path, pack_repo):
    """BDD-24（TAG0008）：tag 不存在 → 非 0 退出、stderr 含 tag 名、不产 manifest.json（此失败发生在 pip 之前，无需 shim）。"""
    out = tmp_path / "out"
    proc = H.run_tool(
        [sys.executable, agate_scripts / "agate-pack-offline.py", "v0.99.0", "--platform", _PLAT, "--outdir", out, "--repo", pack_repo],
        env=H.tool_env(tmp_path / "home"),
    )
    assert proc.returncode != 0
    assert "v0.99.0" in proc.stderr
    assert not (out / f"agate-v0.99.0-{_PLAT}" / "manifest.json").exists()


@_posix_only
def test_bdd_24_fail_pip_network(agate_scripts, tmp_path, pack_repo):
    """BDD-24（TAG0008）：pip download 失败 → 非 0 退出、stderr 含 download、不产 manifest.json。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, "v0.48.0", pip_mode="fail-download")
    assert proc.returncode != 0
    assert "download" in proc.stderr
    assert not (bundle / "manifest.json").exists()


# ─────────────────────────────────────────────
# TAG0031 簇 A（DEBT0002 hash 共享，BDD-1）：compute_sha256 迁移到 agate_common
#   迁移后 agate-pack-offline.py 应 `from agate_common import compute_sha256`（同一函数对象，
#   不再本地重复实现）。（TAG0037 未改动本用例）


def test_bdd_1_pack_offline_imports_compute_sha256_from_agate_common(agate_scripts):
    """BDD-1：agate-pack-offline.py 迁移后 compute_sha256 应是 agate_common.compute_sha256
    同一函数对象（全仓共享单实现），不是本地重复定义。"""
    module = _load_script_module(agate_scripts, "agate_pack_offline_bdd1", "agate-pack-offline.py")
    import agate_common

    assert module.compute_sha256 is agate_common.compute_sha256


@_posix_only
def test_bdd_24_fail_wheel_missing(agate_scripts, tmp_path, pack_repo):
    """BDD-24（TAG0008）：pip download 成功但没有 pyyaml wheel → 非 0 退出、stderr 含 wheel、不产 manifest.json。
    （pip 打桩：本地空实现——exit 0 且不落任何 wheel；helpers 的 shim 总会落占位 wheel，故此处用本地空 shim。）"""
    shim_dir = tmp_path / "emptypip"
    shim_dir.mkdir()
    pip = shim_dir / "pip"
    pip.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    pip.chmod(0o755)
    env = H.tool_env(tmp_path / "home", shim_dir=shim_dir)
    out = tmp_path / "out"
    proc = H.run_tool(
        [sys.executable, agate_scripts / "agate-pack-offline.py", "v0.48.0", "--platform", _PLAT, "--outdir", out, "--repo", pack_repo],
        env=env,
    )
    assert proc.returncode != 0
    assert "wheel" in proc.stderr
    assert not (out / f"agate-v0.48.0-{_PLAT}" / "manifest.json").exists()


# ─────────────────────────────────────────────
# TAG0037 B2：bundle 是本体而非整仓（BDD-9 / BDD-11 sentinel）、files 清单、缺省 --repo、--ref、pyyaml 固定


@_posix_only
def test_bdd_9_and_11_real_pack_bundle_is_body_not_whole_repo(agate_scripts, tmp_path, pack_repo, synth):
    """BDD-9 / BDD-11 ②：真实 pack 产出的 bundle/agate/ 是本体（含 scripts/ 与 WORKFLOW.md，无 agate-workspace/docs/site，无 agate/agate 双层）；
    bundle 顶层 = {agate/, 登记根文件, wheels/, manifest.json}；成员字节 == git blob（不受 .gitattributes eol 影响）。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.MAIN_TAG)
    assert proc.returncode == 0, proc.stderr
    H.assert_real_bundle_layout(bundle)  # sentinel：旧 packer（整仓检出）在此必抛 AssertionError
    assert {p.name for p in bundle.iterdir()} == {"agate", "CHANGELOG.md", "LICENSE", "NOTICES.md", "wheels", "manifest.json"}
    expected = synth.expected_package(H.MAIN_TAG)
    got = {p for p in H.file_set(bundle) if p.startswith("agate/") or p in H.ORACLE_ROOT_FILES}
    assert got == expected, f"bundle 内本体文件集合与包集合 P 不一致: 多 {sorted(got - expected)[:5]} 少 {sorted(expected - got)[:5]}"
    for rel in sorted(expected):
        assert (bundle / rel).read_bytes() == synth.blob(H.MAIN_TAG, rel), f"{rel} 字节应与 git blob 一致"


@_posix_only
def test_bdd_9_bundle_has_no_bytecode_no_worktree_metadata_and_source_repo_untouched(agate_scripts, tmp_path, pack_repo):
    """BDD-9 / T-15：pack 不用 git worktree——bundle 内无 .git 指针、无字节码；源克隆仓库不被写入（无 worktrees/ 登记）。"""
    before = H.snapshot_tree(pack_repo)
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.MAIN_TAG)
    assert proc.returncode == 0, proc.stderr
    assert not [p for p in bundle.rglob("*") if p.name == ".git"], "bundle 内不应有 .git 指针"
    assert not [p for p in bundle.rglob("*") if H.is_bytecode_path(p.relative_to(bundle))]
    assert H.snapshot_tree(pack_repo) == before, "pack 只读源仓库（git plumbing），不得写入 worktrees/ 等元数据"


@_posix_only
def test_bdd_9_manifest_files_lists_package_set_and_root_file_components(agate_scripts, tmp_path, pack_repo, synth):
    """P2 D-5：manifest 新增 `files`（包集合 P 的相对路径清单，排序）；登记根文件各有一个文件组件（sha256 == 文件字节）。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.MAIN_TAG)
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == sorted(synth.expected_package(H.MAIN_TAG))
    by_path = {c["path"]: c for c in manifest["components"].values()}
    for name in H.ORACLE_ROOT_FILES:
        assert name in by_path, f"manifest 缺登记根文件组件 {name}"
        assert by_path[name]["sha256"] == H.sha256_of(bundle / name)
    agate_comp = manifest["components"]["agate"]
    assert agate_comp["path"] == "agate"
    assert agate_comp["sha256"] == H.expected_component_sha256(bundle / "agate")


@_posix_only
def test_bdd_24_old_tag_missing_notices_is_tolerated(agate_scripts, tmp_path, pack_repo, synth):
    """BDD-24 ①（pack 侧）：缺 NOTICES.md 的老 tag 照常打包（缺失的登记根文件被容忍，manifest.files 不含它）。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.NO_NOTICES_TAG)
    assert proc.returncode == 0, proc.stderr
    assert not (bundle / "NOTICES.md").exists()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "NOTICES.md" not in manifest["files"]
    assert set(manifest["files"]) == synth.expected_package(H.NO_NOTICES_TAG)


@_posix_only
def test_bdd_24_malformed_tag_without_agate_scripts_fails_without_manifest(agate_scripts, tmp_path, pack_repo):
    """BDD-24 ②（pack 侧）：树内无 agate/scripts/ 的畸形 tag → 非 0 退出、stderr 指明缺 agate/scripts、不产 manifest。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.MALFORMED_TAG)
    assert proc.returncode != 0
    assert "agate/scripts" in proc.stderr
    assert not (bundle / "manifest.json").exists()


@_posix_only
def test_bdd_10_default_repo_follows_agate_home(agate_scripts, tmp_path, synth):
    """BDD-10：pack 缺省 `--repo` 取 `AGATE_HOME/repo`（与在线安装同源）——仅设 AGATE_HOME，HOME 指向另一空目录，不传 --repo。"""
    agate_home = tmp_path / "ah"
    agate_home.mkdir()
    cloned = H.run_git(tmp_path, "clone", "-q", "--", synth.url, str(agate_home / "repo"), check=False)
    assert cloned.returncode == 0, cloned.stderr
    home = tmp_path / "other-home"
    home.mkdir()
    proc, bundle, _log = _pack(agate_scripts, tmp_path, None, H.MAIN_TAG, home=home, agate_home=agate_home, no_repo_arg=True)
    assert proc.returncode == 0, f"缺省 --repo 应取 AGATE_HOME/repo: {proc.stderr}"
    assert (bundle / "manifest.json").is_file()
    assert not (home / ".agate").exists(), "不得落到 HOME/.agate"


@_posix_only
def test_pack_ref_prerelease_tag_content_with_strict_manifest_version(agate_scripts, tmp_path, pack_repo, synth):
    """P2 §3.4 / BDD-13 ⑤ 支撑：`--ref <预发布 tag>`——内容取自该 tag，manifest.version 恒为严格 vX.Y.Z，source_ref 原样记录。"""
    proc, bundle, _log = _pack(agate_scripts, tmp_path, pack_repo, H.MAIN_TAG, extra=("--ref", H.PRERELEASE_TAG))
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == H.MAIN_TAG
    assert manifest["source_ref"] == H.PRERELEASE_TAG
    assert (bundle / "CHANGELOG.md").read_bytes() == synth.blob(H.PRERELEASE_TAG, "CHANGELOG.md")
    assert (bundle / "CHANGELOG.md").read_bytes() != synth.blob(H.MAIN_TAG, "CHANGELOG.md")


@_posix_only
@pytest.mark.parametrize("wheel_case", ["lower", "upper"], ids=["wheel-name-lowercase", "wheel-name-uppercase-PyYAML"])
def test_pack_pins_pyyaml_and_finds_wheel_case_insensitively(agate_scripts, tmp_path, pack_repo, wheel_case):
    """cso F-2 / E-16：pyyaml 用 agate_package.PYYAML_PIN 固定（pip 收到 `pyyaml==<PIN>`）；wheel 文件名大写（`PyYAML-…`，6.0.2 的实际命名）也能被找到。"""
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    proc, bundle, log = _pack(agate_scripts, tmp_path, pack_repo, "v0.48.0", wheel_case=wheel_case)
    assert proc.returncode == 0, proc.stderr
    downloads = [argv for argv in H.read_pip_log(log) if argv and argv[0] == "download"]
    assert downloads, "应调用 pip download"
    assert f"pyyaml=={pkg.PYYAML_PIN}" in downloads[0], downloads[0]
    assert "--only-binary=:all:" in downloads[0]
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    wheel_path = Path(manifest["components"]["pyyaml"]["path"])
    assert wheel_path.name.lower().startswith("pyyaml-")
    assert (bundle / wheel_path).is_file()


def test_bdd_11_offline_test_helpers_no_longer_forge_the_body_by_hand():
    """BDD-11 ①：三处'同源假设'助手所在文件（test_install_offline.py / test_agate_pack_offline.py / test_offline_bundle_roundtrip.py）
    源码中不再出现"手工往 bundle/agate 下写 WORKFLOW.md 冒充本体"的构造（本判定的正则见下）。"""
    tests_root = H.REPO_ROOT / "agate" / "tests"
    pat = re.compile(r"\(\s*agate\w*\s*/\s*[\"']WORKFLOW\.md[\"']\s*\)\s*\.write_text")
    offenders = []
    for rel in ("unit/test_install_offline.py", "unit/test_agate_pack_offline.py", "regression/test_offline_bundle_roundtrip.py"):
        if pat.search((tests_root / rel).read_text(encoding="utf-8")):
            offenders.append(rel)
    assert not offenders, f"仍手工构造假本体: {offenders}"
