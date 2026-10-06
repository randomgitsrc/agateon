---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: test-designer
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — batch3-agate-run（agate-run 执行层）

> 上游：`P1-requirements.md`（BDD-9 / BDD-10 / BDD-11 / BDD-12）
> + `P2-design.md` §1.1（M9/M10）、§4.2（执行层设计 + 平台分支）、§1.3 R4/R5、
> §6.1b（batch3 `tests_filter` / `output`）
> + `P3-dispatch-context-test-designer-batch3.md`。
> 本批为 TDD 红灯批：测试**先于实现**，当前 15 条全部红灯（红灯原因 = 被测模块/行为未实现，B 类）。
> batch3 是模式 5 串行链的第 3 批（依赖 batch2），只覆盖执行层，不碰 batch4-6。

> **`test_code_dir`**：`agate/tests/unit/`（声明于 frontmatter，单一来源）。

## 1. 测试文件

| 文件 | 说明 |
|---|---|
| `agate/tests/unit/test_agate_run.py` | BDD-9 / BDD-10 / BDD-11 红灯测试（新建） |
| `agate/tests/unit/test_events_ledger.py` | BDD-12 红灯测试（新建） |

> 既有相关测试（`test_check_events.py` 等）**不复用、不改动**——本批只新增 BDD-9..12 的红灯测试。
> `test_events_ledger.py` 与既有 `test_check_events.py` 互补：后者测 `check-events.py` 审计器本身，
> 前者测 **`agate-run` 写入 `cmd_run` 事件后链是否仍完整**（用 tmp_path 下的账本**副本**）。

## 2. BDD → 测试用例映射（1:1）

### BDD-9: agate-run 在不可绕开路径上执行项目命令 (Batch 3)

> Given 声明文件中定义了项目的验证命令
> When 主 Agent/Agent 需要执行验证命令
> Then 经 `agate-run` 执行（而非自由 `bash`），命令的退出码被如实传播（含 `pipefail` 语义）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B9-01 | `test_bdd_9_run_executes_declared_command_and_propagates_exit_code` | 经 agate-run 执行成功命令 rc=0 且捕获输出 | `agate-run.py` 不存在 ⇒ rc≠0（模块未实现） |
| TC-B9-02 | `test_bdd_9_run_propagates_nonzero_exit_code` | 命令 `exit 7` → rc=7（如实传播，不吞成 0） | 脚本不存在 ⇒ rc≠7（模块未实现） |
| TC-B9-03 | `test_bdd_9_run_posix_pipefail_propagates_left_side_failure` | POSIX：`<失败命令> \| tail` 经 pipefail → rc≠0；非 POSIX：退化输出含 WARNING | 脚本不存在 ⇒ rc≠0 断言失败（模块未实现） |
| TC-B9-04 | `test_bdd_9_run_nonposix_pipefail_degrades_with_warning` | 源码含 `set -o pipefail` 前缀 + 平台分支 + 退化 WARNING（review m-2） | 脚本不存在 ⇒ 无从检查（模块未实现） |

### BDD-10: agate-run 产出可比对的基线证据 (Batch 3)

> Given 首次执行某命令
> When 运行 `agate-run --baseline`
> Then 落盘 `.out` 证据文件；后续执行与之逐字节比对，差异被客观报出（可二值判定）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B10-01 | `test_bdd_10_baseline_writes_out_evidence_file` | `--baseline` rc=0 且项目内落盘 `.out`（含命令输出） | 脚本不存在 ⇒ rc≠0、无 `.out`（模块未实现） |
| TC-B10-02 | `test_bdd_10_subsequent_run_matches_baseline_no_diff` | 输出与基线一致 → rc=0（可二值判定） | 脚本不存在 ⇒ 前置 rc≠0（模块未实现） |
| TC-B10-03 | `test_bdd_10_baseline_diff_is_objectively_reported` | 输出偏离基线 → rc≠0 且输出含差异提示 | 脚本不存在 ⇒ 前置 rc≠0（模块未实现） |

### BDD-11: agate-run 证据文件被 ignore 检查覆盖 (Batch 3)

> Given `agate-run` 产出的 `.out` 证据位于项目内
> When 执行 ignore 检查
> Then 证据文件被 `.gitignore` 覆盖（`git check-ignore` 命中），否则报错

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B11-01 | `test_bdd_11_baseline_evidence_is_gitignored` | 证据被 `.gitignore` 覆盖时 `git check-ignore` 命中 | 脚本不存在 ⇒ 前置 rc≠0（模块未实现） |
| TC-B11-02 | `test_bdd_11_run_reports_error_when_evidence_not_ignored` | 证据**未**被覆盖 → rc≠0 且提示 ignore 问题 | 脚本不存在 ⇒ rc≠0 断言失败（模块未实现） |

### BDD-12: agate-run 写入 cmd_run 账本事件且不破坏哈希链 (Batch 3)

> Given `gate-events.jsonl` 是 append-only + `prev_hash` 链
> When `agate-run` 执行一次命令
> Then 追加一条 `cmd_run` 事件且 `prev_hash` 链连续（`check-events.py` 通过）；hook 一并暂存账本

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B12-01 | `test_bdd_12_cmd_run_event_appended` | 执行后账本新增 `event == "cmd_run"` 行 | 脚本不存在 ⇒ 未追加（模块未实现） |
| TC-B12-02 | `test_bdd_12_cmd_run_event_has_required_fields` | `cmd_run` 含命令 / 退出码 / 时间戳字段 | 脚本不存在 ⇒ 无事件（模块未实现） |
| TC-B12-03 | `test_bdd_12_ledger_hash_chain_preserved` | 追加后 `check-events.py` exit 0（链完整、ts 单调） | 脚本不存在 ⇒ 前置未追加 cmd_run（模块未实现） |
| TC-B12-04 | `test_bdd_12_cmd_run_event_uses_append_event_single_write_path` | 新行 `prev_hash == sha256(新增前尾行文本)`（走 append_event 链约定） | 脚本不存在 ⇒ 仅 1 行（模块未实现） |
| TC-B12-05 | `test_bdd_12_agate_run_source_uses_append_event_not_direct_write` | 源码引用 `append_event`，不直接以追加模式打开账本 | 脚本不存在 ⇒ 无从检查（模块未实现） |
| TC-B12-06 | `test_bdd_12_hook_stages_ledger` | pre-commit-gate.py 含「一并 git add 账本」逻辑 | hook 未实现账本暂存（行为未改） |

**BDD 覆盖核对**：BDD-9 ×4 + BDD-10 ×3 + BDD-11 ×2 + BDD-12 ×6 = **15 条用例**，
每条测试名引用对应 BDD 编号，可追溯到 P1 验收条件。

## 3. 红灯基线（自跑记录）

```
python3 -m pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q
→ 15 failed in 0.29s
```

15 条全部失败，失败原因均为 **AssertionError / 文件缺失**——属「被测模块未实现 / 行为未改」
（B 类）：`agate/scripts/agate-run.py` 不存在（子进程 `No such file` ⇒ rc≠0、无 `.out`、
无 `cmd_run` 事件），`pre-commit-gate.py` 无「账本 git add」暂存路径。
**非 SyntaxError、非第三方 import 失败**（A 类，已 grep 确认 0 命中），亦非「断言与测试数据矛盾」：
每条失败消息直指批 3 执行层产物的缺席。

| 用例 | 红灯类型 |
|---|---|
| TC-B9-01/02/03/04 | AssertionError（agate-run.py 不存在） |
| TC-B10-01/02/03 | AssertionError（agate-run.py 不存在） |
| TC-B11-01/02 | AssertionError（agate-run.py 不存在） |
| TC-B12-01/02/03/04/05 | AssertionError（agate-run.py 不存在） |
| TC-B12-06 | AssertionError（hook 无账本暂存逻辑） |

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py \
    agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py
→ exit 0（0 命中）
```

测试平台无关实现要点：
- 用 `tmp_path` / `git_repo` fixtures；`run_cli(python_exe, ...)`（不裸 `python3`）；
- 全文本 I/O 显式 `encoding="utf-8"`；
- 需要「系统临时目录」字面量时**运行时拼接**（`_TMP = "/" + "tmp"`），注释中也**不写字面量**；
- **不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本）——所有账本断言均在 `tmp_path`
  下的**副本**上进行（TC-B12-01..04），跑完 `git status --short` 确认仓库根无新增污染文件。

## 5. 与实现对象的关系（供 P4）

- **被测对象**：`agate/scripts/agate-run.py`（新增，含 `--baseline`、环境变量注入、
  `.out` 证据落盘 + 逐字节比对、`git check-ignore` ignore 检查、平台分支）、
  `agate/scripts/agate_common.py`（复用既有 `append_event` / `run_test_with_formatter` 的
  `set -o pipefail; ` 前缀写法）、`agate/scripts/pre-commit-gate.py`（hook 一并暂存账本）。
- **pipefail 写法口径（P2 §4.2，agate_common.py:747-756）**：用 `"set -o pipefail; " + cmd`
  **前缀** + `shell=True, executable="bash"`；**不能**写 `executable="bash -o pipefail"`
  （`executable` 是路径，实测抛 `FileNotFoundError`）。TC-B9-04 断源码含 `set -o pipefail` 前缀。
- **平台面（review m-2）**：TC-B9-03 按平台分支断言（`sys.platform != "win32"` 断 pipefail 生效；
  否则断退化 + WARNING，不静默报绿）；TC-B9-04 断源码显式平台分支 + WARNING 可观测。
- **账本链（P2 R5）**：`cmd_run` 事件**必须**经既有 `agate_common.append_event()`（唯一写路径）追加，
  否则破坏 append-only `prev_hash` 链；hook 一并暂存用 `git add`，**不直接写账本文件**。
  TC-B12-03 用副本账本跑 `check-events.py` 判链完整；TC-B12-04 断新行 `prev_hash` 自洽；
  TC-B12-05 断源码走 `append_event` 且无旁路直写。
- **账本定位约定**：测试经 `AGATE_TASK_DIR` env 指向 `tmp_path` 副本任务目录（供 P4 实现采用；
  若实现改用其他定位方式，P4 可在不改变 BDD 语义下对齐该注入点）。
- **P4 回归注意**：既有 `test_check_events.py` 不受本批影响（测审计器本身）；新增
  `test_events_ledger.py` 只测 agate-run 的写入侧。

## 6. 边界与不做

- 本批**只写测试**，不写实现（实现是 P4）。
- **只覆盖 batch3 的 BDD-9..12**，不碰 batch4-6（关卡分级 / CI 诊断 / 义务登记表）。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本）——所有断言均在 `tmp_path`/`git_repo` 内。
