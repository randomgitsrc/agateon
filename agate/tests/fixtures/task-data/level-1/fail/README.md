# level-1 黄金 fixture — fail
#
# 本目录是一组"应当判 ERROR"的任务数据样本（设计 §2.1 冻结规则 2）。
# 样本特征：账本首行 task_created（等级 1），随后追加一条**降级** task_upgraded
# （from_level 1 → to_level 0）——违反"等级只升不降"（设计 §2.2 事件规则）。
level: 1
verdict: fail
