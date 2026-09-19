---
phase: P2
task_id: TAG0036
parent: P2-design.md
trace_id: TAG0036-P2-20260919
created: '2026-09-19'
agent: plan-eng-review
status: approved
---
# P2 方案评审（plan-eng-review，复审第 3 轮，轻量）— TAG0036 MVWU 阶段 1 试点

[PROD_NOT_TOUCHED] 只读评审：未改 `P2-design.md`，未 git add/commit，未触碰 `~/.agate`；B3 复现仅用 scratchpad 临时 git 仓库，已删除；`git status --short agate` 为空。

**结论：approved（0 个阻塞问题）。B3 已闭合；B1/B2/N1-N4 沿用第 2 轮已闭合结论，抽查未被破坏。**

## B3 独立实测

- `P2_DESIGN=<P2-design.md> python3 ~/.agate/scripts/agate-read-p5-commands.py` rc=0，读回 10 条 cmd；逐条 `shlex.split` 全部通过。
- `_history_untouched` 读回 `git diff --exit-code main...HEAD -- agate-workspace/tasks/TAG00\[0-2\]\* agate-workspace/tasks/TAG003\[0-5\]\*`，`shlex.split` 得字面 pathspec `agate-workspace/tasks/TAG00[0-2]*`、`agate-workspace/tasks/TAG003[0-5]*`（末 token 无引号，不触发读取器 strip；bash 不展开、git 自解释 glob）。
- scratchpad 临时仓库（main 含 TAG0010-x/0011-x/0031-x/0032-x/0036-x/0037-x），每例从 main 重建 feat 分支后经 `bash -c` 执行读回命令：

| 变更 | 预期 | 实测 rc |
|------|------|---------|
| 同时删除 TAG0010-x + TAG0031-x（第 2 轮漏检用例） | 1 | **1** |
| 仅删 TAG0011-x | 1 | **1** |
| 改 TAG0032-x | 1 | **1** |
| 给 TAG0010-x 新增文件 | 1 | **1** |
| 新建 TAG0033-y 目录 | 1 | **1** |
| 改 TAG0036-x | 0 | **0** |
| 改 TAG0037-x | 0 | **0** |

  临时仓库及中间文件已删除。

## 抽查未破坏

| 项 | 结果 |
|----|------|
| `check-frontmatter.py P2-design.md` | exit 0 |
| `dispatch_plan` 读回（`agate-md-field-get.py`） | 合法：static-batch，`parallel_limit: 6`，6 批，id 含 `architect-batch-guidance`，complexity 均 ∈ {low, medium} |
| 全部 gate_commands 读回 `shlex.split` | 10/10 通过 |
| M18 范围 | 仍只改 `check-protocol-consistency.py::GATE_SCRIPT_EXEMPT` 加 1 行，锚点表不动，`P5_kernel_diff(_wt)` 不含该文件；BDD-70 落点、R2/R14 一致 |
| `git status --short agate` | 空（`agate/` 无改动） |
| 修订记录如实性 | §7 引号约束已明确"第 1 轮去引号结论对删除不成立，改反斜杠转义"；§9 V8 记录删除/修改/新增/36-37 用例与旧写法对照；§13 增 B3 守护用例（删除须 rc=1，并断言 pathspec 为字面）；§14 B2 行与 §14.1 retry #2 均如实更正，未把第 1 轮错误说法当成仍成立 |

## 最终闭合核对表（B1/B2/B3/N1-N4）

| 项 | 结论 | 依据 |
|----|------|------|
| B1（新脚本致 `test_sg_6` 红 / CHECK9 +1） | 已闭合 | M18 一行豁免；第 2 轮实测 8 passed、CHECK9-coverage 0 新增；本轮 M18 范围抽查未变 |
| B2（末尾引号被 strip） | 已闭合 | 10 条 cmd 读回全部 `shlex.split` 通过；`roles_diff` 中间引号 exclude 语义第 2 轮已实测 |
| B3（history_untouched 对删除漏检） | **已闭合** | 反斜杠转义通配；上表 7 例全符合预期 |
| N1（parallel_limit 与并发≤3） | 已闭合 | §6 强制 dispatch-context 写明波次并发上限 ≤3 |
| N2（批 id 名实不符） | 已闭合 | 读回 `architect-batch-guidance` |
| N3（files_to_read 行号漂移） | 已闭合 | 标题定位 + 修正行号 |
| N4（`~` 与 WARNING 表述） | 已闭合 | 更正为首词含 `/` 被跳过 |

## 架构问题（阻塞级）

- 无。

## 架构问题（非阻塞）

- §9 V7 的 method 段仍保留第 1 轮的"改 TAG0010/0035 → hist 1"等旧写法叙述，但同条 note 已注明"被 retry #2 的 V8 证伪，以 V8 为准"，不构成误导，不必再改。
- 第 1 轮 N5（R8 本机无 `python`）、N6（方案 B 偏陪衬）维持非阻塞。
- 无"后续应重构 / 存在架构债"提案，故无需新增 DEBT 条目。

## 测试缺口

- 无新增。§13 已含 B3 守护（删除历史目录须 rc=1、pathspec 为字面）与读回 `shlex.split` 防复发用例；`test_sg_6` 作为 P4 前应绿的守护保持。

## 锁定决策

1. 采用候选 A（单文件 `check-mvwu.py` + 只读 import `agate_common`），零内核改动；观测器不执行命令、exit 0/2。
2. M18：`GATE_SCRIPT_EXEMPT` 加一行为唯一对 `check-protocol-consistency.py` 的改动；锚点表不动；`P5_kernel_diff(_wt)` 不含该文件。
3. 6 批 static-batch，B1 先行，波 2 并行 ≤3（dispatch-context 强制写明），波 3 依赖终稿；dogfooding 不写 `tests_filter`。
4. `gate_commands` 每 key 独立、无 `&&`、无 `P3_xxx`；任何值经 `agate-read-p5-commands.py` 读回后须可 `shlex.split` 且语义等价于声明意图（含删除类变更）；`P5_history_untouched` 固定为反斜杠转义通配写法。
5. P5 验收口径：`P5_consistency` 0 ERROR、`CHECK9-coverage` 0 新增、`test_sg_6` 绿。
