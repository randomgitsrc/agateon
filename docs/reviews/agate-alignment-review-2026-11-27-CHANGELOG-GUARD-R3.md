# 协议-脚本对齐审查（第三轮 / 收敛确认）— CHANGELOG 质量判据（RM-AG0117）

> 评审基线：`edb63b58`（HEAD，分支 `fix/changelog-quality-guard`）。
> ⚠️ **重要状态**：该分支**已合并进 `origin/main`**（`ffdff420` = PR #485，`git merge-base --is-ancestor HEAD origin/main` 返回 0）。
> 该判据**尚未随任何 tag 发布**（`git tag --contains HEAD` 为空；稳定版 `~/.agate/v0.83.4/agate/scripts/pre-commit-gate.py` 无 `2z2`）。
> 前两轮报告：`agate-alignment-review-2026-11-27-CHANGELOG-GUARD.md`（R1）、`…-GUARD-R2.md`（R2）。
> 只读纪律：除本文件与留痕 `…-GUARD-03.progress.md` 外未改仓库；实验全在 `mktemp -d`（已清理）；跑前跑后 `git status --porcelain` 一致。
> 本轮立场：**不预设前两轮正确**。R1 的 A4b「空清单」我判**当时成立**；R2 的 B-6「新 BLOCKER」我判**成立且未真闭合**（见 B-6）。

---

## 独立结论先说

**七个交给我的编号里，5 个真闭合，1 个缺陷已修但守护用例是空的（B-6），1 个仍可被一行标题绕过（B-3′）。**
**修复过程又引入 1 个新的实质缺陷（M-c：`git tag -l` 不认 root，判定随 CWD 变）**，以及 3 个新的呈现/边界缺陷。

| 编号 | 作者声称 | 我的独立裁决 | 关键实测 |
|---|---|---|---|
| B-1 一词绕过 | 机制整体移除 | ✅ **闭合** | 12 个词全部仍 FIRE；旧脚本 5/5 仍可绕（对照） |
| B-2 勘误误伤 | 移出 `勘误`/`上一版` | ✅ **闭合** | 两条纯勘误 rc=0；旧脚本同输入 rc=1（4处/2类） |
| B-3 已发布段硬阻断 | 两段分处置 1/2 | ✅ **闭合**（本仓 `v*` 前提成立） | `[0.83.4]` 痕迹 → rc=2；同内容放 `[Unreleased]` → rc=1 |
| B-3′ 未发布标题可降级 | 与 `git tag` 比对 | ❌ **未闭合** | `## [0.1.0]` / `## [0.79.5]` / 第三段 ⇒ rc=0 或 2 |
| B-4′ 注释冒充登记 | 复用 `uncovered_gate_scripts()` | ✅ **闭合** | 删锚点+加注释 ⇒ `test_bdd_23` 转红 |
| B-5 「CI 兜底」矛盾 | 统一为「不是可靠兜底」 | ✅ **闭合** | `CHANGELOG.md:42` / `scripts/README.md:73` 一致 |
| B-6 CHECK 17 指旧脚本 | 固定路径 + fail-closed | ⚠️ **缺陷已修，守护失效** | 把路径改回旧名：20 用例全绿、SG.6 绿、CI 跑旧实现 |
| B-7 段头漏空格 | `^##\s*\[` | ✅ **闭合** | `##[Unreleased]` → rc=1 |

**总判定：MISALIGNED**（B-3′ 未闭合 + B-6 守护为空 + 新引入 CWD 依赖）。
但**收敛趋势明确**：R1 的 5 个里 5 个真闭合；R2 的 4 个里 3 个真闭合。剩余问题**集中在同一处**（「已发布段」的判定依据），且都有低成本修法。

---

## A1–A8 汇总表

| # | 审查项 | 结论 | 一句话 |
|---|---|---|---|
| A1 | 文档→脚本对齐 | **MISALIGNED** | `CHANGELOG.md:53` / `check-changelog-quality.py:11` 写「v0.77.0 命中 25 处/3 类」，实测 **26/4**；`CHANGELOG.md:55` 列「自我勘误」为 6 类之一，但 `勘误` 已移出 A6（`A7` 才是 revisions） |
| A2 | 脚本→文档对齐 | **MISALIGNED** | `check-changelog-quality.py:31,32,223` 三处旧脚本名，其中 `:223` 是**判据失败时打印给用户的自证命令**（照抄即报「文件不存在」） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** | CHECK 17 的 fail-closed **本身正确**，但守护它的用例看不到调用点（B-6）⇒「CI 侧生效」这一结论无机械保障 |
| A4 | 测试覆盖 | **MISALIGNED** | 20/18 passed 属实；但 B-6 的三个变异全绿（见 §A4）、缺 2z2 行为级测试（`integration/` 0 命中）、挂载点守护可被「移进循环」绕过（M-2，两轮未修） |
| A4b | 闭合后既有测试转红 + 夹具 | **非空（2 项）** | `test_bdd_23`（已正当改写）；`test_released_section_only_warns_never_blocks` **环境敏感**（`AGATE_ROOT` 指向无 `.git` 目录即红）。夹具**无需**更新 |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** | 非 `v*` tag / 无 tag 的下游项目会被**误阻断已发布历史快照**（实测 rc=1）；`UPGRADING.md` 无本章节（RM-AG0052 惯例，发布前需补） |
| A6 | 锚点表覆盖 | **ALIGNED** | 锚点已登记（`:860-864`）、SG.6 绿、`uncovered_gate_scripts()` 判空；改名回归方向正确 |
| A7 | 设计原则一致性 | **MISALIGNED** | 违反 ADR-014（旧脚本 `agate-changelog-quality.py` 仍在 `origin/main`，词表已分叉）+ RM-AG0116（硬编码 `v*` tag 前缀 / `## [x.y.z]` 段头 / `[Unreleased]` 字面量） |
| A8 | 声称-命令绑定 | **MISALIGNED** | 「3076」「20」「18」✅；「25 处/3 类」❌（26/4）；「145 行」❌（144）；测试文件头「158/121 处」❌（两轮未修） |

---

## 逐项详情

### A1 文档→脚本对齐 — MISALIGNED

| 文档声称 | 位置 | 实测 | 判定 |
|---|---|---|---|
| v0.78.0 段 248 行、v0.77.0 段 191 行，命中 **21 / 25 处、3 类** | `check-changelog-quality.py:11`、`CHANGELOG.md:53` | 0.78.0 = **21/3** ✅；0.77.0 = **26/4** ❌ | 数字错 |
| 「第一人称、评审轮次、变异实验、`N passed`、**自我勘误**等 6 类」 | `CHANGELOG.md:55` | 6 类实为 A1/A2/A4/A5/A6/A7，**无「勘误」**（`勘误` 已按 B-2 移出 A6） | 名实不符 |
| 「最新**已发布**段」 | `check-changelog-quality.py:23-25`、`README.md:73`、`CHANGELOG.md:42` | 判据实为「首个非 Unreleased 段 **且** 版本号 ≤ 最大 tag」⇒「未打过 tag 的低版本号」被当成已发布 | **口径窄于文档** |

```bash
# 复现 26/4（文档写 25/3）
git show v0.77.0:CHANGELOG.md > /tmp/x.md
python3 - <<'PY'
import importlib.util
s=importlib.util.spec_from_file_location("m","agate/scripts/check-changelog-quality.py")
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
t=open("/tmp/x.md",encoding="utf-8").read()
for h,b,u in m.target_sections(t):
    body=m._strip_code_fences(b)
    for nm,rx in m._CATEGORIES:
        h2=[x.group(0) for x in rx.finditer(body)]
        if h2: print(nm,len(h2))
PY
# A1-first-person 5 / A4-test-counts 8 / A6-lessons 12 / A7-revisions 1  ⇒ 26 处 / 4 类
```

### A2 脚本→文档对齐 — MISALIGNED

`check-changelog-quality.py` 自身三处旧名（`43fbcf3b` 声称已修「旧脚本名残留 4 处」，实修 1 处）：

```
:31   python3 agate-changelog-quality.py [CHANGELOG.md]
:32   python3 agate-changelog-quality.py --warn-only [CHANGELOG.md]
:223  "    python3 agate/scripts/agate-changelog-quality.py CHANGELOG.md\n"   ← 用户可见
```

`:223` 是 `_GUIDANCE` 里给用户的自证命令。实测照抄：

```bash
python3 agate/scripts/agate-changelog-quality.py CHANGELOG.md
# python3: can't open file '.../agate-changelog-quality.py': [Errno 2] No such file or directory
```
⚠️ 且**当前工作区恰好把它删了（未提交的 `D`）、`origin/main` 里还有** ⇒ 用户拿到的包**可能**有这个文件（旧实现），照着跑会得到**与判据不同的结论**（旧脚本 `勘误` 判 rc=1、新脚本 rc=0）。

### A3 一致性连锁 + 反向传播 — MISALIGNED

CHECK 17 的**实现**是这轮最扎实的一处：脚本缺失 → `rep.error` fail-closed（`:1475-1483`）、`1→ERROR`/`2→WARNING` 分流（`:1495-1508`）、无词表副本（ADR-014 单源）。
问题在**验证方式**：见 B-6。

### A4 测试覆盖 — MISALIGNED

**据实先说**：`test_check_changelog_quality.py` **20 passed**、`test_release_gate.py` **18 passed**，与提交信息一致。

**我做的变异实验（全部在 clone 副本上，不碰工作区）**：

| 变异 | 目标守护用例 | 结果 | 应然 |
|---|---|---|---|
| `check-protocol-consistency.py:1473` 改回旧名 `agate-changelog-quality.py`（**即 R2 的 B-6 原样**） | `test_check17_in_consistency_points_to_existing_script` | **1 passed** | 应红 |
| 同上 + 删除旧脚本（`origin/main` 的最终形态） | 同上 | **1 passed** | 应红 |
| 只把 `:1495` 的 `1→ERROR / 2→WARNING` 分流退回 `if rc != 1: return` | `test_released_section_only_warns_never_blocks` | 1 failed ✅ | 红 |
| 删掉整条 `SCRIPT_ALIGNMENT_ANCHORS` 条目 + 加一行注释「已登记」 | `test_check17_...` / 真门禁 SG.6 | 1 passed ❌ / **1 failed** ✅ | 前者应红 |
| 把 2z2 整块移进 `for state_file in state_files:` 循环体 | `test_pre_commit_mounts_quality_check_outside_state_loop`（:128-139） | **1 passed**（且 2z2 对 hotfix 提交实测 rc=0 失效） | 应红 |

**缺的测试**：2z2 行为级测试为 **0**（`grep -rn "changelog-quality" agate/tests/integration/ | wc -l` → 0；R1 M-5 提过，三轮未补）。

### A4b 闭合后既有测试转红 + 夹具更新清单

| # | 既有用例 | 状态 | 处置 |
|---|---|---|---|
| 1 | `agate/tests/unit/test_release_gate.py::test_bdd_23_no_new_check_star_script_added`（`:352`） | **已被三提交改写**。用 `d3d16ab7^` 的原始断言打当前树：`added=['check-changelog-quality.py']` ⇒ 原断言 `assert not added` **FAIL** | 改写**正当**：BDD-23 支①原文（`agate-workspace/tasks/TAG0051-release-decoupling/P1-requirements.md:292`）确为「该脚本**须已登记**……使 SG.6 通过」。我独立核对原文成立 |
| 2 | `agate/tests/unit/test_check_changelog_quality.py::test_released_section_only_warns_never_blocks`（`:215`） | **环境敏感**：`AGATE_ROOT` 指向无 `.git` 的目录（如已装版本 `~/.agate/v0.83.4/agate`）时，`:225` 的 `git tag -l "v*"` 返回空 ⇒ `assert tags` 前置失败 ⇒ **1 failed** | 自建 `tmp_path` git 仓库并 `git tag`；或登记 `agate/tests/ENV-SENSITIVE-TESTS.md`（该清单已有先例） |
| 3 | 其余既有用例 | **无转红**。实测 44 个引用这两脚本的测试文件：**748 passed in 109s** | 无 |

**夹具更新**：**无需**。`_make_fake_protocol_tree()`（`test_check_protocol_consistency.py:80`）不含判据脚本，但所有用它跑全 CHECKS 的用例都 monkeypatch 了 `run_all_checks`，CHECK 17 的 fail-closed 不误伤（实测 49 passed）。

### A5 下游影响 + 文档传播 — MISALIGNED

三条下游事实：

1. **误阻断非 `v*` tag 项目**（RM-AG0116 同型）：

```bash
# 下游项目 tag=1.2.3（无 v 前缀），最新已发布段含「我们发现/教训/第一版」
AGATE_ROOT=<协议副本> python3 .../pre-commit-gate.py; echo rc=$?   # rc=1  ← 阻断历史快照
# 同内容、同项目，仅把 tag 改名 v1.2.3
...                                  ; echo rc=$?                   # rc=0  ← 放行
# 完全无 tag 的项目（刚接入 agate）
...                                  ; echo rc=$?                   # rc=1  ← 第一次提交即被卡
```
根因：`_released_versions()`（`check-changelog-quality.py:98-102`）硬过滤 `git tag -l "v*"`。

2. **判定随 CWD 变**（同一棵树两个答案）：

```bash
cd /tmp      && python3 .../check-protocol-consistency.py --root $T   # ❌ FAIL CHECK 17 → rc=1
cd <agateon> && python3 .../check-protocol-consistency.py --root $T   # ⚠️  WARN  CHECK 17 → 不阻断
```
根因：`subprocess.run(["git","tag","-l","v*"])` **未传 `cwd`**，取调用者 CWD 的 tag（`:98-102`）。
`docs-check.yml` 的 `docs-consistency` job **checkout 无 `fetch-tags`**（`grep -c fetch-tags` → 0），
而 `protocol-tests.yml` 的 `consistency` job 有 `fetch-tags: true` ⇒ **两个 CI 入口对同一提交结论可不同**。

3. **文档传播缺一节**：`agate/UPGRADING.md` 无本章节（`grep -n "changelog-quality" agate/UPGRADING.md` → 0）。
按发布清单第 3 步（v0.62.0 教训）本判据属「行为变更」，发布前须补「（无破坏性变更）」或行为说明。

### A6 锚点表覆盖 — ALIGNED

```bash
sed -n '860,864p' agate/scripts/check-protocol-consistency.py
#   { "desc": "CHANGELOG 条目「过程日志化」判据（RM-AG0117；阻断级，主闸 pre-commit 2z2）",
#     "script": "agate/scripts/check-changelog-quality.py",
#     "keywords": ["A2-review-rounds", "FIRE_MIN_CATEGORIES", "commit message"] }
AGATE_ROOT=<变异副本>/agate pytest agate/tests/unit/test_release_gate.py::test_bdd_23_...  # 1 failed（数据见了注释）
pytest agate/tests/unit/test_t43_check_registration_surface.py -q                          # 全绿
```
改名 `agate-*` → `check-*` + 登记锚点是**正确方向**，`test_bdd_23` 改为复用 `uncovered_gate_scripts()` 也正确。

### A7 设计原则一致性 — MISALIGNED

| 既有 ADR / RM | 判定 | 证据 |
|---|---|---|
| **ADR-014 判据单源** | ❌ 违反 | `agate/scripts/agate-changelog-quality.py` 仍在 `origin/main`（blob `e4208734`，与 `d3d16ab7` 同 blob）；两份词表**已分叉**（旧版 A6 含 `勘误`、A7 含 `上一版(?:的\|写)`、仍带 `_META_DISCUSSION`）。工作区只有未提交的 `D`（`git status --porcelain` → ` D agate/scripts/agate-changelog-quality.py`）。⇒ 谁跑 `agate-*.py` 得到与判据**相反**的结论 |
| **RM-AG0116 协议不得假设项目流程** | ❌ 违反 | 硬编码 `git tag -l "v*"`（`:99`）、`## [x.y.z]` 段头（`:155`）、`[Unreleased]` 字面量（`:138,152`）。实测试误阻断（A5 第 1 条）。协议正文无「tag 必须 `v` 前缀」的约定（`grep -rn "vN.N.0" agate/WORKFLOW.md agate/phase-cards/P8-release.md` → 0；仅 `release.yml:8` 的 `tags: ['v*']` 是 **agateon 自己的**发布触发）⇒ 这是把**本仓约定**下沉成**所有使用者的门禁** |
| ADR-003 最小约定·不绑技术栈 | ⚠️ 边缘 | 同上。CHANGELOG 段头格式属项目自由，判据只认 Keep-a-Changelog 一种写法 |
| ADR-015 只拦「会导致后续错误决策」 | ⚠️ 需人判 | 本判据拦的是**呈现类**（措辞形态），按 ADR-015 表属「非实质」。R1/R2 已论证其价值（存量 3 段人眼放行），**我不推翻该决定**，但指出张力仍在：AGENTS.md「新增判据 = 给所有使用者加成本：先答它拦下几个真缺陷」——本仓实例成立，**下游实例未举** |
| ADR-004 安全网分层 | ✅ 一致 | pre-commit 主闸 + CI 补充，且文档已如实标注「CI 不是可靠兜底」（B-5 已修，未夸大） |

### A8 声称-命令绑定 — MISALIGNED

| 声称 | 命令 | 实测 | 判定 |
|---|---|---|---|
| `test_check_changelog_quality.py` **20 passed** | `pytest agate/tests/unit/test_check_changelog_quality.py -q` | **20 passed in 0.24s** | ✅ |
| `test_release_gate.py` **18 passed** | `pytest agate/tests/unit/test_release_gate.py -q` | **18 passed in 1.67s** | ✅ |
| 全量 **3076 passed** + 2 failed | `pytest agate/tests --collect-only -q` → **3081**；3081 − 2 failed − 3 skipped = 3076 | 算术自洽；2 failed = `test_setup_agate_dir.py::test_bdd_43/45`（`shutil.which("opencode"/"codex")` 为空已核实，`:207-213` 逻辑是「非 CI 即 fail」）；3 skipped = `test_agate_image_check` ×2（Pillow 已装）+ `test_t41_platform_hygiene` ×1 | ✅ |
| 语料复验 **5/5** | 见留痕 §7 表 | 5/5 结论成立 | ✅ |
| v0.77.0 **25 处 / 3 类** | `scan()` | **26 / 4** | ❌ |
| 旧版 v0.83.4 段 **144 行** | `git show 3df9c9e8^:CHANGELOG.md` 切段 | body 143 + 标题 = **144** | ✅（但 `43fbcf3b` 提交信息仍写「145 行」❌） |
| `ruff` 全绿 | `~/.venvs/agate-dev/bin/ruff check <5 文件>` | All checks passed | ✅ |
| `consistency` 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | rc=0，440 WARNING（全冻结） | ✅ |

---

## BLOCKER / MINOR 清单（文件:行号 + 修法）

### BLOCKER

**BL-1 `agate/scripts/check-changelog-quality.py:159,162`（B-3′ 未闭合）**
`is_really_released = any(v <= rv for rv in released_versions)` 用 **≤ 最大 tag** 判「已发布」，
于是**任意小版本号**（`0.1.0`/`0.79.5`）都算历史快照；且 `:162` 的 `break` 只看首个非 Unreleased 段。
端到端实测（真 clone，88 个 v-tag）：插入一行 `## [0.1.0] - 2026-12-01` 包住过程痕迹 ⇒ **2z2 rc=0**；同一内容留 `[Unreleased]` ⇒ rc=1。
→ **修法**：`is_really_released = v in set(released_versions)`（**精确成员**，不是 ≤）；
   并把「干净已发布段 + 其后新段」一并扫（`break` 改为「收集所有非 Unreleased 段，取首个**真已发布**段 + 任何**未发布**段都按草稿计」）。
→ 补两条测试：`## [0.1.0]` 段含痕迹 ⇒ exit 1；`## [0.83.4]`（干净）+ `## [0.83.5]`（痕迹）⇒ exit 1。

**BL-2 `agate/tests/unit/test_check_changelog_quality.py:258-273`（B-6 守护为空）**
用例用 `re.findall(r'"agate/scripts/([A-Za-z0-9_.-]+\.py)"', cpc)` 找引用，而**真正的调用点**在
`check-protocol-consistency.py:1473`：`root / "agate" / "scripts" / "check-changelog-quality.py"`
（分段字符串，**不含**该字面量）⇒ 正则只能命中锚点表 `:862` 与 loc `:1481`。
实测把 `:1473` 改回旧名（= R2 的 B-6 原样）：**20 用例全绿、SG.6 绿、CHECK 17 报 ✅ PASS**，而 CI 跑的是旧词表实现。
→ **修法**：不要用正则。改为**行为断言**——`importlib` 加载模块，monkeypatch `subprocess.run` 或直接在
   `tmp_path` 建假根（有 `CHANGELOG.md` + 坏 `[Unreleased]`），断言 `check_changelog_quality()` 报 ERROR；
   再加一条「`check_changelog_quality()` 实际执行的脚本路径 `== root/agate/scripts/check-changelog-quality.py`」
   （可 `monkeypatch.setattr(mod, "subprocess", ...)` 捕获 argv，或把路径提为模块常量 `_CHANGELOG_QUALITY_SCRIPT` 后断言该常量）。
→ 顺手：把 `:1473` 的路径提为模块级常量，`rep.error` 的 loc 与真实调用共用它（消灭「两处字面量」这个错误来源本身）。

**BL-3 `agate/scripts/check-changelog-quality.py:98-102`（判定随 CWD 变 + 下游误阻断）**
`subprocess.run(["git","tag","-l","v*"], ...)` 无 `cwd` ⇒ 取**调用者 CWD** 的 tag；且硬过滤 `v*`。
实测同一棵树：`cwd=/tmp` ⇒ ❌ FAIL；`cwd=<agateon>` ⇒ ⚠️ WARN。
`docs-check.yml` 与 `protocol-tests.yml` 的 fetch-tags 不同 ⇒ 两个 CI 入口可给出不同结论。
下游项目 tag `1.2.3`（无 v 前缀）或无 tag ⇒ **误阻断已发布历史快照 rc=1**。
→ **修法**：(1) 加 `cwd=` 参数，由调用方传 `root`（`CHECK 17` 传 `root`，`2z2` 传 `repo_root`）；
   (2) tag 匹配去掉 `v*` 前缀假设：`git tag -l` 全取，再用 `re.search(r"(\d+)\.(\d+)\.(\d+)", line)` 归一
   （`:107` 已能解析无前缀，只是过滤条件砍掉了）；
   (3) 取不到任何 tag / 不是 git 仓库 ⇒ 明确 **`exit 2`（提示）而非 `exit 1`（阻断）**，并在 stderr 说明
   「无法确认发布状态，按提示处理」——否则无 tag 的下游项目升级后**第一次提交就被卡**（实测 rc=1）。

### MINOR

**M-1 `check-changelog-quality.py:11` + `CHANGELOG.md:53`** — v0.77.0「25 处/3 类」实测 **26/4**。→ 改成 26/4（附命令见 A1）。
**M-2 `test_check_changelog_quality.py:128-139`** — 挂载点守护用 `mount > loop` 行号判据。实测把 2z2 整块移进循环体：**仍 PASS**，而 2z2 对 hotfix 提交实测失效（rc=0）。→ 改断言两者缩进相等（`len(ln)-len(ln.lstrip())`）**且**补一条行为测试（无 `.state.yaml` + 暂存坏 CHANGELOG ⇒ gate rc≠0）。
**M-3 `check-changelog-quality.py:48-51`** — A2 字符类缺「两/多」：`两轮评审`、`多轮评审` 实测 0 命中（`二轮评审` 命中）。→ `[两二三四五六七八九十\d]+` 且考虑 `多|数|若干`。
**M-4 `check-changelog-quality.py:44-46`** — A1 只认「我们**发现**」：`我们认为`/`我们判断`/`我们原先`/`我们漏了` 实测全 0。→ `我(?:们)?(?:发现|认为|判断|原先|漏|错|写|以为)`。
**M-5 缺 2z2 行为级测试** — `grep -rn "changelog-quality" agate/tests/integration/ | wc -l` → **0**（R1 提过，三轮未补）。→ 补「只暂存坏 CHANGELOG、无 `.state.yaml` ⇒ `pre-commit-gate.py` rc≠0」，以及「暂存坏件 + 工作区改好（不 add）⇒ 仍 rc≠0」。
**M-6 `check-changelog-quality.py:31,32,223`** — 旧脚本名 3 处（`:223` 是用户可见的自证命令）。→ 改名；并加一条 `assert "agate-changelog-quality" not in Path(script).read_text()` 防第四次。
**M-7 `check-protocol-consistency.py:1463-1465`** — 注释仍写「判据脚本命名为 `agate-*.py` 而非 `check-*.py`」，与现状（已改名回 `check-*`）**直接矛盾**。→ 删掉该段（或改成「已按 README 登记面命名为 `check-*.py`」）。
**M-8 `check-protocol-consistency.py:96-110` 附近的 `break`**（2z2，`pre-commit-gate.py:1217-1218,1234`）— 暂存多个 `*CHANGELOG.md` 时**只查第一个**：实测 `0docs/CHANGELOG.md`（干净）+ `CHANGELOG.md`（坏）⇒ **rc=0 放行**。`_git_show` 返回 `None` 也 `break`。→ 改 `continue`，或只认仓库根的 `CHANGELOG.md`（`_rel == "CHANGELOG.md"`）。按 AGENTS.md 三问①（本仓只有根 CHANGELOG，属构造性输入）我记 MINOR。
**M-9 `agate/UPGRADING.md`** — 无本章节（`grep -n "changelog-quality"` → 0）。发布前按清单第 3 步补。
**M-10 `test_check_changelog_quality.py:6`** — 「158 处 / 121 处」不可复现（R1 M-1、R2 M-1，三轮未修）。→ 改 21/26。
**M-11 `agate/scripts/agate-changelog-quality.py`（旧实现）仍在 `origin/main`** — ADR-014 单源被破坏。→ 提交删除（当前只有未提交的 `D`，未进任何提交）。**这条已随 PR #485 合入 main**，修它需要新 PR。

---

## 你点名的 6 个问题 — 逐条回答

### 1. 前两轮 BLOCKER 是否真闭合

见上表：**B-1/B-2/B-3/B-4′/B-5/B-7 真闭合（6 个）；B-3′ 未闭合；B-6 缺陷已修但守护为空。**
我不认同作者在 `edb63b58` 里「B-6 已修 + 补两条测试」的**有效性**：那两条测试（`:258`/`:276`）分别验证
「字面量存在」与「脚本缺失报错」，**没有一条**验证「`check_changelog_quality()` 实际调用的是哪个文件」——
而这正是 B-6 的缺陷本体。

### 2. B-6 实测：把 CHECK 17 指向不存在的文件，是 ERROR 还是静默跳过？

**ERROR，fail-closed 生效**（`check-protocol-consistency.py:1475-1483`）：

```
❌ FAIL  CHECK 17 CHANGELOG 条目非「过程日志」（RM-AG0117）
  ❌ 判据脚本不存在（协议包不完整或版本过旧）：agate/scripts/check-changelog-quality.py
rc=1
```
这一半是对的。**但**：如果把路径改成一个**存在但错误**的文件（旧脚本仍在树里，正是 `origin/main` 的现状），
就变成 **✅ PASS**（跑了旧词表），而此时 20 条用例 + SG.6 + consistency **全绿**。⇒ 静默跑错比静默跳过更危险。

### 3. B-3′ 端到端：未发布 `## [99.99.99]` vs 真已发布 `0.83.4`

| 构造 | 判据 rc | 2z2 rc | 说明 |
|---|---|---|---|
| `## [99.99.99]`（> 最大 tag） | 1 | 1 | ✅ 阻断（作者修法有效） |
| `## [0.83.5]`（> 最大 tag） | 1 | — | ✅ |
| `## [0.83.4]`（真已发布） | 2 | 0 | ✅ 放行（应然） |
| **`## [0.1.0]` / `## [0.79.5]`（≤ 最大 tag，从未打过）** | **2** | **0** | ❌ **一行标题即绕过** |
| 干净 `[0.83.4]` 后再加 `## [0.83.5]` 段放痕迹 | **0** | — | ❌ 第三段完全不被扫 |

⇒ **作者只堵住了「版本号更大」这一种，用更小的版本号仍然绕过**。`v <= rv` 是错的判据，应为**集合成员**。

### 4. B-4′ 实测：移出锚点表 + 注释里写脚本名，`test_bdd_23` 会红吗？

**会红**（这次是真红，不是假绿）：

```bash
# 变异副本：整条锚点条目删除 + 在 GATE_SCRIPT_EXEMPT 前插一行注释写脚本名
python3 -c "...uncovered_gate_scripts(root)"   # ['agate/scripts/check-changelog-quality.py']
AGATE_ROOT=<变异>/agate pytest agate/tests/unit/test_release_gate.py::test_bdd_23_no_new_check_star_script_added
# 1 failed ✅
```
`importlib` 复用 `uncovered_gate_scripts()` 的做法正确，与 DEBT0046 的修法同型。

### 5. 会不会误伤我（真实变更说明模拟）

**会。** 六条真实体例里六条过（E1–E6 全 rc=0），但下面四条**日常写法**被误拦：

| 输入 | 结果 |
|---|---|
| 两条修复各写「**我们发现** X，已修」+ 一条「**教训**：改键要连测试看」 | **rc=1**（3 处 / 2 类） |
| 单条安全修复：「**我们发现** `--root` 未 realpath；**第一版**实现用字符串比较；**我们**又**发现** `check-gate.py` 同类」 | **rc=1**（3 处 / 2 类） |
| 两条「**我们发现**…」+ 结尾「全量回归 **3076 passed**」 | **rc=1**（3 处 / 2 类） |
| 「**我们发现**…」+「**教训**：」+「**二轮评审**确认覆盖完整」 | **rc=1**（3 处 / 3 类） |

根因：`A1-first-person` 把裸 `我们发现`（**在讲修了什么**，是 CHANGELOG 正当主语）与
`我原先/我第一版/我判断错了`（**自我检讨**）放在同一类、同等计数。
**我的判断：这是 BLOCKER 级误伤**（不是 MINOR）——它拦的是「主语用第一人称的正常条目」，
而作者自己的正例（`CHANGELOG.md:22-27` 的 v0.83.4 节选）恰好**没有**第一人称，所以测试没暴露。
→ 修法：A1 只保留**自我检讨**句式（`我(们)?(?:原先|本来|一开始|第一版|错|漏|判断错)`），
去掉裸 `我们发现`/`我认为`/`我判断`；或把它们降级到 `_HINT_ONLY`（只提示不计数）。
检出能力不受影响：真过程日志几乎必带「第一版/原先/漏了/错了」（留痕 §7 的 3 段语料实测 A7 均命中）。

### 6. A7 设计原则一致性 — 是否违反 `agate/adr.md` 既有 ADR

**违反两条：ADR-014（判据单源）与 RM-AG0116（协议不得假设项目分支/流程）；一条边缘（ADR-003）。**

- **ADR-014**：旧脚本 `agate-changelog-quality.py` 仍在 `origin/main`（blob `e4208734`），与新脚本词表**已分叉**。
  「判据单源」不仅要求 `check-consistency` 不复制词表（这点做到了），也要求**不存在第二份实现**。
- **RM-AG0116**：`git tag -l "v*"` / `## [x.y.z]` / `[Unreleased]` 三个硬编码把**本仓约定**变成**所有人的门禁**。
  该条 roadmap 的原则原话是「协议不得假设项目策略……有的项目允许直接 commit/push 到 main」，
  同一逻辑适用于「有的项目 tag 不带 v / 用 CalVer / 不用 Keep-a-Changelog 段头」。实测已造成误阻断。
  → 不但要修 `v*`，还应给「无法确认发布状态」定义**提示而非阻断**的出口（BL-3）。
- **ADR-003**（最小约定·不绑技术栈）：CHANGELOG 段头格式属项目自由，判据只认一种写法。

---

## 闭环

| 结论 | 主 Agent 动作 |
|---|---|
| **MISALIGNED**，不可按当前状态收尾 | 修 BL-1 / BL-2 / BL-3 再复审（三者都是**局部改动**，不推翻设计） |
| 设计取向仍成立 | 「阻断级 / 不用行数 / A3 只提示 / 扫描面收窄」四条我**再次实测验证成立**，不动 |
| **必须同批处理** | BL-1 + BL-3 改同一函数（`_released_versions` / `target_sections`）；BL-2 改测试，建议同时把路径提为模块常量 |
| **可延后** | M-1…M-11（呈现类，按 AGENTS.md「评审轮次从紧」不单独开轮，随上述修一并做） |
| **发布前** | M-9 补 `UPGRADING.md` 章节；M-11 删除旧脚本（已在 main，需新 PR） |

**收敛判断**：与前两轮相比，缺陷密度显著下降（R1: 5 BLOCKER → R2: 1 新 + 1 未闭合 → R3: 2 未闭合 + 1 新）。
剩余三条 BLOCKER **全部落在同一处语义**（「什么算已发布」+「怎么验证判据真在跑」），
修法都是一两行 + 两三条测试。**再一轮应可闭合**。
