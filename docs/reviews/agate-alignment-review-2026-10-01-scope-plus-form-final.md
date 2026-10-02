---
review_date: 2026-10-01
reviewer: protocol-alignment-review
status: needs-revision
change_summary: SCOPE+ 行首声明形态 hotfix（check-scope-resolved / check-retrospective 双侧放宽 + 3 处协议文档同步 + 边界锁用例）——N1-N6 回改终审
files_changed: [CHANGELOG.md, agate-workspace/roadmap/roadmap.md, agate/WORKFLOW.md, agate/assets/execution-roles/architect.md, agate/assets/execution-roles/implementer.md, agate/dispatch-protocol.md, agate/phase-cards/P4-implementation.md, agate/scripts/check-retrospective.py, agate/scripts/check-scope-resolved.py, agate/state-machine.md, agate/tests/README.md, agate/tests/fixtures/tag0034_regression_baseline.json, agate/tests/unit/test_check_scope_resolved.py, docs/design-notes/README.md]
---

# 协议-脚本对齐审查（终审：N1-N6 回改验证）

## 0. 本轮范围与方法

**范围**：验证复审报告 `agate-alignment-review-2026-10-01-scope-plus-form-rereview.md` 所列 N1-N6 是否真修好、有无新引入问题。
首轮 M1-M6 / L1-L6 仅在「与 N 项交叠」处复查，不重复审。

**方法**：全部数字**自跑复算**（不采信文档与复审报告任一方）；四处必跑项实跑；变异测试在
`<仓库根>/.agate-tmp/final` 一次性副本内做（建→用→清同一次 bash 调用内完成，已确认清理）。

**只读纪律**：本轮**未**执行任何 `git checkout/restore/reset/stash/clean/add/commit`，**未**编辑任何被评审文件。
唯一写入路径 = 本报告。自动脚本对源码的「改写」只发生在已删除的一次性副本内（下 §5 有清理确认）。

**标记约定**：`[实测]` = 本轮真跑并附输出；`[推断]` = 由实测外推，未直接跑。

---

## 1. 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| N1 | 「纳入标题形态新增 **6** 个任务转红」应为 **4**（紧口径） | **修复不当（部分回改，漏 3 处）** |
| N2 | (a) `TAG0008` 非真声明 (b) `TAG0025`「不是行首」被证伪 (c) `test_sc_13` docstring 与设计说明打架 | **修复不当（a 漏 1 处；b ✅；c ✅）** |
| N3 | 判据跑不出自己的数字（`+` 未转义 / 「28 处」口径未披露） | **已修复** |
| N4 | §6 写「10 个已跟踪文件」实测 14；表内漏 3 行 | **已修复** |
| N5 | CHANGELOG 称「3 处…补明形态与不对称」实测 1/3 | **已修复** |
| N6 | 「`SCOPE_PLUS_RE` 逐字节相同」源码层为假 | **已修复** |

| # | 必跑项 | 结论 |
|---|--------|------|
| 1 | 两测试文件 34 passed | **PASS**（34 passed）|
| 2 | `check-protocol-consistency.py` 0 ERROR | **PASS**（0 ERROR / 386 WARNING）|
| 3 | roadmap 92 RM 行 / 0 列数异常 / `:78` 9 列 | **PASS** |
| 4 | 基线 tripwire 2 passed + 基线 hash 与当前文件一致 | **PASS**（6/6 hash 全等）|
| 5 | 转红数复算 4 / 6 / 5 / 24 | **PASS**（四值全部复现）|
| 6 | 新错误声称 / 同族缺陷 | **FAIL —— 发现 4 项（X1-X4）** |

---

## 2. 必跑项实测输出

### 2.1 单测（34 passed）✅

```
$ timeout 600s python3 -m pytest agate/tests/unit/test_check_scope_resolved.py \
    agate/tests/unit/test_check_retrospective.py -q -p no:randomly
..................................                                       [100%]
34 passed in 1.82s
```

### 2.2 一致性（0 ERROR）✅

```
$ timeout 300s python3 agate/scripts/check-protocol-consistency.py
  仅有 386 个 WARNING，无 ERROR。
EXIT=0
```
（386 WARNING 与设计说明 §7 自述一致，属既有基线，非本次引入。）

### 2.3 roadmap 列完整性 ✅

```
RM rows: 92
rows with len(split('|'))!=9 : 0
header line 11 fields 9
line 78: fields 9
  [1] 'RM-AG0077'  [2] len=5859 … [3] 'done' … [8] ''
```
**「列数」口径说明**：`check-gate.py::_check_roadmap_done` 的判据是 `len(line.split("|")) == 9`
（首尾各一个空 cell），故**规范值即 9**，不是 11。全表 96 个九字段行含全部 92 个 RM 行，
`roadmap.md:78` = 9 字段 ✅。另确认该行 `&#124;` 转义生效、**不含**裸 `(?:**|__)` 竖线
（§8 所记的竖线事故确未复发）[实测]。

### 2.4 基线 tripwire（2 passed + hash 一致）✅

```
$ timeout 300s python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py -q -p no:randomly
..                                                                       [100%]
2 passed in 0.02s
```

**关键：基线值是否真的等于当前文件 hash**（防「刷新基线=橡皮章」）[实测]：

```
OK  agate/rules/phases.yaml
OK  agate/scripts/check-gate.py
OK  agate/scripts/check-state-transition.py
OK  agate/state-machine.md
OK  agate/tests/unit/test_tag0027_b2_agate_dispatch.py
OK  agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py

ALL HASHES MATCH: True
captured_phase: P3  task_id: TAG0034
```
6/6 与当前工作区文件逐一相符 ⇒ 基线**确实随本次改动刷新且自洽**，tripwire 非真空。
`state-machine.md` 源码 diff 实测 `1 file changed, 1 insertion(+), 1 deletion(-)`，确为**单行文案**、
未触及任何转移规则 ✅。

### 2.5 转红数复算（4 / 6 / 5 / 24）✅

用**真实脚本**（`import` 后仅替换正则），对全部 41 个任务目录端到端跑 `main()` 判 exit code [实测]：

```
task_count = 41
baseline(new)                      checked=  9 skip= 32 red=  0
A tight_heading_with_N             checked= 11 skip= 26 red=  4  TAG0012 TAG0014 TAG0023 TAG0025
A3 loose_heading                   checked=  9 skip= 26 red=  6  TAG0004 TAG0008 +A四者
B lead_backtick                    checked= 10 skip= 26 red=  5  TAG0004 TAG0012 TAG0016 TAG0025 TAG0033
C inline_anywhere                  checked= 12 skip=  5 red= 24  (24 个，TAG0004…TAG0039)
```
**四个数字全部与文档声称一致**，且红名单逐字匹配：
- 紧标题口径 = **4**（`TAG0012`/`TAG0014`/`TAG0023`/`TAG0025`）
- 松标题口径 = **6**（+`TAG0004`/`TAG0008`）——**6 只在松口径成立，文档此点表述正确**
- 行首反引号 = **5**（1 真声明 : 4 引述/否定）
- 行内任意 = **24**

⇒ **数字本身无争议**；问题在**旧数字仍留在三个文件里**（§3-N1）。

---

## 3. N 项逐条裁定

### N1 —— **修复不当（部分回改，漏 3 处）**

**已改**（✅）：设计说明 §3:59 表格、§3.1:99-100 —— 均为 **4** + 名单
`TAG0012`/`TAG0014`/`TAG0023`/`TAG0025`，并附口径提示（松口径才得 6，且与「行内 24」同口径）；
`CHANGELOG.md:29-32` 与 `roadmap.md:78` 也已改为 **4** [实测，grep + 逐行读]。

**未改**（❌）——**三处仍在传播旧声称**：

| 文件:行 | 现文 | 应为 |
|---|---|---|
| `agate/scripts/check-scope-resolved.py:32` | 「纳入会新增 **6 个任务转红**」 | **4** |
| `agate/tests/unit/test_check_scope_resolved.py:278` | 「纳入会新增 **6 个任务转红**」 | **4** |
| `docs/design-notes/README.md:33` | 「量化取舍（**5/6 个任务转红**）」 | 5 与 **4** |

**为何这是必修而非 nit**：
1. **复审的整改清单第 3.2 节把「`check-scope-resolved.py` 常量注释」列为 N1/N2 的整改落点**（该文件被点名）。
   本轮实测该注释**两行都未改**（`:32` 的 6、`:33` 的 `TAG0004 / TAG0008 的真声明`）。
2. `:32` 与 `:39` 的**实际正则在同一个文件、相隔 7 行**——读者按注释复算会得 4、按注释文字读是 6，
   **同一文件内自相矛盾**，正是本轮要治的缺陷族。
3. `docs/design-notes/README.md` 是**本批 diff 内的新增行**（`git diff` 显示为 `+` 行），
   属「本次改动引入」，不是历史遗留。

**证据** `[实测]`：
```
$ grep -rn "6 个任务转红\|TAG0008\b" <changed files>
agate/scripts/check-scope-resolved.py:32:  纳入会新增 **6 个任务转红**。
agate/scripts/check-scope-resolved.py:33:  **代价**：TAG0004 / TAG0008 的真声明至今未被覆盖…
agate/tests/unit/test_check_scope_resolved.py:278:  纳入会新增 6 个任务转红。
docs/design-notes/README.md:33:  …含量化取舍（5/6 个任务转红）与仍未覆盖的真声明如实登记
```

> **建议**：三处按已完成的设计说明对齐——`6 → 4`、名单去掉 `TAG0008` 只留 `TAG0004`、
> README 的「5/6」改为「5/4（紧口径）」或直接改为「5/4」。

---

### N2 —— **(a) 修复不当（漏 1 处）；(b)(c) 已修复**

**(a) `TAG0008` 非真声明** —— **部分修复** ❌
- ✅ 设计说明 §3.1:102 新增「⚠️ 更正：初版把 `TAG0008` 也列为真声明——不成立」，并给出正文「无」的证据；
  §3.1:95 表格第 3 行 `TAG0025` 标「真声明」、§3.1:101 代价只保留 `TAG0004`。
- ✅ `CHANGELOG.md:33` 已更正（「其 `P2-design.md:202` 标题下正文首句是「无」，属容器标题 + 否定正文」）。
- ✅ `roadmap.md:78` 已更正（「`TAG0008` **不是**真声明……此处已更正初版的错误名单」）。
- ❌ **`agate/scripts/check-scope-resolved.py:33` 仍写「`TAG0004` / `TAG0008` 的真声明至今未被覆盖」**
  ——与同批更正后的另外三处**直接冲突**。

**(b) `TAG0025` 定位** —— **已修复** ✅
设计说明 §3.2:123-128 已改为「**视觉行首、段落中句**」，明确承认「『不是行首』该位置性断言不成立
（独立评审以 `od -c` 证伪，我已复核）」，且把它转为**支持**保守边界的论据。
本轮独立复核位置事实 [实测]：
```
TAG0025-agateon-rename/P4-implementation.md  L80  first-byte: `
TAG0004-env-adaptation/P4-implementation-group1.md  L50  first-byte: -
TAG0012-…/P4-implementation.md L110 first-byte: -    TAG0033-…/P4-implementation.md L113 first-byte: -
```
`TAG0025` 确实**第 0 字节即反引号**，「视觉行首、段落中句」是**准确**表述 ✅。

**(c) `test_sc_13` docstring** —— **已修复** ✅
`test_check_scope_resolved.py:216-222` 现文明确写：「`TAG0033` 等属『`` `[SCOPE+]` ``：**无**』这类确定性否定陈述。
⚠️ **`TAG0025` 不属此类**：其 `P4-implementation.md:80` 虽是**视觉行首**（第 0 字节为反引号，`od -c` 复核），
但它是上一句的**折行续行**，语义上属句中引述……这正是本边界保守的原因（设计说明 §3.2）」。
⇒ 与设计说明 §3.2 **语义一致、无冲突** ✅（M3 的「整改把错位证据写回去」已消除）。

---

### N3 —— **已修复** ✅

**逐字照抄设计说明 §3.1 的命令块真跑** [实测]：

```
$ python3 - <<'EOF'
import re,glob,os
SKIP=re.compile(r"dispatch-context|dispatch-prompt|progress")
CARD=re.compile(r"<!-- AGATE_CARD_START -->.*?<!-- AGATE_CARD_END -->",re.DOTALL)
rx=re.compile(r'^\s*#+\s*(?:\d+\.\s*)?\[SCOPE\+\]',re.M)
occ=0;tasks=set()
for f in sorted(glob.glob('agate-workspace/tasks/*/*.md')):
    if SKIP.search(os.path.basename(f)): continue
    t=CARD.sub('',open(f,encoding='utf-8',errors='replace').read().replace('\r\n','\n'))
    m=rx.findall(t)
    if m: occ+=len(m); tasks.add(f.split('/')[2])
print(occ,'处 /',len(tasks),'个任务')
EOF
15 处 / 10 个任务
```
⇒ **命令跑得出它声称的数字**：`+` 已转义、`\d` 已改 POSIX 安全形、扫描面 `tasks/*/*.md` 与
SKIP/CARD 口径与脚本一致。**15 处 / 10 个任务 = 实测值** ✅。

**宽松口径「26 处 / 15 个任务」也复现** [实测]：
```
tasks/ only        : (26, 15)
tasks/ + docs/     : (28, 17)
agate-workspace/** : (0, 0)
```
⇒ 文档已把原「28 处」改为 **26 处 / 15 个任务**并写明口径（tasks/），**口径已披露** ✅。
（注：本文档给出的 `grep -E` 等价形用 `(?:…)` 时 GNU grep **只得 10**——`(?:` 不被支持；
若将来要附 grep 命令，须用 POSIX 组 `([0-9]+\.\s*)?`，我实测该形 = **15** ✅。文档当前**只给 Python 命令**，
故不构成缺陷；此项列为**提示**。）

---

### N4 —— **已修复** ✅

```
docs/…-declaration-form.md:5  : 14 个已跟踪文件（2 脚本 + 6 处协议文档/角色文件 + 1 测试 + 基线 + CHANGELOG + roadmap + tests/README）
docs/…-declaration-form.md:166: `git diff --name-only | wc -l` = 14 个已跟踪文件
$ git diff --name-only | wc -l
14
```
**逐文件比对**：14 个实际改动文件**全部在 §6 表中列出**（含此前漏的 `roadmap.md` /
`architect.md` / `implementer.md`）——本轮脚本化核验结果 [实测]：

```
actual git diff files: 14
  CHANGELOG.md LISTED / agate-workspace/roadmap/roadmap.md LISTED / agate/WORKFLOW.md LISTED
  agate/assets/execution-roles/architect.md LISTED / …implementer.md LISTED
  agate/dispatch-protocol.md LISTED / agate/phase-cards/P4-implementation.md LISTED
  agate/scripts/check-retrospective.py LISTED / agate/scripts/check-scope-resolved.py LISTED
  agate/state-machine.md LISTED / agate/tests/README.md LISTED
  agate/tests/fixtures/tag0034_regression_baseline.json LISTED
  agate/tests/unit/test_check_scope_resolved.py LISTED / docs/design-notes/README.md LISTED
```
计数（15 vs 14）与表行**均达标** ✅。

---

### N5 —— **已修复** ✅

CHANGELOG 已按**据实**描述收敛 [实测]：

> `CHANGELOG.md:43-45`：「**3 处协议文档字面引用的旧正则同步**（`WORKFLOW.md` / `dispatch-protocol.md` / `state-machine.md`），
> 其中 **`WORKFLOW.md` 一处**写明可接受形态**并**说明「两个标记边界**不对称**：`SCOPE_RESOLVED` 侧接受反引号」，
> 另 2 处只同步正则字面量（`dispatch-protocol.md` 另补粗体/引用形态说明）」

**独立核验三处实况** [实测，`grep -n 不对称`]：

| 落点 | 姿态 | 与 CHANGELOG 相符 |
|---|---|---|
| `agate/WORKFLOW.md:451` | 形态 + **明写「两个标记的边界不对称」** | ✅「一处」 |
| `agate/dispatch-protocol.md:953` | 补形态说明 + **现已含不对称** | ✅「另补形态」 |
| `agate/state-machine.md:233` | **只同步正则字面量**（无「不对称」） | ✅「另 2 处只同步正则」 |

⇒ 实测分布（不对称 2 处 / 形态 3 处）与 CHANGELOG 新表述**一致**，过度声称已消除 ✅。
（附带结果：`dispatch-protocol.md:953` 由「未写不对称」变为「已写」，比 CHANGELOG 描述**更强**而非更弱——
属**保守表述**，不构成缺陷。）

---

### N6 —— **已修复** ✅

```
docs/…-declaration-form.md:136: `check-retrospective.py` 持有**语义等价**的 `SCOPE_PLUS_RE`（源码写法不同：一处拼接常量、一处字面量）
CHANGELOG.md:38:                该脚本持有**语义等价**的 `SCOPE_PLUS_RE`（源码写法不同：一处拼接常量、一处字面量）
```
「逐字节相同」在**两个文件的 SCOPE_PLUS 语境下均已消失** [实测]，与同段自陈的
「源码可一个用拼接常量、一个用字面量」不再互斥 ✅。

**独立核验 pattern 层等价** [实测]：
```
scope pattern: '^\\s*(?:[-*+]\\s*)?(?:>\\s*)?(?:\\*\\*|__)?\\[SCOPE\\+\\]'
retro pattern: '^\\s*(?:[-*+]\\s*)?(?:>\\s*)?(?:\\*\\*|__)?\\[SCOPE\\+\\]'
pattern strings identical: True
```
⇒「语义等价（pattern 相同、源码写法不同）」是**准确**描述 ✅。行为等价守护 `test_sc_14` 实跑通过。

---

## 4. 新引入问题（X1-X4）

### X1（MEDIUM）：N1/N2 的旧声称仍在 **3 处**存活，其中 2 处是「本批改动内」

见 §3-N1 证据表。要点：`check-scope-resolved.py:32-33`（复审点名的整改落点，未改）+
`test_check_scope_resolved.py:278`（本批 diff 内）+ `docs/design-notes/README.md:33`（本批 diff 新增行）。
⇒ 这不是「历史残留」，而是**整改未闭环**：同一事实在仓库内仍有**两种相反写法**
（设计说明说 4/非真声明，脚本注释说 6/真声明）。

**严重性**：不改变任何 gate 判定（纯注释/docstring/索引文案）；但正是 A8「声称-命令绑定」要治的形态，
且 `:32` 与 `:39` 同文件相邻 —— **修复成本极低、不修则把已更正的错误留在最贴近判据的位置**。

### X2（LOW-MEDIUM）：基线刷新序数自相矛盾——**「第 8 次」vs 文件内「第 9 次」**

`CHANGELOG.md:47` 与设计说明 `:177` 均称 `tag0034_regression_baseline.json` **第 8 次刷新**，
但该文件 `_note` 内**自身**记载了 **9 次**，末条为：

> 「2026-10-01（SCOPE+ 形态 hotfix **第 2 轮**，直改）：state-machine.md 第 233 行同步补充
> 「粗体/引用块同为声明、句中引用与反引号包裹不触发、格式权威源指向 WORKFLOW.md §[SCOPE+]」（独立复审 L1…）。
> **未改任何转移规则**……（**第 9 次刷新**。）」

[实测] `_note` 中序数 = `['5','6','7','8','9']`；`git log` 该文件历史 commit = **7** 次，
加本次未提交改动 = 第 **8** 次……**但本次 diff 实际新增了「第 8 次」与「第 9 次」两条注记**
（第二轮回改又刷了一次 hash），故**当前应为第 9 次**；`第 8 次` 是**上一轮**（改 `check-scope-resolved.py` 那次）的序数。

**为何算缺陷**：CHANGELOG/设计说明把**上一轮的刷新**记成本轮的，读者会误判本轮的 actual 改动面
（本轮基线变化 = `state-machine.md` 单行，diff 实测 3 行 JSON / 1 行源码）。属**序数错位**，
不影响 gate。⇒ 建议把两处「第 8 次」改为「第 9 次」（或写「本批共 2 轮刷新，见基线 `_note`」）。

### X3（LOW）：设计说明 §3 表格第 5 行仍留「以引述/否定为主」的弱化定性

`docs/…-declaration-form.md:58`：`行首反引号 …… **以引述/否定为主，但存在真声明反例**——见 §3.2`。
§3.2 已充分更正并给出 1:4 信噪比，故**不算错误**（措辞已带反例提示）。
仅指出：与 §3.2 的「**可量化的取舍**」相比，§3 表格仍是定性措辞，**建议**统一为「真声明 1 : 引述/否定 4」。
**列为 nit，不阻断。**

### X4（LOW）：`docs/design-notes/README.md:33` 的「5/6」与本批结论不一致

同 X1 第三行，但单列以免被合并忽略：索引行写「量化取舍（**5/6** 个任务转红）」——
**5** 是行首反引号、**6** 是**松标题口径**；而本批**采用紧口径 4** 并明确**不采用** 6。
⇒ 索引把「被否决的口径」与「采用的口径」并列，读者会误读为「本批纳入会新增 6」。
**建议**改为「5/4」并注明口径。

---

## 5. 只读纪律与 scratch 清理

- 全程未执行 `git checkout/restore/reset/stash/clean/add/commit`；未编辑被评审文件。
- 变异测试在 `.agate-tmp/final/`（`cp -a agate`）内做，「建→改→跑→`rm -rf`」在**同一次 bash 调用**内完成，
  该调用末尾输出 `CLEANED`。本轮 `git status` 与开工时一致（14 modified + 5 untracked，无新增/丢失）。

**变异结论（边界锁非真空）** [实测]：把 `_SCOPE_LEAD` 改成覆盖标题形态后：
```
FAILED agate/tests/unit/test_check_scope_resolved.py::test_sc_15_heading_form_is_deliberate_exclusion
1 failed, 1 passed, 17 deselected
```
⇒ `test_sc_15` 确实**锁住**了「标题形态刻意排除」的决策，未来放宽必转红 ✅（`sc_16` 同构，本轮未单独变）。

---

## 6. A8 声称-命令绑定（本批残留项）

| 声称 | 出处 | 命令 | 结论 |
|---|---|---|---|
| 紧标题口径转红 **4** | 设计说明 §3:59 / §3.1:99 / CHANGELOG:29 / roadmap:78 | 变体 A e2e（41 任务） | ✅ 4，名单逐字匹配 |
| 松标题口径转红 **6** | 设计说明 §3.1:100 | 变体 A3 | ✅ 6 |
| 行首反引号转红 **5** | §3:58 / §3.2 / CHANGELOG | 变体 B | ✅ 5（1:4 亦核实）|
| 行内任意转红 **24** | §3:57 / CHANGELOG | 变体 C | ✅ 24 |
| 标题形态 **15 处 / 10 任务** | §3.1:69 | §3.1 照抄命令 | ✅ 15/10 |
| 松口径 **26 处 / 15 任务** | §3.1:70 | 同命令改 rx | ✅ 26/15（tasks/）|
| §6 **14 个已跟踪文件** | §6:166 | `git diff --name-only \| wc -l` | ✅ 14，14/14 在表内 |
| roadmap 92 RM 行 / 0 异常 | 必跑项 | 列数脚本 | ✅ |
| 基线 6 hash 自洽 | 必跑项 | sha256 比对 | ✅ 6/6 |
| **标题形态转红 6** | **`check-scope-resolved.py:32`** | 同上变体 A | ❌ **应 4** — **无据声称未删** |
| **`TAG0008` 真声明** | **`check-scope-resolved.py:33`** | `sed -n 202,204p TAG0008/P2-design.md`（正文「无」）| ❌ **不成立** |
| **6 个任务转红** | **`test_check_scope_resolved.py:278`** | 同上 | ❌ **应 4** |
| **5/6 个任务转红** | **`docs/design-notes/README.md:33`** | 同上 | ❌ **6 非本批口径** |
| 基线**第 8 次**刷新 | CHANGELOG:47 / §6:177 | 基线 `_note` 自载序数 | ⚠️ **实为第 9 次** |

---

## 7. 终审判定

### 判定：**NEEDS-REVISION**

**是否可提交：不建议在当前状态提交。**

**理由**（按严重度）：

1. **N1/N2 未闭环（X1/X4）**：`check-scope-resolved.py:32-33` 是复审**点名的整改落点**，
   本轮实测**未改**；同批还漏了 `test_check_scope_resolved.py:278` 与
   `docs/design-notes/README.md:33`（后两处均为**本批 diff 内**内容）。
   后果 = 仓库对同一事实存在**两种相反表述**，且错误的那个**紧邻实际正则（相隔 7 行）**。
   A8 明文：「无法给出命令的声称，应删除该声称」——`6` 与「`TAG0008` 真声明」两条
   **恰是复审已证伪的声称**，留在代码注释里属**必改项**，不是 nit。
2. **X2**：基线刷新序数错位（第 8 / 第 9），属据实性缺陷，一并在本轮改掉成本极低。

**修复量极小**（4 行文本，零逻辑改动、零 gate 行为变化）：
- `agate/scripts/check-scope-resolved.py:32` `6 → 4`；`:33` 删 `TAG0008`、只留 `TAG0004`
- `agate/tests/unit/test_check_scope_resolved.py:278` `6 → 4`
- `docs/design-notes/README.md:33` `5/6 → 5/4`（或注明紧口径）
- `CHANGELOG.md:47` + 设计说明 `:177` `第 8 次 → 第 9 次`

**修完后的预期**：由于改动**纯注释/文案、不触及任何正则与判据**，本轮已跑通的
34 passed / 0 ERROR / 2 passed / 4-6-5-24 复算结论**全部继续成立**，无需重跑变异；
可在改后仅重跑 §2.1+§2.2+§2.4 三项即视为终审通过（`[推断]`——依据是改动面不含可执行分支）。

**为何不是 `APPROVED WITH NITS`**：X1 的两行**正是复审已明确要求回改**的内容（复审整改清单
点名 `check-scope-resolved.py`），未改 = 整改未完成；且「6」与「`TAG0008` 真声明」是**已被证伪的
事实性声称**留在判据旁。判为 nit 会使「A8 无据声称须删」在本批失效。

**未实测项（如实声明）**：
- 未跑全量 pytest（本轮只需 §2.1 两文件；全量用例数经 `count-tests.sh` = 2499，未据此断言全绿）。
- `ruff` 未跑（本轮无源码逻辑改动；`[推断]` 注释文本改动不影响 lint 结论）。
- `sc_16` 未单独做变异（与 `sc_15` 同构，仅实测 `sc_15` 转红）。
- `TAG0016/P7-consistency.md` 的「引述」定性未逐字复核（§3.2 表格其余 5 站点已 `od -c`/首字节核验）。
