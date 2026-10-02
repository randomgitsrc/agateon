---
review_date: 2026-10-02
reviewer: protocol-alignment-review
status: needs-revision
change_summary: 修 agate-install.py 的 fetch fail-silent（保留 fail-open + WARNING + 真因透传）、修 AGENTS.md G-5 判据缺 --abbrev=0、新增 ADR-014「判据单一权威源」
files_changed: [AGENTS.md, CHANGELOG.md, agate/adr.md, agate/scripts/agate-install.py, agate/tests/unit/test_agate_version_install.py]
---

# 协议-脚本对齐审查

**分支**：`fix/installer-fetch-failopen`（改动集**未提交**，已 staged，5 文件 / +198 −10）
**审查纪律**：只读。全部 scratch 在 `<仓库根>/.agate-tmp/` 一次性副本内「建→用→清」同调用完成（已核实临时目录事后不存在）。未对被评审仓库做任何写操作。
**证据口径**：本报告严格区分「**已实测**」（附命令/输出）与「**推断**」（未跑、仅由代码/文档阅读得出）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（G-5 历史副本 + CHANGELOG 悬空指针） |
| A4 | 测试覆盖 | ALIGNED（含 1 项 nit：fail-open 无断言守护） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（CHANGELOG「见 AGENTS.md 记录」悬空） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED**（「全仓其余引用均用 `--abbrev=0`」为过度声称） |

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**意图声称的修法**（任务书 / CHANGELOG）：保留 fail-open，但输出 WARNING + 把原因传给下游报错。

**脚本实现**（`agate/scripts/agate-install.py`）：
- `_run_git_capture()`（L157-169）：`subprocess.run(..., capture_output=True)` 返回 `(rc, stdout, stderr)`。
- `_ensure_repo()`（L192-203）：fetch 失败 → `sys.stderr.write("WARNING: ...")` + `return repo, warn`（**不 exit**）。
- `_install_version(..., fetch_warning=None)`（L243, L260-266）：`PackageError` 分支追加「真因提示」后 `sys.exit(1)`。
- `_cmd_install`（L454-466）：`repo, fetch_warning = _ensure_repo(...)`，两条分支都透传。

**结论**：ALIGNED。文档/意图与实现语义一致（fail-open 保留 + 出声 + 归因）。

### A2: 脚本→文档对齐 — ALIGNED

`agate_common.py::run_git`（L67-86）docstring 明写「返回 `(returncode, stdout)`」，与 `_run_git_capture` docstring 的「它只返回 `(rc, stdout)`，**stderr 被丢弃**」**一致**——新函数的必要性论证与既有实现的自我描述不冲突。脚本的 fail-open 语义在 `_ensure_repo` docstring 中成文，CHANGELOG 同步标注。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（已知连锁）**：`AGENTS.md` / `CHANGELOG.md` / `adr.md` / 脚本 / 测试 5 文件互相自洽，无漏改。

**A3b（反向传播 — 应被影响但未在 diff 中的文件）**：

1. **G-5 判据的历史副本未同步**（**已实测**，见 A8）——`agate-workspace/tasks/{TAG0020,TAG0027,TAG0028,TAG0029,TAG0030}*/P8-release.md` 共 5 处 + `archived/docs-2026-08/HANDOFF-DOGFOODING-3TASKS.md` 1 处，仍带同一缺 `--abbrev=0` 的等式判据。**这些是历史记录（frozen snapshot），不构成"活判据"**，但它们是同一模板的副本、会被后来者照抄 ⇒ 建议在 G-5 注记中点名"历史任务副本已知未回改"，而非声称"其余均用"。
2. **`docs/guides/worktree-dogfooding-guide.md`（活文档）2 处**：L285（演示 `git describe --tags origin/main` **输出**形态，用于展示漂移距离，**非等式判据**）、L477（P8 完成检查表第 9 项 `... && git describe --tags origin/main`，**非等式判据**，用途是"看输出"）。二者**不属于**本次要修的缺陷类型（缺陷是 `== vN.N.0` 等式判据），但**推翻了"全仓其余引用均用 `--abbrev=0`"的字面声称**。
3. **CHECK 7 代码**（`check-protocol-consistency.py:472`）已用 `["git","describe","--tags","--abbrev=0"]` — 无需改动（**已实测**）。

**影响**：无行为影响（历史记录不改判据），但**文档声称与事实相反**，属 A8 过度声称。

### A4: 测试覆盖 — ALIGNED（1 nit）

**实跑证据**（**已实测**）：

```
$ python3 -m pytest agate/tests/unit/test_agate_version_install.py -q -p no:randomly
..............................................                           [100%]
46 passed in 5.70s
```

**全量 unit**（**已实测**）：

```
$ python3 -m pytest agate/tests/unit -q -p no:randomly
1 failed, 2313 passed, 2 skipped in 169.88s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
  → Failed: opencode 不在 PATH：环境未就绪，BDD 判 FAIL
```

与任务书预期（1 failed 既有 opencode + 2313 passed + 2 skipped）**逐项吻合**。

**「先红后绿」声称已独立复核**（**已实测**，mutation 在一次性副本内）：

```
$ cp -a agate/ .agate-tmp/mut-$$/agate
$ git show HEAD:agate/scripts/agate-install.py > .agate-tmp/mut-$$/agate/scripts/agate-install.py
$ pytest -k "fetch_failure_is_reported_not_silent or missing_version_error_mentions_fetch_failure"
FAILED test_fetch_failure_is_reported_not_silent
FAILED test_missing_version_error_mentions_fetch_failure
2 failed, 44 deselected
```

⇒ 新增 2 用例确实「改动前红、改动后绿」。

**nit**：新测试**未断言** fail-open 的 `returncode == 0`——`_install_with_broken_remote` 只断言了**首次**安装 `first.returncode == 0`（L~805），第二次（broken remote）的 `result` 在 `test_fetch_failure_is_reported_not_silent` 中**未断言 rc**。即"fail-open 未被破坏"这一**最重的不回归项没有测试守护**，只能靠本次 e2e 人工验证（见下）。建议补一行 `assert result.returncode == 0`。

### A5: 下游影响 + 文档传播 — MISALIGNED

- 无破坏性变更：`_ensure_repo` 由返回 `repo` 改为返回 `(repo, fetch_warning)`，但**全部 3 处调用点都在同文件内**（L454/462/466，**已实测** `grep _ensure_repo\|_install_version`），无外部 import —— 属私有函数，无 API 破坏。
- `_install_version` 新增可选参数 `fetch_warning=None`，向后兼容。
- **缺陷**：`CHANGELOG.md:19` 写「**该链条在 v0.77.0 升级时实际发生**（见 AGENTS.md 记录）」，但 `AGENTS.md` **没有任何**该链条的记录（**已实测** `grep -n "fetch\|拉取\|Not a valid object\|v0.77.0" AGENTS.md` 仅命中 G-5 的 `git fetch origin` 与注记中的 `v0.77.0-3-gd666d4b`）⇒ **悬空指针**。修法：删去括注，或把 v0.77.0 事故链如实补入 AGENTS.md。

### A6: 锚点表覆盖 — ALIGNED

`agate/adr.md` 不在 CHECK 9 锚点面（**已实测** `grep -rn "adr.md" agate/scripts/check-*.py` 空）。新增 ADR 不引入脚本锚点。`check-protocol-consistency.py` 0 ERROR（**已实测**）。`check-structure-consistency.py`（`AGATE_ROOT=<checkout>/agate`）S0-S6 全 OK（**已实测**）。

### A7: 设计原则一致性 — ALIGNED

**ADR-014 格式符合本文件既有约定**（**已实测**对比 001/002/006/011/013）：`## ADR-014: <标题>` + `### 状态` / `### 语境` / `### 决策` / `### 理由` / `### 后果`，五节齐备；编号在 ADR-013 之后连续；`### 状态` 写「已接受（2026-10-02，PR #388 / 设计 ...）」，与 ADR-013「已接受（2026-09-09，TAG0034 / RM-AG0060）」同格式。

**无重复 / 无矛盾**：ADR-014 决策三条（判据单源 / 文档可复述 / 形态判据不做语义判断）与 ADR-002（可判定性）、ADR-006（同源盲区）、ADR-013（gate 生产者无关性）**互补**，ADR-014 正文明确把自己与 ADR-002/006/013 关联（L575），未改写任何既有决策。ADR-001/011 无关。

**引用数字抽查**（对照 `docs/design-notes/design-marker-single-source.md`，**已实测**）：

| ADR-014 声称 | 设计说明出处 | 结论 |
|---|---|---|
| 改 1 个标记形态被迫同步 **14** 个文件、第一轮漏 **5** 处（**36%**） | L45-58（18 commit / 14 形态同步面 / 5 处 / 36%） | 一致 |
| **6 种**书写形态里 **3 种**分叉 | L83-94 | 一致 |
| `DESIGN_GAP` 现状判据散在 **32** 处 | L32（14 脚本/测试 + 18 文档 = 32） | 一致 |
| 存量标记 **45 种** | L19 | 一致 |
| 逐 P7 对账 **59 vs 121 = 2.05×** | L420 | 一致；**本次独立复算**：当前 `pattern("DESIGN_GAP")` vs `count_design_gap` 在 36 个 P7 文件上 **59 vs 59、差异文件 0** ⇒ 证明修复后**已等价**，121 是修复前的偏宽值（L427-431）——数字自洽 |

**一处保真度 nit**（LOW）：ADR-014 表内 `check-scope-resolved.py` 的"正则"写作 `^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*｜__)?`，其中 `｜` 是**全角 U+FF5C**（**已实测** `ord == 0xff5c`），而真实正则（`agate_markers.pattern("SCOPE+")`）是 **ASCII `|`**（**已实测**：`(?:(?:^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?))(?!`)\[SCOPE\+\](?!\w)`）。该行系从设计说明 L76 **逐字复制**（同一处全角错字，L76 亦为 U+FF5C）。属**引文保真度**问题，不影响 ADR 的决策语义。ADR 内表格 `|` 计数正常（4 pipes/行，无结构污染）。

### A8: 声称-命令绑定 — MISALIGNED

| # | 声称（出处） | 产出它的命令 | 结论 |
|---|---|---|---|
| 1 | fetch 失败 → WARNING 含 git 原始原因 | `HOME=<scratch> AGATE_REPO_URL=<up> agate-install.py v0.43.0`（remote 已改坏） | **成立**（已实测，见下） |
| 2 | 缺 tag 报错归因到 fetch | 同上，改传 `v9.9.9` | **成立**（已实测） |
| 3 | fail-open 未被破坏（离线重装已有版本仍 exit 0） | 同上 e2e（2 变体：已装版本重装 / 未装但本地有 tag 的真实构建路径） | **成立**（已实测） |
| 4 | `git describe --tags origin/main` 无 `--abbrev=0` 时判据恒不成立（v0.77.0 → `v0.77.0-3-gd666d4b`） | `git describe --tags origin/main`／`--abbrev=0 origin/main` | **成立**（已实测，输出 = 声称值） |
| 5 | 「v0.77.0 升级时该链条**实际发生**（见 AGENTS.md 记录）」 | `grep -n "fetch\|拉取\|Not a valid object\|v0.77.0" AGENTS.md` | **不成立**——AGENTS.md 无该记录（悬空指针），见 A5 |
| 6 | 「本节下方的 merge 条与**全仓其余引用均用 `--abbrev=0`**」 | `grep -rn "git describe --tags origin/main"` 全仓逐行判定 | **不成立**（过度声称），见下 |
| 7 | `agate_common.run_git` 丢弃 stderr | 读 `agate_common.py:67-86`：`return proc.returncode, proc.stdout` | **成立**（已实测读码） |
| 8 | ADR-014 各数字（14/5/36%/6/3/32/45/59vs121） | 对照 `design-marker-single-source.md` + 独立复算 | **成立**（择要抽查 8 项全一致） |

**关于第 6 条的实测明细**（**核心核验项**，`grep -rn "git describe --tags origin/main" . | grep -v .git | grep -v .agate-tmp`，逐行判定 `--abbrev=0` 有无）：

| 位置 | 类型 | 判据? | 带 `--abbrev=0`? |
|---|---|---|---|
| `CHANGELOG.md:25` | 本次**引述旧缺陷原文** | 否（引文） | 否（**正确**，引文须保真） |
| `AGENTS.md:148`（G-5 本体） | 活判据（等式） | 是 | **已修 ✅** |
| `AGENTS.md:149` | 本次注记引述 | 否 | 否（同一行内含 `--abbrev=0`，属说明） |
| `AGENTS.md:155`（merge 条） | 文本说明 | — | 是 ✅ |
| `docs/guides/worktree-dogfooding-guide.md:285` | 活文档，**输出示例**（展示漂移形态） | 否 | 否（**合理**） |
| `docs/guides/worktree-dogfooding-guide.md:477` | 活文档，P8 完成检查表第 9 项 | 半（用"看输出"而非等式） | 否 |
| `tasks/{TAG0020,TAG0027,TAG0028,TAG0029,TAG0030}/P8-release.md` 5 处 | **历史任务记录**（等式判据副本） | 是（但为 frozen 记录） | 否 |
| `archived/docs-2026-08/HANDOFF-DOGFOODING-3TASKS.md:88` | 归档记录 | 是（frozen） | 否 |

**判定**：**"孤立失准"这一句在"活判据面"上大体成立**（唯一活等式判据 = AGENTS.md G-5，已修），但**"全仓其余引用均用 `--abbrev=0`"的字面声称不成立**——至少 5 处**历史任务记录**与归档 HANDOFF 携带同一缺陷副本，另有 2 处活文档（`worktree-dogfooding-guide.md`）用无 `--abbrev=0` 的 describe（非等式判据，可辩护）。⇒ 声称**过度**，应改为限定语（如「本文件的其余引用」+「历史任务副本已知未回改」）。**CHANGELOG.md:25 同一句同样过度**（其「全仓其余全部引用」措辞更绝对）。

## 新引入问题（按严重度）

### MEDIUM-1：A8 过度声称「全仓其余引用均用 `--abbrev=0`」
- **位置**：`AGENTS.md:149`、`CHANGELOG.md:25`（「与同文件…条及**全仓其余全部引用**…互相矛盾」）。
- **事实**：全仓另有 5 处历史任务记录 + 1 处归档记录 + 2 处活文档使用无 `--abbrev=0` 的 describe（见 A8 表）。
- **为何是问题**：本批正是以"判据必须与事实绑定"为主题（A8 硬规则 + ADR-014 主旨），而本批自己的声称就与 `grep` 可证的事实相反——**自我例证失败**。
- **建议**：把措辞收窄为「`AGENTS.md` 内其余引用均用 `--abbrev=0`；历史任务记录中的同款副本（TAG0020/0027/0028/0029/0030 等）属 frozen 快照，本次不回改」。

### MEDIUM-2：CHANGELOG 悬空指针「见 AGENTS.md 记录」
- **位置**：`CHANGELOG.md:19`。
- **事实**：`AGENTS.md` 无 v0.77.0 fetch 失败事故的记录（已实测 grep）。
- **建议**：删括注，或补录该事故链到 AGENTS.md。

### LOW-1：新测试未断言 fail-open 的 exit 0
- 第二次（broken remote）安装结果未断言 `returncode == 0`，最重的不回归项缺测试守护。

### LOW-2：`CHANGELOG.md` `[Unreleased]` 出现两个 `### 新增` 标题
- L30 与 L37（本次新增块被插在既有 `### 新增` 之前）。建议合并为一节。

### LOW-3：ADR-014 引文正则含全角 `｜`（U+FF5C）
- 与真实正则不符（真值为 ASCII `|`）；继承自设计说明 L76 的同一错字。属引文保真度，非结构污染（表格 pipe 数正常）。

## 必须自核验项 —— 实测结果（核心）

**① fail-open 是否保留（最重要不回归项）— 已实测，成立。**

端到端，自建最小上游 repo（含 `v0.43.0` tag）+ `HOME`/`AGATE_REPO_URL` 重定向：

```
STEP1 install latest           → rc=0，已安装 latest → v0.48.0
STEP2 git remote set-url origin <不存在的路径>     （模拟离线/不可达）
STEP3 install v0.43.0（本地有 tag、尚未安装 → 走真实 list_package/materialize 路径）
      → rc=0，输出 WARNING，v0.43.0 目录内容完整落盘 ✅
```

另一变体（重装**同一**已装版本）：`rc=0`，输出 `v0.43.0 已安装，跳过（幂等）` + WARNING。⇒ **fail-open 确认保留**。

**② fail-open ≠ fail-silent — 已实测，成立。**

fetch 失败时 stderr 实际输出（**含 git 原始原因**）：

```
WARNING: 无法从上游拉取新版本——git fetch 失败（fatal: '<path>/nope' does not appear to be a git repository）；将使用**本地已有的** tag 继续。若接下来报「版本不存在」，真因是本次拉取失败而非版本号写错。
```

**③ 缺 tag 报错是否归因到 fetch — 已实测，成立（且与基线对照）。**

| 版本 | 输出 |
|---|---|
| **基线（HEAD，改动前）** | `错误: 无法从 v9.9.9 构建本体包：git ls-tree -r -z --full-tree v9.9.9 失败: fatal: Not a valid object name v9.9.9` （**无任何 fetch 提示**，`grep -ci fetch` = **0**） |
| **改动后** | 同上错误行 **+** `真因提示：本地 tag 可能已过期——git fetch 失败（fatal: '<path>/nope' does not appear to be a git repository）。` **+** `请确认网络/仓库地址可达后重试；…`（`grep -ci fetch` = **2**） |

**④ 退出码 — 已实测，成立**：不存在的版本 `rc=1`（≠0）；已有版本离线重装 `rc=0`。

**⑤ `_run_git_capture` 必要性（核验你的声称）— 已实测，声称**成立**。**
`agate_common.py:67-86`：函数体为
```python
proc = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, env=...)
return proc.returncode, proc.stdout
```
**只返回 `(rc, stdout)`，stderr 确实被丢弃**，docstring 亦自述"返回 `(returncode, stdout)`"。⇒ 新函数**不多余**（且与原函数在 `GIT_DIR` 环境处理上同样不做清洗，行为对等，无隐性回归）。

**⑥ AGENTS.md 判据修复 — 已实测，成立。**
```
$ git describe --tags origin/main            → v0.77.0-3-gd666d4b
$ git describe --tags --abbrev=0 origin/main → v0.77.0
```
与声称的 `v0.77.0-3-gd666d4b` 逐字吻合；`--abbrev=0` 修正后判据可成立。**(6b)** 见 A8/MEDIUM-1：修正本身正确，但"其余引用均用"的**广度声称过度**。

**⑦ ADR-014 质量 — 已实测，ALIGNED（1 LOW nit）。** 见 A7。

**⑧ 必跑命令 — 已实测，全部符合预期：**

| 命令 | 结果 |
|---|---|
| `pytest agate/tests/unit/test_agate_version_install.py -q -p no:randomly` | **46 passed** ✅ |
| `pytest agate/tests/unit -q -p no:randomly` | **1 failed**（既有 `opencode` 不在 PATH）**+ 2313 passed + 2 skipped** ✅ |
| `python3 agate/scripts/check-protocol-consistency.py` | **0 ERROR**（386 WARNING）✅ |
| `~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!** ✅ |
| `AGATE_ROOT=<checkout>/agate python3 agate/scripts/check-structure-consistency.py` | S0-S6 **全 OK** ✅ |

**⑨ 新引入问题扫描（表格 `|` 污染 / 数字与命令脱钩 / 声称与实测相反）— 已实测。**
- 表格 `|` 污染：ADR-014 表格 pipe 数正常；**未发现**新增破坏性表格污染（唯一 `｜` 全角在行内 code span 里，不破坏表格结构）。
- 数字与命令脱钩：ADR-014 抽查 8 项全部可溯源到设计说明/可复算；**发现 2 处**（MEDIUM-1 / MEDIUM-2）。

## 未实测项（如实标注）

- 未在 DSH/Windows 等受限 harness 或 Windows 原生下重跑（本机 Linux；`_run_git_capture` 继承 `encoding="utf-8", errors="replace"`，与 `run_git` 同口径 ⇒ **推断**无平台回归）。
- 未验证 v0.77.0 事故链的真实历史（我无法访问当时的终端记录）⇒ **推断**其"实际发生"不可由仓库证据支持，故按悬空指针处理（A5）。
- 未对被评审改动集做提交后/CI 侧验证（改动未提交，符合只读纪律）。

## 总体判定

# **NEEDS-REVISION**

**代码实现（本次最主要的技术目标）质量良好且经独立端到端证明**：fail-open 保留、fail-silent 被消除、缺 tag 报错归因到 fetch、退出码正确、`_run_git_capture` 必要性成立、46 用例含真实"先红后绿"、必跑门禁全绿。**是否可提交：否，需先修 2 项 MEDIUM**（均由本批**自己的文档声称**引入，非代码缺陷）：

1. **MEDIUM-1/A8**：收窄 `AGENTS.md:149` 与 `CHANGELOG.md:25` 的「全仓其余（全部）引用均用 `--abbrev=0`」——该声称被 `grep` 证伪（5 处历史任务记录 + 1 归档 + 2 处活文档）。**这一点尤其重要：本批主旨是"判据单源 / 声称须与事实绑定"，若自身的广度声称与可 `grep` 的事实相反，等于自我例证失败。**
2. **MEDIUM-2/A5**：修 `CHANGELOG.md:19` 的悬空指针「见 AGENTS.md 记录」（AGENTS.md 无该记录）。

**LOW（可与上述一并在同一次修订内收口，不单独阻断）**：LOW-1 补 `assert result.returncode == 0`；LOW-2 合并重复的 `### 新增`；LOW-3 修正 ADR-014 全角 `｜`。

修完 2 项 MEDIUM（LOW 一并处理更佳）后即可 `APPROVED`；**代码本身无需返工**。
