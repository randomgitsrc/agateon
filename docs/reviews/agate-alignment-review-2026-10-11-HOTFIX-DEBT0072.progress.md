# 留痕（原始痕迹）：HOTFIX-DEBT0072 协议-脚本对齐审查

- reset 空文件，开始。
- 读 role: ~/.agate/v0.81.0/agate/assets/review-roles/protocol-alignment-review.md（A1–A8 + A4b + 只读纪律 RM-AG0081）。
- 读 dispatch: /tmp/opencode/hotfix-0072-review-context.md（重点核三处 + 复述陷阱）。
- git status --porcelain → M CHANGELOG.md / M agate-workspace/debt/tech-debt.md / M agate/scripts/agate-md-field-set.py / ?? agate/tests/unit/test_debt0072_append_guard.py。分支 hotfix/debt0072-append-guard。
- 读 git diff：脚本只新增 docstring 段（17–20）+ 新函数 `_script_field_error`（747–762）+ `_require_list_field` 内调用（776–782）。`_cmd_set` 未出现在 diff。
- 读 test_debt0072_append_guard.py（195 行，4 个 test 函数 / 10 用例参数化）。
- 实证（/tmp/opencode 一次性副本，同调用内建→操作→清理；未写真实仓库；git status 前后干净）：
  - AFTER: append pass/fail/blocker_count/deviation_critical_count rc=1（新守卫）；append regression_pass/deviation_count/design_gap_count/design_gap_reviewed_count/code_map_new_files_count/code_map_reviewed_count rc=1（**契约外**分支，改前也 rc=1）；append results/scope_resolved/need_confirm rc=0；upsert pass rc=1；remove pass rc=1；set pass rc=1（文案不变）。
  - BEFORE(HEAD 版脚本): append pass/fail rc=0（OK）；append blocker_count/deviation_critical_count rc=0；upsert pass rc=0；append regression_pass/deviation_count rc=1（契约外）。
  - ⇒ **唯一被新守卫新覆盖 = 契约 writer:system 列表字段 {pass, fail, blocker_count, deviation_critical_count}**；其余「证据字段」改前即被契约分支拒。
  - P6.5: append/upsert/remove criteria_passed/criteria_total/verdict_evidence 改前后均 rc=1（契约外）；**set criteria_passed 9 rc=0**（越 scope，pre-existing）。
- 扫「由脚本/角色产出」字段全部来源：SCHEMAS 4 basename（frontmatter-check.py 39–124）；契约 files 节（level-1.yaml 75–106；level-2 只改 delivery）；md-field-get NO_FALLBACK_INT_FIELDS(148–153)/NO_FALLBACK_BOOL_FIELDS(107)/JSON_FIELDS(178)；check-gate P6/P7 现算（1470/1885）；phase task_fields。
- 跑测得：新用例 `pytest agate/tests/unit/test_debt0072_append_guard.py -q` → **10 passed**。
- 跑既有相关面：md_field_set/debt0067_0068/write_tools/declarations/prod_touched/evidence → **100 passed**；capability/gate/p6_evidence/p6_provenance/mechanism_anchors → **384 passed**。无既有用例转红。
- check-protocol-consistency.py → **0 ERROR**（433 冻结 WARNING），CHECK 9 PASS、CHECK 16 PASS。ruff 两文件 All checks passed。
- check-debt.py tech-debt.md → rc=0；`^status: open` = 2（DEBT0015/DEBT0067）。
- CHANGELOG 条目在 [Unreleased]→修复（70 行起）；closure_note 3132–3137；status closed 3084。
- 结论：0 MISALIGNED；范围未写窄（CHANGELOG/closure_note 均显式写 append/upsert/remove）。
