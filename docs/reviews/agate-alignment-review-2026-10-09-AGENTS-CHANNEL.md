---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 修 `AGENTS.md`「改动通道」内部矛盾——协议本体/脚本改动改判为「独立评审义务」而非「立项义务」
files_changed: [AGENTS.md]
commit: 5171206a
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED** |

**结论**：更正后的**语义口径**（协议本体/脚本改动触发独立评审义务、非立项义务）**本身正确**——与条件 2、轴 C、`SELF-GATE.md` 逐条一致。但本批**未完成反向传播**，且在**同一文件的就地更正**中留下两处结构问题：

1. **A3/A5（反向传播漏项）**：`docs/guides/worktree-dogfooding-guide.md:266` 是 `AGENTS.md`「改动通道」节的**活镜像**，仍写「`agate/` 协议本体/脚本改动」属于「**不适用 hotfix（必须立项为任务）**」——即被本次更正的**同一旧口径**，未同步 ⇒ 更正后与 `AGENTS.md` 直接冲突。
2. **A3（就地更正不彻底）**：更正后的第 3 条**仍列在「不适用 hotfix（必须立项为任务）」标题之下**，而其正文已明说「**不是立项义务**……走 hotfix 即可」——**条目正文与所属标题自相矛盾**，修复把「与条件 2 矛盾」换成了「与本节标题矛盾」。
3. **A8（声称不可复现）**：commit message 的「反向传播自检：协议文档/根级文档中无别处重复该旧口径（grep 0 命中）」**为假**——用与语义相符的检索词（`协议本体/脚本改动`、`不适用 hotfix`）命中上述镜像文件。

修复方向：① 同步 `worktree-dogfooding-guide.md`（连同其滞后的条件 1「≤2 文件」一并改「单一主题」）；② 把更正后的第 3 条移出「必须立项」清单，或改写为独立「⚠️ 更正说明」段落；③ 删除/更正 commit message 中不可复现的 grep 声称。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`AGENTS.md:58`，更正后）：
> ……**口径以条件 2 + 轴 C 为准**：协议本体/脚本改动**触发的是独立评审义务**（提交信息写 `self-gate-review:`），**不是**立项义务——**一次性修复**（单一主题、可快速验证）走 **hotfix + 独立评审**即可；只有**跨多子系统 / 需探索性设计 / 需阶段产出与看板登记**才立项。

**比对锚点**（逐条）：

- 条件 2（`AGENTS.md:42`）：「**不是 agate 任务** | 无 P0-brief/.state.yaml/P1-P8 产物（一次性修复）。**注意：这与是否触发 SELF-GATE 无关**——若碰触发面，仍须在提交信息写 `self-gate-review:`」→ 与更正后正文**一致**（SELF-GATE 触发 ↔ 独立评审留痕，与立项解耦）。
- 轴 C（`AGENTS.md:25`）：「碰 SELF-GATE 触发面 → 须独立评审；**留痕**由 `self-gate-review:` 提交信息机制检查（仅 WARNING、**不拦截**）——**与 B 无关**」→ 与更正后正文**一致**。
- `SELF-GATE.md:7-11`（强制力边界）：「本机制目前有 commit-msg hook 辅助提醒……**WARNING 不拦截**……真正的强制力依赖主 Agent 自觉 + CI 兜底」→ 只谈**评审/留痕**，**从不提「立项」**。更正后正文与之**一致**（把协议改动的义务限定为独立评审，未越界断言立项）。

**脚本面**：`改动通道`（立项 vs hotfix）是**人读的工作流约定**，无机器判据实现该分叉——`check-protocol-consistency.py` 不对「是否立项」做任何判定（`agate/scripts/*` 中无该概念）。故本项无「文档↔脚本」可对齐对象。

**结论**：ALIGNED（更正后的语义与条件 2 / 轴 C / `SELF-GATE.md` 逐条一致；无对应脚本判据）。

---

### A2: 脚本→文档对齐

本次变更**仅改 `AGENTS.md` 一行**（`git show 5171206a` 确认），无脚本改动，故无「脚本→文档」待同步项。

**结论**：ALIGNED（无脚本改动）。

---

### A3: 一致性连锁 + 反向传播

#### A3a 一致性连锁（已知衍生改动）

- **`SELF-GATE.md` 是否需同步**：**不需要**。其「强制力边界」（`SELF-GATE.md:7-11`）表达的是**评审留痕**口径（hook WARNING 不拦截、强制力靠自觉 + CI），**从未主张协议改动须立项**——与更正后口径本就不冲突。触发面表（`SELF-GATE.md:19-35`）只列「哪些文件触发 SELF-GATE」，与「触发后是否立项」是两个问题。**ALIGNED，无需同步**。

#### A3b 反向传播（应被影响但 diff 未列出的文件）

**应被影响的文件：`docs/guides/worktree-dogfooding-guide.md`（未更新）。**

理由：该文件 `242` 行有**同名节**「## 改动通道：worktree 优先，hotfix 例外」，并在 `246` 行**显式声明是 `AGENTS.md` 同节的镜像**：

> `docs/guides/worktree-dogfooding-guide.md:246`：「**先分开三件事**（混同会导致误判，`AGENTS.md`「改动通道」**有同表**）」

其 `266` 行仍写：

> `docs/guides/worktree-dogfooding-guide.md:266`：「**不适用 hotfix（必须立项为任务）**：需阶段产出的改动（= agate 任务）、跨子系统探索性设计、**`agate/` 协议本体/脚本改动（触发 SELF-GATE，须独立评审并留痕 `self-gate-review:`；是否另开 worktree 仍按轴 B 判断）**。」

这正是**本次被更正的同一旧口径**（协议本体/脚本改动列于「必须立项」清单），且与该文件自己的条件 2（`guide:261`「这与是否触发 SELF-GATE 无关」）**同样自相矛盾**。本次未同步 ⇒ 更正后**新矛盾**：`AGENTS.md:58` 说「不是立项义务」，`guide:266` 说「必须立项」。旁证：`agate-workspace/reviews/self-gate-worktree-necessity-20260929.md:118` 记录该节当初就是按「『不适用』改为**须立项**」写的，故其立场是刻意的、非笔误。

**附带发现（同一镜像的陈旧项）**：`guide:260` 条件 1 仍写「改动面 **≤2 文件**、无跨模块影响」，而 `AGENTS.md:41` 已于 **2026-10-03**（commit `37ed89d4`）更正为「**单一主题**（可跨多文件）」。即该镜像在本批之前已滞后于 `AGENTS.md`（本批未改，属既有欠账，一并指出）。

**其余候选文件核查**（均**不**需同步）：

| 文件 | 判定 |
|------|------|
| `agate/**`（协议本体） | 无「协议改动须立项」表述；`agate/` 内 `立项` 均指**项目侧 P0 立项**，与此工作流约定无关（grep 实测） |
| `agate/assets/templates/handoff-template.md:17` | 已写「三轴（立项 / 工作目录 / 独立评审）不要混同」——与更正后口径**一致**，无需改 |
| `agate-workspace/**`、`docs/reviews/**`、`archived/**` | 任务数据 / frozen 历史记录，按设计不回改 |
| `README.md` / `README.zh-CN.md` | 面向使用者的接入门面，无此开发工作流约定 |

**结论**：**MISALIGNED**——反向传播漏 `docs/guides/worktree-dogfooding-guide.md`（活镜像，非 frozen）。

#### A3c 就地更正的结构问题（同一文件内）

更正后的第 3 条**仍位于标题「**不适用 hotfix（必须立项为任务）**：」之下**（`AGENTS.md:55-58`），但正文已明写「**不是**立项义务……走 hotfix + 独立评审即可」：

```
55: > **不适用 hotfix（必须立项为任务）**：
56: > - 需要阶段产出/看板登记/roadmap 回写的改动（= agate 任务）
57: > - 改动跨多个子系统或需探索性设计
58: > - ⚠️ （2026-10-09 更正）…… 协议本体/脚本改动……不是立项义务——一次性修复……走 hotfix + 独立评审即可……
```

⇒ 第 3 条**正文与所属标题直接冲突**。修复把「与条件 2 矛盾」换成了「与本节标题矛盾」——矛盾未消除，只是换了对手。正确做法：把该条**移出**「必须立项」清单（协议改动**不是**「不适用 hotfix」的实例），或改写为独立的「⚠️ 更正说明」段落。

**结论**：MISALIGNED（就地更正未彻底；新矛盾 = 条目正文 vs 本节标题）。

---

### A4: 测试覆盖

本次为 **docs-only**（仅 `AGENTS.md` 一行），无脚本/判据改动，故**无需新增 pytest**。

**已执行的验证**：

1. 相关文档断言测试（直接读 `AGENTS.md`）——**实跑通过**：

   ```
   python3 -m pytest agate/tests/unit/test_doc_sweep.py \
     agate/tests/unit/test_tag0030_assertions.py \
     agate/tests/unit/test_docs_assertions.py \
     agate/tests/unit/test_retrospective_protocol_docs.py -q
   → 60 passed in 0.38s   (EXIT=0)
   ```

2. **既有测试不覆盖本口径**：`grep -rn "协议本体或脚本改动\|协议本体/脚本改动\|不适用 hotfix\|必须立项" agate/tests/` → **rc=1（0 命中）**。即「改动通道」判据文本**无任何 pytest 守护**——本次反向传播漏项（A3b）也**不会被机械测试发现**。此为**观察项**（该文本是人读约定，非机器判据，无守护本身可接受；但它使 A3b 类漂移只能靠人工审查捕获）。

3. **全量 pytest**：见下方「全量实跑」。

**全量实跑输出**（本机，2026-10-09）：

```
python3 -m pytest agate/tests/ -q -n auto
→ 1 failed, 2876 passed, 2 skipped in 84.33s (0:01:24)
```

**唯一失败项与环境相关、与本变更无关**：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——失败根因是本机 `opencode` CLI 的子命令为 `debug agents`（复数）而非测试期望的 `debug agent`（单数）：

```
ERROR  Unknown subcommand "agent" for "opencode debug"
       Did you mean this?  agents
assert 1 == 0
```

单跑复现（`... ::test_bdd_43_opencode_registration_and_debug_agent` → `1 failed in 0.23s`），**与本次 docs-only 改动（仅 `AGENTS.md` 一行）无因果**。该失败属本机工具链版本漂移，**非本批引入**。

**污染核验**：全量跑后 `git status --porcelain` 仅显示本审查的两份产出文件，`agate-workspace/**` 账本零改动（DEBT0040 兜底未被触发）。

**结论**：ALIGNED（docs-only 无需新测试；相关文档测试 60 passed；全量 2876 passed，唯一失败为环境相关且与本变更无关）。

---

### A5: 下游影响 + 文档传播

**下游 gate 行为**：无影响——本变更为开发侧工作流约定，不改变任何 gate 脚本行为、不改变协议对使用者项目的语义，**无破坏性变更**。

**CHANGELOG**：本次为 `AGENTS.md` **内部自相矛盾的就地澄清**，不改变协议对外行为；`AGENTS.md` 的实质约定（协议改动触发 SELF-GATE → 独立评审留痕）**未变**，只是删去一个与之矛盾的条目。故**不强制** CHANGELOG 条目（判断项；若维护者倾向留痕可补，但非 gate 要求）。

**文档传播**：**不完整**——`docs/guides/worktree-dogfooding-guide.md`（活镜像）未同步（详见 A3b）。这与 `ADR-014`「文档可以复述，但必须指向权威源」的**漂移**形态吻合：镜像已声明指向 `AGENTS.md`，但其复述已与权威源分叉。

**结论**：**MISALIGNED**（文档传播漏 `worktree-dogfooding-guide.md`）。

---

### A6: 锚点表覆盖

本次未新增协议规则、未改 `check-*.py`，**CHECK 9 锚点表无需更新**（锚点表映射「协议文档声明 ↔ 脚本关键词」，本次变更不含新声明且不碰脚本）。

补充事实（供后续参考，非本项判据）：根 `AGENTS.md` 确实在 `check-protocol-consistency.py` 的扫描面内——`SCRIPT_REF_SCAN_FILES`（`:970-971`）显式含 `"AGENTS.md"`（CHECK 10 脚本名引用漂移扫描面），故本次改动**会被 CHECK 10 扫描**；该次运行 CHECK 10 为 WARN 且仅命中 frozen 历史文件（见 A8 命令 2），未因本次改动新增告警。

**结论**：ALIGNED。

---

### A7: 设计原则一致性

- **ADR-005（改动性质决定流程——声明性/行为逻辑/机制交叉，`adr.md:134`）**：更正后口径以「**改动性质**」（单一主题 vs 跨多子系统 / 探索性设计）为入口维度，且**明确放弃「文件数」作代理**（`AGENTS.md:45-49`）——与 ADR-005「判断入口是**改动性质**而非任务规模」**一致**。
- **ADR-014（判据单一权威源——判据必须单源，文档可以复述，`adr.md:533`）**：本次更正的**原则本身符合** ADR-014（`AGENTS.md` 为权威源、指南复述）。**但** A3b 的漏项正是 ADR-014 语境里描述的病征——「文档复述」与权威源**分叉且无人发现**（`adr.md:573-574`：「漂移的危害不是『改起来麻烦』，是『必然改漏且无人能发现』」）。这不是**本批引入了违反 ADR 的设计**，而是**本批未把已存在的复述漂移一并收口**。按 A7 规则（设计原则指导性、只有 ALIGNED / NEEDS_HUMAN_REVIEW），本项记为 ALIGNED，漂移归 A3b 处置。
- 未发现需要新补的架构决策。

**结论**：ALIGNED（并提示：A3b 的镜像漂移应并入本批修复）。

---

### A8: 声称-命令绑定

逐条列 `声称 → 命令 → 结论`：

| # | 声称（出处） | 产出命令 | 结论 |
|---|------|---------|------|
| 1 | commit message：「反向传播自检：**协议文档/根级文档中无别处重复该旧口径（grep 0 命中）**」 | 与语义相符的检索：`grep -rn "协议本体/脚本改动" --include="*.md" .`、`grep -rn "不适用 hotfix" --include="*.md" .` | ❌ **假**——两命令均命中 `docs/guides/worktree-dogfooding-guide.md:266`。仅当检索词缩到字面 `协议本体或脚本改动`（`或` vs `/`）才「0 命中」，属**过窄检索**。**应删除/更正该声称** |
| 2 | commit message：「校验：`check-protocol-consistency.py` 0 ERROR」 | `python3 agate/scripts/check-protocol-consistency.py` → `EXIT=0`，输出「仅有 413 个 WARNING，无 ERROR」 | ✅ **真**（413 WARNING 均为 frozen 历史文件，按设计不收敛） |
| 3 | `AGENTS.md:58`：「实践先例：`TAG0042-debt-batch` / `TAG0043-check-registration` / `TAG0044-debt-triage` / `TAG0050-hotfix-M1`（均批次标签直改、**无任务目录**）」 | `grep -n "^task_id:" agate-workspace/debt/tech-debt.md`（4 个 task_id 均存在：`1502/1662/1835`、`1730`、`1795`、`2165`）；`ls -d agate-workspace/tasks/TAG00{42,43,44,50}*` | ⚠️ **基本属实，但有编号碰撞**：4 条 DEBT 条目 `task_id` **均存在** ✓；精确 slug（`TAG0042-debt-batch` 等）**确无同名任务目录** ✓；**但**编号被真实 P0-P8 任务占用——`agate-workspace/tasks/TAG0042-config-and-enforcement/`（P0 2026-10-04）与 `agate-workspace/tasks/TAG0050-task-data-contract/`（P0 2026-10-06，且 `TAG0050-hotfix-M1` 即其 M-1 整改）**存在**。「无任务目录」按字面（slug）成立，但读者按编号理解会误判，建议措辞点明「编号被真实任务复用」 |
| 4 | `AGENTS.md:58`：「**原文第 3 条为「`agate/` 协议本体或脚本改动（触发 SELF-GATE）—— **必须立项**」**」 | `git show 5171206a^:AGENTS.md`（第 58 行原文） | ⚠️ **转述不精确**：原第 3 条**正文并无「必须立项」四字**（原文为「……须走独立评审并留痕 `self-gate-review:`……是否另开 worktree 仍按轴 B 判断」）；「必须立项」实为**所属标题**「不适用 hotfix（必须立项为任务）」的措辞。引号内并非逐字引用，建议改为「（依标题）属『必须立项』清单」 |

**结论**：**MISALIGNED**（声称 1 为假，须删除/更正；声称 4 为不精确转述）。

---

## 需修复项（MISALIGNED）

| # | 项 | 修复方向 |
|---|----|---------|
| M1 | A3b/A5：`worktree-dogfooding-guide.md:266` 未同步 | 按 `AGENTS.md:58` 更正口径改写该行；顺带把 `guide:260` 条件 1「≤2 文件」改为「单一主题」（对齐 `AGENTS.md:41`） |
| M2 | A3c：更正后第 3 条仍列于「不适用 hotfix（必须立项为任务）」标题下，正文与标题矛盾 | 将该条**移出**「必须立项」清单，或改写为独立「⚠️ 更正说明」段落 |
| M3 | A8：commit message「grep 0 命中」声称不可复现 | 删除/更正该声称（协议本体/根级文档中**确存在**重复旧口径的活镜像） |

**次要（NIT，建议但不阻断）**：A8 声称 3 建议点明编号复用；A8 声称 4 的引号应改为转述标注。

---

## 备注：本报告的只读边界

本次审查**未修改任何协议 / 脚本 / 测试**，仅写本报告与留痕文件；未 `commit` / `push`。全量 pytest 已在后台完成并回填（见 A4），跑后账本零污染。
