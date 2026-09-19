---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: analyst
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P1 首次派发（非重试）。

### 目标

把 `P0-brief.md` 已锁定的范围转化为正式 `P1-requirements.md` 需求基线：**MVWU 阶段 1 四项交付物**（① `batches[].tests_filter` ② `P4-evidence/{batch}.log` ③ `check-mvwu.py`（含 `--observe`）④ 字段落地路径）+ **⑤ 组 7 个方法学概念的成文落地**（⑤-a…⑤-e）——每项交付物至少 1 条 BDD（Given/When/Then，二值可判定），frontmatter 声明齐全，含本阶段强制的「同类扫描」结论与「P0-brief 时效性质疑」记录。

### 约束

1. **范围以 P0-brief 当前版本为准（含末尾「P0 自检记录」节），不得超出**。若 P1 发现需超出范围，**不要自行扩**——写 `[NEED_CONFIRM]` 或 `[SCOPE+]` 标注，由主 Agent 转用户裁决。
2. **零协议内核改动是硬约束**：`.state.yaml` schema / `check-gate.py` gate 分支 / `phases.yaml` / `agate/rules/schema/*.json` / hook 三件套 / `gate-events` 审计链——BDD 里不得出现要求改这些的验收项；建议在 BDD 中显式加一条**负向 BDD**（"Given 本任务完成 When 对比基线 Then 上述内核文件 git diff 为空"，可机械判定）。
3. **不挂 gate、不阻断**：`check-mvwu.py` 的任何 verdict（含 FAIL）都不得改变 `.state.yaml` 或令 commit/gate 失败。BDD 要覆盖"FAIL/UNKNOWN 时脚本 exit code 与不阻断语义"的**明确约定**（exit code 取值由你在 BDD 中给出并说明理由；设计依据 `docs/design-notes/design-mvwu-protocol.md` §5.1.1）。
4. **四态 verdict 必须逐态一条 BDD**：`PASS` / `FAIL` / `EXPECTED_RED` / `UNKNOWN`；其中 **UNKNOWN 不得等价于 PASS、不得作为放行依据** 须有独立可判定 BDD。六项检查（且仅此六项）各有对应可验证行为。`--observe` 输出格式（补齐耗时 / commit 形态 / boundary 三列）须有 BDD 规定输出行的列结构。
5. **判据 6（`--observe` 在真实任务上跑通）** 须写成 BDD，且明确"真实任务"可以是任意已有任务目录（不要求多批），验收方式 = 输出格式正确的一行。**不得把「Q1/Q3 已答」写成任何 BDD 或完成条件**（P0-brief 已明确不在范围；Q2=13% 是引用结论，无需试点）。
6. **⑤ 组 BDD 只要求「成文到位」**：⑤-b（Deep Modules 审查锚点）、⑤-d（Walking Skeleton 拒绝/吸收记录）**不得**写出"机制已生效"型 BDD；BDD 的可验证面 = 目标文件存在指定节 + 含判据要点关键词（由你在 BDD 里列出必含要点）。⑤-a（CONTEXT.md 补录 5 个术语，沿用三列格式、不动既有 29 条）、⑤-c（三条判据落 `architect.md` + `P2-design.md`，含"与 P3 红灯批边界"/"Vertical Slice 须写明理由"/"Fitness Functions 不规定工具"）、⑤-e（`adr.md` 复审触发条件 + 项目侧 `decisions/` 落点，含"过时不删"）各有可验证交付物。
7. **⑤ 组的边界（P0-brief out-of-scope）**：不重构既有术语表、不新增术语一致性机械校验、不重写既有角色行为约定、不规定架构适应度工具、不强制垂直切分、不做决策自动过期 gate、不引入部署/CI 机制。
8. **`tests_filter` 相关既有约束须落进 BDD**：filename-safe 字符集（`[A-Za-z0-9._-]+`，约束的是 `{batch}` 即批 `id`）；`tests_filter` 不得裸 `python3`（遵循 `AGATE_PYTHON` 探测，DEBT0014），Windows 无 `make` 应写 `python -m pytest`；scoping 规则（只覆盖该批交付面、禁全量）+ `expected_red` 声明；`tests_filter` 为**可选键**，缺省时既有 P2 gate 行为**不变**（回归 BDD：既有 `check-gate.py P2` 单测全绿）。
9. **自身单测与 SELF-GATE**：`check-mvwu.py` 单测须用 `tmp_path`（DEBT0040 教训）且平台无关（Windows 只跑 `-m windows_smoke`）；命中 SELF-GATE 触发面 → BDD 应含"全量 pytest（CI 口径 `--reruns 1 -n auto`，基线 1666 passed / 2 skipped，只增不减）+ consistency 0 ERROR + ruff 0 error + shellcheck（如涉及 sh）"作为收口 BDD。测试计数漂移须同步 `agate/tests/` 内相关计数文档（见客观查证）。
10. **同类扫描是强制节，不能只复制 P0-brief 已有结论**：
    - `tests_filter` / `P4-evidence`：`grep -rIn` 全仓（排除 `.git`），区分「协议本体 `agate/`」「设计文档」「历史任务产物」，每个命中标"本次处理 / 本次不处理 + 理由"；
    - `dispatch_plan` 全部消费方（`agate/` 内 13 文件，见客观查证）：逐个判定新增可选键是否需要同步（`task-files.md` 的字段登记、`scripts/README.md` 的脚本登记、`tests/README.md` 的计数、`check-structure-consistency.py` 是否对 frontmatter 键做白名单校验）；
    - 新脚本落地面：新增 `agate/scripts/*.py` 需在哪些**登记面**同步（README 脚本表、`agate-summary`、SETUP、`rules/` 中脚本清单、consistency 的脚本-文档双向核对）——用 grep 一个既有独立 check 脚本（如 `check-retrospective.py`）出现的位置作参照，列清单；
    - ⑤ 组：6 个目标文件中是否已有同义节（避免重复补录）；`decisions/` 相关既有引用（`orchestrator-template.md` / `state-machine.md` / `SETUP.md`）是否需同批改；
    - 结论写进 P1-requirements.md 正文（含扫描命令与命中数），"已确认只此一处"也要显式写。
11. **P0-brief 时效性质疑**：立项 2026-09-16 → 启动 2026-09-19（期间 PR #341/#342/#343 合并）。主 Agent 已在 P0-brief「P0 自检记录」逐条核对：**无严重漂移**；轻微漂移 2 条（`_gate_p2_dispatch_plan` 行号 743→767；worktree 内 `decisions/` 目录不存在而非"空置"）。**你仍须独立复核（不要照抄），并在 P1-requirements.md 正文写出 `[P0_STALE: 具体漂移点]`（轻微 2 条）+ 已更新哪个字段的说明（P0-brief 已就位，可注明"P0 自检记录已载明"）**；若你发现新的严重漂移，停下报告主 Agent。
12. **frontmatter 建议值**（可据实际调整，须给出理由）：`risk_level: medium`（新增脚本 + 协议卡片/角色改动，触 SELF-GATE，但零内核）；`phases: [P1,P2,P3,P4,P5,P6,P7,P8]`（不裁剪——含 P3 TDD：`check-mvwu.py` 是新代码；⑤ 文档类改动的测试策略由 P3 定，通常用 grep 断言审计测试）；`domains: [backend]`；`packages: [agate-scripts, agate-docs, agate-tests]`。`judge.enabled: true` 已在 `.state.yaml`（机制强制），正文提一句确认即可。
13. **无 frontend 域**：不需要 UX 类别 BDD / `ui_render_shape`。
14. **BDD 编号全局唯一**（`#### BDD-NN:`，从 BDD-1 顺序编号，按交付物分组标注归属）。BDD 标题后**不要**写 PASS/FAIL 预判字样；有 `[NEED_CONFIRM]` 则标，无则写 `[NO_NEED_CONFIRM]`。
15. **提交粒度决策**（P0-brief 的「提交粒度决策」A/B）属**用户裁决项，非本任务交付**：可在正文「不在范围」里引用，**不要**替用户选。

### 上游关联

- P0-brief.md（权威范围来源：4 项 MVWU 交付物 + ⑤ 组 7 概念 + 判据表 + out-of-scope + known_risks + P0 自检记录）
- HANDOFF-TAG0036.md（worktree 根）：双工作区纪律、验证命令清单、阶段推进纪律、SELF-GATE 触发面——写验证类 BDD 时可直接复用其命令
- 设计依据 `docs/design-notes/design-mvwu-protocol.md`（v2.1：§3.1 I1 / §5.1.1 四态 verdict / §5.1.2 消费方与登记点 / §7 试点 / §11 未决）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P0-brief.md
- HANDOFF-TAG0036.md（worktree 根）
- docs/design-notes/design-mvwu-protocol.md
- agate/scripts/check-gate.py（仅读 `_gate_p2_dispatch_plan`，确认"不拒未知键"）
- agate/scripts/agate-md-field-get.py（`JSON_FIELDS` 读取语义）
- agate/phase-cards/P2-design.md、agate/assets/execution-roles/architect.md（字段落地路径现状）
- agate/CONTEXT.md、agate/role-system.md、agate/adr.md（⑤ 组现状）
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P1

路径：phase-cards/P1-requirements.md
---
# P1 — 需求基线

> 当前状态：[首次 / 重试 #N]
> P1 不可裁剪（核心阶段）

## 如果是首次进入本阶段

1. 派发 analyst subagent → 产出 P1-requirements.md
   1.1 写 P1-dispatch-context-analyst.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 确认：BDD 验收条件 ≥1 条 + 无未决 NEED_CONFIRM
2.5 派发 requirements-review subagent（角色文件：{agate_root}/assets/review-roles/requirements-review.md）
     2.5.1 写 P1-dispatch-context-requirements-review.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
    输入：P1-requirements.md
    产出：P1-review.md（agent≠main，含 BDD 编号引用 + 覆盖维度标注）
    review 不通过 → analyst 修改 → 再 review → … → approved（⑩迭代循环）
3. 预跑 check-gate.py P1（exit 2，主 Agent 自判）
4. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P1，不要提前写 P2——phase = 本 commit 的产出阶段
5. git commit -m "wf({Txxx}-P1): {摘要}"（phase=P1，P1 产出含 P1-requirements.md + P1-review.md）
6. P1 commit 完成后进入 P2：**phase 推进 P2 随 P2 产出 commit 一起**（P2-design.md + P2-review.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（BDD 不完整 / domains 声明错 / NEED_CONFIRM 未处理）
→ review 不通过时：analyst 修改需求 → 重派 requirements-review → 共享 retry 预算
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P1 MAX=3）

## 前置条件

- [ ] P0-brief.md 完成（四字段齐全）

## 派发

- **角色**：analyst（`{agate_root}/assets/execution-roles/analyst.md`）
- **输入**：P0-brief.md（env_constraints / known_risks / executor_env）
- **输出**：P1-requirements.md
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 复杂需求编排（模式 4，条件触发）

需求复杂（多来源 / 多模块 / 无法预先拆清范围）时，P1 可先派**侦察 subagent**（模式 4 先理解后拆，见 dispatch-protocol「派发编排机制」）读全貌后再拆需求：

1. 侦察 subagent 读 P0-brief + 相关上下文，产出拆分方案（拆成哪些子需求、各子需求的输入/产出/依赖）
2. 按方案派 analyst（并行或串行）分别产出需求基线
3. 合并时定义**合并语义**（在侦察产出中声明，P7 一致性检查依赖）：
   - **BDD 全局编号**：各子需求承接的 BDD 编号全局唯一（`#### BDD-NN:`），不允许各子需求各自从 1 编号
   - **包归属去重**：每个 BDD 明确归属唯一包，跨包的共享件单独列出，不允许两个子需求各写一份

## 产出规格

P1-requirements.md 必须包含：
- BDD 验收条件（至少 1 条，Given/When/Then 格式）
- `domains:` 声明（backend / frontend / mcp / security）
- `packages:` 声明（受影响的包/模块）
- `risk_level:` 声明（low / medium / high）→ 决定 P2 评审强度
- `ceremony:` 声明（thin / standard / full）→ 仪式深度档位（可选，缺省 standard，fail-closed：不声明或声明要素不满足一律按 standard 处理，不做薄化）
- `phases:` 裁剪声明（跳过哪些阶段 + 理由）
- `judge:` 启用声明（RM-AG0039 强制）：机制后新任务（P1 `created` ≥ `judge_required_since`，见 `agate/rules/dispatch.yaml`）P1 初始化须在 `.state.yaml` 写 `judge.enabled: true`——check-gate P1 机械校验（缺失/未启用 → exit 1）；历史任务（created < 截止或未声明）缺块 → 跳过
- `capability_requirements:` 能力需求声明（available / supplementable / GAP 三态）
- 无未决 `[NEED_CONFIRM]`（有则 PAUSED）；无待确认项时写 `[NO_NEED_CONFIRM]`

`risk_level`/`phases`/`packages`/`domains` 写在文件头 **frontmatter**（`---` 分隔块），不写正文。
**可直接复制的完整样例**：
```yaml
---
phase: P1
task_id: TAG0001           # 替换为实际任务编号
type: problems
parent: P0-brief.md
trace_id: T001-P1-20260101 # {task_id}-P1-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: analyst
# ── v2.0 机器字段 ──
risk_level: low             # low / medium / high，必填
ceremony: standard          # thin / standard / full，可选；缺省 standard（fail-closed）
phases: [P1, P4, P5, P6, P8]   # list of P\d+，必填
packages: [pkg-a]           # list，必填
domains: [backend, frontend]  # list，必填
# 可选字段：override / implicit_coupling / coupling_checklist / internal_only /
# internal_only_reason / 跳过风险 / design_trivial / follows_existing_pattern
# ── RM-AG0039 judge 启用声明（写在 .state.yaml，非 P1 frontmatter）──
# 机制后新任务（P1 created ≥ judge_required_since，rules/dispatch.yaml "2026-08-22"）必须
# 在 .state.yaml 写 judge.enabled: true——check-gate P1 机械校验，缺失/未启用 → exit 1
# ── v2.0 refactor 任务类型声明（可选，缺省 = 功能任务）──
# change_type: refactor   # 当前仅支持 refactor；枚举非法值由 frontmatter schema 拦截
# ── TAG0007 项目阶段声明（可选，缺省 = established，向后兼容）──
# project_phase: bootstrap   # bootstrap（0→1 新项目）/ established（既有项目，缺省值）；
#                             # bootstrap 时 P2 architect 需额外产出 P2-skeleton.md（骨架声明）
# ── TAG0006 UI/UX 渲染形态声明（可选，presence 语义：缺失 = 常规布局型默认，不红基线）──
# ui_render_shape: render_component   # str，规范形态值：layout（布局型）/ render_component
#                                     # （渲染组件型，仅举例 OpenGL/WebGL/Canvas/图表/模型/特效/
#                                     #  地图/数字地球）/ temporal_effects（时序特效型）；开放集合可扩
# ui_ux_dimensions: [渲染正确性, 动效时序]  # list，从 UX 分类框架选适用维度；渲染组件/时序特效
#                                     # 类形态必填，常规布局型可省略
# ── v2.0 标记"已解决/已确认"状态（可选，仅标记存在时写）──
# need_confirm_resolved: []   # list[str]：已解决的 NEED_CONFIRM 项描述（逐条匹配正文）
# suggest_resolved: []        # list[str]：已采纳的 SUGGEST 项描述
# scope_resolved: []          # list[str]：已解决的 SCOPE+ 项描述
---
```

**UX 类别 BDD 与分类框架（domains 含 frontend 时必做）**：frontend 任务的 P1 必须含至少一条
UX 类别 BDD，并按实际 UI/渲染形态声明 `ui_render_shape` + 从 **UX 分类框架**（布局结构/
渲染正确性/交互行为/动效时序/视觉呈现等示例性开放集合）选 `ui_ux_dimensions` 维度，类别写入
BDD 标题后缀（如 `#### BDD-3: 渲染正确性：...`）。判据必须可量化（渲染正确性 → 渲染结果对比 +
diff 阈值或输出断言；时序 → 帧/时间戳对齐；动效 → 过渡/动画关键帧与结束状态断言；手势交互 →
动作输入的坐标/参数量化），禁主观词。缺失形态声明/维度选择/UX BDD → requirements-review 打回，
P1 gate 在"声明了形态但维度为空"或"维度不在分类框架且未在 BDD 标题声明"时 exit 1。

**人工体验路径验收（强制节）**：任务产出含**用户可见页面**且**页面内容受 seed 数据影响**时，
P1 必须追加一条**人工体验** BDD，句式强制为「Given seed 数据 → 页面有内容」（验证用户按文档 seed 后
页面在人工体验路径下确实渲染出内容）；不得只用 fixture 或单测断言替代人工体验路径验收。

**NEED_CONFIRM 分级**：
- `[SUGGEST: 推荐 X，理由 Y]` - 有倾向但求确认。主 Agent 可自行采纳倾向（除非涉及破坏性变更/业务方向），不必问用户
- `[NEED_CONFIRM]` - 真无方向需人定夺。阻塞推进，主 Agent 问用户

## ceremony fail-closed 声明 checklist（TAG0019，BDD-7/8/9）

`ceremony:` 声明仪式深度档位（thin / standard / full），缺省 standard（fail-closed——不声明或声明要素不满足一律按 standard 处理）。声明 **thin**（薄仪式）时，P1 必须连同以下四要素一起声明，缺一 → check-routing exit 1，档位回退 standard：

1. **申请**：`ceremony: thin` 显式声明
2. **逐信号 checklist**：`coupling_checklist: [...]` 流式声明（判据 `^coupling_checklist:\s*\[`，复用 check-pruning）
3. **跳过风险评估**：`跳过风险:` 声明（复用 check-pruning 判据）
4. **P5/P6 保留**：`phases` 含 P5 与 P6（薄化仪式不薄化验证，P5/P6 由 check-routing / check-pruning 双闸兜底）

不声明（存量/新任务缺 ceremony 字段）→ standard，不拦截。`ceremony: full` 的任务 `phases` 必须含 P7（P7 不可裁，缺失由 requirements-review 审声明拦截，BDD-14）。

### M3 验收锚度量协议（BDD-12，机制文档供提取）

thin 档跳过 LLM 评审的 M3 验收锚四要素：

1. **评审轮数**指标：任务在 P2/P4 阶段派发的 LLM 评审 subagent 轮数（含重试轮）
2. **真实发现数**指标：评审产出中被采纳或阻止了真实问题的条数（排除非阻塞建议、排除机械检查可抓项）
3. **TAG0018 基线值**：4 场 LLM 评审 ≈0 净收益（17 条非阻塞 + 1 条真实发现且机械检查可抓）
4. **不达标决策规则**：「LLM 评审真实发现 ≈ 0 且机械 gate 已覆盖 → 回滚 standard」

## 同类扫描（强制节）

需求基线必须含一次**同类扫描**结论——被报告的那一处几乎从来不是唯一的一处。P0 卡片的「同类/影响面预判」给出粗粒度量级，P1 在此基础上把清单做实：

1. **扫描动作**：对问题涉及的关键符号（函数名、字段名、配置键、协议节标题、错误文案）用 grep/rg 扫全仓，记录**命中数量 + 文件清单**
2. **逐条判定**：每个命中标"本次处理 / 本次不处理 + 理由"。本次不处理的同类实例要么进 roadmap，要么写清为何不构成同一问题
3. **回归拦截**：若同类问题未来还会新增（不是一次性修完的存量），需求里要声明拦截手段（新增测试 / gate 脚本 / 文档约定），并转成对应 BDD
4. **结论落盘**：扫描结论写进 P1-requirements.md 正文（不是只写在 progress 里）；即使结论是"已确认只此一处"也要显式写出，空白不算做过

同类扫描缺失 → requirements-review 打回（"只修被报告的那一处"是 agate 反复复发的反模式）。P2 的「影响面梳理」在本节结论上继续做候选方案级的影响域分析，三处（P0 预判 / P1 同类扫描 / P2 影响面梳理）同源、逐级细化，不重复劳动。

## verification_env vs supplementable 边界判断树

`capability_requirements` 三态（available / supplementable / GAP）和 `verification_env`（运行环境声明）经常被混用——TAG0009 的 11.7 小时就是把一个环境问题错标成 `supplementable` 导致的。P1 声明时按下面的判断树走：

```
先问：缺的是能力还是环境？
├─ 缺的是「agent 侧的能力」（看不见图 / 不会用某工具 / 没有某技能）
│   └─ 走 capability_requirements 三态：
│      ├─ 当前就有 ................................. available
│      ├─ 当前没有，但能通过派发子角色 / 注入 skill / 换工具补上 ... supplementable
│      │   （必须在需求里写清补充方式，否则等同 GAP）
│      └─ 当前没有且补不上 ......................... GAP（阻塞，PAUSED 交人工）
└─ 缺的是「运行环境」（服务没起 / 端口没通 / 数据库没建 / 依赖没装 / 平台不支持）
    └─ 走 verification_env 声明（不是 supplementable）：
       ├─ 环境可由主 Agent 用标准操作准备好 → P1 声明 verification_env，
       │   由主 Agent 按 dispatch-protocol.md「环境准备职责边界」统一准备
       └─ 环境本质不可得（权限/凭据/平台原生不支持）→ 这是不可重试类，
           按 dispatch-protocol.md「verification_env 失败处理协议」立即升级人工
```

**判别口诀**：换个更强的模型/角色就能做 → 能力问题（supplementable）；换谁来做都得先把服务起起来 → 环境问题（verification_env）。**把环境问题标成 `supplementable` 属于机制误用**，不算"环境故障"，不消耗验证轮次预算，应立即改正声明方式。

**环境验证轮次预算占位声明位**：声明了 `verification_env` 的任务，P1 需求里留一行轮次预算占位（默认止损轮次 = 2 轮，与阶段 `retries[Pn]` 独立计数），供 P5/P6 派发时由主 Agent 在 dispatch-context 中接续记录"当前第几轮 + 历次已排除假设"。数值与完整规则的权威定义在 dispatch-protocol.md「verification_env 失败处理协议」，本卡片不重写：

```yaml
verification_env: "debug server http://127.0.0.1:3001 + tests/fixtures/test.db"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

## P0-brief 时效性质疑

analyst 拿到 P0-brief 后不默认它仍然成立——立项与实际启动之间可能已经漂移（跨会话恢复、任务搁置后重启、从 PAUSED 恢复）。P1 阶段必须做一次时效性质疑，判据（严重 3 条 / 轻微 2 条）的权威定义见 P0 卡片「P0-brief 时效性自检（漂移判据）」，本节只定标记规则与处理方式：

**标记格式**（行首声明，一个漂移点一行，必须写出**具体漂移点**，不允许只写标记裸词）：

```
[P0_STALE: executor_env 声明的 CI 镜像已下线，当前实际跑在 ubuntu-24.04]
[P0_STALE: task 描述的 .sh 路线已全量 Python 化，目标方案本身不再成立]
```

**阻塞 / 记录二选一**（按漂移严重程度分流，不允许"既不阻塞也不记录"地含糊推进）：

| 漂移程度 | 处理 | 落盘 |
|---------|------|------|
| **严重**（命中 P0 卡判据 1-3 任一条） | **阻塞**：停止 P1，回 P0 重新立项 / 重做可行性分析 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 说明为何判定严重；主 Agent 按 PAUSED 或回 P0 流程处理 |
| **轻微**（不命中判据 1-3） | **记录**：更新 P0-brief 对应字段后继续 P1，不阻塞 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 已更新哪个字段 |
| 无间隔 / 已核对无漂移 | 继续 | 写一行"已核对 P0-brief 时效性，无漂移"，空白不算做过 |

## gate 规则

check-gate.py P1 → P1-review.md 存在 + status:approved + agent≠main + 含 BDD 编号锚点 → exit 2（BDD 编号格式为 `#### BDD-NN:`）；缺 P1-review.md / agent=main / 无锚点 → exit 1
P1 评审不可裁——所有任务都走独立 requirements-review，无例外

## 推进条件（全部满足才写 phase: P2）

- [ ] P1-requirements.md 含 BDD ≥1 条
- [ ] 含「同类扫描」结论（命中清单 + 逐条处理判定，"只此一处"也要写出）
- [ ] P0-brief 时效性已质疑：无漂移则记录已核对；有漂移则含 `[P0_STALE: 具体漂移点]` 且已按阻塞/记录二选一处理
- [ ] domains / packages / risk_level / phases 已声明
- [ ] 无 [NEED_CONFIRM] 标记
- [ ] 无 status: GAP（supplementable 不阻，GAP 阻）
- [ ] P1-review.md status: approved（agent≠main，含 BDD 编号锚点）

## 常见错误

1. **BDD 写成技术实现而非用户行为**：BDD 应该描述"用户能看到什么/系统应该做什么"，不是"调用哪个 API"
2. **domains 声明不全**：漏了某个受影响域 → P2 不派该域的评审 → 实现方向错误
3. **capability_requirements 漏声明**：P6 验收时才发现需要但不可用的能力 → 返工。**frontend 任务
   漏声明 vision 视觉能力条目（need 含 visual/vision）→ P1 gate exit 1 硬拦**（check-gate.py
   `_gate_p1_vision_capability`）；声明形态但漏选维度 / 形态声明与 UI/渲染形态不符 →
   同样 exit 1
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P2 设计依赖 domains + risk_level 决定评审角色
- P6 验收逐条对照 P1 的 BDD（PASS/FAIL 总数必须 ≥ P1 BDD 总数）
- P7 一致性检查依赖 packages 声明做跨文件交叉核对

## 评审

P1 评审通用必有（所有任务都走 requirements-review），P2/P4 评审是 C8 域触发（见 review-mapping.md）——二者在"是否通用"上不对称，仅在"独立 subagent、agent≠main"上类比。P1 评审不可裁剪。
review 不通过 → analyst 修改需求 → 再 review（⑩迭代循环），直至 approved。

> 完成 → 读 phase-cards/P2-design.md


## P1 基线保护

P1-requirements.md 是需求基线，后续阶段（P2-P8）不应直接修改。如需变更（如 P4 发现 BDD 矛盾需补充注释），必须：
1. 主 Agent 显式批准
2. 在变更处标注 `[BASELINE_CHANGE: 理由]`
3. 不改 BDD 的 Given/When/Then 语义（只补充注释/优先级说明）
4. **隐含扩展同样要授权**（TAG0025 教训）：P3/P4 的实现细节若事实上扩展了 P1 验收标准的范围（新增豁免条件、放宽/收紧某条 BDD 的判定边界等），即使当下未产生"矛盾"，也视为需要`[BASELINE_CHANGE]` 授权的情形——授权内容必须回写 P1-requirements.md 正文，不得只存在于下游阶段的 dispatch-context 口头引用中
<!-- AGATE_CARD_END -->

<objective_info>
主 Agent 本轮实测（均在 worktree 根 /home/kity/oclab/agateon/.worktrees/agate-TAG0036 执行）：

- `grep -rIl tests_filter`（排除 .git）：协议本体 `agate/` 命中 **0**；命中集中在 `docs/design-notes/`（3 份）、`docs/reviews/review-260916-0828.md`、`agate-workspace/roadmap/roadmap.md`、`active-tasks.md`、TAG0035/TAG0036 的 P0/P1 文档、HANDOFF-TAG0036.md。
- `grep -rIl P4-evidence`：同上，协议本体 0 命中；`find agate-workspace -type d -name P4-evidence | wc -l` = 0。
- `_gate_p2_dispatch_plan` 现位于 `agate/scripts/check-gate.py:767`（P0-brief 原写 `:743`，行号漂移，语义不变）；调用点 `check-gate.py:919`。
- `dispatch_plan` 在 `agate/` 内的出现文件（13）：`dispatch-protocol.md` / `scripts/agate-md-field-get.py` / `scripts/check-gate.py` / `scripts/README.md` / `assets/execution-roles/architect.md` / `UPGRADING.md` / `tests/unit/test_dispatch_orchestration.py` / `tests/README.md` / `tests/unit/test_agate_md_field_get.py` / `assets/templates/task-files.md` / `scripts/check-structure-consistency.py` / `phase-cards/P2-design.md` / `tests/unit/test_agate_md_field_set.py`。
- `agate/CONTEXT.md` 共 37 行；`grep -ci "MVWU|tests_filter|P4-evidence" agate/CONTEXT.md` = 0。术语表为三列 markdown 表（术语 | 定义 | 首次定义位置）。
- 本 worktree 内 `agate-workspace/decisions/` 目录**不存在**；`grep decisions agate/phase-cards/*.md agate/assets/execution-roles/*.md` 无命中。
- 环境：python 3.12.3 / pytest 9.0.3；分支 `feat/TAG0036-mvwu-pilot`；基线 CI 口径 1666 passed / 2 skipped；稳定版协议根 `~/.agate/v0.71.1/agate`（勿改，仅读卡片/跑编排类脚本）。
- 当前 `.state.yaml`：phase=P1，`judge.enabled: true`（已暂存）。
</objective_info>
