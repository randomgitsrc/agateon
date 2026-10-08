#!/usr/bin/env python3
"""check-retrospective.py — 复盘异常触发（P2.12）

从 check-retrospective.sh 迁移（TAG0010 批次 2a）。CLI 契约与 sh 版等价：
检测异常模式（gate 重试超限 / SCOPE+ / 裁剪 override），输出复盘提醒到 stderr
（不中止 commit）。exit 0 = 总是通过（只提醒不拦截）。

迁移说明：sh 的 STATE_FILE=... agate-state-get.py retries_over 子进程 →
sys.executable subprocess（$(...) 剥尾换行 → .rstrip("\n")）；sed 剥离 AGATE_CARD
块 + grep 行首 SCOPE+ → 正则等价；grep '^override:' → re.MULTILINE 等价。
"""

import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
AGATE_STATE_GET = os.path.join(SCRIPT_DIR, "agate-state-get.py")
MAX_RETRY_MAP = "P1:3,P2:3,P3:2,P4:3,P5:2,P6:2,P7:2,P8:2"
# 形态判据**单源**（设计 docs/design-notes/design-marker-single-source.md）：
# 与 check-scope-resolved.py **共用同一取值**，本脚本不再自持正则副本。
# 历史（2026-10-01 PR #387）：两处曾各自持有语义等价但源码不同的字面量，靠
# test_sc_14 对 14 个探针做行为等价守护；单源后该分叉**结构上不可能**再发生。
import agate_markers  # noqa: E402 — 同目录单源库

SCOPE_PLUS_RE = agate_markers.pattern("SCOPE+")
SKIP_NAME_RE = re.compile(r"dispatch-context|dispatch-prompt|progress")
AGATE_CARD_RE = re.compile(r"<!-- AGATE_CARD_START -->.*?<!-- AGATE_CARD_END -->", re.DOTALL)
OVERRIDE_RE = re.compile(r"^override:", re.MULTILINE)


def _retries_over(state_file):
    """调 agate-state-get.py retries_over（等价 sh 的 STATE_FILE=... agate-state-get.py
    retries_over 'P1:3,...' 2>/dev/null || echo ""；$(...) 剥尾换行 → .rstrip("\n")）。"""
    env = dict(os.environ)
    env["STATE_FILE"] = state_file
    try:
        proc = subprocess.run(
            [sys.executable, AGATE_STATE_GET, "retries_over", MAX_RETRY_MAP],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


DEBT_TASK_ID_RE_TEMPLATE = r'task_id:\s*"?{}"?\s*$'
ROADMAP_TASK_ID_RE_TEMPLATE = r'\|\s*{}\s*\|'


def _task_id(state_file):
    """调 agate-state-get.py task_id（同 _retries_over 的 subprocess 模式）。"""
    env = dict(os.environ)
    env["STATE_FILE"] = state_file
    try:
        proc = subprocess.run(
            [sys.executable, AGATE_STATE_GET, "task_id"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def _scan_debt_roadmap_signal(task_dir, state_file):
    """BDD-10：检测 DEBT/roadmap 登记信号（机制缺口检测代理），命中返回 tid，否则返回 ""。"""
    if not os.path.isfile(state_file):
        return ""
    tid = _task_id(state_file)
    if not tid:
        return ""

    workspace = os.path.dirname(os.path.dirname(os.path.abspath(task_dir.rstrip(os.sep))))
    debt_file = os.path.join(workspace, "debt", "tech-debt.md")
    roadmap_file = os.path.join(workspace, "roadmap", "roadmap.md")

    if os.path.isfile(debt_file):
        with open(debt_file, encoding="utf-8") as f:
            text = f.read()
        if re.search(DEBT_TASK_ID_RE_TEMPLATE.format(re.escape(tid)), text, re.MULTILINE):
            return tid

    if os.path.isfile(roadmap_file):
        with open(roadmap_file, encoding="utf-8") as f:
            text = f.read()
        if re.search(ROADMAP_TASK_ID_RE_TEMPLATE.format(re.escape(tid)), text):
            return tid

    return ""


def _scan_scope_plus(task_dir):
    """扫描顶层 *.md 找行首 [SCOPE+]（排除 dispatch-context/dispatch-prompt/progress 文件
    + 剥离 AGATE_CARD 块，同 sh sed 删除 + grep -qE）。返回首个命中文件 basename 或空串。

    覆盖形态：裸 / 列表符 / 引用块 / 粗体（2026-10-01 起）。**不覆盖**标题形态、行首反引号、
    行中出现——未覆盖面与量化代价见 `check-scope-resolved.py` 顶部常量注释（两处判据必须等价）。"""
    for name in sorted(os.listdir(task_dir)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(task_dir, name)
        if not os.path.isfile(path):
            continue
        if SKIP_NAME_RE.search(name):
            continue
        with open(path, encoding="utf-8") as f:
            text = AGATE_CARD_RE.sub("", f.read())
        if SCOPE_PLUS_RE.search(text):
            return name
    return ""


def _aggregate_scope_plus_ids(task_dir):
    """TAG0050 批 E：非 legacy 任务读**聚合结果**（结构化 scope_plus id 集合）。

    返回 (is_non_legacy, {id…})；legacy → (False, set())。
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
        if not isinstance(fm, dict) or not isinstance(fm.get("scope_plus"), list):
            continue
        for item in fm["scope_plus"]:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return True, ids


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-retrospective.py TASK_DIR\n")
        sys.exit(1)
    task_dir = args[0]
    state_file = args[1] if len(args) > 1 else ".state.yaml"

    warnings = []

    if os.path.isfile(state_file):
        over = _retries_over(state_file)
        if over:
            warnings.append(f"gate 重试超限（{over}）")

    if os.path.isdir(task_dir):
        hit = _scan_scope_plus(task_dir)
        if hit:
            warnings.append(f"SCOPE+ 触发（{hit}）")
        # TAG0050 批 E：非 legacy 任务读**聚合结果**（结构化 scope_plus）。
        _is_non_legacy, _sp_ids = _aggregate_scope_plus_ids(task_dir)
        if _is_non_legacy and _sp_ids:
            warnings.append(f"SCOPE+ 触发（结构化：{', '.join(sorted(_sp_ids))}）")

    p1_file = os.path.join(task_dir, "P1-requirements.md")
    if os.path.isdir(task_dir) and os.path.isfile(p1_file):
        with open(p1_file, encoding="utf-8") as f:
            if OVERRIDE_RE.search(f.read()):
                warnings.append("裁剪声明与执行不一致（override 触发）")

    if warnings:
        sys.stderr.write("GATE RETRO: 建议复盘 — 检测到异常模式：\n")
        for w in warnings:
            sys.stderr.write(f"  - {w}\n")
        sys.stderr.write("  请在版本 bump 前写简版复盘（tasks/{Txxx}/retrospective.md）\n")
        sys.stderr.write("  复盘发现的新缺口请登记 DEBT/roadmap（技术债清单 / 路线图）\n")

    if os.path.isdir(task_dir):
        debt_roadmap_tid = _scan_debt_roadmap_signal(task_dir, state_file)
        if debt_roadmap_tid:
            sys.stderr.write("GATE RETRO: 建议复盘 — 发现机制缺口信号：\n")
            sys.stderr.write(
                f"  - {debt_roadmap_tid} 关联的 DEBT/roadmap 条目已登记（可能存在机制缺口，建议复盘归因）\n"
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
