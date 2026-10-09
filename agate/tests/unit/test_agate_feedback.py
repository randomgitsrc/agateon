# tests/unit/test_agate_feedback.py — agate-feedback.py 提取/匿名化/开关/不自动提交（TAG0015 新增）
# 覆盖 P1-requirements.md BDD-17（结构化提取）/BDD-18（匿名化）/BDD-19（AGATE_FEEDBACK 开关默认
# off）/BDD-20（不自动提交，产出待人工提交内容）。
# 被测：agate/scripts/agate-feedback.py（P4 implementer 新增，本阶段尚不存在——脚本本身缺失即是
# 预期红灯，见 P2-design.md §1.1 类 4.7 / dispatch-context 约束 1b）。
# 测试口径：CLI subprocess 调用（与 test_check_retrospective.py 风格一致），不 import 被测脚本为
# Python 模块（脚本是独立 CLI 工具，非 import 契约）。BDD-20 的"不调用 git push/gh"用静态源码
# grep 断言（脚本尚不存在时 Path.read_text() 抛 FileNotFoundError，属预期的项目内文件缺失红灯）。
# fixture：复盘文档样例内联构造（BDD-6/BDD-7 格式），不依赖真实存在的
# retrospective-template.md（P4 才会产出，见 dispatch-context 上游关联第二条）。

import re


def _retro_fixture(tmp_path, mechanism_text="gate 脚本未处理并发写入冲突"):
    """构造一份符合 BDD-6（frontmatter 机器字段）+ BDD-7（## agate 反馈 节）的复盘样例文档。"""
    content = (
        "---\n"
        "phase: P8\n"
        "task_id: T001\n"
        "mechanism_issues:\n"
        f'  - "{mechanism_text}"\n'
        "execution_issues:\n"
        '  - "复盘撰写时漏填技术债编号"\n'
        "feedback_ready: true\n"
        "---\n\n"
        "# T001 复盘\n\n"
        "## agate 反馈\n\n"
        f"归因到机制缺口的问题：{mechanism_text}。\n"
    )
    path = tmp_path / "retrospective.md"
    path.write_text(content, encoding="utf-8")
    return path


def _run_feedback(agate_scripts, python_exe, run_cli, *args, env=None):
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-feedback.py"),
        *args,
        env=env,
    )


# ── BDD-17：结构化提取（依赖 BDD-6/BDD-7 输入） ──────────────────────────────


def test_bdd17_extracts_mechanism_issues_from_frontmatter_and_section(
    tmp_path, agate_scripts, python_exe, run_cli
):
    retro = _retro_fixture(tmp_path)

    result = _run_feedback(
        agate_scripts,
        python_exe,
        run_cli,
        str(retro),
        "--format",
        "json",
        env={"AGATE_FEEDBACK": "on"},
    )

    assert result.returncode == 0
    assert "mechanism_issues" in result.stdout
    assert "gate 脚本未处理并发写入冲突" in result.stdout


# ── BDD-18：匿名化（项目名占位符化 + 绝对路径截断/移除） ──────────────────────


def test_bdd18_anonymize_project_name_replaced_with_placeholder(
    tmp_path, agate_scripts, python_exe, run_cli
):
    retro = _retro_fixture(
        tmp_path, mechanism_text="MySecretProject 的 gate 脚本处理有缺陷"
    )

    result = _run_feedback(
        agate_scripts,
        python_exe,
        run_cli,
        str(retro),
        "--format",
        "json",
        "--project-name",
        "MySecretProject",
        env={"AGATE_FEEDBACK": "on"},
    )

    assert result.returncode == 0
    assert "MySecretProject" not in result.stdout
    assert "<PROJECT>" in result.stdout


def test_bdd18_anonymize_absolute_path_removed_or_relativized(
    tmp_path, agate_scripts, python_exe, run_cli
):
    retro = _retro_fixture(
        tmp_path,
        mechanism_text="/home/otheruser/.secret-tool/config.json 里硬编码了路径",
    )

    result = _run_feedback(
        agate_scripts,
        python_exe,
        run_cli,
        str(retro),
        "--format",
        "json",
        env={"AGATE_FEEDBACK": "on"},
    )

    assert result.returncode == 0
    assert "/home/otheruser/.secret-tool/config.json" not in result.stdout
    assert "<PATH>" in result.stdout


# ── BDD-19：AGATE_FEEDBACK 开关默认 off（未设置 / 显式 off 均不产出） ─────────


def test_bdd19_env_unset_produces_no_output_and_disabled_message(
    tmp_path, agate_scripts, python_exe, run_cli
):
    retro = _retro_fixture(tmp_path)

    result = _run_feedback(agate_scripts, python_exe, run_cli, str(retro))

    assert result.returncode == 2
    assert "未启用" in result.output
    assert result.stdout == ""


def test_bdd19_env_explicit_off_produces_no_output_and_disabled_message(
    tmp_path, agate_scripts, python_exe, run_cli
):
    retro = _retro_fixture(tmp_path)

    result = _run_feedback(
        agate_scripts, python_exe, run_cli, str(retro), env={"AGATE_FEEDBACK": "off"}
    )

    assert result.returncode == 2
    assert "未启用" in result.output
    assert result.stdout == ""


# ── BDD-20：触发方式与产出边界（不调用 git push / gh，产出待人工提交内容） ────


def test_bdd20_source_contains_no_network_submit_calls(agate_scripts):
    script = agate_scripts / "agate-feedback.py"
    assert script.is_file(), "agate-feedback.py 尚未实现（P4 职责，P3 预期红灯）"
    source = script.read_text(encoding="utf-8")

    assert "git push" not in source
    assert re.search(r"\bgh\s", source) is None
    # subprocess 允许用于本地脚本间调用（如 agate-md-field-get.py，ADR-007 单一双读工具），
    # 但不得出现任何 git/gh 网络提交子命令字符串（重试#1 断言订正，见
    # P4-dispatch-context-implementer.md「重试 #1」节 2）。
    assert not re.search(r"subprocess\.\w+\(\s*\[[^\]]*\b(git|gh)\b", source)


def test_bdd20_stdout_contains_markdown_issue_body_snippet(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """产出物含面向 issue/PR 的 Markdown 文本片段（供人工手动提交），非自动提交动作。"""
    retro = _retro_fixture(tmp_path)

    result = _run_feedback(
        agate_scripts,
        python_exe,
        run_cli,
        str(retro),
        "--format",
        "markdown",
        env={"AGATE_FEEDBACK": "on"},
    )

    assert result.returncode == 0
    assert "#" in result.stdout  # Markdown 标题标记，标志"待提交文本片段"已生成
    assert "gate 脚本未处理并发写入冲突" in result.stdout


# ── RM-AG0082 / DEBT0008：绝对路径正则收窄（中文斜杠词不误伤）────────────────


def _retro_section_fixture(tmp_path, section_text):
    """构造只把文本放进「## agate 反馈」正文的复盘样例。

    避开 YAML 双引号转义（`C:\\Users\\...` 在 YAML 双引号标量里会被当 `\\U` 转义序列
    解析报错），使反斜杠路径可安全承载。
    """
    content = (
        "---\n"
        "phase: P8\n"
        "task_id: T001\n"
        "mechanism_issues: []\n"
        "execution_issues: []\n"
        "feedback_ready: true\n"
        "---\n\n"
        "# T001 复盘\n\n"
        "## agate 反馈\n\n"
        f"{section_text}\n"
    )
    path = tmp_path / "retrospective.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_rm_ag0082_chinese_slash_word_not_anonymized(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """中文斜杠分隔词 `机制/执行层面` 不得被当绝对路径脱敏（原正则 → `/执行层面`）。"""
    retro = _retro_fixture(tmp_path, mechanism_text="机制/执行层面 存在边界问题")

    result = _run_feedback(
        agate_scripts,
        python_exe,
        run_cli,
        str(retro),
        "--format",
        "markdown",
        env={"AGATE_FEEDBACK": "on"},
    )

    assert result.returncode == 0
    assert "机制/执行层面" in result.stdout
    assert "<PATH>" not in result.stdout


def test_rm_ag0082_real_absolute_paths_still_anonymized(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """真实敏感路径仍须脱敏：Unix 已知顶层 / 通用 ≥2 段（首段 ASCII）/ Windows 盘符。

    注意：**不得在源码里写 `/tmp` 字面量**（`check-platform-assumptions.py` R4 会命中，
    打破 `test_t42_scan_is_runnable_and_clean_on_repo`）——故临时目录用例运行时拼接。
    """
    for abs_path in (
        "/home/alice/proj/secret",
        str(tmp_path / "x" / "y"),  # 临时目录用例由 fixture 派生（不写字面量，见 docstring）
        "/data/secret",  # 未知顶层 + 恰好 2 段（SELF-GATE 评审指出：收窄过头会漏脱敏）
        r"C:\Users\bob\p",
    ):
        retro = _retro_section_fixture(tmp_path, f"泄露路径 {abs_path} 需处理")

        result = _run_feedback(
            agate_scripts,
            python_exe,
            run_cli,
            str(retro),
            "--format",
            "markdown",
            env={"AGATE_FEEDBACK": "on"},
        )

        assert result.returncode == 0, result.output
        assert abs_path not in result.stdout, abs_path
        assert "<PATH>" in result.stdout, abs_path
