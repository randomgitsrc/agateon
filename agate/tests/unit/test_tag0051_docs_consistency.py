# agate/tests/unit/test_tag0051_docs_consistency.py — TAG0051 P3 红灯（文档/语料一致性）
#
# 覆盖 BDD（P1-requirements.md）：1 / 14 / 15。
#   * BDD-1：P8/READY 语料面（**六处**）内「tag 作为 P8 条件或 P8 动作」的表述**零命中**。
#     显式**排除**：`UPGRADING.md` 历史章节、`CHANGELOG.md` 发布产物、frozen 快照，以及
#     `P8-release.md` 中描述发布流程顺序 / CHECK 7 时序说明的行（非 P8 条件面）。
#   * BDD-14：`AGENTS.md` 版本发布清单 + `agate/git-integration.md` 的 tag 时点**全文统一**为
#     「先合 release PR → 合并后 main CI 绿 → 后打 tag」（不再出现 pre-merge 打 tag 的矛盾顺序）。
#   * BDD-15：发布失败处置显式规定「先评估回退 tag/Release 重打，仅当已被外部消费才出补丁」。
#
# 现行为（改动前）：六处语料仍写死 tag 条件/动作；两处文档 tag 时点矛盾且无失败处置
#   ⇒ 断言失败 = B 类红灯（实现未写，非测试自身错误）。
#
# 平台无关：只读仓库文本 + agate_root fixture；不裸 python3；不写字面系统临时目录。
#
# [DESIGN_GAP]（P1 BDD-1 可判定性补强 / P2 §1.1 M2 落点）：BDD-1 的「tag 作为 P8 条件/动作」
#   以**精炼的字面清单**判定（见 _FORBIDDEN_*）——清单取自改动前各文件的真实 tag 条件/动作
#   表述，P4 移除这些表述后即零命中；P8-release.md 的 CHECK 7 时序说明行不在清单内（显式排除）。

# BDD-1 语料面（六处，见 P1 BDD-1）
_P8_READY_FILES = (
    "agate/state-machine.md",
    "agate/phase-cards/P8-release.md",
    "agate/rules/state-transitions.md",
    "agate/rules/phases.yaml",
    "agate/dispatch-protocol.md",
    "agate/assets/execution-roles/implementer.md",
)

# 「tag 作为 P8 条件/动作」的字面清单（非 P8-release.md 的五处语料）。
_FORBIDDEN_COMMON = (
    "git tag",
    "tag 已创建",
    "tag 创建",
    "tag 检查",
    "先 tag",
    "commit + tag",
    "tag 由主 Agent",
    "VERSION_TAG_PREFIX",
)

# P8-release.md 专用的条件/动作短语（其 CHECK 7 时序说明行显式排除，不在清单内）。
_FORBIDDEN_P8CARD = (
    "git tag 已创建",
    "git commit/tag",
    "git commit / git tag",
    "同一 commit + tag",
    "bump-version / git commit / git tag",
)

_CI_MERGE_MARKERS = ("合并后", "main CI 绿", "CI 全绿", "CI 绿")


def _read(repo_root, rel):
    return (repo_root / rel).read_text(encoding="utf-8")


# ── BDD-1：P8/READY 语料面 tag 条件零残留 ───────────────────────────────────
def test_bdd_1_p8_ready_corpus_has_no_tag_conditions(agate_root):
    """BDD-1：六处语料中「tag 作为 P8 条件/动作」的表述零命中。"""
    repo_root = agate_root.parent
    violations = []
    for rel in _P8_READY_FILES:
        text = _read(repo_root, rel)
        patterns = _FORBIDDEN_P8CARD if rel.endswith("P8-release.md") else _FORBIDDEN_COMMON
        for pat in patterns:
            if pat in text:
                violations.append(f"{rel}: 含 tag 条件/动作表述 {pat!r}")
    assert not violations, (
        "BDD-1：P8/READY 语料面仍有「tag 作为 P8 条件或 P8 动作」的表述"
        "（tag 语义应已移出 READY/P8）：\n  " + "\n  ".join(violations)
    )


# ── BDD-14：tag 时点在发布文档中全文统一 ────────────────────────────────────
def _tag_timing_ok(text):
    """tag 步骤是否位于「合并后 CI 绿」之后（或 tag 步骤已整体移除）。"""
    presence = [text.find(m) for m in _CI_MERGE_MARKERS if text.find(m) != -1]
    tag_pos = text.find("git tag")
    if not presence:
        return False, "未出现「合并后 / CI 全绿」合并后验证标记"
    if tag_pos != -1 and tag_pos < min(presence):
        return False, "`git tag` 步骤位于「合并后 CI 绿」之前（矛盾顺序：先 push tag）"
    return True, ""


def test_bdd_14_agents_md_tag_timing_unified(agate_root):
    """BDD-14：`AGENTS.md` 的 tag 时点统一为「先合 PR → main CI 绿 → 后 tag」。"""
    text = _read(agate_root.parent, "AGENTS.md")
    ok, why = _tag_timing_ok(text)
    assert ok, f"BDD-14：AGENTS.md tag 时点未统一——{why}"


def test_bdd_14_git_integration_tag_timing_unified(agate_root):
    """BDD-14：`agate/git-integration.md` 的 tag 时点与 AGENTS.md 一致（无矛盾副本）。"""
    text = _read(agate_root.parent, "agate/git-integration.md")
    ok, why = _tag_timing_ok(text)
    assert ok, f"BDD-14：git-integration.md tag 时点未统一——{why}"


# ── BDD-15：发布失败处置显式规定 ─────────────────────────────────────────────
def test_bdd_15_release_failure_rollback_first(agate_root):
    """BDD-15：显式规定「先评估回退 tag/Release 重打，仅当已被外部消费才出补丁」（顺序二值可判）。"""
    repo_root = agate_root.parent
    text = _read(repo_root, "AGENTS.md")
    text += "\n" + _read(repo_root, ".github/workflows/release.yml")
    assert "回退" in text, "BDD-15：发布流程文档未规定「回退 tag/Release」处置"
    assert "重打" in text or "重新打 tag" in text, (
        "BDD-15：发布失败处置未规定「重打 tag/Release」"
    )
    assert "外部消费" in text or "已被消费" in text, (
        "BDD-15：未规定「仅当已被外部消费才出补丁」的边界"
    )
    i_rollback = text.find("回退")
    i_patch = text.find("补丁")
    assert i_patch == -1 or i_rollback < i_patch, (
        "BDD-15：处置顺序须为「先回退重打、后（仅在已被外部消费时）出补丁」"
    )
