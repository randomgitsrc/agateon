---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: r2 复审——核实批 A（RM-AG0107/DEBT0054 + RM-AG0108/DEBT0051）4 项改正是否落地，并做完整 A1-A8(+A4b) 复评
files_changed:
  - AGENTS.md
  - CHANGELOG.md
  - SELF-GATE.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/UPGRADING.md
  - agate/assets/execution-roles/implementer.md
  - agate/assets/review-roles/protocol-alignment-review.md
---

# 协议-脚本对齐审查（r2 复审）

> 本报告独立核实 r1（`docs/reviews/agate-alignment-review-2026-10-09-A0107-0108-DOC.md`）的 A3 MISALIGNED 与 2 项 NEEDS_HUMAN_REVIEW 是否已改正。**未采信**「已改正」声明，逐条给出证据。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（两条新规均为文档/行为约束，无脚本应对应实现） |
| A2 | 脚本→文档对齐 | ALIGNED（本批仍未改任何脚本） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED（部分闭合）**：主表 A4b ✓、SELF-GATE 枚举 ✓、人工验收清单 ✓；**但 SELF-GATE.md 仍残留 4 处「A1-A8」未同步（含 r1 明确点名的 `:163` 成果文件要求）**；且改正 2/4 **新引入 4 处 stale 记录引用**（见下） |
| A4 | 测试覆盖 | ALIGNED（纯文档变更；全量 pytest 2903 passed + 1 环境失败） |
| A4b | **闭合后既有测试转红 + 夹具更新清单** | ALIGNED（经实测无既有用例因本批转红；`test_sg_2` 仍绿） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（r1 的语义错位已由改正 4 消解：公告约束节已移为顶层 `##`，`UPGRADING.md:40`） |
| A6 | 锚点表覆盖 | ALIGNED（consistency 0 ERROR；CHECK 9 PASS） |
| A7 | 设计原则一致性 | **ALIGNED**（r1 的「自觉/机械」歧义已由改正 3 显式承认消解；RM-AG0107 为角色行为规则，本质属 ADR-015 手段③） |
| A8 | 声称-命令绑定 | ALIGNED（4 条声称全部复现；**但**本批记录中出现与实现不符的 stale 引用——计入 A3） |

**核心判定**：4 项改正中 **3 项完全落地**（implementer 边界、RM-AG0108 自觉承认、UPGRADING 移节），**1 项部分落地**（A3：主表/枚举/验收清单已同步，但 SELF-GATE.md 残留 + 新引入 stale 引用）。**结论：暂不可 commit**（详见末节）。

## r1 发现逐条核实

### r1-A3（A4b 未进权威「审查清单」主表）→ **部分闭合**

| r1 列出的应同步项 | 现状 | 证据 |
|---|---|---|
| role file「审查清单」主表补 A4b | ✅ 已修 | `protocol-alignment-review.md:30`（A4 与 A5 之间插入 A4b 行，含「目的：…收敛到一轮（TAG0050 G3 实证）」） |
| `SELF-GATE.md` 派发模板 A1-A8 枚举补 A4b | ✅ 已修 | `SELF-GATE.md:133`（A4 与 A5 之间新增 A4b 行） |
| role file 人工验收清单「A1-A8 八项」 | ✅ 已修 | `protocol-alignment-review.md:137`：「含 A1-A8 八项（+ **A4b**…），每项有结论」 |
| **`SELF-GATE.md` 成果文件要求「含 A1-A8 结论汇总表」**（r1 明列的第 3 项） | ❌ **未修** | `SELF-GATE.md:163` 仍为「成果文件含 frontmatter + **A1-A8** 结论汇总表（含反向传播检查）+ 逐项审查详情。」 |
| `SELF-GATE.md` 其余 A1-A8 提及 | ❌ 未修 | `:70`（文件约定表「结构化审查报告（A1-A8）」）、`:190`（全量审查模式「逐项检查 A1-A8」）、`:239`（未实现时等价检查「对照 A1-A8」） |

**逐字一致性核查**（r2 问题 2）：role file 两处 A4b **非逐字一致**——
- 主表 `:30` 结尾多一句「。目的：把「改一处发现一处红」的往返整改**收敛到一轮**（TAG0050 G3 实证）。」；
- 输出格式模板 `:88` 无该句。
- **评估**：输出模板其余行均为「…」占位（本就是示意，非逐字要求），此差异**实质无害**；但既然主表已补，建议两处文本对齐（或主表也去掉「目的」句），以彻底满足 ADR-014「判据单源」。

**结论**：A3a（同一文件两表分叉）**已闭合**；A3b（反向传播）**未完全闭合**——`SELF-GATE.md:163` 是 r1 明确点名项，仍漂移。

### r1-重点 2（implementer 边界：P3 测试 vs 既有测试；出口指向）→ **已闭合（1 处轻残留）**

| r1 指出的问题 | 改正 | 证据 |
|---|---|---|
| 未区分「P3 任务测试」与「仓库既有测试」 | ✅ 已在两处澄清 | `implementer.md:20`「**不改 P3 测试去迁就实现**；但**仓库既有的其它测试**若因设计要求而转红，**必须更新它们**」；`:48`「**不修改 P3 测试本身**；**仓库既有其它测试**因设计要求转红时须更新」 |
| 「设计要求有误」出口错指 `[DESIGN_GAP]`/`[SCOPE+]` | ✅ 已改指 `[CLARIFY]` | `implementer.md:80`「若你认为设计要求**本身**有误 → 走 **`[CLARIFY: …]`**（见「P4 实现答疑」节…）；`[DESIGN_GAP]`/`[SCOPE+]` 的语义是「歧义下自主决策」/「发现新需求」，**不是**「质疑需求」」 |

- **`[CLARIFY]` 指向正确性核实**：`implementer.md:111-117` 确有「P4 实现答疑」节——「如对 P2 方案有疑问，标注 `[CLARIFY: xxx]` → 主 Agent 暂停 → 派 architect 解答 → 回 P4」。指向与语义**匹配**。✅
- **无新歧义**：`P3 测试`（契约定义，不得改）与`仓库既有其它测试`（随契约演进须更新）在 `:20`/`:48` 两处显式对立，清晰。✅
- **轻残留（非阻断）**：决策树 `implementer.md:26` 仍写「**测试**断言与 P1 BDD 矛盾 → 标 `[DESIGN_GAP]`，**不改测试**」，其中「测试」未限定为 P3。对「既有测试断言与新 P1 BDD 矛盾」这一边界情形，该行与 `:20` 的新规可被读成冲突。建议该行改为「**P3 测试**断言与 P1 BDD 矛盾 → …」。

### r1-重点 3 / A7（RM-AG0108 不可机械核验）→ **已闭合**

改正 3 在 `DEBT0051.closure_criteria` 追加了显式承认条（`tech-debt.md:2031` 附近）：
> ⚠️ **2026-10-09 实测复核**：`grep` 全 `agate/scripts/` **无**「截止版本/未排期/实施版本号」判据 ⇒ 本判据实为**自觉 + 评审**（`AGENTS.md` 发布清单 3a / `UPGRADING` 公告约束节 + 发布 PR 评审），**无机械门禁**——该口径已在上述两条新条文中写明。

**独立复核**：`grep -rn "截止版本\|未排期\|实施版本号" agate/scripts/` 仍仅命中 `check-gate.py:739` 一条**不含版本号**的 WARNING 文案（非判据）⇒ 承认条与实测一致。✅

### r1-A5（UPGRADING 新节语义错位）→ **已闭合**

改正 4：`agate/UPGRADING.md:40` 现为**顶层** `## 版本号公告约束（RM-AG0108 / DEBT0051）`，位于 `:47` `## 版本管理生命周期` **之前**（不再是其子节）。语义错位消除。✅
- **副作用（计入 A3）**：`tech-debt.md:2017`（DEBT0051 关单证据）仍写「`agate/UPGRADING.md`「**版本管理生命周期**」新增「版本号公告约束」节」——节已移出该节，**该记录已过时**。

## 逐项审查（r2）

### A1: 文档→脚本对齐
**结论**：ALIGNED。两条规则均为行为/人类约定（implementer 纪律、发布公告纪律），本批未触及 `agate/scripts/*`，不存在「文档声明 vs 脚本实现」不一致。

### A2: 脚本→文档对齐
**结论**：ALIGNED。`git diff` 无 `.py`/`.sh`。

### A3: 一致性连锁 + 反向传播
**结论**：**MISALIGNED（部分闭合）**。

**(a) 未同步（r1 点名 + 连带）**：
- `SELF-GATE.md:163`（成果文件要求「含 A1-A8 结论汇总表」）—— r1 明列项，**未修**。
- `SELF-GATE.md:70` / `:190` / `:239`（其余 3 处 A1-A8 提及）—— 未同步。

**(b) 改正 2/4 新引入的 stale 记录引用（改了实现却没回改记录）**：

| 位置 | 现文本 | 应为 | 成因 |
|---|---|---|---|
| `CHANGELOG.md:71-72` | 「认为设计要求有误须走 `[DESIGN_GAP]`/`[SCOPE+]`」 | `[CLARIFY]` | 改正 2 改了出口，CHANGELOG 未回改 |
| `tech-debt.md:2131`（DEBT0054 evidence） | 「…指向 `[DESIGN_GAP]`/`[SCOPE+]` 出口」 | `[CLARIFY]` | 同上 |
| `roadmap.md:106`（RM-AG0107 更新列） | 「（契约驱动优先 + DESIGN_GAP/SCOPE+ 出口）」 | `CLARIFY` 出口 | 同上 |
| `tech-debt.md:2017`（DEBT0051 evidence） | 「`agate/UPGRADING.md`「**版本管理生命周期**」新增…节」 | 「顶层新增…节」 | 改正 4 移了节，evidence 未回改 |

**(c) 逐字一致性（轻微）**：role file 主表 `:30` 与输出模板 `:88` 的 A4b 文本非逐字（主表多「目的」句）——见 r1-A3 节评估。

**建议**：补齐上述 (a) 4 处 + (b) 4 处；可选对齐 (c)。

### A4: 测试覆盖
**结论**：ALIGNED。纯文档变更，无新增用例合理。
**全量实跑**（CI 口径 `agate/tests/README.md:28`）：
```
python3 -m pytest agate/tests/ --reruns 1 -n auto -q
→ 1 failed, 2903 passed, 2 skipped, 1 rerun in 144.26s
```
唯一失败 `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`：`opencode debug agent` → `Unknown subcommand "agent"`（应为 `agents`），**环境性**（opencode CLI 变更），与本批文档改动无关。

### A4b: 闭合后既有测试转红 + 夹具更新清单
**本次变更使哪些既有用例转红 / 需更新哪些夹具**：
> **经实测无既有用例因本批转红，无需更新任何夹具。**
- 本批含 **role file 主表新增 A4b 行**（`:30`）——`test_protocol_alignment_review.py::test_sg_2` 只断言主表 A1..A8（`range(1,9)`），A4b 不触发；全量 pytest 结果（A4）中 `test_sg_2/2b` 均绿。
- 唯一红为环境性 `test_bdd_43`，非本批引入。
**结论**：ALIGNED。

### A5: 下游影响 + 文档传播
**结论**：ALIGNED。无 gate 行为变化；CHANGELOG 已标（`:69-78`）；UPGRADING 新节语义错位已由改正 4 消解。

### A6: 锚点表覆盖
**结论**：ALIGNED。`check-protocol-consistency.py` → `rc=0`，CHECK 9 `✅ PASS`，0 ERROR（424 WARNING 全冻结）。

### A7: 设计原则一致性
**结论**：ALIGNED。相关 ADR：ADR-014（判据单源，见 A3c）、ADR-015（手段优先级）。r1 的「自觉 vs 机械」歧义已由改正 3 的 `closure_criteria` 显式承认消解；RM-AG0107 为角色行为规则（本质属手段③，不可机械化），ADR-015 允许。
**残留建议（非阻断）**：可在提交信息/关单说明补一句「为何不采用 ADR-015 ②『让错误可见』」的取舍留痕。

### A8: 声称-命令绑定
**结论**：ALIGNED。逐条复现见下表；本批记录中 4 处「与实现不符的 stale 引用」计入 A3（属一致性连锁，非无据声称）。

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✓ `rc=0` |
| 2 | `roadmap 0 异常` | 按 `check-gate.py:2159-2177` 同款解析（`line.split("|")` 长度 == `_ROADMAP_EXPECTED_COLS`(9)） | ✓ 全 `^\|\s*RM-` 行 **0** 列数异常；RM-AG0107/0108 均 9 段、`done` |
| 3 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✓ `rc=0`，CHECK 1–16 无 ERROR（424 WARNING 全冻结） |
| 4 | `全量 2903 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✓ **2903 passed**（同批 1 环境失败 + 2 skipped + 1 rerun） |

---

## 是否可 commit

**否——暂不可 commit**（A3 判 MISALIGNED，按角色闭环规则「MISALIGNED 必须修复，修完重审」）。须修复的均为**一行级**编辑：

| # | 文件:行 | 现文本 → 目标 |
|---|---------|--------------|
| 1 | `SELF-GATE.md:163` | 「含 **A1-A8** 结论汇总表」→ 含「A1-A8 **+ A4b**」结论汇总表（r1 点名项） |
| 2 | `CHANGELOG.md:71-72` | `[DESIGN_GAP]`/`[SCOPE+]` → **`[CLARIFY]`** |
| 3 | `agate-workspace/debt/tech-debt.md:2131` | 「指向 `[DESIGN_GAP]`/`[SCOPE+]` 出口」→ 「指向 **`[CLARIFY]`** 出口」 |
| 4 | `agate-workspace/roadmap/roadmap.md:106` | 「DESIGN_GAP/SCOPE+ 出口」→ 「**CLARIFY** 出口」 |
| 5 | `agate-workspace/debt/tech-debt.md:2017` | 「`UPGRADING.md`「**版本管理生命周期**」新增…节」→ 「`UPGRADING.md` **顶层**新增…节」 |

**可选（非阻断）**：
- `SELF-GATE.md:70` / `:190` / `:239` 的「A1-A8」一并补 A4b（与 `:133`/`:163` 保持一致）。
- `implementer.md:26` 决策树的「测试」限定为「**P3 测试**」。
- role file 主表 `:30` 与输出模板 `:88` 的 A4b 文本对齐（去/加「目的」句）。

**修复后**：因均属文档文本，重跑 `check-protocol-consistency.py`（0 ERROR）+ 全量 pytest 即可，**无需重开 A1-A8 全量**（可按 r1 报告 + 本 r2 的 A3 残余项定点复核）。

> **只读纪律遵守说明**：本次复审未执行任何写仓/破坏性 git 操作；未改任何协议/脚本/测试；仅写入留痕文件（`…-02.progress.md`）与本 r2 成果文件。
