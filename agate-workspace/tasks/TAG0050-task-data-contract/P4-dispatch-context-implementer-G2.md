---
phase: P4
generated_by: 主 Agent（G2 = B + C 合批实现）
task_id: TAG0050
role: implementer
batch: G2
---

<dispatch_guide>
> ⚠️ 本批 = **批次 B + 批次 C 合批实现**（用户已批准合批；依赖链 `A1 → B → C` 内部满足）。**只实现这两批**，不改设计路线。

## 前置状态
- 上一批 **G1（A2+A3+A4）已提交** = `54a814fc`；本批在干净树上开工。
- A1 已交付：`agate/rules/task-data/LEVELS.yaml` + `level-1.yaml`（冻结快照）、账本七规则、`agate-task-init.py`。

## 批次 B — 写入工具与契约单源（BDD-45..51，设计 §3，complexity high）

**交付物**
1. **`agate/scripts/agate_schema.py`（新增）**——**唯一的递归 schema 校验实现**；`agate-frontmatter-check.py` / `check-yaml-schema.py` / `agate-config.py` 三处**统一调用它**（BDD-50：不存在第二个递归 schema 校验实现）。
2. **`agate-md-field-set.py` 7 操作**：`set` / `append` / `upsert` / `remove` / `--list` / `explain` / `render`；`agate-config.py` 的 `set` / `unset` / `explain`——**每种操作各写一次往返用例**并全绿（BDD-45）。
3. **系统字段**（`writer: system`，如 P6 的 `pass`/`fail`）：**写入被拒并说明来源**；`md-field-get` 读取返回按 `derive` **现算**的值（忽略文件里的值）（BDD-46）。
4. **缺 frontmatter → ERROR**（修 F10；不回退到正文正则）（BDD-47）。
5. **渲染块**（`<!-- AGATE:RENDER ... -->`）：手改其内容 → **ERROR** 并给出 `agate-md-field-set.py render` 修复命令；**两侧 CRLF 规范化为 LF 后逐字节比较**，CRLF 下行为一致（BDD-48）。
6. **报错附带的修复命令真能执行并转绿**（BDD-49）。
7. **E3（BDD-51）**：T1 绊线在两仓语料（agateon + peekview）命中行各随机抽 50 条人工分类——「引述/讨论/否定」类须为 **0**；**若不为 0**，按设计 §3.6 落实「P7/P8 评审稿 T1 降 WARNING 且声明同时写入字段」的降级。**抽样结果与结论写入 `P4-implementation-G2.md`**。
8. **T1–T3 绊线**按设计 §3 启用（注意 §1.3 R7：批 B 启用 ERROR 前必须完成 E3 抽样）。

## 批次 C — 生产接触（BDD-52..55，设计 **§3.1 规格**，complexity low）

> ⚠️ **必须按 P2 §3.1 的 F4 规格实现**（它**取代**设计 §3.6 的「T4 保持原样」与「T4 优先」表述）。

1. **BDD-52**：主产出 frontmatter 缺 `prod_touched` → **ERROR** 并附修复命令。
2. **BDD-53**：`prod_touched: true` 且**当前不在 PAUSED** → **中止提交**。
3. **单一来源**（§3.1 第 1 点）：
   - `agate/rules/markers.yaml` 中 `PROD_TOUCHED` 的 `lead_variant` 由 `dash_only` 改为 **`default`**；
   - `agate/scripts/pre-commit-gate.py:348/355` **删除字面正则** `^\s*-?\s*\[PROD_TOUCHED\]`，改为调用 `agate_markers.pattern("PROD_TOUCHED")`；
   - 消除「注册表（`dash_only`）与 T1（`default`）口径分叉」。`markers.yaml` 的 `mk_3`（`render()` ⊂ `pattern()`）守护单源继续通过。
4. **BDD-54**：正文写粗体 `**[PROD_TOUCHED]**`（正向）而字段写 `prod_touched: false` → **仍中止**（T4 优先于字段）。补锚：**非声明文件**（如 `P4-progress.md`）写粗体/引用块形式的正向 `[PROD_TOUCHED]` + 字段 false → 中止。
5. **BDD-55**：否定写法 `- [PROD_TOUCHED]: 无` → **仍中止**（fail-safe），报错给出**专门指引**：「疑似否定写法：未触达生产请在主产出写 `prod_touched: false`，并删除正文中的标记」。
6. **扫描面**（§3.1 第 2 点）：对每个**有暂存文件的任务目录**扫描**全部暂存 `*.md` 文件的新增行**（`git diff --cached -M`），不限于声明文件；**只排除 `AGATE_CARD` 块**，**不额外排除**围栏/行内代码。
7. **T4 = 唯一 PROD_TOUCHED 安全门**；**T1 标记表去掉 `PROD_TOUCHED`**（避免两条路径判同一件事）。

## 测试（P3 已落成红灯，本批须转绿）
- `agate/tests/unit/test_tag0050_write_tools.py` —— BDD-45..51
- `agate/tests/integration/test_tag0050_prod_touched.py` —— BDD-52..55
- 另须保持绿：`agate/tests/unit/test_tag0050_fitness.py`（`schema_single_source` 等架构适应度）

## 约束
- **平台无关**（无裸 `python3` / 硬编码 PATH / 系统临时目录字面量，注释也算）。
- **legacy 兼容**：§8 承诺（legacy 退出码与 ERROR 集合不变）——批 C 的 PROD_TOUCHED 在 legacy 上现状也拦，不属新差异（§3.1 第 4 点）。
- 若需新增测试文件，同步更新 `P3-test-cases.md` 并说明计数变化。
- 新增/改名 `agate/scripts/` 下文件时，读 `agate/scripts/README.md`「新增脚本登记面」节并登记（CHECK9/SG.6/CHECK10）。

## 修完自跑（自查 ≠ gate）
- `timeout 900s python3 -m pytest agate/tests/unit/test_tag0050_write_tools.py agate/tests/integration/test_tag0050_prod_touched.py agate/tests/unit/test_tag0050_fitness.py -q`（全绿）
- `python3 agate/scripts/check-protocol-consistency.py`（**0 ERROR**）
- `bash agate/tests/scripts/count-tests.sh`（计数与 P3 基线核对，记录差异原因）
- `python3 agate/scripts/check-platform-assumptions.py`（0）
- 若动了 `agate/rules/markers.yaml`：`python3 -m pytest -k mk_3 -q`（单源守护）

## 落盘
- 新建 `agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G2.md`（交付物逐条、文件清单、DESIGN_GAP、自查结果、环境隔离）
- 追加 `P4-progress.md`

## 输入文件
- `docs/design-notes/design-tag0050-task-data-contract.md`（§3 批次 B、§3.6 T1 绊线、§4 批次 C；**§3.1 规格优先于 §3.6/§4 冲突表述**）
- `P1-requirements.md` §4 批 B/C（BDD-45..55）、`P2-design.md` §3/§3.1/§3.3、`P3-test-cases.md`
- `agate/scripts/`：`agate-md-field-set.py`、`agate-md-field-get.py`、`agate-frontmatter-check.py`、`check-yaml-schema.py`、`agate-config.py`、`pre-commit-gate.py`、`agate_markers.py`
- `agate/rules/markers.yaml`、`agate/rules/phases.yaml`、`agate/rules/dispatch.yaml`
- `{agate_root}/assets/execution-roles/implementer.md`
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

<objective_info>
- **当前 HEAD**：`54a814fc`（G1 已提交）；分支 `feat/TAG0050-task-data-contract`
- **协议版本**：v0.79.0
- **已交付**：A0/A1/A2/A3/A4（含 G1 C8 闭环）
- **本批**：B（BDD-45..51）+ C（BDD-52..55）
</objective_info>
