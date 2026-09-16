#!/usr/bin/env python3
"""check-gate.py — 阶段 gate 总闸（TAG0010 批次 2f-1 框架 + P0-P4，2f-2 补 P5-P8）

从 check-gate.sh 迁移。CLI 契约与 sh 版等价：
  check-gate.py PHASE TASK_DIR [OLD_PHASE]
exit 0 = gate 通过; exit 1 = gate 未通过; exit 2 = 多数 phase 正常通过码（含动态
gate_commands 或语义判断后的"通过"出口）——pass 判定以 phases.yaml gate_pass_exit 为准：
P0-P3/P5/P6/P8 的通过码是 exit 2（gate_p0 L577 / p1 L698 / p2 L883 / p3 L892 / p5 L1048 /
p6 L1093 / p8 L1376 return 2），P4/P7/P6.5 的通过码是 exit 0（p4 L990 / p7 L1241 /
p65 L1110/1120 return 0）。exit 2 是账本常态（pre-commit 每次成功 commit 记 exit:2），
不是暂停——agate-next.py 消费方按 gate_pass_exit pass_set 区分"正常通过"与"真暂停"
（TAG0027 BDD-13/26，CRITICAL-1 修正；本脚本返回语义零改动）。

OLD_PHASE（可选第 3 参数）：上一个 phase。省略时行为与之前完全一致（无回退检测）。
提供且数字上大于 PHASE 时，判定为"回退抵达"，跳过该阶段的完成度校验直接 exit 2
（回退抵达 ≠ 阶段已完成，不该被当"未完成"硬拦截；也不应假装"已通过"）。

P0-P8 全部分支均已实现（2f-2 补齐 P5-P8），与 sh 版 check-gate.sh 逐分支等价：
  P5: gate_commands.P5 动态读取提示 + 多命令 WARNING + pre-task-baseline 机械 diff
  P6: P6-acceptance.md pass/fail 汇总 + P6-evidence/ 非空（provenance 审计由
      pre-commit-gate.sh / ci-gate-backstop.py 单独调用 check-p6-provenance，不在本
      分支内执行——与 sh 版一致，sh check-gate.sh P6 同样不调）
  P7: BLOCKER/DEVIATION-CRITICAL + DESIGN_GAP 配对 + P4/P7 转抄交叉核对
  P8: P8-release.md bump_type/debt_check + version/CHANGELOG/tag 检查

本脚本的判定逻辑与 state-machine.md 步骤 5 保持同步。
步骤 5 变更时必须同步更新本脚本。一致性检查脚本覆盖本文件。
"""

import json
import os
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:
    yaml = None

try:
    from agate_common import read_vision_tri_state, resolve_workspace, run_git
except ImportError:
    read_vision_tri_state = None
    run_git = None
    resolve_workspace = None

# DEBT0018 fail-closed 标记：agate_common 整体不可导入时置 True，供 gate_p1/p6/p7 四个
# "关键读取器"消费点（read_rules_yaml/count_p6_pass_fail/count_p7_markers/
# count_code_map_lines）在使用返回值前判定——命中则显式失败（安装破损），不再静默用
# 0/None/空降级值走到 false-PASS。其余 20+ 个降级 stub 的既有 fail-open 语义不受影响
# （R2：不在 DEBT0018 evidence 点名范围内）。
try:
    from agate_common import (
        body_field_value,
        candidate_count_value,
        count_code_map_lines,
        count_design_gap,
        count_kf_entries,
        count_markers,
        count_p2_declared_fields,
        count_p6_pass_fail,
        count_p7_markers,
        design_trivial_declared,
        extract_bdd_titles,
        extract_embedded_yaml_blocks,
        extract_marker_desc,
        fm_field_value,
        has_keyword,
        has_marker,
        is_legal_gate_key,
        known_phase_ids,
        parse_fail_list_block,
        parse_gate_commands_block,
        parse_ui_design_section,
        read_rules_yaml,
        reconcile_enabled,
        reconcile_field,
        reconcile_summary,
        resolve_rules_root,
        split_frontmatter,
    )
except ImportError:

    # M1 对账辅助缺失 → 对账降级为关闭（对账是叠加层，不影响原判定语义）
    def reconcile_enabled():
        return False

    def reconcile_field(_op, _field, _grep_val, _structured_val):
        return True

    def reconcile_summary():
        return None

    def split_frontmatter(text):
        return (None, text)

    def body_field_value(body, field):
        return ""

    def fm_field_value(fm, field):
        return ""

    def known_phase_ids(rules_root):
        return frozenset()

    def is_legal_gate_key(key, phase_ids=None):
        return True

    def resolve_rules_root(script_path):
        return ""

    # M2 共享解析（BDD-9：已迁移解析点不在本文件字面出现，落在 agate_common 单点）；
    # agate_common 缺失时按数据缺失降级（块解析 → 无块；四字段 → 0，P2 分支 fail-closed）
    def parse_gate_commands_block(text):
        return (False, [])

    def count_p2_declared_fields(text):
        return 0

    # M2-0038 共享读取器（TAG0022 RM-AG0038，BDD-3）：agate_common 缺失 = 安装破损，
    # 读取器按数据缺失降级（计数 → 0 / 布尔 → False / 块解析 → 空），方向与
    # parse_gate_commands_block 降级先例一致；不在此内联迁移前实现（防双实现漂移）。
    # 注意：降级实现不得含已迁移解析点字面（test_md_parse_scan.py BDD-3 静态扫描）。
    def count_markers(text, kind):
        return 0

    def has_marker(line, kind):
        return False

    def extract_marker_desc(line, kind):
        return line

    def extract_bdd_titles(text):
        return ""

    def parse_ui_design_section(text):
        return (None, "", "")

    def candidate_count_value(line):
        return None

    def design_trivial_declared(line):
        return False

    def has_keyword(text, kind):
        return False

    def count_p6_pass_fail(text):
        return 0, 0

    def count_p7_markers(text):
        return 0, 0

    def count_design_gap(text, allow_blockquote=True):
        return 0, 0

    def count_code_map_lines(text):
        return 0

    def parse_fail_list_block(text):
        return []

    def read_rules_yaml(rules_root, name):
        return None

    def count_kf_entries(text):
        return 0

    def extract_embedded_yaml_blocks(text):
        return []

# RM-AG0046（TAG0026）：维护性反模式检测器 check-maintainability.py——gate_p4 三重门槛
# 数据源。ImportError 降级 = WARNING 不阻断（检测未部署 ≠ 判定缺失，R2；
# 与上方 agate_common 兜底区同型先例 :32-41）。
# 注意：文件名 check-maintainability.py 含连字符，裸 import 语句无法按模块名解析
# （模块名标识符不含连字符，子进程 sys.path[0]=scripts 目录时同样失败）——
# ImportError 时按文件路径 importlib 显式加载兜底（agate-risk-score.py _load_script
# 同源机制），仍失败才降级 None。
try:
    from check_maintainability import check_maintainability
except ImportError:
    try:
        import importlib.util

        _cm_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "check-maintainability.py"
        )
        _cm_spec = importlib.util.spec_from_file_location(
            "check_maintainability", _cm_path
        )
        _cm_mod = importlib.util.module_from_spec(_cm_spec)
        _cm_spec.loader.exec_module(_cm_mod)
        check_maintainability = _cm_mod.check_maintainability
    except Exception:
        check_maintainability = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FIELD_GET = os.path.join(SCRIPT_DIR, "agate-md-field-get.py")
GATE_MISSING_CMDS = os.path.join(SCRIPT_DIR, "agate-gate-missing-cmds.py")
P5_COUNT = os.path.join(SCRIPT_DIR, "agate-gate-p5-count.py")

# RM-AG0001（v0.30.2）：P1 行首标记正则加可选反引号前缀（`[NEED_CONFIRM] 反引号包裹标记
# 不再漏计；含 - `[..]` 反引号在 dash 之后的形态）。与 sh `grep -cE` 逐行语义一致。
# M2-0038（TAG0022，BDD-3）：B 组行首标记正则与计数/描述提取已迁 agate_common
# （count_markers / has_marker / extract_marker_desc）——本文件不再字面出现这些正则。

# P4 暂存区排除模式（与 sh grep -qvE 同一模式）：
# 阶段产出 md（P[0-8]-*.md，路径首或 / 后）+ .state.yaml。
_STAGED_EXCLUDE_RE = re.compile(r"(^|/)P[0-8]-.*\.md$|(^|/)\.state\.yaml$")


def _git(args):
    """git 子进程（优先 agate_common.run_git，缺库时本地 subprocess 兜底）。"""
    if run_git is not None:
        return run_git(args)
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout
    except OSError:
        return 1, ""


def _reader_missing(fn):
    """DEBT0018：判定"关键读取器"（read_rules_yaml/count_p6_pass_fail/count_p7_markers/
    count_code_map_lines）当前绑定是否可信——严格要求当前绑定的 `__module__` 是
    `"agate_common"`（真正从 agate_common 导入的实现）。ImportError 降级 stub（定义在
    check-gate.py 内，`__module__` 为本文件的加载态模块名，如 `"__main__"`/
    `"check_gate_direct"`）判定为不可信；任何非 agate_common 来源的替换同样判定为不可信。

    用 `__module__` 身份判定而非一次性导入标记，是因为消费点在使用返回值前才需要知道
    "这个名字现在到底绑的是谁"——对函数对象的引用可能在模块 exec 完成后被重新赋值（无论是
    生产环境的降级恢复，还是白盒测试的依赖注入），身份判定在调用时刻永远准确。
    """
    return getattr(fn, "__module__", None) != "agate_common"


def _read_text(path):
    """读文件全文；文件不存在/不可读返回 ""。"""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _lines(text):
    """逐行（splitlines 剥尾 \r，对应 sh frontmatter sed 的 s/\r$// CRLF 容错）。"""
    return text.splitlines()


def _frontmatter_lines(path):
    """sed -n 's/\r$//; /^---$/,/^---$/p' 等价：返回首个 --- 块内的行（不含 --- 定界）。

    TAG0022（RM-AG0038）A 组迁移后仅剩 gate_p1 的 need_confirm_resolved /
    suggest_resolved 存在性检查使用（frontmatter 行首键扫描）；frontmatter 字段值读取
    已全部改走 _md_field_get（agate-md-field-get 新 op status/agent/project_phase/
    code_map_*，NO_FALLBACK 语义对 well-formed frontmatter 等价）。
    """
    lines = _lines(_read_text(path))
    in_fm = False
    out = []
    for line in lines:
        if line == "---":
            if not in_fm:
                in_fm = True
            else:
                break
            continue
        if in_fm:
            out.append(line)
    return out


def _md_field_get(op, file_path):
    """调 agate-md-field-get.py op（env FILE），失败回退 ""（同 sh || echo ""）。"""
    env = dict(os.environ)
    env["FILE"] = file_path
    try:
        proc = subprocess.run(
            [sys.executable, MD_FIELD_GET, op],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def _gate_missing_cmds(gate_file):
    """调 agate-gate-missing-cmds.py（env GATE_FILE），失败回退 ""。"""
    env = dict(os.environ)
    env["GATE_FILE"] = gate_file
    try:
        proc = subprocess.run(
            [sys.executable, GATE_MISSING_CMDS],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def _gate_p5_count(gate_file):
    """调 agate-gate-p5-count.py（env GATE_FILE），返回 (main, aux)。

    失败回退 (0, 0)（同 sh `|| echo "0 0"`）。
    """
    env = dict(os.environ)
    env["GATE_FILE"] = gate_file
    try:
        proc = subprocess.run(
            [sys.executable, P5_COUNT],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return 0, 0
    if proc.returncode != 0:
        return 0, 0
    parts = (proc.stdout or "").split()
    main = int(parts[0]) if parts and parts[0].isdigit() else 0
    aux = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return main, aux


def _load_state_yaml(task_dir):
    """读 task_dir/.state.yaml 为 dict（TAG0020 gate_p65 用；仿 check-p6-provenance L209-221）。

    文件缺失 / 无 pyyaml / 解析失败 → {}（静默回退，等价 provenance 的
    no_reuse_claim_possible 静默空 dict 语义）。
    """
    state_path = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(state_path) or yaml is None:
        return {}
    try:
        with open(state_path, encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


# RM-AG0039（TAG0022，P2-review 锁定决策 2）：P1 `created` ISO 日期/时间判据。
# 合法形态 = ISO 8601 日期（YYYY-MM-DD）或带时间后缀（T/空格分隔，含可选秒/小数/时区）；
# created 缺失或非 ISO → 返回 False（调用方 fail-open 不拦，R5）。字典序比较对
# judge_required_since（日期型 "YYYY-MM-DD"）前缀等价成立（datetime 字符串按字典序 ≥ 同日日期）。
_ISO_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:[Zz]|[+-]\d{2}:?\d{2})?)?$"
)


def _is_iso_date(value):
    return isinstance(value, str) and bool(_ISO_DATE_RE.match(value))


def _run_gate_script(script_name, task_dir):
    """调 {SCRIPT_DIR}/{script_name} TASK_DIR（TAG0020 gate_p65 用）。

    子脚本 stderr 透传（诊断可见）；脚本缺失/执行失败 → 非 0（fail-closed）。
    """
    path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.isfile(path):
        sys.stderr.write(f"GATE P6.5: 缺子脚本 {script_name}\n")
        return 1
    try:
        proc = subprocess.run(
            [sys.executable, path, task_dir],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return 1
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def _to_int(value, default=0):
    """安全转 int；失败回退 default（对应 bash 算术错误按 0 处理的口径）。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_int_or_none(value):
    """严格转 int；非数字返回 None（对应 bash `[ x -lt y ]` 非整数报错→false 的口径）。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ========== TAG0006 UI/UX 机制（P2 §2.1/§2.15.4/§2.3）：P1 vision 三态 + 形态声明、P2 UI 设计节 ==========
# 分类框架维度（示例性开放集合，§2.15.2）：布局结构/渲染正确性/交互行为/动效时序/视觉呈现。
_FRAMEWORK_DIMS = frozenset({"布局结构", "渲染正确性", "交互行为", "动效时序", "视觉呈现"})
_VISION_STATUSES = frozenset({"available", "supplementable", "GAP"})
# §2.15.1 同义映射表：中文标签 → 规范形态值（杜绝 ASCII 规范值 vs 中文标签字面永不匹配的误拦）。
_SHAPE_SYNONYMS = {
    "布局型": "layout",
    "渲染组件型": "render_component",
    "时序特效型": "temporal_effects",
}
# §2.3 渲染组件型分支的启发关键词（产品域启发词，仅用于识别可能的渲染组件形态分支，
# 不构成任何技术栈绑定——形态判定以 P1 ui_render_shape 规范值 / 维度选择为准）。
_RENDER_COMP_HEURISTICS = ("渲染组件", "视觉渲染", "画布", "图表", "模型", "特效", "地图", "数字地球")


def _canonical_shape(value):
    """P1/P2 形态声明 → 规范形态值（§2.15.1 规范化值比对语义）。

    声明含规范值 ASCII 词（layout/render_component/temporal_effects）直接取用；
    仅含中文标签（布局型/渲染组件型/时序特效型）经同义映射表归一化；
    其余开放形态值原样返回（扩展形态以 P1 字段值为比对基准，P2 声明行需复用同一值）。
    """
    if not value:
        return None
    for canonical in ("layout", "render_component", "temporal_effects"):
        if re.search(r"\b" + canonical + r"\b", value):
            return canonical
    for label, canonical in _SHAPE_SYNONYMS.items():
        if label in value:
            return canonical
    stripped = value.strip("（）()【】[]{}｛｝,， \t")
    return stripped or None


def _gate_p1_vision_capability(p1_file):
    """P1 检查：domains 含 frontend → capability_requirements 必须含视觉能力三态条目（BDD-3）。

    取 frontmatter domains + 正文 YAML capability_requirements 块（need/name 含 visual|vision）：
      - 条目缺失 → exit 1（frontend 任务必须显式声明视觉能力）
      - status 不在 {available, supplementable, GAP} → exit 1
      - 合法（含 GAP——GAP 是合法声明，触发的是 P6 降级链而非 P1 拦截）→ 通过
    兼容：domains 不含 frontend → 不触发（基线 825 fixture 均无 frontend domains）。
    """
    domains = _md_field_get("domains", p1_file)
    if "frontend" not in (domains or "").split():
        return True
    status = None
    if read_vision_tri_state is not None:
        status = read_vision_tri_state(p1_file)
    if status is None and yaml is not None:
        # 兜底：read_vision_tri_state 无视觉条目时本地再解析 capability_requirements 围栏块
        # M2-0038 D 组：内嵌 yaml/yml 块提取迁 agate_common extract_embedded_yaml_blocks
        # （同正则单点，read_vision_tri_state 与兜底共用）
        text = _read_text(p1_file)
        for block in extract_embedded_yaml_blocks(text):
            try:
                data = yaml.safe_load(block)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            reqs = data.get("capability_requirements")
            if not isinstance(reqs, list):
                continue
            for item in reqs:
                if not isinstance(item, dict):
                    continue
                need = item.get("need") or item.get("name")
                if need and re.search(r"visual|vision", str(need), re.IGNORECASE):
                    status = item.get("status")
                    break
            if status is not None:
                break
    if status is None:
        sys.stderr.write(
            "GATE P1: frontend 任务必须声明 vision 能力条目（capability_requirements 含 visual/vision need）\n"
        )
        return False
    if str(status) not in _VISION_STATUSES:
        sys.stderr.write(
            f"GATE P1: frontend 任务 vision 能力条目 status 非法（当前: {status}，须 ∈ available/supplementable/GAP）\n"
        )
        return False
    return True


def _gate_p1_ui_shape(p1_file):
    """P1 检查：domains 含 frontend → ui_render_shape/ui_ux_dimensions 声明合法性（BDD-16，§2.15.4）。

    - 双字段缺失 → 通过（presence 语义，常规布局型默认，不红基线）
    - 声明了形态但维度空 → exit 1（适配层无法生效）
    - 维度 ∈ 分类框架（§2.15.2）→ 通过；维度为扩展名 → 须在 P1 UX 类别 BDD 标题出现证明其运用
    - ui_render_shape 缺失而 ui_ux_dimensions 存在 → 允许（维度选择本身合法）
    """
    text = _read_text(p1_file)
    domains = _md_field_get("domains", p1_file)
    if "frontend" not in (domains or "").split():
        return True
    shape = _md_field_get("ui_render_shape", p1_file).strip()
    dims_raw = _md_field_get("ui_ux_dimensions", p1_file)
    dims = [d.strip() for d in re.split(r"[,，\s]+", dims_raw) if d.strip()]
    if not shape and not dims:
        return True
    if shape and not dims:
        sys.stderr.write(
            "GATE P1: 已声明 ui_render_shape 但 ui_ux_dimensions 为空——形态声明必须选择适用维度（分类框架或扩展维度）\n"
        )
        return False
    bdd_titles = extract_bdd_titles(text)
    for dim in dims:
        if dim in _FRAMEWORK_DIMS:
            continue
        if dim and dim in bdd_titles:
            continue
        sys.stderr.write(
            f"GATE P1: 维度 '{dim}' 不在分类框架且未在 UX 类别 BDD 标题声明运用\n"
        )
        return False
    return True


def _gate_p2_ui_design_section(p2_file):
    """P2 检查：ui_affected: true → P2-design.md 必含 UI 设计节（BDD-4，§2.3）。

    校验：① `## UI 设计`（或 `### UI 设计`）节标题；② 渲染形态声明（`渲染形态:` / `适用维度:`）；
    ③ 按形态分支的目标维度 checklist 关键词（布局型=布局/交互/视觉；渲染组件/时序特效型=
    渲染正确性或动效时序锚点；"不适用"显式声明可豁免该维度关键词）；④ P1-P2 形态一致性
    交叉校验（§2.15.1 规范化值比对：P1 声明 ui_render_shape 时 P2 形态声明须一致）。
    兼容：ui_affected != true → 不触发（既有 fixture 中 full-task/high-risk/paused-task 均 false）。
    """
    ui_affected = _md_field_get("ui_affected", p2_file)
    if ui_affected != "true":
        return True
    p2_text = _read_text(p2_file)

    # M2-0038 C 组：UI 设计节定位 + 渲染形态/适用维度声明提取迁 agate_common
    # parse_ui_design_section（BDD-3：节标题/声明行正则不在本文件字面出现）
    ui_block, shape_line, dim_line = parse_ui_design_section(p2_text)
    if ui_block is None:
        sys.stderr.write("GATE P2: ui_affected: true 但缺 UI 设计 节标题（## UI 设计）\n")
        return False

    # ② 形态声明（渲染形态 或 适用维度）至少出现一次
    if not shape_line and "适用维度" not in ui_block:
        sys.stderr.write(
            "GATE P2: UI 设计 节缺渲染形态声明（须含 渲染形态: 或 适用维度: 声明行）\n"
        )
        return False

    # ③ 按形态分支校验 checklist 维度锚点
    # 维度不适用豁免按"维度"粒度（§2.3）：显式声明"布局不适用"只豁免布局锚点，
    # 交互/视觉 仍须各出现关键词——避免"声明任一维度不适用即一刀切豁免全部三维"过宽。
    canonical = _canonical_shape(shape_line)
    is_render_form = (
        canonical is not None and canonical != "layout"
    ) or any(h in shape_line for h in _RENDER_COMP_HEURISTICS) or bool(
        re.search(r"渲染正确性|动效时序", dim_line or "")
    )
    if is_render_form:
        render_anchor = bool(re.search(r"渲染|渲染正确性|capture", ui_block))
        temporal_anchor = bool(re.search(r"时序|动效|animation|frame", ui_block))
        if not (render_anchor or temporal_anchor):
            sys.stderr.write(
                "GATE P2: 渲染组件/时序特效型形态缺维度锚点——须出现渲染正确性（渲染|渲染正确性|capture）或动效时序（时序|动效|animation|frame）checklist\n"
            )
            return False
    else:
        layout_ok = "布局" in ui_block or bool(re.search(r"布局\s*不适用", ui_block))
        interaction_ok = "交互" in ui_block or bool(re.search(r"交互\s*不适用", ui_block))
        visual_ok = "视觉" in ui_block or bool(re.search(r"视觉\s*不适用", ui_block))
        if not (layout_ok and interaction_ok and visual_ok):
            sys.stderr.write(
                "GATE P2: 常规布局型 UI 设计节缺维度 checklist——布局/交互/视觉 关键词须各出现至少一次（或显式声明维度不适用）\n"
            )
            return False

    # ④ P1-P2 形态一致性交集校验（规范化值比对，§2.15.1）
    p1_file = os.path.join(os.path.dirname(os.path.abspath(p2_file)), "P1-requirements.md")
    p1_shape = _md_field_get("ui_render_shape", p1_file).strip() if os.path.isfile(p1_file) else ""
    if p1_shape:
        p2_canonical = _canonical_shape(shape_line) if shape_line else None
        if p2_canonical is None:
            sys.stderr.write(
                "GATE P2: P1 声明了 ui_render_shape 但 P2 UI 设计节缺形态声明行（P1-P2 形态一致性校验不通过）\n"
            )
            return False
        if p1_shape != p2_canonical:
            sys.stderr.write(
                f"GATE P2: P1-P2 渲染形态声明不一致（P1 ui_render_shape={p1_shape}, P2 形态声明={p2_canonical}）\n"
            )
            return False
    return True


def gate_p0(task_dir):
    sys.stderr.write(
        "GATE P0: 立项阶段无需脚本 gate（仅 P0-brief.md）。主 Agent 确认 P0-brief 四字段齐全即可推进 P1。\n"
    )
    return 2


def gate_p1(task_dir):
    p1_review = os.path.join(task_dir, "P1-review.md")
    if not os.path.isfile(p1_review):
        sys.stderr.write("GATE P1: P1-review.md 不存在——P1 评审不可裁，所有任务都需独立 requirements-review\n")
        return 1

    status = _md_field_get("status", p1_review)
    if status != "approved":
        sys.stderr.write("GATE P1: P1-review.md frontmatter status 非 approved（当前: {}）\n".format(
            status if status else "缺失"))
        return 1

    agent = _md_field_get("agent", p1_review)
    if not agent:
        sys.stderr.write("GATE P1: P1-review.md status:approved 但缺 agent 字段\n")
        return 1
    if agent == "main":
        sys.stderr.write("GATE P1: P1-review.md status:approved 但 agent=main（主 Agent 不可自行批准评审）\n")
        return 1

    review_text = _read_text(p1_review)
    if not re.search(r"BDD-[0-9]", review_text):
        sys.stderr.write("GATE P1: P1-review.md 不含 BDD 编号引用（裸 approved 极可能是假完成，review 结论须引用具体 BDD 编号）\n")
        return 1

    # P1 NEED_CONFIRM 检查（v0.30.2 三值分级：[NEED_CONFIRM] 阻塞 / [SUGGEST:] 不阻塞 / [NO_NEED_CONFIRM] 负向）
    # M2-0038 B 组：行首标记计数/描述提取迁 agate_common count_markers/has_marker/
    # extract_marker_desc（BDD-3：正则不在本文件字面出现）
    p1_file = os.path.join(task_dir, "P1-requirements.md")
    p1_text = _read_text(p1_file)
    p1_lines = _lines(p1_text)
    nc_blocking = count_markers(p1_text, "NC")
    nc_suggest = count_markers(p1_text, "SUGGEST")

    # v2.0 T001 流 C（BDD-21）：need_confirm_resolved 结构化匹配——
    # frontmatter 该字段存在时逐条匹配，未匹配才计入阻塞数；字段缺失（旧格式）沿用整段计数。
    nc_unresolved = nc_blocking
    if nc_blocking > 0:
        fm_lines = _frontmatter_lines(p1_file)
        resolved_present = sum(1 for line in fm_lines if line.startswith("need_confirm_resolved:"))
        if resolved_present > 0:
            resolved_fm = _md_field_get("need_confirm_resolved", p1_file)
            resolved = set(resolved_fm.split("\n"))
            nc_unresolved = 0
            for line in p1_lines:
                if not has_marker(line, "NC"):
                    continue
                desc = extract_marker_desc(line, "NC")
                if not desc:
                    continue
                if desc not in resolved:
                    nc_unresolved += 1
    if nc_unresolved > 0:
        sys.stderr.write(f"GATE P1: {nc_unresolved} 个未解决的 NEED_CONFIRM 项（阻塞）\n")
        return 1

    # v2.0 T001 流 C：SUGGEST WARNING 去重——suggest_resolved 已采纳项不重复 WARNING
    nc_suggest_unacked = nc_suggest
    if nc_suggest > 0:
        fm_lines = _frontmatter_lines(p1_file)
        sg_resolved_present = sum(1 for line in fm_lines if line.startswith("suggest_resolved:"))
        if sg_resolved_present > 0:
            sg_resolved_fm = _md_field_get("suggest_resolved", p1_file)
            resolved = set(sg_resolved_fm.split("\n"))
            nc_suggest_unacked = 0
            for line in p1_lines:
                if not has_marker(line, "SUGGEST"):
                    continue
                desc = extract_marker_desc(line, "SUGGEST")
                if not desc:
                    continue
                if desc not in resolved:
                    nc_suggest_unacked += 1
    if nc_suggest_unacked > 0:
        sys.stderr.write(
            f"GATE P1 WARNING: {nc_suggest_unacked} 个 SUGGEST 项（主 Agent 可自行采纳，不阻塞）\n"
        )

    # typo 兜底 1：旧标记 [NEED_CONFIRM倾向:] 残留
    if "[NEED_CONFIRM倾向:" in p1_text:
        sys.stderr.write("GATE P1: 检测到旧标记 [NEED_CONFIRM倾向:]。v0.30.2 起已重命名为 [SUGGEST: ...]\n")
        return 1
    # typo 兜底 2：[SUGGEST 开头但不是 [SUGGEST:
    if "[SUGGEST" in p1_text and "[SUGGEST:" not in p1_text:
        sys.stderr.write("GATE P1: SUGGEST 格式不符。合法格式：[SUGGEST: 推荐 X，理由 Y]\n")
        return 1
    if "[NEED_CONFIRM]" in p1_text and nc_blocking == 0:
        sys.stderr.write("GATE P1: 不合规的 NEED_CONFIRM 标记格式（须用行首 [NEED_CONFIRM]、[SUGGEST: ...] 或 [NO_NEED_CONFIRM] 声明）\n")
        return 1
    if nc_blocking == 0 and nc_suggest == 0 and not any(has_marker(line, "NO_NEED") for line in p1_lines):
        sys.stderr.write("GATE P1 WARNING: 未检测到 NEED_CONFIRM 声明（[NEED_CONFIRM] / [SUGGEST: ...] / [NO_NEED_CONFIRM]）\n")

    # RM-AG0039（TAG0022，BDD-6/7）：judge 启用强制化（P1 gate 新增校验，纯叠加于 C 批重构后）
    # 判据（P2-review 锁定决策 2 + NB-4）：judge 块 presence + P1 created（agate-md-field-get
    # created op，ISO 字典序）≥ judge_required_since（rules/dispatch.yaml "2026-08-22"）：
    #   - judge dict + enabled truthy → 放行（继续原 P1 判定，exit 2 语义不变）
    #   - judge dict + enabled falsy / judge 缺失 / judge 非 dict → 同走 created 判据（NB-4）：
    #     created 为 ISO 且 ≥ cutoff → exit 1（机制后新任务缺/未启用 judge）；否则（pre-cutoff /
    #     created 缺失或非 ISO）→ 跳过（fail-open，R5）。
    judge = _load_state_yaml(task_dir).get("judge")
    if not (isinstance(judge, dict) and judge.get("enabled")):
        # DEBT0018：read_rules_yaml 是无条件调用点——agate_common 不可导入时须 fail-closed，
        # 不再因 dispatch_rules 静默为 None 导致 cutoff 判据被跳过（fail-open，误判为 PASS）。
        if _reader_missing(read_rules_yaml):
            sys.stderr.write(
                "GATE P1: 安装破损：agate_common 不可导入，无法读取 rules/dispatch.yaml 判定 judge_required_since 门槛\n"
            )
            return 1
        created = _md_field_get("created", p1_file)
        dispatch_rules = read_rules_yaml(resolve_rules_root(__file__), "dispatch")
        cutoff = dispatch_rules.get("judge_required_since") if isinstance(dispatch_rules, dict) else None
        if isinstance(cutoff, str) and _is_iso_date(created) and created >= cutoff:
            sys.stderr.write(
                f"GATE P1: 机制后新任务（P1 created {created} ≥ judge_required_since {cutoff}）须在 .state.yaml "
                "声明 judge.enabled: true（RM-AG0039 强制）\n"
            )
            return 1

    # TAG0006（BDD-3/16）：frontend 任务 vision 三态声明 + 形态/维度声明合法性（P1 gate 新增检查）
    if not _gate_p1_vision_capability(p1_file):
        return 1
    if not _gate_p1_ui_shape(p1_file):
        return 1

    sys.stderr.write("GATE P1: P1-review.md approved + agent≠main + 含 BDD 锚点。BDD 编号格式为 #### BDD-NN:\n")
    return 2


# TAG0014（P2-design.md §3.1，BDD-2~7）：P2 门 dispatch_plan 字段校验。
# 契约：
#   * op 输出空（无字段 / 坏 YAML）→ 跳过，等同现状（BDD-2/7）
#   * 非空 → json.loads 解析；解析失败同样跳过（不误拦不崩溃，BDD-7）
#   * mode ∈ {single, static-batch, parallel, recon-then-split, serial}（BDD-3）
#   * parallel_limit 存在且 ≥1（BDD-4）
#   * mode ∈ {static-batch, parallel} 时校验 batches：每批含 id + complexity ∈ {low, medium, high}（BDD-5）
#   * batch 数 ≤ parallel_limit（缺省 3）（BDD-6）
# 返回 None = 校验通过（或无需校验）；返回非 None = ERROR 描述（调用方负责 return 1）。
def _gate_p2_dispatch_plan(p2_file):
    raw = _md_field_get("dispatch_plan", p2_file)
    if not raw:
        return None
    try:
        plan = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(plan, dict):
        return None

    valid_modes = frozenset({"single", "static-batch", "parallel", "recon-then-split", "serial"})
    mode = plan.get("mode")
    if not isinstance(mode, str) or mode not in valid_modes:
        return f"dispatch_plan.mode 非法（当前: {mode!r}），须 ∈ {sorted(valid_modes)}"

    parallel_limit = plan.get("parallel_limit")
    if parallel_limit is not None and (not isinstance(parallel_limit, int) or parallel_limit < 1):
        return f"dispatch_plan.parallel_limit 非法（当前: {parallel_limit!r}），须为 ≥1 的整数"

    if mode in ("static-batch", "parallel"):
        batches = plan.get("batches", [])
        if not isinstance(batches, list):
            return f"dispatch_plan.batches 须为列表（当前: {type(batches).__name__}）"
        limit = parallel_limit if parallel_limit is not None else 3
        if len(batches) > limit:
            return f"dispatch_plan 批次数（{len(batches)}）超过 parallel_limit（{limit}）"
        for batch in batches:
            if not isinstance(batch, dict) or "id" not in batch:
                return "dispatch_plan.batches 每批须含 id"
            complexity = batch.get("complexity")
            if complexity not in ("low", "medium", "high"):
                return f"dispatch_plan batch {batch.get('id')!r} 的 complexity 非法（当前: {complexity!r}），须 ∈ low/medium/high"
    return None


def _gate_commands_block_keys(p2_text):
    """提取 P2-design.md gate_commands 多行块内所有 key（无块/空块 → []）。

    M2 起经 agate_common.parse_gate_commands_block 共享解析（BDD-9：块正则不在
    本文件字面出现，落在公共库单点）。
    """
    _has_block, entries = parse_gate_commands_block(p2_text)
    return [k for k, _v in entries]


def _reconcile_p2_fields(p2_file, p2_text):
    """M1 对账（P2-design §3.4，BDD-6/7）：P2 分支四字段/candidate_count 双读 + gate_commands 键集。

    - candidate_count/packages/domains/ui_affected：正文 raw 正则读取 vs frontmatter 结构化
      读取（正文有声明才比对，防"仅 frontmatter 声明"误报）
    - gate_commands：块内键集 vs 声明语法（project_module 特判 / is_gate_meta_key /
      P{阶段} 键，阶段集来自 phases.yaml ∪ 内置 P0-P8）
    差异 → stderr `RECONCILE WARNING` + 汇总计数（可重定向进日志）；对账不改变 gate_p2
    退出码语义（0/1/2 不变，BDD-6）；任何异常 fail-open（不阻断原判定）。
    """
    if not reconcile_enabled():
        return
    try:
        fm, body = split_frontmatter(p2_text)
        for field in ("candidate_count", "packages", "domains", "ui_affected"):
            body_val = body_field_value(body, field)
            if body_val:
                reconcile_field("check-gate-P2", field, body_val, fm_field_value(fm, field))
        keys = _gate_commands_block_keys(p2_text)
        phase_ids = known_phase_ids(resolve_rules_root(__file__))
        for key in keys:
            if not is_legal_gate_key(key, phase_ids):
                reconcile_field("check-gate-P2", "gate_commands." + key, key, "(未声明)")
        reconcile_summary()
    except Exception:
        pass


def gate_p2(task_dir):
    p2_file = os.path.join(task_dir, "P2-design.md")
    if not os.path.isfile(p2_file):
        sys.stderr.write("GATE P2: P2-design.md 不存在——P2 不可裁剪，方案设计是必经阶段\n")
        return 1

    p2_text = _read_text(p2_file)
    p2_lines = _lines(p2_text)

    _reconcile_p2_fields(p2_file, p2_text)

    # v0.31.0：候选方案数显式 candidate_count 字段（纯强制，不再用正则数标题）
    # M2-0038 C 组：行首字段扫描迁 agate_common candidate_count_value
    candidate_count = 0
    for line in p2_lines:
        val = candidate_count_value(line)
        if val is not None:
            candidate_count = val
            break

    p1_file = os.path.join(task_dir, "P1-requirements.md")
    min_candidates = 2
    if os.path.isfile(p1_file):
        p1_lines = _lines(_read_text(p1_file))
        if any(design_trivial_declared(line) for line in p1_lines):
            min_candidates = 1
    if candidate_count < min_candidates:
        sys.stderr.write(
            f"GATE P2: P2-design.md candidate_count={candidate_count}，需至少 {min_candidates} 个候选方案（design_trivial/follows_existing_pattern 时可只写 1）。请显式声明 candidate_count 字段\n"
        )
        return 1

    p2_review = os.path.join(task_dir, "P2-review.md")
    if not os.path.isfile(p2_review):
        sys.stderr.write("GATE P2: P2-review.md 不存在（P2 评审不可裁剪，必须派发独立 subagent 产出）\n")
        return 1

    status = _md_field_get("status", p2_review)
    if status != "approved":
        sys.stderr.write("GATE P2: P2-review.md frontmatter status 非 approved（当前: {}）\n".format(
            status if status else "缺失"))
        return 1

    agent = _md_field_get("agent", p2_review)
    if not agent:
        sys.stderr.write("GATE P2: P2-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
        return 2
    if agent == "main":
        sys.stderr.write("GATE P2: P2-review.md status:approved 但 agent=main（主 Agent 不可自行批准评审）\n")
        return 1

    field_count = count_p2_declared_fields(p2_text)
    if field_count < 4:
        sys.stderr.write(f"GATE P2: P2-design.md 缺字段（需 packages/domains/ui_affected/gate_commands 四字段，实际 {field_count}）\n")
        return 1

    # 多方案探索"权衡/选择理由"nudge（v0.6）；M2-0038 C 组：关键词判定迁 agate_common has_keyword
    if has_keyword(p2_text, "tradeoff") or has_keyword(p2_text, "choice_and_reason"):
        pass
    else:
        sys.stderr.write("GATE P2: P2-design.md 有 ≥2 候选方案但缺'权衡'或'选择理由'描述\n")
        return 1

    # P2.61: gate_commands 命令可执行性检查（WARNING 不阻断，T075 教训）
    missing_cmds = _gate_missing_cmds(p2_file)
    for entry in missing_cmds.split("\n"):
        if not entry:
            continue
        key, sep, token = entry.partition(":")
        if not sep:
            token = ""
        if shutil.which(token) is None:
            sys.stderr.write(
                f"GATE P2 WARNING: gate_commands.{key} 命令 '{token}' 不存在于当前环境——请确认使用完整路径（如 .venv/bin/pytest）或安装依赖。T075 教训：python 不存在导致 P3 gate exit 127\n"
            )

    # TAG0014（dispatch_plan 字段契约，P2-design.md §3.1）：op 输出空（无字段/坏 YAML）→ 跳过，
    # 行为等同现状（BDD-2/7 向后兼容）；非空 → json.loads 校验 mode / parallel_limit / batches。
    _dispatch_error = _gate_p2_dispatch_plan(p2_file)
    if _dispatch_error:
        sys.stderr.write(f"GATE P2 ERROR: {_dispatch_error}\n")
        return 1

    # TAG0006（BDD-4）：ui_affected: true → UI 设计节检查（含形态声明 + 维度选择 + P1-P2 一致性）
    if not _gate_p2_ui_design_section(p2_file):
        return 1

    # TAG0007（BDD-1/3）：project_phase: bootstrap → P2-skeleton.md「## 骨架声明」存在性校验。
    # 字段缺失或为 established（含显式声明）时完全不检查——行为须与改动前逐字节一致（BDD-3 回归）。
    project_phase = _md_field_get("project_phase", p1_file)
    if project_phase == "bootstrap":
        skeleton_file = os.path.join(task_dir, "P2-skeleton.md")
        if not os.path.isfile(skeleton_file) or "## 骨架声明" not in _read_text(skeleton_file):
            sys.stderr.write(
                "GATE P2: project_phase: bootstrap 但 P2-skeleton.md 不存在或缺少「## 骨架声明」标题\n"
            )
            return 1

    sys.stderr.write("GATE P2: 需从 P2-design.md gate_commands 动态读取，主 Agent 自行判定\n")
    return 2


def gate_p3(task_dir):
    p3_cases = os.path.join(task_dir, "P3-test-cases.md")
    if not os.path.isfile(p3_cases):
        sys.stderr.write("GATE P3: P3-test-cases.md 不存在——P3 产出文件缺失\n")
        return 1
    sys.stderr.write("GATE P3: P3-test-cases.md 存在。TDD 红灯由主 Agent 手动跑 check-tdd-red.py 确认 + CI backstop P3 兜底。\n")
    return 2


def gate_p4(task_dir):
    # P4 review 门禁（与 P2 对称，roadmap 补 gap）
    p4_review = os.path.join(task_dir, "P4-review.md")
    if not os.path.isfile(p4_review):
        sys.stderr.write(
            "GATE P4: P4-review.md 不存在（P4 评审不可裁剪，必须派发独立 subagent 产出，见 phase-cards/P4-implementation.md C8 机械映射）\n"
        )
        return 1

    status = _md_field_get("status", p4_review)
    if status != "approved":
        sys.stderr.write("GATE P4: P4-review.md frontmatter status 非 approved（当前: {}）\n".format(
            status if status else "缺失"))
        return 1

    agent = _md_field_get("agent", p4_review)
    if not agent:
        sys.stderr.write("GATE P4: P4-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
        return 2
    if agent == "main":
        sys.stderr.write("GATE P4: P4-review.md status:approved 但 agent=main（主 Agent 不可自行批准评审）\n")
        return 1

    # pre-commit 阶段：检查暂存区有代码文件（非纯文档/状态文件）
    # N1 修复：查 git diff --cached 而非 git log——pre-commit 时 commit 还没创建
    rc, name_only = _git(["diff", "--cached", "--name-only"])
    if rc != 0:
        return 1
    has_code_file = False
    for raw_line in name_only.splitlines():
        line = raw_line.rstrip("\r")
        if not _STAGED_EXCLUDE_RE.search(line):
            has_code_file = True
            break
    if not has_code_file:
        return 1

    # ── RM-AG0046（TAG0026）：维护性反模式三重门槛（检测器 agate/scripts/check-maintainability.py）──
    # 返回约定兼容：本步骤只产生 return 1（门槛 a/b 失败）或继续向下，不新增 return 2；
    # violations 为空 / 检测未部署（ImportError 降级）/ git_ok False 三种跳过场景下，
    # gate_p4 行为与本步骤加入前完全一致（R1 等价性保证）。
    if check_maintainability is not None:
        result = check_maintainability(task_dir)
        if result.get("git_ok"):
            violations = result.get("violations", [])
            if violations:
                # 门槛 a：known-violations.md 存在（BDD-7）。登记本身不构成放行依据——
                # 数量对齐由门槛 b 承担，P4 评审 approve 由既有 ①②③ 承担（顺序在后）。
                known_violations = os.path.join(task_dir, "known-violations.md")
                if not os.path.isfile(known_violations):
                    sys.stderr.write(
                        f"GATE P4: 检测到 {len(violations)} 个维护性反模式 violation，"
                        "需登记 known-violations.md"
                        "（模板 agate/assets/templates/known-violations-template.md）\n"
                    )
                    return 1
                # 门槛 b：count_kf_entries 登记条目数 ≥ violation 数
                # （BDD-8；算法同构 gate_p5 的 known-failures 数量对齐）
                known_entries = count_kf_entries(_read_text(known_violations))
                if known_entries < len(violations):
                    sys.stderr.write(
                        f"GATE P4: known-violations.md 登记条目数({known_entries}) < violation 数({len(violations)})，登记不完整\n"
                    )
                    return 1
                # 门槛 c：P4 评审 approve 且 agent≠main——复用本函数既有 ①②③ 检查，
                # 能执行到这里即 ①②③ 已通过，不重复实现（BDD-9/10 由步骤顺序天然保证）。
        else:
            sys.stderr.write(
                "GATE P4 WARNING: check-maintainability git 通道不可用，本轮跳过维护性检测\n"
            )
    else:
        sys.stderr.write(
            "GATE P4 WARNING: check-maintainability 未部署（ImportError），跳过维护性检测\n"
        )

    # TAG0007（BDD-4/7/10）：骨架/CODE-MAP 机制已采用（P2-skeleton.md 或
    # {AGATE_WORKSPACE}/agents/CODE-MAP.md 存在，OR 条件）且 P4-implementation.md 缺少
    # 「## 新增文件核对表」标题 → WARNING 不阻断（仍 return 0）。change_type 字段不读取、
    # 不分支（BDD-10：refactor 任务同样触发，不豁免）。
    skeleton_file = os.path.join(task_dir, "P2-skeleton.md")
    # DEBT0016：CODE-MAP.md 路径改用 agate_common.resolve_workspace 权威解析（取代本地
    # dirname(dirname(task_dir)) 路径算术，该算术假定 task_dir 恰好两级嵌套在 workspace 下，
    # 非标准嵌套 / .agate.env 覆盖工作区位置时会算错）。project_root 优先取
    # run_git(["rev-parse", "--show-toplevel"]) 的 git 顶层；run_git 不可用/失败时退化为
    # 本地算术推导值仅作 resolve_workspace 的入参兜底（resolve_workspace 内部按
    # project_root/.agate.env 覆盖解析，找不到该文件时走其默认 {project_root}/agate-workspace
    # 规则，不因入参不精确而抛错）。resolve_workspace 本身不可用（agate_common 整体不可导入，
    # 与 run_git 同一 import 块，生产环境下二者必然同生共死）时才整体回退旧算术——本分支是
    # WARNING-only（不 return 1），不是 DEBT0018 evidence 点名的 4 个"关键读取器"之一，
    # 保持 fail-open 与既有 WARNING 语义一致（R3）。
    code_map_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(task_dir))), "agents", "CODE-MAP.md"
    )
    if resolve_workspace is not None:
        project_root = None
        if run_git is not None:
            _rc, _out = run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)
            if _rc == 0 and _out.strip():
                project_root = _out.strip()
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(task_dir)))
        _workspace, _tasks_dir = resolve_workspace(project_root)
        code_map_file = os.path.join(_workspace, "agents", "CODE-MAP.md")
    if os.path.isfile(skeleton_file) or os.path.isfile(code_map_file):
        p4_impl_check = os.path.join(task_dir, "P4-implementation.md")
        # DEBT0017：子串 `in` 判定改为整行/标题级 re.MULTILINE 正则（参照 agate_common.py
        # extract_bdd_titles/parse_ui_design_section 写法风格），消除自指/dogfooding 场景下
        # 假阳性（散文提及标题字面量『## 新增文件核对表』被子串判定误判为"标题已存在"，
        # 导致本该触发的 WARNING 被错误跳过）。标题行尾允许附加说明文字（只要求行首匹配，
        # 不要求标题后无内容）。
        if not re.search(r"^##\s+新增文件核对表", _read_text(p4_impl_check), re.MULTILINE):
            sys.stderr.write(
                "GATE P4 WARNING: 骨架/CODE-MAP 机制已采用，但 P4-implementation.md 缺少「## 新增文件核对表」标题（不阻断，请补充）\n"
            )

    return 0


def gate_p5(task_dir):
    # P5 gate：技术验证需动态读取 gate_commands.P5，主 Agent 自行执行并判定
    sys.stderr.write("GATE P5: 需从 P2-design.md gate_commands.P5 动态读取，主 Agent 自行判定\n")
    # WARNING：P2 声明多个 gate_commands.P5 命令（单元+集成+E2E）时提醒全部执行
    # （T060 教训：只跑子集可能掩盖预存失败）
    p2_file = os.path.join(task_dir, "P2-design.md")
    if os.path.isfile(p2_file):
        p5_main, p5_aux = _gate_p5_count(p2_file)
        p5_total = p5_main + p5_aux
        if p5_total > 1:
            sys.stderr.write(
                f"GATE P5 WARNING: P2 声明了 {p5_main} 个主命令 + {p5_aux} 个辅助命令（共 {p5_total} 条 gate_commands.P5 命令），请确认已全部执行（非子集）。\n"
            )
            sys.stderr.write("  T060 教训：只跑子集可能掩盖预存失败（T056 venv 遗漏跨 4 个任务周期无人发现）。\n")

    # 机械 diff：pre-task-baseline.md vs fail-list.txt
    baseline = os.path.join(task_dir, "pre-task-baseline.md")
    post_fails = os.path.join(task_dir, "P5-test-results", "fail-list.txt")
    if os.path.isfile(baseline) and os.path.isfile(post_fails):
        baseline_text = _read_text(baseline)
        if not any(line.startswith("captured_at_commit:") for line in _lines(baseline_text)):
            sys.stderr.write("GATE P5: pre-task-baseline.md 存在但缺少 captured_at_commit: 标记，视为损坏，\n")
            sys.stderr.write("  降级为 WARNING-only（exit 2），不做机械 diff——请检查基线文件完整性\n")
            return 2

        # sed -n '/```fail-list/,/```/p' | sed '1d;$d' | grep -v '^$' 等价；
        # M2-0038 C 组：块解析迁 agate_common parse_fail_list_block
        pre_list = parse_fail_list_block(baseline_text)

        pre_set = sorted(set(pre_list))
        post_set = sorted({line for line in _lines(_read_text(post_fails)) if line})
        # comm -13：仅存在于第二文件（新增失败）；comm -12：两文件共有（预存失败）
        new_fails = [x for x in post_set if x not in pre_set]
        still_failing = [x for x in pre_set if x in post_set]

        if new_fails:
            sys.stderr.write("GATE P5: 检测到基线快照中不存在的新增失败，视为本任务引入的回归，拦截：\n")
            for item in new_fails:
                sys.stderr.write(f"  - {item}\n")
            return 1
        if still_failing:
            still_count = len(still_failing)
            known_failures = os.path.join(task_dir, "known-failures.md")
            if not os.path.isfile(known_failures):
                sys.stderr.write(f"GATE P5: 检测到 {still_count} 个预存失败仍未修复，\n")
                sys.stderr.write("  基线快照证实这些失败早于本任务存在，但 known-failures.md 不存在——按协议必须登记\n")
                return 1
            # M2-0038 C 组：登记表条目计数迁 agate_common count_kf_entries
            known_entries = count_kf_entries(_read_text(known_failures))
            if known_entries < still_count:
                sys.stderr.write(
                    f"GATE P5: known-failures.md 登记条目数({known_entries}) < 预存失败数({still_count})，\n"
                )
                sys.stderr.write("  登记不完整——每个预存失败都应有对应登记行\n")
                return 1
    return 2


def gate_p6(task_dir):
    # T001 v2.0 流 B（BDD-16/18，P2-design.md §3.2.1）：frontmatter pass/fail 汇总判定，
    # 无汇总（旧格式）回退正文 grep 计数（只认行首 `- PASS|FAIL ... BDD-N`，消除 F11 误判）。
    p6_file = os.path.join(task_dir, "P6-acceptance.md")

    # ── v2.0 refactor 口径分流（TAG0002 Phase A，P2-design.md §3.3）──
    change_type = ""
    p1_file = os.path.join(task_dir, "P1-requirements.md")
    if os.path.isfile(p1_file):
        change_type = _md_field_get("change_type", p1_file)
    if change_type == "refactor":
        regression_pass = _md_field_get("regression_pass", p6_file)
        if regression_pass != "true" or not os.path.isfile(os.path.join(task_dir, "P6-evidence", "regression.log")):
            sys.stderr.write(
                "GATE P6: change_type=refactor 但缺全量回归证据（须 P6-acceptance.md frontmatter regression_pass: true 且 P6-evidence/regression.log 存在）\n"
            )
            return 1

    # ↓↓ 既有判定（pass/fail 汇总 / 证据目录非空）原样保留，不随 change_type 变化 ↓↓
    pass_fm = _md_field_get("pass", p6_file)
    fail_fm = _md_field_get("fail", p6_file)
    if pass_fm != "" and fail_fm != "":
        # 新格式：frontmatter 汇总判定（BDD-16）
        total = _to_int(pass_fm) + _to_int(fail_fm)
        fail = _to_int(fail_fm)
    else:
        # 旧格式回退：正文行首 PASS/FAIL 计数（BDD-18，行首须含 BDD 编号才计入，大小写不敏感）
        # M2-0038 C 组：计数迁 agate_common count_p6_pass_fail
        # DEBT0018：agate_common 不可导入时 fail-closed，不再让降级 stub 的 (0, 0) 与真实
        # "无 BDD 条目" 混同为通用消息（无法让运维区分是真的 0 条还是安装破损降级读数）。
        if _reader_missing(count_p6_pass_fail):
            sys.stderr.write(
                "GATE P6: 安装破损：agate_common 不可导入，无法读取 PASS/FAIL 计数\n"
            )
            return 1
        total, fail = count_p6_pass_fail(_read_text(p6_file))
    if fail != 0 or total == 0:
        sys.stderr.write(f"GATE P6: FAIL={fail}, TOTAL={total}\n")
        return 1

    # 证据存在性检查（⚠️ self-authored gate 的缓解措施）
    evidence_dir = os.path.join(task_dir, "P6-evidence")
    if not os.path.isdir(evidence_dir) or not os.listdir(evidence_dir):
        sys.stderr.write("GATE P6: P6-evidence/ 目录不存在或为空\n")
        return 1

    sys.stderr.write(
        f"GATE P6: 证据目录非空，FAIL=0，NC=0，P6_TOTAL={total}。BDD 总数对照由 check-p6-provenance.py 审计 3 自动执行。\n"
    )
    return 2


def gate_p65(task_dir):
    """P6.5 judge 强门槛子阶段（TAG0020，BDD-1/2/9；P2-design §3.5 候选 1）。

    P6.5 是挂载于 P6→P7 转移上的强门槛子阶段，非独立 phase 值（.state.yaml phase
    保持 P6 至 P7）。判定：
    - judge 未启用（.state.yaml 无 judge.enabled: true / 历史任务）→ 早退 0（BDD-2）
    - 启用但缺 P6.5-judge-verdict.md → exit 1（BDD-1 fail-closed，P6→P7 阻断）
    - 否则依次调 check-judge-verdict.py + check-events.py，任一 exit 1 → exit 1
      （BDD-9：机械核对 exit code 才是门槛，LLM verdict 不单独放行）
    """
    state_yaml = _load_state_yaml(task_dir)
    judge = state_yaml.get("judge") if isinstance(state_yaml, dict) else None
    if not (isinstance(judge, dict) and judge.get("enabled")):
        sys.stderr.write("GATE P6.5: judge 机制未启用（历史任务），跳过\n")
        return 0
    verdict = os.path.join(task_dir, "P6.5-judge-verdict.md")
    if not os.path.isfile(verdict):
        sys.stderr.write("GATE P6.5: 缺 P6.5-judge-verdict.md（judge 未产出），P6→P7 阻断\n")
        return 1
    for script in ("check-judge-verdict.py", "check-events.py"):
        if _run_gate_script(script, task_dir) != 0:
            sys.stderr.write(f"GATE P6.5: {script} 未通过\n")
            return 1
    sys.stderr.write("GATE P6.5: judge 复核 + 账本审计通过\n")
    return 0


def gate_p7(task_dir):
    # v0.6：显式 if/elif/else；T001 v2.0 流 B（BDD-19/20，P2-design.md §3.2.2）：
    # frontmatter 声明 blocker_count/deviation_critical_count/design_gap_count/
    # design_gap_reviewed_count（新格式）→ 门禁基于结构化计数判定；缺失（旧格式）回退正文 grep。
    p7_file = os.path.join(task_dir, "P7-consistency.md")

    blocker_fm = _md_field_get("blocker_count", p7_file)
    devcrit_fm = _md_field_get("deviation_critical_count", p7_file)
    if blocker_fm != "" and devcrit_fm != "":
        # 新格式：frontmatter 结构化计数判定（BDD-19）
        blockers = _to_int(blocker_fm)
        devcrit = _to_int(devcrit_fm)
    else:
        # 旧格式回退：正文 grep + 非计数行排除正则（既有逻辑）
        # M4：[:：] bracket 在 POSIX locale 不匹配全角冒号 → alternation (:|：)。
        # M2-0038 C 组：计数迁 agate_common count_p7_markers
        # DEBT0018：agate_common 不可导入时 fail-closed——降级 stub 的 (0, 0) 此前会静默
        # 落到函数末尾 return 0（真正的 false-PASS），改为显式失败。
        if _reader_missing(count_p7_markers):
            sys.stderr.write(
                "GATE P7: 安装破损：agate_common 不可导入，无法读取 BLOCKER/DEVIATION-CRITICAL 计数\n"
            )
            return 1
        blockers, devcrit = count_p7_markers(_read_text(p7_file))
    if blockers > 0 or devcrit > 0:
        sys.stderr.write(f"GATE P7: BLOCKER={blockers}, DEVIATION-CRITICAL={devcrit}\n")
        return 1

    # DESIGN_GAP 配对检查（v0.6：未配对 REVIEWED 标记的 DESIGN_GAP → 不通过）
    dg_count_fm = _md_field_get("design_gap_count", p7_file)
    dg_reviewed_fm = _md_field_get("design_gap_reviewed_count", p7_file)
    if dg_count_fm != "" and dg_reviewed_fm != "":
        # 新格式：reviewed_count >= count 通过（BDD-20，F14 消除数量相减歧义）
        dg_count = _to_int_or_none(dg_count_fm)
        dg_reviewed = _to_int_or_none(dg_reviewed_fm)
        if dg_count is not None and dg_reviewed is not None and dg_reviewed < dg_count:
            sys.stderr.write(
                f"GATE P7: 有 {dg_count - dg_reviewed} 条 [DESIGN_GAP] 未配对 [DESIGN_GAP_REVIEWED]（frontmatter: design_gap_count={dg_count}, design_gap_reviewed_count={dg_reviewed}）——主 Agent 需审查 implementer 的自主决策\n"
            )
            return 1
        if dg_count is None:
            dg_count = 0
        if dg_reviewed is None:
            dg_reviewed = 0
    else:
        # 旧格式回退：正文 grep 数量相减判定（既有逻辑）；M2-0038 C 组：计数迁
        # agate_common count_design_gap（allow_blockquote=True = P7 口径含 blockquote 前缀）
        dg_count, dg_reviewed = count_design_gap(_read_text(p7_file))
        unreviewed = dg_count - dg_reviewed
        if unreviewed > 0:
            sys.stderr.write(
                f"GATE P7: 有 {unreviewed} 条 [DESIGN_GAP] 未配对 [DESIGN_GAP_REVIEWED]——主 Agent 需审查 implementer 的自主决策\n"
            )
            return 1

    # 问题4 (T090)：P4 含"设计偏差/gap"关键词但 DESIGN_GAP 计数为 0 → WARNING 提醒人工确认
    if dg_count == 0:
        p4_impl = os.path.join(task_dir, "P4-implementation.md")
        if os.path.isfile(p4_impl) and has_keyword(_read_text(p4_impl), "design_gap"):
            sys.stderr.write(
                    "GATE P7 WARNING: P4 检测到设计偏差相关关键词但 [DESIGN_GAP:] 计数为 0——请确认是否真的无偏差，或 P4 未按标准格式声明\n"
                )

    # R2.3 修复：P4/P7 DESIGN_GAP 数量交叉核对（architect 忘记把 P4 的 DESIGN_GAP 转抄到 P7）
    p4_gap_lines = []
    p4_impl_file = os.path.join(task_dir, "P4-implementation.md")
    if os.path.isfile(p4_impl_file):
        p4_gap_lines.extend(_lines(_read_text(p4_impl_file)))
    p4_impl_dir = os.path.join(task_dir, "P4-implementation")
    if os.path.isdir(p4_impl_dir):
        for root, _dirs, names in os.walk(p4_impl_dir):
            for name in names:
                p4_gap_lines.extend(_lines(_read_text(os.path.join(root, name))))
    # grep -rh '\[DESIGN_GAP:' 过滤后 grep -cE '^\s*-?\s*\[DESIGN_GAP:' 等价；
    # M2-0038 C 组：计数迁 agate_common count_design_gap（allow_blockquote=False = P4 口径）
    p4_gap_lines = [line for line in p4_gap_lines if "[DESIGN_GAP:" in line]
    p4_design_gap_count, _unused_reviewed = count_design_gap(
        "\n".join(p4_gap_lines), allow_blockquote=False
    )
    if p4_design_gap_count > dg_count:
        sys.stderr.write(
            f"GATE P7: P4 声明了 {p4_design_gap_count} 条 [DESIGN_GAP]，P7 只转抄了 {dg_count} 条——architect 遗漏转抄\n"
        )
        return 1

    # N3: review 实质锚点 WARNING——P7 有 DESIGN_GAP_REVIEWED 但缺跨文件引用
    if dg_reviewed > 0 and not re.search(r"P1.*BDD|P2.*packages|P4.*implementation", _read_text(p7_file)):
        sys.stderr.write(
                "WARNING P7: P7-consistency.md 有 DESIGN_GAP_REVIEWED 但缺跨文件引用关键词（P1 BDD / P2 packages / P4 implementation）——review 可能未做实质性交叉检查\n"
            )

    # TAG0007（BDD-8/9/10）：CODE_MAP pairing 两层硬校验，仿照上方 DESIGN_GAP pairing 模板
    # （字段对应关系：内部一致性层比较 code_map_reviewed_count 与 code_map_new_files_count；
    # 转抄核对层比较 P4 实际标记数与 code_map_new_files_count，不是 code_map_reviewed_count）。
    # 两字段均缺失 → 机制未采用，两层校验全部跳过（回归对照）。change_type 字段不读取、不分支
    # （BDD-10：refactor 任务同样生效）。与上方 DESIGN_GAP 逻辑并行独立，不共享变量。
    # TAG0022（RM-AG0038，A 组）：code_map_new_files_count/code_map_reviewed_count 已注册
    # agate-md-field-get NO_FALLBACK_INT_FIELDS（frontmatter-only，无正文回退），改走
    # _md_field_get——解 DESIGN_GAP 遗留（此前 KNOWN_OPS 未注册，_md_field_get unknown op
    # exit 2 恒回退空串致两层校验整段跳过）。
    cm_count_fm = _md_field_get("code_map_new_files_count", p7_file)
    cm_reviewed_fm = _md_field_get("code_map_reviewed_count", p7_file)
    if cm_count_fm != "" and cm_reviewed_fm != "":
        cm_count = _to_int_or_none(cm_count_fm)
        cm_reviewed = _to_int_or_none(cm_reviewed_fm)
        # 内部一致性层
        if cm_count is not None and cm_reviewed is not None and cm_reviewed < cm_count:
            sys.stderr.write(
                f"GATE P7: CODE_MAP 新增文件核对未通过——code_map_reviewed_count={cm_reviewed} < code_map_new_files_count={cm_count}\n"
            )
            return 1
        if cm_count is None:
            cm_count = 0
        # 转抄核对层：P4 正文实际 [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT] 标记数
        # > code_map_new_files_count（注意不是 code_map_reviewed_count）→ return 1
        # M2-0038 C 组：计数迁 agate_common count_code_map_lines
        # DEBT0018：与另外三个消费点相反——本调用点只在 code_map_new_files_count/
        # code_map_reviewed_count 字段均已声明（机制已采用）时才会触达，不是旧格式回退分支
        # （R2）。agate_common 不可导入时同样 fail-closed，不让降级 stub 的 0 静默落到
        # 函数末尾 return 0（false-PASS）。
        if _reader_missing(count_code_map_lines):
            sys.stderr.write(
                "GATE P7: 安装破损：agate_common 不可导入，无法读取 CODE-MAP 转抄标记计数\n"
            )
            return 1
        p4_impl_file_for_cm = os.path.join(task_dir, "P4-implementation.md")
        p4_code_map_actual_count = count_code_map_lines(_read_text(p4_impl_file_for_cm))
        if p4_code_map_actual_count > cm_count:
            sys.stderr.write(
                f"GATE P7: P4 实际标记 {p4_code_map_actual_count} 条 [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT]，"
                f"超过 P7 声明的 code_map_new_files_count={cm_count}（转抄核对未通过）\n"
            )
            return 1

    return 0


_ROADMAP_EXPECTED_COLS = 9  # 7 数据列（id/标题/状态/来源/关联任务/创建/更新）
                            # + split("|") 产生的首尾两个空字符串 = 9
                            # （已用真实 agate-workspace/roadmap/roadmap.md 表头行核实，
                            # 见 P2-design.md §3.6/§6）


def _check_roadmap_done(task_id, roadmap_path):
    """RM-AG0043（BDD-5/6，P2-design.md §2.2 候选 A / D2 匹配算法）：按 task_id 精确匹配
    roadmap.md「关联任务」列（表格第 5 数据列），收集全部匹配行；任一「状态」列非 done →
    返回 (rm_id, status) 供 gate_p8() 阻断。无匹配行（含关联任务列值是其他 task_id 的情况）
    → 返回 None，不误拦（BDD-6）。roadmap.md 不存在时同样返回 None（不阻断，向后兼容无
    roadmap 场景的既有 G8 系列测试）。

    表格解析：按 `|` 分列，跳过表头/分隔行（首个非空列不以 `RM-` 开头即视为非数据行）。
    列数须精确匹配 _ROADMAP_EXPECTED_COLS（DEBT0019）：单元格内含字面 `|` 会改变
    split 后的列数，此时整行跳过而非错位取值（BDD-20）；既有合法表格列数恰为 9，
    行为不变（BDD-21）。
    """
    text = _read_text(roadmap_path)
    if not text or not task_id:
        return None
    for line in text.splitlines():
        cols = [c.strip() for c in line.split("|")]
        if len(cols) != _ROADMAP_EXPECTED_COLS:
            continue
        rm_id, status, related_task = cols[1], cols[3], cols[5]
        if not rm_id.startswith("RM-"):
            continue
        if related_task == task_id and status != "done":
            return rm_id, status
    return None


def gate_p8(task_dir):
    # P8 部分检查可脚本化，其余需主 Agent 自判。
    # version 文件路径和 CHANGELOG 文件名因项目而异，主 Agent 从 P2-design.md packages 读取。
    # 用 git diff --cached（暂存区），不用 HEAD~1——pre-commit 时本次变更还没进 HEAD
    # （与 P4/P7 同款修复，v0.6 hardening R4 chicken-and-egg 教训）。
    p8_file = os.path.join(task_dir, "P8-release.md")
    p8_text = _read_text(p8_file)

    # 检查 bump_type 字段
    if "bump_type:" not in p8_text:
        sys.stderr.write("GATE P8: P8-release.md 缺 bump_type 字段\n")
        return 1
    # 债务清单确认留痕检查（TAG0001 Phase 3）：只查留痕存在，不查内容达标、不阻断发布
    if "debt_check:" not in p8_text:
        sys.stderr.write("GATE P8: P8-release.md 缺 debt_check 字段（须确认债务清单并留痕，可为 none）\n")
        return 1

    # RM-AG0043（BDD-5/6）：P8 完成时反查 roadmap.md 关联 RM 条目是否已回写 done
    # DEBT0020：roadmap_path 按仓库根锚定（而非 CWD 相对拼接），非仓库根 CWD 下仍能
    # 正确定位（BDD-22）；仓库根不可得（非 git 仓库环境）时给出区分性提示，不静默跳过
    # （BDD-23）；CWD=仓库根的既有场景行为不变（BDD-24）。
    task_id = _load_state_yaml(task_dir).get("task_id", "")
    rc, repo_root_out = _git(["rev-parse", "--show-toplevel"])
    if rc != 0:
        sys.stderr.write(
            "GATE P8 WARNING: 仓库根不可得（非 git 仓库环境），跳过 roadmap-done 检查\n"
        )
        roadmap_path = None
    else:
        roadmap_path = os.path.join(
            repo_root_out.strip(), "agate-workspace", "roadmap", "roadmap.md"
        )
    blocked = _check_roadmap_done(task_id, roadmap_path) if roadmap_path else None
    if blocked:
        rm_id, status = blocked
        sys.stderr.write(
            f"GATE P8: roadmap.md 关联记录 {rm_id} 状态为 {status}（非 done），须先回写 done 再推进发布\n"
        )
        return 1

    # 检查 version 文件变更（路径 A: 暂存区 + 路径 B: 最近 commit）
    version_pattern = os.environ.get(
        "AGATE_VERSION_FILES",
        "version|__version__|package.json|Cargo.toml|pyproject.toml|go.mod|pom.xml|gemspec|csproj",
    )
    version_re = re.compile(version_pattern, re.IGNORECASE)
    cached_version = False
    rc, stat_out = _git(["diff", "--cached", "--stat"])
    if rc == 0 and version_re.search(stat_out or ""):
        cached_version = True
    recent_version = False
    if not cached_version:
        lookback = os.environ.get("AGATE_P8_LOOKBACK", "5")
        lookback_num = _to_int(lookback, 5)
        rc, _ = _git(["rev-parse", f"HEAD~{lookback_num}"])
        if rc == 0:
            rc, stat_out = _git(["diff", f"HEAD~{lookback_num}..HEAD", "--stat"])
            if rc == 0 and version_re.search(stat_out or ""):
                recent_version = True
    if not cached_version and not recent_version:
        sys.stderr.write(f"GATE P8 WARNING: 暂存区和最近 {lookback_num} 个 commit 均无 version 文件变更\n")

    # 检查 CHANGELOG 变更（双路径，降级为 WARNING）
    changelog_file = os.environ.get("CHANGELOG_FILE", "CHANGELOG.md")
    cached_changelog = False
    rc, diff_out = _git(["diff", "--cached", "--", changelog_file])
    if rc == 0 and any(line for line in (diff_out or "").splitlines()):
        cached_changelog = True
    recent_changelog = False
    if not cached_changelog:
        lookback_num = _to_int(os.environ.get("AGATE_P8_LOOKBACK", "5"), 5)
        rc, _ = _git(["rev-parse", f"HEAD~{lookback_num}"])
        if rc == 0:
            rc, diff_out = _git(["diff", f"HEAD~{lookback_num}..HEAD", "--", changelog_file])
            if rc == 0 and any(line for line in (diff_out or "").splitlines()):
                recent_changelog = True
    if not cached_changelog and not recent_changelog:
        sys.stderr.write(
            f"GATE P8 WARNING: 暂存区和最近 {lookback_num} 个 commit 均无 {changelog_file} 变更\n"
        )

    # 检查 tag 存在性（WARNING，不阻断——tag 通常在 gate 通过后才打）
    version_tag_prefix = os.environ.get("VERSION_TAG_PREFIX", "v")
    tag_version = ""
    rc, changelog_diff = _git(["diff", "--cached", "--", changelog_file])
    if rc == 0:
        m = re.search(r"\[[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9.-]*\]", changelog_diff or "")
        if m:
            tag_version = m.group(0).lstrip("[").rstrip("]")
    if tag_version:
        rc, tag_out = _git(["tag", "-l", version_tag_prefix + tag_version])
        if rc == 0 and not any(line for line in (tag_out or "").splitlines()):
            sys.stderr.write(
                f"GATE P8 WARNING: tag {version_tag_prefix}{tag_version} 不存在。打 tag 后再推进到 READY。若 tag 前缀非 v，设置 VERSION_TAG_PREFIX 环境变量。\n"
            )

    sys.stderr.write(
        "GATE P8: 脚本化检查通过。仍需主 Agent：① 从 P2 gate_commands 逐包读取发布检查命令 ② 重跑 P5 gate ③ 用 git log 对照 CHANGELOG 无遗漏 ④ 从 P2 packages 验证 version 文件路径\n"
    )
    return 2


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("用法: check-gate.py PHASE TASK_DIR\n")
        sys.exit(1)
    phase = sys.argv[1]
    task_dir = sys.argv[2]
    old_phase = sys.argv[3] if len(sys.argv) > 3 else ""

    # 回退抵达检测（可选第 3 参数，向后兼容：不传 = 行为与之前完全一致）。
    if old_phase:
        old_num = re.search(r"[0-9]+", old_phase)
        new_num = re.search(r"[0-9]+", phase)
        if old_num and new_num and int(old_num.group(0)) > int(new_num.group(0)):
            sys.stderr.write(
                f"GATE {phase}: 检测到回退抵达（上一阶段 {old_phase} → {phase}），本次 commit 视为回退声明，暂不做完成度校验\n"
            )
            sys.stderr.write(f"  该阶段的工作尚待重新进行；重新推进离开 {phase} 时会再次正常校验\n")
            sys.exit(2)

    handlers = {
        "P0": gate_p0,
        "P1": gate_p1,
        "P2": gate_p2,
        "P3": gate_p3,
        "P4": gate_p4,
        "P5": gate_p5,
        "P6": gate_p6,
        "P6.5": gate_p65,
        "P7": gate_p7,
        "P8": gate_p8,
    }
    func = handlers.get(phase)
    if func is None:
        sys.stderr.write(f"未知阶段: {phase}\n")
        sys.exit(1)
    sys.exit(func(task_dir))


if __name__ == "__main__":
    main()
