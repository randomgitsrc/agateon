---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G3.md
trace_id: TAG0050-P4-20261008
agent: review
status: rejected
---

# P4 实现评审（独立）— TAG0050 批 G3（D + E + F）

> 角色：`review`（偏执 Staff Engineer）。对象：G3 **未提交**改动，HEAD `b746d07d`，
> 分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 范围：`P4-dispatch-context-review-G3.md` 的 6 个重点核验项；不重做设计。
> 依据：`P2-design.md` §3/§5/§6/§7/§8、`P1-requirements.md` §4（BDD-56..72）、
> `docs/design-notes/design-tag0050-task-data-contract.md` §5/§6/§7、两份 SELF-GATE 对齐审查报告。
> 只读纪律：**未编辑任何被评审文件**；全部变异/注入实验在**仓外可丢弃副本** `/tmp/opencode/g3rev/` 上进行；
> 真实仓库仅执行只读命令（`read`/`grep`/`git diff`/`git status`/`check-protocol-consistency.py`/`sha256`）。
> 环境隔离：`[PROD_NOT_TOUCHED]`（全程未接触生产环境；peekview 未打开）。

## 结论

**rejected** — 发现 **1 个 BLOCKER**（P6.5 `criteria` 读取链路断裂，非 legacy 任务 P6.5 **恒不可通过**），
另有 3 项 MINOR。BLOCKER 未被前序 SELF-GATE（`agate-alignment-review-2026-10-08-TAG0050-G3{-rereview}.md`）
捕获：该路径**无任何测试守护**，对齐审查的 A1「ALIGNED」结论因此不成立。

| # | 严重度 | 位置 | 摘要 |
|---|--------|------|------|
| 1 | **BLOCKER** | `check-judge-verdict.py:503,528` + `agate_common.py:594-600` | `read_judge_verdict()` 返回值**不含 `criteria`**，故 `verdict.get("criteria")` 恒为 `None` → 非 legacy 任务 P6.5 一律 exit 1 |
| 2 | MINOR | `check-gate.py:1521-1529`（D8） | 截图"须带 vision，无视觉能力才退 manual_review"退化为"二选一即可" |
| 3 | MINOR | `check-gate.py:1540-1564`（D7） | 只做单向启发式（evidence FAIL vs results PASS），未覆盖反向与字段形态 |
| 4 | MINOR | `check-gate.py:1812-1818,1826-1833` | `design_gap_reviews.verdict` / `basis` 取值域未校验（`in_bdd`/`out_of_scope`/`followup:DEBT<n>` 之外的串被放行） |

---

## BLOCKER-1（CRITICAL）：P6.5 `criteria` 读取链路断裂

### 现象
设计 §5.2 要求非 legacy 任务在 `P6.5-judge-verdict.md` frontmatter 声明
`criteria: [{bdd, verdict, evidence}]`，`criteria_total`/`criteria_passed`/`verdict_evidence`
为**系统字段**（由 `criteria` 现算）；`check-judge-verdict.py` 第 4–6 条改读 `criteria`。
实现中该读法**永远拿不到 `criteria`**：

- `check-judge-verdict.py:503` `verdict = read_judge_verdict(task_dir)`
- `check-judge-verdict.py:528` `criteria = verdict.get("criteria")` → 恒 `None`
- `agate_common.py:594-600` `read_judge_verdict()` 固定返回
  `{status, criteria_total, criteria_passed, verdict_evidence, partial}`，**没有 `criteria` 键**
  （本文件未被 G3 改动，`git diff` 未涉及 `read_judge_verdict`）。

于是非 legacy 分支在 `check-judge-verdict.py:534-539` 恒命中：
```
GATE JUDGE-VERDICT: 非 legacy 任务须在 frontmatter 声明 criteria（设计 §5.2）
```
并且更早地（`:516-524`）会因 `criteria_total`/`criteria_passed`/`verdict_evidence`
（系统字段，按设计 agent 不应写）缺失而先报 `criteria_total 缺失或非整数`。
由于 `gate_p65`（`check-gate.py:1689-1692`）以 `check-judge-verdict.py` 的退出码为准，
**任何非 legacy 任务的 P6→P7 转移都被死锁**。

### 可复现证据（仓外副本 `/tmp/opencode/g3rev/`）
构造非 legacy 任务（账本首行 `task_created` contract_level=1；P1 一条 `#### BDD-1:`；
`P6-evidence/e1.json`；verdict 只声明 `criteria`）：
```
$ AGATE_ROOT=/tmp/opencode/g3rev/agate python3 agate/scripts/check-judge-verdict.py /tmp/opencode/g3rev/task
GATE JUDGE-VERDICT: criteria_total 缺失或非整数
EXIT=1
```
verdict **同时**补上四个系统字段后仍失败（证明 `read_judge_verdict` 丢弃 `criteria`）：
```
$ AGATE_ROOT=/tmp/opencode/g3rev/agate python3 agate/scripts/check-judge-verdict.py /tmp/opencode/g3rev/task2
GATE JUDGE-VERDICT: 非 legacy 任务须在 frontmatter 声明 criteria（设计 §5.2）
EXIT=1
```
副本上 TAG0050 目标三文件 `24 passed`，但**没有一个用例触及非 legacy 的 P6.5 `criteria` 路径**
（`grep -rn "criteria" agate/tests/integration/test_tag0050_*.py agate/tests/unit/test_tag0050_*.py` 无命中）
⇒ 绿灯不代表新判据生效。

### 与文档/对齐审查的冲突
- `UPGRADING.md`「未发布 — TAG0050 批 D/E/F」明文承诺
  「**P6.5** 读结构化 `criteria: [{bdd, verdict, evidence}]`（`criteria_total`/`criteria_passed`/
  `verdict_evidence` 现算）」；`CHANGELOG.md` Unreleased 同款承诺 → 均**不成立**（过度承诺复发）。
- SELF-GATE 复评（`…-G3-rereview.md` §A1）判「ALIGNED（`requires.results` 与执行面单源）」，
  但未覆盖 P6.5 `criteria`；其 §残留项 R1 仅提到"三个负向分支无测试"，未识别本**功能性缺陷**。

### 修复方向（交主 Agent 回派 implementer）
- 在 `agate_common.read_judge_verdict()` 返回 dict 中**透传 `criteria`**（例如
  `"criteria": data.get("criteria")`）；**且**把 `check-judge-verdict.py:516-524` 对
  `criteria_total`/`criteria_passed`/`verdict_evidence` 的强校验移到 `_non_legacy` 判定**之后**
  （非 legacy 时先由 `criteria` 现算，再校验；legacy 保留旧口径）。
- 补 1 条非 legacy 正向用例（声明 `criteria` 且 `status: passed` → exit 0）与 1 条负向用例
  （缺 `criteria` → exit 1），并在 P3-test-cases 登记计数变化。

---

## 6 个重点核验项逐项结论

### 项 1 — 批 D（设计 §5）：D1–D10 / judge / agate-run / extract-context / 跳过面
| 子项 | 位置 | 结论 |
|---|---|---|
| D1 bdd 集合相等/不重复 | `check-gate.py:1437-1453` | ✅ 正确（含重复检测） |
| D2 全 PASS | `:1455-1462` | ✅ |
| D3 `resolve_evidence_ref` + ignore + pre-commit「已跟踪/已暂存」 | `:1478-1498`；`_is_tracked_or_staged:1392-1400`；`pre-commit-gate.py:716` 置 `AGATE_PRECOMMIT_GATE=1`（子进程 env 继承，已核 `_run_script_rc` 不传 env=） | ✅ |
| D3 fail-closed 且区分「事件缺失」vs「sha256 不匹配」 | `agate_common.py:resolve_evidence_ref`（新增）— 两条错误文本可区分 | ✅ |
| D4 P6-evidence 全被引用 | `:1583-1594` | ✅ |
| D5 内容重复 WARNING（不阻断） | `:1499-1538` | ✅ |
| D6 PASS 日志 `EXIT_CODE=0` | `:1507-1520` | ✅ |
| D7 证据 JSON vs results | `:1540-1564` | ⚠️ 见 MINOR-3（弱化） |
| D8 截图须 vision/manual_review | `:1521-1529` | ⚠️ 见 MINOR-2（弱化） |
| D9 `_p6_reuse_blocked` 从 results 读复用 | `:1566-1581` | ✅（与 provenance 审计 7 有重复，不违反） |
| D10 渲染块 | `_check_render_blocks:1319-1366` | ✅ |
| `check-judge-verdict` 第 4–6 条读 `criteria` | `check-judge-verdict.py:526-608` | ❌ **BLOCKER-1** |
| `agate-run --task` + `run:<k>`（`k`/`log`/`sha256`） | `agate-run.py:235-251,168-202` | ✅ |
| `agate-extract-context` 计数 = 现算值 | `agate-extract-context.py:238-300`；`BDD-60` 断言 `1 PASS, 0 FAIL` | ✅（副本实测通过） |
| 非 legacy 跳过 `check-p6-format` + provenance 正文解析 | `pre-commit-gate.py`（2h 加 `task_level(...) is None` 门）；`check-p6-provenance.py:417-431` + 审计 1/3/4/5/6 各加 `and not non_legacy` | ✅ |

### 项 2 — 批 E（设计 §6）：成对声明
- 跨文件聚合（`_aggregate_list:1714-1729`，glob 面 = 快照 `declaration_files`）：✅；`test_bdd_62` 已加判别断言。
- ID `<相对路径去 .md>:<前缀><n>`、每文件独立编号（`agate-md-field-set._autonumber_id`，含 `_relative_stem`/`_task_dir_for`）：✅。
- 集合不等 / 悬空 id → ERROR（`gate_p7:1826-1833`、`1870-1886`）：✅。
- `resolved` 缺 `resolution`/`evidence` → ERROR（`:1795-1805`）：✅。
- `basis: followup:DEBT<n>` 双向回指（`:1835-1868`，`_read_debt_source_refs`）+ `source_ref` schema（`agate-debt-check.py:SOURCE_REF_RE`）：✅（`SOURCE_REF_RE` 仅校验任务 ID 前缀，`<DG id>` 部分宽松——前轮已判可接受）。
- markers 补 5 标记 + schema 放开 `-`（`markers.yaml` / `markers.schema.json`）：✅。

### 项 3 — 批 F（设计 §7）：代理判定
- `reviewed_bdds` 必填且 = P1 BDD 集合（`check-gate.py:786-805`，`task_level` 门）：✅ 恒检。
- P2 UI `na` 无 reason → ERROR（含 `task_level` 门，`:606-652`）：✅（A5 已加门）。
- 快照 `ui_design.shape_dimensions` + 「必填维度存在」（`:641-652`，`_ui_shape_dimensions`）：✅；`test_gap5_*` 通过。
- 骨架标题级判定（RM-AG0085，`:1103-1114`，对全部任务生效）：✅。
- P8 `delivery` 结构化（F12）+ 读快照（`:2108-2138`，`_delivery_spec`）：✅。
- `pruned` 恒检闭合（`check-pruning.py:196-227`，`phase_universe=[P1..P8]`）：✅。
- T2 绊线（`gate_p1:762-781`，置于 `reviewed_bdds` 之前）：✅。

### 项 4 — 快照单源
- `declaration_files` glob 扩展（含 `*-review.md`/`P4-implementation-*.md`/`P4-implementation/**/*.md`；删 `declaration_globs`）：✅（`level-1.yaml:103-115`；消费方同步 `check-gate`/`check-frontmatter`/`pre-commit-gate`/`agate-md-field-set`/`check-scope-resolved`/`check-retrospective`）。
- sha256 重登记（CHECK16）：✅ **实核** `sha256(LF 归一 level-1.yaml)=3b2af190…` == `LEVELS.yaml` 登记值；`check-protocol-consistency.py` **0 ERROR / 410 WARNING**（CHECK 16 PASS）。

### 项 5 — legacy 兼容（§8）
- 各新分支均门控于非 legacy（逐核：`gate_p6` `requirement_active`；`gate_p1/p2/p7/p8`、`check-pruning`、`check-frontmatter`、`check-scope-resolved`、`check-retrospective`、`check-judge-verdict`、`agate-extract-context`、2h 跳过条件均以 `task_level`/`non_legacy` 为门）：✅。
- **重要**：BLOCKER-1 **只影响非 legacy**（legacy 走 `criteria` 之外旧路径，未受影响）⇒ §8 legacy 承诺仍成立，但本批目标能力（非 legacy）不可用。
- R6 双向差分：采信实现者 §7（39 legacy / 0 差异 / exit 0）与复评 §A5；未重跑（需整仓副本 + 时间预算，非本 BLOCKER 判据）。

### 项 6 — SELF-GATE 闭环
- `…-G3-rereview.md` 判 A1–A5 + GAP-1/2/4/5/6/7/8 全闭合；本评审**复核确认 GAP-1/2/4/5/6/7/8 的代码落点属实**。
- **但 A1「文档→脚本对齐」判决不成立**：`UPGRADING.md`/`CHANGELOG.md` 对 P6.5 `criteria` 的承诺
  与实现不符（BLOCKER-1）——前序对齐审查未覆盖该路径。

---

## MINOR 明细

**[MINOR-2] D8 弱化（`check-gate.py:1521-1529`）**
设计 §5.1 D8：截图"必须带 `vision`；**如果没有视觉能力（GAP）**，改为必须带 `manual_review`"。
实现只要求 `vision` 或 `manual_review` **二者之一**，未读 P1 视觉能力三态（`GAP`）来二选一，
且以 `"screenshots/" in refs_str` 子串识别"涉及 UI 的条目"。
Fix：改为读 `read_vision_tri_state`（既有函数）：能力=GAP → 须 `manual_review`；否则须 `vision`（或按设计原文的降级链）。

**[MINOR-3] D7 弱化（`check-gate.py:1540-1564`）**
设计 §5.1 D7「证据 JSON 与结论一致（取代审计 6）」。实现仅：对 `P6-evidence/**/*.json` 取
`bdd_results`/`results` 列表中 `status=="fail"` 的 id，与 `results` 标 PASS 的 id 求交 → 报错。
未覆盖：results 标 FAIL 而 evidence 标 PASS 的反向；JSON 缺该列表/字段形态变化；多个 JSON 的合并语义。
相较被取代的 `agate-evidence-consistency.py` 判据面收窄，属**有意简化但未在文档标注**。
建议：明确 D7 的表征并补测，或在文档注明该判据的范围。

**[MINOR-4] `gate_p7` 取值域未校验（`check-gate.py:1812-1818, 1826-1833`）**
`design_gap_reviews.verdict` 未限定 `accepted|rejected|followup`；`basis` 除 `followup:DEBT<n>` 外
未限定 `in_bdd|out_of_scope`（其余任意串被静默接受）。设计 §6 定义了取值域。
建议：加枚举校验（或显式说明"交由评审判"）。

---

## 附：只读核验命令与结果（真实仓库）
```
$ python3 agate/scripts/check-protocol-consistency.py
... CHECK 16 任务数据契约快照冻结 ✅ PASS；仅有 410 个 WARNING，无 ERROR。（exit 0）
$ python3 -c "…LF 归一 level-1.yaml…"  → 3b2af190c9e17d86a37111613e9c9b0ac2c1cb582997bd9ddd2d5ebadeba7480（== LEVELS.yaml）
$ （仓外副本）pytest test_tag0050_{evidence,declarations,proxy_judgment}.py → 24 passed
```

## 环境隔离
`[PROD_NOT_TOUCHED]` 全程只读：真实仓库仅 `read`/`grep`/`git diff`/`git status`/
`check-protocol-consistency.py`/`sha256` 等只读命令；变异与复现实验仅在仓外一次性副本
`/tmp/opencode/g3rev/`（`cp -r agate agate-workspace`，可丢弃）上进行。未编辑任何被评审文件，
未接触生产环境。
