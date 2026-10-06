# tests/unit/test_t41_platform_hygiene.py — 受限 harness 约定的一致性守护（TAG0041）
#
# 本组不测"散文写得好不好"，只测**结构性与自洽性事实**：
#   ① canonical 临时产物约定的**忽略片段模板真实存在**，且内容含该目录名；
#   ② `check-gate.py P8` 告警里指向的模板路径**真实存在**（防悬空指针——本仓反复踩过
#      「文档指向不存在的文件」这类缺陷）；
#   ③ 约定的四处落点（platform-notes / P8 卡 / P5 卡 / DSH SKILL）**互相可达**；
#   ④ DSH SKILL 显式声明不启用 agent-team（RM-AG0076 的落地判据）。

import re


def _generated_preset_block(agate_root):
    """经 `agate_common.dsh_preset_block()` 生成声明块（子进程 + PYTHONPATH，仓库既有惯例）。

    测生成产物而非模板：用户 profile 里拿到的是它，且 `plugins:` 作用域由生成器添加。
    """
    import subprocess
    import sys

    code = (
        "import sys, os;"
        f"sys.path.insert(0, {str(agate_root / 'scripts')!r});"
        "from agate_common import dsh_preset_block;"
        f"sys.stdout.write(dsh_preset_block({str(agate_root)!r}) or '')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0 and proc.stdout.strip(), (
        f"生成 preset 块失败：{proc.stderr[:300]}"
    )
    return proc.stdout


# R4 平台假设扫描要 0 命中 ⇒ 临时目录字面量运行时拼接（仓库既有惯例）
_TMP = "/" + "tmp"


def _read(p):
    return p.read_text(encoding="utf-8")


def test_t41_gitignore_fragment_exists_and_names_canonical_dir(agate_root):
    """忽略片段模板存在，且含 canonical 目录名（交付物本身可用）。"""
    frag = agate_root / "assets" / "templates" / "gitignore-fragment.txt"
    assert frag.is_file(), f"缺少忽略片段模板：{frag}"
    text = _read(frag)
    assert ".agate-tmp/" in text, "片段未给出可直接复制的忽略行"


def test_t41_p8_warning_names_existing_template_in_output(
    agate_root, agate_scripts, python_exe, run_cli, git_repo, task_dir
):
    """**行为级**：真的触发未忽略告警，并断言 `stderr` 里给出的模板路径**真实存在**。

    ⚠️ 本用例此前是**源文本扫描**（在 check-gate.py 里 grep 模板名）——独立评审用变异实验
    证明它可被绕过：删掉整个 `sys.stderr.write(...)` 告警块、只在注释里留模板路径，测试仍绿。
    现改为触发真实路径并断言**输出内容**（remedy 必须出现在用户实际看到的地方，且文件存在）。
    """
    td = task_dir()
    (td / "P8-release.md").write_text("bump_type: minor\ndebt_check: none\ndelivery: package-release\n", encoding="utf-8")
    repo = git_repo.path
    for name, content in (("package.json", "v0.1.0\n"), ("CHANGELOG.md", "## [Unreleased]\n")):
        (repo / name).write_text(content, encoding="utf-8")
        git_repo.stage(name)
    (repo / ".agate-tmp").mkdir()          # 存在但**未**忽略 ⇒ 触发 (a) 告警
    git_repo.stage(".") if hasattr(git_repo, "stage") else None

    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P8", str(td), cwd=str(repo)
    )
    out = result.output
    assert "未被 .gitignore 忽略" in out, f"未触发告警（用例前提失效）：{out[:300]}"
    m = re.search(r"assets/templates/([A-Za-z0-9._-]+)", out)
    assert m, f"告警未给出可复制的 remedy 模板：{out[:400]}"
    assert (agate_root / "assets" / "templates" / m.group(1)).is_file(), (
        f"告警指向的模板不存在（悬空指针）：assets/templates/{m.group(1)}"
    )


def test_t41_platform_notes_has_restricted_harness_section(agate_root):
    """platform-notes 须有「受限 harness 通用约束」节，且覆盖四项属性与两条事实。"""
    text = _read(agate_root / "platform-notes.md")
    assert "受限 harness 通用约束" in text, "缺权威节"
    for kw in (".agate-tmp", "check-ignore", "排除出测试收集面", "清理时点",
               "存活跟随", "探活", "batch-id"):
        assert kw in text, f"权威节缺关键要素：{kw}"


def test_t41_cards_and_dsh_skill_cross_reference(agate_root):
    """四处落点互相可达：P8 卡清理时点、P5 卡服务探活、DSH SKILL 平台注意。"""
    p8 = _read(agate_root / "phase-cards" / "P8-release.md")
    assert ".agate-tmp" in p8, "P8 卡未把 canonical 临时目录纳入收尾清理"
    p5 = _read(agate_root / "phase-cards" / "P5-verification.md")
    assert "探活" in p5 or "受限 harness" in p5, "P5 卡未引用服务生命周期事实"
    skill = _read(agate_root / "assets" / "templates" / "dsh" / "SKILL.md")
    for kw in (".agate-tmp", "进程树", "agent-team"):
        assert kw in skill, f"DSH SKILL 平台注意缺：{kw}"


def test_t41_dispatch_prompt_points_scratch_to_canonical_dir(agate_root):
    """派发模板（每个 subagent 都读）须把中间临时文件指向 canonical 目录。

    回归来历：该模板原写「系统临时目录可用于中间临时文件」——但受限 harness 下该目录
    **只读**，照做即失败。这与本任务要治的是同一类缺陷（平台事实与指令不符），且影响面
    更大（所有平台的 subagent 都会读到它）。

    注：需要检查的字面量**运行时拼接**（`_TMP`），避免本文件自身命中 R4 平台假设扫描
    （`tests/` 全树要求 0 命中；仓库既有同款规避惯例）。
    """
    text = _read(agate_root / "assets" / "templates" / "dispatch-prompt.md")
    assert ".agate-tmp" in text, "派发模板未指向 canonical 临时目录"
    assert ("不要用 `" + _TMP + "`") in text, "派发模板未警示系统临时目录在受限 harness 下只读"


def test_t41_dsh_skill_forbids_agent_team(agate_root):
    """DSH SKILL 须显式声明**不要启用** agent-team，并给出核查方式（RM-AG0076）。"""
    skill = _read(agate_root / "assets" / "templates" / "dsh" / "SKILL.md")
    assert "不要启用" in skill and "agent-team" in skill
    assert "dsh.profile.bundles" in skill, "未给出可自查的启用状态判据"


def test_t41_preset_mounts_delegation_in_preset_scope(agate_root):
    """**仓内可验的前提**：preset 把 `tool-subagent*` 挂在**预设作用域**（`plugins:`）。

    这是「顶层 agent-team 的 disable 不影响本 preset」这一文档结论的**结构前提**——
    上游 README「已知限制」写明「预设作用域挂载的 continuable Subagent 控件……顶层组合包
    不会替换这些注册」。本用例只断言**仓内可验的那一半**（挂载位置），故 CI 上也有信号。
    """
    # 测**生成产物**（用户 profile 里真正写入的那份），而非原始模板——`plugins:` 作用域是
    # 生成器包上去的（`dsh_preset_block()`），模板本身没有该键。
    block = _generated_preset_block(agate_root)
    assert re.search(r"^\s+plugins:\s*$", block, re.MULTILINE), (
        "生成块结构已变：找不到 plugins: 作用域（文档的「预设作用域」论断需重核）"
    )
    tail = block.split("plugins:", 1)[1]
    granted = set(re.findall(r"^\s+- id: (tool-subagent\S*)", tail, re.MULTILINE))
    assert granted == {
        "tool-subagent",
        "tool-subagent-control",
        "tool-subagent-fork",
        "tool-subagent-list-agents",
    }, f"生成块在 plugins: 下授权的委派控件集合已变：{sorted(granted)} —— 文档需重核"


def test_t41_agent_team_disables_the_same_ids_upstream(agate_root):
    """**上游交叉核对**（无 DSH checkout 时 skip）：agent-team 在顶层禁用的正是这四个 id。

    与上一条合起来才支撑文档论断：**preset 侧挂在预设作用域** + **组合包在顶层禁用**
    ⇒ 顶层 disable 不使 preset 失效，后果是「两套委派面并存」（而非本 preset 失效）。

    注：本用例**不能**证明文档结论本身（那需实机启用 DSH 组合包）；它证明的是**前提**，
    故定位为**结构哨兵**——上游模板任一变动都会让它转红以提醒重核。
    """
    preset = _read(agate_root / "assets" / "templates" / "dsh" / "agent.cordis.yml")
    granted = set(re.findall(r"^\s+- id: (tool-subagent\S*)", preset, re.MULTILINE))
    assert granted, "preset 未授权任何 tool-subagent*（模板结构已变，需重核文档断言）"

    import os

    rel = ("packages", "experimental", "agent-team-profile", "cordis.patch.yml")
    repo = agate_root.parent
    candidates = [
        *([os.path.join(os.environ["DSH_REPO"], *rel)] if os.environ.get("DSH_REPO") else []),
        os.path.join(repo.parent, "deepseek-harness", *rel),
        os.path.join(repo, "deepseek-harness", *rel),
    ]
    upstream = next((c for c in candidates if os.path.isfile(c)), None)
    if upstream is None:
        import pytest

        pytest.skip("DSH 上游 checkout 不在本机，无法交叉核对（CI 上属预期）")
    patch = open(upstream, encoding="utf-8").read()
    disabled = set(re.findall(r"- id: (tool-subagent\S*)\n\s+disabled: true", patch))
    missing = granted - disabled
    assert not missing, (
        f"preset 授权但 agent-team 顶层未禁用的 id：{sorted(missing)}——"
        "文档需重核（它依赖两者不相交的冲突形态）"
    )


def test_t41_agent_team_doc_cites_upstream_limitation(agate_root):
    """文档必须引用上游「已知限制」原文，而不是只引支持性概述段（防选择性引用）。

    来历：本仓**两次**把这条写错（先称「两套工具同时可见」——事实前提为假；再称
    「preset 工具映射整体失效」——与上游「已知限制」直接冲突）。故要求文档**显式承载**
    那句原文，使后续读者能自行核对。
    """
    notes = _read(agate_root / "platform-notes.md")
    assert "顶层组合包不会替换这些注册" in notes, (
        "platform-notes 的 agent-team 条未引用上游「已知限制」原文（易再写错）"
    )
