# P6 真机验证结论 — V6 / V7 / V2（TAG0033）

> verifier subagent 产出。本机：codex-cli **0.153.4** + ChatGPT 登录，Linux/WSL2，2026-09-09。
> 所有 codex exec 仅跑无害命令（`echo` / `sleep` / `ls` / `date`）。`[PROD_NOT_TOUCHED]`。
> 这些真机项是 BDD-13~17 / BDD-24~25 / BDD-30 的**补充/加强证据**（自动化单测用 fixture 已绿；
> 真机验证证明对真实 Codex 会话也成立或指出偏差）。原始命令输出见同目录
> `real-machine-v6-detect.log` / `real-machine-v7-v2.log`。

---

## V6 — 检测引擎对真实 Codex 会话判三态（BDD-13~17 真机佐证）

方法：`codex exec` 现场造 3 个真实 rollout → 各跑
`python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now <虚拟时刻>`。

| 场景 | 真实 rollout | 造法 | detect 结果 | 与 BDD-13~17 判据 |
|---|---|---|---|---|
| ① 卡死会话 | `rollout-2026-09-09T08-17-24-01a08386-cdb0-*.jsonl` | `codex exec` 派 `sleep 600`，55s 后 SIGINT | `now = ts_start+950s` → **FROZEN**（`调用冻结（suspect）… ≥ 兜底阈值 900s`）；`now=+30s` → NORMAL | ✅ **一致**（① → FROZEN，含「调用冻结」） |
| ② 正常会话 | `rollout-2026-09-09T08-14-48-01a08384-68d2-*.jsonl` | 依次跑 `echo p6n-1/p6n-2/sleep 1/p6n-3/date +%s`（5 条秒级完成，输出各异） | `now = 最后活动+30s` → **NORMAL**；对照 `now=+400s` → FROZEN（活动冻结） | ✅ **一致**（② → NORMAL） |
| ③ 重复失败会话 | `rollout-2026-09-09T08-15-30-01a08385-105e-*.jsonl` | 连跑 7 次完全相同的 `ls /nonexistent-xyz-p6spin`（每次 exit 2、输出恒定） | `now=+5s` → NORMAL；`now=+950s` → **FROZEN（调用冻结）** | ⚠️ **不一致**（判据要求 ③ → SPIN；真机实测得不到 SPIN，见下「重要发现 F1」） |

**判定**：V6 ① / ② 与 BDD 判据一致；③ 部分完成——真机 spin 场景未复现 SPIN，根因是真机 Codex
的 `status:"failed"` 语义未被 `CodexAdapter` pending 判据识别（F1）。BDD-15 的 PASS 依据是单测
（`test_bdd_15_codex_invalid_repeat_spin` 绿，见 `bdd-15.log`），本项为加强证据，按 dispatch
「V6 是加强证据，不阻塞」——**不据此判 BDD FAIL**，但 F1 需报告主 Agent。

### 重要发现 F1（需主 Agent 定夺：回写 platform-notes.md / 是否回 P4）

真机 Codex rollout 把**已完成但非 0 退出**的命令记为 `payload.item.status == "failed"`
（**不是** `"completed"`），且该 item **携带完整** `exit_code`（如 2 / 137）、`aggregated_output`、
`completed_at_ms`。实测样本：

- spin 会话 7 条 `ls …` item：`status="failed"`, `exit_code=2`, `aggregated_output="ls: cannot access …"`, `completed_at_ms` 有值
- frozen(SIGINT) 会话的 `sleep 600` item：`status="failed"`, `exit_code=137`, `completed_at_ms` 有值

`CodexAdapter._build_record` 的 pending 判据是 `pending = item.get("status") != "completed"`
（`agate/scripts/agate-cmdstream-adapters.py:739`）。因此真机 `status="failed"` 的**已结束**命令
被误判为 pending → 映射成 `exit=None` / `ts_end=None` / `exit_signal="pending"` / `output_hash=None`，
**丢掉了真实的 exit_code 与 output_hash**。连锁影响：

1. `detect` 对真机重复失败会话拿不到 `(command, exit, output_hash)` 结果签名 → 判不出 SPIN
   （改判 FROZEN 调用冻结 / NORMAL）。BDD-15 真机侧不成立。
2. 真机失败命令的 `CommandRecord.exit` 恒为 `None`（BDD-5 的 Given 明确限定 `status=="completed"`，
   故单测不覆盖此形态；单测 `bdd-05.log` 仍 PASS）。
3. BDD-6「未结束命令 → pending」在真机会有**假阳性**：真正结束但失败的命令也被标 pending。

P1 §4.1 对 `item.status` 的描述（「`"completed"`；未结束时 `"in_progress"` 或缺 completed 事件」）
**未预见** `"failed"` 这一终态取值——属 P1 spike 取样未覆盖到的真机形态。

**建议**（交主 Agent）：pending 判据改为「无终态信号」口径，例如
`status not in ("completed", "failed")` 且 `completed_at_ms`/`exit_code` 缺失时才算 pending；
并在 `platform-notes.md` Codex 章「命令流适配」小节补一句真机 `status` 取值集
（`completed` / `failed` / `in_progress`）。此为 P4 实现口径问题，P6 不改代码。

### post-test 环境残留检查（V6/V7/V2 共用）

- 测试派生的 `~/.codex/sessions/2026/09/09/rollout-*.jsonl`（V6 的 3 个 + V7 的 3 个 + V2 的
  ~6 个子/孙会话）为 **Codex 正常行为产物、只读观察对象**，非 agate 生产环境
  （`~/.agate` / 项目 git）残留。
- `~/.agate` 最近 25 分钟内**无任何文件改动**（`find ~/.agate -newermt '25 minutes ago'` 空）。
- worktree `git status --short`：仅 P6 产出（`P6-evidence/`、`P6-progress.md`、
  `P6-dispatch-*.md`）+ `gate-events.jsonl`（**1 处既有未提交改动**：3 行 P4→P5 state_transition /
  gate_run 台账，时间戳 `2026-09-09T00:05`，会话开始前即为 ` M` 状态，非 P6 验证产物）。
- `git status --short -- agate/`：**完全干净**，无任何代码 / 文档 / 测试 / fixture 改动。
- 残留 codex / `sleep 600` 进程：**无**（`ps -eo pid,args | grep` 确认 SIGINT/SIGKILL 后子进程已回收）。

---

## V7 — spawn_agent 嵌套深度（BDD-25「既有 max_depth=1 注记待复核」的证据）

方法：`codex exec` 派子代理 `p6_v7_child`，指令其再 `spawn_agent` 孙代理 `p6_v7_grand` 跑
`echo v7nest`；`find ~/.codex/sessions` 看孙会话文件 + 读 `session_meta.source.subagent.thread_spawn.depth`。

**观察**（codex exec exit 0，25s，`~/.codex/sessions/` 新增 3 个独立 rollout）：

| 层 | rollout basename | thread_source | thread_spawn.depth | parent_thread_id | agent_path |
|---|---|---|---|---|---|
| 父（codex exec）| `…08-20-43-01a08389-d70b-…` | `user` | （无 thread_spawn）| — | — |
| 子 `p6_v7_child` | `…08-20-51-01a08389-f4db-…` | `subagent` | **1** | `01a08389-d70b…`（父）| `/root/p6_v7_child` |
| 孙 `p6_v7_grand` | `…08-20-56-01a0838a-09f9-…` | `subagent` | **2** | `01a08389-f4db…`（子）| `/root/p6_v7_child/p6_v7_grand` |

**结论 V7**：

1. **嵌套 `spawn_agent` 生效**（0.153.4 / ChatGPT 账号）——`spawn_agent` 内再 `spawn_agent`
   成功产出 depth=2 的孙会话。
2. `source.subagent.thread_spawn.depth` 字段**随嵌套层级递增**（子=1、孙=2）；
   `parent_thread_id` / `forked_from_id` 指向**直接上级**（孙→子，不是孙→根）。
3. 每层子/孙会话是**独立 `rollout-*.jsonl`**，落同一扁平 `YYYY/MM/DD/` 目录 →
   `CodexAdapter.list_sessions` 的 `os.walk` **天然全枚举任意深度**（实测 `probe(孙)=True`、
   `孙 in list_sessions()=True`）。孙会话 `read_commands` 产出记录的 `session_id` = 孙自身
   basename（`echo v7nest` / `exit_code=0`）——**契约不受嵌套影响**（独立再证 BDD-11/BDD-12）。
4. **既有 `platform-notes.md` line 130「Codex subagent max_depth=1」/「单层任务工具无法再派发」
   注记已被实测超越**：嵌套到 depth=2 可用。该注记当前有「待 V7 复核」时效指针
   （line 76 / line 135）——V7 结论出来后，主 Agent 可决定回写 platform-notes.md
   （需重跑 `test_codex_platform_docs.py` + consistency）或另行处理。**P6 不改 `agate/`**。

---

## V2 — spawn_agent 参数 schema 穷尽（跨真实调用归纳键并集，BDD-24 / BDD-30 加强证据）

方法：跨 P6 本阶段 ≥5 次不同参数组合的真实 `spawn_agent` 调用（+ 本机今日更早 3 次），
从各 rollout 的 `response_item` / `payload.type=="function_call"` / `payload.name=="spawn_agent"`
的 `payload.arguments`（JSON 串）收集键并集。

**9 次真实 spawn_agent 调用**（P6：p6_v7_child / p6_v7_grand / p6_v2_a / p6_v2_b / p6_v2_c1 /
p6_v2_c2；更早：schema_probe / probe_child / echo_check）：

| task_name | 观察到的 arguments 键 | model | reasoning_effort | fork_turns |
|---|---|---|---|---|
| schema_probe | task_name, message, fork_turns | — | — | all |
| probe_child | task_name, message, fork_turns, model | gpt-5.6-terra | — | none |
| echo_check | task_name, message, fork_turns | — | — | none |
| p6_v7_child | task_name, message, fork_turns | — | — | all |
| p6_v7_grand | task_name, message, fork_turns | — | — | all |
| p6_v2_a | task_name, message, fork_turns, model, reasoning_effort | gpt-5.6-luna | high | none |
| p6_v2_b | task_name, message, fork_turns | — | — | none |
| p6_v2_c1 | task_name, message, fork_turns | — | — | all |
| p6_v2_c2 | task_name, message, fork_turns, model, reasoning_effort | gpt-5.4-mini | low | none |

**键并集 = `{task_name, message, model, reasoning_effort, fork_turns}`**

**结论 V2**：跨 9 次真实调用**未观察到 `[自述]` 之外的键**——没有 `background` / `timeout` /
`permission` 或其它。但样本量有限（只覆盖模型实际选择发出的键；带默认值的可选键在不显式设置时
不出现在 `arguments` 里），**不等于穷尽**。按 dispatch：`platform-notes.md` 的 `[自述]` 标注
**保持不动**（line 69 / line 78-82），无需回写。V2 无「重要发现」。

---

## 汇总

| 项 | 结论 | 是否需回写 platform-notes.md / 回 P4 |
|---|---|---|
| V6 ① 卡死 → FROZEN | ✅ 一致 | 否 |
| V6 ② 正常 → NORMAL | ✅ 一致 | 否 |
| V6 ③ 重复失败 → SPIN | ⚠️ 真机得 FROZEN/NORMAL，非 SPIN；根因 F1 | **F1：建议主 Agent 决定（P4 pending 判据 + platform-notes.md `status` 取值集）** |
| V7 嵌套深度 | 嵌套生效，depth 1→2 递增，契约不受影响；`max_depth=1` 注记已被超越 | **可选**：主 Agent 决定回写「待 V7 复核」指针（P6 不改） |
| V2 参数键并集 | `{task_name, message, model, reasoning_effort, fork_turns}`，无新键 | 否（`[自述]` 标注保持） |

`[PROD_NOT_TOUCHED]` — codex exec 仅跑 echo/sleep/ls/date；未写任何生产路径；`~/.agate` + worktree
`agate/` git 状态未被测试改动。

EXIT_CODE: 0
