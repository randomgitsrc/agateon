---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B/H3——关单 DEBT0015 / RM-AG0083（env_constraints 声明性字段无执行/gate 绑定），小幅强化 P4 卡「自查≠gate」的构建产物 checklist 落点
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/phase-cards/P4-implementation.md]
---

# 协议-脚本对齐审查

> 触发面：`agate/phase-cards/P4-implementation.md`（`agate/**/*.md`）→ 触发 SELF-GATE。
> 分支 `hotfix/batch-b-env-constraints`（**未提交**，改动在工作区；审查期间未做任何写仓/破坏性 git 操作）。
> 留痕：`docs/reviews/agate-alignment-2026-10-09-H3-ENV-01.progress.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（含 1 条可选同步建议） |
| A4 | 测试覆盖 | ALIGNED（含 1 条**与本批无关**的环境性失败） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED（含 ADR-002 张力备注） |
| A8 | 声称-命令绑定 | **NEEDS_HUMAN_REVIEW**（判据 (3) 关单 + 1 处失准行号） |

**总体**：本批为**文档面澄清 + 关单登记**，不改变任何脚本逻辑与 gate 行为，主体成立。
唯一实质争议在 **closure_criteria (3) 的关单方式**（范围重定义 vs 登记滞后），见 A8 与「重点结论 1」。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/phase-cards/P4-implementation.md:58`，本批新增）：
> 协议**无**对应机械 gate（产物路径项目各异）⇒ 该条目即「无机械 gate 时的既定出口」

**脚本实现**：本批**未改任何脚本**。对上述「无机械 gate」声明做独立核实——
```
$ grep -c "env_constraints" agate/scripts/check-gate.py
0
$ grep -cnE "env_constraints|debug_env|deploy" agate/scripts/check-gate.py
0
```
`check-gate.py` 对 `env_constraints` 零引用（与 DEBT0015 evidence 一致）。新增句所依赖的事实成立。

**结论**：ALIGNED。新增句是纯文档表述，未引入「文档承诺脚本未实现」的缺口；其「无机械 gate」的自我声明经脚本核实为真。

---

### A2: 脚本→文档对齐

**脚本变更**：无（`git diff --stat`：4 文件全为 `.md`）。无需脚本→文档反向同步。

**结论**：ALIGNED。

---

### A3: 一致性连锁 + 反向传播

**A3a 连锁（已知衍生改动）**：
- `CHANGELOG.md:44-48`（[Unreleased]→修复）已记录本批，并明写「文档面澄清（`P2-design.md`「env_constraints 与 gate_commands 的边界」节早已给出语义边界）」——与 `P2-design.md:207-211` 一致。✓
- `agate-workspace/debt/tech-debt.md:611` status→closed、`:653-657` 关单元数据；`roadmap.md:84` status→done、关联任务→`hotfix-batchB-H3`。✓

**A3b 反向传播（主动推断「应被影响但未在 diff 中」的文件）**：

| 候选文件 | 是否需同步 | 判据 |
|----------|-----------|------|
| `agate/assets/execution-roles/architect.md:152-159` | **否**（已一致） | 已有同款边界提醒「`env_constraints` 是**声明性字段**…必须落到 `gate_commands` 或 P4/P8 阶段卡片的明确 checklist」。与本批口径一致，无需改 |
| `agate/assets/execution-roles/implementer.md:72-77` | **可选**（未改，可辩护） | 存在平行「## 自查≠gate」节，但**未**含 dist/构建产物条目。**非必须**：本批落点写在 P4 卡「派发 prompt 模板」的「自查≠gate」追加段（`P4-implementation.md:48-62`），该段在 P4 派发时**注入 implementer 的 prompt**，implementer 实际会看到；角色文件是任务形态无关的基线。属**可选同步**（若要双处一致可加一行），不判 MISALIGNED |
| `agate/assets/templates/task-files.md:338`（`## 6. env_constraints` 样例块） | 否 | 纯样例块，无「会执行」的错误承诺；边界权威源在 P2 卡 + architect，无需复制 |
| `agate/phase-cards/P0-orchestrator.md:111` | 否 | 只述「env_constraints…会注入」，与声明性语义一致 |
| `agate/WORKFLOW.md:303` | 否 | 仅指 `env_constraints.debug_env` 作测试隔离的约定读取点，不涉执行性承诺 |
| `agate/scripts/README.md` | 否 | 无 env_constraints 相关脚本，不在本批影响面 |
| `SELF-GATE.md` | 否（但流程义务） | 内容无需改；但 P4 卡触发 self-gate ⇒ commit message 须含 `self-gate-review:`（见 A5） |
| `agate/dispatch-protocol.md:227/237/311/348/379` | 否 | 均为字段清单/注入说明，无与边界冲突的语义 |

**结论**：ALIGNED。已知连锁项全部到位；反向传播未发现**必需**的漏改（`implementer.md` 为可选同步建议）。

---

### A4: 测试覆盖

**本批变更是否有对应 pytest 测试**：有——`agate/tests/unit/test_p2p4_boundary_docs.py`（TAG0017 批 fg1-doc-boundary 建立，非本批新增）：
- `test_bdd_6_p4_implementation_self_check_section_has_dist_build_reminder`（`:161-173`）——断言 `P4-implementation.md`「## 自查≠gate」节含 UI/需构建 + dist/构建产物 + 「确认…存在」式条目。本批新增行 `:58` **落在该节抽取范围内**（节 = 行 53–58），三条正则均命中，测试仍绿。✓
- `test_bdd_5_*`（`:71-107`）——覆盖 `P2-design.md`「gate_commands 声明」节 + `architect.md` 的边界说明。✓
- 本批为**纯文档澄清**，未新增行为/接口，故无新增用例之必要（既有 BDD-5/6 已锁住落点存在性）。

**最近一次 pytest 全量实跑输出（CI 口径）**：
```
$ python3 -m pytest agate/tests/ --reruns 1 -n auto -q
...
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
1 failed, 2898 passed, 2 skipped, 1 rerun in 86.67s (0:01:26)
```
**失败项归因（与本批无关）**：`test_bdd_43`（`test_setup_agate_dir.py:299-303`）实跑 `opencode debug agent orchestrator`，而本机 `opencode v2.0.23` 已把子命令更名为 `debug agents`（报 `Unknown subcommand "agent"`）。该测试与本批 4 个文件无任何交集，属**本机 CLI 版本漂移**（环境性），非本批引入。

**结论**：ALIGNED（1 条环境性失败已归因隔离）。

---

### A5: 下游影响 + 文档传播

**gate 行为影响**：无。本批不改 gate 脚本；`check-gate.py` P4 分支（`:164-173`）判定项不变（暂存区代码文件 / RM-AG0046 三重门槛 / 骨架 WARNING），构建产物确认**未**被接入任何 gate。

**破坏性变更**：无。纯文档澄清 + 数据面登记。

**CHANGELOG**：已标注（`CHANGELOG.md:44-48`，[Unreleased]→修复）。✓

**文档传播**：见 A3b——architect 已含边界；无其他需同步文档。

**流程义务**：`agate/phase-cards/P4-implementation.md` 命中 self-gate 触发面（`agate/.+/.*\.md`）⇒ commit message 须含 `self-gate-review:`（WARNING 不拦截，但为本角色存在的前提）。其余 3 文件不触发。

**结论**：ALIGNED。

---

### A6: 锚点表覆盖

本批**未新增协议规则、未新增/改名脚本**，故 CHECK 9 锚点表无需更新。`check-protocol-consistency.py` CHECK 9 全 PASS（见 A8 命令）。`test_p2p4_boundary_docs.py` 是既有 BDD 文档断言测试，非脚本锚点，不属 CHECK 9 覆盖面。

**结论**：ALIGNED。

---

### A7: 设计原则一致性

逐条对照相关 ADR：
- **ADR-002（可判定性——gate 门槛机器可判定）**：本批新增句**明示**「协议无对应机械 gate…主 Agent 在 P4 gate 前逐项确认」。P4 gate 本身仍由脚本 exit code 决定（不变），构建产物确认是**补充 checklist 引导**而非 gate，故未把 gate 变成「主 Agent 自报」。
  **张力备注（指导性，不阻断）**：ADR-002 后果节称「有些质量维度不可脚本化…只能用 exit 2 标记需人工判断」，而本条目既非机械 gate 也非 exit-2，属**软 checklist**。但该形态是 `P2-design.md:211`（TAG0017 既有）已确立的合法回退（「P4/P8 阶段卡片里的明确 checklist 条目（有人工自查动作可执行）」），本批沿用既有模式，非新立先例。
- **ADR-005（声明性/行为逻辑/机制交叉）**：本批为声明性改动，与分类自洽。

未发现与 ADR 冲突、也未发现需补记的新架构决策。

**结论**：ALIGNED（含上述 ADR-002 张力备注）。

---

### A8: 声称-命令绑定

逐条列 `声称 → 命令 → 结论`：

| # | 声称（出处） | 命令 | 结论 |
|---|--------------|------|------|
| 1 | `check-debt.py` rc=0（debt evidence `:642-643` 隐含） | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **成立**（rc=0）。closed 准入启发式（task_id + `P[56]` 子串，`agate-debt-check.py:157-163`）由本批 evidence 内的「批次 hotfix-batchB-H3」+「P5/P6 等价验证」满足 |
| 2 | consistency 0 ERROR（debt `:641` / roadmap 备注） | `python3 agate/scripts/check-protocol-consistency.py` | **成立**（419 WARNING / 0 ERROR，rc=0） |
| 3 | roadmap 0 异常（列数） | 复刻 `_check_roadmap_done` 判据扫描（`_ROADMAP_EXPECTED_COLS=9`，`check-gate.py:2138`）：`python3 - <<'EOF' … split('|') … EOF` | **成立**：0 条 RM- 行列表数异常；RM-AG0083 行 9 列，status=`done`、关联=`hotfix-batchB-H3` |
| 4 | (1)「env_constraints 语义边界文档化」已满足（debt `:634-636`） | `sed -n '207,211p' agate/phase-cards/P2-design.md`；`sed -n '159p' agate/assets/execution-roles/architect.md` | **成立**：`P2-design.md:207`「### env_constraints 与 gate_commands 的边界（不等价）」节 + `:211`「必须落到 gate_commands…或者落到 P4/P8 阶段卡片里的明确 checklist 条目」；`architect.md:159` 同款 |
| 5 | (2)「UI 任务 P4 后 dist 构建有明确落点」已满足（debt `:637-639`） | `sed -n '57,58p' agate/phase-cards/P4-implementation.md` | **成立**：`:57`（既有）+ `:58`（本批强化）均在「## 自查≠gate」节 |
| 6 | 全量 pytest（debt `:641`「全量 pytest + consistency 0 ERROR（P5/P6 等价验证）」） | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **基本成立**：2898 passed / 1 failed（环境性，见 A4）；⚠️ 该声称**省略了 closure_criteria ④ 的 shellcheck 项**——本批未改 `.sh`，shellcheck 0 issue 属**真空满足**，但 evidence 文字未提，属表述不完整（非错误） |
| 7 | (3)「TQC0001 类 UI 任务自动产出 dist」属**项目侧**行为（debt `:640` / roadmap 备注） | 无命令可绑定（无真实 UI 任务实证） | **NEEDS_HUMAN_REVIEW**：该结论是对判据的**范围重定义**，非「登记滞后」。原 evidence（`:627-630`）明写 (3) 是「面向未来的行为性指标，需要下一个实际的 UI 任务走完 P4 阶段后才能实证」——本批未提供该实证 |
| 8 | roadmap 行内「语义边界已文档化于 `P2-design.md:193`」（`roadmap.md:84`，本批保留的既有文本） | `sed -n '193p' agate/phase-cards/P2-design.md` | **不成立**：`:193` 是「`{key}_timeout_seconds` 字段规则」的 P3 排除条，**非**边界节。边界节现为 `:207`（TAG0017 落地时在 `:148`）。该行号**自始即失准**（非本批引入），但本批改写了同一行，宜顺手修正 |

**A8 结论**：NEEDS_HUMAN_REVIEW（第 7 条判据 (3) 关单方式；第 8 条失准行号）。

---

## 重点结论（任务点名 4 项）

### 1. 关单判定是否成立

- **(1) 成立**：`P2-design.md:207-211` 明写声明性 vs 执行性边界；`architect.md:159` 同款。逐字见 A8#4。
- **(2) 成立**：`P4-implementation.md:57`（既有）+ `:58`（本批强化）。逐字见 A8#5。
- **(3) 关单方式存疑 → NEEDS_HUMAN_REVIEW**：判据 (3) 原文是「TQC0001 类 UI 任务在 P4 后**自动**产出 dist（不靠用户提醒）」。本批把它改判为「**项目侧**行为」并据此关单。但：
  - 原 evidence（debt `:627-630`）明确把 (3) 定义为**需实证的行为性指标**（「需要下一个实际的 UI 任务走完 P4 阶段后才能实证确认」），本批**未提供**该实证；
  - 因此这是**范围重定义（re-scope）**，不是「登记滞后」。`closure_note`（debt `:655-657`）称「属「登记滞后」而非缺陷仍在（同类先例：DEBT0029 / RM-AG0085）」——但 DEBT0029 的修复**确已落地**（标题级正则），与 (3) **未落地/未实证** 不同，**先例类比不当**；
  - **两读法均成立**，属设计取舍：读法 A（本批）——协议层无代码执行能力，(3) 描述的最终行为只能由项目侧保证，协议侧等价物即 (2) 的卡片条目，且 recommendation(3) 本就标「可选」；读法 B（原作者）——(3) 是待实证指标，未验证前不应关单。
  - **未满足项是否被绕过**：(1)(2) 非绕过（真满足）；(3) 是**以重定义代替满足**——这正是需人工裁决处，故 NEEDS_HUMAN_REVIEW，**不判 MISALIGNED**（真模糊/设计取舍）。

### 2. P4 卡新增表述是否重复/矛盾、是否可被误读为「有机械 gate」

- **与 `P2-design.md:207-211` 一致，无矛盾**：P2 `:211` 要求强制约束「落到 `gate_commands` 或 P4/P8 明确 checklist 条目」；P4 新增句正是这样一个「明确 checklist 条目」，且自陈「无机械 gate ⇒ 既定出口」。二者**互补**，非重复。
- **不会被误读为「有机械 gate」**：新增句逐字写「协议**无**对应机械 gate（产物路径项目各异）」——恰好相反，是**主动澄清无 gate**。
- **轻微可读性观察（不阻断）**：① 该句位于「派发 prompt 模板」的追加段内（`:48-62`，会被注入 implementer 的 prompt），却把动作人写成「**主 Agent** 在 P4 gate 前逐项确认」——阅读对象（implementer）与动作人（主 Agent）错位，建议措辞上明示「implementer 产出并自证、主 Agent 复核」。② 「推进条件（全部满足才写 phase: P5）」（`:175-180`）**未**把该确认列入——与「无机械 gate、软 checklist」定位自洽，但若期望它可被核对，宜在推进条件加一条目。

### 3. 反向传播

- `architect.md`：**已同步**（`:159`），无需改（DEBT recommendation 点名处已满足）。
- `implementer.md`：有平行「## 自查≠gate」节（`:72-77`）**未**含 dist——判为**可选同步**，非必需（P4 卡的该段会在派发时注入 implementer prompt；角色基线任务形态无关）。见 A3b。
- `task-files.md` / `P0-orchestrator.md` / `WORKFLOW.md` / `scripts/README.md`：均**不受影响**（无执行性承诺、无相关脚本）。
- `P2-design.md` 边界节与 P4 新表述**口径一致**（见重点结论 2）。

### 4. A8 声称复现

见 A8 表——7 条声称中 6 条可复现/基本成立（第 6 条 shellcheck 表述不完整、第 8 条行号失准），第 7 条判据 (3) 无命令可绑定。

---

## 需人工确认项

- **A8 / 重点结论 1**：closure_criteria (3)「TQC0001 类 UI 任务自动产出 dist（不靠提醒）」以「项目侧行为」重定义关单——请确认是否接受该重定义（接受则关闭成立；不接受则应保留 (3) 或转跟进项）。**同时**请确认是否顺带修正 `roadmap.md:84` 的失准行号 `P2-design.md:193` → 边界节（现 `:207`，或用节名）。
- **配对标记（未确认前等同 MISALIGNED，不允许 commit）**：
  `[HUMAN_CONFIRMED: 待确认]`（主 Agent/人工确认后补日期与理由）

## 修复建议（供主 Agent 派 implementer；本角色不改代码）

1. （若接受 (3) 重定义）把 `debt/tech-debt.md:655-657` 的「登记滞后」措辞改为「**范围重定义**」——(1)(2) 为既有满足，(3) 为项目侧行为；(3) 的先例类比（DEBT0029）删去或更正。
2. `roadmap.md:84`：`P2-design.md:193` → 改为节名引用（避免行号随插入漂移）或 `:207`。
3. （可选）`implementer.md:72`「自查≠gate」节补一行指向 P4 卡的构建产物 checklist，消除双处不一致。
4. （可选）debt evidence `:641` 的 (4) 补「shellcheck 0 issue（本批未改 .sh，真空满足）」以对齐 closure_criteria ④ 全项。
