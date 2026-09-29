# tests/unit/test_check_skip_announcements.py — 校验器「跳过」必须可辨识
# （RM-AG0077 子批 A，2026-09-29）
#
# 缺陷形态：多个 check 脚本在**其校验对象缺席**时静默 `sys.exit(0)` —— 退出码与
# 「已校验且通过」**完全相同**，输出也是空的。于是"没查"被读成"查过了没问题"。
# TPV0099 实证被误读一次：主 Agent 把 `check-scope-resolved.py` 的 exit 0 引为
# 「SCOPE+ 已闭环」的证据，被 P7 reviewer 用四状态矩阵推翻（该 0 是真空通过）。
#
# 本组测试**行为级**验证：触发各脚本的跳过场景 → stderr 须含 `GATE SKIP:` + 原因，
# 且退出码仍为 0（语义不变，只让「跳过」可辨识）。
#
# 口径说明（避免夸大）：先前登记的「13 个脚本 / 11 处」是**脚本级启发式**计数，
# 把辅助函数（如 `_count_lines`、`_staged_source_count`）的 `return 0` 也算在内。
# 精确口径 = **CLI 级、对象缺席即静默 exit 0** 的站点：本文件覆盖其中的 6 个脚本。


import pytest


def _assert_skip(result, script):
    assert result.returncode == 0, f"{script} 退出码应仍为 0：{result.output[:300]}"
    assert "GATE SKIP:" in result.stderr, (
        f"{script} 跳过时未声明原因（stderr 为空 ⇒ 与「已通过」不可区分）：{result.output[:300]}"
    )


def test_scope_resolved_announces_skip_when_no_scope_plus(python_exe, run_cli, agate_scripts, tmp_path):
    """未检出 [SCOPE+] → 须声明「校验未执行」（TPV0099 被误读的那一处）。"""
    task = tmp_path / "T1"
    task.mkdir()
    (task / "P1-requirements.md").write_text("---\nphase: P1\n---\n# r\n", encoding="utf-8")
    (task / "P2-design.md").write_text("# d\n无标记\n", encoding="utf-8")
    result = run_cli(python_exe, str(agate_scripts / "check-scope-resolved.py"), str(task))
    _assert_skip(result, "check-scope-resolved")


def test_routing_announces_skip_when_ceremony_absent(python_exe, run_cli, agate_scripts, tmp_path):
    """P1 未声明 ceremony → 须声明「按 standard、未做路由校验」。"""
    task = tmp_path / "T2"
    task.mkdir()
    (task / "P1-requirements.md").write_text("---\nphase: P1\n---\n# r\n", encoding="utf-8")
    result = run_cli(python_exe, str(agate_scripts / "check-routing.py"), str(task))
    _assert_skip(result, "check-routing")


def test_changelog_announces_skip_when_file_absent(python_exe, run_cli, agate_scripts, tmp_path):
    """CHANGELOG 不存在 → 须声明「未校验」。"""
    result = run_cli(
        python_exe, str(agate_scripts / "check-changelog.py"), "TAG9999",
        cwd=str(tmp_path), env={"CHANGELOG_FILE": "CHANGELOG.md"},
    )
    _assert_skip(result, "check-changelog")


def test_debt_keeps_documented_silence_for_absent_registry(
    python_exe, run_cli, agate_scripts, tmp_path
):
    """**例外**：check-debt FILE 模式对「文件不存在」保持静默——BDD-10 明文契约。

    BDD-10 规定「无文件 / 空文件 / 旧格式纯正文 → exit 0 **无输出**」为向后兼容契约
    （存量项目可能尚无 debt 文件）。故本脚本**不适用**「跳过须声明」的通则——此处显式
    记录该例外，避免日后被误当作漏改。
    代价（已知局限，登记于 RM-AG0077）：登记簿路径配错时无人察觉；是否收紧属显式决策。
    """
    result = run_cli(
        python_exe, str(agate_scripts / "check-debt.py"),
        str(tmp_path / "nope.md"),
    )
    assert result.returncode == 0
    assert result.output == "", f"BDD-10 契约要求静默：{result.output[:200]}"


def test_debt_retreat_coverage_announces_skip(python_exe, run_cli, agate_scripts, git_repo):
    """`--retreat-coverage` 模式**须**声明跳过（「无 retreat 提交」≠「全部已登记」）。

    与上一条的区别：该模式未被 BDD-10 覆盖（BDD-10 只讲 FILE 模式），而"没有 retreat
    提交可查"与"所有 retreat 都已登记"在退出码上不可区分 ⇒ 属真空通过。
    """
    result = run_cli(
        python_exe, str(agate_scripts / "check-debt.py"), "--retreat-coverage",
        cwd=str(git_repo.path),
    )
    assert result.returncode == 0, result.output[:300]
    assert "GATE SKIP:" in result.stderr, f"未声明跳过：{result.output[:200]}"


def test_p6_format_announces_skip_when_target_absent(python_exe, run_cli, agate_scripts, tmp_path):
    """目标文件不存在 → 须声明「未校验」。"""
    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-format.py"), "--check",
        str(tmp_path / "nope.md"),
    )
    _assert_skip(result, "check-p6-format")


def test_p6_format_announces_skip_when_wrong_basename(python_exe, run_cli, agate_scripts, tmp_path):
    """目标不是 P6-acceptance.md → 须声明「未校验」。"""
    other = tmp_path / "P2-design.md"
    other.write_text("# not the target\n", encoding="utf-8")
    result = run_cli(
        python_exe, str(agate_scripts / "check-p6-format.py"), "--check", str(other),
    )
    _assert_skip(result, "check-p6-format")


def test_state_transition_announces_skip_when_state_not_staged(
    python_exe, run_cli, agate_scripts, tmp_path
):
    """暂存区无该 .state.yaml → 须声明「未校验」（此前静默 fail-open）。"""
    task = tmp_path / "T3"
    task.mkdir()
    (task / ".state.yaml").write_text("task_id: TAG9999\nphase: P1\nstatus: active\n", encoding="utf-8")
    # 不加 git / 不暂存 → 脚本走「暂存区无该文件」或「git 不可用」分支，两者都应声明
    result = run_cli(python_exe, str(agate_scripts / "check-state-transition.py"), cwd=str(task))
    _assert_skip(result, "check-state-transition")


def test_skip_marker_is_absent_on_a_real_pass(python_exe, run_cli, agate_scripts, tmp_path):
    """负向对照：真通过时**不应**出现 `GATE SKIP:`（防"到处乱报跳过"）。

    routing 在 ceremony=standard 时走「更保守声明合法」的正常通过分支。
    """
    task = tmp_path / "T4"
    task.mkdir()
    (task / "P1-requirements.md").write_text(
        "---\nphase: P1\nceremony: standard\n---\n# r\n", encoding="utf-8"
    )
    result = run_cli(python_exe, str(agate_scripts / "check-routing.py"), str(task))
    assert result.returncode == 0
    assert "GATE SKIP:" not in result.stderr, f"正常通过却报了跳过：{result.stderr[:200]}"


# ---- roadmap 列数异常行：告警而非静默跳过（RM-AG0077⑥）----
#
# `_check_roadmap_done`（RM-AG0043，P8 roadmap done 反查）对列数 ≠ 9 的行整行
# `continue`，而"无匹配行 → 返回 None → 不误拦" ⇒ 该行的反查**静默失效**、零输出。
# 实测两例长期隐形：RM-AG0056（11 列）、RM-AG0059（12 列）——单元格里写了字面 `|`，
# 而 `\|` 转义对 `split("|")` 无效。此处断言「有告警 + 不改变阻断语义」。

_ROADMAP_HEADER = (
    "| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |\n"
    "|----|------|------|------|----------|------|------|\n"
)


def test_roadmap_malformed_row_warns_but_does_not_block(python_exe, run_cli, agate_scripts, tmp_path):
    """列数异常的 RM 行 → 须告警（此前静默），且**不得**因此阻断（BDD-6 不误拦）。"""
    code = (
        "import sys; sys.path.insert(0, {scripts!r});"
        "import importlib.util as u;"
        "spec = u.spec_from_file_location('cg', {gate!r});"
        "m = u.module_from_spec(spec); spec.loader.exec_module(m);"
        "print(m._check_roadmap_done('TAG0038', {rm!r}))"
    ).format(
        scripts=str(agate_scripts),
        gate=str(agate_scripts / "check-gate.py"),
        rm=str(tmp_path / "roadmap.md"),
    )
    # 该行含字面 `|` ⇒ split 后 11 列（≠9）；task_id 落在错位列上，故反查不到
    (tmp_path / "roadmap.md").write_text(
        _ROADMAP_HEADER
        + "| RM-AG9999 | 标题含 | 竖线 | done | 来源 | TAG0038 | 2026-01-01 | 2026-01-01 |\n",
        encoding="utf-8",
    )
    result = run_cli(python_exe, "-c", code)
    assert result.returncode == 0, result.output[:400]
    assert "列数异常" in result.stderr, f"未告警：{result.output[:300]}"
    assert result.stdout.strip() == "None", f"不应因此阻断：{result.stdout[:120]}"


def test_roadmap_wellformed_row_has_no_warning(python_exe, run_cli, agate_scripts, tmp_path):
    """负向对照：格式正确的 roadmap 不得产生列数告警（防误报）。"""
    code = (
        "import sys; sys.path.insert(0, {scripts!r});"
        "import importlib.util as u;"
        "spec = u.spec_from_file_location('cg', {gate!r});"
        "m = u.module_from_spec(spec); spec.loader.exec_module(m);"
        "print(m._check_roadmap_done('TAG0038', {rm!r}))"
    ).format(
        scripts=str(agate_scripts),
        gate=str(agate_scripts / "check-gate.py"),
        rm=str(tmp_path / "roadmap.md"),
    )
    (tmp_path / "roadmap.md").write_text(
        _ROADMAP_HEADER
        + "| RM-AG9999 | 标题 | backlog | 来源 | TAG0038 | 2026-01-01 | 2026-01-01 |\n",
        encoding="utf-8",
    )
    result = run_cli(python_exe, "-c", code)
    assert result.returncode == 0
    assert "列数异常" not in result.stderr, f"误报：{result.stderr[:200]}"
    assert result.stdout.strip() == "('RM-AG9999', 'backlog')"


# ---- 覆盖面补全（RM-AG0077 子批 A 独立评审后的逃逸站点，2026-09-29）----
#
# 独立评审指出子批 A 的覆盖与自设验收锚「跳过分支**均**输出显式原因」冲突：
# 至少 3 个可达的静默站点未处理。改用**统一探测**（空任务目录 = 所有校验对象缺席）
# 重扫全部 `check-*.py` 后，实际发现 9 个静默站点，本组覆盖其中 6 个；
# 余下 3 个是**有正当理由的例外**（见文件末注释）。


@pytest.mark.parametrize(
    "script,arg_kind",
    [
        ("check-frontmatter.py", "missing_file"),
        ("check-p6-evidence.py", "empty_dir"),
        ("check-p6-provenance.py", "empty_dir"),
        ("check-pruning.py", "empty_dir"),
        ("check-routing.py", "empty_dir"),
        ("check-state-yaml.py", "missing_state"),
    ],
)
def test_coverage_gap_scripts_announce_skip(
    python_exe, run_cli, agate_scripts, tmp_path, script, arg_kind
):
    """空任务目录（所有校验对象缺席）下，这 6 个脚本须声明跳过而非静默。

    `check-p6-provenance.py` 尤其重要：它位于 `agate-next.py` 的 **P6→P7 推进路径**上，
    此前「无 P6-acceptance.md → exit 0 且零输出」与「已审计且通过」不可区分。
    """
    if arg_kind == "missing_file":
        arg = str(tmp_path / "nope.md")
    elif arg_kind == "missing_state":
        arg = str(tmp_path / "nope-state.yaml")
    else:
        arg = str(tmp_path)  # 空目录
    result = run_cli(python_exe, str(agate_scripts / script), arg)
    assert "GATE SKIP:" in result.stderr, (
        f"{script} 对象缺席时未声明跳过（stderr 空 ⇒ 与「已通过」不可区分）：{result.output[:250]}"
    )


# 余下 3 个静默站点**有意不改**（已识别、有正当理由，非遗漏）：
#   check-debt.py                 —— BDD-10 明文契约「无文件 → exit 0 无输出」（见上文用例）
#   check-platform-assumptions.py —— 对**存在的空目录**扫描 0 个文件 = 正确通过（非「跳过」）；
#                                    目标不存在时它**有** FATAL 输出（stderr 非空）
#   check-retrospective.py        —— advisory 型检查（只产出建议、非门槛）；「无复盘文件」
#                                    与「无建议」语义一致，不构成误导
