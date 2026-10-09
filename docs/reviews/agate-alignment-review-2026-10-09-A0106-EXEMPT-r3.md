---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0106（DEBT0055+DEBT0056）r3 复核——只验 r2 指出的 1 处硬残留 + 4 处建议项
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/assets/review-roles/judge.md
  - agate/phase-cards/P6-acceptance.md
  - agate/scripts/check-maintainability.py
  - agate/tests/unit/test_docs_assertions.py
r1_report: docs/reviews/agate-alignment-review-2026-10-09-A0106-EXEMPT.md
r2_report: docs/reviews/agate-alignment-review-2026-10-09-A0106-EXEMPT-r2.md
---

# 协议-脚本对齐审查 r3（A0106-EXEMPT）

> 分支 `hotfix/batch-a-exemption`（未提交）。只读代码、只写本文件与留痕文件，未改任何协议/脚本/测试，未 commit/push。r3 仅核 r2 残留与建议项。

## 5 项改正核实（逐项证据）

| # | r2 残留/建议 | 核实证据 | 结论 |
|---|---|---|---|
| 1 | `CHANGELOG.md:92`「judge…机械复核」（硬）| `CHANGELOG.md:89-95` 现为「**机械面在 P5**（`pre-task-baseline.md` ↔ `fail-list.txt` diff），judge 处**信息隔离**（白名单不含 `known-failures.md`、禁读 `P6-acceptance.md`）⇒ judge **人工**复核（`check-judge-verdict.py` **无**该逻辑，勿声称机械复核）」| ✅ **已修** |
| 2 | `CHANGELOG.md:94`「依据（设计条目）」+ 口径 | 字段名改「**理由**」；并补「机械可查的登记/计数路径 + 人工评审确认（机械面只到「文件存在 + 条目数 ≥ violation 数」，不判「是否设计强制」）」| ✅ **已修** |
| 3 | `DEBT0055.recommendation` 落点含 `check-judge-verdict.py` | `tech-debt.md:2196` 落点改为「`P6-acceptance.md`（口径 + 机械面指向 P5 baseline diff）」+ 追加「**2026-10-09 更正（SELF-GATE r1 证伪）**：原写「须 judge 可机械复核」**不成立**…⇒ judge 侧为**人工**复核」| ✅ **已修**（原句 `:2195` 保留但紧邻证伪）|
| 4 | `P6-acceptance.md:41`「机械口径」| 改为「本节补齐与 P5 一致的**口径（机械面在 P5，judge 侧人工复核）**」| ✅ **已修** |
| 5 | `judge.md` 补口径（且去重）| `judge.md` 末新增「## 遇「pytest 全绿」类 BDD 时的口径（RM-AG0106）」节；`grep -c` = **1**（去重成功）；节前有空行；含「信息隔离 + 由主 Agent 转述 baseline、不得越白名单取文件」| ✅ **已修** |

## 问题 2：judge.md 唯一性 + 全仓活表述扫描

- `grep -c "遇「pytest 全绿」类 BDD 时的口径（RM-AG0106）" agate/assets/review-roles/judge.md` → **1**（无重复）。
- **「依据（设计条目）」**：全仓 `--include=*.md --include=*.py`（排除 `docs/reviews/`）→ **0 处**（已清零）。
- **「机械复核」**：无**未证伪的活断言**。分类——
  - **已修的正确表述**：`CHANGELOG.md:94`、`agate/phase-cards/P6-acceptance.md:54`、`test_docs_assertions.py:132-133` —— 均为「**勿**声称机械复核」**否定式** ✓。
  - **原句 + 紧邻证伪（可接受）**：`tech-debt.md:2195`（recommendation 原句）下一行 `:2196` 即证伪；`:2199` 为 closure_criteria 的**更正注**（引述被证伪原文）。
  - **原始 spec / 完成注澄清（可接受）**：`roadmap.md:105` 的**spec 列**仍含「judge 可机械复核」+「（+ `check-judge-verdict.py`）」——这是 RM 的**原始定义**（冻结），其**完成注列**已写「judge 按…复核」（无「机械」）。属本仓「spec 冻结、结果记于注列」惯例。
  - **非本批 / 异构语境（无关）**：历史任务记录 `TAG0026/TAG0030/TAG0050` 的 retrospective/dispatch-context；`docs/design-notes/design-orchestration-semantics.md:123`（exit 2 子状态的合法用法）。`.worktrees/blog-post11/...` 属另一工作树，不在本分支工作区。

## 问题 3：全量 pytest（`-n auto`）

```
python3 -m pytest agate/tests/ --reruns 1 -n auto -q
→ 1 failed, 2907 passed, 2 skipped, 1 rerun in 140.75s
```
- 唯一 `FAILED test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` = 先于本批存在的**环境性**失败（实跑真实 `opencode debug agent`，本机只有 `debug agents`）。
- **`test_m1_forward_jump_*`（p0_to_p5 / p0_to_p7 / p2_to_p5）本轮未转红**——DEBT0063 登记的跨文件 flaky 本轮**未复现**（`-n auto` 间歇性；不阻断，DEBT0063 已 open 登记）。
- 无既有用例因本批转红；无需更新夹具。

## 问题 4：A8 声称-命令绑定

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | ✅ RC=0，0 ERROR（429 frozen WARNING）|
| 2 | 全量 pytest 绿 | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✅ `1 failed(环境), 2907 passed, 2 skipped` |
| 3 | check-debt rc=0 | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ RC=0 |
| 4 | roadmap 0 异常 | RM 行 111 条均 9 列（`_ROADMAP_EXPECTED_COLS=9`）| ✅ 0 异常 |
| 5 | 「judge 机械复核」不再作为活声称 | `grep` 扫描（见上）| ✅ CHANGELOG/P6 卡已改；余为原句+紧邻证伪或冻结 spec |

## 问题 5：是否可 commit

**是——可 commit。**

- r2 的唯一硬残留（`CHANGELOG.md:92` 的「机械复核」）**已修**；4 处建议项**全部落实**（含 judge.md 补口径，A5 传播缺口闭合）。
- A1-A8 + A4b 全部 ALIGNED（r1 的核心误述「把人工口径表述为 judge 机械复核」已彻底消除并逐条与代码核对无误）。
- 两处「原句保留 + 紧邻证伪」（`tech-debt.md:2195`）与「RM 原始 spec」（`roadmap.md:105`）按本仓惯例**可接受**（前者下一行即证伪；后者 spec 冻结、完成注已澄清）——非阻断。
- `test_m1_forward_jump_*` 本轮未红；若未来 `-n auto` 间歇转红，归 DEBT0063（已登记），不阻断本批。

> 总评：三轮回合收敛。本批语义（P6 预存失败豁免口径 + 维护性越阈既定出口）与实现/脚本事实**一致**，无据声称已清零，测试与 4 项声称均复现。
