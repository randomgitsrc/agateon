# P0-brief — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测）（RM-AG0060）

> 主 Agent 亲自填写（P0 产出）。RM-AG0060（`agate-workspace/roadmap/roadmap.md`，backlog→scheduled，**epic**）。
> **设计依据**：`docs/design-notes/design-dispatch-routing.md`（终版；两轮外部独立评审 FAIL→PASS +
> 一轮内部——`docs/reviews/review-dispatch-routing-external-20260908.md` 与 `-round2-`）。机制调查
> `docs/research/cross-platform-dispatch-mechanics.md`（三平台 CLI 调用 / model 指定 / 子代理派发 /
> 返回识别 / 续接，A1-A19 实测记录 + §10 落地前复核清单 + §11 未尽项状态）。
> **前置（已解除）**：**RM-AG0061 / TAG0033**（Codex 命令流适配器 + 平台接入）**已于 2026-09-09
> 合并 main → v0.70.0**（PR #298）。`agate-cmdstream-adapters.py` 现含 `CodexAdapter`（`ADAPTERS["codex"]`），
> b 块的 `cli: codex` 子进程存活检测直接复用它，检测引擎 / 阈值 / IR 零改动。TAG0033 复盘
> （`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md`）三条 agate 反馈落
> DEBT0037（check-gate P4 多提交阶段判据）/ DEBT0038（check-judge-verdict 信息隔离误判）/ DEBT0039
> （dispatch_plan 批次执行阶段标注）——**DEBT0037 与本任务直接相关**（本任务是 static-batch 多提交
> 阶段任务，P4a/P4b/P4c 分批 commit 会命中该局限，见 known_risks）。
> **epic 形态**：Codex 接入拆走后按五维评级 ≈ medium，一个 task 内分 P4a/P4b/P4c 串行子批（参照
> RM-AG0058/0057：epic + 一个 task），P2 若判需再拆多 TAG 则另起。

## task

"在 agate 协议层落地派发路由设计（RM-AG0060）——新增**项目级**配置文件
`agate-workspace/dispatch-routing.yaml`（对齐 `agate-workspace/maintainability.yaml` 先例：项目级、
全兜底、非协议本体、不受 SELF-GATE），按 `(phase, role)` 声明候选 `{cli, model, effort?}` 路由（或
引用命名**档位**——见 scope 待确认「配置分层与落点」「档位（tier）抽象」两项）：主 Agent 到某
阶段派某角色时**查表 → 直接派首选候选 → 若『起不来 / 基础设施失败 / 无可解析产出』则逐级回落到
下一个候选 → 全落空则默认派发（同平台同 model，恒等于本机制未启用）**——不做派发前的空探测
（try-and-fall，不是 probe-then-commit）。`cli` 可为 `native`（同厂商换 model，不脱离原生派发工具——
**弱缓解**：省成本 + 一点 failure-mode 多样性，同训练系谱盲区基本共享）或另一个 CLI
（`claude-code`/`codex`/`opencode`，起子进程——**强缓解**：真正的异源独立视角，局限 2 想要的那个）。
协议本体（`agate/rules/` 或 `phases.yaml` 旁）只放**档位词表 + 语义 + 出厂默认**（全 `(phase,role)`
= `standard` ≡ 现状）；档位→具体 `{cli,model,effort}` 的绑定是**机器/安装级**、随 SETUP 流程 scaffold、
以本机现状为准（能用就用、不能用不强制，不追求跨机可复现）。查表/回落/降级是纯机械步骤、落在
CLI 里（优先扩 `agate-dispatch.py`），主 Agent / 档位 C 只调用。**候选回落 ≠ 状态机 retry**：回落只在
基础设施失败时发生，不占 `retries[Pn]`、不触发 PAUSED、只写 `dispatch_route` 事件；**一旦某候选
产出了 gate 能评的东西，这条路由即成功——哪怕 gate 判 FAIL，那是正常阶段 retry（在同一候选上
重跑），绝不换候选**（防「换模型试到出 green」的完整性洞）。
新增 `dispatch_route` 事件无差别留痕。子进程形式若有 `tmux` 则包一层供人 `attach` 观测（wrapper
自带退出倒计时）。**gate / 状态机 / `phases.yaml` 全不动**——gate 只认产出文件和 exit code、不认
『谁生产的』，这条解耦是设计成立的前提。存活/卡死检测复用 RM-AG0055 命令流机制（+ 子进程形式的
`wait(pid)` / `kill -0`），不自造超时。动机 = 给角色隔离补模型维度、部分缓解 `LIMITATIONS.md`
局限 2（同源模型系统性盲区，现状 ADR-006 无解）。"

### scope

P2 声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial（依赖链，不并行）}`。

- **P1/P2 必须先定掉的设计类待确认**（design-note §7 事项 1-5 中「探测缓存 + native 探测方式」一项
  已因砍掉 probe 作废；其余 + 本次讨论新增项）
  - **配置分层与落点**（design-note §2.1 现把文件放 `rules/` 且写「非协议本体」自相矛盾——`agate/rules/`
    就是协议本体；P1 须重写 §2.1 + 头部「做什么」并在本任务交付该 design-note 修订）。三层：
    ① **协议本体**（`agate/rules/` 或 `phases.yaml` 旁）——档位词表 + 每档语义画像 + 出厂默认
    `(phase,role)`→档位映射（全 `standard`），改它走 SELF-GATE（改「什么是 `deep`」本就该评审）；
    ② **机器/安装级**——档位→有序候选链 `[{cli,model,effort}]` 的具体绑定（「本机 `deep` =
    codex/gpt-5.6-terra 再 claude-code/opus」），依赖「装了哪些 CLI + 哪个账号 + 该账号能用哪些
    model」，落 `~/.config/agate/` 或 `~/.agate` 同级**非版本控制**路径，由 SETUP 流程（比照
    「步骤 2-Codex」的 per-platform onboarding）scaffold 出带注释的初始模板（探测本机已装 CLI +
    各自默认 model）；③ **项目级**（`agate-workspace/dispatch-routing.yaml`）——`(phase,role)`→档位映射
    + per-`(phase,role)` 直接值覆盖，只引用档位名故跨机器可移植。**MVP 可合并①③为单文件 + 内联档位定义**
    （对齐 `maintainability.yaml`），是否真拆出机器级档位文件由 P2 按「团队/多机可移植性是否真需求」定。
    全兜底：文件缺失/损坏/类型坏 → 出厂默认（= 现状），不报错不静默跳过（复用
    `check-maintainability.py:_load_config` 模式）
  - **档位（tier）+ effort 两个正交轴**（用户 2026-09-09：类比 Anthropic `haiku/sonnet/opus`、
    OpenAI `luna/terra/sol`）：
    - `tier`（能力档，提议 `bulk / standard / deep`——名字 P1 定）：语义画像写进协议文档
      （`bulk`=高吞吐低成本产出量大 / `standard`=**恒等于继承主 Agent 当前 model 的原生派发、保
      「不配置=逐字节现状」不变量** / `deep`=高能力复杂判断）。经机器级绑定映射到 `{cli, model}`
    - `effort`（`low/medium/high` 可选，与 tier 正交——「便宜模型+高 effort」「顶配+低 effort」都合法）：
      映射到各平台推理档 flag——Codex `-c model_reasoning_effort=` / `spawn_agent.reasoning_effort` ✓；
      OpenCode `--variant high|max|minimal` ✓（近似）；**Claude Code CLI 无干净 effort 旋钮 → 该平台
      静默忽略**并在 `platform-notes.md` 写明（沿用模式层/检测器层：协议声明轴、各平台能映射就映射）
    - 配置里 `(phase,role)` 可写 `tier: deep, effort: high`（引用，可移植）**或**
      `candidates: [{cli,model,effort}]`（直接值，跳过档位间接层，牺牲可移植换明确）——静态校验器
      两种写法都要认。档位→候选是一条有序跨 CLI 链，逐级回落逻辑不变
  - **路由 key 粒度 = `(phase, role)`，role 层可选**：一个 phase 会派多个 subagent（P1 analyst+
    requirements-review / P4 implementer+protocol-alignment-review+code review）。想让 reviewer 跑异
    模型（executor↔reviewer 局部独立）就显式配 `P4.review:` 一条；**不强制分开**——只配 phase 级 /
    只有一个候选 → executor 与 reviewer 都用它。解析顺序：`(phase,role)` → `phase` → 未配 = `standard`
  - `agate-workspace/dispatch-routing.yaml` / 档位文件的确切 schema（已定：无 `fallback` 字段、终点
    回落恒为默认派发、`tier` + `effort?` 两轴、`(phase,role)` key 且 role 可选；待定：字段名、
    `{cli: native, model: null}` 是否合法、档位定义块与 `(phase,role)` 映射块的分隔形式、
    `tier`/`candidates` 二选一的校验）+ 静态校验器落点（新增校验器，非 `agate/rules/schema` 下的协议 schema）
  - `dispatch_route` 事件里「为什么回落」的**理由码**枚举——合法值只有 `launch_fail`（起不来）/
    `infra_error`（auth/网络/429/进程崩溃）/ `no_parseable_output`（跑了但没有 gate 能评的产出）；
    **不存在 `gate_fail` 值**（机械强制「gate verdict 不触发换候选」的完整性不变量）
  - `dispatch_route` 事件 JSON schema + `check-events.py` 如何识别新事件类型（不能把未知 event 判为非法）
  - 决策 CLI 落点（**优先扩 `agate-dispatch.py`**，不成再新增 `agate-route.py`）；`cli: native` 形式
    "决策层算出目标 model → 启动仍由驱动会话代发平台派发工具"的衔接方式（会话侧读什么文件、怎么
    保证零判断）；与 RM-AG0054 已落地的 `agate dispatch`（渲染 dispatch-context）是串联还是同一步
  - retry / 回退时的路由：P5→P4 回退后的 P4 retry 等，**重新解析一次 `(phase,role)` 路由**（落哪个
    候选看当时哪个能用），**不做「上次那个模型失败了所以这次故意升档/换模型」的逻辑**——retry 是
    状态机行为、路由是机械查表，两者不耦合
  - 与既有派发机制的交互：① 五模式并行批（模式 2/3）——每个并行 subagent 各自独立解析 `(phase,role)`
    路由（同 role 的并行分片用同一条路由）；② RM-AG0055 自主再派发的子任务——是否走路由表（倾向
    「不走，继承父的实际 cli/model」）；③ 单 Agent 模式（`has_task_tool:false`）——路由为 no-op，
    显式声明出范围
- **P1/P2 前置真机核实**（design-note §7、research §10/§11；外部评审 B1/B2）
  - OpenCode 旧 bug②（父会话交互式切 model 后子代理跟不跟——本会话只机制推断未直接复现）**直接复现测试**
  - Codex `spawn_agent` 完整 schema **TAG0033 已直接实测**（P6 V7：`spawn_agent` 嵌套 depth 1→2
    生效、`fork_turns` / `model` / `reasoning_effort` 按次可传；V2：跨 9 次真实调用键并集无 `[自述]`
    之外的键）——本任务直接引用 `TAG0033/retrospective.md` §一 + `platform-notes.md` Codex 章，不再重测；
    仅需补 TAG0033 out-of-scope 的 V8（API-key 账号 model 阵容，本机 ChatGPT 账号环境不可得、登记待补）
  - **TAG0033 F1 / DEBT0035 的连带认知**：真机 Codex 把「已结束但非 0 退出」的命令记为
    `payload.item.status == "failed"`（携带完整 `exit_code` / `completed_at_ms`）——子进程结构化输出
    解析判成败时（P4b），`codex exec --json` 的 `turn.failed` 与 item 级 `status: "failed"` 是两层，
    P2 设计须明确取哪层、与退出码不可靠如何叠加
- **P4a — 配置路由核心 + `cli: native`**（design-note §2.1-§2.6，机制细节 research §5）
  - `agate-workspace/dispatch-routing.yaml`（新，**项目级、全兜底、非协议本体、不受 SELF-GATE**；
    对齐 `agate-workspace/maintainability.yaml`）+ 静态校验器（新增，独立于 `agate/rules/schema`）
  - 协议本体侧：档位词表 + 语义画像 + 出厂默认（`agate/rules/` 下新文件或 `phases.yaml` 扩字段，
    **走 SELF-GATE**）；机器级档位绑定文件的 scaffold 接入 SETUP 流程（`agate/SETUP.md` 新小节）
  - `agate-dispatch.py` 扩展：读表（按 `(phase,role)` 解析 → 展开 `tier`/`effort` 或直接值为候选链）
    → 派首选 target → 若 `launch_fail` / `infra_error` / `no_parseable_output` 则逐级回落 → 全落空
    默认派发 → 写 `dispatch_route` 事件（带理由码）。**无 probe 步骤**（try-and-fall）；**回落条件
    显式约束为上述三类基础设施信号，收到任何 gate 能评的产出即停止回落**
  - `dispatch_route` 事件：`gate-events.jsonl` 写入端 + `check-events.py` 校验端（复用既有哈希链）；
    理由码枚举校验（`gate_fail` 为非法值）；候选回落**不写 `state_transition`、不动 `retries`**
  - `cli: native` 执行：Claude Code（Task 单次调用传 `model`，本会话实测生效）+ OpenCode（命名
    subagent 配置 `agents.<name>.model` 间接路——需定义 dispatch 表 phase→预配命名 agent 的映射与
    预注册机制；本会话实测 v1.18.11 生效，旧 bug ①③ 不存在）
  - `dispatch-protocol.md` 新增一节：铁律 1 之前的「查表 → 派首选 → (基础设施失败) 逐级回落 → 再
    派发」步 + 显式写「gate 判定不认谁生产的」解耦声明 + 「候选回落 ≠ 状态机 retry」「gate FAIL
    绝不换候选」两条不变量 + `cli: native` 是弱缓解、自动化天花板是「主 Agent 机械横传 model」的说明
- **P4b — 跨 CLI 子进程**（design-note §2.4/§2.6，research §1/§2/§4/§6）
  - 子进程 spawn：`claude -p --model X --dangerously-skip-permissions` /
    `opencode run -m provider/model#variant --auto` /
    `codex exec -m X --dangerously-bypass-approvals-and-sandbox`（三平台本会话均实测跑通；flag 名
    落地前逐平台对最新官方文档复核，research §10）
  - 结构化输出解析判成败：Claude Code `--output-format json`（`stop_reason` / `modelUsage`）、
    Codex `--json`（`turn.completed` vs `turn.failed`——**退出码对 Codex 不可靠必须解析事件流**）、
    OpenCode `--format json`（`step_finish.part.reason`）+ 空返回判定
  - D2 假完成校验集成——「跑了但无 gate 能评产出」映射为回落理由码 `no_parseable_output`，
    「有产出」则交 gate、不回落；`SETUP.md` 各 CLI 自动化环境 flag 小节
  - **routed-away judge 的 verdict 校验**（P1 先核实是不是真缺口）：P6.5 judge 若路由到 codex/opencode
    子进程，其 transcript 落 `~/.codex/sessions/` 等非 `~/.claude/` 位置——`check-judge-verdict.py`
    的 verdict 定位 + 信息隔离黑/白名单扫描（TAG0033 DEBT0038 同款机制）是否认得跨平台产出的
    verdict。真缺口则纳入本任务补上（P4b 或单列子批）
  - `cli: codex` 子进程的存活检测走 **TAG0033 已合并的 `CodexAdapter`**（`ADAPTERS["codex"]`，v0.70.0）；
    claude-code/opencode 子进程走既有适配器 + 子进程形式的 `wait(pid)` / `kill -0`（research §6.0.2）
  - 评审打回续跑（design-note §2.4a）：同 target 优先平台官方续接（`--resume` / `codex exec resume` /
    `opencode -s` / native 的 `followup_task` / `task_id`），失败或换 target 则全新派发——**续接失败
    无客观信号是已知缺口**，按「续接优先、重起兜底」处理，不假装解决
- **P4c — tmux 观测层**（design-note §3，本会话 WSL2+tmux3.4 含真人 attach 全链路实测）
  —— 用户 2026-09-09：能做就做，维持低优先、可整体切除（不通过不影响 P4a/P4b）
  - wrapper：`which tmux` 成功则 `tmux new-session -d -s {agate-task-phase-ts} '{命令} | tee {capture}'`
    （人看 pane、脚本 tail 文件）；失败裸跑
  - session 命名带命名空间；生命周期 = wrapper 自带退出倒计时（N 默认 ~15 可配）→ 自然结束；
    `list-clients` 非空则不强杀、让倒计时收尾；兜底 `N + 余量` 强杀
  - 明确不做：`send-keys` / `capture-pane` 解析给主 Agent / 跨轮复用
  - **目标环境 tmux 版本验证若与任务环境不同则停在「定稿 + 待落地验证」、不阻塞 P8**（外部评审 W2）
- **测试**：`agate/tests/` 新增 pytest——schema 校验（`tier`/`effort` 两轴、`tier`vs`candidates`
  二选一、`(phase,role)` key）/ 档位→候选链展开 + `effort` 各平台映射（Claude Code 静默忽略）/
  `(phase,role)`→`phase`→`standard` 解析顺序 / 三层配置优先级 + 全兜底（缺失/损坏 → 出厂默认 =
  现状）/ try-and-fall 逐级回落（各基础设施失败形态：起不来 / auth 错 / 429 / 空产出）/
  **回落非 retry**（回落不动 `retries`、不写 `state_transition`）/ **`gate_fail` 非法理由码被校验器拒** /
  **gate FAIL 不触发换候选**（关键完整性用例）/ `dispatch_route` 事件 + check-events / `cli: native`
  各平台 / 子进程 spawn + 结构化输出解析 / tmux wrapper 生命周期；BDD 以 P1 定稿为准（计划 ≥22 条）；
  **回归证明 gate / 状态机 / `phases.yaml` 结构零改动 + 「不配置 = 逐字节现状」**
- **design-note 修订**（本任务交付物之一，非 out-of-scope）：`design-dispatch-routing.md` 头部
  「做什么」+ §2.1/§2.2 按本 P0-brief 讨论定案重写——① 三层落点（配置文件不在 `agate/rules/`）；
  ② 核心循环去掉「按序探测」改 try-and-fall（查表 → 派首选 → 基础设施失败逐级回落 → 默认派发）；
  ③ `tier` + `effort` 两正交轴 + `(phase,role)` key；④ `cli: native` 明确标为弱缓解、跨 CLI 为强
  缓解 + 自动化不对称说明；⑤ 「候选回落 ≠ retry」「gate FAIL 绝不换候选」两条完整性不变量；
  ⑥ routing 是 per-machine 机会式、不追求跨机可复现。头部「机制现状一句话」同步。随 P1/P2 定稿
  同步，走 docs commit（非 SELF-GATE，但属协议配套设计文档）；`roadmap.md` RM-AG0060 长描述里的
  旧 `rules/dispatch-routing.yaml` 措辞一并回写

### out-of-scope

- **Codex 接入**（CodexAdapter + platform-notes Codex 章 + SETUP Codex）——RM-AG0061 / TAG0033 **已完成合并（v0.70.0，2026-09-09）**，本任务直接消费不重做
- 主 Agent 按任务内容动态选型（design-note §2.2 边界，与局限 3 同构，明确排除）
- 会话续接的「软信号」根治（design-note §2.4a 已如实登记为缺口，本任务按「续接优先、重起兜底」处理）
- 第三方终端工具（Herdr/Claude Squad）作为依赖；DSH 纳入 CLI 派发路径（design-note §2.5，能力现状
  不满足前提）
- 局限 3「主 Agent 自身缺乏外部约束」（design-note §7 事项 10，超出本设计，另行立项）
- RM-AG0055 命令流机制/阈值本身（复用不改）；RM-AG0054 `agate next`/`agate advance` 本身（同家族
  但不同性质决策）
- **派发前空探测（probe-then-commit）**——2026-09-09 讨论定案改 try-and-fall，不做 probe / probe 缓存
- **routing 的跨机器/团队可复现**——明确 per-machine 机会式，只有抽象 `(phase,role)`→档位映射可 commit
  共享，档位→具体模型的绑定就是「本机实际能跑什么」，别的机器复现不了不是缺陷
- **retry 时故意换/升档模型**——retry 重新机械查表，不做「上次失败所以这次换更强的」的逻辑

## known_risks

- "同类/影响面预判（gate 解耦是设计前提）：本任务**不改** `check-gate.py` / `check-state-transition.py` /
  `phases.yaml` / 状态机——回归测试必须证明这一点；`dispatch-protocol.md` 新节须显式写『gate 不认谁
  生产的』防未来有人误以为要为跨 CLI 派发定制 gate"
- "同类/影响面预判（`agate-dispatch.py` 是 RM-AG0054 已落地的推进侧 CLI 家族成员）：扩展它加路由决策
  不得破坏既有 dispatch-context 渲染路径（`generated_by: agate-dispatch.py + 主 Agent`）；派发决策
  命令是**新增**，不是 RM-AG0054 的 `agate next`/`advance`——两者性质不同（推进决策 vs 派发决策），
  归同一家族但命令须新增"
- "同类/影响面预判（`check-events.py` 哈希链）：新增 `dispatch_route` 事件类型须让 check-events 认它、
  不判为非法未知 event；复用既有哈希链完整性校验不新造机制"
- "SELF-GATE：改 `agate/dispatch-protocol.md` + `agate/scripts/agate-dispatch.py`（+ 可能
  `check-events.py` 扩展 / 新增校验器）+ `agate/SETUP.md` + **`agate/rules/` 下新增档位词表文件**
  （或 `phases.yaml` 扩字段）+ `agate/tests/` → 触发，commit message 须含 `self-gate-review:` 或
  `self-gate-skip:`；`agate-workspace/dispatch-routing.yaml`（项目级配置）+ 机器级档位绑定文件
  （`~/.config/agate/` 类）新增**不触发** SELF-GATE（非协议本体，同 `maintainability.yaml`）"
- "证据强度（外部评审 B1/B2 教训）：本会话对三平台『按次指定 model 生效』是 `[实测]`；Codex
  `spawn_agent` schema 原为 `[自述]`——**TAG0033 P6 已补成直接实测**（`platform-notes.md` Codex 章
  为准）；仅剩 OpenCode bug② 机制推断未直接复现，P1 前置核实须补成直接实测，P1/P2 表述不得把
  `[自述]`/推断混同为『已实测』"
- "**模型购物完整性洞（最高危）**：gate 解耦（`gate 不认谁生产的`）使『换模型试到出 green』成为
  可能。不变量：候选回落只在 `launch_fail`/`infra_error`/`no_parseable_output` 时发生，**收到任何
  gate 能评的产出即停止回落**、gate FAIL 走正常阶段 retry（同一候选）不换候选。`dispatch_route`
  理由码枚举无 `gate_fail` 值、由 `check-events.py` 机械强制；须有专门回归用例（gate FAIL 后
  `dispatch_route` 事件计数不增）"
- "`cli: native` 是弱缓解（诚实标注，防过度宣称）：同厂商换 model 盲区基本共享，只有跨 CLI（换厂商）
  才是局限 2 想要的异源独立视角。且 `cli: native` 原理上做不到『不依赖主 Agent』——天花板是主 Agent
  读文件机械横传 model。design-note / dispatch-protocol.md 须把弱形/强形、自动化不对称写清"
- "`effort` 轴在 Claude Code CLI 基本是空的：`claude -p` 无干净推理档旋钮 → 该平台 `effort` 静默
  忽略。P2 须确认『声明了 effort 但目标平台不支持』不报错、只 `platform-notes.md` 注明"
- "`cli: native` on OpenCode 的间接路复杂度：要 dispatch 表 phase→预配命名 agent 的映射 + 预注册
  机制，比 Claude Code/Codex 的直接传参多一层——P2 评审须确认这层不失控"
- "跨 CLI flag 名版本漂移：本会话验证基于 Claude Code 2.1.263 / codex-cli 0.153.4 / opencode 1.18.11
  ——`--dangerously-*` 系列 / `-s` / `--auto` / `--variant` / `--format` 落地前照 research §10 逐平台
  对最新官方文档复核"
- "tmux 实测环境代表性（外部评审 W2）：本会话是 WSL2 + tmux 3.4（非容器/CI/物理机）——P4c 目标
  环境须在其自己的 tmux 版本上复跑 research §10 的验证项"
- "机会式启用（局限 6 张力）：不配置候选 = 行为与现状逐字节一致；配了但 CLI 未装/未认证 = 首次派发
  即基础设施失败、自动逐级回落——回归测试须证明『不启用 = 现状』。**档位/effort 两轴 + `(phase,role)`
  key 加了间接层**（`standard` 语义必须钉死为『继承主 Agent 当前 model 的原生派发』，否则出厂默认全
  `standard` ≠ 现状、破坏该不变量）；三层配置的解析优先级与合并语义 P2 须明确写死，避免『机器级
  绑定与项目级映射冲突时取谁』含糊"
- "配置落点是 design-note 现存缺口（用户 2026-09-09 指出）：§2.1 把文件放 `agate/rules/` 又说『非
  协议本体』矛盾。P1 须先定三层落点再据此写 schema——落点没定死就进 P2 会导致 schema / 校验器 /
  SETUP scaffold 三处返工"
- "多提交阶段命中 DEBT0037（TAG0033 复盘新登记）：本任务 `dispatch_plan` = static-batch P4a/P4b/P4c
  分批 commit，`check-gate.py P4` 的完整度判据（暂存区有非 md/yaml 文件）在『某批已 commit、暂存区
  空』时 exit 1、`agate-next.py` 拒绝推进 → 需主 Agent 手动 `_advance` + 补 `state_transition` 事件
  （TAG0033 P4→P5 两次即如此）。P2 排期时预留这个手动步；若 DEBT0037 在本任务启动前已修复则直接受益"
- "TAG0033 F1 类缺陷预防（DEBT0035 教训）：P4b 子进程结构化输出解析（Codex `--json` 判成败）的 P1
  spike / P2 minimal_validation 必须**主动构造** `turn.failed` / item `status:failed` / 空返回 /
  非 0 退出各终态的真实样本，不能只读已有会话——TAG0033 正是漏采 `status:failed` 终态、P6 真机才发现"

## env_constraints

- 本任务改 `agate/dispatch-protocol.md` + `agate/scripts/agate-dispatch.py`（+ 可能新增校验器 /
  `check-events.py` 扩展）+ `agate/SETUP.md` + `agate/rules/` 下档位词表文件（或 `phases.yaml`
  扩字段）+ `agate/tests/` → **触发 SELF-GATE**（commit message `self-gate-review:` /
  `self-gate-skip:`）；`agate-workspace/dispatch-routing.yaml` + 机器级档位绑定文件新增不触发
- P4b `cli: codex` 子进程的存活检测依赖 **TAG0033（已合并 v0.70.0，2026-09-09）的 `CodexAdapter`**——依赖已满足，P4b codex 部分无排期阻塞
- 真机验证需要 Claude Code / OpenCode / Codex 三 CLI 已装已认证（本机具备）
- 用系统 python 跑 pytest/pyyaml；ruff 用 `~/.venvs/agate-dev/bin/ruff`；基线用 `--strict-errors-only`
- 派发类工具用 `~/.agate` 稳定版，不用 worktree 相对路径（TAG0016 教训）

## executor_env

- worktree：`.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`），构建流程见
  `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0034.md` 按模板全 9 节填写
