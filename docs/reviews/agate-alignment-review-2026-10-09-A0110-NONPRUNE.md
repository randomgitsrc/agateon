---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 处置 RM-AG0110（ADR-014 判据单源）——把「不可跳过/不可裁剪阶段集」从两脚本各自硬编码副本下沉为阶段注册表 `rules/phases.yaml` 顶层键 `non_prunable_phases`，两脚本共读 `agate_common.non_prunable_phases()`。
files_changed:
  - CHANGELOG.md
  - agate-workspace/roadmap/roadmap.md
  - agate/rules/phases.yaml
  - agate/rules/schema/phases.schema.json
  - agate/scripts/agate_common.py
  - agate/scripts/check-pruning.py
  - agate/scripts/check-state-transition.py
  - agate/state-machine.md
  - agate/tests/unit/test_non_prunable_phases_guard.py
branch: hotfix/batch-a-nonprunable-contract
commit_state: 未提交（工作区）
---

# 协议-脚本对齐审查（RM-AG0110 / batch-a-nonprunable-contract）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | NEEDS_HUMAN_REVIEW |
| A4 | 测试覆盖 | NEEDS_HUMAN_REVIEW |
| A4b | 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054） | ALIGNED（经实测无残留、无既有用例因本批转红） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | NEEDS_HUMAN_REVIEW |
| A8 | 声称-命令绑定 | ALIGNED（5 条声称全部可复现；含 1 条环境性失败说明） |

**可 commit 结论：❌ 暂不可 commit。** 需先修 A1/A2 的 MISALIGNED（两脚本注释仍写「契约快照 `rules/task-data/level-N.yaml`」，与实现读 `rules/phases.yaml` 不符——是已回退的 level-2 路线残留），并按 A3/A4/A7 的 NEEDS_HUMAN_REVIEW 交人工裁决（或补回退集等价守护）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**文档声明**（`agate/state-machine.md:227-230`）：
> **该集的单一权威源 = 阶段注册表 `rules/phases.yaml` 的顶层键 `non_prunable_phases`**（RM-AG0110 / ADR-014）：`check-pruning.py`（不可裁剪声明）与 `check-state-transition.py`（前向跨阶）**共读** `agate_common.non_prunable_phases()`，不再各自硬编码副本……

`agate/CHANGELOG.md:99-104` 同口径：
> 现下沉为**阶段注册表键**：`rules/phases.yaml` 新增顶层 `non_prunable_phases`……两脚本**共读** `agate_common.non_prunable_phases()`。

`agate_common.py:849` docstring 亦同口径：
> 从**阶段注册表** `rules/phases.yaml` 的顶层键 `non_prunable_phases` 读取

**脚本实现（正确面）**：`agate_common.non_prunable_phases()`（`agate/scripts/agate_common.py:846-864`）确从注册表读：
```python
data = read_rules_yaml(resolve_rules_root(script_path or __file__), "phases")
got = data.get("non_prunable_phases") if isinstance(data, dict) else None
```
两脚本调用点均传 `script_path=__file__`：
- `agate/scripts/check-pruning.py:164`：`agate_common.non_prunable_phases(task_dir, script_path=__file__)`
- `agate/scripts/check-state-transition.py:57`：`non_prunable_phases(task_dir, script_path=__file__)`

**差异（MISALIGNED）**：两脚本**自身注释**仍描述已废弃的路线——「从**契约快照**（`rules/task-data/level-N.yaml`）读取」：
- `agate/scripts/check-pruning.py:22-24`：
  > 改由 `agate_common.non_prunable_phases()` 从**契约快照**（`rules/task-data/level-N.yaml` 的 `non_prunable_phases`）读取；契约不可用时回退内置默认集（同值）。
- `agate/scripts/check-pruning.py:160-161`（`_non_prunable_set` docstring）：「读**契约单源**……回退内置默认集（**与快照同值**）」。
- `agate/scripts/check-state-transition.py:47-48`：「从**契约快照**读取」。

这与 `agate_common.py:849` / `state-machine.md:227` / `CHANGELOG.md:101` 三方口径**直接矛盾**（后三者均说「阶段注册表 `rules/phases.yaml`」）。`level-N.yaml` 是**任务级契约快照**（`agate/rules/task-data/`），而本集是**协议级不变量**，二者不是同一物。

**建议**：把上述三处注释/docstring 的「契约快照（`rules/task-data/level-N.yaml`）」改为「阶段注册表 `rules/phases.yaml` 顶层键 `non_prunable_phases`」，与 `agate_common` docstring / `state-machine.md` / `CHANGELOG` 统一。另 `agate_common.non_prunable_phases` 的形参 `task_dir`/`level`（`agate_common.py:846`）以「向后兼容保留」为由（`:853`）——但该函数是**新增**，无旧签名可兼容，此措辞亦是废弃路线残留，建议改为「仅为签名稳定性保留」。

---

### A2: 脚本→文档对齐 — MISALIGNED

同 A1：脚本内的注释（一种随代码走的「文档」）描述的机制（读 `level-N.yaml` 契约快照）与其**实际实现**（读 `rules/phases.yaml`）不符，属脚本→文档方向的偏离。修复方向同 A1。

（正面：`state-machine.md:225` 的散文枚举与 `:227-230` 的权威源指针一致；`agate/rules/state-transitions.md:94`、`agate/UPGRADING.md:294`、`WORKFLOW.md:245/255` 的散文复述与集内容一致，未发现语义冲突。）

---

### A3: 一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW

**A3a 连锁（已知衍生，均在 diff 中）**：`phases.yaml`（数据源）→ `phases.schema.json`（根 `additionalProperties:false`，故必须同步 `properties`，已做，`:97-101`）→ `agate_common.non_prunable_phases()` → 两脚本调用点 → 守护测试 → `state-machine.md` 指针 → `CHANGELOG` / `roadmap`。链条完整。

**A3b 反向传播（主动推断的应被影响文件，逐一验证）**：

| 文件 | 是否受新键影响 | 验证 |
|------|--------------|------|
| `agate/scripts/agate-advance.py` | 读 `phases.yaml`（`next`/`retreat`） | 实跑 rc=0（`/tmp` 副本）；新顶层键不影响 |
| `agate/scripts/agate-inject-card.py` | 读 `phases.yaml` 渲染卡片 | 实跑 rc=0（`/tmp` 副本）；不影响 |
| `agate/scripts/agate-md-field-set.py` | 读 `phases[].task_fields` | 新键在顶层、非 `phases[]` 内；`check-structure-consistency.py` S-4 实跑 OK |
| `check-structure-consistency.py` S-1/S-2 | YAML↔WORKFLOW 双向 | 实跑 rc=0，S1/S2 OK（新顶层键不进 `phases[]` 解析面） |
| `check-yaml-schema.py` S-5 | schema 校验 | 实跑 rc=0，SCHEMA-phases OK |
| `agate/rules/README` | — | **该文件不存在**（`agate/rules/` 下无 README）；无可同步项 |
| `agate/scripts/README.md:77-78` | 脚本清单表 | 描述 CLI 契约（未变）；未提及集来源，可不改 |
| `agate/WORKFLOW.md` / `phase-cards/*` / `agate/rules/state-transitions.md` | 散文复述同一集 | 见下 |
| `agate/UPGRADING.md:294` | v0.80.2 历史发布说明 | frozen 快照，不应回改（ADR-014②允许复述） |

**NEEDS_HUMAN_REVIEW 点**：ADR-014 ②（`agate/adr.md:567`）规定「**文档（人读的说明）可以复述，但必须指向权威源**」。本批**只在 `state-machine.md` 一处**加了「单一权威源」指针；其余复述该集的文档**均未加指针**：
- `agate/rules/state-transitions.md:94`：「**不可跳过的阶段**（P1 需求基线 / P2 方案设计 / P4 实现 / P5 技术验证 / P6 验收）**一律不得跨过**」——无指针；
- `agate/WORKFLOW.md:245`「P2 不可裁剪」、`:255`「P6 不可裁剪」、`:266-277`「不可跳过的阶段」表——无指针；
- `agate/phase-cards/P1-requirements.md:4`、`P2-design.md:4`、`P5-verification.md:4`、`P6-acceptance.md:4`——无指针。

判据（机器）确已单源（见 A4 运行时验证）；但按 ADR-014 ②，这些复述文档「须指权威源」。**是否要求本批补齐指针属范围裁决**（RM-AG0110 验收锚写的是「该集在协议内**仅一处定义**」——若严格理解为「判据单源」则已满足，若理解为「含散文」则未满足），故标 NEEDS_HUMAN_REVIEW，请人工裁定范围。建议至少给 `state-transitions.md:94`（同属 `rules/` 数据面旁）补一行指针。

**语义重复面（重点 3）**：`non_prunable_phases` 与 `phases.yaml` 既有 `gate_layer` 的关系：
- `gate_layer.transitions.forward`（`phases.yaml:191-199`）是**全链** `P0→P1→…→P8`，**不表达「可跳过」** ⇒ 与 `non_prunable_phases` **不是**同一事实，无重复。
- `gate_layer.commit_types.docs-only: [P0, P1, P2, P7, P8]`（`phases.yaml:187`）**不含 P4/P5/P6**（三者恰是 `non_prunable_phases` 成员）——表面上与「不可裁剪」冲突。**但二者是不同轴**：`commit_types` 是**提交级**（某类 commit 经过哪些 gate，`phases.yaml:176-184` 注释），`non_prunable_phases` 是**任务级**（任务必须包含哪些阶段）。当前两处均**无消费方**（`grep` 全仓：`gate_layer`/`commit_types` 无脚本读取）⇒ 无运行期冲突。**建议**：在 `phases.yaml` 的 `non_prunable_phases` 注释里加一句「本键为**任务级**；与 `gate_layer.commit_types`（提交级）不同轴，勿混读」，避免后来者误判冲突。此项标 NEEDS_HUMAN_REVIEW。

---

### A4: 测试覆盖 — NEEDS_HUMAN_REVIEW

**实跑（AGATE_ROOT=`/home/kity/oclab/agateon/agate`）**：
- 守护测试单跑：`python3 -m pytest agate/tests/unit/test_non_prunable_phases_guard.py -v` → `1 passed`（0.06s）。
- 全量：`python3 -m pytest agate/tests/ --reruns 1 -n auto -q` → **`1 failed, 2907 passed, 2 skipped, 1 rerun`**（83s）。唯一失败 `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` 系**环境性**（opencode v2.0.23 子命令为 `debug agents`，测试调 `debug agent`），与本批无关（见 A8）。

**覆盖到的**（`test_non_prunable_phases_guard.py:25-59`）：① 注册表键存在且值 = `{P1,P2,P4,P5,P6}`；② 两脚本源码含 `non_prunable_phases(` 且不含 `NON_PRUNABLE_PHASES = `。

**运行时单源验证（本次审查新增，副本上做）**：在 `/tmp/opencode/np-scratch` 副本把注册表键改为含 `P3` 后，`agate_common.non_prunable_phases()` / `check-pruning._non_prunable_set()` / `check-state-transition._non_prunable_phases()` **三者均返回含 P3 的集** ⇒ **happy path 确为真单源**（非仅源码字符串层面）。回退路径（`/tmp/opencode/np-empty`，无 `phases.yaml`）两脚本均回退 `{P1,P2,P4,P5,P6}`。

**NEEDS_HUMAN_REVIEW 点（重点 4——回退副本无守护）**：默认集实际有 **3 份硬编码副本**：
1. `agate/scripts/agate_common.py:856`：`_default = ("P1", "P2", "P4", "P5", "P6")`
2. `agate/scripts/check-pruning.py:167`：`return ("P1", "P2", "P4", "P5", "P6")`
3. `agate/scripts/check-state-transition.py:50`：`_NON_PRUNABLE_DEFAULT = frozenset({"P1", "P2", "P4", "P5", "P6"})`

守护测试**只断言源码字符串**（`"non_prunable_phases(" in src` 与 `"NON_PRUNABLE_PHASES = " not in src`），**不校验这 3 份回退默认值与注册表一致**。ADR-014 后果（`agate/adr.md:581`）明确要求「**权威源必须与既有实现逐条对账，并加等价回归守护**」、且「**消费方不得自带副本**」。⇒ 若注册表改为（例如）加 `P3` 且同步更新测试期望值，3 份回退副本会**静默漂移**（`check-state-transition.py` 的 `_NON_PRUNABLE_DEFAULT` 名称与断言串 `NON_PRUNABLE_PHASES = ` 不同，**不会被现守护捕获**）。测试 docstring「不再各自硬编码副本」的声称与实际（回退副本仍在）**不完全相符**。

**建议**（人工择一）：① 加守护断言两脚本回退默认集 == 注册表集；或 ② 删去两脚本各自的回退，统一由 `agate_common.non_prunable_phases()` 内部 `_default` 兜底（消除消费方副本）。另**潜在 KeyError**：`check-pruning.py:265-266` 遍历 `_non_prunable_set()` 后索引 `_NON_PRUNABLE_REASONS[_p]`——若注册表新增一个不在 reasons 表的阶段，将 `KeyError` 崩溃（reasons 表是又一处与集耦合的副本）。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED

**本批使既有用例转红 / 需更新的夹具**：**经实测无既有用例因本批转红**（全量 `2907 passed`；唯一 failed 为环境性 opencode 用例，见 A8，非本批所致）。无需更新的夹具。

**回退路线残留核查（重点 5）**——「登记新一级快照 `level-2.yaml`」路线已完整回退，逐项证据：
- `level-2.yaml` **不存在**：`find . -name 'level-2.yaml'`（排除 `.git`）无命中。
- `LEVELS.yaml` **已还原**：`agate/rules/task-data/LEVELS.yaml` 仅登记 `level: 1`（`:7-9`），且 `git diff` 为空（未改动）。
- `test_tag0050_write_tools.py` **夹具补丁已撤**：该文件 `git status` 干净（未出现在本批 9 个改动文件中）；`grep` 无 `level-2` 命中。
- 其余 `level-2` 字样均为**无关历史**：`agate/tests/integration/test_tag0050_a0_a1_ledger.py:432`（既有用例在 `tmp_path` 里造 level-2，测「存量 level-1 放行」机制）、`docs/reviews/*`（历史评审留痕）、`CHANGELOG.md:105-107`（本批**有意**留下的取舍说明）、`level-1.yaml:7`（设计说明里提到将来会新增 level-2）。
- 另：`git stash@{0}`（`feat/gate-robustness-single-source`）与 `.worktrees/blog-post11/` 的 `LEVELS.yaml` 均属**别处**，与本批无关（未触碰）。

**判断（走 `phases.yaml` 是否比走新一级快照更合适）**：**是，更合适**。理由：① 该集是**协议级不变量**——对**所有**任务成立、与单个任务的契约等级无关，而 `rules/task-data/level-N.yaml` 是**任务级**契约快照（`agate_common.py:852` 已明确此判断）；② 按设计 §2.3 规则 2，新任务须登记**当前等级**，登记新一级会把**全部**在途/测试夹具强制升到新级（实测 35 用例转红），与「纯新增、不追溯」的意图相悖；③ `phases.yaml` 本就是阶段权威源、非冻结，改一处即可。故改挂阶段注册表是正确取舍，`CHANGELOG.md:105-107` 的留痕亦恰当。

---

### A5: 下游影响 + 文档传播 — ALIGNED

- **破坏性变更**：无。改动为**纯新增**（`phases.yaml` 顶层键 + schema `properties` 增项 + 新函数 + 两脚本改读）。旧版本工具忽略未知顶层键；schema `additionalProperties:false` 只需本仓同步（已同步）。回退默认集保证「注册表不可用」时不改变既有行为。
- **CHANGELOG**：已加 `## [Unreleased]` → `### 修复` 条目（`CHANGELOG.md:99-107`），含 RM/ADR 引用与取舍留痕。✓
- **UPGRADING**：无需新增章节（无破坏性变更；且本批为未提交 hotfix，非发布）。
- **文档传播**：`state-machine.md` 已加指针；其余复述文档的指针问题见 A3（NEEDS_HUMAN_REVIEW）。`agate/scripts/README.md` 的脚本清单表未提及集来源——CLI 契约未变，可不改。

---

### A6: 锚点表覆盖 — ALIGNED

`check-protocol-consistency.py` CHECK 9 实跑 **PASS**。相关锚点仍在且被正确挂载：
- `check-protocol-consistency.py:579-581`：`desc="P2 不可裁剪…"` / `script="agate/scripts/check-pruning.py"` / `keywords=["P2 不可裁剪"]`——`_NON_PRUNABLE_REASONS`（`check-pruning.py:27-37`）保留了「P2 不可裁剪」「P6 不可裁剪」文案，锚点命中。
- `:618-622`：前向跨阶锚点（`keywords=["前向跨阶"]`）——`check-state-transition.py:503` 注释保留「前向跨阶」，命中。

本批新增的是**集的数据源位置**（注册表键），非新 CHECK/新脚本，锚点表无需增项；该单源属性由 `test_non_prunable_phases_guard.py` 守护（见 A4）。

---

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

相关 ADR：**ADR-014（判据单一权威源，`agate/adr.md:533-585`）**。
- 与 ①（判据单源）：**基本 ALIGNED**——happy path 已真单源（A4 运行时验证）。
- 与后果条「**消费方不得自带副本**」及「**权威源必须与既有实现逐条对账，并加等价回归守护**」（`adr.md:580-581`）：**存在张力**——两脚本仍各自保留硬编码**回退默认集**（消费方副本），且**无等价守护**（见 A4）。这是 ADR-014 明确点名的「声明单源 ≠ 已经单源」风险模式。
- 与 ②（文档复述须指权威源）：**部分满足**——仅 `state-machine.md` 加了指针（见 A3）。

设计原则是指导性的（A7 无 MISALIGNED），故标 **NEEDS_HUMAN_REVIEW**：请人工裁决「回退副本是否可接受 / 是否需补等价守护」，以及「复述文档是否须本批补指针」。

---

### A8: 声称-命令绑定 — ALIGNED

逐条复现（均须 `export AGATE_ROOT=/home/kity/oclab/agateon/agate`；**注意**：本机未设 env 时 `resolve_rules_root`/`_resolve_root` 会解析到 `~/.agate/current → v0.80.2` 稳定版——**稳定版 `phases.yaml` 无 `non_prunable_phases` 键**，故不设 env 的实跑会检错对象）：

| 声称 | 命令 | 结论 |
|------|------|------|
| `0 ERROR`（consistency） | `python3 agate/scripts/check-protocol-consistency.py`（+ `--strict-errors-only`） | **复现**：`仅有 429 个 WARNING，无 ERROR`；`--strict-errors-only` rc=0 ✓ |
| `2907 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **复现**：`1 failed, 2907 passed, 2 skipped, 1 rerun`。⚠️ 该 1 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，因本机 opencode v2.0.23 用 `debug agents`（测试调 `debug agent`）⇒ **环境性、与本批无关**（该测试文件未被本批改动） |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **复现**：rc=0 ✓ |
| roadmap 0 异常 | `python3 -c "…统计 split('\|') 列数≠9 的 \|RM- 行…"`（对齐 `check-gate.py:2138 _ROADMAP_EXPECTED_COLS=9`） | **复现**：`malformed rows = 0` ✓ |
| `ruff All checks passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（ruff 0.16.4，= CI 口径 `.github/workflows/protocol-tests.yml:254`） | **复现**：`All checks passed!` rc=0 ✓。⚠️ 注意 `ruff check .`（非 CI 口径）会报 36 个**非 `agate/` 目录**的历史错误，勿混淆 |

本批另在 `CHANGELOG.md:105-107` 声称「实测 35 个用例转红」——属**已回退路线**的历史取舍说明，无法在现工作区复现（路线已撤）；作为取舍留痕可接受，非活跃判据。

---

## 六项重点结论

1. **判据是否真单源**：**happy path 是**（运行时验证：改注册表键 → 两脚本 helper 同步变）；两处调用**都传了 `script_path=__file__`**（`check-pruning.py:164`、`check-state-transition.py:57`，关键，避免本机读到稳定版）。**但** ① 两脚本**注释**仍写「契约快照 `level-N.yaml`」（与实现矛盾，MISALIGNED）；② 回退默认集有 **3 份副本**且无守护（见重点 4）。
2. **新键是否破坏既有 gate**：**否**。`check-structure-consistency.py` S-1~S-6 rc=0、`check-yaml-schema.py` S-5 rc=0、`agate-advance.py`/`agate-inject-card.py` 在副本上 rc=0、`check-pruning.py` rc=0。新键在顶层、不进 `phases[]` 解析面。
3. **语义重复面**：`non_prunable_phases` 与 `gate_layer.transitions`（全链）**不重复**；与 `gate_layer.commit_types.docs-only`（不含 P4/P5/P6）**表面冲突但实为不同轴**（提交级 vs 任务级），且两者当前**无消费方**。建议在 `phases.yaml` 注释注明分工（NEEDS_HUMAN_REVIEW）。
4. **回退默认集风险**：**真实存在**。3 份副本（`agate_common.py:856` / `check-pruning.py:167` / `check-state-transition.py:50`）与注册表可能静默漂移；**无测试守护三者一致**（现守护只断源码字符串，且 `_NON_PRUNABLE_DEFAULT` 名称不被 `"NON_PRUNABLE_PHASES = "` 断言覆盖）。违反 ADR-014「消费方不得自带副本 + 须等价守护」。另有 `_NON_PRUNABLE_REASONS` KeyError 潜在风险。
5. **A4b 残留**：**确无残留**（`level-2.yaml` 不存在、`LEVELS.yaml` 仅 level 1 且干净、`test_tag0050_write_tools.py` 干净）。**走 `phases.yaml` 更合适**（协议级不变量 vs 任务级快照；新一级会强制全部夹具升 level = 35 用例转红）。
6. **A8 逐条复现**：5 条声称**全部可复现**（0 ERROR / 2907 passed / check-debt rc=0 / roadmap 0 异常 / ruff All checks passed），唯一 failed 为环境性 opencode 用例。

---

## 审查过程说明（只读纪律）

- 本审查**只读代码、只写本报告与留痕文件**，未改任何协议/脚本/测试，未 commit/push。
- ⚠️ **事故如实上报**：审查中误对真实任务运行写工具 `agate-inject-card.py P4 agate-workspace/tasks/TAG0050-task-data-contract`，弄脏 **47 个** `P4-dispatch-context-*.md`；**已用 `git checkout -- 'agate-workspace/tasks/TAG0050-task-data-contract/P4-dispatch-context-*.md'` 精确还原**该 47 文件，复核 `git status` 恢复为原 9 个改动文件（未触碰被评审改动集）。此后所有写工具（inject-card/advance）改在 `/tmp/opencode` 副本上跑。
- 跑测试/脚本前后 `git status` 一致（除本报告的 2 个产出文件）。
