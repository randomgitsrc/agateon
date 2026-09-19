---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0036
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P3 首次派发，**按包拆分并行的 docs 半边**（另一半 script 由并行的 test-designer-script 负责，二者写不同文件）。

### 目标

为 P1 中**文档类 / 字段链路 / 守护类** BDD 写**字面标记断言测试**，产出 `agate/tests/unit/test_mvwu_protocol_docs.py`，覆盖 **BDD-1、2、3、5、6、7、8、9、10、11、12、59 至 BDD-71**（1:1）；并产出**配套映射** `P3-test-cases-docs.md`（BDD-NN → 用例名，或注明由 P5 gate_commands key 承担 / 由 P6 证据承担）。

### 约束

1. **TDD 红灯必须是真红灯（B 类）**：测试在当前代码（`agate/scripts/check-mvwu.py` 尚不存在、文档尚未改）上必须因**断言失败 / 项目内缺失**而红，不得因 SyntaxError、第三方 import 失败、fixture 写错而红（A 类=假红灯）。可运行性自检：用 `python3 -m pytest <你的测试文件> -q -x --co` 先确认可收集，再跑一次确认失败原因均为断言/文件缺失。
2. **平台无关（`AGENTS.md`「测试约定」硬约束）**：不用 `/tmp` 字面量（用 `tmp_path`）、不裸 `python3`（子进程解释器一律 `sys.executable`）、不假设 POSIX symlink 语义（符号链接用例须 `try/except (OSError, NotImplementedError)` 后 `pytest.skip`）、显式 `encoding="utf-8"`、路径用 `pathlib`；**每个测试文件第 1 个用例加 `@pytest.mark.windows_smoke`**（`pyproject.toml` 已注册该 marker）。
3. **隔离（DEBT0040 教训）**：所有需要 git 仓库/任务目录的用例一律在 `tmp_path` 里 `git init -q` 建临时仓库（`git config user.name/user.email`、`git branch -M main`、显式提交），**不得写仓库内真实账本/证据/任务目录**；用例前后不改 worktree 的 `git status`。git 命令统一 `subprocess.run([...], cwd=..., check=True)` + 超时。
4. **测试命名引用 BDD 编号**（如 `test_bdd_22_unsafe_batch_id_printed_escaped`）；带多个输入的等价类 BDD 用 `pytest.mark.parametrize`（同一 BDD 编号共享）。**每条 BDD-NN 至少一个用例，1:1 映射**；P1 的 `P1-requirements.md` 「口径 A-H」是断言的权威来源——**逐字断言其期望值**，不要自己发明契约。
5. **不得写任何实现代码**：不创建 `agate/scripts/check-mvwu.py`，不改 `agate/` 下除你负责的测试文件外任何文件；不 git add/commit。
6. **不得为让测试变红而故意写错测试**；也不得为通过而放宽断言。BDD 中含"待 P4 决定"的文字契约以 P1/P2 已锁定口径为准；遇到 P1/P2 歧义写入 `P3-progress.md` 并在返回里报告（不擅自解释）。
7. 收口：`python3 agate/scripts/check-frontmatter.py` 不适用于测试文件；测试文件需 `~/.venvs/agate-dev/bin/ruff check <你的测试文件>` 通过（0 error）。
8. **只写你的文件**：`agate/tests/unit/test_mvwu_protocol_docs.py`（唯一测试代码文件）+ `{AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P3-test-cases-docs.md`（含简短 frontmatter：phase=P3 / task_id=TAG0036 / parent=P2-design.md / trace_id=TAG0036-P3-20260919 / type=test-design / created=2026-09-19 / status=draft / agent=test-designer，用 `agate-md-field-set.py`，不接受的键 Edit 单行）+ `P3-progress.md`（追加，`>>`）。script 半边的文件是 `agate/tests/unit/test_check_mvwu.py` 与主映射 `P3-test-cases.md`——**不要碰**。
9. **文档类断言的形式**：读 `agate/` 下目标文件（`phase-cards/P2-design.md`、`assets/execution-roles/architect.md`、`phase-cards/P4-implementation.md`、`assets/templates/task-files.md`、`role-system.md`、`adr.md`、`phase-cards/P7-consistency.md`、`CONTEXT.md`、`scripts/README.md`、`tests/README.md`、`CHANGELOG.md`、`agate-workspace/debt/tech-debt.md` 等，路径以 P1/P2 为准）→ 用 **P1 已列的"字面标记"** 断言存在（`in` / 正则，"字面：…"逐字使用）；负向断言（无"已生效"字样、`agate/` 内 `tests_filter: "…python3…"` 0 命中、既有四条硬规则逐字不变、CONTEXT.md 既有 29 行不变——用 `git show HEAD:<path>` 取基线对比）按 P1 措辞。仓库根用 `Path(__file__).resolve().parents[3]`（`agate/tests/unit/x.py` → 仓库根）；只读，不写仓库。
10. **必须覆盖的守护类用例（P2 §13）**：
   - **B1 守护**：把 `agate/tests/integration/test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts` 在映射表中登记为"P4 前应已绿的守护用例"（无需新增 py 用例；可加一个断言 `GATE_SCRIPT_EXEMPT` 含 `check-mvwu.py` 的用例作为 M18 落地的红灯——当前应红）；
   - **B2 守护**：`agate-read-p5-commands.py`（env `P2_DESIGN` = 本任务 `P2-design.md` 路径；解释器 `sys.executable`，脚本走仓库内 `agate/scripts/` 版本）读回的每条 cmd `shlex.split` 不抛 `ValueError`、末 token 无引号残留；**注意此用例现即为绿（P2 已修），属回归守护**，需在映射表标注"回归守护（当前已绿）"；若 `P2-design.md` 在 tmp 外的真实任务目录被读取，仅只读；
   - **B3 守护**：把 `P5_history_untouched` 读回命令在 `tmp_path` 临时 git 仓库（含 `TAG0010-x`/`TAG0011-x`/`TAG0031-x`/`TAG0032-x`/`TAG0036-x`；`git init -q` + `git branch -M main`）执行：删除（含同时删两个）/ 修改 / 新增历史目录 → rc=1；改 `TAG0036`/`TAG0037` → rc=0；断言 `shlex.split` 的 pathspec 为字面 `agate-workspace/tasks/TAG00[0-2]*` / `agate-workspace/tasks/TAG003[0-5]*`。同为回归守护（当前已绿），命令的 `main...HEAD` 三点写法需与读回值一致（用读回值直接执行，把 `--` 前的 revspec 保留）；
   - **同源对拍**：同一 P2 样例经 `agate-md-field-get.py dispatch_plan`（env `FILE`）与 `agate_common.split_frontmatter` 得同一 JSON——**注意**：`agate_common` 是仓库脚本，import 方式参照既有测试（`sys.path.insert(0, str(<repo>/agate/scripts))`）；
   - BDD-1/2/3：`tests_filter` 经 `agate-md-field-get.py dispatch_plan` 原样透传（含空格 / `|` / 转义引号的值）、既有 P2 gate 不因未知键拒绝（用 `check-gate.py P2` 在 `tmp_path` 任务目录上对带 `tests_filter` 与不带的两份 frontmatter 比对退出码一致；`check-gate.py` 走仓库 `agate/scripts/` 版本，**只读运行**）。
11. 对 P1 里含"字面：…"的 BDD，字面串**逐字**取自 `P1-requirements.md` 该 BDD 正文，不得改写。**P1-requirements.md 是权威**；P1 若有"（P3 落断言时明确）"类留白，由你在测试里选定并在 `P3-test-cases-docs.md` 记录选择及理由。

### 上游关联

- `P1-requirements.md`（BDD-1..3/5..12/59..71 及各"字面标记"）；`P2-design.md`（§0.1 改什么表 M1-M18 = 文档落点与插入位置 / §3 ⑤ 组落点 / §7 gate_commands / §13 给 P3 的提示 / §14 修订记录）；`P0-brief.md`

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P1-requirements.md
- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P2-design.md
- {AGATE_WORKSPACE}/tasks/TAG0036-mvwu-pilot/P0-brief.md
- agate/tests/conftest.py、agate/tests/integration/test_protocol_alignment_review.py、agate/tests/unit/test_agate_md_field_get.py（风格参照，仅读）
- agate/scripts/agate-read-p5-commands.py、agate/scripts/agate-md-field-get.py、agate/scripts/agate_common.py（仅读）
- AGENTS.md「测试约定」
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
- 目标文档现状（P4 前）：`agate/` 内 `tests_filter` / `P4-evidence` / `MVWU` / `check-mvwu` 命中 0；`CONTEXT.md` 术语表 29 行（含表头）；`GATE_SCRIPT_EXEMPT` 现含 2 条；本地 `main` = `efb113b`。
- `agate/tests/unit/test_mvwu_protocol_docs.py` 不存在；基线 `count-tests.sh` = 1668；pytest 9.0.3 / python 3.12.3；`windows_smoke` marker 已注册；ruff 用 `~/.venvs/agate-dev/bin/ruff`。
- 有些"回归守护"用例（B2/B3）当前即绿——属预期；文档类与 M18 用例当前应红。
</objective_info>
