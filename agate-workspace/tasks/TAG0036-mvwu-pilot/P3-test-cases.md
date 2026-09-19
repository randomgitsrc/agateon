---
phase: P3
task_id: TAG0036
parent: P2-design.md
trace_id: TAG0036-P3-20260919
type: test-design
created: '2026-09-19'
status: draft
agent: test-designer
test_code_dir: agate/tests/unit/test_check_mvwu.py,agate/tests/unit/test_mvwu_protocol_docs.py
---
# P3 测试用例清单（主映射）— TAG0036 MVWU 阶段 1 试点

> 本文件为 P3 主映射：全部 71 条 BDD 的 1:1 映射总表。script 半边（`agate/tests/unit/test_check_mvwu.py`）由 test-designer-script 登记具体用例名；docs 半边（`agate/tests/unit/test_mvwu_protocol_docs.py`）的 BDD 条目写「见 P3-test-cases-docs.md」，由 docs 半边负责登记。
> 归属：docs 半边 = BDD-1、2、3、5、6、7、8、9、10、11、12、59 至 BDD-71；script 半边 = BDD-4（check-mvwu 侧）、13 至 55、57、58；BDD-56 为 P6 真实证据（不写单测）。

## 1. 测试代码

（`test_code_dir` 已写入本文件 frontmatter：`test_check_mvwu.py` 与 `test_mvwu_protocol_docs.py` 两个测试文件。）

## 2. TDD 红灯说明（script 半边）

- 被测脚本 `agate/scripts/check-mvwu.py` 尚未存在；所有用例统一经 `MvwuRepo.run()`（或 BDD-57/58 用例的前置断言）先断言脚本存在，缺失即断言失败（项目内缺失，B 类真红灯），无 SyntaxError / 第三方 import 失败。
- 用例均在 pytest `tmp_path` 内建临时 git 仓库与任务目录（`git init -q`，显式 `symbolic-ref` 到 main/trunk），不写仓库内 `agate-workspace/`；子进程解释器一律 `sys.executable`，git 命令 `check=True` + 超时；首个用例（BDD-13）带 `@pytest.mark.windows_smoke`。
- 断言值逐字取自 P1「口径 A-H」与 P2 §13 提示（字面锚点 `仅检查首词` / `不比对 command 与 tests_filter` / `UNKNOWN 不等价于 PASS，不得作为放行依据`；耗时非整数 `8.5s`；id 等价类 `5`/`null` 打印 `batch=?`）。
- 「可解析解释器」实现口径：证据 `command` 默认用 `git status --short`（首词 `git` 在 PATH 上可解析，测试本身依赖 git；避免 `sys.executable` 路径含空格/引号导致的平台差异）；不可解析用 `no-such-runner-xyz tests/`。BDD-19 哨兵法：`command` 与 `tests_filter` 均为 `git init "<tmp_path 内哨兵目录>"`，若被执行则哨兵目录出现。

## 3. BDD → 测试映射（71 条全表）

| BDD | 测试文件::用例名 / 落点 | 负责半边 |
|-----|------------------------|----------|
| BDD-1 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-2 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-3 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-4 | `test_check_mvwu.py::test_bdd_4_mixed_tests_filter_batches_are_independent` | script 半边 |
| BDD-5 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-6 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-7 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-8 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-9 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-10 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-11 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-12 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-13 | `test_check_mvwu.py::test_bdd_13_basic_contract_two_batches_in_declared_order` | script 半边 |
| BDD-14 | `test_check_mvwu.py::test_bdd_14_check1_tests_filter_missing_or_invalid_is_unknown` | script 半边 |
| BDD-15 | `test_check_mvwu.py::test_bdd_15_check2_command_first_word_unresolvable_or_missing_is_unknown` | script 半边 |
| BDD-16 | `test_check_mvwu.py::test_bdd_16_check2_leading_env_assignment_is_skipped` | script 半边 |
| BDD-17 | `test_check_mvwu.py::test_bdd_17_check2_compound_command_only_first_word_is_checked` | script 半边 |
| BDD-18 | `test_check_mvwu.py::test_bdd_18_command_is_not_compared_with_tests_filter` | script 半边 |
| BDD-19 | `test_check_mvwu.py::test_bdd_19_never_executes_command_or_tests_filter` | script 半边 |
| BDD-20 | `test_check_mvwu.py::test_bdd_20_check3_evidence_missing_is_unknown` | script 半边 |
| BDD-21 | `test_check_mvwu.py::test_bdd_21_unsafe_batch_id_is_unknown_and_external_file_not_read` | script 半边 |
| BDD-22 | `test_check_mvwu.py::test_bdd_22_unsafe_batch_id_print_form_is_machine_readable`, `test_check_mvwu.py::test_bdd_22_unsafe_id_encoding_equivalence_classes` | script 半边 |
| BDD-23 | `test_check_mvwu.py::test_bdd_23_check4_exit_code_missing_or_non_integer_is_unknown` | script 半边 |
| BDD-24 | `test_check_mvwu.py::test_bdd_24_check5_git_head_invalid_is_unknown_even_when_green`, `test_check_mvwu.py::test_bdd_24_check5_task_dir_outside_git_repo_is_unknown`, `test_check_mvwu.py::test_bdd_24_check5_uppercase_full_sha_is_valid` | script 半边 |
| BDD-25 | `test_check_mvwu.py::test_bdd_25_verdict_pass` | script 半边 |
| BDD-26 | `test_check_mvwu.py::test_bdd_26_verdict_fail_nonzero_exit_without_expected_red` | script 半边 |
| BDD-27 | `test_check_mvwu.py::test_bdd_27_verdict_fail_unexpected_red` | script 半边 |
| BDD-28 | `test_check_mvwu.py::test_bdd_28_verdict_expected_red` | script 半边 |
| BDD-29 | `test_check_mvwu.py::test_bdd_29_expected_red_not_verifiable_is_unknown_not_guessed` | script 半边 |
| BDD-30 | `test_check_mvwu.py::test_bdd_30_quoted_node_ids_with_commas_brackets_parse_correctly` | script 半边 |
| BDD-31 | `test_check_mvwu.py::test_bdd_31_element_equality_is_exact_node_id` | script 半边 |
| BDD-32 | `test_check_mvwu.py::test_bdd_32_unparseable_expected_red_or_failed_tests_is_unknown` | script 半边 |
| BDD-33 | `test_check_mvwu.py::test_bdd_33_exit_zero_with_nonempty_failed_tests_is_unknown_exit_code` | script 半边 |
| BDD-34 | `test_check_mvwu.py::test_bdd_34_multi_fault_reason_uses_fixed_order` | script 半边 |
| BDD-35 | `test_check_mvwu.py::test_bdd_35_unknown_is_never_pass_and_documents_it` | script 半边 |
| BDD-36 | `test_check_mvwu.py::test_bdd_36_every_verdict_exits_zero_without_traceback` | script 半边 |
| BDD-37 | `test_check_mvwu.py::test_bdd_37_usage_or_target_error_exits_2` | script 半边 |
| BDD-38 | `test_check_mvwu.py::test_bdd_38_read_only_no_state_written` | script 半边 |
| BDD-39 | `test_check_mvwu.py::test_bdd_39_no_judgeable_batch_gives_honest_unknown_line`, `test_check_mvwu.py::test_bdd_39_observe_no_judgeable_batch_gives_single_row_with_dash_first_column` | script 半边 |
| BDD-40 | `test_check_mvwu.py::test_bdd_40_corrupt_evidence_is_unknown_and_does_not_crash` | script 半边 |
| BDD-41 | `test_check_mvwu.py::test_bdd_41_batches_are_judged_independently` | script 半边 |
| BDD-42 | `test_check_mvwu.py::test_bdd_42_boundary_and_commit_form_do_not_affect_verdict` | script 半边 |
| BDD-43 | `test_check_mvwu.py::test_bdd_43_observe_seven_column_rows_one_per_batch` | script 半边 |
| BDD-44 | `test_check_mvwu.py::test_bdd_44_observe_escapes_pipe_backtick_backslash_newline` | script 半边 |
| BDD-45 | `test_check_mvwu.py::test_bdd_45_duration_column_from_duration_seconds` | script 半边 |
| BDD-46 | `test_check_mvwu.py::test_bdd_46_evidence_column_reflects_log_file_existence` | script 半边 |
| BDD-47 | `test_check_mvwu.py::test_bdd_47_commit_form_per_batch` | script 半边 |
| BDD-48 | `test_check_mvwu.py::test_bdd_48_commit_form_merged` | script 半边 |
| BDD-49 | `test_check_mvwu.py::test_bdd_49_commit_form_unattributable_is_unknown` | script 半边 |
| BDD-50 | `test_check_mvwu.py::test_bdd_50_undeterminable_baseline_gives_unknown_and_diagnostic` | script 半边 |
| BDD-51 | `test_check_mvwu.py::test_bdd_51_boundary_exact_excludes_default_workspace_tasks_prefix` | script 半边 |
| BDD-52 | `test_check_mvwu.py::test_bdd_52_boundary_exclusion_prefix_follows_workspace_config` | script 半边 |
| BDD-53 | `test_check_mvwu.py::test_bdd_53_boundary_mismatch` | script 半边 |
| BDD-54 | `test_check_mvwu.py::test_bdd_54_boundary_unknown_for_merged_or_no_output` | script 半边 |
| BDD-55 | `test_check_mvwu.py::test_bdd_55_observe_verdicts_match_default_and_stay_read_only` | script 半边 |
| BDD-56 | P6 真实证据（`python3 agate/scripts/check-mvwu.py --observe agate-workspace/tasks/<任务>` 在真实任务目录跑通，摘录进 `P6-evidence/`；不写单测） | script 半边（P6 证据） |
| BDD-57 | `test_check_mvwu.py::test_bdd_57_test_file_covers_required_bdds_and_windows_smoke_first` | script 半边 |
| BDD-58 | `test_check_mvwu.py::test_bdd_58_windows_smoke_selects_and_passes` | script 半边 |
| BDD-59 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-60 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-61 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-62 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-63 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-64 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-65 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-66 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-67 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-68 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-69 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-70 | 见 P3-test-cases-docs.md | docs 半边 |
| BDD-71 | 见 P3-test-cases-docs.md | docs 半边 |

## 4. 补充守护用例（P2 §13 提示，非 BDD 编号；script 半边）

- `test_check_mvwu.py::test_supplement_symlink_escape_evidence_is_not_read`
- `test_check_mvwu.py::test_supplement_unreadable_evidence_falls_back_without_traceback`
- `test_check_mvwu.py::test_supplement_duplicate_evidence_key_last_one_wins`
- `test_check_mvwu.py::test_supplement_crlf_evidence_file_is_parsed`
- `test_check_mvwu.py::test_supplement_batches_match_agate_md_field_get_source`

- 覆盖点：符号链接逃逸（R9，不支持符号链接的平台 skip）、逐批异常兜底不出 traceback（R10，非 root POSIX）、重复证据键后者覆盖、CRLF 证据文件、与 `agate-md-field-get.py dispatch_plan` 的批集合同源对拍。
- P2 §13 的 B1/B2/B3 守护（`test_sg_6` 列为「P4 前应已绿」、`agate-read-p5-commands.py` 读回不抛 ValueError、`P5_history_untouched` 删除历史目录 rc=1）属文档/gate_commands 面，不在 script 半边范围（由 docs 半边或主 Agent 决定是否登记）。

## 5. 规模

- script 半边：55 个用例函数，展开参数化后 109 个 pytest 用例（`pytest --collect-only`）。
