---
phase: P4
task_id: TAG0035
parent: P4-implementation.md
trace_id: TAG0035-P4-align-20260916
agent: protocol-alignment-review
type: review
created: 2026-09-16
status: approved
review_date: 2026-09-16
reviewer: protocol-alignment-review
change_summary: gate/check 脚本 4 处静默通过/静默失效改 fail-closed（未知阶段 exit2→1、三处数字阶段假设判空、gate_p4 跨commit/回退放宽、judge 黑白名单路径豁免）+ 2 处文档同步
files_changed: [agate/scripts/check-gate.py, agate/scripts/check-judge-verdict.py, agate/scripts/check-state-transition.py, agate/scripts/pre-commit-gate.py, agate/dispatch-protocol.md, agate/phase-cards/P6-acceptance.md, agate/tests/unit/test_check_gate.py]
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |

## 逐项审查

### A1: 文档→脚本对齐

**dispatch-protocol.md:404**（新增措辞）：
> 角色定义文件路径（`execution-roles`、`review-roles` 目录前缀）不受此白名单限制，任意角色文件路径均视为合法引用。

**check-judge-verdict.py:190,219**（实现）：
```python
_ROLE_DIR_RE = re.compile(r"(?:^|/)(?:execution-roles|review-roles)/")
...
if _ROLE_DIR_RE.search(tok):
    return True
```
文档措辞"目录前缀""任意角色文件路径"与正则 `(?:^|/)(?:execution-roles|review-roles)/`（要求路径段前有 `/` 或位于开头，段后跟 `/`）语义一致：只豁免真正落在这两个目录下的路径，不会豁免裸文件名（如直接写 `analyst.md` 不含目录段）。已用 `test_tag0035_bdd_12_whitelist_role_definition_file_path` 验证 `agate/assets/execution-roles/analyst.md` / `agate/assets/review-roles/plan-eng-review.md` 两个真实路径全流程 exit 0。**结论：ALIGNED**。

**P6-acceptance.md:24**（指针式引用）：
> …见 dispatch-protocol.md「Judge 信息隔离」节…含角色定义文件路径豁免

不重复枚举细节，权威源在 dispatch-protocol.md，卡片只做指针，符合 P2-design.md 风险表"双源同步"缓解措施（以 dispatch-protocol.md 为权威源，P6 卡指针式引用）。**结论：ALIGNED**。

### A2: 脚本→文档对齐

**check-gate.py:1516-1519**（实现）：
```python
func = handlers.get(phase)
if func is None:
    sys.stderr.write(f"未知阶段: {phase}\n")
    sys.exit(1)
```
搜索 `agate/state-machine.md`/`agate/WORKFLOW.md`/`agate/dispatch-protocol.md` 全文，均未出现过"未知阶段 exit 2"这一具体表述——三份文档现有的 `exit 2` 描述全部锚定在**已知阶段**各自的通过码语义上（如 state-machine.md:139 `P6 exit 2`、WORKFLOW.md:321 `P3 | ... exit 2`、dispatch-protocol.md:877/879 `P6→P7`/`P8→READY` 的 exit 2），没有任何一处文档描述过"未匹配到 handlers 的未知阶段名"这一分支的退出码值。即该分支此前是**未被任何协议文档承诺过的隐式行为**，本次修复不产生"脚本改了、文档未同步"的落差。**结论：ALIGNED（无需文档同步，因原本无对应文档声明）**。

**check-state-transition.py `phase_num()`**：docstring 已同步更新为"提取首个数字序列；无法解析回退 None"（原为"回退 0"），与实现严格一致。`agate/state-machine.md` 中提及"回退跳变检测""诊断基于 phase 编号差值"（state-machine.md:386-390）等表述未对 `phase_num()` 返回值类型做过声明，本次改动不影响该文档表述的正确性。**结论：ALIGNED**。

### A3: 一致性连锁 + 反向传播

**A3a（连锁）**：4 个子批分别落在 `check-gate.py`（子批A/B/C 共享）/`check-state-transition.py`/`pre-commit-gate.py`/`check-judge-verdict.py`，均已在同一 diff 中处理；`test_check_gate.py` 1 处存量断言矛盾（`test_other_unknown_phase_exit_2`）已同步改名改值；`dispatch-protocol.md`+`P6-acceptance.md` 两处文档同步已完成。连锁范围内的文件全部已处理。

**A3b（反向传播，逐一核查 dispatch-context 第二步点名的 4 个方向）**：

1. **`agate/state-machine.md` 是否描述 `check-state-transition.py` 的 `phase_num` 语义（0 vs None）**：grep 全文未发现描述 `phase_num` 返回值类型或"0"作为哨兵值语义的表述，state-machine.md:386-390 的"回退跳变检测"描述的是差值判定逻辑（"current_phase_num - next_phase_num >= 2"），不涉及 `phase_num()` 内部无法解析时的返回值约定。**无需同步**。
2. **`agate/WORKFLOW.md` 是否提及"未知阶段 exit 2"需同步为 exit 1**：grep 全文 `WORKFLOW.md` 的全部 `exit 2` 出现处（321/324/327 行）均是已知阶段（P3/P6/P8）各自的通过语义，无"未知阶段"表述。**无需同步**。
3. **`agate/rules/dispatch.yaml`/`agate/rules/phases.yaml` 是否依赖 `check-gate.py` 具体退出码数值声明**：`phases.yaml:13-19` 的 `gate_pass_exit` 注释详细声明了 P0-P8/P6.5 **各已知阶段**的通过码（2 或 0），语义锚定在 `gate_p0`~`gate_p8`/`gate_p65` 各函数的既有 `return` 值上（如 `p4 L990 return 0`），与本次改动的"未匹配 handlers 分支"完全无关（该分支不对应 `phases.yaml` 里任何一个已声明的 phase id）。`dispatch.yaml` 只按 phase 名调用 `check-gate.py`，未硬编码具体退出码数值。**均无需同步**。
4. **P0-brief.md 声明的 out-of-scope（不做 phases.yaml 语义重构、不做 handlers 声明式化）是否被意外触碰**：`git diff` 确认未改动 `agate/rules/phases.yaml` 任何字节，`check-gate.py` 的 `handlers` 字典本身（键值对结构）未改，只改了 `handlers.get(phase) is None` 分支内部的退出码数值——**未触碰 out-of-scope 边界**。

补充核查（本审查主动扩展，未在 dispatch-context 列出但属同类风险）：`agate/assets/execution-roles/{implementer,architect,verifier}.md` 全文 grep "exit 2"/"exit(2)"/"未知阶段"/"phase_num" 均无命中（verifier.md:137 的 "exit 2" 是 `check-p6-evidence.py` 截图像素方差 WARNING，与本次改动脚本无关）。`CHANGELOG.md` grep "TAG0035" 无命中——**未记录**，但 P1-requirements.md 已明确"CHANGELOG 标注是 P8 阶段任务，本轮不要求现在改"，本审查如实记录到 A5，不计入需修复项。

**结论：ALIGNED**（未发现反向传播遗漏）。

### A4: 测试覆盖

14 条 BDD 逐条核对测试文件命中（`grep -n tag0035 -i`）：

| BDD | 测试函数 | 文件 |
|---|---|---|
| BDD-1/2/3 | `test_tag0035_bdd_1_unknown_phase_fail_closed_exit_1` / `_bdd_2_ci_backstop_...` / `_bdd_3_known_phase_not_routed_...`（参数化10例）| test_check_gate.py |
| BDD-4/7 | `_bdd_4_retreat_detection_non_numeric_phase_fail_closed` / `_bdd_7_check_gate_numeric_retreat_detection_not_regressed` | test_check_gate.py |
| BDD-5/7 | `_bdd_5_phase_num_non_numeric_fail_closed` / `_bdd_7_state_transition_numeric_phase_not_regressed` | test_check_state_transition.py |
| BDD-6/7 | `_bdd_6_pre_commit_nonstandard_phase_output_warns` / `_bdd_7_pre_commit_standard_phase_output_no_extra_warning` | test_pre_commit_hook.py |
| BDD-8/9/10 | `_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md` / `_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md` / `_bdd_10_gate_p4_pure_doc_no_history_still_blocks` | test_check_gate.py |
| BDD-11/12/13/14 | `_bdd_11_blacklist_exempts_phase_card_path_reference`（参数化2例）/ `_bdd_12_whitelist_role_definition_file_path`（参数化2例）/ `_bdd_13_p6_evidence_bare_filename_recognized` / `_bdd_14_self_referential_p6_acceptance_still_blocked` | test_check_judge_verdict.py |

14/14 全部有对应测试函数，且逐一读过测试体：BDD-8/9/10 的 fixture `_tag0035_write_p4_task` 构造场景精确对应 BDD 原文（跨 commit 交付 / 回退后修复 / 纯文档红灯边界）；BDD-11 明确采用白盒直连 `_check_blacklist`（而非断言整体 CLI exit code），docstring 中给出充分理由（整体 exit 还受 BDD-12/13 才修的 `_check_whitelist_outside` 影响，混测会掩盖 BDD-11 本身的断言目标）；BDD-14 红灯用例混入一条合规角色路径引用，验证豁免机制之间互不干扰。测试质量高，无"断言过松"或"名不副实"问题。

**本次审查独立实跑（未采信 implementer 自报）**：
```
timeout 280 python3 -m pytest agate/tests/unit/ -q -n auto --tb=short
→ 1507 passed, 2 skipped in 23.99s（0 failed）

timeout 280 python3 -m pytest agate/tests/regression/ -q -n auto --tb=short
→ 30 passed, 1 failed in 1.10s
   失败：test_tag0034_zero_change.py::test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change
   （check-gate.py 字节面基线过期——objective_info 已明确声明这是本批改动 check-gate.py 字节导致
   的预期后续事项，将在本审查 ALIGNED 后由主 Agent 更新基线，非本次审查判定范围内的 MISALIGNED）

timeout 280 python3 -m pytest agate/tests/integration/ -q -n auto --tb=short
→ 96 passed in 10.40s（0 failed）
```
唯一失败项是 objective_info 已预先声明排除在判定范围外的已知基线过期项，不计入。

**minor 观察（不构成覆盖缺口）**：`_gate_p4_has_prior_code_commit` 的 tag 右括号边界防御（防止形如 `wf(TAG0035-P40)` 的未来阶段名误配）无专门测试覆盖；但 P1-requirements.md/P2-design.md 已明确注明"当前 `phases.yaml` 阶段名封闭在 P0-P8/P6.5，尚不可实际触发"，属纯防御性加固，不在 14 条 BDD 验收范围内，不计入 MISALIGNED。

**结论：ALIGNED**。

### A5: 下游影响 + 文档传播

- **下游一致性**：`ci-gate-backstop.py`/`check-events.py` 消费 `check-gate.py` 退出码的逻辑经 P1 grep 核实为纯"记录值==重跑值"相等比较，不特判具体数值，BDD-2 已用回归测试锁定这一点，本审查未发现相反证据。
- **破坏性变更**：子批A的 exit 2→1 是"未知阶段"这一此前无文档承诺、无正常业务路径会触达的分支（10 个已知阶段均不受影响，BDD-3 参数化覆盖），不构成对存量任务的破坏性变更。子批B/C/D 均为新增放行/豁免条件或新增判空报错，均有 BDD-7/10/14 红灯边界回归验证不削弱既有拦截力。
- **文档传播**：BDD-12 要求的 `dispatch-protocol.md` + `agate/phase-cards/P6-acceptance.md` 两处同步均已完成（见 A1）。`orchestrator-template.md`/`WORKFLOW.md`/`role-system.md`/`LIMITATIONS.md` 经 grep 核查均未涉及本次改动的 4 个脚本内部判据细节，无需同步。
- **CHANGELOG.md**：未标注 TAG0035 改动。**如实指出**：这是协议语义变更（4 处 fail-closed 修复），按 A5 判据本应标注；但 P1-requirements.md 已明确声明"CHANGELOG 由 P8 阶段处理，本轮不要求现在改"，且任务 `phases` 声明含 P8（未裁剪），P8 阶段有明确的 gate 检查（`check-changelog.py`）会在该阶段拦截未标注的情况。**不计入本次 MISALIGNED**，仅在此提示主 Agent：P8 阶段务必核实 CHANGELOG 补上本批 4 个子批的变更说明。

**结论：ALIGNED**（CHANGELOG 缺口已确认是延后到 P8 处理的既定安排，非本阶段遗漏）。

### A6: 锚点表覆盖

检查 `agate/scripts/check-protocol-consistency.py` 的 `SCRIPT_ALIGNMENT_ANCHORS`（CHECK 9）：
- `check-state-transition.py` 锚点「回退跳变检测」关键词 `["diff", "phase_num"]`（脚本内仍含这两个关键词，`phase_num` 函数名未被改名或删除，只改了内部实现与返回值语义）——**仍命中**。
- `check-judge-verdict.py` 锚点「judge verdict 门槛判定」关键词 `["criteria_total", "judge"]`——本次改动的 `_check_blacklist`/`_is_whitelisted`/`_check_whitelist_outside`/`_p6_evidence_basenames` 均不涉及这两个关键词所在的代码区域，**不受影响，仍命中**。
- `check-gate.py` 相关的多条锚点（`DESIGN_GAP`/`agent=main`/`_check_roadmap_done`/`BDD-[0-9]` 等）均未被本次改动触及的代码段覆盖或移除。
- 未发现本次新增的判据（`_gate_p4_has_prior_code_commit`/`_P_OUTPUT_ANY_RE`/`_PROTOCOL_SPEC_DIR_RE`/`_ROLE_DIR_RE`）属于"协议规格文档声明的规则点"（这些是纯粹的健壮性/bug 修复，不是新协议规则），按角色文件注 6 的说明，CHECK 9 锚点只验证"校验脚本存在且被正确挂载调用"，本次改动未新增需要锚点化的协议规则声明，**无需新增锚点条目**。

**实跑验证**：`timeout 60 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit=0，"仅有 365 个 WARNING，无 ERROR"（365 为改动前既有基线数量级，均为叙事性引用，与本次改动无关）。

**结论：ALIGNED**。

### A7: 设计原则一致性

- **ADR-002（可判定性——gate 门槛机器可判定）**：原文"gate 通过/不通过由脚本 exit code 决定（0=通过，1=不通过，2=需人工判断）"。本次子批A"未知阶段 exit 2→1"的改动，实质是**修正了一处此前与 ADR-002 canonical 语义本就不符的实现缺陷**——未知阶段既不是"通过"也不是"需人工判断"，是真正的"不通过"（fail），原 exit 2 只是历史上恰好借用了其他已知阶段的"通过码"数值、造成 CI backstop 判定被绕过。改为 exit 1 后与 ADR-002 的三态语义映射完全吻合。子批B/C/D 的"判空即报错 fail-closed""放宽需真实代码证据支撑""路径豁免要求越具体的上下文才放宽越窄"均是 ADR-002"可判定性"原则的具体贯彻（不引入无法机器判定的模糊放行）。
- **ADR-013（gate 生产者无关性）**：本次子批D 新增的角色文件路径白名单豁免、`P6-evidence/` 目录真实文件核对，判定依据是"路径/文件本身的客观属性"（目录前缀、文件系统真实存在性），不涉及"谁生产了这份内容"，与 ADR-013"gate 不认谁生产的"红线不冲突。
- 未发现现有 ADR 专门记录"未知/异常输入优先 fail-closed"这一具体子原则（ADR-002 只隐含此语义，未显式点名"未知输入应映射到哪个退出码"）。**建议**（不阻断）：可考虑在后续任务中补一条轻量 ADR 或在 ADR-002 后果节追加一句"未知/无法解析的输入应映射到 exit 1（不通过），不得复用任何已知'通过'语义的退出码数值"，使这一具体推论显式化、可被后续同类改动引用，避免类似缺陷再次出现在其他脚本。此为建议性质，不影响本次 ALIGNED 判定（A7 无 MISALIGNED 态）。

**结论：ALIGNED**。

## 闭环说明

本次审查全部 7 项均判 ALIGNED，无 MISALIGNED 项，无 NEEDS_HUMAN_REVIEW 项（故无待人工确认的悬挂项）。按角色文件闭环规则：**通过，可 commit**。

**遗留提示（非阻断，供主 Agent 后续跟踪）**：
1. P8 阶段需在 CHANGELOG.md 中补上本批 4 个子批（BDD-1~14）的变更说明（A5 已记录，P1-requirements.md 已声明由 P8 处理）。
2. objective_info 中已知的 2 处后续事项（ruff PLW2901 已实测确认修复生效；`tag0034_regression_baseline.json` 零字节基线待主 Agent 在本审查通过后更新）按既定流程处理，不在本次 ALIGNED 判定范围内。
3. A7 建议性补充 ADR 一句话说明"未知输入映射到 exit 1"，可选，不阻断当前 commit。
