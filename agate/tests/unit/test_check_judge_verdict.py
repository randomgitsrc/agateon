# tests/unit/test_check_judge_verdict.py — P6.5 judge verdict 机械校验（check-judge-verdict.py）
# （TAG0020 新增：BDD-1/3/4/5/6/8/9；映射见 P3-test-cases.md §2）
# 被测：agate/scripts/check-judge-verdict.py TASK_DIR（exit 0 = 通过 / exit 1 = 校验不通过）。
# 校验链（P2-design §3.3）：verdict/dispatch-context 存在性 → Header 字段（BDD-5）→ BDD 计数
#   与编号集对照（BDD-3）→ 三数全等 + partial 约束（BDD-5/8）→ 证据交叉核对（BDD-6）→
#   信息隔离白名单（BDD-4）→ 账本 budget_exhausted 交叉（BDD-8）→ 机械核对兜底（BDD-9）。
# TDD 红灯语义：脚本未实现 → subprocess 运行触发 "can't open file"（返回码 2 + stderr），
#   全部 exit 0/1 断言失败 = 真实 B 类红灯（模块未实现，非测试自身语法错误）。
# 平台无关（AGENTS.md 测试约定）：tmp_path/task_dir fixture；文件 I/O 显式 encoding="utf-8"；
#   平台临时目录字面量与软链接语义零假设，解释器一律走 python_exe fixture 探测。

import hashlib
import importlib.util
import json
import re

import pytest

from conftest import add_p1_bdd


def _run_judge(agate_scripts, python_exe, run_cli, td):
    """check-judge-verdict.py TASK_DIR 等价（合并流 result.output 断言）。"""
    return run_cli(python_exe, str(agate_scripts / "check-judge-verdict.py"), str(td))


def _p1_bdd_count(td):
    """P1 BDD 标题数，计数口径 = check-p6-provenance 审计 3：`^#### BDD-[0-9]`。"""
    text = (td / "P1-requirements.md").read_text(encoding="utf-8")
    return len(re.findall(r"^#### BDD-[0-9]", text, re.M))


def _write_evidence(td, rel_path, content):
    full = td / "P6-evidence" / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


def _write_verdict(td, status="passed", criteria_total=1, criteria_passed=1,
                   evidence=None, conclusions=None, partial=None):
    """构造 P6.5-judge-verdict.md。evidence: list[str]（verdict_evidence 引用）；
    conclusions: list[str] 正文结论行；缺省 = 按 P1 BDD 数生成 PASS 行引用第 1 个证据。"""
    if evidence is None:
        evidence = ["e1.json"]
    if conclusions is None:
        conclusions = [
            f"- PASS BDD-{i}: verified ({evidence[0]})"
            for i in range(1, _p1_bdd_count(td) + 1)
        ]
    header = "---\n"
    header += f"status: {status}\n"
    header += f"criteria_total: {criteria_total}\n"
    header += f"criteria_passed: {criteria_passed}\n"
    header += f"verdict_evidence: {json.dumps(evidence)}\n"
    if partial is not None:
        header += f"partial: {str(partial).lower()}\n"
    header += "---\n"
    (td / "P6.5-judge-verdict.md").write_text(
        header + "\n".join(conclusions) + "\n", encoding="utf-8"
    )


def _write_dispatch_context(td, inputs=None, upstream=None, extra_body=""):
    """P6.5-dispatch-context-judge.md：默认两节只含白名单项（合规基线）。
    节标题沿用 assets/templates/dispatch-context.md（### 上游关联 / ### 输入文件）。"""
    if inputs is None:
        inputs = ["P1-requirements.md", "P6-evidence/", ".state.yaml"]
    if upstream is None:
        upstream = ["gate-events.jsonl", "P6.5-judge-verdict.md"]
    text = "---\nphase: P6.5\ntask_id: T0020\n---\n\n"
    text += "### 输入文件\n"
    for item in inputs:
        text += f"- {item}\n"
    text += "\n### 上游关联\n"
    for item in upstream:
        text += f"- {item}\n"
    text += extra_body
    (td / "P6.5-dispatch-context-judge.md").write_text(text, encoding="utf-8")


def _write_ledger(td, events):
    """构造 gate-events.jsonl（逐行哈希链，首行 prev_hash = GENESIS_HASH；BDD-7 同源约定）。
    events: list[dict]，每元素须含 ts/event；raw line = JSON 文本（不含行尾换行符）。"""
    prev_hash = hashlib.sha256(b"").hexdigest()
    lines = []
    for ev in events:
        line = json.dumps(ev, sort_keys=True)
        line = json.dumps({**ev, "prev_hash": prev_hash}, sort_keys=True)
        lines.append(line)
        prev_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
    (td / "gate-events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_judge_fixture(td, verdict_kwargs=None, evidence=None,
                         context_kwargs=None, ledger_events=None):
    """合规基线组装：evidence + verdict + dispatch-context + 可选账本（P1 用 task_dir 默认 1 BDD）。"""
    if evidence is None:
        evidence = {"e1.json": "evidence-a"}
    for rel, content in evidence.items():
        _write_evidence(td, rel, content)
    _write_verdict(td, **(verdict_kwargs or {}))
    _write_dispatch_context(td, **(context_kwargs or {}))
    if ledger_events is not None:
        _write_ledger(td, ledger_events)


@pytest.mark.windows_smoke
def test_bdd_1_verdict_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-1：verdict 缺失 → fail-closed exit 1（P6→P7 阻断前提）。"""
    td = task_dir()
    _write_dispatch_context(td)
    (td / "P6-evidence").mkdir()

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_1_verdict_empty_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-1：verdict 存在但为空 → exit 1（非空校验）。"""
    td = task_dir()
    _write_dispatch_context(td)
    (td / "P6-evidence").mkdir()
    (td / "P6.5-judge-verdict.md").write_text("", encoding="utf-8")

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_dispatch_context_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4：dispatch-context 缺失 → 无法验证信息隔离 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(td)

    (td / "P6.5-dispatch-context-judge.md").unlink()
    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_blacklist_path_in_inputs_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4①：『输入文件』节出现黑名单路径（P6-acceptance.md）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, context_kwargs={"inputs": ["P1-requirements.md", "P6-acceptance.md"]}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_blacklist_path_in_upstream_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4①：『上游关联』节出现黑名单路径（P5-dispatch-context-*.md）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        context_kwargs={"upstream": ["P5-dispatch-context-verifier.md", "gate-events.jsonl"]},
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_blacklist_case_insensitive_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4①（R3）：黑名单串大小写不敏感 + 归一化匹配（小写 p6-acceptance.MD 也命中）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, context_kwargs={"inputs": ["P1-requirements.md", "p6-acceptance.MD"]}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_whitelist_outside_path_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4②：两节出现白名单外任务产出路径（P3-test-cases.md，非黑名单）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, context_kwargs={"inputs": ["P1-requirements.md", "P3-test-cases.md"]}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_line_start_predict_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4③：全文（排除 AGATE_CARD/frontmatter）行首 `- PASS` 验收结论预判 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, context_kwargs={"extra_body": "\n补充说明\n- PASS BDD-1 pre-judged\n"}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_4_agate_card_excluded_not_flagged_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4③：AGATE_CARD 注入块内含 PASS/FAIL 行 → 双排除不误报（exit 0）。"""
    td = task_dir()
    card = (
        "<!-- AGATE_CARD_START -->\n"
        "## 当前阶段卡片：P3\n"
        "- PASS BDD-1 pre-judged (card text)\n"
        "- FAIL BDD-2 pre-judged (card text)\n"
        "<!-- AGATE_CARD_END -->\n"
    )
    _write_judge_fixture(td, context_kwargs={"extra_body": card})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_4_frontmatter_excluded_not_flagged_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-4③：frontmatter 块内含 `- PASS` 行 → frontmatter 排除不误报（exit 0）。"""
    td = task_dir()
    (td / "P6.5-dispatch-context-judge.md").write_text(
        "---\nphase: P6.5\n- PASS BDD-1 pre-judged (frontmatter)\n---\n\n"
        "### 输入文件\n- P1-requirements.md\n- P6-evidence/\n\n"
        "### 上游关联\n- gate-events.jsonl\n",
        encoding="utf-8",
    )
    _write_verdict(td)

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_3_criteria_total_mismatch_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-3：criteria_total != P1 `#### BDD-[0-9]` 标题数 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(td, verdict_kwargs={"criteria_total": 2, "criteria_passed": 2})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_3_skip_bdd_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-3：P1 有 2 条 BDD，verdict 只验 BDD-1 → 编号集不相等（零挑验违约）→ exit 1。"""
    td = task_dir()
    add_p1_bdd(td, "second scenario")
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "criteria_total": 2,
            "criteria_passed": 1,
            "conclusions": ["- PASS BDD-1: verified (e1.json)"],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_3_extra_bdd_not_in_p1_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-3：verdict 含 P1 不存在的 BDD 编号（BDD-9）→ 编号集不相等 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "criteria_total": 1,
            "criteria_passed": 1,
            "conclusions": ["- PASS BDD-9: verified (e1.json)"],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_3_all_bdd_covered_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-3 正向：P1 3 条 BDD 全部独立结论、计数一致、证据合规 → exit 0。"""
    td = task_dir()
    add_p1_bdd(td, "second")
    add_p1_bdd(td, "third")
    evidence = {"e1.json": "evidence-a", "e2.json": "evidence-b", "e3.json": "evidence-c"}
    _write_judge_fixture(
        td,
        evidence=evidence,
        verdict_kwargs={
            "criteria_total": 3,
            "criteria_passed": 3,
            "evidence": ["e1.json", "e2.json", "e3.json"],
            "conclusions": [
                "- PASS BDD-1: verified (e1.json)",
                "- PASS BDD-2: verified (e2.json)",
                "- PASS BDD-3: verified (e3.json)",
            ],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_5_status_invalid_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：status 非三值之一（passed/rejected/needs-revision）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(td, verdict_kwargs={"status": "in_progress"})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_5_criteria_total_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：criteria_total 字段缺失 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(td)
    (td / "P6.5-judge-verdict.md").write_text(
        "---\nstatus: passed\ncriteria_passed: 1\nverdict_evidence: [\"e1.json\"]\n---\n"
        "- PASS BDD-1: verified (e1.json)\n",
        encoding="utf-8",
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_5_criteria_total_non_integer_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：criteria_total 非整数 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, verdict_kwargs={"criteria_total": "abc", "criteria_passed": 1}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_5_verdict_evidence_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：verdict_evidence 字段缺失 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(td)
    (td / "P6.5-judge-verdict.md").write_text(
        "---\nstatus: passed\ncriteria_total: 1\ncriteria_passed: 1\n---\n"
        "- PASS BDD-1: verified (e1.json)\n",
        encoding="utf-8",
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_5_passed_three_counts_equal_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：status=passed 但 criteria_total(2) != P1 BDD 数(1) → 三数全等违反 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(td, verdict_kwargs={"criteria_total": 2, "criteria_passed": 2})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_5_passed_criteria_passed_less_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-5：status=passed 但 criteria_passed(0) < criteria_total(1) → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td, verdict_kwargs={"criteria_total": 1, "criteria_passed": 0}
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_6_evidence_file_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-6：verdict_evidence 引用文件不存在 → exit 1（缺失引用）。"""
    td = task_dir()
    (td / "P6-evidence").mkdir()
    _write_verdict(td, evidence=["ghost.json"])
    _write_dispatch_context(td)

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_6_evidence_empty_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-6：verdict_evidence 引用文件存在但为空 → exit 1（空文件充数）。"""
    td = task_dir()
    (td / "P6-evidence").mkdir()
    _write_evidence(td, "e1.json", "")
    _write_verdict(td, evidence=["e1.json"])
    _write_dispatch_context(td)

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_6_md5_duplicate_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-6：两个 verdict_evidence 引用文件内容相同（md5 相同）→ 重复充数 → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        evidence={"a.json": "same-content", "b.json": "same-content"},
        verdict_kwargs={
            "evidence": ["a.json", "b.json"],
            "conclusions": [
                "- PASS BDD-1: verified (a.json)",
            ],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_6_ref_not_in_evidence_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-6：正文结论引用不在 verdict_evidence 清单（引用 ⊄ verdict_evidence）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "evidence": ["e1.json"],
            "conclusions": ["- PASS BDD-1: verified (ghost2.json)"],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_6_evidence_not_referenced_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-6：verdict_evidence 存在未被任何结论引用的条目（引用不对称）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        evidence={"e1.json": "evidence-a", "e2.json": "evidence-b"},
        verdict_kwargs={
            "evidence": ["e1.json", "e2.json"],
            "conclusions": ["- PASS BDD-1: verified (e1.json)"],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_8_partial_passed_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-8：partial: true + status=passed（超限静默放行）→ exit 1。"""
    td = task_dir()
    _write_judge_fixture(td, verdict_kwargs={"partial": True})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_8_budget_exhausted_verdict_not_revision_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8：账本有 reason=budget_exhausted 的 judge_verdict 事件，但 verdict 非
    needs-revision+partial → exit 1。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "status": "needs-revision",
            "criteria_total": 1,
            "criteria_passed": 0,
        },
        ledger_events=[
            {
                "ts": "2026-08-22T10:00:01.000001Z",
                "event": "judge_verdict",
                "phase": "P6.5",
                "verdict": "needs-revision",
                "criteria_total": 1,
                "criteria_passed": 0,
                "partial": False,
                "reason": "budget_exhausted",
            }
        ],
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_8_budget_exhausted_revision_partial_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8 正向：账本 budget_exhausted + verdict needs-revision + partial: true → exit 0。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "status": "needs-revision",
            "criteria_total": 1,
            "criteria_passed": 0,
            "partial": True,
        },
        ledger_events=[
            {
                "ts": "2026-08-22T10:00:01.000001Z",
                "event": "judge_verdict",
                "phase": "P6.5",
                "verdict": "needs-revision",
                "criteria_total": 1,
                "criteria_passed": 0,
                "partial": True,
                "reason": "budget_exhausted",
            }
        ],
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_9_passed_but_evidence_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-9：status=passed（LLM 自述全过）但证据缺失 → 机械核对 exit 1，LLM 结论不单独放行。"""
    td = task_dir()
    (td / "P6-evidence").mkdir()
    _write_verdict(td, evidence=["ghost.json"])
    _write_dispatch_context(td)

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_8_rerun_same_verdict_round_not_increment(task_dir, agate_scripts, python_exe, run_cli):
    """CRITICAL-1 生命周期回归：同一合规 verdict 连续 2 次跑 check-judge-verdict
    （等价"手动 check-gate P6.5 + verdict commit"两处执行点）→ 账本 2 条 judge_verdict
    事件但 verdict_hash 相同 → 事件 hash == sha256(verdict 文件内容)，check-events 去重后
    轮次=1 → exit 0（正常 P6→P7 流程不再自锁；真实复核才 +1 轮）。"""
    td = task_dir()
    _write_judge_fixture(td)

    r1 = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert r1.returncode == 0
    r2 = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert r2.returncode == 0

    verdict_text = (td / "P6.5-judge-verdict.md").read_text(encoding="utf-8")
    expected_hash = hashlib.sha256(verdict_text.encode("utf-8")).hexdigest()
    ledger_events = []
    for line in (td / "gate-events.jsonl").read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev.get("event") == "judge_verdict":
            ledger_events.append(ev)
    assert len(ledger_events) == 2
    assert ledger_events[0]["verdict_hash"] == expected_hash == ledger_events[1]["verdict_hash"]

    # check-events 按 verdict_hash 去重 → 轮次=1，不触发 ≤2 预算自锁
    events_result = run_cli(python_exe, str(agate_scripts / "check-events.py"), str(td))
    assert events_result.returncode == 0


def test_bdd_4_whitelist_abs_path_not_flagged_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """I-1 回归：『输入文件』节以绝对路径引用白名单文件（仓库路径书写惯例）→
    basename 归一后不误报 → exit 0。"""
    td = task_dir()
    abs_p1 = str(td / "P1-requirements.md")
    _write_judge_fixture(td, context_kwargs={"inputs": [abs_p1, "P6-evidence/"]})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_6_desc_parens_not_misparsed_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """I-2 回归：结论描述含任意括号（如 "(as discussed earlier)"）但证据引用括号为
    明确文件路径形态 → 引用提取收敛到路径形态，不误取描述 token → exit 0。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        verdict_kwargs={
            "conclusions": ["- PASS BDD-1: verified (as discussed earlier) (e1.json)"],
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


# ============================================================
# TAG0035（gate 健壮性批，子批 D，DEBT0038）：BDD-11/12/13/14
# 覆盖 check-judge-verdict.py 信息隔离黑白名单路径 token 化豁免机制。
# 见 P2-design.md §3.4、P1-requirements.md 子批 D 原文。
# 命名沿用既有 test_tag0031_bdd_N 跨任务前缀先例（本文件大量复用裸 test_bdd_N 名，
# 撞名风险高，本批统一加 tag0035 前缀）。
# ============================================================


def _load_check_judge_verdict_direct(agate_scripts):
    """importlib 直接加载 check-judge-verdict.py 为独立模块对象（同源手法：
    test_check_gate.py 的 `_load_check_gate_direct` 既有先例），供 BDD-11 白盒直连
    `_check_blacklist` 使用。"""
    spec = importlib.util.spec_from_file_location(
        "check_judge_verdict_direct", str(agate_scripts / "check-judge-verdict.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    ("basename", "phase_card_path"),
    [
        ("p6-acceptance.md", "agate/phase-cards/P6-acceptance.md"),
        ("p4-implementation.md", "agate/phase-cards/P4-implementation.md"),
    ],
)
def test_tag0035_bdd_11_blacklist_exempts_phase_card_path_reference(
    basename, phase_card_path, agate_scripts
):
    """BDD-11：`_check_blacklist` 不应仅凭 basename 子串命中就判黑名单命中——协议
    阶段卡片路径引用（`phase-cards/` 前缀）须豁免，覆盖两个同类扫描确认的同构实例
    （P6-acceptance.md / P4-implementation.md）。

    白盒直连 `_check_blacklist`（而非跑全流程 CLI 断言整体 exit code）：整体 exit
    code 还受 `_check_whitelist_outside`（BDD-12/13 才会改动，BDD-11 未覆盖的独立
    检查点——该函数把任意非白名单 basename 的 .md 路径都判"白名单外"，含
    phase-cards/ 路径）影响，若断言整体 exit==0 会把两个独立检查点的行为混在一起，
    掩盖 `_check_blacklist` 自身豁免是否生效这一 BDD-11 的真实断言目标（dispatch-
    context 约束 4："测试断言的是修复后行为，不是实现细节"——此处"修复后行为"应
    锚定在 `_check_blacklist` 这一 BDD-11 明确点名的函数上）。
    """
    mod = _load_check_judge_verdict_direct(agate_scripts)
    section_lines = ["- P1-requirements.md", f"- {phase_card_path}"]

    hits = mod._check_blacklist(section_lines)
    assert basename not in hits, (
        f"{phase_card_path} 是协议规格文档路径引用，_check_blacklist 不应命中 "
        f"basename {basename!r}。实际 hits={hits!r}"
    )


@pytest.mark.parametrize(
    "role_path",
    [
        "agate/assets/execution-roles/analyst.md",
        "agate/assets/review-roles/plan-eng-review.md",
    ],
)
def test_tag0035_bdd_12_whitelist_role_definition_file_path(
    role_path, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-12：白名单应补齐角色定义文件路径（`execution-roles/` / `review-roles/`
    目录前缀），`_check_whitelist_outside` 不应把角色文件路径判为"白名单外任务产出
    路径引用"。黑盒全流程断言（无 BDD-11 那类跨检查点交互风险——role_path 不匹配
    任何黑名单模式）。"""
    td = task_dir()
    _write_judge_fixture(td, context_kwargs={"inputs": ["P1-requirements.md", role_path]})

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, (
        f"{role_path} 是角色定义文件路径，不应判为白名单外。实际 "
        f"exit={result.returncode}, output={result.output!r}"
    )


def test_tag0035_bdd_13_p6_evidence_bare_filename_recognized(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-13：`P6-evidence/` 目录下真实存在的文件，即便引用形式是裸文件名（不含
    `P6-evidence/` 前缀），也不应判为白名单外——判定应结合任务目录实际文件列表核对
    （而非扩大裸文件名正则匹配范围）。"""
    td = task_dir()
    _write_judge_fixture(
        td, context_kwargs={"inputs": ["P1-requirements.md", "extra-notes.md"]}
    )
    _write_evidence(td, "extra-notes.md", "供 BDD-13 用的证据说明\n")

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0, (
        "extra-notes.md 是 P6-evidence/ 目录下真实存在的文件，裸文件名引用不应判"
        f"白名单外。实际 exit={result.returncode}, output={result.output!r}"
    )


def test_tag0035_bdd_14_self_referential_p6_acceptance_still_blocked(
    task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-14（防御性红灯）：真实自述场景（裸引用任务自己的 P6-acceptance.md，无
    路径前缀）在 BDD-11/12/13 加固后仍应判黑名单命中并 exit 1，不得被三处路径豁免/
    补齐/裸文件名识别连带放宽（对应 known_risks"DEBT0038 白名单放宽可能削弱 judge
    信息隔离"的止损）。混入一个合规的角色路径引用（BDD-12 场景）确认二者互不干扰。"""
    td = task_dir()
    _write_judge_fixture(
        td,
        context_kwargs={
            "inputs": [
                "P1-requirements.md",
                "agate/assets/execution-roles/analyst.md",
                "P6-acceptance.md",
            ]
        },
    )

    result = _run_judge(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, (
        "裸文件名直接引用任务自己的 P6-acceptance.md 仍应判黑名单命中并 exit 1"
        f"（不得被 BDD-11/12/13 豁免连带放宽）。实际 exit={result.returncode}, "
        f"output={result.output!r}"
    )
