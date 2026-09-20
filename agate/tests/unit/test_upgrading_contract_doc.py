# tests/unit/test_upgrading_contract_doc.py — TAG0037 P3 组 C（批 F1a：agate/UPGRADING.md + CHANGELOG.md 文档面）
# 被测：agate/UPGRADING.md「版本管理生命周期」节新增的「版本目录结构契约」「portable 安装」小节、
#       §3 顶部注记与 `### v0.73.0` 节、对照表 / 解析优先级表去 legacy；CHANGELOG 版本段。
# BDD 映射：BDD-1（契约成文 (a)–(d)）、BDD-3 ③（文档块条目集合 == agate_package.boundary_lines()）、
#           BDD-19（不宣称零依赖 + portable 依赖声明）、BDD-39 ①–⑤、BDD-38 ④（改写口径见 test_upgrading_lifecycle.py）、
#           BDD-50 ①（可判定且不易腐的部分：v0.73.0 变更记录含 BREAKING 标注与迁移指引指针）。
# 口径（P3 约束 2）：只断言关键词 / 结构（节标题存在、命令片段、表列数、不含某模式），不写死易变文案。
# 不易腐（永久回归 vs 一次性交付事实，TAG0025 教训）：
#   * "历史版本节原文保留"以**不可变的基线提交 75a8102** 为参照（历史节内容本就不会再变），不断言"最近一次改动"；
#   * CHANGELOG 断言取「[0.73.0] 段（若已存在）否则 [Unreleased] 段」——发版重命名后仍成立，下个版本累积也不会使其变红。
# 平台无关：纯文本 + git 读取；无临时目录字面量、无符号链接、无裸 python3。
# 当前红灯（B 类，断言失败 / agate_package 缺失）：UPGRADING 尚无契约 / portable / v0.73.0 节；对照表仍有 legacy 列。

import difflib
import re

import pytest

import helpers_tag_repo as H

UPGRADING = H.REPO_ROOT / "agate" / "UPGRADING.md"
CHANGELOG = H.REPO_ROOT / "CHANGELOG.md"
BASE_SHA = "75a8102"  # P1 启动基线（不可变历史证据）
# 旧称字面量（拼接构造：本文件不属 BDD-37 白名单，源码中不得直接出现旧称字面量）
_OLD_SINGLE_LINK = "单" + "软链"

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _read(path):
    return path.read_text(encoding="utf-8")


def _headings(text):
    """[(行号, 级别, 标题)]，跳过 fenced 代码块内的行。"""
    out, in_fence = [], False
    for i, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def _section(text, title_pat, level=None):
    """取第一个标题匹配 title_pat（正则）的小节：从标题行到下一个同级或更高级标题前；不存在返回 ""。"""
    lines = text.splitlines()
    heads = _headings(text)
    for idx, (ln, lv, title) in enumerate(heads):
        if level is not None and lv != level:
            continue
        if re.search(title_pat, title):
            end = len(lines)
            for ln2, lv2, _t in heads[idx + 1 :]:
                if lv2 <= lv:
                    end = ln2
                    break
            return "\n".join(lines[ln:end])
    return ""


def _fences(section_text):
    """小节内全部 fenced 代码块内容（不含围栏行）。"""
    blocks = re.findall(r"^```[^\n]*\n(.*?)^```", section_text, re.S | re.M)
    return blocks


def _table_rows(section_text):
    """小节内所有表格行 → [[单元格...]]（含表头，不含分隔行）。"""
    rows = []
    for line in section_text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
    return rows


@pytest.fixture(scope="module")
def upgrading():
    return _read(UPGRADING)


@pytest.fixture(scope="module")
def lifecycle(upgrading):
    return _section(upgrading, r"版本管理生命周期", level=2)


@pytest.fixture(scope="module")
def contract(lifecycle):
    """契约小节（标题含「结构契约」，位于生命周期节内）；缺失返回 ""——fixture 自身不断言，失败留给用例（避免变成 ERROR）。"""
    return _section(lifecycle, r"结构契约")


# ---------------------------------------------------------------------------
# BDD-1  结构契约成文于权威源
# ---------------------------------------------------------------------------


def test_bdd_1_exactly_one_contract_section_in_whole_document(upgrading):
    """BDD-1：整份 UPGRADING 中标题含「结构契约」的小节恰好一个（不与历史节重复宣称），且位于「版本管理生命周期」节内。"""
    heads = [t for _ln, _lv, t in _headings(upgrading) if "结构契约" in t]
    assert len(heads) == 1, f"应恰好一个契约小节: {heads}"
    life = _section(upgrading, r"版本管理生命周期", level=2)
    assert any("结构契约" in t for _ln, _lv, t in _headings(life)), "契约小节应位于「版本管理生命周期」节内（权威源）"


def test_bdd_1_a_version_root_tree_lists_all_entries(contract):
    """BDD-1 (a)：版本根结构树含 vX.Y.Z/、latest、current、根 scripts/、可选 repo/。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    trees = [b for b in _fences(contract) if "latest" in b and "current" in b]
    assert trees, "契约小节应含版本根结构树（fenced 代码块）"
    tree = trees[0]
    for token in ("vX.Y.Z/", "latest", "current", "scripts/", "repo/", "agate/"):
        assert token in tree, f"结构树缺 {token!r}"
    assert "可选" in contract or "optional" in contract.lower(), "repo/ 应标注为可选"


def test_bdd_1_b_top_level_entry_set_and_violation_rule(contract):
    """BDD-1 (b)：vX.Y.Z/ 顶层条目完整列举（agate/ + 三个登记根文件 + 隐藏元数据说明），并写明未登记 = 违约。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    for token in ("agate/", "CHANGELOG.md", "LICENSE", "NOTICES.md"):
        assert token in contract, f"契约小节缺顶层条目 {token!r}"
    assert "隐藏" in contract, "应说明已登记隐藏元数据（当前为空也须写明）"
    assert re.search(r"未登记[^\n]*违约", contract), "应写明「未登记的顶层条目 = 违约」"


def test_bdd_1_c_body_directory_name_is_fixed(contract):
    """BDD-1 (c)：本体目录名固定为 agate/，不出现可配置 / 可扩展 / manifest 声明表述。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    assert not re.search(r"可配置|可扩展|manifest 声明", contract), "契约小节不得出现「可配置|可扩展|manifest 声明」"
    assert re.search(r"固定", contract), "应写明目录名固定"


def test_bdd_1_d_single_source_file_path(contract):
    """BDD-1 (d) / BDD-3：边界清单单一来源文件路径写入契约小节。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    assert "agate/scripts/agate_package.py" in contract


def test_bdd_1_states_install_state_vs_post_run_state(contract):
    """P2 §3.1 / eng B-1：契约约束"安装器交付的内容"，运行后的字节码不属违约——须成文，否则使用者会把 __pycache__ 当违约。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    assert "__pycache__" in contract


def test_bdd_1_protocol_root_sentence_corrected(upgrading):
    """P2 §3.1 / P1 扫描 G：既有"整仓形态下协议根为 <版本目录>/"与真实 _protocol_root 语义不符，须订正。"""
    assert not re.search(r"协议根为\s*`<版本目录>/`", upgrading), "该句应订正（整仓形态实为 vdir/agate）"


# ---------------------------------------------------------------------------
# BDD-3 ③  文档块与来源不漂移
# ---------------------------------------------------------------------------

_BOUNDARY_LINE = re.compile(r"^(include|exclude|root-file)\s+\S")


def test_bdd_3_3_contract_block_equals_boundary_lines(contract, agate_scripts):
    """BDD-3 ③：UPGRADING 契约小节的边界 fenced 块条目集合 == agate_package.boundary_lines()（文档不得与来源各自维护）。"""
    assert contract, "UPGRADING.md 缺「结构契约」小节（批 F1a 待实现）"
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    blocks = []
    for b in _fences(contract):
        lines = [ln.strip() for ln in b.splitlines() if ln.strip()]
        if lines and all(_BOUNDARY_LINE.match(ln) for ln in lines):
            blocks.append(lines)
    assert len(blocks) == 1, f"契约小节应含且仅含一个边界 fenced 块（每行以 include/exclude/root-file 起头），实得 {len(blocks)}"
    doc_lines = blocks[0]
    lib_lines = list(pkg.boundary_lines())
    assert len(doc_lines) == len(set(doc_lines)), "文档块条目不得重复"
    assert set(doc_lines) == set(lib_lines), (
        f"仅文档: {sorted(set(doc_lines) - set(lib_lines))}；仅来源: {sorted(set(lib_lines) - set(doc_lines))}"
    )


# ---------------------------------------------------------------------------
# BDD-19  不宣称"零依赖"，声明 portable 的真实依赖
# ---------------------------------------------------------------------------

_ZERO_DEP = re.compile(r"零依赖|zero[- ]dependenc|no dependenc|无任何依赖", re.I)
_DOCS_19 = ("README.md", "README.zh-CN.md", "agate/UPGRADING.md", "agate/SETUP.md")


@pytest.mark.parametrize("rel", _DOCS_19)
def test_bdd_19_no_zero_dependency_claim(rel):
    """BDD-19：README / README.zh-CN / UPGRADING / SETUP 不区分大小写 grep「零依赖」类措辞 0 命中。"""
    text = _read(H.REPO_ROOT / rel)
    assert _ZERO_DEP.search(text) is None, f"{rel} 出现零依赖类宣称: {_ZERO_DEP.search(text).group(0)!r}"


@pytest.fixture(scope="module")
def portable(upgrading):
    return _section(upgrading, r"portable 安装")


def test_bdd_19_portable_section_declares_real_dependencies(portable):
    """BDD-19：portable 小节含 python3 与 pyyaml 依赖声明，并写明"无需 git，但 agate-changes.py 等依赖 agate git 仓库的工具不可用"。"""
    assert portable, "UPGRADING.md 缺「portable 安装」小节（批 F1a 待实现）"
    assert "python3" in portable
    assert re.search(r"pyyaml", portable, re.I)
    assert re.search(r"无需\s*git", portable), "应写明「无需 git」"
    assert "agate-changes" in portable, "应点名 agate-changes.py 等依赖 git 仓库的工具不可用"
    assert _ZERO_DEP.search(portable) is None


def test_bdd_17_portable_section_command_block_shape(portable):
    """BDD-17 / P2 §3.5：文档命令块即验收脚本——含 sha256 校验、tar 解压、--adopt、--check --portable、软链基址守卫；
    -B 原因与 SHA256SUMS 完整性局限（只防损坏、不认证发布者）如实写明。"""
    assert portable, "UPGRADING.md 缺「portable 安装」小节（批 F1a 待实现）"
    blocks = [b for b in _fences(portable) if "tar" in b]
    assert blocks, "portable 小节应含 bash 命令块"
    cmd = blocks[0]
    for token in ("sha256sum", "tar -xzf", "--adopt", "--check --portable", "-L"):
        assert token in cmd, f"命令块缺 {token!r}"
    assert "python" "3 -B" in cmd, "从版本目录内运行脚本须带 -B（避免留下 __pycache__）"
    assert "SHA256SUMS" in portable and "认证" in portable, "应如实说明 SHA256SUMS 只防下载损坏、不认证发布者"
    assert re.search(r"Source code|整仓", portable), "应提示下载指引：推荐本体 tarball，GitHub 自动 Source code 包为整仓"


# ---------------------------------------------------------------------------
# BDD-39 ①–⑤  UPGRADING 文档面 legacy 表述改写
# ---------------------------------------------------------------------------


def test_bdd_39_1_lifecycle_table_is_single_layout_with_migration_steps(lifecycle):
    """BDD-39 ①：「安装 / 迁移 / 更新 / 回退对照表」不再有 legacy 列（单布局表），「迁移」行写迁移三步。"""
    sec = _section(lifecycle, r"对照表")
    assert sec, "生命周期节缺「对照表」小节"
    sec = sec.split("\n#### ", 1)[0]  # 不含后面的「回退」子节表格
    rows = _table_rows(sec)
    assert rows, "对照表应是 markdown 表格"
    flat = "\n".join(" | ".join(r) for r in rows)
    assert not re.search(r"legacy|软链布局", flat, re.I), "对照表不应再有 legacy / 软链布局列"
    assert "git pull" not in flat, "legacy 更新指令 git pull 不应留在对照表"
    mig = [r for r in rows if r and "迁移" in r[0]]
    assert mig, "对照表应保留「迁移」行"
    text = " ".join(mig[0])
    for step in ("mv ~/.agate ~/.agate.bak", "mkdir -p ~/.agate", "install.sh"):
        assert step in text, f"「迁移」行缺三步片段 {step!r}"


def test_bdd_39_2_resolution_priority_is_three_layers(lifecycle):
    """BDD-39 ②：解析优先级表无第 5 行，文字口径为「三层」，不再出现「五层」/ legacy 兜底行。"""
    sec = _section(lifecycle, r"解析优先级")
    assert sec, "生命周期节缺「路径层次与解析优先级」小节"
    assert "三层" in sec, "文字口径应为「三层：env → 项目声明 → current」"
    assert "五层" not in sec, "不应再有「五层」"
    for row in _table_rows(sec):
        assert row[0] != "5", f"解析优先级表不应有第 5 行: {row}"
        assert "无版本指针" not in " ".join(row), "legacy 兜底行应删除"


def test_bdd_39_3_legacy_no_behavior_change_promise_rewritten(upgrading):
    """BDD-39 ③：v0.50.0 节内「存量旧软链用户行为不变（红线）」承诺已改写为"legacy 已移除（v0.73.0 BREAKING）+ 迁移指引"。"""
    assert f"存量{_OLD_SINGLE_LINK}用户不跑新工具时行为不变" not in upgrading
    assert "无强制迁移（" + "legacy" + " 兜底" not in upgrading
    v050 = _section(upgrading, r"^v0\.50\.0", level=3)
    assert v050, "v0.50.0 历史节应仍在"
    assert re.search(r"v0\.73\.0", v050), "改写后的 v0.50.0 节应指向 v0.73.0 的移除说明"
    assert "BREAKING" in v050 or "迁移" in v050


@pytest.fixture(scope="module")
def v0730(upgrading):
    return _section(upgrading, r"^v0\.73\.0", level=3)


def test_bdd_39_4_v0730_section_content(upgrading, v0730):
    """BDD-39 ④：`### v0.73.0` 节：BREAKING 标注 + 影响面 + 迁移三步 + install.sh 无参语义 + 废弃 env + Release / portable + 升级自举说明。"""
    assert v0730, "UPGRADING.md 缺 `### v0.73.0` 节"
    assert "BREAKING" in v0730
    for token in ("mv ~/.agate ~/.agate.bak", "mkdir -p ~/.agate", "install.sh", "AGATE_REPO_DIR", "AGATE_SYMLINK"):
        assert token in v0730, f"v0.73.0 节缺 {token!r}"
    assert re.search(r"软链", v0730) and re.search(r"存量|影响", v0730), "应写明影响面（仅软链用户）"
    assert "Release" in v0730 and "portable" in v0730, "应写明新增 Release / portable"
    assert "整仓" in v0730, "P2 §3.8 R-1：应写明 v0.72 用户升级得到的 v0.73.0 自身为旧整仓形态（仍可解析）"
    # 新节位于 v0.72.0 节之前（本节按版本倒序）
    assert upgrading.index("### v0.73.0") < upgrading.index("### v0.72.0")


def test_bdd_39_5_section3_history_note_and_history_sections_preserved(upgrading):
    """BDD-39 ⑤：§3 顶部有 v0.73.0 起旧软链布局不再支持的注记；历史版本节相对不可变基线 75a8102 原文保留
    （v0.50.0 节仅允许因 ③ 改写含旧承诺表述的行）。"""
    sec3 = _section(upgrading, r"已知破坏性变更", level=2)
    assert sec3, "缺「## 3. 已知破坏性变更」"
    top = sec3.split("\n### ", 1)[0]
    assert "v0.73.0" in top and "不再支持" in top, "§3 顶部应加注记：v0.73.0 起旧软链布局不再支持，历史节仅作历史记录"
    base = H.run_git(H.REPO_ROOT, "show", f"{BASE_SHA}:agate/UPGRADING.md", check=False)
    assert base.returncode == 0, f"基线提交 {BASE_SHA} 不可达（CI 需 fetch-depth: 0）: {base.stderr.decode('utf-8', 'replace')}"
    base_text = base.stdout.decode("utf-8")
    base_titles = [t for _ln, lv, t in _headings(_section(base_text, r"已知破坏性变更", level=2)) if lv == 3]
    assert len(base_titles) >= 30, f"基线历史节数量异常（基线实测 34 节）: {len(base_titles)}"
    for title in base_titles:
        old = _section(base_text, "^" + re.escape(title) + "$", level=3)
        new = _section(upgrading, "^" + re.escape(title) + "$", level=3)
        assert new, f"历史节 {title!r} 被删除"
        if old == new:
            continue
        assert title.startswith("v0.50.0"), f"历史节 {title!r} 被改写（仅 v0.50.0 因 ③ 允许）"
        removed = [
            ln[1:] for ln in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
            if ln.startswith("-") and not ln.startswith("---")
        ]
        for ln in removed:
            assert re.search(_OLD_SINGLE_LINK + "|legacy" + " 兜底", ln), f"v0.50.0 节被改写了与 ③ 无关的行: {ln!r}"


# ---------------------------------------------------------------------------
# BDD-50 ①（不易腐部分）  v0.73.0 变更记录如实标注 BREAKING 并指向迁移指引
# ---------------------------------------------------------------------------


def _changelog_v0730_or_unreleased():
    text = _read(CHANGELOG)
    for pat in (r"^\[0\.73\.0\]", r"^\[Unreleased\]"):
        sec = _section(text, pat, level=2)
        if sec:
            return sec
    return ""


def test_bdd_50_1_changelog_marks_breaking_and_points_to_migration_guide():
    """BDD-50 ①：CHANGELOG 的 v0.73.0 内容（发版前在 [Unreleased]，发版后在 [0.73.0]）含 BREAKING 标注与 UPGRADING 迁移指引指针。
    版本号 / badge / CHECK 7 / CHECK 13 一致性由 consistency 脚本在 P8 验收（见 P3-test-cases.md §7），此处不写死版本号。"""
    sec = _changelog_v0730_or_unreleased()
    assert sec, "CHANGELOG 缺 [0.73.0] / [Unreleased] 段"
    assert "BREAKING" in sec, "v0.73.0 变更记录应标注 BREAKING（删除旧软链布局支持）"
    assert "UPGRADING" in sec, "应指向 agate/UPGRADING.md 迁移指引"
