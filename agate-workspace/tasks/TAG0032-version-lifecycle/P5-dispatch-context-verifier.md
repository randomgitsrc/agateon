---
phase: P5
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: verifier
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

P5 技术验证：执行 P2-design.md §6 固化的 `gate_commands.P5*`，如实记录通过/失败，产出 `P5-test-results/`。**非 UI 任务**（P2 `ui_affected: false`），无 Playwright/E2E。

### gate_commands.P5（P2 §6 固化，逐条跑，不改命令）

| key | 命令 | 判定 |
|-----|------|------|
| P5 | `python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto` | exit 0 + failed=0 |
| P5_consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | exit 0（0 ERROR；WARNING 不阻断）|
| P5_shellcheck | `shellcheck -S warning agate/scripts/*.sh` | exit 0 |
| P5_shellcheck_root | `shellcheck -S warning install.sh` | exit 0 |
| P5_counttests | `bash agate/tests/scripts/count-tests.sh` | 跑通、输出用例数（对照文档无漂移；本任务新增 ≥16 用例，只增不减）|

- `P5_timeout_seconds: 600`（P5 pytest 含隔离 HOME 多步 install，归构建类档）→ 外层 `timeout 600s`
- 无 P5_formatter → check-tdd/baseline 退化 exit-code-only；`P5-test-results/fail-list.txt` 可省略或写空文件（无失败时）
- 命令逐条独立跑，**不用 `&&` 拼接**（短路反模式）

### 产出规格

- `P5-test-results/unit.md`：明确写 **failed 数量** + 每条 gate_commands key 的 exit code + 通过/失败汇总。含 test runner 输出签名行（`grep -cE '^(PASSED|FAILED|passed|failed)'` 计数须 >0——主 Agent N5 校验）
- `P5-test-results/fail-list.txt`：failed 测试 id 逐行（无失败 → 空文件）
- `P5-test-results/consistency.log` / `shellcheck.log` / `counttests.log`：各命令原始输出落盘（末行 `EXIT_CODE: <n>`，M1.3a 约定）
- **全量测试**：本任务 P5 跑全量 unit + regression + integration（非仅本任务用例）。发现预存失败 → 在 unit.md 标「预存失败：X（与本次改动无关）」+ 登记 `known-failures.md`（模板 `{agate_root}/assets/templates/known-failures-template.md`）；不擅自标 ✅

### 基线参考（主 Agent P4 阶段已跑，供你对照，不是免跑理由）

- unit + regression：1390 passed / 2 skipped
- integration：94 passed
- tag0032 专项：18 passed
- consistency：0 ERROR（329 WARNING，均既有叙事引用）
- shellcheck（scripts + install.sh）：rc 0
→ 你须**独立重跑全量**确认，不引用主 Agent 的数字当结果

### 约束

- **只读验证**：不改任何代码/测试/文档；不"顺手修复"（发现必要修复 → 回 P4 走正常流程，不混入 P5 commit——R9 缓解，P2-design §1.3）
- **环境**：涉及安装路径的用例靠测试自身的隔离 HOME fixture；verifier 不自行启动任何环境
- **不可逆操作**：本任务无（纯脚本 + 文档 + 隔离 HOME 测试）→ 写行首 `[NO_NEED_CONFIRM]`
- 生产环境：不触碰 → 写 `[PROD_NOT_TOUCHED]`
- `check-protocol-consistency.py` 用 **worktree 自己的**（`agate/scripts/check-protocol-consistency.py`）

### 上游关联

P4 已 commit（`1d9a322`，决策 A1 `_protocol_root` + 决策 B1 单源 copytree + install.sh --versions + UPGRADING 生命周期节；P4-review 复评 approved 0 CRITICAL）。P2-design §6 gate_commands 固化。P3 18 用例（P4 后全绿）。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（§6 gate_commands.P5* 权威——命令清单）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（env_constraints / 隔离 HOME 纪律）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 条 BDD + 范围声明——判断预存失败相关性）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1/2 + fix-1 改动清单——理解本任务动了什么）
- /home/kity/oclab/agateon/agate/assets/execution-roles/verifier.md（角色定义，稳定版——P5 模式）
- /home/kity/oclab/agateon/agate/assets/templates/known-failures-template.md（预存失败登记模板）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体（跑测试） = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片/consistency 脚本注意区分：跑 `check-protocol-consistency.py` 用 worktree 自己的，编排类工具用 `~/.agate` 稳定版。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`（pytest 9.0.3 / pyyaml 6.0.1）；shellcheck 0.9.0
- 全量 pytest 分片跑（unit / regression / integration 各一次 + `-n auto`）或按 gate_commands.P5 一条命令跑——以 gate_commands 命令为准，外层 `timeout 600s`
- **涉安装路径的用例靠 fixture 隔离 HOME**——绝不动真实 `~/.agate`（legacy 软链）
- **主 checkout 禁止改动**；测试在 worktree
- bash 外层 `timeout`（pytest 600s，consistency 120s，shellcheck / count-tests 60s）；单步串行不并行 bash 调用（pytest 内部 `-n auto` 由命令自身管理）
- 产出路径硬约束：`P5-test-results/` 目录写在 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P5-test-results/`
- 分阶段落盘：每跑完一条 gate_commands，把结果追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P5-progress.md`
- unit.md frontmatter 用 `agate-md-field-set.py`（先 `--list`）；Header 成品值：`phase: P5` / `task_id: TAG0032` / `parent: P4-implementation.md` / `trace_id: TAG0032-P5-20260907` / `agent: verifier` / `type: verification` / `status: draft` / `created: 2026-09-07`

### 返回

只返回两行：① P5-test-results/ 路径；② 一句话摘要（≤30 字：failed=N（其中预存 M），各 gate key exit code）。

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
