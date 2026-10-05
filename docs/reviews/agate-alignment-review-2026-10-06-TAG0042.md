---
review_date: 2026-10-06
reviewer: protocol-alignment-review
change_summary: >-
  TAG0042 批 1（batch1-phase-semantics）——统一 phase 语义：agate-next 推进时不再预写下一阶段
  （去掉 _advance 的 state["phase"]=target 预写 + _write_state 落盘 + git add，删除孤儿 _write_state/_git，
  保留 state_transition 事件，改输出「下一阶段建议」）；同步 P2/P8 卡片表述与 UPGRADING v0.79.0 节；
  同步既有 test_tag0027_b1_agate_next_cli.py 的 3 处「推进后 phase」断言。
  【round 3 / 批 2（batch2-agate-config）】引入项目声明层：新增 agate/scripts/agate-config.py
  （init/validate/get/list/show）+ agate/rules/schema/project-config.schema.json；agate_common 新增
  唯一读取函数 read_project_config()；check-gate.py::gate_p0 接入 validate 但迁移期恒 return 2 + WARNING；
  install-hook.py/agate-setup.py 接入时自动 init 声明（幂等）；UPGRADING 批 2 小节（截止 v0.80.0）+ 
  scripts/README + CODE-MAP + 两测试文件缺陷修正。
  【round 4 / 批 3（batch3-agate-run）】引入执行层：新增 agate/scripts/agate-run.py（在不可绕开路径
  执行声明 verify.commands——bash+pipefail 如实传播退出码、--baseline .out 证据逐字节比对、
  git check-ignore 覆盖检查、非 POSIX 退化 + WARNING、cmd_run 事件经 append_event、AGATE_TASK_DIR
  定位账本）；pre-commit-gate.py 一并 git add 账本（不直接写，防破链）；scripts/README + CODE-MAP。
  【round 6 / 批 4（batch4-gate-layer）】关卡层分级 + P8 交付收尾：phases.yaml P8 name
  发布准备→交付收尾 + 新增 gate_layer（commit_types + transitions 含 paused_from）；
  phases.schema.json 扩展；check-gate.py::gate_p8 新增 delivery 校验 + 发版痕迹迁移 WARNING；
  P8-release.md 标题/产出规格；WORKFLOW.md P8 行名；UPGRADING 批 4 小节；测试夹具同步。
  【round 8 / 批 5（batch5-ci-doctor）】CI 与诊断：新增 agate/scripts/agate-ci-verify.py
  （实际重跑 gate 判定，无假绿；跳过面显式 SKIP: + 原因）+ agate-doctor.py（声明/hook/版本解析/
  账本四维诊断 + 修复指引，rc 恒 0）；删除 ci-gate-backstop.py 及其测试；workflow gate-backstop job
  改调新脚本；check-protocol-consistency 移除退役锚点/extras/callers 并保留退役名拦截；agate-summary/
  scripts/README/check-gate 注释/6 协议文档/formatters-README/tests-README 同步。
files_changed:
  - agate/scripts/agate-next.py
  - agate/phase-cards/P2-design.md
  - agate/phase-cards/P8-release.md
  - agate/UPGRADING.md
  - agate/tests/unit/test_tag0027_b1_agate_next_cli.py
  # round 2 修复轮新增（反向传播闭合；纯文本改述）
  - agate/state-machine.md
  - agate/dispatch-protocol.md
  - agate/CONTEXT.md
  - agate/loop-orchestration.md
  - agate/orchestrator-template.md
  # round 3 / 批 2（batch2-agate-config）
  - agate/scripts/agate-config.py
  - agate/rules/schema/project-config.schema.json
  - agate/scripts/agate_common.py
  - agate/scripts/check-gate.py
  - agate/scripts/install-hook.py
  - agate/scripts/agate-setup.py
  - agate/scripts/README.md
  - agate-workspace/agents/CODE-MAP.md
  - agate/tests/unit/test_agate_config.py
  - agate/tests/unit/test_config_schema.py
  # round 4 / 批 3（batch3-agate-run）
  - agate/scripts/agate-run.py
  - agate/scripts/pre-commit-gate.py
  # round 5 / 批 3 修复轮（cmd_run 反向传播闭合）
  - agate/git-integration.md
  - agate/scripts/check-events.py
  # round 6 / 批 4（batch4-gate-layer）
  - agate/rules/phases.yaml
  - agate/rules/schema/phases.schema.json
  - agate/WORKFLOW.md
  - agate/tests/unit/test_gate_layer.py
  - agate/tests/unit/test_check_p8_delivery.py
  - agate/tests/unit/test_check_gate.py
  - agate/tests/unit/test_t41_platform_hygiene.py
  - agate/tests/regression/test_v060_p8_cached.py
  # round 7 / 批 4 修复轮（P8 名称/语义叙事闭合）
  - agate/role-system.md
  - agate/assets/execution-roles/implementer.md
  - agate/LIMITATIONS.md
  - agate/tests/unit/test_agate_run.py
  # round 8 / 批 5（batch5-ci-doctor）
  - agate/scripts/agate-ci-verify.py
  - agate/scripts/agate-doctor.py
  - agate/scripts/ci-gate-backstop.py  # 删除（退役）
  - .github/workflows/protocol-tests.yml
  - agate/scripts/check-protocol-consistency.py
  - agate/scripts/agate-summary.py
  - agate/platform-notes.md
  - agate/phase-cards/P3-tdd.md
  - agate/assets/templates/retrospective-template.md
  - agate/assets/formatters/README.md
  - agate/tests/README.md
  - agate/tests/unit/test_ci_gate_backstop.py  # 删除（测退役对象）
  - agate/tests/unit/test_check_protocol_consistency.py
  - agate/tests/unit/test_mvwu_protocol_docs.py
review_scope: >-
  TAG0042 批 1 的 agate/** 未 commit 改动（SELF-GATE 语义 gate，agent≠main）。
  变更触发模式：意图分析 → 反向传播 → 变更文件全文 + 反向传播文件 + 权威规则源（state-machine.md /
  dispatch-protocol.md / WORKFLOW.md）→ A1-A8。单轮审查。
prod_isolation: "[PROD_NOT_TOUCHED] —— 仅读取仓库 + 写 /tmp 留痕/日志 + 本报告；未触碰被评审改动集、主 checkout 与 ~/.agate。"
conclusion: aligned
review_rounds: 8
round1_conclusion: >-
  批 1 首审：misaligned。A1/A2/A3b/A5.3 同一根因 = 反向传播漏改 5 处权威文档——它们仍描述旧行为
  「agate-next 更新 .state.yaml phase + git add」（state-machine.md:326-331 / dispatch-protocol.md:291-292 /
  CONTEXT.md:33 / loop-orchestration.md:242-247 / orchestrator-template.md:56）。脚本、卡片、UPGRADING、
  测试 5 个改动面本身语义自洽；A3a/A4/A6/A7 ALIGNED；A5.1/A5.2 ALIGNED（CHANGELOG 属 P8 触发，非本批）。
pytest_full_run: >-
  2026-10-06，worktree /home/kity/oclab/agateon：`python3 -m pytest agate/tests/ -q --tb=short`
  → 61 failed / 2624 passed / 2 skipped（222.98s，exit 1）。61 failed 全部落在 batch2-6 的 P3 红灯测试文件
  （test_agate_config 12 / test_config_schema 10 / test_agate_run 9 / test_agate_doctor 8 / test_events_ledger 6 /
  test_agate_ci_verify 6 / test_gate_layer 5 / test_check_p8_delivery 3 / test_setup_agate_dir 1 /
  test_agate_scripts_encoding 1），均为「batch2-6 尚未实现」的 by-design 红灯；
  batch1 相关 4 文件（test_tag0042_batch1_phase_semantics / test_tag0027_b1_agate_next_cli /
  test_check_state_transition / test_agate_next_card）**零失败**。批 1 无回归。
round2_conclusion: >-
  TAG0042 批 1 复审（round 2）：aligned。首轮 4 项 MISALIGNED（A1/A2/A3b/A5.3，同一根因）全部闭合——
  5 处权威文档（state-machine.md 机械化段 :326-335 + 手工规格 step 7 :401-403、dispatch-protocol.md:291-295、
  CONTEXT.md:33、loop-orchestration.md:244-246、orchestrator-template.md:57-59）已改述为与
  agate-next.py:166-178 / P2-design.md:14-17 / P8-release.md:21 / UPGRADING.md:288-296 / git-integration.md:31,33
  同口径：自动化 `agate next` 只输出「下一阶段建议」+ `state_transition` 事件，**不预写** `.state.yaml` 的 `phase`、
  不 `git add`，`phase` 由下一阶段产出 commit 写入；state-machine/dispatch-protocol/CONTEXT/orchestrator-template
  四处显式标注「手工 fallback 仍写 `phase`」，自动化路径与手工路径区分明确。
  残留旧行为 grep（`写回 .state.yaml + git add` / `更新 .state.yaml phase + git add`）→ 0 命中；
  首轮 ALIGNED 项无回退：CHECK9 PASS / CHECK10 WARN 1（pre-existing CHANGELOG `check-windows-smoke.sh`，与本次无关）/
  CHECK2-refs 无来自 5 文档的新命中 / CHECK14-15 PASS；consistency 0 ERROR；count-tests 2687 未漂移；
  batch1 相关 4 测试文件 99 passed、doc 关联 7 文件 142 passed。
  首轮附注（UPGRADING T085 归因措辞侧重）仍为非阻塞观察项，留 P7/P8 留意，不阻塞 commit。
round3_conclusion: >-
  TAG0042 批 2（batch2-agate-config）增量复审（round 3）：aligned。变更面为声明层——新增
  agate-config.py + project-config.schema.json；agate_common 唯一读取函数 read_project_config()；
  check-gate.py::gate_p0 接 validate 但迁移期恒 return 2 + WARNING；install-hook/agate-setup 自动 init
  （幂等）。A1/A2 ALIGNED：gate_p0 恒 return 2 与 UPGRADING「迁移期行为与引入前一致 + WARNING」同口径；
  唯一读取函数有 docstring/README 声明，无第二处声明解析。A3b/A5 ALIGNED：新「声明文件」概念无需传播到
  state-machine/dispatch-protocol/WORKFLOW/phase-cards/角色文件（grep 0 命中）；UPGRADING v0.79.0 节
  自洽（批1+batch2 同节 + 截止 v0.80.0）。A6 ALIGNED：agate-config.py（agate-*.py）不在 CHECK9-coverage/
  SG.6 门禁 glob（实测 SG.6 1 passed，uncovered 为空）；新 schema 被 CHECK15 数据面扫描 + test_config_schema
  同构测试覆盖。A4 ALIGNED：batch2 三文件 24 passed、+3 回归文件 279 passed、count-tests 2687 未漂移。
  A7 ALIGNED（落地 ADR-003 不绑定技术栈 + ADR-014 判据单源）。A8 声称均可复核。consistency 0 ERROR /
  401 WARNING（CHECK9 PASS，CHECK10 WARN1 为 pre-existing，CHECK14/15 PASS）。
  4 条 [DESIGN_GAP] 判定：全部归 DESIGN_GAP（交 P7），0 条 MISALIGNED——#1（P2 §4.1 正文 vs N2/P3 矛盾）
  P2 自相矛盾且实现随 N2+P3+UPGRADING（非 agate/ 协议文档矛盾）；#2/#3 为 P2 未指定的设计选择；
  #4（默认注入使 schema required 不触发，实测仅 schema_version/{} → validate rc0）在 effective-config
  模型下自洽（required 被默认满足、非违反），但有语义影响，建议 P7 裁决 required 去留。
  非阻塞观察：SETUP.md/scripts-README(install-hook 行)/CONTEXT 未提及自动 init 声明（完备性缺口，非矛盾）。
  NEEDS_HUMAN_REVIEW 0 条。
round4_conclusion: >-
  TAG0042 批 3（batch3-agate-run）增量复审（round 4）：misaligned（1 根因）。变更面为执行层——新增
  agate-run.py（bash+pipefail 如实传播退出码、--baseline .out 逐字节比对、git check-ignore、
  非 POSIX 退化 + WARNING、cmd_run 经 append_event、AGATE_TASK_DIR 定位账本）；pre-commit-gate.py
  一并 git add 账本（不直接写，防破链）。A1 ALIGNED（脚本行为与 P2 §4.2 / P3 契约逐条一致，pipefail
  写法与 agate_common:747-756 同口径）；A4 ALIGNED（batch3 两文件 15 passed、hook 集成 61 passed、
  count-tests 2688）；A6 ALIGNED（agate-run.py 不在 CHECK9-coverage/SG.6 glob，实测 SG.6 1 passed）；
  A7 ALIGNED（落地 ADR-015 让错误可见 / ADR-002 可判定 / ADR-004 安全网）；A8 声称均可复核；
  consistency 0 ERROR / 402 WARNING（CHECK9 PASS、CHECK10 WARN1 pre-existing、CHECK14/15 PASS）。
  **MISALIGNED（A2 / A3b / A5.3，同一根因）**：新增账本事件类型 `cmd_run` 未反向传播到两处协议文档的
  「事件类型枚举」——`agate/CONTEXT.md:31`（gate_run / judge_verdict / state_transition / dispatch_route）
  与 `agate/git-integration.md:176-177`（同枚举）。先例：`dispatch_route`（TAG0034）由专门提交
  b68af6b 加入上述两处，故新事件类型须同步。修复方向：两处枚举补 `cmd_run`（纯文本）。state-machine/
  dispatch-protocol/WORKFLOW/卡片/角色无事件类型枚举，无需改。2 条 [DESIGN_GAP] 均归 DESIGN_GAP（交 P7）：
  ① P2 M10「修正 formatter 计数」无缺陷/落点/判据且 P3 无覆盖（改动将违反 N3）——建议 P2 删/细化；
  ② P2 §4.2 `<cmd-key|命令>` 但 schema 无命名 key（实现按命令文本匹配 + 下标槽位）。
  NEEDS_HUMAN_REVIEW 0 条。观察：BDD-9「经 agate-run 执行」尚未传播到 verifier/P5 卡（batch3 §6.1b/
  §12 声明 output 仅脚本，属后续接线）。
round5_conclusion: >-
  TAG0042 批 3 修复复审（round 5）：aligned。round4 的 3 项 MISALIGNED（A2/A3b/A5.3，同一根因 =
  新增账本事件类型 `cmd_run` 未传播到事件类型枚举）已全部闭合：`agate/CONTEXT.md:31`、
  `agate/git-integration.md:177` 两处枚举各补 `cmd_run`；`agate/scripts/check-events.py:14`
  docstring 已知类型注释亦补 `cmd_run`（纯注释，审计逻辑零改动，1 行 diff）。`grep` 残留旧枚举
  （gate_run…dispatch_route 无 cmd_run）→ 0 命中。回归面：consistency 0 ERROR / 402 WARNING（无新增）；
  batch3 回归 test_agate_run + test_events_ledger + test_check_events → 29 passed；SG.6 → 1 passed；
  修复仅动文档/注释、未改脚本逻辑 → A1/A3a/A4/A6/A7/A8 无回退。2 条 [DESIGN_GAP]（formatter 计数 /
  cmd-key）未受本轮修复影响，仍判 DESIGN_GAP（交 P7）。NEEDS_HUMAN_REVIEW 0 条。
round6_conclusion: >-
  TAG0042 批 4（batch4-gate-layer）增量复审（round 6）：misaligned（1 根因）。变更面为关卡层分级 +
  P8 交付收尾：phases.yaml P8 name 发布准备→交付收尾 + 新增 gate_layer（commit_types + transitions
  含 paused_from）；phases.schema.json 扩展；check-gate.py::gate_p8 新增 delivery 校验 + 发版痕迹迁移
  WARNING；P8-release.md 标题/产出规格；WORKFLOW.md P8 行名；UPGRADING 批 4 小节；测试夹具同步。
  A1 ALIGNED（gate_p8 delivery 校验 vs BDD-15/P2 §4.3、gate_layer vs BDD-14 逐条一致；
  gate_pass_exit/next/retreat 未变）；A4 ALIGNED（test_gate_layer+test_check_p8_delivery+test_check_gate
  → 227 passed）；A6 ALIGNED（gate_layer 被 check-yaml-schema S-5 覆盖，SCHEMA-phases OK）；
  A7 ALIGNED；A8 声称均可复核；consistency 0 ERROR / 404 WARNING（CHECK9 PASS、CHECK14/15 PASS）；
  count-tests 2689；ruff 绿；structure S1-S6/S0 全 OK。
  **MISALIGNED（A2 / A3b / A5.3，同一根因）**：P8 名称/语义由「发布准备」改「交付收尾」（BDD-15），
  但名称/身份级叙事未反向传播——`agate/state-machine.md:311`（「P8 是**「发布准备」**」）+:315（表
  「发布准备 (READY)」）、`agate/dispatch-protocol.md:881`（P8→READY「发布准备完成」）、
  `agate/WORKFLOW.md:256`（「P8 发布准备」（同文件 :327 已改交付收尾 → 文件内不一致））、
  `agate/role-system.md:29`（「多包发布准备」）、`agate/assets/execution-roles/implementer.md:9`
  （角色标题「P8 发布准备」）。`state-machine.md:311` 直接违背 BDD-15「P8 语义为交付收尾」基线。
  描述活动级残留（state-machine:167/:438、implementer.md:11、P8-release.md:9/:29/:47、LIMITATIONS:119、
  WORKFLOW:166）措辞可对齐，判 DESIGN_GAP/观察。6 条 [DESIGN_GAP]：①-⑤ 判 DESIGN_GAP（交 P7）；
  ⑥（P8 叙事面未同步）**reclassify 为 MISALIGNED**（与 BDD-15/权威名直接矛盾，无 P7 REVIEWED-ACCEPTED
  → 原则 6）。NEEDS_HUMAN_REVIEW 0 条。
round7_conclusion: >-
  TAG0042 批 4 修复复审（round 7）：aligned。round6 的 3 项 MISALIGNED（A2/A3b/A5.3，同一根因 =
  P8 名称/语义「发布准备」→「交付收尾」未反向传播）已全部闭合：名称/身份级 6 处
  （state-machine.md:311/315、dispatch-protocol.md:881、WORKFLOW.md:256、role-system.md:29、
  implementer.md:9）+ 活动级残留（state-machine.md:167/438、implementer.md:11、P8-release.md:9/29/47、
  LIMITATIONS.md:119、WORKFLOW.md:166）均已改「交付收尾」。`grep -rn "发布准备"` 5 目标文件 → 0 命中；
  全 agate/（非 tests）仅剩 UPGRADING 的历史注（「原「发布准备」」+ 冻结历史版本节）。回归面：
  consistency 0 ERROR / 404 WARNING（无新增）；structure S1-S6/S0 全 OK；batch4 回归
  test_gate_layer+test_check_p8_delivery+test_check_gate+test_agate_run → 237 passed；修复仅动叙事文档 +
  test_agate_run.py 字符串字面量（编码守卫规避）→ A1/A3a/A4/A6/A7/A8 无回退。5 条 [DESIGN_GAP]
  （①-⑤）未受影响，仍判 DESIGN_GAP（交 P7）；⑥（P8 叙事面）即本轮闭合。NEEDS_HUMAN_REVIEW 0 条。
round8_conclusion: >-
  TAG0042 批 5（batch5-ci-doctor）增量复审（round 8）：aligned。变更面为 CI 与诊断——新增
  agate-ci-verify.py（实际重跑 gate 判定，无假绿；跳过面显式 SKIP: + 原因）+ agate-doctor.py
  （声明/hook/版本解析/账本四维诊断 + 修复指引，rc 恒 0）；删除 ci-gate-backstop.py 及其测试；
  workflow gate-backstop job 改调新脚本；check-protocol-consistency 移除退役锚点/extras/callers
  并保留退役名拦截。A1/A2 ALIGNED（两脚本行为 vs BDD-16/17 + P2 §4.4 逐条一致）；A3a ALIGNED
  （锚点表/extras/callers/agate-summary/README/workflow/6 协议文档 + formatters-README 同步）；
  A3b/A5.3 ALIGNED（退役名反向传播——CHECK10 扫描面 0 ERROR，CHECK10-scriptref 1 为既有 CHANGELOG
  聚合未新增；协议文档面 0 残留）；A4 ALIGNED（batch5 两文件 14 passed；count-tests 2671 = batch4
  2689 − 18 删退役测试）；A6 ALIGNED（SCRIPT_REF_RE 退役名拦截自洽；新脚本 agate-*.py 不在
  CHECK9-coverage/SG.6 glob；README 索引已补）；A7 ALIGNED；A8 声称均可复核；consistency 0 ERROR /
  406 WARNING；structure S1-S6/S0 全 OK；ruff 绿；平台扫描 0 命中。5 条 [DESIGN_GAP] 全判 DESIGN_GAP
  （交 P7）：① ci-verify 定位接口未固化；② doctor 退出码语义；③ 未移植 backstop 的 P3-TDD-red/
  P6-provenance CI 重跑；④ formatters/README 属 CHECK10 面但派发清单未列（必要同步）；⑤ workflow
  job 名保留 gate-backstop。观察（非阻塞）：docs/guides/project-map.md:59 活文档仍写
  ci-gate-backstop.py（非协议面/CHECK10 不扫）；agate-doctor 硬编码 .git/hooks（本仓未设
  core.hooksPath → 实测一致）。NEEDS_HUMAN_REVIEW 0 条。
---

# 协议-脚本对齐审查 — TAG0042 批 1（batch1-phase-semantics）

> 审查对象：`git diff` 未 commit 改动（HEAD `d3ba1c5` main，P3 已落）。
> 对齐基准：`P1-requirements.md` BDD-1/BDD-2、`P2-design.md` §1.1 M1/M2/M3 + §1.2 N1、`P4-implementation-batch1.md`、`P3-test-cases-batch1.md`。
> 权威规则源：`agate/state-machine.md`（§主 Agent 的单步执行）、`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（反向传播文档仍声明旧行为，见 A1） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（脚本新行为未传播到权威文档，同 A1 根因） |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **MISALIGNED** → 合计 **MISALIGNED** |
| A4 | 测试覆盖 | **ALIGNED**（全量实跑：批 1 相关文件零失败） |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **MISALIGNED** → 合计 **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：misaligned**。MISALIGNED 共 4 项（A1 / A2 / A3b / A5.3），**同一根因**：本批改变的是 `agate-next` 的可观测行为（不再写 `phase`、不再 `git add`），但 5 处**权威文档**仍逐字描述旧行为，未随批 1 同步。改动面本身（脚本 + 2 卡片 + UPGRADING + 测试）语义自洽。NEEDS_HUMAN_REVIEW 0 条。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**变更意图**：`phase` 只表示「本 commit 的产出阶段」。`agate-next` 推进时只输出「下一阶段建议」+ append `state_transition`，**不**写 `.state.yaml` 的 `phase`、**不** `git add`。

**脚本实现**（`agate-next.py:166-178` `_advance`）：

```python
def _advance(task_dir, state, target, repo_root):
    """输出「下一阶段建议」+ append state_transition 证据；**不预写**下一阶段（TAG0042 批 1）。"""
    old = state.get("phase", "")
    _state_transition_event(task_dir, old, target)
    _log(f"{old} → 建议下一阶段 {target}：.state.yaml phase **未预写**（保持 {old}）。"
         f"phase 由 {target} 产出 commit 时写入；推进证据已 append state_transition。")
```

模块 docstring（`agate-next.py:11-14`）与 `:31` 亦已改述为「不预写 / 不 git add」「无系统临时目录字面量」。**改动面内部（脚本 vs 卡片 vs UPGRADING）语义一致**。

**但权威文档未同步** —— 以下文档逐字声明「由 agate-next 写 `.state.yaml` phase + git add」，与新脚本行为**直接矛盾**（均不在 diff 内）：

1. `agate/state-machine.md:326-331`（§主 Agent 的单步执行，机械化段）：
   > 下面步骤 5-7（跑 gate → 按转移规则算下一状态 → **写回 `.state.yaml` + git add**）对**普通 phase** 是纯查表动作，由 `agate next`（`agate-next.py`）完成
   （另 `state-machine.md:394-396` step 7「写回 `.state.yaml`（新阶段 / 重试记录 / PAUSED）」为该权威语义的手工规格）
2. `agate/dispatch-protocol.md:291-292`：
   > 步骤 6 的「跑 gate → 判定 → **前进写 `.state.yaml` phase → git add**」这一段查表机械动作由 `agate next` 完成
3. `agate/CONTEXT.md:33`（术语表 `agate next / agate advance` 行）：
   > 查 `phases.yaml` 表机械推进一个 phase（跑 gate → 按 `next`/`retreat`/`gate_pass_exit` 算下一状态 → **写 `.state.yaml` + git add**）
4. `agate/loop-orchestration.md:242-247`：
   > …→ 按 phases.yaml next **更新 .state.yaml phase + git add** + state_transition 事件（只 add 不 commit…）
5. `agate/orchestrator-template.md:56`：
   > 状态推进：普通 phase 的「跑 gate → 判定 → **前进写 `.state.yaml` phase → commit**」这一步由 `agate next` 查表机械完成

**结论**：MISALIGNED。
**差异**：文档声明「agate-next 写 phase + git add」，脚本已删除该行为（`:166-178`），文档与脚本在不可绕开路径上的推进语义相反。
**建议**：把这 5 处改述为「`agate-next` 输出「下一阶段建议」，**不预写** `.state.yaml` phase、不 `git add`；`phase` 由下一阶段产出 commit 写入」——与 `agate-next.py:167-178`、`P2-design.md:15-16`、`UPGRADING.md:288-296` 同一口径。

> 说明：`UPGRADING.md:279-296`（v0.79.0 节）与改动后的两张卡片（`P2-design.md:15-17` / `P8-release.md:21`）**本身与脚本一致**，A1 的问题只在反向传播漏改的 5 处权威文档。

---

### A2: 脚本→文档对齐 — MISALIGNED

核对「脚本做了但文档（权威口径）没写 / 写了相反」的裸露行为。

| 脚本行为 | 权威文档对应 | 判定 |
|---|---|---|
| `_advance` 不写 `phase`、不 `git add`，输出建议文本 | `UPGRADING.md:288-296` + `P2-design.md:15-16` + `P8-release.md:21` 已记载 | ALIGNED（卡片/UPGRADING 面） |
| 同上 | `state-machine.md:326-331` / `dispatch-protocol.md:291-292` / `CONTEXT.md:33` / `loop-orchestration.md:242-247` / `orchestrator-template.md:56` 仍写「由 agate-next 写 phase + git add」 | **MISALIGNED**（与 A1 同 5 处） |
| `_advance` 仍 append `state_transition`（`from`/`to`/`phase`=target） | `loop-orchestration.md:258-260` / `CONTEXT.md:31`（账本事件类型含 `state_transition`）| ALIGNED（事件类型与账本描述不变） |
| `_write_state()` / `_git()` 删除（孤儿代码清理） | 无文档引用这两个函数名 | ALIGNED |

**结论**：MISALIGNED（同 A1 根因——脚本新行为只在卡片/UPGRADING 落地，未同步到权威协议文档）。
**建议**：同 A1。

> A1/A2 是同一处差异的**两个方向**（文档声明 X / 脚本做 ¬X），报告不重复计费为两条独立缺陷；均在 A3b 修复后一并转绿。

---

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b MISALIGNED（合计 MISALIGNED）

#### A3a（连锁：已知的衍生改动）— ALIGNED

- **孤儿函数**：`grep -n "_write_state\|_git(" agate/scripts/agate-next.py` → **0 命中**（`:116-129` 的 `_write_state` 与 `:169-183` 的 `_git` 已删，无残留调用）。全仓 `agate/scripts/*.py` 无其它脚本调用 `agate-next.py`（仅注释/docstring 提及）。
- **测试同步**：`test_tag0027_b1_agate_next_cli.py` 3 处「推进后 phase」断言已同步（`:156` L156→保持 P5；`:317` gate_p65 pass 后保持 P6；`:371` 保持 P5）；`_advance` 分支（`:279`/`:288`/`:386`）调用点与保留的 `repo_root` 形参兼容（docstring 已注明「批 1 后不再做 git 操作」）。**无遗留「预写」断言**。
- **状态跳变校验路径**：`check-state-transition.py` **只对暂存 `.state.yaml` 的 diff** 判 `old_phase → new_phase` 合法性（`:251-269`），不读账本 → 去 `git add` 后，phase 变更改由「下一阶段产出 commit 暂存 `.state.yaml`」触发同一校验，跳变合法性守护**未弱化**（与 `P2-design.md` §1.2 N1 一致）。
- **账本交叉**：`check-events.py` 对 `state_transition` 只做哈希链/已知类型处理（`:14`），**无** `state_transition.to == .state.yaml phase` 的交叉断言 → 新语义（事件记「建议推进」而 `.state.yaml` 保持旧 phase）**不破链、不触发审计**。
- **docstring 平台面**：`:31`「无 /tmp 字面量」→「无系统临时目录字面量」是为规避 `check-platform-assumptions.py` R4 自命中，方向正确（`_TMP` 拼接惯例同 `P3-test-cases-batch1.md` §4）。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— MISALIGNED

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| `agate/state-machine.md`（§单步执行 :326-331 + 手工规格 step 7 :394-396）| **否** —— 仍写「写回 `.state.yaml` + git add」由 agate-next 完成 | **MISALIGNED** |
| `agate/dispatch-protocol.md`（:291-292）| **否** —— 仍写「前进写 `.state.yaml` phase → git add」由 agate-next 完成 | **MISALIGNED** |
| `agate/CONTEXT.md`（:33 术语表）| **否** —— 仍写「写 `.state.yaml` + git add」 | **MISALIGNED** |
| `agate/loop-orchestration.md`（:242-247）| **否** —— 仍写「更新 .state.yaml phase + git add」 | **MISALIGNED** |
| `agate/orchestrator-template.md`（:56）| **否** —— 仍写「前进写 `.state.yaml` phase → commit」由 agate-next 完成 | **MISALIGNED** |
| `agate/WORKFLOW.md`（:502/:508）| 不需改 —— 只说「推进这一步用 `agate next` 查表机械完成」，未描述写 phase/git add | ALIGNED |
| `agate/git-integration.md`（:31/:33/:113）| 不需改 —— :31「产出和 .state.yaml phase 更新在同一个 commit 里」、:33「phase = 本 commit 提交的产出阶段，不得提前写」、:113 手工步「更新 .state.yaml phase（先更新再 commit）」**均与新语义一致** | ALIGNED |
| `agate/phase-cards/P1,P3,P4,P5,P6,P7-*.md` | 不需改 —— 各卡均写「phase 推进 Pn+1 **随 Pn+1 产出 commit 一起**」，本就与新语义一致（仅 P2/P8 需补「agate-next 亦不预写」注，已改） | ALIGNED |
| `agate/assets/execution-roles/*.md` / `review-roles/*.md` | 不需改 —— `grep agate-next\|预写\|更新 .state` **0 命中** | ALIGNED |
| `agate/CHANGELOG.md` | 待 P8（`check-changelog.py` 仅 P8 触发，见 A5.2）| 不计入批 1 |

**结论**：MISALIGNED（5 处权威文档反向传播缺失）。**建议**：同 A1；这 5 处为纯文本改述，与批 1 同批修最省（避免后续批次重复触达同一语义）。

> **无 P7 记录**：任务仍在 P4（`ls P7*` 无产物）。5 处缺失**不对应** `P4-implementation-batch1.md` 的两条 `[DESIGN_GAP]`（后者仅涉 UPGRADING 版本号标题 / `_advance` 孤儿函数），故不适用角色原则 6 的 `[KNOWN_DEVIATION]` 豁免，按普通 MISALIGNED 处理。

---

### A4: 测试覆盖 — ALIGNED

**新增/同步测试**：

- `agate/tests/unit/test_tag0042_batch1_phase_semantics.py`（P3 产出，6 例）：TC-B1-01（不预写 phase）/ TC-B1-02（不 `git add`）/ TC-B2-01（`_advance` 无 `state["phase"] = target`）/ TC-B2-02（卡片表述与行为一致）/ TC-B2-03（UPGRADING 记载不预写）/ TC-B2-04（全 `agate/scripts/*.py` 无预写实现）。覆盖 BDD-1/BDD-2 全部要求。
- `test_tag0027_b1_agate_next_cli.py`：3 处断言同步为新语义（A3a 已列），其余 `state_transition` 事件 / 不落盘 resolution / retreat 路径断言不变。

**边界评估**：新逻辑边界 = ① 不写 phase、② 不 `git add`、③ 仍发 `state_transition`、④ 建议文本。① ② ③ 均有直接断言；④ 由 `_advance` 调用链 + BDD-11 事件断言间接覆盖。孤儿函数删除无直接单测，但由源码扫描（TC-B2-01/04）+ 运行时调用点（A3a grep）双重约束。

**全量 pytest 实跑（A4 强制项，2026-10-06，本次审查执行）**：

```
$ python3 -m pytest agate/tests/ -q --tb=short -p no:cacheprovider
（worktree /home/kity/oclab/agateon，HEAD d3ba1c5 + 批 1 未 commit 改动）

=========================== short test summary info ============================
FAILED agate/tests/unit/test_agate_config.py ... (12)
FAILED agate/tests/unit/test_config_schema.py ... (10)
FAILED agate/tests/unit/test_agate_run.py ... (9)
FAILED agate/tests/unit/test_agate_doctor.py ... (8)
FAILED agate/tests/unit/test_events_ledger.py ... (6)
FAILED agate/tests/unit/test_agate_ci_verify.py ... (6)
FAILED agate/tests/unit/test_gate_layer.py ... (5)
FAILED agate/tests/unit/test_check_p8_delivery.py ... (3)
FAILED agate/tests/unit/test_setup_agate_dir.py ... (1)
FAILED agate/tests/unit/test_agate_scripts_encoding.py::test_bdd_5_all_test_py_text_io_explicit_encoding (1)
61 failed, 2624 passed, 2 skipped in 222.98s (0:03:42)
[exit 1]
```

**失败分类**：61 failed 全为 batch2-6 尚未实现的 P3 红灯（`test_agate_config`/`test_config_schema`/`test_agate_run`/`test_events_ledger`/`test_agate_ci_verify`/`test_gate_layer`/`test_check_p8_delivery`/`test_agate_doctor`/`test_setup_agate_dir` = batch2/3/4/5）——恒为「被测特性未实现」断言（如 `test_check_p8_delivery`：「`delivery` 未声明时 P8 gate 须拦截；当前 rc=2（无 delivery 校验）」）；`test_agate_scripts_encoding::test_bdd_5` 是扫描到 **batch2 测试文件** `test_config_schema.py:235` 缺 `encoding=`（属 batch2 测试自身质量，非批 1）。**batch1 相关 4 文件零失败**（`grep` 确认 log 中无 batch1 文件行）。

**结论**：ALIGNED。批 1 新逻辑覆盖充分、全量实跑无批 1 引入的回归。

---

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED / A5.3 MISALIGNED（合计 MISALIGNED）

#### A5.1 破坏性变更 / 向后兼容 — ALIGNED

- `.state.yaml` schema、字段集、frontmatter 均未变（`git diff` 不含 `agate/rules/` / `schema/` / `agate_common.py`）→ 存量任务无需迁移（与 `UPGRADING.md:281-282`「老任务无需迁移」一致）。
- 编排惯例变化已在 `UPGRADING.md:284-296` 明确告知（「phase 推进随下一阶段产出 commit 一起」），符合 `P1` §2 隐含需求 4。
- 回退路径（`agate-retreat-to.py`）仍写 phase，不在本批范围（`P2-design.md` §1.2 N2）——无破坏。

#### A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）

本批是协议语义变更，但本仓 `check-changelog.py` **仅 P8 触发**（`pre-commit-gate.py:522` `if phase == "P8"`；`WORKFLOW.md:355` 表 1.6「仅 P8 检查，P1-P7 不触发」）。`CHANGELOG.md` 顶部 `[Unreleased]` 当前为空，TAG0042 尚无条目——**属 P8 统一补**，符合既有 SELF-GATE 任务惯例（同 TAG0034 A5.2 判据）。**不判 MISALIGNED**。

#### A5.3 文档传播 — MISALIGNED

除代码改动外，应被影响的文档 = A3b 的 5 处权威文档（`state-machine.md` / `dispatch-protocol.md` / `CONTEXT.md` / `loop-orchestration.md` / `orchestrator-template.md`）——均**未同步**，仍描述旧行为。`P2-design.md:15-16` / `P8-release.md:21` / `UPGRADING.md:279-296` 已同步。**MISALIGNED**（同 A1/A2/A3b 根因）。

**结论**：合计 MISALIGNED（A5.1/A5.2 ALIGNED；A5.3 与 A3b 同 5 处）。

---

### A6: 锚点表覆盖 — ALIGNED

- 本批**未新增/改名** `agate/scripts/check-*.py`，也未改 `agate/rules/schema/` 字段集 → CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 无新增义务。
- `grep "agate-next\|agate next\|advance" agate/scripts/check-protocol-consistency.py` → **0 命中**（锚点表不引用 agate-next 行为）→ 无需更新锚点。
- 实跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **exit 0 / 0 ERROR / 400 WARNING**；`✅ PASS CHECK 9 协议-脚本结构对齐`，无 `CHECK9-coverage`。
- WARNING 400 = `CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 397`。较 `P2-design.md` §8 基线（398）多 2 —— 经 `--show-frozen-warnings` 定位为**本次派发文件** `P4-dispatch-context-protocol-alignment-review.md:12,32` 引用「尚未生成的成果报告路径 `docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`」产生的 2 条瞬时报错（本报告写盘后即消失），**非批 1 引入**。
- `bash agate/tests/scripts/count-tests.sh` → **2687**（与 `P4-implementation-batch1.md:88` 一致，未漂移）。

**结论**：ALIGNED。

---

### A7: 设计原则一致性 — ALIGNED

逐条核对相关 ADR（`agate/adr.md`）：

- **ADR-001（隔离性——主 Agent 不写产出）**：本批改的是**状态推进脚本**（`agate-next`），未授权主 Agent 写阶段产出；`phase` 语义收紧为「本 commit 产出阶段」反而强化了「状态与产出一致」。**一致**。
- **ADR-002（可判定性——gate 机器可判定）**：去掉预写后，推进判定仍由 `check-gate.py` exit code + `phases.yaml` 表机械完成；`state_transition` 账本事件保留为可观测证据。**一致**。
- **ADR-004（安全网分层——hook 兜底）**：`check-state-transition.py` 的跳变合法性校验路径不变（phase 由产出 commit 暂存触发，见 A3a）。**一致**（未弱化安全网）。
- **ADR-005（改动性质决定流程）**：本批属协议本体的行为逻辑改动 → 触发 SELF-GATE（本审查即该流程），方向一致。
- **是否存在未记录的新架构决策？** 「phase = 本 commit 提交的产出阶段，不得提前写」这一原则**已记录**于 `agate/git-integration.md:33`（明文档化的原则，非新决策）；本批是让**行为**与之一致（消歧义），不引入新架构决策 → **无需新增 ADR**。

**结论**：ALIGNED。（如需更强留痕，可在 P8 考虑把「phase 语义统一」的一句话回溯进 ADR，但非本批义务。）

---

### A8: 声称-命令绑定

对本批新增/变更的**数字或结论类声称**逐条给出产出命令：

| 声称 | 产出命令 | 结论 |
|---|---|---|
| `agate-next` 推进时不预写下一阶段（`UPGRADING.md:288` / 卡片 / 脚本 docstring）| `grep -n 'state\["phase"\] = target' agate/scripts/agate-next.py` → 0 命中；`python3 -m pytest agate/tests/unit/test_tag0042_batch1_phase_semantics.py -q` | ✅ 声称成立（代码移除 + 6 例绿） |
| 无破坏性变更 / 老任务无需迁移（`UPGRADING.md:279-282`）| `git diff -- agate/rules/ agate/scripts/agate_common.py agate/rules/schema/` → 空（schema/字段集未动）| ✅ 成立 |
| 「peekview T085 的 8 次 `--no-verify`」（`UPGRADING.md:294`）| `grep -n 'no-verify 8 次' /home/kity/oclab/peekview/docs/reviews/T085-retrospective-20260802.md` → 命中 L61/L85/L164/L212 | ✅ 数字成立（外部仓库；根因表述见该复盘 L87/L212「state.yaml phase 更新时机」） |
| 用例数 `2687`（`P4-implementation-batch1.md:88`）| `bash agate/tests/scripts/count-tests.sh` → `总计：2687 个测试用例` | ✅ 成立 |
| 一致性基线 `0 ERROR / 398 WARNING`（`P4-implementation-batch1.md:87`）| `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 400 WARNING | ⚠️ 当前 400（+2 为本次派发文件的瞬时引用告警，见 A6）；**0 ERROR 成立** |

无「无法给出命令」的无据声称；无应删项。

> 备注（非 MISALIGNED）：`UPGRADING.md:294` 把 `--no-verify` 归因于「预写 phase vs pre-commit 校验冲突」，而 T085 复盘的自述根因是「pre-commit hook **超时**」（`T085-retrospective-20260802.md:87/212`），其改进项 IMP-1 即「state.yaml phase 更新时机调整（commit 后更新）」。两处**方向一致**（皆指向 phase 写入时机），措辞侧重不同；不构成需修复项，提请 P7/P8 留意即可。

---

## 闭环规则表（本审查终态）

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **MISALIGNED** | A1 / A2 / A3b / A5.3（同一根因：5 处权威文档未反向传播）| **必须修复**：按 A1「建议」改述 `state-machine.md:326-331`（+ 手工规格 step 7 `:394-396`）`dispatch-protocol.md:291-292` `CONTEXT.md:33` `loop-orchestration.md:242-247` `orchestrator-template.md:56`，与新脚本/卡片/UPGRADING 同口径；修完重审。 |
| ALIGNED | A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | 通过。 |

**不可 commit**（存在未闭合 MISALIGNED）。修复后建议对本报告做同任务复核轮（round 2），追加 `round2_conclusion`。

---

## 附：A4 全量 pytest 尾部实跑输出

```
$ python3 -m pytest agate/tests/ -q --tb=short -p no:cacheprovider
（worktree /home/kity/oclab/agateon，2026-10-06）
...
FAILED agate/tests/unit/test_check_p8_delivery.py::test_bdd_15_p8_gate_passes_only_when_delivery_declared
FAILED agate/tests/unit/test_config_schema.py::test_bdd_5_schema_file_exists_and_is_isomorphic
FAILED agate/tests/unit/test_events_ledger.py::test_bdd_12_cmd_run_event_appended
FAILED agate/tests/unit/test_gate_layer.py::test_bdd_14_phases_yaml_selects_gate_sets_by_commit_type
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED agate/tests/unit/test_agate_scripts_encoding.py::test_bdd_5_all_test_py_text_io_explicit_encoding
61 failed, 2624 passed, 2 skipped in 222.98s (0:03:42)
[exit 1]
```

---

## round 2 复审（2026-10-06，同一任务复核轮）

> 复审范围：只复核首轮 MISALIGNED 的 4 项（A1 / A2 / A3b / A5.3）修复是否闭合，并确认修复未使首轮 ALIGNED 项回退（回归面）。
> 修复落点（`git diff` 可见，均未 commit）：`agate/state-machine.md`、`agate/dispatch-protocol.md`、`agate/CONTEXT.md`、`agate/loop-orchestration.md`、`agate/orchestrator-template.md`（纯文本改述，不改任何机制/脚本/卡片/UPGRADING/测试）。

### 复审结论汇总

| # | 审查项 | 首轮 | round 2 |
|---|--------|------|---------|
| A1 | 文档→脚本对齐 | MISALIGNED | **ALIGNED** |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED** |
| A3b | 反向传播 | MISALIGNED | **ALIGNED** |
| A5.3 | 文档传播 | MISALIGNED | **ALIGNED** |
| A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | — | ALIGNED | **无回退（ALIGNED）** |

**总结论：aligned**。首轮 4 项同一根因（5 处权威文档未反向传播）已全部闭合，无新增不一致，无回退。解除 commit 阻塞。

### A1 / A2 / A3b / A5.3 逐项复核 — ALIGNED

**统一口径基准**：`agate-next.py:166-178`（`_advance` 无 `state["phase"] = target` / 无 `_write_state` / 无 `_git`，仅 `_state_transition_event` + 输出「建议下一阶段」）、`P2-design.md:14-17`、`P8-release.md:21`、`UPGRADING.md:288-296`、`git-integration.md:31/33`（`phase` = 本 commit 提交的产出阶段，不得提前写下一阶段）。

5 处文档新表述逐处核对（同口径）：

| 文档（落点） | 新表述要点 | 判定 |
|---|---|---|
| `state-machine.md:326-335`（机械化段） | 步骤 5-7 表述「建议推进」；`agate next` 只输出「下一阶段建议」+ `state_transition` 事件、**不预写** `phase`、不 `git add`，`phase` 由下一阶段产出 commit 写入（并指 `git-integration.md`）；fallback 句补「手工 fallback 仍写 `phase`，与自动化路径不同」 | ALIGNED |
| `state-machine.md:401-403`（手工规格 step 7） | 保留「写回 `.state.yaml`」手工规格，显式加限定「本步为**手工 fallback** 规格；`agate next` 自动化路径**不写** `phase`」 | ALIGNED |
| `dispatch-protocol.md:291-295` | 「……前进写 phase → git add」改为「……前进」；补只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补「按该节手工规格写 `phase`」 | ALIGNED |
| `CONTEXT.md:33` | 术语行改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 `.state.yaml` 的 `phase`、不 `git add`——`phase` 由下一阶段产出 commit 写入」；fallback 补手工规格写 `phase`；标 TAG0042 批 1 | ALIGNED |
| `loop-orchestration.md:244-246`（自动推进流程图） | 「更新 .state.yaml phase + git add」改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 .state.yaml phase、不 git add」；跳变合法性改由下一阶段产出 commit 的 pre-commit 校验 | ALIGNED |
| `orchestrator-template.md:57-59` | 「前进写 `.state.yaml` phase → commit」改为「……前进」；补只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补手工规格写 `phase` | ALIGNED |

- **「自动化 `agate next` 不写 phase」与「手工 fallback 写 phase」的区分**：在 `state-machine.md`（机械化段 + 手工规格 step 7 两处）、`dispatch-protocol.md`、`CONTEXT.md`、`orchestrator-template.md` 四处显式标注；`loop-orchestration.md` 该段是自动推进流程图（仅描述自动化路径），无手工分支，无需 fallback 注——**区分充分，无歧义**。
- **残留旧行为复核**：`grep -rn "写回 .state.yaml + git add\|更新 .state.yaml phase + git add" agate/*.md` → **0 命中（exit 1）**。全 `agate/` tree 扫描「预写」仅剩新正确表述（`不预写`/`未预写`）与 `UPGRADING.md` 的否定式「不再预写」。
- **其余提及 phase 写入的位置**（`state-machine.md:523/625` 手工 commit / 重试记录、`git-integration.md:113` 手工提交步、`retrospective-template.md:134` 通用术语）经核对均属**手工提交/记录路径**描述，与新语义一致（`phase` 在产出 commit 时写入），**非旧自动化行为残留**，无需改——与首轮 A3b 判定一致。

**A1/A2/A3b/A5.3 结论**：4 项**全部 ALIGNED**（同一根因闭合）。

### 回归面复核 — 首轮 ALIGNED 项无回退

| 维度 | 复核命令 / 依据 | 结果 |
|---|---|---|
| CHECK2-refs / CHECK10 / 平台扫描 | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **exit 0 / 0 ERROR / 398 WARNING**；CHECK9 PASS；CHECK10 WARN 1（`check-windows-smoke.sh @ CHANGELOG.md:1529`，pre-existing，与本次无关）；CHECK2-refs **无来自 5 文档的新命中**（`--show-frozen-warnings` 逐条核对）；CHECK14/15 PASS |
| 文档平台假设 | 新表述文本无 `/tmp` 等字面量（显式传入 5 docs 仅在未改动的 `orchestrator-template.md:68` 命中原存 R2；文档不在 CI 目标面） | 无新增 |
| A4 用例覆盖 | `count-tests.sh` → **2687**（未漂移）；`pytest` batch1 4 文件 → **99 passed**；doc 关联 7 文件（doc_sweep / docs_assertions / protocol_mechanism_anchors / check_protocol_consistency / upgrading_contract_doc / protocol_dedup_audit / review_role_docs）→ **142 passed** | 无回归 |
| A3a（孤儿函数/事件/校验路径） | 修复未改脚本；`agate-next.py` diff 不变（`_write_state`/`_git` 已删、`state_transition` 保留） | 无回退 |
| A5.1 / A5.2 | 修复为纯文本，未动 `.state.yaml` schema / CHANGELOG（仍待 P8） | 无回退 |
| A6 / A7 / A8 | 未新增/改名脚本、未动锚点表、未引入新架构决策；无新增无据声称 | 无回退 |

### round 2 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1 / A2 / A3b / A5.3（首轮 MISALIGNED，本轮闭合）+ A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8（首轮 ALIGNED，无回退） | 通过，**可 commit**。 |

> 遗留（非阻塞，非 MISALIGNED）：首轮 A8 备注——`UPGRADING.md:294` 对 T085 `--no-verify` 的归因侧重（「预写 phase vs pre-commit 校验」vs 复盘自述「pre-commit hook 超时」）措辞不同但方向一致，交由 P7/P8 留意，不阻塞本批 commit。

**round 2 结论：ALIGNED（可 commit）。**

---

## round 3 复审（batch2 增量）（2026-10-06）

> 复审范围：TAG0042 批 2（`batch2-agate-config`，声明层）的 agate 协议/脚本未 commit 改动（HEAD `48091f2`，batch1 已落）。
> 触发模式：SELF-GATE「变更触发模式」A1-A8。
> 变更文件：新增 `agate/scripts/agate-config.py`、`agate/rules/schema/project-config.schema.json`；改 `agate/scripts/agate_common.py`（`read_project_config`）、`check-gate.py::gate_p0`（恒 return 2）、`install-hook.py`/`agate-setup.py`（自动 init）、`agate/UPGRADING.md`、`agate/scripts/README.md`、`agate-workspace/agents/CODE-MAP.md`、`test_agate_config.py`/`test_config_schema.py`（测试缺陷修正）。

### 复审结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **ALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：aligned**。MISALIGNED 0 条、NEEDS_HUMAN_REVIEW 0 条。4 条 `[DESIGN_GAP]` 全部归 **DESIGN_GAP（交 P7）**（见末节），无一条构成 `agate/` 协议文档↔脚本矛盾。变更行为已在权威迁移文档（UPGRADING）+ 新工具文档（scripts/README + CODE-MAP）落地。

### A1: 文档→脚本对齐 — ALIGNED

- **`gate_p0` 恒 return 2 口径**：脚本（`check-gate.py:631-652`）调 `agate-config validate` 子进程，`validate_rc` **只决定是否打印 WARNING**（`agate-config.py` 缺失时视为 0，不误报），随后**恒 `return 2`**。与 `UPGRADING.md:302-304`「迁移期行为与引入前一致：没有 `agate.config.yaml` 的存量项目，`gate_p0` 仍返回通过码（exit 2），只输出显眼 WARNING，不 exit 1」**逐字一致**。`agate-config.py:8-13` 退出码语义（0=成功/非 0=失败）与 `scripts/README.md:156` 同口径。
- **唯一读取函数防第二处解析**：`agate_common.py:851 read_project_config` 是唯一读取路径，docstring（`:832-836`）+ `agate-config.py:15-16` + `scripts/README.md:156` 均声明「声明解析只经 `agate_common.read_project_config`」。`grep read_project_config agate/`（非测试）→ 仅 `agate_common.py`（定义）+ `agate-config.py`（4 处调用）+ README。`agate-config.py` 对项目声明**无旁路 `yaml.safe_load`**（`yaml` 仅用于 `show` 的 `safe_dump`）；`gate_p0`/`install-hook` 经子进程调 `agate-config`，不自行解析。
- **schema 语义**：`project-config.schema.json` 的字段（`schema_version`/`project`/`verify.commands`/`release.preset`/`paths.evidence`）与 `agate-config.py` 的 `_INIT_TEMPLATE`、`read_project_config` 的 `PROJECT_CONFIG_DEFAULTS` 一致；`validate` 实测对非法 enum / 未知字段返回非 0 并指出字段名（见 A8）。

**结论**：ALIGNED。

### A2: 脚本→文档对齐 — ALIGNED

| 脚本行为 | 文档对应 | 判定 |
|---|---|---|
| `gate_p0` 调 validate、rc 只控 WARNING、恒 return 2 | `UPGRADING.md:302-304` | ALIGNED |
| `read_project_config`（唯一读取，缺失→`present=False` 不抛） | `agate_common.py:832-890` docstring + README | ALIGNED |
| `agate-config` 五子命令 + 退出码 | `scripts/README.md:156` + 脚本 docstring | ALIGNED |
| `install-hook`/`agate-setup` 自动 init（幂等） | `UPGRADING.md:300-301`（`agate-setup`/`install-hook` 接入时自动生成，幂等不覆盖） | ALIGNED |
| 新增 schema | `scripts/README.md`（validate schema 校验）+ P2 §1.1 M5 | ALIGNED |
| `install-hook` 新增 `_init_declaration` 行为 | `scripts/README.md:111`（install-hook 行）**未提**自动 init | 观察（见 A5，非矛盾） |

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b ALIGNED

#### A3a（连锁：已知衍生改动）— ALIGNED

- **孤儿/重复实现**：无。`agate-config.py` 未复制声明模板（`install-hook` 经子进程调 `agate-config init`，模板单一实现在 `agate-config.py:_INIT_TEMPLATE`）；`agate_common` 的默认值单一实现，`agate-config.py` 仅做内部键过滤（`_INTERNAL_KEYS`）。
- **测试同步**：`test_config_schema.py:235` docstring 措辞修正（避编码守卫 `test_agate_scripts_encoding` 误判）、`test_agate_config.py:25` 删未用 `import os`（避 ruff F401）——均不改断言语义。
- **subprocess 隔离**：`install-hook._init_declaration` 用 `sys.executable` + 同目录脚本；`agate-config.py` 缺失时只提示不阻断（fake 安装根测试场景）。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— ALIGNED

新引入的「项目声明」概念是否需要传播到权威流程文档？逐一核查：

| 应被影响候选 | 影响到了没 | 判定 |
|---|---|---|
| `agate/state-machine.md` | 无需改 —— 描述阶段转移机制，不涉及项目接入/声明；`grep agate.config\|声明文件\|声明层` → 0 命中，无 stale 旧行为声明 | ALIGNED |
| `agate/dispatch-protocol.md` | 无需改 —— 同上（0 命中） | ALIGNED |
| `agate/WORKFLOW.md` | 无需改 —— 「Pre-commit 检查总览」表未枚举 `gate_p0` 内部行为；gate_p0 的触发条件（phase 变更）未变 | ALIGNED |
| `agate/role-system.md` / `orchestrator-template.md` | 无需改 —— 0 命中 | ALIGNED |
| `agate/phase-cards/P0-orchestrator.md` 及其余卡片 | 无需改 —— P0 卡描述「主 Agent 亲自写 P0-brief」，不含 `gate_p0` 返回值声明 | ALIGNED |
| `agate/assets/execution-roles/*` / `review-roles/*` | 无需改 —— 0 命中 | ALIGNED |
| `agate/UPGRADING.md` 截止版本自洽 | **已改** —— 批 2 小节在 `### v0.79.0` 节内（与批 1 同节），截止版本 v0.80.0（下一 minor），表述自洽 | ALIGNED |
| `agate/scripts/README.md`（工具索引） | **已改** —— 补 `agate-config.py` 行 | ALIGNED |
| `agate-workspace/agents/CODE-MAP.md` | **已改** —— 补「项目声明族」 | ALIGNED |

**结论**：A3b ALIGNED（派发指引点名的 5 类文件均无需传播；无反向传播遗漏）。

### A4: 测试覆盖 — ALIGNED

- **批 2 相关测试全绿（实跑）**：`python3 -m pytest agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py agate/tests/unit/test_agate_scripts_encoding.py -q` → **24 passed**（与 `P4-implementation-batch2.md:116` 自报吻合）。
- **关联回归（实跑）**：上述 3 文件 + `test_check_gate.py` + `test_install_hook.py` + `test_agate_common.py` → **279 passed**。
- **边界覆盖**：BDD-5（schema 同构 / 非法 enum / 未知字段 / 合法声明）、BDD-6（唯一读取函数存在 / 声明值回读 / 两处取值同源 / 无第二处解析）、BDD-7（install-hook 自动 init / 幂等 / setup 接入点）、BDD-8（gate_p0 缺失声明仍 rc=2 + WARNING / UPGRADING 截止版本）、BDD-3/4/20（声明驱动、子命令退出码、非单项目硬编码）均有直接断言。schema 的**同构**由 `test_bdd_5_schema_file_exists_and_is_isomorphic` 机械守护。
- **用例总数**：`count-tests.sh` → **2687**（未漂移）。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED（待 P8）/ A5.3 ALIGNED

- **A5.1 破坏性变更 / 向后兼容 — ALIGNED**：迁移期 `gate_p0` 恒 return 2（行为与引入前一致），无声明的存量项目不受影响；`.state.yaml` schema / 字段集未动（`git diff` 不含 `agate/rules/schema/{phases,dispatch,roles,markers}.schema.json`，仅**新增** `project-config.schema.json`，符合 P2 §1.2 N6）。截止版本 v0.80.0 已在 UPGRADING 明示。
- **A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）**：本批是协议行为变更，但 `check-changelog.py` 仅 P8 触发；`CHANGELOG.md` 待 P8 统一补（同 batch1 判据）。
- **A5.3 文档传播 — ALIGNED**：本批应传播的文档 = `UPGRADING.md`（已改，批 2 小节）+ `scripts/README.md`（已改）+ `CODE-MAP.md`（已改）。派发指引点名的 state-machine/dispatch-protocol/WORKFLOW/卡片/角色文件**均无需改**（A3b 已逐条验证）。
  - **非阻塞观察（完备性缺口，非 MISALIGNED）**：`agate/SETUP.md`「它做的事」表、`agate/scripts/README.md` 的 `install-hook.py`/`agate-setup.py` 行、`agate/CONTEXT.md` 术语表**未提及**接入时自动生成声明。三处均为**遗漏而非矛盾**（行为已在 `UPGRADING.md` 记载），建议后续批次补记；不阻塞本批 commit。

**结论**：合计 ALIGNED。

### A6: 锚点表覆盖 — ALIGNED

- **`agate-config.py` 不在门禁面**：`check-protocol-consistency.py:uncovered_gate_scripts()` 的 glob = `check-*.py` + `pre-commit-gate.{sh,py}` + `ci-gate-backstop.py`；`agate-config.py` 是 `agate-*.py` → 不触发 CHECK9-coverage / SG.6。**实测**：`pytest .../test_protocol_alignment_review.py -k sg_6` → **1 passed**；consistency `CHECK 9 ✅ PASS`，无 `CHECK9-coverage`。
- **新 schema 是否被 CHECK 覆盖**：`project-config.schema.json` 位于 `rules/schema/*.json` → **被 CHECK 15（数据面平台名扫描）覆盖**（`check-protocol-consistency.py:1378-1380` glob 含 `schema/*.json`），CHECK 15 ✅ PASS；`test_bdd_5_schema_file_exists_and_is_isomorphic` 机械守护其与既有 4 schema 同构。
  - **非阻塞观察**：P2 §1.4 称新 schema 由 `check-yaml-schema.py`/`check-structure-consistency.py`（S-5）覆盖——实测 `check-yaml-schema.py` 仅校验**硬编码的 4 对** `rules/{phases,dispatch,roles,markers}.yaml↔schema`，新 schema 不在其列（它校验的是 `agate.config.yaml` 而非 `rules/*.yaml`，故本不应入 S-5 对列表）。**R5 schema 自身健全性自检未覆盖新 schema**（仅 CHECK15 扫描 + 同构测试）。P2 该句表述不精确，属任务设计文档措辞，非 `agate/` 协议文档矛盾 → 观察，建议 P7 留意。
- **无需更新锚点表**：本批未新增/改名 `check-*.py`。

**结论**：ALIGNED。

### A7: 设计原则一致性 — ALIGNED

- **ADR-003（最小约定——不绑定技术栈）**：本批是 ADR-003 的**直接落地**——项目形态（语言/包管理器/验证命令/发版方式）由项目自带 `agate.config.yaml` 声明，协议不硬编码技术栈（`read_project_config` 函数体无 `agateon`/`peekview`/`pytest` token，`agate-config.py` 无 `python3` 硬编码 token）。**一致**。
- **ADR-014（判据单一权威源）**：「唯一读取函数」`read_project_config` 是声明解析的单源，等价守护测试（两处取值同源 + 无第二处解析）防漂移。**一致**。
- **ADR-002（可判定性）**：gate_p0 恒 return 2、validate 退出码为可判定信号；声明缺失迁移期只 WARNING（可观测、不阻断）。**一致**。
- **ADR-001（隔离性）**：声明由项目自述，主 Agent/脚本不写死项目形态。**一致**。
- **是否存在未记录的新架构决策？** 「项目形态声明化 + 唯一读取函数」是 ADR-003 + ADR-014 的既有原则在新层的应用，**不引入新架构决策** → 无需新增 ADR。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| `gate_p0` 恒 return 2（UPGRADING:303-304 / P4-impl） | 读 `check-gate.py:631-652`（恒 `return 2`）；`pytest test_agate_config.py::test_bdd_8_*` | ✅ 成立 |
| 迁移期只 WARNING（UPGRADING:302-304） | `test_bdd_8_gate_p0_missing_declaration_emits_warning` + 实测子进程输出含 `WARNING` + 文件名 | ✅ 成立 |
| 唯一读取函数、无第二处解析（README:156 / P4-impl） | `grep read_project_config agate/`（非测试仅 common+config）；`test_bdd_6_no_second_independent_yaml_parser_in_config` | ✅ 成立 |
| 截止版本 v0.80.0（UPGRADING:305-307） | `grep -n "v0.80.0" agate/UPGRADING.md` | ✅ 成立 |
| batch2 红→绿 `24 passed`（P4-impl:116） | `pytest test_agate_config.py test_config_schema.py test_agate_scripts_encoding.py -q` → 24 passed | ✅ 成立 |
| consistency `0 ERROR / 401 WARNING`（P4-impl:118） | `check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 401 WARNING | ✅ 0 ERROR 成立（401 为冻结文件面） |
| count-tests `2687`（P4-impl:119） | `count-tests.sh` → 2687 | ✅ 成立 |
| ruff `All checks passed`（P4-impl:120） | `~/.venvs/agate-dev/bin/ruff check agate/` | ✅ 成立 |
| 平台扫描「新增行 0 命中」（P4-impl:121） | `check-platform-assumptions.py <改动文件>` → R2 命中均为存量行（`agate_common.py:332`/`install-hook.py:257`/`agate-setup.py:157,848,945`），非本批新增行 | ✅ 成立 |

无「无法给出命令」的无据声称。

### [DESIGN_GAP] 逐条判定（4 条）

| # | DESIGN_GAP | 判定 | 依据 |
|---|---|---|---|
| ① | P2 §4.1 正文「validate 缺失返回 0」vs N2 伪代码 / TC-B8 矛盾 | **DESIGN_GAP（交 P7）** | P2 **自相矛盾**（§4.1 正文 vs 同节 N2）；实现随 N2 + P3（`test_bdd_8_*` 要求 WARNING）+ `UPGRADING.md:302-304`——三者互相一致。P2 正文为离群句，属任务设计文档需订正（建议 P7 或 P2 baseline change），**非 `agate/` 协议文档↔脚本矛盾**，不判 MISALIGNED |
| ② | 脚本内 draft-07 子集校验器（不引入 jsonschema / 未复用 check-yaml-schema.py） | **DESIGN_GAP（交 P7）** | P2 未指定实现方式；无协议文档强制复用 `check-yaml-schema.py`（后者为 `check-*.py` 且带 `if __name__` 侧效应）。设计选择，语义自洽 |
| ③ | install-hook 经子进程调 `agate-config init`（非内联模板） | **DESIGN_GAP（交 P7）** | P2 §1.1 M7 未指定路径；子进程方案保持声明模板单一实现，契合 BDD-6 单源精神。设计选择 |
| ④ | `read_project_config` 默认注入使 schema `required` 不触发 | **DESIGN_GAP（交 P7）** | 实测：仅 `schema_version`（缺 required `project`）→ validate rc=0；`{}` → rc=0。在 **effective-config 模型**下自洽（validate 校验的是已注入默认值的 dict，`required` 被默认**满足**、非违反），故**非** `agate/` 协议文档↔脚本矛盾。但有**语义影响**（schema `required` 形同虚设）——建议 P7 明确裁决：或从 schema 去掉 `required`，或让 validate 对「用户声明的键集合」判 required |

**判定合计**：4 条**全部 DESIGN_GAP（交 P7）**；**MISALIGNED 0 条**。按角色原则 6——4 条均不对应「`agate/` 协议文档↔脚本不一致」（① 是 P2 内部矛盾，②③ 是 P2 未指定的设计选择，④ 在 effective-config 模型下自洽），故不适用「无 P7 记录即按 MISALIGNED」的触发条件；P7 需逐条转抄 `DESIGN_GAP_REVIEWED`。

### round 3 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1/A2/A3a/A3b/A4/A5.1/A5.2/A5.3/A6/A7/A8 | 通过，**可 commit**。 |
| **DESIGN_GAP（交 P7）** | 4 条（见上表） | P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`；其中 ④ 建议明确 schema `required` 去留。 |
| **观察（非阻塞）** | SETUP.md / scripts-README(install-hook 行) / CONTEXT 未提自动 init；P2 §1.4 对新 schema 的 S-5 覆盖表述不精确 | 建议后续补记，不阻塞。 |

**round 3 结论：ALIGNED（可 commit）。**

---

## round 4 复审（batch3 增量）（2026-10-06）

> 复审范围：TAG0042 批 3（`batch3-agate-run`，执行层）的 agate 协议/脚本未 commit 改动（HEAD `18b3e3d`，batch2 已落）。
> 触发模式：SELF-GATE「变更触发模式」A1-A8。
> 变更文件：新增 `agate/scripts/agate-run.py`；改 `agate/scripts/pre-commit-gate.py`（一并 git add 账本 + 导入文案）、`agate/scripts/README.md`、`agate-workspace/agents/CODE-MAP.md`。

### 复审结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED**（新增 `cmd_run` 事件类型未同步到协议文档的事件类型枚举） |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **MISALIGNED** → 合计 **MISALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **MISALIGNED** → 合计 **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：misaligned**。MISALIGNED 共 3 项（A2 / A3b / A5.3），**同一根因**：本批新增账本事件类型 `cmd_run`，但两处**协议文档的事件类型枚举**未同步（见 A2/A3b）。改动面本身（脚本 + hook + README + CODE-MAP）语义自洽。2 条 `[DESIGN_GAP]` 均归 DESIGN_GAP（交 P7）。NEEDS_HUMAN_REVIEW 0 条。

### A1: 文档→脚本对齐 — ALIGNED

- **pipefail 写法**：`agate-run.py:83-89` 用 `"set -o pipefail; " + cmd` + `shell=True, executable="bash"`——与 P2 §4.2（:277-280）及既有 `agate_common.py:747-756` 的已验证写法**逐字同口径**（明确排除 `executable="bash -o pipefail"`）。
- **`.out` 证据（BDD-10）**：`_evidence_path` = `{paths.evidence}/cmd-<index>.out`（缺省 `.agate-evidence`），首次 `--baseline` 落盘、后续逐字节比对（`_read_bytes` vs `output.encode("utf-8")`），差异 → 非 0。与 P2 §4.2（:281）一致。
- **ignore 检查（BDD-11）**：`_is_ignored` 用 `git check-ignore -- <rel>`（rc0=已忽略 / rc1=未忽略 / 其它=无法判定→WARNING 跳过）；未覆盖 → 报错且**不落盘**。与 P2 §4.2（:282）一致。
- **平台分支（m-2）**：`sys.platform == "win32"` → 退化直执行 + 显式 `WARNING`（不静默报绿，ADR-015 手段②）。与 P2 §4.2（:285-289）一致。
- **`cmd_run` 事件（BDD-12）**：`_record_cmd_run` 经 `agate_common.append_event`（唯一写路径）写 `event/cmd/exit/runner`；`append_event`（`agate_common.py:524-566`）自动补 `ts` + `prev_hash` → 满足 BDD-12「命令 / 退出码 / 时间戳」字段。`AGATE_TASK_DIR` 定位账本（P3 §5 约定）。与 P2 §4.2（:283-284）一致。
- **不可绕开路径**：`_resolve_command` 要求 CLI 实参**精确匹配** `verify.commands` 一条，否则拒绝执行（rc=1）。与 docstring/README 一致。

**结论**：ALIGNED。

### A2: 脚本→文档对齐 — MISALIGNED

脚本新增了账本事件类型 `cmd_run`（`agate-run.py:131-136` 经 `append_event` 写入），但**两处协议文档的「事件类型枚举」未同步**：

1. `agate/CONTEXT.md:31`（术语表 `gate-events.jsonl` 行）：
   > 每任务 append-only 事件账本（`gate_run` / `judge_verdict` / `state_transition` / `dispatch_route`）……
2. `agate/git-integration.md:176-177`：
   > **`gate-events.jsonl` 事件账本**（`gate_run` / `state_transition` / `judge_verdict` / `dispatch_route` 追加行，pre-commit hook 会追加、随本 commit 一起入库……）

`cmd_run` 目前**仅**出现在 `agate/scripts/README.md:157`（新工具行），未进入上述两处枚举。**先例**：`dispatch_route`（TAG0034）由专门提交 `b68af6b`（"批 C —— CONTEXT.md + git-integration.md 大改"）加入上述两处——即新事件类型须同步两枚举。

**结论**：MISALIGNED。
**差异**：文档枚举账本事件类型为 4 种（不含 `cmd_run`），脚本已写第 5 种，枚举不再完整。
**建议**：在 `CONTEXT.md:31` 与 `git-integration.md:176-177` 的事件类型枚举各补 `cmd_run`（纯文本）。`check-events.py:14` docstring 的「已知类型」注释可顺带补 `cmd_run`（非门禁，可选）。

> A1/A2 是同一差异的两个方向；本项为纯「脚本新行为未落文档」（A2），故 A1 仍 ALIGNED。

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b MISALIGNED（合计 MISALIGNED）

#### A3a（连锁：已知衍生改动）— ALIGNED

- **账本写路径**：`cmd_run` 经 `append_event`（唯一写路径），未直接 `open(..., 'a')` 写账本；`check-events.py` 第 7 条「未知 event 类型不拦截」→ 链完整、审计通过（`test_bdd_12_ledger_hash_chain_preserved` 绿）。
- **hook 暂存**：`pre-commit-gate.py:424-429`（2h.1d）在 `if phase_changed:` **同级**（非嵌套）新增 `run_git(["add", …/gate-events.jsonl])`——把 agate-run 追加的 `cmd_run` 及本 hook 的 `gate_run`/`state_transition` 一并入库；**不直接写账本**（防破 `prev_hash` 链，P2 R5）。`git-integration.md:175-178` 已述「pre-commit hook 会追加、随本 commit 一起入库」，与该行为一致。
- **导入文案**：`pre-commit-gate.py` 的 `python3`→`Python 3`（消除平台扫描 R2 存量命中，无测试断言该文案）。
- **测试同步**：无（新增测试文件由 P3 产出，本批实现转绿）。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— MISALIGNED

| 应被影响候选 | 影响到了没 | 判定 |
|---|---|---|
| `agate/CONTEXT.md:31`（账本事件类型枚举）| **否** —— 仍为 4 种（缺 `cmd_run`） | **MISALIGNED** |
| `agate/git-integration.md:176-177`（账本事件类型枚举）| **否** —— 仍为 4 种（缺 `cmd_run`） | **MISALIGNED** |
| `agate/state-machine.md` | 无需改 —— 无账本事件类型枚举（CONTEXT:31 的「首次定义位置」指向其，但正文未枚举类型） | ALIGNED |
| `agate/dispatch-protocol.md` | 无需改 —— 仅 judge 白名单提及 `gate-events.jsonl`，不枚举事件类型 | ALIGNED |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」| 无需改 —— 该表列 `check-*.py` **检查项**；账本暂存非检查项，且已由 `git-integration.md:177` 描述 | ALIGNED |
| `agate/phase-cards/*` / `execution-roles/*` / `review-roles/*` | 无需改 —— 无账本事件类型枚举 | ALIGNED |
| `agate/scripts/README.md` / `CODE-MAP.md` | **已改** —— 补 `agate-run.py` 行 / 执行层族 | ALIGNED |

**结论**：MISALIGNED（2 处事件类型枚举反向传播缺失）。**建议**：同 A2。

### A4: 测试覆盖 — ALIGNED

- **批 3 相关测试全绿（实跑）**：`pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q` → **15 passed**（与 `P4-implementation-batch3.md:78` 自报吻合）。
- **hook 集成无回归（实跑）**：`pytest agate/tests/integration/test_pre_commit_hook.py -q` → **61 passed**。
- **关联回归（实跑）**：`test_check_events.py` + `test_t42_p3_platform_selfcheck.py` + `test_agate_gate_p5_count.py` → **24 passed**。
- **边界覆盖**：BDD-9（成功/非 0 退出码/pipefail 左失败/平台分支源码）、BDD-10（baseline 落盘/一致/差异）、BDD-11（ignore 命中/未覆盖报错）、BDD-12（事件追加/字段/链完整/append_event 链约定/源码唯一写路径/hook 暂存）均有直接断言。
- **用例总数**：`count-tests.sh` → **2688**（未漂移）。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED（待 P8）/ A5.3 MISALIGNED

- **A5.1 破坏性变更 / 向后兼容 — ALIGNED**：新增工具 + 账本暂存，不改既有 gate 判定/`.state.yaml` schema/账本链格式；`cmd_run` 为新增事件类型（`check-events.py` 向后兼容不拦截）。既有 hook 行为增强（一并暂存账本）与 `git-integration.md:175-178` 一致。
- **A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）**：`check-changelog.py` 仅 P8 触发，`CHANGELOG.md` 待 P8 统一补（同 batch1/2 判据）。
- **A5.3 文档传播 — MISALIGNED**：除代码改动外，应被影响的文档 = A3b 的 2 处账本事件类型枚举（`CONTEXT.md:31` / `git-integration.md:176-177`）——均**未同步**。`scripts/README.md` / `CODE-MAP.md` 已同步。
  - **非阻塞观察**：BDD-9「经 agate-run 执行验证命令」尚未传播到 `verifier.md` / P5 卡 / WORKFLOW——但 batch3 `§6.1b`/`§12` 声明的 output 仅脚本，工作流接线属后续（非本批义务）。建议主 Agent 确认归属批次。

**结论**：合计 MISALIGNED（A5.1/A5.2 ALIGNED；A5.3 与 A3b 同 2 处）。

### A6: 锚点表覆盖 — ALIGNED

- **`agate-run.py` 不在门禁面**：`uncovered_gate_scripts()` 的 glob = `check-*.py` + `pre-commit-gate.{sh,py}` + `ci-gate-backstop.py`；`agate-run.py` 是 `agate-*.py` → 不触发 CHECK9-coverage / SG.6。**实测**：`pytest .../test_protocol_alignment_review.py -k sg_6` → **1 passed**；consistency `CHECK 9 ✅ PASS`，无 `CHECK9-coverage`。
- **README 索引行**：已补（非门禁，约定）。
- **无需更新锚点表**：本批未新增/改名 `check-*.py`，未改 `rules/schema/` 字段集。

**结论**：ALIGNED。

### A7: 设计原则一致性 — ALIGNED

- **ADR-015（实质/非实质——让错误可见）**：平台退化路径**显式 WARNING**（`_run_command` win32 分支），绝不静默报绿——本批是该原则（手段②）的落地。**一致**。
- **ADR-002（可判定性）**：退出码如实传播、`.out` 逐字节比对为二值判定、ignore 检查经 `git check-ignore` exit code。**一致**。
- **ADR-004（安全网分层）**：账本暂存走 `append_event` 唯一写路径 + hook 一并入库，不绕过哈希链。**一致**。
- **ADR-003（不绑定技术栈）**：命令来自声明 `verify.commands`，脚本不硬编码技术栈。**一致**。
- **是否存在未记录的新架构决策？** 「验证命令经不可绕开路径执行」是 ADR-003（不绑定技术栈）+ ADR-004（安全网）+ ADR-015（让错误可见）在新执行层的应用，**不引入新架构决策** → 无需新增 ADR（如需更强留痕，P8 可考虑把「声明层/执行层分离」回溯进 ADR，非本批义务）。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| batch3 红→绿 `15 passed`（P4-impl:78）| `pytest test_agate_run.py test_events_ledger.py -q` → 15 passed | ✅ 成立 |
| hook 集成 `61 passed`（P4-impl:79）| `pytest test_pre_commit_hook.py -q` → 61 passed | ✅ 成立 |
| 关联回归 `24 passed`（P4-impl:80）| `pytest test_check_events.py test_t42_p3_platform_selfcheck.py test_agate_gate_p5_count.py -q` → 24 passed | ✅ 成立 |
| consistency `0 ERROR / 402 WARNING`（P4-impl:81）| `check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 402 WARNING | ✅ 0 ERROR 成立（402 为冻结文件面） |
| count-tests `2688`（P4-impl:82）| `count-tests.sh` → 2688 | ✅ 成立 |
| ruff `All checks passed`（P4-impl:83）| `~/.venvs/agate-dev/bin/ruff check agate/scripts/` | ✅ 成立 |
| 平台扫描 0 命中（P4-impl:84）| `check-platform-assumptions.py agate-run.py pre-commit-gate.py` → exit 0（0 命中） | ✅ 成立 |
| 账本隔离无污染（P4-impl:85）| `git status --porcelain` → 无 `gate-events.jsonl`/`.out` 新增 | ✅ 成立 |
| `cmd_run` 经 append_event 不破链（脚本/README）| `test_bdd_12_ledger_hash_chain_preserved` + `check-events.py` item 7 向后兼容 | ✅ 成立 |

无「无法给出命令」的无据声称。

### [DESIGN_GAP] 逐条判定（2 条）

| # | DESIGN_GAP | 判定 | 依据 |
|---|---|---|---|
| ① | P2 §4.2/M10「修正 formatter 计数」无缺陷/落点/判据，P3 无覆盖用例（实现未做） | **DESIGN_GAP（交 P7）** | 核查：与 formatter 计数相关的既有代码 `is_gate_meta_key`（后缀排除，正确）、`_fallback_json`（无 formatter 恒 0，为既有设计、A/B 出口码依赖它）、`agate-capture-env-baseline.py` 一致性检查（不在本批 output 面）——均无可复现缺陷；改动 `_fallback_json` 将违反 P2 §1.2 N3（不改 TDD 判定语义）。属 P2 条目不可执行，建议 P2 删/细化。**非 `agate/` 协议文档↔脚本矛盾**，不判 MISALIGNED |
| ② | P2 §4.2 写 `agate-run <cmd-key|命令>`，但 schema `verify.commands` 为字符串数组、无命名 key（实现按命令文本精确匹配 + 下标槽位） | **DESIGN_GAP（交 P7）** | P2 与 schema 的接口张力；实现以命令文本精确匹配 + 声明下标作稳定证据槽位（使 BDD-10-03 成立）。设计选择，语义自洽；若需命名 key 须先扩 schema。**非协议文档↔脚本矛盾** |

**判定合计**：2 条**全部 DESIGN_GAP（交 P7）**；**MISALIGNED 0 条来自 DESIGN_GAP**（本批的 3 条 MISALIGNED 来自 `cmd_run` 反向传播，与 DESIGN_GAP 无关）。按角色原则 6——2 条均不对应「`agate/` 协议文档↔脚本不一致」（① 是 P2 条目不可执行，② 是 P2 与 schema 的接口张力），故不适用「无 P7 记录即按 MISALIGNED」的触发条件；P7 需逐条转抄 `DESIGN_GAP_REVIEWED`。

### round 4 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **MISALIGNED** | A2 / A3b / A5.3（同一根因：`cmd_run` 未同步到 `CONTEXT.md:31` + `git-integration.md:176-177` 的事件类型枚举）| **必须修复**：两处枚举各补 `cmd_run`（纯文本，与先例 `dispatch_route`/`b68af6b` 一致）；修完重审（round 5）。 |
| **ALIGNED** | A1 / A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | 通过。 |
| **DESIGN_GAP（交 P7）** | 2 条（见上表）| P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`。 |
| **观察（非阻塞）** | BDD-9「经 agate-run 执行」未传播到 verifier/P5 卡（batch3 output 仅脚本）| 建议主 Agent 确认归属批次。 |

**不可 commit**（存在未闭合 MISALIGNED）。修复后建议对本报告做同任务复核轮（round 5），追加 `round5_conclusion`。

**round 4 结论：MISALIGNED（须修复 2 处事件类型枚举）。**

---

## round 5 复审（batch3 修复闭合）（2026-10-06）

> 复审范围：round4 判 MISALIGNED 的 3 项（A2 / A3b / A5.3，同一根因 = `cmd_run` 未传播到事件类型枚举）修复是否闭合，以及修复是否引入新不一致（回归面）。HEAD `18b3e3d`（batch2 已落），batch3 改动未 commit。
> 修复文件：`agate/CONTEXT.md`、`agate/git-integration.md`、`agate/scripts/check-events.py`（均纯文本/注释）。

### 复审结论汇总

| # | 审查项 | round 4 | round 5 |
|---|--------|---------|---------|
| A1 | 文档→脚本对齐 | ALIGNED | **ALIGNED（无回退）** |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED（闭合）** |
| A3 | 一致性连锁 + 反向传播 | A3a ALIGNED / A3b MISALIGNED | A3a **ALIGNED** / A3b **ALIGNED（闭合）** |
| A4 | 测试覆盖 | ALIGNED | **ALIGNED（无回退）** |
| A5 | 下游影响 + 文档传播 | A5.1/A5.2 ALIGNED / A5.3 MISALIGNED | A5.1/A5.2 **ALIGNED** / A5.3 **ALIGNED（闭合）** |
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED（无回退）** |
| A7 | 设计原则一致性 | ALIGNED | **ALIGNED（无回退）** |
| A8 | 声称-命令绑定 | ALIGNED | **ALIGNED（无回退）** |

**总结论：aligned**。round4 的 3 项 MISALIGNED 已全部闭合，无新增不一致，无回退。解除 commit 阻塞。

### A2 / A3b / A5.3 逐项复核 — ALIGNED（闭合）

同一根因的 3 处修复（`git diff` 逐处核对）：

| 落点 | 修复后枚举 | 判定 |
|---|---|---|
| `agate/CONTEXT.md:31`（术语表 `gate-events.jsonl` 行）| `gate_run` / `judge_verdict` / `state_transition` / `dispatch_route` / **`cmd_run`** | 闭合 |
| `agate/git-integration.md:176-177`（commit 一并暂存的账本枚举）| `gate_run` / `state_transition` / `judge_verdict` / `dispatch_route` / **`cmd_run`** | 闭合 |
| `agate/scripts/check-events.py:14`（docstring 已知类型注释，可选）| `...dispatch_route/cmd_run` | 闭合（纯注释，审计逻辑零改动） |

- **残留旧枚举复核**：`grep -rn "gate_run.*dispatch_route" agate/*.md agate/**/*.md agate/scripts/*.py`（排除含 `cmd_run` 者）→ **0 命中**。两处协议文档枚举均已含 `cmd_run`，与 `agate-run.py:131-136` 写入的 `cmd_run` 事件一致。
- **与先例一致**：`dispatch_route`（TAG0034，提交 `b68af6b`）亦同时进入上述两处枚举——本修复沿用同一约定。

**结论**：A2 / A3b / A5.3 **全部 ALIGNED**（同一根因闭合）。

### 回归面复核 — 首轮 ALIGNED 项无回退

| 维度 | 复核命令 / 依据 | 结果 |
|---|---|---|
| consistency | `check-protocol-consistency.py --strict-errors-only` | **exit 0 / 0 ERROR / 402 WARNING**（与 round4 前一致，无新增） |
| batch3 回归 | `pytest test_agate_run.py test_events_ledger.py test_check_events.py -q` | **29 passed** |
| A6 门禁面 | `pytest .../test_protocol_alignment_review.py -k sg_6 -q` | **1 passed**（`agate-run.py` 仍不在门禁 glob） |
| A1/A3a/A4/A7/A8 | 修复仅改文档/注释，未改任何脚本逻辑（`check-events.py` 1 行 docstring diff） | 无回退 |

### [DESIGN_GAP] 复核（2 条，未受本轮修复影响）

| # | DESIGN_GAP | 判定 |
|---|---|---|
| ① | P2 §4.2/M10「修正 formatter 计数」无缺陷/落点/判据、P3 无覆盖（实现未做） | **DESIGN_GAP（交 P7）** —— 本轮修复未触及；建议 P2 删/细化该条 |
| ② | P2 §4.2 `agate-run <cmd-key|命令>` 但 schema `verify.commands` 无命名 key（实现按命令文本匹配 + 下标槽位） | **DESIGN_GAP（交 P7）** —— 本轮修复未触及 |

> `P4-implementation-batch3.md` 的 `[SCOPE+]` 已消解为「观察项（已就地处理）」（`check-events.py:14` 注释补 `cmd_run`），与 round5 修复一致。

### round 5 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1 / A2 / A3a / A3b / A4 / A5.1 / A5.2 / A5.3 / A6 / A7 / A8 | 通过，**可 commit**。 |
| **DESIGN_GAP（交 P7）** | 2 条（formatter 计数 / cmd-key）| P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`。 |

**round 5 结论：ALIGNED（可 commit）。**

---

## round 6 复审（batch4 增量）（2026-10-06）

> 复审范围：TAG0042 批 4（`batch4-gate-layer`，关卡层分级 + P8 交付收尾）的 agate 协议/脚本未 commit 改动（HEAD `68a796e`，batch3 已落）。
> 触发模式：SELF-GATE「变更触发模式」A1-A8。**本批重点 = A3b 反向传播**（P8 名称/语义改述）。
> 变更文件：`agate/rules/phases.yaml`、`agate/rules/schema/phases.schema.json`、`agate/scripts/check-gate.py::gate_p8`、`agate/phase-cards/P8-release.md`、`agate/WORKFLOW.md`、`agate/UPGRADING.md`、测试夹具（`test_check_gate.py`/`test_t41_platform_hygiene.py`/`test_v060_p8_cached.py`/`test_check_p8_delivery.py`）。

### 复审结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED**（P8 名称/语义改述未同步到叙事文档） |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **MISALIGNED** → 合计 **MISALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **MISALIGNED** → 合计 **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：misaligned**。MISALIGNED 共 3 项（A2 / A3b / A5.3），**同一根因**：P8 名称/语义由「发布准备」改「交付收尾」（BDD-15），但**名称/身份级叙事未反向传播**（见 A2/A3b）。核心变更面（gate_layer + gate_p8 delivery 校验 + schema + WORKFLOW + 卡片）语义自洽。6 条 `[DESIGN_GAP]`：①-⑤ 判 DESIGN_GAP（交 P7），**⑥ reclassify 为 MISALIGNED**。NEEDS_HUMAN_REVIEW 0 条。

### A1: 文档→脚本对齐 — ALIGNED

- **`gate_p8` delivery 校验 vs BDD-15 / P2 §4.3**：`check-gate.py:1447-1453` 在 `debt_check` 后新增 `if "delivery:" not in p8_text: return 1`——BDD-15「`delivery` 未声明时 gate 拦截（非 0），声明后放行」与 P2 §4.3「`gate_p8()` 校验 `delivery` 声明；未声明 → 非 0」**逐字一致**；既有 bump_type/debt_check/version/CHANGELOG/tag/roadmap 检查**全部保留**。
- **`gate_layer` vs BDD-14**：`phases.yaml` 新增顶层 `gate_layer`——`commit_types`（`code-only`/`docs-only`/`release` 三类不同关卡集合）+ `transitions.forward`/`retreat` + `pause.paused_from`（字面 `paused_from`）——满足 BDD-14「按提交类型选择对应关卡集合（转换表可查），不同类型走不同关卡，且转换表含 `paused_from`」。
- **`gate_pass_exit`/`next`/`retreat` 语义未变（回归）**：`git diff` 仅改 P8 `name`（发布准备→交付收尾）+ P8 `gates[]` 描述 + 追加 `gate_layer`；各 phase 的 `gate_pass_exit`/`next`/`retreat` **未触碰**（`test_gate_layer.py::_EXPECTED_GATE_PASS_EXIT` 回归基线绿）。
- **发版痕迹迁移 WARNING（BDD-21）**：`gate_p8:1520-1534` 在 version/CHANGELOG 变更存在且无 `agate.config.yaml` 时输出指向 `release.preset: semver-changelog-tag` 的 WARNING（不阻断）——与 P2 §4.3「缺失时按发版痕迹给 WARNING」一致。

**结论**：ALIGNED。

### A2: 脚本→文档对齐 — MISALIGNED

本批把 P8 的**名称/语义**从「发布准备」改为「交付收尾」（`phases.yaml:153 name: 交付收尾`，BDD-15「P8 语义为交付收尾（非发版）」）。仅同步了 3 处（`phases.yaml`、`WORKFLOW.md:327` 表行、`P8-release.md:1` 标题），但**其它权威文档的名称/身份级叙事仍写「发布准备」**，与权威名**直接矛盾**：

| # | 落点 | 现文（旧） | 判定 |
|---|------|-----------|------|
| 1 | `agate/state-machine.md:311` | 「P8 是**「发布准备」**，不是「发布」」 | **MISALIGNED** |
| 2 | `agate/state-machine.md:315` | 表行「发布准备 (READY)」 | **MISALIGNED** |
| 3 | `agate/dispatch-protocol.md:881` | P8→READY 行「发布准备完成（…）」 | **MISALIGNED** |
| 4 | `agate/WORKFLOW.md:256` | 「P8 发布准备：涉及发布的任务必做」（同文件 :327 已改「交付收尾」→ **文件内不一致**）| **MISALIGNED** |
| 5 | `agate/role-system.md:29` | 角色表「P4、P8 | 写代码、多包发布准备」 | **MISALIGNED** |
| 6 | `agate/assets/execution-roles/implementer.md:9` | 角色标题「# 实现工程师（P4 实现 / P8 发布准备）」 | **MISALIGNED** |

> **判据**：以上为 P8 的**名称/身份级**表述（读者据此得知「P8 = 发布准备」），与权威数据面 `phases.yaml name: 交付收尾` 及 BDD-15 基线**直接矛盾**——`state-machine.md:311` 尤甚（定义句「P8 是『发布准备』」）。

**结论**：MISALIGNED。
**建议**：将上述 6 处名称/身份级「发布准备」改述为「交付收尾」（与 `phases.yaml`/`WORKFLOW:327`/卡片标题同口径）。

> **描述活动级**残留（「执行发布准备步骤」等，P8 仍做发版准备、措辞可对齐）判 DESIGN_GAP/观察：`state-machine.md:167`/`:438`、`implementer.md:11`、`P8-release.md:9`/`:29`/`:47`、`LIMITATIONS.md:119`、`WORKFLOW.md:166`。

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b MISALIGNED（合计 MISALIGNED）

#### A3a（连锁：已知衍生改动）— ALIGNED

- **schema 同步**：`phases.yaml` 新增顶层 `gate_layer` 在 `additionalProperties:false` 下须同步 `phases.schema.json`——已扩展；`check-yaml-schema.py` → **`SCHEMA-phases: OK`**（S-5 覆盖）。
- **WORKFLOW 名称同步**：`check-structure-consistency.py` → **S1-phases OK**（S-1 YAML↔WORKFLOW 名称一致强制，已同步 `WORKFLOW.md:327`）。
- **测试夹具**：`_P8_COMPLIANT`/`_P8_RELEASE`/t41 夹具补 `delivery: package-release`；`test_check_p8_delivery._p8_repo` 补 `dirs_exist_ok=True`（夹具缺陷修复，未改断言）。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— MISALIGNED

| 应被影响候选 | 影响到了没 | 判定 |
|---|---|---|
| `agate/state-machine.md`（P8 定义/表/转移）| **部分** —— :311/:315 名称级未改；:167/:438 活动级未改 | **MISALIGNED**（:311/:315）|
| `agate/dispatch-protocol.md`（P8→READY 门槛表）| **否** —— :881「发布准备完成」未改 | **MISALIGNED** |
| `agate/WORKFLOW.md` | **部分** —— :327 已改；:256「P8 发布准备」未改 | **MISALIGNED**（:256）|
| `agate/role-system.md`（P4/P8 角色表）| **否** —— :29「多包发布准备」未改 | **MISALIGNED** |
| `agate/assets/execution-roles/implementer.md`（P8 角色）| **部分** —— :9 标题未改；:11 描述未改 | **MISALIGNED**（:9）|
| `agate/phase-cards/P8-release.md` | **部分** —— :1 标题已改；:9/:29/:47 活动级未改 | DESIGN_GAP/观察 |
| `agate/LIMITATIONS.md` | **否** —— :119「P8 发布准备」未改（活动级）| DESIGN_GAP/观察 |
| `agate/rules/phases.yaml` / `phases.schema.json` / `WORKFLOW:327` / `P8-release.md:1` | **已改** | ALIGNED |

**结论**：MISALIGNED（6 处名称/身份级叙事反向传播缺失）。**建议**：同 A2。

### A4: 测试覆盖 — ALIGNED

- **批 4 相关测试全绿（实跑）**：`pytest test_gate_layer.py test_check_p8_delivery.py test_check_gate.py -q` → **227 passed**（与 `P4-implementation-batch4.md:103` 自报吻合）。
- **相邻回归（自报，未重跑）**：`test_check_structure_consistency` / `test_check_yaml_schema` / `test_t41_platform_hygiene` / `test_v060_p8_cached` / `test_check_protocol_consistency` / `test_agate_debt_check` → 101 passed。
- **边界覆盖**：BDD-14（提交类型→关卡集合 + `paused_from`）、BDD-15（`delivery` 缺失拦截 / 声明放行）、BDD-21（preset 等价物 + 发版痕迹 WARNING）均有断言。
- **用例总数**：`count-tests.sh` → **2689**（未漂移）。
- **已知仓库面（非本批）**：`test_agate_scripts_encoding::test_bdd_5`（batch3 `test_agate_run.py:282/284` 缺 `encoding`）、`test_setup_agate_dir::test_bdd_43`（本机 `opencode debug agent` 环境差异）——二者非 batch4 引入。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED（待 P8）/ A5.3 MISALIGNED

- **A5.1 破坏性变更 / 向后兼容 — ALIGNED**：`gate_layer` 为纯新增数据面（不改 `gate_pass_exit`/`next`/`retreat`）；`delivery` 新增为 P8 产出必填（UPGRADING 明示「升级后补一行 `delivery:`，否则 P8 gate 拦」）；发版逻辑**本批未删除**（只提供等价物 + WARNING，符合 P2 §4.3 顺序）。`UPGRADING.md` 批 4 小节自洽（preset 迁移 + 截止版本 v0.80.0，与批 2 同版本）。
- **A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）**：`check-changelog.py` 仅 P8 触发；`CHANGELOG.md` 待 P8 统一补（同前几批判据）。
- **A5.3 文档传播 — MISALIGNED**：除代码改动外，应被影响的文档 = A3b 的 6 处名称/身份级叙事（`state-machine.md:311/:315`、`dispatch-protocol.md:881`、`WORKFLOW.md:256`、`role-system.md:29`、`implementer.md:9`）——均**未同步**。`phases.yaml`/`phases.schema.json`/`WORKFLOW:327`/`P8-release.md:1`/`UPGRADING.md` 已同步。

**结论**：合计 MISALIGNED（A5.1/A5.2 ALIGNED；A5.3 与 A3b 同 6 处）。

### A6: 锚点表覆盖 — ALIGNED

- **`phases.schema.json` 扩展被覆盖**：`check-yaml-schema.py`（S-5）校验 `rules/phases.yaml` 对 `phases.schema.json`——新增 `gate_layer` 已纳入，**`SCHEMA-phases: OK`**。
- **`gate_layer` 新字段登记面**：属 `rules/*.yaml` 数据面（schema 覆盖），非 `check-*.py` 新增/改名 → CHECK 9 锚点表**无新增义务**。consistency `CHECK 9 ✅ PASS`，无 `CHECK9-coverage`。
- **无需更新锚点表**。

**结论**：ALIGNED。

### A7: 设计原则一致性 — ALIGNED

- **ADR-014（判据单一权威源）**：P8 名称在 `phases.yaml` 单源 + S-1 强制 WORKFLOW 同步；`gate_layer` 转换表把各 phase 的 `next`/`retreat` 集中为可查视图（不新增第二判据）。**一致**（但见 A2——叙事文档未跟随单源，属传播缺口而非判据双源）。
- **ADR-002（可判定性）**：`delivery` 存在性、`gate_layer` 结构、发版痕迹 WARNING 均可机械判定。**一致**。
- **ADR-004（安全网分层）/ ADR-015（让错误可见）**：发版痕迹存在但无声明 → 显眼 WARNING（不静默失去保护）。**一致**。
- **是否存在未记录的新架构决策？** 「关卡层按提交类型分级 + P8 交付收尾」是 ADR-002/ADR-004 在新关卡层的应用，**不引入新架构决策** → 无需新增 ADR。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| `gate_p8` 缺 `delivery` → exit 1（BDD-15）| 读 `check-gate.py:1447-1453`；`pytest test_check_p8_delivery.py` | ✅ 成立 |
| `gate_layer` 含 `paused_from`（BDD-14）| `grep -n paused_from agate/rules/phases.yaml`；`pytest test_gate_layer.py` | ✅ 成立 |
| `gate_pass_exit`/`next`/`retreat` 未变（回归）| `git diff -- agate/rules/phases.yaml`（未触碰）；`test_gate_layer.py::_EXPECTED_GATE_PASS_EXIT` | ✅ 成立 |
| batch4 `227 passed`（P4-impl:103）| `pytest test_gate_layer.py test_check_p8_delivery.py test_check_gate.py -q` → 227 passed | ✅ 成立 |
| consistency `0 ERROR / 404 WARNING`（P4-impl:105）| `check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 404 WARNING | ✅ 0 ERROR 成立 |
| count-tests `2689`（P4-impl:107）| `count-tests.sh` → 2689 | ✅ 成立 |
| ruff `All checks passed`（P4-impl:108）| `~/.venvs/agate-dev/bin/ruff check agate/scripts/` | ✅ 成立 |
| structure `S1-S6/S0 全 OK`（P4-impl:106）| `check-structure-consistency.py` → S1-S6/S0 OK | ✅ 成立 |
| 平台扫描 0 命中（P4-impl:109）| `check-platform-assumptions.py <改动文件>` → exit 0 | ✅ 成立 |

无「无法给出命令」的无据声称。

### [DESIGN_GAP] 逐条判定（6 条）

| # | DESIGN_GAP | 判定 | 依据 |
|---|---|---|---|
| ① | 提交类型→关卡集合的具体成员与转换表矩体未定（P4 落定 code-only 全链 / docs-only [P0,P1,P2,P7,P8] / release [P7,P8]）| **DESIGN_GAP（交 P7）** | P2 §11 明确预留「批 4 的关卡层转换表矩体…P4 implementer 应标 [DESIGN_GAP]，P7 逐条审查」；P4 已落定，非文档-脚本矛盾 |
| ② | `phases.schema.json` 不在 §6.1b batch4 output 列，但须同步 | **DESIGN_GAP（交 P7）** | 必要同步（additionalProperties:false）；已扩展，`check-yaml-schema` OK；属 output 清单遗漏，交 P7 核对 |
| ③ | `WORKFLOW.md` 不在 §6.1b batch4 output 列，但 S-1 强制同步 | **DESIGN_GAP（交 P7）** | 必要同步（S-1 强制）；已同步，S-1 OK；交 P7 核对 |
| ④ | `delivery` 合法取值集合设计未定（只查留痕存在）| **DESIGN_GAP（交 P7）** | BDD-15/P2 §4.3 只要求「未声明→拦截」；卡片明示只查留痕；取值集收紧属设计决策，交 P7 |
| ⑤ | 发版逻辑删除时机/顺序（本批未删除）| **DESIGN_GAP（交 P7）** | BDD-21 的 Then 已满足（等价物 + WARNING + UPGRADING 截止版本）；P2 §4.3 明确「先提供等价物 → 再删」；删除属后续批次，交 P7 |
| ⑥ | P8 叙事面（state-machine.md/dispatch-protocol.md/role-system.md/implementer.md）仍写「发布准备」| **MISALIGNED（非 DESIGN_GAP）** | 与权威名 `phases.yaml name: 交付收尾` 及 BDD-15「P8 语义为交付收尾」**直接矛盾**；任务在 P4、无 P7 `REVIEWED-ACCEPTED` → 按角色原则 6 判 MISALIGNED（同 A2/A3b/A5.3）|

**判定合计**：5 条 **DESIGN_GAP（交 P7）**；**1 条（⑥）reclassify 为 MISALIGNED**（与 A2/A3b/A5.3 同根因）。按角色原则 6——①-⑤ 不对应「`agate/` 协议文档↔脚本不一致」（① 是 P2 预留设计未定，②③ 是 output 清单遗漏，④ 是取值集未定，⑤ 是删除时机），故判 DESIGN_GAP；⑥ 是真实名称/语义矛盾，不豁免。

### round 6 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **MISALIGNED** | A2 / A3b / A5.3（同一根因：P8 名称/身份级「发布准备」未同步——`state-machine.md:311`/`:315`、`dispatch-protocol.md:881`、`WORKFLOW.md:256`、`role-system.md:29`、`implementer.md:9`）+ DESIGN_GAP ⑥ | **必须修复**：6 处名称/身份级改述为「交付收尾」；修完重审（round 7）。 |
| **ALIGNED** | A1 / A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | 通过。 |
| **DESIGN_GAP（交 P7）** | ①-⑤（见上表）| P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`。 |
| **观察（非阻塞）** | 活动级「发布准备」残留（state-machine:167/:438、implementer.md:11、P8-release.md:9/:29/:47、LIMITATIONS:119、WORKFLOW:166）| 建议随修复一并对齐措辞。 |

**不可 commit**（存在未闭合 MISALIGNED）。修复后建议对本报告做同任务复核轮（round 7），追加 `round7_conclusion`。

**round 6 结论：MISALIGNED（须同步 P8 名称/身份级叙事 6 处）。**

---

## round 7 复审（batch4 修复闭合）（2026-10-06）

> 复审范围：round6 判 MISALIGNED 的 3 项（A2 / A3b / A5.3，同一根因 = P8 名称/语义「发布准备」→「交付收尾」未反向传播）修复是否闭合，以及修复是否引入新不一致（回归面）。HEAD `68a796e`（batch3 已落），batch4 改动未 commit。
> 修复文件：`agate/state-machine.md`、`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`、`agate/role-system.md`、`agate/assets/execution-roles/implementer.md`、`agate/LIMITATIONS.md`、`agate/phase-cards/P8-release.md`（叙事改述）+ `agate/tests/unit/test_agate_run.py`（编码守卫字符串字面量）。

### 复审结论汇总

| # | 审查项 | round 6 | round 7 |
|---|--------|---------|---------|
| A1 | 文档→脚本对齐 | ALIGNED | **ALIGNED（无回退）** |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED（闭合）** |
| A3 | 一致性连锁 + 反向传播 | A3a ALIGNED / A3b MISALIGNED | A3a **ALIGNED** / A3b **ALIGNED（闭合）** |
| A4 | 测试覆盖 | ALIGNED | **ALIGNED（无回退）** |
| A5 | 下游影响 + 文档传播 | A5.1/A5.2 ALIGNED / A5.3 MISALIGNED | A5.1/A5.2 **ALIGNED** / A5.3 **ALIGNED（闭合）** |
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED（无回退）** |
| A7 | 设计原则一致性 | ALIGNED | **ALIGNED（无回退）** |
| A8 | 声称-命令绑定 | ALIGNED | **ALIGNED（无回退）** |

**总结论：aligned**。round6 的 3 项 MISALIGNED 已全部闭合，无新增不一致，无回退。解除 commit 阻塞。

### A2 / A3b / A5.3 逐项复核 — ALIGNED（闭合）

**名称/身份级 6 处**（`git diff` 逐处核对）：

| 落点 | 修复后 | 判定 |
|---|---|---|
| `agate/state-machine.md:311` | 「P8 是**「交付收尾」**，不是「发布」」 | 闭合 |
| `agate/state-machine.md:315` | 表行「交付收尾 (READY)」 | 闭合 |
| `agate/dispatch-protocol.md:881` | P8→READY「交付收尾完成（…）」 | 闭合 |
| `agate/WORKFLOW.md:256` | 「P8 交付收尾：涉及发布的任务必做」（与 :327 一致）| 闭合 |
| `agate/role-system.md:29` | 「写代码、多包交付收尾」 | 闭合 |
| `agate/assets/execution-roles/implementer.md:9` | 「# 实现工程师（P4 实现 / P8 交付收尾）」 | 闭合 |

**活动级残留**（一并对齐）：`state-machine.md:167`（「执行交付收尾」）、`:438`（「交付收尾，少轮次」）、`implementer.md:11`（「P8 … 做交付收尾」）、`P8-release.md:9/:29/:47`、`LIMITATIONS.md:119`（「P8 交付收尾」）、`WORKFLOW.md:166`（「交付收尾」）——均已改。

- **残留复核**：`grep -rn "发布准备" agate/state-machine.md agate/dispatch-protocol.md agate/WORKFLOW.md agate/role-system.md agate/assets/execution-roles/implementer.md` → **0 命中**。全 `agate/`（非 tests）仅剩 `UPGRADING.md:313`（批 4 节历史注「（原「发布准备」）」）+ `UPGRADING.md:1269`（冻结历史版本节）——均为**合法历史注**。
- **一致性**：`交付收尾` 现覆盖 9 文件（phases.yaml / dispatch-protocol / WORKFLOW / implementer / UPGRADING / role-system / P8-release / state-machine / LIMITATIONS），与权威 `phases.yaml name: 交付收尾` + BDD-15 同口径。

**结论**：A2 / A3b / A5.3 **全部 ALIGNED**（同一根因闭合）。

### 回归面复核 — 首轮 ALIGNED 项无回退

| 维度 | 复核命令 / 依据 | 结果 |
|---|---|---|
| consistency | `check-protocol-consistency.py --strict-errors-only` | **exit 0 / 0 ERROR / 404 WARNING**（与 round6 一致，无新增） |
| structure | `check-structure-consistency.py` | **S1-S6/S0 全 OK**（S-1 YAML↔WORKFLOW 名称一致） |
| batch4 回归 | `pytest test_gate_layer.py test_check_p8_delivery.py test_check_gate.py test_agate_run.py -q` | **237 passed** |
| A1/A3a/A6 | 修复仅动叙事文档 + `test_agate_run.py` 字符串字面量（`"with open" + "("`，编码守卫规避）——未改任何协议逻辑/数据面 | 无回退 |

> **观察（非阻塞）**：`test_agate_run.py:282/284` 的编码守卫误判修复属 batch3 测试源修正（非本批协议面），已随本轮落地。

### [DESIGN_GAP] 复核（5 条，未受本轮修复影响）

| # | DESIGN_GAP | 判定 |
|---|---|---|
| ① | 提交类型→关卡集合的具体成员与转换表矩体未定（P2 §11 预留）| **DESIGN_GAP（交 P7）** |
| ② | `phases.schema.json` 不在 §6.1b output 列但须同步（已同步）| **DESIGN_GAP（交 P7）** |
| ③ | `WORKFLOW.md` 不在 §6.1b output 列但 S-1 强制（已同步）| **DESIGN_GAP（交 P7）** |
| ④ | `delivery` 合法取值集合设计未定（只查留痕存在）| **DESIGN_GAP（交 P7）** |
| ⑤ | 发版逻辑删除时机/顺序（本批未删除）| **DESIGN_GAP（交 P7）** |
| ⑥ | P8 叙事面未同步 | **本轮修复即其闭合 → 转 ALIGNED** |

### round 7 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1 / A2 / A3a / A3b / A4 / A5.1 / A5.2 / A5.3 / A6 / A7 / A8 | 通过，**可 commit**。 |
| **DESIGN_GAP（交 P7）** | ①-⑤（见上表）| P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`。 |

**round 7 结论：ALIGNED（可 commit）。**

---

## round 8 复审（batch5 增量）（2026-10-06）

> 复审范围：TAG0042 批 5（`batch5-ci-doctor`，CI 与诊断）的 agate 协议/脚本未 commit 改动（HEAD `fb56964`，batch4 已落）。
> 触发模式：SELF-GATE「变更触发模式」A1-A8。**本批重点 = A3/A5 反向传播**（退役 `ci-gate-backstop`）。
> 变更文件：新增 `agate/scripts/agate-ci-verify.py`、`agate/scripts/agate-doctor.py`；删除 `agate/scripts/ci-gate-backstop.py` + `agate/tests/unit/test_ci_gate_backstop.py`；改 `.github/workflows/protocol-tests.yml`、`agate/scripts/check-protocol-consistency.py`、`agate/scripts/agate-summary.py`、`agate/scripts/check-gate.py`（注释）、`agate/scripts/README.md`、6 协议文档 + `assets/formatters/README.md`、`tests/README.md`、4 既有测试。

### 复审结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **ALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：aligned**。MISALIGNED 0 条、NEEDS_HUMAN_REVIEW 0 条。5 条 `[DESIGN_GAP]` 全部判 **DESIGN_GAP（交 P7）**。退役脚本的反向传播在 CHECK10 扫描面 **0 ERROR**（CHECK10-scriptref 未新增）。

### A1: 文档→脚本对齐 — ALIGNED

- **`agate-ci-verify.py` vs BDD-16 / P2 §4.4**：`_run_gate(phase, task_dir)` 子进程调 `check-gate.py PHASE TASK_DIR`——**实际重跑** gate 判定（BDD-16「不再是永远 SKIP 却显示绿」）；每个「跳过」面经 `_skip()` 打印 `SKIP: <原因>` + 「本次**未实际执行**」（BDD-16「跳过与通过在输出上可区分」）。不读任何 CI 平台环境变量（P2 §4.4 平台无关）。
- **`agate-doctor.py` vs BDD-17 / P2 §4.4**：四维诊断（声明文件 / git hook / 版本解析 / 账本完整性）+ 异常项可执行修复指引；`main()` **恒 `return 0`**（BDD-17「成功退出码固定」）。声明维度经 `agate_common.read_project_config`（唯一读取函数，不另写 YAML 解析）。
- **workflow（M15）**：`.github/workflows/protocol-tests.yml` 的 `gate-backstop` job run step 改调 `agate-ci-verify.py`（`test_bdd_16_ci_verify_workflow_invokes_new_script` 断言新脚本在、退役名不在）；注解/summary 判据由 `BACKSTOP-INACTIVE` 改 `SKIP:`。

**结论**：ALIGNED。

### A2: 脚本→文档对齐 — ALIGNED

| 脚本行为 | 文档对应 | 判定 |
|---|---|---|
| `agate-ci-verify` 实际重跑 + 显式 SKIP | `scripts/README.md`（CI 兜底行）、`WORKFLOW.md:368`（CI 兜底段）、`platform-notes.md`（CI 兜底说明）、`state-machine.md:154` | ALIGNED |
| `agate-doctor` 四维诊断 + rc 固定 | `scripts/README.md`（新增「诊断」节）、`tests/README.md`（映射行） | ALIGNED |
| 删除 `ci-gate-backstop.py` | 6 协议文档 + `formatters/README.md` + `retrospective-template.md` 引用改述为「CI 兜底」/`agate-ci-verify.py` | ALIGNED |
| 退役名拦截 | `check-protocol-consistency.py` 注释（`SCRIPT_REF_RE` 保留退役名） | ALIGNED |

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b ALIGNED

#### A3a（连锁：已知衍生改动）— ALIGNED

- **锚点表 / extras / callers**：`check-protocol-consistency.py` 移除 `ci-gate-backstop.py` 锚点条目；`uncovered_gate_scripts()` 的 `extras` 去掉该名；`check-judge-verdict` / `check-events` 锚点的 `callers` 去掉该名——四处同步。
- **`agate-summary.py`**：防护清单项 `ci-gate-backstop.py` → `agate-ci-verify.py`。
- **`check-gate.py`**：头注释去掉该名（provenance 仅 `pre-commit-gate.sh` 调用）。
- **测试同步**：删除 `test_ci_gate_backstop.py`（测退役对象）+ 移除 `test_check_protocol_consistency.py` 的退役锚点断言；`test_check_gate.py` 的 `test_tag0035_bdd_2_*` 改测 `agate-ci-verify.py`（同语义）；`test_mvwu_protocol_docs.py` 目标脚本元组同步。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— ALIGNED

**退役名全仓 grep**（`ci-gate-backstop`）分类：

| 面 | 命中 | 判定 |
|---|---|---|
| CHECK10 扫描面 · `agate/UPGRADING.md:943` | 裸名 `ci-gate-backstop`（**无 `.py`**，`SCRIPT_REF_RE` 不匹配 → 不产生 ERROR；历史「不动面」注） | ALIGNED |
| CHECK10 扫描面 · `CHANGELOG.md`（多处） | 叙事文件**降级为聚合 WARNING**（`CHECK10-scriptref 1`，与改动前**同**） | ALIGNED |
| CHECK10 扫描面 · `assets/` `phase-cards/` `rules/` | **0 命中** | ALIGNED |
| workflow / `agate-summary.py` / `scripts/README.md` / 6 协议文档 | 已同步（0 残留） | ALIGNED |
| 扫描面外 · `docs/guides/project-map.md:59` | 活文档仍写 `ci-gate-backstop.py`（`docs/` 非协议面，CHECK10 按设计不扫） | **观察（非阻塞）** |
| 扫描面外 · `docs/reviews/*` `docs/design-notes/*` `archived/*` | 历史记录（按设计不改） | ALIGNED |
| 扫描面外 · `test_agate_ci_verify.py` 注释 | **刻意**引用退役名（断言退役完成） | ALIGNED |

**结论**：A3b ALIGNED（协议文档面 0 残留；`CHECK10-scriptref` 未新增 ERROR/WARNING）。

### A4: 测试覆盖 — ALIGNED

- **批 5 相关测试全绿（实跑）**：`pytest test_agate_ci_verify.py test_agate_doctor.py -q` → **14 passed**（与 `P4-implementation-batch5.md:76` 自报吻合）。
- **相邻回归（实跑）**：`test_check_gate.py` + `test_check_protocol_consistency.py` + `test_mvwu_protocol_docs.py` + `test_protocol_alignment_review.py`（含 SG.6）→ **334 passed**；`test_t43_check_registration_surface.py` + `test_doc_sweep.py` + `test_agate_scripts_encoding.py` → **27 passed**。
- **边界覆盖**：BDD-16（重跑 gate + 报告失败 / 显式 SKIP+原因 / 源码含 `check-gate.py` / workflow 改调 / 协议引用同步）、BDD-17（脚本存在 / 四维 / 修复指引 / 未接入 / 已接入 / rc 固定）均有断言。
- **用例总数**：`count-tests.sh` → **2671**（较 batch4 的 2689 减 18 = 删退役测试 17 + 删退役锚点测试 1；新增 BDD-16/17 的 14 例 P3 已计入）。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED（待 P8）/ A5.3 ALIGNED

- **A5.1 破坏性变更 / 向后兼容 — ALIGNED**：退役 `ci-gate-backstop.py` 属 CI 侧实现替换（对使用者项目无 API 破坏）；`agate-ci-verify.py` 保持「push 后重跑 gate 判定」语义，且修复了旧脚本的「假绿」（X3）。`UPGRADING.md` 待 P8 统一记录（见 A5.2）。
- **A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）**：`check-changelog.py` 仅 P8 触发；`CHANGELOG.md` 待 P8 统一补（同前几批判据）。
- **A5.3 文档传播 — ALIGNED**：应传播面（6 协议文档 + `formatters/README` + `retrospective-template` + `scripts/README` + `tests/README` + `agate-summary` + workflow + 锚点表）均已同步。
  - **观察（非阻塞）**：`docs/guides/project-map.md:59`（活文档，整仓导航地图）仍写 `ci-gate-backstop.py`——`docs/` 按设计不在 CHECK10/协议面，建议后续批次或收尾时更新。

**结论**：合计 ALIGNED。

### A6: 锚点表覆盖 — ALIGNED

- **`CHECK10` 退役名拦截语义自洽**：`SCRIPT_REF_RE` **保留** `ci-gate-backstop\.py`——协议文档回引 → ERROR；`CHANGELOG.md` 等叙事文件降级为聚合 WARNING（`CHECK10-scriptref 1`，未新增）。**实测** consistency → **0 ERROR**。
- **新脚本登记面**：`agate-ci-verify.py` / `agate-doctor.py` 是 `agate-*.py` → **不在** `uncovered_gate_scripts()` 的 glob（`check-*.py` + `pre-commit-gate.{sh,py}`）→ 不触发 CHECK9-coverage / SG.6。**实测** `test_protocol_alignment_review.py`（含 SG.6）→ passed；`CHECK 9 ✅ PASS`。README 索引行已补（非门禁，约定）。
- **无需更新锚点表**（本批删除的锚点条目已移除，无新增 `check-*.py`）。

**结论**：ALIGNED。

### A7: 设计原则一致性 — ALIGNED

- **ADR-015（实质/非实质——让错误可见）**：`agate-ci-verify` 每个「跳过」面显式 `SKIP:` + 原因，workflow 再抬为 GitHub 注解 + job summary——消除旧脚本「永远 SKIP 却显示绿」的假绿。**一致**。
- **ADR-002（可判定性）**：**实际重跑** `check-gate.py` 判定 + `.gate-result.json` 一致性比对，均可机械判定。**一致**。
- **ADR-004（安全网分层）**：CI 兜底（防 `--no-verify`）保留，替换实现而非移除防线。**一致**。
- **是否存在未记录的新架构决策？** 「CI 兜底实现替换 + 诊断工具」是 ADR-015/002/004 的应用，**不引入新架构决策** → 无需新增 ADR。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| batch5 红→绿 `14 passed`（P4-impl:76）| `pytest test_agate_ci_verify.py test_agate_doctor.py -q` → 14 passed | ✅ 成立 |
| consistency `0 ERROR`（P4-impl:80）| `check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 406 WARNING | ✅ 成立（CHECK10-scriptref 1 未新增） |
| structure `S1-S6/S0 全 OK`（P4-impl:81）| `check-structure-consistency.py` → 全 OK | ✅ 成立 |
| count-tests `2671`（P4-impl:82）| `count-tests.sh` → 2671 | ✅ 成立 |
| ruff `All checks passed`（P4-impl:83）| `~/.venvs/agate-dev/bin/ruff check agate/scripts/` | ✅ 成立 |
| 平台扫描新增脚本 0 命中（P4-impl:84）| `check-platform-assumptions.py agate-ci-verify.py agate-doctor.py` → exit 0 | ✅ 成立 |
| `agate-ci-verify` 实际重跑 gate（BDD-16）| 读 `agate-ci-verify.py:41-50`（子进程调 check-gate.py）；`test_bdd_16_ci_verify_source_reruns_gate` | ✅ 成立 |
| `agate-doctor` rc 固定（BDD-17）| 读 `agate-doctor.py:166`（`return 0`）；`test_bdd_17_doctor_success_exit_code_fixed` | ✅ 成立 |

无「无法给出命令」的无据声称。

### [DESIGN_GAP] 逐条判定（5 条）

| # | DESIGN_GAP | 判定 | 依据 |
|---|---|---|---|
| ① | `agate-ci-verify` 调用接口 P2 §4.4 未固化（P4 取无参数 + cwd 定位；多任务歧义 → SKIP）| **DESIGN_GAP（交 P7）** | P2 §4.4 未指定定位接口；BDD-16「无适用场景时显式声明跳过+原因」已满足；属设计未定面 |
| ② | `agate-doctor` 退出码语义（P4 解释「成功=诊断正常完成」⇒ rc 恒 0）| **DESIGN_GAP（交 P7）** | P2 §4.4 仅写「退出码固定」；与 TC-B17-08 一致；若意图为「发现异常即非 0」须改 P3 契约，交 P7 |
| ③ | 未移植退役 backstop 的独立 P3 `check-tdd-red` / P6 provenance CI 层重跑 | **DESIGN_GAP（交 P7）** | BDD-16 只要求「实际重跑 gate 判定」；P6.5 judge/events 已由 `check-gate.py P6.5` 覆盖；是否补回交 P7 |
| ④ | `agate/assets/formatters/README.md` 属 CHECK10 面但派发清单未列（P4 已同步）| **DESIGN_GAP（交 P7）** | 属**必要同步**（否则新增 CHECK10 ERROR）；非新增需求；交 P7 核对 |
| ⑤ | workflow job 名保留 `gate-backstop`（M15 只要求改调用脚本）| **DESIGN_GAP（交 P7）** | P2 M15 未指定改名；保留 job 名不影响语义；是否改名交 P7 |

**判定合计**：5 条**全部 DESIGN_GAP（交 P7）**；**MISALIGNED 0 条**。按角色原则 6——5 条均不对应「`agate/` 协议文档↔脚本不一致」（①②③⑤ 是设计未定/选择，④ 是必要同步），故判 DESIGN_GAP。

### round 8 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1 / A2 / A3a / A3b / A4 / A5.1 / A5.2 / A5.3 / A6 / A7 / A8 | 通过，**可 commit**。 |
| **DESIGN_GAP（交 P7）** | ①-⑤（见上表）| P7 逐条裁决并转抄 `DESIGN_GAP_REVIEWED`。 |
| **观察（非阻塞）** | `docs/guides/project-map.md:59` 活文档仍写退役名（非协议面）；`agate-doctor` 硬编码 `.git/hooks`（本仓未设 `core.hooksPath` → 实测一致）| 建议后续更新 project-map.md。 |

**round 8 结论：ALIGNED（可 commit）。**
