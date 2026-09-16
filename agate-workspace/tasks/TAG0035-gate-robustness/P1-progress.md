# P1 Progress — TAG0035 analyst

- [读完] analyst.md 角色定义
- [读完] P1-dispatch-context-analyst.md（4子批目标/约束/客观查证信息）
- [读完] P0-brief.md（4子批范围、known_risks、env_constraints）
- [读完] HANDOFF-TAG0035.md（双工作区纪律、验证命令、阶段推进纪律）

- [跑完] `python3 agate/scripts/check-gate.py P99 agate-workspace/tasks/TAG0035-gate-robustness` 复核（预期 <10s，实测秒级）：确认 exit=2，stderr "未知阶段: P99"，与 P0-brief 一致
- [读完] check-gate.py 920-990（_gate_p4）、1440-1495（main/handlers/回退检测）
- [读完] check-state-transition.py 195-225（phase_num）
- [同类扫描A] `grep -rn "sys.exit(2)\|return 2\b" agate/scripts/check-*.py`（预期<10s）：22 个 check-*.py 脚本中命中 26 处（check-gate.py 占 14 处），check-gate.py 外 12 处逐条读上下文：check-debt.py:67（依赖加载失败，注释自陈"需主 Agent 自判"）、check-p6-evidence.py:135/312/367（P6 文件缺失/像素方差 WARNING，非阻断约定）、check-p6-provenance.py:573（warning_found 汇总）、check-platform-assumptions.py:134（目标不存在 FATAL exit 2——注意：这条是"目标不存在"用 exit 2 而非 exit 1，需在正文标注为观察项）、check-protocol-consistency.py:1436（--strict 下 WARNING 计数）、check-pruning.py:143/check-routing.py:77/check-scope-resolved.py:80/check-state-yaml.py:44（均为"P1/任务目录缺失→exit 2"，与 check-routing.py 77 行注释自陈的"对齐同链 check-pruning；与不声明=standard 的 exit 0 区分"同一约定）、check-tdd-red.py:108（exit_code==0 时 WARNING）。结论：均为"exit 2 = WARNING/前置文件缺失"既定约定，语义上与真实 pass(exit 0)/fail(exit 1) 区分明确，不构成"未知枚举值静默判等同已知通过码"同构问题；额外用 grep 确认无第二个 handlers.get()/dispatch-dict 模式（`grep -rn "handlers\s*=\s*{" agate/scripts/check-*.py` 只命中 check-gate.py 本身）
- [读完] check-judge-verdict.py 全文（545 行）
- [同类扫描D] 核对 `_BLACKLIST_MD = {"p6-acceptance.md","p4-implementation.md","p4-review.md"}` 的子串匹配方式（`if exact in low`，`low` 为两节全文小写拼接，无路径边界）：`find . -iname "P4-implementation.md" -not -path "*/agate-workspace/tasks/*"` 命中 agate/phase-cards/P4-implementation.md（协议阶段卡片，非 verifier 自述）——与 P0-brief 已知①（p6-acceptance.md 命中 agate/phase-cards/P6-acceptance.md）**同构**，是第二个实例；`find . -iname "P4-review.md" -not -path .../tasks/*` 未命中任何 phase-cards/协议文档（无同构风险）。结论：新增发现并入①的修复与回归测试范围（同一路径豁免机制天然覆盖两个文件名，不新增设计点/BDD），验收测试须显式覆盖 p4-implementation.md 这个第二实例，防止只修 p6-acceptance.md 一个文件名的窄修复

- [写完] P1-requirements.md（14 条 BDD 全局编号，子批A=3/B=4/C=3/D=4；frontmatter 用 agate-md-field-set.py 逐字段写入，agent 字段因工具设计拒绝手动 set 而手工补一行）
- [跑完] `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0035-gate-robustness/P1-requirements.md` → exit=0
- [完成] 无 [NEED_CONFIRM]（写 [NO_NEED_CONFIRM]，附 1 条 [SUGGEST] 关于子批B完整案独立立项）；已核对 P0-brief 时效性无漂移；同类扫描A/D 均已完成并落盘（D 扫描新发现 p4-implementation.md 同构假阳性实例，已并入 BDD-11）

- [补充] 主 Agent 复核反馈：子批C同类核查（P0-brief 原文要求"其它 phase 完整度判据是否共用看暂存区假设"）遗漏，未单独成节
- [跑完] `grep -n "diff.*--cached.*--name-only\|_STAGED_EXCLUDE_RE\|--cached" agate/scripts/check-gate.py`（预期<5s）+ 逐函数定位（gate_p0~gate_p8+gate_p65 共10个）：仅 gate_p4（953-961，无回看+硬return 1）与 gate_p8（1400/1418/1437，已有暂存区+lookback commit回看双路径+WARNING降级）命中"--cached"；其余8个函数不使用暂存区判据
- [判定] gate_p8 设计已规避该风险（回看fallback+非阻断WARNING），不构成同类实例；结论=确认只此一处（gate_p4），不新增BDD，已并入《5.同类扫描》新增"子批C"小节，BDD-1~14 编号未变动
- [跑完] check-frontmatter.py 复核 → exit=0，BDD 计数仍为14

## [requirements-review] 读取进度
- 已读：requirements-review.md（角色定义）
- 已读：P1-dispatch-context-requirements-review.md（派发指引，8条约束）
- 已读：P0-brief.md（范围基线）
- 已读：P1-requirements.md（评审对象，14条BDD）
- 已读：HANDOFF-TAG0035.md（验证命令口径）
- 下一步：读 check-gate.py / check-judge-verdict.py 关键行号，跑独立复现命令

## [requirements-review] 独立复现结果
1. BDD-1 复现：`python3 agate/scripts/check-gate.py P99 ...` → 实测 exit=2（与正文一致，当前未修复状态符合预期）
2. 子批A同类扫描复现：`grep -rn "sys.exit(2)|return 2\b" agate/scripts/check-*.py` → 总命中26处，check-gate.py占14处，其余10个文件占12处，文件总数22个 —— 与正文数字完全一致
3. 子批C同类扫描复现：`grep -n "diff.*--cached.*--name-only|--cached" check-gate.py` 命中行952-953(gate_p4)/1400/1418/1437(gate_p8) —— 与正文"仅gate_p4/gate_p8使用--cached"结论一致
4. 子批D同类扫描复现发现不一致：`find . -iname "P4-implementation.md" -not -path "*/agate-workspace/tasks/*"` 实际命中7处（1处phase-cards + 5处agate/tests/fixtures/*/P4-implementation.md + 1处archived任务），正文只报告并处理了1处（phase-cards），遗漏6处未逐条判定 —— 判定：同类扫描完整性有缺口，需修订
5. BDD编号连续性核实：grep确认BDD-1~14连续不跳号，14条
6. judge.enabled核实：.state.yaml确认judge.enabled:true；judge_required_since=2026-08-22 < created 2026-09-16，机制强制声明成立
7. BDD-3验证命令与HANDOFF §4比对：BDD-3只含unit+regression两片，缺integration分片；结构对应的BDD-7含unit+regression+integration三片，与HANDOFF §4完全一致 —— BDD-3/BDD-7不一致，且BDD-3与HANDOFF §4口径不完全一致
8. 结论：发现2处needs-revision级问题（子批D同类扫描完整性缺口 + BDD-3验证命令与HANDOFF/BDD-7不一致），正在撰写P1-review.md

- [补充2] requirements-review needs-revision 两处修复：① 重跑 find 对 p6-acceptance.md(8处)/p4-implementation.md(7处)/p4-review.md(1处) 全量核实，按 phase-cards(处理,并BDD-11)/archived(不处理,理由已写)/fixtures(不处理,理由已写) 三类逐条判定，写入子批D同类扫描小节；② BDD-3 补齐 integration 分片，与BDD-7/HANDOFF§4三片口径对齐
- [跑完] check-frontmatter.py 复核 → exit=0，BDD计数仍14（未新增/未打乱编号）
