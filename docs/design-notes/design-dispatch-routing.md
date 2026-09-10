# 派发路由设计（agate 协议增强提案）

> **做什么**：新增**项目级** `agate-workspace/dispatch-routing.yaml`（`routes:` + `tier_bindings:`，非协议本体、不受 SELF-GATE、全兜底）+ 协议本体档位词表 `agate/rules/dispatch-tiers.yaml`（`bulk`/`standard`/`deep` 语义画像 + 出厂默认）——按 `(phase, role)` 声明候选 `{cli, model, effort?}` 路由（或引用命名**档位** `tier`；`tier` 与 `effort` 是两个**正交轴**）。到某阶段派某角色时**查表 → 直接派首选候选（第一个动作即派真实 dispatch-context，无 probe）→ 若『起不来 / 基础设施失败 / 无可解析产出』三类之一则逐级回落到下一候选 → 全落空则默认派发（同平台同 model，恒等于本机制未启用）**——**try-and-fall，不是 probe-then-commit**。`cli` 可为 `native`（同厂商换 model，不脱离原生派发工具——**弱缓解**）或另一个 CLI（`claude-code`/`codex`/`opencode`，起子进程——**强缓解**）。查表 / 回落 / 降级是纯机械步骤，落在 CLI 里做、不依赖主 Agent 临场判断（§2.6）。新增 `dispatch_route` 事件无差别留痕。子进程形式下若有 `tmux`，包一层供人类 `attach` 观测。
>
> **本任务定案（2026-09-09 重写，纳入 §2.1 / §2.2 / 头部）**：① **三层落点**——配置文件**不在** `agate/rules/`（① 协议本体档位词表 `agate/rules/dispatch-tiers.yaml`；②③ 项目级 `agate-workspace/dispatch-routing.yaml`）；② 核心循环去「按序探测 probe」改 **try-and-fall**；③ `tier` + `effort` 两**正交轴** + `(phase,role)` key（role 可选）；④ `cli: native` = **弱缓解**（同训练系谱盲区基本共享，且做不到「不依赖主 Agent」——自动化天花板是主 Agent 机械横传 model），跨 CLI 起子进程 = **强缓解**（真正异源独立视角、可端到端自动化）——**自动化不对称**；effort 轴现三平台均可用（Claude Code `--effort` 按能力探测，本机 2.1.266 [实测] 有 / 引入版本未核实）；⑤ 两条**完整性不变量**——「**候选回落 ≠ 状态机 retry**」（回落只在基础设施失败发生，不占 `retries[Pn]`、不写 `state_transition`、不触发 PAUSED，只写 `dispatch_route`）与「**gate FAIL 绝不换候选**」（收到任何 gate 能评产出即停止回落；gate FAIL → 同一候选正常阶段 retry；`dispatch_route` 理由码枚举无 `gate_fail` 值、`check-events.py` 机械拒绝）；⑥ **routing 是 per-machine 机会式、不追求跨机可复现**（只有抽象 `(phase,role)`→档位映射可 commit 共享）。
> **为什么**：见 §1。核心是给"角色隔离"补上模型维度——让任一阶段（尤其 P6.5 judge）能跑在与开发链不同的模型/厂商上，把 `LIMITATIONS.md` 局限 2 的"认知层隔离"往"真正的独立视角"推一步；顺带打开成本 / 模型多样性 / 专业度匹配的优化空间。
> **不做**：主 Agent 按任务内容动态选型（§2.2 边界）；第三方终端工具（Herdr/Claude Squad 等，理由见 §2.4）作为依赖；DSH（理由见 §2.5）。局限 3"主 Agent 自身缺乏外部约束"超出本设计范围，不是本设计任何一条排除决定的理由，见 `LIMITATIONS.md`。
> **评审打回续跑**（§2.4a）：打回后同 target 重做时，优先用平台官方续接（`--resume` / `codex exec resume` / `opencode -s` / native 的 `followup_task`·`task_id`）把评审意见续进原会话；续接失败或 fallback 到别的 target 则退化为全新派发。续接是"重放重建"不是"状态冻结"（research §7），故按"续接优先、重起兜底"处理。
> **机会式启用，零强制基础设施**：不配置候选 = 行为与现状逐字节一致；配了但该 CLI 未装 / 未认证 / 无 `tmux` = 探测失败自动回落。多带一个 CLI/model 或 tmux 就用，否则退回原机制，不新增任何必须先搭好的东西——所以与局限 6"零基础设施"无实质冲突（§6）。
> **平台**：Claude Code、OpenCode、Codex。
> **相关**：`agate/dispatch-protocol.md`（派发三铁律）、`agate/rules/phases.yaml`（`exec_role`）、`agate/LIMITATIONS.md`（局限 2/4/6）、`agate/platform-notes.md`（Codex 现为"待补充"）、`docs/design-notes/design-orchestration-semantics.md`（RM-AG0054 推进侧 CLI，§2.6 决策 CLI 化的方向来源，但具体命令为本设计新提议，非既有命令）、`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`（RM-AG0055 subagent 存活可观测性——命令流日志机制，卡死检测直接复用它，§7 事项 6）、`docs/design-notes/design-maintainability-gate.md`（RM-AG0046 §2"模式层/检测器层分离"——本设计的架构模式沿用它，§2.1）、**`docs/research/cross-platform-dispatch-mechanics.md`（各平台 CLI 调用 / model 指定 / 子代理派发 / 返回识别 / 卡死检测复用机制的客观调查——本设计的机制事实全部引自此，不在此重复）**。
> **沿革**：由两条讨论线合并——跨 CLI 派发路由（v1 FAIL→v2 PASS→v3/v4→v5 三产出物拆分）+ 角色-模型映射（v1 FAIL：`fallback` 权威源分裂 → v2 PASS）。两线共用同一份配置文件，分作两份文档正是那个 BLOCKER 的成因，故合并；`cli: native` 即候选表的一个特化。2026-09-08 二次精简：范围收敛为"配置路由 + tmux 观测"两机制，移除观测信号优先级原则（已在 RM-AG0055）；第三方终端工具（§2.4）与 DSH（§2.5）的排除理由保留但收紧；平台机制的实机核实明细抽到 `docs/research/cross-platform-dispatch-mechanics.md`，本文只留设计相关结论。评审打回续跑（§2.4a）一度被精简掉、2026-09-08 按"续接优先、重起兜底"重新纳入（续接的可靠性调研见 research §7）。2026-09-08 内部独立评审一轮：修 §2.4a 结构损坏（BLOCKER），补探测成本 / `cli: native` 探测方式 / 与五模式·自主再派发·单 Agent 模式的交互 / tmux×stdout 捕获 / epic 拆分等 WARNING 为 §7 待确认项。**外部独立评审两轮**（`docs/reviews/review-dispatch-routing-external-20260908.md` FAIL → `-round2-` PASS 附一项待办）：B1/B2"证据强度传递失真"（把 `[自述]` schema 和 bug② 的机制推断混同为"已实测"）+ W1 续接失败无客观信号 + W2 tmux 实测环境代表性。round1 后改了 B1/B2/W1（复审认可）+ W2（改得不到位）；round2 指出 W2 只动了 §3 header、没同步 §6、且没说清环境代表性——本轮补齐：§3 末详述 WSL2+tmux3.4 环境边界、§6 风险表同步、§7 事项 9 登记目标环境复跑。
> **机制现状一句话**（详见 research 报告）：`cli: native` 三平台情况——Claude Code ✅（Task 单次传 `model`；`--effort` flag 本机 2.1.266 [实测] 有 / 引入版本未核实，路由按能力探测映射）/ Codex ✅（`spawn_agent` 按次传 `model` + `reasoning_effort`）/ OpenCode ⚠（命名 subagent 间接路，bug② 经真机核实不影响本用途）。子进程形式三平台都通（各有 `-m/--model` + 权限绕过 flag）。Codex 退出码不可靠须解析 `--json`（turn 层为准）；各环境可用 model 名单要自查（Codex 随账号类型、OpenCode 部分配置失效）。effort 轴现三平台均可用（Codex `-c model_reasoning_effort=` / OpenCode `--variant` / Claude Code `--effort` 按能力探测）。

---

## 1. 为什么要做

Agateon 的质量模型是"主 Agent 派发 → 每阶段一个独立上下文的 subagent 分角色执行 → 每阶段跑客观 gate"。角色隔离（analyst / … / judge）的目的是制造**独立视角**，让系统不能自己骗自己；P6.5 judge 更是以 fresh context 重验全部 BDD，专门打断"作者 = 裁判"的信任链（T026 教训）。

**局限 2 指出这层独立是结构性不完整的**：全部七个执行角色实际跑在**同一个底层模型**上（继承主 Agent 会话模型），同一训练分布下共享系统性盲区。角色隔离能防"明显偷懒"，防不住"这一类模型都会漏的边界"。`docs/design-notes/main-agent-oversight.md` 的"LLM 裁判员"方案正是因为"裁判与被裁判同源"被否决。局限 2 现状写死"无解"（ADR-006）。

当前协议**没有任何机制**能让某个阶段换一个模型跑——模型就是主 Agent 会话恰好在用的那个，judge 也不例外。

本设计给协议一个**机械的、配置驱动的**办法，让角色隔离真正跨模型/厂商：

1. **局限 2 的结构性部分缓解**——不同厂商模型仍各有盲区，但不再是同一个盲区；judge 跑在异源模型上，独立性不再打折。这是结构性改善，不是根治。
2. **模型档位匹配阶段特征**——每个 phase 的 `exec_role` 有相对稳定的认知需求画像，用户用候选表把它编码成"该用什么档位的模型"：P2 architect / P6.5 judge / P7 consistency-reviewer 这类"复杂或要专业判断"的阶段配高级或专业模型；P4 implementer 这类"产出量大但不一定需要顶尖智力"的阶段配便宜模型。**这个映射是用户在配置时一次性想清楚的**，不是运行时按任务内容动态判断（那越界成 §2.2 排除的语义选型）；静态 per-phase 配置只能逼近"复杂度→档位"，做不到"这一次的 P4 特别难所以临时升档"——真要那种粒度需要语义判断，超出本设计。

**决策机械化、不依赖主 Agent**：查表 → 探测 → 选 target → 逐级回落，全程无自由裁量，是纯脚本可完成的步骤。这承接 RM-AG0054"推进决策从 orchestrator 临场判断改为查表推进"的方向——路由决策同样应落在 CLI（本设计新提议的 `agate dispatch` 家族，非 RM-AG0054 已定义的既有命令，见 §5）里，主 Agent（或档位 C /loop）只调用、不参与判断（§2.6）。

**可观测性（局限 4）不靠新造机制**：新路径的存活/卡死判定**直接复用 RM-AG0055 命令流日志**（子进程形式还多 `wait(pid)` / `kill -0` 这层更强信号，见 §2.6 / research §6.0.1–6.0.2），不引入固定超时。**tmux 观测（§3）只是可选的"人肉眼看"层**——让用户在不介入协议流程的前提下 `attach` 看实时输出，走不走 tmux 对 gate / 留痕 / 存活判定都零影响。它不是局限 4 的答案（协议明确该局限"根治需要平台支持"），也不承担存活判定职责。

**边界**：不解决局限 3（主 Agent 单点故障）。与局限 6"零基础设施"**无实质冲突**——本机制是机会式的（头部已述）：不配 = 现状，配了但 CLI 没装/没认证 = 自动回落，没有"必须先搭好才能用"的东西。用户想用异 CLI 得自己先把那个 CLI 装好认证好，这是他自己的选择、不是协议强加的门槛。

---

## 2. 机制一：配置路由

### 2.1 配置结构（三层落点，2026-09-09 定案）

**配置文件不在 `agate/rules/` 之下**（`agate/rules/` 就是协议本体，与"非协议本体"自相矛盾）。三层：

| 层 | 落点 | SELF-GATE | 内容 |
|---|---|---|---|
| ① 协议本体 | `agate/rules/dispatch-tiers.yaml` | **触发**（改"什么是 `deep`"本就该评审）| 档位（tier）词表 `bulk` / `standard` / `deep` + 每档语义画像 + 出厂 `(phase,role)`→tier 映射（全 `standard`，MVP 空 map ⇒ 隐式全 standard）|
| ②③ 项目级 | `agate-workspace/dispatch-routing.yaml` | **不触发**（非协议本体，同 `maintainability.yaml`）| `tier_bindings:`（机器 / 安装级——tier→有序跨 CLI 候选链 `[{cli, model, effort?}]`，本机现状为准，SETUP scaffold）+ `routes:`（`(phase,role)`→ `{tier, effort?}` 引用 **或** `{candidates: [...]}` 直接值）|

MVP 不拆机器级②独立文件（`maintainability.yaml` 单项目文件先例）；加载器按"层"合并，将来把 `tier_bindings:` 移到 `~/.config/agate/` 是纯机械重构。

```text
# agate-workspace/dispatch-routing.yaml （形态示意）
schema_version: 1
tier_bindings:
  deep:  [{cli: codex, model: gpt-5.6-terra, effort: high}, {cli: claude-code, model: opus}]
  bulk:  [{cli: native, model: claude-haiku-4-5}, {cli: opencode, model: deepseek/deepseek-v4-flash}]
routes:
  P2:  {architect: {tier: deep}}          # (phase,role) key，role 段可选
  P4:  {tier: bulk}                        # phase 级
  P6.5: {judge: {candidates: [{cli: codex, model: null}]}}   # 直接值，跳过档位间接层
```

- **两个正交轴**：`tier`（能力档 `bulk`/`standard`/`deep`）与 `effort`（`low`/`medium`/`high`，可选）是**正交轴**——"便宜 tier + 高 effort""顶配 tier + 低 effort"都合法。`effort` 映射各平台推理档：Codex `-c model_reasoning_effort=` / OpenCode `--variant` / Claude Code `--effort`（按 `claude --help` 能力探测，无该 flag 的旧版省略不报错）。
- **路由 key = `(phase, role)`**，role 段可选：`(phase,role)` → `phase` → `standard` 解析顺序。想让 reviewer 跑异模型就显式配 `P4.review:`。
- `cli` 取值：`native`（不脱离当前会话的原生派发工具）| `claude-code` | `codex` | `opencode`（起子进程）；`model` 允许 `null`（= 该 CLI 默认）。`tier:` 与 `candidates:` 互斥。
- **`standard` 是不变量锚**：`standard` 档**不经 `tier_bindings` 展开**，硬编码 = "继承主 Agent 当前 model + 原生派发"。出厂默认全 `standard` ⇒ "不配置 = 逐字节现状"。
- **终点回落固定、不可配置**：候选全部失败 → 自动回落**默认派发**（同平台、同 model），恒等于"本机制未启用时的行为"。schema 无 `fallback` 字段（静态校验器 `check-dispatch-routing.py` 拦 `fallback:` / 非法 `cli` / 非法 `effort` / `tier`+`candidates` 同现）。
- **routing 是 per-machine 机会式、不追求跨机可复现**：只有抽象 `(phase,role)`→档位映射可 commit 共享；档位→具体 model 的绑定就是"本机实际能跑什么"，别的机器复现不了不是缺陷。
- **架构上沿用既有的"模式层 / 检测器层分离"**（RM-AG0046 §2，已落地）：协议定义语义与机制（模式层，平台无关），具体实现归各方（检测器层）——正如 `gate_commands` 只声明"必须有检查 X"、不规定用哪个工具，`platform-notes.md` 把语义映射到各平台，RM-AG0055 的"统一 IR + 每平台适配器"。本设计里：协议定义"查表→探测→降级→留痕"这套机制 + `dispatch_route` 事件语义（模式层），"配哪些 CLI/model、探测怎么实现"归用户（检测器层）。探测是 G0 式纯机械判定（判通不通），拒绝 G3 式主观品味（"哪个 model 更适合这次任务"）进入机制——§2.2 末尾的边界就是这条。

### 2.2 查表 → 派首选 → 逐级回落 → 再派发（try-and-fall，无 probe）

主 Agent 到某阶段派某角色，在铁律 1"通过平台派发工具启动 subagent"之前插一步机械路由（**此步在铁律 1 之前**）：

1. **查表**：`resolve((phase, role))` —— 按优先级序（项目级直接值 `candidates:` > 项目级档位映射 `tier:` > 机器级绑定 `tier_bindings:` 展开 > 出厂默认 → `standard`）解析出「默认派发」或「有序跨 CLI 候选链 `[{cli, model, effort?}, ...]`」。`(phase,role)` 命中优先于 `phase` 级。
2. `standard` / 无配置 → 直接默认派发（同平台、同 model），**不写** `dispatch_route` 事件（等价机制未启用）。
3. **try-and-fall**（不是 probe-then-commit）：**第一个动作就是把真实 dispatch-context 派给首选候选**——没有 "hi" 预探测。逐候选派发：
   - 起不来（`launch_fail`）/ 基础设施失败（`infra_error`：401 循环 / 网络不可达 / 429 / 进程崩溃 / `turn.failed` / 挂死被杀）/ 跑了但无可解析产出（`no_parseable_output`）→ 记理由码，试下一候选。
   - **收到任何 gate 能评的产出**（产出文件非空、presence 级骨架可解析）→ **停止回落**，交 gate。产出质量差 / 不完整**不是**回落信号（归 `HAS_OUTPUT`，走同候选正常 retry）。
4. 候选链耗尽 → 回落默认派发（`final = {"cli": "default"}`），留痕（§4）。
5. 写 1 条 `dispatch_route` 事件（`candidates_tried` 带理由码 + `final`），复用哈希链账本。

- **无预测性负载校验**：不预判"这次任务量该模型吃不吃得消"——撑爆了就是明确失败信号、走下一候选。与 gate"只信客观结果、不做主观预判"一致。
- **回落条件是纯机械的基础设施信号**，理由码枚举只有 `launch_fail` / `infra_error` / `no_parseable_output` 三值，**没有 `gate_fail`**。查表 / 回落不依据任务内容调整候选顺序——一旦按任务内容动态排序即越界为"主 Agent 语义选型"（与局限 3 同构的自由裁量），本设计明确排除。

### 2.3 `cli: native`——同平台换 model

- 不起子进程，用当前平台的原生派发原语，只指定 `model`。探测简化为"该 model 在当前平台是否被接受"，不涉及跨平台连通性。
- **前提：该平台得能让父会话为子代理指定 model。** 三平台情况（机制细节见 `docs/research/cross-platform-dispatch-mechanics.md` §5）：

  | 平台 | `cli: native` 可行性（"按次指定 model 能生效"这条三平台均端到端 `[实测]`，2026-09-08）|
  |---|---|
  | Claude Code | **✅ 直接**——Task/Agent 工具单次调用传 `model` 参数（Sonnet 会话 → Haiku 子代理）|
  | Codex | **✅ 直接**——`spawn_agent(model=…, reasoning_effort=…)`，通用 prompt 驱动（父 `medium` → 子 `high`）。比 Claude Code 多一个 `reasoning_effort` 维度。注：`spawn_agent` 的完整参数 schema 是模型自述（`[自述]`，非独立验证，见 research §5.2 / §7 事项 7）|
  | OpenCode | **✅ 间接**——`task`/`subagent` 工具调用**无 model 参数**；model 定在命名 subagent 配置 `agents.<name>.model`（实测 v1.18.11 生效：父 `deepseek-v4-flash` 派配了 `deepseek-v4-pro` 的命名 agent → 子确跑 `deepseek-v4-pro`；即旧 bug ①③ 不存在。旧 bug ②"父会话切 model 后子代理跟不跟"未直接复现，见 §7 事项 7）。要用 `cli: native` 得先按角色预配命名 agent，dispatch 表映射 phase→agent 名——比前两者多一层配置 |

- `phases.yaml` **不改**——`exec_role`（谁执行）与"该角色用什么 model"是两个关注点，分别由 `phases.yaml` 和本配置文件承载。
- **某平台 `cli: native` 不可行 / 未配好**：该平台在该 phase 就不提供 `native` 候选（改用 `cli: <平台名>` 子进程候选，或不配 = 维持现状）。等价于"该 phase 的 `native` 候选不存在"，不产生新失败风险。

### 2.4 `cli:` 另一个 CLI——起子进程

- 派发方式：起目标 CLI 子进程，传 model flag + dispatch-context 文件路径。铁律 2（只传路径不传内容）、铁律 3（只回摘要）不变。三平台的非交互入口 / model flag / 权限绕过 flag 见 `docs/research/cross-platform-dispatch-mechanics.md` §1、§2、§4；速记：`claude -p --model X --dangerously-skip-permissions` / `codex exec -m X --dangerously-bypass-approvals-and-sandbox` / `opencode run -m provider/model#variant --auto`。三平台子进程形式都已 `[实测]` 跑通。
- **权限拉平**：子进程要跳过该 CLI 自己的沙箱/审批，否则会出现"implementer 在子进程默认沙箱里做了权限妥协（某个该建的文件被拦），但主 Agent 用自己更宽松的原生环境跑 `gate_commands.P5` 反而通过"——产出环境比验证环境严格，gate 失真。flag 名落地前逐平台复核（research §10 清单）。
- **探测 / 结果识别按平台差异处理**（research §6）：Codex 退出码不可靠（未认证 = 401 重试循环；账号不支持的 model 会先过"已认证"层、真派发才 `turn.failed{400}`）——探测/派发对 Codex 必须**解析 `--json` 事件流**，不能只看退出码，`--json` 正好给了机器可读的失败原因。OpenCode 失效 model 可能空返回或结构化 Error JSON。这与 §2.2"真跑失败就走下一候选、不做预测性预判"一致。
- **Codex 按新增平台接入对待**：CLI 已核实（装好、ChatGPT 登录、`codex exec` + `-m` + `-c model_reasoning_effort` + `--dangerously-bypass-approvals-and-sandbox` + `spawn_agent` 均端到端生效），落地环境仍需自查可用 model 名单（随账号类型）与 `multi_agent` feature flag 状态（`codex features list`，命名有变更史，research §5.1）。`platform-notes.md` 的 Codex 章节从"待补充"补为完整设计 + 实机验证记录（素材即 research 报告）。
- **推理档位是与 model 正交的独立维度**（research §3）：`{cli, model}` 二元组不够，见 §7 事项 1、§8。
- **不采用第三方终端工具（Herdr / Claude Squad 等）作为正式依赖**：这类工具改善的是可观测性体验层（终端管理、agent 状态识别），但① 需要安装独立二进制或依赖工具，与协议"读文件就能用"的零基础设施原则冲突；② 不解决协议真正的核心矛盾——`LIMITATIONS.md` 局限 3"方向性错配"；③ 对应的局限 4 本身是协议主动选择不根治的次要局限（"根治需要平台支持，超出协议范围"）；④ 屏幕解析这条技术路线本身不可靠（业界方案也在往"优先用官方结构化信号、屏幕解析仅兜底"演化）。本设计的 tmux 观测（§3）只做最低限度"人能看"，不做状态识别，不与这类工具定位重叠。

### 2.4a 评审打回后的续跑（子进程 + native 两种形式都适用）

设计 1 → 评审打回 → 续原会话改 → 重交评审，这个循环**优先走平台官方续接、不重起**：

- **session id 已捕获**：spawn 子进程 / 调 native 派发原语时已记录 session id（存活监控要用，§7 事项 6）。候选项状态里一并存这个 id。
- **同 target 重做 → 续接**：cli+model（或 native 的目标 subagent）未变 → 用平台续接命令/原语，把评审意见作为新 prompt 传入：
  - 子进程：`claude -p --resume <id> '<意见>'` / `codex exec resume <id> '<意见>'` / `opencode run -s <id> '<意见>'`
  - native：Codex `followup_task` / OpenCode `task(task_id=<id>, prompt=<意见>)` / Claude Code 续接原语待核实
  - 子代理保留"当初为什么这么设计"的上下文，比重起省一大截。
- **续接是"重放重建"非"状态冻结"**（research §7，三平台 + DSH 共性；Claude Code 有 #43696 报告）——**不假设续接必成功**。重做 fallback 到了**不同 target** → 旧 session 作废，退化为**全新派发**、prompt 完整带回评审意见 + 必要上下文重申。
- **已知缺口：续接失败没有像探测失败那样的客观信号**（外部评审 W1）。探测失败 = 硬故障、走下一候选（§2.2）；但续接命令本身会**成功返回**（exit 0），只是内容表明上下文实际丢了——这是"看起来不对"的软信号，路由层没有可靠办法机械判定。目前只能靠：① 续接后的产出仍走假完成校验（D2）+ 本来就在评审循环里（续接产出质量差，下一轮评审会再打回，只是多绕一圈）；② **Claude Code 命中 #43696 的风险下，可选择对 Claude Code 默认不用续接、直接重起**（保守，落地定）。本设计不假装解决了这条，如实登记为缺口。
- retry 计数、超限 PAUSED 与现状一致——续接只是"这次 retry 怎么执行"的优化，不改 `retries[Pn]` 语义。

### 2.5 DSH：暂不纳入 CLI 派发路径

- DSH 是"everything is a plugin"的可插拔 launcher，headless 能力需要显式安装 `dsh-headless` 插件才存在，不是内置固定能力。
- 模型指定走配置文件（`$DSH_HOME/settings.yaml`），未确认是否支持单次调用临时覆盖模型，无法直接套用本设计"CLI 参数可显式指定 model"的前提。
- 结构化输出（JSON/JSONL）的官方支持程度不明确，已发现的相关能力是第三方社区扩展，非官方原生完整支持。
- DSH 处于 Developer Preview，`platform-notes.md` 一贯将其列为"新兴平台，需持续复核"，不适合作为本设计的首批验证对象。

DSH 的正式派发路径（`subagent`/`subagent_fork`/`workflow`）继续按现有协议使用，不受本设计影响。待 DSH headless CLI 能力成熟后可重新评估纳入。

### 2.6 自动化边界：决策全机械化，执行按形式分层

目标是"派发不依赖主 Agent"。拆成两层看：

- **路由决策层（查表 → 探测 → 选 target → 逐级回落 → 写 `dispatch_route` 事件）**：100% 机械，无自由裁量，应实现为 CLI（**优先扩展 `agate-dispatch.py`**，不成再新增 `agate-route.py`——§7 事项 3；归入 RM-AG0054 的 `agate next`/`agate advance`/`agate dispatch` 推进侧 CLI 家族）。主 Agent 或档位 C /loop 只调用，不参与判断。这一层**完全可自动化**。

- **派发执行层**：能不能脱离主 Agent，取决于路由形式——
  - **`cli:` 另一个 CLI（子进程形式）**：派发就是一条子进程命令（`codex exec --model X …` 之类）。CLI/脚本可完全接管 spawn → （§3 的 tmux 包裹）→ 等待**子进程退出**（正常完成的内在信号，不靠超时）→ 解析结构化输出判成败（research §6）→ 跑假完成校验 → 写事件，主 Agent / 档位 C 只需 `agate dispatch <phase>` 拿回"路径 + 摘要"。**这条形式能真正做到"派发不依赖主 Agent"。**
  - **存活性：子进程形式是三种路由里最好的**（research §6.0.2）——① `wait(pid)` = 完成信号；② `kill -0 pid` / proc 状态 = "死没死"的直接、极便宜信号（抓崩溃/OOM/僵尸），native 形式没有 PID、只能由 RM-AG0055「活动冻结」间接推；③ "卡没卡"复用 **RM-AG0055 命令流机制**（`agate-cmdstream-*.py`），子进程形式还能直接取 `--json` stdout 实时事件流、省去找会话文件；④ 路由脚本不被阻塞 → 走 RM-AG0055 §3.3 主动轮询，不是 §3.4 降级路径。`kill -0` 与命令流互补，两者都不是固定超时。
  - **不用固定紧超时**：固定紧超时会把本该跑久的合法任务强杀 = 违规处理。若确需外层 `timeout` 兜底，值须匹配任务预期、宁宽勿紧。
  - **`cli: native`（同平台换 model）**：实际启动 subagent 仍须走平台自己的派发工具（铁律 1"通过平台派发工具启动 subagent"），只有驱动会话能调用它。所以启动动作仍在会话侧——但**调用参数（目标 model）由决策层全量算好，会话零判断**。决策自动化，机械启动搭平台工具的车。

- 这就是摘要里"（如果可能的话）"的边界：子进程形式可端到端自动化；`native` 形式受平台约束，做到"决策自动、启动动作仍由会话代发但不掺判断"为止。两种形式的 gate 判定、留痕完全一致。

---

## 3. 机制二：tmux 观测（仅 CLI 子进程形式）

- **目的**：让人类用户在不介入协议流程的前提下，肉眼查看某个正在跑的子进程派发的实时输出。
- **机制**：起子进程时若 `which tmux` 成功 → `tmux new-session -d -s {session_name} '{命令}'` 包一层；失败则裸跑子进程。两条路径产出的 gate 结果、`dispatch_route` 留痕完全一致，走不走 tmux 不影响协议判断的任何环节。
- **与结果/存活捕获的衔接**（机制一要抓子进程 `--json` stdout，见 §2.6 / research §6）：tmux 包裹时子进程 stdout 进的是 pane 不是路由脚本的管道。解法——命令里带重定向 `tmux new-session -d -s {name} '{命令} > {capture.jsonl} 2>&1'`，路由脚本 tail 该文件（或用 `tmux pipe-pane`）。人看 pane、脚本读文件，两不误。落地时定这一处。
- **session 命名必须带命名空间**：如 `agate-{task_id}-{phase}-{短时间戳}`。同一机器上常已有别的 tmux session（本机核实：存在 `0` 和用户自己的 `cc`），裸名 `test` 之类会碰撞或误清理。所有 `list-clients`/`kill-session` 一律带 `-t {session_name}` 精确定位。
- **明确不做**：`send-keys` 交互、`capture-pane` 内容解析给主 Agent 用、跨轮次 session 复用。
- **session 生命周期（带退出倒计时，改善 attach 端体验）**：
  - wrapper 命令末尾自带收尾：`{命令} | tee {capture}` 跑完后，在 pane 里打 `=== 派发结束 ===` + 一个 N 秒倒计时（`本窗口将在 N 秒后关闭…，Ctrl+b d 可提前离开`，N 默认 ~15，可配），倒计时完 wrapper 自行退出 → 会话自然结束。
  - 路由脚本清理逻辑：`tmux list-clients -t {session_name}` **空**（没人看）→ 直接 `kill-session`，跳过倒计时；**非空**（有人正 attach）→ **不动手**，让 wrapper 的倒计时走完自然结束——attach 的人看着"N 秒后关闭"从容离开，比被瞬间踢出干净（本机实测：`kill-session` 时 client 会被整个拽出 tmux，无卡但突兀）。
  - 兜底：wrapper 若异常未退出（倒计时脚本本身挂了），路由脚本超过 `N + 余量` 仍见 session 存在 → 强制 `kill-session`。session 存在的唯一理由是"这次派发进行中或收尾倒计时中"，之外不留。
- `cli: native` 形式无子进程，本节不适用。

**实机核实（2026-09-08，含真人 attach）——环境代表性说明（外部评审 W2 round2）**：
- **实测环境**：Windows 11 主机上的 **WSL2**（Windows Subsystem for Linux v2，一个轻量虚拟机里的 Ubuntu）——**不是容器、不是 CI runner、不是纯物理机 Linux**。终端是 Windows Terminal 接进 WSL2 的 pty。tmux **3.4**（一个近年的稳定版；更新的 3.5 系列已发布，本轮未在其上测）。
- **代表性边界**：WSL2 的 pty / 进程 / 信号语义与主流 Linux 一致，本轮 tmux 生命周期 + attach/detach + kill 行为**没有 WSL 特有的偏差**，可视作 Linux 通用结果。但——① 极简容器镜像可能不装 tmux（`which tmux` 会失败 → 裸跑，本设计已覆盖）；② CI runner 通常无交互 pty，机制二"人 attach"在 CI 里本就用不上（CI 不看 pane，走 research §6 的 stdout/文件路径）；③ 不同 tmux 大版本（2.x vs 3.x）在 `pipe-pane` / `list-clients` 输出格式上有差异。
- **落地要求**：目标部署环境照 `docs/research/cross-platform-dispatch-mechanics.md` §10 在其自己的 tmux 版本上复跑一次本节的验证项（§7 事项 9 已登记）。
- `new-session -d` / `list-sessions` / `list-clients` / `kill-session` 起停干净、无残留。
- **真人 attach ✅**：看到子进程输出实时滚动；`Ctrl+b d` 干净 detach、会话继续。
- **有人 attach 时 `kill-session` ✅ 干净**（无卡住/花屏），但 client 会被整个拽出 tmux（若是 `Ctrl+b s` 切过去的工作 client，人就掉出 tmux 了）——突兀。**所以有 client attach 时不强杀，改由 wrapper 的退出倒计时（上面）自然收尾**，让人看着"N 秒后关闭"从容离开。
- **tmux 包裹 × 抓 stdout ✅**：`tmux new-session -d "{命令} | tee {capture}"` → pane 实时滚 + 文件同步在长，人看 pane / 脚本 tail 文件互不干扰（对应 §3 上面那条 W4 落地方式）。
- **非真实 TTY 输出 ✅**：本会话所有 `printf ... | codex exec` / `claude -p` / `opencode run` 的 stdout 都非 tty、输出正常；`--json` / `--format json` 本就为非交互设计。
本节已从"设计意向"转为可写进定稿。

---

## 4. 留痕

留痕是派发这个动作的固有属性，不因阶段类型而有例外——否则"候选全灭、一路 fallback 到底"会被兜底悄无声息吸收，没有信号提示"这次其实全灭了，只是默认派发接住了"。呼应局限 3："fallback 链若做得过于顺滑、不留痕，客观上会成为'主 Agent 倾向自行解决而非报告问题'的新出口。"

新增事件类型 `dispatch_route`，与既有 `gate_run` / `state_transition` / `judge_verdict`（`agate-workspace/tasks/*/gate-events.jsonl` 既有格式）同构：

```json
{"event": "dispatch_route", "phase": "P4", "task_id": "TAGxxxx",
 "candidates_tried": [
   {"cli": "native", "model": "claude-haiku-4-5", "result": "failed", "reason": "model_alias_rejected"},
   {"cli": "opencode", "model": "deepseek/deepseek-v4-flash", "result": "success"}
 ],
 "final": {"cli": "opencode", "model": "deepseek/deepseek-v4-flash"}, "ts": "..."}
```

- 候选全部失败、回落默认派发时同样记录，`final` 记为 `{"cli": "default"}` 并在 `candidates_tried` 里保留每个候选的失败原因。
- 正式产出文档（如 `P4-implementation.md`）建议顺手声明"本阶段由 {cli}/{model} 产出"，便于日后排查质量特征变化。建议项，非强制。

---

## 5. 影响面

- 新增**项目级** `agate-workspace/dispatch-routing.yaml`（配置文件，非协议本体，不受 SELF-GATE）；档位词表在协议本体 `agate/rules/dispatch-tiers.yaml`（改它走 SELF-GATE）。
- **路由决策 CLI 化**：优先扩展 `agate-dispatch.py`（不成再新增 `agate-route.py`，见 §7 事项 3），把"查表 → 派首选 → 逐级回落 → 写 `dispatch_route` 事件"（try-and-fall，无 probe，与 §2.2 一致）实现为脚本步骤。**派发决策命令是本设计新提议，不是 RM-AG0054 已定义的既有命令**——RM-AG0054 定义的是 `agate next`/`agate advance`（状态机推进决策，"该不该进入下一 phase"），本设计要落地的是派发决策（"这一步该派给哪个 CLI/model"），两者性质不同，只是都遵循"决策查表化、落在 CLI 里做"这个同一方向，归入同一 CLI 家族统一维护。子进程形式下由该脚本端到端接管 spawn/tmux/采集/校验（§2.6）。档位 C /loop 全自动路径下内联执行这条链。
- `dispatch-protocol.md` 新增一节：铁律 1 之前的"查表 → 派首选 → 逐级回落 → 再派发"（try-and-fall，无 probe，与 §2.2 一致）这一步；并显式写明"gate 判定不认谁生产的"这条解耦关系，防止未来有人误以为需要为跨 CLI 派发单独定制 gate。
- 新增 `dispatch_route` 事件：`gate-events.jsonl` 写入端 + `check-events.py` 校验端同步支持（复用既有哈希链完整性校验，不新增校验机制）。
- `platform-notes.md`：Codex 章节从"待补充"补为完整设计 + 实机验证记录。
- 各 CLI 的最高权限 flag 写进各自 `SETUP.md` 的"自动化环境"小节。
- **不改** `check-gate.py` / `check-state-transition.py`（gate 只认产出文件和 exit code）、**不改** `phases.yaml`、**不改**状态机（单层不变，gate 判定路径不感知路由）。

---

## 6. 风险与止损

| 风险 | 处理 |
|---|---|
| 用户想用异 CLI，得自己先装好、认证好那个 CLI | 这是**机会式**能力，不是强制基础设施——不配 = 现状；配了但没装 / 没认证 = 探测失败自动回落。没有"必须先搭好才能用协议"的东西，与局限 6 无实质冲突（见头部「机会式启用」）|
| `cli: native` 平台机制有已知 bug，配了不生效（尤其 judge 意外与 implementer 同模型，局限 2 收益落空且不自知）| §2.3 逐条实机验证；不通过的平台不启用；`dispatch_route` 留痕记录实际生效 model，可事后审计 judge 是否真用了独立模型 |
| Codex 沙箱/派发机制首次走 SETUP，成熟度未知 | 按新增平台接入对待，落地前独立实机验证，不与 Claude Code/OpenCode 同等对待 |
| 逐级回落链过于顺滑，"候选全灭"被悄悄吸收、成为"回避报告问题"的新出口 | §4 无差别留痕——不阻止回落，但每次回落（含回落到默认派发）都留痕、可事后追溯 |
| 配置内容质量（把高可靠性阶段配成低质量候选优先）| 责任在用户；协议只保证过程可追溯，不做内容质量把关 |
| 机制二 tmux 链路在目标环境有意外行为 | 已含真人 attach 全链路实测通过，但**实测环境是 WSL2 + tmux 3.4**（非容器/CI/物理机，环境代表性说明见 §3 末）；目标环境需在其自己的 tmux 版本上照 research §10 复跑（§7 事项 9）。不通过可整体移除，不影响机制一 |

---

## 7. 待确认事项

1. `agate-workspace/dispatch-routing.yaml` 的确切 schema（本文候选结构为示意；已定：无 `fallback` 字段，终点回落恒为默认派发）。**候选项需加可选推理档字段**——research §3 已确认 OpenCode / Codex 都有独立推理档维度，与 model 正交。`{cli, model}` 不够，需 `{cli, model, effort?}`（字段名待定）。
2. `dispatch_route` 事件的 JSON schema 细节 + `check-events.py` 校验端如何识别新事件类型（不能把未知 event 判为非法）。
3. **路由决策 CLI 的落点**（全文统一为：**优先扩展 `agate-dispatch.py`**，不成再新增 `agate-route.py`）：`cli: native` 形式下"决策层算出目标 model、启动仍由驱动会话代发平台派发工具"这一步的具体衔接方式（会话侧读什么文件、怎么保证零判断）；与 RM-AG0054 已落地的 `agate dispatch`（渲染 dispatch-context）是串联还是同一步。
4. ~~**探测成本与 `cli: native` 探测方式**~~（**2026-09-09 定案已作废**：核心循环改 try-and-fall、无 probe，故无"探测缓存"需求；`cli: native` 直接派首选、首次真派发失败再走三类基础设施信号逐级回落）：① ~~task 内探测缓存~~；② ~~`cli: native` 怎么探测"该 model 平台认不认"~~。
5. **与既有派发机制的交互**（本文未展开，立项设计要覆盖）：① 五模式并行批（模式 2/3）——每个并行 subagent 是否各自独立探测同一候选链、探测结果 task 内是否共享；② RM-AG0055 自主再派发的子任务——是否走路由表（倾向"不走，继承父的实际 cli/model"）；③ 单 Agent 模式（`has_task_tool:false`，如 Claude Project）——无派发动作，路由为 no-op，应显式声明出范围。
6. **RM 编号：已申领 RM-AG0060**（`agate-workspace/roadmap/roadmap.md`，status backlog，epic）。排期——检查是否与近期涉及 `dispatch-protocol.md` / 推进侧 CLI 的任务冲突（尤其 **RM-AG0059 任务管理命令化** 有 CLI 家族重叠，backlog）。**epic 拆分**：
   - **a 配置路由核心 + `cli: native`**（Claude Code/OpenCode）——U1–U5/U10，可单独交付。
   - **b 跨 CLI 子进程**——spawn + `--json` 解析 + D2；**Codex 接入拆到 RM-AG0061**（`CodexAdapter` + `platform-notes.md` Codex 章 + SETUP，RM-AG0055 §3.4.4 预留扩展点的落地，作 b 的前置——建议先做，去风险）。b 的 `cli: codex` 子进程部分依赖 RM-AG0061 的存活检测，可先发 `cli: claude-code`/`cli: opencode` 子进程。
   - **c tmux 观测层**——U9，可后置/可选，不通过可整体移除不影响 a/b；目标环境 tmux 验证若与任务环境不同则停在"定稿 + 待落地验证"、不阻塞 P8。
   - **一个 task 还是多个**：Codex 拆走后 a/b/c 重新评级掉到 medium 附近——**可一个 task 内分 P4a/P4b/P4c 串行子批交付**（参照 RM-AG0058/0057：epic + 一个 task），也可再拆多个 TAG。P2 立项定。
   - 建议排期：RM-AG0061（Codex 接入，去风险）与 a 并行 → b → c。
7. **平台机制的落地前复核**——照 `docs/research/cross-platform-dispatch-mechanics.md` §10 复核清单。本轮各条的**证据强度不一样，不能一句"已实测通过"带过**（外部评审 B1/B2）：
   - **端到端实测 `[实测]`**：Claude Code Task 传 `model`（父 Sonnet→子 Haiku）；Codex `spawn_agent(model=, reasoning_effort=)` 按次生效（父 medium→子 high）；OpenCode 命名 subagent `agents.<name>.model` 生效（父 flash→子 pro）——即 OpenCode 旧 **bug ①③ 已直接复现测试确认不存在**；三平台子进程权限绕过 + Codex 沙箱对照（`-s read-only` 拦）；结构化输出形态（Codex `--json` / OpenCode `--format json` / Claude `--output-format json`）；tmux 全链路含真人 attach。
   - **模型自述 `[自述]`，未独立验证完整性**：Codex `spawn_agent` 的参数 schema（`task_name`/`message`/`fork_turns`/`model`/`reasoning_effort`）——"未见 background/timeout/permission 字段"是"没在自述里看到"，**不等于确认没有**。落地写调用代码时不能假设 schema 已穷尽（如别假设无 timeout 参数就不处理超时）。
   - **机制推断，未直接复现**：OpenCode 旧 **bug ②**（父会话交互式切换模型后子代理是否跟随）——现有结论基于"`opencode run -m` 只改 session model、不改 agent 配置里的 model"这条机制推理 + 官方文档，**未跑直接复现测试**。落地前补一次：配好命名 agent、父会话交互式切 model、再派该 agent，核对子代理跑的是配置 model 还是父的新 model。
   - 剩余环境自查项（Codex API-key 账号 model 阵容）与低优项见 research §11。版本升级后照 §10 复跑。
8. **存活性 / 卡死检测复用既有机制，不自造超时**（research §6.0.1 / §6.0.2）：
   - 子进程形式：`wait(pid)` 完成 + `kill -0`/proc 状态判"死没死" + RM-AG0055 命令流（可直接取 `--json` stdout 流）判"卡没卡" + §3.3 式主动轮询（子进程可轮询，机制换成 PID/stdout 非心跳文件）。
   - `cli: native` 形式：无 PID，全靠 RM-AG0055 命令流机制（`agate-cmdstream-{adapters,detect,ir}.py`，TAG0028 已落地）。
   - **唯一缺口 = 写一个 `CodexAdapter`**（数据源 `~/.codex/sessions/**/*.jsonl`，按 RM-AG0055 §3.4.4"未来接 Codex：约一个文件"，检测引擎/阈值零改动）。落地衔接点：spawn / 调 `spawn_agent` 时捕获 session id。
9. 机制二 tmux 链路已含真人 attach 全链路实测通过（§3 末），但**实测环境是 WSL2 + tmux 3.4**——目标部署环境需在其自己的 tmux 版本上照 research §10 复跑一次（§3 末的环境代表性说明）。落地时定：`{命令} | tee {capture}` 里 capture 文件的路径/命名与生命周期；退出倒计时的 N 默认值与可配置项；wrapper 收尾脚本的写法（`printf '\r...' ; sleep 1` 循环，纯 sh）。
10. **（超出本设计范围，登记为独立开放问题）主 Agent 自身缺乏外部约束**：`LIMITATIONS.md` 局限 3"方向性错配"——防御机制布置在 subagent 一侧，握有全部裁量权且被实证是主要事故源的主 Agent 几乎没有外部约束（T005/T006/T016/T019 根因均为主 Agent）。这是协议当前最大的敞口，本设计（配置路由 + tmux 观测）完全不解决它，值得作为独立 design-note 另行立项讨论，本设计不认领。

---

## 8. 怎么填 `candidates` 表（非规范）

model 写法、可用 model 名单、推理档语法逐平台的细节见 `docs/research/cross-platform-dispatch-mechanics.md` §2 / §3。要点：

- `candidates` 里写**具体 model 串**（Claude Code alias/ID、`provider/model#variant`、Codex 白名单），**不是抽象档位**——协议不定义"档位"、不声明跨厂商档位等价（主观判断，与"只做可判定"冲突）。
- 推理档在 model 之外单列（`{cli, model, effort?}`，见 §7 事项 1）。
- **可用 model 随环境变**：Codex 随账号类型、OpenCode 部分配置失效——落地时各自 `codex exec --json` / `opencode models <provider>` 自查。
- 典型意图（示意）：judge / architect / consistency-reviewer 配高能力或异厂商 model；implementer（P4，产出量最大）配便宜 model；其余视需求。**具体怎么配、配得好不好是用户的事**（§2.1）。