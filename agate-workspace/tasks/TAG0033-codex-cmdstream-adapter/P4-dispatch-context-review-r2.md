---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: review
review_round: 2
---

<dispatch_guide>
> 以下派发指引是本次评审的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 本次是 P4 review 第 2 轮（P5→P4 回退后的 F1 定向修复）

第 1 轮 P4 review（`P4-review.md`）已 approved 了 `adapter-core` + `protocol-docs` 两批。P6 真机验证
发现 **F1**（DEBT0035）→ 回退 P5→P4（`52fe210`）→ implementer 重试 #1 定向修复。**本轮只审 F1 修复面**，
不重审已 approved 的部分。

F1：真机 Codex 把已结束但非 0 退出的命令记为 `payload.item.status == "failed"`（仍带完整 `exit_code`
+ `completed_at_ms`），`CodexAdapter` pending 判据 `status != "completed"` 误判其为 pending → 丢真实
`exit_code` + `output_hash` → detect 判不出 SPIN。

本轮改动（`git diff HEAD` 覆盖，HEAD = `9a7a1f9` debt commit）：
- `agate/scripts/agate-cmdstream-adapters.py`：新增 `_codex_is_finished(payload, item)` helper；
  `pending = item.get("status") != "completed"` → `pending = not _codex_is_finished(payload, item)`；
  class docstring 微调
- `agate/tests/fixtures/cmdstream/codex-session.jsonl`：`make build-docs` item `status` completed→failed；
  追加真机重复失败簇（`ls /demo/nonexistent-xyz` ×6，`status:"failed"` + `exit_code:2` + `completed_at_ms`）
- `agate/tests/unit/test_agate_cmdstream_adapters.py`：`test_bdd_5_*` Given→`status="failed"` + 加强断言；
  新增 `test_bdd_5_codex_failed_status_not_pending_guard`（无新 BDD 编号）
- `agate/tests/unit/test_agate_cmdstream_detect.py`：`_cx_exec` 加 `status` 参数；`test_bdd_15_*` 重复用 `status="failed"`
- `agate/platform-notes.md`：Codex 章「命令流适配」小节 +1 bullet（真机 `status` 取值集 + 判已结束口径）
- （主 Agent 已单独改 `P1-requirements.md` §4.1/BDD-5/BDD-6 + `P2-design.md` §5/R3 的 `[BASELINE_CHANGE]`
  注记——你**核对这些注记是否恰当**，但不改它们）

### 必须核验（逐项在 P4-review.md 追加「## 第 2 轮复评（F1 修复）」节给结论）

1. **`_codex_is_finished` 逻辑正确**：读 helper 实现——「已结束」= `status ∈ {"completed","failed"}` **或**
   `payload.completed_at_ms` 非 None **或** `item.exit_code` 是 `int` 非 `bool`（三者任一）。确认：
   - `status="failed"` + `exit_code=137` + `completed_at_ms` → finished（不 pending）✔
   - `status="in_progress"` + `exit_code=None` + 无 `completed_at_ms` → not finished（pending）✔
   - `item_started` 事件（无 status / 无 exit_code / 无 completed_at_ms）→ not finished（走 pending 回填）✔
   - 边界：`exit_code=0` 是 `int` 非 `bool` → finished ✔；`exit_code=False`（bool）→ 不算（isinstance bool 排除）✔
2. **`_build_record` 非 pending 路径对 `status="failed"` 无遗漏**：`raw_exit = item.get("exit_code")` →
   `exit_code=137` → `exit_signal="exit_code=137"`；`ts_end = completed_at_ms`；`output_hash = _sha1_hex(...)`。
   确认 `status="failed"` 走这条路径产出完整记录（非 pending 空壳）。
3. **`started_ids - emitted_ids` 回填不再误收 `status="failed"`**：`item_completed` 且 `status="failed"` 的
   item 现在走非 pending 主循环产出、`emitted_ids` 里有它 → 结束时回填分支跳过它。读代码确认。
4. **零改动约束仍守住**：`git diff HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py`
   **须为空**；`CodexAdapter` 的 `probe` / `list_sessions` / `_detect_truncated` / `_join_command` /
   `session_id` 取法 / `ADAPTERS["codex"]` / `test_bdd_6:319` 断言 **未被本轮碰**（`git diff HEAD` 只应有
   pending 判据 + helper + docstring）。
5. **测试充分性**：
   - 自己跑 `timeout 120s python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py
     agate/tests/unit/test_agate_cmdstream_detect.py agate/tests/unit/test_codex_platform_docs.py -q`
     → 应 67 passed / 0 failed。
   - `test_bdd_5_*`：Given `status="failed"` → Then `exit==2` / `exit_signal=="exit_code=2"` / `ts_end` 非 None
     / `output_hash` 非 None（证明不被误判 pending）。
   - `test_bdd_15_codex_invalid_repeat_spin`：重复失败命令用 `status="failed"` → `detect` → `SPIN`。
   - `test_bdd_6_codex_unfinished_command_pending`：**仍**测真·未结束（`item_started` 无 `item_completed`）→
     `exit is None` / `exit_signal == "pending"`。确认它没被改口径破坏（fixture 里的 `sleep 999` 真·未结束样本仍在）。
   - 新守护 `test_bdd_5_codex_failed_status_not_pending_guard`：读断言体，确认是实质断言。
6. **回归**：`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` → **1390 passed（1389 + 1 守护）
   / 0 failed / 2 skipped**。有别的 failed = 回归 → BLOCKER。⚠️ 若 `gate-events.jsonl` 被测试追加行，
   `git checkout` 还原 + 记一句，不计 BLOCKER。
7. **ruff / consistency**：`~/.venvs/agate-dev/bin/ruff check agate/` All checks passed？
   `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 脚本）exit 0 / 0 ERROR？
8. **真机复验**：读 `P4-progress.md` 的重试 #1 段——implementer 报「`codex exec` 连跑 ≥6 次相同失败
   命令 → rollout → `detect --platform codex` → `VERDICT: SPIN`」。**你自己复跑一次**（对 implementer 造的
   rollout，路径在 progress 里；或自己 `codex exec` 造一个）确认 detect 得 SPIN、`read-commands` 对
   `status="failed"` 命令产出 `exit=2` 非 pending。
9. **BASELINE_CHANGE 注记恰当性**：`P1-requirements.md` §4.1（`item.status` 取值集）/ BDD-5 Given
   （`status="failed"`）/ BDD-6 Given（"真·未结束"收紧）+ `P2-design.md` §5 设计点 2 / R3——主 Agent 加的
   `[BASELINE_CHANGE: ...]` 注记是否：(a) 如实反映改动 (b) 未改 BDD 的 Given/When/Then 判定语义（只补事实/
   收紧措辞）(c) DEBT0035 引用正确。有问题 → 在 review 里指出（非 BLOCKER，除非注记实质篡改了 BDD 语义）。

### 上游关联

- **DEBT0035**（`agate-workspace/debt/tech-debt.md`——F1 权威描述）
- **retreat commit `52fe210`**（P5→P4 诊断全文）
- **`.archived/p6-pre-retreat-20260909/real-machine-p6.md` + `real-machine-v6-detect.log`**（F1 现场证据 +
  真机 `status="failed"` 样本 + pre-fix detect 输出）
- **P4-implementation.md「## 重试 #1（F1 修复）」节**（implementer 自述——核对不轻信）
- **P4-review.md**（第 1 轮 approved 结论——你在其后追加第 2 轮节）
- **P2-design.md §5 设计点 2**（含主 Agent 加的 pending 判据 BASELINE_CHANGE）

### 输入文件（按顺序读）

1. `git diff HEAD`（本轮全部改动——先看 stat + adapters.py / fixture / 测试 diff）
2. `agate-workspace/debt/tech-debt.md`（DEBT0035）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/.archived/p6-pre-retreat-20260909/real-machine-p6.md` + `real-machine-v6-detect.log`（F1 现场）
4. `agate/scripts/agate-cmdstream-adapters.py`（`_codex_is_finished` helper + `read_commands` pending 行 + `_build_record`）
5. `agate/tests/unit/test_agate_cmdstream_adapters.py`（`test_bdd_5_*` + 新守护）
6. `agate/tests/unit/test_agate_cmdstream_detect.py`（`test_bdd_15_*` + `_cx_exec`）
7. `agate/tests/fixtures/cmdstream/codex-session.jsonl`（`status="failed"` 样本 + 真·未结束样本）
8. `agate/platform-notes.md`（Codex 章「命令流适配」小节 +1 bullet）
9. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-progress.md`（重试 #1 段 + 真机复验命令输出）
10. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（重试 #1 节）
11. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§4.1 + BDD-5/6 的 BASELINE_CHANGE）
12. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§5 设计点 2 + R3 的 BASELINE_CHANGE）
13. `agate/assets/execution-roles/review.md`（角色定义）
14. `agate/phase-cards/P4-implementation.md`（P4 gate + 「如果是从 P6 退回来的」节）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P4（回退已落地，`retries.P4` attempt 1）/
  judge.enabled=true。HEAD = `9a7a1f9`（debt commit）。系统 `python3`；ruff `~/.venvs/agate-dev/bin/ruff`；
  codex-cli 0.153.4 + ChatGPT 登录。
- **implementer 自查**（你复跑核实）：3 文件 pytest 67 passed / 0 failed；全量单测 1390 passed / 0 failed
  / 2 skipped（1389 + 1 守护）；ruff clean；consistency 0 ERROR。真机 V6 ③ 复验：造的 rollout →
  `detect --platform codex` → `VERDICT: SPIN`（pre-fix 是 FROZEN/NORMAL）。无 `[SCOPE+]` / DESIGN_GAP。
- **本轮改动范围**（你独立核对 `git diff HEAD --stat`）：adapters.py（helper + 1 行判据 + docstring）+
  fixture + 2 测试文件 + platform-notes.md 1 bullet + 4 个任务 md 的 BASELINE_CHANGE/progress。
  **detect.py / ir.py / 既有三适配器 class 体 零改动**。
- **P4 gate**：回退后离开 P4 的 commit 正常校验完成度（不豁免）。C8 backend → 你（review）+ 并行的
  protocol-alignment-review 第 3 轮（SELF-GATE，你不管那个）。

### 产出

在 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-review.md` **追加**「## 第 2 轮复评（F1 修复）」
节（保留第 1 轮结论）：逐项结论（上方 9 项）+ 独立复跑的 pytest/ruff/consistency/真机 detect 输出摘要 +
（若 rejected）逐条 BLOCKER。用 `FILE=... python3 ~/.agate/scripts/agate-md-field-set.py <key> <value>`
更新 frontmatter：`status`（approved / rejected）、`review_round=2`、`trace_id=TAG0033-P4-review-20260909-r2`。

### 返回

P4-review.md 路径 + status（approved / rejected）+ 一句话结论 + `_codex_is_finished` 逻辑是否正确 +
BDD-5/6/15 + 守护是否全绿 + 真机 detect 复验结果（SPIN?）+ BASELINE_CHANGE 注记是否恰当 +
若 rejected 列 BLOCKER。
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
