# tests/regression/test_tag0034_zero_change.py — TAG0034 回归证明（零改动 + 不配置 = 逐字节现状）
#   BDD-39 / BDD-40
#
# 性质：**回归护栏**（test-designer 卡片「永久回归测试判据」允许断言当前状态——这是长期不变量：
#   「gate / 状态机 / phases.yaml 结构零改动」「不配置 = 逐字节现状」）。
#
#   BDD-39 → **P3 绿属预期，非 TDD 违规**（在 P3-test-cases.md 显式标注）。基线 sha256 于 P3
#     捕获（agate/tests/fixtures/tag0034_regression_baseline.json），断言「当前内容 hash == 基线 hash」。
#     本任务任何阶段使这些文件字节变化 → 本用例转红（BDD-39 违反）。
#   BDD-40 → 端到端「跑完整 P1→P8 无配置」依赖路由机制存在 + 加载器「无 dispatch-routing.yaml
#     时返回出厂默认」——该部分 **P3 红**（B 类：agate_dispatch_route 模块 / 加载器待建）；
#     「dispatch_route 事件条数 = 0」的账本部分 P3 绿（回归基线）。整体：BDD-40 至少一个断言红。
#
# 平台无关：hashlib + read_bytes；importlib 在测试体内（B 类红，非 collection error）。

import hashlib
import importlib
import json
import sys


def _baseline(agate_root):
    p = agate_root / "tests" / "fixtures" / "tag0034_regression_baseline.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change(agate_root):
    """BDD-39：本任务全部改动已提交后，check-gate.py / check-state-transition.py /
    phases.yaml / 状态机定义（state-machine.md）逐字节不变；agate-dispatch.py 的既有
    dispatch-context 渲染产物（test_tag0027_b2_agate_dispatch.py +
    test_tag0027_b2_audit2_dual_anchor.py）零改动仍绿。
    [回归护栏 — P3 绿属预期]"""
    repo_root = agate_root.parent
    base = _baseline(agate_root)
    for rel, meta in base["files"].items():
        b = repo_root.joinpath(rel).read_bytes()
        actual = hashlib.sha256(b).hexdigest()
        assert actual == meta["sha256"], (
            f"BDD-39 违反：{rel} 字节面已变（基线 {meta['sha256'][:12]}… → 当前 {actual[:12]}…）"
        )


def test_bdd_40_no_config_equals_byte_for_byte_status_quo(agate_root, agate_scripts, task_dir):
    """BDD-40：仓库无 dispatch-routing.yaml、无机器级绑定文件、协议出厂默认全 standard →
    跑完整一轮 P1→P8 派发，每阶段派发方式 / 产出 / gate-events.jsonl（除不产生任何
    dispatch_route 事件外）与机制引入前一致；dispatch_route 事件条数 = 0。

    P3：
      (a) [B 类红] 加载器「无 dispatch-routing.yaml → 出厂默认」+ resolve 「未配置 → form=default」
          —— agate_dispatch_route 模块待建。
      (b) [回归基线绿] 现状 task 目录（本任务 P3 阶段）gate-events.jsonl 中 dispatch_route
          事件条数 = 0。
    """
    # (b) 回归基线：当前任务账本无 dispatch_route 事件
    ledger = agate_root.parent / "agate-workspace" / "tasks" / "TAG0034-dispatch-routing" / "gate-events.jsonl"
    if ledger.is_file():
        for raw in ledger.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            ev = json.loads(stripped)
            assert ev.get("event") != "dispatch_route", "机制引入前不应有 dispatch_route 事件"

    # (a) B 类红：加载器 + resolve 出厂默认路径
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    mod = importlib.import_module("agate_dispatch_route")
    routes, tier_bindings = mod.load_config(str(task_dir()))  # 无 dispatch-routing.yaml
    assert routes == {} and tier_bindings == {}
    for phase in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"):
        r = mod.resolve(phase, "implementer", routes=routes, tier_bindings=tier_bindings,
                        factory_defaults={}, current_model="parent-model")
        assert r["form"] == "default"
        assert r["chain"] is None
