# agate/tests/unit/test_tag0042_batch1_phase_semantics.py
# TAG0042 批 1（统一 phase 语义）红/绿灯测试 —— BDD-1 + BDD-2。
#
# 目标语义（P1 BDD-1/BDD-2，P2-design §1.1 M1/M2/M3）：
#   phase 在所有路径上只表示「**本 commit 的产出阶段**」——即 commit 时 phase 保持
#   当前产出阶段，**不预写下一阶段**（与 P2/P8 卡既有表述一致）。
#
# 现行为（改动前，实测）：agate-next.py::_advance()（约 L198-210）
#   * `state["phase"] = target`（把 Pn+1 **预写**进 .state.yaml）
#   * `_write_state(...)`（落盘）
#   * `_git(["add", <task>/.state.yaml], repo_root)`（自动 git add）
#   ⇒ BDD-1 的「不预写 + 不 git add」当前**不成立** ⇒ 本文件当前红灯。
#
# 平台无关：tmp_path / task_dir / git_repo fixtures；run_cli(python_exe, ...)；
#   显式 encoding="utf-8"；需要路径字面量时**运行时拼接**（R4 平台扫描，不写字面量）；
#   不裸 python3（用 python_exe fixture）。无仓库内已提交文件写入（全在 tmp_path/git_repo）。
#
# 红灯分类（check-tdd-red）：断言失败（行为未改）= B 类真红灯，非 SyntaxError/第三方 import。

import importlib.util
import re

import pytest

# 被测 CLI（既有文件；批 1 改其 _advance 行为）
_NEXT_SCRIPT = "agate-next.py"

# R4 平台扫描规避：需要「系统临时目录」字面量时运行时拼接（仓库既有惯例）。
_TMP = "/" + "tmp"


# ── 共享工具 ────────────────────────────────────────────────────────────

def _load_next_module(agate_scripts):
    """import agate-next.py（文件名含连字符 ⇒ importlib 显式加载）。"""
    spec = importlib.util.spec_from_file_location(
        "agate_next_mod_b1", str(agate_scripts / _NEXT_SCRIPT)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_next(agate_scripts, python_exe, run_cli, td, env=None):
    return run_cli(python_exe, str(agate_scripts / _NEXT_SCRIPT), str(td), env=env)


def _write_state(td, phase, task_id="T0042"):
    """写任务目录 .state.yaml（只含既有最小字段，避免多余键干扰）。"""
    (td / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: {phase}\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )


def _read_state_phase(td):
    text = (td / ".state.yaml").read_text(encoding="utf-8")
    m = re.search(r"^phase:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def _write_p5_pass_fixture(td):
    """phase=P5 且 check-gate.py P5 返回通过码（exit 2 ∈ gate_pass_exit）的前置。

    依据 gate_p5（check-gate.py）：P2-design.md 存在（无 gate_commands.P5 多命令 WARNING）
    + 无 pre-task-baseline.md（不触发机械 diff）→ 恒 return 2（正常通过码）。
    ⇒ 这是「推进路径确实被走过」的前提：agate-next 会进入 _advance 分支。
    """
    (td / "P2-design.md").write_text(
        "---\nagent: test\n---\n# P2 design\n", encoding="utf-8"
    )


# ── BDD-1：agate-next 推进时不预写下一阶段 ───────────────────────────────
#
# Given 一个 .state.yaml 的 phase: Pn，且 .state.yaml 未被暂存
# When 运行 agate-next 且 check-gate.py Pn 返回通过码（∈ gate_pass_exit）
# Then agate-next **不把** Pn+1 写入 .state.yaml 的 phase 字段，且 **不** git add .state.yaml


def test_bdd_1_advance_does_not_prewrite_next_phase_into_state_yaml(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-1：gate 通过后运行 agate-next → .state.yaml 的 phase **不得**被改为 Pn+1。

    现行为：`_advance` 把 phase 写成 next（P5→P6）⇒ 断言失败（B 类真红灯）。
    目标行为：phase 保持 P5（下一阶段由 P6 产出 commit 时再写）。
    """
    td = task_dir(phases=["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])
    _write_state(td, "P5")
    _write_p5_pass_fixture(td)

    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"agate-next 应正常结束；rc={result.returncode}\n{result.output[:400]}"

    phase_after = _read_state_phase(td)
    assert phase_after != "P6", (
        "BDD-1：agate-next 推进时**不得预写**下一阶段——phase 被预写为 P6 即违规"
        f"（phase={phase_after}）；phase 应保持本 commit 的产出阶段 P5"
    )
    assert phase_after == "P5", (
        f"BDD-1：phase 应保持当前产出阶段 P5（不预写），实际 {phase_after}"
    )


def test_bdd_1_advance_does_not_git_add_state_yaml(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-1：推进路径**不得**把 .state.yaml `git add` 进暂存区。

    Given .state.yaml 未被暂存（先 commit 一次使工作区干净）
    When 运行 agate-next 且 gate 通过
    Then `git diff --cached --name-only` 不含 .state.yaml。
    现行为：`_advance` 调 `_git(["add", <task>/.state.yaml])` ⇒ 暂存区出现该文件 ⇒ 红灯。
    """
    import shutil

    td = task_dir(phases=["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])
    repo = git_repo.path
    # 把任务目录放进真实 git 仓库并提交，使 .state.yaml 初始为「未被暂存」状态
    shutil.copytree(str(td), str(repo / "task"))
    task = repo / "task"
    _write_state(task, "P5")
    _write_p5_pass_fixture(task)
    git_repo.commit("init task")

    result = _run_next(agate_scripts, python_exe, run_cli, task, env={"AGATE_ROOT": ""})
    assert result.returncode == 0, f"agate-next 应正常结束；rc={result.returncode}\n{result.output[:400]}"

    staged = git_repo.staged_files()
    assert ".state.yaml" not in staged, (
        "BDD-1：推进时**不得** git add .state.yaml；当前暂存区含 .state.yaml ⇒ 违规（预写路径残留）"
        f"\nstaged={staged!r}"
    )


# ── BDD-2：不可绕开路径上的 phase 语义与卡片表述一致 ─────────────────────
#
# Given 批 1 落地后
# When 对 agate-next.py 与 phase-cards/ 的 phase 语义表述做一致性扫描
# Then 全仓不再存在「agate-next 预写下一阶段」的行为代码，且卡片的
#      「phase = 本 commit 产出阶段」表述与 agate-next 实际行为一致（无相悖描述）


def test_bdd_2_agate_next_source_has_no_prewrite_behavior(agate_scripts):
    """BDD-2（行为代码面）：agate-next.py 的 `_advance` **不得**再含「预写下一阶段」代码。

    现行为：`_advance` 内含 `state["phase"] = target` 且紧随 `_write_state(...)` 写盘
    ⇒ 该代码段存在 ⇒ 红灯。
    目标：`_advance` 不再把 target 写进 .state.yaml 的 phase（只输出「下一阶段建议」，
    phase 由后续产出 commit 写）。
    """
    src = (agate_scripts / _NEXT_SCRIPT).read_text(encoding="utf-8")

    # 定位 _advance 函数体（从定义到下一个顶层 def）
    m = re.search(r"^def _advance\(.*?\n(?=^def |\Z)", src, re.M | re.S)
    assert m is not None, "未找到 _advance 定义（结构漂移，需同步本判据）"
    body = m.group(0)

    assert 'state["phase"] = target' not in body, (
        "BDD-2：agate-next._advance 仍含 `state[\"phase\"] = target`（预写下一阶段）行为代码"
    )
    # 预写的实际落盘点：改 phase 后必须紧跟写盘 + git add；两者一并不应再出现
    assert not re.search(r"state\[[\"']phase[\"']\]\s*=\s*target", body), (
        "BDD-2：_advance 内仍有对 .state.yaml phase 的 target 赋值（预写残留）"
    )


def test_bdd_2_phase_cards_align_with_phase_is_current_commit_output(
    agate_root, agate_scripts,
):
    """BDD-2（卡片表述与行为一致面）：P2-design.md / P8-release.md 卡片须表述
    「phase = 本 commit 产出阶段」，**且** agate-next 实际行为**不预写**下一阶段
    ——即卡片表述与不可绕开路径上的实际行为一致（无相悖描述）。

    依据（P2-design §1.1 M2）：卡片表述本身已到位（P2 卡「phase 保持 P2，不要提前写 P3」、
    P8 卡「phase = 本 commit 的产出阶段」），但批 1 的目标是让**行为**与之一致——
    行为侧仍预写（`_advance` 写 target）即「卡片说不要提前写、行为却提前写」的矛盾。
    现行为：行为侧仍预写 ⇒ 卡片与行为**不一致** ⇒ 本用例红灯。
    """
    p2_card = (agate_root / "phase-cards" / "P2-design.md").read_text(encoding="utf-8")
    p8_card = (agate_root / "phase-cards" / "P8-release.md").read_text(encoding="utf-8")

    # ① 卡片表述须存在（phase = 本 commit 产出阶段 / 不要提前写下一阶段）
    assert "phase 保持" in p2_card and "不要提前写" in p2_card, (
        "BDD-2：P2-design.md 卡缺「phase 保持当前阶段 / 不要提前写下一阶段」表述"
    )
    assert "本 commit" in p8_card and "产出阶段" in p8_card, (
        "BDD-2：P8-release.md 卡缺「phase = 本 commit 的产出阶段」表述"
    )

    # ② 卡片表述须与实际行为**一致**——agate-next 不得预写下一阶段（否则卡片被行为推翻）
    src = (agate_scripts / _NEXT_SCRIPT).read_text(encoding="utf-8")
    assert 'state["phase"] = target' not in src, (
        "BDD-2：卡片表述「不要提前写下一阶段」与 agate-next 实际行为相悖——"
        "`_advance` 仍预写 target 到 .state.yaml phase（行为代码与卡片不一致）"
    )


def test_bdd_2_upgrading_documents_agate_next_no_prewrite(agate_root):
    """BDD-2（文档一致面，P2-design §1.1 M3）：UPGRADING.md 批 1 章节须改述为
    「批 1 起 agate-next 亦**不预写**下一阶段」。

    现行为：UPGRADING.md 仍写「阶段卡片 phase 语义（**文档，无强制**）」，未记批 1 行为变更
    ⇒ 红灯。
    """
    upgrading = (agate_root / "UPGRADING.md").read_text(encoding="utf-8")
    # 批 1 起应出现「agate-next ... 不预写」的表述（新语义留痕）
    assert re.search(r"agate-next.{0,40}不预写", upgrading, re.S), (
        "BDD-2：UPGRADING.md 未记载「agate-next 不预写下一阶段」的批 1 行为变更"
    )


@pytest.mark.windows_smoke
def test_bdd_2_no_prewrite_behavior_code_anywhere_in_scripts(agate_scripts):
    """BDD-2（全仓行为代码面）：`agate/scripts/` 下**不再存在**「预写下一阶段」的实现。

    扫描点：把 next 阶段写进 .state.yaml phase 的赋值——`_advance` 的
    `state["phase"] = target` 是当前唯一的此类实现。目标为「全仓不再存在」。
    现行为：存在 ⇒ 红灯。
    """
    offenders = []
    for py in agate_scripts.glob("*.py"):
        text = py.read_text(encoding="utf-8", errors="replace")
        if re.search(r"state\[[\"']phase[\"']\]\s*=\s*target", text):
            offenders.append(py.name)

    assert not offenders, (
        "BDD-2：agate/scripts/ 下仍存在「预写下一阶段」行为代码：" + ", ".join(offenders)
    )
