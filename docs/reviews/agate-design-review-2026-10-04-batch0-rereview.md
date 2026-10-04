---
review_date: 2026-10-04
reviewer: independent-adversarial (design RE-review, fresh context)
review_round: 2 (复审)
change_summary: TAG0042 第 0 批 9 项缺陷修复设计 v2 的复审——核验第一轮 P0/P1/P2 整改项是否闭合
files_changed: [docs/design-notes/design-tag0042-batch0-defects.md]
reviewed_object_sha256: 5407140da408fadf9f2cb6a0190f8686496b182de577e741aaadb0904501f81c
reviewed_object_commit: 05edb02
branch: design/tag0042-batch0
prior_round: docs/reviews/agate-design-review-2026-10-04-batch0.md (NEEDS-REVISION, 对象 f5e4c31)
status: needs-revision
---

# 独立对抗式设计复审：TAG0042 第 0 批（9 项缺陷修复）— 第二轮

## 0. 锚定核验（无对象漂移）

| 项 | 值 |
|---|---|
| 被评审 commit（任务指定） | `05edb02` |
| 该 commit 中文件 sha256（实测） | `5407140da408fadf9f2cb6a0190f8686496b182de577e741aaadb0904501f81c` |
| 工作区文件 sha256（实测） | `5407140da408fadf9f2cb6a0190f8686496b182de577e741aaadb0904501f81c` |

命令与输出（实测）：

```
$ git rev-parse --abbrev-ref HEAD
design/tag0042-batch0
$ git show 05edb02:docs/design-notes/design-tag0042-batch0-defects.md | sha256sum
5407140da408fadf9f2cb6a0190f8686496b182de577e741aaadb0904501f81c  -
$ sha256sum docs/design-notes/design-tag0042-batch0-defects.md
5407140da408fadf9f2cb6a0190f8686496b182de577e741aaadb0904501f81c  docs/design-notes/design-tag0042-batch0-defects.md
```

**⇒ 指定对象内部一致，工作区 == 指定 commit，无对象漂移。**

**⇒ 第一轮 §0.2 的分支漂移问题已消解**：本轮工作区就是 HEAD 版本，`fa2fc3d` 的中间态不再需要单独裁定。

```
$ git log --oneline -4 05edb02
05edb02 design(TAG0042-批0): 按独立评审的 P0/P1/P2 清单全部修订（NEEDS-REVISION → 待复审）
fa2fc3d design(TAG0042-批0): 更正 X7——问题不是「与 P1 不一致」而是「返回了通过码」
f5e4c31 design(TAG0042-批0): 9 个「现在就是错的」缺陷修复设计（待独立评审）
bdfe8b6 Merge pull request #398 from randomgitsrc/task/TAG0042-config-and-enforcement
```

---

## 1. P0/P1/P2 逐条核验

### 汇总表

| # | 整改项 | 判定 | 证据要点 |
|---|---|---|---|
| **P0-1** | X6 两键分别处理 | ✅ **已修复** | §X6 L225-231 明写两键分开；**我实测三种实现的 gate 结果，v2 方案正确** |
| **P0-2** | X1 改目标 + 第 4 批划界 + PAUSED 留痕 | ✅ **已修复** | §X1 L52-56 + §3 L346 + §X1 L62-65 |
| **P0-3** | X5 改 `set -o pipefail; ` 前缀 + 更正风险方向 | ✅ **已修复**（但存量数字不实，见 §3.1） | §X5 L185-197；**我实测方向确为"放宽"** |
| **P1-1** | X2 调用点 4→2（L257+L590） | ✅ **已修复** | §X2 L79-82；实测 `grep` 仅 2 个调用点 |
| **P1-2** | X4 补 audit7 消费方 + 更正风险方向 + 别名词表 | ⚠️ **部分修复** | 消费方✅、风险方向✅、**别名词表仅"须补"未给** |
| **P1-3** | X7 三方一致 + 37/37 ⇒ 转红 0、无需迁移期 | ✅ **已修复** | §X7 L267-275；**我实测 37/37 missing=0** |
| **P1-4** | X9 更正理由 + DEBT0013 + "22/38" | ✅ **已修复** | §X9 L323-335；**我实测 READY_DONE=38 P8_EVER=16 NEVER=22** |
| **P1-5** | X3 补第三个 SKIP 面 | ⚠️ **修复不完整** | 补了 phase 面，但实际有 **6 个** `return 0` 面，见 §3.2 |
| **P1-6** | X8 具体化 readlink + 并入第 10 项 | ✅ **已修复** | §X8 L293-300；**我实测悬空软链描述准确** |
| **P2-1** | 声明实现基线（f5e4c31 → fa2fc3d） | ⚠️ **修复不当** | v2 L6-8 写"设计基线 `fa2fc3d`"——**但被评审对象是 `05edb02`**，基线声明又落后一版 |
| **P2-2** | 补 X1 与第 4 批边界声明 | ✅ **已修复** | §3 L346 + §1 L54-56 |
| **P2-3** | §4.2 补每项扫描命令与实测结果 | ⚠️ **部分修复** | 表已补（L379-386），但 **X5/X6 的实测数字不实**，见 §3.1/§3.3 |
| **P2-4** | 定义 V10 判据强度 | ✅ **已修复** | §4.2 L388-391（①/②/③ 三分归因） |
| **P2-5** | 补 self-gate-review 留痕义务 | ✅ **已修复** | §6 L424 |
| **另** | V1/V5/V6/V8/V9 同步更新 | ✅ **已修复** | V1 L399、V5 L403、V6 L404、V8 L406、V9 L407 全部按新方案改写 |

**统计：P0 3/3 已修复；P1 4/6 已修复 + 2 项不完整；P2 4/5 已修复 + 1 项修复不当。**

---

### P0-1 — X6 两键分别处理：✅ **已修复**（本项是本轮最重要的正向确认）

**v2 的目标行为**（L225-231）：

> - `design_trivial`：走 `_md_field_get("design_trivial", p1_file)`（`agate-md-field-get.py` 已有
>   `_regex_scalar(..., r"design_trivial:\s*(true|false)")` 通道），**判 `== "true"`**；
> - `follows_existing_pattern`：**保持 presence 语义**（它是 list，有键即声明），
>   且须**兼容块列表形态**（键行无值也算）——即正则的 `\s*\S` 要求**不适用于该键**。
> **⛔ 原设计「按值判断，`true` 才降为 1」是错的**

**源码核验（实测）**：

```
$ grep -n "design_trivial_declared" -A3 agate/scripts/agate_common.py
1389:def design_trivial_declared(line):
1390:    """P1-requirements.md 行首 `design_trivial:` / `follows_existing_pattern:` 声明 presence。"""
1391:    return bool(re.search(r"^(design_trivial|follows_existing_pattern):\s*\S", line))
```

```
$ grep -n "design_trivial\|follows_existing_pattern" agate/scripts/agate-frontmatter-check.py
35:            "internal_only_reason", "跳过风险", "design_trivial",
36:            "follows_existing_pattern", "need_confirm_resolved",
53:            "design_trivial": bool,
55:            "follows_existing_pattern": list,      ← ★ 确为 list
```

`agate-md-field-get.py` 的既有通道确实存在（实测）：

```
$ grep -n "design_trivial" agate/scripts/agate-md-field-get.py
87:BOOL_FIELDS = frozenset({"ui_affected", "internal_only", "design_trivial"})
230:    if op in ("internal_only", "design_trivial"):
231:        return _regex_scalar(text, re.escape(op) + r":\s*(true|false)")
```

**⇒ v2 引用的 `_regex_scalar(..., r"design_trivial:\s*(true|false)")` 逐字属实（L231）。**

#### ★ 我的反例尝试 1：`design_trivial: true  # 行尾注释` 能否解析出 `true`？

任务点名要求证伪这一点。**实测结论：能正确解析。**

真值表（`FILE=<f> python3 agate/scripts/agate-md-field-get.py design_trivial`）：

| fixture | frontmatter 解析 | `_get()` 输出 |
|---|---|---|
| `design_trivial: true  # 行尾注释` | `{'design_trivial': True}` | **`true`** ✅ |
| `design_trivial: true` | `{'design_trivial': True}` | `true` |
| `design_trivial: false  # 注释` | `{'design_trivial': False}` | `false` ✅ |
| （正文，非 frontmatter）`design_trivial: true` | 无该键 | `true`（走 regex 回退） |

**机理（实测区分两条通道）**：

```
$ python3 -c "... import agate-md-field-get ..."
f  fm= {'task_id': 'TAG9999', 'phase': 'P1', 'design_trivial': True}
   | _get= 'true' | regex_fallback= 'true'
```

**⇒ 点名的反例不成立**：行尾注释由 **YAML 解析通道**（`_read_frontmatter` → `yaml.safe_load`）
先处理掉了，`# 行尾注释` 在 YAML 里是合法注释 ⇒ 值为 `True`；即便落到 regex 回退通道，
`re.search(r"design_trivial:\s*(true|false)")` 是 **search 非 fullmatch**，`\s*(true|false)`
在 `true  # 注释` 上于 `true` 处即命中。**两条通道都正确。**

⚠️ **但这是"实测正确"，不是"设计写对了实现细节"**：v2 只写了"判 `== "true"`"，
**未写明注释处理**。鉴于本轮我实测两通道都通，此项可作为**实现时的回归用例**要求而非设计缺陷
（列入 §4 的 nit）。

#### ★ 我的反例尝试 2：`follows_existing_pattern` 的 presence 正则该长什么样？

任务要求给出**同时**兼容块列表与流式列表的正则。**v2 未给出确切正则**（只说"`\s*\S` 要求不适用于该键"）。
我实测了四个候选：

| 候选正则 | `key:`（块列表） | `key: [a, b]`（流式） | `key: []` | 误伤 `key_extra:` |
|---|---|---|---|---|
| **A** `^follows_existing_pattern:\s*(\S.*)?$` | ✅ True | ✅ True | ✅ True | ✅ False |
| **B** `^follows_existing_pattern:` | ✅ True | ✅ True | ✅ True | ✅ False |
| **C** `^follows_existing_pattern:\s*.*$` | ✅ True | ✅ True | ✅ True | ✅ False |
| D（第一轮建议）`^follows_existing_pattern:\s*$` | ✅ True | ❌ **False** | ❌ **False** | ✅ False |

**⇒ 第一轮报告 §2.X6 自己给的候选 D 是错的**（只兼容块列表，漏流式列表）；
**A/B/C 三者等价且都正确**。B 最简。**v2 未落定正则 ⇒ 实现者可能照抄 D 而漏掉流式列表。**
（列入 §3.4 新发现问题。）

#### ★ 端到端 gate 结果模拟（三种实现对比）

在 `mktemp -d` 一次性副本内构造 3 个任务并复现 `gate_p2` 的判定式（L870-876）：

```
TAG0018: legacy_declared=True  v2_declared=True   (legacy min=1, v2 min=1)
FAKE1:   legacy_declared=False v2_declared=True   (legacy min=2→红, v2 min=1)   ← 块列表-only 任务
FAKE2:   legacy_declared=True  v2_declared=False  (legacy min=1, v2 min=2)      ← false 假绿被修
```

| 任务 | 语义 | legacy | v2 | 判定 |
|---|---|---|---|---|
| TAG0018 | `design_trivial: true` + 块列表 | 声明 | 声明 | **不转红** ✅ |
| FAKE1 | **仅**块列表 `follows_existing_pattern:` | **漏认（假红）** | **认** | **修复反向缺陷** ✅ |
| FAKE2 | **仅** `design_trivial: false` | **误认（假绿）** | **不认** | **修复正向缺陷** ✅ |

**⇒ P0-1 判定：已修复。v2 的两键分离方案在源码语义与端到端结果上均正确，且同时修掉双向缺陷、
不制造存量转红。这是第一轮最强反对意见的完整闭合。**

**⇒ 存量范围复核**：`^\(design_trivial\|follows_existing_pattern\):` 形式**全仓仅 1 个任务**
（TAG0018），与 v2 的"1 个 `design_trivial`"吻合；另有 4 个文件仅在**正文/表格**里提到键名
（TAG0010/0022/0024/0031），**非声明行**，不受影响。
⚠️ **但 v2 写"3 个任务（1 个 design_trivial + 2 个 follows_existing_pattern）"不准确**——
见 §3.3。

---

### P0-2 — X1 改目标 + 第 4 批划界 + PAUSED 留痕：✅ **已修复**

**任务点名的三项，逐条核验**：

**① 目标改为"任务目录内"**（v2 L52-53）：
> **目标行为（修订）**：本批达成「**所有阶段的、任务目录内的**暂存 diff 都扫描」；
> `PAUSED` **只扫描不阻断**。

**② 真"所有文件"划入第 4 批**（v2 L54-56）：
> 真正"所有文件都扫描"须**放宽上面那层门控**——那是**扩大扫描面**，属**跨模块影响**，
> **明确划入第 4 批**（与外部设计分析 §2.4「每一次提交」行同源…）

**③ 边界声明**（§3 L346）：
> | **X1 的「非任务目录文件也扫」** | **第 4 批**——须放宽 L327 门控（扩大扫描面 = 跨模块影响）。本批只做到「所有阶段的**任务目录内** diff 都扫」 |

**源码核验（实测行号完全吻合）**：

```
$ grep -n "any(f.startswith(prefix) for f in _staged_name_only())" agate/scripts/pre-commit-gate.py
327:        if any(f.startswith(prefix) for f in _staged_name_only()):
$ grep -n 'if phase in ("PAUSED", "READY", "DONE")' agate/scripts/pre-commit-gate.py
320:        if phase in ("PAUSED", "READY", "DONE"):
```

**⇒ L320（`continue`）在 L327（门控）之前，两者都在 2g.1 扫描（L325+）之前；v2 对结构的描述准确。**

**④ PAUSED 分支留痕**（v2 L62-65）：
> **PAUSED 分支须留痕**（评审补充，我采纳）：…⇒ **须至少 `append_event` 或写账本 WARNING**，
> 否则等于"只打印到 stderr、无留痕"。

**⑤ 粒度（第一轮确认正确、v2 保留）**（v2 L58-60）："把 2g.1 整体上移"，不是"删掉 `continue`"。

**⇒ P0-2 判定：已修复。**三项要求（改目标 / 第 4 批划界 / PAUSED 留痕）全部落地，
V1 锚同步更新（L399 明写"**任务目录内**"+"PAUSED ⇒ 扫描 + 留痕但不阻断"）。

#### ★ 边界清晰性核验（任务要求）

**边界可执行吗？——是。** 判据是**机械的**：`prefix`（任务目录）vs 非 `prefix`。
本批 = 把 2g.1 上移到 L320 之前 ⇒ 覆盖「所有 phase × 任务目录内」；第 4 批 = 放宽 L327 的
`any(...)` 门控 ⇒ 覆盖「所有 phase × 全仓」。
⚠️ **但有一处未声明的重叠**：上移 2g.1 后，**L327 仍留着** ⇒ 本批结束时该 `if` 是
"半冗余"的（它保留的唯一作用是在**任务目录内无暂存文件**时跳过 `git diff` 调用）。
v2 未说明第 4 批是"删掉这个 if"还是"改判据"——**作为交接说明仍偏薄**，但**不影响本批可执行性**。

---

### P0-3 — X5 改 `set -o pipefail; ` 前缀 + 更正风险方向：✅ **已修复**

**v2 的修正**（L180-197）：
> **⚠️ 原设计的实现指引字面不可执行**（独立评审实测，我复核确认）：
> ```python
> subprocess.run(cmd, shell=True, executable="bash -o pipefail")
> # → FileNotFoundError: [Errno 2] No such file or directory: 'bash -o pipefail'
> ```
> `executable` 是**路径**，不接受命令行参数。**正确写法**（评审实测 rc 符合预期）：
> ```python
> cmd = "set -o pipefail; " + cmd          # ← 前缀方式
> ```

**源码核验**：

```
$ grep -n "shell=True" -B12 -A5 agate/scripts/agate_common.py
712:        proc = subprocess.run(
713:            cmd, shell=True, executable="bash",
714:            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
```

**⇒ 唯一 `shell=True` 站点属实；`executable="bash"` 属实。**

**风险方向更正**（v2 L194-197）：
> `pipefail` 影响 **`check-tdd-red.py` 的 P3 红灯语义**——那里「非 0 = 红灯 = 符合 TDD」，
> 加 pipefail 后**方向可能是放宽**（更容易判为红），而**不是**原设计写的"由绿转红"。

#### ★ 我的反例尝试 3：`set -o pipefail; ` 对已有 `set -e` 的影响 + P3 方向实测

任务要求"实测构造"。我做了两层：

**第一层：前缀写法的 rc 交互矩阵（实测）**

| 命令 | plain | `set -o pipefail; ` 前缀 | SHELLOPTS env |
|---|---|---|---|
| `echo hi` | 0 | 0 | 0 |
| `exit 3 \| tail -1` | **0** | **3** | 3 |
| `bash -c 'exit 5' 2>&1 \| tail -30` | **0** | **5** | 5 |
| **`set -e; false \| tail -1; echo after`** | **0** | **1** | 1 |
| **`set -euo pipefail; false \| tail -1; echo after`** | 1 | 1 | 1 |
| `set -e; echo hi \| tail -1; echo after` | 0 | 0 | 0 |
| **`set -e; exit 7 \| tail -1`** | **0** | **7** | 7 |
| `exit 9`（无管道） | 9 | 9 | 9 |
| `false \| true` | 0 | **1** | 1 |
| `(exit 4) \| tail -1` | 0 | **4** | 4 |

**⇒ 对"已有 `set -e` 的命令"会不会产生新问题？——不会产生新问题，反而修正一个既有漏洞。**
机理：**裸 `bash`（无 pipefail）下 `set -e` 对管道只看最后一段** ⇒ `set -e; false | tail -1`
里 `false` 的失败被 `set -e` **漏掉**（实测 rc=0）。加前缀后 `pipefail` 让管道整体 rc≠0，
`set -e` 随即生效（rc=1）。**这是修复，不是回归。**
⚠️ **一个真实的语义变化**：`set -e; false | tail -1; echo after` 加前缀后**不再执行 `echo after`**
（因 `set -e` 提前退出）。对本批的 21 条 piped 命令而言方向正确（fail-closed），
但**若某命令依赖"管道失败后继续"**，行为会变。**v2 未提这一点**（列入 §4 nit，风险低）。

**第二层：`check-tdd-red.py` 端到端方向实测（任务点名的"实测构造"）**

在 `mktemp -d` 一次性副本内：① 复制 `agate/`；② 用 `TEST_RUNNER` 喂可控命令；
③ 记录打补丁前/后的 rc。

```
########## CURRENT (no pipefail) ##########
--- FAIL masked by | tail ---
    TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests
    >>> rc=2
--- PASS | tail ---
    TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests
    >>> rc=2
--- FAIL no pipe ---
    TDD_CHECK: red-light (unexpected test failure)
    >>> rc=0
--- PASS no pipe ---
    TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests
    >>> rc=2

########## PATCHED (set -o pipefail; prefix) ##########
--- FAIL masked by | tail ---
    TDD_CHECK: red-light (unexpected test failure)
    >>> rc=0                                    ← ★ 2 → 0
--- PASS | tail ---
    TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests
    >>> rc=2                                    ← 不变
--- FAIL no pipe ---
    TDD_CHECK: red-light (unexpected test failure)
    >>> rc=0                                    ← 不变
--- PASS no pipe ---
    TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests
    >>> rc=2                                    ← 不变
```

对照 `judge_result`（`check-tdd-red.py:106-108`）：

```python
    if exit_code == 0:
        print("TDD_CHECK: tests pass, no red-light — implementation may be ahead of tests")
        return 2                      # ← 2 = FAIL（"实现跑到测试前面了"）
```

**⇒ 实测裁定：P3 方向确为「放宽」，v2 的更正正确。**
被管道掩盖的失败从 `rc=2`（P3 判 FAIL）变成 `rc=0`（P3 判 PASS）——即
**pipefail 让 P3 的红灯判定更容易通过**。原设计说的"由绿转红"对 P3 消费方**方向相反**。

**⇒ P0-3 判定：已修复**（写法已改对、方向已更正且经我端到端实测确认）。
⚠️ **但存量风险数字不实**——见 §3.1，这是本轮最重要的新发现。

---

### P1-1 — X2 调用点 4→2（L257 + L590）：✅ **已修复**

**v2 的修正**（L79-82）：
> **⚠️ 原设计称"4 个调用方"不实**（独立评审核验，我采纳）：
> 实测生产调用点**只有 2 个**——`pre-commit-gate.py` 的 **L257 与 L590**
> （`agate-advance.py:76` 是同名**本地**函数、`agate-next.py:52` 只 import 未调用）。
> ⇒ **两个调用点都要改**；只改 L257 会让**同一次 commit 内两处 phase 来源不一致**。

**源码核验（实测，逐字吻合）**：

```
$ grep -n "read_state_phase" agate/scripts/pre-commit-gate.py agate/scripts/agate-advance.py agate/scripts/agate-next.py
agate/scripts/pre-commit-gate.py:23:复制模式 .agate-root 恢复）；write_gate_result / read_state_phase / read_state_task_id /
agate/scripts/pre-commit-gate.py:50:        read_state_phase,
agate/scripts/pre-commit-gate.py:257:        phase = read_state_phase(state_file)          ← 调用点 ① ✅
agate/scripts/pre-commit-gate.py:590:        task_phase = read_state_phase(task_state)     ← 调用点 ② ✅
agate/scripts/agate-advance.py:76:def _read_state_phase(task_dir):                  ← 同名本地函数 ✅
agate/scripts/agate-next.py:52:        read_state_phase,                             ← 仅 import ✅
```

**⇒ L257 / L590 两个调用点、`agate-advance.py:76` 同名本地函数、`agate-next.py` 仅 import——四条全对。**

**新增函数尚未实现**（预期内，设计未实现）：

```
$ grep -rn "read_staged_state_phase" agate/
（无输出）
```

相关问题（**我实测发现，第一轮未提**）：既有 `has_staged_phase_change`（`agate_common.py:602-618`）
已经在做"暂存区 phase"判定，新函数 `read_staged_state_phase` 与它**判据相邻**
（前者判"有无 phase 变更"，后者取"暂存区的 phase 值"）。v2 未说明二者关系，
实现时有"同一概念两处实现"的漂移风险。**⇒ 列入 §4 nit。**

⚠️ **第一轮 P1-4 要求的"暂存区读取失败的回退语义"，v2 未补**（L89 只写"风险"，
未定义 `git show :<path>` 失败时是回退工作区还是报错）。**⇒ 未闭合项，见 §3.5。**

---

### P1-2 — X4 补 audit7 消费方 + 更正风险方向 + 别名词表：⚠️ **部分修复**

| 子项 | v2 处理 | 判定 |
|---|---|---|
| 补 P8 卡片 audit7 消费方 | L156-158：明写 `--audit7-only` CLI 被 `P8-release.md:84-88` 消费 ⇒ 改变 `AUDIT7_RESULT` 三态 | ✅ **已修复** |
| 更正风险方向 | L160-161："放宽识别 ⇒ 更多行被判为已声明复用 ⇒ audit7 更可能判 `reuse_blocked` ⇒ **是更多拦截，不是更多通过**" | ✅ **已修复** |
| 补别名词表 | L163-164：**"须补"别名词表**：哪些英文写法算声明（原设计只说"三种写法"，未定义词表） | ❌ **仍是待办，未给词表** |

**源码核验**：

```
$ sed -n '170,190p' agate/scripts/check-p6-provenance.py
def p6_declares_reuse(task_dir):
    """P6-acceptance.md 是否声明"引用 P5 证据、不重跑"（M21 落地的产出规格判定）。"""
    ...
    return bool(re.search(r"引用\s*P5\s*证据", text))
```

```
$ sed -n '82,95p' agate/phase-cards/P8-release.md
  跑 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`，读 stdout 的
  `AUDIT7_RESULT: <reuse_allowed|reuse_blocked|no_reuse_claim_possible>` 行判定：
  - `AUDIT7_RESULT: reuse_allowed`（exit 0）→ 复用同一份 `P5-test-results/`（不重新执行命令）
  - `AUDIT7_RESULT: reuse_blocked`（exit 1）或 `no_reuse_claim_possible`
    （exit 0 但结果非 reuse_allowed）→ 完整重跑 `gate_commands.P5`（exit 0 + failed==0）
```

**⇒ 消费链属实，v2 引用准确。**

**⚠️ 未闭合**：第一轮要求"**须在设计中列出确切的别名集合，或改判为「结构化字段 + 中文短语」两项**"。
v2 只是把要求**抄进设计**（"须补'别名词表'"），**没给出词表本身**。
⇒ **V4 锚仍不可机械校验**（"三写法都认"仍是关键词判定）。**这是"把待办写成设计条款"，
不是"完成待办"。**

---

### P1-3 — X7 三方一致 + 37/37 ⇒ 转红 0：✅ **已修复**

**v2 的处理**（L267-275）：
> **补强论据（评审给出，我采纳）**：`exit 2` 在该 returning site **确凿就是通过码**，三方一致：
> - `phases.yaml` P2 声明 `gate_pass_exit: 2`；
> - `check-gate.py` 头部：「exit 2 = 多数 phase 正常通过码」；
> - `adr.md` 同口径。

**源码核验**：

```
$ sed -n '885,900p' agate/scripts/check-gate.py
    agent = _md_field_get("agent", p2_review)
    if not agent:
        sys.stderr.write("GATE P2: P2-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
        return 2                                        ← 通过码
    if agent == "main":
        sys.stderr.write("GATE P2: P2-review.md status:approved 但 agent=main（主 Agent 不可自行批准评审）\n")
        return 1                                        ← 阻断
```

```
$ grep -n "gate_pass_exit" agate/rules/phases.yaml
32:    gate_pass_exit: 2      ← P0
46:    gate_pass_exit: 2      ← P1
61:    gate_pass_exit: 2      ← P2 ★
...
```

**⇒ P2 `gate_pass_exit: 2` 属实；`return 2` = fail-open 放行属实；"缺字段（通过）比 `agent: main`（阻断）
更易绕过"的强弱倒挂属实。**

**存量扫描（我独立复跑，逐字吻合）**：

```
$ for f in agate-workspace/tasks/*/P2-review.md; do ... if ! grep -qE "^agent:\s*\S" "$f"; then ...; fi; done
P2-review total=37 missing_agent=0
```

**⇒ 37/37 齐备，missing=0 ⇒ 转红数 = 0，无需迁移期。v2 引用的数字属实。**
（第一轮 §7.2 的推断 #1「未实跑 `agate-next` 端到端」在本轮**仍为推断**——见 §5.2。）

---

### P1-4 — X9 更正理由 + DEBT0013 + "22/38"：✅ **已修复**

**v2 的三处修正**：

| 子项 | v2 处理 | 判定 |
|---|---|---|
| 更正"不改 agate-next"的理由 | L323-324："原设计的理由打空靶……实测 `agate-next` **本就无"预写 READY"行为**（其文件头明写：phase ∈ {PAUSED, READY, DONE} → 提示不推进）" | ✅ |
| 补 DEBT0013 时序 | L332："另漏 `P8-release.md:89-93` 的 DEBT0013 时序说明（CHECK 7 相关），改卡片时须一并核对" | ✅（**列为待核对**，非给出结论） |
| 措辞"22/38 从未以 P8 提交" | L329-330："另：`38/16` 的「gate_p8 从不运行」**措辞过强**……准确表述：**22/38 个任务从未以 P8 提交**" | ✅ |

**源码核验（实测）**：

```
$ sed -n '1,20p' agate/scripts/agate-next.py
语义（消费 check-gate.py exit 三态 + phases.yaml gate_pass_exit，不改 gate 返回约定；BDD-13）：
  * .state.yaml phase ∈ {PAUSED, READY, DONE} → 提示不推进，exit 0
...
$ grep -n "_TERMINAL_PHASES = " agate/scripts/agate-next.py
66:_TERMINAL_PHASES = {"PAUSED", "READY", "DONE"}
```

**⇒ "`agate-next` 本就无预写 READY 行为"属实**——它把终态 phase 视为"不推进"，不会去写 READY。

**`22/38` 统计独立复现（实测，逐字吻合）**：

```
$ n=0; p8=0; for f in $(git ls-tree -r --name-only HEAD | grep "tasks/[^/]*/\.state\.yaml$"); do
    ph=$(git show HEAD:$f | grep "^phase:" | head -1 | awk '{print $2}')
    case $ph in READY|DONE) n=$((n+1)); git log --follow -p --format= -- $f | grep -qE "^\+phase: *P8" && p8=$((p8+1));; esac
  done; echo "$n $p8"
READY_DONE=38 P8_EVER=16  NEVER_P8=22
```

**⇒ 38/16 ⇒ NEVER=22 精确复现。**

**DEBT0013 原文核实**（`P8-release.md:89-93`）：

```
   - **⚠️ 时序注意（DEBT0013）**：若 `gate_commands.P5` 的链路包含
     `check-protocol-consistency.py` 的 CHECK 7（README version badge 与最新 git tag 一致性），
     P5 重跑应安排在 **commit + 创建 git tag 之后** 进行…
```

**⇒ 该节确实存在，且正是 X9 改动会触及的时序。**
⚠️ **v2 只说"须一并核对"，未给出核对结论**（第一轮要求"至少写明不受影响的依据"）。
**⇒ 半闭合**：义务已登记，**结论缺位**。

**V9 机械判据**（L407）：
> 卡片改为「以 `phase: P8` 提交产出、再单独提交 READY」；并核对 `:89-93` 的 DEBT0013 时序；
> **断言无脚本依赖"以 READY 提交"**（可机械：grep）

**⇒ 已按第一轮要求改为可机械校验形态。**我实测该 grep 方向：`agate/scripts/*.py` 中
`READY` 的 13 处命中**全部是"把 READY 当终态跳过"**（`pre-commit-gate.py:320`、
`ci-gate-backstop.py:145`、`agate-next.py:8/66/416` 等），**无一处要求"以 READY 提交"**
⇒ **"无脚本依赖"成立**。

---

### P1-5 — X3 补第三个 SKIP 面：⚠️ **修复不完整**

**v2 补的面**（L133）：
> | **phase ∈ PAUSED/READY/DONE** | `return 0`（**第三个 SKIP 面，原设计漏了**） | 同上（显式 WARNING） |

**源码核验（实测）——`ci-gate-backstop.py` 的 `return 0` 面远不止 3 个**：

```
$ grep -n "print(\"SKIP\|return 0" agate/scripts/ci-gate-backstop.py
124:        print("SKIP: 未识别的 CI 平台（非 Gitea/GitLab/GitHub），backstop 不生效")   ← 面①
125:        return 0
132:        print("SKIP: 无 .state.yaml，非 agate 项目")                                  ← 面②
133:        return 0
142:        print("SKIP: 无法读取 .state.yaml")                                          ← 面③ ★未列
143:        return 0
147:        return 0                                                                     ← 面④（phase 面）★已列
162:            print("SKIP: refactor 任务，TDD 红灯不适用（回归口径由 P5/P6 全量回归兜底）") ← 面⑤ ★未列
163:            return 0
197:        return 0                                                                     ← 面⑥（正常 PASS？）
284:    return 0                                                                         ← 主出口
```

**⇒ 同族"假绿"面实际有 5 个以上**（①②③④⑤），v2 只列了 ①②④。
特别是 **面③「无法读取 `.state.yaml`」**（L142-143）与 **面⑤「refactor 任务跳过」**（L162-163）
**同样是 `SKIP:` + exit 0**，与面②**形态完全一致**，却被 v2 的表漏掉。

**⇒ 判定：修复不完整。**第一轮说"漏了第三个 SKIP 面"，v2 补了第④面，
**但同一形态的第③⑤面仍漏**。⇒ **本项未真正闭合**（见 §3.2）。

⚠️ **另**：第一轮还要求 **V3 判据加强为"输出结构变化"**（加速度负向控制）。
v2 的 V3（L401）仍是：
> 无 `.state.yaml` 时：**exit 0 不变**（保 required check）+ 输出含 **WARNING** 与"backstop 未生效"字样

**⇒ 仍是第一轮批评的"关键词匹配，不是行为判据"。V3 未按 P1-5 要求加强。**

---

### P1-6 — X8 具体化 readlink + 并入第 10 项：✅ **已修复**

**v2 的处理**（L293-300）：
> **实现（评审给出最简做法）**：软链备份即 `os.readlink(hook_file)` 一行，记录**链接目标**
> （**不是**复制内容——复制软链内容无意义）。
> **⚠️ 同函数另有一个更严重的缺陷（评审建议并入本批，我采纳为第 10 项）**：
> `_backup` 用 `os.path.isfile(hook_file)` 作前置条件 ⇒ **悬空软链（dangling symlink）
> `isfile` 为 False** ⇒ **既不备份**，又被后续 `os.unlink` **删除** ⇒ **静默丢失**。

#### ★ 我的反例尝试 4：核实 `install-hook.py` 的实际代码路径（任务点名）

**源码**（`install-hook.py`）：

```python
def _ln_sf(source, link_path):
    if os.path.lexists(link_path):              # ← ★ 用 lexists，不是 isfile
        with contextlib.suppress(OSError):
            os.unlink(link_path)
    ...

def _backup(hook_file, label):
    """已有非软链 hook → 备份为 {hook_file}.bak.{epoch}（cp 语义，sh set -e 下失败即退）。"""
    if os.path.isfile(hook_file) and not os.path.islink(hook_file):
        backup = hook_file + ".bak." + str(int(time.time()))
        shutil.copyfile(hook_file, backup)
        print(f"已备份现有 {label} hook")
```

**Python 语义实测（`mktemp -d` 一次性副本）**：

```
--- dangling symlink ---
lexists : True
isfile  : False
islink  : True
_backup condition (isfile and not islink) -> False

--- valid symlink ---
lexists : True
isfile  : True
islink  : True
_backup condition -> False
```

**⇒ v2 对第 10 项的描述「既不备份，又被后续 `os.unlink` 删除」——准确。**逐环节验证：

1. **不备份**：`isfile` 对悬空软链返回 `False` ⇒ `_backup` 的 `if` 不成立 ⇒ 无 `.bak` 产生。✅
2. **被 `os.unlink` 删除**：`_ln_sf` 用 **`os.path.lexists`**（对悬空软链返回 `True`）
   ⇒ 进入 `os.unlink(link_path)` ⇒ **悬空软链被删**。✅
3. **静默**：两者都无输出（`_backup` 无匹配即无 print；`os.unlink` 静默成功）。✅

**⇒ 描述准确，机制成立。**（⚠️ 精确措辞：删除者是 **`_ln_sf` 的 `os.unlink`**，
v2 写"后续 `os.unlink`"未点名是哪个函数——**指的是对的**，因 `_backup` 自身不含 `unlink`。
列为 §4 nit。）

**⇒ P1-6 判定：已修复。**`os.readlink` 已具体化（L293），第 10 项已并入（L296-300），
V8 锚同步（L406）。**我独立实测确认其描述的代码路径准确——这是第一轮 §7.2 推断 #5
（"未实跑 install-hook"）的闭合**：本轮虽仍未实跑端到端 `install-hook.py`（会写真实仓库），
但**逐条复现了其判定所依赖的全部 Python 语义**，推断升级为实测。

---

### P2-1 — 声明实现基线（f5e4c31 → fa2fc3d）：⚠️ **修复不当**

**v2 的声明**（L6-8）：
> **事实基线**：main `4daa60b` 之后 ｜ **设计基线**：`fa2fc3d`
> （⚠️ 独立评审指出：设计曾有两个版本 `f5e4c31` → `fa2fc3d`，**实现须以本版为准**；
> 本文已按评审的 P0/P1/P2 清单全部修订）

**问题**：本行把"设计基线"写成 `fa2fc3d`，**但被评审对象/本文件本身是 `05edb02`**
（`fa2fc3d` 的前一个 commit 的**后继**）：

```
$ git log --oneline -3 05edb02
05edb02 design(TAG0042-批0): 按独立评审的 P0/P1/P2 清单全部修订（NEEDS-REVISION → 待复审）
fa2fc3d design(TAG0042-批0): 更正 X7——问题不是「与 P1 不一致」而是「返回了通过码」
f5e4c31 design(TAG0042-批0): 9 个「现在就是错的」缺陷修复设计（待独立评审）
```

**⇒ 第一轮 P2-1 的诉求是"消除两版歧义、明确以哪版为准"。v2 的写法把歧义从
`f5e4c31 vs fa2fc3d` 平移成 `fa2fc3d vs 本文件`——歧义未消除，只是换了个位置。**
"实现须以本版为准"这句**语义上是清楚的**（"本版"= 读到的那份），
但 **`设计基线: fa2fc3d` 这个字面值与"本版"自相矛盾**（本版 ≠ `fa2fc3d`）。
⇒ **判定：修复不当**（意图达成，字面未达成，且对机械校验不友好——无法用它锚定 sha）。
**应改为：`设计基线: 05edb02（sha256 5407140d…）`。**（§3.6）

---

### P2-2 / P2-4 / P2-5 / V 锚：✅ **均已修复**

| 项 | v2 位置 | 核验 |
|---|---|---|
| P2-2 X1 与第 4 批边界 | §3 L346 + §1 L54-56 | ✅ 与 X9/第 1 批的声明形式**同构**（§3 L348 明写"X9 声明了"、§3 L350 补方法要求） |
| P2-4 V10 判据强度 | §4.2 L388-391 | ✅ 三分归因（①真违规 / ②有意收紧且已登记 / ③存量数据缺陷登记为债务），**凡不能归入者不得合并**——**可机械裁定** |
| P2-5 self-gate-review 留痕 | §6 L424 | ✅ "提交信息必须带 `self-gate-review:` 路径或 `self-gate-skip:` 理由" + 明写"**原设计漏了这条义务**" |
| V1 | L399 | ✅ 已含"**任务目录内**" + PAUSED 留痕 |
| V5 | L403 | ✅ 已含"写作 `set -o pipefail; cmd \| tail`（**不是** `executable="bash -o pipefail"`）" + "并验证 P3 红灯语义方向" |
| V6 | L404 | ✅ 已含"两键分别处理"+ 块列表算已声明 |
| V8 | L406 | ✅ 已含"记录 `readlink` 目标"+ 悬空软链第 10 项 |
| V9 | L407 | ✅ 已改为可机械 grep 的形态 |
| V3 | L401 | ⚠️ **未加强**（仍为关键词判据，见 P1-5） |
| V4 | L402 | ⚠️ **仍不可机械校验**（无词表，见 P1-2） |

---

## 2. 我的反例尝试汇总（含未成功的）

| # | 攻击点 | 结果 | 证据 |
|---|---|---|---|
| 1 | X6：`design_trivial: true  # 注释` 能否解析出 `true`？ | **攻击失败**——两通道（YAML / regex search）都正确 | §1.P0-1 真值表 |
| 2 | X6：`follows_existing_pattern` presence 正则该用哪个？ | **攻击成功（针对第一轮建议）**——第一轮给的候选 D **漏流式列表**；A/B/C 才对。v2 未落定正则 ⇒ 实现风险 | §1.P0-1 候选表 |
| 3 | X5：`set -o pipefail; ` 对已有 `set -e` 是否引入新问题？P3 方向？ | **部分成功**——对 `set -e` **不引入新问题**（反而是修复）；P3 方向**实测确为放宽**（`rc=2`→`rc=0`），v2 更正正确。但发现 `set -e; … \| …; echo after` 的**提前退出语义变化**未登记 | §1.P0-3 矩阵 + 端到端 |
| 4 | X8 第 10 项：悬空软链描述准确吗？ | **攻击失败**——描述**完全准确**，`lexists`/`isfile` 语义逐条复现 | §1.P1-6 |
| 5 | X5 存量："107 条中仅 1 条含管道"？ | **★ 攻击成功（本轮最重要新发现）**——实测 **315 条中 21 条含管道** | §3.1 |
| 6 | X6 存量："3 个任务"？ | **攻击成功**——实际 `^key:` 声明形式**仅 1 个任务**；另 4 个文件只是正文提及 | §3.3 |
| 7 | X3：SKIP 面只有 3 个？ | **攻击成功**——实测 ≥5 个 | §3.2 |
| 8 | X1：边界是否清晰可执行？ | **基本通过**，但 L327 的"半冗余"归属未写明 | §1.P0-2 |

---

## 3. 新引入的问题 / 未闭合项

### 3.1 ★ X5 的存量扫描数字**严重不实**（本轮最重要发现）

**v2 声称**（§4.2 L384）：
> | X5 | `grep -c '\|' agate-workspace/tasks/*/P2-design.md` 的 `gate_commands` | ✅ **107 条中仅 1 条含管道**（TAG0003 `2>&1 \| tail -30`）⇒ 风险 ≈ 0 |

**我的实测（用仓库自己的解析器 `agate_common.parse_gate_commands_block`，即唯一权威判据）**：

```
$ (逐 P2-design.md 调 parse_gate_commands_block)
total gate_commands entries: 315
with pipe: 21
   TAG0003-workspace-architecture   P5 :: "bats --formatter tap ... 2>&1 | tail -30"
   TAG0010-python-migration         P5              :: "... 2>&1 | tail -30"
   TAG0010-python-migration         P5_consistency  :: "python3 .../check-protocol-consistency.py --strict 2>&1 | tail -20"
   TAG0010-python-migration         P5_ruff         :: "ruff check agate/scripts/ 2>&1 | tail -20"
   TAG0010-python-migration         P5_scan         :: "python3 .../check-platform-assumptions.py 2>&1 | tail -20"
   TAG0010-python-migration         P5_ci           :: "python3 .../ci-gate-backstop.py 2>&1 | tail -20"
   TAG0011-test-migration           P5_consistency / P5_ruff / P5_scan / P5_ci   （同上 4 条）
   TAG0025-agateon-rename           P5_bdd1_readme_en / P5_bdd2_readme_zh / P5_bdd4to8 / P5_bdd9 /
                                    P5_bdd10 / P5_bdd12×2 / P5_bdd13 / P5_bdd14 / P5_bdd15×2 （11 条）
```

**⇒ 实测 315 条 / 21 条含管道，而非 v2 的「107 条 / 1 条」。**

**这 21 条真的会掩盖失败吗？——实测会**：

| 真实命令形态 | plain rc | `set -o pipefail` rc | 结论 |
|---|---|---|---|
| `check-protocol-consistency.py --strict 2>&1 \| tail -20`（失败） | **0** | **1** | 失败被掩盖 |
| `ruff check 2>&1 \| tail -20`（失败） | **0** | **1** | 失败被掩盖 |
| `ci-gate-backstop.py 2>&1 \| tail -20`（失败） | **0** | **1** | 失败被掩盖 |
| `bats … 2>&1 \| tail -30`（失败） | **0** | **1** | 失败被掩盖 |

**⇒ 这些正是 TAG0016 教训的同型案例，且比 v2 承认的多 20 倍。**

**但是否真会"转红"？——关键限定（我实测确定）**：

1. `check-tdd-red.py` 只消费 **`P3` 键**（`agate-read-gate-commands.py` 的循环里
   `elif key == "P3"` 是唯一产出 command 的分支）⇒ **只有 P3 进 `run_test_with_formatter`**。
   实测：**37 个任务的 P3 命令中，含管道者 = 0**：

   ```
   $ grep -rn "^  P3:" agate-workspace/tasks/*/P2-design.md | grep -c "|"
   0
   ```

2. `agate-capture-env-baseline.py` 消费 **`P5*` 键**（`READ_P5`），**是**这些 piped 命令的
   真实执行者——**但实测这 21 条的 formatter 全为空**：

   ```
   （21 条 piped 条目，fmt='' 全部为空）
   仓库 P5_formatter 声明总数 = 4（且不覆盖这 21 条）
   ```

   而 `capture-env-baseline` 对无 formatter 的命令**直接放弃、不执行**：
   ```python
   if not fmt_path:
       sys.stderr.write(f"ENV_BASELINE: 命令 '{cmd}' 无 formatter，无法提取 fail-list，放弃捕获，不写入任何文件\n")
       parse_ok = False
       break
   ```

3. `gate_p5` **不执行** P5 命令，只计数 + WARN（`check-gate.py:1081-1091`）。

**⇒ 结论（我的裁定）**：
- **v2 的最终结论（"转红风险 ≈ 0"）在事实上仍然成立**——但**不是因为它说的理由**。
  它说"107 条中仅 1 条含管道"；真实理由是"**21 条含管道的命令恰好都无 formatter +
  不在 P3 键上，因而逃过执行**"。**这是两个完全不同的论证**，后者才是可辩护的。
- **v2 的扫描命令本身不实**：`grep -c '|' … P2-design.md` 数不出 315/21
  （且 `grep -c` 按**文件**计数、不解析块结构）。**该行是"声称-命令绑定"（A8）不合格**：
  它给出的命令**跑不出**它给的数字。
- **风险面被低估**：一旦将来有任务给 `P5_*` 命令配 formatter，或 P3 命令引入管道，
  这 21 条形态就会**按 X5 的预期转红**（对 P5 是收紧——正确方向；对 P3 是放宽——需评估）。
  **v2 未提示这个条件性风险。**

⚠️ **对第一轮的更正**：第一轮 §2.X5 与 §4 也写了"107 条中仅 1 条含管道"。
**我复核发现该数字用不同口径复现不出**（若按"含顶层 `P5` 键的行数"或某种过滤可能得 107，
但**按仓库自己的解析器口径是 315/21**）。**第一轮报告在这一点上也不准确，本轮据实更正。**

### 3.2 X3 的 SKIP 面仍漏（第一轮意见未真正闭合）

见 §1.P1-5。实测 `ci-gate-backstop.py` 有 **≥5 个** `SKIP:` + `return 0` 面，
v2 只列 3 个，**同形态的面③（无法读取 `.state.yaml`，L142）与面⑤（refactor 任务，L162）被漏**。
**⇒ 这些面同样"exit 0 且与 PASS 无法区分"，按 v2 自己的论证都应纳入"让未生效醒目可见"。**

### 3.3 X6 的存量数字不准确

**v2 声称**（§4.2 L385）：
> ✅ **3 个任务**（1 个 `design_trivial` + 2 个 `follows_existing_pattern`）⇒ 逐个核对

**我的实测**：

```
$ grep -rlE "^(design_trivial|follows_existing_pattern):" agate-workspace/tasks/*/P1-requirements.md
agate-workspace/tasks/TAG0018-dsh-platform/P1-requirements.md      ← 唯一 1 个

$ grep -rn "design_trivial\|follows_existing_pattern" agate-workspace/tasks/*/P1-requirements.md
（5 个文件命中，但除 TAG0018 外均为正文/表格提及，非声明行）
  TAG0010:182  表格里的说明文字
  TAG0018:16,17,215   ★ 真声明（+ 1 处正文引用）
  TAG0022:99    表格：列出正则清单
  TAG0024:54,55,67  文档：描述 BOOL_FIELDS/LIST_FIELDS
  TAG0031:195   正文：列举函数名
```

**⇒ 按"声明行"口径是 1 个任务，按"文件提及"口径是 5 个，v2 的"3 个"两种口径都对不上。**
**且 v2 未指出 TAG0018 的 `follows_existing_pattern:`（L17）与 `design_trivial: true`（L16）同文件**——
这正是第一轮反例的核心，v2 在 §X6 L219-222 **提到了**，但 §4.2 的扫描表**没体现**。
⇒ **数字口径不明确 + 与 §X6 不一致。**

### 3.4 `follows_existing_pattern` 的 presence 正则未落定（实现风险）

v2 L229 只说"正则的 `\s*\S` 要求**不适用于该键**"，**未给出替代正则**。
第一轮 §2.X6 给的候选 `^follows_existing_pattern:\s*$` **实测漏流式列表**（见 §1.P0-1 表）。
⇒ **实现者若照抄，会漏 `follows_existing_pattern: [a, b]` 形态**（虽当前存量无此形态，
但这是"合法声明不被识别"的反向缺陷复发）。
**建议在设计中写死：`re.match(r"^follows_existing_pattern:", line)`（候选 B，最简且实测正确）。**

### 3.5 X2 的暂存区读取失败语义仍未定义（第一轮 P1-1 第 3 点未闭合）

v2 §X2 只写"风险：新增函数须与既有 `read_state_phase` 语义一致（除数据来源外）"，
**未定义 `git show :<path>` 失败（文件未在 index / 路径含空格 / index 锁定）时的回退**。
第一轮明确要求"明确『暂存区读取失败 → 回退工作区 + 打 WARNING』并**给测试**"。
⇒ **未闭合。**

### 3.6 实现基线字面值自相矛盾（见 §1.P2-1）

---

## 4. Nits（不阻塞，建议实现时一并处理）

| # | Nit | 建议 |
|---|---|---|
| N1 | X6 未写明 `design_trivial: true  # 注释` 的处理 | 我实测两通道都通；**请把该形态写成回归用例**（带注释 / 无注释 / `false`+注释 三态） |
| N2 | X5 未登记 `set -e; … \| …; echo after` 的提前退出语义变化 | 在 §X5 加一句：加前缀后 `set -e` 会对管道整体生效，尾部命令可能不再执行 |
| N3 | X8 未点名删除者是 `_ln_sf` 的 `os.unlink` | 改为"被后续 **`_ln_sf`** 的 `os.unlink` 删除"（现状"后续 `os.unlink`"指代正确但不精确） |
| N4 | X2 未说明新函数与既有 `has_staged_phase_change`（`agate_common.py:602`）的关系 | 明确二者判据分工，防"同一概念两处实现"漂移 |
| N5 | §3 L346-347 有**重复行** | 「X2 的『按提交类型分级』」在 §3 表中**出现两次**（L343 与 L347），删一行 |
| N6 | X1 未写明第 4 批如何处理 L327 的"半冗余" `if` | 加一句交接说明（删掉 vs 改判据） |

---

## 5. 已实测 vs 推断（严格区分）

### 5.1 **已实测**（命令/输出见本报告）

| # | 内容 |
|---|---|
| 1 | 文件 sha256：工作区 == `05edb02` == `5407140d…`；三版哈希（`f5e4c31`/`fa2fc3d`/`05edb02`） |
| 2 | X6 `design_trivial_declared` 正则；`agate-frontmatter-check.py:53/55`（bool / **list**）；`agate-md-field-get.py:87/230-231` |
| 3 | **X6 `design_trivial: true  # 注释` ⇒ `md-field-get` 输出 `true`**（YAML 通道 + regex search 通道都验证）；`false`+注释 ⇒ `false` |
| 4 | **X6 presence 正则四候选真值表**：A/B/C 正确、**第一轮候选 D 漏流式列表** |
| 5 | **X6 端到端 gate 模拟三任务**：TAG0018 不转红、FAKE1 修假红、FAKE2 修假绿 |
| 6 | X6 存量：`^key:` 声明形式**仅 TAG0018**；提及形式 5 文件 |
| 7 | X1 `pre-commit-gate.py:320`（`continue`）与 `:327`（门控）行号与相对位置 |
| 8 | X2 调用点 **L257 + L590**；`agate-advance.py:76` 同名本地函数；`agate-next.py:52` 仅 import；`read_staged_state_phase` 尚不存在 |
| 9 | X3 `ci-gate-backstop.py` 的 SKIP/`return 0` 面 **≥5 个**（L124/132/142/147/162/197/284） |
| 10 | X4 `check-p6-provenance.py:184` 单一中文正则；`P8-release.md:84-88` audit7 消费链 |
| 11 | X5 唯一 `shell=True` 站点 `agate_common.py:713`；**前缀写法的 10 例 rc 交互矩阵（含 `set -e` 组合）** |
| 12 | **X5 P3 端到端方向实测：`rc=2`（FAIL）→ `rc=0`（PASS）= 放宽**；对照 `judge_result:106-108` |
| 13 | **X5 存量：解析器口径 315 条 / 21 条含管道**；P3 键含管道 = **0**；21 条 formatter 全空 |
| 14 | X7 `check-gate.py:891-897`（`return 2` / `agent=main` ⇒ `return 1`）；`phases.yaml:61` P2 `gate_pass_exit: 2` |
| 15 | X7 存量：**P2-review 37 个，missing agent = 0** |
| 16 | X8 `install-hook.py` 的 `_backup`（`isfile and not islink`）与 `_ln_sf`（**`lexists`** + `os.unlink`） |
| 17 | **X8 悬空软链 Python 语义**：`lexists=True` / `isfile=False` / `islink=True` ⇒ 不备份且被删（描述准确） |
| 18 | X9 P8 卡 L15 原文；`agate-next.py:8/66`（终态不推进）；**READY_DONE=38 / P8_EVER=16 / NEVER=22 复现** |
| 19 | X9 `P8-release.md:89-93` DEBT0013 原文存在；`agate/scripts/*.py` 中 `READY` 命中共 13 处，**无一处要求"以 READY 提交"** |
| 20 | V3 仍为关键词判据；V4 仍无词表；V1/V5/V6/V8/V9 已按新方案改写 |

### 5.2 **推断**（未实测，须后续验证）

| # | 推断 | 置信度 |
|---|---|---|
| 1 | 把 2g.1 整体上移后，2h–2o 各检查行为不变 | 高（第一轮已论证粒度正确），**本轮未跑端到端 hook** |
| 2 | `agate-next.py` 在 `gate_p2` 返回 1 时会走 retreat 分支 | 高（源码 `pass_set` 语义 + YAML 注释），**未实跑** |
| 3 | X4 放宽 ⇒ audit7 更多判 `reuse_blocked` ⇒ P8 分支改变 | 中（**未跑 `--audit7-only` 构造用例**） |
| 4 | X9 改卡片后，`phase: P8` 提交时 tag 尚未创建的时序**不受影响** | 中（v2 未给结论，**我亦未构造**） |
| 5 | X3 的 21 条 piped P5 命令**将来**配 formatter 后会按预期转红 | 中（据当前 formatter 空值推断其"现在不会"） |

### 5.3 未能完成 / 未做的事项（如实上报）

- **未跑全量 pytest**（按纪律要求）。
- **未实跑 `pre-commit-gate.py` / `install-hook.py` 端到端**（会写真实仓库/账本/git hook）。
  X1 的门控与 X8 的备份路径通过**逐条复现其判定所依赖的语义**验证，非端到端。
- **未做 X4 的 `--audit7-only` 构造用例**（§5.2 推断 #3 仍为推断）。
- 所有 scratch 探针均在 `mktemp -d` 一次性副本内「建→用→清」同一 bash 调用完成
  （含 X5 的 `check-tdd-red` 端到端补丁测试、X6 的 gate 模拟、X8 的软链语义）。
- **本报告未改动工作区任何文件**；未执行任何写仓 git 命令；未切换分支。

---

## 6. 总体判定

### **`NEEDS-REVISION`**

**⇒ 能否开始实现：`基本可以，但建议先做一次小修订`。**

**判定理由**：

**✅ 三个 P0 全部真实闭合，且经我独立实测确认**——这是本轮的主要结论：

1. **P0-1（X6）**：v2 的"两键分别处理"经我**端到端 gate 模拟**验证为**正确**
   （修双向缺陷、不制造存量转红）；任务点名要我证伪的"带行尾注释"反例**攻击失败**。
2. **P0-2（X1）**：目标已改为"任务目录内"、第 4 批划界已补、PAUSED 留痕已补，边界可执行。
3. **P0-3（X5）**：写法已改对；**风险方向"放宽"经我端到端实测确认**（`rc=2`→`rc=0`）。

**⚠️ 但仍有 1 个数值级缺陷 + 若干未闭合项**，其中 **§3.1（X5 存量数字）** 是**新发现的实质问题**：

- **§3.1**：X5 的存量扫描数字（"107 条 / 1 条含管道"）**用仓库自己的解析器跑不出来**
  （实测 **315 / 21**）。虽然**最终结论"风险≈0"仍成立**，但**理由是错的**，
  且**低估了条件性风险**。V10 要求"附扫描命令 + 原始输出"，**该行不满足**。
- **§3.2**：X3 的 SKIP 面仍漏 2 个（同形态），第一轮意见未真正闭合。
- **§3.3**：X6 存量"3 个任务"与实际口径不符。
- **§3.4**：X6 的 presence 正则未落定，**第一轮建议的候选 D 本身是错的**（我实测），
  照抄会复发反向缺陷。
- **§3.5**：X2 的暂存区读取失败回退语义仍未定义（第一轮明确要求）。
- **§3.6**：实现基线字面值自相矛盾（写 `fa2fc3d`，实为 `05edb02`）。
- P1-2 的**别名词表**、P1-5 的 **V3 加强**：仍是"抄成待办"而非"完成待办"。

**⇒ 为什么不是 `APPROVED WITH NITS`**：§3.1 是**可机械证伪的数值错误**（不是措辞问题），
且 §3.4 会让实现者**照抄一个我实测有缺陷的正则**——两者都会直接进入实现。
**⇒ 为什么不是彻底 `NEEDS-REVISION`（不能实现）**：三个 P0 的**设计方向与实现指引已正确**，
剩余项都是"补数字 / 补正则 / 补一句回退语义"，**边际修订成本 < 1 小时**，无需重做设计。

### 建议的最小修订清单（按优先级）

| # | 修订 | 对应 |
|---|---|---|
| 1 | §4.2 的 X5 行改为：用 `parse_gate_commands_block` 扫出 **315 条 / 21 条含管道**，并补上**真实理由**（21 条全在 `P5*` 键且 formatter 为空 ⇒ 不进 `run_test_with_formatter`；P3 键含管道 = 0），**并声明条件性风险** | §3.1 |
| 2 | §X6 写死正则：`re.match(r"^follows_existing_pattern:", line)`；**并删除/更正第一轮候选 `^follows_existing_pattern:\s*$`**（漏流式列表） | §3.4 |
| 3 | §X3 补面③（L142 无法读取 `.state.yaml`）与面⑤（L162 refactor 跳过）；V3 改为"输出结构变化 + 改坏即红负向控制" | §3.2、P1-5 |
| 4 | §4.2 的 X6 行改成准确口径（`^key:` 声明形式 **1 个任务**；含 TAG0018 同文件双键） | §3.3 |
| 5 | §X2 补暂存区读取失败回退（`git show` 失败 ⇒ 回退工作区 + WARNING）+ 测试 | §3.5 |
| 6 | L6 基线改为 `05edb02`（+ sha256） | §3.6 |
| 7 | §X4 给出英别名词表**本身**（或降为"结构化字段 + 中文短语"两项） | P1-2 |
| 8 | §3 删除重复行；§X9 补 DEBT0013 的**核对结论**（非仅"须核对"） | N5、P1-4 |
| 9 | 采纳 §4 的 N1–N4、N6 nits | §4 |

**⇒ 修订 1–3 为"应修"（影响实现正确性），4–8 为"宜修"（影响可验收性），9 为 nit。**
**完成 1–3 后即可开始实现。**

---

*评审性质：独立对抗式设计**复审**（fresh context；设计未实现，无代码改动）*
*只读纪律：全程未执行任何写仓 git 命令（无 checkout/restore/reset/stash/clean/add/commit/push）；*
*未编辑任何文件（本报告为唯一写入路径）；未切换分支；所有探针在 `mktemp -d` 一次性副本内*
*「建→用→清」同一 bash 调用完成；未跑全量 pytest；bash 均加 `timeout`。*
