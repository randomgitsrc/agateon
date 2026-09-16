---
phase: P3
task_id: TAG0035
parent: P2-design.md
trace_id: TAG0035-P3-20260916
agent: test-designer
type: test-design
created: '2026-09-16'
status: draft
test_code_dir: agate/tests/unit/test_check_gate.py,agate/tests/unit/test_check_state_transition.py,agate/tests/unit/test_check_judge_verdict.py,agate/tests/integration/test_pre_commit_hook.py
---
# P3-test-cases — TAG0035 gate 健壮性批

> 依据：P1-requirements.md（14 条 BDD，4 子批）+ P2-design.md（§1.1 改什么表 + §3 逐子批技术方案）+
> P2-review.md（approved，红灯边界核实细节）。TDD 口径：测试按 P2-design.md 已定案的"修复后应有行为"
> 断言，在当前未修改代码上产生真红灯（AssertionError / 项目内 import 失败），不是 SyntaxError。

`test_code_dir`（frontmatter，已用 `agate-md-field-set` 写入）覆盖以下 4 个既有测试文件：

- `agate/tests/unit/test_check_gate.py`
- `agate/tests/unit/test_check_state_transition.py`
- `agate/tests/unit/test_check_judge_verdict.py`
- `agate/tests/integration/test_pre_commit_hook.py`

本任务无新增测试文件——4 个子批的用例全部落在既有测试文件内（见约束 3 落点表），未新增
`agate/tests/regression/` 文件。`pre-commit-gate.py` 的 BDD-6/7 用例选择落在既有
`agate/tests/integration/test_pre_commit_hook.py`（而非新增 `test_pre_commit_gate_phase_num.py`）：
理由——① `pre-commit-gate.py` 的 hook 集成测试基础设施（`_install_pre_commit_hook`/`_init_commit`/
`_git_commit`/`_write_state_yaml`/`_write_p1_requirements` 等 helper）已在该文件完整存在，BDD-6/7 场景
需要真实 pre-commit hook 触发链路（`git commit` → hook → `pre-commit-gate.py` 2f/第 3 节），新增文件会
被迫复制这套 helper 或反向 import，增加维护成本而无隔离收益；② BDD-6/7 与该文件已有的
`test_phase_span_*` 系列（同样测"phase-产出一致性 WARNING"）是同一机制的不同输入维度（标准阶段名 vs
非常规阶段名），归入同文件便于横向比对既有断言风格，不产生跨文件重复。

## 1. gate_commands.P3 命令（与 P2-design.md §4 一致，未追加新文件路径）

```bash
python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_state_transition.py agate/tests/unit/test_check_judge_verdict.py agate/tests/integration/test_pre_commit_hook.py -v
```

## 2. BDD → 测试用例映射（1:1，14 条全覆盖）

| BDD | 落点文件 | 测试函数 | 参数化 | 当前状态（P3 设计时点） |
|---|---|---|---|---|
| BDD-1 | test_check_gate.py | `test_tag0035_bdd_1_unknown_phase_fail_closed_exit_1` | 否 | 红（exit=2，期望 1） |
| BDD-2 | test_check_gate.py | `test_tag0035_bdd_2_ci_backstop_exit_code_comparison_unaffected` | 否 | 红（backstop 判 FAIL：记录值 1 != 重跑值 2） |
| BDD-3 | test_check_gate.py | `test_tag0035_bdd_3_known_phase_not_routed_to_unknown_path` | 是（10 个已知阶段名） | 绿（回归不变性，预期本就是绿，见 §3 说明） |
| BDD-4 | test_check_gate.py | `test_tag0035_bdd_4_retreat_detection_non_numeric_phase_fail_closed` | 是（old_phase 非数字 / phase 非数字 两个子场景） | 红（两个子场景均无"无法解析"提示） |
| BDD-5 | test_check_state_transition.py | `test_tag0035_bdd_5_phase_num_non_numeric_fail_closed` | 是（new_phase 非数字 / old_phase 非数字 两个子场景） | 红（两个子场景均静默 exit 0） |
| BDD-6 | test_pre_commit_hook.py | `test_tag0035_bdd_6_pre_commit_nonstandard_phase_output_warns` | 否 | 红（0 输出，无"无法识别"/"一致性检查未覆盖"提示） |
| BDD-7 | test_check_gate.py<br>test_check_state_transition.py<br>test_pre_commit_hook.py | `test_tag0035_bdd_7_check_gate_numeric_retreat_detection_not_regressed`<br>`test_tag0035_bdd_7_state_transition_numeric_phase_not_regressed`<br>`test_tag0035_bdd_7_pre_commit_standard_phase_output_no_extra_warning` | 否（各 1 个） | 绿 × 3（回归不变性，预期本就是绿） |
| BDD-8 | test_check_gate.py | `test_tag0035_bdd_8_gate_p4_history_scan_prior_code_commit_allows_pure_md` | 否 | 红（exit=1，期望 0） |
| BDD-9 | test_check_gate.py | `test_tag0035_bdd_9_gate_p4_retreat_fix_commit_with_retries_allows_pure_md` | 否 | 红（exit=1，期望 0） |
| BDD-10 | test_check_gate.py | `test_tag0035_bdd_10_gate_p4_pure_doc_no_history_still_blocks` | 否 | 绿（红灯边界，预期本就是绿，见 §3 说明） |
| BDD-11 | test_check_judge_verdict.py | `test_tag0035_bdd_11_blacklist_exempts_phase_card_path_reference` | 是（P6-acceptance.md / P4-implementation.md 两个同构实例） | 红（两个实例均误判黑名单命中） |
| BDD-12 | test_check_judge_verdict.py | `test_tag0035_bdd_12_whitelist_role_definition_file_path` | 是（execution-roles/ / review-roles/ 两个目录前缀） | 红（两个实例均误判白名单外） |
| BDD-13 | test_check_judge_verdict.py | `test_tag0035_bdd_13_p6_evidence_bare_filename_recognized` | 否 | 红（裸文件名误判白名单外） |
| BDD-14 | test_check_judge_verdict.py | `test_tag0035_bdd_14_self_referential_p6_acceptance_still_blocked` | 否 | 绿（防御性红灯边界，预期本就是绿，见 §3 说明） |

14 条 BDD 均有 ≥1 个专属测试函数（不合并断言）；命名统一加 `tag0035` 前缀（既有先例
`test_tag0031_bdd_N_*`）——4 个落点文件内大量复用裸 `test_bdd_N_*` 命名服务于其它历史任务
（如 `test_check_judge_verdict.py` 自身 TAG0020 的 `test_bdd_1..9`），裸用 `test_bdd_N` 会撞名或引发
歧义，故本批统一加任务前缀，与 `test_tag0031_bdd_8/9/10/11/15` 等既有跨任务前缀写法一致。

## 3. dispatch-context 约束 2 对应说明（4 条 BDD 现在即为绿灯，非漏测）

BDD-3/7（×3）/10/14 断言的是"标准场景下行为保持不变"（回归不变性 / 红灯边界），这些场景在当前
未修改代码上本就成立，是预期内的绿——dispatch-context 约束 2 已明确说明，不因此改断言去凑"红灯"：

- **BDD-3**：未知阶段修复（子批 A）只改 `handlers.get(phase) is None` 分支，不影响 10 个已知阶段名的
  分发逻辑，`test_tag0035_bdd_3_*` 断言"已知阶段不出现'未知阶段'字样"，现状本就满足。
- **BDD-7（×3）**：三处判据修复（子批 B）均是新增 fail-closed 分支，不改标准数字阶段名的既有判据路径
  （见 P2-design.md §1.3 风险表"三处设计完全独立"），三个 `test_tag0035_bdd_7_*` 分别验证
  check-gate.py 回退检测 / check-state-transition.py phase_num / pre-commit-gate.py 差集扫描三处的数字
  场景行为不回归，现状本就满足。
- **BDD-10**：`_gate_p4_has_prior_code_commit`（子批 C）尚未实现，当前 `gate_p4` 对"暂存区无代码文件"
  场景本就无条件 `return 1`——BDD-10 要求的正是这一现状行为在放宽后继续保持，天然是绿。
- **BDD-14**：`_BLACKLIST_MD` 对裸文件名 `p6-acceptance.md` 的子串命中（子批 D 修复前）本就会拦截，
  BDD-14 要求这一拦截在 BDD-11/12/13 加固后继续保持，天然是绿。

## 4. 关键测试设计决策

### 4.1 BDD-11 采用白盒直连 `_check_blacklist`，不用全流程 CLI 断言 exit code

已用真实脚本核实：`_check_blacklist` 豁免 `phase-cards/` 路径引用后，若走全流程 CLI，同一 token
（如 `agate/phase-cards/P6-acceptance.md`）会被**另一个独立检查点** `_check_whitelist_outside`
（P2-design §3.4②③只改角色目录 + evidence 裸文件名两处，未涉及 `phase-cards/` 豁免）判定"白名单外
任务产出路径引用"，导致整体 exit 仍为 1——但这不是 `_check_blacklist` 本身豁免逻辑的问题，是另一独立
检查点尚未豁免同一路径前缀（BDD-11 原文精确点名的断言目标是`_check_blacklist` 本身："Then
`_check_blacklist` 不再仅凭 basename 子串命中就判黑名单命中"，验证行文字面也是"断言...不再因这两处
引用报黑名单命中"，未要求整体 exit==0）。若断言整体 `exit==0`，会把两个独立检查点的行为混在一起，
既不符合 BDD-11 原文精确措辞，也会让测试在 P4 implementer 严格按 P2-design 实现后仍然是假红（测试
设计缺陷，非实现缺陷）。故改用 `importlib` 直接加载 `check-judge-verdict.py`（同源手法：
`test_check_gate.py` 的 `_load_check_gate_direct` 既有先例）、直接调用 `_check_blacklist(section_lines)`
并断言其返回的 `hits` 列表不含对应 basename——精确锚定 BDD-11 点名的函数，不受 `_check_whitelist_outside`
是否额外豁免同一路径的影响。

（登记说明，非新 BDD）：`_check_whitelist_outside` 对 `phase-cards/` 前缀路径缺乏豁免这一点，若在
P4 实现阶段确认会导致真实 `P6.5-dispatch-context-judge.md`（引用协议阶段卡片路径）整体判定仍为
exit 1，建议 P4 implementer 视情况在 `_is_whitelisted` 一并加 `_PROTOCOL_SPEC_DIR_RE` 豁免（复用 BDD-11
已定义的同一正则）——P2-design.md 未显式排除这一附加改动，且与 BDD-11 的设计意图（"不应误判协议规格
文档路径引用"）一致；若 P4 判断不做此项，需在 P4-implementation.md 说明理由，供 P5/P6 核实
`P6.5-dispatch-context-judge.md` 真实场景下的端到端结果。

### 4.2 pre-commit-gate.py 相关用例的 task_id 用 "TXX0001" 而非全文件通用的 "T001"

BDD-6/7 用例需要在**真实（非 `--no-verify`）** hook commit 中重新暂存 `.state.yaml`（以触发 2f phase-
产出一致性检查所在的任务候选范围判定），这会经过 `check-state-yaml.py` 的 2a 格式校验。已用
`timeout 20 python3 agate/scripts/check-state-yaml.py` 实测确认：该校验的 `task_id` 正则
`^T[A-Z]{2}\d+$` 不接受本文件其它用例广泛使用的 "T001"（"001" 三位均为数字，不满足"2 个大写字母"要求），
若沿用会导致 commit 在 2a 就被拦截、通不到 2f。本文件已有 `test_it2_root_state_phase_change_gate_passes`
/`test_it3_inline_prod_touched_mention_not_blocked` 等先例在需要真实触发格式校验时改用 "TXX0001"，
BDD-6/7 沿用同一约定。

### 4.3 BDD-6 断言避免"裸文件名"假阳性陷阱

初版用例曾用 `assert "p-alpha-notes.md" in result.output or "无法识别" in result.output` 作为断言——
手工复现（`git commit` 直接跑）发现该断言会被 git 自身的 `create mode 100644
agate-workspace/tasks/T001/p-alpha-notes.md` 摘要行意外命中，产生假绿（与"一致性检查是否真的产出提示"
这一断言目标无关）。已改为只断言 GATE 一致性检查专属的提示短语（"无法识别" / "一致性检查未覆盖"），
不再包含裸文件名分支。

### 4.4 BDD-8/9/10（gate_p4）测试固定用 `task = repo / "task"` 相对路径 + 不写 P2-skeleton.md/CODE-MAP.md

复用 `test_tag0031_bdd_9_gate_p4_non_standard_nesting_resolves_via_agate_env` 已验证的调用形态
（`_run_gate(..., "P4", "task", cwd=str(repo))`），避免不必要的骨架/CODE-MAP WARNING 分支引入额外
干扰变量，使断言聚焦于"暂存区无代码文件"判据本身是否被 `_gate_p4_has_prior_code_commit` 的历史扫描
放宽。

## 5. 红灯自检记录（P3 自跑结果，2026-09-16）

```
timeout 120 python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_state_transition.py agate/tests/unit/test_check_judge_verdict.py agate/tests/integration/test_pre_commit_hook.py -v
```

结果：`14 failed, 338 passed`（全量跑，含既有历史用例）。14 个 FAILED 逐一核对均为 `AssertionError`
（B 类：测试断言与当前未实现行为不符），无 `SyntaxError`/collection error/项目外 import 失败。
14 个 FAILED 精确对应上表 10 条"当前状态：红"的 BDD（BDD-4/BDD-5/BDD-11/BDD-12 各自 2 个参数化子用例，
其余各 1 个，10+2+2+2 = ... 精确计数：BDD-1(1)+BDD-2(1)+BDD-4(2)+BDD-5(2)+BDD-6(1)+BDD-8(1)+BDD-9(1)+
BDD-11(2)+BDD-12(2)+BDD-13(1) = 14），与预期完全一致；BDD-3/7×3/10/14 共 6 个测试函数全部 PASSED，
符合 dispatch-context 约束 2 的预期绿灯说明。既有历史用例（338 个）无一受本批新增测试影响而回归。
