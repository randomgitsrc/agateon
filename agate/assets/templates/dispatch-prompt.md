# 派发 Prompt 模板

> 主 Agent 调用 task 工具派发 subagent 时，prompt 用这个结构
> 本文件是派发 prompt 的权威来源；dispatch-protocol.md 仅保留极简结构提示 + 指针

```
你是 {阶段 Pn} 阶段的 {角色名} 子 Agent。

## 你的角色定义
读取并严格遵循：
{agate_root}/assets/{execution-roles|review-roles}/{role}.md

## dispatch-context（核心输入）
读取并严格遵循：{AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-dispatch-context-{role}.md
> dispatch-context 中的派发指引是本次任务的强制指令，不是参考信息。

## 项目约定（必读）
- {project_conventions_file}（项目约定、命名规范、目录结构）
- {AGATE_WORKSPACE}/tasks/{Txxx}/P0-brief.md（本任务的环境约束和风险声明）

## 环境隔离（强制，所有阶段适用）
本任务的环境约束见 P0-brief.md 的 env_constraints 字段。
- 调试/验证必须使用 P0-brief 的 debug_env 声明的测试环境，严禁直接操作生产环境
- 开发全程不应接触生产环境；若意外接触，立即停止并标注 [PROD_TOUCHED] 报告主 Agent
- 状态标记用二值格式：触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`。不要写"无 [PROD_TOUCHED]"

## 执行顺序
1. 读取 dispatch-context 派发指引（目标/约束/上游关联/输入文件）
2. 读取角色定义文件和项目约定
3. 按输入文件列表逐一读取，每读完一个追加 progress
4. 按 dispatch-context 约束执行任务（跑任何 bash 命令前先设超时，见下方「命令超时兜底」）
5. 写产出文件到约定路径
6. 自检产出文件（Header/内容/证据）
7. 返回路径 + 一句话摘要

## 分阶段落盘（重要，默认启用）
每读完一个输入文件或完成一个关键步骤，立即把发现追加写入 {AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-progress.md（bash 追加模式）。这样即使你最终无法产出完整报告，progress 文件也能让主 Agent 知道你做了什么。不要等所有文件读完再一次性写——逐条写。
落盘粒度还包括**每条 bash 命令执行前**追加一行（要跑什么、预期多久），命令挂死时主 Agent 从 progress 就能看出卡在哪条命令。

## 命令超时兜底（层级 4，所有 bash 命令强制）
执行任意 bash 命令前必须设 shell 层 timeout，不允许无超时裸跑：`timeout 180s <你的命令>`（秒数按下面算；或用工具自带的 timeout 参数）。
取值 = 该命令预期耗时 ×1.5：
- P2 的 `gate_commands` 里该命令对应的 `_timeout_seconds` 声明（如 `P5_e2e_timeout_seconds: 300`）已给出 → "预期耗时"直接取该值
- 未声明（含绝大多数非 gate 的日常 bash 调用）→ 按经验估算预期耗时，再 ×1.5
超时或出现非预期失败后的动作固定：① 停止执行，不自行更换命令、不深入诊断；② 往 progress 写一行（卡在哪条命令、跑了多久、什么输出）；③ 返回主 Agent 决定加长超时重跑 / 换策略 / 升级人工。
与脚本内部硬超时（Playwright/Node 脚本 HARD timeout）的分层关系见 dispatch-protocol.md「命令超时兜底与既有超时机制的分层关系」——外层取值须留够内层完整走完的余量。

## 任务粒度兜底
产出文件 >3 个或输入文件 >5 个时，必须分批派发或在本节明确说明为何不分批
（批量评估与编排模式见 dispatch-protocol.md「派发编排机制」）。

## 输出（路径约束）
产出文件：{AGATE_WORKSPACE}/tasks/{Txxx}/{本阶段产出文件}
（Txxx 是完整目录名，如 T002-fix-db-migration；不是纯 T002 编号。所有派发文件路径统一用 {Txxx} 占位符。）

⚠️ 路径是硬约束，不是建议：
- 必须用 Write 工具写入上述路径
- 不得将产出文件写入 /tmp、工作区根目录、或其他自选路径
- 写到其他位置 = 未产出，主 Agent 只检查上述路径
- 中间临时文件（如 gate-runner 落盘 traceback）放 **`<项目根>/.agate-tmp/`**，产出文件必须写入约定路径。
  ⚠️ **不要用 `/tmp`**：它虽**可写**，但在受限 harness（DSH 等）下是 **per-call tmpfs**——**跨调用不可见**（你这一轮写的探针/pidfile，下一轮就没了）。canonical 目录在项目树内，因此须**已被 .gitignore 忽略**、文件名**不得**匹配测试收集模式（`*.spec.*` / `*.test.*` 等，否则被测试框架默认 `include` 扫到、静默抬高基线）。完整约定见 `{agate_root}/platform-notes.md`「受限 harness 通用约束」

## 产出文件字段填写
用 `agate-md-field-set` 填写产出文件的 frontmatter 字段（先 `--list` 看本阶段应填字段清单；
set 报错就照提示改；不要手写 frontmatter，不要复制任何示例代码块）。
set 报错但改不明白 → 报告主 Agent，不要绕过 set 直接手改文件。
`phase`/`task_id`/`parent`/`trace_id`/`agent` 由主 Agent 派发时已在 dispatch-context 中给出
具体值，用 `agate-md-field-set` 逐个写入即可；完整字段列表见 `task-files.md`「通用 Header」。

## 能力补充说明（若 P1 有 supplementable 条目，此节必填）
本任务需要以下补充能力：
- {能力名}：使用 {补充方式}（如：派发 vision-analyst / 注入 playwright-cdp skill）
> 视觉能力（vision）supplementable 时的**获取指引必须注入本任务语境**：`ui_affected: true`
> 任务的 P6 派发须写明「可调用 vision-analyst 角色 / 视觉分析 skill 获取视觉能力，先自查能否
> 调用，再向主 Agent 报告」——把补充路径落到本任务具体阶段（A3 视觉语境扩展，BDD-11）。

## 能力自查（强制，BDD-12）
若本任务可能涉及视觉能力（如 P6 验收 UI 截图 / vision-analyst 派发）：
- **先自查能否调用视觉能力**（视觉模型 / 视觉分析 skill / 图像读取工具）
- 能 → 正常执行；不能 → 明确报告 `[CAPABILITY_GAP]` 并走降级路径（文档条文/像素检测/
  人工复核记录），不静默假设、不编造观察结果

## 门槛（什么算完成）
{可判定的完成条件，能从文件读出明确值}

## 返回前自检
- 产出的文件确实存在且非空
- 代码改动确实产生了 diff（实现阶段）
- 测试确实跑了（验证阶段）——unit.md 含 test runner 输出签名
- review 确实审查了（review 阶段）——结论引用了具体锚点（BDD 编号 / DESIGN_GAP 配对）

## P1/P2 声明写时自检
若本次产出含 P1-requirements.md/P2-design.md，返回前先跑
`python3 agate/scripts/check-frontmatter.py {写的文件路径}`；若 P1 声明 `ceremony: thin`，
额外 `git add` 本阶段产出后跑 `python3 agate/scripts/check-routing.py {任务目录}`。
非 0 退出先修正后再返回，不允许把格式错误留给 commit 时的 pre-commit hook 才发现。

## 返回给我（重要）
只返回两行：
  1. 产出文件路径
  2. 一句话摘要（不超过 30 字）
绝对不要返回文件全文——我只需要路径和摘要。
```

## 阶段特定提示（按需追加到 prompt 末尾）

### Review 角色特别指令
```
## Review 角色特别指令
如果你的角色是评审/验收角色（review / design-review / plan-eng-review / plan-design-review / plan-ceo-review / cso / qa / requirements-review / consistency-reviewer / protocol-alignment-review / judge）：
- 产出文件的 Header `status:` 字段初始为 `draft`
- 评审/验收完成后，**必须将 `status:` 改为 `approved` / `rejected` / `needs-revision`**
- gate 脚本读的是 Header 的 `status:` 字段，不是你的返回摘要——两者必须一致

**只读纪律（强制，不可省——2026-09-29 实证数据丢失事故后新增，RM-AG0081）**
评审是**只读角色**：你的产出是**评审结论**，不是代码改动。被评审的改动集**可能尚未提交**，
任何写仓操作都会**销毁他人的工作**。
- **禁止**任何破坏性或写仓命令：`git checkout -- .` / `git restore` / `git reset` / `git stash` /
  `git clean` / `git add` / `git commit` / `git switch -f` / 直接编辑或删除被评审文件
- 需要跑验证、做变异测试（mutation test）时，**只在仓外或可丢弃的副本上做**：
  - 优先 `git worktree add <仓外路径>`（用完 `git worktree remove`）；或
  - 复制到**一次性临时目录**，并把「创建 → 操作 → 清理」放进**同一次 bash 调用**
    （受限 harness 的 scratch 语义见 `platform-notes.md`「受限 harness 通用约束」——
    **部分 harness 的临时目录是逐调用重建的，跨调用不保留**，分两次调用会落空）
- scratch 操作失败时（目录不存在、权限拒绝等）**如实上报**，
  **不得**转而"修好"被评审的仓库——那是把评审失败升级成数据丢失
- 事故实例（勿重犯）：某次 SELF-GATE 评审的 scratch 目录跨调用落空，评审者遂在仓库内执行
  `git checkout -- .`，**丢弃了尚未提交的改动集**；恢复不完整，事后又发生在其 diff 捕获之后的
  3 处改动被一并丢弃。主 Agent 据 `git reflog` 才定位。登记为 RM-AG0081。
```

### P2 派发追加
```
## P2 最小验证
方案设计前，先用最小验证确认关键假设（10 行 HTML 测试页 / curl 请求 / 20 行脚本）。
验证结果写入 P2-design.md 的 minimal_validation 字段。
- 方案依赖浏览器行为/安全模型/外部系统行为 → 必须做最小验证
- 纯代码逻辑 → 须在 minimal_validation 字段声明 `纯代码逻辑，无外部系统依赖`（须写明依赖了哪些内部函数/数据转换）
## P2 gate_commands 补充
若 ui_affected 且新增测试主要落在 E2E 层，P3 阶段需声明 `gate_commands.P3_e2e` 作为 TDD 红灯确认命令（避免只跑单元测试产生假绿）。
```

### P3 派发追加
```
## P3 自检（强制）
产出测试代码后，先跑 `python3 {agate_root}/scripts/check-platform-assumptions.py <你写的测试目录>`，**必须 0 命中**（R1~R6：裸 python3 / 硬编码 PATH / 系统临时目录字面量 / 其它平台假设 / **subprocess 文本模式缺 encoding=**）。⚠️ **注释里的字面量同样计命中**——需要该路径时用运行时拼接（如 `TMP = "/" + "tmp"`）。本仓两个批次都曾因注释里的系统临时目录字面量在 P4 才转红（DEBT0048）。 ⚠️ **扫描面限定**：该脚本只认 `.bats/.bash/.sh/.py` ⇒ 对 **Python/shell 测试项目**有效；**TS/JS 用例（Playwright/vitest）不在扫描面内**，跑它恒绿不代表无平台假设。
然后必须自跑测试，确认每个红灯的失败原因都是"被测模块未实现"（import 失败 / 模块不存在 / 组件未导出）。
如果某个红灯的失败原因是"断言与测试数据矛盾"（如断言行数/列数/页数与 fixture 不符）——这是测试代码 bug，先修正断言再交付，不要交付给 P5。
手写魔数断言（`expect(x).toBe(100)` 但数据实际 50 行）与数据矛盾是 T075 的教训，P3 阶段就要发现。
```

### refactor 任务派发追加（P1 change_type: refactor）

```
## refactor 任务（P1 change_type: refactor）：回归测试口径
按回归测试口径设计——复用/保留既有测试用例，标注每条回归用例覆盖的路径，**不新增功能行为断言**；
跳过 check-tdd-red 红灯（重构无新行为可断言，红灯语义不适用，回归质量由 P5 全量回归 + P6 regression.log 兜底）。
## refactor 任务（P1 change_type: refactor）：P6 回归验收口径
P6 验收换用回归口径（换口径 ≠ 裁 P6，P6 仍不可裁剪）——三段式：① 行为不变声明（禁止伪造功能 BDD）；
② 全量回归全绿（以一条关键路径 BDD 的 PASS 行呈现，引用 P6-evidence/regression.log，尾行 EXIT_CODE: 0）；
③ 关键路径行为不变断言 BDD 逐条 PASS/FAIL。frontmatter 额外声明 `regression_pass: true`；
回归双证（regression_pass + regression.log）是 check-gate.py P6 硬校验，任一缺失 → gate exit 1；
regression.log 必须被 PASS 行引用；禁止新增非 BDD 编号 PASS 行；no_behavior_change 不豁免回归双证。
```

### P4 派发追加
```
## 上下文控制
读取代码文件以 P2-design.md 的 files_to_read 清单为准，按需读取（标了行号范围的只读片段）。
不要在项目里盲目搜索或整目录全读。
## 自查≠gate
写完代码后应自跑测试确认基本功能（自查），但自查≠P5 gate。不要声称"P5 已过"。
```

### P5/P6 派发追加
```
## 截图质量标准
操作类 BDD 截图必须互不相同（md5 去重），查询类 BDD 可不截图（断言值是唯一证据）。
## P6 BDD 二值规则
每条 BDD 结果只允许 PASS 或 FAIL，不允许"调整/跳过/覆盖"等中间态。任何 BDD 标 FAIL → gate 不通过。
## P6 BDD 结果格式
每条 BDD 验收结果必须用行首 `- PASS` 或 `- FAIL` 格式，便于 gate 命令 `grep -cE '^\s*- (PASS|FAIL)'` 可靠匹配。
不要用表格格式（`| BDD-1 | ... | PASS |`），不要用 ✅/❌ emoji，不要用其他格式。
示例：
- PASS BDD-1: 用户可以创建分享链接
- FAIL BDD-2: 过期链接返回 410
## P6 BDD 覆盖完整性
P6 验收必须全量对照 P1 的 BDD 条数（含 SCOPE+ 增补），不能挑验。
P1 有 N 条 BDD → P6 必须有 N 条验收结果（PASS 或 FAIL）。挑验 = gate 不通过。
## P6 引用 P5 证据、不重跑（refactor 任务，若适用）
若本次判定可引用 P5 证据（主 Agent 会在 dispatch-context 中告知审计 7 判定结果），
按 verifier.md「引用 P5 证据、不重跑」节口径处理，不必独立产出 regression.log。
## P6 证据要求
每条 BDD 验收结果必须有对应证据文件，存入 {AGATE_WORKSPACE}/tasks/{Txxx}/P6-evidence/。
证据类型：
- test-output.log — 验证脚本执行日志（所有任务通用）
- screenshots/ — Playwright 截图（仅 UI 任务）
- traces/ — Playwright trace（仅 UI 任务，可选）
无证据的 PASS 标记 = gate 不通过。
## P6 证据引用格式
每条 PASS 结果必须在括号内引用对应证据文件路径（相对于 P6-evidence/ 目录）。
示例：- PASS BDD-1: 用户可以创建分享链接（p6-bdd-1.png）
hook 会检查引用路径是否真实存在。无引用的 PASS 行不算有证据。
## P6 verifier 脚本执行
P6 verifier 交付的验证脚本（Playwright / shell / 测试框架）应由主 Agent 执行。
执行输出落盘到 P6-evidence/test-output.log。
若主 Agent 需要自写脚本（如 verifier 脚本不兼容当前环境），自写脚本的执行输出也落盘到 P6-evidence/test-output.log。
关键约束：P6-evidence/ 必须有执行产出，不接受空目录。
## 自查≠gate
写完验证脚本后应自跑确认语法正确（自查），但自查≠P6 gate。不要声称"验收已通过"。
## 证据日志格式约定（M1.3a）
凡是要求 subagent 产出可核验日志的场景（P5 测试执行、P6 验证脚本执行），
日志文件末行必须是可解析的退出码声明，格式固定为：
`EXIT_CODE: <n>`（n 为整数，0 表示成功）
不符合此格式的日志，check-p6-provenance.py 的一致性检测（M1.3b）不做强判定，
仅输出 INFO 提示"日志缺少标准 EXIT_CODE 尾行，无法自动核验一致性"。
```

### Judge 派发追加（P6.5，强制所有任务）

```
## P6.5 Judge 信息隔离（强制）
你的输入只传路径，且只允许白名单：P1-requirements.md / P2-design.md（仅验收相关节）/
P6-evidence/ 目录 / .state.yaml / gate-events.jsonl（另授 git log 查询权）。
禁止输入（黑名单，禁含于 dispatch-context 也禁读）：P6-acceptance.md、P6|P5|P4-dispatch-context-*.md、
P4-implementation.md、P4-review.md、P5-test-results/——verifier/implementer 的自述与派发上下文一律不读。
## 三档预算（超限诚实降级）
轮次 ≤2 / token 100k（judge_token_budget 可覆盖）/ 时间 30min。任一预算耗尽 → 立即停止，
按已验条目落盘 verdict，必须 status: needs-revision + partial: true，禁止 status: passed 静默放行。
## 认知约束（只信证据与 git log）
逐条重验所有 BDD（含 P6 已判 PASS 项，零挑验）；每条结论必须引用 P6-evidence/ 下真实存在且非空的
证据文件（verdict_evidence 清单内）；禁止"看起来没问题"式结论；git log 可查证执行留痕。
## verdict 产出格式
{AGATE_WORKSPACE}/tasks/{Txxx}/P6.5-judge-verdict.md：Header 含 status（passed/rejected/needs-revision）+
criteria_total + criteria_passed + verdict_evidence [JSON 列表]（+ partial 可选）；正文每条 BDD 一行
`- (PASS|FAIL|NEEDS-REVISION) BDD-NN: 描述 (证据路径)`；criteria_total 必须等于 P1 #### BDD-NN: 标题数。
```

### P4 回退派发追加（P5/P6 失败回退时使用）

```
## 回退诊断（强制）
本次是从 P5/P6 回退。上次失败信息：{主 Agent 填：哪条测试/BDD 失败 + 失败现象}

修复前必须先诊断根因，按以下流程：
1. 读 P5-test-results/ 或 P6-acceptance.md 的失败详情
2. 列出至少 3 个可能原因 + 每个原因的证据
3. 选最可能的原因，写最小验证步骤确认
4. 确认根因后再修代码

修复产出必须包含：
- P4-diagnosis.md：根因 + 排除项清单（已排除 X，证据 Y）+ 验证步骤
- 代码改动（只修根因，不带入其他改动）

跳过诊断直接修代码 = 门槛不通过。
```

### 修复轮派发追加（review needs-revision / 修复轮时使用，给主 Agent 的模板）

主 Agent 修复轮派发时，dispatch-context 用增量模式：
- 上轮产出路径：{P{N}-产出文件.md 路径}
- 上轮 dispatch-context：{P{N}-dispatch-context-{role}.md 路径}（复用其约束）
- 修复目标：{具体要修复的问题}
- 不要重写完整目标/约束/上游关联——引用上轮文件即可

### P8 派发追加
```
## READY 收尾检查
P8 gate 通过后，主 Agent 会执行收尾检查（停止调试服务、清理临时数据、还原开发环境、确认生产无残留）。
你在 P8 产出中应列出：启动了哪些临时服务/进程、创建了哪些临时数据、做了哪些开发安装，供主 Agent 清理。

## 版本 bump 判定
- 公共 API 行为变化 / 破坏性变更 → major
- 加功能 / 内部重构改 API（向后兼容）→ minor
- 修 bug / 不改 API 行为 → patch
- 测试缺陷不应影响版本号决策：测试 hard-code 版本号 → 修测试，不降级版本
- 在 P8-release.md 中显式声明：bump 类型（major/minor/patch）+ 理由
```

## 项目占位符映射

> 占位符说明：各项目在自己的约定文件（如 CLAUDE.md）中定义具体映射。以下给出示例值供参考，不是 agate 本身的约定。

| 占位符 | 说明 | 示例值 |
|--------|------|--------|
| {project_conventions_file} | 项目约定文件 | `CLAUDE.md` / `CONTRIBUTING.md` |
| {project_index_file} | 项目总览文件 | `INDEX.md` / `README.md` |
| {test_code_dir} | 测试代码目录 | `tests/` / `backend/tests/` |
| {implementation_dir} | 源码目录 | `src/` / `app/` / `backend/pkg/` |
| {build_command} | 构建验证命令（从 P2 gate_commands 读取）| 项目自定义 |
| {lint_command} | 代码检查命令（从项目约定读取）| 项目自定义 |

## 关键提醒
- prompt 里只写文件**路径**，绝不复制文件内容
- 明确要求 subagent 只返回路径+摘要
- **Header 给成品不给格式**：主 Agent 派发时已知道所有值（phase/task_id/日期），直接填好让 subagent 复制，避免 subagent 自己拼 trace_id 拼错导致门槛校验失败
- **路径用完整目录名**：task_dir 是 Txxx-描述（如 T002-fix-db-migration），不是纯 Txxx
- 这两条是上下文不爆炸的保证
- **P4 派发引用 files_to_read**：让 implementer 按 architect 画好的"上下文地图"读文件，而非自己乱窜——这是控制被派发方上下文的关键
- **分阶段落盘默认启用**：每次派发都带落盘指令，不是空返回后的补救措施
- **产出路径是硬约束**：subagent 必须写入 prompt 指定的路径，不得将产出文件写到 /tmp 或其他位置。主 Agent 只检查约定路径，写错位置 = 未产出 = 重试浪费
- **dispatch-context 是 subagent 的核心输入**：主 Agent 派发前必须写好 dispatch-context（含目标/约束/上游关联/输入文件），subagent 从中获取任务特定信息，prompt 只提供跨阶段通用执行纪律
- **agent 字段由主 Agent 填好**：主 Agent 派发时已知角色名，直接填入，subagent 复制即可

## 返回前自检（强制）
如果任务涉及修改/创建文件，返回前必须：
  1. 用 bash 执行 grep/rg 确认改动已落盘（如：grep "新增函数名" 目标文件）
  2. 如果 grep 未匹配 → 文件未写入成功 → 重新写入后再返回
  3. 不要在未确认落盘的情况下返回"已完成"

## 返回格式（修改类任务）
第 3 行（可选）：files_modified: [path1, path2, ...]
列出你修改/创建的文件路径。主 Agent 将校验这些路径存在且非空。
