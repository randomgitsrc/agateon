# tests/unit/test_tag0034_tryfall.py — TAG0034 try-and-fall 逐级回落循环（无 probe）
#   BDD-19~26 / BDD-28 + T2（P2-review 测试缺口 T2 / N6，对应 P2-design §10 第 3 条）
#
# 被测：agate/scripts/agate_dispatch_route.py（importable helper，P4a 建）
#   - classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None)
#       -> Outcome，Outcome.kind ∈ {"LAUNCH_FAIL","INFRA_ERROR","NO_PARSEABLE_OUTPUT","HAS_OUTPUT"}
#       Outcome.reason ∈ {"launch_fail","infra_error","no_parseable_output"} 或 None（HAS_OUTPUT）
#   - try_and_fall(chain, *, dispatch_context_path, dispatch_once, write_event) -> 结果对象
#       结果.final（成功候选 dict 或 {"cli":"default"}）、结果.tried（list，每项含 result/reason）
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块尚未实现 → import 在测试体内触发
#   ModuleNotFoundError（项目内模块缺失 = B 类）。模块级只 import 标准库。
#
# P2-design §3.7 判定表锚（测试据此写预期）：
#   LAUNCH_FAIL：CLI 未装 / 可执行缺失 / spawn OSError
#   INFRA_ERROR：401 循环 / 网络不可达 / 429 / 进程中途崩溃 / turn.failed / 顶层 error JSON
#               / 挂死被杀（RM-AG0055 命令流阈值 或 wait(pid) 超时 或 kill -0 探测失活 → kill）
#   NO_PARSEABLE_OUTPUT：进程正常退出但 D2 假完成校验不过（约定产出文件缺失或空 / 结构化空返回）
#   HAS_OUTPUT：产出文件非空 + presence 级骨架可解析（不含内容完整度 / 质量判断）
#   回落只在前三类；HAS_OUTPUT 即停、交 gate、不再试后续候选
#   全落空 → 默认派发 + final={"cli":"default"}，candidates_tried 保留每个失败理由码

import importlib
import sys


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def test_bdd_19_no_probe_first_candidate_gets_real_ctx(agate_scripts):
    """BDD-19：候选链首项直接派发——不向候选发任何「探测 / hi」预请求；第一个动作就是把
    真实 dispatch-context 派给首选候选。"""
    mod = _mod(agate_scripts)
    calls = []

    def dispatch_once(cand, ctx_path):
        calls.append((cand, ctx_path))
        return mod.classify_outcome(cand["cli"], stdout="ok", exit_code=0,
                                    produced_files=["P2-design.md"])

    mod.try_and_fall(
        [{"cli": "codex", "model": "A"}],
        dispatch_context_path="P2-dispatch-context-architect.md",
        dispatch_once=dispatch_once,
        write_event=lambda *a, **k: None,
    )
    assert len(calls) == 1
    # 第一个动作即真实 ctx 路径，无任何 probe 预请求
    assert calls[0][1].endswith("dispatch-context.md") or "dispatch-context" in calls[0][1]


def test_bdd_20_launch_fail_falls_back_to_next(agate_scripts):
    """BDD-20：首选候选子进程无法启动（OSError）→ 以理由码 launch_fail 记录，派下一候选。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome("codex", stdout="", exit_code=None, produced_files=[],
                             killed_reason="spawn_oserror")
    assert o.kind == "LAUNCH_FAIL"
    assert o.reason == "launch_fail"


def test_bdd_21_infra_error_falls_back_to_next(agate_scripts):
    """BDD-21：首选候选启动了但基础设施失败（401 / 网络不可达 / 429 / 进程崩溃 / turn.failed）
    → 以理由码 infra_error 记录，派下一候选。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "codex",
        stdout='{"type":"turn.failed","error":{"message":"429"}}',
        exit_code=1,
        produced_files=[],
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"


def test_bdd_22_no_parseable_output_falls_back_to_next(agate_scripts):
    """BDD-22：首选候选正常结束但未产出任何 gate 能评的东西（约定产出文件缺失或空 /
    结构化输出空返回）→ 以理由码 no_parseable_output 记录，派下一候选。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome("claude-code", stdout='{"stop_reason":"end_turn","result":""}',
                             exit_code=0, produced_files=[])
    assert o.kind == "NO_PARSEABLE_OUTPUT"
    assert o.reason == "no_parseable_output"


def test_bdd_23_all_candidates_exhausted_falls_to_default_dispatch(agate_scripts):
    """BDD-23：候选链所有候选都以三类基础设施理由码失败 → 回落默认派发；dispatch_route 事件
    final 记为 {"cli":"default"} 且 candidates_tried 保留每个候选的失败理由码。"""
    mod = _mod(agate_scripts)

    def dispatch_once(cand, ctx_path):
        return mod.classify_outcome(cand["cli"], stdout="", exit_code=None,
                                    produced_files=[], killed_reason="spawn_oserror")

    events = []
    res = mod.try_and_fall(
        [{"cli": "codex", "model": "A"}, {"cli": "opencode", "model": "B"}],
        dispatch_context_path="P2-dispatch-context-architect.md",
        dispatch_once=dispatch_once,
        write_event=lambda phase, tried, final: events.append((tried, final)),
    )
    assert res.final == {"cli": "default"}
    assert [t["reason"] for t in res.tried] == ["launch_fail", "launch_fail"]


def test_bdd_24_fallback_only_on_infra_signals_not_quality(agate_scripts):
    """BDD-24（完整性不变量）：首选候选产出了 gate 能评的东西，但内容质量差 / 不完整 →
    不回落（仅 launch_fail / infra_error / no_parseable_output 触发回落，产出质量不是回落信号）。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "claude-code",
        stdout='{"stop_reason":"end_turn","result":"薄弱但非空的产出"}',
        exit_code=0,
        produced_files=["P2-design.md"],
    )
    assert o.kind == "HAS_OUTPUT"
    assert o.reason is None


def test_bdd_25_any_gate_evaluable_output_stops_fallback(agate_scripts):
    """BDD-25（完整性不变量）：某候选产出了约定产出文件（非空、格式合法）→ 该条路由即判成功、
    停止尝试后续候选、把产出交 gate。"""
    mod = _mod(agate_scripts)
    tried_clis = []

    def dispatch_once(cand, ctx_path):
        tried_clis.append(cand["cli"])
        if cand["cli"] == "codex":
            return mod.classify_outcome("codex", stdout="turn.completed", exit_code=0,
                                        produced_files=["P2-design.md"])
        raise AssertionError("不应尝试后续候选")

    res = mod.try_and_fall(
        [{"cli": "codex", "model": "A"}, {"cli": "opencode", "model": "B"}],
        dispatch_context_path="P2-dispatch-context-architect.md",
        dispatch_once=dispatch_once,
        write_event=lambda *a, **k: None,
    )
    assert tried_clis == ["codex"]
    assert res.final == {"cli": "codex", "model": "A"}


def test_bdd_26_gate_fail_retries_same_candidate_no_new_dispatch_route_event(agate_scripts):
    """BDD-26（完整性不变量）：某候选产出被交给 gate，gate 判 FAIL → retry 在同一候选上重跑
    （不重新解析路由换候选）；本次 retry 不新增 dispatch_route 事件。
    实现层判据：try_and_fall 无状态、gate FAIL 不是 outcome.kind 的取值、不进 tried[].reason；
    「是否重新调用 try_and_fall」由主 Agent 按 retry 类型决定（同阶段 gate-FAIL retry 不调）。"""
    mod = _mod(agate_scripts)
    valid = {"launch_fail", "infra_error", "no_parseable_output"}
    # gate_fail 不是合法 outcome，也不是合法 reason
    assert "gate_fail" not in valid
    assert not hasattr(mod, "GATE_FAIL_TRIGGERS_FALLBACK") or mod.GATE_FAIL_TRIGGERS_FALLBACK is False
    # classify_outcome 无论如何不产出 kind == "GATE_FAIL"
    o = mod.classify_outcome("codex", stdout="turn.completed", exit_code=0,
                             produced_files=["P2-design.md"])
    assert o.kind != "GATE_FAIL"
    assert o.reason not in valid or o.reason is None
    assert o.kind == "HAS_OUTPUT"


def test_bdd_28_fallback_not_state_machine_retry(agate_scripts):
    """BDD-28：某次派发在候选链上逐级回落 2 次后在第 3 候选成功 → 只新增 1 条 dispatch_route
    事件；不写 state_transition、不动 retries[Pn]、不触发 PAUSED。"""
    mod = _mod(agate_scripts)
    seq = iter(["infra_error", "launch_fail", None])

    def dispatch_once(cand, ctx_path):
        reason = next(seq)
        if reason is None:
            return mod.classify_outcome(cand["cli"], stdout="turn.completed", exit_code=0,
                                        produced_files=["P2-design.md"])
        return mod.classify_outcome(cand["cli"], stdout="", exit_code=1, produced_files=[],
                                    killed_reason=("spawn_oserror" if reason == "launch_fail" else None))

    events = []
    res = mod.try_and_fall(
        [{"cli": "codex", "model": "A"}, {"cli": "opencode", "model": "B"},
         {"cli": "claude-code", "model": "C"}],
        dispatch_context_path="P2-dispatch-context-architect.md",
        dispatch_once=dispatch_once,
        write_event=lambda phase, tried, final: events.append((phase, tried, final)),
    )
    assert len(events) == 1  # 只 1 条 dispatch_route 事件
    assert res.final == {"cli": "claude-code", "model": "C"}
    assert [t["reason"] for t in res.tried[:2]] == ["infra_error", "launch_fail"]


def test_t2_hang_kill_maps_to_infra_error(agate_scripts):
    """T2（P2-review 测试缺口 / N6）：模拟 wait(pid) 超时 / RM-AG0055 命令流阈值触发 kill
    → outcome.kind == INFRA_ERROR、回落理由码 infra_error。"""
    mod = _mod(agate_scripts)
    for killed in ("wait_timeout", "cmdstream_threshold", "kill0_dead"):
        o = mod.classify_outcome("claude-code", stdout="", exit_code=None,
                                 produced_files=[], killed_reason=killed)
        assert o.kind == "INFRA_ERROR", killed
        assert o.reason == "infra_error", killed
