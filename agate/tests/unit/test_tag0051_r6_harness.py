# agate/tests/unit/test_tag0051_r6_harness.py — TAG0051 P3 红灯（R6 corpus wrapper）
#
# 覆盖 BDD（P1-requirements.md）：20。
#   * BDD-20：legacy 行为不变的验收锚 = R6 双向差分（`docs/design-notes/r6-differential.sh`）——
#     P2 §5/§4（NB-3）把「备 corpus」从人记改为**机械**：新增 wrapper
#     `docs/design-notes/r6-differential-prepare.sh`（`--src` / `--dst`），先 `cp -a` 建一次性
#     整仓 corpus + 重置干净工作树，再 `exec` 既有差分脚本。
#   * 本文件对 wrapper 做**契约 + 健壮性（NB-8）**判定：`--dst` 为空 / 相对路径 / 位于 `--src`
#     之内 ⇒ **拒绝**（不得把 `rm -rf` 落到源或真仓）；且不得改真实仓库的 `agate/`。
#     全量差分（未匹配差异 0 条 + 真仓跑前/跑后干净）由 `gate_commands.P5_r6` 兜底执行——
#     属「资源密集型、须串行」的运行，不在本单测内跑（P2 §5 明示）。
#
# 现行为（改动前）：wrapper **不存在** ⇒ 断言失败 = B 类红灯。
#
# 平台无关：bash fixture（Linux 返回 "bash"，Windows 探测 Git Bash）；tmp_path；
#   subprocess 显式 encoding="utf-8"；不裸 python3；不写字面系统临时目录。

import subprocess

import helpers_tag_repo as H

_WRAPPER = ("docs", "design-notes", "r6-differential-prepare.sh")


def _wrapper_path():
    return H.REPO_ROOT.joinpath(*_WRAPPER)


def _run_wrapper(bash, *args):
    return subprocess.run(
        [bash, str(_wrapper_path()), *args],
        cwd=str(H.REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )


def test_bdd_20_wrapper_exists_and_is_strict_shell(bash):
    """BDD-20：wrapper 存在、bash 可解析、含 `set -euo pipefail`（NB-8 前置）。"""
    path = _wrapper_path()
    assert path.is_file(), (
        f"BDD-20：R6 corpus wrapper 缺失：{path.relative_to(H.REPO_ROOT)}（P2 §5 NB-3 待实现）"
    )
    syntax = subprocess.run(
        [bash, "-n", str(path)],
        cwd=str(H.REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert syntax.returncode == 0, "BDD-20：wrapper 不是合法 bash 脚本"
    text = path.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text, "BDD-20：wrapper 须 `set -euo pipefail`（NB-8）"


def test_bdd_20_wrapper_rejects_empty_dst(bash):
    """BDD-20（NB-8）：`--dst` 为空串 ⇒ 拒绝（不得落到 cwd / 真仓）。"""
    assert _wrapper_path().is_file(), "BDD-20：wrapper 缺失（见上）"
    result = _run_wrapper(bash, "--src", ".", "--dst", "")
    assert result.returncode != 0, "BDD-20：`--dst` 为空串须被拒绝（防 `rm -rf` 落到真仓）"


def test_bdd_20_wrapper_rejects_relative_dst(bash):
    """BDD-20（NB-8）：`--dst` 为相对路径 ⇒ 拒绝。"""
    assert _wrapper_path().is_file(), "BDD-20：wrapper 缺失（见上）"
    result = _run_wrapper(bash, "--src", ".", "--dst", "relative-corpus")
    assert result.returncode != 0, "BDD-20：`--dst` 相对路径须被拒绝（NB-8）"


def test_bdd_20_wrapper_rejects_dst_inside_src(bash, tmp_path):
    """BDD-20（NB-8）：`--dst` 位于 `--src` 之内 ⇒ 拒绝（否则 `rm -rf` 会删源）。"""
    assert _wrapper_path().is_file(), "BDD-20：wrapper 缺失（见上）"
    src = tmp_path / "src"
    (src / "agate").mkdir(parents=True)
    result = _run_wrapper(
        bash, "--src", str(src), "--dst", str(src / "corpus-inside")
    )
    assert result.returncode != 0, "BDD-20：`--dst` 位于 `--src` 之内须被拒绝（NB-8）"


def test_bdd_20_wrapper_bad_args_do_not_touch_real_repo(bash):
    """BDD-20：参数非法被拒时，真实仓库 `agate/` 不得被改动（跑前/跑后一致）。"""
    assert _wrapper_path().is_file(), "BDD-20：wrapper 缺失（见上）"
    before = H.run_git(H.REPO_ROOT, "status", "--porcelain", "--", "agate").stdout
    _run_wrapper(bash, "--src", ".", "--dst", "")
    after = H.run_git(H.REPO_ROOT, "status", "--porcelain", "--", "agate").stdout
    assert before == after, "BDD-20：wrapper 运行（参数非法）改动了真实仓库 agate/"
