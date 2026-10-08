#!/usr/bin/env python3
"""校验 P1/P2/P6/P7 frontmatter schema（v2.0 T001 流 A，P2-design.md §3.1.3）。

范式仿 agate-state-yaml-check.py：从 FILE env 读文件路径，输出错误行
（每行一个），无错误输出空。由 check-frontmatter.sh 薄壳判非空拦截 exit 1。

判别契约（FIND-1，字段级/文件级两层）：
  - 文件名判定 schema（P1-requirements.md / P2-design.md / P6-acceptance.md /
    P7-consistency.md 之外的文件不校验，exit 0）
  - frontmatter 块不存在 → 旧格式，exit 0（BDD-9 兼容，不误伤在途任务）
  - 块存在但 yaml.safe_load 结果不是 dict（FIND-5，如单行全角冒号纯量）→
    一律报错"frontmatter 必须为 key: value 映射"
  - dict 中含"该文件 schema 对应迁移字段集"（而非全集）任意一个 → 新格式 →
    走必填/枚举/类型/嵌套深度校验；否则 exit 0（旧格式，字段都在正文）
"""

import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-frontmatter-check: 需要 pyyaml\n")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import agate_schema  # TAG0050 批 B：结构校验单源（BDD-50）
except ImportError:  # 安装破损降级（薄壳 fake 根未随附 agate_schema 时仍可运行）
    agate_schema = None


# 按文件名分类的 schema 定义。migrated_keys 对应 P2-design.md §3.1.2
# MIGRATED_KEYS_BY_SCHEMA 的按文件名子集（该常量在此校验器内消费，
# agate-md-field-get.py 的读取路由不依赖它，仅本文件级判定使用）。
SCHEMAS = {
    "P1-requirements.md": {
        "migrated_keys": frozenset({
            "risk_level", "phases", "packages", "domains", "override",
            "implicit_coupling", "coupling_checklist", "internal_only",
            "internal_only_reason", "跳过风险", "design_trivial",
            "follows_existing_pattern", "need_confirm_resolved",
            "suggest_resolved", "scope_resolved", "change_type",
            "ui_render_shape", "ui_ux_dimensions", "ceremony",
        }),
        "required": ("risk_level", "phases", "packages", "domains"),
        "enums": {
            "risk_level": ("low", "medium", "high"),
            "change_type": ("refactor",),
            "ceremony": ("thin", "standard", "full"),
        },
        "types": {
            "risk_level": str,
            "phases": list,
            "packages": list,
            "domains": list,
            "implicit_coupling": bool,
            "internal_only": bool,
            "design_trivial": bool,
            "coupling_checklist": list,
            "follows_existing_pattern": list,
            "change_type": str,
            "ui_render_shape": str,
            "ui_ux_dimensions": list,
            "ceremony": str,
        },
        "min_values": {},
    },
    "P2-design.md": {
        "migrated_keys": frozenset({
            "candidate_count", "packages", "domains", "ui_affected", "ui_design_section",
        }),
        "required": ("candidate_count", "packages", "domains", "ui_affected"),
        "enums": {},
        "types": {
            "candidate_count": int,
            "packages": list,
            "domains": list,
            "ui_affected": bool,
            "ui_design_section": bool,
        },
        "min_values": {"candidate_count": 1},
    },
    "P6-acceptance.md": {
        "migrated_keys": frozenset({"pass", "fail", "ui_affected", "regression_pass"}),
        "required": ("pass", "fail", "ui_affected"),
        "enums": {},
        "types": {
            "pass": int,
            "fail": int,
            "ui_affected": bool,
            "regression_pass": bool,
        },
        "min_values": {"pass": 0, "fail": 0},
    },
    "P7-consistency.md": {
        "migrated_keys": frozenset({
            "blocker_count", "deviation_count", "deviation_critical_count",
            "design_gap_count", "design_gap_reviewed_count",
        }),
        "required": (
            "blocker_count", "deviation_count", "deviation_critical_count",
            "design_gap_count", "design_gap_reviewed_count",
        ),
        "enums": {},
        "types": {
            "blocker_count": int,
            "deviation_count": int,
            "deviation_critical_count": int,
            "design_gap_count": int,
            "design_gap_reviewed_count": int,
        },
        "min_values": {
            "blocker_count": 0,
            "deviation_count": 0,
            "deviation_critical_count": 0,
            "design_gap_count": 0,
            "design_gap_reviewed_count": 0,
        },
    },
}

MAX_DEPTH = 3


_PY_TYPE_TO_JSON = {
    bool: "boolean",
    int: "integer",
    list: "array",
    str: "string",
}


def _to_json_schema(schema):
    """把本文件的历史 SCHEMAS 格式转换为 JSON Schema 子集（供 agate_schema 校验）。"""
    properties = {}
    for field, expected in (schema.get("types") or {}).items():
        properties.setdefault(field, {})["type"] = _PY_TYPE_TO_JSON.get(
            expected, "string"
        )
    for field, allowed in (schema.get("enums") or {}).items():
        properties.setdefault(field, {})["enum"] = list(allowed)
    for field in schema.get("required") or ():
        properties.setdefault(field, {})
    return {
        "type": "object",
        "required": list(schema.get("required") or ()),
        "properties": properties,
        # 历史 frontmatter schema 不拒绝未知字段（保持既有行为）
        "additionalProperties": True,
    }


def _extract_frontmatter_block(text):
    """只认文件头 --- 块；无块（或未闭合）返回 None。"""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    return text[4:end]


def _local_iter_errors(instance, schema, path=""):
    """`agate_schema.iter_errors` 的降级副本（**仅在单源库不可用的安装破损下**使用）。

    形态与前缀与单源库一致，供 `_check` 映射消息。
    """
    type_name = schema.get("type")
    if type_name and not _local_type_ok(instance, type_name):
        yield path, "type", {"expected": type_name, "actual": type(instance).__name__}
        return
    if "enum" in schema and instance not in schema["enum"]:
        yield path, "enum", {"value": instance, "allowed": list(schema["enum"])}
    if type_name == "object" and isinstance(instance, dict):
        for key in schema.get("required", []) or []:
            if key not in instance or instance.get(key) is None:
                yield path, "required", {"field": key}


def _local_type_ok(value, type_name):
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    return True


def _local_max_depth(value):
    if isinstance(value, dict):
        return 1 + max((_local_max_depth(x) for x in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_local_max_depth(x) for x in value), default=0)
    return 0


def _iter_errors(data, json_schema):
    if agate_schema is not None:
        return agate_schema.iter_errors(data, json_schema, "")
    return _local_iter_errors(data, json_schema, "")


def _max_depth(value):
    if agate_schema is not None:
        return agate_schema.max_depth(value)
    return _local_max_depth(value)


def _check(basename, schema, data):
    """校验 frontmatter（TAG0050 批 B，BDD-50）：required/enum/type 经 `agate_schema`
    单源校验，本处只把它映射为历史消息格式（保留「补 / 改用」等修复提示关键词）。

    `min_values`（数值下限）不在 agate_schema 的 draft-07 子集内，保留本地实现；
    嵌套深度复用 `agate_schema.max_depth`（消除第二处递归遍历）。
    """
    errors = []

    json_schema = _to_json_schema(schema)
    for path, code, detail in _iter_errors(data, json_schema):
        field = path
        if code == "required":
            field = detail["field"]
            errors.append(
                f"{basename}:{field}: 缺必填字段 {field} → 请在 frontmatter 补 {field}: <值>"
            )
        elif code == "enum":
            errors.append(
                "{}:{}: 非法值 {!r}（合法值: {}），请改用其一".format(
                    basename, field, detail["value"], ", ".join(str(x) for x in detail["allowed"])
                )
            )
        elif code == "type":
            errors.append(
                f"{basename}:{field}: 类型错误（应为 {detail['expected']}，实际 {detail['actual']}）"
            )

    for field, min_v in (schema.get("min_values") or {}).items():
        value = data.get(field)
        if field in data and value is not None and isinstance(value, int) \
                and not isinstance(value, bool) and value < min_v:
            errors.append(f"{basename}:{field}: 值 {value} 小于最小值 {min_v}")

    for field, value in data.items():
        if _max_depth(value) > MAX_DEPTH:
            errors.append(f"{basename}:{field}: 嵌套深度超过 {MAX_DEPTH} 层")

    return errors


def main():
    file_path = os.environ["FILE"]
    basename = os.path.basename(file_path)
    schema = SCHEMAS.get(basename)
    if schema is None:
        return  # 非目标 4 类文件，不校验

    # P4-review.md CRITICAL fix：兜底捕获 open()/yaml.safe_load()/_check()（含其内部
    # _value_depth() 无保护递归）可能抛出的任意异常（尤其 RecursionError——深嵌套结构
    # 解析会撞 Python 递归栈上限，是 RuntimeError 的子类而非 yaml.YAMLError 的子类；
    # 以及 UnicodeDecodeError——非 UTF-8 文件内容），确保任何未预见异常都转成一行错误
    # 输出打到 stdout，而不是让异常穿透到 check-frontmatter.sh 被 2>/dev/null || true
    # 静默吞掉（那样会让"深到能让解析器自己崩溃"的坏格式被误判为放行）。
    try:
        with open(file_path, encoding="utf-8") as f:
            text = f.read().replace("\r\n", "\n")

        block = _extract_frontmatter_block(text)
        if block is None:
            return  # 无 frontmatter 块 → 旧格式，BDD-9 兼容，不触发必填校验

        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
            print(str(e))
            return

        if data is None:
            return  # frontmatter 块为空 → 视同旧格式

        if not isinstance(data, dict):
            # FIND-5：safe_load 结果非 dict（无 YAMLError，如单行全角冒号纯量）→ 硬拦截
            print(
                f"{basename}: frontmatter 必须为 key: value 映射（当前解析为 {type(data).__name__}）"
            )
            return

        if not (schema["migrated_keys"] & set(data.keys())):
            return  # 无该 schema 迁移字段 → 旧格式（字段在正文），不触发必填校验

        errors = _check(basename, schema, data)
        if errors:
            print("\n".join(errors))
    except Exception as e:
        print(f"{basename}: frontmatter 处理异常（{e}）")


if __name__ == "__main__":
    main()
