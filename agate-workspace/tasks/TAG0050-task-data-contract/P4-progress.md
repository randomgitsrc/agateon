
## P4 A1 implementer 进度

- [x] 读 dispatch-context（15 项交付物清单 + 完成判据）
- [x] 读 implementer.md 角色定义
- [x] 读 design-tag0050-task-data-contract.md（§0-§14）
- [x] 读 P2-design.md（§1/§3/§3.1-3.3/§6/§7/§10）
- [x] 读 test_tag0050_a0_a1_ledger.py（BDD-03..22）+ helpers_tag0050.py
- [x] 读 P1-requirements.md（BDD-03..22）+ P3-test-cases.md + P0-brief.md
- [ ] 读 P2 files_to_read 列出的代码文件

### A1 实现进度（续）

- 读代码文件（P2 files_to_read）：agate_common / check-events / pre-commit-gate / check-gate / check-state-transition / agate-next / check-state-yaml / agate-state-yaml-check / check-protocol-consistency / check-p6-evidence / conftest
- 新增快照：LEVELS.yaml + level-1.yaml + 黄金 fixture（pass/fail）
- 新增 agate-task-init.py（新建/--existing/--adopt/--upgrade）
- agate_common 新增契约函数；is_new_task_for_evidence_ref 改依契约
- check-events 调 check_ledger_events
- pre-commit-gate 新增「账本与新目录」步骤 + 全局面 PROD_TOUCHED + _judge_enabled 依契约
- check-gate gate_p1/gate_p65 依契约；check-state-transition legacy 重开 ERROR
- agate-state-yaml-check ID 正则统一
- check-protocol-consistency 新增 CHECK 16 快照冻结
- conftest 新增 init_task()
- R6 差分脚本 + allowlist（负向用例实测变红）
- 既有测试按设计 §8 例外更新（pre-commit hook / dispatch-context warning / state-yaml ID 正则）
- 自查：BDD-03..22 全绿（24 passed）；pre-commit 61 passed；migrate 9 passed；consistency 0 ERROR；ruff clean
- [PROD_NOT_TOUCHED]

### A1-fix（SELF-GATE 整改 F1–F7）进度

- F1：agate-next.py `_p6_judge_advance` 改调 requirement_active（None 回退 judge.enabled）
- F2：pre-commit 规则 7 后半 `_rerun_gates_for_staged_outputs` 实现；IT_PHASE_SPAN.1/2/4 按设计 §8 例外改回 legacy
- F3：`_level_registration_errors` 只校验已登记；「=当前等级」移至 pre-commit 新建目录分支（规则 2）
- F4：WORKFLOW.md 新增 1.1 行 + 更新多任务适配段
- F5：SELF-GATE.md 两处 CHECK 1-15 → 1-16
- F6：P4-implementation.md §2/§3/§6 声称与数字按实跑修正
- F7：BDD-19 重写（经 pre-commit hook）+ 新增 F1/F3 用例（target 文件 26 passed）
- A1-4：PROD_TOUCHED 扫描面「全部暂存文件」有意偏离已登记
- A5：state-machine.md 同步 legacy 重开 ERROR
- A4-R6：r6-differential.sh 纳入 READY/DONE（实测 legacy 39 个，差异 0，exit 0）
- 自查：target 26 passed / pre-commit 61 passed / 全量 40 failed 2713 passed 2 skipped / consistency 0 ERROR 410 WARNING / ruff clean / shellcheck clean
- [PROD_NOT_TOUCHED]

## [C8-A1-fix] 2026-10-07 起手
- 已读 implementer.md + dispatch-context（A1-cso-fix）+ P0-brief + P4-review-cso.md
- 目标：G1(规则4 rename 洞,BLOCKER) / G2(R6 pre-commit 面) / G3(git rm .state.yaml 绕过全局面扫描)
- 环境隔离：本机工作目录即开发 checkout，未接触生产 → [PROD_NOT_TOUCHED]
- 读完 cso 评审 + 设计 §2.3 规则 4/§8 第 12 项 + r6-differential.sh/allowlist + 测试与 helpers
- 判定：G1 用「源任务目录在暂存后索引中是否已不存在」判目录级改名（稳健，不依赖 rename 检测）；G3 改全局面扫描跳过条件（删除态不跳过）；G2 选 (b) 显式声明只承诺 check-gate 面

## [C8-A1-fix] 完成
- G1：pre-commit-gate.py 规则 4 处理 R（改名）——仅整目录改名豁免（`_is_task_dir_rename`/`_dir_moved_away`，基于索引判据）；新增 BDD-23/24/25。
- G3：`_scan_prod_touched_and_rerun` 跳过条件收紧为「暂存且工作区存在」；新增 BDD-26。
- G2：选 (b) 显式声明 A1 的 R6 只承诺 check-gate 面；§8 补记 + r6-allowlist 可达性声明；`_rule_matches` 补 task_scope；F-5 运行后自核验。
- 复验：新负向用例整改前实测变红（BDD-23/24/26 + BDD-25 去豁免变红），整改后 30 passed。
- 自查：consistency 0 ERROR/410 WARNING；R6 正/负向（0 差异 / 脏 corpus rc=1 / 缺 D12 rc=1）；ruff 通过；platform-assumptions rc=0。
- [PROD_NOT_TOUCHED] 全程仅本 checkout + /tmp/opencode 副本 + pytest tmp_path。

## A2 implementer 进度（2026-10-07）

- 已读 dispatch-context（A2）、implementer.md、P0-brief.md、P2-design.md（含 §2.4 摘要/§3/§8/§10）、验收测试 test_tag0050_ci_replay.py（BDD-23..35）、helpers_tag0050.py、现有 agate-ci-verify.py。
- 关键结论：A2 = 把 agate-ci-verify.py 从「重跑当前 phase gate」改为「逐提交回放本地 hook」；回放用临时 worktree；AGATE_REPLAY=1；协议版本选择；merge-base 等级检查；§8 第 12 项 legacy PROD_TOUCHED ERROR 单独统计。
- 环境隔离：[PROD_NOT_TOUCHED]（全程只读 + tmp_path / 临时 worktree）
## P4 G1 (A2+A3+A4) implementer — 启动
- 已读：dispatch-context、implementer.md、P0-brief、P2-design（含 §1/§3/§6/§7/§8/§9）、P3-test-cases
- 已读：三份验收测试（ci_replay A2 / state_set A3 / obligations A4）+ helpers_tag0050.py
- 已读：agate-ci-verify.py（现状）、check-state-transition.py、check-obligations.py
## A3 实现（BDD-36..39）—— 已完成，4 用例转绿
- 新增 `agate/scripts/agate-state-set.py`（phase/meta/cancel/--list；原子替换 + git add；不写事件）
- `check-state-transition.py`：抽出纯函数 `check_transition(old,new,task_dir,state_file,state_basename,state_data)`，`main()` 与 state-set 共用
- `pre-commit-gate.py`：2h.1c（state_transition）+ 2h.1d（git add 账本）前移到 2g continue 之前；git add 失败可见（WARNING）
- `agate-next.py`：`_advance` 不再 append state_transition，改打印 agate-state-set 建议命令
- `agate-state-yaml-check.py`：非 legacy 任务写 status → ERROR（status 必填只对 legacy）
- 既有测试影响（A3 status 规则）：`test_pre_commit_hook.py` 的 `_write_state_yaml`（非 legacy 分支去 status）+ 两处直接写 status 的用例 → 61 passed
- 回归：`test_check_state_transition.py` 54 passed
## A4 实现（BDD-40..44）—— 已完成，5 用例 + 60 参数化用例转绿
- `check-obligations.py`：M 义务 enforced_at（ast 函数存在 + 必经路径闭包可达）、test（节点存在 + 引用 id）、R 义务 review_output、scope: protocol-repo 不计入 M 占比、baseline.reset
- `obligations.yaml`：60 条 M 补 enforced_at/test；F13 的 4 条 M 归 scope: protocol-repo；R 补 review_output；baseline.reset（60/123 → 56/119）
- 新增 `agate/tests/unit/test_tag0050_obligations_enforcement.py`（60 条 M 的 test 凭证载体）
- 实测：check-obligations rc=1（仅 4 条 F13 M 报 ERROR，符合 BDD-40）

## A2 实现（BDD-23..35）—— 12/13 转绿（BDD-31 为已知矛盾，见 P4-implementation-G1.md）
- 重写 `agate-ci-verify.py`（逐提交回放 + --base/--push + 协议版本选择 + CI-only 账本检查 + 耗时）
- `pre-commit-gate.py` 回放模式（AGATE_REPLAY：跳过 --fix、不写 .gate-result/.gate-history）
- `commit-msg-self-gate.py` 回放模式缺 trailer → exit 1
- 更新 `test_agate_ci_verify.py`（§8 第 8 项）
- 回归：unit 除 TAG0050 其它批 + 环境漂移外全绿；integration 除其它批（C/D）+ BDD-31 外全绿

## 登记面 / 收尾
- `agate/scripts/README.md`：新增 agate-state-set.py 索引行；更新 agate-ci-verify.py 描述
- `agate/tests/README.md`：补 agate-state-set / check-obligations / agate-ci-verify 映射行
- consistency 0 ERROR / 410 WARNING；structure exit 0；platform 0 命中；ruff All checks passed
- [PROD_NOT_TOUCHED]

## P4 G1-test-fix implementer 进度

- [x] 读 implementer.md 角色定义 + dispatch-context（G1-test-fix）+ P0-brief
- [x] 读 test_tag0050_ci_replay.py（BDD-23..35）+ helpers_tag0050.py + conftest 相关 fixture
- [x] 读设计 §2.4 版本选择规则 + P3-test-cases.md（BDD-23..35 段）+ P4-implementation-G1.md
- [x] 实测：`pytest test_tag0050_ci_replay.py -q` → 12 passed / 1 failed（仅 BDD-31）
- 观察：BDD-31 输出 `协议：merge-base 720c97d3 的 agate/`（走 §2.4 分支②）→ 未判 FAIL
- [ ] 实验：仅给 `_task_commit_repo` 写 `.agate-version`（选项 a），确认是否 13/13
- 实测结论：仅选项 (a)（`_task_commit_repo` 补 `.agate-version`）→ 仍 12 passed/1 failed（BDD-31）。
  原因：实现 `main()` 的「未固定版本 → FAIL」判定把 `AGATE_ROOT` 环境变量也算作 agateon-like
  （`not (agate_root_env or _repo_has_protocol_body(repo))`），使未写 `.agate-version` 的使用者
  项目也被判 PASS。设计 §2.4 分支②是「**仓库本身**含协议本体」，`AGATE_ROOT` 只是回放时**提供**
  协议根的输入，不是"项目固定了版本"的证据。
- 决定：实现改为按设计判定（分支③只认 `.agate-version` / 仓库协议本体），并把该判定放在
  「无任务改动 → SKIP」之后（BDD-34 无版本、无任务改动须 SKIP）。同步给 `_task_commit_repo`
  补 `.agate-version`；给 `_setup_failing_gate_repo` 补 `.agate-version` 以保其"回放 gate 失败"语义。

### G1-test-fix 完成

- 改动文件：
  - `agate/scripts/agate-ci-verify.py`：分支③（未固定版本 → FAIL）改为只认
    「仓库里的 `.agate-version`」或「仓库本身含协议本体」，不再把 `AGATE_ROOT` 环境当版本证据；
    该判定移到「无任务改动 → SKIP」之后（保 BDD-34）。docstring 同步。
  - `agate/tests/integration/test_tag0050_ci_replay.py`：`_task_commit_repo` 写 `.agate-version`
    （`agate: v0.79.0`）并 commit（钉版本 ⇒ 可回放）。断言未改。
  - `agate/tests/unit/test_agate_ci_verify.py`：`_setup_failing_gate_repo` 补 `.agate-version`
    （保其"回放 gate 失败"语义）。
  - `agate-workspace/.../P3-test-cases.md`：A2 段补「测试仓库口径」注。
  - `agate-workspace/.../P4-implementation-G1.md`：首个 `[DESIGN_GAP]` 标注「已修复」。
- 自查：`pytest test_tag0050_ci_replay.py -q` → **13 passed**；
  `pytest test_agate_ci_verify.py -q` → 6 passed；
  `check-platform-assumptions.py`（改动文件）→ rc=0；`ruff check agate-ci-verify.py` → All checks passed。
- 注：本修复除测试侧外，**必须**同时修正实现（原实现把 `AGATE_ROOT` 环境当"项目已固定版本"，
  致 BDD-31 永不 FAIL）——已在 DESIGN_GAP 记录中说明。
- [PROD_NOT_TOUCHED] 全程仅在 agateon 本 checkout 改代码/跑 pytest，未接触生产。

## G1-fix（SELF-GATE 整改，2026-10-08）

- 读了 dispatch-context（F1–F7）+ 评审报告 + implementer 角色 + P0-brief + P4-implementation-G1.md。
- 现状定位：F1 check-obligations.py:281-283 对 scope:protocol-repo 项仍跑 enforced_at/test；
  F2 pre-commit-gate.py:701-706 git add 在 gate_run(:750-761) 之前；F3 check-state-transition.py:185-212 无卡片块剔除；
  F4 agate-ci-verify.py:18-20 docstring 声称分支①；F5 无 PROD_TOUCHED 统计。
- 待读：设计 §2.4/§2.9/§8、test_check_state_transition.py、UPGRADING/WORKFLOW/state-machine/CHANGELOG、protocol-tests.yml、scripts/README。
[PROD_NOT_TOUCHED] 仅本 checkout 只读 + 后续改代码。

- F1 完成：check-obligations.py `_evaluate` 对 scope:protocol-repo 跳过 enforced_at/test → rc=0；
  test_bdd_40 改为临时构造（未改标→ERROR；改标→跳过），协调 BDD-40/44。obligations 65 passed。
- F2 完成：pre-commit-gate.py 新增 2h.1e（gate_run 之后再 git add 一次）+ 2h.1d 注释更新；
  test_tag0050_state_set.py 新增真实 commit 用例（已提交账本含 gate_run+state_transition）→ 5 passed。
- F3 完成：check-state-transition.py 新增 _strip_agate_card_blocks，BDD-3 扫描前剔除卡片块；
  test_check_state_transition.py 两向用例（卡内不触发/真实仍触发）→ 6 passed。

- F4/F7 完成：agate-ci-verify.py docstring 分支①降级为「未实现」；scripts/README.md 同步；
  P4-implementation-G1.md 登记 DESIGN_GAP（分支①未实现）。BDD-31 语义仍成立（无协议本体+无 .agate-version→FAIL）。
- F5 完成：agate-ci-verify.py 回放输出对 legacy 新增 PROD_TOUCHED ERROR 单独计数并列 SHA；
  test_tag0050_ci_replay.py 新增用例（15 passed）。
- 评审 #6 完成：push 口径 before 全零 → 回退 merge-base HEAD origin/<默认分支>；新增用例。
- F6 完成：UPGRADING.md 新增未发布 G1 节（.agate-version/fetch-depth/GitHub+GitLab 示例/squash/state-set 用法）；
  WORKFLOW.md CI 兜底口径改逐提交回放；state-machine.md phase 唯一写入口=agate-state-set；
  .github/workflows/protocol-tests.yml gate-backstop 加 fetch-depth:0 + 按事件传 --base/--push --base；
  CHANGELOG 条目按约定 P8 统一（P4-implementation-G1 §6 显式延期留痕）。
- 自查：pytest（ci_replay+state_set+obligations*）=85 passed；check-obligations rc=0；
  check-protocol-consistency 0 ERROR/410 WARNING（基线）；check-platform-assumptions rc=0；ruff All checks passed；
  test_check_state_transition/test_agate_ci_verify/test_pre_commit_hook/next/ledger 全绿。
- 未改（不在 F1–F7）：phase-cards 的「写 phase」表述（评审 A3-3 标 NEEDS_HUMAN_REVIEW）；A4-3/A4-5（BDD-42/43 弱化）。
[PROD_NOT_TOUCHED] 仅本 checkout 改代码 + 跑 pytest；未接触生产环境。

## G1-fix2（SELF-GATE 复评整改第 2 轮，2026-10-08）

依据 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1-rereview.md` 的 A4-3/A4-5/N1。

- 已读：implementer.md、dispatch-context（G1-fix2）、P0-brief、复评报告、test_tag0050_obligations.py、check-obligations.py、obligations.yaml、P4-implementation-G1.md、4 处协议文档。
- **H1（A4-3）真变异**：`test_bdd_42_negative_control_mutation` 重写——在 `tmp_path` 下构造协议根副本（`agate/{rules/obligations.yaml, scripts/, tests/unit/…}`），删掉 `OBL-P8-02` 的 `enforced_at` 后**端到端跑 `check-obligations.py`**（`AGATE_ROOT` 指向副本），断言 rc≠0 且报该 id；恢复后 rc=0。不再只读文本。
- **H2（A4-5）终态**：`test_bdd_43_r_without_review_output_errors` 重写——选 (a) 断言实际终态：缺 `review_output` → `_evaluate` ok=True 且 WARNING（即 rc=0）；合格评审产出 → 无告警；非法 → ERROR；并端到端断言真实 obligations.yaml 跑出 rc=0。docstring 写明设计原文 ERROR 已按 DESIGN_GAP 降级。
- **H3（N1）文档同步**：`platform-notes.md:342/344`、`phase-cards/P3-tdd.md:28`、`assets/templates/retrospective-template.md:144`、`state-machine.md:154` 均改为「逐提交回放 pre-commit + commit-msg hook」口径。
- 同步 `P4-implementation-G1.md` §3 的 review_output DESIGN_GAP：终态已被测试锁定 + BDD-42 改真变异。

### H1 负向验证（命令 + 输出）

命令（临时注释掉判据调用，跑完立即恢复）：
```
cp agate/scripts/check-obligations.py /tmp/opencode/check-obligations.py.bak
sed -i 's/^                _check_enforced_at(item, oid, reachable, errors)$/                pass  # NEGATIVE-CONTROL/' agate/scripts/check-obligations.py
python3 -m pytest agate/tests/unit/test_tag0050_obligations.py::test_bdd_42_negative_control_mutation -q
cp /tmp/opencode/check-obligations.py.bak agate/scripts/check-obligations.py   # 恢复
```
输出（判据被删 → 变异不再转红 → 用例真转红）：
```
FAILED agate/tests/unit/test_tag0050_obligations.py::test_bdd_42_negative_control_mutation
E       AssertionError: BDD-42：删判据后须转红，实际 rc=0
E       assert 0 != 0
1 failed in 0.60s
RESTORED_OK   # diff 确认脚本已逐字节恢复
```

### 自查（自查 ≠ gate）

- `pytest test_tag0050_obligations.py + test_tag0050_ci_replay.py + test_tag0050_state_set.py -q` → **25 passed**。
- `python3 agate/scripts/check-obligations.py` → **rc=0**（56/119，与基线一致；25 条 WARNING 为已知 R 缺 review_output）。
- `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（基线）。
- `ruff check`（改动测试文件）→ All checks passed。
- [PROD_NOT_TOUCHED] 仅本 checkout 改文件 + pytest tmp_path + /tmp/opencode 备份；未接触生产环境。

## G1-fix3（C8 整改第 3 轮，2026-10-08）

依据 `P4-review-cso-G1.md`（F-1/F-2/F-3/F-5）+ `P4-review.md`（C1/C2）的 K1–K6。

- 已读：implementer.md、dispatch-context（G1-fix3）、P0-brief、cso/review 两份评审、design §2.4/§2.9、
  agate-ci-verify.py、check-obligations.py、test_tag0050_ci_replay.py、test_tag0050_obligations.py、
  test_tag0050_obligations_enforcement.py、LEVELS.yaml、agate_common 等级函数、check-gate.py gate_p1/p2/p8/p7。
- K1 方案：`_ci_ledger_checks(repo, base, head)` 改用 `rev-list base..head`（**含合并提交**）+
  `diff --name-status --no-renames`（取源/目标路径），并在「无任务改动 → SKIP」**之前无条件**执行。
- K4 方案：新增 `_ci_level_checks`（新任务目录 contract_level ≥ merge-base 处 LEVELS.yaml 最大等级）。
- K2/K3 方案：为抽样的 M 义务写**真实行为凭证**（新文件 test_tag0050_obligation_behavior.py），
  `obligations.yaml` 的 test/enforced_at.function 指向精确函数；BDD-42 改为对**执行分支**做真变异。
- K5：分支①降级 DESIGN_GAP（已存在）+ docstring 写明。K6：P4-implementation-G1.md 写明锚点 advisory。
- [PROD_NOT_TOUCHED] 仅本 checkout 改代码 + pytest tmp_path。

### G1-fix3 K1 负向验证（命令 + 输出）

构造 evil merge 仓（`/tmp/opencode/k1repo`）：base 含 `task_created` 账本 → feature 非任务改动
→ 回主分支 `git merge --no-ff --no-commit` 并 `git rm` 账本 → 合并提交删除账本。

```
$ git log --oneline --graph -4
*   94dcef3 evil merge deletes ledger
|\
| * 4d7bc2b feature
|/
* 627b387 base
$ git cat-file -e HEAD:agate-workspace/tasks/TAG0001/gate-events.jsonl   # rc=128（不存在）
```

修复后（解耦，`rev-list` 含合并 + 无条件）：
```
$ AGATE_ROOT=<repo>/agate python3 .../agate/scripts/agate-ci-verify.py --base 627b387
  FAIL 账本: agate-workspace/tasks/TAG0001/gate-events.jsonl: 含创建/迁入事件的账本被删除/截空/改写（防降回 legacy）
CI-only 额外检查失败（1 账本 / 0 等级），回放范围 627b387a..94dcef38 未改动任务目录
CI_RC=1
```

模拟修复前（把解耦调用置空，复现「账本检查耦合进回放路径 + `--no-merges`」）：
```
$ AGATE_ROOT=<repo>/agate python3 /tmp/opencode/k1old/scripts/agate-ci-verify.py --base 627b387
SKIP: 回放范围 627b387a..94dcef38 未改动任务目录（1 个提交）
CI_RC=0        # ← 修复前静默通过（F-1 漏洞）
```
用例：`test_tag0050_ci_replay.py::test_k1_evil_merge_deletes_ledger_fails`（实测通过）。

### G1-fix3 K2/K3 负向验证（命令 + 输出）

在协议根副本上把 `check-gate.py` 的 `if "delivery:" not in p8_text:` 改为 `if False:`（删执行分支）：
```
$ MUTATED delivery branch in copy
$ AGATE_TEST_PROTOCOL_ROOT=/tmp/opencode/k2neg pytest \
    agate/tests/unit/test_tag0050_obligation_behavior.py::test_obl_p8_02_delivery_missing_blocks -q
FAILED ... test_obl_p8_02_delivery_missing_blocks
1 failed in 0.08s          # ← 新真实行为凭证：删执行分支 → 真转红
$ pytest \
    agate/tests/unit/test_tag0050_obligations_enforcement.py::test_obligation_enforced[OBL-P8-02] -q
1 passed in 0.03s          # ← 旧登记凭证（自指）：删执行分支仍绿（证明「真能证伪」差别的来源）
```
用例：`test_tag0050_obligations.py::test_bdd_42_negative_control_mutation`（对 6 条抽样 M 义务的
执行分支做真变异 → 断言对应真实行为用例转红；`test_bdd_42a_...` 保留检查器面负向控制）。

### G1-fix3 自查（自查 ≠ gate）

- `pytest test_tag0050_ci_replay + test_tag0050_state_set + test_tag0050_obligations +
  test_tag0050_obligation_behavior -q` → **34 passed**。
- `pytest test_agate_ci_verify + test_tag0050_obligations_enforcement + test_pre_commit_hook -q` → **127 passed**。
- `check-obligations.py` → **rc=0**（56/119）。
- `check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（基线）。
- `ruff check`（改动脚本/测试）→ All checks passed；`check-platform-assumptions.py` → rc=0。
- [PROD_NOT_TOUCHED] 仅本 checkout + `/tmp/opencode` 副本 + pytest tmp_path；未接触生产环境。

## G2（批次 B+C 合批）implementer 开工（2026-10-08）
- HEAD=54a814fc，分支 feat/TAG0050-task-data-contract。
- 三红灯文件现状（G2 前）：write_tools 6 red（BDD-45/47/48/49/50/51），prod_touched 2 red（BDD-54/55），fitness 1 red（schema_single_source）；BDD-46 已绿；**BDD-52/53 在 G2 前即绿但无判别力**（BDD-52 断言 rc≠0 实由 judge 要求触发、BDD-53 只断言快照文本）——**R1/R4 整改后重写为驱动真实强制点，方具判别力**（见下方 G2-fix 记录）。
- 关键既有测试约束：test_marker_single_source mk_7b/mk_8 从 pre-commit-gate.py 源码抽取字面 `re.match(r"...\[PROD_TOUCHED\]...")` ⇒ 不能删净该字面（与 dispatch "删字面正则" 冲突，须标 DESIGN_GAP）。
- agate-config BDD-3 要求源码不含 pytest/agateon/python3 token。
- BDD-45 要求 `set agent writer` rc=0 ⇒ 须解除 agent 写禁（与旧 TAG0024 §7.2 冲突，标 DESIGN_GAP）。

## G2 实现完成（2026-10-08）
- 批次 B：新增 `agate_schema.py`（校验/derive/render 单源）；`agate-md-field-set.py` 7 操作 + 渲染块；
  `agate-config.py` set/unset/explain；`check-frontmatter.py` F10；`check-gate.py` P6 渲染块防篡改；
  `check-yaml-schema.py`/`agate-frontmatter-check.py` 委托单源（含安装破损降级）。
- 批次 C：`markers.yaml PROD_TOUCHED=dash_only→default`；`pre-commit-gate.py` 安全门改调
  `agate_markers.pattern()` + 否定指引 + `prod_touched:true` 中止；快照 T1 去掉 PROD_TOUCHED。
- 快照 level-1.yaml 增 `files`/`declaration_files`/`traps`，重登记 LEVELS.yaml sha256。
- 自查：3 测试文件 14 passed；consistency 0 ERROR/410 WARNING；count-tests 2833（与 G1 同）；
  platform 0；ruff clean；全量 pytest 8 failed（全为既有预期红灯，与 54a814fc 比对确认无回归）。
- E3 抽样：agateon / peekview 各抽 50（seed=20261008）；人工分类误报 > 0 ⇒ 落 T1 降级，不启用 T1 ERROR。
  精确分类数字无仓内命令支撑，R7 整改时已删（抽样脚本+种子入库，见 P4-implementation-G2.md §4）。
- 6 条 [DESIGN_GAP] 见 P4-implementation-G2.md §5（agent 可写、F10/prod_touched 未接 hook、E3 降级、
  markers 字面副本保留、冻结快照同任务演进）。
- peekview 仅只读计数；无生产接触。

## G2 SELF-GATE 整改（R1–R7 + GAP-2）implementer（2026-10-08）
- 依据 `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G2.md`（1 BLOCKER R1 + R2–R7）。
- R1（BLOCKER）：`pre-commit-gate.py:_check_prod_touched_primary` 补「主产出缺 prod_touched → ERROR + 修复命令」；
  重写 `test_bdd_52` 驱动真实强制点（真实 git repo + pre-commit-gate.py）；`test_pre_commit_hook.py` 夹具补 frontmatter/prod_touched。
- R1 负向证据（改前红）：`python3 -m pytest agate/tests/integration/test_tag0050_prod_touched.py::test_bdd_52_missing_prod_touched_errors -q`
  → **1 failed**；输出 `AssertionError: BDD-52：须报缺字段，实际 'GATE P4: P4-review.md 不存在…GATE: 非 legacy 任务暂存了 P4 产出但未改 phase…'`
  （rc=1 来自 P4 gate，与 prod_touched 无关 ⇒ 证明旧断言无判别力）。
- R2：`check-frontmatter.py::_declaration_files()` 改读快照 `declaration_files`（fallback 仅安装破损降级）；
  `pre-commit-gate.py` 2g.2 改读同一快照键；新增 `test_bdd_47b` + `test_tag0050_r2_declaration_files_snapshot_effective` 锁定生效面。
- GAP-2：删 `AGATE_PRECOMMIT_GATE=1` 跳过（`check-frontmatter.py`）与 setdefault（`pre-commit-gate.py`），F10 在 gate 侧生效；
  随 R1 更新夹具（`test_pre_commit_hook.py` / `test_dispatch_context_warning.py`）。
- R3：`test_bdd_48` 断言 render 修复命令文案 + 补 LF/CRLF 双侧用例 + `windows_smoke` 标记。
- R4：`test_bdd_53` 补端到端中止用例；BDD-50 守护改机械判据（扫描 `iter_errors`/`max_depth` 族定义）+
  白名单 `agate-frontmatter-check.py` 降级副本（须门控 `agate_schema is not None`）。
- R5：`agate/scripts/README.md:164` 的 `agate-config.py` 命令集 → `init/validate/get/set/unset/explain/list/show`。
- R6：`agate/UPGRADING.md` 加「未发布 — TAG0050 批 G2」节；`design-md-field-set.md` §7.2 加注「已被 TAG0050 取代（ADR-014）」。
- R7：`P4-implementation-G2.md §4` 删无据精确数字、`e3_sample.py`（脚本+种子）入库并给仓内命令；§6 consistency 改浮动口径；
  `P4-progress.md:272` 自陈修正为 R1 闭合后的真判别力陈述。
- 自查（自查≠gate）：3 测试文件 14 passed；`test_pre_commit_hook + test_dispatch_context_warning` 62 passed；
  全量 `pytest unit+integration -n auto` **8 failed / 2720 passed / 2 skipped**（与 `54a814fc` 基线一致，无回归）；
  consistency **0 ERROR**；count-tests **2835**（2833+2）；platform 0；ruff clean。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest tmp_path；E3 抽样脚本已入库（非 `/tmp`）。

## G2 C8 整改（第 2 轮，B1/H1/F-2/F-3/M1/L1/L2/L5）implementer（2026-10-08）
- 已读：implementer.md、dispatch-context（G2-fix2）、P0-brief、P4-review-G2.md、P4-review-cso-G2.md、
  P4-implementation-G2.md、P4-progress.md、P1-requirements §4（BDD-45/46/49/52）、设计 §3.3/§4、
  agate-md-field-get.py、agate-md-field-set.py、agate_schema.py、pre-commit-gate.py、check-frontmatter.py、
  agate-config.py、agate-frontmatter-check.py、agate_common（level/contract 函数）、level-1.yaml、
  test_tag0050_write_tools/prod_touched/fitness、helpers_tag0050、conftest、agate-next-card/card-inject。
- 关键定位：md-field-get 无 derive 逻辑；md-field-set 的 prod_touched 仅 P6 契约可写；pre-commit-gate 的 CARD 块
  排除是纯文本；check-frontmatter 用 current_level（L1）；_primary_output_for 用 task_level（L2）。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest tmp_path；未接触生产环境。

## G2 C8 整改（第 2 轮）完成（2026-10-08）

改动文件：
- `agate/scripts/agate-md-field-get.py`（B1：`_system_field_spec` + `_get` 现算；非 legacy + 快照可用）
- `agate/scripts/agate-md-field-set.py`（F-2：契约驱动 `writer: system` 拒写；H1：`_declared_safety_keys` 主产出安全字段可写 + bool 强转；explain 跨文件来源）
- `agate/scripts/pre-commit-gate.py`（F-3：`_expected_card_hash`/`_card_block_verified`/`_added_lines_excluding_real_cards`；L2 注释）
- `agate/scripts/check-frontmatter.py`（L1：`_declaration_files(task_dir)` 按任务等级）
- `agate/tests/unit/test_tag0050_write_tools.py`（BDD-46 判别化、BDD-45 真往返、BDD-49 轻量、F-2、L5）
- `agate/tests/integration/test_tag0050_prod_touched.py`（BDD-49 真转绿、F-3 负向）
- `agate-workspace/tasks/TAG0050-task-data-contract/P4-implementation-G2.md`（状态/DESIGN_GAP/可辩护项）

### 改前红（负向控制，命令 + 输出）

B1（禁用 derive 分支）：
```
$ sed -i 's/        if spec is not None and spec.get("derive"):/        if False and spec is not None .../' agate/scripts/agate-md-field-get.py
$ pytest ...::test_bdd_46_system_field_reject_and_derive -q
E   - 2  + 999      ⇒ FAILED（读取返回文件值 999，证明用例有判别力）
$ 恢复 → diff 确认 RESTORED_OK
```
H1（去掉 `_declared_safety_keys`）：
```
$ pytest ...test_bdd_49_fix_command_executes_and_turns_green -q
E   AssertionError: BDD-49：修复命令须可执行，实际 "ERROR: 非法 key 'prod_touched'，合法 key 清单: …"
1 failed            ⇒ FAILED（证明旧可写面确实不可执行 prod_touched）
$ 恢复 → RESTORED_OK
```
F-2（禁用 writer:system 判定）：
```
$ pytest ...::test_f2_system_writer_field_rejected_by_contract -q
E   AssertionError: F-2：未来 writer: system 字段须被拒写，实际 'OK: results_total=5 已写入 P6-acceptance.md'
1 failed            ⇒ FAILED（证明契约驱动判定生效）
$ 恢复 → RESTORED_OK
```
F-3（把 `_card_block_verified` 置 True = 旧纯文本排除）：
```
$ pytest ...::test_f3_forged_card_block_still_blocks -q
E   AssertionError: F-3：伪造 CARD 块内的标记须仍拦，实际 ''
1 failed            ⇒ FAILED（旧行为下伪造块藏住标记、commit 通过）
$ 恢复 → RESTORED_OK
```

### 自查（自查 ≠ gate）

- `pytest test_tag0050_write_tools + test_tag0050_prod_touched + test_tag0050_fitness -q` → **19 passed**。
- `pytest test_pre_commit_hook.py -q` → **62 passed**。
- `pytest unit+integration -n auto` → **8 failed / 2726 passed / 2 skipped**（8 = 既有预期红灯 BDD-43/59/60/63/66/69/71/76，非回归）。
- `pytest regression -n auto` → **81 passed**。
- `check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（基线）。
- `count-tests.sh` → **2839**（G2 上轮 2835 +4 = 4 条新增用例）。
- `check-platform-assumptions.py` → rc=0；`ruff check`（改动文件）→ All checks passed。
- 可辩护项：L2（注释说明结构面/时间面）、L3（保留偏宽 fail-safe 并声明）、L4/L6（已裁定）；M2 登记为后续批待办（DESIGN_GAP）。
- [PROD_NOT_TOUCHED] 仅本 checkout 改代码 + pytest tmp_path + `/tmp/opencode` 备份；未接触生产环境。

## 批 D 前置 hotfix（I-2，`agate-run` 基线比对缺陷）implementer（2026-10-08）

- 已读：`implementer.md`、dispatch-context（hotfix-I2）、P0-brief、设计 §5 前置条件（:505）、
  `agate-run.py`、`test_agate_run.py`、`agate/scripts/README.md`、`agate/UPGRADING.md`、conftest fixtures。
- 环境隔离：[PROD_NOT_TOUCHED]（仅本 checkout 改代码 + pytest tmp_path；未接触生产环境）。
- HEAD=`f21b314e`（G2 已提交），分支 `feat/TAG0050-task-data-contract`。

### 改前红（负向证据，命令 + 输出）

```
$ timeout 600s python3 -m pytest agate/tests/unit/test_agate_run.py -q -k hotfix_i2
FFF.                                                                     [100%]
3 failed, 1 passed, 10 deselected in 0.34s
```
- `test_hotfix_i2_plain_run_returns_command_exit_code_with_stale_evidence` → rc=1（陈旧证据假失败；应为 0）
- `test_hotfix_i2_plain_run_propagates_nonzero_with_stale_evidence` → rc=1（应为命令退出码 7）
- `test_hotfix_i2_baseline_mismatch_prints_real_diff` → 输出只有「diff 已客观报出」字样、无 `---`/`+++`/`-alpha`/`+beta`
- `test_hotfix_i2_baseline_first_write_...`（首次落盘：语义不变的回归守护）→ 改动前即绿

### 实现

- `agate/scripts/agate-run.py`：
  - 删 `:189-190` 的 `elif`——普通运行**不做**基线比对，`return exit_code`（命令自身退出码）；
  - `--baseline` 不一致时新增 `_baseline_diff()`（`difflib.unified_diff`，`fromfile=baseline`/`tofile=current`）
    **实际打印逐行 diff** 再返回 1；逐行相同但逐字节不同时给出字节级提示（保证总有可读证据）；
  - 首次落盘语义不变（`--baseline` 且文件不存在 → 写证据、不 mismatch）；docstring 同步。
- `agate/tests/unit/test_agate_run.py`：新增 4 条回归用例（普通运行+陈旧证据 rc 归命令自身 /
  普通运行失败 rc 归命令自身 / `--baseline` 打印真实 diff / 首次落盘）。
- 文档同步：`agate/scripts/README.md` agate-run 行（普通运行不做比对 + 不一致打印 diff）；
  `agate/UPGRADING.md` 新增「未发布 — TAG0050 批 D 前置 hotfix」节。

### 自查（自查 ≠ gate）

- `pytest agate/tests/unit/test_agate_run.py -q` → **14 passed**（含 4 新增）。
- `check-protocol-consistency.py` → **0 ERROR / 410 WARNING**（基线）。
- `check-platform-assumptions.py` → rc=0（无命中）。
- `bash agate/tests/scripts/count-tests.sh` → **2843**（G2 C8 上轮 2839 +4）。
- `ruff check agate-run.py test_agate_run.py` → All checks passed。
- `git status --porcelain` → 仅 3 改动 + 1 新增测试文件，无账本污染（测试全在 tmp_path）。
- [PROD_NOT_TOUCHED]


## G3（D+E+F 合批）implementer 开工（2026-10-08）
- HEAD=b746d07d，分支 feat/TAG0050-task-data-contract。
- 已读：implementer.md、dispatch-context-G3、P0-brief、设计 §3.1/§5/§6/§7/§8/§10、P1 §4、P2 §1/§3、P3-test-cases。
- 定位：三个"目标测试文件"实际在 unit（declarations/proxy_judgment/cross_batch），非 dispatch 所写 integration；evidence 在 integration。
- 目标红灯现状（5 文件 25 节点，7 failed / 18 passed）：BDD-59/60/63/66/69/71/76 红；其余 18 已绿（多数因 `!=0` 由无关失败满足，弱判别力）。
- 待读：check-gate.py gate_p1/p2/p6/p7/p8 + :964/:1450、agate_common、md-field-set/get、debt-check、pruning、judge-verdict、agate-run、extract-context、check-p6-evidence、level-1.yaml、markers.yaml。
- 环境隔离：[PROD_NOT_TOUCHED]

## G3（D+E+F 合批）实现完成（2026-10-08）
- HEAD=b746d07d；产出 P4-implementation-G3.md。
- **G3-0（E2）**：实测命令写入路径 gate 失败 0 次（rc=0），散文路径 gate 失败 ≥1 次（check-gate P7 rc=1）；
  token 增量仅一条 <80 字符命令，未登记为代价。见 P4-implementation-G3.md §0。
- **批 D**：`resolve_evidence_ref`（相对路径 / `run:<k>`，区分事件缺失与 sha256 不匹配）；`agate-run --task`
  + 任务内 `runs/<k>.log` + `cmd_run` 三字段；`gate_p6` 非 legacy 结构化 D1/D2/D3/D4/D6/D8/D10；
  `check-judge-verdict` 读 `criteria`；`agate-extract-context` P7/P8 按字段现算 + 单参形式；
  2h 段非 legacy 跳过 `check-p6-format`；gitignore 取反 + 父目录排除提示。
- **批 E**：`gate_p7` 跨文件聚合（含 design_gaps↔reviews 集合、悬空 id、resolved 缺证据、findings 计数为系统字段）；
  `basis: followup:DEBT<n>` 双向回指；`agate-debt-check` 增 `source_ref`；markers.yaml 补 5 标记；
  md-field-set 自动编号 `<相对路径去 .md>:<前缀><n>`；scope-resolved/retrospective 读聚合。
- **批 F**：`reviewed_bdds`；P2 `ui_design` na 无 reason；骨架标题级判定（RM-AG0085）；P8 `delivery` 结构化（F12）；
  `check-pruning` `pruned` 闭合（RM-AG0087）；T2 绊线。
- 8 条 [DESIGN_GAP]（见 P4-implementation-G3.md §4）。
- 自查（自查≠gate）：目标 5 文件 25 passed；全量 2840 passed/2 skipped/**1 failed**（唯一 = 既有环境漂移
  `test_setup_agate_dir.py::test_bdd_43`：本机 opencode `debug agent`→`debug agents`，与
  P3-test-cases §1 登记的「非本任务失败」一致）；consistency 0 ERROR/410 WARNING；platform rc=0；
  count-tests 2843；ruff clean。
- 修复的回归：`test_bdd_42_negative_control_mutation`（恢复 OBL-P8-02 变异锚点字面行）；
  `test_hook_evidence_warning_low_variance_not_blocked`（非 legacy 无 results 回退既有判定）。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest tmp_path + /tmp/opencode 演示；无账本污染。

---

## G3-fix（SELF-GATE 整改 · 第 2 轮，2026-10-08）

- 依据：`docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G3.md`「闭合后…清单」+ 主 Agent 三项裁定。
- **GAP-1**：`gate_p6` 非 legacy 改由契约单源（`requirement_active(...,"results","P6")`），缺 `results` 即
  ERROR；快照 `requires.results` 翻真。负向证据：T086 夹具改 structured results 前 gate P6 红。
- **GAP-2**：`reviewed_bdds` 必填且 = P1 BDD 集合；`conftest.init_task` + `_write_p1_review` 夹具补字段；
  负向证据：改前 `test_bdd_71` 因 P1 无 `#### BDD-` 命中 reviewed_bdds 集合差，T2 被掩盖 → 已将 T2 前移。
- **GAP-4**：`phase_universe` 改 `[P1..P8]`；`check-pruning` **恒检**闭合；`pruned` 条目必填 `phase/reason/risk`。
  夹具：`_P1_REQ`/it9/it9b/it10 的 P1 去掉 P0、补 pruned（负向证据：改前 5 条 hook 用例因 "多=['P0']" 转红）。
- **GAP-5**：快照注册 `ui_design.shape_dimensions`/`delivery`/`pruned`；`_gate_p2_ui_design_section` 补「必填
  维度存在」判据（layout→布局/交互/视觉）；`gate_p8` delivery 规格改读快照。新增 `test_gap5_*`（红→绿）。
- **GAP-6**：D5（内容重复 WARNING）/D7（evidence JSON vs results）/D9（`_p6_reuse_blocked`）+ D3 pre-commit
  「已跟踪或已暂存」（`AGATE_PRECOMMIT_GATE` 标记）。新增 `test_gap6_d5/d7/d9`。
- **GAP-7**：`check-p6-provenance.py` 按 `task_level` 跳过审计 1/3/4/5/6（正文解析）+ 审计 6，与 D7 成对。
  新增 `test_gap7_provenance_body_audit_skipped_for_non_legacy`。
- **GAP-8**：`declaration_files` 扩展为 glob（含 `*-review.md`/`P4-implementation-*.md`/`P4-implementation/**/*.md`）；
  删 `declaration_globs`；`check-frontmatter`/`pre-commit-gate`/`agate-md-field-set` 改 glob 匹配。新增 `test_gap8_*` 两条。
- **A1**：UPGRADING/CHANGELOG 去掉过度承诺、D1–D10 只列实际落地项。
- **A2**：README 登记 `agate-extract-context` 单参形式 + 4 脚本行为变化。
- **A3**：task-files.md / phase-cards{P1,P2,P6,P7,P8} / verifier+consistency-reviewer+requirements-review 角色卡 /
  WORKFLOW「Pre-commit 检查总览」反向传播新结构化字段与跳过行为。
- **A4**：test_bdd_56（A/B/C）、57/58（改走 gate_p6 D3/D6）、59（真构造 sha256 不一致）、60（断言计数==现算值）、
  62/64/65（判别性断言）。
- **A5**：`gate_p2` UI `na` 检查加 `task_level` 门；**R6 复跑** → legacy 39 任务 / 差异 0 / 未匹配 0 / exit 0。
- E2 裁定 `[HUMAN_CONFIRMED: 2026-10-08]` 记入 P4-implementation-G3.md §0。
- 自查（自查≠gate）：目标 6 文件 **94 passed**；全量 **2840 passed/2 skipped/1 failed**（唯一 = 既有环境漂移
  `test_bdd_43`）；consistency 0 ERROR/410 WARNING；platform rc=0；count-tests **2850**；R6 exit 0。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest tmp_path + `/tmp/opencode`（R6 在 `cp -r` 副本、跑毕删除）；无账本污染。

---

## G3-fix2（C8 整改 · 第 2 轮，2026-10-09）

- 输入：`P4-review-G3.md`（BLOCKER-1 + MINOR-2/3/4）、`P4-review-cso-G3.md`（F-1..F-6）、主 Agent 裁定。
- 复现 BLOCKER-1：非 legacy 缺 `criteria` → `criteria_total 缺失或非整数`；补系统字段后仍
  `非 legacy 任务须在 frontmatter 声明 criteria`（`read_judge_verdict` 丢弃 `criteria`）。
- 计划：BLOCKER-1（透传 criteria + 校验后移 + 正/负用例 + 文档一致）；MINOR-2（D8 读 vision 三态）；
  MINOR-3（D7 双向/形态/多 JSON 合并）；MINOR-4（gate_p7 取值域枚举）；F-1（run: sha256 fail-closed）；
  F-2（declaration_files 匹配语义单源）；F-3（run: 空日志）/F-4（P7 计数登记系统字段）/F-5/F-6（声明）。

### G3-fix2 完成记录（2026-10-09）

- **BLOCKER-1 修复**：`read_judge_verdict` 透传 `criteria`；`check-judge-verdict.py` 三系统字段强校验
  后移至非 legacy 现算之后。正/负用例各 1（正向改前为红）。文档承诺修好即成立。
- **MINOR-2**：D8 读 `read_vision_tri_state`（GAP→manual_review / 否则→vision）；截图结构化判定。
- **MINOR-3**：D7 扩为双向 + 证据形态 + 多 JSON 合并（4 用例）。
- **MINOR-4**：`gate_p7` design_gap_reviews 的 `verdict`/`basis` 取值域枚举（2 用例）。
- **cso F-1**：`run:<k>` 的 cmd_run 事件缺 k/log/sha256 → fail-closed（1 用例）。
- **cso F-2**：`declaration_files` 匹配语义单源（`agate_common.match_declaration_file`/
  `declaration_file_paths`/`task_dir_for_file`），6 消费方统一 glob 语义（2 用例）。
- **cso F-3**：核实改前未被 D3/D6 覆盖 → 已修（run: 空日志 → ERROR，1 用例）。
- **cso F-4**：P7 `blocker_count`/`deviation_critical_count` 登记为系统字段（LEVELS 重登记 sha256，1 用例）。
- **cso F-5/F-6**：显式声明边界（见 P4-implementation-G3.md §9.7）。
- **[DESIGN_GAP]×1**：P7 计数 derive 取 severity 口径（算子无法表达 open∧severity；门禁不读该字段）。
- 自查：目标 5 文件 **107 passed**；全量 **2863 passed/2 skipped/1 failed**（唯一 = 既有环境漂移
  `test_bdd_43`）；consistency **0 ERROR/410 WARNING**；platform rc=0；count-tests **2866**（+16）；
  ruff 全绿；**R6** 于仓外副本（`/tmp/opencode/r6copy`，提交使树干净后运行）→ legacy 39 / 差异 0 /
  未匹配 0 / exit 0，跑毕删除副本。
- [PROD_NOT_TOUCHED] 仅本 checkout + pytest tmp_path + `/tmp/opencode`；`git status` 无账本污染。

## P8 反向传播整改：TAG0042 BDD-8/21 断言随截止约定变更更新

- 派发：`P8-dispatch-context-implementer-fix.md`（主 Agent 裁定选项①：测试随新语义更新，不留假绿）。
- 输入已读：implementer.md、dispatch-context、P0-brief、review（A3/A4）、两测试文件、UPGRADING 新语义节（L474-505）。
- 旧断言（改前）：
  - `test_agate_config.py::test_bdd_8_upgrading_documents_cutoff_version` 末条 `re.search(r"v?0\.\d+\.\d+|截止版本", upgrading)`（要求「截止版本号」）——改后无版本号，靠全文其它版本号假绿。
  - `test_gate_layer.py::test_bdd_21_upgrading_documents_preset_migration_and_cutoff` 末条 `re.search(r"截止版本", text)`——靠历史节/无关 judge 截止假绿。
- 新语义（UPGRADING L481-484 批 2 / L502-505 批 4）：「硬切**未排期**」+ 指向 `RM-AG0102` + 「本协议不预告实施版本号」。
- 改法：断言改为在对应小节内同时出现「未排期」与「RM-AG0102」；不再要求版本号/「截止版本」字样。

### 改前红证据（隔离副本，不触碰真实仓库）
- 构造：`/tmp/opencode/agate-old-root/`（`git show HEAD:agate/UPGRADING.md`，即 TAG0050 P8 改动前的旧语义「截止版本：v0.80.0」，无「未排期」/`RM-AG0102`）。
- 命令：`AGATE_ROOT=/tmp/opencode/agate-old-root python3 -m pytest <两测试> -q`
- 结果：`2 failed`（BDD-8 断在 `"未排期" in section`；BDD-21 断在 `"未排期" in section`）→ 证明新断言真实锁定新语义，非靠无关命中假绿。
- 对照（当前工作区新语义）：同两测试 `2 passed`。

### 自查结果（自查≠gate）
- `python3 -m pytest agate/tests/unit/test_agate_config.py agate/tests/unit/test_gate_layer.py -q` → `17 passed`，RC=0。
- `bash agate/tests/scripts/count-tests.sh` → `总计：2866`（未增删用例数）。
- `python3 agate/scripts/check-protocol-consistency.py` → `仅有 410 个 WARNING，无 ERROR`，RC=0。
- 状态标记：`[PROD_NOT_TOUCHED]`（仅编辑两个测试文件，未接触生产）。
