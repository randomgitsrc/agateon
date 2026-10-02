# tests/unit/test_check_scope_resolved.py — SCOPE+ 处理追踪
# （check-scope-resolved.bats 10 用例迁移，TAG0011 批次 6c）
# 被测：agate/scripts/check-scope-resolved.py（TASK_DIR；exit 0 = 通过 / exit 1 = SCOPE+ 未处理 /
#   exit 2 = 无 task 目录）。
# task_dir 等价 create_task_dir；add_p1_field 等价 fixtures.bash helper（frontmatter 块写入）。
# 流语义：GATE SCOPE 消息一律 sys.stderr.write → 按 P2 §3.2 先判流归属，
#   本文件断言一律用合并流 result.output（与 bats $output 等价，BLOCKER-1）。
# create_python_shim_bin 退役（P2 §3.1）：pytest 直跑解释器，无需 harness shim。

import pytest

from conftest import add_p1_field


def _run_scope(agate_scripts, python_exe, run_cli, task_arg):
    return run_cli(
        python_exe,
        str(agate_scripts / "check-scope-resolved.py"),
        task_arg,
    )


@pytest.mark.windows_smoke
def test_sc_1_nonexistent_task_dir_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    d = tmp_path / "nonexistent-task"

    result = _run_scope(agate_scripts, python_exe, run_cli, str(d))
    assert result.returncode == 2


def test_sc_2_no_scope_plus_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n正常文档，无 SCOPE+ 标记\n", encoding="utf-8")

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_3_scope_plus_no_p1_file_exit_1(tmp_path, agate_scripts, python_exe, run_cli):
    d = tmp_path / "task"
    d.mkdir()
    (d / "P2-design.md").write_text("# P2 design\n[SCOPE+] 新增功能\n", encoding="utf-8")

    result = _run_scope(agate_scripts, python_exe, run_cli, str(d))
    assert result.returncode == 1
    assert "无 P1-requirements.md" in result.output


def test_p2_53_progress_file_excluded_from_scope_scan(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir(phases=["P0", "P1", "P2", "P4", "P5", "P6", "P7", "P8"])
    (td / "P2-progress.md").write_text(
        "## P2 progress\n- [SCOPE+] 检查: 无新增隐含需求\n",
        encoding="utf-8",
    )
    p1 = td / "P1-requirements.md"
    p1.write_text(
        p1.read_text(encoding="utf-8") + "- [SCOPE_RESOLVED] test\n",
        encoding="utf-8",
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_dp1_dispatch_prompt_excluded_from_scope_scan(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P4-dispatch-prompt-implementer.md").write_text(
        "> render product\n- [SCOPE+] this should be ignored\n",
        encoding="utf-8",
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_4_scope_plus_no_resolved_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n[SCOPE+] 新增功能\n", encoding="utf-8")

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 1
    assert "SCOPE_RESOLVED" in result.output


def test_sc_5_scope_plus_with_resolved_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n[SCOPE+] 新增功能\n", encoding="utf-8")
    p1 = td / "P1-requirements.md"
    p1.write_text(
        p1.read_text(encoding="utf-8") + "\n[SCOPE_RESOLVED] 已纳入 v0.7\n",
        encoding="utf-8",
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_bdd22_1_scope_plus_frontmatter_scope_resolved_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n[SCOPE+] 新增功能\n", encoding="utf-8")
    add_p1_field(td, "scope_resolved", "[新增功能已纳入 v0.7]")

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_6_dispatch_context_excluded_from_scope_scan(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P4-dispatch-context-implementer.md").write_text(
        "---\n"
        "phase: P4\n"
        "task_id: T001\n"
        "role: implementer\n"
        "---\n"
        "\n"
        "<dispatch_guide>\n"
        "### 约束\n"
        "如果发现需求与设计矛盾，标 [SCOPE+] 而非直接做\n"
        "</dispatch_guide>\n",
        encoding="utf-8",
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_7_inline_scope_plus_not_line_start_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n检查了 [SCOPE+] 的引用情况\n", encoding="utf-8")

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


# --- SCOPE+ 行首包裹形态（RM-AG0077⑦ 遗留项的 hotfix，2026-10-01）-----------
# 背景：SCOPE_PLUS_RE 原只认 `^\s*-?\s*\[SCOPE+\]`，粗体 `**[SCOPE+]**` 与引用
# `> [SCOPE+]` 均不命中 → scope_found 空 → exit 0 早退，SCOPE_RESOLVED 校验被静默跳过。
# 关键约束（RM-AG0077⑦ 实测教训）：**必须双侧协同**——只放宽 SCOPE_PLUS_RE 会让
# 「有 SCOPE+ 却查不到对应 SCOPE_RESOLVED」的任务假红（TAG0021 即此形态：其
# SCOPE_RESOLVED 用反引号包裹）。故 SCOPE_RESOLVED_RE 同时覆盖包裹形态。


def test_sc_8_bold_wrapped_scope_plus_detected_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """粗体 `**[SCOPE+]**`（TPV0099 P2-design.md:120 的真实形态）须被检出；
    检出后无 SCOPE_RESOLVED → exit 1（修复前为 exit 0 静默早退）。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n- **[SCOPE+] 新增隐含需求**：需改 check-gate.py\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 1
    assert "SCOPE_RESOLVED" in result.output


def test_sc_9_quote_wrapped_scope_plus_detected_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    """引用块 `> [SCOPE+]` 须被检出（且不再输出 SKIP）。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n> [SCOPE+] 依赖版本变更带来的额外改造\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 1
    assert "GATE SKIP" not in result.output


def test_sc_10_bold_wrapped_with_bold_resolved_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """双侧协同：粗体 SCOPE+ 配粗体 SCOPE_RESOLVED → 通过（非假红）。"""
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n**[SCOPE+] 新增**\n", encoding="utf-8")
    p1 = td / "P1-requirements.md"
    p1.write_text(
        p1.read_text(encoding="utf-8") + "\n**[SCOPE_RESOLVED] 已纳入 v0.8**\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0
    assert "GATE SKIP" not in result.output


def test_sc_11_backtick_wrapped_resolved_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    """TAG0021 形态：SCOPE+ 行首、SCOPE_RESOLVED 反引号包裹 → 必须通过。
    此用例是「单侧放宽会造成假红」的回归锁。"""
    td = task_dir()
    (td / "P2-design.md").write_text("# P2 design\n**[SCOPE+] 新增**\n", encoding="utf-8")
    p1 = td / "P1-requirements.md"
    p1.write_text(
        p1.read_text(encoding="utf-8")
        + "\n`[SCOPE_RESOLVED: 锚点表追加 2 条纯数据登记，无检查逻辑改动]`\n",
        encoding="utf-8",
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0


def test_sc_12_prose_mention_still_not_detected(task_dir, agate_scripts, python_exe, run_cli):
    """反向护栏：prose 提及（行中有字）仍不得被检出——避免把「提及」当「声明」
    （RM-AG0077⑦ 实测：行内任意位置匹配会命中 27 个任务且抽样全为误报）。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n本节讨论 [SCOPE+] 标记的处置合规性，未新增范围外需求。\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0
    assert "GATE SKIP" in result.output


def test_sc_13_backtick_wrapped_plus_is_mention_not_declaration(
    task_dir, agate_scripts, python_exe, run_cli
):
    """反向护栏：反引号包裹的 `[SCOPE+]` 是**引述**而非声明，不检出。

    存量证据：`TAG0033` 等属「`` `[SCOPE+]` ``：**无**」这类确定性否定陈述。
    ⚠️ **`TAG0025` 不属此类**：其 `P4-implementation.md:80` 虽是**视觉行首**（第 0 字节为反引号，
    `od -c` 复核），但它是上一句的**折行续行**，语义上属句中引述——**形态判据无法区分
    「折行导致的视觉行首」与真正的行首声明**，这正是本边界保守的原因（设计说明 §3.2）。
    另有真声明反例 `TAG0004:50`（行首反引号 + 肯定陈述），代价已在设计说明 §3.2 登记。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n- `[SCOPE+]`：无。本批未发现范围外需求。\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0
    assert "GATE SKIP" in result.output


def test_sc_14_two_scripts_scope_plus_regex_identical(agate_scripts):
    """同源守护（DEBT0046「两处判据相反」同族的预防）：`check-scope-resolved.py` 与
    `check-retrospective.py` 各自持有 SCOPE_PLUS_RE，若只改一处，两个脚本会对
    「什么算 SCOPE+ 声明」给出**相反结论**——本用例把两处绑成同一判据。

    判据是**行为等价**（对一组探针输入分类一致），不是源码字符串相同——
    源码可以一个用拼接常量、一个用字面量，只要判定一致即无缺陷；
    反过来，字符串相同但语义不同的写法不该被判为通过。"""
    import importlib.util

    def _load(script_name, mod_name):
        spec = importlib.util.spec_from_file_location(mod_name, agate_scripts / script_name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.SCOPE_PLUS_RE

    rx_scope = _load("check-scope-resolved.py", "_sc_probe")
    rx_retro = _load("check-retrospective.py", "_rt_probe")

    # 探针覆盖：声明形态（应命中）、提及形态（不应命中）、边界
    probes = [
        "[SCOPE+] 裸",
        "- [SCOPE+] 列表符",
        "* [SCOPE+] 星号列表",
        "+ [SCOPE+] 加号列表",
        "> [SCOPE+] 引用块",
        "- **[SCOPE+] 粗体**",
        "**[SCOPE+] 粗体行首",
        "__[SCOPE+] 下划线粗体",
        "  - [SCOPE+] 缩进",
        "本节讨论 [SCOPE+] 的处置",  # 行中提及 → 不命中
        "- `[SCOPE+]`：无",           # 反引号引述 → 不命中
        "检查了 [SCOPE+] 的引用情况",   # 行中 → 不命中
        "无 SCOPE+ 标记",             # 无方括号 → 不命中
        "[SCOPE_GAP] 另一标记",       # 不同标记 → 不命中
    ]
    for p in probes:
        assert bool(rx_scope.search(p)) == bool(rx_retro.search(p)), (
            f"两个脚本对同一输入判定相反（SCOPE_PLUS_RE 已漂移）: {p!r} "
            f"scope={bool(rx_scope.search(p))} retro={bool(rx_retro.search(p))}"
        )


def test_sc_15_heading_form_is_deliberate_exclusion(task_dir, agate_scripts, python_exe, run_cli):
    """**刻意不覆盖**标题形态（2026-10-01 决策，非遗漏）：标题多为「容器」——`## N. [SCOPE+] 声明`
    的正文常是「无新增隐含需求」（`TAG0012:402`/`TAG0014:302`）。纳入会新增 4 个任务转红
    （行首 + 可选 `N.` 编号口径；若放宽成「标题行内任意位置」则 6 个，但那与「行中出现判为提及」冲突）。

    本用例把该决策**锁成判据**：若将来有人放宽 `_SCOPE_LEAD` 覆盖标题，此用例转红，
    强制其同时更新设计说明 §3.1 的未覆盖面登记与存量对账。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n## 8. [SCOPE+] 声明\n\n无新增隐含需求。\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0
    assert "GATE SKIP" in result.output, "标题形态应被刻意排除（容器标题，正文是否定）"


def test_sc_16_line_start_backtick_is_deliberate_exclusion(task_dir, agate_scripts, python_exe, run_cli):
    """**刻意不覆盖**行首反引号 `` - `[SCOPE+]` ``（2026-10-01 决策，非遗漏）。

    ⚠️ 该形态**存在真声明反例**（`TAG0004/P4-implementation-group1.md:50`），故这是**有代价的取舍**
    而非「一律是引述」：纳入会新增 5 个任务转红（1 真声明 : 4 引述/否定）。
    代价已在设计说明 §3.2 与 `check-scope-resolved.py` 常量注释中如实登记。
    纳入该形态前须先更新那些登记并重跑存量对账。"""
    td = task_dir()
    (td / "P2-design.md").write_text(
        "# P2 design\n- `[SCOPE+]`：无。本批未发现范围外需求。\n", encoding="utf-8"
    )

    result = _run_scope(agate_scripts, python_exe, run_cli, str(td))
    assert result.returncode == 0
    assert "GATE SKIP" in result.output
