#!/usr/bin/env python3
"""agate-debt-check.py — tech-debt.md 多条目 schema 校验 + 回退覆盖哈希提取（TAG0001 D2/D3）。

两种模式（由 check-debt.sh 薄壳调用）：
  1. 默认（FILE env）：tech-debt.md 逐条目 schema 校验。错误行输出到 stdout
     （格式 `{basename}:{entry_id}: {msg}`，无 id 用块序号）；无错误输出空。
  2. --covered-hashes FILE：输出 FILE 中所有 `source: retreat` 条目 evidence 里出现的
     hex token（7-40 位 [0-9a-f]），去重后每行一个（回退覆盖比对数据集）。

解析契约（P2-design.md §2.1）：
  - 提取所有 ```yaml fenced 块（正则同 check-protocol-consistency.py 的 extract_code_blocks）
  - 每个块 yaml.safe_load；结果非 dict → 报错"条目 {i} 的 YAML 块必须为 key: value 映射"
  - 无任何 yaml 块 → no-op（BDD-10 向后兼容）

schema 校验规则（P2-design.md §2.2）：
  - 必填：id/category/title/status/priority/evidence(非空 list；元素为 {path/ref, note} 映射)/impact/recommendation/
    closure_criteria(非空 list)/source/created_at
  - 枚举：category=technical|management|protocol；status=open|in_progress|closed；
    priority=high|medium|low；source=retreat|review|retrospective
  - 类型：task_id 允许 null 或 str；evidence/closure_criteria 须为 list；created_at 及
    上述 str 字段须为 str
  - closed 准入（BDD-8）：status==closed → task_id 非空 + evidence 序列化文本同时包含
    task_id 与 P5/P6 标记
  - id 唯一性：同文件内重复 id → 拦截
"""

import datetime
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-debt-check: 需要 pyyaml\n")
    sys.exit(1)


BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.S)
HEX_RE = re.compile(r"[0-9a-f]{7,40}")

REQUIRED = (
    "id", "category", "title", "status", "priority", "evidence",
    "impact", "recommendation", "closure_criteria", "source", "created_at",
)
ENUMS = {
    "category": ("technical", "management", "protocol"),
    "status": ("open", "in_progress", "closed"),
    "priority": ("high", "medium", "low"),
    "source": ("retreat", "review", "retrospective"),
}
STR_FIELDS = (
    "id", "category", "title", "status", "priority", "impact",
    "recommendation", "source", "created_at",
)
LIST_FIELDS = ("evidence", "closure_criteria")


def extract_yaml_blocks(text):
    """提取所有 ```yaml fenced 块内容。"""
    return BLOCK_RE.findall(text)


def serialize_evidence(evidence):
    """把 evidence 列表序列化为纯文本（拼接所有 path/note/ref 值）。

    YAML int 边界：全数字标量（如 7 位 hex 哈希 7008516）被 safe_load 解析为 int，
    需归一为 str 保持字符串语义，否则 round-trip 丢弃该哈希。
    """
    parts = []
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                for k in ("path", "note", "ref"):
                    v = item.get(k)
                    if isinstance(v, str):
                        parts.append(v)
                    elif isinstance(v, int) and not isinstance(v, bool):
                        parts.append(str(v))
            elif isinstance(item, str):
                parts.append(item)
            elif isinstance(item, int) and not isinstance(item, bool):
                parts.append(str(item))
    return " ".join(parts)


def check_entry(basename, eid, data, errors):
    """逐条目校验，错误行追加到 errors。"""
    for f in REQUIRED:
        if f not in data or data[f] is None:
            errors.append(f"{basename}:{eid}: 缺必填字段 {f}")

    for f, allowed in ENUMS.items():
        if f in data and data[f] is not None and data[f] not in allowed:
            errors.append("{}:{}: 非法值 {!r}（{} 合法值: {}）".format(
                basename, eid, f, data[f], ", ".join(allowed)))

    for f in STR_FIELDS:
        if f in data and data[f] is not None and not isinstance(data[f], str):
            # created_at 允许 yaml.safe_load 解析出的 date/datetime（如 2026-08-12 未加引号）
            if f == "created_at" and isinstance(data[f], (datetime.date, datetime.datetime)):
                continue
            errors.append(f"{basename}:{eid}: 类型错误（{f} 应为 str，实际 {type(data[f]).__name__}）")

    for f in LIST_FIELDS:
        if f in data and data[f] is not None:
            if not isinstance(data[f], list):
                errors.append(f"{basename}:{eid}: 类型错误（{f} 应为 list，实际 {type(data[f]).__name__}）")
            elif not data[f]:
                errors.append(f"{basename}:{eid}: {f} 不能为空")
            else:
                # 元素类型校验（2026-09-21 补）：只看"是 list"会放过**挂错清单**的条目
                # ——实测一条 DEBT 的 closure_criteria 里混进了 evidence 形态的
                # `{path, note}` 字典而校验通过（"决策已记录"的证据没进 evidence）。
                # evidence 元素须为 {path/ref, note} 映射；closure_criteria 元素须为字符串。
                want = dict if f == "evidence" else str
                wrong = [type(e).__name__ for e in data[f] if not isinstance(e, want)]
                if wrong:
                    errors.append(
                        f"{basename}:{eid}: {f} 元素类型错误"
                        f"（应为 {want.__name__}，实际含 {sorted(set(wrong))}）"
                        f"——evidence 放 {{path/ref, note}} 映射、closure_criteria 放字符串，勿混挂"
                    )
                elif f == "evidence":
                    # 键要求（2026-09-21 补，**最小收紧**）：上文文案把 evidence 描述为
                    # 「{{path/ref, note}}」，而实现只校验"是 dict"——实测 `evidence: [{{}}]`
                    # 可 rc=0 放行（**零信息量**证据）。此处只拒绝空/无已知键的条目；
                    # 不改动既有可接受形态（如只有 `note` 的历史回填条目——
                    # BDD-11「T001 回填」夹具即含此形态，收紧到"必须含 path/ref"会破坏它）。
                    known = ("path", "ref", "note")
                    for i, e in enumerate(data[f]):
                        if not any(k in e for k in known):
                            errors.append(
                                f"{basename}:{eid}: evidence[{i}] 为空或无已知键"
                                f"（期望 {{path/ref, note}}，至少含其一）"
                            )

    task_id = data.get("task_id")
    if task_id is not None and not isinstance(task_id, str):
        errors.append(f"{basename}:{eid}: 类型错误（task_id 应为 str 或 null，实际 {type(task_id).__name__}）")

    if data.get("status") == "closed":
        if not task_id:
            errors.append(f"{basename}:{eid}: closed 条目必须含 task_id")
        else:
            ev = serialize_evidence(data.get("evidence"))
            if task_id not in ev or not re.search(r"P[56]", ev):
                errors.append(f"{basename}:{eid}: closed 条目 evidence 须引用 task_id 与 P5/P6 证据")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--covered-hashes":
        path = args[1] if len(args) > 1 else ""
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            return  # 文件不存在/不可读 → 空覆盖集合
        tokens = set()
        for block in extract_yaml_blocks(text):
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue
            if data.get("source") != "retreat":
                continue
            tokens.update(HEX_RE.findall(serialize_evidence(data.get("evidence"))))
        for t in sorted(tokens):
            print(t)
        return

    file_path = os.environ.get("FILE", "")
    if not file_path:
        sys.stderr.write("agate-debt-check: 需要 FILE 环境变量\n")
        sys.exit(1)
    basename = os.path.basename(file_path)
    try:
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return  # 文件不存在 → no-op（check-debt.sh 已先处理，双保险）
    except Exception as e:
        print(f"{basename}: 读取失败（{e}）")
        return

    blocks = extract_yaml_blocks(text)
    if not blocks:
        return  # 无 yaml 块 → no-op（BDD-10 旧格式纯正文）

    errors = []
    seen_ids = set()
    for i, block in enumerate(blocks, 1):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
            first = str(e).splitlines()[0] if str(e) else "yaml 解析失败"
            errors.append(f"{basename}: 条目{i}: YAML 解析失败（{first[:100]}）")
            continue
        if data is None:
            continue  # 空块 → 跳过
        if not isinstance(data, dict):
            errors.append(f"{basename}: 条目{i} 的 YAML 块必须为 key: value 映射（当前解析为 {type(data).__name__}）")
            continue
        eid = data.get("id") if isinstance(data.get("id"), str) else f"条目{i}"
        if eid in seen_ids:
            errors.append(f"{basename}:{eid}: id 重复（登记簿 id 必须唯一）")
        seen_ids.add(eid)
        check_entry(basename, eid, data, errors)

    if errors:
        print("\n".join(errors))


if __name__ == "__main__":
    main()
