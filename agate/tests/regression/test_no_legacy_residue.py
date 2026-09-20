# tests/regression/test_no_legacy_residue.py — TAG0037 P3 组 C：旧软链布局（legacy）残留复发拦截（BDD-37，判据 10）
#
# 这是**永久回归**，断言的是长期不变量（"旧软链布局的旧称在全仓只允许出现在有限白名单里"），不是一次性交付事实：
#   * 扫描范围 = `git ls-files`，排除**任意层级**的 archived/（含 agate-workspace/archived/）、agate-workspace/tasks/、
#     docs/reviews/、docs/design-notes/（历史叙事）、node_modules/、package-lock.json 等 lock 文件、本测试文件自身；
#   * 大小写口径：不区分大小写（re.I）；模式集（P1 基线 S-18）：use_legacy、legacy[ _-]?(软链|symlink|layout)、单软链、软链兜底；
#   * 判定：① use_legacy 全范围命中 0（唯一例外 agate-workspace/debt/tech-debt.md：已 closed 债务叙事）；
#           ② 其余模式的命中文件集合 ⊆ 白名单 W（12 项，以 (路径, 理由) 列出；新增白名单项须显式修改本文件）；
#           ③ R 清零集合（12 个文件，P4 / F2 须改写）逐个 0 命中；
#           ④ 判据 10 的原口径 `use_legacy|legacy 软链布局` 在非 W 处无残留（由 ①② 蕴含，另留独立用例便于定位）。
# 当前（P4 前）红灯原因：残留未清零——命中文件 23 个 = R 集合 12 + W 集合 11（+ install-offline.py 预登记）；
#   `use_legacy` 仍在 agate/scripts/agate_common.py（批 E 删除）。属 B 类（断言失败），无 import 失败。
# 落地后的"应绿"形态（P3 已用 scratchpad 参照仓库自扫确认）：R 12 个文件清零，W 内文件可保留命中，use_legacy 仅 tech-debt.md。
#
# 数据安全：只读（git ls-files + 读文件），不写任何文件。
# 注意（跨组约束）：本模式集对**所有被 git 跟踪的文件**生效——新增的测试 / 脚本 / 文档不得在源码里直接写出这四种旧称字面量
#   （测试中需引用它们时用字符串拼接构造，例如 "use_" + "legacy"），除非该文件在下方白名单 W 内。

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SELF_REL = "agate/tests/regression/test_no_legacy_residue.py"

PATTERNS = {
    "use_legacy": re.compile(r"use_legacy", re.I),
    "legacy-symlink-layout": re.compile(r"legacy[ _-]?(软链|symlink|layout)", re.I),
    "单软链": re.compile("单软链", re.I),
    "软链兜底": re.compile("软链兜底", re.I),
}

# 目录级排除（路径分量匹配任意层级 / 前缀匹配）
_EXCLUDED_ANYWHERE_COMPONENTS = ("archived", "node_modules")
_EXCLUDED_PREFIXES = ("agate-workspace/tasks/", "docs/reviews/", "docs/design-notes/")
_LOCK_FILES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "uv.lock")

USE_LEGACY_EXCEPTION = "agate-workspace/debt/tech-debt.md"

# W 白名单（12 项，(路径, 理由)）：这些文件允许在**其余三种模式**上保留命中（use_legacy 一律 0，唯一例外见上）
WHITELIST_W = {
    # (a) 历史 / 叙事
    "CHANGELOG.md": "append-only 发布记录（含 v0.73.0 BREAKING 条目）",
    "agate/UPGRADING.md": "v0.73.0 迁移节 + 历史版本节（按小节标题界定）",
    "agate/adr.md": "ADR-009 历史条目 + 「已被 v0.73.0 取代」注记",
    "agate-workspace/debt/tech-debt.md": "已 closed 债务叙事",
    # (b) fail-closed 迁移文案的承载文件（有限枚举，其余代码文件不得含旧称）
    "install.sh": "软链守卫 + 迁移三步 heredoc",
    "agate/scripts/agate-install.py": "软链 fail-closed 文案常量",
    "agate/scripts/install-offline.py": "软链 fail-closed 文案（预登记，现状无命中）",
    "agate/scripts/agate_common.py": "软链检测 + 迁移提示（resolve 侧）",
    "agate/scripts/agate-resolve.py": "终态失败追加迁移提示",
    "agate/scripts/agate-summary.py": "软链基址迁移提示",
    # (c) 断言 fail-closed 的测试（场景名 / 注释可含旧称）
    "agate/tests/unit/test_agate_version_install.py": "断言安装侧软链 fail-closed",
    "agate/tests/unit/test_agate_version_resolve.py": "断言解析侧软链 fail-closed",
}

# R 清零集合（12 项）：现状均有命中，落地时须改写为 0 命中
R_CLEAR = (
    "AGENTS.md",
    "README.md",
    "README.zh-CN.md",
    "agate/AGENTS.md",
    "agate/SETUP.md",
    "agate/WORKFLOW.md",
    "agate/orchestrator-template.md",
    "agate/platform-notes.md",
    "agate/scripts/README.md",
    "agate/tests/unit/test_dsh_preset.py",
    "docs/guides/project-map.md",
    "docs/guides/worktree-dogfooding-guide.md",
)


def in_scope(rel):
    """BDD-37 扫描范围过滤（纯函数，便于自守卫用例直接测试）。"""
    parts = rel.split("/")
    if rel == SELF_REL:
        return False
    if any(p in _EXCLUDED_ANYWHERE_COMPONENTS for p in parts[:-1]):
        return False
    if any(rel.startswith(pre) for pre in _EXCLUDED_PREFIXES):
        return False
    return parts[-1] not in _LOCK_FILES


def scan_text(text):
    """返回文本命中的模式名集合。"""
    return {name for name, pat in PATTERNS.items() if pat.search(text)}


def _tracked_files():
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], capture_output=True, timeout=120
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return [p for p in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


@pytest.fixture(scope="module")
def hits():
    """{相对路径: {命中的模式名}}（仅 git 跟踪、在范围内、可读的文本文件）。"""
    out = {}
    for rel in _tracked_files():
        if not in_scope(rel):
            continue
        path = REPO_ROOT / rel
        try:
            raw = path.read_bytes()
        except OSError:
            continue  # 已删除但尚未提交的跟踪文件 / 断链
        if b"\0" in raw[:8192]:
            continue  # 二进制
        found = scan_text(raw.decode("utf-8", "replace"))
        if found:
            out[rel] = found
    return out


# ---------------------------------------------------------------------------
# 扫描器自守卫（有意应绿：锁定范围 / 大小写口径，防"扫描器悄悄失效"）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel,expected",
    [
        ("agate-workspace/archived/x.md", False),
        ("docs/archived/y.md", False),
        ("agate-workspace/tasks/TAG0001-x/P1.md", False),
        ("docs/reviews/r.md", False),
        ("docs/design-notes/d.md", False),
        ("site/node_modules/a/b.md", False),
        ("site/package-lock.json", False),
        (SELF_REL, False),
        ("agate/scripts/agate_common.py", True),
        ("README.md", True),
        ("agate-workspace/debt/tech-debt.md", True),
        ("agate-workspace/roadmap/roadmap.md", True),
        ("docs/guides/project-map.md", True),
    ],
)
def test_bdd_37_scan_scope_filter(rel, expected):
    """BDD-37 扫描范围：任意层级 archived/、tasks / reviews / design-notes、node_modules、lock 文件与自身被排除。"""
    assert in_scope(rel) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("USE_LEGACY = 1", {"use_legacy"}),
        ("Legacy 软链布局", {"legacy-symlink-layout"}),
        ("legacy-symlink", {"legacy-symlink-layout"}),
        ("legacy_layout", {"legacy-symlink-layout"}),
        ("LEGACY SYMLINK", {"legacy-symlink-layout"}),
        ("单软链布局", {"单软链"}),
        ("软链兜底", {"软链兜底"}),
        # 与软链无关的同名 legacy 不误伤（P1 扫描 B）
        ("legacy fields / judge_verdict_legacy / legacy docs/tasks layout", set()),
        ("指针是软链", set()),
    ],
)
def test_bdd_37_pattern_semantics_case_insensitive_and_no_collateral(text, expected):
    """BDD-37 模式集：re.I；四模式命中旧称，不误伤其它含义的 legacy。"""
    assert scan_text(text) == expected


def test_bdd_37_whitelist_and_clear_set_shape():
    """BDD-37 ③：W 白名单恰 12 项、R 清零集合恰 12 项且互不相交（R 与 W 现状并集 = 23 个命中文件）。"""
    assert len(WHITELIST_W) == 12 and len(R_CLEAR) == 12
    assert not (set(WHITELIST_W) & set(R_CLEAR))
    assert all(reason.strip() for reason in WHITELIST_W.values()), "白名单每项须给出理由"


# ---------------------------------------------------------------------------
# 永久回归断言（P4 落地前红灯）
# ---------------------------------------------------------------------------


def test_bdd_37_1_use_legacy_has_zero_hits_except_closed_debt_narrative(hits):
    """BDD-37 ①：`use_legacy` 全范围命中 0（唯一例外：已 closed 债务叙事 tech-debt.md）。"""
    offenders = sorted(rel for rel, found in hits.items() if "use_legacy" in found and rel != USE_LEGACY_EXCEPTION)
    assert offenders == [], f"use_legacy 残留（应彻底删除）: {offenders}"


def test_bdd_37_2_other_pattern_hits_are_subset_of_whitelist(hits):
    """BDD-37 ②：其余模式（含任意层级同义旧称）的命中文件集合 ⊆ 白名单 W；命中且不在 W 的文件逐个列出。"""
    offenders = sorted(rel for rel in hits if rel not in WHITELIST_W)
    assert offenders == [], f"非白名单文件含旧称（{len(offenders)} 个，须改写或显式登记白名单）: {offenders}"


@pytest.mark.parametrize("rel", R_CLEAR)
def test_bdd_37_3_clear_set_file_has_zero_hits(rel, hits):
    """BDD-37 ③：R 清零集合逐个文件 0 命中（现状均有命中，须改写；P4 批 F2 / E 交付）。"""
    assert os.path.isfile(REPO_ROOT / rel), f"R 清零集合文件不存在: {rel}"
    assert hits.get(rel, set()) == set(), f"{rel} 仍含旧称: {sorted(hits.get(rel, set()))}"


def test_bdd_37_4_original_p0_grep_has_no_residue_outside_whitelist(hits):
    """BDD-37 ④：判据 10 的原口径 `grep -rn "use_legacy\\|legacy 软链布局"` 在非 W 处无残留。"""
    original = re.compile(r"use_legacy|legacy[ _-]?软链布局", re.I)
    offenders = []
    for rel in _tracked_files():
        if not in_scope(rel) or rel in WHITELIST_W:
            continue
        try:
            raw = (REPO_ROOT / rel).read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:8192]:
            continue
        if original.search(raw.decode("utf-8", "replace")):
            offenders.append(rel)
    assert offenders == [], f"原口径残留: {sorted(offenders)}"
