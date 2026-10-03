# tests/unit/test_marker_single_source.py — 正文标记形态单源守护
#
# 被测设计：docs/design-notes/design-marker-single-source.md
# 被测实现：agate/rules/markers.yaml（权威源）+ agate/scripts/agate_markers.py（取值库）
#
# 守护目标（mk_1~mk_5，见设计 §3.5）：
#   mk_1  消费方不得自带正则副本（判据必须单源）
#   mk_2  注册表驱动的形态与「手写该标记形态」行为一致（防注册表本身写错）
#   mk_3  **render() 产物必被 pattern() 命中** —— 生成器与判据不可能分叉（本设计最强一条）
#   mk_4  非法形态被拒（带参缺参 / 无参给参）
#   mk_5  成对关系完整（paired_with / resolves 指向的标记必须存在，防悬空指针）
#
# 为什么需要（实证）：同一「行首」概念本仓曾有三套互不相同的实现
# （check-scope-resolved.py 接受粗体/星号列表符；agate_common.py 的 DESIGN_GAP 不接受），
# 6 种书写形态里 3 种分叉，且**静默**：粗体 `**[DESIGN_GAP: x]**` 在 DESIGN_GAP 侧计 0。
#
# 平台无关：纯 Python + 文件读取，无 shell / 无路径假设。

import re
import sys

import pytest


def _markers_mod(agate_scripts):
    """导入单源库（同目录 import，避免依赖安装）。"""
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_markers

    agate_markers.reload()
    return agate_markers


# --- mk_1：消费方不得自带正则副本 -------------------------------------------

# 已登记的消费方（注册表 judged_by 声明）。新增消费方须同步此清单——
# 这正是 mk_1 的价值：让"新加一处副本"这件事**必须显式登记**，不能悄悄发生。
_CONSUMERS = [
    "check-scope-resolved.py",
    "check-retrospective.py",
]

# 允许出现字面正则的文件（判据自身所在）：单源库与注册表
_ALLOW_LITERAL = {"agate_markers.py"}


def test_mk_1_consumers_do_not_carry_regex_copies(agate_scripts):
    """消费方脚本不得自带 `\\[SCOPE\\+]` 类字面正则副本（判据单源）。

    PR #387 的教训：形态散在多处 ⇒ 改一处必漏其余（实测 14 处改动面里漏 5 处）。
    本用例把"再抄一份正则"变成**机械可检**。
    """
    # 匹配「转义方括号 + 大写标记名」的正则字面量形态。
    # 真实形态如 r"\[SCOPE\+\]" / r"^\s*-?\s*\[SCOPE\+\]" / "\[DESIGN_GAP:"
    # 判据：出现 `\[` 转义方括号 + 已登记/大写标记名 + 其后紧跟 `\+` 或 `]` 或 `:`
    literal = re.compile(r'\\\[[A-Z][A-Z_+]{2,}(?:\\\+|\]|:)')
    offenders = []
    for name in _CONSUMERS:
        path = agate_scripts / name
        if not path.is_file():
            pytest.fail(f"mk_1：登记的消费方 {name} 不存在（清单过期？）")
        src = path.read_text(encoding="utf-8")
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # 注释里引用形态（说明性）不算副本
            if literal.search(line) and "agate_markers" not in line:
                offenders.append(f"{name}:{i}: {stripped[:90]}")
    assert not offenders, (
        "mk_1 违反：消费方自带正则副本（判据必须单源，取值用 agate_markers.pattern()）：\n  "
        + "\n  ".join(offenders)
    )


def test_mk_1b_consumers_actually_use_single_source(agate_scripts):
    """正向确认：登记的消费方确实 import 了单源库（防"既没副本也没用单源"的空档）。"""
    for name in _CONSUMERS:
        src = (agate_scripts / name).read_text(encoding="utf-8")
        assert "import agate_markers" in src, (
            f"mk_1b：{name} 未 import agate_markers —— 它既无副本也非单源，形态来源不明"
        )


# --- mk_2：注册表形态与手写形态等价 -----------------------------------------

# 「手写该标记形态」的独立基准（**不得**从 markers.yaml 推导，否则是同义反复）。
# 这些是 PR #387 落地后的真实行为，作为回归基准冻结。
_EXPECTED = {
    # (标记, 输入行) -> 是否应检出
    ("SCOPE+", "[SCOPE+] x"): True,
    ("SCOPE+", "- [SCOPE+] x"): True,
    ("SCOPE+", "* [SCOPE+] x"): True,
    ("SCOPE+", "+ [SCOPE+] x"): True,
    ("SCOPE+", "> [SCOPE+] x"): True,
    ("SCOPE+", "**[SCOPE+] x"): True,
    ("SCOPE+", "  - [SCOPE+] x"): True,
    # 保守边界（刻意不覆盖，代价已量化登记）
    ("SCOPE+", "本节讨论 [SCOPE+] 的处置"): False,   # 行中出现
    ("SCOPE+", "- `[SCOPE+]`：无"): False,            # 行首反引号
    ("SCOPE+", "## [SCOPE+] 声明"): False,            # 标题形态
    # SCOPE+ 是**无参**标记：`]` 必须紧跟（故带空格/参数的形态不算）
    ("SCOPE+", "[SCOPE+ 观察] x"): False,
    ("SCOPE+", "[SCOPE+: param] x"): False,
    ("SCOPE+", "[SCOPE+EXTRA]"): False,
    # SCOPE_RESOLVED：接受反引号包裹 + 可带参 + 不要求紧跟 `]`
    ("SCOPE_RESOLVED", "[SCOPE_RESOLVED]"): True,
    ("SCOPE_RESOLVED", "[SCOPE_RESOLVED: y]"): True,
    ("SCOPE_RESOLVED", "`[SCOPE_RESOLVED: z]`"): True,
    ("SCOPE_RESOLVED", "**[SCOPE_RESOLVED: w]**"): True,
    ("SCOPE_RESOLVED", "> [SCOPE_RESOLVED] x"): True,
    ("SCOPE_RESOLVED", "本节讨论 [SCOPE_RESOLVED] 的"): False,
    ("SCOPE_RESOLVED", "[SCOPE_RESOLVEDabc]"): False,
}


@pytest.mark.parametrize("name,line,expected", [
    (n, ln, exp) for (n, ln), exp in _EXPECTED.items()
])
def test_mk_2_registry_matches_frozen_behavior(agate_scripts, name, line, expected):
    """注册表驱动的判据须与冻结基准一致（防注册表本身写错）。"""
    M = _markers_mod(agate_scripts)
    assert M.is_declaration(line, name) is expected, (
        f"mk_2：{name} 对 {line!r} 判定为 {not expected}，基准为 {expected}"
    )


# --- mk_3：生成 ↔ 判据闭环（本设计最强一条）---------------------------------

def test_mk_3_render_output_is_always_detected(agate_scripts):
    """**render() 的产物必被 pattern() 命中** —— 使「生成器」与「判据」不可能分叉。

    这是本设计最强的一条：它消灭的不是"某处写错"，而是"生成器写出来的东西判据不认"
    这个经典分叉**存在的可能**。
    """
    M = _markers_mod(agate_scripts)
    failures = []
    for name in M.names():
        spec = M.spec(name)
        params = None if spec["params"] == "none" else "示例参数内容"
        rendered = M.render(name, params)
        if not M.is_declaration(rendered, name):
            failures.append(f"{name}: render()={rendered!r} 未被 pattern() 命中")
    assert not failures, "mk_3 违反（生成器与判据分叉）：\n  " + "\n  ".join(failures)


def test_mk_3b_render_is_line_start_form(agate_scripts):
    """render() 产物须是**行首**形态（可直接追加到产出文件而不被当"提及"）。"""
    M = _markers_mod(agate_scripts)
    for name in M.names():
        spec = M.spec(name)
        params = None if spec["params"] == "none" else "示例"
        rendered = M.render(name, params)
        assert rendered.startswith("["), f"mk_3b：{name} 生成物非行首形态：{rendered!r}"


# --- mk_4：非法形态被拒（fail-closed）--------------------------------------

def test_mk_4a_no_param_marker_rejects_params(agate_scripts):
    """无参标记给参 → ValueError（不生成非法写法）。"""
    M = _markers_mod(agate_scripts)
    with pytest.raises(ValueError):
        M.render("SCOPE+", "不该有参数")


def test_mk_4b_required_param_marker_rejects_empty(agate_scripts):
    """带参标记缺参 → ValueError。"""
    M = _markers_mod(agate_scripts)
    with pytest.raises(ValueError):
        M.render("DESIGN_GAP")
    with pytest.raises(ValueError):
        M.render("DESIGN_GAP", "   ")


def test_mk_4c_unknown_marker_fails_closed(agate_scripts):
    """未登记标记 → KeyError（不静默返回空——那会让"没查"被读成"没问题"）。"""
    M = _markers_mod(agate_scripts)
    with pytest.raises(KeyError):
        M.pattern("NOT_REGISTERED_MARKER")


# --- mk_5：成对关系完整 -----------------------------------------------------

def test_mk_5_pairing_targets_exist(agate_scripts):
    """paired_with / resolves 指向的标记必须已登记（防悬空指针）。"""
    M = _markers_mod(agate_scripts)
    registered = set(M.names())
    dangling = []
    for name in M.names():
        spec = M.spec(name)
        for field in ("paired_with", "resolves"):
            target = spec.get(field)
            if target and target not in registered:
                dangling.append(f"{name}.{field} → {target}（未登记）")
    assert not dangling, "mk_5 违反（悬空配对指针）：\n  " + "\n  ".join(dangling)


def test_mk_5b_pairing_is_symmetric(agate_scripts):
    """配对须**双向**：A.paired_with=B 时 B 应 resolves=A（防单向声明造成的理解分叉）。"""
    M = _markers_mod(agate_scripts)
    bad = []
    for name in M.names():
        spec = M.spec(name)
        other = spec.get("paired_with")
        if not other:
            continue
        back = M.spec(other).get("resolves")
        if back != name:
            bad.append(f"{name}.paired_with={other}，但 {other}.resolves={back!r}（应为 {name!r}）")
    assert not bad, "mk_5b 违反（配对非双向）：\n  " + "\n  ".join(bad)


# --- 注册表自身合法性 -------------------------------------------------------

def test_registry_schema_fields_present(agate_scripts):
    """每个条目的必填字段齐备且取值合法（schema 的最小可用子集）。"""
    M = _markers_mod(agate_scripts)
    for name in M.names():
        spec = M.spec(name)
        for field in ("name", "purpose", "phases", "params"):
            assert field in spec, f"{name} 缺必填字段 {field}"
        assert spec["params"] in ("none", "optional_text", "required_text"), \
            f"{name} params 取值非法：{spec['params']}"
        assert spec["purpose"].strip(), f"{name} purpose 为空"


# --- mk_6：标记名互斥 + 与既有消费方等价（HIGH-1 的守护）---------------------
#
# HIGH-1（2026-10-02 独立评审查出，已修）：`pattern("DESIGN_GAP")` 曾**吞并**
# `DESIGN_GAP_REVIEWED`（`_` 满足旧的 `[^a-z]` 边界），逐 P7 文件对账 59 vs 121（2.05×）。
# 根因：注册表被声明为判据权威源，但该判据与实际在判的 agate_common **不等价**，
# 且**当时无任何测试守护** ⇒ 下一个接线的人会立刻踩中而测试抓不到。
#
# mk_6 两条：
#   mk_6a 已登记标记两两互斥（A 的 pattern 不得命中 B 的合法写法）——防前缀吞并
#   mk_6b pattern(name) 与**既有消费方**（agate_common）在真实语料上等价


def test_mk_6a_registered_markers_are_mutually_exclusive(agate_scripts):
    """A 的判据不得命中 B 的**合法写法**（防 `DESIGN_GAP` 吞并 `DESIGN_GAP_REVIEWED`）。

    做法：对每对已登记标记 (A,B)，用 B 的 `render()` 产物去测 A 的 `pattern()`——
    `render()` 保证是 B 的合法写法（mk_3 已证），故 A 命中即前缀吞并/重叠。
    """
    M = _markers_mod(agate_scripts)
    overlaps = []
    for a in M.names():
        for b in M.names():
            if a == b:
                continue
            spec_b = M.spec(b)
            params = None if spec_b["params"] == "none" else "示例参数"
            try:
                sample = M.render(b, params)
            except ValueError:
                continue
            if M.is_declaration(sample, a):
                overlaps.append(f"{a} 命中 {b} 的合法写法 {sample!r}")
    assert not overlaps, "mk_6a 违反（标记名重叠/前缀吞并）：\n  " + "\n  ".join(overlaps)


def test_mk_6b_design_gap_matches_agate_common_on_real_corpus(agate_root):
    """`pattern("DESIGN_GAP")` 与既有消费方 `agate_common.count_design_gap` 在**真实语料**上等价。

    这是 HIGH-1 的直接回归锁：注册表被声明为判据权威源，就必须与实际在判的实现一致，
    否则「单源」名不副实。全仓逐文件计数，要求**完全相等**。
    """
    scripts = agate_root / "scripts"
    p = str(scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_markers

    agate_markers.reload()
    from agate_common import count_design_gap

    tasks = agate_root.parent / "agate-workspace" / "tasks"
    if not tasks.is_dir():
        pytest.skip("无 agate-workspace/tasks（安装包环境），跳过语料等价校验")

    total_old = total_new = 0
    diffs = []
    for f in sorted(tasks.glob("*/*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        old, _ = count_design_gap(text, allow_blockquote=True)
        new = agate_markers.count(text, "DESIGN_GAP")
        total_old += old
        total_new += new
        if old != new:
            diffs.append(f"{f.name}: agate_common={old} pattern={new}")

    assert not diffs, (
        f"mk_6b 违反（DESIGN_GAP 判据与 agate_common 不等价）："
        f"总计 old={total_old} new={total_new}\n  " + "\n  ".join(diffs[:10])
    )


# --- mk_7：注册表 vs **真实消费方** 的等价守护（2026-10-03，外部评审查出 #388 分叉）---
#
# 背景（ADR-014 教训「声明单源 ≠ 已经单源」**在同一批改动中重犯**）：
#   注册表把 8 个标记全部声明为权威源，但实际只有 SCOPE+ 一对真正接入了取值库。
#   NEED_CONFIRM / NO_NEED_CONFIRM / PROD_TOUCHED 三对的 `judged_by` 曾为 `[]`（登记为
#   "无消费方"），而**实际消费方存在且口径不同**：
#     · `agate_common._NC_RE` 等用 `^\s*`*-?\s*`*\[NAME\]`（可选反引号 + 可选短横线）
#     · `pre-commit-gate.py:343` 用 `^\s*-?\s*\[PROD_TOUCHED\]`（**安全门**，命中即中止 commit）
#   实测两仓真实语料 **182 行**判定相反 ⇒ 按 ADR-015 属必拦的「判据分叉」。
#
# 本守护把 mk_6b（DESIGN_GAP 等价）推广到**全部声明有消费方的标记**。

# 标记名 -> (消费方文件, 该文件里必须出现的口径片段)
# ⚠️ **F6 修复**（2026-10-03 实施评审查出）：PROD_NOT_TOUCHED 原先登记
#    `pre-commit-gate.py:347`，但第 347 行检查的是 `[PROD_TOUCHED]\s*$` **且不可达**
#    （同形态第 343 行已 sys.exit）⇒ **无任何代码消费 PROD_NOT_TOUCHED**
#    （它是配对声明，供人/评审阅读）。已从本表移除，并在 markers.yaml 登记 `judged_by: []`。
_CONSUMER_ANCHORS = {
    "NEED_CONFIRM": ("agate_common.py", r"\[NEED_CONFIRM\]"),
    "NO_NEED_CONFIRM": ("agate_common.py", r"\[NO_NEED_CONFIRM\]"),
    "PROD_TOUCHED": ("pre-commit-gate.py", r"\[PROD_TOUCHED\]"),
}
# 明确声明「无消费方」的标记——mk_7a 要求其 judged_by **为空**（不得凭空登记）
_NO_CONSUMER = ("PROD_NOT_TOUCHED",)


def test_mk_7a_registry_declares_real_consumer(agate_scripts):
    """mk_7a：声明有消费方的标记，其 `judged_by` 必须**非空且指向真实文件**。

    防「登记为无消费方、实际却有阻断型消费方」——PROD_TOUCHED 正是这样被错登为 `[]`，
    而它是**安全门**（命中即 `sys.exit(1)` 中止 commit）。
    """
    M = _markers_mod(agate_scripts)
    for name in _NO_CONSUMER:
        assert not (M.spec(name).get("judged_by") or []), (
            f"{name} 声明为无消费方，judged_by 必须为空（防凭空登记不存在的消费方）"
        )
    for name in _CONSUMER_ANCHORS:
        entry = M.spec(name)
        judged = entry.get("judged_by") or []
        assert judged, (
            f"{name} 的 judged_by 为空，但它有真实消费方 "
            f"（{_CONSUMER_ANCHORS[name][0]}）——错登会让 agate-mark.py --list 误导读者"
        )
        for ref in judged:
            fn = str(ref).split(":")[0]
            assert (agate_scripts / fn).is_file(), f"{name} 的 judged_by 指向不存在的文件: {ref}"


def test_mk_7b_registry_matches_real_consumer_on_corpus(agate_scripts):
    """mk_7b：注册表口径与**真实消费方正则**在代表性语料上判定一致。

    ⚠️ 这是 mk_6b 的推广：不看声明看**行为**。用例刻意覆盖 default 口径与消费方口径
    **方向相反**的两侧——实测正是这两个方向造成了 182 行分叉。
    """
    import re
    am = _markers_mod(agate_scripts)

    cases = {
        "NEED_CONFIRM": [
            ("- [NEED_CONFIRM] x", True),
            ("- `[NEED_CONFIRM]` x", True),
            ("- [NEED_CONFIRM]其余说明", True),
            ("**[NEED_CONFIRM]** x", False),
            ("* [NEED_CONFIRM] x", False),
            ("> [NEED_CONFIRM] x", False),
        ],
        "NO_NEED_CONFIRM": [
            ("- [NO_NEED_CONFIRM] x", True),
            ("[NO_NEED_CONFIRM]其余隐含需求方向已明确", True),
            ("* [NO_NEED_CONFIRM] x", False),
        ],
        "PROD_TOUCHED": [
            ("- [PROD_TOUCHED]", True),
            ("[PROD_TOUCHED]", True),
        ],
    }
    # **F9 修复**（2026-10-03 实施评审查出）：原先此处**写死**消费方正则副本，
    # 不读消费方源码 ⇒ 消费方一改，本守护会**悄悄失效**（正是最终结论 §6 提醒的守护形态）。
    # 现改为**从消费方源码实际取值**：
    #   · agate_common 的 `_NC_RE` / `_NO_NEED_RE`（模块级常量，可直接 import）
    #   · pre-commit-gate.py 的 PROD_TOUCHED 正则（内联在函数里，从源码抽取）
    sys.path.insert(0, str(agate_scripts))
    import agate_common as _ac
    gate_src = (agate_scripts / "pre-commit-gate.py").read_text(encoding="utf-8")
    _m = re.search(r're\.match\(r"([^"]*\\\[PROD_TOUCHED\\\][^"]*)"', gate_src)
    assert _m, "未能从 pre-commit-gate.py 抽到 PROD_TOUCHED 的消费方正则"
    consumer = {
        "NEED_CONFIRM": _ac._NC_RE,
        "NO_NEED_CONFIRM": _ac._NO_NEED_RE,
        "PROD_TOUCHED": re.compile(_m.group(1)),
    }
    for name, rows in cases.items():
        for line, want in rows:
            got_reg = bool(am.pattern(name).search(line))
            got_con = bool(consumer[name].search(line))
            assert got_reg == want, f"注册表 {name} 对 {line!r} 判定 {got_reg}，期望 {want}"
            assert got_reg == got_con, (
                f"**判据分叉**：{name} 对 {line!r} 注册表={got_reg} 消费方={got_con}"
            )


# --- mk_8：**生成器产物必须被消费方认**（F5 修复的机械约束）---------------------
#
# 2026-10-03 实施评审查出（F5）：面向生产环境安全门的 PROD_TOUCHED，
#   `render()` 原先产出 `[PROD_TOUCHED: db write]`（可选参数 ⇒ 带冒号），
#   而文档（CONTEXT.md:24 / dispatch-protocol.md:1161）与安全门
#   （`pre-commit-gate.py` 的 `^\s*-?\s*\[PROD_TOUCHED\]`）要求 `[PROD_TOUCHED] 描述`。
#   ⇒ **照 WORKFLOW.md 用生成器写标记的 agent，安全门静默放行**（安全门漏检）。
#
# 本守护把「生成器写出的东西，消费方必须认」变成**机械约束**。

def test_mk_8_render_output_is_accepted_by_safety_gate(agate_scripts):
    """mk_8：`render()` 的产物必须被**安全门正则**命中（PROD_TOUCHED）。

    判据直接取自消费方源码的形态（不写死副本 —— F9 的教训）。
    """
    import re
    M = _markers_mod(agate_scripts)
    gate_src = (agate_scripts / "pre-commit-gate.py").read_text(encoding="utf-8")
    m = re.search(r'\^\\s\*-\?\\s\*\\\[(PROD_[A-Z_]+)\\\]', gate_src)
    assert m, "未能在 pre-commit-gate.py 中找到 PROD_* 的安全门正则"
    gate_marker = m.group(1)
    # 用真实的安全门正则（从源码抽取）
    gate_re = re.compile(r"^\s*-?\s*\[" + gate_marker + r"\]")
    sample = M.render("PROD_TOUCHED")
    assert gate_re.match(sample) or gate_re.match("- " + sample), (
        f"render('PROD_TOUCHED') = {sample!r} 不被安全门 {gate_marker} 命中 "
        "⇒ 用生成器写标记会**静默绕过安全门**"
    )


def test_mk_8b_prod_markers_render_without_colon(agate_scripts):
    """mk_8b：PROD_TOUCHED / PROD_NOT_TOUCHED 的产物**不含冒号**（文档二值格式）。

    文档形态：`[PROD_TOUCHED] {描述}` / `[PROD_NOT_TOUCHED]`（CONTEXT.md:24）。
    `params: optional_text` 会渲染成 `[X: 描述]`，那是**旧的错误形态**（F5）。
    """
    M = _markers_mod(agate_scripts)
    for name in ("PROD_TOUCHED", "PROD_NOT_TOUCHED"):
        sample = M.render(name)
        assert name + "]" in sample, f"{name} 渲染产物异常: {sample!r}"
        assert name + ":" not in sample, (
            f"{name} 渲染出带冒号的形态 {sample!r}，与文档/安全门不符（F5 回归）"
        )
