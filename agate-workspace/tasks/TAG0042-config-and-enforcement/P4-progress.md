# TAG0042 P4 progress — batch4-gate-layer

- 读派发指引 + implementer 角色 + P1 BDD-14/15/21 + P2 §1.1/§4.3/§6.1b/§11/§12 + P3 batch4 + 测试代码。
- 红灯基线：`test_gate_layer.py` + `test_check_p8_delivery.py` → 7 failed, 1 passed（TC-B21-01 因 batch2 的 agate-config.py 已落而绿）。
- R3 全量 grep 发版逻辑消费方（见 P4-implementation-batch4.md）；本批不删发版逻辑。
- 实现落点：phases.yaml（gate_layer + P8 语义）/ WORKFLOW.md（S-1 名称一致）/ phases.schema.json（additionalProperties=false 须同步）/ check-gate.py gate_p8（delivery 拦截 + 声明缺失 WARNING）/ P8-release.md 卡 / UPGRADING.md / 同步 3 个 gate_p8 测试夹具。

# TAG0042 P4 progress — batch5-ci-doctor（CI 与诊断）

- 读派发指引 + implementer 角色 + P1 BDD-16/17 + P2 §1.1 M13-15/§4.4/§6.1b/§12 + P3 batch5 + 两份红灯测试 + 退役对象 `ci-gate-backstop.py` 及其测试。
- 红灯基线：`test_agate_ci_verify.py` + `test_agate_doctor.py` → 14 failed（模块未实现 + workflow/文档未同步）。
- 决定：**删除** `ci-gate-backstop.py`（BDD-16/P2「替换/退役」口径），同步其全部引用面（锚点/extras/callers/README/summary/6 协议文档/formatters README/workflow + 4 个既有测试面）。
- 实现落点见 `P4-implementation-batch5.md`；新增 `agate-ci-verify.py`（无参数 + cwd 定位 + 实际重跑 check-gate.py + SKIP 显式）与 `agate-doctor.py`（4 维度 + 修复指引 + rc 固定 0）。
- 自跑：14 passed；相邻 361 passed；全量单元仅 1 既有环境失败；consistency 0 ERROR / 406 WARNING（不变）；structure OK；ruff 绿；平台扫描新脚本 0 命中；count-tests 2671。
- [DESIGN_GAP] ×5（接口定位 / doctor 退出码语义 / 未移植 provenance+P3-TDD-red 兜底 / formatters README 补入退役面 / job 名）。
