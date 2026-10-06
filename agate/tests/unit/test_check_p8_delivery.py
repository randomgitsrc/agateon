# agate/tests/unit/test_check_p8_delivery.py
# TAG0042 批 4（P8 交付收尾）红灯测试 —— BDD-15。
#
# 目标语义（P1 BDD-15，P2-design §4.3 + §1.1 M11/M12）：
#   * BDD-15：P8 语义为**交付收尾**（非「发版」）；`check-gate.py::gate_p8()` 校验 `delivery`
#     声明——**未声明 → gate 拦截（非 0）**，声明后放行。
#
# 现行为（改动前）：`gate_p8()` 只校验 `bump_type` / `debt_check`（+ version/CHANGELOG/tag 告警），
#   **无** `delivery` 声明校验 ⇒ 未声明 `delivery` 也返回通过码 2 ⇒ 本文件当前红灯。
#   `phases.yaml` 的 P8 名称仍为「发布准备」（非交付收尾）⇒ 语义面红灯。
#
# 红灯分类（check-tdd-red）：本批红灯原因须为「被测行为/结构未实现」——gate_p8 无 delivery 拦截
#   （断言失败 = B 类）、phases.yaml P8 语义未改（断言失败 = B 类），而非 SyntaxError /
#   第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / task_dir / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；不写仓库内已提交文件（全在 tmp_path / git_repo）。
#
# [DESIGN_GAP]（P2-design §11 预留，见 P3-test-cases-batch4.md §2）：
#   `delivery` 的合法取值集合与 P8 名称的精确措辞设计未定 ⇒ 断言落在可观察契约上
#   （字段名 `delivery` 由 BDD-15 明列；未声明 → 非 0；声明后 → 通过；P8 语义改述为交付收尾），
#   不臆造内部键名。P4 须按 BDD 落定契约。

import shutil

import yaml

_PHASES_PARTS = ("rules", "phases.yaml")

# 通过码：phases.yaml 声明 P8 gate_pass_exit == 2（回归基线）。
_P8_PASS_EXIT = 2

# 合规 P8 基础字段（不含 delivery——用于「未声明即拦截」的负向场景）。
_P8_BASE = "bump_type: minor\ndebt_check: none\n"


def _write_p8_release(td, body):
    (td / "P8-release.md").write_text(body, encoding="utf-8")


def _p8_repo(git_repo, td, files):
    """建 git 仓库 + 复制任务目录 + 写/暂存给定文件（version/CHANGELOG 等）。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    # dirs_exist_ok：本测试在同一 git_repo 上先后跑「未声明 / 已声明」两场景，
    # 第二次复制需覆盖既有 task/（仅 P8-release.md 不同）——不改变任何断言。
    shutil.copytree(td, repo / "task", dirs_exist_ok=True)
    for name, content in files.items():
        (repo / name).write_text(content, encoding="utf-8")
        git_repo.stage(name)
    return repo


def _run_p8(agate_scripts, python_exe, run_cli, repo):
    return run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P8", "task", cwd=str(repo)
    )


# ── BDD-15：P8 为交付收尾且 delivery 必须声明 ────────────────────────────────
#
# Given 一个任务进入 P8
# When 运行 P8 gate
# Then P8 语义为交付收尾（非「发版」）；delivery 未声明时 gate 拦截（非 0），声明后放行


def test_bdd_15_p8_gate_blocks_when_delivery_missing(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-15：`delivery` 未声明时 P8 gate **拦截**（非 0，且非通过码 2）。

    Given P8-release.md 含 bump_type / debt_check，但**无** `delivery` 声明
    When 运行 P8 gate
    Then gate 拦截（returncode 非 0，指向 delivery 缺失）——不再无条件放行。

    现行为：gate_p8 无 delivery 校验 ⇒ 返回 2（通过）⇒ 红灯（行为未实现）。
    """
    td = task_dir()
    _write_p8_release(td, _P8_BASE)
    repo = _p8_repo(
        git_repo, td,
        {"package.json": '{"version": "0.1.0"}\n', "CHANGELOG.md": "## [Unreleased]\n"},
    )

    result = _run_p8(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode != 0 and result.returncode != _P8_PASS_EXIT, (
        "BDD-15：`delivery` 未声明时 P8 gate 须拦截（非 0，非通过码 2）；"
        f"当前 rc={result.returncode}（无 delivery 校验）\n{result.output[:400]}"
    )
    assert "delivery" in result.output, (
        "BDD-15：拦截信息须指向缺失的 `delivery` 声明；"
        f"实际输出 {result.output[:400]!r}"
    )


def test_bdd_15_p8_gate_passes_only_when_delivery_declared(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-15：`delivery` 是放行的决定因素——声明后放行（rc=2），未声明则拦截。

    Given 两个任务：一个 P8-release.md 声明 `delivery`，另一个未声明
    When 分别运行 P8 gate
    Then 未声明 → 非 0；声明 → 通过码 2（`delivery` 声明后放行）。

    现行为：两者均返回 2（未声明也不拦截）⇒ 前置负向断言即失败 ⇒ 红灯（行为未实现）。
    """
    # 负向：未声明 delivery ⇒ 须拦截
    td_missing = task_dir()
    _write_p8_release(td_missing, _P8_BASE)
    repo_missing = _p8_repo(
        git_repo, td_missing,
        {"package.json": '{"version": "0.1.0"}\n', "CHANGELOG.md": "## [Unreleased]\n"},
    )
    missing = _run_p8(agate_scripts, python_exe, run_cli, repo_missing)
    assert missing.returncode != 0 and missing.returncode != _P8_PASS_EXIT, (
        "BDD-15：前置——未声明 `delivery` 须被拦截（非 0）；"
        f"当前 rc={missing.returncode}\n{missing.output[:400]}"
    )

    # 正向：声明 delivery ⇒ 放行（rc=2）
    td_declared = task_dir()
    _write_p8_release(
        td_declared, _P8_BASE + "delivery: package-release\n"
    )
    repo_declared = _p8_repo(
        git_repo, td_declared,
        {"package.json": '{"version": "0.1.0"}\n', "CHANGELOG.md": "## [Unreleased]\n"},
    )
    declared = _run_p8(agate_scripts, python_exe, run_cli, repo_declared)
    assert declared.returncode == _P8_PASS_EXIT, (
        "BDD-15：声明 `delivery` 后 P8 gate 须放行（rc=2）；"
        f"当前 rc={declared.returncode}\n{declared.output[:400]}"
    )


def test_bdd_15_p8_semantics_is_delivery_wrapup(agate_root):
    """BDD-15：P8 语义为**交付收尾**（非「发版」）——phases.yaml 名称 + 卡片承载 delivery 声明。

    Given phases.yaml 与 phase-cards/P8-release.md（P8 语义权威源）
    When 检查 P8 的语义表述
    Then phases.yaml 的 P8 名称体现「交付收尾」（交付/收尾），
         且 P8 卡片记载 `delivery` 为 P8 产出/门槛的一部分。

    现行为：phases.yaml P8 名称为「发布准备」、卡片无 `delivery` ⇒ 红灯（语义未改）。

    [DESIGN_GAP]：精确措辞设计未定 ⇒ 只断言语义方向（含「交付」或「收尾」）与 `delivery` 载体，
    不绑定具体句子；P4 按 BDD 落定。
    """
    data = yaml.safe_load(
        agate_root.joinpath(*_PHASES_PARTS).read_text(encoding="utf-8")
    )
    p8 = next(p for p in data["phases"] if p["id"] == "P8")
    name = p8.get("name", "")
    assert "交付" in name or "收尾" in name, (
        "BDD-15：P8 语义须改述为**交付收尾**（phases.yaml P8 名称含「交付」或「收尾」）；"
        f"当前 name={name!r}（仍为发版语义）"
    )

    card = (agate_root / "phase-cards" / "P8-release.md").read_text(encoding="utf-8")
    assert "delivery" in card, (
        "BDD-15：P8 卡片须记载 `delivery` 为 P8 产出/门槛的一部分（交付收尾必须声明）"
    )
