---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0042
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标
为 **batch4-gate-layer**（关卡层分级）写 TDD 测试：产出 `{AGATE_WORKSPACE}/tasks/TAG0042-config-and-enforcement/P3-test-cases-batch4.md` + 测试代码 `agate/tests/unit/test_gate_layer.py` + `agate/tests/unit/test_check_p8_delivery.py`。测试当前必须**红灯**。

### 约束
- **只写测试，不写实现**（实现是 P4）。
- 本批覆盖 BDD：**BDD-14**（关卡层按提交类型分级，转换表含 `paused_from`）、**BDD-15**（P8 为交付收尾且 `delivery` 必须声明）、**BDD-21**（第 4 批删除发版逻辑前先提供等价 `preset: semver-changelog-tag`）。
- **平台假设扫描须 0 命中**：`check-platform-assumptions.py`。注释里字面量也算命中——运行时拼接（如需临时目录字面量，用 `TMP = "/" + "tmp"`）。
- **写入隔离**：pytest `tmp_path` / 既有 `git_repo` fixture；**绝不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本、`agate/rules/phases.yaml`）。
- **测试先失败**：红灯原因须 B 类（行为/结构未实现）。禁止 SyntaxError / 第三方 import 失败（A 类）。
- **DESIGN_GAP 边界（重要）**：P2-design §11 明确「批 4 的关卡层转换表矩体可能在实现中遇歧义，P4 implementer 应标 `[DESIGN_GAP]`」。⇒ 你的断言须落在 **BDD-14/15/21 的可观察契约**上（转换表**存在且含 `paused_from`**、按提交类型选择关卡集合、gate_p8 对 `delivery` 的拦截行为、preset 等价物可声明），**不要臆造设计未定的具体内部键名**去写脆断言。若某断言依赖设计未定的字段名，在 `P3-test-cases-batch4.md` 中显式标注 `[DESIGN_GAP]` 并说明 P4 需据 BDD 落定契约。

### 上游关联
- P2-design.md §6.1b：batch4 `output` = `agate/rules/phases.yaml`, `agate/scripts/check-gate.py`, `agate/phase-cards/P8-release.md`, `agate/UPGRADING.md`。
- 设计 §4.3：`phases.yaml` 增加按**提交类型**（纯代码 / 纯文档 / 发版）选择的关卡集合 + **转换表**（含 `paused_from`）；`gate_pass_exit` / `next` / `retreat` 语义**不变**；P8 语义改**交付收尾**，`check-gate.py::gate_p8()` 校验 `delivery` 声明，未声明 → 非 0；删发版逻辑的顺序 = 先提供 `preset: semver-changelog-tag` → 再删；缺失时按发版痕迹（CHANGELOG / 版本文件 / `v*` tag）给 WARNING；UPGRADING 写截止版本。
- 设计 §4.5 提及 BDD-21 的 preset 与 `check-changelog.py` / 发版痕迹消费方相关（但发版逻辑的**删除**属批 4 范围；本批测试只验「等价物先就位 + 迁移提示」）。
- BDD-22（横切：每批不回退）无需独立用例，由既有回归套件 + P5 全量承担。

### 输入文件
- `{AGATE_WORKSPACE}/tasks/TAG0042-config-and-enforcement/P1-requirements.md`（BDD-14 / BDD-15 / BDD-21 原文）
- `{AGATE_WORKSPACE}/tasks/TAG0042-config-and-enforcement/P2-design.md`（§4.3、§4.5、§6.1b、§11 DESIGN_GAP 预留、§12 实现完成的标志 第 4 条）
- `{AGATE_WORKSPACE}/tasks/TAG0042-config-and-enforcement/P0-brief.md` + `P0-batch0-record.md`（批 4 前提与风险 R3）
- `{project_root}/AGENTS.md` + `{project_root}/agate/tests/README.md`
- `{agate_root}/assets/execution-roles/test-designer.md`
- 实现对象（读以理解契约，勿改）：
  - `agate/rules/phases.yaml`（现状：无「提交类型→关卡集合」/转换表；`gate_pass_exit` 等语义）
  - `agate/rules/schema/phases.schema.json`（若扩展字段，schema 同构参照）
  - `agate/scripts/check-gate.py`（`gate_p8` 现状，`grep -n '^def gate_p8'` 取行号；`_md_field_get` 等读取口径）
  - `agate/phase-cards/P8-release.md`（P8 语义现状；批 0 已改部分文字）
  - `agate/UPGRADING.md`（迁移兼容章节写法参照）
  - `agate/tests/unit/test_check_gate.py`（gate_p8 既有测试范式 + fixtures 用法）

### 产出规格
- `P3-test-cases-batch4.md`：BDD-14 / BDD-15 / BDD-21 → 用例 1:1 映射；声明 `test_code_dir: agate/tests/unit/`；frontmatter 填 `phase/task_id/parent/trace_id/agent`。
- 测试代码：`agate/tests/unit/test_gate_layer.py`（BDD-14 + BDD-21）+ `agate/tests/unit/test_check_p8_delivery.py`（BDD-15）；测试名引用 BDD 编号；用既有 `run_cli` / `git_repo` / `task_dir` fixtures。
- 每批 `P3-test-cases-batchN.md` 为分包产出；汇总 `P3-test-cases.md` 由主 Agent 承担（勿自行产出汇总文件）。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P3

路径：phase-cards/P3-tdd.md
---
# P3 — TDD 测试设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P3 + 有合规理由（risk=low + 跳过风险已声明）→ 跳过，读 P4 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。**必须执行**。
   该步骤不阻塞流程——脚本的 stderr 输出（含 WARNING）均可忽略，执行完直接继续步骤 1。

**创建型测试清理钩子（强制要求）**：测试含创建资源用例（建团队/条目等）时，须声明清理钩子要求——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；验收环境残留由清理钩子与 post-test 残留检查共同兜底（见 P6 卡）。

1. 派发 test-designer subagent → 产出 P3-test-cases.md + 测试代码目录
   1.1 写 P3-dispatch-context-test-designer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 跑 check-tdd-red.py 确认红灯
3. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P3，不要提前写 P4——phase = 本 commit 的产出阶段
4. git commit -m "wf({Txxx}-P3): {摘要}"（phase=P3，P3 产出含 P3-test-cases.md + 测试代码）
5. P3 commit 完成后进入 P4：**phase 推进 P4 随 P4 产出 commit 一起**（P4-implementation.md 就绪后），不是单独 phase commit

## refactor 任务：回归测试口径

> 适用：P1 frontmatter 声明 `change_type: refactor` 的任务（P2-design.md §3.4）。功能任务（缺省）走上方既有 TDD 口径，不受本节影响。

refactor 任务无新增功能行为可断言，P3 测试设计改用**回归测试口径**：

- **测试设计 = 回归测试口径**：复用/保留既有测试用例，标注每条回归用例覆盖了重构涉及的哪些文件/路径；**不新增功能行为断言**（无新行为可断言）。
- **跳过 check-tdd-red 红灯步骤**：重构无新功能断言，测试套件本就全绿，红灯语义不适用（check-tdd-red 对 refactor 任务会误报 exit 2 绿灯）。回归质量由 P5 全量回归（gate_commands.P5）+ P6 的 `regression.log`（全量回归重跑）兜底。CI backstop 对 refactor 任务同样跳过 check-tdd-red（ci-gate-backstop.py P3 分支 refactor 感知）。
- **P3 gate 不变**：仍为文件存在性检查——refactor 的 P3 产出是 P3-test-cases.md（回归口径声明 + 既有用例覆盖映射），文件存在即满足 gate。

## 如果是重试

确认上一轮失败原因（测试设计不合理 / 未覆盖关键 BDD / 非真红灯）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P3 MAX=2）

## 前置条件

- [ ] P2-design.md files_to_read 完整（测试设计需要知道实现导航）
- [ ] P2-review.md status: approved（P2 不可裁剪）

## 派发

- **角色**：test-designer（`{agate_root}/assets/execution-roles/test-designer.md`）
- **输入**：P2-design.md + P1-requirements.md（BDD 验收条件，每条 `#### BDD-NN` 对应一个测试用例）
- **输出**：P3-test-cases.md + test_code_dir/
- **派发 prompt**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 产出规格

- P3-test-cases.md 必须声明 `test_code_dir: {路径}`
- 每条测试用例对应一条 P1 的 `#### BDD-NN` 验收条件（1:1 映射）
- UI 任务（P2 ui_affected: true）：必须含 Playwright/E2E 用例

## gate 规则

**check-gate.py P3**（hook + 主 Agent 预跑，秒级文件检查）：
- exit 1：P3-test-cases.md 不存在
- exit 2：P3-test-cases.md 存在（TDD 红灯由 check-tdd-red.py 独立确认）

**check-tdd-red.py**（主 Agent 手动确认红灯 + CI backstop P3 兜底）：

```bash
check-tdd-red.py $TASK_DIR
```

- **exit 0**：真红灯（assertion 失败 / 项目内 import 失败 = B类错误）— 测试正确但因实现未写而失败
- **exit 1**：假红灯（SyntaxError / 第三方 import 失败 = A类错误）— 测试代码自身错误
- **exit 2**：绿了 — 实现先于测试，违反 TDD
- **exit 3**：无可用测试运行器

**技术栈无关**：check-tdd-red.py 通过 formatter 将测试输出标准化为 JSON，不直接解析任何框架的输出格式。formatter 在 gate_commands.P3_formatter 中声明（可选）。不提供 formatter 时退化为 exit-code-only（所有红灯 = 可推进）。

**探测链**：`$TEST_RUNNER` 环境变量 → `gate_commands.P3`（P2-design.md 声明）→ `which pytest` → exit 3。`$TEST_RUNNER` 始终优先（退化为 exit-code-only，无 formatter）。

**formatter 选择**：见 `assets/formatters/README.md` 速查表。常用：pytest → `pytest.sh`，vitest → `vitest.sh`，go test → `go-test.sh`，其他 → `generic-exit-only.sh`。

## 按包拆分并行（条件触发，非强制）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P3 可拆分并行：

1. 每个 package 派一个 test-designer subagent
2. 各自写各自的测试文件（不同目录）
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit

拆分判据（本阶段特定）：
- P2 packages > 1 且包间无数据依赖 → 可并行
- 单包或包间有依赖 → 串行（不拆分）
- P2 未声明 packages → 串行

每个 subagent 的 dispatch-context 必须明确其负责的 package 范围（约束节写"只写 {pkg} 目录下的测试"）。

## 推进条件（全部满足才写 phase: P4）

- [ ] check-tdd-red.py exit 0（真红灯确认）
- [ ] P3-test-cases.md 存在且含 test_code_dir
- [ ] 测试代码目录存在
- [ ] UI 任务：Playwright/E2E 用例存在
- [ ] **新增/改动的测试文件通过平台假设扫描**：`python3 {agate_root}/scripts/check-platform-assumptions.py <测试目录>` → **0 命中**
  - 用 `{agate_root}`（协议根占位符）而非裸 `agate/scripts/`：本卡其余处写 `agate/scripts/...` 是**面向 agateon 自身**的惯例，而本条对**任何使用者项目**都成立（`{agate_root}` 由 `agate-resolve.py` 解析）
  - 扫 R1~R5（裸 `python3` / 硬编码 `PATH` / 系统临时目录字面量 / 其它平台假设）。**注释里的字面量也算命中**——writer 最常踩的就是这个
  - 来历（DEBT0048）：P3 曾只查"红灯对不对"，平台假设要到 **P4 全量 pytest** 才由 `check-platform-assumptions.py` 的 bdd-8（全树 0 命中）抓出 ⇒ 多一个"收口小修"回合。**本仓 2026-09-29 两批修复各自又踩了一次**（新测试注释写系统临时目录字面量）
  - 修法：需要该路径字面量时**运行时拼接**（如 `TMP = "/" + "tmp"`），仓库既有惯例
  - ⚠️ **扫描面限定**：`check-platform-assumptions.py` 只扫 `.bats/.bash/.sh/.py` 四种后缀（源码 `L128`）——**TS/JS 测试文件不在扫描面内**。故本条对 **Python/shell 测试项目**成立；**前端项目（Playwright/vitest 等 .ts/.js 用例）跑该自查恒绿，不等于无平台假设**——那类项目的平台无关性需另想办法（已知缺口，见 DEBT0048 记录）。

## 常见错误

1. **测试绿了才 commit**：测试已在 P4 之前通过 → 违反 TDD"测试先于实现"原则。P3 的 gate 要求红灯
2. **忘记声明 test_code_dir**：后续阶段找不到测试代码 → P5 跑 gate_commands 时找不到测试路径
3. **测试覆盖不全**：只为部分 BDD 写了测试 → P6 验收时那些 BDD 没有自动化验证
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。
5. **只覆盖交互路径，忽略前置状态**：测试设计应覆盖 BDD Given 隐含的前置状态，不只覆盖 When/Then 路径（详见 WORKFLOW.md §P3 测试设计指导）

## 下游影响

- P4 用测试驱动实现（implementer 看测试理解预期行为）
- P5 跑同一套测试验证实现正确性（gate_commands.P5）

> 完成 → 读 phase-cards/P4-implementation.md
<!-- AGATE_CARD_END -->

<objective_info>
- 协议版本：agate v0.78.3（`AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`）
- 当前 HEAD：`a2b8fb1`（main，P2 已落）；batch1/2/3 P3 测试已写（未 commit）
- 本机 python：`python3` = `/usr/bin/python3`
- 账本格式：`gate-events.jsonl` append-only + prev_hash 链（**测试须用 tmp_path 副本，勿写真实账本**）
- 本任务改 agate/ 协议本体 ⇒ 触发 SELF-GATE
</objective_info>

> 注：该文件禁止包含 PASS/FAIL 预判——否则被 `check-p6-provenance.py` 审计失败。
