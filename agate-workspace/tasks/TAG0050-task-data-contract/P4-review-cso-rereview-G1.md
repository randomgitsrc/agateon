---
phase: P4
task_id: TAG0050
parent: P4-implementation-G1.md
trace_id: TAG0050-P4-20261008
type: review
agent: cso
status: approved
---
# P4-review-cso（聚焦复审） — TAG0050 批 G1（A2+A3+A4）第 3 轮整改后安全维度复审

- **评审对象**：TAG0050 合批 G1（A2 CI 逐提交回放 + A3 state-set/状态事实 + A4 义务机械核验）
  的**未提交**实现（fix3 后）；HEAD `b0a16c3a`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
- **评审范围**：`P4-dispatch-context-cso-G1-rereview.md` 的 K1–K6 是否闭合 + 是否引入新安全阻断；
  不重做设计。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本** `/tmp/opencode/cso-g1-re3/` 内做可复现验证；
  不改被评审文件、不写仓（见「六、验证留痕」含一次误操作与完整恢复记录）。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在仓外副本协议根 + 一次性 git 仓中进行。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **MEDIUM**（无 CRITICAL / 无 BLOCKER） |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1（N-1：K1 解耦检查对「整目录改名」误判 FAIL） |
| LOW | 1（N-2：等级检查 `--no-renames` 把改名当新增） |
| K1–K6 闭合 | **K1–K6 全部 ALIGNED** |
| 是否阻塞发布 | **否** —— 安全目标（防合并提交静默摘除账本）已闭合且经独立负向验证；N-1 为**误报型**（过度拦截）非安全绕过 |
| status | `approved` |

## 二、K1–K6 逐条复核（命令 + 输出）

### K1（原 BLOCKER）账本最终状态检查与回放解耦，覆盖合并提交 → **ALIGNED**

- **实现**：`agate-ci-verify.py:288-330` `_ci_ledger_checks(repo, base, head)` 改 `rev-list <base>..<head>`
  （含合并提交）+ `diff --name-status --no-renames`（同时取改名被摘除的源路径）；调用点在
  `:460`（在「无任务改动 → SKIP」`:484-492` **之前无条件执行**）。
- **独立负向验证**（副本 `repo`，含 `task_created` 账本 → feature 非任务改动 → `merge --no-ff --no-commit`
  并 `git rm` 账本）：

  ```
  $ git log --oneline --graph -4
  *   52ee716 evil merge deletes ledger
  |\
  | * 059283b feature non-task
  |/
  * 00968e4 base with created ledger
  $ git cat-file -e HEAD:agate-workspace/tasks/TAG0001/gate-events.jsonl   # rc=128（ABSENT）
  $ git rev-list --no-merges BASE..HEAD      # → 仅 059283b（不改任务目录 → 回放会 SKIP）
  $ AGATE_ROOT=<副本>/agate python3 <副本>/agate/scripts/agate-ci-verify.py --base 00968e46
    FAIL 账本: agate-workspace/tasks/TAG0001/gate-events.jsonl: 含创建/迁入事件的账本被删除/截空/改写（防降回 legacy）
  CI-only 额外检查失败（1 账本 / 0 等级），回放范围 00968e46..52ee7165 未改动任务目录
  CI_RC=1
  ```

- **对照（证明是「解耦检查」拦下的，不是回放）**：把 `:460` 的解耦调用置空（副本 `agate-oldledger`，
  不改被评审文件）→ 同一 evil merge：

  ```
  SKIP: 回放范围 00968e46..52ee7165 未改动任务目录（1 个提交）
  CI_RC=0          # ← 模拟修复前：静默通过（F-1 漏洞）
  ```

- **F-4 改名面同源验证**（`--no-renames` 取源路径）：账本移入**别的任务目录** / 同目录改名 `.bak`
  → 均 `FAIL 账本` + `CI_RC=1`（副本 `repo_move_A/B`）。
- **负向用例存在且绿**：`test_tag0050_ci_replay.py::test_k1_evil_merge_deletes_ledger_fails`（副本内 passed）。
- **结论**：K1 安全目标（合并提交不得静默摘除账本）**闭合**。

### K2 / K3（原 HIGH，同根因）M 义务凭证自指 → **ALIGNED**

- **实现**：`obligations.yaml` 抽样的 6 条 M（OBL-P8-01/02/03、P1-10、P2-07、P2-10）`test` 改指
  `agate/tests/unit/test_tag0050_obligation_behavior.py` 的**真实行为用例**，`enforced_at.function`
  精确到 `gate_p8` / `_gate_p1_vision_capability` 等；BDD-42 改为对**执行分支**做真变异。
- **独立负向验证**（副本 `k2neg` 把 `check-gate.py` 的 `if "delivery:" not in p8_text:` 改为 `if False:`）：

  ```
  # 基线（真实根）：绿
  $ python3 -m pytest .../test_tag0050_obligation_behavior.py::test_obl_p8_02_delivery_missing_blocks -q
  1 passed
  # 删执行分支后（AGATE_TEST_PROTOCOL_ROOT=k2neg）：红
  $ AGATE_TEST_PROTOCOL_ROOT=<副本>/k2neg python3 -m pytest ...::test_obl_p8_02_delivery_missing_blocks -q
  FAILED ...::test_obl_p8_02_delivery_missing_blocks
  1 failed
  ```

- **对照（证伪「自指」已被根除）**：同一变异下——
  - 旧「登记凭证」`test_tag0050_obligations_enforcement.py::test_obligation_enforced[OBL-P8-02]` → **1 passed**（只读 YAML，不敏感）；
  - `check-obligations.py`（`AGATE_ROOT=k2neg`）→ `rc=0`（AST 可达性检查不敏感）。
  即：**只有**新行为凭证对「删执行分支」转红 ⇒ 不再是自指。
- **结论**：K2、K3 **闭合**（设计 §2.9 明确允许负向控制以 mutation **抽样**执行）。
- **残余（非阻塞，供评审知悉）**：60 条 M 中仅 6 条有真实行为凭证，其余仍以「登记存在」辅助断言为
  `test`（设计允许抽样，故不计 MISALIGNED）。`_check_enforced_at` 对多数义务仍指向某脚本 `main`
  （可达性近于「该脚本 main 存在」），这是设计对「函数内部分支型义务」以抽样负向控制兜底的取舍。

### K4（原 CRITICAL）新增任务等级检查 → **ALIGNED**

- **实现**：`agate-ci-verify.py:370-402` `_ci_level_checks`（新增任务目录 `contract_level` ≥
  merge-base 处 `LEVELS.yaml` 最大等级）。
- **验证**（副本内）：`test_bdd_30b_new_task_below_merge_base_level_fails`（负向）+ 重写后的
  `test_bdd_30_branch_crossing_upgrade_no_false_report`（在途升级不误报）→ `3 passed`
  （含 K1 用例；命令 `pytest test_tag0050_ci_replay.py::test_k1... ::test_bdd_30... ::test_bdd_30b... -q`）。
- **结论**：K4 **闭合**。

### K5（原 MEDIUM）版本分支① → **ALIGNED（显式降级）**

- `agate-ci-verify.py:21-23` docstring 明写分支①「**未实现**」；`:24-30` 显式声明 F-5 影响 2
  （缺失 `.agate-version` 不判 FAIL）的绕过面。
- `P4-implementation-G1.md:76` `[DESIGN_GAP]` 登记分支①未实现 + 走 merge-base / 仓库本体协议根。
- **结论**：按 dispatch 允许的「显式 `[DESIGN_GAP]` 降级」闭合。

### K6（原 MEDIUM）锚点 advisory → **ALIGNED**

- `P4-implementation-G1.md:146-152`「K6 — 回放锚点当前为 advisory」节明确：`gate-backstop` 未设
  required、回放失败不阻塞合并、取得许可前「可信锚点」不成立。
- **结论**：已写明，闭合（不改 workflow、不自行设 required）。

## 三、新发现问题

### N-1 MEDIUM（误报型，非安全绕过）：K1 解耦后的账本检查对**整目录任务改名**误判 FAIL

- **位置**：`agate-ci-verify.py:307-326`（`diff --name-status --no-renames` +「源路径含 origin 且当前不存在 → FAIL」）。
- **事实**：pre-commit 规则 4 对「**整个任务目录**被改名」有**显式豁免**（`pre-commit-gate.py:279-289`
  `_is_task_dir_rename` / `_dir_moved_away`；P1 **BDD-25** 要求该场景 **rc=0**）。CI 的新检查**没有**这条豁免，
  且 `--no-renames` 把改名拆成「D 源路径 + A 目标路径」⇒ 源账本（含 origin）被判「被删除/改写」。
- **可复现证据**（副本 `repo_rename`：非 legacy 任务 TAG0001 → `git mv` 为 `TAG0001-renamed`，与 BDD-25 同形）：

  ```
  $ git diff --name-status --no-renames HEAD~1 HEAD
  A  agate-workspace/tasks/TAG0001-renamed/.state.yaml
  A  agate-workspace/tasks/TAG0001-renamed/gate-events.jsonl
  D  agate-workspace/tasks/TAG0001/.state.yaml
  D  agate-workspace/tasks/TAG0001/gate-events.jsonl
  $ AGATE_ROOT=<副本>/agate python3 <副本>/agate/scripts/agate-ci-verify.py --base <BASE>
    FAIL 账本: agate-workspace/tasks/TAG0001/gate-events.jsonl: 含创建/迁入事件的账本被删除/截空/改写（防降回 legacy）
    回放 5043e8ac: PASS            # ← 本地 hook（回放）PASS，CI 账本检查 FAIL ⇒ 同一提交口径分歧
  CI_RC=1
  ```

  即：**同一提交，本地 pre-commit 放行、CI 判失败**——违反设计「回放强度 = hook 强度」的前提，
  且与 BDD-25 的契约相左。真实仓库中该场景更明显：CI 回放用 merge-base（`720c97d3`，pre-A1）协议
  → 回放必 PASS，而新账本检查 FAIL。
- **性质**：**误报/过度拦截**（可用性/一致性缺陷），**不是**安全绕过；且当前 `gate-backstop` 为 advisory
  （K6），实际阻塞面有限。若日后设为 required，则升级为 HIGH（阻塞合法 BDD-25 流程）。
- **建议**：在 `_ci_ledger_checks` 复刻 pre-commit 的目录改名豁免——当「源任务目录在同一提交后已不存在」
  且「目标路径是 `<某任务目录>/gate-events.jsonl`」时按**改名**（非删除）处理；或改用 `--name-status -M`
  同时取源/目标并按 `old_task_rel` 判 `_dir_moved_away`。补一条正向负向用例：整目录改名 → CI 不报 `FAIL 账本`。
- **未重开 K1**：K1 的安全目标（防静默摘除账本）已达成；N-1 是其机制对**合法改名**的副作用。

### N-2 LOW：`_ci_level_checks` 用 `--no-renames` 会把改名目录当「新增」

- 同因：`_ci_level_checks`（`:381-394`）以 `diff --name-status --no-renames` 取「A 状态」任务目录，
  整目录改名的目标目录会被当成「新增任务」，从而套用「新任务等级 ≥ merge-base 最大等级」判据，
  可能对老任务改名产生等级误报。因 N-1 已先 FAIL，实际被其吸收；一并按 N-1 的建议用 `-M` 修正即可。

## 四、正向核验（无误报/无回归）

- **合法追加不误报**（副本 `repo_append`：`task_created` + 追加 `gate_run`）：

  ```
  $ AGATE_ROOT=<副本>/agate python3 <副本>/agate/scripts/agate-ci-verify.py --base <BASE>
   回放 48051213: PASS
  PASS: 逐提交回放全部通过
  CI_RC=0
  ```

- **G1 验收面**（副本内跑 `test_tag0050_ci_replay / state_set / obligations / obligation_behavior /
  obligations_enforcement`）→ `92 passed / 2 failed`。其中 2 例（`test_bdd_23_pr_replay_passes` /
  `test_bdd_24_push_replay_passes`）失败系**副本环境差异**：副本协议根 = 工作树（含 A1 新目录规则），
  测试仓仅建 `.state.yaml` 无账本 ⇒ 回放触发「新目录无 task_created」；而真实仓库 `_resolve_protocol`
  取 merge-base（`720c97d3`，pre-A1，无该规则）协议 ⇒ 通过。**非缺陷**，仅说明复跑须用真实仓库
  merge-base 语境的协议或给测试仓补账本。（`test_k1...`/`test_bdd_30...`/`test_bdd_30b...` 副本内 **3 passed**。）

## 五、STRIDE 矩阵（针对 K1–K6 整改面）

| 威胁 | 面 | 评估 | 关联 |
|---|---|---|---|
| **S**poofing | 任务身份/等级 | 等级仍由账本首行 `task_created` 记录；K4 新增 merge-base 等级下限 ✓ | — |
| **T**ampering | 账本内容 | 合并提交删除/改写账本 ⇒ CI `FAIL 账本` ✓（K1 独立复现）；改名进别目录/`.bak` 亦拦 ✓ | K1 |
| **T**ampering | 判定依据（judge/evidence_ref） | 消费方仍依契约；账本在场性由 K1 恢复 ✓ | K1 |
| **R**epudiation | 义务「机械核验」留痕 | 抽样 M 具备**可被打红**的真实行为凭证 ✓（K2/K3 独立复现）；未抽样项为登记辅助断言（设计允许抽样） | K2/K3 |
| **R**epudiation | CI 可信锚点 | 回放可抓 `--no-verify`；但锚点仍 advisory（K6 已声明） | K6 |
| **I**nfo disclosure | 账本/产出 | 本批无日志/响应面，未见敏感数据暴露 | — |
| **D**oS | 安全门误拦 | **N-1：整目录改名被 CI 误拦**（本地 PASS/CI FAIL）；合法追加无误报 | **N-1** |
| **E**levation | 阶段/gate 推进 | state 以 HEAD 为 old + retries 回退校验（首轮已过） | — |

## 六、验证留痕与环境隔离

- 副本：`/tmp/opencode/cso-g1-re3/agate`（本 checkout `agate/` 工作树副本，供 `AGATE_ROOT`）、
  `agate-oldledger`（K1 对照）、`k2neg`（K2/K3 变异）、一次性 git 仓 `repo / repo_move_A / repo_move_B /
  repo_rename / repo_append`。
- 真实仓库：`git status --porcelain` 评审前 53 行（`status_before.txt`）与全部验证后
  `status_after.txt` **逐行一致（diff 空）**；HEAD 保持 `b0a16c3a`。
- **[事故与恢复 · 如实留痕]**：首次构造临时仓的 bash 因 `cd "$R"`（`$R` 未 `mkdir`）失败，使后续命令在
  真实仓库 cwd 下执行，误产生提交 `2e6bb16d init`（**仅 `README.md` 被改**）+ 暂存区脏 + 新建
  `.agate-version` 与 `agate-workspace/tasks/TAG0001/`。已恢复：`git reset --mixed b0a16c3a` →
  `git checkout b0a16c3a -- README.md` → `rm -rf .agate-version agate-workspace/tasks/TAG0001`；
  核验 `git status --porcelain` 与评审前 `diff` 为空、HEAD=`b0a16c3a`、无 `feature` 分支 / `notes.md` /
  `MERGE_HEAD` 残留、`git config user.*` 与历史作者一致（`t <t@t>`）。后续临时仓改用脚本文件
  （先 `mkdir` + 校验 `pwd`）+ 绝对路径，未再触及真实仓库。此事故**未改动被评审文件**，已完全复原。
- 未编辑任何被评审文件；未在真实仓库执行破坏性/写仓命令（事故为误触，已复原）。
- `[PROD_NOT_TOUCHED]` 未接触生产环境。

## 七、返回给主 Agent

- **File**: `agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso-rereview-G1.md`
- **Status**: `approved`
- **K1–K6**：全部 ALIGNED（K1 独立负向复现：evil merge 删账本 → `FAIL 账本` rc=1；K2/K3：删执行分支 → 行为凭证转红）
- **最高严重级别**：MEDIUM（N-1 误报/一致性，非安全绕过）；CRITICAL 0 / HIGH 0 / MEDIUM 1 / LOW 1
- **是否阻塞发布**：否。建议 K1 的 `_ci_ledger_checks` 补「整目录改名」豁免（N-1）以免在
  `gate-backstop` 转 required 后阻塞 BDD-25 合法流程；N-2 同源一并处理。
