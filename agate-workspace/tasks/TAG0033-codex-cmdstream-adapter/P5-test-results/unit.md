# P5 技术验证 — gate_commands.P5 逐条实跑结果（TAG0033）

> verifier subagent 产出。工作目录：`.worktrees/agate-TAG0033`。
> 系统 `python3` 3.12.3 / pytest；ruff `~/.venvs/agate-dev/bin/ruff`；codex-cli 0.153.4 + ChatGPT 登录。
> `[PROD_NOT_TOUCHED]`
> **本轮为第 3 轮（P5→P4 回退修 F1（DEBT0035）后的重新技术验证）。HEAD = `6f8422f`（P4 重试 #1）。**

## 结论速览（第 3 轮 —— F1 修复后 P5 重新通过）

| gate 命令 | 实跑结果 | 判定 |
|---|---|---|
| `P5`（全量 unit pytest） | **1390 passed, 0 failed, 2 skipped** in 109.74s / exit 0 | PASS（1389 基线 + 1 条 F1 守护 `test_bdd_5_codex_failed_status_not_pending_guard`） |
| `P5_consistency` | exit 0 / **0 ERROR** / 329 WARNING | PASS |
| `P5_shellcheck` | exit 0 / **0 issue** | PASS |
| ruff（AGENTS.md 合并强制，顺手） | exit 0 / All checks passed | PASS |

**F1 修复后 P5 重新通过：1390 passed / 0 failed。无真回归。无 `[PROD_TOUCHED]`。gate_commands.P5 四命令全绿。**

真机侧关键新证据（详见 `real-machine.md`）：
- **V1**：真机 `status="failed"` 且带 `exit_code` + `completed_at_ms` 的命令 → `CommandRecord.exit`
  为非 0 数字（`2` / `137`）、`exit_signal == "exit_code=N"`、`ts_end` 非 None、`output_hash` 非 None
  —— **不再是 pending 空壳**（F1 修复核心）。
- **V6 ③**：真机 `codex exec` 连跑 8 次相同失败命令 `ls /nonexistent-xyz-p5r3` → rollout →
  `agate-cmdstream-detect.py detect --platform codex` → **`VERDICT: SPIN`**（pre-fix 为 FROZEN/NORMAL）。

---

## 1. `P5`: `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no`

### 第 3 轮实跑结果（F1 修复后 —— 当前结论）

```
1390 passed, 2 skipped in 109.74s (0:01:49)
EXIT_CODE: 0
```

- **passed = 1390**
- **failed = 0**
- **skipped = 2**

第 2 轮基线 1389 passed → 第 3 轮 1390 passed，`+1` 即 F1 修复新增的守护用例
`test_agate_cmdstream_adapters.py::test_bdd_5_codex_failed_status_not_pending_guard`
（`agate/tests/unit/test_agate_cmdstream_adapters.py:807`；无新 BDD 编号）。

F1 相关用例定向复跑确认：

- `pytest test_agate_cmdstream_adapters.py -k "bdd_5 or bdd_6 or bdd_7 or truncated"` → **10 passed / exit 0**
  （含 `test_bdd_5_codex_failed_status_not_pending_guard`、`test_bdd_6_codex_unfinished_command_pending`
  真·pending 路径、`test_bdd_7_codex_truncated_output_hash_none`）。
- `pytest ... -k "guard"` → **1 passed**。
- `pytest test_agate_cmdstream_adapters.py test_agate_cmdstream_detect.py -k "truncat"` → **5 passed**。

回归判据核对：

- failed 是否 > 0？ **否**（0 failed）。
- passed 是否较基线减少？ **否**（1389 → 1390，+1 即 F1 守护用例）。
- skipped 数目与前两轮一致（2），非本任务相关。
- → **无回归**。与 P4-review r2 + alignment-review r3 独立复跑（1390 passed / 0 failed / 2 skipped）一致。

### gate-events.jsonl 台账污染处理（第 3 轮）

跑完全量 pytest 后，`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl`
的 sha256 与 pytest 前**逐字节一致**（跑前跑后均 `9b025f61…3955b8c` / 17 行）——本轮该文件
**未被测试追加**，无需还原。

⚠️ 该文件当前对 HEAD 有 **2 行合法未提交改动**（本轮开始时即存在，非本轮产生）：
```
{"cmd":"check-gate.py P4","event":"gate_run","exit":0,"phase":"P4",...,"ts":"2026-09-09T03:45:57..."}
{"event":"state_transition","from":"P4","phase":"P5",...,"to":"P5","ts":"2026-09-09T03:46:55..."}
```
= 主 Agent 手动 `_advance` P4→P5 的台账（`agate-next.py` 因 check-gate P4 多提交阶段局限拒绝推进，
主 Agent 按 `_advance` 逻辑手动补）。**不还原**（dispatch-context 明确说明）。同理 `.state.yaml`
的 `phase: P4 → P5` 也是主 Agent 手动补的，不动。

---

## 历史说明段（第 1 / 第 2 轮过程记录 —— 保留）

### 第 1 轮（`protocol-docs` 批 `90e00db` 之前）

全量 unit pytest：**1383 passed / 6 failed / 2 skipped**（exit 0）。6 条 failed 全部是
`test_codex_platform_docs.py::test_bdd_22` ~ `test_bdd_27`（by-design 待实现，P3 写红，
`protocol-docs` 批待落地）。非预存失败、非回归、非真 bug，未写入 `known-failures.md`。
另做 V4 fixture 数据收敛（`codex-session.jsonl` 截断样例行改为实测形态，1 line，非代码逻辑改动）。

### 第 2 轮（`protocol-docs` 批 `90e00db` 之后）

全量 unit pytest：**1389 passed / 0 failed / 2 skipped** in 117.86s（exit 0）。
第 1 轮 6 条 by-design 红由 `protocol-docs` 批（commit `90e00db`）落地后**全部转绿**。
`P5_consistency` / `P5_shellcheck` / ruff 均绿。real-machine.md 第 2 轮未复跑（该批只改文档）。

### 第 2 轮 → 第 3 轮之间发生的事

`c00f97f`（P5 通过）→ P6 真机 V6 发现 **F1**（DEBT0035：真机 Codex 把已结束但非 0 退出的命令记为
`item.status=="failed"`，携完整 `exit_code`+`completed_at_ms`；原 pending 判据 `status != "completed"`
误判其为 pending，丢真实 `exit_code`+`output_hash` → detect 判不出 SPIN）→ 回退 P5→P4（`52fe210`）→
implementer 重试 #1 修 F1（`6f8422f`：新增 `_codex_is_finished(payload, item)` helper、
fixture 补真机 `status="failed"` 形态 + 重复失败簇、测试调整）→ P4 review r2 + alignment r3 均
approved/PASS。**本轮（第 3 轮）重新做 P5 技术验证**。

---

## 2. `P5_consistency`: `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`

（⚠️ worktree 自己的脚本路径，非 `~/.agate`）

第 3 轮实跑输出尾部：

```
  仅有 329 个 WARNING，无 ERROR。
CONSISTENCY_EXIT: 0
```

- **exit 0**
- **0 ERROR**
- 329 WARNING —— 全部为历史叙事文件死链（`docs/design-notes/...`、`docs/reviews/agate-alignment-review-*`、
  `CHANGELOG.md` 引述的已删脚本名等），与本任务无关，`--strict-errors-only` 不判失败。记数即可。

**判定：PASS**（BDD-20）。与前两轮一致（F1 修复只改 `.py` + fixture + 测试 + `platform-notes.md` 1 bullet，未新增死链）。

---

## 3. `P5_shellcheck`: `timeout 60s shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh`

第 3 轮实跑：

```
SHELLCHECK_EXIT: 0
```

（无任何 issue 行输出）

- **0 issue**，exit 0。本任务不改 `.sh` —— 结构性回归通过。

**判定：PASS**。

---

## 4. ruff（P2 §7 未列，AGENTS.md 合并强制，顺手跑）: `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/`

第 3 轮实跑：

```
All checks passed!
RUFF_EXIT: 0
```

**判定：PASS**。

---

## F1 修改点核对（V1 手跑参照，`agate/scripts/agate-cmdstream-adapters.py`）

`_codex_is_finished(payload, item)`（~line 641）——「有终态信号才算已结束」口径，三者任一：

- `item.status` ∈ `{"completed", "failed"}`
- `item.exit_code` 是 `int` 且非 `bool`
- `payload.completed_at_ms` 非 None

`read_commands`（~line 766）：`pending = not _codex_is_finished(payload, item)`（旧口径为
`pending = status != "completed"`）。P5 未改任何 `agate/scripts/*.py` 代码逻辑。

---

## N5 签名校验用（test runner 输出签名 —— 第 3 轮）

passed=1390 failed=0 skipped=2
（1389 基线 + 1 条 F1 守护 test_bdd_5_codex_failed_status_not_pending_guard；无 FAILED 行）

EXIT_CODE: 0
