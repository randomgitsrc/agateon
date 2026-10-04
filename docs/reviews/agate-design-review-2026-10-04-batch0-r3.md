---
review_date: 2026-10-04
reviewer: independent-adversarial (design review, round 3, fresh context)
review_round: 3
change_summary: TAG0042 第 0 批 9 项缺陷修复设计 v3 的第三轮核验——核验 R2 新提出的 8 项修订是否闭合 + 是否引入新问题
files_changed: [docs/design-notes/design-tag0042-batch0-defects.md]
reviewed_object_sha256: 593606cdc10bf277e49682810719693fb9ad26cb11b7146930d16a71855fbf09
reviewed_object_commit: a27a1d1
branch: design/tag0042-batch0
prior_round: docs/reviews/agate-design-review-2026-10-04-batch0-rereview.md (NEEDS-REVISION, 对象 05edb02)
status: approved-with-nits
---

# 独立对抗式设计评审：TAG0042 第 0 批（9 项缺陷修复）— 第三轮

## 0. 锚定核验（无对象漂移）

| 项 | 值 |
|---|---|
| 被评审 commit（任务指定） | `a27a1d1dbbc1dcc2121a8c23d8ec67706a74e67a` |
| 该 commit 中文件 sha256（实测） | `593606cdc10bf277e49682810719693fb9ad26cb11b7146930d16a71855fbf09` |
| 工作区文件 sha256（实测） | `593606cdc10bf277e49682810719693fb9ad26cb11b7146930d16a71855fbf09` |

命令与输出（实测）：

```
$ git rev-parse --abbrev-ref HEAD
design/tag0042-batch0
$ git show a27a1d1:docs/design-notes/design-tag0042-batch0-defects.md | sha256sum
593606cdc10bf277e49682810719693fb9ad26cb11b7146930d16a71855fbf09  -
$ sha256sum docs/design-notes/design-tag0042-batch0-defects.md
593606cdc10bf277e49682810719693fb9ad26cb11b7146930d16a71855fbf09  docs/design-notes/design-tag0042-batch0-defects.md
$ git status --porcelain
（空）
```

**⇒ 指定对象内部一致，工作区 == 指定 commit，无对象漂移。** 全程只读，未执行任何写仓 git 命令；
所有 scratch 实验（悬空软链探测）在 `mktemp -d` 一次性目录内「建→用→清」同一次 bash 调用完成。

**只读纪律**：已按要求先读 `agate/assets/review-roles/protocol-alignment-review.md`
与 `agate/assets/templates/dispatch-prompt.md` 的评审角色节（L110-129，含 RM-AG0081 事故条文）。

---

## 1. R2 的 8 项修订逐条核验

### 汇总表

| # | 修订项 | 判定 | 证据要点 |
|---|---|---|---|
| 1 | X5 存量数字 315/21 + 正确理由 + 条件性低风险 | ✅ **已修复** | **我用仓库自己的解析器独立复现 315/21、P3=0**；且用真实 resolver 实测 21 条 formatter 全空 |
| 2 | X6 presence 正则落定 + 警告 | ✅ **已修复** | v3 L271 写死 `re.match(r"^follows_existing_pattern:", line)`；L273 含明确警告 |
| 3 | X3 补齐 5 个 SKIP 面 + 行为判据 | ⚠️ **修复不完整**（正文齐、V3 锚未同步） | 5 面行号逐个核对**全部正确**；但 V3 锚（L446）仍只描述 1 面 |
| 4 | X6 存量口径改「仅 TAG0018」 | ✅ **已修复**（残留一处措辞不精确） | **我实测声明形式 = 1 任务**；「3 个任务」已更正 |
| 5 | X2 回退语义 + 两条测试 | ✅ **已修复** | L89-96 定义回退 + 显式提示 + 两输入测试 |
| 6 | 基线字面值更新到当前 | ❌ **未修复** | L6 仍写 `05edb02`（**是 a27a1d1 的父提交**），且 L7 仍在提 `fa2fc3d` |
| 7 | X4 别名词表给出 | ⚠️ **修复不当** | 词表已给出（形式合规），但**我实测英文 3 条正则在两仓 P6 命中 = 0**，且漏掉真实写法 |
| 8 | §3 去重 + X9 DEBT0013 核对 | ✅ **已修复** | §3 重复行已删（v2 有 2 处、v3 有 1 处）；L378 + V9 均含 DEBT0013 时序核对 |

**⇒ 8 项中：5 项已修复、2 项修复不完整/不当、1 项未修复。**

---

### 1.1 【应修-1】X5 存量数字更正 —— ✅ **已修复**（我一比一复现）

**v3 声称**（L218-232）：315 条 / 21 条含管道（`parse_gate_commands_block` 口径），
且真实理由是「21 条全在 `P5*` 键且 formatter 为空 ⇒ bail；P3 键含管道 = 0」。

**我的独立复现**（**注意：`parse_gate_commands_block(text)` 收的是文本而非路径，返回
`(has_block, [(key, value), ...])` 元组**——第一次误用签名得 0，改正后结果如下）：

```
$ python3 -c "（逐 P2-design.md 调 agate_common.parse_gate_commands_block(text)）"
TOTAL 315 PIPE 21 P3TOTAL 37 P3PIPE 0
--- by task ---
  TAG0025-agateon-rename 11
  TAG0010-python-migration 5
  TAG0011-test-migration 4
  TAG0003-workspace-architecture 1
```

**⇒ v3 的 315/21 与逐任务分解（TAG0025 11 / TAG0010 5 / TAG0011 4 / TAG0003 1）
与我的实测逐字吻合。** v2 与 R1 的「107/1」确已更正。

**「21 条全在 `P5*` 键」核验**：实测 21 条键名为 `P5` / `P5_consistency` / `P5_ruff` /
`P5_scan` / `P5_ci` / `P5_bdd*`——**全部匹配 `P5*`，无一在 P3**。✅

**「formatter 为空 ⇒ bail」核验**（这是我重点证伪项，**读源码 + 跑真实 resolver**）：

`agate-capture-env-baseline.py:116-121` 实测：
```python
fmt_path = ""
if fmt_val and resolve_formatter is not None:
    fmt_path = resolve_formatter(fmt_val, task_dir) or ""
if not fmt_path:
    sys.stderr.write(f"ENV_BASELINE: 命令 '{cmd}' 无 formatter，…放弃捕获，不写入任何文件\n")
    parse_ok = False
    break                      # ← 在 run_test_with_formatter 之前
```
```python
json_result = run_test_with_formatter(cmd, fmt_path)   # ← L129，受影响路径
```
**⇒ bail 确在 `run_test_with_formatter` 之前，且 `break` 而非 `continue`——论证成立。** ✅

**⚠️ 但「formatter 为空」这一断言不能只看字面**：TAG0025 **确实声明了 3 个 formatter**
（`P3_formatter` / `P5_unit_formatter` / `P5_other_formatter`），
若 v3 的论证靠「这些任务没有 formatter 声明」就**会被证伪**。
真实机理在 `agate-read-p5-commands.py`：formatter 是**按后缀配对**的——
`fmt_key = "P5" + suffix + "_formatter"`，而 11 条管道命令的后缀是 `bdd1_readme_en` 等，
**与 `unit`/`other` 对不上** ⇒ 实测 formatter 仍为空。**我用真实 resolver 逐任务验证**：

```
$ P2_DESIGN=<task>/P2-design.md python3 agate/scripts/agate-read-p5-commands.py | （筛含管道项）
TAG0003: PIPE fmt=''  bats --formatter tap …
TAG0010: PIPE fmt=''  ×5
TAG0011: PIPE fmt=''  ×4
TAG0025: PIPE fmt=''  ×11
```

**⇒ 21/21 formatter 实测为空，v3 的结论正确——但正确性依赖"后缀配对"这一未写明的机理。**
记为 **N-a（措辞风险，非事实错误）**：v3 写「21 条全在 `P5*` 键且 formatter 为空」，
字面为真但**未点出"formatter 按后缀配对"**，实现者若据此推断「P5 有 formatter 就会执行」
会误判风险面。

**「条件性低风险」声明核验**：v3 L231-232「本项是『条件性低风险』，不是『无风险』…
若将来有 `P3` 键使用管道，pipefail 会立即改变 TDD 红灯判定」+ V5 锚 L448 含同款登记。✅ **已声明。**

**风险方向核验（我实测）**：
```
failing cmd | tail     plain=0  pipefail=1
passing cmd | tail     plain=0  pipefail=0
```
**⇒ pipefail 确实把被掩盖的失败暴露出来**（0→1）。v3「对 P3 方向可能是放宽（更容易判为红）」
的表述**方向正确**——因为 `check-tdd-red.py` 语义是 `exit 0 = 正确红灯`、
`exit 2 = 绿灯违反 TDD`（`check-tdd-red.py:5-7` 实测），
pipefail 让失败更易变非 0 ⇒ 更易落在 exit 0 ⇒ **更易判为"红灯合法"= 放宽**。✅

**本项判定：✅ 已修复。** 数字、理由、条件性声明三者均经我独立实测确认。

---

### 1.2 【应修-2】X6 presence 正则落定 —— ✅ **已修复**

**v3 L268-275 实测原文**：
```python
re.match(r"^follows_existing_pattern:", line)
```
并含警告：
> **⚠️ 不要用 `^follows_existing_pattern:\s*$`**——独立评审实测它**漏掉流式列表**
> `follows_existing_pattern: [a, b]`。（**第一轮评审给出的正是这个候选，照抄会复发反向缺陷。**）

**⇒ 正则已写死，警告已含，且点名了"第一轮候选"。** ✅

**我的独立反例尝试**（见 §2.3）：`^key:` 在注释行、缩进行、正文提及、表格行
**全部正确判 False**（无误判）；`\s*$` 候选确在流式列表上漏认。**v3 的选择经复现正确。**

---

### 1.3 【应修-3】X3 补齐 SKIP 面 —— ⚠️ **修复不完整**

**5 个 SKIP 面行号逐个核对**（`grep -n "SKIP:\|return 0" agate/scripts/ci-gate-backstop.py` 实测）：

| v3 声称 | 实测行号 | 实测输出 | 判定 |
|---|---|---|---|
| L124 平台未识别 | **L124-125** | `SKIP: 未识别的 CI 平台（非 Gitea/GitLab/GitHub），backstop 不生效` | ✅ 吻合 |
| L132 无 `.state.yaml` | **L132-133** | `SKIP: 无 .state.yaml，非 agate 项目` | ✅ 吻合 |
| L142 无法读取 | **L142-143** | `SKIP: 无法读取 .state.yaml` | ✅ 吻合 |
| L146 phase 无 gate 需对照 | **L146-147** | `SKIP: phase={phase}，无 gate 需要对照` | ✅ 吻合 |
| L162 refactor | **L162-163** | `SKIP: refactor 任务，TDD 红灯不适用（…）` | ✅ 吻合 |

**⇒ 5 个面的行号与语义全部精确吻合，v3 的分类正确。** ✅

**改 WARNING / 保留 的逐面决定核验**：v3 L138-144 表格逐面给出——
无 `.state.yaml` / 平台未识别 / phase ∈ PAUSED/READY/DONE / 无法读取 ⇒ **显式 WARNING**；
refactor ⇒ **保留**（语义正当）。**⇒ 逐面决定已给出，分类合理。** ✅

理由核验：refactor 面保留是对的——它**不是"未生效"，而是"有意不适用"**
（`_read_p1_change_type(task_dir) == "refactor"`，重构无新功能断言）。
若给它也打 WARNING，会把"有意跳过"与"根本没跑"混为一谈，**稀释 WARNING 的信号价值**。✅

**行为判据核验**：v3 L150-151 明确
> ⚠️ **V3 不能只用关键词判据**——须**行为判据**：对每个 SKIP 面构造输入，
> 断言「exit 0 不变」**且**「输出含 WARNING 标识」（改坏即红的负向控制）。

L456 另有全局「负向控制：每个新增用例都须'改坏即红'实测」。✅ **已从关键词判据改为行为判据。**

#### ⚠️ 残留缺口：V3 锚（L446）**未同步**到 5 面

v3 的 V3 验收锚原文（L446）：
```
| V3 | X3 不再**静默**假绿 | 无 `.state.yaml` 时：**exit 0 不变**（保 required check）
+ 输出含 **WARNING** 与"backstop 未生效"字样；有 `.state.yaml` 时按原逻辑 |
```

**V3 锚只描述了 5 面中的 1 面（"无 `.state.yaml`"）**，正文 L150-151 要求的
「**对每个 SKIP 面**构造输入」在锚里**没有体现**。
**验收锚是机械校验的入口**（§5 标题即「验收锚（逐条可机械校验）」）——
实现者照 V3 锚写用例，只会覆盖 1 面，**另 4 面（含 v3 自己标注"最该醒目"的 L142 解析失败）
会缺守护**。

**⇒ 判定：修复不完整。** 正文已补齐且正确，但**验收锚未同步** ⇒ 存在
「设计说要 5 面、锚只验 1 面」的**内部不一致**。这是 R2 修订项 3 的直接残留。

**建议**：把 V3 锚改为「对 L124/L132/L142/L146 四面各构造输入 ⇒ `exit 0` 不变 + 输出含 WARNING；
L162 refactor 面绿色保留（措辞与其余区分）；断言 5 面逐一覆盖」。

---

### 1.4 【宜修-4】X6 存量口径 —— ✅ **已修复**（另有一处措辞不精确）

**我的实测**：
```
$ grep -rnE "^(design_trivial|follows_existing_pattern):" agate-workspace/tasks/*/P1-requirements.md
agate-workspace/tasks/TAG0018-dsh-platform/P1-requirements.md:16:design_trivial: true …
agate-workspace/tasks/TAG0018-dsh-platform/P1-requirements.md:17:follows_existing_pattern:
```
**⇒ 声明形式（`^key:`）确实只有 TAG0018 一个任务**，L16/L17 两键同文件——
与 v3 §4.2（L430）「仅 TAG0018 一个任务」✅ 吻合，R2 指出的「3 个任务」已更正。

**提及形式**：`grep -rlE "design_trivial|follows_existing_pattern" …` ⇒ **5 个文件**
（TAG0010 / TAG0018 / TAG0022 / TAG0024 / TAG0031），除 TAG0018 外**均为正文/表格提及**。

#### Nit：L280 的「另有 2 个任务含 `follows_existing_pattern`」口径不精确

v3 L279-281 原文：
> **存量影响**（评审实测，我复核）：全仓**仅 1 个任务**（TAG0018）命中该正则，
> 且它是唯一 `candidate_count < 2` 的任务；**另有 2 个任务含 `follows_existing_pattern`**。
> **⇒ 须逐个核对这 2–3 个任务在修订后的判定。**

**我实测**：`follows_existing_pattern` 出现在 **5 个文件**中（非"2 个"）。
v3 的「2 个」不吻合任何我能复现的口径。**但**：
- 该句**不影响 X6 判定正确性**（真正的声明形式只有 1 个任务，已正确写明）；
- 它要求「逐个核对 2–3 个任务」，而实际需核对的是**声明者 1 个**（提及者不构成声明，
  正则根本不会命中）⇒ **核对面被高估，不会导致漏核对**（方向安全）。

**⇒ 判为 Nit（不阻塞）**，但建议改为：「声明形式仅 TAG0018（L16/L17）；另有 4 个任务
在正文/表格**提及**该字段名，不构成声明、不受本正则影响，无需核对」。

---

### 1.5 【宜修-5】X2 回退语义 —— ✅ **已修复**

v3 L89-96 实测原文：
> **本设计选**：**回退读工作区**——理由是"本次未暂存状态文件"是常见情形，
> 若视为无状态会导致 hook **静默跳过整条链**（正是 X2 要治的病）。
> - **但须同时**：回退时输出**显式提示**（"本次未暂存 .state.yaml，phase 取自工作区"），
>   使"读的是哪一份"可见。
> - **测试**：V2 须含**两种**输入——① 暂存区有 ⇒ 用暂存区；② 暂存区无 ⇒ 回退工作区 + 提示。

**⇒ 回退方向已定义、显式提示已定义、两条测试输入已定义。** ✅ R2 §3.5 的未闭合项已闭合。

**理由核验**：选「回退工作区」而非「视为无状态」是对的——后者会让 hook 整条链静默跳过，
正是 X2 要治的病（把"判错阶段"换成"不判"，是**用一个更严重的 fail-open 换掉一个 fail-wrong**）。

**调用点核验**：`grep -n "read_state_phase" agate/scripts/pre-commit-gate.py` 实测
**L257 与 L590** 两处，与 v3 L80-82「只有 2 个」吻合。✅

**残留 Nit（R2 的 N4 未闭合）**：`agate_common.has_staged_phase_change`（L602-618，实测存在）
与新函数 `read_staged_state_phase` 的**判据分工未说明**。二者都读暂存区 state 文件，
存在「同一概念两处实现」的漂移风险。**不阻塞**（新函数语义是"读值"，旧函数是"判是否有变更"，
职责实际不同），但建议在设计里加一句分工说明。

---

### 1.6 【宜修-6】基线字面值 —— ❌ **未修复**

v3 L6-8 实测原文：
```
6:> **事实基线**：main `4daa60b` 之后 ｜ **设计基线**：**`05edb02`**（本文自身）
7:> （⚠️ 独立评审指出：设计曾有两个版本 `f5e4c31` → `fa2fc3d`，**实现须以本版为准**；
8:> 本文已按评审的 P0/P1/P2 清单全部修订）
```

**实测该基线已过期**：
```
$ git log --oneline -1 05edb02
05edb02 design(TAG0042-批0): 按独立评审的 P0/P1/P2 清单全部修订（NEEDS-REVISION → 待复审）
$ git log --oneline -1 a27a1d1
a27a1d1 design(TAG0042-批0): 清理表格内的字面竖线 + 去重（评审 MINOR 项）
$ git merge-base --is-ancestor 05edb02 a27a1d1 && echo "YES ancestor"
YES ancestor
$ git show 05edb02:<path> | sha256sum   →  5407140da408fadf…
$ git show a27a1d1:<path> | sha256sum   →  593606cdc10bf2…
```

**⇒ `05edb02` 是 `a27a1d1` 的父提交（上上一版），两版文件 sha256 不同。**

**问题性质**：L6 写的是「**设计基线**：`05edb02`（**本文自身**）」——
「本文自身」是**自指宣称**，而本文实际是 `a27a1d1`。**该自指为假**。
R2 P2-1 要求「不得再写 `fa2fc3d`；v3 应写 `05edb02`（当时）**或本版自身**」——
v3 选了「`05edb02`（当时）」但**保留了"本文自身"的括注**，导致：
- 若按「当时基线」读 ⇒ 与「本文自身」矛盾；
- 若按「本文自身」读 ⇒ 字面值错误（应为 `a27a1d1`）。

**⇒ 判定：未修复（自相矛盾未消解）。** 这正是 R2 §3.6「实现基线字面值自相矛盾」的**同一问题**，
v3 只换了一个 commit 字面值，**未消除矛盾结构**。

**另**：L7 仍在提 `fa2fc3d`。R2 明确要求「不得再写 `fa2fc3d`」。
不过该处语境是「设计曾有 `f5e4c31` → `fa2fc3d` 两个版本」的**历史陈述**，
且已注明「实现须以本版为准」——**与 P2-1 担心的"把 fa2fc3d 当基线"语境不同**。
判为**可接受的残留**，但建议连同 L6 一并清理。

**建议改写**：
```
> **事实基线**：main `4daa60b` 之后 ｜ **设计基线**：**`a27a1d1`**（本文自身）
> （历史：设计经 `f5e4c31` → `fa2fc3d` → `05edb02` → `a27a1d1`；**实现须以本版为准**）
```

---

### 1.7 【宜修-7】X4 别名词表 —— ⚠️ **修复不当**

**形式合规性**：v3 L181-190 已给出词表**本身**（不再留作待办）：

| 形态 | 判据 |
|---|---|
| 结构化字段 | `p5_reuse`/`evidence_reuse` 类字段（**须先定字段名**——实现时以 schema 为准） |
| 中文短语 | `引用\s*P5\s*证据`（现行，保留） |
| **英文别名** | `reuse[sd]?\s+P5\s+evidence` / `reusing\s+P5\s+evidence` / `P5\s+evidence\s+reus` |

并注明 L189「英文词表**须在实现时用两仓真实语料验证**」。**⇒ 形式要求满足。** ✅

#### 但内容经实测**不成立**——词表覆盖 0 个真实实例

**我的实测（扫全部 P6-acceptance.md）**：
```
zh (current)                 hits=1 ['TAG0019-risk-routing']
en1 reuse[sd]? P5 evidence   hits=0 []
en2 reusing P5 evidence      hits=0 []
en3 P5 evidence reus         hits=0 []
--- union of proposed en patterns --- （无输出）
```

**⇒ 三条英文正则在整个 P6 语料中命中 0 次。** 这正是 v3 自己警告的
「防'定义了却无实例'」情形——**词表本身即该情形**。

**更关键：真实语料中确实存在 v3 词表漏掉的写法**。实测
`TAG0027-orchestration-semantics/P6-acceptance.md:18`：
```
… 审计 7 reuse_allowed）。功能型任务（非 refactor）…
```
`TAG0034-dispatch-routing/P6-acceptance.md:33`：
```
- **P5 证据复用（审计 7）**：`git diff --stat …` 无输出 → … → `reuse_allowed`；…
```
这两处都是**真实的"复用声明"语义**，但**中文正则 `引用\s*P5\s*证据` 不匹配**
（TAG0034 写的是「P5 证据复用」而非「引用 P5 证据」），**英文词表也不匹配**
（写的是 `reuse_allowed`，非 `reuse P5 evidence`）。

**⇒ 语料里的真实英文/变体写法是 `reuse_allowed`（判定结果词）与「P5 证据复用」（中文变序），
而 v3 词表覆盖的是 `reuse P5 evidence` 这类两仓都不存在的构造。**

**风险方向**：这是 **fail-open**（漏认 ⇒ 判为"未声明复用" ⇒ `no_reuse_claim_possible`），
与 X4 要治的病**同型**。v3 L178-179 已正确指出放宽=更多拦截，但**词表选错方向**——
它放宽的是**不存在的写法**，而**真实写法仍漏**。

**⇒ 判定：修复不当。** 形式合规、方向自洽，但**内容经两仓语料实测不成立**，
且 v3 自己把「用真实语料验证」留到了实现时——**该验证现在就该做，且结果否定该表**。

**建议**：词表改为以**实测语料**为准：
- 中文变序：`P5\s*证据\s*复用`（TAG0034 实证）**加入**；
- 结构化：`审计\s*7` / `reuse_allowed` / `reuse_blocked`（TAG0027/TAG0034 实证）；
- 英文：若无实例（实测 0），**应删去或标注"预置、当前 0 实例"**，避免"定义了却无实例"。

---

### 1.8 【宜修-8】§3 去重 + X9 的 DEBT0013 核对 —— ✅ **已修复**

**§3 去重实测**：
```
$ grep -c "X2 的「按提交类型分级」" <v3 文件>   → 1
$ git show 05edb02:<path> | grep -c "X2 的「按提交类型分级」" → 2
```
**⇒ v2 的重复行（R2 N5 指出的 L343/L347）已删，v3 仅剩 1 处。** ✅

**X9 DEBT0013 核对实测**：v3 L378：
> **⚠️ 另漏 `P8-release.md:89-93` 的 DEBT0013 时序说明**（CHECK 7 相关），改卡片时须一并核对。

V9 锚（L452）含「并核对 `:89-93` 的 DEBT0013 时序」。✅

**行号核验**：`sed -n '80,96p' agate/phase-cards/P8-release.md` 实测 DEBT0013 时序说明
位于 **L89-93**（`- **⚠️ 时序注意（DEBT0013）**：… 先 tag 后重跑即 0 ERROR`）。✅ **行号精确。**

**V9 的机械判据核验**：v3 称「**断言无脚本依赖"以 READY 提交"**（可机械：grep）」。
我实测 `grep -rn "READY" agate/scripts/*.py`：命中的是
`agate-next.py`（`_TERMINAL_PHASES` 提示不推进）、`check-state-transition.py`（终态判定）、
`pre-commit-gate.py:320`（跳过序）、`ci-gate-backstop.py:145`（跳过序）、
`check-gate.py:1495`（**恰恰要求"打 tag 后再推进到 READY"**）——
**无一依赖"以 READY 提交产出"**。✅ **V9 断言成立。**

---

## 2. 我的反例尝试（含未成功的）

### 2.1 ★ X5「条件性低风险」论证 —— **尝试证伪，未成功（论证成立）**

**攻击点**：v3 称 21 条 formatter 为空 ⇒ bail。但 TAG0025 **声明了 3 个 formatter**
（`P3_formatter` / `P5_unit_formatter` / `P5_other_formatter`）⇒
**「该任务没有 formatter」是假的**，若能证明其管道命令拿到 formatter，论证即崩。

**做法**：不读文字，直接跑仓库自己的 resolver：
```
$ P2_DESIGN=agate-workspace/tasks/TAG0025-agateon-rename/P2-design.md \
  python3 agate/scripts/agate-read-p5-commands.py | （筛含管道项）
→ 11 条全部 fmt=''
```
**根因（读源码确认）**：`agate-read-p5-commands.py` 的
`fmt_key = "P5" + suffix + "_formatter"`——**按后缀精确配对**；
11 条命令后缀是 `bdd1_readme_en` / `bdd9_atomic_commit` 等，
与 `unit`/`other` 不匹配 ⇒ formatter 为空。**⇒ 证伪失败，v3 结论成立。**

**次生发现**：`agate-capture-env-baseline.py:120` 对无 formatter 是 **`break`** 而非 `continue`
⇒ 遇到第一条无 formatter 命令即**放弃整个捕获**。这意味着「21 条」的实际影响是
**整批 P5 基线捕获被放弃**，而非"逐条跳过"。v3 未提这一点（**不影响其结论**，
但"bail 的粒度是整批"值得在实现时知道）。

### 2.2 X3 的 5 个 SKIP 面分类 —— **逐面核对，分类合理**

逐个读源码核对（行号见 §1.3 表），**5 面全部吻合**。
分类合理性：refactor 面（L162）保留**正确**——它是"有意不适用"而非"未生效"；
L142（无法读取）判为"最该醒目"**正确**——数据坏了却报绿，是最危险的静默失败。
**未发现分类不当。**

### 2.3 ★ X6 正则 `^follows_existing_pattern:` —— **尝试证伪，未成功（无误判）**

构造 10 个反例行，比对候选 A（v3 采用）与候选 B（R1 的 `\s*$`）：

| 输入 | A `^key:` | B `^key:\s*$` | 期望 |
|---|---|---|---|
| `follows_existing_pattern:`（块列表） | True | True | ✅ |
| `follows_existing_pattern: [a, b]`（流式） | **True** | **False** | A 对 |
| `follows_existing_pattern: foo` | True | False | A 对 |
| `  follows_existing_pattern: [a]`（缩进） | False | False | 不误判 ✅ |
| `# follows_existing_pattern: [a]`（注释） | **False** | False | **不误判** ✅ |
| `  # follows_existing_pattern:` | False | False | 不误判 ✅ |
| `see follows_existing_pattern: for details`（正文） | **False** | False | **不误判** ✅ |
| `\| follows_existing_pattern: \| x \|`（表格） | False | False | 不误判 ✅ |
| `"follows_existing_pattern:"` | False | False | 不误判 ✅ |
| `follows_existing_pattern:   `（尾空格） | True | True | ✅ |

**⇒ 关键结论：v3 选的正则对注释行、缩进行、正文提及、表格行全部正确返回 False，
无误判；且唯一通过全部三形态（块列表/流式/注释）的候选。证伪失败。**

**⚠️ 一处需实现时注意**：`re.match` 只在**行首**匹配 ⇒ 实现必须**逐行**喂入
（`for line in lines`），不能整段文本喂。`design_trivial_declared(line)` 现有签名即逐行，
`check-gate.py:872` 的调用形态 `any(design_trivial_declared(line) for line in p1_lines)` 实测吻合。✅

### 2.4 ★ X4 英文词表 —— **证伪成功（见 §1.7）**

扫全部 P6-acceptance.md：**v3 的 3 条英文正则命中 0 实例**；
而真实存在的两种写法（`reuse_allowed` / 「P5 证据复用」）**均未覆盖**。

### 2.5 X7 严重性论证 —— **尝试证伪，未成功**

v3 称 `return 2` 是 gate_p2 的**通过码**。实测依据链：
- `check-gate.py:891-894`：`if not agent: … return 2`；P1 侧 L649-652 同情形 `return 1`；✅
- `agate/rules/phases.yaml`：P2 `gate_pass_exit: 2`；注释 L14-16 明列
  「exit 2 是多数 phase（P0-P3/P5/P6/P8）的正常通过码（… p2 L883 …）」；✅
- `pre-commit-gate.py:558-560`：`elif gate_exit == 2:` **只打印、不 `sys.exit(1)`** ⇒ 不阻断。✅

**⇒ 三方一致，`return 2` 确实是通过语义，X7 的严重性论证成立。证伪失败。**

**⚠️ 次生发现（新问题，见 §3.1）**：`gate_p4` **有同款 `return 2`**（L974-977），
但 v3 只字未提，V7 锚也只写 P2。

---

## 3. 新引入的问题 / 发现的未闭合项

### 3.1 ★ `gate_p4` 有同款 fail-open（L974-977），v3 与 V7 锚均未覆盖

**实测** `check-gate.py:974-977`：
```python
agent = _md_field_get("agent", p4_review)
if not agent:
    sys.stderr.write("GATE P4: P4-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
    return 2
```

**但 P4 的通过码不是 2**——`phases.yaml` P4 块实测 `gate_pass_exit: 0`，
且 `gate_p4` 末尾实测 `return 0`（L1076）。**P4 的 `return 2` 落在
"∉ pass_set 且 ≠ 1"的区间** ⇒ 按 `agate-next.py:431-434` 实测：
```
# exit ∉ gate_pass_exit 且 ≠ 1（真暂停/异常，协议实际极少）→ 落盘 resolution 转主 Agent
_write_exit2_resolution(task_dir, phase, state, rc)
```
**⇒ P4 缺 `agent` 会触发"真暂停/异常"路径，落盘 `exit2-resolution` 并转主 Agent 决策**——
既非"通过"（P2 那样 fail-open），也非"未通过"（正常 retry），而是**异常暂停**。
**语义比 P2 更混乱**（一个本该 WARNING 的数据缺失，被当成协议异常）。

**为何算"新引入的问题"**：v3 的 X7 把问题定性为「与 P1 不一致 → 统一为 1」，
但它**只列了 P2**。实测**同型缺陷有两个 site**。若本批只修 P2（如 v3 所述），
**P4 的同款 fail-open 会留下**——而 X7 的立项理由（"返回了通过码"）对 P4 部分成立
（返回了一个**错误的异常码**，同样不该）。

**建议**：X7 与 V7 锚扩到 **P2 + P4 两个 site**，逐 site 断言
「缺 `agent` ⇒ 返回该 phase 的未通过码（1），且 ≠ `gate_pass_exit`」。
若有意只修 P2，须在设计中**显式声明 P4 归属哪一批**（依 §3 的"边界声明"方法要求）。

### 3.2 V3 验收锚与 X3 正文不一致（见 §1.3，R2 修订项 3 的残留）

### 3.3 基线自指为假（见 §1.6，R2 P2-1 未真正闭合）

### 3.4 ✗ 已尝试但**未成立**的疑点（如实记录）

- **「21 条全在 `P5*` 键」是否漏了非 P5 键**：实测 21 条键名全部匹配 `P5*`，**未漏**。
- **X6 正则是否误判注释/缩进/正文**：实测**全部正确判 False**，**未误判**。
- **`design_trivial: true  # 注释`（R2 N1）是否可解析**：`agate-md-field-get.py:87`
  实测 `BOOL_FIELDS = frozenset({"ui_affected", "internal_only", "design_trivial"})`，
  走专用通道；v3 L266-267 明写走该通道判 `== "true"` ⇒ **设计方向正确**。
  （R2 已实测两通道皆通；我未重复该实验，标为**推断**。）
- **X2 是否只改 L257 会造成不一致**：v3 已要求两处都改，**未发现问题**。

---

## 4. 总体判定

### **`APPROVED WITH NITS`**

**能否开始实现：可以，但须先修 3 项**（下述 ①–③ 为**实现前必办**，其余为 Nit）。

**判定理由**：

**已充分闭合的（5/8）**：
- ✅ X5（315/21 + 真实理由 + 条件性声明）——**我一比一复现，且用真实 resolver 验证了
  formatter 配对机理**。这是本轮质量最高的修订。
- ✅ X6 正则落定（写死 + 警告）——**10 个反例构造证伪失败**。
- ✅ X6 存量口径（仅 TAG0018）——**声明形式实测确为 1 个任务**。
- ✅ X2 回退语义（回退 + 提示 + 两测试）——R2 §3.5 未闭合项已闭合。
- ✅ §3 去重 + DEBT0013 核对——**去重实测 2→1；DEBT0013 行号 L89-93 精确**。

**须修后再实现的 3 项**：

| # | 问题 | 性质 | 修法 |
|---|---|---|---|
| ① | **X7 只覆盖 P2，漏 P4 同款 fail-open**（L974-977，P4 `gate_pass_exit: 0` ⇒ 落"异常暂停"） | **新发现的功能性缺口** | X7 + V7 扩到 P2/P4 两 site；或显式声明 P4 归属批次 |
| ② | **V3 锚只描述 1 面，正文要求 5 面** | **R2 修订项 3 的残留**（内部不一致） | V3 锚改为逐面列 5 面（4 面改 WARNING + 1 面保留） |
| ③ | **基线 L6 自指为假**（写 `05edb02`（父提交）却标"本文自身"） | **R2 P2-1 未真正闭合** | 改为 `a27a1d1`（本文自身），历史版本移到括注 |

**为何是 WITH NITS 而非 NEEDS-REVISION**：
① 是**范围遗漏**（v3 已正确识别该缺陷类型与修法，只需扩一个 site），
② 是**锚与正文不同步**（正文已正确，锚是摘录不全），
③ 是**一处字面值**。三者**均不推翻任何设计的核心论证**——
X5/X6/X2/X3 的实质结论经我独立实测**全部成立**。
但三者**都会实际削弱验收强度**（① 漏一个 fail-open site、② 漏 4 个 SKIP 面的守护、
③ 实现者按错基线做 diff），故**应在实现前修掉**，不宜降级为纯 Nit。

**与 R1/R2 的关系**：R1（NEEDS-REVISION, f5e4c31）→ R2（NEEDS-REVISION, 05edb02）→
**R3（APPROVED WITH NITS, a27a1d1）**。R2 的 3 个 P0 已在 v2 闭合（R2 自证 + 我本轮复核
X6 正则、X1 门控 L320/L327、X5 前缀写法均成立）；R2 新提的 8 项中 5 项已闭合、
3 项待修。**收敛趋势明确。**

---

## 5. 已实测 vs 推断（严格区分）

### 5.1 **已实测**（命令/输出见本报告）

| # | 内容 |
|---|---|
| 1 | 对象锚定：`a27a1d1` / sha256 `593606cd…`；工作区 == 指定 commit；`git status` 空 |
| 2 | `05edb02` 是 `a27a1d1` 的**父提交**；两版 sha256 不同（`5407140d…` vs `593606cd…`） |
| 3 | **X5 数字独立复现：TOTAL 315 / PIPE 21 / P3TOTAL 37 / P3PIPE 0**；逐任务 TAG0025=11、TAG0010=5、TAG0011=4、TAG0003=1 |
| 4 | **21 条键名全部匹配 `P5*`**（`P5` / `P5_consistency` / `P5_ruff` / `P5_scan` / `P5_ci` / `P5_bdd*`），P3 = 0 |
| 5 | **跑真实 resolver（`agate-read-p5-commands.py`）：21/21 formatter == ''** |
| 6 | `agate-capture-env-baseline.py:116-121` 无 formatter ⇒ `parse_ok=False; break`，**在 `run_test_with_formatter`(L129) 之前** |
| 7 | formatter 按**后缀精确配对**（`fmt_key = "P5" + suffix + "_formatter"`），TAG0025 的 `unit`/`other` 不覆盖 `bdd*` |
| 8 | **pipefail 方向实测**：`failing \| tail` plain=0 / pipefail=1；`passing \| tail` 均 0 |
| 9 | `check-tdd-red.py:5-7` 语义（0=正确红灯 / 2=绿灯违反 TDD）⇒ pipefail 方向为"放宽" |
| 10 | **X3 5 个 SKIP 面行号逐个核对**：L124/132/142/146/162 全部吻合，输出文本一致 |
| 11 | **X6 正则 10 反例真值表**：`^key:` 对注释/缩进/正文/表格/引号**全部正确判 False**；`\s*$` 漏流式列表 |
| 12 | **X6 存量**：声明形式（`^key:`）**仅 TAG0018**（L16/L17）；提及形式 **5 个文件** |
| 13 | **X4 词表实测**：3 条英文正则在全 P6 语料命中 **0**；中文现行正则命中 1 |
| 14 | **X4 真实写法漏识别**：TAG0027:18 `审计 7 reuse_allowed`、TAG0034:33「P5 证据复用」均不匹配现有/新增判据 |
| 15 | `agate_common.design_trivial_declared` L1389-1391 现实现；消费点 `check-gate.py:872`（逐行喂入） |
| 16 | `agate-md-field-get.py:87` `BOOL_FIELDS` 含 `design_trivial`；L230 专用通道 |
| 17 | **X7 三方一致**：`phases.yaml` P2 `gate_pass_exit: 2`；`check-gate.py:891-894` `return 2`；`pre-commit-gate.py:558-560` exit 2 **只打印不阻断** |
| 18 | **★ 新发现：`gate_p4` L974-977 同款 `return 2`；P4 `gate_pass_exit: 0`、`gate_p4` 末尾 `return 0`；`agate-next.py:431-434` 对 rc ∉ pass_set 且 ≠1 落 `exit2-resolution` 转人工** |
| 19 | `pre-commit-gate.py` `read_state_phase` 调用点 = **L257 + L590**（与 v3 吻合） |
| 20 | `install-hook.py:130-135` `_backup` 条件 `isfile and not islink`；**悬空软链实测**：`islink=True, isfile=False` ⇒ 备份条件 False；`_ln_sf` L103 → `os.unlink` L113 |
| 21 | `P8-release.md` DEBT0013 时序说明位于 **L89-93**（v3 引用精确） |
| 22 | **V9 机械判据**：`grep READY agate/scripts/*.py` ⇒ **无脚本依赖"以 READY 提交"** |
| 23 | **§3 去重**：v2 有 2 处「X2 的『按提交类型分级』」，v3 仅 1 处 |
| 24 | `agate_common.has_staged_phase_change` 存在（L602-618），与新函数判据分工未说明 |

### 5.2 **推断**（未实测，须后续验证）

| # | 内容 | 依据 |
|---|---|---|
| 1 | `design_trivial: true  # 注释` 经 `agate-md-field-get.py` 输出 `true` | **R2 已实测**，我未重复；由 L87/L230 通道存在性推得设计方向正确 |
| 2 | 存量任务实际不会因 X1/X5/X6/X7 转红 | v3 §4.2 声称的扫描结果我只**部分复现**（X5/X6/X7 已验；**X1 未验**——须逐 commit 重放，v3 自己也标"不可操作"） |
| 3 | 放宽 `p6_declares_reuse` 后 audit7 三态的实际变化 | 我确认了消费链（`check-p6-provenance.py:622-623`、`P8-release.md:84-88`），但**未跑端到端判定** |
| 4 | refactor 面保留 WARNING 措辞差异的实现效果 | 设计意图明确，实现细节未验 |

### 5.3 未能完成 / 未做的事项（如实上报）

1. **未跑全量 pytest**（任务明令禁止）——本报告不含 pytest 实跑输出。
2. **X1 的存量影响未验证**：须逐 commit 重放 hook 判定"收尾提交 diff 是否含 `[PROD_TOUCHED]`"，
   v3 自己也承认该扫描"不可操作"并退回 `grep` + 人工核对。**我未做该人工核对**——
   它是实现前的门禁（§4.2），**不属本轮设计评审范围**，但**仍待办**。
3. **未验证 `read_staged_state_phase` 的实现可行性**（函数尚未存在，设计阶段）。
4. **未在两仓之外验证 X4 语料**：题目要求"扫两仓 P6-acceptance"。我扫的是
   **agateon 本仓**（`agate-workspace/tasks/*/P6-acceptance.md`，共 5 个文件含 `reuse`）。
   **另一仓（peekview）的 P6-acceptance 未扫**——若该仓存在英文复用写法，
   结论可能需补充。**这是本报告 X4 结论的唯一覆盖缺口。**

---

## 6. 建议的最小修订清单（按优先级）

| # | 项 | 动作 |
|---|---|---|
| 1 | **X7 扩到 P4** | X7 节 + V7 锚加 `gate_p4` L974-977；或声明 P4 归属批次 |
| 2 | **V3 锚同步 5 面** | 改写 V3 锚为逐面（L124/L132/L142/L146 改 WARNING + L162 保留） |
| 3 | **基线字面值** | L6 改 `a27a1d1`（本文自身）；历史版本移括注 |
| 4 | **X4 词表按实测重做** | 加「P5 证据复用」变序 + `reuse_allowed`；英文 0 实例项删去或标注 |
| 5 | X5 措辞 | 补一句"formatter 按后缀配对"，防据"有 formatter"误判风险面 |
| 6 | X6 存量措辞 | L280「另有 2 个任务」→ 更正为"4 个任务仅正文提及、不构成声明" |
| 7 | X2 分工说明 | 一句说明 `read_staged_state_phase` 与 `has_staged_phase_change` 的判据分工（R2 N4） |
