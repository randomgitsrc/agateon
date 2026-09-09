# tests/unit/test_tag0034_resolve.py — TAG0034 resolve(phase, role) 优先级解析算法
#   BDD-7 / BDD-11~18 + T1（P2-review 测试缺口 T1，对应 P2-design §1 M11 / §10 第 2 条 / N2）
#
# 被测：agate/scripts/agate_dispatch_route.py 的 resolve(...)（importable helper，P4a 建）
#   resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model)
#     -> {"form", "chain", "model", "effort"}；form ∈ {"default", "chain"}。
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块尚未实现 → import 在**测试体内**触发
#   ModuleNotFoundError（项目内模块 agate_* 缺失 = B 类；非 collection error / 非第三方）。
#   importlib.import_module 放在函数体内，模块级只 import 标准库 + pytest，无 collection 风险。
#   不用 pytest.importorskip（反模式：会变 skip 不是红）。
#
# P2-design §3.3 定死锚（测试据此写预期）：
#   优先级序：项目级直接值 candidates: > 项目级档位映射 tier: > 机器级绑定 tier_bindings: 展开
#             > 出厂默认 FACTORY.defaults → standard
#   standard 短路：form='default'、chain=None、model=<主 Agent 当前 model>、effort=None
#   tier_bindings 同名键 last-write-wins；effort 合并：候选自带 effort 优先，否则 route 层 effort
#   (phase,role) 命中优先于 phase 级

import importlib
import sys


def _resolve_mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def _resolve(agate_scripts, phase, role, *, routes=None, tier_bindings=None,
             factory_defaults=None, current_model="claude-sonnet-parent"):
    mod = _resolve_mod(agate_scripts)
    return mod.resolve(
        phase, role,
        routes=routes or {},
        tier_bindings=tier_bindings or {},
        factory_defaults=factory_defaults or {},
        current_model=current_model,
    )


def test_bdd_7_tier_expands_to_ordered_cross_cli_chain(agate_scripts):
    """BDD-7：(P2, architect) 写 tier: deep，机器级把 deep 绑为有序链
    [codex/A, claude-code/B]，展开出的候选链顺序逐项一致。"""
    r = _resolve(
        agate_scripts, "P2", "architect",
        routes={"P2": {"architect": {"tier": "deep"}}},
        tier_bindings={"deep": [
            {"cli": "codex", "model": "A"},
            {"cli": "claude-code", "model": "B"},
        ]},
    )
    assert r["form"] == "chain"
    assert [(c["cli"], c["model"]) for c in r["chain"]] == [("codex", "A"), ("claude-code", "B")]


def test_bdd_11_phase_role_hit_beats_phase_level(agate_scripts):
    """BDD-11：同时有 P4:（链 X）与 P4.implementer:（链 Y），派 implementer → 取链 Y。"""
    r = _resolve(
        agate_scripts, "P4", "implementer",
        routes={
            "P4": {"tier": "bulk"},
            "P4.implementer": {"tier": "deep"},
        },
        tier_bindings={
            "bulk": [{"cli": "opencode", "model": "X"}],
            "deep": [{"cli": "codex", "model": "Y"}],
        },
    )
    assert [(c["cli"], c["model"]) for c in r["chain"]] == [("codex", "Y")]


def test_bdd_12_fallback_to_phase_level_when_no_phase_role_entry(agate_scripts):
    """BDD-12：只有 P4:（链 X），无任何 P4.<role>: → 派 protocol-alignment-review 取链 X。"""
    r = _resolve(
        agate_scripts, "P4", "protocol-alignment-review",
        routes={"P4": {"tier": "bulk"}},
        tier_bindings={"bulk": [{"cli": "opencode", "model": "X"}]},
    )
    assert [(c["cli"], c["model"]) for c in r["chain"]] == [("opencode", "X")]


def test_bdd_13_no_phase_entry_equals_standard(agate_scripts):
    """BDD-13：配置无 P7 及 P7.<role> 任何条目 → 解析结果 = standard 档（等价未配置）。"""
    r = _resolve(agate_scripts, "P7", "consistency-reviewer", routes={}, tier_bindings={})
    assert r["form"] == "default"
    assert r["chain"] is None


def test_bdd_14_standard_is_inherit_parent_model_native_dispatch(agate_scripts):
    """BDD-14：解析结果为 standard（显式 tier: standard 或未配置）→ form='default'、
    model = 主 Agent 当前 model、chain=None（不起子进程、不改 model、逐字节等价未启用）。"""
    r = _resolve(
        agate_scripts, "P2", "architect",
        routes={"P2": {"architect": {"tier": "standard"}}},
        current_model="claude-sonnet-parent",
    )
    assert r["form"] == "default"
    assert r["chain"] is None
    assert r["model"] == "claude-sonnet-parent"


def test_bdd_15_three_layer_priority_deterministic(agate_scripts):
    """BDD-15：同一 (phase,role) 在项目级直接值 / 项目级档位映射 / 机器级绑定 / 出厂默认
    四处都可能有值 → 严格按定死优先级序（项目级直接值 > 项目级档位映射 > 机器级绑定 >
    出厂默认），结果唯一确定。此处项目级直接值 candidates: 存在 → 取它，无视 tier/出厂默认。"""
    r = _resolve(
        agate_scripts, "P6.5", "judge",
        routes={"P6.5": {"judge": {"candidates": [{"cli": "codex", "model": "DIRECT"}]}}},
        tier_bindings={"deep": [{"cli": "opencode", "model": "VIA_TIER"}]},
        factory_defaults={"P6.5": "deep"},
    )
    assert r["form"] == "chain"
    assert [(c["cli"], c["model"]) for c in r["chain"]] == [("codex", "DIRECT")]


def test_bdd_16_missing_config_returns_factory_default_no_error(agate_scripts):
    """BDD-16：dispatch-routing.yaml 不存在（routes/tier_bindings 全空）→ 加载器返回出厂默认
    （全 (phase,role) = standard），无 error；后续派发行为 = 现状。"""
    mod = _resolve_mod(agate_scripts)
    routes, tier_bindings = mod.load_config(str(agate_scripts / "no-such-workspace-dir"))
    assert routes == {}
    assert tier_bindings == {}
    r = mod.resolve("P4", "implementer", routes=routes, tier_bindings=tier_bindings,
                    factory_defaults={}, current_model="M")
    assert r["form"] == "default"


def test_bdd_17_corrupt_config_type_bad_returns_factory_default(agate_scripts, tmp_path):
    """BDD-17：dispatch-routing.yaml 存在但 YAML 解析失败（或某键类型坏，如 tier 处写 list）
    → 该文件（或该键）回落出厂默认、写一行 stderr WARNING、不抛异常、不静默把整段路由跳过
    （判据形态复用 check-maintainability.py:_load_config）。"""
    mod = _resolve_mod(agate_scripts)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "dispatch-routing.yaml").write_text("routes: [this, is, not, a, mapping\n", encoding="utf-8")
    routes, tier_bindings = mod.load_config(str(ws))
    assert routes == {}
    assert tier_bindings == {}


def test_bdd_18_machine_binding_duplicate_tier_key_last_write_wins(agate_scripts):
    """BDD-18：项目级把 (P6.5, judge) 映射到 tier: deep，机器级把 deep 绑为候选链 Z，
    且机器级另有一条同名 deep 但不同内容的历史绑定 → 按定死合并规则取唯一结果
    （tier_bindings 同名键 last-write-wins），不产生「两条都生效」的歧义。"""
    r = _resolve(
        agate_scripts, "P6.5", "judge",
        routes={"P6.5": {"judge": {"tier": "deep"}}},
        # 模拟 last-write-wins 已合并后的结果（yaml.safe_load 对重复 mapping key 取最后一个）
        tier_bindings={"deep": [{"cli": "opencode", "model": "Z_LATEST"}]},
    )
    assert [(c["cli"], c["model"]) for c in r["chain"]] == [("opencode", "Z_LATEST")]


def test_t1_resolve_return_contract_key_set_and_form_enum(agate_scripts):
    """T1（P2-review 测试缺口 / N2）：resolve 每条分支返回对象键集恒为 {form, chain, model, effort}；
    form ∈ {'default','chain'}；form == 'default' 时 chain is None。"""
    branches = [
        # standard 短路
        {"routes": {"P2": {"architect": {"tier": "standard"}}}, "tier_bindings": {}},
        # tier 展开
        {"routes": {"P2": {"architect": {"tier": "deep"}}},
         "tier_bindings": {"deep": [{"cli": "codex", "model": "A"}]}},
        # 项目级直接值
        {"routes": {"P2": {"architect": {"candidates": [{"cli": "codex", "model": "D"}]}}},
         "tier_bindings": {}},
        # 未配置 → standard
        {"routes": {}, "tier_bindings": {}},
        # tier 引用但机器级未绑该 tier → 回落默认派发
        {"routes": {"P2": {"architect": {"tier": "deep"}}}, "tier_bindings": {}},
    ]
    for kw in branches:
        r = _resolve(agate_scripts, "P2", "architect", **kw)
        assert set(r.keys()) == {"form", "chain", "model", "effort"}
        assert r["form"] in {"default", "chain"}
        if r["form"] == "default":
            assert r["chain"] is None
