# agate/tests/integration/test_tag0050_a0_a1_ledger.py
# TAG0050 批 A0（F8 / check-gate 不存在目录）与批 A1（契约等级与账本完整性）红灯测试。
#
# 映射：BDD-01..BDD-22（P1-requirements.md §4；设计 §2.1–2.3、2.5、2.6、§10）。
# 红灯口径（check-tdd-red）：实现未写 ⇒ 运行期失败 / 未实现符号 AttributeError（B 类）。
#   * 不写 module-level import 缺失符号（避免 collection error 被判 A 类）。
#   * `init_task()`（A1 交付物）经 helpers_tag0050.init_task_via_conftest 运行期取用。
#   * 断言消息不含 A 类关键词（Traceback / ImportError / SyntaxError / ModuleNotFoundError）。
# 平台无关：tmp_path / git_repo fixture；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

# ── 批 A0 ──────────────────────────────────────────────────────────────────


@pytest.mark.windows_smoke
def test_bdd_01_paused_prod_touched_persisted(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-01：PAUSED 下的生产接触留痕真实落盘（修复 F8）。

    Given 任务进入 PAUSED 且本次提交写入 [PROD_TOUCHED]
    When pre-commit 处理该提交
    Then 账本中真实追加一条 prod_touched_in_paused 事件（可 grep 到）。
    """
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: PAUSED\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    (task / "P5-verification.md").write_text(
        "---\nagent: test\n---\n\n[PROD_TOUCHED] 接触生产\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/.state.yaml")
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)

    ledger = task / "gate-events.jsonl"
    assert ledger.is_file(), "BDD-01：PAUSED 的生产接触留痕须真实落盘（F8：append_event 参数错）"
    assert "prod_touched_in_paused" in ledger.read_text(encoding="utf-8"), (
        "BDD-01：账本须含 prod_touched_in_paused 事件"
    )


@pytest.mark.parametrize("phase", ["P7", "P5", "P0"])
def test_bdd_02_nonexistent_task_dir_returns_1(
    tmp_path, agate_scripts, python_exe, run_cli, phase
):
    """BDD-02：check-gate 对不存在的任务目录返回 1（所有 phase 统一）。

    Given 一个不存在的任务目录路径
    When 运行 check-gate.py <phase> <不存在的目录>
    Then 退出码为 1（不再返回 0/2 造成假 PASS）。
    """
    missing = tmp_path / "does-not-exist-TAGXXXX"
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), phase, str(missing))
    assert r.returncode == 1, f"BDD-02：{phase} 对不存在目录须 rc=1，实际 rc={r.returncode}"


# ── 批 A1：契约等级与账本完整性 ─────────────────────────────────────────────


def _run_check_events(run_cli, python_exe, agate_scripts, task):
    return run_cli(python_exe, str(agate_scripts / "check-events.py"), str(task))


def test_bdd_03_downgrade_event_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-03：追加降级事件被判 ERROR。"""
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 2},
        {"event": "task_upgraded", "from_level": 2, "to_level": 1, "at_phase": "P4"},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert r.returncode != 0, f"BDD-03：降级事件须 ERROR，实际 rc={r.returncode}"


def test_bdd_04_second_task_created_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-04：第 2 条 task_created 被判 ERROR。"""
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 1},
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 1},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert r.returncode != 0, f"BDD-04：第 2 条 task_created 须 ERROR，实际 rc={r.returncode}"


def test_bdd_05_task_created_not_first_line_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-05：task_created 不在第 1 行被判 ERROR。"""
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "gate_run", "phase": "P1", "exit": 0},
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 1},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert r.returncode != 0, f"BDD-05：task_created 非首行须 ERROR，实际 rc={r.returncode}"


def test_bdd_06_unregistered_contract_level_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-06：未登记的 contract_level 被判 ERROR。"""
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 42},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert r.returncode != 0, f"BDD-06：未登记等级须 ERROR，实际 rc={r.returncode}"


def test_bdd_07_handwritten_low_level_new_task_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-07：手写低等级的新任务被判 ERROR（本地检查）。

    Given 新建任务目录，账本首行手写低于当前等级的 contract_level
    When 在本地提交/校验
    Then 判 ERROR；且须提供 agate-task-init.py（新建入口）。
    """
    assert (agate_scripts / "agate-task-init.py").is_file(), (
        "BDD-07：须提供 agate-task-init.py 作为新建入口（当前缺失）"
    )
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 0},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert r.returncode != 0, f"BDD-07：低于当前等级须 ERROR，实际 rc={r.returncode}"


def test_bdd_08_created_backfill_keeps_judge(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-08：回填或删除 created 后 judge 强制仍生效（修复 F3a）。"""
    d = h.init_task_via_conftest(tmp_path)
    p1 = d / "P1-requirements.md"
    text = p1.read_text(encoding="utf-8")
    p1.write_text("\n".join(
        ln for ln in text.splitlines() if not ln.startswith("created:")
    ) + "\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P1", str(d))
    assert r.returncode != 0, f"BDD-08：删除 created 后 judge 仍须强制，实际 rc={r.returncode}"


def test_bdd_09_judge_enabled_false_p65_still_blocks(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-09：P6 改 judge.enabled:false 后 P6.5 仍阻断（修复 F3b）。"""
    d = h.init_task_via_conftest(tmp_path)
    state = d / ".state.yaml"
    state.write_text(
        state.read_text(encoding="utf-8").rstrip("\n") + "\njudge:\n  enabled: false\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6.5", str(d))
    assert r.returncode != 0, f"BDD-09：P6.5 须仍阻断（不读 judge.enabled），实际 rc={r.returncode}"


def test_bdd_10_created_backfill_keeps_evidence_ref_blocking(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-10：回填 created 不改变 evidence_ref 强制级别（修复 F3c）。"""
    d = h.init_task_via_conftest(tmp_path)
    p1 = d / "P1-requirements.md"
    text = p1.read_text(encoding="utf-8")
    p1.write_text(text.replace("created:", "created: 2000-01-01  # "), encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-p6-evidence.py"), str(d))
    assert r.returncode != 0, f"BDD-10：evidence_ref 须仍阻断（rc=1），实际 rc={r.returncode}"


def test_bdd_11_new_dir_without_created_event_errors(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-11：新增无创建事件的目录判 ERROR；--existing 补写后转绿。

    本用例断言前半（判 ERROR）与入口存在性；--existing 转绿由 P4 实现后追加。
    """
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P0\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    (task / "P0-brief.md").write_text(
        'task: "x"\nknown_risks: []\nexecutor_env:\n  platform: "opencode"\n'
        "  has_task_tool: true\n  has_local_runtime: true\n  network: \"full\"\n"
        'env_constraints:\n  debug_env: "echo"\n',
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/.state.yaml")
    git_repo.stage("agate-workspace/tasks/TAG0001/P0-brief.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-11：无创建事件的新目录须 ERROR，实际 rc={r.returncode}"
    assert (agate_scripts / "agate-task-init.py").is_file(), (
        "BDD-11：--existing 补写入口 agate-task-init.py 须存在"
    )


def test_bdd_12_git_mv_legacy_stays_legacy(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-12：git mv legacy 目录后仍为 legacy 且不报错。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    h.write_ledger(task, [{"event": "gate_run", "phase": "P5", "exit": 0}])
    git_repo.commit("add legacy task")
    moved = repo / "agate-workspace" / "tasks" / "TAG0001-renamed"
    git_repo.git("mv", str(task), str(moved))
    ac = h.agate_common_module(agate_scripts)
    assert ac.task_level(str(moved)) is None, "BDD-12：改名后的 legacy 目录须仍为 legacy"
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode == 0, f"BDD-12：legacy 改名不应报错，实际 rc={r.returncode}"


def test_bdd_13_rewrite_or_delete_created_ledger_errors(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-13：改写或删除已有创建事件的账本判 ERROR。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("task with created event")
    git_repo.git("rm", "-q", "agate-workspace/tasks/TAG0001/gate-events.jsonl")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-13：删除含创建事件的账本须 ERROR，实际 rc={r.returncode}"


def test_bdd_14_legacy_done_to_p1_errors(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-14：legacy 任务从 DONE 回到 P1 判 ERROR（提示 --adopt 或新建）。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    state = task / ".state.yaml"
    state.write_text(
        "task_id: TAG0001\nphase: DONE\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy done task")
    state.write_text(
        "task_id: TAG0001\nphase: P1\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/.state.yaml")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert "--adopt" in r.output or "legacy" in r.output.lower(), (
        "BDD-14：legacy 重开须给 --adopt/新建指引"
    )


def test_bdd_15_published_snapshot_freeze(agate_root):
    """BDD-15：修改已发布快照或新增未登记快照判 consistency ERROR。

    断言快照冻结面存在（LEVELS.yaml 登记 + level-N.yaml）；字节 sha256 由
    test_tag0050_fitness.py 的 task_data_freeze 承担。
    """
    levels = agate_root / "rules" / "task-data" / "LEVELS.yaml"
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert levels.is_file(), "BDD-15：须有 agate/rules/task-data/LEVELS.yaml 登记快照"
    assert level1.is_file(), "BDD-15：须有 agate/rules/task-data/level-1.yaml 冻结快照"


def test_bdd_16_golden_fixtures_exist(agate_root):
    """BDD-16：每个已登记等级的一组黄金 fixture（pass/fail）存在。"""
    base = agate_root / "tests" / "fixtures" / "task-data" / "level-1"
    assert (base / "pass").is_dir(), "BDD-16：须有 level-1/pass 黄金 fixture"
    assert (base / "fail").is_dir(), "BDD-16：须有 level-1/fail 黄金 fixture"


def test_bdd_17_task_level_above_protocol_fails_closed(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-17：任务等级高于运行中协议最大等级时 fail-closed 并提示升级。"""
    task = tmp_path / "TAG0001"
    task.mkdir()
    h.write_ledger(task, [
        {"event": "task_created", "task_id": "TAG0001", "contract_level": 42},
    ])
    r = _run_check_events(run_cli, python_exe, agate_scripts, task)
    assert "升级" in r.output or "协议版本低于" in r.output, (
        "BDD-17：须 fail-closed 并提示『协议版本低于任务等级，请升级』"
    )


def test_bdd_18_legacy_output_only_prod_touched_scanned(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-18：只暂存产出未改 phase 时 legacy 任务也做 PROD_TOUCHED 扫描。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-verification.md").write_text(
        "---\nagent: test\n---\n\n[PROD_TOUCHED] 接触生产\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-18：安全门不再依赖『是否改了 phase』，实际 rc={r.returncode}"


def test_bdd_19_non_legacy_staged_output_reruns_phase_gate(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-19：非 legacy 任务按被暂存产出所属阶段重跑 gate（含 HEAD=READY）。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode != 0, f"BDD-19：须按被暂存产出所属阶段重跑 gate，实际 rc={r.returncode}"


def test_bdd_20_p7_adopted_p4_prose_gap_counted(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-20：P7 迁入任务的 P4 散文缺口仍由旧读取器计数。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-20：未覆盖的 P4 散文缺口须判 ERROR，实际 rc={r.returncode}"


def test_bdd_21_consecutive_upgrades_per_phase_level(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-21：连续两次升级时各阶段取各自等级（不统一取最高/最低）。"""
    d = h.init_task_via_conftest(tmp_path)
    ac = h.agate_common_module(agate_scripts)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P4", str(d))
    assert callable(getattr(ac, "requirement_active", None)), (
        "BDD-21：须提供 requirement_active(task, name, phase) 按阶段取等级"
    )
    assert r.returncode == 0, f"BDD-21：各阶段按各自等级判定，实际 rc={r.returncode}"


def test_bdd_22_r6_differential_deliverable(agate_root):
    """BDD-22：两仓副本 R6 差分符合设计 §8（脚本 + 机器可读 allowlist 存在）。"""
    script = agate_root.parent / "docs" / "design-notes" / "r6-differential.sh"
    allow = agate_root.parent / "docs" / "design-notes" / "r6-allowlist.yaml"
    assert script.is_file(), "BDD-22：须交付 docs/design-notes/r6-differential.sh"
    assert allow.is_file(), "BDD-22：须交付 docs/design-notes/r6-allowlist.yaml"
