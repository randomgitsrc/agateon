# 派发路由设计（agate 协议增强提案）

> **做什么**：新增 `rules/dispatch-routing.yaml`——按 phase 声明候选 `{cli, model}` 列表（用户用它编码"复杂/专业的阶段配高级或专业模型、大批量的阶段配便宜模型"这类意图）。到某阶段时查表 → 按序探测「通不通」→ 派发到第一个可用候选 → 候选全不可用则自动逐级回落，终点恒为"同平台、同 model"的默认派发。`cli` 可为 `native`（同平台换 model）或另一个 CLI（`claude-code`/`codex`/`opencode`，起子进程）。查表 / 探测 / 降级是纯机械步骤，目标是落在 CLI 里做、不依赖主 Agent 临场判断（§2.6）。子进程形式下若有 `tmux`，包一层供人类 `attach` 观测。
> **为什么**：见 §1。核心是给"角色隔离"补上模型维度——让任一阶段（尤其 P6.5 judge）能跑在与开发链不同的模型/厂商上，把 `LIMITATIONS.md` 局限 2 的"认知层隔离"往"真正的独立视角"推一步；顺带打开成本 / 模型多样性 / 专业度匹配的优化空间。
> **不做**：主 Agent 按任务内容动态选型（§2.2 边界）；会话续接机制（评审打回 = 协议现有 retry，§2.4）；第三方终端工具（Herdr/Claude Squad 等，理由见 §2.4 附注）作为依赖；DSH（理由见 §2.5）。局限 3"主 Agent 自身缺乏外部约束"超出本设计范围，不是本设计任何一条排除决定的理由，见 `LIMITATIONS.md`。
> **机会式启用，零强制基础设施**：不配置候选 = 行为与现状逐字节一致；配了但该 CLI 未装 / 未认证 / 无 `tmux` = 探测失败自动回落。多带一个 CLI/model 或 tmux 就用，否则退回原机制，不新增任何必须先搭好的东西——所以与局限 6"零基础设施"无实质冲突（§6）。
> **平台**：Claude Code、OpenCode、Codex。
> **相关**：`agate/dispatch-protocol.md`（派发三铁律）、`agate/rules/phases.yaml`（`exec_role`）、`agate/LIMITATIONS.md`（局限 2/4/6）、`agate/platform-notes.md`（Codex 现为"待补充"）、`docs/design-notes/design-orchestration-semantics.md`（RM-AG0054 推进侧 CLI，§2.6 决策 CLI 化的方向来源，但具体命令为本设计新提议，非既有命令）。
> **沿革**：由两条讨论线合并——跨 CLI 派发路由（v1 FAIL→v2 PASS→v3/v4→v5 三产出物拆分）+ 角色-模型映射（v1 FAIL：`fallback` 权威源分裂 → v2 PASS）。两线共用同一份配置文件，分作两份文档正是那个 BLOCKER 的成因，故合并；`cli: native` 即候选表的一个特化。2026-09-08 二次精简：范围收敛为"配置路由 + tmux 观测"两机制，移除会话续接 /`--resume` 可靠性分析、四平台续接机制调研、观测信号优先级原则（已在 RM-AG0055）；第三方终端工具（§2.4）与 DSH（§2.5）的排除理由保留但收紧。合并稿需重新走一轮独立评审再立项。
> **实机核实（2026-09-08）**：`cli: native` 单次派发指定 model（Agent 工具 `model` 参数）✅ 生效（Sonnet 会话派出 Haiku 子代理确认）；`cli: claude-code` 子进程形式（`claude -p --model X --dangerously-skip-permissions`）✅ 生效、非交互干净返回；`tmux` 3.4 会话生命周期 ✅ 正常。`codex`（v0.153.4，ChatGPT 登录）✅ `codex exec --dangerously-bypass-approvals-and-sandbox` 端到端跑通、默认 model `gpt-5.6-terra` 正确应答 exit 0；`-m` 在 CLI 层被接受、`-c model_reasoning_effort=high` 可改推理档；**model 阵容受账号类型限制**——ChatGPT 账号下 `-m gpt-5` / `-m gpt-5-codex` 均被 API 400 拒（"not supported ... with a ChatGPT account"），`--json` 给干净 `turn.failed` 事件。**Codex 有原生子派发原语 `spawn_agent`**（`collaboration` 工具族），已端到端验证按次可指定 `model` + `reasoning_effort`（父 `medium` → 子 `high` 生效）——故 `cli: native` **Claude Code 与 Codex 都适用**（§2.3）。`opencode`（v1.18.11）✅ `run -m deepseek/deepseek-v4-flash` 端到端跑通。其 `task`/`subagent` 工具**调用参数无 model**（两次模型自述 + 官方文档一致），按角色换 model 走**命名 subagent 配置**（`agents.<name>.model = "provider/model#variant"`，子用自己配的 model）——所以 OpenCode 做 `cli: native` 要先按角色预配命名 agent，比 Claude Code/Codex 多一层；`cli: opencode` 子进程（`run -m` + `--variant`）则是干净直路。注：OpenCode 配了多 provider，**部分 model 失效**（`deepseek/deepseek-chat` 报错、`MiniMax-M3` 空返回），候选表里的 OpenCode model 要挑实际可用的。详见对应小节。

---

## 1. 为什么要做

Agateon 的质量模型是"主 Agent 派发 → 每阶段一个独立上下文的 subagent 分角色执行 → 每阶段跑客观 gate"。角色隔离（analyst / … / judge）的目的是制造**独立视角**，让系统不能自己骗自己；P6.5 judge 更是以 fresh context 重验全部 BDD，专门打断"作者 = 裁判"的信任链（T026 教训）。

**局限 2 指出这层独立是结构性不完整的**：全部七个执行角色实际跑在**同一个底层模型**上（继承主 Agent 会话模型），同一训练分布下共享系统性盲区。角色隔离能防"明显偷懒"，防不住"这一类模型都会漏的边界"。`docs/design-notes/main-agent-oversight.md` 的"LLM 裁判员"方案正是因为"裁判与被裁判同源"被否决。局限 2 现状写死"无解"（ADR-006）。

当前协议**没有任何机制**能让某个阶段换一个模型跑——模型就是主 Agent 会话恰好在用的那个，judge 也不例外。

本设计给协议一个**机械的、配置驱动的**办法，让角色隔离真正跨模型/厂商：

1. **局限 2 的结构性部分缓解**——不同厂商模型仍各有盲区，但不再是同一个盲区；judge 跑在异源模型上，独立性不再打折。这是结构性改善，不是根治。
2. **模型档位匹配阶段特征**——每个 phase 的 `exec_role` 有相对稳定的认知需求画像，用户用候选表把它编码成"该用什么档位的模型"：P2 architect / P6.5 judge / P7 consistency-reviewer 这类"复杂或要专业判断"的阶段配高级或专业模型；P4 implementer 这类"产出量大但不一定需要顶尖智力"的阶段配便宜模型。**这个映射是用户在配置时一次性想清楚的**，不是运行时按任务内容动态判断（那越界成 §2.2 排除的语义选型）；静态 per-phase 配置只能逼近"复杂度→档位"，做不到"这一次的 P4 特别难所以临时升档"——真要那种粒度需要语义判断，超出本设计。

**决策机械化、不依赖主 Agent**：查表 → 探测 → 选 target → 逐级回落，全程无自由裁量，是纯脚本可完成的步骤。这承接 RM-AG0054"推进决策从 orchestrator 临场判断改为查表推进"的方向——路由决策同样应落在 CLI（本设计新提议的 `agate dispatch` 家族，非 RM-AG0054 已定义的既有命令，见 §5）里，主 Agent（或档位 C /loop）只调用、不参与判断（§2.6）。

**tmux 观测（§3）服务的是另一条**：局限 4（subagent 活动不可观测）。它只覆盖"CLI 子进程"这种路由形式——该形式比原生派发更黑盒（返回格式无平台背书），至少要保证人能肉眼确认它还活着，不让新路径在可观测性上零退路。这不是解决局限 4（协议明确该局限"根治需要平台支持"），是防止新路径造成可观测性倒退。

**边界**：不解决局限 3（主 Agent 单点故障）。与局限 6"零基础设施"**无实质冲突**——本机制是机会式的（头部已述）：不配 = 现状，配了但 CLI 没装/没认证 = 自动回落，没有"必须先搭好才能用"的东西。用户想用异 CLI 得自己先把那个 CLI 装好认证好，这是他自己的选择、不是协议强加的门槛。

---

## 2. 机制一：配置路由

### 2.1 配置结构

`rules/dispatch-routing.yaml`：按 phase 声明候选链。

```yaml
# 候选结构示意，非最终 schema
P4:
  candidates:
    - {cli: native, model: "claude-haiku-4-5"}   # 同平台换 model：implementer 派到便宜模型
    - {cli: opencode, model: "deepseek/deepseek-v4-flash"}
  # 两个候选都探测不过 → 自动回落到默认派发（同平台、同 model），不需要也不能配置

P6.5:
  candidates:
    - {cli: codex, model: null}                   # judge 派到异厂商模型；null = 该 CLI 默认模型
```

- `cli` 取值：`native`（不脱离当前会话的原生派发工具）| `claude-code` | `codex` | `opencode`（起子进程）。
- `{cli, model}` 是**原子绑定**，不拆成两个维度分别配——不同平台的 model 取值空间互不兼容（`opencode` 的 `provider/model` 写法 Claude Code 完全不认），拆开会产生非法组合，应在配置校验阶段拦下。
- **降级是一条逐级回落的链，终点固定、不可配置**：按候选声明顺序逐个探测，任一探测失败就试下一个；候选全部失败 → 自动回落到**默认派发**（当前平台原生派发工具 + 继承主 Agent 当前 model，即"同平台、同 model"）。这个终点恒等于"本机制未启用时的行为"，所以降级永远是"回到现状"，不会导致派发失败，也不需要用户声明。
- 配置文件**不属于协议本体**，不受 SELF-GATE；协议只定义"读取 / 探测 / 降级 / 留痕"这套机制，候选内容与优先级由使用者决定、后果自负。结构合法性（非法 `cli`/`model` 组合、非法取值）做静态校验，本设计只声明该层校验应存在。

### 2.2 查表 → 探测 → 派发

主 Agent 到某阶段，在铁律 1"通过平台派发工具启动 subagent"之前插一步：

1. 读表取该 phase 的候选链（无该 phase 条目 = 走默认派发，等价未启用）。
2. **按声明顺序**逐个探测——向候选 CLI/model 发一条极简请求（如 "hi"），只判硬故障（未认证 / 服务下线 / 未安装）。未登录 = 不可用，跳下一候选，留痕注明原因。
3. 第一个探测通过的候选 → 作为本次派发 target。
4. 全部失败 → 自动回落到默认派发（同平台、同 model），留痕（§4）。

- **探测尽量便宜**：不做预测性负载校验（"这次任务量该模型吃不吃得消"只有真跑才知道；撑爆了就是明确失败信号，走下一候选）。与 gate"只信客观结果、不做主观预判"一致。
- **探测只判"通不通"这一个二元结果**，不依据任务内容调整候选顺序。一旦探测逻辑开始按任务内容动态排序（"这次看着简单，跳过第一候选直接用便宜的"），即越界为"主 Agent 语义选型"——那是需要理解任务语义、无客观验证手段、与局限 3 同构的自由裁量，本设计明确排除。落地时对探测逻辑做显式约束（仅允许"是否可用"判断，不允许基于任务内容的顺序调整）。

### 2.3 `cli: native`——同平台换 model

- 不起子进程，用当前平台的原生派发工具，只指定 `model`。探测简化为"该 model 在当前平台是否被接受"，不涉及跨平台连通性。
- **前提：该平台得能让父会话为子代理指定 model。** 实机核实：**Claude Code、Codex 支持按次传参**（Task `model` / `spawn_agent(model=…)`，已端到端验证）；**OpenCode 只支持"命名 subagent 配置"这条间接路**（工具调用无 model 参数，model 定在 `agents.<name>.model`），要用得先按角色预配 agent。

  | 平台 | 原生子派发原语 | 状态（2026-09-08 本机核实） |
  |---|---|---|
  | Claude Code | Task/Agent 工具，单次调用可传 `model` 参数 | **✅ 支持 `cli: native`**——从 Sonnet 会话派 `model: haiku` → 子代理确为 `claude-haiku-4-5-20251001`。frontmatter `model` 字段路径未测（路由器走单次传参，不依赖它）|
  | Codex | `spawn_agent`（`collaboration` 工具族之一：`spawn_agent`/`followup_task`/`send_message`/`interrupt_agent`/`list_agents`/`wait_agent`）——通用、prompt 驱动、不限于预定义 skill-agent | **✅ 支持 `cli: native`**——父会话 `reasoning effort: medium`，`spawn_agent(model="gpt-5.6-terra", reasoning_effort="high")` 起的子代理回报 `gpt-5.6-terra high`。**按次可指定 `model` 且可指定 `reasoning_effort`**（比 Claude Code 多一个维度）。注：feature flag `collaboration_modes` stage 显示 `removed` 但 effective `true`（疑似已转常开），目标版本上需复核 |
  | OpenCode | `task`（V1）/ `subagent`（V2）工具 | **部分支持，但不是按次传 model**——工具调用参数只有 `description`/`prompt`/`subagent_type`（+ `task_id` 续接、`command`），**没有 model 参数**（两次模型自述 + 官方文档一致）。OpenCode 的按角色换 model 走**命名 subagent 配置**：`agents.<name>.model = "provider/model#variant"`，父按 `subagent_type` 名字调用，子用它自己配置的 model（官方文档："child session uses its subagent's configured model, or inherits the parent when none configured"）。→ 要在 OpenCode 上做 `cli: native`，得先按角色预定义好命名 agent（`agate-implementer` / `agate-judge` …），dispatch 表映射 phase→agent 名——比 Claude Code/Codex 的直接传参多一层配置。本次环境 `"agent": {}` 未配任何自定义 agent，故 `task` 只列出 `explore`/`general`（不是 bug，是没配）。旧"3 bug"里 ② 其实是官方设计（子用自己配的 model、不跟父会话临时切换——对本设计反而正好），① 需配好 agent 再实测 |

- `phases.yaml` **不改**——`exec_role`（谁执行）与"该角色用什么 model"是两个关注点，分别由 `phases.yaml` 和本配置文件承载。
- **`cli: native` 不适用 / 验证不通过的平台**：该平台在该 phase 就不提供 `native` 候选（改用 `cli: <平台名>` 子进程候选，或不配 = 维持现状）。等价于"该 phase 的 `native` 候选不存在"，不产生新失败风险。

### 2.4 `cli:` 另一个 CLI——起子进程

- 派发方式：起目标 CLI 子进程，传 `--model` + dispatch-context 文件路径。铁律 2（只传路径不传内容）、铁律 3（只回摘要）不变。
- **权限拉平**：子进程要跳过该 CLI 自己的沙箱/审批，否则会出现"implementer 在子进程默认沙箱里做了权限妥协（某个该建的文件被拦），但主 Agent 用自己更宽松的原生环境跑 `gate_commands.P5` 反而通过"——产出环境比验证环境严格，gate 失真。

  | 平台 | 非交互入口 + model flag | 权限绕过 | 本机核实 |
  |---|---|---|---|
  | Claude Code | `claude -p --model <alias或ID>` | `--dangerously-skip-permissions`（≡ `--permission-mode bypassPermissions`）| ✅ `claude -p --model haiku --dangerously-skip-permissions` 实测非交互返回 `claude-haiku-4-5-...`、exit 0 |
  | Codex | `codex exec -m/--model <MODEL>`（或 `-c model="..."`）；推理档 `-c model_reasoning_effort=<low\|medium\|high>` | `--dangerously-bypass-approvals-and-sandbox`（"skip all prompts + no sandbox, 仅供已外部隔离环境"）；中间档 = `-s <read-only\|workspace-write\|danger-full-access>` + `--approve-for-me`。**`--full-auto` / `-a` 已从 `codex exec` 移除**（旧设计"折中方案 `-a never -s workspace-write`"的写法已过期）| ✅ ChatGPT 登录后 `codex exec --dangerously-bypass-approvals-and-sandbox` 端到端跑通、默认 `gpt-5.6-terra` 应答 exit 0；`-m` / `-c model_reasoning_effort` 均在 CLI 层生效。**model 阵容受账号类型限制**：ChatGPT 账号下 `-m gpt-5-codex` 被 API 400 拒——见下"探测注意" |
  | OpenCode | `opencode run -m provider/model`（`--variant` 可选）| `opencode run --auto`（"auto-approve permissions that are not explicitly denied"，官方标注 dangerous）——**非默认，需显式传** | ✅ v1.18.11、多 provider 已认证；`run --auto -m deepseek/deepseek-v4-flash` 端到端跑通。**部分配置的 model 失效**（`deepseek/deepseek-chat` UnknownError、默认 `MiniMax-M3` 空返回）——用 `opencode models <provider>` 查有效 id |

  flag 名落地前逐平台对最新官方文档复核一次（版本变化会改名）。**推理档位是与 model 正交的独立维度**：OpenCode `--variant`（high/max/minimal）、Codex `exec` 启动 banner 有独立的 `reasoning effort` 行——`{cli, model}` 二元组可能不够，见 §7 事项 1、§8。
  **探测注意**（§2.2）：Codex 的失败不总是干净的非零退出——未认证时打 banner 后对 websocket 反复 401 重试；**账号不支持所配 model 时先通过"CLI 已认证"这层、再在真派发时被 API 以 400 拒**（实测：ChatGPT 账号 `-m gpt-5-codex` → `{"type":"turn.failed","error":{...400...}}`）。所以探测/派发对 Codex 要**解析 `--json` 事件流**（`turn.failed` / `item.type:error`），不能只看退出码——这与 §2.2"真跑失败就走下一候选、不做预测性预判"一致，`--json` 正好给了机器可读的失败原因。
- **Codex 按新增平台接入对待**，落地前独立实机验证。已核实：CLI 装好、ChatGPT 登录后 `codex exec` 端到端跑通、`-m` / `-c model_reasoning_effort` / `--dangerously-bypass-approvals-and-sandbox` 生效、默认 `gpt-5.6-terra`；**原生子派发 `spawn_agent` 存在且按次可指定 `model` + `reasoning_effort`**（端到端已验，见 §2.3），故 Codex 既能作 `cli: codex` 子进程候选、也能作 `cli: native` 候选。剩余：可用 model 名单随账号类型（ChatGPT vs API key）而变，需落地环境自查；`collaboration_modes` feature flag 在目标版本上的开启状态需复核。`platform-notes.md` 的 Codex 章节从"待补充"补为完整设计 + 实机验证记录。
- **Codex 子进程形式有原生结构化输出优势**：`codex exec --json` 直接吐 JSONL 事件流、`-o <FILE>` 落最终消息——比裸文本采集更适合 §4 留痕与假完成校验。
- **评审打回**：不做任何续接机制。打回就是协议现有的 retry——重新起一次该候选的派发，prompt 里带上评审意见与必要的上下文重申。计入 `retries[Pn]`，超限走 PAUSED，与现状完全一致。
- **不采用第三方终端工具（Herdr / Claude Squad 等）作为正式依赖**：这类工具改善的是可观测性体验层（终端管理、agent 状态识别），但① 需要安装独立二进制或依赖工具，与协议"读文件就能用"的零基础设施原则冲突；② 不解决协议真正的核心矛盾——`LIMITATIONS.md` 局限 3"方向性错配"（防御机制布置在 subagent 一侧，握有全部裁量权且被实证是主要事故源的主 Agent 几乎没有外部约束）；③ 对应的局限 4（subagent 活动不可观测）本身是协议主动选择不根治的次要局限（"根治需要平台支持，超出协议范围"）；④ 这类工具自身的屏幕解析这条技术路线也不完全可靠（业界方案本身也在往"优先用 agent 官方结构化信号，屏幕解析仅兜底"演化）。本设计的 tmux 观测（§3）只做最低限度的"人能看"，不做状态识别，不与这类工具的定位重叠。

### 2.5 DSH：暂不纳入 CLI 派发路径

- DSH 是"everything is a plugin"的可插拔 launcher，headless 能力需要显式安装 `dsh-headless` 插件才存在，不是内置固定能力。
- 模型指定走配置文件（`$DSH_HOME/settings.yaml`），未确认是否支持单次调用临时覆盖模型，无法直接套用本设计"CLI 参数可显式指定 model"的前提。
- 结构化输出（JSON/JSONL）的官方支持程度不明确，已发现的相关能力是第三方社区扩展，非官方原生完整支持。
- DSH 处于 Developer Preview，`platform-notes.md` 一贯将其列为"新兴平台，需持续复核"，不适合作为本设计的首批验证对象。

DSH 的正式派发路径（`subagent`/`subagent_fork`/`workflow`）继续按现有协议使用，不受本设计影响。待 DSH headless CLI 能力成熟后可重新评估纳入。

### 2.6 自动化边界：决策全机械化，执行按形式分层

目标是"派发不依赖主 Agent"。拆成两层看：

- **路由决策层（查表 → 探测 → 选 target → 逐级回落 → 写 `dispatch_route` 事件）**：100% 机械，无自由裁量，应实现为 CLI（扩展 `agate-dispatch.py` 或新增 `agate-route.py`，归入 RM-AG0054 的 `agate next`/`agate advance`/`agate dispatch` 推进侧 CLI 家族）。主 Agent 或档位 C /loop 只调用，不参与判断。这一层**完全可自动化**。

- **派发执行层**：能不能脱离主 Agent，取决于路由形式——
  - **`cli:` 另一个 CLI（子进程形式）**：派发就是一条子进程命令（`codex exec --model X …` 之类）。CLI/脚本可完全接管 spawn → （§3 的 tmux 包裹）→ 等待 → 采集结果 → 跑假完成校验 → 写事件，主 Agent / 档位 C 只需 `agate dispatch <phase>` 拿回"路径 + 摘要"。**这条形式能真正做到"派发不依赖主 Agent"。**
  - **`cli: native`（同平台换 model）**：实际启动 subagent 仍须走平台自己的派发工具（铁律 1"通过平台派发工具启动 subagent"），只有驱动会话能调用它。所以启动动作仍在会话侧——但**调用参数（目标 model）由决策层全量算好，会话零判断**。决策自动化，机械启动搭平台工具的车。

- 这就是摘要里"（如果可能的话）"的边界：子进程形式可端到端自动化；`native` 形式受平台约束，做到"决策自动、启动动作仍由会话代发但不掺判断"为止。两种形式的 gate 判定、留痕完全一致。

---

## 3. 机制二：tmux 观测（仅 CLI 子进程形式）

- **目的**：让人类用户在不介入协议流程的前提下，肉眼查看某个正在跑的子进程派发的实时输出。
- **机制**：起子进程时若 `which tmux` 成功 → `tmux new-session -d -s {session_name} '{命令}'` 包一层；失败则裸跑子进程。两条路径产出的 gate 结果、`dispatch_route` 留痕完全一致，走不走 tmux 不影响协议判断的任何环节。
- **session 命名必须带命名空间**：如 `agate-{task_id}-{phase}-{短时间戳}`。同一机器上常已有别的 tmux session（本机核实：存在 `0` 和用户自己的 `cc`），裸名 `test` 之类会碰撞或误清理。所有 `list-clients`/`kill-session` 一律带 `-t {session_name}` 精确定位。
- **明确不做**：`send-keys` 交互、`capture-pane` 内容解析给主 Agent 用、跨轮次 session 复用。
- **session 生命周期**：该次派发结束（无论成败）即 `tmux kill-session -t {session_name}`；session 存在的唯一理由是"这次派发进行中"，理由不再成立就清理。唯一例外：清理前 `tmux list-clients -t {session_name}` 非空（有人正 attach）→ 延迟清理，待客户端断开后再清理。
- `cli: native` 形式无子进程，本节不适用。

**实机核实（2026-09-08，本机 tmux 3.4）**：`new-session -d` / `list-sessions` / `list-clients` / `kill-session` 均按预期工作，起停干净、无残留。**仍待验证**：① 真人 `attach` 看实时滚动输出 + `Ctrl+b d` 退出不杀会话；② 有人 attach 时触发清理，attach 端是正常提示还是被直接踢出；③ 某 CLI 在非真实 TTY 下是否拒绝正常输出。验证前本节视为设计意向；不通过则机制二整体移除，不影响机制一。

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

- 新增 `rules/dispatch-routing.yaml`（配置文件，非协议本体，不受 SELF-GATE）。
- **路由决策 CLI 化**：新增 `agate-route.py`（或扩展现有脚本，具体落点待定，见 §7 事项4），把"查表 → 探测 → 选 target → 逐级回落 → 写 `dispatch_route` 事件"实现为脚本步骤。**命令名 `agate dispatch`/`agate route` 是本设计新提议，不是 RM-AG0054 已经定义的既有命令**——RM-AG0054 定义的是 `agate next`/`agate advance`（状态机推进决策，"该不该进入下一 phase"），本设计要落地的是派发决策（"这一步该派给哪个 CLI/model"），两者是不同性质的决策，只是都遵循"决策查表化、落在 CLI 里做"这个同一方向，建议归入同一个 CLI 家族统一维护，但命令本身需要新增，不能假设已存在。子进程形式下由该脚本端到端接管 spawn/tmux/采集/校验（§2.6）。档位 C /loop 全自动路径下，该命令内联执行这条链。
- `dispatch-protocol.md` 新增一节：铁律 1 之前的"查表 → 探测 → 定 target → 再派发"这一步；并显式写明"gate 判定不认谁生产的"这条解耦关系，防止未来有人误以为需要为跨 CLI 派发单独定制 gate。
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
| 机制二 tmux 链路在目标环境有意外行为 | §3 待实机验证；不通过则机制二整体移除，不影响机制一 |

---

## 7. 待确认事项

1. `rules/dispatch-routing.yaml` 的确切 schema（本文候选结构为示意；已定：无 `fallback` 字段，终点回落恒为默认派发）。**候选项需加可选推理档字段**——已实测两平台都有：OpenCode `--variant`（high/max/minimal）、Codex `-c model_reasoning_effort`（low/medium/high），与 model 正交。`{cli, model}` 不够，需 `{cli, model, effort?}`（字段名待定）。
2. 各 CLI 权限绕过 flag 的准确名称——落地前逐平台对最新官方文档复核（本机已核实 `claude --dangerously-skip-permissions`；`opencode run --auto` flag 存在但未跑；Codex 未装）。
3. `dispatch_route` 事件的 JSON schema 细节。
4. **路由决策 CLI 的落点**：扩 `agate-dispatch.py` 还是新增 `agate-route.py`；`cli: native` 形式下"决策层算出目标 model、启动仍由驱动会话代发平台派发工具"这一步的具体衔接方式（会话侧读什么、怎么保证零判断）。
5. RM 编号申领与排期——检查是否与近期其他涉及 `dispatch-protocol.md` / 推进侧 CLI 的任务冲突（参照 RM-AG0054/RM-AG0055 立项前的排期检查惯例）。
6. **三平台 `cli: native` 已核清**（§2.3）：Claude Code ✅ 按次传参、Codex ✅ 按次传参（`spawn_agent`，含 `reasoning_effort`）、OpenCode ⚠ 只能走"命名 subagent 配置"间接路（工具调用无 model 参数）。剩余复核点：OpenCode 配好命名 agent 后 `agents.<name>.model` 是否真生效（旧 bug ① 是否仍在）；`collaboration_modes` flag 在目标 Codex 版本的开启状态；Claude Code frontmatter-model 路径（路由器不依赖，低优）。
7. **各环境的有效 model 名单要自查**——Codex 受账号类型限制（ChatGPT 账号只 `gpt-5.6-terra`）；OpenCode 配了多 provider 但部分失效（`opencode models <provider>` 查）。候选表里写的 model 必须是落地环境实际可用的，否则探测/派发失败走回落。
8. 机制二 tmux 链路剩余验证项（§3 末：真人 attach 滚动 / 清理时 attach 端体验 / 非真实 TTY 输出）。
9. **（超出本设计范围，登记为独立开放问题）主 Agent 自身缺乏外部约束**：`LIMITATIONS.md` 局限 3"方向性错配"——防御机制布置在 subagent 一侧，握有全部裁量权且被实证是主要事故源的主 Agent 几乎没有外部约束（T005/T006/T016/T019 根因均为主 Agent）。这是协议当前最大的敞口，本设计（配置路由 + tmux 观测）完全不解决它，值得作为独立 design-note 另行立项讨论，本设计不认领。

---

## 8. 参考：各平台模型 / 档位速览（非规范，时效性强）

用来帮用户填 `candidates` 表，**不是协议规则**——模型阵容变化快，落地前逐平台对最新官方文档复核；协议本身不定义"档位"，也不声明跨厂商档位等价（那是主观判断，与"只做可判定"冲突）。`candidates` 里写的是具体 model 串，不是抽象档位。

| CLI | model 写法 | 大致档位（低成本 → 高能力）| 额外维度 |
|---|---|---|---|
| **Claude Code**（`--model` / Agent 工具 `model` 参数）| alias 或完整 ID | `fable`（`claude-fable-5-1`，小而快）< `haiku`（`claude-haiku-4-5-20251001`）< `sonnet`（`claude-sonnet-5`）< `opus`（`claude-opus-5`）| `--fallback-model` 为 CLI 自带的降级（与本设计的候选链正交，可叠加）|
| **OpenCode**（子进程 `opencode run -m provider/model` 直路；`cli: native` 需先按角色预配命名 subagent，工具调用本身无 model 参数）| `provider/model#variant`，取值空间取决于用户配的 provider；**部分配置的 model 实际失效**，用 `opencode models <provider>` 查有效 id | 由所选 provider 决定，协议无从枚举 | model 串里 `#high` 之类即 `--variant`（provider-specific reasoning effort），见 §7 事项 1 |
| **Codex**（子进程 `codex exec -m/--model`；`native` 走 `spawn_agent`）| **随账号类型而变**：ChatGPT 登录只 `gpt-5.6-terra`（实测；`gpt-5` / `gpt-5-codex` 均 400）。API key 账号才有 gpt-5 家族——落地环境自查 | 推理档：子进程 `-c model_reasoning_effort=<low\|medium\|high>`、`native` 传 `spawn_agent(reasoning_effort=...)`（均实测生效，与 model 正交）；`--json` 原生 JSONL 事件流利于留痕/探测。**`spawn_agent` 支持按次 `model`+`reasoning_effort`，两种形式都可用** |

典型配法（示意）：judge / architect / consistency-reviewer 这类"要专业判断"的阶段配 `opus` 或异厂商高能力 model；implementer（P4，产出量最大）配 `haiku` 或 `fable` / 便宜 provider model；analyst / test-designer 视需求配中档。**具体怎么配、配得好不好，是用户的事**（§2.1）。