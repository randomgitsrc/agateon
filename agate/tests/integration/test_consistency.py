# tests/integration/test_consistency.py — 跑 check-protocol-consistency.py + 锚点表
# （integration/consistency.bats 11 用例迁移，TAG0011 批次 14）
# 被测：agate/scripts/check-protocol-consistency.py（CHECK 1-9 输出）+ 锚点脚本内容断言。
# bats setup() 每测试跑一次脚本；pytest 用 module 级 fixture 跑一次（结果确定性，行为等价）。
# 合并流：CommandResult.output = stdout + stderr（等价 bats $output，P2 §3.2 BLOCKER-1）。
# windows_smoke：CON.1（文件首 @test）+ CON.3（名称含"编码"，P3 §5.2 平台关键词）。

import pytest

from conftest import _run_cli_impl


@pytest.fixture(scope="module")
def consistency_result(python_exe, agate_scripts, agate_root):
    """等价 bats setup()：跑一致性脚本，--root 显式指向仓库根（= agate_root.parent）。"""
    return _run_cli_impl(
        python_exe,
        str(agate_scripts / "check-protocol-consistency.py"),
        "--root",
        str(agate_root.parent),
    )


@pytest.mark.windows_smoke
def test_con_1_check_1_yaml_parseable(consistency_result):
    """CON.1：CHECK 1 YAML 代码块可解析 → 无 ERROR 块。"""
    assert "ERROR (" not in consistency_result.output


def test_con_2_check_2_internal_refs_exist(consistency_result):
    """CON.2：CHECK 2 文件引用存在 → 非 FAIL。"""
    assert "FAIL  CHECK 2" not in consistency_result.output


@pytest.mark.windows_smoke
def test_con_3_check_3_no_hardcoded_line_refs(consistency_result):
    """CON.3：CHECK 3 无硬编码行号 → PASS。"""
    assert "PASS  CHECK 3" in consistency_result.output


def test_con_4_check_4_gate_commands_keys_consistent(consistency_result):
    """CON.4：CHECK 4 gate_commands 键集合一致 → PASS。"""
    assert "PASS  CHECK 4" in consistency_result.output


def test_con_5_check_6_license_ownership(consistency_result):
    """CON.5：CHECK 6 LICENSE 归属 → PASS。"""
    assert "PASS  CHECK 6" in consistency_result.output


def test_con_6_check_7_version_badge_sync(consistency_result):
    """CON.6：CHECK 7 version badge 同步 → PASS。"""
    assert "PASS  CHECK 7" in consistency_result.output


def test_con_8_check_9_script_structure_alignment(consistency_result):
    """CON.8：CHECK 9 协议-脚本结构对齐（含新增 check-frontmatter.sh 锚点，37→38）。

    md5 去重的 WARN 是已知的（文档声称 hook 强制但脚本未实现）；
    只要有 PASS/WARN 就说明锚点表在跑，不要求全 PASS。
    """
    assert "PASS  CHECK 9" in consistency_result.output or "WARN  CHECK 9" in consistency_result.output
    assert "FAIL  CHECK 9" not in consistency_result.output


def test_con_9_check_9_md5_dedup_anchor_implemented(agate_scripts):
    """CON.9：check-p6-evidence.py 已实现 md5 去重（_md5_entries + md5sum）。

    锁住"已实现"（commit 949055c 后缺口消失，断言改写为锁定实现存在）。
    """
    text = (agate_scripts / "check-p6-evidence.py").read_text(encoding="utf-8")
    assert "_md5_entries" in text
    assert "md5sum" in text


def test_con_10_check_8_v06_keywords_exist(consistency_result):
    """CON.10：CHECK 8 v0.6 关键词存在性 → PASS。"""
    assert "PASS  CHECK 8" in consistency_result.output


def test_con_11_check_9_prod_touched_anchor(agate_scripts):
    """CON.11：pre-commit-gate.sh 含 PROD_NOT_TOUCHED 锚点。"""
    text = (agate_scripts / "pre-commit-gate.sh").read_text(encoding="utf-8")
    assert "PROD_NOT_TOUCHED" in text


def test_con_12_check_9_need_confirm_three_value_anchor(agate_scripts):
    """CON.12：check-gate.py 含 NEED_CONFIRM 三值锚点（v0.30.2 起 SUGGEST）。"""
    text = (agate_scripts / "check-gate.py").read_text(encoding="utf-8")
    assert "NO_NEED_CONFIRM" in text
    assert "SUGGEST" in text
