# agate/tests/integration/test_tag0050_ci_replay.py
# TAG0050 批 A2（CI 逐提交回放 / 可信锚点）红灯测试。
#
# 映射：BDD-23..BDD-35（P1-requirements.md §4；设计 §2.4、§10）。
# 红灯口径：实现未写 ⇒ 运行期失败 / 契约不满足（B 类）。断言消息不含 A 类关键词。
# 平台无关：tmp_path / git_repo；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_CI_VERIFY = "agate-ci-verify.py"


def _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, *args):
    return run_cli(
        python_exe,
        str(agate_scripts / _CI_VERIFY),
        *args,
        cwd=str(repo),
        env={"AGATE_ROOT": str(agate_root)},
    )


def _task_commit_repo(git_repo, task_id="TAG0001", phase="P5"):
    """建一个含一个任务目录提交的仓库，返回 (repo, base_sha)。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    task = repo / "agate-workspace" / "tasks" / task_id
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: {phase}\nstatus: active\nretries: {{}}\n",
        encoding="utf-8",
    )
    git_repo.commit("task commit")
    return repo, base


@pytest.mark.windows_smoke
def test_bdd_23_pr_replay_passes(run_cli, python_exe, agate_scripts, agate_root, git_repo):
    """BDD-23：PR 口径回放非合并提交全部 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "PASS" in r.output, "BDD-23：PR 口径回放须判 PASS"
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-23：须以逐提交回放口径输出"


def test_bdd_24_push_replay_passes(run_cli, python_exe, agate_scripts, agate_root, git_repo):
    """BDD-24：push 口径（--no-merges before..HEAD）回放同样全部 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(
        run_cli, python_exe, agate_scripts, agate_root, repo, "--push", "--base", base
    )
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-24：须以逐提交回放口径输出"
    assert "PASS" in r.output, "BDD-24：push 口径回放须判 PASS"


def test_bdd_25_no_verify_violation_fails_with_sha(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-25：--no-verify 的违规提交判 FAIL 并指出提交。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    (task / "P7-consistency.md").write_text("---\nagent: test\n---\n", encoding="utf-8")
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P7\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("--no-verify violating commit")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-25：--no-verify 违规提交须判 FAIL"
    assert head[:8] in r.output or head in r.output, "BDD-25：须指出是哪个提交"


def test_bdd_26_ready_output_only_prod_touched_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-26：READY 之后只改产出的 PROD_TOUCHED 提交判 FAIL。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: READY\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("to ready")
    (task / "P8-release.md").write_text(
        "---\nagent: test\n---\n\n[PROD_TOUCHED] 接触生产\n", encoding="utf-8"
    )
    git_repo.commit("--no-verify output-only prod touched")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-26：READY 后只改产出的 PROD_TOUCHED 须判 FAIL"


def test_bdd_27_missing_self_gate_trailer_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-27：缺 self-gate trailer 的协议本体提交判 FAIL（commit-msg 回放）。"""
    repo, base = _task_commit_repo(git_repo)
    (repo / "agate").mkdir(exist_ok=True)
    (repo / "agate" / "protocol-note.md").write_text("protocol change\n", encoding="utf-8")
    git_repo.commit("--no-verify protocol body change without trailer")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-27：缺 self-gate trailer 须判 FAIL"


def test_bdd_28_deleted_created_ledger_fails_mv_passes(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-28：删除已有创建事件账本判 FAIL；legacy 改名判 PASS。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("add created ledger")
    git_repo.git("rm", "-q", "agate-workspace/tasks/TAG0001/gate-events.jsonl")
    git_repo.commit("--no-verify delete created ledger")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-28：删除创建事件账本须判 FAIL"


def test_bdd_29_handwritten_low_level_task_created_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-29：手写低等级 task_created 并 --no-verify 提交判 FAIL。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 0}])
    git_repo.commit("--no-verify handwritten low level")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-29：手写低等级 task_created 须判 FAIL"


def test_non_task_ledger_fixture_not_checked(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """CI gate-backstop 真缺陷（TAG0050 自身交付的 CI 兜底抓出）：非任务账本不得被误判 FAIL。

    Given 一个**非任务账本**路径（`agate/tests/fixtures/.../gate-events.jsonl`）含故意非法内容
          （等级回退），且该路径不在 `agate-workspace/tasks/<task>/` 下
    When 以 `--base` 回放（`_ci_ledger_checks` 无条件枚举 base..HEAD 中变化过的账本）
    Then **不得**报「FAIL 账本」——只有任务账本（tasks 下直接子目录里的 gate-events.jsonl）才计入；
          该文件是供 fail 用例断言判 FAIL 的黄金夹具，误判会让 CI 假红。

    对照（判别力）：同一非法内容若落在**任务账本**路径，`_ci_ledger_checks` 仍须判 FAIL
    （既有 BDD-28/29/K1 用例锁定该行为）。
    """
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    git_repo.commit("pin version")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()

    # 非任务账本：路径不在 agate-workspace/tasks/<task>/ 下（模拟 level-1/fail 黄金夹具）
    fixture = repo / "agate" / "tests" / "fixtures" / "task-data" / "level-1" / "fail"
    fixture.mkdir(parents=True)
    (fixture / "gate-events.jsonl").write_text(
        '{"contract_level":1,"event":"task_created","task_id":"TAG9002"}\n'
        '{"event":"task_upgraded","from_level":1,"to_level":0,"at_phase":"P4"}\n',
        encoding="utf-8",
    )
    git_repo.commit("add non-task illegal fixture ledger")

    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL 账本" not in r.output, (
        f"CI 真缺陷：非任务账本（测试夹具）不得被当真实账本判 FAIL\n{r.output}"
    )
    assert r.returncode == 0, f"CI 真缺陷：非任务账本不应致 CI 失败\n{r.output}"


def _levels_yaml(levels):
    return "".join(
        f'- level: {lv}\n  file: level-{lv}.yaml\n  sha256: "x"\n' for lv in levels
    )


def test_bdd_30_branch_crossing_upgrade_no_false_report(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-30：在途分支跨越协议升级不误报（新增任务等级 ≥ merge-base 处最大等级）。

    真构造（K4）：base 处 `LEVELS.yaml` 最大等级 = 1；分支新增任务 `contract_level=1`；
    分支后续把 LEVELS 升到 2。merge-base（=base）处仍为 1，故新增任务（1）≥ 1 → 等级检查
    不误报（对照：若错用 HEAD 处 LEVELS 最大等级 2，则会误报）。
    """
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    levels = repo / "agate" / "rules" / "task-data"
    levels.mkdir(parents=True)
    (levels / "LEVELS.yaml").write_text(_levels_yaml([1]), encoding="utf-8")
    git_repo.commit("pin version + LEVELS L1")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()

    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("new task L1")

    # 分支后续把 LEVELS 升到 2（merge-base 处仍为 1）
    (levels / "LEVELS.yaml").write_text(_levels_yaml([1, 2]), encoding="utf-8")
    git_repo.commit("upgrade LEVELS to L2")

    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL 等级" not in r.output, (
        f"BDD-30：跨协议升级的在途分支不应误报等级 FAIL\n{r.output}"
    )
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-30：须以逐提交回放口径判定"


def test_bdd_30b_new_task_below_merge_base_level_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """K4/设计 §2.4 第 4 点：新增任务 `contract_level` < merge-base 处 LEVELS.yaml 最大等级 → FAIL。"""
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    levels = repo / "agate" / "rules" / "task-data"
    levels.mkdir(parents=True)
    (levels / "LEVELS.yaml").write_text(_levels_yaml([1, 2]), encoding="utf-8")
    git_repo.commit("pin version + LEVELS L2")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()

    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("new task below merge-base max level")

    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert r.returncode != 0, f"K4：新任务等级低于 merge-base 最大等级须判 FAIL\n{r.output}"
    assert "FAIL 等级" in r.output, f"K4：须报等级 FAIL\n{r.output}"


def test_k1_evil_merge_deletes_ledger_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """K1（cso F-1）：合并提交（evil merge）删除含创建事件的账本 → 判 FAIL。

    合并提交被 `--no-merges` 排除、且其内容未改动任务目录 ⇒ 逐提交回放会 SKIP；账本最终
    状态检查**与回放解耦、无条件执行**（含合并提交），故仍能拦下静默摘除账本。
    """
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    h.write_ledger(task, [{"event": "task_created", "task_id": "TAG0001", "contract_level": 1}])
    git_repo.commit("base with created ledger")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    default = git_repo.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    # feature 分支：非任务改动（回放范围因此无任务提交）
    git_repo.git("checkout", "-q", "-b", "feature")
    (repo / "notes.md").write_text("feature non-task\n", encoding="utf-8")
    git_repo.commit("feature non-task")

    # 回主分支 --no-ff 合并，并在合并中删除账本（evil merge 的冲突解）
    git_repo.git("checkout", "-q", default)
    git_repo.git("merge", "--no-ff", "--no-commit", "feature")
    git_repo.git("rm", "-q", "agate-workspace/tasks/TAG0001/gate-events.jsonl")
    git_repo.commit("evil merge deletes ledger")
    assert git_repo.git(
        "cat-file", "-e", "HEAD:agate-workspace/tasks/TAG0001/gate-events.jsonl"
    ).returncode != 0, "K1：构造须真的删除了账本"

    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert r.returncode != 0, f"K1：evil merge 删账本须判 FAIL\n{r.output}"
    assert "FAIL" in r.output, "K1：须报 FAIL"
    assert "账本" in r.output, f"K1：须指明账本被删/改写\n{r.output}"


def test_bdd_31_user_project_without_version_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-31：使用者项目未写 .agate-version 判 FAIL 并给提示。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.commit("task commit")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-31：未固定协议版本须判 FAIL"
    assert ".agate-version" in r.output, "BDD-31：须提示写 .agate-version"


def test_bdd_32_pr_downgrade_version_fails(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-32：PR 降级 .agate-version 判 FAIL（单调不降被违反）。"""
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v9.9.9\n", encoding="utf-8")
    git_repo.commit("pin version")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / ".agate-version").write_text("agate: v0.0.1\n", encoding="utf-8")
    git_repo.commit("downgrade version")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "BDD-32：降级 .agate-version 须判 FAIL"


def test_bdd_33_pr_mid_upgrade_version_no_false_report(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-33：PR 中途升级 .agate-version 不误报。"""
    repo = h.make_git_repo(None, git_repo)
    (repo / ".agate-version").write_text("agate: v0.0.1\n", encoding="utf-8")
    git_repo.commit("pin low")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / ".agate-version").write_text("agate: v9.9.9\n", encoding="utf-8")
    git_repo.commit("upgrade version")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "回放" in r.output or "replay" in r.output.lower(), "BDD-33：须以逐提交回放口径判定"
    assert "FAIL" not in r.output, "BDD-33：中途升级不应误报 FAIL"


def test_bdd_34_no_task_dir_pr_skips_with_reason(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-34：未改动任务目录的 PR 判 SKIP 并附原因。"""
    repo = h.make_git_repo(None, git_repo)
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    (repo / "notes.md").write_text("no task changes\n", encoding="utf-8")
    git_repo.commit("non-task change")
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "SKIP" in r.output or "跳过" in r.output, "BDD-34：无任务目录改动须 SKIP"
    assert "改动" in r.output, "BDD-34：SKIP 须指明『未改动任务目录』原因"


def test_bdd_35_replay_interface_records_timing(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """BDD-35：E4 耗时在可接受范围（回放输出记录被回放提交数与耗时）。"""
    repo, base = _task_commit_repo(git_repo)
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "耗时" in r.output or "elapsed" in r.output.lower(), (
        "BDD-35：回放须记录被回放提交数与耗时"
    )


def test_bdd_26b_legacy_prod_touched_error_separately_counted(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """F5 / 设计 §8 第 12 项：legacy 任务新增 PROD_TOUCHED ERROR 单独计数并列 SHA。"""
    repo, base = _task_commit_repo(git_repo)
    task = repo / "agate-workspace" / "tasks" / "TAG0001"
    (task / "P4-progress.md").write_text("[PROD_TOUCHED] 接触生产\n", encoding="utf-8")
    # 同时暂存 .state.yaml（空白变更）——确保回放协议（merge-base 处）也做 PROD_TOUCHED 扫描
    (task / ".state.yaml").write_text(
        (task / ".state.yaml").read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace/tasks/TAG0001/.state.yaml")
    git_repo.commit("--no-verify prod touched in legacy task")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    r = _ci_verify(run_cli, python_exe, agate_scripts, agate_root, repo, "--base", base)
    assert "FAIL" in r.output, "F5：legacy 新增 PROD_TOUCHED 须判 FAIL"
    assert "§8-12" in r.output or "PROD_TOUCHED ERROR" in r.output, (
        "F5：legacy 新增 PROD_TOUCHED ERROR 须单独统计"
    )
    assert head[:8] in r.output or head in r.output, "F5：须逐条列出提交 SHA"


def test_push_all_zero_before_does_not_fail(
    run_cli, python_exe, agate_scripts, agate_root, git_repo
):
    """A1-6：push 的 `before` 为全零（新建分支）时不因全零 SHA 误判 FAIL。"""
    repo, _ = _task_commit_repo(git_repo)
    zero = "0" * 40
    r = _ci_verify(
        run_cli, python_exe, agate_scripts, agate_root, repo, "--push", "--base", zero
    )
    assert r.returncode == 0, f"A1-6：全零 before 不应判 FAIL，output={r.output}"
    assert "FAIL" not in r.output, "A1-6：全零 before 不应因 rev-list 全零范围失败"
