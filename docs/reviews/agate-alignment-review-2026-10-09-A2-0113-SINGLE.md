---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: RM-AG0113（ADR-014 判据单源）——把 check-state-transition.py::_p1_pruned_and_declared 的 `phases` 读取从「仅 frontmatter」改为「frontmatter 优先 + 缺失时回退 agate_common.body_field_value」，与 check-pruning.py 恒检的 _md_field 口径对齐；并复核 DEBT0031 关单 / DEBT0041 保持 open
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/scripts/check-pruning.py, agate/scripts/check-state-transition.py, agate/tests/unit/test_check_pruning.py]
---

# 协议-脚本对齐审查

> 批次：批 A2 / RM-AG0113（分支 `hotfix/batch-a2-single-source`，未提交，改动在工作区，`git diff` 6 文件 + 本留痕文件）。
> 只读审查：未改任何协议/脚本/测试，未 commit / push；所有 scratch 实验在 `/tmp/opencode/a2scratch` 一次性副本上完成（跑测试前后 `git status --porcelain` 一致）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（`rules/state-transitions.md:93` 明写「读结构化 frontmatter，**不用正文正则**」，而改后代码对 `phases` 走**正文正则回退**——文档所声明的读取机制已与脚本不符） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（同一缺口：脚本行为已变，`state-transitions.md:93` 未同步；属「脚本→文档」方向） |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW**（反向传播清单缺 `state-transitions.md`；`check-routing`/`check-gate`/CHECK 9 锚点/`state-machine.md` 已逐一确认**无需**改；M-1 口径 vs ADR-014 的取舍需人工裁量） |
| A4 | 测试覆盖 | **ALIGNED**（新用例判别力**独立复现**成立：旧实现红 / 新实现绿；全量 `-n auto` 实跑 **2908 passed / 1 failed(环境性) / 2 skipped**） |
| A4b | **闭合后既有测试转红 + 夹具更新清单**（RM-AG0107 / DEBT0054） | **空清单**：经实测**无既有用例转红**、**无既有夹具改动**（diff 仅 6 文件，`test_pre_commit_hook.py` 未改） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（CHANGELOG 已标注；存量 **43 任务全 legacy ⇒ 零影响**、无破坏性变更；但 `state-transitions.md` 未传播 = A2 缺口） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9「前向跨阶检测」锚点关键词 `前向跨阶` 仍在，无需新增/改锚点） |
| A7 | 设计原则一致性 | **ALIGNED**（本改动方向与 ADR-014「判据单一权威源」一致：消除同一 `phases` 的两读分叉） |
| A8 | 声称-命令绑定 | **MISALIGNED**（`DEBT0041` 新注③「md-field-set 拒写 agent」**不可复现**——实测 rc=0 写入；其余声称（`0 ERROR`/`2908 passed`/`check-debt rc=0`/`roadmap 0 异常`/`ruff All passed`/判别力）均可复现；`2908 passed` 字面成立但**非「全绿」**，伴 1 条环境性 failed） |

**是否可 commit**：**否（先修两处，或把 A1/A2 与 M-1 解读交人工确认）**——见文末。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**文档声明**（`agate/rules/state-transitions.md:93`，本批未改）：
> 被跨过的阶段须**已从 P1 `phases` 移除并在 `pruned` 中声明**（读结构化 frontmatter，**不用正文正则**）；

**同源记录**（M-1 hotfix commit `7430b905` 提交信息；`docs/reviews/agate-alignment-review-2026-10-09-HOTFIX-M1.md:51`）：
> `_p1_pruned_and_declared` … **只读 frontmatter，不用正文正则**——符合 M-1 明确要求。

**脚本实现**（`agate/scripts/check-state-transition.py:364-372`，本批新增）：
```python
phases = fm.get("phases")
if phases is None and body_field_value is not None:
    # RM-AG0113：与 check-pruning 恒检同口径——frontmatter 缺失时回退规范读取器
    _fallback = body_field_value(_body, "phases")
    if _fallback:
        phases = _fallback
```
`agate_common.body_field_value` → `_body_list_value`（`agate_common.py:1364-1377`）用 `re.search(r"phases:\s*\[([^\]]+)\]", body)` / 块式正则读**正文**。

**结论**：**MISALIGNED**。文档声明的读取机制是「只读结构化 frontmatter、不用正文正则」；改后脚本在前向跨阶判据里**重新引入了正文正则回退**。语义已不一致。
**差异**：文档禁止的「正文正则」正是改后代码走的路径；`body_field_value` 是正文正则（虽模式与 `^phases:\s*\[` 不同，见「重点 2」）。
**建议**：若采纳「选项一」（RM-AG0113 明文许可），把 `state-transitions.md:93` 的括注改为如实口径，例如「（`phases` **frontmatter 优先，缺失时回退规范读取器 `agate_common.body_field_value`**——与 `check-pruning` 恒检同源；RM-AG0113 / ADR-014 判据单源）」；并在文中显式说明该回退是**对 M-1 原『不用正文正则』口径的修订**（否则两份权威源冲突）。

### A2: 脚本→文档对齐 — MISALIGNED

与 A1 同源缺口，只是方向不同：脚本行为（`_p1_pruned_and_declared` 的读取口径）已变，**对应协议文档 `state-transitions.md:93` 未同步**。本批 `git diff` 6 文件中**不含** `agate/rules/state-transitions.md`。
**结论**：**MISALIGNED**。**建议**：随本批同步该文档（一行括注）。

### A3: 一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW

**A3a 已知连锁**：`CHANGELOG.md`（[Unreleased] 修复节）、`roadmap.md`（RM-AG0113 → done）、`tech-debt.md`（DEBT0031 → closed、DEBT0041 加注）均已随改；`check-debt` rc=0、`consistency` 0 ERROR。

**A3b 反向传播**（主动推断「应被影响但未在 diff 中」的文件，逐一实测）：

| 候选文件 | 是否应改 | 实测依据 |
|----------|----------|----------|
| `agate/rules/state-transitions.md` | **应改**（见 A1/A2） | `:93` 明写「不用正文正则」，代码已回退正文 |
| `agate/scripts/check-routing.py` | 否 | `:113` `_md_field("phases", …)`（复用 check-pruning 的 `_md_field`，**本就 frontmatter+正文回退**）⇒ 与改后 check-state-transition **一致**，无需改 |
| `agate/scripts/check-gate.py`（gate_p1） | 否 | 实测无 P1 `phases`/`pruned` 读取（`:804` 的 `declared` 是 `reviewed_bdds`，无关） |
| `agate/state-machine.md:414` | 否 | 只述规则，**未提读取机制**（无「frontmatter-only」措辞） |
| CHECK 9 锚点表（`check-protocol-consistency.py:617-621`） | 否 | 锚点关键词 `前向跨阶` 仍在，`_p1_pruned_and_declared` 未删 |
| `agate/scripts/README.md:77` / `WORKFLOW.md:359` | 否 | 仅述「状态转移合法性+重试上限」，**未述读取口径** |

**结论**：**NEEDS_HUMAN_REVIEW**。唯一确定缺口 = `state-transitions.md`（= A2）。**核心待裁量**：`state-transitions.md`/M-1 的「不用正文正则」是**规则**还是**实现描述**？若视为规则，则本批需要显式修订该规则（并留痕）；若视为实现描述，则只需同步措辞。此为设计取舍，交人工。

### A4: 测试覆盖 — ALIGNED

**新增用例**：`agate/tests/unit/test_check_pruning.py:413` `test_rm_ag0113_two_judgments_same_read`（非 legacy 任务，把 `phases` 从 frontmatter 移入正文；断言 cst 侧 `declared==全集` **且** check-pruning 恒检 `rc==0`）。

**判别力（独立复现，未采信批次结论）**：把 **HEAD 版** `check-state-transition.py` 装入 `/tmp/opencode/a2scratch/agate`（`check-pruning.py` 保持新版），`AGATE_ROOT` 指向该副本跑该用例：
```
1 failed  —— AssertionError: …实际 set()   （旧实现只读 frontmatter ⇒ declared=∅）
```
换回**新版**：`1 passed`。⇒ 该用例**确实能抓到旧实现**（判别力成立）。

**全量实跑**（`python3 -m pytest agate/tests -n auto -q`）：
```
1 failed, 2908 passed, 2 skipped in 83.36s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
唯一 failed 为**环境性**（`opencode debug agent` 已改名 `agents`，与本改动无关；H6/M-1 评审均记录同一现象）。
**结论**：**ALIGNED**。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — 空清单

**经实测，无既有用例转红**：全量 `-n auto` 仅 1 条**环境性** failed（见 A4），与工作区改动无关；定向跑 `test_check_pruning.py`+`test_check_state_transition.py` = **92 passed**、`test_pre_commit_hook.py` = **68 passed**，全绿。

**无既有夹具更新**：`git diff --stat` 仅 6 文件；`test_pre_commit_hook.py` **未在 diff 中**（选项二曾改的 `_P1_REQ` 夹具已 `git checkout` 还原）。

**残留核查（选项二完整性）**：`grep -rn "_fm_declared_phases" agate/` **零命中**；`git status --porcelain` 仅 6 个已改文件 + 本留痕文件。⇒ 批次所述「选项二已完整回退」**成立**。

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- **CHANGELOG**：`[Unreleased] 修复`节新增条目（`CHANGELOG.md:109-120`），格式与同节一致。**OK**。
- **gate 行为影响**：改动只影响**非 legacy 任务**的前向跨阶判据。实测 `agate-workspace/tasks/` **43 个任务全部 legacy**（账本无 `task_created`/`task_adopted`）⇒ **存量零影响**，无破坏性变更。**OK**。
- **文档传播**：`state-transitions.md` 未同步（= A1/A2）。
- **结论**：**NEEDS_HUMAN_REVIEW**（CHANGELOG/存量影响 OK；文档传播缺口即 A2，且 M-1 口径修订是否需显式公告（UPGRADING）交人工）。

### A6: 锚点表覆盖 — ALIGNED

CHECK 9 锚点（`check-protocol-consistency.py:617-621`）：`{"desc": "前向跨阶检测…", "script": "check-state-transition.py", "keywords": ["前向跨阶"]}`。本批未删该判据、未改其关键词 ⇒ 锚点仍满足。`check-pruning.py` 已有 6 条锚点。**结论**：**ALIGNED**。

### A7: 设计原则一致性 — ALIGNED

**相关 ADR**：`agate/adr.md:533` **ADR-014「判据单一权威源——判据必须单源」**。本批正是消除「同一 P1 `phases` 在两条判据下两种读法」的分叉，**与 ADR-014 主旨一致**。
**结论**：**ALIGNED**（方向一致）。**注**：ADR-014 只要求「判据单源」，不裁定「单源到哪一侧」（frontmatter-only 还是 frontmatter+正文）——该裁定落到 M-1 文档口径上，见重点 2。

### A8: 声称-命令绑定 — MISALIGNED

| # | 声称（来源） | 复现命令 | 结论 |
|---|--------------|----------|------|
| 1 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✅ rc=0（仅 429 冻结 WARNING） |
| 2 | `2908 passed` | `python3 -m pytest agate/tests -n auto -q` | ✅ **2908 passed**，但伴 `1 failed`（环境性）+`2 skipped` ⇒ 「全绿」字面不成立 |
| 3 | `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ rc=0 |
| 4 | `roadmap 0 异常` | 复刻 `check-gate.py` `_ROADMAP_EXPECTED_COLS=9`：扫 `^\|\s*RM-` 行 `len(split("|"))!=9` | ✅ 111 行 RM-，malformed=0 |
| 5 | `ruff All passed` | `~/.venvs/agate-dev/bin/ruff check <3 文件>` | ✅ All checks passed |
| 6 | 新用例「旧实现下 state-transition 侧读到空集 ⇒ 转红，已 scratch 实测」 | 见 A4 变异测试 | ✅ 独立复现（旧=1 failed / 新=1 passed） |
| 7 | `DEBT0031 关单（机械对账已存在、默认开、在 gate 路径；锚点更正为 check-pruning）` | 见「重点 4」 | ✅ 四条成立（warning-only 亦成立） |
| 8 | `DEBT0041 保持 open（… 残留 = P3 agent **写入工具缺口** + 无回归用例）` | `FILE=P3.md AGATE_ROOT=<真仓agate> python3 agate/scripts/agate-md-field-set.py set agent test-designer` | ❌ **不可复现**：rc=0，`OK: agent=test-designer 已写入`。注③「拒写 agent」**错误**，`closure_criteria` 第 1 条**已满足** |
| 9 | CHANGELOG「与 `agate-md-field-get.py` **同源**的正文结构化解析」 | 见「重点 1」 | ⚠️ **近似**（模式同源，但 `_md_field` 回退扫**全文**、`body_field_value` 扫 **body**，存在分叉） |

**结论**：**MISALIGNED**。第 8 条为无据（且与代码相反）的声称，须按 A8 规则**删除或更正**；第 2 条措辞宜收紧为「2908 passed（1 环境性 failed）」；第 9 条「同源」宜改「同模式（回退面略有差异）」。

---

## 五项重点结论

### 重点 1：口径是否**真**统一？——**近似统一，非逐例一致**（NEEDS_HUMAN_REVIEW）

RM 的**目标场景**（正文声明 `phases`、frontmatter 缺失）**已统一**：`check-pruning` 的 `_md_field("phases")` 与 `check-state-transition` 的 `declared` 在该场景下逐例一致。**但**两读取器**不是同一函数**：
- `_md_field`（经 `agate-md-field-get._get`）frontmatter 缺失时回退 `_regex_list(text)`——扫**全文**（含 frontmatter 区）；
- `body_field_value` 回退 `_body_list_value(body)`——只扫 **body**（frontmatter 区已剥离）。

⇒ 凡「`phases: [...]` 形态文本出现在 **frontmatter 区**但**未被 YAML 解析为 `phases` 键**」的输入，两者分叉。实测（`/tmp/opencode/a2scratch/cmp2.py`/`cmp3.py`，真函数）：

| 输入 | `_md_field`（check-pruning 侧） | `declared`（check-state-transition 侧） | 一致？ |
|------|------|------|:--:|
| A frontmatter list / B frontmatter 串 / C 正文内联 / D 正文块式 / E 两者都有且不同（fm 胜）/ F 都没有 / G 引号 / I fm=null+正文 / O 正文 | 同 | 同 | ✅ |
| **H** frontmatter 注释行 `# phases: [P1, P2]` | `P1 P2` | `∅` | ❌ |
| **N** frontmatter 未知键 `pruned_phases: [P1, P2]`（子串命中） | `P1 P2` | `∅` | ❌ |
| **Q** frontmatter 字符串值 `note: "see phases: [P9]"` | `P9` | `∅` | ❌ |
| **R** frontmatter `phases: 3`（int，非 list/str） | `3` | `∅` | ❌ |
| **P** frontmatter 坏 YAML + 正文 phases | 贪婪匹配出垃圾 token | `None` | ❌ |

**结论**：RM 目标场景已收口；**「与恒检同源」为近似表述**（H/N/Q/R/P 为边界/非法输入）。若要**逐例一致**，须让回退面相同（cst 侧改用与 `_md_field` 同面的回退，或 `body_field_value` 也扫全文）。**判为 NEEDS_HUMAN_REVIEW**（差异面窄、多为非法/边界输入，是否值得收紧交人工）。

### 重点 2：M-1 禁令解读——**改写是「技术性成立、实质性存疑」**（NEEDS_HUMAN_REVIEW）

- **被替换的旧实现**（M-1 前的 `agate-state-set.py::_declared_phases`）：`re.search(r"^phases:\s*\[([^\]]*)\]", text, re.M)` —— **全文锚定正则**。
- **M-1 的两种记录口径**：
  - **宽**（commit `7430b905` 信息 / `state-transitions.md:93` / HOTFIX-M1 评审）：**「读结构化 frontmatter，不用正文正则」**。
  - **窄**（M-1 hotfix 写入的 `_p1_pruned_and_declared` docstring）：**「不得用 `^phases:\s*\[` 正则匹配正文」**。
- **本批改写**：称回退「**不是** `^phases:\s*\[` 正则，走 `agate_common` 规范解析（**字段名行级锚定** + 值归一），与恒检同源」。

**判断**：改写**技术性成立**（`_body_list_value` 的模式确为 `phases:\s*\[([^\]]+)\]`，**无 `^`**，与 `^phases:\s*\[` 字面不同）；但**实质性存疑**：
1. 它**仍是正文正则**——M-1 宽口径禁止的正是「读正文（用正则）」，而非仅「`^` 锚定那一个写法」；
2. 「**字段名行级锚定**」表述**失实**——`_body_list_value` 用 `re.search`（**无 `^`**），匹配正文**任意位置**，并非行级锚定；
3. 因此该改写**回避了 M-1 的实质**（「前向跨阶判据应读结构化 frontmatter、不读正文」），只做了字面辨析。

**处置建议**：M-1 若实质是「结构化 frontmatter 权威、前向跨阶不得据正文判定」，则本批应：(a) **不**引入正文回退，改走「选项二」但**保留**协议对该形态的容忍（即：恒检对该形态只 WARNING 不硬失败，见下）；或 (b) 明确**修订 M-1 口径**并在 `state-transitions.md` 留痕（「经 RM-AG0113 复核，前向跨阶 `phases` 读取改为 frontmatter 优先 + 正文回退，与恒检单源」）。二者需人工选定；**现态（改了码、未改 M-1 文档、docstring 用字面辨析掩盖）不宜直接落库**。

**对「选项一 vs 选项二」的独立判断**：本批选**选项一**（两处统一为 frontmatter+正文回退）在**方向**上更符合 RM-AG0113 的明文许可与 ADR-014，且**对 M-1 安全**（回退只让 `declared` 变大 ⇒ 前向跨阶只会**更严**、不会重开 M-1 的「跳阶绕过」口子，实测合法任务最终 rc 不变）。**但**它**触碰了 M-1 文档口径**，故必须同步文档（A2）。选项二（均 frontmatter-only）的**根本障碍**（批次所述）成立：会使恒检对「正文声明」形态**硬失败**，与协议对该形态的**容忍**（`_reconcile_p1_fields` 仅 WARNING）矛盾——除非同时把恒检也降为容忍（= 改动更大）。**⇒ 选项一方向正确，但须补文档同步 + 改写措辞去魅。**

### 重点 3：新用例判别力——**成立**（独立复现）

见 A4：HEAD 旧实现下该用例 **1 failed**（`declared=set()`），新实现 **1 passed**。判别力**真实存在**（非假绿灯）。

### 重点 4：DEBT0031 关单成立？DEBT0041 保持 open 是否正确？

**DEBT0031（关单）——基本成立**：
- 机械对账**存在**：`check-pruning.py:136 _reconcile_p1_fields`（经 `agate_common.reconcile_field`）对 `risk_level`/`phases` 做 fm↔正文双读对账；
- **默认开**：`reconcile_enabled()`（`agate_common.py:1240-1242`）缺省 on（`AGATE_RECONCILE` 未设即启用）；
- **在 gate 路径**：`check-pruning.py:223` 调用（实测 legacy 任务亦触发 `RECONCILE WARNING` + `RECONCILE SUMMARY`）；
- **warning-only**：`_reconcile_p1_fields` 只写 stderr、**不 append `errors`** ⇒ 不改退出码（实测 rc 由其它条件决定）；
- **锚点更正**：`closure_criteria` 原写「**check-gate P1** 校验…」，实际落在 **check-pruning**（同一 P1 gate 路径）——批次如实更正并在 `closure_note` 留痕。属**判断项**（追溯改写 closure_criteria 的锚）→ 计入 **NEEDS_HUMAN_REVIEW**，但不构成硬阻断。

**DEBT0041（保持 open）——理由含**错误**陈述，不正确**：
- 新注③「`agate-md-field-set.py` 拒写 `agent` 是反伪造的刻意策略」**与代码相反**：`agate-md-field-set.py:498-502` 注释明写「**TAG0050 批 B：解除旧的『agent 永久拒写』**」，`writable = (_writable_keys(rules_root) | …)` **无 `- {"agent"}`**；实测 `set agent` 对 `P3-test-cases.md` **rc=0 成功写入**（AGATE_ROOT=真仓 agate）。该陈述系**沿用 `tech-debt.md` 内 2026-09-29 的陈旧注**（当时 `writable = … - {"agent"}`）而未复验。
- 因此「**残留 = 工具缺口**」**不成立**；`closure_criteria` 第 1 条（「agate-md-field-set 能为 P3-test-cases.md 写 agent 字段」）**已满足**；且 `test_tag0050_write_tools.py:41` 已有 `("set","agent","writer")` 回归用例。
- **建议**：要么**关单**（第 1 条已满足、有回归用例），要么**重写残留**（若坚持 open，理由应为「releaser 正常流程未自动写 agent」等**流程**缺口，而非「工具拒写」），并**更正注③**。

### 重点 5：A4b + A8

- **A4b**：**空清单**——实测无既有用例转红（全量仅 1 环境性 failed）；无既有夹具改动（diff 6 文件，`test_pre_commit_hook.py` 未改）；选项二残留**零**（`_fm_declared_phases` 无命中）。
- **A8**：`0 ERROR`/`2908 passed`/`check-debt rc=0`/`roadmap 0 异常`/`ruff`/判别力 **均可复现**；`DEBT0041 注③` **不可复现（错误）**；`2908 passed` 非「全绿」。

---

## 是否可 commit

**结论：否（须先修，或把相关项交人工确认）。** 阻断项：

1. **A1/A2（MISALIGNED）**：`agate/rules/state-transitions.md:93` 的「读结构化 frontmatter，**不用正文正则**」与改后代码（正文正则回退）不符。**最小修**：同步该括注为如实口径，并显式说明「经 RM-AG0113 复核，前向跨阶 `phases` 读取统一为 frontmatter 优先 + 正文回退」。
2. **A8（MISALIGNED）**：`DEBT0041` 新注③「md-field-set 拒写 agent」**与代码相反**（实测 rc=0 写入）⇒ 须**更正/删除**该声称；连带「残留 = 工具缺口」结论与「保持 open」理由须重写（或据 `closure_criteria` 第 1 条已满足而关单）。

**交人工确认项（NEEDS_HUMAN_REVIEW）**：重点 1（口径非逐例一致，是否收紧）、重点 2（M-1 实质口径的修订裁定）、重点 4（DEBT0031 追溯改写 closure_criteria 锚是否接受）。

**非阻断观察（可选优化）**：
- CHANGELOG「与 `agate-md-field-get.py` 同源的正文结构化解析」宜改「同模式」（回退面有差）；「旧实现下…转红」可复现，保留。
- docstring「字段名**行级锚定**」表述失实（`_body_list_value` 无 `^`），宜改「字段名匹配 + 值归一（`re.search`，非行级锚定）」。
- `check-pruning.py` 本批仅加注释 + **多出一个空行**（`:158` 区 3 连续空行），ruff 默认不报，可顺手清理。

---

## 附：只读与复现纪律

- 全程只读；仅写入本报告与 `docs/reviews/agate-alignment-2026-10-09-A2-0113-SINGLE-01.progress.md`。
- 所有 scratch（口径对比 `cmp2.py`/`cmp3.py`、HEAD 版变异测试、CRLF 用例、md-field-set agent 写入测试）均在 `/tmp/opencode/a2scratch` 完成；跑测试前后 `git status --porcelain` 一致（6 个已改文件 + 1 个新增留痕文件）。
- 判别力变异测试使用**完整 `agate/` 副本**（含 `rules/`），`AGATE_ROOT` 指向副本，避免 `_phase_universe` 路径解析失败混淆。
