# 设计：第 0 批——9 个「现在就是错的」缺陷修复（TAG0042 前置）

> **日期**：2026-10-04 ｜ **性质**：设计（**未实现**），待独立评审
> **归属**：TAG0042「项目形态命令化 + 规则脚本化」的**第 0 批**（设计分析 §7 标注「无前提，改动都很小」）
> **范围**：**只改 agateon 本仓**（其他项目不归本任务）
> **事实基线**：main `4daa60b` 之后

---

## 1. 为什么先做这一批

TAG0042 主体（第 1–6 批）是**架构演进**：新增 `agate-config` / `agate-run` / `agate-ci-verify` /
`agate-doctor`，分 7 批推进。**但第 0 批的 9 项不是"改进"，是"现在就是错的"**：

| 性质 | 项 |
|---|---|
| **安全门失效** | X1（收尾阶段不扫 PROD_TOUCHED） |
| **假绿** | X3（backstop 永远 SKIP 却显示绿）、X4、X6、X7 |
| **吞错误** | X5（无 pipefail） |
| **数据丢失风险** | X8（覆盖软链 hook 不备份） |
| **门禁从不运行** | X9（P8 卡要求以 READY 提交 ⇒ gate_p8 跑不到） |

**⇒ 让它们等一个 7 批的大任务走完才修，是不合理的。**

---

## 2. 逐项设计（每项：实测缺陷 → 目标行为 → 风险）

### X1 — READY/DONE 提交跳过 PROD_TOUCHED 扫描（**安全门失效**）

**缺陷**（代码实测）：`pre-commit-gate.py` 的
```python
# 2g. 跳过非 gate 阶段
if phase in ("PAUSED", "READY", "DONE"):
    continue                      # ← 在扫描之前
...
# 2g.1 PROD_TOUCHED 检测（P1.2）
```
`continue` 发生在扫描**之前** ⇒ 收尾提交（正是"准备发布"那个时点）**完全不扫**。

**目标行为**：**所有阶段都扫描**；`PAUSED` **只扫描不阻断**（设计 §5 原文）。
即把"跳过 gate"与"是否扫描 PROD_TOUCHED"解耦。

**风险**：会让**存量任务**在收尾提交时被拦（若其 diff 含 `[PROD_TOUCHED]`）。
⇒ **须先全量扫描存量**（`AGENTS.md` 工作流第 0 条），确认不误伤。

---

### X2（部分）— phase 从**暂存区**读取

**缺陷**：`read_state_phase(state_file)` 读**工作区**文件。若工作区的 phase 与暂存的 phase
不同（"边改边提交"），hook 按工作区判定 ⇒ **判错阶段**。

**目标行为**：hook 侧**一律从暂存区读**（`git show :<task>/.state.yaml`），不读工作区。

**⚠️ 本批只做最小面**：设计 §7 把 X2 拆成两半——
「phase 从暂存区读取」属第 0 批；「按提交类型分级」属第 4 批。
本批**只做前者**，且**只在 hook 的调用点**改为暂存区读取（`read_state_phase` 本身保持兼容，
新增 `read_staged_state_phase`，避免改动 4 个调用方的语义）。

**风险**：新增函数须与既有 `read_state_phase` 语义一致（除数据来源外）。
**存量影响**：若某任务工作区与暂存区 phase 不同，判定会**变化** ⇒ 须扫描存量。

---

### X3 — `ci-gate-backstop` 永远 SKIP 却显示绿（**假绿**）

**缺陷**（代码实测）：
```python
repo_root = Path.cwd()
state_file = repo_root / ".state.yaml"          # ← 只读仓库根
if not state_file.exists():
    print("SKIP: 无 .state.yaml，非 agate 项目")
    return 0                                    # ← exit 0 = 绿
```
而**任务状态在 `<workspace>/tasks/<Txxx>/.state.yaml`** ⇒ 永远 SKIP ⇒
**它是必过检查，却恒绿**（设计分析实测：agateon 上是必过但永远 SKIP）。

**目标行为**（设计 §5 X3）：**找不到对象时大声失败**，或**移出必过检查**；删掉卡片里
「兜底会重跑」的说法。

**⚠️ 实测后本项需要重新设计——原选择会让本仓 CI 断掉。**

**实测补充（设计分析未涵盖）**：
1. `gate-backstop` **是 required check**（`protocol-tests.yml:14` 明列 4 个 required job）。
2. 而 CI 头部注释 **①–③** 记明了一条**血的教训**：
   > required check 若 `skipped` 或无 check-run，GitHub 分支保护会**永久 BLOCK**
   > （PR #193 实证「6 of 6 required status checks are expected」）。
   > **故当前实现的 intentional 设计就是：job 始终运行，跳过时 `echo + exit 0` ⇒
   > conclusion=success ⇒ 分支保护满足。**

**⇒ `return 0`（绿）在 CI 语境下是"为了让 required check 能过"的**有意设计**，
不是纯粹的疏忽。**

**但"假绿"的问题真实存在**：它 `exit 0` 时**输出的是 `SKIP`**，
**读者（和人）无法从 CI 状态分辨"兜底跑了且通过"与"兜底根本没跑"。**

**⇒ 修订后的目标行为**：**保留 exit 0**（不破坏 required check 机制），
但**让"未生效"这件事在 CI 上醒目可见**：

| 场景 | 现在 | 改后 |
|---|---|---|
| 无 `.state.yaml` | `SKIP:` + exit 0（**与 PASS 无法区分**） | **显式 WARNING 块**（含"backstop 未生效"+ 如何配置）+ exit 0 |
| 平台未识别 | 同上 | 同上 |

**理由（ADR-015 手段②「让错误可见」）**：这里**不能**用手段①（让错误不可能）——
CI 机制决定了 required check 必须 success；**但可以让它"绿得刺眼"**。

**并且**：在**本仓**同时把该 job 的**真实目的**说清——它兜的是**项目侧**的 gate，
而 agateon 本仓的任务状态在 `agate-workspace/`，**本仓的兜底应由 `agate-ci-verify`（第 5 批）承担**。
⇒ 本批**登记**该缺口，不假装已解决。

**风险**：低（仅输出变化 + exit code 不变）。

---

### X4 — P6 复用识别只认中文短语（**fail-open**）

**缺陷**（代码实测）：
```python
return bool(re.search(r"引用\s*P5\s*证据", text))
```
只认中文短语。英文写法、结构化字段**都不认** ⇒ 该判定**静默失效**。

**目标行为**（设计 §5 X4）：三种写法都识别——**结构化字段 / 中文短语 / 英文别名**。

**风险**：放宽后可能让**原本被拦**的案例通过 ⇒ 须扫描存量任务的 P6-acceptance。

> ⚠️ **与今晚刚做的 `extract_evidence_refs` 关系**：那是"证据引用提取"；
> 本项是"P5 证据复用声明"识别。**两者不同**，不共用判据（但都属"只认一种写法"的同族病）。

---

### X5 — 执行命令未开 `pipefail`（**吞退出码**）

**缺陷**（代码实测，`agate_common.py`）：
```python
proc = subprocess.run(
    cmd, shell=True, executable="bash",       # ← 无 -o pipefail
    ...)
```
⇒ `cmd | tail` 的失败被吞（**TAG0016 已实际发生**：`| tail` 让失败被长期掩盖）。

**目标行为**：改为 `bash -o pipefail`（与 `AGENTS.md`「所有脚本 `set -euo pipefail`」一致）。

**风险**：**会暴露此前被吞的失败** ⇒ 某些任务可能由绿转红。**这是有意的**
（吞错误才是缺陷）。须扫描存量。

---

### X6 — `design_trivial` 按**存在**判，不按**值**判

**缺陷**（代码实测）：
```python
if any(design_trivial_declared(line) for line in p1_lines):
    min_candidates = 1
```
`design_trivial_declared(line)` 只看**是否有该声明**，不看其**值** ⇒
`design_trivial: false` 也被当成"已声明" ⇒ **最低候选数被降为 1**（本该是 2）。

**目标行为**（设计 §5 X6）：**按值判断**（`true` 才降为 1）。

**风险**：会让某些 P2 由绿转红（候选数不足）。**这是有意的**——正是要修的假绿。

---

### X7 — P2-review 缺 `agent` 放行（exit 2），P1 同类却 exit 1（**不一致**）

**缺陷**（代码实测）：

| 检查 | 缺 `agent` 时 |
|---|---|
| P1-review | `return 1`（阻断） |
| **P2-review** | `return 2`（**放行**，注释写"向后兼容 WARNING"） |

⇒ 同一概念两种判定。且 `agent` 字段正是**"评审者不是主 Agent"**的证据（`agent == "main"` 已阻断），
**缺字段放行等于可绕过**。

**目标行为**（设计 §5 X7）：**统一为 exit 1**。

**风险**：存量任务的 P2-review 若缺 `agent` ⇒ 会转红。须扫描存量。

---

### X8 — `install-hook` 覆盖软链 hook **不备份**（**数据丢失**）

**缺陷**（代码实测）：
```python
def _backup(hook_file, label):
    if os.path.isfile(hook_file) and not os.path.islink(hook_file):   # ← 排除了软链
        ...
```
软链 hook **不备份**。而设计分析实测：**peekview 的 hook 正是软链**
（`make setup-hooks` 与 `install-hook.py` 争用同一位置）。

**目标行为**（设计 §5 X8）：**所有 hook 都备份**，或**改为链式调用**。

**本批选择**：**所有 hook 都备份**（最小改动、可逆）。
> 不选"链式调用"：那是行为变更，属第 4 批的关卡层设计。

**风险**：低（只增加备份）。**但需注意**：软链备份应记**链接目标**而非复制内容，
否则备份无意义 ⇒ 备份时**记录软链指向**。

---

### X9 — P8 卡要求「以 READY 提交」⇒ **gate_p8 从不运行**

**缺陷**（卡片原文实测）：
```
⚠️ 此时 .state.yaml 的 phase 保持 READY，不要提前写 DONE——phase = 本 commit 的产出阶段；
```
而 hook 的跳过序含 `if phase in ("PAUSED","READY","DONE"): continue` ⇒
**以 READY 提交 ⇒ gate_p8 永不运行**。

**实证**：agateon **38 个 READY/DONE 任务中仅 16 个曾以 `phase:P8` 提交**
（我用同样的 `--follow` 统计复核，逐字吻合）。

**目标行为**（设计 §5 X9 + §2.1）：**改为以 `phase: P8` 提交 P8 产出**，gate_p8 才能运行；
进入 READY 单独提交一次。

**⚠️ 这是本批唯一改"协议语义表述"的项**，且与 §2.1 的 phase 语义统一**直接相关**。

**风险**：**改卡片会影响所有用 agateon 的项目**（不限于本仓）。
⇒ **须谨慎**：本批**只改卡片文字**使之与既有 hook 行为**一致**，
**不改 `agate-next` 的预写行为**（那属第 1 批）。

---

## 3. 批内取舍：哪些**不在**本批

| 项 | 为何不在本批 |
|---|---|
| X2 的「按提交类型分级」 | 属第 4 批（关卡层设计） |
| `agate-config` / `agate-run` 等 | 第 2–6 批（架构演进） |
| 「`ci-gate-backstop` 换成 `agate-ci-verify`」 | 第 5 批；本批只让它**不再假绿** |

---

## 4. ⚠️ 必须先确认的两件事（**未确认前不动手**）

### 4.1 X3 —— **已实测确认**（本项设计据此修订）

**实测**：`gate-backstop` **是 required check**；且 CI 头部注释记明
「required check 若 skipped ⇒ 分支保护永久 BLOCK」⇒ **`exit 0` 是有意设计**。

**⇒ 本项改为「保留 exit 0，但让未生效醒目可见」**（见 X3 节），
**不再改为 exit 1**——那会断掉本仓 CI 且违背已记录的教训。

### 4.2 X1/X5/X6/X7 的**存量影响**须先扫描

这四项都会让**某些存量任务由绿转红**。按 `AGENTS.md` 工作流第 0 条
（新增 CHECK/规则前先全量扫描存量）+ 0a（**R6 只在副本上跑**）：

| 项 | 须扫描 | 预期 |
|---|---|---|
| X1 | 存量任务的收尾提交 diff 是否含 `[PROD_TOUCHED]` | 预期 0（设计称语料 0 例） |
| X5 | 存量 `gate_commands` 是否含管道（`\| tail` 等） | **可能有**（TAG0016 先例） |
| X6 | 存量 P1 是否写了 `design_trivial: false` | 待测 |
| X7 | 存量 P2-review 是否缺 `agent` | 待测（设计称"向后兼容"暗示有存量） |

**⇒ 这四项的扫描结果是本批能否合并的前提。**

---

## 5. 验收锚（逐条可机械校验）

| # | 锚 | 判据 |
|---|---|---|
| V1 | X1 所有阶段都扫 | 构造 `phase: READY` + diff 含 `[PROD_TOUCHED]` ⇒ **exit 1**；`PAUSED` ⇒ **扫描但不阻断** |
| V2 | X2 从暂存区读 | 工作区 phase=P1、暂存区 phase=P2 ⇒ hook 按 **P2** 判定 |
| V3 | X3 不再**静默**假绿 | 无 `.state.yaml` 时：**exit 0 不变**（保 required check）+ 输出含 **WARNING** 与"backstop 未生效"字样；有 `.state.yaml` 时按原逻辑 |
| V4 | X4 三写法都认 | 结构化字段 / 中文短语 / 英文别名 ⇒ 均识别 |
| V5 | X5 pipefail 生效 | `cmd \| tail`（cmd 失败）⇒ **非 0** 退出码 |
| V6 | X6 按值判 | `design_trivial: false` ⇒ 仍需 **2** 个候选 |
| V7 | X7 统一 exit 1 | P2-review 缺 `agent` ⇒ **exit 1**（与 P1 一致） |
| V8 | X8 软链也备份 | 目标是软链 ⇒ 生成备份且**记录链接目标** |
| V9 | X9 卡片不再误导 | 卡片文字与 hook 行为一致（不再要求"以 READY 提交"） |
| V10 | **存量扫描报告** | 四项（X1/X5/X6/X7）的存量影响逐条列出，**无未解释的转红** |
| V11 | 全量回归 | `pytest` 全绿 + `consistency 0 ERROR` + `ruff` + structure S0–S6 |

**负向控制**：每个新增用例都须"改坏即红"实测（防空转守护）。

---

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 四项改动让存量任务转红 | §4.2 先扫描；无未解释转红才合并 |
| X3 让本仓 CI 变红 | §4.1 先查 required 配置，本批一并处理 |
| X9 影响所有用 agateon 的项目 | **只改卡片文字**与既有 hook 行为对齐，不动 `agate-next` |
| X8 备份软链无意义 | 备份时**记录链接目标**，不是复制内容 |
| 7 个文件、跨 3 个脚本族 | 沿用 hotfix 判据**修订版**（单一主题「修既有缺陷」+ 无跨模块影响），PR 里说明为何不立项 |

---

## 7. 与 TAG0042 主体的关系

- 本批是 **TAG0042 的第 0 批**（设计分析 §7）；
- 但它**独立可合并**——不依赖第 1–6 批的任何产物；
- **X9 与第 1 批有交集**（都涉及 phase 语义）：本批只做**文字对齐**，
  第 1 批才改 `agate-next` 行为。**须在 TAG0042 的 P0-brief / 后续产物里记明这条分工**，防重复改。
