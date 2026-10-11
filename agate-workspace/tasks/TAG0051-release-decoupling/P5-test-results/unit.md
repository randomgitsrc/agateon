---
phase: P5
task_id: TAG0051
type: verification
parent: P4-implementation.md
trace_id: TAG0051-P5-20261011
status: draft
created: 2026-10-11
agent: verifier
prod_touched: false
---

# P5 技术验证结果 — TAG0051 任务与发布解耦

> **状态标记**：`[PROD_NOT_TOUCHED]`（本任务无生产环境触达，全部命令只读/测试）
> **NO_NEED_CONFIRM**：无不可逆操作（未 push / PR / merge / tag / Release / 改分支保护）
> **执行分支**：`task/TAG0051-release-decoupling`（P4 已提交，父提交 `9771e76`）
> **命令来源**：`P2-design.md` 的 `gate_commands`（逐字照抄，未改写）
> **执行入口**：命中 `agate.config.yaml::verify.commands` 白名单的 4 条走
> `agate-run.py --task agate-workspace/tasks/TAG0051-release-decoupling "<命令>"`（白名单 + 证据入库 `runs/<k>.log` + 账本 `cmd_run`）；
> 白名单外的 3 条（`P5_obligations` / `P5_sg6` / `P5_r6`）用**普通 bash** 执行——**未经白名单/账本路径**（如实声明，未掩盖）。

## 失败清单（pytest 形态）

FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent

## 汇总签名行

passed: 2958  failed: 1  skipped: 2

1 failed, 2958 passed, 2 skipped in 139.05s

---

## 逐条命令结果

### 1. `P5` — 全量回归（agate-run 白名单）

- **命令**：`python3 -m pytest agate/tests/ -q -n auto`
- **退出码**：`1`（唯一红为**预存 + 环境性**失败，见下）
- **关键输出**：`1 failed, 2958 passed, 2 skipped in 139.05s`
- **失败清单**：`FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
- **证据**：`runs/2.log`（run:2 = 口径运行）

> **预存失败：`test_bdd_43`（与本次改动无关）**——本机 `opencode` CLI 的 `debug agent` 子命令已漂移为 `agents`
> （`Unknown subcommand "agent" for "opencode debug"`），断言不符，**非本仓代码缺陷**。主 Agent 于 P0 基线实测同一失败。
> 已按 P5 卡「预存失败的处理」登记至 `known-failures.md`。

> **口径说明（两次全量）**：
> - **run:1**（`runs/1.log`）= `2 failed, 2957 passed, 2 skipped`——**多出一条** `FAILED agate/tests/integration/test_pre_commit_hook.py::test_m1_forward_jump_p2_to_p5_blocked`。
>   该用例**隔离单跑恒绿**（`1 passed in 3.49s`），且 **run:2 全量未复现**——系**已登记的跨文件 flaky（`DEBT0063`，`status: closed`）**，
>   与本任务改动无关（CI 口径的 flaky 兜底即 `--reruns 1`，见 `agate/tests/README.md:27-28`）。
> - **run:2**（`runs/2.log`）= `1 failed, 2958 passed, 2 skipped`——**与主 Agent 预期一致**，唯一红 = `test_bdd_43`（环境性预存失败）。
> - 本报告以 **run:2** 为正式口径；`fail-list.txt` 登记 run:2 的失败。

### 2. `P5_consistency` — 判据单源一致性（agate-run 白名单）

- **命令**：`python3 agate/scripts/check-protocol-consistency.py`
- **退出码**：`0`
- **关键输出**：`仅有 432 个 WARNING，无 ERROR。`（432 为冻结历史 WARNING，设计如此）
- **证据**：`runs/3.log`

### 3. `P5_count` — 用例数未漂移（agate-run 白名单）

- **命令**：`bash agate/tests/scripts/count-tests.sh`
- **退出码**：`0`
- **关键输出**：`总计：2961 个测试用例（pytest collect-only 口径）`
- **证据**：`runs/4.log`

### 4. `P5_ruff` — 静态检查（agate-run 白名单）

- **命令**：`$HOME/.venvs/agate-dev/bin/ruff check agate/`
- **退出码**：`0`
- **关键输出**：`All checks passed!`
- **证据**：`runs/5.log`

### 5. `P5_obligations` — obligations anchor 无悬空 + M 计数不降（**普通 bash，白名单外**）

- **命令**：`python3 agate/scripts/check-obligations.py`
- **退出码**：`0`
- **关键输出**：`M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）`；`CHECK-OBLIGATIONS: OK`
- **说明**：**未经 agate-run 白名单/账本路径**（该命令不在 `verify.commands` 白名单内）。

### 6. `P5_sg6` — 脚本登记面无漂移（**普通 bash，白名单外**）

- **命令**：`python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -q`
- **退出码**：`0`
- **关键输出**：`14 passed in 0.06s`
- **说明**：**未经 agate-run 白名单/账本路径**（该命令不在 `verify.commands` 白名单内）。

### 7. `P5_r6` — legacy 行为不变 R6 双向差分（**普通 bash，白名单外**）

- **命令**：`bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus`
- **退出码**：`0`
- **关键输出**：
  ```
  r6-differential-prepare: after 侧 = /home/kity/oclab/agateon/agate（真实工作树，含未提交改动；非 corpus）
  r6-differential: before=581369fc9d464b60692ebf71cdeb8605b9c3add9  after=/home/kity/oclab/agateon/agate
  [ALLOWED] check-gate:P8 TAG0042-config-and-enforcement rc 2->2 added=1 removed=1
  [ALLOWED] check-gate:P8 TAG0050-task-data-contract rc 2->2 added=1 removed=1
  r6-differential: legacy 任务 39 个，差异 2 条，未匹配 0 条
  ```
- **口径说明**：**after 侧 = 真实工作树**（P4 已提交 `9771e76` ⇒ 差分**包含**本次改动）；before 侧由 corpus（含 `.git` 的整仓副本）经 `git archive` 解析。**2 条差异均 `[ALLOWED]`（D13），`rc 2→2` 不变** ⇒ legacy 行为无破坏性变化。
- **隔离核验**：真实仓库仅被只读（`cp -a` 读取）；**跑前/跑后** `git status --porcelain` 一致（只含 agate-run 按设计追加的 `gate-events.jsonl` + 本 subagent 的 P5 产出/`runs/`），无额外污染。corpus 在 `/tmp/opencode/tag0051-r6-corpus`。
- **说明**：**未经 agate-run 白名单/账本路径**（该命令不在 `verify.commands` 白名单内）。

---

## 结论（供主 Agent 判 gate，非自证「已过」）

- 7 条命令**全部执行完毕**；退出码：`P5=1`（唯一红 = 预存/环境性 `test_bdd_43`）、`P5_consistency=0`、`P5_count=0`、`P5_ruff=0`、`P5_obligations=0`、`P5_sg6=0`、`P5_r6=0`。
- 正式口径 `P5` = `1 failed, 2958 passed, 2 skipped`；唯一失败 = **预存失败 `test_bdd_43`**（环境漂移，与本次改动无关，已登记 `known-failures.md`）。
- 未发现**本次改动引入**的新失败（run:1 的一次额外红 = 既有 flaky `DEBT0063`，隔离恒绿、run:2 未复现）。
- **自查 ≠ gate**：本报告不声称「P5 已过」，判定权在主 Agent（external-output-gate）+ CI backstop。
