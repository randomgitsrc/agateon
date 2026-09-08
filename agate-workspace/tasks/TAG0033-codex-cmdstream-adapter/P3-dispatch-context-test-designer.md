---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: test-designer
---

<dispatch_guide>
> 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片（参考规范）。

### 目标

产出 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md` + 测试代码（写进既有
`agate/tests/unit/test_agate_cmdstream_adapters.py` 与 `agate/tests/unit/test_agate_cmdstream_detect.py`，
不新建测试文件——本任务是给既有 cmdstream 测试树加 Codex 覆盖）。测试必须**先红**（实现未写 →
assertion / AttributeError 失败），P4 再写 `CodexAdapter` 让其转绿。

### BDD → 测试映射（30 条 BDD 的分工）

P1 §6 有 30 条 BDD。**不是每条都在 P3 写单测**——按验证层归位，`P3-test-cases.md` 必须逐条写明每个
BDD 的验证归属（P6 验收逐条对照，缺归属 = P6 无自动化验证）：

| BDD | P3 处理 |
|---|---|
| **BDD-1~12**（probe / list_sessions / read_commands 字段映射 / spawn_agent 子会话）| **P3 写单测**（`test_agate_cmdstream_adapters.py`），1 BDD ≥1 测试用例，红灯 |
| **BDD-13~17**（检测引擎对 Codex 会话判三态：调用冻结 / 活动冻结 / 无效重复 / 正常 / 截断不误判）| **P3 写单测**（`test_agate_cmdstream_detect.py`，虚拟时钟确定性试验，比照既有三态试验范式），红灯 |
| **BDD-18**（全量单测全绿）| **不在 P3 写**——是 P5 回归底线（gate_commands.P5）。P3-test-cases.md 记「P5 验证」 |
| **BDD-19**（`test_bdd_6_detect_consumes_registry_zero_change` @ `test_agate_cmdstream_adapters.py:317` 的精确等值断言改包含式）| **P3 写**——加一条断言「`"codex" in <registered set>`」使当前红（因 `ADAPTERS` 还没 codex 键），P4 加键 + 改 :317 断言后转绿。注意别破坏该测试原语义（检测引擎零改动消费注册表）|
| **BDD-20**（consistency 0 ERROR）| **不在 P3 写**——P5/P7 的 `check-protocol-consistency.py`。记「P5_consistency / P7 验证」 |
| **BDD-21**（检测引擎 / IR / 阈值 / 既有三适配器零功能改动）| **P3 可写一条 diff 断言测试**（`git diff` 检查 `agate-cmdstream-ir.py` 的 `CommandRecord` dataclass 十字段无改动 + `agate-cmdstream-detect.py` 阈值常量无改动）——当前应绿（还没改），属"守护测试"非红灯测试；或记「P5/P7 机械 diff 核对」。你判断哪种更稳，写清理由 |
| **BDD-22~27**（platform-notes.md Codex 章 / SETUP.md Codex 小节的内容锚点）| **P3 写断言审计测试**（grep `agate/platform-notes.md` / `agate/SETUP.md` 是否含规定锚文本）——当前红（文档还没补），P7 补文档后转绿。比照 TAG0030 的"断言审计"模式：一条测试 grep 多个锚。放 `test_agate_cmdstream_adapters.py` 或新增 `test_codex_platform_docs.py`（**这个可以新建**，因为不属既有 cmdstream 测试范畴而是文档审计）——你定，写清 |
| **BDD-28**（SELF-GATE commit 留痕 + protocol-alignment-review 存在）| **不在 P3 写**——P7/P8 人工 + commit-msg hook。记「P7/P8 验证」 |
| **BDD-29~30**（真机验证清单成形 + spawn_agent schema 穷尽项已登记）| **P3 可写文档结构断言**（grep `P1-requirements.md` §7 表有 V1-V8 且每项四要素关键词）——或记「P6 人工核对清单」。你判断 |

**红灯要求**：BDD-1~17 + BDD-19 + BDD-22~27 的测试必须在 P4 之前**真红**（B 类失败：assertion
失败 / `AttributeError: ... has no attribute 'CodexAdapter'` / 项目内 import 失败）。**不允许**：
SyntaxError（A 类，check-tdd-red exit 1）、第三方 import 失败（A 类）、测试写完就绿（exit 2，违反 TDD）。

### 关键约束（不可违反）

1. **测试代码写进既有文件**（`test_agate_cmdstream_adapters.py` / `test_agate_cmdstream_detect.py`）——
   Codex 覆盖是既有 cmdstream 测试树的增量，不新建 adapter 测试文件。文档断言审计测试（BDD-22~27）
   若你判断该独立，可新建 `agate/tests/unit/test_codex_platform_docs.py`——写清理由。
2. **不改既有测试的断言语义**——除 `test_bdd_6_detect_consumes_registry_zero_change`（BDD-19，:317）
   你要加「`"codex" in`」断言使其红，但**不删除 / 不弱化**其原有语义（检测引擎零改动消费注册表）。
   其余既有测试一律不碰。
3. **fixture**：P2-design.md §2.1 已定新建 `agate/tests/fixtures/cmdstream/codex-session.jsonl`
   （+ spawn_agent 子会话片段）。fixture 内容**结构取自真实 rollout**（P2 minimal_validation 已核字段）+
   **脱敏**（`demo` 前缀 / 无 `/home/kity` 真实路径 / 无密钥 / 无真实会话 uuid——用 `demo-0000-...` 式占位）。
   fixture 要覆盖：≥2 条 `event_msg`/`item_completed` `CommandExecution`（`exit_code` 0 与非 0 各一）、
   1 条未结束命令（`item.status != "completed"` 或有起始无完成——P2 §2.3 R3 双判据形态）、1 段
   `spawn_agent` 子会话片段（另一个 rollout 文件 or 同文件内标 `session_meta.thread_source=="subagent"`——
   按 P2 设计点 5，子会话是**独立文件**，故建 `codex-session.jsonl` + `codex-subagent-session.jsonl` 两个
   fixture）、非 shell 工具事件（`apply_patch` / `web__run` 的 `custom_tool_call`）、畸形行（非 JSON /
   JSON 数组非 dict / 缺 `payload` 键）、截断兜底样例（按 P2 设计点 4 的双信号形态构造）。
4. **P2-design.md §5 是测试预期行为的权威**——每个设计点的定论（probe 判据 / 映射规则 / session_id 取
   basename / 截断双信号 / list_sessions os.walk）就是测试的断言目标。测试断言要跟 §5 对齐，不自创预期。
5. **P2-review 的 4 条非阻塞观察要在测试里落地**（P2-review.md N1/N3）：
   - **N1**：`list_sessions` 的 `cwd if cwd else expanduser("~/.codex/sessions")` fallback 分支目前无
     测试覆盖 → P3 补 `list_sessions(cwd=None)` 与 `list_sessions(cwd="")` 用例（断言回落到默认根目录
     的行为——可用 monkeypatch `expanduser` 或传一个临时目录验证遍历逻辑）。
   - **N3**：`test_bdd_7_fixture_sanitized`（`test_agate_cmdstream_adapters.py:325-333`）的既有脱敏正则
     不匹配 Codex 连字符 uuid → **在该测试里把 `codex-session.jsonl` / `codex-subagent-session.jsonl`
     加入脱敏校验清单**，并补一条负向断言（fixture 里无 `/home/kity`、无真实 26 位 hex、无形如
     `rollout-2026-...-01a0....` 的真实会话标识——用脱敏占位）。这条改动属 BDD-19 附近的测试面，范围内。
6. **虚拟时钟三态试验**（BDD-13~17）比照既有范式：读 `test_agate_cmdstream_detect.py` 里既有三平台的
   三态试验怎么写的（构造 `CommandRecord` 列表 + 传 `now` 参数给 `detect()`），Codex 版照搬结构、
   只换数据源为 Codex fixture 经 `CodexAdapter.read_commands` 解析。阈值用 §3.4.3 的值（调用冻结
   suspect 900s / 活动冻结 suspect 300s / SPIN 阈值 5）——**不新造阈值**。
7. **每步落盘** `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-progress.md`（bash 追加）。
8. **所有 bash 命令加 `timeout <秒>s` 前缀**。跑测试确认红灯用
   `timeout 120s python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py agate/tests/unit/test_agate_cmdstream_detect.py -q`。
9. **不要自己派 review / 不要写实现**——P3 只产测试 + 用例文档，`CodexAdapter` 由 P4 写。

### 上游关联

- **P2-design.md**（同目录，已 approved）——§5 五设计点定论（测试断言目标）/ §2.1 改什么（fixture 规格）/
  §4.2 CommandRecord 十字段映射表 / §7 gate_commands（`P3` = `python3 -m pytest <两文件> -q`）/
  §8 files_to_read / §10 minimal_validation（真实 rollout 字段样例）
- **P1-requirements.md**（同目录）——§6 的 30 条 BDD（Given/When/Then 原文，测试用例 1:1 承接）/
  §4 spike 结论（§4.1 事件形态 / §4.1.1 exit_code / §4.2 子会话字段 / §4.1.2 截断待定）/ §7 真机清单
- **P2-review.md**（同目录）——4 条非阻塞观察 N1~N4（N1/N3 要在 P3 测试里落地）
- **既有 cmdstream 测试树**：`agate/tests/unit/test_agate_cmdstream_adapters.py`（既有三适配器单测 +
  `test_bdd_6_detect_consumes_registry_zero_change` @ :317 + `test_bdd_7_fixture_sanitized` @ :325-333）
  / `agate/tests/unit/test_agate_cmdstream_detect.py`（三态确定性试验 + :371 负向断言）
- **既有 fixture**：`agate/tests/fixtures/cmdstream/{dsh-session.jsonl, claude-code-session.jsonl,
  opencode-part-state.json}`（结构 + 脱敏约定范式）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§5 设计点定论 + §2.1 fixture + §4.2 映射表 + §7 gate_commands + §10 minimal_validation）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§6 的 30 条 BDD 原文 + §4 spike）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-review.md`（N1~N4 非阻塞观察）
4. `agate/tests/unit/test_agate_cmdstream_adapters.py`（既有适配器单测范式 + :317 / :325-333 原文——全读）
5. `agate/tests/unit/test_agate_cmdstream_detect.py`（三态确定性试验范式——全读；:371 负向断言）
6. `agate/scripts/agate-cmdstream-adapters.py`（`CommandStreamAdapter` 契约 line 95-114 + `DSHAdapter` line 394-621——CodexAdapter 契约形态 + `_sha1_hex` 助手 + `_detect_truncated` + `ADAPTERS` line 623-628）
7. `agate/scripts/agate-cmdstream-ir.py`（`CommandRecord` dataclass 十字段——断言字段名以此为准）
8. `agate/scripts/agate-cmdstream-detect.py`（`detect()` 签名 + 三态判定 + 阈值常量名——三态试验用）
9. `agate/tests/fixtures/cmdstream/dsh-session.jsonl` + `claude-code-session.jsonl`（fixture 结构 + 脱敏范式）
10. `agate/assets/execution-roles/test-designer.md`（你的角色定义）
11. `agate/phase-cards/P3-tdd.md`（本阶段卡片——产出规格 / check-tdd-red 红灯语义 A/B 类）
12. `AGENTS.md`（worktree 根——改脚本 TDD 工作流、双工作区纪律、工具纪律）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P2（P3 产出 commit 随 P3-test-cases.md
  推进 P3）/ judge.enabled=true。P2 已 commit（`8fbb0d4`）。P3 step 0 `agate-capture-env-baseline.py`
  已跑（无 formatter，未写基线文件——非阻塞，符合卡片）。
- **`gate_commands.P3`**（P2 §7 固化）：`python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py
  agate/tests/unit/test_agate_cmdstream_detect.py -q`。**未声明 `P3_formatter`**——check-tdd-red 走
  exit-code + 输出关键词判 A/B 类。⚠️ **所以测试必须 SyntaxError-free、无第三方 import 失败**，否则会被
  误判 A 类（check-tdd-red exit 1）。红灯来源必须是 assertion 失败 / `AttributeError`（`CodexAdapter`
  不存在）/ 项目内 import 失败（B 类）。
- **`CommandStreamAdapter` 契约**：`probe(self, path)` / `list_sessions(self, cwd)` /
  `read_commands(self, session_path)`（`agate-cmdstream-adapters.py` line 95-114）。`ADAPTERS` 注册表
  line 623-628 现三键 `"claude-code"`/`"opencode"`/`"dsh"`——P4 加 `"codex"`。
- **`CommandRecord` 十字段**（`agate-cmdstream-ir.py` line 31-44）：`platform` / `session_id` / `tool` /
  `command` / `ts_start:int` / `ts_end:int|None` / `exit:int|None` / `exit_signal:str=""` /
  `output_hash:str|None` / `truncated:bool=False`。
- **P2 §5 设计点定论**（测试断言目标，摘要）：
  - probe：basename 匹配 `rollout-*.jsonl`（非 `.zstd`）+ 首行 `readline()` 解析 `type=="session_meta"`
    且 payload 含 `cli_version`/`originator`/`id`；异常 → `return False` 不抛
  - read_commands：源 = `type=="event_msg"` + `payload.type=="item_completed"` +
    `payload.item.type=="CommandExecution"`；`tool="exec"`；`command=shlex.join(item.command)`
    （对 `["/bin/bash","-lc","echo hi"]` → `/bin/bash -lc 'echo hi'`，`"echo hi" in` 仍 True）；
    `exit=item.exit_code`（直取数字，未结束回落 None）；`exit_signal=f"exit_code={n}"` / `"pending"`；
    `ts_start=payload.started_at_ms` / `ts_end=payload.completed_at_ms`；
    `output_hash=_sha1_hex(item.aggregated_output)`（`truncated` 时 None）
  - session_id = `os.path.basename(session_path)`（**不取** `payload.session_id`——对子会话是父 id）
  - 截断：双信号（`_CODEX_TRUNC_BOOL_KEYS` ∪ `_CODEX_TRUNC_TEXT_MARKERS`，任一命中即 True）；
    `truncated=True ⇒ output_hash=None` 无条件
  - list_sessions：`os.walk` 枚举 `rollout-*.jsonl`；根目录 `cwd if cwd else expanduser("~/.codex/sessions")`；
    路径字符串 `sorted()`；返回绝对路径 list
- **P3 gate 规则**（`check-gate.py P3`）：exit 2 = P3-test-cases.md 存在（红灯由 check-tdd-red.py 独立确认）。
  `check-tdd-red.py $TASK_DIR`：exit 0 = 真红灯（可推进）；exit 1 = 假红灯（A 类，测试代码自身错）；
  exit 2 = 绿了（违反 TDD）。

### 产出文件字段

先 `Write` 出 `P3-test-cases.md`（含 `test_code_dir:` 声明 + 30 条 BDD 逐条验证归属表 + 每条 P3 测试
用例的 test id / 覆盖 BDD / 断言要点 / 预期红灯原因），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段并逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter 必填：`phase=P3`、`task_id=TAG0033`、`type`（按 `--list` 提示，通常 `test-design`）、
`parent=P2-design.md`、`trace_id=TAG0033-P3-20260909`、`status=draft`、`created=2026-09-09`、
`agent=test-designer`。`test_code_dir:` 写在正文（值 = `agate/tests/unit/`——测试落既有文件）。

### 返回

返回：P3-test-cases.md 路径 + 新增/改动的测试文件清单 + fixture 文件清单 + P3 写了多少条测试用例、
覆盖哪些 BDD（哪些 BDD 归 P5/P6/P7 验证）+ 本地跑 `python3 -m pytest <两文件> -q` 的红灯结果
（failed 数 + 失败类型确认是 B 类）+ 是否有范围外发现。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P3

路径：phase-cards/P3-tdd.md
---
# P3 — TDD 测试设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P3 + 有合规理由（risk=low + 跳过风险已声明）→ 跳过，读 P4 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。**必须执行**。
   该步骤不阻塞流程——脚本的 stderr 输出（含 WARNING）均可忽略，执行完直接继续步骤 1。

**创建型测试清理钩子（强制要求）**：测试含创建资源用例（建团队/条目等）时，须声明清理钩子要求——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；验收环境残留由清理钩子与 post-test 残留检查共同兜底（见 P6 卡）。

1. 派发 test-designer subagent → 产出 P3-test-cases.md + 测试代码目录
   1.1 写 P3-dispatch-context-test-designer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 跑 check-tdd-red.py 确认红灯
3. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P3，不要提前写 P4——phase = 本 commit 的产出阶段
4. git commit -m "wf({Txxx}-P3): {摘要}"（phase=P3，P3 产出含 P3-test-cases.md + 测试代码）
5. P3 commit 完成后进入 P4：**phase 推进 P4 随 P4 产出 commit 一起**（P4-implementation.md 就绪后），不是单独 phase commit

## refactor 任务：回归测试口径

> 适用：P1 frontmatter 声明 `change_type: refactor` 的任务（P2-design.md §3.4）。功能任务（缺省）走上方既有 TDD 口径，不受本节影响。

refactor 任务无新增功能行为可断言，P3 测试设计改用**回归测试口径**：

- **测试设计 = 回归测试口径**：复用/保留既有测试用例，标注每条回归用例覆盖了重构涉及的哪些文件/路径；**不新增功能行为断言**（无新行为可断言）。
- **跳过 check-tdd-red 红灯步骤**：重构无新功能断言，测试套件本就全绿，红灯语义不适用（check-tdd-red 对 refactor 任务会误报 exit 2 绿灯）。回归质量由 P5 全量回归（gate_commands.P5）+ P6 的 `regression.log`（全量回归重跑）兜底。CI backstop 对 refactor 任务同样跳过 check-tdd-red（ci-gate-backstop.py P3 分支 refactor 感知）。
- **P3 gate 不变**：仍为文件存在性检查——refactor 的 P3 产出是 P3-test-cases.md（回归口径声明 + 既有用例覆盖映射），文件存在即满足 gate。

## 如果是重试

确认上一轮失败原因（测试设计不合理 / 未覆盖关键 BDD / 非真红灯）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P3 MAX=2）

## 前置条件

- [ ] P2-design.md files_to_read 完整（测试设计需要知道实现导航）
- [ ] P2-review.md status: approved（P2 不可裁剪）

## 派发

- **角色**：test-designer（`{agate_root}/assets/execution-roles/test-designer.md`）
- **输入**：P2-design.md + P1-requirements.md（BDD 验收条件，每条 `#### BDD-NN` 对应一个测试用例）
- **输出**：P3-test-cases.md + test_code_dir/
- **派发 prompt**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 产出规格

- P3-test-cases.md 必须声明 `test_code_dir: {路径}`
- 每条测试用例对应一条 P1 的 `#### BDD-NN` 验收条件（1:1 映射）
- UI 任务（P2 ui_affected: true）：必须含 Playwright/E2E 用例

## gate 规则

**check-gate.py P3**（hook + 主 Agent 预跑，秒级文件检查）：
- exit 1：P3-test-cases.md 不存在
- exit 2：P3-test-cases.md 存在（TDD 红灯由 check-tdd-red.py 独立确认）

**check-tdd-red.py**（主 Agent 手动确认红灯 + CI backstop P3 兜底）：

```bash
check-tdd-red.py $TASK_DIR
```

- **exit 0**：真红灯（assertion 失败 / 项目内 import 失败 = B类错误）— 测试正确但因实现未写而失败
- **exit 1**：假红灯（SyntaxError / 第三方 import 失败 = A类错误）— 测试代码自身错误
- **exit 2**：绿了 — 实现先于测试，违反 TDD
- **exit 3**：无可用测试运行器

**技术栈无关**：check-tdd-red.py 通过 formatter 将测试输出标准化为 JSON，不直接解析任何框架的输出格式。formatter 在 gate_commands.P3_formatter 中声明（可选）。不提供 formatter 时退化为 exit-code-only（所有红灯 = 可推进）。

**探测链**：`$TEST_RUNNER` 环境变量 → `gate_commands.P3`（P2-design.md 声明）→ `which pytest` → exit 3。`$TEST_RUNNER` 始终优先（退化为 exit-code-only，无 formatter）。

**formatter 选择**：见 `assets/formatters/README.md` 速查表。常用：pytest → `pytest.sh`，vitest → `vitest.sh`，go test → `go-test.sh`，其他 → `generic-exit-only.sh`。

## 按包拆分并行（条件触发，非强制）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P3 可拆分并行：

1. 每个 package 派一个 test-designer subagent
2. 各自写各自的测试文件（不同目录）
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit

拆分判据（本阶段特定）：
- P2 packages > 1 且包间无数据依赖 → 可并行
- 单包或包间有依赖 → 串行（不拆分）
- P2 未声明 packages → 串行

每个 subagent 的 dispatch-context 必须明确其负责的 package 范围（约束节写"只写 {pkg} 目录下的测试"）。

## 推进条件（全部满足才写 phase: P4）

- [ ] check-tdd-red.py exit 0（真红灯确认）
- [ ] P3-test-cases.md 存在且含 test_code_dir
- [ ] 测试代码目录存在
- [ ] UI 任务：Playwright/E2E 用例存在

## 常见错误

1. **测试绿了才 commit**：测试已在 P4 之前通过 → 违反 TDD"测试先于实现"原则。P3 的 gate 要求红灯
2. **忘记声明 test_code_dir**：后续阶段找不到测试代码 → P5 跑 gate_commands 时找不到测试路径
3. **测试覆盖不全**：只为部分 BDD 写了测试 → P6 验收时那些 BDD 没有自动化验证
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。
5. **只覆盖交互路径，忽略前置状态**：测试设计应覆盖 BDD Given 隐含的前置状态，不只覆盖 When/Then 路径（详见 WORKFLOW.md §P3 测试设计指导）

## 下游影响

- P4 用测试驱动实现（implementer 看测试理解预期行为）
- P5 跑同一套测试验证实现正确性（gate_commands.P5）

> 完成 → 读 phase-cards/P4-implementation.md
<!-- AGATE_CARD_END -->
