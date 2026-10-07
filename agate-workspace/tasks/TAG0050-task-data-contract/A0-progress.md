
## A0 implementer 进度（implementer subagent）

### 已读输入
- `implementer.md`（角色定义）、`A0-dispatch-context-implementer.md`（强制派发指引）
- `agate_common.append_event` 实际签名：`def append_event(task_dir, event)`（2 参，event 为 dict）
- 验收测试 `agate/tests/integration/test_tag0050_a0_a1_ledger.py`（BDD-01/02 属 A0；BDD-03..22 属 A1）
- P2-design §10 G1 / §2.4：A0 落点 = `check-gate.py main()` 单点早检（分派之前），所有 phase 统一 rc=1

### 改动 1（F8）
`agate/scripts/pre-commit-gate.py` PAUSED 留痕分支（原 `:370`）：
- 旧：`append_event(task_dir, "prod_touched_in_paused", {"task_id": task_id})`（3 参 → TypeError 被吞）
- 新：`append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})`

### 改动 2（check-gate 不存在目录 rc）
`agate/scripts/check-gate.py` `main()`：在参数解析后、`handlers` 分派前新增单点早检：
`if not os.path.isdir(task_dir): stderr + sys.exit(1)`
→ P7/P5/P0/P6.5/未知 phase 对不存在目录统一 rc=1（消除 P7→0 假 PASS、P5→2）。

### 平台无关自查
两处改动均为纯逻辑，无裸 `python3` / 硬编码 PATH / 系统临时目录字面量（注释亦无）。

### 自查结果（非 gate）
- `pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q` → 4 passed（BDD-01 + BDD-02×3），其余 A1 用例仍红（预期）
- 手动：`check-gate.py <phase> <不存在目录>` P7/P5/P0/P6.5/P99 均 rc=1
- 回归抽跑：test_check_gate / test_check_p8_delivery / test_gate_layer / test_t41_platform_hygiene / test_tag0027_b1_phases_transfer_fields / test_agate_config → 255 passed

### 补充验证
- 全量 `pytest agate/tests -q -n auto`：79 failed / 2672 passed / 2 skipped。
  79 failed 中 78 为 TAG0050 A1/A2 批的预期红灯用例；余 1 为
  `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
  —— 本机 opencode CLI 子命令由 `debug agent` 变为 `debug agents` 导致的环境性失败，
  **与本次改动无关**（未触及 setup/opencode 代码路径）。
- `ruff check`（~/.venvs/agate-dev/bin/ruff）两文件：All checks passed（行宽 99 < 120）。
- `check-protocol-consistency.py`：0 ERROR（441 WARNING 均为冻结文件，按设计不收敛）。

### 环境隔离
[PROD_NOT_TOUCHED]
