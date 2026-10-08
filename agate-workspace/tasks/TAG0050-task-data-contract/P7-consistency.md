---
phase: P7
task_id: TAG0050
type: consistency
parent: P2-design.md
trace_id: TAG0050-P7-20261009
status: approved
created: 2026-10-09
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0
deviation_count: 0
deviation_critical_count: 0
design_gap_count: 15
design_gap_reviewed_count: 15
code_map_new_files_count: 16
code_map_reviewed_count: 16
---

# TAG0050 P7 一致性检查 — 任务数据契约：结构化判定、可信写入与任务版本

> **角色**：consistency-reviewer（P7 跨文件一致性交叉检查）。
> **对象**：`P1-requirements.md` / `P2-design.md` / `P3-test-cases.md` / `P4-implementation.md`(+`-G1/-G2/-G3.md`) /
> `P5-test-results/` / `P6-acceptance.md` / `P6.5-judge-verdict.md`。
> **口径**：TAG0050 账本首行非 `task_created`（早于批 A1 机制创建）⇒ **legacy 任务**，P7 gate 走既有
> 口径（frontmatter 计数 + 正文回退 + P4 散文转抄核对 + CODE-MAP 两层核对），与稳定版 `~/.agate/current`
> （v0.79.0）`check-gate.py gate_p7` 同构（本 checkout 新增的 `_gate_p7_structured` 结构化面**不适用于本任务**）。
> **环境隔离**：`[PROD_NOT_TOUCHED]` 本轮只读审查 + 只写本文件，未接触生产环境。

## 结论摘要

| 项 | 结果 |
|---|---|
| BLOCKER | **0** |
| DEVIATION-CRITICAL | **0** |
| DESIGN_GAP 配对 | **15/15**（P4 四处记录全量转抄 + `[DESIGN_GAP_REVIEWED:]`） |
| SCOPE+ 闭环 | **空闭环**（P1 无 `[SCOPE+]`，故无需 `[SCOPE_RESOLVED]`） |
| 未决项清零 | **通过**（P1 无行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]`） |
| 跨文件一致性 | **通过**（锚点见 §3） |
| CODE-MAP | **2 SYNC / 若干 DRIFT（WARNING 级，不阻断）**（见 §5） |
| 架构决策落点 | **无待落**（`decisions/` 不存在，P2 §0 已核） |
| N1 反向传播 | **已落**（见 §7） |
| **总判定** | **approved（无 BLOCKER / 无 DEVIATION-CRITICAL）** |

---

## 1. DESIGN_GAP 逐条配对（硬门，15/15）

> **gate 计数面预警**：gate 的 `_p4_prose_design_gap_count` 只读 `P4-implementation.md` + `P4-implementation/`
> 目录（**本任务无该目录**），故 gate 侧 P4 散文 GAP 计数 = **2**（仅 `P4-implementation.md` 两条）。
> 本任务 P4 记录**分四处**（`P4-implementation.md`=2、`-G1.md`=5、`-G2.md`=7、`-G3.md`=1），
> 分批文件 `P4-implementation-{G1,G2,G3}.md` **不在 gate 计数面内**。P7 按**全量 15 条**转抄配对
> （`design_gap_count=15 / design_gap_reviewed_count=15`），gate 转抄核对 `P4散文(2) ≤ dg_count(15)` 成立。

### 1.1 批 A1（`P4-implementation.md`，2 条）

- [DESIGN_GAP: pre-commit 规则 1（新目录须有创建事件）对控制态 PAUSED/READY/DONE 不施加叠加阻断——PAUSED 表示任务已被人工接管，否则 A0 的 BDD-01（PAUSED 留痕）会被规则 1 抢先阻断]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation.md §3.2 / P2-design.md §2.3；basis=in_bdd；主 Agent 裁决接受，A0 BDD-01 保持绿]
- [DESIGN_GAP: 非 legacy 任务写 status 的 ERROR 与 status 现算属批 A3（设计 §2.7），A1 未实现；A1 只统一 ID 正则，BDD-39 仍红属预期]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §2「A3」/ P2-design.md §2.7；basis=in_bdd；A3 已实现（G1 交付 `agate-state-set.py` + `agate-state-yaml-check.py` status 系统字段），BDD-39 现 PASS]

### 1.2 合批 G1（A2+A3+A4，`P4-implementation-G1.md`，5 条）

- [DESIGN_GAP: A2 的 BDD-31 验收测试与 BDD-23/24/30 自相矛盾（同一输入既断言不含 FAIL 又断言含 FAIL）；已修复——`_task_commit_repo` 写 `.agate-version` 钉版本，分支③只认仓库内 `.agate-version` 或仓库含协议本体]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §3 / P1-requirements.md BDD-31 / P6-acceptance.md BDD-31 PASS；basis=in_bdd；两条断言均未改，BDD-31 判 FAIL 语义正确]
- [DESIGN_GAP: A3 的 `agate-state-set phase` 对前向跨阶（delta≥2）从严拒绝，该规则只在 state-set 生效、不加入 `check_transition`（否则破坏既有前向跳用例）]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §2「A3」/ P2-design.md §2.7 / state-machine.md；basis=in_bdd；BDD-36 PASS]
- [DESIGN_GAP: A4 的 `review_output` 缺失判 WARNING（设计原文 ERROR）——存量约 25 条 R 义务无合格评审产出；缺→WARNING、非法→ERROR，终态被测试锁定]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §3 / P2-design.md §2.9 / P6-acceptance.md BDD-43 PASS；basis=in_bdd]
- [DESIGN_GAP: A2 的 commit-msg 回放用当前协议（SCRIPT_DIR）而非回放协议——SELF-GATE 留痕是版本无关策略；pre-commit 回放仍用选定回放协议]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §3 / P2-design.md §2.4；basis=in_bdd；BDD-27 PASS]
- [DESIGN_GAP: A2 协议版本分支①（按逐提交 `.agate-version` 定位/安装对应版本目录）未实现——CI 未安装各版本时无法定位；`.agate-version` 目前只用于单调不降检查；对缺失 `.agate-version` 的提交本批不判 FAIL，属已知绕过面]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G1.md §3/§7(K5) / P2-design.md §2.4；basis=out_of_scope；docstring 与 `scripts/README.md` 已降级为「未实现」，留待后续批/DEBT]

### 1.3 合批 G2（B+C，`P4-implementation-G2.md`，7 条）

- [DESIGN_GAP: BDD-45 的往返用例执行 `set agent writer` 要求 rc=0，与 TAG0024 design-md-field-set §7.2「agent 永久拒写」冲突；本批按 P2 §3.1 七操作规格解除 agent 拒写]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §5(GAP-1) / P2-design.md §3.1 / design-md-field-set.md §7.2；basis=in_bdd；已加注「已被 TAG0050 取代」]
- [DESIGN_GAP: F10「非 legacy 声明文件缺 frontmatter → ERROR」原仅在直接调用 `check-frontmatter.py` 时生效（hook 路径经 `AGATE_PRECOMMIT_GATE=1` 跳过）]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §5(GAP-2) / P2-design.md §3.6 / P6-acceptance.md BDD-47 PASS；basis=in_bdd；已闭合（删跳过 + 夹具演进）]
- [DESIGN_GAP: BDD-52「主产出缺 prod_touched → ERROR」原未接 pre-commit/check-gate 强制点]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §5(GAP-3) / P2-design.md §3.1 / P6-acceptance.md BDD-52 PASS；basis=in_bdd；已闭合（R1 补 `_check_prod_touched_primary`）]
- [DESIGN_GAP: E3 抽样误报 > 0，按设计 §3.6/BDD-51 落 T1 降级（P7/P8 → WARNING + 声明须写字段），本批不启用 T1/T2/T3 的 gate 侧 ERROR 扫描]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §4/§5(GAP-4) / P2-design.md §3.6 / P6-acceptance.md BDD-51 PASS；basis=in_bdd；`traps.T1.downgrade` 已落]
- [DESIGN_GAP: `pre-commit-gate.py` 运行期 PROD_TOUCHED 安全门已改调 `agate_markers.pattern()`（单一来源），但仍保留一处字面正则（既有 `test_marker_single_source.py` 从源码文本抽取守护）]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §5(GAP-5) / P2-design.md §3.1；basis=in_bdd；字面副本保留于格式检查]
- [DESIGN_GAP: 同一任务内对 `level-1.yaml`（批 A1 已登记为冻结快照）追加 `files`/`declaration_files`/`traps` 并重登记 `LEVELS.yaml` sha256——属设计预期的同任务演进，CHECK16 因两文件同步更新而通过]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G2.md §5(GAP-6) / P2-design.md §2.1 / consistency CHECK16；basis=in_bdd；BDD-15 PASS]
- [DESIGN_GAP: M2（C8 复审）——T1/T2/T3 的 gate 侧扫描未接线（`traps`/`downgrade` 目前无 gate 侧消费方），按 BDD-51 允许分支显式登记为后续批待办]
- [DESIGN_GAP_REVIEWED: verdict=followup; checked_against=P4-implementation-G2.md §5.1(M2) / P2-design.md §3.6；basis=out_of_scope；ERROR 启用前要求 E3 误报 = 0，留待后续批接线]

### 1.4 合批 G3（D+E+F，`P4-implementation-G3.md`，1 条）

- [DESIGN_GAP: P7 `blocker_count`/`deviation_critical_count` 的 derive 采用 `count(findings, severity == …)`（按 severity 计全部 findings），而权威门禁 `_gate_p7_structured` 仅计 open findings + 正文绊线；derive 算子无法表达「open 且 severity=X」复合谓词，故取 severity 口径]
- [DESIGN_GAP_REVIEWED: verdict=accepted; checked_against=P4-implementation-G3.md §9.10 / P2-design.md §3.3/§6 / level-1.yaml `files.P7-consistency.md`；basis=in_bdd；门禁不读该字段（F2 保证计数不被汇总值盖住），仅影响 md-field-get 消费方展示口径]

> **配对统计**：行首 `[DESIGN_GAP:]` = 15（P4 四处全量）；行首 `[DESIGN_GAP_REVIEWED:]` = 15；
> frontmatter `design_gap_count=15 / design_gap_reviewed_count=15` 与 P4 实际一致。gate 转抄核对
> `P4散文(2) ≤ 15` 通过。

---

## 2. SCOPE+ 闭环

- **`P1-requirements.md` 无行首 `[SCOPE+]` 声明**（全文仅 §2 标题提及 `[SCOPE+ from Pn]` 机制说明，非声明；
  亦无其他声明文件产生 SCOPE+）。
- ⇒ **无需 `[SCOPE_RESOLVED]`**，SCOPE+ 为**空闭环**（`P1 无 SCOPE+ ⇒ 无悬空增补`）。锚点：
  `P1-requirements.md`（全文 `grep` 无行首 `[SCOPE+]`）；对照 gate 判据 `scope_plus ⊆ scope_resolved`（两侧均空集，成立）。

---

## 3. 跨文件一致性（逐项引源文件节名）

### 3.1 `P2§packages` 与 P8 release bump 范围

- `P2-design.md` frontmatter `packages`（**8 项**：agate-scripts / agate-rules / agate-task-data / agate-cards /
  agate-roles / agate-tests / ci-workflows / docs-upgrading）与 `P1-requirements.md` frontmatter `packages`
  （同 8 项）**逐字一致**。
- `P8-release.md` **尚未产出**（P7 是 P8 前置阶段）⇒ bump 范围将在 P8 依 `P2§packages` 落定；
  当前**无法**做 P8↔P2 的实文件比对，记为 P8 待办（非本阶段 BLOCKER）。
- ⚠️ 记录口径差异：dispatch 提示「`P2§packages`（6 个）」，实测 `P2§packages` 为 **8 项**（与 `P1§packages` 一致）；
  按实测 8 项记录。

### 3.2 `P1 BDD` 数与 P6 验收结果数

- `P1-requirements.md` §4 定义 **BDD-01..77**（标题级 `#### BDD-N` 计数 = 77）。
- `P6-acceptance.md` frontmatter `pass: 77 / fail: 0`，正文 **77 条 PASS**（BDD-01..77，无挑验/无遗漏）。
- `P6.5-judge-verdict.md` `criteria_total: 77 / criteria_passed: 77`（judge 独立复验 77/77，轮次 2/2）。
- ⇒ **P1 BDD(77) = P6 PASS(77) = P6.5(77)**，数量匹配；`P3-test-cases.md` 的 BDD 映射覆盖同 77 条。

### 3.3 `P4§impl-path` 与 `P2§design` 方案吻合（含分批）

- `P2-design.md` §1.1/§4 规划 **10 批**（A0/A1/A2/A3/A4/B/C/D/E/F），`dispatch_plan` 亦声明 10 批。
- `P4-implementation.md`（A1）+ `-G1.md`（A2+A3+A4）+ `-G2.md`（B+C）+ `-G3.md`（D+E+F）**分批交付**，
  与 P2 的 10 批划分**一一对应**（A0 由 hotfix `1d5aab2d` 交付）；实现落点（`agate_common` 契约函数、
  `agate-task-init.py`、`agate-state-set.py`、`agate_schema.py`、`check-gate.py` P6/P7 判据等）与
  `P2§1.1 改什么` 表逐条吻合。
- 批 D 前置 hotfix（`agate-run` I-2，`b746d07d`）与 P2 §10 G6 声明一致。

---

## 4. 未决项清零

- `P1-requirements.md` **无**行首 `[NEED_CONFIRM]`、**无**行首 `[BLOCKER]`、**无**行首 `[DEVIATION-CRITICAL]`
  （`grep -nE '^\s*>?\s*-?\s*\[(NEED_CONFIRM|BLOCKER|DEVIATION-CRITICAL)'` 无命中）。
- `P6-acceptance.md` 客观验收 PASS/FAIL 二值（77 PASS / 0 FAIL），无 NEED_CONFIRM 残留。
- ⇒ 未决项清零**通过**。

---

## 5. CODE-MAP 核对（`{AGATE_WORKSPACE}/agents/CODE-MAP.md` ↔ P4「新增文件核对表」）

> `CODE-MAP.md` 描述 `agate/` 协议本体（phase-cards / roles / scripts / templates / rules）。P4 新增文件核对表
> 行数：`P4-implementation.md` = 15 + `-G2.md` = 1（`agate_schema.py`）+ G1/G3 = 0 ⇒ **16**。

| # | 新增文件（P4 声明） | 所属批 | CODE-MAP 记录 | 判定 |
|---|---|---|---|---|
| 1 | `agate/scripts/agate-task-init.py` | A1 | **未登记** | `[CODE_MAP_DRIFT:]` |
| 2 | `agate/scripts/agate-state-set.py` | A3 | L38「相关状态族补记」 | `[CODE_MAP_SYNC:]` |
| 3 | `agate/rules/task-data/LEVELS.yaml` | A1 | **未登记**（rules 模块未提 task-data） | `[CODE_MAP_DRIFT:]` |
| 4 | `agate/rules/task-data/level-1.yaml` | A1 | **未登记** | `[CODE_MAP_DRIFT:]` |
| 5 | `agate/rules/obligations.yaml` | A4 | L40 已述（**非新增**，TAG0042 建） | `[CODE_MAP_DRIFT:]`（误列为新增） |
| 6 | `agate/scripts/check-obligations.py` | A4 | L40 已述（**非新增**，TAG0042 建） | `[CODE_MAP_DRIFT:]`（误列为新增） |
| 7 | `docs/design-notes/r6-differential.sh` | A1 | 非协议本体 | `[CODE_MAP_EXEMPT:]`（docs） |
| 8 | `docs/design-notes/r6-allowlist.yaml` | A1 | 非协议本体 | `[CODE_MAP_EXEMPT:]`（docs） |
| 9–15 | `agate/tests/**/test_tag0050_*.py`、`agate/tests/helpers_tag0050.py`（7 项） | A1–A4 | 测试文件不改变架构全貌 | `[CODE_MAP_EXEMPT:]`（测试） |
| 16 | `agate/scripts/agate_schema.py` | B(G2) | L37「契约校验单源族」 | `[CODE_MAP_SYNC:]` |

**发现（WARNING 级，不阻断）**：
- `[CODE_MAP_DRIFT: agate/scripts/agate-task-init.py 未登记进 CODE-MAP.md scripts 模块]`——A1 新增的协议脚本
  未在 CODE-MAP 记录（G2 更新 CODE-MAP 时只补了 `agate_schema.py` 与 `agate-state-set.py`）。
- `[CODE_MAP_DRIFT: agate/rules/task-data/{LEVELS,level-1}.yaml 未登记进 CODE-MAP.md rules 模块]`——新增的
  契约快照数据面未记录。
- `[CODE_MAP_DRIFT: P4-implementation.md 新增文件核对表将既有 obligations.yaml / check-obligations.py 误列为「新增文件」]`
  ——实测二者在基线 `720c97d3` 已存在（TAG0042 `b19a425b` 建），属声明面瑕疵。
- 依赖方向**未违反**（新脚本仍属 scripts 工具层、新数据属 rules 数据面，`CODE-MAP.md §依赖方向` 未被反向注入）。
- **机器计数对照**：gate 转抄核对层读 `P4-implementation.md` 行首 `[CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT]` 计数 = **0**
  （标记仅在 `-G2.md` 表格内、非行首）≤ `code_map_new_files_count=16` ⇒ 通过；内部一致性层
  `code_map_reviewed_count(16) ≥ code_map_new_files_count(16)` ⇒ 通过。
- 处置建议：主 Agent 在 P8 前决定是否将 2 处 drift 补登记进 CODE-MAP.md（WARNING 级，不阻断推进）。

---

## 6. 架构决策落点核对（`{AGATE_WORKSPACE}/decisions/`）

- `agate-workspace/decisions/` **不存在**（`P2-design.md` §0 已核：「项目侧架构决策 … 不存在 → 无既有跨任务
  决策需对齐」）。
- ⇒ 本任务**无应落的跨任务架构决策**，亦无「被本任务证伪的既有决策」需就地标注过时。
- **仅核对，不在 P7 撰写决策正文**（符合 DEBT0039 口径）。无待办。

---

## 7. N1 反向传播复核（G1/G2/G3 各批 SELF-GATE 整改是否落到协议文档）

| 协议面 | 落点证据 | 判定 |
|---|---|---|
| `agate/UPGRADING.md` | 「未发布 — TAG0050 批 G1」（L279）/「批 G2」（L360）/「批 D 前置 hotfix」（L393）/「批 D/E/F」（L403） | 已落 |
| `agate/WORKFLOW.md` | 1.1「账本与新目录」行（L354）+ 2.1/2.7/2.11/2h 非 legacy 分支 + CI 逐提交回放（L370）+ 多任务适配（L373） | 已落 |
| `agate/state-machine.md` | legacy 不可重开（L254）+ phase 唯一写入口 `agate-state-set.py`（L332/339/408） | 已落 |
| `agate/platform-notes.md` | 「CI 兜底说明」改逐提交回放（diff 实测 2 行） | 已落 |
| 卡片 | `phase-cards/{P1,P2,P3,P6,P7,P8}` 均改动（git diff 实测） | 已落 |
| 角色卡 | `execution-roles/{consistency-reviewer,verifier}` + `review-roles/requirements-review`（git diff 实测） | 已落 |
| `CHANGELOG.md` | TAG0050 批 D/E/F + 义务基线重设（L15/L32） | 已落 |

⇒ G1/G2/G3 的 SELF-GATE 整改（F1–F7 / R1–R7 / GAP-1..8 / A1–A5 / K1–K6 / MINOR-1..4 / cso F-1..F-6）
均已落到上述协议文档面（各批 P4 记录 §6/§7/§9 自述 + 本表 git 实测交叉印证）。

---

## 计数汇总（与 frontmatter 一致）

`blocker_count=0` / `deviation_count=0` / `deviation_critical_count=0` /
`design_gap_count=15` / `design_gap_reviewed_count=15` /
`code_map_new_files_count=16` / `code_map_reviewed_count=16`。

## 预跑 gate（自查 ≠ gate）

见 `P7-progress.md` 尾行 / 主 Agent 亲跑记录：`python3 ~/.agate/current/agate/scripts/check-gate.py P7 <task_dir>`。

## 环境隔离

[PROD_NOT_TOUCHED] 本轮仅只读审查本 checkout 内任务产出并写本文件，未接触生产环境。
