# agate/tests/unit/test_agate_ci_verify.py
# TAG0042 批 5（CI 与诊断）红灯测试 —— BDD-16。
#
# 目标语义（P1 BDD-16，P2-design §4.4 + §1.1 M13/M15）：
#   * BDD-16：`agate-ci-verify` 替换 `ci-gate-backstop`——它**实际重跑** gate 判定
#     （不再是「永远 SKIP 却显示绿」的假绿），无适用场景时**显式声明「跳过 + 原因」**，
#     且「跳过」与「通过」在输出上**可区分**。
#   * CHECK 10 方向（P2 §4.4）：退役 `ci-gate-backstop.py` 时，workflow 与协议文档的引用
#     须同步更新，否则 `CHECK10-scriptref` 会新增 ERROR。
#
# 现行为（改动前）：`agate/scripts/agate-ci-verify.py` **不存在**；
#   `.github/workflows/protocol-tests.yml` 仍调 `ci-gate-backstop.py`；
#   多个协议文档仍引用 `ci-gate-backstop.py` ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：红灯原因须为「被测模块未实现」——脚本文件缺失（B 类）
#   与断言失败（行为未改 = B 类），而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；不写仓库内已提交文件（全在 tmp_path / git_repo 内）。

import re

# 被测 CLI（批 5 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_CI_VERIFY_SCRIPT = "agate-ci-verify.py"

# 被替换/退役的现状实现（批 5 退役对象）
_RETIRED_BACKSTOP = "ci-gate-backstop.py"

# 退役脚本的裸名（协议文档引用面：CHECK10 只报 `.py` 形式，但退役后文档亦不应再引用其名）
_RETIRED_BACKSTOP_NAME = "ci-gate-backstop"

# CI workflow（批 5 M15：gate-backstop job 改调 agate-ci-verify.py）
_WORKFLOW = ".github/workflows/protocol-tests.yml"

# CHECK10-scriptref 扫描面（非豁免协议文件）中当前引用被退役脚本的文件：
# 退役后须同步更新引用（否则 CHECK10-scriptref 新增 ERROR）。
# 说明：`agate/UPGRADING.md` 整文件豁免、`CHANGELOG.md` 属叙事文件降级 WARNING，
# 均不在本断言面；`agate/scripts/README.md` 另有「退役名豁免」通道，亦不列入。
_PROTOCOL_REFS_TO_SYNC = (
    "agate/WORKFLOW.md",
    "agate/state-machine.md",
    "agate/platform-notes.md",
    "agate/dispatch-protocol.md",
    "agate/phase-cards/P3-tdd.md",
    "agate/assets/templates/retrospective-template.md",
)


def _run_ci_verify(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    """运行 agate-ci-verify.py。当前脚本不存在 ⇒ subprocess 返回非 0 + 'No such file'。"""
    return run_cli(
        python_exe,
        str(agate_scripts / _CI_VERIFY_SCRIPT),
        *args,
        cwd=cwd,
        env=env,
    )


def _setup_failing_gate_repo(git_repo):
    """构造一个 gate 判定**会失败**的 agate 项目。

    phase=P1 且任务目录**缺** `P1-review.md` ⇒ `check-gate.py P1` 返回 1（失败）。
    同时提供仓库根 `.state.yaml`（现状 ci-gate-backstop 的定位约定）与任务级
    `.state.yaml`（agate 任务状态的实际存放位置），使替换实现无论按哪种约定定位都能命中。
    """
    repo = git_repo.path
    task = repo / "agate-workspace" / "tasks" / "T001"
    task.mkdir(parents=True)
    state = "task_id: T001\nphase: P1\nstatus: active\nretries: {}\n"
    (repo / ".state.yaml").write_text(state, encoding="utf-8")
    (task / ".state.yaml").write_text(state, encoding="utf-8")
    (task / "P1-requirements.md").write_text(
        "---\nagent: test\n---\n#### BDD-1: x\n- Given a\n- When b\n- Then c\n",
        encoding="utf-8",
    )
    git_repo.commit("p1 failing gate")
    return repo, task


# ── BDD-16：agate-ci-verify 替换 ci-gate-backstop 且无假绿 ──────────────────
#
# Given 一次 push / PR
# When 运行 `agate-ci-verify`
# Then 它**实际重跑** gate 判定（不再是永远 SKIP 却显示绿），无适用场景时显式声明
#      「跳过 + 原因」（「跳过」与「通过」在输出上可区分）


def test_bdd_16_ci_verify_script_exists(agate_scripts):
    """BDD-16：批 5 新增 `agate-ci-verify.py`（替换 ci-gate-backstop）。

    Given 批 5 的实现对象
    When 检查脚本文件
    Then `agate-ci-verify.py` 存在。

    现行为：脚本不存在 ⇒ 红灯（模块未实现）。
    """
    script = agate_scripts / _CI_VERIFY_SCRIPT
    assert script.is_file(), (
        f"BDD-16：{_CI_VERIFY_SCRIPT} 不存在（批 5 未实现）——"
        "它是替换 ci-gate-backstop 的 CI 兜底实现"
    )


def test_bdd_16_ci_verify_reruns_gate_and_reports_failure(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-16（无假绿）：gate 判定失败时，ci-verify 必须**如实失败**（非 0 + FAIL）。

    Given 一个 gate 判定会失败的项目（phase=P1，缺 P1-review.md）
    When 运行 `agate-ci-verify`
    Then rc≠0 且输出含 FAIL（证明它**实际重跑了** gate，而非永远 SKIP 显示绿）。

    现行为：agate-ci-verify.py 不存在 ⇒ rc≠0 且无 FAIL 语义（模块未实现）⇒ 红灯。
    """
    repo, _task = _setup_failing_gate_repo(git_repo)
    result = _run_ci_verify(agate_scripts, python_exe, run_cli, cwd=repo)
    assert result.returncode != 0, (
        "BDD-16（无假绿）：gate 判定失败时 ci-verify 须 rc≠0；"
        f"当前 rc={result.returncode}（假绿）\n{result.output[:400]}"
    )
    assert "FAIL" in result.output, (
        f"BDD-16：gate 失败须以 FAIL 明确报出；实际输出 {result.output[:300]!r}"
    )


def test_bdd_16_ci_verify_skip_declared_with_reason(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-16（跳过可区分）：无适用场景时**显式声明「跳过 + 原因」**，不静默显示绿。

    Given 一个非 agate 项目（无 `.state.yaml` / 无任务）——无 gate 需兜底
    When 运行 `agate-ci-verify`
    Then 输出显式含「跳过」标识**且**给出原因（不再是「永远 SKIP 却显示绿」的无声绿）。

    现行为：agate-ci-verify.py 不存在 ⇒ 无任何跳过声明（模块未实现）⇒ 红灯。
    """
    result = _run_ci_verify(agate_scripts, python_exe, run_cli, cwd=git_repo.path)
    assert re.search(r"SKIP|跳过", result.output), (
        "BDD-16：无适用场景须**显式**声明「跳过」（不再静默假绿）；"
        f"实际输出 {result.output[:300]!r}"
    )
    assert re.search(r"原因|reason|无|not|absent|non-agate", result.output, re.IGNORECASE), (
        "BDD-16：跳过须附**原因**（「跳过」与「通过」可区分）；"
        f"实际输出 {result.output[:300]!r}"
    )


def test_bdd_16_ci_verify_source_reruns_gate(agate_scripts):
    """BDD-16（实际重跑）：ci-verify 源码确实调用 gate 判定器（check-gate.py）。

    Given agate-ci-verify.py
    When 检查其判定路径
    Then 它引用 `check-gate.py`（= 实际重跑 gate 判定），而非无条件恒绿。

    现行为：脚本不存在 ⇒ 红灯（模块未实现）。
    """
    script = agate_scripts / _CI_VERIFY_SCRIPT
    assert script.is_file(), (
        f"BDD-16：{_CI_VERIFY_SCRIPT} 不存在（批 5 未实现）——重跑 gate 路径无从检查"
    )
    src = script.read_text(encoding="utf-8")
    assert re.search(r"check-gate\.py", src), (
        "BDD-16：ci-verify 须实际重跑 gate 判定（引用 check-gate.py），"
        "而非「永远 SKIP 却显示绿」"
    )


def test_bdd_16_ci_verify_workflow_invokes_new_script(agate_root):
    """BDD-16（M15）：CI workflow 的 gate-backstop job 改调 `agate-ci-verify.py`。

    Given `.github/workflows/protocol-tests.yml`
    When 检查 gate-backstop job 的调用
    Then 它调用 `agate-ci-verify.py`，**不再**调用退役的 `ci-gate-backstop.py`。

    现行为：workflow 仍调 `ci-gate-backstop.py` ⇒ 红灯（引用未同步）。
    """
    workflow = agate_root.parent / _WORKFLOW
    assert workflow.is_file(), f"BDD-16：找不到 workflow {_WORKFLOW}"
    text = workflow.read_text(encoding="utf-8")
    assert _CI_VERIFY_SCRIPT in text, (
        f"BDD-16（M15）：workflow 须调用新脚本 {_CI_VERIFY_SCRIPT}（替换 ci-gate-backstop）"
    )
    assert _RETIRED_BACKSTOP not in text, (
        f"BDD-16（M15）：workflow 不应再调用退役的 {_RETIRED_BACKSTOP}"
        "（引用须同步更新）"
    )


def test_bdd_16_ci_verify_protocol_refs_synced(agate_root):
    """BDD-16（CHECK10-scriptref 方向）：退役后协议文档引用须同步更新。

    Given 退役 `ci-gate-backstop.py` 的批 5
    When 检查 CHECK10-scriptref 扫描面（非豁免协议文件）
    Then 这些文件**不再**引用已退役的 `ci-gate-backstop.py`（否则 CHECK10 新增 ERROR）。

    现行为：协议文档仍引用 `ci-gate-backstop.py` ⇒ 红灯（引用未同步）。
    """
    offenders = []
    for rel in _PROTOCOL_REFS_TO_SYNC:
        path = agate_root.parent / rel
        if path.is_file() and _RETIRED_BACKSTOP_NAME in path.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, (
        "BDD-16（CHECK10-scriptref）：退役 ci-gate-backstop.py 后下列协议文件仍引用它，"
        f"须同步更新引用：{offenders}"
    )
