# tests/unit/test_tag0034_interaction.py — TAG0034 与既有派发机制的交互
#   BDD-43 / BDD-44 / BDD-45 / BDD-51
#
# 被测：
#   - agate/scripts/agate_dispatch_route.py（importable helper，P4a 建）
#       resolve(...) 纯函数、无状态；should_consult_routing_table(dispatch_kind) -> bool；
#       route_is_noop(executor_env) -> bool
#   - agate/dispatch-protocol.md / docs/design-notes/design-dispatch-routing.md（doc-assertion）
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块未实现 → import 在测试体内 ModuleNotFoundError
#   （B 类）；doc-assertion（BDD-45/51 的措辞部分）当前红、P4 author 正文后转绿。

import importlib
import sys

import pytest


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def test_bdd_43_parallel_batch_each_subagent_resolves_independently(agate_scripts):
    """BDD-43：P4 并行模式同时派多个 subagent，其中 2 个是同 role 的并行分片 →
    每个 subagent 独立解析；同 role 的并行分片解析到同一条路由；不同 role 各按自己
    (phase,role) 解析。resolve 是纯函数、无跨调用状态。"""
    mod = _mod(agate_scripts)
    routes = {
        "P4": {
            "implementer": {"tier": "bulk"},
            "code-review": {"tier": "deep"},
        }
    }
    tb = {"bulk": [{"cli": "opencode", "model": "B"}],
          "deep": [{"cli": "codex", "model": "D"}]}
    kw = {"routes": routes, "tier_bindings": tb, "factory_defaults": {}, "current_model": "M"}
    # 同 role 的两个并行分片
    r1 = mod.resolve("P4", "implementer", **kw)
    r2 = mod.resolve("P4", "implementer", **kw)
    assert r1 == r2
    # 不同 role
    r3 = mod.resolve("P4", "code-review", **kw)
    assert [(c["cli"], c["model"]) for c in r1["chain"]] == [("opencode", "B")]
    assert [(c["cli"], c["model"]) for c in r3["chain"]] == [("codex", "D")]


def test_bdd_44_autonomous_redispatch_does_not_consult_routing_table(agate_scripts):
    """BDD-44：某执行角色在授权范围内自主再派发一个子任务（RM-AG0055）→ 不解析
    dispatch-routing.yaml，继承父的实际 cli/model；无 dispatch_route 事件产生。"""
    mod = _mod(agate_scripts)
    assert mod.should_consult_routing_table("autonomous_redispatch") is False
    assert mod.should_consult_routing_table("phase_role_dispatch") is True


def test_bdd_45_single_agent_mode_route_is_noop(agate_scripts):
    """BDD-45：executor_env.has_task_tool == False（如 Claude Project 会话）→ 无派发动作、
    路由为 no-op。"""
    mod = _mod(agate_scripts)
    assert mod.route_is_noop({"has_task_tool": False}) is True
    assert mod.route_is_noop({"has_task_tool": True}) is False


@pytest.mark.windows_smoke
def test_bdd_45_single_agent_mode_declared_out_of_scope_in_docs(agate_root):
    """BDD-45（doc-assertion）：dispatch-protocol.md / design-note 显式写「单 Agent 模式下
    路由不适用」（当前红，P4 author 正文后转绿）。"""
    proto = (agate_root / "dispatch-protocol.md").read_text(encoding="utf-8")
    assert "单 Agent 模式" in proto
    assert ("路由不适用" in proto) or ("路由为 no-op" in proto) or ("路由 no-op" in proto)


@pytest.mark.windows_smoke
def test_bdd_51_p5_to_p4_retreat_reresolves_route_no_upgrade_logic(agate_root):
    """BDD-51：P5→P4 跨阶段回退后 P4 retry → 重新机械解析一次 (phase,role) 路由（按当时候选
    可用性落候选，可能与回退前不同），不注入「上次失败 → 升档 / 换更强 model」逻辑；
    与 BDD-26「同阶段内 gate-FAIL retry 用同一候选」不冲突。
    doc-assertion：dispatch-protocol.md 新节写明这条区分（当前红，P4 author 后转绿）。"""
    proto = (agate_root / "dispatch-protocol.md").read_text(encoding="utf-8")
    assert "机械重解析" in proto or "机械重新解析" in proto or "重新机械解析" in proto
    assert "升档" in proto  # 明确写「不做升档 / 换更强 model」


def test_bdd_51_resolve_is_stateless_no_previous_failure_input(agate_scripts):
    """BDD-51（功能面）：resolve 无状态——签名不接受「上次失败候选」类入参，同输入恒同输出
    （机械查表、与状态机 retry 不耦合）。"""
    mod = _mod(agate_scripts)
    import inspect

    sig = inspect.signature(mod.resolve)
    params = set(sig.parameters)
    # 不得有「上次失败 / 已试候选 / 升档」类入参
    assert not (params & {"previous_failure", "failed_candidate", "escalate", "upgrade", "tried"})
    kw = {"routes": {"P4": {"implementer": {"tier": "bulk"}}},
          "tier_bindings": {"bulk": [{"cli": "opencode", "model": "B"}]},
          "factory_defaults": {}, "current_model": "M"}
    assert mod.resolve("P4", "implementer", **kw) == mod.resolve("P4", "implementer", **kw)
