[PROD_NOT_TOUCHED]
[NO_NEED_CONFIRM]

# P5 全量 pytest 结果（TAG0037，HEAD 467fec7）

命令：`PYTHONDONTWRITEBYTECODE=1 timeout 580s python3 -m pytest agate/tests/ --reruns 1 -n auto`
环境：Python 3.12.3, pytest 9.0.3, xdist 3.8.0, rerunfailures 16.7

第 1 次（无 -rs）：exit 0，耗时 55.74s
2292 passed, 2 skipped in 55.74s

第 2 次（加 -q -rsR 取 skip 原因与 RERUN 记录）：exit 0，耗时 51.49s
2292 passed, 2 skipped in 51.49s

- failed = 0；无 RERUN（--reruns 1 未触发，日志 RERUN 计数 0）；无 flaky。
- 基线口径 passed >= 1842：2292 > 1842（净增 450），满足。
- skipped = 2 （<= 2，满足），原因均为既有 Pillow 分支：
  - agate/tests/unit/test_agate_image_check.py:21 「Pillow 已安装，跳过无 Pillow 分支」
  - agate/tests/unit/test_agate_image_check.py:51 「Pillow 已安装，跳过无 Pillow 分支」
  BDD-43/45（GITHUB_ACTIONS 才 skip）本地未 skip。
- 预存失败：无。
- 未运行全量测试：否（已运行全量）。
- pytest collect-only 总数 2294 = 2292 + 2 skipped，自洽。

原始日志（scratchpad，仓库外）：/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/pytest-full.log, /tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/pytest-full2.log
