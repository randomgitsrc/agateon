#!/usr/bin/env python3
"""check-yaml-schema.py — rules/*.yaml 对 rules/schema/*.json 的 draft-07 子集校验器（TAG0021 M0）

被测契约（P2-design §3.2 / P3 BDD-1）：校验 AGATE_ROOT/rules/{phases,dispatch,roles}.yaml
对 rules/schema/{phases,dispatch,roles}.schema.json：
  * 全部 YAML 合法且过 schema → exit 0
  * 任一非法字段（additionalProperties 拒绝）/ 错误枚举 / 错误类型 / 缺 required /
    schema 自身损坏（非法 JSON）→ exit 非 0

支持的 draft-07 子集：type / required / enum / properties / items / additionalProperties /
minItems。数值刻度的 minimum/exclusiveMinimum 不用（P2-design §3.2，防子集实现膨胀）。
手写校验（不依赖 jsonschema 包，依赖清单仅 pyyaml+Pillow），机制参照
agate-frontmatter-check.py 的 SCHEMAS（required/enums/types/min_values 手写遍历）。

R5 schema 自身健全性自检：schema 根必须是 object（type=object + properties + required），
required 引用的键必须在 properties 中声明——防 schema 形同虚设。

用法：check-yaml-schema.py（无参数）。AGATE_ROOT 解析链 = env → 项目声明 → current →
脚本路径上溯（agate_common.resolve_agate_root）。
输出：SCHEMA-<file>: OK / SCHEMA-<file>: ERROR <path> <msg>（仿 rep 编号风格）。
退出：0 = 全过；1 = 任一 ERROR（含解析失败 / schema 损坏）。

平台无关（BDD-16）：无裸解释器、无硬编码 PATH、无 /tmp、无软链假设；文本 I/O 显式 utf-8。
Python 3.8+（无 match / str.removeprefix）。
"""

import json
import os
import sys

try:
    import yaml

    import agate_schema
    from agate_common import resolve_agate_root
except ImportError:
    sys.stderr.write("check-yaml-schema.py: 需要 pyyaml 与 agate_common（agate 脚本公共库）。pip install pyyaml 或确认在 agate/scripts/ 下运行\n")
    sys.exit(1)

# (规则文件基名, yaml 文件名, schema 文件名)
_RULES = (
    ("phases", "phases.yaml", "phases.schema.json"),
    ("dispatch", "dispatch.yaml", "dispatch.schema.json"),
    ("roles", "roles.yaml", "roles.schema.json"),
    # markers.yaml：正文标记形态单源（设计 docs/design-notes/design-marker-single-source.md）。
    # 纳入 S-5 的理由：它是**判据**的权威源——schema 形同虚设会让「注册表写错」静默传播到
    # 所有消费方（条目字段写错 ⇒ agate_markers.pattern() 生成错正则，且无人发现）。
    ("markers", "markers.yaml", "markers.schema.json"),
)


def _validate_value(value, schema, path, errors):
    """递归校验单个值 vs 子集 schema；错误追加到 errors（(path, msg) 列表）。

    TAG0050 批 B（BDD-50）：递归校验**单源**在 `agate_schema`——本处不再自带
    第二个递归实现，只把结构化错误映射为既有消息格式。
    """
    errors.extend(agate_schema.validate(value, schema, path))


def _schema_self_check(file_name, schema):
    """R5：schema 自身健全性（根 object + properties + required 引用闭合）。"""
    errs = []
    if not isinstance(schema, dict):
        errs.append(("", "schema 根不是对象（损坏）"))
        return errs
    if schema.get("type") != "object":
        errs.append(("", "schema 根 type 应为 object"))
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        errs.append(("", "schema 根缺 properties（应为本文件顶层键的 dict）"))
    required = schema.get("required")
    if not isinstance(required, list):
        errs.append(("", "schema 根缺 required（list）"))
    elif isinstance(properties, dict):
        for key in required:
            if key not in properties:
                errs.append(("", f"required 字段 {key} 未在 properties 中声明（schema 自相矛盾）"))
    return errs


def _check_one(file_name, yaml_path, schema_path):
    """校验单个 rules 文件对 → ERROR 列表（空 = OK）。"""
    errors = []
    data = None
    schema = None
    if not os.path.isfile(yaml_path):
        errors.append(("", f"文件缺失 {os.path.relpath(yaml_path)}"))
    else:
        try:
            with open(yaml_path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except Exception as exc:
            errors.append(("", f"YAML 解析失败: {exc}"))
    if not os.path.isfile(schema_path):
        errors.append(("", f"文件缺失 {os.path.relpath(schema_path)}"))
    else:
        try:
            with open(schema_path, encoding="utf-8") as fh:
                schema = json.load(fh)
        except Exception as exc:
            errors.append(("", f"schema JSON 解析失败: {exc}"))
    if schema is not None:
        errors.extend(_schema_self_check(file_name, schema))
        if data is not None and isinstance(schema, dict):
            _validate_value(data, schema, "", errors)
    return errors


def _resolve_root():
    """AGATE_ROOT 解析：env 优先（返回原值）→ agate_common 四层链。"""
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root
    try:
        return resolve_agate_root(__file__)
    except Exception:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    root = _resolve_root()
    if not root:
        sys.stderr.write("FATAL: 无法解析 AGATE_ROOT（env / .agate-version / current / 脚本上溯均不可用）\n")
        sys.exit(1)
    rules_dir = os.path.join(root, "rules")
    if not os.path.isdir(rules_dir):
        sys.stderr.write(f"FATAL: AGATE_ROOT={root} 下缺少 rules/ 目录\n")
        sys.exit(1)

    any_error = False
    for file_name, yaml_name, schema_name in _RULES:
        yaml_path = os.path.join(rules_dir, yaml_name)
        schema_path = os.path.join(rules_dir, "schema", schema_name)
        errors = _check_one(file_name, yaml_path, schema_path)
        if errors:
            any_error = True
            for path, msg in errors:
                loc = f"{path} " if path else ""
                sys.stdout.write(f"SCHEMA-{file_name}: ERROR {loc}{msg}\n")
        else:
            sys.stdout.write(f"SCHEMA-{file_name}: OK\n")
    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    main()
