# P5 真机验证清单执行结果（TAG0033）

> verifier subagent 产出。本机：codex-cli **0.153.4** + ChatGPT 登录。
> 每项：命令 / 实际观察 / 通过判据二值结论。所有 codex/bash 命令均加 `timeout`。
> `[PROD_NOT_TOUCHED]` —— codex exec 仅跑无害命令（`ls /nonexistent-xyz-p5r3` 等），不写任何生产路径；
> 仅只读 `~/.codex/sessions/` + 现场派 1 个 Codex 会话生成测试用 rollout。适配器模块以 `importlib`
> 从 worktree `agate/scripts/agate-cmdstream-adapters.py` 加载，未改代码逻辑。

## 结论速览（第 3 轮 —— F1 修复（DEBT0035）后重新验证）

| 项 | 阶段 | 第 3 轮结论 | 是否需回 P4 |
|---|---|---|---|
| **V1**（rollout 解析 —— F1 改了 pending 判据） | P5 | **PASS**——真机 `status="failed"` 携 `exit_code`+`completed_at_ms` 的命令 → `exit` 非 0 数字 / `exit_signal="exit_code=N"` / `ts_end` 非 None / `output_hash` 非 None（**不再 pending 空壳**）；真·未结束命令仍 pending（`test_bdd_6` 覆盖） | 否 |
| **V6 ③**（detect 对真机重复失败会话判 SPIN） | P5（新证据） | **PASS**——`codex exec` 连跑 8 次 `ls /nonexistent-xyz-p5r3` → detect `--platform codex --now ts_start+5s` → **`VERDICT: SPIN`**（pre-fix FROZEN/NORMAL）；正常会话 → `NORMAL` | 否 |
| **V3**（子会话枚举） | P5（回归） | **PASS** | 否 |
| **V4**（截断形态确认） | P5（回归） | **PASS**——fixture 截断样例 → `_detect_truncated`=True / `output_hash`=None | 否 |
| **V5**（`multi_agent` feature flag） | P5（回归） | **PASS**——`multi_agent` = stable / true | 否 |
| V2 / V7 | P6 | 延后（P6 首轮已做，结论在 `.archived/p6-pre-retreat-20260909/real-machine-p6.md`，P6 重做时复核） | — |
| V8 | 待环境 | 待补（非阻塞，`verification_env_budget` 轮次 0/2；本机 ChatGPT 账号，API-key 环境本质不可得） | — |

**无真回归。无 `[PROD_TOUCHED]`。**

---

## V1 — rollout JSONL 解析复核（关键，因 F1 改了 pending 判据）  →  **PASS**

### 造 / 选真实 rollout

选本机 3 个真实 rollout（含**含失败命令的**）：

| 标签 | 文件 | item 终态 |
|---|---|---|
| spin（P6 pre-retreat 造，仍在） | `~/.codex/sessions/2026/09/09/rollout-2026-09-09T08-15-30-01a08385-105e-71e1-969d-3cb40b86d4db.jsonl` | 7 条 `status="failed"` / `exit_code=2` / 携 `completed_at_ms` |
| frozen aborted（P6 pre-retreat 造，仍在） | `~/.codex/sessions/2026/09/09/rollout-2026-09-09T08-17-24-01a08386-cdb0-7d81-91c0-754d1650aa0e.jsonl` | 1 条 `status="failed"` / `exit_code=137`（SIGINT abort）/ 携 `completed_at_ms` |
| normal | `~/.codex/sessions/2026/09/09/rollout-2026-09-09T08-14-48-01a08384-68d2-7643-86e7-ec12ce1133a5.jsonl` | 5 条 `status="completed"` / `exit_code=0` |

原始行扫描确认：spin 会话 `counts={'completed':0,'failed':7} withexitcode:7`；frozen `failed:1 exit_code=137`。

### 命令

```
python3  # importlib 取 CodexAdapter，对上述 3 个真实 rollout 跑 probe / read_commands / list_sessions
```

### 实际观察（`CodexAdapter().read_commands`）

| rollout | 产出 `CommandRecord`（摘要） |
|---|---|
| spin（`status="failed"` ×7） | 7 条，每条 `exit=2` / `exit_signal="exit_code=2"` / `ts_end=1788912938049…`（非 None）/ `output_hash="34bc59b9…"`（非 None）/ `truncated=False` |
| frozen aborted（`status="failed"` exit137） | 1 条，`exit=137` / `exit_signal="exit_code=137"` / `ts_end=1788913093815`（非 None）/ `output_hash="da39a3ee…"`（非 None） |
| normal（`status="completed"`） | 5 条，全 `exit=0` / `exit_signal="exit_code=0"` / `ts_end` 非 None / `output_hash` 各异非 None |

`probe` 对三者均 `True`；`list_sessions("~/.codex/sessions")` → 40 条，全绝对路径（`all(os.path.isabs)`==True）。

**对比 pre-fix**（`.archived/p6-pre-retreat-20260909/real-machine-v6-detect.log`）：同一 spin / frozen
rollout 在 F1 修复前 `read_commands` 产出全部为 `exit=null` / `exit_signal="pending"` / `output_hash=null`
（`status != "completed"` 误判 pending）。F1 修复后 → 真实 `(exit, output_hash)`。

### 真·未结束命令仍 pending

本机当前无「item_started 无对应 item_completed」的真实 rollout（扫描全部 `~/.codex/sessions/2026/09/**`
无此形态——含 abort 的 `sleep 600` 也落了 `item_completed`/`status=failed`）。真·pending 路径由单测
`test_agate_cmdstream_adapters.py::test_bdd_6_codex_unfinished_command_pending`（fixture `sleep 999`
仅 item_started）+ `_codex_is_finished` 语义覆盖，第 3 轮全量 pytest 绿。

### 通过判据（二值）

- 真机 `status="failed"` 且带 `exit_code`+`completed_at_ms` 的命令 → `exit` 是非 0 数字（非 None）、
  `exit_signal == f"exit_code={n}"`、`ts_end` 非 None、`output_hash` 非 None → **满足**（F1 修复核心）
- `probe` / `list_sessions` 对真实文件仍正常 → 满足
- 真·未结束命令 → `exit is None` / `exit_signal == "pending"`（单测覆盖，pytest 绿）→ 满足

**结论：V1 = PASS。**

---

## V6 ③ — detect 对真机重复失败会话判 SPIN（P5 重新通过的关键新证据）  →  **PASS**

### 造会话

```
timeout 280s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
  <<< "请在 shell 里依次运行完全相同的命令 'ls /nonexistent-xyz-p5r3' 共 8 次（每次都会失败退出码非0，
       这是预期的，不要修改命令、不要尝试修复、不要创建该目录）..."
```

- `codex exec` exit 0。落盘 rollout：
  `~/.codex/sessions/2026/09/09/rollout-2026-09-09T11-51-59-01a0844b-4082-7ec3-add6-3b8db3a5bd98.jsonl`
  （`originator=="codex_exec"`）。
- 8 条 `CommandExecution` `item_completed`，全 `command==["/bin/bash","-lc","ls /nonexistent-xyz-p5r3"]`、
  `exit_code==2`、`status=="failed"`、`aggregated_output` 恒定
  （`ls: cannot access '/nonexistent-xyz-p5r3': No such file or directory\n`）。

### 命令 + 实际观察

```
python3 agate/scripts/agate-cmdstream-detect.py read-commands codex <rollout>
```
→ 8 条 `CommandRecord`，全 `exit=2` / `exit_signal="exit_code=2"` /
   `output_hash="20794873c1cef623db94d5cd2f0e3363592718ee"`（恒定）/ `truncated=false`。

```
python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now 1788925931516   # = 首命令 started_at_ms + 5000
```
→
```
VERDICT: SPIN
  · 空转：同 (命令, exit, 输出哈希) 组合 ("/bin/bash -lc 'ls /nonexistent-xyz-p5r3'", 2,
    '20794873c1cef623db94d5cd2f0e3363592718ee') 在窗口 10 内重复 8 次 ≥ 5 → 疑似逻辑空转，建议核查
DETECT_EXIT: 0
```

### 顺带：正常会话 → NORMAL

```
python3 agate/scripts/agate-cmdstream-detect.py detect \
  ~/.codex/sessions/2026/09/09/rollout-2026-09-09T08-14-48-...jsonl --platform codex --now <最后活动+30s>
```
→ `VERDICT: NORMAL`（· 正常：活动持续推进，无冻结/空转信号）。

### 通过判据（二值）

- 真机重复失败会话 → detect `VERDICT: SPIN`（F1 修复前是 FROZEN/NORMAL——`read_commands` 产出
  pending 空壳，detect 拿不到 `(command, exit, output_hash)` 结果签名）→ **满足**
- 正常会话 → detect `NORMAL` → 满足

**结论：V6 ③ = PASS。这是 P5 重新通过的关键新证据。** DEBT0035 closure「detect 对真机重复失败会话判
SPIN」这条闭合。（V6 卡死/正常/FROZEN 全场景仍留 P6 复做。）

---

## V3 — spawn_agent 子会话独立文件复核为回归  →  **PASS**

用第 1 轮现场派的子会话文件
`~/.codex/sessions/2026/09/09/rollout-2026-09-09T07-29-57-01a0835b-5bec-7f02-8bb5-fc33323dce64.jsonl`：

- `session_meta.payload`：`thread_source=="subagent"` / `parent_thread_id=="01a0835b-45e3-74e1-a56a-dc7edefa561f"`（父）/
  `id=="01a0835b-5bec-7f02-8bb5-fc33323dce64"`（子自身）。
- `CodexAdapter().list_sessions("~/.codex/sessions")` → **枚举到该子文件**（`any(x.endswith(child))`==True）。
- `CodexAdapter().read_commands(<子文件>)` → 1 条 `CommandRecord`：`session_id` == 子文件 basename
  （含子自身 uuid `5bec`，**不是**父 id）；`command` 含 `echo v3check`。

**结论：V3 = PASS。**（子会话枚举与 F1 pending 判据无关，回归复核通过。）

---

## V4 — Codex 输出截断标记形态确认  →  **PASS**

`CodexAdapter._detect_truncated` 对 fixture `agate/tests/fixtures/cmdstream/codex-session.jsonl`
现有截断样例行（`cat big.log` 事件，`formatted_output` 含 `…N tokens truncated…` —— 命中
`_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"`）：

- `read_commands(fixture)` → 该记录 `truncated is True` 且 `output_hash is None`。
- 定向 pytest：`test_bdd_7_codex_truncated_output_hash_none` PASS；两个 cmdstream 测试文件 `-k truncat`
  → **5 passed**。

**结论：V4 = PASS。**（第 1 轮已做 fixture 数据收敛，本轮仅确认形态仍命中；F1 修复未触碰截断路径。）

---

## V5 — `multi_agent` feature flag 复核为回归  →  **PASS**

```
timeout 60s codex features list | grep -iE 'multi_agent|collab'
```
→
```
collaboration_modes                      removed            true
multi_agent                              stable             true
multi_agent_mode                         removed            false
multi_agent_v2                           stable             false
```

- `multi_agent` = **stable / true** → 满足（与 P1 §4.4 / platform-notes.md 一致）。
- 历史名 `collaboration_modes` / `multi_agent_mode` = `removed` → 与记录一致。

**结论：V5 = PASS。**

---

## 延后 / 待补项

### V2 — spawn_agent schema 键并集穷尽  →  延后 P6

跨真实 `spawn_agent` 调用归纳 `function_call.arguments` 键并集的深度工作归 P6（配合 V7 嵌套深度）。
P6 首轮已做（键并集无新键），结论在 `.archived/p6-pre-retreat-20260909/real-machine-p6.md`，P6 重做复核。

### V7 — spawn_agent 嵌套深度  →  延后 P6

P6 首轮已做（嵌套 depth 1→2 生效），结论在 `.archived/p6-pre-retreat-20260909/real-machine-p6.md`。

### V6 全场景（卡死 / 正常 / FROZEN）  →  P6

本轮只做 V6 ③（SPIN，F1 修复直接相关的 P5 新证据）。V6 的 frozen/normal/活动冻结全场景 P6 执行。

### V8 — API-key 账号 model 阵容  →  待环境（非阻塞）

本机 ChatGPT 账号，API-key 账号环境本质不可得。`verification_env_budget` 止损轮次 2；当前轮次 0
（未尝试——环境本质不可得，非可重试类失败）。不阻塞 P1-P8 推进。

---

## 历史说明段（第 1 轮 —— F1 修复前）

> 第 1 轮（`c00f97f` 之前）V1-V5 真机验证全 PASS，V4 命中并做 fixture 数据收敛。
> 但第 1 轮 V1 未取样 `status=="failed"` 终态（P1 §4.1 spike 局限）——P6 真机 V6 后续发现
> 真机 Codex 把已结束但非 0 退出的命令记为 `item.status=="failed"`（携完整 `exit_code`+`completed_at_ms`），
> 原 pending 判据 `status != "completed"` 误判其为 pending → **F1 / DEBT0035** → 回退 P5→P4 修复。
> 第 1 轮 V1-V5 结论详见 git 历史；当前结论以上方第 3 轮为准。
> 第 2 轮（`90e00db` 后）real-machine.md 未复跑（该批只改文档）。

---

## 汇总

| 项 | 阶段 | 第 3 轮结论 | 是否需回 P4 |
|---|---|---|---|
| V1 | P5 | PASS（真机 `status="failed"` → exit 非 None，不再 pending） | 否 |
| V6 ③ | P5（新证据） | PASS（真机重复失败会话 detect → SPIN；正常 → NORMAL） | 否 |
| V3 | P5 | PASS | 否 |
| V4 | P5 | PASS | 否 |
| V5 | P5 | PASS | 否 |
| V2 / V7 | P6 | 延后（P6 首轮已做，复核） | — |
| V6 全场景 | P6 | 延后 | — |
| V8 | 待环境 | 待补（非阻塞，budget 轮次 0/2） | — |

`[PROD_NOT_TOUCHED]`

EXIT_CODE: 0
