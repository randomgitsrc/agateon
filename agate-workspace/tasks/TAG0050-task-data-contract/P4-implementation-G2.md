---
phase: P4
task_id: TAG0050
type: implementation
parent: P2-design.md
trace_id: TAG0050-P4-G2-20261008
created: '2026-10-08'
agent: implementer
batch: G2
implementation_dir: agate/
---

# P4 实现（批 G2 = 批次 B + 批次 C 合批）— TAG0050 任务数据契约

> `implementation_dir` = `agate/`（协议本体 + 脚本）；测试代码沿用 P3 落成的
> `agate/tests/unit|integration/test_tag0050_*.py`。
> 基线：HEAD `54a814fc`（G1 已提交），分支 `feat/TAG0050-task-data-contract`。

## 0. 范围

- **批次 B**：`agate_schema.py` 单源 + `agate-md-field-set` 7 操作 + `agate-config set|unset|explain`
  + 系统字段拒写/现算 + 缺 frontmatter ERROR(F10) + 渲染块防篡改(CRLF) + 修复命令可执行 + E3 抽样。
- **批次 C**：`prod_touched` 必填/中止 + T4 单一安全门（`markers.yaml default` + `agate_markers.pattern()`）
  + 粗体仍拦 + 否定写法拦 + 专门指引 + 扫描面 = 全部暂存 `*.md`（只排除 CARD 块）+ T1 去掉 PROD_TOUCHED。

## 1. 交付物逐条

### 批次 B（BDD-45..51）

| BDD | 交付物 | 落点 | 状态 |
|---|---|---|---|
| BDD-45 | 7 操作往返：`set`/`append`/`upsert`/`remove`/`--list`/`explain`/`render` + `agate-config set`/`unset`/`explain` | `agate-md-field-set.py`、`agate-config.py` | ✅ 往返用例全绿（**C8 第 2 轮 M1**：`agate-config` 改真往返——隔离 cwd 内 init→set→get/show 可见→unset 后值消失；并断言无声明文件时 set 不创建） |
| BDD-46 | 系统字段（`writer: system`，P6 `pass`/`fail`）拒写并说明来源；**读取按 `derive` 现算（忽略文件值）** | `agate-md-field-set.py`（契约驱动拒写）+ **`agate-md-field-get.py`（`_system_field_spec`：非 legacy + 快照可用时调 `agate_schema.derive`）** + 快照 `files.P6-acceptance.fields.pass/fail`（`derive`） | ✅（**C8 第 2 轮 B1**：读取侧现算已落地，`test_bdd_46` 重写为「文件写 `pass: 999` + results 含 FAIL → 断言现算值 2」的判别用例） |
| BDD-47 | 非 legacy 声明文件缺 frontmatter → ERROR（不回退正文正则，修 F10） | `check-frontmatter.py`（+`agate_common.task_level`）；**GAP-2 已闭合**：hook 路径同样生效 | ✅ |
| BDD-48 | 渲染块 `<!-- AGATE:RENDER ... -->` 被手改 → ERROR + `render` 修复命令；CRLF 归一后逐字节比对 | `agate_schema.render/find_render_blocks`、`agate-md-field-set.py`、`check-gate.py:gate_p6` | ✅（R3：补 CRLF 用例 + 修复命令断言 + `windows_smoke`） |
| BDD-49 | 报错附带修复命令可照抄执行 | `agate-md-field-set.py explain/set/render` 输出 | ✅（**C8 第 2 轮 H1**：新增真用例——非 P6 主产出上「提交报错 → 照抄 `set prod_touched false` → 重新提交 rc=0 转绿」，见 `test_tag0050_prod_touched.py::test_bdd_49_fix_command_executes_and_turns_green`） |
| BDD-50 | 只剩 1 个递归 schema 校验实现 | 新增 `agate_schema.py`；`check-yaml-schema.py`/`agate-frontmatter-check.py`/`agate-config.py` 统一调用 | ✅（R4：守护改机械判据 + 白名单降级副本） |
| BDD-51 | E3 抽样；引述/讨论/否定为 0 则 ERROR，否则落实降级 | 快照 `traps.T1`（含 `downgrade`）；抽样结果见 §4 | ✅（降级已落地） |

### 批次 C（BDD-52..55，按 P2 §3.1）

| BDD | 交付物 | 落点 | 状态 |
|---|---|---|---|
| BDD-52 | 主产出缺 `prod_touched` → ERROR + 修复命令 | 快照 `requires.prod_touched`/`files.P6-acceptance.fields.prod_touched`/`primary_outputs`；**强制点** = `pre-commit-gate.py:_check_prod_touched_primary` | ✅（R1：缺字段 ERROR 已接线；`test_bdd_52` 驱动真实强制点） |
| BDD-53 | `prod_touched: true` 且非 PAUSED → 中止 | `pre-commit-gate.py:_check_prod_touched_primary` | ✅（R4：补端到端用例） |
| BDD-54 | 粗体/引用块 `**[PROD_TOUCHED]**`、字段 false 仍中止 | `markers.yaml PROD_TOUCHED.lead_variant: default` + `pre-commit-gate.py` 用 `agate_markers.pattern()` | ✅ |
| BDD-55 | 否定写法 `- [PROD_TOUCHED]: 无` 仍阻断 + 专门指引 | `pre-commit-gate.py:_PROD_TOUCHED_GUIDANCE` | ✅ |
| §3.1-1 | 单一来源：删字面扫描正则改调 `agate_markers.pattern("PROD_TOUCHED")` | `pre-commit-gate.py`（运行期）+ `markers.yaml` | ✅（字面副本保留于格式检查，见 DESIGN_GAP-5） |
| §3.1-2 | 扫描面 = 全部暂存 `*.md` 新增行，只排除 `AGATE_CARD` 块 | `_scan_prod_touched_and_rerun` + 主循环 2g.0 | ✅（既有实现本就扫全部暂存行，仅排除 CARD） |
| §3.1-3 | T4 = 唯一安全门；T1 标记表去掉 `PROD_TOUCHED` | 快照 `traps.T1.markers`（不含 PROD_TOUCHED） | ✅ |

### 快照 / 规则单源

- `agate/rules/task-data/level-1.yaml`：新增 `files`（P6-acceptance 字段契约 + `pass/fail` 的 `derive`）、
  `declaration_files`、`traps`（T1/T2/T3/T4；T1 标记表**去掉 PROD_TOUCHED**，含 `downgrade`）。
- `agate/rules/task-data/LEVELS.yaml`：重登记 `level-1.yaml` 的新 sha256（`e96a06b2…`）。
- `agate/rules/markers.yaml`：`PROD_TOUCHED.lead_variant` 由 `dash_only` 改 `default`。

## 2. 文件清单

**新增**
- `agate/scripts/agate_schema.py`（JSON Schema 子集校验 + `derive`/`render` + `AGATE:RENDER` 单源库）
- `agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py`（R7：E3 抽样脚本+种子入库）

**修改**
- `agate/scripts/agate-md-field-get.py`（**C8 第 2 轮 B1**：`writer: system` 字段按快照 `derive` 现算——`_system_field_spec`；非 legacy + 快照可用才生效，否则回退文件值）
- `agate/scripts/agate-md-field-set.py`（7 操作 + 快照 `files` 契约字段 + 渲染块 + `explain` 修复命令；**C8 第 2 轮 F-2/H1**：契约驱动 `writer: system` 拒写 + 主产出安全字段 `prod_touched`/`prod_touched_detail` 可写 + explain 跨文件来源）
- `agate/scripts/agate-config.py`（`set`/`unset`/`explain` + 委托 `agate_schema` 校验）
- `agate/scripts/agate-frontmatter-check.py`（委托 `agate_schema`：required/enum/type + `max_depth`；含安装破损降级）
- `agate/scripts/check-yaml-schema.py`（递归校验委托 `agate_schema`）
- `agate/scripts/check-frontmatter.py`（非 legacy 声明文件缺 frontmatter → ERROR；**R2** 改读快照 `declaration_files`；**GAP-2** 删除 hook 路径跳过；**C8 第 2 轮 L1**：`_declaration_files(task_dir)` 改按任务等级，与 `pre-commit-gate` 同口径）
- `agate/scripts/check-gate.py`（`gate_p6` 渲染块防篡改；导入 `load_contract`/`task_level`）
- `agate/scripts/pre-commit-gate.py`（markers 单源安全门 + 否定指引 + **R1** 缺 `prod_touched` ERROR + `true` 中止 + **R2** 声明文件读快照键 + 扫描面；**C8 第 2 轮 F-3**：CARD 块排除收紧为「真实注入块」——dispatch-context 文件名 + 块内容 sha256 匹配，伪造块不排除；**L2**：显式注释两套等级口径）
- `agate/scripts/README.md`（索引登记 `agate_schema.py`；**R5** `agate-config.py` 命令集更新）
- `agate/UPGRADING.md`（**R6** 加「未发布 — TAG0050 批 G2」节）
- `docs/design-notes/design-md-field-set.md`（**R6** §7.2 加注「已被 TAG0050 取代」）
- `agate/tests/unit/test_tag0050_write_tools.py`（**R3** BDD-48 CRLF/修复命令/windows_smoke；**R2** 新增 `test_bdd_47b`；**C8 第 2 轮**：BDD-46 判别化重写、BDD-45 真往返、BDD-49 轻量可执行、新增 F-2 契约驱动拒写 + L5 类型文案守护）
- `agate/tests/integration/test_tag0050_prod_touched.py`（**R1** 重写 BDD-52 驱动真实强制点；**R4** BDD-53 端到端；**C8 第 2 轮**：新增 BDD-49 真「提交报错→照抄执行→转绿」+ F-3 伪造 CARD 块负向用例）
- `agate/tests/unit/test_tag0050_fitness.py`（**R4** BDD-50 守护改机械判据 + 白名单降级副本）
- `agate/tests/integration/test_pre_commit_hook.py`（**R1/GAP-2** 夹具随契约补 frontmatter+prod_touched；**R2** 新增 hook 侧锁定用例）
- `agate/tests/unit/test_dispatch_context_warning.py`（**GAP-2** 夹具随契约补 frontmatter）
- `agate/rules/markers.yaml`、`agate/rules/task-data/level-1.yaml`、`agate/rules/task-data/LEVELS.yaml`
- `agate-workspace/agents/CODE-MAP.md`（登记契约校验单源族 + state-set 补记）

## 3. 新增文件核对表（CODE-MAP 已采用）

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/scripts/agate_schema.py` | 无 P2-skeleton.md | `[CODE_MAP_UPDATED]`（CODE-MAP.md 增「契约校验单源族」句） |

## 4. E3 抽样（BDD-51 / 设计 §3.6 / R7）

口径：只用 `markers.yaml` 的 `default` lead，排除行首反引号/标题；T1 标记表不含 PROD_TOUCHED；
排除 `AGATE_CARD` 块。抽样脚本与种子**已入库**（`e3_sample.py`，与本文件同目录），仓内可复现：

```bash
# agateon 本 checkout（cwd = 仓库根；脚本自动排除 .git/node_modules 等）
python3 agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py . 50 20261008
# peekview 只读副本
python3 agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py /home/kity/oclab/peekview 50 20261008
```

脚本只产出**抽样行**（可机械复现，`total_hits` 随工作树新增文件浮动）；「真实声明 /
引述·讨论·否定」为**人工逐条分类**，不可机械复现，故本文件**不登记精确分类数字**
（原 `~48/~2`、`~49/~1` 无仓内命令支撑，已按 R7 删除）。

误报样例（引述/讨论/模板，非声明）：
- `peekview/agate-workspace/tasks/TPV0099-fullscreen-link/P1-dispatch-context-requirements-review.md:279`
  `- **[SUGGEST]**：{若有，主 Agent 已采纳倾向；无则写"无"}`（**模板占位**）。
- `agateon/agate-workspace/tasks/TAG0025-agateon-rename/P1-progress.md:19`
  `[SCOPE+]反馈机制、[NEED_CONFIRM]触发条件（…）`（列表式**讨论**）。

**结论**：误报 > 0 ⇒ 按设计 §3.6 / BDD-51 的降级分支：**T1 在 P7/P8 评审稿降 WARNING 且声明须同时写入字段**
（已落 `level-1.yaml` 的 `traps.T1.downgrade`）。故批 B **不启用 T1 ERROR**（符合 R7：ERROR 启用前要求 E3 = 0）。
T2/T3 的扫描器本批不接线（无 BDD 机械用例覆盖，且与 T1 同属新 ERROR 面，见 DESIGN_GAP-4）。

## 5. DESIGN_GAP（G2 整改后状态）

> G2 对齐审查（`docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G2.md`）逐条裁定后，
> 本批整改 R1–R7 已闭合 GAP-2/GAP-3；其余 GAP 维持「可接受」。

[DESIGN_GAP: BDD-45 的往返用例执行 `set agent writer` 要求 rc=0，与 TAG0024 design-md-field-set §7.2「agent 永久拒写」冲突；本批按 P2 §3.1 七操作规格解除 agent 拒写（`_cmd_set` 不再从可写面剔除 agent）。]
[DESIGN_GAP_REVIEWED: 已确认（审查 DESIGN_GAP-1「可接受」，与 ADR-014 一致）；R6 已在 `design-md-field-set.md` §7.2 加注「已被 TAG0050 取代」。]

[DESIGN_GAP: F10「非 legacy 声明文件缺 frontmatter → ERROR」仅在直接调用 `check-frontmatter.py` 时生效，pre-commit hook 路径经 AGATE_PRECOMMIT_GATE=1 跳过——本仓多个既有 `test_pre_commit_hook.py` 用例（非 legacy、P1/P2/P6 提交）的主产出无 frontmatter 块，直接启用会把它们转红；角色约束禁止改测试迁就实现。]
[DESIGN_GAP_REVIEWED: 已闭合（R2 + GAP-2 接线）：删除 `AGATE_PRECOMMIT_GATE` 跳过，使 F10 在 gate 侧生效；`_declaration_files()` 与 `pre-commit-gate.py` 改读快照 `declaration_files`；既有 `test_pre_commit_hook.py`/`test_dispatch_context_warning.py` 夹具随新契约补 frontmatter（契约驱动的夹具演进）。]

[DESIGN_GAP: BDD-52「主产出缺 prod_touched → ERROR」未接 pre-commit/check-gate 强制点（仅落地快照数据 + 修复命令文案 + BDD-53 的 true→中止）；原因同 DESIGN_GAP-2——8 个既有 pre_commit_hook 用例的非 legacy 主产出均未声明该字段，启用即转红。跨批次协调（补夹具或收窄作用面）需主 Agent 决策。]
[DESIGN_GAP_REVIEWED: 已闭合（R1）：`_check_prod_touched_primary` 补「缺字段 → ERROR + 修复命令」；`test_bdd_52` 重写为驱动真实强制点（负向证据见 P4-progress）；夹具已随契约更新。]

[DESIGN_GAP: E3 抽样误报 > 0，按设计 §3.6/BDD-51 落 T1 降级（P7/P8 → WARNING + 声明须写字段），本批不启用 T1/T2/T3 的 gate 侧 ERROR 扫描（无 BDD 机械用例覆盖；避免对存量命中引入未接线的新 ERROR 面）。]
[DESIGN_GAP_REVIEWED: 已确认（审查 DESIGN_GAP-4「可接受（附保留意见）」）；R7 已删除无据精确数字、抽样脚本+种子入库（`e3_sample.py`）。]

[DESIGN_GAP: `pre-commit-gate.py` 的运行期 PROD_TOUCHED 安全门已改调 `agate_markers.pattern("PROD_TOUCHED")`（单一来源），但仍**保留**一处字面 `re.match(r"…\[PROD_TOUCHED\]…")`（旧「裸标记格式」检查）——既有 `test_marker_single_source.py` 的 mk_7b/mk_8 从源码**文本抽取**该字面正则做等价守护，删净会使其转红（角色约束禁止改测试）。]
[DESIGN_GAP_REVIEWED: 已确认（审查 DESIGN_GAP-5「可接受」）。]

[DESIGN_GAP: 同一任务内对 `level-1.yaml`（批 A1 已登记为「冻结快照」）追加 `files`/`declaration_files`/`traps` 并重登记 `LEVELS.yaml` sha256——这是既有设计（level-1 注释「其余键为后续批次（B/C/D/E/F）的契约数据，随本快照一并冻结登记」）预期的同任务演进；一致性 CHECK16 因两文件同步更新而通过。]
[DESIGN_GAP_REVIEWED: 已确认（审查 DESIGN_GAP-6「可接受」）。]

## 5.1 C8 第 2 轮整改（B1/H1/F-2/F-3/M1/L1/L2/L5）与可辩护项声明

> 依据 `P4-review-G2.md`（B1/H1/M1/M2/L1–L6）+ `P4-review-cso-G2.md`（F-1/F-2/F-3）。
> 主 Agent 裁定：M2 按 BDD-51 允许分支处理（**显式登记待办**）；L3 保留 fail-safe 并显式声明。

**已修**（负向证据见 `P4-progress.md`「G2 C8 整改（第 2 轮）」节）：

| 项 | 整改 |
|---|---|
| **B1**（BLOCKER）| `agate-md-field-get.py` 增 `_system_field_spec`：对非 legacy 任务读取 `writer: system` 键时调 `agate_schema.derive(spec['derive'], fm)`（快照 `files` 节），忽略文件值；快照不可用/legacy → 回退文件值。`test_bdd_46` 重写为判别用例（文件写 `pass: 999` + results 含 FAIL → 断言现算 2）。 |
| **H1**（HIGH）| `agate-md-field-set.py` 增 `_declared_safety_keys`：`prod_touched`/`prod_touched_detail` 对快照 `declaration_files ∪ primary_outputs` 的文件可写 + bool 强转；`pre-commit-gate.py` 的修复命令与中文注解**分行**（避免整行照抄把注解吃进值）；新增 BDD-49 真「提交报错 → 照抄 `set prod_touched false` → 重新提交 rc=0 转绿」用例。 |
| **F-2**（cso MEDIUM）| `_cmd_set` 增契约驱动 `writer == "system"` 拒写（含**未来**新增、非证据字段的系统字段）；`explain` 增跨文件来源查找（修正来源误报）。 |
| **F-3**（cso MEDIUM）| `pre-commit-gate.py` 的 CARD 块排除收紧为「真实注入块」：文件名为 `*-dispatch-context-*.md` 且块内容 sha256 == 当前阶段卡片期望值（与 2p 同源）才排除；伪造块/非 dispatch-context 文件的块不排除。新增负向用例（伪造块内 `[PROD_TOUCHED]` → 仍拦）。 |
| **M1**（MEDIUM）| BDD-45 的 `agate-config` 部分改真往返（隔离 cwd：init→set→get/show 可见→unset 后值消失）+ 无声明文件时 set 不创建。 |
| **L1**（LOW）| `check-frontmatter._declaration_files(task_dir)` 改按任务等级（回退当前等级），与 `pre-commit-gate` 同口径。 |
| **L5**（LOW）| 补守护用例 `test_l5_frontmatter_type_error_json_type_names`（断言类型文案用 JSON 名「应为 integer」）。 |

**可辩护项声明**（主 Agent 裁定「不必改代码，须显式声明」）：

- **L2**：`_declaration_files`/`_primary_output_for` 用**任务级（最新）快照**（结构面：哪些文件/字段存在），`_check_prod_touched_primary` 的门控 `requirement_active` 用 **level_at_phase**（时间面：要求在本阶段是否生效）——**语义不同，刻意不统一**，已在 `pre-commit-gate.py` 加注释说明（设计 §2.5）。
- **L3**：安全门扫描面 = 任务目录内**全部暂存文件**（`git diff --cached -- <task_rel>`），偏宽于设计 §3.1「全部暂存 `*.md`」——**保留偏宽 fail-safe**（多扫不漏拦；为既有行为，G2 未改）。
- **L4**：`pre-commit-gate.py` 保留一处字面 `[PROD_TOUCHED]` 正则（DESIGN_GAP-5 已裁定可接受；`test_marker_single_source.py` 从源码文本抽取守护）。
- **L6**：`agate-frontmatter-check.py` 的 `_local_*` 降级副本（门控 `agate_schema is not None` + 白名单守护），可辩护为安装破损 fail-safe。

[DESIGN_GAP: M2（C8 复审）——T1/T2/T3 的 gate 侧扫描未接线（`traps`/`downgrade` 目前无 gate 侧消费方）。按 BDD-51 允许分支**显式登记为后续批待办**：T1 在 P7/P8 的降级（`downgrade.action: warning` + `requires_field_write`）与 T2/T3 的 ERROR 扫描待后续批接线；本批不启用（ERROR 启用前要求 E3 误报 = 0）。]

## 5.2 维护性反模式登记（RM-AG0046）

`python3 agate/scripts/check-maintainability.py $TASK_DIR` 检出 **1 条 god-file 跨越**：

- `agate/scripts/pre-commit-gate.py`：`before=998 after=1144 threshold=1000`。

该增长来自本批 **G2** 的两处**设计强制**改动——**T4 单一安全门**（P2 §3.1：markers 单源 +
`PROD_TOUCHED` 缺字段/`true`/否定写法/伪造 CARD 块拦截）与 **F10 接线**（§3.6：非 legacy
声明文件缺 frontmatter → ERROR）——均不可删除。已按协议登记于本任务目录
`known-violations.md`（恰 1 行）。

**待办（后续批，非本任务）**：把 `PROD_TOUCHED` 扫描 / F10 检查从 `pre-commit-gate.py`
抽到独立模块，使该文件回落到 1000 行阈值以下。本任务**只登记、不重构**（不改任何脚本）。

## 6. 自查结果（自查 ≠ gate）

| 命令 | 结果 |
|---|---|
| `python3 -m pytest agate/tests/unit/test_tag0050_write_tools.py agate/tests/integration/test_tag0050_prod_touched.py agate/tests/unit/test_tag0050_fitness.py -q` | **19 passed**（C8 第 2 轮整改后；含 BDD-46 判别化、BDD-45 真往返、BDD-49 轻量、F-2、L5、F-3、BDD-49 真转绿） |
| `python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q` | **62 passed**（F-3 收紧 CARD 块排除后仍全绿） |
| `python3 agate/scripts/check-protocol-consistency.py` | **0 ERROR / 410 WARNING**（基线；WARNING 数随工作树新增未跟踪文件浮动） |
| `bash agate/tests/scripts/count-tests.sh` | **2839**（G2 上轮 2835 **+4** = 新增 `test_bdd_49_fix_command_executes_and_turns_green` + `test_f3_forged_card_block_still_blocks` + `test_f2_system_writer_field_rejected_by_contract` + `test_l5_frontmatter_type_error_json_type_names`；其余为改写既有用例） |
| `python3 agate/scripts/check-platform-assumptions.py` | **0 命中，rc=0** |
| `~/.venvs/agate-dev/bin/ruff check`（改动文件）| All checks passed |
| 全量 `pytest agate/tests/{unit,integration} -n auto` | **8 failed / 2726 passed / 2 skipped**；8 = **既有预期红灯**（BDD-43/59/60/63/66/69/71/76，属 D/E/F 批 + 环境漂移），非本批回归 |
| `pytest agate/tests/regression -n auto` | **81 passed** |

## 7. 环境隔离

[PROD_NOT_TOUCHED] 全程只在本 checkout（`/home/kity/oclab/agateon`）内改代码与跑 pytest；
peekview 仅**只读**打开语料计数（未改其任何文件）；E3 抽样脚本已**入库**（
`agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py`，R7）。
R6 差分/批量实验未对本仓真实数据跑。`agate-config set` 改为「**仅就地更新已存在的声明文件、缺失不创建**」——
避免 BDD-45 往返用例在 cwd（协议源仓库根）意外物化 `agate.config.yaml` 污染其它用例（实测原本会串扰
`test_agate_config.py::test_bdd_8_*`，已修）。
