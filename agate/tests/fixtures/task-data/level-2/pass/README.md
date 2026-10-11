# level-2 黄金 fixture — pass
#
# 本目录是一组"应当通过"的任务数据样本（设计 §2.1 冻结规则 2）。
# 每个已登记等级保存一组 pass/fail 黄金 fixture；CI 对全部已登记等级逐一运行，
# 判定结果不允许变化——用于在代码层拦住"改了渲染或判据，导致在途任务被追溯"。
#
# level-2 样本特征（契约数据见 ../../../rules/task-data/level-2.yaml，经 extends 链
# 合并 level-1 后登记于 LEVELS.yaml）：
# - 账本首行 task_created，contract_level = 2（新契约级）；
# - 等级只升不降：无 task_upgraded，或 to_level 严格递增；
# - 在 level-1 要求（judge / evidence_ref / prod_touched / results）之上，
#   追加 P8 交付声明 method 的取值域收紧（delivery.method_enum）。
level: 2
verdict: pass
