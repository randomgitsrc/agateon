# agate/tests/unit/test_tag0027_b1_agate_next_cli.py — TAG0027 B1 批：agate next 推进 CLI（BDD-6/7/8/9/11/13）
#
# 被测契约（P2-design §3.4 定案 D4-A（exit2fix pass_set 重写）+ §3.1「P6 主线 next 条件式裁决（A1）」）：
#   新增脚本 agate/scripts/agate-next.py [TASK_DIR]（P4 新建）：
#     读 phases.yaml 当前 phase 的 gate_pass_exit（pass_set）+ next/retreat，按 exit 三态判定：
#       exit ∈ pass_set（多数 phase 正常通过码 = exit 2，P4/P7/P6.5 = exit 0）→ 直推候选：
#         普通 phase → 按 phases.yaml next 更新 .state.yaml phase + git add +
#         append_event state_transition（exit 2 正常通过也直推，不落盘 resolution——CRITICAL-1）
#         P6（exit 2 ∈ pass_set 条件式）→ A1 裁决：provenance exit 0 + judge 未启用直推 P7 /
#         启用 → check-gate P6.5 exit 0 推 P7 / exit 1 停留 P6 有指引，不落盘
#       exit 1 → 按 retreat 表值存在即委托 agate-retreat-to.py（CLI 不预判 diff）
#       exit ∉ pass_set 且 ≠ 1（真暂停/异常，如 P4 gate 的 agent 缺失 return 2）→ 落盘
#         {phase}-exit2-resolution.md（BDD-8 触发面收窄到此）
#   P6 恒 exit 2（check-gate.py gate_p6 1051-1093 return 2，无 exit 0 分支）= A1 前提
#   BDD-11：每次推进 append state_transition 事件 = 档位 C 可观测证据
#   BDD-13：check-gate.py exit 0=通过/1=未通过/2=正常通过码（pass 判定以 gate_pass_exit 为准）
#     与 check-state-transition.py exit 0=合法/1=非法 返回约定不被本任务改造（回归守卫，P2 §1.2 Not Modify）
#
# TDD 红灯语义（约束 3）：被测对象 = 新增 agate-next.py，P3 不存在 → subprocess "can't open
#   file"（rc 2）→ 断言 exit==0/1 与文件落盘全部失败 = B 类真红灯（被测模块未实现）。
#   不 mock agate-next.py 本身；check-gate 等既有脚本现状存在，用临时任务目录（task_dir
#   fixture）模拟 .state.yaml 场景即可。
# 平台无关：tmp_path/task_dir fixture + run_cli(python_exe,...)；显式 utf-8；无临时目录字面量（用 tmp_path）。

import json
import re

# 被测新 CLI（P4 实现交付）——P3 现状缺失 → 真红灯锚点
_NEXT_SCRIPT = "agate-next.py"


def _run_next(agate_scripts, python_exe, run_cli, td, env=None):
    """预期 CLI：agate-next.py [TASK_DIR]。P3 脚本缺失 → rc 2（can't open file）。"""
    script = agate_scripts / _NEXT_SCRIPT
    cmd = [python_exe, str(script)]
    if td is not None:
        cmd.append(str(td))
    return run_cli(*cmd, env=env)


def _write_state(agate_root, td, phase, judge=None, retries=None):
    """覆写任务目录 .state.yaml：phase + 可选 judge 块（judge 为 dict）。"""
    lines = ["task_id: T001", f"phase: {phase}", "status: active"]
    if retries:
        lines.append(f"retries: {retries}")
    else:
        lines.append("retries: {}")
    if judge is not None:
        lines.append("judge:")
        lines.append(f"  enabled: {str(judge.get('enabled', True)).lower()}")
        if judge.get("rounds") is not None:
            lines.append(f"  rounds: {judge['rounds']}")
    (td / ".state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_p6_pass_fixture(td):
    """P6 通过路径合规产物：P6-acceptance PASS + 证据 + provenance 可过（审计 2/3 面）。"""
    (td / "P6-acceptance.md").write_text(
        "---\nphase: P6\ntask_id: T001\nagent: verifier\npass: 1\nfail: 0\n---\n"
        "- PASS BDD-1: verified (e1.json)\n",
        encoding="utf-8",
    )
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    # 审计 3 挑验：P1 BDD 计数 = 1（task_dir 默认 P1 有 1 条 BDD）
    (td / "P1-requirements.md").write_text(
        "---\nagent: test\n---\n#### BDD-1: test\n- Given g\n- When w\n- Then t\n",
        encoding="utf-8",
    )


def _write_verdict_pass_fixture(td):
    """P6.5 judge 通过产物：verdict passed + dispatch-context + 证据（check-judge-verdict 可过）。"""
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P6.5-judge-verdict.md").write_text(
        "---\nstatus: passed\ncriteria_total: 1\ncriteria_passed: 1\n"
        'verdict_evidence: ["e1.json"]\n---\n- PASS BDD-1: verified (e1.json)\n',
        encoding="utf-8",
    )
    (td / "P6.5-dispatch-context-judge.md").write_text(
        "---\nphase: P6.5\ntask_id: T001\n---\n\n"
        "### 输入文件\n- P1-requirements.md\n- P6-evidence/\n\n"
        "### 上游关联\n- gate-events.jsonl\n",
        encoding="utf-8",
    )


def _read_state_phase(td):
    text = (td / ".state.yaml").read_text(encoding="utf-8")
    m = re.search(r"^phase:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def _ledger_events(td):
    path = td / "gate-events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# exit2fix：健康任务 P5 正常通过（exit 2 ∈ pass_set）共享夹具。
# gate_p5 成功恒 return 2（check-gate.py L1048，无 exit 0 分支）；无 baseline → 直接 return 2。

def _write_p5_full_pass_fixture(td):
    """P5 正常通过产物（gate_p5 exit 2）：P2-design.md（无 gate_commands.P5 → 无多命令 WARNING）+
    pre-task-baseline.md 损坏场景规避（无 baseline 文件 → 不触发机械 diff，直接 return 2）。"""
    (td / "P2-design.md").write_text(
        "---\nagent: test\n---\n# P2 design\n", encoding="utf-8"
    )


# ── BDD-13 回归守卫（现状绿：既有返回约定不被本任务改造） ─────────────

def test_bdd_13_check_gate_exit_semantics_regression(
    agate_root, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-13：check-gate.py 头注释 exit 0/1/2 三态保留（R8：exit 2 = 正常通过码，pass 判定
    以 phases.yaml gate_pass_exit 为准）+ P1 缺 review 场景 exit 1（未通过）。"""
    head = (agate_root / "scripts" / "check-gate.py").read_text(encoding="utf-8")[:3000]
    assert "exit 0 = gate 通过" in head, "check-gate.py 头注释 exit 0 语义丢失（BDD-13）"
    assert "exit 1 = gate 未通过" in head, "check-gate.py 头注释 exit 1 语义丢失（BDD-13）"
    assert "exit 2" in head, "check-gate.py 头注释 exit 2 语义丢失（BDD-13）"
    assert "gate_pass_exit" in head, "check-gate.py 头注释应说明 exit 2 pass 判定以 gate_pass_exit 为准（R8）"
    td = task_dir()
    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P1", str(td)
    )
    assert result.returncode == 1, "check-gate.py P1 缺 review 场景应 exit 1（回归守卫）"


def test_bdd_13_check_state_transition_exit_semantics_regression(
    agate_root, agate_scripts, python_exe, run_cli, tmp_path
):
    """BDD-13：check-state-transition.py 头注释 exit 0=合法/1=非法保留。"""
    head = (agate_root / "scripts" / "check-state-transition.py").read_text(encoding="utf-8")[:3000]
    assert "exit 0 = 合法" in head and "exit 1 = 非法" in head


# ── BDD-6：exit ∈ gate_pass_exit 直推（P5 exit 2 正常通过码 + P6/P7 锚点） ──

def test_bdd_6_next_exit2_pass_advances_to_next_phase(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6（R3 新语义，CRITICAL-1 补测）：phase=P5 + gate exit 2 ∈ pass_set（P5 正常通过码）
    → agate-next 直推 P6（.state.yaml phase 更新），不落盘 exit2-resolution。
    真实 gate：P5 成功恒 exit 2（gate_p5 L1048）——旧实现（exit 2 一律落盘）在此场景卡死 = 红灯。"""
    td = task_dir()
    _write_state(None, td, "P5")
    _write_p5_full_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"exit ∈ pass_set 直推应 exit 0；rc={result.returncode}"
    assert _read_state_phase(td) == "P6", "P5 gate exit 2（正常通过）→ 应直推 P6（next 字段）"
    assert not (td / "P5-exit2-resolution.md").exists(), "exit 2 正常通过不落盘 resolution（BDD-6 R3）"


def test_bdd_6_p6_judge_disabled_direct_p7_anchor(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-6 P6 通过路径锚点（A1）：phase=P6 + P6 验收产物合规（FAIL=0/证据非空 +
    check-p6-provenance exit 0）+ judge 未启用（历史任务）→ agate-next 按 §3.1 裁决直推 P7。
    P3：agate-next.py 缺失 → 红灯（B 类，被测未实现）。"""
    td = task_dir()
    _write_state(None, td, "P6")  # 无 judge 块 = 历史任务
    _write_p6_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"P6 judge 未启用直推应 exit 0；当前 rc={result.returncode}"
    events = _ledger_events(td)
    assert any(
        ev.get("event") == "state_transition" and ev.get("from") == "P6" and ev.get("to") == "P7"
        for ev in events
    ), "P6→P7 推进应记 state_transition 事件（A1 裁决成立）"


# ── BDD-7：gate exit 1 回退（委托 retreat-to，retry 同步） ──────────────

def test_bdd_7_next_exit1_delegates_retreat_to_retreat_target(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：phase=P5 + gate exit 1（真实前置：pre-task-baseline.md + P5 fail-list 新增失败 →
    gate_p5 机械 diff 判 exit 1）→ 按 retreat:P4 委托 agate-retreat-to（P5→P4 单步）
    + retries[P4] 记录。"""
    td = task_dir()
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    shutil_copytree_into(td, repo)
    task = repo / "task"
    _write_state(None, task, "P5")
    # 真实 gate exit 1 前置：baseline 含 captured_at_commit: + 空 fail-list；
    # P5-test-results/fail-list.txt 放一条基线外的新增失败 → gate_p5 判新增失败 exit 1
    (task / "pre-task-baseline.md").write_text(
        "captured_at_commit: <test-fixture>\n\n```fail-list\n```\n", encoding="utf-8"
    )
    results_dir = task / "P5-test-results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "fail-list.txt").write_text("test_bdd_7_new_failure\n", encoding="utf-8")
    result = _run_next(agate_scripts, python_exe, run_cli, task, env={"AGATE_ROOT": ""})
    assert result.returncode == 0, f"exit 1 委托 retreat-to 应成功；rc={result.returncode}"
    state = (repo / "task" / ".state.yaml").read_text(encoding="utf-8")
    assert "phase: P4" in state, "回退后 phase 应为 P4（retreat 表值）"
    assert "P4:" in state or "retries" in state, "retries[P4] 记录由 retreat-to 同步"


def shutil_copytree_into(td, repo):
    import shutil

    target = repo / "task"
    shutil.copytree(td, target)


def test_bdd_7_p6_exit1_retreats_to_p4_via_retreat_to(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：phase=P6 + gate exit 1 → retreat:P4（diff=2）亦委托 retreat-to 逐阶 P6→P5→P4
    （CLI 不预判 diff，表值存在即委托；state-machine.md:148）。P3 红灯。"""
    td = task_dir()
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    shutil_copytree_into(td, repo)
    _write_state(None, repo / "task", "P6")
    result = _run_next(agate_scripts, python_exe, run_cli, repo / "task", env={"AGATE_ROOT": ""})
    assert result.returncode == 0, f"P6→P4 diff=2 委托 retreat-to 应成功；rc={result.returncode}"
    state = (repo / "task" / ".state.yaml").read_text(encoding="utf-8")
    assert "phase: P4" in state, "P6 gate exit 1 回退目标 = P4（retreat 表值）"


# ── BDD-8：真暂停（exit ∉ gate_pass_exit 且 ≠ 1）落盘 exit2-resolution ──

def test_bdd_8_non_pass_exit_writes_exit2_resolution(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8（R4 收窄语义）：真暂停（exit ∉ gate_pass_exit 且 ≠ 1）→ 不推进 + 落盘
    {phase}-exit2-resolution.md（§3.3 模板）。真实 gate 锚点：phase=P4 + P4-review.md
    status:approved 但缺 agent → gate_p4 L913 return 2，而 P4 的 gate_pass_exit=0
    → 2 ∉ pass_set 且 ≠ 1 = 真暂停。P3 红灯。"""
    td = task_dir()
    _write_state(None, td, "P4")
    (td / "P4-review.md").write_text(
        "---\nstatus: approved\n---\nreviewed.\n", encoding="utf-8"
    )
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"真暂停动作完成应 exit 0；rc={result.returncode}"
    res_file = td / "P4-exit2-resolution.md"
    assert res_file.is_file(), "真暂停应落盘 P4-exit2-resolution.md（BDD-8）"


def test_bdd_8_exit2_resolution_frontmatter_machine_readable(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8：exit2-resolution.md frontmatter 机器可读（phase/task_id/type=exit2-resolution/
    parent=.state.yaml/agent），正文含 触发/客观证据/解决 三节（§3.3 格式）。"""
    td = task_dir()
    _write_state(None, td, "P4")
    (td / "P4-review.md").write_text(
        "---\nstatus: approved\n---\nreviewed.\n", encoding="utf-8"
    )
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"真暂停动作完成应 exit 0；rc={result.returncode}"
    res_file = td / "P4-exit2-resolution.md"
    assert res_file.is_file()
    text = res_file.read_text(encoding="utf-8")
    assert "type: exit2-resolution" in text, "frontmatter type 应为 exit2-resolution"
    assert "task_id:" in text and "phase: P4" in text
    assert "parent:" in text, "frontmatter parent 应声明（§3.3）"
    assert "## 触发" in text and "## 客观证据" in text and "## 解决" in text, "正文三节缺失（§3.3 模板）"


# ── BDD-9：P6 exit 2 前进特例（不落盘不停等） ───────────────────────────

def test_bdd_9_p6_exit2_keeps_advancing_no_resolution_file(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9：P6 exit 2（FAIL=0/证据非空 + provenance exit 0）+ judge 未启用 → 直推 P7，
    不生成 P6-exit2-resolution.md（唯一例外，不泛化）。P3 红灯。"""
    td = task_dir()
    _write_state(None, td, "P6")
    _write_p6_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert not (td / "P6-exit2-resolution.md").exists(), "P6 特例不落盘 exit2-resolution（BDD-9）"


def test_bdd_9_p6_judge_enabled_gate_p65_pass_advances_p7(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9 P6 judge 后推进路径锚点（A1）：judge.enabled=true + verdict/evidence 合规 +
    gate_p65 exit 0 → agate-next 把 phase P6→P7 + state_transition 事件。P3 红灯。"""
    td = task_dir()
    _write_state(None, td, "P6", judge={"enabled": True, "rounds": 1})
    _write_p6_pass_fixture(td)
    _write_verdict_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"judge 通过推 P7 应 exit 0；rc={result.returncode}"
    assert _read_state_phase(td) == "P7", "gate_p65 exit 0 → agate-next 应把 phase 推为 P7"
    events = _ledger_events(td)
    assert any(
        ev.get("event") == "state_transition" and ev.get("to") == "P7" for ev in events
    ), "P6→P7 推进应 append state_transition 事件"


def test_bdd_9_p6_judge_gate_p65_fail_stays_p6(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9 反向锚点（A1）：judge.enabled=true + 缺 verdict（gate_p65 exit 1）→ 停留 P6 不推进、
    不落盘 exit2-resolution（P6 特例豁免）。P3 红灯。"""
    td = task_dir()
    _write_state(None, td, "P6", judge={"enabled": True})
    _write_p6_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, "judge 复核未过 → CLI 提示停留应 exit 0（不推进不报错）"
    assert _read_state_phase(td) == "P6", "gate_p65 exit 1 → 停留 P6"
    assert not (td / "P6-exit2-resolution.md").exists(), "P6 特例不落盘"


# ── BDD-11：档位 C 可观测证据 ───────────────────────────────────────────

def test_bdd_11_state_transition_event_observable(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-11：推进后 gate-events.jsonl 含 state_transition 记录（from/to/ts）——
    档位 C「推进均经 agate next」的可观测证据面（§3.7）。用真实 exit 0 的 P7 场景
    （干净 P7-consistency.md → gate_p7 exit 0 → 消费 P7.next=P8 推进出事件）。"""
    td = task_dir()
    _write_state(None, td, "P7")
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"推进应成功；rc={result.returncode}"
    events = _ledger_events(td)
    transitions = [ev for ev in events if ev.get("event") == "state_transition"]
    assert len(transitions) >= 1, "推进记录应含 state_transition 事件（BDD-11 证据面）"
    ev = transitions[0]
    assert "from" in ev and "to" in ev and "ts" in ev, "state_transition 字段 from/to/ts 齐全"


def test_bdd_11_healthy_exit2_full_advance_no_resolution(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-11（exit2fix CRITICAL-1 盲区补测）：健康任务 P5 exit 2 ∈ pass_set 直推 P6 全链路
    ——经 agate next 推进出 state_transition 事件、不落盘任何 resolution（P0-P3/P5/P8 正常通过码
    exit 2 全程经 CLI 可达成 = 档位 C 可观测证据）。旧实现（exit 2 一律落盘）在此场景停 P5 = 红灯。"""
    td = task_dir()
    _write_state(None, td, "P5")
    _write_p5_full_pass_fixture(td)
    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, f"健康任务 exit 2 直推应 exit 0；rc={result.returncode}"
    assert _read_state_phase(td) == "P6", "P5 exit 2 正常通过 → phase 推进 P6"
    events = _ledger_events(td)
    transitions = [ev for ev in events if ev.get("event") == "state_transition"]
    assert any(
        ev.get("from") == "P5" and ev.get("to") == "P6" for ev in transitions
    ), "P5→P6 推进应记 state_transition 事件（BDD-11 证据面）"
    assert not list(td.glob("*-exit2-resolution.md")), "健康任务无 resolution 落盘（exit 2 正常通过）"


# ── DEBT0045（TAG0042）：一条自称「不阻塞」的警告不得卡住 P6→P7 ──────────
#
# 缺陷形态：`check-p6-provenance.py` 对「缺 agent 字段（协作规范，**不阻塞**）」写 stderr
# 后置 `warning_found=1`，末了 `sys.exit(2)`（脚本 README 的契约：0=通过/1=审计失败/2=WARNING）。
# 但 `agate-next.py::_p6_pass` 只认 `rc == 0` ⇒ **被一条自称不阻塞的警告卡住**：
# 表现为"验收异常"（不指出真因），且暂停时落盘占位 `P6-exit2-resolution.md`
# （易被 `git add <任务目录>` 一并提交——TAG0036 实测）。
#
# 判据：**exit 2（WARNING）与 exit 0（通过）在推进判定上等价**；exit 1（审计失败）仍拦。


def _write_p6_pass_fixture_without_agent(td):
    """与 `_write_p6_pass_fixture` 相同，但产出的 md **全部缺 agent 字段** ⇒ 触发协作规范 WARNING。

    这正是 TAG0036 的真实场景：审计（安全面）全过，只有自报字段缺失这条协作规范警告。
    """
    (td / "P6-acceptance.md").write_text(
        "---\nphase: P6\ntask_id: T001\npass: 1\nfail: 0\n---\n"
        "- PASS BDD-1: verified (e1.json)\n",
        encoding="utf-8",
    )
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P1-requirements.md").write_text(
        "#### BDD-1: test\n- Given g\n- When w\n- Then t\n", encoding="utf-8"
    )


def test_debt0045_warning_only_still_advances_p6_to_p7(
    task_dir, agate_scripts, python_exe, run_cli
):
    """只缺 agent 字段（协作规范 WARNING）→ P6→P7 **仍应推进**（不被警告卡住）。"""
    td = task_dir()
    _write_state(None, td, "P6")  # 无 judge 块 = 历史任务
    _write_p6_pass_fixture_without_agent(td)

    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, (
        f"仅协作规范警告就阻断了推进；rc={result.returncode}\n{result.output[:400]}"
    )
    events = _ledger_events(td)
    assert any(
        ev.get("event") == "state_transition" and ev.get("from") == "P6" and ev.get("to") == "P7"
        for ev in events
    ), "缺 agent 字段（不阻塞）不应阻止 P6→P7 推进"
    # 且不应落盘占位 resolution（那是"真暂停"的产物）
    assert not (td / "P6-exit2-resolution.md").exists(), (
        "警告不该落盘 exit2-resolution（会被 git add 一并提交）"
    )


def test_debt0045_audit_failure_still_blocks(task_dir, agate_scripts, python_exe, run_cli):
    """负向对照：**审计失败（exit 1）必须仍然阻断**——修复不得把真失败也放行。"""
    td = task_dir()
    _write_state(None, td, "P6")
    # PASS 行引用不存在的证据 → 审计 1（证据-结论对应）失败 ⇒ exit 1
    (td / "P6-acceptance.md").write_text(
        "---\nphase: P6\ntask_id: T001\nagent: verifier\npass: 1\nfail: 0\n---\n"
        "- PASS BDD-1: verified (missing-e1.json)\n",
        encoding="utf-8",
    )
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P1-requirements.md").write_text(
        "---\nagent: test\n---\n#### BDD-1: test\n- Given g\n- When w\n- Then t\n", encoding="utf-8"
    )

    result = _run_next(agate_scripts, python_exe, run_cli, td)
    # ⚠️ 本 CLI 的契约是「**不推进**」而非「非零退出」：审计失败时它 `sys.exit(0)` +
    # stderr 提示「暂停转主 Agent 决策」，故判据落在**是否推进**（账本事件 + 产物），
    # 不是 returncode。（初版误用 returncode 断言，当场被这条负向对照证伪。）
    assert not any(
        ev.get("event") == "state_transition" and ev.get("to") == "P7"
        for ev in _ledger_events(td)
    ), "审计失败时不得推进到 P7"
    # 提示须**同时**说明：① 是审计失败（非警告）② 暂停待人工决策
    assert "审计失败" in result.output, f"审计失败须明确措辞：{result.output[:300]}"
    assert "暂停" in result.output, f"须说明暂停（否则静默停留）：{result.output[:300]}"


def test_debt0045_audit_failure_relays_specific_reason(
    task_dir, agate_scripts, python_exe, run_cli
):
    """DEBT0045 closure_criteria #2：审计失败时**暂停信息须含 provenance 的具体原因行**。

    回归来历：初版只改了 exit 2 分支，exit 1 仍只打「验收异常」——主 Agent 必须手动再跑一次
    provenance 才知道原因（债的 impact 原文即此）。独立评审实测输出不含「不存在」等关键词，
    据此判该 closure_criteria 未满足。
    """
    td = task_dir()
    _write_state(None, td, "P6")
    (td / "P6-acceptance.md").write_text(
        "---\nphase: P6\ntask_id: T001\nagent: verifier\npass: 1\nfail: 0\n---\n"
        "- PASS BDD-1: verified (missing-e1.json)\n",
        encoding="utf-8",
    )
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P1-requirements.md").write_text(
        "---\nagent: test\n---\n#### BDD-1: test\n- Given g\n- When w\n- Then t\n", encoding="utf-8"
    )

    result = _run_next(agate_scripts, python_exe, run_cli, td)
    assert not any(
        ev_.get("event") == "state_transition" and ev_.get("to") == "P7"
        for ev_ in _ledger_events(td)
    ), "审计失败不得推进"
    # 关键：原因行须被转达（不必逐字匹配脚本实现，抓 provenance 前缀与缺失文件名即可）
    assert "provenance" in result.output, f"未转达 provenance 原因：{result.output[:400]}"
    assert "missing-e1.json" in result.output, (
        f"未转达具体缺失项（主 Agent 仍须手动复跑才能定位）：{result.output[:400]}"
    )


def test_debt0045_renders_all_warnings_not_just_first(
    task_dir, agate_scripts, python_exe, run_cli
):
    """多条 WARNING 时**不得只转达第一条**（初版 `break` 会丢信息）。"""
    td = task_dir()
    _write_state(None, td, "P6")
    # P6 与另一阶段产出同时缺 agent 字段 ⇒ 至少 2 条 WARNING
    (td / "P6-acceptance.md").write_text(
        "---\nphase: P6\ntask_id: T001\npass: 1\nfail: 0\n---\n"
        "- PASS BDD-1: verified (e1.json)\n",
        encoding="utf-8",
    )
    (td / "P2-design.md").write_text("---\nphase: P2\n---\n# design\n", encoding="utf-8")
    ev = td / "P6-evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "e1.json").write_text("evidence\n", encoding="utf-8")
    (td / "P1-requirements.md").write_text(
        "#### BDD-1: test\n- Given g\n- When w\n- Then t\n", encoding="utf-8"
    )

    result = _run_next(agate_scripts, python_exe, run_cli, td)
    # 推进仍应发生（只是警告），但警告不得被截断成一条
    assert result.output.count("缺 agent 字段") >= 2, (
        f"多条 WARNING 被截断（初版 break 的缺陷）：{result.output[:500]}"
    )
