---
agent: implementer
implementation_dir: agate/
---

# P4-implementation — TAG0034 派发路由 P4a 批（static-batch 第 1 批，complexity: high）

`[PROD_NOT_TOUCHED]`

实现落点（`implementation_dir` 见 frontmatter，= `agate/`）：`agate/scripts/` + `agate/rules/` + `agate/` 协议文档，加项目级 `agate-workspace/dispatch-routing.yaml` + `agate-workspace/roadmap/roadmap.md` + `docs/design-notes/design-dispatch-routing.md`。

> 本批 = P4a：schema 层（M1/M3/M2）+ 引擎层（M4/M4b/M6）+ 协议正文 / 文档（M7/M8/M12 + M10 的 effort 注明子片）。
> 子进程 spawn + 结构化输出端到端执行（M5）、routed-away judge helper、tmux wrapper 归 P4b/P4c，本批不做。
> 自查 ≠ P5 gate。本文件只声明路径 + 改动 + 摘要，不预判 gate 结论。

## 改动清单

### 新增文件

| 文件 | 模块 | 内容 |
|---|---|---|
| `agate/rules/dispatch-tiers.yaml` | M1 | 协议本体档位词表：`schema_version: 1` + `tiers: {bulk, standard, deep}`（每档 `intent:` 语义画像，`standard` 画像写死「恒等于继承主 Agent 当前 model 的原生派发、不经 tier_bindings 展开」）+ `defaults: {}`（出厂 (phase,role)→tier，空 map ⇒ 隐式全 standard）。改它触发 SELF-GATE。|
| `agate/scripts/check-dispatch-routing.py` | M3 | routing schema 静态校验器。CLI `check-dispatch-routing.py <yaml路径>`，exit 0 合法 / exit 1 非法。校验：`tier`/`candidates` 互斥、`cli ∈ {native,claude-code,codex,opencode}`、`effort ∈ {low,medium,high}`、任意层 `fallback:` 非法、`model` 允许 null、`tier` 交叉核 `../rules/dispatch-tiers.yaml`（该文件不可读时降级为「非空字符串放行」+ WARNING）、`machine_routes` 文档化保留字放行、多余顶层 key / `tier_bindings.standard` → WARNING、坏 YAML / 文件不存在 / 顶层非 mapping → exit 0。|
| `agate-workspace/dispatch-routing.yaml` | M2 | 项目级 scaffold（非协议本体、不触发 SELF-GATE，对齐 `maintainability.yaml`）：`schema_version: 1` + `tier_bindings: {}` + `routes: {}` + 带注释的 `tier_bindings:` / `routes:` 示例。`check-dispatch-routing.py` 对它 exit 0。|
| `agate/scripts/agate_dispatch_route.py` | M4 | importable helper（下划线命名）。暴露 `resolve` / `load_config` / `load_factory_defaults` / `classify_outcome`（`Outcome.kind/.reason`）/ `build_dispatch_command` / `resolve_native_target` / `try_and_fall`（`TryFallResult.final/.tried`）/ `write_dispatch_route_event`（复用 `agate_common.append_event` 哈希链）/ `should_consult_routing_table` / `route_is_noop` + 常量 `GATE_FAIL_TRIGGERS_FALLBACK = False`。算法逐条按 P2-design §3.3（优先级序 / standard 短路 / tier 展开 / effort 合并 / (phase,role) 命中优先）+ §3.7（四值 `outcome.kind` 判定表 + 挂死→INFRA_ERROR + 回落只在三类基础设施信号）。`load_config` 全兜底逐字参考 `check-maintainability.py:_load_config`。|

### 修改文件

| 文件 | 模块 | 改动点 |
|---|---|---|
| `agate/scripts/agate-dispatch.py` | M4b | `main()` 顶部新增 `if args and args[0] == "route": _route_main(args[1:]); return` 分支 + 新增 `_route_main(argv_rest)` 函数（读 workspace → `load_config` → `load_factory_defaults` → `resolve` → stdout 单行 target JSON `{"cli","model","effort","form","dispatch_context"[,"chain"]}`）。**无 `route` 参数时既有渲染路径逐字节不变**——`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by` 未触碰。|
| `agate/scripts/check-events.py` | M6 | 追加第 8 条审计链：`event == "dispatch_route"` 的行，每个 `candidates_tried[i].reason`（若存在）必须 ∈ `{launch_fail, infra_error, no_parseable_output}`，出现 `gate_fail` 或任何其它值 → `sys.exit(1)`（走既有错误出口格式）。新增模块常量 `DISPATCH_ROUTE_REASONS`。docstring 审计链清单补第 8 条 + 第 7 条注释补 `dispatch_route` 为已知类型。**第 1-7 条 + 哈希链算法 + GENESIS/ts/judge 计数未动。**|
| `agate/dispatch-protocol.md` | M7 | 「## 派发编排机制」节内新增子节「### 0. 派发路由（查表 → 派首选 → 逐级回落 → 再派发）」：try-and-fall 5 步 + 「此步在铁律 1 启动 subagent 之前插入」+「gate 判定只认产出文件 + exit code，不认谁生产的」+ 两条完整性不变量（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」）+ `cli: native` 弱缓解 / 跨 CLI 强缓解 + 自动化不对称 + 单 Agent 模式路由 no-op + retry/回退时机械重解析、不做升档 + DEBT0039 措辞②（author 文档内容 vs 跨文件一致性验证的阶段边界，§4.3 草稿②逐字）。|
| `agate/assets/execution-roles/architect.md` | M8 | 「## 批次设计（强制节，TAG0014）」节内新增一段 DEBT0039 措辞①（§4.3 草稿①逐字）：「补协议文档正文 = P4，不是 P7」+ P7 只做跨文件一致性验证、不 author 文档内容 + TAG0030 / TAG0033 复盘两先例指针。|
| `agate/platform-notes.md` | M10（effort 子片）| Claude Code 章新增「推理档（effort，与 model 正交）」行：`--effort` flag 本机 2.1.266 [实测] 有 / 2.1.263 [实测] 无 / 引入版本未核实；路由按 `claude --help` 能力探测分流映射 / 省略；不硬编码版本号。（M10 的三平台「结构化输出判成败字段」小节仍归 P4b。）|
| `docs/design-notes/design-dispatch-routing.md` | M12 | 头部「做什么」+「机制现状一句话」重写 + 新增「本任务定案（2026-09-09 重写）」6 项块（三层落点 / try-and-fall / tier+effort 两正交轴 + (phase,role) key / 弱强缓解 + 自动化不对称 + effort 三平台均可用 / 两条完整性不变量 / per-machine 不追求跨机可复现）；§2.1 重写为三层落点表 + `agate-workspace/dispatch-routing.yaml` 形态示意（```text 围栏）+ 两正交轴 / (phase,role) key / standard 不变量锚 / 终点回落不可配 / per-machine 声明；§2.2 标题 + 正文由「按序探测」改写为 try-and-fall（查表 → 派首选 → 三类基础设施信号逐级回落 → 默认派发）。走 docs commit（非 SELF-GATE）。|
| `agate/scripts/check-protocol-consistency.py` | SELF-GATE alignment 修复 | CHECK 9 锚点表 `SCRIPT_ALIGNMENT_ANCHORS` 追加 `check-dispatch-routing.py` 条目（`keywords: [VALID_CLI, VALID_EFFORT, fallback]`，**不设 `callers`**——非常驻 pre-commit gate，设 `callers` 会触发 `CHECK9-callers` WARNING）。修复 protocol-alignment-review misaligned 结论：新 gate 脚本未登记 → `CHECK9-coverage` WARNING + `test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts` 全量 pytest FAIL。改后 CHECK 9 PASS、`test_sg_6` 转绿。|
| `agate-workspace/roadmap/roadmap.md` | M12 | RM-AG0060 长描述行：`rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml`；「按序探测」→ try-and-fall（无 probe，三类基础设施信号逐级回落，收到 gate 能评产出即停）；`{cli,model}` 二元 → tier + effort 两轴；`(phase,role)` key；立项前待办里作废的「探测缓存 + native 探测方式」项删除。走 docs commit（非 SELF-GATE）。|

## 实现关键决策

- **`resolve` 三写法兼容**：`routes["Pn.role"]`（点分 key，BDD-3 的 `P4.review`）/ `routes["Pn"]["role"]`（嵌套）/ `routes["Pn"]`（phase 级直接条目，靠 `tier`/`candidates`/`effort` marker 判定）三种形态都解析；`(phase,role)` 命中优先于 `phase` 级（BDD-11/12）。
- **`resolve` 不改调用方输入**：tier 展开时对每个候选 `dict(cand)` 拷贝后再合并 `effort`，不 mutate `tier_bindings` 里的候选（BDD-43 同输入多次 `resolve` 恒等）。
- **`resolve` 返回契约（T1/N2）**：每条分支返回对象键集恒为 `{form, chain, model, effort}`；`form == 'default'` → `chain is None` / `model = current_model` / `effort = None`；`form == 'chain'` → `chain` 内逐候选 model/effort、外层 `model = None` / `effort = None`。tier 引用但 `tier_bindings` 缺该 tier → `form='default'`（机会式回落）。
- **`classify_outcome` 判定序**：① `killed_reason` —— `spawn_oserror` 类 → LAUNCH_FAIL，其余非空（wait 超时 / 命令流阈值 / kill -0 失活）→ INFRA_ERROR（N6）；② 结构化输出基础设施签名（`turn.failed` / 顶层 `type:error` / `ProviderAuthError` 等）或「非零退出且无产出且无成功签名」→ INFRA_ERROR；③ 产出文件非空（presence 级）→ HAS_OUTPUT；④ 否则 NO_PARSEABLE_OUTPUT。产出质量差 / 内容不完整归 HAS_OUTPUT、不回落（R1 / BDD-24）；结构完整度校验未塞进 NO_PARSEABLE_OUTPUT 分支（N7）。
- **R1 三处闭合**：`classify_outcome` 的 `kind` 无 `GATE_FAIL` 取值、`reason` 无 `gate_fail` 值；`try_and_fall` 只在 LAUNCH_FAIL/INFRA_ERROR/NO_PARSEABLE_OUTPUT 三类 continue，HAS_OUTPUT 即停写事件 return；`check-events.py` 第 8 条机械拒绝 `gate_fail` / 非三值理由码。
- **`build_dispatch_command` effort 映射**：Codex `-c model_reasoning_effort=<e>`；OpenCode `--variant <e>`；Claude Code / native 按 `effort_supported` 布尔——True 加 `--effort <e>`（独立两个 argv 项）、False 省略不报错（BDD-10 [BASELINE_CHANGE]，能力探测由调用方给出，不硬编码版本号）；`model: null` → 不传 `--model`。
- **`write_dispatch_route_event`** 直接复用 `agate_common.append_event`——`prev_hash = sha256(上一行原始文本)` / `ts` 由既有逻辑填；事件体 `{"event":"dispatch_route","phase","candidates_tried","final"}`，不写 `state_transition`、不动 `retries`（BDD-28）。
- **`try_and_fall` 无状态**：`write_event(phase, tried, final)` 位置参数回调（与测试契约一致），`phase` 缺省 `None`；主 Agent 决定「是否重新调用」（同阶段 gate-FAIL retry 不调、跨阶段回退调），helper 本身不感知 retry 类型。

## [DESIGN_GAP]

[DESIGN_GAP: P2-design §3.5 把 `agate-dispatch.py route` 子命令的 `_route_main` 具体形态留给「P4a 落地时定」，未指定 P4a 阶段（子进程 spawn 属 P4b/M5、尚无 `dispatch_once`）下 `form == "chain"` 时 `_route_main` 应输出什么。实现中自主决定：P4a 的 `_route_main` 只做 `resolve` + 输出「已解析的路由计划」JSON（`form == "default"` → `{cli:"default", model, form:"default", dispatch_context}`；`form == "chain"` → 首候选 + 完整 `chain` + `form: native|subprocess` + `dispatch_context`），不在 P4a 内跑端到端 try-and-fall，把 target JSON 契约固化给 P4b 在其上加 subprocess 分支。与 §4.1「P4a 建 route 骨架 + JSON 输出契约 → P4b 加 subprocess 分支」一致，但契约字段的确切取值由本实现自主定。]

[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-09）。P4a 的 `_route_main` 只做 resolve + 输出已解析路由计划 JSON、把端到端 try-and-fall（dispatch_once + subprocess spawn）留给 P4b/M5，与 P2-design §4.1「P4a 建 route 骨架 + JSON 输出契约 → P4b 加 subprocess 分支」的批次意图逐条一致；target JSON 契约字段（form ∈ {default, chain}、chain、首候选、dispatch_context）作为 P4a 固化的跨批共享件，P4b/P4c 只增不改。非偏离 P2 设计，无需回 P2。]

## [SCOPE+] / [CLARIFY]

- 无 `[SCOPE+]`：未发现 P1/P2 未覆盖但必须做的新需求。
- 无 `[CLARIFY]`。

## 说明：M10 归属

派发指引「实现顺序（N3）」的 M 编号清单（M1→M3→M2→M4→M4b→M6→M7→M8→M12）未列出 M10；但同指引「门槛」明确要求 `test_tag0034_native.py` 由红转绿，该文件含 `test_bdd_10_platform_notes_records_effort_probe`（grep `platform-notes.md` 的 `--effort` / `能力探测` / `引入版本未核实`）。据「门槛」为强制指令，本批落地了 M10 的 **effort 注明子片**（Claude Code 章一行 + 能力探测措辞）。M10 的「三平台结构化输出判成败字段」小节（BDD-33~36 素材）仍按 P2-design §4.1 归 P4b，本批未动。

## 新增文件核对表

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/rules/dispatch-tiers.yaml` | 无 P2-skeleton.md / 无 CODE-MAP.md 机制 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |
| `agate/scripts/check-dispatch-routing.py` | 同上 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |
| `agate/scripts/agate_dispatch_route.py` | 同上 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |
| `agate-workspace/dispatch-routing.yaml` | 同上 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |

## 自查记录（非 gate）

- `python3 -m pytest agate/tests/ -k tag0034 -q --tb=short` → 57 passed / 3 failed（`1537 deselected`）。
  - 转绿：`test_tag0034_schema.py`(6) / `test_tag0034_resolve.py`(10) / `test_tag0034_tryfall.py`(10) / `test_tag0034_events.py`(4) / `test_tag0034_native.py`(7) / `test_tag0034_interaction.py`(6) / `test_tag0034_docs.py`(8) 全绿。
  - `regression/test_tag0034_zero_change.py`(2) 全绿（BDD-39 字节基线 + BDD-40 无配置 = 现状）。
  - 仍红（P4b/P4c）：`test_tag0034_subprocess.py::test_bdd_42`（`routed_away_verdict_location` 未实现，P4b）；`test_tag0034_tmux.py::test_bdd_37/38`（`build_subprocess_launch` / `tmux_cleanup_action` 未实现，P4c）。
- `python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` → exit 0。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0（330 WARNING / 0 ERROR）。
- `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（账本 12 行，哈希链完整）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py agate/scripts/check-dispatch-routing.py agate/scripts/agate-dispatch.py agate/scripts/check-events.py` → All checks passed。
- 回归旁证：`test_check_events.py` / `test_tag0027_b2_agate_dispatch.py` / `test_tag0027_b2_audit2_dual_anchor.py` 零改动仍绿（25 passed）；`pytest -k "events or dispatch or consistency or protocol or tag0030 or provenance or judge_verdict or structure"` → 340 passed / 1 failed（仅 P4b 的 `test_bdd_42`）。

## SELF-GATE 预告（供主 Agent，不 commit）

本批改 `agate/scripts/agate-dispatch.py` / `agate/scripts/check-events.py` / `agate/scripts/check-dispatch-routing.py`（新）/ `agate/scripts/agate_dispatch_route.py`（新）/ `agate/rules/dispatch-tiers.yaml`（新）/ `agate/dispatch-protocol.md` / `agate/assets/execution-roles/architect.md` / `agate/platform-notes.md` / `agate/tests/**`（无——测试是 P3 产出，本批未改）→ 触发 SELF-GATE。`agate-workspace/dispatch-routing.yaml` + `docs/design-notes/design-dispatch-routing.md` + `agate-workspace/roadmap/roadmap.md` 不触发（非协议本体 / docs commit）。
