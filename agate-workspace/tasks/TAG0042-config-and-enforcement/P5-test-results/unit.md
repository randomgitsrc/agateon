---
phase: P5
task_id: TAG0042
agent: verifier
type: test-results
created: 2026-10-06
---

# P5 技术验证结果 — TAG0042 项目形态命令化 + 规则脚本化

> 验证对象：HEAD `33413cf`（main，P4 全部 6 批 + 聚合文件已落）。
> 验证环境：dsh / Linux；`python3` = `/usr/bin/python3`；ruff = `~/.venvs/agate-dev/bin/ruff` 0.16.4。
> 命令逐条独立执行（遵守「`--strict` 反模式」），来源 `P2-design.md` §5 `gate_commands`。
> 输出不截断判断：每条命令先看全输出再汇总。

`[PROD_NOT_TOUCHED]` —— 全程仅只读代码 + 写本任务 P5 产出；未触达任何生产环境/服务/数据库。

---

## 1. `P5` — 全量测试

- 命令：`python3 -m pytest agate/tests/ -q --tb=no`
- timeout：600s（实跑 209.70s）
- **exit code：1**
- 汇总：**passed 2668 / failed 1 / skipped 2**（`1 failed, 2668 passed, 2 skipped in 209.70s (0:03:29)`）

失败清单（唯一 1 条）：

```
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```

### 失败判定：预存失败（与本次改动无关，环境/CLI 漂移）

- 该失败**不是**本任务引入。客观证据：
  1. 失败点在 `test_setup_agate_dir.py:308` 的**外部 CLI 子进程**调用 `opencode debug agent orchestrator`，
     返回 `rc=1`，stderr 明确：`ERROR Unknown subcommand "agent" for "opencode debug"` / `Did you mean this? agents`。
  2. 实测本机 CLI：`opencode debug agent orchestrator` → 打印顶层 `opencode debug` 帮助（子命令不存在）；
     `opencode debug agents` → 正常返回 `[]`。即本机 opencode CLI 已把 `debug agent <name>` 改为 `debug agents`，
     `SETUP.md` 该验证命令随**外部 CLI 漂移**过期（非本仓代码问题）。
  3. 本任务（`cb52bef^..HEAD`）**未修改**该测试文件或 `SETUP.md`：`git diff --name-only cb52bef^..HEAD` 中无
     `test_setup_agate_dir.py` / `SETUP.md`；`git log -- agate/tests/unit/test_setup_agate_dir.py` 最后一次改动为
     `5d19828`（DSH preset 修复），`git merge-base --is-ancestor 5d19828 cb52bef` 为真 ⇒ 该文件早于本任务基线。
  4. 该用例的 agate 侧断言（软链创建、`AGATE_DIR` 求值等）均通过，仅在与 opencode 外部 CLI 交互处失败。

⇒ **标注「预存失败：test_bdd_43（与本次改动无关，环境/CLI 漂移）」**，不计入本任务回归。
（另注：本任务 batch2 虽改了 `agate/scripts/agate-setup.py`，但该用例失败位置是外部 `opencode debug agent`
子命令，与 `agate-setup.py` 内容无关。）

---

## 2. `P5_consistency` — 协议一致性

- 命令：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
- timeout：120s
- **exit code：0**
- 汇总：**0 ERROR**（PASS 12 项）；WARNING 408 条，**全部来自冻结文件**：
  `CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 405`。
- 逐 CHECK：CHECK 3/4/6/7/8/9/11/12/13/14/15 = PASS；CHECK 1/2/10 = WARN（冻结文件，按设计不改）。

> 观察（非失败，不影响 gate）：本设计 §8 `consistency_baseline` 声明为 398 WARNING
> （CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 395）。本次实跑为 **408 WARNING**
> （CHECK2-refs 405，+10）。差异全部落在 `tasks/` 等**冻结文件**的引用面（CHECK2-refs），
> 与「本任务新增 P3/P4 任务文档带来的新引用」一致；`--strict-errors-only` 判据下 exit 0，
> 不构成 ERROR，不阻断 P5。已如实记录供主 Agent/P7 复核。

---

## 3. `P5_structure` — 结构一致性

- 命令：`python3 agate/scripts/check-structure-consistency.py`
- timeout：120s
- **exit code：0**
- 全量输出（7 项全 OK）：

```
S1-phases: OK
S2-workflow: OK
S3-cards: OK
S4-scripts: OK
S5-schema: OK
S6-references: OK
S0-numbers: OK
```

---

## 4. `P5_ruff` — 静态检查

- 命令：`~/.venvs/agate-dev/bin/ruff check agate/`
- timeout：120s
- **exit code：0**
- 输出：`All checks passed!`（ruff 0.16.4，与 CI 锁版一致）

---

## 5. `P5_platform` — 平台假设静态扫描

- 命令：`python3 agate/scripts/check-platform-assumptions.py`
- timeout：120s
- **exit code：0**
- 输出：（空）—— 0 命中，无平台假设违规。

---

## 6. 汇总

| key | 命令 | exit | 关键汇总 | 判定 |
|---|---|---|---|---|
| `P5` | `pytest agate/tests/ -q --tb=no` | **1** | passed 2668 / failed 1 / skipped 2 | failed=1 **全部为预存失败（test_bdd_43，环境/CLI 漂移）** |
| `P5_consistency` | `check-protocol-consistency.py --strict-errors-only` | **0** | 0 ERROR / 408 WARNING（全冻结） | PASS |
| `P5_structure` | `check-structure-consistency.py` | **0** | S0-S6 全 OK | PASS |
| `P5_ruff` | `ruff check agate/` | **0** | All checks passed! | PASS |
| `P5_platform` | `check-platform-assumptions.py` | **0** | 0 命中 | PASS |

- **本任务新增回归失败：0**
- **预存失败：1**（`test_bdd_43_opencode_registration_and_debug_agent`，环境/CLI 漂移，与本次改动无关）
- `ui_affected: false` ⇒ 无 `P5_e2e`（未执行符合声明）。
- 测试环境隔离：全量 pytest 使用 pytest `tmp_path`/隔离 fixture，未触达生产库/服务；前后 `git status` 无代码改动
  （工作区仅本任务元数据 + P5 产出）。

### 签名（供主 Agent N5 校验）

```
passed 2668
skipped 2
failed 1
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
