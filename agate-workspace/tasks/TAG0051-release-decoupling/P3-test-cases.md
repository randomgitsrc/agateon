---
phase: P3
task_id: TAG0051
type: test-design
parent: P2-design.md
trace_id: TAG0051-P3-20261011
status: draft
created: '2026-10-11'
agent: test-designer
test_code_dir: agate/tests/unit/
ui_affected: false
prod_touched: false
---

# P3 测试用例清单 — TAG0051 任务与发布解耦（TDD 红灯基线）

> **来源**：`P1-requirements.md`（**23 条 BDD**，1:1 映射）+ `P2-design.md`（方案 / §9 覆盖映射 / 8 批 `tests_filter`）+ `P2-review.md`（approved；NB-6..NB-9 体现见 §4）。
> **`test_code_dir: agate/tests/unit/`**（本仓惯例，见 TAG0042/TAG0050 的 P3 产出）。
> **状态标记**：`[PROD_NOT_TOUCHED]`——本阶段只写测试（全在 `tmp_path` / 只读仓库文本），未触发任何写生产 / push / tag / Release。
> **无 UI**（`ui_affected: false`）⇒ 不含 Playwright/E2E 用例。

---

## 1. 红灯现状（自跑实测）

`python3 -m pytest <8 个新文件> -q` → **36 用例：26 failed / 10 passed**。

- **26 条红灯全部为 B 类**（断言不成立 = 「被测实现未写」），**无 A 类**（无 `SyntaxError` / `ImportError` / `ModuleNotFoundError` / `Traceback`）——测试用 `subprocess` 调脚本 / 只读仓库文本，**不 import 任何尚未存在的符号**。
- 10 条当前即绿者为**回归锁 / 正向控制 / 非真空前置**（见 §2 备注），非「实现先于测试」：它们断言的是 P1 明确**保留**的既有行为（如 BDD-4/5/6/7/11）或本批的反向控制。

---

## 2. BDD → 用例映射（23 条，1:1，测试名引用 BDD 编号）

| BDD | 测试文件 | 用例 | 当前 |
|-----|----------|------|------|
| BDD-1 | `test_tag0051_docs_consistency.py` | `test_bdd_1_p8_ready_corpus_has_no_tag_conditions` | 红 |
| BDD-2 | `test_tag0051_p8_gate.py` | `test_bdd_2_p8_gate_no_tag_warning` | 红 |
| BDD-3 | `test_tag0051_p8_gate.py` | `test_bdd_3_p8_gate_no_version_warning` | 红 |
| BDD-4 | `test_tag0051_p8_gate.py` | `test_bdd_4_changelog_unreleased_with_task_id_exit_0` | 绿（回归锁） |
| BDD-5 | `test_tag0051_p8_gate.py` | `test_bdd_5_changelog_unreleased_without_task_id_exit_1` | 绿（回归锁） |
| BDD-6 | `test_tag0051_p8_gate.py` | `test_bdd_6_p8_gate_with_bump_type_exit_2` | 绿（回归锁） |
| BDD-7 | `test_tag0051_p8_gate.py` | `test_bdd_7_p8_gate_missing_bump_type_exit_1` | 绿（回归锁） |
| BDD-8 | `test_release_gate.py` | `test_bdd_8_release_workflow_has_workflow_dispatch` / `test_bdd_8_workflow_dispatch_coexists_with_push_tags` | 红 ×2 |
| BDD-9 | `test_release_gate.py` | `test_bdd_9_gate_passes_when_ci_success`（正向）/ `test_bdd_9_gate_fails_when_ci_not_success`（反例） | 红 ×2 |
| BDD-10 | `test_release_gate.py` | `test_bdd_10_gate_fails_when_push_branch_ci_failed` | 红 |
| BDD-11 | `test_release_gate.py` | `test_bdd_11_tag_verify_step_still_present` | 绿（回归锁） |
| BDD-12 | `test_release_gate.py` | `test_bdd_12_gate_fails_when_consistency_error` | 红 |
| BDD-13 | `test_release_gate.py` | `test_bdd_13_gate_fails_when_roadmap_rm_not_done` | 红 |
| BDD-14 | `test_tag0051_docs_consistency.py` | `test_bdd_14_agents_md_tag_timing_unified` / `test_bdd_14_git_integration_tag_timing_unified` | 红 ×2 |
| BDD-15 | `test_tag0051_docs_consistency.py` | `test_bdd_15_release_failure_rollback_first` | 红 |
| BDD-16 | `test_tag0051_delivery_contract.py` | `test_bdd_16_delivery_method_valid_enum_exit_2` | 绿（正向控制） |
| BDD-17 | `test_tag0051_delivery_contract.py` | `test_bdd_17_delivery_method_out_of_enum_exit_1` | 红 |
| BDD-18 | `test_tag0051_state_machine.py` | `test_bdd_18_state_machine_declares_release_authorization` / `test_bdd_18_state_machine_no_second_blocking_semantics` | 红 / 绿 |
| BDD-19 | `test_tag0051_p8_gate.py` | `test_bdd_19_no_dangling_config_migration_hint`（运行面/红）/ `test_bdd_19_gate_source_has_no_stale_preset_hint`（静态面/红） | 红 ×2 |
| BDD-20 | `test_tag0051_r6_harness.py` | `test_bdd_20_wrapper_exists_and_is_strict_shell`、`..._rejects_empty_dst`、`..._rejects_relative_dst`、`..._rejects_dst_inside_src`、`..._bad_args_do_not_touch_real_repo` | 红 ×5 |
| BDD-21 | `test_tag0051_obligations_sync.py` | `test_bdd_21_obl_p8_statements_have_no_version_tag_residue`、`test_bdd_21_obl_p8_04_remounted_to_method_enum`、`test_bdd_21_m_ids_keeps_obl_p8_04` | 红 ×2 / 绿 |
| BDD-22 | `test_tag0051_self_gate.py` | `test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review` | 红 |
| BDD-23 | `test_release_gate.py` | `test_bdd_23_release_gate_is_agate_star_subcommand`（支②）/ `test_bdd_23_no_new_check_star_script_added`（支①排除） | 红 / 绿 |

**备注（为何部分当前即绿）**：

- BDD-4/5/6/7/11 断言的是 P1 明确**保留**的既有行为（`check-changelog.py`、`bump_type`、tag 指向校验步）——它们是**回归锁**，改动前即绿是正确状态（P4 不得使它们变红）。
- BDD-16 是 BDD-17 的**正向控制**（合法枚举 → 放行），改动前即绿；BDD-17 因枚举校验未实现而红——一对红绿即证明判据非真空。
- BDD-18b / BDD-21c / BDD-23b 是**排除性 / 非真空**断言（不引入第二套阻塞语义、`M_IDS` 保持含 OBL-P8-04、未新增 `check-*.py`），改动前即绿属预期。

---

## 3. 与 P2 批次 `tests_filter` 对齐

| P2 批 | `tests_filter` | 本阶段对应测试文件 |
|-------|----------------|--------------------|
| `ready-no-tag` | `pytest agate/tests/unit/test_tag0051_p8_gate.py -q` | `test_tag0051_p8_gate.py`（**可单独跑**，满足 NB-9） |
| `obligations-sync` | `pytest agate/tests/unit/test_tag0050_obligations_enforcement.py agate/tests/unit/test_tag0050_obligation_behavior.py -q` | BDD-21 机械断言落在 `test_tag0051_obligations_sync.py`（P5 全量覆盖；P4 M7 亦可内联进 tag0050 文件） |
| `release-gate` | `pytest agate/tests/unit/test_release_gate.py -q` | `test_release_gate.py`（**对齐批 `tests_filter`**） |
| `p8-surfaces` / `p8-rules-roles` / `delivery-contract` / `release-docs` / `r6-harness` | 文档/契约/规则面（无 pytest filter） | `test_tag0051_docs_consistency.py` / `test_tag0051_state_machine.py` / `test_tag0051_delivery_contract.py` / `test_tag0051_r6_harness.py` |

> `test_release_gate.py` 采用 P2 §4 批 `release-gate` 的 `tests_filter` 同名文件（而非 `test_tag0051_release_gate.py`），以确保批级绿灯命令可直接命中。

---

## 4. P2 复评非阻塞项（NB-6..NB-9）在本阶段的体现

- **NB-6（提高 BDD-21 判别力）**：`test_bdd_21_obl_p8_statements_have_no_version_tag_residue` 用**更宽的根词黑名单**（`版本号` / `tag` / `version` / `双路径` / `最近 5 commit` / `bump 后`），**不**含裸 `bump`（避免误伤保留条目 `OBL-P8-01` 的 `bump_type`）——已对 `OBL-P8-01..14` **全量扫**确认对 10 条保留条目**零误伤**；并加 `OBL-P8-04` 重挂断言（`M` + `method_enum` + `enforced_at=gate_p8`）。
- **NB-7（BDD-4/5 直接测载体）**：BDD-4/5 **直接**测 `check-changelog.py <task_id>`，**不**写成「跑 `check-gate.py P8` 期望 CHANGELOG 告警」。
- **NB-8（wrapper 健壮性）**：`test_tag0051_r6_harness.py` 覆盖 `--dst` 为空 / 相对路径 / 位于 `--src` 之内 ⇒ **拒绝**，并在参数非法时断言真实仓库 `agate/` 未被改动。
- **NB-9（批级 smoke 可单独跑）**：`test_tag0051_p8_gate.py` 自包含（不 import 其余 `tag0051` 模块），`pytest <该文件> -q` 可独立跑红。

---

## 5. 固定下来的可测接缝（[DESIGN_GAP] → P4 契约，须实现为可判定的外部行为）

> P2 把「发布门 CI success 校验」的外部查询标注为「可注入命令（`--ci-cmd` / 环境变量）」，但未定死 CLI 形态。P3 为可测性**固定**如下外部契约（P4 implementer 依测试实现）：

```
agate-release.py gate --task <TASK_DIR> --sha <COMMITISH>
                     [--ci-cmd <CMD>] [--consistency-cmd <CMD>]
```
- `--ci-cmd`：stdout = JSON 数组 `[{"name","status","conclusion"}]`（目标提交 check-runs）；**任一** required 检查 `conclusion != success`（含 `in_progress`/`queued`）→ 门非 0；缺省 = 查 GitHub。
- `--consistency-cmd`：退出码即 consistency 结论（缺省 = 真跑 `check-protocol-consistency.py`）；非 0 → 门非 0。
- 命令经 `shlex.split` 后直接执行（无 shell）；`--task` 复用 `check-gate.py P8`（RM-AG0043 反查 / delivery / bump_type）。
- 全绿 → exit 0。

其余断言（BDD-1/2/3/14/15/16/17/18/19/20/21/22/23）落在**已有可观察契约**上（脚本退出码 / 文件检索 / YAML 解析 / git 事实），不绑定内部实现细节。

---

## 6. 平台无关自检（强制，实测）

- `python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/` → **0 命中**（`exit=0`）。
- `ruff check`（`ruff==0.16.4`）对 8 个新测试文件 → **All checks passed**。
- 平台无关做法：`tmp_path` / `git_repo` / `bash` / `python_exe` / `run_cli` fixtures；不裸 `python3`；不写字面系统临时目录（NB 说明见 `check-platform-assumptions.py` R4：`/tmp` 字面量连注释亦命中）；`subprocess` 文本模式均带 `encoding="utf-8"`（R6）。
- **写入隔离**：所有用例复用 `tmp_path` / `git_repo`（临时任务夹具 / level-2 账本**只读**复制 / 合成 git 仓库）；**不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本）；R6 全量差分由 `gate_commands.P5_r6` 在副本上跑，不在本单测内。

---

## 7. 新增测试夹具（属 P3 测试面，不计入 P2 §4 批产出）

- `agate/tests/fixtures/task-data/level-2/pass/gate-events.jsonl`、`.../level-2/fail/gate-events.jsonl`
  —— level-2 黄金 fixture 账本（`task_created.contract_level: 2`），供 BDD-16/17 定格 `task_level==2`（P2 §9.1）。`test_tag0051_delivery_contract.py::test_level2_fixture_encodes_contract_level_2` 守护其非真空。

---

## 8. 红线 / 后续

- P4 用本套测试驱动实现；P5 跑 `gate_commands`（`P5` 全量 + `P5_consistency` + `P5_obligations` + `P5_sg6` + `P5_r6`）验真。
- **不可逆外部动作**（push / PR / merge / tag / Release / 改分支保护）**不在测试内执行**，一律人工授权。
