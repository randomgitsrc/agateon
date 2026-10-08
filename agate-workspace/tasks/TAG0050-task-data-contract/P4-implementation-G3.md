---
phase: P4
task_id: TAG0050
type: implementation
batch: G3-fix
parent: P2-design.md
trace_id: TAG0050-P4-G3-fix-20261008
status: implemented
agent: implementer
implementation_dir: agate/
---

# P4 实现 — 批次 G3（D + E + F）· SELF-GATE 整改（第 2 轮）

> 依据：`P4-dispatch-context-implementer-G3-fix.md`、`docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G3.md`
> （整改依据，含「闭合后…清单」）、设计 §5/§6/§7、`P2-design.md` §3/§11。
> 前置：第 1 轮 G3（HEAD `b746d07d`，未提交）的 8 条 `[DESIGN_GAP]` 被对齐审查判
> **GAP-1/2/4/5/6/7/8 必须闭合**（GAP-3 可接受）；A1–A5 缺口同轮修。

## 0. G3-0：E2 往返成本结论 + 主 Agent 裁定

**问题**：比较「命令写入 + 当场校验的派发轮次 / token」vs「写散文 → gate 失败 → 回退」。

**实测（第 1 轮，本机 `/tmp/opencode/e2`，未接触生产）**：命令写入路径 **gate 失败 0 次**、
错误当场给出；散文路径 **gate 失败 ≥1 次**、错误到 P7 gate 才暴露；token 增量 < 80 字符/条，
远低于 >20% 代价阈值。

> **[HUMAN_CONFIRMED: 2026-10-08 确认：E2 判据采信实现者重释]**
> P2 §11 字面「第二种 gate 失败次数不多于第一种」方向自相矛盾（会要求散文优于结构化，与设计目标
> 相反）；**采信**「结构化写入**不增加** gate 失败次数」之重释。实现者数据（命令 0 次 / 散文 ≥1 次）
> 与重释一致。原始数据与重释均保留在本节。

## 1. 批 D — 验收结论与证据绑定（BDD-56..60）：判据 D1–D10 全部落地

| 判据 | 落点 | 状态 |
|---|---|---|
| D1（bdd 集合与 P1 相等 + 不重复） | `check-gate.py::_gate_p6_structured` | ✅ |
| D2（verdict 全 PASS） | 同上 | ✅ |
| D3（`resolve_evidence_ref` 解析 + ignore 检查 + **pre-commit「已跟踪或已暂存」**） | 同上 + `_is_tracked_or_staged`（GAP-6） | ✅ |
| D4（P6-evidence 全被引用） | 同上 | ✅ |
| **D5（内容相同 → WARNING 可共享引用）** | 同上（GAP-6 新增） | ✅ |
| D6（PASS 日志 `EXIT_CODE=0`） | 同上 | ✅ |
| **D7（evidence JSON 与 results 结论一致，取代审计 6）** | 同上（GAP-6 新增） | ✅ |
| D8（截图须 vision / manual_review） | 同上 | ✅ |
| **D9（审计 7 从 `results` 读取复用声明）** | 同上 + `_p6_reuse_blocked`（GAP-6 新增） | ✅ |
| D10（渲染块一致） | `_check_render_blocks` | ✅ |

- **GAP-1 闭合**：`gate_p6` 非 legacy 分支改由**契约单源**判定（`requirement_active(task_dir,
  "results", "P6") is True`），缺 `results` 时 `_gate_p6_structured` 报 ERROR（不再回退正文/汇总）。
  快照 `requires.results` 由 `false` **翻真**为 `true`（A1 的「声明↔执行单源」）。
- `check-judge-verdict.py` 非 legacy 读 `criteria`（`criteria_total`/`criteria_passed`/`verdict_evidence` 现算）。
- `agate-run --task` + `run:<k>`（第 1 轮交付，未改）。
- `agate-extract-context.py` 非 legacy P7/P8 计数经 md-field-get 现算（第 1 轮交付，未改）。

## 2. 批 E — 成对声明（BDD-61..66）

第 1 轮交付的聚合/ID/`basis`/标记登记保持不变；**GAP-8 闭合**：

- 快照 `declaration_files` 由 6 个主产出**扩展为 glob 面**（各阶段主产出 + `*-review.md` +
  `P4-implementation-*.md` + `P4-implementation/**/*.md`），**删除设计外新键 `declaration_globs`**（单源回归设计 §6）。
- 消费方同步：`check-gate._declaration_globs`、`check-scope-resolved.py`、`check-retrospective.py`
  改读 `declaration_files`；`check-frontmatter.py` / `pre-commit-gate.py` / `agate-md-field-set.py`
  改按 **glob（相对路径 + basename）** 匹配声明文件。

## 3. 批 F — 代理判定（BDD-67..72）

| 交付物 | 状态 |
|---|---|
| P1-review `reviewed_bdds` **必填且 = P1 BDD 集合**（GAP-2 闭合，缺省即 ERROR） | ✅ |
| P2 `ui_design` **必填维度**由快照 `ui_design.shape_dimensions`（shape→slots）决定（GAP-5） | ✅ |
| P2 UI `na` 检查**加 `task_level` 门**（A5：legacy 不变，§8） | ✅ |
| `:964` 骨架标题级判定（RM-AG0085，对所有任务） | ✅ |
| P8 `delivery` 结构化（F12），规格改读快照 `delivery`（GAP-5） | ✅ |
| `check-pruning.py` 读 frontmatter + `pruned` **恒检闭合**（GAP-4） | ✅ |
| T2 绊线（置于 `reviewed_bdds` 之前，避免集合差掩盖格式问题） | ✅ |

- **GAP-4 闭合（主裁定 (a)）**：快照 `phase_universe` 改为 `[P1..P8]`（排除 P0/P6.5）；
  `check-pruning` 对**非 legacy 任务恒检** `set(phases) ∪ set(pruned.phase) == phase_universe`
  且不相交（不再"仅声明 pruned 时"）；`pruned` 条目须含快照 `pruned.required_fields`
  （`[phase, reason, risk]`）。
- **GAP-5 闭合**：快照注册 `ui_design`（`shape_dimensions`）/`delivery`/`pruned`；gate 改读快照；
  补「必填维度存在」判据。

## 4. [DESIGN_GAP] 登记（第 1 轮）— 逐条处置

> 第 1 轮 8 条 `[DESIGN_GAP]` 均已被对齐审查裁定；本轮的处置如下（**原登记保留在
> `P4-dispatch-context-implementer-G3-fix.md` / 审查报告 §DESIGN_GAP 逐条裁定**）：

| GAP | 第 1 轮登记 | 本轮处置 |
|---|---|---|
| GAP-1 | 非 legacy P6 缺 `results` 回退 | **闭合**（规则单源 + 缺即 ERROR + 夹具更新） |
| GAP-2 | `reviewed_bdds` 仅已声明时校验 | **闭合**（必填 + 夹具更新） |
| GAP-3 | `agate-extract-context` 单参形式 | **可接受（附条件）**：补文档（`agate/scripts/README.md`） |
| GAP-4 | `phases ∪ pruned` 仅声明时检查 | **闭合**（恒检 + `phase_universe` 裁定 + 夹具更新） |
| GAP-5 | F 批字段判据硬编码 | **闭合**（快照注册 + gate 读快照 + 必填维度判据） |
| GAP-6 | D5/D7/D9 与 D3 pre-commit 未实现 | **闭合**（实现 + 新测试） |
| GAP-7 | provenance 非 legacy 跳过未实现 | **闭合**（审计 6 + 正文解析按 `task_level` 跳过，与 D7 成对） |
| GAP-8 | `declaration_files` 未扩展 | **闭合**（扩展为 glob + 删 `declaration_globs` + 消费方同步） |

## 5. A1–A5 缺口闭合

- **A1**：`UPGRADING.md` 未发布节去掉过度承诺（D1–D10 只列**实际落地**项）；`requires.results`
  与执行面**单源**（翻真 + gate 读 `requirement_active`）。CHANGELOG 同步改写。
- **A2**：`agate-extract-context.py` 单参形式**已登记**（`agate/scripts/README.md`）；
  `declaration_globs` 删除说明同步；`check-pruning`/`check-scope-resolved`/`check-retrospective`/
  `check-judge-verdict` 的**行为变化**补进 README 工具表。
- **A3**（反向传播，本批补齐）：`assets/templates/task-files.md` + `phase-cards/{P1,P2,P6,P7,P8}`
  的 frontmatter 样例块补新字段（`results`/`reviewed_bdds`/`pruned`/`ui_design`/`delivery` 结构化/
  `findings`/`design_gap_reviews`/`code_map_reviewed`）；`execution-roles/{verifier,consistency-reviewer}`、
  `review-roles/requirements-review`、`phase-cards/P8-release` 指导写结构化字段；
  `WORKFLOW.md`「Pre-commit 检查总览」补 `check-p6-format` 跳过行为与非 legacy 分支说明。
  （P6.5 无独立 phase card——不适用，已在 WORKFLOW/卡片中以 P6 承载。）
- **A4**（测试判别力补强）：`test_bdd_56` 覆盖 F1 的 A（改 FAIL）/B（删条目）/C（重复）；
  `test_bdd_57/58` 改走 **`gate_p6`** 新 D3/D6（非旧 `check-p6-evidence.py` 路径）；
  `test_bdd_59` **构造 sha256 不一致**；`test_bdd_60` **断言计数 == 现算值**；`test_bdd_62/64/65`
  加判别性断言；新增 `D5`/`D7`/`D9`/`GAP-5`/`GAP-7`/`GAP-8` 测试。
- **A5**：`gate_p2` UI `na` 检查加 `task_level` 门（见 §3）；**R6 双向差分复跑**结果见 §7。

## 6. 改动文件清单

**修改**（相对第 1 轮 G3 的增量以 ★ 标注）：
- ★ `agate/rules/task-data/level-1.yaml`（`requires.results: true`；`phase_universe` 改 `[P1..P8]`；
  新增 `ui_design`/`delivery`/`pruned`；`declaration_files` 扩展为 glob、删 `declaration_globs`）
- ★ `agate/rules/task-data/LEVELS.yaml`（重登记 level-1.yaml LF 归一 sha256）
- ★ `agate/scripts/check-gate.py`（GAP-1/2/5）；★ `agate/scripts/check-pruning.py`（GAP-4）
- ★ `agate/scripts/check-p6-provenance.py`（GAP-7）；★ `agate/scripts/check-frontmatter.py`（GAP-8）
- ★ `agate/scripts/pre-commit-gate.py`（GAP-8 + `AGATE_PRECOMMIT_GATE` 标记）
- ★ `agate/scripts/agate-md-field-set.py`（GAP-8 glob 匹配）；★ `agate/scripts/check-scope-resolved.py` / `check-retrospective.py`（GAP-8）
- ★ `agate/tests/conftest.py`（`init_task` P1-review 加 `reviewed_bdds`）
- ★ `agate/tests/integration/test_pre_commit_hook.py`（`_P1_REQ`/it9/it9b/it10/T086/`_write_p1_review` 夹具）
- ★ `agate/tests/integration/test_tag0050_evidence.py` / `agate/tests/unit/test_tag0050_declarations.py` / `test_tag0050_proxy_judgment.py`（新测试 + 判别力补强）
- ★ `agate/UPGRADING.md` / `CHANGELOG.md` / `agate/scripts/README.md` / `agate/WORKFLOW.md`
- ★ `agate/assets/templates/task-files.md` / `phase-cards/{P1,P2,P6,P7,P8}-*.md` / `execution-roles/{verifier,consistency-reviewer}.md` / `review-roles/requirements-review.md`
- （第 1 轮已改：`markers.yaml`/`markers.schema.json`/`gitignore-fragment.txt`/`tech-debt-template.md`/`agate_common.py`/`agate-debt-check.py`/`agate-extract-context.py`/`agate-run.py`/`check-judge-verdict.py`）

**新增**：本文件 + `P4-progress.md` 追加（无新增代码/测试文件、无新增 `agate/scripts/` 文件）。

**登记面**：本批不新增 `agate/scripts/` 文件 → CHECK9/SG.6/CHECK10 无新增动作。

## 7. 自查结果（自查 ≠ gate）

- 目标文件（evidence/declarations/proxy_judgment/cross_batch/fitness + pre_commit_hook）→ **94 passed**。
- `pytest agate/tests/ -q --tb=line -n auto` → **2840 passed / 2 skipped / 1 failed**；唯一 failed =
  `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（**既有环境漂移**：
  本机 `opencode debug agent` 已更名为 `debug agents`；P3 已登记为非本任务失败）。
- `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（基线；CHECK 16 快照冻结通过）。
- `python3 agate/scripts/check-platform-assumptions.py` → **rc=0**。
- `bash agate/tests/scripts/count-tests.sh` → **2850**（+7：本批新增测试）。
- **R6 双向差分**（`bash docs/design-notes/r6-differential.sh --corpus .`，仓外 `cp -r` 副本、副本内
  提交使树干净后运行）：`before=720c97d3`（v0.79.0）、`after=<副本>/agate` →
  **legacy 任务 39 个，差异 0 条，未匹配 0 条，exit 0**（差异全在 allowlist：0 条即无未允许差异；
  §8 承诺「legacy 退出码与 ERROR 集合不变」成立）。

## 8. 环境隔离

- [PROD_NOT_TOUCHED] 全程仅在 `agateon` 本 checkout 改代码/文档 + 跑 pytest（`tmp_path` / `/tmp/opencode`）
  + R6 于 `/tmp/opencode/r6copy` **仓外副本**运行（副本内提交使树干净，跑毕删除）；未接触生产环境。
- 真实仓库 `git status --porcelain` 仅列本批改动 + 未跟踪派发/进度/审查文件，**无账本污染**。

## 9. C8 整改（第 2 轮，2026-10-09）

> 输入：`P4-review-G3.md`（BLOCKER-1 + MINOR-2/3/4）、`P4-review-cso-G3.md`（F-1..F-6）、
> 主 Agent 裁定。**只改裁定项**；legacy §8 承诺不变。

### 9.1 BLOCKER-1（CRITICAL）P6.5 `criteria` 读取链路断裂 — 已修

- `agate_common.read_judge_verdict()` **透传 `criteria`**（原实现丢弃该键）。
- `check-judge-verdict.py` 把 `criteria_total`/`criteria_passed`/`verdict_evidence` 的**强校验
  移到 `_non_legacy` 判定之后**：非 legacy 先由 `criteria` 现算三值再校验；legacy 保留旧口径。
- **复现（改前）**：非 legacy 缺 `criteria` → `criteria_total 缺失或非整数`；补四系统字段后仍
  `非 legacy 任务须在 frontmatter 声明 criteria`（`read_judge_verdict` 丢 `criteria`）。
- **用例**：`test_blocker1_non_legacy_criteria_pass_exit_0`（正，exit 0）+
  `test_blocker1_non_legacy_criteria_missing_exit_1`（负，exit 1）。正向用例改前为红。
- **文档一致**：`UPGRADING.md`/`CHANGELOG.md` 对 P6.5 `criteria` 的承诺（读结构化 `criteria`，
  三系统字段现算）**修好即成立**，无需改写。

### 9.2 MINOR-2 D8 弱化 — 已修

- `check-gate.py::_gate_p6_structured` D8 改读 `read_vision_tri_state(P1)`：能力=`GAP` → 截图条目须
  `manual_review`；否则须 `vision`（不再"二选一即可"）。
- 「涉及 UI 的条目」判定改为**结构化**（`_is_screenshot_ref`：路径分隔符切分后目录段名 ==
  `screenshots`），不再用 `"screenshots/" in refs_str` 子串（`xscreenshots/` 不再误命中）。
- **用例**：D8×3（available 缺 vision → ERROR；GAP 带 vision 缺 manual_review → ERROR；
  `xscreenshots/` 不触发）。
- 夹具演进：`test_pre_commit_hook.py::test_hook_evidence_warning_low_variance_not_blocked` 原用
  `manual_review`（旧弱化口径），改按其任务（无 GAP 声明）写 `vision`（契约驱动的夹具修正，断言不变）。

### 9.3 MINOR-3 D7 弱化 — 补全判据

- D7 判据面扩为：① 正向（results PASS vs evidence FAIL）；② 反向（results FAIL vs evidence PASS）；
  ③ **证据形态**（JSON 声明 `results`/`bdd_results` 但值非列表 / 元素非映射 → ERROR）；
  ④ **多 JSON 合并**（同一 bdd 跨 JSON 状态冲突 → ERROR）。
- **用例**：`test_minor3_d7_*`×4（形态非列表、元素非映射、多 JSON 冲突、反向）。
- 说明：非 legacy 判据 **D2 要求全 PASS**，故「反向」在 `gate_p6` 内被 D2 先行拦截——D7 反向为
  纵深防御（用例断言整体拦截，文案可为 D2 或 D7）。

### 9.4 MINOR-4 `gate_p7` 取值域未校验 — 已加枚举

- `design_gap_reviews.verdict` 限定 `accepted|rejected|followup`；`basis` 限定
  `in_bdd|out_of_scope|followup:DEBT<n>`；越界 → ERROR（`check-gate.py::_gate_p7_structured`）。
- **用例**：`test_minor4_verdict_enum_out_of_range_errors` / `test_minor4_basis_enum_out_of_range_errors`。

### 9.5 cso F-1（MEDIUM）D3 `run:<k>` sha256 fail-open — 已 fail-closed

- `agate_common.resolve_evidence_ref`：`cmd_run` 事件缺 `k`/`log`/`sha256` 任一 → 「事件不完整」
  ERROR（与「sha256 不匹配」区分文案）。
- **用例**：`test_cso_f1_run_event_missing_sha256_fail_closed`。

### 9.6 cso F-2（MEDIUM）`declaration_files` 匹配语义分叉 — 单源统一

- 新增单源 helper `agate_common.declaration_file_paths`（枚举，glob 语义）+
  `agate_common.match_declaration_file`（命中判定，**同 glob 语义**）+
  `agate_common.task_dir_for_file`（子目录文件向上定位任务根）。
- 消费方全部改走单源：`check-gate._aggregate_list`、`check-scope-resolved`、`check-retrospective`
  （枚举）；`check-frontmatter._is_declaration_file`/`_task_is_non_legacy`、`pre-commit-gate._is_declaration_path`、
  `agate-md-field-set._declared_safety_keys`（命中判定）。
- 效果：`P4-implementation/**/*.md` 的**直接子文件**与更深层文件均命中 frontmatter 强制。
- **用例**：`test_cso_f2_p4_implementation_subdir_requires_frontmatter`（直接子文件）+
  `test_cso_f2_nested_subdir_requires_frontmatter`（深层）。

### 9.7 cso F-3 / F-4 / F-5 / F-6（按裁定处理）

- **F-3（LOW，空 `run:` 日志）**：核实结论——**改前未被 D3/D6 覆盖**（D3 的 `run:` 分支只校验存在 +
  事件 + sha256，不校验非空；D6 只在有 `EXIT_CODE` 尾行时判）。**已修**：`run:` 分支补
  `getsize==0 → ERROR`（设计 §5.1 D3「非空文件」）；用例 `test_cso_f3_run_empty_log_errors`。
- **F-4（LOW，`blocker_count` 未登记系统字段）**：**登记为系统字段**——快照
  `level-1.yaml` 新增 `files.P7-consistency.md.fields.blocker_count`/`deviation_critical_count`
  （`writer: system` + `derive: count(findings, severity == …)`）；`agate-md-field-get` 对非 legacy
  按 `findings` 现算（不再信任 agent 手写标量）。用例 `test_cso_f4_p7_blocker_count_is_system_field`。
  （CHECK16：`LEVELS.yaml` 重登记 level-1.yaml LF 归一 sha256 `6ace03c9…`。）
- **F-5（LOW，聚合信任面）**：**显式声明边界**——`_aggregate_list` 只读快照 `declaration_files`
  命中的文件，**不限制**某类声明只能出自哪类文件；与设计 §6「结构化本身不阻止把 BLOCKER 置
  resolved」同口径，全仓无签名（同信任级）→ **不构成新的门禁绕过**；集合相等判据仍要求全覆盖。
- **F-6（LOW，非 legacy SCOPE+ 只认结构化声明）**：**显式声明边界**——`check-scope-resolved.py`
  对非 legacy 只比对**聚合**的 `scope_plus`/`scope_resolved` id 集合；正文 `[SCOPE+]` 不触发
  `scope_resolved` 强制（由批 B 的 T1 绊线作后盾）。**非 G3 新增**，记录为边界。

### 9.8 改动文件（本轮增量）

- `agate/scripts/agate_common.py`（透传 `criteria`；`resolve_evidence_ref` F-1/F-3；
  新增 `declaration_file_paths`/`match_declaration_file`/`task_dir_for_file`）
- `agate/scripts/check-judge-verdict.py`（校验后移）
- `agate/scripts/check-gate.py`（D7/D8、`gate_p7` 枚举、`_aggregate_list` 单源）
- `agate/scripts/check-frontmatter.py` / `pre-commit-gate.py` / `agate-md-field-set.py`
  / `check-scope-resolved.py` / `check-retrospective.py`（匹配单源）
- `agate/rules/task-data/level-1.yaml`（P7 计数系统字段）+ `LEVELS.yaml`（重登记 sha256）
- `agate/UPGRADING.md` / `CHANGELOG.md`（承诺与实现一致）
- `agate/tests/integration/test_tag0050_evidence.py`（+11）/ `agate/tests/unit/test_tag0050_declarations.py`（+5）
- `agate/tests/integration/test_pre_commit_hook.py`（夹具：D8 契约演进）
- `agate-workspace/tasks/TAG0050-task-data-contract/P3-test-cases.md`（C8 新增用例计数登记）

### 9.9 自查结果（自查 ≠ gate）

- 目标 5 文件 → **107 passed**。
- 全量 `pytest agate/tests/ -q --tb=no -n auto` → **2863 passed / 2 skipped / 1 failed**；唯一 failed =
  `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（**既有环境漂移**）。
- `check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（CHECK 16 通过）。
- `check-platform-assumptions.py` → **rc=0**。
- `count-tests.sh` → **2866**（+16）。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest `tmp_path`；无账本污染。

### 9.10 [DESIGN_GAP] 登记（本轮）

[DESIGN_GAP: P7 `blocker_count`/`deviation_critical_count` 的 derive 采用 `count(findings, severity == …)`（按 severity 计全部 findings），而权威门禁 `_gate_p7_structured` 仅计 open findings + 正文绊线；设计 §3.3/§6 未规定 P7 计数的 derive 表达式，且 derive 算子无法表达「open 且 severity=X」复合谓词，故取 severity 口径。门禁不读该字段（F2 已保证计数不被汇总值盖住），该字段仅影响 md-field-get 消费方（如 agate-extract-context）的展示口径。]
