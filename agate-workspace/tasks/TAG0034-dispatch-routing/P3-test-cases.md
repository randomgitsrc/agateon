---
test_code_dir: agate/tests/
---
## test_code_dir

`test_code_dir: agate/tests/`（frontmatter 权威，此处为正文说明）。

本任务改 agate 自身 —— 测试落既有测试树（`agate/tests/unit/` + `agate/tests/regression/` +
`agate/tests/fixtures/`），**不用**任务目录 `P3-test-code/`（dispatch-context 明文）。文件名
`test_tag0034_*.py`。

| 落点 | 用例数 | 覆盖 |
|---|---|---|
| `agate/tests/unit/test_tag0034_schema.py` | 6 | BDD-1~6（`check-dispatch-routing.py` schema 校验器） |
| `agate/tests/unit/test_tag0034_resolve.py` | 10 | BDD-7 / 11~18 + T1（`resolve` 三层优先级 / tier 展开 / standard 短路 / 全兜底 / last-write-wins） |
| `agate/tests/unit/test_tag0034_tryfall.py` | 10 | BDD-19~26 / 28 + T2（try-and-fall 逐级回落 / 完整性不变量 / 回落非 retry / 挂死→infra_error） |
| `agate/tests/unit/test_tag0034_events.py` | 4 | BDD-27 / 29 / 30 + T3（`dispatch_route` 事件 + `check-events.py` 第 8 条理由码枚举） |
| `agate/tests/unit/test_tag0034_native.py` | 7 | BDD-8 / 9 / 10 / 31 / 32（`cli:native` 各平台 + effort 各平台映射，BDD-10 两分支 + doc-assertion） |
| `agate/tests/unit/test_tag0034_subprocess.py` | 5 | BDD-33~36 / 42（子进程 spawn + 结构化输出解析 + routed-away judge 平台无关性） |
| `agate/tests/unit/test_tag0034_tmux.py` | 2 | BDD-37 / 38（tmux wrapper 生命周期，可 mock tmux） |
| `agate/tests/unit/test_tag0034_interaction.py` | 6 | BDD-43 / 44 / 45 / 51（五模式并行 / 自主再派发不走表 / 单 Agent no-op / P5→P4 回退重解析） |
| `agate/tests/unit/test_tag0034_docs.py` | 8 | BDD-41 / 46~50 / 52 / 53（doc-assertion，grep 关键措辞） |
| `agate/tests/regression/test_tag0034_zero_change.py` | 2 | BDD-39 / 40（回归护栏 + 基线 hash） |
| **合计** | **60** | **BDD-1~53 全覆盖 + T1/T2/T3** |

新增 committed fixture：

- `agate/tests/fixtures/tag0034_regression_baseline.json` —— BDD-39 基线 sha256（P3 捕获，长期不变量守护）
- `agate/tests/fixtures/tag0034_claude_code/{ok_end_turn,empty_result,api_error}.json`
- `agate/tests/fixtures/tag0034_codex/{turn_completed_ok,turn_failed_exit0,item_failed_turn_completed}.jsonl`
- `agate/tests/fixtures/tag0034_opencode/{step_finish_stop_ok,provider_auth_error,unknown_error,empty_return}.jsonl`

  子进程结构化输出**静态样本**（P2-design §5 MV1~MV7 真机构造，从 scratchpad `mv/` 收敛）。
  CI 不真调 CLI。

---

## 红灯性质总览（`check-tdd-red.py` 会核）

| 类别 | 用例 | P3 期望 | 红灯类型 |
|---|---|---|---|
| 功能类（import / 子命令 / 子脚本 / 审计链未实现） | BDD-1~38 / 42~45 / 51（功能面）/ T1 / T2 / T3 | 红 | **B 类**：`ModuleNotFoundError: No module named 'agate_dispatch_route'`（`agate_` 前缀 = 项目内模块）/ subprocess `check-dispatch-routing.py` 返回码 2（脚本不存在）/ `check-events.py` 第 8 条未实现（`assert 1 == 0`） |
| doc-assertion（grep 关键措辞） | BDD-10（platform-notes 部分）/ 41 / 45（doc 部分）/ 46 / 47 / 48 / 49 / 51（doc 部分）/ 52 / 53 | 红 | AssertionError（措辞未写入目标文件）。P4 author 正文后转绿（TAG0030 / DEBT0039 同款「P3 写红、P4 补绿」） |
| 回归护栏 | **BDD-39** | **绿**（P3 绿属预期，**非 TDD 违规**） | —— 基线 sha256 长期不变量守护（test-designer 卡片「永久回归测试判据」允许断言当前状态） |
| 回归护栏（含红子断言） | **BDD-40** | 至少一个断言红 | (a) `agate_dispatch_route.load_config` / `resolve` 未实现 = B 类红；(b) 现状账本 `dispatch_route` 条数 = 0 = 回归基线绿 |
| 一致性回归 | **BDD-50** | 红（P3 红属预期） | `check-protocol-consistency.py --strict-errors-only` 现 exit 1：BDD-48/49 文档修订未就位 + `[P2_DESIGN_YAML_FENCE]` 既有 `P2-design.md:364` ```yaml fence 解析 ERROR（非本 test-designer 引入，见 P3-progress，待主 Agent 定 P4/P7 处理）。P4/P7 后转绿 |

**`check-tdd-red.py` 整体判据**：功能类 + T1/T2/T3 的 B 类红灯（55 条）足以让 `check-tdd-red.py $TASK_DIR`
exit 0（真红）。BDD-39 绿不影响整体判定（有红即真红）。自跑结果见 P3-progress.md：
`59 failed, 1 passed`（1 passed = BDD-39 回归护栏，符合预期）。

---

## 测试接口契约（P4 须提供 —— TDD 由这些红灯驱动）

**importable helper 模块 `agate/scripts/agate_dispatch_route.py`**（P2-design §3.5「可 import 一个
helper」；下划线名可 import，与既有 `agate_common.py` 惯例一致）：

| 符号 | 签名 | 语义锚 |
|---|---|---|
| `resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model)` | → `{"form", "chain", "model", "effort"}` | P2-design §3.3；`form ∈ {'default','chain'}`；`form=='default'` → `chain is None` / `model=<主 Agent 当前 model>`；优先级序：项目级直接值 `candidates:` > 项目级 `tier:` > `tier_bindings:` 展开 > `FACTORY.defaults` → `standard` |
| `load_config(workspace_dir)` | → `(routes, tier_bindings)` | 全兜底：文件不存在 / YAML 坏 / 类型坏 → `({}, {})` + stderr WARNING，不抛异常（复用 `check-maintainability.py:_load_config` 范式） |
| `classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None)` | → `Outcome(.kind, .reason)` | P2-design §3.7 判定表；`kind ∈ {LAUNCH_FAIL, INFRA_ERROR, NO_PARSEABLE_OUTPUT, HAS_OUTPUT}`；`reason ∈ {launch_fail, infra_error, no_parseable_output}` 或 `None`；`killed_reason ∈ {spawn_oserror→LAUNCH_FAIL, wait_timeout/cmdstream_threshold/kill0_dead→INFRA_ERROR}`；退出码对 Codex 仅弱佐证，以事件流 turn 层为准；item 级 `status:"failed"` 永不触发回落 |
| `try_and_fall(chain, *, dispatch_context_path, dispatch_once, write_event)` | → `Result(.final, .tried)` | 无 probe（首个动作即派真实 ctx）；回落只在前三类 `kind`；`HAS_OUTPUT` 即停、交 gate；全落空 → `final={"cli":"default"}`；成功/回落各只写 1 条 `dispatch_route` 事件 |
| `write_dispatch_route_event(task_dir, phase, *, tried, final)` | → None（追加 `gate-events.jsonl`） | 复用 `agate_common.append_event` 哈希链（`prev_hash`/`ts` 既有逻辑），不写 `state_transition`、不动 `retries` |
| `build_dispatch_command(candidate, *, ctx_path, effort_supported)` | → `list[str]`（argv） | effort 映射：Codex `-c model_reasoning_effort=<e>` / OpenCode `--variant <e>` 或 `#<e>` / Claude Code `--effort <e>` **仅当 `effort_supported`（`claude --help` 含 `--effort`）**，否则省略不报错（BDD-10 `[BASELINE_CHANGE]`） |
| `resolve_native_target(candidate, *, current_model, platform=None, tier=None)` | → `{"model", "effort", "named_agent"?}` | Claude Code：目标 model 全量算好；OpenCode：命名 agent `agate-route-{tier}`（MVP 约定命名，R6） |
| `should_consult_routing_table(dispatch_kind)` | → `bool` | `"autonomous_redispatch"` → False（继承父）；`"phase_role_dispatch"` → True |
| `route_is_noop(executor_env)` | → `bool` | `has_task_tool == False` → True（单 Agent 模式 no-op，BDD-45） |
| `routed_away_verdict_location(cli)` | → `"TASK_DIR"` | routed-away judge 的 verdict + 证据落 `TASK_DIR`（铁律 2/3 不变，BDD-42） |
| `build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name)` | → `list[str]` | `tmux new-session -d -s <ns> '<cmd> | tee <capture>'`（可用）/ 裸 `cmd`（不可用），BDD-37 |
| `tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s)` | → `"kill_now" / "let_countdown" / "force_kill"` | 无 client → `kill_now`；有 client → `let_countdown`；`elapsed_s > countdown_n + margin_s` → `force_kill`（余量 10s，P2-review 锁定决策 5） |

**新增脚本 `agate/scripts/check-dispatch-routing.py`**（schema 静态校验器，CLI: `<yaml路径>`，exit 0/1）：
`cli ∈ {native, claude-code, codex, opencode}` / `effort ∈ {low, medium, high}` / `tier` 与 `candidates`
互斥 / `(phase,role)` key 两形态 / `fallback` 字段非法 / `model: null` 放行 / `tier_bindings` 同名键
WARNING / 坏 YAML / 文件不存在 → exit 0（无可校验对象）。

**`agate/scripts/check-events.py` 追加第 8 条审计链**：`event == "dispatch_route"` 的行，每个
`candidates_tried[i].reason` 必须 ∈ `{launch_fail, infra_error, no_parseable_output}`；出现 `gate_fail`
或任何其它值 → exit 1。不动第 1-7 条 + 哈希链算法。

---

## 全量映射表（BDD-1~53 + T1/T2/T3 → 测试，每条有且仅一个归属测试）

> 归属列格式：`<文件>::<函数名>`（函数名含 BDD 编号）。预期红灯类型：B=B类 / DA=doc-assertion / RG=回归护栏。

| BDD | 归属测试 | 红灯类型 | P2-design 设计锚 |
|---|---|---|---|
| BDD-1 | `test_tag0034_schema.py::test_bdd_1_tier_effort_two_axes_accepted` | B（脚本不存在，rc 2） | §3.6 schema：两轴独立、任意组合合法 |
| BDD-2 | `test_tag0034_schema.py::test_bdd_2_tier_candidates_mutually_exclusive` | B | §3.6：`tier`/`candidates` 互斥 → exit 1 |
| BDD-3 | `test_tag0034_schema.py::test_bdd_3_phase_role_key_optional` | B | §3.6：`Pn` / `Pn.role` 两 key 形态，role 段可选 |
| BDD-4 | `test_tag0034_schema.py::test_bdd_4_invalid_cli_rejected` | B | §3.6：`cli` 枚举 `{native, claude-code, codex, opencode}` |
| BDD-5 | `test_tag0034_schema.py::test_bdd_5_invalid_effort_rejected` | B | §3.6：`effort` 枚举 `{low, medium, high}` |
| BDD-6 | `test_tag0034_schema.py::test_bdd_6_fallback_field_illegal` | B | §3.6：`fallback` 字段非法（终点回落恒为默认派发） |
| BDD-7 | `test_tag0034_resolve.py::test_bdd_7_tier_expands_to_ordered_cross_cli_chain` | B（模块不存在） | §3.3 步骤 3：tier → 有序跨 CLI 候选链（机器级绑定声明顺序逐项一致） |
| BDD-8 | `test_tag0034_native.py::test_bdd_8_effort_maps_to_codex_reasoning_flag` | B | §3.4：Codex `-c model_reasoning_effort=<e>` / `spawn_agent(reasoning_effort=)` |
| BDD-9 | `test_tag0034_native.py::test_bdd_9_effort_maps_to_opencode_variant_flag` | B | §3.4：OpenCode `--variant <e>` 或 `#<e>` 后缀 |
| BDD-10 | `test_tag0034_native.py::test_bdd_10_effort_claude_code_capability_probe_supported_branch` / `..._absent_branch` / `..._platform_notes_records_effort_probe` | B + B + DA | §3.4 + §5 MV10 + `[BASELINE_CHANGE]`：探测到 `--effort` → 含 `--effort <e>`；未探测到 → 省略不报错；`platform-notes.md` 注明「能力探测 / 引入版本未核实」 |
| BDD-11 | `test_tag0034_resolve.py::test_bdd_11_phase_role_hit_beats_phase_level` | B | §3.3 步骤 1：`(phase,role)` 命中优先于 `phase` 级 |
| BDD-12 | `test_tag0034_resolve.py::test_bdd_12_fallback_to_phase_level_when_no_phase_role_entry` | B | §3.3 步骤 1：无 `(phase,role)` 条目 → 回落 `phase` 级 |
| BDD-13 | `test_tag0034_resolve.py::test_bdd_13_no_phase_entry_equals_standard` | B | §3.3 步骤 1：无 `phase` 条目 → `standard`（等价未配置） |
| BDD-14 | `test_tag0034_resolve.py::test_bdd_14_standard_is_inherit_parent_model_native_dispatch` | B | §3.2 / §3.3 步骤 2：`standard` 短路 `form='default'`、`model=<主 Agent 当前 model>` |
| BDD-15 | `test_tag0034_resolve.py::test_bdd_15_three_layer_priority_deterministic` | B | §3.3 BDD-15 定死点：四层优先级序、结果唯一确定 |
| BDD-16 | `test_tag0034_resolve.py::test_bdd_16_missing_config_returns_factory_default_no_error` | B | §3.3 全兜底：文件不存在 → 出厂默认、exit 0、无 error |
| BDD-17 | `test_tag0034_resolve.py::test_bdd_17_corrupt_config_type_bad_returns_factory_default` | B | §3.3 全兜底：YAML 坏 / 键类型坏 → 回落默认 + stderr WARNING，不抛异常 |
| BDD-18 | `test_tag0034_resolve.py::test_bdd_18_machine_binding_duplicate_tier_key_last_write_wins` | B | §3.3 BDD-18 定死点：`tier_bindings` 同名键 last-write-wins |
| BDD-19 | `test_tag0034_tryfall.py::test_bdd_19_no_probe_first_candidate_gets_real_ctx` | B | §3.7：无 probe，第一个动作即派真实 dispatch-context |
| BDD-20 | `test_tag0034_tryfall.py::test_bdd_20_launch_fail_falls_back_to_next` | B | §3.7：`LAUNCH_FAIL`（spawn OSError）→ `reason: launch_fail` 回落 |
| BDD-21 | `test_tag0034_tryfall.py::test_bdd_21_infra_error_falls_back_to_next` | B | §3.7：`INFRA_ERROR`（401/429/网络/崩溃/turn.failed）→ `reason: infra_error` 回落 |
| BDD-22 | `test_tag0034_tryfall.py::test_bdd_22_no_parseable_output_falls_back_to_next` | B | §3.7：`NO_PARSEABLE_OUTPUT`（产出缺失/空 / 空返回）→ `reason: no_parseable_output` 回落 |
| BDD-23 | `test_tag0034_tryfall.py::test_bdd_23_all_candidates_exhausted_falls_to_default_dispatch` | B | §3.7：全落空 → 默认派发、`final={"cli":"default"}`、`candidates_tried` 保留失败理由码 |
| BDD-24 | `test_tag0034_tryfall.py::test_bdd_24_fallback_only_on_infra_signals_not_quality` | B | §3.7 R1：产出质量差 / 不完整 归 `HAS_OUTPUT` —— 不回落 |
| BDD-25 | `test_tag0034_tryfall.py::test_bdd_25_any_gate_evaluable_output_stops_fallback` | B | §3.7 R1：收到 gate 能评产出即停、交 gate、不再试后续候选 |
| BDD-26 | `test_tag0034_tryfall.py::test_bdd_26_gate_fail_retries_same_candidate_no_new_dispatch_route_event` | B | §3.9 R1：gate FAIL → 同候选 retry、`dispatch_route` 计数不增；`gate_fail` 非 `outcome.kind` / 非 `reason` |
| BDD-27 | `test_tag0034_events.py::test_bdd_27_reason_gate_fail_rejected_by_check_events` | B（第 8 条未实现） | §3.8 M6：`check-events.py` 机械拒绝 `gate_fail` 理由码 → exit 1 |
| BDD-28 | `test_tag0034_tryfall.py::test_bdd_28_fallback_not_state_machine_retry` | B | §3.8：回落不写 `state_transition` / 不动 `retries` / 不触发 PAUSED，只写 1 条 `dispatch_route` |
| BDD-29 | `test_tag0034_events.py::test_bdd_29_dispatch_route_event_written_reuses_hash_chain` | B（写入端未实现） | §3.8：`dispatch_route` 事件复用 `append_event` 哈希链，`prev_hash == sha256(上一行原始文本)` |
| BDD-30 | `test_tag0034_events.py::test_bdd_30_check_events_knows_dispatch_route_as_valid_event_type` | B（`check-events.py` 源码无 `dispatch_route`） | §3.8：`check-events.py` 认 `dispatch_route` 为已知合法事件类型（第 8 条）；既有 `test_check_events.py` 零改动仍绿由全量回归兜底 |
| BDD-31 | `test_tag0034_native.py::test_bdd_31_native_claude_code_target_model_fully_resolved` | B | §3.4：Claude Code native —— 目标 model 全量算好、非父继承、会话零裁量 |
| BDD-32 | `test_tag0034_native.py::test_bdd_32_native_opencode_named_subagent_indirect_route` | B | §3.4 / R6：OpenCode native —— 命名 agent `agate-route-{tier}`、`agents.<name>.model` = 候选 model |
| BDD-33 | `test_tag0034_subprocess.py::test_bdd_33_claude_code_json_output_parsed_for_success` | B | §3.7 判定表：`stop_reason=="end_turn"` + `result` 非空 → `HAS_OUTPUT`；否则回落。fixture `tag0034_claude_code/` |
| BDD-34 | `test_tag0034_subprocess.py::test_bdd_34_codex_success_judged_by_event_stream_not_exit_code` | B | §3.7 + R5：`turn.completed` vs `turn.failed` 判成败（不靠退出码）。fixture `tag0034_codex/turn_failed_exit0.jsonl` |
| BDD-35 | `test_tag0034_subprocess.py::test_bdd_35_codex_item_status_failed_vs_turn_failed_two_layers` | B | §3.3 / §3.7 注：turn 层为准；item 级 `status:"failed"` 永不触发回落。fixture `item_failed_turn_completed.jsonl` |
| BDD-36 | `test_tag0034_subprocess.py::test_bdd_36_opencode_step_finish_and_empty_return` | B | §3.7：`step_finish.part.reason=="stop"` + `text` part → `HAS_OUTPUT`；ProviderAuthError → infra_error；纯空返回 → no_parseable_output |
| BDD-37 | `test_tag0034_tmux.py::test_bdd_37_which_tmux_decides_wrap_or_bare` | B | §3.10：`which tmux` 决定 `tmux new-session ... | tee` 包裹 / 裸跑；两路径留痕逐字节一致 |
| BDD-38 | `test_tag0034_tmux.py::test_bdd_38_countdown_and_no_force_kill_with_client` | B | §3.10：`list-clients` 空 → `kill_now`；非空 → `let_countdown`；`N + 余量(10s)` 超时 → `force_kill` |
| BDD-39 | `test_tag0034_zero_change.py::test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change` | **RG（P3 绿属预期）** | §1.2：`check-gate.py` / `check-state-transition.py` / `phases.yaml` / `state-machine.md` + `test_tag0027_b2_*` 逐字节不变（基线 `tag0034_regression_baseline.json`） |
| BDD-40 | `test_tag0034_zero_change.py::test_bdd_40_no_config_equals_byte_for_byte_status_quo` | RG + B（至少一断言红） | §1.2 R4：无配置 = 逐字节现状；`dispatch_route` 事件条数 = 0（基线绿）+ `load_config`/`resolve` 出厂默认路径（B 类红） |
| BDD-41 | `test_tag0034_docs.py::test_bdd_41_dispatch_protocol_gate_decoupling_and_invariants` | DA | M7：`dispatch-protocol.md` 新节「不认谁生产的」+「候选回落 ≠ 状态机 retry」+「gate FAIL 绝不换候选」+ 步位于铁律 1 之前 |
| BDD-42 | `test_tag0034_subprocess.py::test_bdd_42_routed_away_judge_verdict_platform_independent` | B（+ RG 子断言） | §1.2：`check-judge-verdict.py` / `check-p6-provenance.py` 不读平台 transcript（零改动）；`routed_away_verdict_location("codex") == "TASK_DIR"` |
| BDD-43 | `test_tag0034_interaction.py::test_bdd_43_parallel_batch_each_subagent_resolves_independently` | B | §3.9：`resolve` 纯函数、无跨调用状态；同 role 并行分片解析到同一条路由 |
| BDD-44 | `test_tag0034_interaction.py::test_bdd_44_autonomous_redispatch_does_not_consult_routing_table` | B | §3.9：RM-AG0055 自主再派发不解析路由表、继承父 cli/model、无 `dispatch_route` 事件 |
| BDD-45 | `test_tag0034_interaction.py::test_bdd_45_single_agent_mode_route_is_noop` / `..._declared_out_of_scope_in_docs` | B + DA | §3.9：`has_task_tool:false` → `route_is_noop` True；`dispatch-protocol.md` / design-note 显式写「单 Agent 模式路由不适用 / no-op」 |
| BDD-46 | `test_tag0034_docs.py::test_bdd_46_designnote_config_location_and_core_loop_rewritten` | DA | §9 项 1/2：design-note 三层落点 + 核心循环去「按序探测」改 try-and-fall（锚：`try-and-fall` / `agate-workspace/dispatch-routing.yaml` / `dispatch-tiers.yaml`） |
| BDD-47 | `test_tag0034_docs.py::test_bdd_47_roadmap_rm_ag0060_old_wording_rewritten` | DA | §9：roadmap RM-AG0060 行不再含「按序探测」，含 `try-and-fall` |
| BDD-48 | `test_tag0034_docs.py::test_bdd_48_architect_batch_design_doc_content_is_p4_boundary` | DA | §4.3 草稿①：`architect.md`「批次设计」节「补协议文档正文 = P4」+「跨文件一致性验证」（P7） |
| BDD-49 | `test_tag0034_docs.py::test_bdd_49_dispatch_protocol_author_vs_consistency_boundary` | DA | §4.3 草稿②：`dispatch-protocol.md`「派发编排机制」节「author 文档内容 = P4 / 跨文件一致性验证 = P7」；节标题仍存在 |
| BDD-50 | `test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes` | **红（P3 红属预期，见下 [P2_DESIGN_YAML_FENCE]）** | §8 `P5_consistency`：`check-protocol-consistency.py --strict-errors-only` → exit 0（BDD-48/49 就位 + 既有 fence ERROR 处理后）。P4/P7 转绿 |
| BDD-51 | `test_tag0034_interaction.py::test_bdd_51_p5_to_p4_retreat_reresolves_route_no_upgrade_logic` / `..._resolve_is_stateless_no_previous_failure_input` | DA + B | §3.9 BDD-26 vs 51：跨阶段回退机械重解析、无升档逻辑；`resolve` 无状态、签名不含「上次失败」类入参 |
| BDD-52 | `test_tag0034_docs.py::test_bdd_52_designnote_two_axes_key_and_mitigation_labels` | DA | §9 项 3/4：design-note 两正交轴 + `(phase,role)` key + 弱/强缓解 + 自动化不对称 |
| BDD-53 | `test_tag0034_docs.py::test_bdd_53_designnote_integrity_invariants_and_per_machine` | DA | §9 项 5/6：design-note 两条完整性不变量 + per-machine 机会式 / 不追求跨机可复现 |
| T1 | `test_tag0034_resolve.py::test_t1_resolve_return_contract_key_set_and_form_enum` | B | P2-review 测试缺口 T1 / N2：`resolve` 每分支返回键集恒 `{form,chain,model,effort}`、`form ∈ {'default','chain'}`、`form=='default'` → `chain is None` |
| T2 | `test_tag0034_tryfall.py::test_t2_hang_kill_maps_to_infra_error` | B | P2-review 测试缺口 T2 / N6：`wait(pid)` 超时 / RM-AG0055 命令流阈值触发 kill → `INFRA_ERROR` / `infra_error` |
| T3 | `test_tag0034_events.py::test_t3_check_events_reason_enum_parametrized` | B | P2-review 测试缺口 T3：三合法理由码各一条账本 exit 0 + 混入 `gate_fail` exit 1 |

---

## 回归护栏声明（BDD-39 / 40 —— P3 绿属预期，非 TDD 违规）

- **BDD-39**：长期不变量护栏（test-designer 卡片「永久回归测试判据」允许断言当前状态）。
  P3 捕获 `agate/rules/phases.yaml` / `agate/scripts/check-gate.py` /
  `agate/scripts/check-state-transition.py` / `agate/state-machine.md` /
  `agate/tests/unit/test_tag0027_b2_agate_dispatch.py` /
  `agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py` 的 sha256 到
  `agate/tests/fixtures/tag0034_regression_baseline.json`；测试断言「当前内容 hash == 基线 hash」。
  **P3 时绿**。本任务任何阶段使这些文件字节变化 → 转红（BDD-39 违反）。
- **BDD-40**：端到端「跑完整 P1→P8 无配置」+「加载器无 `dispatch-routing.yaml` 返回出厂默认」部分
  依赖路由机制存在 → **该部分红**（B 类，`agate_dispatch_route` 待建）；「`dispatch_route` 事件
  条数 = 0」账本部分 **P3 绿**（回归基线）。**整体：BDD-40 至少一个断言红**。

---

## [P2_DESIGN_YAML_FENCE] —— P3 阶段发现（非本 test-designer 引入，报主 Agent）

`check-protocol-consistency.py --strict-errors-only` 在 worktree 当前 HEAD（`b851b1e`）即
**exit 1（1 ERROR）**：`YAML 代码块无法解析: mapping values are not allowed here
[agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md:364]`——P2-design.md §4.1 的
```yaml `dispatch_plan` 多行 flow 代码块（P2 产出、已 commit）。

- 与本 test-designer 新增测试文件 / fixture **无关**（新增前后同样 exit 1）。
- 影响：BDD-50（`--strict-errors-only` exit 0）在 P3 红——除「BDD-48/49 文档修订未就位」外，
  另叠加此既有 fence ERROR。
- 建议：主 Agent 决定 P4/P7 是否顺带修 `P2-design.md:364` 的 ```yaml fence（改单行 flow /
  改 ```text 围栏），或将其登记为独立 debt。**test-designer 不改 P2 产出**（P1 基线保护同理）。

---

## 环境隔离

`[PROD_NOT_TOUCHED]` —— 仅在 worktree 内读 P0/P1/P2/P2-review/角色定义/现状生产脚本源码 +
写 `agate/tests/`（新增 10 个 `test_tag0034_*.py` + 4 组 fixture）+ 本文件 + `P3-progress.md`。
未触碰主 checkout `/home/kity/oclab/agateon` 与 `~/.agate` 稳定版。
