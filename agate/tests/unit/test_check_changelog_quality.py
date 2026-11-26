# agate/tests/unit/test_check_changelog_quality.py
# RM-AG0117 —— CHANGELOG 条目「过程日志化」判据。
#
# 该判据的存在理由（不是自明的）：纯 WARNING 在本仓会被无视（`SELF-GATE.md` 自陈
# 「WARNING 不拦截……强制力依赖主 Agent 自觉」；同款纯 warning 机制复犯 6 次后才靠 CI
# 阻断级守卫收住）。存量证据：v0.78.0 段 248 行含 158 处过程痕迹、v0.77.0 段 191 行含 121 处，
# 均被人眼 review 放行 —— 故这里必须是**阻断级**判据。
#
# 本文件同时是「不误伤」的守护：v0.81.0 段 240 行但零过程痕迹（长是真的因为变更多），
# 它必须 PASS。若谁把词表放宽到裸「转红」/「自我更正」，这条会立刻转红。

import importlib.util

_SCRIPT = "agate-changelog-quality.py"


def _load(agate_scripts):
    spec = importlib.util.spec_from_file_location("ccq", agate_scripts / _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cli(agate_scripts, python_exe, run_cli, text, tmp_path):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(text, encoding="utf-8")
    return run_cli(python_exe, str(agate_scripts / _SCRIPT), str(f))


_PROCESS_LOG = """## [Unreleased]

### 修复

- **某缺陷**：第一版判断错了，独立评审用 registry 状态推翻。三轮独立评审共 3 份报告，
  我原先以为是 X。变异实验：加回即红。另加 5 组断言，31 passed。
  教训：以后要先核实。勘误：上一版写错了。
"""

_CLEAN = """## [Unreleased]

### 修复

- **某缺陷**（**需重跑接入**：`python3 ~/.agate/scripts/agate-setup.py`）：
  模板授权了已移除的子路径，DSH 0.2.2-rc.5 起该导出不存在 ⇒ 建会话会失败。已删除该行。
  详见 `agate/UPGRADING.md`。
"""


def test_clean_entry_passes(agate_scripts, python_exe, run_cli, tmp_path):
    """正常的变更条目必须 PASS（零误报是前提，否则判据会被绕过）。"""
    r = _cli(agate_scripts, python_exe, run_cli, _CLEAN, tmp_path)
    assert r.returncode == 0, f"干净条目被误判：{r.output[:500]}"


def test_process_log_is_blocked(agate_scripts, python_exe, run_cli, tmp_path):
    """工作过程记录必须 exit 1（阻断），且提示要指出该往哪挪。"""
    r = _cli(agate_scripts, python_exe, run_cli, _PROCESS_LOG, tmp_path)
    assert r.returncode == 1, f"过程日志未被拦：rc={r.returncode}\n{r.output[:500]}"
    assert "过程" in r.output and "commit message" in r.output, (
        f"提示须说明该内容应移到哪：{r.output[:600]}"
    )


def test_warn_only_returns_2(agate_scripts, python_exe, run_cli, tmp_path):
    """`--warn-only` 供本地试跑用：命中但不阻断（exit 2）。"""
    f = tmp_path / "CHANGELOG.md"
    f.write_text(_PROCESS_LOG, encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / _SCRIPT), "--warn-only", str(f))
    assert r.returncode == 2


def test_single_category_does_not_fire(agate_scripts, tmp_path):
    """单类反复出现不判 —— 那是写法习惯，不是「工作日志」的形态特征。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 教训：甲。教训：乙。教训：丙。教训：丁。\n"
    total, found, _ = mod.scan(text)
    assert total >= 3 and len(found) == 1
    f = tmp_path / "CHANGELOG.md"
    f.write_text(text, encoding="utf-8")
    assert mod.main.__call__  # 存在性；实际判定走下面
    # 单类 ⇒ 不 FIRE（需要 ≥2 类）
    assert not (total >= mod.FIRE_MIN_TOTAL and len(found) >= mod.FIRE_MIN_CATEGORIES)


def test_test_red_is_not_a_process_signal(agate_scripts):
    """裸「转红」不得计入 —— v0.81.0 实测误伤（「不得以会让测试转红为由回退」等 5 处）。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 设计要求：不得以「会让测试转红」为由回退；实测 35 个用例转红。\n"
    total, found, _ = mod.scan(text)
    assert total == 0, f"「转红」被误计为过程痕迹：{found}"


def test_audit_wording_self_correction_not_counted(agate_scripts):
    """裸「自我更正」不得计入 —— 可指「审计口径自我更正」（规格口径，非作者心态）。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 审计口径自我更正：首版按连字符匹配，改为按边界。\n"
    total, found, _ = mod.scan(text)
    assert total == 0, f"「自我更正」被误计：{found}"


def test_review_mention_stays_as_hint_only(agate_scripts):
    """「评审指出/发现」只进提示、不计数（否则会误伤「本版修复了独立评审发现的 X」）。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 修复了独立评审发现的状态泄漏问题。\n"
    total, found, hints = mod.scan(text)
    assert total == 0, f"正当的变更说明被计入：{found}"
    assert hints, "应作为提示出现，便于作者自查"


def test_only_unreleased_and_latest_release_are_scanned(agate_scripts):
    """只扫 `[Unreleased]` + 最新已发布段；更早的历史段不扫（存量零影响）。"""
    mod = _load(agate_scripts)
    text = (
        "## [Unreleased]\n\n- 正常条目。\n\n"
        "## [9.9.9] - 2026-01-01\n\n- 正常条目。\n\n"
        "## [9.9.8] - 2025-12-01\n\n- 教训：历史段。第一版写错了。三轮评审。31 passed。\n"
    )
    total, found, _ = mod.scan(text)
    assert total == 0, f"历史已发布段不应被扫：{found}"


def test_missing_changelog_is_not_an_error(agate_scripts, python_exe, run_cli, tmp_path):
    """无 CHANGELOG 时判据不适用（与 `check-changelog.py` 的 GATE SKIP 同取向）。"""
    r = run_cli(python_exe, str(agate_scripts / _SCRIPT), str(tmp_path / "nope.md"))
    assert r.returncode == 0


def test_pre_commit_mounts_quality_check_outside_state_loop(agate_root):
    """pre-commit 的 2z2 必须挂在 `for state_file in state_files:` **循环之外**。

    为什么（本仓已有先例事故）：循环体内的检查对「没有 `.state.yaml` 的提交」完全不生效
    —— 而 hotfix 通道正是这种提交，恰恰是本判据要拦的主战场。`2z`（技术债 schema）当初
    就因为放错位置而失效过（其注释已记明）。
    """
    lines = (agate_root / "scripts" / "pre-commit-gate.py").read_text(encoding="utf-8").splitlines()
    loop = next((i for i, ln in enumerate(lines) if "for state_file in state_files:" in ln), None)
    mount = next((i for i, ln in enumerate(lines) if "2z2." in ln), None)
    assert loop is not None and mount is not None, "找不到循环或挂载点"
    assert mount > loop, "2z2 必须放在 state_files 循环之外，否则 hotfix 提交不受检查"


def test_meta_discussion_of_the_rule_is_not_counted(agate_scripts):
    """**自指误伤**：描述判据本身时引用它的词表，不该被自己的词表命中。

    实测来源：RM-AG0117 自己那条变更说明写了「（第一人称、评审轮次、变异实验、`N passed`、
    自我勘误等 6 类）」——那是**引用**词表，不是作者在讲自己的过程，却命中 2 处。
    不修这里，判据会惩罚「解释判据」的正当文档（也很容易被用来「写不进去就换个说法」）。
    """
    mod = _load(agate_scripts)
    text = (
        "## [Unreleased]\n\n"
        "- 新增判据：命中「过程痕迹」（第一人称、变异实验、`N passed`、自我勘误等 6 类）即失败。\n"
    )
    total, found, _ = mod.scan(text)
    assert total == 0, f"谈论判据本身的句子被计入：{found}"


def test_code_fence_is_not_counted(agate_scripts):
    """围栏代码块里的示例不是作者叙述，不参与计数。"""
    mod = _load(agate_scripts)
    text = (
        "## [Unreleased]\n\n- 正常条目。\n\n"
        "```python\n# 教训：第一版判断错了，三轮评审，31 passed\n```\n"
    )
    total, found, _ = mod.scan(text)
    assert total == 0, f"代码块被计入：{found}"


def test_meta_keyword_cannot_be_used_to_bypass(agate_scripts):
    """**防绕过**：在坏条目里加「（判据）」二字，不得让该行豁免。

    实测来源：`_strip_non_prose()` 的早期版本用「行内含『判据/命中/词表』任一即整行剥离」，
    于是下面这行 `total` 从 **5 直接归零**（判据被一行注释绕过）。现收紧为「必须同时是
    元讨论句式」，本条锁定该收紧不被回退。
    """
    mod = _load(agate_scripts)
    base = "## [Unreleased]\n\n- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训\n"
    evil = "## [Unreleased]\n\n- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训（判据）\n"

    t_base, _f_base, _ = mod.scan(base)
    t_evil, f_evil, _ = mod.scan(evil)
    assert t_base >= mod.FIRE_MIN_TOTAL, f"前提：基线应超标，实际 {t_base}"
    assert t_evil >= mod.FIRE_MIN_TOTAL and len(f_evil) >= mod.FIRE_MIN_CATEGORIES, (
        f"加「（判据）」后仍须 FIRE —— 否则判据可被一行注释绕过（实测曾从 {t_base} 归零）。"
        f"实际 total={t_evil}, cats={len(f_evil)}"
    )
