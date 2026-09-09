---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: protocol-alignment-review
review_round: 2
---

<dispatch_guide>
> 以下派发指引是本次审查的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 角色文件。

### 本次是 protocol-alignment-review 第 2 轮（protocol-docs 批 / 文档面）

第 1 轮（`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md`）审的是 `adapter-core`
批（代码），结论 SELF-GATE 对齐轴 PASS + 2 项 NEEDS_HUMAN_REVIEW（NHR-1 platform-notes.md/SETUP.md /
NHR-2 research doc）——都是「文档同步待做」。**本轮**审 `protocol-docs` 批的文档改动，核心是**确认
NHR-1 / NHR-2 已闭合**，并对新增文档做 A1-A7 语义对齐 + 事实准确性核查。

本轮改动（`git diff HEAD` 覆盖，`adapter-core` 批已 commit 在 `835c9b9`，本轮是其后的未提交改动）：

| 文件 | 改动 |
|---|---|
| `agate/platform-notes.md` | `## Codex ...`「待补充」→ 完整 `## Codex` 章（能力矩阵 / model 阵容 / spawn_agent schema `[自述]` / 命令流适配 / 验证记录表）+ Hermes/OpenClaw 拆出单节 + 既有「Codex 兼容性」注记附近加 1 行时效指针（+67/-3） |
| `agate/SETUP.md` | 新增 `### 步骤 2-Codex` 小节（+43/-0） |
| `agate-workspace/agents/CODE-MAP.md` | line 33「三平台命令流适配器」→「四平台…/ Codex rollout JSONL」（+1/-1） |
| `docs/research/cross-platform-dispatch-mechanics.md` | L169 / L286「缺 CodexAdapter」逐处回写「已补 (TAG0033, 2026-09)」（+2/-2） |
| `agate/tests/fixtures/cmdstream/codex-session.jsonl` | 1 行——**P5 verifier 的 V4 fixture 收敛**，不是本批产出（截断样例形态实测化） |

### A1-A7 逐项（每项 ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW + 证据）

- **A1 文档→脚本对齐**：新 `## Codex` 章的**每一处技术陈述**是否与实现 / 实测事实一致——逐条核：
  - 「rollout JSONL 落 `~/.codex/sessions/YYYY/MM/DD/`」「per-command 有数字 `exit_code`」「截断标记 =
    `formatted_output` 的 `Warning: truncated output ... tokens truncated`」「`multi_agent` = stable/true」
    「ChatGPT 账号 `-m gpt-5` 被 400 拒」「`spawn_agent` 子会话是独立 rollout 文件」——对照
    `agate/scripts/agate-cmdstream-adapters.py` 的 `CodexAdapter`（`_CODEX_TRUNC_TEXT_MARKERS` 是否真含
    `"tokens truncated"`；`probe`/`read_commands` 逻辑）+ `docs/research/cross-platform-dispatch-mechanics.md`
    的 `[实测]` 标注项 + `P5-test-results/real-machine.md` 的 V1/V3/V4/V5 结论 + `P1-requirements.md §4`。
    任何文档陈述与代码/实测不符 → MISALIGNED（列出具体行 + 正确表述）。
  - 「退出码不可靠须解析 `--json`」与「per-command item 带数字 exit_code」——文档是否把两者的**适用边界
    分清了**（turn 级失败 vs per-command shell 执行）？P1 §4.1.1 更正过这点。
- **A2 脚本→文档对齐（NHR-1 闭合核查）**：`CodexAdapter` 落地所需的协议文档同步是否**已完成**——
  `platform-notes.md` Codex 章（BDD-22~26）+ `SETUP.md` Codex 小节（BDD-27）现均已写。跑
  `timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q` 确认 8 passed / 0 failed
  （BDD-22~27 转绿）。结论应为 **ALIGNED（NHR-1 CLOSED）**。
- **A3 一致性连锁 + 反向传播（NHR-2 闭合核查）**：
  - A3a：`platform-notes.md` 新 Codex 章与既有 line ~53-70 Codex 列 + 「Codex 兼容性」注记
    （`max_depth=1`）是否**无未标时效的对立陈述**（BDD-25）——读全文档，确认新章的时效指针 + 既有注记
    附近的指针行成立，不存在「一处说无法再派发、另一处说已支持多层」的裸对立。
  - A3b（NHR-2）：`docs/research/cross-platform-dispatch-mechanics.md` L169 / L286 是否已回写；**再**主动
    推断还有没有别的「应被 CodexAdapter 落地影响但未改」的文件——候选：`agate/scripts/README.md` /
    `agate/tests/README.md`（cmdstream 适配器清单是否列平台数 / 需加 Codex？grep 确认）/ `agate/WORKFLOW.md`
    （Codex 环境适用性行——本就 ✅，确认无需动）/ `agate/LIMITATIONS.md`（Codex 相关旧表述——尤其
    「无数字 exit code」类，是否有需更新的）。逐一验证，列清单。
- **A4 测试覆盖**：doc-assertion 审计测试（`test_codex_platform_docs.py` BDD-22~27）是否**真的**校验了
  文档写对（不是空断言）？抽 2-3 条读断言体。**必须附** `timeout 300s python3 -m pytest agate/tests/unit/ -q`
  的 passed/failed 计数（你自己跑；预期 1389 passed / 0 failed / 2 skipped）。
- **A5 下游影响 + 文档传播**：新增 Codex 章 / SETUP 小节是否影响已有项目的 gate 行为（不应——纯文档）？
  `CHANGELOG.md` + 版本 bump 由 P8 处理（提示 P8 需覆盖「新增 Codex 平台文档 + CodexAdapter」）。
  `WORKFLOW.md`「Pre-commit 检查总览」是否需动（不应——未新增 CHECK）？
- **A6 锚点表覆盖**：本任务不新增 CHECK / 协议规则（DEBT0025）——`platform-notes.md` / `SETUP.md` 在
  CHECK 14/15 整文件豁免名单（P1 §3 S7 已核）；新增 Codex 章不触发 CHECK 9 / CHECK 12 锚点表变更。确认。
- **A7 设计原则一致性**：对照 `agate/adr.md` 相关 ADR（平台适配 / 新兴平台文档惯例）。新 Codex 章是否
  符合既有「平台适配权威源」职责边界（`platform-notes.md` line 3 声明）+ DSH 章确立的「新兴平台需
  持续复核 + 注明验证版本」范式？只 ALIGNED / NEEDS_HUMAN_REVIEW。

### 事实准确性核查（本轮额外——顶 C8 review 对文档的一遍）

新 `## Codex` 章的**关键事实断言**逐条对照权威来源，标 ✔ / ✘（✘ 列出正确表述）：

| 文档断言 | 权威来源 |
|---|---|
| `codex exec` 别名 / flag 全集（`-m` / `-c model_reasoning_effort` / `-s` / `--approve-for-me` / `--json` / `resume` / `--skip-git-repo-check`）| research §1.2 / §3 / §4.2 |
| `--full-auto` / `-a` 已从 `codex exec` 移除 | research §4.2「已弃」 |
| ChatGPT 账号 `-m gpt-5` / `-m gpt-5-codex` 被 400 拒 + 默认 `gpt-5.6-terra` | research §2.2 `[实测]` |
| `spawn_agent` model 枚举 4 个（`gpt-5.6-terra`/`gpt-5.6-luna`/`gpt-5.5`/`gpt-5.4-mini`）| research §5.2 `[自述]` |
| `multi_agent` = stable/true；`collaboration_modes`/`multi_agent_mode` = removed | research §5.1 + P5 V5 `[实测]` |
| rollout JSONL 目录结构 + `CommandExecution` item 字段 | P1 §4.1 + P5 V1 |
| 截断标记形态 `formatted_output` 的 `Warning: truncated output ... tokens truncated` | P5 V4 `[实测]` |
| spawn_agent schema 标 `[自述]` + 「未见 X ≠ 确认无」+ V2 待实测 | P1 §4.3 + P0-brief 核心约束 3 |

### 输入文件（按顺序读）

1. `git diff HEAD`（本轮全部改动——先看 stat + platform-notes.md / SETUP.md 全 diff）
2. `agate/platform-notes.md`（新 `## Codex` 章全文 + 既有 line ~53-75 Codex 列/注记 + 职责边界声明 line 3 + DSH 章范式）
3. `agate/SETUP.md`（新 `### 步骤 2-Codex` 小节 + DSH 小节对照）
4. `agate-workspace/agents/CODE-MAP.md`（line 33 改动）
5. `docs/research/cross-platform-dispatch-mechanics.md`（§0/§1.2/§2/§3/§4.2/§5 + L169/L286 回写 + §10 复核纪律）
6. `agate/scripts/agate-cmdstream-adapters.py`（`CodexAdapter` + `_CODEX_TRUNC_*` 常量——A1 对照）
7. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/real-machine.md`（V1/V3/V4/V5 实测——A1 对照）
8. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§4 spike + §6.6/6.7 BDD-22~27 + §7 V8）
9. `agate/tests/unit/test_codex_platform_docs.py`（A4——doc-audit 断言体）
10. `agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md`（第 1 轮结论 + NHR-1/NHR-2 原文）
11. `agate/assets/review-roles/protocol-alignment-review.md`（角色定义 + A1-A7 + 反向传播路径表 + 报告结构）
12. `agate/adr.md`（A7）
13. `agate/scripts/README.md` + `agate/tests/README.md` + `agate/LIMITATIONS.md`（A3b 反向传播候选）
14. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P0-brief.md`（核心约束 3「证据强度诚实」+ 4「版本注记」）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，phase=P4（protocol-docs 是 static-batch 第 2 批，
  commit 后仍 phase=P4）。`adapter-core` 批 commit = `835c9b9`。本轮改动未 commit。
- **implementer 自查**（你复核）：`test_codex_platform_docs.py` 8 passed / 0 failed；全量单测
  1389 passed / 0 failed / 2 skipped；`check-protocol-consistency.py --strict-errors-only`（worktree 脚本）
  exit 0 / 0 ERROR；ruff clean。
- **第 1 轮 NHR**：NHR-1 = platform-notes.md/SETUP.md Codex 章待补（本轮应闭合）；NHR-2 =
  research doc L169/L286 过时（本轮应闭合，逐处回写方式）。
- **既有事实**（勿判反）：Codex per-command **有**数字 exit_code；「无数字 exit code」只对 turn 级
  失败成立；`--full-auto`/`-a` 已移除；`multi_agent` stable/true。
- **`self-gate-review` token**：本轮 P4b commit（连同 P5 产出一起 commit，见下）的 message 会含
  `self-gate-review:` 指向你的产出 `agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033-r2.md`。

### 产出

`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033-r2.md`（用 Write，文件名含 `TAG0033`
+ `r2`——DEBT0011 防覆盖）。结构：A1-A7 逐项表（结论 + 证据）+ 事实准确性核查表（逐条 ✔/✘）+
NHR-1 / NHR-2 闭合判定（CLOSED / 未闭合）+ A3b 反向传播清单逐一验证 + A4 pytest 实跑输出 +
总结论（全 ALIGNED → SELF-GATE PASS / 有 MISALIGNED → 阻塞列修订项 / 有新 NEEDS_HUMAN_REVIEW → 逐条列）。
首部注明 `task_id: TAG0033` / `date: 2026-09-09` / `round: 2 (protocol-docs batch)` /
`reviewer: protocol-alignment-review (agent≠main)`。

所有 bash 命令加 `timeout <秒>s` 前缀。

### 返回

产出文件路径 + A1-A7 各项结论（一词）+ 事实核查有无 ✘（有则列）+ NHR-1/NHR-2 是否 CLOSED +
总结论（PASS / 阻塞 / 需人工确认 N 项）+ A4 pytest passed/failed 计数。
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
