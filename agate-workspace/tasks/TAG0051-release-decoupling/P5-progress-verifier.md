# P5 进度（verifier subagent）

> 只读验证：不改代码/测试/协议文件；不 commit / push。产出 = P5-test-results/unit.md + fail-list.txt + known-failures.md。
> 分支 `task/TAG0051-release-decoupling`；P4 已提交（HEAD 9771e76）。
> 状态标记：`[PROD_NOT_TOUCHED]`（无生产环境触达）。

- [命令 P5] 准备跑 `python3 agate/tests/ -q -n auto`（全量回归，预计数分钟，timeout 1800s；走 agate-run 白名单）

- [P5 结果] run:1 = `2 failed, 2957 passed, 2 skipped`（多出 `test_m1_forward_jump_p2_to_p5_blocked` = 已知跨文件 flaky DEBT0063）；run:2 = `1 failed, 2958 passed, 2 skipped`（与主 Agent 预期一致，唯一红 `test_bdd_43` 环境漂移）。隔离单跑该 flaky 用例 = passed。以 run:2 为口径。
- [命令 P5_consistency] 准备跑 `check-protocol-consistency.py`（预计 ~10s，timeout 120s；走 agate-run 白名单）
- [命令 P5_count] 准备跑 `count-tests.sh`（预计 ~2s，timeout 60s；走 agate-run 白名单）
- [命令 P5_ruff] 准备跑 `$HOME/.venvs/agate-dev/bin/ruff check agate/`（预计 ~3s，timeout 60s；走 agate-run 白名单）
- [命令 P5_obligations] 准备跑 `check-obligations.py`（预计 ~3s，timeout 60s；**普通 bash**，白名单外，未经 agate-run/账本路径）
- [命令 P5_sg6] 准备跑 `pytest agate/tests/integration/test_protocol_alignment_review.py -q`（预计 ~20s，timeout 300s；**普通 bash**，白名单外）
- [命令 P5_r6] 准备跑 `r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus`（差分遍历全量 legacy 任务，预计数分钟，timeout 900s；**普通 bash**，白名单外；after 侧 = 真实工作树，P4 已提交）
- [命令 P5_sg6] 完成：exit 0（14 passed）
- [命令 P5_r6] 完成：exit 0（legacy 39 个，差异 2 条，未匹配 0 条；均 [ALLOWED]）；跑前/跑后真实仓库 git status 一致（无污染）
- [产出] 写 P5-test-results/unit.md + fail-list.txt + known-failures.md；签名校验 grep 计数 = 2（>0）；git status 确认无代码/测试/协议文件改动
