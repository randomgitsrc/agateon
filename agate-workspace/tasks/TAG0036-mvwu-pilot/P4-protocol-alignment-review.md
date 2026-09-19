---
phase: P4
task_id: TAG0036
parent: P4-implementation.md
trace_id: TAG0036-P4-align-20260919
agent: protocol-alignment-review
type: review
created: 2026-09-19
status: approved
review_date: 2026-09-19
reviewer: protocol-alignment-review
change_summary: MVWU 阶段 1 观测：新增 check-mvwu.py 观测器（六项检查 / 四态 verdict / --observe 七列）+ batches[].tests_filter/output 可选键与 P4-evidence 落点成文（P2/P4 卡、architect、task-files）+ ⑤ 组方法学（decisions/ 约定、Deep Modules 锚点、adr 复审触发、术语）+ M18 豁免一行 + DEBT0043；零内核改动
files_changed: [agate/scripts/check-mvwu.py, agate/scripts/check-protocol-consistency.py, agate/scripts/README.md, agate/tests/README.md, agate/tests/unit/test_check_mvwu.py, agate/tests/unit/test_mvwu_protocol_docs.py, agate/phase-cards/P2-design.md, agate/phase-cards/P4-implementation.md, agate/phase-cards/P7-consistency.md, agate/assets/execution-roles/architect.md, agate/assets/templates/task-files.md, agate/role-system.md, agate/adr.md, agate/CONTEXT.md, CHANGELOG.md, agate-workspace/debt/tech-debt.md]
---

# 协议-脚本对齐审查（TAG0036 P4 收口，重派轮）

> 说明：上一轮因 API 限流中断未产出；本轮所有结论均由本人重新实跑 / 重新核对，`P4-review-progress.md` 的 `[align]` 行仅作参考。只读审查，未改任何代码/文档，未 git add/commit。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | NEEDS_HUMAN_REVIEW（1 条低严重度术语口径，见 A2；不涉行为缺陷） |
| A3 | 一致性连锁 + 反向传播（A3a / A3b） | ALIGNED |
| A4 | 测试覆盖 | ALIGNED（附实跑输出；唯一红灯 = BDD-71，即本文件） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |

零内核改动核对：`P5_kernel_diff_wt` / `P5_roles_diff` / `P5_history_untouched` 均 exit 0（见 A3b / A5）。

---

## A1：文档→脚本对齐

逐条核对协议文档声明与 `agate/scripts/check-mvwu.py` 实现的语义（非关键词存在）：

| 文档声明 | 文档位置 | 脚本实现 | 一致 |
|---|---|---|---|
| `P4-evidence/{batch}.log`，`{batch}` = 批 `id`，须匹配 `[A-Za-z0-9._-]+` | P4 卡:73；P2 卡:135；task-files.md:33 | `ID_RE`（:56）；`_read_evidence` 对不合规 id 直接返回 MISSING，不读文件（:173-174）；路径 `os.path.join(task_dir, "P4-evidence", bid+".log")`（:175） | 是 |
| 逐行 `key: value`，最小内容 command / exit_code / git_head / timestamp / expected_red(默认 `[]`) / duration_seconds / 可选 failed_tests(默认 `[]`) | P4 卡:75-82 | `KV_RE`（:59）、`_parse_evidence`（:158-168，`#` 行与空行忽略，重复键后者覆盖）；command/exit_code/git_head/expected_red/failed_tests 在 `judge_batch`（:258-271）消费；`duration_seconds` 在 `--observe`（:449，`_fmt_duration`）消费 | 是（`timestamp` 脚本不读取，属"记录项"，见下） |
| `git_head` 须为全长 commit 对象名 | P4 卡:79 | `SHA_RE` = 40 或 64 位 hex（:57）；`commit_exists` 用 `git cat-file -e <sha>^{commit}`（:222-226）；缺失/非全长/不存在 → `UNKNOWN reason=git_head`（:270-272） | 是（同时支持 sha256 仓库） |
| `expected_red` / `failed_tests` 为单行 flow 序列、元素为双引号包裹 pytest node id，精确字符串相等比对，不可解析给 UNKNOWN | P4 卡:83 | `_parse_list`（:190-202）：必须以 `[`…`]` 包裹、`yaml.safe_load`、元素须为 str，否则 None；`all(t in set(expected) for t in failed)` 精确相等（:281）；None → `UNKNOWN reason=expected_red`（:273-274） | 是 |
| 记录不阻断 / UNKNOWN 不等价于 PASS | P4 卡:70、84；CONTEXT:41；scripts/README:47 | `main` 恒 return 0（:472），仅用法/目录不存在 return 2（:461-463）；docstring:33-35 | 是 |
| 从不执行 command / tests_filter；只读 | scripts/README:47；docstring | 全文件无 `subprocess` 执行 evidence 命令；`_first_word_ok`（:229-245）仅 `shlex.split` + `shutil.which`/`os.access`；写文件路径为零（仅 `open(..., "rb")`） | 是 |
| 六项检查顺序 = reason 优先级：tests_filter → evidence → command → exit_code → git_head → expected_red | docstring:27-28；README | `judge_batch`（:251-283）顺序完全一致；唯一附加：exit_code=0 且 failed_tests 非空 → `UNKNOWN reason=exit_code`（:268-269，先于 git_head，自相矛盾的证据判 UNKNOWN，不放行） | 是 |
| 四态 verdict：exit_code=0→PASS；非零且无 expected_red→FAIL；非零且 failed_tests 非空且全部命中 expected_red→EXPECTED_RED；预期外红灯→FAIL；无法核对→UNKNOWN | docstring:30-31；CONTEXT:41 | :275-283（非零、expected 非空但 failed 为空 → UNKNOWN reason=expected_red，即"无法核对"，不当作 EXPECTED_RED，fail-closed 方向） | 是 |
| 契约行 `MVWU_RESULT: <VERDICT> batch=<id>[ reason=<token>]`；无批时 `MVWU_RESULT: UNKNOWN batch=- reason=tests_filter` | docstring:13-18；README:47 | `render_contract`（:286-288）、`NO_BATCH_LINE`（:68）；`_load_batches`（:78-96）对 P2 缺失/无 dispatch_plan/空 batches 返回 None | 是 |
| `--observe` 7 列 `| MVWU | tests_filter | 耗时 | evidence | commit 形态 | boundary | verdict |`，无表头，诊断走 stderr | docstring:22-25；README:47 | `_run`（:447-452）七个 cell 顺序与之吻合；`_warn` 只写 stderr（:71-72）；无批时七列占位行（:418） | 是 |
| `|` 转义 / 不合规 id 打印形态（口径 D） | docstring:19-20 | `_escape_cell`（:116-133，`\|`、反引号、`\\`、控制符转义）；`_encode_id`（:102-113，不合规字节 `\xNN`，非字符串/空 `?`） | 是 |
| git 区间口径：任务分支相对默认分支 `merge-base..HEAD`，基线不可确定诚实 UNKNOWN，不参与 verdict | docstring:24-25；P1 口径 E | `_default_branch_base`（:294-313：origin/HEAD → main → master；空区间/无基线 → None）；`_collect_range`（:316-334，`--no-merges`）；`_forms_and_boundaries`（:362-393）不回写 verdict | 是 |
| `output`（可选）仅供 `--observe` 读取，写错不影响 gate | P2 卡:136；architect.md:266 | `_norm_output`（:349-359）非 list/非 str 元素 → None → boundary UNKNOWN；`check-gate.py` 未改（零内核 diff 实证，见 A3b） | 是 |
| `tests_filter` 缺省 → 该批只是不产生批级证据，gate 行为不变 | P2 卡:133 | 脚本对缺 `tests_filter` 的批判 `UNKNOWN reason=tests_filter`（:253-255）；对现存任务目录实跑（本任务目录）输出 6 行诚实 UNKNOWN、rc=0、无 traceback | 是 |

**实跑核对**（worktree 根）：
- `python3 agate/scripts/check-mvwu.py agate-workspace/tasks/TAG0036-mvwu-pilot` → 6 行 `MVWU_RESULT: UNKNOWN batch=<id> reason=tests_filter`，rc=0（本任务 P2 各批未声明 `tests_filter`——诚实 UNKNOWN，符合 BDD-39/56 对"存量任务须给诚实 UNKNOWN 而非崩溃"的要求）。
- `--observe` 同目录 → 6 行 7 列 `| <id> | - | - | no | UNKNOWN | UNKNOWN | UNKNOWN |`，rc=0。
- `check-mvwu.py /nonexist` → stderr 提示、rc=2。

**备注（不构成 MISALIGNED）**：P4 卡:79 列出 `timestamp` 为最小内容键，脚本未读取该键。这符合"最小内容 = 记录方须写的字段，观测器只消费判定所需字段"的口径（P1 §2 ②），且观测器缺 `timestamp` 不误判；不改结论。

**结论**：ALIGNED

---

## A2：脚本→文档对齐

脚本行为对应的文档已同步：
- `scripts/README.md:47` 新增 `check-mvwu.py` 行：输入（`P2-design.md` 的 `dispatch_plan.batches` + `P4-evidence/<id>.log`）、契约行格式、四态 verdict、`--observe` 七列、"仅观测不阻断（不挂 gate/hook/CI）"、退出码 `0=任一 verdict（含 FAIL/UNKNOWN，不阻断）, 2=用法/目标错误`——与脚本 :472/:463 一致。
- `tests/README.md:88-89` 登记 `test_check_mvwu.py`（109）与 `test_mvwu_protocol_docs.py`（65）；实测 `count-tests.sh` 口径下总数 1842（= 1668+109+65），与全量 pytest 1839 passed + 1 failed + 2 skipped = 1842 吻合。
- P4 卡:69-85、P2 卡:123-140、task-files.md:33/253、architect.md:234-266：口径与脚本一致（见 A1 表）。

**NEEDS_HUMAN_REVIEW（1 条，低严重度术语口径）**：`agate/CONTEXT.md:42` 定义 `boundary(I1)` 为"批声明的 `output` 文件集与该批 commit 实际改动集的比对（**相等为 PASS，改了未声明的文件为 FAIL**），仅由 `check-mvwu.py --observe` 观察"。该措辞取自设计文档 §3.1 的不变量语义（`design-mvwu-protocol.md:129-131`，I1 PASS/FAIL/WARN），但观察器实际在 boundary 列输出的取值是 `exact` / `mismatch` / `UNKNOWN`（`check-mvwu.py:392` `"exact" if changed == out else "mismatch"`，:389 `UNKNOWN`；P1 BDD-51/53/54 明确用 `exact`/`mismatch`）。读者按 CONTEXT 术语去 `--observe` 输出里找 `PASS`/`FAIL` 会对不上；另设计文档的 WARN 情形（声明了没改）在脚本中并入 `mismatch`，CONTEXT 未提。
- 这是术语层的一处口径不精确，不是行为错误：I1 的概念定义（PASS/FAIL）与观察器的三值输出是两个层面，P1 BDD-59 也只要求"boundary（含 I1）"行存在且首次定义位置非空，测试全绿。
- 是否需要在 CONTEXT:42 补半句"观察列取值 `exact` / `mismatch` / `UNKNOWN`"属措辞取舍（补则更自洽；不补亦不影响任何 gate 或测试），故标 NEEDS_HUMAN_REVIEW 而非猜测。
- 建议（可选）：CONTEXT:42 括号后追加"（`--observe` 列取值 `exact`/`mismatch`/`UNKNOWN`）"。
- [HUMAN_CONFIRMED: 待人工确认——主 Agent / 人工在 commit 前二选一：接受现状，或经 implementer 补半句后重审]

**结论**：NEEDS_HUMAN_REVIEW（仅此一条；其余脚本→文档同步项均 ALIGNED）

---

## A3：一致性连锁 + 反向传播

### A3a 连锁（已知衍生改动，均在 diff 中且已落地）

| 变更源 | 衍生文档 | 是否落地 |
|---|---|---|
| 新脚本 `check-mvwu.py` | `scripts/README.md:47`（脚本表）、`tests/README.md:88-89`（测试映射）、`check-protocol-consistency.py:808`（M18 豁免） | 是 |
| `tests_filter`/`output` 契约（P2 卡 :123-140） | `architect.md:234-266`（引用而不复述契约，见其 :236 "权威定义在 P2 卡…本节只写怎么选"）、`task-files.md:253`（dispatch_plan 示例注释） | 是 |
| `P4-evidence` 落点（P4 卡 :69-85） | `task-files.md:33`（阶段产出表 P4 行）、`CONTEXT.md:41` | 是 |
| ⑤ 组（decisions/、Deep Modules、复审触发） | `P2-design.md:27-36`、`P7-consistency.md:36`、`role-system.md:205-217`、`adr.md:6-10` | 是 |
| 术语 | `CONTEXT.md:38-42`（5 行，只追加） | 是 |
| DEBT0043 登记 | `tech-debt.md:1488-`；`check-debt.py` 实跑 rc=0（schema 通过） | 是 |

### A3b 反向传播（应受影响但不在 diff 中的文件，逐一验证）

| 文件 | 判断 | 验证 |
|---|---|---|
| `agate/dispatch-protocol.md`（`batches` 字段说明是否需提 `tests_filter`） | **复核 P1 §4.2 "不处理"判断：成立** | 文件中 `dispatch_plan` 仅在 :592、:635、:644、:659 出现，均为编排/并行规则叙述，**没有**逐字段列举 `batches[]` 键的字段表，因此无需为可选嵌套键补说明；`tests_filter`/`output` 的权威定义在 P2 卡（P0-brief 指定落点）。且该文件属 `P5_kernel_diff_wt` 零内核清单内（白名单/黑名单同源 `check-judge-verdict.py`），改动会触及 P6.5 语义面——`git diff HEAD` 为空。不构成断链：`grep "P4-evidence\|tests_filter\|check-mvwu" dispatch-protocol.md` 命中 0，白名单默认拒绝，P4-evidence 不在其内即受限 |
| `agate/orchestrator-template.md` / `agate/WORKFLOW.md` | 不需要同步 | 二者无逐字段/逐产出文件登记 P4 批级产物（WORKFLOW :324/:336/:356-357 为 P6/P6.5 gate 描述、pre-commit 总览）；`check-mvwu.py` **不触发 pre-commit**，按角色文件反向传播表"仅新增/修改 pre-commit 触发行为才需同步 WORKFLOW「Pre-commit 检查总览」"，故不加行；grep 三关键词命中 0 |
| `agate/SETUP.md` / `agate/state-machine.md` / `agate/LIMITATIONS.md` | 不需要 | 无阶段产出/转移条件/局限变化；grep 命中 0 |
| `agate/rules/*.yaml`（`P4-evidence` 不应出现） | 符合 | `grep -rn "P4-evidence\|tests_filter\|check-mvwu" agate/rules` 命中 0；`agate/rules/phases.yaml`、`agate/rules/schema` 在零内核 diff 清单内且 `git diff HEAD` 为空 |
| `agate/UPGRADING.md`（发布时写，本任务不应改） | 符合 | 不在 `git status` 改动集；CHANGELOG `[Unreleased]` 为 TAG0036 唯一落点 |
| `agate/assets/execution-roles/implementer.md`（是否需知 `P4-evidence`） | 不构成断链 | P4-evidence 由**主 Agent**在批 commit 前机械转录（P4 卡:74），不是 implementer 产出；implementer 角色卡未提及、亦无相反说法（grep 命中 0）；P1/P2 已判"不改" |
| 其余 `execution-roles/*.md` | `P5_roles_diff`（除 architect.md）exit 0 | 见 A5 |
| `agate/scripts/agate-frontmatter-check.py` / `check-structure-consistency.py` / `agate-md-field-get.py`（反向传播表"frontmatter 字段集"路径） | 不需要 | `tests_filter`/`output` 嵌套在 `dispatch_plan` 内（`JSON_FIELDS = {"dispatch_plan"}` frontmatter-only），不产生新顶层键；三脚本 `git diff HEAD` 空 |
| `AGENTS.md` / 根 `README.md` 脚本清单 | 不需要 | 二者不逐脚本列举（`grep check-platform-assumptions.py` 仅命中 UPGRADING）；脚本清单权威为 `scripts/README.md` |
| `check-protocol-consistency.py` CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` | 不动（见 A6） | — |

**零内核改动实测**（`P2_DESIGN=… python3 ~/.agate/scripts/agate-read-p5-commands.py` 读回后逐字执行）：
- `P5_kernel_diff_wt`（`git diff --exit-code HEAD -- <22 条路径>`）→ **rc=0**
- `P5_roles_diff`（`git diff --exit-code main...HEAD -- ':(exclude)…architect.md' agate/assets/execution-roles`）→ **rc=0**；另以 `HEAD` 工作树口径复核同一路径集 → rc=0
- `P5_history_untouched`（`TAG00[0-2]*` / `TAG003[0-5]*`）→ **rc=0**
- `P5_kernel_diff`（`main...HEAD`，节选核心路径）→ rc=0
- 无需列出 MISALIGNED。

**结论**：ALIGNED

---

## A4：测试覆盖

**新逻辑均有 pytest 覆盖**：
- `agate/tests/unit/test_check_mvwu.py`（109 用例）：覆盖六项检查顺序、四态 verdict 边界、契约行/观察表行格式、`|` 转义、不合规 id、重复 id、符号链接逃逸、git 区间口径（origin/HEAD/main/master/无基线/空区间）、`--observe` boundary（exact/mismatch/UNKNOWN、merged commit、workspace 前缀）、从不执行 command、退出码 0/2。
- `agate/tests/unit/test_mvwu_protocol_docs.py`（65 用例）：P2/P4 卡、architect、task-files、CONTEXT、role-system、adr、P7、CHANGELOG、tech-debt、scripts/README、tests/README 的字面标记与 BDD-71。
- 唯一被本任务改动的既有测试文件为 `test_mvwu_protocol_docs.py` 首部一行注释（`/tmp` 字面量表述改写，平台扫描 R 类命中所致），无逻辑变化。

**本人实跑输出**（CI 口径，worktree 根，2026-09-19）：

```
$ timeout 580 python3 -m pytest agate/tests/ --reruns 1 -n auto -q -p no:cacheprovider
...
FAILED agate/tests/unit/test_mvwu_protocol_docs.py::test_bdd_71_p4_protocol_alignment_review_exists_with_conclusion
1 failed, 1839 passed, 2 skipped, 1 rerun in 42.81s
```

- 唯一失败即 BDD-71 的**预期红**（断言 `P4-protocol-alignment-review.md` 存在且含 approved/rejected 结论字样——本文件写出后转绿）；其余 1839 passed，2 skipped 与既往基线一致；无其他失败。1 rerun 属并行 flaky 重试（一次 `R`，重试后 `.` 通过）。
- 同环境其它 P5 口径实跑：`ruff check agate/` → All checks passed；`check-protocol-consistency.py --strict-errors-only` → 仅 367 WARNING、0 ERROR；`grep CHECK9-coverage` 命中 0（无新增覆盖 WARNING）；`check-platform-assumptions.py agate/tests` → rc=0；`check-debt.py tech-debt.md` → rc=0。
- 边界评价：`_first_word_ok` 仅首词检查等"已知局限"在脚本 docstring:37-41 字面声明并有对应用例，不属遗漏。

**结论**：ALIGNED（有实跑输出；除本文件缺失导致的 BDD-71 预期红外无其他失败）

---

## A5：下游影响 + 文档传播

- **既有项目 gate 行为零影响**：
  - `tests_filter`/`output` 为 `dispatch_plan.batches[]` **可选嵌套键**；`check-gate.py::_gate_p2_dispatch_plan`（:767-）本任务**未改**（零内核 diff rc=0），其"不拒未知键"（P1 §1 判据 1 已读源码确认）保证含新键的 P2 仍通过；缺省时行为与之前完全一致（P2 卡:133）。
  - `check-mvwu.py` 不被 `pre-commit-gate`/`pre-push-gate`/CI/hook 调用（`grep -rn check-mvwu agate/rules agate/dispatch-protocol.md agate/WORKFLOW.md …` 命中 0；仅在脚本表 / 测试 / M18 豁免中出现），退出码永不为 1，不可能令流程失败。
  - `P4-evidence/` 目录：不在 `agate/rules/*.yaml`、`dispatch-protocol.md` judge 白名单/黑名单、`check-p6-provenance.py`、`check-judge-verdict.py`、`agate-archive-stale-outputs.py`、`phases.yaml` 目录登记面（均在零内核清单且 diff 空；grep 命中 0）。P4 卡:85 已声明"不进 judge 白名单，P6.5 judge 不读取它"，与 dispatch-protocol 白名单"默认拒绝"机制一致。
- **CHANGELOG.md `[Unreleased]`（CHANGELOG.md:11-26）**：新增 `### 新增（TAG0036：MVWU 阶段 1 观测，RM-AG0063）`，四条 bullet（观测器 / `tests_filter` 可选键 / `P4-evidence` 落点 / ⑤ 组方法学），明确"仅观测、不阻断，不挂 gate / hook / CI"、"可选，缺省不影响既有任务"；**未**出现"机制已生效/已验证有效"类宣称（用"成文"表述，role-system.md:215 也明示"其实际效果尚未做任何验证，不作有效性宣称"）。无破坏性变更，故无需标注 BREAKING。UPGRADING.md 未改（发布时写）。
- **文档传播**：orchestrator-template / WORKFLOW / dispatch-protocol / state-machine / LIMITATIONS / SETUP / implementer 均已按 A3b 逐一核对，无需同步；`P7-consistency.md:36` 新增第 6 项检查清单条目仅为核对而非新增 gate。
- **DEBT 处理**：DEBT0043（`_gate_p2_dispatch_plan` 三处 `return None` fail-open）登记与实证一致——`check-gate.py:769-776` 实读为 `if not raw: return None` / `except ValueError: return None` / `if not isinstance(plan, dict): return None`，行号与条目"767 行起、769-770/772-774/775-776"完全吻合；本任务"只登记不修"符合零内核硬约束。P7 卡:36 引用的 DEBT0039 为已 closed 的同主题（"补协议文档正文误标 P7"）教训条目，仅作依据，不构成断链。

**结论**：ALIGNED

---

## A6：锚点表覆盖

- **M18**：`check-protocol-consistency.py:805-808` `GATE_SCRIPT_EXEMPT` 增一行 `"agate/scripts/check-mvwu.py",  # 观测脚本，不挂 gate`，与既有两条（自身 / `pre-commit-gate.py`）同性质豁免（不承载 gate 判定）。该行是脚本内**唯一**改动（diff 仅 +1 行），且不在零内核清单内（合法，P2 §7 已核对）。
- **CHECK9-coverage 无新增 WARNING**：`python3 agate/scripts/check-protocol-consistency.py | grep CHECK9-coverage` 命中 0；全量 `test_sg_6_check9_anchor_table_covers_all_gate_scripts` 在本人 pytest 实跑中通过。
- **`SCRIPT_ALIGNMENT_ANCHORS` 未动合理**：锚点表验证的是"gate 脚本存在且被正确挂载调用"；`check-mvwu.py` 是不挂 gate 的观测器，无"被挂载"事实可锚定，加锚点反而制造虚假强约束（与 role 文件 A6 说明"锚点验证的是挂载而非语义"一致）；其语义对齐由 A1 逐条人工核对与 `test_mvwu_protocol_docs.py` 字面断言承担。
- 新增协议规则（decisions/ 约定、Deep Modules 锚点、复审触发）均为指导性/成文性，无脚本可挂，不入锚点表。

**结论**：ALIGNED

---

## A7：设计原则一致性（ADR）

逐条核对相关 ADR：

- **ADR-003 最小约定/不绑定技术栈（adr.md:75-97）**：
  - ⑤-d Walking Skeleton 的处理：P2 卡:140 与 architect.md:244 均写"骨架先跑通"部分**吸收**进判据一（Tracer Bullet）、"自动化部署 / CI 配置"部分**拒绝**并明确引用 `adr.md` ADR-003；同时声明它与既有 `P2-skeleton.md`（`project_phase: bootstrap` 目录布局声明）不是同一机制、不新增字段/gate/模板文件。拒绝理由与 ADR-003"不硬编码语言/框架/部署方式"完全同向。
  - ⑤-c 三判据不规定具体架构工具：P2 卡:193-207 "agate 不规定具体工具……命令仍经 `gate_commands` 注入……只要求该维度存在……项目判定无架构约束时写明即可，不强制"，与 ADR-003"技术栈相关命令通过 `gate_commands` 注入"一致（示例维度依赖方向/分层/循环依赖/API 稳定性均为技术栈中立概念，无具体工具名）。`tests_filter` 示例写 `python -m pytest …` 仅作示意，并明示以 `AGATE_PYTHON` 探测为准（P2 卡:134；architect.md:265）。
- **ADR-002 可判定性（adr.md:47-73）**：`tests_filter`/`output`/decisions/ 均明示"不新增 gate 校验 / 不由 gate 校验"，未把指导性判据伪装成机器判定；`check-mvwu.py` 明确"仅观测、不阻断"，UNKNOWN 不当 PASS——与 ADR-002"语义正确性由 subagent/review 保证、gate 只判可判定项"及 ADR-011（引导型工具非安全边界）同向，且不产生新的静默放行路径（UNKNOWN 而非 PASS）。
- **ADR-013 gate 生产者无关（adr.md:435-）/ ADR-004 安全网分层**：`P4-evidence` 由主 Agent 机械转录、观测器事后只读，不引入"谁生产"的 gate 分支；不挂 hook，不改安全网分层。
- **⑤-b Deep Modules 审查锚点（role-system.md:205-217）与既有"不规定步骤"哲学**：锚点问"是否把实现细节写进接口/是否规定第 N 步做 A"，判据"资源地图 + 判据，不给步骤脚本"，与 `implementer.md:15`、`architect.md:15`（"files_to_read 是资源地图，不告诉你按什么顺序做"）同源；并显式豁免"阶段间的协议约束（按序落盘、先红后绿）"，避免与阶段卡既有流程序号冲突；`范围声明`明示"不改动既有角色文件行为、不新增机械检查、不作有效性宣称"。审查锚点与批切分判据"正交"（:213）。一致。
- **`adr.md` 新增「复审触发条件（过时不删）」节（adr.md:6-10）**：与既有 ADR 一致——(a) 在既有 ADR 体例（"状态：已接受"等）之外新增文件头元规则，未修改任何既有 ADR 条目；(b) 与 ADR-008/ADR-009 已有"v0.50.0 论据复核 / 就地复核"先例一致（ADR-008 :267 已在原条目就地复核而不删除），本节把这个先例升格为显式规则；(c) 明确"人工判断、不设自动失效或阻断流程"，不与 ADR-002 冲突；(d) 不绑定技术栈。
- **`decisions/` 落点（P2 卡:29-36）与工作区约定**：`{AGATE_WORKSPACE}/decisions/` 属项目侧、与协议层 `adr.md` 明确分离（P2 卡:31）；"具体文件名与模板不作规定，由项目自定"，"读取与登记的约定，不由 gate 校验，也不设自动过期机制"——不引入新 gate/模板，与 ADR-003 最小约定一致。`decisions/` 属项目工作区子目录，P2-design.md §0（:65、:68、:188-189）已核对：state-machine/SETUP/orchestrator-template 中"创建 decisions/ 目录"的语句仍准确（缺的是写入方而非创建方），本节不改目录约定，且为"若项目存在该目录则读取"的条件式，缺省不影响。
- **是否发现未记录的架构决策**：本任务的两项新增（⑤-b 审查锚点、`decisions/` 落点）均属指导性成文，已由 role-system.md / P2 卡承载，未涉及需新 ADR 的结构性取舍；复审触发条件本身已在 adr.md 头部成文。**无需补 ADR**（可选：`decisions/` 与 `adr.md` 的分层关系已在 P2 卡:31 交代，不必另立）。

**结论**：ALIGNED

---

## 最终结论

- 全部 A1-A7：A1/A3/A4/A5/A6/A7 **ALIGNED**；A2 含 1 条 **NEEDS_HUMAN_REVIEW**（CONTEXT.md:42 `boundary(I1)` 用设计文档 I1 的 PASS/FAIL 措辞，而观察器列取值为 `exact`/`mismatch`/`UNKNOWN`；低严重度术语口径，非行为缺陷，非本任务实现缺陷，测试与 gate 均不受影响）。
- **无 MISALIGNED**；零内核改动核对全部 exit 0；全量 pytest：1 failed（BDD-71，预期，本文件产出后转绿）/ 1839 passed / 2 skipped；ruff 干净；CHECK9-coverage 无新增 WARNING；CHANGELOG 如实。
- **status: approved**（仅 NEEDS_HUMAN_REVIEW 1 条且不涉本任务缺陷）。待办：commit 前由主 Agent / 人工对 A2 的 NEEDS_HUMAN_REVIEW 二选一——接受现状（补 `[HUMAN_CONFIRMED: 日期 确认：理由]`），或经 implementer 在 CONTEXT.md:42 补一句观察列取值后无需重审（纯措辞，`test_mvwu_protocol_docs.py` 对该行只断言行存在与三列格式）。
