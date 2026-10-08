---
review_date: 2026-10-08
reviewer: protocol-alignment-review
task_id: TAG0050
batch: G2-rereview (聚焦复评)
change_summary: TAG0050 批 G2 整改复评——只核 R1–R7 + GAP-2/3 是否闭合 + 是否引入新问题
files_changed: [agate/scripts/pre-commit-gate.py, agate/scripts/check-frontmatter.py, agate/scripts/check-gate.py, agate/scripts/README.md, agate/UPGRADING.md, docs/design-notes/design-md-field-set.md, agate/tests/integration/test_tag0050_prod_touched.py, agate/tests/integration/test_pre_commit_hook.py, agate/tests/unit/test_tag0050_write_tools.py, agate/tests/unit/test_tag0050_fitness.py, agate/tests/unit/test_dispatch_context_warning.py, agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py, agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G2.md, agate-workspace/tasks/TAG0050-task-data-contract/P4-progress.md]
---

# 协议-脚本对齐审查（TAG0050 批 G2 · 聚焦复评）

> **范围**：仅核上一轮 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G2.md` 的 **R1–R7**
> 与 **GAP-2/GAP-3** 是否闭合，以及整改是否引入新问题。不重开 A1–A8 全量（其结论见上一轮报告）。
> **基线**：HEAD `54a814fc`，G2 改动未提交。所有验证在**仓外可丢弃副本**上完成
> （`/tmp/opencode/G2rerev/`，rsync 工作树 + `.git`；未对被评审仓库做任何写操作）。

## 审查结论汇总

| # | 原问题 | 结论 |
|---|--------|------|
| **R1** | BDD-52 判据落空（DESIGN_GAP-3，BLOCKER） | **ALIGNED（已闭合）** |
| **R2** | `declaration_files` 死键 / F10 作用面不符 | **ALIGNED（已闭合）** |
| **GAP-2** | F10 在 gate 侧零强制力 | **ALIGNED（已闭合）** |
| **GAP-3** | BDD-52「缺 `prod_touched`→ERROR」未接强制点 | **ALIGNED（已闭合）** |
| **R3** | BDD-48 弱 + 缺 CRLF 覆盖 | **ALIGNED（已闭合）** |
| **R4** | BDD-53 弱 / BDD-50 子串守护 | **ALIGNED（已闭合）** |
| **R5** | README `agate-config.py` 行陈旧 | **ALIGNED（已闭合）** |
| **R6** | UPGRADING G2 节 / design note §7.2 / tests-README | **ALIGNED（已闭合）** |
| **R7** | E3 数字无据 / consistency 计数 | **ALIGNED（已闭合）** |
| 新问题① | `check-frontmatter._declaration_files` 用 `current_level`，与 `pre-commit-gate` 的 `task_level` 口径不一致 | **OBSERVATION（LOW，不阻断本批）** |
| 新问题② | `prod_touched` 修复命令行尾附中文注，整行照抄不可执行 | **OBSERVATION（LOW，不阻断本批）** |

> **闭环判断**：R1–R7 与 GAP-2/GAP-3 **全部闭合**；两项新问题均为 LOW、**不阻断本批 commit**。
> 未发现整改碰坏其它文件或引入平台假设。

---

## 逐条复核（命令 + 输出证据）

### R1（BLOCKER）— BDD-52 判据落空 —— **ALIGNED**

**整改点**：`pre-commit-gate.py::_check_prod_touched_primary` 补「主产出缺 `prod_touched` → ERROR + 修复命令」；`test_bdd_52` 重写为驱动真实强制点。

**证据 1（代码接线）**：`agate/scripts/pre-commit-gate.py:557-572`（`_check_prod_touched_primary`）：
```python
if "prod_touched" not in fm:
    sys.stderr.write(
        f"GATE: 主产出 {primary} 缺 prod_touched 字段（非 legacy 任务必填，设计 §4）\n"
        f"      修复命令: FILE={out_file} agate-md-field-set.py set prod_touched false（若未触达生产）\n"
    )
    sys.exit(1)
```
且在两条路径均被调用：`_scan_prod_touched_and_rerun`（`:592`）与 `main()` 2g.3（`:780`）。

**证据 2（仓外独立验证，非仓库自带测试）**：`/tmp/opencode/G2rerev/drive.py` 在仓外 scratch git repo 造非 legacy 任务（账本首行 `task_created` contract_level=1），装真 hook（`pre-commit-gate.sh` → `resolve-entry` → 副本 `pre-commit-gate.py`，`AGATE_ROOT` 指向副本），主产出 `P4-implementation.md` 缺 `prod_touched`，`git commit` 实测：
```
=== R1 missing prod_touched (hook) ===
rc=1
  contains '缺 prod_touched': True
  contains 'agate-md-field-set.py set prod_touched': True
GATE: 主产出 P4-implementation.md 缺 prod_touched 字段（非 legacy 任务必填，设计 §4）
      修复命令: FILE=/tmp/opencode/G2rerev/scratch/r1/agate-workspace/tasks/TAG0001/P4-implementation.md agate-md-field-set.py set prod_touched false（若未触达生产）
```

**证据 3（负向：改前红）**：副本内把 `if "prod_touched" not in fm:` 变异为 `if False and ...`，`test_bdd_52` 立即转红：
```
FAILED .../test_tag0050_prod_touched.py::test_bdd_52_missing_prod_touched_errors
E  AssertionError: BDD-52：须报缺字段，实际 'GATE P4: P4-review.md 不存在…'
```
且该红**恰好复现了上一轮的根因**：`rc` 仍为 1，但来自 P4 gate（`P4-review.md` 缺失），**与 `prod_touched` 无关** ⇒ 证明旧断言 `rc != 0` 无判别力，新断言（`缺 prod_touched` + 修复命令文案）才具判别力。变异后 `test_bdd_53` 仍绿（独立判别）。

**证据 4（正向）**：副本 `pytest test_tag0050_prod_touched.py -q` → 5 passed（含 `test_bdd_52`/`test_bdd_53`）。

**结论**：**ALIGNED**。DESIGN_GAP-3 已闭合。

---

### R2 — `declaration_files` 死键 / F10 作用面不符 —— **ALIGNED**

**整改点**：`check-frontmatter.py::_declaration_files()` 与 `pre-commit-gate.py:2g.2` 均改读快照 `declaration_files` 键。

**证据（消费方 + 取值）**：
```
$ grep -rn "declaration_files" agate/scripts/
pre-commit-gate.py:517:    decl = contract.get("declaration_files") if isinstance(contract, dict) else None
pre-commit-gate.py:829:            for fm_name in _declaration_files(task_dir):
check-frontmatter.py:30:        decl = contract.get("declaration_files") if isinstance(contract, dict) else None
check-frontmatter.py:100:        if basename in _declaration_files() and _task_is_non_legacy(file_path):
```
`pre-commit-gate.py:809` 的旧硬编码四文件元组已改为 `_declaration_files(task_dir)`（`:829`）。副本内以 `AGATE_ROOT` 指向副本实测取值：
```
current_level: 1
declaration_files: ['P1-requirements.md','P2-design.md','P6-acceptance.md','P6.5-judge-verdict.md','P7-consistency.md','P8-release.md']
primary_outputs.P4: P4-implementation.md
requires.prod_touched: True
```
生效面已从旧的 4 文件扩到快照 6 文件（含 `P6.5-judge-verdict.md` / `P8-release.md`）。新用例 `test_tag0050_r2_declaration_files_snapshot_effective` 锁定期望被拦（P8-release.md）。旧硬编码的 `fallback` 仅作安装破损降级（`_FALLBACK_DECLARATION_FILES`）。

**结论**：**ALIGNED**。

---

### GAP-2 — F10 在 gate 侧零强制力 —— **ALIGNED**

**整改点**：删 `AGATE_PRECOMMIT_GATE=1` 跳过（`check-frontmatter.py`）与 setdefault（`pre-commit-gate.py`）。

**证据 1（无残留跳过逻辑）**：
```
$ grep -rn "AGATE_PRECOMMIT_GATE" agate/scripts/ agate/tests/
agate/scripts/check-frontmatter.py:96:    # TAG0050 G2 闭合（GAP-2）：本项在 hook 路径同样生效（不再经 AGATE_PRECOMMIT_GATE 跳过）；
```
仅剩注释，无判定分支。

**证据 2（仓外独立验证）**：scratch repo 非 legacy 任务，主产出带 `prod_touched: false`，另暂存缺 frontmatter 的声明文件 `P8-release.md`，经真 hook 提交：
```
=== GAP2 declaration file missing frontmatter (hook) ===
rc=1
  contains 'P8-release.md': True
  contains 'frontmatter': True
GATE FRONTMATTER: .../TAG0001/P8-release.md frontmatter 格式错误：
  - P8-release.md: 非 legacy 任务的声明文件缺 frontmatter 块——请补 `---` 块后用 agate-md-field-set.py 写入字段（不回退正文正则）
```

**证据 3（负向）**：副本内把 F10 分支变异为 `if False and ...`，三用例同时转红：`test_bdd_47_missing_frontmatter_errors`、`test_bdd_47b_declaration_files_from_snapshot`、`test_tag0050_r2_declaration_files_snapshot_effective` ⇒ 守护具判别力、hook 路径确实生效。

**结论**：**ALIGNED**。DESIGN_GAP-2 已闭合。

---

### R3 — BDD-48 弱 + 缺 CRLF 覆盖 —— **ALIGNED**

**证据（`test_tag0050_write_tools.py::test_bdd_48_render_block_tamper_errors`，diff 确认）**：
- 新增 `@pytest.mark.windows_smoke`（对应设计 §3.5「纳入 windows_smoke」）；
- 双侧循环 `for nl, tag in (("\n","lf"), ("\r\n","crlf"))`：手改内容两侧均断言 `rc!=0` + `"渲染块" in output and "被手改" in output` + `"agate-md-field-set.py render" in output`（修复命令文案）；
- 正确内容两侧均断言 `"渲染块" not in output`（CRLF 规范化为 LF 后逐字节比较 → 无假阳性）。

**脚本侧**（`check-gate.py::_check_render_blocks`，`:1200-1246`）：`text.replace("\r\n","\n")` 归一后比对，输出 `GATE P6: 渲染块 {key} 被手改…修复命令: FILE=… agate-md-field-set.py render`。

**结论**：**ALIGNED**。

---

### R4 — BDD-53 弱 / BDD-50 子串守护 —— **ALIGNED**

**BDD-53**：`test_bdd_53_prod_touched_true_not_paused_aborts` 已改端到端（`h.install_pre_commit_hook` + `h.commit_with_hook`，真实 repo + hook），断言 `rc!=0` + `"prod_touched: true" in output and "中止" in output`。仓外 drive.py 独立复核：
```
=== R1b prod_touched true non-PAUSED (hook) ===
rc=1  contains 'prod_touched: true': True  contains '中止': True
GATE: 主产出 P4-implementation.md 声明 prod_touched: true 且当前不在 PAUSED（P4），commit 中止
```

**BDD-50**：`test_schema_single_source_only_agate_schema` 改机械判据：
```python
_RECURSIVE_SCHEMA_DEF = re.compile(r"^\s*def\s+_?(?:local_)?(iter_errors|max_depth)\s*\(", re.M)
_WHITELIST_SCHEMA_DUP = {"agate-frontmatter-check.py"}
```
扫描 `agate/scripts/*.py`（排除 `agate_schema.py`）找递归 schema 遍历定义；仅白名单 `agate-frontmatter-check.py`（且断言源码含 `"agate_schema is not None"` 门控 = 安装破损 fail-safe）。实测全仓命中仅：`agate_schema.py`（单源，被排除）+ `agate-frontmatter-check.py` 的 `_local_iter_errors`/`_local_max_depth`/`_iter_errors`/`_max_depth`（白名单，且门控）⇒ 机械判据成立。

**结论**：**ALIGNED**。

---

### R5 — README `agate-config.py` 行陈旧 —— **ALIGNED**

`agate/scripts/README.md:164`（diff 确认）命令集已更新为：
```
init（幂等，不覆盖）/ validate（schema 校验）/ get <field> / set <field> <value> / unset <field> / explain <field> / list / show
```

**结论**：**ALIGNED**。

---

### R6 — 文档传播 —— **ALIGNED**

- `agate/UPGRADING.md`：新增「未发布 — TAG0050 批 G2」节（含 B/C 两段：F10、渲染块、7 操作、`prod_touched` 必填/中止、T4 单源；并声明**无破坏性变更**、只对非 legacy 任务生效）。
- `docs/design-notes/design-md-field-set.md` §7.2：加注「⚠️ 已被 TAG0050 取代（2026-10-08）…依据 ADR-014」，消除与 DESIGN_GAP-1 的矛盾口径。
- `tests/README.md` 脚本→测试映射（上一轮的「约定项」）本批未补——非门禁项，可接受（不计缺口）。

**结论**：**ALIGNED**。

---

### R7 — 无据数字 / 计数不符 —— **ALIGNED**

- `P4-implementation-G2.md §4`：删除 `~48/~2`、`~49/~1` 精确数字，改为「不登记精确分类数字」，并入库抽样脚本 + 种子：`e3_sample.py`（`agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py`）。仓内可复现命令实测：
  ```
  $ python3 agate-workspace/tasks/TAG0050-task-data-contract/e3_sample.py . 5 20261008
  # corpus=. total_hits=483
  ... （抽样行）
  rc=0
  ```
  `total_hits` 随工作树新增文件浮动，与文档口径一致。
- `§6` consistency 计数改为「0 ERROR，WARNING 数随工作树新增未跟踪文件浮动」。
- `P4-progress.md`：G2 前自陈「BDD-52/53 已绿」已修正为「**G2 前即绿但无判别力**……R1/R4 整改后重写为驱动真实强制点，方具判别力」。

**结论**：**ALIGNED**。

---

## 夹具更新是否削弱断言（dispatch 专项核查）

`agate/tests/integration/test_pre_commit_hook.py` 与 `agate/tests/unit/test_dispatch_context_warning.py` 的 diff **仅新增契约要求的字段内容**，**无任何断言放宽**：

| 夹具位置 | 改动 | 性质 |
|---|---|---|
| `:433 _P1_REQ` | frontmatter 内加 `prod_touched: false` | 契约驱动 |
| `:623/:647/:671/:751` P6 夹具 | 加 `---\nagent: test\nprod_touched: false\n---` | 契约驱动（P6 为声明文件 + 主产出） |
| `:871/:915/:1586` P2 夹具 | frontmatter 加 `prod_touched: false` | 契约驱动 |
| `:1199` P2 夹具 | 加 `---\nprod_touched: false\n---` | 契约驱动 |
| `:1239` P6 夹具 | 加 `prod_touched: false` | 契约驱动 |
| `:1688` P3 夹具 | `P3-test-cases.md` 加 `---\nprod_touched: false\n---` | 契约驱动（P3 为主产出，2g.3 要求） |
| `:1702` 新增 | `test_tag0050_r2_declaration_files_snapshot_effective` | 新增守护 |

判定：**只允许契约驱动的夹具演进**——本次夹具代表的都是**合法的非 legacy 任务提交**，按新契约其主产出/声明文件本就应带 frontmatter 与 `prod_touched`；编码旧契约的夹具随契约更新，属**契约驱动**，非「为迁就实现放宽断言」。**未发现削弱**。

---

## 新引入问题核查

**回归**：副本全量 `pytest agate/tests/{unit,integration} -q -n auto` = **8 failed / 2721 passed / 3 skipped**。8 条失败与基线逐条一致——把副本 `agate/` 改动 `git stash` 后重跑同 8 用例：
```
FAILED test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED test_tag0050_declarations.py::test_bdd_63_parallel_ids_no_collision
FAILED test_tag0050_declarations.py::test_bdd_66_followup_debt_backref_required
FAILED test_tag0050_proxy_judgment.py::test_bdd_69_skeleton_prose_not_treated_as_heading
FAILED test_tag0050_proxy_judgment.py::test_bdd_71_t2_catches_nonconforming_bdd_heading
FAILED test_tag0050_cross_batch.py::test_bdd_76_baseline_reset_in_changelog
FAILED test_tag0050_evidence.py::test_bdd_59_run_ref_sha256_mismatch_errors
FAILED test_tag0050_evidence.py::test_bdd_60_extract_context_counts_equal_computed
8 failed, 15 passed
```
⇒ 全部为**既有预期红灯**（D/E/F 批未实现 + BDD-43 环境漂移），**整改未引入新回归**。
（注：副本 passed/skipped = 2721/3，P4-implementation §6 记 2722/2；差 1 属副本环境差异，非代码问题。）

**其它守卫**（真仓只读实跑）：`check-protocol-consistency.py` → **0 ERROR / 411 WARNING（浮动）**；`count-tests.sh` → **2835**（与 §6 一致）；`check-platform-assumptions.py` → rc=0；`ruff check agate/scripts/` → All checks passed。

**新问题①（LOW，OBSERVATION）**：`check-frontmatter.py::_declaration_files()` 取集合用 `agate_common.current_level(__file__)`（全局最大等级），而 `pre-commit-gate.py::_declaration_files(task_dir)` 用 `task_level(task_dir)`（任务实际等级）。当前快照只有 level 1，两者恒等、无实际影响；但设计 §2.1 的「新增/收紧要求登记新一级，避免追溯在途任务」原则下，未来 level≥2 时二者会对在途任务分叉（check-frontmatter 侧用新级集合，pre-commit-gate 侧用任务级集合）。**建议**：后续将 `check-frontmatter._declaration_files()` 亦按任务等级取值（与 pre-commit-gate 同源口径）。不阻断本批。

**新问题②（LOW，OBSERVATION）**：`_check_prod_touched_primary` 的修复命令 `FILE=<path> agate-md-field-set.py set prod_touched false（若未触达生产）` 行尾附中文注解，**整行照抄会在 shell 里多传一个参数**（BDD-49「照抄执行」的可执行性）。BDD-52 的 Then 只要求「附修复命令」（已满足，`test_bdd_52` 断言到），故非硬缺口。**建议**：注解另起一行，或去掉注解使该行可直接复制。不阻断本批。

---

## 闭环判断

R1（BLOCKER）、R2、GAP-2、GAP-3、R3–R7 **全部闭合**，且经**仓外副本独立验证**（含 R1/GAP-2 的正向 + 负向判别力证据）。未发现断言削弱、回归或平台假设引入。两项新问题为 LOW 级观察、不阻断。

**本轮结论：ALIGNED（可 commit）**——G2 整改已满足 self-gate 的 R1–R7 + GAP-2/3 闭合要求。
