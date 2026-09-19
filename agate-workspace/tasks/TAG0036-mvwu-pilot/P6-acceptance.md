---
phase: P6
task_id: TAG0036
type: acceptance
parent: P5-verification.md
trace_id: TAG0036-P6-20260919
status: draft
created: 2026-09-19
agent: verifier
# ── v2.0 机器汇总 ──
pass: 71
fail: 0
ui_affected: false
---
# P6 验收报告 — TAG0036 MVWU 阶段 1 试点（RM-AG0063）

**Summary**: 71/71 PASS, 0 FAIL（每条均为 P6 阶段本次实跑所得，不引用 P5 结果；无 UI，不派 vision-analyst，无截图）。

## 验收方法与边界

- 基线 `<内核基线>` = `git merge-base HEAD main` = `efb113ba5d491959cc2bdac4f68fefcc1d0130cc`；被验 HEAD = `e1ac29e`（P5 提交），工作树除 `gate-events.jsonl`（验收前已修改）与 P6 产出外无未提交改动。
- 行为类 BDD：`pytest -v` 逐用例结果（`pytest-check-mvwu-verbose.log` 111 passed、`pytest-mvwu-docs-verbose.log` 65 passed）+ `bdd-to-testcase-map.log`（BDD→用例→结果机械映射，70 个 BDD 有同名前缀用例，仅 BDD-56 按设计无单测）。对 dispatch-context 点名的 BDD 另做**独立于测试代码的直接实证**（自建临时 git 仓库直接运行 `check-mvwu.py`，存输入/命令/输出，见 `direct-*.log`）。
- 文档类 BDD：`docs-*.log` 摘录满足 Then 的原文行（文件:行号）与 `git diff efb113b` 统计；负向条目用 grep/diff 计数实证。
- 零内核/范围类：P6 阶段重新执行 P2-design.md §7 的 `P5_kernel_diff` / `P5_kernel_diff_wt` / `P5_roles_diff` / `P5_history_untouched` 四条命令（`diff-p5-four-commands.log`，均 exit 0）。
- BDD-60/62 只验“成文到位”（指定节存在、含字面要点、无“已生效”字样），**未**断言机制已生效。
- 只验收不修改：未改任何代码/文档/测试，未 git add/commit；临时目录均已删除（见 `post-test-residue.log`）。

## ① tests_filter（BDD-1 至 BDD-5）

- PASS BDD-1: tests_filter 写入 frontmatter（双引号、含空格）后，agate-md-field-get.py 读出合法 JSON，batches[0].tests_filter 与写入值逐字节相同；另 5 个特殊值等价类（空格/管道/转义引号/参数化 id/中文注释）原样透传 (P6-evidence/direct-bdd-1-2-4-tests-filter-gate.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-2: 含 tests_filter 的合法 dispatch_plan 与“删去全部 tests_filter”一样被 _gate_p2_dispatch_plan 放行（均返回 None），对照组缺 complexity 仍被拒，证明不是 fail-open (P6-evidence/direct-bdd-1-2-4-tests-filter-gate.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-3: check-gate.py 相对基线零 diff（已提交与工作树两口径），既有三个测试文件相对基线零改动且实跑 239 passed 0 failed (P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/diff-p5-four-commands.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-4: 批 A 有 tests_filter、批 B 无：gate 校验通过；check-mvwu 对 B 输出 UNKNOWN reason=tests_filter，A 输出 PASS 且与“仅含 A”的对照输出相同 (P6-evidence/direct-bdd-1-2-4-tests-filter-gate.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-5: tech-debt.md 新增 DEBT0043，含 _gate_p2_dispatch_plan 与“静默放行”字样，基线上该符号 0 命中；check-debt.py exit 0；check-gate.py 零 diff (P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/pytest-mvwu-docs-verbose.log)

## ④ 字段落地路径（BDD-6 至 BDD-9）

- PASS BDD-6: P2 卡片「dispatch_plan 机器字段」节含 tests_filter 可选键、双引号、禁止全量、expected_red 落 P4-evidence/{batch}.log、[A-Za-z0-9._-]+、缺省、python -m pytest 全部字面要点（摘录含行号） (P6-evidence/docs-bdd-6-7-8-9-tests-filter-guidance.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-7: architect.md「批次设计」节含禁止全量、gate_commands.P3、红灯基线、绿灯确认、expected_red；相对基线只增 34 行零删除，硬规则所在的 209-233 行与基线逐字相同 (P6-evidence/docs-bdd-6-7-8-9-tests-filter-guidance.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-8: agate/（排除 tests）下 tests_filter 示例值内裸 python3 命中 0 行；P2 卡与 architect.md 均含“不裸 python3”与 AGATE_PYTHON 平台中立约束 (P6-evidence/docs-bdd-6-7-8-9-tests-filter-guidance.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-9: P2 卡与 architect.md 均说明 output 为可选键、仅供 --observe、不新增 gate 校验；agate-frontmatter-check.py 与 check-structure-consistency.py 相对基线 diff 为空 (P6-evidence/docs-bdd-6-7-8-9-tests-filter-guidance.log, P6-evidence/pytest-mvwu-docs-verbose.log)

## ② P4-evidence 证据落点（BDD-10 至 BDD-12）

- PASS BDD-10: P4 阶段卡新增「批级证据 P4-evidence」节，含路径、逐行 key: value、command/exit_code/git_head（全长）/timestamp/expected_red/duration_seconds/failed_tests、node id 双引号编码、主 Agent 在批 commit 前写入、不阻断、filename-safe、不进 judge 白名单 16 个字面要点全部命中 (P6-evidence/docs-bdd-10-11-evidence-landing.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-11: task-files.md 阶段产出表已登记 P4 行 P4-evidence/{batch}.log，dispatch_plan 示例注释含 tests_filter 可选说明 (P6-evidence/docs-bdd-10-11-evidence-landing.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-12: pre-commit-gate.py / agate-archive-stale-outputs.py / check-p6-provenance.py / check-judge-verdict.py / judge.md 及 dispatch-protocol.md 整文件相对基线 diff 全空；agate/rules/ 下 P4-evidence 命中 0 (P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/diff-p5-four-commands.log, P6-evidence/pytest-mvwu-docs-verbose.log)

## ③ check-mvwu.py：六项检查与四态 verdict（BDD-13 至 BDD-42）

- PASS BDD-13: 两批 A、B 合法任务目录，stdout 恰两行契约行，顺序与声明一致，VERDICT 属四态 (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-14: 检查 1：缺 tests_filter 键或值为空串/非字符串的批判 UNKNOWN reason=tests_filter（4 个等价类用例全过） (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-15: 检查 2：command 首词不可解析或证据缺 command 键判 UNKNOWN reason=command（5 个用例全过） (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-16: 前导 FOO=1 被跳过：批 A 得 PASS，批 B（FOO=1 no-such-runner-xyz）判 reason=command，直接实证与 pytest 一致 (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-17: 复合命令 cd sub && no-such-runner-xyz 只判首词 cd（内建）得 PASS，--help 含“仅检查首词”已知局限声明 (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-18: tests_filter 与证据 command 不一致仍得 PASS，--help 含“不比对 command 与 tests_filter”声明 (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-19: 哨兵实证：command 与 tests_filter 均为 touch 哨兵，默认与 --observe 两种模式运行后哨兵均不存在；对照组手动执行同一命令哨兵会出现，说明手法有效 (P6-evidence/direct-bdd-19-sentinel.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-20: 检查 3：有 tests_filter 但 P4-evidence/<id>.log 不存在判 UNKNOWN reason=evidence (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-21: 不安全批 id（空格/管道/../）判 reason=evidence，且输出不含 P4-evidence 之外候选文件的字段值（独有标记 OUTSIDE_SECRET_9f3 未出现） (P6-evidence/direct-bdd-22-44-print-forms.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-22: 五批（a b / x|y / ../e / ok-1.2_3 / 空串）直接运行：stdout 恰 5 行，逐行等于期望的 \x20 \x7c \x2f 编码与 batch=?，按空白切分每行 3 或 4 词 (P6-evidence/direct-bdd-22-44-print-forms.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-23: 检查 4：缺 exit_code 键或值非整数判 UNKNOWN reason=exit_code（4 个用例全过） (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-24: 检查 5：exit_code 为 0 时，不存在的 40 位 sha、短 sha、分支名、HEAD、缺键、任务目录不在 git 仓库内均判 UNKNOWN reason=git_head，全长小写与大写有效 sha 得 PASS，直接实证与 pytest 一致 (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-25: 检查 1-5 通过且 exit_code 0 输出 MVWU_RESULT: PASS batch=<id> 无 reason (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-26: exit_code 1 且 expected_red 为空输出 FAIL (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-27: 失败清单含不在 expected_red 内的用例（t_b）输出 FAIL (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-28: exit_code 1，failed_tests 非空且为 expected_red 子集输出 EXPECTED_RED (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-29: exit_code 非零、expected_red 非空但 failed_tests 缺失或为 [] 时判 UNKNOWN reason=expected_red，不猜 EXPECTED_RED (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-30: 直接实证：expected_red 含 test_x[a,b-1] 参数化 id 的引号列表按 2 个与 1 个元素解析，输出 EXPECTED_RED，未被 id 内逗号切碎 (P6-evidence/direct-bdd-30-31-32-node-ids.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-31: 直接实证：failed_tests 为 test_x[a,b-2]、expected_red 为 test_x[a,b-1]（及仅函数名前缀）均输出 FAIL，精确字符串相等不做归并 (P6-evidence/direct-bdd-30-31-32-node-ids.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-32: 直接实证：expected_red 为标量 t_a、未闭合 [t_a, 、含非字符串元素 [1, 2] 均判 UNKNOWN reason=expected_red (P6-evidence/direct-bdd-30-31-32-node-ids.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-33: exit_code 0 而 failed_tests 非空判 UNKNOWN reason=exit_code，不是 PASS (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-34: 直接实证六批（P/Q/R/S/共用 id 两批）reason 依次为 tests_filter、command、exit_code、git_head、evidence、evidence，与固定判定顺序一致，重复 id 的两批均判 evidence (P6-evidence/direct-bdd-34-reason-order.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-35: 全部 UNKNOWN 场景行内不含独立词 PASS，--help 输出含“UNKNOWN 不等价于 PASS，不得作为放行依据” (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-36: 直接实证：PASS/FAIL/EXPECTED_RED/UNKNOWN 四态混合任务在默认与 --observe 两种模式均 exit 0，无 traceback (P6-evidence/direct-bdd-36-37-38-exit-and-readonly.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-37: 直接实证：无参数、目录不存在、--observe 加不存在目录、仅 --observe 均 exit 2，stdout 无契约行，stderr 有用法/目标不存在说明，无 traceback (P6-evidence/direct-bdd-36-37-38-exit-and-readonly.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-38: 直接实证：含 .state.yaml 与 gate-events.jsonl 的真实布局任务目录，两种模式运行前后目录文件字节、git status --porcelain、.git/index 均不变；验收整体环境无残留见 post-test-residue.log (P6-evidence/direct-bdd-36-37-38-exit-and-readonly.log, P6-evidence/post-test-residue.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-39: 直接实证：P2 缺失、坏 YAML frontmatter、无 dispatch_plan、mode: single 无 batches 四种输入均 exit 0、无 traceback，stdout 恰一行 MVWU_RESULT: UNKNOWN batch=- reason=tests_filter (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-40: 直接实证：空文件、含 \xff\xfe\x80 非 UTF-8 字节、无 key: value 行的证据均判 UNKNOWN reason=evidence 且不崩溃，同任务的正常批仍得 PASS (P6-evidence/direct-bdd-16-17-18-24-35-39-40-supplement.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-41: 三批 A(exit 0)/B(exit 1 无预期红)/C(无证据)依序输出 PASS/FAIL/UNKNOWN reason=evidence，互不污染 (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-42: 合并 commit 形态的批：pytest 用例覆盖默认与 --observe 两种模式 verdict 均为 PASS；直接实证（同一 commit 改 a、b）--observe 行 verdict 为 PASS 且 boundary 列为 UNKNOWN，boundary 不参与 verdict (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/direct-bdd-47-48-49-50-git-range.log)

## ③ --observe 模式（BDD-43 至 BDD-56）

- PASS BDD-43: 两批合法任务 --observe 输出恰两行，按 GFM 转义规则切分每行恰 7 列，无表头、诊断只走 stderr，第 1 列批 id、第 2 列 tests_filter (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-44: 直接实证：含管道、反引号加反斜杠、换行的 tests_filter 各输出一行，第 2 列依次为 \| 转义、\` 与 \\ 转义、字面 \n，每行按 GFM 切分恰 7 列 (P6-evidence/direct-bdd-22-44-print-forms.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-45: 直接实证：duration_seconds 8 显示 8s，8.5 显示 8.5s，缺键/负数/非数显示 -，5000 位 9 与 400.400 位超长值不吞行（本实现该列显示 -）且其后的批 12s 仍正常输出，耗时列不影响 verdict (P6-evidence/direct-bdd-45-huge-duration.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-46: 批 A 有 P4-evidence/A.log 时 evidence 列为 yes，批 B 无则为 no (P6-evidence/pytest-check-mvwu-verbose.log, P6-evidence/bdd-to-testcase-map.log)
- PASS BDD-47: 直接实证：src/a.py 在 main 更早历史与分支后前进的 main 中也被改过（区间外不可见），a/b 在任务分支两个独立 commit，A、B 行 commit 形态均为 per-batch (P6-evidence/direct-bdd-47-48-49-50-git-range.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-48: 直接实证：src/a.py 与 src/b.py 在任务分支同一 commit，A、B 行 commit 形态均为 merged (P6-evidence/direct-bdd-47-48-49-50-git-range.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-49: 直接实证：未声明 output、output 文件区间内从未改动、output 文件分散于 2 个 commit 的三批 commit 形态均为 UNKNOWN (P6-evidence/direct-bdd-47-48-49-50-git-range.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-50: 直接实证：仓库仅有 trunk 分支（无 origin/HEAD、无 main/master）及 HEAD 即 main 尖端（区间为空）两种情形，commit 形态与 boundary 均为 UNKNOWN，exit 0，stderr 含 baseline 诊断，verdict 仍为 PASS (P6-evidence/direct-bdd-47-48-49-50-git-range.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-51: 直接实证：逐批 commit 改动 {src/a.py, agate-workspace/tasks/T1/note.md}，排除默认工作区 tasks/ 前缀后恰为 {src/a.py}，boundary 为 exact (P6-evidence/direct-bdd-51-54-boundary.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-52: 直接实证：.agate.env 声明 AGATE_WORKSPACE=my-ws 时，my-ws/tasks/ 被排除得 exact，agate-workspace/tasks/ 不再排除得 mismatch (P6-evidence/direct-bdd-51-54-boundary.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-53: 直接实证：commit 多改未声明的 config/x.yaml，或声明了 src/b.py 却没改，boundary 均为 mismatch (P6-evidence/direct-bdd-51-54-boundary.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-54: 直接实证：合并 commit 形态（已声明 output）与未声明 output 的批，boundary 均为 UNKNOWN (P6-evidence/direct-bdd-51-54-boundary.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-55: 同一批在默认与 --observe 两种模式 verdict 值逐一相同（四态混合任务直接对照），--observe 同样 exit 0、不写文件、目标错误 exit 2 (P6-evidence/direct-bdd-36-37-38-exit-and-readonly.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-56: 判据 6 真实证据：在 worktree 根对 TAG0035-gate-robustness（4 批）与 TAG0034-dispatch-routing（3 批）运行 --observe，均 exit 0，行数等于各自 dispatch_plan 批数（4、3），每行 GFM 切分恰 7 列，运行前后 git status --porcelain 无变化，任务目录无 diff (P6-evidence/bdd-56-observe-real-task.log)

## 单测与平台无关（BDD-57、BDD-58）

- PASS BDD-57: test_check_mvwu.py 含检查 1-5 失败用例、四态用例、--observe 七列与 commit 形态/基线/boundary 各态用例、exit-code、reason 顺序、参数化 id、转义用例；无硬编码 /tmp、无裸 python3 子进程命令、写入均在 tmp_path，运行前后 git status agate-workspace 不变；首个用例带 windows_smoke (P6-evidence/bdd-57-test-file-compliance.log, P6-evidence/pytest-check-mvwu-verbose.log)
- PASS BDD-58: pytest -m windows_smoke 对 test_check_mvwu.py 选中 1 条并通过（1 passed, 110 deselected） (P6-evidence/windows-smoke-bdd-58.log)

## ⑤ 方法学成文（BDD-59 至 BDD-66）

- PASS BDD-59: CONTEXT.md 相对基线仅新增 5 行、零删除，基线 29 个表格行逐字保留；新增 MVWU/tests_filter/P4-evidence/四态 verdict/boundary(I1) 均为三列且首次定义位置指向存在的文件，MVWU 定义含“最小可验证工作单元”，四态 verdict 含四词与“UNKNOWN 不等价于 PASS” (P6-evidence/docs-bdd-59-context-terms.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-60: role-system.md 新增「审查锚点」节，含浅化、执行顺序、资源地图、正交、不可互相替代；新增行“已生效/已验证生效”0 命中；除 architect.md 外执行角色文件相对基线 diff 为空 (P6-evidence/docs-bdd-60-role-system-anchor.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-61: 判据一 Tracer Bullet 在 P2 卡与 architect.md 均含触发条件（≥2 个批加关键路径）、冒烟级验证、管道确实通的目的、与 P3 红灯批的边界 (P6-evidence/docs-bdd-61-62-63-64-batch-criteria.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-62: architect.md 判据一处含 Walking Skeleton 的吸收/拒绝记录（ADR-003、与 P2-skeleton.md 不是同一机制、不新增字段）；新增行“已生效”0 命中；agate/assets/templates 无新增文件 (P6-evidence/docs-bdd-61-62-63-64-batch-criteria.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-63: 判据二 Vertical Slice 在 P2 卡与 architect.md 均含业务能力优先、写明理由、批 id 自检句式、与判据一同一决策的两个面；check-gate.py 零 diff (P6-evidence/docs-bdd-61-62-63-64-batch-criteria.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-64: 判据三 Fitness Functions 在 P2 卡「gate_commands 声明」节与 architect.md 均含适应度、四个示例维度、由项目自选、本任务无架构适应度检查；agate/（排除 tests）对 ArchUnit/dependency-cruiser/import-linter 命中 0 (P6-evidence/docs-bdd-61-62-63-64-batch-criteria.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-65: adr.md 头部（首个 ADR 之前）新增复审触发条件：已过时加被什么取代、不删除、每次新增 ADR 与 P7 复审时机；相对基线零删除行，ADR 数不变，无自动过期/强制复审 gate 表述 (P6-evidence/docs-bdd-65-adr-recheck.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-66: P2 卡含 decisions/ 落点、P2 前读取既有决策、已过时加不删除、写入时机，P7 卡检查项 6 写明落点核对；决策节与 P7 新增项无拦截式表述；check-gate.py 零 diff 且无 decisions 引用 (P6-evidence/docs-bdd-66-decisions-landing.log, P6-evidence/pytest-mvwu-docs-verbose.log)

## 负向与收口（BDD-67 至 BDD-71）

- PASS BDD-67: P1 BDD-67 列出的 16 条内核路径（均真实存在）相对基线 diff 全空，已提交与工作树两口径均 exit 0，P5_kernel_diff 与 P5_kernel_diff_wt 在 P6 阶段重跑 exit 0 (P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/diff-p5-four-commands.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-68: check-mvwu 在 agate/rules、check-gate.py、pre-commit-gate.py、ci-gate-backstop.py、agate-summary.py、.github/ 中命中 0 行（各路径均存在）；TAG00[0-2]*/TAG003[0-5]* 历史任务目录相对基线 diff 为空，P5_history_untouched 重跑 exit 0 (P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/diff-p5-four-commands.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-69: scripts/README.md 含 check-mvwu.py 行（观测、不阻断、--observe、0=任一 verdict、2=用法/目标错误）；tests/README.md 行用例数 111 等于 collect-only 实数；count-tests.sh 总数 1844 大于等于 1668+111；CHANGELOG [Unreleased] 含 TAG0036 (P6-evidence/registry-bdd-69-readme-changelog.log, P6-evidence/count-tests.log, P6-evidence/pytest-mvwu-docs-verbose.log)
- PASS BDD-70: 全量 pytest（CI 口径 --reruns 1 -n auto）1842 passed / 2 skipped / 0 failed，EXIT_CODE 0；consistency --strict-errors-only exit 0（0 ERROR，CHECK9-coverage 0 新增，check-mvwu 已在 GATE_SCRIPT_EXEMPT，test_sg_6 通过）；ruff 全通过；本任务无 .sh 改动 (P6-evidence/full-suite.log, P6-evidence/consistency-ruff-m18.log, P6-evidence/diff-bdd-3-5-9-12-67-68.log, P6-evidence/count-tests.log)
- PASS BDD-71: P4-protocol-alignment-review.md 存在（25316 字节），frontmatter agent 为 protocol-alignment-review（非 main），含各审查项结论与最终结论；P4 提交 4ee499f 信息含 self-gate-review: 路径 (P6-evidence/bdd-71-self-gate-review.log, P6-evidence/pytest-mvwu-docs-verbose.log)

## 验收中的如实观察（不改变上述二值结论）

- BDD-45：5000 位 9 的 duration_seconds 在本实现中耗时列显示 `-`（超出实现的数值位数上限），未吞行、未崩溃，符合 dispatch-context 对该修复点“不吞行”的要求；P1 BDD-45 未规定超长值的具体显示。
- BDD-71：`P4-protocol-alignment-review.md` 内 A2 段保留一条 NEEDS_HUMAN_REVIEW 及“待人工确认”标记（关于 CONTEXT.md 中 boundary(I1) 的措辞）；CONTEXT.md 现文已含“--observe 列取值 exact/mismatch/UNKNOWN”括注。该文件满足 BDD-71 的三项客观条件（存在、agent≠main、含结论），此标记是否需在提交前补 `[HUMAN_CONFIRMED]` 由主 Agent 决定。
- BDD-70：consistency 全量输出含 367 条 WARNING、0 ERROR（其中 2 条 CHECK1 涉及本任务 P2-design.md 示例 YAML、1 条 CHECK10-scriptref，均为 WARNING 级；CHECK9-coverage 0 条；无一条涉及 check-mvwu 的脚本引用漂移）。
- 本次 full-suite 在标准命令上追加 `-p no:cacheprovider`，仅为避免在仓库产生 .pytest_cache，不改变用例集。
- 本地 `main`（7f3ef3b）已领先于 P1 记载的 efb113b；`git merge-base HEAD main` 仍为 efb113b，故 `main...HEAD` 与 `git diff efb113b` 口径一致。
