# agate/tests/integration/test_tag0050_evidence.py
# TAG0050 批 D（验收结论与证据绑定）红灯测试。
#
# 映射：BDD-56..BDD-60（P1-requirements.md §4；设计 §5、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h


def _snapshot(agate_root):
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert level1.is_file(), "批 D：须有契约快照 level-1.yaml（results/criteria）"
    return level1.read_text(encoding="utf-8")


def _write_p1_bdds(d, n=1):
    """给 init 任务写含 n 条 `#### BDD-i:` 的 P1（results 集合须与之相等）。"""
    heads = "".join(f"#### BDD-{i}: b{i}\n- Given a\n" for i in range(1, n + 1))
    (d / "P1-requirements.md").write_text(
        "---\nagent: test\nrisk_level: high\n"
        "phases: [P1, P2, P3, P4, P5, P6, P7, P8]\npackages: [p]\ndomains: [backend]\n"
        "---\n\n[NO_NEED_CONFIRM]\n\n" + heads,
        encoding="utf-8",
    )


def _write_structured_p6(d, results_yaml):
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\nresults:\n" + results_yaml + "---\nbody\n",
        encoding="utf-8",
    )


@pytest.mark.windows_smoke
def test_bdd_56_f1_abc_tampering_turns_red(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-56：F1 的 A（改 FAIL）/B（删条目）/C（重复）三种篡改全部转红（D1/D2）。"""
    # A：全部 PASS → 改一条为 FAIL
    d = h.init_task_via_conftest(tmp_path)
    _write_p1_bdds(d, 1)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P6-evidence" / "e.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    _write_structured_p6(d, "  - {bdd: '1', verdict: FAIL, evidence: [e.log]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D2" in r.output, f"F1-A 改 FAIL 须转红：{r.output}"

    # B：删除条目（P1 有 BDD-2，results 缺）→ D1 集合不等
    d2 = h.init_task_via_conftest(tmp_path / "b")
    _write_p1_bdds(d2, 2)
    (d2 / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d2 / "P6-evidence" / "e.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    _write_structured_p6(d2, "  - {bdd: '1', verdict: PASS, evidence: [e.log]}\n")
    r2 = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d2))
    assert r2.returncode == 1 and "D1" in r2.output, f"F1-B 删条目须转红：{r2.output}"

    # C：重复条目
    d3 = h.init_task_via_conftest(tmp_path / "c")
    _write_p1_bdds(d3, 1)
    (d3 / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d3 / "P6-evidence" / "e.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    _write_structured_p6(
        d3,
        "  - {bdd: '1', verdict: PASS, evidence: [e.log]}\n"
        "  - {bdd: '1', verdict: PASS, evidence: [e.log]}\n",
    )
    r3 = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d3))
    assert r3.returncode == 1 and "重复" in r3.output, f"F1-C 重复条目须转红：{r3.output}"


def test_bdd_57_ignored_evidence_errors(git_repo, agate_scripts, python_exe, run_cli):
    """BDD-57：证据被 ignore 判 ERROR（D3，经 gate_p6 新路径）。"""
    repo = git_repo.path
    d = h.init_task_via_conftest(repo)
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (d / "P6-evidence" / "e.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    _write_structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [e.log]}\n")
    r = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d), cwd=str(repo)
    )
    assert r.returncode == 1 and "忽略" in r.output, f"D3 被忽略证据须 ERROR：{r.output}"


def test_bdd_58_pass_log_nonzero_exit_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-58：PASS 条目日志 EXIT_CODE≠0 判 ERROR（D6，经 gate_p6 新路径）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    # 同时保留一个合规证据避免 D4 未引用噪声（这里只引用 log 本身）。
    (d / "P6-evidence" / "bdd-01.log").write_text("run\nEXIT_CODE: 1\n", encoding="utf-8")
    _write_structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [bdd-01.log]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D6" in r.output, f"D6 EXIT_CODE≠0 须 ERROR：{r.output}"


def test_bdd_59_run_ref_sha256_mismatch_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-59：`run:<k>` 引用的 sha256 与 cmd_run 事件不一致判 ERROR（构造真实不一致）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "runs").mkdir(exist_ok=True)
    (d / "runs" / "1.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    # 账本追加一条 cmd_run 事件，sha256 故意写成错值（与 runs/1.log 实际内容不一致）。
    h.write_ledger(
        d,
        [
            {"event": "task_created", "task_id": "T001", "contract_level": 1},
            {"event": "cmd_run", "task_id": "T001", "k": 1, "sha256": "deadbeef"},
        ],
    )
    _write_structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: ['run:1']}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "sha256" in r.output, (
        f"BDD-59：sha256 不一致须 ERROR，实际：{r.output}"
    )


def test_bdd_60_extract_context_counts_equal_computed(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-60：extract-context 计数等于按字段现算的值（断言计数 == 现算值，非仅 rc==0）。"""
    d = h.init_task_via_conftest(tmp_path)
    # phase=P7 → extract-context 输出 P6 验收计数（经字段现算：pass/fail from results）。
    (d / ".state.yaml").write_text("task_id: T001\nphase: P7\nretries: {}\n", encoding="utf-8")
    (d / "P6-evidence").mkdir(exist_ok=True)
    (d / "P6-evidence" / "ev.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\npass: 0\nfail: 0\n"
        "results:\n  - {bdd: '1', verdict: PASS, evidence: [ev.log]}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "agate-extract-context.py"), str(d))
    assert r.returncode == 0, f"BDD-60：extract-context 须按字段现算，实际 rc={r.returncode}"
    # 判别性断言：计数须 == 现算值（1 条 PASS / 0 条 FAIL），而非仅 rc==0。
    assert "P6 验收: 1 PASS, 0 FAIL" in r.output, r.output


def test_gap6_d5_duplicate_content_warns_not_blocked(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-6 / D5：不同文件内容相同 → WARNING（可共享引用），不阻断。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P1-requirements.md").write_text(
        "---\nagent: test\nrisk_level: high\n"
        "phases: [P1, P2, P3, P4, P5, P6, P7, P8]\npackages: [p]\ndomains: [backend]\n"
        "---\n\n[NO_NEED_CONFIRM]\n\n#### BDD-1: a\n- Given a\n"
        "#### BDD-2: b\n- Given b\n",
        encoding="utf-8",
    )
    ev = d / "P6-evidence"
    ev.mkdir(exist_ok=True)
    (ev / "ev.log").unlink(missing_ok=True)  # 避免 D4 未引用
    (ev / "a.log").write_text("same\nEXIT_CODE: 0\n", encoding="utf-8")
    (ev / "b.log").write_text("same\nEXIT_CODE: 0\n", encoding="utf-8")
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\n"
        "results:\n"
        "  - {bdd: '1', verdict: PASS, evidence: [a.log]}\n"
        "  - {bdd: '2', verdict: PASS, evidence: [b.log]}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode != 1, f"D5 仅 WARNING，不阻断，实际 rc={r.returncode}"
    assert "共享引用" in r.output, r.output


def test_gap6_d7_evidence_json_fail_vs_results_pass(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-6 / D7：evidence JSON 显示 FAIL 但 results 标 PASS → ERROR（取代审计 6）。"""
    d = h.init_task_via_conftest(tmp_path)
    ev = d / "P6-evidence"
    ev.mkdir(exist_ok=True)
    (ev / "ev.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    (ev / "res.json").write_text(
        '{"results": [{"bdd": "1", "status": "fail"}]}', encoding="utf-8"
    )
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\n"
        "results:\n  - {bdd: '1', verdict: PASS, evidence: [ev.log, res.json]}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1, f"D7：evidence JSON FAIL vs results PASS 须 ERROR，实际 rc={r.returncode}"
    assert "D7" in r.output, r.output


def test_gap6_d9_reuse_blocked_from_results(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-6 / D9：results 引用 P5 结果 + p5_pass_commit 不可解析 → reuse_blocked → ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P5-test-results").mkdir(exist_ok=True)
    (d / "P5-test-results" / "unit.md").write_text("P5 pass\n", encoding="utf-8")
    (d / ".state.yaml").write_text(
        "task_id: T001\nphase: P6\np5_pass_commit: deadbeef\nretries: {}\n",
        encoding="utf-8",
    )
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\n"
        "results:\n  - {bdd: '1', verdict: PASS, evidence: ['../P5-test-results/unit.md']}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1, f"D9：reuse_blocked 须 ERROR，实际 rc={r.returncode}"
    assert "D9" in r.output, r.output


def test_gap7_provenance_body_audit_skipped_for_non_legacy(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-7：非 legacy 任务跳过 provenance 正文解析（缺证据不再拦截；D1–D10 取代）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\n---\n- PASS BDD-1 (missing-evidence.log)\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-p6-provenance.py"), str(d))
    assert r.returncode != 1, f"GAP-7：非 legacy 跳过正文解析，实际 rc={r.returncode}"


# ── C8 整改（第 2 轮）新增用例：BLOCKER-1 / MINOR-2 / MINOR-3 / cso F-1 ──────────


def _write_judge_files(d, *, criteria_yaml):
    """给非 legacy 任务写 P6.5 verdict + dispatch-context + 证据（BLOCKER-1 用例）。"""
    (d / "P6-evidence" / "e1.json").write_text('{"ok": true}', encoding="utf-8")
    (d / "P6.5-judge-verdict.md").write_text(
        "---\nagent: judge\nstatus: passed\n" + criteria_yaml + "---\n\nverdict body\n",
        encoding="utf-8",
    )
    (d / "P6.5-dispatch-context-judge.md").write_text(
        "---\nphase: P6.5\ntask_id: T001\n---\n\n### 输入文件\n"
        "- P1-requirements.md\n- P6-evidence/\n- .state.yaml\n\n"
        "### 上游关联\n- gate-events.jsonl\n- P6.5-judge-verdict.md\n",
        encoding="utf-8",
    )


def test_blocker1_non_legacy_criteria_pass_exit_0(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BLOCKER-1 正向：非 legacy 声明 `criteria` 且 status=passed → exit 0。

    （改前：`read_judge_verdict` 丢弃 `criteria` → 恒报「非 legacy 须声明 criteria」死锁。）
    """
    d = h.init_task_via_conftest(tmp_path)
    _write_judge_files(
        d,
        criteria_yaml=(
            "criteria:\n"
            "  - {bdd: '1', verdict: PASS, evidence: [e1.json]}\n"
        ),
    )
    r = run_cli(python_exe, str(agate_scripts / "check-judge-verdict.py"), str(d))
    assert r.returncode == 0, f"BLOCKER-1：非 legacy 声明 criteria 须 exit 0，实际：{r.output}"


def test_blocker1_non_legacy_criteria_missing_exit_1(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BLOCKER-1 负向：非 legacy 缺 `criteria` → exit 1（不再是「系统字段缺失」先行误报）。"""
    d = h.init_task_via_conftest(tmp_path)
    _write_judge_files(d, criteria_yaml="")
    r = run_cli(python_exe, str(agate_scripts / "check-judge-verdict.py"), str(d))
    assert r.returncode == 1, f"BLOCKER-1：缺 criteria 须 exit 1，实际：{r.output}"
    assert "criteria" in r.output, r.output


def _structured_p6(d, results_yaml):
    (d / "P6-acceptance.md").write_text(
        "---\nagent: test\nprod_touched: false\nresults:\n" + results_yaml + "---\nbody\n",
        encoding="utf-8",
    )


def test_minor2_d8_screenshot_requires_vision_when_available(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-2：截图条目、无视觉能力声明（默认 available）→ 须 vision，缺则 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    shots = d / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    (shots / "b1.png").write_text("png", encoding="utf-8")
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [screenshots/b1.png]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D8" in r.output, r.output


def test_minor2_d8_gap_requires_manual_review(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-2：P1 视觉能力=GAP → 截图条目须 manual_review；缺则 ERROR（vision 不算）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P1-requirements.md").write_text(
        "---\nagent: test\nrisk_level: high\n"
        "phases: [P1, P2, P3, P4, P5, P6, P7, P8]\npackages: [p]\ndomains: [backend]\n"
        "---\n\n[NO_NEED_CONFIRM]\n\n#### BDD-1: b\n- Given a\n"
        "\n```yaml\ncapability_requirements:\n"
        "  - need: visual-analysis\n    status: GAP\n```\n",
        encoding="utf-8",
    )
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    shots = d / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    (shots / "b1.png").write_text("png", encoding="utf-8")
    # 带 vision 但缺 manual_review → GAP 分支仍须 ERROR。
    _structured_p6(
        d,
        "  - {bdd: '1', verdict: PASS, evidence: [screenshots/b1.png], vision: v.yaml}\n",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "manual_review" in r.output, r.output


def test_minor2_d8_screenshot_detection_is_structural(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-2：截图判定为结构化（目录段名 `screenshots`）——`xscreenshots/` 不误命中。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    d2 = d / "P6-evidence" / "xscreenshots"
    d2.mkdir(parents=True, exist_ok=True)
    (d2 / "b1.png").write_text("png", encoding="utf-8")
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [xscreenshots/b1.png]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode != 1, f"MINOR-2：xscreenshots 非截图，不应触发 D8，实际：{r.output}"


def test_minor3_d7_json_shape_non_list_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-3：evidence JSON 的 results 非列表 → ERROR（D7 证据形态）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P6-evidence" / "res.json").write_text('{"results": "oops"}', encoding="utf-8")
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [res.json]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D7" in r.output and "形态" in r.output, r.output


def test_minor3_d7_json_shape_non_dict_element_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-3：evidence JSON 的 results 元素非映射 → ERROR（D7 证据形态）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P6-evidence" / "res.json").write_text('{"results": ["x"]}', encoding="utf-8")
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [res.json]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D7" in r.output and "形态" in r.output, r.output


def test_minor3_d7_multi_json_conflict_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-3：同一 bdd 跨多个 evidence JSON 状态冲突（PASS/FAIL 并存）→ ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P6-evidence" / "a.json").write_text(
        '{"results": [{"bdd": "1", "status": "pass"}]}', encoding="utf-8"
    )
    (d / "P6-evidence" / "b.json").write_text(
        '{"bdd_results": [{"bdd": "1", "status": "fail"}]}', encoding="utf-8"
    )
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: [a.json, b.json]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "D7" in r.output, r.output


def test_minor3_d7_reverse_results_fail_evidence_pass(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-3 反向：results 标 FAIL 而 evidence 标 PASS → 拦截（D2 或 D7 反向）。

    说明：非 legacy 判据 D2 要求全 PASS，故该反向在 gate_p6 内被 D2 先行拦截；
    D7 反向为纵深防御（此处断言整体拦截，非 D7 文案专属）。
    """
    d = h.init_task_via_conftest(tmp_path)
    (d / "P6-evidence" / "ev.log").unlink(missing_ok=True)
    (d / "P6-evidence" / "res.json").write_text(
        '{"results": [{"bdd": "1", "status": "pass"}]}', encoding="utf-8"
    )
    _structured_p6(d, "  - {bdd: '1', verdict: FAIL, evidence: [res.json]}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and ("D2" in r.output or "D7" in r.output), r.output


def test_cso_f1_run_event_missing_sha256_fail_closed(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """cso F-1：`run:<k>` 的 cmd_run 事件缺 sha256 → fail-closed（事件不完整）。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "runs").mkdir(exist_ok=True)
    (d / "runs" / "1.log").write_text("run\nEXIT_CODE: 0\n", encoding="utf-8")
    h.write_ledger(
        d,
        [
            {"event": "task_created", "task_id": "T001", "contract_level": 1},
            {"event": "cmd_run", "task_id": "T001", "k": 1, "log": "runs/1.log"},
        ],
    )
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: ['run:1']}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "不完整" in r.output, r.output


def test_cso_f3_run_empty_log_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """cso F-3：`run:<k>` 指向空文件 → ERROR（D3 要求非空文件）。"""
    import hashlib as _hashlib

    d = h.init_task_via_conftest(tmp_path)
    (d / "runs").mkdir(exist_ok=True)
    (d / "runs" / "1.log").write_text("", encoding="utf-8")
    empty_sha = _hashlib.sha256(b"").hexdigest()
    h.write_ledger(
        d,
        [
            {"event": "task_created", "task_id": "T001", "contract_level": 1},
            {"event": "cmd_run", "task_id": "T001", "k": 1, "log": "runs/1.log",
             "sha256": empty_sha},
        ],
    )
    _structured_p6(d, "  - {bdd: '1', verdict: PASS, evidence: ['run:1']}\n")
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode == 1 and "空" in r.output, r.output
