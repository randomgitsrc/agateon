# P5 真机验证清单执行结果 — V1 / V3 / V4 / V5（TAG0033）

> verifier subagent 产出。本机：codex-cli **0.153.4** + ChatGPT 登录。
> 每项：命令 / 实际观察 / 通过判据二值结论。所有 codex/bash 命令均加 `timeout`。
> `[PROD_NOT_TOUCHED]` —— codex exec 仅跑无害命令（`echo v3check` / `python3 -c "print('x'*2000000)"`），
> 不写任何生产路径；仅只读 `~/.codex/sessions/` + 现场派 2 个 Codex 子会话生成测试用 rollout（V3/V4 清单
> 明确许可的方法）。适配器模块以 `importlib` 从 worktree `agate/scripts/agate-cmdstream-adapters.py` 加载，
> 未改代码逻辑。

---

## V1 — rollout JSONL 格式复核为回归  →  **PASS**

### 命令

```
find ~/.codex/sessions -name 'rollout-*.jsonl' -type f | wc -l           # → 23（执行 V3/V4 前）
python3  # 扫描 4 个真实 rollout 头尾 + CommandExecution item 字段结构
python3  # importlib 取 ADAPTERS["codex"]，对一个真实 rollout 跑 probe / read_commands / list_sessions
```

### 实际观察

**目录结构 / 信封**（读 `~/.codex/sessions/2026/09/{08,09}/rollout-*.jsonl` 头尾）：

- 目录布局 `~/.codex/sessions/YYYY/MM/DD/`；文件名 `rollout-<ISO8601 秒精度>-<uuid>.jsonl`。
- 行信封键恒为 `{ordinal, payload, timestamp, type}`；每文件首行 `type=="session_meta"`。
- `session_meta.payload` 键含 `id` / `session_id` / `thread_source` / `cli_version`(=="0.153.4") /
  `originator`（`codex-tui` 或 `codex_exec`）——与 P1 §4.1 一致。

**`CommandExecution` item 字段**（在含该事件的真实 rollout
`rollout-2026-09-08T19-46-58-...01a080d7...jsonl` 观察）：

- `payload` 键：`{completed_at_ms, item, started_at_ms, thread_id, turn_id, type}`；
  `started_at_ms` / `completed_at_ms` = epoch ms **int**（样例 `1788868081170` / `1788868081171`）。
- `item` 键：`{aggregated_output, command, cwd, duration, exit_code, formatted_output, id,
  parsed_cmd, process_id, source, status, stderr, stdout, type}`。
- `item.command` == `["/bin/bash", "-lc", "sed -n '1,240p' ..."]`（数组）；
  `item.exit_code` == `0`（int）；`item.status` == `"completed"`；
  `item.aggregated_output` 为 str（样本 5442 字符）。

→ 逐项与 P1 §4.1 / P2 §4.2 描述吻合，形态无漂移（回归复核通过）。

**适配器对真实文件跑三方法**（≤15 行 python，`importlib` 从
`agate/scripts/agate-cmdstream-adapters.py` 取 `ADAPTERS["codex"]`）：

| 调用 | 结果 |
|---|---|
| `CodexAdapter().probe(<真实 codex rollout>)` | `True` |
| `CodexAdapter().probe(<真实 Claude Code 转录 ~/.claude/projects/.../06458411-...jsonl>)` | `False` |
| `CodexAdapter().read_commands(<真实 codex rollout>)` | 不抛异常；产出 **1** 条 `CommandRecord`；`platform=="codex"`、`ts_start==1788868081170`（int）、`command` 非空（`/bin/bash -lc 'sed -n ...'`）、`exit==0`、`exit_signal=="exit_code=0"`、`truncated is False`、`output_hash` 非空（`50a4b64f4072...`） |
| `CodexAdapter().list_sessions("~/.codex/sessions")` | 返回 **23** 条，全部绝对路径（`all(os.path.isabs)` == True），非空 list |

### 通过判据（二值）

- `probe` 对真实 Codex rollout 返 True、对真实 Claude Code 转录返 False → 满足
- `read_commands` 不抛异常、≥1 条 `CommandRecord`、字段非空（`platform=="codex"` / `ts_start` 是 int /
  `command` 非空）→ 满足
- `list_sessions` 返回非空绝对路径 list → 满足

**结论：V1 = PASS。** rollout JSONL 格式与解析假设一致，无回归。

---

## V3 — spawn_agent 子会话独立文件复核为回归  →  **PASS**

### 命令

```
# 本机已有 3 个 thread_source=="subagent" 的 rollout，但均 CommandExecution 数=0
#  → 按 V3 清单许可现场派一个：
timeout 200s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
  <<< "用 spawn_agent 派一个子代理，让它在 shell 里运行命令 echo v3check，并把子代理的输出返回给我"
python3  # 找 mtime 最新的子 rollout；核 session_meta；跑 list_sessions / read_commands
```

### 实际观察

- `codex exec` exit 0。`~/.codex/sessions/` 文件数 23 → **25**（父会话 rollout + 子会话 rollout 各 1 个新文件）。
- 新子会话文件：`rollout-2026-09-09T07-29-57-01a0835b-5bec-7f02-8bb5-fc33323dce64.jsonl`
  - `session_meta.payload.thread_source == "subagent"`
  - `session_meta.payload.parent_thread_id == "01a0835b-45e3-74e1-a56a-dc7edefa561f"`（= 父）
  - `session_meta.payload.id == "01a0835b-5bec-..."`（= 子自身）；
    `session_meta.payload.session_id == "01a0835b-45e3-..."`（= 父）
    —— 证实「`session_id` 字段是父的，`id` 字段才是本文件的」（设计点 3 定论 A）。
  - 含 1 条 `event_msg`/`item_completed` `CommandExecution`：`command==["/bin/bash","-lc","echo v3check"]`、
    `exit_code==0`、`status=="completed"`。
- `CodexAdapter().probe(<子文件>)` → `True`
- `CodexAdapter().list_sessions("~/.codex/sessions")` → 25 条，**枚举到该子文件**（`child in ls` == True）
- `CodexAdapter().read_commands(<子文件>)` → 1 条 `CommandRecord`：
  - `session_id == "rollout-2026-09-09T07-29-57-01a0835b-5bec-7f02-8bb5-fc33323dce64.jsonl"`
    （= 子文件 basename，**含子自身 uuid `5bec`**）
  - `parent_thread_id`（`01a0835b-45e3-...`）**不在** `session_id` 内 → 不是父 id
  - `platform=="codex"`、`command` 含 `echo v3check`

### 通过判据（二值）

- 子会话是独立 `rollout-*.jsonl` → 满足
- 其 `session_meta` 含 `thread_source=="subagent"` + `parent_thread_id` → 满足
- `list_sessions()` 枚举到它 → 满足
- `read_commands(<子文件>)` 产出记录的 `session_id` = 子文件 basename（含子自身 uuid，不是父 id）→ 满足

**结论：V3 = PASS。**

---

## V4 — Codex 输出截断标记确切形态（P2 §5 设计点 4 收敛锚）  →  **命中（HIT）**

### 命令

```
timeout 240s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
  <<< "请在 shell 里运行 python3 -c \"print('x'*2000000)\" 并把完整输出贴回来"
python3  # 读落盘 rollout 的 CommandExecution item，逐字段找截断标记；对照 _CODEX_TRUNC_*
```

### 实际观察（截断确切形态）

新落盘 rollout：`rollout-2026-09-09T07-30-39-01a0835b-fe56-7cc2-89de-7ec6a36b94fd.jsonl`
的 `event_msg`/`item_completed` `CommandExecution` item（`command==["/bin/bash","-lc","python3 -c
\"print('x'*2000000)\""]`、`exit_code==0`、`status=="completed"`）：

| item 字段 | 观察 |
|---|---|
| item 上的**布尔截断字段** | **无**。item 键 = `{aggregated_output, command, cwd, duration, exit_code, formatted_output, id, parsed_cmd, process_id, source, status, stderr, stdout, type}` —— 无 `truncated` / `output_truncated` / `is_truncated` 任何布尔字段 |
| `aggregated_output` | str，len 1048606（原始输出被 ~1MB 截断，但**文本内无任何截断标记**，仅 `x` + 尾 `\n`） |
| `stdout` | 同 `aggregated_output`（len 1048606，无标记） |
| `formatted_output` | str，len 40105，**含截断标记**，形态如下 ↓ |

`formatted_output` 的截断标记确切形态（两处）：

1. 开头行：`Warning: truncated output (original token count: 262152)\nTotal output lines: 3\n\n`
2. 中段省略号包夹：`…252152 tokens truncated…`（注意是 U+2026 省略号字符 `…`，不是三个点）

### 对照 `CodexAdapter._detect_truncated` 现有常量

```python
_CODEX_TRUNC_BOOL_KEYS   = ("truncated", "output_truncated", "is_truncated")
_CODEX_TRUNC_TEXT_MARKERS = ("[output truncated]", "output truncated", "tokens truncated", "[truncated]")
```

`_detect_truncated` 对 `aggregated_output` **和** `formatted_output` 两个字段做小写子串匹配。

- `_CODEX_TRUNC_BOOL_KEYS`：真机 item 无布尔字段 → 不命中（但这是"任一信号"设计，不命中不影响结论）
- `_CODEX_TRUNC_TEXT_MARKERS`：真机 `formatted_output` 含 `"…252152 tokens truncated…"` →
  子串 **`"tokens truncated"` 命中** ✓

实跑验证：`CodexAdapter._detect_truncated(<真机 item>)` → **`True`**；
`CodexAdapter().read_commands(<该 rollout>)` → 该记录 `truncated is True` 且 `output_hash is None`。

### 结论

**V4 = PASS（命中）。** 实测截断形态 = `formatted_output` 里的
`Warning: truncated output (original token count: N)` + `…N tokens truncated…`；现有
`_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"` 已覆盖，`_CODEX_TRUNC_*` 常量**无需收敛、无需回 P4**。

**顺手 fixture 数据收敛**（dispatch-context 授权的唯一允许写，非代码逻辑改动）：
把 `agate/tests/fixtures/cmdstream/codex-session.jsonl` 的截断样例行（`cat big.log` 事件）
从 P2 推测形态（`item.output_truncated: true` 布尔 + `aggregated_output` 含 `[output truncated]`）
收敛为实测形态：去掉布尔字段，`formatted_output` 用真机标记文本
（`Warning: truncated output (original token count: 262152)` + `…252152 tokens truncated…`），
`aggregated_output` 改为无标记普通输出。改动 = 1 line（1 insertion / 1 deletion）。

改后重跑确认全绿：`test_bdd_7_codex_truncated_output_hash_none` PASS、
`test_bdd_17_codex_truncated_repeat_not_spin` PASS、`test_bdd_7_fixture_sanitized` PASS、
`test_bdd_9_codex_malformed_lines_no_crash` PASS；两个 cmdstream 测试文件 58 passed；
全量 unit pytest 复跑 1383 passed / 6 failed（同基线）/ 2 skipped —— 无回归。详见 `unit.md`。

---

## V5 — `multi_agent` feature flag 复核为回归  →  **PASS**

### 命令

```
timeout 60s codex features list | grep -iE 'multi_agent|spawn|collab'
```

### 实际观察

```
collaboration_modes                      removed            true
multi_agent                              stable             true
multi_agent_mode                         removed            false
multi_agent_v2                           stable             false
```

（exit 0）

### 通过判据（二值）

- `multi_agent` = **stable / true** → 满足（与 P1 §4.4 / platform-notes.md 版本注记将写的一致）
- 历史名 `collaboration_modes` / `multi_agent_mode` = `removed`（与 P1 §4.4 记录一致）

**结论：V5 = PASS。**

---

## 不做 / 延后项

### V2 — spawn_agent schema 穷尽  →  延后 P6

P1 §4.3 已确认「令模型逐字 dump 内部 tool schema」不可用（模型受训拒绝）。跨真实调用归纳
`function_call.arguments` 键并集的深度工作**归 P6**（配合 V7 嵌套深度）。
方法 = 跨 ≥数次真实 `spawn_agent` 调用归纳 `function_call.arguments` 键并集
（`[自述]` 当前上限：`task_name`(必) / `message`(必) / `fork_turns` / `model` / `reasoning_effort`）。

### V6 / V7  →  归 P6

- V6：检测引擎对真实 Codex 会话（非 fixture）判三态（造真实卡死 / 正常 / 重复失败会话）——P6 执行。
- V7：`spawn_agent` 嵌套深度（`spawn_agent` 内再 `spawn_agent`，观察孙会话文件 +
  `session_meta.source.subagent.thread_spawn.depth`）——P6 执行。
- P5 不做。

### V8 — API-key 账号 model 阵容  →  待有该环境时补（非阻塞）

本机为 ChatGPT 账号，API-key 账号环境**本质不可得**。

- `verification_env_budget`：止损轮次 **2**；**当前轮次 0**（未尝试——环境本质不可得，非可重试类失败，
  不消耗轮次）。
- `platform-notes.md` P7 将在「API-key 账号 model 阵容」一列显式写「本会话未核实、待补」。
- 不阻塞 P1-P8 推进（P0-brief env_constraints / P1 §7 V8 / research §11 #5 一致口径）。

---

## 汇总

| 项 | 阶段 | 结论 | 是否需回 P4 |
|---|---|---|---|
| V1 | P5 | PASS | 否 |
| V3 | P5 | PASS | 否 |
| V4 | P5 | PASS（命中，现有 `_CODEX_TRUNC_*` 已覆盖；fixture 数据收敛已做，BDD 复跑绿） | **否** |
| V5 | P5 | PASS | 否 |
| V2 | P6 | 延后 | — |
| V6 | P6 | 延后 | — |
| V7 | P6 | 延后 | — |
| V8 | 待环境 | 待补（非阻塞，budget 轮次 0/2） | — |

`[PROD_NOT_TOUCHED]`

EXIT_CODE: 0
