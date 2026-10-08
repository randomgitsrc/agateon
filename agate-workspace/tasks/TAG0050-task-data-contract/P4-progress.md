
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
