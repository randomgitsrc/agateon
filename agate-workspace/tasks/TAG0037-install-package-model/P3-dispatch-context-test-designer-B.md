---
phase: P3
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0037
role: test-designer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P3 **第 2 组（B：安装 / 离线 / legacy 代码面测试）**，首次派发；C 组并行运行（写文档/回归类测试，互不冲突）。

### 目标

为 P2 批次 B1a、B1b、B2、E（代码面）写测试：

- 新增 `unit/test_agate_install_adopt.py`（`--adopt` / `--check --portable`、失败路径 T-20、指针回滚 T-16）
- 新增 `unit/test_install_sh.py`（install.sh 无参 = --versions 别名、软链守卫、废弃 env WARNING、shellcheck 无关）
- 新增 `regression/test_protocol_root_dual_impl.py`（BDD-8 双实现一致）
- 新增/修改离线与解析相关测试：`unit/test_install_offline.py`（修正 `_make_bundle` 反映真实布局 BDD-11、T-2 红灯回放、T-15 bundle 内入口、T-16 换位失败注入、T-19、T-23 清扫只删自己的——数据安全必测）、`unit/test_agate_pack_offline.py`、`regression/test_offline_bundle_roundtrip.py`
- 解析/软链 fail-closed：`unit/test_agate_version_resolve.py`、`unit/test_agate_workspace_resolve.py`、`unit/test_agate_summary.py`（BDD-27/28/29/30/31/32/33/34/35/51、T-14 软链守卫参数化 `["L","L/","L//","L/.","L/.."]`）
- 既有 4 个真 legacy 测试的处置（BDD-38：删除/改写；⚠ 排除撞名，名含 `bdd_30` 的多数与 legacy 无关，**勿误删**）及 T-11 的既有断言调整
- 在线安装/卸载/历史 tag：`unit/test_agate_version_install.py`、`unit/test_agate_install_uninstall.py`（BDD-22/24/25/26/32/36 中安装侧；T-10 夹具增拷 `agate_package.py`）

### 你的 BDD 范围

BDD-5、6、7、8、10、11、12、18、25、26、27、28、29、30、31、32、33、34、35、36、38、47、51、52（BDD-9/17/22/23/24/4 中 A 组已写的部分不重复；如发现某条 BDD 在 A 组映射 §2 已覆盖，则只补 B 侧独有子场景）。BDD-47（hook 解析不受影响）用既有 hook 相关测试 + 新增回归。拿不准的以 P2 §5 批次表"批内验收"列为准，并在你的小节写明边界。

### 约束

1. 输入必读：P2-design.md（§3、§5、§6 全部 T-*、§14 处置表）、P1-requirements.md、P0-brief.md、P3-test-cases.md（A 组索引）、agate/tests/helpers_tag_repo.py。
2. 被测新行为尚未实现（`agate_package.py`、`--adopt`、软链守卫等）——对它们的调用即红灯。
3. 修改既有测试文件时，被保护的函数体不改（T-10），仅按 T-11 调整/新增；每处修改在你的 P3 小节登记（文件、原因、依据）。

### 通用约束（强制）

1. **TDD**：测试必须在实现前**红灯**（B 类：assertion 失败/项目内模块缺失；禁止 SyntaxError/第三方 import 失败=A 类假红灯）。每条 BDD 至少 1 个测试，用例名或 docstring 含 `BDD-NN`；`[参数化]` BDD 逐子场景各一个参数化用例（P1 §4 全或无规则）。
2. **平台无关**：不用 `/tmp`（用 `tmp_path`）、不裸 `python3`（用 `sys.executable`）、不假设 POSIX symlink 语义（Windows 分支断言）；Windows CI 仅跑 `-m windows_smoke`。
3. **隔离**：安装/打包验证用 `tmp_path` 下的隔离 `AGATE_HOME`/`--dest-root`/合成 git 仓库；**不得触碰真实 `~/.agate`、开发 checkout、真实 origin**（不推 tag、不发 Release）。
4. **数据安全（用户强制）**：禁止 `rm -rf`、禁止清空重建、禁止删除任何非本次新建的文件；测试内清理只依赖 pytest `tmp_path`；仓库内只新增/修改本组指定的测试文件与本组在 P3-test-cases.md 中的小节，**不留任何临时/备份/日志文件**；scratchpad 实验用新建带序号目录。
5. **共享夹具**：A 组已交付 `agate/tests/helpers_tag_repo.py` 与 `P3-test-cases.md` 总索引（§0 夹具用法、§2 A 组 BDD→测试映射）。**先读它们，复用夹具，不要另写第二套**；缺夹具能力时在你的测试文件内加本地助手，**不改** `helpers_tag_repo.py`。
6. **既有测试保护**：P2 §6 T-10/T-11 列明既有测试的处置（函数体不改 / 允许改夹具或断言）——严格遵循；不得为变绿而弱化既有断言。**需要修改既有测试文件的，只做 P2 明确允许的修改。**
7. **`tests_filter` 回填 + 自证**：在你的 P3-test-cases.md 小节给出本组各批的 `tests_filter`（pytest 命令）与 BDD→测试对应表；写完后自己跑本组测试（`PYTHONDONTWRITEBYTECODE=1 timeout 280 python3 -m pytest <files> -q --no-header -p no:cacheprovider`），记录红灯数/有意应绿数，并确认红灯均为 B 类。
8. **只追加你自己的小节**：编辑共享的 `P3-test-cases.md` 时只填你的小节（B 组填「## 6. B 组」，C 组填「## 7. C 组」），另一组与 A 组内容不动；两组并行运行，用 Edit 精确替换自己小节的标题下内容，不要整文件重写。
9. 不 git commit。不写行首 `- PASS`/`- FAIL`。返回：一句话摘要（≤30 字）+ 新增/修改文件列表。

### 上游关联

P0-brief.md、P1-requirements.md、P2-design.md、P3-test-cases.md（A 组索引）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/P2-design.md
- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/P1-requirements.md
- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/P3-test-cases.md
- agate/tests/helpers_tag_repo.py
- 上述被改/参照的既有测试文件与 agate/scripts/{agate-install,install-offline,agate-pack-offline,agate_common,agate-resolve,agate-summary}.py、install.sh
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
