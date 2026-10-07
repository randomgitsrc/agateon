---
agent: cso
phase: P4
task_id: TAG0050
parent: P4-implementation.md
trace_id: TAG0050-P4-20261007
type: review
status: rejected
---

# P4-review-cso — TAG0050 批 A1 安全维度独立评审

- **评审对象**：TAG0050 批 A1（契约等级 + 账本完整性 + 任务初始化 + 生效等级）的未提交实现
  （HEAD `1d5aab2`，分支 `feat/TAG0050-task-data-contract`）。
- **范围**：`P4-dispatch-context-cso-A1.md` 的 6 个重点核验项；不重做设计，只审安全边界。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本**上做可复现验证；不改被评审文件、不写仓。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/` 下的 git 仓副本与
  `mktemp` 目录进行；真实仓库 `git status --porcelain` 评审前后一致（另见「验证留痕」）。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **HIGH**（其中 1 项构成 A1 安全目标的 BLOCKER） |
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 3 |
| 是否阻塞发布 | **是** —— 账本「不可删」保证可被一次 `git mv` 绕过，使任意非 legacy 任务降回 legacy，重开 F3b/F3c（A1 宣称已修的判定改写路径） |

## 二、6 个重点核验项逐条结论

| # | 核验项 | 结论 |
|---|---|---|
| 1 | 判定依据不可改写（所有 `requirement_active` 消费方已改） | **代码消费方全部已改 ✓，但信任锚可被摘除 ✗** —— 见 F-1 |
| 2 | 账本完整性七规则（含绕过路径） | **不通过** —— 规则 4 有 rename 洞（F-1）、规则 7 有删除 `.state.yaml` 洞（F-3） |
| 3 | 等级机制「不追溯」（F3） | **通过** —— 见 §三 |
| 4 | PROD_TOUCHED 扫描面偏离（宁可多拦 vs 漏拦） | **偏离方向正确（多拦），但 F4 粗体漏拦仍在、且被新面继承** —— 见 F-4 |
| 5 | 兼容承诺 §8（legacy 退出码/ERROR 集不变） | **check-gate 面通过；pre-commit 面未验证、§8 第 12 项未交付** —— 见 F-2 |
| 6 | R6 差分脚本自身可信（自核验 + 负向用例） | **负向用例成立 ✓，但存在不可达死规则，可信度不完整** —— 见 F-2/F-5 |

## 三、通过项（可复现证据）

### 核验项 1：`requirement_active` 消费方全覆盖

逐一核对 `judge` / `evidence_ref` 的判定点，A1 后均改依契约，legacy 分支保持原逻辑：

- `agate/scripts/check-gate.py:764`（`gate_p1`）、`:1250`（`gate_p65`）：`requirement_active(..., "judge", ...)`，
  非 legacy 时不再读 `judge.enabled` / `created` 日期门槛；legacy 走 `elif not judge_enabled` 原路径。
- `agate/scripts/pre-commit-gate.py:169`（`_judge_enabled`）：契约优先，legacy 回退。
- `agate/scripts/agate-next.py:280`（`_p6_judge_advance`）：F1 补齐点，契约优先（首评漏改）。
- `evidence_ref` 单点：`agate/scripts/agate_common.py:1707` `is_new_task_for_evidence_ref` 改依契约，
  两消费方 `check-p6-evidence.py` / `check-p6-provenance.py` 自动跟随。

`grep` 全仓确认无其它「判 judge 是否必需」的消费点（`judge_required_since` 仅出现在 legacy 回退路径）。
**但**：这些消费方都以 `task_level(task_dir) is not None` 为「非 legacy」前提，而 `task_level`
依赖账本；账本一旦被 rename 摘除即全部回退旧逻辑 —— 见 F-1。

### 核验项 3：等级机制不追溯存量任务（F3）

`check_ledger_events` 只校验「等级已在 LEVELS 登记」；「等级 = 当前等级」只存在于
`pre-commit-gate.py` 新建目录分支（`agate/scripts/agate_common.py:1963` `_level_registration_errors`
的注释与实现一致）。验证：

```
# 副本上登记 level-2（current=2），对存量 level-1 非 legacy 任务跑 CI 路径：
$ AGATE_ROOT=<fake> python3 agate/scripts/check-events.py <task: task_created contract_level=1>
GATE EVENTS: 账本审计通过（1 行，哈希链完整，ts 单调，judge 轮次×0）
rc=0
# 对照：level=3 未登记 → rc=1（fail-closed 仍在）
```

真实仓库实跑 `pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q` = **26 passed**
（含 `test_f3_current_level_2_existing_level_1_passes`、`test_f1_p6_judge_advance_uses_contract`），
且跑前/跑后 `git status --porcelain` **完全一致**（`-p no:cacheprovider` + `PYTHONDONTWRITEBYTECODE=1`）。
**结论：通过。**

### 核验项 5/6：R6 负向用例与正向差分

```
# 正向（干净 clone corpus，after=本 checkout agate/）：
r6-differential: legacy 任务 39 个，差异 0 条，未匹配 0 条   → rc=0
# clone 跑后 git status --porcelain 为空
# 负向 1（corpus 脏）：
bash r6-differential.sh --corpus <真实仓（有未提交改动）>  → rc=1（自核验拦截）
# 负向 2（allowlist 缺必需规则 D12）：
bash r6-differential.sh --corpus <clone> --allow <缺 D12 的副本> → rc=1
```

负向用例成立、正向 0 差异 —— 对 **check-gate 面**的 §8 兼容承诺成立。缺陷在覆盖范围，见 F-2。

## 四、发现（按严重性降序）

### F-1 HIGH（阻塞）：账本「不可删」规则被 `git mv` 绕过 → 任务静默降回 legacy

- **位置**：`agate/scripts/pre-commit-gate.py:322-333`（规则 4）。循环
  `for entry in entries: if len(entry) != 2 or entry[0] != "D": continue` —— 只处理 **D（删除）**
  状态；`git mv` 产出的是 **R（改名）** 三元组，被无条件跳过。规则 3/5 只在账本**被暂存**时触发，
  改名走账本不在暂存集，全部不触发。
- **影响**：`git mv gate-events.jsonl <任意名>`（同目录 `.bak`、或移到别的目录）后，
  `read_ledger_events` 返回 `[]` → `task_level()` 返回 `None` → **该任务在所有消费方眼中变 legacy**，
  于是 `judge` 回退到可写的 `judge.enabled`（重开 F3b）、`evidence_ref` 回退到可回填的 `created`
  日期（重开 F3c）。这正是 A1 宣称已修复的「判定依据可改写」路径，也正是设计 §2.3 规则 4 明文
  要防的「降回 legacy」（`docs/design-notes/design-tag0050-task-data-contract.md:166`）。
- **可复现证据**（仓外副本 `/tmp/opencode/cso-scratch`）：

  ```
  # 种子任务：.state.yaml(phase P5) + gate-events.jsonl(task_created)，已提交
  $ git rm -q agate-workspace/tasks/TAG0001/gate-events.jsonl
  $ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py
  GATE: 含创建/迁入事件的账本被删除（…）——不得删除/截空/移走（防止降回 legacy）   rc=1  ✅ 删除被拦
  $ git reset --hard; git mv gate-events.jsonl gate-events.bak
  $ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py     rc=0  ❌ 改名放行
  $ git reset --hard; git mv gate-events.jsonl agate-workspace/tasks/TAG0002/gate-events.jsonl
  $ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py     rc=0  ❌ 移走放行
  # 且 CI 路径同样放行：
  $ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/check-events.py <task>
  GATE EVENTS: gate-events.jsonl 不存在（合法态，历史任务/首次运行跳过）          rc=0  ❌
  ```

- **设计口径澄清**：设计 §2.3 规则 4 写「被删除、截空或**移走**（不含改名）时 → ERROR」。
  其中「不含改名」应理解为**目录级改名**（`git mv` 整个任务目录，账本随目录到新路径、仍属于该任务），
  规则 1 的「账本由 HEAD 中某个路径改名而来则沿用原任务」正是这个语义。实现把**账本文件自身**的
  改名也一并豁免，与规则 4 的「防止降回 legacy」目的相悖。
- **建议修复（最小）**：规则 4 对 `entry[0]=="R"` 且 **源路径是账本** 的条目也要处理 ——
  仅当改名目标是**同一任务目录下**的账本路径（目录改名情形）才豁免；否则按删除判 ERROR。
  或加一条不变量：任务目录在 HEAD 有创建事件、而当前/暂存后 `task_level()` 变 `None` → ERROR。
  修复后应补一个负向用例（`git mv gate-events.jsonl` → rc=1），并纳入 R6（但 R6 当前跑不到 pre-commit，见 F-2）。

### F-2 MEDIUM：R6 差分脚本无法覆盖 pre-commit，§8 第 12 项未交付

- **位置**：`docs/design-notes/r6-differential.sh:249-250`（`_run_gate` 只跑 `check-gate.py`）、
  `:321`（`diff["gate"] = "check-gate:" + phase`）、`:267`（`if gate and gate not in diff["gate"]`）。
- **事实**：`r6-allowlist.yaml` 中 `gate: pre-commit` 的规则 **D01/D04/D06/D07/D12** 永远无法匹配
  （`"pre-commit"` 不可能是 `"check-gate:Pn"` 的子串）；D08/D09 同理。`required_ids` 只校验规则
  **存在于 YAML**，不校验**可达/可匹配**，故负向用例「删 D12 → rc=1」通过，但 D12 在场也从未真正
  比对过 pre-commit 行为。
- **影响**：§8 兼容承诺的「gate 退出码与 ERROR 集合不变」只被**部分**机械验证 —— 覆盖 check-gate
  （39 个 legacy 任务、0 差异），**未覆盖** pre-commit（A1 在 `pre-commit-gate.py` 新增了账本步骤、
  全局面 PROD_TOUCHED 扫描、规则 7 重跑）。而设计 §8 第 12 项（`…design-…:617`）明确要求
  「R6 差分须**单独统计** legacy 新增 PROD_TOUCHED ERROR 并逐条列出」——交付物未提供该统计，
  P4-implementation §6 的 R6 结果只覆盖 check-gate。
- **附带**：`_rule_matches` 从不读 `task_scope`，D03 的 `specific:T090` 作用域形同虚设（过宽匹配）。
- **建议**：R6 增加一条 pre-commit 路径（或在 `_run_gate` 中按规则 gate 前缀分派 hook 回放），
  并把 §8 第 12 项的新增 PROD_TOUCHED ERROR 单独列出；或显式声明「A1 的 R6 只承诺 check-gate 面」
  并在 §8 记明第 12 项由批 A2 的 CI 回放承担（若确如此，需在设计里写明，不能默认）。

### F-3 MEDIUM：删除 `.state.yaml` 可绕过 PROD_TOUCHED 全局面扫描

- **位置**：`agate/scripts/pre-commit-gate.py:455-456`（全局面扫描跳过「有暂存 `.state.yaml`」的任务，
  委托主循环 2g.0）+ `:515-517`（主循环 `for state_file in state_files: if not os.path.isfile(...): continue`）。
- **事实**：当 `.state.yaml` 以**删除**方式暂存时，`os.path.isfile` 为假 → 主循环跳过该文件（2g.0 不执行）；
  同时全局面扫描因 `.state.yaml` 在 `state_files_rel` 中而 `continue`。两条路径互相让路 → 该任务目录的
  暂存文件**完全不被 PROD_TOUCHED 扫描**。
- **可复现证据**（`/tmp/opencode/cso-scratch5`）：

  ```
  $ git rm -q agate-workspace/tasks/TAG0001/.state.yaml      # 目录内保留其它文件
  $ <写入 P5-verification.md 含 [PROD_TOUCHED] 并 git add>
  $ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py   rc=0  ❌ 安全门未拦
  ```

- **性质**：这不是 A1 引入的回归（A1 前同样不扫），但 A1 规则 7 声称「**每个**有暂存文件的任务目录
  都检查」并不成立，安全门仍有洞。建议全局面扫描对「暂存了 `.state.yaml` 删除」的任务目录也补扫。

### F-4 LOW：安全门粗体写法仍漏拦 / `[PROD_TOUCHED]: 无` 仍误拦（F4 未在 A1 修复，新面继承同一弱正则）

- **位置**：`agate/scripts/pre-commit-gate.py:231` `_PROD_TOUCHED_RE = r"^\s*-?\s*\[PROD_TOUCHED\]"`
  与 2g.0 的 `:630` 内联正则**逐字相同**。
- **可复现**（`/tmp/opencode/cso-scratch2`）：`**[PROD_TOUCHED]** 接触生产` → rc=0（**漏拦**）；
  `[PROD_TOUCHED]: 无` → rc=1（**误拦**）。二者即设计 §0 记载的 F4 两向判错。
- **归属**：F4 的修复被设计分派给**批 C**（§4，`design-…:671`），不在 A1 范围。A1 只把扫描面从
  `*.md` 扩到「任务目录内全部暂存文件」（实测非 md 文件的 `[PROD_TOUCHED]` 已被拦，方向正确）。
  记录此项是为了提示：**新全局面复用了同一弱正则**，F4 未闭合前「宁可多拦」只是部分成立。

### F-5 LOW：R6 自核验只在运行前、不在运行后

- **位置**：`docs/design-notes/r6-differential.sh:62-76`（`git status --porcelain` 检查在运行前）。
- **事实**：脚本对每个 corpus 只在**运行前**核验干净；运行后不复查。`check-gate.py` 自身无写副作用
  （仅 stderr），但其子脚本（如 `check-judge-verdict.py` 会追加账本事件，见 AGENTS.md 工作流 0a）
  在特定条件下会写。legacy 任务下 `gate_p65` 早退、实测 clone 跑后仍干净，风险低；但「防止跑差分把
  真实仓库弄脏」的承诺仅靠**前置**检查并不闭合（若 `--corpus` 指向干净的真实仓，脚本仍会运行并在
  子脚本写数据时弄脏它）。建议运行后再核验一次 `git status --porcelain`。

### F-6 LOW（信息）：新建目录在控制态（PAUSED）可跳过规则 1/2

- **位置**：`agate/scripts/pre-commit-gate.py` 规则 1/2 的 `phase not in ("PAUSED","READY","DONE")` 例外。
- **可复现**：新目录以 `phase: PAUSED` 提交（无创建事件）→ rc=0（规则 1/2 均跳过）。但后续
  `PAUSED → P0` 被 `check-state-transition` 拦（`GATE P0: 无法解析阶段序号（old_phase='PAUSED'）`），
  故实际无法借此把新任务「养成」legacy 并继续推进，影响有限。该例外是主 Agent 已接受的 DESIGN_GAP，
  此处仅记录边界。

## 五、STRIDE 矩阵（针对 A1 改动面）

| 威胁 | 面 | 评估 | 关联发现 |
|---|---|---|---|
| **S**poofing | 任务身份 / 等级 | 等级由账本首行 `task_created` 记录；`agent` 字段工具拒绝改写（`agate-md-field-set.py:309`）✓ | — |
| **T**ampering | 账本内容 | 只追加（规则 3，截空实测 rc=1）✓；**但账本可被改名摘除 → 信任锚消失** ✗ | **F-1** |
| **T**ampering | 判定依据（judge/evidence_ref） | 消费方均改依契约 ✓；但依赖账本在场 → 随 F-1 回退旧逻辑 ✗ | F-1 |
| **R**epudiation | 创建/升级留痕 | `task_created`/`task_adopted`/`task_upgraded` 事件规则齐备 ✓；CI 兜底属批 A2（A1 内 `--no-verify` 仍可绕过，已知分期） | F-2 |
| **I**nfo disclosure | 账本/产出 | 未见敏感数据暴露面（本批无日志/响应面） | — |
| **D**oS | 安全门误拦 | 扫描面扩大引入误拦风险低（实测新增误拦 0）；F4 否定写法误拦仍存（既有） | F-4 |
| **E**levation | 阶段/gate 推进 | 规则 7 后半（非 legacy 按暂存产出重跑 gate）已实现，实测拦下「只暂存 P6 产出」✓；legacy 控制态重开被拦（规则 6）✓ | — |

## 六、与 SELF-GATE 复评的关系

`docs/reviews/agate-alignment-review-2026-10-07-TAG0050-A1-rereview.md` 判 F1–F7 全 ALIGNED、
「未发现新 MISALIGNED」。本评审**确认其代码对齐结论**（消费方全覆盖、F3 不追溯、负向用例成立），
但指出复评未覆盖的**安全边界**：F-1 不在 F1–F7 清单内（复评只复核原 MISALIGNED 的闭合），
F-2 是 §8 第 12 项的**交付缺口**（复评的「R6 0 差异」只到 check-gate 面）。

## 七、验证留痕与环境隔离

- 所有 pytest / R6 / 绕过复现均在 `/tmp/opencode/` 下的副本
  （`cso-scratch`、`cso-scratch2`、`cso-scratch5`、`cso-repo`、`cso-r6clone`、`cso-allow`）进行。
- 真实仓库只跑了一次只读的 `pytest …test_tag0050_a0_a1_ledger.py`
  （`-p no:cacheprovider` + `PYTHONDONTWRITEBYTECODE=1`），跑前/跑后 `git status --porcelain` 逐行
  相同（26 passed）。
- 未编辑任何被评审文件；未执行任何破坏性/写仓命令。
- `[PROD_NOT_TOUCHED]` 未接触生产环境。

## 八、返回给主 Agent

- **File**: `agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso.md`
- **Status**: `rejected`
- **最高严重级别**：HIGH（1 项为 A1 安全目标的 BLOCKER）
- **各级计数**：CRITICAL 0 / HIGH 1 / MEDIUM 2 / LOW 3
- **是否阻塞发布**：是 —— F-1（账本可被 `git mv` 摘除 → 任意非 legacy 任务静默降回 legacy，
  重开 F3b/F3c）。修复并补负向用例后建议重审；F-2/F-3 可随修复一并处理或经主 Agent 明确豁免。
