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

_SCRIPT = "check-changelog-quality.py"


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
    total, found, _, _rel = mod.scan(text)
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
    total, found, _, _rel = mod.scan(text)
    assert total == 0, f"「转红」被误计为过程痕迹：{found}"


def test_audit_wording_self_correction_not_counted(agate_scripts):
    """裸「自我更正」不得计入 —— 可指「审计口径自我更正」（规格口径，非作者心态）。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 审计口径自我更正：首版按连字符匹配，改为按边界。\n"
    total, found, _, _rel = mod.scan(text)
    assert total == 0, f"「自我更正」被误计：{found}"


def test_review_mention_stays_as_hint_only(agate_scripts):
    """「评审指出/发现」只进提示、不计数（否则会误伤「本版修复了独立评审发现的 X」）。"""
    mod = _load(agate_scripts)
    text = "## [Unreleased]\n\n- 修复了独立评审发现的状态泄漏问题。\n"
    total, found, hints, _rel = mod.scan(text)
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
    total, found, _, _rel = mod.scan(text)
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


def test_meta_words_do_not_exempt_a_line(agate_scripts):
    """**防绕过（B-1）**：在坏条目里插「（阈值）/（自检）/（词表）…」不得让该行豁免。

    历史：曾用 `_META_DISCUSSION` 做「行内含某词即整行剥离」，被实测证伪——11 个词里
    **6 个**仍可绕过（加「（阈值）/（自检）/（词表）/（扫描面）/（误伤）/（本判据）」
    均使 total 5→0）。现已**整体移除**该机制，只剥围栏代码块。

    代价（接受）：作者若在变更说明里**列举**本判据词表，会被计入 → 正确做法是别在
    CHANGELOG 里复述词表（写「见判据脚本」）。把责任放在写法上，而不是开一个任意豁免口。
    """
    mod = _load(agate_scripts)
    for word in ("阈值", "自检", "词表", "扫描面", "误伤", "本判据", "判据", "命中"):
        txt = (
            "## [Unreleased]\n\n"
            f"- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训（{word}）\n"
        )
        total, found, _, _rel = mod.scan(txt)
        assert total >= mod.FIRE_MIN_TOTAL and len(found) >= mod.FIRE_MIN_CATEGORIES, (
            f"插「（{word}）」后仍须 FIRE——否则判据可被一个词绕过。"
            f"实际 total={total}, cats={len(found)}"
        )


def test_code_fence_is_not_counted(agate_scripts):
    """围栏代码块里的示例不是作者叙述，不参与计数。"""
    mod = _load(agate_scripts)
    text = (
        "## [Unreleased]\n\n- 正常条目。\n\n"
        "```python\n# 教训：第一版判断错了，三轮评审，31 passed\n```\n"
    )
    total, found, _, _rel = mod.scan(text)
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

    t_base, _f_base, _, _r1 = mod.scan(base)
    t_evil, f_evil, _, _r2 = mod.scan(evil)
    assert t_base >= mod.FIRE_MIN_TOTAL, f"前提：基线应超标，实际 {t_base}"
    assert t_evil >= mod.FIRE_MIN_TOTAL and len(f_evil) >= mod.FIRE_MIN_CATEGORIES, (
        f"加「（判据）」后仍须 FIRE —— 否则判据可被一行注释绕过（实测曾从 {t_base} 归零）。"
        f"实际 total={t_evil}, cats={len(f_evil)}"
    )


def test_legit_erratum_is_not_blocked(agate_scripts):
    """**B-2**：正当的「勘误：上一版的 X 写错了」不得被判为过程日志。

    实测来源：`A6` 含 `勘误` + `A7` 含 `上一版` 叠加 ⇒ 两条纯正当的勘误行 total=4/cats=2，
    端到端 pre-commit **rc=1 误阻断**。已把 `勘误` 移出 A6、`上一版(的|写)` 移出 A7。
    「勘误」本身是 CHANGELOG 的正当用法（在说**修了什么**）。
    """
    mod = _load(agate_scripts)
    txt = (
        "## [Unreleased]\n\n"
        "- 勘误：上一版的版本号写错了。\n"
        "- 勘误：上一版写错了命令名。\n"
    )
    total, found, _, _rel = mod.scan(txt)
    assert not (total >= mod.FIRE_MIN_TOTAL and len(found) >= mod.FIRE_MIN_CATEGORIES), (
        f"正当勘误被误判为过程日志：total={total}, cats={[c['category'] for c in found]}"
    )


def test_released_section_only_warns_never_blocks(agate_scripts, python_exe, run_cli, tmp_path):
    """**B-3**：`[Unreleased]` 干净、仅**已发布**段有过程痕迹 ⇒ 只提示（exit 2），不阻断。

    为什么：已发布段是历史快照（`doc-freshness-guide.md` §3「保留不动」）。对它硬阻断，
    唯一出路是改写历史——与那条既有纪律直接冲突，且会让「升级协议后第一次提交就被卡住」。
    """
    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        "## [Unreleased]\n\n- 正常条目。\n\n"
        "## [9.9.9] - 2026-01-01\n\n"
        "- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训。\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / _SCRIPT), str(f))
    assert r.returncode == 2, (
        f"已发布段命中应只提示（exit 2），不得阻断；实际 rc={r.returncode}\n{r.output[:400]}"
    )
    assert "不阻断" in r.output, f"须说明为何不阻断：{r.output[:400]}"


def test_unreleased_hit_blocks_even_if_released_also_hit(agate_scripts, python_exe, run_cli, tmp_path):
    """`[Unreleased]` 命中即阻断（exit 1），即使已发布段也命中。"""
    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        "## [Unreleased]\n\n"
        "- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训。\n\n"
        "## [9.9.9] - 2026-01-01\n\n- 正常条目。\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / _SCRIPT), str(f))
    assert r.returncode == 1, f"Unreleased 命中须阻断；实际 rc={r.returncode}"
