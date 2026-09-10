# 子 Agent 派发协议

> 职责边界：派发操作层——可执行门槛判定命令、派发编排机制（工作量评估/并行规则/回退处理）、特殊事件恢复（详见职责声明表，P2-design.md §0）

> agate 核心文件，解决"主 Agent 不派发、自己一路走到底"的问题

---

## 问题诊断

agate 的派发协议把每次阶段推进翻译成**明确的工具调用 + 精确的输入输出规范**，解决「主 Agent 写入上下文」这类不可执行的模糊描述。

---

## 派发的三条铁律

### 铁律 1：派发 subagent，动词是"派发"不是"执行"

> 实现注记：主 Agent 调用的"派发工具"在各平台的实现命名不同（如有的平台叫 task 工具、Claude Code 的 Task 等）——具体工具名随平台而异，协议语义一律以"派发 subagent"为准，不绑定任何平台工具名。

主 Agent 到了某个阶段，**不自己产出文件**，而是通过平台的派发工具启动一个 subagent。

```
❌ 错误理解："P2 阶段我要产出 P2-design.md" → 主 Agent 自己写
✅ 正确理解："P2 阶段我要派发一个 architect subagent 去产出 P2-design.md"
```

### 铁律 2：prompt 只传文件路径，不传文件内容

```
❌ 错：把 P1-requirements.md 的全文复制进 subagent 的 prompt
✅ 对：prompt 写"读取 {AGATE_WORKSPACE}/tasks/{Txxx}/P1-requirements.md"
```

subagent 在自己独立的上下文里读文件。主 Agent 的上下文永远不碰这些文件的全文。**这是上下文隔离的核心。**

### 铁律 3：subagent 只返回"路径 + 一句话摘要"

```
❌ 错：subagent 把 P2-design.md 全文返回给主 Agent
✅ 对：subagent 返回 "已产出 {AGATE_WORKSPACE}/tasks/{Txxx}/P2-design.md，方案采用 schema version 表 + 迁移脚本目录，3 个迁移步骤"
```

主 Agent 只拿摘要做门槛判断，需要细节时让下一个 subagent 自己去读文件。

---

## subagent 返回校验（处理 subagent 自身失败）

subagent 可能崩溃、超时、不产出文件、或不遵守"只返回摘要"。主 Agent 收到返回后必须校验，不能假设 subagent 一定成功。

```
subagent 返回后，主 Agent 校验：
  1. 约定的产出文件是否真的存在？
      不存在 → 派发失败，计入重试，带"未产出文件"原因重派
  2. 返回是否是"路径+摘要"格式？
      返回了文件全文 → 直接判失败重试，要求 subagent 重新只返回摘要
  3. 产出文件是否含合法 Header（phase/task_id/parent/trace_id）？
      没有或不完整 → 门槛不通过，计入重试
  4. 产出文件内容是否非空且有实质内容？
      空文件或半截内容（写一半崩了）→ 视为失败，重试
   5. 独立验证 subagent 的声明：
       主 Agent 必须亲自执行 gate 命令验证门槛，不能仅凭 subagent
       返回的摘要或产出文件中的声明判定通过。
       例：P5 subagent 说 "failed=0" → 主 Agent 跑 gate_commands.P5
           确认 exit 0 且 failed 行确实为 0，才算通过。
   6. 修改类任务的文件内容校验（外部可观测）：
      subagent 返回"已修复/已实现"后，主 Agent 对声称修改的文件做最小验证：
      - 用 bash 执行 grep 确认新增/修改的代码行存在
      - 如果声称修改但文件内容未变 → 视为假完成，重派
      - 这不是"主 Agent 改代码"——主 Agent 只读验证，不写文件
   7. files_modified 路径校验：
      subagent 返回 files_modified: [path1, path2] 时，主 Agent 校验每个路径：
      - 路径对应的文件存在 + 非空 → 通过
      - 路径不存在或文件为空 → 假完成，重派
      - 无 files_modified 字段 → 退回第 6 条的 grep 校验（兼容旧格式）

任一校验失败 → 计入 `retries[Pn]`，超限则 PAUSED。
```

**关键：主 Agent 永远不信任 subagent 的口头返回，以自己执行的命令结果为准。**

### Subagent 假完成校验（D2）

subagent 报告"已修复/已实现"但文件未实际变更（T048 实证）。主 Agent 在收到 subagent 返回后，对产出文件做最小校验：

| 校验项 | 方式 | 触发 |
|--------|------|------|
| 代码文件真改了 | `git diff --stat HEAD` 或 `git diff --cached --stat` → 有非 .md/.yaml 变更 | P4 实现 |
| 测试真跑了 | grep test runner 输出签名于 P5-test-results/ | P5 验证 |
| review 真审查了 | N3 锚点检查（BDD 编号引用 / DESIGN_GAP 配对引用） | P1/P7 review |
| 验收真跑了 | provenance 审计（证据-结论对应 + BDD 总数对照） | P6 验收 |

**假完成 ≠ 失败**：subagent 可能真的做了但结果和之前一样（如格式修复后 diff=0）。此时看 subagent 摘要判断是否合理，而非直接判假。但 diff=0 的"实现完成"值得怀疑，应复验。

### 主 Agent 跑 gate 时保护自己的上下文

主 Agent 必须亲自跑 gate（上面铁律），但 gate 失败时的完整诊断（traceback/堆栈全文）会涌入主 Agent 自己的上下文，长流程下累积污染。

区分两件事：主 Agent 跑 gate 只为**判断「过没过」**，不为**诊断「为什么失败」**。前者只需紧凑信息（exit code + 通过/失败汇总 + 失败项清单），后者（完整 traceback）是修复 subagent 的事，在它的独立上下文里获取。

因此：
- gate 命令从 P2 的 `gate_commands` 读取，这些命令已被 architect 设为**紧凑输出模式**（`--tb=no` / `--quiet` / `--reporter=dot` / `| tail -N` 等，见 architect 角色定义）
- 主 Agent 直接跑这些紧凑命令，判断信息（汇总行、失败清单）都在,完整 traceback 不进上下文
- 若 gate 失败且需要把完整诊断传给修复阶段：派 gate-runner subagent 在独立上下文跑**完整模式**命令、把完整输出落盘到文件，主 Agent 读紧凑结论判断，修复 subagent 读落盘文件——完整 traceback 始终不碰主 Agent 上下文

**不要**先跑完整命令再想办法截取——命令一执行，完整输出已进上下文，事后无法挽回。截断必须在命令层（紧凑模式参数或 shell 管道），让爆炸的输出从一开始就不产生。

### 空返回的恢复策略

subagent 空返回（约定产出文件不存在）是特殊失败模式，不能简单重试相同 prompt。

**分阶段落盘已默认启用**（见派发 prompt 模板），每次派发都带落盘指令。空返回仍可能发生（任务结构问题超出落盘缓解范围），此时：

1. 第 1 次空返回：
   a. 自动重试一次：相同 prompt 原样重发（本次自动重试不占用 `retries[Pn]` 槽位）。
      - 复用下方「派发耗时弱信号」：若本次会话时长 <1min → 输出「会话时长异常短」告警
        （提示可能为平台抖动 / 额度中断，而非任务结构问题），并照常自动重试一次。
      - 自动重试仍空返回 → 进入步骤 b。
   b. 计入 `retries[Pn]`（现成规则），记录 `failure_mode: empty_return, prompt_changed: false, adjustment: null`
   c. 分析失败原因：prompt 是否过复杂？输入文件是否过多？任务粒度是否过大？
   d. 调整策略后重派：拆分任务（见「派发编排机制」）/ 补输入导航（见「输入导航原则」）/ 换 subagent 类型（frontend ↔ general）
   e. 更新本次 retry 记录：`prompt_changed: true, adjustment: <具体调整>`

2. 第 2 次空返回（调整策略后仍失败）：
   - 计入 `retries[Pn]`
   - `len(retries[Pn]) > MAX_RETRY` → PAUSED 报告人工

**禁止**：不调整策略、相同 prompt 直接重试（`retries` 记录里 `prompt_changed=false` 且非首次）。
空返回说明 subagent 扛不住当前任务形态，原样重试大概率还是空返回。
「自动重试一次」是「相同 prompt 直接重试」禁令的唯一豁免——仅限首次、单次、原样重发；自动重试失败后进入步骤 b-e 流程，此后仍禁止不调整直接重试。

**空返回诊断的间接缓解**（当前平台不支持 subagent 活动检测，无法直接判断"subagent 是否在干活"，见 LIMITATIONS.md 局限 4）：
1. 主 Agent 记录派发耗时作为参考（弱信号，不作主要判据——耗时不能区分"卡死"和"在干活但慢"）
2. 空返回后检查中间产物文件（P{N}-progress.md 是否有内容 → 判断 subagent 是否动过；有 progress 内容说明落盘生效但最终产出未完成，问题在产出阶段；无 progress 内容说明 subagent 早期就放弃了）
3. 从任务本身分析（输入是否过多、产出文件数是否超过 3——见「派发编排机制」）

**空返回的最可能根因**（验证实测）：不是上下文窗口被输入占满，而是**任务结构导致认知过载**——subagent 读完所有输入后面对"从零开始写一篇大报告"的推理复杂度过高，模型在单次推理中放弃。`steps` 上限无法缓解（已验证 steps:15/30 均无效）。有效的是**分阶段落盘**（见派发 prompt 模板的落盘指令）——把"一次性大产出"拆成"逐步小产出"，每步认知闭合，降低单次推理复杂度。因此分阶段落盘已作为默认指令写入每次派发 prompt，不再作为空返回后的补救措施。

—— T016 教训：P3 subagent 连续 3 次空返回，主 Agent 既没记 retry 也没调整策略，直接降级亲自写。如果有 `prompt_changed` 字段，事后一眼就能看出"3 次重试 prompt_changed 全是 false"——违规一目了然。
—— T020 教训：空返回后不需要精确诊断"为什么"也能正确应对——走 retry→PAUSED，不降级。诊断是优化，不降级是底线。

---

## subagent 外部中断恢复（额度/超时/崩溃）

subagent 可能因**外部原因**（API 额度上限、平台超时、进程崩溃）中途终止——与"正常返回后校验失败"不同，此时 subagent 可能已落盘部分产出。**不能一律当作失败重派**，应先评估已落盘内容再决定复用/补做/重来。

```
subagent 收到 failed/中断信号后，主 Agent 按序检查：
  1. 检查 {AGATE_WORKSPACE}/tasks/{Txxx}/ 下已落盘产出（Edit 工具即时写入，不因中断丢失）
  2. 评估产出完整度：
     - 文件存在 + Header 完整 + 内容非空非半截 + 能过该阶段 gate → 直接复用
     - 文件存在但内容明显半截（写一半断）→ 补充少量工作后复用，不重派
     - 无产出或产出无实质内容 → 视为失败，计入 retries[Pn] 重派
  3. 复用已落盘内容时，仍须亲自跑 gate 验证（不能因"是上次中断的产出"就采信）
  4. 复用 vs 重派的边界：已落盘内容 ≥80% 完整 → 补充复用；<80% → 重派
  5. 中断不计入 retries[Pn] 的"subagent 失败"语义（那是 subagent 做不好的惩罚）；
     但若中断 2 次以上且均无实质产出，按环境/平台问题记录，不盲目重试
```

> 与"返回校验"的关系：返回校验针对 subagent **正常返回**（含其 step 4 "半截内容 → 视为失败，重试"）；本节针对**外部中断**（额度/超时/崩溃，subagent 无法正常返回）。**本节优先于返回校验 step 4**——外部中断且已落盘内容 ≥80% 完整时，补充复用而非重试；若中断前已正常返回则仍走返回校验。两者都要求主 Agent 亲自跑 gate 验证，不采信 subagent 自述。

---

## 执行模式：支持 subagent 派发 vs 单 Agent

agate 的标准模式假设主 Agent 所在平台支持派发 subagent。若运行环境不支持派发（`executor_env.has_task_tool: false`，如 Claude Project 会话），整个派发机制降级为**单 Agent 顺序执行模式**：
> 实现注记：`task` 工具 / `has_task_tool` 是平台派发能力的具体实现命名——Claude Project 等
> 无 task 工具的环境即走单 Agent 模式；本节属平台适配说明，平台无关的执行模式语义 = "能派发
> subagent 的标准模式" vs "不能派发时的单 Agent 降级模式"，与具体平台工具名无关。

| 标准模式（has_task_tool: true）| 单 Agent 模式（has_task_tool: false）|
|-------------------------------|--------------------------------------|
| 主 Agent 派发 subagent，自己不写产出 | 主 Agent 直接执行每个阶段，自己写产出 |
| 每阶段独立上下文，角色专注 | 所有阶段同一上下文，无上下文隔离 |
| TDD：P3/P4 由不同 subagent 执行 | TDD：P3/P4 同一 Agent 执行，独立视角消失 |
| gate：主 Agent 亲自跑命令 | gate：同上，但本地环境也可能缺失 |

**单 Agent 模式的附加要求：**
- P1 裁剪说明里声明 `single_agent_mode: true`
- P3 写测试时必须在 P4 实现之前完成，模拟 TDD 的「契约先行」
- P6 不能以「代码审查」替代实际运行 BDD——若无法跑，走 HANDOVER 交接
- 强烈建议：P0-P2 在单 Agent 完成后，将结果 push 到 main，再切换到支持 subagent 派发的平台执行 P3-P8

---

## 降级规则（硬边界）

降级（主 Agent 亲自执行阶段产出）只在以下情况发生：
- `has_task_tool: false`（环境不支持 subagent）
- `has_local_runtime: false` 且阶段需要本地运行（gate 无法执行）

**subagent 执行失败 ≠ 降级信号。** subagent 失败时：
1. 计入 `retries[Pn]`（现成规则）
2. 调整策略重派（拆分任务 / 补导航 / 换 subagent 类型）
3. retry 超限 → PAUSED（state-machine 现成规则）

**主 Agent 不得以"subagent 做不好"为由跳过 retry/PAUSED 直接降级。**

—— T016 教训：P3 subagent 3 次空返回后，主 Agent 自行决定降级亲自写代码。协议没有明确说"subagent 失败时不能降级"，主 Agent 把"协议没说不行"当成了"可以"。本节把降级的合法条件写死，降级不再是一个可选项。

---

## 标准派发流程（每个阶段）

```
主 Agent 执行：

0. 任务启动（仅首次，任务刚收到时）

   主 Agent 首先必须写 P0-brief.md，然后再派发任何 subagent。
   这是主 Agent 作为 PM 的判断输出，P1 analyst 以此为输入做需求质疑和 BDD。

   P0-brief.md 结构（主 Agent 亲自填写）：
   ```yaml
   task: {一句话描述这个任务是什么}
      # 若一句话无法概括，考虑拆分为多个任务——见「派发编排机制」
   known_risks:
     - {已知风险1，如：涉及 schema 变更}
     - {已知风险2，如：跨越 N 个改动端}
   executor_env:
     platform: {opencode | claude-code | codex | claude-project}
     has_task_tool: true       # false = 单 Agent 模式
     has_local_runtime: true   # false = gate 命令无法执行，需交接有本地环境的平台
     network: {full | restricted}
   env_constraints:
     debug_env: {项目的测试/调试环境路径/命令，从项目约定读取}
     # 不写 prod_env：生产环境不在 agate 开发流程范围内
   phase_hint: [P1, P2, ..., P8]  # 主 Agent 预判，P1 analyst 可调整，但须经主 Agent 确认
   ```

   P0-brief 完成后，主 Agent 自查四个必填字段是否有实质内容：
   - task：是否是工程视角的一句话描述。若写不出一句话 → 任务太大，拆分
   - known_risks：至少列出一条，没有风险也要写「无已知风险」而不是留空
   - executor_env：platform/has_task_tool/has_local_runtime/network 四项都要填实际值，不是占位符
   - env_constraints.debug_env：是否从项目约定（CLAUDE.md）读取了具体路径/命令
   任一字段为空占位符状态 → 补完再继续。

> 实现注记：上文 `task` 指 P0-brief 的 frontmatter 机器字段名（YAML 键，含该字段值的自查标准），
> 非平台派发工具指代——协议语义不绑定平台工具名，主 Agent 派发 subagent 的工具命名各平台不同
> （见 dispatch-protocol.md「派发的三条铁律」注记）。

   P0-brief 完成后，第一步输出只允许两种内容之一：
   a) 派发 P1 analyst（传入 P0-brief.md 路径作为主要输入）
   b) 判断为微/小任务并声明「直接执行」的理由

   任何其他输出（分析方案、直接改代码）视为违规。

   —— T005/T006 教训：主 Agent 把「提炼问题定义」也委托给了 subagent，
      P1 analyst 拿到的是用户原始需求文档，缺少主 Agent 对环境约束、风险、裁剪倾向的判断注入。
      P0-brief 是主 Agent 作为 PM 的思考文件，不可省略。

   ### P0 / P1 职责边界

   P0 是"决策记忆"（PM 视角），P1 是"需求基线"（analyst 视角）。
   P1 读 P0 作为输入，遵循三层处理：
   - **引用**：P0 已有的决策内容（user_decisions / 协调依赖等），P1 直接引用，不重写
   - **形式化**：P0 的验收基线，P1 转化为 BDD Given/When/Then 格式（仅改格式，不改内容）
   - **补全**：P0 没覆盖的隐含需求、待确认清单、能力需求，由 P1 独立产出

1. 读状态
   读 {AGATE_WORKSPACE}/tasks/active-tasks.md → 确认当前任务和阶段
   读 {AGATE_WORKSPACE}/tasks/{Txxx}/ → 确认上一阶段产出文件存在

2. 选角色
   按阶段从 assets/execution-roles/ 选执行角色
   （P1→analyst, P2→architect, P3→test-designer, P4→implementer, P5→verifier, P7→consistency-reviewer, P8→implementer(P8模式)）

3. 派发 subagent（派发工具）
    传入：
      - 角色定义文件路径（assets/execution-roles/xxx.md）
      - dispatch-context 文件路径（{AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-dispatch-context-{role}.md）
      - 输入文件路径（上一阶段产出，不传内容）
      - 输出要求（产出哪个文件 + Header 规范 + 门槛）
      - 返回要求（只返回路径 + 摘要）

4. 接收返回
   只读 subagent 的摘要，不读产出文件全文

5. 门槛检查
   读产出文件的 Header / 关键字段，判断门槛是否通过
   （可判定条件，见下）

6. 更新状态
   更新 active-tasks.md 的阶段和状态
   门槛通过 → 进入下一阶段（回到步骤 1）
    门槛失败 → 重试（retries 记录 +1，超限则停下报告）
```

> 步骤 6 的「跑 gate → 判定 → 写 `.state.yaml` phase → git add」这一段查表机械动作由 `agate next` /
> `agate advance` 完成（不做临场判断，消费 `phases.yaml` 的 `next`/`retreat`/`gate_pass_exit`）；
> 权威定义在 `state-machine.md`「主 Agent 的单步执行」。手工执行为 fallback。

---

## 输入导航原则

铁律 2"只传路径不传内容"防止的是上下文污染，不是禁止主 Agent 给方向。主 Agent 派发 subagent 前，给 subagent 提供"读哪个节、关注什么"的导航。

**导航 ≠ 提炼 ≠ 读全文：**
- 导航：prompt 里注明"读 P1-requirements.md 的 BDD 验收条件节"
- 提炼（禁止）：主 Agent 读完文件把内容总结进 prompt
- 读全文（禁止）：把文件内容复制进 prompt

**导航的信息来源是协议知识，不是文件内容：**
- 每个阶段产出文件的节结构由对应角色定义文件硬约束（analyst.md 定义 P1 的节、architect.md 定义 P2 的字段）。角色定义文件不在主 Agent 的 mapping 必读路径里——主 Agent 不需要读它们，导航用的节名称在下方已内联
- P1 的节名称（来自 analyst.md）：需求复述 / 隐含需求识别 / BDD 验收条件 / 待确认清单 / 裁剪说明 / 范围声明 / 能力需求声明
- P2 的字段（来自 architect.md）：packages / domains / ui_affected / gate_commands / env_constraints / files_to_read / minimal_validation（后两个控制 P4 implementer 上下文 + 方案可行性验证）
- 主 Agent 用这些协议定义的节名称给导航，不需要读产出文件的实际内容
- 节名称是协议固定的，章节号是 subagent 自己编的——导航用节名称，不用章节号

**主 Agent 的核心职责是任务分解 + 输入导航 + 验证**，不是传话筒（把文件路径原样转发），也不是消化器（读完所有文件做提炼）。

—— T016 教训：P3 派发时主 Agent 把 7 个文件路径（~1917 行）甩给 subagent，没给任何导航。subagent 要自己理解 BDD + 接口 + 串行队列 + mock + vitest，认知负荷过载导致 3 次空返回。

**残余风险**：如果 subagent 产出时偏离了角色定义的节结构（用了自定义标题），导航会静默失效——subagent 找不到对应节，大概率又是空返回循环。缓解方式：P1/P2 gate 检查时，主 Agent 顺带验证产出文件是否含角色定义要求的节名称，缺失则门槛不通过。

### dispatch-context 规范

主 Agent 在派发前必须为每个 subagent 写好 dispatch-context——这是 subagent 的核心信息源，包含目标、约束、上游关联和输入文件。dispatch-prompt 只提供跨阶段通用执行纪律，任务特定信息全部在 dispatch-context 中。

**为什么这是铁律 2 的补全**：铁律 2"只传路径不传内容"当前只覆盖了阶段产出文件（P1-requirements.md 等），没覆盖主 Agent 自己查证的客观信息。这个缺口从 T016 就存在，T020 第一次被显式提出——主 Agent 把环境状态、URL、选择器全写进 prompt（约 50 行），违反铁律 2 精神且不可复用。

**文件名**：`{AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-dispatch-context-{role}.md`（每个 subagent 一个，只含该角色的导航信息）

**所有 P1-P8 阶段统一强制 dispatch-context 存在**——commit 前暂存区必须含至少一个当前阶段的 dispatch-context 文件。

**内容结构**（Markdown + XML 标记）：

```markdown
---
phase: {P1-P8}
generated_by: agate-inject-card.py + 主 Agent
task_id: {Txxx}
role: {角色名，如 analyst / requirements-review / implementer}
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标
{一句话：本角色在本阶段要产出什么}

### 约束
{从 P0-brief env_constraints/known_risks + 上游产出 + 协议知识提取。写的是"必须满足什么/不能做什么"，不是"应该怎么做"——后者是 subagent 的自主决策空间}

### 上游关联
{上一阶段 subagent 摘要中的关键信息}

### 输入文件
- {AGATE_WORKSPACE}/tasks/{Txxx}/P0-brief.md（主 Agent 的任务简报和风险声明）
- {AGATE_WORKSPACE}/tasks/{Txxx}/{上一阶段产出文件}
- {project_conventions_file}（项目约定）
{按角色定义补充其他需要读的文件}
</dispatch_guide>

<!-- AGATE_CARD_START -->
{由 agate-inject-card.py 注入，禁止手写}
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：{服务运行状态、版本号}
- 关键标识：{URL、API 端点、文件 ID、DOM 选择器}
- 查证结果：{grep/命令输出摘要}
</objective_info>

> 注：该文件禁止包含 PASS/FAIL 预判——否则被 `check-p6-provenance.py` 审计失败。
```

**AGATE_CARD 注入**：主 Agent 用 `agate-inject-card.py P{N} TASK_DIR` 注入卡片内容到 dispatch-context 的 `<!-- AGATE_CARD_START -->` / `<!-- AGATE_CARD_END -->` 块，**禁止手写 AGATE_CARD 内容**。

**主 Agent 写 dispatch-context 的信息来源**：

| 来源 | 何时写入 | 写什么 |
|------|---------|--------|
| P0-brief | 首次派发 P1 时 | 约束节（env_constraints/known_risks） |
| subagent 返回摘要 | 每次收到 subagent 返回时 | 上游关联节 |
| gate 诊断 | gate 失败时 | 约束节 + gate-diagnosis.md 引用 |
| 主 Agent 查证 | 派发前查证客观信息时 | objective_info 节 |
| P2-design.md 结构化字段 | P4/P5/P6/P8 派发时 | 约束节（packages/domains/gate_commands/files_to_read grep 提取） |

**dispatch-context 生命周期**：
- 每个 subagent 一个文件：`P{N}-dispatch-context-{role}.md`
- 主 Agent 在派发前写，派发后**冻结**（provenance 审计需要初始版本不变）
- 重试/回退时的诊断信息**不追加到 dispatch-context 文件**，写入单独的 `P{N}-gate-diagnosis.md`（见 ⑫）
- 回退时：新写目标阶段的 dispatch-context 文件，引用 gate-diagnosis.md

派发时 prompt 只给这个文件路径，不写具体内容。这个文件由主 Agent 在派发前查证后写（主 Agent 的合法职责，类似 P0-brief）。

**关键约束**：
- dispatch-context **禁止包含 PASS/FAIL 预判**（已有约束，不变）
- dispatch-context **派发后冻结**——provenance 审计检查的是派发时的初始版本，追加内容会破坏审计基准
- 约束节写的是"必须满足什么/不能做什么"，不是"应该怎么做"——后者是 subagent 的自主决策空间
- 主 Agent 不读产出文件全文——约束的信息来源是 P0-brief + gate 诊断 + subagent 摘要 + P2 结构化字段 grep，不是主 Agent 读完 P1-requirements.md 后的提炼
- P2 结构化字段的 grep 提取是**读特定字段**，不是读全文——`grep -E '^(packages|domains|ui_affected|gate_commands|files_to_read):' P2-design.md`

### Judge 信息隔离（P6.5，TAG0020）

P6.5 judge 派发以 **fresh context** 独立复核（防"评审者与作者同信任链"的锚定），dispatch-context 是信息隔离的唯一载体，由 `check-judge-verdict.py` 机械校验（任一违规 → exit 1，P6.5 门槛不通过）。

**文件名**：`P6.5-dispatch-context-judge.md`（沿用 `P{N}-dispatch-context-{role}.md` 命名；2p dispatch-context glob 按 phase 匹配不覆盖 `P6.5-*`，卡片 hash 校验不强制——内容合规由 check-judge-verdict 白名单扫描承担）。

**白名单输入**（『输入文件』『上游关联』两节只允许）：`P1-requirements.md` / `P2-design.md`（仅验收相关节）/ `P6-evidence/` 目录 / `.state.yaml` / `gate-events.jsonl` / judge 自身产出 `P6.5-judge-verdict.md`；另授 git log 查询权（非路径）。

**黑名单禁注入**（两节禁含，大小写不敏感；与 check-judge-verdict.py 实现同源）：
- `P6-acceptance.md`（verifier 自述，防锚定）
- `P6-dispatch-context-*.md` / `P5-dispatch-context-*.md` / `P4-dispatch-context-*.md`（实现者/验收者派发上下文）
- `P4-implementation.md` / `P4-review.md` / `P5-test-results/`（实现/评审/技术验证产出）

**AGATE_CARD 排除**：dispatch-context 仍含 AGATE_CARD 注入块，白名单扫描排除该块 + frontmatter（复用 check-p6-provenance 审计 2 的双排除 L318-355），卡片内说明文本不误报。

**上游关联注入面防泄漏**：`agate-extract-context.py` 在上游关联节的结构化提取注入在 **P6.5 禁用**，或净化为仅注入白名单路径（不含 verifier 产出结论叙述）；主 Agent 派发时同样不得把黑名单路径 / 验收结论传入。全文行首 `- PASS|FAIL` 验收结论预判（继承审计 2 语义）→ 违规。

**P6.5 派发流程**：
1. P6 commit 完成（phase=P6，P6-acceptance.md + P6-evidence/ 落库）后，主 Agent 写 `P6.5-dispatch-context-judge.md`（白名单输入 + AGATE_CARD 注入 + 派发后冻结）
2. 派发 judge（方法 B：general subagent + 角色文件注入，见 role-system.md「自定义角色怎么用」）
3. judge 产出 `P6.5-judge-verdict.md`（Header status/criteria_total/criteria_passed/verdict_evidence[/partial] + 逐 BDD 结论）
4. 主 Agent 跑 `check-gate.py P6.5 $TASK_DIR`（= check-judge-verdict.py + check-events.py 双 exit 0；历史任务无 `judge.enabled: true` 早退跳过）
5. 通过后 verdict（+dispatch-context）随 commit 落库——.state.yaml phase **保持 P6**（P6.5 非独立 phase 值），pre-commit hook 在 verdict 存在后自动重验双脚本；全部通过 → 写 `phase: P7` 随 P7 commit
6. `status: needs-revision / rejected` → 弹回 P6 重验（judge 轮次 +1，账本 `judge_verdict` 事件计数 ≤2 机械兜底，超限交人工）

**预算与账本交叉（BDD-8）**：judge 复核轮次 ≤2 / token 100k（`judge_token_budget` 可覆盖）/ 时间 30min。预算耗尽时 judge 必须落盘 `status: needs-revision` + `partial: true`，并在账本 `judge_verdict` 事件记录 `reason: budget_exhausted`（append-only 账本预算留痕）；check-judge-verdict.py 对账本 budget_exhausted 事件与 verdict 状态做机械交叉（verdict 非 needs-revision+partial → exit 1，不静默放行）。

### gate 诊断落盘

gate 失败后，主 Agent 的诊断结果**写入单独的 `P{N}-gate-diagnosis.md`**，不追加到 dispatch-context 文件（后者派发后冻结，见 ⑪）。

**诊断信息结构**：

```markdown
---
phase: P6
date: 2026-07-11
trigger: gate_fail
---
# P6 Gate 诊断

- gate 结果：FAIL=3, NC=0
- 失败项：BDD-3 过期链接返回 404 非 410, BDD-7 批量操作无确认, BDD-12 并发竞态
- 诊断：P4 实现问题（BDD-3/BDD-7）+ P2 设计问题（BDD-12 未考虑并发）
- 路由：BDD-3/BDD-7 → 退回 P4；BDD-12 → 标 [SCOPE+] 增补 P1
- 修复方向（P4）：link-service.ts 的 TTL 检查逻辑 + batch 的确认流程
```

**诊断格式禁令（N2）**：

`gate-diagnosis.md` 和 `dispatch-context` 上游关联节引用 gate-diagnosis.md 路径**禁止使用 `^\s*- (PASS|FAIL)` 行首格式**列失败项。理由：`check-p6-provenance.py` 审计 2 grep `^\s*- (PASS|FAIL)\b` 于 dispatch-context 文件，命中即判为"验收结论预判" exit 1。诊断中的失败项是**事后诊断**不是预判，但审计 2 分不出两者。

**允许的格式**（不触审计 2）：
- `失败项：BDD-3, BDD-7`（内联，非列表行首）
- `- 失败BDD: BDD-3 过期链接返回 404`（前缀 `失败BDD` 不匹配 `(PASS|FAIL)\b`）
- `gate 结果：FAIL=3, NC=0`（等号后，非行首列表）

**禁止的格式**（触审计 2）：
- `- FAIL BDD-3: 过期链接返回 404`（行首 `- FAIL` 命中审计 2）
- `- PASS BDD-1: 已验证`（同理）

**dispatch-context 上游关联节**只放 `gate-diagnosis.md` 的**路径引用**，不 inline 诊断内容（方案 ⑪ 已有此约束，此处重申并绑定 N2 禁令）。

**落盘时机**：

| 场景 | 落盘位置 | 何时写 |
|------|---------|--------|
| 重试（本步抖动） | `P{N}-gate-diagnosis.md` | 诊断后立即写 |
| 退回上游 | `P{N}-gate-diagnosis.md` + 目标阶段新 dispatch-context-{role}.md 引用诊断 | 退回前写 |
| PAUSED | `PAUSED-resolution.md` 引用 `P{N}-gate-diagnosis.md` | PAUSED 时写 |

---

## 派发 prompt 模板

> 完整模板（含全部阶段特定追加节）唯一权威源：`assets/templates/dispatch-prompt.md`，本文件不维护完整版。

极简结构骨架（用于快速对照，非完整正文，实际派发以权威源为准）：

```
你是 {阶段 Pn} 阶段的 {角色名} 子 Agent。
读取并严格遵循：{agate_root}/assets/{execution-roles|review-roles}/{role}.md
读取并严格遵循 dispatch-context：{AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-dispatch-context-{role}.md
输出：{AGATE_WORKSPACE}/tasks/{Txxx}/{本阶段产出文件}
```

各阶段特定追加节（评审角色专属指令 / P2 最小验证 / P3 自检 / refactor 任务回归口径 / P4 上下文控制
/ P5-P6 BDD 规则与证据要求 / 证据日志格式约定 / 回退诊断 / READY 收尾检查 / 版本 bump 判定 /
项目占位符映射 / 返回前自检等）均已合并进 `assets/templates/dispatch-prompt.md`，本文件不重复维护。

**命令超时兜底（层级 4，所有 bash 命令强制）**：取值 = 该命令预期耗时 ×1.5，完整规则与分层关系见
`assets/templates/dispatch-prompt.md`「命令超时兜底」节。

---

## 全量重跑点审计

> 本节落地 BDD-11（TAG0016，RM-AG0026）：审计协议全流程中"全量重跑"发生的具体点位，标注哪些是必然发生（无法省略）、哪些是条件触发，以及哪些已被本任务新增的证据引用机制（BDD-12/BDD-14，见「引用 P5 证据、不重跑」相关设计）替代或简化。

| 重跑点 | 性质 | 触发条件 | 是否可被本任务机制替代引用 |
|--------|------|---------|--------------------------|
| P5 首跑 | 必然 | 每个任务到达 P5 阶段必然执行一次 `gate_commands.P5` | 不可替代——首次验证无前序证据可引用 |
| P5 失败后重跑 | 条件 | 仅当首跑失败、修复后重新验证时发生（T027 教训：必须全量重跑，不能只测修复项） | 不可替代——重跑本身就是"确认修复且无新回归"的必要动作 |
| P6 refactor 独立 regression.log | 条件 | 仅 `change_type: refactor` 任务，且当前口径要求独立跑一次全量回归 | **本任务后可替代**——BDD-12 无改动校验成立时，P6 可引用 P5-test-results/ 而非独立重跑 |
| P8 bump-version 后重跑 `gate_commands.P5` | 必然（发布前最后一道防线，不可移除，见 P1 BDD-14）| 每个走到 P8 的任务，bump-version 后需确认测试仍全绿 | **范围/方式可被简化**——主 Agent 跑 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`，读 stdout 的 `AUDIT7_RESULT:` 行：`reuse_allowed` → 复用同一份 `P5-test-results/`（不重新执行命令）；`reuse_blocked` / `no_reuse_claim_possible` → 仍需完整重跑 `gate_commands.P5` |

---

## 派发编排机制

> 本节是 subagent 派发编排的**权威来源**（TAG0014，RM-AG0016）：工作量评估、编排模式、并行规则全阶段适用。既有有效规则（输入/产出数量上限、拆分判据、T016/T026 教训、P7 例外、状态机不变）保留在本节下方，不分散到各阶段卡片。各阶段卡片的「按包拆分并行」节引用本节（仅保留阶段特定约束）。

### 0. 派发路由（查表 → 派首选 → 逐级回落 → 再派发）

> 配置驱动的跨 CLI / model 派发（TAG0034 / RM-AG0060）。**机会式启用**：不配置 =
> 行为与现状逐字节一致（全 `(phase, role)` 解析为 `standard` 档 = 继承主 Agent 当前
> model 的原生派发）。配置文件 = 项目级 `agate-workspace/dispatch-routing.yaml`（`routes:`
> + `tier_bindings:`，非协议本体、不受 SELF-GATE，全兜底）+ 协议本体档位词表
> `agate/rules/dispatch-tiers.yaml`（`bulk` / `standard` / `deep` 语义画像 + 出厂默认）。

**此步在铁律 1 启动 subagent 之前插入。** 主 Agent 到阶段 `Pn` 派角色 `R` 时，
在渲染好 dispatch-context 之后、调用平台派发工具启动 subagent 之前，先跑一步机械路由：

```text
1. 查表：resolve(Pn, R) —— 按优先级序（项目级直接值 candidates: > 项目级档位映射
   tier: > 机器级绑定 tier_bindings: 展开 > 出厂默认 → standard）解析出「默认派发」
   或「有序跨 CLI 候选链 [{cli, model, effort?}, ...]」。(phase,role) 命中优先于 phase 级。
2. standard / 无配置 → 直接默认派发（同平台、同 model），不写 dispatch_route 事件。
3. 候选链 → try-and-fall（无 probe，第一个动作即把真实 dispatch-context 派给首选候选）：
   逐候选派发 → 若「起不来 / 基础设施失败 / 无可解析产出」三类之一 → 记理由码、试下一个；
   → 收到任何 gate 能评的产出（产出文件非空、presence 级骨架可解析）→ 停止回落、交 gate。
4. 候选链耗尽 → 回落默认派发（final = {"cli": "default"}）。
5. 写 1 条 dispatch_route 事件（带 candidates_tried 理由码 + final），复用哈希链账本。
```

**gate 判定只认产出文件 + exit code，不认谁生产的。** 这条解耦是设计成立的前提——
`check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` 对跨 CLI 派发的产出
零特殊处理，谁跑出来的都一样评。未来不得为跨 CLI 派发定制 gate。

**两条完整性不变量（机械强制，防「换模型试到出 green」的完整性洞）：**

1. **候选回落 ≠ 状态机 retry**：候选回落只在 `launch_fail` / `infra_error` /
   `no_parseable_output` 三类基础设施信号时发生——**不占 `retries[Pn]`、不写
   `state_transition`、不触发 PAUSED**，只写 1 条 `dispatch_route` 事件。
2. **gate FAIL 绝不换候选**：一旦某候选产出了 gate 能评的东西，这条路由即成功——
   哪怕 gate 判 FAIL，那是**正常阶段 retry（在同一候选上重跑）**，`dispatch_route`
   事件计数不增。`dispatch_route` 理由码枚举里**没有 `gate_fail` 值**，
   `check-events.py` 第 8 条机械拒绝任何 `gate_fail` / 非三值理由码。

**弱缓解 vs 强缓解 + 自动化不对称**：`cli: native`（同厂商换 model，不脱离原生派发
工具）是**弱缓解**——同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性；
且原理上做不到「不依赖主 Agent」，自动化天花板是**主 Agent 读文件机械横传 model**。
`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解**——真正的
异源独立视角，可端到端自动化。两形式 gate 判定 / 留痕一致。

**tmux 观测层（可选，仅子进程形式）**：子进程形式派发前若 `which tmux` 成功，可把命令
包一层 `tmux new-session -d -s <命名空间> '<命令> | tee <capture>; <收尾>'`——人 `tmux
attach` 肉眼看实时输出，路由脚本读 `<capture>` 文件取结构化流；`which tmux` 失败则裸跑。
经 `tee` 旁路的 `<capture>` 内容与裸跑 stdout 逐字节一致 → **两路径的 `dispatch_route`
留痕 + gate 结果完全一致**，走不走 tmux 不影响协议判断的任何环节。session 名带命名空间
（`agate-<任务>-<阶段>-<短时间戳>`，防与机器上既有 session 碰撞）；wrapper 末尾自带退出
倒计时（默认 15s、可配），倒计时完自退 → session 自然结束。路由脚本清理：`list-clients`
空 → 直接 `kill-session` 跳倒计时；非空（有人 attach）→ 不强杀、让倒计时收尾；倒计时脚本
本身挂死、超过「倒计时 + 余量」（余量 10s）仍在 → 兜底 `kill-session`（先 `has-session`
判断、容忍对已消失 session 的非零退出）。**明确不做**：`send-keys` 交互、`capture-pane`
内容解析回传主 Agent、跨轮次 session 复用。**目标环境代表性**：落地验证环境为 WSL2 +
tmux 3.4（非容器 / CI runner / 纯物理机 Linux）——目标部署环境须在其自己的 tmux 版本上
复跑跨平台机制调查的落地前复核项；未复跑通过则该观测层停在「定稿 + 待落地验证」、**不阻塞
发布**（可整体切除，不影响配置路由核心与跨 CLI 子进程两层）。本机接入默认关（环境开关
启用），亦为「待落地验证」姿态的一部分。

**单 Agent 模式（`executor_env.has_task_tool: false`，如 Claude Project 会话）**：无派发
动作 → **路由为 no-op**，本节不适用（显式出范围）。

**retry / 回退时的路由**：
- **同阶段 gate-FAIL retry**：不重跑路由、用上次成功的同一候选重跑，`dispatch_route` 计数不增。
- **P5→P4 等跨阶段回退后的 P4 retry**：主 Agent **机械重解析一次 `(phase, role)` 路由**
  （按当时候选可用性落候选，可能与回退前不同），**不注入**「上次失败 → 升档 / 换更强
  model」逻辑——retry 是状态机行为、路由是机械查表，两者不耦合。

**评审打回后的续跑（子进程 / native 两种形式都适用）**：设计 → 评审打回 → 改 → 重交评审
这个循环**优先走平台官方续接、不重起**：

- **同 target（cli + model / native 的目标 subagent 未变）→ 续接**：把评审意见作为新 prompt
  传入平台续接原语；子代理保留「当初为什么这么设计」的上下文，比重起省一大截。
- **续接失败 / 换 target → 全新派发**（重新跑一次 `agate dispatch route`）。
- 续接产出**仍走假完成校验（D2）**，且本就在人的评审循环里。
- **续接失败无客观信号是已知缺口**——按「续接优先、重起兜底」处理，**不假装解决**。
  **不需要实现续接的自动化**（人在评审循环里）；决策层留 hook 位给未来，不落自动续接逻辑。

> 实现注记：续接原语随平台而异，属平台适配实现细节、非协议语义——子进程 `claude -p --resume <id>` /
> `codex exec resume <id>` / `opencode run -s <id>`；native 侧 Codex `followup_task`、OpenCode 命名
> subagent 的续接工具调用、Claude Code 续接原语待核实。设计依据见 `docs/design-notes/design-dispatch-routing.md` §2.4a。

**author 文档内容 vs 跨文件一致性验证的阶段边界**：`dispatch_plan` 批次表里，
「补 / 改协议文档正文」（新增章节、修订既有措辞、补 per-platform 说明）是 **P4 author
工作**，标 P4、随批提交；**P7 只验证跨文件一致性**（多个文档 / 脚本 / schema 间的
措辞与引用是否对齐、有无矛盾），P7 **不** author、不改写文档正文。architect 设计批次表
时不得把「补文档正文」批标成 P7。

### 1. 工作量评估（五维评级）

派发前先评估任务工作量，决定编排模式。每个维度按 low / medium / high 评级，综合定级取各维度评级的**最高档**（任一维度 high → 整体 high）：

| 维度 | low | medium | high |
|------|-----|--------|------|
| **产出规模** | ≤3 个文件，单文件 ≤500 行 | 4-6 个文件，或单文件 500-1500 行 | >6 个文件，或单文件 >1500 行 |
| **输入规模** | ≤3 个输入文件 | 4-5 个输入文件 | >5 个输入文件（先精简输入，确实都必要才拆） |
| **改动性质** | 单文件小改 / 新增独立模块 | 多文件改动，结构局部化 | 跨模块改动、接口变更、迁移重构 |
| **耦合度** | 与既有代码零耦合 | 与 1-2 个模块耦合 | 与 ≥3 个模块耦合 / 共享文件牵动多包 |
| **认知负荷** | 纯机械执行（复制模式 / 单一模式） | 需理解局部上下文 | 需读全貌才能动手（结构不明 / 历史包袱重） |

**综合定级规则**：任一维 high → 整体 high（必须拆分，见模式 2/3/4/5）；全部 ≤medium 且无 high → medium（按需拆批）；全部 low → low（模式 1 单发即可）。**high 复杂度必须拆分**——单 subagent 过载是本机制要解决的核心问题（TAG0010 批次 0 实证：agate_common 整库 + ci-gate-backstop + 3 bats 一次派发导致用户中止）。

### 2. 五模式编排

| 模式 | 名称 | 何时用 | 流程 |
|------|------|--------|------|
| 模式 1 | **单发** | 工作量 low / medium，单个 subagent 可靠交付 | 派 1 个 subagent → 产出 → gate |
| 模式 2 | **静态拆批** | 产出可预先划分成互不依赖的批次（如按包/按模块） | 按 P2 声明的 packages 或产出清单静态拆 N 批 → 并行或串行派发 → 合并 |
| 模式 3 | **并行** | 批次间无数据依赖、无共享文件改动 | 同时派发 N 个 subagent（上限见「并行规则」）→ 各自产出 → 主 Agent 汇总统一 commit |
| 模式 4 | **先理解后拆** | 工作量 high / 结构不明 / 无法预先确定拆分方案 | ① 侦察 subagent 读全貌产出拆分方案 → ② 按方案派执行 subagent（并行或串行）→ ③ 合并（见下方模式 4 流程） |
| 模式 5 | **串行链** | 批次间有强依赖（后者依赖前者的产出） | 逐批派发，每批 gate 通过后派下一批；状态机不变，仍属同一阶段 |

### 3. 模式 4 流程（先理解后拆）

适用于工作量 high、任务结构不明、主 Agent 无法预先确定怎么拆的场景。三步：

1. **侦察（recon）**：派 1 个侦察 subagent，读全貌（输入文件 + 相关代码 + 历史上下文），产出**拆分方案**——拆成哪些子任务、每子任务的输入/产出/依赖、批次粒度与并行可行性。侦察产出中同时定义**合并语义**：
   - **BDD 全局编号**：各子任务承接的 BDD 编号必须全局唯一编号（`#### BDD-NN:`），不允许各包各自从 1 编号（否则 P6 验收/P7 一致性对照错位）
   - **包归属去重**：每个 BDD/产出明确归属唯一包，跨包的共享件（类型/接口/配置）单独列出，不允许两个子任务各写一份
2. **执行**：按侦察方案派执行 subagent（并行或串行，遵守「并行规则」）。各执行 subagent 只改自己子任务范围，共享文件统一后处理
3. **合并**：轻量拼装（拼接各自产出、无跨包交叉修改）由主 Agent 或单个 subagent 完成；重量整合（需要交叉核对、统一编号、处理跨包引用）派整合 subagent 完成

**文档样例**（consistency CHECK 2 校验的样例引用路径存在）：

```yaml
dispatch_plan:
  mode: recon-then-split
  parallel_limit: 3
```

侦察 subagent 产出拆分方案后，主 Agent 按方案派执行 subagent（如 `P3a/P3b/P3c` 拆批，commit message 记录拆分 `wf(Txxx-P3a): ...`）。

### 4. 并行规则

1. **并行上限默认 3**：同一阶段同时派发的执行 subagent 数默认 ≤3（平台并发 + 主 Agent 上下文承载上限）；`dispatch_plan.parallel_limit` 字段可覆盖（≥1 整数，gate 校验）
2. **失败批 retry 与 state-machine `retries[Pn]` 对齐**：并行批次中部分失败时，默认**整组计 1 次 retry**（不逐批累加）；重试策略（整批重跑 vs 仅失败批重试）由主 Agent 在 dispatch-context 声明，但 retry 计数一律按整组 1 次计入 `retries[Pn]`（state-machine.md 的表只引用不改）
3. **共享文件统一后处理**：并行 subagent 只改自己批次范围，跨批共享文件（类型/接口/配置）由主 Agent 在所有 subagent 返回后统一处理。**P6 例外**：P6 的证据并行走自身汇总 verifier 机制（见 P6 卡片「证据并行 + 汇总 verifier」），不适用本节共享文件规则
4. **资源密集型默认串行**：批次之间即使无数据依赖、无共享文件改动，只要命令属于**资源密集型**，默认改为串行（模式 5），不并行。资源密集型判据（命中任一即是）：
   - 全量测试套件跑 xdist / 多进程并发（如 `pytest -n auto`）——并行批次各自再起多进程会争抢 CPU 与文件锁
   - 浏览器自动化 E2E（CDP / Playwright）——各批次各起浏览器实例，显存/端口/用户数据目录易冲突
   - 构建/打包/安装依赖类长命令（编译、`npm install`）——磁盘 IO 与网络带宽是共享资源
   - 需要独占外部资源的命令（同一端口的 debug server、同一测试数据库文件）
   要并行跑资源密集型批次时，必须先按 P4 卡片「基础设施隔离（并行时强制）」为每批分配独立端口/数据库/临时目录，并在 dispatch-context 写明；无法隔离 → 串行（安全默认值）。本条在「全阶段适用表」的 P5 行落地（P5 虽是只读验证、无代码写冲突，但 `gate_commands.P5` 常是全量测试/E2E，属资源密集型 → 默认串行），P5 卡片「按包拆分并行」引用本条，不重复展开判据

### 5. 全阶段适用表

| 阶段 | 默认编排模式 | 说明 |
|------|-------------|------|
| P1 | 模式 1（单发）/ 模式 4（复杂需求） | 需求复杂（多来源/多模块）时先派侦察 subagent 再拆（见 P1 卡片） |
| P2 | 模式 1（单发）+ `dispatch_plan:` 产出 | **非 P2 自身拆分**——P2 评估并声明后续阶段的编排方案（模式 + 批次表 + parallel_limit） |
| P3 | 模式 2/3（按包拆批/并行） | 测试设计按包并行，各写各的测试文件（见 P3 卡片） |
| P4 | 模式 2/3（按包拆批/并行，额外约束） | 共享文件后处理 + 基础设施隔离 + 串行安全默认值（见 P4 卡片） |
| P5 | 模式 2/3（按包拆批/并行）；资源密集型命令 → 模式 5（串行） | 只读验证，无代码写冲突；但全量测试/E2E 命令按「并行规则」第 4 条"资源密集型默认串行"处理（见 P5 卡片） |
| P6 | 模式 2/3（证据并行，受限模式） | 证据并行 + 汇总 verifier 整合唯一 P6-acceptance.md（见 P6 卡片） |
| P7 | 模式 1（单发）+ 输入数量豁免特例 | **非串行链**——一致性检查天然需要跨文件对照，不受输入文件数限制 |
| P8 | 模式 2/3（多包拆批 + 合并机制） | 多包发布可拆批（各 releaser 写 P8-release-{pkg}.md → 合并 subagent 整合唯一 P8-release.md） |

### 任务粒度基准（既有有效规则）

当阶段产出涉及以下特征时，主 Agent 应拆分为多个 subagent 任务：
- 输入文件超过 5 个（主 Agent 应先检查是否都必要，精简输入比拆分任务成本低；确实都必要时再拆分）
- 单次产出超过 3 个文件（超出 subagent 可靠交付范围）

**拆分判据用输出数量，不用行数**——LLM 处理 2000 行同质内容没问题，但单次产出文件过多时遗漏率上升。行数是弱相关变量，产出文件数是强相关变量。

**异构性不再是拆分判据**——T026 实验证实：在 agate dispatch prompt 模板（含分阶段落盘指令）下，subagent 能可靠处理异构产出（文档 + 代码 + 测试在同一次派发中）。T016 失败的根因是当时缺乏分阶段落盘指令导致空返回，不是异构切换本身。

**拆分原则：**
- 每个任务产出 1-3 个文件
- 每个任务的输入文件 ≤ 3 个
- 任务间有依赖时串行，无依赖时并行
- 拆分通过多次派发调用实现，commit message 记录拆分（如 `wf(Txxx-P3a): 测试用例文档`）
- 状态机不变——仍只看 P3 阶段，gate 仍是该阶段的门槛命令

**按包拆分并行（与按产出拆分正交）**：
- 当 P2 声明 `packages: [pkg-a, pkg-b, ...]` 且包间无数据依赖时，同一阶段可派多个 subagent 并行（每个包一个）
- 包级并行的操作指引在本节「并行规则」+ 各阶段卡片的「按包拆分并行」节（保留阶段特定约束），phase card 是阶段特定约束的权威来源
- 包级并行不改变拆分原则的其他条目（产出文件数/输入文件数限制仍适用于每个并行 subagent）

—— T016 教训（历史）：P3 要求一个 subagent 产出 3 个异构文件时出现空返回。后经 T026 实验证实根因是缺乏分阶段落盘指令，非异构切换本身。当前模板已默认启用分阶段落盘，异构产出不再需要强制拆分。

**P7 例外**：一致性检查天然需要跨文件对照，不受输入文件数限制。consistency-reviewer 角色文件明确列出输入文件和关注点，dispatch-context-{role}.md 提供关键决策摘要减少提取量。

---

## do→review 迭代循环

每个含 subagent 评审的阶段都是迭代循环，不是单次通过/失败。review 不通过 → 修改 → 再 review，直到 approved 才推进到下一阶段。

**适用迭代循环的阶段**：

| 阶段 | do | review | 循环语义 |
|------|-----|--------|---------|
| P1 | analyst 写需求 | requirements-review（agent≠main） | review 否 → analyst 修改 → 再 review → … → approved |
| P2 | architect 写方案 | design-review（agent≠main） | review 否 → architect 修改 → 再 review → … → approved |
| P4 | implementer 写代码 | 按 C8 映射触发（非可选） | review 否 → implementer 修改 → 再 review → … → approved |
| P6 | verifier 写验收 | provenance 审计 | 格式问题 → verifier 调格式 → 再审计 → … → 通过 |
| P7 | consistency-reviewer | gate 脚本 | BLOCKER → reviewer 修改 → 再验 gate → … → 通过 |

**不适用迭代循环的阶段**：P0（主 Agent 亲自写，无 review）、P3（gate 是脚本判定红灯/绿灯）、P5（gate 是 test runner exit code）、P8（gate 是脚本检查）

**retry 预算**：review 迭代和 gate 重试共享同一阶段 retry 预算（`retries[Pn]`）。首次 review 不算 retry，从第二轮起算。

| 事件 | retry 计数 |
|------|-----------|
| 首次 do → 首次 review | 不算 retry |
| review 不通过 → 修改 → 再 review | retries[Pn] += 1 |
| gate 不通过 → 修改 → 再验 gate | retries[Pn] += 1 |
| review + gate 交替失败 | 共享累加 |

---

## P5 修复流程

P5 gate 不通过时（测试失败），主 Agent 派修复 subagent 回 P4 修复代码。修复后**必须重跑 P5 gate（全量测试）**，不是只检查修复项。

**T027 教训**：P5 修复 subagent 只修了 datetime 问题，但引入了 4 个回归（原有测试从绿变红）。如果主 Agent 只检查修复项不跑全量，回归会被放行到 P6。

### 修复流程

1. P5 gate 失败 → 主 Agent 记录失败项（哪些测试失败、失败原因）
2. 派修复 subagent（角色：implementer，输入含失败项清单 + 修复历史）
3. 修复 subagent 返回 → 主 Agent **重跑 P5 gate（全量测试）**
4. 全量通过 → P5 gate 通过，推进 P6
5. 全量仍有失败 → 回到步骤 1（修复历史追加本轮失败项，避免重复踩坑）

### 修复策略记忆

每轮修复重派时，prompt 里必须附上**修复历史**：
- 之前修了什么、怎么修的
- 之前试过但失败的策略
- 当前仍失败的项

避免修复 subagent 重复踩同一个坑（T027 第 2 轮修复引入了第 1 轮已解决的 datetime 回归）。

---

## Playwright/长时操作 subagent 派发策略

派发工具本身通常无超时参数。subagent 内部脚本挂起会无限阻塞主 Agent。通过**拆分 + 预期耗时**规避，不依赖超时机制。

> 实现注记：上述"派发工具无超时参数"是平台派发机制的既有能力事实（不同平台派发工具均无平台层
> 超时参数，T019 实战验证），属平台能力适配说明；协议语义不依赖该平台事实——防卡死策略一律
> 走 subagent 内部脚本硬超时 + 主 Agent 拆分，见下。

### 拆分原则

P6 Playwright 验证不派一个大 subagent 跑完整流程，按职责拆成小步骤：

| 子任务 | 预期耗时 | 返回值 |
|--------|---------|--------|
| 加载页面 + 检查 readyState | 30-60s | `{ loaded: true, loadTime: 35 }` |
| 检查 CSP 违规 | 5-10s | `{ violations: 0 }` |
| 检查 WebGL context | 5-10s | `{ webgl: true, renderer: "D3D11" }` |
| 检查 React/框架渲染 | 10-20s | `{ rootChildren: 3 }` |
| 截图 + vision 分析 | 10-20s | `{ screenshot: "/path.png" }` |

每个子任务：
- 职责单一，耗时可预测
- 返回结构化结果（不是文件全文）
- 有独立 Node 脚本硬超时兜底（见下）

### subagent 超时判定

主 Agent 不主动计时，但 subagent 的 Node 脚本内部必须设硬超时：

```typescript
const HARD = 90_000;  // 或 180_000 for >1MB HTML
let lastStep = 'init';
setTimeout(() => {
  console.error(`HARD TIMEOUT at: ${lastStep}`);
  process.exit(2);
}, HARD);
```

- exit 0 = 成功，exit 2 = 硬超时，exit 1 = 其他错误
- 主 Agent 看到 exit 2 + `lastStep` 信息，知道卡在哪步，可以加长 timeout 重跑该子任务
- 主 Agent 看到 exit 1，看 error message 决定修复策略

### 误杀处理

硬超时触发后，主 Agent 判断：
1. `lastStep` 是 `goto` → 页面加载慢，加大 `page.goto` timeout 重跑
2. `lastStep` 是 `waitForSelector` → 元素没出现，检查页面逻辑（非超时问题）
3. `lastStep` 是 `evaluate` → JS 执行慢或死循环，检查 evaluate 内容

**续跑**：已完成的子任务结果可复用，不从头重跑。如"加载页面"已完成，"检查 CSP"超时，只需重跑 CSP 检查。

### 大文件处理

涉及 >1MB HTML 的 Playwright 操作：
- 主 Agent **不直接 Read** 大文件内容，用 `wc -c` 查大小
- subagent 脚本 `page.goto` timeout 设 60-90s
- 脚本 HARD timeout 设 180s
- 加载后先 `page.evaluate(() => document.readyState)` 确认加载完成，再 `waitForSelector`

—— T019 教训：3.3MB Three.js HTML 的 P6 验证，subagent 内 `waitForSelector('#root > *')` 无 timeout 等待永不出现的元素（因 WebGL 被禁用导致 Three.js 初始化失败），subagent 挂起 → 派发工具无限等待 → 主 Agent 卡死数小时。根因是缺分层超时 + subagent 粒度过大。

### 写脚本与跑脚本分离

反馈循环长的脚本验证任务（浏览器自动化、测试脚本、构建脚本等），不要让一个 subagent 既写又跑又调试——几轮试错后上下文窗口满了导致空返回。

**拆法**：
- 阶段 A：subagent 写脚本（产出脚本文件，不跑）
  - 输入：dispatch-context-{role}.md（若存在）+ BDD/验收条件 + 参照文件
  - 产出：脚本文件
  - 用专项 subagent（前端/backend/mcp 对应类型）
- 阶段 B：主 Agent 跑脚本（gate 验证，A1 原则）
  - 跑 subagent A 写的脚本，看 exit code + stdout
  - 最小修复属于"跑命令"的一部分
  - 重大逻辑错误回 subagent A 修
- 阶段 C：subagent 读脚本输出写报告（可选，需格式化时）
  - 输入：脚本输出的结构化结果 + 验收条件原文
  - 只做格式化，不做验证

**最小修复 vs 重写的界限**：
- 改常量值（timeout、selector、URL、超时阈值）= 最小修复，主 Agent 可做
- 改控制流（if/else 结构、循环逻辑、数据处理）= 重写，回 subagent

主 Agent 跑 subagent 写的脚本 = "跑命令"不是"写产出"。
主 Agent 重写脚本逻辑 = 降级，违规。

—— T020 教训：主 Agent 空返回后以"跑脚本是 gate 验证"为由降级亲自写脚本。写脚本不是 gate 验证，是有创造性的工程工作。自查≠gate：subagent 可以自跑自查确认基本功能，但自查结论不等于 gate 结论。gate 由主 Agent 亲自执行，结果以主 Agent 为准。这防止 subagent 的"假完成"被当作 gate 通过。

### 主 Agent 的"inspect DOM"属于查证职责

主 Agent 可以跑最小 inspect 脚本（如 `page.evaluate(() => document.querySelector('#root').innerHTML.length)`）来查证 DOM 结构——这是查证客观信息（写 dispatch-context-{role}.md 的选择器清单），不属于"写脚本"或"降级"。查证产出落盘到 dispatch-context-{role}.md，派发时传路径。

区分：
- 主 Agent 跑 inspect 脚本（只查 DOM 结构、不做断言）= 查证职责 ✅
- 主 Agent 写验收脚本（含断言逻辑）= 降级 ❌

### P2 最小验证（方案可行性先验证再全流程推进）

**规则**：P2 方案设计时，如果方案依赖某个**浏览器行为/安全模型/外部系统行为**（非纯代码逻辑），必须在 P2 阶段做最小验证，验证通过后再写 P2 design。

**什么需要最小验证**：
- 浏览器安全模型（CSP 继承规则、sandbox 行为、iframe origin 语义）
- 外部库的核心能力（Three.js 能否初始化、BS4 能否解析目标 HTML）
- 跨系统交互（WSL→Windows 路径、CDP 连接、网络转发）

**怎么做最小验证**：
- 一个 10 行的 HTML 测试页
- 一个 curl 请求验证 API 行为
- 一个 20 行的脚本验证库的核心 API

**纯代码逻辑的声明**：
- 纯代码逻辑（函数输入输出、数据转换）→ 须在 minimal_validation 字段声明"纯代码逻辑"（写明依赖了哪些内部函数/数据转换），TDD 单元测试覆盖
- 项目内已有模式（API 路由、Vue 组件）→ 须声明"已有先例"并列出参照路径

—— T019 教训：srcdoc 方案在 P2 设计、P3 写 57 个测试、P4 完整实现后，到 P6 实跑才发现 srcdoc iframe 继承父 CSP，方案根本不可行。如果 P2 阶段用一个 10 行 HTML 测试页验证 srcdoc 的 CSP 行为，5 分钟就能发现方案不可行，避免 P2-P4 全部返工。

---

## 可判定门槛规范

> 本表为逐条可执行 grep/命令颗粒度；角色/评审映射颗粒度见 `WORKFLOW.md`《P1-P8 阶段总览》。

门槛必须是**主 Agent 亲自跑命令可验证的明确值**，不能是模糊判断或仅依赖 subagent 产出文件字段。

| 阶段 | 门槛 | 怎么判定（主 Agent 亲自执行）|
|------|------|--------------------------|
| P1→P2 | 需求基线建立 | P1-requirements.md 存在 + 有 Header + 含 ≥1 条 BDD 条件（BDD 编号格式为 `#### BDD-NN:`）+ `grep -cE '^\s*-?\s*\[NEED_CONFIRM\]' P1-requirements.md → =0`（仅计算阻塞项，倾向项 `[SUGGEST:]` 不计）+ `grep -cE 'status:.*GAP\b' P1-requirements.md → =0`（仅匹配 status: GAP，不匹配 supplementable）+ `grep -qE 'risk_level:\s*(low|medium|high)' P1-requirements.md → 命中` + P1-review.md status:approved + agent≠main + 含 `BDD-[0-9]` 锚点（check-gate.py P1 检查）|
| P2→P3 | 方案已批准 | `grep 'status: approved' P2-review.md` → 命中 + `grep -cE '^(packages\|domains\|ui_affected\|gate_commands):' P2-design.md → ≥4` + `grep -qE '权衡\|选择理由\|取舍\|考量\|trade-?off' P2-design.md` → 命中（或含"选择"+理由/原因/因为组合）+ 候选方案 ≥2（`scripts/check-gate.py P2` 脚本化部分）|
| P3→P4 | TDD 真红灯 | `scripts/check-tdd-red.py` exit 0（UI 任务额外确认 Playwright 用例存在）|
| P4→P5 | 实现完成 | 暂存区含非 md/yaml 文件（`git diff --cached --name-only | grep -qvE '\.(md|yaml)$|^\.state'`）|
| P5→P6 | 技术验证通过 | 从 P2-design.md `gate_commands.P5` 读取命令执行 → exit 0 AND failed==0 + N5 最小校验（grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' P5-test-results/unit.md → 计数 >0）+ 行首锚点扫描（主 Agent 参照 pre-commit 三步逻辑手动判断：正向→PAUSED / 不合规→修正 / 缺失→静默通过）+ 若 ui_affected：从 gate_commands.P5 读取 E2E 命令执行 → exit 0 |
| P6→P7 | BDD 验收通过 ⚠️ self-authored（降级缓解：provenance 审计 + R1a 截图实质检查，根治待 Phase 3） | `scripts/check-gate.py P6` → exit 2（FAIL=0/NC=0/证据非空已验）+ `scripts/check-p6-evidence.py` UI 截图 > 1KB（R1a 客观证据 barrier）+ `scripts/check-p6-provenance.py` → exit 0（证据-结论对应 + dispatch-context 审计 + BDD 总数对照由审计 3 自动执行，P1 `#### BDD-NN` 标题数与 P6 `grep -cE '^\s*- (PASS|FAIL)'` 结果数不符时 exit 1 硬阻 + UI vision YAML 审计 [R1b hook 化]）（UI 条件须截图 + vision-analyst YAML 引用 + `summary.blocker_count → =0`）。**截图质量标准**：操作类 BDD 截图必须互不相同（md5 去重，hook 强制），查询类 BDD 可不截图但须有断言记录文件（response.json / assert.log 等，hook 强制）。任何 BDD 标 FAIL → gate 不通过 → 回 P4 |
| P7→P8 | 一致性通过（consistency-reviewer subagent 产出） | `grep -E '^\s*-?\s*\[BLOCKER\]' P7-consistency.md | grep -cvE '\[BLOCKER\][:：]?\s*\d+\s*条?\s*$'` → =0 + 同理 `[DEVIATION-CRITICAL]` → =0（声明行如 `[BLOCKER]: 0 条` 被排除，不计为实际 BLOCKER）（已知限制：定性分析，P5 回归测试兜底）|
| P8→READY | 发布准备完成（bump-version + commit + tag 由主 Agent 在 gate 验证后亲自执行） | `scripts/check-gate.py P8` → 脚本化部分通过（exit 2）+ 从 P2-design.md `gate_commands` 逐包读取发布检查命令执行 → 全部 exit 0 + bump-version 后重跑 P5 gate（`gate_commands.P5` exit 0 AND failed==0）+ `git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 条目 → 无遗漏 + 从 P2 `packages` 验证 version 文件路径变更 + `grep -q 'bump_type:' P8-release.md` → 命中 + version 文件双路径检查（暂存区或最近 5 commit，WARNING 级）+ CHANGELOG 双路径检查（`git diff --cached` + `git diff HEAD~5..HEAD`，WARNING 级，`CHANGELOG_FILE` 环境变量可覆盖默认 CHANGELOG.md）|

**反例（禁止用作门槛）：**
- ❌ "unit.md 里 failed: 0"（信 subagent 写的数字）
- ❌ "P8-release.md 存在"（文件存在不等于已发布）
- ❌ "P6 里 subagent 写了 ✅"（信 subagent 自我报告，见下方 C7 规则）
- ❌ "UI 代码看起来对"（UI 必须实跑 Playwright，不接受目测）
- ❌ "方案足够好" / "测试差不多了"

**A1 原则**：gate 判定是主 Agent 运行命令得到的客观事实，不是 subagent 文件里的声明。

**Pre-commit 检查全景（hook + CI 兜底）**：完整清单（触发条件、拦截行为、多任务扫描、三类 WARNING、pre-push 阈值提示、CI backstop）见 `WORKFLOW.md`「Pre-commit 检查总览」——权威唯一来源，本文件不重复维护。

**Gate 分类**：

| 类型 | 阶段 | 判定对象 | 造假风险 |
|------|------|----------|----------|
| 外部产出 gate | P3, P4, P5 | 外部工具输出（test runner exit code, type checker, git log） | 低（主 Agent 无法伪造外部产出） |
| 自写文件 gate ⚠️ | P1, P2, P6, P7 | 主 Agent 写的文件内容 | 高（主 Agent 直接写文件，作者和裁判同一人） |

自写文件 gate 的缓解措施：
- P1/P2：gate 条件简单（标记存在性、字段计数），造假动机低
- P6：证据存在性检查（`P6-evidence/` 非空）+ provenance 客观行为审计 + BDD 总数对照。造假成本提升：需造 N 个证据文件 + 正确交叉引用 + BDD 总数匹配，成本远高于派 verifier subagent
- P7：P5 回归测试兜底（一致性标注错误不会导致 bug 漏过）
- C7 规则见下方：所有阶段遵守「subagent 自我报告不可信」

**C7 规则（subagent 自我报告不可信）**：subagent 产出里的"检查结果""✅/通过"等自评，**仅供参考，绝不作为 gate 判定依据**。gate 一律以主 Agent 亲自跑命令的结果为准。T005 教训：P8 subagent 把 `1 failed` 标成 ✅，主 Agent 若信了就放行了缺陷。

**P6 证据由 CI 执行生成原则**（长期目标，当前 L0 指导）：
- 理想：P6 证据由 CI 从真实代码跑出，agent 只能引用 CI 产出物，不能自带
- 短期（本方案）：若项目有 CI 流水线，优先要求 verifier 引用 CI 产出（如 pytest 结果路径）而非自带证据文件。⚠️ 安全收益为零（provenance 1a 只验引用存在性不验来源）
- 中期：CI 独立重新生成证据，agent 产出若与 CI 不一致则暴露伪造
- 长期：P6 证据产出完全由 CI 驱动，agent 只写引用
- 测试类证据（pytest 结果）：CI 天然可行
- UI 类证据（截图 + vision YAML）：依赖项目有 e2e 流水线，无流水线时退化为"尽量锚 + 明标残余风险"

**verification_env 条件化**：verification_env（运行环境描述：debug server URL、测试数据库、临时端口等）仅在以下条件之一满足时需要写入 P5/P6 dispatch-context：
- `ui_affected: true`（需要浏览器环境）
- `gate_commands.P5` 含 Playwright/e2e 命令
- P0-brief 声明 `known_risks` 含环境依赖

非 UI、无 e2e、无环境依赖的任务无需声明 verification_env。避免为纯后端单元测试填写无意义的环境声明。

**verification_env 失败处理协议**（本节是权威定义，P5/P6 卡片与 verifier.md 引用本节，不重复展开）：声明了 verification_env 的任务，环境验证失败时按以下四条规则处理，不靠临场判断。

1. **先分类：可重试 / 不可重试**

   | 类别 | 判据 | 处理 |
   |------|------|------|
   | **可重试**（环境本身可通过标准操作恢复） | 端口占用 / 临时资源未就绪；依赖包缺失但可用标准安装命令补齐；网络连接瞬时抖动 / 服务未完全启动；配置路径或环境变量误设（本任务范围内可修正） | 在下方「止损轮次」预算内重试 |
   | **不可重试**（当前环境内本质无解） | 权限 / 凭据缺失且当前环境无法自行获取；平台原生能力不支持（如声明只在 Linux 可行的能力，在 Windows CI matrix 侧本质不可行）；需要外部人工提供的账号 / 证书 / 生产访问；**机制误用型问题**（如应声明 verification_env 却标了 supplementable——这是协议使用错误，应立即改正声明方式，不是"环境故障重试"） | 立即升级人工，**不消耗**验证轮次预算 |

2. **批处理要求**：单轮验证若同时存在 ≥2 个待验证假设，必须一次性列出并在同一轮内**批处理**验证完；不允许"改一个假设 → 单独起一轮验证 → 再改下一个假设 → 再起一轮"（TAG0009 教训：逐个假设串行试错导致环境验证拖了 11.7 小时）。

3. **止损轮次 = 2 轮**，与阶段 retry（`retries[Pn]`）**独立计数**，不新增 `.state.yaml` 字段——由主 Agent 在验证 subagent 的 dispatch-context 中手工记录"当前第几轮验证 + 历次已排除假设清单"作为轮次追踪。超过 2 轮仍未解决 → 状态转 **PAUSED**，落盘 `PAUSED-resolution.md` 引用本轮诊断（沿用既有 PAUSED 流程，不新建流程）。独立计数的目的：避免环境重试用光阶段 retry 预算，让实现质量问题仍有 retry 可用。

4. **READY 后问题归属判定（三条判据）**：任务已标 READY 后才暴露的环境相关问题，按以下顺序判定归属：
   1. 问题源于本任务改动引入的环境依赖变化（如新增依赖但 P0-brief 未声明）→ 判定**本任务遗留**，回 P4/P5 修复
   2. 问题源于环境本身的外部变化（与本任务改动无关，如平台/工具链版本升级导致行为差异）→ 判定**环境本身问题**，登记 `known_risks`/roadmap，不重开本任务
   3. 证据不足无法判定 → 默认按第 1 条处理（保守原则，避免真实缺陷逃逸）

**环境准备职责边界**（本节是权威定义，P5 卡片「按包拆分并行」/ P6 卡片 / verifier.md 均引用本节，不重复展开）：

1. 环境的**启动 / 维护 / 关停默认归主 Agent**（或 P0-brief 显式声明的单一责任方）；subagent 默认只消费环境，不自行启动
2. 多个并行 subagent 需要访问同一环境时，由主 Agent 统一启动后通过 dispatch-context 注入访问方式（URL / 端口 / 数据路径），不允许各 subagent 各自启动——否则端口占用、数据库锁、资源竞争
3. 本节与 `.state.yaml` 的 `env_state` 字段（`debug_backend` / `test_entry_slug` / `env_verified_at`）是引用关系：字段语法与一致性验证步骤的权威定义在 state-machine.md「主 Agent 的单步执行（一轮）」的环境一致性验证步骤，本节**不重复定义**字段语法

**packages 动态注入（B4/B6）**：派发 P8 subagent 时，主 Agent 必须先读 P2-design.md 的 `packages:` 声明，把"需要 bump 哪些包"明确写进 prompt，并据此从 `gate_commands:` 字段生成各包的 gate 命令集。不能用固定的单包命令——不同项目的发布命令不同，必须从 P2 声明读取。

**P5/P6 gate 命令固化（B7）**：P5/P6 的 gate 命令必须从 P2-design.md 的 `gate_commands:` 字段读取，不得在派发 prompt 里自行修改或降级。
- subagent 要求跳过命令 / 换更简单的命令 → `[SCOPE_GAP]`，不通过
- 命令本身跑不通（能力缺口）→ `[CAPABILITY_GAP]` 交人决策，不得自行降级为目测
- T004 教训 B7：P6 子代理连续失败后，主 Agent 要求「不用 Playwright，纯命令行验证」—— 这是主 Agent 降级了 P2 已固化的验收标准，属于违规。

**SCOPE+ / SCOPE_GAP 扫描**：每次 subagent 返回后，主 Agent 扫描产出是否含 `[SCOPE+]`（新隐含需求 → 增补 P1 基线 + 定向回补）或 `[SCOPE_GAP]`（prompt 漏了 P2 已声明的改动 → 修正 prompt 重派）。行首声明格式（`^\s*-?\s*\[SCOPE+\]`）。

**SCOPE+ 处理追踪（P2.11）**：产出含 [SCOPE+] 时，主 Agent 必须在 P1-requirements.md 增补对应条目并标记 [SCOPE_RESOLVED: 来源文件]。未标记 [SCOPE_RESOLVED] 的 [SCOPE+] → gate 不通过（scripts/check-scope-resolved.py）。

格式：
[SCOPE_RESOLVED: from P4-implementation.md] 新需求已增补为 AC-N，影响范围已评估

**DESIGN_GAP 处理追踪（v0.6）**：implementer 在 P4 产出中标注 `[DESIGN_GAP: xxx]`（因 P2 设计歧义/缺口而自主做的决策），P7 architect 审查，主 Agent 在确认后追加 `[DESIGN_GAP_REVIEWED: 已确认 / 已打回 P2]` 配对标记。未配对 REVIEWED 标记的 DESIGN_GAP → gate 不通过（仿 SCOPE+/SCOPE_RESOLVED 模式）。行首声明格式（`^\s*-?\s*\[DESIGN_GAP\]`）。

格式：
[DESIGN_GAP_REVIEWED: 已确认] 主 Agent 审查通过——implementer 的自主决策正确，P2 设计此处确实缺失
[DESIGN_GAP_REVIEWED: 已打回 P2] 主 Agent 审查打回——implementer 的决策有问题，需 P2 补充设计后重新实现

### P5 gate 验证方式

P5 subagent 化后，主 Agent 验 gate 的方式：

| 验证项 | 方式 | 理由 |
|--------|------|------|
| P5-test-results/ 存在且非空 | check-gate 脚本检查 | 产出存在性 |
| failed 计数 | gate 脚本读 unit.md 的 failed 字段 | 外部产出 gate（test runner exit code），非自写文件 gate |
| PROD_TOUCHED | 行首锚点 + 二值声明检测（pre-commit 三步） | 客观检查 |
| 测试是否真的跑了 | N5 最小校验 + CI backstop 兜底 | commit 前无法 100% 验证 subagent 确实跑了测试 |

**C7 规则与 P5 的关系**：C7 说"subagent 自我报告不可信"。P5 的 failed 计数写在 unit.md 里——这是 subagent 写的文件，按 C7 不可信。但 P5 是外部产出 gate（test runner exit code 是客观事实），不是自写文件 gate。区分：
- **自写文件 gate**（P1/P2/P6/P7）：gate 检查的是 agent 自己写的文件内容 → 造假风险高 → 需要额外审计
- **外部产出 gate**（P3/P4/P5）：gate 检查的是外部工具输出 → 造假成本高 → CI backstop 兜底足够

---

## 重试与上限

**红灯处理优先级**：
1. 诊断：本步抖动还是上游输入问题？
2. 本步抖动 → 重试一次（仅一次，避免在被污染的输入上打转）
3. 上游问题 → 退回源头那一步（见 state-machine.md 逐步溯源）。退回前须先归档被跨过阶段的自撰产出（`agate-archive-stale-outputs.py`，仅 P1/P2/P6/P7 需要，check-state-transition.py 会强制检查）；若诊断已确定源头在 2 阶之外，用 `agate-retreat-to.py {TASK_DIR} {目标阶段} "{诊断原因}"` 自动化执行多步单向回退（每一步仍是独立、真实、受 gate 校验的 commit，不改变 diff≥2 强制 PAUSED 的安全网本身）
4. 退到 P0 仍无解 / 外部阻塞 → PAUSED 问人类（正确路由，非认输）

```
门槛失败时：
  retries[Pn].append({
    round: len(retries[Pn]) + 1,
    failure_mode: quality | empty_return | timeout,
    prompt_changed: <bool>,
    adjustment: split_task | add_navigation | switch_type | null
  })
   if len(retries[Pn]) < MAX_RETRY (见 state-machine.md 重试上限表):
       带着失败原因重新派发同阶段 subagent
       （prompt 里加上"上次失败原因：xxx，请修正"）

       # v0.6：临近重试上限时注入架构质疑提示（superpowers systematic-debugging 借鉴）
       # ⚠️ 条件用 >= MAX_RETRY(Pn) - 1（本次已是最后一次允许的重派），
       # 不能用 >= 3——详情见 state-machine.md 重试上限表（MAX_RETRY 因阶段而异）
       if len(retries[Pn]) >= MAX_RETRY(Pn) - 1:
          重派 prompt 追加：
          "⚠️ 你已是该阶段最后一次允许的重派。前 {N-1} 次尝试均失败。
           请优先质疑架构假设而非继续在同一层面试错。
           具体方法：回溯 P2-design.md 的方案假设，检查是否有隐含前提不成立。
           若确认架构假设有误，标 [SCOPE+] 触发回 P2 重新设计。"
  else:
      触发 L2 上溯（见 state-machine.md 评审迭代机制）
      上溯后重新开始该阶段
```

重试记录落盘到 `.state.yaml` 的 `retries` 字段（格式见 state-machine.md「每任务独立状态文件」），避免主 Agent 忘记重试了几次、也无法区分"原样重试"和"调整策略后重试"。

---

## 回退处理（诊断→跳转→PAUSED→批准→重跑）

gate 失败后，主 Agent 按以下步骤处理回退：

1. **诊断**：分析 gate 失败根因，确定问题源头在哪一阶段，落盘 `P{N}-gate-diagnosis.md`（含：失败现象、根因分析、目标阶段、诊断依据）
2. **跳转**：直接设置 .state.yaml phase 到目标阶段
3. **PAUSED**（diff≥2 时）：check-state-transition.py 拦截 → 主 Agent 在 PAUSED resolution 中写明诊断和目标 → 人工批准
4. **恢复到目标**：修完后从目标往下逐阶段重跑
5. **不在中间阶段停留**：诊断已确认问题在源头，中间阶段不需要重做

diff=1 回退（如 P5→P4）：直接退，诊断信息写入 P{N}-gate-diagnosis.md，新阶段 dispatch-context 的上游关联节引用诊断路径，无需 PAUSED。
diff≥2 回退：PAUSED + 诊断 + 人工批准（见 state-machine.md 回退机制表）。

---

## Subagent 安全

### 硬超时保护

1. **硬超时**：派发工具本身无平台层超时参数（T019 实战验证：subagent 内部脚本挂起导致主 Agent 卡死数小时）。防卡死依赖 subagent 内部脚本硬超时（见上方「subagent 超时判定」节）+ 主 Agent 拆分策略，不依赖平台超时
2. **进展标记**：派发 prompt 中要求 subagent 每隔若干关键操作输出进度标记
   `[progress] N/M files processed` 到 stdout，让平台日志可追溯
3. **存活检查（命令流日志承担判定职责，RM-AG0055）**：subagent 的**存活/卡死判定**由
   **命令流日志机制**承担（RM-AG0055，`agate/scripts/agate-cmdstream-*.py`）——从平台会话
   记录（Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd）外部获取活动信号
   （model 思考/输出/执行 tool 三类事件），机械检测两类卡死（调用冻结 = 未结束 call 超期；
   活动冻结 = 无未结束 call 且无任何活动超期）与逻辑空转（同命令+同结果签名重复）。
   检测输出定位"证据 + 触发核查、不自动判死"，主 Agent 据证据决定是否中止/重派。
   **两套信号分工**（与 RM-AG0023 progress 心跳扩展的职责边界，不产生职责重叠）：
   - **命令流日志 = 存活/卡死判定信号**（进程是否活着、是否卡在单次调用、是否空转）
   - **progress.md = 语义进展信号**（正在做什么、下一步计划）——保留原职责不变
   - 两者不互相替代：命令流日志是客观活动信号，progress.md 是 subagent 自述语义状态；
     主 Agent 判定存活以命令流日志为准，理解进展以 progress.md 为准

> 实现注记：命令流日志的三平台存储格式（Claude Code JSONL / OpenCode SQLite / DSH
> JSONL.zstd）为平台实现细节（RM-AG0055 验证记录 verification-cmdstream-datasource-
> 20260903.md），协议语义面不依赖具体存储格式；新增平台只需按适配器契约实现 +
> ADAPTERS 注册表加一行（见 agate-cmdstream-adapters.py，BDD-6）。

### 心跳文件生命周期

> RM-AG0055（TAG0028）心跳文件命名/审计豁免/清理时机规范。心跳文件是**可选的**
> 轻量存活补充信号（subagent 主动 touch），命令流日志已承担存活判定主职责时心跳可省略；
> 心跳文件的审计豁免与清理机制如下：

- **命名规范**：任务级心跳文件 = `${TASK_DIR}/.heartbeat`；父 subagent 为子任务维护
  `${TASK_DIR}/.heartbeat.child-{n}`（n 为父任务内子任务序号，同父任务内不重复不覆盖）。
  心跳文件统一以 `.` 开头（隐藏文件），避免被任务目录产物扫描误纳入
- **审计豁免**：`.heartbeat*` 落入 `{TASK_DIR}/` 协议命名空间，但 `check-p6-provenance.py`
  的 `_find_files` 隐藏文件过滤（`if name.startswith("."): continue`）**天然跳过隐藏文件**
  ——`.heartbeat*` 不进入审计枚举，已显式登记豁免确认（见 check-p6-provenance.py 路径
  过滤逻辑处注释）
- **清理时机**：任务结束（成功/失败/超限）由**产生心跳的一方清理**自己产生的心跳文件
  （`cleanup_heartbeats(task_dir)`，见 agate-cmdstream-detect.py）；异常遗留的心跳文件
  由下次同任务重新派发前的**派发前置检查清空**（比照 agate-archive-stale-outputs 任务
  目录收尾模式，不新建清理机制）

### subagent 自主再派发

> RM-AG0055（TAG0028）受控自主再派发：执行角色在授权范围内可自主派发子任务（子 subagent）。
> 权限边界见 `role-system.md`「子派发权限边界」节；本节定义与五模式编排的关系与产出收敛语义。

- **与五模式编排的关系**：subagent 自主再派发是 **subagent 内部的一层**，与主 Agent 层面
  的「五模式编排」（见「派发编排机制」节：单发/静态拆批/并行/先理解后拆/串行链）**并存互补，
  不合并不互相替代**——主 Agent 层面的模式 4（先理解后拆）仍权威，subagent 的再派发
  是在其被授予的子任务范围内做局部拆解，不改变主 Agent 的编排决策
- **§4.1 两条硬边界**（与 role-system.md「子派发权限边界」节一致）：
  1. 子任务**不写** `.state.yaml` / `active-tasks.md`，不产生独立 phase 状态——外部观感
     永远是"一个 subagent 在跑"，父汇总后仅以"路径+摘要"回报
  2. 子任务写权限是**父权限的严格子集**，父在派子任务 prompt 中显式重申约束（不自动继承）
- **产出收敛**：子任务中间产出**不计入 gate 判定对象**；仅父 subagent 最终声明的
  `files_modified` 走既有假完成校验（D2）；**不产生新的编排层级**（状态机单层不变，
  gate 判定路径不感知子派发）
- **judge 类角色例外**：judge 类角色（fresh context 信息隔离）不适用子派发，派发时
  在 dispatch-context 显式声明「不启用子派发能力」（见 role-system.md）

### 升级机制（[UPGRADE] 标记）

subagent 可在产出文件中标注 `[UPGRADE]` 并附建议：

```
> [UPGRADE] 建议拆分为 Txxx-a / Txxx-b，原因：需求范围过大，单任务不可行
```

主 Agent 看到 `[UPGRADE]` → 停止自动流程 → PAUSED 交人工决策。

### P1 需求评审（强制，不可裁）

P1 完成后**必须**派发 requirements-review subagent 评审（与 P2 design-review 对称）。

派发 `requirements-review`（{agate_root}/assets/review-roles/requirements-review.md）评审 P1 产出：
- BDD 条件是否可二值判定
- 隐含需求是否按维度覆盖
- 裁剪跳过的阶段理由是否充分
- 风险分级/裁剪声明（risk_level / ceremony / phases）是否与实际 diff 证据匹配（ceremony: full → phases 含 P7；thin 四要素 vs 文件规模）
- 有无掺入解决方案设计

P1 评审不可裁——所有任务都走独立 requirements-review，无例外。微任务的泄压在更高层（agate 适用边界："微任务可不走 agate 全流程"），而非裁剪 P1 评审。

产出：P1-review.md（agent≠main，含 BDD 编号引用 + 覆盖维度标注）


### 不可逆操作保护协议（通用）

**基本原则：开发全程在测试环境进行，生产环境不在 agate 范围内。**

任何阶段，只要涉及以下操作，必须触发 `[NEED_CONFIRM]` 硬中断，等人确认后才可执行：

- **批量数据删除**：即使在测试环境，批量 DELETE / DROP TABLE / 清空也需人工确认范围
- **数据 schema 迁移**：测试环境的迁移逻辑需人工确认后再执行
- **不可逆的外部调用**：发送邮件/通知、扣费、第三方 API 写操作（应在测试环境用 mock）

`[NEED_CONFIRM]` 采用三值声明（T005/T006 教训 + T080 演进）：
- `[NEED_CONFIRM] {描述}` = 真无方向待人定夺（阻塞，可多条）
- `[SUGGEST: 推荐 X，理由 Y]` = 有倾向但求确认（WARNING 不阻塞，主 Agent 可自行采纳，除非涉及破坏性变更/业务方向）
- `[NO_NEED_CONFIRM]` = 无待确认项（负向）

倾向项使用场景：analyst 知道推荐方案但想留个底（"如果用户没异议就采纳"），主 Agent 读 P1 时直接采纳推荐，无需问用户。倾向项不等同于"待人确认"，仅作为审计痕迹。

每条 `[NEED_CONFIRM]` 须包含：
```
[NEED_CONFIRM] 不可逆操作待确认

操作类型：{删除/迁移/写入/...}
影响范围：{列出将被影响的数据/文件/资源，尽量具体}
是否已备份：{是（备份路径）/ 否（原因）}
建议操作：{具体要执行的命令或步骤}

请确认执行，或说明调整方案。
```

**严禁在未收到人工确认的情况下执行上述操作。**
备份先于删除——若无法备份，必须在 [NEED_CONFIRM] 中说明原因，等人决策。

## 标记声明规范

状态标记采用声明制——必须写正向或负向之一：

| 标记 | 正向（触发了）| 倾向（求确认）| 负向（未触发）| 适用环节 |
|------|-------------|-------------|-------------|---------|
| PROD_TOUCHED | `[PROD_TOUCHED] {描述}` | — | `[PROD_NOT_TOUCHED]` | P5/P8（全阶段检测） |
| NEED_CONFIRM | `[NEED_CONFIRM] {描述}`（可多条）| `[SUGGEST: 推荐 X，理由 Y]` | `[NO_NEED_CONFIRM]` | P1（gate 检测）；P2（信息标记，无 gate）；任意阶段不可逆操作（硬中断，含 P5） |
| BLOCKER | `[BLOCKER] {描述}` | — | `[BLOCKER]: 0 条` | P7（一致性检查） |
| DESIGN_GAP | `[DESIGN_GAP: 描述]` | — | `[DESIGN_GAP_REVIEWED: 描述]` | P4（标记）→ P7（配对检查） |
| SCOPE+ | `[SCOPE+] {描述}` | — | `[SCOPE_RESOLVED]` | P2/P4（声明）→ P1（增补）→ P7（检查） |

注：
- SUGGEST 仅在 P1 有 gate 检测（WARNING 不阻塞）。P2 architect 可用 SUGGEST 作为信息标记（无 gate）
- NEED_CONFIRM 在 P6 不再使用（客观验收，PASS/FAIL 二值）
- BLOCKER 专属于 P7，P4 review 用 DEVIATION-CRITICAL / DEVIATION / EXTENSION（见 architect.md DEVIATION 分类）

**禁止**：在产出文件中引用标记文本做否定描述（如"无 [PROD_TOUCHED]"、"所有 [NEED_CONFIRM] 已解决"）。
要表达"未触发"，写负向格式（`[PROD_NOT_TOUCHED]` / `[NO_NEED_CONFIRM]`）。
写了协议未定义的格式 → gate 拦截 → 重派修正。

**注**：缺失声明处理不对称——PROD_TOUCHED 缺失静默通过（安全网性质，缺失≠风险）；NEED_CONFIRM 缺失触发 WARNING（语义判断可能被遗漏，需要提醒）。

### gate 无法执行时的处理路径

gate 命令因**环境限制**无法执行（如无 npm、无 Playwright、网络受限），不能：
- 跳过 gate 直接推进下一阶段
- 以「代码审查」替代实际运行
- 假装 gate 通过

**正确处理方式（三选一，按优先级）：**

1. **补充能力**：安装缺失依赖、切换有本地环境的 Agent 执行
2. **写 HANDOVER.md 交接**：在 `{AGATE_WORKSPACE}/tasks/{Txxx}/HANDOVER.md` 里写明：
   - 当前完成的阶段
   - 待执行的 gate 命令（逐条列出）
   - 接手 Agent 需要的环境（从 P0-brief `executor_env` 读取）
   - 交接后推进的步骤
   标记任务状态为 `[HANDOVER]`，等能执行 gate 的 Agent 接手
3. **标记 `[CAPABILITY_GAP: gate-env]`**：暂停任务，告知人工干预

**严禁**：在 `executor_env.has_local_runtime: false` 的环境里，对需要本地运行的 gate 声称已通过。

---

### [CAPABILITY_GAP] 处理协议

P1 产出的 `capability_requirements` 中，`status: GAP` 的条目触发此协议：

**主 Agent 处理步骤**：
1. 暂停进入 P2，输出 `[CAPABILITY_GAP]` 报告给人：
   ```
   [CAPABILITY_GAP] 任务 {Txxx} 在 P1 检测到能力缺口：
   - need: {能力名称}
   - why: {为什么需要}
   - 当前环境：无可用补充路径
   - 建议选项：
     A) 注入 {skill名称} / 连接 {@agent名称}
     B) 降级验收标准（说明降级后的影响）
     C) 换具备该能力的模型
   ```
2. 等人选择后继续

**三态判断（不要只看主力模型能力）**：
- `available`：Agent 自身 OR 已注入 skill OR 可调用外部 agent → 不触发，流程自走
- `supplementable`：当前没有但有已知补充路径 → 在后续 prompt 中指引获取，不触发
- `GAP`：主力模型 + 环境均无补充路径 → 触发 `[CAPABILITY_GAP]`

**supplementable 能力的传递规则（A3 修复）**：
P1 产出 `capability_requirements` 后，主 Agent 在派发后续阶段时必须：
1. 读 P1-requirements.md 的 `capability_requirements`，提取 `status: supplementable` 的条目
2. 在该阶段的派发 prompt 里注入能力获取指引，例如：
   ```
   ## 能力补充说明
   本任务 P6 验收需要 browser-vision 能力。
   可用方式：派发 vision-analyst（{agate_root}/assets/execution-roles/vision-analyst.md）
   ```
3. 若能力在 P3/P4 阶段就需要（如 Playwright viewport 配置），提前在对应阶段 prompt 里注入
如未注入，subagent 不知道补充方式，supplementable 等效退化为 GAP。

**A3 视觉语境扩展（TAG0006，BDD-11）**：当 P1-capability_requirements 中视觉条目
status=supplementable 且该任务 P2 `ui_affected: true` 时，P6 派发 prompt 必须注入**视觉能力
获取指引**（如「可调用 vision-analyst 角色 / 视觉分析 skill，先自查能否调用，再向主 Agent
报告」），且派发 prompt 必须含**能力自查**强制要求（subagent 先自查能否调用视觉能力，不能则
报告 `[CAPABILITY_GAP]` 走降级路径——文档条文/像素检测/人工复核记录，不静默假设）。
P5/P6 派发追加段同样带能力自查要求（BDD-12）。

**UI 任务证据规则（TAG0006，BDD-9/14/17，P6 证据段）**：`ui_affected: true` 任务的 P6 证据段
说明须含三态分档 + 证据形式按形态选择——`available`/`supplementable`（无声明默认 available）
→ vision YAML 引用 + blocker_count=0；`GAP` → 截图/帧序列 + 人工复核记录引用（不要求 vision
YAML）；渲染组件/时序特效形态可选用 帧序列（`frames/`）/ 渲染输出对比（`renders/` + diff.json）/
时序截图（`-tN`）证据，帧序列与 `-tN` 时序截图按"同 BDD 证据组（bdd-id 前缀）"同权豁免
avg-hash 雷同判定；跨 BDD 组雷同截图 → 降级待复核（须含 `雷同截图复核` 记录或 manual-review
引用才放行，md5 逐字节去重硬阻断不变）。

**注意**：`supplementable` 不是 `GAP`。
T004 教训 B8：P6 需要 vision，主力模型没有，但环境里有 playwright-cdp skill 可注入。
如果 P1 就识别出这是 `supplementable` 并提示「需要注入 playwright-cdp skill」，
就不会跑到 P6 才撞墙，也不会触发 B7（主动要求跳过 Playwright）。

**什么时候 supplementable 升级为 GAP**：
人无法或不愿提供补充路径 → 人主动标记为 GAP → 此时才降级验收标准。
主 Agent 不得自行决定降级。

---

## 平台适配

平台能力矩阵（各 Agent 平台已覆盖情况、Windows 安装指南）权威源见 `platform-notes.md`——权威唯一来源，本节不重复维护平台能力矩阵本身，只保留与派发调用方式相关的独家操作细节。

> 实现注记：本节记录平台自定义 agent 机制的坑位与规避说明（含 OpenCode issue #29616 实测：
> `opencode.jsonc` 的 `mode: "subagent"` 定义的自定义 agent 可能无法被派发工具调起来，
> subagent_type 枚举硬编码只有 explore/general），属平台适配实现注记，非协议语义定义；
> 平台无关的派发语义见铁律 1 与「标准派发流程」。

**自定义 agent 调用坑位**：以 jsonc/声明方式定义的自定义 agent 可能无法被派发工具调起来。**优先用 markdown 文件方式定义自定义角色**，并在实际环境先做最小验证：定义一个测试角色，让主 Agent 派发它，确认能调起来。如果自定义角色确实调不起来，退路：用内置的 general subagent，把角色定义文件路径写进派发 prompt 让它读取遵循（角色行为靠 prompt 注入而非平台机制）。

---

## 完整派发示例（TAG0001 P2 阶段）

```
主 Agent：

1. 读 active-tasks.md → TAG0001 在 P2 阶段
2. 确认 {AGATE_WORKSPACE}/tasks/TAG0001/P1-requirements.md 存在 ✓
3. 选角色：architect（P2 执行角色）
4. 调用派发工具：
   subagent_type: architect（或 general + 注入角色文件）
   prompt:
     你是 P2 阶段的 architect 子 Agent。
     角色定义：读取 {agate_root}/assets/execution-roles/architect.md
     项目约定（必读）：CLAUDE.md
     P0-brief（必读）：{AGATE_WORKSPACE}/tasks/TAG0001/P0-brief.md（环境约束和风险声明）
     输入：读取 {AGATE_WORKSPACE}/tasks/TAG0001/P1-requirements.md
     任务：为数据库迁移问题设计方案
     输出：{AGATE_WORKSPACE}/tasks/TAG0001/P2-design.md（含 Header）
     门槛：方案覆盖 P1 列出的所有问题
     返回：只返回文件路径 + 一句话摘要
5. subagent 返回："{AGATE_WORKSPACE}/tasks/TAG0001/P2-design.md，采用 schema_version 表 + 顺序迁移脚本"
6. 派发评审 subagent（plan-eng-review 角色）→ 产出 P2-review.md
7. 读 P2-review.md 的 Header status
   - approved → 更新 active-tasks.md，TAG0001 进入 P3
   - rejected → 重试 architect（retries[P2] 记录第 1 轮），通过文件路径回流评审意见（见下）
```

### 评审打回后的意见回流（重要）

rejected 重试时，architect 必须知道"上次为什么被打回"，否则会产出同样的东西再次被打回，空转到 retry 耗尽。

**评审意见通过文件路径回流（不是主 Agent 读全文塞 prompt）：**

```
rejected 时，主 Agent 的重试派发 prompt 里加一行：
  "上一轮方案被评审打回。评审意见见 {AGATE_WORKSPACE}/tasks/{Txxx}/P2-review.md，
   请先读取该文件了解被打回的具体原因，再修正方案。"
```

- architect 自己读 P2-review.md（评审意见在文件里，符合"只传路径"原则）
- 主 Agent 不碰评审全文，上下文不被污染
- architect 角色定义的"输入"在重试时额外包含上一轮的 review 文件

这样评审→执行的反馈闭环真正打通，重试不再是空转。

**评审 rejected 后必须写 retries（RM-AG0042）**：任何评审 rejected 触发的重试，主 Agent 必须同步在 `.state.yaml` 的 `retries[Pn]` 追加一条记录（不能只改派发内容而不落盘）——`check-state-transition.py` 会据此做机械对应性校验（见 `rules/state-transitions.md`「单步回退必须同步写 retries」）。

**重新派发评审角色时的命名强制（RM-AG0042 D6）**：重新派发某评审角色时必须写**新编号**的 `P{n}-dispatch-context-{role}-retryN.md`/`-revN.md` 文件，**不得覆盖旧文件**——这是 BDD-1 对应性校验依赖的事件源判定依据（`check-state-transition.py` 按文件名精确匹配 C8 已知评审角色 token 判定"该阶段是否发生过评审重试"）。**同时禁止**：非评审角色的 dispatch-context 文件命名不得使用与 C8 评审角色 token 相同、或包含其作为独立词段的名字（历史曾出现 `consistency-reviewer`/`implementer-review-fix` 两个非评审角色文件名恰好撞上评审 token 的真实案例，均已被判定为假阳性并从枚举中排除，新命名不应再制造这类碰撞）。

---

## 任务完成小结

**触发时机：P8 gate 通过、状态进入 READY 时。强制输出，不可跳过。**
（T001 教训：主 Agent 完成任务后未向 PM 汇报，PM 需自己翻 git log 才能知道发生了什么）

主 Agent 从各阶段 gate check 的命令输出拼出小结，不读文件全文：

```
[{task_id}] READY — {task_name} {version}

改动：{files_summary from git diff --stat}
验证：{test_results from gate checks}
说明：{one-line design summary}
```

示例：
```
[TAG0001] DONE — 数据库迁移机制修复 v0.1.53

改动：exceptions.py +18 / database.py +51 / cli.py +7 / main.py +2
验证：14/14 migration tests + 486 regression tests
说明：Server 独立迁移，CLI schema 兼容检查
```

---

## PAUSED 报告模板

```markdown
[PAUSED] {task_id} 需用户介入

任务背景：{task_name}
当前阶段：{phase}
失败原因：连续 {len(retries[phase])} 轮 {phase} 评审发现 {issue_summary}

已尝试的解决方案：
  {attempted_solutions}

需要用户决策：
  - [ ] {option_1}
  - [ ] {option_2}
  - [ ] {option_3}

请回复选项或直接说明。
```

---

*派发协议是 agate 解决上下文爆炸的核心，配合 state-machine.md 和 loop-orchestration.md 使用*