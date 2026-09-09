# P6 真机验证结论 — V6 三态 / V7 / V2（TAG0033，P6 重做）

> verifier subagent 产出。本机：codex-cli **0.153.4** + ChatGPT 登录，Linux/WSL2，2026-09-09。
> 所有 `codex exec` 仅跑无害命令（`echo` / `sleep` / `ls` / `date`）。`[PROD_NOT_TOUCHED]`。
> 本轮为 **P6 重做**（P5→P4 回退修 F1（DEBT0035）后）。首轮 V6/V7/V2 结论在
> `.archived/p6-pre-retreat-20260909/real-machine-p6.md`——**V6 因 F1 修复完整重做（三态）**，
> V7/V2 引用首轮 + 本轮简短复核。原始命令输出见同目录
> `real-machine-v6-frozen.log` / `real-machine-v6-normal.log` / `real-machine-v6-spin.log` /
> `real-machine-v7-v2.log`。

---

## V6 — 检测引擎对真实 Codex 会话判三态（F1 修复后完整重做，BDD-13~17 真机佐证）

方法：`codex exec`（codex-cli 0.153.4 + ChatGPT 登录）现场造 3 个真实 rollout → 各跑
`python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now <虚拟时刻>`。

| 场景 | 真实 rollout | 造法 | detect 结果 | 与 BDD 判据 |
|---|---|---|---|---|
| ① 卡死会话 | `rollout-2026-09-09T12-07-54-01a08459-d4cb-73a2-bbe2-d55ea89756d6.jsonl` | `codex exec` 派前台 `sleep 600`，~40s 后对会话 SIGINT（`turn_aborted`）| `--now = ts_start+950s` → **FROZEN**（活动冻结 suspect，最后活动距今 919s ≥ 300s）；`--now = ts_start+30s` → NORMAL | ✅ **一致**（① → FROZEN） |
| ② 正常会话 | `rollout-2026-09-09T12-04-09-01a08456-640d-7921-808b-fa6da4744494.jsonl` | 依次跑 `echo p6norm-alpha` / `date +%s` / `sleep 1` / `ls /etc/hostname` / `echo p6norm-omega-done`（5 条秒级完成，输出各异）| `--now = 最后活动+30s` → **NORMAL**；对照 `--now = 最后活动+400s` → FROZEN（活动冻结）| ✅ **一致**（② → NORMAL） |
| ③ 重复失败会话 | `rollout-2026-09-09T12-04-58-01a08457-242f-7422-b134-54040cfce108.jsonl` | 连跑 7 次完全相同的 `ls /demo/p6spin-nonexistent-xyz`（每次 exit 2、`status=="failed"`、输出恒定）| `--now = 首命令 started_at_ms+5s` → **SPIN**（同 `(命令, exit, 输出哈希)` 组合在窗口 10 内重复 7 次 ≥ 5）| ✅ **一致**（③ → SPIN） |

**V6 三态齐全 = 完整通过。** 三个 verdict 与 BDD-13/14（FROZEN）、BDD-16（NORMAL）、BDD-15（SPIN）判据一致。

### F1 修复在真机的直接体现（③ 是 P6 重做的关键证据）

- ③ 会话 7 条命令真机记为 `payload.item.status == "failed"`（不是 `"completed"`），仍携完整
  `exit_code==2` + `completed_at_ms`。F1 修复后 `_codex_is_finished` 据「有终态信号」判**已结束**，
  `read_commands` 产出 `exit=2` / `exit_signal="exit_code=2"` / `output_hash="67d40ac728a48516d465fc61d2cf38c3d1d577ee"`（恒定）/ `ts_end` 非 None——**不再是 pending 空壳**。
  `detect` 据此拿到稳定的 `(命令, exit, 输出哈希)` 结果签名 → 判 **SPIN**。
  （F1 修复前：同类 `status="failed"` 命令被误判 pending → `exit`/`output_hash` 全 None →
  detect 判 FROZEN/NORMAL，见 `.archived/p6-pre-retreat-20260909/real-machine-p6.md` V6 ③「⚠️ 不一致」。）
- ① 会话的 aborted `sleep 600` 真机记为 `status=="failed"` / `exit_code==-1` / 携 `completed_at_ms`
  → F1 修复后同样判「已结束」（exit=-1，ts_end 非 None），非 pending。因此 ① 的 FROZEN 来自
  **活动冻结**（最后活动 stale），而非首轮 pre-fix 时的「调用冻结」。dispatch ① 判据「FROZEN（调用/活动冻结）」二者皆可 → 一致。
- 真·未结束命令（`item_started` 无 `item_completed`）在本机 codex 0.153.4 无真实 rollout 形态
  （命令要么落 `item_completed`，要么被 abort 前不落 `CommandExecution`）——该路径由单测
  `test_bdd_6_codex_unfinished_command_pending`（fixture `sleep 999` 仅 item_started）+
  `test_bdd_13_codex_call_freeze_frozen` 覆盖，P6 全量 pytest 绿。

---

## V7 — spawn_agent 嵌套深度（引用首轮 + 本轮简短复核）

**首轮结论**（`.archived/p6-pre-retreat-20260909/real-machine-p6.md` V7）：嵌套 `spawn_agent` 生效，
`source.subagent.thread_spawn.depth` 随层级递增（子=1、孙=2），`parent_thread_id`/`forked_from_id`
指向直接上级，每层独立 `rollout-*.jsonl` 落同一扁平目录 → `list_sessions` 的 `os.walk` 天然全枚举；
契约（`session_id`=子/孙自身 basename）不受嵌套影响。

**本轮简短复核**（2 次尝试）：

- attempt 1（thread `01a0845b-5bf3`）：子代理自报「Unable to spawn grandchild: collaboration tool
  unavailable」，`~/.codex/sessions/` 新增 2 个 rollout（父+子，**无孙**）。判定为模型行为噪声
  （子模型该轮未成功发起孙 spawn），非平台能力缺失。
- attempt 2（thread `01a0845c-5982`，指令更直白）：**成功**——`~/.codex/sessions/` 新增 3 个 rollout：
  - child `rollout-2026-09-09T12-10-49-01a0845c-7e4d-…`：`session_meta` `thread_source=="subagent"`、
    `source.subagent.thread_spawn.depth == 1`、`agent_path == "/root/p6redo2_child"`
  - grand `rollout-2026-09-09T12-10-54-01a0845c-919c-…`：`thread_source=="subagent"`、
    **`thread_spawn.depth == 2`**、`agent_path == "/root/p6redo2_child/p6redo2_grand"`
  - parent 报「Child replied: done」

**结论 V7（P6 重做）**：与首轮一致——嵌套 `spawn_agent` 生效，`depth` 字段 1→2 递增，孙会话为独立
rollout 文件、落同一扁平 `YYYY/MM/DD/` 目录，`CodexAdapter.list_sessions` 的 `os.walk` 覆盖任意深度。
`CodexAdapter` 契约不受嵌套影响。

### V7 finding — platform-notes.md「嵌套深度未测」/「max_depth=1 待复核」注记已过时（报告主 Agent）

`agate/platform-notes.md` 现有措辞（`## Codex` 章「子代理派发」小节 + 「Hardening-roadmap 跨平台适配」
节「Codex 兼容性」注记的时效指针）：

- 「**单层 `spawn_agent` 已实测可用**（P5 V3）；**嵌套深度（`spawn_agent` 内再 `spawn_agent`）未测**（归 P6 V7）」
- 「既有 `max_depth=1` 结论待 V7 嵌套深度实测后复核」

**P6 重做 V7 已实测**：嵌套 `spawn_agent` 生效、depth 1→2 可用（本轮 attempt 2 + archived 首轮两次
独立证实）。因此上述「未测（归 P6 V7）」/「待 V7 复核」措辞已过时，宜回写为「已实测 depth=2 可用，
既有 `max_depth=1`（写于 subagent workflows 默认启用前）已被超越」——与 archived 首轮 V7 的同一建议一致。

**处理（二选一，本 verifier 选后者并报告主 Agent）**：platform-notes.md **本轮保持原样不改**
（P6 是 self-authored gate，`pre-commit-gate.sh` 硬拦 phase=P6 时暂存的非证据文件；且 BDD-25 当前
测试的正是现有措辞、现绿）。V7 结论只记入本 `real-machine-p6.md`。**是否回写 platform-notes.md
（属文档收敛，需重跑 `test_codex_platform_docs.py` + `check-protocol-consistency.py --strict-errors-only`
确认，或回 P4/P7 单独处理）交主 Agent 判断**——按 dispatch「V7 若判断该回写 → 先停下报告主 Agent」，
本 verifier 已在返回中明确报告此发现。

---

## V2 — spawn_agent 参数 schema 键并集（引用首轮 + 本轮简短复核）

**首轮结论**（archived V2）：跨 9 次真实 `spawn_agent` 调用，`function_call.arguments` 键并集 =
`{task_name, message, model, reasoning_effort, fork_turns}`，**无 `[自述]` 之外的键**（无 `background` /
`timeout` / `permission`）；样本有限 ≠ 穷尽，`platform-notes.md` 的 `[自述]` 标注保持。

**本轮简短复核**：thread `01a0845b-5bf3` 的 `spawn_agent` `function_call.arguments` 键 =
`['fork_turns', 'message', 'model', 'reasoning_effort', 'task_name']` —— 与首轮键并集**完全一致**，
无新键。

**结论 V2（P6 重做）**：与首轮一致，未观察到 `[自述]` 之外的键。`platform-notes.md` 的
`spawn_agent` 参数 schema `[自述]` 标注**保持不动**，无需回写。V2 无「重要发现」。

---

## post-test 环境残留检查（P6 卡强制步骤）

- 测试派生的 `~/.codex/sessions/2026/09/09/rollout-*.jsonl`（V6 的 3 个 + V7 的 ~5 个子/孙会话 +
  健康检查 1 个）为 **Codex 正常行为产物、只读观察对象**，非 agate 生产环境残留。
- 残留 `codex exec` / `sleep 600` / `code-mode-host` 进程：**无**
  （`ps -eo pid,args | grep -E 'codex exec|sleep 600|code-mode-host'` 空——SIGINT/SIGKILL 后子进程已回收）。
- `~/.agate`：近 40 分钟**无任何文件改动**（`find ~/.agate -type f -newermt '40 minutes ago'` 空）。
- worktree `git status --short -- agate/`：**完全干净**——无任何代码 / 文档 / 测试 / fixture 改动。
- worktree `git status --short`：仅 P6 产出（`P6-evidence/`、`P6-progress.md`、`P6-dispatch-*.md`）+
  `gate-events.jsonl`（19 行 = HEAD 17 + 2 行 `ts 2026-09-09T03:56:50Z` 的既有未提交台账痕迹，
  **会话开始前即存在**，本轮验证未追加——dispatch 明确「不要动」）。
- `~/.agate` + worktree `agate/` git 状态未被测试改动。

---

## 汇总

| 项 | 结论 | 是否需回写 platform-notes.md / 回 P4 |
|---|---|---|
| V6 ① 卡死 → FROZEN | ✅ 一致（活动冻结）| 否 |
| V6 ② 正常 → NORMAL | ✅ 一致 | 否 |
| V6 ③ 重复失败 → SPIN | ✅ 一致（F1 修复关键证据；DEBT0035 closure「detect 对真机重复失败会话判 SPIN」再证）| 否 |
| V7 嵌套深度 | 嵌套生效，depth 1→2 递增，契约不受影响；与首轮一致 | **finding：platform-notes.md「嵌套深度未测/待 V7 复核」措辞已过时——本轮不改，报告主 Agent 判断是否回写** |
| V2 参数键并集 | `{task_name, message, model, reasoning_effort, fork_turns}`，无新键 | 否（`[自述]` 标注保持）|

`[PROD_NOT_TOUCHED]` — `codex exec` 仅跑 `echo`/`sleep`/`ls`/`date`；未写任何生产路径；
`~/.agate` + worktree `agate/` git 状态未被测试改动。

EXIT_CODE: 0
