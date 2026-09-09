---
phase: P6
task_id: TAG0033
type: acceptance
parent: P5-verification.md
trace_id: TAG0033-P6-20260909
status: draft
created: 2026-09-09
agent: verifier
pass: 30
fail: 0
ui_affected: false
---

# P6 验收报告 — TAG0033 Codex 命令流适配器（P6 重做）

> 对 `P1-requirements.md` §6 的 **30 条 BDD（BDD-1~30）逐条**验收。每条只允许 PASS / FAIL，二值。
> `ui_affected: false`——无 vision / 截图，走 pytest `-v` 实跑 + grep + 真机命令输出。
> 本轮为 **P6 重做**（P5→P4 回退修 F1 / DEBT0035 后）：首轮 `P6-evidence/` 已归档
> `.archived/p6-pre-retreat-20260909/`，**不复用**，全部证据重新产出。
> 系统 `python3` 3.12.3 / pytest 9.0.3；worktree `.worktrees/agate-TAG0033`；HEAD 含 P5 通过点
> `5f704a0`（`p5_pass_commit=6f8422f`）。codex-cli 0.153.4 + ChatGPT 登录。

`[PROD_NOT_TOUCHED]` —— P6 未改任何 `agate/` 下代码 / 文档 / 测试 / fixture；`codex exec` 仅跑
无害命令（`echo` / `sleep` / `ls` / `date`）；`~/.agate` + worktree `agate/` git 状态未被测试改动
（post-test 残留检查见 `P6-evidence/real-machine-p6.md`）。

---

## 1. BDD 逐条验收结果

> 证据路径相对本文件所在目录。pytest test id 由
> `pytest --collect-only -q <三文件> | grep -iE "codex|bdd"` 取得后逐条 `pytest -v ::<test_id>` 实跑。

### 6.1 probe / list_sessions

- PASS BDD-1: `CodexAdapter().probe()` 对 Codex rollout JSONL 返回 True，对 Claude Code 转录 jsonl / `.jsonl.zstd` / `opencode.db` 返回 False（`test_bdd_1_codex_probe_identifies_rollout` PASSED）(P6-evidence/bdd-01.log)
- PASS BDD-2: `list_sessions` 枚举日期分层树 `2026/09/08/` + `2026/09/09/` 下全部 rollout 返回绝对路径；`cwd` 为 None/"" 时回落 `~/.codex/sessions` 默认根（`test_bdd_2_codex_list_sessions_enumerates_date_tree` + `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root` 均 PASSED）(P6-evidence/bdd-02.log)
- PASS BDD-3: `list_sessions` 不遗漏 `spawn_agent` 子会话文件（`thread_source=="subagent"` + `parent_thread_id`）——父子 rollout 同扁平目录被 `os.walk` 同时枚举（`test_bdd_3_codex_list_sessions_includes_subagent` PASSED）(P6-evidence/bdd-03.log)

### 6.2 read_commands 字段映射

- PASS BDD-4: 从 `event_msg`/`item_completed` 的 `CommandExecution` 事件映射 `CommandRecord` 十字段——`platform=="codex"`、`command` 含 `"echo hi"`、`tool` 非空、`ts_start==T1`、`ts_end==T2`、`exit==0`、`exit_signal` 非空原始形态、`truncated is False`、`output_hash==sha1("hi\n")`（`test_bdd_4_codex_read_commands_maps_ten_fields` PASSED）(P6-evidence/bdd-04.log)
- PASS BDD-5: 失败命令 `exit_code==2` + 真机 `item.status=="failed"`（`[BASELINE_CHANGE]` / DEBT0035）→ `CommandRecord.exit == 2`（整数，不回落 None）、`exit_signal == "exit_code=2"`、`ts_end` 非 None、`output_hash` 非 None（F1 加强断言全部实跑确认）；含守护 `test_bdd_5_codex_failed_status_not_pending_guard`（6 条 `status="failed"` 重复失败命令全部非 pending）（`test_bdd_5_codex_failed_exit_code_verbatim` + guard 均 PASSED）(P6-evidence/bdd-05.log)
- PASS BDD-6: 真·未结束命令（`item_started` 无 `item_completed`，无 `completed_at_ms`/`exit_code`）→ 1 条 `CommandRecord` `exit is None` / `ts_end is None` / `exit_signal == "pending"`；同文件已完成命令 `exit==2` 不受影响（`[BASELINE_CHANGE]`：pending 判据收紧为「无终态信号才算 pending」）；守护 `test_bdd_5_codex_failed_status_not_pending_guard` 复带（`test_bdd_6_codex_unfinished_command_pending` + guard 均 PASSED）(P6-evidence/bdd-06.log)
- PASS BDD-7: 截断输出（双信号 `item.output_truncated:true` ∪ 文本标记）→ `CommandRecord.truncated is True` 且 `output_hash is None`（`test_bdd_7_codex_truncated_output_hash_none` PASSED）(P6-evidence/bdd-07.log)
- PASS BDD-8: 非 shell 工具事件（`custom_tool_call` `apply_patch` / `web__run`，派生 `FileChange`/`Extension` item）不产出 `CommandRecord`（`test_bdd_8_codex_non_shell_tool_events_no_record` PASSED）(P6-evidence/bdd-08.log)
- PASS BDD-9: 畸形行（非 JSON / JSON 数组 / 缺 `payload` 键）被跳过不抛异常，其后合法 `CommandExecution` 照常产出（`test_bdd_9_codex_malformed_lines_no_crash` PASSED）(P6-evidence/bdd-09.log)
- PASS BDD-10: 同一会话文件 ≥2 条记录 `session_id` 相同、非空、`== os.path.basename(session_path)`（可定位回文件）（`test_bdd_10_codex_session_id_consistent_and_locatable` PASSED）(P6-evidence/bdd-10.log)

### 6.3 spawn_agent 子会话

- PASS BDD-11: 子会话 rollout（`thread_source=="subagent"`）`read_commands` 正常产出子代理 `CommandRecord`（`platform=="codex"`），不因缺父上下文抛异常或返回空（`test_bdd_11_codex_subagent_session_parses_standalone` PASSED）(P6-evidence/bdd-11.log)
- PASS BDD-12: 子会话 `session_meta` 中 `id`（子自身）≠ `session_id`（父）→ 产出记录 `session_id` 解析为子会话自身标识（取 basename，不取 `payload.session_id` 父 id）（`test_bdd_12_codex_subagent_session_id_is_child_not_parent` PASSED）(P6-evidence/bdd-12.log)

### 6.4 检测引擎对 Codex 会话判三态（检测引擎零改动）

- PASS BDD-13: Codex 会话含未结束命令、观察时刻距 `ts_start` > 900s → `verdict == "FROZEN"`，reasons 含「调用冻结」（`test_bdd_13_codex_call_freeze_frozen` PASSED）；真机 V6 ① 佐证 → FROZEN(P6-evidence/bdd-13.log, P6-evidence/real-machine-v6-frozen.log, P6-evidence/real-machine-p6.md)
- PASS BDD-14: Codex 会话所有命令已结束、最后活动距观察时刻 > 300s → `verdict == "FROZEN"`，reasons 含「活动冻结」（`test_bdd_14_codex_activity_freeze_frozen` PASSED）；真机 V6 ① 亦经活动冻结路径判 FROZEN(P6-evidence/bdd-14.log, P6-evidence/real-machine-v6-frozen.log)
- PASS BDD-15: Codex 会话窗口内同 `(command, exit, output_hash)` 组合重复 ≥ 5 次（真机形态 `status="failed"` + `exit_code` 非 0，DEBT0035）→ `verdict == "SPIN"`（`test_bdd_15_codex_invalid_repeat_spin` PASSED）；真机 V6 ③ 佐证 → SPIN(P6-evidence/bdd-15.log, P6-evidence/real-machine-v6-spin.log, P6-evidence/real-machine-p6.md)
- PASS BDD-16: Codex 会话命令持续推进、结果签名在变化、无未结束调用悬挂 → `verdict == "NORMAL"`（`test_bdd_16_codex_normal_progress_no_false_positive` PASSED）；真机 V6 ② 佐证 → NORMAL(P6-evidence/bdd-16.log, P6-evidence/real-machine-v6-normal.log)
- PASS BDD-17: Codex 会话同命令 / 同 exit / 输出均截断（`truncated=True`）重复 ≥ 5 次 → `verdict != "SPIN"`（截断输出不参与哈希比对）（`test_bdd_17_codex_truncated_repeat_not_spin` PASSED）(P6-evidence/bdd-17.log)

### 6.5 回归底线

- PASS BDD-18: 全量单测 `python3 -m pytest agate/tests/unit/ -q` → **1390 passed, 0 failed, 2 skipped**，进程 exit 0（1389 基线 + 1 条 F1 守护 `test_bdd_5_codex_failed_status_not_pending_guard`）(P6-evidence/bdd-18.log)
- PASS BDD-19: `test_bdd_6_detect_consumes_registry_zero_change` PASSED；`git diff main...HEAD` 证原 `assert registered == {"claude-code","opencode","dsh"}` 已改为包含式 `assert {"claude-code","opencode","dsh"}.issubset(registered)` + 追加 `assert "codex" in registered`；`assert "ADAPTERS" in detect_src`（检测引擎零改动消费锚）保留(P6-evidence/bdd-19.log)
- PASS BDD-20: `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 脚本）→ exit 0，**0 ERROR**（329 WARNING 全为既有叙事文件死链，非本质新增）(P6-evidence/bdd-20.log)
- PASS BDD-21: `git diff main...HEAD -- agate-cmdstream-detect.py agate-cmdstream-ir.py` 为**空**；`agate-cmdstream-adapters.py` = 252 insertions / **0 deletions**（纯新增 `CodexAdapter` class + `_codex_is_finished`/`_codex_int_or_none` helper + 2 常量 + `import shlex` + `ADAPTERS` 加一行；`ClaudeCodeAdapter`/`OpenCodeAdapter`/`DSHAdapter` 三 class 体无删除行）；守护 `test_bdd_21_command_record_ten_fields_unchanged` + `test_bdd_21_detect_thresholds_unchanged` 均 PASSED(P6-evidence/bdd-21.log)

### 6.6 platform-notes.md Codex 章

- PASS BDD-22: `test_bdd_22_codex_chapter_capability_matrix` PASSED；`platform-notes.md` `## Codex` 章无「待补充」，grep 命中 `codex exec` / `--model` / `model_reasoning_effort` / `--dangerously-bypass-approvals-and-sandbox` / `danger-full-access` / `--approve-for-me`（含 `--full-auto`/`-a` 已移除说明）/ `spawn_agent` / `--json` / `resume` / 「退出码不可靠」(P6-evidence/bdd-22.log)
- PASS BDD-23: `test_bdd_23_codex_chapter_version_and_account` PASSED；Codex 章含 `0.153.4` + `ChatGPT` + `2026-09` + `codex features list` 复核意味表述(P6-evidence/bdd-23.log)
- PASS BDD-24: `test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade` PASSED；`spawn_agent` schema 段标 `[自述]`，不含「确认无」，指明「穷尽 schema 直接实测」为真机验证清单 V2 待执行项；真机 V2 复核（本轮 `spawn_agent` `function_call.arguments` 键 = `{task_name,message,model,reasoning_effort,fork_turns}`，无 `background`/`timeout`/`permission` 新键，与首轮 9 次调用键并集一致，`[自述]` 标注保持）(P6-evidence/bdd-24.log, P6-evidence/real-machine-v7-v2.log)
- PASS BDD-25: `test_bdd_25_codex_chapter_cross_reference_no_contradiction` PASSED；全文档保留既有 `max_depth=1`，`## Codex` 章交叉引用 `max_depth` + `multi_agent`（stable/true）+ 标注时效（「待 V7 复核」），无未标时效的对立陈述（真机 V7 复做后此「待复核」措辞已过时——嵌套 `spawn_agent` 实测 depth=2 可用，见 §2.4 + `real-machine-p6.md`，属待回写发现、报告主 Agent，本轮 P6 不改文档）(P6-evidence/bdd-25.log, P6-evidence/real-machine-p6.md)
- PASS BDD-26: `test_bdd_26_codex_chapter_model_lineup` PASSED；Codex 章 model 小节含 `gpt-5.6-terra`（ChatGPT 默认、`-m gpt-5`/`-m gpt-5-codex` 被 400 拒）、`spawn_agent` model 枚举 4 个标 `[自述]`、API-key 账号「待有该环境时补（非阻塞）」(P6-evidence/bdd-26.log)
- PASS BDD-27: `test_bdd_27_setup_md_codex_section` PASSED；`SETUP.md` 含独立 Codex 小节，覆盖 `npm i -g @openai/codex` / `codex login`（ChatGPT vs API key 影响 model）/ `--dangerously-bypass-approvals-and-sandbox` / `--skip-git-repo-check`(P6-evidence/bdd-27.log)

### 6.7 SETUP.md Codex 小节

（BDD-27 已在 §6.6 呈现——归属 SETUP.md，证据同 `bdd-27.log`。）

### 6.8 SELF-GATE 留痕

- PASS BDD-28: `git log main..HEAD` 中 SELF-GATE 触发提交的 commit body 含 `self-gate-review:` 前缀行（指向 3 个 alignment review）+ 非触发阶段含 `self-gate-skip:` 前缀行；`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033{,-r2,-r3}.md` **3 个**均首部声明 `reviewer: protocol-alignment-review (agent≠main)`；`check-protocol-consistency.py --strict-errors-only` 记录 0 ERROR（BDD-20）(P6-evidence/bdd-28.log)

### 6.9 真机验证清单

- PASS BDD-29: `test_bdd_29_verification_checklist_shaped_four_elements` PASSED；`P1-requirements.md` §7 表 V1-V8 逐行四要素（验证什么 / 怎么验（含命令）/ 阶段 / 通过判据）齐备；V8（API-key 账号 model 阵容）显式标「待有该环境时补（非阻塞）」+ frontmatter `verification_env_budget` 占位(P6-evidence/bdd-29.log)
- PASS BDD-30: `test_bdd_30_spawn_agent_schema_exhaustive_item_registered` PASSED；§7 含 V2「直接实测穷尽 `spawn_agent` 参数 schema（`background`/`timeout`/`permission` 等）」项，注明 P1「令模型逐字输出内部 tool schema」不可用（模型受训拒绝）、P5-P6 换法（读 codex 二进制/内省、API-key 账号观察、跨大量真实调用归纳）、通过判据 = 给出字段全集并在 platform-notes.md 标 `[实测]`(P6-evidence/bdd-30.log)

---

## 2. 交叉核对节

### 2.1 BDD 编号一一对应

- 本报告逐条实跑 BDD-1 ~ BDD-30，共 **30 条**。
- 通过 30 条、失败 0 条，两者之和 = **30**。
- 与 `P1-requirements.md` §6 全部 BDD 编号（BDD-1 ~ BDD-30，§6.1~§6.9 九个小节）**一一对应，无遗漏、无重复**。
- BDD-5 的 F1 守护 `test_bdd_5_codex_failed_status_not_pending_guard`（无 BDD 编号）不单列 PASS 行，
  在 `bdd-05.log` / `bdd-06.log` 中带上并实跑 PASSED。

### 2.2 证据文件对应

- 每条 PASS 行引用 `P6-evidence/` 下实际存在、含实质内容的证据文件（pytest `-v` 实跑输出含
  `PASSED` + 用例名 + 计数 / `git diff` 输出 / grep 命中 / `check` 脚本 exit）。
- BDD-13~17 除单测 log 外，另引真机 V6 佐证 log（`real-machine-v6-{frozen,normal,spin}.log`）。
- 证据清单：`bdd-01.log` ~ `bdd-30.log`（30 个）+ `real-machine-v6-frozen.log` /
  `real-machine-v6-normal.log` / `real-machine-v6-spin.log` / `real-machine-v7-v2.log` /
  `real-machine-p6.md`。

### 2.3 F1（DEBT0035）变化在本轮验收的落点

- BDD-5：Given 改真机 `status="failed"` 形态；Then 加强断言 `exit==2` / `ts_end` 非 None /
  `output_hash` 非 None——`bdd-05.log` 实跑确认，测试源亦逐条核对（`assert r.exit == 2` /
  `assert r.ts_end is not None` / `assert r.output_hash is not None` / `assert r.exit_signal == "exit_code=2"`）。
- BDD-6：Given 收紧为「真·未结束（`item_started` 无 `item_completed` 且无 `completed_at_ms`/`exit_code`）」；
  Then 语义不变——`bdd-06.log` 实跑确认。
- BDD-15：fixture/构造改用 `status="failed"` 重复失败 → detect 判 SPIN——`bdd-15.log` + 真机 V6 ③ 双证。
- 真机 V6（F1 修复后完整重做三态）：① FROZEN（活动冻结）② NORMAL ③ **SPIN**——三态齐全，
  与 BDD-13/14/16/15 判据一致。详见 `real-machine-p6.md`。DEBT0035 closure_criteria
  「detect 对真机重复失败会话判 SPIN」由 V6 ③ 独立再证。

### 2.4 V7 / V2 复核结论与文档回写发现

- **V7**（引用 archived 首轮 + 本轮简短复核）：嵌套 `spawn_agent` 生效，
  `source.subagent.thread_spawn.depth` 1→2 递增（本轮 attempt 2 得 depth=2 孙会话，与首轮一致）；
  孙会话独立 rollout、落同扁平目录，`list_sessions` 的 `os.walk` 覆盖；`CodexAdapter` 契约不受影响。
- **V7 finding（报告主 Agent）**：`platform-notes.md` 现「嵌套深度未测（归 P6 V7）」/「既有
  `max_depth=1` 结论待 V7 复核」措辞——P6 重做 V7 已实测 depth=2 可用，该措辞已过时，宜回写为
  「已实测 depth=2 可用，`max_depth=1` 已被超越」。**本轮 P6 不改 `agate/`**（self-authored gate
  硬拦非证据文件；BDD-25 当前测的是现有措辞、现绿）。回写与否（文档收敛需重跑
  `test_codex_platform_docs.py` + consistency 确认，或回 P4/P7 单独处理）**交主 Agent 判断**。
- **V2**（引用首轮 + 本轮简短复核）：本轮 `spawn_agent` `function_call.arguments` 键 =
  `{task_name, message, model, reasoning_effort, fork_turns}`，与首轮跨 9 次调用键并集一致，
  无 `background`/`timeout`/`permission` 新键。`platform-notes.md` `[自述]` 标注保持不动，无需回写。

### 2.5 post-test 环境残留检查

- 无残留 `codex exec` / `sleep` / `code-mode-host` 进程。
- worktree `git status --short -- agate/`：**完全干净**——P6 未改任何 `agate/` 代码 / 文档 / 测试 / fixture。
- `~/.agate` 近 40 分钟无文件改动。
- `git status --short` 仅 P6 产出（`P6-acceptance.md` + `P6-evidence/` + `P6-progress.md` +
  `P6-dispatch-*.md`）+ `gate-events.jsonl`（既有未提交台账痕迹，`ts 2026-09-09T03:56:50Z`，
  会话前即存在，本轮验证未追加——不动）+ `.state.yaml`（主 Agent 手动 `_advance` 台账，不动）。
- 测试派生的 `~/.codex/sessions/**/rollout-*.jsonl` 为 Codex 正常行为产物、只读观察对象，非生产残留。
- 详见 `P6-evidence/real-machine-p6.md`「post-test 环境残留检查」。

### 2.6 P5 证据复用判定

- 本任务**不走「复用 P5 证据」口径**（`change_type` 非 refactor；30 BDD 逐条独立实跑）。
- 无 `regression.log`、无 `regression_pass` 声明——非 refactor 任务，不适用。

---

**Summary**: 30/30 PASS, 0 FAIL. `[PROD_NOT_TOUCHED]`. 真机 V6 三态齐全（① FROZEN ② NORMAL ③ SPIN）。
V7 发现 platform-notes.md「嵌套深度未测 / max_depth=1 待复核」措辞已过时——已报告主 Agent，P6 不改文档。
