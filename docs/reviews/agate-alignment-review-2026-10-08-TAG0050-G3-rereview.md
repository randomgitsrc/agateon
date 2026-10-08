---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 批 G3 整改第 2 轮聚焦复评——A1–A5 与 GAP-1/2/4/5/6/7/8 闭合核验（不重开全量；A6–A8 沿用前轮结论）
files_changed:
  - agate/scripts/check-gate.py
  - agate/scripts/check-pruning.py
  - agate/scripts/check-frontmatter.py
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/check-p6-provenance.py
  - agate/scripts/agate-md-field-set.py
  - agate/scripts/agate_common.py
  - agate/rules/task-data/level-1.yaml
  - agate/rules/task-data/LEVELS.yaml
  - agate/tests/conftest.py
  - agate/tests/integration/test_pre_commit_hook.py
  - agate/tests/integration/test_tag0050_evidence.py
  - agate/tests/unit/test_tag0050_declarations.py
  - agate/tests/unit/test_tag0050_proxy_judgment.py
  - agate/UPGRADING.md
  - CHANGELOG.md
  - agate/WORKFLOW.md
  - agate/scripts/README.md
  - agate/assets/templates/task-files.md
---

# 协议-脚本对齐审查 — TAG0050 批 G3 聚焦复评

> **范围**：仅核上一轮 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G3.md` 判定的
> **A1–A5 + GAP-1/2/4/5/6/7/8 是否闭合**，以及是否引入新问题。**不重开全量**；A6–A8 沿用前轮结论。
> **方法**：只读 diff 核验 + **仓外可丢弃副本**（`/tmp/opencode/g3rr`，`cp -r agate agate-workspace`）
> 上的**直接注入实验**与**变异实验**；结果文件/留痕文件未触碰被评审文件。
> **触发面**：`agate/scripts/*.py` / `agate/rules/*.yaml` / `agate/**/*.md` / `README.md` / `CHANGELOG.md`（SELF-GATE 全触发）。
> **HEAD**：`b746d07d`（G3 改动未提交，44 tracked）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（过度承诺已去除；`requires.results` 与执行面单源） |
| A2 | 脚本→文档对齐 | **ALIGNED**（单参 CLI + 4 脚本行为变化已登记 README；`declaration_globs` 已删） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（新字段已传播到模板/卡片/关键角色卡；**残留**见 §残留项 R2） |
| A4 | 测试覆盖 | **ALIGNED**（要求的 8 条补强 + 6 条新增均已落地且有判别力；**残留覆盖缺口**见 §残留项 R1） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（`gate_p2` UI 加 `task_level` 门；R6 复跑 39 legacy / 0 差异；CHANGELOG/UPGRADING 同步） |
| A6 | 锚点表覆盖 | 本轮不重开（前轮 ALIGNED） |
| A7 | 设计原则一致性 | 本轮不重开（前轮 ALIGNED） |
| A8 | 声称-命令绑定 | 本轮不重开；E2 结论已 `[HUMAN_CONFIRMED: 2026-10-08]` 落盘（前轮 NEEDS_HUMAN_REVIEW 关闭） |

**总体**：**A1–A5 + GAP-1/2/4/5/6/7/8 全部闭合**；**未发现新引入的语义缺陷**。另有 2 项**非阻断残留**
（R1 测试覆盖缺口、R2 反向传播未覆盖 `architect.md`/`analyst.md` 且未登记 DEBT），建议随批处理。
按闭环规则：**可 commit**（残留项为建议，非 MISALIGNED）。

---

## 主 Agent 裁定落实核验

| 裁定 | 落实证据 | 结论 |
|---|---|---|
| GAP-4 `phase_universe` → `[P1..P8]`（排除 P0/P6.5），**恒检** | `level-1.yaml:34` 值 = `[P1, P2, P3, P4, P5, P6, P7, P8]`；`check-pruning.py:198-225` 非 legacy 无条件闭合判定 | **已落实** |
| E2 采信重释 | `P4-implementation-G3.md` §0 记 `[HUMAN_CONFIRMED: 2026-10-08 确认：E2 判据采信实现者重释]` | **已落实** |
| `gate_p2` UI 加 `task_level` 门 | `check-gate.py:627` `if isinstance(ui_design, dict) and task_level(_task_dir) is not None:` | **已落实** |

---

## 逐条复核（命令 + 输出）

> 全部实验在仓外副本 `/tmp/opencode/g3rr` 上运行；`AGATE_ROOT` = 副本 `agate/`；构造非 legacy 任务
> （账本首行 `task_created`，等级 1）。脚本 `/tmp/opencode/verify_g3.py`。

### GAP-1 — 非 legacy 缺 `results` → `gate_p6` ERROR（闭合）

**实现**：`check-gate.py:1612` `if requirement_active(task_dir, "results", "P6") is True:` → `_gate_p6_structured`；
`_gate_p6_structured:1431-1435` `items is None` → 报错 `return 1`（不回退正文）。`level-1.yaml:20` `requires.results: true`。

**证据**：
```
① 非 legacy 缺 results → gate_p6: rc=1
   GATE P6: 非 legacy 任务须在 P6-acceptance.md 声明结构化 `results`（设计 §5.1）
①b results bdd 集合 != P1 → rc=1
   GATE P6: results 的 bdd 集合与 P1 不相等（D1）——P6=['1'], P1=['1', '2']
```
**结论：ALIGNED（闭合）**。

### GAP-2 — `reviewed_bdds` 缺失/不等 → ERROR（闭合）

**实现**：`check-gate.py:786-805`（`task_level(task_dir) is not None` 门）—— `rv is None` → ERROR；`declared != actual_bdds` → ERROR。

**证据**：
```
② reviewed_bdds 缺失 → P1 gate: rc=1
   GATE P1: 非 legacy 任务的 P1-review.md 须声明 `reviewed_bdds`（= P1 的 BDD 集合，设计 §7）
②b reviewed_bdds 不等 → rc=1
   GATE P1: reviewed_bdds（['2']）与 P1 BDD 集合（['1']）不相等
```
**结论：ALIGNED（闭合）**。

### GAP-4 — `phases ∪ pruned ≠ [P1..P8]` → ERROR（**恒检**，闭合）

**实现**：`check-pruning.py:198-225` —— 非 legacy 任务**无条件**跑闭合判定（`pruned` 缺省按空集）；
`_phase_universe` 读快照 `[P1..P8]`；`pruned` 条目校验快照 `required_fields=[phase, reason, risk]`。

**证据**：
```
③a phases=[P1..P8] 完整，未声明 pruned → check-pruning rc=0
③b phases 缺 P4，未声明 pruned → rc=1
   GATE PRUNING: ... phases ∪ pruned.phase != 阶段全集：缺=['P4'], 多=[]
   （恒检生效：未声明 pruned 也报——不再是"仅声明时"）
③c phases 缺 P4 + pruned 覆盖 P4 → 闭合错误消失（余下为 P4 不可裁剪/跳过风险等既有条目）
③d pruned 条目缺 reason → rc=1
   GATE PRUNING: ... pruned 条目缺必填字段：['reason']
```
**结论：ALIGNED（闭合）**。

### GAP-5 — F 批结构化字段判据改读快照（闭合）

**实现**：`level-1.yaml` 注册 `ui_design.shape_dimensions`（layout→[布局]/[交互]/[视觉] 等）、`delivery`、`pruned`；
`check-gate.py:505-516` `_ui_shape_dimensions` 读快照；`gate_p2:641-652` 补「必填维度存在」判据；
`gate_p8:2108-2138` `_delivery_spec` 读快照 `delivery`。
**证据**：副本 `test_gap5_ui_design_missing_required_dimension_errors` 通过（实测 rc=1 且含「必填维度」）。
**结论：ALIGNED（闭合）**。

### GAP-6 — D5/D7/D9 + D3 pre-commit（闭合，测试有判别力）

**实现**：`_gate_p6_structured` —— D5（`check-gate.py:1531-1538` 内容相同 → WARNING 不阻断）、
D7（`:1540-1564` evidence JSON FAIL vs results PASS → ERROR）、D9（`:1566-1581` `_p6_reuse_blocked` → ERROR）、
D3（`:1490-1498` `AGATE_PRECOMMIT_GATE==1` 时 `_is_tracked_or_staged` 否则 ERROR）。
**变异实验**（scratch，逐条禁用后跑对应用例）：
```
D5 禁用 → test_gap6_d5_duplicate_content_warns_not_blocked  FAILED（转红）
D7 禁用 → test_gap6_d7_evidence_json_fail_vs_results_pass     FAILED（转红）
D9 禁用 → test_gap6_d9_reuse_blocked_from_results             FAILED（转红）
```
**结论：ALIGNED（闭合）**；D5/D7/D9 判别力已验证。

### GAP-7 — provenance 非 legacy 跳过（闭合）

**实现**：`check-p6-provenance.py:420-431` 计算 `non_legacy`；审计 1（:452）/3（:605）/4（:651）/5（:717）/6（:764）加 `and not non_legacy`；与 D7 成对。
**证据**：副本 `test_gap7_provenance_body_audit_skipped_for_non_legacy` 通过。
**结论：ALIGNED（闭合）**。

### GAP-8 — `declaration_files` 扩 glob、删 `declaration_globs`（闭合）

**实现**：`level-1.yaml:96-112` 扩为各阶段主产出 + `*-review.md` + `P4-implementation-*.md` + `P4-implementation/**/*.md`；
`grep -r declaration_globs agate/` → 仅注释提及（键已删）；`check-frontmatter.py:46-63` / `pre-commit-gate.py:596-612` /
`agate-md-field-set.py:345-351` 均按 glob（相对路径 + basename）匹配。
**证据**：
```
⑤a P2-review.md（*-review.md glob）缺 frontmatter → rc=1
   GATE FRONTMATTER: ... 非 legacy 任务的声明文件缺 frontmatter 块 ...
⑤b P4-implementation-batch1.md（P4-implementation-*.md）缺 frontmatter → rc=1
⑤c 非声明文件 notes.txt 缺 frontmatter → rc=0（无过度命中）
```
**结论：ALIGNED（闭合）**。

### A1 — 文档→脚本对齐（闭合）

- `UPGRADING.md`「未发布 — TAG0050 批 D/E/F」明确「判据 D1–D10 已全部落地，含 D5/D6/D7/D9」——与实现一致（不再过度承诺）；
  「缺 `results` 即 ERROR」「pre-commit 中还须已跟踪/已暂存」「`phases ∪ pruned == phase_universe`（`[P1..P8]`）恒检」
  均与实际实现逐条对应。
- `requires.results: true` 与 `gate_p6` 的 `requirement_active(...,"results","P6")` **单源**一致（§2.5）。
- **结论：ALIGNED**。

### A2 — 脚本→文档对齐（闭合）

- `agate/scripts/README.md` 已登记 `agate-extract-context.py` **单参形式**（GAP-3 的可接受条件满足）；
  并登记 `check-pruning` / `check-scope-resolved` / `check-retrospective` / `check-judge-verdict` 的非 legacy 行为变化。
- `declaration_globs` 删除后说明同步（level-1.yaml 注释 + README）。
- **结论：ALIGNED**。

### A3 — 一致性连锁 + 反向传播（闭合；残留见 R2）

- 新结构化字段已传播：`assets/templates/task-files.md`（P1/P2/P6/P7 样例块）、
  `phase-cards/{P1,P2,P6,P7,P8}`、`execution-roles/{verifier,consistency-reviewer}.md`、
  `review-roles/requirements-review.md`、`WORKFLOW.md`「Pre-commit 检查总览」（含 2h 跳过 + 2.1/2.7/2.11/2.12 非 legacy 分支）。
- `LEVELS.yaml` sha256 重登记，实测 `sha256(LF 归一 level-1.yaml)=3b2af190…` == 登记值 ✓（CHECK 16 冻结未破坏）。
- **残留 R2**（非阻断）：`execution-roles/architect.md`（仍仅有 `ui_design_section`，未含新 `ui_design` 结构化样例）、
  `analyst.md` 及 `review-roles/*`（`requirements-review` 之外）未同步；整改指引允许「显式登记 DEBT（引用 DEBT0039）」
  替代，但**未见 DEBT 登记**。
- **结论：ALIGNED**（核心传播已完成；R2 建议随批补或登记 DEBT）。

### A4 — 测试覆盖（闭合；残留覆盖缺口见 R1）

- 要求的补强全部落地且有判别力：`test_bdd_56` 覆盖 F1 的 A/B/C（副本实测三子断言均经 D2/D1/重复路径红）；
  `test_bdd_57/58` 改走 `gate_p6`（断言含 D3/D6）；`test_bdd_59` 构造真实 sha256 不一致（断言含 `sha256`）；
  `test_bdd_60` 断言 `P6 验收: 1 PASS, 0 FAIL`（== 现算值）；`test_bdd_62/64/65` 增判别性断言。
  新增 `test_gap5_*` / `test_gap6_d5/d7/d9` / `test_gap7_*` / `test_gap8_*`。
- 副本实跑目标 6 文件：**91 passed / 3 failed**（3 failed = `test_bdd_74/75/76`，因副本缺根文档
  `docs/design-notes/r6-allowlist.yaml` / `CHANGELOG.md` 与 consistency 环境——**非本批缺陷**，与上一轮观察一致）。
- **夹具未削弱**（逐条核，均契约驱动）：`_P1_REQ` phases 去 `P0`（随 `phase_universe=[P1..P8]`）；
  `it9/it9b` 补结构化 `pruned`（随闭合恒检）；`_write_p1_review` 与 `conftest.init_task` 补 `reviewed_bdds`
  （`_P1_REQ` 无 `#### BDD-` 标题 ⇒ `[]`、`init_task` 有 BDD-1 ⇒ `['1']`，均正确）；
  T086 改结构化 `results`（随 P6 新契约，且断言由「rc==0」增为带输出）；`bdd_62` 清理隔离面并**新增**判别断言。
- **残留 R1**（非阻断，建议补测）：三个负向分支**无直接测试守护**——禁用守卫后目标集仍 3 failed/88 passed（基线噪声，无新红）：
  ① 非 legacy **缺 `results`**；② 闭合**恒检（未声明 pruned 时）**；③ **`reviewed_bdds 缺失`**（现仅 test_bdd_68 测 mismatch）。
  另 `_is_tracked_or_staged` / `AGATE_PRECOMMIT_GATE`（D3 pre-commit）与 `pruned` 缺必填字段在 tests 中 0 命中。
- **结论：ALIGNED**（要求的覆盖已达标；R1 建议补 3 条负向用例）。

### A5 — 下游影响 + 文档传播（闭合）

- **§8 legacy 承诺**：所有新分支均门控于非 legacy（逐一核：`gate_p6` `requirement_active`；`gate_p1/p2/p7/p8`
  `task_level`；`check-pruning` `task_level`；`check-frontmatter` `_task_is_non_legacy`；`check-p6-provenance`
  `non_legacy`；2h 跳过条件 `task_level(...) is None`）→ legacy 走原路径。
- **语料实测**：`agate-workspace/tasks/` 含账本任务 **22 个，非 legacy = 0** ⇒ 新契约分支不触发生效任何存量任务。
- **R6 复跑**：`P4-implementation-G3.md` §7 记「legacy 39 任务 / 差异 0 / 未匹配 0 / exit 0」（仓外副本）。
- `CHANGELOG.md` / `UPGRADING.md` 已同步；`gate_p2` UI 检查已加门（见裁定落实表）。
- **结论：ALIGNED**。

---

## 残留项（非阻断，建议处理）

| # | 残留 | 证据 | 建议 |
|---|------|------|------|
| R1 | 三个负向分支无测试守护（缺 results / 闭合恒检 / reviewed_bdds 缺失）；D3 pre-commit 与 pruned 必填字段亦无 | 变异实验禁用守卫后目标集无新红；`grep` tests 0 命中 | 各补 1 条负向用例（可直接复用独立验证脚本用例） |
| R2 | `architect.md`/`analyst.md`/其余 `review-roles/*` 未同步新结构化字段，且未登记 DEBT | `grep ui_design agate/assets` 仅 P2 卡/task-files；debt `tech-debt.md` 无新条目 | 补齐或显式登记 DEBT（引用 DEBT0039） |
| R3 | `check-gate.py:1697` 函数名 `_declaration_globs()` 保留旧键名（实际读 `declaration_files`） | 同名函数 docstring 已注明 | 重命名（cosmetic，不影响行为） |

---

## 闭环规则

- **A1–A5 + GAP-1/2/4/5/6/7/8**：**ALIGNED**（闭合）→ 通过。
- **残留 R1/R2/R3**：非阻断建议（非 MISALIGNED）——不强制修复；R1/R2 建议随批处理。
- 前轮 **NEEDS_HUMAN_REVIEW**（A8 的 E2 结论、GAP-4 `phase_universe` 语义、`gate_p2` UI 未加门）：
  三项均已附 `[HUMAN_CONFIRMED: 2026-10-08]` 并落实（见「主 Agent 裁定落实核验」）。

## 环境隔离

[PROD_NOT_TOUCHED] 全程只读：仅 `git diff`/`grep`/`read`/只读 `check-protocol-consistency.py`/`count-tests.sh`；
注入与变异实验仅在仓外一次性副本 `/tmp/opencode/g3rr` 上做（`cp -r`，可丢弃）。未编辑被评审文件；
运行前后真实仓 `git status --porcelain` 一致（44 tracked + 未跟踪派发/进度文件），无账本污染。
