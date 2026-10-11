---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0051
role: implementer
scope: Impl-A（批 ready-no-tag + release-gate）
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的**强制指令**。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。
> **本任务 P4 由 4 个 implementer 并行**（A/B/C/D），各自**只改本指引列出的文件**——**越界改动会与他人冲突**。

### 你负责的范围（**只改这些文件，别的一律不碰**）

| 批 | 文件 |
|----|------|
| `ready-no-tag` | `agate/scripts/check-gate.py` |
| `release-gate` | `agate/scripts/agate-release.py`、`.github/workflows/release.yml` |

**禁止改动**（他人负责）：`agate/rules/**`、`agate/phase-cards/**`、`agate/state-machine.md`、
`agate/dispatch-protocol.md`、`agate/assets/**`、`AGENTS.md`、`agate/git-integration.md`、`agate/UPGRADING.md`、
`docs/**`、**以及 `agate/tests/**` 下的任何文件**（P3 已产出的测试是**验收判据**，不是你的实现对象；
若你认为某测试断言写错，**标 `[SCOPE+]` 报告主 Agent**，不要自己改）。

### 目标

**① M1（`check-gate.py::gate_p8`）——P8 不再要求 version / tag**

- **删** tag 存在性 WARNING 块（约 `:2376-2389`，含 `VERSION_TAG_PREFIX` 的使用）；
- **删** version 双路径 WARNING 块（约 `:2317-2337`）；
- **删** CHANGELOG 暂存区 diff WARNING 块（约 `:2339-2356`）——载体改由
  `check-changelog.py <task_id>` 承担（该脚本已在**必经路径** `pre-commit-gate.py:1086` 被调用，
  故判据强度不降）；
- **删** 迁移期 `agate.config.yaml` 提示块（约 `:2358-2374`，其触发条件与文案均基于已移除的 version/tag 痕迹）；
- **保留**：`bump_type` 缺 → exit 1（约 `:2245-2247`）、`debt_check` 缺 → exit 1（约 `:2249-2251`）、
  结构化 `delivery`（约 `:2255-2292`）、RM-AG0043 roadmap 反查（约 `:2294-2315`）；
- **新增**：`delivery.method` **枚举校验**——读契约快照的 `delivery.method_enum`（`load_contract`），
  **缺省（快照无该键）时 no-op**（向后兼容，legacy 走既有 `:2288` 子串路径**不受影响**）；
  仅对**非 legacy 且 `task_level ≥ 2`** 的任务施加；枚举外**非空**值 → **exit 1**。

**② M11（`agate-release.py` 新增 `gate` 子命令）**

- 串起：**目标提交 CI success（查 check-runs，按 required contexts 逐项 `conclusion == success`；
  非 success 含 `in_progress`/`queued` ⇒ fail-closed 非 0）** + `check-protocol-consistency.py` 0 ERROR
  + `check-gate.py P8`（复用其 RM 反查/delivery/bump_type 判据）。
- **必须**：CI 查询走**可注入命令**（`--ci-cmd` / 环境变量），使本地 P5/P6 能用 fixture/mock 验证；
  CI 内用真 `gh`。**不得写死 `main`**——经 `git remote` / `gh` 解析默认分支（复用
  `agate_common.default_branch()`，RM-AG0116）。
- **不得**无界轮询（无 `sleep` 循环）；竞态以「前置顺序（先合 PR → 等 main CI 绿 → 再跑门 → 打 tag）+
  fail-closed」处理。
- 保持既有子命令（`build` / `notes` / `boundary` / `pyyaml-pin` / `is-prerelease`）**行为不变**；
  argparser 结构见 `:330-348`。

**③ M12（`.github/workflows/release.yml`）**

- `on:` **追加** `workflow_dispatch:`（可带 `tag` 输入）——与既有 `push: tags: ['v*']` **并存**
  （先例：仓库内 `deploy-pages.yml`）。
- **追加**一步**调用** `agate-release.py gate`（tag-push 路径的 fail-closed backstop）——
  **只调用、不内联逻辑**（该文件既有头注释明写「构建逻辑全在 `agate/scripts/agate-release.py`，
  本文件只做编排」）。
- **保留**既有 `:33-65` 的「Verify tag points to matching commit」步**不动**（RM-AG0098 的落地件，
  本任务只要求它继续生效）。

### 统一口径（canonical——本任务 4 个 implementer 必须逐字一致）

写进你改动的**任何文档/注释/错误文案**时，READY 前置一律表述为：

> **READY 前置 = 交付物 + CHANGELOG `[Unreleased]` 含 task_id + `bump_type` 意图 + 交付收尾 +
> CI 全绿（含 push 口径）；不含 version bump / tag。**

### 上游输入

- `{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P2-design.md`（**核心**：§1.1 M1/M11/M12 的落点与行号、
  §3 决策 1/3/5/6、§4 批表）
- `.../P2-review.md`（approved；注意 NB-2：`:2339-2356` **定死为删**）
- `.../P1-requirements.md`（BDD-2/3/4/5/6/7/8/9/10/11/12/13/16/17/19 是你的验收对照）
- `.../P3-test-cases.md` + `agate/tests/unit/test_tag0051_p8_gate.py`、`test_release_gate.py`
  （**红灯判据**——你要让它们转绿，但**不得改动测试文件本身**）
- `agate/scripts/agate_common.py`（`load_contract` / `task_level` / `default_branch`）
- `agate/rules/task-data/level-1.yaml`（`delivery` 契约现状；`method_enum` 由 Impl-B 在 `level-2.yaml` 新增
  ——**你只需读「快照里有没有 `method_enum`」并按缺省 no-op 处理**，不要自己创建 level-2）

### 客观查证信息（主 Agent / 评审已核实）

- `check-gate.py::gate_p8`：被删的四个块**全部是 WARNING（不 return）** ⇒ `(rc, ERROR 集合)` 对 legacy 不变。
- `delivery` 枚举钩子只在 `if task_level(task_dir) is not None:`（`:2255`）结构化分支内 ⇒ legacy 不进。
- `agate-release.py` 文件名带 `-` **无法 import** ⇒ 测试走 `subprocess`（P3 已如此）。
- required contexts 实测 **6 项**（`shellcheck×2 / pytest×2 / consistency / gate-backstop`），`strict=true`；
  `combined status API` 实测返回 `state=pending, total_count=0` ⇒ **必须查 check-runs**。
- **本任务是契约级**（`contract_level: 1`）；本仓**无 `.agate-version`**，协议根 `~/.agate/v0.81.0/agate`。

### 约束（硬）

- **只改上表文件**；**不得**新增 `agate/scripts/` 下的**新文件**（BDD-23：落点必须是既有 `agate-*.py`
  ⇒ 登记面零触发；新增 `check-*.py` 会红 SG.6）。
- **自查 ≠ gate**：写完自跑相关测试确认基本功能即可，**不要**声称「P5 已过」。
- **不得**修改 P3 的测试文件、不得为了让测试变绿而弱化断言。
- 状态标记二值：未触发写 `[PROD_NOT_TOUCHED]`。bash 设超时。
- progress **追加**到 `P4-progress-implementer-A.md`。

### 返回给我（重要）

只返回**三行**：① 你改动的文件路径列表 ② 一句话摘要 ③ `files_modified: [...]`。
**绝对不要**返回文件全文或完整 diff。
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
**这是本卡明确的 checklist 条目**（RM-AG0083 / DEBT0015 的落点）：`gate_commands` 声明了**构建 / 打包 / 部署**类命令时，P4 完成后须**实际产出并确认产物存在**（如 UI 任务的 `dist`）；协议**无**对应机械 gate（产物路径项目各异）⇒ 该条目即「无机械 gate 时的既定出口」，主 Agent 在 P4 gate 前逐项确认，不得只凭单元测试全绿判完成。

## 生产环境隔离
任何写入生产环境/生产数据库/生产 API 的操作都必须先 PAUSED 报告人工。
```

## 产出规格

- P4-implementation.md 必须声明 `implementation_dir: {实际路径}`
- 代码文件在声明的目录下
- 遵守 P2-design.md 的方案设计 + 现有项目代码规范

## 批级证据 P4-evidence（MVWU 阶段 1，不阻断，TAG0036）

> 适用于 P2 声明了 `dispatch_plan.batches` 的任务：每批一个证据日志，回答"这一批的 `tests_filter` 跑出了什么"。**记录不阻断**——它不是 gate、hook 或 CI 的一部分，非零退出的批仍可 commit。

- **路径**：任务目录下 `P4-evidence/{batch}.log`。`{batch}` = 该批在 `dispatch_plan` 中的 `id`，须 filename-safe（匹配 `[A-Za-z0-9._-]+`）。
- **写入方**：主 Agent 在该批 commit 前运行该批 `tests_filter`，并把运行结果**机械转录**入日志（重定向/脚本落盘，不是撰写内容；内容只来自命令实际结果）。
- **格式**：逐行 `key: value`，最小内容：
  - `command`：实际运行的命令
  - `exit_code`：命令退出码
  - `git_head`：运行时的 HEAD，须为全长 commit 对象名
  - `timestamp`：运行时间
  - `expected_red`：预期为红的用例，默认 `[]`
  - `duration_seconds`：耗时秒数
  - `failed_tests`（可选）：实际失败的用例，默认 `[]`
- **列表编码**：`expected_red` / `failed_tests` 的值为单行 flow 序列，元素为用双引号包裹的 pytest node id（如 `["tests/a.py::test_x[case 1]"]`）；元素相等按 node id 精确字符串相等比对，不可解析时观测器给 UNKNOWN。
- **观测**：`python3 agate/scripts/check-mvwu.py <task_dir>`（默认每批一行契约行）或 `--observe`（每批一行观察表）。观测**不阻断**；UNKNOWN 不等价于 PASS——无法核对时不得当作通过。
- **边界**：该目录不进 judge 白名单，也不登记进 rules / dispatch-protocol；P6.5 judge 不读取它。

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
2. **自行加范围外改动**：发现需要做但不在 P1 范围内的改动 → 标 [SCOPE+]（行首声明格式：裸 `[SCOPE+]` / `- [SCOPE+]` / `**[SCOPE+]**` / `> [SCOPE+]` 均可；句中引用与反引号包裹不触发 gate）而非直接做
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
