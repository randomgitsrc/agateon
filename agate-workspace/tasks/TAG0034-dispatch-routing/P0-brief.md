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
全兜底、非协议本体、不受 SELF-GATE），按 phase 声明候选 `{cli, model, effort?}` 路由（或引用命名
**档位**——见 scope 待确认「配置分层与落点」「档位（tier）抽象」两项）：主 Agent 到某阶段时**查表 → 按序探测「通不通」→
派发到第一个可用候选 → 候选全不可用则逐级回落（终点恒为同平台同 model 的默认派发）**；`cli` 可为
`native`（同平台换 model，不脱离原生派发工具）或另一个 CLI（`claude-code`/`codex`/`opencode`，起
子进程）。协议本体（`agate/rules/` 或 `phases.yaml` 旁）只放**档位词表 + 语义 + 出厂默认**（全阶段
= `standard` ≡ 现状）；档位→具体 `{cli,model,effort}` 的绑定是**机器/安装级**、随 SETUP 流程 scaffold。
查表/探测/降级是纯机械步骤、落在 CLI 里（优先扩 `agate-dispatch.py`），主 Agent / 档位 C 只调用。
新增 `dispatch_route` 事件无差别留痕。子进程形式若有 `tmux` 则包一层供人 `attach` 观测（wrapper
自带退出倒计时）。**gate / 状态机 / `phases.yaml` 全不动**——gate 只认产出文件和 exit code、不认
『谁生产的』，这条解耦是设计成立的前提。存活/卡死检测复用 RM-AG0055 命令流机制（+ 子进程形式的
`wait(pid)` / `kill -0`），不自造超时。动机 = 给角色隔离补模型维度、部分缓解 `LIMITATIONS.md`
局限 2（同源模型系统性盲区，现状 ADR-006 无解）。"

### scope

P2 声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial（依赖链，不并行）}`。

- **P1/P2 必须先定掉的设计类待确认**（design-note §7 事项 1-5 + 本次新增两项）
  - **配置分层与落点**（design-note §2.1 现把文件放 `rules/` 且写「非协议本体」自相矛盾——`agate/rules/`
    就是协议本体；P1 须重写 §2.1 + 头部「做什么」并在本任务交付该 design-note 修订）。三层：
    ① **协议本体**（`agate/rules/` 或 `phases.yaml` 旁）——档位词表 + 每档语义画像 + 出厂默认
    phase→档位映射（全 `standard`），改它走 SELF-GATE（改「什么是 premium」本就该评审）；
    ② **机器/安装级**——档位→有序候选链 `[{cli,model,effort}]` 的具体绑定（「本机 premium =
    codex/gpt-5.6-terra 再 claude-code/opus」），依赖「装了哪些 CLI + 哪个账号 + 该账号能用哪些
    model」，落 `~/.config/agate/` 或 `~/.agate` 同级**非版本控制**路径，由 SETUP 流程（比照
    「步骤 2-Codex」的 per-platform onboarding）scaffold 出带注释的初始模板（探测本机已装 CLI +
    各自默认 model）；③ **项目级**（`agate-workspace/dispatch-routing.yaml`）——phase→档位映射
    + per-phase 直接值覆盖，只引用档位名故跨机器可移植。**MVP 可合并①③为单文件 + 内联档位定义**
    （对齐 `maintainability.yaml`），是否真拆出机器级档位文件由 P2 按「团队/多机可移植性是否真需求」定。
    全兜底：文件缺失/损坏/类型坏 → 出厂默认（= 现状），不报错不静默跳过（复用
    `check-maintainability.py:_load_config` 模式）
  - **档位（tier）抽象**（用户 2026-09-09：类比 Anthropic `haiku/sonnet/opus`、OpenAI `luna/terra/sol`）：
    协议定义一组命名档位（提议 `bulk / standard / deep / reasoning`，或 `basic/standard/plus/pro`——
    名字 P1 定），语义画像写进协议文档（`bulk`=高吞吐低成本产出量大 / `standard`=**恒等于继承主
    Agent 当前 model 的原生派发、保「不配置=逐字节现状」不变量** / `deep`=高能力复杂判断 /
    `reasoning`=显式深度推理档）。配置里 phase 可写 `tier: deep`（引用，可移植）**或**
    `candidates: [{cli,model,effort}]`（直接值，跳过档位间接层，牺牲可移植换明确）——静态校验器
    两种写法都要认。`effort` 字段自然归档位定义（`reasoning` → `effort: high`）。档位→候选是一条
    有序跨 CLI 链，逐级回落逻辑不变
  - `agate-workspace/dispatch-routing.yaml` / 档位文件的确切 schema（已定：无 `fallback` 字段、终点
    回落恒为默认派发、需 `effort?` 字段；待定：字段名、`{cli: native, model: null}` 是否合法、
    档位块与 phase 块的分隔形式）+ 静态校验器落点（新增校验器，非 `agate/rules/schema` 下的协议 schema）
  - `dispatch_route` 事件 JSON schema + `check-events.py` 如何识别新事件类型（不能把未知 event 判为非法）
  - 决策 CLI 落点（**优先扩 `agate-dispatch.py`**，不成再新增 `agate-route.py`）；`cli: native` 形式
    "决策层算出目标 model → 启动仍由驱动会话代发平台派发工具"的衔接方式（会话侧读什么文件、怎么
    保证零判断）；与 RM-AG0054 已落地的 `agate dispatch`（渲染 dispatch-context）是串联还是同一步
  - 探测缓存（同候选一个 task 内只探一次）+ `cli: native` 探测方式（倾向「查平台已知 alias 表 /
    接受配置、让首次真派发失败时走降级」，不起一次性子代理探测）
  - 与既有派发机制的交互：① 五模式并行批（模式 2/3）——每个并行 subagent 是否各自独立探测、结果
    task 内是否共享；② RM-AG0055 自主再派发的子任务——是否走路由表（倾向「不走，继承父的实际
    cli/model」）；③ 单 Agent 模式（`has_task_tool:false`）——路由为 no-op，显式声明出范围
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
  - `agate-dispatch.py` 扩展：读表（解析档位引用 → 展开为候选链）→ 按序探测（发极简请求判硬故障，
    **只判「通不通」、不掺任务内容语义**——落地对探测逻辑做显式约束）→ 选 target → 逐级回落 →
    写 `dispatch_route` 事件
  - `dispatch_route` 事件：`gate-events.jsonl` 写入端 + `check-events.py` 校验端（复用既有哈希链）
  - `cli: native` 执行：Claude Code（Task 单次调用传 `model`，本会话实测生效）+ OpenCode（命名
    subagent 配置 `agents.<name>.model` 间接路——需定义 dispatch 表 phase→预配命名 agent 的映射与
    预注册机制；本会话实测 v1.18.11 生效，旧 bug ①③ 不存在）
  - `dispatch-protocol.md` 新增一节：铁律 1 之前的「查表 → 探测 → 定 target → 再派发」步 + 显式
    写「gate 判定不认谁生产的」解耦声明
- **P4b — 跨 CLI 子进程**（design-note §2.4/§2.6，research §1/§2/§4/§6）
  - 子进程 spawn：`claude -p --model X --dangerously-skip-permissions` /
    `opencode run -m provider/model#variant --auto` /
    `codex exec -m X --dangerously-bypass-approvals-and-sandbox`（三平台本会话均实测跑通；flag 名
    落地前逐平台对最新官方文档复核，research §10）
  - 结构化输出解析判成败：Claude Code `--output-format json`（`stop_reason` / `modelUsage`）、
    Codex `--json`（`turn.completed` vs `turn.failed`——**退出码对 Codex 不可靠必须解析事件流**）、
    OpenCode `--format json`（`step_finish.part.reason`）+ 空返回判定
  - D2 假完成校验集成；`SETUP.md` 各 CLI 自动化环境 flag 小节
  - `cli: codex` 子进程的存活检测走 **TAG0033 已合并的 `CodexAdapter`**（`ADAPTERS["codex"]`，v0.70.0）；
    claude-code/opencode 子进程走既有适配器 + 子进程形式的 `wait(pid)` / `kill -0`（research §6.0.2）
  - 评审打回续跑（design-note §2.4a）：同 target 优先平台官方续接（`--resume` / `codex exec resume` /
    `opencode -s` / native 的 `followup_task` / `task_id`），失败或换 target 则全新派发——**续接失败
    无客观信号是已知缺口**，按「续接优先、重起兜底」处理，不假装解决
- **P4c — tmux 观测层**（design-note §3，本会话 WSL2+tmux3.4 含真人 attach 全链路实测）
  - wrapper：`which tmux` 成功则 `tmux new-session -d -s {agate-task-phase-ts} '{命令} | tee {capture}'`
    （人看 pane、脚本 tail 文件）；失败裸跑
  - session 命名带命名空间；生命周期 = wrapper 自带退出倒计时（N 默认 ~15 可配）→ 自然结束；
    `list-clients` 非空则不强杀、让倒计时收尾；兜底 `N + 余量` 强杀
  - 明确不做：`send-keys` / `capture-pane` 解析给主 Agent / 跨轮复用
  - **目标环境 tmux 版本验证若与任务环境不同则停在「定稿 + 待落地验证」、不阻塞 P8**（外部评审 W2）
- **测试**：`agate/tests/` 新增 pytest——schema 校验（含档位引用 + 直接值两种写法）/ 档位→候选链
  展开 / 三层配置解析优先级 + 全兜底（缺失/损坏 → 出厂默认 = 现状）/ 探测（各平台失败形态）/
  逐级回落 / `dispatch_route` 事件 + check-events / `cli: native` 各平台 / 子进程 spawn + 结构化
  输出解析 / tmux wrapper 生命周期；BDD 以 P1 定稿为准（计划 ≥20 条）；**回归证明 gate / 状态机 /
  `phases.yaml` 结构零改动 + 「不配置 = 逐字节现状」**
- **design-note 修订**（本任务交付物之一，非 out-of-scope）：`design-dispatch-routing.md` §2.1 +
  头部「做什么」按本 P0-brief 的三层落点 + 档位抽象重写（现文本把配置文件放 `rules/` 且称「非协议
  本体」自相矛盾）；随 P1/P2 定稿同步，走 docs commit（非 SELF-GATE，但属协议配套设计文档）

### out-of-scope

- **Codex 接入**（CodexAdapter + platform-notes Codex 章 + SETUP Codex）——RM-AG0061 / TAG0033 **已完成合并（v0.70.0，2026-09-09）**，本任务直接消费不重做
- 主 Agent 按任务内容动态选型（design-note §2.2 边界，与局限 3 同构，明确排除）
- 会话续接的「软信号」根治（design-note §2.4a 已如实登记为缺口，本任务按「续接优先、重起兜底」处理）
- 第三方终端工具（Herdr/Claude Squad）作为依赖；DSH 纳入 CLI 派发路径（design-note §2.5，能力现状
  不满足前提）
- 局限 3「主 Agent 自身缺乏外部约束」（design-note §7 事项 10，超出本设计，另行立项）
- RM-AG0055 命令流机制/阈值本身（复用不改）；RM-AG0054 `agate next`/`agate advance` 本身（同家族
  但不同性质决策）

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
- "探测成本：无 task 内缓存则 P1-P8 × 每 phase 多候选 = 每任务几十次真 API 调用——P2 必须定探测缓存策略"
- "`cli: native` on OpenCode 的间接路复杂度：要 dispatch 表 phase→预配命名 agent 的映射 + 预注册
  机制，比 Claude Code/Codex 的直接传参多一层——P2 评审须确认这层不失控"
- "跨 CLI flag 名版本漂移：本会话验证基于 Claude Code 2.1.263 / codex-cli 0.153.4 / opencode 1.18.11
  ——`--dangerously-*` 系列 / `-s` / `--auto` / `--variant` / `--format` 落地前照 research §10 逐平台
  对最新官方文档复核"
- "tmux 实测环境代表性（外部评审 W2）：本会话是 WSL2 + tmux 3.4（非容器/CI/物理机）——P4c 目标
  环境须在其自己的 tmux 版本上复跑 research §10 的验证项"
- "机会式启用（局限 6 张力）：不配置候选 = 行为与现状逐字节一致；配了但 CLI 未装/未认证 = 探测失败
  自动回落——回归测试须证明『不启用 = 现状』。**档位抽象加了一层间接**（`standard` 语义必须钉死为
  『继承主 Agent 当前 model 的原生派发』，否则出厂默认全 `standard` ≠ 现状、破坏该不变量）；三层
  配置的解析优先级与合并语义 P2 须明确写死，避免『机器级绑定与项目级映射冲突时取谁』含糊"
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
