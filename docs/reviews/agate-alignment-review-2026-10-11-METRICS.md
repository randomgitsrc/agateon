---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: RM-AG0074 ① / RM-AG0095 ① 的 summary 面——账本 state_transition 算阶段耗时（measure_duration 优先账本）+ agate-summary 效率度量节
files_changed:
  - CHANGELOG.md
  - agate-workspace/roadmap/roadmap.md
  - agate/scripts/README.md
  - agate/scripts/agate-dispatch-cost.py
  - agate/scripts/agate-summary.py
  - agate/tests/unit/test_agate_dispatch_cost.py
---

# 协议-脚本对齐审查

**分支**：`feat/phase-duration-metrics`（未提交，改动在工作区；`git diff` 可见）
**审查对象**：RM-AG0074 ①（+ RM-AG0095 ①）的 summary 面落地
**独立复核前提修正**：RM 原注「① 耗时一面**须先让账本记全阶段 entry/exit**，未做」——本次独立核实**该前提已由 TAG0050 A3 落地**（见 A1 与该前提的证据强度）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（输出头 RM id 写错；`agate-dispatch-cost.py` 模块 docstring 未随「优先账本」同步） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`agate/scripts/README.md:158` 表行破损；dispatch-cost 模块 docstring 陈旧） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（A3a：README 行破损；A3b：`agate-summary.py` 内「启动建议 1. 第一行」措辞与新增前置节自相矛盾） |
| A4 | 测试覆盖 | **ALIGNED**（新增 2 用例实跑绿；全量实跑见下）——⚠️ 遗留未覆盖面已记账（precedence 分支 / 静默降级无用例） |
| A4b | 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054） | **ALIGNED**——**经实测无既有用例转红；无需更新夹具**（空清单，见 A4b） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（`agate-summary.py` 启动建议文本陈旧；`UPGRADING.md` 新版本章节按仓库惯例属发版清单，本轮非缺陷但须记账） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9 PASS；无新增协议规则/脚本 ⇒ 无需新锚点） |
| A7 | 设计原则一致性 | **ALIGNED**（纯增量，与 RM 意图一致；无 ADR 冲突） |
| A8 | 声称-命令绑定 | **MISALIGNED**（「history 9/79」为**另一语料**数字、本仓不可复现（本仓 0/43）；输出头 RM id 声称错误） |

**总判**：**作为代码核心，逻辑正确、可复核、诚实（不编造）；当前状态不建议直接 commit**——阻断项集中在**引用/文档/文本层**（均属快修，非逻辑缺陷）。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（roadmap RM-AG0074 本轮更新，`agate-workspace/roadmap/roadmap.md:96`）：
> 本轮：`agate-dispatch-cost.py::measure_duration` **优先账本**…；`agate-summary.py` 新增**效率度量节**（可算耗时 18/43…）。**token / 步数明确标注不可得**（harness 不报，不猜）。

**脚本实现**：
- `agate-dispatch-cost.py:141-143`：`from_ledger = _duration_from_ledger(task_dir); if from_ledger is not None: return from_ledger`（优先账本）。
- `agate-dispatch-cost.py:81-135`：`_duration_from_ledger` 读 `gate-events.jsonl` 的 `state_transition`，要求 `>=2` 条且 `ts` 可解析，返回 `duration_seconds` + `phase_spans`。
- `agate-summary.py:377-418`：`_efficiency_lines` 输出「可算耗时 N/M」+ 按耗时前 10 的「任务/耗时(h)/派发份数/上下文 KiB」+「token / 步数**不可得**」。

**差异（MISALIGNED）**：
1. **输出头 RM id 写错**——`agate-summary.py:404` 打印
   `"=== 效率度量（RM-AG0074/0085 ①：阶段耗时 + 派发成本）==="`。
   同函数 docstring（`:378`）写的是正确的 `RM-AG0095 ①`。**RM-AG0085 是无关条目**（roadmap:107「gate_p2 骨架声明判定是子串匹配」）。⇒ 面向用户输出面循环引用了错误 id。
2. **模块 docstring 与实现背离**——`agate-dispatch-cost.py` 顶部仍写（`:12-17`）「设计原则 2. **拒绝编造**——阶段耗时**不可靠可算**：`.state.yaml` 的 `history`…」，`:23`「`duration_*` —— 阶段耗时，**仅在账本覆盖完整时**给出」。新实现已改为「优先账本 + 回退 history」，模块级口径未同步（仅函数级 docstring 同步）。

**建议**：`:404` 改 `RM-AG0095`；模块 docstring 的「设计原则 / 度量口径」两段补「账本优先」。

### A2: 脚本→文档对齐

**脚本变更**：`measure_duration` 返回值新增 `duration_source`（`"ledger"`/`"history"`）与 `phase_spans`；`agate-summary.py` 新增依赖 `agate-dispatch-cost.py`。

**文档**：
- `CHANGELOG.md:13-22` 已记录（`### 新增`，keep-a-changelog 顺序正确）✓。
- `agate/scripts/README.md:158` **表行破损（MISALIGNED）**：新增段落在第 2 列的 closing `|` **之后**——
  ```
  | `agate-summary.py` | …（指向已装但非 current 的版本）|；并输出**效率度量节**（…不可得）
  ```
  实测 `ends_with_pipe=False`、`raw_n_pipes=3`。该行因此形成**溢出的第 3 个 cell**且**不以 `|` 结尾** ⇒ 在 GFM 渲染下表头只有 2 列，**新增描述多半不显示**。正确写法应把新增文字插到第 2 列内、行尾补 `|`：
  `| \`agate-summary.py\` | …（…版本）**；并输出效率度量节**（…不可得）|`。

**建议**：修 README 表行；dispatch-cost 模块 docstring 同步（同 A1.2）。

### A3: 一致性连锁 + 反向传播

**A3a（已知衍生改动）**：
| 文件 | 状态 |
|------|------|
| `CHANGELOG.md` | ✓ 已更新 |
| `agate-workspace/roadmap/roadmap.md` | ✓ 已更新（RM-AG0074 行；**列数 7 = 表头 7，未漂移**，无 RM-AG0043 隐形风险） |
| `agate/scripts/README.md` | ⚠️ 已更新但**行破损**（见 A2） |
| `agate/tests/unit/test_agate_dispatch_cost.py` | ✓ 已更新（+2 用例） |
| `agate/tests/README.md` | ✓ 无需改（`:112` 已有「派发成本度量（RM-AG0074）→ unit/test_agate_dispatch_cost.py」映射） |

**A3b（主动推断「应被影响但未在 diff 中」的文件）**：
1. `agate-summary.py`**自身**（`：474`）「1. 第一行：上面这一段（确认协议版本 + 防护机制就位）」——本次把效率节**前置**到 `lines` 首位（`:456-457` `[*_efficiency_lines(...), "=== agate 当前状态 ==="…]`）⇒ **「第一行」与「上面这一段」现在指效率节，而非版本/防护块**。该自述文本与实现自相矛盾（MISALIGNED）。
2. `agate/SETUP.md:74` / `agate/orchestrator-template.md:74` / `docs/guides/worktree-dogfooding-guide.md` 等把 `agate-summary.py` 描述为「确认协议版本 / hook 已装」——仍**语义成立**（版本块仍在），但用户/编排者若按「第一行」读取会先看到效率节。是否顺带更新这些文档属**传播范围判断**（见 A5）。
3. `agate/UPGRADING.md`：本轮为**新增能力、无破坏性变更**；按仓库「版本发布清单」惯例，章节在**发版时**补（不属本轮缺陷，但应记账）。

### A4: 测试覆盖

**新增用例**（`test_agate_dispatch_cost.py`）：
- `test_rm_ag0074_duration_from_ledger_preferred`：账本优先 + `history` 缺失仍可算（1.5h）+ `<2` 事件回退不可算。**直接单测 `measure_duration`**（不依赖 CLI）。
- `test_rm_ag0074_summary_reports_efficiency_section`：`agate-summary.py` 在 `cwd=proj` 下输出「效率度量 / T001 / 2.0 / token 不可得」。**走 CLI**。

**实跑输出**（本机，2026-10-11）：
- 目标文件：`python3 -m pytest agate/tests/unit/test_agate_dispatch_cost.py -q` → **`13 passed in 0.60s`**（= 11 既有 + 2 新）。
- 全量：`python3 -m pytest agate/tests/ -n auto --reruns 1 -q` → **`1 failed, 2920 passed, 2 skipped, 1 rerun in 134.14s`**。
  - 唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，**环境性**：本机 `opencode` CLI 的 `debug` 只有子命令 `agents`（无 `agent`）⇒ `Unknown subcommand "agent"`（`opencode debug --help` 实测印证）。该用例不触碰本次改动文件（`grep` 实测：`test_setup_agate_dir.py` 只引 `agate-summary.py` 的启动建议路径，无 `agate-dispatch-cost`/`效率度量`）。**不称「全绿」**。

**遗留未覆盖面（记账，低风险）**：
- 「账本与 history **都能算且数值不同** ⇒ 取账本」的 **precedence 分支无用例**。实测本仓**无此重叠数据**（见 A8），无法用真实数据覆盖；建议造一条同时含账本与 history 的夹具。
- `agate-summary.py` 的**静默降级**无用例（`agate-dispatch-cost.py` 缺失 / 加载异常 / 非项目根 cwd）。
- 结论 **ALIGNED**（新主路径有测试），以上为增强建议。

### A4b: 闭合后既有测试转红 + 夹具更新清单

- **经实测无既有用例转红**。理由：既有 11 条 dispatch-cost 用例**无一创建 `gate-events.jsonl`**（逐条读 `test_agate_dispatch_cost.py:57-243` 确认）⇒ 新增的「优先账本」路径不在这些用例中触发 ⇒ 语义不变（实跑 13 passed 印证）。
- `agate-summary.py` 的既有用例（`test_agate_summary.py`、`test_setup_agate_dir.py`）断言均为**子串**，且跑在这些用例的 cwd = 临时项目目录（**无** `agate-workspace/tasks`）⇒ 效率节为空、输出与改动前一致 ⇒ 不转红。
- **无需更新夹具**（空清单）。

### A5: 下游影响 + 文档传播

- **破坏性变更**：无（纯增量；`measure_duration` 仅**新增键**，`measure()` spread、`_human()` 只读旧键 ⇒ 既有形状不破）。
- **CHANGELOG**：已标注 ✓。
- **文档传播（MISALIGNED）**：`agate-summary.py:474` 的「第一行」自述须修（或把效率节移到状态块**之后**）；`SETUP.md`/`orchestrator-template.md` 的「确认协议版本」描述与新前置节并存，建议复核是否要一句话注明「summary 现首屏含效率度量」。
- `UPGRADING.md` 新版本章节：**发版时**补（本轮非缺陷，记账）。

### A6: 锚点表覆盖

`python3 agate/scripts/check-protocol-consistency.py` → **CHECK 9 协议-脚本结构对齐 PASS**，整体 **0 ERROR**（432 条为按设计不改的 frozen WARNING，EXIT=0）。本次**未新增协议规则 / 未新增 CHECK / 未新增脚本**（只在既有脚本加函数）⇒ **无需更新 CHECK 9 锚点表**。结论 **ALIGNED**。

### A7: 设计原则一致性

- 变更性质：**观测层增量**，不改状态机、不改 gate 判定、不改 `{key}_timeout_seconds` 等声明面。
- 与 `agate/adr.md` 相关条目核对：adr:259/317/354/478 均为「`agate-summary.py` 版本解析/接入产物漂移」——本变更**不改**这些语义；无 ADR 与新行为冲突。
- 「优先账本」是基于「账本随 git 版本化 + 哈希链防改写，history 疑手写」的证据取舍，与**已知 ADR 无冲突**。若要固化为长期契约，可考虑补一条 ADR（非必须）。结论 **ALIGNED**。

### A8: 声称-命令绑定

| 声称 | 产出它的命令 | 结论 |
|------|--------------|------|
| 账本 **22/43** 个任务有 `state_transition` | 遍历 `agate-workspace/tasks/*/gate-events.jsonl` 计 `event==state_transition && ts` | ✅ **22/43**（但其中 **4 个**仅 1 条合成 `''->P0`，见下） |
| 可算耗时 **18/43** | `agate/scripts/agate-summary.py`（或 `measure()` 遍历） | ✅ **18/43** |
| `TAG0050 56.3h / 75 份 / 1346 KiB` | `python3 agate/scripts/agate-dispatch-cost.py TAG0050-…` | ✅ `202760 s`=56.3h / 75 / 1346 KiB |
| `TAG0042 48.0h / 50 份` | 同上 | ✅ `172675 s`=48.0h / 50 |
| hook `2h.1c` **每次 phase 变更**写 `state_transition`，含 PAUSED/READY/DONE | 读 `pre-commit-gate.py:888-897`（`:912` 的 `continue` **之后**才跳过非 gate 阶段） | ✅ **代码级为真**；实证见下 |
| history 口径可算 **9/79** | 本仓：对 43 任务算 history 覆盖 → **0/43**（全部 `.state.yaml` **无 `history` 键**） | ❌ **本仓不可复现**：9/79 系**另一（两仓）语料**数字、**分母不同**（43 vs 79）。建议标明语料或本仓改记 **0/43**。 |

**A8 结论 MISALIGNED**：① 「9/79」与「22/43」混用不同语料/分母，且本仓不可复核（本仓 history=0/43）——应限定语料或替换；② 「RM-AG0074/0085」为错误 id 声称（见 A1）。

---

## 五项重点结论

### 1. 前提更正的证据强度 —— 成立（证据充分）

- **代码级**：`pre-commit-gate.py:888-897` 在 `if phase_changed:` 下 `append_event({event:"state_transition", phase, from: old_phase or "", to: phase})`，且该段位于 `:911-912`「`if phase in (PAUSED,READY,DONE): continue`」**之前** ⇒ **进入 PAUSED/READY/DONE 的转换确被记录**。`from`/`to`/`phase` 齐备；`ts` 由 `append_event`（`agate_common.py:526-561`）自动补 **UTC ISO8601 微秒** + `prev_hash` 链。
- **链连贯性（抽 3-5 样本）**：`ts` **严格递增**（本仓所有 `>=2` 事件任务 `ts_ok=True`）；但 **`from`/`to` 链非严格连贯**——多数任务**每次转移出现两次**（例：`TAG0030` 16 事件 = 8 转移 ×2；`TAG0050` 的 `P1->P2` 出现 3 次，`TAG0042` 的 `P0->P1`/`P3->P4` 各 2 次）。⇒ 因 `_duration_from_ledger` **按 `ts` 排序、不依赖链连贯**，总时长仍可算；但 `phase_spans` 会含**近零重复段**（低影响，见第 2 点）。
- **22/43 与 18/43 之差 = 4**：解释成立。**TAG0038/0039/0040/0041** 各仅 **1 条** `''->P0`（均 `2026-09-29T04:54` 前后 ~0.6s 内批量写入 → 疑似迁移播种），`_duration_from_ledger` 要求 `>=2` 条 ⇒ 这 4 个不可算。⇒ 「22/43 有事件」中 **4 个并非真实转移链**，措辞宜注明。
- **PAUSED/READY/DONE 实证**：本仓仅 **TAG0033 / TAG0034** 两任务的账本含这些状态（代码级保证 + 实证样本存在）。判：**前提更正证据充分**。

### 2. `measure_duration` 的等价性与回归 —— 既有回归绿；precedence 无真实数据；`to` 归属正确但末段丢失

- **既有 11 用例仍绿**（实跑 13 passed 含 2 新）。
- **「两者都能算且不同 ⇒ 取账本」在本仓无可观测量**：本仓 **43/43 任务 `.state.yaml` 无 `history` 键** ⇒ history 分支**完全失效（0/43）**；18/43 **全部**来自账本，账本与 history **重叠 = 0**。故本仓「优先账本」**无实际取值冲突**；该取舍**合理**（账本是 hook 判定锚点、`append_event` 哈希链防改写；history 在本仓根本不存），但**无真实数据/无用例**覆盖 precedence。
- **`phase_spans` 的 phase 归属**：按 `e0.get("to")` 归属——对「两转移之间的区间」是**正确**的（进入 P1 到进入 P2 之间的时长确属 P1）。但**最后一个事件之后到「现在」的末段无下游事件可闭合 ⇒ 末阶段（含 DONE）耗时丢失**（实测 `TAG0050` 14 事件 → 13 段，末段即被丢弃）。属**固有**（需 `now`/DONE 收尾），且 **`phase_spans` 当前无展示**（见第 3 点），影响低。
- **`duration_source`/`phase_spans` 不破坏既有形状**：`measure()` spread、`_human()` 只读 `duration_available/seconds/reason` ⇒ 无消费方因新增键受影响。

### 3. `agate-summary` 新节的稳健性 —— 性能无忧；**静默降级**与 **cwd 依赖**是弱点

- **性能**：全量 43 任务跑 `agate-summary.py` 实测 **0.416s**（读账本 + 统计上下文体积）⇒ 无性能问题。
- **降级（MISALIGNED 倾向）**：`_efficiency_lines`（`:385-389`）在 ①`tasks_root` 不存在、②`agate-dispatch-cost.py` 缺失（`_load_dispatch_cost` 返 `None`）、③`spec.loader.exec_module` 抛任何异常（`except Exception`）、④ 单任务 `measure()` 抛异常（`except Exception: continue`）时**静默返回 `[]`**——**不打印任何提示**。这与本仓刚确立的「跳过与通过可区分」（RM-AG0077）纪律相悖。
- **`os.getcwd()` 作项目根不可靠**：从**非项目根**调用时（实测 `cd /tmp` 与 `cd agate/`）效率节**静默消失**，而版本/防护块仍正常（它不依赖 cwd）——用户会看到「半截」输出且**无从知道少了什么**。文档化用法是 `python3 ~/.agate/scripts/agate-summary.py`，但未规定 cwd。
- **放置位置**：效率节被置于**最顶**，使 summary 的**首屏从「版本/防护」变成「效率」**，与 `:474`「第一行…确认协议版本 + 防护机制就位」自相矛盾（见 A3/A5）。

### 4. 诚实性 —— 「不编造」到位；但「静默降级」与诚实性精神有张力

- **两种口径都不可用**：`measure_duration` 返 `{"duration_available": False, "duration_seconds": None, "duration_reason": …}`（`agate-dispatch-cost.py:145-157,177-206`）——**真做到不编造**，且 `test_dc_5`/`test_dc_11` 守护「不可算须明说、不得给数值」。
- **token/步数**：summary 明确打印「⚠️ token / 步数**不可得**（harness 不报）——本工具不猜、不编造」（`:416`），`test_rm_ag0074_summary_reports_efficiency_section` 断言「token」「不可得」。**标注明确** ✓。
- **张力点**：当**整个节**因脚本缺失/cwd 不对而消失时，用户看不到「本应有而未显示」——**这是静默，不是诚实标注**。建议：脚本缺失/cwd 不对时打印一行显式跳过原因（「效率度量：跳过（未找到 `agate-workspace/tasks` / `agate-dispatch-cost.py`）」）。

### 5. A4b + A8 —— 实跑数字与声称绑定

- **实跑（`-n auto --reruns 1`）**：**1 failed, 2920 passed, 2 skipped, 1 rerun in 134.14s**；唯一 failed 为环境性（`opencode debug agent` 子命令不存在）。目标文件单跑 **13 passed**。**勿称「全绿」**。
- **A4b**：**无既有用例转红、无需改夹具**（依据见 A4b 节）。
- **A8**：见上表——**「9/79」本仓不可复现（本仓 0/43）**、**「RM-AG0085」为错 id**，两条须处置。

---

## 是否可 commit

**结论：不建议直接 commit——存在 MISALIGNED 阻断项（均属快修，非逻辑缺陷）。**

**必须修（MISALIGNED，逐条）**：
1. `agate-summary.py:404`：`RM-AG0074/0085` → **`RM-AG0074/0095`**（A1/A8，输出面错 id）。
2. `agate/scripts/README.md:158`：修复**表行破损**——把「；并输出效率度量节…」移入第 2 列内、行尾补 `|`（A2/A3）。
3. `agate-dispatch-cost.py` **模块 docstring**（`:12-23`）：同步「优先账本 + 回退 history」口径（A1/A2）。
4. `agate-summary.py:474`「1. 第一行：上面这一段（确认协议版本 + 防护机制就位）」：**改措辞**，或把 `_efficiency_lines()` 移到状态块**之后**（A3/A5）。
5. A8 的「history 9/79」：**限定语料**（注明为两仓 79 任务的历史测量）或本仓改记 **0/43**。

**建议（非阻断）**：
- `_efficiency_lines` 的**静默降级**改为**显式跳过原因**（对齐 RM-AG0077 纪律）。
- 补一条「账本 + history 都存在」的 precedence 用例（造夹具）。
- 若希望 `phase_spans` 成为可用能力，需在 summary/`--json` 中**展示**（当前仅返回、无消费方）。
- 发版时补 `UPGRADING.md` 章节（按仓库惯例「无破坏性变更也写」）。

**共同点**：以上均不影响「账本优先算耗时 + 诚实标注不可算」这一核心逻辑——该核心**正确、已测、可复核**；修复引用/文档/文本层后即可提交。

---

## 人工验收清单自检

- [x] Write 前检查目标路径（报告文件不存在 ⇒ 直接写；留痕文件已 `rm -f` 起空）
- [x] 报告含 A1-A8 + A4b，每项有结论
- [x] MISALIGNED 项均有差异描述 + 建议方向
- [x] 无 NEEDS_HUMAN_REVIEW 结论（本报告不产生需 `[HUMAN_CONFIRMED]` 的项）
- [x] 报告落盘 `docs/reviews/agate-alignment-review-2026-10-11-METRICS.md`
