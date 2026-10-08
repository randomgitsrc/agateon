---
phase: P3
task_id: TAG0050
type: test-cases
parent: P2-design.md
trace_id: TAG0050-P3-20261007
status: draft
created: '2026-10-07'
agent: test-designer
test_code_dir: agate/tests/
---
# P3 测试设计 — 任务数据契约：结构化判定、可信写入与任务版本（TAG0050）

> **口径**：功能任务（P1 缺 `change_type: refactor`）→ 走标准 TDD 口径：先写测试、当前全部红灯。
> **映射来源**：`P1-requirements.md` §4（77 条 BDD）+ `P2-design.md` §3（批↔BDD↔设计节）。
> **上游规格**：`docs/design-notes/design-tag0050-task-data-contract.md`（§0 F1–F15 / §2.9 / §10 验收锚）、
> `docs/reviews/tag0050-p2-expert-answers.md`（Q1–Q4 裁决）、`P2-design.md` §3.1（F4 规格）、§3.2/§3.3（r6 规格）。
> **本文件不预判 PASS/FAIL**——只登记「每条 BDD → 测试节点 → 先红锚」。

## 0. test_code_dir 声明

```
test_code_dir: agate/tests/
```

- 测试代码归入 `agate/tests/` 既有目录结构（按性质 unit / integration 归位），**未新建 P3-test-code/ 目录**——
  遵循本仓既有惯例（`agate/tests/{unit,integration,regression}/`）。
- 共享 helper：`agate/tests/helpers_tag0050.py`（哈希链账本构造、hook 安装、运行期取用 `agate_common` /
  `conftest.init_task`——**不在模块级引用未实现符号**，避免 collection error 被判 A 类假红灯）。

### 测试文件清单（10 批 + 跨批 + fitness）

| 文件 | 批 | BDD |
|---|---|---|
| `agate/tests/integration/test_tag0050_a0_a1_ledger.py` | A0 / A1 | BDD-01..22 |
| `agate/tests/integration/test_tag0050_ci_replay.py` | A2 | BDD-23..35 |
| `agate/tests/integration/test_tag0050_state_set.py` | A3 | BDD-36..39 |
| `agate/tests/unit/test_tag0050_obligations.py` | A4 | BDD-40..44 |
| `agate/tests/unit/test_tag0050_write_tools.py` | B | BDD-45..51 |
| `agate/tests/integration/test_tag0050_prod_touched.py` | C | BDD-52..55 |
| `agate/tests/integration/test_tag0050_evidence.py` | D | BDD-56..60 |
| `agate/tests/unit/test_tag0050_declarations.py` | E | BDD-61..66 |
| `agate/tests/unit/test_tag0050_proxy_judgment.py` | F | BDD-67..72 |
| `agate/tests/unit/test_tag0050_cross_batch.py` | 跨批 | BDD-73..77 |
| `agate/tests/unit/test_tag0050_fitness.py` | fitness | BDD-15/16/50 的架构适应度节点 |

### 粒度说明（为何单次派发且全批写入）

按 dispatch-context「任务粒度说明」：10 批共享同一套 conftest / 平台假设面 / 红灯口径，拆分会造成跨 subagent
测试文件冲突；故**单次派发、按批分节**。本次**未裁剪**——77 条 BDD 全部落地为真实测试（含 A2–F），
非仅 A0/A1。A2–F 中依赖新机制的用例以「契约级断言」设计（新 CLI 接口 / 快照定义 / `init_task()` 非 legacy 任务），
在当前代码下均失败；P4 实现后按批收敛。

## 1. 红灯确认

- **测试文件自跑**：11 个测试文件共 **82 个测试节点**（77 BDD：BDD-02 参数化为 P7/P5/P0 三例；+ 3 fitness），
  `python3 -m pytest <11 files> -q` → **82 failed**，无 SyntaxError / 第三方 import 失败（A 类关键词扫描 0 命中）。
- **`check-tdd-red.py agate-workspace/tasks/TAG0050-task-data-contract`** → **exit 0**。
  ⚠️ 实测口径：`gate_commands.P3 = "python3 -m pytest"`（全量、无 `-n`），本机全量串行 > 120s，
  check-tdd-red 以**超时（exit 124）→ 视为红灯可推进**返回 exit 0；若需**断言失败型真红灯**，
  主 Agent 可设 `AGATE_TDD_TIMEOUT=600` 或 `TEST_RUNNER="python3 -m pytest agate/tests/ -q --tb=no -n auto"`。
- **红灯原因**：均为「实现未写」——缺失脚本（`agate-task-init.py` / `agate-state-set.py` / `agate_schema.py`）、
  缺失符号（`agate_common.task_level` / `requirement_active` / `check_ledger_events` / `TASK_ID_RE` /
  `load_contract` / `project_root` / `resolve_evidence_ref`）、缺失交付物（`rules/task-data/LEVELS.yaml` /
  `level-1.yaml` / `r6-differential.sh` / `r6-allowlist.yaml` / 黄金 fixture）、或现状行为与 BDD 目标不一致
  （F8 留痕不落盘、check-gate 不存在目录 rc≠1、粗体/否定 PROD_TOUCHED、骨架子串判定等）。
- **`conftest.init_task()`**（A1 交付物，尚未存在）经 helper 运行期取用；引用它的用例红灯由 AttributeError 体现。

### 已知的非本任务失败（如实登记）

全量 `python3 -m pytest agate/tests/ -n auto` 实测 **83 failed / 2668 passed / 2 skipped**，其中
**82 failed = 本任务新增红灯**；余 1 条为**既有环境漂移**（与本任务无关，不在本任务范围）：

- `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
  ——本机 `opencode` CLI 子命令 `debug agent` 已更名为 `debug agents`（环境漂移，非 TAG0050 引入）。

## 2. 平台无关自查

- `python3 agate/scripts/check-platform-assumptions.py agate/tests/` → **exit 0（0 命中）**。
- 新增文件未使用裸 `python3`（用 `python_exe` fixture / `sys.executable`）、未硬编码 `PATH`、
  未写字面系统临时目录（用 pytest `tmp_path` / `git_repo`），注释中亦无字面量命中。
- ruff（`ruff==0.16.4`）：新增文件 `ruff check` 全通过。

## 3. BDD 逐条映射（1:1）

> 节点名格式 `<文件>::<测试函数>`；参数化节点以 `[P7]` 等后缀区分（同属该 BDD）。

### 批 A0 — hotfix（F8；check-gate 不存在目录 → rc=1）

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-01 | `test_tag0050_a0_a1_ledger.py::test_bdd_01_paused_prod_touched_persisted` | PAUSED + PROD_TOUCHED 提交后账本须含 `prod_touched_in_paused`；实测 F8 参数错→事件从未落盘 |
| BDD-02 | `test_tag0050_a0_a1_ledger.py::test_bdd_02_nonexistent_task_dir_returns_1[P7/P5/P0]` | 不存在目录须 rc=1；实测 P7=0、P5/P0=2 |

### 批 A1 — 契约等级与账本完整性

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-03 | `test_bdd_03_downgrade_event_errors` | 降级事件须 ERROR；`check-events.py` 现忽略事件规则 |
| BDD-04 | `test_bdd_04_second_task_created_errors` | 第 2 条 `task_created` 须 ERROR |
| BDD-05 | `test_bdd_05_task_created_not_first_line_errors` | `task_created` 非首行须 ERROR |
| BDD-06 | `test_bdd_06_unregistered_contract_level_errors` | 未登记等级须 ERROR |
| BDD-07 | `test_bdd_07_handwritten_low_level_new_task_errors` | 低于当前等级须 ERROR；`agate-task-init.py` 缺失 |
| BDD-08 | `test_bdd_08_created_backfill_keeps_judge` | `init_task()` 缺失（F3a） |
| BDD-09 | `test_bdd_09_judge_enabled_false_p65_still_blocks` | `init_task()` 缺失（F3b） |
| BDD-10 | `test_bdd_10_created_backfill_keeps_evidence_ref_blocking` | `init_task()` 缺失（F3c） |
| BDD-11 | `test_bdd_11_new_dir_without_created_event_errors` | 无创建事件新目录须 ERROR + `--existing` 入口 |
| BDD-12 | `test_bdd_12_git_mv_legacy_stays_legacy` | `agate_common.task_level` 缺失 |
| BDD-13 | `test_bdd_13_rewrite_or_delete_created_ledger_errors` | 删除含创建事件账本须 ERROR |
| BDD-14 | `test_bdd_14_legacy_done_to_p1_errors` | legacy 重开须给 `--adopt` 指引 |
| BDD-15 | `test_bdd_15_published_snapshot_freeze` | `rules/task-data/{LEVELS,level-1}.yaml` 缺失 |
| BDD-16 | `test_bdd_16_golden_fixtures_exist` | 黄金 fixture 缺失 |
| BDD-17 | `test_bdd_17_task_level_above_protocol_fails_closed` | fail-closed 升级提示缺失 |
| BDD-18 | `test_bdd_18_legacy_output_only_prod_touched_scanned` | 只暂存产出的安全门扫描缺失 |
| BDD-19 | `test_bdd_19_non_legacy_staged_output_reruns_phase_gate` | `init_task()` 缺失 |
| BDD-20 | `test_bdd_20_p7_adopted_p4_prose_gap_counted` | `init_task()` 缺失 |
| BDD-21 | `test_bdd_21_consecutive_upgrades_per_phase_level` | `requirement_active` 缺失 |
| BDD-22 | `test_bdd_22_r6_differential_deliverable` | `r6-differential.sh` / `r6-allowlist.yaml` 缺失 |

### 批 A2 — CI 回放（可信锚点，F15）

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-23 | `test_tag0050_ci_replay.py::test_bdd_23_pr_replay_passes` | 现状 `agate-ci-verify.py` 无回放口径（0 个新 token） |
| BDD-24 | `test_bdd_24_push_replay_passes` | 同上（push 口径） |
| BDD-25 | `test_bdd_25_no_verify_violation_fails_with_sha` | 须 FAIL 并指出提交 |
| BDD-26 | `test_bdd_26_ready_output_only_prod_touched_fails` | READY 后只改产出须 FAIL |
| BDD-27 | `test_bdd_27_missing_self_gate_trailer_fails` | commit-msg 回放缺失 |
| BDD-28 | `test_bdd_28_deleted_created_ledger_fails_mv_passes` | 删除创建事件账本须 FAIL |
| BDD-29 | `test_bdd_29_handwritten_low_level_task_created_fails` | 手写低等级须 FAIL |
| BDD-30 | `test_bdd_30_branch_crossing_upgrade_no_false_report` | 须以回放口径判定且不误报 |
| BDD-31 | `test_bdd_31_user_project_without_version_fails` | 未固定版本须 FAIL + 提示 |
| BDD-32 | `test_bdd_32_pr_downgrade_version_fails` | 降级 `.agate-version` 须 FAIL |
| BDD-33 | `test_bdd_33_pr_mid_upgrade_version_no_false_report` | 中途升级不误报 |
| BDD-34 | `test_bdd_34_no_task_dir_pr_skips_with_reason` | 无任务目录改动须 SKIP + 原因 |
| BDD-35 | `test_bdd_35_replay_interface_records_timing` | 回放须记录提交数与耗时（E4） |

> **测试仓库口径（2026-10-08 修正）**：`_task_commit_repo()`（BDD-23/24/25/26/27/28/29/30/35 用）
> 建的仓库写 `.agate-version`（`agate: v0.79.0`）并 commit——钉版本 ⇒ 可回放（设计 §2.4 分支①）。
> BDD-31 用**无 `.agate-version`、无协议本体**的使用者项目仓库 ⇒ 命中设计 §2.4 分支③ → FAIL。
> BDD-30（跨协议升级不误报）与 BDD-31（版本缺失判 FAIL）此前仓库逐字节相同、断言相反，属测试设计
> 矛盾；现以"是否钉版本"区分（BDD-31 才是"版本缺失"用例），两条断言均不改。

### 批 A3 — state-set 与状态事实

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-36 | `test_tag0050_state_set.py::test_bdd_36_state_set_rejects_illegal_transition` | `agate-state-set.py` 缺失 |
| BDD-37 | `test_bdd_37_retreat_writes_retries` | 同上；回退须写 retries |
| BDD-38 | `test_bdd_38_entering_ready_paused_writes_event` | 进入 PAUSED 须写 `state_transition`；`agate-next` 不再写 |
| BDD-39 | `test_bdd_39_non_legacy_status_written_errors` | `init_task()` 缺失；非 legacy 写 status 须 ERROR |

### 批 A4 — 义务执行方式机械核验（F13）

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-40 | `test_tag0050_obligations.py::test_bdd_40_f13_four_m_items_error` | `obligations.yaml` 无 `enforced_at`；check-obligations 现 rc=0 |
| BDD-41 | `test_bdd_41_missing_test_or_node_errors` | 无 `test: <节点>` 字段 |
| BDD-42 | `test_bdd_42_negative_control_mutation` | OBL-P8-02 无 `test`/`enforced_at` |
| BDD-43 | `test_bdd_43_r_without_review_output_errors` | 无 `review_output` 字段 |
| BDD-44 | `test_bdd_44_baseline_reset_supported` | 无 `baseline.reset` 支持 |

### 批 B — 写入工具与契约单源

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-45 | `test_tag0050_write_tools.py::test_bdd_45_seven_ops_and_config_roundtrip` | md-field-set 7 操作 / agate-config set/unset/explain 未实现 |
| BDD-46 | `test_bdd_46_system_field_reject_and_derive` | `init_task()` 缺失；系统字段拒写/现算未实现 |
| BDD-47 | `test_bdd_47_missing_frontmatter_errors` | `init_task()` 缺失；缺 frontmatter 须 ERROR（F10） |
| BDD-48 | `test_bdd_48_render_block_tamper_errors` | 无 `AGATE:RENDER` 渲染块支持 |
| BDD-49 | `test_bdd_49_fix_command_executes` | `explain` 未输出可照抄修复命令 |
| BDD-50 | `test_bdd_50_single_schema_implementation` | `agate_schema.py` 缺失 |
| BDD-51 | `test_bdd_51_e3_downgrade_or_zero_false_positive` | 快照（T1 绊线/降级）缺失 |

### 批 C — 生产接触

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-52 | `test_tag0050_prod_touched.py::test_bdd_52_missing_prod_touched_errors` | 快照 `primary_outputs`/`prod_touched` 缺失；`init_task()` 缺失 |
| BDD-53 | `test_bdd_53_prod_touched_true_not_paused_aborts` | prod_touched 中止语义未实现 |
| BDD-54 | `test_bdd_54_bold_marker_field_false_still_aborts` | 粗体 `**[PROD_TOUCHED]**` 现不拦（F4） |
| BDD-55 | `test_bdd_55_negation_form_blocks_with_guidance` | 无「疑似否定写法」专门指引（F4） |

### 批 D — 验收结论与证据绑定

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-56 | `test_tag0050_evidence.py::test_bdd_56_f1_abc_tampering_turns_red` | `init_task()` 缺失；D1/D2 未实现（F1） |
| BDD-57 | `test_bdd_57_ignored_evidence_errors` | `init_task()` 缺失（F9） |
| BDD-58 | `test_bdd_58_pass_log_nonzero_exit_errors` | `init_task()` 缺失 |
| BDD-59 | `test_bdd_59_run_ref_sha256_mismatch_errors` | `resolve_evidence_ref` 缺失 |
| BDD-60 | `test_bdd_60_extract_context_counts_equal_computed` | `init_task()` 缺失；计数现算未实现 |

### 批 E — 成对声明

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-61 | `test_tag0050_declarations.py::test_bdd_61_f2_blocker_count_not_covering_prose` | `init_task()` 缺失（F2） |
| BDD-62 | `test_bdd_62_cross_file_declaration_aggregation` | `init_task()` 缺失；跨文件聚合未实现 |
| BDD-63 | `test_bdd_63_parallel_ids_no_collision` | `init_task()` 缺失；ID 路径前缀编号未实现 |
| BDD-64 | `test_bdd_64_set_mismatch_or_dangling_errors` | `init_task()` 缺失 |
| BDD-65 | `test_bdd_65_resolved_missing_evidence_errors` | `init_task()` 缺失 |
| BDD-66 | `test_bdd_66_followup_debt_backref_required` | tech-debt 无 `source_ref` |

### 批 F — 代理判定（RM-AG0085 / RM-AG0087 / F12）

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-67 | `test_tag0050_proxy_judgment.py::test_bdd_67_ui_dimension_na_without_reason_errors` | `init_task()` 缺失 |
| BDD-68 | `test_bdd_68_reviewed_bdds_mismatch_errors` | `init_task()` 缺失 |
| BDD-69 | `test_bdd_69_skeleton_prose_not_treated_as_heading` | 骨架判定现为子串：散文提及 `## 骨架声明` 即通过（rc=2）→ 须 rc=1 |
| BDD-70 | `test_bdd_70_phase_set_not_closed_errors` | `init_task()` 缺失（RM-AG0087） |
| BDD-71 | `test_bdd_71_t2_catches_nonconforming_bdd_heading` | T2 绊线未实现（无统一格式指引） |
| BDD-72 | `test_bdd_72_p8_delivery_structured` | `init_task()` 缺失；delivery 子串判定未结构化（F12） |

### 跨批通用验收

| BDD | 测试节点 | 先红锚 |
|---|---|---|
| BDD-73 | `test_tag0050_cross_batch.py::test_bdd_73_each_batch_registers_snapshot` | `LEVELS.yaml` 缺失 |
| BDD-74 | `test_bdd_74_legacy_diff_allowlist_twelve` | `r6-allowlist.yaml` 缺失（D01..D12） |
| BDD-75 | `test_bdd_75_pytest_consistency_count` | `LEVELS.yaml` 缺失（快照冻结 CHECK 未落地） |
| BDD-76 | `test_bdd_76_baseline_reset_in_changelog` | CHANGELOG 无基线重设说明 |
| BDD-77 | `test_bdd_77_new_scripts_do_not_break_existing_tests` | 三个新增脚本缺失 |

### 架构适应度（P2 §6 判据三 / N2）

| BDD | 测试节点（`-k` 选择子串） | 先红锚 |
|---|---|---|
| BDD-15 | `test_tag0050_fitness.py::test_task_data_freeze_snapshot_sha256`（`task_data_freeze`） | `LEVELS.yaml`/sha256 登记缺失 |
| BDD-16 | `test_task_data_golden_fixture_regression`（`task_data_golden`） | 黄金 fixture 缺失 |
| BDD-50 | `test_schema_single_source_only_agate_schema`（`schema_single_source`） | `agate_schema.py` 缺失 |

## 4. F1–F15「改坏即红」口径落实

`P5_repro` 已从 `gate_commands` 移除（专家新发现：`repro-tag0050.sh` 只打印、不断言）。
F1–F15 的「改坏即红」改由**各批在非 legacy init 任务上构造同样篡改、断言判 FAIL 的 pytest 用例**承担：

- F1 → BDD-56（`init_task` 任务上构造 A/B/C 篡改，断言 P6 转红）；
- F2 → BDD-61；F3a/b/c → BDD-08/09/10；F4 → BDD-54/55；F8 → BDD-01；
- F9 → BDD-57；F10 → BDD-47；F12 → BDD-72；F13 → BDD-40..44；F15 → BDD-23..35。

上述用例引用 `conftest.init_task()`（A1 交付物），此刻因该 helper 缺失而红灯——符合 TDD。

## 5. 创建型用例清理钩子

本任务测试的临时资源一律在 pytest `tmp_path` / `git_repo` fixture 内创建（含 git 仓库、任务目录、
账本、证据文件），pytest 结束由 `tmp_path` 自动清理；**不写仓库内已提交文件**（尤其不碰真实
`gate-events.jsonl` 账本）。A2 的逐提交回放用例在 `tmp_path` 内的 git 仓库上运行，回放副本随 fixture 清理。

## 6. 环境隔离

`[PROD_NOT_TOUCHED]` 本 P3 仅在 agateon 本 checkout 内写测试与运行 pytest，未接触生产环境；
R6 差分相关用例（BDD-22/74）只断言交付物存在，未对真实仓库跑批量实验。
