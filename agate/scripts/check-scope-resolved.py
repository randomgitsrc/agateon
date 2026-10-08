#!/usr/bin/env python3
"""check-scope-resolved.py — SCOPE+ 处理追踪（P2.11）

从 check-scope-resolved.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
检查产出含 [SCOPE+] 时，P1-requirements.md 有对应 [SCOPE_RESOLVED] 标记
exit 0 = 通过; exit 1 = SCOPE+ 未处理; exit 2 = 无 task 目录。

判据形态（2026-10-01 放宽，RM-AG0077⑦ 遗留项）：[SCOPE+] 的**行首声明**按下述形态识别——
裸 `[SCOPE+]` / 列表符 `- [SCOPE+]` / 粗体 `**[SCOPE+]**` / 引用块 `> [SCOPE+]`。
反引号包裹与行中出现视为「提及」，不触发校验（保守边界，理由见下方常量注释）。
"""

import glob
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# 形态判据**单源**（设计 docs/design-notes/design-marker-single-source.md）：
# 取值自 rules/markers.yaml，本脚本**不再自带正则副本**（由 mk_1 机械守护）。
#
# 历史背景（RM-AG0077⑦，2026-10-01 PR #387）：原为 `^\s*-?\s*\[SCOPE\+\]`，粗体
# `**[SCOPE+]**`（TPV0099 实写）与引用块 `> [SCOPE+]` 均不命中 ⇒ scope_found 空 ⇒ 静默早退，
# SCOPE_RESOLVED 校验被跳过。已放宽为「列表符/引用块/粗体」。
#
# 刻意保留的未覆盖面（单源后见 markers.yaml::exclude 的注释，代价已量化登记）：
#   行首反引号（纳入 +5 转红，含 TAG0004 真声明）／标题形态（+4）／行中出现（+24）。
import agate_markers  # noqa: E402 — 同目录单源库

SCOPE_PLUS_RE = agate_markers.pattern("SCOPE+")
# SCOPE_RESOLVED 侧**必须与 SCOPE+ 同步放宽**（RM-AG0077⑦ 的核心教训）：只放宽 SCOPE+ 一侧会让
# 「有 SCOPE+ 但标记写法不匹配」的任务**假红**——TAG0021 正是此形态（其 SCOPE_RESOLVED 用
# 反引号包裹）。差异已**在注册表内**以 `accept_backtick: true` 字段表达（而非本处特例判断）。
SCOPE_RESOLVED_RE = agate_markers.pattern("SCOPE_RESOLVED")
SKIP_NAME_RE = re.compile(r"dispatch-context|dispatch-prompt|progress")
AGATE_CARD_RE = re.compile(r"<!-- AGATE_CARD_START -->.*?<!-- AGATE_CARD_END -->", re.DOTALL)


def _strip_agate_card(text):
    """移除 AGATE_CARD 嵌入块（等价 sh 的 sed '/START/,/END/d'，卡片模板文本含字面
    SCOPE+ 会触发误报）。"""
    return AGATE_CARD_RE.sub("", text)


def _scan_scope_plus(task_dir):
    """扫描所有顶层 .md 文件找行首 [SCOPE+]（M2 修复：SCOPE+ 可能出现在非 P 前缀文件）。
    返回命中文件 basename 空格连接串（含尾空格，与 sh 版 SCOPE_FOUND 语义一致）。"""
    found = ""
    for f in sorted(glob.glob(os.path.join(task_dir, "*.md"))):
        name = os.path.basename(f)
        if SKIP_NAME_RE.search(name):
            continue
        with open(f, encoding="utf-8") as fh:
            text = fh.read().replace("\r\n", "\n")
        if SCOPE_PLUS_RE.search(_strip_agate_card(text)):
            found += name + " "
    return found


def _scope_resolved_frontmatter(p1_file):
    """读 P1 frontmatter 结构化 scope_resolved（等价 sh 的 FILE=... agate-md-field-get.py
    scope_resolved 2>/dev/null || echo ""）。"""
    env = dict(os.environ)
    env["FILE"] = p1_file
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-md-field-get.py"), "scope_resolved"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    # sh 命令替换剥掉尾部换行（agate-md-field-get 输出空结果时 print 仍打 \n，
    # sh 版 $(...) 收尾后为空串 → 落到正文回退判定）。等价：剥尾后判空。
    return (proc.stdout or "").rstrip("\n")


def _count_resolved_body(p1_file):
    """正文 [SCOPE_RESOLVED] 散文标记计数（等价 sh 的 grep -cE + tail -1，处理 "0\n0"）。"""
    with open(p1_file, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    return len(SCOPE_RESOLVED_RE.findall(text))


def _aggregate_declaration_ids(task_dir, field):
    """跨声明文件聚合 `field` 的 id 集合（TAG0050 批 E）。

    返回 `(is_non_legacy, {id…})`。legacy 任务返回 `(False, set())`（调用方走正文路径）。
    """
    try:
        import agate_common
    except ImportError:
        return False, set()
    try:
        level = agate_common.task_level(task_dir, __file__)
    except Exception:
        return False, set()
    if level is None:
        return False, set()
    try:
        contract = agate_common.load_contract(level, __file__) or {}
        # GAP-8 闭合（2026-10-08）：聚合面回归设计 §6 的 `declaration_files`（单源）。
        globs = contract.get("declaration_files") or []
    except Exception:
        globs = []
    ids = set()
    for path in agate_common.declaration_file_paths(task_dir, globs):
        try:
            with open(path, encoding="utf-8") as fh:
                fm, _body = agate_common.split_frontmatter(fh.read())
        except OSError:
            continue
        if not isinstance(fm, dict) or not isinstance(fm.get(field), list):
            continue
        for item in fm[field]:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return True, ids


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-scope-resolved.py TASK_DIR\n")
        sys.exit(1)
    task_dir = args[0]

    if not os.path.isdir(task_dir):
        sys.exit(2)

    # TAG0050 批 E（设计 §6）：非 legacy 任务读**聚合结果**（结构化 scope_plus/scope_resolved）。
    is_non_legacy, sp_ids = _aggregate_declaration_ids(task_dir, "scope_plus")
    if is_non_legacy:
        _unused, sr_ids = _aggregate_declaration_ids(task_dir, "scope_resolved")
        dangling = sp_ids - sr_ids
        if dangling:
            sys.stderr.write(
                f"GATE SCOPE: 结构化 scope_plus 悬空 id 未被 scope_resolved 覆盖：{sorted(dangling)}\n"
            )
            sys.exit(1)
        sys.stderr.write("GATE SCOPE: 结构化 scope_plus/scope_resolved 集合一致\n")
        sys.exit(0)

    p1_file = os.path.join(task_dir, "P1-requirements.md")

    scope_found = _scan_scope_plus(task_dir)
    if not scope_found:
        sys.stderr.write(
            "GATE SKIP: check-scope-resolved: 未检出 [SCOPE+] 行首声明"
            "（裸 / 列表符 / 粗体 / 引用块形态），SCOPE_RESOLVED 校验未执行\n"
        )
        sys.exit(0)

    if not os.path.isfile(p1_file):
        sys.stderr.write(
            f"GATE SCOPE: 产出含 [SCOPE+]（{scope_found}），但无 P1-requirements.md\n"
        )
        sys.exit(1)

    # v2.0 T001 流 C（BDD-22）：优先读 P1 frontmatter 结构化 scope_resolved 列表——
    # 非空列表即已解决 → 直接通过。
    scope_resolved_fm = _scope_resolved_frontmatter(p1_file)
    if scope_resolved_fm:
        count = len([ln for ln in scope_resolved_fm.splitlines() if ln.strip()])
        sys.stderr.write(
            f"GATE SCOPE: {scope_found}有 [SCOPE+]，P1 frontmatter scope_resolved 非空（{count} 项已解决）\n"
        )
        sys.exit(0)

    resolved_count = _count_resolved_body(p1_file)
    if resolved_count == 0:
        sys.stderr.write(
            f"GATE SCOPE: 产出含 [SCOPE+]（{scope_found}），但 P1 无 [SCOPE_RESOLVED] 标记\n"
        )
        sys.exit(1)

    sys.stderr.write(
        f"GATE SCOPE: {scope_found}有 [SCOPE+]，P1 有 {resolved_count} 个 [SCOPE_RESOLVED]\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
