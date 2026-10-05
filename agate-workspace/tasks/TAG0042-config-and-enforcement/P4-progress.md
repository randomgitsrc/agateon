# TAG0042 P4 progress — batch4-gate-layer

- 读派发指引 + implementer 角色 + P1 BDD-14/15/21 + P2 §1.1/§4.3/§6.1b/§11/§12 + P3 batch4 + 测试代码。
- 红灯基线：`test_gate_layer.py` + `test_check_p8_delivery.py` → 7 failed, 1 passed（TC-B21-01 因 batch2 的 agate-config.py 已落而绿）。
- R3 全量 grep 发版逻辑消费方（见 P4-implementation-batch4.md）；本批不删发版逻辑。
- 实现落点：phases.yaml（gate_layer + P8 语义）/ WORKFLOW.md（S-1 名称一致）/ phases.schema.json（additionalProperties=false 须同步）/ check-gate.py gate_p8（delivery 拦截 + 声明缺失 WARNING）/ P8-release.md 卡 / UPGRADING.md / 同步 3 个 gate_p8 测试夹具。
