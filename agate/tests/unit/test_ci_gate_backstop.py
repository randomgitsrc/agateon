# tests/unit/test_ci_gate_backstop.py — ci-gate-backstop.py 平台探测 + P3 兜底（ci-gate-backstop.bats 11 用例迁移）
# （TAG0011 批次 9c；TAG0002 [SCOPE+] refactor 感知分支同批迁移）
# 被测：agate/scripts/ci-gate-backstop.py（cwd 下 .state.yaml + .gate-result.json 对照）。
# 流语义（P2 BLOCKER-1）：bats `bash -c "... 2>&1 || true"` 显式合并 → 断言一律用合并流
#   result.output（stdout+stderr），无需再显式合并（P2 §3.2 流语义规则）。
# 平台探测：CI 平台变量（GITEA/GITLAB/GITHUB）经 run_cli env 显式控制（"" 等价 unset，
#   防御测试机本身在 CI 中被注入）；mock TDD 运行器经 AGATE_TDD_RED_SCRIPT env 指向可执行脚本
#   （等价 bats export + py_path；py_path Linux 恒等）。windows_smoke 4 处（P3 §5.2 表 W：
#   detect_ci_platform 3 + cp1252 1）。

import pytest


def _ci_env(**overrides):
    env = {
        "PYTHONIOENCODING": "utf-8",
        "GITEA_ACTIONS": "",
        "GITLAB_CI": "",
        "GITHUB_ACTIONS": "",
    }
    env.update(overrides)
    return env


def _run_backstop(python_exe, run_cli, py_path, scripts, repo, env):
    return run_cli(
        python_exe,
        py_path(str(scripts / "ci-gate-backstop.py")),
        cwd=str(repo),
        env=env,
    )


def _setup_p3_base(git_repo):
    """setup_git_repo_p3 等价：git_init + 根 .state.yaml（phase P3）+ T001/P3-test-cases.md + commit。"""
    repo = git_repo.path
    tasks = repo / "agate-workspace" / "tasks" / "T001"
    tasks.mkdir(parents=True)
    (repo / ".state.yaml").write_text(
        "task_id: T001\nphase: P3\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    (tasks / "P3-test-cases.md").write_text("## P3 test cases\n", encoding="utf-8")
    git_repo.commit("p3")
    return repo, tasks


def _write_mock(repo, name, exit_code):
    mock = repo / name
    mock.write_text(
        f"#!/usr/bin/env python3\nimport sys\nsys.exit({exit_code})\n",
        encoding="utf-8",
    )
    mock.chmod(0o755)
    return mock


@pytest.mark.windows_smoke
def test_detect_ci_platform_gitea_priority(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    env = _ci_env(GITEA_ACTIONS="true", GITHUB_ACTIONS="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, git_repo.path, env)
    assert "gitea" in result.output


@pytest.mark.windows_smoke
def test_detect_ci_platform_gitlab(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    env = _ci_env(GITLAB_CI="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, git_repo.path, env)
    assert "gitlab" in result.output


@pytest.mark.windows_smoke
def test_detect_ci_platform_no_platform_skip(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    env = _ci_env()
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, git_repo.path, env)
    assert "SKIP" in result.output or "None" in result.output


def test_backstop_p3_true_red_pass(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-ok", 0)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "真红灯" in result.output


def test_backstop_p3_green_fail(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-green", 2)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "FAIL" in result.output
    assert "绿灯" in result.output


def test_backstop_p3_fake_red_fail(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-fake", 1)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "FAIL" in result.output
    assert "假红灯" in result.output


def test_backstop_p3_no_runner_warn(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-norunner", 3)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "WARN" in result.output
    assert "FAIL" not in result.output


def test_backstop_p3_no_gate_result_still_runs_tdd(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-ok2", 0)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "真红灯" in result.output


def test_backstop_p3_refactor_skip(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, tasks = _setup_p3_base(git_repo)
    (tasks / "P1-requirements.md").write_text(
        "---\n"
        "agent: test\n"
        "risk_level: medium\n"
        "change_type: refactor\n"
        "---\n"
        "#### BDD-1: 关键路径行为不变\n"
        "- Given 重构后的协议状态\n"
        "- When 执行关键路径\n"
        "- Then 行为与重构前一致\n",
        encoding="utf-8",
    )
    git_repo.commit("p3 refactor")
    mock = _write_mock(repo, "mock-tdd-refactor", 2)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "SKIP" in result.output
    assert "refactor" in result.output
    assert "FAIL" not in result.output


def test_backstop_p3_body_mention_not_skip(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, tasks = _setup_p3_base(git_repo)
    (tasks / "P1-requirements.md").write_text(
        "---\n"
        "agent: test\n"
        "risk_level: medium\n"
        "---\n"
        "change_type: refactor 是可选字段，缺省为功能任务（本文档仅作说明，本任务不采用 refactor 口径）\n",
        encoding="utf-8",
    )
    git_repo.commit("p3 body mention")
    mock = _write_mock(repo, "mock-tdd-body-mention", 2)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "FAIL" in result.output
    assert "绿灯" in result.output
    assert "SKIP: refactor" not in result.output


@pytest.mark.windows_smoke
def test_backstop_p3_cp1252(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    repo, _tasks = _setup_p3_base(git_repo)
    mock = _write_mock(repo, "mock-tdd-cp1252", 0)
    base = {"GITHUB_ACTIONS": "true", "AGATE_TDD_RED_SCRIPT": py_path(str(mock))}
    # ① 无 utf-8 导出 + 强制 cp1252 → 中文 print 崩溃
    crash = _run_backstop(
        python_exe, run_cli, py_path, agate_scripts, repo, _ci_env(PYTHONIOENCODING="cp1252", **base)
    )
    assert "UnicodeEncodeError" in crash.output
    # ② 文件级 utf-8 导出兜底 → 无崩溃、中文关键词可断言
    ok = _run_backstop(
        python_exe, run_cli, py_path, agate_scripts, repo, _ci_env(**base)
    )
    assert "UnicodeEncodeError" not in ok.output
    assert "真红灯" in ok.output


def test_backstop_p5_py_gate_pass(
    git_repo, agate_scripts, python_exe, run_cli, py_path
):
    """M1 回归锁：run_gate 调 check-gate.py（非已删 .sh），P5 场景 exit 一致 → PASS。

    历史：v0.47.0 ci-gate-backstop.py 仍调已删 check-gate.sh → 合法项目恒
    "check-gate.sh not found" exit 2 → .gate-result.json 对照必 FAIL（CI backstop 失效）。
    P5 gate 返回 2（需主 Agent 自判），.gate-result.json exit_code=2 应一致 PASS。
    """
    repo = git_repo.path
    tasks = repo / "agate-workspace" / "tasks" / "T001"
    tasks.mkdir(parents=True)
    (repo / ".state.yaml").write_text(
        "task_id: T001\nphase: P5\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    (repo / ".gate-result.json").write_text(
        '{"phase": "P5", "exit_code": 2, "timestamp": ""}\n', encoding="utf-8"
    )
    git_repo.commit("p5")
    env = _ci_env(GITHUB_ACTIONS="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert "check-gate.sh not found" not in result.output
    assert "PASS" in result.output
    assert "FAIL" not in result.output


# ── X3（TAG0042 批0）：5 个 SKIP 面不得**静默**假绿 ──────────────────────────
#
# 缺陷：`return 0`（exit 0 = 绿）是**有意**设计（gate-backstop 是 required check，
#   一旦 skipped 会被分支保护永久 BLOCK）。但 5 个 SKIP 面的输出**与 PASS 无法区分**
#   ⇒ 读者无法从 CI 状态分辨「兜底跑了且通过」与「兜底根本没跑」= 假绿。
# 目标（ADR-015 手段②「让错误可见」）：**保留 exit 0**，但每个 SKIP 面都输出
#   **显式 WARNING 块**（含"backstop 未生效"+ 如何配置）。
# 判据为**行为判据**：逐面构造输入，断言「exit 0 不变」**且**「输出含 WARNING 标识」。

_SKIP_WARN = "BACKSTOP-INACTIVE"


def test_x3_no_platform_skip_is_loud(git_repo, agate_scripts, python_exe, run_cli, py_path):
    """面①：未识别 CI 平台（L124）。"""
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, git_repo.path, _ci_env())
    assert result.returncode == 0, "exit 0 必须保持（required check 不能被 skip）"
    assert _SKIP_WARN in result.output, f"未识别平台须显式告警\n{result.output[-400:]}"


def test_x3_no_state_yaml_skip_is_loud(git_repo, agate_scripts, python_exe, run_cli, py_path):
    """面②：无 .state.yaml（L132）。"""
    env = _ci_env(GITHUB_ACTIONS="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, git_repo.path, env)
    assert result.returncode == 0
    assert _SKIP_WARN in result.output, f"无 .state.yaml 须显式告警\n{result.output[-400:]}"


def test_x3_unreadable_state_yaml_skip_is_loud(git_repo, agate_scripts, python_exe, run_cli, py_path):
    """面③：无法读取 .state.yaml（L142）——**最该醒目的一个**（数据坏了却报绿）。"""
    repo = git_repo.path
    (repo / ".state.yaml").write_text("phase: [未闭合\n", encoding="utf-8")   # YAML 非法
    env = _ci_env(GITHUB_ACTIONS="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert result.returncode == 0
    assert _SKIP_WARN in result.output, (
        f"读不出 .state.yaml 时更须显式告警（否则数据坏了却显示绿）\n{result.output[-400:]}"
    )


def test_x3_phase_without_gate_skip_is_loud(git_repo, agate_scripts, python_exe, run_cli, py_path):
    """面④：phase 无 gate 需对照（L146，如 PAUSED/READY/DONE）。"""
    repo = git_repo.path
    (repo / ".state.yaml").write_text(
        "task_id: T001\nphase: READY\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    env = _ci_env(GITHUB_ACTIONS="true")
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert result.returncode == 0
    assert _SKIP_WARN in result.output, f"phase 无 gate 对照须显式告警\n{result.output[-400:]}"


def test_x3_refactor_skip_distinguishable(git_repo, agate_scripts, python_exe, run_cli, py_path):
    """面⑤：refactor 任务跳过 TDD 红灯（语义正当）——但**措辞须与其余 SKIP 区分**。

    该面是"有意跳过且语义正确"，故仍须可见（否则与其他面一样无法分辨），
    但用**不同的标识**（REFACTOR-EXEMPT）表明这是**规则允许**的豁免，不是机制失效。
    """
    repo, tasks = _setup_p3_base(git_repo)
    (tasks / "P1-requirements.md").write_text(
        "---\nagent: test\nrisk_level: medium\nchange_type: refactor\n---\n"
        "#### BDD-1: 关键路径行为不变\n- Given 重构后的协议状态\n"
        "- When 执行关键路径\n- Then 行为与重构前一致\n",
        encoding="utf-8",
    )
    git_repo.commit("p3 refactor")
    mock = _write_mock(repo, "mock-tdd-refactor", 2)
    env = _ci_env(GITHUB_ACTIONS="true", AGATE_TDD_RED_SCRIPT=py_path(str(mock)))
    result = _run_backstop(python_exe, run_cli, py_path, agate_scripts, repo, env)
    assert result.returncode == 0
    assert "REFACTOR-EXEMPT" in result.output, (
        f"refactor 豁免须有**可区分**标识\n{result.output[-400:]}"
    )
    assert _SKIP_WARN not in result.output, "refactor 面是规则允许的豁免，不属'机制未生效'"
