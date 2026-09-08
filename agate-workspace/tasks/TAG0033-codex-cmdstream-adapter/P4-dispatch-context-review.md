---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: review
---

<dispatch_guide>
> 以下派发指引是本次评审的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标

对 P4 实现（`agate/scripts/agate-cmdstream-adapters.py` 新增 `CodexAdapter` +225 行 + `ADAPTERS` 加
`"codex"` 键 + `test_agate_cmdstream_adapters.py` `test_bdd_6_detect_consumes_registry_zero_change` 的
:319 断言改包含式）做独立工程评审（C8：domains=[backend] → `review`），产出
`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-review.md`（`agent: review`，`agent != main`）。
结论 `status: approved` 或 `status: rejected`（rejected 须逐条列 BLOCKER + 引用文件:行 / BDD / 设计点）。
**不通过时不要自己改代码**——写清 BLOCKER，返回主 Agent 派 implementer 修改后再评审。

> 本评审是 C8 工程评审。SELF-GATE 的协议-脚本语义对齐（A1-A7）由**并行**的 protocol-alignment-review
> 单独产出，不在你的范围——你专注实现正确性 / 测试充分性 / 是否守住零改动约束。

### 必须独立核验的维度（逐项在 P4-review.md 给结论 + 证据，须读实际 `git diff` 不只看 P4-implementation.md 文字）

1. **5 个设计点实现是否对齐 P2-design.md §5 定论**（逐条读 `CodexAdapter` 代码）：
   - **probe**：basename 匹配 `rollout-*.jsonl` 且排除 `.jsonl.zstd`？只 `readline()` 一行不整文件
     load？首行判 `type=="session_meta"` 且 payload 含 `cli_version`/`originator`/`id` 任一？异常
     （路径不存在 / 首行非 JSON / 非 dict）`return False` 不抛？与 `DSHAdapter.probe` 异常处理一致？
   - **read_commands 映射**（对照 P2 §4.2 十字段表）：`platform=="codex"` / `session_id=os.path.basename`
     （**没取** `session_meta.session_id`——grep 确认代码里没有 `payload["session_id"]` / `["session_id"]`
     取值用于 `CommandRecord.session_id`）/ `tool="exec"` / `command` 用 `shlex.join`（跑
     `python3 -c "import shlex;print(shlex.join(['/bin/bash','-lc','echo hi']))"` 确认 `"echo hi" in` 仍 True）/
     `exit` 直取 `item.get("exit_code")`（无文本前缀解析）/ `exit_signal` 有 exit 时 `f"exit_code={n}"`、
     未结束 `"pending"` / `ts_start`←`started_at_ms` / `ts_end`←`completed_at_ms` /
     `output_hash=_sha1_hex(...)` 且 `truncated` 时为 `None`。
   - **源过滤 / 非 shell 工具事件**（BDD-8）：只从 `event_msg`→`item_completed`→`item.type=="CommandExecution"`
     产出记录；`apply_patch`/`web__run` 的 `custom_tool_call` 不产出。是靠源过滤天然排除还是显式白名单？
     哪种都可，确认对 fixture 里的这些事件确实不产出记录。
   - **畸形行**（BDD-9）：逐行 `json.loads` try/except + continue，对「非 JSON / JSON 数组非 dict /
     缺 payload 键」三类都不崩、坏行跳过、合法记录照常产出。
   - **pending 双判据形态 B**（BDD-6 / P3 finding #4 / P2 §2.3 R3）：实现是否做了
     `started_ids - completed_ids`（或等价）回填——对「有 `item_started`/`CommandExecution` 起始事件、
     无对应 `item_completed`」的 id 补一条 `exit=None` / `ts_end=None` / `exit_signal="pending"` 的记录？
     只判 `item.status != "completed"` 一条不够（fixture 用的是形态 B）。已完成命令记录不受影响？
   - **session_id 对子会话**（BDD-12）：`read_commands(codex-subagent-session.jsonl)` 产出记录的
     `session_id` 是子会话文件的 basename（含子自身 uuid），不是父会话 id。
   - **list_sessions**（BDD-2/3 + P2-review N1）：`root = cwd if cwd else expanduser("~/.codex/sessions")`
     （`cwd=None` 与 `cwd=""` 都回落）；`os.walk` 收 `rollout-*.jsonl`；返回绝对路径 list；`sorted()`。
     父 + `spawn_agent` 子会话都被枚举（同扁平目录）。
   - **截断双信号**（BDD-7/17 + P2 §5 设计点 4）：`_detect_truncated` classmethod（比照
     `DSHAdapter._detect_truncated`）+ 2 个模块常量（bool 键集 ∪ 文本标记集，任一命中即 True）+
     `# P5 V4 收敛锚` 注释；`truncated=True ⇒ output_hash=None` 无条件（grep 确认没有"truncated 但
     仍算 hash"的路径）。
2. **零改动约束守住**（BDD-21 / P2 §2.2）：`git diff` 确认**未改** `agate-cmdstream-detect.py` /
   `agate-cmdstream-ir.py`（`CommandRecord` dataclass）/ `ClaudeCodeAdapter` / `OpenCodeAdapter` /
   `DSHAdapter` 的 class 体 / `agate/platform-notes.md` / `agate/SETUP.md`。改动只有
   `agate-cmdstream-adapters.py`（新增 CodexAdapter + 常量 + 助手 + ADAPTERS 加一行 + `import shlex`）
   与 `test_agate_cmdstream_adapters.py`（:319 一行断言）。有别的改动 → BLOCKER。
3. **`test_bdd_6` 断言改动语义**（BDD-19）：原 `assert registered == {"claude-code","opencode","dsh"}`
   改为 `assert {"claude-code","opencode","dsh"}.issubset(registered)`（或 `>=`）——语义从"恰好三键"
   放宽为"至少这三键"。该测试**其它断言未被删/弱化**（它验证「检测引擎零改动消费注册表」——确认
   `assert "ADAPTERS" in detect_src` 等仍在）。P3 追加的 `assert "codex" in registered` 保留。
4. **测试充分性**：19 条原红灯（14 adapters + 5 detect）全绿？跑
   `timeout 120s python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py agate/tests/unit/test_agate_cmdstream_detect.py -q`
   自己确认（不只信 P4-implementation.md）。三态确定性试验（BDD-13~17）用的阈值是既有值（900/300/5）？
5. **回归**：`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no`——**只**有
   `test_codex_platform_docs.py::test_bdd_22~27`（6 条）failed（P7 文档，预期红）？有别的 failed = P4
   引入的回归 → BLOCKER。⚠️ 跑完全量 pytest 若发现 `agate-workspace/tasks/TAG0033-.../gate-events.jsonl`
   被某测试追加了行（已知测试隔离问题，非本任务引入），`git checkout` 还原它、在评审里记一句，不计 BLOCKER。
6. **ruff / consistency**：`~/.venvs/agate-dev/bin/ruff check agate/` All checks passed？
   `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` exit 0 / 0 ERROR？
7. **可维护性**（RM-AG0046）：`python3 agate/scripts/check-maintainability.py` 若对新代码报 violations
   非空 → 须有任务目录 `known-violations.md` 登记；无 violations 则跳过。
8. **CODE-MAP / 新增文件核对表**：本阶段无新增源码文件（CodexAdapter 加进既有文件）——P4-implementation.md
   是否如实写了这一点。

### 上游关联

- **P2-design.md**（同目录，已 approved）——§5 五设计点定论（实现权威）/ §2.2 不改什么 / §4.2 十字段映射表
- **P3-test-cases.md**（同目录）——测试用例断言要点表（实现让它们转绿的目标）
- **P1-requirements.md**（同目录）——§6 BDD-1~21 原文 / §4 spike 实测事实
- **P2-review.md**（同目录）——N1~N4 非阻塞观察（P4 是否落地）
- **既有实现**：`agate/scripts/agate-cmdstream-adapters.py` 的 `DSHAdapter`（近亲范式）/
  `agate-cmdstream-ir.py`（`CommandRecord` 十字段）/ `agate-cmdstream-detect.py`（三态 + 阈值）

### 输入文件（按顺序读）

1. `git diff HEAD -- agate/scripts/agate-cmdstream-adapters.py agate/tests/unit/test_agate_cmdstream_adapters.py`（本次改动全貌——先读这个）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（implementer 自述——核对但不轻信）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-progress.md`（实现过程 + 自查命令）
4. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§5 设计点 + §2.2 + §4.2）
5. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md`（用例断言要点）
6. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§6 BDD-1~21 + §4 spike）
7. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-review.md`（N1~N4）
8. `agate/scripts/agate-cmdstream-adapters.py`（全文——`CodexAdapter` + `DSHAdapter` 对照 + `_sha1_hex` + `ADAPTERS`）
9. `agate/scripts/agate-cmdstream-ir.py`（`CommandRecord` 十字段——确认未改）
10. `agate/scripts/agate-cmdstream-detect.py`（确认未改 + 三态阈值常量名）
11. `agate/tests/unit/test_agate_cmdstream_adapters.py` + `test_agate_cmdstream_detect.py`（新增用例全读）
12. `agate/tests/fixtures/cmdstream/codex-session.jsonl` + `codex-subagent-session.jsonl`（实现解析对象）
13. `agate/assets/execution-roles/review.md`（你的角色定义）
14. `agate/phase-cards/P4-implementation.md`（P4 gate 规则 / 评审 checklist / RM-AG0046 三重门槛）
15. `AGENTS.md`（worktree 根——改脚本工作流、双工作区纪律、ruff 合并强制）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P3（P4 产出 commit 随
  P4-implementation.md 推进 P4）/ judge.enabled=true。P3 已 commit（`b5f3187`）。系统 `python3` 跑 pytest；
  ruff 用 `~/.venvs/agate-dev/bin/ruff`。
- **implementer 自查结果**（你独立复跑核实）：两 cmdstream 测试文件 58 passed / 0 failed（原 19 红清零）；
  全量单测 1383 passed / 6 failed（全 `test_codex_platform_docs.py::test_bdd_22~27`，预期）/ 2 skipped；
  ruff All checks passed；consistency 0 ERROR。无 `[SCOPE+]` / `DESIGN_GAP`。
- **改动 diff 范围**：`agate/scripts/agate-cmdstream-adapters.py`（+225/-0：`import shlex` + 2 常量
  `_CODEX_TRUNC_BOOL_KEYS`/`_CODEX_TRUNC_TEXT_MARKERS` + 助手 `_codex_int_or_none` + `class CodexAdapter`
  + `ADAPTERS["codex"]`）+ `agate/tests/unit/test_agate_cmdstream_adapters.py`（+1/-1：:319 断言改包含式）。
- **P4 gate 规则**（`check-gate.py P4`）：exit 0 = 暂存区含非 md/yaml 代码文件；exit 1 = 仅 md/yaml /
  RM-AG0046 三重门槛未满足。**P4-review.md 必须 `status: approved` 且 `agent != main`**（check-gate P4
  不硬拦 agent=main，但 P4 卡片要求；provenance 审计会查）。

### 产出文件字段

先 `Write` 出 `P4-review.md`（含正文），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-review.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter：`status`（approved / rejected）、`phase=P4`、`task_id=TAG0033`、`parent=P4-implementation.md`、
`trace_id=TAG0033-P4-review-20260909`、`created=2026-09-09`、`agent=review`。

正文必须含：逐维度评审结论（上方 8 项）+ 引用文件:行 / BDD / 设计点 + （若 rejected）逐条 BLOCKER +
你独立复跑的 pytest / ruff / consistency 输出摘要（passed/failed 计数）。
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
