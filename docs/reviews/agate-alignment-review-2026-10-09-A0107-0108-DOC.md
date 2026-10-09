---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A 两条纯文档约束补强——implementer 不得以「保持既有测试全绿」为由不实现设计要求（RM-AG0107/DEBT0054）+ 不得预告未排期能力的实施版本号（RM-AG0108/DEBT0051）
files_changed:
  - AGENTS.md
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/UPGRADING.md
  - agate/assets/execution-roles/implementer.md
  - agate/assets/review-roles/protocol-alignment-review.md
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（两条新规均为文档/行为约束，**无脚本应对应实现**；但 RM-AG0108 的「验收锚」无机械 gate，见重点 3） |
| A2 | 脚本→文档对齐 | ALIGNED（本批**未改任何脚本**：`git status` 无 `.py`/`.sh`） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（A4b 只加进 role file「输出格式汇总表」，**未同步同一文件的「审查清单」主表**；SELF-GATE.md 派发模板与成果文件要求仍列 A1-A8） |
| A4 | 测试覆盖 | ALIGNED（纯文档变更，无新增用例合理；全量 pytest 2903 passed + 1 环境失败，见下） |
| A4b | **闭合后既有测试转红 + 夹具更新清单**（RM-AG0107 / DEBT0054） | ALIGNED（本批为文档改动，**经实测无既有用例因本批转红**；唯一红为环境性 `test_bdd_43`，与本批无关——详见 A4b 节） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（无 gate 行为变化 + CHANGELOG 已标 ✓；但 UPGRADING 新节被置于「版本管理生命周期」下，与该节自述职责语义错位） |
| A6 | 锚点表覆盖 | ALIGNED（CHECK 9 无涉及 role file A-项 的锚点；consistency 0 ERROR） |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW**（两条修复均属 ADR-015 手段③「要求人做对」；本批未记录为何不采用①②，且 DEBT0051 closure_criteria 称「机械或评审判据」而实际为自觉项） |
| A8 | 声称-命令绑定 | ALIGNED（4 条声称全部复现；1 处措辞不精确，建议收紧——见 A8 节） |

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**：
- `implementer.md:72-80` 新增「不得以『保持既有测试全绿』为由不实现设计要求」节。
- `agate/UPGRADING.md:46-51` 新增「版本号公告约束」节 + `AGENTS.md:169` 3a。

**脚本实现**：本批未触及 `agate/scripts/*`（`git status --porcelain` 无脚本文件）。两条规则均为**行为/人类约定**（implementer 角色纪律、发布公告纪律），其性质决定**不应对应机械脚本**。

**结论**：ALIGNED。
**差异**：无脚本 = 无「文档声明 vs 脚本实现」的不一致。**但** RM-AG0108 在 `roadmap.md:107` 的「验收锚=新公告的版本号承诺能反查到对应 RM/DEBT」隐含一个可查判据，当前**无任何 gate** 提供它（见重点 3）。

### A2: 脚本→文档对齐

**结论**：ALIGNED。
**依据**：`git diff` 未改任何 `.py`/`.sh`，不存在「脚本逻辑变更未同步文档」的方向。

### A3: 一致性连锁 + 反向传播

#### A3a 连锁（已知衍生改动）——**MISALIGNED**

**同一文件内两表分叉**：`agate/assets/review-roles/protocol-alignment-review.md` 有**两张 A-项 表**：

1. 「审查清单」主表（`20-33`，权威的「逐项检查」清单，表头 `| # | 审查项 | 说明 |`）——**仍是 A1–A8，无 A4b**；
2. 「输出格式」代码块内的汇总表（`81-91`）——**新增了 `A4b` 行（`87`）**。

**证据**：`agate/tests/integration/test_protocol_alignment_review.py::test_sg_2` 的注释（`44-47`）**明确区分**这两张表（「输出格式汇总表也有一行 `| A8 | ... |`……故先切出主清单表区段再逐项断言」），即本仓已把「主清单表」当作权威判据面守护。A4b 只进汇总表、不进主清单表 ⇒ **权威清单与实际要求输出项分叉**，正是 ADR-014（`adr.md:533-585`）「判据单源」所警告的「改一处漏其余、且无人能发现」形态。

**结论**：MISALIGNED。
**建议**：把 A4b 作为 **A4 的子项行**补入「审查清单」主表（与 `test_sg_2` 的 A1–A8 断言兼容，`range(1,9)` 不受影响），使「要检查什么」单源。

#### A3b 反向传播（主动推断的应被影响文件）——**MISALIGNED**

| 应被影响文件 | 现状 | 影响理由 |
|---|---|---|
| `SELF-GATE.md:128-136`（变更触发派发模板的 A1-A8 枚举） | **未同步**，仍逐项列 A1-A8 | 它是对 role file 清单的**复述**（ADR-014② 允许复述但须与源一致）；A4b 缺失 ⇒ 复述漂移 |
| `SELF-GATE.md:162`（成果文件要求「含 **A1-A8** 结论汇总表」） | **未同步** | 输出要求与 role file 的「输出格式」（含 A4b）不一致 |
| `agate/assets/review-roles/protocol-alignment-review.md:136`（人工验收清单「审查报告含 **A1-A8 八项**」） | **未同步** | 同一文件内的自验收清单，项数与新增 A4b 不符（应为 9 项） |
| `agate/phase-cards/P4-implementation.md`「常见错误」节 | 未提及新禁令（**可选**） | 新禁令是 implementer 角色纪律，权威源在 role file；P4 卡是主 Agent 视角，非必需同步（记为 NEEDS_HUMAN_REVIEW 级） |

**结论**：MISALIGNED（前 3 项为确定漂移，第 4 项为可选）。
**建议**：在 SELF-GATE.md 派发模板与成果文件要求、以及 role file 人工验收清单中同步 A4b（或把枚举改为「见 role file 清单」以彻底去副本，符合 ADR-014 ①「判据单源」）。

### A4: 测试覆盖

**变更性质**：纯文档（协议 `.md` + 工作区登记），无脚本/逻辑变更 ⇒ **无新增 pytest 用例是合理的**。

**全量实跑**（复现 CI 口径，`agate/tests/README.md:28`）：

```
python3 -m pytest agate/tests/ --reruns 1 -n auto -q
→ 1 failed, 2903 passed, 2 skipped, 1 rerun in 140.90s
```

唯一失败：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——`opencode debug agent orchestrator` 返回 `rc=1`（opencode CLI 参数/版本变化），**环境性**，与本草案改动面（文档 + 工作区登记）无因果关系（该用例不读 `implementer.md` / `UPGRADING.md` / role file）。

**结论**：ALIGNED。
**说明**：A4b 作为新审查项**无机械守护**（不同于 A1–A8 有 `test_sg_2`）——符合 ADR-015「非实质错误不设要求型规则」，但应知悉其约束力 = 约定。

### A4b: 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054）

**本次变更使哪些既有用例转红 / 需更新哪些夹具**：

> **经实测无既有用例因本批转红，无需更新任何夹具。**

- 本批改动集 = 4 个协议/根文档 + 3 个工作区登记文件，**不含任何脚本**；既有 pytest 用例中唯一可能读取 role file 的 `test_protocol_alignment_review.py::test_sg_2/2b` 只断言**主清单表**（`range(1,9)`）与 A8 行，A4b 落在输出格式汇总表 ⇒ **不触发**。
- 全量实跑（见 A4）唯一红为环境性 `test_bdd_43`，非本批引入。
- **该新增审查项本身**（A4b）未导致既有用例转红（无守护该行的用例存在）。

**结论**：ALIGNED。
**关联**：A4b 未进入 role file「审查清单」主表 —— 见 A3a。

### A5: 下游影响 + 文档传播

- **gate 行为影响**：无。两条规则均不改任何 gate/脚本，既有项目 gate 行为不变。
- **CHANGELOG 标注**：✓ 已标（`CHANGELOG.md:69-78`，位于 `[Unreleased] → ### 修复`）；CHECK 13（CHANGELOG↔UPGRADING 章节对应）PASS。
- **文档传播问题**：`agate/UPGRADING.md` 的新节（`46-51`）被插入到「版本管理生命周期」节（`40-44`）内，而该节**自称**是「**安装 / 迁移 / 更新 / 回退** 四个动作，以及 hook 重装时机、根 `scripts/` 维护语义的**单一权威口径**」。一条「发布公告约束」不属于这四类生命周期动作 ⇒ **语义错位**，且稀释该节的「单源」声明。规则本身与既有表述（`UPGRADING.md:329-331`、`524-526`、`545-547` 的「本协议不预告实施版本号」）**口径一致、无冲突**。

**结论**：NEEDS_HUMAN_REVIEW。
**建议**：把「版本号公告约束」移到与「发布」语义更贴合的落点（如独立小节/`AGENTS.md` 发布清单为主、UPGRADING 仅指针引用），或显式扩充「版本管理生命周期」节头使其名实相符。
**人工确认**：需主 Agent/作者确认「置于生命周期节」是否可接受。

### A6: 锚点表覆盖

`check-protocol-consistency.py` CHECK 9 锚点面（`check-protocol-consistency.py:546` 的 `("DESIGN_GAP", ".../implementer.md", ...)` 等）只做**关键词存在性**兜底，且**不覆盖 role file 的 A-项集合**。本批新增的 A4b / 公告约束**不需要**新增 CHECK 9 锚点。

**证据**：`python3 agate/scripts/check-protocol-consistency.py` → `rc=0`，CHECK 9 `✅ PASS`，**0 ERROR**（424 WARNING 全为冻结文件）。

**结论**：ALIGNED。

### A7: 设计原则一致性

相关 ADR：**ADR-014**（判据单源，`adr.md:533-585`）、**ADR-015**（实质/非实质 + 手段优先级，`adr.md:589-647`）。

- **ADR-014**：A3a 的「两表分叉」与 ①「判据必须单源」精神相抵（详见 A3a）。
- **ADR-015**：两条修复均属手段 **③「要求人做对」**（写规范 + 检查有没有照做）：
  - RM-AG0107：`implementer.md` 文字禁令 + role file 输出要求（无机械判据）；
  - RM-AG0108：`AGENTS.md` 发布清单项 + `UPGRADING.md` 文字约束（**无任何 gate**，`grep` 全 `agate/scripts/` 无「截止版本/未排期/实施版本号」判据；仅 `check-gate.py:739` 一条**不含版本号**的 WARNING 文案）。
  ADR-015 明确「手段③应尽量少用；只在实质错误 + 无法用①②解决时才用」。本批**未记录**为何不采用 ②「让错误可见」（例如对 `UPGRADING`/`CHANGELOG` 做「`截止版本 vN` ↔ 存在对应 RM/DEBT」的存在性扫描）。ADR-015 判「实质错误」的标准是「是否会导致后续错误决策」——RM-AG0108 的原始事故（TAG0042 无主公告）**确属实质**，故用③**未必违规**，但按 ADR-015 应给出「为何不用②」的留痕。

**结论**：NEEDS_HUMAN_REVIEW（设计原则为指导性，非硬规则）。
**建议**：在 DEBT0051/DEBT0054 的关单说明或提交信息中，显式记录「采用手段③的取舍理由」（尤其 RM-AG0108）。

### A8: 声称-命令绑定

| # | 声称 | 命令 | 结论 |
|---|------|------|------|
| 1 | `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✓ `rc=0`（closed 条目 `task_id` + evidence 含该 id + `closed_at` 齐备，符合 `agate-debt-check.py:158-173`） |
| 2 | `roadmap 0 异常` | `python3` 按 `check-gate.py:2159-2177` 同款解析（`line.split("|")` 长度 == `_ROADMAP_EXPECTED_COLS`(9)） | ✓ 全 `^\|\s*RM-` 行 **0** 列数异常；RM-AG0107/0108 均 9 段、`status=done`、关联任务列正确 |
| 3 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✓ `rc=0`，CHECK 1–16 无 ERROR（424 WARNING 全冻结） |
| 4 | `全量 2903 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✓ **2903 passed**（同批 **1 failed** 环境性 + 2 skipped + 1 rerun） |

**结论**：ALIGNED（4 条均可复现）。

**建议收紧（措辞，非删除声称）**：
- `tech-debt.md:2028`（DEBT0051 closure_note）与 `:2140`（DEBT0054）写「该 hotfix 的 **P5/P6 等价验证** = 全量 pytest + ... 0 ERROR」——全量 pytest **非全绿**（1 环境失败）。建议按批 B/A0104 先例改为「全量 pytest **2903 passed**（+1 环境失败，与本批无关）+ consistency 0 ERROR」，避免被读成「全绿」。
- `tech-debt.md:2033/2145` 的「触 agate/ **协议本体与脚本**」——本批**只触协议本体（.md），未触脚本**；该措辞为复制自 `hotfix-batchB-*` 的样板（先例 DEBT0046/0049 确实存在，但 DEBT0046 的 task_id 为 `TAG0043-check-registration`、DEBT0049 为 `hotfix-batchB-H1`，均确为无任务目录的批次名，**先例引用成立**）。建议本批删去「与脚本」三字。

---

## 五项重点结论

### 重点 1：A4b 新增是否自洽 → **不自洽（MISALIGNED）**

- A4b **只**加进了 `protocol-alignment-review.md` 的「**输出格式**」代码块汇总表（`87`），**未**加进同一文件的权威「**审查清单**」主表（`24-33`）。
- 本仓已把「主清单表」当作权威面守护（`test_sg_2` 显式切出主表断言、并区分输出汇总表）⇒ 这是**判据面与实际输出项分叉**（ADR-014 所警告形态）。
- **连带未同步**：`SELF-GATE.md:128-136`（A1-A8 枚举）、`SELF-GATE.md:162`（成果文件要求「含 A1-A8 结论汇总表」）、role file 人工验收清单 `136`（「A1-A8 八项」）。
- **建议**：把 A4b 作为 **A4 子项**补入主清单表，并同步上述三处（或改为指针引用 role file 清单以去副本）。

### 重点 2：implementer 新禁令的边界

- **与既有条文有措辞张力**：`implementer.md:20`「不改测试去迁就实现」、`:48`「不修改测试本身」、决策树 `:26`「测试断言与 P1 BDD 矛盾 → 标 `[DESIGN_GAP]`，不改测试」——新节 `:74-75` 却要求「**同步更新受影响的既有测试/夹具**」。文本未显式区分「**P3 任务测试**（契约定义，不得改）」与「**仓库既有测试**（随契约演进须更新）」⇒ 抵触型 implementer 可援引 `:48` 拒绝更新既有测试，**正是 DEBT0054 想根除的行为**。建议补一句边界定义。
- **出口指向不精确（可能有误）**：新节 `:80` 把「你认为设计要求**本身**有误」的出口指向 `[DESIGN_GAP]` / `[SCOPE+]`。但：
  - `[DESIGN_GAP]`（`:119-131`）语义 = 「P2 设计**有歧义/缺口**而**自主做了决策**」，**不是**「质疑需求」；
  - `[SCOPE+]`（`:133-135`）语义 = 「发现**新隐含需求**」，**不是**「设计有误」；
  - role file 已有**专为此设**的 `[CLARIFY: xxx]`（`:111-117`：「如对 P2 方案有疑问」→ 派 architect 解答），新节**未提**。
  建议把「设计要求有误」的出口改为 `[CLARIFY]`（或同时列出并说明三者区别）。
- **无滥用口**：`[DESIGN_GAP]` 须配 `[DESIGN_GAP_REVIEWED]`（`dispatch-protocol.md:962-966`）、`[SCOPE+]` 须配 `[SCOPE_RESOLVED]`（`WORKFLOW.md:455`），均有闭环 ⇒ implementer **不能**靠声称「设计要求有误」静默豁免（申报会被主 Agent/architect 复核）。
- **与 P4 卡「自查≠gate」一致**：新节不涉 gate 语义（`P4-implementation.md:53-58` 是「自查≠P5 gate」），无冲突。

### 重点 3：RM-AG0108 是否可机械核验 → **不可，纯自觉 + 文档**

- `grep -rn "截止版本\|未排期\|实施版本号" agate/scripts/` → **无任何 gate 判据**；唯一命中是 `check-gate.py:739` 的一条 WARNING 文案（且**不含版本号**，属既有 RM-AG0102 欠账的提示，非新判据）。
- 规则落点 = `AGENTS.md` 发布清单 3a（**人类发布流程**）+ `UPGRADING.md` 文字约束，**无脚本、无 CI、无评审角色显式检查项**。
- DEBT0051 的 `closure_criteria`（`tech-debt.md:2030`）写「该条有**机械或评审判据**（新公告的版本号承诺能反查到对应 RM/DEBT）」——实际提供的是**发布清单自觉项**，机械判据（②）与指派评审（③-评审）**皆无**。⇒ 建议在 closure_criteria/closure_note 中**显式承认「自觉 + 评审」**，或补一条机械扫描（ADR-015 ②「让错误可见」，如 `UPGRADING`/`CHANGELOG` 中 `截止版本 vN` 模式须能反查到对应 RM/DEBT）。

### 重点 4：反向传播未同步项（汇总）

1. **MISALIGNED**：`protocol-alignment-review.md` 审查清单主表（`24-33`）缺 A4b。
2. **MISALIGNED**：`SELF-GATE.md` 派发模板 A1-A8 枚举（`128-136`）未含 A4b。
3. **MISALIGNED**：`SELF-GATE.md:162` 成果文件要求「含 A1-A8 结论汇总表」未含 A4b。
4. **MISALIGNED（轻）**：role file 人工验收清单 `136`「A1-A8 八项」应更新。
5. **可选 / NEEDS_HUMAN_REVIEW**：`P4-implementation.md`「常见错误」未提新禁令（权威源在 role file，非必需）。
6. **NEEDS_HUMAN_REVIEW**：`UPGRADING.md` 新节置于「版本管理生命周期」下，语义错位（见 A5）。

### 重点 5：A8 复现（逐条）

见 A8 节表。四条声称（`check-debt rc=0`、`roadmap 0 异常`、`0 ERROR`、`全量 2903 passed`）**全部复现**；两处措辞建议收紧（「全量 pytest 非全绿」「触脚本」），但不构成无据声称。

---

## 闭环建议（供主 Agent）

| 结论 | 项 | 动作 |
|------|----|------|
| MISALIGNED | A3a / A3b | 把 A4b 补入 role file 审查清单主表，并同步 SELF-GATE.md（派发模板 + 成果文件要求）+ role file 人工验收清单 |
| NEEDS_HUMAN_REVIEW | A5 | 确认「版本号公告约束」置于「版本管理生命周期」节是否可接受 |
| NEEDS_HUMAN_REVIEW | A7 | 记录两条修复采用 ADR-015 手段③的取舍理由；DEBT0051 closure_criteria 承认「自觉 + 评审」或补机械扫描 |
| 建议（非阻断） | A8 | 收紧 DEBT0051/0054 closure_note 的「全量 pytest」与「触脚本」措辞；implementer 新节补「既有测试」边界定义 + 出口改用 `[CLARIFY]` |

> 只读纪律遵守说明：本次审查未执行任何写仓/破坏性 git 操作；未改任何协议/脚本/测试；仅写入留痕文件与本草案成果文件。
