---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 G1（A2 CI 逐提交回放 + A3 state-set/状态事实 + A4 义务机械核验）SELF-GATE 复评——复核原 MISALIGNED（A1-A5）的 F1–F7 整改闭合 + 新引入问题
files_changed: [agate/scripts/check-obligations.py, agate/scripts/pre-commit-gate.py, agate/scripts/check-state-transition.py, agate/scripts/agate-ci-verify.py, agate/rules/obligations.yaml, agate/UPGRADING.md, agate/WORKFLOW.md, agate/state-machine.md, agate/scripts/README.md, agate/tests/README.md, .github/workflows/protocol-tests.yml, agate/tests/unit/test_tag0050_obligations.py, agate/tests/unit/test_check_state_transition.py, agate/tests/integration/test_tag0050_ci_replay.py, agate/tests/integration/test_tag0050_state_set.py, agate/tests/unit/test_agate_ci_verify.py]
---

# 协议-脚本对齐审查（复评）— TAG0050 合批 G1（A2 + A3 + A4）

> 模式：SELF-GATE **Layer 1 · 复评**。对象 = 原审查 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1.md` 判 MISALIGNED 的 A1/A2/A3/A4/A5，是否已按 `P4-dispatch-context-implementer-G1-fix.md` 的 **F1–F7** 整改闭合 + 是否引入新问题。
> HEAD `b0a16c3a`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0），G1 改动**未提交**。
> 只读纪律：全程未写被评审文件；F2 真实 commit 复现在 `/tmp/opencode` 可丢弃副本内完成，pytest 用 `--basetemp=/tmp/opencode/...`；复评前后 `git status --porcelain` 逐字节一致。`[PROD_NOT_TOUCHED]`。

## 复评结论汇总

| # | 审查项 | 原结论 | 复评结论 |
|---|--------|--------|----------|
| A1 | 文档→脚本对齐 | MISALIGNED | **ALIGNED**（A1-1..A1-6 全闭合，见 F1–F5） |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED**（F4/F7 所列 4 处已闭合；另有反向传播残留 → 新发现 N1） |
| A3 | 一致性连锁 + 反向传播 | MISALIGNED | **ALIGNED**（F3 + F6 闭合；N1 为反向传播残留） |
| A4 | 测试覆盖 | MISALIGNED | **仍 MISALIGNED**（A4-3 / A4-5 未闭合——DESIGN_GAP 无 P7 `REVIEWED-ACCEPTED`） |
| A5 | 下游影响 + 文档传播 | MISALIGNED | **ALIGNED**（workflow / UPGRADING 已同步；CHANGELOG 显式延期留痕） |
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED** |
| A7 | 设计原则一致性 | NEEDS_HUMAN_REVIEW | **NEEDS_HUMAN_REVIEW**（未变） |
| A8 | 声称-命令绑定 | ALIGNED | **ALIGNED** |

> **一句话**：F1–F7 的**脚本/文档/测试整改主体已闭合**（F1 真 rc=0、F2 真 commit 账本含 `gate_run`、F3/F4/F5/F6 均有实跑证据）；**A4 仍有 2 个未被 F1–F7 覆盖的测试缺口**（BDD-42 真变异、BDD-43），且 A2 的文档反向传播有一处遗漏（N1）。⇒ 不建议在补齐 A4-3/A4-5 或补 `[HUMAN_CONFIRMED]`/P7 `REVIEWED-ACCEPTED` 前直接 commit。

---

## F1–F7 逐条闭合核验（可复现证据）

| # | 原问题 | 复评结论 | 证据 |
|---|--------|----------|------|
| **F1** | `check-obligations.py` 恒红，BDD-44 未达成 | **ALIGNED** | 见下 F1 |
| **F2** | `gate_run` 未随本次提交入库 | **ALIGNED** | 见下 F2 |
| **F3** | RM-AG0101 未落地 | **ALIGNED** | 见下 F3 |
| **F4** | A2 分支①未实现却声称已实现 | **ALIGNED** | 见下 F4 |
| **F5** | A2 §8 第 12 项未实现 | **ALIGNED** | 见下 F5 |
| **F6** | UPGRADING/WORKFLOW/state-machine/workflow 未同步 | **ALIGNED** | 见下 F6 |
| **F7** | docstring/README/注释与实现不符 | **ALIGNED（所列 4 处）** | 见下 F7；残留 N1 |

### F1（重点）— `check-obligations.py` 真 rc=0

**脚本实现**（`agate/scripts/check-obligations.py:282-287`）：
```python
if disposition == "M":
    # scope: protocol-repo（CI/手工执行）的义务：…不核验必经路径可达性 / pytest 凭证
    if in_ratio:                       # in_ratio = item.get("scope") != "protocol-repo"（:275）
        _check_enforced_at(item, oid, reachable, errors)
        _check_test_node(item, oid, repo_root, errors)
```

**实跑证据**（本复评执行）：
```
$ python3 agate/scripts/check-obligations.py ; echo EXIT=$?
M 类占比: 56/119 = 0.4706（基线 56/119 = 0.4706）
归宿分布: M=56 C=33 R=30
CHECK-OBLIGATIONS: OK（无「无归宿」项 + 无 ERROR + M 类占比不低于基线）
EXIT=0
```
F13 的 4 条（`obligations.yaml:294/907/971/990`）均已带 `scope: protocol-repo`（`grep -c` = 7，含基线注释行），跳过硬核验 ⇒ **工具转绿，BDD-44 达成**。BDD-40/44 的终态冲突按原评审建议以**临时构造**协调（`test_tag0050_obligations.py:22-51`：同一条目去 scope 报 ERROR / 加 scope 跳过）。**结论：ALIGNED。**

### F2（重点）— 真实 commit 后已提交账本含 `gate_run`

**脚本实现**：`pre-commit-gate.py` 新增 `2h.1e`——`gate_run`（2h.1b）之后再 `git add` 一次（原 2h.1d 的 add 保留在前，覆盖 `state_transition`）。

**独立复现**（本复评在 `/tmp/opencode` 一次性副本内：`git init` → symlink `pre-commit-gate.sh` → 种子 `.state.yaml`(P5)+`P5-verification.md`+账本 → `AGATE_ROOT=<dev checkout>/agate git commit`）：
```
COMMIT rc = 0
--- git show HEAD:agate-workspace/tasks/T001/gate-events.jsonl ---
{"contract_level":1,"event":"task_created",...}
{"event":"state_transition","from":"","phase":"P5",...,"to":"P5",...}
{"cmd":"check-gate.py P5","event":"gate_run","exit":2,"phase":"P5",...,"runner":"pre-commit",...}
has gate_run        : True
has state_transition: True
```
新增用例 `test_tag0050_state_set.py::test_gate_run_and_state_transition_committed_with_real_commit`（真实 `git commit` + 读**已提交**账本）单跑 `1 passed`，覆盖 A4-1/A4-2。**结论：ALIGNED。**

### F3 — RM-AG0101（BDD-3 扫描排除 `AGATE_CARD` 块）

**脚本实现**（`check-state-transition.py:64-84`）：新增 `_strip_agate_card_blocks()`，`_scan_bdd3_keyword_phases` 扫描前先剔除 `<!-- AGATE_CARD_START -->…<!-- AGATE_CARD_END -->` 块（`:235`）。
**两向回归用例**（`test_check_state_transition.py` 新增）：
- `test_bdd_3_card_block_keyword_excluded`——仅卡内"重派"→ 不触发 WARNING；
- `test_bdd_3_real_progress_signal_still_warns_with_card_present`——`P*-progress.md` 真实"重派"仍触发 WARNING。

两用例随 `test_check_state_transition.py` 一并实跑通过（见下 A4 实跑）。**结论：ALIGNED。**

### F4（重点）— docstring 与实现一致（分支①）

**docstring**（`agate-ci-verify.py:21-26`）：
> ① 按逐提交 `.agate-version` 定位/安装对应版本目录**未实现**（依赖 CI 安装各版本…）——`.agate-version` 目前只用于「单调不降」检查…**不用于选协议根**。

**实现**（`_resolve_protocol` `:160-181`）：只认 `AGATE_ROOT` 环境（→ 其仓库 merge-base）或「仓库含协议本体」（→ merge-base），**确实不读 `.agate-version` 选根**；`.agate-version` 仅用于 `:355-368` 单调不降检查。判定分支③（`:378`）只认「仓库里的 `.agate-version`」或「仓库含协议本体」。docstring 与实现**逐条一致**；`agate/scripts/README.md:106` 同步降级为「未实现」；`P4-implementation-G1.md:76` 登记 `[DESIGN_GAP]`。**结论：ALIGNED（实现与降级后的文档一致）。**

### F5 — A2 §8 第 12 项（legacy 新增 PROD_TOUCHED ERROR 单独统计）

**脚本实现**（`agate-ci-verify.py:403-412`）：对回放失败中 `"PROD_TOUCHED" in reason` 且 `_is_legacy_commit(repo, c)` 者单独计数并列 SHA。
**用例**：`test_tag0050_ci_replay.py::test_bdd_26b_legacy_prod_touched_error_separately_counted`（断言 `FAIL` + `§8-12`/`PROD_TOUCHED ERROR` + SHA）实跑通过。**结论：ALIGNED。**

### F6 — 文档同步

- `agate/UPGRADING.md`：新增「未发布 — TAG0050 批 G1」节（`.agate-version` / `fetch-depth: 0` / GitHub+GitLab 示例 / squash 说明 / `agate-state-set` 用法）✓
- `agate/WORKFLOW.md:369`：CI 兜底口径改为「逐提交回放本地 hook」+ `fetch-depth: 0` + `--base` ✓
- `agate/state-machine.md`：`agate next` 不再追加 `state_transition`；「phase 的唯一写入口是 `agate-state-set.py`」✓
- `.github/workflows/protocol-tests.yml`：`gate-backstop` 加 `fetch-depth: 0` + 按事件传 `--base`/`--push --base` ✓

**结论：ALIGNED。**

### F7 — docstring/README/注释与实现不符（所列 4 处）

原评审 A2-2 列的 4 处（`agate-ci-verify.py` docstring、`pre-commit-gate.py` 注释、`protocol-tests.yml:298` 注释、`scripts/README.md:106`）**均已修正**：前两处随 F4/F2 改；workflow 注释随 F6 改为「逐提交回放」；README 随 F4 降级。**结论：ALIGNED（所列位置）。** 但见新发现 **N1**（同类问题在其它协议文档仍存在）。

---

## 逐项审查（A1–A8）

### A1: 文档→脚本对齐 — **ALIGNED**

A1-1（F1）、A1-2（F2）、A1-3（F3）、A1-4（F4）、A1-5（F5）已闭合；A1-6（push `before` 全零）也已补：`agate-ci-verify.py:337-342` 全零时回退 `merge-base HEAD origin/<默认分支>`，用例 `test_push_all_zero_before_does_not_fail` 通过。**全部 ALIGNED。**

### A2: 脚本→文档对齐 — **ALIGNED（附 N1）**

F4/F7 所列位置已与实现一致（见上）。残留：N1（`platform-notes.md` 等仍称「重跑 `check-gate.py` 判定」）——属同类「声称与实现不符」，但不在原评审枚举内，列为新发现。

### A3: 一致性连锁 + 反向传播 — **ALIGNED（附 N1）**

- 连锁：RM-AG0101 已落地（F3）；workflow / UPGRADING / state-machine 已同步（F6）。
- 反向传播：`agate/scripts/README.md`、`agate/tests/README.md` 已同步 ✓。
- 残留（新发现 N1）：A2 的行为变更**未传播到** `agate/platform-notes.md:342-344`（具体、可证伪）、`agate/phase-cards/P3-tdd.md:28`、`agate/assets/templates/retrospective-template.md:144`、`agate/state-machine.md:154`。

### A4: 测试覆盖 — **仍 MISALIGNED**

**实跑输出**（本复评执行，`--basetemp=/tmp/opencode/...`）：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_ci_replay.py \
    agate/tests/integration/test_tag0050_state_set.py \
    agate/tests/unit/test_tag0050_obligations.py \
    agate/tests/unit/test_tag0050_obligations_enforcement.py \
    agate/tests/unit/test_check_state_transition.py -q
141 passed in 19.92s

$ python3 -m pytest agate/tests/integration/test_pre_commit_hook.py \
    agate/tests/unit/test_agate_ci_verify.py \
    agate/tests/unit/test_tag0027_b1_agate_next_cli.py \
    agate/tests/unit/test_dispatch_context_warning.py \
    agate/tests/integration/test_tag0050_a0_a1_ledger.py -q
115 passed in 47.02s

$ python3 -m pytest agate/tests/unit/test_agate_state_yaml_check.py \
    agate/tests/unit/test_check_state_yaml.py -q
12 passed in 0.74s
```

- **A4-1 / A4-2 已闭合** ✓：真实 commit 读**已提交**账本（`test_gate_run_and_state_transition_committed_with_real_commit`）。
- **A4-4 部分闭合**：push 全零（`test_push_all_zero_before_does_not_fail`）、§8-12（`test_bdd_26b_...`）已补；分支①未实现（F4 降级，无可测对象）；**squash 账本检查仍无用例**。
- **A4-3 未闭合（仍 MISALIGNED）**：`test_bdd_42_negative_control_mutation`（`test_tag0050_obligations.py:70-77`）**仅读 `obligations.yaml` 文本**断言 `test:`/`enforced_at` 存在——**删脚本判据分支不会转红**，与 BDD-42「删掉判据分支 → test 转红」不符。`P4-implementation-G1.md:72` 自认「未做逐条判据分支 mutation」，**且任务无 `P7-consistency.md`**（`ls` 确认不存在）⇒ 按角色原则 6，DESIGN_GAP 无 `REVIEWED-ACCEPTED` 时计 MISALIGNED。
- **A4-5 未闭合（仍 MISALIGNED）**：`test_bdd_43_r_without_review_output_errors`（`:80-85`）**仅断言文本含 `review_output`**，不断言「缺则 ERROR」（实现已降为 WARNING，见 `P4-implementation-G1.md:72` 的 DESIGN_GAP，同样无 P7 `REVIEWED-ACCEPTED`）。

**结论：MISALIGNED**（A4-3 / A4-5）。**建议**：① 补 BDD-42 真变异（如测试内 `monkeypatch` 掉 `_check_enforced_at`/改写 obligations 判据分支后断言 `test` 转红），或走 P7 `REVIEWED-ACCEPTED`；② BDD-43 明确其终态（接受 WARNING 降级并留 P7 `REVIEWED-ACCEPTED` / `[HUMAN_CONFIRMED]`）。

### A5: 下游影响 + 文档传播 — **ALIGNED**

- workflow（`fetch-depth: 0` + `--base`）、UPGRADING（新增 A2/A3 节）已同步 ✓。
- CHANGELOG：A2/A3/A4 条目按团队约定留 P8（`P4-implementation-G1.md:99` 显式留痕）——属显式延期，登记非 MISALIGNED ✓。
- §8 兼容承诺：本次整改改动面均在 §8 允许面（第 7/8/10 项 + A3 status）内；未发现越界改动。

### A6: 锚点表覆盖 — **ALIGNED**

`python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR / 411 WARNING**（411 为冻结扫描面，含本复评的 progress 文件；与基线一致）。`check-platform-assumptions.py` 对改动脚本 **0 命中**（无新平台假设）。

### A7: 设计原则一致性 — **NEEDS_HUMAN_REVIEW**（未变）

G1 引入的两项架构决策（CI 回放可信锚点 / phase 唯一写入口）是否补 ADR，仍待人工裁决（原评审 A7 结论保留）。

### A8: 声称-命令绑定 — **ALIGNED**

| 声称 | 产出命令 | 结论 |
|---|---|---|
| `check-obligations.py` rc=0 | `python3 agate/scripts/check-obligations.py` | 复核通过（EXIT=0） |
| G1 验收测试全绿 | `pytest ... -q`（上列三条） | 复核通过（141/115/12 passed） |
| `gate_run` 随本次提交入库 | `/tmp/opencode` 副本真实 commit + `git show HEAD:...gate-events.jsonl` | 复核通过（含 `gate_run`） |
| consistency 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | 复核通过（0 ERROR） |

---

## 新引入问题

### N1（MISALIGNED-class）— A2 反向传播遗漏：多个协议文档仍称「重跑 `check-gate.py` 判定」

A2 已把 `agate-ci-verify.py` 从「重跑当前 phase gate」改为「逐提交回放本地 hook」，但下列**协议文档（SELF-GATE 触发面 `agate/**/*.md`）仍描述旧行为**，与实现不符：

| 位置 | 原文 | 与实现不符点 |
|---|---|---|
| `agate/platform-notes.md:342` | 「在任何环境直接调用都会**实际重跑** `check-gate.py` 判定」 | 现为逐提交回放 hook（经 `pre-commit-gate.py` 间接跑 gate） |
| `agate/platform-notes.md:344` | 「`agate-ci-verify.py`（无参数，cwd = 项目根；它**实际重跑** `scripts/check-gate.py` 判定）」 | 无参数现按 `merge-base HEAD origin/<默认分支>` 逐提交回放 |
| `agate/phase-cards/P3-tdd.md:28` | 「CI 兜底（`agate-ci-verify.py`）**重跑 gate 判定**」 | 同上 |
| `agate/assets/templates/retrospective-template.md:144` | 「CI 兜底 \| push 后**重跑 gate 判定** \| `agate-ci-verify.py`」 | 同上 |
| `agate/state-machine.md:154` | 「CI 由 `agate-ci-verify` **兜底重跑**」 | 同上（语义弱化，低危） |

**可复现证据**：
```
$ grep -rn "实际重跑\|重跑 gate 判定\|兜底重跑" agate/platform-notes.md agate/phase-cards/P3-tdd.md \
    agate/assets/templates/retrospective-template.md agate/state-machine.md
agate/platform-notes.md:342:…都会**实际重跑** `check-gate.py` 判定…
agate/platform-notes.md:344:…它实际重跑 `scripts/check-gate.py` 判定…
agate/phase-cards/P3-tdd.md:28:…CI 兜底（`agate-ci-verify.py`）重跑 gate 判定…
agate/assets/templates/retrospective-template.md:144:| CI 兜底 | push 后重跑 gate 判定 … | agate-ci-verify.py |
agate/state-machine.md:154:…CI 由 agate-ci-verify 兜底重跑…
```
**建议**：把 `platform-notes.md:342-344` 改为「逐提交回放本地 hook」；`P3-tdd.md:28`、`retrospective-template.md:144`、`state-machine.md:154` 同步措辞。**注**：这是复评**新发现**，非 F1–F7 未闭合项（原评审未枚举这些位置）；但因其为 `agate/**/*.md`（SELF-GATE 触发面）且声称可证伪，按 A2/A3 语义应判 MISALIGNED。

### N2（minor）— `_strip_agate_card_blocks` 边界处理

`check-state-transition.py:75-84`：仅当 `not in_card` 时识别 START 行；若 `AGATE_CARD_START` 与 `END` 同行，或 START 无配对 END，则**其后全部内容被剔除**（整文件）。当前卡片块格式规范（两行成对）下不触发；建议加"无 END 时不剔除"兜底。**低危，不阻断。**

### N3（minor）— 测试文件头部注释陈旧

`agate/tests/unit/test_agate_ci_verify.py:5` 与 `:88` 仍写「**实际重跑** gate 判定」（TAG0042 批 5 的历史红测规格文本）；同文件用例 docstring/断言已更新为「逐提交回放」。属测试文件注释陈旧，非协议文档。**低危。**

---

## NEEDS_HUMAN_REVIEW 汇总（未确认者等同 MISALIGNED）

- **A7**：是否补 ADR（CI 回放可信锚点 / phase 唯一写入口）。
- **A4-3 / A4-5**：BDD-42 真变异、BDD-43 终态（review_output 缺失判 WARNING）——任务无 P7 `REVIEWED-ACCEPTED`，需人工确认或补记录。

---

## 闭环建议

1. **A4-3 / A4-5**：补 BDD-42 真变异用例，或为两处 DESIGN_GAP 走 P7 `REVIEWED-ACCEPTED` / 补 `[HUMAN_CONFIRMED: 日期 确认：理由]`。
2. **N1**：同步 `platform-notes.md` 等 4 处协议文档措辞（SELF-GATE 触发面，须与实现一致）。
3. **N2 / N3**：低危，建议一并修（非阻断）。
4. F1–F6 与 F7 所列位置已闭合，**无需重审**；上述 1–2 完成后可 commit。
