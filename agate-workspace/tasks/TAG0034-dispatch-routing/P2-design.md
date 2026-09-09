---
phase: P2
task_id: TAG0034
type: design
parent: P1-requirements.md
trace_id: TAG0034-P2-20260909
status: draft
created: 2026-09-09
agent: architect
candidate_count: 2
packages: [agate-scripts, agate-rules, agate-docs, agate-tests]
domains: [backend, cli]
ui_affected: false
dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [{id: P4a, complexity: high}, {id: P4b, complexity: medium}, {id: P4c, complexity: low}], serial: true}
---

# P2 方案设计 — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）

> parent：`P1-requirements.md`（approved，53 条 BDD + §3 同类扫描 9 组 + §5 六条已采纳 SUGGEST + §6 minimal_validation 要求 + §7 裁剪 / DEBT0037 / DEBT0039）
> 设计依据：`docs/design-notes/design-dispatch-routing.md`（§2.1/§2.2 + 头部为本任务待修订交付物，冲突以 P0-brief 2026-09-09 定案为准）
> 机制事实：`docs/research/cross-platform-dispatch-mechanics.md`（A1-A19 实测 + §10 复核清单）
> 本文在 P1 既定基线上做**方案取舍与结构设计 + 三平台最小验证**，六条已采纳 SUGGEST 作既定前提（见 §0）。

`[PROD_NOT_TOUCHED]`

`[BASELINE_CHANGE: BDD-10 — 用户 2026-09-09 批准，effort 按能力探测映射到 Claude Code --effort，详见 P1-requirements.md BDD-10 及 §3.4 / §5 MV10]`

---

## §0 既定前提（六条已采纳 SUGGEST，按其设计、不推翻）

| # | 已采纳 SUGGEST | 本方案落法 |
|---|---|---|
| 1 | `tier` 三档 = `bulk` / `standard` / `deep` | §3.2 档位词表；语义画像 bulk=高吞吐低成本产出量大 / standard=**恒等于继承主 Agent 当前 model 的原生派发**（不变量锚）/ deep=高能力复杂判断 |
| 2 | `{cli: native, model: null}` 合法，`null` = 该 CLI 当前默认 model | §3.6 schema：`model` 允许 `null`；决策层 native 形式遇 `null` 不传 `--model`，由平台取默认 |
| 3 | MVP 单文件合并 + 机器级②是否拆出由 P2 判定 | **本方案判定：MVP 不拆机器级②**（候选方案 A，§2）。①（协议本体档位词表）落 `agate/rules/dispatch-tiers.yaml`（G 硬约束「档位词表放 `agate/rules/` 下新文件」）；②③合并落 `agate-workspace/dispatch-routing.yaml`（`tier_bindings:` + `routes:` 两顶层 key）。判据与结论见 §2 |
| 4 | 三层优先级序 = 项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认；机器级同名档位键后写覆盖先写 | §3.3 `resolve(phase, role)` 算法（BDD-15/18「P2 定」留白已定死） |
| 5 | 决策落点扩 `agate-dispatch.py` 新增子命令 `agate dispatch route <phase> <role>`，与 RM-AG0054 `agate dispatch`（渲染 dispatch-context）**串联为两步、不合并**；不新增 `agate-route.py` | §3.5 决策 CLI 衔接 |
| 6 | routing schema 静态校验器 = 新增独立脚本 `agate/scripts/check-dispatch-routing.py`，不入 `agate/rules/schema`；挂载时机 P2 定 | §3.6；挂载 = SELF-GATE 链（`protocol-alignment-review` 前置手动跑）+ 可选 pre-commit（见 §7 SELF-GATE 面） |

---

## §1 影响面梳理（写在候选方案之前）

> 基于 P1 §3 同类扫描 9 组逐级细化到候选方案级。证据 = grep 命中清单 + 读过的消费方代码 + 既有 gate 脚本校验口径（见 §5 minimal_validation MV8、§6 files_to_read）。

### 1.1 改什么（Modify）

| # | 文件 / 落点（到函数 / 小节） | 改动点 | 关联 BDD | package |
|---|---|---|---|---|
| M1 | `agate/rules/dispatch-tiers.yaml`（**新文件**） | 顶层 `tiers:`（bulk/standard/deep 定义 + 语义画像）+ `defaults:`（出厂 `(phase,role)`→tier 映射，**全 `standard`**，MVP 可为空 map ⇒ 隐式全 standard） | BDD-7/13/14 | agate-rules |
| M2 | `agate-workspace/dispatch-routing.yaml`（**新文件**，随本任务提交一份最小示例 / scaffold；`.gitignore` 不忽略，对齐 `maintainability.yaml`） | 顶层 `tier_bindings:`（tier→有序跨 CLI 候选链 `[{cli,model,effort?}]`，本机现状为准）+ `routes:`（`(phase,role)`→ `{tier, effort?}` 引用 **或** `{candidates: [...]}` 直接值） | BDD-1~6/7~13/15~18 | agate-workspace（非 package，非 SELF-GATE） |
| M3 | `agate/scripts/check-dispatch-routing.py`（**新文件**） | routing schema 静态校验器：`cli` 枚举 `{native, claude-code, codex, opencode}`、`effort` 枚举 `{low, medium, high}`、`tier`/`candidates` 互斥、`(phase,role)` key 形态、`fallback` 字段非法、`model: null` 放行、`tier_bindings` 同名键 WARNING | BDD-1~6 | agate-scripts |
| M4 | `agate/scripts/agate-dispatch.py` | **新增子命令 `route`**（`argv[1] == "route"` 分支，或 `main()` 顶层 dispatch）：`resolve(phase, role)` → 展开候选链 → try-and-fall 逐级回落 → 写 `dispatch_route` 事件 → stdout 输出解析后的 target 描述（JSON）。**既有渲染路径（无 `route` 子命令时）逐字节不动**——`_render_dispatch_context` / `_next_card_content` / CARD-SOURCE 锚点 / `generated_by: agate-dispatch.py + 主 Agent` 不改 | BDD-19~28/31~36/43~45/51 | agate-scripts |
| M5 | `agate/scripts/agate-dispatch.py`（同文件，可拆 helper 模块 `agate-dispatch-route.py` 被 import——落地 P4a 定，不影响 schema） | 子进程 spawn + 结构化输出解析（Claude Code `--output-format json` / Codex `--json` / OpenCode `--format json`）+ 存活检测衔接（复用 `agate-cmdstream-adapters.py` 的 `ADAPTERS`，`cli: codex` 用 `CodexAdapter`） | BDD-33~36/42 | agate-scripts |
| M6 | `agate/scripts/check-events.py` | **追加审计链（第 8 条）**：识别 `event == "dispatch_route"` → 校验 `candidates_tried[].reason ∈ {launch_fail, infra_error, no_parseable_output}`，出现 `gate_fail`（或任何非三值）→ exit 1。**不动第 1-7 条既有链、不动哈希链算法、不动 GENESIS/ts/judge 计数** | BDD-27/29/30 | agate-scripts |
| M7 | `agate/dispatch-protocol.md`「派发编排机制」节区域（line 502 起） | **新增子节**「派发路由（查表 → 派首选 → 逐级回落 → 再派发）」，位于**铁律 1 之前**语义顺序上（正文放派发编排机制节内、明确「此步在铁律 1 启动 subagent 之前插入」）。含：① try-and-fall 步骤；② 「gate 判定只认产出文件 + exit code，不认谁生产的」显式声明；③ 「候选回落 ≠ 状态机 retry」「gate FAIL 绝不换候选」两条完整性不变量；④ `cli: native` 弱缓解 / 跨 CLI 强缓解 + 自动化不对称说明；⑤ 单 Agent 模式（`has_task_tool:false`）路由 no-op 声明；⑥ **DEBT0039 边界措辞**（§4.3 草稿②） | BDD-19/24~28/41/45/49 | agate-docs |
| M8 | `agate/assets/execution-roles/architect.md`「批次设计（强制节，TAG0014）」节（line 209 起） | **DEBT0039 边界措辞**（§4.3 草稿①）：补一句「补协议文档正文 = P4 实现工作、批次执行阶段标 P4；P7 只做跨文件一致性验证、不 author 文档内容」+ 两先例指针（TAG0030 / TAG0033 复盘） | BDD-48 | agate-docs |
| M9 | `agate/SETUP.md` | 新增小节「步骤 2-dispatch-routing：机器级档位绑定 scaffold」（比照「步骤 2-Codex」per-platform onboarding 形态）：说明 `agate-workspace/dispatch-routing.yaml` 的 `tier_bindings:` 由本机现状填（探测已装 CLI + 各自默认 model），能用就用、不能用不强制；各 CLI 自动化环境绕过 flag（`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check` / `--auto`）小节 | BDD-33~36（flag 落地） | agate-docs |
| M10 | `agate/platform-notes.md` | ① Claude Code 章 effort 注明如实写：`--effort` flag —— 2.1.266 [实测] 有 / 2.1.263 [实测] 无 / 引入版本未核实；路由按 `claude --help` 能力探测映射，无该 flag 的版本静默忽略不报错；② 三平台「结构化输出判成败字段」小节（`stop_reason` / `turn.completed` vs `turn.failed` + item 级两层 / `step_finish.part.reason`）——素材即 §5 MV1~MV7 | BDD-8/9/10/33~36 | agate-docs |
| M11 | `agate/tests/`（新增 pytest 文件若干，unit 为主 + 1 组回归） | schema 校验 / 档位展开 + effort 映射 / 解析顺序 / 三层优先级 + 全兜底 / try-and-fall 各失败形态 / 回落非 retry / `gate_fail` 非法理由码被拒 / **gate FAIL 不触发换候选（关键完整性用例）** / `dispatch_route` + check-events / cli:native 各平台（可 mock 平台层）/ 子进程 spawn + 结构化输出解析（fixture 用 §5 真机样本收敛）/ tmux wrapper 生命周期 / **回归：`phases.yaml` / `check-gate.py` / `check-state-transition.py` / 状态机结构零改动 + 「不配置 = 逐字节现状」**。**必含 3 条（评审补）**：**T1** `resolve` 每条分支返回对象键集固定为 `{form, chain, model, effort}`、`form ∈ {'default','chain'}`、`form=='default'` 时 `chain is None`（对应 N2）；**T2** try-and-fall 用例集补「模拟 `wait(pid)` 超时 / RM-AG0055 命令流阈值触发 kill → `outcome.kind=INFRA_ERROR`、回落 `infra_error`」（对应 N6）；**T3** `check-events.py` 第 8 条参数化用例——`launch_fail` / `infra_error` / `no_parseable_output` 三值各构造一条合法账本断言 exit 0 + 混入第四值（如 `gate_fail`）断言 exit 1 | BDD-1~53 全覆盖 | agate-tests |
| M12 | `docs/design-notes/design-dispatch-routing.md` + `agate-workspace/roadmap/roadmap.md` | design-note 头部 + §2.1/§2.2 按 2026-09-09 定案重写（§9 修订要点 6 项）；roadmap RM-AG0060 长描述旧措辞（`rules/dispatch-routing.yaml` / 「按序探测」/ `{cli,model}` 二元）回写。走 docs commit（非 SELF-GATE） | BDD-46/47/52/53 | agate-docs |

### 1.2 不改什么（Not Modify）— 边界（P4 implementer 判范围的依据，避免「顺手改进」）

| 文件 / 范围 | 看起来该改的理由 | 为什么不改 |
|---|---|---|
| `agate/rules/phases.yaml` **结构 + 字段** | 「该角色用什么 model」看似 phase 属性 | G 硬约束「不扩 `phases.yaml` 字段」。档位放 M1 新文件；`exec_role`（谁执行）与「用什么 model」是两个关注点，分别由 `phases.yaml` / dispatch-routing 承载。9 个消费方 + `check-structure-consistency.py` S-1/S-2 双向锚点不动（BDD-39） |
| `agate/scripts/check-gate.py` / `check-state-transition.py` | 跨 CLI 派发看似要「为异源产出定制 gate」 | **gate 解耦是设计前提**：gate 只认产出文件 + exit code、不认「谁生产的」。M7 新节写死这句防未来误改。BDD-39 断言逐字节不变 |
| 状态机（`state-machine.md` 结构化部分 / `retries[Pn]` / PAUSED / `state_transition` 语义） | 候选回落看似是一种 retry | **候选回落 ≠ 状态机 retry**（BDD-28）：回落只在基础设施失败时发生，不占 `retries[Pn]`、不写 `state_transition`、不触发 PAUSED，只写 1 条 `dispatch_route` |
| `check-events.py` 第 1-7 条既有审计链 + 哈希链算法（`sha256(上一行原始文本)` / GENESIS / ts 单调 / judge 计数） | 加新事件类型看似要动校验框架 | 只**追加**第 8 条理由码枚举校验（M6），既有链零改动。MV8 已实测现 `check-events.py` 对含 `dispatch_route` 的账本 exit 0（第 7 条未知 event 不拦），追加链只做「已知则严格校验理由码」 |
| `check-judge-verdict.py` / `check-p6-provenance.py` | routed-away judge 的 verdict 落非 `~/.claude/` 位置，看似 gate 认不出 | P1 §3 第 6 组 + P1-review 独立 grep 核实：两校验器纯 `TASK_DIR` 文件解析、不读平台 transcript。judge 路由到子进程时只要 verdict + 证据落 `TASK_DIR`（铁律 2/3 不变）即平台无关通过。BDD-42 作回归断言，**本任务零改动这两个脚本** |
| `agate-dispatch.py` 既有 dispatch-context 渲染路径（`_render_dispatch_context` / `_next_card_content` / CARD-SOURCE / `generated_by`） | 扩子命令看似会碰渲染逻辑 | `route` 子命令是**新增分支**，无 `route` 参数时行为逐字节不变。5 处消费方（`dispatch-context.md` 模板 / `check-p6-provenance.py` 审计 2 / `check-judge-verdict.py` `_strip_card` / 2 个 `test_tag0027_b2_*` 测试）零改动仍绿（BDD-39） |
| RM-AG0055 命令流机制 / 阈值 / `CommandRecord` IR / `agate-cmdstream-{detect,ir}.py` | 存活检测要接子进程 | **复用不改**：`cli: codex` 子进程走 `CodexAdapter`（TAG0033 已合并 v0.70.0，`ADAPTERS["codex"]`）；claude-code / opencode 走既有适配器 + 子进程形式的 `wait(pid)` / `kill -0`。检测引擎零改动 |
| RM-AG0054 `agate next` / `agate advance`（状态机推进决策） | 同 CLI 家族 | 派发决策命令是**新增**（`agate dispatch route`），与推进决策性质不同，串联不合并（SUGGEST #5） |
| `agate/rules/dispatch.yaml` | 五模式词表 / gate 表 | 不动。路由是铁律 1 之前插入的一步，不改五模式枚举 / gate 表 / `field_readers` |

### 1.3 风险在哪（Risk）— 每条配缓解

| # | 风险 | 缓解 |
|---|---|---|
| R1 | **模型购物完整性洞（最高危）**：gate 解耦使「换模型试到出 green」成为可能 | 三重机械强制：① `resolve` / try-and-fall 的回落**只**在 `launch_fail` / `infra_error` / `no_parseable_output` 三类信号触发，「收到任何 gate 能评产出即停止回落」写进 §3.7 循环（BDD-24/25）；② `dispatch_route` 理由码枚举**无 `gate_fail` 值**，`check-events.py` 第 8 条机械拒绝（M6，BDD-27）；③ gate FAIL → 同一候选正常阶段 retry，`dispatch_route` 事件计数不增（BDD-26），专门回归用例（M11） |
| R2 | 双源同步：`gate-events.jsonl` 写入端认了 `dispatch_route`，`check-events.py` 校验端没认 → 账本审计红（T005 同构） | M4（写入端）+ M6（校验端）同批（P4a）提交；BDD-30 断言既有 `test_check_events.py` 零改动仍绿；MV8 已验现状不拦 |
| R3 | 三层配置解析「取谁含糊」运行时分支 | §3.3 `resolve` 算法把 key 序 + tier 展开 + 同名键规则全定死（BDD-15/18「P2 定」留白已闭合），无运行时歧义分支；`check-dispatch-routing.py` 静态拦 `tier`/`candidates` 同现（BDD-2） |
| R4 | 「不配置 = 逐字节现状」不变量被 `standard` 语义漂移破坏（出厂默认全 `standard` ≠ 现状） | `standard` 档**不经 `tier_bindings` 展开**，硬编码 = 「继承主 Agent 当前 model + 原生派发」（§3.2 / §3.3 step 5，BDD-14/40）。回归用例：无任何配置文件跑完整 P1→P8，`dispatch_route` 事件条数 = 0（BDD-40，M11） |
| R5 | Codex 退出码不可靠 + 两层 status 混淆 → 误判整轮成败 → 错误回落 / 错误换候选 | §3.3 BDD-35 定死「turn 层为准」；MV3/MV4 真机样本佐证（本版 0.153.4 turn.failed→exit 1、item 级 status:failed→turn.completed→exit 0，退出码两向都不稳）；解析逻辑：`turn.completed` 存在且无 `turn.failed`/顶层 `error` → 成功；item 级 `status:"failed"` 永不触发回落 |
| R6 | `cli: native` on OpenCode 间接路复杂度失控（要 phase→预配命名 agent 映射 + 预注册机制） | §3.4：MVP 用「约定命名」——命名 agent 名 = `agate-route-{tier}`（如 `agate-route-deep`），SETUP scaffold 时按 `tier_bindings` 里出现的 OpenCode native 候选预注册；`routes:` 侧只引用 tier，决策层机械映射到 agent 名。无该命名 agent → 该候选判 `launch_fail` 回落（不阻断）。这层只在「用户显式配了 OpenCode native 候选」时才需要，默认路径不碰 |
| R7 | 跨 CLI flag 名版本漂移（本机 Claude Code 已 2.1.266，P0-brief 记 2.1.263） | §5 MV9 已按 research §10 逐平台对最新 `--help` 复核（结论：`--model` / `--output-format json` / `--dangerously-*` / `-m` / `--json` / `--skip-git-repo-check` / `-s`（session）/ `--auto` / `--variant` / `--format json` 全部仍有效、语义未变；**新增发现** Claude Code `--effort`，见文件顶部 `[BASELINE_CHANGE]` + §3.4）。M9/M10 落地时 P4b 再复跑一次（按能力探测、不硬编码版本号）|
| R8 | DEBT0037：P4a/P4b/P4c 分批 commit 命中 `check-gate.py P4` 完整度判据（暂存区空时 exit 1）→ `agate-next.py` 拒推进 | §4.2 已注明为**已知手动步**：主 Agent 手动 `_advance` + 补 `state_transition` 事件（TAG0033 P4→P5 ×2 先例）。排期预留。若 DEBT0037 在本任务推进前修复则直接受益 |
| R9 | SELF-GATE 面漏派 `protocol-alignment-review` | §7 SELF-GATE 面清单已列出触发文件；P4/P7 涉及 `agate/**` 的 commit 前主 Agent 须派 `protocol-alignment-review`（A1-A7），commit message 含 `self-gate-review:` / `self-gate-skip:` |
| R10 | tmux 目标环境代表性（本会话 WSL2 + tmux 3.4，非容器 / CI / 物理机，外部评审 W2） | P4c **可整体切除**：不通过不影响 P4a/P4b；目标环境须在其自己 tmux 版本复跑 research §10 验证项，停在「定稿 + 待落地验证」不阻塞 P8。MV11 本机已验生命周期 / `list-clients` / `kill-session` 不存在 session 的 exit 1 |
| R11 | 续接失败无客观信号（外部评审 W1） | 按「续接优先、重起兜底」处理（design-note §2.4a）：同 target 优先平台官方续接（`--resume` / `codex exec resume` / `opencode run -s`），失败或换 target 则全新派发；续接产出仍走假完成校验（D2）+ 本就在评审循环里。不假装解决，如实登记为缺口（§9 design-note 保留） |

---

## §2 候选方案（≥2 + 权衡 + 选择理由）

**场景类型判定**：系统架构（决策 CLI + 三层配置 + 事件账本 + 三平台子进程，数据流跨多个边界）+ 原型验证（minimal_validation 触发，三平台外部行为）。方法论：画数据流 → 找「取值含糊」瓶颈 → 针对配置分层设计替代拓扑；关键 P2 判断点 = **机器级档位绑定②是否拆出独立文件**（SUGGEST #3 明确留给 P2，判据「团队/多机可移植性是否真需求」）。两个候选就此轴展开。

### 候选方案 A（选中）— MVP 双文件：①协议本体 + ②③合并项目文件

- **①** `agate/rules/dispatch-tiers.yaml`（SELF-GATE）：`tiers:`（bulk/standard/deep 定义 + 语义画像）+ `defaults:`（出厂 `(phase,role)`→tier，全 standard / 空 map）。
- **②③** `agate-workspace/dispatch-routing.yaml`（**不** SELF-GATE，对齐 `maintainability.yaml`）：
  - `tier_bindings:`（机器级②）：`deep: [{cli: codex, model: gpt-5.6-terra, effort: high}, {cli: claude-code, model: opus}]` 之类，本机现状为准。
  - `routes:`（项目级③）：`{P2: {architect: {tier: deep}}, P4: {tier: bulk}}` 或 `{P6.5: {judge: {candidates: [{cli: codex, model: null}]}}}`。
- **决策层**：扩 `agate-dispatch.py` `route` 子命令（SUGGEST #5）。
- **schema 校验器**：新增 `check-dispatch-routing.py`（SUGGEST #6），校 `agate-workspace/dispatch-routing.yaml`（`tiers:` 引用一致性对 `dispatch-tiers.yaml` 交叉核）。
- **全兜底加载器**：逐字参考 `check-maintainability.py:_load_config`（文件不存在→出厂默认；yaml 不可导入→默认 + stderr；非 dict / 单键类型坏→该键默认 + stderr WARNING）。

**权衡**

| 维度 | 评价 |
|---|---|
| 优点 | ① 文件数最少（新增 2 个协议内 + 1 个项目内），全兜底加载器少一个；② SELF-GATE 边界清晰（`agate/rules/` 下 = SELF-GATE，`agate-workspace/` 下 = 否，与 H 硬约束逐字对齐）；③ `maintainability.yaml` 单项目文件先例可直接抄；④ 与「per-machine 机会式、不追求跨机可复现」（P0-brief out-of-scope）一致——`tier_bindings` 本就是本机现状，和 `routes` 放一起不损失任何可移植性 |
| 风险 | 若将来真出现「多机共享 `routes:` 但 `tier_bindings` 各机不同」的需求，需把 `tier_bindings:` 拆到 `~/.config/agate/`——但加载器已按「层」merge，拆分是机械重构，可延后（YAGNI） |
| 工作量 | 低-中：2 个新 YAML + 1 校验器 + 1 加载器；P4a 批 |

### 候选方案 B（未选）— 三文件全拆：①协议本体 + ②机器级独立 + ③项目级仅 routes

- **①** 同 A。
- **②** `~/.config/agate/dispatch-tier-bindings.yaml`（非版本控制，SETUP scaffold）：仅 `tier_bindings:`。
- **③** `agate-workspace/dispatch-routing.yaml`：仅 `routes:`（只引用 tier 名 → 跨机可 commit 共享）。

**权衡**

| 维度 | 评价 |
|---|---|
| 优点（B 在此轴上确实优于 A）| `routes:` 文件不含任何本机 model 串 → 可放心 commit 进项目、团队共享；`tier_bindings` 完全隔离在用户 home，换机器只需重跑 scaffold。若「团队统一 `(phase,role)`→档位策略、各人机器 model 不同」成为真需求，B 是直接答案 |
| 风险 | ① 多一个全兜底加载器 + 一个 `~/.config/agate/` 路径约定（跨平台 home 解析、Windows 无 `~/.config` 等）；② 三层优先级的「机器级绑定」层需要真的是独立文件、解析顺序多一跳；③ `routes:` 里若写 `candidates:` 直接值（BDD 允许）又把本机 model 串带回项目文件，B 的「可移植」优势只在「纯 tier 引用」时成立——收益条件苛刻；④ SETUP 复杂度上升（新增一个必跑 scaffold 步，与「零基础设施」张力） |
| 工作量 | 中：3 个 YAML + 2 加载器 + scaffold 逻辑 + 跨平台 home 解析 |

### 选择理由（A）

1. **判据「团队/多机可移植性是否真需求」→ 当前无消费方**。P0-brief 明确 out-of-scope「routing 的跨机器/团队可复现——per-machine 机会式」；design-note §9 修订要点也写「per-machine 机会式、不追求跨机可复现」。B 的唯一增益（可 commit 的 `routes:`）正是被 P0-brief 排除的目标，为它付三文件 + 两加载器 + scaffold 复杂度不划算（YAGNI）。
2. **A 的 SELF-GATE 边界与 H 硬约束逐字一致**：「`agate-workspace/dispatch-routing.yaml` + 机器级绑定文件新增不触发 SELF-GATE（非协议本体，同 `maintainability.yaml`）」——A 把②③都放 `agate-workspace/`，天然不触发；`agate/rules/dispatch-tiers.yaml`（①）触发，符合「改『什么是 deep』本就该评审」。
3. **A 可平滑升级到 B**：加载器按「层」合并（§3.3），将来把 `tier_bindings:` 段移到独立文件是纯机械重构，不改 `resolve` 算法、不改 schema、不破坏既有配置。先做窄的、留好扩展点。
4. **`maintainability.yaml` 先例**：项目级、全兜底、非协议本体、单文件——A 是它的同构复制，加载器逐字参考 `_load_config`，风险最低。

> `agate-route.py` 独立脚本方案已由 SUGGEST #5 排除（决策落点扩 `agate-dispatch.py`），不作候选。

---

## §3 设计详解（选中方案 A）

### 3.1 数据流

```
主 Agent 到阶段 Pn 派角色 R：
  step 1  agate dispatch <Pn> <R>            ← RM-AG0054 既有：渲染 Pn-dispatch-context-R.md（不变）
  step 2  agate dispatch route <Pn> <R>      ← 本任务新增：
            2.1 resolve(Pn, R) → tier / 直接候选链              （§3.3）
            2.2 展开为有序候选链 [{cli,model,effort?}, ...]     （§3.3 tier 展开）
            2.3 try-and-fall：逐候选派发 → 基础设施失败则回落   （§3.7）
            2.4 收到 gate 能评产出 → 停止；全落空 → 默认派发
            2.5 写 dispatch_route 事件（带理由码）              （§3.8）
            2.6 stdout 输出 target 描述 JSON:
                {"cli":..., "model":..., "effort":..., "form":"native|subprocess|default",
                 "dispatch_context": "<Pn-dispatch-context-R.md 路径>"}
  step 3  驱动会话按 target.form 落地：
            form=default / native → 会话按铁律 1 用平台派发工具启动 subagent，
                                     model 参数 = target.model（决策层已全量算好，会话零判断）
            form=subprocess       → step 2 内路由脚本已端到端 spawn（会话只收「路径 + 摘要」）
```

**「零判断」保证**：`cli: native` / `default` 形式下驱动会话唯一动作 = 把 `target.model`（决策层算好的字符串）传给平台派发工具。会话不读 `dispatch-routing.yaml`、不做 tier 展开、不选候选。会话侧读的文件只有 `agate dispatch route` 的 stdout JSON。

### 3.2 档位词表（`agate/rules/dispatch-tiers.yaml`，协议本体，SELF-GATE）

```yaml
schema_version: 1
tiers:
  bulk:
    intent: "高吞吐、低成本、产出量大；不要求顶尖智力（典型：P4 implementer）"
  standard:
    intent: "恒等于『继承主 Agent 当前 model 的原生派发』——保『不配置 = 逐字节现状』不变量。不经 tier_bindings 展开。"
  deep:
    intent: "高能力、复杂判断、专业视角（典型：P2 architect / P6.5 judge / P7 consistency-reviewer）"
defaults: {}      # 出厂 (phase,role)→tier 映射，空 map ⇒ 隐式全 standard ≡ 现状
```

- `standard` 是**语义锚**，不是一个「有 model 绑定」的档：决策层遇 `standard` 直接返回 `{form: default}`（§3.3 step 5）。`tier_bindings` 里定义 `standard` 属非法（`check-dispatch-routing.py` WARNING）。
- 改本文件（新增 tier / 改语义画像 / 改 `defaults`）→ SELF-GATE。

### 3.3 `resolve(phase, role)` 完整优先级解析算法（BDD-15 / BDD-18「P2 定」留白 —— 定死）

**四个来源，各自全兜底加载（`_load_config` 范式）**：

| 记号 | 来源 | 缺失 / 损坏兜底 |
|---|---|---|
| `FACTORY` | `agate/rules/dispatch-tiers.yaml` 的 `tiers:` + `defaults:` | 内建 `tiers={bulk,standard,deep}` + `defaults={}` |
| `ROUTES` | `agate-workspace/dispatch-routing.yaml` 的 `routes:` | `{}` |
| `BINDINGS` | 同文件的 `tier_bindings:` | `{}` |
| （机器级 default routing） | MVP **不实现**——`machine_routes:` 为**文档化保留字**（校验器 exit 0 放行、不作任何语义、恒空），预留未来扩展点 | `{}` |

**返回契约（统一，N2）**：`resolve` 恒返回单一对象 `{form, chain, model, effort}`：
- `form ∈ {'default', 'chain'}`。
- `form == 'default'` → `chain = None`、`model = <主 Agent 当前 model>`、`effort = None`（走默认派发，等价本机制未启用）。
- `form == 'chain'` → `chain = 有序 list[{cli, model, effort?}]`（每项 effort 已合并）、`model = None`、`effort = None`（逐候选的 model/effort 在 `chain` 内）。

**算法**（结果唯一，无运行时「取谁含糊」分支）：

```
resolve(phase, role):
  # ── 步骤 1：确定 tier 或直接候选链，按「项目级直接值 > 项目级档位映射 > 机器级绑定 > 出厂默认」──
  entry = ROUTES.get((phase, role))  or  ROUTES.get(phase)     # (phase,role) 命中优先于 phase（BDD-11/12）
  chain = entry.candidates if (entry and 'candidates' in entry) else None
  tier  = None ; effort_override = None
  if chain is not None:                                        # 【优先级 1】项目级直接值
      pass
  elif entry and 'tier' in entry:                              # 【优先级 2】项目级档位映射
      tier = entry.tier ; effort_override = entry.get('effort')
  else:                                                        # 【优先级 4】出厂默认（machine_routes 恒空 ⇒ 跳过优先级 3）
      tier = FACTORY.defaults.get((phase, role)) or FACTORY.defaults.get(phase) or 'standard'

  # ── 步骤 2：standard 短路（不变量锚，BDD-14）──
  if tier == 'standard':
      return {form: 'default', chain: None, model: <主 Agent 当前 model>, effort: None}

  # ── 步骤 3：tier → 有序跨 CLI 候选链（【优先级 3】机器级绑定 = 展开目标）──
  if chain is None:                                            # 来自 tier 引用
      chain = BINDINGS.get(tier)                               # 有序 list[{cli,model,effort?}] 或 None
      if not chain:                                            # 机器级未绑定该 tier
          return {form: 'default', chain: None, model: <主 Agent 当前 model>, effort: None}
                                                               # 回落默认派发（配了但本机没绑 = 机会式，BDD-16/17 精神）

  # ── 步骤 4：effort 合并（正交轴）──
  for c in chain:
      c.effort = c.get('effort') or effort_override            # 候选自带 effort 优先；否则用 route 层 effort
  return {form: 'chain', chain: chain, model: None, effort: None}   # 交 try-and-fall（§3.7）
```

**BDD-18 定死点 —— `tier_bindings:` 同名档位键取谁**：**后写覆盖先写**（last-write-wins）。理由：① SUGGEST #4 明文「机器级同名档位键后写覆盖先写」；② `yaml.safe_load` 对重复 mapping key 本就取最后一个 —— 与库行为一致，无需额外代码；③ 该文件非 SELF-GATE、非协议本体，全兜底原则下「配置问题 → 取一个确定值继续」优于「报错中断路由加载」。`check-dispatch-routing.py` 对重复 tier key 出 **WARNING**（不 exit 1），提示用户但不阻断。

**BDD-15 定死点 —— 四层优先级**：严格按上算法步骤 1 的分支顺序（项目级直接值 → 项目级档位映射 → 机器级绑定作为 tier 展开目标 → 出厂默认）。「机器级绑定」在 MVP 里不是一张与 `routes:` 竞争的路由表，而是 tier→候选链的**展开字典**（步骤 3）；`machine_routes:` 是**文档化保留字**（校验器 exit 0 放行、不作任何语义、恒空），故优先级 3 当前不产生独立取值路径。结果对任意 `(phase, role)` 唯一确定。

### 3.4 `cli: native` 各平台执行 + effort 映射

| 平台 | native 落法 | effort 映射（正交轴，BDD-8/9/10） |
|---|---|---|
| Claude Code | 决策层算出 `target.model`（`haiku` 等 alias 或全 ID），驱动会话按铁律 1 用平台派发工具单次调用传 `model`。`--output-format json` 的 `modelUsage` 字段可核实实际 model（MV1 实测 `modelUsage` key = `claude-haiku-4-5-20251001`，非父继承）。子进程形式：`claude -p --output-format json --model <M> --dangerously-skip-permissions <ctx路径>` | **按能力探测**（BDD-10 已走 `[BASELINE_CHANGE]`，用户 2026-09-09 批准）：路由决策层构造命令前探测 `claude --help` 是否含 `--effort`——含则映射 `--effort <e>`（`e ∈ {low,medium,high}`，schema 只放行三值；`--effort bogus` 实测只 Warning 不失败）；不含（旧版本）则省略 effort flag、不报错。**不硬编码版本号**——实测仅知本机 2.1.266 有、research 的 2.1.263 无，引入版本未核实 |
| Codex | 子进程 `codex exec --json -m <M> --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox`；native（`spawn_agent`）形式：`spawn_agent(model=<M>, reasoning_effort=<e>)` | `-c model_reasoning_effort=<e>`（子进程）/ `spawn_agent(reasoning_effort=<e>)`（native）。schema 三值 `{low,medium,high}` ⊂ Codex 支持集 `{low,medium,high,xhigh,max,ultra}` |
| OpenCode | native 无 model 参数 → 走**命名 subagent 间接路**（MVP 约定命名 `agate-route-{tier}`，见 R6）：被派 agent 的 `agents.<name>.model` = 候选 model。子进程形式：`opencode run --format json --auto -m <provider/model[#variant]> <ctx路径>` | `--variant <e>` 或 model 串 `#<e>` 后缀。MV7 实测：命名 subagent 跑其**配置 model**，不继承父会话切换后的 model（详见 §5 MV7 —— bug② 相关维度） |

### 3.5 决策 CLI 衔接（`agate dispatch` ↔ `agate dispatch route`，串联两步）

- **两步、不合并**（SUGGEST #5）：`agate dispatch <Pn> <R>` 仍只渲染 `Pn-dispatch-context-R.md`（RM-AG0054，`agate-dispatch.py` 既有逻辑逐字不动）；`agate dispatch route <Pn> <R>` 是新增子命令，读**已渲染好的** dispatch-context 路径 + `resolve` 结果 → 输出 target 描述。
- **实现落点**：`agate-dispatch.py` 的 `main()` 顶部加分支——`sys.argv[1] == "route"` 时进 `_route_main(phase, role)`；否则走既有渲染路径。`_route_main` 可 import 一个 helper（`agate-dispatch-route.py` 或内联函数集），P4a 落地时定，**不影响 schema / BDD**。
- **零判断衔接**：`agate dispatch route` 的 stdout = 单行 JSON `{"cli","model","effort","form","dispatch_context"}`。驱动会话读它、按 `form` 机械落地（§3.1 step 3）。`form: native` / `default` 时会话把 `model` 塞给平台派发工具即止；`form: subprocess` 时路由脚本已在 step 2 内 spawn 完毕，会话只接「路径 + 摘要」。

### 3.6 schema + 静态校验器（`check-dispatch-routing.py`，独立脚本，不入 `agate/rules/schema`）

**`agate-workspace/dispatch-routing.yaml` schema（校验器口径）**：

- 顶层 key：`tier_bindings`（可选，dict）/ `routes`（可选，dict）/ `machine_routes`（**文档化保留字**——校验器 exit 0 放行、不作任何语义校验，MVP 恒空）/ `schema_version`。其它多余顶层 key → WARNING。
- `routes` 条目 key 形态：`Pn`（phase 级）或 `Pn: {role: {...}}`（`(phase,role)` 级，role 段可选）（BDD-3）。
- 每条 route 值：**`tier:` 与 `candidates:` 互斥**，同时出现 → exit 1（BDD-2）。
- `tier:` 值 ∈ `dispatch-tiers.yaml` 的 `tiers:` key 集（交叉核）；未知 tier → exit 1。
- `candidates:` = 非空 list，每项 `{cli, model, effort?}`：
  - `cli` ∈ `{native, claude-code, codex, opencode}`，否则 exit 1（BDD-4）。
  - `model`：字符串 **或 `null`**（`null` = 该 CLI 默认，SUGGEST #2）——放行（BDD 无「model 必填」）。
  - `effort`（可选）∈ `{low, medium, high}`，否则 exit 1（BDD-5）。
- `effort:` 也可写在 route 层（与 `tier:` 并列），同枚举校验。
- **`fallback` 字段非法**：条目任意层出现 `fallback:` → exit 1（BDD-6；终点回落恒为默认派发，不可配、不需声明）。
- `tier_bindings` 条目：key ∈ tiers（不含 `standard` → WARNING），值 = 有序候选 list（同 `candidates` 项校验）；重复 key → WARNING（§3.3 last-write-wins）。
- 坏 YAML / 文件不存在 → 校验器 exit 0（无可校验对象，不阻断——与全兜底运行时一致）。

**挂载时机**（SUGGEST #6 留 P2 定）：① **SELF-GATE 链**——改 `agate/**`（含 `dispatch-tiers.yaml`）的 commit 前，主 Agent 派 `protocol-alignment-review` 时一并跑 `check-dispatch-routing.py agate-workspace/dispatch-routing.yaml`；② **可选 pre-commit**——用户可自行把它加进本地 pre-commit（非协议强制，因 `dispatch-routing.yaml` 非协议本体）；③ **本任务 P5**——以 `gate_commands.P5_routing_schema` 对本任务提交的 scaffold 跑一次冒烟校验（见 §8）。**不作为 `dispatch-routing.yaml` 后续任意编辑的常驻 gate**（非协议本体，同 `maintainability.yaml`——用户后续改该文件不受协议 gate 治理）；BDD-1~6 的完整合法 / 非法 fixture 覆盖在 §1 M11 pytest 内，`P5_routing_schema` 只对提交的 scaffold 做 presence 级冒烟。

### 3.7 try-and-fall 逐级回落循环（无 probe，§3.1 step 2.3-2.4）

```
r = resolve(phase, role)
if r.form == 'default':                                  # resolve 返回 form=default → 直接默认派发，无循环
    return DEFAULT_DISPATCH                              # （不写 dispatch_route 事件——未启用路由，BDD-40）
chain = r.chain
tried = []
for cand in chain:                                       # 按声明顺序，无 probe（BDD-19：第一个动作即派真实 ctx）
    outcome = dispatch_once(cand, dispatch_context_path) # native 形式：由会话代发；subprocess：脚本 spawn
    if outcome.kind == LAUNCH_FAIL:                       # CLI 未装 / 可执行缺失 / spawn OSError
        tried.append({**cand, result: "failed", reason: "launch_fail"}); continue          # BDD-20
    if outcome.kind == INFRA_ERROR:                       # 401 循环 / 网络不可达 / 429 / 进程中途崩溃 / turn.failed / 顶层 error JSON
                                                          #   / 挂死被杀：RM-AG0055 命令流阈值 或 wait(pid) 超时 或 kill -0 探测失活 → 触发 kill
        tried.append({**cand, result: "failed", reason: "infra_error"}); continue          # BDD-21
    if outcome.kind == NO_PARSEABLE_OUTPUT:               # 进程正常退出/工具返回，但 D2 假完成校验不过：
                                                          #   约定产出文件缺失或空 / 结构化输出空返回（无 text part / 无 agent_message）
        tried.append({**cand, result: "failed", reason: "no_parseable_output"}); continue  # BDD-22
    # outcome.kind == HAS_OUTPUT：产出了 gate 能评的东西（产出文件非空、格式合法）
    tried.append({**cand, result: "success"})
    write_dispatch_route_event(phase, tried, final=cand)  # BDD-25：收到即停，交 gate，不再试后续候选
    return cand
# 候选链耗尽 —— 全部三类基础设施理由码失败
write_dispatch_route_event(phase, tried, final={"cli": "default"})   # BDD-23
return DEFAULT_DISPATCH                                   # 同平台同 model，恒等于本机制未启用
```

**回落信号边界（R1 / BDD-24）**：`outcome.kind` 只可能是上述四值。**产出质量差 / 内容不完整** 归 `HAS_OUTPUT`（只要文件非空、格式合法）——**不回落**，交 gate；gate 判 FAIL 是正常阶段 retry（同一候选，`dispatch_route` 事件不新增，BDD-26）。`gate_fail` 不是 `outcome.kind` 的取值、不进 `tried[].reason`。

**`HAS_OUTPUT` 的「格式合法」定死（N7，R1 侧门风险）**：「格式合法」= 产出文件可解析为期望的 md/yaml 骨架（**presence 级**：frontmatter 可解析、必需锚点标题存在），**不含**内容完整度 / BDD 覆盖度 / 质量判断。后者一律 gate 负责、走同候选 retry（BDD-26）。实现**不得**把结构完整度校验塞进 `NO_PARSEABLE_OUTPUT` 分支——`NO_PARSEABLE_OUTPUT` 只判「产出文件缺失或空 / 结构化输出空返回（无 text part / 无 agent_message）」，一旦文件存在且 frontmatter + 必需锚点可解析即 `HAS_OUTPUT`。

**挂死 / 无退出（N6）**：进程挂死、结构化事件永不到来、`wait(pid)` 超时、`kill -0` / `/proc` 探测失活、或 RM-AG0055 命令流阈值（调用冻结 / 活动冻结 / 逻辑空转）触发 → 路由脚本 kill 该子进程 / 中止该 native 调用 → `outcome.kind = INFRA_ERROR`、`reason: infra_error` 回落。与 BDD-21「进程中途崩溃」并列，补齐「挂死被杀」即穷尽 `INFRA_ERROR` 形态。**不用固定紧超时**：`wait` 超时值须匹配任务预期、宁宽勿紧（命令超时兜底层级 4）。

**结构化输出 → `outcome.kind` 判定表**（素材 §5 MV1~MV6）：

| 平台 | HAS_OUTPUT（成功，停回落） | INFRA_ERROR（回落） | NO_PARSEABLE_OUTPUT（回落） |
|---|---|---|---|
| Claude Code | `stop_reason == "end_turn"` + `result` 非空 + 产出文件非空且骨架可解析 | 启动即报未登录 / API error status / 挂死被杀（N6） | `stop_reason != "end_turn"` / `result` 空 / 产出文件缺失或空 |
| Codex | 事件流含 `{"type":"turn.completed"}` 且**无** `{"type":"turn.failed"}` / 无顶层 `{"type":"error"}` + 产出文件非空且骨架可解析 | `{"type":"turn.failed"}` 或顶层 `{"type":"error","status":...}`（MV3）/ 挂死被杀（N6） | 有 `turn.completed` 但无任何 `agent_message` text / 产出文件缺失或空 |
| OpenCode | `step_finish` 且 `part.reason == "stop"` + 有 `text` part + 产出文件非空且骨架可解析 | 顶层 `{"type":"error", "error":{"name":"ProviderAuthError"...}}`（MV6a）/ 挂死被杀（N6） | 无 `step_finish` / 无 `text` part（空返回）/ `{"type":"error","name":"UnknownError"}`（MV6b）/ 产出文件缺失或空 |

> **Codex 两层 status（BDD-35，§3.3 已定死「turn 层为准」）**：item 级 `payload.item.status == "failed"`（携 `exit_code`，MV4）= agent 内部跑的某条 shell 命令非 0 退出，**不改变** `outcome.kind`——只要整轮 `turn.completed`，即 `HAS_OUTPUT`。退出码本身**仅弱佐证**（MV3 本版 turn.failed → exit 1，研究记 auth 循环 → exit 0，两向都不稳）：判定以事件流为准，退出码非 0 但有 `turn.completed` + 产出文件非空 → 仍 `HAS_OUTPUT`。

### 3.8 `dispatch_route` 事件 + `check-events.py` 扩展（M6）

**事件 JSON**（与既有 `gate_run` / `state_transition` / `judge_verdict` 同构，复用 `append_event` 哈希链）：

```json
{"event":"dispatch_route","phase":"P4","task_id":"TAG0034",
 "candidates_tried":[
   {"cli":"codex","model":"gpt-5.6-terra","effort":"high","result":"failed","reason":"infra_error"},
   {"cli":"native","model":"haiku","result":"success"}],
 "final":{"cli":"native","model":"haiku"},
 "prev_hash":"<sha256(上一行原始文本)>","ts":"<UTC ISO8601 微秒>"}
```

- `prev_hash` / `ts` 由 `append_event` 既有逻辑填（BDD-29：`check-events.py` 第 3-5 条哈希链 / ts 单调不受影响；MV8 已验现状 exit 0）。
- 候选回落**不写 `state_transition`、不动 `retries`**（BDD-28）。
- 全候选落空：`final = {"cli":"default"}`，`candidates_tried` 保留每个失败理由码（BDD-23）。

**`check-events.py` 追加第 8 条审计链**（M6，**不动第 1-7 条 + 哈希链算法**）：

```
8. dispatch_route 理由码枚举：对 event == "dispatch_route" 的行，
   每个 candidates_tried[i].reason 必须 ∈ {"launch_fail", "infra_error", "no_parseable_output"}；
   出现 "gate_fail" 或任何其它值 → exit 1（BDD-27）。
   合法三值 / 无 dispatch_route 事件 → 不影响判定（BDD-30：既有 test_check_events.py 零改动仍绿）。
```

实现：在既有逐行循环内，`if ev.get("event") == "dispatch_route":` 分支加 reason 集合校验，`sys.exit(1)` 走既有错误出口格式。第 7 条注释「gate_run/judge_verdict/state_transition 为已知类型」补 `dispatch_route`。

### 3.9 与既有派发机制的交互

| BDD | 场景 | 设计 |
|---|---|---|
| BDD-43 | 五模式并行批（模式 3） | 每个并行 subagent 各自独立跑 `agate dispatch route <Pn> <R>` —— `resolve` 是纯函数、无跨调用状态；同 role 的并行分片 `(phase,role)` 相同 → 解析到同一条链；不同 role 各按自己 `(phase,role)` 解析 |
| BDD-44 | RM-AG0055 自主再派发的子任务 | **不走路由表**：子任务由执行角色在授权范围内自主起，不调 `agate dispatch route`、继承父的实际 cli/model；**不产生 `dispatch_route` 事件**。`dispatch-protocol.md`「subagent 自主再派发」既有约束不变 |
| BDD-45 | 单 Agent 模式（`executor_env.has_task_tool: false`） | 无派发动作 → 路由 no-op；M7 新节 + design-note §9 显式写「单 Agent 模式下路由不适用（出范围）」 |
| BDD-26 vs BDD-51 | 两类 retry 的路由行为 | **同阶段 gate-FAIL retry**（BDD-26）：不重跑 `agate dispatch route`，用上次成功的同一候选重跑，`dispatch_route` 事件计数不增。**P5→P4 跨阶段回退后的 P4 retry**（BDD-51）：主 Agent 重新跑一次 `agate dispatch route P4 <R>`（机械重解析、按当时候选可用性落候选，可能与回退前不同），**不注入**「上次失败→升档/换更强 model」逻辑。两者不冲突：前者是「同阶段内、已有成功候选」，后者是「跨阶段回退、重新进入 P4」。实现层面：`agate dispatch route` 无状态、每次调用独立解析；「是否重新调用」由主 Agent 按 retry 类型决定（同阶段 retry 不调、跨阶段回退调），协议在 M7 新节写明 |

### 3.10 tmux 观测层（P4c，低优先、可整体切除，不通过不影响 P4a/P4b）

- **包裹判定**（BDD-37）：子进程形式派发前 `which tmux`——成功 → `tmux new-session -d -s <ns> '<cmd> | tee <capture>'`（人看 pane、路由脚本 `tail -f <capture>` 取结构化流）；失败 → 裸跑子进程。两路径的 `dispatch_route` 留痕 + gate 结果逐字节一致。
- **session 命名带命名空间**：`agate-{task_id}-{phase}-{短时间戳}`（MV11 已验本机存在别的 session，裸名会碰撞）。所有 `list-clients` / `kill-session` 带 `-t <session>` 精确定位。
- **生命周期 + 退出倒计时**（BDD-38）：wrapper 命令末尾自带收尾脚本——跑完打 `=== 派发结束 ===` + N 秒倒计时（`N` 默认 **15**，可配），倒计时完 wrapper 自退 → session 自然结束（MV11 已验）。路由脚本清理：`tmux list-clients -t <session>` 空 → 直接 `kill-session`（跳倒计时）；非空（有人 attach）→ 不强杀，让倒计时收尾。
- **BDD-38「N + 余量」定值 —— 余量 = 10 秒**（P1 建议 ≥10s，取下界）。即：wrapper 异常未退出（倒计时脚本本身挂了）且路由脚本在 **`N + 10s`**（默认 25s）后仍见 session 存在 → 兜底 `kill-session` 强杀。理由：10s 覆盖倒计时脚本 jitter + tmux teardown 延迟，又足够短使卡死 session 不久留；MV11 实测 `kill-session` 对已消失 session → exit 1，故清理逻辑先 `tmux has-session -t <session>` 判断 / 容忍 exit 1。
- **明确不做**：`send-keys` / `capture-pane` 内容解析给主 Agent / 跨轮 session 复用。
- **目标环境代表性**（R10 / 外部评审 W2）：本会话实测环境 = WSL2 + tmux 3.4（非容器 / CI / 物理机）。目标部署环境须在其自己的 tmux 版本复跑 research §10 验证项；不通过 → 停在「定稿 + 待落地验证」、不阻塞 P8。

---

## §4 批次设计（强制节，TAG0014）

### 4.1 dispatch_plan（frontmatter 机器字段）

frontmatter 实际写单行 flow YAML（见文件头 `dispatch_plan:` 行）；此处按等价 block 形态展开便于阅读：

```yaml
dispatch_plan:
  mode: static-batch
  parallel_limit: 3
  batches:
    - id: P4a
      complexity: high
    - id: P4b
      complexity: medium
    - id: P4c
      complexity: low
  serial: true
```

> **`serial: true` 说明（N4）**：`mode: static-batch` + `batches: [P4a, P4b, P4c]` 是 P1 §7 / P0-brief scope 明文钉死的目标值，逐字承接。`serial: true` **非 `_gate_p2_dispatch_plan` 契约键**（gate 只校验 `mode` / `parallel_limit` / `batches` 每批 `id`+`complexity` / 批数 ≤ `parallel_limit`），其强制力落在下方「批次边界对齐」串行依赖散文 + 主 Agent 排期。若未来 `dispatch_plan` 契约新增 `serial` 语义，本任务应同步。

**前置检查项**（拆批之前先过）：

- [x] **影响面梳理已完成**：§1（改什么 12 项 / 不改什么 8 项 / 风险 11 条），批次边界建立其上。
- [x] **批次边界对齐 §1 文件分组，同一文件不跨批改两轮**：`agate-dispatch.py` 的 `route` 子命令核心（M4）在 P4a、子进程 spawn + 结构化解析（M5）在 P4b —— 同文件两批，**故 P4a→P4b 串行依赖**（`serial: true`），非并行；`dispatch-protocol.md` 只 P4a 动一次（M7，含 DEBT0039 措辞②）；`check-events.py` 只 P4a 动一次（M6）。跨批共享件：`agate-dispatch.py`（P4a 建 `route` 骨架 + JSON 输出契约 → P4b 在其上加 subprocess 分支）、target 描述 JSON schema（P4a 定、P4b/P4c 消费）—— 由主 Agent 在 P4a 返回后固化，P4b/P4c 只增不改。
- [x] **P4a 同批不拆 + 内部实现顺序（N3）**：P1 §7 / P0-brief scope 明文钉死 `batches: [P4a, P4b, P4c]`，**不拆成 P4a-1/P4a-2**（会偏离 P1 既定值）。P4a 内含两层——**schema 层** = M1（词表 `dispatch-tiers.yaml`）/ M3（校验器 `check-dispatch-routing.py`）/ M2（`dispatch-routing.yaml` scaffold）；**引擎层** = M4（`route` 核心 `resolve` + try-and-fall）/ M6（`check-events.py` 第 8 条）/ M7（`dispatch-protocol.md` 协议正文）。依赖 M1→M3、M1→M4、M4→M6，schema 层无反向依赖 → **P4a 内部实现顺序 = 先 schema 层、后引擎层**；implementer 交付 schema 层即可跑 `P5_routing_schema` 冒烟。**同批不拆的依据**：三层配置 schema 与 `resolve` / `dispatch_route` 事件 schema 是**同一份数据契约的两面**，跨批会拆出契约漂移风险；R1 完整性用例锚定的是 M4+M6 的**联合行为**，须与二者同批落地。
- [x] **资源密集型批次已判定**：P4a/P4b 的 gate 命令 = `python3 -m pytest agate/tests/`（单元测试类，非 xdist 全量 / 非 E2E / 非构建），非资源密集型；但因**同文件依赖链**仍判**串行**（`serial: true` / P4a→P4b→P4c）。
- [x] **长命令 timeout 已声明**：见 §8 `gate_commands`（`{key}_timeout_seconds`）。

**批次内容**：

| 批 | 复杂度 | 内容 | 产出文件（≤3 类核心 + 测试 + 文档随批） | 依赖 |
|---|---|---|---|---|
| **P4a** | **high** | 配置路由核心 + `cli: native` + `dispatch_route` 事件 + 协议本体档位词表 + `dispatch-protocol.md` 新节 | **内部两段顺序（N3）**：**① schema 层** `agate/rules/dispatch-tiers.yaml`（新）→ `agate/scripts/check-dispatch-routing.py`（新）→ `agate-workspace/dispatch-routing.yaml`（新 scaffold）；**② 引擎层** `agate/scripts/agate-dispatch.py`（`route` 子命令 + `resolve` + try-and-fall 骨架 + `cli:native` + 默认派发）→ `agate/scripts/check-events.py`（第 8 条）→ `agate/dispatch-protocol.md`（新节 + DEBT0039 措辞②）；两段各带对应 pytest。**完整性不变量（R1）= M4+M6 联合行为，本批落地——评审强度按高危** | 无（首批） |
| **P4b** | medium | 跨 CLI 子进程 + 结构化输出解析 + routed-away judge 核实 + 评审打回续跑 | `agate/scripts/agate-dispatch.py`（subprocess 分支 + 三平台结构化输出解析 + `CodexAdapter` 存活衔接 + 续接优先/重起兜底）、`agate/SETUP.md`（步骤 2-dispatch-routing）、`agate/platform-notes.md`（结构化输出字段 + effort 注明）、对应 pytest（fixture 用 §5 真机样本收敛）、BDD-42 回归断言 | P4a（同 `agate-dispatch.py`，用 P4a 的 `route` 骨架 + JSON 契约） |
| **P4c** | low | tmux 观测层 | tmux wrapper（`agate-dispatch.py` 内 helper 或独立 sh）、`dispatch-protocol.md` §tmux 小节（若 M7 未含）、对应 pytest（wrapper 生命周期，可 mock tmux）| P4b（包裹的是子进程形式派发）；**可整体切除** |

> **DEBT0039 边界（本任务据此把 P4 文档批标 P4，不标 P7）**：M7（`dispatch-protocol.md` 新节）+ M8（`architect.md` 批次设计节措辞）+ M9（`SETUP.md`）+ M10（`platform-notes.md`）+ M12（design-note / roadmap）都是**补 / 改协议文档正文 = P4 author 工作**，随对应批在 P4 提交、批次执行阶段标 P4。**P7 只做跨文件一致性验证**（`dispatch-protocol.md` / `agate-dispatch.py` / `check-events.py` / `dispatch-tiers.yaml` / `SETUP.md` / `platform-notes.md` / `architect.md` / design-note / roadmap 之间措辞、字段、引用是否对齐），**不 author 文档内容**。先例：TAG0030（doc-assertion 审计 P3 写红、正文 P4 补绿）、TAG0033 复盘（protocol-docs 批被 architect 误标 P7、主 Agent 比照 TAG0030 拉回 P4）。

### 4.2 DEBT0037 已知手动步（排期预留）

`dispatch_plan` = static-batch 多提交阶段：P4a/P4b/P4c 分批 commit 后，某批已 commit、暂存区空时 `check-gate.py P4` 完整度判据（暂存区有非 md/yaml 文件）exit 1 → `agate-next.py` 查 P4 `retreat`（null）→ 拒推进。**需主 Agent 手动 `_advance`（改 `.state.yaml` phase + `append_event` state_transition 事件）**（TAG0033 P4→P5 ×2 先例）。P4b/P4c 之间、P4c→P5 均可能命中。若 DEBT0037 在本任务推进前修复则直接受益。

### 4.3 DEBT0039 两处边界措辞草稿（P4 照此落地，随对应批提交）

**草稿① —— `agate/assets/execution-roles/architect.md`「批次设计（强制节，TAG0014）」节内新增一段**：

> **补协议文档正文 = P4，不是 P7**：`dispatch_plan` 批次表的「执行阶段」标注里，补写 / 修订协议文档正文（`platform-notes.md` / `SETUP.md` / `dispatch-protocol.md` / phase-cards 等的新增章节、措辞修订、per-platform 说明）属 **P4 实现工作**——随对应批次在 P4 提交、批次执行阶段标 **P4**。**P7 一致性检查只做跨文件一致性验证**（各文档、脚本、schema 之间的措辞 / 字段 / 引用是否对齐、有无矛盾），**不 author 文档内容**、不新增或改写正文。architect 设计批次表时不得把「补文档正文」批标成 P7。先例：TAG0030（doc-assertion 审计测试 P3 写红、正文 P4 补绿）、TAG0033 复盘（protocol-docs 批被 architect 误标 P7、主 Agent 比照 TAG0030 拉回 P4，避免带 by-design 红推进）。

**草稿② —— `agate/dispatch-protocol.md`「派发编排机制」节内新增一句区分**：

> **author 文档内容 vs 跨文件一致性验证的阶段边界**：`dispatch_plan` 批次表里，「补 / 改协议文档正文」（新增章节、修订既有措辞、补 per-platform 说明）是 **P4 author 工作**，标 P4、随批提交；**P7 只验证跨文件一致性**（多个文档 / 脚本 / schema 间的措辞与引用是否对齐、有无矛盾），P7 **不** author、不改写文档正文。architect 设计批次表时不得把「补文档正文」批标成 P7。

**边界约束**：只做这两处措辞澄清，不扩到其它 DEBT、不改任何脚本 / gate 逻辑。consistency 回归 → BDD-50。P8 收尾：DEBT0039 置 `status: closed`、`task_id: null → TAG0034`。

### 4.4 SELF-GATE 文件面梳理（供 P4/P7 commit 规划，H 硬约束）

**触发 SELF-GATE（`protocol-alignment-review`，A1-A7，phases: pre-commit，insert_after P7）——P4/P7 涉及以下文件的 commit 前，主 Agent 须派 `protocol-alignment-review`，commit message 含 `self-gate-review:` 路径 / `self-gate-skip:` 理由**：

- `agate/dispatch-protocol.md`（M7）
- `agate/scripts/agate-dispatch.py`（M4/M5）
- `agate/scripts/check-events.py`（M6）
- `agate/scripts/check-dispatch-routing.py`（M3，新）
- `agate/rules/dispatch-tiers.yaml`（M1，新 —— 档位词表，协议本体）
- `agate/SETUP.md`（M9）
- `agate/platform-notes.md`（M10）
- `agate/assets/execution-roles/architect.md`（M8，DEBT0039 措辞）
- `agate/tests/**`（M11）

**不触发 SELF-GATE**（非协议本体，同 `maintainability.yaml`）：

- `agate-workspace/dispatch-routing.yaml`（M2，项目级配置）
- （若未来拆出）机器级档位绑定文件（`~/.config/agate/` 类）
- `docs/design-notes/design-dispatch-routing.md` + `agate-workspace/roadmap/roadmap.md`（M12，走 docs commit）

---

## §5 minimal_validation（真机结果，非声明）

> `requires_minimal_validation: true`（P1 §6）。本方案重度依赖三平台外部行为，**不接受「纯代码逻辑」声明**。以下样本均 2026-09-09 本机真机构造（Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4，均已认证），命令加 shell `timeout`，逐条 progress 落盘。样本文件在 scratchpad `mv/`，关键结论回引本节。

```yaml
minimal_validation:
  - id: MV1
    assumption: "Claude Code cli:native 传 model 生效，modelUsage 字段可核实实际 model（BDD-31/33）"
    method: "timeout 120s claude -p --output-format json --model haiku --dangerously-skip-permissions <<< 'Reply ok'"
    result: confirmed
    note: "[实测] exit 0；stop_reason=end_turn；modelUsage 唯一 key = claude-haiku-4-5-20251001（非父会话继承 model）；result='ok'。BDD-31 判据锚定成立"
  - id: MV2
    assumption: "Codex 正常派发终态 = turn.completed（BDD-34）"
    method: "timeout 180s codex exec --json -m gpt-5.6-terra --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< 'Reply ok'"
    result: confirmed
    note: "[实测] exit 0；事件流末尾 {\"type\":\"turn.completed\",\"usage\":{...}}；agent_message item text='ok'。无 turn.failed"
  - id: MV3
    assumption: "Codex exit-0-但-turn.failed 失败样本（不支持的 model）——退出码不可靠、必须解析 --json（BDD-34）"
    method: "timeout 120s codex exec --json -m gpt-5（及 -m totally-bogus-xyz）--skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< 'Reply ok'"
    result: confirmed
    note: "[实测] 事件流：item.completed{item.type:error,'Model metadata ... not found'} → {\"type\":\"error\",\"status\":400,...} → {\"type\":\"turn.failed\",\"error\":{...}}。本版 codex-cli 0.153.4 进程 exit=1（研究报告记『auth 循环场景 may exit 0』）——即退出码在不同失败形态/版本间不稳定，故路由判成败必须解析事件流（turn.failed / 顶层 error），退出码仅弱佐证。映射 infra_error 回落"
  - id: MV4
    assumption: "Codex item 级 status:'failed'（带 exit_code）与 turn.failed 是两层，取哪层判定（BDD-35）"
    method: "timeout 240s codex exec --json -m gpt-5.6-terra ... <<< \"Run: sh -c 'exit 3'  then reply 'done'\""
    result: confirmed
    note: "[实测] exit 0；item.completed{item.type:command_execution, status:'failed', exit_code:3} 出现在事件流中间；整轮末尾 {\"type\":\"turn.completed\"}，agent 回复 'done'。=> **P2 定死：turn 层为准**。turn.completed 存在且无 turn.failed → 该次派发成功、交 gate、停止回落；item 级 status:'failed'（agent 内部某条 shell 命令非 0 退出）**永不触发换候选**（与 BDD-24『产出质量非回落信号』一致）。与『退出码不可靠』叠加：以事件流的 turn 层信号为准，退出码非 0 但有 turn.completed + 产出文件非空 → 仍判成功"
  - id: MV5
    assumption: "OpenCode 正常派发终态 = step_finish.part.reason == 'stop'（BDD-36）"
    method: "timeout 150s opencode run --format json --auto -m deepseek/deepseek-v4-flash <<< 'Reply ok'"
    result: confirmed
    note: "[实测] exit 0；JSONL: step_start / text(part.text='ok') / step_finish(part.reason='stop')"
  - id: MV6
    assumption: "OpenCode 失效 provider 空返回 / 结构化 Error 样本（BDD-36 回落）"
    method: "timeout 150s opencode run --format json --auto <<< 'Reply ok'（默认 minimax-cn）；及 -m deepseek/deepseek-chat（坏 id）"
    result: confirmed
    note: "[实测] 两者均 exit 1、单行 {\"type\":\"error\",\"error\":{\"name\":\"ProviderAuthError\"/\"UnknownError\",...}}、**无 step_finish、无 text part**。=> 判失败信号 = 缺 step_finish/reason=stop 或 缺 text part（空返回）或 顶层 type:error。ProviderAuthError→infra_error；纯空返回（无 error 事件也无 text）→ no_parseable_output"
  - id: MV7
    assumption: "OpenCode 旧 bug②：父会话切 model 后，命名 subagent 跑配置 model 还是父的新 model（P1 前置真机核实项，外部评审 B2）"
    method: "① 建临时命名 agent agate-child-pro（.opencode/agents/，mode:subagent, model:deepseek/deepseek-v4-pro，测后已删）；② opencode run -m deepseek/deepseek-v4-pro 起会话取 SID；③ opencode run -s <SID> -m deepseek/deepseek-v4-flash（同会话切 model 为 flash）+ task 派 subagent_type=agate-child-pro 令其报告自身 model"
    result: confirmed
    note: "[实测] 子代理回报 `deepseek/deepseek-v4-pro`（其**配置 model**），非父会话切换后的 flash。=> 命名 subagent 的 model 由 agents.<name>.model 决定，不继承父会话（切换后的）session model —— OpenCode cli:native 走命名 subagent 间接路对本用途可行、bug② 不影响。**如实标注**：`opencode run -s <id> -m <model>` 是**程序化 session model 覆盖**（resume 时改 session model），非交互式 TUI `/model` 切换；两者机制同（都改 session model、不改 agent 配置里的 model），故『交互式切换后子代理仍跑配置 model』这一维度为 [实测机制一致 + 交互式路径推断]，非逐字复现交互式 TUI 操作。research §5.2 / §10 的机制推理与本实测结论一致"
  - id: MV8
    assumption: "现 check-events.py 对含 dispatch_route 的账本不误判为非法未知 event（BDD-30 基线）"
    method: "构造 2 行合法哈希链账本（state_transition + dispatch_route，理由码 launch_fail），跑 python3 agate/scripts/check-events.py <dir>"
    result: confirmed
    note: "[实测] exit 0『账本审计通过（2 行，哈希链完整，ts 单调）』。=> 第 7 条『未知 event 不拦截』已保 BDD-30 基线；本任务新增的第 8 条理由码枚举校验（M6）是**追加**审计链，不动既有 1-7 条"
  - id: MV9
    assumption: "跨 CLI flag 名版本漂移复核（research §10；本机 Claude Code 已 2.1.266，P0-brief 记 2.1.263）"
    method: "claude --help / codex exec --help / opencode run --help 逐条对 §0 矩阵"
    result: confirmed
    note: "[实测] --model / --output-format json / --dangerously-skip-permissions（Claude Code）；-m / --json / --skip-git-repo-check / --dangerously-bypass-approvals-and-sandbox / -s sandbox / -c model_reasoning_effort（Codex）；-m / --format json / --variant / --auto / -s session / --fork（OpenCode）—— 全部仍有效、语义未变。版本：Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4"
  - id: MV10
    assumption: "effort 在 Claude Code CLI 静默忽略（BDD-10）"
    method: "claude --help | grep effort；timeout 120s claude -p --output-format json --model haiku --effort high --dangerously-skip-permissions <<< 'Reply ok'；及 --effort bogus"
    result: refuted
    note: "[实测] Claude Code 2.1.266 有 `--effort <low|medium|high|xhigh|max>` flag（'Effort level for the current session'）。--effort high → exit 0 正常应答、modelUsage=claude-haiku-4-5-20251001；--effort bogus → 'Warning: Unknown --effort value ... ignoring it'、exit 0。=> BDD-10 走 `[BASELINE_CHANGE]`（用户已批准）：按能力探测（`claude --help` 含 `--effort`）分流映射 / 省略；**不硬编码版本号**，实测边界 = 2.1.266 [实测] 有 / 2.1.263 [实测] 无 / 引入版本未核实"
  - id: MV11
    assumption: "tmux wrapper 生命周期 + list-clients + kill-session 行为（BDD-37/38）"
    method: "tmux new-session -d -s agate-TAG0034-mvtest-$$ '<自结束 wrapper 带倒计时>'；tmux list-sessions/list-clients；等 wrapper 自结束；tmux kill-session 对已消失 session"
    result: confirmed
    note: "[实测] wrapper 自结束 → session 自然结束、无残留；list-clients 无人 attach → 空输出 + exit 0；kill-session 对已消失 session → 'can't find session' + exit 1。=> 清理逻辑先 tmux has-session 判断 / 容忍 exit 1（§3.10）。BDD-38 余量取 10s（force-kill at N+10s，N 默认 15s）。环境 = WSL2 + tmux 3.4，目标环境须复跑（R10）"
```

**整体结论**：三平台 spawn + 结构化输出解析、Codex 两层 status、OpenCode 命名 subagent model 继承、tmux 生命周期均 `confirmed`（真机实测）；OpenCode bug② 交互式 TUI 切换路径为 [实测机制一致 + 交互路径推断]（如实标注）；BDD-10 `refuted`（Claude Code 2.1.266 [实测] 有 `--effort`），已由用户 2026-09-09 定夺为 `[BASELINE_CHANGE]`（按能力探测映射、不硬编码版本号），不阻塞其余设计。

---

## §6 files_to_read（P4 implementer 精准清单，不列全仓）

```yaml
files_to_read:
  # ── P4a ──
  - path: agate/scripts/check-maintainability.py:88-148
    why: "_load_config 全兜底范式——dispatch-routing.yaml + dispatch-tiers.yaml 加载器逐字参考（文件不存在/yaml不可导入/非dict/单键类型坏 的四档兜底）"
  - path: agate/scripts/agate-dispatch.py
    why: "route 子命令落点；读懂 main() 参数分派 + 既有渲染路径（_render_dispatch_context/_next_card_content/CARD-SOURCE/generated_by）——route 分支不得改动这些"
  - path: agate/scripts/check-events.py
    why: "第 8 条追加审计链落点；读懂逐行循环 + 既有 1-7 条 + 哈希链 sha256(上一行原始文本) + 错误出口格式——只在 event==dispatch_route 分支加 reason 枚举校验，不动其余"
  - path: agate/scripts/agate_common.py
    why: "append_event / GENESIS_HASH / write_gate_result / resolve_workspace——dispatch_route 事件写入复用 append_event，不自造"
  - path: agate/rules/dispatch.yaml
    why: "五模式词表 / gates 表 / field_readers——路由是铁律1之前插入的一步，确认不改这些枚举"
  - path: agate/rules/phases.yaml
    why: "回归对照基准『结构零改动』——档位词表放新文件、不扩此文件字段；确认 exec_role 结构不动"
  - path: agate/dispatch-protocol.md:15-45
    why: "三铁律原文——新节『查表→派首选→逐级回落→再派发』在语义顺序上位于铁律1之前"
  - path: agate/dispatch-protocol.md:502-601
    why: "『派发编排机制』节——新节落点 + DEBT0039 措辞② + 单Agent模式/BDD-26vs51 说明落点"
  - path: agate/scripts/check-gate.py:734-775
    why: "_gate_p2_dispatch_plan 校验口径（mode/parallel_limit/batches≤limit/complexity枚举）——确认本文件 dispatch_plan 合法；及 _gate_p4 完整度判据（DEBT0037 手动步来源）"
  # ── P4b ──
  - path: agate/scripts/agate-cmdstream-adapters.py:666-888
    why: "CodexAdapter class + ADAPTERS['codex'] + _codex_is_finished——cli:codex 子进程存活检测直接复用，不改；payload.item.status 取值集 completed/failed/in_progress"
  - path: docs/research/cross-platform-dispatch-mechanics.md:141-210
    why: "§6 返回/输出与结果识别——三平台结构化输出字段 + 退出码可靠性 + 失败特征签名（与本文 §3.7 判定表交叉核）"
  - path: docs/research/cross-platform-dispatch-mechanics.md:96-131
    why: "§4 权限沙箱绕过 flag + §5.2 子代理 model 传参——子进程命令构造 + OpenCode 命名 agent 间接路"
  - path: agate/platform-notes.md:43-105
    why: "Codex 章——spawn_agent schema [自述] / payload.item.status 真机取值集 / CodexAdapter 数据源；effort 注明落点（M10）"
  - path: agate/SETUP.md:175-217
    why: "步骤 2-Codex——机器级 scaffold 小节（M9）比照此 per-platform onboarding 形态"
  - path: docs/design-notes/design-dispatch-routing.md:96-108
    why: "§2.4a 评审打回续跑——续接优先/重起兜底；续接失败无客观信号是已知缺口"
  # ── P4c ──
  - path: docs/research/cross-platform-dispatch-mechanics.md:298-321
    why: "附录 A3/A19 tmux 真机实测记录——wrapper | tee capture / list-clients / kill-session 有client时的行为"
  - path: docs/design-notes/design-dispatch-routing.md:134-157
    why: "§3 tmux 观测——session 命名/生命周期/退出倒计时/明确不做；环境代表性 W2"
  # ── 全批共用 ──
  - path: agate-workspace/maintainability.yaml
    why: "项目级配置文件形态先例——dispatch-routing.yaml scaffold 结构参照"
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md:1-90
    why: "F1/DEBT0035 终态样本教训 + DEBT0037/DEBT0039 来源 + protocol-docs 批标 P4 先例"
```

---

## §7 env_constraints（正文）

```yaml
env_constraints:
  debug_env: "worktree .worktrees/agate-TAG0034（分支 feat/TAG0034-dispatch-routing）；系统 python3 /usr/bin/python3 (3.12.3) 跑 pytest/pyyaml；ruff = ~/.venvs/agate-dev/bin/ruff；检查对象类脚本用 worktree 的 agate/scripts/，派发/渲染类工具用 ~/.agate/scripts/ 稳定版（TAG0016 教训）"
  isolation_check: "P5 gate 前确认：git diff --cached 只含预期文件；check-protocol-consistency.py 用 worktree 自己的脚本（否则扫到主 checkout）；真机 CLI 调用写 ~/.codex/sessions/ 与 ~/.local/share/opencode/ 是 CLI 自身 state，非 prod agate、非 repo——minimal_validation 固有，可接受；主 checkout 与 ~/.agate 稳定版禁止改动"
  self_gate: "改 agate/dispatch-protocol.md / agate/scripts/agate-dispatch.py / agate/scripts/check-events.py / agate/scripts/check-dispatch-routing.py（新）/ agate/rules/dispatch-tiers.yaml（新）/ agate/SETUP.md / agate/platform-notes.md / agate/assets/execution-roles/architect.md / agate/tests/** 的 commit → 触发 SELF-GATE，主 Agent 须派 protocol-alignment-review（A1-A7），commit message 含 self-gate-review: 路径 / self-gate-skip: 理由。agate-workspace/dispatch-routing.yaml + 机器级绑定文件新增不触发（非协议本体，同 maintainability.yaml）"
  debt0037_manual_step: "dispatch_plan=static-batch 多提交阶段：P4a/P4b/P4c 分批 commit 后暂存区空时 check-gate.py P4 exit 1 → agate-next.py 拒推进 → 主 Agent 手动 _advance（改 .state.yaml phase + append_event state_transition）。P4b/P4c 之间、P4c→P5 可能命中。排期预留"
  real_machine: "三 CLI + tmux 本机已装已认证（Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4）。唯一环境不可得项 = Codex API-key 账号 model 阵容（V8，research §11）——本机 ChatGPT 账号，非阻塞、登记待补；止损轮次 2（独立计数，不占 retries[P5/P6]）"
  effort_flag_capability_probe: "Claude Code effort 映射按能力探测——路由决策层跑 `claude --help`，含 `--effort` 则映射 `--effort <e>`、不含则省略 effort flag 不报错。**不硬编码版本号**：实测边界 = 本机 2.1.266 有 / 2.1.263 无 / 引入版本未核实。BDD-10 已走 [BASELINE_CHANGE]（用户 2026-09-09 批准），P1-requirements.md BDD-10 同步修订"
```

> **边界提醒**：`env_constraints` 是声明性字段，不被自动执行、无 gate 脚本校验其条件成立。真正强制的是 §8 `gate_commands`（有 exit code 可判）+ P4 批次 checklist（§4）。`self_gate` / `debt0037_manual_step` 的强制力落在「主 Agent 派 `protocol-alignment-review`」+「主 Agent 手动 `_advance`」这两个 P4/P7 阶段动作上，不因写进本字段就自动生效。

---

## §8 gate_commands（P2 固化，P3-P6 不得修改）

```yaml
gate_commands:
  P3: "python3 -m pytest agate/tests/ -q"
  P3_timeout_seconds: 300
  P5: "python3 -m pytest agate/tests/ -q --tb=no"
  P5_timeout_seconds: 300
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_consistency_timeout_seconds: 120
  P5_events: "python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing"
  P5_events_timeout_seconds: 60
  P5_routing_schema: "python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml"
  P5_routing_schema_timeout_seconds: 60
  project_module: "agate"
```

**说明**：

- **每个校验独立 key，不用 `&&` 串接**（短路反模式，TAG0004 教训）。
- `P3` = 测试运行器（verbose 供 `check-tdd-red.py` 读取）；裸 `P3`，**不声明 `P3_xxx` 检测键**（BDD-6 卡禁令）。`P3` 走 `AGATE_TDD_TIMEOUT`（默认 120s）——本任务测试量较大，实际执行时 subagent 可按「命令超时兜底」层级 4 设 `timeout` = 预期 ×1.5。`P3_timeout_seconds` 为静态声明供人读（300s，测试树较大）。
- `P5` = 紧凑模式全量 pytest；`P5_consistency` = `--strict-errors-only`（AGENTS.md 定义：只按 ERROR 判失败，日常任务默认；BDD-50 承接 DEBT0039 closure「consistency 0 ERROR」）；`P5_events` = `dispatch_route` 事件账本审计（BDD-27/29/30）；`P5_routing_schema` = routing schema 静态校验器（BDD-1~6，跑本任务提交的 `agate-workspace/dispatch-routing.yaml` scaffold）。
- **无 `P5_e2e`**：`ui_affected: false`，无用户可见页面 / 渲染产出。
- **无 `P5_shellcheck`**：本任务大概率不新增 `.sh`（tmux wrapper 若落为独立 `.sh` 则 P4c 批补声明 `P5_shellcheck: "shellcheck <path>"`——结构性预留，P4c 定）。
- `project_module: "agate"` —— B 类 import 错误检测前缀（pytest 项目填包名）。
- `{key}_timeout_seconds` 均按类型档：单元/脚本类 60-300s（`AGATE_TDD_TIMEOUT` 对齐 + 测试树规模上浮）；无 E2E（300s 档）/ 构建（600s 档）项。

---

## §9 design-note / roadmap 修订要点（M12，走 docs commit，非 SELF-GATE）

**`docs/design-notes/design-dispatch-routing.md`** —— 头部「做什么」+ §2.1 + §2.2 按 2026-09-09 定案重写，纳入 6 项（BDD-46/52/53）：

1. **三层落点**：配置文件**不在** `agate/rules/`——① 协议本体档位词表 `agate/rules/dispatch-tiers.yaml`（SELF-GATE）；②③ 项目级 `agate-workspace/dispatch-routing.yaml`（`tier_bindings:` + `routes:`，非 SELF-GATE，MVP 不拆机器级）。删除「新增 `rules/dispatch-routing.yaml`」自相矛盾表述。
2. **核心循环去「按序探测 probe」改 try-and-fall**：查表 → 派首选（第一个动作即派真实 dispatch-context，无「hi」预请求）→ 基础设施失败（`launch_fail` / `infra_error` / `no_parseable_output` 三类）逐级回落 → 全落空默认派发。§2.2「按声明顺序逐个探测」「向候选 CLI 发一条极简请求」等整段替换。
3. **`tier` + `effort` 两正交轴 + `(phase,role)` key（role 可选）**：`{cli, model}` 二元 → `tier`（bulk/standard/deep）与 `effort`（low/medium/high 可选）正交；配置里 `tier: deep, effort: high` 引用 或 `candidates: [{cli,model,effort?}]` 直接值二选一；解析 key = `(phase,role)` → `phase` → `standard`。§8「不定义档位」表述反转为「协议定义档位词表 + 语义画像 + 出厂默认（全 standard）」。
4. **`cli: native` 弱缓解 / 跨 CLI 强缓解 + 自动化不对称**：`cli: native`（同厂商换 model）= **弱缓解**（同训练系谱盲区基本共享），且原理上做不到「不依赖主 Agent」——天花板是主 Agent 机械横传 model；跨 CLI 起子进程 = **强缓解**（真正异源独立视角），可端到端自动化。两形式 gate 判定 / 留痕一致。
   - **effort 轴 evidence-honesty 叙述**：**早期 Claude Code 版本无 effort 旋钮、2.1.26x 起有**（按能力探测映射）——不再说「Claude Code CLI 无 effort 旋钮」。**结论：effort 轴现三平台均可用**（Codex `-c model_reasoning_effort=` / OpenCode `--variant` / Claude Code `--effort`，Claude Code 按 `claude --help` 能力探测、无该 flag 的旧版省略不报错）。
5. **两条完整性不变量**：① 「候选回落 ≠ 状态机 retry」（回落只在基础设施失败发生，不占 `retries[Pn]`、不写 `state_transition`、不触发 PAUSED，只写 `dispatch_route`）；② 「gate FAIL 绝不换候选」（收到任何 gate 能评产出即停止回落；gate FAIL → 同一候选正常阶段 retry；`dispatch_route` 理由码枚举无 `gate_fail` 值，`check-events.py` 机械拒绝）。
6. **per-machine 机会式、不追求跨机可复现**：只有抽象 `(phase,role)`→档位映射可 commit 共享；档位→具体 model 的绑定就是「本机实际能跑什么」，别的机器复现不了不是缺陷。

头部「机制现状一句话」同步：`cli: native` 三平台 = Claude Code ✅（Task 单次传 `model`；`--effort` flag 本机 2.1.266 [实测] 有 / 引入版本未核实，路由按能力探测映射）/ Codex ✅（`spawn_agent` 按次传 `model` + `reasoning_effort`）/ OpenCode ⚠（命名 subagent 间接路，bug② 经真机核实不影响本用途）。子进程形式三平台都通。Codex 退出码不可靠须解析 `--json`（turn 层为准）。

**`agate-workspace/roadmap/roadmap.md`** —— RM-AG0060 长描述旧措辞回写（BDD-47）：`rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml`；「按序探测」→ try-and-fall；`{cli,model}` 二元 → `tier` + `effort` 两轴。与 design-note 定案一致。

---

## §10 实现完成的标志（供 P3 测试设计 / P5 验证）

1. `check-dispatch-routing.py` 对 §3.6 schema 全部合法 / 非法样本判定正确（BDD-1~6）；`agate-workspace/dispatch-routing.yaml` scaffold 通过。
2. `resolve(phase, role)` 对 §3.3 算法的每条分支（`(phase,role)` 命中 / `phase` 回落 / 出厂默认 / `standard` 短路 / tier 展开 / `tier_bindings` 缺该 tier / 同名键 last-write-wins / effort 合并）产出唯一确定结果（BDD-7~18）；**T1**：返回对象键集恒为 `{form, chain, model, effort}`、`form ∈ {'default','chain'}`、`form=='default'` 时 `chain is None`。
3. try-and-fall 对 §3.7 四种 `outcome.kind`（`launch_fail` / `infra_error` / `no_parseable_output` / `HAS_OUTPUT`）分别走「回落带对应理由码」/「停止交 gate」；全落空 → 默认派发 + `final={"cli":"default"}`（BDD-19~23）；`resolve` 返回 `form=='default'` → 直接默认派发、**不写** `dispatch_route` 事件。**T2**：模拟 `wait(pid)` 超时 / RM-AG0055 命令流阈值触发 kill → `outcome.kind=INFRA_ERROR`、回落 `infra_error`（N6）。「格式合法」= presence 级骨架可解析（frontmatter + 必需锚点标题），不含内容完整度 / 质量判断，结构完整度校验不得塞进 `NO_PARSEABLE_OUTPUT`（N7）。
4. 完整性不变量：产出质量差不回落（BDD-24）；收到产出即停（BDD-25）；gate FAIL → 同候选 retry + `dispatch_route` 计数不增（BDD-26）；`gate_fail` 理由码 → `check-events.py` exit 1（BDD-27）；回落不写 `state_transition` / 不动 `retries` / 不进 PAUSED（BDD-28）。**T3**：`check-events.py` 第 8 条参数化用例——三合法理由码各一条账本断言 exit 0 + 混入第四值断言 exit 1。
5. `dispatch_route` 事件写入复用哈希链、`check-events.py` 认它为已知类型且既有 `test_check_events.py` 零改动仍绿（BDD-29/30）。
6. `cli: native` 三平台：Claude Code `modelUsage` == 解析目标（BDD-31）；OpenCode 命名 subagent 跑配置 model（BDD-32）；effort 映射 Codex `-c model_reasoning_effort=` / OpenCode `--variant` / Claude Code 按 `claude --help` 能力探测——含 `--effort` 则映射、不含则省略不报错（BDD-8/9/10，BDD-10 走 `[BASELINE_CHANGE]`，判据 key off 能力探测、不硬编码版本号）。
7. 子进程 spawn + 结构化输出解析对 §3.7 判定表正确（BDD-33~36），fixture 用 §5 真机样本收敛。
8. routed-away judge：verdict + 证据落 `TASK_DIR` 时 `check-gate.py P6.5` 平台无关 exit 0，两校验器本任务零改动（BDD-42）。
9. tmux：`which tmux` 决定包裹 / 裸跑、两路径留痕逐字节一致（BDD-37）；生命周期 + `N+10s` 兜底强杀 + 有 client 不强杀（BDD-38）。
10. 交互：五模式并行各自独立解析（BDD-43）；自主再派发不走路由表 + 无 `dispatch_route` 事件（BDD-44）；单 Agent 模式 no-op（BDD-45）；P5→P4 回退重解析、无升档逻辑（BDD-51）。
11. 回归：`git diff` 改动前后 `phases.yaml` / `check-gate.py` / `check-state-transition.py` / 状态机结构化部分逐字节不变；`test_tag0027_b2_*` 零改动仍绿（BDD-39）；无任何配置文件跑完整 P1→P8，`dispatch_route` 事件条数 = 0、派发行为与机制引入前一致（BDD-40）。
12. `dispatch-protocol.md` 新节含「gate 不认谁生产的」+ 两条完整性不变量 + 「查表→派首选→逐级回落→再派发」步位于铁律 1 之前（BDD-41）+ DEBT0039 措辞②（BDD-49）；`architect.md` 批次设计节含 DEBT0039 措辞①（BDD-48）；`check-protocol-consistency.py --strict-errors-only` exit 0（BDD-50）。
13. design-note 头部 + §2.1/§2.2 含 §9 六项 + 两轴/key/缓解标注 + 两条完整性不变量 + per-machine 声明（BDD-46/52/53）；roadmap RM-AG0060 旧措辞已回写（BDD-47）。

---

## §11 SCOPE / NEED_CONFIRM 小结

- **无 `[SCOPE+]`**：设计未发现 P1 未预见的必须做的事。DEBT0039 并入是 P1 已批准既有范围（`[SCOPE+ from user-approval]`），不重复标注。
- **`[NEED_CONFIRM]`：无**（原 BDD-10 冲突项已由用户 2026-09-09 定夺为 `[BASELINE_CHANGE]`，见文件顶部 + §3.4 + §5 MV10）。
- **`[BASELINE_CHANGE]`（1 处，见文件顶部）**：BDD-10 —— 用户 2026-09-09 批准，effort 按能力探测（`claude --help` 是否含 `--effort`）映射到 Claude Code `--effort`，不硬编码版本号；P1-requirements.md BDD-10 已同步修订。
- 其余「P2 定」留白（BDD-15/18 合并语义 / BDD-35 两层取 turn 层 / BDD-38 余量 10s）已在 §3.3 / §3.7 / §3.10 定死。
