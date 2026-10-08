# agate/tests/integration/test_tag0050_prod_touched.py
# TAG0050 批 C（生产接触安全门）红灯测试。
#
# 映射：BDD-52..BDD-55（P1-requirements.md §4；设计 §4、P2 §3.1 F4 规格、§10）。
# 平台无关：tmp_path / git_repo；python_exe；不写字面系统临时目录。
#
# R1 整改（G2 SELF-GATE）：BDD-52 走**真实强制点**（真实 git repo + pre-commit-gate.py），
# 断言「主产出缺 prod_touched」错误文案与修复命令；BDD-53 补端到端「true 且非 PAUSED → 中止」。

import pytest

import helpers_tag0050 as h


def _seed_nonlegacy_task(repo, phase, main_output, main_text):
    """在 repo 内建一个非 legacy 任务（账本首行 task_created），返回任务目录。

    main_output / main_text = 该阶段主产出文件名与内容（真实强制点的输入）。
    """
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        f"task_id: TAG0001\nphase: {phase}\nretries: {{}}\n", encoding="utf-8"
    )
    h.write_ledger(
        task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}]
    )
    (task / main_output).write_text(main_text, encoding="utf-8")
    return task


def _commit_via_hook(run_cli, agate_root, agate_scripts, git_repo, repo, rel):
    """安装 pre-commit hook 后暂存主产出并真实提交（端到端强制点）。"""
    h.install_pre_commit_hook(repo, agate_scripts)
    git_repo.stage(rel)
    return h.commit_with_hook(run_cli, agate_root, repo, "-m", "TAG0050 prod_touched probe")


def test_f3_forged_card_block_still_blocks(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """F-3（cso）：伪造的 AGATE_CARD 块不得成为 PROD_TOUCHED 标记的藏身处。

    非 dispatch-context 文件里伪造 START/END 对、把 `[PROD_TOUCHED]` 藏进块内 →
    **仍拦**（排除条件已收紧为「真实注入的卡片块」：文件名 + 块内容 sha256 匹配）。
    """
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-test.md").write_text(
        "---\nagent: test\nprod_touched: false\n---\n\n"
        "<!-- AGATE_CARD_START -->\n[PROD_TOUCHED] 藏在伪造卡片块里\n<!-- AGATE_CARD_END -->\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-test.md")
    r = h.run_gate(
        run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo
    )
    assert r.returncode != 0, f"F-3：伪造 CARD 块内的标记须仍拦，实际 {r.output!r}"
    assert "PROD_TOUCHED" in r.output, f"F-3：须报 PROD_TOUCHED，实际 {r.output!r}"


def test_bdd_49_fix_command_executes_and_turns_green(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-49（H1 整改）：报错附带的修复命令照抄执行后，重新校验**转绿**。

    场景：非 legacy 任务、phase=P4、主产出 P4-implementation.md 缺 `prod_touched`。
    - 第一次提交（真实 hook）→ 报「缺 prod_touched」+ 修复命令；
    - 照抄执行 `agate-md-field-set.py set prod_touched false`（须 rc=0，修复 H1：非 P6
      主产出此前不可写）；
    - 重新提交 → **rc=0 转绿**（P4-review + 任务目录外代码文件满足 gate_p4 的其它前置）。
    """
    repo = h.make_git_repo(None, git_repo)
    task = _seed_nonlegacy_task(
        repo, "P4", "P4-implementation.md",
        "---\nagent: implementer\n---\n\n实现完成\n",
    )
    # P4 gate 的其它前置（与 prod_touched 无关）：P4-review approved + 暂存一个代码文件。
    # 代码文件放**任务目录外** → 满足 gate_p4 的 has_code_file，但不触发 2p 的 P4
    # dispatch-context 强制（该强制只统计任务目录内的非 md/yaml 文件）。
    (task / "P4-review.md").write_text(
        "---\nstatus: approved\nagent: reviewer-subagent\n---\nP4 review.\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src" / "note.txt").write_text("code artifact\n", encoding="utf-8")

    rel = "agate-workspace/tasks/TAG0001/P4-implementation.md"
    h.install_pre_commit_hook(repo, agate_scripts)
    git_repo.stage(rel)
    git_repo.stage("agate-workspace/tasks/TAG0001/P4-review.md")
    git_repo.stage("src/note.txt")
    r = h.commit_with_hook(run_cli, agate_root, repo, "-m", "probe missing prod_touched")
    assert r.returncode != 0, f"BDD-49：前置须因缺 prod_touched 失败，实际 {r.output!r}"
    assert "缺 prod_touched" in r.output, f"BDD-49：须报缺字段，实际 {r.output!r}"

    # 照抄执行修复命令（H1：非 P6 主产出也可执行）
    fix = run_cli(
        python_exe,
        str(agate_scripts / "agate-md-field-set.py"),
        "set",
        "prod_touched",
        "false",
        env={"FILE": str(repo / rel)},
    )
    assert fix.returncode == 0, f"BDD-49：修复命令须可执行，实际 {fix.output!r}"

    # 重新校验 → 转绿
    git_repo.stage(rel)
    r2 = h.commit_with_hook(run_cli, agate_root, repo, "-m", "after fix")
    assert r2.returncode == 0, f"BDD-49：照抄修复后须转绿，实际 {r2.output!r}"


@pytest.mark.windows_smoke
def test_bdd_52_missing_prod_touched_errors(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-52：主产出缺 prod_touched → 真实强制点（装 hook 提交）ERROR + 修复命令。"""
    repo = h.make_git_repo(None, git_repo)
    _seed_nonlegacy_task(
        repo, "P4", "P4-implementation.md",
        "---\nagent: implementer\n---\n\n实现完成\n",
    )
    r = _commit_via_hook(
        run_cli, agate_root, agate_scripts, git_repo, repo,
        "agate-workspace/tasks/TAG0001/P4-implementation.md",
    )
    assert r.returncode != 0, f"BDD-52：缺 prod_touched 须 ERROR，实际 rc={r.returncode}"
    assert "缺 prod_touched" in r.output, f"BDD-52：须报缺字段，实际 {r.output!r}"
    assert "agate-md-field-set.py set prod_touched" in r.output, (
        f"BDD-52：须附可照抄的修复命令，实际 {r.output!r}"
    )


def test_bdd_53_prod_touched_true_not_paused_aborts(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-53：prod_touched: true 且非 PAUSED → 真实强制点（装 hook 提交）中止。"""
    repo = h.make_git_repo(None, git_repo)
    _seed_nonlegacy_task(
        repo, "P4", "P4-implementation.md",
        "---\nagent: implementer\nprod_touched: true\n---\n\n实现完成\n",
    )
    r = _commit_via_hook(
        run_cli, agate_root, agate_scripts, git_repo, repo,
        "agate-workspace/tasks/TAG0001/P4-implementation.md",
    )
    assert r.returncode != 0, f"BDD-53：prod_touched=true 须中止，实际 rc={r.returncode}"
    assert "prod_touched: true" in r.output and "中止" in r.output, (
        f"BDD-53：须报中止语义，实际 {r.output!r}"
    )


def test_bdd_54_bold_marker_field_false_still_aborts(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-54：正文粗体 **[PROD_TOUCHED]**、字段 false 仍中止（T4 优先）。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-verification.md").write_text(
        "---\nagent: test\nprod_touched: false\n---\n\n**[PROD_TOUCHED]** 接触生产\n",
        encoding="utf-8",
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-54：粗体 PROD_TOUCHED 须仍中止，实际 rc={r.returncode}"


def test_bdd_55_negation_form_blocks_with_guidance(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-55：否定写法 `- [PROD_TOUCHED]: 无` 继续阻断并给专门指引（修复 F4）。"""
    repo = h.make_git_repo(None, git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("legacy p5 task")
    (task / "P5-verification.md").write_text(
        "---\nagent: test\n---\n\n- [PROD_TOUCHED]: 无\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/P5-verification.md")
    r = h.run_gate(run_cli, python_exe, agate_scripts, agate_root, "pre-commit-gate.py", cwd=repo)
    assert r.returncode != 0, f"BDD-55：否定写法须继续阻断，实际 rc={r.returncode}"
    assert "疑似否定写法" in r.output, "BDD-55：须给出『疑似否定写法』专门指引"
