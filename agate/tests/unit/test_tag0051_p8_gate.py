# agate/tests/unit/test_tag0051_p8_gate.py — TAG0051 P3 红灯（批 ready-no-tag）
#
# 交付能力：**P8 gate 不再要求 version/tag；交付止于 READY**（P2-design §4 批 `ready-no-tag`）。
# 覆盖 BDD（P1-requirements.md）：2 / 3 / 4 / 5 / 6 / 7 / 19。
#
# 目标语义（P2-design M1 / 决策 5 / 决策 6）：
#   * BDD-2：`check-gate.py P8` 对「无对应版本 tag」**不再告警**（删 :2376-2389 tag WARNING 块）。
#   * BDD-3：`check-gate.py P8` **不再要求 version 文件变更**（删 :2317-2337 version WARNING 块）。
#   * BDD-4/5：READY 前置保留「CHANGELOG `[Unreleased]` 含 task_id」——载体 `check-changelog.py`
#     （**回归锁**，载体已存在；本对用例是回归锁，当前即绿）。
#   * BDD-6/7：`bump_type` 意图字段（有 → exit 2；缺 → exit 1）——已有行为，**回归锁**。
#   * BDD-19：`agate.config.yaml` 的迁移期提示块（基于已移除的 version/tag 痕迹）**不再出现**
#     （删 :2358-2374），且 `check-protocol-consistency.py` 0 ERROR（后者由 P5_consistency 兜底）。
#
# 现行为（改动前）：P8 gate 仍发 version/tag WARNING；仍打「未发现项目声明 agate.config.yaml」提示
#   ⇒ BDD-2/3/19 断言失败 = B 类红灯（实现未写，非测试自身错误）。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；显式 encoding；
#   不写仓库内已提交文件（全在 tmp_path / git_repo）。红灯原因一律为「断言不成立」（B 类）。

import json

import helpers_tag0050 as H5

_P8_PASS_EXIT = 2  # phases.yaml 声明 P8 gate_pass_exit == 2（回归基线）

# level-1 非 legacy 任务的合规 P8 产出（结构化 delivery，见 level-1.yaml `delivery` 契约）。
_P8_LEVEL1_BODY = (
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


def _ledger(task_id, contract_level):
    """单行 `task_created` 账本（哈希链合法，prev_hash = GENESIS）。"""
    ev = {
        "event": "task_created",
        "task_id": task_id,
        "contract_level": contract_level,
        "prev_hash": H5.GENESIS_HASH,
        "ts": "2026-10-07T00:00:00.000000Z",
    }
    return json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n"


def _write_task(task_dir, p8_body, task_id="TAG9001", contract_level=1):
    """在给定目录写最小可判定任务（.state.yaml + 合法账本 + P8-release.md）。"""
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: P8\nretries: {{}}\n", encoding="utf-8"
    )
    (task_dir / "gate-events.jsonl").write_text(
        _ledger(task_id, contract_level), encoding="utf-8"
    )
    (task_dir / "P8-release.md").write_text(p8_body, encoding="utf-8")
    return task_dir


def _run_p8(task_dir, agate_scripts, python_exe, run_cli, cwd):
    return run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P8", str(task_dir), cwd=str(cwd)
    )


# ── BDD-2：无对应版本 tag → 不再告警 ─────────────────────────────────────────
def test_bdd_2_p8_gate_no_tag_warning(git_repo, agate_scripts, python_exe, run_cli):
    """BDD-2：P8 产出已声明 bump_type/delivery/debt_check，本地无对应 tag ⇒ gate 不因 tag 告警。

    Given 非 legacy（level-1）任务 P8 产出 + 暂存区 CHANGELOG 含版本节（无对应 tag）
    When 运行 `check-gate.py P8`
    Then stderr 不含 tag 相关告警，且退出码为 2。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    td = _write_task(repo / "task", _P8_LEVEL1_BODY)
    # 暂存区 CHANGELOG 含 `[9.9.9]` 版本节：触发（既有）tag 存在性检查路径
    (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n- TAG9001 条目\n\n## [9.9.9] - 2026-10-11\n\n- x\n",
        encoding="utf-8",
    )
    git_repo.stage("CHANGELOG.md")

    result = _run_p8(td, agate_scripts, python_exe, run_cli, repo)
    assert "tag" not in result.stderr.lower(), (
        "BDD-2：P8 gate 对无对应版本 tag 仍告警（tag 语义应已移出 READY/P8）——"
        f"rc={result.returncode}"
    )
    assert result.returncode == _P8_PASS_EXIT, (
        f"BDD-2：无 tag 时 P8 gate 应通过（rc={_P8_PASS_EXIT}），实际 rc={result.returncode}"
    )


# ── BDD-3：不再要求 version 文件变更 ────────────────────────────────────────
def test_bdd_3_p8_gate_no_version_warning(git_repo, agate_scripts, python_exe, run_cli):
    """BDD-3：未修改任何 version 文件 ⇒ gate 不因 version 变更告警，退出码 2（刻意口径收敛）。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    td = _write_task(repo / "task", _P8_LEVEL1_BODY)

    result = _run_p8(td, agate_scripts, python_exe, run_cli, repo)
    assert "version 文件变更" not in result.stderr, (
        "BDD-3：P8 gate 仍在要求 version 文件变更（应已移除）——"
        f"rc={result.returncode}"
    )
    assert result.returncode == _P8_PASS_EXIT, (
        f"BDD-3：未改 version 文件时 P8 gate 应通过（rc={_P8_PASS_EXIT}），"
        f"实际 rc={result.returncode}"
    )


# ── BDD-4/5：CHANGELOG `[Unreleased]` 含 task_id（回归锁，载体 check-changelog.py）──
def test_bdd_4_changelog_unreleased_with_task_id_exit_0(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-4：`[Unreleased]` 段含 task_id ⇒ `check-changelog.py <task_id>` exit 0（回归锁）。"""
    repo = git_repo.path
    (repo / "CHANGELOG.md").write_text(
        "## [Unreleased]\n- TAG9001 任务完成\n", encoding="utf-8"
    )
    result = run_cli(
        python_exe, str(agate_scripts / "check-changelog.py"), "TAG9001", cwd=str(repo)
    )
    assert result.returncode == 0, (
        f"BDD-4：`[Unreleased]` 含 task_id 应 exit 0，实际 rc={result.returncode}"
    )


def test_bdd_5_changelog_unreleased_without_task_id_exit_1(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-5（BDD-4 反例）：`[Unreleased]` 段**不含** task_id ⇒ `check-changelog.py` exit 1。"""
    repo = git_repo.path
    (repo / "CHANGELOG.md").write_text(
        "## [Unreleased]\n- 其他任务条目\n", encoding="utf-8"
    )
    result = run_cli(
        python_exe, str(agate_scripts / "check-changelog.py"), "TAG9001", cwd=str(repo)
    )
    assert result.returncode == 1, (
        f"BDD-5：`[Unreleased]` 缺 task_id 应 exit 1，实际 rc={result.returncode}"
    )


# ── BDD-6/7：bump_type 意图字段（回归锁）────────────────────────────────────
def test_bdd_6_p8_gate_with_bump_type_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-6：P8 产出含 `bump_type: {major|minor|patch}` ⇒ exit 2。"""
    td = _write_task(tmp_path / "task", _P8_LEVEL1_BODY)
    result = _run_p8(td, agate_scripts, python_exe, run_cli, tmp_path)
    assert result.returncode == _P8_PASS_EXIT, (
        f"BDD-6：含 bump_type 时 P8 gate 应通过（rc={_P8_PASS_EXIT}），"
        f"实际 rc={result.returncode}"
    )


def test_bdd_7_p8_gate_missing_bump_type_exit_1(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-7（BDD-6 反例）：P8 产出**缺** `bump_type` ⇒ exit 1。"""
    body = (
        "---\n"
        "debt_check: none\n"
        "delivery:\n"
        "  method: release-notes\n"
        "  ref:\n"
        "    - CHANGELOG.md\n"
        "---\n\n"
        "# P8 交付收尾（fixture，无 bump_type）\n"
    )
    td = _write_task(tmp_path / "task", body)
    result = _run_p8(td, agate_scripts, python_exe, run_cli, tmp_path)
    assert result.returncode == 1, (
        f"BDD-7：缺 bump_type 时 P8 gate 应 exit 1，实际 rc={result.returncode}"
    )


# ── BDD-19：release.preset 声明层消费点与去 tag/version 后的 P8 语义一致 ───────
def test_bdd_19_no_dangling_config_migration_hint(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-19：基于已移除 version/tag 痕迹触发的「未声明 agate.config.yaml」迁移提示不再出现。

    Given 暂存区有 CHANGELOG 变更（会触发既有 version/tag 痕迹路径）、项目根无 agate.config.yaml
    When 运行 `check-gate.py P8`
    Then stderr 不含该迁移期提示（悬空提示）。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    td = _write_task(repo / "task", _P8_LEVEL1_BODY)
    (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n- TAG9001\n\n## [9.9.9] - 2026-10-11\n\n- x\n",
        encoding="utf-8",
    )
    git_repo.stage("CHANGELOG.md")

    result = _run_p8(td, agate_scripts, python_exe, run_cli, repo)
    assert "agate.config.yaml" not in result.stderr, (
        "BDD-19：P8 gate 仍发基于已移除 version/tag 痕迹的 agate.config.yaml 迁移提示"
        f"（悬空提示）——rc={result.returncode}"
    )


def test_bdd_19_gate_source_has_no_stale_preset_hint(agate_scripts):
    """BDD-19（静态面）：`check-gate.py` 不再含迁移期 preset 提示文案（悬空引用面）。

    该提示块的触发条件基于已移除的 version/tag 痕迹（P2-design M1 / 决策 6），须整体移除。
    """
    src = (agate_scripts / "check-gate.py").read_text(encoding="utf-8")
    assert "未发现项目声明 agate.config.yaml" not in src, (
        "BDD-19：check-gate.py 仍含基于 version/tag 痕迹的迁移期 preset 提示块"
    )
