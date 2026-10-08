#!/usr/bin/env python3
"""agate-md-field-set.py — 结构化字段写入工具（TAG0024 P4，RM-AG0048 一期，P2-design.md §3）

CLI 形态（FILE 环境变量传路径，与 agate-md-field-get.py 同惯例）：
  agate-md-field-set.py <key> <value>    # 写入一个字段
  agate-md-field-set.py --list           # 列出本文件应填字段 + 当前值 + 剩余缺失

同源铁律（P2-design.md §2 候选方案 A / §3.2，BDD-15）：value 校验 importlib 动态加载
agate-frontmatter-check.py 的 SCHEMAS/_check()、agate-md-field-get.py 的字段分类常量、
check-judge-verdict.py 的 _VALID_STATUS——逐字节复用，不复制、不重写。仿
check-routing.py._load_script（第 41-52 行）的加载 + 模块级缓存模式。

key 白名单（BDD-17）：GENERIC_HEADER_KEYS ∪ phases.yaml 全部 task_fields（运行时并集计算，
不手抄）。证据字段（BDD-9）/追加-嵌套字段（BDD-18）一期明确拒绝写入。status 字段按 basename
分派固定枚举 + 角色白名单（BDD-3/4，UX 引导，非安全边界，见 design-md-field-set.md §7.1）。

原子写（BDD-10）：tempfile.mkstemp 同目录 + os.replace，写入中断不落盘半截内容。
"""

import contextlib
import importlib.util
import os
import re
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import agate_common  # noqa: E402 — 普通共享库 import（P2-design §2 候选 A，无连字符问题）
import agate_schema  # noqa: E402 — 结构校验 / derive / render 单源（TAG0050 批 B，BDD-48/50）

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-md-field-set: 需要 pyyaml\n")
    sys.exit(1)

# 渲染块标记（TAG0050 批 B，BDD-48）。生成/校验的形态单源在 agate_schema。
RENDER_MARKER = "AGATE:RENDER"


# ---------- importlib 动态加载（同源铁律，仿 check-routing.py:41-52 _load_script） ----------

_CACHE = {}


def _load_script(name, module_name=None):
    """importlib 加载同目录带连字符文件名脚本，模块级缓存避免重复 exec_module。"""
    key = name
    if key not in _CACHE:
        path = os.path.join(SCRIPT_DIR, name + ".py")
        spec = importlib.util.spec_from_file_location(module_name or name.replace("-", "_"), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CACHE[key] = mod
    return _CACHE[key]


def _fm_check():
    """agate-frontmatter-check.py：取 SCHEMAS / _check()（BDD-1~3, 15）。"""
    return _load_script("agate-frontmatter-check", "agate_frontmatter_check")


def _fm_get():
    """agate-md-field-get.py：取字段分类常量（BOOL/LIST/INT/STRING/NO_FALLBACK_*/JSON）。"""
    return _load_script("agate-md-field-get", "agate_md_field_get")


def _judge_verdict():
    """check-judge-verdict.py：取 _VALID_STATUS（P6.5 status 枚举同源来源）。"""
    return _load_script("check-judge-verdict", "check_judge_verdict")


# ---------- key 白名单（P2-design.md §3.1，BDD-17） ----------

GENERIC_HEADER_KEYS = frozenset({
    "phase", "task_id", "type", "parent", "trace_id", "status", "created", "agent",
})  # 来源：agate/assets/templates/task-files.md「通用 Header」（纯 prose，硬编码，供未来
    # 该文档改版时人工同步）


def _writable_keys(rules_root):
    """GENERIC_HEADER_KEYS ∪ phases.yaml 全部 task_fields（机械并集，含 agent——排除 agent
    是调用方的责任，见 §3.1"排除"节；本函数本身只做纯并集计算，BDD-17 白盒断言的正是这一点）。
    """
    phases = agate_common.read_rules_yaml(rules_root, "phases") or {}
    task_field_union = set()
    for p in phases.get("phases", []) or []:
        task_field_union.update(p.get("task_fields", []) or [])
    return set(GENERIC_HEADER_KEYS) | task_field_union


# ---------- status / agent 角色权限（P2-design.md §3.4，BDD-3/4） ----------

STATUS_ENUM_BY_BASENAME = {
    # task-files.md 通用 Header：status: {draft|approved|rejected|done}
    # + dispatch-prompt.md「Review 角色特别指令」：review 类文件补充 needs-revision
    "P1-review.md": frozenset({"draft", "approved", "rejected", "needs-revision"}),
    "P2-review.md": frozenset({"draft", "approved", "rejected", "needs-revision"}),
    "P4-review.md": frozenset({"draft", "approved", "rejected", "needs-revision"}),
}
DEFAULT_STATUS_ENUM = frozenset({"draft", "approved", "rejected", "done"})


def _status_enum_for(basename):
    if basename == "P6.5-judge-verdict.md":
        return frozenset(_judge_verdict()._VALID_STATUS)
    return STATUS_ENUM_BY_BASENAME.get(basename, DEFAULT_STATUS_ENUM)


def _review_role_names(agate_root):
    """{agate_root}/assets/review-roles/*.md 文件名集合（去 .md）。解析失败返回 None（调用方
    fail-closed）。role-system.md §37-74「第二层：评审角色」是该目录的权威声明来源。
    """
    roles_dir = os.path.join(agate_root, "assets", "review-roles")
    try:
        names = {os.path.splitext(f)[0] for f in os.listdir(roles_dir) if f.endswith(".md")}
    except OSError:
        return None
    return names


def _check_status_role(basename, existing_agent, agate_root):
    """status 写非 draft 值时的角色校验（design note §7.1/§7.4：UX 引导，非安全边界）。

    通过返回 None；不通过返回错误信息字符串。
    """
    if existing_agent == "main":
        return (
            "ERROR: status 写入被拒绝——agent=main（主 Agent 不可自行批准评审，"
            "该 fail-closed 判定与 check-gate.py 的 agent==main 判定同源）"
        )
    role_names = _review_role_names(agate_root)
    if role_names is None:
        return "ERROR: status 写入被拒绝——无法解析角色清单（fail-closed，见 role-system.md）"
    if existing_agent not in role_names:
        return (
            f"ERROR: status 写入被拒绝（{basename}）——该字段按协议应由 review/judge 类角色填写"
            f"（见 role-system.md），当前 agent={existing_agent!r} 不在角色清单内"
        )
    return None


# ---------- value 强类型转换（P2-design.md §3.2） ----------


def _split_list(raw):
    return raw.split()


def _coerce_typed(raw, expected, key):
    if expected is bool:
        if raw not in ("true", "false"):
            raise ValueError(f"{key} 须为 true/false（当前: {raw!r}）")
        return raw == "true"
    if expected is int:
        try:
            return int(raw)
        except ValueError as e:
            raise ValueError(f"{key} 须为整数（当前: {raw!r}）") from e
    if expected is list:
        return _split_list(raw)
    return raw


def _coerce_value(key, raw, schema, get_mod):
    """把 CLI 字符串参数转换为写入 frontmatter 用的 Python 值（P2-design §3.2 分派）。

    1) SCHEMAS 覆盖字段：按 schema['types'] 类型转换
    2) P6.5 专属三字段（criteria_total/criteria_passed int，verdict_evidence list）：
       无 SCHEMAS/KNOWN_OPS 覆盖，类型依据 check-judge-verdict.py 文档口径（读代码确认）
    3) get 工具字段分类（BOOL/INT/LIST）：类型强校验
    4) 其余（STRING_FIELDS 等）：原样透传，不发明枚举
    """
    if schema and key in schema.get("types", {}):
        return _coerce_typed(raw, schema["types"][key], key)
    # 快照声明的主产出安全字段（设计 §4）：prod_touched 为 bool、prod_touched_detail 为 str。
    if key == "prod_touched":
        return _coerce_typed(raw, bool, key)
    if key in ("criteria_total", "criteria_passed"):
        return _coerce_typed(raw, int, key)
    if key == "verdict_evidence":
        return _split_list(raw)
    if key in get_mod.BOOL_FIELDS or key in get_mod.NO_FALLBACK_BOOL_FIELDS:
        return _coerce_typed(raw, bool, key)
    if key in get_mod.INT_FIELDS or key in get_mod.NO_FALLBACK_INT_FIELDS:
        return _coerce_typed(raw, int, key)
    if key in get_mod.LIST_FIELDS:
        return _split_list(raw)
    return raw


# ---------- 原子写（P2-design.md §3.5，BDD-10） ----------


def _atomic_write(path, content):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".md-field-set-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


# ---------- 通用 helper ----------


def _read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def _phase_for_basename(phases_data, basename):
    """basename → phases.yaml 中声明该文件为 outputs 的阶段条目（供 --list / 剩余缺失使用）。"""
    for p in phases_data.get("phases", []) or []:
        for outp in p.get("outputs", []) or []:
            if isinstance(outp, dict) and outp.get("file") == basename:
                return p
    return None


def _remaining_missing(basename, phases_data, new_fm, body):
    """写入后剩余缺失字段清单（BDD-6/16）：frontmatter 字段查 new_fm，gate_commands 查正文块。"""
    phase = _phase_for_basename(phases_data, basename)
    if not phase:
        return []
    missing = []
    for f in phase.get("task_fields", []) or []:
        if f == "gate_commands":
            has_block, _ = agate_common.parse_gate_commands_block(body)
            if not has_block:
                missing.append(f)
            continue
        if f not in new_fm or new_fm.get(f) is None:
            missing.append(f)
    return missing


def _missing_report(missing):
    if not missing:
        return ""
    return "剩余缺失: " + ", ".join(missing)


# ---------- 契约字段（快照 files 节，TAG0050 批 B，设计 §3.1） ----------


def _contract_fields(file_path):
    """本文件在快照 `files` 节登记的字段 → {key: spec}（无登记 → {}）。

    等级优先取任务账本等级，回退协议当前等级；快照不可用 → {}（不阻断旧写法）。
    """
    task_dir = os.path.dirname(os.path.abspath(file_path))
    try:
        level = agate_common.task_level(task_dir, __file__) or agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
    except Exception:
        contract = {}
    files = contract.get("files") if isinstance(contract, dict) else None
    if not isinstance(files, dict):
        return {}
    spec = files.get(os.path.basename(file_path))
    if not isinstance(spec, dict):
        return {}
    fields = spec.get("fields")
    return fields if isinstance(fields, dict) else {}


def _field_spec(file_path, key):
    return _contract_fields(file_path).get(key)


def _declared_safety_keys(file_path):
    """快照声明 `prod_touched` 的文件（declaration_files ∪ primary_outputs 主产出）
    → 安全字段集合 {prod_touched, prod_touched_detail}；否则空集。

    TAG0050 批 C（设计 §4）：`prod_touched` 是**主产出**必填字段（不只 P6）。gate 输出的
    `set prod_touched …` 修复命令对非 P6 主产出（如 P4-implementation.md）须**真能执行**
    （修复 H1 / cso 复审：原可写面仅覆盖 P6 契约字段）。
    """
    basename = os.path.basename(file_path)
    task_dir = os.path.dirname(os.path.abspath(file_path))
    try:
        level = agate_common.task_level(task_dir, __file__) or agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
    except Exception:
        contract = {}
    if not isinstance(contract, dict):
        return frozenset()
    names = {str(x) for x in (contract.get("declaration_files") or [])}
    outputs = contract.get("primary_outputs")
    if isinstance(outputs, dict):
        names.update(str(v) for v in outputs.values())
    if basename in names:
        return frozenset({"prod_touched", "prod_touched_detail"})
    return frozenset()


def _coerce_pair(prop_schema, raw):
    """按元素属性 schema 把 CLI 字符串值转换为 Python 值。"""
    if not isinstance(prop_schema, dict):
        return raw
    t = prop_schema.get("type")
    if t == "integer":
        return int(raw)
    if t == "boolean":
        return raw == "true"
    if t == "array":
        return [p for p in raw.split(",") if p]
    return raw


def _build_item(spec, pairs):
    """按元素 schema 把 `k=v` 列表构建为 dict；非法键/值 → ValueError。"""
    schema = spec.get("schema") or {}
    item_schema = schema.get("items") or {}
    props = item_schema.get("properties") or {}
    item = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"追加/更新项须为 k=v 形式：{pair!r}")
        k, v = pair.split("=", 1)
        item[k] = _coerce_pair(props.get(k), v)
    return item


def _render_fields(file_path, fm):
    """{key: 渲染内容}：契约中带 render 且当前值存在的字段。"""
    out = {}
    for key, spec in _contract_fields(file_path).items():
        kind = spec.get("render") if isinstance(spec, dict) else None
        if not kind:
            continue
        out[key] = agate_schema.render(kind, fm.get(key))
    return out


def _rewrite_render_blocks(text, rendered):
    """把文件里的 AGATE:RENDER 块替换为 `rendered[key]`；缺失的块追加到正文末尾。"""
    text = text.replace("\r\n", "\n")
    present = set()
    for block in agate_schema.find_render_blocks(text):
        key = block["key"]
        content = rendered.get(key)
        if content is None:
            continue
        present.add(key)
        new_block = agate_schema.render_block(key, content)
        text = text[:block["start"]] + new_block + text[block["end"]:]
    for key, content in rendered.items():
        if key in present:
            continue
        text = text.rstrip("\n") + "\n\n" + agate_schema.render_block(key, content) + "\n"
    return text


def _compose(fm, body):
    """拼回 frontmatter + 正文（正文以换行开头时不重复插空行）。"""
    fm_dump = yaml.safe_dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    if body == "":
        return "---\n" + fm_dump + "---"
    if body.startswith("\n"):
        return "---\n" + fm_dump + "---" + body
    return "---\n" + fm_dump + "---\n" + body


def _write(file_path, fm, body, auto_render=True):
    new_text = _compose(fm, body)
    if auto_render:
        with contextlib.suppress(Exception):
            new_text = _rewrite_render_blocks(new_text, _render_fields(file_path, fm))
    _atomic_write(file_path, new_text)


# ---------- 子命令 ----------


def _cmd_list(file_path):
    basename = os.path.basename(file_path)
    text = _read_text(file_path)
    fm, body = agate_common.split_frontmatter(text)
    fm = fm if isinstance(fm, dict) else {}

    rules_root = agate_common.resolve_rules_root(__file__)
    phases_data = agate_common.read_rules_yaml(rules_root, "phases") or {}
    phase = _phase_for_basename(phases_data, basename)

    lines = []
    if phase is None:
        lines.append(
            f"未在 phases.yaml 找到 {basename} 对应阶段；通用 Header 字段: "
            + ", ".join(sorted(GENERIC_HEADER_KEYS))
        )
    else:
        lines.append(f"{basename}（阶段 {phase.get('id')}）可填字段:")
        for f in phase.get("task_fields", []) or []:
            if f == "gate_commands":
                has_block, entries = agate_common.parse_gate_commands_block(body)
                cur = f"已声明 {len(entries)} 项" if has_block else "未声明"
            else:
                v = fm.get(f)
                cur = "未设置" if v is None else repr(v)
            lines.append(f"  - {f}: 当前值 = {cur}")

    missing = _remaining_missing(basename, phases_data, fm, body) if phase else []
    report = _missing_report(missing)
    if report:
        lines.append(report)

    print("\n".join(lines))
    return 0


def _cmd_set(file_path, key, value):
    basename = os.path.basename(file_path)
    text = _read_text(file_path)
    fm, body = agate_common.split_frontmatter(text)
    existing_fm = fm if isinstance(fm, dict) else {}

    get_mod = _fm_get()

    # TAG0050 批 B（设计 §3.3 / cso F-2）：契约驱动的系统字段拒写——凡快照 files 节登记
    # `writer: system` 的字段（含**未来**新增、且不在证据字段表内的字段）一律拒写，并指明
    # derive 来源。不再仅靠「证据字段表」的偶发耦合。
    contract_spec = _field_spec(file_path, key)
    if isinstance(contract_spec, dict) and contract_spec.get("writer") == "system":
        derive = contract_spec.get("derive")
        sys.stderr.write(
            f"ERROR: {key} 是系统字段（writer: system），由契约现算，不可手动填写"
            + (f"；来源: derive {derive}\n" if derive else "\n")
        )
        return 1

    # 证据字段一期拒绝（BDD-9）：get 工具.NO_FALLBACK_INT_FIELDS | {"regression_pass"}，
    # 动态取值不手抄 9+1 个字段名。
    evidence_fields = get_mod.NO_FALLBACK_INT_FIELDS | frozenset({"regression_pass"})
    if key in evidence_fields:
        sys.stderr.write(f"ERROR: {key} 是证据字段，由验证脚本产出，不可手动填写\n")
        return 1

    # 追加/嵌套字段一期拒绝（BDD-18）：NO_FALLBACK_LIST_FIELDS | JSON_FIELDS，动态取值。
    append_only_fields = get_mod.NO_FALLBACK_LIST_FIELDS | get_mod.JSON_FIELDS
    if key in append_only_fields:
        sys.stderr.write(
            f"ERROR: {key} 是追加/嵌套字段，一期 set 暂不支持覆盖式之外的写入\n"
        )
        return 1

    rules_root = agate_common.resolve_rules_root(__file__)
    # 可写面 = phases.yaml task_fields ∪ 通用 Header ∪ 本文件契约（快照 files 节）字段
    #        ∪ 快照声明的主产出安全字段（prod_touched / prod_touched_detail，设计 §4）。
    # ⚠️ TAG0050 批 B：解除旧的「agent 永久拒写」——七操作规格（P2 §3.1）要求 agent 可写，
    #    且新的 7 操作往返用例显式执行 `set agent`（见 P4-implementation-G2.md [DESIGN_GAP]）。
    writable = (_writable_keys(rules_root)
                | set(_contract_fields(file_path).keys())
                | _declared_safety_keys(file_path))
    if key not in writable:
        sys.stderr.write(
            "ERROR: 非法 key {!r}，合法 key 清单: {}\n".format(key, ", ".join(sorted(writable)))
        )
        return 1

    if key == "status":
        enum = _status_enum_for(basename)
        if value not in enum:
            sys.stderr.write(
                "ERROR: status 非法值 {!r}（合法值: {}）。该字段按协议应由 review/judge "
                "角色填写（见 role-system.md），建议改用合法值之一。\n".format(
                    value, "|".join(sorted(enum))
                )
            )
            return 1
        if value != "draft":
            agate_root = os.path.dirname(rules_root)
            role_err = _check_status_role(basename, existing_fm.get("agent"), agate_root)
            if role_err:
                sys.stderr.write(role_err + "\n")
                return 1
        coerced = value
    else:
        fm_check_mod = _fm_check()
        schema = fm_check_mod.SCHEMAS.get(basename)
        try:
            coerced = _coerce_value(key, value, schema, get_mod)
        except ValueError as e:
            sys.stderr.write(f"ERROR: {e}\n")
            return 1

        if schema and (key in schema.get("types", {}) or key in schema.get("enums", {})):
            candidate_fm = dict(existing_fm)
            candidate_fm[key] = coerced
            errors = fm_check_mod._check(basename, schema, candidate_fm)
            # 按 f"{basename}:{field}:" 前缀过滤，只透传本次候选写入的 key 相关错误
            # （P2-design §1.3 风险 6：防止无关字段的既有错误一并报出）。
            field_errors = [e for e in errors if e.startswith(f"{basename}:{key}:")]
            if field_errors:
                sys.stderr.write("\n".join(field_errors) + "\n")
                return 1

    new_fm = dict(existing_fm)
    new_fm[key] = coerced

    residual_line = ""
    if re.search(rf"^{re.escape(key)}:", body, re.MULTILINE):
        residual_line = f"WARNING: 检测到正文残留同名字段 {key}，frontmatter 优先，建议清理正文残留"

    try:
        # 无 frontmatter：_compose 在文件头插入新块，原文全文（body==原文）拼接在后面（BDD-12）。
        new_text = _compose(new_fm, body)
        # TAG0050 批 B：每次写入后重新渲染（设计 §3.4）。
        with contextlib.suppress(Exception):
            new_text = _rewrite_render_blocks(new_text, _render_fields(file_path, new_fm))
        _atomic_write(file_path, new_text)
    except Exception as e:
        sys.stderr.write(f"ERROR: 写入失败（{e}），未落盘\n")
        return 1

    out_lines = [f"OK: {key}={value} 已写入 {basename}"]
    if residual_line:
        out_lines.append(residual_line)

    phases_data = agate_common.read_rules_yaml(rules_root, "phases") or {}
    missing = _remaining_missing(basename, phases_data, new_fm, body)
    report = _missing_report(missing)
    if report:
        out_lines.append(report)

    print("\n".join(out_lines))
    return 0


def _load_fm_body(file_path):
    text = _read_text(file_path)
    fm, body = agate_common.split_frontmatter(text)
    return (fm if isinstance(fm, dict) else {}), body, (fm is None)


def _require_list_field(file_path, key):
    spec = _field_spec(file_path, key)
    if spec is None:
        sys.stderr.write(
            f"ERROR: {key!r} 不在本文件契约字段中（见快照 files 节；用 explain 查看可用字段）\n"
        )
        return None
    return spec


def _cmd_append(file_path, key, pairs):
    """向列表字段追加一个元素（TAG0050 批 B，设计 §3.4）。"""
    spec = _require_list_field(file_path, key)
    if spec is None:
        return 1
    try:
        item = _build_item(spec, pairs)
    except ValueError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 1
    fm, body, _ = _load_fm_body(file_path)
    cur = fm.get(key)
    if not isinstance(cur, list):
        cur = [] if cur is None else [cur]
    cur.append(item)
    fm[key] = cur
    try:
        _write(file_path, fm, body)
    except Exception as e:
        sys.stderr.write(f"ERROR: 写入失败（{e}），未落盘\n")
        return 1
    print(f"OK: {key} 追加一项 {item}")
    return 0


def _cmd_upsert(file_path, key, pk, pairs):
    """按主键 upsert 列表字段中一个元素（TAG0050 批 B，设计 §3.4）。"""
    spec = _require_list_field(file_path, key)
    if spec is None:
        return 1
    key_field = spec.get("key")
    try:
        item = _build_item(spec, pairs)
    except ValueError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 1
    fm, body, _ = _load_fm_body(file_path)
    cur = fm.get(key)
    if not isinstance(cur, list):
        cur = [] if cur is None else [cur]
    found = False
    for idx, existing in enumerate(cur):
        if isinstance(existing, dict) and str(existing.get(key_field)) == str(pk):
            merged = dict(existing)
            merged.update(item)
            cur[idx] = merged
            found = True
            break
    if not found:
        item.setdefault(key_field, pk)
        cur.append(item)
    fm[key] = cur
    try:
        _write(file_path, fm, body)
    except Exception as e:
        sys.stderr.write(f"ERROR: 写入失败（{e}），未落盘\n")
        return 1
    print(f"OK: {key} upsert {key_field}={pk}")
    return 0


def _cmd_remove(file_path, key, pk):
    """按主键移除列表字段中一个元素（TAG0050 批 B，设计 §3.4）。"""
    spec = _require_list_field(file_path, key)
    if spec is None:
        return 1
    key_field = spec.get("key")
    fm, body, _ = _load_fm_body(file_path)
    cur = fm.get(key)
    if not isinstance(cur, list):
        sys.stderr.write(f"ERROR: {key} 当前不是列表（实际 {type(cur).__name__}）\n")
        return 1
    fm[key] = [
        it for it in cur
        if not (isinstance(it, dict) and str(it.get(key_field)) == str(pk))
    ]
    try:
        _write(file_path, fm, body)
    except Exception as e:
        sys.stderr.write(f"ERROR: 写入失败（{e}），未落盘\n")
        return 1
    print(f"OK: {key} 移除 {key_field}={pk}")
    return 0


def _find_field_in_contract(file_path, key):
    """在**同一快照**的 files 节中跨文件查找 key → (登记文件名, spec) 或 (None, None)。

    供 `explain` 修正「对非本文件契约字段（如对非 P6 文件 explain pass）时的来源误报」——
    此前会误报为 phases.yaml task_fields / 通用 Header（cso F-2 附项）。
    """
    file_path_dir = os.path.dirname(os.path.abspath(file_path))
    try:
        level = agate_common.task_level(file_path_dir, __file__) or agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
    except Exception:
        contract = {}
    files = contract.get("files") if isinstance(contract, dict) else None
    if not isinstance(files, dict):
        return None, None
    for name, spec in files.items():
        fields = spec.get("fields") if isinstance(spec, dict) else None
        if isinstance(fields, dict) and key in fields:
            return name, fields.get(key)
    return None, None


def _cmd_explain(file_path, key):
    """解释一个字段：来源 / 类型 / 主键 / 渲染 / 可照抄的修复命令（TAG0050 批 B，BDD-49）。"""
    basename = os.path.basename(file_path)
    spec = _field_spec(file_path, key)
    print(f"字段: {key}（{basename}）")
    if spec is None:
        # 跨文件查找：key 可能登记在快照别的文件契约里（如对非 P6 文件 explain pass）。
        owner, spec = _find_field_in_contract(file_path, key)
        if spec is not None:
            print(f"来源: 快照 files.{owner}.fields（{basename} 非其登记文件）")
    if spec is None:
        writable = _writable_keys(agate_common.resolve_rules_root(__file__))
        if key in writable:
            print("来源: phases.yaml task_fields / 通用 Header（frontmatter 标量字段）")
        else:
            print("来源: 未在契约字段或可写字段中找到")
    else:
        if spec.get("writer"):
            print(f"写入方: {spec['writer']}")
        if spec.get("key"):
            print(f"主键: {spec['key']}")
        if spec.get("render"):
            print(f"渲染: {spec['render']}")
        if spec.get("derive"):
            print(f"现算 derive: {spec['derive']}")
    print(f"修复/写入命令: FILE=<path> agate-md-field-set.py set {key} <值>")
    print("渲染修复命令:  FILE=<path> agate-md-field-set.py render")
    return 0


def _cmd_render(file_path):
    """按契约 render 规格重写文件中的 AGATE:RENDER 块（TAG0050 批 B，BDD-48）。"""
    fm, body, _ = _load_fm_body(file_path)
    rendered = _render_fields(file_path, fm)
    if not rendered:
        print("OK: 无带 render 规格的字段，未改动")
        return 0
    new_text = _rewrite_render_blocks(_compose(fm, body), rendered)
    try:
        _atomic_write(file_path, new_text)
    except Exception as e:
        sys.stderr.write(f"ERROR: 写入失败（{e}），未落盘\n")
        return 1
    print(f"OK: 已渲染 {', '.join(sorted(rendered))} 块（{RENDER_MARKER}）")
    return 0


def main():
    file_path = os.environ.get("FILE")
    args = sys.argv[1:]

    if not args:
        sys.stderr.write(
            "用法: agate-md-field-set.py set <key> <value> | append <key> k=v… | "
            "upsert <key> <主键值> k=v… | remove <key> <主键值> | --list | explain <key> | render\n"
        )
        return 2

    if not file_path:
        sys.stderr.write("agate-md-field-set: 需要 FILE 环境变量\n")
        return 1

    if not os.path.isfile(file_path):
        sys.stderr.write(
            f"ERROR: 文件不存在（{file_path}），请先 Write 产出文件，再 set 字段\n"
        )
        return 1

    op = args[0]
    if op == "--list":
        return _cmd_list(file_path)
    if op == "render":
        return _cmd_render(file_path)
    if op == "explain":
        if len(args) != 2:
            sys.stderr.write("用法: agate-md-field-set.py explain <key>\n")
            return 2
        return _cmd_explain(file_path, args[1])
    if op == "set":
        if len(args) != 3:
            sys.stderr.write("用法: agate-md-field-set.py set <key> <value>\n")
            return 2
        return _cmd_set(file_path, args[1], args[2])
    if op == "append":
        if len(args) < 3:
            sys.stderr.write("用法: agate-md-field-set.py append <key> k=v…\n")
            return 2
        return _cmd_append(file_path, args[1], args[2:])
    if op == "upsert":
        if len(args) < 4:
            sys.stderr.write("用法: agate-md-field-set.py upsert <key> <主键值> k=v…\n")
            return 2
        return _cmd_upsert(file_path, args[1], args[2], args[3:])
    if op == "remove":
        if len(args) != 3:
            sys.stderr.write("用法: agate-md-field-set.py remove <key> <主键值>\n")
            return 2
        return _cmd_remove(file_path, args[1], args[2])

    # 兼容旧写法：<key> <value> 等同于 set
    if len(args) != 2:
        sys.stderr.write(
            "用法: agate-md-field-set.py set <key> <value> | append/upsert/remove | "
            "--list | explain | render（或旧写法 <key> <value>）\n"
        )
        return 2
    return _cmd_set(file_path, args[0], args[1])


if __name__ == "__main__":
    sys.exit(main())
