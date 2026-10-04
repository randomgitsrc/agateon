# 设计：第 0 批——9 个「现在就是错的」缺陷修复（TAG0042 前置）

> **日期**：2026-10-04 ｜ **性质**：设计（**未实现**），待独立评审
> **归属**：TAG0042「项目形态命令化 + 规则脚本化」的**第 0 批**（设计分析 §7 标注「无前提，改动都很小」）
> **范围**：**只改 agateon 本仓**（其他项目不归本任务）
> **事实基线**：main `4daa60b` 之后 ｜ **设计基线**：**本文所在 commit**
> （⚠️ **刻意不写 SHA**——写了就会随每次修订过期，且「本文自身」自指必然为假。
> 实现前请以 `git log -1 -- <本文件>` 取当时的 commit；这是本设计**第二次**踩该坑：
> first 写 `fa2fc3d`（实为上一版）、再写 `05edb02`（实为父提交）、又写 `a27a1d1`（随即过期）。
> **⇒ 自指引用一律用命令取，不写字面值**——与 `AGENTS.md`「不写死可自主发现的时变数字」同口径。）
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

**⚠️ 两个调用点的语义不同（第五轮评审实测，我复核确认）——须分别写清**：

| 调用点 | 所在循环遍历什么 | 暂存区"没有"会发生吗 | 语义 |
|---|---|---|---|
| **L257** | **已暂存**的 `.state.yaml`（实测 `:224-228` 收集 `staged_all`） | **不会** | **直接读暂存区即可，不需回退** |
| **L590** | 2f「暂存了产出但阶段对不上」检查 | **会**（`task_state` 可能未暂存） | **需回退读工作区 + 提示** |

⇒ **实现时不可两处都加回退逻辑**——那会让 L257 也意外读到工作区（正是 X2 要治的病）。

**⚠️ 暂存区读取失败的语义须定义（针对 L590）**：
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

**⚠️ 第五轮评审的两点补充（我采纳）**：

1. **可见性不够**：绿色 job 日志里的一行 WARNING **几乎没人看**。
   按 ADR-015 手段②，建议**在 agateon 自己的 workflow 里**把该 WARNING 也作为
   **GitHub 注解**（`::warning::`）或 **job summary**（`$GITHUB_STEP_SUMMARY`）输出，
   让它出现在 PR 检查摘要里。
   （`ci-gate-backstop.py` 本身仍只打普通文本，**不依赖任何 CI 平台**——保持其平台无关性。）
2. **「移出必过检查」是被我过早否决的选项**：我引用的教训是「必过检查一旦被 **skip** ⇒ 永久阻断」；
   而**「从必过列表中移除」是分支保护设置，job 照样运行、不进 skip 状态**，不触发那条教训。
   ⇒ **该选项可行**。考虑第 5 批会用 `agate-ci-verify` 替换它，
   **在此之前把一个永远不会失败的检查留作必过，只是一种假保障**
   ⇒ **本批选择「移出必过」**（若保留则须在 PR 里写明理由）。

**风险**：低（输出变化 + 分支保护设置；exit code 不变）。

---

### X4 — P6 复用识别：(**必须改方向**——第五轮评审否决了"继续加词表")

**缺陷（代码实测）**：
```python
return bool(re.search(r"引用\s*P5\s*证据", text))
```
只认中文正序 ⇒ 英文写法、结构化字段**都不认** ⇒ 判定静默失效。

**⚠️ 本项前四轮的设计方向（"把词表加宽"）已被第五轮评审否决，我复核确认。**

**否决证据（语料回放，我逐条复现）**：把"定稿正则"（含 R4 建议补的两条）在两仓回放，
命中里含**明确的误报**：

| 任务 | 命中原文 | 性质 |
|---|---|---|
| **TAG0033** | 「本任务**不走「复用 P5 证据」口径**」 | **否定式**（`不走「」不紧挨关键词，lookbehind 管不到） |
| **TAG0028 / TAG0027 / TAG0020 / TAG0016** | `reuse_allowed` 等 | **审计三态的"描述文字"**，不是复用声明 |
| TAG0018 | 「P5 证据复用判定均通过」 | 含义不明 |

**为何有害**：X4 的消费方（audit 7）对**误报是有害的**——误报 ⇒ 又碰上"P5 之后改过代码"
⇒ 判 `reuse_blocked` ⇒ provenance **exit 1**，把**根本没复用证据**的任务拦下。

**⇒ 根因**：设计已指出「词表即上限」，但**处理方法仍是继续加词表**——
这正是"用自己定义的判据去验证自己定义的判据"的加重版。

**✅ 改后的方向（按外部设计分析的原意，第 0 批此前未采纳）**：

1. **以结构化字段为准**：P6-acceptance frontmatter 增 `p5_evidence_reuse: true|false`，
   用已有的 `agate-md-field-set` 写入；provenance **优先读该字段**。
2. **关键词只用于迁移期**：
   - **字段缺失时**才用关键词，并输出 **WARNING**「请用 `p5_evidence_reuse` 显式声明」；
   - 词表**只放精确的肯定写法**，**删掉** `reuse_(allowed|blocked)` 这类**描述性字面**；
   - 截止版本后不再认关键词。
3. **V4 改为三类断言**（**不再**断言"那 10 个任务都必须被识别"——那等于**把误报写进测试**，
   是 `pv_4_last_paren_taken`「假绿写进测试」的**反向版**）：
   - 字段 `true` ⇒ 判为声明；
   - 字段 `false` ⇒ **正文出现任何关键词也不算声明**（TAG0033 型）；
   - 字段缺失 ⇒ 关键词命中给 **WARNING**。

> **本项与 ADR-015 手段①一致**：结构化字段是"让错误不可能"，
> 继续加词表是"用手段③（要求人写对）"去追一个语义判断。

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

**⚠️ 新发现：P2 **不是唯一**的同款 site（R3 评审查出，我复核确认）**

`gate_p4` 有**同款** `return 2`：
```python
# check-gate.py  gate_p4 内
agent = _md_field_get("agent", p4_review)
if not agent:
    sys.stderr.write("GATE P4: P4-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
    return 2
```
**但 P4 的语义与 P2 **不同**（实测 `phases.yaml`）**：

| phase | `gate_pass_exit` | `return 2` 的实际后果 |
|---|---|---|
| **P2** | **2** | **通过**（fail-open 放行） |
| **P4** | **0** | **∉ pass_set 且 ≠ 1** ⇒ `agate-next.py` 落 **`exit2-resolution` 转人工**（"真暂停/异常"路径） |

⇒ **同一句注释、同一个 `return 2`，在两个 phase 上是两种截然不同的错误行为**
（P2 = 静默放行；P4 = 误判为异常暂停）。**两者都应改为 `return 1`。**

**⇒ 本项范围扩为两个 site**（`gate_p1` 已是 1，无需改；`gate_p2` / `gate_p4` 均改 1）。
> 注：P7/P6.5 的通过码是 0，P3/P5/P6/P8 是 2——**新加 site 时须先查 `gate_pass_exit`**，
> 这正是「`return 2` 在不同 phase 含义不同」这一陷阱的根源（R3 指出）。**该陷阱值得单独登记。**

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

**⚠️ 只改卡片仍依赖记忆——第五轮评审指出，一条很小的机械检查现在就能加（我采纳）**：

> **转换到 READY 时，上一次已提交的 phase 必须是 `P8`**；
> 若 P1 声明了 `internal_only` 从而**合法裁剪了 P8**，则允许是 `P7`。

- **实现位置**：`check-state-transition.py`——它**现在会跳过 READY 目标**（实测 `:249` 的
  `if new_phase in ("", "PAUSED", "READY", "DONE")` ⇒ `GATE SKIP`），这条规则正好**补上该跳过**。
- **存量影响**：只影响**新的**转换提交；存量任务已处于 READY，**不受影响**。
- **证据**：`TAG0037` 实测已是「先 P8、后 READY」两次提交的写法 ⇒ **符合现有习惯**。

**风险**：**改卡片会影响所有用 agateon 的项目**（不限于本仓）。
⇒ 本批**只改卡片文字** + **加上述机械检查**，**不改 `agate-next`**（那属第 1 批）。

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
| V3 | X3 不再**静默**假绿（**覆盖全部 5 个 SKIP 面** + **CI 注解可见**） | **逐面**构造输入（L124 平台未识别 / L132 无 .state.yaml / **L142 无法读取** / **L146 phase 无 gate 需对照** / L162 refactor），断言**每个面**：**exit 0 不变**（保 required check）**且**输出含 **WARNING** 标识（refactor 面可按正文分类保留原文案）。**行为判据，非关键词判据；每面须有改坏即红的负向控制** |
| V4 | X4 **三类断言**（**不再是"10 个都必须识别"**） | ① 字段 `p5_evidence_reuse: true` ⇒ 判为声明；② 字段 `false` ⇒ **正文出现任何关键词也不算声明**（TAG0033 型的否定式与 `reuse_allowed` 型的描述文字都归此类）；③ 字段缺失 ⇒ 关键词命中给 **WARNING**（并提示改用字段）。**禁用**描述性字面（即 `reuse_allowed` / `reuse_blocked` 这类审计状态名） |
| V5 | X5 pipefail 生效 | 命令写作 `set -o pipefail;` 前缀 + 含管道的 cmd（**不是** `executable="bash -o pipefail"`）；cmd 失败 ⇒ **非 0**。**并验证 P3 红灯语义方向（实测为"放宽"）**。**⚠️ 条件性低风险**：现存量 `P3` 键含管道 = **0**（实测），若将来出现则会改变 TDD 判定 ⇒ **须留下该条件的登记** |
| V6 | X6 **两键分别处理** | `design_trivial: false` ⇒ 仍需 **2** 个候选（**非**降为 1）；`follows_existing_pattern:`（**块列表，键行无值**）⇒ **算已声明** ⇒ 可降为 1 |
| V7 | X7 不再返回**通过码**（**两个 site**） | **P2**：缺 `agent` ⇒ **exit 1**（现 2 = P2 的**通过码** ⇒ 静默放行）；**P4**：缺 `agent` ⇒ **exit 1**（现 2 ∉ P4 的 pass_set ⇒ 落 `exit2-resolution` 误判为异常暂停）。断言「**两个 site 都不得返回 `gate_pass_exit`**」 |
| V8 | X8 软链也备份 | 目标为软链 ⇒ 备份**记录 `readlink` 目标**；**悬空软链** ⇒ 备份而非被删（第 10 项） |
| V9 | X9 卡片 + **机械检查** | 除卡片文字外，加 `check-state-transition.py` 规则：**转换到 READY 时上一次已提交 phase 必须是 P8**（合法裁剪 P8 时允许 P7）——补上该脚本当前对 READY 的 `GATE SKIP`。原锚： 卡片改为「以 `phase: P8` 提交产出、再单独提交 READY」；并核对 `:89-93` 的 DEBT0013 时序；**断言无脚本依赖"以 READY 提交"**（可机械：grep） |
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

---

## 8. 实现记录（2026-10-04，实现侧回写）

> 本节由**实现者**回写：设计阶段未预见的事实、V10/V11 的实测结果。
> 设计正文（§1–§7）不改写，本节只做**增量登记**。

### 8.1 V10 存量扫描（实测，均在 `/tmp` 副本上跑，真实仓库 `git status` 为空）

| 项 | 命令 | 实测结果 | 结论 |
|---|---|---|---|
| X1 | `grep -rh '\[PROD_TOUCHED\]' tasks/` 后核对其**行首形式** | 245 行命中，**行首形式 = 0** | **无存量转红**：扫描只判「暂存 diff 中**新增**的行首标记」，存量皆为行内提及（卡片注入文本 / 日志 / 正文）⇒ 即便重写也不命中 |
| X1（行为） | READY 任务普通收尾提交 | **exit 0**（不阻断） | 不误伤收尾提交 |
| X1（行为） | READY + 暂存 `.state.yaml` + 新增行首 `[PROD_TOUCHED]` | **exit 1**（阻断） | ✅ X1 生效（改前为静默跳过） |
| X5 | `parse_gate_commands_block()`（仓库自己的解析器，唯一权威判据）逐 `P2-design.md` | **315 条 / 21 条含管道**；**全部落在 P5 键，P3 键 = 0** | 与设计 §4.2 的更正后数字**完全一致**（「107/1」为误） |
| X6 | `grep` 存量 `P1-requirements.md` 的两键声明 | **仅 TAG0018 一个任务**，且两键均为 `true`/存在 | 判定结果不变 ⇒ **无转红** |
| X7 | 扫 4 类评审文件的 `agent` 字段 | **missing = 0**（全齐备） | **无转红**，无需迁移期 |
| X4 | 兜底词表逐 `P6-acceptance.md` 回放 | **命中 2 个 = 恰好 2 个真声明，0 误报**（TAG0026 / TAG0034） | 见 §8.6 —— **实现偏离设计**：兜底收窄为「粗体独立声明」 |

**⇒ 四项均为"无未解释转红"**，满足 §4.2 的合并前提（V10 判据强度 ①②③ 无一触发）。

> ⚠️ **X5 的 V5 条件登记（设计已要求，此处落实）**：现存量 **P3 键含管道 = 0**，
> 故 X5 目前**不改变任何 P3 红灯判定**；若将来出现 `P3` 键含管道，其 TDD 判定会随之改变。
> 该条件已由 V5 锚覆盖（断言方向为"放宽"）。

### 8.2 V11 全量回归（实测）

```
pytest agate/tests/ -n auto -p no:randomly   # 排除已知环境失败（opencode 未安装）
→ 2596 passed, 0 failed, 2 skipped
```

> ⚠️ **本小节初版记的是「5 failed, 2575 passed」——那是 X2/X9 测试修好之前的中间态**，
> 已被后续修复消解；下表保留是为了交代那 5 个失败各自的去向（勿当作当前状态）。

| 失败项 | 归属 | 处置 |
|---|---|---|
| `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` | **环境**（`opencode` 不在 PATH） | 已在 `origin/main` 复现 ⇒ **非回归**，不处理 |
| `test_check_gate_p4_maintainability.py::test_g5_legacy_failure_paths_unchanged` | **X7 引起** | 见 §8.3 |
| `test_check_gate_p4_maintainability.py::test_g7_no_new_return_2_from_new_step` | **X7 引起** | 见 §8.3 |
| `test_tag0027_b1_agate_next_cli.py::test_bdd_8_non_pass_exit_writes_exit2_resolution` | **X7 引起** | 见 §8.4 |
| `test_tag0027_b1_agate_next_cli.py::test_bdd_8_exit2_resolution_frontmatter_machine_readable` | **X7 引起** | 见 §8.4 |

（其余三项：`consistency` **0 ERROR**、`ruff` 干净、structure S0–S6 全 OK。）

### 8.3 ⚠️ 设计未预见（一）：X7 与两处**既有守护断言**冲突

`test_check_gate_p4_maintainability.py` 的两条断言**把 P4 缺 `agent` → exit 2 当作基线**固定下来：

- `test_g5_legacy_failure_paths_unchanged`（`assert r5.returncode == 2`）
- `test_g7_no_new_return_2_from_new_step`（`assert result_c.returncode == 2`）

**但它们记录的是"当时的既有行为"，不是"P4 应有的行为"**——证据（时间线）：

| 事实 | commit | 日期 |
|---|---|---|
| P4 缺 `agent` → `return 2` 出现（**机械移植 shell→py**，TAG0010） | `3547b62` | 2026-08-15 |
| `gate_pass_exit` / pass_set 机制引入（TAG0027） | `fcf3fd2` | 2026-09-03 |

⇒ `return 2` **早于**它被赋予「按 phase 而变」的语义约 3 周，**并非为 P4 设计**；
守护测试（TAG0026）晚于机制、却按"现状快照"写断言。
**故这是"守护测试把缺陷记为基线"，应改测试而非回退 X7**（设计 §X7 的判据成立）。

**处置**：把两处断言由 `== 2` 改为 `== 1`，**守护目的不变**（"新步骤不得新增 `return 2`"仍成立）。

### 8.4 ⚠️ 设计未预见（二）：X7 之后 **P4 不再存在任何合法 exit 2 路径**

`test_tag0027_b1_agate_next_cli.py` 的两条 BDD-8 用例**借用**"P4 缺 `agent`"作为
"真暂停（exit ∉ pass_set 且 ≠ 1）"的**真实 gate 锚点**（其 docstring 明写该锚点）。
X7 把该处改为 1 后，锚点消失：

- 实测 `gate_p4` 现有返回**只有 0 与 1**，**无 `return 2`**；
- 且 P0/P1/P2/P3/P5/P6/P8 的 `gate_pass_exit` **都是 2**（2 = 通过），
  P7/P6.5 虽 pass_exit=0 但其 `gate_p*` **不含 `return 2`**。

**⇒ 全仓已无任何 gate 能产生"非 pass 的 exit 2"**，
`agate-next` 的"真暂停"分支**经真实 gate 不可达**。

**处置**（本批）：BDD-8 用例改用**受控输入**触发 exit-2 分支（不依赖真实 gate 的缺口），
以保留该分支的覆盖；**该"分支不可达"本身登记为独立事项**，不在本批改 `agate-next`
（属第 1 批 phase 语义统一的范围，见 §7 边界）。

### 8.4b ⚠️ X9 的存量面比设计所述更广（实测）

设计称 X9「**只影响新的转换提交；存量任务已处于 READY，不受影响**」。就"不会再触发阻断"
这一点成立（存量不产生新提交），**但它掩盖了一个事实**：新规则比历史实践**严格得多**。

逐任务核对其 `READY` 提交的**前序已提交 phase**（实测 43 个任务中 35 个有可判定的 READY 提交）：

| 前序 phase | 任务数 | 新规则下 | 说明 |
|---|---|---|---|
| **P8** | **9** | ✅ 合法 | 正是 X9 目标写法（TAG0037 即此） |
| **P7** | **17** | ❌ 会被拦 | 除声明 `internal_only` 外不再放行 |
| READY（同一次提交内改到 READY） | **9** | ❌ 会被拦 | 无 P8 前序 |

⇒ **26/35 的存量任务用的是新规则禁止的写法**。

**这是"历史实践即缺陷"，不是"新规则过严"**——依据：

- 这 17 个 P7→READY 任务中核对的样本（`TAG0014`、`TAG0021`）在 P1 里明确声明了
  `phases: [P0…P7, P8]`（**P8 未被裁剪**），却跳过了 P8 直接进 READY；
- 而协议规定裁剪 P8 必须有 `internal_only: true`（`WORKFLOW.md` 的 P8 行 +
  `check-pruning.py`），实测这 17 个**全部未声明** `internal_only`。
- ⇒ 它们正是 X9 要修的那个洞：**P8 在声明范围内却没跑 gate_p8**。

**结论**：无"未解释转红"——26 个存量全部归入 §4.2 判据的 ②「本批有意收紧且已在本设计登记」。
**不改存量数据**（frozen 快照，重写历史提交无意义），但**新任务必须遵守新规则**。

### 8.5 实现范围边界（重申）

- X1 只做到「**所有阶段的、任务目录内的** diff 都扫」；"所有文件都扫"属第 4 批。
- X9 只做**卡片文字 + 机械规则**，不改 `agate-next` 行为（属第 1 批）。

### 8.6 ⚠️ 实现偏离设计（一）：X4 兜底词表**收窄**（独立评审已复核认可）

**设计说的是**（§X4 目标行为 2）："词表**只放精确的肯定写法**，**删掉** `reuse_(allowed|blocked)`
这类**描述性字面**"——即设计仍打算保留一个**关键词兜底**，只是把词表"收精确"。

**实现时按该口径做了一版，实测发现"精确的肯定写法"本身仍会误报 3 例**（逐条实测）：

| 任务 | 原文 | 性质 |
|---|---|---|
| **TAG0033** | `### 2.6 P5 证据复用判定`（**节标题**）+ 正文「本任务**不走**「复用 P5 证据」口径」 | 标题命中 + **否定式** |
| **TAG0019** | 「引用 P5 证据说明：…**未在本报告作"复用"声明**」 | **否定式** |
| **TAG0018** | 「…P5 证据复用**判定均通过**」 | 描述**审计跑了**，非复用声明 |

**误报为何有害**（设计已论证）：audit 7 对误报不宽容 ⇒ 又碰上"P5 之后改过代码"就判
`reuse_blocked` ⇒ **把根本没复用的任务拦下**。

**⇒ 实现的偏离**：兜底**只认「粗体独立声明」一种高置信形态**：
```
^\s*[-*]?\s*\*\*\s*(?:引用\s*P5\s*证据|P5\s*证据复用)\s*[*（(:：]
```
**实测：命中 2 个 = 恰好 2 个真声明（TAG0026 / TAG0034）、0 误报。**
（改前的旧正则命中真声明 **0 个**——5 个相关文件里的真声明**全是倒序写法**。）

**独立评审的判定（采纳）**：**"defensible and the right trade"** —— 因为漏判现在是
**朝安全方向失败**：漏 ⇒ 视为"未声明" ⇒ 任务须自己产出 `regression.log`（多跑一次而已）；
而误报 ⇒ 硬 exit 1 拦下**从未声明复用**的任务。且**召回的正解是结构化字段**，该字段已落地。
评审同时指出代价（据实登记）：**会漏掉 `- P5 证据复用：…`（无粗体）等朴素写法**。

**落盘**：3 个误报已固化为**反例测试**（`test_x4_negation_and_headings_are_not_declarations`），
防将来有人"顺手把词表加宽"。

### 8.7 ⚠️ 实现自纠（二）：X7 测试的 P4 参数**曾是空转**（独立评审查出，已修）

**缺陷**：`test_x7_missing_agent_returns_not_pass[P4]` 原断言 `got != pass_exit[phase]`。
P4 的 `gate_pass_exit` = **0**、缺陷值 = **2** ⇒ `2 != 0` 为**真** ⇒
**把 X7 改回缺陷值，该参数照样通过**（实测确认：`[P2]` 变红、`[P4]` 仍绿）。
⇒ 这个宣称"两个 site 都不得返回通过码"的参数化用例，**实际只覆盖了 P2**。

**根因**：断言锚在**代理判据**（"不等于通过码"）而非**期望行为**（"返回未通过码 1"）。
这是本项目反复出现的同一类错误——**用自己定义的判据去验证自己定义的判据**。

**已修**：断言改为 `assert got == 1`（锚在期望行为上）。**改坏即红复验**：
在"两处都改回 2"的副本上，`[P2]` 与 `[P4]` **均变红**。

> 注：P4 的**代码**修复本身是正确的，且另有 2 处既有守护断言（`test_check_gate_p4_maintainability.py`
> 的 g5b/g7）确实能抓住它——**只有这个新用例是空转的**。据实登记，不掩饰。
