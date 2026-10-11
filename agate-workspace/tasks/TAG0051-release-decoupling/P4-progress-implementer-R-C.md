
## R-C（retry 1）：测试/夹具闭合（只改 agate/tests/**）

### ① 契约等级抬升（夹具 contract_level 1→2）
根因：`level-2.yaml` 登记 ⇒ `current_level()=2` ⇒ `pre-commit-gate.py`（设计 §2.3 规则 2）
拒一切「新建**等级 1** 任务 + commit」。修法 = 把**夹具造出的任务等级**改成当前等级 2
（不动任何断言语义）。逐处：
- `agate/tests/integration/test_pre_commit_hook.py::_seed_task_created`（默认 `contract_level=1`→`2`；
  仅 `_write_state_yaml` 非 legacy 分支调用）→ **覆盖 29 条** pre_commit 用例（整文件 69 passed）。
- `agate/tests/integration/test_tag0050_prod_touched.py::_seed_nonlegacy_task`（1→2）→ 覆盖 bdd_49/52/53。
- `agate/tests/integration/test_tag0050_ci_replay.py::_task_commit_repo`（1→2）→ 覆盖 bdd_23/24。
- `agate/tests/integration/test_tag0050_state_set.py::_seed_created_task`（1→2）→ 覆盖 test_gate_run_*。
- 保留负例：`test_tag0050_a0_a1_ledger.py` 中 contract_level=0/42 的 BDD-06/07 等**未动**（它们
  测的就是「低于当前等级 → ERROR」，是设计面，不是夹具）。

### ⑤ 需单独判断的一条（`test_tag0050_write_tools.py::test_f2_*`）
诊断结论：**与等级抬升相关**（=同一根因的另一面）。`agate-md-field-set.py::_contract_fields` 里
`level = task_level(...) or current_level(...)`，等级抬升后该值由 1 变 2 ⇒ `load_contract(2)` 沿
`extends: 1` 链**先读 `level-2.yaml`**；而用例夹具此前只复制了 `LEVELS.yaml` + `level-1.yaml`，
**缺 level-2.yaml** ⇒ extends 链首步即断（chain 空）⇒ 快照整体 `{}` ⇒ 注入的 `results_total`
读不到 ⇒ 拒写原因从契约的 `writer: system` 退化为「非法 key」。
修法（**测试侧**）：夹具改为 `shutil.copytree(agate_root/"rules"/"task-data", td)` 整目录复制
（含 level-2.yaml，未来新增等级亦自动覆盖），再就地改写 level-1.yaml。⇒ 现 1 passed。

### ③ 断言「已删 WARNING」（BDD-2/3 正向口径，保留「P8 通过」核心断言）
- `test_check_gate.py::test_g8_2_no_version_change_warning_exit_2`：改为 rc=2 且 **无** WARNING / version。
- `test_check_gate.py::test_g8_7_tag_missing_warning_exit_2`：改为 rc=2 且 **无** tag 缺失告警 / WARNING。
- `test_check_gate.py::test_g8_3_version_changed_no_changelog_exit_2`（**失真项修正**）：旧断言
  `"CHANGELOG" in output` 现仅命中 gate_p8 收尾文案；改为 rc=2 且无 WARNING + 新载体
  `check-changelog.py T001` 对未记录 task 判 FAIL（exit 1）。
- `test_v060_p8_cached.py::test_r5_2_*` / `test_r5_3_*`：与 g8_2/g8_3 同源同型修正（r5_3 同为失真项，
  一并修，见返回摘要）。
- `test_gate_layer.py::test_bdd_21_missing_declaration_with_release_traces_warns`：改为 rc=2 +
  「脚本化检查通过」+ 反向断言（`semver-changelog-tag|release.preset|agate.config.yaml` **不出现**）。

### ④ release.yml 静态契约（BDD-8 / SEC-05）
- `test_release_workflow.py::test_bdd_13_1_*`：触发面 = `push.tags['v*']` **且** `workflow_dispatch`
  （含 tag 输入）；仍禁 branches/PR/workflow_run/schedule。
- `test_bdd_13_2_*`：`permissions == {contents: write, checks: read}`（Release gate 读 CI 结论）。
- `test_t8_gh_token_only_in_publish_step_env`：令牌持有面 = **{Release gate, Publish}**（SEC-05 有意）；
  其它步骤 / job 级 / 顶层仍不持有。

### ②（S-3b）与 ⑥（不动）
- ② S-3b：**R-B 已落盘**（实测 `check-structure-consistency.py` S3-cards: OK）⇒ 相关 7 条已转绿，
  测试侧无需改动。
- ⑥ `test_bdd_43`（环境漂移）/ `test_bdd_22`（设计性必红）**未动**。
- `[PROD_NOT_TOUCHED]`

### 自检实测（R-C 完成时）
- `python3 -m pytest agate/tests/ -q -n auto` → **2 failed, 2957 passed, 2 skipped**（208.01s）。
  剩余红**仅**：
  1. `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` —— **环境漂移**
     （本机 `opencode debug` 无 `agent` 子命令，只有 `agents`），与本任务无关，未动。
  2. `test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review`
     —— **设计性必红**（本分支尚无协议提交；P4 commit 带 `self-gate-review:` 后转绿），未动。
- `bash agate/tests/scripts/count-tests.sh` → **2961**（未漂移）。
- 本 R-C 改动文件（仅 `agate/tests/**`）：见 files_modified。
- ② S-3b（`test_check_structure_consistency.py::test_bdd_26*` + `test_dispatch_context_card.py`×6
  + `test_tag0050_a0_a1_ledger.py::bdd_12/25`）：**R-B 已落盘**（实测 S3-cards: OK）⇒ 已转绿，
  测试侧未动。
