---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: RM-AG0113 r2 复核——核实 r1 三项改正（① 两处 phases/risk_level 读取统一到 _p1_field/同路径；② M-1 读法如实改写 + state-transitions.md 同步；③ DEBT0041 依实测改判关单 + 新增回归用例）；并复核 r1 反例逐例一致性与残留
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/rules/state-transitions.md, agate/scripts/check-pruning.py, agate/scripts/check-state-transition.py, agate/tests/unit/test_agate_md_field_set.py, agate/tests/unit/test_check_pruning.py]
---

# 协议-脚本对齐审查（r2）

> 批次：批 A2 / RM-AG0113（分支 `hotfix/batch-a2-single-source`，未提交；`git diff` **8 文件** + 本留痕文件）。
> 第 1 轮报告：`docs/reviews/agate-alignment-review-2026-10-09-A2-0113-SINGLE.md`。
> 只读审查：未改任何协议/脚本/测试，未 commit / push；scratch 在 `/tmp/opencode/a2r2` 一次性副本上完成（跑测试前后 `git status --porcelain` 一致）。

## 审查结论汇总

| # | 审查项 | r2 结论 | r1 结论 |
|---|--------|---------|---------|
| A1 | 文档→脚本对齐 | **MISALIGNED（残留）**：`state-transitions.md` **新增了**如实口径段（`:91`），但**同一节** `:93` 的规则句仍写「读结构化 frontmatter，**不用正文正则**」⇒ 同节**自相矛盾** | MISALIGNED |
| A2 | 脚本→文档对齐 | **MISALIGNED（残留）**：`roadmap.md` RM-AG0113 done 注仍称「与 `check-pruning.py` 恒检的 **`_md_field`** 同源」——r2 已改走 `_p1_field`，该引用**陈旧** | MISALIGNED |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW**：新增 `_p1_field` 后，**`check-routing.py:113` 仍用 `_md_field`**（全文回退）⇒ 与 check-pruning 的 `_p1_field` **新分叉**（ADR-014 视角） | NEEDS_HUMAN_REVIEW |
| A4 | 测试覆盖 | **ALIGNED**（新用例判别力**独立复现**：旧红/新绿；`md-field-set` 新用例经**变异测试**确证锁定；全量 `-n auto` = **2909 passed / 1 failed(环境性) / 2 skipped**） | ALIGNED |
| A4b | **闭合后既有测试转红 + 夹具更新清单** | **空清单**（实测无既有用例转红；无既有夹具改动；diff 8 文件） | 空清单 |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（CHANGELOG 已更新 DEBT0041→关单；存量 43 任务全 legacy ⇒ 零影响；但 `roadmap` 陈旧引用 = A2） | NEEDS_HUMAN_REVIEW |
| A6 | 锚点表覆盖 | **ALIGNED** | ALIGNED |
| A7 | 设计原则一致性 | **ALIGNED**（且 r2 的「两处共用同一对函数」比 r1 更贴近 ADR-014 判据单源） | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED（残留）**：`DEBT0041` yaml 已改 `closed` + 自我更正，但**其尾部 2026-09-29 段仍写「本债仍 open」并重复「对任何 basename 都永久拒绝写 agent」**——与代码相反、且与新状态矛盾 | MISALIGNED |

**是否可 commit**：**否（残留文档/记录面 3 处需清，代码面已对齐）**——见文末。

---

## r1 发现逐条核实

| r1 项 | 批次声称的改正 | 独立核实 | 结论 |
|-------|----------------|----------|------|
| A1/A2（`state-transitions.md:93` 与代码不符） | 同步 `:91` M-1 括注 | `:91` **已加**「M-1 读法修订（RM-AG0113）…frontmatter 缺失时回退 `body_field_value`…M-1 禁止的是写法非读正文」；**但 `:93` 未动**，仍「不用正文正则」 | **部分成立**——新段与旧句**同节矛盾** |
| 重点 1（口径非逐例一致，H/N/Q/R/P） | 两处统一到同一代码路径 | 实测 **H/N/Q/R 已一致**；**P（坏 YAML）/S（无 frontmatter）仍不一致**（fm 非 dict：prune 回退正文，cst 早退 `None`） | **大部成立**，残留 2 例 |
| 重点 2（docstring「字段名行级锚定」失实） | 删除失实表述 + 如实改写 | `check-state-transition.py` 与 `check-pruning.py::_p1_field` docstring 均**已删**「行级锚定」，改为如实描述 + 明标「读法修订」 | **成立**（读法本身仍是判断项） |
| A8 / DEBT0041 注③错误 | 实测写入 → 改判关单 + 自我更正 + 新增回归用例 | yaml 内**已自我更正**、`status: closed`、新用例 `test_rm_ag0113_p3_agent_writable_by_tool`（变异测试确证锁定）；**但 yaml 外尾部段未更新** | **部分成立**——尾部段自相矛盾 |

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED（残留）

**r2 改动**（`agate/rules/state-transitions.md:91`，本批新增）：
> …（**M-1 读法修订（RM-AG0113）**：`declared` 的读取与 `check-pruning.py::_p1_field` **同代码路径**——`agate_common.fm_field_value` 优先、**frontmatter 缺失时**回退 `body_field_value` 的正文结构化解析；M-1 禁止的是「用 `^phases:\s*\[` 正则匹配正文」这一**写法**，非「读正文」本身，且回退只会让判据**更严**）…

**残留问题**（`state-transitions.md:93`，**本批未改**）：
> - 被跨过的阶段须**已从 P1 `phases` 移除并在 `pruned` 中声明**（读结构化 frontmatter，**不用正文正则**）；

**结论**：**MISALIGNED（残留）**。`:91` 说「回退正文结构化解析、M-1 禁的是写法非读正文」，`:93` 却说「不用正文正则」——**同一节内两条陈述互相否定**。文档仍与代码不符（代码走正文回退）。
**建议**：把 `:93` 括注同步为如实口径，例如「（`phases` **frontmatter 优先，缺失时回退 `agate_common.body_field_value`**——RM-AG0113 读法修订，见上）」；或删去 `:93` 括注、由 `:91` 统一承载。

### A2: 脚本→文档对齐 — MISALIGNED（残留）

**脚本改动**：`check-pruning.py` 新增 `_p1_field`（`:99`），`risk_level`/`phases` 改用它（`:236-237`）；**不再走 `_md_field`/`agate-md-field-get.py`**。

**文档现状**：
- `roadmap.md` RM-AG0113 done 注：`…（与 check-pruning.py 恒检的 **`_md_field`** 同源；**非** M-1 禁止的 `^phases:\s*\[` 正则）`——**陈旧**（恒检现用 `_p1_field`，非 `_md_field`）。
- `CHANGELOG.md:110`：`恒检（check-pruning.py）用 `_md_field`…`——为**改前**状态描述；`CHANGELOG:113` 的「现统一为…`body_field_value`」与代码相符，但未点明 check-pruning **自身也已换读器**（`_md_field`→`_p1_field`）。

**结论**：**MISALIGNED（残留）**（`roadmap` 的 `_md_field` 引用确定陈旧；`CHANGELOG` 属可接受的 before/after 叙述，但建议补一句）。
**建议**：`roadmap` 注改「与 `check-pruning.py::_p1_field` 同代码路径」；`CHANGELOG` 补「check-pruning 侧亦由 `_md_field` 换为 `_p1_field`（同路径）」。

### A3: 一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW

**A3b 反向传播（r2 新变化）**：

| 候选文件 | 是否应改 | 实测依据 |
|----------|----------|----------|
| `agate/scripts/check-routing.py:113` | **待裁量**（新分叉） | 仍 `_md_field("phases", …).split()`（`_md_field` = `agate-md-field-get`，回退扫**全文**）；而 check-pruning 现用 `_p1_field`（回退扫 **body**）。实测 H/N/Q 三例：`_md_field`=`P1 P2`/`P9`，`_p1_field`=`''` ⇒ **两处对同一 P1 的 `phases` 结论分叉**（r1 时二者同用 `_md_field`，一致） |
| `agate/rules/state-transitions.md` | 应改（见 A1） | `:93` 未同步 |
| `agate/state-machine.md:414` | 否 | 未提读取机制 |
| CHECK 9 锚点表 | 否 | 关键词 `前向跨阶` 仍在 |
| `agate/scripts/README.md:77` / `WORKFLOW.md:359` | 否 | 未述读取口径 |

**结论**：**NEEDS_HUMAN_REVIEW**。核心待裁量：ADR-014「判据单源」是否要求 `check-routing.py` 也改用 `_p1_field`（现为 `_md_field`，与 check-pruning 新分叉）。差异面窄（仅 frontmatter 区非键命中），但属**本批新引入**的分叉。

### A4: 测试覆盖 — ALIGNED

**新增/变更用例**：
- `test_check_pruning.py:413 test_rm_ag0113_two_judgments_same_read`（r1 已有，未变）：非 legacy 任务、`phases` 从 frontmatter 移入正文；断言 cst 侧 `declared==全集` **且** check-pruning `rc==0`。
- `test_agate_md_field_set.py:540 test_rm_ag0113_p3_agent_writable_by_tool`（**r2 新增**）：断言 P3 `agent` 可由 `agate-md-field-set` 写入（`rc==0` + 文件含 `agent: test-designer`）。

**判别力（独立复现）**：
- pruning 用例：装入 **HEAD 版** `check-state-transition.py`（check-pruning 新版）→ **1 failed**（`declared=set()`）；新版 → **1 passed**。✅
- md-field-set 用例：**变异测试**——给 scratch 版 `writable` 加回 `- {'agent'}` → 该用例 **1 failed**；还原 → **1 passed**。✅（真锁定，非假绿灯）

**全量实跑**（`python3 -m pytest agate/tests -n auto -q`）：
```
1 failed, 2909 passed, 2 skipped in 82.17s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
（r1 为 2908 passed；+1 = 本批新增 md-field-set 用例。）唯一 failed 为**环境性**（`opencode debug agent`→`agents`）。
**结论**：**ALIGNED**。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — 空清单

**无既有用例转红**：全量仅 1 条**环境性** failed（与本改动无关）。定向：`test_check_pruning.py`+`test_check_state_transition.py`=92 passed（r1）、`test_pre_commit_hook.py`=68 passed（r1）、`test_agate_md_field_set.py` 全绿。
**无既有夹具改动**：diff **8 文件**，均为本批目标面（新增 `state-transitions.md` + `test_agate_md_field_set.py`）；`test_pre_commit_hook.py` **未在 diff**。
**残留核查**：`grep -rn "_fm_declared_phases" agate/` 零命中。

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- **CHANGELOG**：已更新——DEBT0041 条目由「保持 open」改「**关单**」（`CHANGELOG.md:118-120`），与 r1 建议一致。**OK**。
- **gate 行为影响**：只影响非 legacy 任务的前向跨阶判据（+check-pruning 的 `phases`/`risk_level` 读器）。实测 `agate-workspace/tasks/` **43 任务全 legacy ⇒ 存量零影响**。**OK**。
- **文档传播**：`roadmap` 陈旧 `_md_field` 引用（= A2）；`state-transitions.md` 同节矛盾（= A1）。
- **结论**：**NEEDS_HUMAN_REVIEW**（CHANGELOG/存量 OK；文档传播 2 处残留即 A1/A2）。

### A6: 锚点表覆盖 — ALIGNED

CHECK 9 锚点「前向跨阶检测」关键词 `前向跨阶` 仍在（`check-protocol-consistency.py:617-621`）；`_p1_field` 是新增辅助函数、未删判据。**ALIGNED**。

### A7: 设计原则一致性 — ALIGNED

ADR-014「判据单一权威源」。r2 把两处收敛到**同一对函数**（`fm_field_value`+`body_field_value`），比 r1 的「同模式但异面」**更贴近** ADR-014。**ALIGNED**。（注：`check-routing` 未一并收敛，见 A3。）

### A8: 声称-命令绑定 — MISALIGNED（残留）

| # | 声称（来源） | 复现命令 | 结论 |
|---|--------------|----------|------|
| 1 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✅ rc=0（仅 429 冻结 WARNING） |
| 2 | `2909 passed` | `python3 -m pytest agate/tests -n auto -q` | ✅ **2909 passed**，伴 `1 failed`（环境性）+`2 skipped` ⇒ **非「全绿」** |
| 3 | `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ rc=0 |
| 4 | `roadmap 0 异常` | 复刻 `_ROADMAP_EXPECTED_COLS=9` 扫 `^\|\s*RM-` | ✅ 111 行，malformed=0 |
| 5 | `ruff All passed` | `~/.venvs/agate-dev/bin/ruff check <4 文件>` | ✅ All checks passed |
| 6 | 「两处**逐字同路径** ⇒ 结论一致」 | 见「重点 1」实测 | ⚠️ **fm 为 dict 时成立**；**fm 非 dict（坏/无 frontmatter）仍分叉**（P/S） |
| 7 | `DEBT0041 判据①已满足`（实测写入 rc=0） | `FILE=<P3.md> agate-md-field-set.py set agent test-designer` | ✅ rc=0（独立复现） |
| 8 | `DEBT0041 判据②由新增回归用例锁定` | 变异测试（加回 `- {'agent'}`） | ✅ 用例真锁定 |
| 9 | `DEBT0041 判据③全量 pytest 绿`（`closure_note`） | 全量 pytest | ⚠️ 字面不成立（1 环境性 failed）——与前批一贯口径同（应写「2909 passed / 1 环境性 failed」） |
| 10 | DEBT0041 yaml「自我更正…拒写 agent 与代码相反」 | 见 #7 | ✅ yaml 内更正属实；**但 yaml 外尾部段仍写「本债仍 open」+「永久拒绝写 agent」**（见下） |

**结论**：**MISALIGNED（残留）**。第 10 条的「更正」**未落到同一债的尾部段**：`tech-debt.md:1648` 仍「本债仍 open，但理由须改」，`:1650` 仍「`writable = _writable_keys(rules_root) - {"agent"}`——**对任何 basename 都永久拒绝写 agent**」⇒ 与 `status: closed` 及代码**双重矛盾**。第 9 条措辞宜收紧。

---

## 五项重点结论（r2）

### 重点 1：口径是否**逐字同路径**？——**fm 为 dict 时是；fm 非 dict 时仍分叉**（NEEDS_HUMAN_REVIEW，低风险）

**代码逐条比对**（`check-pruning.py:99` vs `check-state-transition.py:341`）：
```python
# check-pruning.py::_p1_field
fm, body = split_frontmatter(p1_text)
v = fm_field_value(fm, field) if isinstance(fm, dict) else ""
if not v:
    v = body_field_value(body, field)
return v
# 调用方：phases = _p1_field(p1_text, "phases").split() → set(phases)
```
```python
# check-state-transition.py::_p1_pruned_and_declared
fm, _body = split_frontmatter(text)
if not isinstance(fm, dict):
    return None, None                      # ← 早退
if fm_field_value is None or body_field_value is None:
    return None, None
_phases_val = fm_field_value(fm, "phases")
if not _phases_val:
    _phases_val = body_field_value(_body, "phases")
declared = {p for p in str(_phases_val).split() if p}
```
**同**：`fm_field_value(fm,"phases")` → 空则 `body_field_value(body,"phases")` → `split()` 归一到 `Pn` 集。
**异**：`fm` **非 dict** 时——`_p1_field` 仍走 `body_field_value(body,…)`（且 `split_frontmatter` 无块时 `body`=**全文**）；cst **直接返回 `None`**（fail-closed）。⇒ `_p1_field` docstring「两处共用同一对函数 ⇒ **结论必一致**」**过于绝对**。

**反例逐例实测**（`/tmp/opencode/a2r2/cmp.py`，真函数）：

| 输入 | r1 两处 | r2 两处 | 结论 |
|------|:--:|:--:|------|
| A fm list / B fm 串 / C 正文内联 / D 正文块式 / E 两者都有(fm 胜) / F 都无 / G 引号 / I fm=null+正文 / O 正文 | 一致 | 一致 | ✅ |
| **H** fm 注释 `# phases: [P1, P2]` | ❌ 分叉 | ✅ 一致（均 `∅`） | **已修** |
| **N** fm 未知键 `pruned_phases: [P1, P2]` | ❌ 分叉 | ✅ 一致（均 `∅`） | **已修** |
| **Q** fm 串值 `note: "see phases: [P9]"` | ❌ 分叉 | ✅ 一致（均 `∅`） | **已修** |
| **R** fm `phases: 3`（int） | ❌ 分叉 | ✅ 一致（均 `{"3"}`） | **已修** |
| **P** 坏 YAML + 正文 phases | ❌ 分叉 | ❌ **仍分叉**（prune=`{P1,P2,P3}` / cst=`None`） | 残留 |
| **S** 无 frontmatter + 正文 phases | （r1 未测） | ❌ **分叉**（prune=`{P1,P2,P3}` / cst=`None`） | 残留 |

**结论**：r1 的 4 例**确已修**；残留 P/S 均属「**frontmatter 非 dict**」（坏/无 frontmatter）。对非 legacy 任务，`check-frontmatter.py` 会先判 ERROR，故**实践面被遮蔽**；但函数级「结论必一致」不成立。**判 NEEDS_HUMAN_REVIEW**（是否把 cst 的早退改为与 `_p1_field` 同面，或弱化 docstring 的「必一致」措辞）。

### 重点 2：M-1 读法修订是否诚实？——**比 r1 明显改善；但 `state-transitions.md:93` 未同步，同节自相矛盾**（NEEDS_HUMAN_REVIEW）

- **已改正**：两函数 docstring **删除**了「字段名行级锚定」失实表述（实测 `_body_list_value` 用 `re.search`、无 `^`）；明标「M-1 读法修订（RM-AG0113）」；如实写出「回退只会让 `declared` 变大 ⇒ 前向跨阶**更严**」。⇒ r1 的「失实」指控**已消**。
- **残留失实/矛盾**：`state-transitions.md:91` 说「M-1 禁止的是写法非读正文」，紧邻的 `:93` 仍「读结构化 frontmatter，**不用正文正则**」——同节自相矛盾（见 A1）。
- **读法本身仍是判断项**：「M-1 禁的是 `^phases:\s*\[` 写法、非读正文」是对 M-1 的**窄解读**（依据 HEAD docstring 的窄措辞）；M-1 的宽记录（commit `7430b905` 信息 / `state-transitions.md` 原文）是「读结构化 frontmatter，不用正文正则」。批次已把该解读**显式化并留痕**（诚实），但解读正确性仍属人工裁定。
- **附注（措辞）**：docstring 称 M-1 禁 `^phases` 正则因其「易被正文散文误命中」——但新回退用的 `body_field_value` 模式 `phases:\s*\[…\]` **无 `^`**，误命中面**更大**；此句作为「为何不用旧正则」的论证偏弱，宜删或改述（不影响行为）。

### 重点 3：判别力——**成立**（两用例均独立复现，md-field-set 用例经变异测试）

见 A4：pruning 用例旧红/新绿；md-field-set 用例加回 `- {'agent'}` 即红。

### 重点 4：DEBT0041 关单是否成立？——**判据 ①② 成立；③ 措辞需收紧；债内尾部段自相矛盾**（A8 MISALIGNED）

- **①** 实测 `set agent` 对 `P3-test-cases.md` **rc=0 成功写入**（AGATE_ROOT=真仓 agate）→ **满足** ✅
- **②** 新回归用例 `test_rm_ag0113_p3_agent_writable_by_tool` **变异测试确证锁定**（加回限制即红）→ **满足** ✅
- **③** `closure_note` 写「全量 pytest 绿 + consistency 0 ERROR」→ consistency ✅；pytest **非全绿**（1 环境性 failed）⚠️
- **债内矛盾（须修）**：yaml 内已 `status: closed` + 自我更正；但 **yaml 外的 `:1648` 段仍「本债仍 open，但理由须改」，`:1650` 仍重复「对任何 basename 都永久拒绝写 agent」**（与代码相反）。⇒ 同一债条目**自相矛盾**。
- `check-debt.py` **rc=0**（schema 层面未拦——两段不在同一 yaml 块，故机械校验发现不了）。

### 重点 5：A4b + A8

- **A4b**：**空清单**——实测无既有用例转红（全量仅 1 环境性 failed）；无既有夹具改动。
- **A8**：`0 ERROR`/`2909 passed`/`check-debt rc=0`/`roadmap 0 异常`/`ruff`/判据①② 均**可复现**；残留 = 第 6（口径「必一致」过绝对）、第 9（「全绿」措辞）、第 10（DEBT0041 尾部段未更正）。

---

## 是否可 commit

**结论：否（残留集中在文档/记录面 3 处，代码面已对齐）。** 阻断项（均为小改）：

1. **A1（MISALIGNED 残留）**：`agate/rules/state-transitions.md:93` 的「读结构化 frontmatter，**不用正文正则**」与新加 `:91` **同节矛盾**。**最小修**：同步 `:93` 括注（或删除该括注，由 `:91` 统一承载）。
2. **A8（MISALIGNED 残留）**：`agate-workspace/debt/tech-debt.md:1648/1650` 仍「本债仍 open」+「永久拒绝写 agent」，与本债 `status: closed` 及代码**双重矛盾**。**最小修**：改写该 2026-09-29 尾段为「**已**由 TAG0050 批 B 解除（`writable` 不再 `- {"agent"}`）」并去掉「仍 open」。
3. **A2（MISALIGNED 残留）**：`roadmap.md` RM-AG0113 done 注的「与 check-pruning.py 恒检的 `_md_field` 同源」→ 改 `_p1_field`（同代码路径）；`CHANGELOG` 建议补一句 check-pruning 侧亦换读器。

**交人工确认项（NEEDS_HUMAN_REVIEW）**：
- 重点 1（fm 非 dict 时两处仍分叉：是否统一早退面 / 弱化 docstring「必一致」措辞）；
- 重点 2（「M-1 禁的是写法非读正文」这一窄解读的裁定）；
- A3（`check-routing.py` 是否随 ADR-014 改用 `_p1_field`）。

**非阻断观察（可选优化）**：
- `check-pruning.py:99` `_p1_field` docstring「**结论必一致**」宜改「fm 为 dict 时同路径一致」。
- `check-state-transition.py` docstring「M-1 禁 `^phases` 正则因其易被正文散文误命中」论证偏弱（新回退模式误命中面更大），宜删/改述。
- `check-pruning.py:158` 区仍多出一个空行（3 连续空行；ruff 默认不报）。
- `risk_level` 读器本批一并由 `_md_field` 改 `_p1_field`（RM 只要求 `phases`）——属小幅顺带统一，行为经全量绿验证，无碍。

---

## 附：只读与复现纪律

- 全程只读；仅写入本报告与 `docs/reviews/agate-alignment-2026-10-09-A2-0113-SINGLE-02.progress.md`。
- scratch 均在 `/tmp/opencode/a2r2`（口径对比 `cmp.py`/`cmp_routing.py`、HEAD 版变异测试、md-field-set `- {'agent'}` 变异测试）；跑测试前后 `git status --porcelain` 一致（8 个已改文件 + r1/r2 留痕文件）。
- 变异测试用**完整 `agate/` 副本**（含 `rules/`），`AGATE_ROOT` 指向副本。
