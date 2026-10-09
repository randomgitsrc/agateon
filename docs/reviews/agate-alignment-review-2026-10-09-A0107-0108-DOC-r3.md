---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: r3 复审——只核实 r2 列出的 SELF-GATE.md 4 处 A1-A8 同步 + A4b 逐字对齐 + 4 处 stale 引用 + 决策树 :26 是否已修
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

# 协议-脚本对齐审查（r3 复审）

> 范围：只验 r2 列出的 5 处一行级 + 4 处 stale 引用。逐项给证据（`grep`/行号）。

## 5 项结论

### 1. `SELF-GATE.md` 4 处 A1-A8 → **✅ 已修（+ 1 处 cosmetic 残留）**

`grep -n "A1-A8" SELF-GATE.md`：
- `:70` → 「结构化审查报告（**A1-A8 + A4b**）」✅
- `:163` → 「含 frontmatter + **A1-A8（+ A4b…）** 结论汇总表…」✅（r2 点名项，已修）
- `:190` → 「逐项检查 **A1-A8（+ A4b…）**——见角色文件」✅
- `:239` → 「对照 **A1-A8 + A4b**」✅
- **`:128` → 「逐项检查 A1-A8（见角色文件）」未加「+ A4b」**（其下方枚举 `:133` 已含 A4b 行）。**cosmetic**：枚举本身完整，仅该引言行措辞与 `:190` 风格不一。非阻断。

### 2. A4b 逐字一致 → **❌ 非逐字（差 1 个句号）**

两处原文（`grep -n "A4b"`）：
- 主表 `:30`：`| A4b | **闭合后既有测试转红 + 夹具更新清单**（RM-AG0107 / DEBT0054） | 逐条列出「本次变更使哪些**既有**用例转红 / 需更新哪些夹具」及其处置；**空清单也须显式写出**（"经实测无既有用例转红"）**。** |`
- 输出模板 `:88`：`| A4b | **闭合后既有测试转红 + 夹具更新清单**（RM-AG0107 / DEBT0054） | 逐条列出「本次变更使哪些**既有**用例转红 / 需更新哪些夹具」及其处置；**空清单也须显式写出**（"经实测无既有用例转红"） |`

r2 多出的「目的：…（TAG0050 G3 实证）」句**已删** ✅；但 `:30` 仍以「**。**」结尾、`:88` 无句号 ⇒ `python` 逐行比对 `identical: False`。**cosmetic（1 个标点）**：要求正文逐字相同，仅句末标点差异，非实质（ADR-015）。

### 3. 4 处 stale 引用 → **3/4 已修；④ 未落实**

| # | 位置 | 现状 | 结论 |
|---|------|------|------|
| ① | `CHANGELOG.md:72` | 「认为设计要求有误须走 **`[CLARIFY]`**」 | ✅ |
| ② | `tech-debt.md:2132`（DEBT0054 evidence） | 「指向 **`[CLARIFY]`** 出口」 | ✅ |
| ③ | `roadmap.md:106`（RM-AG0107 更新列） | 「契约驱动优先 + **`[CLARIFY]`** 出口」 | ✅ |
| ④ | `tech-debt.md:2017`（DEBT0051 evidence） | **仍为**「`agate/UPGRADING.md`「**版本管理生命周期**」新增「版本号公告约束」节」 | ❌ **未修**（改正 3④ 未落实） |

- 全仓 `grep "DESIGN_GAP`/`[SCOPE+] 出口"` → **无 live 残留**（仅历史任务记录，无关）。
- ④ 的事实：公告约束节现为 `agate/UPGRADING.md:40` **顶层** `## 版本号公告约束`，位于 `:47 ## 版本管理生命周期` 之前 ⇒ 该 evidence 的「版本管理生命周期」定位**与现状不符**。应为「`agate/UPGRADING.md` 新增**顶层**「版本号公告约束」节」。

### 4. 决策树 `:26` → **✅ 已修**

`implementer.md:26`：
> 2. **P3** 测试断言与 P1 BDD 矛盾 → 标 `[DESIGN_GAP]`，**不改 P3 测试**（仓库**既有**其它测试若因此转红，须按设计要求更新——见「不得以『保持既有测试全绿』为由不实现设计要求」）

「测试」已限定为 **P3**，并显式指出「仓库既有其它测试」的相反处置 ⇒ 与 `:20`/`:48`/新节一致，无残留歧义。✅

### 5. A8 声称-命令绑定 → **全部复现**

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✓ `rc=0`，CHECK 1–16 无 ERROR（424 WARNING 全冻结） |
| 2 | `2903 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✓ **2903 passed**（同批 1 failed 环境性 + 2 skipped + 1 rerun, 93.23s） |
| 3 | `ruff All checks passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（CI 口径，ruff **0.16.4**） | ✓ `All checks passed!` `rc=0` |
| 4 | `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✓ `rc=0` |
| 5 | `roadmap 0 异常` | 按 `check-gate.py:2159-2177` 同款解析（`line.split("|")` 长度 == `_ROADMAP_EXPECTED_COLS`(9)） | ✓ 全 `^\|\s*RM-` 行 **0** 列数异常 |

（唯一 pytest 失败 `test_bdd_43_opencode_registration_and_debug_agent` = 环境性 `opencode debug agent` → `Unknown subcommand "agent"`，与本批文档改动无关。）

## 是否可 commit

**可 commit**（协议/脚本面已对齐：`SELF-GATE.md` 4 处枚举、role file 主表 A4b、implementer 决策树、3/4 stale 引用均已修正；`0 ERROR` / `2903 passed` / `ruff` 绿 / `check-debt rc=0` / `roadmap 0 异常`）。

**建议顺手修（均非阻断，属 ADR-015「非实质」）**：
1. `tech-debt.md:2017` —— 改正 3④**未落实**：把「`UPGRADING.md`「版本管理生命周期」新增…节」改为「`agate/UPGRADING.md` 新增**顶层**「版本号公告约束」节」（1 行，事实性）。
2. `SELF-GATE.md:128` —— 「逐项检查 A1-A8（见角色文件）」可补「+ A4b」，与 `:190` 一致（1 行，cosmetic）。
3. role file `:30` / `:88` —— A4b 行末「。」对齐（1 个标点，cosmetic）。

> **只读纪律遵守说明**：本次复审未执行任何写仓/破坏性 git 操作；未改任何协议/脚本/测试；仅写入留痕文件（`…-03.progress.md`）与本 r3 成果文件。
