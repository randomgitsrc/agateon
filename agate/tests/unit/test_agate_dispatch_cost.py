# tests/unit/test_agate_dispatch_cost.py — 派发成本的**可复核度量**（RM-AG0074 前置）
#
# 为何需要：2026-09-29 我（主 Agent）在 roadmap 里写下「60%（251KB）是 AGATE_CARD 重复注入」，
# 经复核实测为 **36%（245KB），其中纯重复 27%（182KB）**——**错诊断会驱动错配的方案**。
# 根因是**手抄数字**：没有任何脚本能复核该声称。本工具把「派发成本」变成**可量测**，
# 使此后所有效率声称都能被复核，而不是靠谁的记忆。
#
# 设计原则（本组的判据即由此而来）：
#   1. **只测可测的**——`*dispatch-context*.md` 是客观产物，计数/字节可信；
#   2. **拒绝编造**——`.state.yaml` 的 `history` 实测只有 7 条、缺 P3/P4/P5/P6/P7
#      ⇒ **阶段耗时不可算**。工具须**明说不可算**，而不是用残缺时间戳算出一个假数字
#      （TAG0030 教训：把不可判定伪装成可判定）。
#
# 平台无关：全部走 pytest `tmp_path`；不裸 python3；不用临时目录字面量。

import json
import re
from pathlib import Path

import pytest

CARD_START = "<!-- AGATE_CARD_START -->"
CARD_END = "<!-- AGATE_CARD_END -->"


def _script(agate_scripts: Path) -> Path:
    return agate_scripts / "agate-dispatch-cost.py"


def _mk_task(root: Path, name: str = "T0001-x") -> Path:
    d = root / "agate-workspace" / "tasks" / name
    d.mkdir(parents=True)
    return d


def _ctx(d: Path, fname: str, card: str = "", body: str = "x" * 100) -> Path:
    p = d / fname
    text = ""
    if card:
        text += f"{CARD_START}\n{card}\n{CARD_END}\n"
    text += body
    p.write_text(text, encoding="utf-8")
    return p


def _run(agate_scripts, python_exe, run_cli, task_dir, *extra):
    return run_cli(
        python_exe, str(_script(agate_scripts)), str(task_dir), *extra
    )


# ---------------------------------------------------------------------------
# 基本计数与字节
# ---------------------------------------------------------------------------


def test_dc_1_counts_contexts_and_bytes(agate_scripts, python_exe, run_cli, tmp_path):
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md", body="a" * 1000)
    _ctx(d, "P2-dispatch-context-architect.md", body="b" * 2000)

    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    assert r.returncode == 0, r.output
    data = json.loads(r.stdout)
    assert data["contexts"] == 2
    assert data["total_bytes"] == 3000


def test_dc_2_rev_files_are_counted_separately(agate_scripts, python_exe, run_cli, tmp_path):
    """`-revN` 重发单列（它是可避免的重复派发，不是新增信息）。"""
    d = _mk_task(tmp_path)
    _ctx(d, "P2-dispatch-context-architect.md", body="a" * 1000)
    _ctx(d, "P2-dispatch-context-architect-rev1.md", body="b" * 900)
    _ctx(d, "P2-dispatch-context-review.md", body="c" * 100)

    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    data = json.loads(r.stdout)
    assert data["contexts"] == 3
    assert data["rev_contexts"] == 1
    assert data["rev_bytes"] == 900
    assert data["rev_ratio"] == pytest.approx(900 / 2000, abs=0.01)


# ---------------------------------------------------------------------------
# 卡片注入：总量 + **纯重复**
# ---------------------------------------------------------------------------


def test_dc_3_card_bytes_and_duplicate_bytes(agate_scripts, python_exe, run_cli, tmp_path):
    """同卡片第 2..N 次注入属**纯浪费**，须与「卡片总量」分开报。"""
    d = _mk_task(tmp_path)
    card = "C" * 500
    _ctx(d, "P1-dispatch-context-analyst.md", card=card, body="a" * 100)
    _ctx(d, "P1-dispatch-context-review.md", card=card, body="b" * 100)   # 同一张卡
    _ctx(d, "P2-dispatch-context-architect.md", card="D" * 300, body="c" * 100)

    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    data = json.loads(r.stdout)
    # 三份都有卡片 ⇒ 卡片总量 > 0；其中 1 份是重复
    assert data["card_bytes"] > 0
    assert data["card_duplicate_bytes"] == pytest.approx(len(card) + 2 * len(CARD_START) + 2, abs=40), (
        f"重复卡片字节应≈一份 CSP 块的字节：{data['card_duplicate_bytes']}"
    )
    assert data["card_duplicate_bytes"] < data["card_bytes"], "纯重复必须小于卡片总量"


def test_dc_4_absent_card_markers_yield_zero(agate_scripts, python_exe, run_cli, tmp_path):
    """无卡片标记 ⇒ 0（不得把正文误当卡片）。防"正则没匹配上却报 0% 或报满"。"""
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md", body="no card here " * 50)

    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    data = json.loads(r.stdout)
    assert data["card_bytes"] == 0
    assert data["card_duplicate_bytes"] == 0


# ---------------------------------------------------------------------------
# 诚实性：阶段耗时不可算时**必须明说**，不得编造
# ---------------------------------------------------------------------------


def test_dc_5_duration_reported_unavailable_when_history_incomplete(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """`history` 覆盖不全 ⇒ `duration_available` 为 false（**不编造数值**）。"""
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md")
    (d / ".state.yaml").write_text(
        "task_id: T1\nphase: P2\nhistory:\n"
        "  - {phase: P0, action: created, ts: '2026-01-01T00:00:00Z'}\n"
        "  - {phase: P2, action: completed, ts: '2026-01-02T00:00:00Z'}\n",
        encoding="utf-8",
    )
    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    data = json.loads(r.stdout)
    assert data["duration_available"] is False, (
        "history 缺多数阶段却声称可算耗时——正是「把不可判定伪装成可判定」"
    )
    assert data.get("duration_seconds") is None, "不可算时不得给出数值"


def test_dc_6_no_state_yaml_is_not_an_error(agate_scripts, python_exe, run_cli, tmp_path):
    """任务目录无 .state.yaml ⇒ 派发成本照常可算（这是独立维度）。"""
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md", body="a" * 10)
    r = _run(agate_scripts, python_exe, run_cli, d, "--json")
    assert r.returncode == 0
    assert json.loads(r.stdout)["contexts"] == 1


# ---------------------------------------------------------------------------
# fail-closed：目标不存在须非零，不得静默"通过"
# ---------------------------------------------------------------------------


def test_dc_7_missing_task_dir_is_fail_closed(agate_scripts, python_exe, run_cli, tmp_path):
    """目标不存在 ⇒ exit 2（不静默报 0 份，那会被读成"没有问题"）。"""
    r = _run(agate_scripts, python_exe, run_cli, tmp_path / "nope")
    assert r.returncode == 2, f"缺目标应 fail-closed，实得 {r.returncode}"


def test_dc_8_missing_arg_is_usage_error(agate_scripts, python_exe, run_cli):
    r = run_cli(python_exe, str(_script(agate_scripts)))
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 人类可读输出（默认）与 --json 一致
# ---------------------------------------------------------------------------


def test_dc_9_human_output_reports_key_numbers(agate_scripts, python_exe, run_cli, tmp_path):
    """默认输出须含份数/字节/rev/卡片占比——供人工快速复核。"""
    d = _mk_task(tmp_path)
    _ctx(d, "P2-dispatch-context-architect.md", card="C" * 200, body="a" * 800)
    _ctx(d, "P2-dispatch-context-architect-rev1.md", card="C" * 200, body="b" * 800)

    r = _run(agate_scripts, python_exe, run_cli, d)
    assert r.returncode == 0
    out = r.stdout
    assert re.search(r"\b2\b", out), "未报份数"
    assert "rev" in out.lower(), "未报修订重发"
    assert "%" in out, "未报占比（复核需要）"


def test_dc_10_p0_created_entry_counts_as_covered(agate_scripts, python_exe, run_cli, tmp_path):
    """P0 在账本里的 action 是 `created`/`pending-start`（非 `completed`）——须计为**已覆盖**。

    缺陷形态（我自己的实现 bug，2026-09-29 自查发现）：覆盖判据只认 `action == "completed"`，
    而 P0 从不产生 `completed` 条目 ⇒ `duration_available` **永远为 false**、该功能形同虚设
    （表现为「诚实但无用」）。修法：P0 接受**任意** history 条目即视为覆盖。
    """
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md")
    # **必须**放 P0-brief.md：否则 P0 不被观测到，测不出真实缺陷（初版测试即因此假绿）
    (d / "P0-brief.md").write_text("task: x\n", encoding="utf-8")
    (d / ".state.yaml").write_text(
        "task_id: T1\nphase: P1\nhistory:\n"
        "  - {phase: P0, action: created, ts: '2026-01-01T00:00:00Z'}\n"
        "  - {phase: P1, action: completed, ts: '2026-01-01T05:00:00Z'}\n",
        encoding="utf-8",
    )
    data = json.loads(run_cli(
        python_exe, str(_script(agate_scripts)), str(d), "--json"
    ).stdout)
    assert data["duration_available"] is True, (
        f"P0 的 created 条目应计为已覆盖，否则耗时永远不可算（工具形同虚设）：{data.get('duration_reason')}"
    )
    assert data["duration_seconds"] == 5 * 3600


def test_dc_11_p6_5_artifacts_map_to_p6_not_silently_ignored(
    agate_scripts, python_exe, run_cli, tmp_path
):
    """P6.5 产物须**显式**归到 P6，而非被正则静默漏掉。

    缺陷形态（独立评审 2026-09-29 发现）：`_observed_phases` 用 `^P(\\d+)-`，而 `P6.5-judge-verdict.md`
    在 "P6" 之后是 `.` 不是 `-` ⇒ **永不匹配**，P6.5 被静默忽略。
    协议上 P6.5 **不是独立 phase 值**（`P6-acceptance.md`：「phase 保持 P6」），故正确行为是
    **显式映射到 P6**——而不是靠"恰好不匹配"来实现，那属**偶然正确**：
    一旦某任务只留 P6.5 产物而无 P6-* 产物，P6 就会漏检，判据即失真。
    """
    d = _mk_task(tmp_path)
    _ctx(d, "P1-dispatch-context-analyst.md")
    # 只有 P6.5 产物、**没有** P6-acceptance.md ⇒ 若 P6.5 被忽略，P6 就不在 observed 里
    (d / "P6.5-judge-verdict.md").write_text("---\nstatus: x\n---\n", encoding="utf-8")
    (d / ".state.yaml").write_text(
        "task_id: T1\nphase: P1\nhistory:\n"
        "  - {phase: P0, action: created, ts: '2026-01-01T00:00:00Z'}\n"
        "  - {phase: P1, action: completed, ts: '2026-01-01T01:00:00Z'}\n",
        encoding="utf-8",
    )
    data = json.loads(run_cli(
        python_exe, str(_script(agate_scripts)), str(d), "--json"
    ).stdout)
    assert data["duration_available"] is False, (
        "P6.5 产物应显式映射到 P6 ⇒ 账本缺 P6 时须判不可算；"
        "若此处为 True，说明 P6.5 被静默忽略（偶然正确，非设计）"
    )
    assert "P6" in (data.get("duration_reason") or ""), (
        f"不可算原因应点名 P6（P6.5 归 P6）：{data.get('duration_reason')}"
    )
