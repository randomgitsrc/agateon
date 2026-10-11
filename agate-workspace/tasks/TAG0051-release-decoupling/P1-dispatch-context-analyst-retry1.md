---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0051
role: analyst
retry: 1
---

<dispatch_guide>
> ⚠️ 以下是**修复轮（retry 1）**的增量派发指引，是本次任务的**强制指令**。
> **上轮的约束、输入文件清单、客观查证信息全部继续有效**——见
> `{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P1-dispatch-context-analyst.md`
> （首轮派发指引，本文件**不重复**其内容）。执行优先级：本指引 > 首轮指引 > 阶段卡片。

### 修复目标

上轮产出 `P1-requirements.md` 经独立评审（`P1-review.md`）判 **`status: needs-revision`**。
评审**确认**：20 条 BDD 编号连续、跨条一致性无矛盾、裁剪与声明核对通过、`ceremony` 缺省等价性成立、
**§五 22 项事实性断言全部独立复现成立** ⇒ **需求地基牢固，本次只修覆盖面与编号结构，不做事实性返工**。

请**只改** `{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P1-requirements.md`。
**不要改** `P1-review.md`（那是评审产物）。

---

#### (A) 【必改】覆盖缺口：4 处被标「本次处理」的语料面无任何 BDD 判定面

评审逐条比对后指出——`§4.1` 自述「本次处理」的文件里，下面这些**没有任何 BDD 覆盖**，且 §4.1 已把
「BDD-1 承接 `dispatch-protocol.md`」写成事实，与其实际判定面**不符**（声明≠实际）：

| 名单 | 位置 |
|------|------|
| `agate/dispatch-protocol.md` | `:881`（P8→READY 行含「bump-version + commit + tag 由主 Agent 亲自执行」） |
| `agate/rules/phases.yaml` | `:167`（P8 `gates` 措辞「version/CHANGELOG/tag 检查」）、`:169`（「先 tag 后重跑（DEBT0013）」） |
| `agate/assets/execution-roles/implementer.md` | `:101`（「P8 模式禁止执行 git commit / git tag」） |
| `agate/phase-cards/P8-release.md` | `:11/:12/:37/:50`（releaser 不执行 tag / 主 Agent 统一 commit+tag / 首入步骤；BDD-1 只覆盖该卡的 READY 条件面 `:122/:156`） |

**为何必改**：本任务的核心失败模式就是「只改一处 ⇒ 卡片/gate/工作流不一致」（正是 RM-AG0103 的编制理由）。
P6 的机械机制是**逐条对照 P1 的 BDD**（PASS/FAIL 总数 ≥ BDD 总数）；上述语料面无 BDD ⇒ **P6 无从机械断言**，
只能等 P7 定性核对发现——**P7 是不同镜头，不能替代 P6**。

**修法（择一，主 Agent 倾向 ①）**：
① **扩 `BDD-1` 的判定面**：`Given` 改为「`agate/` 活面内描述 P8/READY 的语料」并**显式列举**：
`state-machine.md`、`phase-cards/P8-release.md`、`rules/state-transitions.md`、`rules/phases.yaml`、
`dispatch-protocol.md`、`assets/execution-roles/implementer.md`；`Then` 改为「上述语料面内
`git tag` / `tag 已创建` / 同类 tag 条件表述**零命中**」，并**显式列出不处理项**（`UPGRADING.md` 的历史
迁移章节、`CHANGELOG.md` 的发布产物、`agate-workspace/archived/**` 快照）⇒ 判据仍可二值。
② 新增 1 条 BDD（如 `BDD-21`）专载「P8 语料面 tag 条件零残留」的机械检索断言。

**无论择哪条，都必须**：在 `§4.1` 的**每一行**「本次处理」标注它由**哪条 BDD** 承接
（建立「语料面 ↔ BDD」的可追溯性，消除声明与实际不一致）。

---

#### (B) 【必改】`BDD-4 / BDD-5 / BDD-14 / BDD-20` 在 `Then` 行内嵌了第二组 G-W-T

现状形如「…；且 Given X 时 Then Y」，与你自己在 §3 自述的「每条**单一** Given/When/Then」相抵，
也与角色文件检查项「每条 BDD 是否只有一条 G-W-T（多场景是否已拆为独立编号）」相抵。
全仓 `P1-requirements.md` 实测 `grep "且 Given"` **零命中**（仅本文件命中）⇒ **无先例**。
后果：P6 逐条对照时「正例 + 反例」记作**一条**，实现只满足正例也可判 PASS（反例未独立计分），削弱验收强度。

**修法：拆成独立 BDD 编号，并保持编号全局连续。**
⚠️ **必须用纯数字编号重排，禁止使用字母后缀（`BDD-4a` 之类）** —— 主 Agent 已实测：
① `check-p6-provenance.py:615` / `check-judge-verdict.py:110` 等计数器用 `^#### BDD-[0-9]`（后缀**能**匹配）；
**但** ② `check-judge-verdict.py` 的逐条 verdict 行解析用 `BDD-([0-9]+)\s*[:：]`
（`^\s*-\s*(PASS|FAIL|NEEDS-REVISION)\s+BDD-([0-9]+)\s*[:：]`）——**`BDD-4a:` 不匹配** ⇒
P6.5 judge 的 `criteria_total`（条数）与逐条解析数会对不上，**在 P6.5 才炸**。
⇒ 请**重排为纯 `#### BDD-NN:` 连续编号**（如 1..24），不做任何字母后缀。

重排后 `reviewed_bdds` 的集合会由评审在下一轮重标，**你不需要处理它**。

---

#### (C) 【随改】`BDD-7/8/9/11` 的判定载体「发布门」在本任务内**尚不存在**

四条都以「When 运行发布门」触发，但没点名任何脚本/步骤（BDD-10 例外，它自带替代载体
`check-protocol-consistency.py`）。请在 BDD 内点明**可观察载体**，或统一附注：
「发布门 = 创建 tag 前的一道可执行校验；**载体由 P2 定**，P6 按其命令 exit code 判定」。
（这是**可判定性补强**，**不是**要你在 P1 定实现——P1 仍不得掺入方案设计。）

#### (D) 【随改】`BDD-20` 是条件式（「Given 实现**若**新增/改名 …」）⇒ 未新增时**恒 PASS**

会造成 P6 计数虚高与「假绿」。请注明：**若 P2 判定落为 `agate-*.py`，本 BDD 记为 N/A 不计 PASS**；
或在 P2 定下落点后转为无条件 BDD。

#### (E) 【随改】`packages` 未归属 `BDD-12` 的两个判定文件

根 `AGENTS.md` 与 `agate/git-integration.md` 是 BDD-12 的判定对象，却不在 `packages` 8 项内 ⇒
P7 按 `packages` 做跨文件交叉核时会漏。请归入某 package（或显式声明「doc 面不单独计包」并说明 P7 覆盖口径）。

#### (F) 【可选，不阻塞】

- **F-2（建议采纳）**：`BDD-15` 的 `Then` 把机制名 `workflow_dispatch` 写成了文档要求。
  若 P2 换用其它授权机制（如 environment protection），该 BDD 会失真。改为
  「**人工授权入口**（当前实现为 `workflow_dispatch`）」（低成本、防失真）。
- **F-1（建议加一句）**：`BDD-11`（发布门校 roadmap RM `done`）与 `gate_p8` 既有 RM-AG0043 反查**重叠**；
  `BDD-10`（CHECK 7/13）亦与既有 CI required 重叠。请补一句**保护优先级/谁兜底**的显式声明。

---

### 约束（本轮补充）

- **只改 `P1-requirements.md`**；不改 `P1-review.md`、不改任何协议/脚本/测试文件。
- **不得降低既有 BDD 的强度**（不许把可二值判据改软、不许删 BDD 场景）；改动方向是**增覆盖、拆编号**。
- **不得掺入方案设计**（P1 只定义"做什么 / 做完什么样算对"）。
- 修复内容写在 `P1-requirements.md` 正文（不是只写 progress）。
- progress 仍**追加**（不是覆盖）到 `P1-progress-analyst.md`。

### 产出与自检

- 产出路径不变：`{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P1-requirements.md`
- 返回前跑：`python3 agate/scripts/check-frontmatter.py <该文件路径>`，非 0 先修正
- 自检：① `#### BDD-NN:` 编号**连续无跳号**、**无字母后缀**、每条**恰一组** G-W-T；
  ② §4.1 每行「本次处理」都标了承接 BDD 编号；③ 无新引入的 `[NEED_CONFIRM]`

### 返回

只返回两行：① 产出文件路径 ② 一句话摘要（≤30 字，格式：修复 (A)(B)(C)(D)(E)，N 条 BDD）。
不要返回文件全文。
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
# ── TAG0050 批 E/F 结构化字段（非 legacy 任务）──
# scope_plus: [{id: SP1, text: "增补项"}]   # list；P7 聚合，须被 scope_resolved 覆盖
# pruned: [{phase: P3, reason: "low 风险可裁", risk: low}]  # 跳过阶段；phases ∪ pruned == phase_universe（恒检）
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
5. **机械门禁必须实测，不得推理**：凡本任务**新增或改名 `agate/scripts/` 下的脚本/文件**，除逻辑上的同类扫描外，还须对「**既有测试与 gate 是否会因这个新文件被触发**」做**实测**——把文件真放进仓库，跑一遍相关测试与 consistency，记录**实际**变红/告警的面。「凭推理判『不处理』」在本仓库已被证伪（TAG0036 M18：P1 推理判"不处理"，P2 评审实测才发现 SG.6 由绿转红）。登记面权威清单见 `agate/scripts/README.md`「新增脚本登记面」节（该节已区分**机械门禁**与**团队约定**，照单登记前先看类型列）。

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
- [ ] 若本任务新增/改名 `agate/scripts/` 下文件：登记面已按 `agate/scripts/README.md`「新增脚本登记面」节**实测**过（不是推理），并记下实际变红/告警的面
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
