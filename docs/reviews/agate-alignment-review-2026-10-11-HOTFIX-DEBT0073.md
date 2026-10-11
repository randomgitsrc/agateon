---
review_date: 2026-10-11
reviewer: protocol-alignment-review
round: r3（最终确认）
status: approved
change_summary: DEBT0073 收口（最终）——判据的 self-gate 留痕接受集改导入 hook 的 _REVIEW_RE/_SKIP_RE（正则定义真单源），接受 self-gate-skip: 非空理由；r2 两项文字级问题（tech-debt closure_note 未收窄、「2 处」应为「3 类」）已据实更正；残差 3 类既有逻辑差异另立 DEBT0075。
files_changed: [agate/tests/unit/test_tag0051_self_gate.py, SELF-GATE.md, CHANGELOG.md, agate-workspace/debt/tech-debt.md]
---

# 协议-脚本对齐审查（最终）— HOTFIX-DEBT0073（`hotfix/debt0073-unify-trailer`）

> 三轮：r1 判 `needs-revision`（A2 错路径、A8 超范围声称）；r2 判 `needs-revision`（tech-debt closure_note 未收窄、残差不均计数）；r3 确认全部据实闭合。只读评审；探针在 `/tmp/opencode` 一次性副本内建→清。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（经实测无既有用例转红） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（closure_note 已随其余处收窄） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **ALIGNED**（计数已据实为「3 类」；超范围声称已删） |

**MISALIGNED 数：0。**
**接受集对齐是否引入放松：否**（见文末「核心结论」）。

## ① r1/r2 两项文字级问题 → 闭合核验（逐条，不采信转述）

| r2 待修项 | 处置 | 核验 |
|---|---|---|
| A5：`tech-debt.md` `closure_note` 仍称「接受集真单源」 | 已收窄 | `tech-debt.md:3220-3225` 现为「**正则定义**已真单源（`is` 同一对象）+ 5 组代表性样例一致 + 负例仍全判违规 ⇒ **成因**已消除」，并「⚠️ 如实限定：接受集**尚未**逐例一致——另有 **3 类既有逻辑差异**已另立 **DEBT0075**，『接受集一致（单源）』在逻辑层未完全达成」。✓ |
| A8：残差「2 处」应为「3 类」+ 测试注释 ③ 表述 | 三处改为「3 类」 | `CHANGELOG.md:24`、`SELF-GATE.md:13`、`test_tag0051_self_gate.py:342` 均现为「**3 类**既有…差异…交独立债务 DEBT0075」，第 ③ 类描述含「不存在且非 `reviews/`」与「真实存在则一致」对照。✓ |

**残留强声称扫描**（改动面）：`逐个一致 / 结构上不可分叉 / 接受集真单源 / 结构上不再可能` → **无命中**（除"不构成…穷尽证明"的正当否定句）。错路径 `.githooks/commit-msg-self-gate.sh` → **限定面 grep 空**。

## ② 本审查自身第 3 条发现的更正（重要）

**r1 原表述（不精确）**：把「`self-gate-review:` 指向**非 `reviews/`** 路径」本身作为分叉条件。
**更正**：分叉的**真实条件**是「路径**不存在**且 hook 不视其为报告指向」；若该非报告路径是**真实文件**，双方**一致接受**。

**本审查独立复跑探针**（合成仓；judge `_bdd_22_violations` vs hook 真实子进程；`_SKIP_RE is` / `_REVIEW_RE is` = True）：

| # | trailer | judge | hook | 结论 |
|---|---|---|---|---|
| C1 | `self-gate-skip: 理由` + `self-gate-review: <幽灵>` | 拒 | 接 | 分叉（判据更严）|
| C2 | 非行首 `self-gate-review: <路径>` | 接 | 拒 | 分叉（hook 更严）|
| C3 | `self-gate-review: agate/scripts/probe_agree.py`（**真实文件**，非 reviews/） | 接 | 接 | **一致** |
| **C3'** | `self-gate-review: agate/scripts/ghost_probe.py`（**不存在**，非 reviews/） | **拒** | **接** | **分叉（判据更严）** |
| C4/C5 | `reviews/` 真实报告 / 幽灵报告 | 接/接、拒/拒 | 同 | 一致 |

⇒ 你方 r2 的「真实文件 → 一致」成立；r3 已将第 ③ 类精确为「**不存在且非 `reviews/`**」并补对照句，**记录与实测一致**。我上轮对此条的标签不精确，已在本文件更正。

## ③ DEBT0075 新登记核验

`tech-debt.md` 新增 `## DEBT0075`（`status: open`、`priority: medium`），标题「BDD-22 判据与 commit-msg hook 的留痕**逻辑**差异 3 类（正则已真单源，逻辑层尚未单源）」；evidence 含 **3 类逐例复现**（含方向：①③ 判据更严、② hook 更严）+「此前记录误作 2 处，已据实更正」；recommendation 给 (a) 逻辑层单源（抽可导入判定函数）/ (b) 明示权威侧并对齐，均要求为 3 类补判别力用例；closure_criteria 两条。✓
计数核验：`grep -c '^## DEBT'` = **75**、`grep -c '^status: open'` = **1**（唯一 open 即 DEBT0075）。✓

## 核心结论

1. **本批未引入放松**：判据接受 `self-gate-skip:` 是对齐 hook 与 `SELF-GATE.md`/`AGENTS.md`（`:134`）既有约定的**缩小分叉**（此前判据只认 `self-gate-review:` ⇒ 轻量档逃生通道在 CI 必红）。`skip` 仍要求**理由非空**——本审查独立构造负例（无留痕 / `skip` 空 / `skip` 纯空白 / `review` 指向不存在路径）**全部仍判违规**。
2. **正则定义真单源**：判据导入 hook 的 `_SKIP_RE`/`_REVIEW_RE`，实测 `is` **同一对象**；判据文件内无第二份留痕正则字面量。
3. **残差 3 类属既有逻辑差异**（非本批引入；根因：判据「review 优先 + 全 token 校验」vs hook「二者任一 + 仅报告指向 token 校验」），已**如实记录并另立 DEBT0075**（open）。
4. 实现与测试正确；记录已与事实一致。

## 实测复核（本轮独立跑）

| 命令 | 结果 |
|---|---|
| `python3 -m pytest agate/tests/unit/test_tag0051_self_gate.py -q` | **15 passed** |
| `ruff check agate/` | **All checks passed!** |
| `python3 agate/scripts/check-protocol-consistency.py` | **0 ERROR**，433 冻结 WARNING（未增） |
| `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **rc=0** |
| `grep -c '^## DEBT'` / `grep -c '^status: open'` | **75 / 1**（唯一 open = DEBT0075） |

## 反向传播清单（A3/A5）

| 文件 | 应被本批影响 | 现状 |
|---|---|---|
| `agate/tests/unit/test_tag0051_self_gate.py` | 是 | 已改 ✓ |
| `SELF-GATE.md` | 是 | 已改（口径 + 3 类限定 + 指 DEBT0075）✓ |
| `CHANGELOG.md` | 是 | 已改（收窄 + 3 类 + 指 DEBT0075）✓ |
| `agate-workspace/debt/tech-debt.md` | 是 | DEBT0073 关单收窄 + DEBT0075 新登记 ✓ |
| `AGENTS.md:134` | 是 | 已正确，无需改 ✓ |
| `agate/scripts/README.md` / `test_selfgate_trailer_integrity.py` | 否（hook 未变 / 已真同源）| 未改 ✓ |

**结论：approved。** MISALIGNED 0；无 NEEDS_HUMAN_REVIEW。
