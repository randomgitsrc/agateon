# agate/tests/unit/_rules_test_utils.py — TAG0021 结构化层 P3 共享测试工具
# （非测试模块，pytest 不收集；供 test_check_yaml_schema / test_check_structure_consistency /
#   test_structure_migration / test_card_render 共用）
#
# 被测脚本 check-yaml-schema.py / check-structure-consistency.py（P4 M0 才实现）尚不存在，
# 全部测试以「最小假协议树」为夹具入口（design §3.6：resolve_agate_root 四层链 env 优先）：
#   AGATE_ROOT=<tmp>/fake-root  →  {root}/rules/{phases,dispatch,roles}.yaml +
#   {root}/rules/schema/*.json + {root}/WORKFLOW.md（S-1/S-2 md 侧锚点）+ {root}/phase-cards/
#   （S-3 抽检）+ {root}/scripts/ + {root}/assets/（S-6 引用完整性 + resolve 前提）。
#
# YAML 数据形状沿用 P2-design §3.1/§3.2 已定字段与枚举（exec_role / phase id / retry_cap /
# 五模式词表 = {single, static-batch, parallel, recon-then-split, serial}，P2-review 发现 #2
# 对齐后词表；gate_commands 合法 key = is_gate_meta_key OR project_module 特判，发现 #3）。
#
# 平台无关（BDD-16）：无临时目录字面量（全部 tmp_path）、无软链、无裸解释器字面量；
# 文本 I/O 显式 utf-8。

import json
import shutil
from pathlib import Path

# ---- 默认 rules YAML 内容（P1/P2/P3 最小合法集；测试可整体覆写） ----

DEFAULT_PHASES_YAML = (
    "schema_version: 1\n"
    "phases:\n"
    "  - id: P1\n"
    "    name: 需求基线\n"
    "    exec_role: analyst\n"
    "    outputs:\n"
    "      - {file: P1-requirements.md, required: true}\n"
    "    gates:\n"
    "      - {check: P1-requirements.md 含 BDD}\n"
    "    retry_cap: 3\n"
    "  - id: P2\n"
    "    name: 方案设计层\n"
    "    exec_role: architect\n"
    "    outputs:\n"
    "      - {file: P2-design.md, required: true}\n"
    "      - {file: P2-review.md, required: true, status_field: status}\n"
    "    gates:\n"
    "      - {check: P2-review.md status == approved}\n"
    "    retry_cap: 3\n"
    "  - id: P3\n"
    "    name: 测试设计\n"
    "    exec_role: test-designer\n"
    "    outputs:\n"
    "      - {file: P3-test-cases.md, required: true}\n"
    "    gates:\n"
    "      - {check: P3-test-cases.md 声明 test_code_dir}\n"
    "    retry_cap: 2\n"
)

DEFAULT_DISPATCH_YAML = (
    "schema_version: 1\n"
    "modes: [single, static-batch, parallel, recon-then-split, serial]\n"
    "templates:\n"
    "  - {name: dispatch-prompt, file: assets/templates/dispatch-prompt.md}\n"
    "gate_commands_syntax:\n"
    "  pattern: '^P[0-9]+'\n"
    "  meta_suffixes: [_formatter, _timeout_seconds]\n"
    "  special_keys: [project_module]\n"
    "field_readers:\n"
    "  - {script: check-gate.py, phase: P2, fields: [candidate_count, packages, domains, ui_affected, gate_commands]}\n"
)

DEFAULT_ROLES_YAML = (
    "schema_version: 1\n"
    "execution_roles:\n"
    "  - {id: analyst, file: assets/execution-roles/analyst.md}\n"
    "  - {id: architect, file: assets/execution-roles/architect.md}\n"
    "  - {id: test-designer, file: assets/execution-roles/test-designer.md}\n"
    "review_roles:\n"
    "  - {id: requirements-review, file: assets/review-roles/requirements-review.md}\n"
    "  - {id: plan-eng-review, file: assets/review-roles/plan-eng-review.md}\n"
    "scripts:\n"
    "  - {script: check-gate.py, path: scripts/check-gate.py}\n"
    "  - {script: check-yaml-schema.py, path: scripts/check-yaml-schema.py}\n"
)

# markers.yaml（正文标记形态单源；2026-10-02）。
# 假协议树须**镜像真协议结构**——check-yaml-schema.py 的 _RULES 声明了 markers，
# 假树缺之会误报「文件缺失」。此处为最小可过 schema 的子集（不必等同真注册表全量）。
DEFAULT_MARKERS_YAML = r"""schema_version: 1
lead: '^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?'
lead_variants:
  blockquote_ok: '^\s*>?\s*-?\s*'
markers:
  - name: SCOPE+
    purpose: 发现 P1 未覆盖的新隐含需求
    phases: [P2, P4]
    params: none
    paired_with: SCOPE_RESOLVED
  - name: SCOPE_RESOLVED
    purpose: SCOPE+ 已纳入基线
    phases: [P1]
    params: optional_text
    resolves: SCOPE+
"""

# WORKFLOW.md 阶段总览表（S-1/S-2 md 侧锚点）。
# 含 READY 行：P2-review 发现 #1 要求 S-2 只匹配 P 数字前缀行，READY/表外行显式排除。
DEFAULT_WORKFLOW_TABLE = (
    "| 阶段 | 名称 | 执行角色 | 评审角色 | 门槛 |\n"
    "|------|------|----------|----------|------|\n"
    "| P1 | 需求基线 | analyst | requirements-review | P1-requirements.md 存在 |\n"
    "| P2 | 方案设计层 | architect | plan-eng-review | P2-review.md approved |\n"
    "| P3 | 测试设计 | test-designer | --- | check-tdd-red exit 0 |\n"
    "| READY | 待发布 | --- | --- | 人手动发布 |\n"
)

# phase-cards/P2-design.md（S-3 抽检 md 侧；产出/派发两节与 phases.yaml P2 声明一致）
DEFAULT_P2_CARD = (
    "# P2 方案设计层\n\n"
    "## 前置条件\n"
    "- P1-requirements.md 完成\n\n"
    "## 产出规格\n"
    "- P2-design.md\n"
    "- P2-review.md\n\n"
    "## 派发\n"
    "- architect\n"
)


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _schema_text(required_keys, props, enum_lists=None):
    """构造 draft-07 子集 schema JSON 文本（仅 type/required/enum/properties/items）。"""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": required_keys,
        "properties": props,
        "additionalProperties": False,
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def default_phases_schema():
    """phases.schema.json 默认：与 DEFAULT_PHASES_YAML 互证的 draft-07 子集。"""
    return _schema_text(
        ["schema_version", "phases"],
        {
            "schema_version": {"type": "integer"},
            "phases": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "name", "exec_role"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "enum": ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P6.5", "P7", "P8"],
                        },
                        "name": {"type": "string"},
                        "exec_role": {
                            "type": "string",
                            "enum": [
                                "analyst",
                                "architect",
                                "test-designer",
                                "implementer",
                                "verifier",
                                "consistency-reviewer",
                                "judge",
                                "releaser",
                            ],
                        },
                        "outputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["file"],
                                "properties": {
                                    "file": {"type": "string"},
                                    "required": {"type": "boolean"},
                                    "status_field": {"type": "string"},
                                },
                            },
                        },
                        "gates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["check"],
                                "properties": {"check": {"type": "string"}},
                            },
                        },
                        "retry_cap": {"type": "integer", "enum": [2, 3]},
                    },
                    "additionalProperties": False,
                },
            },
        },
    )


def default_dispatch_schema():
    """dispatch.schema.json 默认：modes 词表 = 对齐后五模式（P2-review 发现 #2）。"""
    return _schema_text(
        ["schema_version", "modes"],
        {
            "schema_version": {"type": "integer"},
            "modes": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["single", "static-batch", "parallel", "recon-then-split", "serial"],
                },
            },
            "templates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "file"],
                    "properties": {
                        "name": {"type": "string"},
                        "file": {"type": "string"},
                    },
                },
            },
            "gate_commands_syntax": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "meta_suffixes": {"type": "array", "items": {"type": "string"}},
                    "special_keys": {"type": "array", "items": {"type": "string"}},
                },
            },
            "field_readers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["script", "phase", "fields"],
                    "properties": {
                        "script": {"type": "string"},
                        "phase": {"type": "string"},
                        "fields": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    )


def default_roles_schema():
    """roles.schema.json 默认。"""
    return _schema_text(
        ["schema_version"],
        {
            "schema_version": {"type": "integer"},
            "execution_roles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "file"],
                    "properties": {"id": {"type": "string"}, "file": {"type": "string"}},
                },
            },
            "review_roles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "file"],
                    "properties": {"id": {"type": "string"}, "file": {"type": "string"}},
                },
            },
            "scripts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["script", "path"],
                    "properties": {"script": {"type": "string"}, "path": {"type": "string"}},
                },
            },
        },
    )


def default_markers_schema():
    """markers.schema.json 默认（假树用最小子集，与真 schema 的必填字段一致）。"""
    return _schema_text(
        ["schema_version", "lead", "lead_variants", "markers"],
        {
            "schema_version": {"type": "integer"},
            "lead": {"type": "string"},
            "lead_variants": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "markers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "purpose", "phases", "params"],
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "purpose": {"type": "string"},
                        "phases": {"type": "array", "items": {"type": "string"}},
                        "params": {"type": "string"},
                        "paired_with": {"type": "string"},
                        "resolves": {"type": "string"},
                        "accept_backtick": {"type": "boolean"},
                    },
                },
            },
        },
    )


# S-6 引用完整性需要真实存在的占位文件（内容空即可）
_REFERENCED_FILES = (
    "scripts/check-gate.py",
    "scripts/check-yaml-schema.py",
    "scripts/check-structure-consistency.py",
    "scripts/agate-md-field-get.py",
    "assets/execution-roles/analyst.md",
    "assets/execution-roles/architect.md",
    "assets/execution-roles/test-designer.md",
    "assets/review-roles/requirements-review.md",
    "assets/review-roles/plan-eng-review.md",
    "assets/templates/dispatch-prompt.md",
)


def make_fake_root(
    tmp_path,
    phases_text=None,
    dispatch_text=None,
    roles_text=None,
    workflow_text=None,
    card_text=None,
    phases_schema=None,
    dispatch_schema=None,
    roles_schema=None,
    markers_text=None,
    markers_schema=None,
    add_files=None,
    agate_scripts=None,
):
    """构造最小假协议树（tmp_path 下），返回 root 路径。

    默认内容互相一致（S-1~S-6 全过、schema 全过）；测试传覆写参数制造漂移。
    add_files: {相对路径: 文本} 追加写（如引用 fake 文件制造 S-6 错误前需要的占位）。
    agate_scripts: 传入时把真实 agate-next-card.py 拷贝进假树 scripts/——
        agate-inject-card.py 经 {root}/scripts/agate-next-card.py 取卡片，且该脚本
        agate_common 缺失时回退 env AGATE_ROOT；拷贝使 BDD-13 注入测试在 P3（静态
        卡片 → 红灯）与 M3（渲染器版本 → 绿）两阶段都可达。
    """
    root = Path(tmp_path) / "fake-root"
    _write(root, "rules/phases.yaml", phases_text or DEFAULT_PHASES_YAML)
    _write(root, "rules/dispatch.yaml", dispatch_text or DEFAULT_DISPATCH_YAML)
    _write(root, "rules/roles.yaml", roles_text or DEFAULT_ROLES_YAML)
    # markers.yaml：正文标记形态单源（2026-10-02）。假树须镜像真协议结构——
    # check-yaml-schema.py 的 _RULES 声明了 markers，假树缺之会误报「文件缺失」。
    _write(root, "rules/markers.yaml", markers_text or DEFAULT_MARKERS_YAML)
    _write(root, "rules/schema/phases.schema.json", phases_schema or default_phases_schema())
    _write(root, "rules/schema/dispatch.schema.json", dispatch_schema or default_dispatch_schema())
    _write(root, "rules/schema/roles.schema.json", roles_schema or default_roles_schema())
    _write(root, "rules/schema/markers.schema.json", markers_schema or default_markers_schema())
    _write(root, "WORKFLOW.md", workflow_text or DEFAULT_WORKFLOW_TABLE)
    _write(root, "phase-cards/P2-design.md", card_text or DEFAULT_P2_CARD)
    for rel in _REFERENCED_FILES:
        _write(root, rel, "# 占位\n")
    if agate_scripts is not None:
        next_card_src = Path(agate_scripts) / "agate-next-card.py"
        if next_card_src.is_file():
            shutil.copy2(next_card_src, root / "scripts" / "agate-next-card.py")
    if add_files:
        for rel, text in add_files.items():
            _write(root, rel, text)
    return root
