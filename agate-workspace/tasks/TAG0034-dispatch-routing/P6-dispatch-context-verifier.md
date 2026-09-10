---
phase: P6
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: verifier
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

P6 验收（模式二）：**逐条对照 `P1-requirements.md` 的全部 53 条 `#### BDD-NN`**，每条给 `- PASS BDD-NN: 描述 (证据路径)` 或 `- FAIL BDD-NN: ...`（**只允许 PASS / FAIL，无中间态**），产出 `P6-acceptance.md`（frontmatter `pass:` / `fail:` / `ui_affected: false`）+ `P6-evidence/`（非空、每个文件含实质内容）。**只验不改**——不改任何代码 / 测试 / 配置 / 协议文档。P6 是 self-authored gate，验收报告记录的是**验收时的事实**。

### 本任务 BDD → 证据形式（`ui_affected: false`，无截图 / 无 vision）

53 条 BDD 分三类，证据形式对应：

| BDD 类别 | BDD 编号 | 证据形式 |
|---|---|---|
| **功能类（pytest 验收）** | 1~38（除 39/40）/ 42~45 / 51 / 52 / 53（部分）/ T1/T2/T3 | 跑对应 `agate/tests/unit/test_tag0034_*.py` 用例 → PASS 行引 `(P6-evidence/pytest-tag0034.log)` + 该 BDD 对应的测试函数名（可在描述里写 `test_bdd_NN_xxx`） |
| **文档断言类（grep 关键措辞）** | 41 / 46 / 47 / 48 / 49 / 52 / 53 + BDD-10 的 platform-notes 部分 / BDD-45 的声明部分 | grep 目标文件的关键措辞 → 输出存进 `P6-evidence/doc-assertions.log`，PASS 行引它 + 命中的文件:行 |
| **回归护栏类** | 39 / 40 | `test_tag0034_zero_change.py` 实跑 + `git diff --stat <P4 前 commit>..HEAD` 证明 `phases.yaml` / `check-gate.py` / `check-state-transition.py` / 状态机结构化部分零改动 → `P6-evidence/regression-zero-change.log`；BDD-40「不配置 = 逐字节现状 + `dispatch_route` 事件条数 = 0」可引 `P5-test-results/` 的全量绿 + `grep -c dispatch_route agate-workspace/tasks/TAG0034-dispatch-routing/gate-events.jsonl` = 0 |

**BDD-42（routed-away judge 平台无关性）**：证据 = `grep -nE '\.codex/sessions|\.claude/projects' agate/scripts/check-judge-verdict.py agate/scripts/check-p6-provenance.py`（应 0 命中）+ `git log --oneline -- agate/scripts/check-judge-verdict.py agate/scripts/check-p6-provenance.py` 确认本任务范围（`f75e129..HEAD`）无这两文件的 commit + `test_bdd_42` PASS → 存 `P6-evidence/bdd-42-platform-independence.log`。

**执行主体命令**（每条前设 `timeout`）：
- `timeout 400 python3 -m pytest agate/tests/ -k tag0034 -q` → 全量 tag0034（预期 90 passed / 0 failed）→ 落 `P6-evidence/pytest-tag0034.log`（**末行 `EXIT_CODE: <n>`**）
- 按需 `pytest -k "bdd_NN"` 单跑某条做定向证据
- doc-assertion：`grep -nE '<关键串>' <目标文件>` 逐条 → 汇总 `P6-evidence/doc-assertions.log`
- `git diff --stat f75e129..HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py agate/state-machine.md`（应无输出 = 零改动）→ `P6-evidence/regression-zero-change.log`

### BDD 逐条对照要点（对照 `P1-requirements.md` §4 各条的 Then 判据）

- **§4.1 schema（BDD-1~6）**：`test_tag0034_schema.py`（`check-dispatch-routing.py` 两轴 / `tier`vs`candidates` 互斥 / `(phase,role)` key / 非法 cli·effort / `fallback` 非法）
- **§4.2/4.3/4.4 档位展开·解析顺序·standard 钉死（BDD-7~14）**：`test_tag0034_resolve.py` + `test_tag0034_native.py`（BDD-8/9/10 effort 映射；**BDD-10 两分支**：探测到 `--effort` → 含 flag / 未探测到 → 不含、不报错 + `platform-notes.md` 注明串）
- **§4.5 三层配置 + 全兜底（BDD-15~18）**：`test_tag0034_resolve.py`（优先级序 / 缺失→出厂默认 / 损坏→兜底 / 同名键 last-write-wins）
- **§4.6 try-and-fall（BDD-19~23）**：`test_tag0034_tryfall.py` + `test_tag0034_p4b.py`（无 probe / 三类基础设施理由码逐级回落 / 全落空默认派发）
- **§4.7 完整性不变量（BDD-24~27）+ §4.8（BDD-28）**：`test_tag0034_tryfall.py` + `test_tag0034_events.py` + `test_tag0034_p4b.py`（产出质量非回落信号 / 收到即停 / gate FAIL 同候选 retry `dispatch_route` 计数不增 / `gate_fail` 理由码被 `check-events.py` 拒 / 回落不写 `state_transition`·不动 `retries`）——**known_risks 最高危，逐条给证据**
- **§4.9 dispatch_route 事件（BDD-29/30）**：`test_tag0034_events.py`（哈希链复用 / `check-events.py` 认新事件 + 既有 `test_check_events.py` 零改动仍绿）
- **§4.10 cli:native（BDD-31/32）**：`test_tag0034_native.py`（Claude Code modelUsage 与解析目标一致·非父继承 / OpenCode 命名 subagent 跑配置 model）
- **§4.11 子进程 spawn + 结构化解析（BDD-33~36）**：`test_tag0034_subprocess.py` + `test_tag0034_p4b.py`（三平台 fixture 样本 / Codex turn 层为准 + item status:failed 不换候选 / OpenCode 空返回·ProviderAuthError·UnknownError 各归类）
- **§4.12 tmux（BDD-37/38）**：`test_tag0034_tmux.py` + `test_tag0034_p4c.py`（`which tmux` 决定包裹/裸跑 + 两路径逐字节一致 / 倒计时 + 有 client 不强杀 + `N+余量` 兜底强杀）——**标注「P4c 可整体切除、feature flag 默认关；BDD-37/38 断言的纯逻辑 helper 转绿」**
- **§4.13 回归证明（BDD-39/40）**：见上「回归护栏类」
- **§4.14 routed-away judge（BDD-42）**：见上「BDD-42」
- **§4.15 交互（BDD-43/44/45）**：`test_tag0034_interaction.py`（五模式并行各自解析 / 自主再派发不走表·无事件 / 单 Agent no-op + 显式声明出范围）
- **§4.16/4.17/4.18 doc 修订 + DEBT0039 + P5→P4 回退（BDD-41/46~51/52/53）**：`test_tag0034_docs.py`（grep design-note / roadmap / dispatch-protocol.md 新节 / architect.md DEBT0039① / dispatch-protocol.md DEBT0039② / consistency 0 ERROR）+ `test_tag0034_interaction.py`（BDD-51 P5→P4 回退重解析、无升档）
- **T1/T2/T3**（P2-review 折入）：`test_tag0034_resolve.py`（T1 返回契约）/ `test_tag0034_tryfall.py`+`test_tag0034_p4b.py`（T2 挂死→infra_error）/ `test_tag0034_events.py`（T3 三值参数化）——按 P1 §3 §4.17 的登记，这三条若 P1 有独立 BDD 编号则逐条，若并入某 BDD 则在该 BDD 证据里覆盖。**核对 P1-requirements.md 的实际 BDD 计数**（53 条 `#### BDD-NN:`）——P6 的 PASS+FAIL 总数必须 **≥ 53**。

### 约束

- **BDD 二值**：每条只 PASS 或 FAIL，无「调整/跳过/覆盖」。FAIL>0 → gate exit 1 → 主 Agent 判回 P4（**你不改代码让它变绿**）。
- **证据实质**：`P6-evidence/` 每个文件含实际输出（pytest 汇总 + 失败清单 / grep 命中行 / git diff 结果），**不接受 1 行充数**（T046 教训）。可核验日志末行 `EXIT_CODE: <n>`。
- **PASS 行格式**：`- PASS BDD-NN: {描述} ({证据路径})`——证据路径用精确格式（`(P6-evidence/xxx.log)` / 多文件逗号分隔）。总结行**不用**行首 `- PASS`/`- FAIL`（用 `**Summary**: N/N PASS, 0 FAIL`）。
- **只验不改 / PROD**：dogfooding，"生产" = 主 checkout `/home/kity/oclab/agateon` + `~/.agate`，**禁改**。仅 worktree 内读 + 写 `P6-acceptance.md` + `P6-evidence/`。检查对象类脚本用 worktree 的 `agate/scripts/`。意外触碰主 checkout/`~/.agate` → `[PROD_TOUCHED]` PAUSED；否则 `[PROD_NOT_TOUCHED]`。
- **post-test 环境残留检查**（强制）：本任务测试是纯脚本 + mock，不建外部资源。验收后确认无残留（`git status` 只有 P6 产出 + `.state.yaml`/`gate-events.jsonl`，无意外文件）→ 记进 `P6-acceptance.md`。
- **P5 证据复用**：`.state.yaml` 有 `p5_pass_commit: 92edcfc`。P5→P6 间**只有 P6 dispatch-context + P5 commit 的产出改动**（无代码改动）——BDD-40 的「全量回归全绿」部分可引 `../P5-test-results/unit.md`（`check-p6-provenance.py` 审计 7 会判 `reuse_allowed`）。功能类 BDD 仍须你独立跑 `pytest -k tag0034` 给证据。
- **自查 ≠ gate**：你自跑确认脚本可执行，但不在返回里声称「验收已通过」——只返回路径 + 摘要。
- **命令超时兜底**：所有 bash 前 `timeout <n>s`。挂死/超时 → 停、progress 写一行、返回主 Agent。
- **格式预检**：产出后自跑 `python3 agate/scripts/check-p6-format.py --fix agate-workspace/tasks/TAG0034-dispatch-routing/P6-acceptance.md`（归一化 PASS/FAIL 大小写 + 行首空白），再返回。

> 子派发能力：不启用（P6 是验收，单 verifier）。

### 上游关联

- P5 已 commit（`2772891`）：verifier 独立跑 4 条 gate_command 全 exit 0（全量 1625 passed / 0 failed / 2 skipped）。`.state.yaml` phase=P6 / `p5_pass_commit: 92edcfc`。
- P4 三批 commit（`d1c2aca` / `99a4c19` / `92edcfc`）：`pytest -k tag0034` = 90 passed / 0 failed。C8 review approved + protocol-alignment-review aligned（round 5）。
- P1-requirements.md：53 条 BDD（`#### BDD-NN:` 连续 1~53）+ BDD-10 `[BASELINE_CHANGE]`（effort 能力探测）+ §4.17 DEBT0039 BDD-48/49/50 + §4.18 BDD-51/52/53 + §1 两条 `[SCOPE+]`（DEBT0039 并入 / A5.3·A7.4 doc-sync）。**A5.3·A7.4 的 LIMITATIONS.md 局限 2 缓解链 + ADR-013 落 P8**——P6 **不验**这两条（P8 交付项，P1 §9 已登记）；tmux 观测层目标环境复跑同样是 P8 项。
- judge：`.state.yaml` `judge.enabled: true` → P6 commit 后主 Agent 强制派 P6.5 judge 复核（你的 P6-acceptance.md + P6-evidence/ 是 judge 的白名单输入之一）。
- P0-brief known_risks 最高危 = **模型购物完整性洞**（BDD-24~28）——这几条的验收证据要扎实（gate FAIL 不换候选 / 理由码枚举无 `gate_fail` / 回落非 retry）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（**53 条 BDD —— 逐条对照的权威**）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P5-test-results/`（unit.md + fail-list.txt + 4 条 log —— P5 全绿证据，BDD-40 可引用）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（§3 各节 Then 判据的设计基准 + §10 实现完成的标志 13 条）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md` + `P4-implementation-P4b.md` + `P4-implementation-P4c.md`（改了什么 —— 帮你定位每条 BDD 的验收对象）
- `agate/assets/execution-roles/verifier.md`（你的角色定义「模式二：P6 验收」+「验证纪律」+「gate 格式契约」）
- 测试文件（BDD 验收对象）：`agate/tests/unit/test_tag0034_*.py` + `agate/tests/regression/test_tag0034_zero_change.py`
- 文档断言目标：`docs/design-notes/design-dispatch-routing.md`（§2.1/§2.2 + 头部）/ `agate-workspace/roadmap/roadmap.md`（RM-AG0060 行）/ `agate/dispatch-protocol.md`（「### 0. 派发路由」子节）/ `agate/assets/execution-roles/architect.md`（批次设计节 DEBT0039①）/ `agate/platform-notes.md`（effort 行 + 结构化输出字段小节）
- `agate/scripts/check-judge-verdict.py` + `agate/scripts/check-p6-provenance.py`（BDD-42 —— grep 确认无平台 transcript 路径）
- `AGENTS.md`（gate 脚本分层、双工作区纪律、`--strict-errors-only` 定义）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P6-acceptance.md agate-md-field-set --list` 查看应填字段（`pass` / `fail` / `ui_affected` / `agent` / `trace_id` 等）；逐个 `agate-md-field-set <key> <value>` 写入（`ui_affected: false`，`fail: 0` 期望）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
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

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P6 / status=active / judge.enabled=true / p5_pass_commit=92edcfc
- HEAD = `2772891`（P5）；P4c `92edcfc` / P4b `99a4c19` / P4a `d1c2aca` / P3 `c218026` / P2 `b851b1e` / P1 `f75e129`
- 主 Agent 已核（**你须独立复跑给证据**）：`pytest agate/tests/ -k tag0034 -q` = 90 passed / 0 failed；`check-protocol-consistency.py --strict-errors-only` exit 0；`check-events.py <task dir>` exit 0（15 行）；`check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` exit 0；`git diff f75e129..HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py` 无输出
- `grep -c dispatch_route agate-workspace/tasks/TAG0034-dispatch-routing/gate-events.jsonl` = 0（本任务运行未真触发路由回落，BDD-40 事件计数 = 0）
- P1 BDD 计数：`grep -c '^#### BDD-' P1-requirements.md` = 53 —— P6 PASS+FAIL 总数须 ≥ 53
- `ui_affected: false` —— 无 vision-analyst、无截图；证据 = pytest 日志 + grep 命中 + git diff
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
- gate：主 Agent 跑 `check-p6-format.py --fix` + `check-gate.py P6` + `check-p6-evidence.py` + `check-p6-provenance.py`，之后强制 P6.5 judge
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败（本 dispatch-context 的 BDD 类别表 / 要点是「验收对象导航」，非结论预判）。
