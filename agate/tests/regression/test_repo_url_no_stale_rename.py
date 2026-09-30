# tests/regression/test_repo_url_no_stale_rename.py — 回归测试：TAG0025 Agateon 品牌改名
# （RM-AG0035 剩余工作② Phase 0-1；P1-requirements.md BDD-1~10 的 A 类测试落地，P3 test-designer）
#
# 兜底职责（重要，不是普通回归测试）：
#   P2-review.md「测试缺口」节已确认 gate_commands.P5_bdd4to8_new_url_present 只验证"新 URL
#   randomgitsrc/agateon 在文件内至少出现一次"，不验证"旧 URL randomgitsrc/agate 已被完全清除"
#   ——单靠那条 gate key 拦不住"README.md 两处 URL 只改一处"这类部分修复（BDD-7/BDD-8 明确禁止）。
#   本文件的 test_bdd_4~test_bdd_8 显式补上这个缺口：每个断言都同时覆盖两个方向——
#     ① 该文件不含字面 randomgitsrc/agate\b（旧 URL 已清除，word-boundary 排除 agateon 误判）
#     ② 该文件含字面 randomgitsrc/agateon（新 URL 已存在）
#   本文件同时承担 gate_commands.P5_bdd4to8_new_url_present 未覆盖的旧 URL 完全清除校验。
#
#   test_bdd_10_* 还额外兜底了 gate_commands.P5_bdd10_residual_scan 自身的一个已知盲区：
#   该 gate key 的排除正则里，P2 architect 自行追加排除了 5 个核心文件本身（install.sh: /
#   README.md: / README.zh-CN.md: / agate-install.py: / agate-changes.py:），这 5 条排除项不
#   属于 P1 BDD-10 声明的 5 类豁免（P2-review.md 核查项 3 已指出这是 gate_commands 的自行追加、
#   未在"5 类豁免"叙述里说明理由的排除项）。若全仓残留扫描沿用 gate_commands 的排除正则，改名前
#   这 7 处核心文件的旧 URL 命中会被排除正则悄悄吞掉，扫描"看起来"是 0 残留，但这是假阴性——
#   本文件的 test_bdd_10_* 只应用 P1-requirements.md BDD-10 原文声明的 5 类豁免（不含 P2 额外
#   追加的核心文件排除），因此改名前会真实命中这 7 处、产生真红灯；改名后 7 处清除、其余位置
#   未新增旧 URL，才会转绿。
#
# 三层解耦原则边界（P1 §1）：本文件只断言"外部品牌层"（仓库 URL / 品牌声明 / CHANGELOG 条目），
# 不触碰 agate/ 目录名、agate-workspace/、~/.agate、AGATE_*、agate-*.py 文件名、agate_common ——
# 这些内部命名空间永久保留，任何断言都不应要求它们改名。

import os
import re
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 公共常量与 fixture
# ---------------------------------------------------------------------------

OLD_URL_PATTERN = re.compile(r"randomgitsrc/agate\b")
NEW_URL = "randomgitsrc/agateon"

# Phase 1 核心 7 处更新点所在的 5 个文件（P2-design.md §0.1）
CORE_FILES = [
    "install.sh",
    "agate/scripts/agate-install.py",
    "agate/scripts/agate-changes.py",
    "README.md",
    "README.zh-CN.md",
]

# BDD-10 的豁免清单：P1-requirements.md 第 4 节 BDD-10 原文声明的 5 类（含 [BASELINE_CHANGE]
# 追加的第 5 类），刻意不包含 gate_commands.P5_bdd10_residual_scan 自行追加的核心文件排除
# （那 5 条排除项不属于本 BDD 的豁免清单，见文件顶部注释）。
_EXEMPT_PATH_PREFIXES = (
    "archived/",
    "agate-workspace/tasks/",
    "agate-workspace/archived/",
)
_EXEMPT_EXACT_FILES = (
    "docs/design-notes/agateon-trademark-research.md",
    "docs/superpowers/specs/2026-08-15-docs-suite-review.md",
    "HANDOFF-TAG0025.md",
    "docs/design-notes/design-rename-execution.md",
)

_SCAN_INCLUDE_EXTS = {".md", ".py", ".sh", ".yml", ".yaml"}
# canonical scratch（platform-notes「受限 harness 通用约束」约定 1：`<项目根>/.agate-tmp/`，
# `AGATE_TMP_DIR` 可覆盖）**必须排除**：其内容按定义被 VCS 忽略、且常含**整仓副本**（变异测试用），
# 副本里的历史旧 URL 会污染本扫描 ⇒ 本机红而 CI 绿（2026-09-30 实测）。
# 与 check-protocol-consistency.py::iter_md_files 的同类排除保持一致。
# scratch 目录名：与 `check-protocol-consistency.py` 的解析**同源**——
# `AGATE_TMP_DIR` 非空取 basename，否则回退 `.agate-tmp`（`or` 兜底，与
# `check-gate.py` 的 `_tmp_dir_rel()` 同款；本仓反例 7 的教训：
# 用 `os.environ[...]` 直取会在值非法/为空时与脚本行为分歧）。
_SCRATCH_DIR_NAME = os.path.basename(os.environ.get("AGATE_TMP_DIR") or ".agate-tmp")
_SCAN_EXCLUDE_DIRS = {".git", ".worktrees", ".agate-tmp", _SCRATCH_DIR_NAME}


@pytest.fixture(scope="session")
def repo_root(agate_root):
    """仓库根目录（含 README.md / install.sh / CHANGELOG.md），是 agate_root（agate/）的父目录。"""
    root = agate_root.parent
    assert (root / "README.md").is_file(), f"FATAL: {root} 下找不到 README.md，agate_root 推导错误"
    return root


def _read(repo_root, rel_path):
    return (repo_root / rel_path).read_text(encoding="utf-8")


def _assert_old_cleared_new_present(text, label):
    assert NEW_URL in text, f"{label}: 新 URL {NEW_URL} 未出现（改名尚未落地）"
    stale = OLD_URL_PATTERN.search(text)
    assert stale is None, (
        f"{label}: 仍残留旧 URL 字面命中 {stale.group(0)!r}"
        f"（word-boundary 排除 agateon 误判后仍命中，说明只改了一部分，BDD-7/8 明确禁止这种部分修复）"
    )


def _is_exempt(rel_posix, self_rel_posix):
    if rel_posix == self_rel_posix:
        # 本测试文件自身：文件顶部注释/docstring 出于说明目的引用了字面 "randomgitsrc/agate"
        # 字符串（描述兜底职责、断言逻辑），不是产品/文档层的活跃品牌引用；不排除会导致本测试
        # 扫描自身命中自己，属自指假阳性，与 P1 BDD-10 排除历史性/说明性引用同理（豁免依据类比
        # 第 3.2 节"边界案例"判定方法论：撰写说明当下对旧字符串的引用，非需要被替换的活跃品牌层）。
        return True
    if rel_posix in _EXEMPT_EXACT_FILES:
        return True
    return any(rel_posix.startswith(prefix) for prefix in _EXEMPT_PATH_PREFIXES)


def _scan_residual_old_url(repo_root):
    """按 P1-requirements.md BDD-10 原文 5 类豁免清单扫描全仓旧 URL 残留（不采用
    gate_commands.P5_bdd10_residual_scan 额外追加的核心文件排除，见文件顶部注释兜底职责说明）。
    """
    self_rel = Path(__file__).resolve().relative_to(repo_root).as_posix()
    hits = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in _SCAN_EXCLUDE_DIRS]
        for fname in filenames:
            if Path(fname).suffix not in _SCAN_INCLUDE_EXTS:
                continue
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(repo_root).as_posix()
            if _is_exempt(rel, self_rel):
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if OLD_URL_PATTERN.search(line):
                    hits.append(f"{rel}:{lineno}:{line.strip()}")
    return hits


# ---------------------------------------------------------------------------
# BDD-1 / BDD-2：品牌声明（Phase 0）
# ---------------------------------------------------------------------------


def test_bdd_1_readme_en_brand_statement_first_screen(repo_root):
    """README.md 首屏（前 15 行）须含 "Agateon (formerly agate)"（新旧品牌名同时出现）。"""
    head = "\n".join(_read(repo_root, "README.md").splitlines()[:15])
    assert "Agateon (formerly agate)" in head, (
        "README.md 首屏未找到品牌声明 'Agateon (formerly agate)'（改名前的预期红灯）"
    )


def test_bdd_2_readme_zh_brand_statement_first_screen(repo_root):
    """README.zh-CN.md 首屏（前 15 行）须同时含 "Agateon" 与 "agate" 两个品牌词（不要求逐字
    照搬英文版句式，但两个品牌词缺一不可）。
    """
    head = "\n".join(_read(repo_root, "README.zh-CN.md").splitlines()[:15])
    assert "Agateon" in head, "README.zh-CN.md 首屏未找到新品牌词 'Agateon'（改名前的预期红灯）"
    assert "agate" in head, "README.zh-CN.md 首屏未找到旧品牌词 'agate'（品牌沿革表述缺失）"


# ---------------------------------------------------------------------------
# BDD-3：CHANGELOG [Unreleased] 段 + TAG0025 条目
# ---------------------------------------------------------------------------


def test_bdd_3_changelog_unreleased_section_above_0_63_0(repo_root):
    """CHANGELOG.md 须含 TAG0025 品牌改名的发布段，位于 [0.63.0] 段之上。

    [P8_TEST_FIX: 本测试最初（P3/P4 阶段）断言"改名前 CHANGELOG 顶部应新增 [Unreleased] 段"，
    这是一次性 TDD 验收事实——该事实已在 v0.64.0 发布时永久兑现（[Unreleased] 转正为
    [0.64.0]）。作为永久回归测试，继续断言"存在 [Unreleased] 段"在发布后必然恒假（每次发布都会
    清空 Unreleased），会让本测试永久变红。P8 阶段改为断言"TAG0025 的发布记录永久存在于
    [0.63.0] 段之上"这一不随时间变化的历史事实，函数名保留不改（避免 P3-test-cases.md 的函数名
    引用失效），仅修正断言语义使其对"发布"这一动作幂等。]
    """
    text = _read(repo_root, "CHANGELOG.md")
    tag0025_release_match = re.search(r"^## \[0\.64\.0\]", text, re.MULTILINE)
    assert tag0025_release_match is not None, (
        "CHANGELOG.md 未找到 TAG0025 对应的 '## [0.64.0]' 发布段（v0.64.0 发布时由 "
        "[Unreleased] 转正，此后应永久存在于 CHANGELOG 历史中）"
    )
    released_match = re.search(r"^## \[0\.63\.0\]", text, re.MULTILINE)
    assert released_match is not None, "CHANGELOG.md 找不到 [0.63.0] 段，无法比较相对位置"
    assert tag0025_release_match.start() < released_match.start(), (
        "'## [0.64.0]'（TAG0025 发布段）必须出现在 '## [0.63.0]' 段之上"
        "（CHANGELOG 版本段应保持新→旧的时间倒序排列）"
    )


def test_bdd_3_changelog_tag0025_entry_under_unreleased(repo_root):
    """`[0.64.0]` 发布段下须永久含至少一条描述 TAG0025（品牌改名 Phase 0-1）的条目。

    [P8_TEST_FIX: 同上一条，语义不变（"改名记录确实被写进了这次发布"），只是不再依赖发布后
    必然消失的 [Unreleased] 包装，改断言已转正的 [0.64.0] 段内容，函数名保留不改。]
    """
    text = _read(repo_root, "CHANGELOG.md")
    tag0025_release_match = re.search(r"^## \[0\.64\.0\]", text, re.MULTILINE)
    if tag0025_release_match is None:
        pytest.fail(
            "CHANGELOG.md 未找到 '## [0.64.0]' 发布段，无法判定 TAG0025 条目是否落在段内"
        )
    next_section_match = re.search(r"^## \[", text[tag0025_release_match.end():], re.MULTILINE)
    section_end = (
        tag0025_release_match.end() + next_section_match.start()
        if next_section_match is not None
        else len(text)
    )
    section_body = text[tag0025_release_match.end():section_end]
    assert "TAG0025" in section_body, (
        "'## [0.64.0]' 发布段下未找到 TAG0025 条目"
    )


# ---------------------------------------------------------------------------
# BDD-4 ~ BDD-8：Phase 1 核心 7 处硬编码 URL（双方向断言：旧 URL 清除 + 新 URL 存在）
# ---------------------------------------------------------------------------


def test_bdd_4_install_sh_new_url_and_old_url_cleared(repo_root):
    """install.sh 第 24 行（克隆入口）：randomgitsrc/agate → randomgitsrc/agateon。"""
    _assert_old_cleared_new_present(_read(repo_root, "install.sh"), "install.sh")


def test_bdd_5_agate_install_py_new_url_and_old_url_cleared(repo_root):
    """agate/scripts/agate-install.py 第 55 行（DEFAULT_REPO_URL 常量）：新仓名。"""
    _assert_old_cleared_new_present(
        _read(repo_root, "agate/scripts/agate-install.py"), "agate/scripts/agate-install.py"
    )


def test_bdd_6_agate_changes_py_new_url_and_old_url_cleared(repo_root):
    """agate/scripts/agate-changes.py 第 116 行（更新提示文案内嵌 URL）：新仓名。"""
    _assert_old_cleared_new_present(
        _read(repo_root, "agate/scripts/agate-changes.py"), "agate/scripts/agate-changes.py"
    )


def _locate_line(lines, needle, fallback):
    """按内容定位行，找不到返回 fallback。

    不依赖行号——README 顶部是品牌展示区，2026-08-26 加入 logo-lockup <picture> 块后
    badge/安装入口行号整体下移，硬编码行号会让"badge 与安装入口须同批指向新仓名"这一
    断言意图被无关的头部内容变更误伤（PR #217 CI 实证）。
    """
    for line in lines:
        if needle in line:
            return line
    return fallback


def test_bdd_7_readme_en_badge_and_install_entry_new_url_and_old_cleared(repo_root):
    """README.md 的 badge 行与 curl 安装入口行须同批指向新仓名，不允许只改其中一行
    （badge 是 URL 硬编码点的一种，不是独立于安装入口的另一类工作）。

    [TEST_FIX: 原实现硬编码"第 5 行=badge、第 29 行=安装入口"。README 顶部是品牌展示区，
    加入 logo-lockup <picture> 块后行号下移，硬编码行号误判（PR #217 CI FAIL）。改为按内容
    定位：badge=含 img.shields.io 的版本徽标行，安装入口=含 raw.githubusercontent.com 且
    install.sh 的 curl 行；断言意图不变——两条 URL 硬编码点必须同时指向 randomgitsrc/agateon，
    任一单独回退仍会被拦。]
    """
    text = _read(repo_root, "README.md")
    _assert_old_cleared_new_present(text, "README.md")
    lines = text.splitlines()
    badge_line = _locate_line(lines, "img.shields.io", "")
    install_line = _locate_line(lines, "raw.githubusercontent.com", "")
    assert NEW_URL in badge_line, f"README.md badge 行未指向 {NEW_URL}：{badge_line!r}"
    assert NEW_URL in install_line, (
        f"README.md 安装入口行未指向 {NEW_URL}：{install_line!r}"
    )


def test_bdd_8_readme_zh_badge_and_install_entry_new_url_and_old_cleared(repo_root):
    """README.zh-CN.md 的 badge 行与 curl 安装入口行须同批指向新仓名。

    [TEST_FIX: 同 test_bdd_7，行号改为按内容定位，断言意图不变。]
    """
    text = _read(repo_root, "README.zh-CN.md")
    _assert_old_cleared_new_present(text, "README.zh-CN.md")
    lines = text.splitlines()
    badge_line = _locate_line(lines, "img.shields.io", "")
    install_line = _locate_line(lines, "raw.githubusercontent.com", "")
    assert NEW_URL in badge_line, f"README.zh-CN.md badge 行未指向 {NEW_URL}：{badge_line!r}"
    assert NEW_URL in install_line, (
        f"README.zh-CN.md 安装入口行未指向 {NEW_URL}：{install_line!r}"
    )


# ---------------------------------------------------------------------------
# BDD-9：批次原子性（Phase 1 核心 7 处更新落在同一 commit）
# ---------------------------------------------------------------------------
#
# 时序说明（呼应 dispatch-context 约束 4）：本用例复刻 gate_commands.P5_bdd9_atomic_commit 的
# 真实判定逻辑（`git log -1 --format=%H -- <file>` 逐文件比对 SHA 是否一致），不是一个和真正
# 判定逻辑无关的假断言。但它的"有意义程度"随阶段变化：
#   - P3/P4 阶段（当前）：这些文件各自最近一次改动的 commit 并非同一个（各自独立演进而来），
#     SHA 天然不一致 → 断言失败 → 真红灯，但红灯原因是"批次 commit 尚未发生"，而非"实现有 bug"。
#   - P4 implementer 完成一次性 commit 之后：SHA 会趋于一致 → 断言转绿，且与
#     gate_commands.P5_bdd9_atomic_commit 在 P5 阶段的复跑结果同源一致。
#   - 最终以 P5/P6 阶段 gate_commands.P5_bdd9_atomic_commit 的复跑结果为准（可独立于 pytest
#     环境重跑，是这条 BDD 的权威判定源）。


def test_bdd_9_seven_urls_same_commit_batch_atomicity(repo_root):
    """Phase 1 核心 7 处更新点（6 个文件：install.sh / agate-install.py / agate-changes.py /
    README.md / README.zh-CN.md / CHANGELOG.md）须落在同一个 commit 的 diff 中。

    [P8_TEST_FIX: 原实现用 `git log -1 -- <file>`（"这个文件最近一次改动是哪个 commit"）逐文件
    比对 SHA 是否相同——这在 P4-P7 阶段成立，但该断言会被这些文件之后任何一次合法后续改动打破
    （如 P8 阶段 bump README 版本号 badge，最近一次改动就变成了 P8 commit），不是真正意义上的
    永久回归检查，只是"截至目前这些文件没再被碰过"的偶然巧合。批次原子性这个历史事实本身（commit
    751f421a... 是否确实同批改了这 6 个文件）是不随时间变化的 git 历史事实，改为直接核实该具体
    commit 的 diff 覆盖这 6 个文件，不再依赖"最近一次改动"这个会被后续任意合法改动打破的相对
    判据。]
    """
    atomic_commit = "751f421a4c36becd657ab12fed0e80cd7423bef3"
    proc = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", atomic_commit],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, (
        f"commit {atomic_commit} 不存在或无法读取 diff（stderr: {proc.stderr!r}）"
    )
    changed_files = set(proc.stdout.strip().splitlines())
    files = [*CORE_FILES, "CHANGELOG.md"]
    missing = [f for f in files if f not in changed_files]
    assert not missing, (
        f"批次原子性 commit {atomic_commit} 的 diff 未覆盖以下文件：{missing}"
        f"（该 commit 实际改动文件：{sorted(changed_files)}）"
    )


# ---------------------------------------------------------------------------
# BDD-10：全仓无旧仓库 URL 残留（含显式豁免清单）
# ---------------------------------------------------------------------------


def test_bdd_10_repo_wide_residual_scan_zero_after_exemptions(repo_root):
    """对全仓（排除 .git/ 与 .worktrees/）执行 randomgitsrc/agate\\b 字面扫描，应用
    P1-requirements.md BDD-10 原文声明的 5 类豁免后，剩余命中数须为 0。

    刻意不复用 gate_commands.P5_bdd10_residual_scan 的排除正则（该 key 额外排除了 5 个核心
    文件本身，见文件顶部注释「兜底职责」），因此本用例在 Phase 1 核心 7 处更新落地前会真实
    命中这 7 处（已实测确认），落地后归零。
    """
    hits = _scan_residual_old_url(repo_root)
    assert hits == [], (
        "全仓残留旧 URL 扫描（按 P1 BDD-10 5 类豁免清单）命中数应为 0，当前命中：\n"
        + "\n".join(hits)
    )
