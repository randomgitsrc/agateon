#!/usr/bin/env python3
"""agate-dispatch-cost.py — 派发成本度量（RM-AG0074 的前置：无度量则无法发现退化）

用法：
    python3 agate/scripts/agate-dispatch-cost.py TASK_DIR [--json]

为何存在（2026-09-29 实证）：主 Agent 曾在 roadmap 写下「60%（251KB）是 AGATE_CARD 重复注入」，
实测为 **36%（245KB），其中纯重复 27%（182KB）**——**错诊断会驱动错配的方案**。根因是
**手抄数字、无人能复核**。本工具把「派发成本」变成可量测，使此后效率声称可被脚本复核。
基线（TPV0099）：26 份 / 678 KiB，rev 重发 10 份（42% 字节），卡片 36%、纯重复 27%。

设计原则（两条都由实测驱动，勿随手改）：
  1. **只测可测的**——`*dispatch-context*.md` 是客观产物，计数与字节可信。
  2. **拒绝编造**——阶段耗时**不可靠可算**：`.state.yaml` 的 `history` 实测只有 7 条、
     缺 P3/P4/P5/P6/P7（TPV0099）。故当 `history` 的 `completed` 条目**未覆盖**任务实际出现的
     阶段时，本工具报 `duration_available: false` 且**不给数值**——把不可判定伪装成可判定
     （TAG0030 教训）比不给答案更糟。

度量口径（三项，均为**可避免的重复**，是与"新增信息"相对的成本）：
  * `rev_*`      —— `-revN` 修订**整份重发**。它比卡片重复更贵：任一修订触发整面板重派，
                    而重发 = **多跑一次完整生成**（时间构成 generation 67% / 上下文仅影响 TTFT 22%）。
  * `card_*`     —— AGATE_CARD 注入总量，及其中的**纯重复**（同一张卡第 2..N 次，纯浪费）。
  * `duration_*` —— 阶段耗时，**仅在账本覆盖完整时**给出。

退出码：0 = 成功；2 = 用法错误 / 目标不是任务目录（**不静默报 0 份**——那会被读成"没问题"）。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CARD_RE = re.compile(r"<!-- AGATE_CARD_START -->(.*?)<!-- AGATE_CARD_END -->", re.S)
REV_RE = re.compile(r"-rev\d+\.md$")
CONTEXT_RE = re.compile(r"dispatch-context.*\.md$")
# 阶段产物形如 P1-requirements.md / P6-evidence/ ...；取 P<N> 前缀。
# **P6.5 须显式支持**：它在 "P6" 之后是 `.` 不是 `-`，用 `^P(\d+)-` 会**永不匹配**并被静默忽略。
# 协议上 P6.5 **不是独立 phase 值**（`P6-acceptance.md`：「phase 保持 P6」），故**映射到 P6**——
# 显式表达，而不是靠"恰好不匹配"实现（那是偶然正确：若某任务只留 P6.5 产物而无 P6-* 产物，
# P6 就会漏检，判据即失真）。独立评审 2026-09-29 发现此盲点。
PHASE_FILE_RE = re.compile(r"^P(\d+)(?:\.5)?-")
PHASE_CTX_RE = re.compile(r"^P(\d+)(?:\.5)?-dispatch-context")


def find_contexts(task_dir: Path) -> list[Path]:
    return sorted(p for p in task_dir.glob("*.md") if CONTEXT_RE.search(p.name))


def measure_cards(files: list[Path]) -> tuple[int, int]:
    """返回 (卡片总字节, **纯重复**字节)。

    纯重复 = 同一卡片内容在第 2..N 次注入上的字节（按块内容 sha 分组，计 (n-1) 次）。
    """
    import hashlib

    groups: dict[str, list[int]] = {}
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in CARD_RE.finditer(text):
            block = m.group(0)
            total += len(block)
            key = hashlib.sha256(m.group(1).strip().encode("utf-8")).hexdigest()
            groups.setdefault(key, []).append(len(block))
    dup = sum(sum(sizes[1:]) for sizes in groups.values())
    return total, dup


def _observed_phases(task_dir: Path) -> set[str]:
    """任务实际出现过的阶段号（由产物文件名与派发上下文名推断）。"""
    out: set[str] = set()
    for p in task_dir.iterdir():
        m = PHASE_FILE_RE.match(p.name) or PHASE_CTX_RE.match(p.name)
        if m:
            out.add(f"P{int(m.group(1))}")
    return out


def measure_duration(task_dir: Path) -> dict:
    """阶段耗时——**仅在账本覆盖完整时**给出；否则明说不可算。"""
    state = task_dir / ".state.yaml"
    if not state.is_file():
        return {"duration_available": False, "duration_seconds": None,
                "duration_reason": "无 .state.yaml"}
    try:
        import yaml

        data = yaml.safe_load(state.read_text(encoding="utf-8"))
    except Exception as exc:  # 解析失败 → 不可算（不猜）
        return {"duration_available": False, "duration_seconds": None,
                "duration_reason": f".state.yaml 解析失败: {type(exc).__name__}"}
    if not isinstance(data, dict):
        return {"duration_available": False, "duration_seconds": None,
                "duration_reason": ".state.yaml 顶层非映射"}

    history = data.get("history") or []
    # P0 特殊：账本对它记的是 `created` / `pending-start`（阶段起点），**从不**记 `completed`
    # ⇒ 若只认 completed，P0 永远"缺"、`duration_available` 永远为 false（工具形同虚设）。
    # 故 P0 接受**任意** history 条目即视为覆盖。
    completed = {
        str(h.get("phase"))
        for h in history
        if isinstance(h, dict) and h.get("action") == "completed" and h.get("phase")
    }
    seen_any = {
        str(h.get("phase"))
        for h in history
        if isinstance(h, dict) and h.get("phase")
    }
    covered = completed | {"P0"} if "P0" in seen_any else completed
    observed = _observed_phases(task_dir)
    missing = sorted(observed - covered)
    if missing:
        return {
            "duration_available": False,
            "duration_seconds": None,
            "duration_reason": (
                "history 的 completed 条目未覆盖任务出现的阶段（缺 "
                + "/".join(missing)
                + f"，共 {len(history)} 条 history）⇒ 耗时不可算，不给数值"
            ),
        }
    stamps = sorted(
        str(h.get("ts")) for h in history
        if isinstance(h, dict) and h.get("ts")
    )
    if len(stamps) < 2:
        return {"duration_available": False, "duration_seconds": None,
                "duration_reason": "history 时间戳不足 2 条"}
    from datetime import datetime

    def _parse(s: str):
        s = s.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    parsed = [_parse(s) for s in stamps]
    parsed = [d for d in parsed if d is not None]
    if len(parsed) < 2:
        return {"duration_available": False, "duration_seconds": None,
                "duration_reason": "时间戳格式无法解析"}
    return {
        "duration_available": True,
        "duration_seconds": int((max(parsed) - min(parsed)).total_seconds()),
        "duration_reason": "",
    }


def measure(task_dir: Path) -> dict:
    files = find_contexts(task_dir)
    total = sum(f.stat().st_size for f in files)
    rev = [f for f in files if REV_RE.search(f.name)]
    rev_bytes = sum(f.stat().st_size for f in rev)
    card_bytes, card_dup = measure_cards(files)
    return {
        "task_dir": str(task_dir),
        "contexts": len(files),
        "total_bytes": total,
        "rev_contexts": len(rev),
        "rev_bytes": rev_bytes,
        "rev_ratio": (rev_bytes / total) if total else 0.0,
        "card_bytes": card_bytes,
        "card_ratio": (card_bytes / total) if total else 0.0,
        "card_duplicate_bytes": card_dup,
        "card_duplicate_ratio": (card_dup / total) if total else 0.0,
        **measure_duration(task_dir),
    }


def _human(m: dict) -> str:
    lines = [
        f"派发成本：{m['task_dir']}",
        f"  派发上下文    {m['contexts']} 份 / {m['total_bytes']} B "
        f"({m['total_bytes'] / 1024:.0f} KiB)",
        f"  rev 修订重发  {m['rev_contexts']} 份 / {m['rev_bytes']} B "
        f"= {100 * m['rev_ratio']:.0f}%   ← 可避免（整份重发）",
        f"  卡片注入      {m['card_bytes']} B = {100 * m['card_ratio']:.0f}%",
        f"  其中纯重复    {m['card_duplicate_bytes']} B = "
        f"{100 * m['card_duplicate_ratio']:.0f}%   ← 可避免（同卡第 2..N 次）",
    ]
    if m["duration_available"]:
        lines.append(f"  阶段耗时      {m['duration_seconds']} s")
    else:
        lines.append(f"  阶段耗时      不可算（{m['duration_reason']}）")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if not args or args[0] in ("-h", "--help"):
        sys.stderr.write("用法: agate-dispatch-cost.py TASK_DIR [--json]\n")
        return 2
    task_dir = Path(args[0])
    if not task_dir.is_dir():
        sys.stderr.write(f"GATE DISPATCH-COST: 目标不是目录: {task_dir}\n")
        return 2

    metrics = measure(task_dir)
    if as_json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(_human(metrics))
    return 0


if __name__ == "__main__":
    sys.exit(main())
