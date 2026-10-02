---
review_date: 2026-10-02
reviewer: protocol-alignment-review
status: needs-revision
change_summary: 复审「正文标记判据单源化」整改轮——HIGH-1 等价性修复、mk_6a/mk_6b 守护、MEDIUM-2/3 表述与数字更正、LOW-4/5/6 收口
files_changed: [CHANGELOG.md, agate/WORKFLOW.md, agate/rules/markers.yaml, agate/rules/schema/markers.schema.json, agate/scripts/README.md, agate/scripts/agate-mark.py, agate/scripts/agate_markers.py, agate/scripts/check-protocol-consistency.py, agate/scripts/check-retrospective.py, agate/scripts/check-scope-resolved.py, agate/scripts/check-yaml-schema.py, agate/tests/README.md, agate/tests/unit/_rules_test_utils.py, agate/tests/unit/test_marker_single_source.py, docs/design-notes/README.md, docs/design-notes/design-marker-single-source.md, docs/design-notes/design-scope-plus-declaration-form.md]
---

# 协议-脚本对齐审查（正文标记单源）—— **复审**

> **审查方式说明**：本报告严格区分「**我已实测**」与「**我推断**」。每条数字结论均附**实际跑过的命令**与**真实输出**。
> 所有变异测试在**一次性副本** `<仓库根>/.agate-tmp/mut*/` 上做，「建→用→清」均在同一次 bash 调用内完成；
> 仓库内被评审文件**全程只读**（未执行 `git checkout/restore/reset/stash/clean/add/commit/switch -f`，未编辑/删除被评审文件）。
> 唯一写入路径为本报告文件（写前已 `ls` 确认不存在同名文件，符合 BDD-8）。
>
> **本轮为复审（re-review）**：审查对象 = 上一轮 `NEEDS-REVISION` 的**整改**是否到位、有无**新引入问题**。
> 上一轮报告：`docs/reviews/agate-alignment-review-2026-10-02-marker-single-source.md`。
>
> **⚠️ 取证口径（重要，本轮中途更正）**：被评审方在**本复审进行期间仍在编辑**该改动集——我只读，不介入；
> 但由此产生一个**必须显式声明的取证问题**：`docs/design-notes/design-marker-single-source.md` 的状态为 **`AM`**
> （已暂存 **+ 工作区另有未暂存修改**，该次修改 mtime = `2026-10-02 18:28:16`，落在本会话内）。
> **`git commit` 只会带上暂存内容** ⇒ 凡是「整改后原文」的引用，我**一律以 `git show :<path>`（暂存版）复核为准**，
> 并在**逐条标注「已暂存 / 仅工作区」**。此差异恰好构成本轮最重要的发现（N-4）。

---

## 复审结论汇总

| 上一轮发现 | 复审判定 |
|---|---|
| **HIGH-1** `pattern("DESIGN_GAP")` 与 `agate_common.count_design_gap` 不等价（2.05×）+ 无等价守护 | **已修复**（等价性 116/116、差异 0；`mk_6a`/`mk_6b` 已证非真空） |
| **MEDIUM-2** `mk_3` 只覆盖「判据过严」方向；§3.5「最强一条/结构上不可能」表述过强 | **已修复**（§3.5 已明确收窄 + 声明两方向都需守护） |
| **MEDIUM-3** §1.3「PR#387 改动 14 个已跟踪文件」实为 18 | **已修复**（18 已复现，14 已重新定性为「形态同步面」并附 28% 联动数） |
| **LOW-4** §10.4「CHECK9-coverage 新脚本已覆盖」绑定错判据 | **已修复**（已改为正确判据并显式说明扫描面） |
| **LOW-5** `design-scope-plus-declaration-form.md` 未加前向指针 | **已修复**（文件头已加「后继（2026-10-02）」块） |
| **LOW-6** §3.3 示例 `agate-mark.py SCOPE+ "…"` 与无参标记拒参冲突 | **已修复**（示例已改为无参形态并标注 exit 1） |
| **A8** 若干数字不可复现 | **部分修复**：「45 种」✅ 本次按指定口径**复现成功**；「18 文件」✅；「116/116、差异 0」✅；「2311/195/2531/32」✅；**「存量 3 处跨行」❌ 未更正（实为 11）** |
| **新引入 N-4** 🚨 | **载荷点更正块只存在于工作区、未暂存**；暂存版三处（§10.3(2)/CHANGELOG/docstring）**同向把 HIGH-1 归因于 `(?!\w)`**，与实测相反 |

**终审判定**：**`NEEDS-REVISION`（轻量收口）** —— **修 N-4 三项后即可提交**（详见文末「总体判定」与「可提交的最小条件」）。

---

## 一、HIGH-1 是否真修好 —— **已修复（我已实测）**

### 1.1 全仓逐文件等价（首要证据）

上一轮要求在**全仓** `agate-workspace/tasks/*/*.md` 上对账 `pattern("DESIGN_GAP")` vs `agate_common.count_design_gap(..., allow_blockquote=True)`：

```
$ python3 <逐文件: common=count_design_gap(t,True)[0] vs new=Σ pattern("DESIGN_GAP").finditer(t)>
files scanned: 1564
agate_common total (P7口径 allow_blockquote=True): 116
new pattern total : 116
DIFF FILES: 0
```

✅ **完全相等**：两侧总数 **116 vs 116**，**差异文件数 0**。上一轮的 2.05× 偏离已消除。

### 1.2 逐形态核验（**我已实测**，全部 OK）

```
probe                                           cP7  cP4  NEW  match
'[DESIGN_GAP]'                                    0    0    0  OK      ← 应 False ✅
'[DESIGN_GAP: x]'                                 1    1    1  OK      ← 应 True  ✅
'[DESIGN_GAP_REVIEWED: x]'                        0    0    0  OK      ← 应 False ✅
'**[DESIGN_GAP: x]**'                             0    0    0  OK      ← 粗体
'> [DESIGN_GAP: x]'                               1    0    1  OK      ← 引用（P7 口径）
'- [DESIGN_GAP: x]'                               1    1    1  OK
'  [DESIGN_GAP: x]'                               1    1    1  OK
'> - [DESIGN_GAP: x]'                             1    0    1  OK
'[DESIGN_GAP: a\nb]'                              1    1    1  OK      ← 跨行
'[DESIGN_GAP: 跨多行的长参数\n继续第二行]'                1    1    1  OK      ← 跨行（中文）
'[DESIGN_GAPx: y]'                                0    0    0  OK
'text [DESIGN_GAP: x]'                            0    0    0  OK      ← 行中
```

**关键三项**（任务书点名）：
- `[DESIGN_GAP]` → `NEW search -> False` ✅（冒号必填生效）
- `[DESIGN_GAP: x]` → `NEW search -> True` ✅
- `[DESIGN_GAP_REVIEWED: x]` → `NEW search -> False` ✅（**前缀吞并已消除**）

另：文档 §10.3(2) 声称「逐形态 **8/8** 等价」——**我已实测 8/8 OK**。文档「61 行 REVIEWED 被误计为 DESIGN_GAP」——实测 P7 侧 `[DESIGN_GAP_REVIEWED` 行数 = **61** ✅。

**P7 口径复现上一轮基线**（我已实测）：

```
=== HIGH-1 RESTORED state（变异还原）===   P7 DESIGN_GAP: common=59 new=121 ratio=2.05x
=== CURRENT (fixed) state ===              P7 DESIGN_GAP: common=59 new=59  ratio=1.00x
```

✅ 与上一轮报告的 **59 vs 121（2.05×）** 逐字复现，现为 **59 vs 59**。

### 1.3 ⚠️ 反推修复声称：**您的「主因」说法在被评审文档内部自相矛盾**

您在任务书中称：「**前缀吞并靠 `(?!\w)` + 冒号必填共同解决**」。我做了**分约束变异 2×2 矩阵**（一次性副本，同一次 bash 调用内建→用→清）：

```
=== colon_required=yes  name_boundary=yes ===   common=116 new=116 difffiles=0   DG_REVIEWED_match=False
=== colon_required=yes  name_boundary=no  ===   common=116 new=116 difffiles=0   DG_REVIEWED_match=False
=== colon_required=no   name_boundary=yes ===   common=116 new=124 difffiles=7   DG_REVIEWED_match=False
=== colon_required=no   name_boundary=no  ===   common=116 new=195 difffiles=36  DG_REVIEWED_match=True
```

| colon 必填 | `(?!\w)` | 全仓 new | 差异文件 | `[DESIGN_GAP_REVIEWED: x]` 命中 |
|---|---|---|---|---|
| 有（现状） | 有 | **116** ✅ | 0 | False |
| 有 | **去掉** | **116** ✅ | **0** | **False** |
| **去掉** | 有 | **124** ❌ | 7 | False |
| **去掉** | **去掉** | **195** ❌ | 36 | **True** |

**⇒ 结论（我已实测）**：

1. **真正的载荷点是「冒号必填」**，不是 `(?!\w)`。在冒号必填存在的前提下，**单独去掉 `(?!\w)` 对全仓计数、差异文件数、`DESIGN_GAP_REVIEWED` 命中三者**——**全部零影响**（116/116、0、False）。
2. **`(?!\w)` 是防御性冗余**：它只在「冒号也可选」时才有可观测作用。而**恰好防护 `DESIGN_GAP_REVIEWED` 吞并的是冒号必填**——因为 `[DESIGN_GAP_REVIEWED:` 中 `DESIGN_GAP` 之后紧跟的是 `_`，**不是 `:`**，故被冒号约束直接挡住。
3. 因此您的表述「前缀吞并靠 `(?!\w)` + 冒号必填**共同**解决」**不准确**：冒号必填**单独**即已充分。

**⚠️ 但请注意——有人已在设计文档里写过与我的实测完全一致的更正**（工作区 `design-marker-single-source.md` 的未暂存编辑）：

> | 只去 `(?!\w)` | **116** | 仍等价 ⇒ **边界在本语料上非载荷** |
> | 只去「冒号必填」 | **124** ❌ | 偏多 8 ⇒ **冒号必填才是载荷点** |
>
> ⇒ **主因是「冒号必填」**……`(?!\w)` 是**防御性冗余**……**不得把冗余说成主因**。

我的独立实测**证实这段更正**（116 / 116 / 124 三个数字逐字命中）。

**🚨 但该更正不在提交范围内 —— 见下方 N-4（本轮最重要的新发现）。**

### 1.5 🚨 新引入问题 N-4（**MEDIUM**）：机制更正确实存在，但**只存在于工作区、未暂存**

**发现经过（如实上报）**：我在复审中途 `git status --short` 发现 `docs/design-notes/design-marker-single-source.md` 的状态是 **`AM`**（已暂存 + **工作区又有未暂存修改**），其 mtime 为 `2026-10-02 18:28:16` —— **落在本次复审会话进行期间**。即：**被评审方在我复审过程中仍在编辑该文件**。

**我必须据此更正自己的取证口径**：我前文引用的「整改后原文」中，**只要来自该文件，就可能读的是工作区内容而非暂存内容**。而 **commit 只会带上暂存内容**。故我重新**以 `git show :<path>`（暂存版）为准**逐条复核，结果如下：

| 复核对象 | 暂存版（= 将提交） | 工作区版 | 判定 |
|---|---|---|---|
| §10.3(2) **载荷点更正块**（「主因是冒号必填 / `(?!\w)` 防御性冗余」） | ❌ **不存在** | ✅ 存在 | **未进入提交** |
| §10.3(2) 修复措辞 | 「**修复**：① 本体后加 `(?!\w)` 名称边界；② `required_text` 分支冒号**必填**。」 | 「① 冒号**必填**；② …边界」+ 更正块 | 暂存版**次序相反、无更正** |
| CHANGELOG 同项 | 「**修复**：本体后加 `(?!\w)` 名称边界 + `required_text` 分支冒号**必填**。」 | 同左（未改） | 暂存版**并列、未标主次** |
| §3.5 `mk_6a`/`mk_6b` 两行 | ✅ 存在 | ✅ 存在 | 已提交 |
| MEDIUM-2 §3.5 收窄段 | ✅ 存在 | ✅ 存在 | 已提交 |
| LOW-4 §10.4 CHECK9 措辞 | ✅ 已更正 | ✅ | 已提交 |
| §1.3 18 文件 / 14 形态同步面 / 28% | ✅ 已更正 | ✅ | 已提交 |

**⇒ 后果**：若**现在**提交，进入 commit 的文档会写：

- `design-marker-single-source.md` §10.3(2)：**「① 本体后加 `(?!\w)` 名称边界；② 冒号必填」**
- `CHANGELOG.md`：「**本体后加 `(?!\w)` 名称边界 + `required_text` 分支冒号必填**」（并列，未标主次）
- `agate_markers.py:110-114` docstring：**「名称边界（HIGH-1 修复）……否则 `DESIGN_GAP` 会吞并 `DESIGN_GAP_REVIEWED`」**

而**三者都与实测不符**：`(?!\w)` **不是**吞并的防护（**冒号必填**才是），去掉 `(?!\w)` 在全仓**零影响**（116/116、差异 0、`DESIGN_GAP_REVIEWED` 不命中）。**恰好防护吞并的是冒号必填**——因为 `[DESIGN_GAP_REVIEWED:` 里 `DESIGN_GAP` 后紧跟 `_` 而非 `:`。

**性质定为 MEDIUM（而非 LOW）的理由**：这不是「措辞不精确」，而是**改动集内三处同向的错误因果声称**，且**作者本人已写出正确版本、只是没暂存**。它直接落在**上一轮 HIGH-1 的收口项**上——上一轮明确要求「更正 §10.3(2) / CHANGELOG 中『不会改变既有行为』的声称」。**该声称的实质已随代码修复而消解，但因果归属的更正没有进提交**，读者会据此误以为 `(?!\w)` 是载荷点，从而在下次改动中**删掉真正起作用的约束**（若误信 `(?!\w)` 是关键而保留它、放开冒号，判据立即退化为 124/195）。

**建议（最小改动，可当场完成）**：`git add docs/design-notes/design-marker-single-source.md`（把已有更正纳入暂存），并**同步改**：
1. `CHANGELOG.md` 该行 → 「**修复**：① `required_text` 分支冒号**必填**（**载荷点**）；② 本体后加 `(?!\w)`（防御性冗余，防未来 `DESIGN_GAP_XXX` 型前缀标记）。」
2. `agate_markers.py:110-114` docstring → 同口径（现称「名称边界（HIGH-1 修复）……否则会吞并」，**与实测相反**）。

**⇒ 这三处（N-4）是本轮唯一需要「修一下再提交」的项。** 其余两项 NIT（N-2/N-3）纯叙述，可留后续。

### 1.4 ⚠️ 新引入问题 N-1（LOW）：**源码 docstring 与设计文档结论相反**

`agate/scripts/agate_markers.py:110-114` 仍写着：

```python
**⚠️ 名称边界（HIGH-1 修复，2026-10-02）**：本体后必须紧跟 `(?!\w)` ——
否则 `DESIGN_GAP` 会**吞并** `DESIGN_GAP_REVIEWED`（`_` 满足 `[^a-z]`）。
```

而设计文档 §10.3(2)（同一改动集、同一日期）明确写「**主因是「冒号必填」**……`(?!\w)` 是**防御性冗余**……**不得把冗余说成主因**」。

**我的实测站在设计文档一侧**（见 §1.3 矩阵：冒号必填在时，去掉 `(?!\w)` 零影响）。⇒ **同一改动集内两处对同一因果给出相反陈述**，且**源码那处是错的那一处**。

**性质**：LOW（注释/文档，不影响判据行为；判据本身正确）。**建议**：把 `agate_markers.py:110-114` 的措辞对齐 §10.3(2)——说明冒号必填为主因、`(?!\w)` 为对未来 `DESIGN_GAP_XXX` 型前缀标记的防御性冗余。**不阻断提交**。

---

## 二、`mk_6a` / `mk_6b` 是否非真空 —— **已证非真空（我已实测，双向）**

按要求：把 `agate_markers.py` + `markers.yaml` **退回 HIGH-1 状态**（去 `(?!\w)` + `params: required_text`→`optional_text`），确认两者**转红**；还原确认**转绿**。全程在一次性副本 `$TMP` 内，并以 `AGATE_ROOT` 指向副本、副本旁配 `agate-workspace/tasks` 语料：

```
=== STEP 1: BASELINE (unmutated) — expect GREEN ===
2 passed, 30 deselected in 0.57s                                  ← mk_6a/mk_6b 绿

=== STEP 2: REVERT to HIGH-1 state ===
  marker.py has boundary: False                                   ← 变异已落盘
  DESIGN_GAP params: params: optional_text                        ← 变异已落盘

=== STEP 3: rerun mk_6 on HIGH-1 state — expect RED ===
E  AssertionError: mk_6b 违反（DESIGN_GAP 判据与 agate_common 不等价）：总计 old=116 new=195
E      P7-consistency.md: agate_common=8 pattern=16
E      P4-implementation-core.md: agate_common=1 pattern=2
E      ...
FAILED test_mk_6a_registered_markers_are_mutually_exclusive
FAILED test_mk_6b_design_gap_matches_agate_common_on_real_corpus
2 failed, 30 deselected in 0.57s

=== STEP 4: full file on HIGH-1 state ===
FAILED test_mk_6a_... ; FAILED test_mk_6b_...
2 failed, 30 passed in 0.69s

=== CLEANUP ===  removed: OK
```

✅ **`mk_6a` 与 `mk_6b` 均非真空**：HIGH-1 状态下**双双转红**（且 `mk_6b` 报出 `116 → 195` 的真实偏离，与 §1.3 矩阵第 4 行一致），还原后转绿。变异经 `grep`/断言**回显确认已落盘**，非空跑假红。

**两项守护的判据分工亦已核实**（我已实测读源码）：
- `mk_6a`：对每对已登记标记 (A,B)，用 B 的 `render()` 产物测 A 的 `pattern()` —— 抓「前缀吞并/重叠」。
- `mk_6b`：全仓逐文件 `count(text,"DESIGN_GAP")` vs `count_design_gap(text,True)`，要求**完全相等** —— 抓「与既有消费方不等价」。

⇒ 上一轮 HIGH-1 的收口条件「必须补一条等价回归断言」**已兑现**。

---

## 三、其余整改逐条核验

### MEDIUM-2 —— **已修复**

上一轮：`mk_3` 只覆盖「判据过严」，§3.5 称其「最强一条」「结构上不可能」表述过强。

**整改后原文**（`design-marker-single-source.md:283-285`，我已实测引用）：

> **⇒ `mk_3` 覆盖「生成器产出判据不认」这一方向（过严），但不覆盖「判据过宽」**——
> 后者（判据命中不属于它的东西）由 `mk_6a`/`mk_6b` 承担。**两个方向都需要，缺一不可**
> （HIGH-1 正是「判据过宽」且当时无守护）。

✅ **表述已收窄**（明确限定 `mk_3` 的覆盖方向），且**明确声明两方向都需守护**（正是上一轮的要求）。§3.5 用例表亦新增 `mk_6a`/`mk_6b` 两行。CHANGELOG 同步（`:63-64`「后者由 `mk_6a`/`mk_6b` 承担。已收窄文档表述：两方向都需守护，缺一不可」）。

**✅ 且该守护已由我实测证明有效**（见第二节：HIGH-1 状态下 `mk_6a`/`mk_6b` 确实转红）——这正是「判据过宽」方向的机械守护，上一轮的「盲区」已消除。

### MEDIUM-3 —— **已修复**

上一轮：§1.3「PR#387 改动 14 个已跟踪文件」实为 **18**。

**实测命令**：

```
$ git show --name-only --format="" 6101a9e | wc -l
18
$ git show --name-only --format="" 6101a9e | grep -v '^$' | wc -l
18
```

✅ **18 复现**。**整改后原文**（`design-marker-single-source.md:45` / `:54`）：

> 只改 `[SCOPE+]` **一个**标记的形态，commit `6101a9e` 实测改动 **18 个已跟踪文件**（`git show --name-only 6101a9e | wc -l`，含 3 份评审报告 + 1 份设计说明）
>
> （另有 3 份评审报告 + 1 份设计说明共 4 个文件，属**记录产物**而非形态同步面 ⇒ commit 总数 18，形态同步面 14。）

✅ **14→18 已更正**，且**「14」被重新定性**为「形态同步面」而非总数（并保留 4+6+4=14 的明细表，明细真实）。**漏改率联动亦已更正**（`:58`）：

> **⇒ 形态同步面 14 处里漏了 5 处 = 漏改率 36%**（按 commit 总数 18 计为 28%）。

✅ 两口径**并列给出**并标明分母，符合上一轮「须联动重算」的要求。**判定：修复到位**（口径选择属设计表述自由，关键是分母与数字绑定且已声明）。

### LOW-4 —— **已修复**

上一轮：§10.4 把「新脚本已覆盖」绑定到 `uncovered_gate_scripts()` 返回空（该函数只 glob `check-*.py`，两新脚本不在扫描面）。

**整改后原文**（`:453`）：

> | CHECK9-coverage | 新脚本已进 CHECK9 锚点表（**注意**：`uncovered_gate_scripts()` 只 glob `check-*.py`，两个新脚本**不在其扫描面**，它返回空**不构成**覆盖证据——真实覆盖由锚点表成立） |

✅ 表述已绑定到**真实判据**（锚点表），并**显式说明**原判据的扫描面局限。

**我独立核实两件事**：
1. 扫描面确实只含 `check-*.py`：
   ```
   gate_scripts = [ ... for p in scripts_dir.glob("check-*.py") if p.is_file() ]
   for extra in ("pre-commit-gate.sh", "pre-commit-gate.py", "ci-gate-backstop.py"): ...
   ```
   ✅ 确认 `agate_markers.py` / `agate-mark.py` **不匹配** `check-*.py`。
2. 锚点表**确实含**这两条（这才是真覆盖证据）：
   ```
   SCRIPT_ALIGNMENT_ANCHORS contains agate_markers.py: True | agate-mark.py: True
   ```
   ✅ **真实覆盖成立**。CHEK9 主逻辑另实测 **0 ERROR**（见第五节）。

### LOW-5 —— **已修复**

**实测**（`design-scope-plus-declaration-form.md:4-9`）：文件头已加：

> **⚠️ 后继（2026-10-02）**：本文件讨论的形态判据**已单源化**——形态权威源迁移至
> `agate/rules/markers.yaml`，消费方经 `agate_markers.py` 取值。本文件保留为**决策记录与代价登记**
> （未覆盖面的量化取舍），**判据以 markers.yaml 为准**。见 `design-marker-single-source.md`。

✅ 前向指针已加，且**明确「判据以 markers.yaml 为准」**，历史记录与现行判据的从属关系无歧义。

### LOW-6 —— **已修复**

**整改后原文**（`design-marker-single-source.md:228-230`）：

```bash
python3 agate/scripts/agate-mark.py SCOPE+          # 无参标记：**不接参数**（给了会 exit 1）
#   → [SCOPE+]
```

**实测对照**（我已实测）：

```
$ python3 agate/scripts/agate-mark.py SCOPE+
[SCOPE+]                      ← exit_noargs=0   ✅ 与文档一致
$ python3 agate/scripts/agate-mark.py SCOPE+ "createEntry..."
GATE ERROR: 标记 SCOPE+ 不接受参数（params=none），但收到 'createEntry...'
exit=1                        ← 与文档「给了会 exit 1」一致 ✅
$ python3 agate/scripts/agate-mark.py DESIGN_GAP "示例"
[DESIGN_GAP: 示例]            ← exit_dg=0 ✅
```

✅ 示例已改为无参形态，且**显式标注**给参会 exit 1——不再引导读者照抄失败命令。

---

## 四、A8 数字复核

| # | 声称（出处） | 我的产出命令 | 结论 |
|---|---|---|---|
| 1 | 「**45 种**标记 / ≥3 次 **30 种**」（§1.1:19-20；CHANGELOG） | 按您指定口径 `agate/**` + `\[([A-Z][A-Z_]{2,})(?::[^\]]{0,40})?\]` | ✅ **复现成功**：`files scanned: 596 / distinct marker names: 45 / names with >=3 occurrences: 30`。**口径已写明后完全可复现** |
| 2 | PR #387「改动 **18 个已跟踪文件**」（§1.3:45） | `git show --name-only --format="" 6101a9e \| wc -l` → **18** | ✅ 复现 |
| 3 | 「全仓语料 **116 vs 116、差异文件数 0**」（§10.3(2):434；CHANGELOG） | 1564 文件逐文件新旧比对 | ✅ 复现（116/116、0） |
| 4 | 「**2311 passed** / 1 failed / 2 skipped」（CHANGELOG:47） | `pytest agate/tests/unit/ -q -p no:randomly` | ✅ **2311 passed**，1 failed（既有 `opencode` 不在 PATH，非本批）、2 skipped |
| 5 | 「**195 passed**」（regression+integration） | `pytest agate/tests/regression/ agate/tests/integration/ -q` | ✅ **195 passed** |
| 6 | 「**2531** 用例」 | `bash agate/tests/scripts/count-tests.sh` | ✅ **总计：2531 个测试用例** |
| 7 | 「**32** 用例（mk）」 | `pytest .../test_marker_single_source.py --collect-only -q` | ✅ **32 tests collected** |
| 8 | 「0 ERROR / 386 WARNING」 | `python3 agate/scripts/check-protocol-consistency.py` | ✅ **仅有 386 个 WARNING，无 ERROR**（exit 0） |
| 9 | 「逐形态 **8/8** 等价」（§10.3(2):434） | 8 探针 × 两实现 | ✅ 8/8 OK |
| 10 | 「**61** 行 REVIEWED 被误计」（§10.3(2):417） | 计 P7 侧 `^\s*>?\s*-?\s*\[DESIGN_GAP_REVIEWED` 行 | ✅ = 61 |
| 11 | 「载荷点 = 冒号必填；只去 `(?!\w)` 116 / 只去冒号必填 124」（§10.3(2):426-428） | 我的 2×2 变异矩阵 | ✅ **116 / 116 / 124 逐字复现**，结论一致 |
| 12 | 「批次 B 门禁 通过 **9** / 跳过 **32** / 失败 **0**」（§10.2） | 遍历 41 任务实跑 `check-scope-resolved.py <TASK_DIR>` | ✅ **passed=9 skipped=32 failed=0，DIST {0: 41}** |
| 13 | 「**存量 3 处**跨行参数」（`agate_markers.py:104,123`；§10.3(1):407；CHANGELOG:70） | 计全仓 `SCOPE_RESOLVED` 跨行命中（剥 AGATE_CARD） | ❌ **未更正**：实测 **11 处（10 个文件）**，最小口径亦为 11。**详见下方 N-2** |

### ⚠️ N-2（A8 遗留）：**「存量 3 处跨行」未更正，实测为 11**

上一轮已指出「存量 3 处**作为总数不成立**（实为 11；最小口径 5）」，并建议改为「如 `TAG0027/P7:48` 等（全仓 11 处）」。

**整改后，该声称在 4 处仍逐字未动**：

```
docs/design-notes/design-marker-single-source.md:407: ...允许跨行参数**（存量 3 处：`TAG0027/P7:48`、`TAG0031/P1:371`、`TAG0031/P7:60`）。
agate/scripts/agate_markers.py:104:        `[SCOPE_RESOLVED: 跨多行的长参数…]`（存量 3 处：TAG0027/P7:48、TAG0031/P1:371、
agate/scripts/agate_markers.py:123:    #   带参两支均**不要求闭合 `]`**，允许跨行续写（存量 SCOPE_RESOLVED 3 处）
CHANGELOG.md:70:  存量 3 处）。**教训：单源的前提是先如实刻画差异，不是先统一。**
```

**我的独立实测**（剥 `AGATE_CARD` 后，与 `check-scope-resolved.py` 同口径）：

```
files with cross-line SCOPE_RESOLVED hits: 10
TOTAL cross-line occurrences (AGATE_CARD stripped): 11
   TAG0001/P7-consistency.md 2 ; TAG0004/P7-consistency.md 1 ; TAG0010/P1-requirements.md 1
   TAG0021/P1-requirements.md 1 ; TAG0021/P7-consistency.md 1 ; TAG0022/P1-requirements.md 1
   TAG0024/P1-requirements.md 1 ; TAG0027/P7-consistency.md 1 ; TAG0031/P1-requirements.md 1
   TAG0031/P7-consistency.md 1
（不剥 AGATE_CARD 亦为 11）
```

**三处被引例子均真实存在**（我已 `sed -n` 逐行确认），错的是「**存量**」这个**总量词**——它把 3 个**例子**读成了 3 个**总数**。

**性质**：A8 项（声称-命令绑定）——上一轮明确列为须修复项，本轮**未修**。**严重度：LOW-MEDIUM**。理由：
- 不影响任何 gate 判定或判据行为（纯叙述数字）；
- 但按角色文件 A8 原则「**无法给出命令的声称，应删除该声称**」，一个**可被证伪且已被证伪**的总量词留在改动集里，正是本设计（「数字必须与判据绑定」）要治的病——**且它出现在论证「必须如实刻画差异」的同一段**，反讽地削弱了该教训的说服力。

**建议**（最小改动）：把 4 处的「存量 3 处」改为「**如** `TAG0027/P7:48` 等（全仓 **11 处**，最小口径 11）」，或直接删「存量」二字改为「例（3 个）」+ 附命令。

### ✅ 未复现的怀疑点（供留痕）

- **表格 `|` 污染**：**未复现为真问题**。我用 `|` 计数启发式初扫出 3 处“列数不符”（`WORKFLOW.md:316`、`scripts/README.md:115`、`design-notes/README.md:5`），**逐一开文件核对后判定全部为我启发式的假阳性**——那些单元格内含反引号包裹的**字面竖线**（如 `grep -cE ... | grep -cvE ...`）与长散文，朴素 `split("|")` 必然误计。**关键佐证**：`git diff --cached -U0` 显示这三处的改动 hunk 分别在 **451 行 / 81-83 行 / 34 行**，**与“不符”行号完全不相交** ⇒ **非本批引入、本批亦未新增**。**上一批的坑未重演**。
- **`check-yaml-schema.py` / `check-structure-consistency.py` 的环境解析**：因本 checkout 无 `.agate-version`，须 `AGATE_ROOT=<checkout>/agate`。**固定后全绿**（我已实测）：
  ```
  AGATE_ROOT=... python3 agate/scripts/check-yaml-schema.py
  SCHEMA-phases: OK / SCHEMA-dispatch: OK / SCHEMA-roles: OK / SCHEMA-markers: OK   exit=0
  AGATE_ROOT=... python3 agate/scripts/check-structure-consistency.py
  S1-phases: OK ... S5-schema: OK S6-references: OK S0-numbers: OK                 exit=0
  ```
- **`_rules_test_utils.py` 的修复正当性**：**核实为正当**。diff 显示 `make_fake_root()` **补齐了缺失文件**（`DEFAULT_MARKERS_YAML` + `default_markers_schema()`），**未削弱任何既有断言**，与 §10.4「假树须镜像真协议结构……非改测试迁就实现」的自我更正**一致**。

---

## 五、必跑命令结果（全部实跑）

```
$ python3 -m pytest agate/tests/unit/test_marker_single_source.py \
      agate/tests/unit/test_check_scope_resolved.py \
      agate/tests/unit/test_check_retrospective.py \
      agate/tests/unit/test_check_yaml_schema.py -q -p no:randomly
74 passed in 3.35s                       ✅（上一轮为 72；+2 = mk_6a/mk_6b）

$ python3 agate/scripts/check-protocol-consistency.py
仅有 386 个 WARNING，无 ERROR。          ✅ exit 0（0 ERROR 达成）

$ <遍历 41 任务跑 check-scope-resolved.py>
tasks: 41 / DIST: {0: 41} / passed(9) / skipped(32) / failed(0)   ✅ 9/32/0

$ ~/.venvs/agate-dev/bin/ruff check agate/
All checks passed!                       ✅
```

**说明（命令口径）**：`check-scope-resolved.py` 的 CLI 是**位置参数** `TASK_DIR`（无 `--task` 选项）；误用 `--task` 会因 `task_dir` 不存在而 `exit 2`（=「无 task 目录」）。首次我以 `--task` 跑得 `DIST: {2: 41}`，**定位为我的调用错误、非脚本缺陷**，改用位置参数后得 9/32/0。

---

## 六、新引入问题汇总

| # | 问题 | 严重度 | 判定依据 |
|---|---|---|---|
| **N-1** | `agate_markers.py:110-114` docstring 称「`(?!\w)` 是 HIGH-1 修复（否则吞并 `DESIGN_GAP_REVIEWED`）」，与实测**相反**（**已暂存**） | **LOW→并入 N-4** | 判据行为正确，仅注释因果错误 |
| **N-4** 🚨 | **载荷点更正只在工作区、未暂存**；暂存版三处（§10.3(2) / CHANGELOG / docstring）**同向错误归因于 `(?!\w)`** | **MEDIUM** | 直接落在上一轮 HIGH-1 收口项上；作者已写出正确版但未 `git add` |
| **N-2** | 「存量 **3 处**跨行参数」在 4 处未更正；实测**总数 11（10 文件）**（**已暂存**） | **LOW** | A8 项（上一轮已列）。纯叙述数字，不影响判据 |
| **N-3** | §10.4 验证表仍写「`mk_1~mk_5` 守护 \| **30 passed**」与「负向控制（**3 组**）」；实测现为 **32 用例**、守护组共 **6 组**（**已暂存**，为该批 `+` 行 `:381`/`:432`） | **LOW** | 自述与自身产物脱钩 |
| — | 表格 `\|` 污染 / CHECK 10 脚本名 / ruff / 环境解析 | **未发生** | 见 §4「未复现的怀疑点」 |

**未见 HIGH 级新引入问题。** N-4 为 **MEDIUM**（文档-代码因果声称与实测相反，且**只差一次 `git add` + 两处措辞**即可闭合）；N-1/N-2/N-3 为 LOW。

---

## 总体判定

**`NEEDS-REVISION`（轻量收口）** —— **暂不建议按当前暂存状态提交**；修 N-4 三项后即可提交。

> **为何不是 `APPROVED WITH NITS`**：N-4 不是「措辞不精确」，而是**将提交的三处文档/注释同向地把 HIGH-1 的因果归错**（都指向 `(?!\w)`，而实测载荷点是冒号必填）。上一轮 HIGH-1 的**收口条件第 2 条**明确要求「更正 §10.3(2) / CHANGELOG 中的错误声称」——**该更正作者已写出，但没有 `git add`**，属**未完成的收口**。鉴于修复成本极低（一次 `git add` + 两处措辞）且**风险实质为零**，这是「轻量」收口而非「重做」。
>
> **为何不是重度 `NEEDS-REVISION`**：**代码与判据本身完全正确**（我已实测 116/116、差异 0、逐形态 12/12、`mk_6a`/`mk_6b` 双向非真空、批 B 9/32/0、0 ERROR、ruff 全绿）。**不存在功能性缺陷**，N-4 全部落在**文档/注释层**。

### 判据

| 维度 | 结论 |
|---|---|
| **HIGH-1 是否真修好** | ✅ **是**（全仓 116 vs 116、差异文件数 0；逐形态含 `[DESIGN_GAP]`/`[DESIGN_GAP_REVIEWED: x]`/粗体/引用/跨行全部等价；P7 口径 59 vs 59） |
| **等价守护是否非真空** | ✅ **是**（HIGH-1 状态下 `mk_6a`/`mk_6b` **双双转红**，还原转绿；双向已证） |
| **MEDIUM-2 / 3** | ✅ 均已修复且**已暂存**（§3.5 表述收窄 + 两方向都需守护；18 复现、14 重新定性、漏改率 28% 联动） |
| **LOW-4 / 5 / 6** | ✅ 均已修复（绑定真实判据 / 前向指针 / 示例改无参） |
| **A8 数字** | ⚠️ **12/13 可复现**；仅「存量 3 处跨行」（实为 11）**未更正** |
| **硬门禁** | ✅ pytest 74 passed；consistency **0 ERROR**；批 B **9/32/0**；ruff **All checks passed**；S-1~S-6 + SCHEMA 全 OK |
| **新引入问题** | 🚨 **N-4（MEDIUM，未暂存的更正是关键）** + N-1/N-2/N-3（LOW） |

### 为什么 HIGH-1 本身判「已修复」而整体仍判 `NEEDS-REVISION`

**代码层 HIGH-1 已彻底闭合**——这是上一轮唯一的 HIGH，其三条实质要求（①判据等价 ②补等价守护 ③更正错误声称）中，**①②已由我实测证明达成**。**③只做了一半**：作者写出了更正，但**没进暂存区**，而**暂存区才是提交对象**。

我无法替被评审方判断「未暂存是有意（还在改）还是疏漏」——但按**取证事实**：**当前 `git commit` 会带上一个已知错误的三处归因**。故据实判 `NEEDS-REVISION`，并明确**这是最小收口**。

### 可提交的最小条件

| # | 收口项 | 类型 | 量 |
|---|---|---|---|
| **1** | `git add docs/design-notes/design-marker-single-source.md` —— 纳入**已存在**的载荷点更正块 | 暂存操作 | 1 条命令 |
| **2** | `CHANGELOG.md` 该行改为「① 冒号**必填**（**载荷点**）；② `(?!\w)`（防御性冗余）」 | 文档 | 改 1 行 |
| **3** | `agate_markers.py:110-114` docstring 同口径（**现与实测相反**） | 注释 | 改 2 句 |

**+ 建议（不阻断）**：
- **N-2**：「存量 3 处」→「如 `TAG0027/P7:48` 等（全仓 **11 处**）」（4 处）。
- **N-3**：§10.4 表「`mk_1~mk_5` 守护 | 30 passed」→「`mk_1~mk_6b` 守护 | **32 passed**」；「负向控制（3 组）」→「（6 组，含 `mk_6a`/`mk_6b` 转红）」。
- **A7 附带观察（延续上一轮）**：补一条「判据单一权威源」ADR，把 `mk_1` 的「消费方不得复制判据」升格为跨机制通则。

**收口后预期**：三处措辞改动**不触碰任何判据**，故**无需重跑全部门禁**；建议至少重跑 `test_marker_single_source.py`（32 passed）+ `check-protocol-consistency.py`（0 ERROR）确认无扰动。

> **闭环标注**：本报告**无 `NEEDS_HUMAN_REVIEW` 项**，故无需 `[HUMAN_CONFIRMED: ...]` 配对标记。
> 所有结论均为 ALIGNED / MISALIGNED / NIT，可直接进入闭环。

---

## 已实测 vs 推断 的区分

| 类别 | 条目 |
|---|---|
| **我已实测**（附真实命令/输出） | HIGH-1 全仓 116/116/差异 0；逐形态 12 探针；P7 口径 59 vs 121 → 59 vs 59；**2×2 分约束变异矩阵**（116/116/124/195）；`mk_6a`/`mk_6b` 双向变异（红↔绿）；`git show --name-only 6101a9e \| wc -l` = 18；45/30 标记（指定口径）；61 行 REVIEWED；8/8 逐形态；2311 passed / 195 passed / 2531 用例 / 32 用例；consistency 0 ERROR + 386 WARNING；批 B 41 任务 9/32/0 DIST{0:41}；ruff All checks passed；S-1~S-6 + SCHEMA-markers 全 OK；`uncovered_gate_scripts()` 源码扫描面 + `SCRIPT_ALIGNMENT_ANCHORS` 命中；跨行 11 处（10 文件）；`agate-mark.py` 三种调用的 exit code；**`git show :<path>` 暂存版逐条比对**（N-4 的判据）；表格 3 处「不符」的 hunk 行号不相交 |
| **我的推断**（未直接实测） | N-2/N-3 的**严重度定级**（基于「不改判据」的事实推断不影响 gate）；N-4 的**定级为 MEDIUM**（基于「落在上一轮明确收口项上」判断，非机械判据）；§4 表格假阳性的**归因**（判定为反引号内字面竖线，未逐字符解析 CommonMark）；「14 定性为形态同步面」属**表述选择**（我实测 18，未独立复核 4+6+4 明细**每一项**归属） |
| **未独立复现**（如实声明） | §10.5 G4「只加 1 条 → 生成/`--list`/守护零代码改动自动可用」——只读纪律下不做仓库内写注册表操作；由 `mk_*` 全量遍历 `M.names()` 的**实现结构**佐证（测试与 CLI 均遍历注册表，无硬编码标记名），**推断成立但未实测**。**另**：我**未**核验工作区那份未暂存编辑是「有意保留」还是「疏漏」——只报告**它不在暂存区**这一事实 |

---

## 审查方法留痕（只读纪律执行说明）

- **未执行**任何写仓 git 命令：全程无 `checkout/restore/reset/stash/clean/add/commit/switch -f`。
- **未编辑/删除**任何被评审文件。唯一写入路径：本报告文件（写前已 `ls` 确认不存在同名文件，符合 BDD-8）。
- 变异测试**全部**在 `<仓库根>/.agate-tmp/mut_payload/`、`mut2/`、`mut3/`、`mut_mk6/` 的一次性副本上进行，「建→用→清」均在**同一次 bash 调用**内完成；每次变异均以断言 + `grep` 回显确认**已实际落盘**（防空跑假红/假绿），并在同一调用末尾 `rm -rf` 后回显确认清理成功（每次输出均为 `CLEANUP: OK`）。
- **scratch 失败如实上报**：本次有两处 scratch 自身失误，均已定位为**我脚本的问题、非被评审仓缺陷**，并如实记录：
  1. 首次副本用 `../agate-workspace` 相对路径，副本下无该目录 ⇒ 计数得 0/0。**已改为复制语料 + 绝对路径**后重跑。
  2. 首次等价脚本用 `len(finditer(...))` ⇒ `TypeError`（iterator 无 `len`）。**已改为 `sum(1 for _ in ...)`**。
  3. 表格污染启发式初版产出 3 处假阳性，**已开文件逐一核对并证伪**（见 §4），未据错误启发式下结论。
- **纪律说明**：对比 `count-tests.sh` 时**未用 `tail` 截断做判断**（首次 `tail -3` 吞掉总计行，遂改用 `grep -i "总计"` 重取全量结果）——沿用 AGENTS.md「截断仅用于展示、不得用于判断」的教训。
