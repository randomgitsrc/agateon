---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0051
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的**强制指令**，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

产出 `{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P3-test-cases.md` + 测试代码，为 TAG0051
（任务与发布解耦）建立 **TDD 红灯基线**：

- 每条 P1 的 `#### BDD-NN`（**共 23 条**）转成一个测试用例（**1:1 映射**，测试名引用 BDD 编号）；
- `test_code_dir` 声明为 **`agate/tests/unit/`**（本仓惯例——见 TAG0042/TAG0050 的 P3 产出；
  **不是**角色文件里写的 `P3-test-code/`，那是通用默认值）；
- 测试**当前必须全部失败**（红灯），失败原因须是「被测实现未写」而非「测试自身有错」。

### ⚠️ 本次最重要的两条硬约束（不遵守会让 P3 gate 直接红）

**① 红灯必须是「B 类」（断言失败），不能是「A 类」（编译/导入错误）**
`check-tdd-red.py` 的判定（实测源码 :110-125）：命令 exit 1 且**原始输出命中
`Traceback|SyntaxError|ImportError|ModuleNotFoundError`** ⇒ 判 **A 类（假红灯）→ exit 1**（gate 不过）。
⇒ **测试里不要 `import` 尚不存在的模块/符号**。要测尚未存在的 CLI 子命令 / 未实现的函数时，
**用 `subprocess` 调脚本**（断言其返回码/输出），而不是 `from agate.scripts.agate_release import gate`。
（`agate-release.py` 文件名带 `-` 本就无法直接 import，天然只能走 subprocess——请沿用这个形态。）

**② 平台假设扫描必须 0 命中**（P3 推进硬条件）
`python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/` → **0 命中**。
- ⚠️ **注释里的字面量同样计命中**（R4 = 系统临时目录字面量，R1 = 裸 `python3`，R2 = 硬编码 `PATH`）。
  需要该路径时**运行时拼接**（仓库既有惯例：`TMP = "/" + "tmp"`）。
- 调 Python 解释器请用 conftest 既有 fixture（本仓 `agate/tests/conftest.py` 有 `python_exe` 等），
  **不要**在命令串里写裸 `python3`。

### 测试映射（每条 BDD 的落点，源自 `P2-design.md` §9）

| BDD | 测什么（载体） |
|-----|---------------|
| 1 | **P8/READY 语料面 tag 条件零残留**：对设计列出的**6 个文件**（`state-machine.md` / `phase-cards/P8-release.md` / `rules/state-transitions.md` / `rules/phases.yaml` / `dispatch-protocol.md` / `assets/execution-roles/implementer.md`）做检索断言；**显式排除** `UPGRADING.md` 历史章节 / `CHANGELOG.md` / `archived/**`（判据须可二值） |
| 2 / 3 | `check-gate.py P8` 对**无 tag / 无 version 变更**的 fixture **不再告警**、exit 2（构造 `tmp_path` 任务夹具） |
| 4 / 5 | `check-changelog.py <task_id>` 在 `[Unreleased]` **含/不含** task_id 时 exit 0/1（**回归锁**，载体已存在） |
| 6 / 7 | `bump_type` 缺 → exit 1；有 → 放行 |
| 8 | `release.yml` 的 `on:` 含 `workflow_dispatch` |
| 9 / 10 | 新发布门（`agate-release.py gate`）在 **CI 非 success / PR 口径绿但 push 口径红** 时非 0 |
| 11 | 门校验 **tag↔提交一致**（badge / CHANGELOG 版本节） |
| 12 | 门跑 `check-protocol-consistency.py` **0 ERROR** |
| 13 | 门校验 **roadmap 关联 RM 已 done** |
| 14 / 15 | `AGENTS.md`（与 `agate/git-integration.md`）tag 时点**全文一致** + 含失败处置 |
| 16 / 17 | `delivery.method` 枚举：合法 → exit 2；枚举外非空 → exit 1（**需 level-2 fixture**，见下） |
| 18 | `state-machine.md` 显式发布授权转移 + **不引入**第二套阻塞语义 |
| 19 | 无悬空预设提示 + consistency 0 ERROR |
| 20 | **legacy 行为不变**：R6 双向差分（`docs/design-notes/r6-differential.sh`；**只在 `/tmp/opencode` 副本上跑**） |
| 21 | **obligations 语义一致**：`OBL-P8-*` 十四条 statement 无 version/tag 期残留 + `OBL-P8-04` 仍为 `M` 且含 `method_enum` |
| 22 | 改 `agate/` 的 commit 含 `self-gate-review:` 留痕（可按既有同类用例形态） |
| 23 | **发布门三落点穷尽分支**（落 `check-*.py` ⇒ SG.6 通过；落 `agate-*.py` ⇒ SG.6/CHECK9 零触发；落 `release.yml` 内步 ⇒ 无新增 scripts 文件） |

### 必须构造的 fixture（P2 评审列出的测试缺口 #2）

**BDD-16/17 需要「非 legacy **且** `task_level ≥ 2`」的任务夹具**——本仓当前唯一非 legacy 任务是 TAG0051
自身（level **1**，快照无 `method_enum` ⇒ 枚举钩子 no-op），故**不建 level-2 夹具则红灯不成立**。
请在 `tmp_path` 下按 `agate/rules/task-data/{LEVELS.yaml, level-1.yaml, level-2.yaml}` 的格式构造最小
level-2 任务夹具（P4 会新增 `level-2.yaml`；你的夹具可先按设计 §决策 4 的 `delivery.method_enum` 形态写，
红灯即因该文件/钩子尚未存在）。

### 复评析出的 4 条非阻塞项（**须在本阶段测试设计中体现**）

- **NB-6**：BDD-21 的机械断言若是「statement 不含 5 个精确 token」的**黑名单**，可被
  `「CHANGELOG 写入版本号」`/`「tag 存在性」`/`「执行 bump」` 等绕过。请**提高判别力**：
  优先「statement 与 anchor 节文本的关键词交集非空」这类随锚点变化的判据；若仍用黑名单，须补更宽的根词
  （`版本号`/`tag`/`bump`）**并先全量扫 `OBL-P8-*` 十四条确认零误伤**再启用。
- **NB-7**：`check-changelog.py` **只在 `pre-commit-gate.py:1086`（pre-commit 阶段）**被调用，
  **`check-gate.py` 内无任何调用**（实测 grep 无命中）⇒ BDD-4/5 的测试应**直接测
  `check-changelog.py <task_id>`**，不要写成「跑 `check-gate.py P8` 期望 CHANGELOG 告警」。
- **NB-8**：新增 wrapper `docs/design-notes/r6-differential-prepare.sh`（P4 写）的**健壮性**须有测试：
  `--dst` 为空 / 相对路径 / 位于 `--src` 之内 ⇒ **拒绝**（不得 `rm -rf` 到源或真仓）。
- **NB-9**：批级 smoke——首批 `ready-no-tag` 的 `tests_filter` 是
  `python -m pytest agate/tests/unit/test_tag0051_p8_gate.py -q`，请让该文件的用例可**单独跑绿/红**。

### 约束

- **只写测试代码 + `P3-test-cases.md`**；**不要改任何协议/脚本/CI 文件**（那是 P4 的事）。
  测试可以是「断言当前**尚未发生**的改动」，但**不得**自己动手改被断言的产物。
- **不得写仓库内已提交的文件**（尤其 `gate-events.jsonl` 账本——写坏会污染他人任务）；一律用 `tmp_path`。
- **`/tmp/opencode` 只用于 R6 差分副本**；测试代码里不得出现系统临时目录**字面量**（平台假设扫描会命中）。
- progress **追加**到 `P3-progress-test-designer.md`。

### 客观查证信息（主 Agent 已核实，可引用）

- 协议 `AGATE_ROOT=/home/kity/.agate/v0.81.0/agate`；本仓无 `.agate-version`。
- `check-tdd-red.py` 的探测链：`$TEST_RUNNER` → `gate_commands.P3` → `which pytest` → exit 3；
  **超时（exit 124）会被当作红灯放行**——这不是你要利用的路径，请让红灯是**真断言失败**。
- P2 的 `gate_commands`（**已固化，勿改**）：`P3`/`P5`/`P5_consistency`/`P5_count`/`P5_ruff`/`P5_obligations`/
  `P5_sg6`/`P5_r6` + 两个 `_timeout_seconds` meta 键；全合法、无 `&&`。
- 既有同类测试可参考：`agate/tests/unit/test_tag0050_obligations_enforcement.py`（anchor/M 断言形态）、
  `test_release_workflow.py`（`release.yml` 解析形态）、`test_check_changelog.py`、
  `test_agate_release.py`、`test_check_gate*.py`。
- 基线：全量 pytest **2920 passed / 2 skipped / 1 failed**（`test_bdd_43` = 本机 opencode CLI 环境漂移，
  与本任务无关）；consistency **0 ERROR**（432 WARNING）。
- 你的新测试**加进套件后，全量基线会变红**（这是预期的 TDD 状态，P4 实现后转绿）。

### 产出与自检（强制）

- 产出：`P3-test-cases.md`（frontmatter 含 `test_code_dir: agate/tests/unit/`）+ 测试文件（**可多个**，
  建议按落点分文件，如 `test_tag0051_p8_gate.py` / `test_tag0051_release_gate.py` / `test_tag0051_docs_consistency.py`
  / `test_tag0051_obligations_sync.py` / `test_tag0051_delivery_contract.py` 等，与 P2 的批 `tests_filter` 对齐）
- 自检（**必做，逐项给实测输出**）：
  ① `python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/` → **0 命中**；
  ② 自跑你的新测试，**逐个确认红灯原因**是「被测实现未写/断言不成立」，**不是** A 类（SyntaxError/ImportError）；
  ③ 每条 BDD 有对应用例（`grep -c '^#### BDD-' P1-requirements.md` = 23 ⇒ 用例 ≥23 且映射可追溯）
- 返回：路径 + 「N 个测试用例，当前全部红灯」

### 返回给我（重要）

只返回**两行**：① 产出文件路径 ② 一句话摘要（≤30 字：`N 个测试用例，当前全部红灯`）。
**绝对不要**返回文件全文。
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
- **跳过 check-tdd-red 红灯步骤**：重构无新功能断言，测试套件本就全绿，红灯语义不适用（check-tdd-red 对 refactor 任务会误报 exit 2 绿灯）。回归质量由 P5 全量回归（gate_commands.P5）+ P6 的 `regression.log`（全量回归重跑）兜底。CI 兜底（`agate-ci-verify.py`）逐提交回放 pre-commit 与 commit-msg hook 判定，不单独执行 TDD 红灯检查。
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
  - 扫 R1~R6（裸 `python3` / 硬编码 `PATH` / 系统临时目录字面量 / 其它平台假设 / **`subprocess` 文本模式缺 `encoding=`**）。**注释里的字面量也算命中**——writer 最常踩的就是这个
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
