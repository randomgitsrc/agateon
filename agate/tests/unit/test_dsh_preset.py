# tests/unit/test_dsh_preset.py — DSH 平台支持模板结构守护（TAG0018，防复发）
#
# 背景：实机验证（2026-08-21）发现 agate/assets/templates/dsh/agent.cordis.yml 的
# tool-fs-search 行缺必填配置 sampleOverCapGlobResults（DSH schemastery 校验必填，
# 无默认值），导致 preset 挂载失败、DSH 按 fail-closed 拒绝创建会话
# （agent-preset-invalid: preset "agate" failed to mount ... sampleOverCapGlobResults
# missing required value）。本文件把该缺陷固化为回归测试，防止后续编辑模板时再次缺配置。
#
# 验收对象层次：本文件只断言"模板文件结构合法 + 已知必填配置在位 + 文档章节存在"，
# 不断言真实 DSH 实例行为（那是实机验证的职责，本测试在无 DSH 的环境也要可跑）。
#
# BDD 覆盖（TAG0018 P1-requirements.md）：
#   - BDD-1  agent.cordis.yml 行列表每行非空 id/name（用例 1）
#   - BDD-2  tool-fs-search 必填配置 sampleOverCapGlobResults: false（用例 2，BDD-17 回归护栏同源）
#   - BDD-3  persona 薄身份：含模板路径引用、**不含**模板正文/会话步骤/职责边界（用例 3，2026-09-21 加严）
#   - BDD-4  preset.yml 合法且 name/description 非空（用例 4）
#   - BDD-5  SKILL.md frontmatter name: agate-protocol + description 非空（用例 5）
#   - BDD-7   SETUP.md「步骤 2-DSH」标题串（用例 6）+ 位于步骤 2 平台章节区内（用例 7）
#   - BDD-8  SETUP.md DSH 章节含 BDD-8 精确命令串（mkdir -p + 三条独立 ln -sf）（用例 6）
#   - BDD-9  DSH 章节含唯一安装脚本 install-hook.py 调用（用例 8）
#   - BDD-15 本文件 ≥5 用例（8 用例），pytest 全绿由 P4 落位后 P5 验证
#   - BDD-16 平台无关：只读仓库内文件，四条禁止项见下方"平台无关原则"
#   - BDD-17 用例 2 红/绿双态可复现（缺配置 FAIL / 在位 PASS）
#
# 平台无关原则（BDD-16，agate 测试核心约束）：
#   1. 不写系统临时目录 —— 只读仓库内文件，无临时文件
#   2. 不假设符号链接语义 —— 不调用 islink、不创建链接；SETUP.md 里的 ln -sf 仅作文档文本断言
#   3. 不调用 DSH —— 不 spawn 任何 DSH 进程；~/.dsh 仅作为 SETUP.md 文本断言的目标路径字面量
#   4. 不依赖主目录路径 —— 仓库路径一律经 agate_root fixture 解析（conftest 上溯反推或 AGATE_ROOT 覆盖）
#
# 路径约定：
#   - 模板根 = {agate_root}/assets/templates/dsh/（agate_root fixture 指向 agate/ 子目录）
#   - SETUP.md 在 agate_root 下

import re

import pytest
import yaml

from conftest import (
    MAPPING_ROW_RE,
    PERSONA_INTERNAL_NAME_MARKERS,
    PROTOCOL_RULE_MARKERS,
)

TEMPLATE_DIR = ("assets", "templates", "dsh")


def _js_loader():
    """容忍 agent.cordis.yml 中的 `!!js process.platform === 'win32'` 自定义标签。"""
    class Loader(yaml.SafeLoader):
        pass

    def _construct_js(loader, node):
        return node.value

    Loader.add_constructor("tag:yaml.org,2002:js", _construct_js)
    return Loader


def _read(agate_root, *parts):
    return agate_root.joinpath(*parts).read_text(encoding="utf-8")


def _load_rows(agate_root):
    """解析 agent.cordis.yml，返回行列表（每行为 dict）。"""
    text = _read(agate_root, *TEMPLATE_DIR, "agent.cordis.yml")
    data = yaml.load(text, Loader=_js_loader())
    assert isinstance(data, list), "agent.cordis.yml 顶层应为行列表"
    return data


def _frontmatter(text):
    """解析 SKILL.md 的 YAML frontmatter。"""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    assert m, "缺少 frontmatter 块"
    return yaml.safe_load(m.group(1))


def _dsh_section(setup):
    """提取 SETUP.md「步骤 2-DSH」章节切片（标题 → 步骤 3 前）；标题缺失时 fail（红灯原因：实现缺失）。

    章节切片断言是刻意设计：install-hook.py 在 SETUP.md 其他章节（步骤 4、Windows 适配）也有
    既有引用，全局子串断言会让"DSH 章节漏写 install-hook 调用"变绿，切片断言才真正守护 BDD-9。
    """
    dsh_heading = "### 步骤 2-DSH"
    dsh_pos = setup.find(dsh_heading)
    if dsh_pos == -1:
        pytest.fail("SETUP.md 缺「### 步骤 2-DSH」标题（TAG0018 交付物未落位）")
    step3_start = setup.find("## 步骤 3")
    end = step3_start if step3_start != -1 else len(setup)
    return setup[dsh_pos:end]



# 适配层去漂移判据的来源见 `agate/tests/conftest.py`（PROTOCOL_RULE_MARKERS /
# PERSONA_INTERNAL_NAME_MARKERS / MAPPING_ROW_RE）——**单源**，多个测试文件 import，
# 避免改一处词表另一处不跟随（那正是本 PR 要消的"两套标准"形态）。


_VERIFY_SECTION_RE = re.compile(r"^## 验证清单", re.MULTILINE)


def _strip_verification_section(text):
    """去掉「验证清单」节——该节职责是"点名验证命令与预期输出"，出现文件名/变量名
    属其正常工作方式，不是复述协议规则。三个载体共用同一豁免边界。"""
    return _VERIFY_SECTION_RE.split(text, maxsplit=1)[0]

def test_dsh_agent_cordis_rows_have_id_and_name(agate_root):
    """BDD-1：每行都有 id 与 name（DSH 装配器按 id/name 解析，缺字段会挂载失败）。"""
    for row in _load_rows(agate_root):
        assert isinstance(row, dict), f"行不是 dict: {row!r}"
        assert row.get("id"), f"行缺 id: {row!r}"
        assert row.get("name"), f"行缺 name: {row!r}"


def test_dsh_tool_fs_search_has_required_config(agate_root):
    """BDD-2 + BDD-17：tool-fs-search 必须带 config.sampleOverCapGlobResults（schemastery 必填，无默认值）。

    实机复现：缺失该字段 → preset mount 失败 → DSH 拒绝创建会话（fail-closed）。
    本用例即 BDD-17 回归护栏：缺配置 FAIL / 在位 PASS 双态可复现。
    """
    rows = _load_rows(agate_root)
    fs_search = next((r for r in rows if r.get("id") == "tool-fs-search"), None)
    assert fs_search is not None, "缺少 tool-fs-search 行"
    config = fs_search.get("config") or {}
    assert config.get("sampleOverCapGlobResults") is False, (
        "tool-fs-search 缺 config.sampleOverCapGlobResults: false（DSH schemastery 必填）"
    )


def test_dsh_persona_is_thin_identity(agate_root):
    """BDD-3：persona 薄身份——指向 orchestrator-template.md 而非内嵌模板正文。

    三判据（P2-review 建议 1，核心约束 CI 护栏）：
       schema 判据：persona.config 必含 `prefix`（DSH ≥rc.8 起 persona 的必填 key；
        缺失 → preset 挂载失败 → DSH fail-closed 拒绝创建会话）。
      正判据：persona.prefix 含 {agate_root}/orchestrator-template.md 路径引用（行为规范指向模板）；
      负判据：不含模板首行标题「# Orchestrator（agate 编排 Agent）」（不复制模板全文 verbatim）。
    """
    rows = _load_rows(agate_root)
    persona = next((r for r in rows if r.get("id") == "persona"), None)
    assert persona is not None, "agent.cordis.yml 缺 persona 行"
    config = persona.get("config") or {}
    text = config.get("prefix") or ""
    assert text, "persona 行缺 config.prefix（DSH ≥rc.8 必填）"
    assert "{agate_root}/orchestrator-template.md" in text, (
        "persona 必须引用 {agate_root}/orchestrator-template.md（身份薄、协议厚）"
    )
    assert "# Orchestrator（agate 编排 Agent）" not in text, (
        "persona 不得内嵌模板正文首行标题「# Orchestrator（agate 编排 Agent）」（不复制模板全文）"
    )
    # 2026-09-21 加严：原负判据只查模板首行标题，**放任 persona 复制会话开始步骤**
    # （解析 {AGATE_WORKSPACE} / 读 active-tasks / 读 phase-cards / 职责边界四件事）。
    # 后果实证：TAG0037 改了模板的协议根回退路径，persona 副本未跟 → 把版本根
    # `~/.agate` 当协议根（实测失实）。协议内容必须单一来源（模板），适配层只做
    # 「指向 + 平台差异」——下列关键词属模板的「你是谁」「会话开始时」两节，不得复制。
    # 判据（分层，理由见模组级注释）：
    #   A. 协议规则句——三载体统一禁；
    #   B. 协议内部文件名/变量——persona 专属禁（它的职责只是"指向模板"）。
    # 锚点均经 main 版本验证：旧 persona 含 `只有你能写的文件`(1)/`会话开始时`(1)/
    # `active-tasks.md`(1)/`{AGATE_WORKSPACE}`(3) → 本判据对旧文件**会变红**（回归可证）。
    # ⚠ 不套用「验证清单」豁免：persona **没有**该节，豁免只会开旁路——复审实证
    # （在 prefix 里插一行 `## 验证清单` + 全部禁词 → 判据放行）。「当前没有该节」不等于
    # 「未来不会被加进来」；persona 用未截断原文。
    for forbidden in (*PROTOCOL_RULE_MARKERS, *PERSONA_INTERNAL_NAME_MARKERS):
        assert forbidden not in text, (
            f"persona 复述了协议内容「{forbidden}」——协议内容单一来源在 "
            f"orchestrator-template.md；persona 只做「指向 + 平台工具映射」，否则必然漂移"
        )


# ── DSH 包 required-key 契约（通用 schema 校验）─────────────────────────────
#
# 为什么需要（2026-09-16，同类故障第二次发生）：
#   本文件原有用例只断言 persona **内容**（config.text 含 orchestrator-template.md 引用），
#   不校验 **key 名是否符合 DSH 包的 schema**。DSH 40792330c0 起 persona 必填 key
#   由 `text` 改为 `prefix`，模板未跟进 → preset 挂载失败 → DSH fail-closed 拒绝建会话
#   （$.prefix missing required value；hotfix PR #325）。而原有测试**全绿**——因为
#   它查的正是那个已经失效的旧 key。
#   同类先例：tool-fs-search 的 sampleOverCapGlobResults（本文件第 3-7 行注释记录）。
#
# 维护方式：DSH 各包的 required key 来自其 src/index.ts 的 `z.object({...})` 中
#   `.required()`（或裸 `z.<type>()` 无 `.default()`）的字段。DSH 改 schema 时
#   本清单需同步——不同步则 CI 红（这正是本契约的目的：**让 schema 漂移在 CI 暴露，
#   而非等用户新开会话时才发现**）。
#
# 数据来源（harness 仓库，2026-09-16 核对）：
#   packages/preset/persona/src/index.ts          → prefix: z.string().required()
#   packages/fs/tool-fs-search/src/index.ts       → sampleOverCapGlobResults: z.boolean().required()
#   packages/todo/tool-todo/src/index.ts          → allowParallelInProgress: z.boolean().required()
#   （tool-web / tool-goal / agent-instructions 的 Config 字段全有 .default()，无 required key）
DSH_PACKAGE_REQUIRED_KEYS = {
    "@deepseek-ai/dsh-persona": ("prefix",),
    "@deepseek-ai/dsh-tool-fs-search": ("sampleOverCapGlobResults",),
    "@deepseek-ai/dsh-tool-todo": ("allowParallelInProgress",),
}


def test_dsh_package_configs_have_all_required_keys(agate_root):
    """BDD-18：模板中每个引用 DSH 包的行，其 config 必含该包的 schema required key。

    这是**通用契约**（非单字段断言）：DSH 任意包新增/改名必填 key → 本用例红，
    避免"文件语法合法 + 内容正确，但 key 不符 schema → 挂载失败且测试全绿"的故障模式。
    """
    rows = _load_rows(agate_root)
    checked = []
    for row in rows:
        name = row.get("name")
        if name not in DSH_PACKAGE_REQUIRED_KEYS:
            continue
        config = row.get("config")
        if config is None:
            config = {}
        assert isinstance(config, dict), (
            f"{row.get('id')} 行（{name}）的 config 须为 mapping，实际 {type(config).__name__}"
        )
        for key in DSH_PACKAGE_REQUIRED_KEYS[name]:
            assert key in config, (
                f"{row.get('id')} 行（{name}）缺 schema 必填 config key `{key}`——"
                f"该包 src/index.ts 中 `{key}` 为 required，缺失 → preset 挂载失败 → "
                f"DSH fail-closed 拒绝创建会话"
            )
        checked.append(name)
    # 防"清单写了但模板没引用该包"导致空跑
    assert checked, (
        "模板中未找到任何带 required-key 契约的 DSH 包行——"
        f"契约清单 {sorted(DSH_PACKAGE_REQUIRED_KEYS)} 疑与模板脱节"
    )


def test_dsh_preset_yml_has_name_and_description(agate_root):
    """BDD-4：preset.yml 需含 GUI 选择器展示用的 name/description（产品级要求，非 schema 强制）。"""
    data = yaml.safe_load(_read(agate_root, *TEMPLATE_DIR, "preset.yml"))
    assert data.get("name"), "preset.yml 缺 name"
    assert data.get("description"), "preset.yml 缺 description"


def test_dsh_skill_frontmatter_valid(agate_root):
    """BDD-5：SKILL.md frontmatter 需含 name: agate-protocol 与 description（DSH 技能目录按名发现）。"""
    fm = _frontmatter(_read(agate_root, *TEMPLATE_DIR, "SKILL.md"))
    assert fm.get("name") == "agate-protocol", "SKILL.md frontmatter name 应为 agate-protocol"
    assert fm.get("description"), "SKILL.md frontmatter 缺 description"


def test_dsh_setup_section_and_symlink_commands_present(agate_root):
    """BDD-7（标题串）+ BDD-8：SETUP.md 需含「步骤 2-DSH」章节与 BDD-8 精确符号链接命令串。

    断言以 BDD-8 字面为准（P2-design R-1：以精确命令串为断言基准；P2-review 建议 5：三条独立 ln 行），
    且限定在 DSH 章节切片内，防既有章节路径字面量误命中。
    """
    setup = _read(agate_root, "SETUP.md")
    assert "步骤 2-DSH" in setup, "SETUP.md 缺「步骤 2-DSH」章节"
    section = _dsh_section(setup)
    # BDD-8：mkdir -p 目标目录（preset + skill 两处安装根）
    assert "mkdir -p ~/.dsh/.agent-presets/agate ~/.dsh/skills/agate-protocol" in section, (
        "SETUP.md DSH 章节缺 mkdir -p 命令"
    )
    # BDD-8：三条独立 ln -sf，源路径均指向模板目录下的三个文件。
    # 源前缀用 $AGATE_DIR（2026-09-19 起）——协议根在版本管理布局下是 ~/.agate/current/agate，
    # 不是 ~/.agate 本身，写死 ~/.agate/... 在版本管理布局下会创建**断链**
    # （实测 claude --agent orchestrator 报 not found）。BDD-8 的契约是"命令与模板文件名
    # 耦合在册"（见 P1-requirements coupling_checklist），故断言锚定**文件名 + 目标路径**，
    # 前缀统一为 "$AGATE_DIR/assets/templates/dsh/"。
    src_prefix = '"$AGATE_DIR/assets/templates/dsh/'
    assert f"ln -sf {src_prefix}agent.cordis.yml\"" in section, (
        "DSH 章节缺 agent.cordis.yml 符号链接命令"
    )
    assert f"ln -sf {src_prefix}preset.yml\"" in section, (
        "DSH 章节缺 preset.yml 符号链接命令"
    )
    assert f"ln -sf {src_prefix}SKILL.md\"" in section, (
        "DSH 章节缺 SKILL.md 符号链接命令"
    )
    # BDD-8：安装目标路径（preset → ~/.dsh/.agent-presets/agate/、SKILL → ~/.dsh/skills/agate-protocol/）
    assert "~/.dsh/.agent-presets/agate/" in section, "DSH 章节缺 preset 安装目标路径"
    assert "~/.dsh/skills/agate-protocol/SKILL.md" in section, "DSH 章节缺 skill 安装目标路径"


def test_dsh_setup_dsh_section_within_step_2(agate_root):
    """BDD-7 位置判据：DSH 章节标题必须位于步骤 2 平台章节区内（## 步骤 2 与 ## 步骤 3 之间）。

    对应 P2-design 决策 D-1：DSH 小节为步骤 2 区内最后一个 h3（Windows 小节后、步骤 3 前），
    与 Claude Code/OpenCode/Windows 小节同构——用户按既有路径可找到。
    """
    setup = _read(agate_root, "SETUP.md")
    step2_start = setup.find("## 步骤 2：")
    step3_start = setup.find("## 步骤 3")
    dsh_pos = setup.find("### 步骤 2-DSH")
    assert step2_start != -1, "SETUP.md 缺「步骤 2」章节"
    assert step3_start != -1, "SETUP.md 缺「步骤 3」章节"
    assert dsh_pos != -1, "SETUP.md 缺「### 步骤 2-DSH」标题"
    assert step2_start < dsh_pos < step3_start, (
        "「步骤 2-DSH」必须位于步骤 2 平台章节区内（## 步骤 2 之后、## 步骤 3 之前）"
    )


def test_dsh_setup_section_has_install_hook_call(agate_root):
    """BDD-9：不发明新结构——DSH 章节须含唯一安装脚本 install-hook.py 调用。

    章节切片断言（见 _dsh_section docstring）：SETUP.md 步骤 4 / Windows 适配已有既有
    install-hook.py 引用，全局断言无法守护"DSH 章节漏写调用"；全仓无 per-platform installer
    的核查（BDD-9 后半）由 P4 grep 复证 + P6 完成标准 #5 兜底，不进本单测。
    """
    setup = _read(agate_root, "SETUP.md")
    section = _dsh_section(setup)
    # 只断言脚本路径，不硬编码解释器名（python3/python，R2 平台无关约束——解释器名在
    # Windows 上可能是 python，见 AGENTS.md 测试约定「不允许裸 python3」）
    assert "~/.agate/scripts/install-hook.py" in section, (
        "SETUP.md DSH 章节缺 install-hook.py 调用（唯一安装脚本；不引入 per-platform installer）"
    )


def test_dsh_skill_avoids_protocol_content_and_duplicate_mapping(agate_root):
    """DSH SKILL.md：不复述协议规则，且**不再重复工具映射**（单一来源 = persona）。

    2026-09-21 复审修正两处：
      (1) 原判据锚点含 `AGATE_WORKSPACE`/`phase-cards`，而旧文件里这两词**都落在被豁免的
          「验证清单」节内** → 判据对旧文件不变红（**死判据**，不是回归测试）。现改用
          `PROTOCOL_RULE_MARKERS`（协议规则句）+ **映射单一来源**判据。
      (2) 原判据漏了 `active-tasks.md`——它恰是旧文件里**唯一落在豁免区外**的旁路词。

    回归可证：main 版 SKILL.md 含「| 更新状态 | … active-tasks.md |」映射行 → 映射判据变红。
    """
    skill = agate_root.joinpath("assets", "templates", "dsh", "SKILL.md")
    text = skill.read_text(encoding="utf-8")
    body = _strip_verification_section(text)  # 豁免「验证清单」节（理由见下）

    for forbidden in PROTOCOL_RULE_MARKERS:
        assert forbidden not in body, (
            f"DSH SKILL.md 复述了协议规则「{forbidden}」——单一来源在模板"
        )
    # 映射单一来源：DSH 有 persona 层，映射已在那里；SKILL.md 不得再有映射表。
    # 判据用映射表的**行特征**（职责→工具 的表格行），不用文件名——因为文件名在
    # 「验证清单」节里是合法的（该节职责即点名验证命令与预期输出）。
    # 用正则（`MAPPING_ROW_RE`，单源在 conftest）而非字面量——复审实测字面量会被
    # `|读状态|`（管道无空格）绕过。格式变体（bullet 形式、职责标签改名）仍无法穷尽，
    # 属关键词判据上限，见 conftest 的已知限制登记。
    hit = MAPPING_ROW_RE.search(body)
    assert hit is None, (
        f"DSH SKILL.md 仍含工具映射表行「{hit.group(0).strip() if hit else ''}」——"
        f"映射单一来源应为 agent.cordis.yml 的 persona（否则两处维护必然漂移）"
    )


def test_dsh_skill_mapping_pointer_targets_exist(agate_root):
    """SKILL.md 指向 `agent.cordis.yml` 取工具映射——该指针的**两个目标都必须存在**。

    2026-09-21 复审发现：工具映射收敛到 persona 后，SKILL.md 的无-preset 入口指向
    `agent.cordis.yml`，但既未给基路径、也无测试守护其目标存在（悬空指针风险）。
    本用例锁定：① 正文确实声明了该指针；② 模板源路径存在且**含映射**（否则收敛是空的）。
    """
    skill = agate_root.joinpath("assets", "templates", "dsh", "SKILL.md")
    text = skill.read_text(encoding="utf-8")
    assert "persona.config.prefix" in text, "SKILL.md 应指明从 persona.config.prefix 取映射"
    assert ".agent-presets/agate/agent.cordis.yml" in text, (
        "应给出安装后的基路径（~/.dsh/.agent-presets/agate/），否则无-preset 环境找不到文件"
    )
    agent = agate_root.joinpath("assets", "templates", "dsh", "agent.cordis.yml")
    assert agent.is_file(), "指针目标（模板源 agent.cordis.yml）必须存在"
    # 目标里必须真有映射——否则"单一来源"指向的是空处
    rows = _load_rows(agate_root)
    persona = next((r for r in rows if r.get("id") == "persona"), None)
    prefix = (persona or {}).get("config", {}).get("prefix", "")
    for tool in ("subagent", "read", "bash"):
        assert tool in prefix, f"persona 映射应含工具「{tool}」（SKILL.md 的指针指向它）"
