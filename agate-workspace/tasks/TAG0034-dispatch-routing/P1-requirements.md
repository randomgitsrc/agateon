---
phase: P1
task_id: TAG0034
type: problems
parent: P0-brief.md
trace_id: TAG0034-P1-20260909
status: draft
created: 2026-09-09
agent: analyst
risk_level: medium
ceremony: standard
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-scripts, agate-rules, agate-docs, agate-tests]
domains: [backend, cli]
baseline_changes:
  - "BDD-10（用户批准 2026-09-09）：Claude Code effort 由『无旋钮→静默忽略』改为『按 claude --help 是否含 --effort 能力探测分流』——P2 minimal_validation MV10 实测本机 2.1.266 有 --effort，2.1.263 无；不硬编码版本号。标记在 BDD-10 行首 [BASELINE_CHANGE:]"
suggest_resolved:
  - "tier 三档命名 bulk/standard/deep（已采纳 by 主 Agent 2026-09-09）"
  - "{cli: native, model: null} 合法，null = 该 CLI 默认 model（已采纳 by 主 Agent 2026-09-09）"
  - "MVP 单文件合并协议本体①与项目级③ + 内联档位；机器级②是否拆出留 P2 定（已采纳 by 主 Agent 2026-09-09）"
  - "三层配置优先级序：项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认（已采纳 by 主 Agent 2026-09-09）"
  - "决策落点扩 agate-dispatch.py 新增子命令，不新增 agate-route.py（已采纳 by 主 Agent 2026-09-09）"
  - "routing schema 静态校验器新增为独立脚本 check-dispatch-routing.py，不入 agate/rules/schema（已采纳 by 主 Agent 2026-09-09）"
capability_requirements:
  - need: three-cli-installed-authenticated
    why: P1 前置真机核实（OpenCode bug② 直接复现）+ P4a/P4b cli:native 与子进程 spawn 的真机验证 + P5/P6 端到端验收都要真派三平台
    available:
      - "本机 Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4 均已装已认证（P0-brief env_constraints + objective_info）"
    status: available
  - need: opencode-bug2-repro
    why: 外部评审 B2 教训——OpenCode 旧 bug②（父会话交互式切 model 后命名 subagent 是否跟随）本会话仅机制推断未直接复现，P1/P2 表述不得把推断混同「已实测」
    available:
      - "本机 opencode 1.18.11 已装已认证，可配命名 agent + 父会话交互式切 model + 再派该 agent 直接复现（research §5.2 / §10 步骤具体可执行）"
    status: available
  - need: no-frontend-no-vision
    why: 纯协议/CLI/脚本/文档任务，无用户可见页面产线、无渲染产出
    available: []
    status: available
verification_env: "Claude Code 2.1.266 + codex-cli 0.153.4 + opencode 1.18.11 + tmux 3.4（本机已就绪，均已认证）；Codex API-key 账号 model 阵容（V8）本机 ChatGPT 账号环境不可得"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5/P6]）；仅适用于 Codex API-key 账号 model 阵容（V8）一项——非阻塞、登记待补；其余真机项本机可做"
---

# P1 需求基线 — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）

> parent：`P0-brief.md`（task / scope / out-of-scope / known_risks 12 条 / env_constraints / executor_env）
> 设计意图来源：`docs/design-notes/design-dispatch-routing.md`（**本任务待修订交付物**，§2.1/§2.2 + 头部自相矛盾，冲突以 P0-brief 2026-09-09 定案为准）
> 机制事实：`docs/research/cross-platform-dispatch-mechanics.md`（三平台机制 A1-A19 实测 + §10 复核清单 + §11 未尽项）
> 证据强度纪律：`docs/reviews/review-dispatch-routing-external-{20260908,round2-20260908}.md`（B1/B2 教训：`[自述]` / 推断不得混同「已实测」）

`[NO_NEED_CONFIRM]`
`[PROD_NOT_TOUCHED]`

---

## 0. P0-brief 时效性质疑（跨会话恢复任务，立项 2026-09-08 / 启动 2026-09-09）

**已核对 P0-brief 时效性，无严重漂移。** 独立复核严重判据 1-3：

| 判据 | 复核 | 结论 |
|---|---|---|
| 1. `task` 目标方案不再成立 | 配置驱动跨 CLI/model 派发 + tmux 观测：三 CLI 已装已认证；`agate-dispatch.py` 存在且当前仅渲染 dispatch-context，可扩；`check-events.py` 第 7 条「未知 event 类型不拦截」向后兼容；`agate-workspace/maintainability.yaml` + `check-maintainability.py:_load_config`（line 88-148）全兜底先例在位 | ✅ 方案成立 |
| 2. `executor_env` 平台前提不再成立 | worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）就绪；`.state.yaml` phase=P1 / status=active / judge.enabled=true | ✅ 前提成立 |
| 3. `known_risks` 的「已解决前提」实际未解决或被他任务解决 | 关键前置 = TAG0033 / RM-AG0061 合并 main → v0.70.0（PR #298，CHANGELOG `[0.70.0] - 2026-09-09`）提供 `CodexAdapter`（`agate/scripts/agate-cmdstream-adapters.py:666` class + `:878` `ADAPTERS["codex"]`）；roadmap RM-AG0061 status=done。DEBT0037（check-gate P4 多提交阶段判据）**未修复**——但 known_risks 明确写「若在本任务启动前已修复则直接受益」，未修复是 P0-brief 已登记的已知手动步，不构成漂移 | ✅ 前提成立 |

**轻微偏移（记录，不阻塞）**：`[P0_STALE: Claude Code 本机实际 2.1.266，P0-brief / HANDOFF known_risks 记 2.1.263]` —— patch bump，属 known_risks 已预期的「跨 CLI flag 名版本漂移」；不影响 `-m` / `--model` / `--dangerously-skip-permissions` / `--output-format json` flag 语义。已在本文件 `verification_env` 与 §7 反映实际版本；P0-brief 字段本身由主 Agent 视需要回写。无其它偏移。

---

## 1. 需求复述

在 agate 协议层落地派发路由设计（RM-AG0060 epic，Codex 接入已由 TAG0033 拆走并合并 v0.70.0）：

**机制一 — 配置驱动路由**：新增**项目级**配置文件 `agate-workspace/dispatch-routing.yaml`（对齐 `maintainability.yaml` 先例：项目级、全兜底、非协议本体、不受 SELF-GATE），按 `(phase, role)`（role 层可选）声明候选路由 —— 可写档位引用 `tier: <档> [effort: <档>]`（可移植）**或**直接值 `candidates: [{cli, model, effort?}]`（跳过间接层，牺牲可移植换明确），二选一。主 Agent 到某阶段派某角色时：**查表 → 直接派首选候选（无 probe，try-and-fall） → 若『起不来 / 基础设施失败 / 无可解析产出』则逐级回落下一候选 → 全落空则默认派发（同平台同 model，恒等于本机制未启用）**。`cli` 可为 `native`（同厂商换 model，不脱离原生派发工具——**弱缓解**）或另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程——**强缓解**）。新增 `dispatch_route` 事件无差别留痕（带回落理由码）。

**机制二 — tmux 观测层（P4c，低优先、可整体切除）**：子进程形式若 `which tmux` 成功则包一层 `tmux new-session` 供人 `attach`，wrapper 自带退出倒计时；失败裸跑。不通过不影响 P4a/P4b。

**配置三层**（P0-brief scope 定案）：① **协议本体**（`agate/rules/` 下新文件或 `phases.yaml` 旁）—— 档位词表 + 每档语义画像 + 出厂默认 `(phase,role)`→档位映射（全 `standard`），改它**走 SELF-GATE**；② **机器/安装级** —— 档位→有序跨 CLI 候选链 `[{cli,model,effort}]` 的具体绑定，落 `~/.config/agate/` 类**非版本控制**路径，由 SETUP 流程 scaffold；③ **项目级** `agate-workspace/dispatch-routing.yaml` —— `(phase,role)`→档位映射 + 直接值覆盖。全兜底：任一层缺失/损坏/类型坏 → 出厂默认（= 现状），不报错不静默跳过（复用 `check-maintainability.py:_load_config` 模式）。MVP 可合并 ①③ 为单文件 + 内联档位定义（是否真拆机器级档位文件由 P2 按「多机可移植性是否真需求」定）。

**两轴**：`tier`（能力档，`bulk` / `standard` / `deep`）与 `effort`（`low`/`medium`/`high`，可选）**正交** —— 「便宜模型 + 高 effort」「顶配 + 低 effort」都合法。`effort` 映射各平台推理档 flag：Codex `-c model_reasoning_effort=` / OpenCode `--variant` / **Claude Code 按能力探测**——`claude --help` 含 `--effort` 则映射（本机 2.1.266 [实测] 有），旧版本无该 flag 则静默忽略、不报错。引入版本未核实（2.1.263 [实测] 无 / 2.1.266 [实测] 有）。

**决策落点**：优先扩 `agate/scripts/agate-dispatch.py`（不成再新增 `agate-route.py`）。查表/回落/降级是纯机械步骤。

**回归硬约束（设计前提）**：`gate` / `check-gate.py` / `check-state-transition.py` / `phases.yaml` 结构 / 状态机 **零改动**；「不配置 = 逐字节现状」。gate 只认产出文件 + exit code，不认「谁生产的」——`dispatch-protocol.md` 新节须显式写这句。

**design-note 修订 + roadmap 回写**（本任务交付物）：`design-dispatch-routing.md` 头部 + §2.1/§2.2 按 2026-09-09 定案重写；`roadmap.md` RM-AG0060 长描述里旧 `rules/dispatch-routing.yaml` / 「按序探测」措辞一并回写。

**SELF-GATE**：改 `agate/dispatch-protocol.md` + `agate/scripts/agate-dispatch.py`（+ 可能 `check-events.py` 扩展 / 新增校验器）+ `agate/SETUP.md` + `agate/rules/` 档位词表文件 + `agate/tests/` → 触发（commit message 含 `self-gate-review:` / `self-gate-skip:`）。`agate-workspace/dispatch-routing.yaml` + 机器级绑定文件新增**不触发**。

`[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]`（来源：用户批准 + DEBT0039 并入，主会话已确认转交条件，2026-09-09）—— **DEBT0039 文档边界澄清**并入本任务范围，作显式交付项（非顺手改漏）。DEBT0039 根因：TAG0033 复盘中 architect 把「补协议文档正文」批（`platform-notes.md` Codex 章 + `SETUP.md` 小节）误标为 P7 执行，主 Agent 比照 TAG0030 先例（doc-assertion 审计 P3 写红、正文 P4 补绿）拉回 P4 才避免带 by-design 红推进；两处权威文档没写清「author 文档内容（P4）」vs「跨文件一致性验证（P7）」的阶段边界。本任务交付：① `agate/assets/execution-roles/architect.md`「批次设计」节增补「补协议文档正文 = P4」的显式边界措辞；② `agate/dispatch-protocol.md`「派发编排机制」节显式区分 author 内容（P4）vs 跨文件一致性验证（P7）。**只做这两处纯文档边界澄清**，不扩到其它 DEBT、不改任何脚本 / gate 逻辑。承接 DEBT0039 `closure_criteria` 三条 → 转 BDD-48/49/50。

`[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4 — 2026-09-09]`（来源：P4a `protocol-alignment-review` 提出 2 项 NEEDS_HUMAN_REVIEW，用户 2026-09-09 批准「两项都补，落 P8 收尾，标 `[HUMAN_CONFIRMED]`」）—— 两条**文档传播交付项**并入本任务范围（P2-design §4.4 / §10 未覆盖，属经用户批准新增的改动面）：
① **`agate/LIMITATIONS.md` 局限 2（同源模型系统性盲区）补一段「部分缓解链」**：指向本任务的路由机制（`cli: native` 弱缓解 / 跨 CLI 子进程强缓解 / `dispatch_route` 留痕 + 两条完整性不变量），与 TAG0020 P6.5 Judge 落地时给局限 3 补「P6.5 独立 Judge 缓解链」的先例对称。**措辞务必保留诚实边界句**：「仍非根治 —— 主 Agent 自身选型 / 横传 model 无外部约束（与局限 3 同构）」。
② **`agate/adr.md` 补 ADR-013「派发路由 / gate 生产者无关性」**：记录红线级架构决策「gate 只认产出文件 + exit code、不认谁生产的；这条解耦是跨 CLI/model 派发设计成立的前提；未来不得为跨 CLI 派发定制 gate」，关联 ADR-002（可判定性）/ ADR-006（同源盲区）/ RM-AG0060。理由：`dispatch-protocol.md` 散文承载不够稳（会被后人改），红线决策须进 `adr.md`。
**两条均落 P8 收尾批**（内容基于 P4a-P4c 最终落地的机制形态，措辞最准），P8 dispatch-context 显式列为 doc-sync 交付项。alignment review 复审时以 `[HUMAN_CONFIRMED: 2026-09-09 …（P8 落地）]` 闭合 A5.3 / A7.4。

---

## 2. 隐含需求识别（逐维度）

| 维度 | 识别结果 | 为什么必须 |
|---|---|---|
| 同类/影响面 | 见 §3 同类扫描 —— `dispatch_route` 全仓 0 命中（新事件）；`agate-dispatch.py` 有 5 处消费方（含 `check-p6-provenance.py` / `check-judge-verdict.py` / 2 个测试）；`check-events.py` 有 15 个脚本消费方；`maintainability.yaml` + `_load_config` 是配置落点先例 | 不梳理会「只改被报告的那一处」——扩 `agate-dispatch.py` 破坏 dispatch-context 渲染路径、加 `dispatch_route` 校验破坏哈希链的既有消费方 |
| 数据 | 无既有数据迁移；`gate-events.jsonl` 追加新事件类型，须复用既有哈希链、不改写历史行 | 账本 append-only 语义（`check-events.py` 第 4 条）不能破坏 |
| 前端 | 无用户可见页面 / 渲染产出（`domains: [backend, cli]`），无 UX BDD / vision 能力硬要求（P1 gate `_gate_p1_vision_capability` 仅 `domains` 含 frontend 触发） | 明确排除，避免 P2 误派 UI 评审 |
| 多端 | 本任务本身就是「多 CLI 端」；`check-events.py` 校验端 + `gate-events.jsonl` 写入端须同步认 `dispatch_route`；`platform-notes.md` 三平台章 + 各 `SETUP.md` 自动化 flag 小节须同步 | T005 漏 MCP 教训的同构——写入端认了校验端不认 = 账本审计红 |
| 边界 | 候选全灭 / 配了但 CLI 未装未认证 / 配置文件损坏 / gate FAIL 后同阶段 retry（同候选，BDD-26）/ P5→P4 跨阶段回退后重新机械解析一次路由（BDD-51）/ 五模式并行批 / 自主再派发 / 单 Agent 模式（`has_task_tool:false`）各自的路由行为 | 完整性不变量（模型购物洞）+ 「不启用 = 现状」不变量都在边界上；两类 retry 的路由行为须显式区分（同阶段 = 同候选 / 跨阶段回退 = 机械重解析、无升档逻辑）|
| 兼容 | 「不配置 = 逐字节现状」；`standard` 语义必须钉死为「继承主 Agent 当前 model 的原生派发」，否则出厂默认全 `standard` ≠ 现状 | 破坏「机会式启用」不变量 = 破坏局限 6「零基础设施」 |

**证据强度诚实（外部评审 B1/B2）**：`cli: native` 是**弱缓解**（同厂商换 model 盲区基本共享）；`effort` 轴**早期 Claude Code 版本无 effort 旋钮、2.1.26x 起有**（按能力探测映射，见 BDD-10 `[BASELINE_CHANGE]`）——现三平台均可用；OpenCode bug② 是**机制推断 + P2 已真机核实机制一致**（见 P2-design §5 MV7，交互式 TUI 切换路径仍为推断）。表述不得把 `[自述]` / 推断写成「已实测」。

---

## 3. 同类扫描（强制节）

扫描动作：对关键符号 grep 全仓（worktree 根，排除本任务目录 / 设计三件套 / roadmap / active-tasks / HANDOFF 自引用）。

| # | 符号 | 命中 | 文件清单 | 逐条处理判定 |
|---|---|---|---|---|
| 1 | `dispatch_route`（新事件名） | **0**（协议本体 / 脚本 / 测试） | 仅 `active-tasks.md` / `HANDOFF-TAG0034.md` / roadmap / 本任务目录（均为本任务自身叙述） | **确认只此一处（全新）**：`dispatch_route` 是新增事件类型，无既有冲突。本次处理：`gate-events.jsonl` 写入端 + `check-events.py` 校验端同步新增识别 + 理由码枚举校验 |
| 2 | `agate-route` / `agate_route` | **0**（脚本） | 仅 P0-brief / HANDOFF / design-note 提及「不成再新增 `agate-route.py`」 | **不新增**：本次优先扩 `agate-dispatch.py`（P0-brief 定案）。`agate-route.py` 仅作 P2 备选记录，不构成同类实例 |
| 3 | `agate-dispatch` 消费方 | **5** | `agate/assets/templates/dispatch-context.md`、`agate/scripts/agate-dispatch.py`（自身）、`agate/scripts/check-p6-provenance.py`（审计 2：`<!-- CARD-SOURCE: agate-dispatch.py -->` 锚点）、`agate/scripts/check-judge-verdict.py`（`_strip_card` 同款锚点）、`agate/tests/unit/test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` | **全部本次处理（回归拦截）**：扩 `agate-dispatch.py` 加路由决策**不得**改变既有 dispatch-context 渲染产物字节面（`generated_by: agate-dispatch.py + 主 Agent` / CARD-SOURCE 锚点位置）。BDD-39 断言这 5 处消费方的既有测试零改动仍绿 |
| 4 | `check-events.py` 消费方 | **15 脚本 + 4 测试** | `agate/rules/phases.yaml`、`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`、`agate/scripts/{check-judge-verdict,agate-next,check-protocol-consistency,agate_common,check-gate,pre-commit-gate,ci-gate-backstop,agate-summary}.py`、`agate/{phase-cards/P6-acceptance.md,state-machine.md,LIMITATIONS.md,loop-orchestration.md}`、`agate/assets/review-roles/judge.md`、`agate/UPGRADING.md`、`agate/tests/unit/test_check_events.py` 等 | **本次处理**：`dispatch_route` 识别 + 理由码枚举校验作为 `check-events.py` 的**追加审计链**（不动第 1-6 条既有链、不动哈希链算法）。BDD-30 断言既有 `test_check_events.py` 用例零改动仍绿 |
| 5 | `maintainability.yaml` + `check-maintainability.py:_load_config` | **1**（`_load_config` line 88-148） | `agate/scripts/check-maintainability.py`、`agate-workspace/maintainability.yaml`、`agate/rules/dispatch.yaml`（间接） | **参考对象（不改）**：`dispatch-routing.yaml` 的加载器逐字参考 `_load_config` 全兜底模式（文件不存在 → 默认值；yaml 不可导入 → 默认值 + stderr；单键缺失 / 类型坏 → 该键默认值）。BDD-16/17 复用该判据形态 |
| 6 | `check-judge-verdict.py` 的 verdict 定位 / 信息隔离扫描（P0-brief P4b 列为可能真缺口） | 纯 `TASK_DIR` 文件解析 | `check-judge-verdict.py`（读 `P6.5-judge-verdict.md` / `P6.5-dispatch-context-judge.md` / `P6-evidence/` / `P1-requirements.md` / `gate-events.jsonl`）、`check-p6-provenance.py`（glob `task_dir` 内文件） | **核实结论：非真缺口**。两校验器都不定位 / 读取 `~/.claude/` 或 `~/.codex/sessions/` 平台 transcript —— judge 路由到 codex/opencode 子进程时，只要其 verdict 文件 + 证据落 `TASK_DIR`（铁律 2/3 不变），`check-judge-verdict.py` + `check-events.py` 平台无关照常通过。本次处理：不改这两个校验器；BDD-42 断言该平台无关性作回归证明 |
| 7 | `phases.yaml` 消费方（回归对照基准） | **9 脚本** | `agate/scripts/{agate-advance,agate-next,agate_common,check-gate,check-structure-consistency,check-yaml-schema,agate-next-card,agate-inject-card,agate-md-field-set}.py` | **本次不处理 `phases.yaml`（零改动硬约束）**：档位词表放 `agate/rules/` 下**新文件**，不扩 `phases.yaml` 字段（避免动 9 个消费方 + `check-structure-consistency.py` S-1/S-2 双向锚点）。BDD-39 断言 `phases.yaml` 逐字节不变 |
| 8 | RM-AG0060 长描述旧措辞 | **1** | `agate-workspace/roadmap/roadmap.md` 的 RM-AG0060 行（`rules/dispatch-routing.yaml` + 「按序探测」+ `{cli,model}` 二元） | **本次处理**：随 design-note 修订一并回写为 `agate-workspace/dispatch-routing.yaml` + try-and-fall + 两轴。BDD-46/47 |
| 9 | DEBT0039 文档边界（author 内容 P4 vs 一致性验证 P7） | 2 处措辞缺口 | `agate/assets/execution-roles/architect.md`「批次设计」节、`agate/dispatch-protocol.md`「派发编排机制」节 | **本次处理（SCOPE+ 用户批准并入）**：`architect.md` 是 **P0-brief 声明改动面之外、经用户批准新增的改动面**（DEBT0039 并入带入，frontmatter `packages` 归 `agate-docs`）；`dispatch-protocol.md`「派发编排机制」节本任务本来就要动（新增「查表 → 派首选 → 逐级回落」步在同一节区），**同文件同批提交、无冲突**。两处只加边界澄清措辞，不改脚本 / gate。转 BDD-48/49；consistency 回归转 BDD-50 |

**回归拦截手段**（同类问题未来仍会新增）：① `dispatch_route` 理由码枚举校验入 `check-events.py`（机械拒绝 `gate_fail`）—— 转 BDD-27；② routing schema 静态校验器（新增，独立于 `agate/rules/schema`）—— 转 BDD-1~6；③ 回归测试证明 `phases.yaml` / gate / 状态机零改动 —— 转 BDD-39；④ `dispatch-protocol.md` 新节写死「gate 不认谁生产的」防未来为跨 CLI 定制 gate —— 转 BDD-41。新增 CHECK 上线前按 AGENTS.md「改脚本工作流第 0 条」全量扫描存量确认不误伤（DEBT0025）。

---

## 4. BDD 验收条件

> 编号连续、单条 Given/When/Then、可二值判定（PASS / FAIL，无中间态）。判据锚定客观信号（exit code / 事件计数 / 文件字节面 / 结构化输出字段），不绑定实现符号名。
> P4c（tmux）相关 BDD 标注「不通过不影响 P4a/P4b」。

### 4.1 schema 校验（新增静态校验器）

#### BDD-1: tier + effort 两正交轴合法组合被接受
- Given `dispatch-routing.yaml` 某 `(phase,role)` 写 `tier: deep` + `effort: high`（含「便宜 tier + 高 effort」「顶配 tier + 低 effort」等交叉组合）
- When 跑 routing 静态校验器
- Then 校验器 exit 0（两轴独立、任意组合合法）

#### BDD-2: tier 与 candidates 二选一，同时出现即非法
- Given 某 `(phase,role)` 条目同时写了 `tier:` 与 `candidates:`
- When 跑 routing 静态校验器
- Then 校验器 exit 1（明确报「tier 与 candidates 互斥」）

#### BDD-3: 路由 key 粒度 = (phase, role)，role 层可选
- Given 配置同时含 `P4:`（phase 级）与 `P4.review:`（`(phase,role)` 级）两种 key 形态
- When 跑 routing 静态校验器
- Then 校验器 exit 0（两种 key 形态都合法识别，role 段可省略）

#### BDD-4: 非法 cli 取值被拒
- Given 某候选写 `cli: gpt-4`（不在 `{native, claude-code, codex, opencode}` 内）
- When 跑 routing 静态校验器
- Then 校验器 exit 1

#### BDD-5: 非法 effort 取值被拒
- Given 某候选写 `effort: turbo`（不在 `{low, medium, high}` 内）
- When 跑 routing 静态校验器
- Then 校验器 exit 1

#### BDD-6: fallback 字段不存在于 schema
- Given 某条目写了 `fallback: <任意值>`
- When 跑 routing 静态校验器
- Then 校验器 exit 1（schema 无 `fallback` 字段——终点回落恒为默认派发、不可配、不需声明）

### 4.2 档位→跨 CLI 候选链展开 + effort 各平台映射

#### BDD-7: tier 引用展开为机器级绑定的有序跨 CLI 候选链
- Given 项目级配置 `(P2, architect)` 写 `tier: deep`，机器级绑定把 `deep` 定义为有序链 `[{cli: codex, model: A}, {cli: claude-code, model: B}]`
- When 路由决策层解析该 `(phase,role)`
- Then 展开出的候选链顺序 = `[codex/A, claude-code/B]`（与机器级绑定声明顺序逐项一致）

#### BDD-8: effort 映射到 Codex 推理档 flag
- Given 候选 `{cli: codex, model: A, effort: high}`
- When 路由决策层构造该 Codex 派发命令
- Then 命令含 `-c model_reasoning_effort=high`（子进程形式）或 `spawn_agent(reasoning_effort="high")`（native 形式）

#### BDD-9: effort 映射到 OpenCode 推理档 flag
- Given 候选 `{cli: opencode, model: provider/M, effort: high}`
- When 路由决策层构造该 OpenCode 派发命令
- Then 命令含 `--variant high`（或等价 `provider/M#high` 后缀）

#### BDD-10: effort 按能力探测映射到 Claude Code `--effort`，无该 flag 时静默忽略

[BASELINE_CHANGE: 用户批准 2026-09-09。原 BDD-10 假设「Claude Code CLI 无 effort 旋钮 → 静默忽略」基于 research 的 2.1.263 实测；P2 minimal_validation MV10 实测本机 2.1.266 已有可用的 `--effort <low|medium|high|xhigh|max>` flag。判据改为按能力探测（`claude --help` 是否含 `--effort`）分流，不硬编码版本号——实测仅知 2.1.266 有 / 2.1.263 无，引入版本未核实。]

- Given 候选 `{cli: claude-code, model: haiku, effort: high}`
- When 路由决策层构造该 Claude Code 派发命令，并探测 `claude --help` 是否含 `--effort`
- Then 探测到 `--effort` → 命令含 `--effort high`（effort ∈ {low,medium,high}）；未探测到（旧版本）→ 命令不含任何 effort/reasoning flag、不报错、无非零退出；两分支均正常派发；`platform-notes.md` 如实注明「2.1.266 [实测] 有 / 2.1.263 [实测] 无 / 引入版本未核实」

### 4.3 解析顺序

#### BDD-11: (phase,role) 命中优先于 phase 级
- Given 配置同时有 `P4:`（phase 级候选链 X）与 `P4.implementer:`（候选链 Y）
- When 主 Agent 在 P4 派 implementer 角色解析路由
- Then 取候选链 Y

#### BDD-12: 无 (phase,role) 条目时回落 phase 级
- Given 配置只有 `P4:`（候选链 X），无任何 `P4.<role>:` 条目
- When 主 Agent 在 P4 派 protocol-alignment-review 角色解析路由
- Then 取候选链 X

#### BDD-13: 无 phase 条目 = standard
- Given 配置无 `P7` 及 `P7.<role>` 任何条目
- When 主 Agent 在 P7 解析路由
- Then 解析结果 = `standard` 档（等价未配置）

### 4.4 standard 语义钉死

#### BDD-14: standard 恒等于继承主 Agent 当前 model 的原生派发
- Given 某 `(phase,role)` 解析结果为 `standard`（显式配 `tier: standard` 或未配置两种来源）
- When 执行该次派发
- Then 派发方式 = 主 Agent 当前平台的原生派发工具 + 继承主 Agent 当前 model，不起子进程、不改 model；行为与「本机制未启用」逐字节一致

### 4.5 三层配置优先级 + 合并语义 + 全兜底

#### BDD-15: 三层优先级确定且可判定
- Given 同一 `(phase,role)` 在项目级直接值覆盖、项目级档位映射、机器级绑定、协议出厂默认四处都可能有值
- When 路由决策层求该 `(phase,role)` 的最终候选链
- Then 取值来源严格按 P2 定死的优先级序（项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认），结果唯一确定、无「取谁含糊」的运行时分支

#### BDD-16: 配置文件缺失 → 出厂默认（= 现状），不报错
- Given `agate-workspace/dispatch-routing.yaml` 不存在
- When 路由决策层加载配置
- Then 加载器返回出厂默认（全 `(phase,role)` = `standard`）、exit 0、无 error；后续派发行为 = 现状

#### BDD-17: 配置文件损坏 / 类型坏 → 出厂默认，不报错不静默跳过
- Given `dispatch-routing.yaml` 存在但 YAML 解析失败（或某键类型坏，如 `tier` 处写了 list）
- When 路由决策层加载配置
- Then 该文件（或该键）回落出厂默认、写一行 stderr WARNING、exit 0；不抛异常、不静默把整段路由跳过（判据形态复用 `check-maintainability.py:_load_config`）

#### BDD-18: 机器级绑定与项目级映射冲突时取值确定
- Given 项目级把 `(P6.5, judge)` 映射到 `tier: deep`，机器级把 `deep` 绑定为候选链 Z，且机器级另有一条与 `deep` 同名但不同内容的历史绑定
- When 路由决策层解析 `(P6.5, judge)`
- Then 按 P2 定死的合并规则取唯一结果（机器级同名键后写覆盖先写 / 或报 schema 错——P2 定），不产生「两条都生效」的歧义

### 4.6 try-and-fall 逐级回落（无 probe）

#### BDD-19: 无 probe——首选候选直接派发
- Given 某 `(phase,role)` 候选链首项为 `{cli: codex, model: A}`
- When 路由决策层执行该次派发
- Then 不向候选发任何「探测 / hi」预请求；第一个动作就是把真实 dispatch-context 派给首选候选

#### BDD-20: launch_fail（起不来）→ 回落下一候选
- Given 首选候选子进程无法启动（CLI 未安装 / 可执行文件缺失 / spawn 报 OSError）
- When 路由决策层捕获该失败
- Then 以理由码 `launch_fail` 记录该候选失败，派发链上的下一候选

#### BDD-21: infra_error（auth / 网络 / 429 / 进程崩溃）→ 回落下一候选
- Given 首选候选启动了但基础设施失败（未认证 401 循环 / 网络不可达 / 429 限流 / 进程中途崩溃）
- When 路由决策层从结构化输出 / 退出信号识别出该形态
- Then 以理由码 `infra_error` 记录该候选失败，派发下一候选

#### BDD-22: no_parseable_output（跑了但无 gate 能评产出）→ 回落下一候选
- Given 首选候选正常结束（进程退出 / 工具返回）但未产出任何 gate 能评的东西（约定产出文件缺失或空 / 结构化输出为空返回）
- When 路由决策层跑假完成校验（D2）
- Then 以理由码 `no_parseable_output` 记录该候选失败，派发下一候选

#### BDD-23: 全部候选落空 → 默认派发
- Given 候选链所有候选都以三类基础设施理由码失败
- When 路由决策层耗尽候选链
- Then 回落到默认派发（同平台同 model，恒等于本机制未启用）；`dispatch_route` 事件 `final` 记为 `{"cli": "default"}` 且 `candidates_tried` 保留每个候选的失败理由码

### 4.7 完整性不变量（最高危——模型购物完整性洞）

#### BDD-24: 候选回落只在三类基础设施信号时发生
- Given 首选候选产出了 gate 能评的东西，但该产出内容质量差 / 不完整
- When 路由决策层判断是否回落
- Then 不回落（仅 `launch_fail` / `infra_error` / `no_parseable_output` 触发回落，产出质量不是回落信号）

#### BDD-25: 收到任何 gate 能评产出即停止回落
- Given 某候选产出了约定产出文件（非空、格式合法）
- When 路由决策层评估该次派发
- Then 该条路由即判成功、停止尝试后续候选，把产出交 gate

#### BDD-26: gate 判 FAIL → 同一候选正常阶段 retry，绝不换候选，dispatch_route 计数不增
- Given 某候选产出被交给 gate，gate 判 FAIL
- When 阶段进入 retry
- Then retry 在**同一候选**上重跑（不重新解析路由换候选）；本次 retry 不新增 `dispatch_route` 事件（`gate-events.jsonl` 中 `dispatch_route` 事件条数与 gate FAIL 前相同）
- 边界区分：本条是**同阶段内 gate-FAIL retry = 同一候选**；**P5→P4 跨阶段回退**后的 P4 retry 走「机械重新解析一次路由」，见 BDD-51，两者不冲突

#### BDD-27: dispatch_route 理由码枚举仅三值，check-events.py 机械拒绝 gate_fail
- Given `gate-events.jsonl` 出现一条 `dispatch_route` 事件，某 `candidates_tried[].reason` 值为 `gate_fail`（或任何非 `{launch_fail, infra_error, no_parseable_output}` 值）
- When 跑 `check-events.py TASK_DIR`
- Then exit 1（理由码枚举校验拒绝该事件）；合法三值中任一值则 exit 0

### 4.8 候选回落 ≠ 状态机 retry

#### BDD-28: 候选回落不写 state_transition、不动 retries、不触发 PAUSED
- Given 某次派发在候选链上逐级回落了 2 次后在第 3 候选成功
- When 检查该次派发前后的 `.state.yaml` 与 `gate-events.jsonl`
- Then `retries[Pn]` 数值不变、无新增 `state_transition` 事件、状态未进入 PAUSED；只新增 1 条 `dispatch_route` 事件

### 4.9 dispatch_route 事件 + check-events 校验端

#### BDD-29: dispatch_route 事件写入 gate-events.jsonl 且复用既有哈希链
- Given 一次发生了回落的派发
- When 路由决策层写 `dispatch_route` 事件
- Then 该事件行 `prev_hash` == sha256(上一行原始文本)，`ts` 单调不减；`check-events.py` 第 3-5 条哈希链 / ts 审计 exit 0

#### BDD-30: check-events.py 认 dispatch_route 为已知合法事件类型
- Given `gate-events.jsonl` 含合法 `dispatch_route` 事件（理由码合法、字段齐全）
- When 跑 `check-events.py TASK_DIR`
- Then exit 0，不把 `dispatch_route` 判为「非法未知 event」；既有 `test_check_events.py` 用例全部零改动仍绿

### 4.10 cli: native 各平台执行

#### BDD-31: cli: native on Claude Code — Task 单次调用传 model
- Given 候选 `{cli: native, model: haiku}`，主 Agent 在 Claude Code 平台
- When 路由决策层算出目标 model 后，驱动会话按铁律 1 启动 subagent
- Then `--output-format json` 的 `modelUsage` 字段显示的实际 model，与候选 `model: haiku` 经档位/别名解析后的目标一致，且非父会话继承 model；驱动会话侧无自由裁量（目标 model 由决策层全量算好）

#### BDD-32: cli: native on OpenCode — 命名 subagent 间接路
- Given 候选 `{cli: native, model: provider/M-pro}`，主 Agent 在 OpenCode 平台
- When 路由决策层解析该候选
- Then 存在 phase→预配命名 agent 的映射 + 预注册机制，使被派命名 agent 的 `agents.<name>.model` = `provider/M-pro`；子代理实际跑该配置 model（非父会话 model）

### 4.11 跨 CLI 子进程 spawn + 结构化输出解析

#### BDD-33: claude-code 子进程 spawn + JSON 输出解析判成败
- Given 候选 `{cli: claude-code, model: X}`（子进程形式）
- When 路由决策层 spawn `claude -p --output-format json --model X --dangerously-skip-permissions <ctx路径>` 并解析输出
- Then 用 `stop_reason == "end_turn"` 判正常结束、`modelUsage` 确认实际 model；`stop_reason` 非 `end_turn` 或输出为空 → 判失败进回落

#### BDD-34: codex 子进程判成败必须解析事件流、不靠退出码
- Given 候选 `{cli: codex, model: X}`，且构造一个「进程 exit 0 但实际失败」的真实终态样本（如账号不支持的 model → `turn.failed{status:400}` 却 exit 0）
- When 路由决策层解析 `codex exec --json` 事件流
- Then 依据 `turn.completed` vs `turn.failed` 判成败（不依据退出码）；该样本被正确判为失败并进回落

#### BDD-35: codex item 级 status:"failed" 与 turn.failed 是两层
- Given 一个真实 Codex `--json` 样本，其中某 `payload.item.status == "failed"`（携带 `exit_code`）但该 turn 整体 `turn.completed`
- When 路由决策层解析该事件流
- Then 按 P2 明确取的那一层判定（turn 层 vs item 层）；构造样本的已知正确 verdict = 「该 turn 整体成功」，路由决策层对该样本的解析结论须等于该 verdict（不因两层混淆把整条 `turn.completed` 的 turn 误判为失败、也不因某 item `status:failed` 就换候选）

#### BDD-36: opencode 子进程 + 空返回判定
- Given 候选 `{cli: opencode, model: provider/M#variant}`，构造一个失效 provider 的空返回样本（只有头行、无 assistant 内容、exit 0）
- When 路由决策层解析 `opencode run --format json` 输出
- Then 用 `step_finish.part.reason == "stop"` 判正常；空返回（无 `text` part / 结构化 Error JSON）被判失败并进回落

### 4.12 tmux 观测层（P4c，不通过不影响 P4a/P4b）

#### BDD-37: which tmux 决定包裹 or 裸跑
- Given 子进程形式派发，且（场景 A）`which tmux` 成功 /（场景 B）失败
- When 路由脚本启动子进程
- Then 场景 A：`tmux new-session -d -s <命名空间-task-phase-ts> '<cmd> | tee <capture>'`，capture 文件被脚本 tail；场景 B：直接裸跑子进程；两场景的 `dispatch_route` 留痕与 gate 结果逐字节一致

#### BDD-38: tmux session 退出倒计时 + 有 client 不强杀
- Given tmux 包裹的子进程已跑完，wrapper 进入 N 秒退出倒计时（N 默认 ≈15、可配）
- When 路由脚本清理：`tmux list-clients -t <session>` 为空 / 非空
- Then 为空 → 直接 `kill-session`；非空 → 不强杀、让倒计时自然收尾；wrapper 异常未退出且超过 `N + 余量`（余量具体秒数 P2 定值，建议 ≥10s）→ 兜底强杀

### 4.13 回归证明（零改动 + 不配置 = 逐字节现状）

#### BDD-39: gate / 状态机 / phases.yaml 结构零改动
- Given 本任务全部改动已提交
- When 对比改动前后的 `agate/scripts/check-gate.py` / `agate/scripts/check-state-transition.py` / `agate/rules/phases.yaml` / 状态机定义（`state-machine.md` 结构化部分）
- Then 这四者逐字节不变；`agate-dispatch.py` 的既有 dispatch-context 渲染产物（`test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py`）零改动仍绿

#### BDD-40: 不配置 = 逐字节现状
- Given 仓库无 `dispatch-routing.yaml`、无机器级绑定文件、协议出厂默认全 `standard`
- When 跑完整一轮 P1→P8 派发
- Then 每个阶段的派发方式、产出、`gate-events.jsonl`（除不产生任何 `dispatch_route` 事件外）与本机制引入前一致；`dispatch_route` 事件条数 = 0

#### BDD-41: dispatch-protocol.md 新节显式写「gate 不认谁生产的」
- Given 本任务对 `dispatch-protocol.md` 的新增节
- When 检查该节正文
- Then 含一句显式声明「gate 判定只认产出文件 + exit code，不认谁生产的」+ 「候选回落 ≠ 状态机 retry」+ 「gate FAIL 绝不换候选」两条完整性不变量 + 「查表 → 派首选 →（基础设施失败）逐级回落 → 再派发」步位于铁律 1 之前

### 4.14 routed-away judge verdict 平台无关性（P4b 核实项）

#### BDD-42: 路由到子进程的 judge，其 verdict 落 task dir 后 P6.5 gate 平台无关通过
- Given P6.5 judge 被路由到 codex 或 opencode 子进程，judge 把 `P6.5-judge-verdict.md` + 证据写入 `TASK_DIR`
- When 主 Agent 跑 `check-gate.py P6.5 TASK_DIR`（= `check-judge-verdict.py` + `check-events.py`）
- Then exit 0（两校验器纯 `TASK_DIR` 文件解析、不读平台 transcript，平台无关）；`check-judge-verdict.py` / `check-events.py` 两脚本本任务零改动

### 4.15 与既有派发机制的交互

#### BDD-43: 五模式并行批——每个并行 subagent 各自独立解析路由
- Given P4 用并行模式（模式 3）同时派多个 subagent，其中 2 个是同 role 的并行分片
- When 各并行 subagent 解析 `(phase,role)` 路由
- Then 每个 subagent 独立解析；同 role 的并行分片解析到同一条路由；不同 role 的并行 subagent 各自按自己的 `(phase,role)` 解析

#### BDD-44: 自主再派发的子任务不走路由表
- Given 某执行角色在授权范围内自主再派发一个子任务（RM-AG0055）
- When 该子任务被启动
- Then 不解析 `dispatch-routing.yaml`，继承父的实际 cli/model；无 `dispatch_route` 事件产生

#### BDD-45: 单 Agent 模式路由为 no-op 且显式声明出范围
- Given `executor_env.has_task_tool: false`（如 Claude Project 会话）
- When 进入任一阶段
- Then 无派发动作发生、路由为 no-op；`dispatch-protocol.md` / design-note 显式写「单 Agent 模式下路由不适用」

### 4.16 design-note 修订 + roadmap 回写

#### BDD-46: design-note 配置落点 + 核心循环按 2026-09-09 定案重写
- Given `docs/design-notes/design-dispatch-routing.md` 修订后
- When 检查头部「做什么」+ §2.1 + §2.2
- Then 配置落点不再写 `agate/rules/dispatch-routing.yaml`（改三层落点、项目级文件在 `agate-workspace/`）；核心循环不再写「按序探测」（改 try-and-fall：查表 → 派首选 → 基础设施失败逐级回落 → 默认派发）
- 注：两轴/key/缓解标注见 BDD-52；两条完整性不变量 + per-machine 见 BDD-53

#### BDD-47: roadmap RM-AG0060 长描述旧措辞回写
- Given `agate-workspace/roadmap/roadmap.md` 的 RM-AG0060 行修订后
- When 检查其长描述
- Then 不再含 `rules/dispatch-routing.yaml` 与「按序探测」字样；与 design-note 定案一致（try-and-fall + 两轴 + 项目级落点）

### 4.17 DEBT0039 文档边界澄清（SCOPE+ 用户批准并入，承接 closure_criteria）

#### BDD-48: architect.md「批次设计」节含「补协议文档正文 = P4」的显式边界措辞
- Given `agate/assets/execution-roles/architect.md` 修订后
- When 在「批次设计」节 grep 边界措辞
- Then 该节存在一句显式说明「补协议文档正文（`platform-notes.md` / `SETUP.md` / phase-cards 等）= P4 实现工作，批次执行阶段标 P4；P7 只做跨文件一致性验证、不 author 文档内容」（关键串 grep 命中）

#### BDD-49: dispatch-protocol.md「派发编排机制」节显式区分 author 内容（P4）vs 一致性验证（P7）
- Given `agate/dispatch-protocol.md` 修订后
- When 在「派发编排机制」节 grep 该区分措辞
- Then 该节存在一句显式区分「author 文档内容 = P4 / 跨文件一致性验证 = P7」（关键串 grep 命中）；节标题「派发编排机制」仍存在

#### BDD-50: 全量 consistency 改后仍 0 ERROR（回归）
- Given 本任务全部改动（含 BDD-48/49 的两处文档修订）已就位
- When 跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
- Then exit 0（0 ERROR）

### 4.18 P5→P4 回退路由 + design-note 定案重写（拆分补充）

#### BDD-51: P5→P4 跨阶段回退后 P4 retry 重新机械解析一次路由
- Given P5→P4 回退发生、P4 进入 retry
- When 路由决策层解析该次派发
- Then 重新机械解析一次 `(phase,role)` 路由（按当时候选可用性落候选，可能与回退前不同候选），**不注入**「上次失败 → 升档 / 换更强 model」逻辑；与 BDD-26 的「同阶段内 gate-FAIL retry 用同一候选」不冲突（本条是跨阶段回退、BDD-26 是同阶段内）

#### BDD-52: design-note 含 tier + effort 两正交轴 + (phase,role) key + 弱/强缓解标注
- Given `docs/design-notes/design-dispatch-routing.md` 修订后
- When 检查头部 + §2.1/§2.2/§2.3 相关表述
- Then 含 `tier` + `effort` 两正交轴 + `(phase,role)` key（role 可选）；`cli: native` 明确标为**弱缓解**、跨 CLI 起子进程标为**强缓解**；含「自动化不对称」说明（子进程形式可端到端自动化 / `native` 形式启动仍由驱动会话代发但零判断）

#### BDD-53: design-note 含两条完整性不变量 + per-machine 机会式声明
- Given `docs/design-notes/design-dispatch-routing.md` 修订后
- When 检查正文
- Then 含「候选回落 ≠ 状态机 retry」与「gate FAIL 绝不换候选」两条完整性不变量的显式表述；含「routing 是 per-machine 机会式、不追求跨机可复现（只有抽象 `(phase,role)`→档位映射可 commit 共享）」的显式声明

---

## 5. 待确认清单

`[NO_NEED_CONFIRM]` —— 无真无方向、需人定夺的阻塞项。以下为**有倾向、可由主 Agent 直接采纳**的建议项（`[SUGGEST:]`，不阻塞）：

- `[SUGGEST: tier 三档命名用 bulk / standard / deep，理由 对齐用户 2026-09-09 类比（Anthropic haiku/sonnet/opus）+ design-note §7 事项 1 提议；语义画像 bulk=高吞吐低成本 / standard=继承主 Agent 当前 model 原生派发 / deep=高能力复杂判断]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）
- `[SUGGEST: {cli: native, model: null} 合法，null = 该 CLI 当前默认 model，与 design-note §2.1 P6.5 示例一致；schema 校验器放行 model: null]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）
- `[SUGGEST: 档位定义块与 (phase,role) 映射块在同一 YAML 文件内用顶层 key 分隔（如 tiers: 与 routes:），MVP 合并协议本体①与项目级③为单文件 + 内联档位；是否真拆出机器级档位文件（②）由 P2 按「多机可移植性是否真需求」定，倾向 MVP 不拆]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）
- `[SUGGEST: 三层配置优先级 = 项目级直接值覆盖 > 项目级档位映射 > 机器级绑定 > 协议出厂默认；机器级同名档位键后写覆盖先写。P2 在设计里写死这条合并规则]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）
- `[SUGGEST: 决策 CLI 落点扩 agate-dispatch.py 新增子命令（如 agate dispatch route <phase> <role>），与 RM-AG0054 的 agate dispatch（渲染 dispatch-context）串联为两步、不合并；不新增 agate-route.py]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）
- `[SUGGEST: routing schema 静态校验器新增为独立脚本 agate/scripts/check-dispatch-routing.py，不塞进 agate/rules/schema 协议 schema 体系；挂载时机由 P2 定（倾向 SELF-GATE 链 + 可选 pre-commit）]` （已采纳 by 主 Agent，2026-09-09，作 P2 设计输入）

> 主 Agent 采纳倾向项后，把已采纳项追加进 frontmatter `suggest_resolved`（散文标记保留）。
> **状态：6 条 [SUGGEST:] 已全部由主 Agent 采纳（2026-09-09），已写入 frontmatter `suggest_resolved`，作 P2 设计输入；散文标记本体保留不删。**

---

## 6. 能力需求 / 环境声明

- **capability_requirements**（详见 frontmatter）：
  - `three-cli-installed-authenticated` → **available**（本机 Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4 已装已认证）
  - `opencode-bug2-repro` → **available**（本机可直接复现：配命名 agent → 父会话交互式切 model → 再派该 agent → 核对子跑配置 model 还是父的新 model，research §5.2 / §10 步骤具体）
  - `no-frontend-no-vision` → **available**（无 UI / 渲染产出，无 vision 需求；P1 gate vision 硬拦仅 `domains` 含 frontend 时触发，本任务 `domains: [backend, cli]`）
  - **无 `status: GAP`** —— 无 `[CAPABILITY_GAP]`。
- **verification_env**：三 CLI + tmux 本机就绪（均已认证）。**唯一环境不可得项** = Codex API-key 账号 model 阵容（V8，research §11 第 5 项）—— 本机 ChatGPT 账号环境不可得，**非阻塞、登记待补**（TAG0033 已实测 `spawn_agent` schema + ChatGPT 账号 model 枚举，本任务直接引用 `TAG0033/retrospective.md` + `platform-notes.md` Codex 章，不重测）。
- **verification_env_budget**：止损轮次 2（独立计数，不占 `retries[P5/P6]`）；仅适用于 V8 一项，其余真机项本机可做。轮次追踪由主 Agent 在 P5/P6 dispatch-context 接续记录。
- **判别口诀核对**：三 CLI「已装已认证」是环境就绪状态（走 `verification_env`），不是 agent 能力缺口；OpenCode bug② 复现是「本机可做的真机测试」，非「换更强模型才能做」——归 available，不标 supplementable/GAP。
- **judge**：`.state.yaml` 已有 `judge.enabled: true`（P1 created 2026-09-09 ≥ `judge_required_since` 2026-08-22 机制强制），无需改，此处提一句「已启用」。
- **requires_minimal_validation: true**（隐含）：本任务重度依赖三平台外部行为（子进程结构化输出终态、OpenCode 命名 subagent model 继承、Codex 两层 status、tmux 生命周期）——P2 architect 须产出 `minimal_validation:` 块且 result = confirmed，并**主动构造** `turn.failed` / item `status:failed` / 空返回 / 非 0 退出各终态的真实样本（TAG0033 F1 / DEBT0035 教训：不能只读已有会话）。

---

## 7. 裁剪说明（phases）

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]` —— **全阶段不裁**。逐阶段理由：

| 阶段 | 走 / 裁 | 理由 |
|---|---|---|
| P1 | 走 | 需求基线（本文件） |
| P2 | 走（不可裁） | 改协议本体 + 三层配置 + 完整性不变量高危，须方案设计 + 独立评审；P2 须声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial}` |
| P3 | 走（不可裁） | 新增 schema 校验器 + `dispatch_route` 理由码校验 + 回归证明，TDD 先写红 |
| P4 | 走（不可裁） | 实现，内部 P4a（配置路由核心 + `cli: native`）/ P4b（跨 CLI 子进程 + routed-away judge 核实）/ P4c（tmux，低优先可整体切除）串行子批。**DEBT0039 的两处纯文档边界澄清（`architect.md`「批次设计」节 + `dispatch-protocol.md`「派发编排机制」节）= P4 author 工作**（不是 P7）——正是 DEBT0039 要澄清的那条边界，本任务自身也据此把该批标 P4 |
| P5 | 走（不可裁） | 三平台真机验证 + 回归测试全绿 |
| P6 | 走（不可裁） | 逐条 BDD 验收 |
| P7 | 走（不可裁） | 改协议本体 + SELF-GATE，`ceremony: standard`（不薄化，改协议本体 + 完整性不变量高危不适合薄化），P7 一致性检查跨 `dispatch-protocol.md` / `agate-dispatch.py` / `check-events.py` / rules 档位词表 / design-note 交叉核对 |
| P8 | 走（不可裁） | 触发 SELF-GATE，`P7` 不可裁；roadmap RM-AG0060 回写 done（P8 gate 硬校验 RM-AG0043） |

- **`ceremony: standard`**（显式，不薄化）。**不声明 `dispatch_plan`**（P2 architect 字段，P1 不写）；正文注明 P2 须声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial}`。
- **DEBT0037 已知手动步（P2 排期预留）**：本任务 `dispatch_plan` = static-batch 多提交阶段，P4a/P4b/P4c 分批 commit 会命中 `check-gate.py P4` 完整度判据（暂存区有非 md/yaml 文件；某批已 commit、暂存区空时 exit 1）→ `agate-next.py` 拒绝推进 → 需主 Agent 手动 `_advance` + 补 `state_transition` 事件（TAG0033 P4→P5 两次即如此）。若 DEBT0037 在本任务推进前修复则直接受益。
- **P4c 可整体切除**：tmux 观测层若目标环境验证不通过（外部评审 W2：本会话 WSL2 + tmux 3.4 非容器/CI/物理机），停在「定稿 + 待落地验证」、不阻塞 P8，不影响 P4a/P4b 验收。
- **`[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]` 边界约束**：DEBT0039 并入范围**仅限**两处纯文档边界澄清 —— `agate/assets/execution-roles/architect.md`「批次设计」节 + `agate/dispatch-protocol.md`「派发编排机制」节，写清「补协议文档正文 = P4 / 跨文件一致性验证 = P7」。**不扩到其它 DEBT、不改任何脚本 / gate 逻辑**。measures = BDD-48/49/50。P8 收尾：DEBT0039 置 `status: closed`、`task_id: null` → `task_id: TAG0034`。

---

## 8. frontmatter 声明说明（写在文件头，不在正文重复）

- `risk_level: medium` —— P0-brief 定「epic 拆走 Codex 接入后按五维评级 ≈ medium」，同意（决定 P2 评审强度）。
- `phases: [P1, P2, P3, P4, P5, P6, P7, P8]` —— 见 §7。
- `packages: [agate-scripts, agate-rules, agate-docs, agate-tests]` —— `agate-scripts`（`agate-dispatch.py` / `check-events.py` 扩展 + 新 schema 校验器）；`agate-rules`（`agate/rules/` 下新增档位词表文件）；`agate-docs`（`dispatch-protocol.md` 新节 + `SETUP.md` + `platform-notes.md` + design-note 修订 + roadmap 回写 + **DEBT0039 并入的 `agate/assets/execution-roles/architect.md`「批次设计」节 —— 归 `agate-docs`，纯文档措辞，无需独立 package 项**）；`agate-tests`（`agate/tests/` 新增 pytest）。
- **SCOPE+ 来源登记**：`[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]`（§1）—— 已批准项、非待确认，§5 仍 `[NO_NEED_CONFIRM]`。DEBT0039 工作尚未完成，故不写入 frontmatter `scope_resolved`（该字段语义为「已解决」，由 P8 收尾回写）。
- `domains: [backend, cli]` —— 无 frontend / mcp / security；`cli` 因决策落 `agate-dispatch.py` CLI 家族 + 三平台子进程 spawn。
- `dispatch_plan` —— P2 architect 产出字段，P1 不写（见 §7 注明的目标值）。

---

## 9. 下游影响

- **P2**：依赖 `risk_level: medium` + `domains: [backend, cli]` 决定评审角色（改协议本体 → protocol-alignment-review；C8 域触发）；`packages` 作方案范围；§3 同类扫描 9 组作影响面梳理输入（逐级细化，不重复劳动）；§6 `requires_minimal_validation` → `minimal_validation` 块必做。P2 须声明 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial}`。
- **P2（DEBT0039 边界措辞）**：architect 起草 BDD-48/49 的边界措辞时，可引用两个先例（DEBT0039 evidence 里有指针）—— TAG0030（doc-assertion 审计 P3 写红、正文 P4 补绿）与 TAG0033 复盘（protocol-docs 批被 architect 误标 P7、主 Agent 拉回 P4）；措辞落点 = `architect.md`「批次设计」节 + `dispatch-protocol.md`「派发编排机制」节。
- **P3**：BDD-1~6 / 27 / 39 转测试运行器可读的红灯用例；BDD-48/49 是纯文档断言（grep 措辞），BDD-50 是 consistency 回归，按 TAG0030/TAG0033 先例走 P3 写红、P4 补绿或直接 P4 author + P5/P6 验证（P2 定）。
- **P4**：P4a/P4b/P4c 分批 commit，注意 DEBT0037 手动步。**DEBT0039 两处纯文档修订（`architect.md` + `dispatch-protocol.md`）= P4 author 工作**，随对应批提交。
- **P6**：逐条对照本文件 53 条 BDD（PASS/FAIL 总数 ≥ 53）。
- **P7**：`packages` 声明做跨文件一致性核对；改动面文件清单（`dispatch-protocol.md` / `agate-dispatch.py` / `check-events.py` / rules 档位词表 / `SETUP.md` / `platform-notes.md` / `architect.md` / design-note / roadmap）交叉引用检查。
- **P8**：roadmap RM-AG0060 回写 done；**DEBT0039 置 `status: closed`、`task_id: null` → `task_id: TAG0034`**（tech-debt.md）；**SCOPE+（P4a alignment review A5.3/A7.4，用户 2026-09-09 批准）两条 doc-sync**：① `agate/LIMITATIONS.md` 局限 2 补「部分缓解链」段（含诚实边界句「仍非根治 / 主 Agent 自身选型·横传 model 无外部约束，与局限 3 同构」）；② `agate/adr.md` 补 ADR-013「派发路由 / gate 生产者无关性」（关联 ADR-002 / ADR-006 / RM-AG0060）。P8 dispatch-context 显式列。CHANGELOG `[Unreleased]` 段随 P8 补（`check-changelog.py` 仅 P8 触发）。

---

## 10. P1 基线保护

本文件是需求基线，P2-P8 不直接修改。如需变更（含隐含扩展——下游实现事实上扩展了某条 BDD 的判定边界 / 新增豁免条件）：① 主 Agent 显式批准；② 变更处标 `[BASELINE_CHANGE: 理由]`；③ 不改 BDD 的 Given/When/Then 语义；④ 授权内容回写本文件正文，不得只存在于下游 dispatch-context 口头引用（TAG0025 教训）。
