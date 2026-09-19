---
agent: test-designer
phase: P3
task_id: TAG0036
parent: P2-design.md
trace_id: TAG0036-P3-20260919
type: test-design
created: '2026-09-19'
status: draft
---
# P3 测试用例映射（docs 半边）— TAG0036

> 测试代码：`agate/tests/unit/test_mvwu_protocol_docs.py`（65 个收集项；script 半边见 `test_check_mvwu.py` / `P3-test-cases.md`，本文件不覆盖）。
> 负责 BDD：1、2、3、5、6、7、8、9、10、11、12、59-71。BDD-4、13-58 属 script 半边。
> 权威源：P1 `口径 A-H` 与各 BDD「字面标记」，字面串逐字取自 P1；P2 §0.1 M1-M18 / §3 定插入位置（节标题用于 section 提取）。
> 红/绿分布（自检实测）：28 红（全为断言失败，无 SyntaxError / ImportError）、37 绿（回归守护）。

## 断言形式与三条设计取舍（P3 落断言时明确）

1. **git 基线依赖型断言不入永久测试**：BDD-3/5/9/12/67/68②/60/62 中 `git diff <内核基线>` 为空 / 无删除行的部分由 **P5 gate_commands**（`P5_kernel_diff` / `P5_kernel_diff_wt` / `P5_roles_diff` / `P5_history_untouched`）或 **P6 证据**承担（P2 R5；TAG0025「一次性交付事实」判据）。偏离 dispatch-context 第 9 条"用 `git show HEAD:<path>` 取基线"：`HEAD` 在 P4 提交后即含新内容、基线失真；固定 SHA `efb113b` 则在 `agate/adr.md`（已过时标注会改行）、`CONTEXT.md` 等后续合法编辑时假性变红。改为**嵌入不可变基线字面**：CONTEXT.md 28 个既有"术语"列（只增不删）、architect.md 四条硬规则（逐字 + 相邻），"恰新增 5 行 / 既有行逐字未变 / ADR 零删除行"的 `git diff` 部分转 P6 证据。
2. **"新增文字"的边界靠 P2 设计的节标题定位**：M2 `### batches[] 可选键…`、M5 `### 批切分判据与 tests_filter 写法…`、M8 标题含"审查锚点"、M9 头部（首个 `## ADR-` 前）、M4 P2 卡 `decisions/` 相关字面；节缺失即红（断言式），不因 fixture 错误而红。
3. **P1 留白由 P3 选定**：BDD-61 触发条件用正则 `≥2 / >=2 / 至少 2 / 2 个及以上 / 两个及以上` + 字面 `关键路径` `端到端`，目的用字面 `管道`（P1 引述"管道确实通"，取稳健子串）；BDD-59 四态 verdict 的 `PASS/FAIL/EXPECTED_RED/UNKNOWN` 与 boundary 的 `I1` 检查**整行**（术语列或定义列均可）；BDD-64 示例维度 ≥3（依赖方向 / 分层边界 / 循环依赖 / 公共 API 稳定性）；BDD-66 写入时机以"同一行含 `decisions/` 与 `写入`"判定；BDD-69 scripts/README 行含 `观测` `不阻断` `--observe` `verdict` 及 `0=`/`2=`。

## BDD → 用例映射

| BDD | 用例（`test_mvwu_protocol_docs.py::`） | 承担 | 当前 |
|-----|------|------|------|
| 1 | `test_bdd_1_tests_filter_roundtrip_via_md_field_get`（P1 原样例，`windows_smoke`）；`test_bdd_1_tests_filter_special_values_passthrough[5 参数：空格/管道/转义引号/参数化 id/`#`中文]` | 单测（回归守护，现绿） | 绿 |
| 2 | `test_bdd_2_gate_p2_accepts_tests_filter_same_as_without`（`check-gate.py P2`：含/不含 tests_filter，退出码=2 且输出一致）；`test_bdd_2_gate_p2_still_rejects_invalid_plan_with_tests_filter`（对照：缺 complexity 仍 exit 1，证明非 fail-open） | 单测（回归守护，现绿） | 绿 |
| 3 | `test_bdd_3_existing_gate_test_files_present[3 文件]`（既有三测试文件仍在且含用例）；`check-gate.py` 空 diff + 三文件全绿 → **P5_kernel_diff / P5_kernel_diff_wt + 全量 P5** | 单测 + P5 key | 绿 |
| 5 | `test_bdd_5_debt_entry_registers_gate_p2_fail_open`（含 `_gate_p2_dispatch_plan` 与 静默放行/`return None` 的 DEBT yaml 块，且含 `id: DEBT\d+`）；`test_bdd_5_check_debt_passes_on_tech_debt`（check-debt exit 0，回归守护）；`check-gate.py` 空 diff → **P5_debt + P5_kernel_diff** | 单测 + P5 key | 红 / 绿 |
| 6 | `test_bdd_6_p2_card_documents_tests_filter` | 单测 | 红 |
| 7 | `test_bdd_7_architect_documents_tests_filter_selection`；`test_bdd_7_architect_four_hard_rules_verbatim_and_adjacent`（四条硬规则逐字 + 相邻，回归守护） | 单测 | 红 / 绿 |
| 8 | `test_bdd_8_no_bare_python3_inside_tests_filter_examples`（P1 原正则，agate/ 除 tests/，回归守护）；`test_bdd_8_docs_state_platform_neutral_constraint[p2_card/architect]` | 单测 | 绿 / 红 |
| 9 | `test_bdd_9_output_optional_key_documented[p2_card/architect]`；`agate-frontmatter-check.py` / `check-structure-consistency.py` 空 diff → **P5_kernel_diff**（清单已含二者） | 单测 + P5 key | 红 |
| 10 | `test_bdd_10_p4_card_documents_evidence_landing` | 单测 | 红 |
| 11 | `test_bdd_11_task_files_registers_p4_evidence_and_tests_filter_comment` | 单测 | 红 |
| 12 | `test_bdd_12_no_p4_evidence_in_rules_dispatch_protocol_or_judge`（rules/、dispatch-protocol.md、judge.md 均 0 命中，回归守护）；五个文件 + 两段白/黑名单空 diff → **P5_kernel_diff** | 单测 + P5 key | 绿 |
| 59 | `test_bdd_59_context_five_new_terms_three_columns_with_literals`；`test_bdd_59_new_terms_in_order_and_locations_exist`；`test_bdd_59_baseline_28_term_rows_still_present`（回归守护）；"diff 仅新增、恰 5 行"→ **P6 证据**（`git diff main...HEAD -- agate/CONTEXT.md` 无 `-` 行、`+` 行数 5） | 单测 + P6 证据 | 红 / 红 / 绿 |
| 60 | `test_bdd_60_role_system_review_anchor_section`；`test_bdd_60_new_section_has_no_bare_platform_tokens`（R3/CHECK 14 预防）；其余执行角色文件空 diff → **P5_roles_diff** | 单测 + P5 key | 红 |
| 61 | `test_bdd_61_tracer_bullet_criterion[p2_card/architect]` | 单测 | 红 |
| 62 | `test_bdd_62_walking_skeleton_absorb_reject_record`（含 M2/M5 新小节无"已生效"）；`agate/assets/templates/` 无新增文件 → **P6 证据**（`git diff --name-status main...HEAD -- agate/assets/templates` 无 `A`） | 单测 + P6 证据 | 红 |
| 63 | `test_bdd_63_vertical_slice_criterion[p2_card/architect]` | 单测 | 红 |
| 64 | `test_bdd_64_fitness_functions_criterion[p2_card_gate_commands/architect]`；`test_bdd_64_no_mandatory_arch_tool_requirement_in_protocol_docs`（回归守护） | 单测 | 红 / 绿 |
| 65 | `test_bdd_65_adr_header_recheck_triggers`；`test_bdd_65_adr_header_has_no_bare_platform_tokens`（R3）；`test_bdd_65_existing_adrs_still_present`（回归守护）；既有 ADR 正文零删除行 → **P6 证据**（`git diff main...HEAD -- agate/adr.md` 无 `-` 行） | 单测 + P6 证据 | 红 / 绿 / 绿 |
| 66 | `test_bdd_66_p2_card_decisions_landing_and_reading`；`test_bdd_66_write_timing_stated_in_p2_or_p7_card`；`test_bdd_66_check_gate_does_not_read_decisions_dir`（`check-gate.py` 无 decisions 读取，回归守护） | 单测 | 红 / 红 / 绿 |
| 67 | `test_bdd_67_kernel_files_exist_for_p5_diff_gate`（P2 `P5_kernel_diff` 含 P1 BDD-67 全部 16 条路径且路径均真实存在，防 gate 漏项）；空 diff 本体 → **P5_kernel_diff / P5_kernel_diff_wt** | P5 key（+ 元守护） | 绿 |
| 68 | ① `test_bdd_68_check_mvwu_not_registered_in_gate_hook_ci_surfaces`（P1 原路径清单 0 命中，回归守护）；② 历史任务目录空 diff → **P5_history_untouched**，其命令语义由 B3 守护锁定 | 单测 + P5 key | 绿 |
| 69 | `test_bdd_69_scripts_readme_row_for_check_mvwu`；`test_bdd_69_tests_readme_row_matches_collected_count`（README 行数 = 子进程 `pytest --collect-only` 实数）；`test_bdd_69_changelog_mentions_tag0036`（不断言 `[Unreleased]` 段本身，TAG0025 教训）；count-tests ≥ 1668+N → **P5_count** | 单测 + P5 key | 红 / 红 / 红 |
| 70 | `test_bdd_70_gate_script_exempt_contains_check_mvwu`（M18：`GATE_SCRIPT_EXEMPT` 含 `agate/scripts/check-mvwu.py`，既有两条豁免保留）；全量 pytest / consistency / ruff / 无 `.sh` 改动 → **P5 / P5_consistency / P5_ruff**；**B1 守护** `test_sg_6_check9_anchor_table_covers_all_gate_scripts`（既有用例，"P4 前应已绿"，P5 全量须保持绿） | 单测 + P5 key | 红 |
| 71 | `test_bdd_71_p4_protocol_alignment_review_exists_with_conclusion`（文件存在、frontmatter `agent` ≠ `main`、含"结论"）；P4 提交信息含 `self-gate-review:` → **P6 证据**（`git log --format=%B` 摘录） | 单测 + P6 证据 | 红 |

## 守护类用例（P2 §13）

| 守护 | 用例 | 当前 |
|------|------|------|
| B1（登记，不新增） | `test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts` = "P4 前应已绿"的守护用例；另 `test_guard_b1_sg6_exists_in_alignment_review_tests` 仅防被误删；M18 落地由 `test_bdd_70_gate_script_exempt_contains_check_mvwu` 承担 | 绿（既有）+ 绿 + 红 |
| B2 | `test_guard_b2_p5_commands_shlex_split_and_no_quote_residue`：`agate-read-p5-commands.py`（env `P2_DESIGN`、`sys.executable`、仓库 `agate/scripts/` 版本，只读本任务 P2-design.md）读回 ≥10 条 cmd 均 `shlex.split` 不抛 `ValueError`、末 token 无引号残留 | **回归守护（当前已绿）** |
| B3 | `test_guard_b3_history_untouched_pathspec_is_literal_glob`（pathspec 字面 `agate-workspace/tasks/TAG00[0-2]*` / `TAG003[0-5]*`，revspec `main...HEAD` 在 `--` 前）；`test_guard_b3_history_untouched_command_in_tmp_repo[11 参数]`：读回命令直接在 `tmp_path` 临时 git 仓库（`git init -q` + `git branch -M main` + `feat` 分支提交；含 `TAG0010/0011/0031/0032/0036-x`）执行，删除 / 同删两个 / 修改 / 新增历史目录 rc=1，改 `TAG0036` / 增 `TAG0037` rc=0 | **回归守护（当前已绿）** |
| 同源对拍 | `test_guard_same_source_md_field_get_vs_split_frontmatter`：同一 P2 样例（含转义引号 tests_filter + `output` 列表）与本任务 P2-design.md，经 `agate-md-field-get.py dispatch_plan` 与 `agate_common.split_frontmatter`（`sys.path` 临时插入仓库脚本目录）得同一 JSON | **回归守护（当前已绿）** |

## 隔离与平台无关

- 只读运行仓库脚本（`agate-md-field-get.py` / `check-gate.py` / `agate-read-p5-commands.py` / `check-debt.py`），任务目录一律 `tmp_path`（`task_dir` fixture / 手建），不写仓库内 `agate-workspace/`；用例前后 `git status` 不变。
- 临时 git 仓库：`git init -q`、显式 `user.name/email`、`commit.gpgsign=false`、`core.hooksPath` 指向空目录、剔除 `GIT_*` 环境变量；`subprocess.run(..., check=True, timeout=60)`。
- 解释器一律 `sys.executable`；无 `/tmp` 字面量；全部读写显式 `utf-8`；文件内首个用例带 `@pytest.mark.windows_smoke`；未使用符号链接。

## 歧义 / 需主 Agent 知晓

- 无 P1/P2 歧义阻塞。上述"设计取舍"第 1、3 条为 P3 选定，若主 Agent 坚持 dispatch 第 9 条的 `git show <基线>` 形式，可在 P5/P6 用一次性命令补，不建议进永久测试。
- `test_bdd_69_tests_readme_row_matches_collected_count` 依赖 script 半边 `test_check_mvwu.py` 的最终用例数（README 行数须与实数一致）；`test_bdd_71_*` 依赖 P4 收口产物，均为设计如此的 P4 后转绿点。
