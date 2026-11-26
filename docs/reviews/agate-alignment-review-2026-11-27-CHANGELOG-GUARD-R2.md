---
review_date: 2026-11-27
review_round: 2
reviewer: protocol-alignment-review (fresh context, 不预设上一轮)
reviewed_range: 746591da..43fbcf3b (origin/main..HEAD)
commits:
  - d3d16ab7 feat(changelog): 加「过程日志化」判据（RM-AG0117）
  - 43fbcf3b fix(changelog-quality): 修 5 个 BLOCKER
first_round_report: docs/reviews/agate-alignment-review-2026-11-27-CHANGELOG-GUARD.md
progress_log: docs/reviews/agate-alignment-2026-11-27-CHANGELOG-GUARD-02.progress.md
---

# 协议-脚本对齐审查（第二轮）— CHANGELOG 质量判据（RM-AG0117）

> 只读纪律：除本文与留痕文件外未修改仓库；未 commit / push / 改暂存区 / 改 git config。
> 实验在 `/tmp/r2a`…`/tmp/r2g`、`/tmp/e1`、`git archive HEAD` 副本、`git clone` 副本中进行，跑前跑后原仓 `git status` 一致。
> ⚠️ 审前工作区已有他人未提交改动（`README.md` / `README.zh-CN.md` / `agate.config.yaml` / `docs/research/*`，以及**删除 `agate/scripts/agate-changelog-quality.py`**）。非我所为；其中删除旧脚本与本次裁决直接相关（见 B-6）。

## 独立结论先说

第一轮的 5 个 BLOCKER，**4 个真闭合，1 个方向对但实现有洞**。但**修复本身引入了 1 个新 BLOCKER（B-6）**，且**上一轮的一个 MINOR 与一个 A4b 结论在本次修法下变成了必须处理的项**。

| 第一轮 BLOCKER | 作者声称 | 我的独立裁决 |
|---|---|---|
| B-1 一词绕过 | 整体移除 `_META_DISCUSSION` | ✅ **闭合**（12 个词实测全部仍 FIRE；旧脚本 11/11 全绕过）。但仍存在**阈值本身的边界**（口风改写可绕），判为**可接受**（理由见 A2） |
| B-2 误伤正当勘误 | 移出 `勘误` / `上一版(的\|写)` / `原先写` | ✅ **闭合**（3 组正当勘误全部 PASS），检出能力 5/5 未削弱。**代价**：通篇「教训+勘误」的真过程日志不再被拦（单类被阈值豁免）——须人工确认可接受 |
| B-3 已发布段硬阻断 | 两段分处置 exit 1 / exit 2 | ⚠️ **逻辑合理，但可被利用**：把痕迹写进新加一个 `## [x.y.z]` 版本节即只 exit 2 ⇒ 放行（端到端 rc=0 实测）。且**CI 侧（CHECK 17）完全没修**——见 B-6 |
| B-4 改名规避登记面 | 改名回 `check-*.py` + 进锚点 + 改 `test_bdd_23` | ⚠️ **方向正当，实现有洞**：改测试**是正当修正**（原文确实是「须已登记」），但新实现用**子串匹配**判登记 ⇒ 一行注释即可绕（真门禁 SG.6 不会）。见 A6 |
| B-5 README「兜底」矛盾 | 统一为「不是可靠兜底」 | ✅ **闭合**（`agate/scripts/README.md:73` 已改，与 CHANGELOG 一致）。但「由 CI CHECK 17 兜底」在 CHANGELOG:41-42 仍在，见 A8 |

**总判定：MISALIGNED**（B-6 为新 BLOCKER；B-3 可利用路径 + A6 子串漏洞为 MINOR~BLOCKER 之间，按「真 MISALIGNED 一律修完再复审」处理）。

## A1–A8 汇总表

| # | 审查项 | 结论 | 一句话 |
|---|--------|------|--------|
| A1 | 文档→脚本对齐 | **MISALIGNED** | CHANGELOG 说「6 类含自我勘误」——`勘误` 已移出词表，文档未同步；「21/25 处」实测为 21/**26** |
| A2 | 脚本→文档对齐 | **MISALIGNED** | 脚本 docstring/用法行仍写旧脚本名 `agate-changelog-quality.py`（3 处） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** | CHECK 17 仍指向**旧脚本** ⇒ CI 侧 B-1/B-2/B-3 修复全部未生效（B-6） |
| A4 | 测试覆盖 | **MISALIGNED** | 16 passed 属实；但缺 2z2 行为级测试、缺 CHECK 17 测试；M-2 变异仍可绕过 |
| A4b | 闭合后既有测试转红 + 夹具 | **非空**：`test_bdd_23_no_new_check_star_script_added`（必须改）；夹具**无需**更新 | 第一轮「空清单」结论在本次修法下失效 |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** | B-3 胶着：已发布段只提示合理，但可利用；且 CI 侧没修 |
| A6 | 锚点表覆盖 | **MISALIGNED** | 改名+登记**正确**；但 `test_bdd_23` 新实现用子串判登记，**一行注释即绕** |
| A7 | 设计原则一致性 | **ALIGNED** | ADR-014 判据单源成立（新脚本无词表副本）；ADR-015 成本面因 B-2/B-3 已收窄，比第一轮改善 |
| A8 | 声称-命令绑定 | **MISALIGNED** | 「3072」自洽可复现✅、「16/18/5-5」✅；「21/25 处」「145 行」❌ |

## 逐项详情

### A1：文档→脚本对齐 — MISALIGNED

**(a) 「6 类含自我勘误」已过时。** `CHANGELOG.md:53` 写「（第一人称、评审轮次、变异实验、`N passed`、**自我勘误**等 6 类）」；
但 `check-changelog-quality.py:62-68` 已把 `勘误` 移出 A6（B-2 修复），且 `:181` 的 `_GUIDANCE` 仍列「自我勘误」。
⇒ 读者/作者按文档写「自我勘误」会**以为会被拦，实际不会**（`勘误` 现在完全不命中）。属**修了代码没同步文档**。

**(b) 「21 / 25 处」数字漂移。** 实测（用**出厂脚本**，非我构造的词表）：

| 段 | 行数 | 实测 total / 类 | 文档声称 |
|---|---|---|---|
| v0.78.0 | 248 | **21 / 3** | 21 / 3 ✅ |
| v0.77.0 | 191 | **26 / 4** | 25 / 3 ❌ |

原因：A7 去掉 `上一版(的|写)`/`原先写` 后改成 `我(?:原先|本来|一开始)` 等，**v0.77.0 段反而多命中 1 处 `我原先`、多 1 类**。
⇒ 作者写「检出能力未削弱」（这句成立，26>25）但**同一段里引用的旧数字没跟着更新**。
`CHANGELOG.md:50`、`check-changelog-quality.py:11`、`pre-commit-gate.py:1203`、`test_check_changelog_quality.py:6` 四处都写 21/25（后者写 158/121，见 M-1）。

**修法**：把四处数字统一改成可复现值「248 行命中 21 处 / 191 行命中 26 处」；`CHANGELOG.md:53` 与 `check-changelog-quality.py:181` 的「自我勘误」删掉（或改成「第一版写错了」）。

### A2：脚本→文档对齐 — MISALIGNED

`check-changelog-quality.py` 自身仍残留旧名 3 处：

| 行 | 内容 |
|---|---|
| `:31` | `python3 agate-changelog-quality.py [CHANGELOG.md]` |
| `:32` | `python3 agate-changelog-quality.py --warn-only [CHANGELOG.md]` |
| `:183` | `"    python3 agate/scripts/agate-changelog-quality.py CHANGELOG.md\n"` ← **这是 stderr 自证命令**，用户会照抄 |

第三处最严重：**判据失败时打印给用户的「自证命令」指向一个即将被删除的脚本**。
（第一轮曾指出「旧脚本名残留 4 处已修」——那是**另一个** 4 处，本轮改名又引入了新的 3 处。属**同一类错误第二次发生**。）

**修法**：三处改成 `check-changelog-quality.py`（`:183` 改成 `agate/scripts/check-changelog-quality.py`）。
建议加一条测试：`assert "agate-changelog-quality" not in script_text`（防第三次）。

### A3：一致性连锁 + 反向传播 — MISALIGNED（**新 BLOCKER B-6**）

#### B-6（新，BLOCKER）：`check-protocol-consistency.py` 的 CHECK 17 仍调用**旧脚本**，两个状态都是错的

`git ls-tree HEAD agate/scripts/` **同时**存在两个脚本：
```
agate-changelog-quality.py      (旧, 200 行, d3d16ab7 引入)
check-changelog-quality.py      (新, 232 行, 43fbcf3b 引入)
```
而 `check-protocol-consistency.py` 的 CHECK 17 停在旧脚本上：

| 行 | 内容 |
|---|---|
| `:27` | `CHECK 17 …（RM-AG0117；判据单源 = agate-changelog-quality.py）` |
| `:1461` | `# 判据本体在 agate-changelog-quality.py（**单源**，…` |
| `:1468` | `script = root / "agate" / "scripts" / "agate-changelog-quality.py"` ← **实际调用** |
| `:1481` | `"CHANGELOG 条目疑似「工作过程记录」（详见 agate-changelog-quality.py）"` |

**实测两种状态（干净的 `git archive HEAD` 副本）**：

```
场景：Unreleased 干净 + 已发布段是过程日志（= 第一轮 B-3 的原场景）

状态 A：HEAD 原样（旧脚本在）
  pre-commit 2z2（新脚本）→ rc=2（只提示）✅ 作者声称的 B-3 修复在此生效
  CHECK 17（旧脚本）      → ❌ FAIL，consistency rc=1   ← B-3 修复在 CI 侧**完全没生效**

状态 B：删掉旧脚本（= 作者工作区当前 `D` 项）
  CHECK 17 → ✅ PASS，即使 Unreleased 塞极端坏条目（total=5/cats=5）也 PASS
  原因：`:1470 if not script.is_file(): return` —— **静默跳过，真空通过**
```

⇒ **留旧脚本 = CI 用带 B-1/B-2/B-3 全部缺陷的旧判据；删旧脚本 = CI 真空。**
两种状态都使 `CHANGELOG.md:41-42`「由 CI **CHECK 17** 兜底」与 `agate/scripts/README.md:73`「CHECK 17 作补充检查」**不成立**。

**这也解释了为什么上一轮的 A4b 判「空清单」而本轮不为空**：上一轮脚本名是 `agate-*`，CHECK 17 调它是对的；本轮改名后**忘了改 CHECK 17 的路径**，于是产生了一个「新脚本被 2z2 用、旧脚本被 CHECK 17 用」的双轨状态。
`test_check_changelog_quality.py` 与 `test_release_gate.py` 都绿，因为它们只测新脚本 / 只测登记面，**没有任何测试断言 CHECK 17 用的是哪个脚本**（见 A4-问题 2）。

**修法**（按序）：
1. `check-protocol-consistency.py:1468` 改为 `check-changelog-quality.py`；`:27`/`:1461`/`:1481` 三处措辞同步。
2. **删掉旧脚本 `agate/scripts/agate-changelog-quality.py`**（作者工作区已删，但**尚未提交**——`git status` 显示 `D` 且未 staged）。
3. CHECK 17 改为判 `returncode != 0`（而非 `== 1`），或至少把 `== 2` 也当「有发现」输出为 NOTE——否则 B-3 的 exit 2 在 CI 侧等于**静默**。
4. **补一条测试**：断言 CHECK 17 调用的脚本相对路径 == `check-changelog-quality.py`，且该文件存在（防「路径写错 → 静默 fail-open」这类。当前 `:1470` 的 `if not script.is_file(): return` 是**静默**的，属 fail-open）。

> 附带：`agate/scripts/agate-changelog-quality.py` 与 `check-changelog-quality.py` **词表已分叉**（B-2 的 A6/A7 只改了后者）。
> 两份判据并存 = 直接违反 ADR-014「判据单一权威源」。这也使 `agate/scripts/README.md:73` 的「判据单源」自述失真。

### A4：测试覆盖 — MISALIGNED

**实跑（本机）**：
```
test_check_changelog_quality.py ................. 16 passed in 0.15s   ✅ 与作者声称一致
test_release_gate.py ............................ 18 passed in 1.73s   ✅ 与作者声称一致
test_pre_commit_hook.py ......................... 69 passed in 51.55s
5 个相邻文件（doc_sweep/consistency/t43/protocol_alignment/tag0050） 79 passed
ruff 0.16.4（5 文件）............................. All checks passed
```

**问题 1（沿用第一轮 M-2，未修）：挂载点守护测试测不出「移进循环体」。**
`test_check_changelog_quality.py:128-139` 用 `mount > loop`（行号先后）。
变异实测：把 2z2 整块缩进 +4 移进 `for state_file in state_files:` 循环体 → 测试**仍 PASS**。
它守护的正是注释 `pre-commit-gate.py:1204-1205` 自称「本仓已记过一次放错位置的事故」的那个缺陷。
**修法**：断言缩进相等——`indent(2z2 注释行) == indent(for state_file 行)`。

**问题 2（新）：没有任何测试断言 CHECK 17 调用的是哪个脚本。**
`grep -rn "CHECK 17\|CHECK17\|check_changelog_quality" agate/tests/` → 仅命中测试文件名，**零测试**。
这是 B-6 能存在而全绿的直接原因。
**修法**：`assert check-protocol-consistency.py 里 CHECK 17 段的 script 路径 == "check-changelog-quality.py"`，并断言两文件名不得同时存在（防双份）。

**问题 3（沿用第一轮 M-5，未修）：2z2 无行为级测试。**
`grep -rn "changelog-quality\|CHANGELOG-QUALITY" agate/tests/integration/` → **0 命中**。
「hotfix 无 `.state.yaml` 时 2z2 真的阻断」这条主战场结论仍无 pytest 守护（我用手工 mktemp 仓库验证成立）。

**问题 4（新）：B-3 的 exit 2 有测试（`test_released_section_only_warns_never_blocks`），但只测了「直接调脚本」，没测「pre-commit 端到端 rc=0」。** 端到端仍成立（我实测 rc=0），属覆盖偏好问题，非缺陷。

### A4b：闭合后既有测试转红 + 夹具更新清单 — **非空**

**转红的既有用例（1 个）**：

| 用例 | 为何转红 | 处置 |
|---|---|---|
| `test_release_gate.py::test_bdd_23_no_new_check_star_script_added` | 新增 `check-changelog-quality.py` 命中 `check-*.py` glob，原断言「不得新增」直接 FAIL | **必须改**（作者已改，方向正当，实现有洞——见 A6） |

**实测证据**（用 `origin/main` 的**原版**测试跑 HEAD 的 scripts 目录）：
```
FAILED test_bdd_23_no_new_check_star_script_added
  AssertionError: BDD-23：新增了 `agate/scripts/check-*.py`（落点①）——本方案应落 agate-*.py（支②）；
                  新增：['check-changelog-quality.py']
```

**需更新的夹具：无**（实测）。依据：`test_pre_commit_hook.py` 69 passed、5 个相邻文件 79 passed、登记面 80 passed；全仓 `grep -rn 'glob("check-\*' agate/tests/` 仅 `test_release_gate.py:367` 一处，无夹具硬编码脚本清单或旧脚本名。

> **对第一轮 A4b「空清单」的独立判断**：那个结论**在当时成立**（脚本名 `agate-*`，不匹配 glob）。
> 但它**没有预见** B-4 的修法（改回 `check-*`）必然导致本用例转红 ⇒ 两轮结论不矛盾，是**修法变更导致清单变更**。
> 这也说明第一轮 A4b 的判据「有无转红」不能只看当前状态，还应看「若按建议修，会不会转红」。

### A5：下游影响 + 文档传播 — MISALIGNED

**B-3 的两段分处置：逻辑合理，但留下一条可利用路径。**

**(a) 实测符合声称**：
```
A 痕迹在 [Unreleased]                → rc=1  ✅
B 无 [Unreleased]，痕迹在 ## [0.84.0]  → rc=2  ⚠️
C [Unreleased] 空，痕迹在 ## [0.84.0]   → rc=2  ⚠️
D 痕迹在已发布段 ## [0.83.4]           → rc=2  ✅ 设计如此
```

**(b) 只提示是否合理？——合理，但当前「提示」的判定面被一个**作者可控的动作**绕开。**
关键在 `target_sections()`（`:116-122`）的定义：**「最新一个已发布段」= 首个非 `[Unreleased]` 的 `## [` 段**——它**不校验该版本是否真的发布过**。
于是作者只要**新写一个 `## [0.84.0] - 2026-12-01` 标题**（还没发布的版本），痕迹就自动落进「已发布段」，降级为 exit 2。

**端到端实测（mktemp 仓库 + 真 `pre-commit-gate.py`，hotfix 无 `.state.yaml`）**：
```
只暂存含 ## [0.84.0] ... 痕迹 的 CHANGELOG.md
→ NOTE CHANGELOG-QUALITY: 最新**已发布**段也含过程痕迹 … ⇒ **不阻断**，仅提示
→ gate rc=0     ← 放行
```

**(c) 这个动作显眼吗？——显眼，但不是 pre-commit 能看见的显眼。**
- 新增一个带版本号+日期的 `## [` 标题是**结构性改动**，code review 可见。
- 它立刻会撞 **CHECK 7**（badge 未同步：`❌ FAIL README version badge v0.83.4 != CHANGELOG 最新已发布版本 v0.84.0`）与 **CHECK 13**（`❌ FAIL CHANGELOG 最新版本 [0.84.0] 在 agate/UPGRADING.md §3 无对应章节`）——**实测两项都红**。
- **但**：这两道都在 `check-protocol-consistency.py` 里，而**纯 docs 提交时 `consistency` job fast-pass**（本项目自陈、第一轮已核）；`docs-check` 不在 required check 里。
- ⇒ **在 pre-commit 这个「主要强制力」层面，确实没有任何东西拦它。**

**(d) 我的判断：这是 B-3 修复的合理代价，但应显式记录，不应留成暗口。**
建议（保持「已发布段不阻断」不变）：
1. 把 `target_sections()` 的「已发布段」判定加上**校验**：该版本号是否 ≤ 最近 git tag / 是否在 `agate/UPGRADING.md` §3 有章节。没有 ⇒ **按 Unreleased 处理（exit 1）**。这样「新写一个版本节」就不再是降级通道。
2. 若不做校验，至少在 exit 2 的提示里加一句：「**若该段其实尚未发布，请改为写在 `[Unreleased]` 下——把新内容包进一个新版本标题不改变判据**」，让绕行变成显式违规而非无心之失。
3. CHECK 17 侧把 `== 2` 也输出为 WARNING（当前只处理 `== 1`，exit 2 在 CI 里是**完全静默**的）。

**另外（B-5 相关，CHANGELOG 仍自相矛盾）**：`CHANGELOG.md:41-42` 仍写「并由 CI **CHECK 17** 兜底」，
而同一批次 `agate/scripts/README.md:73` 已改成「CHECK 17 作补充检查，但**不是可靠兜底**」。
⇒ B-5 只修了 README 一侧，**CHANGELOG 一侧仍写「兜底」**。且结合 B-6，该「兜底」在任一状态下都不成立。

### A6：锚点表覆盖 — MISALIGNED

#### B-4 独立裁决（你点名要的）

**(a) TAG0051 需求原文怎么写的？** 我直接读 `agate-workspace/tasks/TAG0051-release-decoupling/P1-requirements.md`（BDD-23，约 289-300 行）：

> - **Given** 实现把发布门落为三种互斥落点之一：① 新增/改名 `agate/scripts/check-*.py`；② 落为 `agate/scripts/agate-*.py`（如扩展现有 `agate-release.py`）；③ `.github/workflows/release.yml` 内新增步（**不**新增 `agate/scripts/` 文件）
> - **Then** …① 落 `check-*.py`：该脚本**须已登记**（进 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表或 `GATE_SCRIPT_EXEMPT` 豁免集）使 SG.6 通过（未登记则 SG.6 红，判 FAIL）；② 落 `agate-*.py`：SG.6 与 CHECK9-coverage 对该新文件**零触发**…判 PASS；③ …

⇒ **作者对原文的引用逐字准确。** 原文确实是「**须已登记**」而非「**不许新增**」。

**(b) 改这个测试是正当修正还是为通过而放宽判据？—— 明确结论：`test_bdd_23` 的修改是正当修正**

理由三条，逐条可验证：
1. **原断言与需求原文不符**：原文写「须已登记使 SG.6 通过」，原测试断言「不得新增」。这两句不等价——前者允许新增（带登记），后者禁止新增。原测试**比需求更严**，且严的方向是**错的**（它把 TAG0051 这个任务自己的落点选择 ② 固化成全仓规则）。
2. **原断言与仓库既有规范冲突**：`agate/scripts/README.md`「新增脚本登记面」明写「**承载 gate 判定逻辑 → 命名 `check-*.py` 并登记 `SCRIPT_ALIGNMENT_ANCHORS`**」。原测试会把这个规范**判成违规**。
3. **真实门禁不依赖这个测试**：SG.6（`test_sg_6_check9_anchor_table_covers_all_gate_scripts`）与 CHECK9-coverage 已经用 `uncovered_gate_scripts()` 判「须已登记」。`test_bdd_23` 的这条分支是**冗余的**，改它不降低任何真实门禁的强度。

**关键区分**：如果作者是**删掉/弱化**「须已登记」这个要求，那就是「为通过而放宽」；但他是把判据**从「禁止新增」改成「新增须登记」**——这是**向需求原文靠拢**，不是放宽。

**(c) 修改后它还能拦住「新增未登记的 check-*.py」吗？——能，但**有一个绕过口**（新 MINOR）

变异验证（`git clone` 副本，每次 `git checkout` 复位）：

| 变异 | `test_bdd_23`（新） | SG.6（真门禁） | 判读 |
|---|---|---|---|
| M1 新增未登记 `check-mutant-probe.py` | **FAIL** ✅ | **FAIL** ✅ | 能拦 |
| M2 登记进 `SCRIPT_ALIGNMENT_ANCHORS` | PASS ✅ | PASS ✅ | 正确放行 |
| M4 名字只出现在**文件末尾注释** | **PASS** ❌ | **FAIL** ✅ | **能绕过** |
| M6 名字只出现在 `GATE_SCRIPT_EXEMPT = {` 的**同行注释** | **PASS** ❌ | **FAIL** ✅ | **能绕过** |
| M8 名字出现在豁免集闭合 `}` **之后**的注释 | **PASS** ❌ | **FAIL** ✅ | **能绕过** |
| M7 名字出现在 `GATE_SCRIPT_EXEMPT` **之前**的注释 | FAIL ✅ | FAIL ✅ | 不能绕过（偶然） |

**根因**（`test_release_gate.py:389-395`）：
```python
exempt_m = _re.search(r"GATE_SCRIPT_EXEMPT\s*=\s*[\{\(\[]", cpc)
unregistered = [
    n for n in added
    if n not in anchors and (exempt_m is None or n not in cpc[exempt_m.start():])
]
```
`cpc[exempt_m.start():]` 是「从豁免集起点**到文件末尾**」的整段子串，不是「豁免集成员集合」。
⇒ 在文件里豁免集之后的**任何位置**（含注释）写一遍脚本名，就满足 `n in ...`。

**这与 DEBT0046 已修掉的缺陷完全同型**：SG.6 的 docstring（`test_protocol_alignment_review.py`）自己写着
> 「旧版断言 `name in consistency_text` 是**子串**判定……在 `check-protocol-consistency.py` 里写一行**注释**提及脚本名即可让本测试变绿」

——作者把**同型缺陷**从 SG.6 搬进了 `test_bdd_23`。

**修法（推荐：不要自己实现，直接复用单一判据）**：
```python
# 与 SG.6 / CHECK9-coverage 共用同一判据（ADR-014 单源）
spec = importlib.util.spec_from_file_location("cpc", agate_scripts / "check-protocol-consistency.py")
cpc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cpc)
unregistered = [f"agate/scripts/{n}" for n in added
                if f"agate/scripts/{n}" in cpc.uncovered_gate_scripts(H.REPO_ROOT)]
```
这样两处判据不可能再分叉，M4/M6/M8 三个绕过口一并消失。

**(d) 如果不该改这个测试，正确做法是什么？**
**该改**（结论见 (b)），所以这一问的正解是：改，但**按需求原文精确实现**——
- 不要自己写 `exempt_m` 子串匹配，**复用 `uncovered_gate_scripts()`**（同上）。
- 或者更彻底：**删掉本用例的这条分支**，因为 SG.6 已经用单一判据覆盖了同一事实；保留一个弱化副本只会制造「测试绿而门禁红」的 DEBT0046 型矛盾。若要保留，加一句 docstring 说明「本用例是 SG.6 的冗余快速反馈，判据必须与其同源」。

#### 锚点表本身：✅ 正确
```
SCRIPT_ALIGNMENT_ANCHORS 新增条目（check-protocol-consistency.py:858-863）：
  script   = agate/scripts/check-changelog-quality.py
  keywords = ["A2-review-rounds", "FIRE_MIN_CATEGORIES", "commit message"]
实测三个 keyword 在脚本中字面出现次数：1 / 3 / 2  ✅
CHECK 9 → ✅ PASS（无 CHECK9-coverage WARNING）
```
这个修法（改回 `check-*` + 登记锚点）**完全正确**，比第一轮建议的「保留 `agate-*` 只加锚点」更符合 `agate/scripts/README.md` 的规范。

### A7：设计原则一致性 — ALIGNED

| ADR | 关系 | 判断 |
|---|---|---|
| **ADR-014 判据单一权威源** | 新脚本无词表副本，CHECK 17 只调用不复制 | ⚠️ **部分成立**：单看新脚本 ✅；但**旧脚本仍在 HEAD**、词表已分叉（A6/B-6）⇒ 现状违反 ADR-014。删旧脚本后即成立 |
| **ADR-015 门禁只用于会导致后续错误决策的错误** | B-2/B-3 修完后误伤面大幅收窄（实测 3 组正当勘误全部 PASS，存量历史快照不再硬阻断） | ✅ **比第一轮改善**：第一轮判 NEEDS_HUMAN_REVIEW 的两个理由（误伤、「升级后第一次提交被卡」）都已消除 |
| `AGENTS.md`「新增判据 = 给所有使用者加成本：先答它拦下几个真缺陷」 | 已答，且本判据**自身**在本次提交里就拦下了一次（`3df9c9e8^` 的 144 行段 total=14/cats=5 FIRE） | ✅ 实例成立（且是自我验证，价值明确） |

**唯一仍需人工确认**：B-2 的代价（通篇「教训+勘误」的真过程日志不再拦）是否可接受。见 A2 的「阈值边界」。

### A8：声称-命令绑定 — MISALIGNED

逐条给产出命令（全部本机实跑）：

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | `test_check_changelog_quality.py` **16 passed**（`43fbcf3b` commit msg） | `python3 -m pytest agate/tests/unit/test_check_changelog_quality.py -q` | ✅ **= 16 passed** |
| 2 | `test_release_gate.py` **18 passed** | `python3 -m pytest agate/tests/unit/test_release_gate.py -q` | ✅ **= 18 passed** |
| 3 | 语料复验 **5/5**（v0.81.0/v0.83.3 放行；v0.78.0/v0.77.0/旧版 145 行 FIRE） | `python3 /tmp/r2a/corpus2.py`（见留痕 E-C） | ✅ **5/5 全部符合**（v0.77.0 实测 26/4 而非 25/3，但仍 FIRE；旧版段 144 行而非 145） |
| 4 | 全量 **3072 passed + 2 failed**（缺 CLI） | `python3 -m pytest --collect-only -q agate/tests/` → **3077**；`pytest -q -k "opencode or codex"` → **2 failed** | ✅ **自洽**：3077 − 2 failed − 3 skipped = **3072**。3 个 skip 实测 = `test_agate_image_check.py` 2 个（Pillow 已装）+ `test_t41_platform_hygiene.py` 1 个（DSH 上游 checkout 不在本机） |
| 5 | v0.78.0 段 **248 行**、v0.77.0 段 **191 行** | 按 `^## \[` 切段计数 | ✅ 248 / 191 |
| 6 | 「按本判据分别命中 **21 / 25 处、3 类**」（CHANGELOG:50、脚本:11、pre-commit:1203） | 出厂脚本 `scan()` | ❌ **实测 21 / 3 与 26 / 4**（v0.77.0 因 A7 收窄**多**命中 1 处 1 类） |
| 7 | 「旧版 **145 行**」 | `git show 3df9c9e8^:CHANGELOG.md` 切段 → 144 行（不含标题） | ❌ **144 行**（第一轮已指出差 1，未改） |
| 8 | 「**6 类** … 自我勘误」（CHANGELOG:53、脚本:181） | 读 `_CATEGORIES` | ❌ **`勘误` 已移出**，实际 6 类里不含「自我勘误」 |
| 9 | B-1「加了参数化防绕过用例（**8 个词**逐个断言仍 FIRE）」 | `grep -A3 "for word in" test_check_changelog_quality.py` | ✅ 8 个词（阈值/自检/词表/扫描面/误伤/本判据/判据/命中）；**建议补到 12 个**（我另测 12 个全过，无风险） |
| 10 | B-2「检出能力复验 **5/5** 未削弱」 | 同 #3 | ✅（虽然数字变了 25→26，但方向是**增强**，「未削弱」成立） |
| 11 | B-3「两段分处置：exit 1 / exit 2」 | `/tmp/r2d/t.py` | ✅ 脚本层面成立；⚠️ **CHECK 17 侧不成立**（B-6） |
| 12 | B-4「已做变异验证（移出锚点 → 转红）」 | `/tmp/r2g/mut.py` M1 | ✅ 成立 |
| 13 | B-5「已统一为后者」 | `sed -n 73p agate/scripts/README.md` | ✅ README 已改；❌ **CHANGELOG:41-42 仍写「兜底」**（只改了一侧） |
| 14 | 「ruff 全绿；consistency 0 ERROR」 | `ruff check`（5 文件）→ All checks passed；`check-protocol-consistency.py --strict-errors-only` → rc=0 / 0 ERROR / 440 WARNING（全冻结文件） | ✅ |

**结论**：4 项声称可复现且精确（#1/#2/#4/#5、#9/#10/#12/#13/#14），**3 处数字/措辞不可复现**（#6 的 21/25、#7 的 145 行、#8 的「自我勘误」）。
#6 是**本次修复直接造成的漂移**（改了词表没重算引用），按 A8 应改。

## 你点名的 8 个问题 — 逐条回答

### 1. B-1 是否真闭合？自己遍历绕过手法

**插词绕过：已完全闭合。** 我另测 12 个词（比作者的 8 个多 4 个），基线 total=5：
```
（阈值）（自检）（词表）（扫描面）（误伤）（本判据）（判据）（命中）（过程痕迹）（等 6 类）（规则）（元讨论）
→ 全部 total=5 / cats=5，无一降级
```
对照旧脚本：**11/11 全部可绕过**（total 5→0）。⇒ `_META_DISCUSSION` 整体移除是**正确修法**。

**其它包装手法实测**：

| 手法 | total | 能绕过？ | 判读 |
|---|---|---|---|
| 把整句包进 ` ``` ` 代码块 | 0 | **能** | **设计如此**（围栏内是示例代码，不是叙述）。但这也意味着「作者把过程日志包进代码块」可绕——需在文档里写明「代码块里的示例不算豁免依据」 |
| 拆分到代码块（半句在外） | 5 | 不能 | ✅ |
| 引用块 `> ` 包一行 | 5 | 不能 | ✅（第一轮建议的「引用块豁免」**没有**实现，现状是引用块照样计数——这一点**比第一轮建议更严**，好） |
| HTML 注释包裹整句 | 5 | 不能 | ✅（未剥 HTML 注释，正确） |
| HTML 注释包关键词 | 5 | 不能 | ✅ |
| 长句稀释（单行 800 字、10 句无关内容） | 5 | 不能 | ✅ **按「处数」计不按「密度」计，稀释无效**——这个设计对 |
| 逐行拆开（每行 1 个痕迹） | 5 | 不能 | ✅ |
| 全角括号夹在句中 | 5 | 不能 | ✅ |

**仍能绕过的手法（列全）**：

| # | 手法 | 实测 | 我的判断 |
|---|---|---|---|
| 1 | **整句包进围栏代码块** | ` ```\n<过程日志>\n``` ` → total=0 | **可接受**（代码块是合法文档结构，且需作者主动做）；但建议在 `CHANGELOG.md` 规范里补一句「不得用代码块承载变更叙述」 |
| 2 | **口风改写**（不用词表里的词）`两轮评审后才发现`/`初版判断有误`/`我改了三轮才对`/`先按 A 实现，发现不对，改成 B，又漏了 C` | → total=0 ~ 1 | **可接受**，理由见下 |
| 3 | **小写/大写 `[unreleased]`/`[UNRELEASED]`** 或 **`##[Unreleased]`（缺空格）** | rc=2 / **rc=0** | ⚠️ **不可接受**，见下 |
| 4 | **把痕迹写进新加一个 `## [x.y.z]` 版本标题下** | rc=2（pre-commit rc=0 放行） | ⚠️ **B-3 的可利用路径**，见 A5 |

**关于 #2（阈值本身的边界）——判断：可接受，理由与第一轮的区分一致且我现在能给出更强的依据。**

- 第一轮已经确立的区分：**「改口风」需要作者持续、主动地规避自己刚写的规范**，属「故意违规」；而 B-1 的「加一个词」是**无意的、顺手就会发生的**（正常技术条目里写「阈值」就自动豁免）。前者可接受漏，后者不可接受。
- **B-1 修完后，#2 是唯一剩下的「口风」类绕过，而它现在没有任何「顺手」的入口**——判据不再有任何按词/按行的豁免面。这是我判它可接受的关键：**绕过成本从「顺手」回到了「刻意」**。
- 但注意 #2 的实测面比第一轮描述的更宽：`两轮评审`（缺「两」）**仍是 0 命中**（M-3 未修），`初版/首版/前一稿` 也全 0。这两处**补起来零成本且不误伤**，建议补（`[两三四五六七八九十\d]`、`初版|首版|前一稿`）。这属 MINOR，非 BLOCKER。

**关于 #3（标题格式）——这是我新发现的、必须修的一条。**
`target_sections()` 用 `re.match(r"^## \[", ln)` 找段头，然后 `if "[Unreleased]" in ln`。
于是：
```
## [Unreleased]      → 找到，rc=1 ✅
##[Unreleased]       → re.match 不匹配 ⇒ 整段不被扫 ⇒ rc=0（完全放行）❌
## [unreleased]      → 不匹配 "[Unreleased]" ⇒ 被当成「已发布段」⇒ rc=2 ⚠️
```
**而 `2m` 的提取器（`agate-changelog-unreleased.py:9`）用的是 `##\s*\[Unreleased\]` —— 它能看见 `##[Unreleased]`。**
⇒ **两个脚本对「`[Unreleased]` 在哪」的判定不一致**：`2m` 认为该段存在（要求含 task_id），`2z2` 认为不存在（不检查）。
这是 ADR-014「判据单源」在本判据内部的一次**分叉**（虽然分的是两个不同判据，但共用同一份 Markdown 结构的解析口径）。
端到端实测：`##[Unreleased]` + 极端坏条目 → `pre-commit rc=0`（放行）。
**修法**：段头正则改成 `^##\s*\[`，`[Unreleased]` 判定改成 `"[Unreleased]" in ln`（保留）或统一复用 `agate-changelog-unreleased.py` 的 `##\s*\[Unreleased\]` 口径。**优先级高于 #2。**

### 2. B-2 修完后检出能力有没有被削弱？用真实语料复验

**没有被削弱，反而在 v0.77.0 上增强（25→26）。** 5 语料复验全部符合预期（见 A8 #3）。

**误伤面残留：已基本消除。**

| 情形 | 修复前 | 修复后 |
|---|---|---|
| 勘误①（2 条纯勘误） | rc=1 阻断 ❌ | **total=0 PASS** ✅ |
| 勘误②（勘误+教训） | rc=1 阻断 ❌ | **total=1/cats=1 PASS** ✅ |
| 勘误③（同行「勘误+上一版+我们发现」） | rc=1 阻断 ❌ | **total=1/cats=1 PASS** ✅ |

**但你点名的那个问题成立：一个通篇「教训」+「勘误」的真过程日志**：
```
- 教训：不该先改后测。
- 教训：这次漏了口子。
- 教训：下回先写回归。
- 勘误：上一版的说明写错了。
- 勘误：上一版的示例也错了。
- 勘误：上一版还有一处笔误。
→ NEW total=3 / cats=1（只有 A6）⇒ PASS  ← **该拦，现在放行了**
→ OLD total=8 / cats=2 ⇒ FIRE ✅
```
**根因**：`勘误` 移出 A6 后，这类条目里**唯一命中的类别只剩 A6**，单类被阈值（≥2 类）豁免。
**我的判断：这是 B-2 修复的必然代价，且我认为可接受**——理由：
- 「勘误：上一版写错了」**本身确实是正当的 CHANGELOG 内容**（第一轮 B-2 的论证成立）。
- 要同时做到「拦勘误风暴」和「不拦正当勘误」，靠**词汇表**做不到——两者字面相同，只能靠语义判断（本判据明确不做 LLM 判断）。
- 真正的「通篇教训+勘误」过程日志在实践中会同时带第一人称/评审轮次/测试计数（实测「教训风暴」6/1 PASS 但「教训+两轮评审」6/2 FIRE）。
- **建议（可选，非阻断）**：把 A6 再收窄为 `教训(?!：上一版)` 这类**否定前瞻**，或给「勘误」单独设「≥5 处才计数」的次级阈值。但这会让判据变复杂，收益不明确——**我倾向不做**，只需在 `CHANGELOG.md` 规范里明确「勘误类条目也要写清影响，不要写成自我检讨」。

### 3. B-3 的两段分处置是否合理

**实测符合声称**：exit 2（Unreleased 干净+旧段痕迹）/ exit 1（Unreleased 有痕迹）✅。

**只提示（exit 2）对已发布段合理吗？——合理。**
理由（我独立认可，与第一轮建议同向）：已发布段是历史快照（`doc-freshness-guide.md` §3），硬阻断的唯一出路是改写历史，与既有纪律直接矛盾，且会让存量仓库升级后第一次提交就被卡。

**会不会导致「作者把过程日志写进已发布段就没人拦」？——会，而且不需要真的「改已发布段标题」。**
关键实测（见 A5）：`target_sections()` 把「首个非 `[Unreleased]` 的 `## [` 段」当作「已发布段」，**不校验是否真发布**。
所以作者只需**新写一个还没发布的 `## [0.84.0] - 2026-12-01`** 把痕迹放进去，就自动降级为 exit 2。
端到端 `pre-commit rc=0` 放行（实测）。

**这个动作显眼吗？**
- 在 **diff 层面显眼**：新增带版本号+日期的标题是结构性改动，review 会看见。
- 在 **pre-commit 层面完全不显眼**：2z2 只会打一行 NOTE（不阻断）。
- 而且**会撞 CHECK 7 / CHECK 13**（实测两项都 `❌ FAIL`）——但那两道在纯 docs 提交时 **fast-pass**（consistency job），`docs-check` 不在 required check。
⇒ **净结论：在「主要强制力」pre-commit 上，这条路径没有任何拦截。** 这是我判 A5 = MISALIGNED 而不是 ALIGNED 的原因。
**修法见 A5(d)**：给「已发布段」加真伪校验（版本号 ≤ 最近 tag / 在 UPGRADING §3 有章节），否则按 Unreleased 处理。

### 4. B-4 独立裁决

见 A6 的 (a)(b)(c)(d)。**核心结论重述**：

- **(a)** 原文（`P1-requirements.md` BDD-23 支①）= 「该脚本**须已登记**（进 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表或 `GATE_SCRIPT_EXEMPT` 豁免集）使 SG.6 通过（未登记则 SG.6 红，判 FAIL）」。**作者引用准确。**
- **(b)** **改这个测试是正当修正，不是为通过而放宽判据。** 三条依据：原断言比需求更严且严错方向；原断言与 `agate/scripts/README.md`「新增脚本登记面」冲突；真实门禁（SG.6 / CHECK9-coverage）不依赖它，改它不降低门禁强度。
- **(c)** **能拦住**（M1 实测 FAIL），**但有一个「一行注释即绕」的洞**（M4/M6/M8 实测：新测试 PASS 而真门禁 FAIL）——这与 DEBT0046 已修掉的子串判定**完全同型**。必须修。
- **(d)** **该改**，正确做法 = 改，但**复用 `uncovered_gate_scripts()`**（不要自己写子串匹配）；或删掉这条冗余分支（SG.6 已覆盖同一事实）。

### 5. 回归面

**「18 passed / 16 passed 属实」——属实**，我独立复跑：18 passed / 16 passed。

**新判据会不会影响既有 gate 流程（如 P8 的 `check-changelog.py`）？——不会，已实测。**

| 流程 | 脚本 | 触发面 | 与 2z2 的关系 | 实测 |
|---|---|---|---|---|
| 2m（P1.6） | `check-changelog.py` + `agate-changelog-unreleased.py` | **仅 P8 phase**（`pre-commit-gate.py:1086-1087`，`phase == "P8"`） | 不同脚本、不同触发面 | `test_check_changelog.py` + `test_agate_changelog_unreleased.py` = **10 passed** ✅ |
| 2z2（RM-AG0117） | `check-changelog-quality.py` | **仓库级循环外**（暂存 CHANGELOG 即跑） | 独立 | 端到端 rc=1（hotfix 无 `.state.yaml`）✅ |

**两者检查的是同一文件的不同维度**（2m 查「有没有 task_id」，2z2 查「文风」），不冲突。
但注意 A5 观察到的**语义倒挂**仍存在（第一轮已指出）：2m 对缺 task_id 只 WARNING，2z2 对文风 exit 1 —— 同一文件上「存在性软、文风硬」。**本轮仍未处理**，建议在 `WORKFLOW.md` 的 2m/2z2 行各加一句说明这是有意的（否则下一个人会当成 bug 修）。

### 6. A4b：转红清单 + 夹具

**转红清单（非空，1 项）**：`test_release_gate.py::test_bdd_23_no_new_check_star_script_added`
**需更新的夹具：无**（实测依据见 A4b 段）。
（第一轮判「空清单」在当时成立，但未预见本轮修法；见 A4b 段的说明。）

### 7. A8：逐条产出命令

见 A8 表。**特别注意**：
- **「3072 passed」自洽**：3077 collected − 2 failed − 3 skipped = 3072。3 个 skip 我逐个找到（Pillow 2 个 + DSH 上游 checkout 1 个），**不是一个凑出来的数字** ✅
- **「16 passed」「18 passed」精确** ✅
- **「5/5 语料」精确** ✅
- **「21/25 处」不精确**：实测 21/**26**（v0.77.0 因 A7 收窄反而多命中）❌
- **「145 行」不精确**：实测 **144 行**（第一轮已指出，未改）❌

### 8. 有没有新引入的过度声称？

| 位置 | 声称 | 实际 | 判定 |
|---|---|---|---|
| `check-changelog-quality.py:133-136` | 「**不要再加**行级元讨论豁免（曾经的 `_META_DISCUSSION`）……实测 11 个词里 6 个仍能绕过」 | 我实测**11/11 全部可绕过**（不止 6 个） | **不算过度声称**，是**低报**（说 6 个实际 11 个）。但注释里保留 `_META_DISCUSSION` 这个名字作为「历史教训」，属**合理留痕**，不构成「仍残留元讨论豁免」——**机制确已整体移除，dunder 级别验证：`_META_DISCUSSION` 在文件中仅作为注释文本出现 1 次（`:133`），无定义、无调用** ✅ |
| `CHANGELOG.md:41-42` | 「并由 CI **CHECK 17** 兜底」 | ① CHECK 17 调的是旧脚本，B-3 修复在 CI 侧不生效；② 删旧脚本后 CHECK 17 静默 fail-open；③ 纯 docs 提交 consistency fast-pass | ❌ **过度声称**（且与同批 `agate/scripts/README.md:73`的「不是可靠兜底」矛盾——B-5 只修了一侧） |
| `agate/scripts/README.md:73` | 「CHECK 17 作补充（覆盖 `--no-verify`），但**不是可靠兜底**」 | 「补充」在当前实现下是**真空**（B-6） | ⚠️ 措辞比 CHANGELOG 诚实，但「作补充」仍乐观 |
| `check-protocol-consistency.py:27,1461` | 「判据单源 = `agate-changelog-quality.py`」 | **两个脚本并存，词表已分叉** | ❌ **过度声称**（ADR-014 字面违反） |
| `check-protocol-consistency.py:1462-1465` | 「⚠️ 判据脚本命名为 `agate-*.py` 而非 `check-*.py`：后者会触发 SG.6/CHECK9-coverage 两处登记面……而本判据是「工具/观测定性」类」 | 脚本**已改名**为 `check-*` 并登记锚点；这段注释**描述的是已被推翻的决定**，且理由（「工具/观测定性」）已被作者自己在 commit msg 里否定 | ❌ **残留陈旧注释**，会误导后来者以为「不该用 check- 前缀」 |
| `check-changelog-quality.py:31,32,183` | 用法/自证命令写 `agate-changelog-quality.py` | 正确名是 `check-changelog-quality.py` | ❌ **残留旧名**（A2） |
| `test_check_changelog_quality.py:6` | 「v0.78.0 段 248 行含 **158** 处过程痕迹、v0.77.0 段 191 行含 **121** 处」 | 实测 21 / 26 | ❌ **不可复现**（第一轮 M-1，未修） |
| `CHANGELOG.md:50`、`check-changelog-quality.py:11`、`pre-commit-gate.py:1203` | 「21 / 25 处、3 类」 | 21 / **26**、3 / **4** 类 | ❌ 数字漂移 |

**结论：「B-1 的注释是否仍残留元讨论豁免的说法」——没有残留机制，只有历史说明，这是对的。**
但**「已修」类过度声称集中在 B-3 的 CI 侧与 B-5 的 CHANGELOG 侧**，以及**旧名/旧数字未同步**（3 处脚本名 + 3 处 21/25 + 1 处 158/121 + 1 处 145 行）。

## BLOCKER / MINOR 清单（文件:行号 + 修法）

### BLOCKER

**B-6（新）`agate/scripts/check-protocol-consistency.py:1468`（+ `:27` `:1461` `:1481`）**
CHECK 17 仍调用**旧脚本** `agate-changelog-quality.py`，而 2z2 用新脚本 `check-changelog-quality.py`。两脚本并存且词表已分叉。
实测：留旧脚本 ⇒ B-3 修复在 CI 侧不生效（已发布段痕迹仍 `❌ FAIL`）；删旧脚本 ⇒ `:1470 if not script.is_file(): return` **静默 fail-open**，极端坏 Unreleased 也 `✅ PASS`。**两个状态都错。**
→ (1) `:1468` 改 `check-changelog-quality.py`；(2) **提交删除 `agate/scripts/agate-changelog-quality.py`**；(3) `:27`/`:1461`/`:1481` 措辞同步、删掉 `:1462-1465` 那段已被推翻的「不该用 check- 前缀」注释；(4) CHECK 17 判 `returncode != 0` 或至少把 `== 2` 输出为 WARNING（现在 exit 2 在 CI 里完全静默）；(5) 补测试断言 CHECK 17 的脚本路径 + 两文件名不得同时存在。

**B-3′（升级自 MINOR）`check-changelog-quality.py:90-124`（`target_sections`）**
「最新已发布段」= 「首个非 `[Unreleased]` 的 `## [` 段」，**不校验是否真发布**。作者新写一个 `## [0.84.0]` 标题把痕迹放进去即降级 exit 2 ⇒ 端到端 `pre-commit rc=0` 放行（hotfix 无 `.state.yaml` 实测）。
→ 给「已发布段」加真伪校验（版本号 ≤ 最近 git tag，或在 `agate/UPGRADING.md` §3 有章节）；不满足 ⇒ 按 Unreleased 处理（exit 1）。
→ 或在 exit 2 提示里明写「**把新内容包进一个新版本标题不改变判据**」。
→ 补测试：`## [9.9.9]`（UPGRADING 无章节）+ 痕迹 → 期望 exit 1。

**B-7（新，MINOR 升 BLOCKER）`check-changelog-quality.py:105`**
段头正则 `^## \[` **不匹配 `##[Unreleased]`（缺空格）** ⇒ 整段不扫 ⇒ 端到端 `pre-commit rc=0` 放行；`## [unreleased]`（小写）⇒ 被当已发布段 ⇒ rc=2。
而 `2m` 的提取器（`agate-changelog-unreleased.py:9`）用 `##\s*\[Unreleased\]` **能**看见它 ⇒ 同一文件两份判据口径不一致。
→ 改 `^##\s*\[`；`[Unreleased]` 判定建议复用 `##\s*\[Unreleased\]` 口径。
→ 补测试：`##[Unreleased]` + 坏条目 → 期望 exit 1。

**B-4′（A6 实现洞）`agate/tests/unit/test_release_gate.py:389-395`**
新测试用 `cpc[exempt_m.start():]` **子串**判「是否已登记」⇒ 在文件里豁免集之后的任意位置（含注释）写一遍脚本名即 PASS，而真门禁 SG.6 仍 FAIL（M4/M6/M8 实测）。与 DEBT0046 已修掉的缺陷同型。
→ 改 `importlib` 加载 `check-protocol-consistency.py`，直接复用 `uncovered_gate_scripts(H.REPO_ROOT)`；或删掉这条冗余分支（SG.6 已覆盖）。

### MINOR

**M-1（沿用第一轮，未修）`agate/tests/unit/test_check_changelog_quality.py:6`** — 「158 处 / 121 处」不可复现。→ 改成「248 行命中 21 处 / 191 行命中 26 处」。

**M-2（沿用第一轮，未修）`test_check_changelog_quality.py:128-139`** — 挂载点守护用 `mount > loop` 行号判据；变异（2z2 整块缩进 +4 移进循环体）实测**仍 PASS**。→ 改断言缩进相等：`len(ln)-len(ln.lstrip())`。

**M-3（沿用第一轮，未修）`check-changelog-quality.py:48-51`** — A2 字符类缺「两」：`两轮评审`/`两轮独立评审`/`多轮评审` 实测 0；`二轮评审` 命中。→ 字符类补 `两`，并考虑 `多|数|若干`。

**M-4（沿用第一轮，部分修）`check-changelog-quality.py:44-46`** — 已加 `我判断/我认为`（`我判断` 实测命中），但**「我们」全不认**：`我们认为/我们判断/我们原先/我们漏了` 实测全 0（正则只有单字「我」）。→ 改 `我(?:们)?(?:发现|认为|判断|原先|漏|错|写|以为)`。

**M-5（沿用第一轮，未修）缺 2z2 行为级测试** — `grep -rn "changelog-quality\|CHANGELOG-QUALITY" agate/tests/integration/` → **0 命中**。→ 补「只暂存坏 CHANGELOG、无 `.state.yaml` → `pre-commit-gate.py` rc≠0」。

**M-6（新）`check-changelog-quality.py:31,32,183`** — 旧脚本名 3 处残留，其中 `:183` 是**判据失败时打印给用户的自证命令**。→ 改成 `check-changelog-quality.py`；建议加测试 `assert "agate-changelog-quality" not in text`（防第三次同型错误）。

**M-7（新）`CHANGELOG.md:53` / `check-changelog-quality.py:181`** — 仍写「自我勘误」属 6 类之一，但 `勘误` 已移出词表。→ 删除该词或改为「第一版写错了」。

**M-8（新）`CHANGELOG.md:41-42`** — 仍写「由 CI **CHECK 17** 兜底」，与同批 `agate/scripts/README.md:73` 的「不是可靠兜底」矛盾（B-5 只修了一侧）。→ 改成与 README 一致。

**M-9（新）`check-changelog-quality.py:105` 与 `agate-changelog-unreleased.py:9` 口径不一致** — 见 B-7；即使不修 B-7，也应在两处注释里互相指认「段头解析口径不同，改动须同步」。

## 闭环

| 结论 | 主 Agent 动作 |
|---|---|
| **MISALIGNED**（A1/A2/A3/A4/A5/A6/A8） | **必须修复后重审**。B-6（CHECK 17 指向旧脚本 / 双份判据）、B-3′（版本节降级通道）、B-7（段头正则漏 `##[Unreleased]`）、B-4′（子串判登记）都是机制缺陷，不是措辞；按 `AGENTS.md`「真 MISALIGNED 一律修完再复审」不得以「呈现类问题」跳过。 |
| **A7 = ALIGNED** | ADR-015 的成本面已因 B-2/B-3 收窄而改善，第一轮的 NEEDS_HUMAN_REVIEW 可关闭。**唯一仍需人工拍板**：B-2 的代价（通篇「教训+勘误」的真过程日志不再被拦）是否可接受——我判**可接受**，但这是价值取舍，应由你决定。 |

> **对第一轮结论的独立判断**：第一轮的 5 个 BLOCKER 诊断**全部成立**，我逐条复现了（含 B-4 的「改回 check- 前缀即 SG.6 红」）。
> 但第一轮有两个盲点：(1) **没发现 CHECK 17 用的是哪个脚本**（它的 A4b 实测是在「脚本名 `agate-*`」的基线上做的，改名后该结论失效）；
> (2) **A4b 判「空清单」没有预见修法会引入转红**。这两点都不是错误判断，是**基线与修法变更**导致的时效问题——但正因为如此，本轮把「修法会不会引入转红」也纳入了 A4b 的判据。

> 设计取向再强调：**阻断级、不用行数、A3 只提示不计数、已发布段不硬阻断 —— 这四条我复验后仍然认为是对的，不要在修复中放宽。**
> B-6/B-3′/B-7/B-4′ 全部可以在保持这四条的前提下修掉。
