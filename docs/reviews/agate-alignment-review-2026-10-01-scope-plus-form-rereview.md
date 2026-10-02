---
review_date: 2026-10-01
reviewer: protocol-alignment-review
review_type: re-review（复审）
change_summary: 对 agate-alignment-review-2026-10-01-scope-plus-form.md（NEEDS-REVISION）的 M1-M6 / L1-L6 整改逐条复核，并检查整改本身是否引入新问题
supersedes: docs/reviews/agate-alignment-review-2026-10-01-scope-plus-form.md
files_changed: [CHANGELOG.md, agate-workspace/roadmap/roadmap.md, agate/WORKFLOW.md, agate/assets/execution-roles/architect.md, agate/assets/execution-roles/implementer.md, agate/dispatch-protocol.md, agate/phase-cards/P4-implementation.md, agate/scripts/check-retrospective.py, agate/scripts/check-scope-resolved.py, agate/state-machine.md, agate/tests/README.md, agate/tests/fixtures/tag0034_regression_baseline.json, agate/tests/unit/test_check_scope_resolved.py, docs/design-notes/README.md, docs/design-notes/design-scope-plus-declaration-form.md]
---

# 协议-脚本对齐审查（复审）

> **证据标记约定**：**[实测]** = 本次会话真实跑出输出；**[推断]** = 读代码/文档推导，未跑命令。
> **只读纪律**：本审查**未执行任何写仓 git 命令**（无 `checkout`/`restore`/`reset`/`stash`/`clean`/`add`/`commit`），
> **未编辑被评审文件**。全部变异测试在 `.agate-tmp/rerev/copy/`（仓库 scratch 区、`.gitignore:32` 已忽略）内完成，
> 「建副本 → 变异 → 跑测 → 删副本」在**同一次 bash 调用**内；每次调用末尾均打印 `copy removed: YES` [实测]。
> scratch 脚本保留在 `.agate-tmp/rerev/`（`mutate.py` / `mutate2.py` / `mutate_m1.py` / `scan.py` / `scan2.py` / `e2e.py` / `evid.py` / `patcheck.py`），
> **不含任何仓库源码副本**。本次唯一写出的成果文件 = 本报告。

## 0. 审查快照与被评审对象的变动（重要）

**本报告结论只对下列快照成立**（`HEAD = acbc450`，快照时间 2026-10-02 16:15）[实测：`sha256sum` 前 16 位]：

| 文件 | sha256（前 16） |
|---|---|
| `agate/scripts/check-scope-resolved.py` | `afcd365e72a821fc` |
| `agate/scripts/check-retrospective.py` | `2a35b2ae5ffa2b3d` |
| `agate/tests/unit/test_check_scope_resolved.py` | `fdbd13d084fe0c37` |
| `CHANGELOG.md` | `4b7e78d6a122f9e2` |
| `docs/design-notes/design-scope-plus-declaration-form.md` | `582313acd1964448` |
| `agate-workspace/roadmap/roadmap.md` | `d99bfeaf9611f8a7` |
| `agate/WORKFLOW.md` | `93eb405a5a3a25c7` |
| `agate/dispatch-protocol.md` | `c3898ee1a36ec41c` |
| `agate/state-machine.md` | `e3a1f5708bf3fef8` |

> ⚠️ **被评审文件在本审查进行期间被改动过** [实测：`stat` mtime + 两次 `wc -l`]：
> - 设计说明在我首次读取时为 **191 行**，再次读取时已是 **209 行**（mtime `15:40:33`），新增了 §9「我又犯的两个错」；
> - `CHANGELOG.md` mtime `15:40:44`，晚于全部代码文件（`15:28`–`15:35`）。
>
> 这不构成缺陷（主 Agent 在并发整改），但**意味着复审对象是一个移动靶**：本报告的判定以 16:15 快照为准。
> 若此后再次改动上述文件，本报告对应条目需重新核验。

### 0.1 审查期间主 Agent 已在并发修复本报告的部分发现（截至 16:23）[实测]

我在出报告的同时观察到主 Agent 正在改动设计说明与测试文件，其内容**与本报告的 N1/N2 高度一致**
（疑似独立得出相同结论，或已看到本报告）。**截至快照时刻的落地情况**：

| 项 | 设计说明 | `test_check_scope_resolved.py` | `CHANGELOG.md` | `roadmap.md` |
|---|---|---|---|---|
| **N1**（6 → 4） | ✅ **已改**：§3:59 与 §3.1:81 均为 **4**，名单 `TAG0012`/`TAG0014`/`TAG0023`/`TAG0025`，并补口径提示（若用「标题行内任意位置」才得 6） | — | ❌ **仍写 6**（`:29`） | ❌ **仍写 6**（`:78`） |
| **N2**（`TAG0008` 非真声明） | ✅ **已改**：§3.1:84 新增「⚠️ 更正：初版把 `TAG0008` 也列为真声明——不成立」，给出正文「无」的证据 | — | ❌ **仍写**（`:30`「`TAG0004`/`TAG0008` 的真声明」） | ❌ **仍写**（`:78`） |
| **N2b**（`TAG0025` 定位） | ✅ **已改**：§3.2:105-110「二次更正」——承认「不是行首」被 `od -c` 证伪，改称「视觉行首、段落中句」，并指出这**反而支持**保守边界 | ✅ **已改**：`sc_13` docstring 重写，明确 `TAG0025` 不属否定类并解释折行 | — | — |
| **N3**（判据不可复现 / 28） | ❌ **未改**（`:69-70` 仍是未转义 `+` 与 `28 处`） | — | — | — |
| **N4**（10 vs 14） | ❌ **未改**（`:148` 仍写 10 个已跟踪文件） | — | — | — |

⇒ **第二批整改已修掉 N1/N2 在设计说明与测试侧的部分**，但 **N1/N2 的错误数字与定性仍留在
`CHANGELOG.md` 与 `roadmap.md`**（扩散面未同步回改），且 **N3/N4 完全未动**。
**最终判定仍为 NEEDS-REVISION**：回改面从 5 项收窄为「同步 CHANGELOG + roadmap 的 N1/N2 + N3 + N4」。

> 复核实测：改动后 `pytest agate/tests/unit/test_check_scope_resolved.py -q` 仍为 **19 passed** [实测，16:23]，
> 设计说明 `6ead13660892ece4`、测试 `5e550fadd31b7025`。

---

## 1. 复审结论汇总（M1-M6 / L1-L6）

| # | 原报告要求 | 复审判定 | 一句话依据 |
|---|---|---|---|
| **M1** | §7「实现后 16 passed」→ 17（后又因新增 2 条边界用例变 19） | ✅ **已修复** | §7 现为「**19 passed**」；实测 19 passed [实测] |
| **M2** | CHANGELOG「unit 2276 passed」→ 2277（后变 2279） | ✅ **已修复** | CHANGELOG:58 现为「**2279 passed** / 1 failed + 2 skipped」；实测 1 failed, 2279 passed, 2 skipped [实测] |
| **M3** | 「反引号**一律**是引述/否定」有反例（`TAG0004:50`）；`TAG0025` 是**错位证据** | ⚠️ **修复不当（部分回退）** | 文档三处已更正「一律」并登记 `TAG0004` 反例 ✅；但**新增的 `test_sc_13` docstring 又把 `TAG0025` 写成「反引号**行首**形态」**，与设计说明 §3.2 的「`TAG0025` **不是行首**」**直接冲突**，且该「不是行首」本身**被 `od -c` 证伪**（详见 §2-N2） |
| **M4** | 标题形态未覆盖且未申报为**刻意排除** | ✅ **已修复**（申报到位）／❌ **但转红数错误（新引入）** | 设计说明 §3.1 已显式申报为刻意排除 + 代价；`test_sc_15` 锁成判据且**变异实测转红** ✅。**但「新增 6 个任务转红」实测为 4** [实测]，且清单含 `TAG0004`/`TAG0008` 与该判据矛盾（详见 §2-N1） |
| **M5** | `docs/design-notes/README.md` 未登记新设计说明 | ✅ **已修复** | README:33 已登记；该表列数 5 与表头一致 [实测] |
| **M6** | `roadmap.md` 的 `RM-AG0077` 行与本次 hotfix 矛盾 | ✅ **已修复**（行内事项）／❌ **但承接了一处错误声称** | roadmap:78 已追加 2026-10-01 落地说明；**9 列正确**、`&#124;` 转义已生效 [实测]。但该行复制了「纳入会新增 6 个任务转红」的错误数字（详见 §2-N1） |
| **L1** | 「反引号包裹不触发」无条件表述，与 `SCOPE_RESOLVED` 侧不对称 | ⚠️ **部分修复（1/3 处）** | 仅 `WORKFLOW.md:451` 写明两侧边界与「不对称」；`dispatch-protocol.md:953`、`state-machine.md:233` **均未**提及不对称（详见 §2-N5） |
| **L2** | `implementer.md:124` / `architect.md:293` 未含反引号说明 | ✅ **已修复** | 两处均补「句中引用与反引号包裹不触发 gate」+ 指向 `WORKFLOW.md` 单源 [实测] |
| **L3** | 「一版语义启发式全仓命中 22 个任务」无产出命令 | ✅ **已修复** | 该量化声称已**删除**；改为止性表述并说明理由（设计说明 §3 引用块；`grep "22 个任务"` = 0 命中）[实测] |
| **L4** | §5 方法学措辞不自洽 | ✅ **已修复** | §5 现写「分别以改动前正则与改动后正则求值（同一判据链，仅正则不同），并另用改动后的真实脚本端到端交叉验证」——措辞自洽 [实测] |
| **L5** | §6 变更清单漏列 `CHANGELOG.md` 与 `tests/README.md` | ⚠️ **部分修复** | 两个被点名的文件**已补入表中** ✅；但 §6 的**计数仍错**（写 10，实测 **14**），且表中**仍漏** `roadmap.md` / `architect.md` / `implementer.md`（详见 §2-N4） |
| **L6** | §4 未记 `TAG0001` 的文件级次生变化 | ✅ **已修复** | §4 已补记 `TAG0001` 新增 `P2-review.md` 命中且输出不变；实测 TAG0001 命中文件 = 3（新增 1）✅ |

**另**（原报告 §2 要求更正的双侧协同理由链）：
**✅ 已修复。** 设计说明 §2 现明确写「**载荷点更正**：初版把理由写成『`SCOPE_RESOLVED_RE` 同样只认行首』——**不准确**」，
并指出「真实载荷点是**反引号**」[实测：`TAG0021/P1-requirements.md:231` 首字节 `od -c` = `` ` ``（0x60），
`**[SCOPE+]` 在 `P2-design.md:379`]。CHANGELOG 同步更正。

**原报告 13 项必须修复项中：9 项完全修复、3 项部分修复、1 项修复不当（M3）。**
**但整改同时引入了 4 项新问题（2 项 MEDIUM、2 项 MEDIUM-LOW），其中 2 项已扩散到 3 个文件。**

---

## 2. 整改引入的新问题（本报告新增项）

### N1（MEDIUM）：标题形态「新增 **6** 个任务转红」实测为 **4**，且清单含两个判据不命中的任务

**声称**（三处，措辞一致）：
- 设计说明 §3.1:81「实测纳入标题形态会新增 **6 个任务转红**（`TAG0004`/`TAG0008`/`TAG0012`/`TAG0014`/`TAG0023`/`TAG0025`）」
- `CHANGELOG.md:29`「**纳入会新增 6 个任务转红**」
- `roadmap.md:78`「纳入会新增 6 个任务转红」

**实测**（用**真实脚本**端到端跑全部 41 个任务目录；`.agate-tmp/rerev/e2e.py`）[实测]：

```
task_count = 41
baseline(new)              checked=9  skip=32 red=0
A_tight_heading_with_N     checked=11 skip=26 red=4   ← 与设计说明 L80 自述判据一致
A2_tight_heading_no_N      checked=11 skip=28 red=2
A3_loose_heading           checked=11 skip=24 red=6   ← 唯一能得 6 的变体
B_lead_backtick            checked=10 skip=26 red=5
C_inline                   checked=12 skip=5  red=24
```

| 「纳入标题形态」的实现方式 | 转红数 | 红名单 |
|---|---|---|
| **A** `_SCOPE_LEAD` 追加 `(?:#{1,6}\s+)?(?:\d+\.\s*)?`（**吃掉 `N. ` 编号前缀**，即设计说明 L80 自述的「标记前有标题编号」口径） | **4** | TAG0012 / TAG0014 / TAG0023 / TAG0025 |
| **A3** 改成 `^#{1,6}\s+.*\[SCOPE+\]`（标题内**任意位置**命中） | **6** | +TAG0004 / +TAG0008 |

⇒ **两处错误**：

1. **数字与自述判据不符**：设计说明把边界描述为「`[SCOPE+]` 须在行首…`## 8. [SCOPE+] 声明` 的标记前有**标题编号**」（L80），
   这正是变体 **A**；而 A 的转红数是 **4**，不是 6。**6 只在把判据放宽成「标题行内任意位置」时才成立**（变体 A3）——
   而 A3 恰恰是**同一个文件**把「行中出现」判为提及的那条边界（§3 表格第 4 行，转红 24）。
   即：**6 与 24 用的是同一种「行内任意位置」口径，却只给 24 挂了「行中出现」的标签。**
2. **清单含不命中的任务**：`TAG0004` / `TAG0008` **不在变体 A 的命中集内**（`tight` 逐行扫描确认二者为 `loose`-only：
   `TAG0004:P7-consistency.md:42`、`TAG0008:P2-design.md:202` 均为「标题 + 标题文字里带 `[SCOPE+]`」而不含 `N.` 前缀形态）。
   ⇒ 把它们列进「纳入标题形态会转红」的名单，**在 A 口径下不成立**。

**并且这是一处「同族缺陷」的复发**：原报告 L3 的整改要求是「无产出命令的量化声称应删除」。
本条**有命令可得**（我有），但**给出的数字与文档自述的判据不匹配**——即声称与判据未绑定，正是 A8 要治的形态。

**证据（A 与 A3 的红名单对比）** [实测，`.agate-tmp/rerev/e2e.py`]：

```
A_tight_heading_with_N     red=4  TAG0012 / TAG0014 / TAG0023 / TAG0025
A3_loose_heading           red=6  TAG0004 / TAG0008 / TAG0012 / TAG0014 / TAG0023 / TAG0025
```

**建议**（二选一，不可含糊）：
- 若判据是变体 A（推荐，与协议「行首」定义一致）→ 三处数字改为 **4**，名单改为 `TAG0012`/`TAG0014`/`TAG0023`/`TAG0025`；
- 若坚持 6 → 必须**同时改判据**为「标题行内任意位置」，并说明它与「行中出现（24）」的口径差别。

---

### N2（MEDIUM）：`TAG0008` 被写成「真声明」不成立；`TAG0025` 的「不是行首」被 `od -c` 证伪，且新增测试 docstring 与设计说明互相矛盾

**(a) `TAG0008` 是「容器标题」，不是真声明。**
设计说明 §3.1:82 称「代价已知且有未覆盖的**真声明**：`TAG0004`、`TAG0008` 的标题形态属真声明」，
`CHANGELOG.md:30` 与 `roadmap.md:78` 均复制了「`TAG0004`/`TAG0008` 的真声明仍未被覆盖」。

**实测**：`TAG0008/P2-design.md:202-204` 原文为——

```
202|### 4.8 设计中新发现的隐含需求（[SCOPE+] 标注意见）
203|
204|- 无。调研结论 + P1 基线已覆盖全部实现决策点；未发现 P1 未预见的必须做的事。…
```

正文是「**无**」——这正是 §3.1 表格第 1/2 行所说的「**容器标题**，正文是否定 ⇒ 匹配它会**假红**」。
把 `TAG0008` 同时归入「容器标题（会假红）」与「真声明（漏检有代价）」，**同一文件内自相矛盾**；
且经逐文件扫描，`TAG0008` 的全部 `.md`（排除 `dispatch-*`/`progress`）在**新正则下 0 命中** [实测]：

```
TAG0008-version-management -> NONE (0 declarations)
TAG0004-env-adaptation     -> NONE (0 declarations)
```

⇒ `TAG0004` 的真声明性**成立**（`P7-consistency.md:42-48` 有「### 2.1 P4 组 1 的 [SCOPE+]」节 +
`[SCOPE_RESOLVED: pre-commit-gate.sh L104/L290 …]` 闭环判定）[实测]，
但 `TAG0008` 的标题**只登记「无」**，不是真声明。**该错误已扩散到 3 个文件。**

**(b) `TAG0025` 的「不是行首」是位置层面的错误陈述。**
设计说明 §3.2:103 的「更正另一处错位证据」写：

> 实测 `TAG0025/P4-implementation.md:80` 是**句中**形态（`` `[SCOPE+]`/`[DESIGN_GAP]`/… ``），**不是行首**——用它论证行首边界是**错位证据**。

**实测**（`od -c` + 正则 span）[实测]：

```
$ sed -n '80p' …/TAG0025/P4-implementation.md | od -c
0000000   `   [   S   C   O   P   E   +   ]   `   /   `   [   D   E   S     ← 第 0 字节 = 反引号
match: '`[SCOPE+]'  span (0, 9)   → IS line-start match: True
```

⇒ 该行**视觉行首即反引号**，行首反引号变体**在偏移 0 处命中**。
「**不是行首**」这一**位置性**断言**不成立**。可辩护的说法是「**段落中句**（因换行折行落在行首）」——
即「形态判据无法区分『折行导致的视觉行首』与真正的行首声明」。这恰恰是一个**有利于**现行保守边界的论据，
但文档把它写成了位置事实，读者据 `grep -n` 即可推翻。

**(c) 更严重：同一批新增的测试 docstring 与设计说明直接矛盾。**
`test_sc_13` 的 docstring（`test_check_scope_resolved.py:217`）是**本次 diff 新增行** [实测：
`git diff … | grep -c '^+.*TAG0025/TAG0033'` = **1**]，其内容为：

```python
"""反向护栏：反引号包裹的 `[SCOPE+]` 是**引述**而非声明，不检出。
存量证据：TAG0025/TAG0033 的反引号行首形态实为「`[SCOPE+]`：无」这类确定性否定陈述。"""
```

即：**测试说 `TAG0025` 是「反引号行首形态」，设计说明说 `TAG0025`「不是行首」**——
两个都在本批改动内的文件，对同一行给出相反的位置判定。M3 的整改要求正是「更正 `TAG0025` 错位证据」，
而整改后的**新增测试代码把该错位证据原样写了回去**。

**建议**：
- 设计说明 §3.2:103 改为「**视觉行首、段落中句**（换行折行所致）——位置判据无法区分，故仍判提及」；
- `TAG0008` 从「真声明」名单移除（三处），§3.1 的「代价」只保留 `TAG0004`（并说明 `TAG0008` 属容器标题）；
- `test_sc_13` docstring 的「反引号行首形态」措辞与设计说明统一。

---

### N3（MEDIUM）：设计说明给出的**判据命令跑不出它自己的数字**（A8 复发）

设计说明 §3.1:69-70 与 §9:194-195 两处给出标题形态的**判据**：

```
判据 `^\s*#+\s*(?:\d+\.\s*)?\[SCOPE+\]`   → 声称 15 处 / 10 个任务
更宽松的 `^#+ .*\[SCOPE+\]`              → 声称 28 处
```

**实测**（照抄该判据进 `grep -E`）[实测]：

```
$ grep -rnE '^\s*#+\s*(?:\d+\.\s*)?\[SCOPE+\]' agate-workspace/tasks/ | wc -l
0                                            ← 照抄判据 = 0 命中
$ grep -rnE '^\s*#+\s*(?:\d+\.\s*)?\[SCOPE\+\]' agate-workspace/tasks/ | wc -l
10                                           ← 转义 + 后 = 10（注：-c 口径为行数计数差，见下）
```

Python 逐行口径（无 `grep` 的 `-c` 与 `sed` 差异）[实测]：

```
STATED (unescaped +): 0 命中；且它把 '## [SCOPE]' 判为命中（+ 被当成量词）
INTENDED (escaped +): 15 命中 / 10 个任务
```

该判据**有两处独立缺陷**，任一处都足以使其无法复现 [实测]：

1. **`+` 未转义**：在 ERE 里 `\[SCOPE+\]` 是「`[SCOPE` + 一个或多个 `]`」，**恰好 0 命中**
   （且它会把 `## [SCOPE]` 判为命中，即**换了一个标记**）；
2. **`(?:` 非捕获组不通用**：把 `+` 转义后，GNU `grep -E` 仍只得 **10**（不支持 `(?:`），
   而 **Python 得 15** —— 这正是文档声称的 `15 处 / 10 个任务`。

⇒ **数字（15/10）是对的，但只对 Python 成立；标注的判据在任何 `grep -E` 下都复现不出来。
§9 声称「已改为实测值**并附判据**」，而所附判据无法产出该值。**
这与 L3 的整改方向（A8：声称必须绑定可复现命令）**同族复发**。

**「28 处」还有口径未披露问题** [实测]：

| 扫描面 / 工具 | `^#+ .*\[SCOPE\+\]` 命中 |
|---|---|
| `agate-workspace/tasks/`（`grep`、Python 一致） | **26** |
| `agate-workspace/tasks/` + `docs/` | **28** |
| `agate-workspace/` | 29 |

§3.1 讨论的是「**存量任务**的标题形态」，自然口径是 `tasks/`（= **26**）；28 需要把 `docs/` 并入，
而文档**未声明该口径**。⇒ 同一句里的两个数字（15/10 与 28）用了**两个不同扫描面与两种工具**且都未标注。

**建议**：判据写为 `^\s*#+\s*([0-9]+\.\s*)?\[SCOPE\+\]`（转义 `+`、改用 POSIX 捕获组，`grep`/Python 同为 15）
并明示扫描面；28 改为 26（tasks/）或注明口径。

---

### N4（MEDIUM）：§6 变更清单的计数仍是错的（写 10，实测 14），且仍漏 3 个已跟踪文件

`docs/design-notes/design-scope-plus-declaration-form.md:141`：

> **改动面实测**：`git diff` = **10 个已跟踪文件**（下表前 5 行合并计数）+ 本文件为**新增未跟踪**。

**实测** [实测]：

```
$ git diff --stat | tail -1
 14 files changed, 293 insertions(+), 16 deletions(-)
$ git diff --name-only | wc -l
14
```

14 个已跟踪文件：`CHANGELOG.md`、`agate-workspace/roadmap/roadmap.md`、`agate/WORKFLOW.md`、
`agate/assets/execution-roles/architect.md`、`agate/assets/execution-roles/implementer.md`、
`agate/dispatch-protocol.md`、`agate/phase-cards/P4-implementation.md`、`agate/scripts/check-retrospective.py`、
`agate/scripts/check-scope-resolved.py`、`agate/state-machine.md`、`agate/tests/README.md`、
`agate/tests/fixtures/tag0034_regression_baseline.json`、`agate/tests/unit/test_check_scope_resolved.py`、
`docs/design-notes/README.md`。

§6 表内实际点名 **11** 个（`WORKFLOW`/`dispatch-protocol`/`state-machine` 合并为 1 行，算 3），
**未列**：`agate-workspace/roadmap/roadmap.md`、`agate/assets/execution-roles/architect.md`、
`agate/assets/execution-roles/implementer.md`；而 `architect.md` / `implementer.md` **恰恰是 L2 的两个修复落点**。

另：设计说明文件头 `:5` 仍写「改动面：2 个脚本 + 4 处协议文档 + 1 个测试文件 + 基线刷新」——
这是**整改前**的口径（未含 `CHANGELOG`、`roadmap`、`design-notes/README`、两个角色文件）。

⇒ L5 只完成了「把被点名的两个文件补进表」，**计数与清单完整性仍未达标**。

**建议**：L141 改为 **14**（或写「15 个文件（含本新增文件）」），表内补上 roadmap 与两个角色文件。

---

### N5（LOW-MEDIUM）：L1 的「两个标记边界不对称」只落到 3 处中的 1 处

原报告 L1 的整改方向是「**分开表述两个标记的边界**」，落点为 `WORKFLOW.md:451` /
`dispatch-protocol.md:953` / `state-machine.md:233` 三处。**实测** [实测，`grep -n "不对称"`]：

| 落点 | 是否含「不对称」 | 是否含反引号边界 |
|---|---|---|
| `agate/WORKFLOW.md:451` | ✅ 明写「两个标记的边界**不对称**：`[SCOPE_RESOLVED]` 侧**接受**反引号包裹」 | ✅ |
| `agate/dispatch-protocol.md:953` | ❌（该文件 `不对称` 仅出现在 547/1176 两处**无关**旧文） | ❌ 只写「粗体/引用同样算声明」 |
| `agate/state-machine.md:233` | ❌（全文无此词） | ❌ 只有正则字面量 |

而 `CHANGELOG.md:39-40` 的表述为：

> **3 处协议文档字面引用的旧正则同步**（`WORKFLOW.md` / `dispatch-protocol.md` / `state-machine.md`）
> 并补明可接受形态（含「两个标记边界不对称：`SCOPE_RESOLVED` 侧接受反引号」）；

读起来像是三处都补了形态与不对称说明，**实测为 1/3**（形态说明 2/3）。⇒ 轻微过度声称。

**建议**：`CHANGELOG` 措辞收敛为「`WORKFLOW.md` 补明两侧边界与不对称；另两处仅同步正则」，
或把不对称说明补进另两处。

---

### N6（LOW）：「逐字节相同」与同段自陈的「源码可一个用拼接常量」互斥

设计说明 §4:111「`check-retrospective.py` 持有**逐字节相同**的 `SCOPE_PLUS_RE`」；
`CHANGELOG.md:34` 同。但同节 §4:115 又写「**比对行为而非源码字符串**——源码可一个用**拼接常量**、
一个用**字面量**，只要判定一致即无缺陷」。

**实测** [实测]：两个**正则 pattern 字符串**相同，但**源码文本不同**：

```
scope pattern: '^\\s*(?:[-*+]\\s*)?(?:>\\s*)?(?:\\*\\*|__)?\\[SCOPE\\+\\]'
retro pattern: '^\\s*(?:[-*+]\\s*)?(?:>\\s*)?(?:\\*\\*|__)?\\[SCOPE\\+\\]'
pattern strings identical: True          ← pattern 层相同
# 源码层：scope = _SCOPE_LEAD + r"\[SCOPE\+\]"；retro = r"^…\[SCOPE\+\]"  → 非逐字节相同
```

⇒「逐字节相同」在**源码层**为假。属措辞瑕疵（不影响任何判定），但与同段新增的澄清自相矛盾。

**建议**：改为「`SCOPE_PLUS_RE` 的**pattern 字符串相同**（源码写法不同，见下）」或删去「逐字节」。

---

## 3. 主 Agent 要求的重点核验（逐条应答）

### 3.1 所有数字 —— 全部自跑 [实测]

| 声称 | 出处 | 命令 | 实测 | 判定 |
|---|---|---|---|---|
| `unit 2279 passed` | CHANGELOG:58 | `pytest agate/tests/unit -q -p no:randomly` | `1 failed, 2279 passed, 2 skipped in 174.32s`（唯一 FAIL = `opencode` 不在 PATH，既有环境缺陷） | ✅ |
| `19 passed` | 设计说明 §7:158 | `pytest …/test_check_scope_resolved.py -q` | `19 passed` | ✅ |
| `+9 用例（10→19）` | 设计说明 §6:145；CHANGELOG:36 | `grep -c '^def test_'` | `19`（原 10 ⇒ +9） | ✅ |
| 任务数 `41` | 设计说明 §5；CHANGELOG:44 | `scan.py` glob `tasks/*` | `task_count = 41` | ✅ |
| 转红 `5`（行首反引号） | 设计说明 §3.2:99；CHANGELOG:28；roadmap:78 | `e2e.py` B_lead_backtick | `red=5` = TAG0004/TAG0012/TAG0016/TAG0025/TAG0033 | ✅ |
| 转红 `6`（标题形态） | 设计说明 §3.1:81；CHANGELOG:29；roadmap:78 | `e2e.py` 变体 A / A2 / A3 | **A=4 / A2=2 / A3=6** ⇒ 与自述判据不符 | ❌ **见 N1** |
| 转红 `24`（行中出现） | 设计说明 §3:57；CHANGELOG:31 | `e2e.py` C_inline | `red=24` | ✅ |
| `通过 8→9 / 跳过 33→32 / 失败 0→0` | 设计说明 §5；CHANGELOG:44-46 | `scan.py`（OLD/NEW 双正则）+ `e2e.py` 交叉 | `OLD real-check=8 skip=33`；`NEW real-check=9 skip=32`；`codes {0:41}`；`ONLY_PLUS_RELAXED {0:40,1:1}` = TAG0021 | ✅ |
| `探针 14 个` | 设计说明 §4:115；CHANGELOG:36 | 读 `test_check_scope_resolved.py:248-263` | 14 条 | ✅ |
| `regression+integration 195 passed` | CHANGELOG:59 | `pytest agate/tests/regression agate/tests/integration -q` | `195 passed in 47.07s` | ✅ |
| `consistency 0 ERROR / 386 WARNING` | 设计说明 §7:165；CHANGELOG:60 | `check-protocol-consistency.py` | `仅有 386 个 WARNING，无 ERROR。` | ✅ |
| `ruff 全绿` | 设计说明 §7:166 | `ruff check agate/` | `All checks passed!` | ✅ |
| 用例总数（交叉校验） | — | `count-tests.sh` | `总计：2499 个测试用例`（原报告快照为 2497 ⇒ **+2**，与新增 `sc_15`/`sc_16` 一致） | ✅ |
| 负向控制 `3 条转红`（sc_8/9/10） | 设计说明 §7:160 | 副本 `mutate_m1.py`（两脚本均退回原版，单跑 scope 测试） | `3 failed, 16 passed` = sc_8/sc_9/sc_10 | ✅ |
| 负向控制 `2 条转红`（sc_10/11） | 设计说明 §7:161 | 副本 `mutate2.py plus_only` | `2 failed` = sc_10/sc_11 | ✅ |
| 负向控制 `1 条转红`（sc_11） | 设计说明 §7:162 | 副本 `mutate2.py resolved_no_backtick` | `1 failed, 18 passed` = sc_11 | ✅ |
| 「两者结论一致」（§5 正则注入 vs 真实脚本） | 设计说明 §5:125 | `scan.py` vs `e2e.py` baseline | 均为 checked=9 / skip=32 / red=0 | ✅ |

> **说明（口径）**：设计说明 §7 的「正则退回原版 → 3 条转红」指**单跑** `test_check_scope_resolved.py`；
> 我复现为 3（sc_8/9/10）✅。若**两文件合跑**则为 4 failed（多 `sc_14`——两脚本同时退回原版时
> `sc_14` 的 14 个探针里含新语义探针，分类与期望不符）。设计说明**未标注该口径差异**，
> 但已在 §7 明写「单跑 `test_check_scope_resolved.py`」，故不判缺陷 —— 属 [推断]+[实测] 已澄清。

### 3.2 `roadmap.md` 的 `RM-AG0077` 行是否 9 列 + 全 roadmap 无列数异常 + `_check_roadmap_done` 可用 [实测]

**列数复核（用 `check-gate.py` 自己的判据）**：

```python
_ROADMAP_EXPECTED_COLS = 9            # check-gate.py:1354
# 对 ^\|\s*RM- 开头的每一行按 line.split("|") 判 len != 9
RM rows: 92   anomalous: 0   []
```

⇒ **全 roadmap 92 个 RM 行，0 个列数异常**。`roadmap.md:78` 本体：`len(line.split("|")) == 9`（✅ 9 列），
含 **1 处 `&#124;`**（用于展示正则中的字面竖线）——主 Agent 自陈的「9 列 → 10 列 → `&#124;` 修复」**已确认修复到位**。

**`_check_roadmap_done` 功能复核（正/负/异常三态）** [实测]：

```
synth 9-col non-done          -> ('RM-AG9999', 'scheduled')     ← 正常阻断路径可达
synth 9-col done              -> None                           ← 正常放行
synth 10-col (literal pipe)   -> None | warn: 'GATE WARNING: roadmap 第 3 行列数异常（10，应为 9）…'
真实 roadmap: TAG0039/TAG0034/TAG0021/TAG0004 -> None（均无 done 反查异常）
真实 roadmap 上的异常行告警 stderr 为空
```

⇒ `_check_roadmap_done` **正常工作**：非 done 行能被检出、错位行有 WARNING 且不回显 cell（守住 BDD-20）。
**M6 的自伤事故（列数）已闭环。**

**但**：`roadmap.md:78` 复制了 N1 的错误数字「纳入会新增 6 个任务转红」+ `TAG0008` 的「真声明」（N2）。

### 3.3 两条「刻意排除」边界锁是否**非真空** [实测，变异测试]

副本 `cp -r agate .agate-tmp/rerev/copy/agate`，变异真实 `_SCOPE_LEAD`，**每次同一次 bash 调用内建→用→清**：

| 变异 | 操作 | 结果 | 判定 |
|---|---|---|---|
| **A**（锁 `sc_15`） | `_SCOPE_LEAD` 追加 `(?:#{1,6}\s+)?(?:\d+\.\s*)?`（**吃掉 `N. ` 编号前缀**） | `-k sc_15` → `1 failed`；全文件 `1 failed, 18 passed` | ✅ **非真空** |
| **B**（锁 `sc_16`） | `_SCOPE_LEAD` 追加反引号分支 `(?:\*\*\|__\|\`)?` | `-k sc_16` → `1 failed`；全文件 `3 failed, 16 passed`（sc_13/sc_14/sc_16） | ✅ **非真空** |
| **C**（锁 `sc_14`） | 只把 `check-retrospective.py` 的 `SCOPE_PLUS_RE` 退回原版（两脚本判据分叉） | `-k sc_14` → `1 failed`；全文件 `1 failed, 18 passed` | ✅ **非真空** |
| 基线 | 原样 | `19 passed` | — |

三处变异均以 `ast.parse` 预检过语法（`syntax OK`），排除「变异把脚本弄坏导致假红」。
⇒ **`sc_14` / `sc_15` / `sc_16` 三个守护均非真空**，且 `sc_15`/`sc_16` 与其 docstring 声称的
「将来有人放宽 `_SCOPE_LEAD` 覆盖标题/反引号 → 此用例转红」**行为一致** ✅。

> ⚠️ **方法学自陈（如实登记）**：本项第一次尝试时，`python3 - <<'PY'` 的 heredoc 转义把引号写成了
> 字面 `\"`，导致变异**未生效**（脚本 `AssertionError: anchor not found`），而我误把未变异的基线
> 当成变异结果（当时输出 `19 passed`）。我据此改为**file-based 变异脚本**（`mutate.py`）并加
> `ast.parse` 预检，重跑得到上表真实结果。**该失败尝试未改动被评审仓库**（仅在副本内）。

### 3.4 `test_sc_14` 行为等价守护是否仍非真空 [实测]

✅ **非真空**，见上表变异 **C**（两脚本判据分叉 → `sc_14` 转红）。
另实测两脚本 `SCOPE_PLUS_RE.pattern` 字符串**完全相同**（`pattern strings identical: True`），
且 14 个探针覆盖声明（裸/列表符 `- * +`/缩进/引用块/粗体 `**`/下划线 `__`）与提及（行中/反引号/无方括号/异标记）两类。

### 3.5 是否有新引入的错误声称（A8） [实测]

**有 3 处**（N1 的 6、N2 的 `TAG0008` 真声明、N3 的不可复现判据），另 1 处过度声称（N5）。
**L3 原项（「22 个任务」）已确认删除**：`grep "22 个任务"`（设计说明 + CHANGELOG）= **0 命中** ✅。

### 3.6 是否又在别处引入「同族缺陷」（表格单元格内写含 `|` 的正则） [实测]

**markdown 表格单元格层面：未复现该缺陷。**

- `roadmap.md:78`：9 列 ✅，字面竖线已用 `&#124;` 转义 ✅；
- 扫描**全部本次改动/新增的 `.md`**（fenced-code 与 inline-code 感知），
  表格行内**因内联代码含竖线而改变列数**的情况：**未在 `roadmap.md` / `CHANGELOG.md` / 设计说明 /
  `design-notes/README.md` / `tests/README.md` 的**新增行**中出现**。
- `git diff -U0 | grep '^+|'` 新增表格行仅 3 行：roadmap（7 数据列 ✅）、`tests/README.md`（用例数 19 ✅）、
  `design-notes/README.md`（登记行 ✅）——**列数均与各自表头一致**。

> 附带发现（**非本次引入，属存量**）：扫描器在 `agate/WORKFLOW.md:320/322/326`、
> `agate/dispatch-protocol.md:872-878` 的**既存表格**中检出内联代码内的字面 `|`。
> 这些行**未被本次 diff 触碰** [实测：不在 `git diff` 内]，且它们不在 `_check_roadmap_done` 的解析面，
> ⇒ **不作为本次整改问题**，仅登记为存量观察 [推断：是否影响渲染未验证]。

⇒ 主 Agent 在文档表格层**没有**再次踩同族的 `|` 缺陷；但其**修复内容本身**（放宽后的正则）
在 roadmap 行的转义处理是**正确**的。

---

## 4. 逐项 A1-A8 结论（复审视角）

| # | 审查项 | 结论 |
|---|---|---|
| A1 | 文档→脚本对齐 | **MISALIGNED（轻）**：`WORKFLOW.md:451` 已与脚本一致并声明不对称；但 `dispatch-protocol.md:953`/`state-machine.md:233` 未承接不对称边界（N5）；设计说明 §3.1 的「6」与其自述判据不符（N1） |
| A2 | 脚本→文档对齐 | **ALIGNED**：脚本判据（`_SCOPE_LEAD` + RESOLVED 反引号分支）与 `WORKFLOW.md:451` 逐字符一致；`check-scope-resolved.py` 常量注释已登记未覆盖面与代价 |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**：原报告的 3 项遗漏（`design-notes/README.md`、`implementer.md`、`architect.md`）**均已回填**；`roadmap.md` 已回写 |
| A4 | 测试覆盖 | **ALIGNED**：19 passed 实测；三组负向控制 + 两条边界锁 + `sc_14` 守护**全部变异转红**（§3.3） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW（轻）**：0 任务变红、无破坏性变更、CHANGELOG 已标注；但错误声称已扩散到 roadmap 与 CHANGELOG（N1/N2），需回改 |
| A6 | 锚点表覆盖 | **ALIGNED**：未新增/改名脚本；`SCOPE_RESOLVED` 关键词仍在脚本内；consistency 0 ERROR / 386 WARNING 实测 |
| A7 | 设计原则一致性 | **ALIGNED**：与 ADR-002（可判定性）/004（安全网分层）/011（引导型工具）/013（gate 生产者无关）方向一致；「只认形态、不猜语义」的边界与 `design-claim-evidence-binding.md` v1/v2 先例同构 |
| A8 | 声称-命令绑定 | **MISALIGNED**：**3 处量化声称不可由所附判据复现/不符**（N1 的 6、N3 的 15/10 与 28 判据、N2 的 `TAG0008` 真声明）——按 A8 规则须改数或删声称 |

---

## 5. 最终判定

### **NEEDS-REVISION**

**理由**：13 项必须修复项中 9 项完全修复、3 项部分修复、1 项修复不当；**无 HIGH**——
脚本本体（`check-scope-resolved.py` / `check-retrospective.py`）逻辑、19 条测试、
三条边界锁与同源守护、基线刷新、roadmap 列完整性**均经实测正确**。
但整改**新引入 4 处声称层缺陷**（N1/N2/N3/N4），其中 **N1、N2 各已扩散到 3 个文件**
（设计说明 + CHANGELOG + roadmap），而本次 hotfix 的**全部价值就在文档准确性**上。
按 A8「无法给出命令 / 与判据不符的声称应改正或删除」，这些必须回改后重审。

**是否可提交**：**不建议在回改 N1-N4 之前提交**（N5/N6 可作为可选 nit 一并处理）。
脚本与测试层已具备提交质量；**阻塞点全部在文档/声称层**，且改动面小、可快速回改。

**回改清单（按优先级）**：

| 优先 | 项 | 落点 | 动作 |
|---|---|---|---|
| 1 | **N1** | ~~设计说明 §3.1~~（**已改**）；**`CHANGELOG.md:29`；`roadmap.md:78`** | 剩余两处「6 个任务转红」→ **4**，名单改为 `TAG0012`/`TAG0014`/`TAG0023`/`TAG0025` |
| 1 | **N2** | ~~设计说明 §3.1:82、§3.2:103；`test_check_scope_resolved.py:217`~~（**已改**）；**`CHANGELOG.md:30`；`roadmap.md:78`** | 剩余两处移除 `TAG0008` 的「真声明」定性（改为容器标题） |
| 2 | **N3** | 设计说明 §3.1:69-70、§9:194-195 | 判据改为 `^\s*#+\s*([0-9]+\.\s*)?\[SCOPE\+\]`（转义 `+` + POSIX 捕获组，使 `grep` 与 Python 同为 15）；28 改为 26（tasks/）或注明扫描面 |
| 2 | **N4** | 设计说明 §6:148（及文件头 :5） | 「10 个已跟踪文件」→ **14**；表内补 `roadmap.md` / `architect.md` / `implementer.md` |
| 3 | **N5** | `CHANGELOG.md:39-40`（或补另两处文档） | 收敛「3 处…补明可形态与不对称」的表述，或把不对称说明补进 `dispatch-protocol.md` / `state-machine.md` |
| 3 | **N6** | 设计说明 §4:111；`CHANGELOG.md:34` | 「逐字节相同」→「pattern 字符串相同」 |

**复审触发条件**：上述 1-2 级项回改后，重跑
`pytest agate/tests/unit/test_check_scope_resolved.py -q`（应仍 19 passed）+
`check-protocol-consistency.py`（应仍 0 ERROR）+ 复核 `roadmap.md` 列数（应仍 0 异常），即可判 APPROVED。

---

## 6. 附录：本次复审的命令索引（可复核载体）

| 用途 | 载体 | 说明 |
|---|---|---|
| 存量对账（41 任务 × OLD/NEW/单侧 + 三变体转红数） | `.agate-tmp/rerev/scan.py` | 注入正则、逐任务求值 |
| 标题形态变体算术（A/A2/A3） | `.agate-tmp/rerev/scan2.py` | 分离「限定标题」与「标题行内任意」 |
| **真实脚本端到端**转红数（权威口径） | `.agate-tmp/rerev/e2e.py` | 复制 `agate/` → 改 `_SCOPE_LEAD` → 跑真脚本 41 次 → 删副本 |
| 边界锁变异（A/B/C） | `.agate-tmp/rerev/mutate.py` | 含 `ast.parse` 语法预检 |
| 负向控制变异（3/2/1） | `.agate-tmp/rerev/mutate2.py` | revert_both / plus_only / resolved_no_backtick |
| 真 M1（两脚本均退回原版） | `.agate-tmp/rerev/mutate_m1.py` | 单跑 = 3 failed |
| 反引号证据站点枚举 | `.agate-tmp/rerev/evid.py` | 按真实 `_scan_scope_plus` 语义（含 SKIP 与 AGATE_CARD 剥离） |
| 判据可复现性 | `.agate-tmp/rerev/patcheck.py` | 证明未转义 `+` 命中 0 |

**scratch 清理**：全部变异副本 `.agate-tmp/rerev/copy/`、`.agate-tmp/rerev/e2e/` 已在
**各自同一次 bash 调用内** `rm -rf` 并打印 `copy removed: YES` / `e2e scratch removed: True` [实测]。
保留的仅上表 **scratch 脚本**（无仓库源码副本），位于 `.agate-tmp/`（`git check-ignore` 确认被忽略：
`.gitignore:32:.agate-tmp/`）。**被评审的改动集未被触碰、未被写入。**
