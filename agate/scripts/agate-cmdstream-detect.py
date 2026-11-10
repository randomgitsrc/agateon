#!/usr/bin/env python3
"""agate-cmdstream-detect.py — 命令流检测引擎 + 心跳 helper + CLI（TAG0028，RM-AG0055）

消费 CommandRecord IR（或与 verify 脚本同构的活动事件 dict 列表），机械检测两类卡死
与逻辑空转（BDD-8~24，P2-design.md §3.2 M3）：

  - 调用冻结（FROZEN）：存在未结束 call（call 无配对 result），开始距今超阈值——
    声明 expected → max(expected×2, 30s) 主信号（BDD-8）；未声明 → 兜底 alert 300s
    （BDD-9）/ suspect 900s（BDD-10）
  - 活动冻结（FROZEN）：无未结束 call 时，任何活动事件（思考/输出/工具）距今超
    alert 60s（BDD-11）/ suspect 300s（BDD-12）；三类活动均计入 → 长时间思考不误杀
    （BDD-13）
  - 无效重复（SPIN）：窗口内同 (命令, exit, 输出哈希) 组合重复 ≥5（BDD-14）；
    结果签名变化不误报（BDD-15）；唯一命令数 <3 信息级提示不判空转（BDD-16）；
    truncated 输出不参与哈希比对、仍参与冻结检测（BDD-17）
  - 轮询误报标注：gh pr checks --watch 类合法轮询附"轮询"标注（核查提示而非自动
    判定/终止，BDD-18/23）
  - 输出平台无关：判定类别 + 原因 + 阈值依据 + 建议动作方向，不含平台工具名（BDD-24）

阈值读取（BDD-19/20/21）：config 为 dict（显式覆盖，兼容 activity_alert 别名）或
maintainability.yaml 路径（缺失/损坏/类型坏 → 协议默认值不报错、不静默跳过），复用
check-maintainability.py:88-148 `_load_config` 全兜底模式（P2 §3.2 R4）。

心跳 helper（P3 §4.4，Phase 3）：heartbeat_path(task_dir, n=None) 命名
（.heartbeat / .heartbeat.child-{n}）；cleanup_heartbeats(task_dir) 产生方清理。

CLI 子命令：list-sessions PLATFORM CWD / read-commands PLATFORM SESSION / detect
SESSION [--platform P] [--now N] [--config PATH]（P2 M3）。
"""

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 阈值常量（与 verify_cmdstream_detection.py 同源，P2 §3.2 R3） ----

CALL_EXPECT_MULT = 2          # expected × 2
CALL_FLOOR = 30               # expected 很小时兜底下限（秒）
CALL_ALERT_FALLBACK = 300     # 未声明 expected：>300s 提示核查
CALL_SUSPECT_FALLBACK = 900   # 未声明 expected：>900s 考虑中止核查
ACTIVITY_ALERT = 60           # 无任何活动 >60s 提示核查
ACTIVITY_SUSPECT = 300        # 无任何活动 >300s 考虑中止核查
SPIN_THRESHOLD = 5            # 同一 (命令, exit, 输出哈希) 重复 >= 5 → 空转
REPEAT_WINDOW = 10            # 重复检测窗口
REPEAT_UNIQUE_MIN = 3         # 窗口内唯一命令数 < 3 → 信息级提示

DEFAULT_THRESHOLDS = {
    "call_freeze_alert": CALL_ALERT_FALLBACK,
    "call_freeze_suspect": CALL_SUSPECT_FALLBACK,
    "activity_freeze_alert": ACTIVITY_ALERT,
    "activity_freeze_suspect": ACTIVITY_SUSPECT,
    "spin_window": REPEAT_WINDOW,
    "spin_threshold": SPIN_THRESHOLD,
    "repeat_unique_min": REPEAT_UNIQUE_MIN,
    "expected_multiplier": CALL_EXPECT_MULT,
    "expected_lower_bound": CALL_FLOOR,
}

# config dict 别名（测试/用户友好短名 → 规范键）
_CONFIG_ALIASES = {
    "call_freeze_alert": "call_freeze_alert",
    "call_freeze_suspect": "call_freeze_suspect",
    "activity_alert": "activity_freeze_alert",
    "activity_freeze_alert": "activity_freeze_alert",
    "activity_suspect": "activity_freeze_suspect",
    "activity_freeze_suspect": "activity_freeze_suspect",
    "spin_window": "spin_window",
    "spin_threshold": "spin_threshold",
    "repeat_unique_min": "repeat_unique_min",
    "expected_multiplier": "expected_multiplier",
    "expected_lower_bound": "expected_lower_bound",
}

# ---- 兄弟模块动态加载（ADAPTERS 注册表消费锚，BDD-6） ----

_ADAPTERS_CACHE = {}


def _load_adapters():
    """importlib 加载 agate-cmdstream-adapters.py，取 ADAPTERS 注册表（带缓存）。"""
    if "adapters" in _ADAPTERS_CACHE:
        return _ADAPTERS_CACHE["adapters"]
    path = os.path.join(_SCRIPT_DIR, "agate-cmdstream-adapters.py")
    spec = importlib.util.spec_from_file_location("agate_cmdstream_adapters", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _ADAPTERS_CACHE["adapters"] = mod
    return mod


ADAPTERS = _load_adapters().ADAPTERS  # 显式注册表（BDD-6：检测引擎零改动消费新平台）


# ---- 阈值配置（全兜底，BDD-19/20/21） ----


def _load_config(config=None):
    """解析阈值配置 → 阈值 dict。

    - None → 协议默认值
    - dict → 显式覆盖（键经 _CONFIG_ALIASES 归一，类型坏/未知键忽略）
    - str 路径 → maintainability.yaml：缺失/损坏 → 默认值（stderr 提示，不报错、
      不静默跳过）；单键缺失/类型坏 → 该键默认值
    """
    cfg = dict(DEFAULT_THRESHOLDS)
    if config is None:
        return cfg

    if isinstance(config, dict):
        _merge_config(cfg, config)
        return cfg

    if isinstance(config, str) and os.path.isfile(config):
        try:
            import yaml
            with open(config, encoding="utf-8", errors="replace") as f:
                raw = yaml.safe_load(f)
        except Exception:
            sys.stderr.write(
                f"agate-cmdstream-detect WARNING: 配置文件解析失败，使用默认值: {config}\n"
            )
            return cfg
        section = raw.get("cmdstream_detection") if isinstance(raw, dict) else None
        if isinstance(section, dict):
            _merge_config(cfg, section)
    return cfg


def _merge_config(cfg, raw):
    """把用户配置合并进 cfg（规范化键 + 类型校验，类型坏忽略并提示）。"""
    for key, canonical in _CONFIG_ALIASES.items():
        if key not in raw:
            continue
        val = raw[key]
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            sys.stderr.write(
                f"agate-cmdstream-detect WARNING: 阈值 {key} 类型坏（期望正整数），使用默认值\n"
            )
            continue
        cfg[canonical] = val


# ---- 检测引擎（判据与 verify_cmdstream_detection.py 对齐，阈值常量同源） ----


def detect(events, now, config=None):
    """检测命令流活动事件 → (verdict, reasons)。

    events：活动事件 dict 列表（与 verify Event 同构）——
      {"ts": int, "kind": "think"|"out"|"call"|"result", "id"?: str, "cmd"?: str,
       "exit"?: int, "out"?: str, "expected"?: int, "truncated"?: bool}
    now：主 Agent 观察时刻（epoch 秒/毫秒同单位即可，内部只做差值比较）。
    返回 (verdict, reasons)；verdict ∈ {"FROZEN", "SPIN", "NORMAL"}，
    reasons 为字符串列表（阈值依据 + alert/suspect 级别 + 建议动作方向，平台无关）。
    """
    if not events:
        return "NORMAL", ["无活动记录（进程未启动？）"]
    cfg = _load_config(config)
    reasons = []

    call_ids = {e.get("id") for e in events if e.get("kind") == "call" and e.get("id")}
    result_ids = {e.get("id") for e in events if e.get("kind") == "result" and e.get("id")}
    unresolved = [e for e in events if e.get("kind") == "call" and e.get("id") in (call_ids - result_ids)]
    completed = [e for e in events if e.get("kind") == "result"]

    # ---- 1. 调用冻结（存在未结束 call）----
    if unresolved:
        # 最新开始的未结束调用优先判定（最相关信号，BDD-8 语义）
        for c in sorted(unresolved, key=lambda e: e.get("ts", 0), reverse=True):
            age = now - c.get("ts", 0)
            expected = c.get("expected")
            if expected is not None:
                thr = max(expected * cfg["expected_multiplier"], cfg["expected_lower_bound"])
                src = f"expected={expected}s ×{cfg['expected_multiplier']}"
            else:
                if age > cfg["call_freeze_suspect"]:
                    reasons.append(
                        f"调用冻结（suspect）：未结束调用 {c.get('id')}（{c.get('cmd')}）"
                        f"距今 {age}s ≥ 兜底阈值 {cfg['call_freeze_suspect']}s "
                        f"（未声明 expected）→ 疑似卡在单次调用，建议人工核查"
                    )
                    return "FROZEN", reasons
                thr = cfg["call_freeze_alert"]
                src = f"未声明 expected，兜底 {cfg['call_freeze_alert']}s"
            if age >= thr:
                reasons.append(
                    f"调用冻结（alert）：未结束调用 {c.get('id')}（{c.get('cmd')}）"
                    f"距今 {age}s ≥ 阈值 {thr}s（{src}）→ 疑似卡在单次调用，建议核查"
                )
                return "FROZEN", reasons
            reasons.append(
                f"提示：存在未结束调用 {c.get('id')}（{c.get('cmd')}）距今 {age}s，"
                f"未超阈值 {thr}s（{src}）——长命令执行中，正常"
            )
    else:
        # ---- 2. 活动冻结（无未结束 call）----
        last_activity = max(
            e.get("ts", 0) for e in events if e.get("kind") in ("think", "out", "call", "result")
        )
        age = now - last_activity
        if age >= cfg["activity_freeze_suspect"]:
            reasons.append(
                f"活动冻结（suspect）：最后活动事件距今 {age}s ≥ "
                f"{cfg['activity_freeze_suspect']}s → 疑似进程无任何活动，建议人工核查"
            )
            return "FROZEN", reasons
        if age >= cfg["activity_freeze_alert"]:
            reasons.append(
                f"活动冻结（alert）：最后活动事件距今 {age}s ≥ "
                f"{cfg['activity_freeze_alert']}s → 提示核查"
            )
            return "FROZEN", reasons

    # ---- 3. 无效重复检测（逻辑空转）----
    # 窗口按 **ts 排序后取最近 N 条**，不依赖调用方给的列表顺序：
    # 适配器可能"最新在前"返回（DSH 适配器 records[::-1]，注释明写监控视角最新优先），
    # 此时 `completed[-N:]` 取到的是**会话最早**的 N 条——实测 1773 条记录的会话里，
    # 该窗口落在会话开头，判出的 SPIN 命中 `command=""` 的 read/skill 调用（空串 sha1
    # da39a3ee…），与真正要抓的空转无关。按 ts 排序即与顺序约定解耦。
    ordered = sorted(completed, key=lambda e: e.get("ts", 0))
    window = ordered[-cfg["spin_window"]:]
    combo_counts = {}
    for r in window:
        if r.get("truncated"):
            continue  # 截断输出不参与哈希比对（BDD-17）
        key = (r.get("cmd"), r.get("exit"), r.get("out"))
        combo_counts[key] = combo_counts.get(key, 0) + 1
    if combo_counts:
        worst = max(combo_counts.values())
        if worst >= cfg["spin_threshold"]:
            worst_key = max(combo_counts, key=combo_counts.get)
            msg = (
                f"空转：同 (命令, exit, 输出哈希) 组合 {worst_key} "
                f"在窗口 {cfg['spin_window']} 内重复 {worst} 次 ≥ {cfg['spin_threshold']}"
                f" → 疑似逻辑空转，建议核查"
            )
            if _looks_like_polling(str(worst_key[0])):
                msg += "（轮询误报类：命令含 watch/poll 特征，可能是合法轮询循环，仅提示核查）"
            reasons.append(msg)
            return "SPIN", reasons

    # ---- 4. NORMAL（含信息级提示）----
    unique_cmds = {r.get("cmd") for r in window}
    if len(unique_cmds) < cfg["repeat_unique_min"]:
        reasons.append(
            f"提示：窗口 {cfg['spin_window']} 内唯一命令数 {len(unique_cmds)} < "
            f"{cfg['repeat_unique_min']}，但结果签名在变化（合法迭代特征），不判空转"
        )
    reasons.append("正常：活动持续推进，无冻结/空转信号")
    return "NORMAL", reasons


def _looks_like_polling(cmd):
    """轮询误报类特征：命令含 watch / poll / checks --watch 等轮询关键字（BDD-18）。"""
    lowered = cmd.lower()
    return any(kw in lowered for kw in ("watch", "poll", "checks --watch", "sleep"))


# ---- 心跳文件生命周期 helper（P3 §4.4，Phase 3） ----


def heartbeat_path(task_dir, n=None):
    """心跳文件路径：n=None → {TASK_DIR}/.heartbeat；n 为整数 →
    {TASK_DIR}/.heartbeat.child-{n}（同父任务内不重复不覆盖，BDD-25）。"""
    base = Path(task_dir)
    if n is None:
        return base / ".heartbeat"
    return base / f".heartbeat.child-{n}"


def cleanup_heartbeats(task_dir):
    """清理任务目录内心跳文件（产生方清理；异常遗留由派发前置检查清空，BDD-27）。
    返回清理文件数。比照 agate-archive-stale-outputs 任务目录收尾模式，不新建清理机制。"""
    base = Path(task_dir)
    removed = 0
    for p in sorted(base.glob(".heartbeat*")):
        if p.is_file():
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed


# ---- CLI（list-sessions / read-commands / detect，P2 M3） ----


def _parse_epoch_seconds(ts_str):
    """CLI now 参数：接受 epoch 毫秒 int 或 ISO-8601 → 归一为 epoch 秒（CRITICAL-1）。

    CLI detect 事件 ts 与 --now 统一为秒（epoch 毫秒 IR → //1000），与 detect()
    秒级阈值同口径；10 位秒输入原样保留，13 位毫秒输入转秒。
    """
    if ts_str.isdigit():
        v = int(ts_str)
        return v // 1000 if v >= 10 ** 12 else v
    return _load_adapters()._iso8601_to_epoch_ms(ts_str) // 1000


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="agate-cmdstream-detect.py",
        description="命令流日志检测引擎（RM-AG0055）：解析三平台会话 + 检测冻结/空转",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-sessions", help="列出平台会话文件")
    p_list.add_argument("platform", choices=sorted(ADAPTERS.keys()))
    p_list.add_argument("cwd")

    p_read = sub.add_parser("read-commands", help="解析会话为 CommandRecord JSON")
    p_read.add_argument("platform", choices=sorted(ADAPTERS.keys()))
    p_read.add_argument("session")

    p_detect = sub.add_parser("detect", help="检测命令流冻结/空转")
    p_detect.add_argument("session")
    p_detect.add_argument("--platform", choices=sorted(ADAPTERS.keys()), required=True)
    p_detect.add_argument("--now", default=None, help="观察时刻 epoch 毫秒/秒或 ISO-8601（内部归一秒）")
    p_detect.add_argument("--config", default=None, help="maintainability.yaml 路径")
    p_detect.add_argument(
        "--expected", type=int, default=None,
        help="未结束调用预期时长（秒），调用冻结 expected×2 主信号（BDD-8）；"
             "缺省走兜底 300/900s（BDD-9/10）",
    )

    args = parser.parse_args(argv)

    adapter = ADAPTERS[args.platform]
    if args.command == "list-sessions":
        for s in adapter.list_sessions(args.cwd):
            print(s)
        return 0
    if args.command == "read-commands":
        for rec in adapter.read_commands(args.session):
            print(rec.to_json())
        return 0
    if args.command == "detect":
        records = adapter.read_commands(args.session)
        events = []
        skipped_ts = 0  # 无开始时间记录计数（CRITICAL-4 精神：防静默吞数据）
        # CRITICAL-3 ②：事件 id 加调用序号保证唯一——同会话同命令多次调用不再坍缩，
        # call_ids/result_ids 集合运算保留每条未结束 call（BDD-8/9/10 CLI 通路可达）。
        for idx, r in enumerate(records):
            if r.ts_start is None:
                skipped_ts += 1
                continue  # 无开始时间的记录不参与时间判定
            ev_id = f"{r.session_id}:{r.tool}:{r.command}#{idx}"
            events.append(
                {
                    "ts": r.ts_start // 1000,  # CRITICAL-1：epoch 毫秒 → 秒
                    "kind": "call",
                    "id": ev_id,
                    "cmd": r.command,
                    "expected": args.expected,  # CRITICAL-3 ③：expected 接入 CLI 事件
                }
            )
            if r.exit is not None or r.ts_end is not None:
                ts_end = (r.ts_end if r.ts_end is not None else r.ts_start) // 1000
                events.append(
                    {
                        "ts": ts_end,
                        "kind": "result",
                        "id": ev_id,
                        "cmd": r.command,
                        "exit": r.exit,
                        "out": r.output_hash,
                        "truncated": r.truncated,
                    }
                )

        now = _parse_epoch_seconds(args.now) if args.now else int(time.time())
        verdict, reasons = detect(events, now, config=args.config)
        print(f"VERDICT: {verdict}")
        for reason in reasons:
            print(f"  · {reason}")
        if skipped_ts:
            sys.stderr.write(f"警告: {skipped_ts} 条记录缺开始时间，未参与冻结判定\n")
        return 0
    parser.error(f"未知子命令: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
