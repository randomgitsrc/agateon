---
review_date: 2026-10-10
reviewer: protocol-alignment-review
round: r2
change_summary: r1 复审——清账+债务清欠批（新增 SELF-GATE 轻量档；DEBT0060/0061/0062 关单 + DEBT0064 另立；check-obligations R 判据收窄；obligations.yaml 去重复键）
files_changed:
  - CHANGELOG.md
  - SELF-GATE.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate-workspace/tasks/active-tasks.md
  - agate/LIMITATIONS.md
  - agate/rules/obligations.yaml
  - agate/scripts/README.md
  - agate/scripts/check-obligations.py
  - agate/tests/unit/test_tag0050_obligations.py
---

# 协议-脚本对齐审查（TRIAGE-r2）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（LIMITATIONS 新增 bullet 3「含协议本体 → 用**当前**协议回放」与 `agate-ci-verify.py` 实测不符——实测 note = `回放基准 <base> 的 agate/`） |
| A2 | 脚本→文档对齐 | **MISALIGNED（minor）**（`warnings` 仍死代码；obligations.yaml 头部字段表仍缺 `review_output`；README 退出码列仍未列新增 ERROR 因） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（LIMITATIONS 已改，但 `tech-debt.md` DEBT0060 note 与 `CHANGELOG` ① 未同步 → 三处对同一事实说法不一；CHANGELOG ② 未同步 T3；`AGENTS.md` 轴 C 未随轻量档更新；P4-implementation-G1.md DESIGN_GAP 仍未标闭合） |
| A4 | 测试覆盖 | **ALIGNED**（`test_bdd_43` 已改写；实跑全量 1 failed 环境性 + 2909 passed + 3 skipped） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **空清单**：本次 r2 修正**未新增**既有用例转红；实跑仅 1 条环境性 failed |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（CHANGELOG 的 DEBT0060/0061 描述与 tech-debt/LIMITATIONS 相矛盾；轻量档未在 AGENTS.md 轴 C 反映） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9 锚点 keywords 未变，CHECK 9 PASS） |
| A7 | 设计原则一致性 | **ALIGNED**（无相关 ADR；轻量档属评审策略细化，其跨文件一致性问题归 A3/A5） |
| A8 | 声称-命令绑定 | **MISALIGNED**（「7 个 PR / 12+ 处」仍在 roadmap/SELF-GATE 且无命令；「6 个旋钮中 5 个无消费」引 RM-AG0071 **已撤回**的结论；CHANGELOG「12 条」仍在） |

**总判定：仍不可 commit**——r1 的 **BLOCKER 已清除**，但出现「只改了主文件、未同步派生物」的成批不一致（A3/A5）与 A8 未兑现。

---

## r1 发现逐条核实结论

| r1 项 | 用户声称的改正 | 独立核实 | 结论 |
|---|---|---|---|
| **BLOCKER A1-1**（5 处重复键） | 删除 5 条重复 | 严格解析器（自建 dup 检测 SafeLoader）：**NO duplicate keys**；`review_output:` 行数 = **12**（30 R / 12 有指针） | ✅ **已修** |
| A1-2/A5（LIMITATIONS 不实） | 按实测重写四条 | LIMITATIONS **已重写**（bullet 2/4 现符）；**但 bullet 3 仍不准**，且 tech-debt/CHANGELOG 未同步 | ⚠️ **部分修** |
| A1-3（DEBT0061 漏 T3） | 关单注改写 + 另立 DEBT0064 | tech-debt 关单注**已改写**（T3 → DEBT0064）✅；**但 closure_note 自相矛盾**（见下）；CHANGELOG ② 未同步 | ⚠️ **部分修** |
| A3（roadmap 轻量档悬空） | 真正落地轻量档 + 改措辞 | SELF-GATE **已新增轻量档节** ✅；roadmap 措辞已改 ✅；**但 AGENTS.md 轴 C 未同步** ⇒ 新冲突 | ⚠️ **部分修** |
| A2（stale 注释/README） | 改注释 + README | `_check_review_output` 注释 ✅、README 描述列 ✅；**字段表/退出码列/死代码未处理** | ⚠️ **部分修** |
| A8（数字） | 改可核指代 | **未改**——`7 个 PR/12+ 处` 仍在 roadmap.md:11 + SELF-GATE.md:47；CHANGELOG 仍「12 条」 | ❌ **未修** |

---

## 逐项审查

### A1: 文档→脚本对齐

#### A1-1：LIMITATIONS 新增 bullet 3「用当前协议回放」与实现不符

**文档**（`agate/LIMITATIONS.md:143-144`）：
> - 仓库含协议本体（本仓即此类）→ 用**当前**协议回放 ⇒ 对「按当时协议书写」的历史提交可能 **误判或漏判**；

**脚本实测**（在 `/tmp/opencode` 副本上直接调 `_resolve_protocol(repo, None, base)`，protocol-body 分支）：
```
base= 397a88cd  HEAD= 032f6b2c  merge-base= 397a88cd
protocol_root= /tmp/agate-proto-.../agate
note= 回放基准 397a88cd 的 agate/
```

**语义**：实现取的是 **`merge-base(base, HEAD)`（= 回放基准 `base`）处的 `agate/`**（`agate-ci-verify.py:209-216`；docstring `:22-25` 明确「回放基准 base 处的 agate/」），**不是 HEAD/当前协议**。该函数 `:26-29` 之所以改用 `base` 而不用 `merge-base HEAD origin/*`，正是**为了用旧协议**（避免用刚合并的新协议回放历史提交）。⇒ bullet 3 的「用**当前**协议」既不符代码，也与该函数的设计意图相反。

**结论**：MISALIGNED（措辞级，实践影响有限——「非逐提交」这一要点仍成立）。
**建议**：把 bullet 3 的「用当前协议回放」改为「用**回放基准 `base` 处**的协议回放（即本区间之前的协议）」。

#### A1-2（重点复核）：12 条 `review_output` 取值——r1 结论维持

取值逐条对应关系未变（r1 A1-4 已核），且本次去重后 `review_output` 行数 = 12、`_evaluate` 判据未变。**ALIGNED**。

#### A1-3（重点复核）：判据收窄的安全性——r1 结论维持

`P6.5` 仍不会被 `P6-` 误匹配（`startswith` 语义未变）；registry 协议自有、`check-obligations.py` 不在 hook/CI 路径（`grep .github/` 空）。**ALIGNED**（残余静默通道同 r1，未变化）。

---

### A2: 脚本→文档对齐（部分修）

1. `_check_review_output` 注释已改（`:229` → 「缺 review_output 的处置见 `_evaluate`（DEBT0062…）」）✅
2. `agate/scripts/README.md:94` 描述列已补「R 义务的 `review_output`：仅对 P1/P2/P4 判 ERROR」✅
3. **残留**：
   - `agate/rules/obligations.yaml:14-23` 头部字段表**仍只列** `id/phase/statement/anchor/disposition/script/evidence`——**缺 `review_output`**（r1 A2-3 未处理）。
   - README 的**退出码列**仍只写「1=不通过（无归宿项 / M 类占比低于基线）」——未列新增的「P1/P2/P4 的 R 缺 `review_output`」这一 ERROR 因。
   - `_evaluate` 的 `warnings`（`:251`）仍**无任何 `warnings.append`** ⇒ 恒空，`main()` 的 `for warn in warnings`（`:357-358`）为死代码。

**结论**：MISALIGNED（minor，不阻断语义）。
**建议**：字段表补 `review_output`；README 退出码列补新 ERROR 因；删除 `warnings` 死代码（或保留但在 README 说明其现为空）。

---

### A3: 一致性连锁 + 反向传播（未同步派生物）

#### A3-1（HIGH）：LIMITATIONS 已改，`tech-debt.md` 与 `CHANGELOG` 未同步 → 三处对同一事实说法不一

| 位置 | 对「未写 `.agate-version`」的描述 |
|---|---|
| `agate/LIMITATIONS.md:141-142`（已改） | 「仓库**未写** `.agate-version` 且**不含**协议本体 → **直接 FAIL**」 |
| `tech-debt.md:2466`（**未改**） | 「仓库未写 `.agate-version` ⇒ **用当前协议回放**」 |
| `CHANGELOG.md:145-146`（**未改**） | 「未写 `.agate-version` 的仓库**按当前协议回放**，可能误判/漏判」 |

⇒ 用户只把 LIMITATIONS 改对了，**两处「派生物」（tech-debt 关单注、CHANGELOG）仍保留 r1 判为不实的措辞**，且**与已改的 LIMITATIONS 直接矛盾**（FAIL vs 用当前协议回放）。这是典型的反向传播未做全。

#### A3-2（HIGH）：`CHANGELOG` ② 与 `tech-debt.md` 对 DEBT0061 说法不一

- `tech-debt.md`（已改）：「**T3**（`strict_verdict_line_in_prose`）**全仓 0 消费方** ⇒ 该条承诺不成立，另立 DEBT0064」
- `CHANGELOG.md:148-150`（**未改**）：「T1… T2… T4… 真正无消费方的是**契约快照的 `traps`/`downgrade` 键本身**」——**完全没提 T3**，仍维持「原诊断不成立」的口径。

⇒ CHANGELOG 与 tech-debt 相互矛盾。

#### A3-3（HIGH）：`AGENTS.md` 轴 C 未随轻量档更新 → 新冲突

- `SELF-GATE.md:37-54`（新增轻量档）：「纯措辞/错别字/注释/纯格式 ⇒ **不派独立评审**」。
- `AGENTS.md:25`（**未改**，`git diff --stat AGENTS.md` 为空）：轴 C「**碰 SELF-GATE 触发面 → 须独立评审**」。
- `SELF-GATE.md:19-27` 的**触发面**明确**包含 `agate/*.md` 与 `agate/**/*.md`**——「纯措辞」改动的落点正在其中。

⇒ 两份权威文件对**同一类改动**（改 agate/*.md 里的一个错别字）给出**相反**结论。roadmap 范围节（`:22-24`）自己也写「⚠️ 碰判据/脚本/契约的改动仍须独立评审（`AGENTS.md` 轴 C：评审义务由 SELF-GATE 触发面决定）」——但**触发面是文件式、轻量档是语义式**，二者边界不同，roadmap 引轴 C 却用它支撑一个轴 C 不承认的例外。

**结论**：MISALIGNED。
**建议**：把轴 C 的「触发面 → 须评审」**改为语义式**（「碰判据/脚本/契约/数据面 → 须独立评审；纯措辞/注释走 SELF-GATE 轻量档」），使 `AGENTS.md` 与 `SELF-GATE.md` 同源；否则两文件将持续互相矛盾。

#### A3-4（同 r1 未处理）：轻量档与 `检查清单` 未互指

`SELF-GATE.md:56-62` 的检查清单 step 2「**派发 protocol-alignment-review subagent**」为**无条件**，未指「除非走轻量档」；触发条件 `:3-5` 仍写「必须走本流程 … + LLM 语义审查」。轻量档节未声明它是这两处的例外。→ 轻度不一致。

#### A3-5（同 r1 未处理）：`P4-implementation-G1.md` 的 DESIGN_GAP 仍未标闭合

TAG0050 的 `[DESIGN_GAP: A4 的 review_output 缺失判 WARNING（设计原文为 ERROR）]` 已被 DEBT0062 消解，但该 frozen 任务文件未加「已由 DEBT0062 闭合」注（r1 已提，本次未处理）。

---

### A4: 测试覆盖

- `test_tag0050_obligations.py::test_bdd_43_r_without_review_output_errors` 未变（r1 已按新语义改写）。
- **实跑全量**（`/tmp/opencode/agateon-triage2`，`--reruns 1 -n auto`，CI 同口径）：
  ```
  1 failed, 2909 passed, 3 skipped, 1 rerun in 101.05s
  ```
  唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（`Unknown subcommand "agent" for "opencode debug"`，**本机 opencode CLI 漂移，环境性**）。

**结论**：ALIGNED。**不称「全绿」**——有 1 条环境性 failed。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单

**本次 r2 修正（去重、文档改写、轻量档）未使任何既有用例转红**（实跑全量仅 1 条环境性 failed）。夹具无新增/更新。→ **空清单**（显式）。

---

### A5: 下游影响 + 文档传播

- **对用户项目**：仍**无**破坏性变更（`check-obligations.py` 不在 hook/CI 路径；轻量档只影响 agate 自身维护流程）。
- **CHANGELOG**：与 tech-debt/LIMITATIONS 矛盾（见 A3-1/A3-2）——**未随关单注同步**。
- **AGENTS.md**：轴 C 未随轻量档同步（见 A3-3）。

**结论**：MISALIGNED。

---

### A6: 锚点表覆盖

CHECK 9 锚点 `["obligations.yaml","M 类占比","无归宿"]` 未变、字面存在，实跑 **CHECK 9 PASS**（consistency 0 ERROR）。**ALIGNED**。

---

### A7: 设计原则一致性

`agate/adr.md` 无 `obligations`/`review_output`/轻量档相关条目 ⇒ 无对应 ADR 可逐条核。轻量档属**评审策略细化**，其跨文件一致性问题归 A3/A5（非 ADR 违反）。**ALIGNED**。

---

### A8: 声称-命令绑定

| 声称（出处） | 命令 | 结论 |
|---|---|---|
| `0 ERROR`（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | ✅ rc=0，0 ERROR（432 冻结 WARNING） |
| `check-obligations 0 WARNING` | `AGATE_ROOT=./agate python3 agate/scripts/check-obligations.py` | ✅ rc=0，无 WARNING（M 56/121） |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ rc=0（含新 DEBT0064） |
| `roadmap 0 异常` | `<复现 _check_roadmap_done 列数判据>` | ✅ 0 行列数异常 |
| `ruff` | `ruff check check-obligations.py test_tag0050_obligations.py`（0.16.4） | ✅ rc=0 |
| `--strict-errors-only` 可用 | `check-protocol-consistency.py --strict-errors-only` | ✅ rc=0（轻量档命令有效） |
| 全量 pytest | `pytest agate/tests/ --reruns 1 -n auto` | ✅ **1 failed(环境) + 2909 passed + 3 skipped**（**非「2910 passed」**） |
| 「7 个 PR / 12+ 处」（roadmap:11；SELF-GATE:47） | （无命令） | ❌ **仍未改**；且 2026-10-09 评审文档实测 >25 个 |
| 「RM-AG0071 实测：6 个旋钮中 5 个[无消费]」（roadmap:16-17） | `sed -n '93p' roadmap.md`（RM-AG0071 正文） | ❌ **引 RM-AG0071 已撤回的结论**——其〔2026-09-29 重大复核更正〕「更正 C：『除 1 个外全部无消费』**不成立**——6 个旋钮里**至少 3 个有真实 gate 消费方**」 |
| CHANGELOG「补 `review_output`（12 条）」（:152） | `git diff` + `yaml` 遍历 | ❌ 不精确：去重后**真正新增 7 条**（另 5 条原已存在）；DEBT0062 注已写清「7 条」，CHANGELOG 未同步 |

**结论**：MISALIGNED——三处声称（「7 个 PR/12+ 处」「6 个旋钮中 5 个」「12 条」）**无法由命令支撑/与来源相矛盾**，按 A8 应修正或删除。**其中「6 个旋钮中 5 个」是本轮新引入的**（r1 未出现）。

---

## 重点结论（本轮 5 项验证）

1. **6 项是否真修**：BLOCKER（重复键）**真修** ✅；LIMITATIONS/DEBT0061/轻量档/A2 **只改了主文件、未同步派生物**（部分修）；A8 数字 **未修**。逐项证据见上表。
2. **重复键复核**：用自建 dup 检测 SafeLoader（非 `safe_load`）→ **NO duplicate keys**；`review_output:` 行数 = **12**。✅
3. **轻量档自洽性**：节内**自洽**（判定/做什么/不做什么/三条边界齐备；`--strict-errors-only` 与 `self-gate-skip:` 均与现有实现一致）。**确能省掉错别字体量的评审**（这正是其目的，内部无矛盾）。**但与 `AGENTS.md` 轴 C 冲突**（轴 C 未同步，见 A3-3）；与 `检查清单` step 2 未互指（A3-4）。
4. **DEBT0064 登记**：`check-debt.py` **rc=0** ✅；`status: open` / `task_id: null` / 判据可核（「接线 或 明确仅记录不判定」）✅。唯 DEBT0061 自身 `closure_note` 与 `impact` **自相矛盾**（A1-3 残留，见下）。
5. **A4b + A8 实跑数字**：`1 failed（环境性）+ 2909 passed + 3 skipped`；`0 ERROR` / `check-debt rc=0` / `roadmap 0 异常` / `check-obligations 0 WARNING` / `ruff rc=0` 均复现；「2910 passed」**未复现**。

### 额外发现（本轮新增）

**DEBT0061 内部自相矛盾**（`tech-debt.md`）：
- `impact` 字段：「「命中即拦」的承诺在 gate 侧**不成立**」
- `closure_note`：「…`traps`/`downgrade` 契约键为描述性…；**「命中即拦」的承诺由代码承载、成立**」

同一条目内两处结论相反。既然 T3 已被拆到 DEBT0064（其承诺不成立），`closure_note` 的「成立」应改为「T1/T2/T4 成立；T3 见 DEBT0064」。→ MISALIGNED。

---

## 是否可 commit

**不可 commit（NEEDS_FIX）**。r1 的 **BLOCKER 已清除**，但仍有下列 MISALIGNED：

| 优先级 | 项 | 修复方向 |
|---|---|---|
| HIGH | A3-1 LIMITATIONS 与 tech-debt/CHANGELOG 对 DEBT0060 说法不一 | 把 tech-debt DEBT0060 note、CHANGELOG ① 改成与已改 LIMITATIONS 一致（未写且不含本体 → FAIL） |
| HIGH | A3-2 CHANGELOG ② 未同步 T3/DEBT0064 | CHANGELOG ② 补 T3 拆分说明 |
| HIGH | A3-3 轻量档 vs AGENTS.md 轴 C | 把轴 C 改为语义式（判据/脚本/契约 → 须评审；纯措辞 → 轻量档） |
| HIGH | 额外发现 DEBT0061 closure_note 自相矛盾 | closure_note 改为「T1/T2/T4 成立；T3 见 DEBT0064」 |
| MED | A1-1 LIMITATIONS bullet 3「用当前协议回放」 | 改「用回放基准 `base` 处的协议」 |
| MED | A8 「7 个 PR/12+ 处」「6 个旋钮中 5 个」「12 条」 | 补命令或删；「6 个中 5 个」须改用 RM-AG0071 更正后的口径 |
| MED | A2 字段表/退出码列/死代码 | 补 `review_output`；README 退出码列补新因；处理 `warnings` 死代码 |
| LOW | A3-4 轻量档与检查清单互指；A3-5 P4-implementation-G1 DESIGN_GAP 标注 | 补指针 / 补闭合注 |

**ALIGNED 可直接保留**：A4（含实跑）、A4b（空清单）、A6（锚点）、A7（ADR）；A1-2/A1-3（取值与安全性）无缺陷。

修复 HIGH 后重派本角色复审即可 commit。
