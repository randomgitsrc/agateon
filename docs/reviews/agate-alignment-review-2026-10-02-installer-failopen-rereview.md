---
review_date: 2026-10-02
reviewer: protocol-alignment-review
status: approved
change_summary: 复审 —— 上一轮 NEEDS-REVISION 的 2 项 MEDIUM（AGENTS.md/CHANGELOG 过度声称、CHANGELOG 悬空指针）+ 3 项 LOW 整改是否到位；本轮代码路径未改，仅文档 + 一条测试断言
files_changed: [AGENTS.md, CHANGELOG.md, agate/adr.md, agate/scripts/agate-install.py, agate/tests/unit/test_agate_version_install.py]
---

# 协议-脚本对齐审查（复审 / re-review）

**分支**：`fix/installer-fetch-failopen`（改动集**未提交**，已 staged，5 文件 / **+205 −10**）
**上一轮报告**：[agate-alignment-review-2026-10-02-installer-failopen.md](agate-alignment-review-2026-10-02-installer-failopen.md)，判定 NEEDS-REVISION（代码无需返工）
**审查纪律**：只读。两次变异（mutation）均在 `<仓库根>/.agate-tmp/` 一次性副本内「创建 → 操作 → 清理」**同一次 bash 调用**内完成；事后核实 `.agate-tmp/{rr-*,rg-*,hc-*}` 均不存在。未对被评审仓库做任何写操作（`git status --short` 复审前后一致，仍为 5 个 staged `M` + 4 个未跟踪文件）。
**证据口径**：每条结论标注「**已实测**」（附命令/输出）或「**推断**」（未跑，仅由阅读/旁证得出）。

## 复审结论汇总

| 整改项 | 上一轮判定 | 本轮复审 | 依据 |
|---|---|---|---|
| **MEDIUM-1** 过度声称「全仓其余（全部）引用均用 `--abbrev=0`」 | NEEDS-REVISION | **已修复**（反向核验：新措辞本身无新过度声称） | §1 + A8 |
| **MEDIUM-2** CHANGELOG 悬空指针「见 AGENTS.md 记录」 | NEEDS-REVISION | **已修复** | §2 |
| **LOW-①** 新测试未断言 fail-open `returncode == 0` | LOW | **已修复**（变异实测非真空） | §3 |
| **LOW-②** `[Unreleased]` 内重复 `### 新增` | LOW | **已修复** | §4 |
| **LOW-③** ADR-014 引文含全角 `｜`(U+FF5C) | LOW | **修复不当（部分）** —— 全角字符已消除、表格列数正确，但换成了在 code span 内**不渲染**的 `&#124;`，引文**仍与真值 ASCII `|` 不符**，且比原错字更难读 | §5 |

**新引入问题**：1 项 LOW（即 LOW-③ 的 `&#124;` 换法本身，属"改法引入的新缺陷"）+ 2 项 NIT。**无 MEDIUM / 无 HIGH**。

**终审判定**：**APPROVED WITH NITS** —— **可以提交**。LOW-③ 建议在同一次提交内顺手改成已验证的写法（§5 有实测对照），但不构成阻断。

---

## 1. MEDIUM-1 是否真收窄 —— **已修复**

### 1.1 新措辞（**已实测**，`read AGENTS.md:148-150`）

`AGENTS.md:150`：

> **失准范围（据实，勿扩大）**：**活等式判据面**上仅本条如此（`check-protocol-consistency.py` CHECK 7 与本文件下方「release PR 必须普通 merge」条均已用 `--abbrev=0`）；但**历史任务记录里有多处同款副本**（`agate-workspace/tasks/{TAG0020,0027,0028,0029,0030}*/P8-release.md` 等 + `archived/docs-2026-08/HANDOFF-DOGFOODING-3TASKS.md`），它们是 frozen 快照、**本次不回改**，但**会被后来者照抄**——接手 G-5 时请以本条为准。另有 `docs/guides/worktree-dogfooding-guide.md` 两处用它**看输出**（非等式判据），可辩护。

`CHANGELOG.md:28-31`：

> **失准范围据实收窄**（独立评审指出我初稿的「全仓其余引用均用」是**过度声称**）：**活等式判据面**上仅此一处；但历史任务记录里有多处同款副本（`tasks/{TAG0020,0027,0028,0029,0030}*/P8-release.md` 等 + 归档 HANDOFF），属 frozen 快照、本次不回改，但会被照抄——已在 `AGENTS.md` 点名警示。

**判定**：原声称的两处（`AGENTS.md:149`、`CHANGELOG.md:25`）**均已替换**——全仓 `grep -n "全仓" AGENTS.md CHANGELOG.md` 仅剩 `CHANGELOG.md:28` 一处，且那处是**引述并否定**该过度声称（"我初稿的…是**过度声称**"），非主张本身（**已实测**）。措辞已**据实限定**（"活**等式判据面**上仅此一处"），并**点名历史副本存在**（TAG 列表 + 归档 HANDOFF + frozen 定性 + "会被照抄"的后果）。✅

### 1.2 反向核验：新措辞本身有无新的过度声称 —— **未发现新过度声称**

逐条把新措辞拆成可验证的主张，全部实测：

| # | 新主张（出处） | 核验命令 | 结论 |
|---|---|---|---|
| 1 | 「活**等式判据**面上仅此一处」 | `grep -rn "describe" --include=*.md . --exclude-dir={.git,.agate-tmp,tasks,archived,reviews} \| grep "=="` | **成立**（已实测）：全仓仅 2 命中——`AGENTS.md:148`（已修，带 `--abbrev=0`）与 `CHANGELOG.md:25`（**引述旧缺陷原文**，须保真）。此外 `check-protocol-consistency.py:472`、`agate-changes.py:104/151`、`agate/git-integration.md:186`、`worktree-dogfooding-guide.md:319/321/380` 均带 `--abbrev=0`（已实测）。**"等式判据面"这一限定词是关键**——其余无 `--abbrev=0` 的 describe 全部是「看当前版本」的指针/输出示例，不构成本条缺陷类型，故限定是**准确**的，不是话术性闪避 |
| 2 | 「CHECK 7…已用 `--abbrev=0`」 | `grep -n "abbrev=0" agate/scripts/check-protocol-consistency.py` | **成立**：L472 `["git","describe","--tags","--abbrev=0"]`（已实测） |
| 3 | 「本文件下方『release PR 必须普通 merge』条…已用」 | `sed -n '156p' AGENTS.md` | **成立**（已实测）：L156 含 `git describe --tags --abbrev=0` |
| 4 | 历史副本路径 `agate-workspace/tasks/{TAG0020,0027,0028,0029,0030}*/P8-release.md` | `ls -d agate-workspace/tasks/TAG00{20,27,28,29,30}*/` | **成立**：5 个目录均存在（已实测） |
| 5 | 归档 `archived/docs-2026-08/HANDOFF-DOGFOODING-3TASKS.md` | `ls -l` + `sed -n '88p'` | **成立**：文件存在，L88 即该等式判据（已实测） |
| 6 | worktree 指南**两处**用它看输出（非等式判据） | `sed -n '283,287p;475,479p' docs/guides/worktree-dogfooding-guide.md` | **成立**：L285 = `$ git describe --tags origin/main  # → v0.71.1-7-g8890a09 ✅ 正确`（**输出示例**）、L477 = 完成检查表第 9 项（**看输出**）。两处均**非** `== vX.Y.Z` 等式——"两处"这个**数字**准确（已实测） |
| 7 | 「**多**处同款副本」 | 同上 | **成立**：未给具体数字（用"多处"），且实际另有 **TAG0022** 也带同款等式判据（已实测：`agate-workspace/tasks/TAG0022-confirmed-problems/P8-release.md:160`）——被措辞里的「**等**」覆盖，**不构成漏报或过度声称** |

**特别核验「给了数字的地方数对不对」**：新措辞中仅有一个数字（"两处"，指 worktree 指南）——**实测 = 2，正确**；TAG 清单用了「等」显式表示非穷举，**没有**落入"声称历史副本共 N 处"的陷阱。✅ **未发现新的过度声称。**

### 1.3 残留观察（NIT，非缺陷）

- `CHANGELOG.md:30` 写 `tasks/{TAG0020,...}`，`AGENTS.md:150` 写 `agate-workspace/tasks/{...}` —— 同一事实两处路径前缀不一致。**但** `tasks/` 简写是 CHANGELOG **本文件既有惯例**（`CHANGELOG.md:1179`、`1190` 同用 `tasks/{Txxx}/retrospective.md`），故不判缺陷；`AGENTS.md` 用全路径亦正确（该文件是读者据以执行的地方）。**NIT-1**。

---

## 2. MEDIUM-2 是否修 —— **已修复**

**上一轮要求的判据**（**已实测**）：

```
$ grep -n "AGENTS.md 记录" CHANGELOG.md
(无输出, exit=1)
```

**新表述**（`CHANGELOG.md:19`）：

> 而真因是拉取失败（**本机 v0.77.0 升级时实际踩到：手动把 `fetch` 拆出来单独跑才看见真因**）。

**判定**：✅ 悬空指针已**删除**（不再是"见 AGENTS.md 记录"），改为**自足的第一人称陈述**，不再指向任何不存在的记录。反向核验"新表述与事实相符"：

- `grep -n "fetch" AGENTS.md` → **仅 1 命中**，即 `AGENTS.md:148` 的 `git fetch origin`（G-5 命令行本身）——**AGENTS.md 确实没有** v0.77.0 fetch 事故记录（**已实测**），故"删去括注"是正确修法（若保留指针则仍悬空）。
- `AGENTS.md:149` 记录的 v0.77.0 证据是 **`--abbrev=0` 那条**（`v0.77.0-3-gd666d4b`，**已实测** `git describe --tags origin/main` → `v0.77.0-3-gd666d4b`），**不是** fetch 事故——两者是不同事件，新措辞不再把二者混为一谈。✅
- 新表述的**剩余属性**：这是一条**关于历史事件的自述**，本机无终端留痕可供独立复现 ⇒ 我**无法证实也无法证伪**其"实际踩到"（**推断**：至少 `_ensure_repo` 旧实现在 `run_git` 丢 stderr 的情况下**结构上必然**产生该误导链，事故可信；但"v0.77.0 那次确实踩到"这一点本身**未实测**）。这不再是**文档缺陷**（无悬空指针、无与可 grep 事实相反的声称），只是**不可独立复核的历史陈述** —— 也正因如此，改用自述而非指针是**恰当**的。

---

## 3. LOW-① 断言是否加上且非真空 —— **已修复，且变异实测非真空**

**断言存在**（**已实测**，`agate/tests/unit/test_agate_version_install.py:830-835`）：

```python
# **最重的不回归项**：fail-open 必须保留——离线重装**已有**版本要能成功（BDD-4 判据 2）。
# 这条断言不可省：只测"出声"而不测"仍成功"，会把「改成 fail-closed」误判为通过，
# 而那恰恰破坏离线重装（本次修复的第一原则是"出声，不是变严"）。
assert result.returncode == 0, (
    f"fail-open 被破坏（离线重装已有版本应成功，实际 rc={result.returncode}）: {combined!r}"
)
```

**变异实测（fail-closed 复现）—— 断言转红 ✅**（在 `.agate-tmp/rr-<pid>/` 一次性副本内，同调用建→用→清）：

```
$ cp -a agate .agate-tmp/rr-$$/agate
$ python3 -  # 把 _ensure_repo 的 fetch 失败分支 "return repo, warn" → "sys.exit(1)"（fail-closed）
MUTATED OK
$ pytest agate/tests/unit/test_agate_version_install.py -q -p no:randomly -k fetch_failure_is_reported_not_silent
>       assert result.returncode == 0, (
E       AssertionError: fail-open 被破坏（离线重装已有版本应成功，实际 rc=1）: "WARNING: 无法从上游拉取新版本——git fetch 失败（fatal: '.../nonexistent-upstream' does not appear to be a git repository）；…"
E       assert 1 == 0
1 failed, 45 deselected in 0.18s
```

⇒ 该断言**确实在守护"fail-open 未被改成 fail-closed"**，**不是真空断言**（若只断 `WARNING in combined`，上面这次变异会**通过**——这正是上一轮 LOW-① 的实质风险，现已消除）。**已实测**，清理后 `.agate-tmp/rr-*` 不存在。

**另一条独立复核**（"先红后绿"在我手里也成立，**已实测**）：把 `agate-install.py` 换回 `HEAD` 版本（副本内），两个新用例**同时转红**：

```
FAILED test_fetch_failure_is_reported_not_silent
FAILED test_missing_version_error_mentions_fetch_failure
2 failed, 44 deselected in 0.34s
```

---

## 4. LOW-② 重复标题 —— **已修复**

**`[Unreleased]` 段内标题序列**（**已实测**，`awk` 取 `## [Unreleased]` 到 `## [0.77.0]` 之间的 `###`）：

| 行 | 标题 |
|---|---|
| 13 | `### 修复` ← 本批新增块（fetch + G-5 两条） |
| 33 | `### 新增` ← **唯一**，本次 ADR-014 条目与既有的「正文标记形态单源」条目**已合并在这一节内**（L35 ADR-014、L39 标记单源） |
| 54 | `### 变更` |
| 62 | `### 验证` |
| 74 | `### 独立评审查出并已修的 HIGH 缺陷（如实登记）` |
| 91 | `### 落地中据实更正的两处（设计未预见，实测发现）` |
| 99 | `### 修复` |
| 136 | `### 变更` |
| 143 | `### 验证` |
| 160 | `### 自伤事故登记` |
| 170 | `### 遗留（本次不做）` |

**判定**：✅ **L13/L33 是 `修复` → `新增`，不再有两个连续的 `### 新增`**；上一轮指的"新块被插在既有 `### 新增` 之前 → 两个相邻 `新增`"已被**合并**（`grep -c "^### 新增" CHANGELOG.md` = 57 是**全文件**历史版本计数，与判据无关；段内计数 = **1**）。

**残留说明（非回归，不计入）**：`[Unreleased]` 内仍有 2× `修复` / 2× `变更` / 2× `验证`（L99/L136/L143）。**这是改动前就有的文件形态**——**已实测** `git show HEAD:CHANGELOG.md` 的 `[Unreleased]` 同样是 2× `变更` + 2× `验证`（HEAD L30/L112、L38/L119）；本批只**新增**了顶部的 `修复`+`新增` 两块，**没有**新增任何重复类型，也未与既有块相邻。故 LOW-② 已闭环，此形态属既存风格问题，**不构成本次新引入问题**。

---

## 5. LOW-③ 全角竖线 —— **修复不当（部分修复，并引入一处 LOW 级新缺陷）**

### 5.1 已达成的一半

| 判据 | 命令 | 结果 |
|---|---|---|
| `agate/adr.md` 内无全角 `｜`(U+FF5C) | `grep -n "｜" agate/adr.md` | **空**（exit 1）✅ **已实测** |
| ADR-014 表格**列数仍正确** | `awk 'NR>=543&&NR<=547{n=split($0,a,"|");print n}'` | 5 行**全部 5 个 cell（4 个裸 `\|`）**，与表头/分隔行一致 ✅ **已实测** |
| 是否破坏表格结构 | GFM 渲染 `gfm-like`（`markdown_it`）| 渲染为**规范 `<table>`**，3 列 × 3 数据行，**无错位** ✅ **已实测** |

### 5.2 修复不当之处（**新引入问题，LOW**）

主 Agent 用的是 `&#124;`，但它落在 **code span 内部**（`agate/adr.md:545`）：

```
| `check-scope-resolved.py` | `^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*&#124;__)?` | 空白 / 列表符 / 引用 / **粗体** |
```

**HTML 实体在 code span 内不解码**——两个渲染器**一致实测**：

```
$ node -e "require('marked').parse(表行)"          # = 本仓 site/node_modules/marked（VitePress 站点同族）
<td><code>^\s*(?:[-*+]\s*)?(?:&gt;\s*)?(?:\*\*&amp;#124;__)?</code></td>

$ python3 -c "MarkdownIt('gfm-like').render(表行)"
<td><code>^\s*(?:[-*+]\s*)?(?:&gt;\s*)?(?:\*\*&amp;#124;__)?</code></td>
```

⇒ **读者看到的字面文本是 `&#124;`，不是竖线**。

**这为什么仍算"未达标"**：
- LOW-③ 的**目标**是"引文与真值一致（真值 ASCII `|`）"。修复后引文里的该位置是 `&`/`#`/`1`/`2`/`4`/`;` —— **仍不等于 ASCII `|`**；只是把一个**可读的错字**（`｜`）换成了一个**更不可读的转义残渣**（`&#124;`）。从**引文保真度**看是**横向移动**，从**可读性**看是**变差**。
- 讽刺点：ADR-014 的决策②正是"**文档（人读）可以复述，但必须指向权威源**"，其语境表的作用就是让人核对"三套正则哪不一样"。现在读者看到的是 `&#124;`，**恰恰在最需要人读的那个格子**。

**这不是"表格 `|` 污染"**：列数正确、结构正确（§5.1），所以**不升级为 MEDIUM**；属**引文保真/可读性**缺陷，与上一轮对 LOW-③ 的定级一致。

### 5.3 已验证的替代写法（**已实测**，供主 Agent 直接采用）

同一个表行、同一对渲染器，三种写法对照：

| 写法 | 渲染结果 | 判定 |
|---|---|---|
| `` `…&#124;…` ``（**当前**） | `<code>…&amp;#124;…</code>` | ❌ 显示 `&#124;` 字面量 |
| `` `…\|…` `` | `<code>…|…</code>` | ✅ **两边渲染器都把 `\|` 解为字面 `|`**（GFM 表格扩展） |
| `` `…|…` ``（裸竖线） | `` `X `` 单元格被**劈开** | ❌ 破坏表格 |

**推荐**：把 `adr.md:545` 的 `&#124;` 改为 **`\|`**（一个字符），即 `` `^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*\|__)?` ``。
- 为什么不用 `&#124;`：`marked`（本仓站点）与 `markdown-it`（VitePress）实测**在 code span 内不解码实体** ⇒ 读者看不到竖线。
- 为什么不用裸 `|`：会把单元格劈开（实测）。
- **更稳的选项**（若不愿依赖 `\|`）：把这段"三套正则对照"从**表格**挪到**列表/代码块**（表格外的 code fence 内裸 `|` 永远不会劈列）——代价是失去表格的三列并排对照。**取舍**：一处字符改动 vs 结构性重排，故首选 `\|`。
- ⚠️ **一处未实测（推断）**：GitHub 用的是 **cmark-gfm**，本机无该渲染器，我未能实测其对 `` `\|` `` 的等价行为（CommonMark 规范本身说"code span 内反斜杠转义无效"，GFM 表格扩展在**重写单元格**阶段处理 `\|`——`marked`/`markdown-it` 均如此）。**若要求 100% 稳**，选上面"移出表格"的方案；本仓主消费面（站点两套渲染器）已实测两种写法可用。
- 同时建议：**`｜` 的源头**仍在 —— `grep -c "｜" docs/design-notes/design-marker-single-source.md` = **1**（L76，**已实测**）。ADR-014 的语境表明写"逐字复制自设计说明"，本次只改了下游副本，**上游错字仍在**，下次再复制会**回流**。**NIT-2**：要么同步修设计说明 L76，要么在 ADR-014 该行加一个"（权威源此处有笔误，已按真值校正）"的注记——后者更符合"判据单源、文档可复述"的自洽要求。

---

## 6. 必跑门禁 —— **全部已实测，逐项符合预期**

| # | 命令 | 实测结果 |
|---|---|---|
| 1 | `python3 -m pytest agate/tests/unit/test_agate_version_install.py -q -p no:randomly` | **46 passed in 5.83s** ✅（`--collect-only` 亦为 46） |
| 2 | `python3 agate/scripts/check-protocol-consistency.py` | **0 ERROR / 386 WARNING**（rc=0）✅ —— WARNING 数与上一轮一致，未因本批新增 |
| 3 | `~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!** ✅ |
| 4 | `AGATE_ROOT=/home/kity/oclab/agateon/agate python3 agate/scripts/check-structure-consistency.py` | **S0-numbers / S1-phases / S2-workflow / S3-cards / S4-scripts / S5-schema / S6-references 全 OK** ✅（已确认本 checkout **无** `.agate-version`） |
| 5 | `python3 -m pytest agate/tests/unit -q -p no:randomly` | **1 failed, 2313 passed, 2 skipped in 168.91s** ✅ —— 唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（`opencode 不在 PATH`，**既有环境问题**，非本批） |
| 6 | `python3 -m pytest agate/tests/regression agate/tests/integration -q -p no:randomly`（加跑） | **195 passed in 45.40s** ✅ |

---

## 7. 逐项审查（A1–A8，仅就本轮改动面）

| # | 审查项 | 结论 | 说明 |
|---|---|---|---|
| A1 | 文档→脚本对齐 | **ALIGNED** | 本轮**未改** `agate-install.py`（diff 与上一轮一致）；`_run_git_capture`(L157) / `_ensure_repo`(L174, 返回 `(repo, warn)` L199-200) / `_install_version(..., fetch_warning=None)`(L243) / 真因提示(L264, L460) 与 CHANGELOG 描述逐条对齐（**已实测**） |
| A2 | 脚本→文档对齐 | **ALIGNED** | `_ensure_repo` docstring 的 fail-open/fail-silent 语义成文；CHANGELOG:15-23 与之一致 |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** | 上一轮 MEDIUM-1/2 的两处传播缺口**已闭合**；新增的"历史副本存在"事实**已双向绑定**：`CHANGELOG.md:31`「已在 `AGENTS.md` 点名警示」↔ `AGENTS.md:150` 实际点名（**已实测**，指针可解析——与 MEDIUM-2 的悬空指针形成对照） |
| A4 | 测试覆盖 | **ALIGNED** | §3 变异实测证明 `returncode == 0` 断言**非真空**；§6 提供全量实跑计数 |
| A5 | 下游影响 + 文档传播 | **ALIGNED** | 上一轮的悬空指针已除；无破坏性变更（`_ensure_repo` 3 个调用点全在同文件） |
| A6 | 锚点表覆盖 | **ALIGNED** | 无新增脚本/锚点；consistency 0 ERROR |
| A7 | 设计原则一致性 | **ALIGNED** | ADR-014 五节齐备、编号连续、与 ADR-002/006/013 互补；**但**其语境表引文因 §5 的 `&#124;` **与"引文须与真值一致"的自设原则相抵**（不影响 ① ② ③ 三条决策语义）——建议随 §5.3 一并收口 |
| A8 | 声称-命令绑定 | **ALIGNED**（本批声称新增 1 项 NIT） | 见下 |

### A8 逐条：本轮**新增/变更的声称** → 命令 → 结论

| # | 新声称（出处） | 产出它的命令 | 结论 |
|---|---|---|---|
| 1 | 「活等式判据面上仅此一处」（AGENTS.md:150 / CHANGELOG.md:29） | `grep -rn "describe" … \| grep "=="`（排除 tasks/archived/reviews） | **成立**（已实测，2 命中：已修的 G-5 + CHANGELOG 引文） |
| 2 | 「CHECK 7 与本文件下方 merge 条均已用 `--abbrev=0`」 | `grep -n "abbrev=0" check-protocol-consistency.py` / `sed -n '156p' AGENTS.md` | **成立**（已实测：L472 / L156） |
| 3 | 「历史任务记录里有多处同款副本 + 归档 HANDOFF」 | `ls -d agate-workspace/tasks/TAG00{20,27,28,29,30}*/` + `sed -n '88p' archived/.../HANDOFF-DOGFOODING-3TASKS.md` | **成立**（已实测，5 目录 + L88；另有 TAG0022 被「等」覆盖） |
| 4 | 「worktree 指南**两处**用它看输出（非等式判据）」 | `sed -n '283,287p;475,479p' docs/guides/worktree-dogfooding-guide.md` | **成立**，数字 = 2 **正确**（已实测） |
| 5 | 「已在 `AGENTS.md` 点名警示」（CHANGELOG.md:31） | `sed -n '150p' AGENTS.md` | **成立**（已实测，指向实际存在的内容） |
| 6 | v0.77.0 fetch 事故「实际踩到」（CHANGELOG.md:19，**自述非指针**） | 无命令可产出（历史事件，本机无留痕） | **不可复核**（推断）：不再是文档缺陷（无悬空指针），但**这条具体的历史断言我无法证实**——已在 §2 如实标注 |
| 7 | ADR-014 引文 `…(?:\*\*&#124;__)?`（adr.md:545） | `python3 -c "agate_markers.pattern('SCOPE+')"` = `(?:(?:^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*\|__)?))(?!`)…` | **不成立/不忠实**（已实测）——真值是 ASCII `|`，非 `&#124;`；且渲染后读者看到 `&#124;`。**见 §5** |

**A8 判定**：本轮新声称 **6/7 成立、1 不忠实（第 7 条，LOW）**，且**第 1–5 条恰是上一轮被判 MISALIGNED 的那批**——**过度声称已消除，替换为可 grep 复核的限定语**，这正是本轮整改的核心目标，达成。第 7 条是**上一轮已存在的 LOW 引文保真问题**，本轮**改法未达标**（§5）。

---

## 8. 新引入问题（复审判定）

| # | 级别 | 问题 | 证据 | 建议 |
|---|---|---|---|---|
| N-1 | **LOW** | 修 LOW-③ 时用 `&#124;`，但它位于 **code span 内**，`marked`（本仓站点）与 `markdown-it`（VitePress）**均不解码实体** ⇒ 读者看到字面 `&#124;`；ADR-014 引文**仍不等于真值 ASCII `|`**，且比原 `｜` 更不可读 | §5.2（两渲染器实测输出） | 改 `\|`（已实测渲染为 `|`）；若求绝对稳，把该对照表移出表格 |
| N-2 | **NIT** | `｜` 的**上游源头**未修：`docs/design-notes/design-marker-single-source.md:76` 仍含 U+FF5C（**已实测** count=1），ADR-014 自称逐字复制自它 ⇒ 下次复制会回流 | `grep -c "｜" docs/design-notes/design-marker-single-source.md` = 1 | 同步修上游，或在 ADR-014 该行加"按真值校正"注记 |
| N-3 | **NIT** | `CHANGELOG.md:30` 用 `tasks/…` 简写、`AGENTS.md:150` 用 `agate-workspace/tasks/…`，同一事实两种路径前缀 | §1.3 | 可保留（CHANGELOG 本文件既用 `tasks/{Txxx}/…` 简写，见 L1179/L1190）；如需统一则对齐 CHANGELOG 侧 |

**已核查但未发现问题的项**（**均已实测**）：
- **表格 `|` 污染**：AGENTS.md / CHANGELOG.md 新增行**均非表格行**（无裸 `|`）；adr.md 表行 cell 数 5/5/5/5/5 一致，GFM 渲染为规范 3 列表格。**未发现**污染。
- **数字与命令脱钩**：本轮新增措辞中**唯一数字**是"两处"，**经实测 = 2**；其余用"多处/等"显式非穷举。
- **声称与实测相反**：逐条核验 §1.2 / A8 第 1–5 条，**未发现**任何与 `grep`/`git` 可证事实相反的声称。
- **改动集一致性**：`git status --short` 显示 5 个 staged `M`、**无 unstaged 改动**；staged 统计 +205/−10 = 上一轮 +198/−10 **+ 7 行**（正是 §3 的 3 行注释 + 3 行断言 + 1 空行）⇒ **代码路径本轮未被改动**，上一轮对实现的端到端验证**仍然有效**。

---

## 9. 范围外观察（**非本次引入**，如实登记）

- `CHANGELOG.md:71-72`（`[Unreleased]` 内**既有**段落）写 `unit **2309 passed**` / `count-tests **2529**`。本轮实测：unit **2313 passed**（`pytest --collect-only` 全仓 **2533** 条），本批新增 2 条用例 ⇒ 若扣掉本批，HEAD 口径应为 **2311 / 2531**（**已实测**：把测试文件换回 `HEAD` 版后 collect = **2531**）。即该两行相对 HEAD 现状**偏低 2**。
  **判定归属**：该两行文本与 `HEAD` **逐字相同**（**已实测** `git show HEAD:CHANGELOG.md | grep -n "2309\|2529"` 命中 L47/L48），本 diff 的 hunk 只在 `+13..32` 与 `+35..38`，**未触碰**该区域 ⇒ **非本次引入**、**不在本轮 6 项范围内**。**推断**（未实测）：属前一批（标记单源）落盘后又加了 2 条用例而未刷新该行。**不阻断本次提交**；若主 Agent 顺手刷新，建议整段重跑一次并同步 `unit/regression/integration/count-tests` 四个数。

## 10. 未实测项（如实标注）

- GitHub 的 **cmark-gfm** 对表格 code span 内 `` `\|` `` 的处理**未实测**（本机无该渲染器）—— 已在 §5.3 标为推断，并给出不依赖它的备选方案。
- `//? v0.77.0 "fetch 失败实际踩到"` 这一**历史断言本身**不可复现（无终端留痕）⇒ §2 标为不可复核。
- 未在 Windows 原生 / DSH 受限 harness 下重跑（本机 Linux；`_run_git_capture` 继承 `encoding="utf-8", errors="replace"`，与 `run_git` 同口径 ⇒ **推断**无平台回归）。
- 未做提交后 / CI 侧验证（改动未提交，符合只读纪律）。

---

## 11. 终审判定

# **APPROVED WITH NITS**

**明确结论：可以提交。**

**理由（按上一轮的闭环规则）**：

1. **两项 MEDIUM 均已修复，且经反向核验**：
   - **MEDIUM-1**：过度声称已**据实收窄**为"活**等式判据**面上仅此一处 + 历史副本已被点名 + frozen 不回改"；反向核验**新措辞的 7 条可验证主张逐条成立**（含唯一数字"两处"= 2 正确），**未引入新的过度声称**（§1）。
   - **MEDIUM-2**：`grep -n "AGENTS.md 记录" CHANGELOG.md` **为空**；新表述自足、不再指向不存在的记录，且与"AGENTS.md 只有 `--abbrev=0` 记录、无 fetch 事故记录"这一实测事实**不冲突**（§2）。
2. **LOW-① 已修复且经变异证明非真空**（fail-closed 变异 → 断言转红，rc=1），LOW-② 已修复（段内唯一 `### 新增`）。
3. **LOW-③ 修复不当（部分）**：全角 `｜` 已消除、表格列数正确、无结构污染，但换成 code span 内**不渲染**的 `&#124;`，引文**仍不忠于真值 ASCII `|`**。**级别仍为 LOW**（不破坏结构、不影响 ADR 决策语义），且**已给出经两套渲染器实测的替代写法**（§5.3）。
4. **门禁全绿**：46 passed / 0 ERROR / ruff 全绿 / structure S0-S6 OK / 全量 unit = 1 failed（**既有 opencode**）+ 2313 passed + 2 skipped，与预期**逐项吻合**；加跑 regression+integration = 195 passed。
5. **代码路径本轮未被改动**（staged 增量 = 7 行测试断言），上一轮对实现（fail-open 保留 / fail-silent 消除 / 缺 tag 归因 / 退出码 / `_run_git_capture` 必要性）的端到端验证**仍然有效**，本轮无需重做 e2e。

**提交建议（不阻断，成本各 ≤1 行）**：
- 建议在同一提交内把 `agate/adr.md:545` 的 `&#124;` 改为 `\|`（**已实测** `marked` 与 `markdown-it` 均渲染为 `|`）——否则 ADR-014 的引文仍与其"引文须与事实一致"的自设主旨相抵；若不愿依赖 `\|`，则把三套正则对照移出表格（§5.3）。
- 可选：把 `NIT-2`（上游设计说明 L76 的 `｜`）与 `NIT-3`（路径前缀）留给后续文档批次。

**留痕**：本轮全部 scratch 位于 `.agate-tmp/` 且已清空（**已实测**无 `rr-*`/`rg-*`/`hc-*` 残留）；复审前后 `git status --short` 一致，**未对被评审改动集做任何写操作**。
