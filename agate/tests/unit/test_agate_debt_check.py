# tests/unit/test_agate_debt_check.py — 技术债登记闭环（check-debt.py / agate-debt-check.py）
# （agate-debt-check.bats 21 用例迁移，TAG0011 批次 5）
# 被测：check-debt.py FILE（schema 校验，fail-closed）+ check-debt.py --retreat-coverage（回退覆盖比对）
#   + agate-debt-check.py（多条目 schema 校验器，fenced 块解析）
# 流语义：schema 错误行 / GATE DEBT WARNING / 依赖缺失报错 均写 stderr → 断言用 .stderr
#   （P2 §3.2 先判流归属）；成功路径零输出 → 空/非空断言基于合并流 .output（BLOCKER-1，
#   debt-check 5 处 `[ -z "$output" ]`：bdd_5 / bdd_10 / bdd_11）
# 生产 shim 退役（P2 §3.1）：check-debt.py 内部用 sys.executable，无需 PATH shim

import re
import shutil

import pytest


def _run_check_debt(agate_scripts, python_exe, run_cli, *args, cwd=None):
    return run_cli(
        python_exe,
        str(agate_scripts / "check-debt.py"),
        *args,
        cwd=cwd,
    )


def _run_check_debt_retreat(agate_scripts, python_exe, run_cli, repo):
    """bats `cd $repo && check-debt.py --retreat-coverage` 等价（cwd 解析 repo_root）。"""
    return run_cli(
        python_exe,
        str(agate_scripts / "check-debt.py"),
        "--retreat-coverage",
        cwd=str(repo),
    )


# ---------- 功能组 A：debt/ 归类修正（BDD-1..4） ----------


@pytest.mark.windows_smoke
def test_bdd_1_workflow_directory_diagram_has_debt_dir(agate_root):
    workflow = (agate_root / "WORKFLOW.md").read_text(encoding="utf-8")
    assert "debt/" in workflow
    assert not re.search(r"agents/.*tech-debt", workflow)


def test_bdd_2_mkdir_nine_subdirs_synced_across_three_files(agate_root, tmp_path):
    ws_dirs = "roadmap,tasks,agents,archived,reviews,decisions,plans,logs,debt"
    for name in ("SETUP.md", "orchestrator-template.md", "state-machine.md"):
        text = (agate_root / name).read_text(encoding="utf-8")
        assert ws_dirs in text
    d = tmp_path / "ws"
    for sub in ("roadmap", "tasks", "agents", "archived", "reviews", "decisions", "plans", "logs", "debt"):
        (d / sub).mkdir(parents=True)
    assert len([p for p in d.iterdir() if p.is_dir()]) == 9


def test_bdd_3_setup_upgrading_debt_path_consistent(agate_root):
    upgrading = (agate_root / "UPGRADING.md").read_text(encoding="utf-8")
    setup = (agate_root / "SETUP.md").read_text(encoding="utf-8")
    assert "debt/tech-debt.md" in upgrading
    assert "debt" in setup
    assert not re.search(r"agents/tech-debt", upgrading)


def test_bdd_4_tag0003_scope_rechecked_to_nine(agate_root):
    base = agate_root.parent / "agate-workspace" / "tasks" / "TAG0003-workspace-architecture"
    p1 = base / "P1-requirements.md"
    p6 = base / "P6-acceptance.md"
    assert p1.is_file()
    assert p6.is_file()
    assert "9 子目录" in p1.read_text(encoding="utf-8")
    assert "9 子目录" in p6.read_text(encoding="utf-8")


# ---------- 功能组 B：DEBT 条目 schema 校验（BDD-5..10） ----------


def test_bdd_5_valid_entry_passes_schema(tmp_path, agate_scripts, python_exe, run_cli):
    md = tmp_path / "tech-debt.md"
    md.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: technical\n"
        "title: 模块耦合\n"
        "status: open\n"
        "priority: high\n"
        "evidence:\n"
        "  - path: docs/reviews/review-20260812-1204.md\n"
        "impact: 未来变更更贵\n"
        "recommendation: 拆分模块\n"
        "closure_criteria:\n"
        "  - 拆分完成\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT0002\n"
        "\n"
        "```yaml\n"
        "id: DEBT0002\n"
        "category: management\n"
        "title: 验收流程遗留\n"
        "status: closed\n"
        "priority: medium\n"
        "task_id: TAG0002\n"
        "evidence:\n"
        "  - path: docs/tasks/TAG0002/P6-acceptance.md\n"
        "impact: 影响后续验收\n"
        "recommendation: 补登记\n"
        "closure_criteria:\n"
        "  - 验收通过\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md))
    assert result.returncode == 0
    assert result.output == ""


def test_bdd_6_evidence_missing_intercepted(tmp_path, agate_scripts, python_exe, run_cli):
    md = tmp_path / "tech-debt.md"
    md.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: technical\n"
        "title: 无证据债\n"
        "status: open\n"
        "priority: high\n"
        "impact: 未来变更更贵\n"
        "recommendation: 补证据\n"
        "closure_criteria:\n"
        "  - 补证据\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md))
    assert result.returncode == 1
    assert "evidence" in result.stderr


def test_bdd_7_invalid_enum_values_intercepted(tmp_path, agate_scripts, python_exe, run_cli):
    md = tmp_path / "tech-debt.md"
    md.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: bug\n"
        "title: 非法枚举\n"
        "status: open\n"
        "priority: high\n"
        "evidence:\n"
        "  - path: docs/reviews/x.md\n"
        "impact: 未来变更更贵\n"
        "recommendation: 修正枚举\n"
        "closure_criteria:\n"
        "  - 枚举修正\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md))
    assert result.returncode == 1
    assert "category" in result.stderr


def test_bdd_8_closed_missing_task_id_or_p5p6_intercepted(tmp_path, agate_scripts, python_exe, run_cli):
    # 子场景 1：closed 缺 task_id
    md1 = tmp_path / "closed-no-task.md"
    md1.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: management\n"
        "title: 已关闭债\n"
        "status: closed\n"
        "priority: medium\n"
        "evidence:\n"
        "  - path: docs/tasks/TAG0002/P6-acceptance.md\n"
        "impact: 影响验收\n"
        "recommendation: 补 task_id\n"
        "closure_criteria:\n"
        "  - 补 task_id\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md1))
    assert result.returncode == 1
    assert "task_id" in result.stderr

    # 子场景 2：closed 有 task_id 但 evidence 未引用 P5/P6
    md2 = tmp_path / "closed-no-evidence-ref.md"
    md2.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: management\n"
        "title: 已关闭债\n"
        "status: closed\n"
        "priority: medium\n"
        "task_id: TAG0002\n"
        "evidence:\n"
        "  - path: docs/tasks/TAG0002/meeting.md\n"
        "impact: 影响验收\n"
        "recommendation: 补证据引用\n"
        "closure_criteria:\n"
        "  - 补证据引用\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md2))
    assert result.returncode == 1
    assert "P5" in result.stderr or "P6" in result.stderr or "evidence" in result.stderr


def test_bdd_9_three_state_and_open_with_task_id_legal(tmp_path, agate_scripts, python_exe, run_cli):
    md_open = tmp_path / "open-with-task.md"
    md_open.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: technical\n"
        "title: 已立项债\n"
        "status: open\n"
        "priority: high\n"
        "task_id: TAG0009\n"
        "evidence:\n"
        "  - path: docs/reviews/x.md\n"
        "impact: 未来变更更贵\n"
        "recommendation: 处理\n"
        "closure_criteria:\n"
        "  - 处理完成\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md_open))
    assert result.returncode == 0

    md_fourth = tmp_path / "fourth-state.md"
    md_fourth.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT0001\n"
        "\n"
        "```yaml\n"
        "id: DEBT0001\n"
        "category: technical\n"
        "title: 额外态\n"
        "status: accepted\n"
        "priority: high\n"
        "evidence:\n"
        "  - path: docs/reviews/x.md\n"
        "impact: 未来变更更贵\n"
        "recommendation: 修正\n"
        "closure_criteria:\n"
        "  - 修正\n"
        "source: review\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md_fourth))
    assert result.returncode == 1
    assert "status" in result.stderr


def test_bdd_10_no_file_or_no_yaml_block_is_noop(tmp_path, agate_scripts, python_exe, run_cli):
    # 无文件 → exit 0 无输出
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(tmp_path / "not-exist.md"))
    assert result.returncode == 0
    assert result.output == ""

    # 空文件 → exit 0 无输出
    empty = tmp_path / "empty.md"
    empty.write_text("", encoding="utf-8")
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(empty))
    assert result.returncode == 0
    assert result.output == ""

    # 旧格式纯正文（无 yaml 块）→ exit 0 无输出（向后兼容）
    prose = tmp_path / "prose-only.md"
    prose.write_text("# 技术债登记\n旧格式纯正文，无 yaml 块。\n", encoding="utf-8")
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(prose))
    assert result.returncode == 0
    assert result.output == ""


# ---------- 功能组 C：T001 回填验证模板（BDD-11） ----------


def test_bdd_11_t001_backfill_entries_pass_schema(tmp_path, agate_scripts, python_exe, run_cli):
    md = tmp_path / "tech-debt.md"
    md.write_text(
        "# 技术债登记（T001 回填）\n"
        "\n"
        "## DEBT-T1\n"
        "\n"
        "```yaml\n"
        "id: DEBT-T1\n"
        "category: technical\n"
        "title: T1 问题\n"
        "status: open\n"
        "priority: high\n"
        "evidence:\n"
        "  - path: docs/reviews/T001-retrospective-2026-08-10.md\n"
        "  - note: 根因：T1 根因\n"
        "impact: T1 影响\n"
        "recommendation: T1 建议\n"
        "closure_criteria:\n"
        "  - T1 判据\n"
        "source: retrospective\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT-T2\n"
        "\n"
        "```yaml\n"
        "id: DEBT-T2\n"
        "category: technical\n"
        "title: T2 问题\n"
        "status: open\n"
        "priority: high\n"
        "evidence:\n"
        "  - path: docs/reviews/T001-retrospective-2026-08-10.md\n"
        "  - note: 根因：T2 根因\n"
        "impact: T2 影响\n"
        "recommendation: T2 建议\n"
        "closure_criteria:\n"
        "  - T2 判据\n"
        "source: retrospective\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT-T3\n"
        "\n"
        "```yaml\n"
        "id: DEBT-T3\n"
        "category: technical\n"
        "title: T3 问题\n"
        "status: open\n"
        "priority: medium\n"
        "evidence:\n"
        "  - path: docs/reviews/T001-retrospective-2026-08-10.md\n"
        "  - note: 根因：T3 根因\n"
        "impact: T3 影响\n"
        "recommendation: T3 建议\n"
        "closure_criteria:\n"
        "  - T3 判据\n"
        "source: retrospective\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT-T4\n"
        "\n"
        "```yaml\n"
        "id: DEBT-T4\n"
        "category: technical\n"
        "title: T4 问题\n"
        "status: open\n"
        "priority: medium\n"
        "evidence:\n"
        "  - path: docs/reviews/T001-retrospective-2026-08-10.md\n"
        "  - note: 根因：T4 根因\n"
        "impact: T4 影响\n"
        "recommendation: T4 建议\n"
        "closure_criteria:\n"
        "  - T4 判据\n"
        "source: retrospective\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT-A5\n"
        "\n"
        "```yaml\n"
        "id: DEBT-A5\n"
        "category: protocol\n"
        "title: A5 协议原因\n"
        "status: open\n"
        "priority: low\n"
        "evidence:\n"
        "  - path: docs/reviews/T001-retrospective-2026-08-10.md\n"
        "  - note: 根因：A5 根因\n"
        "impact: A5 影响\n"
        "recommendation: A5 建议\n"
        "closure_criteria:\n"
        "  - A5 判据\n"
        "source: retrospective\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )
    result = _run_check_debt(agate_scripts, python_exe, run_cli, str(md))
    assert result.returncode == 0
    assert result.output == ""


# ---------- 功能组 D：回退事件强制登记（BDD-12..15） ----------


def test_bdd_12_retreat_requires_debt_entry_documented(agate_root):
    for rel in (
        "rules/state-transitions.md",
        "phase-cards/P6-acceptance.md",
        "phase-cards/P4-implementation.md",
        "scripts/agate-retreat-to.py",
    ):
        assert "DEBT" in (agate_root / rel).read_text(encoding="utf-8")


def test_bdd_13_retreat_commit_without_entry_warns(git_repo, agate_scripts, python_exe, run_cli):
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    git_repo.git("commit", "-qm", "retreat: P6 -> P4（诊断：测试回退）", "--allow-empty")

    result = _run_check_debt_retreat(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 0
    assert "GATE DEBT WARNING" in result.stderr


def test_bdd_14_retreat_entry_present_no_warning(git_repo, agate_scripts, python_exe, run_cli):
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    git_repo.git("commit", "-qm", "retreat: P5 -> P4（诊断：测试回退）", "--allow-empty")
    short = git_repo.git("rev-parse", "--short", "HEAD").stdout.strip()

    debt_dir = repo / "agate-workspace" / "debt"
    debt_dir.mkdir(parents=True)
    md = debt_dir / "tech-debt.md"
    md.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT-R1\n"
        "\n"
        "```yaml\n"
        "id: DEBT-R1\n"
        "category: management\n"
        "title: 回退债\n"
        "status: open\n"
        "priority: medium\n"
        "evidence:\n"
        f"  - path: {short}\n"
        "impact: 影响未来变更\n"
        "recommendation: 补登记\n"
        "closure_criteria:\n"
        "  - 补登记完成\n"
        "source: retreat\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )

    result = _run_check_debt_retreat(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 0
    assert "GATE DEBT WARNING" not in result.stderr


def test_bdd_15_real_retreat_records_fixture_reproducible(git_repo, agate_scripts, python_exe, run_cli):
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    git_repo.git(
        "commit", "-qm",
        "retreat: P5 -> P4（诊断：BDD-17: check-p6-format.sh --fix 破坏 frontmatter pass/fail 字段，需修复（用户已批准 2026-08-10））",
        "--allow-empty",
    )
    git_repo.git(
        "commit", "-qm",
        "retreat: P6 -> P5（诊断：BDD-17: check-p6-format.sh --fix 破坏 frontmatter pass/fail 字段，需修复（用户已批准 2026-08-10））",
        "--allow-empty",
    )

    # 方向 A：未建条目 → 报缺失 WARNING
    result = _run_check_debt_retreat(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 0
    assert "GATE DEBT WARNING" in result.stderr

    # 方向 B：已建条目且 evidence 引用两个提交 → 通过
    s1 = git_repo.git("rev-parse", "--short", "HEAD").stdout.strip()
    s2 = git_repo.git("rev-parse", "--short", "HEAD~1").stdout.strip()
    debt_dir = repo / "agate-workspace" / "debt"
    debt_dir.mkdir(parents=True)
    md = debt_dir / "tech-debt.md"
    md.write_text(
        "# 技术债登记\n"
        "\n"
        "## DEBT-R1\n"
        "\n"
        "```yaml\n"
        "id: DEBT-R1\n"
        "category: management\n"
        "title: 回退债一\n"
        "status: open\n"
        "priority: medium\n"
        "evidence:\n"
        f"  - path: {s1}\n"
        "impact: 影响未来变更\n"
        "recommendation: 补登记\n"
        "closure_criteria:\n"
        "  - 补登记完成\n"
        "source: retreat\n"
        "created_at: 2026-08-12\n"
        "```\n"
        "\n"
        "## DEBT-R2\n"
        "\n"
        "```yaml\n"
        "id: DEBT-R2\n"
        "category: management\n"
        "title: 回退债二\n"
        "status: open\n"
        "priority: medium\n"
        "evidence:\n"
        f"  - path: {s2}\n"
        "impact: 影响未来变更\n"
        "recommendation: 补登记\n"
        "closure_criteria:\n"
        "  - 补登记完成\n"
        "source: retreat\n"
        "created_at: 2026-08-12\n"
        "```\n",
        encoding="utf-8",
    )

    result = _run_check_debt_retreat(agate_scripts, python_exe, run_cli, repo)
    assert result.returncode == 0
    assert "GATE DEBT WARNING" not in result.stderr


def test_bdd_16_retreat_coverage_missing_agate_common_exit2(tmp_path, agate_scripts, python_exe, run_cli):
    sdir = tmp_path / "sdir"
    sdir.mkdir()
    shutil.copyfile(agate_scripts / "check-debt.py", sdir / "check-debt.py")

    result = run_cli(python_exe, str(sdir / "check-debt.py"), "--retreat-coverage")
    assert result.returncode == 2
    assert "缺少 agate_common" in result.stderr


# ---------- 功能组 E：P8 锚定留痕（BDD-16..18） ----------


def test_bdd_16_p8_card_requires_debt_confirm_and_field(agate_root):
    p8 = (agate_root / "phase-cards" / "P8-release.md").read_text(encoding="utf-8")
    assert "确认债务清单" in p8
    assert "debt_check" in p8


def test_bdd_17_p8_gate_checks_debt_check_existence_only(agate_root):
    gate = (agate_root / "scripts" / "check-gate.py").read_text(encoding="utf-8")
    assert "debt_check:" in gate


def test_bdd_18_empty_confirmation_observable(agate_root):
    p8 = (agate_root / "phase-cards" / "P8-release.md").read_text(encoding="utf-8")
    assert "debt_check: none" in p8


# ---------- 功能组 F：债 vs 缺陷判据（BDD-19..20） ----------


def test_bdd_19_criteria_documented_with_no_registration_outlet(agate_assets):
    tmpl = agate_assets / "templates" / "tech-debt-template.md"
    assert tmpl.is_file()
    text = tmpl.read_text(encoding="utf-8")
    assert "验收声明" in text
    assert "不登记" in text


def test_bdd_20_registration_does_not_exempt_current_task(agate_assets):
    tmpl = agate_assets / "templates" / "tech-debt-template.md"
    assert tmpl.is_file()
    assert "豁免" in tmpl.read_text(encoding="utf-8")
    review = (agate_assets / "review-roles" / "plan-eng-review.md").read_text(encoding="utf-8")
    assert "DEBT 条目格式" in review


# ---------- TAG0023 RM-AG0044（BDD-8）：复现定位计划 + 已知证据基线四要素 ----------
# 判据来源：P2-design.md 本身（dispatch-context 约束 4：BDD-8 是"文档四要素齐全"判据，
# 不是代码逻辑）。①已知证据基线 ②环境敏感测试判定标准 ④CI flaky 自动重跑机制触发条件
# 三项已由 P2-design.md §2.3 落盘（approved，本轮断言预期已通过）；③集中清单文件
# （agate/tests/ENV-SENSITIVE-TESTS.md）尚未创建（P4 待新建）——该文件缺失是本用例的
# 红灯来源（四要素任一缺失即 FAIL，见 P2-design.md §4 完成标准表 BDD-8 行）。


def test_bdd_8_recon_plan_and_known_baseline_four_elements(agate_root):
    p2_design = (
        agate_root.parent
        / "agate-workspace"
        / "tasks"
        / "TAG0023-mechanism-checks"
        / "P2-design.md"
    )
    assert p2_design.is_file()
    text = p2_design.read_text(encoding="utf-8")
    assert "PR #188" in text  # ①已知证据基线（CI 双 run 一过一挂实证）
    assert "环境敏感测试判定标准" in text  # ②判定标准
    assert "pytest-rerunfailures" in text  # ④CI flaky 自动重跑机制触发条件

    env_sensitive_doc = agate_root / "tests" / "ENV-SENSITIVE-TESTS.md"
    assert env_sensitive_doc.is_file(), (
        "③集中清单文件位置与格式：agate/tests/ENV-SENSITIVE-TESTS.md 尚未创建"
        "（P2-design.md §2.3，P4 待新建）"
    )


# ---------- TAG0023 RM-AG0044（BDD-9）：占位声明，本阶段不提供单元测试 ----------
# BDD-9（test_bdd_14 连续 5 次 CI 稳定）是环境级验收锚，需连续触发 5 次
# protocol-tests.yml 真实 CI run 才能判定，P3 单元测试无法本地模拟/断言这类跨多次
# CI 触发的稳定性结果。此 BDD 由 P6 阶段的 CI 触发验证覆盖，P3 不提供单元测试
# （见 P3-test-cases.md 与 dispatch-context 约束 5，避免为了凑数造一个假测试）。


# ---------- 元素类型校验（2026-09-21 补；对齐审查 E2 的连带建议）----------
#
# 背景：原校验只查 evidence / closure_criteria「是 list」，不查**元素类型**——实测一条
# DEBT 的 closure_criteria 里混进了 evidence 形态的 `{path, note}` 字典而 **rc=0 放行**
# （"决策已记录"的证据没进 evidence）。下面两例锁死两个方向。

_PREFIX = (
    "# 技术债登记\n\n## DEBT0001\n\n```yaml\n"
    "id: DEBT0001\ncategory: technical\ntitle: T\nstatus: open\npriority: high\n"
)


def _run_single_entry(agate_scripts, python_exe, run_cli, tmp_path, body):
    md = tmp_path / "tech-debt.md"
    md.write_text(_PREFIX + body + "```\n", encoding="utf-8")
    return _run_check_debt(agate_scripts, python_exe, run_cli, str(md))


def test_closure_criteria_element_type_enforced(agate_scripts, python_exe, run_cli, tmp_path):
    """closure_criteria 混入 dict（evidence 形态）→ 必须报错（原实现 rc=0 放行）。"""
    body = (
        "evidence:\n  - path: a.md\n    note: n\n"
        "impact: i\nrecommendation: r\n"
        "closure_criteria:\n  - path: b.md\n    note: 错挂证据\n"
        "source: review\ncreated_at: 2026-09-21\n"
    )
    result = _run_single_entry(agate_scripts, python_exe, run_cli, tmp_path, body)
    assert result.returncode != 0, f"closure_criteria 含 dict 应报错:\n{result.output}"
    assert "closure_criteria 元素类型错误" in result.output


def test_evidence_element_type_enforced(agate_scripts, python_exe, run_cli, tmp_path):
    """evidence 混入 str（closure_criteria 形态）→ 必须报错。"""
    body = (
        "evidence:\n  - 只是个字符串\n"
        "impact: i\nrecommendation: r\n"
        "closure_criteria:\n  - 完成\n"
        "source: review\ncreated_at: 2026-09-21\n"
    )
    result = _run_single_entry(agate_scripts, python_exe, run_cli, tmp_path, body)
    assert result.returncode != 0, f"evidence 含 str 应报错:\n{result.output}"
    assert "evidence 元素类型错误" in result.output
