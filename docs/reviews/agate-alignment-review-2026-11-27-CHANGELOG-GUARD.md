---
review_date: 2026-11-27
reviewer: protocol-alignment-review
change_summary: 新增 CHANGELOG 条目「过程日志化」阻断级判据（agate-changelog-quality.py + pre-commit 2z2 + CHECK 17）
files_changed:
  - CHANGELOG.md
  - agate/scripts/README.md
  - agate/scripts/agate-changelog-quality.py
  - agate/scripts/check-protocol-consistency.py
  - agate/scripts/pre-commit-gate.py
  - agate/tests/unit/test_check_changelog_quality.py
  - docs/reviews/changelog-guard-placement-review-2026-11-27.md
baseline_commit: d3d16ab7
---

# 协议-脚本对齐审查 — CHANGELOG 质量判据（RM-AG0117）

> 评审基线：`d3d16ab7`（作者在评审过程中提交；此前暂存态快照 `481f6145`/`4b9d5433` 的结论保留在留痕文件里）。
> 只读纪律：除本文件与留痕文件外未修改仓库；所有实验在 `mktemp -d`（`/tmp/agate-guard-review.*`、`/tmp/sim2.*`、`/tmp/rename.*` 等）进行，跑前跑后 `git status` 一致。
> **重要背景（影响结论）**：评审期间作者连续两次改稿并提交 —— 我上一轮实测到的「暂存坏件 + 工作区改好即可放行」漏口，作者已在 `d3d16ab7` 修掉（改用 `git show :<path>` 判暂存区 blob）。本报告的结论针对 `d3d16ab7`；对先前版本的结论作为演进记录保留在留痕文件。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（空清单，实测） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | **MISALIGNED** |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW** |
| A8 | 声称-命令绑定 | **MISALIGNED** |

**总判定：MISALIGNED**。三处 BLOCKER 都不是「措辞」问题——分别是**判据可被一行注释整行豁免**（B-1）、**合法条目被硬阻断**（B-2）、**存量（已发布历史快照）会造成硬阻断**（B-3）。其中 B-3 直接推翻了脚本自述的「对存量仓库零影响」，而 B-1 是判据自身机制被自己的注释绕过，属「机制声称 ≠ 机制实现」。

设计取向先说清楚（避免被读成"要求放宽"）：**阻断级、不用行数、A3 只提示不计数、扫描面收到 Unreleased + 最新已发布段 —— 这四条我都实测验证过是对的，不动它们。** 下面所有 BLOCKER 都是在**不动这四个决定**的前提下可修的。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**文档声明**（`CHANGELOG.md:52-53`）：
> 命中「过程痕迹」（第一人称、评审轮次、变异实验、`N passed`、自我勘误等 6 类）**≥3 处且 ≥2 类**即判失败

**脚本实现**（`agate/scripts/agate-changelog-quality.py:42-75`）：6 类 + `FIRE_MIN_TOTAL=3` / `FIRE_MIN_CATEGORIES=2`。

**结论：数值阈值 ALIGNED，类别语义 MISALIGNED。** 三处实测不符：

1. **A2「评审轮次」的数字量词只覆盖一半中文写法。** 正则 `:[48-51]` 的字符类是 `[一二三四五六七八九十\d]`，**不含「两」**。实测：
   ```
   "二轮评审"   → ['二轮评审']   ✅
   "两轮评审"   → []             ❌（"两轮" 是中文更高频写法）
   "两轮独立评审" → []           ❌
   "多轮评审"/"数轮评审"/"若干轮" → []  ❌
   ```
   文档说「评审轮次」会被抓，但「两轮独立评审」这种最自然的写法抓不到。

2. **A1「第一人称」只覆盖「我们」的一个动词。** 实测 `我们发现` → 1，而 `我们认为 / 我们判断 / 我们原先 / 我们漏了 / 我们错 / 我们写` **全部 0**（正则只有 `我们发现` 这一条含「我们」）。这不是"故意收窄"——注释 `:43` 自称「作者在讲自己的动作/判断」，实现只认一个动词。

3. **A4 精确性良好（此项无误）**：`修复导致 3 个测试 failed 的缺陷` → 0、`实测 35 个用例转红` → 0（裸「转红」已按设计排除），`用例数` → 1。**A4 不误伤「3 个测试 failed」这类正当描述，这个问题不用担心。**

**差异**：文档列的类别语义 > 脚本实际覆盖面。
**建议**：A2 字符类补 `两`，并考虑 `多|数|若干`；A1 把 `我发现` 抽象为 `我(?:们)?(?:发现|认为|判断|原先|漏|错|写|以为)`。

---

### A2: 脚本→文档对齐 — MISALIGNED

**BLOCKER B-1：`_META_DISCUSSION` 的注释与实现不符，坏条目单加一个词即可整行豁免。**

**脚本注释**（`agate-changelog-quality.py:119-121`）：
> 「在讨论判据本身」的行——**比单纯命中某个词严得多**，防「加个词就整行豁免」。
> 必须**同时**满足「提到判据/词表」**且**「是元讨论的句式」，而非「出现某词」。

**实现**（`:121-123`）：
```python
_META_DISCUSSION = re.compile(
    r"(本判据|该判据|判据本体|判据规则|词表|阈值|扫描面|自检|误伤|过程痕迹等|等\s*\d+\s*类)"
)
```
**这是一个纯 alternation —— 任一词单独出现即整行剥离（`:141`）。** 实测（坏条目 `- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训`，基线 total=5）：

| 尾加 | 行被剥 | total |
|---|---|---|
| （判据） | False | **5** ✅（已被 `test_meta_keyword_cannot_be_used_to_bypass` 锁住） |
| （本判据）/（该判据）/（判据本体）/（判据规则） | True | **0** ❌ |
| （词表）/（阈值）/（扫描面） | True | **0** ❌ |
| （自检）/（误伤）/（过程痕迹等） | True | **0** ❌ |

**11 个词里 10 个仍能一行绕过，只有「判据」这一个被修好了** —— 而新增的那条守护测试（`test_check_changelog_quality.py:169-186`）只测了「（判据）」一个词，所以它绿着，却**宣称**锁定了"不能被一行注释绕过"。

**这不只是理论口子，是现实误判**：`阈值 / 扫描面 / 自检 / 误伤` 都是普通技术词，正常条目里会出现：
```
- 本版把重试阈值从 3 调到 5；第一版设成 10，三轮评审后改回。   → total=0（该拦，放行了）
- 本版把重试上限从 3 调到 5；第一版设成 10，三轮评审后改回。   → total=1（对照）
- 修掉 ABS_PATH_RE 误伤 /或；第一版以为是正则笔误，二轮评审才定位。 → total=0（该拦，放行了）
```
**判据自己那条 `[Unreleased]` 条目正是靠这个口子才通过的**（`CHANGELOG.md:52` 含「6 类」、`:51` 含「本判据」，两行被整行剥离；不剥离则 total=2 / 2 类 — 尚未 FIRE，但已在阈值边缘）。

**建议（保持从严、不用放宽词表）**：
- 改成真·双条件，例如「同时出现『判据/词表』**且**出现『扫描/检查/命中/阈值』」的**同一行 within-N-chars** 判定；或
- 更稳的做法：**放弃行级豁免，改为只在「被完整围栏代码块包裹」时豁免**，元讨论靠作者自己写进代码块或 `> ` 引用块（把「怎么豁免」变成一个显式、可审的动作，而不是靠分词猜测）。
- 无论选哪条，**守护测试必须参数化覆盖 `_META_DISCUSSION` 里的每一个词**（现在漏了 10 个）。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（已知衍生改动）**：

| 应被影响 | 实际 | 判定 |
|---|---|---|
| `agate/scripts/README.md` 索引行 | 已加（`:73`） | ✅ |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | **未加 2z2 行** | ❌ |
| `agate/UPGRADING.md` §3 | 无（属发布时补，可接受） | 观察 |
| `CHANGELOG.md` 顶部规范 | 已加 | ✅ |

**WORKFLOW.md 是硬伤**：`agate/WORKFLOW.md:347` 明文自称
> 「**本表是「pre-commit 检查集」的唯一事实源**——其它文档只指针引用、不复制清单。」

而该表（`:350-366`）有 `2z`、`2y`，**没有 `2z2`**。本次新增的是一道**阻断 commit 的仓库级检查**（对所有 agate 用户生效），却缺席唯一事实源。这是 A2/A3a 两向都成立的漏传播（`grep -n "2z2" agate/*.md` → 仅命中 `agate/scripts/README.md`，那是索引表不是检查清单）。

**A3b（反向传播——应被影响而未列在 diff 里）**：
- **`agate/scripts/README.md:73` 与 `CHANGELOG.md:54-56` 对同一事实给出相反结论**：README 写「CI 由 **CHECK 17 兜底**（覆盖 `--no-verify`）」，而 CHANGELOG/`check-protocol-consistency.py:1452-1455` 已经改成「**不是**可靠兜底……红了不阻止合并」。README 是 `agate/` 内活文档（freshness-guide §3 明列），留着「兜底」这一说法就是同一批改动内自相矛盾。
- **`SELF-GATE.md` 触发面**：本次改动碰 `agate/scripts/*.py`，属 self-gate 触发面 —— 提交信息带了 `self-gate-review:`（已核，`git log -1 --format=%B d3d16ab7 | grep -c self-gate-review` = 1）✅。

---

### A4: 测试覆盖 — MISALIGNED

**实跑输出**（本机，非全量，按纪律单跑目标文件）：
```
agate/tests/unit/test_check_changelog_quality.py ................. 13 passed in 0.10s
agate/tests/integration/test_pre_commit_hook.py + 上者 ....... 82 passed in 51.69s
test_doc_sweep + test_check_protocol_consistency + test_t43 +
test_release_gate + test_protocol_alignment_review +
test_tag0050_fitness ....................................... 97 passed in 1.82s
ruff check（4 文件）....................................... All checks passed
check-platform-assumptions.py ............................. rc=0
count-tests.sh ........................................... 3061 → 3074（+13，与新增用例数一致，无漂移断言）
```

**问题 1（BLOCKER 级，与 B-1 同一处）：守护测试只覆盖了 1/11 个绕过词。**
`test_meta_keyword_cannot_be_used_to_bypass`（`:169`）的 docstring 自称：
> 「在坏条目里加「（判据）」二字，不得让该行豁免……本条锁定该收紧不被回退。」
实测「（词表）/（阈值）/（扫描面）/（自检）/（误伤）/（本判据）」全部仍能从 5 归零，而测试全绿。**测试锁的是一个不存在的性质。**

**问题 2：挂载点守护测试没有断言缩进，改一行就能"假绿"。**
`test_pre_commit_mounts_quality_check_outside_state_loop`（`:128-139`）的判据是 `mount > loop`（行号先后）。实测变异：把 2z2 整块**移进循环体**（缩进 8）后，行号仍 `768 > 767` ⇒ **断言依旧 PASS**。它守护的正是注释 `:1203` 自称"本仓已记过一次放错位置的事故"的那个缺陷，却守不住。建议断言 `2z2` 行的缩进等于 `for state_file` 行的缩进（`len(line) - len(line.lstrip())`），而不是行号先后。

**问题 3：2z2 无行为级测试。** 现有 `test_pre_commit_hook.py` 里两处 CHANGELOG 用例（`:818`、`:841`）测的是 **2m（`check-changelog.py` 的 task_id 存在性）**，不是 2z2。`grep -n "changelog-quality\|CHANGELOG-QUALITY" agate/tests/integration/test_pre_commit_hook.py` → 0 命中。即：**「hotfix 无 `.state.yaml` 时 2z2 真的阻断」这一条主战场结论，没有任何 pytest 守护**（我用手工 mktemp 仓库验证了它成立，见实测记录 E1；但没测试守着它）。审查角色建议至少补一条：只暂存坏 `CHANGELOG.md`（无 `.state.yaml`）→ `run_cli(pre-commit-gate.sh)` 非 0。

**问题 4：B-3 那条行为（已发布段会阻断）没有测试，而它和文档自述相反。** 见 A5。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED（空清单，已实测）

**经实测无既有用例转红。** 依据：
- `test_release_gate.py::test_bdd_23_no_new_check_star_script_added` —— **绿**。原因实测：脚本名是 `agate-*.py`，不匹配 `check-*.py` glob。我把脚本**复制**一份改名 `check-changelog-quality.py` 到 `git archive HEAD` 的副本里复跑：
  ```
  CHECK 9 → WARN，含「gate 脚本 agate/scripts/check-changelog-quality.py 既未纳入 CHECK 9 锚点表…」
  pytest test_protocol_alignment_review.py → 1 failed（test_sg_6_check9_anchor_table_covers_all_gate_scripts）
  ```
  ⇒ 若沿用 `check-` 前缀，SG.6 **会红**、CHECK9-coverage **会告警**。作者的改名确实"规避"了这两道门禁。
- `test_t43_check_registration_surface.py` 12 passed、`test_doc_sweep.py` 绿、`test_check_protocol_consistency.py` 绿。
- `count-tests.sh` 3061 → 3074（+13 = 新文件 13 个用例），且该脚本是下界语义（≥749），未转红。
- 无夹具需要更新：无既有夹具写「过程痕迹」式 CHANGELOG（`grep` 全 `agate/tests/` 仅新文件命中）。

**但"转红清单为空"这个结果本身需要单独裁决** —— 见 A6：**它是靠改名绕开了本该触发的登记面**。

---

### A5: 下游影响 + 文档传播 — MISALIGNED

**BLOCKER B-3：扫描面含「最新已发布段」，与「已发布条目是历史快照、保留不动」直接冲突；对存量用户仓库不是零影响，是硬阻断。**

**脚本自述**（`agate-changelog-quality.py:23-25`）：
> 扫描面 = `[Unreleased]` + **最新一个已发布段**：存量历史条目不动
> （`docs/guides/doc-freshness-guide.md` §3 已把「CHANGELOG 已发布版本的条目」定为历史快照、保留不动）⇒ **对存量仓库零影响**，无需豁免清单。

**这两句自相矛盾**：既把「最新已发布段」纳入扫描面，就等于**要求作者修改一项被 §3 定义为「改反而失真」的历史快照**才能提交。

**实测（`/tmp/sim2*` 复制真实 `agate/scripts` 的临时 git 仓库，用户仓库视角）**：
```
CHANGELOG.md:
## [Unreleased]
- 修复导出超时（升级须知：默认超时 30s，可用 --timeout 覆盖）。   ← 本身完全干净

## [1.2.0] - 2026-11-01
- 第一版判断错了（独立评审两轮推翻），变异实验转红，31 passed，教训：以后先写回归。

→ pre-commit rc = 1（硬阻断）
→ 只把 [1.2.0] 段改写成「- 修复导出超时竞态。」（= 改历史快照）后 rc = 0
```
⇒ **任何存量 agate 用户，只要其「最新已发布段」恰好是过程日志写法（本仓 v0.78.0/v0.77.0 就是），升级后下一次动 `CHANGELOG.md` 就会被卡住，且唯一出路是改写已发布历史。**

同时该判定**与 `2m` 的语义冲突**：`pre-commit-gate.py:1086-1090` 的 `check-changelog.py` 对缺 task_id **只 WARNING 不阻断**；而新判据在**同一次提交**上会硬阻断同一个文件。同一文件上"存在性"是软的、"文风"是硬的 —— 需要显式确认这个倒挂是有意的。

**建议**（不动「含最新已发布段」这个决定）：把已发布段降级为 `exit 2`（提示不阻断），或给「已发布段」单独一个 `--released-warn-only`；只让 `[Unreleased]` 具备阻断力。这样既保住"发布前把最新一条拦住"，又不逼迫任何人改历史快照。

**BLOCKER B-2：合法条目被硬阻断（误伤面实测）**

脚本与 CHANGELOG 都只论证了「单类反复不判」，但**没说清两类正当写法的叠加也会 FIRE**。实测三次端到端（真跑 `pre-commit-gate.py`）：

```
情形①（2 条纯文档勘误，零过程叙述）
- 勘误：上一版的迁移命令写错了（`setup` 应为 `init`），已更正。
- 勘误：上一版的示例代码漏了 `await`，已补齐。
→ total=4 cats=2 → rc=1 阻断（A6 勘误×2 + A7「上一版的」×2）

情形②（读者真正需要的信息）
- 勘误：上一版的迁移命令写错了，已更正。
- 勘误：上一版的示例代码漏了 await。
- 教训：v1.2 缓存无上限导致 OOM，本版加 512MB 上限。
→ total=5 cats=2 → rc=1 阻断

情形③（同一行内）
- **勘误**：上一版写错了；我们发现并已修正。
→ total=3 cats=3 → rc=1 阻断
```
这三段**全部是在告诉读者「上版文档错了 / 本版加了上限」**，正是 `CHANGELOG.md` 顶部新规范自己列的「该写在这里」那一栏。判断：**A6「教训/勘误」与 A7「上一版(的|写)」两类词过宽** —— 它们在技术文档里是**合法动词**，不是过程痕迹。过程痕迹的特征是「**我**做了什么」，而「勘误：上版写错了」的主语是**文档/规格**。

**建议**：A6 收窄到 `教训(?!落地)|事后复盘|复犯`，A7 收窄到 `第一版(?:判断|实现)(?:错|是错)`（去掉 `上一版的`、`上一版写`、`原先写`——这三者都是正当的"修了上版的错"表述），或把 A6+A7 **合并计为一类**（二者语义同源：都在讲"修订"，各自单类已被阈值豁免，合并后就不会两类叠加触发）。

**BLOCKER B-1 的下游版本**：`agate/scripts/README.md:73` 与 CHANGELOG 结论相反（见 A3）。

**A5 补充（成立的部分）**：
- `pre-commit-gate.py:1192-1207` 的注释把「CI 兜底不成立」写得比 CHANGELOG 还清楚，属正确传播 ✅。
- 只在暂存了 `CHANGELOG.md` 时跑 —— 实测 `T4`（完全不暂存）rc=0，**无日常增量** ✅（成本顾虑成立：实测 pre-commit 全程 0.07 s）。
- 破坏性影响对**新项目**为零：不适用（无 CHANGELOG）→ rc=0 ✅。

---

### A6: 锚点表覆盖 — MISALIGNED

**BLOCKER B-4：`agate-*.py` 改名规避了本该触发的登记面；且锚点表本来就接受 `agate-*.py`，"规避"缺乏必要理由。**

`check-protocol-consistency.py:1457-1459` 的注释自陈规避意图：
> ⚠️ 判据脚本命名为 `agate-*.py` 而非 `check-*.py`：后者会触发 SG.6 / CHECK9-coverage 两处登记面（`test_release_gate.py::test_bdd_23_no_new_check_star_script_added` 硬守护），而本判据是「工具/观测定性」类，用 agate- 前缀是既有约定。

**两点核实：**

1. **这道判据确实是"判据"不是"观测"**。它 exit 1 **阻断 commit**，是 `pre-commit-gate.py` 里**唯一**一个承载阻断判定的 `agate-*.py`（`grep -o '_run_script_rc("[a-z0-9-]*\.py"'` 的 14 个里，13 个是 `check-*`）。「工具/观测定性」的自我归类与本脚本行为不符。

2. **`agate-*.py` 完全可以进锚点表** —— 表里已有两个：`agate/scripts/agate-mark.py`、`agate/scripts/agate-state-yaml-check.py`（`check-protocol-consistency.py:648-701`）。所以「用 agate- 前缀所以不用登记」不成立；正确表述是「`uncovered_gate_scripts()` 只 glob `check-*.py`，故 `agate-*.py` 天然不在门禁覆盖面内」——那是**门禁的已知盲区**（`agate/scripts/README.md:12-15` 已如实记载），不是一个可以主动用来"避免触发"的通道。

**核实是否为"真规避"**：把脚本改名 `check-changelog-quality.py` 复跑 ⇒ CHECK9-coverage WARN + SG.6 red（见 A4b 实测）。**所以这个改名确实让一个本该变红的门禁保持绿灯。**

**判定：这是规避了本该触发的登记面，不是正当规避。** 但它**不需要改名回退**——应在 `SCRIPT_ALIGNMENT_ANCHORS` 补一条锚点（关键词实测存在：`过程痕迹`/`FIRE_MIN_TOTAL`/`_CATEGORIES`/`scan` 均在脚本内），让「判据单源」这件事被 CHECK 9 正向守护。这样既不触发 BDD-23（文件名仍是 `agate-*`），又补上了登记面。

---

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

逐条对照 `agate/adr.md`：

| ADR | 关系 | 判断 |
|---|---|---|
| **ADR-014 判据单一权威源** | 判据本体单源（脚本），CHECK 17 只调用不复制词表 | ✅ ALIGNED（实测 `check-protocol-consistency.py` 内无任何词表副本） |
| **ADR-015 实质/非实质——门禁只用于「会导致后续错误决策」的错误** | 「CHANGELOG 写成过程日志」是否属"会导致后续错误决策"？用户明确要求（"记了不看等于不记"），且给出了本仓 6 次复犯的实证 | ⚠️ **需人工裁决**：这条 ADR 的原文倾向"不要为非实质面增设规则"。作者用"用户明确要求 + 6 次复犯"来回应，我认为理由成立（用户意图不属可质疑范畴），但**新增的是对所有 agate 用户仓库生效的阻断门禁**，其成本面（B-2/B-3 已证有真误伤）超出本仓范围 —— 这一点 ADR-015 与「新增判据 = 给所有使用者加成本」（`AGENTS.md`）都要求更严的误伤论证，而现在只论证了"单类不判"。 |
| **ADR-005 改动性质决定流程** | 脚本行为 + 契约变化 | ✅ ALIGNED |
| `AGENTS.md`「新增判据 = 给所有使用者加成本：先答『它会拦下几个**真**缺陷（举实例）』」 | 已答：7 个真实提交回放，5 个 FIRE（我独立复算：`c8acd5ff` 8/3 T、`70f051ba` 3/3 T、`60ff46fd` 5/3 T、`9f9c12f4` 4/4 T、`8690c9d2` 1/1 F、`38616417` 0/0 F、`3df9c9e8` 0/0 F —— 与报告一致） | ✅ 实例成立 |

**为什么是 NEEDS_HUMAN_REVIEW 而不是 MISALIGNED**：ADR-015 是指导性的（角色文件原则 3：“设计原则是指导性的，不是可机器判定的硬规则，不存在 MISALIGNED”）。需人工确认的是：**接受"对所有 agate 用户仓库阻断"这一成本，还是先把 A5 的误伤/存量两处收窄再阻断。**

---

### A8: 声称-命令绑定 — MISALIGNED

逐条 `声称 → 命令 → 结论`（全部本机实跑）：

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | v0.78.0 段 **248 行**（CHANGELOG:51 等） | `python3 -c "…按 '^## \[' 切段计数…"` | ✅ 复核通过 = 248 |
| 2 | v0.77.0 段 **191 行** | 同上 | ✅ = 191 |
| 3 | v0.81.0 段 **240 行**、过程痕迹 **0** | `import agate-changelog-quality; scan(段)` | ✅ 240 行 / total=0（反例成立，**这是本次设计最扎实的一处论证**） |
| 4 | 按本判据分别命中 **21 / 25 处、3 类** | 同上 | ✅ 21/3 类、25/3 类 |
| 5 | 0.83.4 重写前 **145 行**、FIRE | `git show 3df9c9e8^:CHANGELOG.md` + `scan` | ✅ 实测 **144 行**（报告称 145，差 1：含/不含标题行的口径差），total=16 cats=5 FIRE=True |
| 6 | 「**158 处 / 121 处**」（`agate/tests/unit/test_check_changelog_quality.py:6`） | 试了 5 套词表定义 + 逐词子集枚举（27 词，2..8 元组合穷举） | ❌ **无法复现，且无法给出产出命令**。最接近的组合也只有 86/123。**注意：CHANGELOG.md、脚本 docstring、pre-commit 注释里的 158/121 已被作者改成 21/25（可复核）——只剩测试文件注释这一处残留。** |
| 7 | 报告「6 条正则扫整个 CHANGELOG **5.00 ms**」 | `timeit` ×50 | ❌ 复核不出：6 条正则扫全文 **18.5 ms**（中位）；`scan()`（只扫两段）**1.46 ms**；CLI 全程 **20.1 ms**。5.00 ms 与任一口径都不符（同量级，非阻断，但按 A8 规则应改成可复现的数字或删除） |
| 8 | 报告「`CHANGELOG.md` 185 633 bytes / 2944 行」 | `git show 3df9c9e8:CHANGELOG.md` | ✅ 精确对上（chars=185633, lines=2944；bytes=308485 —— 报告写 "bytes" 实为 chars，但数字可复现） |
| 9 | 报告「**211** 个改过 CHANGELOG 的提交，**25** 纯 docs，**186** mixed」 | 按 `protocol-tests.yml` 的 NON_DOCS 正则逐提交判定 | ✅ 211 / 25 / 186 全部精确复现 |
| 10 | 报告「`check-changelog.py` **0.033 s**」 | `subprocess` 计时 | ✅ 0.034 s |
| 11 | 报告「consistency **1.94 / 1.98 s**」 | `/usr/bin/time` ×3 | ✅ 1.93 / 1.94 / 1.98 s |
| 12 | 报告「E-2：只暂存 CHANGELOG.md 时 gate rc=0、零输出」 | 同构造复跑 | ✅ rc=0（**但那是修复前**；`d3d16ab7` 后同一场景 rc=1 —— 该实验结论已被本次改动推翻，报告未更新，属历史快照可接受） |
| 13 | 「7 个真实提交 5 拦 2 放」 | 逐提交取 `+` 行后 `scan` | ✅ 与报告完全一致 |
| 14 | pre-commit 2z2 是否在循环外 | 缩进/行号 + 运行时实验 | ✅ 在循环外（行号 1192 > 767，缩进同为 4）；**运行时也证明有效**（E1 rc=1） |

**结论**：数字类声称绝大多数可复核（#1-5、#8-11、#13-14），两处不可复核（#6 残留、#7 计时口径）。**#6 必须处理**——按 A8「无法给出命令的声称应删除」，`test_check_changelog_quality.py:6` 的「158 处 / 121 处」应改成 `248 行命中 21 处 / 191 行命中 25 处`（与 CHANGELOG 及脚本 docstring 已用的口径统一）。

---

## 你点名的 8 个问题 — 逐条回答

**1. 判据有效性**（实测，基线 d3d16ab7）
| 样本 | 行数 | total / 类 | 期望 | 实际 |
|---|---|---|---|---|
| v0.78.0 | 248 | 21 / 3 | FIRE | ✅ FIRE |
| v0.77.0 | 191 | 25 / 3 | FIRE | ✅ FIRE |
| 我那版 v0.83.4（`3df9c9e8^`） | 144 | 16 / 5 | FIRE | ✅ FIRE |
| v0.81.0（反例） | 240 | 0 / 0 | PASS | ✅ PASS |
| v0.83.4 重写后 | 39 | 0 / 0 | PASS | ✅ PASS |
| 正常热修 7 提交回放 | — | 5 T / 2 F | — | ✅ 与报告一致 |
**结论：抓真形态有效，反例不误伤，行数无关这一点被证明。** 但「有效性」只覆盖**典型形态**；下面 3 是绕过面，5 是误伤面。

**2. 误伤面**
- `A1-first-person`：**不过宽，反而过窄**。「我们发现」计入（1 处），但 `我们认为/我们判断/我们原先/我们漏了` 全 0。单类 ×3 被阈值挡住（实测 `3 条「我们发现」→ total=3 cats=1 → PASS`），所以**「我们」类不是主要误伤源**。至于「CHANGELOG 里出现『我们』本就该避免」——我不同意把它当作免于讨论的理由：`我们发现 X，已修` 对读者是有效信息，而它现在**不被拦**（因为只有「我们发现」一个动词）；真被拦的是「我们+某个未覆盖动词」的补集，逻辑上不成立。
- `A4-test-counts`：**不过宽，判断正确**。实测 `修复导致 3 个测试 failed 的缺陷` → 0、`实测 35 个用例转红` → 0、`3 个 failed` → 0；只有 `用例数` 字面命中。作者主动排除裸「转红」「自我更正」是对的（我复算了 v0.81.0：不排除则误伤 6 处）。
- **真正的误伤源是 A6 + A7 叠加**：`勘误：上一版的…写错了` 这类**纯正当**条目，两条即触发（B-2 情形①，端到端 rc=1）。这才是必须修的误伤。

**3. 阈值「≥3 处且 ≥2 类」评价与绕过**
- **阈值本身合理**：单类 ×4 实测 PASS（写法习惯被挡住），2 处 2 类 PASS，3 处 2 类 FIRE —— 边界行为符合设计意图。不要改。
- **但改口风能绕过，且成本极低**（实测）：`初版判断有误，经复核推翻，回归验证转红，5 passed` → total=**1**；`一度误判为 A，后经核对改为 B` → total=**0**；`两轮独立评审` → **0**（「两」不在字符类）。
- **判断：这是设计缺陷，不是"只需拦典型形态"。** 理由不是"理论上能绕过"，而是 **B-1 已证明存在零成本绕过**（坏条目任意一行加「（阈值）」即可 total=5→0）——那一条是**一行注释**，不是改写整段口风。改口风需要作者持续努力且违反自己刚写的规范（属"故意违规"，可接受漏）；「加个词就归零」是**无意的、顺手就会发生的**（正常条目里写「阈值」就自动豁免该行），会把判据静默削弱成随机噪声。**两者必须分开对待：口风绕过可接受，词表豁免不可接受。**
- 建议：A2 补 `两`；A7 补 `初版|前一稿|首版`（成本极低，且不误伤——"初版"在正当条目里几乎不出现）；**优先级低于修 B-1/B-2/B-3**。

**4. 挂载点正确性**
- **静态**：2z2 在 `pre-commit-gate.py:1192`，缩进 4，与 `for state_file in state_files:`（`:767`，缩进 4）同级 ⇒ **确在循环外** ✅。
- **运行时（mktemp git 仓库，复制真实 `agate/scripts` + `agate/rules/markers.yaml`）**：
  - `T1` 只暂存坏 `CHANGELOG.md`、**无 `.state.yaml`**（hotfix 场景）→ **rc=1，真阻断** ✅（stderr 打印命中明细）
  - `T2` 暂存坏件 + 工作区改好（不 `git add`）→ **rc=1** ✅ ← 我上一轮实测到的是 rc=0，**作者在 d3d16ab7 已修**（改用 `_git_show(repo_root, ":" + _rel)` 读暂存区 blob，`:1214-1218`）
  - `T3` 暂存好件 → rc=0 ✅；`T4` 完全没暂存 CHANGELOG → rc=0 ✅（前置门有效）
- **唯一缺陷**：守护测试没有断言缩进（A4 问题 2），把它移进循环体内测试仍绿。

**5. CHECK 17 兜底是否有效 → 结论：作为「CI 兜底」的说法不成立，但代码/CHANGELOG 已如实承认这一点，只有 README 还写着旧说法。**
- `docs-check.yml` 的 `paths` **含** `CHANGELOG.md`（`:14`、`:27`）✅。
- 但该 job 名是 `docs-consistency`，`gh api repos/randomgitsrc/agateon/branches/main/protection` 实测 required = `shellcheck (ubuntu/windows)` / `pytest (ubuntu/windows)` / `consistency` / `gate-backstop` —— **`docs-consistency` 不在其中** ⇒ 它红了**不阻止合并**。
- 而 required 的 `consistency` job 在 `docs_only=true` 时 `exit 0` fast-pass（`protocol-tests.yml:273-276`）⇒ **纯 docs 提交（CHANGELOG 的主场）由 required 检查完全看不见**。
- CHECK 17 本身有效：注入坏条目到隔离副本 → `❌ FAIL CHECK 17` + rc=1 ✅（且因为用 `rep.error` 而非 `rep.warn`，**不会**被 `is_frozen_loc` 折叠进「冻结文件 N 条」聚合行——这一点设计正确）。
- **判定**：`CHANGELOG.md:54-56` 与 `check-protocol-consistency.py:1452-1455` 已如实写「不是可靠兜底」，✅；**但 `agate/scripts/README.md:73` 仍写「CI 由 CHECK 17 兜底（覆盖 `--no-verify`）」❌ —— 同一批改动内两处相反，必须改 README。**

**6. A4b 转红清单 + BDD-23 规避是否正当**
- **转红清单：空**（实测，见 A4b）。`test_bdd_23_no_new_check_star_script_added` 绿、`CHECK9-coverage` 无新增告警（`grep -c "agate-changelog-quality" /tmp/c-full.log` = 0，即新脚本在 consistency 输出里零出现）、SG.6 14 passed。
- **但"规避是否正当"的答案是：规避动作本身不正当，虽然结果无害。** 依据：(a) 该判据 exit 1 阻断 commit，是 `pre-commit-gate.py` 中唯一承载阻断判定的 `agate-*.py`，"工具/观测"自我归类不实；(b) 锚点表**本来就接受** `agate-*.py`（`agate-mark.py`、`agate-state-yaml-check.py` 已在表中，`check-protocol-consistency.py:648-701`），所以"用 agate- 前缀"与"不登记"没有必然联系——真正的理由是 `uncovered_gate_scripts()` 只 glob `check-*.py`（`check-protocol-consistency.py:922-926`，`agate/scripts/README.md:12-15` 已如实记载该盲区）。**修法：不必改名，在 `SCRIPT_ALIGNMENT_ANCHORS` 补一条锚点**（关键词实测均存在），让 CHECK 9 正向守护"判据单源"。

**7. `_strip_non_prose()` / 自指误伤修复是否可靠 → 不可靠，这是本批最严重的一处。**
- **它能被滥用，而且门槛低到"顺手"**：单加「阈值」「扫描面」「自检」「误伤」「词表」「本判据」「该判据」「判据本体」「判据规则」「过程痕迹等」中**任一个**词，整行即豁免（实测 total 5→0，10/11 全中）。只有「判据」一词被修好。
- **注释与实现不符**（`agate-changelog-quality.py:119-121` 自称"必须同时满足『提到判据/词表』且『是元讨论的句式』"）——实现是纯 alternation。
- **它现在就在吃真检出**：`本版把重试阈值从 3 调到 5；第一版设成 10，三轮评审后改回` → total=0（该拦）；把「阈值」换成「上限」→ total=1。判据自己那条 `[Unreleased]` 条目（含「6 类」「本判据」）也全靠它才通过（不剥离则 total=2/2 类，尚未 FIRE，但在边缘）。
- **构成明显漏口，判断：是。** 建议见 A2 —— 优先方案是**放弃行级词匹配豁免，改为"只在完整围栏代码块/引用块内豁免"**；如果保留行级，必须改成真双条件（同行内「判据/词表」与「扫描/命中/阈值」共现 within N chars），并把守护测试**参数化覆盖每一个词**。

**8. A8 声称-命令绑定** → 见上表。要点：`248/191/240/21/25/0` 行与命中数、`211/25/186`、`185633/2944`、`0.033s`、`1.94/1.98s`、7 提交 5T/2F **全部可复核**；`158/121`（测试文件注释残留）**复核不出、无产出命令**；`5.00 ms` **复核不出**（实测 1.46 ms 两段 / 18.5 ms 全文 / 20.1 ms CLI）。

---

## BLOCKER / MINOR 清单（文件:行号 + 修法）

### BLOCKER

**B-1 `agate/scripts/agate-changelog-quality.py:119-123`**（`_META_DISCUSSION`）— 注释称"必须同时满足两个条件"，实现是纯 alternation；10/11 个词单独出现即整行豁免，坏条目加「（阈值）」即 total 5→0。
→ 改成真双条件（同行内「判据/词表」与「扫描/命中/阈值」共现），或改为"仅围栏/引用块内豁免"。
→ 同步 `agate/tests/unit/test_check_changelog_quality.py:169` 参数化覆盖 `_META_DISCUSSION` 的每个词（现在只测了「（判据）」）。

**B-2 `agate/scripts/agate-changelog-quality.py:64-68`**（A6-lessons / A7-revisions）— 两条**纯正当**的「勘误：上一版的…写错了」即 FIRE（实测 total=4 cats=2，端到端 rc=1 阻断）。这两类词在技术文档里是合法动词。
→ A6 收窄为 `教训(?!落地)|事后复盘|复犯`；A7 去掉 `上一版的|上一版写|原先写`（保留 `第一版(?:判断|实现)…错`）；或把 A6+A7 合并为同一类（语义同源，各自单类已被阈值豁免）。
→ 补一条正向测试：`勘误：上一版的示例代码漏了 await` ×2 + `教训：…` 必须 PASS。

**B-3 `agate/scripts/agate-changelog-quality.py:23-25` + `:106-112`** — 扫描面含「最新已发布段」⇒ 存量用户仓库的**已发布历史快照**（`doc-freshness-guide.md` §3 明定"保留不动"）会造成硬阻断；实测 rc=1，唯一出路是改写历史快照。与脚本自述「对存量仓库零影响」自相矛盾。
→ 已发布段降级为 `exit 2`（或 `--released-warn-only`），只让 `[Unreleased]` 具备阻断力；或改自述，明确"会要求改写最新已发布段"并给出豁免方式。
→ 补一条测试：Unreleased 干净 + 已发布段是过程日志 → 期望 rc=0 或 2（现状 1）。

**B-4 `agate/scripts/check-protocol-consistency.py:1457-1459`**（+ `agate/WORKFLOW.md:350-366`）— 两件事：
(a) 用 `agate-*.py` 改名规避了 CHECK9-coverage / SG.6 登记面（实测改回 `check-` 前缀即 CHECK9-coverage WARN + SG.6 red），而锚点表**本就接受** `agate-*.py` ⇒ 应在 `SCRIPT_ALIGNMENT_ANCHORS` 补锚点（关键词 `过程痕迹`/`FIRE_MIN_TOTAL`/`_CATEGORIES` 均实测存在），不必改名；
(b) `WORKFLOW.md:347` 自称"pre-commit 检查集的唯一事实源"，但表里**没有 2z2**（有 2z/2y）⇒ 补一行。

**B-5 `agate/scripts/README.md:73`** — 写「CI 由 CHECK 17 **兜底**（覆盖 `--no-verify`）」，与 `CHANGELOG.md:54-56` 及 `check-protocol-consistency.py:1452-1455` 的「**不是**可靠兜底」直接矛盾（同一批改动内）。
→ 改成与 CHANGELOG 一致的说法。

### MINOR

**M-1 `agate/tests/unit/test_check_changelog_quality.py:6`** — 残留「158 处 / 121 处」，实测无法复现、无产出命令（A8）。→ 改为「248 行命中 21 处、191 行命中 25 处」。

**M-2 `agate/tests/unit/test_check_changelog_quality.py:128-139`** — 挂载点守护用 `mount > loop` 行号判据；实测把 2z2 移进循环体仍 PASS。→ 改为断言两者缩进相等。

**M-3 `agate/scripts/agate-changelog-quality.py:48-51`** — A2 字符类缺「两」：`两轮评审/两轮独立评审` 实测 0（`二轮评审` 命中）。→ 字符类补 `两`，并考虑 `多|数|若干`。

**M-4 `agate/scripts/agate-changelog-quality.py:44-46`** — A1 只认「我们发现」，`我们认为/我们判断/我们原先/我们漏了/我们错` 实测全 0。→ 泛化为 `我(?:们)?(?:发现|认为|判断|原先|漏|错|写|以为)`。

**M-5 缺 2z2 行为级测试** — `agate/tests/integration/test_pre_commit_hook.py` 里现有两处 CHANGELOG 用例测的是 2m 而非 2z2（`grep "changelog-quality"` → 0）。→ 补"只暂存坏 CHANGELOG、无 `.state.yaml` → gate 非 0"。

**M-6 `docs/reviews/changelog-guard-placement-review-2026-11-27.md:40,128`** — 「判据本体 5.00 ms」复核不出（1.46 ms 两段 / 18.5 ms 全文 / 20.1 ms CLI）。→ 改成实测口径或删除该数。

**M-7 `docs/reviews/changelog-guard-placement-review-2026-11-27.md` §2.1 的 E-2** — 「只暂存 CHANGELOG 时 gate rc=0」在 `d3d16ab7` 后已不成立（同场景 rc=1）。属历史快照可留，但该报告正被当作决策依据引用，建议加一行时点标注。

---

## 我的实测记录（可复现命令）

```bash
# ── 判据有效性（基线 d3d16ab7）──
python3 - <<'EOF'
import re, importlib.util
spec = importlib.util.spec_from_file_location("ccq","agate/scripts/agate-changelog-quality.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def sech(text, ver):
    lines=text.splitlines(); heads=[(i,l) for i,l in enumerate(lines) if re.match(r"^## \[",l)]
    for i,l in heads:
        if ver in l:
            e=next((j for j,_ in heads if j>i),len(lines))
            return l, "\n".join(lines[i+1:e]), e-i-1
    return None,None,0
EOF
# 实测结果（段行数 / total / 类 / FIRE）：
#   0.78.0  248  21  3  True
#   0.77.0  191  25  3  True
#   0.83.4  144  16  5  True   (git show 3df9c9e8^:CHANGELOG.md)
#   0.81.0  240   0  0  False  ← 反例
#   0.83.4'  39   0  0  False  (HEAD)
#   Unreleased 15  0  0  False

# ── 绕过面：单加一词即整行豁免（B-1）──
# 基线 "- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训" → total=5
# +（阈值）/（自检）/（词表）/（扫描面）/（误伤）/（本判据）/（该判据）/（判据本体） → total=0  ❌
# +（判据）                                                                    → total=5  ✅

# ── 误伤面（B-2）──
# - 勘误：上一版的迁移命令写错了（`setup` 应为 `init`），已更正。
# - 勘误：上一版的示例代码漏了 `await`，已补齐。
#   → total=4 cats=2 ⇒ 真跑 pre-commit rc=1（阻断）

# ── 挂载点运行时（mktemp git 仓库 + 复制 agate/scripts + agate/rules/markers.yaml）──
# T1 只暂存坏 CHANGELOG、无 .state.yaml            → rc=1  ✅（hotfix 场景真拦）
# T2 暂存坏件 + 工作区改好（不 add）                → rc=1  ✅（d3d16ab7 已修；修复前为 rc=0）
# T3 暂存好件                                     → rc=0  ✅
# T4 完全不暂存 CHANGELOG                          → rc=0  ✅（零增量）

# ── 存量（B-3）──
# Unreleased 干净 + [1.2.0] 段是过程日志 → pre-commit rc=1（阻断）
# 仅把 [1.2.0] 段改成干净 → rc=0   ⇒ 必须改写「已发布历史快照」才能提交

# ── CHECK 17 ──
R2=$(mktemp -d); cp -r agate "$R2/"; cp CHANGELOG.md "$R2/"
# 往 [Unreleased] 注入 "- 第一版判断错了，三轮独立评审，变异实验，31 passed，教训"
cd "$R2" && AGATE_ROOT="$R2/agate" python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
#   → ❌ FAIL CHECK 17 … rc=1  ✅（且未被折叠进「冻结文件」聚合行）

# ── required checks（B-5 的事实依据）──
gh api repos/randomgitsrc/agateon/branches/main/protection \
  --jq '.required_status_checks.contexts'
#   → ["shellcheck (ubuntu-latest)","shellcheck (windows-latest)","pytest (ubuntu-latest)",
#      "pytest (windows-latest)","consistency","gate-backstop"]   ← 无 docs-consistency

# ── BDD-23 规避核实（B-4）──
T=$(mktemp -d); git archive HEAD | tar -x -C "$T"
cp "$T/agate/scripts/agate-changelog-quality.py" "$T/agate/scripts/check-changelog-quality.py"
cd "$T" && python3 agate/scripts/check-protocol-consistency.py --strict-errors-only | grep CHECK9-coverage
#   → WARN gate 脚本 …/check-changelog-quality.py 既未纳入 CHECK 9 锚点表
python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -q
#   → 1 failed  test_sg_6_check9_anchor_table_covers_all_gate_scripts   ⇒ 改名确实绕过了真门禁

# ── 测试/A4b ──
python3 -m pytest agate/tests/unit/test_check_changelog_quality.py -q            # 13 passed
python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q             # 69 passed（与上者合跑 82）
python3 -m pytest agate/tests/unit/test_doc_sweep.py \
  agate/tests/unit/test_check_protocol_consistency.py \
  agate/tests/unit/test_t43_check_registration_surface.py \
  agate/tests/unit/test_release_gate.py \
  agate/tests/integration/test_protocol_alignment_review.py \
  agate/tests/unit/test_tag0050_fitness.py -q                                    # 97 passed
bash agate/tests/scripts/count-tests.sh                                          # 3074（基线 3061）
~/.venvs/agate-dev/bin/ruff check <4 files>                                      # All checks passed
python3 agate/scripts/check-platform-assumptions.py                              # rc=0

# ── A8 复核 ──
git log --format=%H -- CHANGELOG.md | wc -l                                      # 211
# 按 protocol-tests.yml 的 NON_DOCS 正则逐提交判定                                     # docs-only 25 / mixed 186
git show 3df9c9e8:CHANGELOG.md | wc -lc                                          # 2944 / 308485 bytes（185633 chars）
# 计时：scan() 1.46ms（中位, n=50）；6 正则扫全文 18.5ms；CLI 20.1ms；check-changelog.py 0.034s
# consistency: 1.93 / 1.94 / 1.98 s
```

**只读核验**：所有实验在 `/tmp/agate-guard-review.*`、`/tmp/sim2.*`、`/tmp/rename.*`、`/tmp/agate-check17.*` 及 `git archive` 副本中进行；跑完 `git status --porcelain` 与基线的差异**仅本文件与留痕文件**。未执行任何 `git add/commit/reset/checkout/stash/clean`，未改 git config。

---

## 闭环

| 结论 | 主 Agent 动作 |
|---|---|
| **MISALIGNED**（A1/A2/A3/A4/A5/A6/A8） | **必须修复后重审**。B-1..B-5 是机制缺陷（可被绕过 / 合法内容被阻断 / 存量快照被迫改写 / 门禁被规避 / 同批自相矛盾），不是措辞；按 `AGENTS.md`「真 MISALIGNED 一律修完再复审」不得以"呈现类问题"跳过。 |
| **NEEDS_HUMAN_REVIEW**（A7） | 需确认：是否接受"对所有 agate 用户仓库阻断"这一成本（ADR-015 + 「新增判据 = 给所有使用者加成本」），还是先把 B-2/B-3 收窄再上阻断。**未确认前等同 MISALIGNED，不允许 commit。** |

> 设计取向再强调一次：**阻断级、不用行数、A3 只提示不计数、扫描面只扫两段 —— 这四条实测都对，不要在修复中放宽它们。** B-1..B-5 全部可以在保持这四条的前提下修掉。
