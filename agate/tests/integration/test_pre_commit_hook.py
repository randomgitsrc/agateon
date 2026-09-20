# tests/integration/test_pre_commit_hook.py — pre-commit hook 集成测试
# （integration/pre-commit-hook.bats 迁移，TAG0011 批次 13a / 13b / 13c 子批）
# 13a 覆盖 IT_PT_BINARY.1-7 / IT_PT_MENTION.1 / IT_PT_T6.1-4（12 个）；
# 13b 追加 IT_PHASE_SPAN.1-5 / IT_P6_CODE.1-5 / IT_RETREAT.1-2 /
#      IT_CHANGELOG_P54/P54b / IT.9 / IT.9b（17 个）；
# 13c 追加 IT.1-8 / IT.10-11 / IT_GATE_REAL.1 / HOOK_EVIDENCE_WARNING /
#      AGATE_ROOT 自定位 / bdd-1/2/3/4/17/19（19 个，合计 48 覆盖 pre-commit-hook.bats 全量）；
# 被测：pre-commit-gate.sh 薄壳 + pre-commit-gate.py 真 hook 行为（BDD-11）——
# git commit 经 .git/hooks/pre-commit 软链触发（等价 bats setup `ln -sf`）。
# 合并流：run_cli .output = stdout + stderr（等价 bats $output，P2 §3.2 BLOCKER-1）。

import os
import shlex
import shutil
import struct
import sys
import zlib

import pytest


def _install_pre_commit_hook(repo, agate_scripts):
    """等价 bats setup()：`ln -sf pre-commit-gate.sh .git/hooks/pre-commit` + chmod +x。

    Linux 用 POSIX 软链（bats ln 语义）；Windows（Git Bash ln 退化为复制）复制薄壳，
    AGATE_ROOT 由 _git_commit env= 显式传入（P3 §5.2 平台分支纪律）。13a 用例不打
    windows_smoke 标（无平台关键词用例且非文件首 @test），软链语义由 Linux 全量覆盖。
    """
    hook = repo / ".git" / "hooks" / "pre-commit"
    src = str(agate_scripts / "pre-commit-gate.sh")
    if sys.platform == "win32":
        shutil.copy2(src, str(hook))
    else:
        os.symlink(src, str(hook))
    hook.chmod(0o755)


def _git_commit(run_cli, agate_root, repo, *args):
    """等价 bats `git -C "$REPO" commit <args>`；AGATE_ROOT 经 env= 显式传入
    （bats 由 load.bash export 继承给 git → hook，pytest 用 run_cli env= 承接）。"""
    return run_cli(
        "git",
        "-C",
        str(repo),
        "commit",
        *args,
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


def _init_commit(run_cli, agate_root, git_repo, repo):
    """等价 bats `echo init > README.md; git add README.md; git commit -qm "init"`。"""
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.stage("README.md")
    return _git_commit(run_cli, agate_root, repo, "-q", "-m", "init")


def _write_state_yaml(task_dir, task_id, phase):
    """等价 bats `cat > task_dir/.state.yaml` heredoc（retries 空表）。"""
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: {phase}\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )


def _write_min_valid_dispatch_context(
    run_cli, python_exe, agate_scripts, agate_root, task_dir, phase, role
):
    """等价 bats _write_min_valid_dispatch_context：写 dispatch-context + 注入 AGATE_CARD。

    卡片内容 = agate-next-card.py phase 输出（hook 用 sha256 校验嵌入块是当前版本），
    注入于 AGATE_CARD_START/END 之间（T6.1 验证卡片说明文本不触发 PROD_TOUCHED 误报）。
    """
    card = run_cli(
        python_exe,
        str(agate_scripts / "agate-next-card.py"),
        phase,
        cwd=str(task_dir),
        env={"AGATE_ROOT": str(agate_root)},
    )
    body = (
        "---\n"
        f"phase: {phase}\n"
        "generated_by: agate-next-card.sh + 主 Agent\n"
        "task_id: T001\n"
        f"role: {role}\n"
        "---\n"
        "\n"
        "<dispatch_guide>\n"
        "### 目标\n"
        "测试\n"
        "\n"
        "### 约束\n"
        "无\n"
        "\n"
        "### 上游关联\n"
        "无\n"
        "\n"
        "### 输入文件\n"
        "- agate-workspace/tasks/T001/P0-brief.md\n"
        "</dispatch_guide>\n"
        "\n"
        "<!-- AGATE_CARD_START -->\n"
        + card.stdout.rstrip("\n")
        + "\n"
        "<!-- AGATE_CARD_END -->\n"
        "\n"
        "<objective_info>\n"
        "- 环境状态：正常\n"
        "</objective_info>\n"
    )
    target = task_dir / f"{phase}-dispatch-context-{role}.md"
    target.write_text(body, encoding="utf-8")


def test_pt_binary_1_line_start_prod_touched_blocks(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "[PROD_TOUCHED] 接触了生产环境：修改了线上配置\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should fail")
    assert result.returncode != 0
    assert "PROD_TOUCHED" in result.output


def test_pt_binary_2_prod_not_touched_passes(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text("[PROD_NOT_TOUCHED]\n", encoding="utf-8")
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should pass")
    assert result.returncode == 0


def test_pt_binary_3_deleted_line_not_scanned(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "[PROD_TOUCHED] 旧内容\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "T001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    _git_commit(
        run_cli,
        agate_root,
        repo,
        "--no-verify",
        "-q",
        "-m",
        "setup with PROD_TOUCHED",
    )

    (task_dir / "P5-verification.md").write_text("clean content\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "remove PROD_TOUCHED")
    assert result.returncode == 0


def test_pt_binary_4_inline_mention_passes(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "无 [PROD_TOUCHED] 需要报告\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should pass")
    assert result.returncode == 0


def test_pt_binary_5_inline_mention_passes_variant(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "检查了 [PROD_TOUCHED] 标记\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should pass")
    assert result.returncode == 0


def test_pt_binary_6_no_marker_no_warning(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "normal content without any marker\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should pass")
    assert result.returncode == 0
    assert "WARNING" not in result.output


def test_pt_binary_7_prod_not_touched_with_desc_passes(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "[PROD_NOT_TOUCHED] 确认未接触\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should pass")
    assert result.returncode == 0


def test_pt_mention_1_body_mention_not_declaration(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "说明：本任务无生产接触，不需要写 [PROD_TOUCHED] 声明\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    result = _git_commit(run_cli, agate_root, repo, "-m", "mention not declaration")
    assert result.returncode == 0


def test_t6_1_p8_card_injection_no_false_flag(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P8", "releaser"
    )
    _write_state_yaml(task_dir, "T001", "P8")
    git_repo.stage("agate-workspace/tasks/T001/")

    result = _git_commit(run_cli, agate_root, repo, "-m", "p8 dispatch-context with AGATE_CARD")
    assert "不合规的 PROD_TOUCHED" not in result.output
    assert "检测到生产环境接触" not in result.output


def test_t6_2_note_inline_mention_passes(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "note.md").write_text(
        "记录：曾经不小心碰到了 [PROD_TOUCHED] 生产环境\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/")

    result = _git_commit(run_cli, agate_root, repo, "-m", "mention not declaration")
    assert result.returncode == 0


def test_t6_3_note_line_start_declaration_blocked(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "note.md").write_text(
        "[PROD_TOUCHED] 意外接触生产环境\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/")

    result = _git_commit(run_cli, agate_root, repo, "-m", "should be blocked")
    assert result.returncode != 0
    assert "检测到生产环境接触" in result.output


def test_t6_4_note_prod_not_touched_passes(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "note.md").write_text(
        "[PROD_NOT_TOUCHED] 未接触生产环境\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "T001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/")

    result = _git_commit(
        run_cli, agate_root, repo, "-m", "should not be blocked by PROD_TOUCHED check"
    )
    assert "不合规的 PROD_TOUCHED" not in result.output
    assert "检测到生产环境接触" not in result.output


# ============================================================
# TAG0011 批次 13b：IT_PHASE_SPAN / IT_P6_CODE / IT_RETREAT /
# IT_CHANGELOG / IT.9 系列（中段 @test，pre-commit-hook.bats 迁移）
# ============================================================


def _in_order(text, *parts):
    """bats `[[ "$output" == *"A"*"B"* ]]` 复合 glob 等价：parts 按顺序出现。"""
    pos = 0
    for part in parts:
        idx = text.find(part, pos)
        if idx == -1:
            return False
        pos = idx + len(part)
    return True


_P1_REQ = (
    "---\nagent: test\n---\n"
    "risk_level: medium\n"
    "phases: [P0, P1, P2, P3, P4, P5, P6, P7, P8]\n"
    "- Given test precondition\n"
)


def _write_p1_requirements(task_dir):
    (task_dir / "P1-requirements.md").write_text(_P1_REQ, encoding="utf-8")


def test_phase_span_1_late_p1_p2_outputs_no_warning(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "T001", "P3")
    (task_dir / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P3", "test-designer"
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    _write_p1_requirements(task_dir)
    (task_dir / "P2-design.md").write_text(
        "---\nagent: test\nphase: P2\ntask_id: T001\ntype: design\n"
        "parent: P1-requirements.md\ntrace_id: T001-P2-20260708\n"
        "status: approved\ncreated: 2026-07-08\n---\n"
        "### 候选方案 A：方案一\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-requirements.md")
    git_repo.stage("agate-workspace/tasks/T001/P2-design.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 late commit P1/P2 outputs")
    assert result.returncode == 0
    assert not _in_order(result.output, "WARNING", "P1")
    assert not _in_order(result.output, "WARNING", "P2")


def test_phase_span_2_existing_p1_restaged_warns(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "T001", "P1")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P1 setup")

    _write_state_yaml(task_dir, "T001", "P3")
    (task_dir / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    git_repo.stage("agate-workspace/tasks/T001/P3-test-cases.md")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    with open(task_dir / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write("updated requirements\n")
    git_repo.stage("agate-workspace/tasks/T001/P1-requirements.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 modify P1 while phase=P3")
    assert result.returncode == 0
    assert _in_order(result.output, "WARNING", "P1")


def test_phase_span_3_new_p4_output_early_warns(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "T001", "P3")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    (task_dir / "P4-implementation.md").write_text("implementation\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/P4-implementation.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 P4 output while phase=P3")
    assert result.returncode == 0
    assert _in_order(result.output, "WARNING", "P4")


def test_phase_span_4_multi_task_warn_selective(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    # T001: phase=P3, 历史产出晚提交（P1/P2/P3/P1-review 全新增）→ 不 WARNING
    t1 = repo / "agate-workspace" / "tasks" / "T001"
    t1.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(t1, "T001", "P3")
    _write_p1_requirements(t1)
    (t1 / "P2-design.md").write_text(
        "---\nagent: test\nphase: P2\ntask_id: T001\ntype: design\n"
        "parent: P1-requirements.md\ntrace_id: T001-P2-20260708\n"
        "status: approved\ncreated: 2026-07-08\n---\n"
        "### 候选方案 A：方案一\n",
        encoding="utf-8",
    )
    (t1 / "P3-test-cases.md").write_text(
        "---\nagent: test\n---\ntest cases\n", encoding="utf-8"
    )
    (t1 / "P1-review.md").write_text(
        "---\nphase: P1\ntask_id: T001\nstatus: approved\nagent: requirements-review\n---\n"
        "## BDD 评审\n- BDD-1: PASS + 覆盖维度：数据✓\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, t1, "P3", "test-designer"
    )
    git_repo.stage("agate-workspace/tasks/T001/P3-dispatch-context-test-designer.md")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    # T002: phase=P3, 已存在 P1 产出被修改 → WARNING
    t2 = repo / "agate-workspace" / "tasks" / "T002"
    t2.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(t2, "T002", "P1")
    _write_p1_requirements(t2)
    git_repo.stage("agate-workspace/tasks/T002/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T002 P1 setup")
    _write_state_yaml(t2, "T002", "P3")
    (t2 / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T002/.state.yaml")
    git_repo.stage("agate-workspace/tasks/T002/P3-test-cases.md")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T002 P3 setup")
    with open(t2 / "P1-requirements.md", "a", encoding="utf-8") as fh:
        fh.write("updated\n")

    # T003: phase=P3, 新增 P4 产出（提前产出）→ WARNING
    t3 = repo / "agate-workspace" / "tasks" / "T003"
    t3.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(t3, "T003", "P3")
    _write_p1_requirements(t3)
    (t3 / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T003/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T003 P3 setup")
    (t3 / "P4-implementation.md").write_text("implementation\n", encoding="utf-8")

    git_repo.stage("agate-workspace/tasks/T002/P1-requirements.md")
    git_repo.stage("agate-workspace/tasks/T003/P4-implementation.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "multi-task phase-span")
    assert result.returncode == 0
    assert not _in_order(result.output, "WARNING", "T001", "P1")
    assert _in_order(result.output, "WARNING", "P1")
    assert _in_order(result.output, "WARNING", "P4")


def test_phase_span_5_paused_phase_no_crash(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "PAUSED")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 PAUSED with P1 output")
    assert result.returncode == 0
    assert "integer expression expected" not in result.output


def test_p6_code_1_p6_evidence_dir_allowed(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    screenshots = task_dir / "P6-evidence" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    (screenshots / "a.png").touch()
    (task_dir / "P6-acceptance.md").write_text(
        "- PASS BDD-1: ok (screenshots/a.png)\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "T001", "P6")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P6", "verifier"
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "p6 evidence only")
    assert "暂存了项目源码" not in result.output
    assert "不应直接改代码" not in result.output


def test_p6_code_1b_evidences_dir_allowed(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    evidences = task_dir / "evidences"
    evidences.mkdir(parents=True, exist_ok=True)
    (evidences / "desktop.png").touch()
    (task_dir / "P6-acceptance.md").write_text(
        "- PASS BDD-1: ok (screenshots/a.png)\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "T001", "P6")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P6", "verifier"
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "evidences dir only")
    assert "暂存了项目源码" not in result.output
    assert "不应直接改代码" not in result.output


def test_p6_code_2_p6_source_blocked(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    screenshots = task_dir / "P6-evidence" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    (screenshots / "a.png").touch()
    (task_dir / "P6-acceptance.md").write_text(
        "- PASS BDD-1: ok (screenshots/a.png)\n", encoding="utf-8"
    )
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text("print('fix')\n", encoding="utf-8")
    _write_state_yaml(task_dir, "TXX0001", "P6")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P6", "verifier"
    )
    git_repo.stage("src/app.py")
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "should be blocked")
    assert result.returncode != 0
    assert "不应直接改代码" in result.output


def test_p6_code_3_p4_source_allowed(git_repo, agate_root, agate_scripts, run_cli):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text("print('impl')\n", encoding="utf-8")
    _write_state_yaml(task_dir, "T001", "P4")
    git_repo.stage("src/app.py")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "p4 impl")
    assert "不应直接改代码" not in result.output


def test_p6_code_4_p5_source_allowed(git_repo, agate_root, agate_scripts, run_cli):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text("print('fix')\n", encoding="utf-8")
    _write_state_yaml(task_dir, "T001", "P5")
    git_repo.stage("src/app.py")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "p5 fix")
    assert "不应直接改代码" not in result.output


def test_p6_code_5_p2_source_warns_not_blocked(
    git_repo, agate_root, agate_scripts, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text("print('early')\n", encoding="utf-8")
    _write_state_yaml(task_dir, "TXX0001", "P2")
    git_repo.stage("src/app.py")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "p2 early code")
    assert "是否在非实现阶段直接改代码" in result.output
    assert "不应直接改代码" not in result.output


def _retreat_setup(git_repo, agate_root, agate_scripts, python_exe, run_cli):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    screenshots = task_dir / "P6-evidence" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    (task_dir / "P6-acceptance.md").write_text(
        "- PASS BDD-1: ok (screenshots/x.png)\n", encoding="utf-8"
    )
    (screenshots / "x.png").touch()
    _write_state_yaml(task_dir, "TXX0001", "P6")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P6", "verifier"
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "-q", "-m", "setup P6 state")
    return repo, task_dir


def test_retreat_1_real_hook_each_step(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo, _task_dir = _retreat_setup(
        git_repo, agate_root, agate_scripts, python_exe, run_cli
    )
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-retreat-to.py"),
        "agate-workspace/tasks/T001",
        "P4",
        "集成测试诊断",
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert result.returncode == 0
    assert "共 2 步" in result.output
    log = git_repo.git("log", "--oneline").stdout
    assert "retreat: P6 -> P5" in log
    assert "retreat: P5 -> P4" in log


def test_retreat_2_midway_hook_rejected(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo, task_dir = _retreat_setup(
        git_repo, agate_root, agate_scripts, python_exe, run_cli
    )
    (task_dir / "note.md").write_text(
        "[PROD_TOUCHED] 意外接触了生产环境\n", encoding="utf-8"
    )
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-retreat-to.py"),
        "agate-workspace/tasks/T001",
        "P4",
        "集成测试：中途拒绝",
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert result.returncode == 1
    assert "未通过 pre-commit hook 校验" in result.output
    assert "已停在 P6" in result.output
    log = git_repo.git("log", "--oneline").stdout
    assert "retreat:" not in log


def test_changelog_1_p4_no_changelog_warning(git_repo, agate_root, agate_scripts, run_cli, bash):
    repo = git_repo.path
    git_repo.git("commit", "-q", "--allow-empty", "-m", "init")
    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "T001", "P4")
    (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Fixed\n- T999: other task\n",
        encoding="utf-8",
    )
    (task_dir / "P0-brief.md").write_text("task: test\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    git_repo.stage("agate-workspace/tasks/T001/P0-brief.md")
    result = run_cli(
        bash,
        str(agate_scripts / "pre-commit-gate.sh"),
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert "CHANGELOG" not in result.output


def test_changelog_2_p8_changelog_warning(git_repo, agate_root, agate_scripts, run_cli, bash):
    repo = git_repo.path
    git_repo.git("commit", "-q", "--allow-empty", "-m", "init")
    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P8")
    (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Fixed\n- T999: other task\n",
        encoding="utf-8",
    )
    (task_dir / "P0-brief.md").write_text("task: test\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    git_repo.stage("agate-workspace/tasks/T001/P0-brief.md")
    result = run_cli(
        bash,
        str(agate_scripts / "pre-commit-gate.sh"),
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert "CHANGELOG" in result.output


def test_it9_pruning_skip_low_passes(git_repo, agate_root, agate_scripts, python_exe, run_cli):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P2")
    (task_dir / "P1-requirements.md").write_text(
        "---\nagent: test\n---\nrisk_level: low\n"
        "phases: [P0, P1, P2, P4, P5, P6, P7, P8]\n跳过风险: 低\n",
        encoding="utf-8",
    )
    (task_dir / "P2-design.md").write_text(
        "---\nagent: test\nphase: P2\ntask_id: TXX0001\ntype: design\n"
        "parent: P1-requirements.md\ntrace_id: T001-P2-20260708\n"
        "status: approved\ncreated: 2026-07-08\n---\n"
        "### 候选方案 A：方案一\n### 候选方案 B：方案二\n## 权衡\nA 简单 B 稳健\n"
        "candidate_count: 2\npackages: [pkg-a]\ndomains: [backend]\n"
        "ui_affected: false\ngate_commands: {}\n",
        encoding="utf-8",
    )
    (task_dir / "P2-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nP2 review approved.\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P2", "architect"
    )
    git_repo.stage("agate-workspace/tasks/T001/P2-dispatch-context-architect.md")
    _git_commit(run_cli, agate_root, repo, "-q", "-m", "T001 P2")

    _write_state_yaml(task_dir, "TXX0001", "P5")
    (task_dir / "P5-verification.md").write_text(
        "---\nagent: test\n---\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 skip to P5")
    assert result.returncode == 0


def test_it9b_pruning_skip_medium_blocked(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P2")
    (task_dir / "P1-requirements.md").write_text(
        "---\nagent: test\n---\nrisk_level: medium\n"
        "phases: [P0, P1, P2, P4, P5, P6, P7, P8]\n跳过风险: 低\n",
        encoding="utf-8",
    )
    (task_dir / "P2-design.md").write_text(
        "---\nagent: test\nphase: P2\ntask_id: TXX0001\ntype: design\n"
        "parent: P1-requirements.md\ntrace_id: T001-P2-20260708\n"
        "status: approved\ncreated: 2026-07-08\n---\n"
        "### 候选方案 A：方案一\n### 候选方案 B：方案二\n## 权衡\nA 简单 B 稳健\n"
        "candidate_count: 2\npackages: [pkg-a]\ndomains: [backend]\n"
        "ui_affected: false\ngate_commands: {}\n",
        encoding="utf-8",
    )
    (task_dir / "P2-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nP2 review approved.\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P2", "architect"
    )
    git_repo.stage("agate-workspace/tasks/T001/P2-dispatch-context-architect.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 P2 medium skip P3")
    assert result.returncode != 0
    assert _in_order(result.output, "P3 不可裁剪", "仅 low")


# ============================================================
# TAG0011 批次 13c：IT.1-8 / IT.10-11 / IT_GATE_REAL.1 /
# HOOK_EVIDENCE_WARNING / AGATE_ROOT 自定位 / bdd-1/2/3/4/17/19
# （pre-commit-hook.bats 迁移收尾，48 @test 全覆盖）
# ============================================================


def _write_root_state_yaml(repo, task_id, phase):
    """等价 bats 根级 `.state.yaml`（repo_root，task_id 指向任务）。"""
    (repo / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: {phase}\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )


def _write_p1_review(task_dir, bdd_note="- BDD-1: PASS + 覆盖维度：数据✓"):
    (task_dir / "P1-review.md").write_text(
        "---\nphase: P1\ntask_id: TXX0001\nstatus: approved\nagent: requirements-review\n---\n"
        "## BDD 评审\n"
        + bdd_note
        + "\n",
        encoding="utf-8",
    )


def _write_low_variance_png(path):
    """等价 bats `$PYTHON -c` struct/zlib 生成的 100x100 全白 PNG（方差 0）。"""
    w, h = 100, 100
    raw = b"\x00" + b"\xff\xff\xff" * w
    raw = raw * h
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw)

    def chunk(typ, data):
        return (
            struct.pack(">I", len(data))
            + typ
            + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


@pytest.mark.windows_smoke
def test_it1_no_state_yaml_change_no_trigger(git_repo, agate_root, agate_scripts, run_cli):
    """IT.1：无 .state.yaml 变更（仅 README 首次 commit）→ hook 不触发。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.stage("README.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "init")
    assert result.returncode == 0


def test_it2_root_state_phase_change_gate_passes(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """IT.2：根 .state.yaml phase 变更 → 合法 P1 全流程 commit 通过。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    _write_root_state_yaml(repo, "TXX0001", "P1")
    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir)
    git_repo.stage(".state.yaml")
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-dispatch-context-analyst.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "phase change to P1")
    assert result.returncode == 0


def test_it3_inline_prod_touched_mention_not_blocked(
    git_repo, agate_root, agate_scripts, run_cli
):
    """IT.3：P5 产出句中提及 [PROD_TOUCHED]（非行首声明）→ 不中止（T090）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "P5-verification.md").write_text(
        "do something to production [PROD_TOUCHED]\n", encoding="utf-8"
    )
    _write_state_yaml(task_dir, "TXX0001", "P5")
    git_repo.stage("agate-workspace/tasks/T001/P5-verification.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "mention not declaration")
    assert result.returncode == 0


def test_it4_bad_state_yaml_format_blocked(git_repo, agate_root, agate_scripts, run_cli):
    """IT.4：根 .state.yaml task_id 格式错误 → state-yaml 校验拦截。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    (repo / ".state.yaml").write_text("task_id: T001a\nphase: P1\n", encoding="utf-8")
    git_repo.stage(".state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "bad state yaml")
    assert result.returncode != 0
    assert "task_id 格式错误" in result.output


def test_it5_state_yaml_format_check_passes(git_repo, agate_root, agate_scripts, run_cli):
    """IT.5：任意 .state.yaml 变更都触发格式校验；格式正确 → commit 通过。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    _write_root_state_yaml(repo, "TXX0001", "P1")
    git_repo.stage(".state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "state format check")
    assert result.returncode == 0


def test_it6_task_level_state_p1_output_commits(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """IT.6：多任务——任务级 .state.yaml + P1 产出 → 正常 commit。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P1")
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-dispatch-context-analyst.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 P1")
    assert result.returncode == 0


def test_it7_p4_output_phase_p3_warning_not_blocked(
    git_repo, agate_root, agate_scripts, run_cli
):
    """IT.7：P4 产出但 phase 仍 P3 → WARNING 不拦截（产出了但忘改 phase）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "T001", "P3")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3")

    (task_dir / "P4-implementation.md").write_text("implementation\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/P4-implementation.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 P4 output only")
    assert result.returncode == 0
    assert ("WARNING" in result.output) or ("phase" in result.output)


def test_it8_phase_p2_missing_design_blocked(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """IT.8：phase 变更到 P2 但无 P2-design.md → 拦截。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P1")
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-dispatch-context-analyst.md")
    _git_commit(run_cli, agate_root, repo, "-q", "-m", "T001 P1")

    _write_state_yaml(task_dir, "TXX0001", "P2")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 phase P2")
    assert result.returncode != 0
    assert ("P2-design.md 不存在" in result.output) or ("P2 不可裁剪" in result.output)


def test_it10_root_state_backward_compat(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """IT.10：向后兼容——根 .state.yaml 仍工作。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    _write_root_state_yaml(repo, "TXX0001", "P1")
    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir)
    git_repo.stage(".state.yaml")
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-dispatch-context-analyst.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "root state P1")
    assert result.returncode == 0


def test_it11_p2_code_file_warning(git_repo, agate_root, agate_scripts, run_cli, bash):
    """IT.11：P2 阶段暂存代码文件 → WARNING（非实现阶段直接改代码）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P2")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P2 setup")

    (repo / "hack.py").write_text("print('hello')\n", encoding="utf-8")
    (task_dir / ".state.yaml").write_text(
        "task_id: TXX0001\nphase: P2\nstatus: active\n"
        "retries:\n  P2:\n    - round: 1\n      failure_mode: test\n",
        encoding="utf-8",
    )
    git_repo.stage("hack.py")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = run_cli(
        bash,
        str(agate_scripts / "pre-commit-gate.sh"),
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert "代码文件" in result.output


def test_gate_real_1_writes_gate_result_json(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """IT_GATE_REAL.1：hook 跑真 check-gate 并写入真实 .gate-result.json。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P2")
    (task_dir / "P2-design.md").write_text(
        "# P2 design\n### 候选方案 A：方案一\n### 候选方案 B：方案二\n## 权衡\n"
        "A 更简单，B 更稳健。\ncandidate_count: 2\npackages: [pkg-a]\n"
        "domains: [backend]\nui_affected: false\ngate_commands: {}\n",
        encoding="utf-8",
    )
    (task_dir / "P2-review.md").write_text(
        "---\nagent: test\nstatus: approved\n---\n通过。\n", encoding="utf-8"
    )
    card = run_cli(
        python_exe,
        str(agate_scripts / "agate-next-card.py"),
        "P2",
        cwd=str(task_dir),
        env={"AGATE_ROOT": str(agate_root)},
    )
    (task_dir / "P2-dispatch-context-architect.md").write_text(
        "---\nagent: test\n---\n## 任务\n设计 P2\n\n<!-- AGATE_CARD_START -->\n"
        + card.stdout.rstrip("\n")
        + "\n<!-- AGATE_CARD_END -->\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "P2")
    assert result.returncode == 0
    assert (repo / ".gate-result.json").is_file()
    assert "pre-commit-hook" in (repo / ".gate-result.json").read_text(encoding="utf-8")


def test_hook_evidence_warning_low_variance_not_blocked(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """HOOK_EVIDENCE_WARNING：P6 低方差截图 → WARNING 不拦截 commit（T086）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)

    task_dir = repo / "agate-workspace" / "tasks" / "T086"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0086", "P6")
    (task_dir / "P6-acceptance.md").write_text(
        "---\nagent: test\n---\n- PASS BDD-1 (screenshots/test.png)\n",
        encoding="utf-8",
    )
    (task_dir / "P2-design.md").write_text(
        "---\nagent: test\n---\nui_affected: true\n", encoding="utf-8"
    )
    screenshots = task_dir / "P6-evidence" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    _write_low_variance_png(screenshots / "test.png")
    (task_dir / "P6-dispatch-context-verifier.md").write_text(
        "---\nphase: P6\ngenerated_by: agate-next-card.sh + 主 Agent\n"
        "task_id: TXX0086\nrole: verifier\n---\n\n"
        "<!-- AGATE_CARD_START -->\n<!-- AGATE_CARD_END -->\n",
        encoding="utf-8",
    )
    run_cli(
        python_exe,
        str(agate_scripts / "agate-inject-card.py"),
        "P6",
        str(task_dir),
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )
    git_repo.stage("agate-workspace/tasks/T086/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T086 evidence warning test")
    assert result.returncode == 0
    assert "WARNING" in result.output


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows 无 POSIX 软链，软链 hook 自定位场景无法验证",
)
def test_agate_root_self_locate_worktree(git_repo, agate_root, tmp_path, run_cli, bash):
    """AGATE_ROOT 未设时自定位到脚本自身本体（worktree 软链，T086）。"""
    repo = git_repo.path
    workflow_root = tmp_path / "workflow-root"
    (workflow_root / "scripts").mkdir(parents=True)
    shutil.copy2(
        str(agate_root / "scripts" / "pre-commit-gate.sh"),
        str(workflow_root / "scripts" / "pre-commit-gate.sh"),
    )
    # TAG0008：hook 薄壳经 resolve-entry 解析版本后 exec 对应 gate——fake 安装根补齐
    # 解析入口（resolve-entry.py + 其依赖 agate_common.py），否则薄壳 fail-closed 阻断。
    # TAG0037（P2 §6 T-10 / eng N-1）：agate_common 现依赖 agate_package.py——拷贝清单须同时含它（存在才拷）。
    for entry_name in ("resolve-entry.py", "agate_common.py", "agate_package.py"):
        if (agate_root / "scripts" / entry_name).is_file():
            shutil.copy2(
                str(agate_root / "scripts" / entry_name),
                str(workflow_root / "scripts" / entry_name),
            )
    (workflow_root / "scripts" / "pre-commit-gate.sh").chmod(0o755)
    (workflow_root / "scripts" / "pre-commit-gate.py").write_text(
        "#!/usr/bin/env python3\nprint(\"WORKTREE_SOURCED\")\n", encoding="utf-8"
    )
    os.symlink(
        str(workflow_root / "scripts" / "pre-commit-gate.sh"),
        str(repo / ".git" / "hooks" / "pre-commit"),
    )
    hook = repo / ".git" / "hooks" / "pre-commit"
    result = run_cli(
        bash,
        "-c",
        f"unset AGATE_ROOT; cd {shlex.quote(str(repo))} && bash {shlex.quote(str(hook))}",
        cwd=str(repo),
        # HOME 隔离：resolve_hook_root 会查 ~/.agate 的版本解析链（current/latest 指针），
        # 不隔离则解析到本机稳定版而非本测试的 workflow_root（TAG0032 版本管理布局引入）
        env={"HOME": str(tmp_path)},
    )
    assert "WORKTREE_SOURCED" in result.output


def test_bdd_1_space_path_gate_fail(git_repo, agate_root, agate_scripts, run_cli):
    """bdd-1：空格路径任务 gate 实际不通过时拦截（S1 fail-open 修复）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "Task Space"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P1")
    git_repo.stage("agate-workspace/tasks/Task Space/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "space path gate fail")
    assert result.returncode == 1


def test_bdd_2_space_path_multiple_state_yaml(
    git_repo, agate_root, agate_scripts, run_cli
):
    """bdd-2：多个 .state.yaml 含空格路径逐个处理（不因切词丢失文件）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    t1 = repo / "agate-workspace" / "tasks" / "T001"
    t1.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(t1, "TXX0001", "P0")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")

    ts = repo / "agate-workspace" / "tasks" / "Task Space"
    ts.mkdir(parents=True, exist_ok=True)
    (ts / ".state.yaml").write_text(
        "task_id: T001a\nphase: P0\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/Task Space/.state.yaml")
    result = _git_commit(run_cli, agate_root, repo, "-m", "space state invalid")
    assert result.returncode == 1


def test_bdd_3_space_dir_gate_runs(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """bdd-3：空格目录 PROCESSED_DIRS 不拆段，gate 正常执行（输出含 GATE P1）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "Task Space"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P1")
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir, bdd_note="- BDD-1: PASS")
    git_repo.stage("agate-workspace/tasks/Task Space/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/Task Space/P1-dispatch-context-analyst.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "space valid P1")
    assert result.returncode == 0
    assert "GATE P1" in result.output


def test_bdd_4_no_space_single_task_regression(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """bdd-4：无空格路径单任务 gate 行为不变（Linux 回归）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P1")
    _write_p1_requirements(task_dir)
    _write_p1_review(task_dir, bdd_note="- BDD-1: PASS")
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P1", "analyst"
    )
    git_repo.stage("agate-workspace/tasks/T001/P1-dispatch-context-analyst.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "normal P1")
    assert result.returncode == 0
    assert "GATE P1" in result.output


def test_bdd_17_metachar_dir_prod_touched(git_repo, agate_root, agate_scripts, run_cli):
    """bdd-17：任务目录含 [ 元字符时 PROD_TOUCHED 检测不静默绕过（M9）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T[1]"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P5")
    (task_dir / "P5-verification.md").write_text(
        "[PROD_TOUCHED] 生产环境被接触\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/T[1]/")
    result = _git_commit(run_cli, agate_root, repo, "-m", "metachar prod touched")
    assert result.returncode == 1


@pytest.mark.windows_smoke
def test_bdd_19_copy_mode_agate_root(
    git_repo, agate_root, agate_scripts, run_cli, bash
):
    """bdd-19：复制模式 hook 经 .agate-root 标记正确解析 AGATE_ROOT。"""
    repo = git_repo.path
    hook = repo / ".git" / "hooks" / "pre-commit"
    shutil.copy2(str(agate_scripts / "pre-commit-gate.sh"), str(hook))
    hook.chmod(0o755)
    (repo / ".git" / "hooks" / ".agate-root").write_text(
        str(agate_root) + "\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.stage("README.md")
    _git_commit(run_cli, agate_root, repo, "-q", "-m", "init")

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P0")
    git_repo.stage("agate-workspace/tasks/T001/")
    result = run_cli(
        bash,
        "-c",
        f"cd {shlex.quote(str(repo))} && env -u AGATE_ROOT git commit -m 'copy mode hook'",
        cwd=str(repo),
    )
    assert result.returncode == 0


# ── DEBT0014 / BDD-10 / BDD-11：3 个 hook 薄壳 python 探测循环增强 ──
# （TAG0017 fg4-windows-python-probe 批次；诚实边界：本环境 Linux 无法真实触发 Windows
#   Store python3.exe 占位符 exit 49，以下用模拟 stub 复现"候选可被 command -v 找到但
#   不可正常执行"这一症状特征，不代表已在真实 Windows 环境验证——见 P0-brief 约束 3 /
#   P1 verification_env / P2-design.md §8 minimal_validation。）

_PROBE_HOOKS = [
    pytest.param("pre-commit-gate.sh", "pre-commit-gate.py", id="pre-commit"),
    pytest.param("commit-msg-self-gate.sh", "commit-msg-self-gate.py", id="commit-msg"),
    pytest.param("pre-push-gate.sh", "pre-push-gate.py", id="pre-push"),
]

_PROBE_MARKER = "AGATE_PROBE_TEST_OK"


def _build_probe_workflow_root(tmp_path, agate_root, hook_filename, gate_py_filename):
    """构造一个独立 workflow_root，复制 hook 薄壳 + resolve-entry.py + agate_common.py，
    并把对应的真 gate py（pre-commit-gate.py 等）替换为只打印 marker 的假实现——
    等价 test_agate_root_self_locate_worktree（T086）的自定位验证模式，用于隔离验证
    探测循环本身是否解析到"可正常 exec 的解释器"，不牵涉真实 gate 业务逻辑。
    薄壳文件直接落在 workflow_root/scripts/ 下（非软链），readlink -f 解析到自身，
    ENTRY_ROOT 自定位 = workflow_root，AGATE_ROOT 传空字符串触发该自定位分支。
    """
    workflow_root = tmp_path / "workflow-root"
    (workflow_root / "scripts").mkdir(parents=True)
    # TAG0037（P2 §6 T-10 / eng N-1）：agate_common 现依赖 agate_package.py——拷贝清单须同时含它（存在才拷）。
    for name in (hook_filename, "resolve-entry.py", "agate_common.py", "agate_package.py"):
        if (agate_root / "scripts" / name).is_file():
            shutil.copy2(
                str(agate_root / "scripts" / name), str(workflow_root / "scripts" / name)
            )
    hook_path = workflow_root / "scripts" / hook_filename
    hook_path.chmod(0o755)
    (workflow_root / "scripts" / gate_py_filename).write_text(
        f'#!/usr/bin/env python3\nprint("{_PROBE_MARKER}")\n', encoding="utf-8"
    )
    return hook_path


def _make_broken_python3_stub(bin_dir):
    """模拟 Windows Store python3.exe 占位符的症状特征：`command -v` 能找到（有执行位），
    但执行任何操作一律非零退出、忽略传入参数——不解释所给的 .py 脚本内容。"""
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "python3"
    stub.write_text("#!/bin/sh\nexit 49\n", encoding="utf-8")
    stub.chmod(0o755)
    return stub


def _make_working_python_stub(bin_dir, real_python_exe):
    """构造一个真正可用的 `python` 候选（软链到本机真实 python3 解释器）。"""
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "python"
    os.symlink(real_python_exe, str(stub))
    return stub


@pytest.mark.parametrize("hook_filename,gate_py_filename", _PROBE_HOOKS)
def test_bdd_10_probe_skips_unexecutable_candidate(
    tmp_path, agate_root, python_exe, bash, run_cli, hook_filename, gate_py_filename
):
    """bdd-10：探测循环命中不可执行候选（PATH 上找得到但 exec 一律失败）时跳过，
    继续探测下一候选，最终解析到可正常执行的解释器（3 个 hook 薄壳均需验证）。
    模拟 stub 复现，非真实 Windows 环境验证。"""
    hook_path = _build_probe_workflow_root(
        tmp_path, agate_root, hook_filename, gate_py_filename
    )
    bin1 = tmp_path / "fake-bin1"
    bin2 = tmp_path / "fake-bin2"
    _make_broken_python3_stub(bin1)
    _make_working_python_stub(bin2, python_exe)
    fake_path = f"{bin1}:{bin2}:{os.environ.get('PATH', '')}"

    result = run_cli(
        bash,
        str(hook_path),
        # HOME 隔离：同 test_agate_root_self_locate_worktree——防 resolve_hook_root
        # 解析到本机 ~/.agate 的版本目录而非本测试的 workflow_root
        env={"AGATE_ROOT": "", "PATH": fake_path, "HOME": str(tmp_path)},
    )
    assert result.returncode == 0, (
        f"探测循环未跳过不可执行的 Python 解释器候选（{hook_filename}）："
        f"returncode={result.returncode} output={result.output!r}"
    )
    assert _PROBE_MARKER in result.output


@pytest.mark.parametrize("hook_filename,gate_py_filename", _PROBE_HOOKS)
def test_bdd_11_agate_python_explicit_override_skips_probe_loop(
    tmp_path, agate_root, python_exe, bash, run_cli, hook_filename, gate_py_filename
):
    """bdd-11：显式指定 AGATE_PYTHON 时薄壳直接使用该路径，不执行 command -v 探测循环——
    即便 PATH 上唯一能找到的 python3 候选是不可执行的（3 个 hook 薄壳均需验证）。"""
    hook_path = _build_probe_workflow_root(
        tmp_path, agate_root, hook_filename, gate_py_filename
    )
    bin1 = tmp_path / "fake-bin1"
    _make_broken_python3_stub(bin1)
    fake_path = f"{bin1}:{os.environ.get('PATH', '')}"

    result = run_cli(
        bash,
        str(hook_path),
        env={
            "AGATE_ROOT": "",
            "PATH": fake_path,
            "AGATE_PYTHON": python_exe,
            "HOME": str(tmp_path),  # HOME 隔离（同上）
        },
    )
    assert result.returncode == 0, (
        f"AGATE_PYTHON 显式指定未被薄壳采用，仍走了探测循环并命中不可执行候选"
        f"（{hook_filename}）：returncode={result.returncode} output={result.output!r}"
    )
    assert _PROBE_MARKER in result.output


# ============================================================
# TAG0019 2j.1 挂载链（P4-review C3 / P2 §0.3 R3 缓解）：
# ceremony 路由校验在 pre-commit 链上（check-routing 与 2j check-pruning 并列）
# ============================================================


def test_it10_routing_2j1_thin_missing_element_blocks(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """TAG0019 C3（P2 §0.3 R3）：ceremony: thin 缺四要素（coupling_checklist）→
    check-routing exit 1 → commit 被 2j.1 拦截（输出含 GATE ROUTING）。
    若 2j.1 未挂载，本 commit 应成功 → 该用例失败，证明挂载链缺失。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P2")
    (task_dir / "P1-requirements.md").write_text(
        "---\nagent: test\nceremony: thin\nrisk_level: low\n"
        "phases: [P0, P1, P2, P3, P4, P5, P6, P7, P8]\n"
        "packages: [pkg-a]\ndomains: [backend]\n---\n"
        "### 主流程\n#### BDD-1: test\n",
        encoding="utf-8",
    )
    (task_dir / "P2-design.md").write_text(
        "---\nagent: test\nphase: P2\ntask_id: TXX0001\ntype: design\n"
        "parent: P1-requirements.md\ntrace_id: T001-P2-20260708\n"
        "status: approved\ncreated: 2026-07-08\n---\n"
        "### 候选方案 A：方案一\n### 候选方案 B：方案二\n## 权衡\nA 简单 B 稳健\n"
        "candidate_count: 2\npackages: [pkg-a]\ndomains: [backend]\n"
        "ui_affected: false\ngate_commands: {}\n",
        encoding="utf-8",
    )
    (task_dir / "P2-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nP2 review approved.\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/")
    _write_min_valid_dispatch_context(
        run_cli, python_exe, agate_scripts, agate_root, task_dir, "P2", "architect"
    )
    git_repo.stage("agate-workspace/tasks/T001/P2-dispatch-context-architect.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 P2 thin missing checklist")
    assert result.returncode != 0
    assert "GATE ROUTING" in result.output


# ============================================================
# TAG0035（gate 健壮性批，子批 B，pre-commit-gate.py 部分）：BDD-6/7
# 覆盖非常规（非 P[0-8]- 前缀）阶段名产出文件被暂存时，phase-产出一致性 WARNING
# 不再完全无痕跳过（P2-design.md §3.2-3；根因在 `_P_OUTPUT_RE` 上游过滤层，
# 本批新增 `_P_OUTPUT_ANY_RE` 差集扫描，不改既有窄口径分支）。
# task_id 用 "TXX0001"（而非全文件通用的 "T001"）：本簇用例需要在真实（非
# --no-verify）hook commit 中重新暂存 .state.yaml 以触发 2f 一致性检查，
# check-state-yaml.py 的 task_id 正则 `^T[A-Z]{2}\d+$` 不接受 "T001"
# （已用 `timeout 20 python3 agate/scripts/check-state-yaml.py` 实测确认），
# 沿用本文件 test_it2/test_it3 等既有先例的 "TXX0001"。
# ============================================================


def test_tag0035_bdd_6_pre_commit_nonstandard_phase_output_warns(
    git_repo, agate_root, agate_scripts, run_cli
):
    """BDD-6：任务采用非常规（非 P[0-8]- 前缀）阶段名产出的文件被暂存时，
    pre-commit-gate.py 的 phase-产出一致性检查（WARNING，不拦截 commit）不应在数字
    假设的过滤逻辑下把该文件完全过滤掉、连一条提示都不产生——至少应在 stderr 产生
    可观测提示（如"无法识别该产出文件的阶段号，一致性检查未覆盖"）。

    Given：task phase 全程保持 P3（不触发 2c 状态转移检查），本次 commit 额外暂存了
    一个自定义阶段名产出文件 `p-alpha-notes.md`（非 P[0-8]- 前缀，现有 `_P_OUTPUT_RE`
    完全过滤不掉它进入候选集合）。同时"触碰"（重新暂存但不改变 phase 文本）
    .state.yaml 以让本次 commit 落入 2f 检查的任务候选范围。
    """
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P3")
    _write_p1_requirements(task_dir)
    # P3-test-cases.md 存在（gate_p3 完整度判据只要求文件存在）——避免本用例断言被
    # 无关的 P3 完整度阻断掩盖（本用例只关心 2f 一致性 WARNING 是否产出，不关心
    # commit 最终是否被阻断）。
    (task_dir / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    # 非常规阶段名产出文件（自定义阶段名 p-alpha，非 P[0-8]- 前缀）
    (task_dir / "p-alpha-notes.md").write_text("custom phase output\n", encoding="utf-8")
    # 触碰 .state.yaml（phase 文本本身不变，只追加一个无关字段）——让其在本次 commit
    # 中"被暂存"以进入 2f 检查范围，同时不触发 2c 状态转移检查（无 "+...phase:" 行）
    (task_dir / ".state.yaml").write_text(
        "task_id: TXX0001\nphase: P3\nstatus: active\nretries: {}\nnote: touch\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/T001/p-alpha-notes.md")
    git_repo.stage("agate-workspace/tasks/T001/.state.yaml")
    result = _git_commit(
        run_cli, agate_root, repo, "-m", "T001 non-standard phase output staged"
    )

    # 注意：不能用裸文件名 "p-alpha-notes.md" 作为判据——git commit 自身的
    # "create mode ... p-alpha-notes.md" 摘要行天然包含该文件名，会与"一致性检查
    # 是否产出提示"这一断言目标混淆（曾用手工复现验证过这一假阳性陷阱）。只断言
    # GATE 一致性检查特有的提示短语。
    assert "无法识别" in result.output or "一致性检查未覆盖" in result.output, (
        "非常规阶段名产出文件被暂存时，phase-产出一致性检查应至少产生一条可观测的 "
        f"GATE 提示（不允许 0 输出悄然跳过）。实际 output={result.output!r}"
    )


def test_tag0035_bdd_7_pre_commit_standard_phase_output_no_extra_warning(
    git_repo, agate_root, agate_scripts, run_cli
):
    """BDD-7（pre-commit-gate.py 部分）：标准数字阶段名（P[0-8]-*.md）产出文件被暂存
    时，新增的宽松探测差集扫描不应对已被既有 `_P_OUTPUT_RE` 覆盖的标准文件重复触发
    额外 WARNING（差集 = 宽松命中 - 窄口径命中，标准文件已被窄口径覆盖，差集为空）。"""
    repo = git_repo.path
    _install_pre_commit_hook(repo, agate_scripts)
    _init_commit(run_cli, agate_root, git_repo, repo)

    task_dir = repo / "agate-workspace" / "tasks" / "T001"
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_state_yaml(task_dir, "TXX0001", "P3")
    _write_p1_requirements(task_dir)
    git_repo.stage("agate-workspace/tasks/T001/")
    _git_commit(run_cli, agate_root, repo, "--no-verify", "-q", "-m", "T001 P3 setup")

    (task_dir / "P3-test-cases.md").write_text("## cases\n", encoding="utf-8")
    git_repo.stage("agate-workspace/tasks/T001/P3-test-cases.md")
    result = _git_commit(run_cli, agate_root, repo, "-m", "T001 standard P3 output")

    assert result.returncode == 0
    assert "无法识别" not in result.output
    assert "一致性检查未覆盖" not in result.output
