[review] 读 review.md + dispatch-context
[align] 读 diff + check-mvwu.py 全文（已读）
[review] 读 check-mvwu.py 全文 + P1 口径 A-H
[align] pytest 全量: 1 failed(BDD-71 预期) 1839 passed 2 skipped; 读 P4-implementation.md/design-note I1
[review] 哨兵/audit hook 实测进行中(tmp)
[review] 实测: 哨兵未执行/无写文件/id 特殊字符/verdict 边界完成；发现 observe duration 超长数字异常吞行
[align] 读 A 组 diff(CHANGELOG/CONTEXT/adr/architect/task-files/P2/P4/P7/role-system/README/M18)
[review] 重派: 已重读 check-mvwu.py; 开始复现 duration 吞行
[review] - 关键: 复现成功 5000 位纯数字 duration_seconds -> ValueError(int str limit) 逃出 print 循环, 落 main 兜底; 该批及其后批丢失, 输出行数<批数
[align] 零内核 diff 核对: kernel_wt/roles/history 已跑; A3b 全库 grep 完成
[review] 重派: 哨兵/特殊 id/符号链接/BOM/CRLF 已重测(全 OK); 下步 verdict 边界 + task_dir 边界 + git -z
[review] 重派: verdict 27 边界用例实测完成(全符合)，待核 口径 A-H 对照(+0/重复键/大写sha)
[align] pytest 复跑(1 failed=BDD-71 / 1839 passed / 2 skipped); ruff/consistency/platform/debt/check-mvwu 冒烟完成; 发现 CONTEXT boundary(I1) 用 PASS/FAIL 而脚本 exact/mismatch
[review] 重派: task_dir(-x/空格/不存在/文件/无git/git不在PATH/P2 损坏) 实测完成
[review] 重派: git -z(空格/非ASCII/换行名)/merged/exact/tasks 前缀排除 实测通过; 下步 M18/范围/文档
[review] 重派: M18(仅+1行)/范围(无 .sh、测试仅注释修订)/小文档 diff 已核; 待 P2/P4 卡、architect、CHANGELOG diff + check-debt
[review] 重派: NUL 命令/case-insens id/符号链接证据目录/无 reconfigure 实测完成; 开始写 P4-review.md
[review] 重派: P4-review.md 已写出 (approved, 0 BLOCKER, 1 MAJOR)
