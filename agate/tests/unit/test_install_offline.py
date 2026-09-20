# tests/unit/test_install_offline.py — 内网安装器 install-offline.py（TAG0008 批次 offline，BDD-25~29；TAG0037 P3 组 B 修订）
# 被测：agate/scripts/install-offline.py（TAG0037 批 B2 重写：manifest `files` 对账、只拷登记文件、工作目录 + 换位 + 兄弟安装器 --adopt、软链守卫）。
#
# TAG0037 修订登记（P2 §6 T-2 / T-11 / BDD-11 ①，详见 P3-test-cases.md §6「既有测试修改登记」）：
#   * `_make_bundle` 改为经**真实 pack 入口**（子进程运行 agate-pack-offline.py，git 步骤真实执行于合成 file:// 上游的 bare 克隆；
#     仅 pip download 用 PATH shim 打桩）生成 bundle，并立刻用 sentinel 断言其为"本体而非整仓"——不再手工构造 bundle/agate/WORKFLOW.md 冒充本体
#     （旧同源假设：假 bundle 与 install-offline 同样以为 `bundle/agate/` 就是本体，掩盖了 P0 BUG）。
#   * 因 D-7 / R-9 / R-10：`.installed-version` 断言删除；`--skip-python` 用例改为"vX.Y.Z/python 恒不存在"；copy-mode 用例改为验证 `--adopt` 结果。
#   * 禁止全局 `mock.patch("subprocess.run")`（会吞掉 `--adopt` 子进程，eng G-2）：pip 一律用 PATH 内 shim，日志经 AGATE_TEST_PIP_LOG 读取。
#   * `test_bdd_25/26`、`test_manifest_*_rejected`、TAG0031 R1 三个用例的断言逻辑未改（仅 bundle 来源变化 / 文件名去伪装）。
# 新增：BDD-9/10/11/12/33、T-2 红灯回放、T-15（bundle 内入口）、T-16（换位失败注入）、T-19（P 集合对账）、T-23（清扫只删自己的，数据安全必测）、
#       agate_package 换位 / 清扫库函数（make_work_dir / sweep_stale / recover_backups / swap_in / rollback_swap / snapshot_pointers /
#       restore_pointers / discard_backup；A 组 §1 明确归本组）。
# 平台：pip shim / 软链 / 换位用例仅 POSIX（Windows 上 skip）。隔离：全部在 tmp_path；无 rm -rf（清理仅依赖 pytest tmp_path）。

import contextlib
import errno
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

import helpers_tag_repo as H

_posix_only = pytest.mark.skipif(sys.platform == "win32", reason="pip shim / 软链 / 换位用例仅 POSIX")

_STEP_RES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}
_VARIANTS = ["L", "L/", "L//", "L/.", "L/.."]
_VARIANT_IDS = [f"t14-{i}-{v.replace('/', 's').replace('.', 'd')}" for i, v in enumerate(_VARIANTS)]
_TMP_MARKER = "agate-package/1 kind=tmp version=v0.73.0 pid=1\n"
_BAK_MARKER = "agate-package/1 kind=bak version=v0.72.5 pid=1\n"
_MARKER_NAME = ".agate-installer-owned"  # P2 §3.2 MARKER_NAME（R-8：专属标记文件）


def _load_script_module(agate_scripts, module_name, filename):
    """从 agate/scripts/ 加载脚本为模块；被测模块未实现 → ModuleNotFoundError（B 类红灯，No module named 供 formatter 提取）。"""
    path = agate_scripts / filename
    if not path.is_file():
        raise ModuleNotFoundError(f"No module named '{module_name}' (被测模块未实现: {filename})")
    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 真实 pack 入口生成的 bundle（BDD-11 ①：取代假 bundle 助手）
# ---------------------------------------------------------------------------

_STATE = {}


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


@pytest.fixture(scope="module", autouse=True)
def _bundle_cache(agate_scripts, tmp_path_factory, synth):
    """模块级：按 (version, platform, with_pillow) 缓存真实 pack 产物（子进程运行 agate-pack-offline.py）。fixture 自身不断言。"""
    base = tmp_path_factory.mktemp("offline_real_bundles")
    cache = {}

    def build(version, platform, with_pillow):
        key = (version, platform, with_pillow)
        if key not in cache:
            work = base / f"b{len(cache)}"
            work.mkdir()
            repo = H.clone_bare(synth.bare, work / "src.git")
            shim = H.make_pip_shim(work / "pipbin")
            env = H.tool_env(work / "home", shim_dir=shim, pip_log=work / "pip.log")
            argv = [sys.executable, agate_scripts / "agate-pack-offline.py", version, "--platform", platform, "--outdir", work / "out", "--repo", repo]
            if with_pillow:
                argv.append("--include-pillow")
            proc = H.run_tool(argv, env=env)
            cache[key] = (proc, work / "out" / f"agate-{version}-{platform}")
        return cache[key]

    _STATE["build"] = build
    yield
    _STATE.clear()


def _make_bundle(tmp_path, version="v0.48.0", platform="linux-x86_64", with_pillow=False):
    """离线 bundle：经真实 pack 入口生成（合成 tag 仓库 + PATH pip shim），拷到 tmp_path/bundle；并立即断言 sentinel（bundle/agate 是本体而非整仓，BDD-11）。"""
    if sys.platform == "win32":
        pytest.skip("真实 pack 需 PATH pip shim（仅 POSIX）")
    proc, cached = _STATE["build"](version, platform, with_pillow)
    assert proc.returncode == 0, f"真实 pack 应成功: {proc.stderr}"
    H.assert_real_bundle_layout(cached)
    bundle = tmp_path / "bundle"
    shutil.copytree(str(cached), str(bundle))
    return bundle


def _host_plat():
    plat = H.host_platform_label()
    if plat is None:
        pytest.skip("宿主平台无对应 offline 平台标签")
    return plat


def _use_pip_shim(monkeypatch, tmp_path, mode=None):
    """当前进程内运行 main() 时使用：PATH 前置 pip shim、隔离 HOME；返回 pip 调用日志路径。"""
    shim = H.make_pip_shim(tmp_path / "pipbin-inproc")
    log = tmp_path / "pip-inproc.log"
    monkeypatch.setenv("PATH", str(shim) + os.pathsep + os.environ.get("PATH", ""))
    monkeypatch.setenv("AGATE_TEST_PIP_LOG", str(log))
    if mode:
        monkeypatch.setenv("AGATE_TEST_PIP_MODE", mode)
    (tmp_path / "home-inproc").mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home-inproc"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home-inproc"))
    for key in ("AGATE_ROOT", "AGATE_HOME", "AGATE_HOOK_COPY_MODE"):
        monkeypatch.delenv(key, raising=False)
    return log


def _run_offline(agate_scripts, tmp_path, bundle, *args, entry=None, agate_home=None, pip_mode=None, extra_env=None, home=None):
    """子进程运行 install-offline.py（默认仓库脚本；entry 可指 bundle 内入口）；返回 (proc, pip_log)。"""
    shim = H.make_pip_shim(tmp_path / "pipbin-run")
    log = tmp_path / "pip-run.log"
    extra = dict(extra_env or {})
    if pip_mode:
        extra["AGATE_TEST_PIP_MODE"] = pip_mode
    env = H.tool_env(home or (tmp_path / "home-run"), agate_home=agate_home, shim_dir=shim, pip_log=log, extra=extra)
    proc = H.run_tool([sys.executable, entry or (agate_scripts / "install-offline.py"), bundle, *args], env=env)
    return proc, log


def _pointer_state(dest):
    out = {}
    for name in ("latest", "current"):
        p = Path(dest) / name
        if p.is_symlink():
            out[name] = ("link", os.readlink(str(p)))
        elif p.is_dir():
            out[name] = ("dir", tuple(sorted(os.listdir(str(p)))))
        elif p.is_file():
            out[name] = ("file", p.read_text(encoding="utf-8"))
        else:
            out[name] = None
    return out


def _snap(dest):
    dest = Path(dest)
    if not dest.exists():
        return None
    return (sorted(os.listdir(str(dest))), H.snapshot_tree(dest, ignore_bytecode=False))


def _symlink_dest(tmp_path):
    """软链 dest：<tmp>/home/.agate 软链 → <tmp>/src/agate（含 scripts/ 与金丝雀）。返回 (link, target)。"""
    target = tmp_path / "src" / "agate"
    (target / "scripts").mkdir(parents=True)
    (target / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home-link"
    home.mkdir()
    link = home / ".agate"
    try:
        os.symlink(str(target), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    return link, target


def _variant(link, variant):
    return str(link) + variant[1:]


# ---------------------------------------------------------------------------
# TAG0008 既有用例（BDD-25~29）——bundle 来源改为真实 pack；pip 改 PATH shim
# ---------------------------------------------------------------------------


@pytest.mark.windows_smoke
def test_bdd_25_platform_mismatch_reject(tmp_path, agate_scripts, capsys):
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, platform="linux-x86_64")
    dest = tmp_path / "dest"

    with mock.patch.object(module, "get_current_platform", return_value="windows-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code != 0
    assert "linux-x86_64" in err
    assert "windows-x86_64" in err
    assert not dest.exists()


def test_bdd_26_checksum_mismatch_reject(tmp_path, agate_scripts, capsys):
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, platform="linux-x86_64")
    wheel = next((bundle / "wheels").glob("pyyaml-*.whl"))
    tampered = bytearray(wheel.read_bytes())
    tampered[0] ^= 0xFF
    wheel.write_bytes(bytes(tampered))
    dest = tmp_path / "dest"

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code != 0
    assert "pyyaml" in err
    assert not dest.exists()


def test_bdd_26b_checksum_mismatch_message_says_corrupt_or_replaced_not_tampered(tmp_path, agate_scripts, capsys):
    """cso F-4：校验失败文案如实——"不一致（损坏或被替换）"，不断言"被篡改"（哈希无法认证发布者，只能发现不一致）。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, platform="linux-x86_64")
    wheel = next((bundle / "wheels").glob("pyyaml-*.whl"))
    wheel.write_bytes(wheel.read_bytes() + b"x")
    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(tmp_path / "dest")])
    err = capsys.readouterr().err
    assert code != 0
    assert "不一致" in err and "损坏或被替换" in err
    assert "篡改" not in err


@_posix_only
def test_bdd_27_wheels_offline_install(tmp_path, agate_scripts, monkeypatch):
    """BDD-27（TAG0008）：install_wheels 用 `pip install --no-index --find-links <bundle>/wheels pyyaml [Pillow]`。
    TAG0037 T-11：不再全局 patch subprocess.run，改由 PATH 内 pip shim 记录 argv。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, with_pillow=True)
    log = _use_pip_shim(monkeypatch, tmp_path)

    module.install_wheels(str(bundle), skip=())

    installs = [a for a in H.read_pip_log(log) if a and a[0] == "install"]
    assert installs, "应调用 pip install"
    argv = installs[-1]
    assert "--no-index" in argv
    assert "--find-links" in argv
    assert any(str(bundle / "wheels") in a for a in argv)
    assert any("pyyaml" in a for a in argv)
    assert any("Pillow" in a for a in argv)


@_posix_only
def test_bdd_28_version_dir_hook_verify(tmp_path, agate_scripts, monkeypatch):
    """BDD-28（TAG0008）：安装后版本目录就位、指针建立。TAG0037 T-11 / D-7 / R-10：删除 `.installed-version` 断言（契约不再登记隐藏元数据）；
    指针改为 `--adopt` 写入的 `latest → vX.Y.Z`、`current → latest`（不再由 install-offline 直指 vX.Y.Z）；不再写 `dest/.agate-root`。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, version="v0.48.0")
    dest = tmp_path / "agate-root"
    _use_pip_shim(monkeypatch, tmp_path)

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])
    assert code == 0

    version_dir = dest / "v0.48.0"
    assert version_dir.is_dir()
    assert (version_dir / "agate" / "WORKFLOW.md").is_file()
    assert not (version_dir / ".installed-version").exists(), "D-7：不再写 .installed-version"
    assert not (dest / ".agate-root").exists(), "D-7：不再写 dest/.agate-root"
    assert os.readlink(str(dest / "latest")) == "v0.48.0"
    assert os.readlink(str(dest / "current")) == "latest", "current 应指向 latest（不再直指 vX.Y.Z）"


@_posix_only
def test_bdd_28b_copy_mode_hook(agate_scripts, tmp_path, monkeypatch):
    """BDD-28b（TAG0008）：AGATE_HOOK_COPY_MODE=1。TAG0037 R-10 / T-11：该变量是 hook 复制模式概念，不再影响版本根指针——
    改为验证 `--adopt` 结果：latest / current 指针存在且解析到版本目录，不写 dest/.agate-root。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, version="v0.48.0")
    dest = tmp_path / "agate-root-copy"
    _use_pip_shim(monkeypatch, tmp_path)
    monkeypatch.setenv("AGATE_HOOK_COPY_MODE", "1")

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])
    assert code == 0

    version_dir = dest / "v0.48.0"
    assert version_dir.is_dir()
    assert (dest / "latest").exists() and (dest / "current").exists()
    assert (dest / "current").resolve() == version_dir.resolve()
    assert not (dest / ".agate-root").exists()


@_posix_only
def test_bdd_29_skip_flags(tmp_path, agate_scripts, capsys, monkeypatch):
    """BDD-29（TAG0008）：--skip-python / --skip-pillow 过滤已包含项。TAG0037 T-11：pip 用 PATH shim；`vX.Y.Z/python` 任一情况下均不存在（R-9）。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, with_pillow=True)
    dest = tmp_path / "dest"
    log = _use_pip_shim(monkeypatch, tmp_path)

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest), "--skip-python", "--skip-pillow"])

    err = capsys.readouterr().err
    assert code == 0
    assert err.strip() == ""
    installs = [a for a in H.read_pip_log(log) if a and a[0] == "install"]
    assert installs
    last = installs[-1]
    assert "--no-index" in last
    assert "--find-links" in last
    assert any("pyyaml" in a for a in last)
    assert not any("Pillow" in a for a in last)
    assert not (dest / "v0.48.0" / "python").exists()


@_posix_only
def test_bdd_29b_no_pillow_bundle_installs_pyyaml_only(tmp_path, agate_scripts, capsys, monkeypatch):
    """rev2 CRITICAL-2：无 Pillow bundle + 无 --skip-pillow → 只装 pyyaml，默认流成功。

    回归用例：`install_wheels` 旧实现恒把 Pillow 塞进 pip 命令（仅由 skip 控制），
    对无 Pillow wheel 的最小 bundle `--no-index` 下必失败。修复后安装清单从 manifest
    `components` 推导——"pillow" 组件不存在则不装 Pillow（BDD-29 语义：skip 只过滤已包含项）。
    TAG0037：bundle 来源改真实 pack；pip 用 PATH shim；`.installed-version` 断言删除（D-7）。
    """
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, with_pillow=False)
    dest = tmp_path / "dest"
    log = _use_pip_shim(monkeypatch, tmp_path)

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code == 0
    assert err.strip() == ""
    installs = [a for a in H.read_pip_log(log) if a and a[0] == "install"]
    assert installs
    last = installs[-1]
    assert "--no-index" in last
    assert "--find-links" in last
    assert any("pyyaml" in a for a in last)
    assert not any("Pillow" in a for a in last)
    assert (dest / "v0.48.0").is_dir()
    assert not (dest / "v0.48.0" / ".installed-version").exists()


def test_manifest_version_traversal_rejected(tmp_path, agate_scripts, capsys):
    """rev2 CRITICAL-3：恶意 manifest `version` 穿越（../../..）→ 拒绝安装，不写出 dest_root。

    回归用例：旧实现 `version = manifest["version"]` 直接作 `dest / version` 目录名，
    篡改后可把 bundle 复制到 dest_root 之外。修复后 version 套 vX.Y.Z 正则
    （同 agate-install `_VERSION_RE`），非法即 fail-closed。
    """
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, version="v0.48.0")
    mpath = bundle / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["version"] = "../../../../pwned"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    dest = tmp_path / "dest"

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code != 0
    assert "version" in err
    assert not (tmp_path / "pwned").exists()
    assert not dest.exists()


@pytest.mark.parametrize("bad_version", ["v0.48.0\n", "v0.48.0-tagtest.1", "v٠.٤٨.٠"], ids=["trailing-newline", "prerelease-suffix", "unicode-digits"])
def test_manifest_version_must_be_strict_fullmatch(bad_version, tmp_path, agate_scripts, capsys, monkeypatch):
    """P2 §3.4 步骤 2 / cso F-9：manifest.version 恒为严格 `vX.Y.Z`（fullmatch + ASCII）——旧 `^…$` 正则会放过结尾换行；
    预发布后缀属于 source_ref，不得出现在 version（否则进入目录名）；Unicode 数字被拒。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path, version="v0.48.0")
    _use_pip_shim(monkeypatch, tmp_path)  # 万一（旧实现）走到 pip，也只打桩
    mpath = bundle / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["version"] = bad_version
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    dest = tmp_path / "dest"
    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])
    err = capsys.readouterr().err
    assert code != 0
    assert "version" in err
    assert not dest.exists()


def test_manifest_component_path_traversal_rejected(tmp_path, agate_scripts, capsys):
    """rev2 CRITICAL-3：恶意 manifest 组件 `path` 用 `..` 越界 → 拒绝安装（防越界读）。

    回归用例：旧实现 `verify_checksums` 直接 `bundle / comp["path"]`，`..` 可越过 bundle
    读取 bundle 外文件（哈希比对作可探测 oracle）。修复后组件 path 必须是 bundle 内相对路径
    （拒绝绝对路径与 `..`，commonpath 断言），非法即 fail-closed。
    """
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path)
    mpath = bundle / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    secret = tmp_path / "secret.txt"
    secret.write_text("sensitive", encoding="utf-8")
    manifest["components"]["evil"] = {
        "path": "../secret.txt",
        "sha256": "0" * 64,
    }
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    dest = tmp_path / "dest"

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code != 0
    assert "path" in err
    assert not dest.exists()


# ─────────────────────────────────────────────
# TAG0031 簇 A（DEBT0002 hash 共享，BDD-1）+ R1（P2-design.md §1.3 pyyaml 引导缓解设计，
# 列入 BDD-2 范围）：compute_sha256 迁移到 agate_common + install-offline.py 的
# _ensure_agate_common(bundle_dir, manifest) 引导函数。
#
# 迁移前 install-offline.py 顶部零外部依赖（不 import agate_common/yaml），刻意设计为可在
# 未装 pyyaml 的机器上跑。迁移后 verify_checksums 需要 agate_common.compute_sha256，但
# agate_common 顶部硬依赖 pyyaml（缺失即 sys.exit(1)）——若直接 `import agate_common` 会在
# 真正没装 pyyaml 的机器上于"给它装 pyyaml"（install_wheels）之前就崩溃。缓解设计：
# _ensure_agate_common 先探测 yaml 可用性；不可用时先内联 hashlib 校验 pyyaml wheel 的
# manifest checksum（校验通过才 pip install --no-index --find-links，不匹配则报错且不装），
# 再 import agate_common 返回模块引用。
# （TAG0037 未改动下列 R1 用例的断言；test_bdd_1 仅把样本文件名去掉"WORKFLOW.md"伪装——它只测哈希一致，
#  不是在造本体。）


def test_bdd_1_verify_checksums_uses_agate_common_compute_sha256(tmp_path, agate_scripts):
    """BDD-1：install-offline.py 的 checksum 校验改用 agate_common.compute_sha256 后，
    用 agate_common.compute_sha256 算出的 checksum 应通过 verify_checksums 校验（两侧共享
    同一 hash 实现的行为证据；不假设 verify_checksums 内部变量命名，兼容 R1 引导设计）。

    当前状态：agate_common 尚无 compute_sha256（迁移前）→ AttributeError（真红灯）。
    """
    module = _load_script_module(agate_scripts, "agate_install_offline_bdd1", "install-offline.py")
    import agate_common

    bundle = tmp_path / "bundle"
    agate_dir = bundle / "agate"
    agate_dir.mkdir(parents=True)
    (agate_dir / "sample.txt").write_text("# sample\n", encoding="utf-8")

    checksum = agate_common.compute_sha256(agate_dir)
    manifest = {
        "version": "v0.48.0",
        "platform": "linux-x86_64",
        "components": {"agate": {"path": "agate", "sha256": checksum}},
    }

    mismatched = module.verify_checksums(manifest, str(bundle))
    assert mismatched == []


def test_r1_ensure_agate_common_bootstraps_when_yaml_unavailable(tmp_path, agate_scripts, monkeypatch):
    """R1（P2-design.md §1.3「回归覆盖」①，列入 BDD-2 范围）：yaml 不可导入时，
    install-offline.py 的 _ensure_agate_common(bundle_dir, manifest) 应能引导安装 pyyaml
    （mock subprocess.run 的 pip install --no-index --find-links <bundle>/wheels pyyaml）后
    返回可用的 agate_common 模块引用（具备 compute_sha256）。

    先确保 agate_common 已在本进程缓存（避免 yaml 不可用模拟期间，其自身模块级 `import yaml`
    真的被重新触发从而 sys.exit(1)，导致进程级副作用而非测试目标本身的红灯）。

    当前状态：install-offline.py 尚无 _ensure_agate_common → AttributeError（真红灯）。
    """
    module = _load_script_module(
        agate_scripts, "agate_install_offline_r1a", "install-offline.py"
    )
    import agate_common as _agate_common  # noqa: F401  # 确保已缓存，规避测试顺序依赖

    bundle = tmp_path / "bundle"
    wheels = bundle / "wheels"
    wheels.mkdir(parents=True)
    pyyaml_whl = wheels / "pyyaml-6.0.2-py3-none-any.whl"
    pyyaml_whl.write_bytes(b"fake pyyaml wheel data")
    manifest = {
        "version": "v0.48.0",
        "platform": "linux-x86_64",
        "components": {
            "pyyaml": {
                "path": "wheels/pyyaml-6.0.2-py3-none-any.whl",
                "sha256": _sha256_bytes(pyyaml_whl.read_bytes()),
            }
        },
    }

    pip_calls = []

    def fake_run(argv, **kwargs):
        pip_calls.append([str(a) for a in argv])
        return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")

    monkeypatch.setitem(sys.modules, "yaml", None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = module._ensure_agate_common(str(bundle), manifest)

    assert result is not None
    assert hasattr(result, "compute_sha256")
    assert pip_calls, "yaml 不可用时应触发 pip install 引导安装 pyyaml"
    assert any("pyyaml" in a for a in pip_calls[-1])
    assert "--no-index" in pip_calls[-1]


def test_r1_ensure_agate_common_rejects_pyyaml_checksum_mismatch_before_pip_install(
    tmp_path, agate_scripts, monkeypatch, capsys
):
    """R1（P2-design.md §1.3「回归覆盖」②，列入 BDD-2 范围）：pyyaml wheel checksum 与
    manifest 不匹配时，_ensure_agate_common 必须在执行 pip install 之前就拒绝（stderr 报错 +
    非成功返回），且全程 mock 的 subprocess.run 未被调用——用"未被调用"断言校验"校验先于安装"
    这一顺序本身，而不只是校验最终结果（BDD-26 字面不变量"checksum 不匹配则不落地"对 pyyaml
    组件同样成立）。

    当前状态：install-offline.py 尚无 _ensure_agate_common → AttributeError（真红灯）。
    """
    module = _load_script_module(
        agate_scripts, "agate_install_offline_r1b", "install-offline.py"
    )
    import agate_common as _agate_common  # noqa: F401  # 确保已缓存，规避测试顺序依赖

    bundle = tmp_path / "bundle"
    wheels = bundle / "wheels"
    wheels.mkdir(parents=True)
    pyyaml_whl = wheels / "pyyaml-6.0.2-py3-none-any.whl"
    pyyaml_whl.write_bytes(b"fake pyyaml wheel data")
    manifest = {
        "version": "v0.48.0",
        "platform": "linux-x86_64",
        "components": {
            "pyyaml": {
                "path": "wheels/pyyaml-6.0.2-py3-none-any.whl",
                # 篡改：与真实 wheel 内容不匹配的 sha256（模拟被篡改/损坏的 pyyaml 组件）
                "sha256": "0" * 64,
            }
        },
    }

    subprocess_run_calls = []

    def fake_run(argv, **kwargs):
        subprocess_run_calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")

    monkeypatch.setitem(sys.modules, "yaml", None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = module._ensure_agate_common(str(bundle), manifest)

    err = capsys.readouterr().err
    assert result is None
    assert "pyyaml" in err
    assert not subprocess_run_calls, "checksum 不匹配时 pip install 不应被执行（校验先于安装）"


def test_manifest_absolute_path_rejected(tmp_path, agate_scripts, capsys):
    """rev2 CRITICAL-3：恶意 manifest 组件 `path` 为绝对路径 → 拒绝安装。"""
    module = _load_script_module(agate_scripts, "agate_install_offline", "install-offline.py")
    bundle = _make_bundle(tmp_path)
    mpath = bundle / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["components"]["evil"] = {
        "path": "/etc/hostname",
        "sha256": "0" * 64,
    }
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    dest = tmp_path / "dest"

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    err = capsys.readouterr().err
    assert code != 0
    assert "path" in err
    assert not dest.exists()


# ---------------------------------------------------------------------------
# TAG0037 B2：BDD-9 / BDD-10（真实 pack 产物离线安装后解析成功；T-15 bundle 内入口）
# ---------------------------------------------------------------------------


@_posix_only
def test_bdd_9_offline_install_from_bundle_internal_entry_then_resolve(tmp_path, agate_scripts, synth):
    """BDD-9 + T-15：以 **bundle 内入口**（真实内网机器的调用方式）运行 install-offline → agate-resolve exit 0，
    AGATE_ROOT == <dest>/vX.Y.Z/agate 且其 scripts/agate-resolve.py 存在；无 agate/agate 双层；_protocol_root(vdir) 不再原样返回 vdir；
    安装前后 bundle 不被改写（无字节码）、vdir/agate 无 __pycache__。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "dest"
    before_bundle = H.snapshot_tree(bundle, ignore_bytecode=False)

    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest, entry=bundle / "agate" / "scripts" / "install-offline.py")
    assert proc.returncode == 0, f"bundle 内入口安装应成功: {proc.stderr}"

    vdir = dest / H.MAIN_TAG
    assert H.file_set(vdir) == synth.expected_package(H.MAIN_TAG), "vX.Y.Z/ 应恰为本体包集合（不含 wheels/ manifest.json 等安装输入物）"
    assert not (vdir / "agate" / "agate").exists(), "不得出现 agate/agate 双层嵌套（P0 机理）"
    assert not (vdir / ".installed-version").exists() and not (dest / ".agate-root").exists()
    assert H.snapshot_tree(bundle, ignore_bytecode=False) == before_bundle, "安装不得改写 bundle（含不得写字节码，eng B-1）"
    assert not [p for p in (vdir / "agate").rglob("*") if H.is_bytecode_path(p.relative_to(vdir))], "vdir/agate 安装态无字节码"

    common = H.load_project_module(agate_scripts, "agate_common.py", "agate_common")
    assert os.path.normpath(common._protocol_root(str(vdir))) == os.path.normpath(str(vdir / "agate")), "_protocol_root(vdir) 不得原样返回 vdir"

    res = H.run_tool([sys.executable, dest / "scripts" / "agate-resolve.py"], env=H.tool_env(tmp_path / "home-run", agate_home=dest), cwd=tmp_path)
    assert res.returncode == 0, res.stderr
    kv = dict(line.split("=", 1) for line in res.stdout.splitlines() if "=" in line)
    assert kv["AGATE_ROOT"] == str((vdir / "agate").resolve())
    assert (Path(kv["AGATE_ROOT"]) / "scripts" / "agate-resolve.py").is_file()
    assert kv["AGATE_VERSION"] == H.MAIN_TAG


@_posix_only
def test_bdd_10_dest_defaults_to_agate_home_and_fills_version_root_structure(tmp_path, agate_scripts):
    """BDD-10：仅设 AGATE_HOME（HOME 指向另一空目录），不传 --dest-root → 装到 AGATE_HOME（不落 HOME/.agate），
    含 latest、current → latest、根 scripts/agate-install.py；`agate-install.py --check` 可运行。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    agate_home = tmp_path / "ah"
    home = tmp_path / "other-home"
    home.mkdir()
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, agate_home=agate_home, home=home)
    assert proc.returncode == 0, proc.stderr
    assert (agate_home / H.MAIN_TAG / "agate" / "scripts").is_dir()
    assert not (home / ".agate").exists(), "不得落到 HOME/.agate"
    assert os.readlink(str(agate_home / "latest")) == H.MAIN_TAG
    assert os.readlink(str(agate_home / "current")) == "latest", "current 不再直指 vX.Y.Z"
    root_entry = agate_home / "scripts" / "agate-install.py"
    assert root_entry.is_file()
    chk = H.run_tool([sys.executable, root_entry, "--check"], env=H.tool_env(home, agate_home=agate_home))
    assert chk.returncode == 0, chk.stdout + chk.stderr


# ---------------------------------------------------------------------------
# BDD-11（sentinel + T-2 红灯回放）/ BDD-12（旧格式 bundle 被拒绝）
# ---------------------------------------------------------------------------


@_posix_only
def test_bdd_11_bundle_helper_output_is_body_not_whole_repo(tmp_path):
    """BDD-11 ①②：`_make_bundle`（经真实 pack）产出的 bundle/agate/ 顶层含 scripts/ 与 WORKFLOW.md，且不含 agate-workspace / docs / site。"""
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG)
    H.assert_real_bundle_layout(bundle)
    top = {p.name for p in (bundle / "agate").iterdir()}
    assert {"scripts", "WORKFLOW.md"} <= top
    assert not ({"agate-workspace", "docs", "site", "archived", ".github"} & top)


@_posix_only
def test_bdd_11_t2_replay_old_packer_layout_fails_the_sentinel(tmp_path, synth):
    """T-2 红灯回放（永久变异测试）：旧 packer 行为构造器（真实 git worktree add 整仓检出到 bundle/agate）→ sentinel 必须抛 AssertionError。"""
    plat = _host_plat()
    legacy = H.make_legacy_worktree_bundle(tmp_path, synth.bare, H.MAIN_TAG, plat)
    with pytest.raises(AssertionError):
        H.assert_real_bundle_layout(legacy)


@_posix_only
@pytest.mark.parametrize("dest_precreated", [False, True], ids=["bdd12-1-dest-absent", "bdd12-2-dest-empty-dir"])
def test_bdd_12_old_format_bundle_rejected_and_nothing_written(dest_precreated, tmp_path, agate_scripts, synth):
    """BDD-12 + T-2：旧格式 bundle（bundle/agate 为整仓树、agate/agate/scripts 存在，manifest 校验和自洽）→ exit 1，
    stderr 指明"旧格式（agate/agate/scripts 双层嵌套）请用新版 agate-pack-offline.py 重新打包"，dest 下不产生任何 vX.Y.Z/ 与 current。"""
    plat = _host_plat()
    legacy = H.make_legacy_worktree_bundle(tmp_path, synth.bare, H.MAIN_TAG, plat)
    assert (legacy / "agate" / "agate" / "scripts").is_dir(), "Given：旧格式（双层嵌套）"
    dest = tmp_path / "dest"
    if dest_precreated:
        dest.mkdir()
    before = _snap(dest)
    proc, _log = _run_offline(agate_scripts, tmp_path, legacy, "--dest-root", dest)
    assert proc.returncode == 1, f"旧格式应 exit 1: rc={proc.returncode} {proc.stderr}"
    assert "agate/agate/scripts" in proc.stderr
    assert "重新打包" in proc.stderr and "agate-pack-offline" in proc.stderr
    assert _snap(dest) == before, "拒绝而非自动归一化：dest 下不得产生任何目录 / 指针"


# ---------------------------------------------------------------------------
# BDD-33：软链 dest fail-closed（T-14 参数化）+ 不误伤
# ---------------------------------------------------------------------------


@_posix_only
@pytest.mark.parametrize("variant", _VARIANTS, ids=_VARIANT_IDS)
@pytest.mark.parametrize("form", ["dest-root-arg", "agate-home-env"], ids=["bdd33-1-dest-root", "bdd33-2-agate-home"])
def test_bdd_33_offline_install_symlink_dest_fail_closed(form, variant, tmp_path, agate_scripts):
    """BDD-33 + T-14：--dest-root / AGATE_HOME 解析到软链（含 L/ L// L/. L/.. 变体）+ 合法新格式 bundle → exit 1、三步迁移片段，
    软链目标目录内容 / 金丝雀不变（无 vX.Y.Z/、无 current），物理父目录不新增条目。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    link, target = _symlink_dest(tmp_path)
    before = H.snapshot_tree(target)
    parent_listing = sorted(os.listdir(str(target.parent)))
    v = _variant(link, variant)
    if form == "dest-root-arg":
        proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", v)
    else:
        proc, _log = _run_offline(agate_scripts, tmp_path, bundle, agate_home=v)
    assert proc.returncode == 1, f"软链基址应 fail-closed exit 1: rc={proc.returncode}\n{proc.stderr}"
    for key, rx in _STEP_RES.items():
        assert rx.search(proc.stderr), f"stderr 缺三步迁移片段 {key}: {proc.stderr}"
    assert H.snapshot_tree(target) == before
    assert not (target / H.MAIN_TAG).exists() and not (target / "current").exists()
    assert sorted(os.listdir(str(target.parent))) == parent_listing


@_posix_only
@pytest.mark.parametrize("kind", ["existing-empty-dir", "nonexistent-new-dir"], ids=["bdd33-3-existing-dir", "bdd33-4-new-dir"])
def test_bdd_33_regular_dest_root_is_not_rejected(kind, tmp_path, agate_scripts):
    """BDD-33 不误伤：--dest-root 指向普通目录 / 不存在的新目录时行为不受影响（exit 0，版本目录就位）。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "plain-dest"
    if kind == "existing-empty-dir":
        dest.mkdir()
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 0, proc.stderr
    assert (dest / H.MAIN_TAG / "agate" / "scripts").is_dir()


# ---------------------------------------------------------------------------
# T-19：P 集合对账（manifest `files` vs 磁盘）；G-5：契约外顶层文件不拷
# ---------------------------------------------------------------------------


def _resync_agate_checksum(bundle):
    """改动 bundle/agate 后重算 manifest 中 agate 组件的目录哈希——保证 checksum 自洽，使拒绝只可能来自 P 集合对账。"""
    mpath = bundle / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["components"]["agate"]["sha256"] = H.expected_component_sha256(bundle / "agate")
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


@_posix_only
@pytest.mark.parametrize("mutation", ["extra-file", "missing-file", "renamed-file"], ids=["t19-1-extra", "t19-2-missing", "t19-3-renamed"])
def test_t19_p_set_reconciliation_rejects_and_leaves_dest_unchanged(mutation, tmp_path, agate_scripts):
    """T-19：bundle 内多一个 / 少一个 / 改名一个 agate/** 文件，manifest `files` 对账均使 install-offline exit 1 且 dest 不变（不产生目录）。
    多 / 少的变体重算目录哈希，改名变体的目录哈希本就不变（哈希不含路径名——这正是 `files` 清单要弥补的局限，cso F-4 / F-6）。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    target = bundle / "agate" / "UPGRADING.md"
    assert target.is_file()
    if mutation == "extra-file":
        (bundle / "agate" / "zz-extra.md").write_text("extra\n", encoding="utf-8")
        _resync_agate_checksum(bundle)
        offending = "zz-extra.md"
    elif mutation == "missing-file":
        os.unlink(str(target))
        _resync_agate_checksum(bundle)
        offending = "UPGRADING.md"
    else:
        os.rename(str(target), str(bundle / "agate" / "UPGRADING-renamed.md"))
        offending = "UPGRADING"
    dest = tmp_path / "dest"
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 1, f"P 集合对账失败应 exit 1: rc={proc.returncode} {proc.stderr}"
    assert offending in proc.stderr, f"stderr 应指出不一致的路径 {offending}: {proc.stderr}"
    assert not dest.exists(), "对账先于任何写入：dest 不变"


@_posix_only
def test_t19_bundle_top_level_file_outside_contract_is_not_copied(tmp_path, agate_scripts):
    """T-6 / G-5：bundle 顶层出现契约外文件（extra.sh，不在 manifest.files 中）→ 不被拷入 vdir，并给出告警。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    (bundle / "extra.sh").write_text("#!/bin/sh\necho pwned\n", encoding="utf-8")
    dest = tmp_path / "dest"
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 0, proc.stderr
    assert not (dest / H.MAIN_TAG / "extra.sh").exists()
    assert "extra.sh" in proc.stderr, "契约外文件应给出告警"
    assert not (dest / H.MAIN_TAG / "wheels").exists() and not (dest / H.MAIN_TAG / "manifest.json").exists()


@_posix_only
@pytest.mark.parametrize("kind", ["symlink-member", "symlink-root-file"], ids=["t6-1-agate-member-symlink", "t6-2-root-file-symlink"])
def test_t6_bundle_with_symlink_member_is_rejected(kind, tmp_path, agate_scripts):
    """T-6 / cso F-6：bundle 内的软链成员（agate/** 或登记根文件被换成软链）→ install-offline 拒绝（exit 1），dest 不变。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    victim = bundle / "agate" / "WORKFLOW.md" if kind == "symlink-member" else bundle / "LICENSE"
    outside = tmp_path / "outside.txt"
    outside.write_bytes(victim.read_bytes())  # 内容与原文件逐字节相同：checksum 不变，只有软链检查能拒绝
    os.unlink(str(victim))
    os.symlink(str(outside), str(victim))
    dest = tmp_path / "dest"
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 1, proc.stderr
    assert not dest.exists()


# ---------------------------------------------------------------------------
# T-16：换位失败注入（旧版完整或新版完整；latest/current 指针与目录一致）
# ---------------------------------------------------------------------------


def _seed_existing_install(dest, version=H.MAIN_TAG, older="v0.72.5", current_is_dir=False):
    """预置一个已装版本 + 指针（POSIX 软链）：dest/<older>、dest/<version>（含哨兵）；latest → version、current → latest。"""
    for v in (older, version):
        (dest / v / "agate" / "scripts").mkdir(parents=True)
        (dest / v / "agate" / "scripts" / "README.md").write_text(f"# {v}\n", encoding="utf-8")
    (dest / version / "agate" / "OLD-SENTINEL.txt").write_text("old-content\n", encoding="utf-8")
    if current_is_dir:
        os.symlink(older, str(dest / "latest"))
        (dest / "current").mkdir()
        (dest / "current" / "keep.txt").write_text("keep\n", encoding="utf-8")
    else:
        os.symlink(version, str(dest / "latest"))
        os.symlink("latest", str(dest / "current"))


def _under(root, path):
    root = os.path.abspath(str(root)) + os.sep
    return os.path.abspath(str(path)).startswith(root)


def _fail_nth_rename(monkeypatch, root, nth):
    """让"涉及 root 的第 nth 次 rename / replace"抛 OSError（实现无关：覆盖 os.rename 与 os.replace；shutil.move 也经 os.rename）。"""
    state = {"n": 0}

    def wrap(real):
        def inner(src, dst, *a, **k):
            if _under(root, src) or _under(root, dst):
                state["n"] += 1
                if state["n"] == nth:
                    raise OSError(errno.EIO, "注入的换位失败")
            return real(src, dst, *a, **k)

        return inner

    monkeypatch.setattr(os, "rename", wrap(os.rename))
    monkeypatch.setattr(os, "replace", wrap(os.replace))
    return state


@_posix_only
@pytest.mark.parametrize("nth", [1, 2], ids=["t16-1-step1-backup-rename", "t16-2-step2-final-rename"])
def test_t16_swap_failure_keeps_old_version_complete_and_pointers_unchanged(nth, tmp_path, agate_scripts, monkeypatch):
    """T-16：已存在旧版本时，换位第一步（旧目录 → 备份容器）/ 第二步（新 pkg → 目标）分别注入 OSError：
    exit 非 0；旧版本目录逐字节完整（哨兵在）；latest / current 指针不变；不出现新版本内容。"""
    module = _load_script_module(agate_scripts, "agate_install_offline_t16", "install-offline.py")
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG)
    dest = tmp_path / "dest"
    _seed_existing_install(dest)
    _use_pip_shim(monkeypatch, tmp_path)
    old_v = H.snapshot_tree(dest / H.MAIN_TAG, ignore_bytecode=False)
    old_ptr = _pointer_state(dest)
    state = _fail_nth_rename(monkeypatch, dest, nth)

    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])

    assert state["n"] >= nth, "换位应至少发生 nth 次 rename（实现须用 os.rename/os.replace 换位）"
    assert code != 0
    assert H.snapshot_tree(dest / H.MAIN_TAG, ignore_bytecode=False) == old_v, "旧版本必须完整（含哨兵）"
    assert (dest / H.MAIN_TAG / "agate" / "OLD-SENTINEL.txt").read_text(encoding="utf-8") == "old-content\n"
    assert _pointer_state(dest) == old_ptr, "latest / current 指针必须与还原后的目录一致"


@_posix_only
def test_t16_fresh_install_final_rename_failure_leaves_no_half_install(tmp_path, agate_scripts, monkeypatch):
    """T-16（全新安装分支）：目标不存在时，pkg → 目标的换位失败 → exit 非 0，dest 下无版本目录、无指针（绝不出现半装）。"""
    module = _load_script_module(agate_scripts, "agate_install_offline_t16b", "install-offline.py")
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG)
    dest = tmp_path / "dest"
    dest.mkdir()
    _use_pip_shim(monkeypatch, tmp_path)
    state = _fail_nth_rename(monkeypatch, dest, 1)
    with mock.patch.object(module, "get_current_platform", return_value="linux-x86_64"):
        code = module.main([str(bundle), "--dest-root", str(dest)])
    assert state["n"] >= 1
    assert code != 0
    assert not (dest / H.MAIN_TAG).exists()
    assert _pointer_state(dest) == {"latest": None, "current": None}


@_posix_only
def test_t16_adopt_failure_restores_old_directory_and_partially_written_pointers(tmp_path, agate_scripts):
    """T-16 / eng N-2：换位成功后 `--adopt` 失败（current 位置是真实目录 → adopt 写指针失败，此前已改写的 latest 须还原）→
    exit 1；旧版本目录逐字节还原；latest 仍指向原值；current 目录原样；stderr 说明版本目录与指针均已还原。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "dest"
    _seed_existing_install(dest, current_is_dir=True)
    old_v = H.snapshot_tree(dest / H.MAIN_TAG, ignore_bytecode=False)
    old_ptr = _pointer_state(dest)
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 1, proc.stderr
    assert "Traceback" not in proc.stderr
    assert H.snapshot_tree(dest / H.MAIN_TAG, ignore_bytecode=False) == old_v
    assert _pointer_state(dest) == old_ptr
    assert old_ptr["latest"] == ("link", "v0.72.5"), "Given：latest 原指向 v0.72.5"
    assert "还原" in proc.stderr


@_posix_only
def test_t16_pip_install_failure_leaves_dest_untouched(tmp_path, agate_scripts):
    """P2 §3.4 步骤 6：pip install 失败（有系统副作用，排在拷贝之后、换位之前）→ exit 1，dest 逐项不变（临时目录被丢弃）。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "dest"
    _seed_existing_install(dest)
    before = _snap(dest)
    ptr = _pointer_state(dest)
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest, pip_mode="fail-install")
    assert proc.returncode == 1
    assert _snap(dest) == before, "dest 不变（含无遗留 .agate-tmp-* 容器）"
    assert _pointer_state(dest) == ptr


@_posix_only
def test_replace_existing_version_dir_recovers_a_damaged_install(tmp_path, agate_scripts):
    """S-16 / D-6：对已存在（受损）的 vX.Y.Z/ 重装 → 被完整替换（旧内容消失、包集合恢复），备份容器在 adopt 成功后清除。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "dest"
    damaged = dest / H.MAIN_TAG
    (damaged / "agate").mkdir(parents=True)
    (damaged / "agate" / "junk.txt").write_text("damaged\n", encoding="utf-8")
    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 0, proc.stderr
    assert not (damaged / "agate" / "junk.txt").exists()
    assert (damaged / "agate" / "scripts").is_dir()
    assert not [n for n in os.listdir(str(dest)) if n.startswith((".agate-bak-", ".agate-tmp-"))], "成功后不遗留备份 / 工作容器"


# ---------------------------------------------------------------------------
# T-23：清扫只删自己的（cso N-1，数据安全，必测）
# ---------------------------------------------------------------------------


def _write_marker(container, text, age_seconds=0):
    m = Path(container) / _MARKER_NAME
    m.write_text(text, encoding="utf-8")
    if age_seconds:
        t = time.time() - age_seconds
        os.utime(str(m), (t, t))
    return m


def _populate_foreign_entries(root):
    """在版本根预置 T-23 的用户 / 无标记 / 伪标记 / 软链 / 备份 / 新鲜容器条目；返回 {条目名: 快照函数}。"""
    root = Path(root)
    ext = root.parent / "external-dir"
    ext.mkdir(exist_ok=True)
    (ext / "precious.txt").write_text("precious\n", encoding="utf-8")
    outside_marker = root.parent / "outside-marker.txt"
    outside_marker.write_text(_TMP_MARKER, encoding="utf-8")

    for name in ("v0.73.0.bak-user", "v0.73.0.tmp-x", ".agate-tmp-user"):
        (root / name).mkdir()
        (root / name / "user-data.txt").write_text(f"data of {name}\n", encoding="utf-8")
    fake_link_marker = root / ".agate-tmp-fake-linkmarker"  # 标记文件是软链（指向内容看似有效的外部文件）
    fake_link_marker.mkdir()
    os.symlink(str(outside_marker), str(fake_link_marker / _MARKER_NAME))
    t_old = time.time() - 7200
    os.utime(str(outside_marker), (t_old, t_old))
    fake_content = root / ".agate-tmp-fake-content"  # 标记内容不符（且已过期）
    fake_content.mkdir()
    _write_marker(fake_content, "hello world\n", age_seconds=7200)
    (fake_content / "data.txt").write_text("fake content dir\n", encoding="utf-8")
    os.symlink(str(ext), str(root / ".agate-tmp-link"))  # 指向外部目录的软链
    (root / "v0.72.5" / "agate").mkdir(parents=True)  # 备份容器对应版本存在 → recover_backups 只提示、不移动
    (root / "v0.72.5" / "agate" / "here.txt").write_text("v0.72.5\n", encoding="utf-8")
    bak = root / ".agate-bak-v0.72.5-AAAA"  # 有效标记的备份容器：也绝不删
    (bak / "old" / "agate").mkdir(parents=True)
    (bak / "old" / "agate" / "old.txt").write_text("backup data\n", encoding="utf-8")
    _write_marker(bak, _BAK_MARKER, age_seconds=7200)
    young = root / ".agate-tmp-young"  # 有效标记但不足 1 小时（可能是并发安装的活跃目录）
    (young / "pkg").mkdir(parents=True)
    (young / "pkg" / "wip.txt").write_text("in progress\n", encoding="utf-8")
    _write_marker(young, _TMP_MARKER, age_seconds=0)
    return ext


_FOREIGN = [
    "v0.73.0.bak-user",
    "v0.73.0.tmp-x",
    ".agate-tmp-user",
    ".agate-tmp-fake-linkmarker",
    ".agate-tmp-fake-content",
    ".agate-tmp-link",
    "v0.72.5",
    ".agate-bak-v0.72.5-AAAA",
    ".agate-tmp-young",
]


def _entry_state(root, name):
    p = Path(root) / name
    if p.is_symlink():
        return ("link", os.readlink(str(p)))
    return ("tree", H.snapshot_tree(p, ignore_bytecode=False))


@_posix_only
def test_t23_install_sweeps_only_own_expired_containers_and_keeps_everything_else(tmp_path, agate_scripts):
    """T-23（数据安全）：版本根内预置用户目录 v0.73.0.bak-user / v0.73.0.tmp-x、无标记的 .agate-tmp-user、标记为软链或内容不符的 .agate-tmp-*、
    指向外部目录的软链 .agate-tmp-link、有标记的 .agate-bak-*、不足 1 小时的有标记容器——跑一次安装（触发 sweep_stale / recover_backups）后
    **全部原样保留**（内容哈希不变、外部目录不变）；只有「前缀 + 真实目录 + 有效标记 + 标记 mtime > 1h」的本工具容器被清扫。"""
    plat = _host_plat()
    bundle = _make_bundle(tmp_path, version=H.MAIN_TAG, platform=plat)
    dest = tmp_path / "dest"
    dest.mkdir()
    ext = _populate_foreign_entries(dest)
    expired = dest / ".agate-tmp-v0.73.0-EXPIRED"
    (expired / "pkg").mkdir(parents=True)
    (expired / "pkg" / "x.txt").write_text("stale\n", encoding="utf-8")
    _write_marker(expired, _TMP_MARKER, age_seconds=7200)
    before = {n: _entry_state(dest, n) for n in _FOREIGN}
    ext_before = H.snapshot_tree(ext, ignore_bytecode=False)

    proc, _log = _run_offline(agate_scripts, tmp_path, bundle, "--dest-root", dest)
    assert proc.returncode == 0, proc.stderr

    for name in _FOREIGN:
        assert os.path.lexists(str(dest / name)), f"{name} 被删除（清扫只许删除本工具的过期容器）"
        assert _entry_state(dest, name) == before[name], f"{name} 内容被改动"
    assert H.snapshot_tree(ext, ignore_bytecode=False) == ext_before, "软链指向的外部目录不得被清扫"
    assert not os.path.lexists(str(expired)), "有标记且 > 1h 的本工具容器应被清扫"
    assert (dest / H.MAIN_TAG / "agate" / "scripts").is_dir(), "安装本身应成功"


# ---------------------------------------------------------------------------
# agate_package 换位 / 清扫库函数（P2 §3.2；A 组 §1 明确归 B2 批覆盖）
# ---------------------------------------------------------------------------


def _pkg(agate_scripts):
    return H.load_project_module(agate_scripts, "agate_package.py", "agate_package")


def _first_line(p):
    with open(str(p), encoding="utf-8") as fh:
        return fh.readline().strip()


@_posix_only
def test_lib_make_work_dir_creates_marked_private_container(tmp_path, agate_scripts):
    """R-8：make_work_dir(root, ver) = 版本根内专属命名（`.agate-tmp-<ver>-…`，不匹配版本号正则）的私有（0700）容器，
    立即写入专属标记文件（首行 `agate-package/1 kind=tmp`，普通文件）。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    root.mkdir()
    container = Path(pkg.make_work_dir(str(root), "v0.73.0"))
    assert container.is_dir() and container.parent == root
    assert container.name.startswith(".agate-tmp-v0.73.0-")
    assert not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", container.name)
    marker = container / _MARKER_NAME
    assert marker.is_file() and not marker.is_symlink()
    assert _first_line(marker).startswith("agate-package/1 kind=tmp")
    assert (container.stat().st_mode & 0o777) == 0o700


@_posix_only
def test_lib_sweep_stale_only_removes_marked_expired_tmp_containers(tmp_path, agate_scripts):
    """T-23（库层）：sweep_stale 不按名字模式删，只删「前缀 + 真实目录 + 有效标记 + >1h」的容器。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    root.mkdir()
    ext = _populate_foreign_entries(root)
    expired = root / ".agate-tmp-v0.73.0-EXPIRED"
    (expired / "pkg").mkdir(parents=True)
    (expired / "pkg" / "x.txt").write_text("stale\n", encoding="utf-8")
    _write_marker(expired, _TMP_MARKER, age_seconds=7200)
    before = {n: _entry_state(root, n) for n in _FOREIGN}
    ext_before = H.snapshot_tree(ext, ignore_bytecode=False)

    pkg.sweep_stale(str(root))

    assert not os.path.lexists(str(expired))
    for name in _FOREIGN:
        assert os.path.lexists(str(root / name)), f"{name} 被 sweep_stale 删除"
        assert _entry_state(root, name) == before[name]
    assert H.snapshot_tree(ext, ignore_bytecode=False) == ext_before


@_posix_only
def test_lib_recover_backups_only_renames_and_never_deletes(tmp_path, agate_scripts, capsys):
    """R-8：recover_backups——vX.Y.Z 缺失时把备份容器内 old/ 改名挪回（不删任何数据）；vX.Y.Z 存在时仅 stderr 提示遗留备份路径。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    root.mkdir()
    lost = root / ".agate-bak-v0.73.0-BBBB"  # v0.73.0 缺失 → 应挪回
    (lost / "old" / "agate").mkdir(parents=True)
    (lost / "old" / "agate" / "precious.txt").write_text("only copy\n", encoding="utf-8")
    _write_marker(lost, "agate-package/1 kind=bak version=v0.73.0 pid=1\n", age_seconds=7200)
    kept = root / ".agate-bak-v0.72.5-AAAA"  # v0.72.5 存在 → 仅提示
    (kept / "old" / "agate").mkdir(parents=True)
    (kept / "old" / "agate" / "old.txt").write_text("backup\n", encoding="utf-8")
    _write_marker(kept, _BAK_MARKER, age_seconds=7200)
    (root / "v0.72.5" / "agate").mkdir(parents=True)
    (root / "v0.72.5" / "agate" / "live.txt").write_text("live\n", encoding="utf-8")
    kept_before = H.snapshot_tree(kept, ignore_bytecode=False)
    live_before = H.snapshot_tree(root / "v0.72.5", ignore_bytecode=False)

    pkg.recover_backups(str(root))

    assert (root / "v0.73.0" / "agate" / "precious.txt").read_text(encoding="utf-8") == "only copy\n", "崩溃后唯一完整的旧版本应被挪回"
    assert H.snapshot_tree(kept, ignore_bytecode=False) == kept_before, "vX 存在时备份容器原样保留"
    assert H.snapshot_tree(root / "v0.72.5", ignore_bytecode=False) == live_before
    assert ".agate-bak-v0.72.5-AAAA" in capsys.readouterr().err, "应在 stderr 提示遗留备份路径"


@_posix_only
def test_lib_swap_in_fresh_replace_rollback_and_discard(tmp_path, agate_scripts):
    """swap_in / rollback_swap / discard_backup（P2 §3.2）：
    ① 目标不存在：pkg 改名为目标，返回 None，工作容器被清空删除；
    ② 目标存在：旧目录移入带标记的备份容器 old/，新内容就位，返回备份容器；
    ③ rollback_swap：新目录挪走、旧目录还原；④ discard_backup：仅删本进程创建、标记有效的备份容器。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    root.mkdir()

    def container_with(content):
        c = Path(pkg.make_work_dir(str(root), "v0.73.0"))
        (c / "pkg").mkdir()
        (c / "pkg" / "new.txt").write_text(content, encoding="utf-8")
        return c

    final = root / "v0.73.0"
    c1 = container_with("first\n")
    assert pkg.swap_in(str(c1), str(final)) is None
    assert (final / "new.txt").read_text(encoding="utf-8") == "first\n"
    assert not c1.exists(), "换位后空工作容器应被删除"

    (final / "old.txt").write_text("old\n", encoding="utf-8")
    c2 = container_with("second\n")
    backup = pkg.swap_in(str(c2), str(final))
    assert backup is not None
    backup = Path(backup)
    assert (final / "new.txt").read_text(encoding="utf-8") == "second\n"
    assert not (final / "old.txt").exists()
    assert (backup / "old" / "old.txt").read_text(encoding="utf-8") == "old\n"
    assert _first_line(backup / _MARKER_NAME).startswith("agate-package/1 kind=bak")

    pkg.rollback_swap(str(backup), str(final))
    assert (final / "old.txt").read_text(encoding="utf-8") == "old\n"
    assert (final / "new.txt").read_text(encoding="utf-8") == "first\n", "回滚后目标位置应是旧目录内容（含第一次换位写入的 new.txt=first），而非 second"

    c3 = container_with("third\n")
    backup2 = pkg.swap_in(str(c3), str(final))
    assert backup2 is not None and Path(backup2).is_dir()
    pkg.discard_backup(str(backup2))
    assert not Path(backup2).exists(), "adopt 成功后本次创建的备份容器应被删除"
    assert (final / "new.txt").read_text(encoding="utf-8") == "third\n"


@_posix_only
def test_lib_discard_backup_refuses_directories_it_did_not_create(tmp_path, agate_scripts):
    """T-23：discard_backup 拒绝标记不符 / 名字不符 / 不是本工具备份容器的目录（抛异常或忽略均可，但目录必须原样保留）。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    root.mkdir()
    victims = {}
    plain = root / "user-dir"
    plain.mkdir()
    (plain / "u.txt").write_text("u\n", encoding="utf-8")
    victims["user-dir"] = plain
    nomarker = root / ".agate-bak-v0.73.0-NOMK"
    (nomarker / "old").mkdir(parents=True)
    (nomarker / "old" / "d.txt").write_text("d\n", encoding="utf-8")
    victims["no-marker"] = nomarker
    wrongname = tmp_path / "not-a-backup"
    (wrongname / "old").mkdir(parents=True)
    _write_marker(wrongname, _BAK_MARKER)
    (wrongname / "old" / "d.txt").write_text("d\n", encoding="utf-8")
    victims["outside-root-wrong-name"] = wrongname
    before = {k: H.snapshot_tree(v, ignore_bytecode=False) for k, v in victims.items()}
    for path in victims.values():
        with contextlib.suppress(Exception):  # 拒绝可表现为异常，也可表现为静默忽略
            pkg.discard_backup(str(path))
    for key, path in victims.items():
        assert path.exists(), f"discard_backup 不应删除非本工具备份容器: {key}"
        assert H.snapshot_tree(path, ignore_bytecode=False) == before[key]


@_posix_only
@pytest.mark.parametrize("form", ["symlink", "text-file", "absent"], ids=["ptr-symlink", "ptr-text-file", "ptr-absent"])
def test_lib_snapshot_and_restore_pointers_roundtrip(form, tmp_path, agate_scripts):
    """snapshot_pointers / restore_pointers：记录 latest / current 的存在性与形态（软链目标 / 文本内容 / 无），按快照精确还原。"""
    pkg = _pkg(agate_scripts)
    root = tmp_path / "vroot"
    (root / "v0.72.5").mkdir(parents=True)
    (root / "v0.73.0").mkdir()
    if form == "symlink":
        os.symlink("v0.72.5", str(root / "latest"))
        os.symlink("latest", str(root / "current"))
    elif form == "text-file":
        (root / "latest").write_text("v0.72.5\n", encoding="utf-8")
        (root / "current").write_text("latest\n", encoding="utf-8")
    before = _pointer_state(root)
    snap = pkg.snapshot_pointers(str(root))

    for name in ("latest", "current"):  # 破坏现状：删除 / 改写为别的形态
        p = root / name
        if p.is_symlink() or p.is_file():
            os.unlink(str(p))
    os.symlink("v0.73.0", str(root / "latest"))
    (root / "current").write_text("garbage\n", encoding="utf-8")

    pkg.restore_pointers(str(root), snap)
    assert _pointer_state(root) == before
