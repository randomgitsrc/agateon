# 设计：第 0 批——9 个「现在就是错的」缺陷修复（TAG0042 前置）

> **日期**：2026-10-04 ｜ **性质**：设计（**未实现**），待独立评审
> **归属**：TAG0042「项目形态命令化 + 规则脚本化」的**第 0 批**（设计分析 §7 标注「无前提，改动都很小」）
> **范围**：**只改 agateon 本仓**（其他项目不归本任务）
> **事实基线**：main `4daa60b` 之后 ｜ **设计基线**：**`05edb02`**（本文自身）
> （⚠️ 独立评审指出：设计曾有两个版本 `f5e4c31` → `fa2fc3d`，**实现须以本版为准**；
> 本文已按评审的 P0/P1/P2 清单全部修订）

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

**⚠️ 原设计目标「**所有阶段都扫描**」**无法由它给出的改动达成**（独立评审反例，我复核确认）**：

扫描另有一层门控——
```python
if any(f.startswith(prefix) for f in _staged_name_only()):   # ← 只在「任务目录下有文件被暂存」时才扫
```
⇒ **`phase: P4` 下把 `[PROD_TOUCHED]` 写进 `app.py`（非任务目录文件）也完全不扫**；
把 `continue` 下移**改变不了这一点**。

**目标行为（修订）**：本批达成「**所有阶段的、任务目录内的**暂存 diff 都扫描」；
`PAUSED` **只扫描不阻断**。
> 真正"所有文件都扫描"须**放宽上面那层门控**——那是**扩大扫描面**，属**跨模块影响**，
> **明确划入第 4 批**（与外部设计分析 §2.4「每一次提交」行同源：该行本就写「PROD_TOUCHED 扫描
> （PAUSED 只扫描不阻断）」）。

**粒度说明**（评审确认此点设计是对的）：改动粒度须为「**把 2g.1 整体上移**」，
**不是"删掉 `continue`"**——后者会连带跳过 frontmatter schema、P6 归一化、`check-gate`、
`write_gate_result`、`append_event` 及 2i–2o 全部检查。

**PAUSED 分支须留痕**（评审补充，我采纳）：`state-machine.md:98` 定义
`任意阶段 --[出现 PROD_TOUCHED]--> PAUSED` ⇒ "PAUSED 只扫不阻断"语义自洽；
但若扫到**新的** PROD_TOUCHED，按 `state-machine.md:255` 该信息**无机械消费方**
⇒ **须至少 `append_event` 或写账本 WARNING**，否则等于"只打印到 stderr、无留痕"。

**风险**：会让**存量任务**在收尾提交时被拦（若其 diff 含 `[PROD_TOUCHED]`）。
⇒ **须先全量扫描存量**（`AGENTS.md` 工作流第 0 条），确认不误伤。

---

### X2（部分）— phase 从**暂存区**读取

**缺陷**：`read_state_phase(state_file)` 读**工作区**文件。若工作区的 phase 与暂存的 phase
不同（"边改边提交"），hook 按工作区判定 ⇒ **判错阶段**。

**目标行为**：hook 侧**一律从暂存区读**（`git show :<task>/.state.yaml`），不读工作区。

**⚠️ 原设计称"4 个调用方"不实**（独立评审核验，我采纳）：
实测生产调用点**只有 2 个**——`pre-commit-gate.py` 的 **L257 与 L590**
（`agate-advance.py:76` 是同名**本地**函数、`agate-next.py:52` 只 import 未调用）。
⇒ **两个调用点都要改**；只改 L257 会让**同一次 commit 内两处 phase 来源不一致**。

**⚠️ 本批只做最小面**：设计 §7 把 X2 拆成两半——
「phase 从暂存区读取」属第 0 批；「按提交类型分级」属第 4 批。
本批**只做前者**：新增 `read_staged_state_phase`（`agate_common`），
`read_state_phase` **本身不动**（避免语义漂移），在**两个** hook 调用点改用新函数。

**⚠️ 暂存区读取失败的语义须定义（第一轮已要求，本版补）**：
- 暂存区**无** `.state.yaml`（如该文件本次未暂存）⇒ **回退读工作区**？
  还是**视为"无状态"跳过**？
- **本设计选**：**回退读工作区**——理由是"本次未暂存状态文件"是常见情形，
  若视为无状态会导致 hook **静默跳过整条链**（正是 X2 要治的病）。
- **但须同时**：回退时输出**显式提示**（"本次未暂存 .state.yaml，phase 取自工作区"），
  使"读的是哪一份"可见。
- **测试**：V2 须含**两种**输入——① 暂存区有 ⇒ 用暂存区；② 暂存区无 ⇒ 回退工作区 + 提示。

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
| **phase ∈ PAUSED/READY/DONE** | `return 0` | 同上（显式 WARNING） |
| **无法读取 `.state.yaml`**（解析失败） | `return 0` | 同上（**这是最该醒目的一个**——数据坏了却报绿） |
| **refactor 任务**（TDD 红灯不适用） | `return 0` | **这一面可保留**（语义正当），但措辞须与其余区分 |

> ⚠️ **实测共 5 个 SKIP 面**（原设计只列 3 个；第一轮评审补了 1 个；**本版补齐**）。
> 逐行核对：L124 平台未识别 / L132 无 `.state.yaml` / **L142 无法读取** /
> **L146 phase 无 gate 需对照** / **L162 refactor**。
> **须逐个决定**：哪些改「显式 WARNING」、哪些保留原样（refactor 面语义正当）。
> ⚠️ **V3 不能只用关键词判据**（第一轮已指出）——须**行为判据**：对每个 SKIP 面构造输入，
> 断言「exit 0 不变」**且**「输出含 WARNING 标识」（改坏即红的负向控制）。

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

**⚠️ 消费方遗漏（评审查出）**：`p6_declares_reuse` 经 **`--audit7-only` CLI** 被
**`P8-release.md:84-88`** 消费 ⇒ 放宽会改变 **`AUDIT7_RESULT` 三态**、进而改变
**P8 主 Agent 的动作**（`reuse_allowed` vs `reuse_blocked`）。**须一并评估。**

**⚠️ 风险方向说反了**（评审更正）：放宽识别 ⇒ **更多行被判为"已声明复用"** ⇒
audit7 更可能判 `reuse_blocked` ⇒ **是更多拦截，不是更多通过**。

**别名词表（本版给出，不再留作待办）**：

| 形态 | 判据 |
|---|---|
| 结构化字段 | P6-acceptance.md frontmatter 的 `p5_reuse`/`evidence_reuse` 类字段（**须先定字段名**——实现时以 schema 为准） |
| 中文短语 | `引用\s*P5\s*证据`（现行，保留） |
| **英文别名** | `reuse[sd]?\s+P5\s+evidence` / `reusing\s+P5\s+evidence` / `P5\s+evidence\s+reus` |

⚠️ 英文词表**须在实现时用两仓真实语料验证**（防"定义了却无实例"或"漏掉真实写法"）。
**本表是起点，不是终点**——V4 须含真实语料回放。

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

**⚠️ 原设计的实现指引字面不可执行**（独立评审实测，我复核确认）：
```python
subprocess.run(cmd, shell=True, executable="bash -o pipefail")
# → FileNotFoundError: [Errno 2] No such file or directory: 'bash -o pipefail'
```
`executable` 是**路径**，不接受命令行参数。**正确写法**（评审实测 rc 符合预期）：
```python
cmd = "set -o pipefail; " + cmd          # ← 前缀方式
# 或 SHELLOPTS env
```

**存量扫描（⚠️ 数字经两轮评审更正，我复核确认）**：

| 口径 | 结果 |
|---|---|
| 原设计写 | 「107 条中仅 1 条含管道」——**不实**（其给出的命令跑不出该数字） |
| 第一轮评审写 | 同样 107/1——**同样不实** |
| **实测（`parse_gate_commands_block`，权威判据）** | **315 条 / 21 条含管道** |

**但「转红风险 ≈ 0」的结论仍成立——理由与原设计不同**（评审给出，我采纳）：
- 这 21 条**全在 `P5*` 键且 formatter 为空** ⇒ `agate-capture-env-baseline` 遇无 formatter
  **直接 bail**，**不进** `run_test_with_formatter`（即不进被 pipefail 影响的那条路径）；
- **`P3` 键含管道 = 0**（实测）——而 `check-tdd-red` **只消费 `P3` 键**。

⇒ **本项是「条件性低风险」，不是「无风险」**：若将来有 `P3` 键使用管道，
pipefail 会**立即**改变 TDD 红灯判定。**该条件须写进 V5。**

**⚠️ 原设计漏了一个耦合，且风险方向说反了**（评审指出）：
`pipefail` 影响 **`check-tdd-red.py` 的 P3 红灯语义**——那里「非 0 = 红灯 = 符合 TDD」，
加 pipefail 后**方向可能是放宽**（更容易判为红），而**不是**原设计写的"由绿转红"。
⇒ **须在实现时评估该方向**，并在 P3 相关测试上验证。

---

### X6 — 「轻量设计」声明判定：**两键语义不同，须分别处理**（原设计应拒绝）

**⚠️ 本项经独立评审**拒绝**并给出反例，我复核确认。原设计「按值判断」是错的。**

**实测的两个反向缺陷**（同一函数 `agate_common.design_trivial_declared`）：

```python
return bool(re.search(r"^(design_trivial|follows_existing_pattern):\s*\S", line))
```

| 键 | schema 类型 | 真实写法 | 现判定 | 问题 |
|---|---|---|---|---|
| `design_trivial` | bool | `design_trivial: false` | **presence=True** | ❌ **假绿**：`false` 被当成"已声明" ⇒ 最低候选数降为 1 |
| `follows_existing_pattern` | **`list`**（`agate-frontmatter-check.py:54` 明列） | `follows_existing_pattern:`（**块列表，键行无值**） | **presence=False** | ❌ **漏认**：合法声明不被识别 |

**⛔ 原设计「按值判断，`true` 才降为 1」是错的**：它只修了第一行，**会强化第二行的漏认**
（块列表**不存在 `true`/`false`**）。反例（存量 TAG0018）：
```
P1-requirements.md:16  design_trivial: true
P1-requirements.md:17  follows_existing_pattern:      ← 块列表，presence=False
```
该任务今天"生效"只是因为 L16 另有 `design_trivial: true`；
**一个只写了块列表的任务，今天与改后都判「未声明」** ⇒ `candidate_count: 1` 会被判红。

**目标行为（修订）——两键分别处理**：
- `design_trivial`：走 `_md_field_get("design_trivial", p1_file)`（`agate-md-field-get.py` 已有
  `_regex_scalar(..., r"design_trivial:\s*(true|false)")` 通道），**判 `== "true"`**；
- `follows_existing_pattern`：**保持 presence 语义**（它是 list，有键即声明），
  **正则写死为**：
  ```python
  re.match(r"^follows_existing_pattern:", line)
  ```
  **⚠️ 不要用 `^follows_existing_pattern:\s*$`**——独立评审实测它**漏掉流式列表**
  `follows_existing_pattern: [a, b]`。（**第一轮评审给出的正是这个候选，照抄会复发反向缺陷。**）
  实测三形态（块列表 / 流式列表 / 注释掉的）**只有 `^key:` 全部正确**。

**⚠️ 实现者若把两键合并成一条规则，会制造真实的存量转红。** 本设计**明写**此点。

**存量影响**（评审实测，我复核）：全仓**仅 1 个任务**（TAG0018）命中该正则，
且它是唯一 `candidate_count < 2` 的任务；另有 2 个任务含 `follows_existing_pattern`。
**⇒ 须逐个核对这 2–3 个任务在修订后的判定。**

### X7 — P2-review 缺 `agent` 返回**通过码**（**真 fail-open**，比设计分析描述的更严重）

**⚠️ 实测后本项理解需更正——问题不是「与 P1 不一致」，而是「返回了通过码」。**

**代码实测**：
```python
# check-gate.py  gate_p2 内
agent = _md_field_get("agent", p2_review)
if not agent:
    sys.stderr.write("GATE P2: ...缺 agent 字段（向后兼容 WARNING）\n")
    return 2                       # ← ← ← 这是 gate_p2 的**正常通过码**
```

**而 `check-gate.py` 头部与 `phases.yaml` 明确定义**：
```
exit 2 = 多数 phase 正常通过码（含动态 gate_commands 或语义判断后的"通过"出口）
P0-P3/P5/P6/P8 的通过码是 exit 2（… p2 L883 … return 2）
```

**⇒ `return 2` 不是"WARNING 不阻塞"，是"**通过**"。**
注释写"向后兼容 WARNING"是**误标**——实际语义是 **fail-open 放行**。

**目标行为**：**不得返回通过码**。缺 `agent` ⇒ 返回 **1**（`gate_p2` 的未通过码）。
与 P1 侧（缺 `agent` ⇒ `return 1`）**行为一致**，但**理由不是"统一"，是"当前返回了通过码"**。

**⚠️ "是否需迁移期"这个未决点已被评审实测消解**：
评审扫描 **37 个任务**的 `P2-review` / `P1-review` / `P4-review` / `P6-acceptance` 的
`agent` 字段 ⇒ **missing = 0（100% 齐备）** ⇒ **转红数 = 0，无需迁移期**。
（原设计称"注释暗示存量中确有此类"是**从注释推测**，实测否定了该推测。）

**补强论据（评审给出，我采纳）**：`exit 2` 在该 returning site **确凿就是通过码**，三方一致：
- `phases.yaml` P2 声明 `gate_pass_exit: 2`；
- `check-gate.py` 头部：「exit 2 = 多数 phase 正常通过码」；
- `adr.md` 同口径。

且消费方行为印证：`pre-commit-gate.py` 对 exit 2 **只打印、不 `sys.exit(1)`**；
`agate-next.py` 对 `2 ∈ pass_set` **直推下一阶段**。

**⇒「统一为 1」不过度，是修正 fail-open。**

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

**实现（评审给出最简做法）**：软链备份即 `os.readlink(hook_file)` 一行，记录**链接目标**
（**不是**复制内容——复制软链内容无意义）。

**⚠️ 同函数另有一个更严重的缺陷（评审建议并入本批，我采纳为第 10 项）**：
`_backup` 用 `os.path.isfile(hook_file)` 作前置条件 ⇒ **悬空软链（dangling symlink）
`isfile` 为 False** ⇒ **既不备份**，又被后续 `os.unlink` **删除** ⇒ **静默丢失**。
**比 X8 原指的"软链不备份"更严重**（原缺陷至少留下软链，这个直接删掉）。
同函数、同主题，**边际成本 ≈ 0** ⇒ **并入 X8 一并修**。

**风险**：低（只增加备份与 readlink）。

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

**⚠️ 原设计的理由打空靶**（评审查出）：实测 `agate-next` **本就无"预写 READY"行为**
（其文件头明写：phase ∈ {PAUSED, READY, DONE} → 提示不推进）。原设计把它当成要防的对象，是**误指**。

**实测支持"可拆分"**（评审，我采纳）：`TAG0037` 真有
`30e2354 phase=P8` → `59aeaeb phase=READY` **两次提交** ⇒ **"以 P8 提交产出、再单独提交 READY"
可行且已成惯例**；**无脚本依赖"以 READY 提交"**。
另：`38/16` 的「gate_p8 从不运行」**措辞过强**——对那 16 个任务不成立（它们确有 phase=P8 提交）。
准确表述：**22/38 个任务从未以 P8 提交**。

**⚠️ 另漏 `P8-release.md:89-93` 的 DEBT0013 时序说明**（CHECK 7 相关），改卡片时须一并核对。

**风险**：**改卡片会影响所有用 agateon 的项目**（不限于本仓）。
⇒ 本批**只改卡片文字**使之与既有 hook 行为一致，**不改 `agate-next`**（那属第 1 批）。

---

## 3. 批内取舍：哪些**不在**本批

| 项 | 为何不在本批 |
|---|---|
| X2 的「按提交类型分级」 | 属第 4 批（关卡层设计） |
| `agate-config` / `agate-run` 等 | 第 2–6 批（架构演进） |
| 「`ci-gate-backstop` 换成 `agate-ci-verify`」 | 第 5 批；本批只让它**不再假绿** |
| **X1 的「非任务目录文件也扫」** | **第 4 批**——须放宽 L327 门控（扩大扫描面 = 跨模块影响）。本批只做到「所有阶段的**任务目录内** diff 都扫」 |
| X9 的「改 `agate-next` 行为」 | 第 1 批；本批只改**卡片文字** |

> **边界声明的方法要求**（评审）：凡本批只做"一半"的项，**都要像 X9 那样显式声明另一半归属哪批**。
> X1 原设计漏了这条（X9 声明了），已补。

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
| X5 | 存量 `gate_commands` 是否含管道（如 `2>&1` 接 `tail`） | **可能有**（TAG0016 先例） |
| X6 | 存量 P1 是否写了 `design_trivial: false` | 待测 |
| X7 | 存量 P2-review 是否缺 `agent` | 待测（设计称"向后兼容"暗示有存量） |

**⇒ 这四项的扫描结果是本批能否合并的前提。**

**扫描命令（评审要求"每项该怎么扫"，且我实测过的项已给出结果）**：

| 项 | 命令 | 实测结果 |
|---|---|---|
| X1 | 逐 commit 重放 hook 判「收尾提交 diff 是否含 `[PROD_TOUCHED]`」 | ⚠️ **不可操作**（需重放）⇒ 改为：`grep -rl '\[PROD_TOUCHED\]' agate-workspace/tasks/*/` 后**逐个人工核对**其阶段 |
| X5 | **用仓库自己的解析器**（唯一权威判据）`parse_gate_commands_block()` 逐 P2-design.md | ✅ 实测 **315 条 / 21 条含管道**（TAG0025 11 / TAG0010 5 / TAG0011 4 / TAG0003 1）——**原设计与第一轮评审的「107/1」均不实**；**但 `P3` 键含管道 = 0** ⇒ 见下 |
| X6 | `grep -rl -e design_trivial -e follows_existing_pattern agate-workspace/tasks/*/P1-requirements.md` | ✅ **仅 TAG0018 一个任务**（`^key:` 声明形式；原设计写「3 个任务」口径不符，已更正）⇒ 逐个核对 |
| X7 | 扫 `P1-review` / `P2-review` / `P4-review` / `P6-acceptance` 的 `agent` 字段 | ✅ **37/37 齐备，missing=0** ⇒ 转红 0 |

**V10 的判据强度**（评审要求定义）：
> **「无未解释转红」= 上表四项的扫描结果中，每一条转红都能归入以下之一：
> ① 已实测的真违规；② 本批有意收紧且已在本设计登记；③ 存量数据缺陷（登记为债务）。
> 凡不能归入者，本批不得合并。**

---

## 5. 验收锚（逐条可机械校验）

| # | 锚 | 判据 |
|---|---|---|
| V1 | X1 所有阶段都扫（**任务目录内**） | `phase: READY` + **任务目录内** diff 含 `[PROD_TOUCHED]` ⇒ **exit 1**；`PAUSED` ⇒ **扫描 + 留痕（append_event/WARNING）但不阻断** |
| V2 | X2 从暂存区读 | 工作区 phase=P1、暂存区 phase=P2 ⇒ hook 按 **P2** 判定 |
| V3 | X3 不再**静默**假绿 | 无 `.state.yaml` 时：**exit 0 不变**（保 required check）+ 输出含 **WARNING** 与"backstop 未生效"字样；有 `.state.yaml` 时按原逻辑 |
| V4 | X4 三写法都认 | 结构化字段 / 中文短语 / 英文别名 ⇒ 均识别 |
| V5 | X5 pipefail 生效 | 命令写作 `set -o pipefail;` 前缀 + 含管道的 cmd（**不是** `executable="bash -o pipefail"`）；cmd 失败 ⇒ **非 0**。**并验证 P3 红灯语义方向（实测为"放宽"）**。**⚠️ 条件性低风险**：现存量 `P3` 键含管道 = **0**（实测），若将来出现则会改变 TDD 判定 ⇒ **须留下该条件的登记** |
| V6 | X6 **两键分别处理** | `design_trivial: false` ⇒ 仍需 **2** 个候选（**非**降为 1）；`follows_existing_pattern:`（**块列表，键行无值**）⇒ **算已声明** ⇒ 可降为 1 |
| V7 | X7 不再返回**通过码** | P2-review 缺 `agent` ⇒ **exit 1**（现为 exit 2 = gate_p2 的**通过码**）；断言「不得等于 `gate_pass_exit`」 |
| V8 | X8 软链也备份 | 目标为软链 ⇒ 备份**记录 `readlink` 目标**；**悬空软链** ⇒ 备份而非被删（第 10 项） |
| V9 | X9 卡片不再误导 | 卡片改为「以 `phase: P8` 提交产出、再单独提交 READY」；并核对 `:89-93` 的 DEBT0013 时序；**断言无脚本依赖"以 READY 提交"**（可机械：grep） |
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
| **碰 `agate/` 触发 SELF-GATE** | **提交信息必须带 `self-gate-review:` 路径或 `self-gate-skip:` 理由**（`AGENTS.md` 工作流第 5 条）。**原设计漏了这条义务** |
| X1 目标若被扩大解读 | 本批**只做任务目录内**；扩大属第 4 批（见 §3 边界声明） |

---

## 7. 与 TAG0042 主体的关系

- 本批是 **TAG0042 的第 0 批**（设计分析 §7）；
- 但它**独立可合并**——不依赖第 1–6 批的任何产物；
- **X9 与第 1 批有交集**（都涉及 phase 语义）：本批只做**文字对齐**，
  第 1 批才改 `agate-next` 行为。**须在 TAG0042 的 P0-brief / 后续产物里记明这条分工**，防重复改。
