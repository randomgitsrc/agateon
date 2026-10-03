# tests/unit/test_agate_common_evidence.py — 判据鲁棒性四项单源（设计 v3）
#
# 被测：agate_common.py 的 resolve_evidence / extract_evidence_refs /
#       PAREN_OPEN·PAREN_CLOSE·PAREN_INNER / strip_fenced_blocks
#
# 设计依据：docs/design-notes/design-gate-robustness-four-gaps.md（过两轮独立评审）
#
# **本文件的存在理由**（设计 §1.2 的核心洞察）：
#   每处「放宽解析」都是**交换**——解除假红的同时，移除了原本靠假红**顺带**提供的保护。
#   故每条放宽都配**链路级**回归锁，而不只在函数内验证。
#
# 覆盖验收锚：V1 V2 V2b V4 V7 V8 V9c V9d V12
# （V7b/V9/V9b/V10/V10b/V11/V12b 在各自消费方的测试文件中）

import re
import sys

import pytest


def _common(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    return agate_common


# --- V1 / V2 / V2b：resolve_evidence 的解析与越界 ---------------------------

def _mk_task(tmp_path, files=("a.json",), nested=None):
    """建最小任务目录。nested: 在 P6-evidence/ 下再建同名嵌套目录并放同名文件。"""
    td = tmp_path / "task"
    ev = td / "P6-evidence"
    ev.mkdir(parents=True)
    for f in files:
        (ev / f).write_text('{"v":"outer"}', encoding="utf-8")
    if nested:
        n = ev / "P6-evidence"
        n.mkdir()
        (n / nested).write_text('{"v":"inner"}', encoding="utf-8")
    return td


@pytest.mark.parametrize("ref", [
    "a.json",                    # 裸名
    "P6-evidence/a.json",        # 带前缀（TPV0100 实际写法）
    "./a.json",                  # 前导 ./
    "./P6-evidence/a.json",      # 两者组合
])
def test_ev_v1_four_forms_all_resolve(agate_scripts, tmp_path, ref):
    """V1：四种常见写法均解析成功（原缺口①是「带前缀被判缺失」）。"""
    C = _common(agate_scripts)
    td = _mk_task(tmp_path)
    assert C.resolve_evidence(str(td), ref) is not None, f"{ref} 应解析成功"


def test_ev_v1_task_root_relative(agate_scripts, tmp_path):
    """V1：任务根相对（`../vision-reports/x.yml`）——TPV0100 的真实写法。

    实测依据：TPV0100 的 `verdict_evidence` 与结论行**都**用了
    `../vision-reports/bdd-01.yaml`（全文出现 56 次），vision YAML 在任务根。
    """
    C = _common(agate_scripts)
    td = _mk_task(tmp_path)
    vr = td / "vision-reports"
    vr.mkdir()
    (vr / "x.yml").write_text("k: v", encoding="utf-8")
    assert C.resolve_evidence(str(td), "../vision-reports/x.yml") is not None


@pytest.mark.parametrize("ref", [
    "../../etc/passwd",
    "/etc/passwd",
    "../sibling-task/x.json",
])
def test_ev_v2_out_of_range_rejected(agate_scripts, tmp_path, ref):
    """V2：越界一律 None（绝对路径 / 上溯 / 兄弟任务）。"""
    C = _common(agate_scripts)
    td = _mk_task(tmp_path)
    assert C.resolve_evidence(str(td), ref) is None, f"{ref} 应被拒绝"


def test_ev_v2_symlink_escape_rejected(agate_scripts, tmp_path):
    """V2：**软链逃逸**必须被 realpath 拦住。

    ⚠️ 平台分支：Windows 上 `os.symlink` 需权限，退化为复制模式 —— 复制模式下
    目标仍在任务外但已不是软链，realpath 不改变结果，故两种平台断言的都是
    「解析结果不得越出任务目录」这一个**语义**，不假设 POSIX 软链语义。
    """
    C = _common(agate_scripts)
    td = _mk_task(tmp_path)
    outside = tmp_path / "secret"
    outside.mkdir()
    (outside / "x.json").write_text("secret", encoding="utf-8")
    link = td / "P6-evidence" / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("本平台不支持创建目录软链（Windows 无权限）——由 platform-scan 覆盖")
    assert C.resolve_evidence(str(td), "link/x.json") is None, "软链逃逸未被拦住"


def test_ev_v2b_nested_same_name_resolves_outer(agate_scripts, tmp_path):
    """V2b（**本设计最重要的回归锁**）：嵌套同名目录时，必须解析到**外层**。

    背景：只剥一次前缀 / 或不剥前缀直接 join，都会**静默**指向嵌套副本
    （内容不同、零告警），使 BDD-6 的存在性/非空/md5 三项**全部在错误制品上求值**。
    """
    C = _common(agate_scripts)
    td = _mk_task(tmp_path, nested="a.json")
    got = C.resolve_evidence(str(td), "P6-evidence/a.json")
    assert got is not None
    assert '{"v":"outer"}' in open(got, encoding="utf-8").read(), (
        f"解析到了嵌套副本（内容 inner）而非外层：{got}"
    )


@pytest.mark.parametrize("ref", [
    ".//P6-evidence/a.json",     # 双斜杠（单去 ./ 会漏）
    "P6-evidence//a.json",       # 冗余分隔符
    "P6-evidence/./a.json",      # 内嵌 ./
    "P6-evidence/P6-evidence/a.json",   # 自身前缀嵌套（只剥一次会落嵌套）
])
def test_ev_v2b_redundant_separators_and_prefix_loop(agate_scripts, tmp_path, ref):
    """V2b：冗余分隔符与多重前缀都必须归一到外层（自测发现的两类弱点）。"""
    C = _common(agate_scripts)
    td = _mk_task(tmp_path, nested="a.json")
    got = C.resolve_evidence(str(td), ref)
    assert got is not None, f"{ref} 应解析成功"
    assert '{"v":"outer"}' in open(got, encoding="utf-8").read(), (
        f"{ref} 解析到了嵌套副本：{got}"
    )


def test_ev_v7_real_violations_still_rejected(agate_scripts, tmp_path):
    """V7：真违规仍拦——放宽解析不得让"不存在的文件"过关。"""
    C = _common(agate_scripts)
    td = _mk_task(tmp_path)
    for ref in ("nonexist.json", "P6-evidence/nonexist.json", "nope/x.json"):
        assert C.resolve_evidence(str(td), ref) is None, f"{ref} 不存在，应为 None"


# --- V4：括号常量 ----------------------------------------------------------

def test_ev_v4_paren_constants_cover_four_forms(agate_scripts):
    """V4：四种括号写法全提取（ASCII / 全角 / 全角开+半角闭 / 半角开+全角闭）。

    ⚠️ 中段用**排除类**（不得改成 `.*?`：会吞跨括号内容，改变提取语义）。
    """
    C = _common(agate_scripts)
    rx = re.compile(C.PAREN_OPEN + "(" + C.PAREN_INNER + "+)" + C.PAREN_CLOSE)
    cases = {
        "(a.json)": "a.json",
        "（a.json）": "a.json",
        "（a.json)": "a.json",
        "(a.json）": "a.json",
    }
    for line, want in cases.items():
        m = rx.search(line)
        assert m and m.group(1) == want, f"{line!r} 未正确提取"


# --- V9c / V9d：extract_evidence_refs（第四项单源）--------------------------

def test_ev_v9c_mid_line_prefixed_path_extracted(agate_scripts):
    """V9c：**行中的目录前缀路径**必须被提取（真实数据的主流写法）。

    实测依据：两仓 1,774 条 PASS 行回放——旧"行末括号"规则取不到、新提取器能取到的有
    **70 条**（真实的 M-A 假红）。形态是「引用在行中、后面跟说明」，如
    `(screenshots/b07.png — element: .katex nth(1))`。

    ⚠️ **行中「无目录前缀」的纯文件名不取**（如 `(bdd-1.log) — 说明`）——
    这不是遗漏，是**实测否决**：加上它会让两仓 **517 行**多出引用、**701 次解析不到**
    ⇒ 大面积假红。根因是多括号行的非末组多为**命令注释**。
    详见 `agate_common.extract_evidence_refs` docstring 的 (c) 否决记录。
    """
    C = _common(agate_scripts)
    # ⚠️ 2026-10-03 按**决策 A1** 更正：原用例用的形态含**内层括号**
    #    （`… nth(1)`），该形态经裁决确认为**已接受边界**（不提取）——
    #    见 test_ev_v9c_nested_parens_is_boundary。此处改测真正的
    #    「行中目录前缀路径」（**无**内层括号）。
    refs = C.extract_evidence_refs("- PASS BDD-1: works (screenshots/b07.png) — 后跟说明文字")
    assert "screenshots/b07.png" in refs, f"行中目录前缀路径未被提取：{refs}"
    # 注：census 规则对「行中**整体是路径**的括号组」**会**提取——
    #   `(bdd-1.log) — 说明` 属此类（组内项整体是路径），故**应当**取到。
    #   真正被否决的是「行中**任意**括号组都算引用」（含命令注记），那会造成
    #   517 行多出引用 / 701 次解析不到（见 extract_evidence_refs docstring）。
    assert C.extract_evidence_refs("- PASS BDD-1: x (bdd-1.log) — 说明") == ["bdd-1.log"]


def test_ev_v9c_nested_parens_is_boundary(agate_scripts):
    """**决策 A1**：含内层括号的注释组是**已接受边界**，不构成引用。

    实测依据（裁决复核一致）：两仓含内层括号的括号组 26 处，
    逐一对两处基址 isfile ⇒ **26/26 全部命中 0**；A2（加规则覆盖）收益为 0。
    """
    C = _common(agate_scripts)
    assert C.extract_evidence_refs(
        "- PASS BDD-1: works (screenshots/b07.png — element: .katex nth(1))"
    ) == [], "A1：注释组不应被提取"


def test_ev_metadata_markers_are_not_refs(agate_scripts):
    """元数据标记**不是**证据引用：`(vision: …)` 与 `(manual-review: <file>)` 须排除。

    实测依据：`(manual-review: review-gap.md)` 是 provenance 审计 5 读的**协议标记**，
    若被当引用会去 P6-evidence/ 找它 ⇒ 假红（测试 test_vision_gap_prov_1 锁定）。
    """
    C = _common(agate_scripts)
    refs = C.extract_evidence_refs("- PASS BDD-1 (screenshots/login.png) (manual-review: review-gap.md)")
    assert refs == ["screenshots/login.png"], refs


def test_ev_v9d_fullwidth_screenshots_not_truncated(agate_scripts):
    """V9d：全角 screenshots 引用不得把 `）` 截进路径。

    背景：`re.findall(r"screenshots/[^ ),]+", "（screenshots/a.png）")`
    会得到 `screenshots/a.png）`（把全角右括号算进路径）⇒ 解析为不存在的文件。
    """
    C = _common(agate_scripts)
    refs = C.extract_evidence_refs("x（screenshots/a.png）")
    assert refs == ["screenshots/a.png"], f"全角右括号被截进路径：{refs}"


def test_ev_extract_separates_multiple_refs(agate_scripts):
    """逗号分隔多文件（既有写法，勿破坏）。"""
    C = _common(agate_scripts)
    refs = C.extract_evidence_refs("- PASS BDD-1: 描述 (a.json, screenshots/b.png)")
    assert "a.json" in refs and "screenshots/b.png" in refs, refs


def test_ev_extract_strips_vision_marker(agate_scripts):
    """`(vision: …)` 是元数据而非引用，须先剥离（沿用 provenance 既有做法）。"""
    C = _common(agate_scripts)
    refs = C.extract_evidence_refs("- PASS BDD-1: 描述 (vision: ok) (a.json)")
    assert refs == ["a.json"], refs


def test_ev_extract_ignores_prose_parenthetical(agate_scripts):
    """散文括号（`(as discussed)`）不是引用——内容不像文件名则不取。"""
    C = _common(agate_scripts)
    assert C.extract_evidence_refs("- PASS BDD-1: 描述 (as discussed)") == []


# --- V12：围栏剥离 + 未闭合不吞正文 ----------------------------------------

def test_ev_v12_fenced_block_stripped(agate_scripts):
    """V12 正向：围栏内的 `- PASS` 被剥离（格式示例不算预判）。"""
    C = _common(agate_scripts)
    lines = ["说明", "```", "- PASS BDD-1: 示例 (a.json)", "```", "正文"]
    kept, warn = C.strip_fenced_blocks(lines)
    assert not any("- PASS" in _ln for _ln in kept), kept
    assert warn is None


def test_ev_v12_unclosed_fence_not_stripped(agate_scripts):
    """V12 反向（**关键**）：未闭合围栏**不剥离** + 返回告警。

    ⚠️ 不得照搬 `check-protocol-consistency.py` 的 `in_fence`——它遇未闭合会
    **跳到 EOF**，会把其后的真预判一起吞掉（假绿）。先例是 provenance 对
    frontmatter 的处理：「找不到闭合对 ⇒ 不剥离 + 显式告警（宁可多审，不可吞正文）」。
    """
    C = _common(agate_scripts)
    lines = ["说明", "```", "- PASS BDD-1: 真预判 (a.json)"]
    kept, warn = C.strip_fenced_blocks(lines)
    assert any("- PASS" in _ln for _ln in kept), "未闭合围栏吞掉了正文（假绿）"
    assert warn, "未闭合围栏应返回告警"


def test_ev_v12_outside_fence_still_detected(agate_scripts):
    """V12 双向：围栏**外**的 `- PASS` 仍被保留（不得误放）。"""
    C = _common(agate_scripts)
    lines = ["```", "- PASS 示例", "```", "- PASS 真预判"]
    kept, _ = C.strip_fenced_blocks(lines)
    assert sum(1 for _ln in kept if "- PASS" in _ln) == 1, kept


# --- V8：常量值相等（不得用 is）--------------------------------------------

def test_ev_v8_consumers_share_constants_by_value(agate_scripts):
    """V8：三个消费方**不再自带括号字面量**，而是走 `agate_common`。

    判据是「**不自带副本**」而非「都直接写 PAREN_OPEN」——provenance 通过
    `extract_evidence_refs()` 间接消费（该函数已内含括号常量），这同样是单源。
    ⚠️ 不得用 `is` 断言对象同一性：字符串驻留使**同文件独立字面量 `is` 返回 True**
    ⇒ 空断言假通过；`re.compile(...) is` 实测 False ⇒ 恒失败断言。故只断言**值相等**。
    """
    C = _common(agate_scripts)
    # 值相等（可断言）：三个消费方若各自定义，必须与单源常量一致
    assert C.PAREN_OPEN == r"[（(]"
    assert C.PAREN_CLOSE == r"[）)]"
    assert C.PAREN_INNER == r"[^（()）]"

    for consumer in ("check-p6-evidence.py", "check-p6-provenance.py",
                     "check-judge-verdict.py"):
        src = (agate_scripts / consumer).read_text(encoding="utf-8")
        assert "agate_common" in src, f"{consumer} 未 import agate_common"
        # 不得再出现只认 ASCII 括号的旧字面量（那是本批要消灭的分叉源头）
        assert r'r"\([^()]*' not in src, f"{consumer} 仍带 ASCII-only 括号字面量"
        assert r'"[^()]"' not in src, f"{consumer} 仍带 ASCII-only 括号字面量"
        # 至少以某种方式消费**提取单源**——2026-10-03 裁决后三个消费方**全部**走
        # agate_common 的提取函数（judge 也改走 extract_conclusion_refs，
        # 原先它自持 _REF_GROUP_RE，属 ADR-014 意义上的判据分叉，已被评审查出并修掉）。
        consumed = ("extract_evidence_refs" in src or "extract_conclusion_refs" in src)
        assert consumed, f"{consumer} 未消费提取单源"
        # 只查**代码行**（去注释），否则会把自己的说明性注释误判为副本
        code = "\n".join(_ln for _ln in src.splitlines()
                          if not _ln.lstrip().startswith("#"))
        assert "_REF_GROUP_RE" not in code, f"{consumer} 仍自带提取正则副本"
