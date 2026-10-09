---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: >-
  RM-AG0105（DEBT0053 + DEBT0058）——BDD-3 关键词扫描面收窄（check-state-transition.py）
  + 平台假设扫描器新增 R6 调用级规则（check-platform-assumptions.py，subprocess 文本模式缺 encoding=）
  + test_bdd_1 断言由子串改调用形态 + 3 处 test_release_workflow.py 调用补 encoding=。
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/scripts/check-platform-assumptions.py
  - agate/scripts/check-state-transition.py
  - agate/tests/scripts/test_check_platform_assumptions.py
  - agate/tests/unit/test_check_state_transition.py
  - agate/tests/unit/test_release_workflow.py
---

# 协议-脚本对齐审查（RM-AG0105 / DEBT0053 + DEBT0058）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（规则本体按 RM-AG0105 验收锚实现；见 A2 的悬空引用） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（README 规则号 stale「R1-R5」+ 扫描器 docstring 漏 R6 + **悬空引用「见 README 判据边界」**） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（P3-tdd / dispatch-prompt / test-designer / tests/README 仍写「R1~R5」，未传播 R6） |
| A4 | 测试覆盖 | **MISALIGNED**（BDD-3「散文」负例**无判别力**；R6 多个边界无覆盖） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（2 条既有用例受影响，均已在批内处置；详见 A4b） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（CHANGELOG 已标 ✓；但文档传播不全 + R6 扫描面边界未成文） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9 锚点关键词仍满足，无需更新） |
| A7 | 设计原则一致性 | **ALIGNED**（遵循 ADR-014 判据单源） |
| A8 | 声称-命令绑定 | **MISALIGNED**（「83 passed」「2906 passed」均**不可复现**；其余 3 条 ✓；「3 处真缺陷」不全） |

**总判定：MISALIGNED（A2/A3/A4/A5/A8）——须修复后重审。**

---

## 逐项审查

### A1: 文档→脚本对齐

**规则来源**（`agate-workspace/roadmap/roadmap.md:104`，RM-AG0105 验收锚）：

> 修复：① BDD-3 扫描**收窄为结构化信号**（或至少排除代码块/行内代码）；② 平台扫描器新增
> `text=True`/`universal_newlines=True` 无 `encoding=` 规则并接入 CI 阻断。验收锚=散文不再误报 +
> 跨平台解码假设有静态判据

**脚本实现**：

- BDD-3（`agate/scripts/check-state-transition.py:74-100`）：新增 `_bdd3_event_lines()`（剔 fence /
  行内代码）、`_BDD3_DOC_REF_RE`（剔 `.md`/`agate/` 引用行）、`_BDD3_SUBAGENT_RE`（要求含
  `subagent`/`子代理`），在 `_scan_bdd3_keyword_phases`（:268-278）应用。
- R6（`agate/scripts/check-platform-assumptions.py:49-78`）：`_r6_text_without_encoding_hits()` 括号
  配平取整次调用，命中条件 = 文本模式 ∧ 无 `encoding=`；在 `_scan_file`（:155-163）挂载。

**结论**：**ALIGNED**。两条验收锚均落地。R6 确已在 CI `platform-scan` job 的扫描面内——该 job
（`.github/workflows/protocol-tests.yml:194`）跑 `python3 agate/scripts/check-platform-assumptions.py`
**无参**，脚本无参时默认扫 `agate/tests/`（`check-platform-assumptions.py:183-186`），而 R6 已并入
`_scan_file` ⇒ 对 tests/ 生效（实测 `agate/tests` 全树 rc=0，见 A8）。
⚠️ 但 R6 的**扫描面边界**（默认只扫 tests/，不扫 `agate/scripts/`）未成文，且该边界外仍有同类真缺陷
（见 A5）。

---

### A2: 脚本→文档对齐

三处脚本侧描述未与脚本实际对齐：

**① README 工具行 stale**（`agate/scripts/README.md:91`）：

> \| `check-platform-assumptions.py` \| 平台假设静态扫描器（**R1-R5**，扫描覆盖 .bats/.bash/.sh/.py）\| ...

脚本现有 R1–R6（R6 见 `check-platform-assumptions.py:49-78`）⇒ 该行漏 R6。

**② 扫描器 docstring 规则清单漏 R6**（`check-platform-assumptions.py:18-24`）：

> 规则（行级豁免见 …）：
>   R1 … R5 …

R6 未列入（`_scan_file:134` 的 `"""逐行跑 R1-R5 正则"""` 亦然）。R6 虽为调用级、不在 `_RULES` 表内，
但作为脚本契约的一部分应登记。

**③ 悬空引用（最实）**（`check-platform-assumptions.py:55`）：

> 局限：不做 AST 解析（同文件多调用/字符串内括号属已知近似，**见 README 判据边界**）。

实测 `agate/scripts/README.md` **无「判据边界」节**（`grep -n 判据 README.md` 仅命中「新增脚本登记面」
一节，与本引用无关）⇒ 该指针指向不存在的权威源，违反 ADR-014「文档复述但**必须指向权威源**」
（`agate/adr.md:567`）。且 R6 的真实局限**未被任何文档记录**（见 A4/A5）。

**结论**：**MISALIGNED**。
**建议**：① README L91 改「R1-R6」；② 扫描器 docstring 补 R6 一行；③ 二选一——在 README 增
「判据边界」节（写明 R6 的调用级近似与已知假阴/假阳面），或删除该悬空引用改指向实际存在的权威源。

---

### A3: 一致性连锁 + 反向传播

**反向传播清单（应被本批影响但不在 diff 中）**，逐一验证：

| 应传播目标 | 现状 | 结论 |
|---|---|---|
| `agate/scripts/README.md:91`（扫描器工具行）| 「R1-R5」 | ❌ 未传播（A2①） |
| `agate/scripts/check-platform-assumptions.py:18-24,134`（docstring）| 仅 R1-R5 | ❌ 未传播（A2②） |
| `agate/phase-cards/P3-tdd.md:104` | 「扫 R1~R5（裸 python3 / 硬编码 PATH / 系统临时目录字面量 / 其它平台假设）」 | ❌ 未传播——P3 自检指令漏 R6 |
| `agate/assets/templates/dispatch-prompt.md:146` | 「必须 0 命中（R1~R5：…）」 | ❌ 未传播——派发模板漏 R6 |
| `agate/assets/execution-roles/test-designer.md:61-64` | 「平台假设扫描必须 0 命中」+「扫描面限定」 | ⚠️ 未提 R6（措辞未枚举规则，影响较轻） |
| `agate/tests/README.md:95,101,136` | 映射行 + 「回归 (R1-R5)」+「发现平台假设（…/tmp）」 | ⚠️ 未提 R6（L101 系回归目录行，关联弱） |
| `agate/state-machine.md:655` / `agate/WORKFLOW.md:359` / `agate/UPGRADING.md:1121`（BDD-3 机制描述）| 仍述「关键词扫描」 | ⚠️ 描述未失真（仍是关键词扫描，只是收窄），可不动 |
| `agate/dispatch-protocol.md:109-141`（空返回恢复节）| 恢复策略，非扫描判据 | ✅ 无需动 |
| `agate/UPGRADING.md` 版本节 | 本批未加（同批 RM-AG0104 亦未加）| ✅ 与 hotfix 系列先例一致（发布时补）|

**连锁（A3a）**：本批无新增 BDD 编号、无 frontmatter 字段变更 ⇒ 无 BDD 编号格式连锁面。

**结论**：**MISALIGNED**。
**建议**：至少修 P3-tdd.md:104 与 dispatch-prompt.md:146（writer 会照此自检，漏 R6 会让 subagent 漏掉
`encoding=` 自检）；test-designer.md / tests/README.md 视维护成本顺手补。

---

### A4: 测试覆盖

**新增测试**（均有判别力）：
- `test_check_platform_assumptions.py:244-263` R6 正例（缺 `encoding=` → 命中）——去掉 R6 实现即红。
- `test_check_platform_assumptions.py:266-284` R6 反例（含 `encoding=` → 不命中）。
- `test_check_state_transition.py:1177-1207` BDD-3 收窄用例。

**覆盖缺口（实测）**：

1. **BDD-3「散文」负例无判别力**（`test_check_state_transition.py:1205`）：
   ```python
   assert not _hits("**dispatch-context 先写后派**。拆并行/重试时每个子任务各写一个。"), "散文不得命中"
   ```
   该串**不含关键词**「空返回/重派」（含的是「重**试**」）⇒ 旧实现（未收窄）同样返回 False。故这条断言
   **不能证明「散文误报已被收窄消除」**，与其 docstring「实测误报两类…②散文」的声称不符。
   真正有判别力的只有 `.md` 引用那条（:1206）。
   **建议**：改用**含关键词但无 subagent** 的散文，例如
   `"评审不通过时：analyst 修改需求 → 重派 requirements-review"`（旧实现命中、新实现不命中）。

2. **R6 边界无覆盖**（实测 `_r6_text_without_encoding_hits` 行为）：
   | 场景 | 实测 | 性质 |
   |---|---|---|
   | 嵌套括号 `subprocess.run([f(a), b], text=True)` | 命中 ✓ | 正确 |
   | 多行 f-string | 命中 ✓ | 正确 |
   | 同一行两个调用（一缺一含 `encoding=`）| 合并块 → **漏报** | 假阴（未记录）|
   | `encoding=` 出现在**字符串/注释**里 | 视作已满足 → **假阴** | 假阴（未记录）|
   | 调用跨 >40 行、`text=True` 在窗内而 `encoding=` 在窗外 | **误报** | 假阳（未记录）|
   | 注释/docstring 里提及 `subprocess.run(cmd, text=True)` | **误报** | 假阳（未记录）|
   | `subprocess.PIPE` 等**无括号属性行**吞后续调用括号 | **误报**（实测 `hits=[1,3]`，line1 被误报）| 假阳（未记录）|

   这些边界均未被 R6 的两个用例覆盖，也未写入任何「判据边界」（与 A2③ 的悬空引用叠加）。

**结论**：**MISALIGNED**。
**建议**：① 把 BDD-3 散文负例换成含关键词的串；② 为 R6 的「同调用跨行（正确不误报）」「属性行不误报」
至少各加一条；③ 其余近似面写入 README 判据边界（A2③）。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054）

**逐条清单（经实测）**：

| # | 既有用例/夹具 | 为何会转红 | 处置 | 状态 |
|---|---|---|---|---|
| 1 | `test_check_platform_assumptions.py::test_bdd_1_scanner_script_exists_platform_neutral`（:57-70）| 原断言 `not re.search(r"subprocess\|os\.system\|os\.popen", text)` 是**子串**判定；扫描器因 R6 必须**提及** `subprocess` ⇒ 子串命中即红 | 本批改为**调用形态**断言 `subprocess\.\w+\s*\(…` | ✅ 批内已改 |
| 2 | `test_check_platform_assumptions.py::test_bdd_8_clean_tree_zero_detection`（:109-117）| R6 对全 tests 树扫描时命中 `test_release_workflow.py` 的 3 处调用（HEAD 实测命中行 186/268/275）⇒ 非 0 命中即红 | 本批给这 3 处调用补 `encoding="utf-8"` | ✅ 批内已修（实测现 rc=0）|
| 3 | `agate/tests/unit/test_release_workflow.py`（夹具/被测调用）| 上述 3 处 `subprocess.run(..., text=True)` 缺 `encoding=` | 补 `encoding="utf-8"`（:188/:271/:279）| ✅ 批内已修 |
| 4 | 既有 BDD-3 用例（`test_bdd_3_empty_return_redispatch_*` / `card_block_*` / `real_progress_*` / `progress_batch_named_*`，:761-916）| 其夹具串均为「子代理空返回，已重派」含 `子代理` | 无需改（仍命中）| ✅ 实测绿 |
| 5 | `test_cross_milestone.py::test_bdd_16_*`（:21-31）| 扫描 `check-yaml-schema.py`/`check-structure-consistency.py` 两个脚本 | R6 对二者 rc=0 ⇒ 绿 | ✅ 实测绿 |

**空清单项**：除上表外，**经实测无其它既有用例转红**。

**另记（非本批导致）**：全量 pytest `-n auto` 实跑为 **2 failed, 2905 passed, 2 skipped**；两条 failed
**均非本批引入**——
- `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`：**环境**所致——本机
  `opencode` CLI 只有 `agents` 子命令、无 `agent`（隔离跑复现 `Unknown subcommand "agent"`）；
- `test_pre_commit_hook.py::test_m1_forward_jump_p0_to_p7_blocked`：**跨文件并行 flaky**——隔离跑
  连跑 2 次均绿、单文件 `-n auto` 68 passed。

**结论**：**ALIGNED**（清单完整且处置到位）。

---

### A5: 下游影响 + 文档传播

**CHANGELOG**：已在 `[Unreleased] > 修复`（`CHANGELOG.md:80-86`）标注本批 ✓。

**下游影响（gate/CI 行为）**：
- R6 已进入 CI `platform-scan` job 的扫描面（默认 tests/），**属新增阻断点**（对 agate 自身 tests）。
- 更重要：扫描器被 P3 自检/派发模板要求由 subagent 对**用户项目**的测试目录调用
  （`P3-tdd.md:102`、`dispatch-prompt.md:146`）⇒ **R6 对用户项目测试同样是新阻断点**。此为真实
  行为变更，应随发布写入 `UPGRADING.md`（本批未写，但**与同批 RM-AG0104 先例一致**——该批新增
  pre-commit 2y 步亦未写 UPGRADING ⇒ 按发布时补的口径可接受，不单独判 MISALIGNED）。

**文档传播不全**（与 A3 同源）：P3-tdd / dispatch-prompt / test-designer / tests/README 未提 R6。

**扫描面边界未成文 + 边界外有真缺陷**：R6 默认只扫 tests/，实测扫 `agate/scripts` 时 R6 命中 **5 处**
同类真缺陷（未修）：
```
R6 agate/scripts/agate_dispatch_route.py:569 / 574 / 605 / 621
R6 agate/scripts/check-protocol-consistency.py:529
```
（均为 `subprocess.run([...], capture_output=True, text=True)` 缺 `encoding=`，与本批所修同类）。
CHANGELOG（:85）称「该规则**抓到 3 处真缺陷**」在 tests/ 口径内成立，但会让人误以为 R6 已覆盖全仓；
建议成文扫描面边界（并评估是否将 scripts/ 纳入或登记 DEBT）。

**结论**：**MISALIGNED**（传播不全 + 边界未成文）。
**建议**：同步 P3-tdd/dispatch-prompt 的规则号；在 README 或 CHANGELOG 写明 R6 的默认扫描面；
把 scripts/ 的 5 处同类缺陷登记 DEBT 或一并修。

---

### A6: 锚点表覆盖

CHECK 9 锚点（`agate/scripts/check-protocol-consistency.py:800-804`）：
```python
{"desc": "平台假设静态扫描器（TAG0009：Unix 假设检出 + CI 阻断）",
 "script": "agate/scripts/check-platform-assumptions.py",
 "keywords": ["平台假设", "R1", "R2"]},
```
以及 `check-state-transition.py` 的 4 条锚点（:608-627，关键词 `MAX_RETRY`/`diff,phase_num`/`前向跨阶`/`RM-AG0042`）。

本批为既有脚本的**规则增补/收窄**，未新增脚本、未新增协议规则条目；锚点关键词均仍命中（实测
`check-protocol-consistency.py` CHECK 9 PASS）。**无需更新锚点表**。

**结论**：**ALIGNED**。

---

### A7: 设计原则一致性

- **ADR-014（判据单一权威源，`adr.md:533-575`）**：R6 的判据（文本模式缺 `encoding=`）在脚本内**单点
  实现**（`_r6_text_without_encoding_hits`），未在别处复制第二套 ⇒ 符合。但 A2③ 的「见 README 判据边界」
  是 ADR-014 要求的「文档指向权威源」的**失效指针**（目标不存在）——该缺陷已归 A2，不在 A7 重复计。
- **ADR-002（可判定性）**：R6 为二值判定（命中/不命中），可机械判定 ✓。
- 未发现需要新增 ADR 的架构决策。

**结论**：**ALIGNED**。

---

### A8: 声称-命令绑定

| 声称（来源）| 产出命令 | 实测结论 |
|---|---|---|
| **83 passed**（实现者汇报）| `python3 -m pytest agate/tests/scripts/test_check_platform_assumptions.py agate/tests/unit/test_check_state_transition.py -q` | ❌ **不可复现**：实为 **78 passed**（18 + 60）。试 `agate/tests/scripts/`(18)、+`test_release_workflow.py`(96) 等组合均非 83。**须改正或删除** |
| **2906 passed**（实现者汇报）| `python3 -m pytest agate/tests/ -q -n auto -p no:cacheprovider` | ❌ **不符**：实为 **2 failed, 2905 passed, 2 skipped**（2 failed 非本批，见 A4b，但「2906 passed」把失败掩盖了）。**须改为如实计数** |
| **0 ERROR**（CHANGELOG/tech-debt/roadmap）| `python3 agate/scripts/check-protocol-consistency.py` | ✅ 复现：`仅有 424 个 WARNING，无 ERROR`，rc=0 |
| **扫描 0 命中**（DEBT0058 关单证据）| `python3 agate/scripts/check-platform-assumptions.py agate/tests` | ✅ 复现 rc=0（**仅 tests/ 口径**；扫 `agate/scripts` 为 rc=1、5 处 R6 命中，见 A5）|
| **check-debt rc=0**（tech-debt 关单）| `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ 复现 rc=0 |
| **抓到 3 处真缺陷（test_release_workflow.py）**（CHANGELOG:85 / roadmap:104 / DEBT0053+0058 关单）| `git show HEAD:agate/tests/unit/test_release_workflow.py` 过 `_r6_text_without_encoding_hits` | ✅ 复现：HEAD tests 树 R6 命中恰 3 行（186/268/275）——但**口径仅 tests/**；scripts/ 另有 5 处同类（A5）|

**结论**：**MISALIGNED**。
**建议**：把「83 passed」「2906 passed」改为可复现的实测值（78 passed；全量 2905 passed / 2 failed /
2 skipped 并注明失败非本批）；「抓到 3 处真缺陷」加注「（扫描面 = tests/）」。

---

## 五项重点结论（对应任务派发）

1. **BDD-3 收窄误报/漏报面**：正例（含 `subagent` 真事件）命中 ✓、散文（无 `subagent`）不命中 ✓、
   文档引用（含 `.md`）不命中 ✓；**漏报面**（不含 `subagent` 的真事件，如「（上次空返回后重跑）」）
   会漏——该取舍**已如实写在代码注释** `check-state-transition.py:79-82`（「会漏掉…未点名 subagent 的
   真事件…漏报可接受」）。中文「重派」的正常用法（如「→ 重派 requirements-review」）由
   **「须含 subagent/子代理」** 这条兜住（实测不命中），卡片块剥离（RM-AG0101）另覆盖卡片正文——两条
   叠加已足。
2. **R6 调用级实现正确性**：嵌套括号 ✓、多行 f-string ✓、`text=` 紧跟 `)` ✓、`universal_newlines` ✓；
   但**同一行两调用→漏报**、**`encoding=` 在字符串/注释→假阴**、**>40 行窗口→误报/漏报**、
   **注释/docstring 提及→误报**、**`subprocess.PIPE` 等属性行吞后续括号→误报**（实测）。「40 行上限」
   确会截断致错；docstring 声称的局限「同**文件**多调用」**描述不准**（真局限是「同**行**多调用」），
   且引用「见 README 判据边界」——**该节不存在**。
3. **`test_bdd_1` 断言改写是否保持本意**：新正则 `subprocess\.\w+\s*\(|os\.system\s*\(|os\.popen\s*\(`
   能抓 `subprocess.run(`/`Popen(`/`check_output(`/`os.system(`/`os.popen(`（含 `run (` 带空格）✓；
   **绕过面**：`import subprocess as sp; sp.run(`、`from subprocess import run; run(`、
   `getattr(subprocess,"run")(`、裸 `import subprocess` 均不命中（旧的子串判定会命中）。本意「不得**调用**」
   基本达成，别名/反射为可接受的残余面。
4. **A4b**：本批使 **2 条既有用例**转红（`test_bdd_1` 子串断言、`test_bdd_8` 全树 0 命中），均在批内
   处置（改断言 / 补 `encoding=`）；其余既有用例（BDD-3 五条 + cross_milestone bdd_16）经实测不红。
   逐条见 A4b。
5. **A8 逐条复现**：见 A8 表——`0 ERROR`/`扫描 0 命中`/`check-debt rc=0`/`3 处真缺陷` 复现成功；
   **`83 passed` 与 `2906 passed` 不成立**。

---

## 需修复项（主 Agent 动作）

**MISALIGNED（须修）**：
1. `agate/scripts/README.md:91` 改「R1-R6」；扫描器 docstring（:18-24,134）补 R6。
2. 修悬空引用 `check-platform-assumptions.py:55`（增 README「判据边界」节 或 改指向实际权威源），
   并把 R6 的调用级近似/假阴假阳面写入该节。
3. 传播 R6 到 `agate/phase-cards/P3-tdd.md:104`、`agate/assets/templates/dispatch-prompt.md:146`
   （`test-designer.md` / `tests/README.md` 视成本顺手补）。
4. 加强 `test_check_state_transition.py:1205` 的散文负例（改用含「重派」但无 subagent 的串）；为 R6
   补「跨行同调用不误报」「属性行不误报」用例。
5. 改正 A8 两处不可复现数字（83→78；2906→2905 passed / 2 failed / 2 skipped 并注明非本批）。
6. （建议）R6 扫描面边界成文 + `agate/scripts` 的 5 处同类缺陷登记 DEBT 或一并修。

**NEEDS_HUMAN_REVIEW**：无。

---

*留痕文件：`docs/reviews/agate-alignment-2026-10-09-A0105-SCAN-01.progress.md`*
