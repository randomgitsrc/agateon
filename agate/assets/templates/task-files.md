# 各阶段产出文件模板

> 每个任务目录 {AGATE_WORKSPACE}/tasks/{Txxx}/ 下的标准文件

## 通用 Header（所有文件必须有）
```yaml
---
phase: {P1-P8}
task_id: {Txxx}
type: {problems|design|review|test-cases|...}
parent: {上一阶段文件名，P1 时是外部需求来源}
trace_id: {Txxx}-{Pn}-{YYYYMMDD}
status: {draft|approved|rejected|done}
created: {YYYY-MM-DD}
agent: {main|analyst|architect|reviewer|test-designer|implementer|verifier|vision-analyst}
---

> **agent 字段由主 Agent 在派发 prompt Header 里填好**（角色 ID），subagent 复制即可，不要自行推断。缺字段 → `check-p6-provenance.py` 缺字段 WARNING（exit 2 不阻塞，向后兼容）。
```

## 各阶段文件清单

| 阶段 | 文件 | 关键 Header 字段 |
|------|------|-----------------|
| P0 | P0-brief.md | 主 Agent 亲自填写（非 subagent 产出）：task/known_risks/executor_env/env_constraints |
| P1 | P1-requirements.md | 含 BDD 验收条件 + `packages:` `domains:` 初判 + 裁剪说明；无未决 `[NEED_CONFIRM]`（门槛）|
| P2 | P2-design.md | **必须声明 `packages:` `domains:` `ui_affected:` `gate_commands:` `files_to_read:` `env_constraints:`；确认/细化 P0-brief 的 `env_constraints`** |
| P2 | P2-review.md | **status: approved/rejected**（门槛）|
| P3 | P3-test-cases.md | 声明 `test_code_dir: {实际路径}`；每用例对应一条 BDD；UI 任务含 E2E 用例 |
| P3 | {test_code_dir}/ | 测试代码目录（项目自定义，如 `backend/tests/`）|
| P4 | P4-implementation.md | 声明 `implementation_dir: {实际路径}` |
| P4 | {implementation_dir}/ | 代码目录（项目自定义，如 `src/` 或 `backend/app/`）|
| P4 | P4-evidence/{batch}.log | 批级证据日志（MVWU 阶段 1，可选、不阻断；逐行 `key: value`，`{batch}` 为 dispatch_plan 批 `id`；由主 Agent 在该批 commit 前机械转录 `tests_filter` 的运行结果；`check-mvwu.py` 事后观测；不进 gate / judge 白名单）|
| P5 | P5-test-results/unit.md | 标注 `failed: N`（仅供参考，gate 以主 Agent 跑 gate_commands.P5 为准）|
| P5 | P5-test-results/e2e.md | UI 任务必须：Playwright 实跑结果 + 截图路径。须含 `status: passed` 字段（hook 检查） |
| P6 | P6-acceptance.md | P1 每条 BDD 有实跑结果（**只允许 PASS 或 FAIL，不允许中间态**）；UI 条件含截图 |
| P7 | P7-consistency.md | 无 `[BLOCKER]` 标记（门槛）|
| P8 | P8-release.md | 每个 package 的版本 bump + CHANGELOG + 临时资源清单 |

### 辅助文件（非阶段产出，由主 Agent 或 subagent 过程产出）

| 文件 | 产出者 | 说明 |
|------|--------|------|
| P{N}-dispatch-context-{role}.md | 主 Agent | 派发前查证的客观信息（环境状态、URL、选择器等），每个 subagent 一个，信息量 >10 行或需复用时落盘 |
| P{N}-progress.md | subagent | 分阶段落盘的中间产物（每步追加写入），空返回时供主 Agent 判断 subagent 是否动过 |
| orchestrator-log.md | 主 Agent | 防无响应锚点（长操作前写 NEXT:），详见 state-machine.md「orchestrator-log.md 防无响应」节 |
| P{n}-checkpoint.md | 主 Agent | L2 会话 checkpoint（每阶段 gate 通过后落盘，本阶段异常/关键判断/subagent 表现），详见 state-machine.md「L2 会话 checkpoint」节 |
| task-session-summary.md | 主 Agent | L2 会话 checkpoint（任务完成时一次性落盘），详见 state-machine.md「L2 会话 checkpoint」节 |
| PAUSED-resolution.md | 主 Agent | PAUSED 恢复时人工决策内容 |
| HANDOVER.md | 主 Agent | 环境受限时交接给其他 Agent |

## 路径占位符

P3/P4 的代码路径由产出文件显式声明，不使用固定目录名：

- P3-test-cases.md 必须声明：`test_code_dir: backend/tests/`
- P4-implementation.md 必须声明：`implementation_dir: {项目实际源码路径}`

派发 prompt 引用这些声明而非固定路径，避免模板硬编码项目特定路径。

## 门槛字段说明

主 Agent 不依赖 subagent 产出文件字段判定门槛，而是**亲自跑命令验证**：

- P1 → 主 Agent 确认有 BDD 条件 + 无未决 `[NEED_CONFIRM]`
- P2-review.md `status` → subagent 评审产出的结论
- P3 → 主 Agent 跑 `scripts/check-tdd-red.py` 验证（UI 任务查 Playwright 用例存在）
- P5 → 主 Agent 跑 `gate_commands.P5` 验证（UI 任务实跑 Playwright/E2E）
- P6 → 主 Agent 确认 P1 每条 BDD 有实跑结果
- P7 → 主 Agent grep `[BLOCKER]` 验证
- P8 → 主 Agent 为每个 package 跑发布检查命令验证

## P0-brief.md 结构（主 Agent 任务简报，亲自填写）

P0-brief 是主 Agent 作为 PM 在派发任何 subagent 之前写的判断文件。
不是 subagent 的产出，是主 Agent 的职责——把产品需求翻译为工程视角、注入风险判断。

**核心原则：开发全程在测试环境进行。** 生产环境不在 agate 的编排范围内——
生产部署属于发布步骤（`make publish` 之后的运维范畴），不属于 P1-P8。

```yaml
## P0-brief.md
task: "一句话描述任务（工程视角，不是产品语言）。若写不出一句话 → 任务太大，考虑拆分（见 dispatch-protocol.md「派发编排机制」）"

known_risks:
  - "涉及数据 schema 变更（需要在测试环境充分验证迁移逻辑）"
  - "跨越 3 个改动端（API+CLI+客户端）"
  - "修改权限/认证逻辑（安全敏感）"

executor_env:
  platform: "opencode"          # opencode | claude-code | codex | claude-project
  has_task_tool: true           # 能否派发 subagent（false = 单 Agent 模式）
  has_local_runtime: true       # 有完整本地环境（npm/python/playwright/测试框架）
  network: "full"               # full | restricted（restricted 时 npm install 等可能失败）
  model_tier: "standard"        # 可选字段，非强制。协议不硬编码模型选择建议。
                                # standard = 用默认模型；premium = 方案设计/验收时用强模型；budget = 机械任务用便宜模型
                                # 实际可用性取决于项目环境，此处仅为项目自填的倾向说明

env_constraints:
  debug_env: "项目的测试/调试环境命令或路径（从项目约定读取，如 CLAUDE.md）"
  # 注意：不写 prod_env。生产环境不在开发流程范围内。
  # 若 subagent 接触了生产环境，须行首声明 [PROD_TOUCHED] {描述}（触发 PAUSED）或 [PROD_NOT_TOUCHED]（未触发，静默通过）。

phase_hint: [P1, P2, P3, P4, P5, P6, P8]  # 主 Agent 预判；P3 默认保留，跳过须有理由
# has_task_tool=false 时所有阶段由主 Agent 直接执行，subagent 派发步骤自动降级
```

**P0-brief 的核心价值**：每个 subagent 都在独立上下文里启动，不知道项目约定和环境约束。
P0-brief 是把这些约束注入每次派发的桥梁——所有 subagent 的 prompt 都要包含 P0-brief.md 路径。

### 扩展章节（项目自定）

5 字段是 agate 协议要求的最小集。项目可根据需要扩展。

**常见扩展类别（实战中验证有效，仅作参考不强制）**：
- `user_decisions`：PM 视角记录已与用户确认的关键决策
- `coordination`：与其他任务的依赖和时序约束
- `验收基线`：PM 视角的可量化验收条件
- 其他按需扩展

注意：
- 这些是**参考类别**而非模板。具体格式和内容由项目决定。
- agate 不维护具体模板——避免偏向单一项目实践。
- 项目可自由选择不用上述任何类别。

## P1-requirements.md 结构（需求基线）

**frontmatter（v2.0 机器字段，直接复制到文件头 `---` 块）**：
```yaml
---
phase: P1
task_id: TAG0001           # 替换为实际任务编号
type: problems
parent: P0-brief.md
trace_id: T001-P1-20260101 # {task_id}-P1-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: analyst
# ── v2.0 机器字段 ──
risk_level: high                  # enum: low/medium/high，必填
phases: [P1, P2, P3, P4, P5, P6, P7, P8]   # list of P\d+，必填
packages: [pkg-a]                 # list，必填
domains: [backend, cli]           # list，必填
# 可选字段：仅在适用时写（不适用即省略，不写 null——presence 语义）
# ceremony: standard            # thin/standard/full；缺省 standard（fail-closed）；thin 需四要素 checklist
# override: "P2 retained"         # 裁剪声明与执行不一致时
# implicit_coupling: false        # bool；P7 裁剪时声明
# coupling_checklist: [api-schema: checked]  # list；P7 裁剪时必填
# internal_only: true             # bool；P8 裁剪时
# internal_only_reason: "内部工具" # string；P8 裁剪时必填
# 跳过风险: "..."                 # string；裁剪时必填
# design_trivial: true            # bool；P2 候选方案可减为 1 时
# follows_existing_pattern: [agate/scripts/check-state-yaml.py]  # list
# ── v2.0 标记"已解决/已确认"状态（可选，仅标记存在时写，BDD-21/22）──
# need_confirm_resolved: []       # list[str]：已解决的 NEED_CONFIRM 项描述（逐条匹配正文）
# suggest_resolved: []            # list[str]：已采纳的 SUGGEST 项描述
# scope_resolved: []              # list[str]：已解决的 SCOPE+ 项描述
---
```
`risk_level`/`phases`/`packages`/`domains` 必填；其余为可选字段，仅在适用时写。
上述字段全部写在文件头 frontmatter 块内，**不再写在下方正文的"5. 裁剪说明"/"6. 范围声明"里**——
正文只保留裁剪理由的散文说明（如"跳过 P3 理由：..."一句话解释，机器判定字段已迁到 frontmatter）。
`need_confirm_resolved`/`suggest_resolved`/`scope_resolved` 是"已解决状态"的结构化声明，
正文的 `[NEED_CONFIRM]`/`[SUGGEST: ...]`/`[SCOPE+]` 散文标记本体仍保留（人类痕迹，不迁移，BDD-23）。

```markdown
## 1. 需求复述
（用结构化语言重写原始需求）

## 2. 隐含需求识别
- 隐含需求 A：... | 为什么必须：...
- 隐含需求 B：... | 为什么必须：...

## 3. BDD 验收条件

### {功能分组名}

#### BDD-1: {行为描述}
- Given ...
- When ...
- Then ...

#### BDD-2: {行为描述}
- Given ...
- When ...
- Then ...

## 4. 待确认清单
- [NEED_CONFIRM] 问题描述 + 几种可能的理解（真无方向 → 阻塞）
- [SUGGEST: 推荐方案 X，理由是 Y]（有倾向 → 主 Agent 自行采纳，WARNING 不阻塞）
（已解决/已采纳时不删除本条，而是在文件头 frontmatter 的 `need_confirm_resolved`/
`suggest_resolved` 列表中追加对应描述——标记本体保留为人类痕迹，机器判定读 frontmatter）

## 5. 裁剪说明
risk_level / phases / internal_only / internal_only_reason / coupling_checklist /
override / 跳过风险 / design_trivial / follows_existing_pattern
↑ 已迁移至文件头 frontmatter（见上方"frontmatter"示例块），此处只保留裁剪理由的散文说明：
- 跳过 P3 理由：...
- 跳过 P7 理由：...

## 6. 范围声明
packages / domains ↑ 已迁移至文件头 frontmatter（见上方示例块）

## 7. 能力需求声明
capability_requirements:
  - need: browser-vision
    why: P6 验收需截图验证 UI 交互
    available:
      - playwright-cdp skill（已注入）
    status: available          # available / supplementable / GAP

  - need: external-network
    why: 验证 CDN 加载
    available: []
    status: GAP
    [CAPABILITY_GAP: external-network] — 建议降级为 mock 验证

## SCOPE+ 增补区（后续阶段回写）
- [SCOPE+ from P2] 新需求 + 对应 BDD
（已纳入基线后不删除本条，而是在文件头 frontmatter 的 `scope_resolved` 列表中追加对应
描述——`check-scope-resolved.py` 闭环判定改读该结构化列表，BDD-22）
```

**能力三态说明**：
- `available`：环境中已有（Agent 自身 / 已注入 skill / 可调用外部 agent）→ 自走
- `supplementable`：当前没有但有已知补充路径 → 在 prompt 里指引，不阻塞
- `GAP`：无任何补充路径 → 标 `[CAPABILITY_GAP]`，主 Agent 暂停问人

判断 status 时**先看环境**（已注入的 skills、可调用的 agent），不只看主力模型自身能力。

## P2-design.md 结构（方案设计）

**frontmatter（v2.0 机器字段，直接复制到文件头 `---` 块）**：
```yaml
---
phase: P2
task_id: TAG0001           # 替换为实际任务编号
type: design
parent: P1-requirements.md
trace_id: T001-P2-20260101 # {task_id}-P2-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: architect
# ── v2.0 机器字段 ──
candidate_count: 2                # int ≥1，必填
packages: [pkg-a]                 # list，必填
domains: [backend, cli]           # list，必填
ui_affected: false                # bool，必填
# ui_design_section: true          # bool，可选（presence 语义：ui_affected: true 时声明已含 UI 设计节）
# ── v2.0 派发编排字段（可选，TAG0014）──
# dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [{id: pkg-a, complexity: medium}, {id: pkg-b, complexity: low}]}
# 可选字段：多子任务编排方案（单行 flow YAML），契约以 P2 卡「dispatch_plan 机器字段」/ architect.md「批次设计」为准
# 批内可选键 tests_filter / output：tests_filter 为该批的验证命令（可选，缺省不影响 gate；示例用 `python -m pytest ...` 或遵循 AGATE_PYTHON 探测，不写裸 python3）；output 为该批产出说明（可选）；写法与约束以 P2 卡「dispatch_plan 机器字段」为准
---
```
`gate_commands:` / `files_to_read:` / `env_constraints:` / `minimal_validation:` **留正文**（不迁移 frontmatter）。

```markdown
## 1. 候选方案（v0.6：至少 2 个 + 权衡 + 选择理由）
# design_trivial: true 或 follows_existing_pattern: [参照文件] 时可只写 1 个候选方案（P2 仍不可省略）
# brainstorm 借鉴：强制 architect 至少走一遍"还有别的做法吗"的思考

### 候选方案 A：[简短标题]
（影响域、设计、数据流、异常路径、优点、风险、工作量）
### 候选方案 B：[简短标题]
（同上）
### 选择理由
（为什么选 A 不选 B——必须具体到方案的隐含假设差异，不能是"A 更简单"这种空话）

## 3. gate 命令（在 P2 固化，后续不得修改）
gate_commands:
  P3: "pytest"                     # 可选：测试运行器（verbose 输出，供 check-tdd-red.py 自动读取）
  P3_e2e: "playwright test --reporter=line tests/e2e/"   # ui_affected 且新增测试在 E2E 层时必填（T090 问题2）
  P3_formatter: "pytest.sh"  # 可选：formatter 脚本（见 assets/formatters/README.md 速查表）
  P5: "pytest -q --tb=no"          # 紧凑输出模式（见下）
  P5_formatter: "pytest.sh"        # 可选：formatter 脚本，将测试输出标准化为 JSON
  P5_timeout_seconds: 120          # 可选：该 key 命令的预期耗时上限（秒），见下方字段说明
  P5_e2e: "playwright test --reporter=line tests/e2e/"   # ui_affected: true 时必填
  P5_e2e_timeout_seconds: 300      # 可选：per-key 声明，E2E 与单元测试各取各的档
  P6: "pytest -q --tb=no tests/acceptance/"
  P6_timeout_seconds: 120          # 可选
  project_module: "myapp"  # 可选：项目模块前缀，B 类检测用
# ── {key}_timeout_seconds（可选，per-key 声明）──
# 用途：给对应 key 的 gate 命令声明"预期耗时上限（秒）"，供跑命令的一方据此设 shell 层超时
#       （运行时取值 = 预期耗时 ×1.5，见 dispatch-protocol.md「命令超时兜底与既有超时机制的分层关系」）。
# 命名：与 {key}_formatter / {key}_e2e 同为 per-key 惯例，逐条 key 各自声明，不设整体共享默认
#       （单元测试与 E2E 耗时差 2.5 倍以上，共享一个值起不到分类阈值作用）。
# 建议档位（**手动按命令类型声明，不是自动推断**——没有代码去猜命令属于哪一类）：
#       单元测试类 120s / E2E 类 300s / 构建类（编译·安装依赖·打包）600s。
# 缺省行为：**不声明即等同现状**——无强制阻断、无 gate 拦截，跑命令的一方按经验估算预期耗时
#       （向后兼容，沿用 dispatch_plan"缺字段 → gate 跳过校验"先例，老任务无需回填）。
# ⚠️ 排除 P3：P3 key **不适用**本字段——P3 的超时继续走既有 AGATE_TDD_TIMEOUT 环境变量机制
#       （默认 120s，由 agate_common.py 的 run_test_with_formatter() 消费、check-tdd-red.py 读取）。
#       两层不合并的完整关系说明见 P2 卡片「gate_commands 声明」的 {key}_timeout_seconds 字段规则，
#       此处不重复展开。
# P3 键（可选）：声明后 check-tdd-red.py 自动读取，无需主 Agent 手动设 TEST_RUNNER。
# P3 用 verbose 输出（区分 A/B 类错误），P5 用紧凑输出（只判过没过），两者分离。
# 非 pytest 项目建议声明此键（如 P3: "npx vitest run"）。
# P3 的超时不写 P3_timeout_seconds（见上方"排除 P3"），改用 AGATE_TDD_TIMEOUT 环境变量。
# 紧凑输出要求：P5/P6 gate 命令只供主 Agent 判断「过没过」，须用工具的汇总/安静模式
# （pytest --tb=no / cargo --quiet / dotnet --verbosity quiet / vitest --reporter=dot
#  / go test | tail -30 / mvn -q），保留通过失败汇总+失败清单，去掉逐项 traceback。
# 工具无紧凑模式时用 shell 兜底：命令 2>&1 | tail -N（语言无关）。

## 4. 实现导航（必填，控制 P4 implementer 上下文体量）
# v0.6 澄清：这是"实现导航"不是"实现计划"——
# 不列每步做什么（那是步骤脚本，superpowers writing-plans 的模型）
# 列实现时需要参考的文件 + 为什么（资源地图，agate P2-P4 模型）
files_to_read:
  - path: backend/services/auth.py
    why: 复用现有 hash_password 模式
  - path: backend/models.py:120-180      # 大文件标行号范围，只读相关片段
    why: User 模型定义，新字段加在这里
# 只列实现确实需要参考的文件，不是相关文件大杂烩。
# P4 implementer 按此清单读取，不在项目里乱窜——这是上下文不爆炸的关键。

## 5. 最小验证
minimal_validation:
  assumption: "srcdoc iframe 继承父页面 CSP"
  method: "10 行 HTML 测试页验证 srcdoc 的 CSP 行为"
  result: "confirmed | refuted | not_needed"
  note: "（验证过程和结论简述）"
# 方案依赖浏览器行为/安全模型/外部系统行为 → 必须做最小验证
# 纯代码逻辑 → 须声明"纯代码逻辑，无外部系统依赖"（写明依赖了哪些内部函数/数据转换）
# T019 教训：srcdoc 方案到 P6 才发现不可行，P2 用 10 行 HTML 5 分钟就能发现。

## 6. env_constraints（确认/细化 P0-brief）
env_constraints:
  debug_env: "..."
  isolation_check: "..."

## 7. UI 设计节（ui_affected: true 时必含；由 architect 兼任产出；不新增 designer 角色）
# 样式：## UI 设计 + ### 渲染形态声明 + 按形态 checklist（布局/交互/视觉 或 渲染正确性/动效时序）
# 形态声明必须与 P1 frontmatter 的 ui_render_shape/ui_ux_dimensions 一致（P2 gate 规范化值比对）。
## UI 设计
### 渲染形态声明
- 渲染形态: layout（布局型）        # 或 render_component（渲染组件型）/ temporal_effects（时序特效型）
- 适用维度: 布局结构, 交互行为, 视觉呈现   # 渲染组件型可写 渲染正确性, 动效时序
### 布局 checklist
- [ ] 页面/组件层级结构与关键区域占位已描述
### 交互 checklist
- [ ] 键盘可达 / 输入态反馈 / 反馈态已覆盖；输入态用例宣称需人工复核
### 视觉 checklist
- [ ] 颜色对比度 / 字体层级 / 组件一致性已说明
### 渲染正确性 checklist（渲染组件型适用）
- [ ] 判定锚点：渲染结果对比参考图 + diff 阈值（量化）
### 动效时序 checklist（时序特效型适用）
- [ ] 帧/时序采样点与动画关键帧已定义

## SCOPE+ 增补区（后续阶段回写）
- [SCOPE+ from P4] ...
```

## P6-acceptance.md 结构（验收报告）

**frontmatter（v2.0 机器字段，直接复制到文件头 `---` 块）**：
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
逐条结果仍留正文，但**行格式从严**（BDD-17/18）：行首必须 `- PASS BDD-NN: ...` 或
`- FAIL BDD-NN: ...`（PASS/FAIL 后紧跟一个空格再接 BDD 编号），消除"总结行误判"（F11）。

```markdown
## 验收结果（逐条对照 P1 的 BDD）

**BDD 二值规则**：每条 BDD 结果只允许 PASS 或 FAIL，不允许"⚠️ 调整/跳过/覆盖"等中间态。
**截图质量标准**：操作类 BDD 截图必须互不相同（md5 去重），查询类 BDD 可不截图（断言值是唯一证据）。

#### BDD-1: entry 不指定过期时间默认 15 天
- PASS BDD-1: 创建 entry 不填过期 → 实测 15 天后过期（p6-bdd-1.png）
- PASS BDD-1: MCP publish_files 不传 expires → 实测同样生效

#### BDD-2: ...
- FAIL BDD-2: 实测结果与预期不符：... → 触发回 P4

## 验收小结（总结行，不计入逐条 PASS/FAIL 统计）
**Summary**: 28/28 PASS, 0 FAIL，UI 截图 N 张
```

**证据引用格式**：每条 PASS 结果必须在括号内引用对应证据文件路径（相对于 `P6-evidence/` 目录）。示例：`- PASS BDD-1: ... (p6-bdd-1.png)`。hook 会检查引用路径必须真实存在。无引用的 PASS 行不算有证据。

**UI 任务证据追加约定**（`ui_affected: true` 时）：
- `P6-evidence/screenshots/` 目录必须非空，每个截图文件大小 > 1KB（防空 png 充数，hook 检查）
- 视觉证据按 **P1 vision 能力三态分档** + **渲染形态**选形式：
  - **available / supplementable**（无声明默认 available）→ 每条 UI 类 PASS 必须含
    vision-analyst YAML 引用：`- PASS BDD-1: ... (screenshots/bdd-1.png) (vision: vision-reports/bdd-1.yaml)`；
    vision YAML 文件必须存在且 `summary.blocker_count == 0`（hook 检查）
  - **GAP**（无视觉能力降级）→ 截图/帧序列 + **人工复核记录**引用：
    `- PASS BDD-1: ... (screenshots/bdd-1.png) (manual-review: review-bdd-1.md)`；
    复核记录文件必须存在，不要求 vision YAML
  - **渲染组件/时序特效形态**（P1 `ui_render_shape: render_component` / `temporal_effects`）：
    视觉证据可选用 帧序列 `(frames/bdd16-01.png, frames/bdd16-02.png)` / 渲染输出对比
    `(renders/bdd1-a-actual.png, renders/bdd1-a-diff.json)`（diff.json 含量化度量）/
    时序截图 `(screenshots/bdd7-t1.png, screenshots/bdd7-t2.png)`
  - **输入态/交互形态变化类 PASS**：附人工复核记录（复核人/时间/结论）：
    `- PASS BDD-3: ... (screenshots/x.png) 人工复核: 张三 2026-08-17 确认输入态正常`
- vision YAML 格式见 `assets/execution-roles/vision-analyst.md` 的完整 YAML 结构
- **雷同截图复核记录样例**：
  `- 雷同截图复核: bdd1/bdd2 截图视觉相近，已人工复核确为不同操作但视觉相近（张三 2026-08-17）`

**查询类 BDD 证据约定**：
- 查询类 BDD（断言值是唯一证据）可不截图，但**须有断言记录文件**作为客观证据
- 断言记录形式：API 响应 JSON（`response.json`）、测试输出日志（`assert.log`）、数据库查询结果（`query-result.txt`）等
- 引用格式：`- PASS BDD-1: 返回 3 条记录 (response.json)`——括号内路径相对 P6-evidence/，文件必须存在
- **所有 PASS 都必须有文件引用**（hook 强制）——无文件引用的纯断言 PASS 不被接受。文件形式不限（截图/日志/JSON/文本），不绑定技术栈

## P7-consistency.md 结构（一致性检查）

**frontmatter（v2.0 机器字段，直接复制到文件头 `---` 块）**：
```yaml
---
phase: P7
task_id: TAG0001           # 替换为实际任务编号
type: consistency
parent: P2-design.md
trace_id: T001-P7-20260101 # {task_id}-P7-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0                  # int ≥0（BDD-19）
deviation_count: 0                # int ≥0（BDD-19）
deviation_critical_count: 0       # int ≥0（DEVIATION-CRITICAL）
design_gap_count: 0               # int ≥0（BDD-20）
design_gap_reviewed_count: 0      # int ≥0（BDD-20）
code_map_new_files_count: 0        # int ≥0（可选，仅骨架/CODE-MAP 机制已采用时填）
code_map_reviewed_count: 0         # int ≥0（可选，语义对应 design_gap_reviewed_count）
---
```
正文 `[BLOCKER]` / `[DEVIATION-CRITICAL]` / `[DESIGN_GAP]` / `[DESIGN_GAP_REVIEWED]` 散文标记
**保留为人类痕迹**（不迁移，BDD-23），但 gate 判定改读上述 frontmatter 结构化计数（F13 消除）。

```markdown
## 一致性审查结论

### DESIGN_GAP 配对
[DESIGN_GAP_REVIEWED: 转抄 P4-implementation.md 的 DESIGN_GAP 声明 + 裁决结论]

### 跨文件一致性
- P2§packages 与 P8 release bump 范围一致
- P1 的 BDD 数与 P6 的验收结果数量匹配

## 结论
无 [BLOCKER] / [DEVIATION-CRITICAL]，全部 DESIGN_GAP 已 REVIEWED
```

## READY 收尾检查（P8 gate 通过后、标记 READY 前）

详见 state-machine.md「READY 收尾检查」节（权威来源）。主 Agent 逐项检查 4 类（状态与版本 / 测试环境已清理 / 开发环境已还原 / 生产环境无残留），任一项未通过 → 不进入 READY；生产环境相关项未通过 → 立即 PAUSED 报告人工。

P8-release.md 应包含「临时资源清单」节，列出本任务启动的临时服务/进程、临时数据、开发安装，供主 Agent 清理时参照。