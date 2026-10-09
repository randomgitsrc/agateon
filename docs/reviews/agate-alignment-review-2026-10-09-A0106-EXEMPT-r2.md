---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0106（DEBT0055+DEBT0056）r2 复核——r1 的 4 项 MISALIGNED + 3 附带问题已改；本批复核 6 项改正是否到位 + 残留
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/phase-cards/P6-acceptance.md
  - agate/scripts/check-maintainability.py
  - agate/tests/unit/test_docs_assertions.py
r1_report: docs/reviews/agate-alignment-review-2026-10-09-A0106-EXEMPT.md
---

# 协议-脚本对齐审查 r2（A0106-EXEMPT）

> 分支 `hotfix/batch-a-exemption`（未提交）。本报告只读代码、只写本文件与留痕文件，未改任何协议/脚本/测试，未 commit/push。

## 审查结论汇总

| # | 审查项 | r1 | r2 结论 |
|---|--------|----|---------|
| A1 | 文档→脚本对齐 | MISALIGNED | **ALIGNED**（P6 卡 judge 条重写；4 条事实声明逐条与代码核对一致）|
| A2 | 脚本→文档对齐 | ALIGNED | **ALIGNED**（docstring 改为准确口径 + 字段名「理由」）|
| A3 | 一致性连锁 + 反向传播 | MISALIGNED | **NEEDS_HUMAN_REVIEW**（主缺口已修；残留：CHANGELOG 字段名、DEBT0055 recommendation、P6 卡「机械口径」措辞、judge.md 未同步）|
| A4 | 测试覆盖 | MISALIGNED | **ALIGNED**（DEBT0055 判据更正 + 新增文档断言用例，实跑通过）|
| A4b | 闭合后既有测试转红 + 夹具清单 | 无 | **无既有用例转红 / 无夹具需更新**（实跑 `1 failed, 2907 passed, 2 skipped, 1 rerun`）|
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW | **NEEDS_HUMAN_REVIEW**（judge.md 未同步——作者选「口径写进 P6 卡」路线，需人裁是否够）|
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED** |
| A7 | 设计原则一致性 | ALIGNED | **ALIGNED** |
| A8 | 声称-命令绑定 | MISALIGNED | **MISALIGNED（残留）**——`CHANGELOG.md:92` 仍写「judge 按…**机械复核**」（已被 r1 证伪的同一声称，未删）|

**是否可 commit：否（仅差一处硬残留）**——`CHANGELOG.md:92` 的「机械复核」必须删/改为「人工复核」（A8）；其余为可选的措辞清理（A3/A5）。核心对齐问题（A1）已实修并逐条核实无误。

---

## r1 发现逐条核实

| r1 项 | 声称的改正 | 独立核实 | 结论 |
|---|---|---|---|
| **1. judge 机械复核无实现且与隔离互斥** | P6 卡 judge 条重写 | `P6-acceptance.md:46-56`：判据呈现去「机械」；新增「**机械面在 P5**」（`pre-task-baseline.md` ↔ `P5-test-results/fail-list.txt` diff，`gate_p5`）；「**judge 侧**：信息隔离（白名单 `_WHITELIST_MD` 不含 `known-failures.md`、禁读 `P6-acceptance.md`）⇒ **人工**核对；`check-judge-verdict.py` **无**该逻辑（勿声称机械复核）」| ✅ **已修** |
| **2. ② 验收锚过宽** | docstring 改准确口径 | `check-maintainability.py:26-33`：「机械可查的**登记/计数**路径 + 人工评审确认」+「机械面只到 `gate_p4` 文件存在 + 条目数 ≥ violation 数，**不判**是否设计强制」| ✅ **已修** |
| **3. ① 残留软滥用口** | P6 卡要求与 baseline 逐条对应 | `P6-acceptance.md:50,55`：「豁免集须与该 baseline **逐条对应**，不得凭空新增」+「未在 `known-failures.md` **且不在 P5 baseline** ⇒ 视为本次引入」| ✅ **已修** |
| **4. DEBT0055 判据未满足仍关单** | 判据更正 + 补文档断言用例 | `tech-debt.md:2197-2200`：#1 改「本次引入失败 0」；#2 改为**判据更正注**（写明 r1 证伪理由）；#3 新增「文档断言用例」；`test_docs_assertions.py:121-133` 新用例（5 断言）实跑 **1 passed** | ⚠️ **部分**：判据/用例已补；但 `recommendation:2195` 仍留「须 judge 可机械复核」+ 落点 `check-judge-verdict.py`（未同步）|
| **5. DEBT0056 evidence 误贴 P6 note** | 改为 check-maintainability ref | `tech-debt.md:2225-2231`：ref 已改为 `agate/scripts/check-maintainability.py`，note 重写为维护性口径（不再贴 P6 节）| ✅ **已修** |
| **6. docstring 字段名不一致** | 「依据（设计条目）」→「理由」 | `check-maintainability.py:28`：「文件 / before / after / 阈值 / **理由**」| ✅ **已修**（但 `CHANGELOG.md:94` 仍写「依据（设计条目）」）|

**r1 修复方向 item 2 未执行**：`CHANGELOG.md:92` 仍为「judge 按「实际失败集 − known-failures 集 = ∅」**机械复核**」——与已修的 P6 卡**直接矛盾**。

---

## 5 项重点核实

### 1. 6 项是否真的修了 → 见上表：4 项 ✅ 全修、1 项 ⚠️ 部分（DEBT0055 判据已补但 recommendation 未同步）、1 项 ✅（附 CHANGELOG 残留）。

### 2. P6 卡新表述是否与事实一致（逐条核代码）

| P6 卡声明（行） | 代码证据 | 判定 |
|---|---|---|
| 「白名单 `_WHITELIST_MD` **不含** `known-failures.md`」（:51）| `check-judge-verdict.py:81-87` `_WHITELIST_MD = {p1-requirements.md, p2-design.md, .state.yaml, gate-events.jsonl, p6.5-judge-verdict.md}` | ✅ 真 |
| 「**禁读** `P6-acceptance.md`」（:52）| `check-judge-verdict.py:70-74` `_BLACKLIST_MD` 含 `p6-acceptance.md`；`judge.md:15`「P6-acceptance.md 是 verifier 的自述——不读、不引用」 | ✅ 真 |
| 「`check-judge-verdict.py` **无**该逻辑」（:54）| 全文件已读（9 步校验链，无任何测试失败集/`known-failures` 读取）| ✅ 真 |
| 「机械依据是 P5 的 `pre-task-baseline.md` ↔ `P5-test-results/fail-list.txt` **diff**（`gate_p5` 已实现）」（:48-50）| `check-gate.py:1276-1316` `gate_p5`：`pre_list` vs `post_set` → `new_fails`（本次引入）/ `still_failing`（预存）；`still_failing` 须 `known-failures.md` 登记计数 ≥ 数 | ✅ 真 |

⇒ P6 卡新表述**与事实完全一致**，r1 的核心误述已消除。

### 3. 新增文档断言用例是否真覆盖该口径

`test_rm_ag0106_p6_preexisting_failure_exemption`（`test_docs_assertions.py:121-133`）5 条断言逐条映射 P6 卡原文：

| # | 断言关键词 | P6 卡对应原文（行） | 命中 |
|---|---|---|---|
| 1 | `预存失败豁免口径` | 节标题（:37）| ✅ |
| 2 | `本次任务引入的失败 = 0`（或 `引入失败 0`）| 判定基准（:43）；PASS 行示例（:47）| ✅ |
| 3 | `pre-task-baseline.md` | 机械面在 P5（:49）| ✅ |
| 4 | `禁读` + `_WHITELIST_MD` | judge 侧（:51-52）| ✅ |
| 5 | `勿声称机械复核` | judge 侧（:54）| ✅ |

⇒ 5 条断言**均有对应原文**，实跑 `1 passed`。**局限（须知悉）**：这是**关键词存在性**断言（与 `test_docs_assertions.py` 全文件风格一致），只守护「P6 卡写了这些条文」，**不验证条文与代码的事实一致性**（如 `_WHITELIST_MD` 是否真不含 known-failures.md）——后者靠本报告第 2 项的人工核对。对 doc-only 改动属恰当粒度。

### 4. DEBT0055 判据更正是否恰当（更正 vs 重开）

**判断：更正被证伪的判据是更诚实的做法，优于重开债务——但须同时清掉同块内的 stale recommendation。**

理由：
- 债务的**问题本体**是「P6 无预存失败豁免口径」，该缺口**真实存在且已实修**（P6 卡新节）。重开债务会**误述**「底层缺口仍未修」。
- 被证伪的是**当时的处置形式假设**（「judge 可机械复核」——登记时假定机械可行，事后证明与 judge 隔离互斥）。这是**手段假设**，非债务本体。
- 更正**已做到诚实的两点**：① 显式标注「**SELF-GATE r1 证伪**」保留原判据的失败痕迹（而非静默替换）；② 新判据（#1「P6 卡含口径」+ #3「文档断言用例」）仍**检验问题本体**，不是「照抄实现细节凑通过」。
- ⚠️ **一处不诚实风险**：`recommendation:2195` 仍写「（与 P5 卡 known-failures 一致，**须 judge 可机械复核**）」且落点含 `check-judge-verdict.py`——**同一 YAML 块内**的这条 stale 文本会让读者以为该要求仍成立。**应**删除或加注「已被 #2 判据更正证伪」。

### 5. A4b + A8 实跑

**A4b**：`python3 -m pytest agate/tests/ --reruns 1 -n auto -q` →
```
1 failed, 2907 passed, 2 skipped, 1 rerun in 140.79s
```
- **无既有用例因本批转红**；`passed` 由 r1 的 2906 → **2907**（+1 = 新增的 `test_rm_ag0106_...`，已单独实跑 `1 passed`）。
- 唯一 `FAILED test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` 为先于本批存在的**环境性**失败（实跑真实 `opencode debug agent`，本机只有 `debug agents`），与本批无因果。
- **无需更新任何夹具**。

**A8（本批声称逐条复现）**：

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | ✅ RC=0，0 ERROR（429 frozen WARNING）|
| 2 | 全量 pytest 绿（新增用例通过）| `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✅ `1 failed(环境), 2907 passed, 2 skipped` |
| 3 | check-debt rc=0 | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ RC=0 |
| 4 | roadmap 0 异常 | RM 行 111 条均 9 列（`_ROADMAP_EXPECTED_COLS=9`）| ✅ 0 异常 |
| 5 | 「judge 按…**机械复核**」（`CHANGELOG.md:92`）| **无命令**——`check-judge-verdict.py` 无该逻辑 | ❌ **无据声称仍在，须删** |

---

## 残留清单（供收尾）

| 严重度 | 位置 | 问题 | 建议 |
|---|---|---|---|
| **硬（A8）** | `CHANGELOG.md:92` | 仍写「judge 按…**机械复核**」（r1 已证伪的同一声称）| 改为「judge **人工**复核（机械面在 P5）」|
| 软（A3） | `CHANGELOG.md:94` | 仍写「依据（设计条目）」，与已改的 docstring「理由」不一致 | 改为「理由」|
| 软（A3） | `tech-debt.md:2195` | DEBT0055 `recommendation` 仍「须 judge 可机械复核」+ 落点 `check-judge-verdict.py`，与同块 #2 判据更正矛盾 | 删除或加注「已证伪」|
| 软 | `P6-acceptance.md:41` | 引子仍写「本节补齐…的**机械口径**」（正文已澄清机械面在 P5）| 改为「本节补齐与 P5 一致的**判定口径**」|
| 软（A5） | `agate/assets/review-roles/judge.md` | 未同步该口径（作者选「写进 P6 卡」路线）| 需人裁：judge 是执行者，宜在 `judge.md` 留一句（口径须经 dispatch-context 到达 judge）|
| 记录 | `roadmap.md:105` | RM-AG0106 spec 列「验收锚=…**机械可查的豁免路径**」原文未动（完成注已澄清）| 可接受（spec 为原始定义）；如需一致可加注 |

---

## 闭环

| 结论 | 项 | 动作 |
|------|----|------|
| MISALIGNED | A8（`CHANGELOG.md:92`）| **必须修复**（1 行；修完即可 commit）|
| NEEDS_HUMAN_REVIEW | A3（残留措辞）/ A5（judge.md 传播）| 人工确认后附 `[HUMAN_CONFIRMED: …]`；非阻断项可作后续清理 |
| ALIGNED | A1 / A2 / A4 / A4b / A6 / A7 | 通过 |

> **总评**：r1 的核心误述（把人工口径表述为 judge 机械复核、与隔离机制互斥）已**实修并逐条与代码核对无误**；DEBT0055 判据更正**方向正确且诚实**。仅剩 `CHANGELOG.md:92` 一处硬残留（同一证伪声称未删）——修掉即可 commit；其余为可选措辞清理。
