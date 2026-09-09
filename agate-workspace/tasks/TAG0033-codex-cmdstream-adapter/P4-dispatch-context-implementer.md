---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: implementer
---

<dispatch_guide>
> 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片（参考规范）。

### 目标

在 `agate/scripts/agate-cmdstream-adapters.py` 实现 `CodexAdapter` class + `ADAPTERS` 注册表加一行，
让 P3 的 19 条红灯测试（`test_agate_cmdstream_adapters.py` 14 条 + `test_agate_cmdstream_detect.py` 5 条）
转绿；产出 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（声明
`implementation_dir:`）。**这是 P2 dispatch_plan 的 `adapter-core` 批**——`protocol-docs`（platform-notes.md /
SETUP.md）是 **P7** 的事，本阶段**不碰**。

### 必须完成（对齐 P2-design.md §5 五设计点定论）

1. **`CodexAdapter(CommandStreamAdapter)` class**（放在 `DSHAdapter` 之后、`ADAPTERS` 字典之前），实现三方法：
   - **`probe(self, path)`**（P2 §5 设计点 1）：`os.path.basename(path)` 匹配 `rollout-*.jsonl`（**排除
     `.jsonl.zstd` 等**）→ 再 `open` 只 `readline()` 第一行 `json.loads`，判 `type=="session_meta"` 且
     `payload` 含 codex 标记（`cli_version` / `originator` / `id` 任一）。任何异常（路径不存在 / 首行非
     JSON / 非 dict）→ `return False`，**不抛**（比照 `DSHAdapter.probe` 的异常处理）。
   - **`list_sessions(self, cwd)`**（P2 §5 设计点 5 + P2-review N1）：根目录 =
     `cwd if cwd else os.path.expanduser("~/.codex/sessions")`（`cwd` 为 `None` 或 `""` 都回落默认——
     P3 有 `cwd=None` / `cwd=""` 用例）。`os.walk` 遍历，收集 basename 匹配 `rollout-*.jsonl` 的文件，
     返回**绝对路径 list**，按路径字符串 `sorted()`（文件名内嵌 ISO8601，字典序≈时间序）。父会话与
     `spawn_agent` 子会话都是独立 `rollout-*.jsonl`、同 `YYYY/MM/DD/` 扁平目录 → `os.walk` 天然同时枚举
     （P1 §4.2 实测），**不需要**特殊处理子会话枚举。
   - **`read_commands(self, session_path)`**（P2 §5 设计点 2/3/4）：逐行 `json.loads`，**坏行
     try/except + continue**（非 JSON / JSON 数组非 dict / 缺 `payload` 键——P3 BDD-9 三类），不整体崩。
     - **源过滤**：`type=="event_msg"` 且 `payload.get("type")=="item_completed"` 且
       `payload["item"].get("type")=="CommandExecution"` → 产出 `CommandRecord`。其它事件类型
       （`apply_patch`→FileChange / `web__run`→Extension / `message` / `reasoning` 等）**不产出记录**
       （P3 BDD-8）。
     - **十字段映射**（`CommandRecord` 见 `agate-cmdstream-ir.py:31-44`，**不改这个 dataclass**）：
       `platform="codex"` / `session_id=os.path.basename(session_path)`（P2 §5 设计点 3——**不取
       `session_meta.session_id`**，那对子会话是父 id；basename 对主/子会话都天然指向自身且可定位回文件）/
       `tool="exec"`（常量）/ `command=shlex.join(item["command"])`（`item["command"]` 是数组
       `["/bin/bash","-lc","echo hi"]`——`shlex.join` → `/bin/bash -lc 'echo hi'`，P3 BDD-4 断言
       `"echo hi" in command` 仍 True）/ `ts_start=payload.get("started_at_ms")` /
       `ts_end=payload.get("completed_at_ms")` / `exit=item.get("exit_code")`（**直取数字**，P1 §4.1.1；
       缺字段 / 未结束 → `None`）/ `exit_signal=f"exit_code={n}"`（有 exit 时）或 `"pending"`（未结束时）/
       `output_hash=_sha1_hex(item.get("aggregated_output",""))`（`truncated` 时 `None`——用既有
       `_sha1_hex` 助手 line 68）/ `truncated=` 截断双信号（见下）。
     - **未结束命令（pending，P3 BDD-6 + P3 finding #4 + P2 §2.3 R3）**：fixture 用的是**双判据形态 B**
       ——`item_started`（有 `item.id` 的 `CommandExecution` 起始事件）但同 `item.id` **无对应
       `item_completed`**。实现须收集 `started_ids`（从 `item_started` / `item_updated` 类事件）与
       `completed_ids`（从 `item_completed`），对 `started_ids - completed_ids` 的每个 id **补一条 pending
       记录**：`exit=None` / `ts_end=None` / `exit_signal="pending"` / `ts_start=` 起始事件的
       `started_at_ms`（或该 item 起始事件里的时间戳）。比照 `DSHAdapter` 未结束 call 补记录逻辑
       （`agate-cmdstream-adapters.py:556-560`）。已完成命令记录不受影响。
     - **截断双信号（P2 §5 设计点 4）**：新增 `classmethod _detect_truncated(cls, item)`（比照
       `DSHAdapter._detect_truncated` @ line 468-496）+ 2 个模块级常量 `_CODEX_TRUNC_BOOL_KEYS`
       （item 上的显式布尔字段名候选，如 `truncated` / `output_truncated`）+ `_CODEX_TRUNC_TEXT_MARKERS`
       （`aggregated_output` 里的字面量标记候选，如 `"[output truncated]"` / `"… (truncated)"`）。
       **任一命中 → `truncated=True`**。加注释 `# P5 V4 收敛锚：Codex 截断标记形态实测后收敛此常量/方法`
       （P1 §4.1.2 / §7 V4）。`truncated=True` ⇒ `output_hash=None` **无条件**（IR 铁律，不放宽）。
2. **`ADAPTERS` 字典加一行**：`"codex": CodexAdapter(),`（键名 `"codex"`——P1 §8 SUGGEST ① 已采纳）。
3. **`test_agate_cmdstream_adapters.py` 的 `test_bdd_6_detect_consumes_registry_zero_change`（约 :317）**
   （P3 BDD-19）：该测试原有 `assert registered == {"claude-code", "opencode", "dsh"}` 精确等值断言——
   加 `"codex"` 键后必失败。**改为**：`assert {"claude-code", "opencode", "dsh"}.issubset(registered)`
   或 `assert registered >= {"claude-code", "opencode", "dsh"}`（包含式）。P3 已在其后追加
   `assert "codex" in registered`——保留。**语义不变**（该测试验证「检测引擎零改动消费注册表」——
   只是从"恰好三键"放宽为"至少这三键"）。不删 / 不弱化该测试其它断言。

### 绝对不能做

1. **不改** `agate/scripts/agate-cmdstream-detect.py`（检测引擎 + 阈值常量）——P3 有
   `test_bdd_21_detect_thresholds_unchanged` 守护，改了会红。
2. **不改** `agate/scripts/agate-cmdstream-ir.py` 的 `CommandRecord` dataclass 十字段——P3 有
   `test_bdd_21_command_record_ten_fields_unchanged` 守护。
3. **不改** `ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter` 的 class 体（BDD-21）。可**复用**其
   模块级助手（`_sha1_hex` 等），但不动它们的方法。
4. **不碰** `agate/platform-notes.md` / `agate/SETUP.md`——那是 P7。`test_codex_platform_docs.py` 的
   BDD-22~27 会**保持红**，这是**预期的**（P7 补文档后转绿）。**不要**为了让它们绿去改文档。
5. **不动** P1-requirements.md / P2-design.md / P3-test-cases.md（基线文件）。P4 发现 BDD 矛盾 → 标
   `DESIGN_GAP`，不直接改。范围外改动 → 标行首 `[SCOPE+]`，不擅自做。
6. **不新造阈值 / 不新增 gate 脚本 / CHECK**（P0-brief 核心约束、DEBT0025）。

### 完成判据（P4 自查，非 gate）

- `timeout 120s python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py agate/tests/unit/test_agate_cmdstream_detect.py -q`
  → **全绿**（原 19 failed → 0 failed；既有测试无回归）
- `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` → 仅 `test_codex_platform_docs.py` 的
  BDD-22~27（6 条）failed（预期，P7 转绿），其余全绿。**若还有别的 failed → 是你引入的回归，必须修**。
- `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` → All checks passed（新代码符合 ruff：
  `b"..."` 字面量而非 `.encode()`、无未用 import 等）
- `timeout 60s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR
  （本阶段不改协议文档，应无变化——跑一遍确认没连带破坏）

### 上游关联

- **P2-design.md**（同目录，已 approved）——**§5 五设计点定论是实现权威**；§2.1 改什么 / §2.2 不改什么 /
  §2.3 风险（R3 pending 双判据 / R5 session_id 陷阱）/ §4.2 十字段映射表 / §7 gate_commands / §8 files_to_read
- **P3-test-cases.md**（同目录）——每条测试用例的断言要点 + 预期红灯原因（实现让它们转绿的目标）
- **P2-review.md**（同目录）——N1（cwd fallback，P3 已补用例）/ N2（排序措辞，实现按路径 sorted 即可）/
  N3（P3 已在 test_bdd_7 落地，你实现时确保 fixture 已脱敏——fixture 已由 P3 建好，你**不需要**改 fixture，
  除非实现暴露 fixture 数据形态错误，那种情况标 `DESIGN_GAP` 报告）/ N4（`ts_start: int` 提示 vs None——
  与 DSHAdapter 既有行为一致，detect CLI 已跳过 `ts_start is None`，照做即可）
- **P1-requirements.md**（同目录）——§4 spike 实测事实（§4.1 事件形态 / §4.1.1 exit_code / §4.2 子会话
  字段 / §4.1.2 截断待定）+ §6 BDD-1~21 原文
- **P3 finding #4**（test-designer 返回）：fixture 的 pending 用双判据形态 B（`item_started` 无
  `item_completed`）——实现必须做 `started_ids - completed_ids` 回填，否则 BDD-6 / BDD-13 合法保持红。

### 输入文件（P2 §8 files_to_read，按此读，勿全目录扫）

1. `agate/scripts/agate-cmdstream-adapters.py:391-627`（`DSHAdapter` 近亲——`probe` / `list_sessions`
   结构 / `_detect_truncated` 双信号 @ 468-496 / 未结束 call 补记录 @ 556-560 / `_build_record` @ 565-618 /
   `_sha1_hex` @ 68 / `ADAPTERS` @ 623-627）
2. `agate/scripts/agate-cmdstream-ir.py:31-44`（`CommandRecord` 十字段 dataclass——只读，零改动）
3. `agate/tests/unit/test_agate_cmdstream_adapters.py:294-342`（`test_bdd_6` @ :317 改包含式 /
   `test_bdd_7` 脱敏清单 / 既有 `test_bdd_2~5` 单测范式）+ 新增的 14 条 Codex 用例（全读，理解断言目标）
4. `agate/tests/unit/test_agate_cmdstream_detect.py:300-373`（三态确定性试验范式 `_run_detect` / `_ev`）
   + 新增的 5 条 Codex 三态用例
5. `agate/tests/fixtures/cmdstream/codex-session.jsonl` + `codex-subagent-session.jsonl`（P3 已建——
   实现要能正确解析它们；**不改** fixture，除非发现数据形态错误 → 标 `DESIGN_GAP`）
6. `agate/tests/fixtures/cmdstream/dsh-session.jsonl`（对照——fixture 结构 + 脱敏范式）
7. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§5 设计点全文 + §2 影响面梳理）
8. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md`（用例断言要点表）
9. `agate/assets/execution-roles/implementer.md`（你的角色定义）
10. `agate/phase-cards/P4-implementation.md`（本阶段卡片——产出规格 / gate 规则 / 新增文件核对表）
11. `AGENTS.md`（worktree 根——改脚本 TDD 工作流、双工作区纪律、工具纪律、ruff 合并强制）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P3（P4 产出 commit 随 P4-implementation.md
  推进 P4）/ judge.enabled=true。P3 已 commit（`b5f3187`）。用系统 `python3`（/usr/bin/python3）跑 pytest；
  ruff 用 `~/.venvs/agate-dev/bin/ruff`。
- **P3 红灯基线**（P4 目标是清零前 19 条）：`test_agate_cmdstream_adapters.py` 14 failed
  （`test_bdd_1_codex_probe_...` / `test_bdd_2_codex_list_sessions_...`（含 `_cwd_falsy_falls_back`）/
  `test_bdd_3_..._includes_subagent` / `test_bdd_4_..._maps_ten_fields` / `test_bdd_5_..._failed_exit_code_verbatim` /
  `test_bdd_6_codex_unfinished_command_pending` / `test_bdd_7_codex_truncated_output_hash_none` /
  `test_bdd_8_..._non_shell_tool_events_no_record` / `test_bdd_9_..._malformed_lines_no_crash` /
  `test_bdd_10_..._session_id_consistent_and_locatable` / `test_bdd_11_..._subagent_session_parses_standalone` /
  `test_bdd_12_..._subagent_session_id_is_child_not_parent` / `test_bdd_6_detect_consumes_registry_zero_change`
  （BDD-19 有意红）） + `test_agate_cmdstream_detect.py` 5 failed（`test_bdd_13_codex_call_freeze_frozen` /
  `test_bdd_14_codex_activity_freeze_frozen` / `test_bdd_15_codex_invalid_repeat_spin` /
  `test_bdd_16_codex_normal_progress_no_false_positive` / `test_bdd_17_codex_truncated_repeat_not_spin`）。
  失败类型全 B 类（`AttributeError: ... has no attribute 'CodexAdapter'` / assertion）。
- **`CommandStreamAdapter` 契约**（`agate-cmdstream-adapters.py:95-114`）：`probe(self, path)` /
  `list_sessions(self, cwd)` / `read_commands(self, session_path)`。
- **`_sha1_hex`** 在 `agate-cmdstream-adapters.py:~68`（模块级助手，复用）。
- **`CommandRecord` 十字段**（`agate-cmdstream-ir.py:31-44`）：`platform` / `session_id` / `tool` /
  `command` / `ts_start:int` / `ts_end:int|None` / `exit:int|None` / `exit_signal:str=""` /
  `output_hash:str|None` / `truncated:bool=False`。
- **P4 gate 规则**（`check-gate.py P4`）：exit 0 = 暂存区含非 md/yaml 代码文件；exit 1 = 仅 md/yaml。
- **C8 评审**：domains=[backend] + risk_level=medium → **单角色 `review`**（无组长汇总）——主 Agent 在你
  返回后派，评审兼做 SELF-GATE 协议-脚本语义对齐（A1-A6，因改 `agate-cmdstream-adapters.py`）。你**不派**评审。
- **CODE-MAP / 骨架**：本任务不新增源码文件（`CodexAdapter` 加进既有 `agate-cmdstream-adapters.py`），
  P3 已新建的 `test_codex_platform_docs.py` 是 P3 产出不是 P4 的——**P4 新增文件核对表可写"本阶段无新增
  源码文件"**（`agents/CODE-MAP.md` 是否存在你确认一下，不存在则该表整节可省）。

### 产出文件字段

先 `Write` 出 `P4-implementation.md`（含 `implementation_dir: agate/scripts/` + 改动文件清单 + 每条原
红灯测试转绿确认 + 新增文件核对表或"无新增源码文件"声明 + 自查结果），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter 必填：`phase=P4`、`task_id=TAG0033`、`type`（按 `--list`，通常 `implementation`）、
`parent=P3-test-cases.md` 或 `P2-design.md`、`trace_id=TAG0033-P4-20260909`、`status=draft`、
`created=2026-09-09`、`agent=implementer`。

### 返回

返回：P4-implementation.md 路径 + 改动文件清单（含行数增量）+ `CodexAdapter` 三方法 + 截断
classmethod + 2 常量的落点 + 原 19 条红灯测试转绿确认（跑 pytest 的 failed 数）+ 全量单测结果
（确认只剩 BDD-22~27 的 6 条预期红）+ ruff / consistency 结果 + 是否有 `[SCOPE+]` / `DESIGN_GAP`。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P4

路径：phase-cards/P4-implementation.md
---
# P4 — 代码实现

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P4 且有合规理由（check-pruning.py 已检查）→ 跳过，读 P5 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。
   该步骤不会阻塞流程——任何 stderr 输出（含 WARNING）均可忽略，直接继续步骤 1，
   无需查看结果、无需判断、无需因为看到 WARNING 而停下来处理。

**创建型测试清理钩子（强制要求，与 P3 卡同源）**：实现含创建资源用例时，须落地清理钩子——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；只修 P3 卡不修本卡即复发，两处须同步。

1. 派发 implementer subagent → 产出代码文件
   1.1 写 P4-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 P2 的 gate_commands 跑单元测试（非 gate，只是自查）
3. 按 C8 映射表派发评审（见下方）
4. 预跑 check-gate.py P4（确认暂存区有代码文件）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/ + 代码文件（含 .state.yaml，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P4，不要提前写 P5——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P4): {摘要}"（phase=P4，P4 产出含 P4-implementation.md + 代码文件）
7. P4 commit 完成后进入 P5：**phase 推进 P5 随 P5 产出 commit 一起**（P5-test-results/ 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（来自 gate 输出 / review rejected 理由）
→ 只修复失败项，不重做已通过的部分
→ 修复后重跑全量测试（T027 教训：修复可能引入回归）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P4 MAX=3）

**若这次是从 P6（或其他更后的阶段）退回来的**：`{AGATE_WORKSPACE}/tasks/{Txxx}/` 下不会再有旧的 P6-acceptance.md（已被归档），但当初具体是哪条 BDD 失败、失败原因是什么，会摘要在 `{AGATE_WORKSPACE}/tasks/{Txxx}/.retreat-history.md` 里——**重新派发 implementer 时，dispatch-context 必须引用这份摘要**，不能让 implementer 只看到"现有代码"却不知道具体要修哪里。已有代码不会被撤销、也不需要重新实现，是在已有实现基础上定向修复。**回退落地后必须建 DEBT 条目**（`source: retreat`，`evidence` 引用 retreat 提交哈希，模板 `assets/templates/tech-debt-template.md`——TAG0001 强制，见 `agate/rules/state-transitions.md` 回退规则节）。

## 前置条件

- [ ] P2-design.md 存在且 files_to_read 字段完整（导航清单）
- [ ] P2-review.md status: approved（P2 不可裁剪）
- [ ] P3-test-cases.md 存在（测试已设计）
- [ ] check-tdd-red.py 确认红灯（测试先于实现）
- [ ] 未跳过 P4（如有裁剪理由，见上方裁剪跳阶）

## 派发

- **角色**：implementer（`{agate_root}/assets/execution-roles/implementer.md`）
- **输入**：P2-design.md（files_to_read 导航 + gate_commands）+ P3-test-cases.md + P0-brief.md（env_constraints）
- **输出**：代码文件（在 P4-implementation.md 声明的 implementation_dir 下）
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md` + 以下阶段特定追加：

```
## 上下文控制
读取代码文件以 P2-design.md 的 files_to_read 清单为准，按需读取（标了行号范围的只读片段）。
不要在项目里盲目搜索或整目录全读。

## 自查≠gate
写完代码后应自跑测试确认基本功能（自查），但自查通过 ≠ P5 gate 通过。
P5 由主 Agent 派发 verifier subagent 执行 gate_commands.P5，主 Agent 验 gate（检查产出 + failed 计数 + N5 最小校验）。
不要在返回中声称"P5 已过"或"全部测试通过"——只返回路径 + 摘要。
UI/前端等需构建任务：单元测试全绿不代表可用，implementer 在 P4 完成后应构建并确认 dist 等构建产物存在，不能只跑单元测试就认为完成。

## 生产环境隔离
任何写入生产环境/生产数据库/生产 API 的操作都必须先 PAUSED 报告人工。
```

## 产出规格

- P4-implementation.md 必须声明 `implementation_dir: {实际路径}`
- 代码文件在声明的目录下
- 遵守 P2-design.md 的方案设计 + 现有项目代码规范

## 新增文件核对表

> 仅当项目已采用骨架（`P2-skeleton.md` 存在）或 CODE-MAP（`{AGATE_WORKSPACE}/agents/CODE-MAP.md`
> 存在）机制时填写；未采用则本节可省略。

implementer 为本阶段**每个新增文件**填一行：

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| {path} | `within <dir>` / `[SKELETON_DEVIATION: 理由]` | `[CODE_MAP_UPDATED]` / `[CODE_MAP_EXEMPT: 理由]` |

- **骨架归属列**：新增文件落在骨架声明的目录内 → `within <dir>`；落在骨架外 → 标
  `[SKELETON_DEVIATION: 理由]`（不阻断，供 P7 核对）
- **CODE-MAP 处理列**：新增文件已同步更新 `agents/CODE-MAP.md` → `[CODE_MAP_UPDATED]`；判断
  该文件不需要更新 CODE-MAP（如临时/测试脚手架）→ `[CODE_MAP_EXEMPT: 理由]`

`change_type: refactor` 同样适用本表（不因换用回归口径而豁免）。

## 评审派发（C8 机械映射）

**在 P4 实现完成后、gate 前**，按 P1 声明的 domains 和 risk_level 派评审。C8 映射表是机械规则，不靠判断"需不需要"：

| domain | 派哪些评审 | 产出 |
|--------|----------|------|
| backend | review | P4-review.md |
| frontend | design-review | P4-review.md |
| mcp | review（关注 MCP 接口契约）| P4-review.md |
| security | cso | P4-review.md |
| risk=high | P4 实现评审（按 domains 派 review/design-review/cso；P2 plan-eng-review 已审方案，P4 实现评审不可省）| P4-review.md |
| full（tier=full 或声明 ceremony: full）| P4 实现评审（按 domains 派 review/design-review/cso，同 risk=high 不可省；P2 plan-eng-review 已审方案）+ cso（security 域）+ P7 不可裁（full 档任务 P7 为强制阶段）| P4-review.md |

多个评审角色 `专家组并行` → 所有返回后派组长汇总 → 统一 P4-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长产出：P4-review.md。**agent 字段必须非 main**（与 P2 评审同规则，check-gate.py 在 P2 分支硬拦截 agent=main 的 approved）
5. 组长规则：不发表新意见，只汇总；任何 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P4-review.md。

**评审 checklist（RM-AG0046）**：`agate/scripts/check-maintainability.py` 检出 violations 非空时，评审角色 approve 前必须读过任务目录 `known-violations.md` 的登记理由——"是否接受该反模式"的判断权在评审角色，登记与数量对齐不单独构成放行依据。

review 不通过 → implementer 修改代码 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 按包拆分并行（条件触发，需额外约束）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P4 可拆分并行，但**有额外约束**：

1. 每个 package 派一个 implementer subagent
2. **各 implementer 只改自己 package 目录下的文件**——跨包的共享文件（类型定义、接口、配置）由主 Agent 在所有并行 implementer 返回后统一处理
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit
5. 主 Agent 在所有 implementer 返回后，统一处理共享文件改动（如果有）

**冲突预防**：
- dispatch-context 约束节必须写明：`只改动 {pkg}/ 目录下的文件。共享文件（{列出}）不在本次改动范围内`
- 如果某个 implementer 必须改共享文件 → 该包不能并行，改为串行（主 Agent 先派其他包并行，再串行处理含共享改动的包）
- 无法确定是否有共享改动 → 串行（安全默认值）

**基础设施隔离（并行时强制）**：
- debug server 端口：每个 implementer 的 dispatch-context 约束节分配不同端口（如 pkg-a: 3001, pkg-b: 3002）
- 测试数据库：每个 implementer 用独立数据库路径（如 `test-{pkg}.db`），不共享同一 test.db
- 环境变量：dispatch-context 写明各 subagent 独立的环境变量值（如 `PORT=3001` vs `PORT=3002`）
- 临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录

主 Agent 在并行派发前**必须**为每个 subagent 的 dispatch-context 分配上述隔离参数。当前无 gate 脚本检查（已知缺口），但未分配导致运行时冲突（端口占用/数据库锁）时计为重试，不算环境问题。

## gate 规则（check-gate.py 会跑）

```bash
check-gate.py P4 $TASK_DIR
```

- **exit 0**：暂存区含非 md/yaml 代码文件（git diff --cached --name-only）
- **exit 1**：暂存区仅 .md/.yaml 文件（无实际代码变更）→ 不能推进
- **exit 1**（RM-AG0046 三重门槛）：检测 violations 非空时，`known-violations.md` 必须存在且登记条目数 ≥ violation 数（评审检查复用上方既有 exit 1 条件；violations 为空 / 检测未部署 / git 通道不可用时不阻断）
- WARNING（不改变 exit code）：骨架/CODE-MAP 机制已采用（P2-skeleton.md 或 agents/CODE-MAP.md 存在）但缺「新增文件核对表」标题

## 推进条件（全部满足才写 phase: P5）

- [ ] 暂存区含代码文件（非 .md/.yaml）
- [ ] 按 C8 映射表触发的评审全部完成：P4-review.md status: approved（所有任务都要求——risk=high 的 P2 plan-eng-review 审方案，P4 实现评审按 domains 另行派发，不可省）
- [ ] SCOPE+ 已处理（若本阶段产生）：P1-requirements.md 有 [SCOPE_RESOLVED]（行首声明格式）
- [ ] git commit 完成

## 常见错误

1. **不读 files_to_read，在项目里乱翻**：implementer 拿到 P2 的 files_to_read 清单后应按清单阅读，不要在项目里全文搜索或整目录全读——上下文会爆炸
2. **自行加范围外改动**：发现需要做但不在 P1 范围内的改动 → 标 [SCOPE+]（行首声明格式）而非直接做
3. **只跑单元测试不验证集成**：单元测试全绿 ≠ 功能可用。P5 会跑 gate_commands 做技术验证，但要确保实现时路径依赖的端点行为已验证
4. **先更新 .state.yaml 再 commit**：state 和产出在同一 commit 里——不要先 commit 产出再单独 commit state
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P5 验证依赖：P5 跑 gate_commands.P5 的命令（在 P2 声明），确保你的实现能通过
- P6 验收依赖：实现路径的端点行为必须可验证（确认 API 返回正确的 Content-Type、状态码等）
- 代码改动文件路径：P8 发布时确认版本文件变更需要知道你改动了哪些 package

> 完成 → 读 phase-cards/P5-verification.md

6. **修改 P1 文档**：P4 发现 BDD 矛盾时标 DESIGN_GAP，不直接改 P1-requirements.md。需变更 P1 时标 `[BASELINE_CHANGE: 理由]` 并经主 Agent 批准。
<!-- AGATE_CARD_END -->
