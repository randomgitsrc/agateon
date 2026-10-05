---
review_date: 2026-10-06
reviewer: protocol-alignment-review
change_summary: >-
  TAG0042 批 1（batch1-phase-semantics）——统一 phase 语义：agate-next 推进时不再预写下一阶段
  （去掉 _advance 的 state["phase"]=target 预写 + _write_state 落盘 + git add，删除孤儿 _write_state/_git，
  保留 state_transition 事件，改输出「下一阶段建议」）；同步 P2/P8 卡片表述与 UPGRADING v0.79.0 节；
  同步既有 test_tag0027_b1_agate_next_cli.py 的 3 处「推进后 phase」断言。
files_changed:
  - agate/scripts/agate-next.py
  - agate/phase-cards/P2-design.md
  - agate/phase-cards/P8-release.md
  - agate/UPGRADING.md
  - agate/tests/unit/test_tag0027_b1_agate_next_cli.py
  # round 2 修复轮新增（反向传播闭合；纯文本改述）
  - agate/state-machine.md
  - agate/dispatch-protocol.md
  - agate/CONTEXT.md
  - agate/loop-orchestration.md
  - agate/orchestrator-template.md
review_scope: >-
  TAG0042 批 1 的 agate/** 未 commit 改动（SELF-GATE 语义 gate，agent≠main）。
  变更触发模式：意图分析 → 反向传播 → 变更文件全文 + 反向传播文件 + 权威规则源（state-machine.md /
  dispatch-protocol.md / WORKFLOW.md）→ A1-A8。单轮审查。
prod_isolation: "[PROD_NOT_TOUCHED] —— 仅读取仓库 + 写 /tmp 留痕/日志 + 本报告；未触碰被评审改动集、主 checkout 与 ~/.agate。"
conclusion: aligned
review_rounds: 2
round1_conclusion: >-
  批 1 首审：misaligned。A1/A2/A3b/A5.3 同一根因 = 反向传播漏改 5 处权威文档——它们仍描述旧行为
  「agate-next 更新 .state.yaml phase + git add」（state-machine.md:326-331 / dispatch-protocol.md:291-292 /
  CONTEXT.md:33 / loop-orchestration.md:242-247 / orchestrator-template.md:56）。脚本、卡片、UPGRADING、
  测试 5 个改动面本身语义自洽；A3a/A4/A6/A7 ALIGNED；A5.1/A5.2 ALIGNED（CHANGELOG 属 P8 触发，非本批）。
pytest_full_run: >-
  2026-10-06，worktree /home/kity/oclab/agateon：`python3 -m pytest agate/tests/ -q --tb=short`
  → 61 failed / 2624 passed / 2 skipped（222.98s，exit 1）。61 failed 全部落在 batch2-6 的 P3 红灯测试文件
  （test_agate_config 12 / test_config_schema 10 / test_agate_run 9 / test_agate_doctor 8 / test_events_ledger 6 /
  test_agate_ci_verify 6 / test_gate_layer 5 / test_check_p8_delivery 3 / test_setup_agate_dir 1 /
  test_agate_scripts_encoding 1），均为「batch2-6 尚未实现」的 by-design 红灯；
  batch1 相关 4 文件（test_tag0042_batch1_phase_semantics / test_tag0027_b1_agate_next_cli /
  test_check_state_transition / test_agate_next_card）**零失败**。批 1 无回归。
round2_conclusion: >-
  TAG0042 批 1 复审（round 2）：aligned。首轮 4 项 MISALIGNED（A1/A2/A3b/A5.3，同一根因）全部闭合——
  5 处权威文档（state-machine.md 机械化段 :326-335 + 手工规格 step 7 :401-403、dispatch-protocol.md:291-295、
  CONTEXT.md:33、loop-orchestration.md:244-246、orchestrator-template.md:57-59）已改述为与
  agate-next.py:166-178 / P2-design.md:14-17 / P8-release.md:21 / UPGRADING.md:288-296 / git-integration.md:31,33
  同口径：自动化 `agate next` 只输出「下一阶段建议」+ `state_transition` 事件，**不预写** `.state.yaml` 的 `phase`、
  不 `git add`，`phase` 由下一阶段产出 commit 写入；state-machine/dispatch-protocol/CONTEXT/orchestrator-template
  四处显式标注「手工 fallback 仍写 `phase`」，自动化路径与手工路径区分明确。
  残留旧行为 grep（`写回 .state.yaml + git add` / `更新 .state.yaml phase + git add`）→ 0 命中；
  首轮 ALIGNED 项无回退：CHECK9 PASS / CHECK10 WARN 1（pre-existing CHANGELOG `check-windows-smoke.sh`，与本次无关）/
  CHECK2-refs 无来自 5 文档的新命中 / CHECK14-15 PASS；consistency 0 ERROR；count-tests 2687 未漂移；
  batch1 相关 4 测试文件 99 passed、doc 关联 7 文件 142 passed。
  首轮附注（UPGRADING T085 归因措辞侧重）仍为非阻塞观察项，留 P7/P8 留意，不阻塞 commit。
---

# 协议-脚本对齐审查 — TAG0042 批 1（batch1-phase-semantics）

> 审查对象：`git diff` 未 commit 改动（HEAD `d3ba1c5` main，P3 已落）。
> 对齐基准：`P1-requirements.md` BDD-1/BDD-2、`P2-design.md` §1.1 M1/M2/M3 + §1.2 N1、`P4-implementation-batch1.md`、`P3-test-cases-batch1.md`。
> 权威规则源：`agate/state-machine.md`（§主 Agent 的单步执行）、`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（反向传播文档仍声明旧行为，见 A1） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（脚本新行为未传播到权威文档，同 A1 根因） |
| A3 | 一致性连锁 + 反向传播 | A3a **ALIGNED** / A3b **MISALIGNED** → 合计 **MISALIGNED** |
| A4 | 测试覆盖 | **ALIGNED**（全量实跑：批 1 相关文件零失败） |
| A5 | 下游影响 + 文档传播 | A5.1 **ALIGNED** / A5.2 **ALIGNED**（待 P8）/ A5.3 **MISALIGNED** → 合计 **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | 逐条列出（见 A8；无无据声称） |

**总结论：misaligned**。MISALIGNED 共 4 项（A1 / A2 / A3b / A5.3），**同一根因**：本批改变的是 `agate-next` 的可观测行为（不再写 `phase`、不再 `git add`），但 5 处**权威文档**仍逐字描述旧行为，未随批 1 同步。改动面本身（脚本 + 2 卡片 + UPGRADING + 测试）语义自洽。NEEDS_HUMAN_REVIEW 0 条。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**变更意图**：`phase` 只表示「本 commit 的产出阶段」。`agate-next` 推进时只输出「下一阶段建议」+ append `state_transition`，**不**写 `.state.yaml` 的 `phase`、**不** `git add`。

**脚本实现**（`agate-next.py:166-178` `_advance`）：

```python
def _advance(task_dir, state, target, repo_root):
    """输出「下一阶段建议」+ append state_transition 证据；**不预写**下一阶段（TAG0042 批 1）。"""
    old = state.get("phase", "")
    _state_transition_event(task_dir, old, target)
    _log(f"{old} → 建议下一阶段 {target}：.state.yaml phase **未预写**（保持 {old}）。"
         f"phase 由 {target} 产出 commit 时写入；推进证据已 append state_transition。")
```

模块 docstring（`agate-next.py:11-14`）与 `:31` 亦已改述为「不预写 / 不 git add」「无系统临时目录字面量」。**改动面内部（脚本 vs 卡片 vs UPGRADING）语义一致**。

**但权威文档未同步** —— 以下文档逐字声明「由 agate-next 写 `.state.yaml` phase + git add」，与新脚本行为**直接矛盾**（均不在 diff 内）：

1. `agate/state-machine.md:326-331`（§主 Agent 的单步执行，机械化段）：
   > 下面步骤 5-7（跑 gate → 按转移规则算下一状态 → **写回 `.state.yaml` + git add**）对**普通 phase** 是纯查表动作，由 `agate next`（`agate-next.py`）完成
   （另 `state-machine.md:394-396` step 7「写回 `.state.yaml`（新阶段 / 重试记录 / PAUSED）」为该权威语义的手工规格）
2. `agate/dispatch-protocol.md:291-292`：
   > 步骤 6 的「跑 gate → 判定 → **前进写 `.state.yaml` phase → git add**」这一段查表机械动作由 `agate next` 完成
3. `agate/CONTEXT.md:33`（术语表 `agate next / agate advance` 行）：
   > 查 `phases.yaml` 表机械推进一个 phase（跑 gate → 按 `next`/`retreat`/`gate_pass_exit` 算下一状态 → **写 `.state.yaml` + git add**）
4. `agate/loop-orchestration.md:242-247`：
   > …→ 按 phases.yaml next **更新 .state.yaml phase + git add** + state_transition 事件（只 add 不 commit…）
5. `agate/orchestrator-template.md:56`：
   > 状态推进：普通 phase 的「跑 gate → 判定 → **前进写 `.state.yaml` phase → commit**」这一步由 `agate next` 查表机械完成

**结论**：MISALIGNED。
**差异**：文档声明「agate-next 写 phase + git add」，脚本已删除该行为（`:166-178`），文档与脚本在不可绕开路径上的推进语义相反。
**建议**：把这 5 处改述为「`agate-next` 输出「下一阶段建议」，**不预写** `.state.yaml` phase、不 `git add`；`phase` 由下一阶段产出 commit 写入」——与 `agate-next.py:167-178`、`P2-design.md:15-16`、`UPGRADING.md:288-296` 同一口径。

> 说明：`UPGRADING.md:279-296`（v0.79.0 节）与改动后的两张卡片（`P2-design.md:15-17` / `P8-release.md:21`）**本身与脚本一致**，A1 的问题只在反向传播漏改的 5 处权威文档。

---

### A2: 脚本→文档对齐 — MISALIGNED

核对「脚本做了但文档（权威口径）没写 / 写了相反」的裸露行为。

| 脚本行为 | 权威文档对应 | 判定 |
|---|---|---|
| `_advance` 不写 `phase`、不 `git add`，输出建议文本 | `UPGRADING.md:288-296` + `P2-design.md:15-16` + `P8-release.md:21` 已记载 | ALIGNED（卡片/UPGRADING 面） |
| 同上 | `state-machine.md:326-331` / `dispatch-protocol.md:291-292` / `CONTEXT.md:33` / `loop-orchestration.md:242-247` / `orchestrator-template.md:56` 仍写「由 agate-next 写 phase + git add」 | **MISALIGNED**（与 A1 同 5 处） |
| `_advance` 仍 append `state_transition`（`from`/`to`/`phase`=target） | `loop-orchestration.md:258-260` / `CONTEXT.md:31`（账本事件类型含 `state_transition`）| ALIGNED（事件类型与账本描述不变） |
| `_write_state()` / `_git()` 删除（孤儿代码清理） | 无文档引用这两个函数名 | ALIGNED |

**结论**：MISALIGNED（同 A1 根因——脚本新行为只在卡片/UPGRADING 落地，未同步到权威协议文档）。
**建议**：同 A1。

> A1/A2 是同一处差异的**两个方向**（文档声明 X / 脚本做 ¬X），报告不重复计费为两条独立缺陷；均在 A3b 修复后一并转绿。

---

### A3: 一致性连锁 + 反向传播 — A3a ALIGNED / A3b MISALIGNED（合计 MISALIGNED）

#### A3a（连锁：已知的衍生改动）— ALIGNED

- **孤儿函数**：`grep -n "_write_state\|_git(" agate/scripts/agate-next.py` → **0 命中**（`:116-129` 的 `_write_state` 与 `:169-183` 的 `_git` 已删，无残留调用）。全仓 `agate/scripts/*.py` 无其它脚本调用 `agate-next.py`（仅注释/docstring 提及）。
- **测试同步**：`test_tag0027_b1_agate_next_cli.py` 3 处「推进后 phase」断言已同步（`:156` L156→保持 P5；`:317` gate_p65 pass 后保持 P6；`:371` 保持 P5）；`_advance` 分支（`:279`/`:288`/`:386`）调用点与保留的 `repo_root` 形参兼容（docstring 已注明「批 1 后不再做 git 操作」）。**无遗留「预写」断言**。
- **状态跳变校验路径**：`check-state-transition.py` **只对暂存 `.state.yaml` 的 diff** 判 `old_phase → new_phase` 合法性（`:251-269`），不读账本 → 去 `git add` 后，phase 变更改由「下一阶段产出 commit 暂存 `.state.yaml`」触发同一校验，跳变合法性守护**未弱化**（与 `P2-design.md` §1.2 N1 一致）。
- **账本交叉**：`check-events.py` 对 `state_transition` 只做哈希链/已知类型处理（`:14`），**无** `state_transition.to == .state.yaml phase` 的交叉断言 → 新语义（事件记「建议推进」而 `.state.yaml` 保持旧 phase）**不破链、不触发审计**。
- **docstring 平台面**：`:31`「无 /tmp 字面量」→「无系统临时目录字面量」是为规避 `check-platform-assumptions.py` R4 自命中，方向正确（`_TMP` 拼接惯例同 `P3-test-cases-batch1.md` §4）。

#### A3b（反向传播：应被本批影响但未在 diff 中的文件）— MISALIGNED

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| `agate/state-machine.md`（§单步执行 :326-331 + 手工规格 step 7 :394-396）| **否** —— 仍写「写回 `.state.yaml` + git add」由 agate-next 完成 | **MISALIGNED** |
| `agate/dispatch-protocol.md`（:291-292）| **否** —— 仍写「前进写 `.state.yaml` phase → git add」由 agate-next 完成 | **MISALIGNED** |
| `agate/CONTEXT.md`（:33 术语表）| **否** —— 仍写「写 `.state.yaml` + git add」 | **MISALIGNED** |
| `agate/loop-orchestration.md`（:242-247）| **否** —— 仍写「更新 .state.yaml phase + git add」 | **MISALIGNED** |
| `agate/orchestrator-template.md`（:56）| **否** —— 仍写「前进写 `.state.yaml` phase → commit」由 agate-next 完成 | **MISALIGNED** |
| `agate/WORKFLOW.md`（:502/:508）| 不需改 —— 只说「推进这一步用 `agate next` 查表机械完成」，未描述写 phase/git add | ALIGNED |
| `agate/git-integration.md`（:31/:33/:113）| 不需改 —— :31「产出和 .state.yaml phase 更新在同一个 commit 里」、:33「phase = 本 commit 提交的产出阶段，不得提前写」、:113 手工步「更新 .state.yaml phase（先更新再 commit）」**均与新语义一致** | ALIGNED |
| `agate/phase-cards/P1,P3,P4,P5,P6,P7-*.md` | 不需改 —— 各卡均写「phase 推进 Pn+1 **随 Pn+1 产出 commit 一起**」，本就与新语义一致（仅 P2/P8 需补「agate-next 亦不预写」注，已改） | ALIGNED |
| `agate/assets/execution-roles/*.md` / `review-roles/*.md` | 不需改 —— `grep agate-next\|预写\|更新 .state` **0 命中** | ALIGNED |
| `agate/CHANGELOG.md` | 待 P8（`check-changelog.py` 仅 P8 触发，见 A5.2）| 不计入批 1 |

**结论**：MISALIGNED（5 处权威文档反向传播缺失）。**建议**：同 A1；这 5 处为纯文本改述，与批 1 同批修最省（避免后续批次重复触达同一语义）。

> **无 P7 记录**：任务仍在 P4（`ls P7*` 无产物）。5 处缺失**不对应** `P4-implementation-batch1.md` 的两条 `[DESIGN_GAP]`（后者仅涉 UPGRADING 版本号标题 / `_advance` 孤儿函数），故不适用角色原则 6 的 `[KNOWN_DEVIATION]` 豁免，按普通 MISALIGNED 处理。

---

### A4: 测试覆盖 — ALIGNED

**新增/同步测试**：

- `agate/tests/unit/test_tag0042_batch1_phase_semantics.py`（P3 产出，6 例）：TC-B1-01（不预写 phase）/ TC-B1-02（不 `git add`）/ TC-B2-01（`_advance` 无 `state["phase"] = target`）/ TC-B2-02（卡片表述与行为一致）/ TC-B2-03（UPGRADING 记载不预写）/ TC-B2-04（全 `agate/scripts/*.py` 无预写实现）。覆盖 BDD-1/BDD-2 全部要求。
- `test_tag0027_b1_agate_next_cli.py`：3 处断言同步为新语义（A3a 已列），其余 `state_transition` 事件 / 不落盘 resolution / retreat 路径断言不变。

**边界评估**：新逻辑边界 = ① 不写 phase、② 不 `git add`、③ 仍发 `state_transition`、④ 建议文本。① ② ③ 均有直接断言；④ 由 `_advance` 调用链 + BDD-11 事件断言间接覆盖。孤儿函数删除无直接单测，但由源码扫描（TC-B2-01/04）+ 运行时调用点（A3a grep）双重约束。

**全量 pytest 实跑（A4 强制项，2026-10-06，本次审查执行）**：

```
$ python3 -m pytest agate/tests/ -q --tb=short -p no:cacheprovider
（worktree /home/kity/oclab/agateon，HEAD d3ba1c5 + 批 1 未 commit 改动）

=========================== short test summary info ============================
FAILED agate/tests/unit/test_agate_config.py ... (12)
FAILED agate/tests/unit/test_config_schema.py ... (10)
FAILED agate/tests/unit/test_agate_run.py ... (9)
FAILED agate/tests/unit/test_agate_doctor.py ... (8)
FAILED agate/tests/unit/test_events_ledger.py ... (6)
FAILED agate/tests/unit/test_agate_ci_verify.py ... (6)
FAILED agate/tests/unit/test_gate_layer.py ... (5)
FAILED agate/tests/unit/test_check_p8_delivery.py ... (3)
FAILED agate/tests/unit/test_setup_agate_dir.py ... (1)
FAILED agate/tests/unit/test_agate_scripts_encoding.py::test_bdd_5_all_test_py_text_io_explicit_encoding (1)
61 failed, 2624 passed, 2 skipped in 222.98s (0:03:42)
[exit 1]
```

**失败分类**：61 failed 全为 batch2-6 尚未实现的 P3 红灯（`test_agate_config`/`test_config_schema`/`test_agate_run`/`test_events_ledger`/`test_agate_ci_verify`/`test_gate_layer`/`test_check_p8_delivery`/`test_agate_doctor`/`test_setup_agate_dir` = batch2/3/4/5）——恒为「被测特性未实现」断言（如 `test_check_p8_delivery`：「`delivery` 未声明时 P8 gate 须拦截；当前 rc=2（无 delivery 校验）」）；`test_agate_scripts_encoding::test_bdd_5` 是扫描到 **batch2 测试文件** `test_config_schema.py:235` 缺 `encoding=`（属 batch2 测试自身质量，非批 1）。**batch1 相关 4 文件零失败**（`grep` 确认 log 中无 batch1 文件行）。

**结论**：ALIGNED。批 1 新逻辑覆盖充分、全量实跑无批 1 引入的回归。

---

### A5: 下游影响 + 文档传播 — A5.1 ALIGNED / A5.2 ALIGNED / A5.3 MISALIGNED（合计 MISALIGNED）

#### A5.1 破坏性变更 / 向后兼容 — ALIGNED

- `.state.yaml` schema、字段集、frontmatter 均未变（`git diff` 不含 `agate/rules/` / `schema/` / `agate_common.py`）→ 存量任务无需迁移（与 `UPGRADING.md:281-282`「老任务无需迁移」一致）。
- 编排惯例变化已在 `UPGRADING.md:284-296` 明确告知（「phase 推进随下一阶段产出 commit 一起」），符合 `P1` §2 隐含需求 4。
- 回退路径（`agate-retreat-to.py`）仍写 phase，不在本批范围（`P2-design.md` §1.2 N2）——无破坏。

#### A5.2 CHANGELOG — ALIGNED（待 P8，非 MISALIGNED）

本批是协议语义变更，但本仓 `check-changelog.py` **仅 P8 触发**（`pre-commit-gate.py:522` `if phase == "P8"`；`WORKFLOW.md:355` 表 1.6「仅 P8 检查，P1-P7 不触发」）。`CHANGELOG.md` 顶部 `[Unreleased]` 当前为空，TAG0042 尚无条目——**属 P8 统一补**，符合既有 SELF-GATE 任务惯例（同 TAG0034 A5.2 判据）。**不判 MISALIGNED**。

#### A5.3 文档传播 — MISALIGNED

除代码改动外，应被影响的文档 = A3b 的 5 处权威文档（`state-machine.md` / `dispatch-protocol.md` / `CONTEXT.md` / `loop-orchestration.md` / `orchestrator-template.md`）——均**未同步**，仍描述旧行为。`P2-design.md:15-16` / `P8-release.md:21` / `UPGRADING.md:279-296` 已同步。**MISALIGNED**（同 A1/A2/A3b 根因）。

**结论**：合计 MISALIGNED（A5.1/A5.2 ALIGNED；A5.3 与 A3b 同 5 处）。

---

### A6: 锚点表覆盖 — ALIGNED

- 本批**未新增/改名** `agate/scripts/check-*.py`，也未改 `agate/rules/schema/` 字段集 → CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 无新增义务。
- `grep "agate-next\|agate next\|advance" agate/scripts/check-protocol-consistency.py` → **0 命中**（锚点表不引用 agate-next 行为）→ 无需更新锚点。
- 实跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **exit 0 / 0 ERROR / 400 WARNING**；`✅ PASS CHECK 9 协议-脚本结构对齐`，无 `CHECK9-coverage`。
- WARNING 400 = `CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 397`。较 `P2-design.md` §8 基线（398）多 2 —— 经 `--show-frozen-warnings` 定位为**本次派发文件** `P4-dispatch-context-protocol-alignment-review.md:12,32` 引用「尚未生成的成果报告路径 `docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`」产生的 2 条瞬时报错（本报告写盘后即消失），**非批 1 引入**。
- `bash agate/tests/scripts/count-tests.sh` → **2687**（与 `P4-implementation-batch1.md:88` 一致，未漂移）。

**结论**：ALIGNED。

---

### A7: 设计原则一致性 — ALIGNED

逐条核对相关 ADR（`agate/adr.md`）：

- **ADR-001（隔离性——主 Agent 不写产出）**：本批改的是**状态推进脚本**（`agate-next`），未授权主 Agent 写阶段产出；`phase` 语义收紧为「本 commit 产出阶段」反而强化了「状态与产出一致」。**一致**。
- **ADR-002（可判定性——gate 机器可判定）**：去掉预写后，推进判定仍由 `check-gate.py` exit code + `phases.yaml` 表机械完成；`state_transition` 账本事件保留为可观测证据。**一致**。
- **ADR-004（安全网分层——hook 兜底）**：`check-state-transition.py` 的跳变合法性校验路径不变（phase 由产出 commit 暂存触发，见 A3a）。**一致**（未弱化安全网）。
- **ADR-005（改动性质决定流程）**：本批属协议本体的行为逻辑改动 → 触发 SELF-GATE（本审查即该流程），方向一致。
- **是否存在未记录的新架构决策？** 「phase = 本 commit 提交的产出阶段，不得提前写」这一原则**已记录**于 `agate/git-integration.md:33`（明文档化的原则，非新决策）；本批是让**行为**与之一致（消歧义），不引入新架构决策 → **无需新增 ADR**。

**结论**：ALIGNED。（如需更强留痕，可在 P8 考虑把「phase 语义统一」的一句话回溯进 ADR，但非本批义务。）

---

### A8: 声称-命令绑定

对本批新增/变更的**数字或结论类声称**逐条给出产出命令：

| 声称 | 产出命令 | 结论 |
|---|---|---|
| `agate-next` 推进时不预写下一阶段（`UPGRADING.md:288` / 卡片 / 脚本 docstring）| `grep -n 'state\["phase"\] = target' agate/scripts/agate-next.py` → 0 命中；`python3 -m pytest agate/tests/unit/test_tag0042_batch1_phase_semantics.py -q` | ✅ 声称成立（代码移除 + 6 例绿） |
| 无破坏性变更 / 老任务无需迁移（`UPGRADING.md:279-282`）| `git diff -- agate/rules/ agate/scripts/agate_common.py agate/rules/schema/` → 空（schema/字段集未动）| ✅ 成立 |
| 「peekview T085 的 8 次 `--no-verify`」（`UPGRADING.md:294`）| `grep -n 'no-verify 8 次' /home/kity/oclab/peekview/docs/reviews/T085-retrospective-20260802.md` → 命中 L61/L85/L164/L212 | ✅ 数字成立（外部仓库；根因表述见该复盘 L87/L212「state.yaml phase 更新时机」） |
| 用例数 `2687`（`P4-implementation-batch1.md:88`）| `bash agate/tests/scripts/count-tests.sh` → `总计：2687 个测试用例` | ✅ 成立 |
| 一致性基线 `0 ERROR / 398 WARNING`（`P4-implementation-batch1.md:87`）| `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR / 400 WARNING | ⚠️ 当前 400（+2 为本次派发文件的瞬时引用告警，见 A6）；**0 ERROR 成立** |

无「无法给出命令」的无据声称；无应删项。

> 备注（非 MISALIGNED）：`UPGRADING.md:294` 把 `--no-verify` 归因于「预写 phase vs pre-commit 校验冲突」，而 T085 复盘的自述根因是「pre-commit hook **超时**」（`T085-retrospective-20260802.md:87/212`），其改进项 IMP-1 即「state.yaml phase 更新时机调整（commit 后更新）」。两处**方向一致**（皆指向 phase 写入时机），措辞侧重不同；不构成需修复项，提请 P7/P8 留意即可。

---

## 闭环规则表（本审查终态）

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **MISALIGNED** | A1 / A2 / A3b / A5.3（同一根因：5 处权威文档未反向传播）| **必须修复**：按 A1「建议」改述 `state-machine.md:326-331`（+ 手工规格 step 7 `:394-396`）`dispatch-protocol.md:291-292` `CONTEXT.md:33` `loop-orchestration.md:242-247` `orchestrator-template.md:56`，与新脚本/卡片/UPGRADING 同口径；修完重审。 |
| ALIGNED | A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | 通过。 |

**不可 commit**（存在未闭合 MISALIGNED）。修复后建议对本报告做同任务复核轮（round 2），追加 `round2_conclusion`。

---

## 附：A4 全量 pytest 尾部实跑输出

```
$ python3 -m pytest agate/tests/ -q --tb=short -p no:cacheprovider
（worktree /home/kity/oclab/agateon，2026-10-06）
...
FAILED agate/tests/unit/test_check_p8_delivery.py::test_bdd_15_p8_gate_passes_only_when_delivery_declared
FAILED agate/tests/unit/test_config_schema.py::test_bdd_5_schema_file_exists_and_is_isomorphic
FAILED agate/tests/unit/test_events_ledger.py::test_bdd_12_cmd_run_event_appended
FAILED agate/tests/unit/test_gate_layer.py::test_bdd_14_phases_yaml_selects_gate_sets_by_commit_type
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED agate/tests/unit/test_agate_scripts_encoding.py::test_bdd_5_all_test_py_text_io_explicit_encoding
61 failed, 2624 passed, 2 skipped in 222.98s (0:03:42)
[exit 1]
```

---

## round 2 复审（2026-10-06，同一任务复核轮）

> 复审范围：只复核首轮 MISALIGNED 的 4 项（A1 / A2 / A3b / A5.3）修复是否闭合，并确认修复未使首轮 ALIGNED 项回退（回归面）。
> 修复落点（`git diff` 可见，均未 commit）：`agate/state-machine.md`、`agate/dispatch-protocol.md`、`agate/CONTEXT.md`、`agate/loop-orchestration.md`、`agate/orchestrator-template.md`（纯文本改述，不改任何机制/脚本/卡片/UPGRADING/测试）。

### 复审结论汇总

| # | 审查项 | 首轮 | round 2 |
|---|--------|------|---------|
| A1 | 文档→脚本对齐 | MISALIGNED | **ALIGNED** |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED** |
| A3b | 反向传播 | MISALIGNED | **ALIGNED** |
| A5.3 | 文档传播 | MISALIGNED | **ALIGNED** |
| A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8 | — | ALIGNED | **无回退（ALIGNED）** |

**总结论：aligned**。首轮 4 项同一根因（5 处权威文档未反向传播）已全部闭合，无新增不一致，无回退。解除 commit 阻塞。

### A1 / A2 / A3b / A5.3 逐项复核 — ALIGNED

**统一口径基准**：`agate-next.py:166-178`（`_advance` 无 `state["phase"] = target` / 无 `_write_state` / 无 `_git`，仅 `_state_transition_event` + 输出「建议下一阶段」）、`P2-design.md:14-17`、`P8-release.md:21`、`UPGRADING.md:288-296`、`git-integration.md:31/33`（`phase` = 本 commit 提交的产出阶段，不得提前写下一阶段）。

5 处文档新表述逐处核对（同口径）：

| 文档（落点） | 新表述要点 | 判定 |
|---|---|---|
| `state-machine.md:326-335`（机械化段） | 步骤 5-7 表述「建议推进」；`agate next` 只输出「下一阶段建议」+ `state_transition` 事件、**不预写** `phase`、不 `git add`，`phase` 由下一阶段产出 commit 写入（并指 `git-integration.md`）；fallback 句补「手工 fallback 仍写 `phase`，与自动化路径不同」 | ALIGNED |
| `state-machine.md:401-403`（手工规格 step 7） | 保留「写回 `.state.yaml`」手工规格，显式加限定「本步为**手工 fallback** 规格；`agate next` 自动化路径**不写** `phase`」 | ALIGNED |
| `dispatch-protocol.md:291-295` | 「……前进写 phase → git add」改为「……前进」；补只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补「按该节手工规格写 `phase`」 | ALIGNED |
| `CONTEXT.md:33` | 术语行改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 `.state.yaml` 的 `phase`、不 `git add`——`phase` 由下一阶段产出 commit 写入」；fallback 补手工规格写 `phase`；标 TAG0042 批 1 | ALIGNED |
| `loop-orchestration.md:244-246`（自动推进流程图） | 「更新 .state.yaml phase + git add」改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 .state.yaml phase、不 git add」；跳变合法性改由下一阶段产出 commit 的 pre-commit 校验 | ALIGNED |
| `orchestrator-template.md:57-59` | 「前进写 `.state.yaml` phase → commit」改为「……前进」；补只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补手工规格写 `phase` | ALIGNED |

- **「自动化 `agate next` 不写 phase」与「手工 fallback 写 phase」的区分**：在 `state-machine.md`（机械化段 + 手工规格 step 7 两处）、`dispatch-protocol.md`、`CONTEXT.md`、`orchestrator-template.md` 四处显式标注；`loop-orchestration.md` 该段是自动推进流程图（仅描述自动化路径），无手工分支，无需 fallback 注——**区分充分，无歧义**。
- **残留旧行为复核**：`grep -rn "写回 .state.yaml + git add\|更新 .state.yaml phase + git add" agate/*.md` → **0 命中（exit 1）**。全 `agate/` tree 扫描「预写」仅剩新正确表述（`不预写`/`未预写`）与 `UPGRADING.md` 的否定式「不再预写」。
- **其余提及 phase 写入的位置**（`state-machine.md:523/625` 手工 commit / 重试记录、`git-integration.md:113` 手工提交步、`retrospective-template.md:134` 通用术语）经核对均属**手工提交/记录路径**描述，与新语义一致（`phase` 在产出 commit 时写入），**非旧自动化行为残留**，无需改——与首轮 A3b 判定一致。

**A1/A2/A3b/A5.3 结论**：4 项**全部 ALIGNED**（同一根因闭合）。

### 回归面复核 — 首轮 ALIGNED 项无回退

| 维度 | 复核命令 / 依据 | 结果 |
|---|---|---|
| CHECK2-refs / CHECK10 / 平台扫描 | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **exit 0 / 0 ERROR / 398 WARNING**；CHECK9 PASS；CHECK10 WARN 1（`check-windows-smoke.sh @ CHANGELOG.md:1529`，pre-existing，与本次无关）；CHECK2-refs **无来自 5 文档的新命中**（`--show-frozen-warnings` 逐条核对）；CHECK14/15 PASS |
| 文档平台假设 | 新表述文本无 `/tmp` 等字面量（显式传入 5 docs 仅在未改动的 `orchestrator-template.md:68` 命中原存 R2；文档不在 CI 目标面） | 无新增 |
| A4 用例覆盖 | `count-tests.sh` → **2687**（未漂移）；`pytest` batch1 4 文件 → **99 passed**；doc 关联 7 文件（doc_sweep / docs_assertions / protocol_mechanism_anchors / check_protocol_consistency / upgrading_contract_doc / protocol_dedup_audit / review_role_docs）→ **142 passed** | 无回归 |
| A3a（孤儿函数/事件/校验路径） | 修复未改脚本；`agate-next.py` diff 不变（`_write_state`/`_git` 已删、`state_transition` 保留） | 无回退 |
| A5.1 / A5.2 | 修复为纯文本，未动 `.state.yaml` schema / CHANGELOG（仍待 P8） | 无回退 |
| A6 / A7 / A8 | 未新增/改名脚本、未动锚点表、未引入新架构决策；无新增无据声称 | 无回退 |

### round 2 闭环规则表

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| **ALIGNED** | A1 / A2 / A3b / A5.3（首轮 MISALIGNED，本轮闭合）+ A3a / A4 / A5.1 / A5.2 / A6 / A7 / A8（首轮 ALIGNED，无回退） | 通过，**可 commit**。 |

> 遗留（非阻塞，非 MISALIGNED）：首轮 A8 备注——`UPGRADING.md:294` 对 T085 `--no-verify` 的归因侧重（「预写 phase vs pre-commit 校验」vs 复盘自述「pre-commit hook 超时」）措辞不同但方向一致，交由 P7/P8 留意，不阻塞本批 commit。

**round 2 结论：ALIGNED（可 commit）。**
