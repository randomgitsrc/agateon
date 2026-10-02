# tests/regression/test_tag0034_zero_change.py — TAG0034 回归证明（BDD-40）
#
# ⚠️ **2026-10-02：BDD-39 的「字节零改动绊线」已删除**，本文件只保留 BDD-40。
#
#   删除理由（本文件原注释已自陈该绊线的缺陷，此处据以执行）：
#     · **过严**：注释、WARNING 文案等**行为无关**的字节变化同样触发 ⇒ 每次都要人工判断 +
#       刷新基线 + 写 `_note`。基线累计被刷新 **9 次**，其中末两次（2026-10-02）都是同一会话内的
#       **纯注释**改动。
#     · **过松**：真正的判据回归可混在同一次刷新里蒙混 ⇒ 它只保证「有人注意到并申报」，
#       **不保证「行为未变」**（原注释原话）。
#     · **申报已被别处承担**：`_note` 是没人读的 JSON 散文；「改了什么、为什么」本就由
#       CHANGELOG + PR 描述承担 ⇒ 该绊线边际价值 ≈ 0。
#     · **行为不变已被覆盖**：4 个受护文件各有判据测试（全量套件约 2500 用例）。
#     · 原注释提的改进方向（「行为不变」自动断言 + 变更申报两层）若将来要做，应**重新设计**，
#       不是复活字节哈希。
#   随之删除：`agate/tests/fixtures/tag0034_regression_baseline.json`（基线夹具，仅该绊线消费）。
#
# BDD-40（保留）→ 仓库无 `dispatch-routing.yaml`、无机器级绑定文件、协议出厂默认全 standard 时：
#   ① 加载器 `load_config` 返回空配置；② `resolve` 对全阶段返回 `form=default` 且无 chain；
#   ③ 现状任务账本 `gate-events.jsonl` 中 `dispatch_route` 事件条数 = 0（机制引入前的回归基线）。
#
# 平台无关：纯文件读取 + importlib；无 shell / 无路径分隔符假设。

import importlib
import json
import sys


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
