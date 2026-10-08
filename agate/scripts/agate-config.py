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
import agate_schema

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
        "用法: agate-config.py <init|validate|get <field>|set <field> <value>|unset <field>|explain <field>|list|show>\n"
        "  init           生成初始声明文件（幂等，已存在不覆盖）\n"
        "  validate       按 schema 校验声明（0=合法，非 0=非法/缺失）\n"
        "  get <f>        输出单一字段客观值（点分路径，如 project.language）\n"
        "  set <f> <v>    写入点分路径字段（可加 --append），写入前经 schema 复验\n"
        "  unset <f>      移除点分路径字段（幂等）\n"
        "  explain <f>    解释字段类型/消费方/当前值 + 修复命令\n"
        "  list           列出声明的全部字段路径\n"
        "  show           展示完整声明\n"
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
    """draft-07 子集递归校验——单源 = agate_schema（TAG0050 批 B，BDD-50）。

    本处不再自带递归实现，只把 `agate_schema.iter_errors()` 的结构化错误映射为
    既有人类可读消息。
    """
    for p, code, detail in agate_schema.iter_errors(node, schema, path):
        if code == "type":
            errors.append(f"{p or '<root>'}: 期望 {detail['expected']}，实际 {detail['actual']}")
        elif code == "enum":
            errors.append(f"{p}: {detail['value']!r} 不在允许枚举 {detail['allowed']!r}")
        elif code == "required":
            errors.append(f"{path + '.' if path else ''}{detail['field']}: 缺失必填字段")
        elif code == "unknown":
            errors.append(f"{path + '.' if path else ''}{detail['field']}: 未知字段（不在 schema 允许的字段内）")
        elif code == "minItems":
            errors.append(f"{p}: 数组长度 {detail['length']} < minItems {detail['min']}")
        elif code == "pattern":
            errors.append(f"{p}: {detail['value']!r} 不匹配 pattern {detail['pattern']}")


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


def _config_path(project_root):
    return os.path.join(project_root, CONFIG_FILE)


def _load_raw_config(project_root):
    """读原始声明（dict, existed）；缺失/不可解析时从初始模板起步（未创建）。"""
    path = _config_path(project_root)
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data, True
        except Exception:
            pass
    return yaml.safe_load(_INIT_TEMPLATE), False


def _coerce_scalar(text):
    if text == "true":
        return True
    if text == "false":
        return False
    try:
        return int(text)
    except ValueError:
        return text


def _write_config(project_root, cfg):
    with open(_config_path(project_root), "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)


def _set_dotted(cfg, field, value, append):
    parts = field.split(".")
    node = cfg
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    leaf = parts[-1]
    if append:
        cur = node.get(leaf)
        if not isinstance(cur, list):
            cur = [] if cur is None else [cur]
        cur.append(value)
        node[leaf] = cur
    else:
        node[leaf] = value


def _unset_dotted(cfg, field):
    parts = field.split(".")
    node = cfg
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]
    if isinstance(node, dict):
        node.pop(parts[-1], None)


def _cmd_set(project_root, field, value, append=False):
    """写入点分路径字段（TAG0050 批 B，修复 F14 的 set 部分）；写入前经 agate_schema 复验。

    ⚠️ 仅就地更新**已存在**的声明文件；文件缺失时**不创建**（创建是 `init` 的职责）——
    避免在无关 cwd（如协议源仓库根）意外物化一份项目声明，并保持迁移期「无声明的
    存量项目行为不变」。
    """
    cfg, existed = _load_raw_config(project_root)
    _set_dotted(cfg, field, _coerce_scalar(value), append)
    try:
        schema, _ = _load_schema()
    except Exception as exc:
        sys.stderr.write(f"schema 不可用: {exc}\n")
        return 1
    errors = []
    _validate_node(cfg, schema, "", errors)
    if errors:
        sys.stderr.write("写入被拒绝（违反 schema）:\n")
        for err in errors:
            sys.stderr.write("  - " + err + "\n")
        return 1
    if not existed:
        print(f"校验通过（无声明文件，未创建）：{field} = {value!r}；创建请运行 agate-config.py init")
        return 0
    _write_config(project_root, cfg)
    print(f"已写入 {field} = {value!r}")
    return 0


def _cmd_unset(project_root, field):
    """移除点分路径字段（幂等：字段不存在也算成功）。"""
    cfg, existed = _load_raw_config(project_root)
    _unset_dotted(cfg, field)
    if existed:
        _write_config(project_root, cfg)
    print(f"已移除 {field}")
    return 0


def _cmd_explain(project_root, field):
    """解释一个点分路径字段：类型/枚举/消费方/当前值 + 可照抄的修复命令。"""
    print(f"字段: {field}")
    try:
        schema, _ = _load_schema()
        node = schema
        for part in field.split("."):
            props = node.get("properties", {}) if isinstance(node, dict) else {}
            node = props.get(part)
            if node is None:
                break
        if isinstance(node, dict):
            if "type" in node:
                print(f"类型: {node['type']}")
            if "enum" in node:
                print("允许值: " + ", ".join(str(x) for x in node["enum"]))
            if "description" in node:
                print(f"说明: {node['description']}")
            if "consumed_by" in node:
                print(f"消费方: {node['consumed_by']}")
    except Exception:
        pass
    cfg = agate_common.read_project_config(project_root)
    if cfg.get("present"):
        value, found = _get_field(_public_config(cfg), field)
        if found:
            shown = yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip()
            print(f"当前值: {shown}")
        else:
            print("当前值: （未设置）")
    else:
        print("当前值: （声明文件缺失）")
    print(f"修复命令: agate-config.py set {field} <值>")
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
    if cmd == "set":
        if len(argv) < 3:
            sys.stderr.write("用法: agate-config.py set <点分路径> <value> [--append]\n")
            return 2
        return _cmd_set(project_root, argv[1], argv[2], append="--append" in argv[3:])
    if cmd == "unset":
        if len(argv) != 2:
            sys.stderr.write("用法: agate-config.py unset <点分路径>\n")
            return 2
        return _cmd_unset(project_root, argv[1])
    if cmd == "explain":
        if len(argv) != 2:
            sys.stderr.write("用法: agate-config.py explain <点分路径>\n")
            return 2
        return _cmd_explain(project_root, argv[1])
    if cmd == "list":
        return _cmd_list(project_root)
    if cmd == "show":
        return _cmd_show(project_root)
    sys.stderr.write(f"未知子命令: {cmd}\n")
    _usage()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
