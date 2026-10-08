#!/usr/bin/env python3
"""从 P1/P2 markdown 提取字段（py 抽离共享工具，v2.0 T001 流 A 双读改造）。

== 两类字段（M2/TAG0021 结构化层，P2-design §3.5 M2-2）==
本工具是**任务数据字段**的统一读取入口：本文件全部 KNOWN_OPS（risk_level / phases /
candidate_count / packages / domains / ui_affected / gate 汇总计数 / 标记状态等）都是
任务文件（P1/P2/P6/P7 产出 md）中由用户/前序阶段声明的**任务数据**，读取路径 =
frontmatter（结构化优先，v2.0 机器字段）→ 正文正则回退（旧格式兼容）。
**协议规则字段**（阶段门槛 / 产出声明 / gate 语法 / retry 上限——存于 {agate_root}/rules/
*.yaml）**不经本工具读取**：消费脚本经 agate_common.read_rules_yaml 直接读 YAML 权威源
（check-gate / check-pruning 等的 gate_commands 合法 key 判定、阶段集即此路径）。
两类字段边界：任务数据随任务走（本文件），协议规则随协议版本走（rules/*.yaml）——
M2 切换权威源后二者不再混读，防止"同一规则多处解析"漂移（P1 §4.1 B 组实证）。

从 FILE 环境变量读文件路径，按子命令（op）提取字段值。FILE 不存在/不可读时
抛异常（FileNotFoundError）→非零退出（由 bash 调用方 2>/dev/null || echo 兜底）。

双读判别契约（P2-design.md §3.1.2，FIND-1 修订，字段级 presence 检测）：
  - 文件头 "---" frontmatter 块存在、可解析为 dict、且该 op 对应字段在
    frontmatter 中存在（key 存在且值非 null）→ 取 frontmatter 值（格式化后输出）
  - 否则（无 frontmatter 块 / 解析失败 / 字段不在 frontmatter 中 / 值为 null）
    → 正则回退（v0.35 行为，扫描全文，兼容旧格式正文内嵌字段）

用法（op 列表）：
  风险_level                 frontmatter 字符串 / 正文 "risk_level: low|medium|high"
  change_type                frontmatter 字符串（P1 任务类型声明，可选；缺省=功能口径；
                            frontmatter-only，无正文回退，TAG0002——正文散文提及
                            "change_type: refactor" 不读取）
  ui_affected                frontmatter bool（归一化输出 "true"/"false"）/ 正文 "ui_affected: true|false"
  ui_render_shape            frontmatter 字符串（P1 渲染形态声明，规范值 layout/render_component/
                            temporal_effects）/ 正文 "ui_render_shape: <值>"（presence 语义，缺失即布局型默认）
  ui_ux_dimensions           frontmatter list（P1 维度选择，空格连接）/ 正文内联或块式列表
  phases                     frontmatter list（内联或块式）/ 正文内联 "[P1, P2]" 或块式 "- Pn"
  candidate_count             frontmatter int（P2-design.md）/ 正文 "candidate_count: N"
  packages / domains         frontmatter list（空格连接）/ 正文内联或块式列表
  override / internal_only_reason / 跳过风险   presence 语义字符串字段
  internal_only / design_trivial               presence 语义 bool 字段
  coupling_checklist / follows_existing_pattern  presence 语义 list 字段
  pass / fail                                    P6 int 汇总字段（frontmatter-only，无正文回退）
  regression_pass                               P6 refactor 回归全绿 bool（frontmatter-only，无正文回退）
  blocker_count / deviation_count /
  deviation_critical_count / design_gap_count /
  design_gap_reviewed_count                      P7 int 计数字段（frontmatter-only，无正文回退）
  code_map_new_files_count / code_map_reviewed_count  P7 CODE_MAP 配对 int 计数字段
                                                    （frontmatter-only，无正文回退，TAG0022）
  status / agent                                 P1/P2/P4 review 文件 frontmatter-only 字段
                                                    （TAG0022：A 组迁移自 check-gate 本地读取）
  project_phase                                  P1-requirements.md frontmatter-only 字段（TAG0022）
  created                                        P1-requirements.md 日期字段（frontmatter-only，
                                                    TAG0022 C 批注册，B 批 judge_required_since 判据用）
  need_confirm_resolved / suggest_resolved /
  scope_resolved                                 P1 流 C 标记状态字段（frontmatter-only，无正文回退，
                                                  换行连接，供调用方逐条匹配）

流 C 新增字段（P1 标记"已解决/已确认"状态，P2-design.md §3.3）的语义：
  这 3 个字段是 v2.0 新增的结构化状态列表，v0.35 正文里没有对应的单行声明形式
  （散文标记 [NEED_CONFIRM]/[SUGGEST:]/[SCOPE+] 本体仍保留在正文，不迁移，BDD-23）。
  frontmatter 中不存在该字段时输出空字符串，不做正则回退——"字段是否存在"和"回退到
  旧格式判定逻辑"的责任交给调用方（check-gate.sh / check-scope-resolved.sh）。
  列表格式化为**换行连接**（而非其余 LIST_FIELDS 的空格连接）：因为这 3 个字段的元素
  是含空格的散文描述（如"z 的边界条件需确认"），空格连接会让调用方无法区分元素边界，
  换行连接使调用方可用 `grep -qF -- "$desc"` 逐条子串匹配（BDD-21 逐条匹配要求）。

流 B 新增字段（P6/P7 结构化计数）的"无正文回退"语义（P2-design.md §3.2）：
  v0.35 正文里这些字段从来不是单行声明——旧格式靠 grep 计数 PASS/FAIL 行数、
  BLOCKER 关键词数，不是读一个字段。因此这些字段在 frontmatter 中不存在时，
  本工具直接输出空字符串，不在内部模拟"正则计数回退"。"回退到旧格式计数逻辑"
  是调用方（check-gate.sh / check-p6-provenance.sh）的责任：op 返回非空 → 用
  frontmatter 声明值；op 返回空 → 调用方自行执行原有的正文 grep 计数逻辑。
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-md-field-get: 需要 pyyaml\n")
    sys.exit(1)

# TAG0050 批 B（设计 §3.3）：writer: system 字段按快照 derive 现算。单源库与等级/契约
# 解析来自 agate_common（与 md-field-set / gate 同源）；仅在非 legacy 且快照可用时生效。
try:
    import agate_common
    import agate_schema
except ImportError:  # 安装破损降级：单源库不可用时不做现算（回退文件值，保持旧行为）
    agate_common = None
    agate_schema = None


# bool 字段：_format_value 归一化为恰好 "true"/"false"（小写，FIND-4 落地）。
# 下游 check-p6-evidence.sh:64 / check-p6-provenance.sh:155 做精确字符串匹配，
# 依赖此处输出小写，不能是 Python str(bool) 的 "True"/"False"。
BOOL_FIELDS = frozenset({"ui_affected", "internal_only", "design_trivial"})

# P6 refactor 口径的"回归全绿"声明字段（TAG0002，P2-design.md §3.1.3）：bool 无正文回退。
# 与 NO_FALLBACK_INT_FIELDS 同语义——frontmatter 无该字段时输出空字符串，不做正文正则
# 回退（防正文伪造陷阱，MDF.10：正文写 `regression_pass: false` 陷阱行不应被读到）。
# TAG0015（BDD-6/17，重试#1 A7 修复）：feedback_ready 同语义，retrospective.md 全新文档类型，
# 无需正文回退。
NO_FALLBACK_BOOL_FIELDS = frozenset({"regression_pass", "feedback_ready"})

# TAG0002（P2-design.md §3.1.3，P4-review §2.1 BLOCKER 修复）：P1 任务类型声明字段
# （可选，缺省=功能口径），frontmatter-only，无正文回退——change_type 是新增 P1 机器字段，
# v0.35 正文旧格式从未有该字段（与 risk_level 不同——risk_level 有旧正文格式需要回退，
# 无向后兼容需求）。正文散文提及 `change_type: refactor`（如"change_type: refactor 是可选
# 字段"、"本任务不涉及 change_type: refactor 机制"）不得被误判为 refactor 任务（否则违反
# BDD-2"未声明 change_type 的任务验收行为与改造前完全一致"）。
# TAG0019（P4-review C1 修复）：ceremony 同因移入——全新 P1 机器字段（thin/standard/full），
# 无旧正文格式回退需求；frontmatter 未声明 ceremony 的任务，正文散文提及 `ceremony: xxx`
# （如薄化叙述/checklist 引用）不得被误读为非法值（否则违反 BDD-8"不声明 = standard 不拦截"）。
# TAG0022（RM-AG0038，C 批）：status/agent（评审文件 P1/P2/P4-review.md）、project_phase
# （P1-requirements.md）、created（P1 日期判据，B 批 judge_required_since 用）——全部是
# frontmatter-only 字段，无正文回退：旧格式正文从未有这些字段的单行机器声明（review 文件的
# status/agent 从 v0.35 起就只读 frontmatter 块），正文散文提及不得被误读。A 组迁移前由
# check-gate.py 的 `_frontmatter_field`（sed 式行扫描）读取，迁移后统一走本 op（YAML 解析 +
# NO_FALLBACK 语义，行为对 well-formed frontmatter 等价）。
NO_FALLBACK_STRING_FIELDS = frozenset({
    "change_type", "ceremony", "status", "agent", "project_phase", "created",
})

# list 字段：frontmatter 值（YAML list）格式化为空格连接字符串。
# ui_ux_dimensions（TAG0006 P2 §2.15.1）：P1 维度选择可选字段，presence 语义（缺失=未声明）；
# 维度名单 token 无内嵌空格，空格连接即可区分元素。
LIST_FIELDS = frozenset({
    "phases", "packages", "domains",
    "coupling_checklist", "follows_existing_pattern", "ui_ux_dimensions",
})

# int 字段：格式化为 str(int)。
INT_FIELDS = frozenset({"candidate_count"})

# P6/P7 结构化计数字段（流 B，P2-design.md §3.2）：int 格式化同 INT_FIELDS，
# 但 frontmatter 无该字段时**不做正则回退**——直接输出空字符串（见模块 docstring
# "无正文回退语义"）。调用方据此判断走 frontmatter 汇总还是旧格式正文 grep 计数。
# TAG0022（RM-AG0038，C 批）：code_map_new_files_count / code_map_reviewed_count
# （P7-consistency.md CODE_MAP 配对计数）移入——解 check-gate.py L1098-1107 DESIGN_GAP
# 遗留（此前因 KNOWN_OPS 未注册无法经 _md_field_get 读取，改走本地 _frontmatter_field）。
# 与 P7 其他计数同语义：frontmatter 无该字段 → 空字符串（机制未采用 → 调用方跳过配对校验）。
# TAG0050 批 B（设计 §3.3）：`pass`/`fail` 在快照 files 节登记为 `writer: system` + `derive`；
# 对**非 legacy** 任务，本工具读取这两个键时按 derive 现算（忽略文件值，见 `_system_field_spec`）。
NO_FALLBACK_INT_FIELDS = frozenset({
    "pass", "fail",
    "blocker_count", "deviation_count", "deviation_critical_count",
    "design_gap_count", "design_gap_reviewed_count",
    "code_map_new_files_count", "code_map_reviewed_count",
})

# P1 流 C 标记"已解决/已确认"状态字段（P2-design.md §3.3.1）：list 字段，
# 但 frontmatter 无该字段时**不做正则回退**（同 NO_FALLBACK_INT_FIELDS 的理由——
# v0.35 正文里没有这些字段的单行声明形式）；格式化为换行连接（非空格连接，
# 元素是含空格的散文描述，见模块 docstring）。
# TAG0015（BDD-6/17，重试#1 A7 修复）：retrospective.md 是全新文档类型，无需兼容旧格式，
# 无正文回退，元素为散文描述，换行连接，与 need_confirm_resolved 等字段同语义。
NO_FALLBACK_LIST_FIELDS = frozenset({
    "need_confirm_resolved", "suggest_resolved", "scope_resolved",
    "mechanism_issues", "execution_issues",
})

# presence 语义的纯字符串字段：key 存在且值非 null → 输出值原样，否则空。
# 注意：change_type/ceremony 不在其中——它们走 NO_FALLBACK_STRING_FIELDS（frontmatter-only，
# 无正文回退，防散文误读）。
# ui_render_shape（TAG0006 P2 §2.15.1）：P1 渲染形态声明可选字段（规范值，开放集合），
# presence 语义——缺失 = 常规布局型默认，不做必填校验；正文回退供旧格式兼容。
STRING_FIELDS = frozenset({
    "override", "internal_only_reason", "跳过风险", "risk_level", "ui_render_shape",
})

# TAG0014（P2-design.md §3.1）：结构化 JSON 字段（dispatch_plan）。frontmatter dict/list
# 值格式化为 json.dumps（ensure_ascii=False 保持中文可读），无正文回退——防止正文散文里的
# `dispatch_plan:` 被误读（与 change_type/regression_pass 同语义，防伪造）。
JSON_FIELDS = frozenset({"dispatch_plan"})


def _read():
    with open(os.environ["FILE"], encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def _read_frontmatter(text):
    """只认文件头 --- 块；无块或解析失败返回 None（由校验器在 pre-commit 拦截坏格式）。"""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    try:
        return yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return None


def _format_value(value, field):
    if field in JSON_FIELDS:
        return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    if field in BOOL_FIELDS or field in NO_FALLBACK_BOOL_FIELDS:
        return str(value).lower()
    if field in LIST_FIELDS:
        if isinstance(value, list):
            return " ".join(str(v) for v in value)
        return str(value)
    if field in NO_FALLBACK_LIST_FIELDS:
        if isinstance(value, list):
            return "\n".join(str(v) for v in value)
        return str(value)
    if field in INT_FIELDS or field in NO_FALLBACK_INT_FIELDS:
        return str(value)
    return str(value)


def _regex_scalar(text, pattern):
    m = re.search(pattern, text)
    return m.group(1) if m else ""


def _regex_list(text, field):
    # 内联块式列表（[a, b, c]）
    m = re.search(re.escape(field) + r":\s*\[([^\]]+)\]", text)
    if m:
        items = [p.strip() for p in m.group(1).split(",") if p.strip()]
        return " ".join(items)
    # 块式列表（每行 "- item"）
    m = re.search(re.escape(field) + r":\s*\n((?:[ \t]+-[ \t]+\S+[ \t]*\n)+)", text)
    if m:
        items = re.findall(r"-\s+(\S+)", m.group(1))
        return " ".join(items)
    return ""


def _regex_fallback(text, op):
    if op == "risk_level":
        return _regex_scalar(text, r"risk_level:\s*(low|medium|high)")
    if op == "ui_affected":
        return _regex_scalar(text, r"ui_affected:\s*(true|false)")
    if op in LIST_FIELDS:
        return _regex_list(text, op)
    if op == "candidate_count":
        return _regex_scalar(text, r"candidate_count:\s*(\d+)")
    if op in ("internal_only", "design_trivial"):
        return _regex_scalar(text, re.escape(op) + r":\s*(true|false)")
    if op in ("override", "internal_only_reason", "跳过风险", "ui_render_shape"):
        m = re.search(re.escape(op) + r":\s*(.+)", text)
        if not m:
            return ""
        return m.group(1).strip().strip('"').strip("'")
    return ""


def _system_field_spec(op):
    """op 是否为本文件快照契约中的 `writer: system` 字段 → 返回其 spec（否则 None）。

    TAG0050 批 B（设计 §3.3）：仅**非 legacy** 任务（账本有创建/迁入事件）且快照可用时
    返回 spec；legacy / 快照不可用 → None（调用方回退文件值，保持旧行为）。
    """
    if agate_common is None or agate_schema is None:
        return None
    file_path = os.environ.get("FILE", "")
    if not file_path:
        return None
    basename = os.path.basename(file_path)
    try:
        task_dir = os.path.dirname(os.path.abspath(file_path))
        level = agate_common.task_level(task_dir, __file__)
        if level is None:
            return None  # legacy：不现算（设计 §3.3 只承诺非 legacy 任务）
        contract = agate_common.load_contract(level, __file__)
        files = contract.get("files") if isinstance(contract, dict) else None
        spec = files.get(basename) if isinstance(files, dict) else None
        fields = spec.get("fields") if isinstance(spec, dict) else None
        field = fields.get(op) if isinstance(fields, dict) else None
        if isinstance(field, dict) and field.get("writer") == "system":
            return field
    except Exception:
        return None
    return None


def _get(text, op):
    fm = _read_frontmatter(text)
    # TAG0050 批 B（设计 §3.3）：writer: system 字段（如 P6 pass/fail）按契约 `derive`
    # 现算，**忽略文件里的值**；消费方（check-gate / check-p6-provenance / agate-feedback）
    # 不改代码即生效。仅当字段存在于 frontmatter 且快照可用时现算——字段缺失保持
    # 既有「无声明 → 空串 → 调用方回退」语义，避免把「未写」误判为「现算 0」。
    if isinstance(fm, dict) and op in fm:
        spec = _system_field_spec(op)
        if spec is not None and spec.get("derive"):
            try:
                return str(agate_schema.derive(spec["derive"], fm))
            except Exception as e:  # 非法 derive 表达式等 → 降级用文件值并 WARNING
                sys.stderr.write(
                    f"agate-md-field-get: WARNING: {op} 的 derive 现算失败（{e}），降级用文件值\n"
                )
    # 字段级 presence 检测：frontmatter 是 dict 且 key 存在且值非 null → 取 frontmatter
    if isinstance(fm, dict) and op in fm and fm[op] is not None:
        return _format_value(fm[op], op)
    if op in (NO_FALLBACK_INT_FIELDS | NO_FALLBACK_LIST_FIELDS
              | NO_FALLBACK_BOOL_FIELDS | NO_FALLBACK_STRING_FIELDS
              | JSON_FIELDS):
        return ""  # 流 B/C/TAG0002 字段 + JSON 字段：无正文回退语义，frontmatter 无该字段直接输出空字符串
    return _regex_fallback(text, op)  # 字段不在 frontmatter → 正则回退


KNOWN_OPS = (
    BOOL_FIELDS | LIST_FIELDS | INT_FIELDS | STRING_FIELDS
    | NO_FALLBACK_INT_FIELDS | NO_FALLBACK_LIST_FIELDS | NO_FALLBACK_BOOL_FIELDS
    | NO_FALLBACK_STRING_FIELDS | JSON_FIELDS
)


def main():
    op = sys.argv[1]
    text = _read()
    if op not in KNOWN_OPS:
        sys.stderr.write(f"agate-md-field-get: unknown op {op}\n")
        sys.exit(2)
    print(_get(text, op))


if __name__ == "__main__":
    main()
