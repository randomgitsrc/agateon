---
phase: P4
task_id: TAG0051
type: implementation
parent: P2-design.md
trace_id: TAG0051-P4-20261011
agent: implementer
status: draft
implementation_dir: agate/
prod_touched: false
---
# P4 实现记录 — TAG0051 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

> **性质**：本文件是 TAG0051 的 **P4 阶段产出（实现记录）**。P4 的代码改动由 **4 个实现支
> （A/B/C/D）+ 4 个修复支（R-A..R-F）** 完成，**已全部落盘且通过评审**；本记录**事后如实转录**已发生的
> 实现，**未改动任何代码 / 测试 / 协议文件**。
> **自查 ≠ gate**：本文只汇总实现与自查实测，**不预判** P5/P6/P7/P8 结论。
> **状态标记**：`[PROD_NOT_TOUCHED]` —— P4 全程只在本 checkout + `/tmp/opencode` 一次性副本上实现/验证，
> **未触发任何不可逆外部动作**（push / PR / merge / tag / Release / `workflow_dispatch` 一概未做）。
> **验收锚**：`P1-requirements.md`（23 条 BDD，1:1 映射见 `P3-test-cases.md` §2）。
> **评审**：`P4-review.md`（approved；backend `review` + `cso` 专家组）+
> SELF-GATE `docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md`（approved）。

## 0. 编排形态（P2 §4 / 派发实况）

P2 声明 `dispatch_plan.mode: static-batch`、`parallel_limit: 8`、**8 批**。P4 实按**人员支**执行（非按批一人）：

- **首轮 4 支并行**：A（`ready-no-tag` + `release-gate`）/ B（`delivery-contract` + `obligations-sync` +
  `p8-rules-roles` rules 面）/ C（`p8-surfaces` + `release-docs` + `p8-rules-roles` 文档面）/ D（`r6-harness` + P3 观察项）。
  各支**只改自己声明的文件**（dispatch-context 硬约束），避免并行冲突；跨批共享件 `check-gate.py`（仅 A 改）、
  `agate-release.py`（仅 A 改）**同文件不跨支改两轮**。
- **修复轮 3 支并行**（retry 1）：R-A（脚本/CI/wrapper 硬化）/ R-B（文档/规则/ADR 反向传播闭合）/ R-C（测试/夹具）。
- **收口轮**（retry 2/3）：R-D（R6 allowlist）/ R-E（文档传播 8 文件收敛）/ R-F（收口 3 条超授权项 + wrapper 健壮性）。
- **全部写类动作用 `git status` 实测核验**；R6 差分类实验**只在 `/tmp/opencode` 副本**上跑（AGENTS.md 工作流 0a）。

## 1. 任务摘要

把**不可逆的对外发布动作**（tag → GitHub Release）从任务 P8 结构性移出：

1. **任务终态 = READY**：交付物 + `CHANGELOG [Unreleased]` 含 task_id + `bump_type` 意图 + 交付收尾 +
   CI 全绿（含 push 口径）；**不落 tag / 不建 Release / 不 bump 版本文件**。
2. **Release = 独立流程**：`workflow_dispatch` 人工授权入口 + 机械发布门（目标提交 CI success + `check-protocol-consistency.py`
   0 ERROR + `check-gate.py P8` 复用的 RM 反查 / delivery / bump_type）+ 动作序列 + 失败处置。
3. **配套**：`delivery.method` 取值域收紧（新契约级 `level-2.yaml`）/ 发布授权说明（不引入第二套阻塞语义）/
   `AGENTS.md` 三处 tag 时点统一。

**统一口径（canonical，七处一致）**：
> READY 前置 = 交付物 + CHANGELOG `[Unreleased]` 含 task_id + `bump_type` 意图 + 交付收尾 + CI 全绿（含 push 口径）；不含 version bump / tag。

## 2. 批次与落地对照（P2 §4 的 8 批 × 产出文件 × 关联 BDD）

| 批 id | 复杂度 | 产出文件（实际落盘） | 关联 BDD | 批 `tests_filter` |
|-------|--------|----------------------|----------|-------------------|
| `ready-no-tag` | high | `agate/scripts/check-gate.py`（`gate_p8` 改造 + `method` 枚举钩子） | BDD-2/3/4/5/6/7/16/17/19 | `pytest agate/tests/unit/test_tag0051_p8_gate.py -q` |
| `p8-surfaces` | high | `agate/phase-cards/P8-release.md`、`agate/state-machine.md`、`agate/rules/state-transitions.md` | BDD-1/2/3/4/18 | —（文档） |
| `p8-rules-roles` | medium | `agate/rules/phases.yaml`、`agate/dispatch-protocol.md`、`agate/assets/execution-roles/implementer.md` | BDD-1/18 | —（规则/文档） |
| `delivery-contract` | medium | `agate/rules/task-data/level-2.yaml`（**新增**）、`agate/rules/task-data/LEVELS.yaml`、`agate/UPGRADING.md` | BDD-16/17/19 | —（契约） |
| `obligations-sync` | medium | `agate/rules/obligations.yaml`、`agate/tests/unit/test_tag0050_obligations_enforcement.py` | BDD-21 | `pytest …test_tag0050_obligations_enforcement.py …test_tag0050_obligation_behavior.py -q` |
| `release-gate` | high | `agate/scripts/agate-release.py`、`.github/workflows/release.yml`、`agate/tests/unit/test_release_gate.py` | BDD-8/9/10/11/12/13/23 | `pytest agate/tests/unit/test_release_gate.py -q` |
| `release-docs` | low | `AGENTS.md`、`agate/git-integration.md` | BDD-14/15 | —（文档） |
| `r6-harness` | low | `docs/design-notes/r6-differential-prepare.sh`（**新增**，NB-3） | BDD-20 | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus` |

> **批外增量（修复轮引入，均落 P4 改动面）**：R-B 追加 `agate/WORKFLOW.md`（反向传播漏项）、`agate/adr.md`（ADR-016）；
> R-D 追加 `docs/design-notes/r6-allowlist.yaml`（D13）；R-E 追加 `agate/phase-cards/P5-verification.md`、
> `agate/phase-cards/README.md`、`agate/assets/templates/{task-files,active-tasks-template}.md`、
> `agate/scripts/README.md`、`agate/tests/README.md`；R-F 追加 `agate/assets/templates/dispatch-prompt.md`。
> （文档面新增测试 `test_tag0051_docs_consistency.py` / `test_tag0051_state_machine.py` /
> `test_tag0051_delivery_contract.py` / `test_tag0051_r6_harness.py` / `test_tag0051_obligations_sync.py` /
> `test_tag0051_self_gate.py` 为 **P3 产出**（已随 P3 提交），**不计入 P4 新增**。）

## 3. `P2-design.md` §1.1 的 M1–M16 落点对照

| # | 文件 | 改了什么（实测） | 关联 BDD |
|---|------|------------------|----------|
| M1 | `agate/scripts/check-gate.py` | `gate_p8` **删** tag 存在性 WARNING 块、version 双路径 WARNING 块、CHANGELOG 暂存区 diff WARNING 块、迁移期 `agate.config.yaml` 提示块；**保留** `bump_type`/`debt_check`/结构化 `delivery`/RM-AG0043 反查；**新增** `delivery.method` 枚举校验（读快照 `delivery.method_enum`，缺省 no-op，仅非 legacy 且 task_level ≥2 生效） | BDD-2/3/4/5/6/7/16/17/19 |
| M2 | `agate/phase-cards/P8-release.md` | 去「同 commit + tag」、CHANGELOG「→新版本号」、两处「`git tag` 已创建」、gate 规则的 version/CHANGELOG-diff 行；CHANGELOG 载体改为一行 `check-changelog.py <task_id>`；**保留 anchor 节标题** `## gate 规则` / `## 如果是首次进入本阶段` | BDD-1/2/3/4 |
| M3 | `agate/state-machine.md` | P8→READY 转移条件删 tag/version；READY 收尾检查删「`git tag` 已创建」；**新增**发布授权说明（独立流程 + `workflow_dispatch`，不新增第二套阻塞语义）；**R-B 追加修复**同文件其余 P8 描述（`:323/:327/:330/:403-406` 的 version bump/version 文件残留） | BDD-1/2/3/18 |
| M4 | `agate/rules/state-transitions.md` | P8→READY 行删 tag/version 条件，保留 bump/CHANGELOG | BDD-1/3 |
| M5 | `agate/rules/phases.yaml` | P8 `gates` 措辞去 version/CHANGELOG/tag 检查与「先 tag 后重跑（DEBT0013）」；**R-B 补** `check-changelog.py <task_id>` 声明（闭 S-3b）；结构键 `gate_pass_exit`/`retry_cap`/`outputs`/`task_fields` 不动 | BDD-1/3 |
| M6 | `agate/rules/obligations.yaml` | `OBL-P8-*` 十四条逐条同步：**OBL-P8-04 就地重挂**为 `delivery.method` 枚举校验（`disposition` 保持 **M**、`enforced_at` → `check-gate.py::gate_p8`）；OBL-P8-05/08/13 仅 statement 改述；其余 10 条保留；**不删条目、不写 `baseline.reset`** ⇒ M 计数 56 不变 | BDD-1/21 |
| M7 | `agate/tests/unit/test_tag0050_obligations_enforcement.py` | `M_IDS` 保持含 `OBL-P8-04`（零改动）；**新增** BDD-21 机械断言（`OBL-P8-*` statement 无 version/tag 期残留 + `OBL-P8-04` 仍为 M 且含 `method_enum`）；`test_tag0050_obligation_behavior.py`（OBL-P8-01/02/03）**不改**，作回归锁 | BDD-21 |
| M8 | `agate/rules/task-data/level-2.yaml`（**新增**） | `level: 2` / `extends: 1`；`delivery` 节**重述完整**并新增 `method_enum: [release-notes, tag-release, none]`（`load_contract` 顶层键整体覆盖 ⇒ 必须重述） | BDD-16/17 |
| M9 | `agate/rules/task-data/LEVELS.yaml` | 追加 `{level: 2, file: level-2.yaml, sha256: "741afaf7…2b34"}`（未登记即 consistency ERROR） | BDD-16/19 |
| M10 | `agate/UPGRADING.md` | 新增版本节记录 `delivery.method` 收紧 + P8 去 tag/version；**R-B 追加修复**如实框定破坏半径（登记 level-2 后当前等级 1→2，此后所有非 legacy 新任务须为等级 2；既有任务/存量数据不受影响），不预告未排期版本号 | BDD-16/19 |
| M11 | `agate/scripts/agate-release.py` | **新增** `gate` 子命令（+ `_cmd_gate`）：复用 `check-gate.py P8` + 目标提交 CI success（查 check-runs，required contexts 逐项 `conclusion==success`）+ `check-protocol-consistency.py` 0 ERROR；CI 查询走**可注入命令**（`--ci-cmd`）、经 `git remote`/`gh` 解析仓库（不写死 main）；缺省 fail-closed；既有子命令语义不变 | BDD-9/10/12/13 |
| M12 | `.github/workflows/release.yml` | `on:` **追加** `workflow_dispatch:`（与 `push: tags` 并存）；**新增**一步**调用** `agate-release.py gate`（tag push 路径 fail-closed backstop，只调用不内联）；**保留**「Verify tag points to matching commit」步 | BDD-8/9/10/11/12/13 |
| M13 | `AGENTS.md` | 版本发布清单**三处 tag 时点统一**为「先合 release PR → main CI 绿 → 后 tag」；新增「发布失败处置」小节（先评估回退重打，仅被外部消费才出补丁）；不可逆动作须用户授权 | BDD-14/15 |
| M14 | `agate/git-integration.md` | `:185-188`（release PR 普通 merge + G-5 tag 时点）与 `AGENTS.md` 口径一致 | BDD-14 |
| M15 | `agate/dispatch-protocol.md` | P8→READY 行删「+ tag 由主 Agent 亲自执行」与 version 双路径；保留 bump_type/CHANGELOG/debt_check；**R-F** 同步 `:487` 节名索引 | BDD-1 |
| M16 | `agate/assets/execution-roles/implementer.md` | `:101` 收为「不执行 `git commit`」（tag 移出 P8 语义）；**R-E** 同步 `:45/:49/:90-99` 的「P8 多包发布」节（旧版本→新版本 ⇒ `bump_type` 意图 + CHANGELOG） | BDD-1 |

## 4. P4 修复轮记录（R-A..R-F，一支一句话）

| 支 | 动机 | 结果（一句话） |
|----|------|----------------|
| R-A | 首轮评审 SEC-01/04/09 + A8 #5（R6 证据「空转」）| 本地发布门 **fail-closed**（required 空 + 零 check-run ⇒ 非 0）；wrapper `--dst` 全负例**删除前**拒绝（含空/相对/src 内/src 祖先/前缀外）；显式拒空 `--sha`；R6 wrapper 的 `--after` 指向**真实工作树**（含未提交改动）使证据非空转；SEC-02/03/07 以注释记录信任前提 |
| R-B | SELF-GATE MISALIGNED-1/3/4/5 + A7 | 闭合 `state-machine.md` 同文件自相矛盾、`WORKFLOW.md:327` 反向传播漏项（原 Not-Modify 判定据 `git tag` 单字面失效）、`phases.yaml` 补 `check-changelog.py <task_id>` 声明（S-3b 闭）、`UPGRADING.md` 如实框定破坏半径；新增 **ADR-016**（发布与任务解耦） |
| R-C | SELF-GATE A4b：54 个既有用例转红 | 收敛到「仅剩设计性必红 + 环境项」：契约等级抬升（约 38 条，改夹具等级非放宽断言）、已删 WARNING 断言（5 条，正向重定向）、`release.yml` 锁定（3 条）、`write_tools`（1 条）；S-3b 7 条由 R-B 闭合 |
| R-D | R6 差异需登记 | 在 `r6-allowlist.yaml` 追加 **D13** 记录 P8 删「④ 从 P2 packages 验证 version 文件路径」的有意差异（rc 2→2，仅收尾文案），并将 D13 加入 `required_ids` ⇒ 复跑 `差异 2 条、未匹配 0 条` |
| R-E | 反向传播文档残留（语义族 grep） | 收敛 8 文件：`check-gate.py:25` docstring、`implementer.md` P8 节、`P5-verification.md`、`phase-cards/README.md`、`task-files.md`、`active-tasks-template.md`、`scripts/README.md`、`tests/README.md` |
| R-F | 收口 R-E 上报的 3 条超授权项 + wrapper N1 健壮性 | `check-gate.py` `gate_p8` 函数头注释更新；`dispatch-prompt.md` 节名改「`bump_type` 意图判定（不执行 bump）」；`dispatch-protocol.md:487` 节名索引同步；wrapper 建 corpus 由 `cp -a`+`clean -fdx` 换为 **`git clone --local --no-hardlinks`**（外部契约不变） |

## 5. `P4-evidence/` 批级证据索引（MVWU 阶段 1）

| 日志 | 所属批 | 命令 | `exit_code` | 耗时 | `git_head` |
|------|--------|------|-------------|------|-----------|
| `P4-evidence/ready-no-tag.log` | `ready-no-tag` | `python3 -m pytest agate/tests/unit/test_tag0051_p8_gate.py -q` | 0 | 1s | `d4e32f4fbcefe7ef7d4910f7a770928c99588f1c` |
| `P4-evidence/obligations-sync.log` | `obligations-sync` | `python3 -m pytest …/test_tag0050_obligations_enforcement.py …/test_tag0050_obligation_behavior.py -q` | 0 | 1s | 同上 |
| `P4-evidence/release-gate.log` | `release-gate` | `python3 -m pytest agate/tests/unit/test_release_gate.py -q` | 0 | 3s | 同上 |
| `P4-evidence/r6-harness.log` | `r6-harness` | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus` | 0 | 41s | 同上 |

> 四份日志的 `expected_red`/`failed_tests` 均 `[]`。除这 4 个有 `tests_filter` 的批外，
> `p8-surfaces`/`p8-rules-roles`/`delivery-contract`/`release-docs` **无 `tests_filter`**（文档/契约/规则面），
> 按规范不产证据日志。

## 6. 全量改动文件清单（`git status --porcelain -uall` 实测，2026-10-11）

`git status --porcelain -uall` 实测 **40 个 `M`**，其中任务目录内 3 个
（`.state.yaml`、`P2-design.md`、`P3-progress-test-designer.md`）⇒ **代码/协议/文档面修改 37 个**。

### 6.1 修改（37 个）

1. `.github/workflows/release.yml`
2. `AGENTS.md`
3. `agate-workspace/debt/tech-debt.md`（登记 DEBT0069/DEBT0070）
4. `agate/UPGRADING.md`
5. `agate/WORKFLOW.md`
6. `agate/adr.md`（ADR-016）
7. `agate/assets/execution-roles/implementer.md`
8. `agate/assets/templates/active-tasks-template.md`
9. `agate/assets/templates/dispatch-prompt.md`
10. `agate/assets/templates/task-files.md`
11. `agate/dispatch-protocol.md`
12. `agate/git-integration.md`
13. `agate/phase-cards/P5-verification.md`
14. `agate/phase-cards/P8-release.md`
15. `agate/phase-cards/README.md`
16. `agate/rules/obligations.yaml`
17. `agate/rules/phases.yaml`
18. `agate/rules/state-transitions.md`
19. `agate/rules/task-data/LEVELS.yaml`
20. `agate/scripts/README.md`
21. `agate/scripts/agate-release.py`
22. `agate/scripts/check-gate.py`
23. `agate/state-machine.md`
24. `agate/tests/README.md`
25. `agate/tests/integration/test_pre_commit_hook.py`
26. `agate/tests/integration/test_tag0050_ci_replay.py`
27. `agate/tests/integration/test_tag0050_prod_touched.py`
28. `agate/tests/integration/test_tag0050_state_set.py`
29. `agate/tests/regression/test_v060_p8_cached.py`
30. `agate/tests/unit/test_check_gate.py`
31. `agate/tests/unit/test_gate_layer.py`
32. `agate/tests/unit/test_release_gate.py`
33. `agate/tests/unit/test_release_workflow.py`
34. `agate/tests/unit/test_tag0050_obligations_enforcement.py`
35. `agate/tests/unit/test_tag0050_write_tools.py`
36. `agate/tests/unit/test_tag0051_obligations_sync.py`
37. `docs/design-notes/r6-allowlist.yaml`

> 其中 **12 个测试文件**（25–36）为 R-C 修复轮改动。

### 6.2 新增代码/资产文件（4 个）

1. `agate/rules/task-data/level-2.yaml`（新契约级快照，M8）
2. `agate/tests/fixtures/task-data/level-2/pass/README.md`（P3 观察项补齐）
3. `agate/tests/fixtures/task-data/level-2/fail/README.md`（P3 观察项补齐）
4. `docs/design-notes/r6-differential-prepare.sh`（R6 wrapper，NB-3）

> 说明：`P2` 表格把新增列写为「`agate/rules/task-data/level-2.yaml`、`agate/tests/fixtures/task-data/level-2/{pass,fail}/README.md`、
> `docs/design-notes/r6-differential-prepare.sh`」（3 条目，其中 `{pass,fail}` 为两文件）⇒ 实为 **4 个文件**，如实列出。

### 6.3 新增的评审/记录产物（非代码，随 P4 一并提交）

- `docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md`（+ `.progress.md`）：SELF-GATE 独立评审。
- 任务目录内：`P4-dispatch-context-*.md`、`P4-progress-implementer-*.md`、`P4-review*.md`、`P4-evidence/*.log`、本文件。

## 7. 测试 / 验证结果（自跑实测，2026-10-11；`HEAD=d4e32f4f`）

| 命令 | 实测结果 |
|------|----------|
| `python3 -m pytest agate/tests/ -q -n auto` | **2 failed / 2957 passed / 2 skipped**（115.82s） |
| `bash agate/tests/scripts/count-tests.sh` | **2961** |
| `python3 agate/scripts/check-protocol-consistency.py` | **0 ERROR / 432 WARNING**（rc=0） |
| `python3 agate/scripts/check-obligations.py` | `M 类占比: 56/121 = 0.4628`（不低于基线，OK） |
| `python3 agate/scripts/check-structure-consistency.py` | rc=0（S1–S6/S0 全 OK） |
| `~/.venvs/agate-dev/bin/ruff check agate/` | All checks passed |
| `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-record-r6` | rc=0；`legacy 任务 39 个，差异 2 条，未匹配 0 条`（2 条均 `[ALLOWED]`，对应 D13） |
| 批级 `tests_filter` 复跑 | `test_tag0051_p8_gate.py` **8 passed**；`test_tag0050_obligations_enforcement.py …obligation_behavior.py` **68 passed**；`test_release_gate.py` **10 passed** |

**两条 remaining red 的归因**（均**非本任务引入**）：

- `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
  —— **本机 opencode CLI 环境漂移**（`opencode debug agent` 已更名 `opencode debug agents`），与本任务无关。
- `agate/tests/unit/test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review`
  —— **设计性必红**：须等**本任务的 P4 提交携带 `self-gate-review:` 留痕**后才转绿（P4 提交尚未创建）。

> **未复跑项（如实）**：`check-platform-assumptions.py` 全仓自检、`P5_sg6`
> （`test_protocol_alignment_review.py`）本次未单独复跑——它们属 P5 `gate_commands` 面，由 P5 阶段验真。

## 8. 新引入的机制 / 工具（各一段）

- **`agate-release.py gate` 子命令（M11）**：既有 `agate-*.py` 面上**新增**的发布门子命令，**不新增/不改名
  `agate/scripts/` 下任何文件** ⇒ CHECK 9 / SG.6 / CHECK 10 三处登记面**零触发**。串起三判据：① 复用
  `check-gate.py P8`（RM 反查 / delivery / bump_type，判据单源）；② 目标提交 CI success——查 check-runs
  按 required contexts 逐项要求 `conclusion == success`（**非** combined status：本仓实测该 API 返回
  `state=pending,total_count=0`）；③ `check-protocol-consistency.py` 0 ERROR。CI 查询走**可注入命令**
  （`--ci-cmd`）供本地 fixture/mock 验证；缺省 fail-closed（required 解析为空 + 零 check-run ⇒ 非 0，SEC-01 硬化）；
  无无界轮询；经 `git remote`/`gh` 解析仓库不写死 `main`（RM-AG0116）。
- **R6 一键 wrapper（`docs/design-notes/r6-differential-prepare.sh`，NB-3）**：把 `P5_r6` 的「备 corpus」
  从**人记**改为**机械**——落在 `docs/design-notes/`（**非** `agate/scripts/`）⇒ 登记面零触发。
  行为：校验 `--dst`（空/相对/位于 `--src` 内/是 `--src` 祖先/前缀外/已存在软链 ⇒ **删除前** `exit 2`）→
  建一次性 corpus（R-F 后为 `git clone --local --no-hardlinks`，自带 `.git` 全史 + 干净工作树）→ `exec`
  既有 `r6-differential.sh`，并把 `--after` 指向**真实工作树**（`--src/agate`，含未提交改动）使证据非空转。
  真实仓库**只被只读**（`cp -a`/`clone` 读取 + `git -C <dst>` 写类命令）。
- **`level-2.yaml` 契约级快照（M8/M9）**：`extends: 1`，`delivery` 节**重述完整** + 新增
  `method_enum: [release-notes, tag-release, none]`；登记 `LEVELS.yaml`（LF 归一 sha256）。
  生效面 = **非 legacy 且 task_level ≥ 2** 的新声明；legacy 走既有子串路径不受影响 ⇒ 对存量**机械非破坏**。
  注意破坏半径（R-B 如实框定）：登记后 `current_level` 1→2 ⇒ 升级后**所有非 legacy 新任务须为等级 2**。
- **ADR-016（`agate/adr.md`，A7）**：「发布与任务解耦」——不可逆对外发布动作（tag → Release）**移出任务状态机**；
  任务终态 = READY；发布 = 独立流程 + 人工授权入口（当前实现 `workflow_dispatch`）+ 机械发布门；
  **不引入**与既有 `PAUSED`/`NEED_CONFIRM` 并行的第二套阻塞语义。

## 新增文件核对表

> `{AGATE_WORKSPACE}/agents/CODE-MAP.md` **存在** ⇒ 填本表（缺此表会触发 P4 gate 的 WARNING）。
> 本任务**未采用 `P2-skeleton.md`** ⇒ 骨架归属列按 `within <父目录>` 判定。
> **主 Agent 实测 `CODE-MAP.md` 未含本次新文件**；改 `CODE-MAP.md` **超出本次授权**（不在产出面）⇒
> 一律填 `[CODE_MAP_EXEMPT: 理由]`。

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/rules/task-data/level-2.yaml` | `within agate/rules/task-data/` | `[CODE_MAP_EXEMPT: 契约级快照数据文件（非代码模块），由 LEVELS.yaml 登记 + CHECK 16 快照冻结守护；惯例上不入 CODE-MAP]` |
| `agate/tests/fixtures/task-data/level-2/pass/README.md` | `within agate/tests/fixtures/task-data/level-2/` | `[CODE_MAP_EXEMPT: 测试黄金 fixture 的说明文件，非代码模块]` |
| `agate/tests/fixtures/task-data/level-2/fail/README.md` | `within agate/tests/fixtures/task-data/level-2/` | `[CODE_MAP_EXEMPT: 测试黄金 fixture 的说明文件，非代码模块]` |
| `docs/design-notes/r6-differential-prepare.sh` | `within docs/design-notes/` | `[CODE_MAP_EXEMPT: 文档目录下的一次性差分 wrapper，Check 9/SG.6/CHECK 10 三处均不扫 docs/ ⇒ 零登记面；非 agate/ 代码模块]` |

如需登记 CODE-MAP，请主 Agent 授权。

## 10. 设计偏差 / 已知偏离（供 P7 处置）

- **R2（P4-review.md 已登记）**：`P2-design.md` §决策 8/§5（`:235/:283/:326/:337`）仍述 wrapper 用
  `cp -a` + `checkout -- .` + `clean -fdx`，而 R-F 已按主 Agent 派发指引换为 **`git clone --local --no-hardlinks`**
  （外部契约不变：同名参数、corpus 干净、跑后真仓干净）。该偏离**由派发指引授权**（非未评审的自主决策），
  `P4-review.md` R2 判「已批准设计记录 vs 实现，**留待 P7 以已知偏离处置**」。
- **`r6-differential.sh::_error_lines` 口径落差**：该脚本把**所有以 `GATE ` 开头的行**（含成功消息）纳入比较，
  比其文件头自述的「(退出码, ERROR 行集合)」更宽 ⇒ 本任务 P8 成功文案删 ④ 被判为差异；已由 **D13** allowlist
  记录（不收紧守卫强度）；口径落差由主 Agent 另行登记 **DEBT0070**（不在本任务面）。
- **`release.preset` 悬空键**：`gate_p8` 迁移期提示块删除后该键**无值消费方**，保留为信息性声明，
  由 **DEBT0069** 登记（**M11 发布门不消费该键**，避免超出 BDD-19 要求）。
- **实现期上报的 `[SCOPE+]`（已在各 progress 文件留存，非本记录新增）**：① A 支报
  `test_release_gate.py::_ledger()` 用了 `helpers_tag_repo` 不存在的 `GENESIS_HASH`（夹具缺陷，属测试面 ⇒ 转 R-C 处理）；
  ② R-A 支报 R6 非空转后暴露的 P8 成功文案差异（⇒ 转 R-D 以 D13 记录）。二者均**已闭合**。

## 11. 临时资源与残留

- **无长驻服务/进程**（本仓验证面 = `agate.config.yaml::verify.commands` 四条 + `gate_commands`，均为一次性命令）。
- **一次性 corpus**：`/tmp/opencode/tag0051-r6-corpus`（P4-evidence 用）与本次复跑
  `/tmp/opencode/tag0051-record-r6`、`/tmp/opencode/tag0051-pytest-full.log`——**均在 `/tmp/opencode` scratch 根下**，
  由 wrapper 每次 `rm -rf` 重建/覆盖，**不触及真实仓库**；如需清理可直接删除该 scratch 目录。
- **未做任何开发安装**（无 editable install / 全局包安装）。
- **跑后核验**：R6 复跑后真实仓库 `git status --porcelain` 的新增项**全部为本任务既有改动**（无 `gate-events.jsonl`
  等账本污染）⇒ 真实仓库只被只读。

## 12. 自查声明

- 本文件**未改动任何代码/测试/协议文件**（特别是**未碰** `agate-workspace/agents/CODE-MAP.md`）；仅**新增本文件**
  + **追加** `P4-progress-implementer-record.md`。
- **自查 ≠ gate**：上述数字为本 implementer 自跑实测；P5 由主 Agent 派发 verifier 执行 `gate_commands.P5` 验真，
  本文不声称「P5 已过」。
- `[PROD_NOT_TOUCHED]`：未触发任何写入生产 / 不可逆外部动作。
