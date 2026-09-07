# tests/unit/test_upgrading_lifecycle.py — TAG0032 断点三：update 统一入口（文档面）
# 被测：agate/UPGRADING.md「版本管理生命周期」新节 + README.md / README.zh-CN.md /
#       agate/SETUP.md 升级口径收敛（P4 实现 M7-M11）。
# BDD 映射（1:1，P1-requirements.md §3.3）：
#   BDD-10（两布局更新指令对齐 + 各自幂等）
#   BDD-11（生命周期节覆盖 安装/迁移/更新/回退 + hook 重装时机 + 根 scripts/ 副本维护语义）
#   BDD-12（4 条具体矛盾表述逐条收敛：v0.50.0 表格两行加指针 / v0.60-0.62 vs v0.66-0.68
#           hook 口径统一 / README×2 + SETUP 口径一致）
#   BDD-4 判据 3（根 ~/.agate/scripts/ 副本维护语义写入生命周期节，与 BDD-11 判据 3 交叉锁）
# 命名前缀 test_tag0032_bdd_N_。
# 平台无关：纯文本检索，无 symlink / 无 /tmp 字面量 / 无 python3 硬编码。
# 当前红灯（B 类，断言失败）：UPGRADING.md 无「版本管理生命周期」节。
#
# 附加回归项（BDD-12「非主判据」）：check-protocol-consistency.py --strict-errors-only
# EXIT 0 / 0 ERROR —— 基线即 0 ERROR，由 P2 §6 gate_commands.P5_consistency 常驻执行，
# 不在此新增始终绿的用例（P3 全部新增用例须红灯）。

import re

import pytest


def _read(path):
    return path.read_text(encoding="utf-8")


def _section(text, title, level="## "):
    """抽取 markdown 章节：从含 title 的 `level` 标题行起，到下一个同级/更高级标题止。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(level) and title in ln:
            start = i
            break
    if start is None:
        return ""
    depth = len(level.strip())
    out = [lines[start]]
    for ln in lines[start + 1 :]:
        m = re.match(r"^(#+)\s", ln)
        if m and len(m.group(1)) <= depth:
            break
        out.append(ln)
    return "\n".join(out)


def _v050_section(text):
    return _section(text, "v0.50.0", level="### ")


@pytest.fixture
def upgrading(agate_root):
    return _read(agate_root / "UPGRADING.md")


@pytest.fixture
def lifecycle_section(upgrading):
    return _section(upgrading, "版本管理生命周期")


def test_tag0032_bdd_10_update_commands_aligned_and_idempotent(upgrading, lifecycle_section):
    """BDD-10：两种布局的更新指令在文档面对齐且各自幂等。"""
    assert "版本管理生命周期" in upgrading, "UPGRADING.md 应新增「版本管理生命周期」节"
    sec = lifecycle_section
    assert sec, "「版本管理生命周期」节应可抽取"
    # legacy 布局：git pull + hook 判定口径
    assert "git pull" in sec, "legacy 布局更新指令应明确为 git pull"
    assert "install-hook.py" in sec, "legacy 更新应含『是否需重跑 install-hook.py』判定口径"
    # 版本布局：agate-install latest + 幂等
    assert re.search(r"agate-install(\.py)?\s+latest", sec), "版本布局更新应为 agate-install latest"
    assert "幂等" in sec, "版本布局更新应声明幂等（重复执行不报错、不重复建版本目录）"


def test_tag0032_bdd_11_lifecycle_section_covers_four_actions(lifecycle_section):
    """BDD-11：生命周期节覆盖 安装/迁移/更新/回退 + hook 重装时机 + 根 scripts/ 维护语义。"""
    sec = lifecycle_section
    assert sec, "「版本管理生命周期」节应存在"
    for action in ("安装", "迁移", "更新", "回退"):
        assert action in sec, f"生命周期节应覆盖动作：{action}"
    # hook 重装时机（薄壳固定 + resolve-entry 机制下通常无需随版本重装）
    assert "install-hook.py" in sec
    assert ("薄壳" in sec) or ("resolve-entry" in sec), "应写明 hook 重装时机口径"
    assert ("通常无需" in sec) or ("无需重跑" in sec) or ("无需随版本重装" in sec)
    # 根 ~/.agate/scripts/ 维护语义条目（决策 B1 副本）
    assert "~/.agate/scripts" in sec, "应含根 ~/.agate/scripts/ 维护语义条目"
    assert "副本" in sec, "决策 B1：根 scripts/ 建立方式为副本，须写明"


def test_tag0032_bdd_4_root_scripts_copy_semantics_documented(lifecycle_section):
    """BDD-4 判据 3（与 BDD-11 判据 3 交叉锁）：根 scripts/ 副本维护语义写入生命周期节——
    升级期须重跑 agate-install + repo/ 被删不影响副本可用性。"""
    sec = lifecycle_section
    assert sec, "「版本管理生命周期」节应存在"
    assert "副本" in sec
    assert re.search(r"重跑.*agate-install|agate-install.*刷新", sec), (
        "应写明副本方式升级期须重跑 agate-install latest 刷新"
    )
    assert "repo/" in sec, "应写明 repo/ 或版本目录被删对根入口副本的影响"


@pytest.mark.parametrize(
    "checklist_item",
    [
        "v050_root_scripts_row_pointer",
        "v050_upgrade_row_pointer",
        "hook_reinstall_unified_across_version_sections",
        "readme_setup_aligned",
    ],
)
def test_tag0032_bdd_12_doc_contradiction_converged(
    checklist_item, agate_root, upgrading, lifecycle_section
):
    """BDD-12：§4 扫描 4 列出的 4 条具体矛盾表述逐条收敛（命中『已收敛』或『历史叙事保留+指针』）。"""
    if checklist_item == "v050_root_scripts_row_pointer":
        v050 = _v050_section(upgrading)
        assert v050, "v0.50.0 节应可抽取"
        assert "scripts/（版本管理工具）" in v050, "v0.50.0 §① 表格『根含 scripts/』行应仍在（历史叙事）"
        assert "版本管理生命周期" in v050, (
            "该行应加『详见「版本管理生命周期」节』指针（doc/reality mismatch 收敛，I-4）"
        )
    elif checklist_item == "v050_upgrade_row_pointer":
        v050 = _v050_section(upgrading)
        assert "agate-install.py" in v050, "v0.50.0 §① 表格『升级 = agate-install.py』行应仍在"
        assert "版本管理生命周期" in v050, "『升级 = agate-install.py』行应加指向生命周期节的指针"
    elif checklist_item == "hook_reinstall_unified_across_version_sections":
        sec = lifecycle_section
        assert sec, "生命周期节应给 hook 重装统一判定口径"
        assert "install-hook.py" in sec
        assert ("复制模式" in sec) or ("Windows" in sec), (
            "统一口径应写明『仅 hook 薄壳 .sh 变更或 Windows 复制模式才重跑』"
        )
        assert (".sh" in sec) or ("薄壳" in sec)
    elif checklist_item == "readme_setup_aligned":
        readme = _read(agate_root.parent / "README.md")
        readme_zh = _read(agate_root.parent / "README.zh-CN.md")
        setup = _read(agate_root / "SETUP.md")
        # M10：README 快速上手补『进入版本布局』官方路径 install.sh --versions
        assert "install.sh --versions" in readme, "README.md 应补 install.sh --versions 官方路径"
        assert "install.sh --versions" in readme_zh, "README.zh-CN.md 应同步补 install.sh --versions"
        # M11：SETUP 升级节加指向生命周期节的指针，口径一致
        assert "版本管理生命周期" in setup, "SETUP.md 升级节应加指向 UPGRADING 生命周期节的指针"
