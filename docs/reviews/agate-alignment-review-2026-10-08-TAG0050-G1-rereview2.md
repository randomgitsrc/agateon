---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 G1 SELF-GATE 聚焦复评（第 2 轮）——只核 H1(A4-3 真变异)/H2(A4-5 终态断言)/H3(N1 文档同步) 是否闭合 + 是否引入新问题
files_changed: [agate/tests/unit/test_tag0050_obligations.py, agate/scripts/check-obligations.py, agate/platform-notes.md, agate/phase-cards/P3-tdd.md, agate/assets/templates/retrospective-template.md, agate/state-machine.md, agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G1.md]
---

# 协议-脚本对齐审查（聚焦复评 · 第 2 轮）— TAG0050 G1

> 模式：SELF-GATE **Layer 1 · 聚焦复评**。对象 = 上一轮复评 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1-rereview.md` 仍判 MISALIGNED 的 **A4-3 / A4-5** 与 **N1**，经 `P4-dispatch-context-implementer-G1-fix2.md`（H1–H3）整改后是否闭合。
> **只核 H1–H3 + 新引入问题，不重开全量**（A1/A2/A3/A5 上轮已判 ALIGNED，本轮不重审）。
> HEAD `b0a16c3a`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0），G1 改动**未提交**。
> 只读纪律：全程未写被评审文件；H1 真变异在 `/tmp/opencode/scratch0050` 一次性副本内做（创建→变异→跑→清理同一流程），pytest 用 `--basetemp=/tmp/opencode/...`；复评前后 `git status --porcelain` 一致（43 项，无 `__pycache__`/`.pytest_cache` 新增）。`[PROD_NOT_TOUCHED]`。

## 复评结论汇总

| # | 原问题 | 复评结论 | 证据（可复现） |
|---|--------|----------|----------------|
| **H1** | A4-3 `test_bdd_42_negative_control_mutation` 只读文本、删判据不转红 | **ALIGNED** | 见下 H1：真变异（数据+脚本两向）均打红 |
| **H2** | A4-5 `test_bdd_43_r_without_review_output_errors` 未断言终态 | **ALIGNED** | 见下 H2：断言与 `check-obligations.py` 实际行为逐条一致 |
| **H3** | N1 4 处协议文档仍称「重跑 `check-gate.py` 判定」 | **ALIGNED** | 见下 H3：4 处均已同步为「逐提交回放」 |

> **一句话**：H1–H3 **全部闭合**，未发现整改引入的新问题（平台假设 0 命中、consistency 0 ERROR）；A4 由上轮 MISALIGNED 转为 ALIGNED。仅剩两处**非本批范围**的低危措辞观察（N4，pre-existing，不阻断）。

---

## H1（A4-3）— 真变异用例能否被打红 — **ALIGNED**

**整改后实现**（`agate/tests/unit/test_tag0050_obligations.py:101-140`）：

- `_copy_protocol_root`（`:31-47`）在 `tmp_path` 下构造最小协议根（`tmp_path/agate/{rules/obligations.yaml, scripts/, tests/unit/…}`）；
- `_run_check_obligations`（`:50-56`）以 `AGATE_ROOT=<副本>` **端到端跑** `check-obligations.py`；
- 用例正文（`:111-140`）：基线 rc=0 → 删 `OBL-P8-02` 的 `enforced_at`（`:123-127`）→ 断言 rc≠0 且输出含 `OBL-P8-02`+`enforced_at`（`:130-133`）→ 恢复 → 断言 rc=0（`:136-140`）。

**证据 1 — 用例本体真跑（基线绿）**：
```
$ python3 -m pytest agate/tests/unit/test_tag0050_obligations.py -q
5 passed in 1.15s
```

**证据 2 — 删脚本判据分支 → 本用例真转红**（在 `/tmp/opencode/scratch0050` 副本上删掉 `check-obligations.py` 的 `_check_enforced_at(item, oid, reachable, errors)` 调用）：
```
$ python3 -m pytest agate/tests/unit/test_tag0050_obligations.py::test_bdd_42_negative_control_mutation -q
FAILED agate/tests/unit/test_tag0050_obligations.py::test_bdd_42_negative_control_mutation
E  AssertionError: BDD-42：删判据后须转红，实际 rc=0
E  assert 0 != 0
1 failed
```
⇒ 删掉判据分支后，变异数据不再被检出 ⇒ 用例在 `:130` 断言处转红。**这正是原 MISALIGNED 所指「删判据分支不转红」的修复点**：现在删判据分支会真正使本用例失败。

**证据 3 — 变异对象有效**（`OBL-P8-02` 为在比 M 项，带 `enforced_at`）：
```
{'id': 'OBL-P8-02', 'disposition': 'M', 'scope': None,
 'enforced_at': {'file': 'agate/scripts/check-gate.py', 'function': 'main'},
 'test': '...test_obligation_enforced[OBL-P8-02]'}
```
`scope` 为 `None` ⇒ 属 in-ratio（走 `_check_enforced_at`/`_check_test_node` 核验），删其 `enforced_at` 会触发 `:188` 的 ERROR 分支 ⇒ 转红成立。

**结论**：**ALIGNED**。用例已是「真变异」（端到端跑脚本 + 断言 rc 翻转），且对**脚本判据分支的删除**敏感。

---

## H2（A4-5）— 终态断言与实现一致 — **ALIGNED**

**实现行为**（`agate/scripts/check-obligations.py`）：
- `_evaluate` 对 R 义务：`if not item.get("review_output"): warnings.append(...)`（`:289-291`，**入 warnings 不入 errors**）；
- `main`：warnings 打印为 `CHECK-OBLIGATIONS: WARNING …`（`:348-349`），`errors` 为空 → `return 0`（`:370-377`）；
- `_check_review_output`（`:225-233`）：`review_output` 存在但非 `P1/P2/P4-review.md` → **ERROR**。

**用例断言**（`test_tag0050_obligations.py:143-187`）：缺 `review_output` → `ok=True and not errors` + warnings 含 `review_output`（`:163-167`）；合格 → 无告警无 ERROR（`:170-172`）；非法 → ERROR（`:175-177`）；真实 `obligations.yaml` 端到端 rc=0（`:180-187`）。

**证据（实跑，三者一致）**：
```
$ python3 agate/scripts/check-obligations.py
CHECK-OBLIGATIONS: WARNING OBL-P0-01: R 义务缺 review_output——找不到合格评审产出的 R 应改标为 C
…（共 25 条 WARNING）
M 类占比: 56/119 = 0.4706（基线 56/119 = 0.4706）
CHECK-OBLIGATIONS: OK（无「无归宿」项 + 无 ERROR + M 类占比不低于基线）
EXIT=0
```
⇒ 实现实际终态 = **缺 → WARNING 且 rc=0**；用例断言与之逐条一致（含非法 → ERROR）。

**DESIGN_GAP 终态已留痕**（`P4-implementation-G1.md:72`）：
> `[DESIGN_GAP: A4 的 review_output 缺失判 WARNING（设计原文为 ERROR）…**终态已被测试锁定**（test_bdd_43…：缺 → WARNING 且 rc=0；合格 → 无告警；非法 → ERROR）…]`

**结论**：**ALIGNED**。断言与 `check-obligations.py` 实际行为一致，DESIGN_GAP 终态已由测试锁定并在 P4-implementation 登记。

---

## H3（N1）— 4 处协议文档同步 — **ALIGNED**

**逐处复核**（`grep` + `sed` 实读）：

| 位置 | 复核结果 | 现状原文（节选） |
|---|---|---|
| `agate/platform-notes.md:342` | 已同步 | 「…在任何环境直接调用都会**逐提交回放** pre-commit 与 commit-msg hook（`pre-commit-gate.py` / `commit-msg-self-gate.py`）判定」 |
| `agate/platform-notes.md:344` | 已同步 | 「…它按 `merge-base HEAD origin/<默认分支>` **逐提交回放**本地 hook 判定」 |
| `agate/phase-cards/P3-tdd.md:28` | 已同步 | 「CI 兜底（`agate-ci-verify.py`）逐提交回放 pre-commit 与 commit-msg hook 判定…」 |
| `agate/assets/templates/retrospective-template.md:144` | 已同步 | 「\| CI 兜底 \| push 后逐提交回放 pre-commit + commit-msg hook 判定… \|」 |
| `agate/state-machine.md:154` | 已同步 | 「…CI 由 agate-ci-verify 兜底逐提交回放 pre-commit + commit-msg hook…」 |

**与实现一致**（`agate/scripts/agate-ci-verify.py:1-16`）：docstring 明确「不再『重跑当前 phase 的 gate』，改为逐提交回放本地 hook（`pre-commit-gate.py` + `commit-msg-self-gate.py`）」；`_replay_commit`（`:200-236`）依次跑 `pre-commit-gate.py` + `commit-msg-self-gate.py`。⇒ 文档新口径与脚本实现语义一致。

**旧口径残留扫描**（`grep -rn "重跑 gate|实际重跑|重跑当前 phase|兜底重跑" agate/ --include=*.md`）：4 处目标位置**零残留**；其余命中经逐条判读**均非本类偏差**——
- `agate/UPGRADING.md:288`（描述被删除的旧行为）、`:418`（TAG0042 批 5 的**历史**版本记录「新增 agate-ci-verify…实际重跑 gate 判定」）——历史/被替代行为的记录，非当前声称；
- `agate/WORKFLOW.md:372`（pre-commit 按被暂存产出所属阶段重跑 gate，规则 7，**另一机制**）；
- `agate/phase-cards/P5-verification.md:26`（P5 修复后重跑 `gate_commands.P5`，**另一机制**）。

**结论**：**ALIGNED**。N1 所列 4 处（5 行）均已同步为「逐提交回放」，且与 `agate-ci-verify.py` 实现一致。

---

## 新引入问题

**无阻断级新问题。** 整改仅触碰 H1–H3 目标文件，未发现碰坏其它文件：

- **平台假设**：`python3 agate/scripts/check-platform-assumptions.py agate/tests/unit/test_tag0050_obligations.py` → 0 命中，exit 0（新测试用 `tmp_path` / `python_exe` / `AGATE_ROOT` env，无裸解释器名、无字面临时目录、无软链假设）。
- **一致性**：`python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（412 WARNING，冻结扫描面；与基线同量级）。
- **只读副作用**：复评前后 `git status --porcelain` 一致（43 项），无 `__pycache__`/`.pytest_cache` 新增；H1 变异只在仓外一次性副本执行并已清理。

### N4（minor，pre-existing，**不属 H3 枚举范围**，不阻断）

旧口径同类措辞仍散见于两处**非本批枚举**位置（整改前即存在，非本次引入）：

| 位置 | 原文 | 判读 |
|---|---|---|
| `agate/tests/README.md:128` | 「`gate-backstop` job：push 后**重跑 gate** + P6 git blame 单 author WARNING」 | 对 `gate-backstop` job 的粗粒度描述；现经 `agate-ci-verify` 逐提交回放 hook（内含 gate）——语义近似，措辞可再精确 |
| `agate/loop-orchestration.md:255` | 「push → CI backstop **重跑 gate**（捕获 `--no-verify` 绕过）」 | 同上，粗粒度；核心（捕获 `--no-verify`）正确 |

**建议**：可在后续批次顺带把「重跑 gate」改为「逐提交回放 hook」。**低危，不阻断本批**（既非 H1–H3 目标，也未新增偏差）。

### 上轮遗留（N2 / N3，低危，不阻断）

上轮复评登记的 N2（`_strip_agate_card_blocks` 边界）、N3（`test_agate_ci_verify.py:5/88` 历史注释陈旧）**未被本批整改触及**，维持原判（低危、非阻断）。本轮不重开。

---

## 闭环建议

1. **H1 / H2 / H3 全部闭合**，A4 由 MISALIGNED → **ALIGNED**。上轮 F1–F7 已闭合，本轮三项亦闭合 ⇒ 就 H1–H3 而言**可 commit**。
2. A7（是否补 ADR）仍为上轮遗留的 **NEEDS_HUMAN_REVIEW**，与本轮三项无关；如尚未附 `[HUMAN_CONFIRMED: …]`，按角色闭环规则仍等同 MISALIGNED，须在 commit 前处理（**注**：该结论属上轮范围，本轮不重判）。
3. **N4 / N2 / N3** 低危，建议后续批次顺带处理，不阻断本批。

---

## 人工验收清单自检

- [x] Write 前已检查目标路径：`docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1-rereview2.md` 为本次（同任务同日复核轮）新文件，无同名冲突
- [x] 每项（H1/H2/H3）有结论 + 可复现证据
- [x] 无 MISALIGNED 项（H1–H3 全 ALIGNED）
- [x] 留痕文件独立（`-rereview2-01.progress.md`），成果文件为本文件
- [x] 结论落盘至 `docs/reviews/agate-alignment-review-{date}-{task_id}-rereview2.md`
