# tests/unit/test_t43_debt0014_store_placeholder.py — DEBT0014 ⑤（行为级回归）
#
# 缺陷形态（本仓 2026-08-19 登记）：部分 Windows 安装（未关闭「应用执行别名」）下，PATH 上的
# `python3`（有时 `python`）解析到 **Microsoft Store 的占位符可执行文件**——`command -v` /
# `where` 能找到它、有执行位，但**实际执行任意命令一律非零退出**、不解释传入的脚本。
# 后果：3 个 hook 薄壳的探测循环「command -v 命中即用」，于是选中占位符 → exec 失败 →
# **Windows 用户 commit 被阻断**。
#
# 修复（已落地）：探测循环改为**逐候选先做一次可执行性小测试**（`"$c" -c "" || continue`，
# 通用 exit code 判据），命中占位符即跳过并继续下一候选；另加 `AGATE_PYTHON` 显式覆盖。
#
# ⚠️ 本文件补的是 DEBT0014 的 **closure_criteria 第 ⑤ 条**（「新增回归用例覆盖 Store 占位符
#    场景（**模拟**或 Windows CI matrix）」）。此前该债只有**文档断言**测试
#    （`test_windows_python_probe_docs.py` 5 条，只断言文档写了什么），以及本机 Linux 环境
#    **无法触发真实 Store 占位符** —— 即「实现改了但行为无回归锁」，正是本债长期只剩
#    ⑤ 未闭环的原因。本文件用**模拟占位符**（一个 `command -v` 命中但执行非零退出的
#    `python3`）锁住该行为，使其在 Linux CI 上也能验证。
#
# 判据是**行为级**的：断言薄壳最终 exec 的是**真实候选**（可观测的标记物），
# 而非断言源码里有没有某个字符串——后者会被"改了但写错"骗过。
#
# 平台无关：临时目录用 pytest `tmp_path`；不硬编码单平台路径；PATH 拼接用 os.pathsep；
# 标记物用文件而非 stdout（exec 后 stdout 归属会变）。

import os
import stat
from pathlib import Path

import pytest

HOOKS = ("pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh")


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _make_entry_root(tmp_path: Path) -> Path:
    """构造最小「入口根」：<tmp>/scripts/resolve-entry.py（存在即可，薄壳只判存在性）。"""
    entry = tmp_path / "entry"
    (entry / "scripts").mkdir(parents=True)
    (entry / "scripts" / "resolve-entry.py").write_text("# stub\n", encoding="utf-8")
    return entry


def _make_fake_bin(tmp_path: Path, *, placeholder_python3: bool, real_python: bool, marker_dir: Path):
    """构造受控 PATH 目录。

    - placeholder_python3=True：`python3` 是**模拟 Store 占位符**——存在于 PATH、可执行，
      但执行任何命令都非零退出（并在 marker 里记一笔，用于证明它**没有**被最终选中）。
    - real_python=True：`python` 是**可用的**候选——写标记物后 exit 0，用于证明薄壳回退到了它。
    """
    fake = tmp_path / "bin"
    fake.mkdir()
    # 兜底：PATH 里仍需能找 system 工具（dirname/readlink/tr 等）
    if placeholder_python3:
        _write_exe(
            fake / "python3",
            "#!/bin/sh\n"
            f'echo used > "{marker_dir}/placeholder-python3-was-executed"\n'
            # 模拟 Store 占位符：不解释脚本、一律非零退出
            "exit 9009\n",
        )
    if real_python:
        _write_exe(
            fake / "python",
            "#!/bin/sh\n"
            f'echo used > "{marker_dir}/real-python-was-executed"\n'
            "exit 0\n",
        )
    return fake


@pytest.mark.windows_smoke
def test_t43_d14_store_placeholder_is_skipped_and_real_python_used(
    agate_scripts, bash, tmp_path
):
    """核心行为：`python3` 是 Store 占位符时，薄壳须**跳过它**并回退到可用的 `python`。

    这是 DEBT0014 的用户可见缺陷本身（Windows commit 被阻断）的行为级回归锁。
    初版实现（command -v 命中即用）在本用例下会选中占位符 ⇒ 标记物为 placeholder、无 real。
    """
    entry = _make_entry_root(tmp_path)
    markers = tmp_path / "markers"
    markers.mkdir()
    fake = _make_fake_bin(tmp_path, placeholder_python3=True, real_python=True, marker_dir=markers)

    hook = agate_scripts / "pre-commit-gate.sh"
    assert hook.is_file(), f"缺 hook 薄壳：{hook}"

    env = {
        "AGATE_ROOT": str(entry),
        # 受控 PATH：假 bin 在前，再补系统目录供 shell 内置工具解析
        "PATH": os.pathsep.join([str(fake), "/usr/bin", "/bin"]),
        "AGATE_PYTHON": "",  # 显式清空，确保走探测循环而非覆盖路径
    }
    from conftest import _run_cli_impl

    _run_cli_impl(bash, str(hook), env=env, cwd=str(tmp_path))

    assert (markers / "real-python-was-executed").is_file(), (
        "薄壳未回退到可用的 `python`——`python3` 占位符（执行非零退出）被误选，"
        "Windows 用户 commit 会被阻断（DEBT0014 的原始缺陷）"
    )


def test_t43_d14_agate_python_override_skips_probe_entirely(agate_scripts, bash, tmp_path):
    """`AGATE_PYTHON` 显式覆盖：直接用该路径，**跳过整个探测循环**（含占位符）。"""
    entry = _make_entry_root(tmp_path)
    markers = tmp_path / "markers"
    markers.mkdir()
    fake = _make_fake_bin(tmp_path, placeholder_python3=True, real_python=True, marker_dir=markers)
    # 覆盖路径指向一个"第三种"解释器，用于区分「走了覆盖」还是「走了探测」
    override = tmp_path / "override-python"
    _write_exe(
        override,
        "#!/bin/sh\n" f'echo used > "{markers}/override-python-was-executed"\n' "exit 0\n",
    )

    hook = agate_scripts / "pre-commit-gate.sh"
    env = {
        "AGATE_ROOT": str(entry),
        "PATH": os.pathsep.join([str(fake), "/usr/bin", "/bin"]),
        "AGATE_PYTHON": str(override),
    }
    from conftest import _run_cli_impl

    _run_cli_impl(bash, str(hook), env=env, cwd=str(tmp_path))

    assert (markers / "override-python-was-executed").is_file(), (
        "AGATE_PYTHON 覆盖未生效——探测循环仍被执行（覆盖优先是 DEBT0014 的规避手段之一）"
    )
    assert not (markers / "real-python-was-executed").is_file(), (
        "设置了 AGATE_PYTHON 却仍走了探测循环（覆盖应直接跳过探测）"
    )


def test_t43_d14_all_three_hook_shells_have_executability_probe(agate_scripts):
    """3 个薄壳**都**须有可执行性小测试（DEBT0014 说的是 3 薄壳，不只 pre-commit）。

    源码级判据（与上面两条行为判据互补）：断言每个薄壳的探测循环里有 `-c ""` 形式的
    可执行性测试调用，而非仅 `command -v`。
    """
    missing = []
    for name in HOOKS:
        text = (agate_scripts / name).read_text(encoding="utf-8")
        has_probe = '-c ""' in text or "-c ''" in text
        has_cmdv = "command -v" in text
        if not (has_probe and has_cmdv):
            missing.append(f"{name}(probe={has_probe}, command_v={has_cmdv})")
    assert missing == [], (
        "以下薄壳缺「逐候选可执行性小测试」（只靠 command -v 会选中 Store 占位符，DEBT0014）："
        + ", ".join(missing)
    )
