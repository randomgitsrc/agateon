# 编排语义统一设计（自动化在协议内，平台只做执行环境）

> 状态：**已落地（TAG0027，v0.66.0，RM-AG0054：`agate next`/`agate advance` 推进侧 CLI）**
> 评审链：v1 经独立评审 FAIL（2 BLOCKER + 4 WARNING + 4 NIT，见 `docs/reviews/review-design-orchestration-semantics-2026-09-01.md`）→ v2 逐条修复 → 2026-09-02 经 Claude 独立评审（见 `docs/reviews/review-orchestration-semantics-v2-independent-20260902.md`）指出"PASS 标签无复审证据"（B1'）+ 护栏范围遗漏 WORKFLOW.md（W1'）+ 护栏机械化仍是未来时（W2'）+ 平台语义表排版（N1'）+ README 登记待核验（N2'）→ **本版 v3 修复上述全部发现并采纳其 4 条补充想法**（exit 2 可复核子状态 / CLI 为档位 C 可观测层 / S-1-S-2 纳入转移表 / 结构性判据替代文件名单）→ v3 经落盘复审 PASS（`review-orchestration-semantics-v3-20260902.md`，审查对象 v3a、4 个 NIT 修复闭环为 v3b，见该文件 4.5 节）→ 2026-09-02 第三轮 Claude 元评审（`review-orchestration-semantics-v3-claude-meta-20260902.md`）指出"复审指控失实"，经时间线核验（复审落盘 12:55 先于修复 12:59）该指控不成立，但其可追溯性建议已采纳（版本/时点标注 + 修复闭环确认）。
> 问题：Agateon 目前以 orchestrator agent 角色驱动运转，流程正确性押在模型的持续正确上；同时三平台（OpenCode / Claude Code / DSH）能力差异正在扩大。本笔记回答两个问题：① 编排能否程序化、程序化到什么程度；② 如何让三平台不走向"三条路线"。
> 相关文档：`agate/WORKFLOW.md`、`agate/orchestrator-template.md`、`agate/dispatch-protocol.md`、`agate/state-machine.md`、`agate/loop-orchestration.md`、`agate/rules/phases.yaml`、`agate/rules/state-transitions.md`、`docs/design-notes/dsh-integration.md`、`docs/design-notes/design-independent-judge.md`、`agate/platform-notes.md`、`agate/SETUP.md`。

---

## 1. 问题定义

### 1.1 现状机制

Agateon 的运转模型是"协议 + orchestrator 角色"：

```text
协议 agate/（P0-P8 阶段 + BDD + gate 脚本 + 状态 schema）
        ↑ 被读取/执行
orchestrator agent ── 四项职责：读状态 → 派发 subagent → 跑 gate → 更新状态
        ↑ 派发（prompt 带角色文件路径）
subagent（执行角色）── 产出 → gate 脚本 exit code 判定
```

三个关键设计（已实证有效，不推翻）：

1. **状态显式落盘**（`.state.yaml` / `active-tasks.md` / `roadmap.md`）——跨会话、跨 agent 可恢复，不依赖模型记忆；
2. **判定可执行化**（BDD-9：exit code 才是门槛）——质量判断从"模型自律"转移到"脚本强制"；
3. **角色薄化**（执行角色不预注册，派发时给路径自读）——协议升级不动 agent 注册。

### 1.2 两个张力

| 张力 | 具体表现 |
|------|---------|
| **推进决策仍是模型** | 判定被 gate 接管了，但"当前 phase 该读哪张卡、gate 过了该不该 advance、红灯批该派几个"仍是 orchestrator 这个模型做的。流程正确性从"产出判定"转移到"编排决策"，后者没有脚本兜底——这与"exit code 才是门槛"的精神相悖 |
| **平台适配面在扩大** | 三平台工具面不同（DSH 有 workflow/ralph/goal，另两个没有），若按"各平台各自最优"演进，会形成三套食谱、三套心智，协议被平台绑架 |

**现状盘点（v2 修正）**：状态机侧已有大量资产，问题不是"没有状态机"，而是**推进决策未机械承接**。已有：`state-machine.md`（状态集合/转移规则/PAUSED 恢复）、`loop-orchestration.md`（三档自动化，档位 C 全自动跑 P1-P8、硬中断点必停）、`check-state-transition.py`（跳变合法性/重试超限/回退 diff≥2 机械校验）、`agate-retreat-to.py` / `agate-retreat-state.py` / `agate-archive-stale-outputs.py`（自动化多步回退 + 归档）、`rules/phases.yaml` + `rules/state-transitions.md`（TAG0021 结构化层数据面）。**真实缺口收敛为两点**：① 转移表的"下一 phase / 回退边"未结构化（phases.yaml 无此字段）；② 推进侧无 CLI（无 `agate next` / `agate advance`），推进由 orchestrator 临场决策。

---

## 2. 讨论过的方案

| 方案 | 做法 | 否决/采纳理由 |
|------|------|--------------|
| A：保持现状 | orchestrator 继续同时做执行者和决策者 | 决策面无脚本兜底，流程正确性押在模型持续正确上；不作为终态，但作为过渡态 |
| B：全程序化（通用图引擎）| 引入 langgraph 类框架，把 P0-P8 建成动态图 | **否决**。P0-P8 是固定主线（P0→…→READY）+ 有限非主线边（回退/PAUSED/裁剪跳变），不需要图引擎；langgraph 的复杂度（动态构图、checkpoint、人工中断）不产生价值，反而带来依赖锁定与学习成本 |
| C：领域专用状态机（采纳）| 复用既有状态机资产，协议定义转移表，脚本跑状态机，模型是节点 | **采纳**。P0-P8 的主线推进是确定性状态机：`{phase, gate_exit_code, 输入产物} → 下一 phase`。既有 `check-state-transition.py` / `rules/phases.yaml` / 回退 CLI 已覆盖大半，缺口是转移边结构化 + 推进侧 CLI |

---

## 3. 核心洞察：三层拆解

"编排程序化"必须拆成三层，可程序化程度完全不同：

| 层 | 内容 | 可程序化程度 |
|----|------|-------------|
| 流程层（编排）| 主线推进、gate 判定、单步回退 | ✅ 主线推进与单步回退可程序化（确定性状态机）|
| 判定层（验收）| 产出好不好、bug 修没修 | ⚠️ 混合——可判定的走脚本（BDD/gate exit code），不可判定的走 judge 模型节点 |
| 内容层（执行）| 需求/设计/代码/验收文档 | ❌ 永远不能——这是 LLM 的工作 |

**v2 修正（W1）**：流程层不是"100% 可程序化"，而是**"主线推进 + 单步回退"可程序化**。既有状态机含大量非确定性成分，必须显式建模为**状态机暂停点（转模型/人工）**：

| 非确定性成分 | 性质 | 程序化边界 |
|-------------|------|-----------|
| PAUSED 汇合 | 任意阶段遇 NEED_CONFIRM / PROD_TOUCHED / GAP / retry 超限 → PAUSED（state-machine.md:95-99, 254-263）| 触发条件可脚本判定，恢复决策转人工 |
| 跨阶段回退 | P5/P6 gate 失败 → 回 P4；回退 diff≥2 → 强制 PAUSED + 人工批准（state-machine.md:132-133, 148）| 回退目标表驱动（P5/P6→P4），diff≥2 判定已由 check-state-transition.py 机械拦截 |
| 裁剪跳变 | P1 裁剪声明驱动 P2→P4 / P5→P7 / P6→P8 / P7→DONE 等跳边（state-machine.md:218-224，跳过无 TDD/无验收/无一致性/无发布阶段）| 跳边由 P1 analyst 产出 + 主 Agent 确认——转模型 |
| SCOPE+ 定向回补 | 任意阶段发现新需求 → 增补 P1，"判断影响范围"依赖主 Agent（state-machine.md:233-241）| 无明确决策规则——转模型 |
| P6.5 judge 门槛 | 判定层模型节点（WORKFLOW.md:310）| judge 是模型节点，但其 verdict exit code 进入程序化状态机 |

**结论**：主线推进 + 单步回退可以 100% 程序化；判定层保留 judge 模型节点（但 judge 的"采纳/驳回"exit code 进入程序化状态机）；内容层本就不该程序化。所以"完全编排程序化"在**主线子集**上能做到——但"完全编排"不等于"完全自动化"，非确定性成分显式保留为暂停点。

---

## 4. 采纳的设计

### 4.1 编排心智统一（语义在协议，执行在适配）

**统一锚点是 dispatch-protocol 的实际五模式**（dispatch-protocol.md:511-519）：

| 模式 | 名称 | 何时用 |
|------|------|--------|
| 模式 1 | 单发 | 工作量 low / medium，单个 subagent 可靠交付 |
| 模式 2 | 静态拆批 | 产出可预先划分成互不依赖的批次 |
| 模式 3 | 并行 | 批次间无数据依赖、无共享文件改动 |
| 模式 4 | 先理解后拆 | 工作量 high / 结构不明 / 无法预先确定拆分方案 |
| 模式 5 | 串行链 | 批次间有强依赖（后者依赖前者的产出）|

> v2 修正（B1）：v1 误把 DSH 工具映射（workflow 的 pipeline、ralph、goal）当作协议五模式——那恰违反本笔记 4.3 护栏 1。统一锚点必须是**协议侧**的 dispatch-protocol 五模式；DSH 的 workflow/ralph/goal 是这些语义的**实现**，见 4.2。

orchestrator 在**任何平台**上只说同一套心智：

> 按五模式判定该单发还是拆批 → 派一批 subagent，每个带角色路径 → 各自产出 → 跑 gate 判 exit code → 失败按转移表回退

### 4.2 自动化在协议内，不依赖平台能力

自动化的三件套**没有一样依赖平台**：

```text
推进决策  → 状态转移表（rules/phases.yaml 扩展 + state-machine.md 口径）
判定      → gate 脚本 exit code（check-gate.py，三态：0 直推 / 1 回退 / 2 暂停转主 Agent）
状态      → 落盘文件（协议自有 schema）
```

这三样都是 Python 脚本 + 数据文件 + markdown 权威源，在**任何**平台（甚至没有模型、只有人照着执行）上都成立。平台因此被降级为：

> **平台 = 模型的执行环境，不是编排环境。**

它只负责两件事：① 跑模型产出内容（subagent）；② 提供 bash 跑协议脚本。流程怎么走完全在协议内——所以 DSH 的 `workflow` / `ralph` / `goal` 对协议是**可选加速器**（批次渲染省手写），不是依赖：哪天某平台没有这些工具了，退回"多路 subagent"流程照转，因为批次清单数据在协议手里。

**v2 修正（W4）：exit code 必须建模为三态**，不能假设"exit code → 唯一后继"：

| exit code | 语义（check-gate.py:6-7）| 状态机动作 |
|-----------|--------------------------|-----------|
| 0 | gate 通过 | 直推下一 phase |
| 1 | gate 未通过 | 按转移表回退（如 P5/P6 → P4，retry+1）|
| 2 | 需主 Agent 自判（动态 gate_commands / 语义判断）| **暂停转主 Agent**；**P6 例外**：P6 exit 2（FAIL=0/证据非空 + provenance exit 0）→ **前进 P6.5**（judge 复核，state-machine.md:139）——P6 的 exit 2 是"脚本化部分通过后的过渡态"而非"需额外自判" |

> 注（N-New4）：exit 2 的"暂停转主 Agent"是多数阶段的通用语义，P6 是唯一"exit 2 直通下一子阶段"的例外（该例外是既有状态机的固定口径，转移表照抄，不泛化）。

即"推进决策查表 + exit 2 分支人机混合"——exit 2 是"推进决策仍是模型"的显式残留点（1.2 张力 1 的诚实边界，不假装消除）。

**v3 采纳（Claude 评审想法 1）：exit 2 的"下一动作"建模为可机械复核的子状态**，而非自由文本占位。要求 exit 2 分支的解决必须落盘一个机器可读产物（如 `exit2-resolution.md` 或 `.state.yaml` 字段，记录"何时 / 依据什么客观证据 / 由谁解决"），纳入 P6.5 judge 或 provenance 审计的复核范围——这样"必须信任模型的区间"至少留下审计痕迹，与协议"判定权可以留给模型，但过程必须留痕"的一贯思路一致。这不是消灭 exit 2 的模型依赖（1.2 已诚实承认），而是让该依赖可被事后核查。

> 实现注记：平台名只出现在挂此标记的小节/段落（如本表、4.4 的渲染示例），不进入协议语义定义。以下为同一语义的三平台实现映射，非协议语义定义：

| 协议语义 | DSH 实现 | OpenCode / Claude Code 实现 |
|---------|---------|----------------------------|
| 并行 / 静态拆批（模式 2/3）| `workflow` 脚本 `parallel`+`agent` | 一次发 N 个 Task 调用 |
| 独立复核（judge，P6.5）| `ralph`（fresh context）| 新开会话 / 派 spawn 子 agent |
| 跨轮续跑 | `goal` 工具 | 手动重开会话读 `.state.yaml` |

这不是"不同路线"，是"同一路线的不同实现"——orchestrator 的编排心智三平台完全一致，变的只是"说这句话的口音"。该表带「实现注记」标记（4.3 想法 4 的结构性判据锚点），与协议语义叙述（4.1 五模式表）排版分离。

### 4.3 护栏：三条规则防止路线分叉（v3 修正 W1'/W2'：补 WORKFLOW.md 归属 + 结构性判据）

1. **协议概念禁止平台特化**：协议层只认 dispatch-protocol 五模式 + judge + 跨轮续跑语义，不发明"workflow 模式"、"ralph 模式"这类以平台工具命名的概念。**可操作判据（v3 修正，采纳想法 4：结构性判据替代文件名单）**：凡 `rules/*.yaml` 等机器可读数据面，禁止出现平台名（OpenCode / Claude Code / DSH / workflow / ralph / goal / task）；凡 markdown 叙述文档，允许出现平台名，但**仅限带「实现注记」标记的小节/表格**（统一格式约定：`> 实现注记：` 标记行，见 4.2 的平台语义等价表示范）。这样护栏检查不需要维护一份不断增补的文件名单，而是扫描"markdown 里不含实现注记标记、但含平台名的段落"——新增任何权威文档都自动被覆盖；
2. **平台差异收敛为"如何实现"**：`platform-notes.md` / `SETUP.md` / `WORKFLOW.md`「已知适用环境」表 **整文件/整表视为"如何实现"**（v3 修正 W1'：它们是平台适配权威源，平台名集中于此是正确组织，不违反护栏；`WORKFLOW.md:143-148` 的「已知适用环境」表描述的是"这份文档在哪些平台验证过"，是元信息而非编排语义，与 `platform-notes.md` 同类豁免）。协议文档里平台名只出现在"如何实现"小节，不出现在"语义"小节。**可操作判据**：平台名出现的段落必须挂「实现注记」标记或指向数据面（`rules/*.yaml`）或阶段卡片，不得自称语义定义；
3. **通用食谱先于平台食谱**：编排心智写成平台无关的一份，DSH 的 workflow 只是"这份通用食谱在 DSH 上的快捷实现"——读者先学语义，再学口音。**可操作判据**：新增平台食谱前，先确认通用食谱里已有对应语义；语义文档评审时检查"平台名是否出现在语义小节"。

**可判定化方向（对齐"exit code 才是门槛"；v3 修正 W2'：明确排期与残留点）**：三护栏目前是文档写作纪律（评审时人工检查），机械化是**随 RM-AG0054 一起排期的方向**（不做则遗留"协议一致性靠评审员把关"的残留点，与本笔记 4.2 对 exit 2 分支的诚实态度一致，不假装消除）。落地形态：`check-protocol-consistency.py` 增加"扫描 markdown 中含平台名但无「实现注记」标记的段落"检查（按护栏 1 的结构性判据，非文件名单），把护栏从"评审时检查"升级为"CI 硬校验"。

### 4.4 不造轮子的正确姿势（v2 修正 N3：措辞降级；v3 修正 N-New2：补实现注记）

不该造的是"另一个 workflow 引擎"；该造的是"批次语义 → 各平台派发指令"的渲染层：

> 实现注记：以下渲染示例是平台实现的"翻译层"说明，非协议语义定义。

```text
协议层：P3 红灯批 = 模式 2/3 拆批（{task, role, gate}... 数据）
  ↓ 渲染
DSH      → workflow 脚本（parallel + agent）
OpenCode → "同时派发 N 个 Task，各带角色路径"指令
Claude   → 同上
```

数据是同一份（批次清单 + 角色 + gate），只是翻译成各平台的语言。DSH 的 `workflow`（`agent`/`pipeline`/`parallel`/`phase` 四钩子）与 OpenCode 的[社区提案 issue #20849](https://github.com/anomalyco/opencode/issues/20849)（"Plugin-based agent orchestration layer"）表明**平台层有向该方向演进的社区提案**（注意：单一 issue 不代表官方路线图，表述到此为止）——协议层现在定义好语义，将来平台能力对齐时适配层跟着换就行，语义不用动。

---

## 5. 与现有资产的衔接（v2 修正 B2：完整盘点，避免重复造轮子）

| 既有资产 | 实际功能 | 与本文档的关系 |
|---------|---------|---------------|
| `state-machine.md` | 状态集合 / 转移规则 / 回退规则 / PAUSED 恢复 / 单步函数 | 权威语义源，本文档引用不改 |
| `loop-orchestration.md` | 三档自动化（手动 / 半自动 / 全自动 /loop），档位 C 自动跑 P1-P8、硬中断点必停——但推进节奏目前由主 Agent 自律 | 状态机 CLI 是档位 C 的**可观测层**：档位 C 的自动推进强制走 `agate next`，消除模型自律环节（见下方缺口 3）|
| `check-state-transition.py` | 跳变合法性 / 重试超限→PAUSED / 回退 diff≥2→强制 PAUSED 机械校验 | "状态转移表 + 机械校验"的现成骨架，推进侧 CLI 复用它 |
| `agate-retreat-to.py` / `agate-retreat-state.py` / `agate-archive-stale-outputs.py` | 自动化多步单向回退（每步独立 gate 校验）+ 被跨过阶段产出归档 | 回退侧 CLI **已存在**，不是缺口 |
| `rules/phases.yaml` + `rules/state-transitions.md` | phase/id/exec_role/outputs/gates/retry_cap 数据面 + S-1/S-2 一致性 gate | Phase 1 **扩展它**（增 next/retreat 字段），不新建 schema |
| `agate-next-card.py` | 按 PHASE 参数输出阶段卡片全文（sha256 校验契约 + M3 从 phases.yaml 渲染可判定节）| 不承担"选下一张"逻辑——推进选择正是缺口 |
| `check-gate.py` | gate 判定（exit 0/1/2 三态契约 + 第 3 参 OLD_PHASE 回退检测）| 判定侧已完备，状态机直接消费 exit code |
| `agate_common.py` | 公共函数库（write_gate_result / read_state_phase / resolve_workspace 等）| 推进 CLI 复用 |

**真实缺口（收敛后）**：

1. 转移表的**"下一 phase / 回退边"**未结构化——`phases.yaml` 有 phase/gates/retry_cap，但没有 next/retreat 字段（评审 B2 确认）；
2. **推进侧 CLI** 不存在（无 `agate next` / `agate advance`）——回退侧已有 `agate-retreat-to.py`，推进侧是空白；
3. **与 /loop 的关系（v3 采纳想法 2：CLI 是档位 C 的可观测层，非机械替身）**：`loop-orchestration.md` 档位 C 已实现"自动跑 P1-P8、硬中断点必停"——但档位 C 的"自动推进"目前由**主 Agent 自己反复判断"该往下走了"**（同一个模型在多轮里对自己说"继续"），这本质上是 1.2 张力 1 在宏观循环层面的同一问题。状态机 CLI 落地后，档位 C 的"自动推进"应**强制走 `agate next`**（主 Agent 只执行内容，循环节奏由脚本控制），即 CLI 是档位 C 的**可观测层**——它不仅替代档位 C 的实现，更**消除档位 C 里唯一一处完全依赖模型自律的环节**（"知道什么时候该停、什么时候该继续"）。落地时补一条 BDD 方向：验证"档位 C 全程使用 `agate next` 推进，主 Agent 从未自行判断是否进入下一 phase"。

---

## 6. 落地路径（v3 修正：复用既有资产，不新建 schema；采纳想法 3：纳入 S-1/S-2）

```text
Phase 1：扩展 rules/phases.yaml 增 next/retreat 字段（或扩展 rules/state-transitions.md 数据面），
    对齐 state-machine.md 既有转移语义（P5/P6→P4、P6.5→P6、diff≥2→PAUSED）
    【v3 采纳想法 3】新增字段直接纳入既有 S-1/S-2 双向一致性 gate 的检查范围
    （check-structure-consistency.py：S-1 YAML→md 以 WORKFLOW.md 阶段总览表为 md 侧锚点，
    S-2 md→YAML 反向，行 7-11）——转移表数据面与 WORKFLOW.md 总览防漂移，
    不新开独立一致性检查
Phase 2：写推进侧 CLI（agate next / agate advance），消费 check-state-transition.py 校验
    + check-gate.py exit 三态（含 exit 2 的 exit2-resolution 落盘产物）；
    与 agate-retreat-to.py 回退侧对接；档位 C 的自动推进改走 agate next
    （补 BDD："档位 C 全程用 agate next 推进，主 Agent 未自行判断进入下一 phase"）
Phase 3：编排心智统一文档化——dispatch-protocol 五模式作为唯一语义锚点，
    平台差异（workflow/ralph/goal）全部挂「实现注记」标记（4.3 结构性判据格式约定）
Phase 4（可选）：渲染层——批次清单 → 各平台派发指令（DSH 先做）；
    护栏 1 机械化（check-protocol-consistency.py 扫描含平台名无实现注记的段落）
```

---

## 7. 风险与对策（v2 修正 W2：回退语义对齐既有状态机）

| 风险 | 对策 |
|------|------|
| 转移表把回退路由写错（绕过既有语义）| 回退目标**照抄 state-machine.md**：P1/P2 review rejected → 回自身（retry+1）；P5/P6 gate 失败 → 回 **P4**（retry+1）；P6.5 needs-revision → 回 **P6** 重验（judge 轮次 ≤2）；回退 diff≥2 → **强制 PAUSED** + 人工批准（check-state-transition.py 机械拦截，转移表与之一致，不搞双套判定）|
| 转移表把 P6.5 当独立 phase | P6.5 是挂载于 P6→P7 转移上的**强门槛子阶段，非独立 phase 值**（state-machine.md:74-78）——schema 用"子阶段门槛（挂载于转移上）"表达，.state.yaml 的 phase 保持 P6 直至 P7 |
| exit 2 分支无后继 | 转移表建模 exit 三态（0 直推 / 1 回退 / 2 暂停转主 Agent），为 exit 2 定义"下一动作"字段（如 P5 exit 2 → 主 Agent 跑 gate_commands.P5）；**v3 采纳想法 1**：解决必须落盘机器可读产物（exit2-resolution），纳入 P6.5 judge / provenance 审计复核范围，留下审计痕迹 |
| judge 层仍是模型，无法完全程序化 | 接受"判定层混合"为设计边界；judge 的输出（verdict exit code）进入程序化状态机 |
| 平台能力演进（如 OpenCode 加编排引擎）| 语义层不动，只换适配层渲染——这是 4.3 护栏的收益 |
| 协议概念被平台名污染（文档层）| 执行 4.3 三条护栏（结构性判据：数据面禁平台名 / 叙述面挂实现注记），并推进"含平台名无实现注记标记段落"的 consistency 检查（随 RM-AG0054 排期）|
| 状态机 CLI 与 /loop 档位 C 重叠 | 定位为档位 C 的**可观测层**（档位 C 推进强制走 agate next，复用"硬中断点必停"语义），先论证关系再实现，避免双套自动化 |
