# tests/unit/test_docs_assertions.py — 协议文档静态条文断言
# （TAG0019，BDD-11/12/14：ceremony 机制；TAG0020 增补，BDD-4/8/10：P6.5 judge 机制条文）
# 断言 ceremony 新机制的文档条文可 grep（P4 实现落协议文档后应存在；当前未实现 → 红）。
# 平台无关：读文件经 pathlib（agate_root fixture），无 shell / 无硬编码临时目录字面 / 无裸 python3。

import re
from pathlib import Path


def _read(agate_root, rel):
    return (Path(agate_root) / rel).read_text(encoding="utf-8")


def test_bdd_11_requirements_review_audits_declaration_vs_diff(
    agate_root
):
    """BDD-11：requirements-review 清单含「风险分级/裁剪声明 vs 暂存区 diff 证据」核对项（审声明职责显式化）。"""
    text = _read(agate_root, "assets/review-roles/requirements-review.md")
    assert re.search(r"diff\s*证据|声明.*证据|证据.*声明", text), \
        "requirements-review 缺「声明 vs diff 证据」核对项"


def test_bdd_12_m3_acceptance_anchor_four_elements(agate_root):
    """BDD-12：P1 卡 ceremony 机制文档可提取 M3 验收锚四要素（评审轮数 / 真实发现数 / TAG0018 基线 / 回滚 standard 决策）。"""
    text = _read(agate_root, "phase-cards/P1-requirements.md")
    for kw in ("评审轮数", "真实发现数", "TAG0018", "回滚 standard"):
        assert kw in text, f"M3 验收锚缺要素：{kw}"


def test_bdd_14_full_ceremony_p7_not_prunable_sync(agate_root):
    """BDD-14：full 档 P7 不可裁四处同步声明（role-system / review-mapping / P2 卡 / P4 卡）均含 ceremony full 消费。"""
    files = [
        "role-system.md",
        "rules/review-mapping.md",
        "phase-cards/P2-design.md",
        "phase-cards/P4-implementation.md",
    ]
    for rel in files:
        text = _read(agate_root, rel)
        assert "ceremony" in text or re.search(r"tier.*full|full.*tier", text), \
            f"{rel} 缺 full 档（ceremony full / tier full）消费声明"


def test_bdd_14_full_requires_p7_phase_in_review(agate_root):
    """BDD-14 评审层保证：requirements-review 补「声明 ceremony: full → phases 含 P7」核对项（缺则需回退/拒）。"""
    text = _read(agate_root, "assets/review-roles/requirements-review.md")
    assert "ceremony" in text and "P7" in text, \
        "requirements-review 缺 full→P7 核对项（BDD-14 评审层保证）"


# ─────────────────────────────────────────────
# TAG0020 增补：P6.5 judge 机制文档条文断言（BDD-4/8/10，P3-test-cases.md §2）
# 文档先行断言：协议文档条文由 P4 implementer 同批落地，当前未落地 → 各断言均红。

def test_bdd_4_dispatch_prompt_judge_isolation_section(agate_root):
    """BDD-4：dispatch-prompt 模板含 Judge 派发追加节（信息隔离清单 + 只信证据/git log 认知约束）。"""
    text = _read(agate_root, "assets/templates/dispatch-prompt.md")
    assert "信息隔离" in text, "dispatch-prompt 缺 Judge 信息隔离条文（BDD-4）"
    assert re.search(r"黑名单|白名单", text), "dispatch-prompt 缺黑/白名单清单条文（BDD-4）"
    assert re.search(r"只信证据|证据.*git log|git log.*证据", text), \
        "dispatch-prompt 缺 judge 只信证据/git log 认知约束（BDD-4）"


def test_bdd_4_dispatch_protocol_isolation_section(agate_root):
    """BDD-4：dispatch-protocol 新增「Judge 信息隔离」节（黑名单路径引用集 + agate-extract-context 禁用/净化）。"""
    text = _read(agate_root, "dispatch-protocol.md")
    assert re.search(r"Judge\s*信息隔离", text), "dispatch-protocol 缺 Judge 信息隔离节（BDD-4）"
    assert "黑名单" in text, "dispatch-protocol 缺黑名单路径引用集条文（BDD-4）"


def test_bdd_8_judge_role_three_tier_budget_and_partial(agate_root):
    """BDD-8：judge.md 三档预算（轮次 ≤2 / token 100k / 时间 30min）+ partial 诚实降级条文。"""
    text = _read(agate_root, "assets/review-roles/judge.md")
    assert re.search(r"100\s*[kK]|100000", text), "judge.md 缺 token 预算（100k）条文（BDD-8）"
    assert re.search(r"30\s*min|30\s*分钟", text), "judge.md 缺时间预算（30 min）条文（BDD-8）"
    assert re.search(r"轮次|rounds?", text), "judge.md 缺轮次预算条文（BDD-8）"
    assert "partial" in text, "judge.md 缺 partial 诚实降级条文（BDD-8）"


def test_bdd_8_ledger_budget_exhausted_reason_documented(agate_root):
    """BDD-8：账本事件 schema 文档声明 reason: budget_exhausted（append-only 账本预算留痕）。"""
    text = _read(agate_root, "dispatch-protocol.md") + _read(agate_root, "WORKFLOW.md")
    assert "budget_exhausted" in text, "账本 schema 文档缺 reason: budget_exhausted（BDD-8）"


def test_bdd_10_workflow_p65_row(agate_root):
    """BDD-10：WORKFLOW 阶段总览含 P6.5 行（执行角色 judge 强制 + verdict/双脚本门槛）。"""
    text = _read(agate_root, "WORKFLOW.md")
    assert "P6.5" in text, "WORKFLOW 缺 P6.5 阶段行（BDD-10）"
    assert "judge" in text, "WORKFLOW P6.5 行缺 judge 角色声明（BDD-10）"


def test_bdd_10_state_machine_mount(agate_root):
    """BDD-10：state-machine P6→P7 转移含 judge 条件 + P6.5 子阶段（非独立 phase 值）声明。"""
    text = _read(agate_root, "state-machine.md")
    assert "P6.5" in text, "state-machine 缺 P6.5 描述行（BDD-10）"
    assert "judge" in text, "state-machine 缺 judge 条件（BDD-10）"
    assert re.search(r"非独立|子阶段|门槛子阶段", text), "state-machine 缺 P6.5 非独立 phase 值声明（BDD-10）"


def test_bdd_10_role_system_judge_registered(agate_root):
    """BDD-10：role-system 第二层评审名册登记 judge + status 三值映射复用说明。"""
    text = _read(agate_root, "role-system.md")
    assert "judge" in text, "role-system 名册缺 judge 登记（BDD-10）"
    assert "approved" in text and "needs-revision" in text, \
        "role-system 缺 status 三值映射（passed/rejected/needs-revision）条文（BDD-10）"


def test_bdd_10_agents_role_list_judge_registered(agate_root):
    """BDD-10：AGENTS.md（协议本体入口）角色文件清单登记 judge.md（多端隐含需求）。"""
    text = _read(agate_root, "AGENTS.md")
    assert "judge" in text, "AGENTS.md 角色清单缺 judge.md 登记（BDD-10）"


def test_bdd_10_p6_card_p65_threshold(agate_root):
    """BDD-10：P6 验收卡增「P6.5 judge 复核（强制）」门槛条文。"""
    text = _read(agate_root, "phase-cards/P6-acceptance.md")
    assert "P6.5" in text and "judge" in text, "P6 卡缺 P6.5 judge 复核门槛（BDD-10）"


def test_rm_ag0106_p6_preexisting_failure_exemption(agate_root):
    """RM-AG0106 / DEBT0055：P6 卡含「预存失败豁免口径」——判据是**本次引入失败 0**，
    机械面在 **P5** 的 baseline diff，judge 侧为**人工**复核（不得声称机械复核）。"""
    text = _read(agate_root, "phase-cards/P6-acceptance.md")
    assert "预存失败豁免口径" in text, "P6 卡缺「预存失败豁免口径」节（RM-AG0106）"
    assert "本次任务引入的失败 = 0" in text or "引入失败 0" in text, \
        "P6 卡缺「判据 = 本次引入失败 0」（非全量 0 失败）的表述"
    assert "pre-task-baseline.md" in text, \
        "P6 卡须指明机械依据在 P5 的 pre-task-baseline.md ↔ fail-list.txt diff"
    assert "禁读" in text and "_WHITELIST_MD" in text, \
        "P6 卡须写明 judge 处信息隔离（白名单不含 known-failures.md、禁读 P6-acceptance.md）"
    assert "勿声称机械复核" in text, \
        "P6 卡须显式禁止「judge 机械复核」的声称（check-judge-verdict.py 无该逻辑）"
