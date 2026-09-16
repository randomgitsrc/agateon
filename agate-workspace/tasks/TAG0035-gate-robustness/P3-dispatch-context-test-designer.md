---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0035
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P3 首次派发（非重试）。

### 目标

为 P1-requirements.md 的 14 条 BDD（4 子批 A/B/C/D）逐条写测试用例（1:1 映射），产出 `P3-test-cases.md` + 测试代码。当前**代码尚未修改**（仍是 P0-brief 描述的现状缺陷行为），测试要按 P2-design.md 已定案的"修复后应有行为"来写断言，使其在当前代码上产生**真红灯**（AssertionError / 项目内 import 失败，不是 SyntaxError）。

### 任务粒度兜底（本节按模板要求显式说明为何不分批）

产出会触达 4 个既有测试文件 + 可能 1 个新增文件（超过模板"产出文件 >3 个须分批"的软阈值），**本次不分批**，理由：
1. 4 个子批虽在 P4 会串行分批实现（P2 `dispatch_plan: serial`），但测试设计阶段不存在"跨批文件冲突"——冲突风险只在 P4 implementer 修改被测代码本身时出现，写测试用例不改动被测代码。
2. 14 条 BDD 共用相近的测试基础设施（`agate/tests/unit/conftest.py` 的 fixture、`run_cli`/`agate_scripts`/`python_exe`/`git_repo` 等既有 helper），单个 test-designer 一次性设计能保证跨文件断言风格、fixture 复用方式一致；拆成 4 次派发反而会导致同一套 fixture 被不同 subagent 各自重新发明。
3. `check-tdd-red.py` 是对整个 `gate_commands.P3` 命令的一次性判定（见下方"红灯预期"说明），分批派发不会减少最终这一次判定所需的信息量，只会增加协调成本。

### 约束

1. **1:1 映射**：14 条 BDD 各自对应至少 1 个测试用例（`#### BDD-NN:` → 测试函数/用例），不得合并多条 BDD 到一个断言里。
2. **红灯预期不是"全部测试都失败"**：BDD-3/BDD-7（回归不变性）、BDD-10/BDD-14（红灯边界）这 4 条 BDD 断言的是"标准场景下行为保持不变"——这些场景在**当前未修改的代码上很可能已经是真的**（如 BDD-10 断言"纯文档、无历史、非回退场景下 `gate_p4` 仍 return 1"，这正是当前代码的现状行为，不是尚待实现的新行为）。这类测试用例现在跑出来是 PASS 也完全正常，不代表你写错了——`check-tdd-red.py` 判定的是**整个 P3 gate_commands 命令的合并输出**是否含真实失败（AssertionError 类），只要 BDD-1/2/4/5/6/8/9/11/12/13 这些"尚待实现的新行为"类用例产生真红灯，整体判定就会是"真红灯"，不需要每一条 BDD 都失败。
3. **各文件落点**（对应 P2-design.md「1.1 改什么」表）：
   - `agate/tests/unit/test_check_gate.py`：新增用例覆盖 BDD-1/2/3（子批A）、BDD-4/7 中 `check-gate.py` 部分（子批B）、BDD-8/9/10（子批C）
   - `agate/tests/unit/test_check_state_transition.py`：新增用例覆盖 BDD-5/7 中 `check-state-transition.py` 部分（子批B）
   - `agate/tests/unit/test_check_judge_verdict.py`：新增用例覆盖 BDD-11/12/13/14（子批D）
   - `pre-commit-gate.py` 的 BDD-6/7 用例：P0-brief/P2-design 已确认该脚本无专属单测文件，覆盖面在 `agate/tests/integration/test_pre_commit_hook.py`；由你判断是在该集成测试文件里加用例，还是按 P2-design 提示新增 `agate/tests/regression/test_pre_commit_gate_phase_num.py`（两种做法均可，选一种并在 P3-test-cases.md 里说明理由，不要两处都写导致重复）
4. **测试断言的是"修复后行为"，不是"实现细节"**：如 BDD-6 的断言应该是"stderr 出现某种可观测提示"，不要断言具体改用了哪个正则变量名（P2-design 的 `_P_OUTPUT_ANY_RE` 等是实现细节，测试不应耦合到变量名本身，只耦合到可观测的 stderr 文本/退出码）。
5. **复用既有测试基础设施**：`test_check_gate.py` 已有 `_run_gate` helper + `git_repo`/`agate_scripts`/`python_exe`/`run_cli` fixture（见下方客观查证信息），子批A/B/C的用例应复用这些 helper，不要重新发明一套调用方式。子批 C（BDD-8/9/10）需要构造"跨多 commit"/"回退后修复"场景，需要用到 `git_repo` fixture 做真实多 commit 操作（`git commit`），参考文件里 G4 系列用例的既有写法。
6. **`_gate_p4_has_prior_code_commit` 的历史扫描依赖 commit message 含 `wf(<task_id>-P4` 标签**（P2-design 3.3 节）：BDD-8/9 的测试用例构造历史 commit 时，commit message 必须带这个标签格式（如 `wf(TEST0001-P4): ...`），否则测试会得到与预期相反的结果——这是测试构造的关键细节，不是可选项。
7. **test_code_dir 声明**：P3-test-cases.md frontmatter 或正文声明 `test_code_dir:`，本任务涉及多个既有目录（`agate/tests/unit/`、可能的 `agate/tests/regression/`、`agate/tests/integration/`），按现有惯例列出实际改动到的文件路径清单即可，不要求单一目录。

### 上游关联

- P1-requirements.md（已 approved，14 条 BDD 的验证命令是测试设计的直接依据——每条 BDD 正文已给出"验证："这一行，虽然多数写的是"新增测试构造...场景"这类概述性描述而非可直接复制的断言代码，需要你据此设计具体测试）
- P2-design.md（已 approved，含逐子批技术方案 §3.1-3.4——测试断言的"修复后应有行为"以此为准；§1.1"改什么"表给出各文件/函数改动落点，测试应针对这些落点设计）
- P2-review.md（评审记录，含对子批C/D红灯边界的独立验证，供你理解 BDD-10/14 的边界条件应如何精确构造）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P1-requirements.md（14 条 BDD 原文）
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P2-design.md（技术方案，尤其 §1.1 改什么表 + §3 逐子批详述）
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P2-review.md（评审记录，红灯边界核实细节）
- agate/tests/unit/test_check_gate.py（既有测试写法/fixture 参照，重点看 `_run_gate` helper 与 G4 系列的 `git_repo` 用法）
- agate/tests/unit/test_check_state_transition.py（既有测试写法参照）
- agate/tests/unit/test_check_judge_verdict.py（既有测试写法参照）
- agate/tests/integration/test_pre_commit_hook.py（pre-commit-gate.py 现有覆盖面参照）
- agate/tests/unit/conftest.py（共享 fixture 定义，写新用例前先看有没有现成 fixture 可用）
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
- 环境：worktree 分支 feat/TAG0035-gate-robustness；python3 3.12.3 / pyyaml / pytest 9.0.3
- `agate-capture-env-baseline.py` 已跑（非阻塞提示："命令无 formatter，无法提取 fail-list"，按卡片说明可忽略，已按流程执行）
- `test_check_gate.py` 现状：190 个既有 `test_` 函数，文件头注释含批次沿革说明，已确认存在 `_run_gate(agate_scripts, python_exe, run_cli, phase, task_arg, cwd=None, env=None, old_phase=None)` helper（G_RETREAT 系列已用它测试回退检测的第 3 参数 `old_phase`，子批 B 的 BDD-4 可直接复用这个 helper 传 `old_phase`）
- gate_commands.P3（P2-design.md 已固化）：`python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_state_transition.py agate/tests/unit/test_check_judge_verdict.py agate/tests/integration/test_pre_commit_hook.py -v`——你新增的测试文件/用例必须落在这四个文件内（或按约束2 新增 regression 文件后，需告知主 Agent 是否要追加进 gate_commands.P3，P2 卡片允许"P4 阶段按新增测试文件路径追加"）
</objective_info>
