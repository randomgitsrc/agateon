---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: test-designer
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

产出 `P3-test-cases.md` + 测试代码（TDD 红灯）：为 TAG0032 的 14 条 BDD 各写 1:1 对应测试用例，**当前全部红灯**（实现未写 → 断言失败 / import 失败 = B 类红灯）。

本任务**非 UI**（P2 `ui_affected: false`），无 Playwright/E2E；测试落在 pytest（unit + integration）。测试代码直接写进 **worktree 既有测试树**（P2-design M12-M15 已指定文件），不新建独立 `P3-test-code/` 目录——因为这是对既有脚本的改造，测试须与既有用例同目录同 runner。`P3-test-cases.md` 的 `test_code_dir:` 声明为 `agate/tests/`（既有测试树）。

### 测试用例设计（按 P2-design M12-M15 落点，1:1 映射 14 条 BDD）

| BDD | 测试文件 | 用例要点（P2 M 编号） |
|-----|----------|----------------------|
| BDD-1 | `agate/tests/unit/test_agate_version_install.py` | legacy 软链布局 → `agate-install.py` exit≠0 + 软链目标内无新建 `repo/` / `vX.Y.Z/`（M1/M12）。`os.symlink` 失败 → `pytest.skip`（同既有 `test_bdd_30_legacy_symlink_direct_root` 模式，见 test_agate_version_resolve.py:181-205） |
| BDD-2 | 同上 | 拒绝 stderr 含三段同粒度命令片段：`mv ~/.agate ~/.agate.bak` / `mkdir -p ~/.agate` / `install.sh --versions`（或带 `latest`/`v<X.Y.Z>` 的 `agate-install.py`）——逐段 grep 断言，三者缺一即用例 FAIL（M1/§4.1） |
| BDD-3 | 同上 | `~/.agate` 不存在 或 普通目录 → `agate-install.py v<X.Y.Z>`（`AGATE_REPO_URL` 注入本地源）exit 0 + `~/.agate/v<X.Y.Z>/` 建立（M1 守卫不误伤，`os.path.islink` 对普通目录/不存在为 False） |
| BDD-4 | 同上 | 装 latest 后：① `~/.agate/scripts/agate-install.py` 存在 + `--help` exit 0（判据 1）；② 重跑 `agate-install.py latest` 后根 `~/.agate/scripts/` 副本随 current 刷新（判据 2，决策 B1 副本语义单测锁）；③ 用例断言的维护语义与 UPGRADING「版本管理生命周期」节一致（判据 3，与 BDD-11 交叉——可先断言 UPGRADING 含该条目文本）（M2/M12） |
| BDD-5 | 同上 | 隔离 HOME + `AGATE_REPO_URL` 指向本地**元仓库形态** fixture repo → `install.sh --versions` → 产出 `repo/` + `vX.Y.Z/` + `current`/`latest` 指针 + 根 `scripts/`，且源树（worktree）无新建 `repo/` / `vX.Y.Z/`（M6/M12）。**注意 P2-review 非阻塞项 2**：`install.sh --versions` 须读 `AGATE_REPO_URL`（P4 会落地 `git clone "${AGATE_REPO_URL:-<default>}"`），测试按此假设写——设置 `AGATE_REPO_URL` env 后跑 |
| BDD-6 | `agate/tests/unit/test_agate_version_resolve.py` | 新 fixture `_make_home_meta`（建 `~/.agate/vX/agate/scripts/`，**不建** `vX/scripts/`）→ 项目 `.agate-version` = `agate: vX` → `agate-resolve.py` → `AGATE_ROOT` 结尾 `/vX/agate` + `AGATE_VERSION == vX`（版本号不回归，I-1）（M4/M13） |
| BDD-7 | 同上 | 新 fixture `_make_home_rootproto`（`vX/scripts/` 直建）→ `agate-resolve.py` → `AGATE_ROOT` 结尾 `/vX`（不进 `/agate` 分支）**且** `AGATE_VERSION == vX`（P2-review 建议对称断言）（M3 探测序 1，纯增量红线，M13） |
| BDD-8 | `agate/tests/unit/test_hook_resolve_entry.py` | meta fixture → `resolve-entry.py pre-commit`（钉版项目目录内）→ exit 0 + 解析出的 gate 路径 `<root>/scripts/pre-commit-gate.py`（root = `vX/agate`）存在并被 exec（stub gate 打 marker，同既有 `_STUB_GATE` 模式）（M14） |
| BDD-9 | （无独立用例，回归锁）| P3-test-cases.md 说明：BDD-9 由 P5 全量 pytest（`gate_commands.P5`，含本批新增双 fixture 常驻用例）承接，不单独写用例 |
| BDD-10 | `agate/tests/unit/`（文档面用例，新增 `test_upgrading_lifecycle.py` 或并入既有文档测试）| `agate/UPGRADING.md` 「版本管理生命周期」节：legacy 更新 = `git pull`（含 hook 判定口径）、版本布局更新 = `agate-install latest` + 幂等语句——文本检索断言（M7） |
| BDD-11 | 同上 | 「版本管理生命周期」节存在 + 四动作（安装/迁移/更新/回退）各有命令/步骤 + hook 重装时机口径 + 根 `~/.agate/scripts/` 维护语义条目（判据 3，与 BDD-4 判据 3 交叉）（M7） |
| BDD-12 | 同上 | §4.3 的 4 条 checklist 逐条：v0.50.0 表格「根含 scripts/」行 + 「升级 = agate-install.py」行有指针 / v0.60-0.62 vs v0.66-0.68 由生命周期节统一口径 / README×2 + SETUP 口径一致——文本检索断言每条命中「已收敛」或「历史叙事保留 + 指针」；附加回归项 `check-protocol-consistency.py --strict-errors-only` EXIT 0（M7-M11） |
| BDD-13 | `agate/tests/integration/test_version_lifecycle_e2e.py`（新增）| 隔离 HOME + 本地构造**元仓库形态** git repo（`agate/` 子目录 + `vX.Y.Z` tag，经 `AGATE_REPO_URL` 注入，helper `_tag_meta_upstream`）→ `install.sh --versions` → 钉 `.agate-version` → `resolve-entry.py pre-commit`（exit 0 + marker）→ 再 `agate-install.py latest`（幂等：`~/.agate/vX/` 数量不变、指针幂等）。逐步 exit 断言（M15）。真实 GitHub clone 增强 → 无网 `pytest.skip`（I-6） |
| BDD-14 | 同上 | 同 BDD-13 fixture 全链路后：worktree `git status --porcelain` 无新增 `repo/` / `vX.Y.Z/` / 非预期未跟踪条目（M15） |

### 约束（关键项）

- **测试用例命名加区分前缀**（P2-review 非阻塞项 4）：目标文件已含 `test_bdd_1`..`test_bdd_8`（TAG0008 语义），TAG0032 BDD-N ≠ TAG0008 BDD-N → 新用例函数名用 `test_tag0032_bdd_N_*`（或 `test_meta_repo_*` / `test_rootproto_*` 语义名），避免 pytest 收集冲突与 BDD 编号语义混淆
- **红灯必须是 B 类**（真红灯）：断言失败 / 项目内 import 失败（如 `from agate_common import _protocol_root` 尚不存在、install 无软链守卫 → 断言 exit≠0 得到 exit 0 而失败）。**不得**是 A 类（SyntaxError / 第三方 import 失败）。写完**必须自跑测试**确认每条红灯的失败原因，A 类先修
- **平台无关**（AGENTS.md 硬约束）：`tmp_path` / `python_exe` fixture（不裸 `python3`）；不假设 POSIX symlink（`os.symlink` 失败 → `pytest.skip`）；不用 `/tmp` 字面量；`install.sh` 经 conftest `bash` fixture 调用；隔离 HOME 用 `HOME` + `USERPROFILE` 双 env（见 conftest `_resolve_env`）
- **fixture 形态铁律**（I-5，TAG0008 教训）：元仓库形态 fixture 必须「协议在 `agate/` 子目录、`vX/scripts/` 不存在」；不得用「根即协议」模拟 repo 代替。保留 `_make_home_rootproto` 作 BDD-7 对照
- **创建型资源清理**：涉及隔离 HOME + `~/.agate` 目录创建的用例，用 `tmp_path` / fixture teardown 无条件清理（pytest tmp_path 自动清理即可，隔离 HOME 用 `monkeypatch.setenv` + tmp_path）
- **永久回归判据**（TAG0025 教训）：BDD-12 断言的是「文档口径长期不变量」——断言「生命周期节存在且口径一致」这种长期不变量，不要断言「最近一次 commit 改了什么」
- **不改实现代码**：P3 只写测试；`_protocol_root` / install 守卫 / `install.sh --versions` / UPGRADING 新节等都由 P4 实现。测试针对「实现后应表现成什么样」写
- **范围锁定**：只为 14 条 BDD 写用例，不给 out-of-scope（install-offline / Windows 复制模式 / .state.yaml schema）写用例

### 上游关联

P2-design.md approved（决策 A1 resolve 侧 `_protocol_root` 增量探测 + 决策 B1 副本 copytree；M1-M15 落点；§10 实现完成标志）。P2-review.md approved（0 阻塞，4 项非阻塞澄清项已并入本 dispatch-context 相关行）。P1 14 条 BDD 是测试的 1:1 来源。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 条 BDD，测试主来源——§3 BDD 全文 + §5 verification_env）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（M12-M15 测试落点 + §4.4 端到端 fixture 形态 + §7 files_to_read + §10 实现完成标志，权威）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review.md（4 项非阻塞澄清项：M2 指定版本分支源 / install.sh --versions 读 AGATE_REPO_URL / M5 version basename 入参 / BDD 命名前缀）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（env_constraints / 隔离 HOME 纪律）
- /home/kity/oclab/agateon/agate/assets/execution-roles/test-designer.md（角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/conftest.py（fixture 契约：`_resolve_env` / `git_repo` / `python_exe` / `run_cli` / `agate_scripts` / `bash` fixture，264-429 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_agate_version_install.py（`_run_install` / `_tag_upstream` / 既有 `test_bdd_N` 形态——新用例基准）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_agate_version_resolve.py（`_make_home` / `_write_version_decl` / `test_bdd_30` 的 `os.symlink`→skip 模式——双 fixture `_make_home_meta` / `_make_home_rootproto` 基准）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_hook_resolve_entry.py（`_STUB_GATE` / `_make_home` 建 `vX/scripts/` 直含——meta fixture BDD-8 基准）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/integration/test_pre_commit_hook.py（integration 层结构参考——`test_version_lifecycle_e2e.py` 骨架）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate_common.py（`_resolve_version_info`:125-196——理解 `_protocol_root` 将插入的位置与两处调用点，测试据此断言解析输出）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-install.py（`_cmd_install` / `_ensure_repo` / `_install_version`——理解 M1 守卫 + M2 副本落点，测试据此断言 install 行为）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/resolve-entry.py（`:49` gate 路径拼接——BDD-8 断言基准）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/install.sh（M6 `--versions` 分支将加在哪——BDD-5 断言基准）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`（pytest 9.0.3 / pyyaml 6.0.1）
- 自跑测试确认红灯：`timeout 180 /usr/bin/python3 -m pytest <你新增的测试文件> -p no:cacheprovider -x` —— 逐条确认失败原因是 B 类（断言失败 / 项目内 import 失败），A 类（SyntaxError / 第三方 import）先修
- gate_commands.P3（P2 固化）：`python3 -m pytest agate/tests/ -p no:cacheprovider`；无 P3_formatter → check-tdd-red 退化为 exit-code-only（所有红灯 = 可推进），但你仍须自查每条红灯为 B 类
- **涉及安装路径 / `~/.agate` 的用例一律隔离 HOME**（`monkeypatch.setenv('HOME', str(tmp_path))` + `USERPROFILE`）——绝不动真实 `~/.agate`
- **主 checkout 禁止改动**；测试写进 worktree 的 `agate/tests/`
- bash 外层 `timeout` 30-180s（pytest 自跑给 180s）；单步串行不并行
- 状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：`P3-test-cases.md` 写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P3-test-cases.md`；测试代码写进 `agate/tests/unit/` `agate/tests/integration/`（既有树，按上表）
- 分阶段落盘：每读完一个输入文件 / 写完一个测试文件，追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P3-progress.md`（P3 是空返回高发阶段，逐条写）
- P3-test-cases.md frontmatter 用 `agate-md-field-set.py`（先 `--list`）；Header 成品值：`phase: P3` / `task_id: TAG0032` / `parent: P2-design.md` / `trace_id: TAG0032-P3-20260907` / `agent: test-designer` / `type: test-design` / `status: draft` / `created: 2026-09-07`；正文必须声明 `test_code_dir: agate/tests/`

### P3 自检（强制）
产出测试代码后必须自跑，确认每个红灯的失败原因是「被测模块/行为未实现」（`_protocol_root` import 失败 / install 无守卫致断言失败 / UPGRADING 无生命周期节致文本检索失败）。若某红灯失败原因是「断言与测试数据矛盾」（如断言的路径拼写错、fixture 形态搭错）——这是测试代码 bug，先修正再交付，不要留给 P5。

### 返回

只返回两行：① P3-test-cases.md 路径；② 一句话摘要（≤30 字：N 个测试用例，当前全部红灯 + 红灯类别）。
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
