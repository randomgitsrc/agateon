# agate/tests/unit/test_tag0050_obligation_behavior.py
# TAG0050 批 A4（G1-fix3 K2/K3）——M 义务的**真实行为凭证**。
#
# 背景：A4 原先把 60 条 M 义务的 `test` 全部指向一个只读 `obligations.yaml` 文本的参数化节点
# （`test_tag0050_obligations_enforcement.py::test_obligation_enforced[<id>]`）——那对「义务是否
# 真被执行」不敏感（删掉义务的**执行分支**它不转红），即「凭证自指」（评审 C1/cso F-2）。
#
# 本文件为**抽样**的 M 义务各写一个**真实行为用例**：加载 `enforced_at.file` 模块，构造违反
# 该义务的输入，调用 `enforced_at.function`，断言该义务被检出（返回失败码 + 特定消息）。
# 删掉义务对应的判断分支 → 本文件对应用例转红（负向控制由
# `test_tag0050_obligations.py::test_bdd_42_negative_control_mutation` 端到端验证：在协议根副本上
# 删分支 → 以 `AGATE_TEST_PROTOCOL_ROOT` 指向副本重跑本文件的用例 → 断言转红）。
#
# 设计 §2.9 明确允许「负向控制以 mutation 方式**抽样**执行」——本文件即抽样样本（覆盖 P1/P2/P8）。
# 未抽样的 M 义务仍由 `test_tag0050_obligations_enforcement.py` 承担「登记存在」辅助断言。
#
# 平台无关：tmp_path；不裸 python3；不写字面系统临时目录；文本 I/O 显式 utf-8。

import importlib.util
import os
import sys
from pathlib import Path

import pytest

# 协议根可经 AGATE_TEST_PROTOCOL_ROOT 覆盖（供负向控制在副本上运行本文件）。
_ENV_PROTOCOL_ROOT = "AGATE_TEST_PROTOCOL_ROOT"


def _protocol_root():
    env = os.environ.get(_ENV_PROTOCOL_ROOT)
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def _load_module(filename):
    """按路径加载协议脚本模块（文件名含连字符，不能直接 import）。"""
    scripts = _protocol_root() / "scripts"
    sp = str(scripts)
    if sp not in sys.path:
        sys.path.insert(0, sp)
    name = "obl_behavior_" + filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, str(scripts / filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.windows_smoke
def test_obl_p8_01_bump_type_missing_blocks(tmp_path, monkeypatch, capsys):
    """OBL-P8-01：P8-release.md 缺 bump_type 字段 → gate_p8 判失败。"""
    mod = _load_module("check-gate.py")
    monkeypatch.chdir(tmp_path)
    task = tmp_path / "TASK"
    _write(task / "P8-release.md", "debt_check: none\ndelivery: local\n")
    assert mod.gate_p8(str(task)) == 1
    assert "缺 bump_type 字段" in capsys.readouterr().err


def test_obl_p8_02_delivery_missing_blocks(tmp_path, monkeypatch, capsys):
    """OBL-P8-02：P8-release.md 缺 delivery 字段 → gate_p8 判失败（BDD-42 点名的义务）。"""
    mod = _load_module("check-gate.py")
    monkeypatch.chdir(tmp_path)
    task = tmp_path / "TASK"
    _write(task / "P8-release.md", "bump_type: patch\ndebt_check: none\n")
    assert mod.gate_p8(str(task)) == 1
    assert "缺 delivery 字段" in capsys.readouterr().err


def test_obl_p8_03_debt_check_missing_blocks(tmp_path, monkeypatch, capsys):
    """OBL-P8-03：P8-release.md 缺 debt_check 字段 → gate_p8 判失败。"""
    mod = _load_module("check-gate.py")
    monkeypatch.chdir(tmp_path)
    task = tmp_path / "TASK"
    _write(task / "P8-release.md", "bump_type: patch\ndelivery: local\n")
    assert mod.gate_p8(str(task)) == 1
    assert "缺 debt_check 字段" in capsys.readouterr().err


def test_obl_p1_10_vision_capability_missing_blocks(tmp_path, capsys):
    """OBL-P1-10：frontend 任务未声明 vision 能力条目 → `_gate_p1_vision_capability` 判失败。"""
    mod = _load_module("check-gate.py")
    p1 = tmp_path / "P1-requirements.md"
    _write(p1, "---\ndomains: frontend\n---\n#### BDD-1: x\n- Given a\n- When b\n- Then c\n")
    assert mod._gate_p1_vision_capability(str(p1)) is False
    assert "vision 能力条目" in capsys.readouterr().err


def test_obl_p2_07_ui_design_section_missing_blocks(tmp_path, capsys):
    """OBL-P2-07：ui_affected: true 但缺 UI 设计节 → `_gate_p2_ui_design_section` 判失败。"""
    mod = _load_module("check-gate.py")
    p2 = tmp_path / "P2-design.md"
    _write(p2, "---\nui_affected: true\n---\n## 方案\n正文\n")
    assert mod._gate_p2_ui_design_section(str(p2)) is False
    assert "缺 UI 设计" in capsys.readouterr().err


def test_obl_p2_10_dispatch_plan_invalid_mode_blocks(tmp_path):
    """OBL-P2-10：dispatch_plan.mode 非法 → `_gate_p2_dispatch_plan` 返回错误描述。"""
    mod = _load_module("check-gate.py")
    p2 = tmp_path / "P2-design.md"
    _write(p2, '---\ndispatch_plan: {"mode": "bogus"}\n---\n## 方案\n正文\n')
    err = mod._gate_p2_dispatch_plan(str(p2))
    assert err is not None and "mode" in err
