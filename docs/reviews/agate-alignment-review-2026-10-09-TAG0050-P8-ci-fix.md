---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "修复 TAG0050 CI 两处真缺陷：agate-ci-verify.py 账本路径过滤收窄为任务账本（新增 _is_task_ledger_path）；两处 subprocess text=True 补 encoding='utf-8'"
files_changed:
  - agate/scripts/agate-ci-verify.py
  - agate/tests/integration/test_tag0050_ci_replay.py
  - agate/tests/unit/test_tag0050_obligations.py
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/tasks/TAG0050-task-data-contract/retrospective.md
  - agate-workspace/tasks/TAG0050-task-data-contract/P4-progress.md
---

# 协议-脚本对齐审查（TAG0050 P8 CI 两处真缺陷修复）

> 审查对象：PR #408 上未提交的两处真缺陷修复。触发面 = `agate/scripts/agate-ci-verify.py`（SELF-GATE）。
> 方法：仓外全量副本（含 `.git`）独立复跑；改前红/改后绿双向证据；端到端真脚本复现 CI。
> 环境隔离：`[PROD_NOT_TOUCHED]` —— 只在仓外一次性副本 `/tmp/opencode/tag0050-p8review-repo` 上做变异/复跑，未对真实仓库执行任何写仓命令，未编辑被评审文件。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（附 1 条措辞小瑕，见下） |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（`retrospective.md` frontmatter `execution_issues` 与正文条数不一致） |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（附 3 条轻微数字漂移，见下） |

**需修复项：A3（1 条）。** 其余 ALIGNED。

## dispatch 范围 6 条逐条对照

| 范围 | 问题 | 结论 |
|------|------|------|
| 1 | `_is_task_ledger_path` 口径正确性（恰好排除非任务账本、不误伤真账本、删除/改名/evil merge） | 全部独立验证通过 —— ALIGNED |
| 2 | 回归用例改前红 + 既有 FAIL 用例仍绿 | 双向验证通过 —— ALIGNED |
| 3 | Windows 编码修复覆盖全部同类 + 与既有写法一致 | 覆盖完整、写法一致 —— ALIGNED |
| 4 | 缺口登记（DEBT0058 + 账本路径缺口）、编号、check-debt | 已登记、编号正确、0 错 —— ALIGNED |
| 5 | `retrospective.md` 两条补充与事实一致 | 事实一致，但 frontmatter 漏登 1 条 —— **MISALIGNED** |
| 6 | SELF-GATE 清单（consistency 0 ERROR；全量 pytest 除环境漂移 1 条外 0 failed） | 通过 —— ALIGNED |

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

**设计意图**（`P4-implementation-G1.md:126-129`）：
> **K1（BLOCKER）**：`agate-ci-verify.py` 的「账本最终状态检查」与逐提交回放**解耦**……合并提交（evil merge）删除账本 → `FAIL 账本` + rc=1。

设计意图是「对**任务账本**做最终状态检查以防降回 legacy」。修复前 `_ci_ledger_checks` 用 `path.endswith(_LEDGER_NAME)` 判账本（`agate-ci-verify.py` 旧 :315），未限定 `agate-workspace/tasks/` 前缀，把黄金夹具当真实账本。该过宽过滤**已在 G1 复审**记为已知偏离（`P4-review-rereview-G1.md:198-235`，[MEDIUM] 非阻断，首选修法 = 加 `tasks` 前缀 + 回归用例）。

**脚本实现**（`agate/scripts/agate-ci-verify.py:210-221`）：
```python
def _is_task_ledger_path(path):
    if not path.startswith(_TASKS_PREFIX) or not path.endswith(_LEDGER_NAME):
        return False
    parts = path[len(_TASKS_PREFIX):].split("/")
    return len(parts) == 2 and parts[1] == _LEDGER_NAME
```
`_ci_ledger_checks` 的 `if not path.endswith(_LEDGER_NAME)` 改为 `if not _is_task_ledger_path(path)`（:332），函数 docstring（:306-307）同步。

**结论**：ALIGNED —— 修复使脚本与设计意图（仅任务账本）一致，且正是 G1 复审的「首选」修法。
**措辞小瑕（不阻断）**：模块 docstring :34 仍写「对 `<base>..HEAD` 中**全部**变化过的账本……」，未加「任务」限定；函数 docstring :210-217 已精确。建议顺手在 :34 补「任务」二字（可选）。

### A2: 脚本→文档对齐 —— ALIGNED

本修复是脚本内部缺陷修正，未引入新的协议规则或字段。相关「文档」为任务内设计（`P4-implementation-G1.md` §2.4）与脚本自身 docstring（已同步）。无协议文档需改。**ALIGNED**。

### A3: 一致性连锁 + 反向传播 —— **MISALIGNED**

**连锁（已核，无需改）**：
- `_ci_level_checks`（:387-419）已用 `path.startswith(_TASKS_PREFIX)`（:407）收窄，夹具路径天然排除，**无同类误判**（与 `P4-progress.md` 的实现说明一致）。
- `_changed_task_dirs`（:194-207）与 `_is_task_ledger_path` 共用 `_TASKS_PREFIX`，口径一致。
- 其他账本路径识别脚本（`agate-doctor.py`、`check-ledger-pollution.py`、`pre-commit-gate.py`、`agate-state-set.py`）均按 `task_dir` 拼接，或已显式覆盖 fixtures（`check-ledger-pollution.py:55` 含 `:(glob)agate/tests/fixtures/**/gate-events.jsonl`），**无同类过宽过滤**。

**MISALIGNED —— `retrospective.md` frontmatter 与正文不一致**：

frontmatter（`retrospective.md:12-16`）`execution_issues` 列出 **4** 条：
> - "主 Agent 两次在 dispatch-context 散文里写入会触发扫描的字面量，自造误报"
> - "G3 整改子任务返回中间状态（全量测试仍在后台跑）而主 Agent 未即时核对"
> - "主 Agent 一度以「会话边界」为由准备停止推进（协议无「会话边界」概念）"
> - "写 TAG0050 批 A4 测试时未按平台无关硬约束为 subprocess.run(text=True) 指定 encoding，Windows CI 抓出"

正文「### 执行错误」（`retrospective.md:119-151`）含 **5** 条 `- 问题：`，多出的一条为本批新增（:143-151）：
> **TAG0050 自身交付的 CI 兜底（A2 的 `agate-ci-verify.py`）在 PR CI 上抓出 K1 修复的真缺陷** …… 归因层面: 执行错误

模板（`agate/assets/templates/retrospective-template.md:27-28`）将 frontmatter 定义为「本次复盘归因为『执行错误』的问题条目（简述）」——即正文问题条目的机器可解析镜像（供 `agate-feedback.py` 提取）。对照机制缺口侧：frontmatter `mechanism_issues` = 8 = 正文机制缺口 8 条（一致）。执行错误侧 frontmatter 4 ≠ 正文 5。

**差异描述**：本批新增的「CI 兜底抓出 K1 账本路径缺陷」执行错误条目只落正文（:143），未同步进 frontmatter `execution_issues`（:12-16）。
**建议修复方向**：在 `execution_issues` 补一行，例如
`- "K1 账本路径过滤过宽（endswith）把测试夹具误判为任务账本，由本任务自身 CI 兜底抓出"`，
使 frontmatter 与正文条数一致（一处一行改动）。

**反向传播观察（非本批引入，不阻断）**：
- G1 复审 `P4-review-rereview-G1.md:224-229` 附带观察：`_check_one_ledger_text` 未把回放协议根透传给 `check_ledger_events`，本机有 `~/.agate` 且仓库无 `.agate-version` 时会解析到**已安装稳定版**的 LEVELS（可能多报）。该缺口**未登记**进 `tech-debt.md`/`retrospective.md`（grep 0 命中），属本次范围外的存量项，建议后续登记或修。
- 全仓 AST 扫描（273 个 `.py`）另有 **13** 处 `subprocess.run(..., text=True)` 无 `encoding=`（`agate_dispatch_route.py` 4、`check-protocol-consistency.py` 1、`test_release_workflow.py` 3、`test_platform_setup.py` 5、`test_agate_cmdstream_adapters.py` 2）。均**非 TAG0050 触及文件**，属 DEBT0058 登记的「扫描器未覆盖该类」之存量面；本批不要求处理。

### A4: 测试覆盖 —— ALIGNED

新增用例 `agate/tests/integration/test_tag0050_ci_replay.py::test_non_task_ledger_fixture_not_checked`（:132-165），断言 `"FAIL 账本" not in r.output` 且 `r.returncode == 0`。

**改前红（仓外副本，变异 `_is_task_ledger_path` → `return path.endswith(_LEDGER_NAME)`）**：
```
FAILED agate/tests/integration/test_tag0050_ci_replay.py::test_non_task_ledger_fixture_not_checked
E  AssertionError: CI 真缺陷：非任务账本（测试夹具）不得被当真实账本判 FAIL
E      FAIL 账本: agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl: task_upgraded 的等级 0 未登记（第 2 行）
E      FAIL 账本: ... task_upgraded 等级未严格递增（1 → 0，第 2 行）
1 failed in 0.11s
```
**改后绿（修复版）**：新用例 + 既有 FAIL 用例 BDD-28（删账本）/BDD-29（手写低等级）/K1（evil merge 删账本）：
```
4 passed in 2.60s
```
**端到端真脚本复现（副本，base=merge-base `720c97d3`）**：
- 修复版 → `回放完成：22 个提交，失败 0 个` / `PASS: 逐提交回放全部通过` / **RC=0**（无 `FAIL 账本`）；
- 还原 `endswith` 版 → 3 条 `FAIL 账本: agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl` / **RC=1**（与 CI 日志一致）。

**路径分类判别力（11 例，独立探针）**：真任务账本 → True；`agate/tests/fixtures/**/gate-events.jsonl`、`tasks/gate-events.jsonl`（无子目录）、`tasks/TAG1/sub/gate-events.jsonl`（嵌套）、`.../gate-events.jsonl.bak`、`docs/...`、`gate-events.jsonl`、`.state.yaml` → False。`BAD_COUNT=0`。

**删除/改名/evil merge 独立探针（副本）**：
- 改名 `TAG0001 → TAG0002`（`--no-renames` 输出被删源路径）：被删源路径**仍识别为任务账本**并报 `含创建/迁入事件的账本被删除/截空/改写` → 拦下 ✓
- 非任务夹具（非法内容）→ 不报 ✓
- evil merge（合并提交删真账本）→ 报 FAIL ✓

**全量 pytest（副本，最近一次实跑）**：
```
1 failed, 2863 passed, 3 skipped in 302.68s (0:05:02)
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
唯一 failed = 本机 `opencode` CLI 无 `debug agent` 子命令（`rc=1: Unknown subcommand "agent"`），属**既有环境漂移**，文件未被 TAG0050 触及。新回归用例计入 `2863 passed`。**除该 1 条外 0 failed。**

**结论**：ALIGNED —— 新用例改前红、改后绿、判别力充分；既有 FAIL 用例仍绿；全量 0 意外失败。

### A5: 下游影响 + 文档传播 —— ALIGNED

- `agate-ci-verify.py` 的 `_ci_ledger_checks` 系 **v0.80.0 新增**（`~/.agate/current` = v0.79.0 的脚本无此函数，实为「CI gate 重跑兜底」旧版）。本修复落在**未发布**的 v0.80.0 特性内：README badge = v0.80.0、CHANGELOG `[0.80.0] - 2026-10-09` 已提交（`9bfef64d`），但**无 `v0.80.0` tag**（release PR #408 未合）。⇒ 修复折叠进同一未发布特性，**无需单独 CHANGELOG 条目**。
- 行为影响：仅**收窄**被检查路径（非任务账本不再计入），是纯修正，无破坏性变更；下游项目 gate-backstop 不再因夹具假红。
- 无新增协议字段/规则，故无 `orchestrator-template.md`/`dispatch-protocol.md`/角色文件等传播需求。

**结论**：ALIGNED。

### A6: 锚点表覆盖 —— ALIGNED

未新增/改名脚本、未新增协议规则。CHECK 9 锚点表无需更新（`check-protocol-consistency.py:951` 仅有一处退役名注释）。`check-protocol-consistency.py` 实跑 **0 ERROR / 412 WARNING**，RC=0。**ALIGNED**。

### A7: 设计原则一致性 —— ALIGNED

变更未引入新架构决策。相关 ADR（`agate/adr.md:420,433`）确立「真正的防造假安全边界在 gate 链（账本 + 独立 judge）」。修复使账本检查**更精确地**作用于任务账本，符合该原则，无 ADR 需补。**ALIGNED**。

### A8: 声称-命令绑定 —— ALIGNED（附轻微漂移）

| 声称（出处） | 命令 | 结论 |
|---|---|---|
| `test_agate_ci_verify.py + test_tag0050_ci_replay.py → 24 passed`（P4-progress） | `pytest 两文件 -q` | ✅ 24 passed |
| `test_tag0050_obligations.py → 6 passed`（P4-progress） | `pytest 该文件 -q` | ✅ 6 passed |
| `count-tests → 2867`（P4-progress） | `bash agate/tests/scripts/count-tests.sh` | ✅ 总计：2867 |
| `check-debt.py → RC=0`（P4-progress） | `python3 agate/scripts/check-debt.py …`（repo 与稳定版均跑） | ✅ rc=0 |
| `ruff → All checks passed`（P4-progress） | `~/.venvs/agate-dev/bin/ruff check 三文件` | ✅ All checks passed |
| `AST 扫描 … TOTAL_HITS=2`（P4-progress） | 对 24 个 TAG0050 触及 `.py` 的 AST 扫描 | ✅ pre-fix 2（`:54`/`:279`）/ post-fix 0 |
| 改前红 `1 failed`；改后绿 CI_RC=1→0（P4-progress） | 副本变异 + 端到端真脚本 | ✅ 复现一致 |
| `retrospective … 技术债 7→8 条` | `grep DEBT0051..0058`（均 `source: retrospective`） | ✅ 8 条 |

**轻微数字漂移（不构成无据声称，仅时效漂移）**：
1. P4-progress 两处称 consistency「**410** WARNING」，实跑 **412**（冻结警告随新增引用增长）——ERROR 恒为 0。
2. P4-progress 称扫描范围「**23** 文件」，实为 **24** 个 `.py`（29 触及路径 − 5 非 `.py`）——命中数 2 一致，不影响结论。
3. `retrospective.md:42-43` 事实基线写「2863 passed / **2 skipped**；count-tests **2866**」——系 P6/P7 期快照；本批 +1 用例后 count-tests=2867、实跑 skipped=3。属历史快照，非无据声称。

**结论**：ALIGNED —— 所有数字/结论类声称均可绑定到产出命令；上述为轻微时效漂移，建议但不强制同步。

## 独立验证证据清单（命令 + 输出摘要）

```
# 仓外全量副本（含 .git，忠实协议解析）
cp -a /home/kity/oclab/agateon/. /tmp/opencode/tag0050-p8review-repo/
# 1) 修复版基线：新用例 + BDD-28/29/K1
pytest .../test_tag0050_ci_replay.py::{test_non_task_ledger_fixture_not_checked,
  test_bdd_28_...,test_bdd_29_...,test_k1_...} -q            → 4 passed
# 2) 改前红：变异 _is_task_ledger_path → endswith
pytest ...::test_non_task_ledger_fixture_not_checked -q      → 1 failed（FAIL 账本 fixture）
# 3) 端到端真脚本：修复版 RC=0 / 还原版 RC=1（3 条 FAIL 账本 fixture）
python3 agate/scripts/agate-ci-verify.py --base 720c97d3...  → 修复版 22 提交 0 失败 RC=0；
                                                              还原版 fixture FAIL 账本 RC=1
# 4) 路径分类 11 例探针 → BAD_COUNT=0
# 5) 改名/夹具/evil-merge 探针 → ALL PROBES PASS
# 6) AST text=True 无 encoding：pre-fix(HEAD) 2 命中(:54/:279) → post-fix 0（24 触及 .py）
# 7) Windows 语义模拟 LC_ALL=C PYTHONUTF8=0：pre-fix 1 failed(UnicodeDecodeError 'ascii' 0xe4)
#    / post-fix 1 passed
# 8) check-protocol-consistency.py → 0 ERROR / 412 WARNING，RC=0
# 9) check-debt.py（repo + 稳定版）→ rc=0
# 10) ruff 0.16.4 check 三文件 → All checks passed
# 11) 全量 pytest（副本，干净）→ 1 failed(环境漂移) / 2863 passed / 3 skipped
```

## 环境隔离

`[PROD_NOT_TOUCHED]` —— 全部变异、复跑、端到端均在仓外一次性副本 `/tmp/opencode/tag0050-p8review-repo`（含 `.git`）与 pytest `tmp_path` 内完成；未对真实仓库执行 `git checkout/reset/clean/add/commit` 等写仓命令，未编辑任何被评审文件。真实仓库仅跑过只读的 `check-protocol-consistency.py` / `check-debt.py` / `ruff` / 目标 pytest（只写 `tmp_path`）。

## 闭环

| 结论 | 项 |
|------|----|
| ALIGNED | A1、A2、A4、A5、A6、A7、A8 |
| **MISALIGNED（必须修复）** | A3：`retrospective.md` frontmatter `execution_issues` 漏登「CI 兜底抓出 K1 账本路径缺陷」执行错误条目（补 1 行即可） |
| NEEDS_HUMAN_REVIEW | 无 |
