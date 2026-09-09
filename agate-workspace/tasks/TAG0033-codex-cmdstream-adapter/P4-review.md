---
status: approved
phase: P4
task_id: TAG0033
parent: P4-implementation.md
trace_id: TAG0033-P4-review-20260909-r2
created: '2026-09-09'
agent: review
type: review
review_round: 2
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

---

## 第 2 轮复评（F1 修复）

> 受评对象：P5→P4 单步回退（retreat `52fe210` / debt `9a7a1f9`）后 implementer 重试 #1 的 F1（DEBT0035）
> 定向修复。`git diff HEAD`（HEAD = `9a7a1f9`）覆盖：`agate/scripts/agate-cmdstream-adapters.py`
> （+33/-2：模块级 helper `_codex_is_finished` + `pending` 判据 1 行 + class docstring）+
> `agate/tests/fixtures/cmdstream/codex-session.jsonl`（`make build-docs` `status` completed→failed +
> 追加 6 行 `ls /demo/nonexistent-xyz` 真机 `status:"failed"` 重复失败簇）+
> `agate/tests/unit/test_agate_cmdstream_adapters.py`（`test_bdd_5_*` Given/Then 改真机形态 + 新守护
> `test_bdd_5_codex_failed_status_not_pending_guard`）+ `agate/tests/unit/test_agate_cmdstream_detect.py`
> （`_cx_exec` 加 `status` 参 + `test_bdd_15_*` 用 `status="failed"`）+ `agate/platform-notes.md`（Codex 章
> 「命令流适配」小节 +1 bullet）+ 4 个任务 md 的 BASELINE_CHANGE/progress。
> 评审方式：读实际 `git diff HEAD` + 逐条比对 DEBT0035 closure_criteria + 独立复跑
> pytest/ruff/consistency + **自己对 implementer 造的真机 rollout 复跑 detect**，不轻信 P4-implementation.md 文字。
> 本轮只审 F1 修复面，不重审第 1 轮已 approved 的部分。

`[PROD_NOT_TOUCHED]`

### 结论

**status: approved**（第 1 轮结论保留）

9 项必核维度全部通过。`_codex_is_finished` 三判据逻辑与 DEBT0035 / P2 §5 BASELINE_CHANGE 定论逐条对齐，
四个边界（`status="failed"+exit_code+completed_at_ms` → finished；`in_progress` 无信号 → pending；
`item_started` 无 completed → 走 pending 回填；`exit_code=0` → finished / `exit_code=False`(bool) → 不算）
均正确。零改动硬约束在 `git diff HEAD` 下守住（`detect.py` / `ir.py` diff 为空；CodexAdapter 的
probe/list_sessions/`_detect_truncated`/`_join_command`/session_id/ADAPTERS/`test_bdd_6:319` 均未被本轮碰）。
独立复跑：3 文件 **67 passed**、全量单测 **1390 passed / 0 failed / 2 skipped**、ruff clean、consistency
EXIT 0 / 0 ERROR。**真机复验**：对 implementer 造的 rollout
（`rollout-2026-09-09T11-29-48-01a08436-...jsonl`，仍在 `~/.codex/sessions/2026/09/09/`）自行复跑
`detect --platform codex --now +5s` → **`VERDICT: SPIN`** / EXIT 0，`read-commands` 7 条真机
`status="failed"` 命令全部产出 `exit=2` / `exit_signal="exit_code=2"` / `output_hash` 非 None /
`ts_end` 非 None（非 pending 空壳）。BASELINE_CHANGE 注记如实、未篡改 BDD 判定语义、DEBT0035 引用正确。
无 BLOCKER。

---

### 独立复跑输出摘要（加 timeout，未信 P4-implementation.md 重试 #1 节）

| 命令 | 结果 |
|---|---|
| `timeout 120s python3 -m pytest .../test_agate_cmdstream_adapters.py .../test_agate_cmdstream_detect.py .../test_codex_platform_docs.py -q` | **67 passed / 0 failed**（0.90s） |
| `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` | **1390 passed, 2 skipped**（114s）——0 failed，无回归（第 1 轮的 BDD-22~27 P7 文档红灯已在 P4 protocol-docs 批转绿） |
| `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` | **All checks passed!** |
| `timeout 90s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **EXIT 0**，「仅有 329 个 WARNING，无 ERROR」（WARNING 全为既有叙事文件引用，与本改动无关） |
| `git diff HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py` | **空**（零改动确认） |
| 真机 `python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now 1788924619` | **`VERDICT: SPIN`**（窗口 10 内重复 7 次 ≥ 5）/ EXIT_CODE 0 |
| 真机 `read-commands codex <rollout>` | 7 条，每条 `exit=2` / `exit_signal="exit_code=2"` / `output_hash="fca0f86e…5a41"` / `ts_end` 非 None |
| fixture 侧 `detect codex-session.jsonl --platform codex --now 1788400887` | **`VERDICT: SPIN`**（`ls /demo/nonexistent-xyz`, 2, `28a08b08…626c` 重复 6 次）+ `sleep 999` 未结束提示（正常）|

> ⚠️ `git diff HEAD` 中 `agate-workspace/tasks/TAG0033-.../gate-events.jsonl` 有 +2 行
> （`check-gate.py P4` exit 2 + `state_transition from=P5 to=P4`，ts `2026-09-09T03:18:28Z`）——这是
> **回退 `52fe210` 的 pre-commit hook 台账**（时间戳 = retreat 提交时刻，非本次复跑），非测试污染。
> 本轮独立复跑后该文件**未**被再追加（已知测试隔离问题未触发），无需 `git checkout` 还原；这 2 行应随
> P4 重试 commit 一并提交。

---

### 9 项必核维度逐项结论

#### 1 — `_codex_is_finished` 逻辑正确 —— PASS

`agate-cmdstream-adapters.py:641-663`。「已结束」= 三者任一：

```python
if isinstance(item, dict):
    if item.get("status") in ("completed", "failed"):
        return True
    raw_exit = item.get("exit_code")
    if isinstance(raw_exit, int) and not isinstance(raw_exit, bool):
        return True
return isinstance(payload, dict) and payload.get("completed_at_ms") is not None
```

与 DEBT0035 recommendation / P1 §4.1 + P2 §5 设计点 2 的 BASELINE_CHANGE 口径逐字对齐。逐边界核实：

| 场景 | 判定 | 结论 |
|---|---|---|
| `status="failed"` + `exit_code=137` + `completed_at_ms` | `status in {...}` 命中 → `True` → 非 pending | ✔ |
| `status="in_progress"` + `exit_code=None` + 无 `completed_at_ms` | 三判据皆不命中 → `False` → pending | ✔ |
| `item_started` 事件（无 status/exit_code/completed_at_ms） | 主循环里 `item_started`/`item_updated` 收进 `started` 后 `continue`，**不经** `_codex_is_finished`；结束时 `started - emitted_ids` 回填 `pending=True` | ✔ |
| 边界 `exit_code=0`（int 非 bool） | `isinstance(0, int) and not isinstance(0, bool)` → `True` → finished | ✔ |
| 边界 `exit_code=False`（bool） | `isinstance(False, bool)` → `not …` 为 False → 该分支不命中；无其它终态信号则 pending | ✔（isinstance bool 显式排除，与 `_codex_int_or_none` / `ir.py:_is_int` 契约一致）|
| `item_completed` 但 `status="in_progress"` 且无 completed_at_ms/exit_code（理论态）| `False` → pending | ✔（口径正确落到"真·未结束"）|

`_codex_is_finished` 仅在主循环 `item_completed` 分支被调用（`:766` `pending = not _codex_is_finished(payload, item)`），
回填分支恒 `pending=True`——与 P2 §5「`item_completed` 事件在改口径下几乎恒为已结束」一致。逻辑正确。

#### 2 — `_build_record` 非 pending 路径对 `status="failed"` 无遗漏 —— PASS

`:845-869`（非 pending 分支）：

- `ts_end = _codex_int_or_none(payload.get("completed_at_ms"))`——真机 failed item 带 `completed_at_ms` → int，非 None ✔
- `raw_exit = item.get("exit_code")` → `137` / `2`，`isinstance int and not bool` 守卫 → `exit_code=137` ✔
- `exit_code is not None` → `exit_signal = f"exit_code={exit_code}"`（即 `"exit_code=137"` / `"exit_code=2"`）✔
- `truncated = self._detect_truncated(item)`；`output_hash = None if truncated else _sha1_hex(str(output or ""))` ✔
- 真机复跑实证：7 条 `status="failed"` 命令 `exit=2` / `exit_signal="exit_code=2"` / `output_hash` 非 None /
  `ts_end` 非 None——全字段完整，非 pending 空壳。

DEBT0035 closure_criteria 第 1 条（`status=="failed"` 且带 exit_code → `exit=<非0 int>` / `ts_end=<完成时刻>` /
`output_hash=<真实哈希>`，非 pending）**满足**。

#### 3 — `started_ids - emitted_ids` 回填不再误收 `status="failed"` —— PASS

`:764-771`：`item_completed` 事件 → `pending = not _codex_is_finished(...)`（failed → `False`）→
`_build_record(..., pending=False)` → `emitted_ids.add(item_id)`。`:774-779` 回填循环
`if item_id in emitted_ids: continue`——failed item 的 id 已在 `emitted_ids` → **跳过**，不会二次补 pending。
读代码确认无双产出路径（`item_id is None` 时既不进 `started` 也不进 `emitted_ids`，无影响）。

#### 4 — 零改动约束仍守住 —— PASS

- `git diff HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py` → **空**。
- `agate-cmdstream-adapters.py` `git diff` 仅：模块级 `_codex_is_finished` helper 新增（`_codex_int_or_none`
  之后）+ `pending` 判据 1 行（`:766`）+ `CodexAdapter` class docstring 改口径（`-2/+4`）。
- `CodexAdapter.probe`（:684-708）/ `list_sessions`（:710-724）/ `_detect_truncated`（:793-814）/
  `_join_command`（:786-791）/ `session_id = os.path.basename`（:727）/ `ADAPTERS["codex"]` / `_build_record`
  的截断+session_id+十字段映射主体——`git diff` 下**均未出现**，未被本轮碰。
- `test_agate_cmdstream_adapters.py:319`（`test_bdd_6_detect_consumes_registry_zero_change` 的
  `.issubset` 断言）——`git diff` 只落在 `:788-820`（`test_bdd_5` 区），:319 未动。
- `CommandRecord` 十字段（`ir.py`）未动，`test_bdd_21_*` 守护测试仍绿。

#### 5 — 测试充分性 —— PASS

- 独立复跑 3 文件 → **67 passed / 0 failed**（第 1 轮基线 58 + F1 批 codex_platform_docs 转绿计入 + 新守护 1）。
- `test_bdd_5_codex_failed_exit_code_verbatim`：Given fixture `make build-docs` 改 `status="failed"`；Then
  `r.exit == 2` / `r.exit is not None` / `r.exit_signal == "exit_code=2"` / `r.ts_end is not None` /
  `r.output_hash is not None`——四断言实质锁定"不被误判 pending"。✔
- `test_bdd_15_codex_invalid_repeat_spin`：`_cx_exec(..., status="failed")` × 6 + `exit_code=2` →
  `_records_to_events` → detect → `verdict == "SPIN"`。✔（真机形态覆盖）
- `test_bdd_6_codex_unfinished_command_pending`：**未改**，仍测 `sleep 999`（`item_started` 无
  `item_completed`，fixture 中 `grep -c "sleep 999"` = 1，样本仍在）→ `exit is None` / `ts_end is None`
  / `exit_signal == "pending"`；`make build-docs`（现 `status="failed"`）`done[0].exit == 2` 走新 finished
  路径仍成立。口径未被破坏。✔
- 新守护 `test_bdd_5_codex_failed_status_not_pending_guard`（无新 BDD 编号）：读断言体——
  `failed = [r for r in records if "ls /demo/nonexistent-xyz" in r.command]`；`assert len(failed) == 6`；
  循环内 `assert r.exit_signal != "pending"` / `r.exit == 2` / `r.ts_end is not None` /
  `r.output_hash is not None`——实质断言，非 `pass` / 弱断言。✔
  DEBT0035 closure_criteria 第 2 条（P3 测试覆盖 `status=="failed"` 形态 + fixture 含真机 failed 样本）满足。

#### 6 — 回归 —— PASS

`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` → **1390 passed, 2 skipped**（114s），
**0 failed**。（第 1 轮遗留的 BDD-22~27 P7 文档预期红，已在其后 P4 protocol-docs 批 `90e00db` 转绿——
本轮不涉及。）无别的 failed → 无 P4 回归 → 无 BLOCKER。跑完后 `gate-events.jsonl` 未被测试追加。

#### 7 — ruff / consistency —— PASS

- `~/.venvs/agate-dev/bin/ruff check agate/` → **All checks passed!**（implementer 自述首轮 SIM103
  命中 helper 末尾 if→return，已改直接 `return` 条件——现 `:663` 即为 `return isinstance(...) and ...`
  单行，无 SIM103）。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 脚本）→ **EXIT 0**，
  「仅有 329 个 WARNING，无 ERROR」。329 WARNING 全为既有叙事文件（`docs/reviews/` / `CHANGELOG.md`）
  对已归档文件的引用，与本改动无关。
  DEBT0035 closure_criteria 第 4 条（全量 pytest 全绿 + consistency 0 ERROR）满足。

#### 8 — 真机复验 —— PASS（SPIN）

`P4-progress.md` 重试 #1 段给出 implementer 造的 rollout：
`~/.codex/sessions/2026/09/09/rollout-2026-09-09T11-29-48-01a08436-f250-7dc2-b7e2-8d254686de7e.jsonl`
（`ls -la` 确认文件在，76490 bytes，codex-cli 0.153.4 + ChatGPT 登录）。**评审自行复跑**（未信 progress 文字）：

```
$ python3 agate/scripts/agate-cmdstream-detect.py read-commands codex <rollout>
→ 7 条 CommandRecord，每条：
   command="/bin/bash -lc 'ls /nonexistent-xyz-r1check .'"
   exit=2   exit_signal="exit_code=2"   output_hash="fca0f86ef91d0880417a3541041e402cb8be5a41"
   ts_start / ts_end 均非 None（非 pending）

$ python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now 1788924619
VERDICT: SPIN
  · 空转：同 (命令, exit, 输出哈希) 组合 (…, 2, 'fca0f86e…5a41') 在窗口 10 内重复 7 次 ≥ 5
    → 疑似逻辑空转，建议核查
EXIT_CODE: 0
```

pre-fix 对照（`.archived/p6-pre-retreat-20260909/real-machine-p6.md` V6 ③ + `52fe210` 诊断）：同类真机
spin 会话 `now=+5s → NORMAL` / `now=+950s → FROZEN`，判不出 SPIN。**修复后 SPIN 复现通过**，`read-commands`
对 `status="failed"` 命令产出 `exit=2` 非 pending。DEBT0035 closure_criteria 第 3 条（detect 对真机重复
失败会话判 SPIN）满足。

fixture 侧对照亦复跑确认：`detect codex-session.jsonl --platform codex --now 1788400887` → `VERDICT: SPIN`
（`ls /demo/nonexistent-xyz`, 2, `28a08b08…626c` 重复 6 次）+ 并行给出 `sleep 999` 未结束调用提示（22s <
兜底 300s，判"正常"）——证明"真·未结束"与"已结束 failed"两条路径在同一 fixture 里并存且各走各的。

#### 9 — BASELINE_CHANGE 注记恰当性 —— PASS（恰当，未篡改 BDD 语义，DEBT0035 引用正确）

| 位置 | 注记内容 | (a) 如实 | (b) 未改 BDD 判定语义 | (c) DEBT0035 引用 |
|---|---|---|---|---|
| `P1-requirements.md` §4.1（`item.status`） | `[BASELINE_CHANGE: spike 取样未覆盖 "failed" 终态]`——补真机 `status` 取值集 = completed/failed/in_progress；「已结束」判据据此改口径 | ✔ 与真机证据一致 | ✔ 明写"Given/When/Then 语义不变，仅补充真机事实"，无 BDD 条款改动 | ✔ 指向 P2 §5 设计点 2 BASELINE_CHANGE / DEBT0035 |
| `P1` BDD-5 Given | `item.status` 从 `"completed"` 改 `"failed"` + `[BASELINE_CHANGE: item.status 从 "completed" 改为 "failed"]` | ✔ 原 Given 自相矛盾（"失败命令"却 `status="completed"`），改后贴合真机 | ✔ Then 判定语义不变（仍是"失败命令 exit_code 非 0 如实映射，不回落 None"），仅**加强**断言（`ts_end`/`output_hash` 非 None） | ✔ 括注 DEBT0035 |
| `P1` BDD-6 Given | `"item.status != completed"` 措辞**收紧**为"真·未结束"（有 `item_started`/`item_updated` 无 `item_completed`，且无 `completed_at_ms`/`exit_code`）+ `[BASELINE_CHANGE: …措辞收紧…]` | ✔ 原措辞基于不完整 spike；`status:"failed"` 确是已结束终态 | ✔ Then 不变（未结束→`exit is None`/`ts_end is None`/`"pending"`；已完成不受影响）——只收紧 Given 的"未结束"定义，未动判定 | ✔ 指向 P2 §5 设计点 2 BASELINE_CHANGE / DEBT0035 |
| `P2-design.md` §5 设计点 2 | `[BASELINE_CHANGE: pending 判据从 "status != completed" 收紧为「无终态信号才算 pending」]` + 三判据展开（`status ∈ {completed,failed}` 或 `completed_at_ms` 非 None 或 `exit_code` int 非 bool）+ 抽 `_codex_is_finished` helper | ✔ 与实现逐字对齐 | ✔ 设计点非 BDD 条款；§5 原"`item_completed` 且 `status != "completed"` 直接产出 pending"句被替换为新口径，合理 | ✔ 正文明写 DEBT0035 |
| `P2-design.md` R3（风险缓解表） | 判据更新为「无终态信号才算 pending」+「P6 补真机 `status:"failed"` 样本」 | ✔ | ✔ 风险表非 BDD 判定 | ✔ 括注 DEBT0035 |

五处注记均：(a) 如实反映改动；(b) 未改任何 BDD 的 Given/When/Then **判定语义**（Then 一律保留，Given
改动限于"贴合真机形态"或"收紧过宽措辞"，并显式声明语义不变）；(c) DEBT0035 引用正确。DEBT0035
closure_criteria 第 5 条（platform-notes.md Codex 章含真机 status 取值集 + P1 §4.1 补 "failed" 终态）
——`agate/platform-notes.md:88` 新 bullet 含 `payload.item.status` 真机取值集（completed/failed/in_progress）
+ `_codex_is_finished`「有终态信号」判已结束口径 + 旧口径误判说明（DEBT0035）；P1 §4.1 已补——满足。
无实质篡改 → 非 BLOCKER，无需在 review 里降级。

---

### DEBT0035 closure_criteria 核对

| # | 准则 | 结论 |
|---|---|---|
| 1 | CodexAdapter 对 `status=="failed"` 带 exit_code 的 item → `exit=<非0 int>` / `ts_end=<完成时刻>` / `output_hash=<真实哈希>`，非 pending | ✔ 维度 2 + 真机复跑实证 |
| 2 | P3 测试覆盖 `status=="failed"` 形态；fixture 含真机 failed 样本 | ✔ 维度 5（`test_bdd_5_*` + 守护 + fixture +7 行）|
| 3 | detect 对真机重复失败会话（复跑 P6 V6 ③）判 SPIN | ✔ 维度 8（评审自行复跑 → `VERDICT: SPIN`）|
| 4 | 全量 pytest 全绿 + consistency 0 ERROR + P5/P6 重新通过 | ✔ pytest 1390 passed / consistency EXIT 0；P5/P6 属后续阶段（本轮为 P4 review） |
| 5 | platform-notes.md Codex 章含真机 status 取值集；P1 §4.1 补 "failed" 终态 | ✔ 维度 9 |

DEBT0035 可在 P5/P6 重新通过后由主 Agent 置 `status: resolved`（本轮不改 debt 台账）。

---

### 覆盖声明（第 2 轮）

- **已覆盖**：dispatch-context「必须核验」9 项全部逐项给结论 + 证据（文件:行 / `git diff` / DEBT0035
  closure_criteria / 独立复跑输出 / 评审自跑真机 detect）。DEBT0035 五条闭环准则额外核对。
- **未覆盖**：SELF-GATE 协议-脚本语义对齐（并行 protocol-alignment-review 第 3 轮，按分工不在本 C8 范围）；
  P5 gate_commands / P6 完整验收清单（后续阶段）。
- 视觉能力：`domains: [backend]` / `ui_affected: false`，无 `[CAPABILITY_GAP]`。
- 第 1 轮非阻塞观察 O1（CODE-MAP「三平台」措辞）本轮未涉及，仍留待 P7 / 主 Agent 顺手处理。

`[PROD_NOT_TOUCHED]`
