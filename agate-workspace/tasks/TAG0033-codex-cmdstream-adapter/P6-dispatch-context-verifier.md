---
phase: P6
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: verifier
review_round: 2
---

<dispatch_guide>
> 以下派发指引是本次验收的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 本次是 P6 重做（P5→P4 回退修 F1 后）

前情：P6 首轮（因 API 限额中断）真机 V6 发现 **F1**（DEBT0035）——真机 Codex 把已结束非 0 退出命令记
`status="failed"`、原 pending 判据误判 → detect 判不出 SPIN。已回退 P5→P4 修复（`6f8422f`：新增
`_codex_is_finished` helper + fixture 补真机 `status="failed"` + 测试调整 + platform-notes.md）→ P4
review r2 + alignment r3 approved/PASS → P5 第 3 轮重验通过（`5f704a0`：1390 passed，真机 V6 ③ → SPIN）。
**本轮从零重做 P6 验收**——首轮的 `P6-evidence/` 已在 `.archived/p6-pre-retreat-20260909/` 留痕，**不复用**，
须重新产出真实证据。

产出 `P6-acceptance.md` + `P6-evidence/`：对 P1-requirements.md §6 的 **30 条 BDD 逐条**验收，每条只允许
**PASS 或 FAIL**，每条 PASS 有 `P6-evidence/` 证据引用。`ui_affected: false`——无 vision/截图，走 pytest
`-v` 实跑 + grep + 真机命令输出。**非 refactor**（标准口径）。

### BDD → 验证方式 + 证据文件（逐条，比照 TAG0031 P6 先例）

| BDD | 验证方式 | 证据文件 |
|---|---|---|
| BDD-1~12 | `timeout 60s python3 -m pytest -v agate/tests/unit/test_agate_cmdstream_adapters.py::<对应 test_bdd_N_codex_*>`（逐条 `-v`）| `bdd-01.log`~`bdd-12.log` |
| BDD-13~17 | `timeout 60s python3 -m pytest -v agate/tests/unit/test_agate_cmdstream_detect.py::<对应 test_bdd_N_codex_*>` | `bdd-13.log`~`bdd-17.log` |
| BDD-18 | `timeout 300s python3 -m pytest agate/tests/unit/ -q`（预期 **1390 passed / 0 failed / 2 skipped**——1389 + F1 守护）| `bdd-18.log` |
| BDD-19 | `pytest -v ...::test_bdd_6_detect_consumes_registry_zero_change` + `git diff main...HEAD -- agate/tests/unit/test_agate_cmdstream_adapters.py`（:319 断言改包含式）| `bdd-19.log` |
| BDD-20 | `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（⚠️ worktree 脚本）→ exit 0 / 0 ERROR | `bdd-20.log` |
| BDD-21 | `git diff main...HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py`（**须为空**）+ `git diff main...HEAD -- agate/scripts/agate-cmdstream-adapters.py` 里既有三 class 体无改动（只新增 `CodexAdapter` + `_codex_is_finished`/常量/助手）+ `pytest -v ...::test_bdd_21_command_record_ten_fields_unchanged ...::test_bdd_21_detect_thresholds_unchanged` | `bdd-21.log` |
| BDD-22~27 | `pytest -v agate/tests/unit/test_codex_platform_docs.py::<对应 test_bdd_N>` + 补 `grep -nE "<该 BDD 关键锚词>" agate/platform-notes.md`（22~26）/ `agate/SETUP.md`（27）| `bdd-22.log`~`bdd-27.log` |
| BDD-28 | `git log --oneline --grep="self-gate-review\|self-gate-skip"`（本任务提交范围）+ `ls agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033*.md`（**3 个**：r0/r2/r3，`agent != main`——读首部 reviewer 声明）+ `check-protocol-consistency.py --strict-errors-only` 0 ERROR | `bdd-28.log` |
| BDD-29 | `grep -nE "^\| V[1-8] " agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§7 表 V1-V8 每行四要素）+ V8 标「待有该环境时补（非阻塞）」+ `verification_env_budget` 占位 | `bdd-29.log` |
| BDD-30 | `grep -nE "V2\|穷尽\|spawn_agent.*schema\|逐字输出" P1-requirements.md`（§7 含「穷尽 spawn_agent 参数 schema」项 + P1「令模型逐字输出内部 tool schema」不可用 + P5-P6 换法 + 通过判据）| `bdd-30.log` |

**F1 修复带来的 BDD 变化（验收时注意）**：
- **BDD-5** Given 现为 `item.status=="failed"`（`[BASELINE_CHANGE]` 已在 P1 §6，DEBT0035），Then 加强
  为 `exit==2` / `ts_end` 非 None / `output_hash` 非 None。验收对 `test_bdd_5_codex_failed_exit_code_verbatim`
  实跑 `-v` 确认这些断言。
- **BDD-6** Given 收紧为「真·未结束（`item_started` 无 `item_completed` 且无 `completed_at_ms`/`exit_code`）」
  （`[BASELINE_CHANGE]`）。Then 判定语义不变。
- **BDD-15** fixture/构造改用 `status="failed"` 重复失败 → SPIN（`test_bdd_15_codex_invalid_repeat_spin`）。
- 另：新增守护 `test_bdd_5_codex_failed_status_not_pending_guard`（无 BDD 编号）——**不单列 PASS 行**，
  在 BDD-5 或 BDD-6 的证据 log 里带上即可。

### P6 阶段的真机验证清单（P1 §7 归 P6 的 V6 全场景 / V7 / V2——记 `P6-evidence/real-machine-p6.md`）

本机 codex-cli **0.153.4** + ChatGPT 登录。命令加 `timeout`。**首轮已做过 V7 / V2**（结论在
`.archived/p6-pre-retreat-20260909/real-machine-p6.md`）——本轮可**引用 + 简短复核**，不必从头重做；
V6 因 F1 修复**必须完整重做**（三态）。

- **V6（检测引擎对真实 Codex 会话判三态——F1 修复后完整重做）**：造 3 个真实 rollout：
  ① 卡死会话（`codex exec` 派 `sleep 600`，中途 SIGINT——留下真·未结束命令）② 正常会话（几条秒级命令，
  输出各异）③ 重复失败会话（同一失败命令连跑 ≥6 次）。对每个跑
  `python3 agate/scripts/agate-cmdstream-detect.py detect <rollout> --platform codex --now <虚拟时刻>`。
  **判据**：① → `FROZEN`（调用/活动冻结）② → `NORMAL` ③ → **`SPIN`**（F1 修复后应成立——P5 r3 已证，
  P6 独立再证）。三态齐 = V6 完整通过，作 BDD-13~17 的真机佐证。
- **V7（`spawn_agent` 嵌套深度——引用首轮 + 简短复核）**：首轮结论：嵌套 `spawn_agent` 生效（depth 1→2
  递增），`list_sessions` 的 `os.walk` 天然覆盖任意深度独立文件，契约不受影响；既有 `platform-notes.md`
  `max_depth=1` 注记已被实测超越（有「待 V7 复核」时效指针）。本轮：读
  `.archived/p6-pre-retreat-20260909/real-machine-p6.md` V7 节引用其结论；**可选**现场再派一个嵌套
  `spawn_agent` 简短复核 depth 字段行为。**结论出来后**——platform-notes.md 的「嵌套深度未测（V7 归 P6）」
  是否回写：若你判断值得回写（改「已实测 depth=2 可用」），属文档收敛，需重跑 `test_codex_platform_docs.py`
  + consistency 0 ERROR 确认；嫌动文档麻烦则只在 `real-machine-p6.md` 记结论、platform-notes.md 留原样——
  **二选一，写清理由**。若回写，**明确报告主 Agent**（P6 self-authored gate 硬拦非证据文件，回写
  platform-notes.md 需主 Agent 判断是否单独处理 / 回 P4）。
- **V2（`spawn_agent` schema 键并集——引用首轮 + 简短复核）**：首轮跨 9 次真实调用键并集 =
  `{task_name, message, model, reasoning_effort, fork_turns}`，**无 `[自述]` 之外的键**（无 `background`/
  `timeout`/`permission`），但样本有限不等于穷尽——`platform-notes.md` `[自述]` 标注保持。本轮引用该结论
  + 可选再派 2-3 次不同参数组合复核键并集，确认无新键。

### 关键约束（不可违反）

1. **P6 是 self-authored gate**——`pre-commit-gate.sh` 硬拦截 phase=P6 时暂存的**非证据文件**（不在
   `P6-evidence/` 下的）。**不改任何 `agate/` 下代码/文档/测试/fixture**（V7 回写 platform-notes.md 的
   例外见上——必须先报告主 Agent）。验收报告 + 证据是 P6 唯一产出面。
2. **验收报告记录验收时的事实**——某 BDD 实跑 FAIL 就写 FAIL。FAIL > 0 → 主 Agent 诊断退回，不在 P6 改代码。
3. **证据文件有实质内容**——pytest `-v` 实跑输出（含 `PASSED`/`FAILED` + 用例名 + 计数），不接受 1 行充数。
4. **PASS 行格式**：`- PASS BDD-NN: {描述} ({证据路径})`（路径相对 `P6-acceptance.md` 目录）。多文件逗号分隔。
   总结行**不用** `- PASS`/`- FAIL` 行首（用 `**Summary**: 30/30 PASS, 0 FAIL`）。
5. **交叉核对节**：确认「30 条 BDD（BDD-1~30）逐条实跑，PASS + FAIL = 30，与 P1-requirements.md §6
   全部 BDD 编号一一对应，无遗漏、无重复」。
6. **post-test 环境残留检查**（P6 卡强制步骤）：真机验证在 `~/.codex/sessions/` 生成测试用子会话
   rollout 文件——只读观察产物、非 agate 生产环境残留。`real-machine-p6.md` 记一句「`~/.agate` +
   worktree `agate/` git 状态未被测试改动」。跑 `git status --short`（应只有 P6-acceptance.md + P6-evidence/
   + .state.yaml + gate-events.jsonl 的合法未提交台账）确认无意外改动。
7. **不碰生产环境**：codex exec 只跑无害命令（echo/sleep/ls/date）。触发写 `[PROD_TOUCHED]`，未触发写 `[PROD_NOT_TOUCHED]`。
8. **所有 bash 命令加 `timeout <秒>s` 前缀**；每步落盘 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6-progress.md`。
9. **不派 judge**——P6.5 judge 复核由主 Agent 在你返回、P6 gate 通过、P6 commit 后单独派。

### 上游关联

- **P1-requirements.md §6**（30 BDD 原文——验收基准；BDD-5/6 含 `[BASELINE_CHANGE]`）+ §7（V6/V7/V2）
- **P5-test-results/**（第 3 轮：`unit.md` 1390 passed / `real-machine.md` V1/V6③ PASS）
- **P2-design.md §5**（五设计点定论 + 设计点 2 pending 判据 `[BASELINE_CHANGE]`）
- **P3-test-cases.md**（BDD → test id 映射 + 验证层归位表）
- **P4-implementation.md**（adapter-core §2/§3 + protocol-docs 批 + 「重试 #1（F1 修复）」节）
- **DEBT0035**（`agate-workspace/debt/tech-debt.md`——closure_criteria「detect 对真机重复失败会话判 SPIN」
  本轮 V6 ③ 验证；「P5/P6 重新通过」本任务收尾时闭合）
- **`.archived/p6-pre-retreat-20260909/real-machine-p6.md`**（首轮 V6/V7/V2 结论——V7/V2 引用）
- **agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033{,-r2,-r3}.md**（3 个——BDD-28 SELF-GATE 留痕）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§6 全 30 BDD + §7 真机清单）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md`（BDD → test id 映射 + 验证层归位表）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（§3 转绿确认 + 重试 #1 节）
4. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/unit.md` + `real-machine.md`（P5 r3 基线）
5. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§5 设计点定论 + BASELINE_CHANGE）
6. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/.archived/p6-pre-retreat-20260909/real-machine-p6.md`（首轮 V7/V2）
7. `agate/tests/unit/test_agate_cmdstream_adapters.py` + `test_agate_cmdstream_detect.py` + `test_codex_platform_docs.py`（逐条实跑对象——先 `pytest --collect-only -q <三文件> | grep -iE "codex|bdd"` 拿确切 test id）
8. `agate/platform-notes.md`（Codex 章——BDD-22~26 grep 锚 + V7 回写候选位）
9. `agate/SETUP.md`（Codex 小节——BDD-27）
10. `agate/scripts/agate-cmdstream-detect.py`（BDD-21 零改动核对 + `detect` CLI 用法——V6）
11. `agate/assets/execution-roles/verifier.md`（角色定义——P6 模式）
12. `agate/phase-cards/P6-acceptance.md`（产出规格 / PASS 行格式 / provenance 审计 / post-test 残留检查）
13. `AGENTS.md`（worktree 根——双工作区纪律、工具纪律）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P5（P6 产出 commit 随 P6-acceptance.md
  + P6-evidence/ 推进 P6；`p5_pass_commit=6f8422f`）/ judge.enabled=true。P5 已 commit（`5f704a0`）。
  ⚠️ `gate-events.jsonl` + `.state.yaml` 有合法未提交痕迹（主 Agent 手动 `_advance` P4→P5）——不要动。
  系统 `python3`；codex-cli 0.153.4 + ChatGPT 登录。
- **当前测试基线**（你逐条实跑复核）：`agate/tests/unit/` = 1390 passed / 0 failed / 2 skipped；
  `check-protocol-consistency.py --strict-errors-only`（worktree）exit 0 / 0 ERROR；`test_codex_platform_docs.py` 8 passed。
- **F1 修复已验**（P4 review r2 / alignment r3 / P5 r3 三方）：真机 `status="failed"` → exit 非 None；
  重复失败会话 detect → SPIN。本轮 P6 V6 独立再证。
- **30 BDD 全部本阶段给 PASS/FAIL + 证据**（BDD-22~27 文档已由 protocol-docs 批 P4b 补齐、现绿——
  P6 不再「归 P7」跳过）。
- **BDD-21 `git diff main...HEAD`**：`agate-cmdstream-detect.py` / `agate-cmdstream-ir.py` 相对 main **应无 diff**；
  `agate-cmdstream-adapters.py` 相对 main 只应有 CodexAdapter 新增（class + `_codex_is_finished` helper +
  2 常量 + `_codex_int_or_none` + ADAPTERS 加一行 + import shlex），既有三 class 体无改动。
- **P6 gate 三脚本**：`check-p6-format.py --fix`（主 Agent 跑）→ `check-gate.py P6`（FAIL=0 / 总数>0）→
  `check-p6-evidence.py`（证据非空 / 被引用）→ `check-p6-provenance.py`（证据-结论对应 / dispatch-context
  审计 / BDD 对照 PASS+FAIL ≥ P1 BDD 数 / 审计 7 P5 证据复用判定——`p5_pass_commit=6f8422f`，P5→P6 间
  只有 P5 产出改动，审计 7 大概率 `reuse_allowed`，但本任务不走「复用 P5 证据」口径，逐条独立跑）。
  **你的 P6-acceptance.md 必须 agent≠main**。
- **P6.5 judge**：主 Agent 在 P6 commit 后单独派 judge（fresh context 逐条重验全部 30 BDD）——你不管，
  只管把 P6-acceptance.md + 证据做扎实、可被 judge 独立复核。

### 产出文件字段

先 `Write` 出 `P6-acceptance.md`（30 条 PASS/FAIL 行 + 交叉核对节 + `[PROD_NOT_TOUCHED]`），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6-acceptance.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter：`phase=P6`、`task_id=TAG0033`、`type=acceptance`、`parent=P5-verification.md`、
`trace_id=TAG0033-P6-20260909`、`status=draft`、`created=2026-09-09`、`agent=verifier`、
`pass`（int，预期 30）、`fail`（int，预期 0）、`ui_affected: false`。

### 返回

返回：P6-acceptance.md 路径 + pass/fail 计数（预期 30/0）+ 逐条是否全 PASS（否则列 FAIL + 根因）+
`P6-evidence/` 文件清单 + V6 三态结果（① FROZEN ② NORMAL ③ SPIN?）+ V7/V2 复核结论 + 是否有需回写
platform-notes.md 的发现（V7 回写与否 + 理由）+ 有无 `[PROD_TOUCHED]`。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P6

路径：phase-cards/P6-acceptance.md
---
# P6 — 验收

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → P6 不可裁剪。no_behavior_change 可简化（快速验收），不可省略。
> `change_type: refactor` 的任务（P1 frontmatter 声明）P6 **换用回归验收口径**（换口径 ≠ 裁 P6，P6 仍不可裁剪）——见下方「refactor 任务：回归验收口径」。

## 如果是首次进入本阶段

1. 派发 verifier subagent → 产出 P6-acceptance.md + P6-evidence/
   1.1 写 P6-dispatch-context-verifier.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. UI 任务：派 vision-analyst → 产出 vision-reports/（P1 vision 能力 GAP 降级时改走
   人工复核记录路径——截图/帧序列证据 + `(manual-review: <file>)` 引用，不派 vision-analyst）
3. 主 Agent 逐条核实 BDD 对照结果
4. **post-test 环境残留检查（强制步骤）**：验收测试执行完毕后、记录 PASS 证据前，先做环境残留检查——
   快照比对（测试前环境快照 vs 测试后）或清理钩子验证（创建型测试的清理钩子已执行、无残留对象）二选一；
   发现残留先清理并记录，残留未清不计入 PASS 证据。
5. **功能验证和 gate 格式都必须满足**（T046 教训：先做功能验证，不要只凑格式）
6. **运行 `python3 $AGATE_ROOT/scripts/check-p6-format.py --fix "$TASK_DIR/P6-acceptance.md"`** 归一化 PASS/FAIL 大小写和行首空白（verifier 产出后、gate 前，① 自动格式化）
7. 预跑 check-gate.py P6 + check-p6-evidence.py + check-p6-provenance.py
8. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P6，不要提前写 P7——phase = 本 commit 的产出阶段
9. git commit -m "wf({Txxx}-P6): {摘要}"（phase=P6，P6 产出含 P6-acceptance.md + P6-evidence/）
10. P6 commit 完成后进入 P7：**phase 推进 P7 随 P7 产出 commit 一起**（P7-consistency.md 就绪后），不是单独 phase commit
11. **P6.5 judge 复核（强制，所有任务）**：P6 commit 后、P7 前，主 Agent 写 `P6.5-dispatch-context-judge.md`（白名单输入，见 dispatch-protocol.md「Judge 信息隔离」节）→ 派发 judge（fresh context 逐条重验**所有** BDD，含已 PASS 项，只信证据与 git log）→ judge 产出 `P6.5-judge-verdict.md` → 主 Agent 跑 `check-gate.py P6.5 $TASK_DIR`（= check-judge-verdict.py + check-events.py 双 exit 0；**历史任务无 `judge.enabled: true` 自动跳过**）→ 通过 → verdict 随 commit 落库（**phase 保持 P6**，P6.5 非独立 phase 值）→ 写 `phase: P7`

## 如果是重试

确认上一轮失败原因（BDD 不覆盖 / 证据不足 / gate 格式拦截）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P6 MAX=2）

## 核心原则 ⚠️

**功能验证和 gate 格式都必须满足。** T046 教训：花 2 小时凑 PASS 格式，没花 5 分钟检查 API 响应头。不接受只满足格式不验证功能，也不接受只验证功能不满足格式。gate 是必要条件（格式不对 → commit 不了），不是充分条件（格式对了 ≠ 功能正确）。

**验收报告记录的是验收时的事实，不是修复后的状态。** P6-acceptance.md 的 PASS/FAIL 声明必须基于 evidence 文件的实际输出。如果验收时 BDD 为 FAIL，写 FAIL——修复后重新验收时再改 PASS。不能在同一个 P6 acceptance 里写"修复后 PASS"。

## 前置条件

- [ ] P1-requirements.md BDD 验收条件完整（含 SCOPE+ 增补）
- [ ] P1 声明的 capability_requirements 中 ability 为 available

## 派发

- **角色**：verifier（`{agate_root}/assets/execution-roles/verifier.md`）
- **UI 任务追加**：vision-analyst（`{agate_root}/assets/execution-roles/vision-analyst.md`）
- **输入**：P1-requirements.md + P5-test-results/
- **输出**：P6-acceptance.md + P6-evidence/

## 产出规格

### P6-acceptance.md

- BDD 逐条对照，每条只允许 PASS 或 FAIL（不允许"调整/跳过/覆盖"）
- 所有 PASS 必须有文件引用：`- PASS Bxx: 描述 (p6-bxx.png)` 或响应日志/断言文件
- UI 任务：操作类 BDD 截图必须互不相同（md5 去重），查询类 BDD 可不截图但须有断言记录文件
- UI 任务：每条 UI 类 PASS 的视觉证据按 **P1 vision 能力三态分档** + **渲染形态选择形式**：
  - **available / supplementable**（P1 capability_requirements 视觉条目 status；无声明默认
    available 语义）→ 含 vision 引用 `(vision: vision-reports/bxx.yaml)`（blocker_count=0）
  - **GAP**（无视觉能力，走降级链）→ 视觉证据 = 截图/帧序列 + **人工复核记录**引用
    `(manual-review: review-bxx.md)`，不要求 vision YAML；复核记录文件必须存在
  - **渲染形态**（P1 frontmatter `ui_render_shape`，缺失=常规布局型）选证据形式：常规布局型 =
    截图/行为日志；渲染组件型可选用**帧序列**（`frames/{bdd-id}-{NN}.png`，PASS 行引首末帧）、
    **渲染输出对比**（`renders/{bdd-id}-{variant}-actual.png`/`-reference.png`/`-diff.json`，
    PASS 行引 actual + diff，diff.json 含量化度量）或**时序截图**
    （`screenshots/{bdd-id}-t{N}.png` 时刻后缀）；帧序列与 `-tN` 时序截图按"同 BDD 证据组
    （bdd-id 前缀）"同权豁免 avg-hash 雷同判定
  - **输入态/交互形态变化类 BDD**（When 子句含输入动作或动作/特效/时序触发）→ 结论必须附
    **人工复核记录**（复核人/复核时间/复核结论），不能仅由自动断言通过——判定标准见
    `assets/execution-roles/verifier.md`
  - **雷同截图降级待复核**：avg-hash 高度相似截图（非逐字节相同）跨 BDD 组重复 → 须附
    `雷同截图复核` 记录或 manual-review 引用（复核人确认"确为不同操作但视觉相近"）才放行；
    无复核记录 → check-p6-evidence 拦截（exit 1）

`pass:`/`fail:`/`ui_affected:` 汇总写在文件头 **frontmatter**（`---` 分隔块），不写正文。
**可直接复制的完整样例**：
```yaml
---
phase: P6
task_id: TAG0001           # 替换为实际任务编号
type: acceptance
parent: P5-verification.md
trace_id: T001-P6-20260101 # {task_id}-P6-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: verifier
# ── v2.0 机器汇总 ──
pass: 28                          # int ≥0
fail: 0                           # int ≥0
ui_affected: false                # bool（与 P2 声明一致）
---
```

**PASS 行最小格式规范**：

```
- PASS BDD-NN: {描述} ({证据路径})
```

证据路径格式：
- 截图：`(screenshots/{filename}.png)`
- vision：`(vision: vision-reports/{filename}.yaml)`
- 其他：`(result.json)` / `(assert.log)` / `(P6-evidence/{filename})` / ...
- 多文件引用（逗号分隔）：`(file1.json, file2.log)` / `(screenshots/a.png, screenshots/b.png)`

描述文本可自由添加，不影响解析（provenance 脚本用精确正则提取路径）。

**总结行格式**：行首 `- PASS`/`- FAIL` 只用于 BDD 条目，不得用于总结行。总结行用其他格式（如 `**Summary**: 34/34 PASS, 0 FAIL`）。check-p6-format.py `--fix` 会自动修正违规总结行。

### P6-acceptance.md（refactor 任务：回归验收口径）

> 适用：P1 frontmatter 声明 `change_type: refactor` 的任务（P2-design.md §3.2）。功能任务（缺省）走上方既有口径，不受本节影响。

refactor 任务无新增功能行为可验收，P6 验收口径 = **行为不变声明 + 全量回归全绿 + 关键路径 BDD 逐条**，固定为三段式：

1. **行为不变声明节**：verifier 自声明"本次重构仅改变内部实现，不改外部行为；判定依据 = 全量回归全绿 + 关键路径 BDD 逐条 PASS；**禁止为凑验收数量新增功能性质 BDD**（禁止伪造功能 BDD）"。
2. **全量回归全绿节**：以"全量回归全绿"为一条关键路径 BDD 的 PASS 行——`- PASS BDD-NN: 全量回归全绿（重构后完整测试套件 0 失败）(P6-evidence/regression.log)`，其中 regression.log 为全量回归套件实跑输出，尾行 `EXIT_CODE: 0`（check-p6-provenance.py 审计 5 核对）。
3. **关键路径验收节**：其余关键路径行为不变断言 BDD 逐条 PASS/FAIL（每条带证据引用）。

frontmatter 额外声明 `regression_pass: true`（bool，可选字段）：
```yaml
# ── v2.0 机器汇总 ──
pass: N
fail: 0
ui_affected: false
regression_pass: true      # refactor 口径：全量回归全绿声明（change_type=refactor 时 gate 必校验）
```

约束：
- **回归双证是硬校验**：`regression_pass: true` + `P6-evidence/regression.log` 存在是 check-gate.py P6 对 refactor 任务的强制要求，任一缺失 → gate exit 1（BDD-4）。回归检查独立于关键路径 FAIL 判定，关键路径 PASS 不能豁免。
- **regression.log 必须被一条 PASS 行引用**（满足 check-p6-provenance.py 审计 1c 证据引用 + 审计 5 EXIT_CODE 核对）。
- **禁止新增非 BDD 编号 PASS 行**：check-p6-format.py 只认 `- PASS|FAIL BDD-N` 行，回归结果不能单列 `- PASS REGRESSION: ...`——"全量回归全绿"作为一条关键路径 BDD 的 PASS 行呈现，多文件证据用逗号分隔。
- **BDD 编号机制不豁免**：refactor 任务 P1 仍须 ≥1 条"关键路径行为不变断言" BDD，P6 逐条 PASS/FAIL 对照（check-p6-provenance.py 审计 3 的 PASS+FAIL ≥ P1 BDD 数 对 refactor 不豁免）。
- **no_behavior_change 不豁免回归双证**：refactor 口径只看 change_type，即使任务声明了 no_behavior_change，回归双证仍强制（BDD-6）。
- **禁止伪造功能 BDD**：禁止为凑验收数量新增功能性质 BDD——refactor 任务的 BDD 都是关键路径行为不变断言。

### P6-acceptance.md（引用 P5 证据、不重跑：BDD-12/13）

> 适用范围：`change_type: refactor` 任务的「全量回归全绿」证据（上方口径要求独立 `regression.log`）。TAG0016 起，当 P5 通过点到本次 P6 发起时点之间**无非产出文件改动**时，可引用同一份 `P5-test-results/`，不必再独立跑一次全量回归产出 `regression.log`。

判定依据：`check-p6-provenance.py` 审计 7（`audit7_p5_evidence_reuse`，读取 `.state.yaml` 的可选字段 `p5_pass_commit`，比对 `p5_pass_commit..HEAD` 间的改动，排除 `agate-workspace/tasks/` 前缀后判定）：

- **`reuse_allowed`**（无非产出文件改动）→ 允许「行为不变声明」引用 `P5-test-results/` 路径作为全量回归证据的 PASS 行引用（如
  `- PASS BDD-NN: 全量回归全绿（复用 P5 通过证据，P5→P6 间无代码改动）(../P5-test-results/unit.md)`），不必新产出 `P6-evidence/regression.log`
- **`reuse_blocked`**（检测到非产出文件改动，含 BDD-13 场景：P6→P4 修复后重到 P6 但未重跑 P5）→ 仍要求按上方既有口径独立产出 `P6-evidence/regression.log`（尾行 `EXIT_CODE: 0`），不得声明复用
- **`no_reuse_claim_possible`**（`.state.yaml` 无 `p5_pass_commit` 字段，存量任务兼容）→ 静默回退，等同 `reuse_blocked`，按既有口径独立产出 `regression.log`

**gate 门槛**：若 P6-acceptance.md 已写"引用 P5 证据"类表述但审计 7 判定为 `reuse_blocked`，`check-p6-provenance.py` 拦截（exit 1，GATE PROVENANCE），要求重跑 P5 后再走 P6。判定方向保守——失败只会导致"本可复用却被要求重跑"，不会出现"应重跑却被放行"的安全漏洞。

### P6-evidence/

- 必须非空，每个文件含实质内容（截图 >1KB，断言文件含实际输出）
- 不接受 1 行文本文件充数（T046 教训：15 个 1 行 txt 文件凑 provenance 数量）
- 元素级截图建议使用父级元素 + padding，避免过小截图（≤1KB 虽不阻断但会触发 WARNING）
- 操作类 BDD 截图必须互不相同（md5 完全重复会被 hook 硬阻断，无例外）。
  若某个行为差异类 BDD 天然会产出视觉相同的页面（如两个不同查询都命中同一个空状态），
  优先改用非截图证据（断言日志 / response.json）而非截图，或截图时带上能体现差异的元素
  （如带时间戳的调试面板、高亮差异区域），确保截图本身逐字节不同。
  查询类 BDD 本来就可以不截图，这类场景应优先归为查询类而非勉强用截图。

### vision-helper 结论绑定 ⚠️

- `ui_affected: true` 时至少一条 PASS 基于 vision-helper 报告
- vision-helper 报 `blocker_count > 0`：不能仅用程序化指标（naturalWidth>0, complete=true, HTTP 200）反驳
- 必须追查根因（curl -I 检查响应头 / DevTools Network / API 日志），追查结果写入 P6-acceptance.md
- **真实视觉分析（BDD-10）**：P1 显式声明视觉能力 status=available 时，P6 必须执行**真实视觉分析**
  ——按所选证据形式（截图/帧序列逐帧描述帧间差异与时序/渲染输出对比描述结果差异）→ 结构化描述 →
  判定 BDD；**不得仅以 naturalWidth>0 / complete=true / HTTP 200 / 像素方差断言视觉 PASS**。
  视觉分析对象不写死工具/技术栈（vision YAML 由 vision-analyst 产出，形式随渲染形态适配）；
  渲染组件型任务的真实视觉分析按所选证据形式执行：帧序列逐帧描述 → 时序/动效判定、渲染输出对比
  → 结果差异描述 → 判定（anchor 为 P1/P2 定义的量化判据）。渲染正确性/时序/动效类 BDD 的判据
  必须有量化锚点（渲染结果对比 + diff 度量/帧时间戳对齐/动效起止状态断言），禁主观词。

## gate 规则

```bash
check-p6-format.py --fix $TASK_DIR/P6-acceptance.md  # ① 自动格式化（verifier 产出后、gate 前）
check-gate.py P6 $TASK_DIR      # FAIL=0 / 总数>0
check-p6-evidence.py $TASK_DIR  # 证据目录非空 / UI截图>1KB / md5去重
check-p6-provenance.py $TASK_DIR # 证据-结论对应 / dispatch-context审计 / BDD对照 / P5证据复用判定（审计7，BDD-12/13）

# ── P6.5 judge 复核（强制，所有任务；历史任务无 judge.enabled: true 自动跳过）──
check-gate.py P6.5 $TASK_DIR    # = check-judge-verdict.py + check-events.py 双 exit 0
```

- FAIL > 0 → gate exit 1 → 回 P4

格式问题 → 运行 check-p6-format.py --fix 归一化 → 再验 gate → … → 通过（⑩迭代循环，格式迭代和 gate 重试共享 retry 预算）

**⚠️ FAIL > 0 时，主 Agent 不能直接改项目源码让它变绿**：P6 是 self-authored gate（判定对象是 verifier 自己写的 P6-acceptance.md），验收阶段本身不应该有代码变更——`pre-commit-gate.sh` 会硬拦截 phase=P6 时暂存的非证据文件（不在 `P6-evidence/` 下的文件）。正确流程：诊断问题出在哪个上游阶段 → 退回该阶段（`agate/rules/state-transitions.md` 回退规则，退回前须先跑 `agate-archive-stale-outputs.py` 归档当前 P6 产出，或用 `agate-retreat-to.py` 自动化多步回退）→ 重新派发对应角色 subagent 修复 → 重新走到 P6 时，旧的 P6-acceptance.md/P6-evidence/ 已被归档清空，verifier 必须重新产出真实证据，不存在"挑几条改改、其余沿用旧结论"的空间。**回退落地后必须建 DEBT 条目**（`source: retreat`，`evidence` 引用 retreat 提交哈希，模板 `assets/templates/tech-debt-template.md`——TAG0001 强制，见 `agate/rules/state-transitions.md` 回退规则节）。

## 按包拆分并行（条件触发，受限模式）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry 见 dispatch-protocol「派发编排机制」并行规则。**P6 例外**：P6 的汇总整合走自身证据并行 + 汇总 verifier 机制（下方），不适用权威节共享文件统一后处理规则。

P6 采用**证据并行、验收文件不并行**模式：

1. 各包 verifier 并行跑 BDD 验证，证据写入 P6-evidence/{pkg}/，同时写 P6-evidence/{pkg}/results.md（PASS/FAIL 行 + 证据引用，不进 gate）
2. 所有 verifier 返回后，派一个汇总 verifier 逐包读取 results.md，转抄整合进唯一的 P6-acceptance.md
3. 汇总 verifier 确认各包 BDD 编号合集 = P1 全部 BDD 编号，无重复/遗漏，**必须在 P6-acceptance.md 中记录交叉核对结果**

基础设施隔离同 P5（端口/数据库/截图目录独立）。

**环境准备职责边界（本阶段落地）**：P6 的环境访问沿用 P5 已由主 Agent 准备好的环境（环境状态未变时不重复起）；需要新环境时同样遵循 dispatch-protocol.md「verification_env 条件化」/「环境准备职责边界」的统一准备规则——由主 Agent 统一启动并通过 dispatch-context 注入访问方式，**不由 verifier subagent 自行启动**（多个并行 verifier 各自起环境会导致端口占用与资源竞争）。环境验证失败时的分类与止损见 dispatch-protocol.md「verification_env 失败处理协议」，本卡片不重复展开。

## 推进条件（全部满足才写 phase: P7）

- [ ] 所有 BDD PASS（FAIL=0）
- [ ] P6-evidence/ 目录非空 + 证据文件被引用
- [ ] UI 任务：vision-helper blocker_count=0；blocker>0 时须在 P6-acceptance.md 写明追查命令 + 输出 + 根因结论（仅写"已追查"不合规）
- [ ] provenance 审计通过
- [ ] **P6.5 judge 复核通过（强制，所有任务）**：judge 启用任务须 `P6.5-judge-verdict.md` 存在 + `check-gate.py P6.5` exit 0（check-judge-verdict + check-events 双脚本）；历史任务（无 `judge.enabled: true`）自动跳过（BDD-1/2）

## 常见错误（T046 实证）

1. **用 DOM 属性替代视觉验证**：img.src 被重写 = 图片显示正常。不对——还有 Content-Type、CORS、CSP 等 100 种原因导致图片不渲染。**vision-helper 说破了就是破了**
2. **凑 PASS 数量**：deferred BDD 标 PASS、用 1 行文本文件充证据 → provenance 审计能通过但功能不对
3. **只验证中间指标不验证用户结果**：naturalWidth>0, complete=true, API 返回 200 → 结论"功能正常"。用户看到的：破图。**问自己：用户看到了什么**
4. **收到视觉否定先反驳**：vision-helper 报异常 → 先 curl -I 查响应头 → 再决定是 vision 误报还是真问题。T046：三次视觉否定被三次程序化指标反驳，15 分钟浪费
5. **验收失败自己动手改代码**：这和上面几条本质是同一类问题（判定证据和判定对象由同一人在同一时间点生产），只是这次改的是真代码而非假 markdown，反而更难被察觉。正确动作是退回重新派发，见上方 FAIL > 0 的处理说明

gate 不过 ≠ 你失败了。红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P7 一致性检查依赖 P6 的 BDD 对照结果
- 验收结果是判定任务成败的最终依据——P8 发布只是机械步骤

## 自查≠gate
写完验证脚本后应自跑确认脚本可执行（自查），但自查通过 ≠ P6 gate 通过。
P6 gate 由主 Agent 亲自跑 gate 脚本（check-gate.py P6 + check-p6-evidence.py + check-p6-provenance.py），验证的是 verifier subagent 的产出。结果以主 Agent 跑的 gate 脚本为准。
不要在返回中声称"验收已通过"或"全部 BDD PASS"——只返回路径 + 摘要。
自查可（非阻断）复跑 `python3 agate/scripts/check-maintainability.py {TASK_DIR}` 确认 P4 后无新增反模式——P6 阶段暂存区通常已不含代码 diff，此为自查提醒而非 gate 判定点（检测器挂载在 P4，BDD-13）。

> 完成 → 读 phase-cards/P7-consistency.md
<!-- AGATE_CARD_END -->
