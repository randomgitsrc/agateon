---
agent: implementer
phase: P4
task_id: TAG0050
type: implementation
parent: P3-test-cases.md
trace_id: TAG0050-P4-20261007
status: draft
implementation_dir: agate/
---

# P4 实现记录 — TAG0050 批 A1（契约等级 + 账本完整性 + 任务初始化 + 生效等级）

> 本文件是批 **A1** 的 P4 实现记录（地基批）。只做 A1 范围；A2/B/C/D/E/F 未触及。
> **自查 ≠ gate**：本文只做实现汇总与自查结果记录，不预判 P5/P6/P7/P8 结论。
> 下游消费：`check-gate.py` P7 的 DESIGN_GAP 转抄核对 / `agate-extract-context.py` 的
> `implementation_dir`。

## 1. 任务摘要

按 `P2-design.md` §2.1–§2.3、§2.5、§2.6（+ §3/§4/§10）实现批 A1：契约按等级冻结
（`agate/rules/task-data/`）、任务以账本首行 `task_created` 记等级（只升不降）、
`agate-task-init` 新建/迁移入口、账本完整性七规则、judge 与 evidence_ref 由契约决定
（取代 `created` 日期门槛与 `judge.enabled` 开关）、创建时间系统化、任务 ID 正则统一、
快照冻结 CHECK + 黄金 fixture、R6 双向差分可执行判据。

验收锚：`agate/tests/integration/test_tag0050_a0_a1_ledger.py` 的 **BDD-03..22**（BDD-01/02
为 A0，保持绿）。

## 2. 交付物清单（逐条落地）

| # | 交付物 | 落点 | 状态 |
|---|---|---|---|
| 1 | 冻结快照 + 黄金 fixture | `agate/rules/task-data/{LEVELS,level-1}.yaml`；`agate/tests/fixtures/task-data/level-1/{pass,fail}/` | 已落地 |
| 2 | `agate-task-init.py` | `agate/scripts/agate-task-init.py`（新建 / `--existing` / `--adopt` / `--upgrade`） | 已落地 |
| 3 | `agate_common` 契约函数 | `TASK_ID_RE`/`load_contract`/`registered_levels`/`current_level`/`task_level`/`level_at_phase`/`requirement_active`/`check_ledger_events`/`read_ledger_events`/`project_root`；`is_new_task_for_evidence_ref` 改依契约 | 已落地 |
| 4 | 账本事件规则 | `agate_common.check_ledger_events`（task_created 首行/≤1/**等级已登记**；task_adopted；task_upgraded 只升不降且已登记）。「新任务等级 = 当前等级」**不在本函数**（避免经 CI 追溯存量任务），改在 pre-commit 新建目录分支本地判（§2.3 规则 2，见交付物 6） | 已落地 |
| 5 | `check-events.py` | 调 `check_ledger_events` | 已落地 |
| 6 | `pre-commit-gate.py` 账本与新目录步骤 | 位于 2h.1b 之前、每次提交都跑：规则 1/3/4/5 + 规则 2（新任务等级 = 当前等级，本地仅新任务）+ 全局面 PROD_TOUCHED 扫描 + **规则 7 后半**（非 legacy 任务按被暂存产出所属阶段重跑 gate）；`_judge_enabled` 改依契约 | 已落地 |
| 7 | `check-gate.py` judge 依契约 | `gate_p1`（`:767` 附近）+ `gate_p65` | 已落地 |
| 8 | `check-state-transition.py` legacy 重开 | READY/DONE → Pn（legacy）→ ERROR（提示 `--adopt`/新建） | 已落地 |
| 9 | `agate-next.py:_p6_judge_advance` | 改依契约（`requirement_active(task_dir, "judge", "P6")`；legacy 回退 `judge.enabled`）——F1 补齐（原记录谎称已落地，实为未改） | 已落地 |
| 10 | 任务 ID 正则统一 | `agate-state-yaml-check.py` 统一到 `TASK_ID_RE` | 已落地 |
| 11 | 快照冻结 CHECK + 黄金 fixture 回归 | `check-protocol-consistency.py` CHECK 16；fitness 节点 `test_task_data_freeze_snapshot_sha256`/`test_task_data_golden_fixture_regression` | 已落地 |
| 12 | `evidence_ref` 改依契约 | 经 `agate_common.is_new_task_for_evidence_ref` 单点改（消费方 `check-p6-evidence.py`/`check-p6-provenance.py` 自动跟随） | 已落地 |
| 13 | `conftest.init_task()` | `agate/tests/conftest.py`（写 `task_created`，等级 1） | 已落地 |
| 14 | R6 差分交付物 | `docs/design-notes/r6-differential.sh` + `r6-allowlist.yaml`（接口 `--before/--after/--corpus/--allow`；副本/干净核验；负向用例） | 已落地 |
| 15 | `agate-migrate-workspace.py` | **不改代码**；既有改名检测用例（`test_agate_migrate_workspace.py` 9 用例）全绿，legacy 改名不受影响（BDD-12 另覆盖） | 已落地 |

## 3. 关键实现说明

### 3.1 契约与等级（设计 §2.1–§2.3）

- `LEVELS.yaml` 为顶层列表 `[{level, file, sha256}]`，当前等级 = 最大值；`level-1.yaml`
  含 `requires`/`primary_outputs`/`phase_universe`/`task_id_pattern`/`state`。
- `task_level(task_dir)`：最后一条 `task_upgraded.to_level`，否则创建/迁入事件等级；
  无创建/迁入事件 → `None`（legacy）。
- `level_at_phase(task_dir, Pk)`：`at_phase ≤ Pk` 的创建/迁入/升级事件中等级最大值；
  `task_created` 的 `at_phase` 视为 P0。
- `requirement_active(task, name, phase)`：`snapshot(level(phase)).requires[name]`；
  `level` 为 `None` 时返回 `None`，消费方走旧逻辑。
- `check_ledger_events`：实现设计 §2.2 的事件规则；`task_adopted` 的"本次暂存新增"
  条件由 pre-commit 侧判定（函数注释已注明）。

### 3.2 pre-commit「账本与新目录」步骤（设计 §2.3）

置于主循环之前（任何追加写入之前），每次提交都跑：

- **规则 1**：`git diff --cached -M --name-status` 判定新目录；改名目标（R）沿用原任务；
  新目录账本第 1 行须为 `task_created`，否则 ERROR 并附 `agate-task-init.py` 修复命令。
  **例外**：控制态（PAUSED/READY/DONE）不加叠加阻断（见 §5 DESIGN_GAP 说明）。
- **规则 2**：新任务的等级必须是当前等级（`current_level()`）——**只在本地、仅新任务**
  判（本步骤的新建目录分支）；不在 `check_ledger_events` / CI 路径判，避免协议升级后
  追溯存量非 legacy 任务。
- **规则 3**：暂存账本 HEAD 内容须为暂存内容前缀（LF 归一后比较）。
- **规则 4**：HEAD 含创建/迁入事件的账本被 **D（删除）或 R（改名）** 摘除 → ERROR。
  改名到同目录 `.bak`、或移入**别的任务目录**同样使源任务失去账本 ⇒ 按删除判 ERROR；
  仅**整个任务目录被改名**（账本随目录到新路径、仍属同一任务，即规则 1 的目录改名语义）
  豁免（判据 `_is_task_dir_rename`：改名目标仍是某任务目录下的账本 + 源任务目录在暂存后
  的索引中已不存在）。
- **规则 5**：暂存账本调 `check_ledger_events`（只校验「等级已登记」）。
- **规则 7（全局面）**：每个有暂存文件、但未暂存 `.state.yaml` 的任务目录：
  - **前半（PROD_TOUCHED）**：扫描其暂存文件的新增行（排除 `AGATE_CARD` 块）；命中且
    非 PAUSED → 中止；PAUSED → 写 `prod_touched_in_paused` 事件（与主循环 2g.0 不重复）。
    跳过条件为「有暂存 **且工作区仍存在** 的 `.state.yaml`」——`.state.yaml` 以**删除**
    方式暂存（`git rm`）时不跳过，否则与主循环 `os.path.isfile` 的跳过互相让路，
    该任务目录完全不被扫描（评审 F-3）。
  - **后半（重跑 gate）**：非 legacy 任务暂存了阶段产出、却未改 phase 时，按**被暂存产出
    所属的阶段**重跑该阶段 gate（该阶段须不晚于 HEAD 的 phase；HEAD 为 READY/DONE 时同样
    执行）；任一重跑 exit 1 → 中止 commit（`_rerun_gates_for_staged_outputs`）。

  > **有意偏离（A1-4，主 Agent 裁决）**：P2-design §3.1 第 2 点字面为「全部暂存 **`*.md`**
  > 文件的新增行」，实现按「任务目录内**全部暂存文件**」扫描（未过滤 `*.md`）。理由：
  > 安全门「宁可多拦」，与既有 2g.0 段一致；评审实测新增误拦为 0。此偏离已由主 Agent
  > 接受并登记（相对 P2 §3.1 的 `*.md` 字面）。

### 3.3 judge / evidence_ref 依契约（设计 §2.5，修复 F3a/b/c）

- `check-gate.gate_p1`：非 legacy（`requirement_active` 非 None）时，`requires.judge` 为真
  且未声明 `judge.enabled` → ERROR，**不读** `created`；legacy 保持 `created` 日期门槛。
- `check-gate.gate_p65`：非 legacy 时依契约决定是否强制 judge，**不读** `judge.enabled`。
- `pre-commit._judge_enabled`：非 legacy 时依契约。
- `agate_common.is_new_task_for_evidence_ref`：非 legacy 时返回 `requirement_active(...,
  "evidence_ref", "P6")`；legacy 回退 `created ≥ 截止`。两消费方自动跟随。

### 3.4 快照冻结 CHECK（设计 §2.1 冻结规则 1）

`check-protocol-consistency.py` 新增 **CHECK 16**：对 `agate/rules/task-data/` 下每个
登记快照，LF 归一 sha256 必须等于 `LEVELS.yaml` 登记值；新增 `level-*.yaml` 未登记 → ERROR。
扫描面仅限契约目录（DEBT0025）。

### 3.5 R6 双向差分（P2 §3.2/§3.3）

`r6-differential.sh`：在 `--before`（缺省 `merge-base HEAD origin/main`）与 `--after`
（缺省工作树 `agate/`）两套协议下，对每个 legacy 任务、其阶段 gate 比较 (rc, ERROR 集合)；
差异须匹配 `r6-allowlist.yaml` 的某条规则（D01..D12），否则 exit 1。脚本自核验每个 corpus
原仓库 `git status --porcelain` 为空；allowlist 的 `required_ids` 缺任一规则即 exit 1（负向用例）。

## 4. 文件清单

**新增**：

- `agate/rules/task-data/LEVELS.yaml`
- `agate/rules/task-data/level-1.yaml`
- `agate/tests/fixtures/task-data/level-1/pass/{README.md,gate-events.jsonl}`
- `agate/tests/fixtures/task-data/level-1/fail/{README.md,gate-events.jsonl}`
- `agate/scripts/agate-task-init.py`
- `docs/design-notes/r6-differential.sh`
- `docs/design-notes/r6-allowlist.yaml`

**修改**：

- `agate/scripts/agate_common.py`（契约函数 + `is_new_task_for_evidence_ref`）
- `agate/scripts/check-events.py`（调 `check_ledger_events`）
- `agate/scripts/pre-commit-gate.py`（账本与新目录步骤 + 全局面 PROD_TOUCHED + `_judge_enabled`）
- `agate/scripts/check-gate.py`（`gate_p1` / `gate_p65` 依契约）
- `agate/scripts/check-state-transition.py`（legacy 重开 → ERROR）
- `agate/scripts/agate-next.py`（`_p6_judge_advance` 依契约）
- `agate/scripts/agate-state-yaml-check.py`（ID 正则统一到 `TASK_ID_RE`）
- `agate/scripts/check-protocol-consistency.py`（CHECK 16 快照冻结）
- `agate/tests/conftest.py`（`init_task()`）
- `agate/scripts/README.md`（`agate-task-init.py` 索引行）
- `docs/design-notes/README.md`（R6 交付物索引行）

**按设计 §8 例外改动的既有测试**（"新建任务目录并提交"用例 → 满足规则 1；ID 正则放宽）：

- `agate/tests/integration/test_pre_commit_hook.py`（`_write_state_yaml` 增写 `task_created`
  账本 + `judge.enabled: true`；新增 `_seed_task_created`）
- `agate/tests/unit/test_dispatch_context_warning.py`（新任务目录补 `task_created`）
- `agate/tests/unit/test_agate_state_yaml_check.py`（ID 正则放宽：`T001` 由拒绝变为通过）

## 5. 设计偏差与自主决策

[DESIGN_GAP: pre-commit 规则 1（新目录须有创建事件）对控制态（PAUSED/READY/DONE）不施加叠加阻断——PAUSED 表示任务已被人工接管（同 2g 段语义），且新建任务本应在 P0 登记；否则 A0 的 BDD-01（PAUSED 留痕）会被规则 1 抢先阻断]

> **规则 7 后半已在本批补齐（F2 整改，SELF-GATE 评审 A1-2）**：原记录曾登记
> `[DESIGN_GAP]` 称「本批未启用」，评审判 MISALIGNED 后已实现（`_rerun_gates_for_staged_outputs`）。
> 与既有 `IT_PHASE_SPAN.1/2/4` 的冲突按设计 §8 例外处置：这三个用例验证的是阶段产出与
> phase 的一致性 WARNING（与契约等级无关），其任务在 A1 中因 `_write_state_yaml` 变为非
> legacy 而触发规则 7 后半；已改为 legacy 任务（恢复其原形态），重跑行为由重写的 BDD-19
> （经 pre-commit hook）覆盖。

[DESIGN_GAP: 非 legacy 任务写 `status` 的 ERROR 与 `status` 现算属批 A3（设计 §2.7），A1 未实现；A1 只统一 ID 正则。BDD-39 仍红属预期（批 A3）]

## 6. 自查结果（自查 ≠ gate）

- `python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q` → **26 passed**
  （BDD-01/02 + BDD-03..22 + F1/F3 补充用例全部绿；BDD-02 参数化 P7/P5/P0；BDD-19 已重写为
  经 pre-commit hook 的场景）。
- `python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q` → **61 passed**。
- `python3 -m pytest agate/tests/unit/test_agate_migrate_workspace.py -q` → **9 passed**。
- 全量 `python3 -m pytest agate/tests/ -q -n auto` → **2713 passed / 40 failed / 2 skipped**
  （SELF-GATE 整改后实跑值）；
  40 条失败**全部为 A2/A3/A4/B/C/D/E/F 批次的既有红灯**（`test_tag0050_{ci_replay,state_set,
  obligations,write_tools,declarations,proxy_judgment,evidence,prod_touched,fitness,cross_batch}`）
  + 1 条与本任务无关的既有环境漂移（`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，
  本机 opencode `debug agent` 已更名 `debug agents`，P3 已登记）。**A1 范围内 0 回归**。
- `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（实跑值；
  与基线一致；CHECK 16 通过；临时新增未登记 `level-2.yaml` 实测报 ERROR）。
- `~/.venvs/agate-dev/bin/ruff check agate/` → **All checks passed**。
- `python3 agate/scripts/check-platform-assumptions.py agate/scripts/ agate/tests/`：本批新增/
  改动文件 **0 命中**（其余命中为既有基线）。
- R6 差分：在干净 clone 上 `bash docs/design-notes/r6-differential.sh --corpus <clone>` → exit 0；
  负向用例（删 allowlist 必需规则 / 弄脏 corpus）→ exit 1。SELF-GATE 整改后 R6 已纳入
  READY/DONE 任务（按最高阶段产出映射相关 gate）。

## 7. 环境隔离

[PROD_NOT_TOUCHED] 本批只在 agateon 本 checkout 与只读 clone（`.agate-tmp/r6clone`）上实现与
验证，未接触生产环境。

## 8. SELF-GATE 整改（F1–F7，依据 `docs/reviews/agate-alignment-review-2026-10-07-TAG0050-A1.md`）

- **F1**：`agate-next.py:_p6_judge_advance` 改调 `requirement_active(task_dir, "judge", "P6")`
  （None → 回退 `judge.enabled`），与 check-gate/pre-commit 一致。
- **F2**：`pre-commit-gate.py` 补齐规则 7 后半 `_rerun_gates_for_staged_outputs`
  （非 legacy 任务按被暂存产出所属阶段重跑 gate）；与 `IT_PHASE_SPAN.1/2/4` 的冲突按设计 §8
  例外处置（三个用例改回 legacy 形态）。
- **F3**：`agate_common._level_registration_errors` 只校验「等级已登记」；「新任务等级 =
  当前等级」移至 pre-commit 新建目录分支（本地、仅新任务）。
- **F4**：`agate/WORKFLOW.md`「Pre-commit 检查总览」新增 `1.1 账本与新目录` 行 + 更新
  「多任务适配」段。
- **F5**：`SELF-GATE.md` 两处「当前 CHECK 1-15」→「1-16」。
- **F6**：本文件 §2/§3/§6 声称与数字按实跑值修正（删除被证伪的「已落地」不实记录，
  经 F1 补齐后可如实写）。
- **F7**：`test_tag0050_a0_a1_ledger.py` 重写 BDD-19（经 pre-commit hook）+ 新增
  `test_f1_p6_judge_advance_uses_contract` / `test_f3_current_level_2_existing_level_1_passes`。
- **A1-4**（主 Agent 裁决）：PROD_TOUCHED 扫描面接受「任务目录内全部暂存文件」（§3.2 有意偏离）。
- **A5**：`state-machine.md` 同步 legacy 重开 ERROR（`UPGRADING.md`/`CHANGELOG.md` 归 P8）。
- **A4-R6**：`r6-differential.sh` 纳入 READY/DONE 任务（按最高阶段产出映射相关 gate）。

## 9. 本次整改触碰的协议/文档文件

- `agate/scripts/agate-next.py`、`agate/scripts/agate_common.py`、`agate/scripts/pre-commit-gate.py`
- `agate/WORKFLOW.md`、`agate/state-machine.md`、`SELF-GATE.md`
- `agate/tests/integration/test_pre_commit_hook.py`、`agate/tests/integration/test_tag0050_a0_a1_ledger.py`
- `docs/design-notes/design-tag0050-task-data-contract.md`（§8 例外清单）、
  `docs/design-notes/r6-differential.sh`（READY/DONE）

## 10. C8 评审整改（依据 `P4-review-cso.md` F-1..F-6，2026-10-07）

`P4-review-cso.md` 判 **rejected**（F-1 HIGH/BLOCKER）。本次整改只修 G1–G3（+ 酌情 F-5），
不改设计路线。

### G1（F-1 BLOCKER）规则 4 的 rename 洞

- 原实现只处理 `D`（删除），`git mv` 的 `R`（改名）三元组被无条件跳过 ⇒ `git mv
  gate-events.jsonl <任意名/别目录>` 后任务静默降回 legacy（重开 F3b/F3c）。
- 整改：规则 4 同时处理 `R`——源路径是账本时，仅**整目录改名**（`_is_task_dir_rename`）
  豁免；否则按删除判 ERROR。判据基于「源任务目录在暂存后索引中是否已不存在」
  （`git ls-files`），不依赖 git rename 相似度检测，比 `R` 三元组稳健。
- 新增用例：BDD-23（同目录 `.bak` → rc≠0）、BDD-24（移入别的任务目录 → rc≠0）、
  BDD-25（整目录改名 → rc=0 放行）。**BDD-23/24 在整改前实测变红**（已复验）。

### G2（F-2 MEDIUM）R6 覆盖范围 —— 选择 (b) 显式声明

- **声明**：A1 交付的 `r6-differential.sh` **只承诺 check-gate 面**（`check-gate.py <phase>
  <task>`）。理由：干净 corpus 无暂存改动，pre-commit 的行为取决于暂存区，回放无意义。
- 设计 §8 第 12 项（新增 PROD_TOUCHED ERROR 单独统计并逐条列出）**改由批 A2 的
  `agate-ci-verify` 逐提交回放 pre-commit 承担**（§2.4）。已在 `design-…§8` 补记
  「第 12 项的 R6 归属（G2）」段，并在 `r6-allowlist.yaml` 头部写明 `gate: pre-commit`
  规则不在 A1 的 R6 覆盖内（`required_ids` 只校验存在、不校验可达）。
- 附带修正：`_rule_matches` 此前**从不读 `task_scope`**（D03 的 `specific:T090` 形同虚设）
  ——已补 `task_scope` 判定（`legacy` / `non-legacy` / `any` / `specific:<id>`）。
- F-5（LOW）：`r6-differential.sh` 增加**运行后** `git status --porcelain` 自核验（此前只在
  运行前），兑现「跑差分不弄脏真实仓库」。

### G3（F-3 MEDIUM）`git rm .state.yaml` 绕过 PROD_TOUCHED 全局面扫描

- 原实现：全局面扫描跳过「有暂存 `.state.yaml`」的任务目录（委托主循环 2g.0）；主循环对
  被**删除**的 `.state.yaml` 因 `os.path.isfile` 为假而跳过 ⇒ 两条路径互相让路，该目录
  完全不被扫描。
- 整改：全局面扫描的跳过条件收紧为「有暂存 **且工作区仍存在** 的 `.state.yaml`」——
  删除态不跳过。新增用例 BDD-26（`git rm .state.yaml` + 目录内写 `[PROD_TOUCHED]` 并
  `git add` → rc≠0）。**整改前实测变红**（已复验）。

### 其余发现（F-4 / F-6）

- **F-4（LOW）**：安全门粗体漏拦 / `[PROD_TOUCHED]: 无` 误拦——**属批 C 的 P2 §3.1 规格**
  （`markers.yaml` 改 `default` + `agate_markers.pattern()`），**不在 A1 修复范围**。A1 的
  新全局面复用同一弱正则，F-4 未闭合前「宁可多拦」只部分成立（记录待批 C 承接）。
- **F-6（LOW，信息）**：新建目录在控制态（PAUSED）可跳过规则 1/2——已知 DESIGN_GAP，
  实际无法借此养成 legacy（`PAUSED → P0` 被 `check-state-transition` 拦）。**登记不改**。

### 环境隔离

[PROD_NOT_TOUCHED] 整改只在本 checkout 与 pytest `tmp_path` 仓上进行。
