---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: review
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

对 TAG0032 P4 实现（批 1 scripts + 批 2 docs）做独立实现评审，产出 `P4-review.md`。C8 P4 映射：`domains=[backend, cli]` + `risk=high` → 单评审角色 `review`（去重后一个，无需组长，直接写 P4-review.md）。

**只审不写**——不改代码/文档；修复意见由主 Agent 回派 implementer 落地。

### 约束

- 产出 Header `status:` 初始 `draft`；评审完成后**必须**改为 `approved` / `rejected` / `needs-revision`（gate 读 status 字段）；**agent 字段必须是 review（非 main）**——check-gate.py P4（同 P2 分支）硬拦截 agent=main 的 approved
- 结论须引用具体锚点（文件:行号 / M 编号 / DESIGN_GAP 编号 / BDD 编号），按角色「输出格式」（[CRITICAL] / [INFORMATIONAL] + 文件:行 + Fix）
- 逻辑变更 / 架构决策 → 列选项 A/B/C 让主 Agent 决定，不直接给单一结论

### 本任务重点核查项（逐条给结论）

**A. 4 条 [DESIGN_GAP] 裁决（最高优先级）** — 逐条判断：是「合理自主决策，P7 配对 REVIEWED 即可」，还是「偏离 P2 设计意图 / 引入新风险，须回 P2 或 implementer 修正」：

1. **DESIGN_GAP 1（M2 双 copytree）**：根 `~/.agate/scripts/` = ①运行中安装器 `scripts/` + ②`_protocol_root(version_dir)/scripts` 叠加（协议脚本覆盖）。
   - 核查：P2-design 决策 B1 原意是「副本 = 当前 current 版本协议 `scripts/`」单源。双 copytree 是否偏离？真实元仓库形态下 `vX.Y.Z/agate/scripts/` **本就含** `agate-install.py` 等版本工具（协议仓的一部分）——那么「自拷贝运行中安装器」这一层是**真需要**还是**只为迁就 P3 stub fixture**（fixture 故意精简了协议 `scripts/`）？若只为迁就 fixture → 应改 fixture 让其贴近真实元仓库形态，而非在 install 里加迁就逻辑。
   - 风险：安装器版本 ≠ 协议版本时，根 `scripts/` 会是「旧安装器工具 + 新协议脚本」混合，可能出现工具与协议不同版本的隐性不一致
2. **DESIGN_GAP 2（`latest` 别名）**：`agate-install.py main()` 新增 `latest` 作无参 install 别名。
   - 核查：P1 §3.4 / BDD-2 迁移指引 / BDD-13 步骤 5 / `install.sh --versions` 确实都用 `agate-install.py latest` → 这是 P1 隐含要求、M 表遗漏，属合理补全。核实 `_usage()` 文案已同步、`latest` 语义与「装最新 tag」一致、不与既有版本号参数解析冲突
3. **DESIGN_GAP 3（`install.sh --versions` 用 `$SCRIPT_DIR/agate/scripts/agate-install.py`）**：不用 `~/.agate/repo/agate/scripts/agate-install.py`。
   - **核查重点（可能 CRITICAL）**：真实新机场景——用户如何拿到 `install.sh`？若是 `curl -sSL <raw-url>/install.sh | bash`，`$SCRIPT_DIR`（`dirname "$0"` / `BASH_SOURCE`）指向哪里？管道执行时 `$SCRIPT_DIR` 可能是 `/dev/fd` 或 cwd，`$SCRIPT_DIR/agate/scripts/agate-install.py` **不存在** → `install.sh --versions` 在真实 `curl | bash` 场景是否直接坏掉？还是 install.sh 本就要求先 `git clone` 仓库再本地跑（那 `$SCRIPT_DIR` 有效）？读既有 `install.sh`（批 1 改动前的原逻辑）确认它对「如何获取自己」的假设，判断 DESIGN_GAP 3 是否破坏了新机官方路径（BDD-5 用例是隔离 HOME + 本地 fixture，测不出 `curl | bash` 场景）
   - 若破坏真实场景 → [CRITICAL]，给修正方向（如：`git clone` 后用 `~/.agate/repo/agate/scripts/agate-install.py`，仅当该路径不存在才回退 `$SCRIPT_DIR`；或 P3 fixture 应让协议 `scripts/` 含 `agate-install.py`）
4. **DESIGN_GAP 4（`_ensure_repo` 加 `git fetch --tags`）**：复用已 clone 的 `~/.agate/repo` 时先 fetch。
   - 核查：属 TAG0032 「update 路径」范围内（P0-brief scope Phase 3）→ 合理。核实 fail-open（离线 fetch 失败不中断）、`--force --prune` 不会误删本地 tag、不影响 `agate-install.py vX.Y.Z`（指定版本）路径

**B. 决策 A1 实现正确性**：
- `_protocol_root`（`agate_common.py`）探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后——读实现确认硬编码顺序、两形态皆无返回 `vdir` 原样（下游 `resolve-entry.py:50-52` fail-closed 兜底不变）
- M5 current 链分支：`version = os.path.basename(cur)`（入参 `cur`，**不是** `_protocol_root(cur)` 返回值）——I-1 红线，读实现逐字确认
- env 覆盖分支 / legacy 软链兜底分支 / `resolve_hook_root` 脚本上溯兜底 / `.agate-version` 格式解析**均未改**——git diff 逐行确认无越界改动

**C. 断点一 fail-closed 守卫（M1）**：`os.path.islink(agate_home)` 守卫在 `os.makedirs`/`git clone` **之前**——读 `_cmd_install()` 确认守卫位置，拒绝后确实不建任何目录（`repo/` / `vX.Y.Z/`）；三步指引文案三段命令片段（`mv` / `mkdir -p` / `install.sh --versions` 或 `agate-install.py latest`）齐全

**D. 文档面（批 2 M7-M11）**：
- M7「根 `~/.agate/scripts/` 维护语义条目」是否与批 1 实际实现（双 copytree / latest 刷新 / repo 删不断 / 不参与 hook 解析）**一致**（BDD-4 判据 3 交叉锁）——若文档描述的是理想化 B1 而非实际双 copytree 行为，则文档失真
- M9 历史版本节（v0.50.0 / v0.60-0.62 / v0.66-0.68）确实只加指针未改叙事
- M7 生命周期节口径与 README×2 / SETUP 一致（单一真相源）

**E. 范围锁定 + 回归**：`install-offline.py` / Windows 复制模式 / `.state.yaml` schema / agateon 仓库形态未触碰（git diff 确认）；全量 unit+regression 1390 passed / integration 94 passed（主 Agent 已跑，你可抽查 diff 是否有明显回归风险点）

**F. 可维护性**：`agate-install.py` 新增 `_sync_root_scripts` 等函数 + `install.sh` 新增 `--versions` heredoc 块——是否有反模式（重复代码、魔法字符串、错误吞掉）；若提「后续应重构」用标准 DEBT 格式（evidence 必填，登记 `{AGATE_WORKSPACE}/debt/tech-debt.md`）

### 结论口径

- 无 CRITICAL + 4 条 DESIGN_GAP 均属合理自主决策（P7 配对即可）→ `status: approved`（正文逐条列 DESIGN_GAP 裁决 + B/C/D/E/F 核查结论 + 引用锚点）
- 任一 DESIGN_GAP 偏离 P2 意图 / 引入真实场景 bug（尤其 DESIGN_GAP 3）→ `status: rejected` 或 `needs-revision` + 明确修正方向（列 A/B/C 选项）
- DESIGN_GAP 属实但可接受、仅需登记 → 用 DEBT 条目 + `status: approved`

### 上游关联

P2-design.md approved（决策 A1 `_protocol_root` + 决策 B1 副本；M1-M15 落点）。P2-review.md approved（0 阻塞 + 4 项非阻塞澄清项）。P3 18 用例；P4 批 1+2 后全部转绿（主 Agent 已核实：18 tag0032 + 1390 unit/regression + 94 integration + consistency 0 ERROR + shellcheck 干净）。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1 + 批 2 实现说明 + 4 条 DESIGN_GAP，权威——先读）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（决策 A1/B1 原意 + M1-M15 落点 + §4.1/§4.3，比对偏差基准）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review.md（P2 阶段已确认项 + 4 项非阻塞澄清）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 条 BDD 原文 + §3.4 端到端步骤）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P3-test-cases.md（用例断言——判断 DESIGN_GAP 1/3 是否只为迁就 fixture）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（scope / out-of-scope）
- /home/kity/oclab/agateon/agate/assets/review-roles/review.md（你的角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-install.py（批 1 改动对象——读 `_cmd_install` / `_sync_root_scripts` / `_ensure_repo` / `main` 全貌）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate_common.py（`_protocol_root` + `_resolve_version_info` 两处调用 + 未改分支核对）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/install.sh（批 1 `--versions` 分支——DESIGN_GAP 3 核查重点）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（批 2 M7 生命周期节 + M8/M9 历史节指针）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/README.md 与 README.zh-CN.md 与 agate/SETUP.md（批 2 M10/M11）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_agate_version_install.py 与 test_agate_version_resolve.py 与 test_upgrading_lifecycle.py 与 agate/tests/integration/test_version_lifecycle_e2e.py（P3 用例——判断 DESIGN_GAP 是否迁就 fixture）
- 用 `git diff` 看 P4 全部改动（`git -C /home/kity/oclab/agateon/.worktrees/agate-TAG0032 diff HEAD -- agate/ install.sh README.md README.zh-CN.md`）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`；核对用 read/grep/git diff，不改任何文件
- 若要验证 DESIGN_GAP 3 的真实场景，用隔离 HOME（`HOME=$(mktemp -d)`，测完删），绝不动真实 `~/.agate`
- 跑 `check-protocol-consistency.py` 用 worktree 自己的（`agate/scripts/check-protocol-consistency.py --strict-errors-only`）
- bash 外层 `timeout` 30-120s；单步串行；状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-review.md`
- 分阶段落盘：发现逐条追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-review-progress.md`
- frontmatter：用 `agate-md-field-set.py`（先 `--list`）能填的填；不支持的（trace_id/status/agent）用 Write 直接写 frontmatter。Header 成品值：`phase: P4` / `task_id: TAG0032` / `parent: P4-implementation.md` / `trace_id: TAG0032-P4review-20260907` / `agent: review` / `type: review` / `status: draft`（评审后改终值）

### 返回

`File: <P4-review.md 路径>` + `Status: <approved|rejected|needs-revision>` + CRITICAL 数 + 一句话摘要（≤30 字：4 条 DESIGN_GAP 裁决结论）。不返回文件全文。
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
