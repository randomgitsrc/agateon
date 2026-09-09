---
phase: P2
task_id: TAG0034
type: review
parent: P2-design.md
trace_id: TAG0034-P2-20260909
status: approved
created: 2026-09-09
agent: plan-eng-review
---

# TAG0034 P2 方案设计评审（plan-eng-review，工程经理视角）

评审对象：`agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（`candidate_count: 2`，`dispatch_plan: {mode: static-batch, batches:[P4a:high, P4b:medium, P4c:low], serial:true}`，`ui_affected:false`，`domains:[backend,cli]`，`packages:[agate-scripts, agate-rules, agate-docs, agate-tests]`）。
评审依据：`P2-dispatch-context-plan-eng-review.md` 派发指引（强制指令）、`P1-requirements.md`（53 条 BDD + §5 六条 suggest_resolved + BDD-10 `[BASELINE_CHANGE]`）、`P1-review.md`（requirements-review approved，retry #1 后）、`P0-brief.md`（scope / out-of-scope / known_risks 12 条）、`agate/assets/review-roles/plan-eng-review.md`、`tech-debt.md` DEBT0037/0038/0039、`docs/design-notes/design-dispatch-routing.md`、`docs/research/cross-platform-dispatch-mechanics.md`，以及对本 worktree 脚本口径的独立查证（见「客观查证摘要」）。

结论：**approved**。阻塞级架构问题 0 项。非阻塞项 7 条 + 测试缺口 3 条，建议 architect 折入或主 Agent 在 P3/P4 择机处理，不构成返工。多方案探索、实现就绪度、`minimal_validation` MV3/MV4/MV7/MV10、模型购物完整性洞 R1（BDD-24~28）、回归硬约束 G、数据流 / 错误边界、状态机完整性、接口契约、测试策略、批次设计、DEBT0039 边界措辞、范围核对——逐项覆盖，锚点见下。

`[PROD_NOT_TOUCHED]`

---

## 客观查证摘要（P2-design 的事实陈述已在 worktree 独立核实）

- `agate/scripts/check-maintainability.py:_load_config`（88-148 行）：四档兜底范式（文件不存在→默认；`import yaml` 失败→默认+stderr；`not isinstance(cfg, dict)`→默认；单键类型坏→该键默认+stderr WARNING）——P2 §3.3 / §2「全兜底加载器逐字参考」的参照对象存在且形态与描述一致。
- `agate/scripts/check-events.py`（125 行）：7 条审计链，第 7 条「未知 event 类型不拦截（向后兼容；gate_run/judge_verdict/state_transition 为已知类型）」；逐行 `ev.get("event") == "judge_verdict"` 分支模式在 104-110 行——P2 §3.8 M6「在逐行循环内加 `if ev.get("event") == "dispatch_route":` 分支」落点属实，追加第 8 条不触及第 1-7 条与哈希链算法。MV8「含 `dispatch_route` 的账本现状 exit 0」与第 7 条一致。
- `agate/scripts/agate-dispatch.py`（248 行）：`main()` 从 `args = sys.argv[1:]`、`phase = args[0]`、`if phase not in _PHASES: exit 1` 起分派；`route` 作为首位参数会被 `_PHASES` 校验拒绝，故 P2 §3.5「`main()` 顶部加 `argv[1]=="route"` 分支、须在 phase 校验之前」是可落地的新增分支，无 `route` 参数时 `_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER`（`<!-- CARD-SOURCE: agate-dispatch.py`）/ `generated_by` 路径逐字节不动。§1.2「既有渲染路径不改」成立。
- `agate/scripts/check-gate.py:_gate_p2_dispatch_plan`（742 行起）：校验 `mode ∈ {single, static-batch, parallel, recon-then-split, serial}`、`parallel_limit ≥1`、`static-batch/parallel` 时每批 `id`+`complexity ∈ {low,medium,high}`、批数 ≤ `parallel_limit`。P2 的 `dispatch_plan`（3 批 ≤ 3，complexity 合法，多出的 `serial: true` 不在契约内、被忽略）通过校验。
- `agate/assets/execution-roles/architect.md:209`「## 批次设计（强制节，TAG0014）」节存在——§4.3 草稿① / M8 锚点有效。硬规则「high 复杂度必须拆分——任一维度 high → 必须设计拆批（模式 2/3/4/5），不允许单发」+「high 复杂度不拆批会被 P7 一致性检查捕获为 DEVIATION」原文确认。
- `agate/dispatch-protocol.md:502`「## 派发编排机制」节存在，为「subagent 派发编排的权威来源」——§4.3 草稿② / M7 锚点有效；铁律 1（15-24 行）「派发 subagent，动词是派发不是执行」原文确认，M7「新节在语义顺序上位于铁律 1 之前」表述可落地。
- `docs/design-notes/design-dispatch-routing.md` 头部「做什么」+ §2.1 现含旧措辞 `rules/dispatch-routing.yaml` / 「按序探测」/ `{cli, model}` 二元——P2 §9 / M12 / BDD-46/47/52/53 的回写目标属实。
- `docs/research/cross-platform-dispatch-mechanics.md` §6.1/§6.2/§6.3/§6.4：三平台结构化输出字段（`stop_reason`=`end_turn` / `turn.completed` vs `turn.failed` + `item.type:error` / `step_finish.part.reason`=`stop`）+ 「Codex 退出码不可靠必须解析 `--json`」+ D2 假完成校验建议——与 P2 §3.7 判定表逐格对应。
- `tech-debt.md`：DEBT0037（P4 多提交阶段判据）`status: open`、DEBT0039（批次执行阶段标注）`status: open`、`closure_criteria` 三条与 P2 §4.2/§4.3 承接一致。
- `[PROD_NOT_TOUCHED]`：本次评审仅在 worktree 内读；写入仅 `P2-review.md` + `P2-progress.md`（本任务目录内）。主 checkout / `~/.agate` 未触碰。

---

## 架构问题（阻塞级）

**无。**

模型购物完整性洞（R1，最高危）在 §3.7 循环 + §3.8 M6 + §3.9 BDD-26 三处机械强制，未发现「产出质量差也回落」或「gate FAIL 换候选」的口子（详见下方「R1 完整性不变量专项」）。回归硬约束 G（§1.2）覆盖面完整、逐条有「看起来该改 vs 为什么不改」。数据流两步串联（§3.1/§3.5）「驱动会话零判断」衔接成立。故无阻塞级问题。

---

## 架构问题（非阻塞）

### N1 — §3.6 与 §8 对 `check-dispatch-routing.py` 是否进 `gate_commands` 表述矛盾（须在冻结前对齐）

- 定位：`P2-design.md` §3.6 末段「**不进 `gate_commands`**（该文件是项目级配置、非本任务测试对象）」 vs §8 `gate_commands` 块内 `P5_routing_schema: "python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml"` + §8 说明「`P5_routing_schema` = routing schema 静态校验器（BDD-1~6，跑本任务提交的 `dispatch-routing.yaml` scaffold）」。
- 问题：`gate_commands` 在 P2 固化、P3-P6 不可改（P2 卡「下游影响」）。两处一旦冻结不一致，P4/P5 执行方按 §8 跑、按 §3.6 理解，判定口径分叉。
- 建议：以 §8 为准（P5_routing_schema 作 scaffold 冒烟校验、BDD-1~6 的真正 fixture 覆盖在 §3 M11 pytest 内是恰当分工），把 §3.6 末段改为「不作为 `dispatch-routing.yaml` 后续任意编辑的常驻 gate（非协议本体，同 `maintainability.yaml`）；本任务 P5 内以 `P5_routing_schema` 对提交的 scaffold 跑一次冒烟」。措辞对齐后 §3.6「挂载时机 SUGGEST #6 留 P2 定」即闭合。

### N2 — §3.3 `resolve` 伪代码 `chain` 变量在 tier 分支未初始化，返回结构不统一

- 定位：`P2-design.md` §3.3 算法块。步骤 1 仅在 `entry has 'candidates'` 分支给 `chain` 赋值；`tier` 分支与出厂默认分支只设 `tier` / `effort_override`，未设 `chain`。步骤 3 `if not chain:` 在 `tier` 路径下引用未定义名。另：步骤 2/3 `return {form:'default', ...}` 与步骤 4 `return {chain: chain}` 两种返回形状不同，而 §3.7 首行 `chain = resolve(phase, role).chain` 无条件取 `.chain`。
- 问题：伪代码级精度缺口。implementer 能推断意图，但「无需额外步骤计划即可自主实现」的门槛下，返回契约不统一会诱发实现分歧（`.chain` 在 `form=default` 分支为 `None` 还是 KeyError）。
- 建议：步骤 1 显式 `chain = entry.candidates if entry has 'candidates' else None`；统一返回一个对象 `{form, chain, model, effort}`（`form ∈ {default, chain}`，`form=='default'` 时 `chain=None`），§3.7 首行改为「`r = resolve(...); if r.form=='default': 默认派发, 无循环; else: chain = r.chain`」。不影响 schema / BDD 编号。

### N3 — P4a 批相对「单批产出 ≤3」基准偏重，R1 高危不变量与 schema 层、协议正文捆在同一批

- 定位：`P2-design.md` §4.1 批次表 P4a 行 + §4.1 前置检查第 2 项。P4a（complexity: high）产出 = `dispatch-tiers.yaml`（新）+ `dispatch-routing.yaml`（新 scaffold）+ `agate-dispatch.py`（route 核心）+ `check-dispatch-routing.py`（新）+ `check-events.py`（第 8 条）+ `dispatch-protocol.md`（新节）+ pytest，约 6-7 个产出落点，超出 `architect.md`「批次设计」节 /「派发编排机制」任务粒度基准「产出 ≤3」。
- 问题：P2 卡 /`architect.md`「high 复杂度必须拆分」在 plan 层已满足（static-batch 三批，非单发），故非 DEVIATION；但 P4a 内部把「配置 schema 层（M1 词表 / M3 校验器 / M2 scaffold）」与「路由引擎层 + R1 完整性不变量（M4 resolve+try-and-fall / M6 check-events 第 8 条 / M7 协议正文）」压在一次派发里，单 subagent 认知负荷偏高，且 R1 是 known_risks 点名的最高危项。
- 依赖分析（本评审独立核对）：M1→M3（校验器交叉核 `tiers:` 键）、M1→M4（resolve 展开 tier）、M4→M6（第 8 条校验 M4 产出的 `dispatch_route` 事件 schema）。M1/M3/M2 不依赖 M4/M6/M7，可前置为独立子批。
- 建议（非强制，主 Agent / architect 定）：考虑把 P4a 拆为 P4a-1 = {M1 `dispatch-tiers.yaml` + M3 `check-dispatch-routing.py` + M2 scaffold + 对应 pytest}（complexity: medium，schema 层，交付即可跑 `P5_routing_schema`）与 P4a-2 = {M4 route 核心 + M6 check-events 第 8 条 + M7 `dispatch-protocol.md` 新节 + R1 完整性用例}（complexity: high，引擎层，依赖 P4a-1）。若坚持 P4a 单批，§4.1 前置检查第 2 项须补一句「M1/M3/M6 为何不能前置为独立子批」的依据（当前只说明了 M4↔M5 的同文件串行，未说明 schema 层为何必须与引擎层同批）。

### N4 — `dispatch_plan` 用 `mode: static-batch` + `serial: true` 而非 `mode: serial`

- 定位：`P2-design.md` frontmatter line 14 / §4.1。枚举里有专门的 `mode: serial`（串行链），P2 选 `static-batch` 再加非契约子键 `serial: true` 表达串行依赖。
- 问题：`_gate_p2_dispatch_plan` 不校验 `serial` 键（忽略），故不报错；但语义上「静态拆批 + 串行」与「串行链」两种 mode 的区分在此被绕过，P7 一致性检查 / 未来读 `dispatch_plan` 的工具看到 `static-batch` 会默认「可并行到 parallel_limit」。
- 说明：P1 §7 / P0-brief scope 明文要求的目标值就是 `{mode: static-batch, batches:[P4a,P4b,P4c], serial}`，architect 逐字承接、无过错。此条仅记录：`serial: true` 的强制力落在 §4.1「P4a→P4b 串行依赖」的散文声明 + 主 Agent 排期，不在机器字段。若后续 `dispatch_plan` 契约新增 `serial` 语义，本任务应同步。

### N5 — `machine_routes:` 预留顶层键「MVP 恒空、不实现」引入了未用的扩展面

- 定位：`P2-design.md` §3.3 来源表第 4 行、§3.6 顶层 key 清单、§3.3 BDD-15 定死点。
- 问题：`machine_routes:` 作为「未来机器级 default routing」占位，当前恒空、`resolve` 步骤 3 注明「无 `machine_routes` ⇒ 跳过优先级 3」。校验器要为它留放行分支。属轻度 YAGNI——三层优先级序（SUGGEST #4）里「机器级绑定」在 MVP 已由 `tier_bindings:`（tier→候选链展开字典）承载，`machine_routes:` 是第二个「机器级」概念，易与 `tier_bindings` 混淆。
- 建议：MVP 直接不定义 `machine_routes:`（校验器对未知顶层键已给 WARNING 而非 exit 1，未来要加是纯增量）；或在 §3.6 明确「`machine_routes:` 为文档化保留字，校验器 exit 0 放行且不作任何语义」。architect 定。

### N6 — §3.7 `outcome.kind` 四值未显式覆盖「进程挂死 / 无退出」路径

- 定位：`P2-design.md` §3.7 循环 + 判定表 + §1.2「RM-AG0055 命令流机制」行。四值 = `LAUNCH_FAIL` / `INFRA_ERROR` / `NO_PARSEABLE_OUTPUT` / `HAS_OUTPUT`。判定表按「进程退出后解析结构化输出」组织。
- 问题：子进程卡死 / 长时间无输出的场景，`dispatch_once` 何时返回、映射到哪个 `outcome.kind`，§3.7 未画。§1.2 说「存活 / 卡死检测复用 RM-AG0055 + `wait(pid)` / `kill -0`」，但循环体里没有「检测触发 kill → 归 INFRA_ERROR」这一步。
- 建议：§3.7 判定表补一行或在 `INFRA_ERROR` 定义里显式写「卡死检测（RM-AG0055 命令流阈值 / `wait` 超时）触发 kill → `INFRA_ERROR`，携 `reason: infra_error` 回落」。BDD-21 的 `infra_error` 识别形态里已列「进程中途崩溃」，补齐「挂死被杀」即穷尽。

### N7 — §3.7「HAS_OUTPUT」判据「文件非空 + 格式合法」中「格式合法」的边界未钉死，存在完整性洞的侧门风险

- 定位：`P2-design.md` §3.7「回落信号边界（R1 / BDD-24）」段 +判定表三平台 `HAS_OUTPUT` 列「+ 产出文件非空」。
- 问题：`NO_PARSEABLE_OUTPUT`（回落）与 `HAS_OUTPUT`（不回落、交 gate）的分界完全压在「文件非空 + 格式合法」。若「格式合法」被实现成「内容结构完整度校验」，就等于把一部分质量判断塞回回落路径，R1 不变量出现侧门（「结构不够完整 → no_parseable_output → 换候选」）。
- 建议：§3.7 明确「格式合法 = 产出文件可被解析为期望的 md/yaml 骨架（presence 级，如 frontmatter 可解析、必需锚点标题存在），**不含**内容完整度 / BDD 覆盖度判断；后者一律 gate 负责、走同候选 retry」。与 §3.7 已有的「产出质量差 / 内容不完整 归 HAS_OUTPUT」一句并列写死，堵死实现漂移。

---

## R1 完整性不变量专项（模型购物完整性洞，BDD-24~28，known_risks 最高危）

逐条机械强制核对，结论：设计成立，未发现口子。

- ① 回落只在三类基础设施信号触发：`P2-design.md` §3.7 循环体只有 `LAUNCH_FAIL` / `INFRA_ERROR` / `NO_PARSEABLE_OUTPUT` 三个 `continue` 分支；`HAS_OUTPUT` 分支 `return cand`。「回落信号边界」段明写「产出质量差 / 内容不完整 归 `HAS_OUTPUT`——不回落，交 gate」。与 BDD-24 一致。（配合 N7 把「格式合法」边界钉死则更稳。）
- ② 收到任何 gate 能评产出即停止回落：§3.7 `HAS_OUTPUT` 分支 `write_dispatch_route_event(..., final=cand); return cand`，注释「BDD-25：收到即停，交 gate，不再试后续候选」。与 BDD-25 一致。
- ③ gate FAIL → 同候选正常阶段 retry、`dispatch_route` 计数不增：§3.7「回落信号边界」段 +§3.9 交互表「BDD-26 vs BDD-51」行「同阶段 gate-FAIL retry：不重跑 `agate dispatch route`，用上次成功的同一候选重跑，`dispatch_route` 事件计数不增」。与 BDD-26 一致，并显式与 BDD-51（跨阶段回退机械重解析）区分——正是 P1-review retry #1 收紧的那处张力，此处落到「`agate dispatch route` 无状态、是否重新调用由主 Agent 按 retry 类型决定」的实现层判据，可落地、互不干扰。
- ④ 理由码枚举无 `gate_fail`、`check-events.py` 机械拒绝：§3.8 第 8 条审计链「`reason` 必须 ∈ `{launch_fail, infra_error, no_parseable_output}`；出现 `gate_fail` 或任何其它值 → exit 1」；`dispatch_route` 事件 JSON 样本的 `candidates_tried[].reason` 与 `final` 结构与 `gate_run` / `state_transition` / `judge_verdict` 同构，复用 `append_event` 哈希链（`prev_hash` / `ts` 由既有逻辑填）。与 BDD-27/29 一致。M11 列了「gate FAIL 不触发换候选（关键完整性用例）」+「`gate_fail` 非法理由码被拒」两条专门回归。
- ⑤ 候选回落 ≠ 状态机 retry：§3.8「候选回落不写 `state_transition`、不动 `retries`」+ §1.2 状态机行「不占 `retries[Pn]`、不写 `state_transition`、不触发 PAUSED，只写 1 条 `dispatch_route`」。与 BDD-28 一致。

---

## 测试缺口

### T1 — `resolve` 返回契约的单元测试未在 M11 显式列出「返回形状」断言

- §3 M11 列了「解析顺序 / 三层优先级 + 全兜底 / 档位展开」，§10 完成标志第 2 条列了 8 条 `resolve` 分支，但没有一条覆盖「`resolve` 对 `standard` 短路返回 `{form:'default'}` vs tier 展开返回候选链」的返回结构一致性（对应 N2）。建议 M11 补一条：`resolve` 每条分支的返回对象键集固定、`form` 取值合法。

### T2 — 「挂死 → INFRA_ERROR 回落」无对应用例

- §3 M11「try-and-fall 各失败形态」枚举了「起不来 / auth 错 / 429 / 空产出」，缺「子进程挂死被卡死检测杀掉 → 回落 `infra_error`」（对应 N6）。BDD-21 识别形态含此场景但 M11 未落测试点。建议 M11 的 try-and-fall 用例集补「模拟 `wait` 超时 / RM-AG0055 阈值触发 kill」一例。

### T3 — `dispatch_route` 事件与 `check-events.py` 第 8 条的「合法三值全绿」正向用例只提了 BDD-30，未提「三值各自单测」

- §3.8 / M11 保证了「`gate_fail` → exit 1」「既有 `test_check_events.py` 零改动仍绿」，但对 `launch_fail` / `infra_error` / `no_parseable_output` 三值分别构造一条合法账本、断言 exit 0 的正向覆盖没写明。建议 M11 明确「第 8 条：合法三理由码逐一 exit 0 + 混入第四值 exit 1」的参数化用例。

---

## 锁定决策（本次评审确认、后续阶段据此执行）

1. **候选方案 A（MVP 双文件）锁定**：`agate/rules/dispatch-tiers.yaml`（协议本体①，SELF-GATE）+ `agate-workspace/dispatch-routing.yaml`（②③合并，`tier_bindings:` + `routes:` 两顶层 key，非 SELF-GATE）。机器级②不拆出独立文件。判据「团队 / 多机可移植性是否真需求」→ 当前无消费方（P0-brief out-of-scope 明确排除跨机可复现），候选 B 的唯一增益正是被排除目标 → YAGNI；A 的 SELF-GATE 边界与 H 硬约束逐字一致；A 可平滑升级到 B（加载器按层合并，纯机械重构）。理由自洽、B 被 steelman（§2「B 在此轴上确实优于 A」段给了具体成立条件与代价），非稻草人。`agate-route.py` 独立脚本由 SUGGEST #5 排除、不作候选，成立。
2. **`resolve` 优先级序锁定**（BDD-15/18「P2 定」留白闭合）：项目级直接值 `candidates:` > 项目级档位映射 `tier:` > 机器级绑定 `tier_bindings:`（tier→候选链展开字典）> 出厂默认（`FACTORY.defaults` → `standard`）。`tier_bindings:` 同名档位键 = 后写覆盖先写（last-write-wins，与 `yaml.safe_load` 行为一致），校验器出 WARNING 不 exit 1。
3. **`standard` 语义锚锁定**：不经 `tier_bindings` 展开，`resolve` 步骤 2 短路返回 `{form:'default', model:<主 Agent 当前 model>}`；`tier_bindings` 内定义 `standard` 属非法（校验器 WARNING）。回归用例 = 无任何配置跑完整 P1→P8、`dispatch_route` 条数 = 0（BDD-40）。这是「不配置 = 逐字节现状」不变量的实现锚。
4. **Codex 判成败「turn 层为准」锁定**（BDD-35）：`turn.completed` 存在且无 `turn.failed` / 顶层 `error` → 成功；item 级 `status:"failed"`（携 `exit_code`）永不触发回落；退出码仅弱佐证（MV3 本版 0.153.4 `turn.failed`→exit 1、MV4 item `status:failed`→`turn.completed`→exit 0，两向都不稳）。MV3/MV4 为主动构造的真机终态样本，满足 DEBT0035 / TAG0033 F1 教训要求。
5. **BDD-38 tmux 兜底余量 = 10 秒锁定**：force-kill at `N + 10s`（`N` 默认 15s）；清理逻辑先 `tmux has-session` 判断、容忍 `kill-session` 对已消失 session 的 exit 1（MV11 实测）。P4c 可整体切除，目标环境须在其自己 tmux 版本复跑 research §10（R10 / 外部评审 W2）。
6. **effort 轴按能力探测映射锁定**（BDD-10 `[BASELINE_CHANGE]`，用户 2026-09-09 批准）：路由决策层构造命令前探测 `claude --help` 是否含 `--effort`——含则映射 `--effort <e>`（`e ∈ {low,medium,high}`，schema 只放行三值即三平台交集）、不含则省略不报错。判据 key off 能力探测，**不硬编码版本号**；P2-design 全篇（§3.4 / §5 MV10 / §7 `effort_flag_capability_probe` / §9 项 4 / §10.6 / M10）措辞统一为「2.1.266 [实测] 有 / 2.1.263 [实测] 无 / 引入版本未核实」，无残留把中间版本当事实的表述。MV7 的 OpenCode bug② 交互式 TUI 切换路径如实标注为「[实测机制一致 + 交互路径推断]」（用 `opencode run -s -m` 程序化 session model 覆盖近似，非逐字复现交互切换），证据强度未被写成「已完全实测」——诚实。
7. **DEBT0039 两处文档批标 P4（不标 P7）锁定**：M7（`dispatch-protocol.md` 新节）/ M8（`architect.md` 批次设计节措辞）/ M9（`SETUP.md`）/ M10（`platform-notes.md`）/ M12（design-note / roadmap）均为「补 / 改协议文档正文 = P4 author 工作」，随对应批在 P4 提交；P7 只做跨文件一致性验证、不 author。§4.3 草稿① / 草稿② 忠实承接 DEBT0039 `closure_criteria` 三条、只做边界澄清（不扩其它 DEBT、不改脚本 / gate）、引 TAG0030 / TAG0033 先例。本任务自身把 doc 批标 P4 即对 DEBT0039 根因（architect 误标 P7）的自洽演示。P8 收尾：DEBT0039 置 `status: closed`、`task_id: null → TAG0034`。
8. **P4a→P4b 同文件（`agate-dispatch.py`）串行依赖锁定**：M4（route 核心 + JSON 输出契约）在 P4a、M5（subprocess 分支 + 结构化解析）在 P4b；`target` 描述 JSON schema 由主 Agent 在 P4a 返回后固化、P4b/P4c 只增不改。故 `serial: true`、非并行。

---

## 逐项覆盖对照（dispatch-context 评审重点 → 本评审结论位置）

| 评审重点 | 结论 | 锚点 |
|---|---|---|
| 多方案探索（≥2 候选 + 权衡 + 理由自洽，判据轴 = 机器级②是否拆） | 满足 | 锁定决策 1；§2 候选 A/B + 选择理由 4 点 |
| 实现就绪度（P4a/P4b/P4c 无需步骤计划 + files_to_read 覆盖 + §10 13 条对 53 BDD） | 大体满足，2 处精度缺口 | N2（resolve 返回契约）、N3（P4a 粒度）；§6 files_to_read 含行号片段、§10 逐条对 BDD 范围 |
| minimal_validation 真机（MV1~MV11，非「纯代码逻辑」声明） | 满足 | §5 全条 `confirmed` / `refuted`（MV10）；锁定决策 4/6 |
| MV3/MV4（退出码不可靠 + item vs turn 两层，turn 层为准） | 满足，真机样本支撑 | 锁定决策 4；§3.3 R5 / §3.7 判定表注 / BDD-35 |
| MV7（OpenCode bug②，证据强度诚实） | 满足，如实标注 | 锁定决策 6 末；§5 MV7 note |
| MV10 + `[BASELINE_CHANGE]`（能力探测、不硬编码版本号，措辞统一） | 满足，全篇一致 | 锁定决策 6；版本串核查见「客观查证摘要」 |
| 模型购物完整性洞 R1（BDD-24~28，机械强制、无口子） | 成立，未发现口子 | R1 专项五条；N7（格式合法边界建议钉死） |
| 回归硬约束 G / R-not-modify（§1.2 覆盖面 + BDD-39/40 可执行） | 满足 | §1.2 表（phases.yaml 结构+字段 / check-gate / check-state-transition / 状态机 / check-events 1-7 条+哈希链 / check-judge-verdict / check-p6-provenance / agate-dispatch 渲染路径 / RM-AG0055 / RM-AG0054 / dispatch.yaml）逐条有「看起来该改 vs 为什么不改」；BDD-39 逐字节比对 + BDD-40 dispatch_route 条数=0 |
| 数据流 / 错误边界（两步串联 + 三 form 零判断 + outcome.kind 穷尽） | 大体满足，1 处未画 | §3.1/§3.5「零判断保证」成立；N6（挂死路径未映射） |
| 状态机完整性（回落≠retry；BDD-26 vs BDD-51 可落地互不干扰） | 满足 | R1 专项 ③⑤；§3.9 交互表 |
| 接口契约（dispatch_route 事件同构复用哈希链；target JSON P4a 定/P4b 只增不改） | 满足 | §3.8 事件 JSON；§4.1 前置检查跨批共享件；锁定决策 8 |
| 测试策略（unit/回归对 53 BDD；每校验独立 key；P5_e2e 正确省略；分档合理） | 满足，3 处补点 | §8 gate_commands（P3/P5/P5_consistency/P5_events/P5_routing_schema 独立 key，无 && 串接，无 P3_xxx，ui_affected:false 故无 P5_e2e）；T1/T2/T3；N1（check-dispatch-routing 表述矛盾） |
| 批次设计 §4（P4a high 是否再拆；同文件串行；DEBT0039 批标 P4） | plan 层合规，P4a 粒度偏重 | N3、N4；锁定决策 7/8 |
| DEBT0039 边界措辞草稿 §4.3（忠实承接 closure_criteria、只做边界澄清、引先例） | 满足 | 锁定决策 7；§4.3 草稿① `architect.md` / 草稿② `dispatch-protocol.md` |
| 范围核对（越出 P0-brief scope / out-of-scope；§11「无 [SCOPE+]」是否成立） | 成立 | §11；out-of-scope 逐项核对（动态选型 / 续接软信号根治（§1.3 R11 如实登记为缺口、未假装解决）/ 第三方终端工具 / DSH / 局限 3 / RM-AG0055 机制 / RM-AG0054 agate next / probe（§3.7「无 probe」）/ 跨机可复现（§2 选择理由明引为 out-of-scope）/ retry 故意升档（§3.9 BDD-51「不注入升档逻辑」））均未越界；`[NEED_CONFIRM]` 无；`[BASELINE_CHANGE]` 1 处（BDD-10）已登记 |

---

## 技术债

本评审**不新增** DEBT 条目。非阻塞项 N1~N7 均为「P3/P4 落地前在本设计内定点收敛」的措辞 / 精度 / 批次粒度建议，非「先上线、后重构」的架构债。DEBT0037（P4 多提交阶段判据）由 §4.2 作已知手动步排期预留、DEBT0039 由本任务承接闭合，均已在 P2-design 处理。

---

## 门槛映射

- 非阻塞项 7 条 + 测试缺口 3 条，全部可由 architect 折入现稿或主 Agent 在 P3/P4 择机处理，无「候选方案不足 / 多方案未探索 / 完整性不变量有口子 / 回归硬约束漏项 / 范围越界」类根本问题 → **approved**。
- Header `status:` → `approved`（`agate-md-field-set status approved`；`agent` = plan-eng-review ≠ main）。
