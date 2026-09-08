---
status: approved
phase: P4
task_id: TAG0033
parent: P4-implementation.md
trace_id: TAG0033-P4-review-20260909
created: '2026-09-09'
agent: review
type: review
---

# P4-review — TAG0033 Codex 命令流适配器（C8 独立工程评审）

> 受评对象：`agate/scripts/agate-cmdstream-adapters.py`（+225/-0：`import shlex` + 2 模块常量
> `_CODEX_TRUNC_BOOL_KEYS`/`_CODEX_TRUNC_TEXT_MARKERS` + 助手 `_codex_int_or_none` +
> `class CodexAdapter` + `ADAPTERS["codex"]` 一行）+ `agate/tests/unit/test_agate_cmdstream_adapters.py`
> （+1/-1：`test_bdd_6_detect_consumes_registry_zero_change` :319 精确等值断言改包含式）。
> 角色：`review`（C8：domains=[backend] → review，`agent != main`）。单评审角色，无组长汇总。
> SELF-GATE 协议-脚本语义对齐（A1-A7）由并行的 protocol-alignment-review 单独产出，不在本文范围。
> 评审方式：读实际 `git diff HEAD` + 逐条比对 P2 §5 定论 + 独立复跑 pytest/ruff/consistency，不轻信 P4-implementation.md 文字。

`[PROD_NOT_TOUCHED]`

## 结论

**status: approved**

8 项必核维度全部通过。5 个设计点实现逐条对齐 P2-design.md §5 定论；零改动硬约束在 `git diff`
下守住（仅 2 文件变更）；`test_bdd_6` 断言改包含式语义未弱化；19 条原红灯全绿、回归仅 P7 文档预期
6 条红；ruff / consistency / maintainability 全清。P2-review 的 N1~N4 非阻塞观察 P4 已全部落地。
无 BLOCKER。留 1 条非阻塞观察（CODE-MAP 条目措辞"三平台"未随第四平台更新，见文末）。

---

## 独立复跑输出摘要（加 timeout，未信 P4-implementation.md §5）

| 命令 | 结果 |
|---|---|
| `timeout 120s python3 -m pytest .../test_agate_cmdstream_adapters.py .../test_agate_cmdstream_detect.py -q` | **58 passed / 0 failed**（0.75s）——P3 基线 19 红清零，无回归 |
| `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` | **1383 passed, 6 failed, 2 skipped**（114s）。6 failed 全为 `test_codex_platform_docs.py::test_bdd_22~27`（P7 文档，预期红），**无其它 failed** → 无 P4 回归 |
| `python3 -c "import shlex;print(shlex.join(['/bin/bash','-lc','echo hi']))"` | `/bin/bash -lc 'echo hi'`；`"echo hi" in` 结果 = **True**（BDD-4 子串判据满足） |
| `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!** |
| `timeout 60s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **EXIT 0，0 ERROR**（329 WARNING 全为既有叙事文件引用，与本改动无关） |
| `python3 agate/scripts/check-maintainability.py <task_dir>` | `god_file_count: 0` / `fuzzy_boundary_count: 0`，EXIT 0 |
| `git diff HEAD --name-only` | 仅 `agate/scripts/agate-cmdstream-adapters.py` + `agate/tests/unit/test_agate_cmdstream_adapters.py` |

全量跑完后检查 `agate-workspace/tasks/TAG0033-.../gate-events.jsonl` **未**被测试追加（本次未触发
已知隔离问题），无需 `git checkout` 还原。

---

## 维度 1 —— 5 个设计点实现对齐 P2 §5 定论

**结论：PASS（逐条读 `CodexAdapter` 代码核实）。**

### 设计点 1 —— `probe`（P2 §5 定论 B）

`agate-cmdstream-adapters.py:657-681`：

- basename `startswith("rollout-")`（:667）且 `endswith(".jsonl")` 且**排除** `.jsonl.zstd`（:669）✔
- 只 `f.readline()` 读一行（:671-672），**不** `json.load` 整文件 ✔
- 首行 `json.loads` 判 `type=="session_meta"`（:674）且 `payload` 为 dict（:677）且含
  `cli_version`/`originator`/`id` **任一**（:679，`any(k in payload for k in (...))`）✔
- 异常处理：`try` 包全体，`except (OSError, ValueError, TypeError): return False`（:663/:680-681）——
  路径不存在（OSError）/ 首行空串或非 JSON（`json.JSONDecodeError` ⊂ ValueError）/ `path` 非 str
  提前 `return False`（:664-665）。**绝不抛**。
- 与既有 `DSHAdapter.probe`（:407-408，纯 `endswith` 无 I/O）/ `ClaudeCodeAdapter.probe`（:129-130）
  的"probe 不抛"隐含契约一致——Codex 因引入 `open`/`readline` 自带 try/except，符合 §5 明确要求。
- BDD-1（`test_bdd_1_codex_probe_identifies_rollout` :667-689）覆盖 codex rollout→True /
  claude 内容写入 `rollout-fake.jsonl`（首行 `tool_use` 非 `session_meta`）→False / `.jsonl.zstd`→False /
  `opencode.db`（非 `rollout-` 前缀）→False。独立复跑通过。

### 设计点 2 —— `read_commands` 十字段映射（对照 P2 §4.2）

`:699-842`。逐字段核：

| 字段 | 代码位置 | 对齐 §4.2 |
|---|---|---|
| `platform` | `:808` / `:834` 常量 `"codex"` | ✔ |
| `session_id` | `:700` `os.path.basename(session_path)` | ✔ **未取** `payload.session_id`——grep `session_id` 在 CodexAdapter 区段（:640-861）确认无 `payload["session_id"]` / `.get("session_id")` 取值用于 `CommandRecord.session_id`（唯一来源 = basename） |
| `tool` | `:809` / `:835` 常量 `"exec"` | ✔ |
| `command` | `_join_command`（:759-764）= `shlex.join(str(part) for part in command)`；非 list → `""` | ✔ 独立跑 `shlex.join` 确认 `"echo hi" in` 结果仍 True |
| `ts_start` | `:797` `_codex_int_or_none(payload.get("started_at_ms"))`；缺则 fallback 封套 `timestamp` 经 `_iso8601_to_epoch_ms`（:798-802）；再缺 → `None` | ✔ |
| `ts_end` | `:818` `_codex_int_or_none(payload.get("completed_at_ms"))`；pending → `None`（:812） | ✔ |
| `exit` | `:819-822` `item.get("exit_code")`，`isinstance(int) and not isinstance(bool)` 守卫，**无文本前缀解析**；pending → `None`（:812） | ✔ |
| `exit_signal` | 有 exit_code → `f"exit_code={n}"`（:824）；完成无 exit_code → `item.status` 或 `"status=completed"`（:826-827）；pending → `"pending"`（:813） | ✔ |
| `output_hash` | `:830` `None if truncated else _sha1_hex(str(output or ""))`；pending → `None`（:814） | ✔ |
| `truncated` | `:828` `self._detect_truncated(item)`；pending → `False`（:815） | ✔ |

`_codex_int_or_none`（:634-638）：`bool` 显式排除后 `isinstance(int)`——与 `agate-cmdstream-ir.py:68`
的 `_is_int` 契约一致。

### 设计点 3（同 §5 设计点 2 内）—— 源过滤 + 非 shell 工具事件（BDD-8）

`:722` `obj.get("type") != "event_msg"` → `continue`；`:729`
`not isinstance(item, dict) or item.get("type") != "CommandExecution"` → `continue`；`:737`
`ptype != "item_completed"`（在 `item_started`/`item_updated` 收集后）→ `continue`。

- **单类型正向白名单**（非黑名单）：任何非 `CommandExecution` item（`FileChange` / `Extension` /
  未来新类型）一律不进映射。
- `custom_tool_call`（`apply_patch` / `web__run`）在 fixture 中是 `type=="response_item"`，在**第一层**
  `:722` 就被挡掉。
- 对 fixture `codex-session.jsonl` 的 `apply_patch`（ordinal 4 `response_item` + ordinal 5 派生
  `FileChange`）/ `web__run`（ordinal 6/7）确实不产出记录——`test_bdd_8_codex_non_shell_tool_events_no_record`
  （:843-853）断言 `records` 中无 `"apply_patch"` / `"web__run"` / `"demo.py"` 子串，独立复跑通过。

### 设计点 4（同 §5 设计点 2 内）—— 畸形行（BDD-9）

`:714-718` `json.loads` `except ValueError: skipped += 1; continue`（非 JSON）；`:719-721`
`not isinstance(obj, dict)` → skipped + continue（JSON 数组等非 dict）；`:725-727`
`not isinstance(payload, dict)` → skipped + continue（缺 `payload` 键 → `.get` 返回 None）。
三类坏行均不崩、坏行跳过 + `skipped` 计数 + stderr 一行（:753-756，照 `ClaudeCodeAdapter` :160-163）。
fixture 三类坏行（`this line is not codex json at all` / `["not","a","dict","line"]` /
`{...,"type":"event_msg"}` 无 payload）之后的 `cat big.log` 事件照常产出——
`test_bdd_9_codex_malformed_lines_no_crash`（:859-870）独立复跑通过。

### 设计点 5（P2 §5 设计点 2 / P3 finding #4 / P2 §2.3 R3）—— pending 双判据形态 B 回填

`:699-757`：

- `started` dict（:702）收集 `ptype in ("item_started","item_updated")` 的 `CommandExecution`
  事件（:733-736），键 = `item.id`。
- 主循环 `item_completed` 且 `item.get("status") != "completed"` → 直接产出 pending 记录（:739-742，形态 A）。
- **形态 B 回填**（:747-752）：循环结束后遍历 `started`，`item_id not in emitted_ids`（emitted_ids
  于 :743-744 收集所有已产出 `item_completed` 的 id）→ 补一条 `pending=True` 记录。这即
  `started_ids - completed_ids` 的等价实现。
- pending 记录字段：`exit=None` / `ts_end=None` / `exit_signal="pending"` / `output_hash=None` /
  `truncated=False`（`_build_record` :804-816）。
- **已完成命令不受影响**：`test_bdd_6_codex_unfinished_command_pending`（:806-821）——fixture 的
  `sleep 999`（ordinal 3，`item_started` 无 `item_completed`）回填 1 条 pending；`make build-docs`
  （ordinal 2，已完成 `exit_code==2`）记录 `exit == 2` 不变。独立复跑通过。
- detect 层验证：`test_bdd_13_codex_call_freeze_frozen`（detect 文件 :553）用 `_cx_started` 造
  `item_started` 无 completed → 回填 pending 记录 `ts_start` 非 None、`exit`/`ts_end` 均 None →
  `_records_to_events` 产出 unresolved call → 901s > 兜底 suspect 900s → `FROZEN` + "调用冻结"。通过。

### 设计点（§5 设计点 3）—— session_id 子会话取 basename（BDD-12）

`:700` `session_id = os.path.basename(session_path)`。`test_bdd_12_codex_subagent_session_id_is_child_not_parent`
（:916-935）把子会话 fixture 写入 `rollout-2026-09-08T21-02-03-demo0000-80c6-7000-a000-000000000def.jsonl`
→ 产出记录 `session_id == child_name`（含 `"80c6"` 子自身标识），`!= "demo0000-0000-7000-a000-000000000abc"`
（fixture `codex-subagent-session.jsonl` 首行 `payload.session_id` = 父 id）。因取 basename 而非
`payload.session_id` 绕开陷阱字段。独立复跑通过。`test_bdd_11`（:899-910）确认子会话可独立解析、
`platform=="codex"`、不因缺父上下文返回空。

### 设计点（§5 设计点 5）—— list_sessions cwd fallback（BDD-2/3 + P2-review N1）

`:683-697`：`root = cwd if cwd else os.path.expanduser("~/.codex/sessions")`（:687）——`cwd=None`
与 `cwd=""` 都回落 ✔。`os.walk` 收 `name.startswith("rollout-") and name.endswith(".jsonl") and
not name.endswith(".jsonl.zstd")`（:691-695）✔。返回 `sorted(sessions)`（:697）——**全局路径字符串
排序**（落地 P2-review N2 建议，比"逐目录 sorted"更确定）✔。绝对路径 list（`os.path.join(dirpath, name)`）✔。
`test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root`（:712-737）monkeypatch
`os.path.expanduser` 后对 `cwd in (None, "")` 断言命中 fallback 根——**N1 的"fallback 分支不得成为
未测死代码"已落地**。`test_bdd_3_codex_list_sessions_includes_subagent`（:743-758）确认父
`rollout-P.jsonl` + 子 `rollout-C.jsonl` 同目录都被枚举。独立复跑通过。

### 设计点 4 —— 截断双信号 + truncated⇒output_hash=None

`_CODEX_TRUNC_BOOL_KEYS`（:625）/ `_CODEX_TRUNC_TEXT_MARKERS`（:626-631）模块常量，紧挨 class
上方，带 `# P5 V4 收敛锚` 注释（:624，`_detect_truncated` docstring :770 再次标注）✔。
`_detect_truncated` 为 **classmethod**（:766-787，比照 `DSHAdapter._detect_truncated` :469-497）：
非 dict → False（:775-776）；先查 bool 键集 `isinstance(val, bool) and val`（:777-780）；再查
`aggregated_output` + `formatted_output` 小写子串标记集（:781-787）；**任一命中即 True** ✔。

`truncated=True ⇒ output_hash=None` **无条件**：`_build_record` :830
`output_hash = None if truncated else _sha1_hex(...)`——这是**唯一**一处 hash 计算，被 `truncated`
守卫；pending 分支 :814 亦为 `None`。grep 确认无"truncated 但仍算 hash"的路径 ✔。
`test_bdd_7_codex_truncated_output_hash_none`（:827-837）——fixture `cat big.log` 事件
（`output_truncated:true` bool 键命中 ∪ `aggregated_output` 含 `"[output truncated]"` 文本标记命中）
→ `truncated is True` 且 `output_hash is None`。detect 层 `test_bdd_17_codex_truncated_repeat_not_spin`
（detect 文件 :643）——6× 同命令同 exit 截断输出 → `output_hash=None` 不参与
`(command, exit, output_hash)` 比对 → `verdict != "SPIN"`。独立复跑均通过。

---

## 维度 2 —— 零改动约束守住

**结论：PASS。**

`git diff HEAD --name-only` = 仅 `agate/scripts/agate-cmdstream-adapters.py` +
`agate/tests/unit/test_agate_cmdstream_adapters.py` 两文件。

- `git diff HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py
  agate/platform-notes.md agate/SETUP.md agate/tests/fixtures/` → **空**（零改动确认）。
- `agate-cmdstream-ir.py` `CommandRecord` dataclass（:31-44）十字段名与顺序未动——
  `test_bdd_21_command_record_ten_fields_unchanged`（adapters 文件 :941-951，守护测试）绿。
- `ClaudeCodeAdapter`（:117-288）/ `OpenCodeAdapter`（:294-389）/ `DSHAdapter`（:395-619）
  三 class 体逐行未改（diff 中 `DSHAdapter` 结束行 :619 之后才是新增块）。
- `agate-cmdstream-adapters.py` 改动只有：`import shlex`（:38，插入既有 import 块，字母序位）+
  2 常量 + `_codex_int_or_none` 助手 + `class CodexAdapter` + `ADAPTERS` 加 `"codex": CodexAdapter()`
  一行（:851）。无"顺手重构"、未动 `_sha1_hex`（:69）/ `_iso8601_to_epoch_ms`（:74）定义。
- `codex-session.jsonl` / `codex-subagent-session.jsonl` fixture 是 P3 commit（`b5f3187`）产物，
  `git status` 下无变更——非 P4 改动。
- BDD-21 / P2 §2.2 零改动硬约束守住，无别的改动 → 无 BLOCKER。

---

## 维度 3 —— `test_bdd_6` 断言改动语义未弱化

**结论：PASS。**

`test_agate_cmdstream_adapters.py:319`：
`assert registered == {"claude-code","opencode","dsh"}` → `assert {"claude-code","opencode","dsh"}.issubset(registered)`。
语义从"**恰好**三键"放宽为"**至少**这三键"——这正是 BDD-19 要求（新增第四键 `codex` 后精确等值
必然红）。

该测试其它断言**未被删/弱化**（读 :306-326 全函数）：
- `detect_path.is_file()` 守卫 + `spec.loader.exec_module(detect_mod)` 加载 detect 模块（:310-315）保留。
- P3 追加的 `assert "codex" in registered`（:323）**保留**。
- `detect_src = detect_path.read_text(...)` + `assert "ADAPTERS" in detect_src`（:325-326）**保留**——
  "检测引擎零改动消费注册表"的核心锚点仍在。
- 注释（:320-322）明确写"原语义不删、不弱化"。

`test_bdd_6_adapter_registry_contract`（:296-303）的 `:300` 本就是 `>=` 包含式，未动。

---

## 维度 4 —— 19 条原红灯全绿 + 三态阈值用既有值

**结论：PASS。**

独立复跑 `timeout 120s python3 -m pytest .../test_agate_cmdstream_adapters.py
.../test_agate_cmdstream_detect.py -q` → **58 passed / 0 failed**。

原红灯 19 条（P3 基线）清点：
- `test_agate_cmdstream_adapters.py` 14 条：`test_bdd_1_codex_probe...` / `test_bdd_2_..._enumerates_date_tree` /
  `test_bdd_2_..._cwd_falsy_falls_back...` / `test_bdd_3_..._includes_subagent` / `test_bdd_4_..._maps_ten_fields` /
  `test_bdd_5_..._failed_exit_code_verbatim` / `test_bdd_6_..._unfinished_command_pending` /
  `test_bdd_7_..._truncated_output_hash_none` / `test_bdd_8_..._non_shell_tool_events_no_record` /
  `test_bdd_9_..._malformed_lines_no_crash` / `test_bdd_10_..._session_id_consistent...` /
  `test_bdd_11_..._subagent_session_parses_standalone` / `test_bdd_12_..._subagent_session_id_is_child...` /
  `test_bdd_6_detect_consumes_registry_zero_change`（:319 断言 + :323 `"codex" in`）。
- `test_agate_cmdstream_detect.py` 5 条：`test_bdd_13_codex_call_freeze_frozen` /
  `test_bdd_14_codex_activity_freeze_frozen` / `test_bdd_15_codex_invalid_repeat_spin` /
  `test_bdd_16_codex_normal_progress_no_false_positive` / `test_bdd_17_codex_truncated_repeat_not_spin`。

全部转绿，无回归（守护测试 `test_bdd_21_*` 两条亦绿）。

三态确定性试验阈值 = 既有值：`test_bdd_21_detect_thresholds_unchanged`（detect 文件 :663-672）断言
`CALL_ALERT_FALLBACK==300` / `CALL_SUSPECT_FALLBACK==900` / `ACTIVITY_ALERT==60` /
`ACTIVITY_SUSPECT==300` / `SPIN_THRESHOLD==5` / `REPEAT_WINDOW==10`，通过。Codex 三态用例
（`now=1788400002+901` vs 900、`+301` vs 300、`range(6)` vs SPIN 5）均以 900/300/5 为界，未新造常量。

---

## 维度 5 —— 回归（仅 BDD-22~27 预期红）

**结论：PASS。**

独立复跑 `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` →
**1383 passed, 6 failed, 2 skipped**（114s）。6 failed 逐条：

```
FAILED test_codex_platform_docs.py::test_bdd_22_codex_chapter_capability_matrix
FAILED test_codex_platform_docs.py::test_bdd_23_codex_chapter_version_and_account
FAILED test_codex_platform_docs.py::test_bdd_24_codex_chapter_spawn_agent_schema_evidence_grade
FAILED test_codex_platform_docs.py::test_bdd_25_codex_chapter_cross_reference_no_contradiction
FAILED test_codex_platform_docs.py::test_bdd_26_codex_chapter_model_lineup
FAILED test_codex_platform_docs.py::test_bdd_27_setup_md_codex_section
```

全部为 P7 协议文档阶段（`platform-notes.md` / `SETUP.md` Codex 章）——**预期红**，非 P4 引入。
**无其它 failed** → 无 P4 回归 → 无 BLOCKER。

跑完后 `agate-workspace/tasks/TAG0033-.../gate-events.jsonl` **未**被测试追加（本次未触发已知
测试隔离问题），无需还原。

---

## 维度 6 —— ruff / consistency

**结论：PASS。**

- `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` → **All checks passed!**
  （另单独 `ruff check` 两改动文件亦 All checks passed）。
- `timeout 60s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` →
  **EXIT 0，"仅有 329 个 WARNING，无 ERROR"**。329 WARNING 全为既有叙事文件（`docs/design-notes/` /
  `docs/reviews/` / `CHANGELOG.md`）对已归档文件的引用，与本改动无关。

---

## 维度 7 —— 可维护性（RM-AG0046）

**结论：PASS（无 violations，known-violations.md 非必需）。**

`python3 agate/scripts/check-maintainability.py agate-workspace/tasks/TAG0033-codex-cmdstream-adapter`
→ `god_file_count: 0` / `fuzzy_boundary_count: 0`，EXIT 0。任务目录下无
`known-violations.md`（不需要——violations 为空）。`agate-cmdstream-adapters.py` 现 861 行，未触发
god-file 阈值。C8 checklist「violations 非空须读 known-violations.md 登记理由」不适用。

---

## 维度 8 —— CODE-MAP / 新增文件核对表

**结论：PASS（P4-implementation.md 如实声明无新增源码文件）。**

- `git diff HEAD --name-only` 确认本阶段**无新增文件**（fixture 是 P3 产物）。
- `P4-implementation.md` §1 表格 + §4「新增文件核对表」如实写「新增源码文件：**无**」/「（无）」，
  并说明 `CodexAdapter` class + 2 常量 + 1 助手加入既有 `agate-cmdstream-adapters.py`。
- 该文件已在 `agate-workspace/agents/CODE-MAP.md:33` 登记（命令流检测族条目）。

> **非阻塞观察 O1**：CODE-MAP.md:33 条目描述为「agate-cmdstream-adapters.py（**三平台**命令流适配器：
> Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd，显式注册表 ADAPTERS）」——新增 Codex 后
> 实为四平台、且 rollout JSONL 源未列入描述。P4-implementation.md §4 称「条目语义不变——仍是三平台
> 命令流适配器」略欠准确（条目现**低描述**）。此非零改动约束禁改项（P2 §2.2 未列 CODE-MAP），
> 建议 P7（本就触协议文档面）或主 Agent 顺手把「三平台」→「四平台」+ 补「Codex rollout JSONL」。
> **不阻断 P4 推进**——不影响任何 BDD / 测试 / gate。

---

## P2-review N1~N4 落地核对

| # | 观察 | P4 落地 |
|---|---|---|
| N1 | `list_sessions` cwd 假值 fallback 分支无测试覆盖 | ✔ `test_bdd_2_codex_list_sessions_cwd_falsy_falls_back_to_default_root`（:712-737）monkeypatch expanduser + `cwd in (None,"")` 双值断言 |
| N2 | 排序应为全局 `sorted()` 全路径而非逐目录 | ✔ `:697` `return sorted(sessions)` 全局路径排序 |
| N3 | `test_bdd_7_fixture_sanitized` 对 Codex 连字符 uuid 无形态负向断言 | ✔ `:353-365` 新增：无形似真实连字符 hex uuid、无 `01a0…` 前缀、无 `/.codex/sessions/` 路径 |
| N4 | `ts_start=None` 兜底与 `ir.py:39` `ts_start: int` 提示 | 记录备查项，非问题——`_build_record` :797-802 与 `DSHAdapter._build_record` :591 对 `ts_start` 传 `None` 行为一致，detect CLI 跳过 `ts_start is None`（`_records_to_events` :538-539 同）|

---

## 覆盖声明

- **已覆盖**：dispatch-context 8 项必核维度全部逐项给结论 + 证据（文件:行 / BDD 编号 / P2 §5 设计点 /
  独立复跑输出）。P2-review N1~N4 落地额外核对。
- **未覆盖**：SELF-GATE 协议-脚本语义对齐（A1-A7）——由并行 protocol-alignment-review 子 Agent 产出，
  按分工不在本 C8 工程评审范围。真机验证清单 V1~V8 属 P5/P6 范畴，未重跑。
- 视觉能力：`domains: [backend]` / `ui_affected: false`，无视觉需求，无 `[CAPABILITY_GAP]`。

`[PROD_NOT_TOUCHED]`
