# tests/unit/test_codex_platform_docs.py — TAG0033 Codex 平台接入文档断言审计
# （BDD-22~27 协议文档锚点 + BDD-29/30 真机验证清单结构守护）
#
# 被测（P7 才补，本文件 BDD-22~27 用例当前必须红）：
#   - agate/platform-notes.md 的 `## Codex ...` 章：从「待补充」补为完整能力矩阵 + 实机验证记录
#   - agate/SETUP.md 的 Codex 接入小节
#
# 归属说明（P3-test-cases.md §「BDD 验证归属表」详述）：
#   * 文档断言审计（BDD-22~27）不属既有 cmdstream 适配器/检测单测范畴 → 独立文件（比照
#     TAG0027 的 test_tag0027_b3a_platform_name_docs.py 断言审计模式：一条测试 grep 多个锚）。
#   * gate_commands.P3 冻结为 test_agate_cmdstream_adapters.py + test_agate_cmdstream_detect.py
#     两文件 → 本文件不在 check-tdd-red 的 P3 gate 扫描范围；其红灯由 test-designer 自检的
#     三文件 pytest 运行确认，转绿由 P7 协议文档阶段负责。
#   * ⚠️ 下游提示：gate_commands.P5（`pytest agate/tests/unit/ -q`）会扫到本文件 → BDD-22~27
#     的 6 条在 P4~P6 期间为 task-introduced 失败（P7 补文档后转绿）。P5 dispatch 须显式处理
#     （--deselect 这 6 条 / 或按 P5 卡「预期在 P7 转绿的失败」登记），详见 P3-test-cases.md。
#
# 红灯性质（B 类）：断言失败（platform-notes.md 仍含「待补充」、SETUP.md 无 Codex 小节、
#   spawn_agent schema 段未标 `[自述]`）。仅 stdlib + pytest。

import re


def _read(root, rel):
    return (root / rel).read_text(encoding="utf-8")


def _codex_section(text):
    """截取 platform-notes.md 中 `## Codex ...` 章正文（到下一个 `## ` 或文件尾）。"""
    m = re.search(r"^##\s+Codex[^\n]*\n", text, re.MULTILINE)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


# ============ BDD-22: Codex 章从「待补充」补为完整能力矩阵 ============


def test_bdd_22_codex_chapter_capability_matrix(agate_root):
    """BDD-22：platform-notes.md 的 `## Codex ...` 节不再含「待补充」；且逐项可 grep 命中：
    非交互 codex exec、-m/--model、model_reasoning_effort 推理档、
    --dangerously-bypass-approvals-and-sandbox、中间档 -s（read-only/workspace-write/
    danger-full-access）+ --approve-for-me（并注明 --full-auto 已从 codex exec 移除）、
    spawn_agent 原生子派发、--json 结构化输出、resume、"退出码不可靠须解析 --json"。"""
    section = _codex_section(_read(agate_root, "platform-notes.md"))
    assert section, "platform-notes.md 缺 `## Codex ...` 章"
    assert "待补充" not in section, "Codex 章仍为「待补充」占位"
    for anchor in (
        "codex exec",
        "--model",
        "model_reasoning_effort",
        "--dangerously-bypass-approvals-and-sandbox",
        "danger-full-access",
        "--approve-for-me",
        "--full-auto",
        "spawn_agent",
        "--json",
        "resume",
        "退出码",
    ):
        assert anchor in section, f"Codex 能力矩阵缺锚点: {anchor!r}"


# ============ BDD-23: 验证 CLI 版本号与账号类型已注明 ============


def test_bdd_23_codex_chapter_version_and_account(agate_root):
    """BDD-23：Codex 章含 `0.153.4`，注明验证账号类型 ChatGPT 登录、验证日期 2026-09，
    并含"新兴平台需持续复核 / 目标版本上 codex features list 复核"意味的表述。"""
    section = _codex_section(_read(agate_root, "platform-notes.md"))
    assert "0.153.4" in section, "缺验证 CLI 版本号 0.153.4"
    assert "ChatGPT" in section, "缺验证账号类型 ChatGPT"
    assert "2026-09" in section, "缺验证日期 2026-09"
    assert "features list" in section, "缺「codex features list 复核」意味表述"


# ============ BDD-24: spawn_agent schema 证据强度如实标注、不混同 ============


def test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade(agate_root):
    """BDD-24：Codex 章关于 spawn_agent 参数 schema 的段落明确标注为 `[自述]`（或等价措辞）；
    不把"未见 background/timeout/permission 字段"表述为"确认无这些字段"；并指明"穷尽 schema
    直接实测"是真机验证清单待执行项。"""
    section = _codex_section(_read(agate_root, "platform-notes.md"))
    assert "spawn_agent" in section, "Codex 章缺 spawn_agent 段落"
    assert "[自述]" in section, "spawn_agent schema 段未标注证据强度 [自述]"
    assert "确认无" not in section, "不得把「未见字段」表述为「确认无字段」"
    assert ("待执行" in section or "真机验证" in section or "待实测" in section), (
        "未指明「穷尽 schema 直接实测」为真机验证清单待执行项"
    )


# ============ BDD-25: 新 Codex 章与既有 Codex 内容不自相矛盾 ============


def test_bdd_25_codex_chapter_cross_reference_no_contradiction(agate_root):
    """BDD-25：新 `## Codex` 章对 spawn_agent / 多层派发的表述与既有 line 67-70「Codex 兼容性」
    注记（Codex subagent max_depth=1）交叉引用并标注时效（multi_agent stable/true、单层已实测、
    嵌套深度未测、既有 max_depth=1 注记待复核）。"""
    text = _read(agate_root, "platform-notes.md")
    section = _codex_section(text)
    assert "max_depth=1" in text, "既有「Codex 兼容性」注记 max_depth=1 被误删"
    assert "max_depth" in section, "新 Codex 章未交叉引用既有 max_depth 注记"
    assert "multi_agent" in section, "新 Codex 章未提 multi_agent flag 状态"
    assert ("待复核" in section or "时效" in section or "复核" in section), (
        "新 Codex 章对多层派发表述未标注时效状态"
    )


# ============ BDD-26: model 阵容随账号类型的表述完整 ============


def test_bdd_26_codex_chapter_model_lineup(agate_root):
    """BDD-26：Codex 章 model 小节注明：ChatGPT 账号下默认 gpt-5.6-terra；spawn_agent 的 model
    枚举（[自述]）；API-key 账号 model 阵容登记为"待有该环境时补"（非阻塞）。"""
    section = _codex_section(_read(agate_root, "platform-notes.md"))
    assert "gpt-5.6-terra" in section, "缺 ChatGPT 账号默认 model gpt-5.6-terra"
    assert "API" in section and ("待有该环境" in section or "待补" in section), (
        "API-key 账号 model 阵容未登记为「待有该环境时补」"
    )


# ============ BDD-27: SETUP.md 新增 Codex 接入小节 ============


def test_bdd_27_setup_md_codex_section(agate_root):
    """BDD-27：SETUP.md 含独立 Codex 小节，覆盖：安装（npm i -g @openai/codex 或官方方式）、
    codex login（并说明 ChatGPT vs API key 影响可用 model）、自动化环境绕过 flag
    （--dangerously-bypass-approvals-and-sandbox、--skip-git-repo-check）。"""
    text = _read(agate_root, "SETUP.md")
    assert re.search(r"Codex", text), "SETUP.md 无 Codex 小节"
    for anchor in (
        "npm i -g @openai/codex",
        "codex login",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
    ):
        assert anchor in text, f"SETUP.md Codex 小节缺锚点: {anchor!r}"
    assert "API key" in text or "API-key" in text, (
        "SETUP.md 未说明 ChatGPT vs API key 影响可用 model"
    )


# ============ BDD-29/30: 真机验证清单结构守护（当前绿，回归防线） ============


def _p1_requirements(agate_root):
    return _read(agate_root.parent,
                 "agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md")


def test_bdd_29_verification_checklist_shaped_four_elements(agate_root):
    """BDD-29 守护（当前绿）：P1-requirements.md §7「真机验证清单」成形——含 V1..V8 逐项，
    表头四要素（验证什么 / 怎么验 / 阶段 / 通过判据）齐备，且 V8 显式标注"待有该环境时补
    （非阻塞）"。§7 表被删/缩减即转红。"""
    text = _p1_requirements(agate_root)
    for n in range(1, 9):
        assert f"| V{n} |" in text, f"真机验证清单缺 V{n} 项"
    for element in ("验证什么", "怎么验", "阶段", "通过判据"):
        assert element in text, f"真机验证清单表头缺四要素: {element}"
    assert "待有该环境时补" in text, "V8（API-key 账号 model 阵容）未标注「待有该环境时补（非阻塞）」"
    assert "verification_env_budget" in text, "缺 verification_env_budget 轮次占位"


def test_bdd_30_spawn_agent_schema_exhaustive_item_registered(agate_root):
    """BDD-30 守护（当前绿）：P1-requirements.md 含 spawn_agent 参数 schema 穷尽实测项，
    并注明「令模型逐字输出内部 tool schema」此法不可用（模型受训拒绝），P5-P6 须换法。
    该登记被删即转红。"""
    text = _p1_requirements(agate_root)
    assert "spawn_agent" in text and "穷尽" in text, "缺 spawn_agent schema 穷尽实测登记"
    assert "模型受训" in text or "模型拒绝" in text, "未注明「模型逐字输出内部 tool schema」此法不可用"
    assert "换法" in text, "未注明 P5-P6 须换法"
    assert "background" in text and "timeout" in text and "permission" in text, (
        "未列出 [自述] 未提及的候选字段（background/timeout/permission）"
    )
