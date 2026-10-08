# level-1 黄金 fixture — pass
#
# 本目录是一组"应当通过"的任务数据样本（设计 §2.1 冻结规则 2）。
# 每个已登记等级保存一组 pass/fail 黄金 fixture；CI 对全部已登记等级逐一运行，
# 判定结果不允许变化——用于在代码层拦住"改了渲染或判据，导致在途任务被追溯"。
#
# level-1 样本特征（契约数据见 ../../../rules/task-data/level-1.yaml）：
# - 账本首行 task_created，contract_level = 1（当前等级）；
# - 等级只升不降：无 task_upgraded，或 to_level 严格递增；
# - requires.judge = true、requires.evidence_ref = true。
level: 1
verdict: pass
