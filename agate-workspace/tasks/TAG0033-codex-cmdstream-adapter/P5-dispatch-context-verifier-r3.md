---
phase: P5
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: verifier
review_round: 3
---

<dispatch_guide>
> 以下派发指引是本次验证的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 本次是 P5 verifier 第 3 轮（P5→P4 回退修 F1 后的重新验证）

前情：P5 曾通过（`c00f97f`）→ P6 真机 V6 发现 **F1**（DEBT0035）→ 回退 P5→P4（`52fe210`）→
implementer 重试 #1 修 F1（`6f8422f`，新增 `_codex_is_finished` helper、fixture 补真机 `status="failed"`、
测试调整）→ P4 review r2 + alignment r3 均 approved/PASS。**本轮重新做 P5 技术验证**（F1 修改了
`agate/scripts/agate-cmdstream-adapters.py`，须重跑）。

**覆盖 `P5-test-results/`**（`unit.md` / `fail-list.txt` / `real-machine.md`——第 1 轮的旧内容作为
过程记录可在文件里保留一段「第 1 轮（F1 修复前）」历史说明，但结论速览 + 主体更新为本轮）。

### A. gate_commands.P5（逐条实跑 + 记 `unit.md` + `fail-list.txt`）

1. `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no`
   - **预期**：`1390 passed / 0 failed / 2 skipped`（1389 基线 + 1 条 F1 守护 `test_bdd_5_codex_failed_status_not_pending_guard`）。
   - failed > 0 → 逐条列出 + traceback 摘要，返回主 Agent（回 P4 判定）。
   - `fail-list.txt`：刷新为实跑 `FAILED ` 行（预期**空**）。
2. `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（⚠️ worktree 脚本）
   - **预期**：exit 0 / **0 ERROR**（~329 WARNING 历史死链，记数）。
3. `timeout 60s shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh`
   - **预期**：0 issue。
4. `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` → All checks passed。

跑完全量 pytest 后：若 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl` 被测试
追加行（已知隔离问题），`git checkout -- <该文件>` 还原 + `unit.md` 记一句，**不计失败**。
⚠️ 注意：本轮开始时 `gate-events.jsonl` 已有 1 处**合法**未提交改动（主 Agent 手动追加的 P4→P5
`state_transition` 事件——`agate-next.py` 因 check-gate P4 多提交阶段的已知局限拒绝推进，主 Agent 按
`_advance` 逻辑手动补的）。这行**不要**还原——只还原**测试追加的** `gate_run` 类行。分辨：主 Agent 补的
是 `{"event":"state_transition","from":"P4","to":"P5",...}`，测试污染的是 `{"cmd":"check-gate.py ...","event":"gate_run",...}`。

### B. 真机验证复核（`real-machine.md`）

F1 修改了 `read_commands` 的 pending 判据 → **V1 必须重跑**（用新代码解析真实 rollout）；V3/V5 复跑为
回归（子会话枚举 / feature flag 与 pending 判据无关，但顺手确认）；V4 fixture 已在第 1 轮收敛为实测
形态（`formatted_output` 的 `tokens truncated`），本轮确认 `_detect_truncated` 对该形态仍命中即可。

- **V1（rollout JSONL 解析复核——关键，因 F1 改了 pending 判据）**：
  - 读 3-5 个真实 `~/.codex/sessions/2026/09/*/rollout-*.jsonl`（含**含失败命令的**，如
    `.archived/p6-pre-retreat-20260909/real-machine-v6-detect.log` 提到的 spin 会话
    `rollout-2026-09-09T08-15-30-...jsonl`、frozen 会话，若还在；或本机任一近期含 `status:"failed"` 命令的会话）。
  - 用 ≤15 行 python `importlib` 取 `CodexAdapter`，对这些真实文件跑 `read_commands`。
  - **判据**：真机 `status="failed"` 且带 `exit_code` + `completed_at_ms` 的命令 → `CommandRecord.exit`
    是**非 0 数字**（非 None）、`exit_signal == f"exit_code={n}"`、`ts_end` 非 None、`output_hash` 非 None
    （**不再是 pending 空壳**——这是 F1 修复的核心）。真·未结束命令（`item_started` 无 `item_completed`）
    仍 → `exit is None` / `exit_signal == "pending"`。`probe` / `list_sessions` 对真实文件仍正常。
- **V6（检测引擎对真实 Codex 会话判三态——F1 修复后重跑 ③ SPIN）**：
  - `codex exec` 现场造重复失败会话（连跑 ≥6 次相同失败命令 `ls /nonexistent-xyz-p5r3`，每次 exit≠0、输出恒定）。
  - `python3 agate/scripts/agate-cmdstream-detect.py detect <该 rollout> --platform codex --now <ts_start+5s>`
  - **判据**：→ `VERDICT: SPIN`（F1 修复前是 FROZEN/NORMAL；修复后 `read_commands` 产出真实
    `(command, exit, output_hash)` 签名 → detect 能判 SPIN）。**这是 P5 重新通过的关键新证据**（P6 归属的
    V6 卡死/正常场景仍留 P6）。
  - 顺带：正常会话（几条秒级命令，输出各异）→ detect `--now 最后活动+30s` → `NORMAL`；`--now +400s` → `FROZEN`（活动冻结）。
- **V3 / V5（回归复核，简短）**：`find ~/.codex/sessions -name 'rollout-*.jsonl' -newermt '-3 days'`
  + `grep -l '"thread_source"[: ]*"subagent"'` 找子会话文件 → `CodexAdapter().list_sessions()` 枚举到 +
  `read_commands` session_id = 子文件 basename。`codex features list | grep -iE 'multi_agent'` → stable/true。
- **V4（截断形态确认，简短）**：`CodexAdapter._detect_truncated` 对 fixture 现有截断样例行
  （`formatted_output` 含 `tokens truncated`）→ True；`test_bdd_7_codex_truncated_output_hash_none` 绿。
- **V2 / V7**：归 P6（`real-machine.md` 记「延后 P6：V2 跨调用归纳 spawn_agent 键并集 / V7 嵌套深度」——
  注：P6 首轮已做过 V7（嵌套 depth 1→2 生效）+ V2（键并集无新键），结论在
  `.archived/p6-pre-retreat-20260909/real-machine-p6.md`，P6 重做时可引用/复核）。
- **V8**：待有 API-key 账号环境时补（非阻塞，`verification_env_budget` 轮次 0）。

### 约束

- **P5 不改代码逻辑**：`agate/scripts/*.py` 一律不动。真机验证只跑无害命令（`echo` / `ls` / `date`）。
  触发写 `[PROD_TOUCHED]`，未触发写 `[PROD_NOT_TOUCHED]`。
- **external-output gate**：产出必须逐命令附实跑输出摘要（passed/failed 计数），不接受无输出的「✓」。
- `unit.md` 必须含至少一行 `passed`/`failed` 字样（N5 签名校验）。
- 每步落盘 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-progress.md`（追加，标「第 3 轮」）。
- 所有 bash 命令加 `timeout <秒>s` 前缀。不推进 phase、不写 `p5_pass_commit`（主 Agent 做）。不派 review。

### 上游关联

- **DEBT0035**（`agate-workspace/debt/tech-debt.md`——F1 + closure_criteria，本轮验「detect 对真机重复失败会话判 SPIN」这条）
- **`6f8422f` wf(TAG0033-P4): 重试 #1**（F1 修复——`_codex_is_finished` helper + fixture + 测试）
- **P4-review.md 第 2 轮节 + `agate-alignment-review-2026-09-09-TAG0033-r3.md`**（均 approved/PASS——你复核不轻信，但可参照其复跑结论 1390 passed / detect SPIN）
- **`.archived/p6-pre-retreat-20260909/real-machine-p6.md` + `real-machine-v6-detect.log`**（F1 现场 + 真机 rollout 参照）
- **P2-design.md §7**（gate_commands.P5 权威）+ §5 设计点 2（含 pending 判据 BASELINE_CHANGE）
- **P1-requirements.md §7**（真机清单 V1-V8）+ §4.1 / BDD-5 / BDD-6（BASELINE_CHANGE）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/unit.md` + `real-machine.md`（第 1 轮产出——你刷新它们）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§7 gate_commands.P5 + §5 设计点 2）
3. `agate-workspace/debt/tech-debt.md`（DEBT0035）
4. `agate/scripts/agate-cmdstream-adapters.py`（`_codex_is_finished` helper + `read_commands` + `_build_record`——V1 手跑参照）
5. `agate/tests/unit/test_agate_cmdstream_adapters.py` + `test_agate_cmdstream_detect.py`（F1 相关用例——确认现绿）
6. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/.archived/p6-pre-retreat-20260909/real-machine-v6-detect.log`（V6 真机场景造法参照）
7. `agate/scripts/agate-cmdstream-detect.py`（`detect` CLI 用法——V6/V1 用）
8. `agate/assets/execution-roles/verifier.md`（角色定义）
9. `agate/phase-cards/P5-verification.md`（判定规则 / N5 签名校验 / 「如果是重试」节）
10. `AGENTS.md`（worktree 根——双工作区纪律）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P5（主 Agent 手动 `_advance` P4→P5——
  `agate-next.py` 因 check-gate P4 多提交阶段局限拒绝，已手动补 phase + state_transition 事件）/
  judge.enabled=true。HEAD = `6f8422f`（P4 重试 #1）。系统 `python3`；ruff `~/.venvs/agate-dev/bin/ruff`；
  codex-cli 0.153.4 + ChatGPT 登录。
- **F1 修复后基线**（P4 review r2 + alignment r3 双独立复跑确认——你再复跑一次）：`agate/tests/unit/` =
  1390 passed / 0 failed / 2 skipped；consistency 0 ERROR；ruff clean；真机 detect 对重复失败会话 → SPIN。
- **`_codex_is_finished`**（`agate/scripts/agate-cmdstream-adapters.py` ~line 641）：已结束 =
  `item.status ∈ {"completed","failed"}` **或** `payload.completed_at_ms` 非 None **或** `item.exit_code`
  是 `int` 非 `bool`（三者任一）；`pending = not _codex_is_finished(payload, item)`（~line 766）。
- **P5 gate 规则**（`check-gate.py P5`）：exit 2；主 Agent 验 `P5-test-results/` 存在 + failed 计数 +
  N5 签名（`grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' P5-test-results/unit.md` > 0）。
- **`p5_pass_commit`**：主 Agent 在你返回、判定 P5 通过后 `git rev-parse HEAD` 写入 `.state.yaml`——你不写。

### 产出

- 刷新 `P5-test-results/unit.md`（gate_commands.P5 四命令第 3 轮实跑计数 + 结论「F1 修复后 P5 重新通过：
  1390 passed / 0 failed」+ 保留第 1 轮历史说明段）。
- 刷新 `P5-test-results/fail-list.txt`（预期空 / 「无失败」）。
- 刷新 `P5-test-results/real-machine.md`（V1 重跑结论——真机 `status="failed"` → exit 非 None；V6 ③ →
  SPIN；V3/V4/V5 回归复核；V2/V7 延后 P6 说明；V8 待补）。

### 返回

返回：gate_commands.P5 四命令各 passed/failed/exit 计数 + 确认 1390 passed / 0 failed + `fail-list.txt`
是否空 + V1 真机 `status="failed"` 命令是否映射为 exit 非 None（非 pending）+ V6 ③ detect verdict
（应 SPIN）+ 有无真回归 + 有无 `[PROD_TOUCHED]`。
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
