#!/usr/bin/env python
"""agate-config.py — 项目形态声明（agate.config.yaml）读写/校验 CLI（TAG0042 批 2）

项目形态（语言 / 包管理器 / 验证命令 / 发版方式等）由项目根的声明文件
`agate.config.yaml` 描述；协议 gate / 推进 / 证据路径读取该声明决定行为，
不写死任何单一技术栈（BDD-3）。

子命令（退出码：0=成功，非 0=失败）：
  init            生成初始声明文件（已存在则不覆盖，幂等）
  validate        按 rules/schema/project-config.schema.json 校验声明
  get <field>     输出单一字段客观值（点分路径，如 project.language）
  list            列出声明的全部字段路径
  show            展示完整声明

**唯一读取函数**（BDD-6）：声明解析只经 `agate_common.read_project_config`；
本脚本不另写第二处声明解析实现（无旁路 YAML 解析）。

平台无关：显式 utf-8；无系统临时目录字面量；Python 3.8+（禁 match / str.removeprefix）。
"""

import json
import os
import sys

import yaml

import agate_common

CONFIG_FILE = "agate.config.yaml"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 声明 schema 相对协议根（scripts/ 的上一级）的路径。
_SCHEMA_REL = ("rules", "schema", "project-config.schema.json")

# 缺字段默认值由 agate_common 单一维护（read_project_config）；此处仅做内部键过滤。
_INTERNAL_KEYS = ("present", "parse_error")

# init 生成的初始声明（形态值用中性占位，不含任何单一项目假设）。
_INIT_TEMPLATE = (
    "schema_version: 1\n"
    "project:\n"
    "  language: unknown\n"
    "  package_manager: unknown\n"
    "verify:\n"
    "  commands: []\n"
    "release:\n"
    "  preset: semver-changelog-tag\n"
    "paths:\n"
    "  evidence: .agate-evidence\n"
)


def _usage():
    sys.stderr.write(
        "用法: agate-config.py <init|validate|get <field>|list|show>\n"
        "  init      生成初始声明文件（幂等，已存在不覆盖）\n"
        "  validate  按 schema 校验声明（0=合法，非 0=非法/缺失）\n"
        "  get <f>   输出单一字段客观值（点分路径，如 project.language）\n"
        "  list      列出声明的全部字段路径\n"
        "  show      展示完整声明\n"
    )


def _public_config(cfg):
    """去掉内部标记键（present / parse_error），只留声明内容。"""
    return {k: v for k, v in cfg.items() if k not in _INTERNAL_KEYS}


def _leaf_paths(node, prefix=""):
    """递归收集叶子字段的点分路径。"""
    paths = []
    if isinstance(node, dict):
        for key in node:
            child = (prefix + "." + key) if prefix else key
            paths.extend(_leaf_paths(node[key], child))
    else:
        paths.append(prefix)
    return paths


def _get_field(cfg, field):
    """按点分路径取值 → (value, found)。"""
    node = cfg
    for part in field.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


def _schema_path():
    protocol_root = os.path.dirname(_SCRIPT_DIR)
    return os.path.join(protocol_root, *_SCHEMA_REL)


def _load_schema():
    path = _schema_path()
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def _validate_node(node, schema, path, errors):
    """draft-07 子集递归校验（object / array / integer / string / boolean + enum）。"""
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(node, dict):
            errors.append(f"{path or '<root>'}: 期望映射(object)，实际 {type(node).__name__}")
            return
        for req in schema.get("required", []):
            if req not in node:
                errors.append(f"{path + '.' if path else ''}{req}: 缺失必填字段")
        properties = schema.get("properties", {})
        for key, value in node.items():
            child = (path + "." + key) if path else key
            if key in properties:
                _validate_node(value, properties[key], child, errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{child}: 未知字段（不在 schema 允许的字段内）")
    elif schema_type == "array":
        if not isinstance(node, list):
            errors.append(f"{path}: 期望列表(array)，实际 {type(node).__name__}")
            return
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(node):
                _validate_node(item, item_schema, f"{path}[{index}]", errors)
    elif schema_type == "integer":
        if isinstance(node, bool) or not isinstance(node, int):
            errors.append(f"{path}: 期望整数，实际 {node!r}")
            return
    elif schema_type == "string":
        if not isinstance(node, str):
            errors.append(f"{path}: 期望字符串，实际 {node!r}")
            return
    elif schema_type == "boolean":
        if not isinstance(node, bool):
            errors.append(f"{path}: 期望布尔值，实际 {node!r}")
            return
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: {node!r} 不在允许枚举 {schema['enum']!r}")


def _cmd_init(project_root):
    path = os.path.join(project_root, CONFIG_FILE)
    if os.path.exists(path):
        print(f"声明文件已存在，未覆盖（幂等）: {CONFIG_FILE}")
        return 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(_INIT_TEMPLATE)
    print(f"已生成声明文件: {CONFIG_FILE}")
    return 0


def _cmd_validate(project_root):
    cfg = agate_common.read_project_config(project_root)
    if not cfg.get("present"):
        sys.stderr.write(f"声明文件缺失或不可解析: {CONFIG_FILE}（迁移期不阻断）\n")
        return 1
    schema, _ = _load_schema()
    errors = []
    _validate_node(_public_config(cfg), schema, "", errors)
    if errors:
        sys.stderr.write(f"声明校验失败（{CONFIG_FILE}）:\n")
        for err in errors:
            sys.stderr.write("  - " + err + "\n")
        return 1
    return 0


def _cmd_get(project_root, field):
    cfg = agate_common.read_project_config(project_root)
    if not cfg.get("present"):
        sys.stderr.write(f"声明文件缺失: {CONFIG_FILE}\n")
        return 1
    value, found = _get_field(_public_config(cfg), field)
    if not found:
        sys.stderr.write(f"字段不存在: {field}\n")
        return 1
    if isinstance(value, str):
        print(value)
    else:
        sys.stdout.write(yaml.safe_dump(value, allow_unicode=True, sort_keys=False))
    return 0


def _cmd_list(project_root):
    cfg = agate_common.read_project_config(project_root)
    if not cfg.get("present"):
        sys.stderr.write(f"声明文件缺失: {CONFIG_FILE}\n")
        return 1
    for leaf in sorted(_leaf_paths(_public_config(cfg))):
        print(leaf)
    return 0


def _cmd_show(project_root):
    cfg = agate_common.read_project_config(project_root)
    if not cfg.get("present"):
        sys.stderr.write(f"声明文件缺失: {CONFIG_FILE}\n")
        return 1
    sys.stdout.write(yaml.safe_dump(_public_config(cfg), allow_unicode=True, sort_keys=False))
    return 0


def main(argv):
    if not argv:
        _usage()
        return 2
    cmd = argv[0]
    if cmd in ("-h", "--help"):
        _usage()
        return 0
    project_root = os.getcwd()
    if cmd == "init":
        return _cmd_init(project_root)
    if cmd == "validate":
        return _cmd_validate(project_root)
    if cmd == "get":
        if len(argv) != 2:
            sys.stderr.write("用法: agate-config.py get <field>\n")
            return 2
        return _cmd_get(project_root, argv[1])
    if cmd == "list":
        return _cmd_list(project_root)
    if cmd == "show":
        return _cmd_show(project_root)
    sys.stderr.write(f"未知子命令: {cmd}\n")
    _usage()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
