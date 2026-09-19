[script] 读完 dispatch-context + 角色文件
[docs] 读完 dispatch-context + 角色文件
[script] 读完 P1(71 BDD+口径A-H) + P2-design
[docs] 读完 P1 BDD-1..12/57-71 + 口径
[docs] 读完 P2-design（§0.1 M1-M18/§3/§7/§13）
[docs] 读完 conftest/风格参照/check-gate；决策：基线比对用固定 SHA efb113b（非 HEAD），git-diff 类由 P5 key 承担
[script] 读完 conftest/AGENTS 测试约定/check-platform-assumptions 规则(R2 裸 python3 / R4 /tmp 字面量)；设计要点：所有用例经 run() 断言 SCRIPT 存在=文件缺失式红灯；可解析命令用 git（sys.executable 路径含空格风险）；BDD-56 登记 P6 证据
[docs] 设计定稿：文档字面标记按 section 提取；基线比对不用 git（避免永久回归时间炸弹，改嵌入 28 术语/4 硬规则字面）；git-diff 类由 P5 key/P6 证据承担；开始写测试文件
[script] test_check_mvwu.py 已写出（约 60 用例函数），开始自检
[docs] 测试文件已写，开始自检
[docs] 自检完：65 用例收集，28 红（全为断言失败）/37 绿（守护类），ruff 0 error；开始写映射表
[script] 原型对拍（scratchpad 内临时实现，未入库）109/109 通过 => 测试 helper 自洽；仓库内当前 109 全红(全为脚本缺失断言)；ruff 0；platform-assumptions 扫描 0。开始写主映射
[script] 主映射 P3-test-cases.md 完成（71 行）；自检全过：可收集 109 / 全红=脚本缺失断言 / ruff 0；无歧义上报；未 git add
[docs] 完成：65 项 28 红/37 绿，映射表已写
