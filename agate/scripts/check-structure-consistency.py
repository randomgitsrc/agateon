#!/usr/bin/env python3
"""check-structure-consistency.py — S-1~S-6 结构一致性双向 gate（TAG0021 M0）

被测契约（P2-design §3.3 / P3 BDD-2/3/5）：AGATE_ROOT 协议根下 6 条机器可判定检查（独立
S 编号空间，与 check-protocol-consistency 的 CHECK 1-12 不重复）：

  S-1 YAML→md   phases.yaml 每个 phase（id/name/exec_role + 声明的 next/retreat）在
                WORKFLOW.md 阶段总览表有对应行且一致（表行解析：`| P{N} | 名称 | 执行角色 |
                next | retreat | …`；执行角色列含修饰文本 → 取（前导 token：`（`/`(`/`/` 前
                片段；P0 主 Agent 特判 main-agent ↔ "主 Agent" 别名）。next/retreat 比对 =
                表第 4/5 列（TAG0027 B3b 加列，YAML `null` ↔ 表 `—`/空 归一；YAML 侧未声明
                转移键的阶段跳过——schema 仅 required id/name/exec_role）；P6.5 无
                next/retreat（gate_subphase 表达）→ 形态级检查：md 侧 4/5 列不出现指向独立
                后继 phase 的 plain 值（如裸 `P7`）
  S-2 md→YAML   WORKFLOW 表每行 phase id 在 phases.yaml 有定义（只匹配 `P` 数字/P6.5
                前缀行；READY 行与表外行显式排除——P2-review 发现 #1 固化）
  S-3 YAML→cards 抽检 phase-cards/P2-design.md：phases.yaml P2 声明的 outputs file 在
                卡片文本中出现（整卡级，真实卡产出规格节外亦有引用）+ exec_role 出现在
                派发节（## 派发 至下一个 ## 标题）
  S-4 YAML→scripts ①dispatch.yaml field_readers 登记字段 ⊆ 已知任务字段词表（内置基线 ∪
                phases.yaml task_fields 声明）；②gate_commands_syntax 声明与
                agate_common.is_gate_meta_key 判据一致（special_keys 须含 project_module
                特判——P2-review 发现 #3；meta_suffixes 逐项对 is_gate_meta_key 抽样验证；
                pattern 须可编译）
  S-5 schema    串联 check-yaml-schema.py（独立进程，sys.executable 调用同目录脚本，
                AGATE_ROOT 透传），任一 rules/*.yaml 违反 schema → S-5 ERROR
  S-6 引用完整性 YAML 中 file:/path: 引用路径（dispatch.templates[].file、
                roles.execution_roles/review_roles[].file、roles.scripts[].path）
                在协议根下真实存在（与 CHECK 2/CHECK 10 引文风格一致）
  S-0 编号自校验 本脚本使用的 S 编号 ⊆ 保留空间 {S1..S6}（无 S7+ 蔓延）且
                check-protocol-consistency.py 不以 `S<n>[-:]` 行首 rep 编号（编号空间隔离）

失败语义：任一 S 检查 ERROR → exit 1；全部 OK → exit 0。输出仿 rep（`S1-phases: OK` /
`S1-phases: ERROR <msg>`），供 check-gate/CI 机器消费。--strict-errors-only 语义常开
（无 WARNING 档，ERROR 即阻断；M0-M1 手动跑，M2 起进 pre-commit+CI，P2-design §3.3）。

平台无关（BDD-16）：无裸解释器、无硬编码 PATH、无 /tmp、无软链假设；文本 I/O 显式 utf-8。
Python 3.8+（无 match / str.removeprefix）。
"""

import os
import re
import subprocess
import sys

try:
    import yaml

    from agate_common import is_gate_meta_key, resolve_agate_root
except ImportError:
    sys.stderr.write("check-structure-consistency.py: 需要 pyyaml 与 agate_common（agate 脚本公共库）。pip install pyyaml 或确认在 agate/scripts/ 下运行\n")
    sys.exit(1)

# ---- 常量：S 编号保留空间 / 内置字段词表 / 主 Agent 别名 ----

_S_IDS = ("S1", "S2", "S3", "S4", "S5", "S6")

# 已知任务 frontmatter 机器字段（agate-frontmatter-check.py SCHEMAS migrated_keys +
# P2/P4 卡片机器字段 + 通用字段；phases.yaml 的 task_fields 声明为其扩展面）
_TASK_FRONTMATTER_FIELDS = frozenset({
    "agent", "phase", "task_id", "type", "parent", "trace_id", "status", "created",
    "risk_level", "phases", "packages", "domains", "ui_affected", "candidate_count",
    "gate_commands", "files_to_read", "env_constraints", "minimal_validation",
    "test_code_dir", "implementation_dir", "bump_type", "override",
    "implicit_coupling", "coupling_checklist", "internal_only", "internal_only_reason",
    "design_trivial", "follows_existing_pattern", "need_confirm_resolved",
    "suggest_resolved", "scope_resolved", "change_type", "ui_render_shape",
    "ui_ux_dimensions", "ceremony", "ui_design_section", "project_phase",
    "dispatch_plan", "pass", "fail", "regression_pass", "p5_evidence_reuse",
    "blocker_count", "deviation_count", "deviation_critical_count",
    "design_gap_count", "design_gap_reviewed_count",
    "code_map_new_files_count", "code_map_reviewed_count",
})

# P0 执行角色 = 主 Agent 亲自写（WORKFLOW 表列 "**主 Agent 亲自写**（非 subagent）"）
_MAIN_AGENT_ALIASES = ("主 Agent", "main agent", "main-agent")

_TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
_PHASE_ID_RE = re.compile(r"P\d+(?:\.5)?\Z")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CHECK_YAML_SCHEMA = os.path.join(_SCRIPT_DIR, "check-yaml-schema.py")


# ---- 通用小工具 ----

def _read_utf8(path):
    """读文本文件（utf-8）；缺失/IOError → None。"""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _load_yaml(path):
    """yaml.safe_load；失败返回 None（调用方按数据缺失处理）。"""
    text = _read_utf8(path)
    if text is None:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _resolve_root():
    """AGATE_ROOT 解析：env 优先（返回原值）→ agate_common 四层链。"""
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root
    try:
        return resolve_agate_root(__file__)
    except Exception:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- S-1 / S-2：WORKFLOW 总览表解析与双向比较 ----

def _parse_workflow_rows(workflow_text):
    """解析阶段总览表行 → [(id, name, role_cell, next_cell, retreat_cell)]（仅 P 数字/P6.5
    前缀行，READY 排除）。next_cell/retreat_cell 取行 split 后第 4/5 列（TAG0027 B3b 加列），
    行不足 6 内容列（旧 3/5 列表无 next/retreat 列）→ None。"""
    rows = []
    if not workflow_text:
        return rows
    for line in workflow_text.splitlines():
        if not line.startswith("|"):
            continue
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        pid = m.group(1).strip()
        if not _PHASE_ID_RE.match(pid):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # 新表形态 = 7 内容列（阶段/名称/执行角色/next/retreat/评审角色/门槛）；不足 6 列
        # 说明是旧 3/5 列表（无 next/retreat 列）→ 4/5 列取 None
        if len(cells) >= 6:
            next_cell = cells[3] or None
            retreat_cell = cells[4] or None
        else:
            next_cell = None
            retreat_cell = None
        rows.append((pid, m.group(2).strip(), m.group(3).strip(), next_cell, retreat_cell))
    return rows


def _normalize_role_cell(cell):
    """执行角色列归一化：去 ** 修饰 → 取 （/(/ 前片段。"""
    tok = cell.strip().lstrip("*").strip().rstrip("*").strip()
    for sep in ("（", "(", "/"):
        if sep in tok:
            tok = tok.split(sep, 1)[0].strip()
            break
    return tok


def _role_matches(yaml_role, cell):
    """YAML exec_role 与表角色列一致：归一化 token 相等；main-agent 特判别名。"""
    if _normalize_role_cell(cell) == yaml_role:
        return True
    if yaml_role == "main-agent":
        return any(alias in cell for alias in _MAIN_AGENT_ALIASES)
    return False


def _norm_transfer_cell(cell):
    """表 next/retreat 单元格归一化：空/`—`/`-`/`–`/`—（…）` 等"无值"形态 → None
    （YAML null 归一），其余（plain phase id 如 P5）去首尾空白原样返回。"""
    if not cell:
        return None
    s = cell.strip()
    if s in ("", "-", "–", "--") or s.startswith("—"):
        return None
    return s


def _check_s1(phases_by_id, workflow_text):
    """S-1 YAML→md：phases.yaml 每个 phase 在总览表有对应行且 id/name/exec_role 一致；
    TAG0027 B3b：声明了 next/retreat 的 phase 追加比对表 4/5 列（YAML null ↔ 表 —/空 归一）；
    P6.5（无 next/retreat，gate_subphase 表达）→ 形态级检查 4/5 列无 plain 独立后继值。"""
    errs = []
    rows = _parse_workflow_rows(workflow_text)
    rows_by_id = {pid: (name, role, nxt, retr) for pid, name, role, nxt, retr in rows}
    for pid, phase in phases_by_id.items():
        if pid not in rows_by_id:
            errs.append(f"phase {pid} 在 WORKFLOW 阶段总览表无对应行（S-1 YAML→md）")
            continue
        table_name, table_role, table_next, table_retreat = rows_by_id[pid]
        yaml_name = str(phase.get("name", ""))
        if yaml_name != table_name:
            errs.append(f"phase {pid} name 不一致：phases.yaml={yaml_name!r} vs WORKFLOW 表={table_name!r}")
        yaml_role = str(phase.get("exec_role", ""))
        if not _role_matches(yaml_role, table_role):
            errs.append(
                f"phase {pid} exec_role 不一致：phases.yaml={yaml_role!r} vs WORKFLOW 表列={table_role!r}"
            )

        yaml_next = phase.get("next", "MISSING")
        yaml_retreat = phase.get("retreat", "MISSING")
        yaml_has_gate_subphase = bool(phase.get("gate_subphase"))
        if yaml_has_gate_subphase:
            # P6.5 gate_subphase 形态检查（§3.2）：md 侧 4/5 列不得出现指向独立后继 phase 的
            # plain 值（如裸 P7）——P6.5 非独立转移边，注释是人类可读，机器判据以 YAML
            # gate_subphase 为准，仅做负面形态校验（不逐字比对注释文本）。
            for col_name, cell in (("next", table_next), ("retreat", table_retreat)):
                if cell is not None and _PHASE_ID_RE.match(cell.strip()):
                    errs.append(
                        f"phase {pid} 表 {col_name} 列出现指向独立后继 phase 的 plain 值 {cell!r}"
                        f"（P6.5 走 gate_subphase，非独立转移边，应写 —（gate_subphase 语义注释））（S-1 YAML→md）"
                    )
            continue
        # 主线 phase：YAML 声明了 next/retreat 才比对（schema 仅 required id/name/exec_role）
        for field_name, yaml_val, cell in (
            ("next", yaml_next, table_next),
            ("retreat", yaml_retreat, table_retreat),
        ):
            if yaml_val == "MISSING":
                continue
            norm_cell = _norm_transfer_cell(cell)
            if yaml_val is None:
                if norm_cell is not None:
                    errs.append(
                        f"phase {pid} {field_name} 不一致：phases.yaml={None!r}（无自动后继）"
                        f" vs WORKFLOW 表列={cell!r}（S-1 YAML→md）"
                    )
            else:
                if norm_cell != str(yaml_val):
                    errs.append(
                        f"phase {pid} {field_name} 不一致：phases.yaml={yaml_val!r} vs WORKFLOW 表列={cell!r}（S-1 YAML→md）"
                    )
    return errs


def _check_s2(phases_by_id, workflow_text):
    """S-2 md→YAML：总览表每行 P 前缀 phase id 在 phases.yaml 有定义（READY/表外行排除）。"""
    errs = []
    for pid, _name, _role, _nxt, _retr in _parse_workflow_rows(workflow_text):
        if pid not in phases_by_id:
            errs.append(f"WORKFLOW 总览表阶段 {pid} 未在 phases.yaml 定义（S-2 md→YAML）")
    return errs


# ---- S-3：卡片渲染一致（产出/派发 vs phases.yaml 声明） ----

_CARD_PREFIX_RE = re.compile(r"^(P\d+(?:\.5)?)-")


def _check_s3(phases_by_id, root):
    """S-3 YAML→cards：产出/派发 vs phases.yaml 声明逐卡片比对。

    M0-M1 抽检 phase-cards/P2-design.md（P2 试点，整卡级文本包含 + exec_role 派发节）；
    M3 渲染化后（BDD-12）扩展两点：
      ① 孤儿卡片防护：phase-cards/ 下存在 P 前缀卡片但 phases.yaml 无该阶段定义 →
         ERROR（人为篡改 YAML 删阶段 / 增卡片均被 S-3 双向捕获）；
      ② 有卡片的阶段输出文件整卡级包含（产出文件清单为可判定字段，逐字段对账）。
    无卡片阶段跳过（叙事先行阶段不强制渲染产物；P6.5 无独立卡片）。
    """
    errs = []
    card_dir = os.path.join(root, "phase-cards")

    # ① 孤儿卡片：存在的卡片必须能在 phases.yaml 找到阶段定义
    if os.path.isdir(card_dir):
        for fname in sorted(os.listdir(card_dir)):
            if not fname.endswith(".md"):
                continue
            m = _CARD_PREFIX_RE.match(fname)
            if m and m.group(1) not in phases_by_id:
                errs.append(
                    f"阶段卡片 {fname} 无对应 phases.yaml 定义（S-3 YAML→cards 渲染一致，人为删阶段/增卡片均检出）"
                )

    # ② 逐阶段产出/派发对账（有卡片的阶段）
    for pid, phase in phases_by_id.items():
        card_path = _phase_card_path(card_dir, pid)
        if not card_path:
            if pid == "P2":
                # M0 抽检试点锚点强制：P2 属必查对象，卡片缺失报错（防锚点消失）
                errs.append("phase-cards/P2-design.md 缺失（S-3 抽检锚点）")
            continue
        card_text = _read_utf8(card_path)
        if card_text is None:
            continue
        for out in phase.get("outputs", []) or []:
            if isinstance(out, dict) and out.get("file"):
                fname = str(out["file"])
                if fname not in card_text:
                    errs.append(
                        f"phase {pid} 产出 {fname} 未出现在 {os.path.basename(card_path)}（S-3 YAML→cards 渲染一致）"
                    )
        exec_role = str(phase.get("exec_role", ""))
        dispatch_block = _section_block(card_text, "## 派发")
        if dispatch_block is not None and exec_role and exec_role not in dispatch_block:
            errs.append(
                f"phase {pid} exec_role {exec_role} 未出现在卡片派发节（S-3 YAML→cards 渲染一致）"
            )

        # S-3a（TAG0022，YAML→md 双向 gate 命令一致性）：gates[].check 中的机器可判定
        # 命令串须在卡片 ## gate 规则（或推进条件）节出现；缺失 → ERROR（单侧漂移：
        # YAML 侧加了命令串、卡片没写）。
        yaml_cmd_refs = _yaml_gate_cmd_refs(phase)
        if yaml_cmd_refs:
            sec = _gate_rules_block(card_text, fallback_to_conditions=True)
            sec_refs = _machine_gate_refs(sec) if sec else set()
            missing = sorted(yaml_cmd_refs - sec_refs)
            if missing:
                errs.append(
                    f"phase {pid} gates[].check 命令串 {missing} 未在 {os.path.basename(card_path)} ## gate 规则（或推进条件）节出现（S-3a YAML→md 双向 gate 命令一致性）"
                )

        # S-3b（TAG0022，md→YAML 双向 gate 命令一致性）：卡片 ## gate 规则 节中的
        # 机器可判定命令行须在该阶段 gates[].check 有声明；未声明 → ERROR（单侧漂移：
        # 卡片写了命令行、phases.yaml 没声明）。
        card_sec = _gate_rules_block(card_text, fallback_to_conditions=False)
        if card_sec:
            card_refs = _machine_gate_refs(card_sec)
            declared_refs = _yaml_gate_cmd_refs(phase)
            undeclared = sorted(card_refs - declared_refs)
            if undeclared:
                errs.append(
                    f"卡片 {os.path.basename(card_path)} ## gate 规则 节命令行 {undeclared} 未在 phases.yaml {pid} gates[].check 声明（S-3b md→YAML 双向 gate 命令一致性）"
                )

    # P2 试点锚点强制（M0 语义）：phases.yaml 必须定义 P2（S-3 抽检对象）
    if "P2" not in phases_by_id:
        errs.append("phases.yaml 无 P2 定义（S-3 抽检对象缺失）")
    return errs


def _phase_card_path(card_dir, pid):
    """找阶段卡片文件：phase-cards/{pid}-*.md；缺失 → None。"""
    if not os.path.isdir(card_dir):
        return None
    prefix = pid + "-"
    for fname in sorted(os.listdir(card_dir)):
        if fname.startswith(prefix) and fname.endswith(".md"):
            return os.path.join(card_dir, fname)
    return None


def _section_block(text, heading):
    """取 md 某个 `## 标题` 节到下一个 `## `/`# ` 标题之间的文本；标题缺失 → None。"""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i
            break
    if start is None:
        return None
    block = []
    for line in lines[start + 1:]:
        if re.match(r"^#\s+\S", line):
            break
        block.append(line)
    return "\n".join(block)


# ---- S-3a/S-3b：双向 gate 命令一致性（TAG0022 RM-AG0038，P2 §4.2.2 S-3a/S-3b；TG-1） ----
# S-3a（YAML→md）：phases.yaml gates[].check 中的机器可判定命令串须在对应卡片
#   `## gate 规则`（或推进条件）节出现——YAML 侧加了、md 侧没加 → ERROR。
# S-3b（md→YAML）：卡片 `## gate 规则` 节中的机器可判定命令行须在该阶段
#   gates[].check 有声明——md 侧加了、YAML 侧没加 → ERROR。
# 机器可判定命令行模式（P2 §4.2.2）：check-gate.py P{n} / gate_commands.P{n} /
#   check-*.py。NB-1：S-3a/S-3b 是叠加在既有 S-3 outputs/orphan/exec_role 检查下的
#   新增子检查，不是重定义。NB-2：无卡片阶段（P6.5 无独立卡片）沿用既有跳过。

_MACHINE_GATE_REF_RE = re.compile(
    r"check-gate\.py P[0-9]+(?:\.[0-9]+)?"
    r"|gate_commands\.P[0-9]+(?:\.[0-9]+)?"
    r"|check-[A-Za-z0-9_-]+\.py"
)


def _machine_gate_refs(text):
    """提取文本中的机器可判定 gate 命令引用（去重 set）。"""
    if not text:
        return set()
    return {m.group(0) for m in _MACHINE_GATE_REF_RE.finditer(text)}


def _yaml_gate_cmd_refs(phase):
    """某阶段 phases.yaml gates[].check 声明中的机器可判定命令引用集。"""
    refs = set()
    for g in phase.get("gates", []) or []:
        if isinstance(g, dict) and g.get("check"):
            refs |= _machine_gate_refs(str(g["check"]))
    return refs


def _block_since(lines, i):
    """自第 i 行起取到下一个 `## ` 标题的行块（卡内 `# 注释` 行不算节边界）。"""
    out = []
    for ln in lines[i + 1:]:
        if ln.startswith("## "):
            break
        out.append(ln)
    return "\n".join(out)


def _gate_rules_block(text, fallback_to_conditions=False):
    """取卡片 `## gate 规则` 节文本；fallback_to_conditions=True 时缺 gate 规则节
    回退 `## 推进条件` 节；两节均无 → None（NB-2：无卡片阶段由调用方跳过）。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## gate 规则"):
            return _block_since(lines, i)
        if fallback_to_conditions and line.startswith("## 推进条件"):
            return _block_since(lines, i)
    return None


# ---- S-4：YAML→scripts（字段登记 + gate_commands 语法声明） ----

def _check_s4(dispatch, phases_by_id):
    """S-4 YAML→scripts：字段读取登记表 vs 字段集一致；语法声明 vs is_gate_meta_key 一致。"""
    errs = []
    declared_fields = set()
    for phase in phases_by_id.values():
        for f in phase.get("task_fields", []) or []:
            declared_fields.add(str(f))
    allowed_fields = _TASK_FRONTMATTER_FIELDS | declared_fields

    if dispatch is not None:
        for reader in dispatch.get("field_readers", []) or []:
            if not isinstance(reader, dict):
                continue
            script = reader.get("script", "")
            phase = reader.get("phase", "")
            if phase and phase not in phases_by_id:
                errs.append(
                f"field_readers[{script}] 引用未定义阶段 {phase}（S-4 YAML→scripts）"
            )
            for f in reader.get("fields", []) or []:
                if str(f) not in allowed_fields:
                    errs.append(
                        f"field_readers[{script}] 登记字段 {f!r} 不在已知任务字段表（内置基线 ∪ phases.yaml task_fields）（S-4 YAML→scripts）"
                    )

        syntax = dispatch.get("gate_commands_syntax")
        if isinstance(syntax, dict):
            special = set(syntax.get("special_keys", []) or [])
            if "project_module" not in special:
                errs.append("gate_commands_syntax.special_keys 缺 project_module 特判（合法 key = is_gate_meta_key OR project_module，S-4 YAML→scripts）")
            for suffix in syntax.get("meta_suffixes", []) or []:
                if not is_gate_meta_key("P5" + str(suffix)):
                    errs.append(
                    f"gate_commands_syntax.meta_suffixes 声明 {suffix!r} 与 is_gate_meta_key 判据不一致（S-4 YAML→scripts）"
                )
            pattern = syntax.get("pattern")
            if pattern:
                try:
                    re.compile(str(pattern))
                except re.error as exc:
                    errs.append(
                    f"gate_commands_syntax.pattern {pattern!r} 非合法正则（S-4 YAML→scripts）：{exc}"
                )
    else:
        errs.append("rules/dispatch.yaml 缺失或解析失败（S-4 判定不可用）")
    return errs


# ---- S-5：串联 schema 校验（独立进程） ----

def _check_s5(root):
    """S-5 schema：独立进程调用 check-yaml-schema.py（AGATE_ROOT 透传），非 0 → ERROR。"""
    if not os.path.isfile(_CHECK_YAML_SCHEMA):
        return ["scripts/check-yaml-schema.py 缺失（S-5 依赖）"]
    env = dict(os.environ)
    env["AGATE_ROOT"] = str(root)
    try:
        proc = subprocess.run(
            [sys.executable, _CHECK_YAML_SCHEMA],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=120,
        )
    except Exception as exc:
        return [f"check-yaml-schema.py 运行失败（S-5 schema）：{exc}"]
    if proc.returncode != 0:
        detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return [
            f"rules/*.yaml 未过 schema（S-5 schema，check-yaml-schema.py exit {proc.returncode}）：{detail[:300]}"
        ]
    return []


# ---- S-6：引用完整性 ----

def _collect_references(dispatch, roles):
    """收集 YAML 中协议根相对引用（file:/path:）→ [(位置说明, 引用路径)]。"""
    refs = []
    if dispatch is not None:
        for entry in dispatch.get("templates", []) or []:
            if isinstance(entry, dict) and entry.get("file"):
                refs.append(("dispatch.templates[].file", str(entry["file"])))
    if roles is not None:
        for key in ("execution_roles", "review_roles"):
            for entry in roles.get(key, []) or []:
                if isinstance(entry, dict) and entry.get("file"):
                    refs.append((f"roles.{key}[].file", str(entry["file"])))
        for entry in roles.get("scripts", []) or []:
            if isinstance(entry, dict) and entry.get("path"):
                refs.append(("roles.scripts[].path", str(entry["path"])))
    return refs


def _check_s6(dispatch, roles, root):
    """S-6 引用完整性：file:/path: 引用路径在协议根下真实存在。"""
    errs = []
    for loc, ref in _collect_references(dispatch, roles):
        if not os.path.isfile(os.path.join(root, ref)):
            errs.append(f"{loc} 引用 {ref} 在协议根下不存在（S-6 引用完整性）")
    return errs


# ---- S-0：编号自校验（S 编号空间隔离） ----

def _check_s_numbering(root):
    """S-0 编号自校验：本脚本 S 编号 ⊆ {S1..S6}；与 CHECK 1-12 编号空间不冲突。"""
    errs = []
    own_text = _read_utf8(__file__) or ""
    used = set(re.findall(r"\b(S[0-9]+)-", own_text))
    overflow = (used - set(_S_IDS)) - {"S0"}
    if overflow:
        errs.append(
            f"本脚本使用 S 编号 {sorted(overflow)} 超出保留空间 {_S_IDS}（S-0 编号自校验）"
        )
    consistency = os.path.join(root, "scripts", "check-protocol-consistency.py")
    cons_text = _read_utf8(consistency)
    if cons_text is not None:
        for m in re.finditer(r"^S([0-9]+)[-:]", cons_text, re.M):
            errs.append(
                f"check-protocol-consistency.py 使用 S 编号 S{m.group(1)}（与 S-1~S-6 空间冲突，S-0 编号自校验）"
            )
    return errs


# ---- 主流程 ----

def main():
    root = _resolve_root()
    if not root:
        sys.stderr.write("FATAL: 无法解析 AGATE_ROOT（env / .agate-version / current / 脚本上溯均不可用）\n")
        sys.exit(1)
    rules_dir = os.path.join(root, "rules")
    if not os.path.isdir(rules_dir):
        sys.stderr.write(f"FATAL: AGATE_ROOT={root} 下缺少 rules/ 目录\n")
        sys.exit(1)

    phases_path = os.path.join(rules_dir, "phases.yaml")
    dispatch_path = os.path.join(rules_dir, "dispatch.yaml")
    roles_path = os.path.join(rules_dir, "roles.yaml")

    phases_data = _load_yaml(phases_path)
    dispatch = _load_yaml(dispatch_path)
    roles = _load_yaml(roles_path)

    phases_by_id = {}
    phases_load_error = None
    if not isinstance(phases_data, dict) or not isinstance(phases_data.get("phases"), list):
        phases_load_error = "rules/phases.yaml 缺失或解析失败（phases 列表不可用）"
    else:
        for phase in phases_data["phases"]:
            if isinstance(phase, dict) and phase.get("id"):
                phases_by_id[str(phase["id"])] = phase

    workflow_text = _read_utf8(os.path.join(root, "WORKFLOW.md"))

    results = []
    if phases_load_error:
        results.append(("S1", "phases", [phases_load_error]))
        results.append(("S2", "workflow", [phases_load_error]))
        results.append(("S3", "cards", [phases_load_error]))
    else:
        results.append(("S1", "phases", _check_s1(phases_by_id, workflow_text)))
        results.append(("S2", "workflow", _check_s2(phases_by_id, workflow_text)))
        results.append(("S3", "cards", _check_s3(phases_by_id, root)))

    results.append(("S4", "scripts", _check_s4(dispatch, phases_by_id)))
    results.append(("S5", "schema", _check_s5(root)))
    results.append(("S6", "references", _check_s6(dispatch, roles, root)))
    results.append(("S0", "numbers", _check_s_numbering(root)))

    any_error = False
    for sid, name, errs in results:
        if errs:
            any_error = True
            for msg in errs:
                sys.stdout.write(f"{sid}-{name}: ERROR {msg}\n")
        else:
            sys.stdout.write(f"{sid}-{name}: OK\n")
    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    main()
