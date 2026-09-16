---
phase: P4
task_id: TAG0035
parent: P4-implementation.md
trace_id: TAG0035-P4-review-20260916
agent: review
type: review
created: 2026-09-16
status: approved
---

# P4-review — TAG0035 gate 健壮性批（review，4 子批累积 diff）

> 偏执 Staff Engineer 视角，独立评审 4 个子批（A/B/C/D）的完整代码实现（工作树未 commit，`git diff --stat` 确认 8 文件改动，124 insertions(+)/17 deletions(-)，无意外改动）。评审依据：dispatch-context 约束 1-7、P1-requirements.md（14 条 BDD）、P2-design.md §3.1-3.4、P2-review.md、4 份 P4-implementation*.md。已独立读代码 + 独立重跑测试，未照单全收 implementer 自测声明。

## Pass 1（CRITICAL）— 数据安全与正确性

- 未发现 SQL 注入/字符串拼接进查询（本批无数据库交互）。
- 未发现无约束的 Read-Check-Write 竞态（本批全部改动为只读 git 命令 + 本地文件系统判据，`_gate_p4_has_prior_code_commit`/`_p6_evidence_basenames` 均为只读，无写操作）。
- 未发现 LLM 生成数据未校验直接写库的情况。
- 未发现 TOCTOU。

无 CRITICAL 发现。

## Pass 2（INFORMATIONAL）— 代码健康

未发现 async/sync 混用、N+1、O(n²) 或资源泄漏问题。`_p6_evidence_basenames` 对 `os.listdir` 结果显式 `try/except OSError` 兜底，边界处理合理；`_gate_p4_has_prior_code_commit` 对 `_git()` 返回码逐层检查（`rc != 0` 分别 continue/return False），无吞错。三处新增函数均有清晰 docstring，说明了 BDD 关联与设计取舍（详见约束 7）。

## 逐条评审结论（dispatch-context 约束 1-7）

### 约束 1：逐子批核对实现 vs 设计

已逐一核对 4 份 `P4-implementation*.md` 与 `P2-design.md` §3.1-3.4：

- **子批 A**：`check-gate.py:1517-1519` `sys.exit(2)` → `sys.exit(1)`，与设计 §3.1 逐字一致；stderr 文案未改（已含阶段名），满足 BDD-1。
- **子批 B**：三处独立实现均与设计 §3.2 一致——`check-gate.py:1490-1496` 回退检测判空分支、`check-state-transition.py:212-216` `phase_num()` 返回 `Optional[int]`、`pre-commit-gate.py:87` 新增 `_P_OUTPUT_ANY_RE` + 两处差集扫描（L307-316、L606-614）。三处消费语义（early-exit fail-closed / 主流程 fail-closed / WARNING 不阻断）确实各自独立，未复用同一 patch，符合 P1 隐含需求 3 的强制要求。
- **子批 C**：`_gate_p4_has_prior_code_commit`（`check-gate.py:214-235`）用 `git log --grep="wf(<task_id>-P4)" --fixed-strings` + 逐 commit `git diff-tree` 扫描，与设计 §3.3 完全一致，且已按 P2-review.md 约束 3 的建议加了收尾右括号定界（`wf({task_id}-P4)` 而非无定界的 `wf({task_id}-P4`）。
- **子批 D**：`check-judge-verdict.py` 的 `_PROTOCOL_SPEC_DIR_RE`/`_check_blacklist`/`_ROLE_DIR_RE`/`_p6_evidence_basenames`/`_is_whitelisted`/`_check_whitelist_outside` 六处改动与设计 §3.4 逐字一致；`dispatch-protocol.md`/`P6-acceptance.md` 两处文档同步已核实（`git diff` 确认措辞落地）。

**结论：4 子批实现均忠实落实设计方案，无"实现了什么都行、只要测试过"的偏离。**

### 约束 2：两处 DESIGN_GAP 的处理是否恰当

1. **子批 A：`test_other_unknown_phase_exit_2` → `test_other_unknown_phase_exit_1`**——已读该测试（`test_check_gate.py:199-204`），断言场景是"未知阶段 P9 应 exit=?"，这正是 BDD-1 要修复的目标行为本身（未知阶段 fail-open→fail-closed），断言值从 2 改 1 是同一测试场景对新行为的必然更新，不是误改了一条无关测试。**判定：合理。**
2. **子批 B：`check-state-transition.py` main() 把 `old_phase in ("PAUSED","READY","DONE")` 与空字符串同等处理为合法 `old_num=0`**——已独立验证：临时把该扩展判据还原为仅判空字符串（`old_num = 0 if not old_phase else phase_num(old_phase)`），重跑 `test_st_15_paused_to_p4_recovery_exit_0` 与 `test_st_19_commit_gate_paused_recovery_skipped_exit_0`，**两条既有回归测试确实从 pass 变为 fail**（`AssertionError: assert 1 == 0`），随后已恢复原文件并确认 47 个用例全部转回 pass。**这不是"编出来的理由"，是真实存在的回归依赖，扩展判据是必要的，处理恰当。**

### 约束 3：红灯边界是否真的不会被破坏（独立验证）

- **BDD-10**（`gate_p4` 判据放宽不误伤纯文档场景）：`test_tag0035_bdd_10_gate_p4_pure_doc_no_history_still_blocks` 通过。额外用临时 git 仓库手工构造了一个比既有测试更刁钻的场景——`retries: {P4: [...]}` 非空但从未有过真实代码 commit——独立验证 `check-gate.py P4` 仍返回 1（`exit=1`）。这证明 `_gate_p4_has_prior_code_commit` 的判据真正锚定在"git 历史是否存在过真实代码 diff"这一客观事实上，而不是可被 `retries` 字段这类状态标记绕过，红灯边界成立。
- **BDD-14**（judge 黑白名单加固不放松真实自述场景）：独立重跑 `test_tag0035_bdd_14_self_referential_p6_acceptance_still_blocked`，通过（exit=1）。已读 `main()` 调用顺序（`check-judge-verdict.py:530-537`）确认 `_check_blacklist` 先于 `_check_whitelist_outside` 执行，裸文件名引用（无 `phase-cards/` 路径前缀）不满足 `_PROTOCOL_SPEC_DIR_RE` 豁免条件，仍计入 `hits` 触发 `exit 1`。**两条止损点均独立确认成立。**

### 约束 4：子批 D"可选加固不采纳"决定是否合理

已读 `check-judge-verdict.py` 的实际调用链验证该决定的技术论证：`_check_blacklist` 豁免 `phase-cards/` 路径引用后（BDD-11），若同一引用同时经过 `_check_whitelist_outside`（`main()` L534），`_is_whitelisted` 的 basename 判定不认识 `phase-cards/` 前缀（`_WHITELIST_MD` 不含 `p6-acceptance.md`/`p4-implementation.md`），该路径仍会被判"白名单外"→ `exit 1`。也就是说，即便接入 `_PROTOCOL_SPEC_DIR_RE` 到 `_is_whitelisted`，`_check_whitelist_outside` 这条独立检查点不改也不会真正让整体流程放行——implementer-D 给出的三点理由（P2-design 未要求该接入 / P3 测试白盒锚定 `_check_blacklist` 本身不断言整体 exit / 已知残留行为非新回归）经代码验证站得住脚，"不采纳"是合理决定，不构成打回理由。

### 约束 5：测试覆盖是否真实（独立抽样重跑）

未照单全收，独立重跑：
- 全部 29 个 `tag0035` 相关用例（`test_check_gate.py`/`test_check_state_transition.py`/`test_check_judge_verdict.py`/`test_pre_commit_hook.py`）：**29 passed**。
- `agate/tests/unit/` 全量 `-n auto`：**1507 passed, 2 skipped, 0 failed**（与子批 D 声明的"1 failed（ruff PLW2901）"不同——已核实子批 C 事后已修复该 ruff 问题，`commit_hash` 改名为 `raw_hash`，当前单元测试全绿，无残留）。
- `agate/tests/integration/` 全量 `-n auto`：**96 passed, 0 failed**。
- `agate/tests/regression/` 全量 `-n auto`：**30 passed, 1 failed**——唯一失败是 `test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change`（TAG0034 零字节基线，`check-gate.py` 字节面已变），与 dispatch-context objective_info 描述完全一致，属已知的、待本轮评审通过后由主 Agent 统一处理的基线更新事项，不是本次实现缺陷。
- `ruff check agate/scripts/`：**All checks passed!**
- `check-protocol-consistency.py --strict-errors-only`：**0 ERROR**（365 WARNING，与本批改动无关）。
- `check-maintainability.py`：`god_file_count: 0, fuzzy_boundary_count: 0`，无 violation，无需 `known-violations.md`。

**结论：4 份 P4-implementation*.md 声明的自测结果真实可信，独立重跑结果一致（除子批 D 文档记录的 ruff 失败已被后续子批修复，当前状态更优）。**

### 约束 6：维护性反模式检查

`check-maintainability.py` 检出 0 violations，`known-violations.md` 不存在但也不需要（violations 为空场景不阻断）。**满足约束 6。**

### 约束 7：代码质量

- `_gate_p4_has_prior_code_commit`：docstring 清晰说明覆盖 BDD-8/9 的共同前提，逻辑边界处理合理（`task_id` 空/git 命令失败/无匹配 commit 均安全返回 `False`，fail-closed 取向正确）。
- `_p6_evidence_basenames`：docstring 说明目录不存在返回空集、裸文件名识别语义，`OSError` 兜底已实现（`try/except OSError: return frozenset()`），边界处理合理。
- `_check_blacklist` 改造：docstring 更新说明豁免逻辑与红灯边界的关系，逻辑清晰。

无代码质量问题。

## 输出结构

```
CRITICAL：无
INFORMATIONAL：无实质性发现
测试缺口：未发现（29 个 TAG0035 用例 + 三分片全量测试独立重跑一致）
锁定决策：
  - 子批A/B/C/D 实现均忠实落实 P2-design.md 方案
  - 两处 DESIGN_GAP（子批A测试更名、子批B PAUSED/READY/DONE 扩展）均已独立验证为必要且合理
  - BDD-10/BDD-14 红灯边界独立验证成立（含超出既有测试范围的手工红队验证）
  - 子批D"不采纳可选加固"决定经代码调用链验证站得住脚
```

## 门槛判定

**status: approved**

理由：4 个子批的代码实现均忠实对应 P2-design.md 技术方案，14 条 BDD 全部有对应测试且独立重跑通过（29/29 tag0035 用例 + unit 1507 passed + integration 96 passed + regression 30 passed/1 known-failure），两处 DESIGN_GAP 均独立验证为真实必要（非编造理由），两条已知止损点（BDD-10/BDD-14）通过独立手工红队测试确认未被放松，子批 D 的"不采纳"决定经代码调用链验证合理，`ruff`/`check-protocol-consistency.py`/`check-maintainability.py` 均无问题。唯一的测试失败（`test_bdd_39` 零字节基线）是已知的、范围外的待办事项，不构成本次实现缺陷，不影响 approve 判定。
