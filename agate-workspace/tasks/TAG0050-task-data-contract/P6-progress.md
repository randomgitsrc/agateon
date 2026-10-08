---
task_id: TAG0050
phase: P6
agent: verifier
---

# TAG0050 P6 进度记录（verifier subagent）

> 分阶段落盘：每完成一个关键步骤追加。本文件为 verifier 自述，非 gate 判定对象。

## 步骤记录

1. **读输入**：`verifier.md` 角色定义、`P6-dispatch-context-verifier.md`、`P0-brief.md`、`AGENTS.md`、
   `P1-requirements.md`（77 BDD）、`P2-design.md`（批↔BDD、gate_commands）、`P3-test-cases.md`（节点↔BDD）、
   `P4-implementation.md`、`P5-test-results/unit.md`、`known-failures.md`。
2. **口径判定**：查 `.state.yaml` 与账本首行——TAG0050 无 `task_created` ⇒ **legacy 任务** ⇒ P6 走既有口径
   （正文逐条 PASS 行 + frontmatter `pass`/`fail`；provenance 审计 1/3/5/6 生效）。非 legacy 结构化判据 D1–D10
   由 BDD-56 用例在 `init_task()` 构造的非 legacy 任务上验证。
3. **实跑各批验收测试**（13 个 `test_tag0050_*.py`，`-v`）：全部 `passed`，逐批日志落 `P6-evidence/batch-tests/`。
4. **实跑脚本证据**：`check-protocol-consistency.py`（0 ERROR）、`count-tests.sh`（2866）、
   `check-obligations.py`（M 占比 56/119 不低于基线）、`r6-differential.sh`（agateon 39 / agateon+peekview 107 个
   legacy 任务，均 0 差异 0 未匹配）、全量 pytest（2863 passed / 1 预存失败 / 2 skipped）、登记面测试（36 passed）。
5. **负向对照（改坏即红，均在 `/tmp/opencode` 副本）**：删 `r6-allowlist.yaml` 必需规则 D12 → 脚本 exit 1；
   篡改 `level-1.yaml` → consistency CHECK 16 ERROR。
6. **post-test 环境残留检查**：真实仓库 `git status` 仅本 P6 产出；两个 R6 副本跑后干净。
7. **产出**：`P6-acceptance.md`（77 PASS / 0 FAIL）+ `P6-evidence/`（25 个证据文件，均被 PASS 行引用）。
8. **自查（≠gate）**：`check-p6-format.py --fix` exit 0；`check-p6-evidence.py` exit 0；
   `check-p6-provenance.py` exit 2（仅非阻塞 WARNING：3 个负向/含预存失败的日志无 `EXIT_CODE` 尾行 +
   既有 `P1-gate-diagnosis.md` 缺 agent 字段）；`check-gate.py P6` exit 2（FAIL=0, TOTAL=77，WARNING 通过）。
