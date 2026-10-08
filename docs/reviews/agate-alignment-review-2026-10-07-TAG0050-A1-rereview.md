---
review_date: 2026-10-07
reviewer: protocol-alignment-review
change_summary: TAG0050 批 A1 SELF-GATE 复评——复核原审查 A1/A2/A3/A4/A8（MISALIGNED）是否按 F1–F7 闭合，并扫描是否引入新问题
files_changed:
  - agate/scripts/agate-next.py
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/agate_common.py
  - agate/scripts/check-events.py
  - agate/scripts/check-state-transition.py
  - agate/scripts/check-gate.py
  - agate/WORKFLOW.md
  - SELF-GATE.md
  - agate/state-machine.md
  - agate/tests/integration/test_tag0050_a0_a1_ledger.py
  - agate/tests/integration/test_pre_commit_hook.py
  - agate/tests/conftest.py
  - docs/design-notes/design-tag0050-task-data-contract.md
---

# 协议-脚本对齐审查（TAG0050 批 A1 · SELF-GATE Layer 1 · **复评**）

> 本报告**只复核**原审查 `docs/reviews/agate-alignment-review-2026-10-07-TAG0050-A1.md` 判出的
> MISALIGNED（A1/A2/A3/A4/A8）是否按 `P4-dispatch-context-implementer-A1-fix.md` 的 **F1–F7**
> 整改闭合，并扫描整改是否引入新问题。不重开全量审查。
> HEAD = `1d5aab2`（分支 `feat/TAG0050-task-data-contract`），A1 改动**未提交**（工作区）。

## 复核结论汇总

| 整改项 | 对应原 MISALIGNED | 结论 |
|---|---|---|
| F1 `agate-next.py:_p6_judge_advance` 依契约 | A1-1 | **ALIGNED** |
| F2 pre-commit 规则 7 后半（按被暂存产出所属阶段重跑 gate） | A1-2 | **ALIGNED** |
| F3 `check_ledger_events` 不再追溯存量任务 | A1-3 | **ALIGNED** |
| F4 `WORKFLOW.md` 收录新步骤 | A2-1 | **ALIGNED** |
| F5 `SELF-GATE.md` CHECK 范围 1-16 | A2-2 | **ALIGNED** |
| F6 `P4-implementation.md` 声称修正 | A8 | **ALIGNED**（附残余观察 R-1/R-2） |
| F7 测试缺口补齐 | A4 | **ALIGNED** |

**新增问题扫描**：未发现新 MISALIGNED；未发现平台假设 / 破坏 §8 兼容承诺 / 碰坏其它文件。
原 MISALIGNED 全部闭合。残留两项**非阻塞**观察（R-1 数字漂移、R-2 `scripts/README.md` 旧描述未改）见文末。

---

## 逐条复核（可复现证据）

### F1（原 A1-1）`agate-next.py:_p6_judge_advance` 依契约 — ALIGNED

**整改点**（`agate/scripts/agate-next.py`）：
```python
# 非 legacy 任务的 judge 由**契约**决定（requirement_active(task_dir, "judge", "P6")），
# 不读可被改写的 judge.enabled；legacy 任务（返回 None）回退旧逻辑。
judge_enabled = None
if requirement_active is not None:
    req = requirement_active(task_dir, "judge", "P6")
    if req is not None:
        judge_enabled = bool(req)
if judge_enabled is None:
    judge = state.get("judge")
    judge_enabled = bool(isinstance(judge, dict) and judge.get("enabled"))
```

**证据**：
```
$ git diff agate/scripts/agate-next.py        # 新增 requirement_active import + 上述分支
$ grep -n requirement_active agate/scripts/agate-next.py
54:        requirement_active,
279:    if requirement_active is not None:
280:        req = requirement_active(task_dir, "judge", "P6")

$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py::test_f1_p6_judge_advance_uses_contract -v
... test_f1_p6_judge_advance_uses_contract PASSED [100%]
```
新用例构造「非 legacy（level-1，`requires.judge: true`）+ `.state.yaml` 写 `judge.enabled: false`」，
断言走 P6.5 分支（不因开关直推 P7）→ 证明契约优先。**结论：ALIGNED**。

---

### F2（原 A1-2）pre-commit 规则 7 后半 — ALIGNED

**整改点**：`pre-commit-gate.py` 新增 `_rerun_gates_for_staged_outputs`（非 legacy 任务按
**被暂存产出所属阶段**重跑该阶段 gate；阶段须不晚于 HEAD phase；HEAD 为 READY/DONE 时同样执行），
并由 `_scan_prod_touched_and_rerun` 调用。

**证据（独立复现，仓外 `/tmp/opencode/f2scratch`，经真实 pre-commit hook）**：

非 legacy 任务、暂存 `P6-acceptance.md`（含 FAIL）、未改 phase（HEAD=P7）：
```
$ AGATE_ROOT=<repo>/agate git commit -m "stage P6 only"
GATE P6: FAIL=1, TOTAL=1
GATE: 非 legacy 任务暂存了 P6 产出但未改 phase（agate-workspace/tasks/T001-rerun）——按被暂存产出所属阶段重跑 P6 gate 未通过（设计 §2.3 规则 7）
rc=1
```
同一任务去掉 `gate-events.jsonl`（降为 legacy）后：
```
GATE WARNING: 暂存了 P6 产出但 phase=P7（T001-rerun）——请确认是否需要更新 phase
[master 962bdd7] legacy stage P6 only
rc=0
```
即：非 legacy → 重跑拦截；legacy → 仅 WARNING（不重跑），与设计 §2.3 规则 7 / §8 承诺一致。

**与既有用例的冲突处置（§8 例外已登记）**：
```
$ git diff docs/design-notes/design-tag0050-task-data-contract.md
-**现有测试**：... 只有以下两类允许改动用例：
+**现有测试**：... 只有以下三类允许改动用例：
+- **§2.3 规则 7 后半 ... 涉及的用例**：
+  `test_pre_commit_hook.py::test_phase_span_1/2/4`——...
+  处置：这三个用例改用 legacy 任务（`_write_state_yaml(..., legacy=True)`，恢复其原形态）
```
`test_pre_commit_hook.py` 中 `test_phase_span_1/2/4` 均已加 `legacy=True`；`test_phase_span_3`
**未改**（其暂存产出 P4 晚于 HEAD phase P3 → 规则 7 前半的"提前产出"分支跳过重跑，故无需改）。
重写的 BDD-19 经真实 hook 覆盖重跑行为：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py::test_bdd_19_non_legacy_staged_output_reruns_phase_gate -v
... test_bdd_19_non_legacy_staged_output_reruns_phase_gate PASSED [100%]
$ python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q
61 passed in 40.34s
```
**结论：ALIGNED**（重跑确按被暂存产出所属阶段；既有用例冲突已在设计 §8 例外清单逐条登记，
无静默放宽）。

---

### F3（原 A1-3）`check_ledger_events` 不再追溯存量任务 — ALIGNED（dispatch 重点）

**整改点**（`agate_common._level_registration_errors`）：**只校验「等级已在 LEVELS 登记」**；
「新任务等级 = 当前等级」移至 `pre-commit-gate.py` 的**新建目录分支**（本地、仅新任务）。

**证据 1（追溯 bug 已修，仓外 `/tmp/opencode/f3check`）**：登记 level-2（current=2），
对一条 level-1 存量非 legacy 任务跑 **CI 路径** `check-events.py`：
```
$ AGATE_ROOT=<fake>/fake python3 agate/scripts/check-events.py <task: task_created contract_level=1>
GATE EVENTS: 账本审计通过（1 行，哈希链完整，ts 单调，judge 轮次×0）
rc=0
```
放行（不再被追溯）。对照负向（`level=3` > 已登记 {1,2}，未登记）：
```
GATE EVENTS: 契约等级事件规则违反：
  - task_created 的等级 3 未登记；协议版本低于任务等级，请升级（第 1 行）
rc=1
```
即 fail-closed 语义仍在，仅去掉「恒等当前等级」。

**证据 2（「新任务等级 = 当前等级」仍在，且只在 pre-commit 新建目录分支）**：
```
# 新建目录 T009，task_created contract_level=2，current=1
$ AGATE_ROOT=<repo>/agate git commit -m "new task level2"
GATE: 新增任务目录 agate-workspace/tasks/T009-new 的等级 2 ≠ 当前等级 1（新任务必须登记当前等级，设计 §2.3 规则 2）
rc=1
# 新建目录 T010，task_created contract_level=1，current=1
$ AGATE_ROOT=<repo>/agate git commit -m "new task level1"
[master cf3ef7f] new task level1 v2
rc=0
```

**证据 3（新用例）**：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py::test_f3_current_level_2_existing_level_1_passes -v
... test_f3_current_level_2_existing_level_1_passes PASSED [100%]
```
**结论：ALIGNED**（F3 确认不再经 CI 路径追溯存量任务；恒等约束改在本地仅新任务分支）。

---

### F4（原 A2-1）`WORKFLOW.md` 收录新步骤 — ALIGNED

**证据**：
```
$ git diff agate/WORKFLOW.md
+| 1.1 | `pre-commit-gate.py`「账本与新目录」步骤 | 任意提交（每次提交都跑，不依赖 `.state.yaml` 是否暂存）| 账本级 | 新目录须有创建事件（规则 1）/ 新任务等级 = 当前等级（规则 2，本地仅新任务）/ 账本只追加（规则 3）/ 含创建/迁入事件的账本不可删（规则 4）/ 账本事件规则（规则 5）/ 每个有暂存文件的任务目录做 `[PROD_TOUCHED]` 扫描 + 非 legacy 任务按被暂存产出所属阶段重跑该阶段 gate（规则 7）；违反任一 → 中止 commit（TAG0050 批 A1，设计 §2.3）|
...
-**多任务适配**：`pre-commit-gate.sh` 扫描暂存区中所有变更的 `.state.yaml`...
+**多任务适配**：... **此外**，`1.1 账本与新目录` 步骤对**每个含暂存文件的任务目录**执行（不再只扫暂存的 `.state.yaml`）...
```
唯一事实源表已收录新步骤，「多任务适配」段已更新。**结论：ALIGNED**。

---

### F5（原 A2-2）`SELF-GATE.md` CHECK 范围 — ALIGNED

**证据**：
```
$ git diff SELF-GATE.md
-> ... （不写死上界，当前 CHECK 1-15，其中 CHECK 9 ...）+ LLM 语义审查。
+> ... （不写死上界，当前 CHECK 1-16，其中 CHECK 9 ...）+ LLM 语义审查。
-1. **跑 check-protocol-consistency.py** — 确认结构 CHECK 全集（当前 1-15）无 ERROR
+1. **跑 check-protocol-consistency.py** — 确认结构 CHECK 全集（当前 1-16）无 ERROR
$ grep -c '("CHECK ' agate/scripts/check-protocol-consistency.py
16
```
两处均已 1-16，与脚本 CHECK 数（16）一致。**结论：ALIGNED**。

---

### F6（原 A8）`P4-implementation.md` 声称修正 — ALIGNED（附残余观察）

**证据 1（被证伪的「已落地」已如实改写）**：`P4-implementation.md` §2 row 9 现写：
> `agate-next.py:_p6_judge_advance` | 改依契约（`requirement_active(...)`；legacy 回退 `judge.enabled`）——**F1 补齐（原记录谎称已落地，实为未改）** | 已落地

不再谎称；且 F1 已真落地（见上）。**逐条「声称 → 命令 → 结论」**：

| # | 声称（`P4-implementation.md` §6） | 产出它的命令 | 复评实跑 | 结论 |
|---|---|---|---|---|
| 1 | A1 验收文件 **26 passed** | `pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q` | `26 passed` | ✓ 成立 |
| 2 | `test_pre_commit_hook.py` **61 passed** | 同命令 | `61 passed` | ✓ 成立 |
| 3 | `test_agate_migrate_workspace.py` **9 passed** | 同命令 | `9 passed` | ✓ 成立 |
| 4 | 全量 **2713 passed / 40 failed / 2 skipped** | `pytest agate/tests/ -q -n auto` | `40 failed / 2712 passed / 3 skipped` | △ 见 R-1 |
| 5 | consistency **0 ERROR / 410 WARNING** | `check-protocol-consistency.py` | `0 ERROR / 411 WARNING` | △ 见 R-1 |
| 6 | ruff **All checks passed** | `~/.venvs/agate-dev/bin/ruff check agate/` | `All checks passed!` | ✓ 成立 |
| 7 | platform-assumptions 本批文件 **0 命中** | `check-platform-assumptions.py agate/scripts/ agate/tests/` | 新增行 0 命中；新文件 `agate-task-init.py` rc=0 | ✓ 成立 |
| 8 | R6 干净 clone **exit 0**；负向 **exit 1** | `bash docs/design-notes/r6-differential.sh ...` | 见 F2/A4 证据 | ✓ 成立 |

**结论：ALIGNED**——所有声称均已绑定可执行命令，被证伪的声称已删除/改写。第 4/5 条与复评实跑
差 1–2，经查为**环境/树依赖**（见 R-1），非无据声称。**A8 的实质缺陷（无据声称）已闭合。**

---

### F7（原 A4）测试缺口补齐 — ALIGNED

**证据**：新增/重写用例实跑全绿（仓外副本 `/tmp/opencode/tag0050_rr`）：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q
26 passed in 2.90s
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py::test_f1_p6_judge_advance_uses_contract \
    ::test_f3_current_level_2_existing_level_1_passes \
    ::test_bdd_19_non_legacy_staged_output_reruns_phase_gate -v
... 3 passed in 0.34s
```
- F1 缺口（原 0 命中）→ `test_f1_p6_judge_advance_uses_contract`；
- BDD-19 名不副实 → 已重写为**经 pre-commit hook** 提交只改产出、未改 phase 的场景（旧用例只直跑
  check-gate，不会因规则 7 后半缺失而红）；
- F3 追溯 bug → `test_f3_current_level_2_existing_level_1_passes`。

**全量 pytest（A4 要求实跑输出）**：
```
$ python3 -m pytest agate/tests/ -q --tb=no -n auto
40 failed, 2712 passed, 3 skipped in 68.24s
```
40 条失败**全部**落在 A2/A3/A4/B/C/D/E/F 后续批的既有红灯文件（`test_tag0050_{ci_replay, state_set,
obligations, write_tools, declarations, proxy_judgment, evidence, prod_touched, fitness, cross_batch}`
共 39 条）+ 1 条环境漂移 `test_setup_agate_dir.py`——与 A1 前**同一集合**，**A1 范围内 0 新回归**。
**结论：ALIGNED**。

---

## 新引入问题扫描

| 检查 | 方法 | 结论 |
|---|---|---|
| 平台假设 | `git diff -U0 -- agate/scripts agate/tests \| grep '^+' \| grep -nE 'python3\|/usr/bin\|/bin/\|\[ -L\|/tmp'` | 新增行 **0 命中**；新文件 `agate-task-init.py` 平台扫描 rc=0 ✓ |
| 破坏 §8 兼容承诺 | R6 双向差分（干净 clone corpus + A1 after） | **39 legacy 任务，0 差异，rc=0** ✓ |
| 既有测试被静默放宽 | 对照 §8 例外清单 | 仅 `test_phase_span_1/2/4` 改 legacy，已逐条登记；无其它静默放宽 ✓ |
| 碰坏其它文件 / 新回归 | 全量 pytest 失败集合 | 与 A1 前一致（同 40 条）✓ |
| `state-machine.md` 与脚本一致 | `check-state-transition.py`（legacy READY/DONE→Pn ERROR） | 文档与实现语义一致 ✓ |
| R6 自核验 + 负向 | 脏 corpus / 删必需规则 | 脏 corpus → rc=1；删 D12 → rc=1 ✓ |
| CHECK 16 负向 | 新增未登记 level-2 / 篡改 level-1 | 均 `ERROR (1)` rc=1（`快照文件 level-2.yaml 未登记到 LEVELS.yaml`）✓ |

R6 复跑命令与输出（干净 clone `/tmp/opencode/r6clone`，`--after` = A1 工作树）：
```
$ bash docs/design-notes/r6-differential.sh --corpus . --after <repo>/agate --allow <repo>/docs/design-notes/r6-allowlist.yaml
r6-differential: legacy 任务 39 个，差异 0 条，未匹配 0 条
rc=0
```
（原审查时仅比对到 1 个 legacy 任务；整改后纳入 READY/DONE，覆盖面扩大到 39 个——A4-R6 裁决已落实。）

**结论：未发现新引入的 MISALIGNED。**

---

## 残余观察（非阻塞，供主 Agent / 人工裁量）

- **R-1（数字环境/树依赖）**：`P4-implementation.md` §6 的「2713 passed / 2 skipped」与
  「410 WARNING」在复评机上分别为「2712 passed / 3 skipped」「411 WARNING」。
  - passed/skipped 差 1：源于 **Pillow 是否安装**——`test_agate_image_check.py` 的
    `test_img_1/3` 在装 Pillow 时 skip、缺 Pillow 时运行（`@pytest.mark.skipif(HAS_PIL)`）。
    故实现者机器的数字是其**真实运行值**，非无据声称。
  - WARNING 差 1–2：该计数随 `docs/reviews/`、`agate-workspace/tasks/` 下**未跟踪文件**
    漂移（实测：加/删本次 rereview 留痕文件即改变计数）。故固定值不可稳定复现。
  - **建议**：可把该行改为区间/口径说明（如「≈410，随未跟踪文件漂移」），或按最新实跑值刷新。
    不影响 A8 的实质闭合。
- **R-2（原 A2-3，未在 F1–F7 范围内）**：`agate/scripts/README.md:67` 仍写
  「hook 主程序：按顺序调度 **9 项检查** + …」——A1 新增步骤后该描述更不准。原审查标
  NEEDS_HUMAN_REVIEW（既有数字），本次未改，仍待人工确认（属 F 清单外）。
- **A1-4（有意偏离）**：PROD_TOUCHED 扫描面按「任务目录内**全部**暂存文件」而非 P2 §3.1 字面
  `*.md`，已由主 Agent 裁决接受并在 `P4-implementation.md` §3.2 登记为有意偏离 ✓。
- **A5（批次归属）**：`state-machine.md`（legacy 重开 ERROR）已随本批同步 ✓；
  `UPGRADING.md` / `CHANGELOG.md` 归 P8（发布时），符合主 Agent 裁决。

---

## 闭环建议（供主 Agent）

| 结论 | 项 | 动作 |
|---|---|---|
| ALIGNED | F1–F7（原 A1/A2/A3/A4/A8） | 可 commit |
| 残余（非阻塞） | R-1 数字漂移 | 可选：刷新 §6 数字或注明环境依赖 |
| 待人工 | R-2 `scripts/README.md`「9 项检查」 | 人工确认（原 NEEDS_HUMAN_REVIEW） |

> 环境隔离：本复评全程只读。所有 pytest / R6 / F2/F3 复现均在**仓外可丢弃副本**
> （`/tmp/opencode/tag0050_rr`、`/tmp/opencode/{f3check,f3new,f2scratch,r6clone}`，已清理）上运行；
> 被评审仓库 `git status --porcelain` 复核前后一致（仅新增本次留痕文件），未对被评审文件做任何写操作。
> [PROD_NOT_TOUCHED] 未接触生产环境。
