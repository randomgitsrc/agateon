---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: check-pruning.py 非 legacy 恒检块新增「散文式裁剪声明」判据（正文命中 跳过|裁剪|prune + P<数字> 且 frontmatter 缺 phases → ERROR），收口 RM-AG0087 / DEBT0031
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/scripts/check-pruning.py, agate/tests/unit/test_check_pruning.py]
---

# 协议-脚本对齐审查

> 批次：批 B / H6（分支 `hotfix/batch-b-p1-pruning-consistency`，未提交，改动在工作区）
> 只读审查：未改任何协议/脚本/测试，未 commit / push；所有 scratch 实验在 `/tmp/opencode` 一次性副本上完成。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（新检查落实「frontmatter 权威、散文不被识别」的既有文档口径；附 1 条措辞提示） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`scripts/README.md:78` / `WORKFLOW.md:360` 枚举 check-pruning 非 legacy 检查，未同步新判据） |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW**（state-machine.md「裁剪条件」清单 / P1 卡是否需补，属可选；已确认 gate_p1 / extract-context / phases.yaml **无需**改） |
| A4 | 测试覆盖 | **MISALIGNED**（新用例非判别——变异测试在 HEAD 旧实现上**通过**；无「场景 D」正例覆盖） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（CHANGELOG 已标注；但 DEBT0031 标 `closed` 而其 `closure_criteria` 未实现，fix 落点与 RM 锚不同） |
| A6 | 锚点表覆盖 | **ALIGNED**（新判据未写入协议文档 ⇒ 无需新锚点；check-pruning 既有锚点已覆盖该脚本） |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW**（ADR-014「判据单源」：同一脚本内 `phases` 两种读法分叉） |
| A8 | 声称-命令绑定 | **MISALIGNED**（「原先 rc=0 / 无任何判据」不可复现；「全量 pytest」含 1 条环境性失败；其余可复现） |

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/assets/execution-roles/analyst.md:49`）：
> **机器字段写入文件头 frontmatter 块**（`---` 分隔……；不再写在正文里，**gate 脚本读 frontmatter，散文表述不会被识别**）

**文档声明**（`agate/phase-cards/P1-requirements.md:62`）：
> `risk_level`/`phases`/`packages`/`domains` 写在文件头 **frontmatter**（`---` 分隔块），不写正文。

**脚本实现**（`agate/scripts/check-pruning.py:218-229`）：
> ```python
> if not isinstance(fm_p1, dict) or not fm_p1.get("phases"):
>     _prose_prune = re.search(r"(跳过|裁剪|prune)\s*P[0-9]", _body_p1 or "")
>     if _prose_prune:
>         errors.append("正文声明了阶段裁剪（命中 …）但 frontmatter 缺 `phases` 字段——…")
> ```

**结论**：**ALIGNED**。新检查落实了既有文档口径（frontmatter 权威、散文不被 gate 识别），并**只在** frontmatter 缺 `phases` 时触发（已实测：frontmatter 含 `phases` + 正文「跳过 P3」→ rc=0，不拦）。
**提示（非阻断）**：脚本注释（`check-pruning.py:219`）与错误文案称「裁剪不可机械读（gate 无从据其跳过）」——对**场景 D**（frontmatter 缺 `phases` 但**正文**有 grep 式 `phases: [...]`）并不成立，此时 `_md_field("phases")` 是可读的。措辞宜改为「frontmatter 缺 `phases`（正文散文/回退值不构成 gate 可据以跳过的结构化声明）」。

### A2: 脚本→文档对齐

**脚本行为变更**：`check-pruning.py` 的非 legacy 分支新增一条阻断性 ERROR（`check-pruning.py:218-229`）。

**文档现状**：
- `agate/scripts/README.md:78`：`check-pruning.py (P2.7-P2.9) | …**非 legacy 任务**（TAG0050 批 F，RM-AG0087）：读 frontmatter phases/pruned，**恒检** set(phases) ∪ set(pruned.phase) == 快照 phase_universe …`——**只列恒检，未列新「散文式裁剪声明」判据**。
- `agate/WORKFLOW.md:360`（Pre-commit 检查总览，唯一权威）：`2.7 | check-pruning.py | … **非 legacy 任务**（TAG0050 批 F）：读 frontmatter phases/pruned，**恒检** phases ∪ pruned == phase_universe …`——同上，未列新判据。

**结论**：**MISALIGNED**。审查角色反向传播表（`protocol-alignment-review.md:42`）明确：`check-*.py` 脚本行为变更 → 同步 `scripts/README.md`；`protocol-alignment-review.md:47`：pre-commit 触发行为变更 → 同步 `WORKFLOW.md`「Pre-commit 检查总览」（唯一权威）+ CHECK 9 锚点表。本批新增一条非 legacy 阻断条件，两处描述均应补一句（如「正文命中 `跳过|裁剪|prune` + `P<数字>` 且 frontmatter 缺 `phases` → ERROR」）。
**建议**：在 `README.md:78` 与 `WORKFLOW.md:360` 的 check-pruning 行各补新判据的半句描述。

### A3: 一致性连锁 + 反向传播

**A3a 已知连锁**：`CHANGELOG.md`（[Unreleased] 修复节）、`roadmap.md`（RM-AG0087 → done）、`tech-debt.md`（DEBT0031 → closed）均已随改；`check-debt.py` rc=0。

**A3b 反向传播**（主动推断「应被影响但未在 diff 中」的文件）：

| 候选文件 | 是否应改 | 实测依据 |
|----------|----------|----------|
| `agate/scripts/README.md` | **应改**（见 A2） | `:78` 未列新判据 |
| `agate/WORKFLOW.md` | **应改**（见 A2） | `:360` 未列新判据 |
| `agate/state-machine.md`（「裁剪条件」清单 201-212） | 可选 | 清单标题为「裁剪条件（hook 验证，见 scripts/check-pruning.py）」，逐 phase 列条件；新判据是「声明形式」要求，非 per-phase 条件。补一条 bullet 更完整，但非硬缺口 |
| `agate/phase-cards/P1-requirements.md` | 否（已含口径） | `:57/:62/:77` 已声明 `phases` 必填且写 frontmatter |
| `agate/rules/phases.yaml` | 否 | 阶段定义权威源，不含裁剪声明形式规则；无 `phase_universe`/散文相关键 |
| `agate/scripts/check-gate.py`（gate_p1） | 否 | 实测 `gate_p1`（`check-gate.py:747-900`）**零** `phases/pruned/裁剪` 引用 |
| `agate/scripts/agate-extract-context.py` | 否 | 实测零 `phases/prune` 引用 |
| 其它脚本 | 否 | 实测除 check-pruning 外无脚本扫正文散文裁剪；`check-state-transition.py:285-295` 为 **frontmatter-only**（明确「不得用正则匹配正文」） |

**结论**：**NEEDS_HUMAN_REVIEW**。反向传播清单中 `README.md`/`WORKFLOW.md` 是确定缺口（已在 A2 判 MISALIGNED）；`state-machine.md` 是否补为人工裁量。

### A4: 测试覆盖

**新增用例**（`test_check_pruning.py:413-449`，`test_rm_ag0087_prose_only_pruning_without_phases_blocks`）：构造非 legacy 任务（手写账本 `task_created`）+ frontmatter **无** `phases` + 正文「跳过 P3（低风险可裁）」，断言 `returncode == 1` 且 `"结构化" in output or "phases" in output`。

**变异测试（决定性）**：把 HEAD 版 `check-pruning.py` 装入完整 `agate/` 副本（含 `rules/`，使 `_phase_universe` 可解析），令 `AGATE_ROOT` 指向该副本跑**同一条**新用例：
```
AGATE_ROOT=/tmp/opencode/h6old_agate pytest agate/tests/unit/test_check_pruning.py::test_rm_ag0087_prose_only_pruning_without_phases_blocks
→ 1 passed
```
即**该用例在旧实现（HEAD）上亦通过**——两条断言在旧实现均成立（旧实现对此 fixture 已 rc=1，且输出含「phases ∪ pruned.phase != 阶段全集」子串「phases」）。**该用例不具判别力（假绿灯）**，无法锁住新行为。

**根因**：该 fixture（下文「场景 F」）缺 `phases` 时，旧实现已由（i）检查 2~5（P1/P2/P4/P5/P6 不可裁剪）与（ii）既有恒检 `phases ∪ pruned != universe` 使 rc=1。新判据**唯一的判别场景**是「场景 D」：

| 场景 | 内容 | OLD(HEAD) rc | NEW rc |
|------|------|:---:|:---:|
| **D（唯一判别）** | frontmatter 无 `phases` + **正文 grep 式** `phases: [P1..P8]` + 散文「跳过 P3」 | **0** | **1** |
| E | frontmatter 无 `phases` + 正文 `phases: [P1,P2,P4,P5,P6,P8]` + 散文「跳过 P3」 | 1（恒检） | 1 |
| F（=新用例 fixture） | frontmatter 无 `phases` + 散文「跳过 P3」（无正文 phases） | 1（恒检+检查2~5） | 1 |
| G | frontmatter 无 `phases` + 正文 `phases: [P1,P2,P4,P5,P6,P8]`（无散文） | 1（恒检） | 1 |
| H | frontmatter `phases:[P1..P8]` + 散文「跳过 P3」（fm↔prose 矛盾） | 0 | 0 |

**结论**：**MISALIGNED**。新用例既非判别（D 才是判别场景），又缺「正例」（frontmatter 含 `phases`+`pruned` + 正文散文 → rc=0，实测成立）覆盖。A4 明令「无实跑输出的 ✓ 视为无效（T026/G2.5 事故教训：A4 看不跑导致假绿灯进 main）」——本批正是该模式。
**建议**：新增/改用**场景 D** 作为回归 fixture（旧实现红、新实现绿），并把断言收紧为只认新文案（如 `"正文声明了阶段裁剪" in output`），去掉过宽的 `or "phases" in output`。

### A5: 下游影响 + 文档传播

- **CHANGELOG**：已在 `[Unreleased] 修复` 节新增条目（`CHANGELOG.md`），格式与同节其它条目一致（无 task_id，用 RM/DEBT 码）；CHECK 7（badge↔CHANGELOG）通过。**OK**。
- **gate 行为影响**：仅非 legacy 任务受影响；**实测真实工作区 43 个任务全部为 legacy**（账本无 `task_created`/`task_adopted`，仅 `gate_run`/`state_transition`）⇒ 新判据对存量任务**零影响**，无破坏性变更。**OK**。
- **⚠️ 关单口径**：`tech-debt.md:1251-1253` 的 `closure_criteria` 写「**check-gate P1** 对 frontmatter phases 与**正文裁剪声明**做机械一致性校验」；`roadmap.md` RM-AG0087 锚写「**check-gate P1** 加机械一致性校验」。实际实现落在 **check-pruning.py**（非 check-gate），且**未**做 frontmatter↔正文 的一致性核对——**场景 H（frontmatter `phases` 含 P3 + 正文「跳过 P3」）实测 OLD/NEW 均 rc=0**，即标题所述「frontmatter phases 与正文裁剪声明一致性」的核心场景仍未拦。
- 但 `analyst.md:49` 的口径是「散文不被识别 ⇒ frontmatter 权威」，故「fm↔prose 一致性」在设计中本非必查项——DEBT0031 的 `closure_criteria` 措辞与设计口径存在张力。

**结论**：**NEEDS_HUMAN_REVIEW**。DEBT0031 被标 `closed`、RM-AG0087 被标 `done`（均注明「PARTIAL 闭合」），但 `closure_criteria`/锚的**字面**未满足。需人工裁决：是把该 partial 收口**接受**为关单（则应修订 `closure_criteria` 以反映实际交付面），还是保留 `open`/`backlog` 直至场景 H 被覆盖。

### A6: 锚点表覆盖

CHECK 9 锚点表（`check-protocol-consistency.py:577-607`）中 `check-pruning.py` 已有 6 条锚点（`P2 不可裁剪` / `risk_level` / `P6 不可裁剪` / `coupling_checklist` / `源码文件数` / `internal_only`）。新判据**未**写入任何协议文档（见 A1/A2），故无需新锚点；`CHECK9-coverage`（`:907-945`）只要求 gate 脚本至少有一条锚点，check-pruning 满足。

**结论**：**ALIGNED**。（若采纳 A2 把新判据写入 `state-machine.md`，则 CHECK 9 锚点表宜相应加一条关键词锚点——二者联动。）

### A7: 设计原则一致性

**相关 ADR**：`agate/adr.md:533` **ADR-014「判据单一权威源——判据必须单源」**。

**发现（判据分叉）**：`check-pruning.py` 内 `phases` 有**两种读法**：
- `:204` `phases_declared = _md_field("phases", p1_file)`（frontmatter 优先，**正文正则回退**）→ `:207` `phases = phases_declared.split()` → `:240` `declared = set(phases)`，供**恒检**（`:251` `declared | pruned_phases != universe`）。
- `:217/:222` `fm_p1, _ = split_frontmatter(p1_text)` → `not fm_p1.get("phases")`（**frontmatter-only**），供**新判据**。

同一脚本对「phases 是否已声明」给出两套语义：**场景 D** 中 `_md_field` 读得正文 `phases`（`declared == universe` ⇒ 恒检**通过**），而新判据因 frontmatter 缺 `phases` **报错**——两条判据在同一输入上互相矛盾。这正是 ADR-014 所要防的「同一输入在链路不同环节得到不同判定」。

**结论**：**NEEDS_HUMAN_REVIEW**（设计原则为指导性，按 A7 规则不判 MISALIGNED）。
**建议**：二选一统一语义——(a) 新判据改用 `phases_declared`（与恒检同源，仅当「机器可读的 phases 为空」才报），或 (b) 让恒检 `declared` 也改 frontmatter-only（与 `check-state-transition.py:285-295` 的 frontmatter-only 口径对齐，但需评估对存量非 legacy 任务的影响）。并在注释中点明「本脚本 phases 读取口径」以避免后续再分叉。

### A8: 声称-命令绑定

| 声称（来源） | 复现命令 | 结论 |
|--------------|----------|------|
| `91 passed`（批次声称） | `python3 -m pytest agate/tests/unit/test_check_pruning.py agate/tests/unit/test_check_state_transition.py -n auto -q` | ✅ **91 passed**（32 + 59） |
| `2902 passed`（批次声称） | `python3 -m pytest agate/tests -n auto -q` | ⚠️ **2902 passed, 1 failed, 2 skipped**——唯一失败 `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（`opencode debug agent` → 子命令改名为 `agents`），**环境相关、与本改动无关**；声称「全量 pytest（全绿）」字面不成立 |
| `0 ERROR`（批次声称） | `python3 agate/scripts/check-protocol-consistency.py`（rc=0；仅 421 冻结 WARNING） | ✅ **0 ERROR** |
| `check-debt rc=0`（批次声称） | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ **rc=0** |
| 「原先该场景**无任何判据**，实测 **rc=0**」（`CHANGELOG.md` [Unreleased]；`tech-debt.md:1244`；`roadmap.md` RM-AG0087 行） | 见 A4 场景表：字面场景（新用例 fixture = 场景 F）旧实现 **rc=1**（检查 2~5 + 恒检已拦）；仅**场景 D**（正文有 grep 式 `phases`）旧实现 rc=0 | ❌ **不可复现**——「无任何判据」与「rc=0」对**字面描述的场景**均不成立 |

**结论**：**MISALIGNED**。前三项可复现；末项（「原先无任何判据 / rc=0」）应修正为准确表述，例如：「原先对**frontmatter 缺 `phases` 但正文以 grep 式 `phases` 声明**（场景 D）无判据，实测 rc=0」——否则该声称把「无判据」放大到全部「散文裁剪」场景，与实际不符。按 A8 规则「无法给出命令的声称，应删除该声称」，建议改写而非保留。

## 五项重点结论

1. **判据恰当性**（误报/漏报/生效面）：
   - **只在缺 `phases` 时生效**：✅ 已验证（frontmatter 含 `phases` + 正文散文 → rc=0，不拦）。
   - **误报面**：`(跳过|裁剪|prune)\s*P[0-9]` 对**否定句**与**规则说明**误伤——实测缺 `phases` 时，正文「本任务**不跳过 P3**，全阶段执行」与「**裁剪 P7** 需源码数 ≤5（规则说明）」均触发 ERROR。二者语义上非「声明裁剪」，属误报（虽仅在缺 `phases` 这一狭窄面生效）。
   - **漏报面**：同义措辞**不命中**——「省去 P4」「不执行 P5」「省略 P3」「略过 P7」「跳过第三阶段」实测均**不触发**（`跳过第三阶段` 因无 `P<数字>` 不匹配；前四者措辞不在 `跳过|裁剪|prune` 内）。即判据只覆盖 3 个词形，漏报面可观。
2. **与既有判据冲突/重复**：既有恒检 `phases ∪ pruned == phase_universe`（`:251`）**已覆盖**场景 E/F/G；新判据**边际贡献仅场景 D**。在 E/F 中两者**同时报错**（同因双报，噪声，非矛盾）。与 `_reconcile_p1_fields`（WARNING，`:135-155`）**可并存**：实测「正文 grep 式 `phases` + frontmatter 缺 phases + 散文」→ **RECONCILE WARNING + 新 ERROR 同时出现**（一条 WARNING、一条 ERROR，退出码由 ERROR 决定）。本批**未改** WARNING 的退出码语义（与声称一致）。
3. **对既有任务的影响**：✅ 实测真实工作区 **43 个任务全部 legacy**（账本仅 `gate_run`/`state_transition`，无 `task_created`/`task_adopted`）⇒ 新块不执行，零影响。**⚠️ 任务描述中「契约级任务（仅 TAG0051）」失实：`agate-workspace/tasks/` 下**不存在 TAG0051**（43 个 TAG 任务，最高 TAG0050）**；且无任何非 legacy 任务。
4. **测试判别力**：❌ **新用例不具判别力**——变异测试（`AGATE_ROOT` 指向 HEAD 版 `check-pruning.py` 的完整副本）跑该用例 **1 passed**，即旧实现同样通过；且**无「有 `phases` + 正文提及裁剪 → 不拦」的正例**覆盖（该正例实测存在但未被用例锁定）。唯一判别场景 D 未被覆盖。
5. **A8**：见上表——`91 passed` / `2902 passed` / `0 ERROR` / `check-debt rc=0` 可复现（`2902 passed` 伴 1 条环境性失败）；**「原先无任何判据 / 实测 rc=0」不可复现**，需按场景 D 改写。

## 附：只读与复现纪律

- 全程只读；仅写入本报告与 `docs/reviews/agate-alignment-2026-10-09-H6-PRUNING-01.progress.md`。
- 所有 scratch（HEAD 脚本副本、场景构造）在 `/tmp/opencode/` 下完成；跑测试前后 `git status --porcelain` 一致（5 个已改文件 + 1 个新增 progress 文件，无新增污染）。
- 变异测试使用**完整 `agate/` 副本**（含 `rules/`）以消除 `_phase_universe` 因路径解析失败的混淆变量。
