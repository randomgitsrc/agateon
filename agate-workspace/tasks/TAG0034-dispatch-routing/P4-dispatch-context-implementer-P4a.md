---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

实现 **P4a 批**（`dispatch_plan` static-batch 第 1 批，complexity: high）：配置路由核心 + `cli: native` + `dispatch_route` 事件 + 协议本体档位词表 + `dispatch-protocol.md` 新节 + DEBT0039 两处边界措辞 + design-note/roadmap 修订。让 P3 的以下测试文件由红转绿（**不改测试本身**）：`test_tag0034_schema.py` / `test_tag0034_resolve.py` / `test_tag0034_tryfall.py` / `test_tag0034_events.py` / `test_tag0034_native.py` / `test_tag0034_interaction.py` / `test_tag0034_docs.py`。`test_tag0034_zero_change.py`（BDD-39/40 回归护栏）须保持绿。`test_tag0034_subprocess.py`（BDD-33~36/42）+ `test_tag0034_tmux.py`（BDD-37/38）留红（P4b/P4c）。产出 `P4-implementation.md`（声明 `implementation_dir`）。

### 实现顺序（P2-review N3 定死：先 schema 层、后引擎层）

**① schema 层（交付即可跑 `P5_routing_schema` 冒烟）**：

- **M1** `agate/rules/dispatch-tiers.yaml`（新，协议本体）—— 按 P2-design §3.2：`schema_version: 1` + `tiers: {bulk, standard, deep}`（每档 `intent:` 语义画像，`standard` 画像写死「恒等于继承主 Agent 当前 model 的原生派发、不经 tier_bindings 展开、保『不配置 = 逐字节现状』不变量」）+ `defaults: {}`（出厂 `(phase,role)`→tier 映射，空 map ⇒ 隐式全 standard）。
- **M3** `agate/scripts/check-dispatch-routing.py`（新）—— routing schema 静态校验器，CLI `check-dispatch-routing.py <yaml路径>`，exit 0 合法 / exit 1 非法。按 P2-design §3.6 校验口径：
  - 顶层 key：`tier_bindings`（可选 dict）/ `routes`（可选 dict）/ `machine_routes`（可选，**文档化保留字**：exit 0 放行、不作任何语义校验）/ `schema_version`；多余顶层 key → WARNING（不 exit 1）
  - `routes` 条目 key：`Pn` 或 `Pn: {role: {...}}`（role 段可选，BDD-3）
  - 每条 route 值：**`tier:` 与 `candidates:` 互斥**，同时出现 → exit 1（BDD-2）
  - `tier:` 值 ∈ `dispatch-tiers.yaml` 的 `tiers:` key 集（交叉核，读同目录 `../rules/dispatch-tiers.yaml`；该文件缺失时降级为「只要非空字符串即放行」+ WARNING）；未知 tier → exit 1
  - `candidates:` = 非空 list，每项 `{cli, model, effort?}`：`cli ∈ {native, claude-code, codex, opencode}` 否则 exit 1（BDD-4）；`model` 为字符串**或 `null`**（放行，SUGGEST #2）；`effort`（可选）∈ `{low, medium, high}` 否则 exit 1（BDD-5）
  - `effort:` 也可写在 route 层（与 `tier:` 并列），同枚举校验
  - **`fallback` 字段任意层出现 → exit 1**（BDD-6）
  - `tier_bindings` 条目：key ∈ tiers（含 `standard` → WARNING，不 exit 1）；值 = 有序候选 list（同 `candidates` 项校验）；重复 tier key → WARNING（last-write-wins，§3.3）
  - 坏 YAML / 文件不存在 → **exit 0**（无可校验对象，与全兜底运行时一致）
  - 测试锚点见 `agate/tests/unit/test_tag0034_schema.py`（fixture 运行时构造 yaml，`run_cli` + `python_exe` + `agate_scripts` conftest fixture）
- **M2** `agate-workspace/dispatch-routing.yaml`（新，项目级 scaffold）—— 随本任务提交一份**最小 / 带注释**示例：`schema_version: 1` + 注释说明 `tier_bindings:` 由本机现状填（探测已装 CLI + 各自默认 model）、`routes:` 引用 tier。可以是「几乎全注释、`routes: {}` / `tier_bindings: {}`」的骨架（不配置 = 现状）。**该文件非协议本体、不触发 SELF-GATE**（对齐 `maintainability.yaml`）。`check-dispatch-routing.py` 对它 exit 0。

**② 引擎层**：

- **M4** `agate/scripts/agate_dispatch_route.py`（新，**importable helper 模块**，下划线命名，`agate/scripts/` 下）—— 按 `agate/tests/unit/test_tag0034_{resolve,tryfall,events,native}.py` 的接口契约暴露：
  - `resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model) -> {"form", "chain", "model", "effort"}` —— 完全按 P2-design §3.3 算法（`form ∈ {"default","chain"}`；优先级序 项目级 `candidates:` > 项目级 `tier:` > `tier_bindings:` 展开 > `factory_defaults` → `standard`；`(phase,role)` 命中优先于 `phase` 级；`standard` 短路 `form='default'` / `chain=None` / `model=current_model` / `effort=None`；`tier` 引用但 `tier_bindings` 缺该 tier → `form='default'`；effort 合并：候选自带 `effort` 优先、否则 route 层 `effort`）。**T1（N2）**：每条分支返回对象键集恒为 `{form, chain, model, effort}`。
  - `load_config(workspace_dir) -> (routes, tier_bindings)` —— 全兜底，**逐字参考 `agate/scripts/check-maintainability.py:_load_config`（88-148 行）**四档兜底（目录/文件不存在 → `({}, {})`；`import yaml` 失败 → `({}, {})` + stderr；非 dict / 某键类型坏 → 该键默认 + stderr WARNING）。读 `<workspace_dir>/dispatch-routing.yaml` 的 `routes:` 与 `tier_bindings:` 两顶层 key。
  - `classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None) -> Outcome`（`.kind ∈ {"LAUNCH_FAIL","INFRA_ERROR","NO_PARSEABLE_OUTPUT","HAS_OUTPUT"}`，`.reason ∈ {"launch_fail","infra_error","no_parseable_output"}` 或 `None`）—— 按 P2-design §3.7 判定表 + `HAS_OUTPUT`「格式合法」定死（**presence 级骨架可解析**：frontmatter 可解析 + 必需锚点标题存在，**不含**内容完整度 / 质量判断）+ 挂死被杀（`killed_reason` 非空 / RM-AG0055 阈值 / `wait` 超时）→ `INFRA_ERROR`。三平台结构化输出字段见 §3.7 判定表（Claude Code `stop_reason`；Codex 事件流 `turn.completed` vs `turn.failed` + 顶层 `error`，**item 级 `status:"failed"` 不改变 kind**，turn 层为准，BDD-35；OpenCode `step_finish.part.reason == "stop"` + `text` part）。fixture 样本在 `agate/tests/fixtures/tag0034_{claude_code,codex,opencode}/`。
  - `build_dispatch_command(candidate, *, ctx_path, effort_supported) -> list[str]` —— 构造子进程 / native 命令。effort 映射：Codex `-c model_reasoning_effort=<e>`（子进程）；OpenCode `--variant <e>`（或 `#<e>` 后缀）；**Claude Code：按 `effort_supported` 布尔——True 加 `--effort <e>`、False 省略（不报错）**（BDD-10 `[BASELINE_CHANGE]`：`effort_supported` 由调用方按 `claude --help` 是否含 `--effort` 能力探测得出，**不硬编码版本号**）。`model: null` → 不传 `--model`。
  - **try-and-fall 循环**（P2-design §3.7）：`for cand in chain: dispatch_once → LAUNCH_FAIL/INFRA_ERROR/NO_PARSEABLE_OUTPUT 三类 continue（记 reason）；HAS_OUTPUT → 写 dispatch_route 事件 final=cand、return；候选耗尽 → 写事件 final={"cli":"default"}、return DEFAULT`。**无 probe**（BDD-19）。**回落只在三类基础设施信号**（BDD-24：产出质量差归 HAS_OUTPUT、不回落）。
  - `write_dispatch_route_event(...)` —— 复用 `agate/scripts/agate_common.py` 的 `append_event`（哈希链 `prev_hash = sha256(上一行原始文本)` / `ts` 由既有逻辑填）。事件 JSON 结构见 P2-design §3.8：`{"event":"dispatch_route","phase":...,"task_id":...,"candidates_tried":[{cli,model,effort?,result,reason?}],"final":{cli,model?},...}`。**不写 `state_transition`、不动 `retries`**（BDD-28）。
- **M4b** `agate/scripts/agate-dispatch.py` —— **新增 `route` 子命令分支**。在 `main()` 顶部、`phase = args[0]` / `_PHASES` 校验**之前**加 `if args and args[0] == "route": return _route_main(args[1], args[2])`（`_route_main` import `agate_dispatch_route` helper）。`_route_main(phase, role)`：读 workspace → `load_config` → `resolve` → 展开候选链 → try-and-fall → stdout 输出单行 JSON `{"cli","model","effort","form","dispatch_context"}`（P2-design §3.1 step 2.6）。**无 `route` 参数时行为逐字节不变**——`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER`（`<!-- CARD-SOURCE: agate-dispatch.py`）/ `generated_by: agate-dispatch.py + 主 Agent` 路径不改。`agate/tests/unit/test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` 零改动仍绿（BDD-39）。
- **M6** `agate/scripts/check-events.py` —— **追加第 8 条审计链**（P2-design §3.8）：在既有逐行循环内加 `if ev.get("event") == "dispatch_route":` 分支——校验每个 `candidates_tried[i].reason ∈ {"launch_fail","infra_error","no_parseable_output"}`，出现 `"gate_fail"` 或任何其它值 → `sys.exit(1)`（走既有错误出口格式）。第 7 条注释「gate_run/judge_verdict/state_transition 为已知类型」补 `dispatch_route`。**不动第 1-7 条 + 哈希链算法 + GENESIS/ts/judge 计数**。既有 `agate/tests/unit/test_check_events.py` 零改动仍绿（BDD-30）。测试锚点 `agate/tests/unit/test_tag0034_events.py`（T3：三合法值 exit 0 + 混入第四值 exit 1）。

**③ 协议正文 + 文档（DEBT0039 / BDD-41/46~49/52/53）**：

- **M7** `agate/dispatch-protocol.md` —— 在「## 派发编排机制」节区域（line ~502 起）**新增子节**「### 派发路由（查表 → 派首选 → 逐级回落 → 再派发）」。含（BDD-41/49）：
  - try-and-fall 步骤描述 + 明确「此步在铁律 1 启动 subagent **之前**插入」
  - 显式一句「gate 判定只认产出文件 + exit code，**不认谁生产的**」
  - 两条完整性不变量：①「候选回落 ≠ 状态机 retry」（不占 `retries[Pn]`、不写 `state_transition`、不触发 PAUSED、只写 `dispatch_route`）；②「gate FAIL 绝不换候选」（收到任何 gate 能评产出即停止回落；gate FAIL → 同一候选正常阶段 retry；`dispatch_route` 理由码枚举无 `gate_fail` 值、`check-events.py` 机械拒绝）
  - `cli: native` 弱缓解 / 跨 CLI 强缓解 + 自动化不对称说明
  - 单 Agent 模式（`has_task_tool: false`）路由 no-op 声明（BDD-45）
  - **DEBT0039 措辞②**（P2-design §4.3 草稿②，逐字落地）：「author 文档内容 = P4 / 跨文件一致性验证 = P7」的区分句
- **M8** `agate/assets/execution-roles/architect.md` —— 「## 批次设计（强制节，TAG0014）」节内新增一段 **DEBT0039 措辞①**（P2-design §4.3 草稿①，逐字落地）：「补协议文档正文（`platform-notes.md` / `SETUP.md` / phase-cards 等）= P4 实现工作、批次执行阶段标 P4；P7 只做跨文件一致性验证、不 author 文档内容」+ TAG0030 / TAG0033 复盘两先例指针。
- **M12** `docs/design-notes/design-dispatch-routing.md` + `agate-workspace/roadmap/roadmap.md` —— 按 P2-design §9 的 6 项修订要点重写 design-note 头部「做什么」+ §2.1 + §2.2（三层落点 / try-and-fall / 两轴 + `(phase,role)` key / 弱强缓解 + 自动化不对称 / 两条完整性不变量 / per-machine 机会式）+ 头部「机制现状一句话」同步（effort 轴按 P2-design §9 末的措辞：`--effort` 本机 2.1.266 [实测] 有 / 引入版本未核实 / 按能力探测映射）；roadmap RM-AG0060 长描述旧措辞（`rules/dispatch-routing.yaml` / 「按序探测」/ `{cli,model}` 二元）回写为 `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml` / try-and-fall / 两轴。测试锚点 `agate/tests/unit/test_tag0034_docs.py`（BDD-46/47/52/53 grep 关键措辞）。
  - **DEBT0039 边界约束**：M7/M8 只做边界澄清措辞，**不扩到其它 DEBT、不改任何脚本 / gate 逻辑**。

### 约束

- **回归硬约束（known_risk 最高危 / BDD-39/40）**：**不改** `agate/rules/phases.yaml`（结构 + 字段）/ `agate/scripts/check-gate.py` / `agate/scripts/check-state-transition.py` / `agate/state-machine.md` 结构化部分。**不改** `check-events.py` 第 1-7 条 + 哈希链算法。**不改** `check-judge-verdict.py` / `check-p6-provenance.py`（BDD-42 平台无关性靠这两个脚本零改动成立）。**不改** `agate-dispatch.py` 既有渲染路径（`route` 子命令是纯新增分支）。**不改** RM-AG0055 命令流机制（`agate-cmdstream-*.py`）/ RM-AG0054 `agate next` `agate advance`。改前先 `git stash`-free 地跑 `python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py -q` 确认基线捕获，改后再跑确认仍绿。
- **不改测试**：P3 的 `test_tag0034_*.py` 是验收契约，只让实现使其转绿，不动测试断言。若发现测试断言与 P2-design 设计矛盾 → 标 `[DESIGN_GAP: ...]` 报主 Agent，不擅自改测试。
- **模型购物完整性洞（R1）**：`classify_outcome` / try-and-fall 循环里回落**只**在 `LAUNCH_FAIL` / `INFRA_ERROR` / `NO_PARSEABLE_OUTPUT` 触发；`gate_fail` 不是 `Outcome.kind` 取值、不进 `candidates_tried[].reason`；`check-events.py` 第 8 条机械拒绝 `gate_fail`。这三处任一留口子 = 阻塞级缺陷。
- **上下文控制**：按 P2-design.md §6 `files_to_read` 清单读代码（标行号的只读片段），不整目录全读、不盲搜。清单遗漏必读文件 → 照读并在产出标注。
- **SCOPE / CLARIFY / DESIGN_GAP**：对照 P2-design 改动清单（§1.1 M1~M12），prompt 漏了 P2 明确要做的 → 标 `[SCOPE_GAP]`；对 P2 方案有疑问 → 标 `[CLARIFY: ...]`；实现时自主决策补 P2 缺口 → 标 `[DESIGN_GAP: ...]`（独立成行单行 tag）。发现 P1/P2 未覆盖但必须做 → 标 `[SCOPE+]`（行首）。
- **自查 ≠ gate**：写完自跑 `timeout 400 python3 -m pytest agate/tests/ -k tag0034 -q --tb=short` 确认 P4a 目标测试文件转绿、subprocess/tmux 仍红、zero_change 仍绿；再跑 `timeout 120 python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml`（exit 0）+ `timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（exit 0）+ `timeout 60 python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`（exit 0）。**不要在返回里声称「P5 已过」**——只返回路径 + 摘要。
- **命令超时兜底**：所有 bash 命令前设 `timeout <n>s`（pytest 全量给 ~400-600s；单脚本 60-120s）。超时/非预期失败 → 停、progress 写一行、返回主 Agent。
- **ruff**：`~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py agate/scripts/check-dispatch-routing.py` clean（新脚本须过 lint）。
- **生产隔离**：dogfooding，"生产" = 主 checkout + `~/.agate` 稳定版，禁改。仅 worktree 内写。意外触碰写 `[PROD_TOUCHED]` 报告，否则 `[PROD_NOT_TOUCHED]`。
- **SELF-GATE 预告**（供主 Agent commit 规划，你不 commit）：本批改 `agate/scripts/agate-dispatch.py` / `check-events.py` / `check-dispatch-routing.py`（新）/ `agate_dispatch_route.py`（新）/ `agate/rules/dispatch-tiers.yaml`（新）/ `agate/dispatch-protocol.md` / `agate/assets/execution-roles/architect.md` / `agate/tests/**` → 触发 SELF-GATE。主 Agent 会在 commit 前派 `protocol-alignment-review`（A1-A7）+ C8 的 `review`（P4 实现评审），commit message 带 `self-gate-review:` trailer。
- **格式**：产出文件避免行首 `- PASS` / `- FAIL`（provenance 预判检测）。

> 子派发能力：启用（执行角色，按需）—— P4a 跨 schema 层 + 引擎层 + 协议正文 + design-note 修订，工作量大。若判断需拆，可按「schema 层子任务 / 引擎层子任务 / 文档子任务」派子任务（子任务继承你的 cli/model，不走路由表）；优先自己按「先 schema 后引擎后文档」顺序完成，逐步骤 progress 落盘。

### 上游关联

- P3 已 commit（`c218026`）：60 用例 / 10 文件，`pytest -k tag0034` = 58 failed / 2 passed（58 红全 B 类 + doc-assertion；2 绿 = BDD-39/40 回归护栏）。`.state.yaml` 现 phase=P4（P3→P4 transition 已 git add 未 commit）。
- `P3-progress.md`「测试接口契约」节 = M4 helper 模块的权威接口签名（`resolve` / `load_config` / `classify_outcome` / `build_dispatch_command`）。
- P2-design.md（`b851b1e` + yaml fence 修复在 `c218026`）：§3.1 数据流 / §3.2 档位词表 / §3.3 `resolve` 算法（含 T1/N2 返回契约、BDD-15/18 定死）/ §3.4 cli:native + effort 映射 / §3.5 决策 CLI 衔接 / §3.6 schema + 校验器 / §3.7 try-and-fall + `outcome.kind` 判定表 + `HAS_OUTPUT` 格式合法定死（N7）+ 挂死→INFRA_ERROR（N6）/ §3.8 `dispatch_route` 事件 + check-events 第 8 条 / §3.9 交互表（BDD-26 vs 51）/ §4.3 DEBT0039 草稿①② / §9 design-note 修订 6 项。
- P2-review.md（plan-eng-review approved）：8 条锁定决策 = 实现预期的权威（尤其 4「Codex turn 层为准」/ 6「effort 能力探测」/ 8「P4a→P4b 同文件串行、P4a 定 target JSON 契约」）。
- BDD-10 `[BASELINE_CHANGE]`（用户 2026-09-09 批准，P1-requirements.md BDD-10 + frontmatter `baseline_changes`）：effort 按 `claude --help` 能力探测，`build_dispatch_command` 收 `effort_supported` 布尔。
- 前置 TAG0033 v0.70.0：`agate/scripts/agate-cmdstream-adapters.py` `CodexAdapter`（class ~line 666 / `ADAPTERS["codex"]` ~line 878）—— **P4a 不碰**（子进程存活检测是 P4b），但 `classify_outcome` 的 Codex 分支判据与 `CodexAdapter._codex_is_finished` 的 `payload.item.status` 取值集（completed/failed/in_progress）一致即可。

### 输入文件（P2-design §6 files_to_read + 本批必读）

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（**方案权威**：§3 全节 + §4.3 + §6 + §9）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-review.md`（8 条锁定决策）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P3-test-cases.md` + `P3-progress.md`（测试映射表 + 接口契约）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（BDD-1~53 验收判据；BDD-10 `[BASELINE_CHANGE]`）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（env_constraints / known_risks）
- 测试文件（验收契约，只读不改）：`agate/tests/unit/test_tag0034_{schema,resolve,tryfall,events,native,interaction,docs}.py` + `agate/tests/regression/test_tag0034_zero_change.py` + `agate/tests/conftest.py`（fixture：`agate_scripts` / `python_exe` / `run_cli` / `task_dir`）
- `agate/scripts/check-maintainability.py:88-148`（`_load_config` 全兜底范式 —— `load_config` 逐字参考）
- `agate/scripts/agate-dispatch.py`（`main()` 分派 —— `route` 分支落点 + 既有渲染路径不碰）
- `agate/scripts/check-events.py`（7 条审计链 + 哈希链 —— 第 8 条追加落点）
- `agate/scripts/agate_common.py`（`append_event` / `GENESIS_HASH` / `resolve_workspace` —— 事件写入复用）
- `agate/rules/dispatch.yaml`（五模式词表 / gate 表 —— 确认不改）
- `agate/rules/phases.yaml`（回归对照，不改字段）
- `agate/dispatch-protocol.md:15-45`（三铁律原文）+ `:502-601`（派发编排机制节 —— M7 落点）
- `agate/assets/execution-roles/architect.md:209+`（批次设计节 —— M8 落点）
- `docs/design-notes/design-dispatch-routing.md`（头部 + §2.1/§2.2 —— M12 重写对象）
- `docs/research/cross-platform-dispatch-mechanics.md:141-210`（§6 结构化输出字段 —— `classify_outcome` 判据交叉核）
- `agate-workspace/roadmap/roadmap.md`（RM-AG0060 行 —— M12 回写）
- `agate-workspace/maintainability.yaml`（M2 scaffold 形态参照）
- `AGENTS.md`（gate 脚本分层、SELF-GATE、双工作区纪律、`--strict-errors-only` 定义）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md agate-md-field-set --list` 查看应填字段；逐个写入（须含 `implementation_dir`，本批 = `agate/scripts/` + `agate/rules/` + `agate/` 文档 + `agate-workspace/`，可写 `implementation_dir: agate/`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P4

路径：phase-cards/P4-implementation.md
---
# P4 — 代码实现

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P4 且有合规理由（check-pruning.py 已检查）→ 跳过，读 P5 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。
   该步骤不会阻塞流程——任何 stderr 输出（含 WARNING）均可忽略，直接继续步骤 1，
   无需查看结果、无需判断、无需因为看到 WARNING 而停下来处理。

**创建型测试清理钩子（强制要求，与 P3 卡同源）**：实现含创建资源用例时，须落地清理钩子——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；只修 P3 卡不修本卡即复发，两处须同步。

1. 派发 implementer subagent → 产出代码文件
   1.1 写 P4-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 P2 的 gate_commands 跑单元测试（非 gate，只是自查）
3. 按 C8 映射表派发评审（见下方）
4. 预跑 check-gate.py P4（确认暂存区有代码文件）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/ + 代码文件（含 .state.yaml，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P4，不要提前写 P5——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P4): {摘要}"（phase=P4，P4 产出含 P4-implementation.md + 代码文件）
7. P4 commit 完成后进入 P5：**phase 推进 P5 随 P5 产出 commit 一起**（P5-test-results/ 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（来自 gate 输出 / review rejected 理由）
→ 只修复失败项，不重做已通过的部分
→ 修复后重跑全量测试（T027 教训：修复可能引入回归）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P4 MAX=3）

**若这次是从 P6（或其他更后的阶段）退回来的**：`{AGATE_WORKSPACE}/tasks/{Txxx}/` 下不会再有旧的 P6-acceptance.md（已被归档），但当初具体是哪条 BDD 失败、失败原因是什么，会摘要在 `{AGATE_WORKSPACE}/tasks/{Txxx}/.retreat-history.md` 里——**重新派发 implementer 时，dispatch-context 必须引用这份摘要**，不能让 implementer 只看到"现有代码"却不知道具体要修哪里。已有代码不会被撤销、也不需要重新实现，是在已有实现基础上定向修复。**回退落地后必须建 DEBT 条目**（`source: retreat`，`evidence` 引用 retreat 提交哈希，模板 `assets/templates/tech-debt-template.md`——TAG0001 强制，见 `agate/rules/state-transitions.md` 回退规则节）。

## 前置条件

- [ ] P2-design.md 存在且 files_to_read 字段完整（导航清单）
- [ ] P2-review.md status: approved（P2 不可裁剪）
- [ ] P3-test-cases.md 存在（测试已设计）
- [ ] check-tdd-red.py 确认红灯（测试先于实现）
- [ ] 未跳过 P4（如有裁剪理由，见上方裁剪跳阶）

## 派发

- **角色**：implementer（`{agate_root}/assets/execution-roles/implementer.md`）
- **输入**：P2-design.md（files_to_read 导航 + gate_commands）+ P3-test-cases.md + P0-brief.md（env_constraints）
- **输出**：代码文件（在 P4-implementation.md 声明的 implementation_dir 下）
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md` + 以下阶段特定追加：

```
## 上下文控制
读取代码文件以 P2-design.md 的 files_to_read 清单为准，按需读取（标了行号范围的只读片段）。
不要在项目里盲目搜索或整目录全读。

## 自查≠gate
写完代码后应自跑测试确认基本功能（自查），但自查通过 ≠ P5 gate 通过。
P5 由主 Agent 派发 verifier subagent 执行 gate_commands.P5，主 Agent 验 gate（检查产出 + failed 计数 + N5 最小校验）。
不要在返回中声称"P5 已过"或"全部测试通过"——只返回路径 + 摘要。
UI/前端等需构建任务：单元测试全绿不代表可用，implementer 在 P4 完成后应构建并确认 dist 等构建产物存在，不能只跑单元测试就认为完成。

## 生产环境隔离
任何写入生产环境/生产数据库/生产 API 的操作都必须先 PAUSED 报告人工。
```

## 产出规格

- P4-implementation.md 必须声明 `implementation_dir: {实际路径}`
- 代码文件在声明的目录下
- 遵守 P2-design.md 的方案设计 + 现有项目代码规范

## 新增文件核对表

> 仅当项目已采用骨架（`P2-skeleton.md` 存在）或 CODE-MAP（`{AGATE_WORKSPACE}/agents/CODE-MAP.md`
> 存在）机制时填写；未采用则本节可省略。

implementer 为本阶段**每个新增文件**填一行：

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| {path} | `within <dir>` / `[SKELETON_DEVIATION: 理由]` | `[CODE_MAP_UPDATED]` / `[CODE_MAP_EXEMPT: 理由]` |

- **骨架归属列**：新增文件落在骨架声明的目录内 → `within <dir>`；落在骨架外 → 标
  `[SKELETON_DEVIATION: 理由]`（不阻断，供 P7 核对）
- **CODE-MAP 处理列**：新增文件已同步更新 `agents/CODE-MAP.md` → `[CODE_MAP_UPDATED]`；判断
  该文件不需要更新 CODE-MAP（如临时/测试脚手架）→ `[CODE_MAP_EXEMPT: 理由]`

`change_type: refactor` 同样适用本表（不因换用回归口径而豁免）。

## 评审派发（C8 机械映射）

**在 P4 实现完成后、gate 前**，按 P1 声明的 domains 和 risk_level 派评审。C8 映射表是机械规则，不靠判断"需不需要"：

| domain | 派哪些评审 | 产出 |
|--------|----------|------|
| backend | review | P4-review.md |
| frontend | design-review | P4-review.md |
| mcp | review（关注 MCP 接口契约）| P4-review.md |
| security | cso | P4-review.md |
| risk=high | P4 实现评审（按 domains 派 review/design-review/cso；P2 plan-eng-review 已审方案，P4 实现评审不可省）| P4-review.md |
| full（tier=full 或声明 ceremony: full）| P4 实现评审（按 domains 派 review/design-review/cso，同 risk=high 不可省；P2 plan-eng-review 已审方案）+ cso（security 域）+ P7 不可裁（full 档任务 P7 为强制阶段）| P4-review.md |

多个评审角色 `专家组并行` → 所有返回后派组长汇总 → 统一 P4-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长产出：P4-review.md。**agent 字段必须非 main**（与 P2 评审同规则，check-gate.py 在 P2 分支硬拦截 agent=main 的 approved）
5. 组长规则：不发表新意见，只汇总；任何 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P4-review.md。

**评审 checklist（RM-AG0046）**：`agate/scripts/check-maintainability.py` 检出 violations 非空时，评审角色 approve 前必须读过任务目录 `known-violations.md` 的登记理由——"是否接受该反模式"的判断权在评审角色，登记与数量对齐不单独构成放行依据。

review 不通过 → implementer 修改代码 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 按包拆分并行（条件触发，需额外约束）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P4 可拆分并行，但**有额外约束**：

1. 每个 package 派一个 implementer subagent
2. **各 implementer 只改自己 package 目录下的文件**——跨包的共享文件（类型定义、接口、配置）由主 Agent 在所有并行 implementer 返回后统一处理
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit
5. 主 Agent 在所有 implementer 返回后，统一处理共享文件改动（如果有）

**冲突预防**：
- dispatch-context 约束节必须写明：`只改动 {pkg}/ 目录下的文件。共享文件（{列出}）不在本次改动范围内`
- 如果某个 implementer 必须改共享文件 → 该包不能并行，改为串行（主 Agent 先派其他包并行，再串行处理含共享改动的包）
- 无法确定是否有共享改动 → 串行（安全默认值）

**基础设施隔离（并行时强制）**：
- debug server 端口：每个 implementer 的 dispatch-context 约束节分配不同端口（如 pkg-a: 3001, pkg-b: 3002）
- 测试数据库：每个 implementer 用独立数据库路径（如 `test-{pkg}.db`），不共享同一 test.db
- 环境变量：dispatch-context 写明各 subagent 独立的环境变量值（如 `PORT=3001` vs `PORT=3002`）
- 临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录

主 Agent 在并行派发前**必须**为每个 subagent 的 dispatch-context 分配上述隔离参数。当前无 gate 脚本检查（已知缺口），但未分配导致运行时冲突（端口占用/数据库锁）时计为重试，不算环境问题。

## gate 规则（check-gate.py 会跑）

```bash
check-gate.py P4 $TASK_DIR
```

- **exit 0**：暂存区含非 md/yaml 代码文件（git diff --cached --name-only）
- **exit 1**：暂存区仅 .md/.yaml 文件（无实际代码变更）→ 不能推进
- **exit 1**（RM-AG0046 三重门槛）：检测 violations 非空时，`known-violations.md` 必须存在且登记条目数 ≥ violation 数（评审检查复用上方既有 exit 1 条件；violations 为空 / 检测未部署 / git 通道不可用时不阻断）
- WARNING（不改变 exit code）：骨架/CODE-MAP 机制已采用（P2-skeleton.md 或 agents/CODE-MAP.md 存在）但缺「新增文件核对表」标题

## 推进条件（全部满足才写 phase: P5）

- [ ] 暂存区含代码文件（非 .md/.yaml）
- [ ] 按 C8 映射表触发的评审全部完成：P4-review.md status: approved（所有任务都要求——risk=high 的 P2 plan-eng-review 审方案，P4 实现评审按 domains 另行派发，不可省）
- [ ] SCOPE+ 已处理（若本阶段产生）：P1-requirements.md 有 [SCOPE_RESOLVED]（行首声明格式）
- [ ] git commit 完成

## 常见错误

1. **不读 files_to_read，在项目里乱翻**：implementer 拿到 P2 的 files_to_read 清单后应按清单阅读，不要在项目里全文搜索或整目录全读——上下文会爆炸
2. **自行加范围外改动**：发现需要做但不在 P1 范围内的改动 → 标 [SCOPE+]（行首声明格式）而非直接做
3. **只跑单元测试不验证集成**：单元测试全绿 ≠ 功能可用。P5 会跑 gate_commands 做技术验证，但要确保实现时路径依赖的端点行为已验证
4. **先更新 .state.yaml 再 commit**：state 和产出在同一 commit 里——不要先 commit 产出再单独 commit state
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P5 验证依赖：P5 跑 gate_commands.P5 的命令（在 P2 声明），确保你的实现能通过
- P6 验收依赖：实现路径的端点行为必须可验证（确认 API 返回正确的 Content-Type、状态码等）
- 代码改动文件路径：P8 发布时确认版本文件变更需要知道你改动了哪些 package

> 完成 → 读 phase-cards/P5-verification.md

6. **修改 P1 文档**：P4 发现 BDD 矛盾时标 DESIGN_GAP，不直接改 P1-requirements.md。需变更 P1 时标 `[BASELINE_CHANGE: 理由]` 并经主 Agent 批准。
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P4（P3 已 commit `c218026`）/ judge.enabled=true
- P3 红灯基线：`pytest -k tag0034` = 58 failed / 2 passed（2 绿 = `test_tag0034_zero_change.py` BDD-39/40 回归护栏）
- 目标物均不存在（待建）：`agate/scripts/agate_dispatch_route.py` / `agate/scripts/check-dispatch-routing.py` / `agate/rules/dispatch-tiers.yaml` / `agate-workspace/dispatch-routing.yaml`；`agate-dispatch.py` 无 `route` 子命令（`main()` 从 `args=sys.argv[1:]` / `phase=args[0]` / `_PHASES` 校验起）；`check-events.py` 7 条审计链（第 7 条「未知 event 不拦」，line ~104-118）
- conftest fixture 可用：`agate_scripts`（= `agate/scripts/` 路径）/ `python_exe` / `run_cli`（合并流 `.output` / `.returncode`）/ `task_dir` / `tmp_path`
- 工具：python 3.12.3（`/usr/bin/python3`）/ pytest 9.0.3 / pyyaml 6.0.1 / ruff `~/.venvs/agate-dev/bin/ruff`
- CLI 版本（本机实测，`classify_outcome` / `build_dispatch_command` 判据参照）：Claude Code 2.1.266（有 `--effort`）/ codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4
- `check-protocol-consistency.py` 当前 `--strict-errors-only` exit 0（P2-design yaml fence 已在 `c218026` 修复）—— 改 design-note / dispatch-protocol.md 后须保持 exit 0（BDD-50）
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- gate_commands（P2 §8 固化，不改）：`P3`/`P5` = `python3 -m pytest agate/tests/ -q [--tb=no]`；`P5_consistency` = `check-protocol-consistency.py --strict-errors-only`；`P5_events` = `check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`；`P5_routing_schema` = `check-dispatch-routing.py agate-workspace/dispatch-routing.yaml`
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
