---
status: approved_with_nits
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---
# SELF-GATE 评审：DEBT0046 新增脚本登记面（RM-AG0068 另一半）

## 范围

本批为 **直改通道**交付（分支 + PR，未走 P0-P8，无任务目录）。改动 11 个跟踪文件 + 1 个新测试文件，
核心是：把「新增 `agate/scripts/check-*.py` 要同步哪些登记面」从**凭记忆**变成**有权威清单 + 单一机械判据**，
并修掉过程中实测发现的一处判据矛盾。

**触发面**：`agate/scripts/*.py` + `agate/**/*.md` + 仓库根 `AGENTS.md` ⇒ 须 SELF-GATE（本报告即留痕）。

## 结论

**APPROVE WITH NITS —— 1 MAJOR + 2 MINOR + 2 NIT，全部已处置，无 BLOCKER。**

评审独立复现了本批的**核心声称**：旧 SG.6 断言确是**子串**判定，加一行**注释**提及探针脚本名即可让它变绿，
而 `CHECK9-coverage` 仍告警 —— **两处判据对同一事实给出相反结论**。修法（抽出 `uncovered_gate_scripts()`
供 gate 与 SG.6 **共用**）真实且结构性地消除了该类分歧。

评审同时确认所有可复算数字**逐一吻合**：`2438 passed`（2 failed 均为既有环境缺陷、非本批触及文件）、
`0 ERROR / 386 WARNING`、`+11 用例`（2442 vs HEAD 2431）、ruff 全绿、tag0034 绊线 6 文件 sha256 无漂移。
**唯一被判定为失实的陈述**是登记面表第④行的「无机械校验」（见 MINOR-2）。

## 逐条核实（评审给结论，本表为摘要）

| # | 声称 | 判定 | 依据 |
|---|------|------|------|
| 1 | 旧 SG.6 存在「注释即可满足」的判据矛盾 | **TRUE** | 评审在 scratch 副本放探针 + 一行注释：旧断言 0 缺失（绿），`check_anchor_coverage` 仍出 1 条 WARNING；副本已清理、diff hash 未变 |
| 2 | 单一判据被 gate 与 SG.6 共同消费、SG.6 不再用子串 | **TRUE** | `check-protocol-consistency.py:812/:847`；`test_protocol_alignment_review.py:101-106` |
| 3a | `CHECK9-coverage` 是真门禁（WARNING） | **TRUE** | 未登记脚本使 warning 387→388，增量恰为 `{CHECK9-coverage:+1}` |
| 3b | SG.6 是真门禁（pytest 会红） | **TRUE** | 同一合成树 ⇒ SG.6 FAILED |
| 3c | CHECK 10 不因「新增脚本文件」触发（方向相反） | **TRUE** | 增量中 `CHECK10-scriptref` 无变化；而 README 写不存在的名字 ⇒ **ERROR**，同句写进 CHANGELOG ⇒ 仅叙事 WARNING |
| 3d | `scripts/README.md` 索引行无机械校验 | **PARTIAL / 原文失实** | 7 个 `check-*.py` 无索引行而全绿 ✔；但 `test_doc_sweep.py:210` 对 `agate_package.py`/`agate-release.py` 确有断言（删行即红）⇒ 「**无**机械校验」表述错误 → **MINOR-2** |
| 3e | `count-tests.sh` 是下界语义 | **TRUE** | 只 echo「目标：≥ 749」，无 assert；`749` 无任何消费方 |
| 4 | 11 条新测试非真空 | **PARTIAL** | 真回退下 12 条红 ✔；但「判据恒返回 `[]`」突变下仅 3/11 红 ⇒ `test_t43_2` 与 SG.6 同型真空 → **NIT-5** |
| 5 | P1/P2/architect 三处要求实测 | **TRUE** | 三处均存在且要求"放进仓库跑一遍"；HEAD 上三文件该措辞命中数为 0 ⇒ 回退即红 |
| 6 | 数字类声称 | **TRUE** | 全部复算吻合 |

## 处置记录（评审后由主 Agent 逐项完成）

| 编号 | 级别 | 问题 | 处置 |
|------|------|------|------|
| MAJOR-1 | **MAJOR** | `roadmap.md` RM-AG0068 行**自相矛盾**：状态格已翻 `done`，同行创建格仍写「② DEBT0046 未做（仍 open）…**故本条 RM 保持 backlog，不标 done**」 | 改为过去时叙述「该批结束时保持 backlog」+ 明写「**现已 done**」；并把 DEBT0046 **移出 A 档待办清单**（加"已由 TAG0043 完成并出列"标注）。无机制能捕获此类散文矛盾（RM-AG0043 只校验 done 回写存在性） |
| MINOR-2 | MINOR | 登记面表第④行「**无机械校验**」**失实**（评审以删行突变实测复现） | 改为「**约定**（有特定例外）」并写明 `test_doc_sweep.py` 对哪两个脚本有断言；**同类扩展到第⑤行**（`test_mvwu_protocol_docs.py` 对 `check-mvwu` 行有断言）——只修被报告的那一处正是本仓反复复发的反模式 |
| MINOR-3 | MINOR | closure_criteria 指定「**P2 卡或 architect.md**」须点名 SG.6 / CHECK 9 / CHECK 10；初版只在 `scripts/README.md` 点名 CHECK 10 ⇒ 字面未满足，而 closure_note 却称"已满足" | P2 卡「影响面梳理」第 4 条改为**三处齐名**（并注明 CHECK 10 方向相反）；新增判据 `test_t43_9b_p2_card_names_all_three_closure_criteria_surfaces` 固化；DEBT0046/roadmap 的"诚实补充"改写为**如实承认初版字面未满足** |
| NIT-4 | NIT | `test_t43_4` docstring 越界声称"证明旧子串判据被骗"，但该用例**从不执行**旧判据（只断言自己刚写入的字面量） | docstring 加**范围声明**：本用例只确认当前判据不退回子串语义；旧判据的复现证据是**一次性探针实测**（记于 DEBT0046 closure_note），非本用例 |
| NIT-5 | NIT | `test_t43_2`（真实仓库零未覆盖）缺非真空自证——判据被架空时它照样通过（与我在 SG.6 修掉的是同一模式） | 加合成树非真空自证；`test_t43_4` 探针名改为中性 `check-t43probe.py` 避免与 SG.6 重复 |

## 复验结果（整改后）

| 项 | 结果 |
|----|------|
| 全量 pytest | **2439 passed / 2 failed / 2 skipped**（整改新增 `t43_9b` 后）（2 failed 为既有环境缺陷：opencode 不在 PATH、临时目录为独立 tmpfs 致 `git clone --bare --local` 跨设备链接；均非本批触及文件） |
| consistency | **0 ERROR / 386 WARNING**（与基线一致） |
| ruff | 全绿 |
| tag0034 绊线 | 6 基线文件 sha256 无漂移 |
| **突变复验**（判据恒返回 `[]`） | 失败用例由 3 个（`t43_3/4/5`）增至 **5 个**（+`t43_2`、+SG.6）（+`t43_2`、+SG.6）⇒ NIT-5 已实质修复 |
| 探针清理 | `git status` 无残留（`check-zzprobe.py` / `check-newgate.py` / `check-t43probe.py` 均只存在于合成树或已删） |

## 遗留与诚实说明

- **评审期间父 Agent 持续编辑被评审文件**（AGENTS.md 第 6 条、SG.6 非真空探针均在评审中途出现）——与本仓既有的「评审快照 vs 持续编辑」流程缺口同源，本次未单方面改动该流程。评审以其核实当时的 diff hash 为准并已声明。
- **本批未做**：`RM-AG0071/0072/0073`（效率类，需先出设计）；`DEBT0040` 仅剩的 CI 兜底步**需用户许可**才能动 `.github/workflows/`。
- 评审发现「`test_t43_6/7/8`、`t43_9/10` 为**存在性/子串**断言，无法识别"清单写错"」——已如实登记，**本次不修**：这些是文档存在性守护，其正确性由人工评审承担（与 `DEBT0049` 同性质，不宜用机械判据伪装成语义判据）。
