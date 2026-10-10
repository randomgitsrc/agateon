---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: 清账+债务清欠批——roadmap 新增「范围」节、RM 收窄/关单、DEBT0060/0061/0062 关单 + DEBT0015 重定范围、check-obligations R 判据收窄并升 ERROR
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate-workspace/tasks/active-tasks.md
  - agate/LIMITATIONS.md
  - agate/rules/obligations.yaml
  - agate/scripts/check-obligations.py
  - agate/tests/unit/test_tag0050_obligations.py
---

# 协议-脚本对齐审查（TRIAGE-01）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（① `obligations.yaml` 新增 5 处重复键；② `LIMITATIONS.md`「版本定位边界」与 `agate-ci-verify.py` 实现不符） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`warnings` 已成死代码但注释/README 未同步；`_check_review_output` 注释 stale；obligations.yaml 头部字段表未列 `review_output`） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（roadmap 新节引不存在的 `SELF-GATE.md 轻量档`；P4-implementation-G1.md 的 DESIGN_GAP 未随 DEBT0062 关单标注已闭合） |
| A4 | 测试覆盖 | **ALIGNED**（`test_bdd_43` 已按新语义改写；实跑全量：1 failed 环境性 + 2909 passed + 3 skipped） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **空清单**：唯一既有用例 `test_bdd_43_r_without_review_output_errors` 已同批改写；经实跑**无其他既有用例转红**（仅 1 条环境性 failed） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（DEBT0060 的 LIMITATIONS 表述不准确；CHANGELOG「补 review_output（12 条）」不精确；无对用户项目的破坏性变更——`check-obligations.py` 不在 hook/CI 路径） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9 锚点 keywords `["obligations.yaml","M 类占比","无归宿"]` 未变、仍字面存在，CHECK 9 PASS） |
| A7 | 设计原则一致性 | **ALIGNED**（无相关 ADR；本批为热修语义收窄，未引入未记录架构决策） |
| A8 | 声称-命令绑定 | **MISALIGNED**（roadmap「7 个 PR / 12+ 处」无命令；「2910 passed」实跑未复现；「补 review_output（12 条）」把 7 新增+5 重复并称） |

**总判定：不可 commit**——A1/A2/A3/A5/A8 存在 MISALIGNED，须修复后重审（见文末「是否可 commit」）。

---

## 逐项审查

### A1: 文档→脚本对齐

#### A1-1（BLOCKER）：`agate/rules/obligations.yaml` 新增 5 处重复键 `review_output`

**本次改动引入**：`git diff` 在 OBL-P1-06 / OBL-P2-13 / OBL-P2-14 / OBL-P2-15 / OBL-P4-07 各**新增一行** `review_output:`，而**这 5 条原本就已含** `review_output:`（在 `script: ""` 之后）⇒ 每个映射出现**两个同名键**。

证据（`agate/rules/obligations.yaml`）：

```
132:  - id: OBL-P1-06
136:    disposition: R
137:    review_output: P1-review.md      # ← 本次新增
138:    script: ""
139:    review_output: P1-review.md      # ← 原有（重复）
```
（OBL-P2-13 → 312/314；OBL-P2-14 → 321/323；OBL-P2-15 → 330/332；OBL-P4-07 → 459/461，同形。）

实测（严格解析器探测）：
```
$ python3 -c "<SafeLoader 加 dup 检测>"
DUP: duplicate key 'review_output' at line 139
```

**语义判断**：PyYAML `safe_load` 对重复键 **last-wins、不报错**（两处值相同，故当前 rc=0、行为未变）——**属潜伏缺陷**：换严格解析器即由 PASS 变 FAIL。更严重的是，**该文件头部注释自己就警告过这个坑**：

```
agate/rules/obligations.yaml:40-41
# ⚠️ YAML **单键**：历史上两次重设合并为一条（避免重复键——重复键下 PyYAML last-wins，
# 结果正确但依赖键序，换严格解析器会由 PASS 变 FAIL；SELF-GATE 评审 r1 指出）。
```

**结论**：MISALIGNED（BLOCKER）。
**建议**：删掉 5 处**本次新增**的重复行（保留原有那行，或反之，只留一处）。

#### A1-2（重点）：DEBT0060 的 LIMITATIONS 表述 vs `agate-ci-verify.py` 实现（逐条核三种情形）

**文档**（`agate/LIMITATIONS.md:139-145`）：
> - 仓库**写了** `.agate-version`（或仓库本身含协议本体）→ 用该版本；**单调不降**另有检查；
> - 仓库**没写** → 用**当前**协议回放 ⇒ 对「按当时协议书写」的历史提交可能**误判或漏判**；
> - **某提交缺失** `.agate-version`（仓库整体写了、个别提交没写）→ **不判 FAIL**（已知绕过面）。

**脚本**（`agate/scripts/agate-ci-verify.py`）：

| 实现分支 | 行号 | 行为 |
|---|---|---|
| `.agate-version` 用途 | `:32-34` docstring；`:151-152` `_version_in_commit`；`:543-555` 唯一调用点 | **只用于「单调不降」检查，不用于选协议根** |
| ① `AGATE_ROOT` 提供协议 | `:199-208` | 用其仓库 `merge-base(base,HEAD)` 处的 `agate/`；失败回退 `AGATE_ROOT`（**当前**协议） |
| ② 仓库含协议本体 | `:209-216` | 用仓库 `merge-base(base,HEAD)` 处的 `agate/` |
| ③ 二者皆无 | `:571-576` | `return _fail("未固定协议版本…请写 .agate-version")` → **FAIL** |
| 某提交缺失 `.agate-version` | `:546-549`（`v is None: continue`） | 不判 FAIL |

**逐条比对**：

- **bullet 3 = ALIGNED**：`:546-549` 的 `continue` 确使「个别提交缺 `.agate-version`」不判 FAIL，与 docstring「已知绕过面」一致。
- **bullet 1 = MISALIGNED**：文档说「写了 `.agate-version` → **用该版本**」，但脚本明确 `.agate-version` **不用于选协议根**（`:33-34`）。真正的版本选择来自 `AGATE_ROOT`/仓库本体在 `base` 处的 `agate/`（`:199-216`）——**与 `.agate-version` 里钉的版本无关**。
- **bullet 2 = MISALIGNED**：文档说「仓库**没写** → 用**当前**协议回放」，但脚本在「未写 `.agate-version` **且**非协议本体」时**直接 FAIL**（`:571-572`），并非「用当前协议回放」；且 `AGATE_ROOT` 即便设置也不改此结论（`:569-570` 注释明确）。

**结论**：MISALIGNED（A5 同见）。
**建议**：把「实际判定」三条**改写成脚本的真实分支**（AGATE_ROOT 提供协议 / 仓库含协议本体 / 二者皆无 → FAIL；`.agate-version` 仅用于单调不降），删除「写了 .agate-version → 用该版本」「没写 → 用当前协议回放」这两条不实表述。

#### A1-3（重点）：DEBT0061「原诊断有误」的成立性——T3 被漏

**DEBT0061 关单注**（`tech-debt.md`）：
> 原诊断有误——「绊线无任何消费方 ⇒ 命中即拦不成立」不成立：T1 由 `count_p7_markers` 消费、T2 由 `check-gate.py:771-785` 硬拦（BDD-71）、T4 由 gate 消费。真正「无消费方」的是契约快照里的 `traps`/`downgrade` 键本身…

**独立核**（各绊线的真实消费方）：

| 绊线 | 定义（`agate/rules/task-data/level-1.yaml`） | 消费方（实测） | 结论 |
|---|---|---|---|
| T1 `positive_declaration_in_prose` | `:246-264` | `count_p7_markers`（`agate_common.py:1611`，BLOCKER/DEVIATION-CRITICAL）+ `count_design_gap`（`:1632`）+ `count_code_map_lines`（`:1647`） | 有消费方 ✓ |
| T2 `bdd_heading_format` | `:265-267` | `check-gate.py:771-785`（硬拦，BDD-71） | 有消费方 ✓ |
| **T3 `strict_verdict_line_in_prose`** | **`:268-270`** | **全仓 0 命中**——字符串仅出现于 `level-1.yaml:269` 本身 | **无消费方 ✗** |
| T4 `prod_touched_safety_gate` | `:271-274` | `pre-commit-gate.py:241-251`（PROD_TOUCHED 扫描） | 有消费方 ✓ |
| `traps` / `downgrade` 键本身 | `:245-274` | 脚本 0 命中（仅同名测试函数，语义无关） | 描述性 ✓ |

实测：
```
$ grep -rn "strict_verdict\|traps\b\|\"downgrade\"\|T3\b" agate/scripts/*.py
（无输出）
$ grep -rn "strict_verdict_line_in_prose" agate/ --include=*.py --include=*.md
agate/rules/task-data/level-1.yaml:269:    kind: strict_verdict_line_in_prose
```

**结论**：MISALIGNED / NEEDS_HUMAN_REVIEW。关单注把 T1/T2/T4 列为已消费（成立），却**整条漏掉 T3**——而 T3 恰是**原 DEBT 标题点名的对象之一**（「T1/T2/T3 绊线…」）。关单理由「命中即拦 成立」对 T3 **不成立**：`strict_verdict_line_in_prose` 无任何 gate 侧扫描。
**建议**：二选一——(a) 保留 DEBT0061 open（T3 部分未接线）；或 (b) 在关单注中**显式**说明 T3 的处置（「已明确不实现/仅记录不判定」并同步文档），且**不能再笼统声称「命中即拦成立」**。CHANGELOG 同步条（「T1…T2…T4…」）同此问题。

#### A1-4（重点）：12 条 `review_output` 取值逐个抽查

`_QUALIFIED_REVIEW_OUTPUTS = ("P1-review.md","P2-review.md","P4-review.md")`（`check-obligations.py:51`）。逐条核 anchor/statement 与所指产出：

| 义务 | phase | review_output | anchor / statement 摘要 | 判定 |
|---|---|---|---|---|
| OBL-P1-06 | P1 | P1-review.md | review-mapping.md#映射规则「requirements-review 强制派发」 | 对得上 ✓ |
| OBL-P1-07 | P1 | P1-review.md | P1-requirements.md#同类扫描「同类扫描结论写入正文」 | 对得上 ✓ |
| OBL-P1-14 | P1 | P1-review.md | P1-requirements.md#P1 基线保护 | 对得上 ✓ |
| OBL-P2-05 | P2 | P2-review.md | P2-design.md#影响面梳理 | 对得上 ✓ |
| OBL-P2-09 | P2 | P2-review.md | P2-design.md#派发「minimal_validation」 | 对得上 ✓ |
| OBL-P2-13/14/15 | P2 | P2-review.md | review-mapping.md#映射规则（plan-eng/design/ceo） | 对得上 ✓（P2 评审产出确为 P2-review.md） |
| OBL-P2-16 | P2 | P2-review.md | P2-design.md#项目侧架构决策 | 可接受（P2 评审承载） |
| OBL-P2-17 | P2 | P2-review.md | P2-design.md#评审派发「组长汇总」 | 对得上 ✓ |
| OBL-P4-02 | P4 | P4-review.md | implementer.md#认知模式「P3 测试变绿」 | 可接受（P4 评审核测试是否变绿） |
| OBL-P4-07 | P4 | P4-review.md | review-mapping.md#映射规则「review/design-review/cso 派发」 | 对得上 ✓ |

**取值本身**：逐条与所在阶段的评审产出**一一对应**，未发现错配。
**但**：其中 OBL-P1-06 / P2-13 / P2-14 / P2-15 / P4-07 **5 条的「新增」是重复写入**（见 A1-1）——即**真正新增的只有 7 条**。

**结论**：取值 ALIGNED；新增计数 MISALIGNED（见 A1-1、A8）。

#### A1-5（重点）：判据收窄的正确性与安全性

**(a) `P6.5` 是否被 `P6-` 误匹配？** 否。判据为 `a.startswith(_ph + "-")`（`check-obligations.py:295`）：phase=`P6.5` 时比对 `"P6-review.md".startswith("P6.5-")` = **False** ⇒ 不误匹配。同理 `P10` 不会被 `P1-` 命中（分隔符 `-` 起保护作用）。实测该 R 项（OBL-P6-12，phase=P6.5）在收窄后**静默、不告警不判错**，符合「协议无 P6.5 评审产出」的事实。**安全**。

**(b) 会不会掩盖真缺口？** 有两处残余风险：
1. **无 `phase` 字段的 R 被静默跳过**：`_ph = ""` ⇒ `_has_artifact` 恒 False ⇒ 既不检查也不告警。当前 registry 中**所有 30 条 R 均有 `phase`**（实测），故**无现存实例**；但这是一条「静默」通道——将来新增 R 若漏写 `phase` 且属 P1/P2/P4，会被无声放过。
2. **`_QUALIFIED_REVIEW_OUTPUTS` 与真实评审产出脱耦**：若协议将来新增某阶段的评审产出文件（如 `P5-review.md`）却忘了加入该常量，则该阶段 R 会被**静默**视为「无产出」。当前无机械判据把两者绑定。

**结论**：判据本身 ALIGNED（P6.5 安全），但**残余风险应记为后续加固点**（建议：对「P1/P2/P4 之外的阶段出现 `*-review.md` 产出」或「R 缺 `phase`」给一条 WARNING/CI 断言）。

**(c) 升 ERROR 对用户项目是否安全？** **安全**。`rules/obligations.yaml` 位于 `agate/`（协议本体），是**协议自有单份**，非各项目各有；`check-obligations.py` 的 `_resolve_root()`（`:62-80`）解析到 `AGATE_ROOT`/协议根。实测该脚本**不在任何 hook / CI 路径**：
```
$ grep -rn "obligations" .github/            # 空
$ grep -n "obligations" agate/scripts/pre-commit-gate.py   # 空
```
唯一机械引用是 `check-protocol-consistency.py:855` 的 **CHECK 9 锚点表**（结构存在性），以及 pytest。⇒ ERROR 升级只作用于 agate 自身 registry 与测试，**不影响使用者项目**。

---

### A2: 脚本→文档对齐

1. **`warnings` 已成死代码**：`_evaluate` 中 `warnings = []`（`:251`），本次**删除了唯一的 `warnings.append`**（原 R 缺 `review_output` 的 WARNING）。此后 `warnings` 恒为空，`main()` 的 `for warn in warnings: ... WARNING ...`（`:357-358`）成死代码。而脚本 README（`agate/scripts/README.md:94`）与退出码描述**仍把 WARNING 作为可输出项**、且失败原因只列「无归宿项 / M 类占比低于基线」——**未列**「P1/P2/P4 的 R 缺 `review_output`」这一**新增 ERROR**。→ MISALIGNED。
2. **`_check_review_output` 注释 stale**（`:229`）：`return  # 缺 review_output 的 R 交由调用方按「改标 C」提示（不阻断，见 _evaluate）`——调用方现已**不再**「提示改标 C」，且对 P1/P2/P4 **判 ERROR**。→ MISALIGNED（注释与实现相反）。
3. **obligations.yaml 头部字段表**（`:14-23`）列出 `id/phase/statement/anchor/disposition/script/evidence`，**未列 `review_output`**——本次给 12 条 R 增补该字段却未登记其语义。→ 轻微 MISALIGNED。

**建议**：同步 README 退出码/失败原因、修 `_check_review_output` 注释、把 `review_output` 补进头部字段表。

---

### A3: 一致性连锁 + 反向传播

**应被影响文件清单与验证**：

| 应被影响文件 | 理由 | 实测 |
|---|---|---|
| `agate/scripts/README.md` | 脚本退出码/失败原因变化 | **未同步**（见 A2）✗ |
| `agate/rules/obligations.yaml` 头部字段表 | 新增 `review_output` 语义 | **未同步** ✗ |
| `agate/scripts/check-obligations.py` docstring `:15` | R 判据收窄 | 未提收窄（仍写「须是合格评审产出」）△ |
| `agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G1.md` | 其 `[DESIGN_GAP: A4 的 review_output 缺失判 WARNING（设计原文为 ERROR）]` 现已被 DEBT0062 消解 | **未标注「已闭合」** ✗ |
| `CHANGELOG.md` | 语义变更留痕 | 已加（但计数不精确，见 A8）△ |
| `agate-workspace/roadmap/roadmap.md`「范围」节 | 与 AGENTS.md/SELF-GATE.md 口径一致 | **引不存在的 `SELF-GATE.md 轻量档`；「不派评审」与 AGENTS.md 轴 C 相悖** ✗ |
| `check-gate.py` 是否读 obligations | 反向核查 | 不读（无关联）✓ |

**roadmap「范围」节的具体不一致**（`roadmap.md:15-21`）：
> 2. **为小改动强加的仪式**——单一主题 + 可快速验证的改动：不立项、**不派评审**（`AGENTS.md` hotfix 通道 + **`SELF-GATE.md` 轻量档**）。

- `SELF-GATE.md` **没有「轻量档」概念**（全仓 `grep 轻量` 无「轻量档」；SELF-GATE.md 只有 Layer 0/1）⇒ **悬空引用**。
- 「不派评审」与 `AGENTS.md` 轴 C 直接相悖：**碰 SELF-GATE 触发面 → 须独立评审**（`AGENTS.md:25,42,59`）。hotfix 通道**只免立项**，不免评审。

**结论**：MISALIGNED。
**建议**：删「`SELF-GATE.md` 轻量档」或改为真实条文；把「不派评审」改为「不立项；碰 SELF-GATE 面仍须独立评审」。

---

### A4: 测试覆盖

- **新语义有回归用例**：`test_tag0050_obligations.py::test_bdd_43_r_without_review_output_errors` 已改写，断言 ① P2 R 缺 → ERROR；② X 阶段 R 缺 → 无告警无错；③ 合格产出 → 无告警；④ 非合格产出 → ERROR；⑤ 端到端真实 registry rc=0。
- **实跑全量**（`/tmp/opencode` 副本，`--reruns 1 -n auto`，与 CI 同口径）：
  ```
  1 failed, 2909 passed, 3 skipped, 1 rerun in 105.69s
  ```
  唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，原因 `Unknown subcommand "agent" for "opencode debug"`（**本机 opencode CLI 子命令漂移，环境性**，与本次改动无关）。

**结论**：ALIGNED。**注意：不称「全绿」**——有 1 条环境性 failed。

**小瑕疵**：`test_bdd_43` 端到端注释（`:285`）仍写「真实 obligations.yaml 上同样 rc=0（**缺 review_output 不阻断**）」——新语义下 P1/P2/P4 缺 `review_output` 会**阻断**，该注释已 stale（断言 rc=0 仍成立，因 registry 已无缺口）。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单

**清单（非空）**：

| 既有用例 | 处置 |
|---|---|
| `agate/tests/unit/test_tag0050_obligations.py::test_bdd_43_r_without_review_output_errors` | **同批改写**（按收窄后语义重写断言与 docstring） |

**夹具更新**：无新增/更新夹具（测试用 `_data()` 内联构造 registry，未依赖外部 fixture 结构）。

**其余既有用例**：经实跑全量（`-n auto`）**无其他既有用例转红**（仅 1 条环境性 failed，与本改动无关）。全仓仅 `test_bdd_43` 引用 `review_output`（`grep` 实测），无第二处依赖旧 WARNING 语义。

---

### A5: 下游影响 + 文档传播

- **对用户项目的破坏性变更**：**无**。`check-obligations.py` 不在 hook/CI 路径（A1-5c 实测），`obligations.yaml` 协议自有单份。ERROR 升级只作用于 agate 自身。
- **CHANGELOG**：已加「债务清欠批」条（`:143-157`），但计数不精确（「补 `review_output`（12 条）」，实为 7 新增 + 5 重复）——见 A8。
- **LIMITATIONS**：新增节存在不实表述——见 A1-2。
- **roadmap 新「范围」节**：与 AGENTS.md/SELF-GATE.md 不一致——见 A3。

**结论**：MISALIGNED（文档传播不完整/不准确；无下游破坏性变更这一半为 ALIGNED）。

---

### A6: 锚点表覆盖

`check-protocol-consistency.py:854-857` 的 CHECK 9 锚点：
```
"script": "agate/scripts/check-obligations.py",
"keywords": ["obligations.yaml", "M 类占比", "无归宿"],
```
本次改动**未移除**这三个字面串（实测 `check-obligations.py` 仍含），CHECK 9 实跑 **PASS**。新增/变更的判据属脚本内部逻辑，无需新增锚点（CHECK 9 只验证「脚本存在 + 关键词在」，不验证语义——后者按角色文件说明仍需 A1 人工核对，已在 A1 完成）。

**结论**：ALIGNED。

---

### A7: 设计原则一致性

- `grep` 实测 `agate/adr.md` 中**无** `obligations`/`review_output`/`DEBT0062` 相关条目 ⇒ 本批**无对应 ADR 可逐条核**。
- 本批为**热修语义收窄**（把不可行动 WARNING 改可行动 ERROR + 收窄扫描面），未引入新的架构决策。
- 与既有「hotfix 通道」原则（`AGENTS.md`）的关系：本批**碰 SELF-GATE 触发面**（改 `agate/scripts/*.py`、`agate/rules/*.yaml`、`agate/*.md`）⇒ 须独立评审（即本报告）+ 提交信息含 `self-gate-review:`。**这一原则与 A3 中 roadmap「不派评审」的表述相悖**（已计入 A3）。

**结论**：ALIGNED（无未记录架构决策）。

---

### A8: 声称-命令绑定

逐条列 `声称 → 命令 → 结论`（均在 `/tmp/opencode/agateon-triage` 副本或只读命令上实跑）：

| 声称（出处） | 命令 | 结论 |
|---|---|---|
| `0 ERROR`（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | ✅ rc=0，0 ERROR（432 冻结 WARNING） |
| `check-obligations 0 WARNING` | `AGATE_ROOT=./agate python3 agate/scripts/check-obligations.py` | ✅ rc=0，无 WARNING 行（M 56/121） |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ rc=0 |
| `roadmap 0 异常` | `<replicate _check_roadmap_done 列数判据>` | ✅ 0 行列数异常 |
| `ruff` | `ruff check check-obligations.py test_tag0050_obligations.py`（0.16.4） | ✅ rc=0 |
| `2910 passed`（任务书复现项） | `pytest agate/tests/ --reruns 1 -n auto` | ❌ **实为 2909 passed + 1 failed（环境）+ 3 skipped**；「2910 passed」未复现 |
| DEBT0062「实测 25 条告警中 7 条属这些阶段…现 12 条 R 有产出指针」 | `yaml.safe_load` + 遍历 R | ✅ 25=30-5；P1/P2/P4 缺 7；R 有产出 12 |
| CHANGELOG「已给可指阶段的 R 补 `review_output`（12 条）」 | 同上 + `git diff` | ❌ 不精确：新增 12 行中 **5 行为重复**（原已存在），**真正新增 7 条** |
| roadmap「一轮 7 个 PR 的独立评审抓出 12+ 处作者自身错误」 | （无命令） | ❌ **无命令可给**；2026-10-09 评审文档实际远超 7 个（`ls docs/reviews` 实测 >25 个）。**须补命令或删声称** |
| RM-AG0096「`P[56]` 子串启发式已被替换（RM-AG0088/DEBT0033）」 | `sed -n '157-170p' agate/scripts/agate-debt-check.py` | ✅ 已改为「`closed` 须含 `closed_at`」 |
| RM-AG0097「`gitignore-fragment.txt:32` 已放行 P6-evidence」 | `grep -n P6-evidence agate/assets/templates/gitignore-fragment.txt` | ✅ `:32 !agate-workspace/tasks/**/P6-evidence/**` |
| RM-AG0065①「全仓未检出写真实仓库账本的测试」 | `grep -rn "append_event\|gate-events.jsonl" agate/tests/` | ✅ 均落 `tmp_path`/`git_repo` 副本；`test_events_ledger.py:16` 有硬规则 |
| RM-AG0065②「P3 agent 可由 agate-md-field-set 写入 + 回归用例」 | `grep -n "test_rm_ag0113_p3_agent" agate/tests/unit/test_agate_md_field_set.py` | ✅ 用例存在（`:542`），实现注释 `:498` 已解除旧拒写 |
| TAG0041 标完成（RM-AG0075/0076 均 done） | `<解析 roadmap 关联任务列>` | ✅ RM-AG0075/0076 状态均 `done`、关联任务均 `TAG0041` |
| DEBT0015「env_constraints 有真实消费方」 | `grep -n env_constraints agate/scripts/agate-extract-context.py` | ✅ `:161-163` 抽入派发上下文 |

**结论**：MISALIGNED——「2910 passed」「7 个 PR / 12+ 处」「补 review_output（12 条）」三处声称**无法由命令支撑或与命令结果不符**，按 A8 规则应**修正或删除**。

---

## 重点结论（任务书 6 项）

1. **DEBT0062 判据收窄是否正确且安全** —— 判据**正确**（P6.5 不会被 `P6-` 误匹配，实测 `startswith` 语义安全）；**升 ERROR 对用户项目安全**（registry 协议自有、脚本不在 hook/CI 路径）。但有两处**静默通道**应记为加固点：① 无 `phase` 的 R 被静默跳过（当前无实例）；② `_QUALIFIED_REVIEW_OUTPUTS` 与真实评审产出无机械绑定。
2. **12 条 `review_output` 取值** —— **逐条对得上**（anchor/statement 与所指 `*-review.md` 一一对应，无错配）；**但 5 条（OBL-P1-06/P2-13/P2-14/P2-15/P4-07）是重复写入**（原本已有）⇒ 实为 7 新增 + 5 重复，且**产生 5 处重复键**（BLOCKER）。
3. **DEBT0061「原诊断有误」是否成立** —— **部分成立**：T1/T2/T4 确有消费方（T1 经 `count_p7_markers` 等、T2 经 `check-gate.py:771-785`、T4 经 `pre-commit-gate.py` PROD_TOUCHED），`traps`/`downgrade` 键确为描述性；**但整条漏掉 T3**（`strict_verdict_line_in_prose` 全仓 0 消费方），而 T3 是原 DEBT 标题点名的对象。关单理由对 T3 **不成立**。
4. **DEBT0060 LIMITATIONS 是否与 `agate-ci-verify.py` 一致** —— **不一致**：bullet 3 符；**bullet 1、2 不符**（`.agate-version` 不用于选协议根；「未写 `.agate-version` 且非协议本体」直接 FAIL，而非「用当前协议回放」）。
5. **清账是否准确** —— `RM-AG0096`（`P[56]` 已替换 ✓）、`RM-AG0097`（gitignore 放行 ✓）、`RM-AG0065`①②（✓）、`TAG0041`（与 RM-AG0075/0076 的 done 一致 ✓）均**实测成立**；`RM-AG0102` 的「删版本号承诺」**基本成立**——[Unreleased] 与 UPGRADING 当前节已改为「未排期」，`CHANGELOG.md:283`（v0.79.0 历史节）仍含「截止版本 v0.80.0」**属冻结历史记录、不应回改**（口径可接受，唯措辞「已删」略宽）。
6. **A4b + A8 实跑数字** —— 见上：`1 failed（环境性）+ 2909 passed + 3 skipped`；`0 ERROR` / `check-debt rc=0` / `roadmap 0 异常` / `check-obligations 0 WARNING` / `ruff rc=0` 均复现；「2910 passed」**未复现**。

---

## 是否可 commit

**不可 commit（NEEDS_FIX）**。存在以下 MISALIGNED，按闭环规则须修复后重审：

| 优先级 | 项 | 修复方向 |
|---|---|---|
| BLOCKER | A1-1 `obligations.yaml` 5 处重复键 | 删除本次新增的重复 `review_output:` 行 |
| HIGH | A1-2 / A5 DEBT0060 LIMITATIONS 表述不实 | 按 `agate-ci-verify.py` 真实三分支改写 |
| HIGH | A1-3 DEBT0061 漏 T3 | 保留 open 或在关单注显式交代 T3 处置（勿笼统称「命中即拦成立」） |
| HIGH | A3 roadmap「范围」节悬空引用 + 「不派评审」 | 删/改「SELF-GATE.md 轻量档」；「不派评审」→「不立项；碰 SELF-GATE 面仍须独立评审」 |
| MED | A2 README/注释 stale、obligations.yaml 字段表 | 同步 `warnings` 死代码说明、`_check_review_output` 注释、字段表 |
| MED | A8 三处声称 | 修「2910 passed」为实测数；「12 条」改为「7 新增（另 5 条已存在）」；「7 个 PR/12+ 处」补命令或删 |

**ALIGNED 可直接保留**：A4（测试覆盖，含实跑）、A4b（既有用例清单）、A6（锚点）、A7（ADR）。A1-4/A1-5（取值与安全性）无缺陷。

修复 BLOCKER/HIGH 后重派本角色复审即可 commit。
