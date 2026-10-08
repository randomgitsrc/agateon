---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 批 G3（D+E+F 合批）——P6 results 判据/P6.5 criteria、P7 成对声明跨文件聚合、P1/P2/P8 结构化判定、pruned 闭合；8 条 [DESIGN_GAP] 逐条裁定
files_changed:
  - agate/scripts/check-gate.py
  - agate/scripts/check-pruning.py
  - agate/scripts/check-scope-resolved.py
  - agate/scripts/check-retrospective.py
  - agate/scripts/check-judge-verdict.py
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/agate_common.py
  - agate/scripts/agate-extract-context.py
  - agate/scripts/agate-md-field-set.py
  - agate/scripts/agate-run.py
  - agate/scripts/agate-debt-check.py
  - agate/rules/task-data/level-1.yaml
  - agate/rules/task-data/LEVELS.yaml
  - agate/rules/markers.yaml
  - agate/rules/schema/markers.schema.json
  - agate/assets/templates/gitignore-fragment.txt
  - agate/assets/templates/tech-debt-template.md
  - agate/scripts/README.md
  - agate/UPGRADING.md
  - CHANGELOG.md
---

# 协议-脚本对齐审查 — TAG0050 批 G3（D + E + F）

> **范围**：批 G3 的 21 个 tracked 改动 + 3 个新增任务文件（`P4-implementation-G3.md` 等），HEAD `b746d07d`（未提交）。
> **方法**：只读 diff 核验 + 设计/P1/P2 原文对照 + **仓外副本**（`/tmp/opencode/g3scratch`、`/tmp/opencode/g3base`，仅 `agate/`+`agate-workspace/` 复制）上的"按设计接线"变异实验。未对被评审文件做任何写操作。
> **触发面**：`agate/scripts/*.py` / `agate/rules/*.yaml` / `agate/**/*.md` / `README.md` / `UPGRADING.md` / `CHANGELOG.md`（SELF-GATE 全触发）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（GAP-1/2/5/6/7/8：脚本+文档同时偏离设计，见逐项） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`agate-extract-context` 单参形式、`declaration_globs` 机制未文档化） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（新结构化字段未传播到 `task-files.md`/phase-cards/role-cards；`declaration_globs` 为设计外新键） |
| A4 | 测试覆盖 | **MISALIGNED**（BDD-56..60 目标测试判别力弱：BDD-57/58 走旧脚本、BDD-59 仅断言函数存在、BDD-60 仅断言 rc==0；D5/D7/D9/GAP-7/GAP-8 无测试） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（CHANGELOG/UPGRADING 对 D1–D10 的承诺超出实现；legacy 兼容未见 R6 复跑；模板/卡片未同步） |
| A6 | 锚点表覆盖 | **ALIGNED**（未新增 `check-*.py`；既有脚本已在锚点表；consistency 实测 **0 ERROR**） |
| A7 | 设计原则一致性 | **ALIGNED**（符合 ADR-007 机器字段并入 frontmatter；建议为"跨文件声明聚合"补一条 ADR） |
| A8 | 声称-命令绑定 | 见 §A8（E2 结论与 P2 §11 字面判据方向不一致 → **NEEDS_HUMAN_REVIEW**） |

**总体**：**不可直接 commit**。7 条 `[DESIGN_GAP]` 判「**必须闭合**」，1 条判「可接受（附条件）」；另有多项 A1–A5 文档/测试缺口。逐条见下。

---

## DESIGN_GAP 逐条裁定（`P4-implementation-G3.md` §4）

> **裁定口径**（与前两批同）：「为保持既有测试全绿而未**实现**设计要求」**不是**可接受理由。正解 = **按设计接线 + 随新契约更新既有夹具**。下表的"闭合后转红测试"均在**仓外副本**上实测（变异法：仅施加该 GAP 的"按设计接线"补丁，其余不动）。

| GAP | 描述 | 裁定 | 依据（设计原文） | 闭合后转红的既有测试 + 夹具更新 |
|---|---|---|---|---|
| **GAP-1** | 非 legacy P6 未声明 `results` 时回退既有判定 | **必须闭合**（MISALIGNED） | 设计 §5.1「非 legacy 任务的判据 D1–D10」；`_gate_p6_structured` 自身对缺 `results` 报 ERROR（`check-gate.py:1341-1345`） | **1 条**：`test_pre_commit_hook.py::test_hook_evidence_warning_low_variance_not_blocked`（实测转红）。夹具：T086 的 `P6-acceptance.md` 改为结构化 `results`（bdd 集合 = P1，全 PASS，证据引用存在的文件）或改 `legacy=True`。**另**：`requires.results: false`（level-1.yaml:20）应随批 D 翻真（见 A1） |
| **GAP-2** | `reviewed_bdds` 仅在已声明时校验 | **必须闭合**（MISALIGNED） | 设计 §7「`reviewed_bdds` 必须**等于** P1 的 BDD 集合」 | **1 条**：`test_tag0050_proxy_judgment.py::test_bdd_71`（实测转红，因 gate_p1 先于 T2 报 reviewed_bdds）。夹具：`conftest.init_task()` 的 `P1-review.md` 加 `reviewed_bdds: ['1']`（`init_task_via_conftest` 经它）；新任务 P1-review 须声明 |
| **GAP-3** | `agate-extract-context.py` 新增单参形式（越过"只改 :190-211"） | **可接受（附条件）** | 设计 §5.1「:190-211 改为经 md-field-get 取值」（约束意图 = 抽取算法不动） | 抽取算法确未动，:190-211 的字段读取改动落在边界内；单参形式是**新增非破坏性 CLI**、为满足 BDD-60 的 P3 调用口径。**条件**：该新接口未文档化（`agate/scripts/README.md`/`UPGRADING.md` 均无）→ 补文档，或把 P3 测试改用两参形式 |
| **GAP-4** | `phases ∪ pruned` 闭合只在声明 `pruned` 时检查 | **必须闭合**（MISALIGNED） | 设计 §7 / RM-AG0087「`set(phases) ∪ set(pruned.phase)` 等于快照 `phase_universe`，且两者不相交」（无"仅在声明时"限定） | **5 条**（实测转红）：`test_pre_commit_hook.py::{test_bdd_3_space_dir_gate_runs, test_bdd_4_no_space_single_task_regression, test_it6_task_level_state_p1_output_commits, test_it9_pruning_skip_low_passes, test_it10_routing_2j1_thin_missing_element_blocks}`。夹具：这些 P1 用**结构化 `pruned` frontmatter** 声明被跳过阶段（如 P3/P6.5）。⚠️ 见下方「GAP-4 语义澄清」 |
| **GAP-5** | F 批结构化字段（`ui_design`/`delivery`/`pruned`）判据硬编码在 gate，未进快照 | **必须闭合**（MISALIGNED） | 设计 §7「必填维度由 `shape` 决定（**在快照中定义**）」；§3.6「按任务等级对应的**快照**校验」；dispatch §2 批次 F 第 7 项要求快照 `ui_design`/`delivery`/`pruned`/`phase_universe` | 无既有测试转红（新能力）；但 `ui_design` 的"必填维度由 shape 决定"**完全未实现**（现仅查 `na` 须带 `reason`）。须：注册 3 键 + gate 读快照 + 补"必填维度存在"判据 + 新增测试 |
| **GAP-6** | D5 / D7 / D9 未实现；D3 的"pre-commit 中要求已跟踪或已暂存"未实现 | **必须闭合**（MISALIGNED） | 设计 §5.1 判据 D3/D5/D7/D9（D3 明确"在 pre-commit 中还要求它已跟踪或已暂存"） | 无既有测试转红（新判据）；须补实现 + 新测试（D5 为 WARNING、D7/D9 为 ERROR） |
| **GAP-7** | `agate-evidence-consistency.py` 的非 legacy 跳过未实现（provenance 正文解析同） | **必须闭合**（MISALIGNED） | 设计 §5.1「非 legacy 任务**不再运行** … `agate-evidence-consistency.py`、provenance 中的正文解析」 | 须改 `check-p6-provenance.py`（审计 6 + 正文解析按 `task_level` 跳过）；跑 `test_check_p6_provenance.py`/`test_p6_evidence*` 确认非 legacy 夹具。**必须与 GAP-6 的 D7 成对**（D7 取代审计 6） |
| **GAP-8** | 快照 `declaration_files` 未扩到 `*-review.md` / `P4-implementation-*.md` | **必须闭合**（MISALIGNED） | 设计 §6「快照的 `declaration_files` 覆盖各阶段主产出、`*-review.md`、`P4-implementation-*.md` 和 `P4-implementation/**/*.md`」 | 实现者改为新增设计外的 `declaration_globs` 键（level-1.yaml:201），`declaration_files` 仍 6 项（level-1.yaml:75-81）。闭合：按设计扩展 `declaration_files`（影响 `check-frontmatter.py` 的缺 frontmatter 判据 + `pre-commit-gate` 的 prod_touched 面）→ 相关非 legacy 夹具补 frontmatter |

### GAP-4 语义澄清（NEEDS_HUMAN_REVIEW）

快照 `phase_universe` = `[P0, P1, P2, P3, P4, P5, P6, P6.5, P7, P8]`（level-1.yaml:35）。若"恒检"字面执行，则**任何**非 legacy 任务即便 `phases: [P1..P8]`（常规全流程）也因缺 `P0`/`P6.5` 而 ERROR，须额外声明 `pruned`。这与既有 `phases` 语义（任务计划阶段）冲突。**请人工裁定**：是 (a) `phase_universe` 应排除 P0/P6.5，还是 (b) 常规任务的 `phases` 本应含 P0/P6.5，还是 (c) `pruned` 只覆盖"可裁剪阶段"。裁定前实现不应"静默跳过"（GAP-4 仍判必须闭合——至少不能在**声明了 pruned 时**才检查）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

文档（`UPGRADING.md` 未发布节 / `CHANGELOG.md` Unreleased）承诺与实现比对：

- **`UPGRADING.md`「未发布 — TAG0050 批 D/E/F」** 写「P1 `reviewed_bdds`（**已声明时**须等于 P1 BDD 集合）」——文档与**实现**一致，但**双双偏离设计 §7**（"必须等于"）→ 对应 GAP-2。文档已把"未实现"固化为承诺。
- 同节写 P6「`results` … 判据 D1–D10」、P7 聚合、P8 `delivery` 结构化——`delivery`/P7 聚合属实；但 **D1–D10 只有 D1/D2/D3(部分)/D4/D6/D8/D10 落地**（D5/D7/D9 缺，见 GAP-6）→ 文档**过度承诺**。
- **快照单源**：`level-1.yaml` 的 `requires.results: false`（:20，注释「批 D：P6 results 结构化（本任务不启用）」）**未随批 D 翻真**；而 `gate_p6` 对**所有**非 legacy 任务强制结构化（`check-gate.py:1455`）。设计 §2.5「要求项由契约决定」⇒ 声明（false）与执行（强制）分叉。**建议**：翻 `requires.results: true`，或让 `gate_p6` 经 `requirement_active(..., "results", "P6")` 判定（与 §2.5 单源一致）。
- `markers.yaml` 补登记 5 标记（:150-191）+ `markers.schema.json` name pattern 放开 `-`（:50）——与设计 §6「补登记 BLOCKER/DEVIATION-CRITICAL/CODE_MAP_UPDATED/CODE_MAP_EXEMPT/SUGGEST」一致，**ALIGNED**。
- `tech-debt-template.md` 增 `source_ref` + `agate-debt-check.py` 校验（`SOURCE_REF_RE = ^[A-Z]+[0-9]+:.+$`）——与设计 §6「`source_ref` 回指 `<task_id>:<DG id>`」一致，**ALIGNED**（`SOURCE_REF_RE` 只校验前缀任务 ID，`<DG id>` 部分宽松，可接受）。
- `agate/scripts/README.md` `agate-run` 行补 `--task`/`run:<k>`——与实现一致，**ALIGNED**。

### A2: 脚本→文档对齐 — MISALIGNED

- `agate-extract-context.py` 新增单参形式（`main()`，`check` 见 GAP-3）**未在任何文档登记**（README/UPGRADING 均无）→ 脚本能力 > 文档。
- 新增快照键 `declaration_globs`（level-1.yaml:201）与 gate 消费（`check-gate.py:1540`、`check-scope-resolved.py:108`、`check-retrospective.py:140`）**未在文档说明**；且该键不在设计 §6 的数据契约中（设计用 `declaration_files`）→ GAP-8。
- `check-pruning.py` / `check-scope-resolved.py` / `check-retrospective.py` / `check-judge-verdict.py` 的**行为变化**（非 legacy 分支）未在 `agate/scripts/README.md` 工具表描述中体现（README 仅改了 `agate-run` 行）。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**连锁（已改）**：`level-1.yaml` 追加键后**已重登记** `LEVELS.yaml` sha256——实测 `sha256(LF 归一 level-1.yaml) = 663abfea…` == 登记值 ✓（CHECK16 冻结未破坏，B 批快照单源未被本批打破）。TAG0050 自身为 **legacy**（账本首行 `gate_run`，无 `task_created`）→ 新契约分支不作用于本任务，自应用面无风险。

**反向传播（应被影响但 diff 未列出）**：

| 应被影响的文件 | 理由 | 状态 |
|---|---|---|
| `agate/assets/templates/task-files.md` | 新增结构化字段（`results`/`criteria`/`design_gaps`/`code_map`/`findings`/`scope_plus`/`reviewed_bdds`/`ui_design`/`delivery`/`pruned`）未出现在 P1/P2/P6/P7/P8 可复制 frontmatter 样例块（`grep` 0 命中） | **缺失** |
| `agate/phase-cards/{P1,P2,P6,P6.5,P7,P8}-*.md` | 产出规格节的 frontmatter 样例块应含新字段（P6 `results`、P6.5 `criteria`、P8 `delivery`、P2 `ui_design`、P1 `reviewed_bdds`/`pruned`） | **缺失**（0 命中） |
| `agate/assets/execution-roles/{verifier,consistency-reviewer,architect,analyst}.md`、`assets/review-roles/*` | 角色卡应指导写结构化字段（verifier 写 `results`/`criteria`；consistency-reviewer 写 `design_gap_reviews`/`findings`） | **缺失**（0 命中） |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | `pre-commit-gate.py` 的 2h 段对非 legacy 跳过 `check-p6-format`（行为变更） | **未同步**（`grep check-p6-format` 0 命中） |

> 说明：P2 §1.2 记「协议文档正文的改写属各批 P4 工作（DEBT0039）」，故上述传播可辩护为"分批进行"。但本批的 G3 交付面**恰好是**这些结构化字段，读者（verifier/consistency-reviewer）不更新卡片就无法写对字段。**建议**：本批补齐或显式登记 DEBT（引用 DEBT0039）并写明"哪一批补"。

### A4: 测试覆盖 — MISALIGNED

- **必须附实跑输出**：本审查在**仓外副本**复算——`test_tag0050_{evidence,declarations,proxy_judgment,cross_batch,fitness}` → **22 passed / 3 failed**（3 failed = `test_bdd_74/75/76`，因副本缺根文档/`r6-differential.sh` 的环境噪声，非本批缺陷）；`count-tests.sh` = **2843**（与 implementer 一致）。目标 5 文件在本仓应为 25 passed（采信 implementer，副本排除环境噪声后一致）。
- **判别力弱（关键）**：
  - `test_bdd_56` 仅覆盖 D1 重复一项，未覆盖 F1 的 A（改 FAIL）/B（删条目）两种篡改；
  - `test_bdd_57`/`test_bdd_58` 调用的是 **`check-p6-evidence.py`（旧路径）**，**未走** `gate_p6` 的新 D3/D6；`test_bdd_58` 的失败很可能来自"`bdd-01.log` 未被引用"（D4）而非"`EXIT_CODE≠0`"（D6）；
  - `test_bdd_59` **仅断言 `resolve_evidence_ref` 存在**，未构造 sha256 不一致；
  - `test_bdd_60` **仅断言 rc==0**，未断言"计数 == 现算值"；
  - `test_bdd_62`/`64`/`65` 仅 `rc != 0`，弱判别（可能因无关失败满足）；
  - **D5/D7/D9（GAP-6）、`agate-evidence-consistency` 跳过（GAP-7）、`declaration_files` 扩展（GAP-8）、`ui_design` 必填维度（GAP-5）均无测试**。
- 结论：现有目标测试**不足以守护**本批新逻辑；闭合 GAP-5/6/7/8 时必须补强测试（否则"绿"不代表新判据生效）。

### A5: 下游影响 + 文档传播 — MISALIGNED

- **CHANGELOG**（Unreleased 节）标注了 D/E/F 与义务基线重设，方向正确；但见 A1 的"D1–D10 过度承诺"。
- **legacy 兼容（§8 硬承诺）**：新分支多数以 `task_level(...) is not None` 为门（`gate_p6:1455`、`gate_p7:1746`、`gate_p8:1947`、`gate_p1:716/747`、`check-pruning:182`、`check-scope-resolved`、`check-retrospective`、`check-judge-verdict`、`agate-extract-context`）→ 良好。**但 `gate_p2` 的 UI `na` 检查未加门**（`check-gate.py:591-610`），对 legacy 也生效——设计 §3.6 明示 gate 侧为"非 legacy 任务"，且 §8 承诺 legacy ERROR 集合不变。**语料实测**：`agate-workspace/tasks/**` 中 `ui_design:` **0 命中** ⇒ 当前不可观测，但属**潜在 §8 违规**（新增 ERROR 未列入 §8 十二项）。**建议**：加 `task_level` 门；并在 R6 差分中确认 legacy 新增 ERROR = 0。
- **R6 双向差分未见本批复跑证据**（implementer §6 未列 `r6-differential.sh` 结果）——G3 改了 3 个 gate 的 legacy 面外分支，宜按设计 §8/§3.2 复跑并核对差异全在 allowlist。
- **模板/卡片/角色传播缺失**（见 A3）。

### A6: 锚点表覆盖 — ALIGNED

- 本批**不新增** `check-*.py`（`P4-implementation-G3.md` §5「登记面」属实）→ CHECK 9 覆盖面无需扩展；`check-gate.py`/`check-pruning.py` 等既有脚本已在锚点表。
- 本审查**只读复跑** `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（WARNING 412；较 implementer 的 410 多 2，源于新增未跟踪叙事文件与本留痕文件，非本批缺陷）。
- `grep` 未发现 `骨架声明`/`pruned`/`RM-AG0085`/`RM-AG0087` 的 CHECK 9 锚点条目——但这两条规则出自 `docs/` 设计与 P1（非 `agate/*.md` 协议文档），不属 CHECK 9 扫描面，**无需新增锚点**。

### A7: 设计原则一致性 — ALIGNED

- 结构化字段并入 frontmatter（`results`/`criteria`/声明字段）符合 **ADR-007**（机器字段并入 frontmatter、单工具双读）；未引入独立事实文件。
- 未发现与 ADR-001/002/005 冲突（判定仍机器可判定；改动走分支）。
- **建议**：本批引入"跨声明文件聚合 + `declaration_globs`"这一新机制（设计外新键，见 GAP-8），属未记录的架构决策 → 建议补一条 ADR（或在 GAP-8 闭合时回到设计的 `declaration_files` 单源，从而无需新 ADR）。

### A8: 声称-命令绑定

| 声称（来源） | 产出它的命令 | 结论 |
|---|---|---|
| 目标 5 文件 **25 passed** | `pytest test_tag0050_{evidence,declarations,proxy_judgment,cross_batch,fitness} -q` | 副本复算 22 passed/3 failed（3 failed=缺根文档环境噪声）→ 与本仓 25 passed 一致（采信） |
| 全量 **2840 passed / 2 skipped / 1 failed** | `pytest agate/tests/ -q --tb=no -n auto` | 未逐字复算（副本缺 `site/`/根文档）；副本 unit+integration 复算**无新增非环境失败**；唯一 failed（`test_setup_agate_dir.py::test_bdd_43`，本机 `opencode debug agents` 漂移）与 P3 登记一致（采信） |
| consistency **0 ERROR / 410 WARNING** | `python3 agate/scripts/check-protocol-consistency.py` | 只读复跑 **0 ERROR / 412 WARNING**（+2 为新增未跟踪文件）→ **0 ERROR 确认** |
| count-tests **2843** | `bash agate/tests/scripts/count-tests.sh` | **实测 2843** ✓ |
| platform **rc=0** | `check-platform-assumptions.py` | 未复跑（采信） |
| ruff **clean** | `~/.venvs/agate-dev/bin/ruff check` | 未复跑（采信） |
| `LEVELS.yaml` sha256 重登记 | `sha256sum`（LF 归一） | **实测 663abfea… == 登记值** ✓ |
| **E2**：命令写入 gate 失败 0 次 vs 散文 ≥1 次 | `/tmp/opencode/e2` 实测（implementer） | **NEEDS_HUMAN_REVIEW**：P2 §11 字面判据「**第二种** gate 失败次数**不多于第一种**」——若"第一种=命令写入"，则散文(1) > 命令(0) **不满足**；implementer 明示重释为"结构化写入不增加 gate 失败"（方向相反）。判据方向存在歧义，请人工确认。**未删除该声称**（附重释与原始数据），待人工裁决 |

---

## 闭合后"既有测试转红 + 夹具更新"清单（一轮修完）

> 均在仓外副本上以"仅施加单条 GAP 的按设计接线补丁"实测得到（隔离法见留痕文件）。

| GAP | 转红的既有测试 | 夹具/实现更新 |
|---|---|---|
| GAP-1 | `test_pre_commit_hook.py::test_hook_evidence_warning_low_variance_not_blocked` | T086 `P6-acceptance.md` 写结构化 `results`（bdd 集合 = P1 的 `#### BDD-N:`；全 PASS；`evidence` 指向存在的文件）；或该夹具改 `legacy=True`。另建议 `level-1.yaml` `requires.results` 翻真 |
| GAP-2 | `test_tag0050_proxy_judgment.py::test_bdd_71` | `conftest.init_task()` 的 `P1-review.md` 加 `reviewed_bdds: ['1']`（其 P1 仅 BDD-1）；其余走 `gate_p1` 的非 legacy 夹具（如有）同补 |
| GAP-4 | `test_pre_commit_hook.py::{test_bdd_3_space_dir_gate_runs, test_bdd_4_no_space_single_task_regression, test_it6_task_level_state_p1_output_commits, test_it9_pruning_skip_low_passes, test_it10_routing_2j1_thin_missing_element_blocks}` | 这些 P1 用结构化 `pruned` frontmatter 声明被跳过阶段（含 `phase_universe` 与 `phases` 的差集）。**先裁定 `phase_universe` 语义**（P0/P6.5 是否计入） |
| GAP-5 | 无（新能力） | 快照注册 `ui_design`（shape→必填维度）/`delivery`/`pruned`；gate 改读快照 + 补"必填维度存在"判据；新增测试 |
| GAP-6 | 无（新判据） | 实现 D5（WARNING）/D7/D9 + D3 的 pre-commit "已跟踪/已暂存"；新增测试 |
| GAP-7 | 待定（需跑 `test_check_p6_provenance.py` / `test_p6_evidence*`） | `check-p6-provenance.py` 审计 6 + 正文解析按 `task_level` 跳过；**与 GAP-6 的 D7 成对** |
| GAP-8 | 待定（`check-frontmatter.py` 相关测试；扩展后非 legacy 的 `P2-review`/`P4-implementation*` 需 frontmatter） | 按设计扩展 `declaration_files`（或把 `declaration_globs` 并回 `declaration_files` 单源），删除设计外新键；同步 `check-frontmatter`/`pre-commit-gate` 面 |

---

## 闭环规则

- **MISALIGNED 项**（A1–A5 + GAP-1/2/4/5/6/7/8）：**必须修复**——按设计接线 + 更新夹具（见上表），修完重审。
- **NEEDS_HUMAN_REVIEW 项**（A8 的 E2 结论、GAP-4 的 `phase_universe` 语义、`gate_p2` UI 未加门）：须附 `[HUMAN_CONFIRMED: 日期 确认：理由]` 后方可 commit；未确认等同 MISALIGNED。
- **ALIGNED 项**（A6/A7）：通过。

## 环境隔离

[PROD_NOT_TOUCHED] 全程只读：仅 `git diff`/`grep`/`sed` 读文件、`sha256sum` 与只读 `check-protocol-consistency.py`/`count-tests.sh`；变异实验仅在仓外一次性副本 `/tmp/opencode/{g3scratch,g3base}` 上做（已 `cp -r`，可丢弃）。未对被评审文件做任何写操作，未接触生产环境。
