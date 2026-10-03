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


# --- CHECK 16 活文档数字漂移（2026-10-02）-------------------------------------
#
# 动机：数字漂移在本仓反复发作，根因是**它只有"约定"没有机械门禁**
# （`roadmap.md` 原话：`tests 计数 | ❌ 非机械门禁（约定）`）——约定不拦人。
# 实测代价：`agate/tests/README.md` 曾写死 68 行逐文件用例数，**30 行已漂移（44%）**。
#
# 两条规则（设计见 `docs/guides/doc-freshness-guide.md` §2/§2.1/§3）：
#   ① 测量声称须带**时态锚**（`@ <commit>` / `（实测于…）` / `（改动前…）` 等）；
#   ② 表格不得有**计数列**（表头含「用例数/条目数/总数…」且该列多为纯整数）。
# 范围 = 活文档（协议本体 + 开发指引 + 根文档）；记录类（tasks/reviews/blog/fixtures）**刻意不覆盖**。


def test_con_13_check_16_passes_on_current_tree(consistency_result):
    """CON.13：当前树上 CHECK 16 通过（0 误报——若误报，它会立刻变成需要长期对齐的噪音）。"""
    assert "PASS  CHECK 16" in consistency_result.output


def test_con_14_check_16_flags_count_column(python_exe, agate_scripts, agate_root, tmp_path):
    """CON.14：**计数列**被机械检出——在真实树上加回「用例数」列即应 ERROR。

    这是 68 行索引的**真实形状**回归锁：防它被重新加回。
    """
    import shutil

    root = tmp_path / "root"
    shutil.copytree(agate_root.parent, root, symlinks=True)
    readme = root / "agate" / "tests" / "README.md"
    text = readme.read_text(encoding="utf-8")
    # 注入：表头加计数列；并把**前 3 个数据行**补上第 3 列纯整数
    # （判据要求 ≥3 且 ≥60%，故 3 行即足够触发）
    text = text.replace(
        "| 脚本 | 测试文件 |\n|------|---------|",
        "| 脚本 | 测试文件 | 用例数 |\n|------|---------|-------|",
    )
    lines = text.splitlines()
    filled = 0
    for idx, ln in enumerate(lines):
        if filled >= 3:
            break
        if ln.startswith("|") and not ln.startswith("| 脚本") and not ln.startswith("|---") \
                and ln.count("|") == 3:          # 恰为两列的数据行
            lines[idx] = ln.rstrip() + " 29 |"   # 追加**新列**（原行以 | 结尾）
            filled += 1
    assert filled == 3, f"注入失败：只填充 {filled} 行"
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = _run_cli_impl(python_exe, str(agate_scripts / "check-protocol-consistency.py"),
                           "--root", str(root))
    assert "FAIL  CHECK 16" in result.output, result.output
    assert "计数列" in result.output, result.output


def test_con_15_check_16_flags_unanchored_measurement(python_exe, agate_scripts, agate_root, tmp_path):
    """CON.15：**缺时态锚的测量声称**被检出——移除锚即应 ERROR。

    这是 CHANGELOG `[Unreleased]` 的真实形状回归锁（该段是**混合文档**：
    已发布段是历史快照、Unreleased 段是活文档）。
    """
    import shutil

    root = tmp_path / "root2"
    shutil.copytree(agate_root.parent, root2 := root, symlinks=True)
    cl = root2 / "CHANGELOG.md"
    text = cl.read_text(encoding="utf-8")
    i = text.index("## [Unreleased]")
    j = text.index("\n## [", i + 5)
    section = text[i:j]
    for anchor in ("实测于", "改动前", "当时", "提交时", "@ ", "基线"):
        section = section.replace(anchor, "〔X〕")
    cl.write_text(text[:i] + section + text[j:], encoding="utf-8")
    result = _run_cli_impl(python_exe, str(agate_scripts / "check-protocol-consistency.py"),
                           "--root", str(root2))
    assert "FAIL  CHECK 16" in result.output, result.output
    assert "缺时态锚" in result.output, result.output


def test_con_16_check_16_scope_excludes_records(agate_scripts):
    """CON.16 范围断言：记录类目录**刻意不在**扫描面（广范围实测 59 处误报，全在记录类文件）。

    这是防"有人顺手把范围放宽"的护栏——放宽前必须先给记录类一个可机械判定的分类判据。
    """
    src = (agate_scripts / "check-protocol-consistency.py").read_text(encoding="utf-8")
    assert '_LIVE_DOC_DIRS = ("agate/", "docs/guides/", "docs/brand/", "docs/notes/")' in src
    for excluded in ("agate-workspace/", "site/"):
        assert excluded not in src.split("_LIVE_DOC_DIRS = ")[1].split("\n")[0], (
            f"CHECK 16 范围不得纳入 {excluded}（记录类，全体带锚反而失真）"
        )
