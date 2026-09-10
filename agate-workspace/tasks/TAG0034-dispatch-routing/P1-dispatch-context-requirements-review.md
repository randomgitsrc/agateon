---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: requirements-review
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

独立视角评审 `P1-requirements.md`（TAG0034 派发路由需求基线，**现 53 条 BDD**，含 DEBT0039 并入的 BDD-48/49/50），产出 `P1-review.md`。**只审不写** —— 不直接改 P1-requirements.md；发现问题写进评审意见，由主 Agent 回派 analyst 修改。Header `status:` 必须落 `approved` / `rejected` / `needs-revision` 之一（gate 读该字段，与返回摘要必须一致）。

### ⚠️ 本轮是复核轮（P1 retry #1）

上一轮你（requirements-review）产出 `P1-review.md` 结论 `needs-revision`，2 项阻塞 + 4 项非阻塞。analyst 已修订。**本轮重点是复核这 6 项是否修好，不需要从头重审全部 53 条**（其余已通过项如无连带影响不必重复逐条判定，但编号连续性 / 无新增矛盾仍要扫一遍）：

| 项 | 上轮要求 | analyst 自报修订 | 你复核 |
|---|---|---|---|
| 阻塞 1 | BDD-31 Then 去掉漂移版本串 `claude-haiku-4-5-*`，改锚定机制 | Then 改为「`modelUsage` 实际 model 与候选 `model: haiku` 经档位/别名解析后目标一致，且非父会话继承」，保留「驱动会话零判断」 | Then 是否已无硬编码 model family 版本串、判据是否锚「可核实实际 model」的机制、仍可二值判定 |
| 阻塞 2 | 新增 P5→P4 回退重解析路由 BDD + BDD-26 补边界注 | 新增 BDD-51（§4.18）：P5→P4 跨阶段回退 P4 retry 机械重解析一次路由、无升档逻辑、与 BDD-26 显式不冲突；BDD-26 Then 末尾补边界句；§2 边界行改写（同阶段=同候选 / 跨阶段回退=机械重解析） | BDD-51 单条 GWT 可二值判定；BDD-26 与 BDD-51 措辞是否真的不再有张力（同阶段 gate-FAIL retry=同候选 vs 跨阶段回退=重解析，两者边界清晰）；§2 边界行是否同步 |
| 非阻塞 3 | BDD-35 Then「结论稳定」措辞收紧 | 补「构造样本已知正确 verdict = 该 turn 整体成功，解析结论须等于该 verdict」 | 措辞是否够硬 |
| 非阻塞 4 | BDD-38「余量」量化 | 「余量」→「P2 定值，建议 ≥10s」 | 是否可接受 |
| 非阻塞 5 | BDD-46 一条 Then 塞 6 断言 → 拆 | 拆为 BDD-46（落点三层 + 核心循环 try-and-fall）/ BDD-52（两轴 + `(phase,role)` key + 弱/强缓解 + 自动化不对称）/ BDD-53（两条完整性不变量 + per-machine），BDD-46 加注指向 52/53 | 三条是否各自可独立 PASS/FAIL、编号连续（BDD-52/53 在 §4.18）、§9「P6 总数」已改 ≥53 |
| 非阻塞 6 | §3 第 8 行 `roadmap.md:68` 行号不符 | 改为「`agate-workspace/roadmap/roadmap.md` 的 RM-AG0060 行」，BDD 引用补 44/47 | 是否已校正 |

复核通过（6 项都修好、无新引入问题、编号 1~53 连续）→ `status: approved`（逐条锚点可复用上轮 BDD 判定 + 本轮 6 项复核结论，不必重抄 53 条全文，但 approved 结论须显式覆盖全部 53 条的「已判定通过」声明 + 本轮 6 项）。仍有问题 → `needs-revision`（P1 retry #2，MAX=3）。

### 约束

- **实质锚点要求**：结论不得是裸 `approved` / `BLOCKER=0`。`approved` 必须逐条列 BDD-1~50 判定 + 覆盖维度清单（数据/前端/多端/边界/兼容逐项标注）；裁剪合理性逐个跳过阶段 + 理由（本任务 `phases` 全走不裁，逐阶段核对「走」的理由是否成立即可）；审声明核对引用 `git diff --cached` 证据。
- **审声明核对（TAG0019）**：先 `git add agate-workspace/tasks/TAG0034-dispatch-routing/` 再 `git diff --cached --stat`，核对 analyst 的 `risk_level: medium` / `ceremony: standard` / `phases: [P1..P8]` 声明是否与暂存区实际改动（文件类型 / 规模 / 域）匹配。注意本阶段暂存区只有 P1 产出（md 文件），实际代码改动在 P2+ —— 核对口径是「声明与 P0-brief 描述的改动面是否自洽」，不是「暂存区已有代码 diff」。声明与实际不一致 → 结论必须 `needs-revision` / `rejected`，不得 `approved`。
- **BDD 可二值判定**：逐条查 Given/When/Then 是否可明确 PASS/FAIL、无「调整 / 部分通过」中间态、编号 `#### BDD-NN:` 连续不跳号（主 Agent 已机械核 50 条连续，你复核语义）、每条只有一条 Given-When-Then。特别关注：
  - BDD-24~28（完整性不变量，最高危）：判据是否真的可机械二值判定 —— 尤其 BDD-26「gate FAIL 后 `dispatch_route` 事件计数不增」、BDD-27「`gate_fail` 理由码被 `check-events.py` 拒」是否措辞成可 grep/计数的客观信号
  - BDD-34/35（Codex 两层 status）：是否把「P2 须明确取哪层」这一未决点如实留给 P2，而不是在 P1 就武断锁定
  - BDD-31/32（`cli: native`）：Then 子句是否绑定了会漂移的实现符号（model id 字符串 `claude-haiku-4-5-*` 之类）—— 判据应锚定「可核实实际 model」的机制而非硬编码版本串
- **隐含需求覆盖**：逐维度核对 §2 —— 数据（`gate-events.jsonl` append-only）/ 前端（明确排除，`domains` 无 frontend，是否成立）/ 多端（写入端↔校验端同步、`platform-notes.md` 三平台章、各 `SETUP.md` flag 小节）/ 边界（候选全灭 / CLI 未装 / 配置损坏 / gate FAIL retry / P5→P4 回退重解析 / 五模式并行 / 自主再派发 / 单 Agent 模式）/ 兼容（「不配置 = 逐字节现状」、`standard` 语义钉死）。有遗漏维度直接指出。
- **同类扫描核对（§3）**：9 组扫描（第 9 行为 DEBT0039 带入的 architect.md 新增面）的命中数 / 文件清单 / 逐条处理判定是否可信；特别是第 6 组「routed-away judge verdict 非真缺口」的结论 —— analyst 判定 `check-judge-verdict.py` / `check-p6-provenance.py` 纯 TASK_DIR 文件解析、平台无关。你要独立核这个结论（可自己 grep 这两个脚本看有没有读 `~/.claude/` / `~/.codex/` 的路径）。若结论站不住 → `needs-revision`。
- **P1 纯净性**：有无掺入解决方案设计 / 实现细节。本任务 BDD 天然贴近机制（schema 字段名、flag 名、事件字段），判据是「BDD 描述的是可验收的行为 / 客观信号，还是在替 P2 做设计决策」。§5 的 6 条 `[SUGGEST:]` 是 analyst 的设计倾向留底（tier 命名 / `model: null` 合法 / MVP 合并①③ / 三层优先级 / 扩 `agate-dispatch.py` 子命令 / 新增 `check-dispatch-routing.py`）—— 这些是「有倾向待主 Agent 采纳」的非阻塞项，不是 P1 越界做设计；核对它们确实以 `[SUGGEST:]`（非 `[NEED_CONFIRM]`）呈现、且不涉破坏性变更 / 业务方向即可。
- **裁剪合理性**：`phases` 全走不裁 —— 核对 §7 逐阶段「走」的理由；`risk_level: medium` 是否与「改协议本体 + 三层配置 + 完整性不变量高危」匹配（偏低则指出）；`ceremony: standard`（不薄化）是否恰当；capability_requirements 三态（三条全 `available`、无 GAP）判断是否正确 —— 尤其 `opencode-bug2-repro` 归 `available` 而非 `supplementable`（口诀：本机可做的真机测试 vs 换更强模型才能做）。
- **范围核对**：P1-requirements.md 是否有任何一条 BDD / 隐含需求越出 `P0-brief.md` 的 scope / out-of-scope 边界（P0-brief out-of-scope 明确排除：动态选型 / 续接软信号根治 / 第三方终端工具作依赖 / DSH / 局限 3 / RM-AG0055 机制本身 / RM-AG0054 `agate next` 本身 / probe / 跨机可复现 / retry 故意换升档模型）。越界 → `needs-revision` 并指出具体条目。**例外**：§1 的 `[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]` 是**主会话已确认的用户批准新增面**（不是 analyst 擅自扩范围）—— 核对口径是「这一 SCOPE+ 是否如实登记（来源标注 + 边界约束 + closure criteria 转 BDD）」，而不是「它超出了 P0-brief 所以打回」。
- **DEBT0039 增补专项核对**：
  - §1 SCOPE+ 条目：来源是否标注为「用户批准 + DEBT0039 并入」（非顺手改漏）；边界约束是否写明「仅限 `architect.md`「批次设计」节 + `dispatch-protocol.md`「派发编排机制」节两处纯文档、不扩其它 DEBT、不改脚本/gate」
  - §3 同类扫描第 9 行：`agate/assets/execution-roles/architect.md` 是否**显式标为 P0-brief 声明改动面之外、经用户批准新增的改动面**（这是本次并入的关键披露，漏了 → `needs-revision`）
  - BDD-48/49/50：是否忠实承接 DEBT0039 的 3 条 closure criteria（① architect.md「批次设计」节含「补协议文档正文 = P4」边界措辞；② dispatch-protocol.md「派发编排机制」节区分 author 内容 P4 vs 一致性验证 P7；③ consistency `--strict-errors-only` 0 ERROR 回归）；判据是否锚客观信号（节标题 / 关键串 grep 命中 / exit code），可二值判定
  - §7 / §9：P4 是否明确「DEBT0039 两处文档修订 = P4 author 工作」（不是 P7）；P8 收尾是否含「DEBT0039 置 closed、task_id 空 → TAG0034」
  - `packages` 是否覆盖 architect.md（analyst 归 `agate-docs`，核对是否合理，或应显式加项）
- **格式**：约束节 / 评审正文避免行首 `- PASS` / `- FAIL`（被 `check-p6-provenance.py` provenance 预判检测匹配）；BDD 判定用「通过 / 不通过」或加引号，不用行首裸 `- PASS`。

> 子派发能力：不启用子派发能力（review 类角色）。

### 上游关联

- P1 analyst 已产出 `P1-requirements.md`（含一轮修复）：**50 条 BDD**（连续 1~50，主 Agent 已机械核）、`[NO_NEED_CONFIRM]`、6 条 `[SUGGEST:]`、frontmatter `check-frontmatter.py` exit 0。
- **DEBT0039 已并入**（用户 2026-09-09 明确批准，主会话确认转交条件后转交）：analyst 修复轮增补 §1 SCOPE+ 交付项 + §3 同类扫描第 9 行 + §4.17 BDD-48/49/50 + §7/§9 下游。DEBT0039 = TAG0033 复盘产物（`agate-workspace/debt/tech-debt.md`），根因是 `architect.md` 与 `dispatch-protocol.md` 没写清「author 文档内容 = P4」vs「跨文件一致性验证 = P7」的阶段边界。`agate/assets/execution-roles/architect.md` 是 **P0-brief 声明改动面之外、经用户批准新增的面**。
- frontmatter：`risk_level: medium` / `ceremony: standard` / `phases: [P1,P2,P3,P4,P5,P6,P7,P8]` / `packages: [agate-scripts, agate-rules, agate-docs, agate-tests]` / `domains: [backend, cli]` / `judge.enabled: true`（.state.yaml）。
- 时效性质疑：analyst 判无严重漂移，轻微偏移 `[P0_STALE: Claude Code 本机 2.1.266 vs P0-brief 记 2.1.263]`（patch bump）。
- 主 Agent 预跑 `check-gate.py P1` = exit 2（回退抵达态，暂不做完成度校验，属预期；正式校验在离开 P1 时）。
- 这是跨会话恢复任务，P0-brief 经两轮外部评审 + 2026-09-09 讨论定案，边界刻意收紧。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（**评审对象**）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（范围 / 边界核对基准：task / scope / out-of-scope / known_risks 12 条）
- `docs/design-notes/design-dispatch-routing.md`（设计意图来源；§2.1/§2.2 + 头部是本任务待修订项 —— 核对 P1 需求与「定案后的意图」一致，不是与 design-note 现状逐字一致）
- `docs/research/cross-platform-dispatch-mechanics.md`（三平台机制实测 A1-A19 + §10 复核清单 + §11 未尽项 —— 核对 BDD 里的 flag 名 / 结构化输出字段是否与实测一致，或如实标为待复核）
- `agate/assets/review-roles/requirements-review.md`（你的角色定义，已在 prompt 指出，此处再列）
- `agate/scripts/check-judge-verdict.py` + `agate/scripts/check-p6-provenance.py`（独立核对 §3 第 6 组「routed-away judge verdict 非真缺口」结论）
- `agate-workspace/debt/tech-debt.md`（DEBT0039 条目：核对 §4.17 BDD-48/49/50 是否忠实承接其 `closure_criteria`；`task_id` 字段现为空，P8 收尾补 TAG0034）
- `AGENTS.md`（仓库开发约定：gate 脚本分层、self-gate、CI）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P1-review.md agate-md-field-set --list` 查看应填字段；逐个 `agate-md-field-set <key> <value>` 写入（`status` 字段务必落 `approved`/`rejected`/`needs-revision`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
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
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P1 / status=active / judge.enabled=true
- P1-requirements.md 机械核查结果（主 Agent 已跑）：`#### BDD-NN:` 共 50 条、编号连续 1..50 无跳号（含 DEBT0039 增补的 §4.17 BDD-48/49/50）；`[NEED_CONFIRM` 0 命中；`status: GAP` 无实际命中（唯一匹配是散文「无 status: GAP」）；`[SUGGEST:` 6 条实体条目；`check-frontmatter.py` exit 0
- `check-gate.py P1` 预跑 = exit 2（回退抵达态，主 Agent 自判，非失败）
- CLI 版本（本机实测）：Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- 评审结论若为 approved：gate 脚本会检查 P1-review.md 含 BDD 编号锚点（`#### BDD-NN:` 引用）+ agent≠main + status:approved，缺任一 → gate exit 1
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
