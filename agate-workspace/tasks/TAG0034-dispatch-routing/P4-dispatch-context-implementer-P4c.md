---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

实现 **P4c 批**（`dispatch_plan` static-batch 第 3 批，complexity: low，依赖 P4b，**可整体切除——不通过不影响 P4a/P4b**）：tmux 观测层。让 P3 的 `test_tag0034_tmux.py::test_bdd_37` + `test_bdd_38` 由红转绿（**不改测试断言**）。其余 tag0034 测试 + 回归护栏保持绿。产出追加 `P4-implementation-P4c.md`（与 P4a/P4b 并列）。

### 实现内容（P2-design §3.10 + 测试契约）

- **`agate/scripts/agate_dispatch_route.py` 新增两个 importable helper**（`test_tag0034_tmux.py` 契约）：
  - `build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name) -> list[str]`：
    - `tmux_available=True` → 返回 `["tmux", "new-session", "-d", "-s", session_name, "<cmd 串> | tee <capture_path>"]`（末项是一条 shell 串 —— `" ".join(cmd) + " | tee " + capture_path`）。测试断言 `"tmux"` 与 `"new-session"` 在 `" ".join(结果)` 中、`"-s " + session_name` 子串在、`"tee"` 与 `capture_path` 在。
    - `tmux_available=False` → 返回 `list(cmd)` 原样裸跑（测试断言结果 `"tmux" not in " ".join(结果)` 且 `结果[:len(cmd)] == cmd`）。
  - `tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s) -> str`（返回值 ∈ `{"kill_now", "let_countdown", "force_kill", "noop"}`）：
    - `has_clients=False` → `"kill_now"`（`list-clients` 空 → 直接 `kill-session` 跳倒计时）
    - `has_clients=True` 且 `elapsed_s <= countdown_n + margin_s` → `"let_countdown"`（有人 attach，不强杀，让倒计时收尾）
    - `has_clients=True` 且 `elapsed_s > countdown_n + margin_s` → `"force_kill"`（wrapper 异常未退出、超过 `N + 余量` → 兜底强杀）
    - 测试用例：`(has_clients=False, elapsed_s=1, countdown_n=15, margin_s=10) → "kill_now"`；`(True, 5, 15, 10) → "let_countdown"`；`(True, 26, 15, 10) → "force_kill"`
- **接入 `_default_subprocess_run`**（P4b 留的 hook 位）：子进程形态派发前 `which tmux`（或 `shutil.which("tmux")`）——成功则用 `build_subprocess_launch(..., tmux_available=True, ...)` 包裹、`tee` 到 capture 文件、路由脚本 `tail -f` capture 取结构化流；失败则裸跑（现状）。**两路径的 `dispatch_route` 留痕 + gate 结果逐字节一致**（BDD-37）。session 名 = `agate-{task_id}-{phase}-{短时间戳}`（带命名空间；`{短时间戳}` 用 `int(time.time())` 即可）。清理逻辑：先 `tmux has-session -t <session>`（容忍 `kill-session` 对已消失 session 的 exit 1）→ 按 `tmux_cleanup_action` 的返回值决定 `kill-session` / 等待。
- **`agate/dispatch-protocol.md` 派发路由子节**：补一小段「tmux 观测层（可选）」——`which tmux` 成功则包 `tmux new-session` 供人 `attach`（wrapper 自带 N 秒退出倒计时，`N` 默认 15、余量 10s 兜底强杀），失败裸跑；**明确不做** `send-keys` / `capture-pane` 内容解析给主 Agent / 跨轮 session 复用；**目标环境代表性**（本会话 WSL2 + tmux 3.4，非容器/CI/物理机）——目标部署环境须在其自己 tmux 版本复跑 research §10 验证项，不通过则停在「定稿 + 待落地验证」、不阻塞 P8。
- **折入 P4b-review 的 3 条 INFORMATIONAL**（`P4-review.md` P4b 节，若判断轻量可做；重则注明不做 + 理由）：stderr 丢弃（`_default_subprocess_run` 是否保留 stderr 供诊断）/ `except` 冗余 / `_route_main` 子进程分支无 CI 覆盖（能否加一条 mock 子进程的端到端单测进 `test_tag0034_p4c.py` 或 `p4b.py`）。

### 约束

- **回归硬约束（最高危 / BDD-39/40）**：**不改** `phases.yaml` 结构+字段 / `check-gate.py` / `check-state-transition.py` / 状态机 / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py`（第 1-8 条 + 哈希链）/ `agate-cmdstream-*.py` / `agate-dispatch.py` 既有渲染路径 / `classify_outcome` / `resolve` / `load_config` / `try_and_fall` 的既有行为（只加 tmux 包裹分支，不改回落逻辑）。改前后跑 `timeout 120 python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py agate/tests/unit/test_tag0027_b2_agate_dispatch.py agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py -q`。
- **模型购物完整性洞（R1）**：tmux 包裹**不改变** `outcome.kind` 判定 / 回落逻辑 —— 包裹只影响「子进程怎么起 + 人能不能 attach」，`classify_outcome` 拿到的 stdout 内容（经 `tee` 的 capture 文件）与裸跑一致。BDD-37 断言「两路径留痕 + gate 结果逐字节一致」正是这条。
- **不改测试**：`test_tag0034_tmux.py` 只让实现使其转绿，不动断言。新测试写进 `test_tag0034_p4c.py`。
- **平台**：`build_subprocess_launch` / `tmux_cleanup_action` 是**纯逻辑**（无 IO），CI 直接跑；`_default_subprocess_run` 里的 `shutil.which("tmux")` / 真 `tmux` 调用要能 mock（单测不真起 tmux）。本机 tmux 3.4 可手动跑一次冒烟（加 timeout），结论记 progress。
- **自查 ≠ gate**：写完自跑 `timeout 500 python3 -m pytest agate/tests/ -k tag0034 -q --tb=short`（`test_bdd_37/38` 转绿、其余全绿、无红）+ `timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（exit 0）+ `timeout 60 python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`（exit 0）+ `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py`（clean）。**不声称「P5 已过」**。
- **命令超时兜底**：所有 bash 前 `timeout <n>s`。超时/非预期失败 → 停、progress 写一行、返回主 Agent。
- **生产隔离**：dogfooding，"生产" = 主 checkout + `~/.agate` 稳定版，禁改。仅 worktree 内写。意外触碰写 `[PROD_TOUCHED]`，否则 `[PROD_NOT_TOUCHED]`。
- **SELF-GATE 预告**：本批改 `agate/scripts/agate_dispatch_route.py` + `agate/dispatch-protocol.md` + `agate/tests/**` → 触发 SELF-GATE。主 Agent commit 前派 `protocol-alignment-review`（A1-A7）+ C8 `review`，commit message 带 `self-gate-review:` trailer。
- **切除条款**：若 tmux 包裹在本机跑不通 / 目标环境代表性存疑 —— 标 `[DESIGN_GAP: tmux 包裹待目标环境验证]`，把 `build_subprocess_launch` / `tmux_cleanup_action` 留为纯逻辑函数（测试转绿）+ `_default_subprocess_run` 的接入用 feature flag / 默认关，**不阻塞**。P4c 不通过不影响 P4a/P4b 已 commit 的成果。
- **格式**：产出文件避免行首 `- PASS` / `- FAIL`。

> 子派发能力：不启用（本批轻量，直接完成）。

### 上游关联

- P4b 已 commit（`99a4c19`）：M5 端到端子进程 + I1/I2/I3/I5 + M9/M10 + A1 fix。`pytest -k tag0034` = 76 passed / 2 failed（2 红 = `test_bdd_37/38` 本批目标）。C8 review approved、protocol-alignment-review aligned（round 4）。
- `agate/scripts/agate_dispatch_route.py`（P4a+P4b）已有：`resolve` / `load_config` / `classify_outcome` / `build_dispatch_command` / `try_and_fall`（I1 白名单 + I5）/ `dispatch_once` / `presence_parse_ok` / `_default_subprocess_run`（**P4c 的 tmux hook 位在此**，P4b 已用注释标出）/ `routed_away_verdict_location` / `write_dispatch_route_event` / `DispatchContractError`。
- P4b `_default_subprocess_run` 是「先直接裸跑」——本批加 `shutil.which("tmux")` + `build_subprocess_launch` 包裹分支。
- P4b-review 3 条 INFORMATIONAL（`P4-review.md` P4b 节「转 P4c」）。
- P1-requirements.md §1 有 `[SCOPE+ ... A5.3/A7.4]`（LIMITATIONS.md 局限 2 + ADR-013）——**落 P8**，不在 P4c 范围。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（**§3.10 tmux 观测层**全节 + §4.1 P4c 行 + §10 完成标志 9）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-review.md`（P4b 节 3 条 INFORMATIONAL）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation-P4b.md`（`_default_subprocess_run` 的 hook 位 + 关键决策）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（BDD-37/38 判据 + §7「P4c 可整体切除」）
- 测试文件（验收契约）：`agate/tests/unit/test_tag0034_tmux.py`（BDD-37/38 —— 精确契约在文件头注释 + 断言）+ `agate/tests/regression/test_tag0034_zero_change.py` + `agate/tests/conftest.py`（`agate_scripts` fixture）
- 代码：`agate/scripts/agate_dispatch_route.py`（`_default_subprocess_run` 附近 —— tmux 分支落此 + 两个 helper 加此）
- `docs/design-notes/design-dispatch-routing.md:134-157`（§3 tmux 观测 —— session 命名 / 生命周期 / 退出倒计时 / 明确不做 / 环境代表性 W2）
- `docs/research/cross-platform-dispatch-mechanics.md`（附录 tmux 真机实测记录 —— `wrapper | tee capture` / `list-clients` / `kill-session` 有 client 时行为）
- `agate/dispatch-protocol.md`（「### 0. 派发路由」子节 —— tmux 小段落点）
- `AGENTS.md`（gate 脚本分层、SELF-GATE、双工作区纪律）

### 产出文件字段

新建 `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation-P4c.md`（与 P4a/P4b 并列，`agate-md-field-set` 写 frontmatter 含 `implementation_dir`）。不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
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

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P4（P4b commit `99a4c19`）/ judge.enabled=true
- P4b 后 `pytest -k tag0034` = 76 passed / 2 failed（2 红 = `test_bdd_37`（`build_subprocess_launch` 未实现）/ `test_bdd_38`（`tmux_cleanup_action` 未实现），本批目标）
- 全量 pytest（P4b 后）= 1611 passed / 2 failed / 2 skipped（2 红同上）
- `test_tag0034_tmux.py` 契约（文件头 + 断言）：
  - `build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name) -> list[str]`
  - `tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s) -> str ∈ {kill_now, let_countdown, force_kill, noop}`
  - 用例：wrap 时 `-s <session_name>` + `tee <capture_path>` 在 join；bare 时 `结果[:len(cmd)] == cmd`；cleanup `(F,1,15,10)→kill_now` / `(T,5,15,10)→let_countdown` / `(T,26,15,10)→force_kill`
- 本机 tmux 3.4（WSL2）——`build_subprocess_launch` / `tmux_cleanup_action` 纯逻辑、CI 直跑；`_default_subprocess_run` 的 `shutil.which` / 真 tmux 调用单测须 mock
- gate_commands（P2 §8 固化，不改）：`P5` = `python3 -m pytest agate/tests/ -q --tb=no`；`P5_consistency` = `check-protocol-consistency.py --strict-errors-only`
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
