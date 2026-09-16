---
phase: P1
task_id: TAG0035
parent: P1-requirements.md
trace_id: TAG0035-P1-review-20260916
agent: requirements-review
type: review
created: 2026-09-16
status: approved
---
# P1-review — TAG0035 gate 健壮性批（requirements-review 独立评审）

> 独立复现记录见 `agate-workspace/tasks/TAG0035-gate-robustness/P1-progress.md`（本 agent 追加的分阶段落盘）。

## BDD 评审

- BDD-1: 判定 PASS（可二值判定，Given/When/Then 完整，验证命令给出退出码断言）+ <覆盖维度：数据✓ 前端N/A 多端✓（明确点名 pre-commit-gate.py/ci-gate-backstop.py 消费点）边界✓（未知阶段名）兼容✓（"不再是2"显式声明与旧行为的差异）>。已独立复现：`timeout 30 python3 agate/scripts/check-gate.py P99 agate-workspace/tasks/TAG0035-gate-robustness; echo "exit=$?"` 实测 `exit=2`（当前未修复状态，与 BDD 描述的"修复前"现状一致）。
- BDD-2: 判定 PASS + <覆盖维度：数据✓ 多端✓（显式要求验证 ci-gate-backstop.py 比对逻辑不因退出码语义变化而异常）边界✓ 兼容✓>。
- BDD-3: 判定 PASS（复审：验证命令已补齐 integration 分片并对齐 HANDOFF §4/BDD-7，见「跨条一致性」节）+ <覆盖维度：数据✓ 边界✓ 兼容✓（回归不变性核心 BDD）>。
- BDD-4: 判定 PASS + <覆盖维度：数据✓（正则输入边界）边界✓（非数字阶段名）兼容✓（与子批A取向一致，显式声明）>。
- BDD-5: 判定 PASS + <覆盖维度：数据✓ 边界✓ 兼容✓（"非零退出码"未锁定具体数值，留给 P2/P3 定案，符合 P1 纯净性）>。
- BDD-6: 判定 PASS + <覆盖维度：数据✓ 边界✓ 兼容✓（未预设修复点在 `_phase_num` 内部还是上游 `_P_OUTPUT_RE`，符合"隐含需求识别"第4条的根因分析结论，未越界写实现细节）>。
- BDD-7: 判定 PASS + <覆盖维度：数据✓ 多端✓ 边界✓ 兼容✓（验证命令与 HANDOFF §4 全量三分片命令逐字一致，已核对）>。
- BDD-8: 判定 PASS + <覆盖维度：数据✓ 边界✓（跨 commit 场景）兼容✓（"具体判定机制由 P2 设计"，未越界）>。
- BDD-9: 判定 PASS + <覆盖维度：数据✓ 边界✓（回退场景状态组合）兼容✓>。
- BDD-10: 判定 PASS（红灯边界成立，见下方专节）+ <覆盖维度：边界✓（与 BDD-8/9 互斥声明清晰："不满足 BDD-8/BDD-9 任一豁免条件"）兼容✓>。
- BDD-11: 判定 PASS（复审：上游"同类扫描"完整性缺口已闭合，见「同类扫描核对」）+ <覆盖维度：数据✓ 边界✓（子串匹配无路径边界）兼容✓（要求验收覆盖两个同构文件名）>。
- BDD-12: 判定 PASS + <覆盖维度：数据✓ 多端✓（要求同步 dispatch-protocol.md + P6 卡，纳入 packages: agate-docs）边界✓ 兼容✓>。
- BDD-13: 判定 PASS + <覆盖维度：数据✓ 边界✓（裸文件名 vs 带前缀引用）兼容✓>。
- BDD-14: 判定 PASS（红灯边界成立，见下方专节）+ <覆盖维度：边界✓（与 BDD-11 互斥声明清晰："协议规格文档引用" vs "任务自己产出文件的引用"）兼容✓>。

## 隐含需求覆盖

- 数据维度：覆盖（隐含需求1"回归不变性"、隐含需求3"三处正则形态不同、不可复用同一patch"均已转化为独立 BDD）
- 前端维度：不适用（domains 不含 frontend，正文第9点已显式说明理由，非空白遗漏）
- 多端维度：覆盖（隐含需求2"退出码语义变化的下游一致性"已转化 BDD-1/BDD-2；隐含需求4的根因分析定位到 pre-commit-gate.py 上游过滤层）
- 边界维度：覆盖（隐含需求5"判据放宽边界必须可验证"→BDD-8/9/10；隐含需求6"加固不能连带放松"→BDD-14）
- 兼容维度：覆盖（隐含需求6 + BDD-3/7 的既有阶段行为不回归声明）

## 审声明（风险分级/裁剪声明 vs diff 证据）

- `risk_level: medium` / `phases` 全阶段不裁剪 vs 暂存区实际改动：本轮为 P1 阶段，暂存区尚无代码 diff（仅 P1-requirements.md 等文档产出），无法用 `git diff --cached` 直接核对"代码规模"，但风险声明依据的是 P0-brief 已锁定的范围（5个协议脚本、跨P1-P8全阶段判定影响面），文件类型/规模/域与 P0-brief scope 一致，`risk_level: medium` 与"改核心 gate 脚本 + 影响面覆盖全阶段判定"的量级匹配（参照 TAG0031/TAG0034 先例），未见虚报或漏报。判定：**匹配**。
- `ceremony`：未声明（frontmatter 无 `ceremony` 字段）→ 按 fail-closed 规则落 `standard`，不适用 thin 档四要素 checklist，也不适用 `ceremony: full → phases 含 P7` 校验（本任务非 full）。`phases` 恰好也含全部 P1-P8（含 P7），即便按最严格档位要求校验也满足，无风险。判定：**通过（不适用/n.a. 但结果性满足）**。

## 同类扫描核对（复审更新，见下方「复审记录」）

- 子批 A（`grep -rn "sys.exit(2)|return 2\b" agate/scripts/check-*.py`）：已独立复现，实测总命中 26 处，`check-gate.py` 占 14 处，其余 10 个文件占 12 处，`ls agate/scripts/check-*.py` 实测共 22 个脚本文件——三个数字均与正文陈述**完全一致**。判定：**扫描可复现，结论可信**。
- 子批 C（`grep -n "diff.*--cached.*--name-only|--cached" check-gate.py` + `grep -n "^def gate_p"`）：已独立复现，命中行 952-953 落在 `gate_p4`（928行起）、1400/1418/1437 落在 `gate_p8`（1353行起），其余 8 个 `gate_pN` 函数体内均无 `--cached` 出现——与正文"仅 `gate_p4`/`gate_p8` 使用暂存区快照判据，`gate_p8` 已有双路径回看+WARNING降级不构成同类风险"的结论**完全一致**。判定：**扫描可复现，结论可信**。
- 子批 D：**首轮发现的完整性缺口已修复**（详见「复审记录」），修订后的表格对 `p6-acceptance.md`/`p4-implementation.md`/`p4-review.md` 三个 basename 逐一重新执行 `find . -iname "<basename>" -not -path "*/agate-workspace/tasks/*"`，本 agent 独立复现 `p6-acceptance.md` 一条：实测 8 处命中，与正文表格（1 phase-cards + 5 fixtures + 2 archived = 8）**逐字一致**（`p4-implementation.md`=7、`p4-review.md`=1 两条数字与上轮本 agent 已亲自跑出的结果一致，未见变化，未重复验证）。三类判定（phase-cards→处理并入BDD-11；archived→不处理，理由含"不会引用不相关历史任务的归档产出"+"即便误引用，拦截也是保守正确行为，非误伤"+"BDD-11豁免精确限定phase-cards前缀不会误扩"三层论证；fixtures→不处理，理由含"测试基础设施固定数据非真实协议/角色文档"+"扩大豁免到fixtures前缀反而可能被用作绕过黑名单的构造路径"两层论证）均给出具体、可站住脚的理由，无空白项。判定：**通过，完整性缺口已闭合**。
- 子批 B：派发指引已明确"P0-brief 阶段完成，P1 正文有引用即可，不需要重新扫描"，正文确有引用（"沿用 P0-brief 已裁定的三处定位"），判定：**符合派发指引，不要求本轮重新扫描**。

## 复审记录（2026-09-16，第二轮）

analyst 已针对上轮 needs-revision 的两处发现提交修复，本 agent 复核如下：

1. **子批D同类扫描补全**：P1-requirements.md「5. 同类扫描」子批D一节已重写，对三个 basename 逐一重新跑 `find` 并按 phase-cards/archived/fixtures 三类逐条给出处理判定。独立复现 `find . -iname "P6-acceptance.md" -not -path "*/agate-workspace/tasks/*"`：实测 8 处命中（`agate/phase-cards/P6-acceptance.md`、`agate/tests/fixtures/{full-task,high-risk,paused-task,ui-affected,vision-blocked}/P6-acceptance.md` 共5处、`agate-workspace/archived/tasks/T001-v2.0-structured/{.archived/20260810-085926-P6/,}P6-acceptance.md` 共2处），与正文表格完全一致。三类判定理由具体、非空泛（archived类给出三层论证，fixtures类给出两层论证），满足「同类扫描（强制节）」"每个命中标处理/不处理+理由""空白不算做过"的要求。**判定：完整性缺口已闭合，问题解决**。
2. **BDD-3验证命令口径**：正文 BDD-3 验证命令已补齐 `agate/tests/integration/` 分片，与 BDD-7、HANDOFF-TAG0035.md §4 三分片命令逐字对齐，并附具体理由（"`check-gate.py` 是被 `pre-commit-gate.py` 调用的核心判据脚本，integration 用例可能间接覆盖到 gate 判定，不预先假设无关"）。**判定：口径不一致问题已解决**。
3. **collateral check**：`grep -c '^#### BDD-' P1-requirements.md` 仍为 14，BDD 编号连续未变；BDD-11 的 Given/When/Then 文本未被本次修改影响。未发现修复动作对其余 12 条已 PASS 的 BDD 产生连带影响。

## 红灯边界 BDD 核对

- BDD-10 vs BDD-8/9：Given 场景显式写"不满足 BDD-8/BDD-9 任一豁免条件"，与 BDD-8（跨 commit 有历史代码）、BDD-9（回退后修复）在场景描述上互斥、不重叠，能真正起到边界验证作用。判定：**成立**。
- BDD-14 vs BDD-11/12/13：Given 场景显式写"确实直接引用了该任务自己产出的 P6-acceptance.md（verifier 自述场景，真实信息隔离违规，而非协议规格文档引用）"，与 BDD-11（协议规格文档路径引用）在场景语义上互斥（"自己产出的文件"vs"协议规格文档"），能起到边界验证作用。判定：**成立**。BDD-14 未覆盖 BDD-12/13（白名单补齐角色文件/裸文件名）维度的对称红灯用例，但 BDD-14 聚焦的是黑名单（子批D①最核心的自述场景），BDD-12/13 是白名单扩展，两者风险性质不同（白名单扩得过宽的红灯风险更多体现在"错误放行本不该放行的路径"，本身已被 BDD-13 的"仍需真实存在于 P6-evidence/ 目录"这一限定间接约束），未强制要求专属红灯，不构成缺陷。

## BDD 跨条一致性（含验证命令口径核对，复审已解决）

- 复审前：BDD-3 verification 命令仅含 unit + regression 两片，比 HANDOFF-TAG0035.md §4 与结构对应的 BDD-7（unit+regression+integration 三片）少一片，且未给出理由。
- 复审后：BDD-3 verification 命令已补齐 `agate/tests/integration/` 分片，与 BDD-7、HANDOFF §4 逐字对齐，并附具体理由（`check-gate.py` 被 `pre-commit-gate.py` 调用，integration 用例可能间接覆盖 gate 判定，不预先假设无关）。已读取 P1-requirements.md 76-80 行确认修改落地。
- 判定：**通过，口径不一致问题已解决**。

## 裁剪评审（本任务无阶段裁剪）

- `phases: [P1, P2, P3, P4, P5, P6, P7, P8]`，正文第6节「裁剪说明」逐阶段给出不裁剪理由（P2/P3/P4-P6/P7/P8 各有专门说明），无阶段被跳过。核对：**理由充分，成立**。

## P1 纯净性核查

- 通读全部14条 BDD 与「隐含需求识别」章节：BDD 表述均为"退出码/stderr是否包含特定文本/pytest是否绿"等用户可观测行为断言，未见"改哪个函数""用哪种数据结构"等实现细节写入 BDD 判据本身；具体机制（如子批C的判定方式、子批B的修复层级）均显式标注"由 P2/P3 设计"。判定：**纯净，无解决方案design混入**。

## 结论

status: **approved**

第一轮（needs-revision）指出的 2 处缺口均已由 analyst 修复并经本 agent 独立复核确认：
1. 子批D「5. 同类扫描」的 `find` 命中报告不完整问题——已重写为对三个 basename（`p6-acceptance.md`/`p4-implementation.md`/`p4-review.md`）逐一重新扫描、按 phase-cards/archived/fixtures 三类逐条给出处理判定，本 agent 独立复现 `p6-acceptance.md` 一条命令得到 8 处命中，与正文表格逐字一致；三类判定理由具体、非空泛。**已解决**。
2. BDD-3 验证命令与 HANDOFF §4/BDD-7 口径不一致问题——已补齐 `integration` 分片并附具体理由。**已解决**。

复审未发现新问题，且确认修复动作未对其余已判 PASS 的 12 条 BDD（BDD-1/2/4/5/6/7/8/9/10/12/13/14）、隐含需求覆盖、裁剪说明、P1纯净性、红灯边界（BDD-10/14）、审声明（risk_level/ceremony）产生连带影响（BDD 总数仍为 14，编号连续，其余 BDD 文本未被触碰）。14 条 BDD 全部判定 PASS，覆盖维度（数据/前端N-A/多端/边界/兼容）均已逐条标注，同类扫描三处（子批A/C/D）均可复现且结论可信，P0-brief 时效性质疑格式合规，frontmatter 声明（risk_level/phases/packages/domains）自洽。判定：**approved**。
