# tests/unit/test_tag0034_events.py — TAG0034 dispatch_route 事件 + check-events.py 第 8 条
#   BDD-27 / BDD-29 / BDD-30 + T3（P2-review 测试缺口 T3，对应 P2-design §3.8 M6 / §10 第 4 条）
#
# 被测：
#   - agate/scripts/check-events.py TASK_DIR（既有 7 条审计链，本任务追加第 8 条）
#   - agate/scripts/agate_dispatch_route.py（写 dispatch_route 事件，复用 append_event 哈希链）
#
# TDD 红灯语义（P3）：
#   - BDD-27 / T3：check-events.py 第 8 条（dispatch_route 理由码枚举校验）尚未实现——含
#     reason == "gate_fail" 的合法哈希链账本当前 exit 0（第 7 条「未知 event 不拦截」放行）；
#     断言 exit 1 失败 = 真红（功能未实现，B 类）。
#   - BDD-29 / BDD-30：check-events.py 源码尚无 "dispatch_route" 字样 / agate_dispatch_route
#     模块未实现——grep 断言与 import 断言失败 = 真红（B 类）。
#
# 哈希链构造：与 test_check_events.py._write_ledger 同源约定
#   （prev_hash = sha256(上一行 JSON 文本 UTF-8，不含行尾换行符)；GENESIS_HASH = sha256(b"")）。

import hashlib
import importlib
import json
import sys

import pytest


def _genesis():
    return hashlib.sha256(b"").hexdigest()


def _write_ledger(td, events):
    """构造 gate-events.jsonl：逐行哈希链，首行 prev_hash = GENESIS_HASH。"""
    prev_hash = _genesis()
    lines = []
    for ev in events:
        row = dict(ev)
        row["prev_hash"] = prev_hash
        line = json.dumps(row, sort_keys=True)
        lines.append(line)
        prev_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
    (td / "gate-events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_events(agate_scripts, python_exe, run_cli, td):
    return run_cli(python_exe, str(agate_scripts / "check-events.py"), str(td))


def _dispatch_route_ev(ts, reasons, final=None):
    tried = []
    for i, reason in enumerate(reasons):
        tried.append({"cli": "codex", "model": f"m{i}", "result": "failed", "reason": reason})
    if final is None:
        final = {"cli": "default"}
    else:
        tried.append({"cli": final["cli"], "model": final.get("model"), "result": "success"})
    return {"ts": ts, "event": "dispatch_route", "phase": "P4", "task_id": "TAG0034",
            "candidates_tried": tried, "final": final}


@pytest.mark.windows_smoke
def test_bdd_27_reason_gate_fail_rejected_by_check_events(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-27：gate-events.jsonl 出现一条 dispatch_route 事件，某 candidates_tried[].reason 值为
    gate_fail（非 {launch_fail, infra_error, no_parseable_output}）→ check-events.py exit 1。"""
    td = task_dir()
    _write_ledger(td, [
        {"ts": "2026-09-09T10:00:01.000001Z", "event": "gate_run", "phase": "P4",
         "cmd": "check-gate.py P4", "exit": 2, "runner": "pre-commit"},
        _dispatch_route_ev("2026-09-09T10:00:02.000001Z", ["infra_error", "gate_fail"]),
    ])
    result = _run_events(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_bdd_29_dispatch_route_event_written_reuses_hash_chain(task_dir, agate_scripts):
    """BDD-29：一次发生了回落的派发，路由决策层写 dispatch_route 事件 → 该事件行
    prev_hash == sha256(上一行原始文本)、ts 单调不减（复用 append_event 哈希链，不自造）。
    P3 红灯：agate_dispatch_route 模块（写入端）尚未实现。"""
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    mod = importlib.import_module("agate_dispatch_route")
    td = task_dir()
    # 先落一条既有事件
    _write_ledger(td, [
        {"ts": "2026-09-09T10:00:01.000001Z", "event": "gate_run", "phase": "P4",
         "cmd": "check-gate.py P4", "exit": 2, "runner": "pre-commit"},
    ])
    ledger = td / "gate-events.jsonl"
    prev_last_line = ledger.read_text(encoding="utf-8").splitlines()[-1]
    mod.write_dispatch_route_event(
        str(td), "P4",
        tried=[{"cli": "codex", "model": "A", "result": "failed", "reason": "infra_error"},
               {"cli": "native", "model": "haiku", "result": "success"}],
        final={"cli": "native", "model": "haiku"},
    )
    new_last = ledger.read_text(encoding="utf-8").splitlines()[-1]
    ev = json.loads(new_last)
    assert ev["event"] == "dispatch_route"
    assert ev["prev_hash"] == hashlib.sha256(prev_last_line.encode("utf-8")).hexdigest()


@pytest.mark.windows_smoke
def test_bdd_30_check_events_knows_dispatch_route_as_valid_event_type(agate_scripts):
    """BDD-30：check-events.py 认 dispatch_route 为已知合法事件类型（第 8 条审计链识别 +
    理由码严格校验），不把它判为「非法未知 event」。
    P3 红灯：check-events.py 源码尚无 dispatch_route 处理分支。
    （既有 test_check_events.py 用例零改动仍绿——由全量回归兜底，非本用例断言对象）。"""
    src = (agate_scripts / "check-events.py").read_text(encoding="utf-8")
    assert "dispatch_route" in src


def test_t3_check_events_reason_enum_parametrized(task_dir, agate_scripts, python_exe, run_cli):
    """T3（P2-review 测试缺口 / N4）：check-events.py 第 8 条参数化——
    launch_fail / infra_error / no_parseable_output 三值各构造一条合法账本断言 exit 0；
    混入第四值（gate_fail）断言 exit 1。"""
    for reason in ("launch_fail", "infra_error", "no_parseable_output"):
        td = task_dir()
        _write_ledger(td, [
            _dispatch_route_ev("2026-09-09T10:00:01.000001Z", [reason],
                               final={"cli": "native", "model": "haiku"}),
        ])
        result = _run_events(agate_scripts, python_exe, run_cli, td)
        assert result.returncode == 0, f"合法理由码 {reason} 应 exit 0"

    td = task_dir()
    _write_ledger(td, [
        _dispatch_route_ev("2026-09-09T10:00:01.000001Z", ["gate_fail"],
                           final={"cli": "native", "model": "haiku"}),
    ])
    result = _run_events(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, "非法理由码 gate_fail 应 exit 1"
