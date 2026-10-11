---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0051
role: test-designer
retry: 1
---

<dispatch_guide>
> ⚠️ 这是 **P3 产出的**修复轮**（retry 1）**，是本次任务的**强制指令**。
> 首轮目标/约束见 `P3-dispatch-context-test-designer.md`（**其余约束继续有效**，本文件不重复）。

### 为什么要修（P4 实现完成后暴露的 P3 质量缺陷）

P4 的 4 个 implementer 完成后，8 个新测试文件跑出 **8 failed / 28 passed**。逐条定位后：
**其中 5 条不是实现缺口，而是 P3 测试代码自身的缺陷**——它们"红"的原因是**测试写错**，
不是"被测模块未实现"。这正是测试设计师角色文件警告的那个失败模式
（「确认每个红灯的失败原因都是"被测模块未实现"，而非"断言与测试数据矛盾"」）。

**P3 当时的自检结论「红灯全部 B 类」在字面上成立**（确实是断言失败、无 ImportError/SyntaxError），
但**掩盖了「B 类失败中混着测试自身的 bug」**——`check-tdd-red.py` 只看失败类别，看不出这一层。

### 要修的两处（**只改这两处，其余一律不动**）

**① `agate/tests/unit/test_tag0051_obligations_sync.py` —— `_obligations()` 解析口径错**

现状（约 `:28-30`）：

```python
def _obligations():
    data = yaml.safe_load(_OBLIGATIONS.read_text(encoding="utf-8"))
    return [o for o in data if isinstance(o, dict) and str(o.get("id", "")).startswith("OBL-P8-")]
```

**问题**：`agate/rules/obligations.yaml` 顶层是**字典**（`baseline:` / `obligations:` / …），
**不是列表** ⇒ 遍历 dict 得到的是**字符串键**，`isinstance(o, dict)` 恒假 ⇒ **永远返回 0 条**
（实测报错：`OBL-P8 条目应为 14 条，实际 0`）。而 `check-obligations.py` 能正常解析出 14 条
（实测 `M 类占比: 56/121`），说明**是测试侧的解析写错**。

**修法**：按 `check-obligations.py` 的同源口径取列表（读该脚本确认键名，例如 `data["obligations"]`），
**不要**用 `isinstance` 猜。修完 `test_bdd_21_*` 三条应能真正验到实现（Impl-B 已把
`OBL-P8-04` 重挂为 `delivery.method 枚举校验`、`disposition: M`、`enforced_at.function == "gate_p8"`）。

**② `agate/tests/unit/test_release_gate.py` —— 常量取自错误的 helper**

现状（约 `:34` + `:123`）：`import helpers_tag_repo as H` … `"prev_hash": H.GENESIS_HASH,`

**问题**：`GENESIS_HASH` **不在** `agate/tests/helpers_tag_repo.py`（实测该模块导出表里没有它），
它在 **`agate/tests/helpers_tag0050.py`**（`GENESIS_HASH = hashlib.sha256(b"").hexdigest()`）。
⇒ 夹具构造期即 `AttributeError`，BDD-9/10/12/13 **根本没跑起来**（假红灯）。

**修法**：与本任务另一测试文件**同源**的既有写法——`test_tag0051_p8_gate.py` 用的是
`import helpers_tag0050 as H5` + `H5.GENESIS_HASH`。照它改（可同时保留 `helpers_tag_repo` 的其它用法，
形如 `import helpers_tag_repo as H` + `import helpers_tag0050 as H5`）。**只改这一处引用，不动任何断言**。

### 修完必须自证（P3 的原始门槛在这里重跑）

1. **每个红灯的失败原因重新逐条确认**：
   - 修后跑 `python3 -m pytest agate/tests/unit/test_tag0051_p8_gate.py agate/tests/unit/test_tag0051_docs_consistency.py agate/tests/unit/test_tag0051_state_machine.py agate/tests/unit/test_tag0051_delivery_contract.py agate/tests/unit/test_tag0051_obligations_sync.py agate/tests/unit/test_tag0051_r6_harness.py agate/tests/unit/test_release_gate.py agate/tests/unit/test_tag0051_self_gate.py -q`
   - **期望**：只剩 **1 条红** —— `test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review`
     （它按设计**在 P4 提交前必然红**：BDD-22 要求"本任务改动 `agate/` 的提交带 `self-gate-review:` 留痕"，
     而该提交尚未发生）。**其余必须全绿**。
   - 若仍有红：**逐条判定是"测试 bug"还是"实现缺口"**，并在返回里分别说明（**不得**含糊）。
2. **同类扫描**：8 个文件里还有没有**同一类**缺陷（引用不存在的 helper 常量/函数、路径假设错、
   YAML 解析口径假设错）？主 Agent 已扫过 `H.*`/`H5.*` 的全部用法（仅上述 1 处），
   你请**再扫一遍**其它形态（`Path(...).parents[N]` 层级是否指对、`import` 的 helper 是否真导出该名字）。
3. `python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/` → **0 命中**
   （`{agate_root}` = `/home/kity/.agate/v0.81.0/agate`）。

### 约束（硬）

- **只改上述 2 个文件、且只改点名的位置**；**不得**改任何实现的代码、不得改其它测试、
  **不得**为让测试变绿而弱化/删除任何断言（这是修复**测试自身的 bug**，不是修实现）。
- **不得**改 P1/P2 基线文件。
- 状态标记二值 `[PROD_NOT_TOUCHED]`；bash 设超时。
- progress **追加**到 `P3-progress-test-designer.md`。

### 返回给我（重要）

只返回**三行**：① 改动文件路径 ② 一句话摘要（**须含修后 8 文件的 failed/passed 实测数字 + 剩余红灯的逐条归因**）
③ `files_modified: [...]`。**绝对不要**返回文件全文。
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
