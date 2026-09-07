---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: implementer
batch: 2-docs-consistency
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。
> 本轮是 **P4 批 2（docs-consistency）**（P2 dispatch_plan serial 两批之二）。批 1（scripts-tests，M1-M6）已落地并 11 用例转绿。

### 目标

实现 P2-design.md 的 **M7-M11 文档面改动**，让 P3 的 `test_upgrading_lifecycle.py` 中 **BDD-10 / BDD-11 / BDD-12 + BDD-4 判据 3** 相关红灯转绿（当前 7 failed）。

**M 编号落点（P2-design §1.1 + §4.3）**：

| M | 文件 | 改动 |
|---|------|------|
| M7 | `agate/UPGRADING.md` · 新增 `## 版本管理生命周期` 节（插在 `## 1. 通用升级步骤` 之后，不重排既有编号）| 三部分：① 安装/迁移/更新/回退**对照表**（两列 legacy 软链布局 / 版本管理布局，见 P2-design §4.3 表）；② **hook 重装时机条目**（统一口径：resolve-entry 固定入口机制下切版本/升级通常无需重跑 `install-hook.py`；仅 hook 薄壳 `.sh` 变更或 Windows 复制模式才重跑）；③ **根 `~/.agate/scripts/` 维护语义条目**（决策 B1 副本语义，见下方「与批 1 实现对齐」） |
| M8 | `agate/UPGRADING.md` · v0.50.0 节 §① 布局变化表格（约 L543-583）| 「根含 `scripts/`」行 + 「升级 = `agate-install.py`」行：各加一句「详见『版本管理生命周期』节」指针，**不改历史叙事文字** |
| M9 | `agate/UPGRADING.md` · v0.60.0/0.61.0/0.62.0 节 与 v0.66-0.68 节 | **不逐条改写**历史节；hook 重装口径分歧由 M7 生命周期节的统一口径条目收敛。历史版本节保留原叙事 |
| M10 | `README.md` 与 `README.zh-CN.md` · 快速上手「版本管理」块（约 L34-46）| 补「进入版本管理布局」官方路径 `install.sh --versions`；升级表述与生命周期节口径一致（版本布局 = `agate-install latest`）。中英同步 |
| M11 | `agate/SETUP.md` · 「## 升级 Agateon 之后」节（约 L242-250）| 升级表述加指向 UPGRADING 生命周期节的指针，口径一致（legacy = `git pull`；版本布局 = `agate-install latest`） |

### 与批 1 实现对齐（BDD-4 判据 3 交叉锁 —— 关键）

批 1 的 M2 实际实现（见 `P4-implementation.md` §改动清单 + §决策/偏差声明，**必读**）：
- 根 `~/.agate/scripts/` = **双 copytree** 叠加：① 运行中安装器的 `scripts/` 目录（保证 `agate-install.py` 等入口命令在新机可用）② `_protocol_root(version_dir)/scripts` 当前版本协议脚本（重跑 `latest` 随 current 刷新）。协议脚本覆盖安装器脚本（后拷贝者胜）。
- `agate-install.py latest` = 无参 install 的显式别名（批 1 DESIGN_GAP 2）。
- `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时新增 `git fetch --tags`（批 1 DESIGN_GAP 4），令 `latest` 能发现上游更高 tag。

**M7 的「根 `~/.agate/scripts/` 维护语义条目」必须描述批 1 实际建立的行为**，不能照抄 P2-design §3 末尾的理想化 B1 语义块——若两者有出入，以批 1 实现为准来写文档（`test_upgrading_lifecycle.py::test_tag0032_bdd_4_root_scripts_copy_semantics_documented` 会断言文档条目与实现一致）。核心要点须涵盖：
- 根 `scripts/` 是副本（非软链），随 `agate-install.py`（含 `latest`）重跑刷新
- `repo/` 或某 `vX.Y.Z/` 版本目录被删**不影响**已建立的 `~/.agate/scripts/` 副本可用性
- 该副本**不参与 hook 版本解析**——hook 经 resolve-entry 固定入口按项目 `.agate-version` 解析版本，切版本无需重跑 install
- 升级期须重跑 `agate-install.py latest` 使根入口刷新到新版本工具

### 测试转绿目标（本批）

自跑确认 `test_upgrading_lifecycle.py` 全绿：
`timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -p no:cacheprovider -q`
（当前 7 failed：`test_tag0032_bdd_10` / `bdd_11` / `bdd_4_root_scripts_copy_semantics_documented` / `bdd_12[v050_root_scripts_row_pointer]` / `bdd_12[v050_upgrade_row_pointer]` / `bdd_12[hook_reinstall_unified_across_version_sections]` / `bdd_12[readme_setup_aligned]`）
读这些用例的断言原文（`agate/tests/unit/test_upgrading_lifecycle.py`）确认文档改动满足断言——**不改测试**（测试与 P1 BDD 矛盾 → 标 `[DESIGN_GAP]`）。

改完跑一致性回归（BDD-12 附加回归项）：
`timeout 120 /usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（须 0 ERROR）

### 约束

- **最小实现**：只改让红灯转绿的文档，不重写无关章节、不"顺便润色"
- **不逐条改写历史版本节**（M9）：v0.50.0 / v0.60-0.62 / v0.66-0.68 节的历史叙事保留原文，只在 M8 指定的两行加指针（BDD-12「历史叙事保留」判据 = 加指针不改叙事）
- **文档口径单一真相源**：M7 新节是唯一权威，M8/M10/M11 都指向它
- **范围锁定**：不碰 out-of-scope；不改脚本代码（批 1 已完成）；不改测试；不改 P2 gate_commands
- **SELF-GATE**：本批改 `agate/UPGRADING.md` + `README.md` + `README.zh-CN.md` + `agate/SETUP.md` → 触发 SELF-GATE；主 Agent commit 时处理 commit message
- 疑问标 `[CLARIFY: xxx]`；自主决策标 `[DESIGN_GAP: xxx]`（独立成行单行 tag）；发现必须做但 P1/P2 未覆盖 → 标行首 `[SCOPE+]`
- 产出 `P4-implementation.md` **追加**批 2 节（不覆盖批 1 内容）——用 Edit 在文件末尾追加 `## 批 2（docs-consistency）` 节，或另写 `P4-implementation-batch2.md`（二选一，在 progress 注明）

### 上游关联

批 1 P4-implementation.md（M1-M6 落地，11 用例转绿，4 条 DESIGN_GAP）。P2-design.md approved（决策 A1/B1；§4.3 UPGRADING 生命周期节结构 + BDD-12 checklist 四条落点）。P2-review.md approved。P3 `test_upgrading_lifecycle.py`（BDD-10/11/12 + BDD-4 判据 3 断言）。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1 实际实现 + 4 条 DESIGN_GAP——M7 维护语义条目须与此对齐，必读）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（§4.3 UPGRADING 生命周期节结构 + §4.3 BDD-12 checklist 四条落点 + M7-M11 落点，权威）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review.md（非阻塞澄清项）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P3-test-cases.md（BDD-10/11/12 + BDD-4 判据 3 用例映射）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（BDD-10/11/12 原文 + §4 扫描 4 文档矛盾清单）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（scope / SELF-GATE 触发面）
- /home/kity/oclab/agateon/agate/assets/execution-roles/implementer.md（角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_upgrading_lifecycle.py（本批转绿目标用例——读断言原文，**不改**）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（改动对象：§1 通用升级步骤位置 + v0.50.0 §① 表格 + v0.60-0.62 / v0.66-0.68 hook 节）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/README.md 与 README.zh-CN.md（快速上手块）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/SETUP.md（升级节）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/install.sh（批 1 已加 --versions 分支——M10 README 补的官方路径以此为准）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`
- 自跑：`timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -p no:cacheprovider -q`；一致性 `timeout 120 /usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 自己的脚本，须 0 ERROR）
- **主 checkout 禁止改动**；改文档在 worktree
- bash 外层 `timeout` 30-180s；单步串行；状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：文档改 worktree 的 `agate/UPGRADING.md` / `README.md` / `README.zh-CN.md` / `agate/SETUP.md`；P4-implementation 批 2 节写进 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md`（追加）或 `P4-implementation-batch2.md`
- 分阶段落盘：每改完一个文件 / 自跑一次，追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-progress.md`

### 返回

只返回两行：① P4-implementation.md（或 batch2）路径；② 一句话摘要（≤30 字：本批文档改动 + test_upgrading_lifecycle.py 转绿情况）。

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
