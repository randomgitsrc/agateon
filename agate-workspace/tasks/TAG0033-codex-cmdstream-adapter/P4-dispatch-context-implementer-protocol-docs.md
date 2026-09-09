---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: implementer
batch: protocol-docs (2/2)
---

<dispatch_guide>
> 以下派发指引是本次实现的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标

这是 P2 dispatch_plan `static-batch` 的**第 2 批 `protocol-docs`**（第 1 批 `adapter-core` 已在
`835c9b9` 落地）。产出 = 补齐 Codex 平台文档，让 `test_codex_platform_docs.py::test_bdd_22` ~
`test_bdd_27`（6 条 doc-assertion 审计，当前红）转绿。追加到 `P4-implementation.md`（同文件，新增
「## protocol-docs 批（2/2）」节）。

> 说明：P2-design.md §11 曾标 `protocol-docs` 批「P7 执行」，但补文档内容属实现工作、非 P7 一致性
> 验证工作（比照 TAG0030 先例：doc-assertion 审计测试在 P3 写红、doc 内容在 P4 补绿）。主 Agent 决定
> 把它拉回 P4 第 2 批执行，避免 P5/P6 带着 6 条 by-design 红推进。P7 仍做完整 consistency + SELF-GATE
> 对齐（针对代码 + 文档的完整改动面）。

### 必须完成

#### 1. `agate/platform-notes.md` 的 `## Codex / Hermes / OpenClaw 等` 节（现 line ~43-45「待补充」）

改成完整的 `## Codex` 章（可保留 Hermes/OpenClaw 作单独一行「待补充」或并入）。逐条满足 BDD-22~26：

- **BDD-22**：不再含「待补充」字样；逐项可 grep 命中：非交互 `codex exec`、`-m`/`--model`、
  `-c model_reasoning_effort=<low|medium|high>` 推理档、`--dangerously-bypass-approvals-and-sandbox`、
  中间档 `-s <read-only|workspace-write|danger-full-access>` + `--approve-for-me`（并注明 `--full-auto`/`-a`
  已从 `codex exec` 移除）、`spawn_agent` 原生子派发、`--json` 结构化输出、`resume`、
  「退出码不可靠须解析 `--json`」意味的表述。
- **BDD-23**：含字符串 `0.153.4`；注明验证账号类型 = ChatGPT 登录、验证日期 2026-09；含「新兴平台
  需持续复核 / 目标版本上 `codex features list` 复核」意味的表述（比照 DSH 章的「新兴平台需持续复核」惯例）。
- **BDD-24**：`spawn_agent` 参数 schema 段落**明确标 `[自述]`**（或等价措辞）；**不得**把「未见
  `background`/`timeout`/`permission` 字段」写成「确认无这些字段」；指明「穷尽 schema 直接实测」是
  真机验证清单（V2）待执行项（P6 归纳键并集）。
- **BDD-25**：与既有 line ~53-70 的 Codex 列（Hardening-roadmap 跨平台适配表）+ line ~67-70「Codex
  兼容性」注记（`Codex subagent max_depth=1`）**交叉引用并标注时效**——例如：「`multi_agent` flag 已
  `stable`/`true`（实测 0.153.4）、`spawn_agent` 单层已实测可用（P5 V3）、嵌套深度未测（V7 归 P6）——
  既有 `max_depth=1` 注记写于 subagent workflows 默认启用前，待 V7 复核」。**全文档不得出现**「一处说
  Codex 无法再派发、另一处说已支持多层」这类**未标时效**的对立陈述。既有注记那几行**不删**，可在其
  附近加一句「↑ 时效见下方 `## Codex` 章」式指针。
- **BDD-26**：model 小节注明——ChatGPT 账号下 `codex exec -m` 默认 `gpt-5.6-terra`（`-m gpt-5` /
  `-m gpt-5-codex` 被 API 400 拒）；`spawn_agent` 的 `model` 枚举 = `gpt-5.6-terra` / `gpt-5.6-luna` /
  `gpt-5.5` / `gpt-5.4-mini`（标 `[自述]`）；**API-key 账号 model 阵容登记为「待有该环境时补」（非阻塞）**。
- 另：把 **P5 V4 实测的截断标记形态**记进本章一句（「输出截断实测形态：`formatted_output` 里
  `Warning: truncated output (original token count: N)` / `… tokens truncated …`；CodexAdapter 截断检测
  据此」——供未来复核 / RM-AG0055 §3.4.2 差异点 4 的 Codex 侧记录）。

#### 2. `agate/SETUP.md` 新增 Codex 小节（比照既有 DSH 小节 line ~144-175 的结构）

满足 **BDD-27**：独立 Codex 小节，覆盖——安装（`npm i -g @openai/codex` 或官方方式）、`codex login`
（说明 ChatGPT vs API key 影响可用 model）、自动化环境绕过 flag（`--dangerously-bypass-approvals-and-sandbox`、
`--skip-git-repo-check`）。

#### 3. `agate-workspace/agents/CODE-MAP.md`（P4-review 非阻塞观察 + 协议对齐 NHR-2 之一）

line ~33 的命令流适配器条目：`三平台命令流适配器：Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd`
→ 更新为**四平台** + 补 `Codex rollout JSONL`（`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`）。措辞
与该文件既有风格一致，最小改动。

#### 4. `docs/research/cross-platform-dispatch-mechanics.md`（协议对齐 NHR-2 之二）

L169 附近「⚠ 缺 CodexAdapter」/ L286 附近「唯一缺口 = Codex 适配器」——CodexAdapter 已于 TAG0033
落地。加一行回写（如「[TAG0033 已补 `CodexAdapter`，2026-09]」）**或**若你判断该文为时效性研究叙事、
明确接受不逐处回写，则在文首或该处加一句总说明「适配器落地进度见 agate 主线，本文为调查期快照」。
二选一，写清理由。**不做**大规模重写。

### 绝对不能做

1. **不改** `agate/scripts/*.py`（adapter-core 批已冻结；本批纯文档）/ `agate/tests/`（`test_codex_platform_docs.py`
   是 P3 产出，本批**不改测试**，只补文档让它自然转绿——若某条 BDD 断言的锚词与你写的文档措辞对不上，
   **以 BDD 断言为准调整文档措辞**，不改测试）。
2. **不改** P1/P2/P3 基线文件 / `.state.yaml`。
3. **不动** 既有 `platform-notes.md` line 53-70 的 Codex 兼容性表与注记的**事实内容**（只加时效指针 +
   交叉引用，见 BDD-25）。
4. 范围外改动标行首 `[SCOPE+]`；不擅自做。

### 完成判据（自查，非 gate）

- `timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q` → **全绿**
  （BDD-22~27 由红转绿；BDD-29/30 守护本就绿）
- `timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=no` → **1389 passed / 0 failed / 2 skipped**
  （原 6 条 doc-audit 红全部转绿，无新增失败）
- `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **exit 0 / 0 ERROR**
  （⚠️ worktree 自己的脚本——检查对象是你改的 platform-notes.md / SETUP.md；新增 Codex 章不得引入死链 /
  行号引用漂移 / 平台名污染 ERROR；既有 ~329 WARNING 不新增本质条目）
- `timeout 60s ~/.venvs/agate-dev/bin/ruff check agate/` → All checks passed（本批不改 .py，应无变化）

### 上游关联 / 事实来源

- **`docs/research/cross-platform-dispatch-mechanics.md`**（Codex 机制事实权威——§0 速查矩阵 / §1.2
  `codex exec` flag 全集 / §2.1-2.4 model 指定与可用性（ChatGPT 账号 gpt-5.6-terra / gpt-5 被 400 拒）/
  §3 推理档 `model_reasoning_effort` / §4.2 权限绕过（`--full-auto`/`-a` 已移除）/ §5.1 `spawn_agent`
  `multi_agent` flag stable/true + 命名变更史 / §5.2 `spawn_agent(task_name,message,model?,reasoning_effort?,fork_turns?)`
  schema `[自述]` + model 枚举 4 个）
- **P1-requirements.md §4**（spike 实测：§4.1 事件形态 / §4.1.1 exit_code 有数字 / §4.2 子会话 / §4.4
  `codex features list` / §4.5 实时流对比）+ **§7 V8**（API-key 账号待补的措辞）
- **P5-test-results/real-machine.md**（V1/V3/V4/V5 实测结论——尤其 V4 截断标记实测形态、V5 feature flag、
  V3 子会话字段）
- **`agate/platform-notes.md`**（现状：line ~43「待补充」/ line ~53-70 既有 Codex 列 + 兼容性注记 /
  line ~74 验证记录节 / DSH 章 line ~176 作新兴平台文档范式）
- **`agate/SETUP.md`**（DSH 小节 line ~144-175 作结构范式）
- **`agate/tests/unit/test_codex_platform_docs.py`**（BDD-22~27 的**确切锚词**——你的文档措辞必须能被
  这些断言 grep 命中；先读它再写文档）
- **P0-brief.md**（scope ② ③ 的原始要求 + 核心约束 3「证据强度诚实」+ 核心约束 4「版本注记」）

### 输入文件（按顺序读）

1. `agate/tests/unit/test_codex_platform_docs.py`（**先读**——BDD-22~27 的锚词断言，文档措辞对齐这个）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（§6.6/6.7 BDD-22~27 原文 + §4 spike + §7 V8）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/real-machine.md`（V1/V3/V4/V5 实测）
4. `docs/research/cross-platform-dispatch-mechanics.md`（Codex 机制事实——§0/§1.2/§2/§3/§4.2/§5）
5. `agate/platform-notes.md`（全文——现 Codex「待补充」+ 既有 Codex 列/注记 + DSH 章范式 + 验证记录节）
6. `agate/SETUP.md`（DSH 小节结构范式）
7. `agate-workspace/agents/CODE-MAP.md`（line ~33 适配器条目）
8. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（§0 既定前提 + §6 SELF-GATE 预告 + §11）
9. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P0-brief.md`（scope ②③ + 核心约束 3/4）
10. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`（adapter-core 批产出——你追加节）
11. `agate/assets/execution-roles/implementer.md`（角色定义）
12. `agate/phase-cards/P4-implementation.md`（P4 gate 规则）
13. `AGENTS.md`（worktree 根——双工作区纪律、consistency 用 worktree 脚本、SELF-GATE 触发）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P4（本批 commit 后仍 phase=P4，
  是 static-batch 第 2 批 / P4 延续，不推进）。P4 batch1（`835c9b9`）已 commit。P5 verifier 已跑（V1-V5 PASS，
  V4 已收敛 fixture 1 行），**P5-test-results 尚未 commit**——本批完成后主 Agent 会重跑 gate_commands.P5
  再一起 commit P5。
- **当前全量单测**：1383 passed / 6 failed（`test_codex_platform_docs.py::test_bdd_22~27`）/ 2 skipped。
  本批目标：6 failed → 0。
- **SELF-GATE**：本批改 `agate/platform-notes.md` + `agate/SETUP.md`（`agate/*.md`）→ 再次触发 SELF-GATE。
  主 Agent 会在本批返回后派 **protocol-alignment-review 第 2 轮**（针对文档改动面）。你**不派**评审。
- **既有事实（勿写反）**：Codex **有** per-command 数字 `exit_code`（P1 §4.1.1 更正——`CommandExecution`
  item 带 `exit_code`；「无数字 exit code」只对 turn 级失败成立）；`multi_agent` = stable/true（0.153.4）；
  `--full-auto`/`-a` 已从 `codex exec` **移除**；ChatGPT 账号 `-m gpt-5` 被 **400 拒**。
- **P4 gate 规则**：exit 0 = 暂存区含非 md/yaml 文件——⚠️ 本批**纯 .md 改动**，check-gate.py P4 可能
  exit 1（「仅 md/yaml」）。这是 static-batch 第 2 批的已知形态——主 Agent 会在 commit 时连同 P5 产出
  一起处理，或对本批 commit 用 P4 延续语义。你只管产出文档 + 自查判据全绿，gate 判定归主 Agent。

### 产出

- 改 `agate/platform-notes.md` + `agate/SETUP.md` + `agate-workspace/agents/CODE-MAP.md` +
  `docs/research/cross-platform-dispatch-mechanics.md`（第 4 项按二选一）。
- 在 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md` 追加
  「## protocol-docs 批（2/2）」节：改了哪些文件 + 每条 BDD-22~27 转绿确认 + 自查判据结果。
- 每步落盘 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-progress.md`（追加，不覆盖 batch1 内容）。
- 所有 bash 命令加 `timeout <秒>s` 前缀。

### 返回

返回：改动文件清单（行数增量）+ BDD-22~27 逐条转绿确认（pytest failed 数）+ 全量单测结果
（应 1389 passed / 0 failed）+ consistency exit 码 + 0 ERROR 确认 + 第 4 项（research doc）用了回写还是
总说明 + 是否有 `[SCOPE+]`。
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
