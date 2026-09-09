# P5 技术验证 — gate_commands.P5 逐条实跑结果（TAG0033）

> verifier subagent 产出。工作目录：`.worktrees/agate-TAG0033`。
> 系统 `python3` 3.12.3 / pytest 9.0.3；ruff `~/.venvs/agate-dev/bin/ruff`。
> `[PROD_NOT_TOUCHED]`
> **本轮为第 2 轮复跑（`protocol-docs` 批 commit `90e00db` 之后），gate_commands.P5 全绿。**

## 结论速览（第 2 轮复跑 —— protocol-docs 批 `90e00db` 后）

| gate 命令 | 实跑结果 | 判定 |
|---|---|---|
| `P5`（全量 unit pytest） | **1389 passed, 0 failed, 2 skipped** in 117.86s | PASS（原 6 条 by-design 红 BDD-22~27 已由 protocol-docs 批转绿） |
| `P5_consistency` | exit 0 / **0 ERROR** / 329 WARNING | PASS |
| `P5_shellcheck` | exit 0 / **0 issue** | PASS |
| ruff（AGENTS.md 合并强制，顺手） | exit 0 / All checks passed | PASS |

**无真回归。无 `[PROD_TOUCHED]`。gate_commands.P5 四命令全绿。**

---

## 1. `P5`: `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no`

### 第 2 轮复跑结果（protocol-docs 批 `90e00db` 后 —— 当前结论）

```
1389 passed, 2 skipped in 117.86s
EXIT_CODE: 0
```

- **passed = 1389**
- **failed = 0**
- **skipped = 2**

原第 1 轮的 6 条 by-design 红（`agate/tests/unit/test_codex_platform_docs.py::test_bdd_22` ~
`test_bdd_27`）已**全部转绿**。`protocol-docs` 批（commit `90e00db`）补齐了：

- `platform-notes.md` 的 Codex 章（capability matrix / version & account / spawn_agent schema
  证据等级 `[自述]` 标注 / cross-reference 无矛盾 / model lineup）
- `SETUP.md` 的 Codex 小节

定向复跑确认：`pytest agate/tests/unit/test_codex_platform_docs.py -q` → **8 passed in 0.03s / exit 0**。

回归判据核对：

- failed 是否 > 0？ **否**（0 failed）。
- passed 是否较基线减少？ **否**（1383 → 1389，+6 即原 6 条 doc-audit 转绿）。
- skipped 数目与第 1 轮一致（2），非本任务相关。
- → **无回归**。alignment-review-r2 独立复跑（1389 passed / 0 failed / 2 skipped）逐字一致。

### gate-events.jsonl 台账污染处理（第 2 轮）

跑完全量 pytest 后，`git status --short agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl`
**无输出**、`git diff --stat` 空 —— 本轮该文件**未被测试追加**，无需还原。工作区对该文件 clean。
（第 1 轮曾被追加 2 行并 `git checkout --` 还原，见下方历史说明段。）

---

## 历史说明段（第 1 轮过程记录 —— protocol-docs 批之前）

> 以下为 P5 第 1 轮验证（`protocol-docs` 批 commit `90e00db` **之前**）的结论，作为过程记录保留。
> 当前结论以上方「结论速览（第 2 轮复跑）」与第 1 节第 2 轮复跑结果为准。

第 1 轮全量 unit pytest：**1383 passed / 6 failed / 2 skipped** in 111.88s（exit 0）。

6 条 failed **全部**是 `agate/tests/unit/test_codex_platform_docs.py` 的 `test_bdd_22` ~ `test_bdd_27`：

1. `test_bdd_22_codex_chapter_capability_matrix`
2. `test_bdd_23_codex_chapter_version_and_account`
3. `test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade`
4. `test_bdd_25_codex_chapter_cross_reference_no_contradiction`
5. `test_bdd_26_codex_chapter_model_lineup`
6. `test_bdd_27_setup_md_codex_section`

**当时的标注（by-design 待实现）**：`protocol-docs` 批（P2-design.md §11 dispatch_plan
`static-batch` 两批的第 2 批）待实现 —— `platform-notes.md` Codex 章仍为「待补充」占位、
`SETUP.md` 无 Codex 小节、`spawn_agent` schema 段未标 `[自述]`。P3 写红、`test_codex_platform_docs.py`
文件头注释已声明「BDD-22~27 red until protocol-docs 批」。非预存失败、非回归、非真 bug，
**未写入 `known-failures.md`**。

**第 2 轮结果**：`protocol-docs` 批（commit `90e00db`）落地后，这 6 条已如设计预期**全部转绿**，
第 1 轮的 by-design 红项闭合。

---

## 2. `P5_consistency`: `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`

（⚠️ worktree 自己的脚本路径，非 `~/.agate`）

第 2 轮实跑输出尾部：

```
  仅有 329 个 WARNING，无 ERROR。
CONSISTENCY_EXIT=0
```

- **exit 0**
- **0 ERROR**
- 329 WARNING —— 全部为历史叙事文件死链（`docs/design-notes/...`、`docs/reviews/agate-alignment-review-*`、
  `CHANGELOG.md` 里引述的已删脚本名等），与本任务无关，`--strict-errors-only` 不判失败。记数即可，不处理。

**判定：PASS**（BDD-20）。第 2 轮与第 1 轮一致（`protocol-docs` 批只改文档，未新增死链 ERROR）。

---

## 3. `P5_shellcheck`: `timeout 60s shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh`

第 2 轮实跑：

```
SHELLCHECK_EXIT=0
```

（无任何 issue 行输出）

- **0 issue**，exit 0。本任务不改 `.sh` — 结构性回归通过。

**判定：PASS**。

---

## 4. ruff（P2 §7 未列，AGENTS.md 合并强制，顺手跑）: `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/`

第 2 轮实跑：

```
All checks passed!
RUFF_EXIT=0
```

**判定：PASS**。

---

## V4 fixture 数据收敛记录（第 1 轮，P5 允许的唯一写，非代码逻辑改动 —— 保留为过程记录）

真机验证 V4 命中（详见 `real-machine.md`）。按第 1 轮 dispatch-context 授权，把实测截断形态补进
`agate/tests/fixtures/cmdstream/codex-session.jsonl` 的截断样例行（`cat big.log` 事件，line 12）：

- 去掉 P2 推测的 `item.output_truncated: true` 布尔字段（真机实测该 item 无此字段）
- `formatted_output` 改为真机实测标记文本：`Warning: truncated output (original token count: 262152)` +
  `…252152 tokens truncated…`（命中现有 `_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"`）
- `aggregated_output` 改为无标记的普通输出（真机该字段不含截断标记）

改动为 fixture **数据**收敛（1 line changed），**未动** `agate/scripts/*.py` 代码逻辑。
本轮（第 2 轮）**未再改动任何 fixture / `.py` / 测试 / 文档**。

---

## real-machine.md 说明

`real-machine.md`（V1-V5 真机验证）为 P5 第 1 轮实测结论，**本轮不动** —— `protocol-docs` 批
（commit `90e00db`）只改文档（`platform-notes.md` / `SETUP.md`），未改 `agate/scripts/*.py`，
V1-V5 结论不变，无需复跑。

---

## N5 签名校验用（test runner 输出签名 —— 第 2 轮复跑）

passed=1389 failed=0 skipped=2
（原 BDD-22~27 已由 protocol-docs 批 `90e00db` 转绿；无 FAILED 行）

EXIT_CODE: 0
