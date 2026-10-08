---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G2.md
trace_id: TAG0050-P4-20261008
agent: review
status: rejected
---

# P4 实现评审（独立）— TAG0050 批 G2（B + C）

> 角色：`review`（偏执 Staff Engineer）。
> 对象：G2 **未提交**改动，HEAD `54a814fc`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 范围：`P4-dispatch-context-review-G2.md` 的 5 个重点核验项；不重做设计。
> 依据：`P2-design.md` §3/§3.1/§3.6、`P1-requirements.md` §4（BDD-45..55）、`docs/design-notes/design-tag0050-task-data-contract.md` §3/§4。
> 只读纪律：**未编辑任何被评审文件**；全部验证在**仓外可丢弃副本** `/tmp/opencode/G2rev/` 上进行；
> 真实仓库仅执行只读命令（`read`/`grep`/`git status`/`git diff`/`sha256sum`），未执行任何写仓或破坏性命令。
> 环境隔离：`[PROD_NOT_TOUCHED]`（全程未接触生产环境；peekview 未打开）。

## 0. 汇总结论

**`status: rejected`** —— 存在 **1 项 [BLOCKER]（B1）** 与 **1 项 [HIGH]（H1）**，
另有 2 项 [MEDIUM]、6 项 [LOW]/观察。批次 B/C 的多数交付物已落地且经独立复现（见 §2），
但 BDD-46 的一半 Then 未实现，且其验收用例对半无判别力；BDD-52 的修复命令在多数主产出上不可执行。

| 编号 | 级别 | 一句话 |
| --- | --- | --- |
| B1 | **[BLOCKER]** | BDD-46「md-field-get 读取 `writer: system` 字段按 `derive` 现算」**未实现**（`agate_schema.derive()` 零生产消费方），验收用例对半空转 |
| H1 | **[HIGH]** | BDD-52 报错附带的修复命令 `set prod_touched …` 在非 P6 主产出上**不可执行**（`非法 key`），连带 BDD-49「照抄执行转绿」未真验证 |
| M1 | [MEDIUM] | BDD-45 的 `agate-config set/unset/explain` **往返用例未真往返**（缺文件时 `set` 为 no-op；用例只断言 rc=0） |
| M2 | [MEDIUM] | BDD-51 的 `traps.T1.downgrade` 是**惰性数据**（`traps` 无 gate 侧消费方；T1/T2/T3 均未接线） |
| L1 | [LOW] | `check-frontmatter._declaration_files` 用 `current_level`，与 `pre-commit-gate._declaration_files` 的 `task_level` 口径不一致（复评 ① 复现） |
| L2 | [LOW] | `_primary_output_for`/`_declaration_files(task_dir)` 用 `task_level`（最新级），与 `requirement_active` 的 `level_at_phase` 口径不一致 |
| L3 | [LOW] | 安全门扫描面 = 任务目录内**全部**暂存文件，非设计 §3.1 第 2 点的「全部暂存 `*.md`」（既有行为，偏宽 fail-safe） |
| L4 | [LOW] | `pre-commit-gate.py:775` 保留一处字面 `[PROD_TOUCHED]` 正则（DESIGN_GAP-5，已裁定可接受） |
| L5 | [LOW] | `agate-frontmatter-check._check` 类型错误文案由 Python 名改 JSON 名（`应为 str`→`应为 string`），无测试守护 |
| L6 | [LOW] | `_local_iter_errors`/`_local_max_depth` 是**不完全的**第二份递归遍历（白名单 + 门控，可辩护） |

> **判定口径**：review 角色规则「任何 BLOCKER → rejected」。B1 使任务的核心目标
>（系统事实由工具现算、不可自报）在 P6 `pass`/`fail` 上仍不成立 ⇒ 打回。

---

## 1. 环境与验收面复核（命令 + 输出）

- 仓外副本 `/tmp/opencode/G2rev/`（`rsync -a --exclude __pycache__ --exclude .pytest_cache`，含 `.git`）。
- G2 焦点用例：`pytest agate/tests/unit/test_tag0050_write_tools.py agate/tests/integration/test_tag0050_prod_touched.py agate/tests/unit/test_tag0050_fitness.py -q` → **15 passed**。
- 夹具面：`pytest agate/tests/integration/test_pre_commit_hook.py -q` → **62 passed**。
- 全量：`pytest agate/tests/unit agate/tests/integration -q -n auto` → 副本 **12 failed / 2717 passed / 3 skipped**。
  其中 4 条为**副本环境差异**（`test_install_sh.py` ×3、`test_agate_version_install.py` ×1：副本内
  `?? repo/` 触发「源 checkout 被污染」判定）——`git stash -u`（去掉 G2 改动）后**同样红**，
  证明**非 G2 引入**；其余 8 条 = 已登记预期红灯（BDD-43/59/60/63/66/69/71/76）。
  ⇒ **G2 未引入新回归**。
- `python3 agate/scripts/check-protocol-consistency.py`（副本自己的）→ **0 ERROR**（WARNING 410，随未跟踪文件浮动）。
- `bash agate/tests/scripts/count-tests.sh` → **2835**（与 `P4-implementation-G2.md §6` 一致）。

## 2. 重点核验项逐条

### 2.1 批次 B

| 子项 | 判定 | 证据 |
| --- | --- | --- |
| BDD-50 `agate_schema.py` 单源（三校验器统一调用） | ✅（附 L6） | `check-yaml-schema.py:303-334`、`agate-config.py:106-124`、`agate-frontmatter-check.py:108-118` 均委托 `agate_schema`；`test_tag0050_fitness.py::test_schema_single_source_only_agate_schema` 改机械判据（递归定义扫描 + 白名单 + 门控断言） |
| BDD-45 7 操作真实可用 | ✅ 工具层 / ⚠️ 用例弱 | 独立复现 append→upsert→remove→render 内容正确（`results` 正确增改删 + 渲染块同步重生成）；`agate-config` `init→set→get` 真往返。但用例只断言 rc=0（见 M1） |
| BDD-46 系统字段拒写 + derive 现算 | ❌ **一半未实现** | 见 B1 |
| BDD-47 缺 frontmatter → ERROR（gate 侧生效） | ✅ | `check-frontmatter.py:98-110`；`AGATE_PRECOMMIT_GATE` 仅剩注释（`grep` 无判定分支）；`test_tag0050_r2_declaration_files_snapshot_effective` 锁 hook 侧 |
| BDD-48 渲染块防篡改 + CRLF | ✅ | `check-gate.py:_check_render_blocks`（`text.replace("\r\n","\n")` 归一 + `render()` 逐字节 + 修复命令）；`test_bdd_48` 双侧 LF/CRLF + `windows_smoke` |
| BDD-49 修复命令可执行转绿 | ⚠️ | 见 H1（prod_touched 路径命令不可执行；用例未执行） |
| BDD-51 E3 抽样 + 降级 | ✅（数据）/ ⚠️（惰性） | `e3_sample.py` 仓内可复现（`… . 5 20261008` → `total_hits=483`，含种子）；`traps.T1.downgrade` 已落快照。但见 M2 |

### 2.2 批次 C（按 P2 §3.1）

| 子项 | 判定 | 证据 |
| --- | --- | --- |
| BDD-52 真判别力（pre-commit ERROR + 修复命令） | ✅ 判据 / ❌ 修复命令 | **负向控制**：把 `pre-commit-gate.py:561` 的 `if "prod_touched" not in fm:` 变异为 `if False and …` → `test_bdd_52` 立即红，且红因恰为旧的 `GATE P4: P4-review.md 不存在`（rc 仍 1 但与该 BDD 无关）⇒ 证明旧断言无判别力、新断言有判别力。修复命令问题见 H1 |
| BDD-53 `true` + 非 PAUSED → 中止（端到端） | ✅ | 负向控制：禁用 `pre-commit-gate.py:567` 分支 → `test_bdd_53` 红；正向用例真实 git repo + hook |
| BDD-54 粗体 / 非声明文件仍拦 | ✅ | `markers.yaml` `lead_variant: default`（`^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*\|__)?` 认粗体）；`_PROD_TOUCHED_RE = agate_markers.pattern("PROD_TOUCHED")`（`pre-commit-gate.py:247`）；`test_bdd_54` 用非声明文件 `P5-verification.md` + 粗体 |
| BDD-55 否定写法拦 + 专门指引 | ✅ | `_PROD_TOUCHED_GUIDANCE`（`:251`）；`test_bdd_55` 断言「疑似否定写法」 |
| T4 单一来源 + T1 去 PROD_TOUCHED | ✅ | `markers.yaml` 改 `default`；安全门调 `pattern()`；`level-1.yaml traps.T1.markers` 不含 PROD_TOUCHED |
| 扫描面 = 全部暂存 `*.md`（只排除 CARD 块） | ⚠️ 偏宽 | 实现扫任务目录内**全部**暂存文件（`git diff --cached -- <task_rel>`），非仅 `*.md`；仅排除 CARD 块（见 L3，既有行为） |

### 2.3 回归面（夹具是否削弱断言）

`git diff agate/tests/integration/test_pre_commit_hook.py` **逐行核对**：全部为**新增契约字段**
（`_P1_REQ` 加 `prod_touched: false`；P6 夹具加 `---\nagent: test\nprod_touched: false\n---`；
P2/P3 夹具加 `prod_touched: false`）+ 1 个新增守护用例。**无任何 `assert` 被删除或放宽**。
`test_dispatch_context_warning.py` 同型（仅夹具补 frontmatter）。判定：**契约驱动的夹具演进，未削弱**。

### 2.4 legacy 兼容（§8）

- F10（缺 frontmatter）与 `prod_touched`（缺/true）均**非 legacy 门控**：
  `requirement_active(...,"prod_touched",...)` 对 legacy 返回 `None`；`check-frontmatter._task_is_non_legacy` 对 legacy 返回 `False`。
  BDD-54/55 用例即以 legacy 任务验证（只拦标记、不报 prod_touched）⇒ legacy 行为不变。
- 唯一 legacy 可见变化 = PROD_TOUCHED 由 `dash_only` 扩到 `default`（粗体/引用块/`*`/`+` 列表符），
  属设计 §8 第 12 项、`r6-allowlist.yaml` 的 **D12**（`new_error` / `pre-commit` / `legacy` / `PROD_TOUCHED`）。
- **R6 全量差分未能在评审期运行**：`r6-differential.sh` 要求 corpus 干净，而 G2 未提交 ⇒ 拒绝
  （`corpus 原仓库不干净`）。R6 是 **P5 gate**（`P5_r6_differential`），此处只做代码路径的静态核对。

### 2.5 SELF-GATE 闭环（R1–R7 / GAP-2/3）

逐条独立复核 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G2-rereview.md`：
R1（负向控制复现）、R2（`declaration_files` 有消费方 + 快照 6 文件生效）、GAP-2（无 `AGATE_PRECOMMIT_GATE` 跳过）、
R3（CRLF + 修复命令 + windows_smoke）、R4（BDD-53 端到端 + BDD-50 机械判据）、R5（README `:164`）、
R6（UPGRADING「未发布 — TAG0050 批 G2」节 + `design-md-field-set.md:253` 加注）、R7（`e3_sample.py` 入库 + §6 措辞）
**均已落实**。但复评的两项「LOW 观察」我独立确认（L1）并新增 L2。

## 3. 发现详述

### B1 [BLOCKER] BDD-46「derive 现算」未实现

- **契约**：设计 §3.3「对非 legacy 任务，`agate-md-field-get` 读取 `writer: system` 的键时**按 `derive` 现算**，忽略文件里的值」；
  BDD-46 Then 第二分句（`P1-requirements.md:371`）与 `P4-dispatch-context-implementer-G2.md` 批次 B 第 3 点同口径。
- **事实**：
  - `agate-md-field-get.py` **无任何** `derive`/`results`/`writer`/`system` 逻辑（`grep` 零命中）；`pass`/`fail` 走
    `NO_FALLBACK_INT_FIELDS`（`agate-md-field-get.py:133-134`）直接读 frontmatter 值。
  - `agate_schema.derive()` 有定义，但**零生产消费方**（`grep -rn "derive(" agate/scripts/*.py` 仅命中文档/自身定义）。
- **复现**（仓外副本）：非 legacy 任务（账本首行 `task_created`），`P6-acceptance.md` 含
  `results` = 2×PASS + 1×FAIL 且 `pass: 99`：
  ```
  $ FILE=…/P6-acceptance.md agate-md-field-get.py pass
  99          # 期望按 derive 现算 = 2（忽略文件里的 99）
  ```
- **验收用例空转**：`test_bdd_46_system_field_reject_and_derive`（`test_tag0050_write_tools.py:52-64`）
  先 `set pass 3`（被拒 ⇒ 文件里**从不出现** `pass`），再断言 `"3" not in g.output`——**恒真**，对 derive 零判别力。
- **影响**：TAG0050 的核心目标（系统事实现算、不可自报）在 P6 `pass`/`fail` 上仍不成立；
  `check-gate.py:1270-1275` 仍以 frontmatter `pass`/`fail` 判定（手改 frontmatter 即可自报）。
- **说明**：若设计意图是把 derive 接线留到批 D（P6 `results` 消费方），则本批应把它显式登记为
  **待办**（DESIGN_GAP / progress），而 `P4-implementation-G2.md §1` 的 BDD-46 行标 ✅ 与
  `P4-dispatch-context-implementer-G2.md` 批次 B 第 3 点的明文要求相矛盾——二者必须一致（实现，或改标待办）。
- **建议**：`agate-md-field-get.py` 读 `writer: system` 字段时改从快照 `files.<basename>.fields.<key>.derive`
  取表达式并调 `agate_schema.derive(expr, fm)`；同步把 `test_bdd_46` 改为**先手工写入错误值再读取断言现算值**。

### H1 [HIGH] BDD-52 修复命令在非 P6 主产出上不可执行（连带 BDD-49 未真验证）

- **事实**：`pre-commit-gate.py:561-566` 在「主产出缺 `prod_touched`」时输出
  `修复命令: FILE=<out_file> agate-md-field-set.py set prod_touched false（若未触达生产）`。
  但 `prod_touched` 只登记在快照 `files.P6-acceptance.md.fields`；`agate-md-field-set.py:418` 的可写面
  = `_writable_keys()` ∪ 本文件契约字段 ⇒ 对 `P4-implementation.md` 等非 P6 主产出**不在可写面**。
- **复现**（仓外副本）：
  ```
  $ FILE=…/P4-implementation.md agate-md-field-set.py set prod_touched false
  ERROR: 非法 key 'prod_touched'，合法 key 清单: agent, blocker_count, …, verdict_evidence
  RC=1
  ```
  即 BDD-52 的验收用例（phase=P4，主产出 `P4-implementation.md`）给出的修复命令**照抄必失败**。
- **附带**：在 P6 上该行整行照抄会把行尾中文注解吃进值里——
  `set prod_touched 'false（若未触达生产）'` → 写入 `prod_touched: false（若未触达生产）`（字符串）。
- **BDD-49 未真验证**：`test_bdd_49_fix_command_executes`（`test_tag0050_write_tools.py:133-137`）只断言
  `explain` 输出含 `"agate-md-field-set"`，**从不执行**命令、也不复验转绿 ⇒ 无法发现本缺陷。
- **建议**：① 把 `prod_touched` 纳入所有 `primary_outputs` 的可写字段（快照逐文件 `files` 登记，
  或 `_writable_keys` 兜底）；② 修复命令与中文注解分行（注解另起一行）；③ `test_bdd_49` 改为
  **执行命令 → 复跑 gate 断言转绿**。

### M1 [MEDIUM] BDD-45 `agate-config` 往返用例未真往返

`test_bdd_45_seven_ops_and_config_roundtrip`（`test_tag0050_write_tools.py:45-49`）对
`set/unset/explain` 只断言 `rc==0` 且无「未知子命令」。而 `_cmd_set`（`agate-config.py:167-193`）
在 `agate.config.yaml` **缺失时不创建**（刻意设计，避免污染 cwd）⇒ 用例中 `set` 为 no-op，
`unset`/`explain` 同理。工具本身经独立复现**真能往返**（`init→set→get` = `python`），
但「往返」这一 BDD 语义**未被用例覆盖**。建议用例改用 `tmp_path` 内 `init` 后再 `set/get` 断言值。

### M2 [MEDIUM] BDD-51 的 T1 降级是惰性数据

`grep -rn "traps\[\|downgrade" agate/scripts/*.py` **零命中**；`level-1.yaml:85-114` 的
`traps.T1/T2/T3/T4` 与 `T1.downgrade.requires_field_write` **无任何 gate 侧消费方**。
即 G2 在「降级」与「未启用」之间实际选的是**未启用**（T1/T2/T3 的 ERROR/WARNING 扫描均未接线），
`requires_field_write` 无人执行。这与对齐审查的「保留意见」一致。BDD-51 的 Then 允许「已落实降级」
分支（数据已登记），故不阻断，但建议在 `P4-implementation-G2.md` 明确登记「T1–T3 接线留待后续批」为显式待办。

### L1–L6 [LOW]/观察

- **L1**：`check-frontmatter._declaration_files()`（`:28`）用 `current_level(__file__)`（全局最大级），
  `pre-commit-gate._declaration_files(task_dir)`（`:510`）用 `task_level(task_dir)`（任务级）。
  当前仅 level 1 ⇒ 恒等；level≥2 时会对在途任务分叉。
- **L2**：`_primary_output_for`（`:523`）与 `_declaration_files`（`:510`）用 `task_level`（最新级），
  而 `_check_prod_touched_primary` 的门控用 `requirement_active`（`level_at_phase`）——同一函数内两套等级口径。
- **L3**：`_scan_prod_touched_and_rerun`/2g.0 扫 `git diff --cached -- <task_rel>`（全部文件），
  非设计 §3.1 第 2 点的「全部暂存 `*.md`」。偏宽、fail-safe，且为既有行为（G2 未改）。
- **L4**：`pre-commit-gate.py:775` 保留 `re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$", ln)`（裸格式检查），
  是 `test_marker_single_source.py` mk_7b/mk_8 从源码抽取的守护对象；DESIGN_GAP-5 已裁定可接受。
- **L5**：`agate-frontmatter-check._check` 的类型错误文案由 Python 名改 JSON 名
  （`应为 str/int/bool/list` → `应为 string/integer/boolean/array`），`grep` 无测试守护该措辞。
- **L6**：`agate-frontmatter-check.py:69-117` 的 `_local_iter_errors`/`_local_max_depth` 是**不完全子集**
  的第二份递归遍历（缺 array/items/pattern），由 `agate_schema is not None` 门控 + 白名单守护；可辩护为
  安装破损 fail-safe，但字面上「只剩 1 个实现」不严格成立。

## 4. 处理规则声明

- 本评审**只说不改**：所有修复建议写在本文件，未改动任何代码/测试/被评审文件。
- B1/H1 属**逻辑/契约变更**：修复由主 Agent 回派 implementer 落地。
- M1/M2/L1–L6 为改进项，可由主 Agent 决定是否本批处理或登记 DEBT。

## 5. 留痕

- 副本：`/tmp/opencode/G2rev/`（含 `.git`）；临时 scratch：`/tmp/opencode/G2rev/scratch/`。
- 真实仓库只读命令：`git status --porcelain`、`git diff -- <files>`、`grep`、`sha256sum`、`read`。
- `sha256sum agate/rules/task-data/level-1.yaml` = `e96a06b2a7c7…`，与 `LEVELS.yaml` 登记一致（CHECK 16 PASS）。
- `[PROD_NOT_TOUCHED]`。
