---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: RM-AG0110 复核轮 r2——核实 r1 的 1 项 MISALIGNED（A1/A2 注释残留）与 2 项 NEEDS_HUMAN_REVIEW（A4 回退副本无守护、A7 ADR-014 等价守护）的改正；核心目标（不可裁剪集判据单源）已闭环。
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
round: r2
r1_report: docs/reviews/agate-alignment-review-2026-10-09-A0110-NONPRUNE.md
---

# 协议-脚本对齐审查（r2，RM-AG0110 / batch-a-nonprunable-contract）

## 审查结论汇总

| # | 审查项 | 结论 | 与 r1 对比 |
|---|--------|------|-----------|
| A1 | 文档→脚本对齐 | **ALIGNED** | r1 MISALIGNED → 已修 |
| A2 | 脚本→文档对齐 | **ALIGNED** | r1 MISALIGNED → 已修 |
| A3 | 一致性连锁 + 反向传播 | NEEDS_HUMAN_REVIEW | 未变（复述文档指针面未处置） |
| A4 | 测试覆盖 | **ALIGNED** | r1 NEEDS_HUMAN_REVIEW → 已修 |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED | 未变 |
| A5 | 下游影响 + 文档传播 | ALIGNED | 未变 |
| A6 | 锚点表覆盖 | ALIGNED | 未变 |
| A7 | 设计原则一致性 | **ALIGNED** | r1 NEEDS_HUMAN_REVIEW → 已修 |
| A8 | 声称-命令绑定 | ALIGNED | 未变（全部复现） |

**可 commit 结论：** r1 的**唯一阻塞项 MISALIGNED（A1/A2）已消除**，A4/A7 两项 NEEDS_HUMAN_REVIEW 已按改正落地并独立验证通过，**无新增 MISALIGNED**。仅余 **A3（复述文档是否须补权威源指针）** 一条 NEEDS_HUMAN_REVIEW——它是**范围裁决**（非功能缺陷）：
- 若人工确认「本批范围为**机器判据单源**」（与现有 `state-machine.md:227-230` 指针一致）⇒ A3 关闭，**可 commit**；
- 若要求按 ADR-014 ② 给复述文档补指针 ⇒ 建议**至少**给 `agate/rules/state-transitions.md:94` 补一行（同属 `rules/` 数据面旁），补后再 commit。

> 注：r1 报告列了 **3** 项 NEEDS_HUMAN_REVIEW（A3/A4/A7），本轮改动只覆盖了 **A4/A7 两项**；A3 未在改动集中（`state-machine.md` 的 diff 与 r1 一致，未新增指针），故仍开放。

---

## r1 发现逐条核实

### 发现 1（r1 MISALIGNED A1/A2）：两脚本注释仍写「契约快照 level-N.yaml」 → **已修（核实通过）**

| 位置 | r1 原文 | 现文（r2） |
|------|---------|-----------|
| `check-pruning.py:22-24` | 「从**契约快照**（`rules/task-data/level-N.yaml`）读取」 | 「从**阶段注册表** `rules/phases.yaml` 的顶层键 `non_prunable_phases` 读取；注册表不可用时回退 `agate_common.NON_PRUNABLE_PHASES_DEFAULT`」 |
| `check-pruning.py:159-162`（docstring） | 「读**契约单源**……回退内置默认集（**与快照同值**）」 | 「读**注册表单源**……回退默认值**只**在 `agate_common.NON_PRUNABLE_PHASES_DEFAULT` 定义，此处不再抄副本」 |
| `check-state-transition.py:53-57` | 「从**契约快照**读取」 | 「从**阶段注册表** `rules/phases.yaml` 的顶层键读取；不可用时回退 `agate_common.NON_PRUNABLE_PHASES_DEFAULT`（唯一定义处）」 |

**证据**：`grep -n "契约快照\|level-N" agate/scripts/check-pruning.py agate/scripts/check-state-transition.py` → **无命中**（残留已除）。三处现文与 `agate_common.py:849` / `state-machine.md:227` / `CHANGELOG.md:101` 口径统一（均「阶段注册表 `rules/phases.yaml`」）。

**残留措辞（cosmetic，不阻塞）**：调用点注释仍用「**契约单源**」字样——`check-pruning.py:262`、`check-state-transition.py:507`；`agate_common.py:861` 仍写形参「仅为**向后兼容**保留」（该函数为新增，无旧签名）。均**未误导机制**（同句已点名 `agate_common.non_prunable_phases()` / 注册表），属可选润色。**结论：A1/A2 ALIGNED。**

### 发现 2（r1 NEEDS_HUMAN_REVIEW A4/A7）：回退默认集 3 份副本 + 无守护 → **已修（核实通过）**

**改为唯一定义处**：`agate/scripts/agate_common.py:849`：
```python
NON_PRUNABLE_PHASES_DEFAULT = ("P1", "P2", "P4", "P5", "P6")
```
两脚本回退改为**引用**而非**抄写**：
- `check-pruning.py:159-167`：`_non_prunable_set()` 在 `agate_common` 不可用时返回 **`()`**（无字面量副本）；
- `check-state-transition.py:58-67`：`_non_prunable_phases()` 不可用时返回 `frozenset(NON_PRUNABLE_PHASES_DEFAULT)`；该常量在 `:27` 从 `agate_common` import（`:39` ImportError 时为 `None`，则最终回退 `frozenset()`）。

**守护测试新增断言**（`test_non_prunable_phases_guard.py:47-56`）：
```python
assert hasattr(common, "NON_PRUNABLE_PHASES_DEFAULT")
assert {str(x) for x in common.NON_PRUNABLE_PHASES_DEFAULT} == got      # 与注册表同值
for _n in (...): assert '"P1", "P2", "P4", "P5", "P6"' not in _src and "'P1', 'P2', 'P4', 'P5', 'P6'" not in _src
```
即：① 回退常量与注册表**同值**（`==got`，`got` 来自注册表）② 两脚本**不含字面量副本**。**结论：A4/A7 ALIGNED。**

### 发现 3（r1 附带建议）：`_NON_PRUNABLE_REASONS[_p]` KeyError → **已修（核实通过）**

`check-pruning.py:268` 改为 `errors.append(_NON_PRUNABLE_REASONS.get(_p, f"{_p} 不可裁剪"))`。
**实跑证据**（副本 `/tmp/opencode/np2`，注册表改为含 `P3`，任务 P1 的 `phases` 缺 `P3`）：
```
GATE PRUNING: 裁剪条件不满足：
  - P3 不可裁剪
  - 裁剪声明缺'跳过风险:'评估…
rc=1
```
无 `KeyError`/traceback（旧写法会崩）。**结论：隐患已消除。**

---

## 逐项审查

### A1 / A2：文档→脚本 / 脚本→文档 — ALIGNED

r1 的 MISALIGNED 已按上文「发现 1」修复。`agate_common.non_prunable_phases()`（`:852-870`）从注册表顶层键读、异常回退 `NON_PRUNABLE_PHASES_DEFAULT`；两脚本调用点仍均传 `script_path=__file__`（`check-pruning.py:165`、`check-state-transition.py:62`，**关键**，避免本机读到稳定版）。三方口径（`agate_common` docstring / `state-machine.md:227` / `CHANGELOG.md:101`）一致。

### A3：一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW（未变）

**A3a 连锁**：完整（注册表 → schema → helper → 两脚本 → 守护测试 → `state-machine.md` → CHANGELOG/roadmap）。

**A3b 反向传播**（本轮**新增补查**，回应「删除模块级常量是否破坏其它消费方」）：
- `check-routing.py:23` 以 importlib 加载 `check-pruning.py` 复用 `_md_field`/`_read_p1`，**无 `NON_PRUNABLE` 引用**（`grep` 无命中）；
- `agate-state-set.py:52` 加载 `check-state-transition.py` 的纯函数 `check_transition`，**无 `NON_PRUNABLE` 引用**；
- 全仓 `grep NON_PRUNABLE` 仅命中 `agate_common.py` + 两脚本 + 守护测试 ⇒ **删模块级 `NON_PRUNABLE_PHASES` 不破坏任何其它消费方**。

**仍开放点**：ADR-014 ②（`agate/adr.md:567`）「文档可复述**但必须指向权威源**」。本批仅在 `state-machine.md:227-230` 加了指针；`agate/rules/state-transitions.md:94`、`agate/WORKFLOW.md:245/255/266-277`、`agate/phase-cards/P1|P2|P5|P6-*.md` 的散文复述**仍无指针**（与 r1 相同，本批未处置）。属**范围裁决**（RM-AG0110 验收锚「该集在协议内仅一处定义」——机器判据已满足），故保留 NEEDS_HUMAN_REVIEW。**建议**：至少给 `state-transitions.md:94` 补一行指向 `rules/phases.yaml`。

### A4：测试覆盖 — ALIGNED

- 守护测试单跑：`python3 -m pytest agate/tests/unit/test_non_prunable_phases_guard.py -v` → **`1 passed`**。
- 全量：`python3 -m pytest agate/tests/ --reruns 1 -n auto -q` → **`1 failed, 2907 passed, 2 skipped, 1 rerun`**（82s）。唯一 failed 为**环境性** opencode 用例（见 A8），与本批无关。
- **运行时单源验证（副本 `/tmp/opencode/np2`，注册表加 P3）**：`agate_common.non_prunable_phases()` / `check-pruning._non_prunable_set()` / `check-state-transition._non_prunable_phases()` **三者均返回含 P3 的集** ⇒ 真单源（happy path）。
- **回退路径验证**：无注册表时（`/tmp/opencode/np2b`）三者均回退 `{P1,P2,P4,P5,P6}`；`agate_common=None` 时 `check-pruning` 返回 `()`；`check-state-transition` 两常量均 `None` 时返回 `frozenset()`。
- **回退副本守护**：已加（见「发现 2」）。

**minor 观察（不阻塞）**：守护的字面量断言 `'"P1", "P2", "P4", "P5", "P6"'` 用**带空格**写法；若将来有人写成 `{"P1","P2",...}`（逗号后无空格）可规避。属启发式守护的保守边界，可接受。

### A4b：闭合后既有测试转红 + 夹具更新清单 — ALIGNED

**经实测无既有用例因本批（r2 增量）转红**（全量 `2907 passed`，与 r1 相同；唯一 failed 为环境性）。无需更新的夹具。r1 已核的「level-2 路线无残留」（`level-2.yaml` 不存在、`LEVELS.yaml` 仅 level 1 且干净、`test_tag0050_write_tools.py` 干净）**本轮仍成立**（未新增改动）。

### A5：下游影响 + 文档传播 — ALIGNED

无破坏性变更（纯新增键 + 新常量 + 两脚本改读）；CHANGELOG 条目在 `[Unreleased]`（`CHANGELOG.md:99-107`）。r2 增量（`agate_common.py` 新增常量、两脚本回退改引用、测试加断言）**不改变 CLI 契约**，无需新文档传播。复述文档指针问题见 A3。

### A6：锚点表覆盖 — ALIGNED

`check-protocol-consistency.py` CHECK 9 实跑 **PASS**（`--strict-errors-only` rc=0）。锚点 `:579-581`（`keywords=["P2 不可裁剪"]`）仍命中 `check-pruning.py` 的 `_NON_PRUNABLE_REASONS`；`:618-622`（前向跨阶）仍命中 `check-state-transition.py`。本批为数据源位置变更，非新 CHECK，锚点表无需增项。

### A7：设计原则一致性 — ALIGNED

ADR-014（`agate/adr.md:533-585`）：
- ① 判据单源：**满足**（happy path 运行时验证真单源）。
- 后果条「消费方不得自带副本 + 须等价守护」（`:580-581`）：**满足**——回退集收为**唯一定义处** `NON_PRUNABLE_PHASES_DEFAULT`，且守护断言「常量 == 注册表值」「两脚本无字面量副本」。r1 指出的张力已消。
- ② 文档复述须指权威源：**部分满足**（仅 `state-machine.md`）——见 A3（范围裁决）。

### A8：声称-命令绑定 — ALIGNED

均须 `export AGATE_ROOT=/home/kity/oclab/agateon/agate`（本机未设 env 会解析到 `~/.agate/current → v0.80.2` 稳定版；稳定版 `phases.yaml` 无该键）：

| 声称 | 命令 | 结论 |
|------|------|------|
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **复现**：`仅有 429 个 WARNING，无 ERROR`，rc=0 ✓ |
| `2907 passed` | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **复现**：`1 failed, 2907 passed, 2 skipped, 1 rerun`。唯一 failed=`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（本机 opencode v2.0.23 用 `debug agents`，测试调 `debug agent`）⇒ **环境性、与本批无关** |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **复现**：rc=0 ✓ |
| roadmap 0 异常 | 统计 `split('\|')` 列数≠9 的 `\|RM-` 行（对齐 `check-gate.py:2138 _ROADMAP_EXPECTED_COLS=9`） | **复现**：`malformed rows = 0` ✓ |
| `ruff All checks passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（0.16.4，= CI 口径） | **复现**：`All checks passed!` rc=0 ✓ |
| （r2 增量）两脚本无字面量副本 | `grep -rn '"P1", "P2", "P4", "P5", "P6"' agate/scripts/` | **复现**：仅 `agate_common.py:849` 命中（唯一定义处）✓ |

---

## 本轮五项重点结论

1. **3 项改正是否真修**：**全部核实通过**——注释残留已除（`grep` 无 `level-N`）；回退集收为 `NON_PRUNABLE_PHASES_DEFAULT` 唯一定义 + 守护断言同值/无副本；KeyError 改 `.get` 并实跑（副本加 P3）不崩。
2. **回退路径可达性**：`pre-commit-gate.py:47-74` **模块级 import `agate_common`，失败即 `GATE ERROR` + `exit 1`（fail-closed）** ⇒ 经 gate 调用 `check-pruning.py` 时 `agate_common` 必可导入 ⇒ 其 `()` 分支**不可达**（与 `_phase_universe` 的降级口径一致）。`check-state-transition.py` 的 `NON_PRUNABLE_PHASES_DEFAULT` import 与 None 分支正确（实跑验证两分支）。
3. **单源闭环**：`grep` 全仓（`agate/` 的 `.py/.yaml/.json`）确认非裁剪集字面量只剩 **3 处语义位置**——注册表 `phases.yaml:27`、回退常量 `agate_common.py:849`、守护测试期望值（`test_non_prunable_phases_guard.py:26/40/55`）；其余命中均为**任务 `phases` 夹具**（不同概念，非副本）。另删模块级常量**不破坏** `check-routing.py`/`agate-state-set.py`（无 `NON_PRUNABLE` 引用）。
4. **全量 pytest**：`1 failed, 2907 passed, 2 skipped, 1 rerun`（唯一 failed 环境性）。
5. **是否可 commit**：**核心阻塞项已消除、无新增 MISALIGNED**；仅余 A3 一条范围裁决 NEEDS_HUMAN_REVIEW。人工确认 A3 范围后可 commit（若要求补指针，先补 `state-transitions.md:94` 一行）。

---

## 审查过程说明（只读纪律）

- 本审查**只读代码、只写本报告与留痕文件**，未改任何协议/脚本/测试，未 commit/push。
- 本轮所有**写类操作**（含运行时单源/回退/KeyError 验证）均在 `/tmp/opencode/np2`、`/tmp/opencode/np2b` 副本上跑；**未对真实任务运行 `agate-inject-card.py` 等写工具**（吸取 r1 教训）。
- 跑测试/脚本前后 `git status` 一致（仅 9 个已改文件 + 本报告的留痕/成果文件）。
