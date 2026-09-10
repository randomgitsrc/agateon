#!/usr/bin/env python3
"""check-events.py — 事件账本审计（TAG0020，P2-design §3.4）

CLI：check-events.py [TASK_DIR]（exit 0 = 审计通过 / exit 1 = 审计不通过）

审计链（任一违反 → exit 1）：
  1. gate-events.jsonl 缺失或空文件 → exit 0（合法态，BDD-7：历史任务/首次运行不误报）
  2. 逐行 JSON 可解析（坏行 → exit 1）
  3. 首行 prev_hash == GENESIS_HASH（不符 → exit 1）
  4. 逐行 prev_hash == sha256(上一行原始文本 UTF-8)（链断裂 → exit 1 = 历史行被改写检测）
  5. ts 单调不减（同格式 UTC ISO8601 微秒字符串字典序可比；违例 → exit 1）
  6. judge 复核轮次 = judge_verdict 事件按 verdict_hash 去重后计数 ≤ 2（同一 verdict
     重跑不增轮，真实复核才 +1；无 hash 旧事件各计 1——轮次预算机械兜底，BDD-8；超出 → exit 1）
  7. 未知 event 类型不拦截（向后兼容；gate_run/judge_verdict/state_transition/dispatch_route 为已知类型）
  8. dispatch_route 理由码枚举（TAG0034 / RM-AG0060）：event == "dispatch_route" 的行，
     每个 candidates_tried[i].reason（若存在）必须 ∈ {launch_fail, infra_error, no_parseable_output}；
     出现 gate_fail 或任何其它值 → exit 1（机械强制「gate 判定不触发换候选」的完整性不变量）

append-only 语义：哈希链 + ts 单调组合判定"仅允许行尾追加"——改写任何历史行 →
后续行 prev_hash 断裂；删除尾部无法由哈希链检测，由 ts 单调 + judge_verdict 计数部分兜底。
账本审计是 P6.5 gate 前置（BDD-7）；账本不要求特定事件必须存在（只校验存在内容的完整性）。

平台无关：纯文件文本解析（显式 encoding="utf-8"）；哈希链对原始文本（不含行尾
换行符）求 sha256，与 append_event / P3 测试同源约定。

Python 3.8+（禁 match / str.removeprefix）。
"""

import hashlib
import json
import os
import sys

# 与 append_event 同源取 GENESIS_HASH（P2 §3.2：首行 prev_hash 常量对齐 test_bdd_7）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agate_common import GENESIS_HASH

LEDGER_NAME = "gate-events.jsonl"

# BDD-8：judge 轮次预算机械兜底（轮次 ≤ 2，账本 judge_verdict 事件计数 ≤ 2）
MAX_JUDGE_VERDICT_EVENTS = 2

# TAG0034 第 8 条：dispatch_route 事件的合法回落理由码枚举（无 gate_fail 值——
# 机械强制「gate 判定不触发换候选」的完整性不变量，P2-design §3.8）。
DISPATCH_ROUTE_REASONS = {"launch_fail", "infra_error", "no_parseable_output"}


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-events.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    ledger_path = os.path.join(task_dir, LEDGER_NAME)

    # 1. 缺失或空文件 → 合法态（BDD-7）
    if not os.path.isfile(ledger_path):
        sys.stderr.write("GATE EVENTS: gate-events.jsonl 不存在（合法态，历史任务/首次运行跳过）\n")
        sys.exit(0)
    try:
        with open(ledger_path, encoding="utf-8", errors="replace") as f:
            raw_lines = f.read().splitlines()
    except OSError:
        raw_lines = []
    if not raw_lines or not any(line.strip() for line in raw_lines):
        sys.stderr.write("GATE EVENTS: gate-events.jsonl 为空（合法态）\n")
        sys.exit(0)

    # judge 轮次数 = verdict_hash 去重计数 + 无 hash 历史事件各计 1（CRITICAL-1 修复：
    # 同一 verdict 被 pre-commit/gate_p65/CI backstop 多次重跑 → 相同 verdict_hash 只计 1 轮；
    # 真实复核（verdict 内容变化 → 新 hash）才 +1。无 hash 的旧格式事件无去重键，各自计 1，向后兼容）
    judge_verdict_hashes = set()
    judge_verdict_legacy = 0
    prev_ts = None

    for idx, raw in enumerate(raw_lines, start=1):
        # 2. 逐行 JSON 可解析
        try:
            ev = json.loads(raw)
        except Exception:
            sys.stderr.write(f"GATE EVENTS: 第 {idx} 行非合法 JSON\n")
            sys.exit(1)
        if not isinstance(ev, dict):
            sys.stderr.write(f"GATE EVENTS: 第 {idx} 行不是 JSON 对象\n")
            sys.exit(1)

        # 3. 首行 prev_hash == GENESIS_HASH
        if idx == 1:
            if ev.get("prev_hash") != GENESIS_HASH:
                sys.stderr.write(
                    "GATE EVENTS: 首行 prev_hash != GENESIS_HASH（账本起始行被改写或伪造）\n")
                sys.exit(1)
        else:
            # 4. 逐行 prev_hash == sha256(上一行原始文本)
            expected = hashlib.sha256(raw_lines[idx - 2].encode("utf-8")).hexdigest()
            if ev.get("prev_hash") != expected:
                sys.stderr.write(
                    f"GATE EVENTS: 第 {idx} 行 prev_hash 与上一行原始文本不匹配（历史行被改写检测）\n")
                sys.exit(1)

        # 5. ts 单调不减（同格式微秒时间戳，字符串字典序可比）
        ts = ev.get("ts")
        if not isinstance(ts, str) or not ts:
            sys.stderr.write(f"GATE EVENTS: 第 {idx} 行缺 ts 字段或非字符串\n")
            sys.exit(1)
        if prev_ts is not None and ts < prev_ts:
            sys.stderr.write(
                f"GATE EVENTS: 第 {idx} 行 ts({ts}) < 上一行 ts({prev_ts})——时间戳单调违反（仅允许行尾追加）\n")
            sys.exit(1)
        prev_ts = ts

        # 6. judge_verdict 轮次计数（BDD-8 预算兜底；verdict_hash 去重，CRITICAL-1）
        if ev.get("event") == "judge_verdict":
            vh = ev.get("verdict_hash")
            if isinstance(vh, str) and vh:
                judge_verdict_hashes.add(vh)
            else:
                judge_verdict_legacy += 1

        # 8. dispatch_route 理由码枚举校验（TAG0034 / RM-AG0060）——不动第 1-7 条
        if ev.get("event") == "dispatch_route":
            tried = ev.get("candidates_tried")
            if isinstance(tried, list):
                for cand in tried:
                    if not isinstance(cand, dict):
                        continue
                    reason = cand.get("reason")
                    if reason is not None and reason not in DISPATCH_ROUTE_REASONS:
                        sys.stderr.write(
                            f"GATE EVENTS: 第 {idx} 行 dispatch_route 事件 candidates_tried "
                            f"理由码 {reason!r} 非法（合法值仅 "
                            f"{sorted(DISPATCH_ROUTE_REASONS)}——gate_fail 等值机械拒绝，"
                            "gate 判定不触发换候选）\n"
                        )
                        sys.exit(1)

    judge_verdict_count = len(judge_verdict_hashes) + judge_verdict_legacy
    if judge_verdict_count > MAX_JUDGE_VERDICT_EVENTS:
        sys.stderr.write(
            f"GATE EVENTS: judge 复核轮次 {judge_verdict_count} > {MAX_JUDGE_VERDICT_EVENTS}（verdict_hash 去重后计）——judge 轮次预算超限，须人工接管\n")
        sys.exit(1)

    # 7. 未知 event 类型不拦截（向后兼容）
    sys.stderr.write(
        f"GATE EVENTS: 账本审计通过（{len(raw_lines)} 行，哈希链完整，ts 单调，judge 轮次×{judge_verdict_count}）\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
