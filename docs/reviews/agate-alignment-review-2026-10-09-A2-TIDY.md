---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A2 收尾的登记/治理小修——① RM-AG0087 → done（锚点更正为 check-pruning，与 DEBT0031 同步关单）；② RM-AG0103 → scheduled（已拆任务 TAG0051-release-decoupling）；③ protocol-alignment-review.md 新增「只读纪律：写类工具一律在副本上跑」节
files_changed: [CHANGELOG.md, agate-workspace/roadmap/roadmap.md, agate/assets/review-roles/protocol-alignment-review.md]
branch: hotfix/batch-a2-tidy（未提交，改动在工作区）
---

# 协议-脚本对齐审查（批 A2 收尾 / A2-TIDY）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | ALIGNED（本批无脚本改动；相关脚本→文档方向并入 A1） |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW** |
| A4 | 测试覆盖 | **NEEDS_HUMAN_REVIEW** |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空清单，见下） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED**（1 条行号不准 + 1 条误导性结论） |

**是否可 commit**：**否（先修）**。RM-AG0087 的关单**结论**成立（机械校验确已存在），但**关单理由写错了机制**（A1/A8），且该条锚的「新测试覆盖」**未被真正满足**（A4，BDD-70 假绿灯）。最小修复：改 `roadmap.md` RM-AG0087 注 + `CHANGELOG.md` 条目，把锚点证据改为 **TAG0050 批 F 的 `phases ∪ pruned == phase_universe` 硬检**（check-pruning.py:248，ERROR/exit 1），并删去「级别 warning-only 系设计选择」这一误导表述；建议一并决定是否补/修一个**真正的**失败测试（A4）。A3/A5 的两处传播为建议项，可与主 Agent 商议是否同批落地。

---

## 逐项审查

### A1: 文档→脚本对齐 —— MISALIGNED

**文档声明**（`agate-workspace/roadmap/roadmap.md:87`，RM-AG0087 注，本批新增）：
> 机械一致性校验**已存在**——`check-pruning.py:240` 的 `_reconcile_p1_fields` 对 P1 `risk_level`/`phases` 做 frontmatter ↔ 正文双读对账，不一致即 `RECONCILE WARNING`，开关 `reconcile_enabled()` **缺省 on** ⇒ 默认在 gate 路径生效。⚠️ **锚点更正**：本条原锚 `check-gate`，实际落地在 **check-pruning**（同一 P1 gate 路径）；**级别 warning-only 系设计选择（协议刻意不改退出码，避免 legacy 归一化差异被硬阻断）**。

**脚本实现**（`agate/scripts/check-pruning.py`）：
> `:248` 注释：`# TAG0050 批 F（RM-AG0087，设计 §7）：非 legacy 任务**恒检**——`
> `:249-266`：`set(phases) ∪ set(pruned.phase)` 须等于快照 `phase_universe` 且不相交，否则 `errors.append(...)` → **`sys.exit(1)`（ERROR，阻断）**。

**实测复核**（`/tmp/opencode` 副本，非真实仓库）：
- 非 legacy 任务（账本首行 `task_created`）`phases: [P1, P3, P4, P5, P6, P7, P8]`（漏 P2、无 `pruned`）→ `check-pruning.py` **rc=1**，stderr：`phases ∪ pruned.phase != 阶段全集：缺=['P2']`。
- 同一夹具的 `_reconcile_p1_fields` 输出：`RECONCILE SUMMARY: 0 mismatches across 0 fields`（frontmatter 与正文**都**漏 P2 ⇒ 对账**不告警**）。

**差异**：
1. **机制归属错误**。代码注释、`agate/scripts/README.md:78`（`check-pruning.py` 行）与 `agate/tests/unit/test_tag0050_proxy_judgment.py:83`（BDD-70）**一致地把 RM-AG0087 归属到「`phases ∪ pruned == phase_universe` 硬检（ERROR）」**，而非 `_reconcile_p1_fields`。本批注（及 `CHANGELOG.md` 条目）只引用了后者。
2. **「warning-only 系设计选择」是误导性表述**。对账层（M1）确实 warning-only，但 **RM-AG0087 的真实实现是阻断性硬检**；该句会让读者以为本条只有软告警。
3. **对账不覆盖本条原始缺陷**。DEBT0031 的 evidence（`tech-debt.md:1238-1239`）与设计 §7 的原始场景是「**P1 `phases` 漏写 P2**」；实测证明 `_reconcile_p1_fields` **抓不到**（fm 与正文同时漏写即 0 差异），只有硬检抓得到。

**建议**：把 RM-AG0087 注与 CHANGELOG 条目的锚点证据改为 **TAG0050 批 F 的 `phases ∪ pruned == phase_universe` 硬检**（`check-pruning.py:248-266`，ERROR/exit 1；README:78 同步），删除「级别 warning-only 系设计选择」句；如需保留对账作为**补充**证据，须显式区分「对账（fm↔正文，软）」与「闭合硬检（阻断）」两个机制。

### A2: 脚本→文档对齐 —— ALIGNED

本批**未改动任何脚本**（`git diff` 仅 3 个 md）。脚本→文档方向的相关不一致即 A1 所述的「脚本内 RM-AG0087 归属未被文档反映」，已在 A1 计一次，不重复计。

### A3: 一致性连锁 + 反向传播 —— NEEDS_HUMAN_REVIEW

**A3a 连锁（已知衍生）**：
- 任务点名的核对项「`roadmap.md` RM-AG0087 新注 vs RM-AG0113 注是否一致」→ **一致**。两者都写「锚点更正为 check-pruning」「对账已存在/默认开/在 gate 路径」（`roadmap.md:87` 与 `:112`）。⚠️ 但二者**共享同一处误归属**（见 A1）。
- DEBT0031（`tech-debt.md:1229-1263`）**已是 closed**，由已合并的 `0c29f7bc`（PR #436，批 A2/RM-AG0113）关单——**不在本工作区 diff 内**。本批 roadmap 注称「DEBT0031 同步关单」与该既成事实一致（非本批新增动作）。

**A3b 反向传播（主动推断，diff 未列出）**：
- **`agate/assets/templates/dispatch-prompt.md`（未改）**：该文件的「Review 角色特别指令」节（`:109-130`）是**全部评审/验收角色共享的只读纪律单源**（RM-AG0081 就落在那里，`SG.9a/SG.9d` 机械守护）。新增的「**写类工具一律在副本上跑**」规则是通用纪律（任何评审角色跑 `agate-inject-card.py`/`agate-md-field-set.py`/`agate-state-set.py` 都可能重演 47 文件事故），却**只落在 `protocol-alignment-review.md`**。**且本角色文件自己的「反向传播的常见路径」表（`:44`）规定：`agate/assets/review-roles/*.md` 改动 → 应传播到「模板文件、`dispatch-protocol.md`」**——本批未传播。
- 其它评审角色文件（`requirements-review.md`/`design-review.md`/`judge.md` 等）：是否需要各自复述该纪律，取决于是否走单源；若采纳「写进 dispatch-prompt.md 单源」则无需逐文件复制。
- `SELF-GATE.md`：只引用角色文件（`:40`/`:93`/`:177`），未承载只读条文 → 无需同步。
- `agate/WORKFLOW.md`：评审总览（`:316` 评审角色列 / `:382` pre-push 提示）只列角色名，不承载纪律条文 → 无需同步。

**结论**：NEEDS_HUMAN_REVIEW——建议把「写类工具在副本上跑」并入 `dispatch-prompt.md` 的只读纪律节（单源，惠及全部评审角色），或明确论证其确应限于本角色。

### A4: 测试覆盖 —— NEEDS_HUMAN_REVIEW

**本批自身**：纯文档/数据变更（无脚本/测试改动）⇒ 按 A4 字面口径无需新测试；全量 pytest 实跑见 A4b/A8（2909 passed，唯一 failed 为环境性）。

**但 RM-AG0087 的锚（「先加失败测试确认红 + 新测试覆盖」）未被真正满足**：
- 代码/README/BDD-70 把 RM-AG0087 归属到**闭合硬检**；该硬检的**唯一**「测试」是 `test_tag0050_proxy_judgment.py::test_bdd_70_phase_set_not_closed_errors`，其**先红锚**（`P3-test-cases.md:219`）写的是「`init_task()` 缺失（RM-AG0087）」。
- **实测：BDD-70 是假绿灯**。它跑的是 `check-gate.py P1`，而 `check-gate.py` **根本不调用** `check-pruning.py`（`grep -n "pruning\|phase_universe\|pruned" agate/scripts/check-gate.py` → 0 命中）。它用的 `init_task` 夹具 `phases: [P1, P2, P3, P4, P5, P6, P7, P8]` **本就是全集**（闭合），故：`check-pruning.py <夹具>` **rc=0**；`check-gate.py P1 <夹具>` rc=1 的原因是 **`GATE P1: 契约要求 judge … 须在 .state.yaml 声明 judge.enabled: true`**（与闭合无关）。即 BDD-70 的 Given（「`set(phases) ∪ set(pruned.phase)` 不等于 `phase_universe`」）**从未被构造**。
- 结论：**闭合硬检的负向（非闭合 → ERROR）无任何真实测试覆盖**（`grep -rn "阶段全集\|不闭合\|phase_universe" agate/tests/` 仅命中 BDD-70 自身文档串；唯一用非 legacy 夹具跑 `check-pruning` 的用例 `test_rm_ag0113_two_judgments_same_read` 断言 rc=0）。

**建议**：二者择一——(a) 修 BDD-70 为真红灯（非 legacy 夹具 + 非闭合 `phases` + 断言 `check-pruning.py` rc=1 / stderr 含「阶段全集」），再关 RM-AG0087；或 (b) 暂**不**关 RM-AG0087，另立条目承接该测试缺口。（若坚持采用本批的「对账即满足」口径，则该锚的测试要求由 `test_check_reconcile.py` 覆盖——但需先解决 A1 的机制归属问题。）

### A4b: 闭合后既有测试转红 + 夹具更新清单 —— ALIGNED

**空清单（显式写出）**：本批仅改 3 个文档/数据文件（`CHANGELOG.md` / `roadmap.md` / `protocol-alignment-review.md`），**无脚本/测试改动**，经**全量 pytest 实跑**（命令见 A8）：

```
1 failed, 2909 passed, 2 skipped, 1 rerun in 139.56s
```

- **无既有用例因本批转红**；**无需更新夹具**。
- 唯一 failed = `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，系**环境性**（本机 opencode 用 `debug agents`，测试调 `debug agent`），该测试文件**未被本批改动**，与批 A/RM-AG0110 评审报告（`agate-alignment-review-2026-10-09-A0110-NONPRUNE.md:185`）记录的同一环境性失败一致。
- 相关文档守护未受影响：`test_protocol_alignment_review.py::test_sg_9a/b/c/d`（只读纪律）、`test_sg_2/sg_2b`（A1-A8 主清单表）均绿——新增节位于主清单表/输出格式之后，未破坏其正则切区。

### A5: 下游影响 + 文档传播 —— NEEDS_HUMAN_REVIEW

- **CHANGELOG 已标注** ✓（`CHANGELOG.md` 新增条目，位于 `[Unreleased]`）。⚠️ 但条目落在 `### 修复` 节，其内容为「登记/治理」——同批的 RM-AG0103 状态变更与角色文件文档新增都非「修复」，**更贴合 `### 文档 / 登记` 节**（该节紧随其后）。建议移位（次要）。
- **文档传播缺口**：见 A3b——写类工具纪律未传播到 `dispatch-prompt.md`（共享单源）。
- **新规范节无机械守护**：同族的只读纪律有 `SG.9b`（`test_protocol_alignment_review.py`）防未来编辑丢失；**新增的「写类工具」节无任何守护**。若其目的是防 47 文件事故复发，建议补一条守卫测试（断言该节存在 + 点名具体写类工具）。属建议项。
- 破坏性变更：无（不改 gate 行为、不改 schema）。

### A6: 锚点表覆盖 —— ALIGNED

本批未新增协议规则、未改脚本行为 ⇒ 无需新增/更新 CHECK 9 锚点。新增节引用的脚本（`agate-inject-card.py` / `agate-md-field-set.py` / `agate-state-set.py` / `agate-task-init.py`）均存在；`check-protocol-consistency.py` 实跑 **0 ERROR**，且**改动文件未产生任何新 WARNING**（`--show-frozen-warnings` 中无源自这 3 个文件的条目）。

### A7: 设计原则一致性 —— ALIGNED

本批为登记/治理 + 文档新增，无架构决策，无需新 ADR。与 ADR-014（判据单源）**无冲突**：新增节是对评审角色的**过程纪律**补充，不涉及判据读取路径。（⚠️ A1 的机制归属问题属文档准确性问题，非 ADR 违反。）

### A8: 声称-命令绑定 —— MISALIGNED

| 声称（本批 / 相关记录） | 命令 | 结论 |
|---|---|---|
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py`（+ `--strict-errors-only`） | **复现**：`仅有 432 个 WARNING，无 ERROR`；`--strict-errors-only` rc=0 ✓ |
| `2909 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **复现**：`1 failed, 2909 passed, 2 skipped, 1 rerun`。⚠️ 1 failed = 环境性 opencode 用例（与本批无关）✓ |
| `roadmap 0 异常` | `python3 -c "…统计 split('\|') 列数≠9 的 \|RM- 行…"`（对齐 `check-gate.py` `_ROADMAP_EXPECTED_COLS=9`） | **复现**：`RM rows= 111 malformed= 0` ✓ |
| `ruff All passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（ruff **0.16.4** = CI 口径） | **复现**：`All checks passed!` rc=0 ✓ |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **复现**：rc=0 ✓ |
| 「`check-pruning.py:240` 的 `_reconcile_p1_fields`」 | `grep -n "_reconcile_p1_fields" agate/scripts/check-pruning.py` | **不准确**：定义在 `:158`、**调用**在 `:244`；`:240` 是 `phases_declared = _p1_field(...)`。行号错 4 行且指向错误位置 |
| 「弄脏 **47** 个 `P4-dispatch-context-*.md`」 | `docs/reviews/agate-alignment-review-2026-10-09-A0110-NONPRUNE.md:208` | **复现**：原文「弄脏 **47 个** `P4-dispatch-context-*.md`」✓（措辞「为验证『同源复用』」「逐个 `git checkout --`」为该报告上下文的**转述**：原文是单条 glob 还原——属轻度不精确，非错误） |
| 「TAG0051 … P1-requirements **19 BDD** 草稿」 | `git show task/TAG0051-release-decoupling:…/P1-requirements.md \| grep -c '^#### BDD-'` | **复现**：`19` ✓；`.state.yaml` `phase: P0` ✓ |
| 「级别 warning-only 系设计选择」 | `agate/scripts/check-pruning.py:248-266` | **误导**：RM-AG0087 的真实实现是**阻断性硬检**（见 A1）——**建议删除该声称** |

**结论**：MISALIGNED。除「:240 行号」与「warning-only」两条外，其余数字类声称均可复现。

---

## 重点结论（任务点名 5 项）

1. **① RM-AG0087 是否成立 —— 结论成立、理由写错、锚测试未满足。**
   - `_reconcile_p1_fields` 确实**默认开**（`agate_common.py:1242`，`AGATE_RECONCILE` 缺省 `1`）、**在 gate 路径**（`pre-commit-gate.py:965` 调 `check-pruning.py`）、**只发 WARNING 不改退出码**（docstring `:164` + `test_bdd_6_pruning_warning_and_exit_preserved` 断 rc=0）——**这三点均实测为真**。
   - **但它不是 RM-AG0087 的实现**。真实实现是 `check-pruning.py:248-266` 的**闭合硬检**（`phases ∪ pruned == phase_universe`，ERROR/exit 1），代码注释/README/BDD-70 **一致**这样归属；且对账**抓不到**本条原始缺陷（「phases 漏写 P2」实测 0 差异，硬检抓得到）。
   - 锚「先加失败测试确认红 + 新测试覆盖」**未被真正满足**：BDD-70 假绿灯（跑 check-gate，非闭合夹具）。**⇒ 建议：不按现理由关单；改注为闭合硬检，并决定是否补真红灯（A4）。**

2. **② RM-AG0103 → scheduled 的状态口径 —— 建议人工确认（NEEDS_HUMAN_REVIEW）。**
   - **已拆任务为真**：分支 `task/TAG0051-release-decoupling` 存在，`.state.yaml` `phase: P0`，P0-brief + P1-requirements（19 BDD）齐备，**active-tasks 行已在该任务分支**（`| TAG0051 | … | ⬜ | P0 |`）。与 `roadmap-template.md:19` 的定义「`scheduled` = 已拆任务」一致；也与本条的自我更正史（RM-AG0102：「原标 scheduled 但未拆任务 → backlog」）一致。
   - **唯一疑点**：`roadmap-template.md:32` 把 scheduled 绑到「**工作区 `tasks/` 建任务目录 + `active-tasks.md` 写入任务行**」，而**这两件产物只存在于未合并的任务分支**——本分支（及合并后的 main）**既无 TAG0051 任务目录、也无 active-tasks 行**。即：在「状态被改到 `scheduled`」的这个分支上，其前置产物**不在场**，main 的 roadmap 会**短暂**指向一个 main 上不存在的任务。
   - 无机械 gate 校验 scheduled（`grep -rn scheduled agate/scripts/*.py agate/rules/*.yaml` → 0 命中）⇒ 属软约定。**判为 NEEDS_HUMAN_REVIEW**：口径本身满足「已拆任务」，但落点时机（先于任务分支合并）值得人工拍板（可接受，或改在任务分支合并时一并回写）。

3. **③ 新节的准确性与位置 —— 事实准确；传播不足；与顶部只读节主题重复。**
   - **准确性**：47 文件数**准确**（来源 `A0110-NONPRUNE.md:208`）；「为验证『同源复用』」是对该报告上下文的合理转述（该评审重点即「判据是否真单源」）；「逐个 `git checkout --`」为轻度不精确（原文是单条 glob 还原）。
   - **位置/重复**：文件**顶部已有**「⚠️ 只读纪律（强制…RM-AG0081）」块（`:14-18`，含「副本上做 scratch」），新增节（`:111-121`）与之**同主题、同标题词**。二者互补（顶部=禁破坏性 git 命令；新增=禁写类脚本），但读者可能困惑。与 `## Write 前检查`（`:135`，关于 **Write 工具的目标路径**）**不冲突**（关注点不同：Write 工具 vs 写类脚本）。建议：合并进顶部只读节，或改名（如「只读纪律（续）：写类工具」）并交叉引用。
   - **其它角色/单源**：见 A3b——建议并入 `dispatch-prompt.md` 单源；`SELF-GATE.md`/`WORKFLOW.md` 无需同步。

4. **A4b**：**经实测无既有用例转红**（空清单，见 A4b 节；全量 pytest `2909 passed`，唯一 failed 为环境性 opencode 用例）。

5. **A8**：5 条数字/结论类声称**全部可复现**；另有 1 条行号不准（`:240`）、1 条误导性结论（「warning-only」）——见 A8 表。

---

## 审查过程说明（只读纪律）

- 本审查**只读代码、只写本报告与留痕文件**，未改任何协议/脚本/测试，未 commit/push。
- **所有写类/实验操作均在 `/tmp/opencode` 副本上跑**（`rm87probe` / `rm87probe2`），未对真实任务运行 `agate-inject-card.py` 等写工具（吸取 A0110 r1 的 47 文件事故教训）。
- 跑测试/脚本前后 `git status --porcelain` 一致（除本报告的 2 个产出文件）——实测收尾仅 ` M CHANGELOG.md / M roadmap.md / M protocol-alignment-review.md` + 本报告与留痕文件。
