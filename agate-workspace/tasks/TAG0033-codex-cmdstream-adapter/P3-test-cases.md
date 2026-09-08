---
test_code_dir: agate/tests/unit/
phase: P3
task_id: TAG0033
type: test-design
parent: P2-design.md
trace_id: TAG0033-P3-20260909
status: draft
created: '2026-09-09'
agent: test-designer
---


## test_code_dir

`test_code_dir: agate/tests/unit/`

测试代码落既有 cmdstream 测试树（不新建 adapter 测试文件）：

| 文件 | 改动 | 说明 |
|---|---|---|
| `agate/tests/unit/test_agate_cmdstream_adapters.py` | 追加 CodexAdapter 解析单测 BDD-1~12 + 守护 BDD-21；改 `test_bdd_6_detect_consumes_registry_zero_change`(:317 区域) 加 `assert "codex" in registered`（BDD-19）；扩 `test_bdd_7_fixture_sanitized` 脱敏清单 + Codex 连字符 uuid 负向断言（N3）| 既有 cmdstream 测试树增量 |
| `agate/tests/unit/test_agate_cmdstream_detect.py` | 追加 Codex 会话三态确定性试验 BDD-13~17 + 守护 BDD-21（阈值常量）| 比照既有 `_run_detect`/`_ev` 虚拟时钟范式，数据源换为 `CodexAdapter.read_commands` 解析 Codex fixture |
| `agate/tests/unit/test_codex_platform_docs.py` | **新建**：文档断言审计 BDD-22~27（红，P7 转绿）+ 真机验证清单结构守护 BDD-29/30（绿）| 独立文件理由见下 |

**新建 `test_codex_platform_docs.py` 的理由**：文档断言审计不属既有 cmdstream 适配器/检测单测范畴
（比照 TAG0027 的 `test_tag0027_b3a_platform_name_docs.py` 断言审计模式：一条测试 grep 多个锚）。
`gate_commands.P3` 已冻结为 `test_agate_cmdstream_adapters.py` + `test_agate_cmdstream_detect.py` 两文件，
把文档审计塞进这两个文件会污染「适配器解析 + 检测三态行为」的语义边界。代价：本文件不在
`check-tdd-red.py` 的 P3 gate 扫描范围——其红灯由 test-designer 自检的三文件 pytest 运行确认（见文末
自检结果），转绿由 **P7** 协议文档阶段负责。

**⚠️ 下游提示（P5 排序张力，交主 Agent 决策）**：`gate_commands.P5`（`python3 -m pytest
agate/tests/unit/ -q --tb=no`）会扫到 `test_codex_platform_docs.py` → BDD-22~27 的 **6 条**在
P4~P6 期间为 task-introduced 失败（P7 补 `platform-notes.md` / `SETUP.md` 后转绿）。P2 §7 的 P5
命令不含 deselect。P5 dispatch 须显式处理二选一：
① `--deselect agate/tests/unit/test_codex_platform_docs.py::test_bdd_2{2..7}_*`（或 `--ignore` 整文件），
P7 dispatch 再纳回；
② 按 P5 卡「预期在 P7 转绿的失败」在 `P5-test-results/unit.md` 登记这 6 条（BDD-18「全绿」口径
本就把文档审计排除在「解析单测与三态试验」之外）。
本 P3 阶段按 dispatch「BDD-22~27 必须真红」写为**普通失败断言**（非 xfail——xfail 会让
`check-tdd-red` 在含本文件时判 exit 2 假绿）。

---

## 30 条 BDD 逐条验证归属表

> P6 验收逐条对照本表。「P3 写单测」= 本阶段产出红灯测试；其余归对应阶段。

| BDD | 一句话 | 验证归属 | 本阶段 test id（`test_` 前缀省略）|
|---|---|---|---|
| BDD-1 | probe 识别 Codex rollout、拒绝其它平台会话文件 | **P3 单测**（红）| `bdd_1_codex_probe_identifies_rollout` |
| BDD-2 | list_sessions 枚举日期分层树下全部 rollout | **P3 单测**（红）| `bdd_2_codex_list_sessions_enumerates_date_tree` + `bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root`（N1）|
| BDD-3 | list_sessions 不遗漏 spawn_agent 子会话文件 | **P3 单测**（红）| `bdd_3_codex_list_sessions_includes_subagent` |
| BDD-4 | 从 CommandExecution 映射 CommandRecord 十字段 | **P3 单测**（红）| `bdd_4_codex_read_commands_maps_ten_fields` |
| BDD-5 | 失败命令 exit_code 非 0 如实映射不回落 None | **P3 单测**（红）| `bdd_5_codex_failed_exit_code_verbatim` |
| BDD-6 | 未结束命令 → exit=None/ts_end=None/"pending" | **P3 单测**（红）| `bdd_6_codex_unfinished_command_pending` |
| BDD-7 | 截断输出 → truncated=True 且 output_hash=None | **P3 单测**（红）| `bdd_7_codex_truncated_output_hash_none` |
| BDD-8 | 非 shell 工具事件不产出 CommandRecord | **P3 单测**（红）| `bdd_8_codex_non_shell_tool_events_no_record` |
| BDD-9 | 畸形行不崩溃 | **P3 单测**（红）| `bdd_9_codex_malformed_lines_no_crash` |
| BDD-10 | 同会话文件记录 session_id 一致且可定位 | **P3 单测**（红）| `bdd_10_codex_session_id_consistent_and_locatable` |
| BDD-11 | 子会话记录可独立解析 | **P3 单测**（红）| `bdd_11_codex_subagent_session_parses_standalone` |
| BDD-12 | 子会话 session_id 指向子会话自身（不取父 id）| **P3 单测**（红）| `bdd_12_codex_subagent_session_id_is_child_not_parent` |
| BDD-13 | Codex 会话调用冻结 → FROZEN | **P3 单测**（红）| `bdd_13_codex_call_freeze_frozen` |
| BDD-14 | Codex 会话活动冻结 → FROZEN | **P3 单测**（红）| `bdd_14_codex_activity_freeze_frozen` |
| BDD-15 | Codex 会话无效重复 → SPIN | **P3 单测**（红）| `bdd_15_codex_invalid_repeat_spin` |
| BDD-16 | Codex 会话正常推进 → NORMAL（不误报）| **P3 单测**（红）| `bdd_16_codex_normal_progress_no_false_positive` |
| BDD-17 | Codex 会话截断输出不误判 SPIN | **P3 单测**（红）| `bdd_17_codex_truncated_repeat_not_spin` |
| BDD-18 | 全量单测全绿（含新增）| **P5 验证**（`gate_commands.P5`）——回归底线，P3 不写 | — |
| BDD-19 | ADAPTERS 精确等值断言改包含式 | **P3 写**（红）| `bdd_6_detect_consumes_registry_zero_change`（:317 区域加 `assert "codex" in registered`）|
| BDD-20 | 协议一致性 0 ERROR | **P5_consistency / P7 验证**——`check-protocol-consistency.py --strict-errors-only`，P3 不写 | — |
| BDD-21 | 检测引擎 / IR / 阈值 / 既有三适配器零功能改动 | **P3 守护测试（绿）** + P5/P7 机械 diff 核对 | `bdd_21_command_record_ten_fields_unchanged`（adapters）+ `bdd_21_detect_thresholds_unchanged`（detect）|
| BDD-22 | Codex 章从「待补充」补为完整能力矩阵 | **P3 断言审计（红→P7 绿）**| `bdd_22_codex_chapter_capability_matrix` |
| BDD-23 | 验证 CLI 版本号与账号类型已注明 | **P3 断言审计（红→P7 绿）**| `bdd_23_codex_chapter_version_and_account` |
| BDD-24 | spawn_agent schema 证据强度如实标注不混同 | **P3 断言审计（红→P7 绿）**| `bdd_24_codex_chapter_spawn_agent_schema_evidence_grade` |
| BDD-25 | 新 Codex 章与既有 Codex 内容不自相矛盾 | **P3 断言审计（红→P7 绿）**| `bdd_25_codex_chapter_cross_reference_no_contradiction` |
| BDD-26 | model 阵容随账号类型的表述完整 | **P3 断言审计（红→P7 绿）**| `bdd_26_codex_chapter_model_lineup` |
| BDD-27 | SETUP.md 新增 Codex 接入小节 | **P3 断言审计（红→P7 绿）**| `bdd_27_setup_md_codex_section` |
| BDD-28 | SELF-GATE commit 留痕 + 协议对齐评审存在 | **P7/P8 验证**——commit-msg hook + protocol-alignment-review（`agent != main`），P3 不写 | — |
| BDD-29 | 真机验证清单成形且逐项四要素可判定 | **P3 结构守护（绿）** + P6 人工核对 | `bdd_29_verification_checklist_shaped_four_elements` |
| BDD-30 | spawn_agent schema 穷尽实测项已登记且方法边界已注明 | **P3 结构守护（绿）** + P6 人工核对 | `bdd_30_spawn_agent_schema_exhaustive_item_registered` |

**P3 写测试的 BDD**：1~17（含 N1 的 cwd 假值 fallback 用例）、19、21（守护）、22~27、29~30（守护）。
**归 P5**：18（`gate_commands.P5`）、20（`P5_consistency`）。
**归 P6**：29/30 的人工核对补充（自动结构守护已覆盖）、V6/V7 真机三态。
**归 P7**：22~27 转绿（补 `platform-notes.md` / `SETUP.md`）、20（`P7` consistency）。
**归 P7/P8**：28（SELF-GATE 留痕 + protocol-alignment-review）。

---

## fixture

| 文件（**新建**）| 覆盖 | 关键字段（结构取自真实 rollout，minimal_validation 已核；内容脱敏）|
|---|---|---|
| `agate/tests/fixtures/cmdstream/codex-session.jsonl` | BDD-1/4/5/6/7/8/9/10 + 三态试验数据基底 | 首行 `session_meta`（`thread_source:"user"`、`id==session_id=="demo0000-0000-…-abc"`、`cli_version:"0.153.4"`、`originator:"codex-tui"`）；2 条 `event_msg`/`item_completed` `CommandExecution` exit 0 与 2（`echo hi` / `make build-docs`）；1 条 `item_started`-only（`sleep 999`，`status:"in_progress"`，无 `item_completed`）= pending 双判据形态 B；`response_item`/`custom_tool_call` `apply_patch` + `web__run`（非 shell）；派生 `FileChange` / `Extension` item（非 `CommandExecution`）；畸形行 3 类（非 JSON / JSON 数组 / 缺 `payload`）；1 条截断 `CommandExecution`（双信号：`item.output_truncated:true` **且** `aggregated_output` 含 `"[output truncated]"`，`cat big.log`，位于畸形行之后证明解析器恢复）|
| `agate/tests/fixtures/cmdstream/codex-subagent-session.jsonl` | BDD-3/11/12 | 首行 `session_meta`（`thread_source:"subagent"`、`id=="demo0000-80c6-…-def"`（子自身）、`session_id=="demo0000-0000-…-abc"`（父，陷阱字段）、`parent_thread_id`/`forked_from_id`（父）、`source.subagent.thread_spawn.depth:1`、`originator:"codex_exec"`、`multi_agent_version:"v2"`）；1 条子代理 `CommandExecution` item_completed（`python3 -m pytest -q`，exit 0）|

**脱敏**：`demo` 前缀占位（`demo0000-0000-7000-a000-000000000abc` 父 / `demo0000-80c6-…-def` 子）；
无 `/home/kity`；用 `/demo/repo`；无密钥块（`BEGIN `/`PRIVATE KEY`）；无真实连字符 hex uuid（首段
`demo0000` 含非 hex 字符 `m`/`o` → 不匹配 `[0-9a-f]{8}-…`）；无真实 rollout 会话前缀 `01a0…`；
无真实 `~/.codex/sessions/` 路径。
**N3 落地**：`test_bdd_7_fixture_sanitized` 的 `for name in (...)` 元组加两个 codex fixture + 追加一段
Codex-专属负向断言（无形似真实的连字符 hex uuid、无 `01a0…` 前缀、无 `/.codex/sessions/` 路径）。
既有正则 `\b(?:ses|msg|prt|call)_[0-9a-f]{26}\b` 不匹配 Codex 连字符 uuid 的缺口由此补上。既有 4 条
断言（路径 / 密钥 / 26-hex / demo 占位）继续对 5 个 fixture 全部生效，语义不删不弱化。

---

## 每条 P3 测试用例：test id / 覆盖 BDD / 断言要点 / 预期红灯原因

> 断言目标全部来自 **P2-design.md §5 五设计点定论 + §4.2 十字段映射表**，不自创预期。
> 红灯原因分两类：**B-Attr** = `adapters.CodexAdapter` 触发 `AttributeError`（模块无该属性，P4 加 class 后消失）；
> **B-Assert** = 断言与当前仓库状态矛盾（P4/P7 落地后消失）。均为 B 类（非 SyntaxError / 非第三方 import）。

### A. CodexAdapter 解析单测（`test_agate_cmdstream_adapters.py`）

| test id | 覆盖 BDD | 断言要点（§5 定论）| 预期红灯 |
|---|---|---|---|
| `test_bdd_1_codex_probe_identifies_rollout` | BDD-1 | 设计点 1 定论 B：Codex rollout（basename `rollout-*.jsonl` 非 `.zstd` + 首行 `readline()` `type=="session_meta"` 且 payload 含 `cli_version`/`originator`/`id`）→ `probe` 返回 `True`；Claude Code 转录 `.jsonl`（首行 `tool_use`，无 `session_meta`）/ `.jsonl.zstd` / `opencode.db` → `False`；路径异常不抛 | B-Attr |
| `test_bdd_2_codex_list_sessions_enumerates_date_tree` | BDD-2 | 设计点 5：`os.walk` 枚举 `2026/09/08/rollout-A.jsonl` + `2026/09/09/rollout-B.jsonl`，返回**绝对路径** list，两者都在 | B-Attr |
| `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root` | BDD-2（**P2-review N1**）| 设计点 5 定论 B：`root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`——`monkeypatch` `os.path.expanduser("~/.codex/sessions")` 指向临时树，`list_sessions(None)` 与 `list_sessions("")` 均遍历该默认根、命中其中 rollout。fallback 分支不得成未测死代码 | B-Attr |
| `test_bdd_3_codex_list_sessions_includes_subagent` | BDD-3 | 设计点 5：父子 rollout 同在扁平 `YYYY/MM/DD/` → `os.walk` 天然同时枚举，`rollout-P.jsonl`（user）与 `rollout-C.jsonl`（subagent + `parent_thread_id`）都返回 | B-Attr |
| `test_bdd_4_codex_read_commands_maps_ten_fields` | BDD-4 | §4.2：`command==["/bin/bash","-lc","echo hi"]` → `platform=="codex"`、`command` 含 `"echo hi"`（`shlex.join` 后 `'echo hi'` 仍含子串）、`tool` 非空 str（常量 `"exec"`）、`ts_start==started_at_ms(1788400860000)`、`ts_end==completed_at_ms(1788400861000)`、`exit==0`、`exit_signal` 非空、`truncated is False`、`output_hash==sha1("hi\n")` | B-Attr |
| `test_bdd_5_codex_failed_exit_code_verbatim` | BDD-5 | §4.2 / 设计点 2 exit：`item.exit_code==2` → `CommandRecord.exit == 2`（整数，**不回落 None**），`exit_signal` 非空原始形态留档 | B-Attr |
| `test_bdd_6_codex_unfinished_command_pending` | BDD-6 | 设计点 2 pending：`item_started` 无 `item_completed` → 1 条记录 `exit is None`、`ts_end is None`、`exit_signal == "pending"`；同文件已完成命令（`make build-docs`）`exit==2` 不受影响 | B-Attr |
| `test_bdd_7_codex_truncated_output_hash_none` | BDD-7 | 设计点 4：双信号任一命中 → `truncated is True`；IR 铁律 `truncated=True ⇒ output_hash is None` **无条件** | B-Attr |
| `test_bdd_8_codex_non_shell_tool_events_no_record` | BDD-8 | 设计点 2 源过滤单类型正向白名单 `item.type=="CommandExecution"` + 第一层 `type=="event_msg"` → `custom_tool_call`（`apply_patch`/`web__run`）与派生 `FileChange`/`Extension` item 均不产出记录（断言无记录 command 含 `apply_patch`/`web__run`/`demo.py`）| B-Attr |
| `test_bdd_9_codex_malformed_lines_no_crash` | BDD-9 | 设计点 2：逐层 `isinstance` 守卫 + 顶层 try/except → 非 JSON / JSON 数组 / 缺 `payload` 三类坏行跳过、不抛异常；坏行**之后**的合法 `CommandExecution`（`cat big.log`）照常产出（证明解析器恢复）| B-Attr |
| `test_bdd_10_codex_session_id_consistent_and_locatable` | BDD-10 | 设计点 3 定论 A：≥2 条记录 `session_id` 全相同、非空、`== os.path.basename(session_path)`（可定位回文件）| B-Attr |
| `test_bdd_11_codex_subagent_session_parses_standalone` | BDD-11 | 子会话 rollout（`thread_source=="subagent"`）→ `read_commands` 正常产出记录（`platform=="codex"`），不因缺父上下文抛异常或返回空 | B-Attr |
| `test_bdd_12_codex_subagent_session_id_is_child_not_parent` | BDD-12 | 设计点 3：子会话文件名含**子自身** uuid → `session_id == basename`（含 `80c6` 子标识）；**不等于** `session_meta.session_id`（父 `demo0000-0000-…-abc`）——明确不取 `payload.session_id` | B-Attr |
| `test_bdd_21_command_record_ten_fields_unchanged` | BDD-21 | **守护（当前绿）**：`dataclasses.fields(CommandRecord)` 名与顺序恒为十字段 `platform/session_id/tool/command/ts_start/ts_end/exit/exit_signal/output_hash/truncated`——CodexAdapter 接入不得扩 IR schema（P1 §5 逃生阀）。P4 若动 IR 转红 | 绿（守护）|

### B. 检测引擎三态确定性试验（`test_agate_cmdstream_detect.py`）

> 范式：`CodexAdapter().read_commands(fixture/inline rollout)` → `_records_to_events`（比照
> `agate-cmdstream-detect.py` CLI 转换层 :343-369）→ `detect(events, now)`。阈值用 §3.4.3 既有值。

| test id | 覆盖 BDD | 断言要点 | 预期红灯 |
|---|---|---|---|
| `test_bdd_13_codex_call_freeze_frozen` | BDD-13 | inline rollout（1 完成 + 1 `item_started`-only）→ 未结束命令映射 `exit=None/ts_end=None` → CLI 转换只发 `call` 事件无 `result` → `detect` 距 `ts_start` 901s > 兜底 suspect 900s → `verdict=="FROZEN"`，reasons 含「调用冻结」 | B-Attr |
| `test_bdd_14_codex_activity_freeze_frozen` | BDD-14 | inline rollout（2 完成命令，无 pending）→ 最后活动距今 301s > 活动冻结 suspect 300s → `verdict=="FROZEN"`，reasons 含「活动冻结」 | B-Attr |
| `test_bdd_15_codex_invalid_repeat_spin` | BDD-15 | inline rollout：同 `command`/`exit_code=1`/`aggregated_output` × 6（→ 同 `(cmd, exit, output_hash)`，无截断）→ 窗口 10 内重复 6 ≥ SPIN 阈值 5 → `verdict=="SPIN"`，reasons 含命令名 | B-Attr |
| `test_bdd_16_codex_normal_progress_no_false_positive` | BDD-16 | inline rollout：run_test/apply_fix 迭代，exit 与输出哈希在变化，无未结束调用悬挂 → `verdict=="NORMAL"` | B-Attr |
| `test_bdd_17_codex_truncated_repeat_not_spin` | BDD-17 | inline rollout：同命令 / 同 exit / 输出均截断（`truncated=True ⇒ output_hash=None`）× 6 → `detect` 截断记录不进 `(cmd,exit,out)` 组合计数 → `verdict != "SPIN"` | B-Attr |
| `test_bdd_21_detect_thresholds_unchanged` | BDD-21 | **守护（当前绿）**：`CALL_ALERT_FALLBACK==300` / `CALL_SUSPECT_FALLBACK==900` / `ACTIVITY_ALERT==60` / `ACTIVITY_SUSPECT==300` / `SPIN_THRESHOLD==5` / `REPEAT_WINDOW==10`——三态试验用既有阈值，不新造。P4 改常量转红 | 绿（守护）|

### C. BDD-19：ADAPTERS 精确等值断言改包含式（`test_agate_cmdstream_adapters.py`）

| test id | 覆盖 BDD | 断言要点 | 预期红灯 |
|---|---|---|---|
| `test_bdd_6_detect_consumes_registry_zero_change` | BDD-19 | 在原 `assert registered == {"claude-code","opencode","dsh"}` **之后**加一行 `assert "codex" in registered`。当前 `ADAPTERS` 无 `codex` 键 → 新断言失败（红）。**原语义（检测引擎零改动消费注册表）不删、不弱化**——原 `==` 行与 `"ADAPTERS" in detect_src` 锚均保留。P4 加键 + 把 `==` 行改成含 `codex` 的四键集合 / `>=` 包含式后整片转绿 | B-Assert |

### D. 文档断言审计（`test_codex_platform_docs.py`，新建）

> 比照 TAG0027「一条测试 grep 多个锚」。当前红（`platform-notes.md` `## Codex` 仍「待补充」、
> `SETUP.md` 无 Codex 小节），**P7** 补文档后转绿。B-Assert。

| test id | 覆盖 BDD | 断言要点 | 预期红灯 |
|---|---|---|---|
| `test_bdd_22_codex_chapter_capability_matrix` | BDD-22 | `## Codex` 章正文不含「待补充」；grep 命中 `codex exec` / `--model` / `model_reasoning_effort` / `--dangerously-bypass-approvals-and-sandbox` / `danger-full-access` / `--approve-for-me` / `--full-auto` / `spawn_agent` / `--json` / `resume` / `退出码` | B-Assert |
| `test_bdd_23_codex_chapter_version_and_account` | BDD-23 | Codex 章含 `0.153.4` + `ChatGPT` + `2026-09` + `features list`（复核意味）| B-Assert |
| `test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade` | BDD-24 | spawn_agent schema 段含 `[自述]`；**不含**「确认无」；含「待执行 / 真机验证 / 待实测」意味 | B-Assert |
| `test_bdd_25_codex_chapter_cross_reference_no_contradiction` | BDD-25 | 全文档保留既有 `max_depth=1`；`## Codex` 章交叉引用 `max_depth` + `multi_agent` + 时效状态（`待复核`/`时效`/`复核`）| B-Assert |
| `test_bdd_26_codex_chapter_model_lineup` | BDD-26 | Codex 章含 `gpt-5.6-terra` + `API` + 「待有该环境 / 待补」（API-key 账号 model 登记为待补，非阻塞）| B-Assert |
| `test_bdd_27_setup_md_codex_section` | BDD-27 | `SETUP.md` 含 `Codex` 小节 + `npm i -g @openai/codex` + `codex login` + `--dangerously-bypass-approvals-and-sandbox` + `--skip-git-repo-check` + `API key`/`API-key` | B-Assert |
| `test_bdd_29_verification_checklist_shaped_four_elements` | BDD-29 | **守护（当前绿）**：`P1-requirements.md` §7 含 `\| V1 \|`..`\| V8 \|` 逐项 + 表头四要素（`验证什么`/`怎么验`/`阶段`/`通过判据`）+ `待有该环境时补` + `verification_env_budget`。§7 表被删/缩减转红 | 绿（守护）|
| `test_bdd_30_spawn_agent_schema_exhaustive_item_registered` | BDD-30 | **守护（当前绿）**：`P1-requirements.md` 含 `spawn_agent` + `穷尽` + `模型受训`/`模型拒绝` + `换法` + 候选字段 `background`/`timeout`/`permission`。该登记被删转红 | 绿（守护）|

---

## 9 条关键约束落地核对

| # | 约束 | 落地 |
|---|---|---|
| 1 | 测试代码写进既有文件 | BDD-1~19 全落 `test_agate_cmdstream_{adapters,detect}.py`；仅文档审计 BDD-22~27（+ 结构守护 29/30）新建 `test_codex_platform_docs.py`（理由见「test_code_dir」节）|
| 2 | 不改既有测试断言语义，唯一例外 `:317` | `test_bdd_6_detect_consumes_registry_zero_change` 仅**追加** `assert "codex" in registered`，原 `==` 行 + `"ADAPTERS" in detect_src` 锚 + 注释语义保留。其余既有测试一律不碰 |
| 3 | fixture 结构取自真实 rollout + 脱敏 | 见「fixture」节；covered：exit 0/非 0 各一、1 未结束、1 子会话文件、非 shell 工具事件、畸形行 3 类、截断双信号样例 |
| 4 | §5 五设计点定论是断言目标 | probe 判据 / 映射规则 / `session_id` 取 basename / 截断双信号 / `list_sessions` os.walk —— 每条 test 断言点直接引 §5 / §4.2（见「每条用例」表）|
| 5 | P2-review N1/N3 落地 | N1 → `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root`（`cwd=None`/`""` 触发 fallback）；N3 → `test_bdd_7_fixture_sanitized` 加 codex fixture 到清单 + Codex 连字符 uuid 负向断言 |
| 6 | 虚拟时钟三态试验比照既有范式、阈值用 §3.4.3 | `_records_to_events` 比照 CLI 转换层；`test_bdd_21_detect_thresholds_unchanged` 守护常量值（900/300/5/10/60/300）不新造 |
| 7 | 每步落盘 P3-progress.md | 见 `P3-progress.md`（bash 追加）|
| 8 | 所有 bash 命令加 `timeout` 前缀 | 已遵守；自检用 `timeout 120s python3 -m pytest …` |
| 9 | 不派 review / 不写实现 | 本阶段只产测试 + fixture + 本文档；`CodexAdapter` 留给 P4 |

---

## 阈值引用（RM-AG0055 §3.4.3 既有值，不新造）

| 常量 | 值 | 用于 |
|---|---|---|
| `CALL_SUSPECT_FALLBACK` | 900s | BDD-13 调用冻结 suspect |
| `CALL_ALERT_FALLBACK` | 300s | 调用冻结 alert（守护断言）|
| `ACTIVITY_SUSPECT` | 300s | BDD-14 活动冻结 suspect |
| `ACTIVITY_ALERT` | 60s | 活动冻结 alert（守护断言）|
| `SPIN_THRESHOLD` | 5 | BDD-15 无效重复 |
| `REPEAT_WINDOW` | 10 | SPIN 窗口 |

---

## 自检结果（返回前 `timeout 120s python3 -m pytest <三文件> -q`）

```
25 failed, 41 passed        （三文件：test_agate_cmdstream_adapters.py + test_agate_cmdstream_detect.py + test_codex_platform_docs.py）
```

- **新增/改动用例红灯 25 条**，全部 B 类：
  - BDD-1~12 + N1（14 条）+ BDD-13~17（5 条）→ `AttributeError: module '…agate_cmdstream_adapters…' has no attribute 'CodexAdapter'`（B-Attr）
  - BDD-19（`test_bdd_6_detect_consumes_registry_zero_change`，1 条）→ `assert "codex" in registered` 失败（B-Assert）
  - BDD-22~27（6 条）→ 文档锚点断言失败（B-Assert）
- **无 SyntaxError / 无第三方 import 失败**：三文件 `compile()` 通过；pytest 收集无 error；gate 输出中
  `Traceback|SyntaxError|ImportError|ModuleNotFoundError` 关键词计数 = 0（`check-tdd-red.py` line 123 A 类误判不触发）。
- **既有用例不因本改动转红**（除 `:317` 有意改红那条）：两 gate 文件单独跑 `19 failed, 39 passed`，
  非-codex 失败**仅** `test_bdd_6_detect_consumes_registry_zero_change`（= BDD-19 有意）。基线 38 passed → 现
  39 passed（+2 守护测试，−1 有意改红）。
- **守护测试绿**：`test_bdd_21_command_record_ten_fields_unchanged` / `test_bdd_21_detect_thresholds_unchanged`
  / `test_bdd_29_*` / `test_bdd_30_*` / 扩展后的 `test_bdd_7_fixture_sanitized` 全 pass。
- **`check-tdd-red.py $TASK_DIR` 实跑 exit 0**（`TDD_CHECK: red-light (unexpected test failure)`——
  无 formatter 兜底路径落在真实失败、无 A 类关键词）。
- 全量 `pytest agate/tests/unit/ --collect-only` = 1391 tests collected，无收集错误。

---

## 范围外发现

1. **P5 排序张力（非阻塞，交主 Agent 决策）**：`gate_commands.P5`（`pytest agate/tests/unit/ -q`）会跑
   `test_codex_platform_docs.py`，BDD-22~27 的 6 条在 P4~P6 期间为 task-introduced 失败（P7 补文档转绿）。
   P2 §7 的 P5 命令未含 deselect。建议 P5 dispatch：① `--deselect`/`--ignore` 这 6 条，P7 dispatch 纳回；
   或 ② 按 P5 卡「预期在 P7 转绿的失败」在 `P5-test-results/unit.md` 登记。BDD-18「全绿」原文已把文档审计
   排除在「解析单测与三态试验」之外，与此一致。未采用 `xfail`——`xfail` 会让含本文件的 pytest 运行
   在 P7 前 exit 0，违反「BDD-22~27 必须真红」。
2. **pending 形态依赖设计点 2 的 form B**：fixture 用「`item_started` 无 `item_completed`」表达未结束命令
   （§2.3 R3 双判据之一）。若 P4 只实现 form A（`item_completed` 且 `status!="completed"`）则 BDD-6/BDD-13
   仍红——这是 TDD 正常拦截（设计点 2 明确要求 `started_ids - completed_ids` 补记录），非测试 bug。
   P5 V3 真机若捕获到 form A 的真实 rollout，P4/P5 可按易替换形式收敛 fixture。
3. **截断常量为 P5 V4 前的推测形态**：fixture 截断样例同时命中 `item.output_truncated:true`（bool 键集）
   与 `"[output truncated]"`（文本标记集）两个 P2 §5 列出的推测形态 → 无论 P4 先实现哪个信号都能命中。
   P5 V4 实测真形态后，按 §5「P5 V4 收敛锚」定向改 `_detect_truncated` + 2 常量 + 本 fixture 截断行三处。
4. **frontmatter `agent` 字段无法用 set 写入（工具版本 skew，交主 Agent）**：`~/.agate/scripts/agate-md-field-set.py`
   的合法 key 清单不含 `agent`（`ERROR: 非法 key 'agent'`），但 dispatch 要求 `agent=test-designer` 且
   同目录 sibling（TAG0030/0032）P3-test-cases.md frontmatter 均有 `agent: test-designer`。按纪律未绕过 set
   手改。当前 `check-frontmatter.py P3-test-cases.md` **exit 0**（不因缺 `agent` 失败）。建议主 Agent 用
   worktree 内的 `agate/scripts/agate-md-field-set.py`（若支持）或人工补 `agent: test-designer` 一行。
5. **ruff 回归**：新增测试代码触发既有 `test_env_adapt_docs.py::test_bdd_34`（`ruff check agate/`）——
   已在 P3 内修正（`hashlib.sha1("hi\n".encode("utf-8"))` → `hashlib.sha1(b"hi\n")`，UP012）。
   `ruff check agate/` 现 `All checks passed`。非范围外，记录备查。
