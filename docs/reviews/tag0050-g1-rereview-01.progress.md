# TAG0050 P4 G1 聚焦复审（第 3 轮整改后）进度

- 角色：review（偏执 Staff Engineer）
- dispatch-context：`P4-dispatch-context-review-G1-rereview.md`
- 对象：G1 未提交改动，HEAD `b0a16c3a`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0
- 仓外副本：`/tmp/opencode/tag0050-rr3`（rsync 排除 site/archived/node_modules，含 .git）
- [PROD_NOT_TOUCHED]

## 进度

- [x] 读 review.md 角色 + dispatch-context + 两份首轮评审（review/cso）+ P4-implementation-G1 + progress
- [x] 读 agate-ci-verify.py / check-obligations.py / test_tag0050_obligations.py /
      test_tag0050_ci_replay.py / test_tag0050_obligation_behavior.py
- [x] 复制仓外副本（首轮不含 .git 致协议解析偏移，重做为含 .git 的忠实副本）
- [x] 跑 G1 验收测试集 → 34 passed；127 passed（enforcement+ci_verify+pre_commit）；183 passed（回归）
- [x] K1 独立负向：evil merge 删账本 → FAIL rc=1；再证因果（账本检查加 --no-merges → SKIP rc=0）
- [x] K1 附加：git mv 账本（源路径）→ FAIL
- [x] K2 独立负向：删执行分支 → 真实行为 `test` 转红（基线绿 / 变异红）
- [x] K4 复核：_ci_level_checks + bdd_30/bdd_30b；真实历史 level_errors=[]
- [x] K5/K6 复核：docstring 降级 + DESIGN_GAP；P4-implementation-G1 §K6 advisory
- [x] consistency（真仓）0 ERROR / 410 WARNING；ruff All passed；platform rc=0
- [x] 发现：`_ci_ledger_checks` 账本路径过滤过宽（把 `agate/tests/fixtures/**/gate-events.jsonl`
      当真实账本 → 误报）——经 1 轮副本比对确认**非本批引入**（pre-fix3 同缺 tasks 前缀）
- [x] 写产出 P4-review-rereview-G1.md
