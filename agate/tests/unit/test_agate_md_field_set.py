# tests/unit/test_agate_md_field_set.py — 结构化字段写入工具（TAG0024 P3，RM-AG0048 一期）
# 被测（P4 才新建，本文件当前必须全红）：
#   - agate/scripts/agate-md-field-set.py           （frontmatter 字段写入，FILE 环境变量传路径，
#                                                      与 agate-md-field-get.py 同惯例——P2-design §3.1 pseudocode）
#   - agate/scripts/agate-md-field-set-gate-commands.py（正文 gate_commands YAML 块写入，
#                                                      FILE 位置参数——P2-design.md §3.3 CLI 用法行原样引用：
#                                                      "agate-md-field-set-gate-commands.py FILE <yaml块或@文件路径>"）
#
# 覆盖 P1-requirements.md BDD-1~19（RM-AG0048 一期，1:1 映射）。
#
# 白盒测试的接口假设（P4 实现须提供，均有 P2-design.md 明文依据，非杜撰）：
#   - agate-md-field-set.py 顶层 `def main():`（本仓库全部 CLI 脚本的既定约定，见
#     agate-md-field-get.py / check-routing.py）+ 顶层 `import os`（供 monkeypatch os.replace）
#   - `_writable_keys(rules_root)` 函数与 `GENERIC_HEADER_KEYS` 常量：P2-design.md §3.1 伪代码
#     原样给出的函数名/常量名，非本测试文件发明
#
# 红灯性质：两个脚本文件当前均不存在——CLI 用例经 subprocess 调用会因"文件不存在"
# （python3: can't open file ...）非 0 退出；白盒用例经 importlib.spec_from_file_location +
# exec_module 会在 exec_module 阶段抛 FileNotFoundError（B 类：被测模块未实现，非 A 类语法错误）。

import importlib.util
import re
import sys

import pytest

SCRIPT_SET = "agate-md-field-set.py"
SCRIPT_SET_GC = "agate-md-field-set-gate-commands.py"


# ---------- 通用 helper（黑盒 CLI 调用，风格对齐 test_agate_md_field_get.py） ----------


def _run_set(agate_scripts, python_exe, run_cli, args, md_file, extra_env=None):
    """调 agate-md-field-set.py（FILE env 传路径，与 md-field-get 同惯例）。"""
    env = {"FILE": str(md_file)}
    if extra_env:
        env.update(extra_env)
    return run_cli(
        python_exe,
        str(agate_scripts / SCRIPT_SET),
        *args,
        env=env,
    )


def _run_set_gc(agate_scripts, python_exe, run_cli, md_file, yaml_block):
    """调 agate-md-field-set-gate-commands.py（FILE 位置参数，见 P2-design.md §3.3 用法行）。"""
    return run_cli(
        python_exe,
        str(agate_scripts / SCRIPT_SET_GC),
        str(md_file),
        yaml_block,
    )


def _run_get(agate_scripts, python_exe, run_cli, op, md_file):
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-md-field-get.py"),
        op,
        env={"FILE": str(md_file)},
    )


# ---------- 白盒 helper（importlib 动态加载，BDD-10/15/17 需要访问内部对象） ----------


def _load_module(agate_scripts, script_name, module_name):
    """importlib 加载带连字符文件名的脚本（同 check-routing.py._load_script 惯例）。

    被测脚本不存在时，spec_from_file_location 本身不报错（只是构造 spec），
    真正的 FileNotFoundError 在 exec_module 阶段抛出——这正是本批次期望的真红灯。
    """
    path = agate_scripts / f"{script_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_agate_common(agate_scripts):
    scripts_str = str(agate_scripts)
    if scripts_str not in sys.path:
        sys.path.insert(0, scripts_str)
    import agate_common

    return agate_common


def _call_main_expect_exit(mod, monkeypatch, argv, env):
    """统一调用 mod.main() 并取到退出码（兼容 sys.exit() 内部调用 / return code 两种约定）。"""
    monkeypatch.setattr(sys, "argv", argv)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    try:
        code = mod.main()
    except SystemExit as e:
        code = e.code
    return code


# ================= BDD-1: 合法 key/value 写入成功且可被读回 + gate 通过 =================


def test_bdd_1_valid_key_value_roundtrip_and_gate_pass(
    agate_scripts, python_exe, run_cli, task_dir
):
    """BDD-1：写入 packages（P2 最后一个待补字段）后 get 能读回，且 check-gate.py P2 不再
    因该字段被拦（gate_p2 正常路径终点返回 2 = 需主 Agent 自行判定 gate_commands，非 1 =
    阻断；用 != 1 断言"该字段相关检查通过"，避免对 check-gate.py 自身 0/2 语义做过度假设）。
    """
    td = task_dir(phases=["P1", "P2"])
    p2_file = td / "P2-design.md"
    p2_file.write_text(
        "---\n"
        "agent: test\n"
        "candidate_count: 2\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "---\n"
        "方案设计正文，选择理由如下：候选 A 更简单，权衡后选 A。\n\n"
        "gate_commands:\n"
        '  P3: "true"\n'
        '  P5: "true"\n',
        encoding="utf-8",
    )
    from conftest import add_p2_review

    add_p2_review(td, status="approved", agent="reviewer-subagent")

    result = _run_set(agate_scripts, python_exe, run_cli, ["packages", "agate-scripts other-pkg"], p2_file)
    assert result.returncode == 0

    get_result = _run_get(agate_scripts, python_exe, run_cli, "packages", p2_file)
    assert get_result.returncode == 0
    assert get_result.output.strip() == "agate-scripts other-pkg"

    gate_result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P2", str(td)
    )
    assert gate_result.returncode != 1, gate_result.output


# ================= BDD-2: 非法 key 被拒绝 =================


def test_bdd_2_invalid_key_rejected_lists_valid_keys(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "P1-requirements.md"
    md_file.write_text(
        "---\nagent: test\nrisk_level: medium\nphases: [P1]\npackages: [agate]\n"
        "domains: [backend]\n---\nbody\n",
        encoding="utf-8",
    )
    result = _run_set(agate_scripts, python_exe, run_cli, ["risks_level", "high"], md_file)
    assert result.returncode != 0
    # 合法 key 清单命中真实白名单成员（risk_level 是 phases.yaml P1 task_fields 之一）
    assert "risk_level" in result.output


# ================= BDD-3: 非法 value 被拒绝（枚举 + 归属角色 + 下一步） =================


def test_bdd_3_invalid_value_rejected_with_enum_role_and_suggestion(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "P2-review.md"
    md_file.write_text("---\nagent: reviewer-subagent\n---\nreview notes\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, ["status", "Approve"], md_file)
    assert result.returncode != 0
    assert re.search(r"approved", result.output)  # 合法值枚举
    assert re.search(r"review|评审|角色", result.output)  # 字段归属角色
    assert re.search(r"建议|请|见", result.output)  # 下一步建议


# ================= BDD-4: 角色越权写入被拒绝 =================


def test_bdd_4_role_unauthorized_write_rejected(agate_scripts, python_exe, run_cli, tmp_path):
    md_file = tmp_path / "P4-review.md"
    # implementer 属 execution-roles（非 review 角色），不在 assets/review-roles/ 清单内
    md_file.write_text("---\nagent: implementer\n---\nnotes\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, ["status", "approved"], md_file)
    assert result.returncode != 0
    assert re.search(r"角色|role", result.output, re.IGNORECASE)


# ================= BDD-5: --list 输出与阶段 schema 一致 =================


def test_bdd_5_list_matches_phase_task_fields(agate_scripts, python_exe, run_cli, task_dir):
    td = task_dir(phases=["P1", "P2"])
    p2_file = td / "P2-design.md"
    result = _run_set(agate_scripts, python_exe, run_cli, ["--list"], p2_file)
    assert result.returncode == 0
    # phases.yaml id:P2 task_fields = [candidate_count, packages, domains, ui_affected, gate_commands]
    for field in ("candidate_count", "packages", "domains", "ui_affected", "gate_commands"):
        assert field in result.output


# ================= BDD-6: 写入后报告剩余缺失 =================


def test_bdd_6_reports_remaining_missing_after_write(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "P2-design.md"
    md_file.write_text("---\nagent: test\n---\nbody\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, ["candidate_count", "2"], md_file)
    assert result.returncode == 0
    assert re.search(r"缺失", result.output)
    for field in ("packages", "domains", "ui_affected", "gate_commands"):
        assert field in result.output


# ================= BDD-7: gate_commands 正文块写入与解析 =================


def test_bdd_7_gate_commands_block_write_and_parse(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "P2-design.md"
    md_file.write_text("---\nagent: test\n---\n方案正文\n", encoding="utf-8")
    result = _run_set_gc(
        agate_scripts,
        python_exe,
        run_cli,
        md_file,
        '{P3: "pytest -q", P5: "pytest -q", P5_timeout_seconds: 120}',
    )
    assert result.returncode == 0

    agate_common = _load_agate_common(agate_scripts)
    new_text = md_file.read_text(encoding="utf-8")
    has_block, entries = agate_common.parse_gate_commands_block(new_text)
    assert has_block
    entries_dict = dict(entries)
    assert "pytest -q" in entries_dict.get("P3", "")
    assert "pytest -q" in entries_dict.get("P5", "")
    assert entries_dict.get("P5_timeout_seconds") is not None


# ================= BDD-8: gate_commands 非法块被拒绝 =================


@pytest.mark.parametrize(
    "yaml_block,offending_token",
    [
        pytest.param('{P9_custom: "pytest"}', "P9_custom", id="undeclared-phase-key"),
        pytest.param('{P3_timeout_seconds: "abc"}', "P3_timeout_seconds", id="non-integer-timeout"),
    ],
)
def test_bdd_8_gate_commands_invalid_block_rejected(
    agate_scripts, python_exe, run_cli, tmp_path, yaml_block, offending_token
):
    md_file = tmp_path / "P2-design.md"
    original = "---\nagent: test\n---\n方案正文\n"
    md_file.write_text(original, encoding="utf-8")
    result = _run_set_gc(agate_scripts, python_exe, run_cli, md_file, yaml_block)
    assert result.returncode != 0
    # 错误信息须点名具体非法 key（否则"随便一个非零退出+非空输出"的假红灯会永远绿，
    # 见本文件当前"can't open file"报错同样满足弱断言的教训）
    assert offending_token in result.output
    assert md_file.read_text(encoding="utf-8") == original  # 拒绝时不落盘


# ================= BDD-9: 证据字段一期拒绝写入 =================

_EVIDENCE_FIELD_TARGETS = {
    "pass": ("P6-acceptance.md", "1"),
    "fail": ("P6-acceptance.md", "0"),
    "regression_pass": ("P6-acceptance.md", "true"),
    "blocker_count": ("P7-consistency.md", "0"),
    "deviation_count": ("P7-consistency.md", "0"),
    "deviation_critical_count": ("P7-consistency.md", "0"),
    "design_gap_count": ("P7-consistency.md", "0"),
    "design_gap_reviewed_count": ("P7-consistency.md", "0"),
    "code_map_new_files_count": ("P7-consistency.md", "0"),
    "code_map_reviewed_count": ("P7-consistency.md", "0"),
}


@pytest.mark.parametrize("field", sorted(_EVIDENCE_FIELD_TARGETS.keys()))
def test_bdd_9_evidence_fields_rejected(agate_scripts, python_exe, run_cli, tmp_path, field):
    basename, value = _EVIDENCE_FIELD_TARGETS[field]
    md_file = tmp_path / basename
    md_file.write_text("---\nagent: test\n---\nbody\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, [field, value], md_file)
    assert result.returncode != 0
    assert re.search(r"验证脚本|不可手动填写", result.output)


# ================= BDD-10: 原子写，中断不落盘 =================


def test_bdd_10_atomic_write_interrupted_leaves_file_unchanged(
    agate_scripts, tmp_path, monkeypatch
):
    mod = _load_module(agate_scripts, "agate-md-field-set", "agate_md_field_set")
    md_file = tmp_path / "atomic-test.md"
    original = "---\nagent: test\nrisk_level: medium\n---\nbody\n"
    md_file.write_text(original, encoding="utf-8")

    def _boom(*_args, **_kwargs):
        raise OSError("simulated interruption mid-write")

    monkeypatch.setattr(mod.os, "replace", _boom)

    code = _call_main_expect_exit(
        mod,
        monkeypatch,
        [SCRIPT_SET, "risk_level", "high"],
        {"FILE": str(md_file)},
    )
    assert code not in (0, None)
    assert md_file.read_text(encoding="utf-8") == original


# ================= BDD-11: 文件不存在时拒绝 =================


def test_bdd_11_missing_file_rejected(agate_scripts, python_exe, run_cli, tmp_path):
    md_file = tmp_path / "does-not-exist.md"
    result = _run_set(agate_scripts, python_exe, run_cli, ["risk_level", "high"], md_file)
    assert result.returncode != 0
    assert "请先 Write 产出文件，再 set 字段" in result.output
    assert not md_file.exists()


# ================= BDD-12: 无 frontmatter 时插入且不破坏正文 =================


def test_bdd_12_inserts_frontmatter_preserves_body(agate_scripts, python_exe, run_cli, tmp_path):
    md_file = tmp_path / "legacy.md"
    original_body = "旧格式正文第一行\n第二行内容\n"
    md_file.write_text(original_body, encoding="utf-8")

    result = _run_set(agate_scripts, python_exe, run_cli, ["risk_level", "medium"], md_file)
    assert result.returncode == 0

    new_text = md_file.read_text(encoding="utf-8")
    assert new_text.startswith("---\n")
    assert new_text.endswith(original_body)


# ================= BDD-13: 正文残留旧字段时提示不删除 =================


def test_bdd_13_residual_body_field_warns_but_not_deleted(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "residual.md"
    residual_body = "risk_level: low\n其他正文内容\n"
    md_file.write_text(f"---\nagent: test\n---\n{residual_body}", encoding="utf-8")

    result = _run_set(agate_scripts, python_exe, run_cli, ["risk_level", "high"], md_file)
    assert result.returncode == 0
    assert re.search(r"残留", result.output)
    assert re.search(r"清理", result.output)
    assert "risk_level" in result.output

    new_text = md_file.read_text(encoding="utf-8")
    assert residual_body in new_text  # 正文残留原样保留，不被自动删除

    get_result = _run_get(agate_scripts, python_exe, run_cli, "risk_level", md_file)
    assert get_result.output.strip() == "high"  # frontmatter 优先生效


# ================= BDD-14: 生成的 frontmatter 通过 check-frontmatter.py =================


def test_bdd_14_generated_frontmatter_passes_check_frontmatter(
    agate_scripts, python_exe, run_cli, tmp_path
):
    md_file = tmp_path / "P2-design.md"
    md_file.write_text(
        "---\nagent: test\ncandidate_count: 2\ndomains: [backend]\nui_affected: false\n---\nbody\n",
        encoding="utf-8",
    )
    result = _run_set(agate_scripts, python_exe, run_cli, ["packages", "agate-scripts"], md_file)
    assert result.returncode == 0

    check_result = run_cli(
        python_exe,
        str(agate_scripts / "check-frontmatter.py"),
        str(md_file),
    )
    assert check_result.returncode == 0, check_result.output


# ================= BDD-15: set 校验与 check-gate.py（agate-frontmatter-check._check）同源 =================


@pytest.mark.parametrize(
    "candidate_count,should_reject",
    [
        pytest.param(0, True, id="invalid-below-min"),
        pytest.param(2, False, id="valid-above-min"),
    ],
)
def test_bdd_15_value_validation_same_source_as_check(
    agate_scripts, python_exe, run_cli, tmp_path, candidate_count, should_reject
):
    """不分别断言两次硬编码期望值：直接调用 agate-frontmatter-check.py 的真实 _check()，
    把它的返回结果作为 CLI 断言的输入，防止 set 与 gate 两边独立漂移仍各自通过。"""
    fm_check = _load_module(agate_scripts, "agate-frontmatter-check", "agate_frontmatter_check_direct")
    schema = fm_check.SCHEMAS["P2-design.md"]
    candidate_fm = {
        "candidate_count": candidate_count,
        "packages": [],
        "domains": [],
        "ui_affected": False,
    }
    expected_errors = fm_check._check("P2-design.md", schema, candidate_fm)
    candidate_count_errors = [e for e in expected_errors if e.startswith("P2-design.md:candidate_count:")]
    assert bool(candidate_count_errors) == should_reject  # 前提校验：真实 _check() 确实按预期分叉

    md_file = tmp_path / "P2-design.md"
    md_file.write_text("---\nagent: test\n---\nbody\n", encoding="utf-8")
    result = _run_set(
        agate_scripts, python_exe, run_cli, ["candidate_count", str(candidate_count)], md_file
    )

    if should_reject:
        assert result.returncode != 0
        assert candidate_count_errors[0] in result.output
    else:
        assert result.returncode == 0


# ================= BDD-16: 零协议知识 subagent 模拟场景 =================


def test_bdd_16_zero_protocol_knowledge_walkthrough_converges(
    agate_scripts, python_exe, run_cli, task_dir
):
    """模拟"只被告知 --list 看要填什么，照提示填"的序列：不预先注入协议知识——驱动逻辑
    本身不解析 --list 的具体排版（排版是 P4 才落定的实现细节，测试不应对其字面格式打赌），
    只依赖 phases.yaml 已声明的 P2 task_fields 名单（--list 承诺会展示的字段集，BDD-5 已
    锁定这一契约）逐项调用 set；真正验证"引导是否足够"的断言在最后：--list 收敛到无缺失
    + check-gate.py 不再因这些字段被拦。"""
    td = task_dir(phases=["P1", "P2"])
    p2_file = td / "P2-design.md"
    # fixture 数据前提：task_dir 生成的 P2-design.md 正文为空，不含 check-gate.py gate_p2()
    # 独立要求的"权衡/选择理由"正文散文关键词（与本条 BDD 验证的 set 工具字段写入逻辑无关，
    # 直接追加满足即可，不通过 set 工具写入——set 按设计不处理正文散文）。
    with p2_file.open("a", encoding="utf-8") as f:
        f.write("方案设计正文，选择理由如下：候选 A 更简单，权衡后选 A。\n")
    from conftest import add_p2_review

    add_p2_review(td, status="approved", agent="reviewer-subagent")

    # 模拟 agent 唯一知道的东西：BDD-5 已确认 --list 会展示的标量字段名 → 一个合法值
    # （zero-knowledge 体现在"不知道 value 该怎么校验"，靠 set 的写入即校验兜底，
    # 不体现在"连字段名单都要靠猜"——字段名单本身是 --list 的输出契约，非协议内部知识）。
    plausible_values = {
        "candidate_count": "2",
        "packages": "agate-scripts",
        "domains": "backend",
        "ui_affected": "false",
    }
    for field, value in plausible_values.items():
        write_result = _run_set(agate_scripts, python_exe, run_cli, [field, value], p2_file)
        assert write_result.returncode == 0, write_result.output

    # gate_commands 走专用子命令（body 块，非标量字段，--list 只报告其"是否已声明"）
    gc_result = _run_set_gc(agate_scripts, python_exe, run_cli, p2_file, '{P3: "true", P5: "true"}')
    assert gc_result.returncode == 0, gc_result.output

    final_list = _run_set(agate_scripts, python_exe, run_cli, ["--list"], p2_file)
    assert final_list.returncode == 0
    assert not re.search(r"剩余缺失", final_list.output)

    gate_result = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P2", str(td))
    assert gate_result.returncode != 1, gate_result.output


# ================= BDD-17: set 白名单 = task_fields ∪ 通用 Header 的完整并集 =================


def test_bdd_17_writable_keys_is_mechanical_union(agate_scripts):
    mod = _load_module(agate_scripts, "agate-md-field-set", "agate_md_field_set")
    agate_common = _load_agate_common(agate_scripts)

    rules_root = agate_common.resolve_rules_root(str(agate_scripts / "agate-md-field-set.py"))
    phases_data = agate_common.read_rules_yaml(rules_root, "phases") or {}
    expected_task_fields = set()
    for p in phases_data.get("phases", []) or []:
        expected_task_fields.update(p.get("task_fields") or [])

    # GENERIC_HEADER_KEYS 复用实现自身声明的常量（task-files.md 通用 Header 是纯 prose
    # 文档，无机器可读结构，此处不重抄字面清单，只验证并集计算逻辑本身）
    expected = set(mod.GENERIC_HEADER_KEYS) | expected_task_fields
    actual = mod._writable_keys(rules_root)

    assert actual == expected
    # 边界：命中（P8 task_fields 成员）
    assert "bump_type" in actual
    # 边界：不命中（不在并集内的任意生造 key）
    assert "totally_bogus_key_xyz_not_in_any_schema" not in actual


# ================= BDD-18: 追加/自由格式字段一期明确拒绝 =================

_APPEND_ONLY_TARGETS = {
    "need_confirm_resolved": "P1-requirements.md",
    "suggest_resolved": "P1-requirements.md",
    "scope_resolved": "P1-requirements.md",
    "mechanism_issues": "retrospective.md",
    "execution_issues": "retrospective.md",
    "dispatch_plan": "P2-design.md",
}


@pytest.mark.parametrize("field", sorted(_APPEND_ONLY_TARGETS.keys()))
def test_bdd_18_append_only_fields_rejected(agate_scripts, python_exe, run_cli, tmp_path, field):
    basename = _APPEND_ONLY_TARGETS[field]
    md_file = tmp_path / basename
    md_file.write_text("---\nagent: test\n---\nbody\n", encoding="utf-8")
    value = '{"mode": "single"}' if field == "dispatch_plan" else "描述文本"
    result = _run_set(agate_scripts, python_exe, run_cli, [field, value], md_file)
    assert result.returncode != 0
    assert re.search(r"追加|嵌套|暂不支持", result.output)


# ================= BDD-19: dispatch-context / dispatch-prompt 模板同步改为引导 set =================


def test_bdd_19_dispatch_templates_reference_set_tool_no_copyable_fence(agate_assets):
    prompt_text = (agate_assets / "templates" / "dispatch-prompt.md").read_text(encoding="utf-8")
    context_text = (agate_assets / "templates" / "dispatch-context.md").read_text(encoding="utf-8")

    assert "agate-md-field-set" in prompt_text
    assert "agate-md-field-set" in context_text

    # 旧的"直接复制"裸 frontmatter 围栏指引必须已被替换（当前仍存在，是本 BDD 的真红灯来源）
    assert "文件必须以这段 Header 开头（直接复制" not in prompt_text


def test_rm_ag0113_p3_agent_writable_by_tool(agate_scripts, python_exe, run_cli, tmp_path):
    """DEBT0041 关单回归（RM-AG0113 一并复核）：`P3-test-cases.md` 的 `agent` 可由
    `agate-md-field-set` **正常写入**——releaser 正常流程**无需手写 frontmatter**。

    该债原判据①即此场景；2026-10-09 实测：`set agent` 对 P3 rc=0 成功（TAG0050 批 B 已解除
    旧的 `writable - {"agent"}` 限制）。本用例锁定该行为，防再次回退。
    """
    md = tmp_path / "P3-test-cases.md"
    md.write_text(
        "---\nphase: P3\ntask_id: T001\ntype: test-cases\n---\n\n## 用例\n",
        encoding="utf-8",
    )
    result = _run_set(agate_scripts, python_exe, run_cli, ["agent", "test-designer"], md)
    assert result.returncode == 0, (
        f"P3-test-cases.md 的 agent 须可由工具写入（DEBT0041）；rc={result.returncode}\n"
        f"{result.output[-400:]}"
    )
    assert "agent: test-designer" in md.read_text(encoding="utf-8")
