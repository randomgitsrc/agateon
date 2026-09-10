# tests/unit/test_tag0034_schema.py — TAG0034 派发路由 schema 静态校验器（BDD-1~6）
#
# 被测：agate/scripts/check-dispatch-routing.py <dispatch-routing.yaml 路径>
#   exit 0 = schema 合法 / exit 1 = schema 非法。
#
# TDD 红灯语义（P3）：check-dispatch-routing.py 尚未实现（P4a 建）。subprocess 运行触发
#   "can't open file"（python 返回码 2），全部 exit 0/1 断言失败 = 真实 B 类红灯
#   （子命令/脚本不存在，非 SyntaxError / 第三方 import 失败）。
#   与 test_check_events.py 的 "脚本未实现 → 返回码 2" 同款红灯范式。
#
# fixture：dispatch-routing.yaml 内容运行时构造（tmp_path 写 yaml 文本，不落 committed 夹具）。
# 平台无关：tmp_path fixture、python_exe fixture、显式 encoding="utf-8"，无裸解释器 / 无 /tmp。

import pytest


def _run_checker(agate_scripts, python_exe, run_cli, yaml_path):
    """check-dispatch-routing.py <yaml_path> 等价（合并流 result.output 断言）。"""
    return run_cli(
        python_exe, str(agate_scripts / "check-dispatch-routing.py"), str(yaml_path)
    )


def _write_yaml(tmp_path, text):
    p = tmp_path / "dispatch-routing.yaml"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.windows_smoke
def test_bdd_1_tier_effort_two_axes_accepted(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-1：tier + effort 两正交轴的任意组合（含便宜 tier + 高 effort / 顶配 tier + 低 effort）
    被 schema 校验器接受 → exit 0。"""
    y = _write_yaml(
        tmp_path,
        "schema_version: 1\n"
        "tier_bindings:\n"
        "  deep:\n"
        "    - {cli: codex, model: gpt-x, effort: low}\n"
        "  bulk:\n"
        "    - {cli: opencode, model: prov/m, effort: high}\n"
        "routes:\n"
        "  P2:\n"
        "    architect: {tier: deep, effort: high}\n"
        "  P4: {tier: bulk, effort: low}\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 0


@pytest.mark.windows_smoke
def test_bdd_2_tier_candidates_mutually_exclusive(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-2：同一 (phase,role) 条目同时写 tier: 与 candidates: → exit 1（互斥）。"""
    y = _write_yaml(
        tmp_path,
        "routes:\n"
        "  P2:\n"
        "    architect:\n"
        "      tier: deep\n"
        "      candidates:\n"
        "        - {cli: codex, model: gpt-x}\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 1


@pytest.mark.windows_smoke
def test_bdd_3_phase_role_key_optional(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-3：配置同时含 P4:（phase 级）与 P4.review:（(phase,role) 级）两种 key 形态 → exit 0
    （role 段可省略，两形态都合法识别）。"""
    y = _write_yaml(
        tmp_path,
        "tier_bindings:\n"
        "  deep:\n"
        "    - {cli: codex, model: gpt-x}\n"
        "routes:\n"
        "  P4: {tier: deep}\n"
        "  P4.review: {tier: deep}\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 0


@pytest.mark.windows_smoke
def test_bdd_4_invalid_cli_rejected(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-4：候选写 cli: gpt-4（不在 {native, claude-code, codex, opencode}）→ exit 1。"""
    y = _write_yaml(
        tmp_path,
        "routes:\n"
        "  P6.5:\n"
        "    judge:\n"
        "      candidates:\n"
        "        - {cli: gpt-4, model: whatever}\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 1


@pytest.mark.windows_smoke
def test_bdd_5_invalid_effort_rejected(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-5：候选写 effort: turbo（不在 {low, medium, high}）→ exit 1。"""
    y = _write_yaml(
        tmp_path,
        "routes:\n"
        "  P4:\n"
        "    implementer:\n"
        "      candidates:\n"
        "        - {cli: codex, model: gpt-x, effort: turbo}\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 1


@pytest.mark.windows_smoke
def test_bdd_6_fallback_field_illegal(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-6：任意层出现 fallback: <值> → exit 1（schema 无 fallback 字段——终点回落恒为
    默认派发、不可配、不需声明）。"""
    y = _write_yaml(
        tmp_path,
        "routes:\n"
        "  P4:\n"
        "    implementer:\n"
        "      tier: deep\n"
        "      fallback: standard\n",
    )
    result = _run_checker(agate_scripts, python_exe, run_cli, y)
    assert result.returncode == 1
