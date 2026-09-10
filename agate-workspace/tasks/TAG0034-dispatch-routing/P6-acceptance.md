---
phase: P6
task_id: TAG0034
type: acceptance
parent: P5-verification.md
trace_id: TAG0034-P6-20260910
status: draft
created: 2026-09-10
agent: verifier
pass: 53
fail: 0
ui_affected: false
---

# P6 验收报告 — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060）

> 对 `P1-requirements.md` §4 的 **53 条 BDD（BDD-1~53）逐条**验收。每条只允许 PASS / FAIL，二值，无中间态。
> `grep -c '^#### BDD-' P1-requirements.md` = 53 ；本报告 PASS + FAIL = 53 ≥ 53。
> `ui_affected: false` —— 无 vision / 截图；证据 = `pytest -k tag0034` 全量实跑日志 + doc-assertion grep 命中 + `git diff` 零改动 + 平台无关 grep。
> 系统 `python3` / worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；HEAD = `2772891`（P5 通过点），`p5_pass_commit = 92edcfc`，P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` / P1 `f75e129`。

`[NO_NEED_CONFIRM]`
`[PROD_NOT_TOUCHED]` —— P6 未改任何 `agate/` 下代码 / 测试 / 配置 / 协议文档；仅 worktree 内读 + 写本文件与 `P6-evidence/`。主 checkout `/home/kity/oclab/agateon` 与 `~/.agate` 未写入（仅只读检查）。post-test 环境残留检查见 §5。

---

## 1. 验收方法

- **功能类 BDD**：`timeout 400 python3 -m pytest agate/tests/ -k tag0034 -q` 全量实跑 → **90 passed / 0 failed / 1537 deselected**，`EXIT_CODE: 0`。逐条 BDD 均有直接 `test_bdd_NN_*` 用例（`-v` 清单见 `P6-evidence/pytest-tag0034.log`），另含 T1/T2/T3 契约用例。
- **文档断言类 BDD**：对目标文件 grep 关键语义短语，命中行（`file:line`）落 `P6-evidence/doc-assertions.log`。
- **回归护栏类 BDD（39/40）**：`git diff --stat f75e129..HEAD` 对 `phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` 无输出（零改动）+ `test_tag0034_zero_change.py` 实跑 + `grep -c dispatch_route <task>/gate-events.jsonl` = 0，落 `P6-evidence/regression-zero-change.log`。
- **BDD-42**：`grep -nE '\.codex/sessions|\.claude/projects'` 两校验器 0 命中 + `git log`/`git diff` 确认任务范围零改动 + `test_bdd_42` 实跑，落 `P6-evidence/bdd-42-platform-independence.log`。
- **P5 证据复用（审计 7）**：`git diff --stat 92edcfc..HEAD -- . ':(exclude)agate-workspace/tasks/*'` 无输出 → P5→P6 间无非产出文件改动 → `reuse_allowed`；BDD-40 的「全量回归全绿」部分引 `../P5-test-results/unit.md`（1625 passed / 0 failed / 2 skipped）。

---

## 2. BDD 逐条验收结果

> 证据路径相对 `P6-evidence/`。多文件证据逗号分隔。

### 4.1 schema 校验（check-dispatch-routing.py）

- PASS BDD-1: tier + effort 两正交轴任意组合被接受，校验器 exit 0（`test_bdd_1_tier_effort_two_axes_accepted`）(pytest-tag0034.log)
- PASS BDD-2: 同一 `(phase,role)` 同时写 `tier:` 与 `candidates:` → 校验器 exit 1（互斥）（`test_bdd_2_tier_candidates_mutually_exclusive`）(pytest-tag0034.log)
- PASS BDD-3: `P4:`（phase 级）与 `P4.review:`（`(phase,role)` 级）两种 key 形态均合法识别，role 段可选，exit 0（`test_bdd_3_phase_role_key_optional`）(pytest-tag0034.log)
- PASS BDD-4: `cli: gpt-4`（不在 `{native, claude-code, codex, opencode}`）被拒，exit 1（`test_bdd_4_invalid_cli_rejected`）(pytest-tag0034.log)
- PASS BDD-5: `effort: turbo`（不在 `{low, medium, high}`）被拒，exit 1（`test_bdd_5_invalid_effort_rejected`）(pytest-tag0034.log)
- PASS BDD-6: `fallback:` 字段不在 schema，出现即 exit 1（终点回落恒为默认派发、不可配）（`test_bdd_6_fallback_field_illegal`）(pytest-tag0034.log)

### 4.2 档位→跨 CLI 候选链展开 + effort 各平台映射

- PASS BDD-7: `tier: deep` 引用展开为机器级绑定的有序跨 CLI 候选链，顺序与声明逐项一致（`test_bdd_7_tier_expands_to_ordered_cross_cli_chain`）(pytest-tag0034.log)
- PASS BDD-8: `effort: high` 映射到 Codex `-c model_reasoning_effort=high`（子进程）/ `reasoning_effort` （native）（`test_bdd_8_effort_maps_to_codex_reasoning_flag`）(pytest-tag0034.log)
- PASS BDD-9: `effort: high` 映射到 OpenCode `--variant high`（或 `provider/M#high`）（`test_bdd_9_effort_maps_to_opencode_variant_flag`）(pytest-tag0034.log)
- PASS BDD-10: 探测到 `claude --help` 含 `--effort` → 命令含 `--effort high`；未探测到 → 命令不含任何 effort/reasoning flag、不报错、正常派发；`platform-notes.md` 注明「2.1.266 有 / 2.1.263 无 / 引入版本未核实」（`test_bdd_10_effort_claude_code_capability_probe_supported_branch`, `test_bdd_10_effort_claude_code_capability_probe_absent_branch`, `test_bdd_10_platform_notes_records_effort_probe`）(pytest-tag0034.log, doc-assertions.log)

### 4.3 解析顺序

- PASS BDD-11: `(phase,role)` 命中（`P4.implementer:` 链 Y）优先于 phase 级（`P4:` 链 X）（`test_bdd_11_phase_role_hit_beats_phase_level`）(pytest-tag0034.log)
- PASS BDD-12: 无 `(phase,role)` 条目时回落 phase 级候选链（`test_bdd_12_fallback_to_phase_level_when_no_phase_role_entry`）(pytest-tag0034.log)
- PASS BDD-13: 无 phase 及 `phase.role` 任何条目 → 解析结果 = `standard`（等价未配置）（`test_bdd_13_no_phase_entry_equals_standard`）(pytest-tag0034.log)

### 4.4 standard 语义钉死

- PASS BDD-14: `standard`（显式配 `tier: standard` 或未配置）= 主 Agent 当前平台原生派发 + 继承当前 model，不起子进程、不改 model，与「机制未启用」逐字节一致（`test_bdd_14_standard_is_inherit_parent_model_native_dispatch`）(pytest-tag0034.log)

### 4.5 三层配置优先级 + 合并语义 + 全兜底

- PASS BDD-15: 三层优先级（项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认）确定、结果唯一，无运行时「取谁含糊」分支（`test_bdd_15_three_layer_priority_deterministic`）(pytest-tag0034.log)
- PASS BDD-16: `dispatch-routing.yaml` 不存在 → 加载器返回出厂默认（全 `standard`）、exit 0、无 error（`test_bdd_16_missing_config_returns_factory_default_no_error`）(pytest-tag0034.log)
- PASS BDD-17: YAML 解析失败 / 键类型坏 → 回落出厂默认、一行 stderr WARNING、exit 0，不抛异常不静默跳过（复用 `_load_config` 判据形态）（`test_bdd_17_corrupt_config_type_bad_returns_factory_default`）(pytest-tag0034.log)
- PASS BDD-18: 机器级同名档位键冲突按 last-write-wins 取唯一结果，不产生「两条都生效」歧义（`test_bdd_18_machine_binding_duplicate_tier_key_last_write_wins`）(pytest-tag0034.log)

### 4.6 try-and-fall 逐级回落（无 probe）

- PASS BDD-19: 无 probe——第一个动作即把真实 dispatch-context 派给首选候选，不发「探测 / hi」预请求（`test_bdd_19_no_probe_first_candidate_gets_real_ctx`）(pytest-tag0034.log)
- PASS BDD-20: 子进程无法启动（OSError / 可执行文件缺失）→ 理由码 `launch_fail`，派发下一候选（`test_bdd_20_launch_fail_falls_back_to_next`）(pytest-tag0034.log)
- PASS BDD-21: 启动了但 auth/网络/429/进程崩溃 → 理由码 `infra_error`，派发下一候选（`test_bdd_21_infra_error_falls_back_to_next`）(pytest-tag0034.log)
- PASS BDD-22: 正常结束但无 gate 能评产出（产出文件缺失/空 / 空返回）→ 理由码 `no_parseable_output`，派发下一候选（`test_bdd_22_no_parseable_output_falls_back_to_next`）(pytest-tag0034.log)
- PASS BDD-23: 全部候选以三类基础设施理由码失败 → 回落默认派发，`final` 记 `{"cli": "default"}`，`candidates_tried` 保留每个失败理由码（`test_bdd_23_all_candidates_exhausted_falls_to_default_dispatch`）(pytest-tag0034.log)

### 4.7 完整性不变量（模型购物完整性洞——最高危）

- PASS BDD-24: 首选候选产出了 gate 能评的东西但质量差/不完整 → **不回落**（仅三类基础设施信号触发回落，产出质量不是回落信号）（`test_bdd_24_fallback_only_on_infra_signals_not_quality`）(pytest-tag0034.log)
- PASS BDD-25: 收到约定产出文件（非空、格式合法）即判路由成功、停止尝试后续候选、把产出交 gate（`test_bdd_25_any_gate_evaluable_output_stops_fallback`）(pytest-tag0034.log)
- PASS BDD-26: gate 判 FAIL → retry 在**同一候选**上重跑（不重新解析换候选）；本次 retry 不新增 `dispatch_route` 事件（条数与 gate FAIL 前相同）（`test_bdd_26_gate_fail_retries_same_candidate_no_new_dispatch_route_event`）(pytest-tag0034.log)
- PASS BDD-27: `dispatch_route` 某 `candidates_tried[].reason` = `gate_fail`（或任何非三值）→ `check-events.py` exit 1；合法三值任一 → exit 0（`test_bdd_27_reason_gate_fail_rejected_by_check_events`, `test_t3_check_events_reason_enum_parametrized`）(pytest-tag0034.log)

### 4.8 候选回落 ≠ 状态机 retry

- PASS BDD-28: 候选链回落 2 次后第 3 候选成功 → `retries[Pn]` 不变、无新增 `state_transition` 事件、未进入 PAUSED，只新增 1 条 `dispatch_route` 事件（`test_bdd_28_fallback_not_state_machine_retry`）(pytest-tag0034.log)

### 4.9 dispatch_route 事件 + check-events 校验端

- PASS BDD-29: `dispatch_route` 事件行 `prev_hash` == sha256(上一行原始文本)、`ts` 单调不减，`check-events.py` 哈希链/ts 审计 exit 0（`test_bdd_29_dispatch_route_event_written_reuses_hash_chain`）(pytest-tag0034.log)
- PASS BDD-30: `check-events.py` 认合法 `dispatch_route` 为已知事件类型（不判「非法未知 event」）；既有 `test_check_events.py` 用例零改动仍绿（`test_bdd_30_check_events_knows_dispatch_route_as_valid_event_type`）(pytest-tag0034.log)

### 4.10 cli: native 各平台执行

- PASS BDD-31: `{cli: native, model: haiku}` on Claude Code —— `--output-format json` 的 `modelUsage` 实际 model 与候选解析目标一致（`haiku`，非父继承 `claude-sonnet-parent`），驱动会话侧无自由裁量（`test_bdd_31_native_claude_code_target_model_fully_resolved`）(pytest-tag0034.log)
- PASS BDD-32: `{cli: native, model: provider/M-pro}` on OpenCode —— 存在 phase→预配命名 agent 映射 + 预注册机制，被派命名 agent 的 `agents.<name>.model` = `provider/M-pro`，子代理跑该配置 model（`test_bdd_32_native_opencode_named_subagent_indirect_route`）(pytest-tag0034.log)

### 4.11 跨 CLI 子进程 spawn + 结构化输出解析

- PASS BDD-33: `claude -p --output-format json --model X --dangerously-skip-permissions` spawn + 用 `stop_reason == "end_turn"` 判正常、`modelUsage` 确认 model；非 `end_turn` 或空输出 → 判失败进回落（`test_bdd_33_claude_code_json_output_parsed_for_success`）(pytest-tag0034.log)
- PASS BDD-34: Codex「进程 exit 0 但实际失败」样本 → 依 `turn.completed` vs `turn.failed` 判成败（不依退出码），该样本被正确判失败并进回落（`test_bdd_34_codex_success_judged_by_event_stream_not_exit_code`）(pytest-tag0034.log)
- PASS BDD-35: Codex `payload.item.status == "failed"`（带 `exit_code`）但 turn 整体 `turn.completed` → 按 P2 明确取的层（turn 层）判定 = 「该 turn 整体成功」，不因 item 级 `status:failed` 换候选（`test_bdd_35_codex_item_status_failed_vs_turn_failed_two_layers`）(pytest-tag0034.log)
- PASS BDD-36: OpenCode `--format json` 用 `step_finish.part.reason == "stop"` 判正常；失效 provider 空返回（无 `text` part / 结构化 Error）被判失败并进回落（`test_bdd_36_opencode_step_finish_and_empty_return`）(pytest-tag0034.log)

### 4.12 tmux 观测层（P4c，不通过不影响 P4a/P4b —— feature flag 默认关；BDD-37/38 断言的纯逻辑 helper 已转绿）

- PASS BDD-37: `which tmux` 成功 → `tmux new-session -d -s <命名空间-task-phase-ts> '<cmd> | tee <capture>'` 且 capture 被 tail；失败 → 裸跑子进程；两场景 `dispatch_route` 留痕与 gate 结果逐字节一致（`test_bdd_37_which_tmux_decides_wrap_or_bare`）(pytest-tag0034.log)
- PASS BDD-38: wrapper N 秒退出倒计时（默认 ≈15、可配）；`list-clients` 为空 → 直接 `kill-session`，非空 → 不强杀让倒计时收尾；超过 `N + 余量` → 兜底强杀（`test_bdd_38_countdown_and_no_force_kill_with_client`）(pytest-tag0034.log)

### 4.13 回归证明（零改动 + 不配置 = 逐字节现状）

- PASS BDD-39: `check-gate.py` / `check-state-transition.py` / `phases.yaml` / `state-machine.md` 结构化部分 —— `git diff --stat f75e129..HEAD` 无输出（逐字节不变）；`test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` 零改动仍绿（`test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change`）(pytest-tag0034.log, regression-zero-change.log)
- PASS BDD-40: 无 `dispatch-routing.yaml` / 无机器级绑定 / 出厂默认全 `standard` → 各阶段派发方式、产出、事件账本与机制引入前一致，`dispatch_route` 事件条数 = 0（`grep -c dispatch_route <task>/gate-events.jsonl` = 0）；全量回归全绿引 P5 通过证据（审计 7 判 `reuse_allowed`，P5→P6 无代码改动）（`test_bdd_40_no_config_equals_byte_for_byte_status_quo`）(regression-zero-change.log, ../P5-test-results/unit.md)

- PASS BDD-41: `dispatch-protocol.md` 新增「### 0. 派发路由」节含「gate 判定只认产出文件 + exit code，不认谁生产的」+「候选回落 ≠ 状态机 retry」+「gate FAIL 绝不换候选」两条完整性不变量，且「查表 → 派首选 → 逐级回落 → 再派发」步位于铁律 1 之前（`test_bdd_41_dispatch_protocol_gate_decoupling_and_invariants`；doc-assertions.log 命中 dispatch-protocol.md:506/514/529/535/538）(pytest-tag0034.log, doc-assertions.log)

### 4.14 routed-away judge verdict 平台无关性

- PASS BDD-42: judge 路由到 codex/opencode 子进程、verdict + 证据写入 `TASK_DIR` → `check-gate.py P6.5`（= `check-judge-verdict.py` + `check-events.py`）exit 0；两校验器 `grep -nE '\.codex/sessions|\.claude/projects'` 0 命中（纯 `TASK_DIR` 文件解析），本任务范围 `f75e129..HEAD` 对这两脚本无 commit、零字节改动（`test_bdd_42_routed_away_judge_verdict_platform_independent`）(pytest-tag0034.log, bdd-42-platform-independence.log)

### 4.15 与既有派发机制的交互

- PASS BDD-43: 并行模式多 subagent —— 每个独立解析 `(phase,role)`；同 role 并行分片解析到同一条路由，不同 role 各按自己的 `(phase,role)` 解析（`test_bdd_43_parallel_batch_each_subagent_resolves_independently`）(pytest-tag0034.log)
- PASS BDD-44: 授权范围内自主再派发的子任务不解析 `dispatch-routing.yaml`，继承父的实际 cli/model，无 `dispatch_route` 事件产生（`test_bdd_44_autonomous_redispatch_does_not_consult_routing_table`）(pytest-tag0034.log)
- PASS BDD-45: `has_task_tool: false` → 无派发动作、路由为 no-op；`dispatch-protocol.md` 显式写「单 Agent 模式……路由为 no-op，本节不适用（显式出范围）」（`test_bdd_45_single_agent_mode_route_is_noop`, `test_bdd_45_single_agent_mode_declared_out_of_scope_in_docs`；doc-assertions.log 命中 dispatch-protocol.md:565-566）(pytest-tag0034.log, doc-assertions.log)

### 4.16 design-note 修订 + roadmap 回写

- PASS BDD-46: design-note 头部「做什么」+ §2.1 + §2.2 —— 配置落点改三层落点（项目级文件 `agate-workspace/dispatch-routing.yaml` + 协议本体 `agate/rules/dispatch-tiers.yaml`），核心循环改 try-and-fall（§2.2 标题「查表 → 派首选 → 逐级回落 → 再派发（try-and-fall，无 probe）」），范围内无「按序探测」残留（`test_bdd_46_designnote_config_location_and_core_loop_rewritten`；doc-assertions.log 命中 design-dispatch-routing.md:3/5/46-47/71/77）(pytest-tag0034.log, doc-assertions.log)
- PASS BDD-47: `roadmap.md` RM-AG0060 表行不再含 `rules/dispatch-routing.yaml` 与「按序探测」，含 try-and-fall + 两轴 + 项目级落点（`test_bdd_47_roadmap_rm_ag0060_old_wording_rewritten`；doc-assertions.log 命中 roadmap.md:68 + neg-check 无禁用措辞）(pytest-tag0034.log, doc-assertions.log)

### 4.17 DEBT0039 文档边界澄清（SCOPE+ 用户批准并入）

- PASS BDD-48: `architect.md`「## 批次设计」节含显式说明「补协议文档正文（`platform-notes.md` / `SETUP.md` / phase-cards 等）= P4 实现工作，批次执行阶段标 P4；P7 一致性检查只做跨文件一致性验证、不 author 文档内容」（`test_bdd_48_architect_batch_design_doc_content_is_p4_boundary`；doc-assertions.log 命中 architect.md:209/225）(pytest-tag0034.log, doc-assertions.log)
- PASS BDD-49: `dispatch-protocol.md`「## 派发编排机制」节仍存在，且含显式区分「author 文档内容 = P4 / 跨文件一致性验证 = P7」（`test_bdd_49_dispatch_protocol_author_vs_consistency_boundary`；doc-assertions.log 命中 dispatch-protocol.md:502/588）(pytest-tag0034.log, doc-assertions.log)
- PASS BDD-50: 本任务全部改动就位后 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0（0 ERROR）（`test_bdd_50_consistency_zero_error_after_task_changes`；P5-test-results/unit.md §2 独立复核同口径 0 ERROR / 329 WARNING）(pytest-tag0034.log)

### 4.18 P5→P4 回退路由 + design-note 定案重写

- PASS BDD-51: P5→P4 跨阶段回退后 P4 retry —— 重新机械解析一次 `(phase,role)` 路由（按当时候选可用性落候选），**不注入**「上次失败 → 升档 / 换更强 model」逻辑；resolve 无状态（签名不接受「上次失败候选」入参，同输入恒同输出）；`dispatch-protocol.md` 新节写明该区分（`test_bdd_51_p5_to_p4_retreat_reresolves_route_no_upgrade_logic`, `test_bdd_51_resolve_is_stateless_no_previous_failure_input`；doc-assertions.log 命中 dispatch-protocol.md:570-571）(pytest-tag0034.log, doc-assertions.log)
- PASS BDD-52: design-note 含 `tier` + `effort` 两正交轴 + `(phase,role)` key（role 可选）；`cli: native` 标为**弱缓解**、跨 CLI 起子进程标为**强缓解**；含「自动化不对称」说明（`test_bdd_52_designnote_two_axes_key_and_mitigation_labels`；doc-assertions.log 命中 design-dispatch-routing.md:3/5/46-47/58/63-64/68/75）(pytest-tag0034.log, doc-assertions.log)
- PASS BDD-53: design-note 含「候选回落 ≠ 状态机 retry」与「gate FAIL 绝不换候选」两条完整性不变量的显式表述；含「routing 是 per-machine 机会式、不追求跨机可复现（只有抽象 `(phase,role)`→档位映射可 commit 共享）」的显式声明（`test_bdd_53_designnote_integrity_invariants_and_per_machine`；doc-assertions.log 命中 design-dispatch-routing.md:5/68）(pytest-tag0034.log, doc-assertions.log)

---

## 3. T1/T2/T3 契约用例（P2-review 折入，随对应 BDD 证据覆盖）

- T1（resolve 返回契约：key 集合 + form 枚举）—— `test_t1_resolve_return_contract_key_set_and_form_enum` PASSED（并入 §4.5 BDD-15~18 证据）(pytest-tag0034.log)
- T2（子进程挂死/kill → `infra_error`）—— `test_t2_hang_kill_maps_to_infra_error`, `test_dispatch_once_wait_timeout_infra_error` PASSED（并入 §4.6 BDD-21 证据）(pytest-tag0034.log)
- T3（`check-events.py` 理由码枚举三值参数化）—— `test_t3_check_events_reason_enum_parametrized` PASSED（并入 §4.7 BDD-27 证据）(pytest-tag0034.log)

---

## 4. 汇总

**Summary**: 53/53 PASS, 0 FAIL （PASS + FAIL = 53 ≥ P1 BDD 计数 53）

- 功能类 BDD：`pytest -k tag0034` 90 passed / 0 failed / `EXIT_CODE: 0`
- 文档断言类 BDD：全部关键措辞 grep 命中（`doc-assertions.log`）
- 回归护栏类 BDD-39/40：4 个核心文件 `git diff` 零改动 + `dispatch_route` 事件计数 0 + `zero_change` 测试 2 passed
- BDD-42：两校验器平台 transcript 路径 0 命中 + 任务范围零改动 + `test_bdd_42` PASS

### 观察（不判 FAIL，供 P7 一致性检查参考）

- `design-dispatch-routing.md` §5「影响面」(line 195) 与 §7「待确认事项」(line 220) 仍留旧串 `rules/dispatch-routing.yaml` / 「探测」。BDD-46 的 Then 判据范围明确限定为「头部『做什么』+ §2.1 + §2.2」，这三处已按 2026-09-09 定案重写、范围内无旧措辞；P3 编码的 `test_bdd_46` 为全文正向断言且通过。跨节残留属 P7 跨文件一致性验证范畴，本阶段记录不阻断。

---

## 5. post-test 环境残留检查

- `git status --porcelain` 验收后：
  - `M  agate-workspace/tasks/TAG0034-dispatch-routing/.state.yaml`（既有暂存，非本次产生）
  - ` M agate-workspace/tasks/TAG0034-dispatch-routing/gate-events.jsonl`（既有改动，非本次产生）
  - `?? .../P6-dispatch-context-verifier.md`（主 Agent 派发输入）
  - `?? .../P6-acceptance.md` + `?? .../P6-evidence/` + `?? .../P6-progress.md`（本阶段 P6 产出）
- 无 task dir 之外的意外文件；主 checkout `/home/kity/oclab/agateon` 与 `~/.agate` 未写入。
- 本任务测试为纯脚本 + mock/fixture，未创建外部资源（tmux session / 子进程 / 临时端口 / 数据库），无清理钩子残留对象。
- `[PROD_NOT_TOUCHED]`

---

## 6. 结论

53 条 BDD 逐条实跑，PASS 53 / FAIL 0。证据落 `P6-evidence/`（`pytest-tag0034.log` / `doc-assertions.log` / `regression-zero-change.log` / `bdd-42-platform-independence.log`，均含实质输出）+ 复用 `../P5-test-results/unit.md`（审计 7 `reuse_allowed`）。P6 未改任何代码 / 测试 / 配置 / 协议文档。gate 判定以主 Agent 亲跑 `check-gate.py P6` + `check-p6-evidence.py` + `check-p6-provenance.py` 为准。
