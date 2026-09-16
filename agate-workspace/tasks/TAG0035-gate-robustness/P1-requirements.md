---
phase: P1
task_id: TAG0035
type: problems
parent: P0-brief.md
trace_id: TAG0035-P1-20260916
created: '2026-09-16'
status: draft
agent: analyst
risk_level: medium
phases:
- P1
- P2
- P3
- P4
- P5
- P6
- P7
- P8
packages:
- agate-scripts
- agate-tests
- agate-docs
domains:
- backend
---
# P1-requirements — TAG0035 gate 健壮性批（RM-AG0062 归并 + RM-AG0064 并入）

[已核对 P0-brief 时效性，无漂移]：P0-brief 于 2026-09-16 立项，本 P1 同日启动，间隔为 0。对照 P0 卡片「P0-brief 时效性自检」严重 3 条判据逐条排查：① `task` 目标方案（fail-open→fail-closed 判据修复）未变；② `executor_env` 平台前提（worktree + python3/pyyaml + Linux 基线）未变；③ `known_risks` 的"已解决前提"未被他任务解决（TAG0036 尚未启动，与本批文件面不重叠，见 P0-brief 头部「与 TAG0036 的排序关系」）。三条均不命中，无严重漂移；也未发现路径/依赖版本等局部变化，无轻微漂移。

`judge.enabled` 确认：`.state.yaml` 已写 `judge:\n  enabled: true`（P0 立项时完成），本任务 created=2026-09-16 ≥ `agate/rules/dispatch.yaml:17` 的 `judge_required_since: "2026-08-22"`，机制强制要求已满足，本轮无需改动。

`verification_env`：不适用。本批全部验证在 worktree 本地完成（`python3 agate/scripts/check-gate.py ...` 手工调用 / `pytest` 分片跑 / `grep` 静态扫描），无需额外服务、端口、数据库或外部凭据，不存在"环境未就绪"缺口。

## 1. 需求复述

在 agate 协议层，把 gate / check-script 中会**静默通过**（未知/异常输入被判定为与"正常通过"相同的退出码）或**静默失效**（判据前提不成立时无声跳过，不留痕迹）的判据，改为**响应式失败**（fail-closed：无法确定的情况优先报错而非放行），并补齐多提交 / 回退场景下过窄的判据假设。一个任务内分 4 个子批串行交付：

- **子批 A**：`check-gate.py` 对未知阶段名（不在 `handlers` 字典中）当前 `sys.exit(2)`——与 P0/P1/P2/P3/P5/P6/P8 的"通过"退出码相同，导致 CI backstop 的"记录值 == 重跑值"比对被绕过（两边都错得一样就都通过）。改为 `sys.exit(1)`。
- **子批 B**：`check-gate.py`（回退抵达检测）/ `check-state-transition.py`（`phase_num`）/ `pre-commit-gate.py`（`_P_NUM_RE`/`_P_OUTPUT_RE`）三处依赖"阶段名含数字"的假设，遇非数字阶段名（如 `p-alpha`）静默失效（短路 / 回退 0 / 静默跳过）。本批**只做最小案**：非数字阶段名场景下改为显式可观测的失败/提示，不改 `phases.yaml` 语义、不引入 `order`/`predecessors`。
- **子批 C（DEBT0037）**：`_gate_p4` 的"暂存区含非 md/yaml 代码文件"判据在①一个 phase 跨多 commit、②P5→P4 回退后修复 commit 两种场景下误判 `return 1`，需放宽到能识别这两种合法场景，但不能削弱对"纯文档、无代码历史、非回退"场景的拦截。
- **子批 D（DEBT0038）**：`check-judge-verdict.py` 的 judge 信息隔离黑/白名单用**子串匹配**（非路径匹配）导致 3 处假阳性：①黑名单 `p6-acceptance.md` 命中协议阶段卡片路径 `agate/phase-cards/P6-acceptance.md`；②白名单不含角色定义文件路径；③`P6-evidence/` 目录白名单不认目录内裸文件名。

out-of-scope（沿用 P0-brief，本 P1 不重复展开）：`check-gate.py` phase 语义重构 / `handlers` 字典声明式化 / TAG0036 任何内容 / DAG 相关 / DEBT0040（CI workflow 改动需用户许可）/ DEBT0041（字段集同源，与 TAG0036 `tests_filter` 同字段族）。

## 2. 隐含需求识别

1. **回归不变性（数据/兼容维度）**：本批全部修复只应改变"异常/边界输入"路径的行为，**不得**改变 P0-P8 标准数字阶段名 + 正常代码变更场景下的既有判定结果——否则会让存量任务（Linux 现状基线）的 gate 判定发生非预期漂移。为什么必须：这是 pytest 全绿回归底线（HANDOFF §核心约束 1），也是 known_risks 里"三处正则不一致，不能假设可以一次性统一改成同一个正则"的直接推论。已转化为 BDD-2/BDD-7/BDD-10。
2. **子批 A 退出码语义变化的下游一致性（多端维度）**：`exit 2 → exit 1` 会被 `pre-commit-gate.py` 的 `write_gate_result` 记账、`ci-gate-backstop.py` 的"记录值==重跑值"比对、`check-events.py` 等消费 `gate-events.jsonl` 的脚本读取。为什么必须：若下游有代码把"未知阶段 exit 2"当特殊分支处理，改动会产生连锁失效。已用 `grep -rn "handlers\s*=\s*{" agate/scripts/check-*.py` 核实全仓只有 `check-gate.py` 一处 dispatch-dict，`ci-gate-backstop.py` 的比对逻辑是纯粹的"两值相等判断"，不特判具体数值，因此退出码语义变化不会破坏 backstop 自身逻辑——但这一点需要写进 BDD 由 regression 验证，不能只凭代码阅读断言。已转化为 BDD-1/BDD-2（隐含验证点）。
3. **子批 B 三处独立验证，不可复用同一 patch（边界维度）**：三处正则形态不同（`re.search(r"[0-9]+", ...)` vs `re.compile(r"P[0-8]")`，后者大小写敏感且只认单数字 P0-P8），消费点也不同（回退检测 early-exit / 转移合法性判定 / commit-hook 一致性 WARNING，且后者本身只是 WARNING 不拦截 commit）。为什么必须：如果按"三处同类问题→一次性统一正则/统一改法"处理，会把一个"early-exit 快速失败"逻辑和一个"WARNING 不拦截"逻辑混为一谈，可能把非阻断检查错误地改成阻断，或反之削弱了本应阻断的检测。已转化为 BDD-4/5/6 三条独立验收。
4. **子批 B 对 pre-commit-gate.py 的实际失效点比 P0-brief 描述更细一层（根因维度，5 Whys）**：`_phase_num()` 内部的 `if not m: return None` 分支，在当前两处调用点（行 291、576）都是在 `_P_OUTPUT_RE = r"P[0-8]-.*\.md$"` 已过滤过的字符串上调用的——由于该正则本身要求 `P[0-8]-` 子串存在，`_phase_num` 传入这类字符串必然能匹配，`return None` 分支目前实际不可达。真正的静默失效点在**更上游**：`_P_OUTPUT_RE`/其他文件名前缀判断本身只认 `P[0-8]-*.md` 形式，非常规（非数字）阶段名产出的文件**完全不会进入**该 WARNING 检查的候选列表，一致性提示被 0 提示地整体跳过。为什么必须：如果只按 P0-brief 字面描述去"修 `_phase_num` 内部的 None 分支"，改动会打在不可达代码上，实际问题（上游过滤层）不会被修复。已转化为 BDD-6（表述聚焦"该产出文件的一致性检查是否有任何可观测输出"，不预设具体修复点在哪一层，留给 P2/P3 设计）。
5. **子批 C 判据放宽的边界必须可验证（边界维度）**：`known_risks` 已提出"判据放宽若过宽会削弱 gate 拦截力"。为什么必须：DEBT0037 的修复方向本身列了两种可选机制（history 扫描 / 回退状态识别），P1 只声明"哪些场景应该放行、哪些场景仍应拦截"，机制选择留给 P2。已转化为 BDD-8/9（应放行）+ BDD-10（红灯边界，仍应拦截）。
6. **子批 D 加固不能连带放松真实自述场景（兼容维度）**：`known_risks` 已提出"DEBT0038 白名单放宽可能削弱 judge 信息隔离"。为什么必须：①②③ 三处假阳性修复的落点都在"放宽判定"，必须有对称的"仍应拦截"红灯用例兜底，否则加固动作本身可能引入新的信息隔离漏洞。已转化为 BDD-14。
7. **子批 D 的黑名单同类风险不止 1 处（本节详见下方「同类扫描」）**：`_BLACKLIST_MD` 集合中 `p4-implementation.md` 与 `p6-acceptance.md` 共享同一个"子串匹配、无路径边界"的实现，且仓库里确实存在同名的协议阶段卡片 `agate/phase-cards/P4-implementation.md`，构成第二个同构假阳性实例。为什么必须：只按 P0-brief 列出的"① p6-acceptance.md"修，规避了同一段代码里另一个已知会触发的同名文件，属于"只修被报告的那一处"的反模式。已并入 BDD-11 的验收范围（同一路径豁免机制天然覆盖两个文件名，验收测试须显式覆盖两者，不新增设计点）。
8. **测试计数文档同步（procedural，不设专门 BDD）**：HANDOFF-TAG0035.md §4 列出 `bash agate/tests/scripts/count-tests.sh` 作为验证命令之一，用于确认测试数量文档未漂移。为什么必须：本批每个子批都会新增 regression 测试（BDD-2/3/6/7/8/9/10/11/12/13/14 均要求新增测试），若测试计数文档未同步会在 P5/P7 阶段被拦截。这是执行纪律，不是需求缺口，故不单列 BDD，登记在此供 P3/P4 阶段提醒。
9. **无 frontend 域**：本任务全部改动是脚本/协议判据，无用户可见页面、无渲染形态，`domains` 不含 `frontend`，不需要声明 `ui_render_shape`/`ui_ux_dimensions`/UX 类别 BDD（沿用派发指引第 8 条）。

## 3. BDD 验收条件

BDD 编号全局唯一，四个子批依次编号（不各自从 1 编号）。每条含验证命令，作为"改完后跑什么、断言什么"的落地依据（不留白到 P4）。

### 子批 A：未知阶段 fail-closed

#### BDD-1: 未知阶段名 fail-closed
- Given `check-gate.py` 收到一个不在 `handlers` 字典中的阶段名（如 `"P99"`）
- When 执行 `python3 agate/scripts/check-gate.py P99 <task_dir>`
- Then 退出码为 1（不再是 2），且 stderr 输出中包含该未知阶段名文本
- 验证：`timeout 30 python3 agate/scripts/check-gate.py P99 agate-workspace/tasks/TAG0035-gate-robustness; echo "exit=$?"`，断言 `exit=1`

#### BDD-2: 新增 regression 测试锁定未知阶段行为
- Given 测试套件中新增一条针对未知阶段的用例
- When 跑该用例（落在 `agate/tests/unit/test_check_gate.py` 或 `agate/tests/regression/`，具体文件由 P3/P4 决定）
- Then 用例断言 `check-gate.py <未知阶段> <task_dir>` 退出码恒为 1 且 stderr 含阶段名；同时断言 `ci-gate-backstop.py` 的"记录值==重跑值"比对逻辑本身不因退出码语义变化（2→1）而报错或行为异常（隐含需求 2 的验证点）
- 验证：`timeout 60 python3 -m pytest agate/tests/unit/test_check_gate.py -q`（新增用例需在此绿）

#### BDD-3: 已知阶段行为不回归
- Given `check-gate.py` 收到 10 个已知阶段名（P0/P1/.../P8/P6.5）中任一个
- When 正常执行该阶段的 gate 检查（含各阶段既有产出齐全/缺失等既有测试场景）
- Then 退出码与修复前完全一致（各阶段既有的 0/1/2 语义不变），不受未知阶段修复影响
- 验证：`timeout 280 python3 -m pytest agate/tests/unit/ -q -n auto && timeout 280 python3 -m pytest agate/tests/regression/ -q -n auto && timeout 280 python3 -m pytest agate/tests/integration/ -q -n auto` 全绿（与 BDD-7、HANDOFF-TAG0035.md §4「全量测试」三分片口径对齐——`check-gate.py` 是被 `pre-commit-gate.py` 调用的核心判据脚本，`agate/tests/integration/` 中可能存在端到端跑通 commit 流程的用例会间接覆盖到 gate 判定，不预先假设子批 A 的改动与 integration 分片无关）

### 子批 B：非数字阶段名三处静默失效（最小案）

#### BDD-4: check-gate.py 回退抵达检测对非数字阶段名不再静默短路
- Given `check-gate.py` 以三参数形式调用，`old_phase` 或 `phase` 任一为非数字阶段名（如 `"p-alpha"`，`re.search(r"[0-9]+", ...)` 无匹配）
- When 执行 `check-gate.py <phase> <task_dir> <old_phase>`
- Then 脚本不得把"无法解析阶段序号"静默等同于"未发生回退"进而直接放行到该阶段的正常完整度校验；须在 stderr 显式提示"无法解析阶段序号"，并以退出码 1 终止（fail-closed，与子批 A 取向一致）
- 验证：新增单测构造非数字阶段名的三参数调用，断言 exit=1 且 stderr 含"无法解析"或该阶段名原文

#### BDD-5: check-state-transition.py 的 phase_num() 对非数字阶段名不再静默回退为 0
- Given `.state.yaml` 或转移判定输入中的阶段名文本不含数字
- When `check-state-transition.py` 主流程调用 `phase_num()` 做转移合法性判定
- Then 不再静默 `return 0`（会被误判为"退回到最初阶段"），而是在 stderr 显式提示"无法解析阶段序号"并使脚本以非零退出码终止
- 验证：新增测试构造非数字阶段名场景，断言 `check-state-transition.py` 退出码非 0 且 stderr 含"无法解析"字样

#### BDD-6: pre-commit-gate.py 对非常规阶段名产出文件的一致性 WARNING 不再完全无痕跳过
- Given 任务采用非常规（非 `P[0-8]-` 前缀）阶段名产出的文件被暂存（如某任务实际使用了自定义阶段名对应的产出文件）
- When `pre-commit-gate.py` 执行「phase-产出一致性检查」（现有 2f 节 + 第 3 节，均为 WARNING 性质、不拦截 commit）
- Then 该产出文件不应在数字假设的过滤/提取逻辑下被完全过滤掉、连一条提示都不产生；至少应在 stderr 产生可观测提示（如"无法识别该产出文件的阶段号，一致性检查未覆盖"），不允许 0 输出地悄然跳过
- 验证：新增 regression 测试构造非常规阶段名产出文件被暂存的场景，断言 `pre-commit-gate.py` 的 stderr 输出中出现对应提示（而非当前的完全无输出）

#### BDD-7: 三处判据修复对标准数字阶段名（P0-P8）行为不回归
- Given `check-gate.py` 回退检测 / `check-state-transition.py` phase_num / `pre-commit-gate.py` 的阶段号提取，输入均为标准数字阶段名
- When 跑全量测试
- Then 三处对 P0-P8 标准阶段名的既有行为（回退检测触发条件、转移判定结果、一致性 WARNING 触发条件）与修复前完全一致
- 验证：`timeout 280 python3 -m pytest agate/tests/unit/ -q -n auto && timeout 280 python3 -m pytest agate/tests/regression/ -q -n auto && timeout 280 python3 -m pytest agate/tests/integration/ -q -n auto` 全绿

### 子批 C：DEBT0037（_gate_p4 完整度判据）

#### BDD-8: 一个 phase 跨多个 commit 交付时不再误判"当前 commit 无代码"
- Given 某任务的 P4 阶段跨多个 commit 交付，其中至少一个更早的 commit 已引入过非 md/yaml 代码 diff，当前待检查 commit 的暂存区只含 md/yaml 文件
- When 对当前 commit 执行 `check-gate.py P4 <task_dir>`
- Then `_gate_p4` 不再仅凭"当前暂存区无代码文件"就判定完整度不足（`return 1`）；本 phase 是否已引入过代码变更的判定范围应覆盖该 phase 的历史提交，而不仅是当前暂存区快照（具体判定机制由 P2 设计）
- 验证：新增 regression 测试模拟"两次 commit 完成同一 P4 阶段"，断言第二次纯 md commit 不再被误判 `return 1`（其余既有判据仍需满足）

#### BDD-9: P5→P4 回退后修复 commit 不再误判
- Given `.state.yaml` 的 `retries[P4]` 非空（发生过 P5→P4 回退）且此前已存在 `wf(TAG0035-P4)` 一类 commit，本次回退修复 commit 的暂存区只含 md/yaml
- When 执行 `check-gate.py P4 <task_dir>`
- Then `_gate_p4` 能识别"回退后再推进"这一场景，不因该次修复 commit 暂存区无代码文件而 `return 1`
- 验证：新增 regression 测试构造该状态组合，断言 `_gate_p4` 不再因"无代码文件"判据本身而拦截（其余既有判据仍需满足）

#### BDD-10: 判据放宽不削弱既有拦截力（红灯边界）
- Given 一次 commit 暂存区只含 md/yaml，且该 phase 此前既无代码 diff 历史、也不属于"回退后修复"场景（不满足 BDD-8/BDD-9 任一豁免条件）
- When 执行 `check-gate.py P4 <task_dir>`
- Then `_gate_p4` 仍然 `return 1`（放宽只在 BDD-8/BDD-9 声明的两种场景生效，其余场景维持原判据不放松）
- 验证：新增 regression 测试断言"纯文档、无历史代码、非回退"场景仍 `exit 1`（对应 known_risks「判据放宽若过宽会削弱 gate 拦截力」的止损）

### 子批 D：DEBT0038（check-judge-verdict.py 黑白名单 3 处假阳性 + 同类扫描新增实例）

#### BDD-11: 黑名单不再误判协议阶段卡片路径引用（覆盖两个同构文件名）
- Given `P6.5-dispatch-context-judge.md` 的「输入文件」/「上游关联」两节中合法引用了协议阶段卡片路径（`agate/phase-cards/P6-acceptance.md` 或 `agate/phase-cards/P4-implementation.md`，指向协议规格文档而非该任务自己的 `P6-acceptance.md`/`P4-implementation.md` 产出文件）
- When 执行 `check-judge-verdict.py <task_dir>`
- Then `_check_blacklist` 不再仅凭 basename 子串命中就判黑名单命中，需能区分"任务自己产出文件的引用"与"协议规格文档路径引用"；两个文件名（本次同类扫描确认的两个已知同构实例）均须验证豁免生效
- 验证：新增 regression 测试分别构造含 `phase-cards/P6-acceptance.md` 与 `phase-cards/P4-implementation.md` 引用的 `dispatch-context-judge.md`，断言 `check-judge-verdict.py` 不再因这两处引用报黑名单命中

#### BDD-12: 白名单补齐角色定义文件路径
- Given `P6.5-dispatch-context-judge.md` 的「输入文件」节按通用惯例列出角色定义文件路径（如 `agate/assets/execution-roles/analyst.md` 或 `agate/assets/review-roles/*.md`）
- When 执行 `check-judge-verdict.py <task_dir>`
- Then `_check_whitelist_outside` 不再把角色定义文件路径判为"白名单外任务产出路径引用"
- 验证：新增 regression 测试构造含角色定义文件路径引用的 `dispatch-context-judge.md`，断言不再报"白名单外"错误；`dispatch-protocol.md`「Judge 信息隔离」节 + P6 卡须同步补充"角色文件路径不受白名单限制"的说明（文档同步属本 BDD 验收范围一部分，对应 `packages: agate-docs`）

#### BDD-13: P6-evidence/ 目录下裸文件名引用不再误报白名单外
- Given `P6.5-dispatch-context-judge.md` 的两节中引用的是该任务 `P6-evidence/` 目录下真实存在的产物，但引用形式是目录内裸文件名（不含 `P6-evidence/` 前缀）
- When 执行 `check-judge-verdict.py <task_dir>`
- Then 白名单判定结果与"引用时是否显式带 `P6-evidence/` 前缀"无关——只要该文件名可判定为该任务 `P6-evidence/` 目录下的真实产物，就不应被判"白名单外"（具体判定机制，如结合任务目录实际文件列表核对，由 P2/P3 设计）
- 验证：新增 regression 测试构造 `dispatch-context-judge.md` 中含 `P6-evidence/` 目录下某文件的裸文件名引用（该文件在任务的 `P6-evidence/` 目录下真实存在），断言不再报"白名单外"

#### BDD-14: 黑白名单加固后仍能拦住真实自述（防御性红灯用例）
- Given `P6.5-dispatch-context-judge.md` 的两节确实直接引用了该任务自己产出的 `P6-acceptance.md`（verifier 自述场景，真实信息隔离违规，而非协议规格文档引用）
- When 执行 `check-judge-verdict.py <task_dir>`
- Then 仍然判定为黑名单命中并 `exit 1`——BDD-11/12/13 的路径豁免/白名单补齐/裸文件名识别不得连带放宽掉对真实自述场景的拦截
- 验证：新增/保留一条"`P6.5-dispatch-context-judge.md` 引用任务自己的 `P6-acceptance.md`"的红灯 regression 用例，断言仍 `exit 1`（对应 known_risks「DEBT0038 白名单放宽可能削弱 judge 信息隔离」的止损）

## 4. 待确认清单

[NO_NEED_CONFIRM]

本 P1 未发现需要人定夺业务方向的隐含需求：子批 A/D 范围已由 P0-brief 独立评审锁定；子批 B 已明确"最小案"取向（完整案已转 `[SUGGEST]`，见下）；子批 C 的两种可选机制留给 P2 architect 定案（不涉及业务判断，纯技术方案选择）。

`[SUGGEST: 子批 B 完整案（phases.yaml 加 order/predecessors 显式阶段序）如仍认为有必要，作为独立议题另行立项，理由：与本批 out-of-scope「不做 phase 语义重构」冲突，且需要先解 additionalProperties: false schema 变更，影响面（存量任务兼容）超出本批"gate 判据健壮性"的范围]`

## 5. 同类扫描（强制节）

### 子批 A：check-gate.py 之外，其余 check-*.py 是否存在同构 fail-open 模式

**扫描命令**：`grep -rn "sys.exit(2)\|return 2\b" agate/scripts/check-*.py`

**命中**：22 个 `check-*.py` 脚本中共命中 26 处（`check-gate.py` 自身占 14 处，均为已知的"通过/WARNING"既有语义，不在本次扫描讨论范围）；`check-gate.py` 之外命中 12 处，分布于 10 个文件：

| 文件:行 | 上下文 | 逐条判定 |
|---|---|---|
| check-debt.py:67 | `resolve_workspace is None`（依赖加载失败）→ `sys.exit(2)`，注释自陈"需主 Agent 自判" | 本次不处理——依赖加载失败是环境问题非"未知枚举值"，且已显式打印错误信息到 stderr，非静默 |
| check-p6-evidence.py:135 | `P6-acceptance.md` 不存在 → `sys.exit(2)` | 本次不处理——"前置文件缺失→exit 2"是与 `check-pruning.py`/`check-routing.py` 一致的既定约定（见下），非未知输入误判为通过 |
| check-p6-evidence.py:312 | 合法小图片数量 >0 → WARNING `exit(2)` | 本次不处理——WARNING 语义明确（"疑似充数，不阻断但请确认"），非静默 |
| check-p6-evidence.py:367 | 像素方差 WARNING → `exit(2)` | 本次不处理——同上，WARNING 语义明确 |
| check-p6-provenance.py:573 | `warning_found==1` → `exit(2)` | 本次不处理——WARNING 语义明确 |
| check-platform-assumptions.py:134 | 扫描目标路径不存在 → `sys.stderr.write("FATAL...")` + `sys.exit(2)` | 本次不处理——该脚本自身只用 0（无命中）/1（有命中）/2（无法运行）三个互斥的码，调用方按非零判定失败，exit(2) 不会被误判为"通过"，不构成"未知输入映射为已知通过码"的同构问题 |
| check-protocol-consistency.py:1436 | `--strict` 下有 WARNING 无 ERROR → `return 2` | 本次不处理——`--strict-errors-only` 模式下走的是 `return 0` 分支（HANDOFF 强制用此模式），`return 2` 只在 `--strict` 全量模式下触发，语义是"WARNING 计数"而非"未知输入" |
| check-pruning.py:143 | `P1-requirements.md` 不存在 → `sys.exit(2)` | 本次不处理——同 check-p6-evidence.py:135，既定"前置文件缺失"约定 |
| check-routing.py:77 | `P1-requirements.md` 不存在 → `sys.exit(2)`，注释自陈"对齐同链 check-pruning；与'不声明=standard'的 exit 0 明确区分" | 本次不处理——代码自证是有意为之的约定，非 bug |
| check-scope-resolved.py:80 | `task_dir` 不是目录 → `sys.exit(2)` | 本次不处理——前置条件缺失约定 |
| check-state-yaml.py:44 | `state_file` 不存在 → `sys.exit(2)` | 本次不处理——前置条件缺失约定 |
| check-tdd-red.py:108 | `exit_code==0`（测试全过，无红灯）→ `return 2` | 本次不处理——WARNING 语义明确（"实现可能领先于测试"） |

**结论**：全仓 `check-*.py` 中，"未知枚举值 / 无法识别的输入被静默映射为与已知正确状态相同的退出码"这一具体缺陷模式（即子批 A 的 bug 本身：`handlers.get(未知key) → sys.exit(2)`，与已知阶段的"通过"码完全相同、且无任何区分手段）**只存在于 `check-gate.py` 一处**（已是本批交付项，无需新增修复点）。额外用 `grep -rn "handlers\s*=\s*{\|\.get(phase)\|\.get(mode)\|\.get(kind)\|\.get(type)\|\.get(action)" agate/scripts/check-*.py` 核实全仓只有 `check-gate.py:1474/1486` 一处 dispatch-dict 模式，确认没有第二个"未知 key 静默走默认分支"的同构实例。其余 12 处 `exit(2)`/`return 2` 全部是"前置文件/前置条件缺失"或"WARNING、非阻断"两类既定约定（`check-routing.py:77` 的注释已自证这是有意设计），语义上与"真实 pass"和"真实 fail"均能区分，不构成同一类风险。**未发现更多同类实例，本次不新增修复范围。**

### 子批 C：其它 phase 完整度判据是否共用「看暂存区」假设

P0-brief 子批 C 原文已明确要求这一项"同类核查"："其它 phase 完整度判据是否共用『看暂存区』假设"。扫描对象：`check-gate.py` 的全部 10 个阶段判据函数（`gate_p0`~`gate_p8` + `gate_p65`）。

**扫描命令**：`grep -n "diff.*--cached.*--name-only\|_STAGED_EXCLUDE_RE\|--cached" agate/scripts/check-gate.py`，再逐个命中行定位所属函数（`grep -n "^def gate_p"` 取函数边界）。

**命中与逐条判定**：

| 函数 | 是否用"暂存区快照"判据 | 逐条判定 |
|---|---|---|
| `gate_p0` | 否 | 不适用 |
| `gate_p1` | 否 | 不适用 |
| `gate_p2` | 否 | 不适用 |
| `gate_p3` | 否 | 不适用 |
| `gate_p4` | **是**——`git diff --cached --name-only` + `_STAGED_EXCLUDE_RE`（行 953-961），只看当前 commit 暂存区快照，无历史回看，命中"无代码文件"即硬 `return 1` | 已是本批交付项（DEBT0037），**已被 BDD-8/9/10 覆盖**，此处不重复处理 |
| `gate_p5` | 否 | 不适用 |
| `gate_p6` | 否 | 不适用 |
| `gate_p65`（P6.5） | 否 | 不适用 |
| `gate_p7` | 否（通读 1183-1352 行，未出现任何 `git diff --cached` 调用，判据全部基于 `P7-consistency.md` 文件内容字段） | 不适用 |
| `gate_p8` | **是，但设计不同**——`git diff --cached --stat`（version 文件变更，行 1400）与 `git diff --cached -- <changelog_file>`（行 1418/1437），表面上也读暂存区快照 | **本次不处理**，理由见下 |

**`gate_p8` 逐条判定详述（唯一需要辨析的候选命中）**：`gate_p8` 检查 version 文件 / CHANGELOG 变更时，**已自带"路径 A 暂存区 + 路径 B 最近 N 个 commit 回看"双路径 fallback**（行 1393、1403-1411、1421-1428，`AGATE_P8_LOOKBACK` 环境变量控制回看窗口，默认 5）：暂存区快照找不到时不会立即判失败，而是继续查最近 N 个 commit 的历史 diff；且两条路径都找不到时，**只降级为 `sys.stderr.write(...WARNING...)`，不 `return 1`**（不阻断推进）。这与 `gate_p4` 当前"只看当前 commit 暂存区快照、无回看、命中即硬 `return 1`"的风险模式在**两个维度上都不同**：① 已有跨 commit 历史回看，不会因为"本 phase 跨多 commit 交付、当前 commit 暂存区恰好不含目标文件类型"而误判；② 即使误判也只是 WARNING 提示，不会像 `gate_p4` 那样拒绝推进。因此 `gate_p8` **不构成同一类风险的实例**。

**结论**：全仓 `check-gate.py` 的 10 个阶段判据函数中，**只有 `gate_p4` 存在 P0-brief 描述的"仅凭当前 commit 暂存区快照判定、无历史回看、命中即硬 `return 1`"风险模式**；`gate_p8` 虽然同样读取 `git diff --cached`，但已用"暂存区+最近 N 个 commit 回看"双路径设计 + WARNING 降级规避了该风险；其余 8 个函数完全不使用暂存区快照类判据。**确认只此一处（`gate_p4`），本次不新增 BDD**——DEBT0037 现有的 BDD-8/BDD-9/BDD-10 已完整覆盖该唯一实例，`gate_p8` 的既有 fallback 设计本身即是该风险的正确应对范式，可作为 P2 设计 `gate_p4` 放宽方案时的参照先例（`[SUGGEST: gate_p4` 的放宽实现可参照 `gate_p8` 已验证的"暂存区+lookback commit 回看"双路径模式，理由：同一脚本内已有先例，风格一致、无需新引入机制]`）。

### 子批 D：check-judge-verdict.py 黑白名单是否还有其他子串匹配风险点

**扫描方式**：通读 `check-judge-verdict.py` 全文（545 行），逐一核对 `_check_blacklist` / `_check_whitelist_outside` / `_is_whitelisted` / `_check_prediction` 四处子串匹配逻辑的匹配边界。

**命中与判定**：

1. `_BLACKLIST_MD = {"p6-acceptance.md", "p4-implementation.md", "p4-review.md"}`（第 62-66 行），匹配方式 `if exact in low`（第 171 行，`low` 为两节全文小写拼接，无路径边界）——**本身就是 P0-brief 已知问题①的实现，但 P0-brief 只举了 `p6-acceptance.md` 一个例子**。用同一命令模式对三个文件名逐一重新全仓扫描（`find . -iname "<basename>" -not -path "*/agate-workspace/tasks/*"`），**命中数比首轮扫描报告的更多**，逐条判定如下（首轮扫描只报告了 phase-cards 一条命中，遗漏了 archived/fixtures 路径，本轮补全）：

   | basename | 全部命中（`find` 原始输出） | 逐条判定 |
   |---|---|---|
   | `p6-acceptance.md` | `agate/phase-cards/P6-acceptance.md`；`agate-workspace/archived/tasks/T001-v2.0-structured/P6-acceptance.md`；`agate-workspace/archived/tasks/T001-v2.0-structured/.archived/20260810-085926-P6/P6-acceptance.md`；`agate/tests/fixtures/{vision-blocked,high-risk,ui-affected,paused-task,full-task}/P6-acceptance.md`（5 个 fixture） | 共 8 处，逐类判定见下 |
   | `p4-implementation.md` | `agate/phase-cards/P4-implementation.md`；`agate-workspace/archived/tasks/T001-v2.0-structured/P4-implementation.md`；`agate/tests/fixtures/{full-task,vision-blocked,high-risk,ui-affected,paused-task}/P4-implementation.md`（5 个 fixture） | 共 7 处，逐类判定见下 |
   | `p4-review.md` | `agate-workspace/archived/tasks/T001-v2.0-structured/P4-review.md` | 共 1 处（无 phase-cards/fixtures 同名命中） |

   两个 basename 的命中按路径归为三类，逐类给出处理判定（不留白）：

   - **`agate/phase-cards/*.md`（各 1 处，协议阶段卡片）**：**本次处理**——并入 BDD-11 验收范围。这类路径是「输入文件」节按通用惯例引用角色/协议规格文档的合法场景（本任务自己的 dispatch-context 亦如此引用，见 P1-dispatch-context-analyst.md 的角色定义文件路径），会被真实的 `P6.5-dispatch-context-judge.md` 合法引用到，是已确认的假阳性场景。验收测试须同时覆盖 `p6-acceptance.md`（P0-brief 原举例）与 `p4-implementation.md`（本次同类扫描新增确认的第二实例）。
   - **`agate-workspace/archived/tasks/T001-v2.0-structured/**`（`p6-acceptance.md` 2 处、`p4-implementation.md` 1 处、`p4-review.md` 1 处，均为其他历史任务 T001 自己的归档产出文件）：**本次不处理**——理由：①「输入文件」/「上游关联」两节按协议惯例引用的对象是角色定义文件、协议阶段卡片、以及**当前任务自己**的产出文件，不会引用**另一个不相关历史任务**的归档产出路径（这不是本仓库任何已知的 dispatch-context 撰写惯例，遍历现存任务的 dispatch-context 文件未发现此类引用模式）；②即便理论上被引用，判定为黑名单命中也不算误伤——它确实不是协议规格文档，属于另一任务的历史自述类产出，继续拦截是保守但方向正确的行为，不需要额外豁免；③ BDD-11 的路径豁免机制按第①类的"协议规格文档路径前缀"精确豁免，天然不会覆盖到 `agate-workspace/archived/` 路径，不会连带放宽这一类。
   - **`agate/tests/fixtures/*/*.md`（`p6-acceptance.md` 5 处、`p4-implementation.md` 5 处）**：**本次不处理**——理由：①这些是本仓库测试基础设施自身的固定数据（供 `check-gate.py`/`check-judge-verdict.py` 等脚本的单测/回归测试构造输入用），不是任何真实任务的协议产出或角色文件，**不会**出现在真实任务 `P6.5-dispatch-context-judge.md` 的「输入文件」/「上游关联」两节引用中（这两节引用的是任务协作过程中人类可读的协议/角色文档，不会引用测试 fixture 数据路径）；②因此不构成真实场景下的假阳性风险，BDD-11 的路径豁免范围也不应扩大到 `agate/tests/fixtures/` 前缀（扩大反而可能被用来构造绕过黑名单的测试数据路径，无收益、有风险）。

   **本节结论修正**：子批 D 的黑名单假阳性同类扫描发现的新增实例是 `agate/phase-cards/P4-implementation.md`（第一类，已并入 BDD-11）；`agate-workspace/archived/` 与 `agate/tests/fixtures/` 两类命中经核实均不构成真实假阳性场景，明确判定为本次不处理，不扩大 BDD-11 的豁免范围。
2. `_BLACKLIST_DC_RE = re.compile(r"p[456]-dispatch-context-[^\s]*\.md")` / `_BLACKLIST_DIR_RE = re.compile(r"p5-test-results/")`（第 67-68 行）：这两处同样是无路径边界的子串扫描，但语义不同——黑名单意图是"两节内**任何**对这些任务产出文件的文本引用都视为潜在信息泄露"（设计文档 §22 行注释"两节黑名单串扫描"），即便只是提及文件名也应拦截，这与①③的"basename 碰撞到不相关的协议文档"性质不同。本次不处理——未发现该正则命中协议文档或角色文件等合法场景的假阳性证据（`phase-cards/` 目录下没有 `P4/P5/P6-dispatch-context-*.md` 或 `P5-test-results/` 这类命名的协议文件），维持现状。
3. `_is_whitelisted()` 的目录前缀判定 `if "p6-evidence/" in tok: return True`（第 186 行）与 `_check_whitelist_outside()` 第二个循环 `if re.match(r"^p[0-9]", stripped): outside.append(stripped)`（第 205 行）：后者会把任何形如 `p<digit>.../` 的目录引用（未命中 `p6-evidence/`）标记为"越界"，覆盖面比字面 White/Black 名单更宽——这是已知问题③（裸文件名不被识别为白名单内）的另一面，即"错杀"而非"放过"。本次不处理（不是假阳性风险点，而是已知③本身的一体两面，修复③时一并验证不误伤其他合法 `p[0-9]` 前缀目录引用，已含在 BDD-13 的验收范围内）。

**结论**：本轮新扫描在 `_BLACKLIST_MD` 集合中确认**新增 1 个同构假阳性实例**（`p4-implementation.md` 对应 `agate/phase-cards/P4-implementation.md`），已并入 BDD-11 处理；`_BLACKLIST_DC_RE`/`_BLACKLIST_DIR_RE`/`_is_whitelisted` 目录前缀逻辑经核对**未发现**独立于 P0-brief 已知①②③之外的新增假阳性/假阴性风险点，本次不新增修复范围。

## 6. 裁剪说明

本批风险面覆盖 4 个子批、5 个核心协议脚本（`check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`/`check-judge-verdict.py`，均在 SELF-GATE 触发面内），且判据放宽（子批 C）/黑白名单放宽（子批 D）任一处过宽都会削弱 gate 拦截力本身——risk_level 定为 `medium`（参照 TAG0031/TAG0034 先例：改核心 gate 脚本、影响面覆盖 P1-P8 全阶段判定，不适用 low）。

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]`——不裁剪任何阶段，理由：
- P2（设计）：子批 B/C 均有多机制可选，需要 architect 定案；子批 D 加固方案需要影响面梳理，不可裁
- P3（TDD）：HANDOFF §5 明确要求"改脚本走 TDD，先写失败测试确认红"，且本批全部 BDD 都要求"新增 regression 测试"，P3 产出的红灯用例是 P4/P5 验证的前提，不可裁
- P4/P5/P6（实现/验证/验收）：核心阶段，不可裁
- P7（一致性检查）：本批改动跨 5 个脚本 + 可能的文档（`dispatch-protocol.md`/P6 卡，见 BDD-12），需要跨文件交叉核对，且 `packages` 声明依赖 P7 做一致性检查，不可裁
- P8（发布）：涉及 roadmap RM-AG0062 回写 + DEBT0037/0038 回写 `closed`，按 HANDOFF §8 要求走完整发布流程，不可裁

无阶段被跳过，故无需逐阶段写跳过理由。

## 7. 范围声明（写入 frontmatter，此处仅说明依据）

- `packages: [agate-scripts, agate-tests, agate-docs]`——`agate-scripts`（5 个被改动脚本）、`agate-tests`（本批要求的全部新增 regression/unit 测试）、`agate-docs`（BDD-12 要求同步 `dispatch-protocol.md`「Judge 信息隔离」节 + P6 卡说明角色文件路径豁免）
- `domains: [backend]`——纯协议脚本/判据改动，无用户可见页面

## 8. 能力需求声明

```yaml
capability_requirements: []
```

本任务无特殊能力需求：全部验证通过本地 `pytest` / `grep` / 手工调用 `check-gate.py` 等脚本完成，不涉及浏览器行为、视觉能力、外部网络或安全模型验证，`domains` 不含 `frontend`，无需声明视觉能力条目。
