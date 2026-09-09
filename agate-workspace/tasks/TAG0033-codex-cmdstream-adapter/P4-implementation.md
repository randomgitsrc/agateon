---
implementation_dir: agate/scripts/
phase: P4
task_id: TAG0033
type: implementation
parent: P3-test-cases.md
trace_id: TAG0033-P4-20260909
status: draft
created: '2026-09-09'
agent: implementer
---

# P4 实现报告 — TAG0033 Codex 命令流适配器

`[PROD_NOT_TOUCHED]`

`implementation_dir: agate/scripts/`

> parent：`P2-design.md`（§5 五设计点定论 = 实现权威）+ `P3-test-cases.md`
> 近亲范式：`agate/scripts/agate-cmdstream-adapters.py` 的 `DSHAdapter`

## 1. 改动文件清单（行数增量）

| 文件 | 改动 | 增量 |
|---|---|---|
| `agate/scripts/agate-cmdstream-adapters.py` | 新增 `import shlex`；新增 2 个模块级常量 `_CODEX_TRUNC_BOOL_KEYS` / `_CODEX_TRUNC_TEXT_MARKERS` + 模块级助手 `_codex_int_or_none`；新增 `class CodexAdapter(CommandStreamAdapter)`（`probe` / `list_sessions` / `read_commands` + `_join_command` staticmethod + `_detect_truncated` classmethod + `_build_record` method）；`ADAPTERS` 字典加 `"codex": CodexAdapter(),` | +225 / -0 |
| `agate/tests/unit/test_agate_cmdstream_adapters.py` | `test_bdd_6_detect_consumes_registry_zero_change`（:319）精确等值断言 `assert registered == {"claude-code","opencode","dsh"}` → 包含式 `assert {"claude-code","opencode","dsh"}.issubset(registered)`；其后 `assert "codex" in registered` / `assert "ADAPTERS" in detect_src` 保留不动 | +1 / -1 |

新增源码文件：**无**（`CodexAdapter` 加入既有 `agate-cmdstream-adapters.py`）。
不改：`agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` 的 `CommandRecord` dataclass /
`ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` class 体 / fixtures / `platform-notes.md` / `SETUP.md`。

## 2. CodexAdapter 三方法 + 截断 classmethod + 2 常量 落点

在 `agate-cmdstream-adapters.py` 中，位于 `DSHAdapter`（结束于 `_build_record` @ 旧 line 618）之后、
`ADAPTERS` 字典之前：

| 符号 | 类型 | 说明（对齐 P2 §5 / §4.2） |
|---|---|---|
| `_CODEX_TRUNC_BOOL_KEYS` | 模块级常量（class 上方） | `("truncated", "output_truncated", "is_truncated")`——item dict 上的显式布尔字段候选。带 `# P5 V4 收敛锚` 注释 |
| `_CODEX_TRUNC_TEXT_MARKERS` | 模块级常量（class 上方） | `("[output truncated]", "output truncated", "tokens truncated", "[truncated]")`——`aggregated_output`/`formatted_output` 里的字面量标记候选（小写子串匹配） |
| `_codex_int_or_none(val)` | 模块级助手 | epoch 毫秒字段取整数（`bool` 不算 `int`，畸形 → `None`） |
| `CodexAdapter.probe(self, path)` | 方法（设计点 1，定论 B） | basename `startswith("rollout-")` 且 `endswith(".jsonl")` 且非 `.jsonl.zstd` → `open` + `readline()` 首行 `json.loads`，判 `type=="session_meta"` 且 `payload` 含 `cli_version`/`originator`/`id` 任一。异常（路径不存在 / 首行非 JSON / 非 dict）→ `return False`，`except (OSError, ValueError, TypeError)` 不抛 |
| `CodexAdapter.list_sessions(self, cwd)` | 方法（设计点 5，定论 B + P2-review N1） | `root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`（`None`/`""` 都回落）；`os.walk` 收集 basename `startswith("rollout-")` 且 `endswith(".jsonl")` 且非 `.jsonl.zstd` 的文件；返回 `sorted()` 绝对路径 list |
| `CodexAdapter.read_commands(self, session_path)` | 方法（设计点 2/3/4） | 逐行 `json.loads`，坏行 `try/except (ValueError)` + `skipped+=1` + `continue`（非 JSON / 非 dict / 缺 `payload` 键 三类）；源过滤 `type=="event_msg"` ∧ `payload.type=="item_completed"` ∧ `item.type=="CommandExecution"`；十字段映射见下；pending 双判据（`status!="completed"` ∪ `started_ids - emitted_ids` 回填）；`skipped` 时 stderr 一行 |
| `CodexAdapter._join_command(command)` | staticmethod | `shlex.join(str(part) for part in command)`；非 list → `""` |
| `CodexAdapter._detect_truncated(cls, item)` | **classmethod**（设计点 4，比照 `DSHAdapter._detect_truncated`） | 非 dict → `False`；先查 `_CODEX_TRUNC_BOOL_KEYS`（`isinstance(v, bool) and v`），再查 `_CODEX_TRUNC_TEXT_MARKERS`（`aggregated_output`+`formatted_output` 小写子串）。任一命中 → `True`。带 `# P5 V4 收敛锚` 注释 |
| `CodexAdapter._build_record(...)` | 方法 | 十字段组装；`pending=True` → `exit=None` / `ts_end=None` / `exit_signal="pending"` / `output_hash=None` / `truncated=False`；已完成 → `exit` 直取 `item.exit_code`（`int` 非 `bool`），`exit_signal=f"exit_code={n}"`（无 exit_code → `item.status` 或 `"status=completed"`），`truncated` ⇒ `output_hash=None` 无条件 |
| `ADAPTERS["codex"]` | 注册表项 | `"codex": CodexAdapter()` |

十字段映射（P2 §4.2）：`platform="codex"` / `session_id=os.path.basename(session_path)`（**不取** `payload.session_id`——对子会话是父 id，设计点 3 定论 A）/ `tool="exec"`（常量）/ `command=shlex.join(item["command"])` / `ts_start=payload.started_at_ms`（缺 → 封套 `timestamp` 经 `_iso8601_to_epoch_ms`；再缺 → `None`）/ `ts_end=payload.completed_at_ms` / `exit=item.exit_code`（数字直取）/ `exit_signal` 如上 / `output_hash=_sha1_hex(item.aggregated_output or "")`（`truncated` → `None`）/ `truncated=_detect_truncated(item)`。

## 3. 每条原红灯测试转绿确认（P3 基线 19 条）

`test_agate_cmdstream_adapters.py`（14 条）：

| 测试 | 转绿点 |
|---|---|
| `test_bdd_1_codex_probe_identifies_rollout` | `probe` basename 门 + 首行 `session_meta` sniff：codex rollout→True；claude 内容 `rollout-fake.jsonl`（首行无 `session_meta`）→False；`.jsonl.zstd`→False；`opencode.db`（非 `rollout-` 前缀）→False |
| `test_bdd_2_codex_list_sessions_enumerates_date_tree` | `os.walk` 枚举 `YYYY/MM/DD` 下 `rollout-*.jsonl`，返回绝对路径 |
| `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root` | `root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`；`cwd=None` / `cwd=""` 均命中 monkeypatch 的 fallback 根 |
| `test_bdd_3_codex_list_sessions_includes_subagent` | 父 `rollout-P.jsonl` 与子 `rollout-C.jsonl` 同目录 → `os.walk` 天然同时枚举 |
| `test_bdd_4_codex_read_commands_maps_ten_fields` | `echo hi` 恰好 1 条：`platform=="codex"` / `tool=="exec"`（非空）/ `ts_start==1788400860000` / `ts_end==1788400861000` / `exit==0` / `exit_signal=="exit_code=0"`（非空）/ `truncated is False` / `output_hash==sha1(b"hi\n")` |
| `test_bdd_5_codex_failed_exit_code_verbatim` | `make build-docs` `exit_code==2` / `status=="completed"` → `exit==2`（非 None），`exit_signal=="exit_code=2"` 非空 |
| `test_bdd_6_codex_unfinished_command_pending` | `sleep 999` 有 `item_started` 无 `item_completed` → `started` 收集 → 回填 pending：`exit is None` / `ts_end is None` / `exit_signal=="pending"`；`make build-docs` 已完成记录 `exit==2` 不受影响 |
| `test_bdd_7_codex_truncated_output_hash_none` | `cat big.log`：`item.output_truncated==true`（bool 键命中）∪ `aggregated_output` 含 `"[output truncated]"`（文本标记命中）→ `truncated is True` 且 `output_hash is None` |
| `test_bdd_8_codex_non_shell_tool_events_no_record` | `custom_tool_call`（`type=="response_item"`）被 `type!="event_msg"` 滤除；派生 `FileChange` / `Extension` item 被 `item.type!="CommandExecution"` 滤除 → 记录中无 `apply_patch` / `web__run` / `demo.py` |
| `test_bdd_9_codex_malformed_lines_no_crash` | 非 JSON 行 → `except ValueError`；JSON 数组 → `not isinstance(obj, dict)`；缺 `payload` 键 `event_msg` → `not isinstance(payload, dict)`；三类均 `skipped+=1`+`continue`，其后 `cat big.log` 照常产出 |
| `test_bdd_10_codex_session_id_consistent_and_locatable` | `session_id = os.path.basename(session_path)`：≥2 条记录 `session_id` 唯一、非空、`== basename` |
| `test_bdd_11_codex_subagent_session_parses_standalone` | 子会话 fixture（`thread_source=="subagent"`）`read_commands` 正常产出 1 条 `python3 -m pytest -q`，`platform=="codex"`，不因缺父上下文返回空 |
| `test_bdd_12_codex_subagent_session_id_is_child_not_parent` | `session_id == child_name`（含 `80c6` 子自身标识），`!= "demo0000-0000-7000-a000-000000000abc"`（父 id）——因取 basename 而非 `payload.session_id` |
| `test_bdd_6_detect_consumes_registry_zero_change`（BDD-19，有意红） | `ADAPTERS` 加 `"codex"` 键 + `:319` 精确等值断言改包含式 `.issubset` → `assert "codex" in registered` 通过；`assert "ADAPTERS" in detect_src` 保留（detect 引擎零改动） |

`test_agate_cmdstream_detect.py`（5 条，检测引擎零改动，走 `CodexAdapter.read_commands` → `_records_to_events` → `detect`）：

| 测试 | 转绿点 |
|---|---|
| `test_bdd_13_codex_call_freeze_frozen` | `_cx_started` 未结束命令 → pending 记录 `ts_start` 非 None（取 `started_at_ms`），`exit`/`ts_end` 均 None → `_records_to_events` 产出 unresolved call → 距今 901s > 兜底 suspect 900s → `FROZEN` + "调用冻结" |
| `test_bdd_14_codex_activity_freeze_frozen` | 两条已完成命令，最后活动距今 301s > 活动冻结 suspect 300s → `FROZEN` + "活动冻结" |
| `test_bdd_15_codex_invalid_repeat_spin` | 6× `retry_convert` 同 `exit==1` 同 `aggregated_output` → 同 `output_hash` → 窗口内重复 ≥5 → `SPIN` + `retry_convert` |
| `test_bdd_16_codex_normal_progress_no_false_positive` | `exit` / 输出哈希在变化、无悬挂 → `NORMAL` |
| `test_bdd_17_codex_truncated_repeat_not_spin` | 6× `fail_task` `output_truncated=True` → `_detect_truncated` True → `output_hash=None` → 不参与 `(command, exit, output_hash)` 比对 → `verdict != "SPIN"` |

## 新增文件核对表

CODE-MAP 机制已采用（`agate-workspace/agents/CODE-MAP.md` 存在）。

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|---|---|---|
| （无） | — | — |

本阶段**无新增源码文件**：`CodexAdapter` class + 2 常量 + 1 助手加入既有
`agate/scripts/agate-cmdstream-adapters.py`（该文件已在 CODE-MAP 登记，无需新增 CODE-MAP 条目）。
`test_codex_platform_docs.py` 是 P3 产出、非本阶段新增。

> P4-review 非阻塞观察 + 协议对齐 NHR-2 已记：`agate-workspace/agents/CODE-MAP.md:33`「三平台命令流
> 适配器」措辞在 Codex 落地后需更新为「四平台」+ 补 rollout JSONL 源；`docs/research/
> cross-platform-dispatch-mechanics.md` L169/L286「缺 CodexAdapter」表述过时。二者均非零改动禁改项、
> 非 P4 阻塞——归入 **P7 `protocol-docs` 批**顺手更新（与 platform-notes.md Codex 章 / SETUP.md Codex
> 小节同批）。

## 5. 自查结果（自查 ≠ gate）

| 命令 | 结果 |
|---|---|
| `timeout 120s python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py agate/tests/unit/test_agate_cmdstream_detect.py -q` | **58 passed**（P3 基线 19 failed → 0 failed，无回归） |
| `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` | **1383 passed, 6 failed, 2 skipped**；6 failed 全为 `test_codex_platform_docs.py::test_bdd_22~27`（P7 文档，预期红），其余全绿——无引入回归 |
| `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!** |
| `timeout 60s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | exit 0，**0 ERROR**（329 WARNING 全为既有叙事文件引用，与本改动无关） |

## 6. 范围外 / 设计缺口

- `[SCOPE+]`：**无**。
- `DESIGN_GAP`：**无**。fixture 数据形态与 P2 §5 / §4.2 定论一致，未发现矛盾，未改 fixture。
- 说明：全量单测运行期间，某个非 cmdstream 测试向 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl` 追加了 2 行 gate 台账事件（P3 phase 台账补记，非本阶段代码产物）——已 `git checkout` 还原，不在本次改动 diff 内。仅 cmdstream 两个测试文件不触发该追加。

---

## protocol-docs 批（2/2）

> P2 dispatch_plan `static-batch` 第 2 批（第 1 批 `adapter-core` 已在 `835c9b9` 落地）。
> 纯 `.md` 文档补齐——让 `test_codex_platform_docs.py::test_bdd_22`~`test_bdd_27`（6 条 doc-assertion 审计，P4~P6 期间 by-design 红）自然转绿。**不改** `agate/scripts/*.py` / `agate/tests/`。

### 改动文件清单（行数增量）

| 文件 | 改动 | 增量 |
|---|---|---|
| `agate/platform-notes.md` | `## Codex / Hermes / OpenClaw 等` 节的「待补充」占位 → 完整 `## Codex` 章：平台形态 + 能力矩阵（`codex exec` / `-m`/`--model` / `model_reasoning_effort` / `--dangerously-bypass-approvals-and-sandbox` / `-s <read-only\|workspace-write\|danger-full-access>` + `--approve-for-me` + 注明 `--full-auto`/`-a` 已从 `codex exec` 移除 / `--json` / `resume` / 退出码不可靠须解析 `--json`）+ model 阵容小节（ChatGPT 账号默认 `gpt-5.6-terra`、`-m gpt-5`/`-m gpt-5-codex` 被 400 拒、`spawn_agent` model 枚举 4 个标 `[自述]`、API-key 账号「待有该环境时补（非阻塞）」）+ `spawn_agent` 子派发时效小节（`multi_agent` stable/true、单层已实测、嵌套未测、与既有 `max_depth=1` 注记交叉引用并标时效）+ `spawn_agent` 参数 schema `[自述]` 小节（不写「确认无字段」、穷尽实测归 V2 待执行）+ 命令流适配小节（`CodexAdapter` TAG0033 落地、per-command 数字 `exit_code`、V4 截断标记实测形态 `formatted_output` 的 `Warning: truncated output (original token count: N)` + `…N tokens truncated…`）+ Codex 验证记录表（含 `0.153.4` / `ChatGPT` / `2026-09` / `codex features list` 复核）；Hermes/OpenClaw 拆为独立 `## Hermes / OpenClaw 等` 节续保「待补充」；既有「Hardening-roadmap 跨平台适配」节「Codex 兼容性」注记下加 1 行时效指针（既有 `max_depth=1` / CI backstop 表等事实行**未动**）| +67 / -3 |
| `agate/SETUP.md` | DSH 小节（`### 步骤 2-DSH`）后新增 `### 步骤 2-Codex：codex-cli（Codex）接入`：安装（`npm i -g @openai/codex`）/ `codex login`（ChatGPT vs API key 影响可用 model）/ 自动化绕过 flag（`--dangerously-bypass-approvals-and-sandbox`、`--skip-git-repo-check`、`--json`）/ 验证接入（`codex features list` grep `multi_agent` + `codex exec --json` 冒烟）| +43 / -0 |
| `agate-workspace/agents/CODE-MAP.md` | line 33「三平台命令流适配器：… DSH JSONL.zstd」→「四平台命令流适配器：… DSH JSONL.zstd / Codex rollout JSONL（`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，CodexAdapter 于 TAG0033 补齐）」| +1 / -1 |
| `docs/research/cross-platform-dispatch-mechanics.md` | **逐处回写**（非文首总说明；未做大规模重写）：L169 §6.0.1 映射表 Codex 行「⚠ 缺 `CodexAdapter`」→「✅ `CodexAdapter` 已补（TAG0033，2026-09；本文调查快照期 2026-09-08 为『⚠ 缺』）」；L286 §11 未尽项 #2「唯一缺口 = Codex 适配器」→ 划除 + 「`CodexAdapter` 已补（TAG0033，2026-09）」| +2 / -2 |

新增源码文件：**无**。改测试：**无**（`test_codex_platform_docs.py` 是 P3 产出，仅补文档使其自然转绿；锚词与文档措辞对齐以 BDD 断言为准）。

### BDD-22~27 逐条转绿确认

`timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q` → **8 passed / 0 failed**（改前 6 failed / 2 passed）：

| BDD | 断言要点 | 转绿点 |
|---|---|---|
| BDD-22 | `## Codex` 节无「待补充」；11 个能力锚点 grep 命中 | 新 `## Codex` 章逐锚点覆盖；「待补充」仅存于拆出的独立 `## Hermes / OpenClaw 等` 节（不在 `_codex_section` 截取范围）|
| BDD-23 | `0.153.4` / `ChatGPT` / `2026-09` / `features list` | 章首时效注记 + 验证记录表 + model 阵容小节 |
| BDD-24 | `spawn_agent` schema 段标 `[自述]`；无「确认无」字样；指明穷尽实测为待执行项 | schema 小节标 `[自述]`，措辞「不得升级为『这些字段一定不存在』的断言」（回避 `确认无` 子串）+「真机验证清单 V2 待执行项」|
| BDD-25 | `max_depth=1` 仍在全文；`## Codex` 节交叉引用 `max_depth` + `multi_agent` + 标时效 | 子派发时效小节交叉引用既有注记 + `multi_agent` stable/true + 「待 V7…复核」；既有注记行未删，其下加时效指针 |
| BDD-26 | `gpt-5.6-terra` + `API` + 「待有该环境时补」/「待补」 | model 阵容小节三点齐备 |
| BDD-27 | SETUP.md 独立 Codex 小节 + 4 锚点 + `API key` | `### 步骤 2-Codex` 小节 |

BDD-29 / BDD-30（真机验证清单结构守护，本就绿）：未触碰 `P1-requirements.md`，保持绿。

### 自查判据结果（自查 ≠ gate）

| 命令 | 结果 |
|---|---|
| `timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q` | **8 passed**（BDD-22~27 红转绿）|
| `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` | **1389 passed / 0 failed / 2 skipped**（原 6 条 doc-audit 红全转绿，无新增失败）|
| `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **EXIT 0 / 0 ERROR**（329 WARNING，全为既有叙事文件引用，未新增本质条目；新增 Codex 章 / SETUP 小节未引入死链 / 行号引用漂移 / 平台名污染 ERROR）|
| `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!**（本批未改 .py）|

### 范围外 / 说明

- `[SCOPE+]`：**无**。
- research doc 第 4 项：采用**逐处回写**（L169 + L286 各一句），非文首总说明——两处即全部命中点，回写精确且最小；文档 §10 复核清单对 flag 名 / model 阵容等其它时效条目仍有效，故不加「全文皆快照」式总说明以免过度声明陈旧。
- `agate/tests/fixtures/cmdstream/codex-session.jsonl` 的 1 行改动（git status 可见）= P5 verifier 已做的 V4 fixture 收敛，属未 commit 的 P5 产出，**非本批产物**，未触碰。
