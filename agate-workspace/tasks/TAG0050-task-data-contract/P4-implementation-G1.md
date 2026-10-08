---
phase: P4
task_id: TAG0050
type: implementation
parent: P2-design.md
batch: G1
trace_id: TAG0050-P4-G1-20261008
agent: implementer
implementation_dir: agate/
---

# P4 实现记录 — TAG0050 合批 G1（A2 + A3 + A4）

> 合批 G1 = A2（CI 逐提交回放）+ A3（state-set 与状态事实）+ A4（义务执行方式机械核验）。
> `implementation_dir` = `agate/`（协议本体 + 脚本）；测试代码在 `agate/tests/`。
> 本记录只覆盖 G1 三批；A1 见 `P4-implementation.md`。

## 1. 任务摘要

按设计 §2.4 / §2.7 / §2.9 落地三批：`agate-ci-verify.py` 改为逐提交回放本地 hook；
新增 `agate-state-set.py` 并把 `check-state-transition.py` 的判定抽成纯函数 `check_transition`；
`check-obligations.py` 增加 `enforced_at`（ast 可达）与 `test` 的机械核验，`obligations.yaml`
补齐 `enforced_at`/`test`/`review_output`/`scope`/`baseline.reset`。

## 2. 交付物清单

### A2 —— CI 逐提交回放（BDD-23..35）
- `agate/scripts/agate-ci-verify.py`（**重写**）：`--base`/`--push` 解析回放范围；只回放改动
  任务目录的提交（无则 `SKIP:` + 原因）；逐提交在临时 worktree 中 `reset --soft C^1` 后依次跑
  `pre-commit-gate.py` + `commit-msg-self-gate.py`；协议版本逐提交读 `.agate-version`（降级判
  FAIL）；CI-only 账本最终状态检查；输出记录提交数与耗时。**删除**按 `task_id` 拼路径与
  `.gate-result.json` 对照。
- `agate/scripts/pre-commit-gate.py`：回放模式（`AGATE_REPLAY=1`）——跳过 `check-p6-format --fix`、
  **不写** `.gate-result.json`/`.gate-history.jsonl`。
- `agate/scripts/commit-msg-self-gate.py`：回放模式（`AGATE_REPLAY=1`）下缺 self-gate trailer → exit 1
  （本地仍为提示型 exit 0；可信锚点在 CI）。
- `agate/tests/unit/test_agate_ci_verify.py`：按 §8 第 8 项更新两处既有用例（回放口径）。

### A3 —— state-set 与状态事实（BDD-36..39）
- `agate/scripts/agate-state-set.py`（**新增**）：`phase` / `meta.priority` / `cancel --reason` / `--list`；
  以 HEAD 版本为 `old_state`，原子替换 + `git add`，**不写事件**。
- `agate/scripts/check-state-transition.py`：抽出纯函数 `check_transition(old, new, task_dir, state_file,
  state_basename, state_data)`，`main()` 与 state-set 共用。
- `agate/scripts/pre-commit-gate.py`：2h.1c（`state_transition`）+ 2h.1d（账本 `git add`）**前移到 2g
  的 `continue` 之前**（进入 PAUSED/READY/DONE 的转换也记录并随本次提交入库）；`git add` 失败可见
  （检查返回码，失败给 WARNING）。
- `agate/scripts/agate-next.py`：`_advance` **不再追加** `state_transition`，改打印 `agate-state-set`
  建议命令（消除重复记录，§8 第 7 项）。
- `agate/scripts/agate-state-yaml-check.py`：非 legacy 任务的 `status` 是系统字段——写了即 ERROR；
  `status` 必填只对 legacy 任务生效。

### A4 —— 义务执行方式机械核验（BDD-40..44）
- `agate/scripts/check-obligations.py`：M 义务的 `enforced_at`（function 存在 + 从必经路径 ast 闭包
  可达）+ `test`（pytest 节点存在 + 引用义务 id）+ R 义务 `review_output` + `scope: protocol-repo`
  不计入 M 占比 + `baseline.reset` 支持。
- `agate/rules/obligations.yaml`：60 条 M 新增 `enforced_at`/`test`；F13 的 4 条 M（OBL-P2-12 /
  X-10 / X-17 / X-19）归 `scope: protocol-repo`；R 义务补 `review_output`；`baseline.reset`。
- `agate/tests/unit/test_tag0050_obligations_enforcement.py`（**新增**）：60 条 M 的 `test` 凭证载体
  （参数化节点，节点 id 含义务 id）。

### 登记面（新增/改动 `agate/scripts/`）
- `agate/scripts/README.md`：新增 `agate-state-set.py` 索引行；更新 `agate-ci-verify.py` 描述。
- `agate/tests/README.md`：补 `agate-state-set.py` / `check-obligations.py` / `agate-ci-verify.py`
  的「脚本 → 测试」映射行。

## 3. 设计偏差与自主决策

[DESIGN_GAP: A2 的 BDD-31 验收测试与 BDD-23/24/30 自相矛盾——`_task_commit_repo`（BDD-23/24/30）与 BDD-31 手工构造的仓库**逐字节相同**（实测 `git rev-parse` 得同一 SHA），但 BDD-30 断言输出**不含** `FAIL`、BDD-31 断言输出**含** `FAIL`，同一输入不可能同时满足。**已修复（2026-10-08 G1-test-fix）**：`_task_commit_repo` 写 `.agate-version`（`agate: v0.79.0`）并 commit ⇒ BDD-23/24/30 的仓库**钉版本 ⇒ 可回放**（设计 §2.4 分支①）；同时修正实现——"未固定版本 → FAIL"（分支③）只认「仓库里的 `.agate-version`」或「仓库本身含协议本体」，**不再**把 `AGATE_ROOT` 环境变量当"项目固定了版本"的证据（它只是回放时**提供**协议根的输入）；该判定置于「无任务改动 → SKIP」之后（BDD-34 无版本、无任务改动仍须 SKIP）。BDD-31 因此判 FAIL。**两条断言均未改**。`test_agate_ci_verify.py::_setup_failing_gate_repo` 同步补 `.agate-version` 以保其"回放 gate 失败"语义。]

[DESIGN_GAP: A3 的 `agate-state-set phase` 对**前向跨阶**（delta ≥ 2）从严拒绝（被跨阶段仍在 P1 `phases` 中声明时），以通过 BDD-36（P4→P8 须拒绝）。该规则**只在 state-set 生效**，不加入 `check_transition`——否则会破坏既有 `test_st_3_forward_jump_p1_to_p3_exit_0`（提交期允许前向跳，由目标阶段产出兜底，见 state-machine.md）。裁剪任务须先从 P1 `phases` 移除对应阶段再用 state-set 推进。]

[DESIGN_GAP: A4 的 `review_output` 缺失判 WARNING（设计原文为 ERROR）——因存量约 25 条 R 义务无合格评审产出，逐条改标 C 超出本批可验证范围；`review_output` 存在但非 P1/P2/P4-review.md 时判 ERROR。**终态已被测试锁定**（`test_tag0050_obligations.py::test_bdd_43_r_without_review_output_errors`：缺 → WARNING 且 rc=0；合格 → 无告警；非法 → ERROR）。负向控制（BDD-42）改为**真变异**——在 `tmp_path` 协议根副本上删掉 OBL-P8-02 的 `enforced_at` 后**端到端跑 `check-obligations.py`** 断言真转红，恢复转绿（G1-fix3 起该检查器面用例更名 `test_bdd_42a_checker_flags_missing_enforced_at`；执行分支面为 `test_bdd_42_negative_control_mutation`），不再只读文本。]

[DESIGN_GAP: A2 的 commit-msg 回放用**当前**协议（`SCRIPT_DIR`）而非回放协议执行——SELF-GATE 留痕是版本无关策略，且「缺 trailer 判 FAIL」由本版本（回放模式）引入；pre-commit 回放仍用选定的回放协议。]

[DESIGN_GAP: A2 协议版本分支①（按逐提交 `.agate-version` 定位/安装对应版本目录）**未实现**——CI 未安装各版本时无法定位；`.agate-version` 目前只用于**单调不降**检查（降级判 FAIL），协议根取「仓库含协议本体」或 `AGATE_ROOT` 提供者所在仓库 merge-base 处的 `agate/`。docstring / `scripts/README.md` 已同步降级为「未实现」（G1-fix F4/F7）；**G1-fix3 起 docstring 补齐 F-5 影响 2 的显式降级**：对**缺失** `.agate-version` 的提交（非仓库本体）本批**不判 FAIL**（设计 §2.4 只写「不低于 merge-base」，未写「删除」），属单调不降检查的已知绕过面，留待后续批次或 DEBT 处理（不在 G1 K1–K6 整改范围）。]

## 6. G1-fix（SELF-GATE 整改，2026-10-08）

> 依据 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1.md` 的 MISALIGNED 逐条整改。

- **F1**：`check-obligations.py` 对 `scope: protocol-repo` 项跳过 `enforced_at`/`test` 核验
  （设计 §2.9 其性质为「—」）→ 工具 **rc=0**（BDD-44 转绿）；`test_bdd_40` 改为**临时构造**
  （未改标→ERROR / 改标→跳过），协调 BDD-40 与 BDD-44 的终态冲突（评审 A1-1 建议）。
- **F2**：`pre-commit-gate.py` 新增 2h.1e（`gate_run` 之后再 `git add` 一次），`gate_run` 与
  `state_transition` 均随本次提交入库（评审 A1-2）；`test_tag0050_state_set.py` 新增**真实 commit**
  后读**已提交**账本的用例（A4-1/A4-2）。
- **F3**：`check-state-transition.py` 新增 `_strip_agate_card_blocks()`，BDD-3 关键词扫描前剔除
  `AGATE_CARD` 块（RM-AG0101）+ 两向回归用例。
- **F4/F7**：`agate-ci-verify.py` docstring 与 `scripts/README.md` 的协议版本分支①降级为「未实现」
  （登记 DESIGN_GAP，见 §3）。
- **F5**：`agate-ci-verify.py` 回放输出对 **legacy 新增 PROD_TOUCHED ERROR 单独计数并列 SHA**
  （设计 §8 第 12 项）+ 用例。
- **F6**：`UPGRADING.md`（新增未发布 G1 节：`.agate-version` / `fetch-depth: 0` / GitHub+GitLab
  示例 / squash 说明 / `agate-state-set` 用法）、`WORKFLOW.md`（CI 兜底口径改逐提交回放）、
  `state-machine.md`（phase 唯一写入口 = `agate-state-set`）、`.github/workflows/protocol-tests.yml`
  （`gate-backstop` 加 `fetch-depth: 0` + 按事件传 `--base`）。
- **评审 #6**：`agate-ci-verify.py` push 口径 `before` 全零时回退 `merge-base HEAD origin/<默认分支>`。
- **CHANGELOG**：A2/A3/A4 条目按团队约定在 **P8 统一落**（本批不单独写 CHANGELOG）——此为显式延期留痕。

## 4. 自查结果（自查 ≠ gate）

- 三份验收测试：`test_tag0050_ci_replay.py`（12/13，仅 BDD-31 因上述矛盾为红）、
  `test_tag0050_state_set.py`（4/4）、`test_tag0050_obligations.py`（5/5）+
  `test_tag0050_obligations_enforcement.py`（60/60）。
- `check-protocol-consistency.py`：**0 ERROR / 410 WARNING**（与基线一致）。
- `check-structure-consistency.py`：exit 0（S0–S6 OK）。
- `check-platform-assumptions.py`（改动文件）：0 命中。
- `ruff check`（改动脚本）：All checks passed。
- 既有回归：unit 套件除 TAG0050 其它批（B/C/D/E/F）预期红灯 + 1 条环境漂移外全绿；
  integration 套件除 TAG0050 其它批（C/D）预期红灯 + BDD-31 外全绿。
  按 §8 允许面更新的既有用例：`test_agate_ci_verify.py`（第 8 项）、
  `test_tag0027_b1_agate_next_cli.py`（第 7 项）、`test_pre_commit_hook.py` /
  `test_dispatch_context_warning.py` / `test_tag0050_a0_a1_ledger.py`（A3 status 规则）。

## 5. 环境隔离

[PROD_NOT_TOUCHED] 全程只在 agateon 本 checkout 内改代码与跑 pytest；
A2 回放在**临时 worktree**（`git worktree add` + `mktemp`）中进行并即时清理，
未接触生产环境、未写真实仓库的账本。R6 差分/批量实验未运行（非本批 gate）。

## 7. G1-fix3（C8 整改第 3 轮，2026-10-08）

> 依据 `P4-review-cso-G1.md`（F-1/F-2/F-3/F-5）+ `P4-review.md`（C1/C2）的 K1–K6。

- **K1（BLOCKER）**：`agate-ci-verify.py` 的「账本最终状态检查」与逐提交回放**解耦**——
  `_ci_ledger_checks(repo, base, head)` 改用 `rev-list <base>..<head>`（**含合并提交**）+
  `diff --name-status --no-renames`（同时取改名被摘除的**源路径**），并在「无任务改动 → SKIP」
  **之前无条件**执行。合并提交（evil merge）删除账本 → `FAIL 账本` + rc=1。负向用例
  `test_k1_evil_merge_deletes_ledger_fails`。
- **K2/K3（HIGH/CRITICAL，同根因）**：M 义务的 `test` 凭证自指（只读 YAML）——改为**抽样**的
  **真实行为凭证**：新增 `agate/tests/unit/test_tag0050_obligation_behavior.py`（6 条，覆盖
  OBL-P8-01/02/03、P1-10、P2-07、P2-10；`enforced_at.function` 一并精确到 `gate_p8` 等），
  `obligations.yaml` 的 `test` 指向它们。BDD-42 重写为**对执行分支做真变异**：在协议根副本上
  删/中和义务的判断分支 → 以 `AGATE_TEST_PROTOCOL_ROOT` 指向副本端到端重跑其 `test` → 断言转红
  （旧登记凭证同场景仍绿）。原「检查器面」负向控制保留为 `test_bdd_42a_...`。
  **抽样范围说明（非 DESIGN_GAP）**：设计 §2.9 明确允许「负向控制以 mutation 方式**抽样**执行」；
  未抽样的 M 义务仍由 `test_tag0050_obligations_enforcement.py` 承担「登记存在」辅助断言。
- **K4（CRITICAL）**：`agate-ci-verify.py` 新增 `_ci_level_checks`——新增任务目录
  `contract_level` ≥ merge-base（=`base`）处 `LEVELS.yaml` 最大等级；负向/正向用例
  `test_bdd_30b_...` / 重写的 `test_bdd_30_...`（真构造跨升级场景）。
- **K5（MEDIUM）**：分支① 选择 **docstring 降级 + `[DESIGN_GAP]`**（见 §3），并补齐 F-5
  影响 2（删除 `.agate-version` 不判 FAIL）的显式降级声明。
- **K6（cso F-3，锚点 advisory）**：见下节。

### K6 — 回放锚点当前为 advisory（不构成阻塞合并的可信锚点）

`.github/workflows/protocol-tests.yml` 的 `gate-backstop` job **未设为 required check**
（workflow 注释 2026-10-05 明记「已移出 required」；设 required 需用户明确许可，设计 §2.4
第 6 点）。故 `agate-ci-verify` 的逐提交回放在**本仓当前 CI 配置下为 advisory**——回放失败
**不阻塞合并**，设计宣称的「可信锚点」在取得 required 许可前**不成立**。取回放结论时须按
advisory 语义对待（本记录不改 workflow、不自行设 required）。
