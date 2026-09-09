---
phase: P5
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: verifier
---

<dispatch_guide>
> 以下派发指引是本次验证的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标

执行 TAG0033 的 P5 技术验证，产出 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/`
目录（`unit.md` + `fail-list.txt` + `real-machine.md`）。两部分：

- **A. gate_commands.P5**（P2-design.md §7 固化的命令，逐条执行 + 记录）
- **B. 真机验证清单 V1 / V3 / V4 / V5**（P1-requirements.md §7——本机 ChatGPT 账号可做的项；V6/V7 归 P6，
  V8 归"待有该环境时补"）

**你是 external-output gate 的执行方**——主 Agent 验的是你产出的 `P5-test-results/`，不是自己重跑。
所以产出必须**逐命令附实跑输出摘要**（passed/failed 计数 + 失败清单），不接受无输出的"✓ 通过"。

### A. gate_commands.P5（逐条执行）

从 `P2-design.md §7` 读，逐条跑、逐条记 `P5-test-results/unit.md`：

1. **`P5`**: `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no`
   - **预期**：`1383 passed / 6 failed / 2 skipped`（±，以实跑为准）。
   - **6 failed 必须全部是** `test_codex_platform_docs.py::test_bdd_22` ~ `test_bdd_27`——这 6 条是
     **本任务 `protocol-docs` 批（P7）待实现**的 doc-assertion 审计测试（P3 写红、P7 补
     `platform-notes.md` Codex 章 + `SETUP.md` Codex 小节后转绿；P2 §11 dispatch_plan `static-batch`
     两批的设计，P1 §9「P7 不可裁」）。在 `unit.md` 里**逐条列出这 6 个测试 id**，标注
     「本任务 protocol-docs 批（P7）待实现，doc-assertion 审计，预期 P7 转绿——非预存失败、非回归、非真 bug」。
     **不写进 `known-failures.md`**（那只登预存失败；这是任务引入的、by-design 的待实现项）。
   - **若 failed > 6，或 6 条里有任何一条不是 `test_codex_platform_docs.py::test_bdd_22~27`** →
     这是 P4 引入的回归 → 停止，写清哪条、traceback 摘要，返回主 Agent（回 P4 判定）。
   - `fail-list.txt`：把实跑的 `FAILED ` 行逐行写入（这 6 条 doc-audit 会在里面——正常，主 Agent 已知）。
2. **`P5_consistency`**: `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
   （⚠️ **worktree 自己的脚本路径**，不是 `~/.agate`——检查对象含 worktree 里的 P3/P4 产出）
   - **预期**：exit 0 / **0 ERROR**（既有 ~329 WARNING 是历史叙事文件死链，与本任务无关——记数即可，不处理）。
   - exit ≠ 0 或 ERROR > 0 → 停止，记 ERROR 全文，返回主 Agent。
3. **`P5_shellcheck`**: `timeout 60s shellcheck -S warning agate/scripts/pre-commit-gate.sh
   agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh`
   - 本任务不改 `.sh`——预期 0 issue（结构性回归）。有 issue → 记录，判断是否本任务相关（大概率不相关，
     记入 `unit.md` 预存说明）。
4. **ruff**（P2 §7 未列但 AGENTS.md 合并强制，顺手跑）：`timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/`
   → All checks passed。

⚠️ **跑完全量 pytest 后**：检查 `git status --short agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/gate-events.jsonl`
——若某测试向该账本追加了行（已知测试隔离问题，非本任务引入），`git checkout -- <该文件>` 还原它，
在 `unit.md` 记一句，**不计失败、不计 BLOCKER**。

### B. 真机验证清单（P1 §7 的 V1 / V3 / V4 / V5——记 `P5-test-results/real-machine.md`）

本机：codex-cli **0.153.4** + ChatGPT 登录。每项写「命令 / 实际观察 / 通过判据二值结论」。
命令一律加 `timeout`。

- **V1（rollout JSONL 格式复核为回归）**：读 3-5 个真实 `~/.codex/sessions/2026/09/*/rollout-*.jsonl`
  的头尾。核对 `CommandExecution` item 确有 `command`(数组) / `exit_code` / `status` /
  `payload.started_at_ms` / `payload.completed_at_ms` / `aggregated_output`，形态与 P1 §4.1 / P2 §4.2
  一致。**再**：写一段 ≤15 行 python `import` 既有适配器模块（`importlib` 从 `agate-cmdstream-adapters.py`
  取 `CodexAdapter` / `ADAPTERS["codex"]`），对**一个真实 rollout 文件**跑
  `CodexAdapter().read_commands(<真实文件>)` + `.probe(<真实文件>)` + `.list_sessions("~/.codex/sessions")`
  —— **通过判据**：`probe` 对真实 Codex rollout 返 True、对某个真实 Claude Code 转录 jsonl（若本机有）
  返 False；`read_commands` 不抛异常、产出 ≥1 条 `CommandRecord` 且字段非空（`platform=="codex"` /
  `ts_start` 是 int / `command` 非空）；`list_sessions` 返回非空绝对路径 list。
- **V3（spawn_agent 子会话独立文件复核为回归）**：`find ~/.codex/sessions -name 'rollout-*.jsonl' -newermt '-7 days'`
  找已有子会话文件（`grep -l '"thread_source"[: ]*"subagent"'`）。若本机已无、可现场派一个：
  `timeout 180s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "用 spawn_agent 派一个子代理跑 echo v3check"`
  然后 `find ~/.codex/sessions -name 'rollout-*.jsonl' -newermt '-3 min'`。**通过判据**：子会话是独立
  `rollout-*.jsonl`；其 `session_meta` 含 `thread_source=="subagent"` + `parent_thread_id`；
  `CodexAdapter().list_sessions()` 枚举到它；`CodexAdapter().read_commands(<子文件>)` 产出记录的
  `session_id` = 子文件 basename（含子自身 uuid，**不是**父 id）。
- **V4（Codex 输出截断标记确切形态——本任务 P2 §5 设计点 4 的收敛锚）**：构造超长输出经 codex exec：
  `timeout 240s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "跑 python3 -c \"print('x'*2000000)\" 并把完整输出贴回来"`
  （或 `yes | head -c 5000000`）。然后读落盘 rollout 的对应 `CommandExecution` item，找**截断字段 / 文本标记**
  的确切形态。
  - **对照** `CodexAdapter._detect_truncated` 现有的 `_CODEX_TRUNC_BOOL_KEYS` / `_CODEX_TRUNC_TEXT_MARKERS`
    （P2 §5 设计点 4 定的保守双信号候选值）：
    - **命中**（真实截断形态被现有常量覆盖）→ `real-machine.md` 记「V4 PASS：实测截断形态 = X，
      现有 `_CODEX_TRUNC_*` 已覆盖，无需收敛」。**顺手**：把这个真实形态补进
      `agate/tests/fixtures/cmdstream/codex-session.jsonl` 的截断样例行（使 BDD-7/17 fixture 从"P2 推测形态"
      收敛为"实测形态"）——**这是 fixture 数据收敛，不是代码逻辑改动**，允许；改完重跑
      `test_bdd_7_codex_truncated_output_hash_none` / `test_bdd_17_codex_truncated_repeat_not_spin` 确认仍绿。
    - **未命中**（真实形态 = 现有常量没有的新字段/标记）→ **不要自己改 `agate-cmdstream-adapters.py`**
      （P5 不改代码逻辑）。在 `real-machine.md` 记「V4 = 需 P4 微调：实测截断形态 = Y，现有
      `_CODEX_TRUNC_*` 未覆盖，需在常量里加 Y」，返回主 Agent 判定（大概率回 P4 一次定向微调常量 + 重跑）。
    - **无法复现截断**（codex 对该输出未截断 / 环境限制）→ 记「V4 = 未复现，现有双信号保持保守值，
      收敛推迟到有截断样例时」，**不阻塞**（P1 §4.1.2 已标 `[未实测/待定]`，P2 §5 设计点 4 用保守兜底）。
- **V5（`multi_agent` feature flag 复核为回归）**：`timeout 60s codex features list | grep -iE 'multi_agent|spawn|collab'`
  —— **通过判据**：`multi_agent` = stable / true（与 P1 §4.4 / platform-notes.md 版本注记将写的一致）。

### 不做 / 边界

- **V2**（spawn_agent schema 穷尽）：P1 §4.3 已确认「令模型逐字 dump schema」不可用；跨真实调用归纳键
  全集的深度工作**归 P6**（配合 V7 嵌套深度）——P5 只需在 `real-machine.md` 记「V2 延后 P6，方法 = 跨
  ≥数次真实 spawn_agent 调用归纳 `function_call.arguments` 键并集」。
- **V6 / V7**：归 P6（真实卡死场景三态 / 嵌套深度）——P5 不做。
- **V8**（API-key 账号 model 阵容）：本机是 ChatGPT 账号、环境不可得。`real-machine.md` 记
  「V8 = 待有 API-key 账号环境时补（非阻塞）；verification_env_budget 止损轮次 2，当前轮次 0（未尝试，
  环境本质不可得）；platform-notes.md P7 将在 API-key 账号列显式写"本会话未核实、待补"」。
- **P5 不改代码逻辑**：`agate/scripts/*.py` 一律不动（V4 若需改常量 → 回 P4）。**唯一允许的写**是 V4 命中
  时把实测截断形态**补进 fixture 的截断样例行**（数据收敛，不是逻辑），且改完必须重跑相关 BDD 确认仍绿。
- **不碰生产环境**：codex exec 用 `--dangerously-bypass-approvals-and-sandbox` 只在本 worktree /tmp 跑
  无害命令（echo / print），不写任何生产路径。触发写 `[PROD_TOUCHED]`，未触发写 `[PROD_NOT_TOUCHED]`。

### 上游关联

- **P2-design.md §7**（gate_commands 权威）+ §5 设计点 4（截断双信号收敛锚）+ §11 dispatch_plan（两批）
- **P1-requirements.md §7**（真机验证清单 V1-V8）+ §4（spike 实测事实，V1/V3/V5 是复核）+ §9（P7 不可裁）
- **P4-implementation.md**（CodexAdapter 落点：`_CODEX_TRUNC_BOOL_KEYS` / `_CODEX_TRUNC_TEXT_MARKERS`
  常量在 `agate-cmdstream-adapters.py` class 上方，带 `# P5 V4 收敛锚` 注释）
- **P4-review.md + agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md**（P4 已 approved /
  SELF-GATE PASS；NHR-1/NHR-2 = P7 文档排期项，与 P5 无关，供背景）
- **P3-test-cases.md**（BDD → 验证层归位表——BDD-18/20 归 P5；BDD-22~27 归 P7）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§7 gate_commands + §5 设计点 4 + §11）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§7 真机清单 + §4 spike + §9）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md`（BDD 验证层归位表）
4. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（CodexAdapter 落点 + 截断常量）
5. `agate/scripts/agate-cmdstream-adapters.py`（`CodexAdapter` 全文——V1 手跑解析用；`_CODEX_TRUNC_*` 常量——V4 对照）
6. `agate/tests/unit/test_codex_platform_docs.py`（头部注释已声明 BDD-22~27 red-until-P7——确认 6 failed 就是这些）
7. `agate/tests/fixtures/cmdstream/codex-session.jsonl`（V4 命中时的收敛目标——截断样例行）
8. `agate/assets/execution-roles/verifier.md`（你的角色定义）
9. `agate/phase-cards/P5-verification.md`（本阶段卡片——判定规则 / 预存失败处理 / 产出规格 / N5 签名校验）
10. `AGENTS.md`（worktree 根——双工作区纪律、工具纪律、验证命令清单）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P4（P5 产出 commit 随
  P5-test-results/ 推进 P5）/ judge.enabled=true。P4 已 commit（`835c9b9`）。系统 `python3` 跑 pytest；
  ruff 用 `~/.venvs/agate-dev/bin/ruff`。codex-cli 0.153.4 + ChatGPT 登录。
- **P4 已知基线**（你逐条实跑复核，不是照抄）：全量 `agate/tests/unit/` = 1383 passed / 6 failed
  （全 `test_codex_platform_docs.py::test_bdd_22~27`）/ 2 skipped；consistency 0 ERROR；ruff clean。
- **gate_commands.P5**（P2 §7）：`P5` = `python3 -m pytest agate/tests/unit/ -q --tb=no`；
  `P5_consistency` = `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`；
  `P5_shellcheck` = `shellcheck -S warning agate/scripts/{pre-commit-gate,commit-msg-self-gate,pre-push-gate}.sh`。
  未声明 `P5_formatter` → `fail-list.txt` 用 `grep '^FAILED ' 实跑输出` 提取。
- **6 条 doc-audit failed 是设计内的**：P2 dispatch_plan `static-batch` 两批（`adapter-core` P4 完成 /
  `protocol-docs` P7）；`test_codex_platform_docs.py` 文件头注释已声明「BDD-22~27 red until P7」。
  主 Agent 判定：这 6 条**不阻断 P5 推进**（by-design 待实现，P7 转绿，P8 重跑 P5 gate 兜底）。
- **P5 gate 规则**（`check-gate.py P5`）：exit 2；主 Agent 验 `P5-test-results/` 存在 + failed 计数 +
  N5 签名校验（`grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' P5-test-results/unit.md` > 0）。
- **`p5_pass_commit`**：主 Agent 在你返回、判定 P5 通过后，会 `git rev-parse HEAD` 写入 `.state.yaml`——你不写。

### 产出文件

- `P5-test-results/unit.md`：gate_commands.P5 逐条实跑结果（命令 + passed/failed 计数 + 6 条 doc-audit
  逐条列出并标注「P7 待实现」+ consistency ERROR 计数 + shellcheck + ruff）。**必须含**至少一行
  `passed`/`failed` 字样（N5 签名校验）。
- `P5-test-results/fail-list.txt`：实跑的 `FAILED ` 行逐行（6 条 doc-audit 会在内——正常）。
- `P5-test-results/real-machine.md`：V1 / V3 / V4 / V5 逐项（命令 / 观察 / 二值结论）+ V2/V6/V7 延后说明 +
  V8 待补说明（含 verification_env_budget 轮次 0）。
- （V4 命中时）改 `agate/tests/fixtures/cmdstream/codex-session.jsonl` 截断样例行为实测形态 + 重跑确认。

frontmatter（若 `unit.md` / `real-machine.md` 需要）：按 `agate-md-field-set.py --list` 提示写；
`P5-test-results/` 下文件通常不强制 frontmatter，以 gate 实际要求为准。

### 返回

返回：`P5-test-results/` 路径 + gate_commands.P5 三条命令各自 passed/failed 计数 + 确认 6 failed 全是
`test_codex_platform_docs.py::BDD-22~27`（是/否；否则列出异常项）+ V1/V3/V4/V5 各自二值结论 +
V4 是否需回 P4（命中/未命中/未复现）+ 是否有 `[PROD_TOUCHED]` + 是否有真回归。
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
