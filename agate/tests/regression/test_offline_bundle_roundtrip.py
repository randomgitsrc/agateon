# tests/regression/test_offline_bundle_roundtrip.py — 离线包 pack→install→卸载全流程回归
# （TAG0031 DEBT0002 hash 共享迁移，BDD-2；P2-design.md §1.1 簇 A 新增测试 / §3
# gate_commands.P5_offline_bundle 独立 key）。
#
# 覆盖：agate-pack-offline.py 打包 → install-offline.py 安装 → agate-install.py 卸载三步链路，
# `compute_sha256` 迁移到 `agate_common.py` 共享实现后，三步行为与迁移前逐字节一致——
# 打包产出 manifest.json（sha256 字段值不变）、安装 checksum 校验通过、卸载成功移除版本目录，
# 全程无 checksum 不匹配误报（BDD-2 原文验收条件）。
#
# 迁移锚点（保证本文件当前为真红灯，而非"流程本就跑得通"的假绿）：pack/install 两侧的
# `compute_sha256` 必须是 `agate_common.compute_sha256` 同一函数对象（全仓共享单实现，
# 与 BDD-1「全仓 grep def compute_sha256 只有 1 处定义」同一约束的行为面证据）。当前
# pack/install 两侧仍各自本地定义 → identity 不成立，断言失败（真红灯，非语法错误）；
# 迁移落地后该断言转绿，其后的 pack→install→卸载全流程行为不变性断言才真正开始把关回归。
#
# 网络隔离（TAG0037 P3 组 B 修订，P2 §6 T-11 / BDD-11）：pip download / pip install 用 PATH 内 pip shim（占位 wheel，无网络）；
# git 步骤**真实执行**于合成 file:// 上游的 bare 克隆——不再 mock subprocess.run 凭空造 bundle/agate/WORKFLOW.md（同源假设缺陷）。
# HOME 环境变量重定向到 tmp_path（agate-install.py 的 `_find_references` 卸载引用扫描用 os.path.expanduser("~")，必须隔离
# 防触碰真实 ~/.agate）；安装目标 dest_root 同样落在 tmp_path 下，不写 ~/.agate。
# TAG0037 改动：链路 = 真实 pack → sentinel（bundle/agate 是本体）→ install（--adopt）→ **agate-resolve exit 0（BDD-11 ③，新增）** → 卸载；
# `.installed-version` 断言删除（D-7，契约不再登记隐藏元数据）；卸载走 dest_root/scripts 的根入口（无 repo/，BDD-25 ②）。

import json
import os
import sys
from pathlib import Path

import pytest

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="真实 pack 链路需 PATH pip shim（仅 POSIX）")


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)


def _load_script_module(agate_scripts, module_name, filename):
    """从 agate/scripts/ 加载脚本为模块（同 test_agate_pack_offline.py/test_install_offline.py
    既有惯例）；被测模块未实现 → ModuleNotFoundError（B 类红灯）。"""
    return H.load_project_module(agate_scripts, filename, module_name)


def test_bdd_2_pack_install_uninstall_roundtrip_no_behavior_change(
    tmp_path, agate_scripts, monkeypatch, capsys, synth
):
    """BDD-2：hash 合并后 pack → install → 卸载全流程无行为变化（回归）。

    Given 用改造后的 agate-pack-offline.py 对合成 tag 仓库（真实 git 步骤，无网络依赖）打包一个 bundle
    When 依次执行 agate-pack-offline.py 打包 → install-offline.py 安装 → agate-resolve 解析（BDD-11 ③）→
         agate-install.py 卸载该版本
    Then 三步均与改造前行为一致：打包产出 manifest.json（sha256 字段值不变）、安装 checksum
         校验通过、卸载成功移除版本目录，全程无 checksum 不匹配误报；且安装后解析 exit 0
    """
    # ── 迁移锚点：pack/install 两侧的 compute_sha256 必须是 agate_common 共享的同一函数对象 ──
    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    pack_module = _load_script_module(agate_scripts, "agate_pack_offline_rt", "agate-pack-offline.py")
    install_module = _load_script_module(agate_scripts, "agate_install_offline_rt", "install-offline.py")

    import agate_common

    assert pack_module.compute_sha256 is agate_common.compute_sha256, (
        "agate-pack-offline.py 的 compute_sha256 应迁移为 agate_common 共享实现（当前各自本地定义）"
    )
    assert install_module.compute_sha256 is agate_common.compute_sha256, (
        "install-offline.py 的 compute_sha256 应迁移为 agate_common 共享实现（当前各自本地定义）"
    )

    out_dir = tmp_path / "out"
    repo_dir = H.clone_bare(synth.bare, tmp_path / "repo.git")
    dest_root = tmp_path / "dest"
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    shim = H.make_pip_shim(tmp_path / "pipbin")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setenv("PATH", str(shim) + os.pathsep + os.environ.get("PATH", ""))
    for key in ("AGATE_ROOT", "AGATE_HOME", "AGATE_HOOK_COPY_MODE"):
        monkeypatch.delenv(key, raising=False)

    version = "v0.48.0"
    platform = "linux-x86_64"
    bundle = out_dir / f"agate-{version}-{platform}"

    # ── ① pack：真实 git 步骤 + pip shim，本地无网络 ──
    result_bundle = pack_module.pack_offline(version, platform, str(out_dir), str(repo_dir))
    assert Path(result_bundle) == bundle
    H.assert_real_bundle_layout(bundle)  # BDD-11 sentinel：bundle/agate 是本体而非整仓
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for name, comp in manifest["components"].items():
        comp_path = bundle / comp["path"]
        expected = H.expected_component_sha256(comp_path)
        assert comp["sha256"] == expected, (
            f"组件 {name} 的 sha256 应与现状目录/文件 hash 约定逐字节一致（迁移未改变算法）"
        )

    # ── ② install：真实 --adopt 子进程 + pip shim，checksum 校验须通过 ──
    monkeypatch.setattr(install_module, "get_current_platform", lambda: platform)
    code = install_module.main([str(bundle), "--dest-root", str(dest_root)])
    err = capsys.readouterr().err
    assert code == 0, f"安装应成功（无 checksum 不匹配误报），stderr: {err}"
    assert "checksum" not in err.lower(), f"安装阶段不应有 checksum 误报: {err}"
    version_dir = dest_root / version
    assert version_dir.is_dir()
    assert not (version_dir / ".installed-version").exists(), "D-7：不再写 .installed-version"

    # ── ③ resolve（BDD-11 ③）：安装后 agate-resolve exit 0，AGATE_ROOT 为 vX.Y.Z/agate（P0 BUG：旧链路从不调用解析故长期不暴露）──
    resolved = H.run_tool(
        [sys.executable, dest_root / "scripts" / "agate-resolve.py"],
        env=H.tool_env(fake_home, agate_home=dest_root),
        cwd=tmp_path,
    )
    assert resolved.returncode == 0, f"安装后解析应成功: {resolved.stderr}"
    assert f"AGATE_ROOT={(version_dir / 'agate').resolve()}" in resolved.stdout

    # ── ④ 卸载：经 dest_root 根入口（无 repo/），HOME 已隔离到 fake_home，
    #    _find_references 不应因扫到本次安装本身而误判为"仍被引用" ──
    uninstall = H.run_tool(
        [sys.executable, dest_root / "scripts" / "agate-install.py", "--uninstall", version],
        env=H.tool_env(fake_home, agate_home=dest_root),
        cwd=tmp_path,
    )
    assert uninstall.returncode == 0, f"卸载应成功退出（exit 0）: {uninstall.stderr}"
    assert not version_dir.exists(), "卸载后版本目录应被移除"
    assert not (dest_root / "repo").exists(), "离线安装无 repo/，卸载不得凭空创建"
    for name in ("latest", "current"):
        assert not os.path.lexists(str(dest_root / name)), f"卸载最后一个版本后指针 {name} 应清除（不悬空）"
