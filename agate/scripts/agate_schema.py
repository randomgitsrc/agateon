#!/usr/bin/env python3
"""agate_schema.py — JSON Schema 子集校验器 + derive/render（TAG0050 批 B 单源库）

设计依据：`docs/design-notes/design-tag0050-task-data-contract.md` §3.2。
**唯一**的递归 schema 校验实现——`check-yaml-schema.py` / `agate-frontmatter-check.py`
/ `agate-config.py` 三处统一调用本库（BDD-50：`agate/scripts/*.py` 中不存在第二个
递归 schema 校验实现）。

支持的关键字（draft-07 子集）：`type` / `enum` / `required` / `properties` /
`additionalProperties` / `items` / `minItems`，**只新增** `pattern`。

`iter_errors()` 返回**结构化**错误 `(path, code, detail)`，由各消费方映射为自己
的历史消息格式（保持既有测试的关键词契约）。`validate()` 为其便捷封装。

`derive()` 实现系统字段的四个算子：`count` / `sum` / `union` / `any`。
`render()` 实现渲染块内容生成（如 `results_table`）。

平台无关：无裸解释器、无硬编码 PATH、无系统临时目录字面量。Python 3.8+。
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 行首渲染块标记（AGATE:RENDER）——md-field-set 生成、gate 校验共用同一形态
# ---------------------------------------------------------------------------

RENDER_BEGIN_TMPL = "<!-- AGATE:RENDER {key} BEGIN（agate-md-field-set 生成，勿手改） -->"
RENDER_END_TMPL = "<!-- AGATE:RENDER {key} END -->"
# 兼容测试/手写的最小形态（不带“生成”说明）。
_RENDER_RE = re.compile(
    r"<!--\s*AGATE:RENDER\s+(\S+)\s+BEGIN[^\n]*?-->(.*?)<!--\s*AGATE:RENDER\s+\1\s+END\s*-->",
    re.DOTALL,
)


def render_block(key, content):
    """生成一个渲染块（BEGIN/END 包裹 content）。"""
    return (
        RENDER_BEGIN_TMPL.format(key=key)
        + "\n"
        + content
        + "\n"
        + RENDER_END_TMPL.format(key=key)
    )


def find_render_blocks(text):
    """提取全部渲染块 → [{key, content, start, end, count}]。

    `content` 为块内容（已把 CRLF 规范为 LF 后逐字节原样），用于与 render() 比对。
    """
    out = []
    for m in _RENDER_RE.finditer(text.replace("\r\n", "\n")):
        out.append({
            "key": m.group(1),
            "content": m.group(2),
            "start": m.start(),
            "end": m.end(),
        })
    return out


# ---------------------------------------------------------------------------
# 校验器
# ---------------------------------------------------------------------------


def type_ok(value, type_name):
    """JSON Schema `type` 判定（bool 是 int 子类，integer 须排除 bool）。"""
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "null":
        return value is None
    return True


def iter_errors(instance, schema, path=""):
    """递归校验 instance vs schema；yield `(path, code, detail)`。

    code ∈ {type, enum, required, unknown, minItems, pattern}。detail 为 dict。
    """
    if not isinstance(schema, dict):
        return
    type_name = schema.get("type")
    if type_name and not type_ok(instance, type_name):
        yield path, "type", {"expected": type_name, "actual": type(instance).__name__}
        return
    if "enum" in schema and instance not in schema["enum"]:
        yield path, "enum", {"value": instance, "allowed": list(schema["enum"])}
    if type_name == "object" and isinstance(instance, dict):
        properties = schema.get("properties", {}) or {}
        for key in schema.get("required", []) or []:
            if key not in instance or instance.get(key) is None:
                yield path, "required", {"field": key}
        for key, item in instance.items():
            child = f"{path}.{key}" if path else key
            if key in properties:
                yield from iter_errors(item, properties[key], child)
            elif schema.get("additionalProperties") is False:
                yield path, "unknown", {"field": key}
    elif type_name == "array" and isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            yield path, "minItems", {"length": len(instance), "min": schema["minItems"]}
        items = schema.get("items")
        if items:
            for idx, item in enumerate(instance):
                yield from iter_errors(item, items, f"{path}[{idx}]")
    if "pattern" in schema and isinstance(instance, str):
        try:
            matched = re.search(schema["pattern"], instance) is not None
        except re.error:
            matched = True
        if not matched:
            yield path, "pattern", {"value": instance, "pattern": schema["pattern"]}


def validate(instance, schema, path=""):
    """便捷封装：返回 `[(path, msg)]`（中性消息，供消息不敏感的消费方）。"""
    out = []
    for p, code, detail in iter_errors(instance, schema, path):
        if code == "type":
            msg = f"类型应为 {detail['expected']}，实际 {detail['actual']}"
        elif code == "enum":
            msg = f"值 {detail['value']!r} 不在枚举 {detail['allowed']}"
        elif code == "required":
            msg = f"缺 required 字段 {detail['field']}"
        elif code == "unknown":
            msg = f"未知字段 {detail['field']}（additionalProperties=false）"
        elif code == "minItems":
            msg = f"数组长度 {detail['length']} < minItems {detail['min']}"
        elif code == "pattern":
            msg = f"值 {detail['value']!r} 不匹配 pattern {detail['pattern']}"
        else:
            msg = code
        out.append((p, msg))
    return out


def max_depth(value):
    """标量深度 0；dict/list 深度 = 1 + 子项最大深度（空容器记 1）。

    （frontmatter 校验的 MAX_DEPTH 判定复用本函数——消除第二处递归遍历。）
    """
    if isinstance(value, dict):
        if not value:
            return 1
        return 1 + max(max_depth(x) for x in value.values())
    if isinstance(value, list):
        if not value:
            return 1
        return 1 + max(max_depth(x) for x in value)
    return 0


# ---------------------------------------------------------------------------
# derive（系统字段现算）——只允许 count / sum / union / any 四个算子
# ---------------------------------------------------------------------------

_DERIVE_RE = re.compile(r"^\s*([a-z]+)\s*\(\s*([^,]+?)\s*(?:,\s*(.+?)\s*)?\)\s*$")


def _predicate(spec):
    """解析谓词 `key == VALUE` / `key != VALUE` / `key`（存在即真）。"""
    spec = (spec or "").strip()
    if "==" in spec:
        left, right = spec.split("==", 1)
        key = left.strip()
        val = right.strip().strip("'\"")
        return lambda item: isinstance(item, dict) and str(item.get(key)) == val
    if "!=" in spec:
        left, right = spec.split("!=", 1)
        key = left.strip()
        val = right.strip().strip("'\"")
        return lambda item: isinstance(item, dict) and str(item.get(key)) != val
    key = spec
    return lambda item: isinstance(item, dict) and bool(item.get(key))


def derive(expr, data):
    """按 derive 表达式现算系统字段值（忽略文件里的值）。

    表达式形态：`count(results, verdict == PASS)` / `sum(xs, n)` / `union(xs)` /
    `any(xs, ok)`。`data` 为 frontmatter dict。非法表达式 → ValueError。
    """
    m = _DERIVE_RE.match(expr or "")
    if not m:
        raise ValueError(f"非法 derive 表达式: {expr!r}")
    op, name, pred = m.group(1), m.group(2).strip(), m.group(3)
    value = data.get(name)
    if op == "count":
        items = value if isinstance(value, list) else []
        p = _predicate(pred)
        return sum(1 for it in items if p(it))
    if op == "sum":
        items = value if isinstance(value, list) else []
        p = _predicate(pred) if pred else (lambda _it: True)
        total = 0
        for it in items:
            if not p(it):
                continue
            if isinstance(it, dict):
                total += 1
            else:
                total += int(it)
        return total
    if op == "union":
        items = value if isinstance(value, list) else []
        out = []
        for it in items:
            k = it.get(pred) if isinstance(it, dict) and pred else it
            if k not in out:
                out.append(k)
        return out
    if op == "any":
        items = value if isinstance(value, list) else []
        p = _predicate(pred)
        return any(p(it) for it in items)
    raise ValueError(f"不支持的 derive 算子: {op!r}（只允许 count/sum/union/any）")


# ---------------------------------------------------------------------------
# render（渲染块内容）
# ---------------------------------------------------------------------------


def render(kind, value):
    """按 render 种类生成块内容（确定性，供 gate 逐字节比对）。"""
    if kind == "results_table":
        lines = ["| BDD | 结论 | 证据 |", "|---|---|---|"]
        for item in (value if isinstance(value, list) else []):
            if not isinstance(item, dict):
                continue
            bdd = item.get("bdd", "")
            verdict = item.get("verdict", "")
            evidence = item.get("evidence")
            if isinstance(evidence, list):
                ev = ", ".join(str(e) for e in evidence)
            else:
                ev = "" if evidence is None else str(evidence)
            lines.append(f"| {bdd} | {verdict} | {ev} |")
        return "\n".join(lines)
    if kind == "scalar":
        return "" if value is None else str(value)
    # 未知种类：fail-closed 到字符串（不静默丢内容）
    return "" if value is None else str(value)


def main():
    """极简 CLI（供人与调试）：--validate F JSON | --derive EXPR JSON。"""
    import json

    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: agate_schema.py --derive <expr> <json> | <instance-json> <schema-json>\n")
        return 2
    if args[0] == "--derive":
        if len(args) != 3:
            sys.stderr.write("用法: agate_schema.py --derive <expr> <json>\n")
            return 2
        print(derive(args[1], json.loads(args[2])))
        return 0
    if len(args) == 2:
        errors = validate(json.loads(args[0]), json.loads(args[1]))
        for path, msg in errors:
            print(f"{path}: {msg}")
        return 1 if errors else 0
    sys.stderr.write("用法: agate_schema.py --derive <expr> <json> | <instance-json> <schema-json>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
