---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

实现 **P4b 批**（`dispatch_plan` static-batch 第 2 批，complexity: medium，依赖 P4a）：跨 CLI 子进程 spawn end-to-end + routed-away judge 核实 + SETUP scaffold + platform-notes 结构化输出字段 + 评审打回续跑 + 折入 P4a-review 的 6 条 INFORMATIONAL（I1/I2 关系 R1 稳健性，必做；I3 端到端必需；I4/I5/I6 可选）。让 P3 的 `test_tag0034_subprocess.py::test_bdd_42` 由红转绿（BDD-33~36 已在 P4a 的 `classify_outcome` 转绿）。`test_tag0034_tmux.py`（BDD-37/38）留红（P4c）。其余 tag0034 测试 + 回归护栏保持绿。产出追加进 `P4-implementation.md`（或新建 `P4-implementation-P4b.md`，与 P4a 并列；`implementation_dir` 已声明）。

### 实现内容

- **M5 端到端子进程 spawn**（`agate/scripts/agate_dispatch_route.py` + `agate-dispatch.py`）：
  - `dispatch_once(candidate, *, dispatch_context_path, effort_supported, ...)` —— 按 `candidate.cli` 分支：`native` / `default` → 返回 `Outcome(kind="HAS_OUTPUT")` 的占位（native 由驱动会话代发，路由脚本不 spawn，`_route_main` 输出路由计划 JSON 即止，与 P4a DESIGN_GAP 一致）；`claude-code` / `codex` / `opencode` → 真 `subprocess` spawn（`build_dispatch_command` 构造命令、`build_subprocess_launch` 若 P4c 已落则包裹，本批可先直接 `subprocess.Popen` 裸跑、留 hook 给 P4c）→ 收 stdout + exit_code + 检测 `produced_files`（约定产出文件路径）→ `classify_outcome(cli, stdout=..., exit_code=..., produced_files=..., killed_reason=...)`。
  - **存活 / 卡死检测**：`cli: codex` 子进程复用 TAG0033 已合并的 `agate/scripts/agate-cmdstream-adapters.py` 的 `CodexAdapter`（`ADAPTERS["codex"]`，class ~L666）；`claude-code` / `opencode` 走既有适配器 + 子进程形式 `wait(pid)` 超时 / `kill -0` 探测失活（research §6.0.2）。卡死检测触发 kill → `killed_reason` 非空 → `classify_outcome` 归 `INFRA_ERROR`（P4a 已实现该分支，N6）。**不自造超时**——复用 RM-AG0055 命令流阈值机制。
  - **`_route_main` 端到端分支**（`agate-dispatch.py`）：`form == "chain"` 且候选是子进程形态时，跑 `try_and_fall`（P4a 已实现循环骨架）—— 逐候选 `dispatch_once` → 三类基础设施理由码则回落 → `HAS_OUTPUT` 即停、`write_dispatch_route_event`、输出 target JSON（含实际 `final` 候选）→ 全落空 → 默认派发 + `final={"cli":"default"}`。**I3 缝**：`try_and_fall` 的 `write_event(phase, tried, final)` 位置参数回调 与 `write_dispatch_route_event(task_dir, phase, *, tried, final, task_id=None)` kw-only 签名——在 `_route_main` 写适配层桥接，或统一两处签名（你定，注明）。
  - **flag 名落地前复核**（research §10）：子进程命令 `claude -p --output-format json --model X --dangerously-skip-permissions <ctx>` / `codex exec --json -m X --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox` / `opencode run --format json --auto -m provider/model[#variant] <ctx>` —— 落地前对本机 `claude --help` / `codex exec --help` / `opencode run --help` 逐条复核（Claude Code 本机 2.1.266）。有漂移标 `[DESIGN_GAP]` 报主 Agent。
- **routed-away judge 核实（BDD-42）**：`agate_dispatch_route.py` 新增 `routed_away_verdict_location(cli) -> str`，恒返回 `"TASK_DIR"`（judge 路由到 codex/opencode 子进程时，verdict + 证据仍落 `TASK_DIR`，铁律 2/3 不变 → `check-judge-verdict.py` / `check-p6-provenance.py` 平台无关照常通过）。**不改** `check-judge-verdict.py` / `check-p6-provenance.py`（BDD-42 回归断言靠这两脚本零改动 + 无平台 transcript 路径成立，主 Agent 已核）。在 `dispatch-protocol.md` 派发路由子节或 P4b 文档里注明「judge 路由到子进程时 verdict 落 TASK_DIR，不落平台 transcript 位置」。
- **M9 `agate/SETUP.md`**：新增小节「机器级档位绑定 scaffold（dispatch-routing.yaml）」，比照既有「步骤 2-Codex」per-platform onboarding 形态：说明 `agate-workspace/dispatch-routing.yaml` 的 `tier_bindings:` 由本机现状填（探测已装 CLI + 各自默认 model），能用就用、不能用不强制（不追求跨机可复现）；各 CLI 自动化环境绕过 flag（`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check` / `--auto`）小节。
- **M10 `agate/platform-notes.md`**：新增「跨 CLI 子进程结构化输出判成败字段」小节（三平台）：Claude Code `--output-format json` 的 `stop_reason` / `modelUsage`；Codex `--json` 事件流 `turn.completed` vs `turn.failed` + 顶层 `type:error` + item 级 `status:"failed"`（**turn 层为准**，退出码不可靠）；OpenCode `--format json` 的 `step_finish.part.reason` + `text` part + `ProviderAuthError`（→ infra_error）/ 纯空返回（→ no_parseable_output）。素材 = P2-design §3.7 判定表 + §5 MV1~MV7 + `agate/tests/fixtures/tag0034_*/`。（P4a 已落 effort 能力探测行，本批补结构化输出字段小节。）
- **评审打回续跑**（P2-design §3.9 / design-note §2.4a）：在 `dispatch-protocol.md` 派发路由子节或 P4b 文档写明「同 target 优先平台官方续接（`claude --resume` / `codex exec resume` / `opencode run -s <id>` / native 的 followup），失败或换 target 则全新派发；续接产出仍走假完成校验（D2）。**续接失败无客观信号是已知缺口**，按『续接优先、重起兜底』处理、不假装解决」。**不需要实现续接的自动化**（人在评审循环里），只需协议文档写清 + 若 `agate_dispatch_route.py` 有对应 hook 位则留位。
- **I1（必做，R1 稳健性）**：`try_and_fall` 回落分支显式判 `kind in {"LAUNCH_FAIL","INFRA_ERROR","NO_PARSEABLE_OUTPUT"}` 才 `continue`；其它「非 HAS_OUTPUT」kind → `raise`（契约违例大声失败），不静默当回落信号。加对应单测（可在 `test_tag0034_tryfall.py` 之外新建 `test_tag0034_p4b.py`，**不改 P3 既有断言**）。
- **I2（必做，R1 CRITICAL 边界）**：presence 级「frontmatter 可解析 + 必需锚点标题存在」的判据落在 `produced_files` 填充处（P4b spawn 侧，`dispatch_once` 判「约定产出文件是否算有产出」时）；**禁止**在 `classify_outcome` 的 `NO_PARSEABLE_OUTPUT` 分支引入结构完整度 / 内容完整度判断（否则即 R1 CRITICAL）。`NO_PARSEABLE_OUTPUT` 只判「产出文件缺失或空 / 结构化输出空返回」。
- **I3（必做）**：见 M5 的 `_route_main` 端到端分支——写适配层桥接位置↔kw 参数，或统一签名。
- **I4 / I5 / I6（可选）**：I4 混合条目 / 孤立 `effort:` 出 WARNING；I5 `_VALID_REASONS` 要么 `try_and_fall` 写事件前自校 `reason`、要么删 / 改注释为「对外契约常量」；I6 `sys.path` 注入收窄。做了在 P4-implementation 注明，不做也注明「INFORMATIONAL，P4b 判定不处理，理由 X」。

### 约束

- **回归硬约束（最高危 / BDD-39/40）**：**不改** `agate/rules/phases.yaml`（结构 + 字段）/ `check-gate.py` / `check-state-transition.py` / `state-machine.md` 结构化部分 / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py` 第 1-8 条 + 哈希链算法（第 8 条 P4a 已加，P4b 不再动它）/ `agate-dispatch.py` 既有渲染路径 / `agate-cmdstream-*.py`（复用 `CodexAdapter` 不改）。改前后跑 `timeout 120 python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py agate/tests/unit/test_tag0027_b2_agate_dispatch.py -q` 确认仍绿。
- **模型购物完整性洞（R1）**：I1 + I2 是本批对 R1 的加固。`dispatch_once` / `try_and_fall` end-to-end 后，回落**只**在 `LAUNCH_FAIL` / `INFRA_ERROR` / `NO_PARSEABLE_OUTPUT` 触发；收到 `HAS_OUTPUT`（presence 级骨架可解析）即停、交 gate、gate FAIL 走同候选 retry（不重跑 `agate dispatch route`）。`gate_fail` 不进任何枚举。
- **不改测试**：P3 的 `test_tag0034_*.py` 只让实现使其转绿，不动断言。新测试写进 `test_tag0034_p4b.py`。测试与 P2-design 矛盾 → 标 `[DESIGN_GAP]`。
- **上下文控制**：按 P2-design §6 `files_to_read` 的「P4b」段读代码（标行号片段），不整目录全读。
- **SCOPE / CLARIFY / DESIGN_GAP**：对照 P2-design §1.1（M5/M9/M10）+ §4.1 P4b 行；prompt 漏 P2 明确要做的 → `[SCOPE_GAP]`；对方案有疑问 → `[CLARIFY]`；自主决策补缺口 → `[DESIGN_GAP]`（独立成行）。
- **自查 ≠ gate**：写完自跑 `timeout 500 python3 -m pytest agate/tests/ -k tag0034 -q --tb=short`（`test_bdd_42` 转绿、`test_bdd_37/38` 仍红、其余绿）+ `timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（exit 0）+ `timeout 60 python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`（exit 0）+ `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py agate/scripts/agate-dispatch.py`（clean）。**不声称「P5 已过」**。
- **命令超时兜底**：所有 bash 前 `timeout <n>s`（pytest 全量 400-600s；CLI `--help` 复核 30-60s；单脚本 60-120s）。超时/非预期失败 → 停、progress 写一行、返回主 Agent。
- **CI 不真调 CLI**：`dispatch_once` 的子进程 spawn 单测须能 mock `subprocess`（fixture 喂结构化输出样本），不在 CI 里真起 `claude`/`codex`/`opencode`。真机复核 flag 名可以在本 worktree 手动跑一次（加 timeout），结论记进 progress。
- **生产隔离**：dogfooding，"生产" = 主 checkout + `~/.agate` 稳定版，禁改。仅 worktree 内写。意外触碰写 `[PROD_TOUCHED]`，否则 `[PROD_NOT_TOUCHED]`。
- **SELF-GATE 预告**（供主 Agent commit 规划）：本批改 `agate/scripts/agate_dispatch_route.py` / `agate/scripts/agate-dispatch.py` / `agate/SETUP.md` / `agate/platform-notes.md` / `agate/dispatch-protocol.md`（可能）/ `agate/tests/**` → 触发 SELF-GATE。主 Agent commit 前派 `protocol-alignment-review`（A1-A7）+ C8 `review`，commit message 带 `self-gate-review:` trailer。
- **格式**：产出文件避免行首 `- PASS` / `- FAIL`。

> 子派发能力：启用（执行角色，按需）—— 若判断 M5 端到端 + M9/M10 文档 + INFORMATIONAL 修 三块工作量需拆，可派子任务；优先自己按「M5 端到端 → I1/I2/I3 加固 → BDD-42 → M9/M10 文档」顺序完成，逐步骤 progress 落盘。

### 上游关联

- P4a 已 commit（`d1c2aca`）：schema 层 + 引擎骨架 + 协议正文；`pytest -k tag0034` = 57 passed / 3 failed（3 红 = `test_bdd_42` 本批 + `test_bdd_37/38` P4c）。C8 review approved、protocol-alignment-review aligned（复审轮）。
- `agate/scripts/agate_dispatch_route.py`（P4a 建）已暴露：`resolve` / `load_config` / `load_factory_defaults` / `classify_outcome`（`Outcome.kind/.reason`，四值判定 + 挂死→INFRA_ERROR 已实现）/ `build_dispatch_command`（effort 映射 + `effort_supported` 布尔）/ `resolve_native_target` / `try_and_fall`（`TryFallResult.final/.tried`，循环骨架已实现）/ `write_dispatch_route_event`（复用 `append_event`）/ `should_consult_routing_table` / `route_is_noop` + 常量 `GATE_FAIL_TRIGGERS_FALLBACK = False` / `_VALID_REASONS`。
- P4a `[DESIGN_GAP_REVIEWED]`：`_route_main` P4a 只做 resolve + 输出路由计划 JSON、端到端 try-and-fall 交 P4b（= 本批）。target JSON 契约（`form ∈ {default,chain}` / `chain` / 首候选 / `dispatch_context`）由 P4a 固化，**P4b 只增不改**（加实际 `final` 候选等字段）。
- P4a-review 的 6 条 INFORMATIONAL（I1~I6，见 `P4-review.md`「Pass 2」节）—— I1/I2/I3 本批必做。
- fixture：`agate/tests/fixtures/tag0034_{claude_code,codex,opencode}/`（P3 已 commit，静态样本，`test_tag0034_subprocess.py` 用）。
- 前置 TAG0033 v0.70.0：`agate/scripts/agate-cmdstream-adapters.py` `CodexAdapter`（class ~L666 / `ADAPTERS["codex"]` ~L878 / `_codex_is_finished` 的 `payload.item.status` 取值集 completed/failed/in_progress）—— `cli: codex` 存活检测直接复用、不改。
- P1-requirements.md §1 有 `[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4]`（LIMITATIONS.md 局限 2 缓解链 + ADR-013）——**落 P8**，不在 P4b 范围（P4b 不碰 `LIMITATIONS.md` / `adr.md`）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（§3.4 native + effort / §3.5 决策 CLI 衔接 / §3.7 判定表 + `outcome.kind` + N6/N7 / §3.9 交互表（BDD-26 vs 51、评审打回续跑）/ §4.1 P4b 行 / §6 files_to_read P4b 段 / §10 完成标志 6~8）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-review.md`（**6 条 INFORMATIONAL I1~I6**）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md`（P4a 改动清单 + 关键决策 + DESIGN_GAP）+ `P4-progress.md`
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（BDD-33~36 / 42 判据；BDD-10 `[BASELINE_CHANGE]`）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（known_risks 最高危 / research §10 复核清单）
- 代码：`agate/scripts/agate_dispatch_route.py`（P4a 全文 —— `dispatch_once` / `_route_main` 端到端加在此）、`agate/scripts/agate-dispatch.py`（`_route_main` diff）、`agate/scripts/check-events.py`（第 8 条 —— 只读确认不改）
- 测试文件（验收契约）：`agate/tests/unit/test_tag0034_subprocess.py`（BDD-33~36/42）+ `agate/tests/regression/test_tag0034_zero_change.py` + `agate/tests/conftest.py`（`agate_scripts` / `agate_root` / `run_cli` fixture）
- `agate/scripts/agate-cmdstream-adapters.py:640-900`（`CodexAdapter` / `ADAPTERS` / `_codex_is_finished` —— `cli: codex` 存活检测复用）
- `docs/research/cross-platform-dispatch-mechanics.md:96-131`（§4 沙箱绕过 flag + §5.2 子代理 model 传参）+ `:141-210`（§6 结构化输出 + 退出码可靠性 + D2 假完成校验）
- `agate/SETUP.md:170-230`（「步骤 2-Codex」per-platform onboarding —— M9 比照形态）
- `agate/platform-notes.md`（Codex 章 + P4a 已加的 effort 行 —— M10 结构化输出小节落点）
- `docs/design-notes/design-dispatch-routing.md:96-108`（§2.4a 评审打回续跑 —— 续接优先/重起兜底）
- `agate/scripts/check-judge-verdict.py` + `agate/scripts/check-p6-provenance.py`（BDD-42 —— 只读确认无平台 transcript 路径，本任务零改动）
- `AGENTS.md`（gate 脚本分层、SELF-GATE、双工作区纪律）

### 产出文件字段

追加进 `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md`（P4b 段）或新建 `P4-implementation-P4b.md`（与 P4a 并列，`agate-md-field-set` 写 frontmatter，须含 `implementation_dir`）。不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
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
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P4（P4a commit `d1c2aca`）/ judge.enabled=true
- P4a 后 `pytest -k tag0034` = 57 passed / 3 failed（3 红 = `test_bdd_42`（本批目标）+ `test_bdd_37/38`（P4c））
- 全量 pytest（P4a 后）= 1592 passed / 3 failed / 2 skipped（3 红同上，批次边界 by-design）
- `agate_dispatch_route.py` 已实现：`classify_outcome`（四值 + 挂死→INFRA_ERROR，N6/N7 方向已定）、`try_and_fall`（循环骨架，`write_event(phase, tried, final)` 位置参数回调）、`build_dispatch_command`（effort 映射）；未实现：`dispatch_once` 端到端 / `routed_away_verdict_location` / `_route_main` 端到端分支
- I1/I2/I3 = P4a-review INFORMATIONAL（`P4-review.md` Pass 2）——I1（try_and_fall 白名单化）+ I2（presence-parse 落 produced_files 侧、禁塞 NO_PARSEABLE_OUTPUT）+ I3（write_event 位置↔kw 签名桥接）本批必做
- CLI 版本（本机实测）：Claude Code 2.1.266 / codex-cli 0.153.4 / opencode 1.18.11 / tmux 3.4（均已认证；子进程单测 mock、不真调）
- gate_commands（P2 §8 固化，不改）：`P5` = `python3 -m pytest agate/tests/ -q --tb=no`；`P5_consistency` = `check-protocol-consistency.py --strict-errors-only`；`P5_events` / `P5_routing_schema` 见 P2-design §8
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
