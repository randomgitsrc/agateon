---
phase: P5
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: verifier
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

P5 技术验证：**独立执行** `P2-design.md §8` 固化的 `gate_commands.P5*` 全部命令，产出 `P5-test-results/unit.md`（标注 failed 数量）+ `P5-test-results/fail-list.txt`（failed 测试 id 逐行，无失败则空文件）。逐条判定通过/失败。**只跑不改**——不改任何代码 / 测试 / 配置。P5 是 external-output-gate，你的产出是主 Agent 验 gate 的依据。

### 执行的命令（P2-design §8 固化，逐条独立跑，不用 `&&` 串接）

| key | 命令 | 预期 | 超时 |
|---|---|---|---|
| `P5` | `python3 -m pytest agate/tests/ -q --tb=no` | **全量套件 exit 0 + failed=0**（含非本任务测试） | `timeout 600` |
| `P5_consistency` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | exit 0（0 ERROR；存量 ~329 WARNING 为历史叙事文件死链，`--strict-errors-only` 下不判失败） | `timeout 180` |
| `P5_events` | `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` | exit 0（账本哈希链完整、ts 单调、`dispatch_route` 理由码合法 —— 现 15 行含主 Agent 手动 `_advance` 的 P4→P5 state_transition） | `timeout 90` |
| `P5_routing_schema` | `python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` | exit 0（本任务提交的 scaffold 通过 schema 校验） | `timeout 90` |

- **无 `P5_e2e`**（`ui_affected: false`）；**无 `P5_shellcheck`**（本任务未新增 `.sh`，tmux wrapper 落为 python helper）。
- `P5` 是**全量** pytest（不加 `-k`）——P5 阶段应运行全套件含非本任务测试。用 `-q --tb=no` 紧凑模式，只保留通过/失败汇总 + 失败清单。
- 每条命令前设 shell `timeout`（上表值）。命令挂死 / 超时 → 停、progress 写一行、返回主 Agent（不自行换命令、不深入诊断）。

### 判定 + 预存失败处理

- **exit 0 + failed=0**（全部命令）→ 判「P5 全通过」。
- 任一命令 exit≠0 或 failed>0：
  - 判定是**真失败**（回 P4）还是**环境问题**（超时 / 依赖缺失 → 修复环境重跑）还是 **flaky**（记入 `P5-test-results/`、三振记录）。
  - 若是**改动前就存在的失败**（预存失败，与本任务无关）：拷 `{agate_root}/assets/templates/known-failures-template.md` → `agate-workspace/tasks/TAG0034-dispatch-routing/known-failures.md` 登记（测试文件 / 失败数 / 根因 / 是否与本任务相关）；在 `P5-test-results/unit.md` 标注「预存失败：X（与本次改动无关）」。预存失败不阻断 P5 推进。
- **本任务基线预期**（供你对照，不是让你跳过实跑）：主 Agent P4c 后自查 `python3 -m pytest agate/tests/ -q --tb=no` = **1625 passed / 0 failed / 2 skipped**；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py <task dir>` exit 0；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0。你须**独立重跑**确认，若结果与此不符如实记录、报主 Agent。

### 约束

- **环境隔离 / PROD**：dogfooding，"生产" = 主 checkout `/home/kity/oclab/agateon` + `~/.agate` 稳定版，**禁改**。仅在 worktree `.worktrees/agate-TAG0034` 内读 + 写 `P5-test-results/`。测试是纯脚本 + 文件断言 + mock，不建外部资源、不起服务、不碰生产。意外触碰主 checkout / `~/.agate` → 写 `[PROD_TOUCHED] {描述}` 立即 PAUSED 报告；否则写 `[PROD_NOT_TOUCHED]`。
- **只跑不改**：P5 不改代码 / 测试 / 配置 / 协议文档。发现 bug → 如实记录、报主 Agent 判「回 P4」，**不自己修**（R9：P5 commit 不得混入非产出文件改动）。
- **检查对象类脚本用 worktree 自己的**：`check-protocol-consistency.py` / `check-events.py` / `check-dispatch-routing.py` 都跑 `python3 agate/scripts/...`（worktree 版本），不用 `~/.agate` 稳定版（TAG0016 教训：检查对象是 worktree 里改动的东西）。
- **签名校验（N5 缓解）**：产出 `P5-test-results/unit.md` 后自跑 `grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' P5-test-results/unit.md` 确认计数 >0（有效产出），把这个 grep 结果也写进 unit.md。
- **日志尾行**：若产出可核验日志（`P5-test-results/` 下），末行写 `EXIT_CODE: <n>`（供 `check-p6-provenance.py` 一致性核验）。
- **格式**：产出文件避免行首 `- PASS` / `- FAIL`（provenance 预判检测）——P5 的 unit.md 用 pytest 原生的 `PASSED`/`FAILED` 前缀或「passed=N failed=M」汇总行，不用行首 `- PASS`。
- **命令超时兜底**：见上表；所有 bash 前 `timeout <n>s`。

> 子派发能力：不启用（P5 是只读验证，单 verifier 直接跑）。

### 上游关联

- P4 三批全部 commit：P4a `d1c2aca`（schema 层 + 引擎骨架 + 协议正文）/ P4b `99a4c19`（跨 CLI 子进程 end-to-end + I1/I2/I3/I5 + M9/M10 + A1 fix）/ P4c `92edcfc`（tmux 观测层 feature flag 默认关）。
- 三批 C8 `review` approved（`P4-review.md` status: approved，agent≠main）+ `protocol-alignment-review` aligned（`docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`，round 5，A1-A7 全 ALIGNED）。
- `.state.yaml` 现 phase=P5（主 Agent 手动 `_advance` P4→P5，DEBT0037 多提交阶段局限）；`gate-events.jsonl` 15 行含该 state_transition。
- 新增测试：`agate/tests/unit/test_tag0034_{schema,resolve,tryfall,events,native,subprocess,tmux,interaction,docs,p4b,p4c}.py` + `agate/tests/regression/test_tag0034_zero_change.py` + `agate/tests/fixtures/tag0034_*/`。P3 `pytest -k tag0034` 目标 = 90 例（P4c 后全绿）。
- BDD-39/40 回归护栏（`test_tag0034_zero_change.py`）：断言 `phases.yaml` / `check-gate.py` / `check-state-transition.py` / 状态机结构化部分 / `test_tag0027_b2_*` 逐字节 / 零改动 —— 全量 pytest 里应绿。
- A5.3 / A7.4 两条 doc-sync（`LIMITATIONS.md` 局限 2 缓解链 + `adr.md` ADR-013）+ tmux 观测层目标环境复跑 = **P8 交付项**，不在 P5 范围。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（**§8 gate_commands** —— 执行清单权威）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md` + `P4-implementation-P4b.md` + `P4-implementation-P4c.md`（三批改动清单 —— 理解改了什么，判「预存 vs 本次引入」失败）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-review.md`（三批评审结论 + INFORMATIONAL）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（env_constraints / known_risks —— PROD 隔离纪律、`--strict-errors-only` 基线）
- `agate/assets/execution-roles/verifier.md`（你的角色定义「模式一：P5 技术验证」）
- `agate/assets/templates/known-failures-template.md`（若有预存失败要登记）
- `AGENTS.md`（`--strict-errors-only` 定义、gate 脚本分层、双工作区纪律、测试约定）

### 产出文件字段

- `P5-test-results/unit.md`：全量 pytest 汇总（passed / failed / skipped 计数）+ 4 条 gate_command 各自 exit code + 「未运行全量测试」/「预存失败：X」标注（如适用）+ 签名校验 grep 计数 + 末行 `EXIT_CODE: <n>`。
- `P5-test-results/fail-list.txt`：failed 测试 id 逐行（`FAILED ` 前缀，pytest 风格）；无失败 → 空文件（仍创建）。
- 用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P5-test-results/unit.md agate-md-field-set --list` 看是否有 frontmatter 字段要填（若无则纯正文）；不要手写 frontmatter。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P5

路径：phase-cards/P5-verification.md
---
# P5 — 技术验证

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> P5 不可裁剪（核心阶段）
> ⑨ P5 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 verifier subagent（P5 模式）执行 gate_commands.P5
   1.1 写 P5-dispatch-context-verifier.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 逐条判定通过/失败
3. 若失败：判定是真失败还是环境问题 → 真失败回 P4，环境问题修复环境
4. `git rev-parse HEAD` 取当前（父）提交哈希，写入 `.state.yaml` 的 `p5_pass_commit` 字段（TAG0016 BDD-12：供 P6/P8 判定"引用 P5 证据、不重跑"，字段可选、写入时机见 `state-machine.md`「每任务独立状态文件」）
   ⚠️ **P5 commit 不得混入非产出文件改动**（真实反例：`5bdcd90` 混入了 `agate-debt-check.py` 的真实修复）——若发现顺手修复的必要性，应先回 P4 走正常流程，不要混入 P5 commit（R9 缓解措施，P2-design.md §3.2/§1.3）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + P5 产出，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P5，不要提前写 P6——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P5): {摘要}"（phase=P5，P5 产出含 P5-test-results/fail-list.txt）
7. P5 commit 完成后进入 P6：**phase 推进 P6 随 P6 产出 commit 一起**（P6-acceptance.md + P6-evidence/ 就绪后），不是单独 phase commit
   ⚠️ P5→P6 是唯一硬拦边界：P6 的 self-authored gate 拦截"非证据文件"，
      P5 的 .txt/.json 等合法产出必须在 phase=P5 的 commit 里提交，不能带进 phase=P6
   ⚠️ 不要"先 commit 产出再单独 commit 改 phase"（state-machine.md:431 明确禁止）——
      phase 与产出同 commit，P6 产出就绪时 phase 一并写 P6

## 如果是重试

→ 修复后重跑 gate_commands.P5 **全量**（T027 教训：修复可能引入回归，不能只检查修复项）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P5 MAX=2）

## 前置条件

- [ ] P4 代码已 commit（暂存区含代码文件）
- [ ] gate_commands.P5 命令在 P2 已声明（这是 gate 会执行的命令清单）

## 执行方式

verifier subagent 从 P2-design.md 读取 gate_commands.P5 并执行：

```bash
# 示例（实际命令取决于 P2 声明）
pytest -q --tb=no                    # 后端单元测试
vitest run --reporter=verbose        # 前端单元测试
playwright test --reporter=line tests/e2e/  # E2E（ui_affected: true 时）
```

紧凑输出模式：用工具的汇总模式（pytest --tb=no / vitest --reporter=dot / go test | tail -30）。只保留通过/失败汇总+失败清单，不逐项 traceback。

**技术栈无关**：gate_commands.P5_formatter 声明 formatter 脚本（可选），将测试输出标准化。见 `assets/formatters/README.md` 速查表。不提供 formatter 时退化为 exit-code-only。

## 判定规则

- **exit 0 + failed=0**：全通过 → 继续
- **exit ≠0 或 failed>0**：主 Agent 判定
  - 真 bug → 回 P4 修复
  - 环境问题（超时/端口占用/依赖缺失）→ 修复环境重新跑
  - flaky test → 记入 P5-test-results/，三振记录
- **PROD_TOUCHED**：任何生产环境触达 → 立即 PAUSED（触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`）
- **E2E 未执行**（ui_affected: true 但未跑 P5_e2e）：视为验证不完整
- **全量测试**：P5 阶段应运行全量测试套件（含非本任务测试）。发现预存失败时：
  - 在 P5-test-results/unit.md 标注"预存失败：X（与本次改动无关）"
  - 主 Agent 判断：修复成本 < 推迟成本 → 立即修复；否则记录到 known-failures.md
  全量测试不阻断 P5 推进，但未运行全量测试时须在 P5-test-results/unit.md 标注"未运行全量测试"。

## 产出规格

- P5-test-results/unit.md：标注 failed 数量（verifier subagent 产出）
- P5-test-results/fail-list.txt：verifier subagent 产出，failed 测试 id 逐行列出（`FAILED ` 前缀同上，
  pytest 参考实现），可为空文件（无失败时）。使用 gate_commands.P5_formatter 声明的 formatter 提取（与 baseline 捕获一致）。无 formatter 时可省略此文件——P5 gate 检测到缺失时优雅降级为 WARNING-only 行为，不因此新增拦截。
- UI 任务：P5-test-results/e2e.md（Playwright 实跑结果 + 截图路径，verifier subagent 产出）

## 预存失败的处理

若 verifier subagent 发现改动前就存在的失败（预存失败），按以下流程登记：

> **known-failures.md 只登预存失败**（P5 之前就存在的、与当前任务无关的）。当前任务引入的失败用 P5-test-results/ 记录。

1. 在 `{AGATE_WORKSPACE}/tasks/{Txxx}/known-failures.md`（从 `{agate_root}/assets/templates/known-failures-template.md` 拷贝模板）登记：
   - 测试文件、失败数、根因、是否与当前任务相关
2. 在 P5-test-results/unit.md 标注"预存失败：X（与本次改动无关）"
3. 主 Agent 按修复成本判断：修复成本 < 推迟成本 → 立即修复；否则记录推迟
4. 即使不立即修复，债务也可见、可追踪——不会因为"与本任务无关"而默默累积

## gate 规则

check-gate.py P5 → exit 2。主 Agent 验 gate（检查 P5-test-results/ 存在 + failed 计数），CI backstop 兜底。

**external-output-gate vs self-authored-gate**：P5 的 gate 是 external-output-gate——主 Agent 验证的是 verifier subagent 的产出（P5-test-results/），而非自己跑的命令结果。这与 P4（主 Agent 自己写代码、自己跑 lint）的 self-authored-gate 不同。external-output-gate 的信任链依赖 subagent 隔离 + CI backstop 双重保障。

## 推进条件（全部满足才写 phase: P6）

- [ ] gate_commands.P5 全部命令 exit 0 + failed=0
- [ ] UI 任务：gate_commands.P5_e2e 已执行且通过
- [ ] 无 PROD_TOUCHED 标记
- [ ] 测试环境隔离正常（对比测试前后生产库状态）

## 常见错误

1. **不跑 E2E**：UI 任务只跑单元测试和类型检查 → 端到端行为未验证。T046 教训：38 个单元测试全绿 + vue-tsc OK，但浏览器里图片是破的
2. **把测试绿了当作功能正确**：单元测试通过 ≠ 用户看到的功能正常。P5 是代码正确性验证，P6 才是用户视角验收
3. **修复后不重跑全量**：只跑修复的那一个测试 → 修复引入的回归没被发现

## P5 commit→push 窗口残余风险（N5）

**残余风险**：verifier subagent 产出 P5-test-results/ 后，主 Agent commit 并推进到 P6，但 push→CI 之前存在时间窗口。伪造的 P5-test-results 可在此窗口内流向下游。

**缓解**：主 Agent 在推进前**必须**执行签名校验——grep test runner 输出签名：

```bash
grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' P5-test-results/unit.md
```

计数 >0 才视为有效产出，计数=0 视为假完成，计为重试。这不是重跑测试（CI backstop 在 push 后兜底全量验证）。

gate 不过 ≠ 你失败了。红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 按包拆分并行（条件触发，非强制）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 时，P5 可按包拆分并行——各 verifier subagent 跑各包的 gate_commands，各写 P5-test-results/{pkg}/。

拆分判据同 P3。P5 是只读验证，无代码写冲突风险。

**但"无写冲突"不等于可以随便并行**：`gate_commands.P5` 常是全量测试套件（含 xdist 多进程）或 E2E 浏览器命令，属**资源密集型默认串行**——按 dispatch-protocol.md「派发编排机制」并行规则第 4 条处理，即使包间无依赖也默认改为串行；要并行必须先按下方「基础设施隔离」为每批分配独立端口/数据库/临时目录，无法隔离即串行（安全默认值）。判据细节见该节，本卡片不重复展开。

**环境准备职责边界（本阶段落地）**：verifier subagent **默认不自行启动环境**——debug server、测试数据库、临时端口等由主 Agent（或 P0-brief 声明的单一责任方）统一准备好，通过 dispatch-context 注入访问方式；多个并行 verifier 共享同一环境时更是如此，不允许各自启动。环境验证失败时的可重试/不可重试分类、批处理要求与止损轮次，一律按 dispatch-protocol.md「verification_env 失败处理协议」与「环境准备职责边界」执行，本卡片只做落地引用，不重复展开规则。

**基础设施隔离（本阶段特定，并行时强制）**：
- 测试端口：各 verifier 使用独立端口（与 P4 并行时分配的端口一致，或新分配）
- 测试数据库：各 verifier 用独立数据库（与 P4 隔离方案一致），不共享同一 test.db
- 临时输出：各 verifier 写入 `P5-test-results/{pkg}/` 独立目录，不共享同一 unit.md
- E2E 浏览器：Playwright 默认隔离 browser context，但若 E2E 测试启动了本地 server，各 verifier 需用不同端口

主 Agent 在并行派发前**必须**为每个 verifier 的 dispatch-context 分配独立的基础设施参数（同 P4，未分配导致冲突时计为重试）。

## 下游影响

- P6 验收在 P5 通过的基础上做用户视角验证
- P8 发布时需重跑 P5 gate（确认 bump-version 后测试仍全绿）

> 完成 → 读 phase-cards/P6-acceptance.md
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P5 / status=active / judge.enabled=true
- HEAD = `92edcfc`（P4c）；P4a `d1c2aca` / P4b `99a4c19` / P3 `c218026` / P2 `b851b1e` / P1 `f75e129`
- 主 Agent P4c 后自查（**你须独立重跑**）：全量 `pytest agate/tests/ -q --tb=no` = 1625 passed / 0 failed / 2 skipped；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0（15 行）；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0
- 工具：python 3.12.3（`/usr/bin/python3`）/ pytest 9.0.3 / pyyaml 6.0.1 —— 全量套件约 170-180s，给 `timeout 600`
- gate_commands 无 `P5_e2e` / `P5_shellcheck` / `P5_formatter`（无 formatter → `fail-list.txt` 可从 pytest `-q` 输出的 `FAILED ` 行提取，无失败则空文件）
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- P5 gate（`check-gate.py P5`）= exit 2，主 Agent 验（检查 `P5-test-results/` 存在 + failed 计数 + 签名校验 grep >0）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
