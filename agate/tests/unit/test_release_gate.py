# agate/tests/unit/test_release_gate.py — TAG0051 P3 红灯（批 release-gate）
#
# 交付能力：**独立发布门 + `workflow_dispatch` 人工入口**（P2-design §4 批 `release-gate`）。
# 覆盖 BDD（P1-requirements.md）：8 / 9 / 10 / 11 / 12 / 13 / 23。
#
# 目标语义（P2-design M11 / M12 / 决策 1-3）：
#   * BDD-8：`.github/workflows/release.yml` 的 `on:` 含 `workflow_dispatch`。
#   * BDD-9/10：发布门（`agate-release.py gate`）机械校验「目标提交 CI success」；非 success
#     （含 push-to-main 口径失败）→ 非 0（fail-closed）。
#   * BDD-11：保留既有「Verify tag points to matching commit」步（不重实现，只要求继续生效）——回归锁。
#   * BDD-12：发布门校验 `check-protocol-consistency.py` 0 ERROR；ERROR → 门判失败。
#   * BDD-13：发布门复用 `check-gate.py P8` 的 RM-AG0043 反查（关联 RM 非 done → 判失败）。
#   * BDD-23：发布门落点 = 既有 `agate-*.py`（`agate-release.py gate`）⇒ SG.6 / CHECK9-coverage 零触发。
#
# 现行为（改动前）：`release.yml` 无 `workflow_dispatch`；`agate-release.py` 无 `gate` 子命令
#   ⇒ 断言失败 = B 类红灯。
#
# [DESIGN_GAP → 契约固定]（P2 §2 候选 A / §8；P3 固定可测接缝）：
#   发布门的 CI / consistency 结果经**注入命令**提供（P2 明示「可注入命令（--ci-cmd / 环境变量）」）：
#     agate-release.py gate --task <TASK_DIR> --sha <COMMITISH>
#                          [--ci-cmd <CMD>] [--consistency-cmd <CMD>]
#   * `--ci-cmd`   stdout = JSON 数组 `[{"name","status","conclusion"}]`（目标提交的 check-runs）；
#                  缺省 = 查 GitHub；任一 required 检查 `conclusion != success`（含 in_progress/queued）→ 非 0。
#   * `--consistency-cmd` 退出码即 consistency 结论（缺省 = 真跑 check-protocol-consistency.py）；非 0 → 门非 0。
#   命令经 `shlex.split` 后直接执行（无 shell）。
#
# 平台无关：tmp_path / git_repo / agate_root fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding；不写仓库内已提交文件。不写字面系统临时目录。

import json

import yaml

import helpers_tag0050 as H5
import helpers_tag_repo as H

_RELEASE_YML = ".github/workflows/release.yml"

_P8_BODY = (
    "---\n"
    "bump_type: minor\n"
    "debt_check: none\n"
    "delivery:\n"
    "  method: release-notes\n"
    "  ref:\n"
    "    - CHANGELOG.md\n"
    "---\n\n"
    "# P8 交付收尾（fixture）\n"
)

_ROADMAP_HEADER = (
    "# roadmap\n\n"
    "| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |\n"
    "|----|------|------|------|----------|------|------|\n"
)


# ── release.yml 契约（BDD-8 / BDD-11）─────────────────────────────────────
def _release_doc(agate_root):
    text = (agate_root.parent / _RELEASE_YML).read_text(encoding="utf-8")
    return yaml.safe_load(text), text


def _steps(doc):
    return [s for job in doc["jobs"].values() for s in job.get("steps", [])]


def test_bdd_8_release_workflow_has_workflow_dispatch(agate_root):
    """BDD-8：release.yml 的 `on:` 含 `workflow_dispatch`（人工授权入口）。"""
    doc, _ = _release_doc(agate_root)
    trig = doc.get(True, doc.get("on"))
    assert isinstance(trig, dict), f"BDD-8：release.yml `on` 应为映射，实际 {trig!r}"
    assert "workflow_dispatch" in trig, (
        "BDD-8：release.yml 未提供 `workflow_dispatch` 人工授权入口"
        f"（当前触发器：{sorted(trig)}）"
    )


def test_bdd_8_workflow_dispatch_coexists_with_push_tags(agate_root):
    """BDD-8：`workflow_dispatch` 与既有 `push: tags` 触发器并存（tag push 仍是 backstop）。"""
    doc, _ = _release_doc(agate_root)
    trig = doc.get(True, doc.get("on"))
    assert "workflow_dispatch" in trig and "push" in trig, (
        f"BDD-8：`workflow_dispatch` 须与既有 push 触发器并存，实际 {sorted(trig)}"
    )


def test_bdd_11_tag_verify_step_still_present(agate_root):
    """BDD-11（回归锁）：保留既有「Verify tag points to matching commit」步（tag↔提交一致）。"""
    doc, _ = _release_doc(agate_root)
    hits = [s for s in _steps(doc) if "Verify tag points to matching commit" in str(s.get("name", ""))]
    assert len(hits) == 1, f"BDD-11：应恰有 1 个 tag 指向校验步骤，实际 {len(hits)}"
    run = str(hits[0].get("run", ""))
    assert "badge/version-v" in run and "CHANGELOG" in run, (
        "BDD-11：tag 指向校验步须校验 README badge 与 CHANGELOG 版本节"
    )
    assert run.count("exit 1") >= 2, "BDD-11：tag 指向校验须 fail-closed（多处显式 exit 1）"


# ── 发布门 CLI 注入夹具 ───────────────────────────────────────────────────
def _repo_with_task(git_repo, task_id="TAG9100", roadmap_row=None):
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    td = repo / "task"
    td.mkdir()
    (td / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: P8\nretries: {{}}\n", encoding="utf-8"
    )
    (td / "gate-events.jsonl").write_text(_ledger(task_id, 1), encoding="utf-8")
    (td / "P8-release.md").write_text(_P8_BODY, encoding="utf-8")
    if roadmap_row is not None:
        rm = repo / "agate-workspace" / "roadmap"
        rm.mkdir(parents=True)
        (rm / "roadmap.md").write_text(_ROADMAP_HEADER + roadmap_row + "\n", encoding="utf-8")
    return repo, td


def _ledger(task_id, level):
    ev = {
        "event": "task_created",
        "task_id": task_id,
        "contract_level": level,
        "prev_hash": H5.GENESIS_HASH,
        "ts": "2026-10-07T00:00:00.000000Z",
    }
    return json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n"


def _cmd_script(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def _ci_cmd(tmp_path, python_exe, runs):
    """构造 `--ci-cmd`：打印 runs（check-runs JSON）到 stdout。"""
    json_file = tmp_path / "runs.json"
    json_file.write_text(json.dumps(runs), encoding="utf-8")
    script = _cmd_script(
        tmp_path,
        "ci_dump.py",
        "import sys\nsys.stdout.write(open(sys.argv[1], encoding='utf-8').read())\n",
    )
    return f"{python_exe} {script} {json_file}"


def _rc_cmd(tmp_path, python_exe, rc):
    """构造 `--consistency-cmd`：以给定退出码结束。"""
    script = _cmd_script(
        tmp_path, f"rc_{rc}.py", "import sys\nsys.exit(int(sys.argv[1]))\n"
    )
    return f"{python_exe} {script} {rc}"


_OK_RUNS = [
    {"name": "pytest (ubuntu-latest)", "status": "completed", "conclusion": "success"},
    {"name": "consistency", "status": "completed", "conclusion": "success"},
    {"name": "gate-backstop", "status": "completed", "conclusion": "success"},
]


def _gate(agate_scripts, python_exe, run_cli, repo, td, extra):
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-release.py"),
        "gate",
        "--task",
        str(td),
        "--sha",
        "HEAD",
        *extra,
        cwd=str(repo),
    )


# ── BDD-9/10：CI success 机械校验（fail-closed）─────────────────────────────
def test_bdd_9_gate_passes_when_ci_success(
    git_repo, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-9（正向）：目标提交 CI 全 success + consistency 0 ⇒ 发布门通过（exit 0）。"""
    repo, td = _repo_with_task(git_repo)
    extra = [
        "--ci-cmd", _ci_cmd(tmp_path, python_exe, _OK_RUNS),
        "--consistency-cmd", _rc_cmd(tmp_path, python_exe, 0),
    ]
    result = _gate(agate_scripts, python_exe, run_cli, repo, td, extra)
    assert result.returncode == 0, (
        f"BDD-9：CI 全 success 时发布门应通过（exit 0），实际 rc={result.returncode}"
    )


def test_bdd_9_gate_fails_when_ci_not_success(
    git_repo, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-9（反例）：目标提交 CI 非 success（in_progress）⇒ 发布门非 0。"""
    repo, td = _repo_with_task(git_repo)
    runs = [
        {"name": "pytest (ubuntu-latest)", "status": "in_progress", "conclusion": None},
        {"name": "consistency", "status": "completed", "conclusion": "success"},
    ]
    extra = [
        "--ci-cmd", _ci_cmd(tmp_path, python_exe, runs),
        "--consistency-cmd", _rc_cmd(tmp_path, python_exe, 0),
    ]
    result = _gate(agate_scripts, python_exe, run_cli, repo, td, extra)
    assert result.returncode != 0, (
        f"BDD-9：CI 非 success（pending）时发布门须非 0（fail-closed），实际 rc={result.returncode}"
    )


def test_bdd_10_gate_fails_when_push_branch_ci_failed(
    git_repo, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-10（TAG0050 事故回归锁）：合并后 push 口径 CI 失败 ⇒ 发布门非 0。

    「PR required 全绿 ≠ 合并后绿」须机械可查——本用例直接以 push 口径的失败结论驱动门。
    """
    repo, td = _repo_with_task(git_repo)
    runs = [
        {"name": "pytest (ubuntu-latest)", "status": "completed", "conclusion": "failure"},
        {"name": "consistency", "status": "completed", "conclusion": "success"},
    ]
    extra = [
        "--ci-cmd", _ci_cmd(tmp_path, python_exe, runs),
        "--consistency-cmd", _rc_cmd(tmp_path, python_exe, 0),
    ]
    result = _gate(agate_scripts, python_exe, run_cli, repo, td, extra)
    assert result.returncode != 0, (
        "BDD-10：push 口径 CI 失败时发布门须非 0（不得把 PR 口径绿当等价），"
        f"实际 rc={result.returncode}"
    )


# ── BDD-12：CHECK 7/13（consistency）0 ERROR ───────────────────────────────
def test_bdd_12_gate_fails_when_consistency_error(
    git_repo, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-12（反例）：consistency 非 0（含 CHECK 7/13 ERROR）⇒ 发布门非 0。"""
    repo, td = _repo_with_task(git_repo)
    extra = [
        "--ci-cmd", _ci_cmd(tmp_path, python_exe, _OK_RUNS),
        "--consistency-cmd", _rc_cmd(tmp_path, python_exe, 1),
    ]
    result = _gate(agate_scripts, python_exe, run_cli, repo, td, extra)
    assert result.returncode != 0, (
        f"BDD-12：consistency 报 ERROR 时发布门须非 0，实际 rc={result.returncode}"
    )


# ── BDD-13：roadmap 关联 RM 须已 done ─────────────────────────────────────
def test_bdd_13_gate_fails_when_roadmap_rm_not_done(
    git_repo, tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-13：待发布任务关联 RM 状态非 done ⇒ 发布门非 0（须先回写 done）。"""
    row = "| RM-AG9100 | fixture | scheduled | P0 | TAG9100 | 2026-10-11 | 2026-10-11 |"
    repo, td = _repo_with_task(git_repo, task_id="TAG9100", roadmap_row=row)
    extra = [
        "--ci-cmd", _ci_cmd(tmp_path, python_exe, _OK_RUNS),
        "--consistency-cmd", _rc_cmd(tmp_path, python_exe, 0),
    ]
    result = _gate(agate_scripts, python_exe, run_cli, repo, td, extra)
    assert result.returncode != 0, (
        f"BDD-13：关联 RM 非 done 时发布门须非 0，实际 rc={result.returncode}"
    )


# ── BDD-23：发布门落点 = 既有 agate-*.py ⇒ 登记面零触发 ─────────────────────
def test_bdd_23_release_gate_is_agate_star_subcommand(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-23 支②：发布门落为既有 `agate-*.py`（`agate-release.py gate`）子命令。

    以 `gate --help` 退出码判定子命令存在（当前无 `gate` ⇒ argparse 失败 ⇒ 红灯）。
    """
    result = run_cli(
        python_exe, str(agate_scripts / "agate-release.py"), "gate", "--help", cwd=str(tmp_path)
    )
    assert result.returncode == 0, (
        "BDD-23：发布门须落为 `agate-release.py gate` 子命令（支②）；"
        f"`gate --help` rc={result.returncode}（无该子命令，或落点非 agate-*.py）"
    )


def test_bdd_23_no_new_check_star_script_added(agate_scripts):
    """BDD-23 支①排除：未新增 `agate/scripts/check-*.py`（否则 SG.6 红 / CHECK9-coverage WARNING）。

    对照 `origin/main` 的 `agate/scripts/check-*.py` 集合；本方案（支②）不应引入新 check 脚本。
    """
    current = sorted(p.name for p in agate_scripts.glob("check-*.py"))
    probe = H.run_git(H.REPO_ROOT, "rev-parse", "--verify", "-q", "origin/main")
    if probe.returncode != 0:
        # 无 origin/main（浅克隆 / 无远端）：仅断言既有 check 家族存在，分支① 排除由落点判定覆盖
        assert current, "BDD-23：应与既有 check-*.py 家族共存"
        return
    out = H.run_git(
        H.REPO_ROOT, "ls-tree", "-r", "--name-only", "origin/main", "--", "agate/scripts"
    ).stdout.decode("utf-8")
    baseline = sorted(
        p.rsplit("/", 1)[-1]
        for p in out.split()
        if p.rsplit("/", 1)[-1].startswith("check-") and p.endswith(".py")
    )
    added = [n for n in current if n not in baseline]
    assert not added, (
        "BDD-23：新增了 `agate/scripts/check-*.py`（落点①）——本方案应落 agate-*.py（支②）；"
        f"新增：{added}"
    )
