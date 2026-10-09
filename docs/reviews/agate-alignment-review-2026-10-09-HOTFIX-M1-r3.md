---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: HOTFIX/M-1-state-machine 第 3 轮——A6 补 CHECK 9「前向跨阶」锚点；A7 最小对齐（check-pruning 补 P1 不可裁 + 两脚本模块级 NON_PRUNABLE_PHASES + 等价守护测试）+ RM-AG0110 登记
files_changed:
  - agate/scripts/check-protocol-consistency.py
  - agate/scripts/check-pruning.py
  - agate/scripts/check-state-transition.py
  - agate-workspace/roadmap/roadmap.md
  - agate/tests/unit/test_non_prunable_phases_guard.py
---

# 协议-脚本对齐审查（第 3 轮：A6/A7 实施验证）

**审查对象**：分支 `hotfix/M-1-state-machine`（工作区未提交）。本轮新增/变更 4 文件 + 1 新测试。
**意图**：验证用户裁决后实施的 A6（CHECK 9 锚点）与 A7（不可裁剪集最小对齐 + 等价守护 + RM）。
**前轮**：第 1 轮（M-1 三 P0）、第 2 轮（P0 核实 + A1–A8）。本轮聚焦 A6/A7 逐条核实 + 增量 A1–A8。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（新：`state-machine.md` 裁剪条件块缺 P1，见 A1-1） |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（同 A1-1 根因 + tests/README 映射可选） |
| A4 | 测试覆盖 | **MISALIGNED**（新：check-pruning 的 P1 拦截无行为用例，见 A4-1） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（含 1 条可选 CHANGELOG 补记） |
| A6 | 锚点表覆盖 | **ALIGNED**（4 项核实全过） |
| A7 | 设计原则一致性 | **ALIGNED**（最小对齐 + 等价守护已落地；残余风险已由 RM-AG0110 承接） |
| A8 | 声称-命令绑定 | **ALIGNED** |

> **一句话**：A6、A7 的实施**均正确且经独立复现**；但 A7 把 P1 加入 `check-pruning.py` 后，`state-machine.md:201-208`「裁剪条件（hook 验证）」列表**未同步补 P1**（新 A1/A3 MISALIGNED），且该 P1 拦截分支**无行为测试**（新 A4 MISALIGNED）。两处均为一行的机械补齐。

---

## A6 逐条核实 —— ✅ ALIGNED

| 核实项 | 方法 | 结论 |
|---|---|---|
| ① 锚点结构合法（同 schema） | `ast` 解析 `SCRIPT_ALIGNMENT_ANCHORS`（53 条）→ key schema 仅 `('desc','keywords','script')`（多数）与 `('callers','desc','keywords','script')`（少数） | ✅ 新条目 `check-protocol-consistency.py:618-622` 恰为 `desc/script/keywords`，与同脚本既有 3 条一致 |
| ② 关键词确实出现在脚本 | `grep -c "前向跨阶" agate/scripts/check-state-transition.py` → **2**（注释 + 错误消息 `:472`） | ✅ `check_script_alignment:870-875` 的「keyword ∈ script text」满足（否则只会 WARN） |
| ③ 仍 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | ✅ **CHECK 9 PASS**，0 ERROR，410 frozen WARNING（与第 2 轮逐项一致，未新增） |
| ④ 无重复/冲突锚点 | 53 锚点无重复 `desc`；关键词 `前向跨阶` 全局仅出现 1 次；`check-state-transition.py` 4 条锚点关键词互不重叠（`MAX_RETRY`/`diff,phase_num`/`前向跨阶`/`RM-AG0042`） | ✅ 无冲突 |

**结论**：A6 **ALIGNED**。第 2 轮 A6 的 NEEDS_HUMAN_REVIEW 已闭环。

---

## A7 逐条核实 —— ✅ ALIGNED（实施正确，但引出 2 个新缺口，见下）

### ① 两处集合逐字一致、均含 P1 —— ✅

- `check-pruning.py:24`：`NON_PRUNABLE_PHASES = ("P1", "P2", "P4", "P5", "P6")`（tuple）
- `check-state-transition.py:48`：`NON_PRUNABLE_PHASES = frozenset({"P1", "P2", "P4", "P5", "P6"})`（frozenset）
- 实测：`set(pruning) == set(trans) == {"P1","P2","P4","P5","P6"}`，两者均含 P1。
- **措辞注记**：注释写「**逐字一致**」——元素序列逐字相同，但**容器类型不同**（tuple vs frozenset），严格说不是字符级相同；等价守护按 `set()` 比较，语义无碍。属措辞细节，非缺陷。

### ② P1 项真的会拦 + 既有 4 条文案未削弱 —— ✅

- **实测（scratch 一次性副本）**：构造 `phases: [P2,P3,P4,P5,P6,P7,P8]`（缺 P1）→ `check-pruning.py` **rc=1**，stderr：`GATE PRUNING: 裁剪条件不满足： - P1 不可裁剪——需求基线是全流程脊梁，无论任务大小都需建立`。✅
- **既有 4 条文案**：`_NON_PRUNABLE_REASONS`（`:26-36`）逐条与重构前原文一致（P2 含「design_trivial / follows_existing_pattern…」、P6 含「no_behavior_change…」、P4/P5 原文照旧）；仍 `errors.append(...)` → **ERROR 级**（exit 1）。`test_check_pruning.py` 中 4 条断言（`P2/P6/P4/P5 不可裁剪`）全部通过。✅

### ③ 错误顺序/数量变化对既有用例的影响 —— ✅ 无影响

- **顺序**：改前逐条追加顺序 `P2,P6,P4,P5`；改后 `for _p in NON_PRUNABLE_PHASES` → `P1,P2,P4,P5,P6`（**多一条 P1**，其余相对顺序 P2→P4→P5→P6 不变）。
- **原始实跑输出**：
  ```
  $ python3 -m pytest agate/tests/unit/test_check_pruning.py -q -p no:cacheprovider
  ..............................                                           [100%]
  30 passed in 3.91s
  ```
- 核查：`test_check_pruning.py` 无任何用例断言错误**数量**或**顺序**（无 `len(errors)`/`.index`），只做 `"<Pn> 不可裁剪" in output` 子串断言 → 顺序/计数变化**不触及**任何既有用例。✅

### ④ 守护测试真能抓到漂移 —— ✅

**scratch 副本（`/tmp/opencode/a7scratch`，`AGATE_ROOT` 指向副本；创建→操作→清理同一调用，未污染真实仓库）**：
```
基线（未改副本）          → 1 passed
去掉副本 check-state-transition 的 "P1" → 1 failed
  AssertionError: 不可裁剪阶段集在两脚本已分叉（ADR-014 判据单源）：
    check-pruning=['P1','P2','P4','P5','P6'] vs check-state-transition=['P2','P4','P5','P6']
```
✅ 守护**真能转红**，且消息给出两集合差异。
**守护局限（知悉项）**：`test_non_prunable_phases_guard.py` 只校验**两处相等 + 含 P1**，不校验集合「正确性」——若两处被同时改成同一错误集（如误加 P7），守护仍绿。该守护目标是「防漂移」，非「防错值」；正确性另有 `check-protocol-consistency.py` 的 `P2/P6 不可裁剪` 锚点 + `test_check_pruning.py` 覆盖。

### ⑤ RM-AG0110 行合法性 —— ✅

- 行（`roadmap.md:109`）：`line.split("|")` **长度 = 9**，精确等于 `check-gate.py:2128` 的 `_ROADMAP_EXPECTED_COLS = 9`（7 数据列 + 首尾空串）。✅
- 状态列 `cols[3] = "backlog"`——活跃表内合法值（`backlog` 33 次 / `done` 63 / `scheduled` 7）；`cols[5]`（关联任务）为 `—`（无关联 task ⇒ `_check_roadmap_done` 不会误匹配）。✅
- 单元格内无字面 `|`（未破坏列数）。✅

### ⑥ 本轮是否引入新 A1–A8 问题 —— 引入 2 处（见 A1/A3/A4）

- **A3 反向传播（新）**：`check-pruning.py` 现校验 P1，但 `state-machine.md:201-208`「裁剪条件（hook 验证，见 scripts/check-pruning.py）」列表**仍无 P1** ⇒ 文档块与脚本不一致。**MISALIGNED**。
- **A4 覆盖（新）**：`check-pruning.py` 的 P1 拦截分支**无行为测试**。**MISALIGNED**。

**A7 结论**：实施**正确**、与用户裁决一致；ADR-014 的「最小对齐 + 等价守护」已落地，完整单源（下沉契约）由 RM-AG0110 承接。A7 本项 **ALIGNED**。

---

## 增量 A1–A8

### A1: 文档→脚本对齐 — MISALIGNED

#### A1-1 【MISALIGNED】`state-machine.md` 裁剪条件块缺 P1

**文档声明**（`agate/state-machine.md:201-208`）：
> **裁剪条件（hook 验证，见 scripts/check-pruning.py）**：
> - P2 不可裁剪（…）
> - P3：仅 low 风险可裁剪（…）
> - P4 不可裁剪（…）
> - P5 不可裁剪（…）
> - P6 不可裁剪（…）
> - 裁剪 P7：…
> - 裁剪 P8：…

**脚本实现**（`agate/scripts/check-pruning.py:253-255`）：`for _p in NON_PRUNABLE_PHASES: if _p not in phases: errors.append(...)`，`NON_PRUNABLE_PHASES` **含 P1**。

**差异**：该块自称「hook 验证」的裁剪条件**穷举**，且**逐条**列出 P2/P3/P4/P5/P6/P7/P8，但**漏 P1**——而 P1 自本轮起已由 `check-pruning.py` 机械拦截（实测 rc=1）。读者据该块会误以为 P1 裁剪不经 hook 拦截。属**本轮 A7 引入的文档漂移**（第 2 轮时该块与脚本一致，因脚本当时确实不校验 P1）。

**建议方向**：在 `state-machine.md:202` 前补一行，与 `check-pruning.py:27` 的文案一致，例如：
> - P1 不可裁剪（需求基线是全流程脊梁，无论任务大小都需建立——小任务可简化，见 WORKFLOW.md 适用边界）

**注**：同文档 `:224`「不可跳过的阶段：P1、P2、P4、P5、P6」已含 P1，故信息未完全缺失；仅「hook 验证」枚举列表不完整。**WORKFLOW.md:239**（核心阶段含 P1）、**phase-cards/P1:4**（P1 不可裁剪）、**analyst.md:64**（`# P1 必填`）均已含 P1，**无需改**。

### A2: 脚本→文档对齐 — ALIGNED

新增脚本逻辑（check-pruning 的 P1 项、check-state-transition 的模块级常量）对应的文档面：`state-machine.md:224`、`WORKFLOW.md:239`、`rules/state-transitions.md:94`、`phase-cards/P1:4` 均已声明 P1 不可跳过/裁剪。唯一缺口是 A1-1 的枚举块（属 A1 方向），非 A2 方向。ALIGNED。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（连锁）**：`check-pruning.py` 与 `check-state-transition.py` 的不可裁集经等价守护收敛为「同值」；`agate-state-set.py` 前向判据仍单源（前轮已核）。ALIGNED。

**A3b（反向传播）**：

| 应被影响文件 | 现状 | 判定 |
|---|---|---|
| `agate/state-machine.md:201-208` | 「裁剪条件（hook 验证）」列表**缺 P1**（脚本已校验） | **未闭合**（= A1-1） |
| `agate/WORKFLOW.md:239` | 核心阶段已含 P1 | ✅ 无需改 |
| `agate/phase-cards/P1-requirements.md:4` | 「P1 不可裁剪」 | ✅ 一致 |
| `agate/assets/execution-roles/analyst.md:64` | `# P1 必填，P2/P4/P5/P6 不可裁` | ✅ 一致 |
| `agate/rules/state-transitions.md:94` | 不可跳过阶段含 P1 | ✅ 一致 |
| `agate/scripts/README.md:78` | check-pruning 条目为泛述（未枚举各阶段） | 可选（不必逐一列） |
| `agate/tests/README.md` 映射表 | 未登记新 `test_non_prunable_phases_guard.py` | 可选（tests/README 内容非机械登记面，见 `test_t43_check_registration_surface.py:21-26`：scripts/README 索引与 tests/README 用例计数均为**约定**非门禁） |
| `agate/scripts/check-protocol-consistency.py` 锚点 | 新增「前向跨阶」锚点（A6）；未新增「P1 不可裁剪」锚点 | 可选（P2/P6 已有锚点，P1 无——非必须） |
| `CHANGELOG.md` | 未提「check-pruning 现也校验 P1」 | 见 A5（可选） |

**结论**：A3 **MISALIGNED**（唯一必补 = `state-machine.md:201-208` 补 P1，同 A1-1；其余为可选）。

### A4: 测试覆盖 — MISALIGNED

**最近一次全量 pytest 实跑**（后台 job + `-n auto`；跑前/跑后 `git status --porcelain` 逐字节一致，**未污染**）：
```
$ python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
1 failed, 2873 passed, 2 skipped, 1 rerun in 85.14s (0:01:25)
```
唯一失败仍为环境问题：`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（本机 opencode CLI 无 `debug agent` 子命令），与前两轮同源、与本 diff 无关。较第 2 轮 **+1 passed**（新守护用例）。

**定向实跑**：
- `test_check_pruning.py` → **30 passed**（原始输出见 A7-③）；
- `test_non_prunable_phases_guard.py` → **1 passed**（基线）。

#### A4-1 【MISALIGNED】check-pruning 的 P1 拦截分支无行为用例

本轮 A7 的**核心行为**是「`check-pruning.py` 拒绝裁剪 P1」。但：
- `test_check_pruning.py`（30 用例）**无 P1 用例**——所有 fixture 的 `phases` 都含 P1（P1 检查恒过，append 分支**从未执行**）；
- 新守护测试 `test_non_prunable_phases_guard.py` 只校验**常量**（两处相等 + 含 P1），**不执行** `main()` 的拦截分支。

即：P1 拦截的**行为**仅由本报告的 scratch 验证，**无 committed 测试锁定**。建议补一条 `test_p2_*_prune_p1_exit_1`（`phases` 不含 P1 → rc=1 + 输出含「P1 不可裁剪」）。

**守护局限（知悉项，非 MISALIGNED）**：`test_non_prunable_phases_guard.py` 只防「两处漂移」，不防「两处同时错」（如同时误加 P7）；正确性依赖 `check-pruning` 的 P2/P6 锚点 + `test_check_pruning.py`。

**结论**：A4 **MISALIGNED**（建议补 P1 行为用例）。

### A5: 下游影响 + 文档传播 — ALIGNED

- **行为变更**：`check-pruning.py` 现对**所有任务**（含 legacy）拒绝 `pruned: [P1]`/`phases` 不含 P1——在途任务若曾合法声明裁 P1 会新失败。但此类声明本就被 `check_transition` 在转移期拦截（非 legacy），且 `phase-cards/P1:4` 早已声明「P1 不可裁剪」，属**修正既有不一致**，非破坏性。
- **CHANGELOG**：`[Unreleased]` 的 M-1 条目已声明「不得跨过不可跳过阶段（P1/P2/P4/P5/P6）」，涵盖该规则；**未**单独提「check-pruning 也校验 P1」。属**可选补记**（同一 M-1 修复的第二落点）。
- `check-protocol-consistency.py` **CHECK 8**（`:549-550` 要求 `P2 不可裁剪` 出现在 check-pruning.py 与 state-machine.md）与 **CHECK 12** 均通过（新 `_NON_PRUNABLE_REASONS` 保留字面文案）。

**结论**：ALIGNED（含 1 条可选 CHANGELOG 补记）。

### A6: 锚点表覆盖 — ALIGNED

见上「A6 逐条核实」（4 项全过）。

### A7: 设计原则一致性 — ALIGNED

| ADR | 相关性 | 判定 |
|---|---|---|
| ADR-014 判据单一权威源 | 不可裁集从「两处各写且 P1 分叉」→ 两处模块级常量**同值** + **等价守护**；完整单源（下沉契约键）由 **RM-AG0110** 承接 | **ALIGNED**（最小对齐达标；完整单源有 owner） |
| ADR-015 门禁只用于实质错误 | P1 不可裁属「跳过需求基线」的实质错误（会导致后续错误决策）→ 必须拦 | **ALIGNED** |
| ADR-002 可判定性 | check-pruning 的 P1 判定为 exit code，机器可判定 | **ALIGNED** |

**残余风险（已登记，非阻塞）**：本方案仍是「两处同值 + 守护」，非「单一定义」；ADR-014 严格意义要求「仅一处定义」。RM-AG0110（backlog）明确验收锚=「该集在协议内仅一处定义，两脚本均从契约读取」。守护测试（`test_non_prunable_phases_guard.py`）是当前唯一防漂移手段，且在 RM 落地前**应保留**（落地后应改为「两脚本均从契约读值」的等价守护）。

**结论**：ALIGNED。

### A8: 声称-命令绑定 — ALIGNED

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | 锚点已补（用户陈述） | `grep -n "前向跨阶检测" check-protocol-consistency.py` → `:619` | 成立 |
| 2 | 关键词存在 | `grep -c "前向跨阶" check-state-transition.py` → 2 | 成立 |
| 3 | 两处集合逐字一致且含 P1（`check-pruning.py:22`、`check-state-transition.py:46` 注释） | scratch 加载两模块 → `set` 相等、含 P1 | 成立（容器类型不同，见 A7-① 注记） |
| 4 | check-pruning 的 P1 项会拦（RM-AG0110 / 用户陈述） | scratch：`phases` 缺 P1 → rc=1 + 「P1 不可裁剪」 | 成立 |
| 5 | 既有 4 条文案未被削弱 | `test_check_pruning.py` 30 passed（含 P2/P4/P5/P6 子串断言） | 成立 |
| 6 | 等价守护测试（RM-AG0110 陈述） | scratch：改一处 → guard 转红；基线 → 1 passed | 成立 |
| 7 | RM-AG0110 行合法（9 列 / backlog） | `len(line.split("|"))==9`（== `_ROADMAP_EXPECTED_COLS`）；status=backlog | 成立 |

**无据声称**：未发现需删除的无据声称。**结论：ALIGNED**。

---

## 闭环建议（本轮）

| 优先级 | 项 | 动作 |
|---|---|---|
| P1 | A1-1 / A3b | `state-machine.md:201-208`「裁剪条件（hook 验证）」补一行 **P1 不可裁剪**（与 `check-pruning.py:27` 文案一致）——一行的机械补齐 |
| P1 | A4-1 | 补 `test_check_pruning.py::test_p2_*_prune_p1_exit_1`（`phases` 不含 P1 → rc=1 + 输出含「P1 不可裁剪」），锁定本轮新行为 |
| P3 | A5 / A3b | 可选：CHANGELOG [Unreleased] 一句「`check-pruning` 亦校验 P1」；`tests/README.md` 映射表登记 `test_non_prunable_phases_guard.py` |

**注**：A6/A7 实施本身**正确、经独立复现**；上述两处 P1 缺口均为「一行的机械补齐」，不涉及脚本语义。本报告为**只读**审查，未修改任何协议/脚本/测试文件，未 commit；全量 pytest 跑前/跑后 `git status` 一致（无污染）。留痕文件见 `docs/reviews/agate-alignment-2026-10-09-HOTFIX-M1-03.progress.md`。
