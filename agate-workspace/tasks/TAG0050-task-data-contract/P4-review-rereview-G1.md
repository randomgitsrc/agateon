---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G1.md
trace_id: TAG0050-P4-20261008
agent: review
status: approved
created: '2026-10-08'
---

# P4 聚焦复审（第 3 轮整改后）— TAG0050 批 G1（A2 + A3 + A4）

> 角色：`review`（偏执 Staff Engineer）。
> 对象：G1 未提交改动，HEAD `b0a16c3a`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 范围：**只核 K1–K6 是否闭合 + 是否引入新阻断**（不重开全量）。
> 依据：`P4-dispatch-context-review-G1-rereview.md`；`P4-review.md`（C1/C2）、`P4-review-cso-G1.md`（F-1/F-2/F-3/F-5）。
> 只读纪律：未编辑任何被评审文件；全部验证在**仓外可丢弃副本** `/tmp/opencode/tag0050-rr3` 上进行；
> 真实仓库未执行任何破坏性或写仓命令（仅跑只读 `check-protocol-consistency.py` 取基线）。
> `[PROD_NOT_TOUCHED]`（未接触生产环境）。

## 0. 汇总结论

**`status: approved`** —— K1–K6 **全部 ALIGNED**（含独立复现的 K1/K2 负向控制）。
另记 **1 项 [MEDIUM]（非本批引入、非阻断）**：`_ci_ledger_checks` 的账本路径过滤过宽，
会把 `agate/tests/fixtures/**/gate-events.jsonl` 测试夹具当真实账本而误报 FAIL（详见 §8）。
无 [CRITICAL]、无阻断项。

| # | 整改项（来源） | 判定 | 证据锚点 |
| --- | --- | --- | --- |
| K1 | cso F-1（BLOCKER）合并提交静默删/改账本，A2 漏检 | **ALIGNED** | §2：独立 evil-merge 构造 → `FAIL 账本` rc=1；因果证明（加 `--no-merges` 即退化为 `SKIP` rc=0）；`git mv` 源路径亦拦 |
| K2 | cso F-2（HIGH）M 义务核验空转 | **ALIGNED** | §3：删执行分支 → 真实行为 `test` 真转红（基线绿/变异红）；设计 §2.9 允许抽样 |
| K3 | review C1（CRITICAL）A4 凭证自指 | **ALIGNED** | §3：同 K2 根因；`obligations.yaml` 6 条 `test` 改指真实行为凭证 |
| K4 | review C2（CRITICAL）A2 等级检查缺失 | **ALIGNED** | §4：`_ci_level_checks` 落地；`test_bdd_30`（真构造不误报）/`test_bdd_30b`（低于则 FAIL）转绿 |
| K5 | cso F-5（MEDIUM）分支①未实现 | **ALIGNED** | §5：docstring 显式「未实现」+ F-5 影响 2 降级；`P4-implementation-G1.md` `[DESIGN_GAP]` |
| K6 | cso F-3 锚点 advisory | **ALIGNED** | §6：`P4-implementation-G1.md` 专节写明「gate-backstop 未设 required ⇒ advisory」 |

## 1. 环境与验收面复核（命令 + 输出）

仓外副本 `/tmp/opencode/tag0050-rr3`（`rsync -a --exclude site/ --exclude archived/ --exclude node_modules/`，**含 `.git`**）。

```
# G1 验收面（A2+A3+A4，fix3 后）
$ python3 -m pytest agate/tests/integration/test_tag0050_ci_replay.py \
    agate/tests/integration/test_tag0050_state_set.py \
    agate/tests/unit/test_tag0050_obligations.py \
    agate/tests/unit/test_tag0050_obligation_behavior.py -q -p no:cacheprovider
34 passed in 19.24s

# 登记凭证 + CI 工具 + 既有 hook
$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py \
    agate/tests/unit/test_tag0050_obligations_enforcement.py \
    agate/tests/integration/test_pre_commit_hook.py -q
127 passed in 40.10s

# 兼容回归（首轮 §5 同口径）
$ python3 -m pytest test_check_state_transition.py test_agate_ci_verify.py \
    test_tag0027_b1_agate_next_cli.py test_dispatch_context_warning.py \
    test_pre_commit_hook.py test_tag0050_a0_a1_ledger.py \
    test_agate_state_yaml_check.py test_check_state_yaml.py -q
183 passed in 55.56s

# A4 工具终态
$ python3 agate/scripts/check-obligations.py ; echo rc=$?
M 类占比: 56/119 = 0.4706（基线 56/119 = 0.4706）
CHECK-OBLIGATIONS: OK（无「无归宿」项 + 无 ERROR + M 类占比不低于基线）
rc=0

# 门禁（真实仓库，只读）：与基线一致
$ python3 agate/scripts/check-protocol-consistency.py
仅有 410 个 WARNING，无 ERROR。

# 静态
$ ruff check <改动脚本/测试>        → All checks passed!
$ check-platform-assumptions.py <改动文件> → rc=0
```

> 副本 `check-protocol-consistency` 报 411–412 WARNING（因 `--exclude archived/` 造成
> `agate-workspace/archived/` 556 文件缺失的噪声）；**真实仓库取值为准 = 0 ERROR / 410 WARNING**，与基线一致。

## 2. K1 —— 合并提交静默删账本（独立负向控制）

**实现**（`agate/scripts/agate-ci-verify.py`）：账本最终状态检查 `_ci_ledger_checks(repo, base, head)`
（`:288-330`）与逐提交回放**解耦**——① 枚举 `rev-list <base>..<head>`（`:300`，**含合并提交**，
不依赖 `--no-merges` 过滤后的 `commits`）；② `diff --name-status --no-renames`（`:307`）同时取
改名被摘除的**源路径**；③ 在「无任务改动 → SKIP」**之前无条件**执行（`main` `:460-461`）。

**独立复现（仓外，从零构造 evil merge）**：base 含 `task_created` 账本 → feature 非任务改动
→ 回主分支 `git merge --no-ff --no-commit` + `git rm` 账本 → 合并提交删除账本。

```
$ git log --oneline --graph -4
*   7a3d5a1 evil merge deletes ledger
|\
| * de4223d feature
|/
* 978cba3 base
$ git cat-file -e HEAD:agate-workspace/tasks/TAG0001/gate-events.jsonl ; → ABSENT
$ AGATE_ROOT=<副本>/agate python3 <副本>/agate/scripts/agate-ci-verify.py --base 978cba3
  FAIL 账本: agate-workspace/tasks/TAG0001/gate-events.jsonl: 含创建/迁入事件的账本被删除/截空/改写（防降回 legacy）
CI-only 额外检查失败（1 账本 / 0 等级），回放范围 978cba34..7a3d5a19 未改动任务目录
CI_RC=1
```

**因果证明（证明「解耦 + 含合并」是拦下的原因，非偶然）**：把 `_ci_ledger_checks` 的
`rev-list` 加回 `--no-merges`（复现修复前 `commits` 过滤），同一仓库同一输入即退化：

```
$ AGATE_ROOT=<副本>/agate python3 <变异脚本> --base 978cba3
SKIP: 回放范围 978cba34..7a3d5a19 未改动任务目录（1 个提交）
CI_RC=0
```

**附加（F-4 同源面）**：`git mv` 把含 `task_created` 的账本移入既有任务目录——
`--no-renames` 使源路径出现 → `FAIL 账本: .../TAG0001/gate-events.jsonl: ...被删除/迁空/改写`，`CI_RC=1`
（对照 `git diff --name-only` 默认改名检测**只输出目标路径**，看不到源被摘除）。

**结论：K1 ALIGNED**（原有漏洞已闭合；负向控制由我方独立复现，非仅采信实现者自述）。

## 3. K2/K3 —— M 义务真实行为凭证（独立负向控制）

**实现**：
- `obligations.yaml` 6 条 M（抽样覆盖 P1/P2/P8）的 `test` 改指**真实行为凭证**
  `agate/tests/unit/test_tag0050_obligation_behavior.py::test_obl_<...>`，`enforced_at.function`
  精确到 `gate_p8` / `_gate_p1_vision_capability` / `_gate_p2_ui_design_section` / `_gate_p2_dispatch_plan`
  （如 `OBL-P8-02`，`obligations.yaml:713-720`）。
- 其余 54 条仍指登记参数化节点（`...obligations_enforcement.py::test_obligation_enforced[<id>]`），
  作「登记存在」辅助断言。
- 行为凭证**加载真实脚本模块**，构造违约输入，调用 `enforced_at.function` 断言判失败
  （`test_tag0050_obligation_behavior.py:56-110`）。

**独立复现（删执行分支 → 凭证转红）**：在协议根副本上把 `check-gate.py` 的
`if "delivery:" not in p8_text:` 改为 `if False:`（`:1474`），以 `AGATE_TEST_PROTOCOL_ROOT` 指向副本：

```
# 基线（真实根）
$ pytest ".../test_tag0050_obligation_behavior.py::test_obl_p8_02_delivery_missing_blocks" -q
1 passed in 0.04s
# 删执行分支后（副本根）
$ AGATE_TEST_PROTOCOL_ROOT=/tmp/opencode/k2neg pytest <同节点> -q
FAILED .../test_tag0050_obligation_behavior.py::test_obl_p8_02_delivery_missing_blocks
1 failed in 0.08s
```

⇒ 凭证**对「义务是否真被执行」敏感**（非自指）。`test_tag0050_obligations.py::test_bdd_42_negative_control_mutation`
（`:212-239`）对 6 条抽样逐条做该端到端变异；保留 `test_bdd_42a_...`（检查器面）作双面覆盖。

**设计依据**：设计 §2.9 明确「A4 的负向控制以 mutation 方式**抽样**执行，每批至少覆盖本批新增或改动的
M 项」（`design-tag0050-task-data-contract.md:337`）；BDD-42 原文含「（以及本批抽样的其他 M 项）」。
抽样 6 条覆盖 P1/P2/P8 三阶段，符合设计授权。

**结论：K2 ALIGNED、K3 ALIGNED**（同根因修复；凭证不再自指）。

## 4. K4 —— A2 新任务等级检查

**实现**：`_ci_level_checks(repo, base, head)`（`agate-ci-verify.py:370-402`）——对 `<base>..<head>`
中新出现的任务目录（`status A`），读其账本首个 `task_created`/`task_adopted` 的 `contract_level`，
要求 **≥ `base`（= merge-base）处 `LEVELS.yaml` 最大等级**（`_levels_max_at` `:333-347`）；
不足则输出 `FAIL 等级`。

**用例（验收面已转绿）**：
- `test_bdd_30_branch_crossing_upgrade_no_false_report`（`:138-171`）**真构造**跨升级场景：
  base 处 LEVELS=L1、分支新增任务 L1、随后 LEVELS 升 L2 → 断言**无** `FAIL 等级`（merge-base 仍 L1，不误报）。
- `test_bdd_30b_new_task_below_merge_base_level_fails`（`:174-196`）：base 处 LEVELS=[1,2]、
  新增任务 L1 → 断言 `FAIL 等级` 且 rc≠0。

**真实历史冒烟（无假阳性）**：对 `720c97d3..b0a16c3a` 跑 `_ci_level_checks` → `level_errors=[]`。

**结论：K4 ALIGNED**。

## 5. K5 —— 协议版本分支①降级

`agate-ci-verify.py` docstring `:18-30` 显式写明分支①**未实现**（不用于选协议根）、
且补齐 **F-5 影响 2**「对缺失 `.agate-version` 的提交不判 FAIL」的已知绕过面降级；
`P4-implementation-G1.md` 有两处对应 `[DESIGN_GAP]`（`:76`，及 §K5 `:142-143`）。
`scripts/README.md` 同步降级（G1-fix F4/F7）。

**结论：K5 ALIGNED**（选取「docstring 降级 + DESIGN_GAP」，二选一已明确）。

## 6. K6 —— 锚点 advisory 定性

`P4-implementation-G1.md:146-152`「K6 — 回放锚点当前为 advisory（不构成阻塞合并的可信锚点）」
明确写明：`.github/workflows/protocol-tests.yml` 的 `gate-backstop` **未设 required check**
（workflow 注释 2026-10-05「已移出 required」），故逐提交回放在本仓当前 CI 下为 **advisory**，
回放失败**不阻塞合并**，「可信锚点」在取得 required 许可前**不成立**。

**结论：K6 ALIGNED**。

## 7. 新引入问题排查

- **改动文件一致性**：fix3 触及 `agate-ci-verify.py` / `obligations.yaml` / 两份测试 + 新行为凭证 /
  `P4-implementation-G1.md` / `P4-progress.md`，未见触碰无关模块。
- **平台无关**：`check-platform-assumptions.py`（全部改动文件）rc=0；新凭证用 `tmp_path` +
  `AGATE_TEST_PROTOCOL_ROOT`，无硬编码系统临时目录、无裸解释器名。
- **回归**：§1 的 34 + 127 + 183 全绿；未观测到 fix3 引入的回归。
- **无新阻断**（下述 §8 为**非本批引入**）。

## 8. [MEDIUM]（非本批引入、非阻断）账本检查路径过滤过宽 → 测试夹具误报

**位置**：`agate/scripts/agate-ci-verify.py:315` —— `_ci_ledger_checks` 仅以
`path.endswith(_LEDGER_NAME)` 判「账本」，**未限定 `agate-workspace/tasks/` 前缀**，
故把 `agate/tests/fixtures/task-data/level-1/{pass,fail}/gate-events.jsonl`（**契约等级黄金夹具**）
当作真实任务账本跑 `check_ledger_events`。

**证据**（仓外副本，`AGATE_ROOT` 指向正确协议根）：

```
$ AGATE_ROOT=<副本>/agate python3 -c "_ci_ledger_checks(cwd,'720c97d3','b0a16c3a')"
 - agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl: task_upgraded 的等级 0 未登记（第 2 行）
 - agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl: task_upgraded 等级未严格递增（1 → 0，第 2 行）
 - agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl: task_upgraded 等级未严格递增（from 1 → to 0，第 2 行）
count=3
```

`fail` 夹具是**有意非法**的（负向黄金样本），故只要其引入/修改提交落在 `<base>..<head>`
（本分支 A1 提交 `b0a16c3a` 即如此），`ci_extra_failed=True` → **CI 回放报 FAIL**（gate-backstop 为
advisory，不阻塞合并，但属**假阳性**，与 K1 修复的本意相悖）。

**非本批引入（已核）**：从首轮评审副本 `/tmp/opencode/tag0050-review/agate/scripts/agate-ci-verify.py`
取 pre-fix3 原文，其 `_ci_ledger_checks` 同样以 `... .endswith(_LEDGER_NAME)` 过滤（旧版 `:289`），
**不含** tasks 前缀；fix3 的改动只是把它从「耦合回放路径」变为「无条件 + 含合并 + `--no-renames`」，
路径过滤面未变。⇒ 属存量缺陷，非本轮整改引入。

**附带观察（环境相关）**：当运行环境存在 `~/.agate` 且仓库**未**写 `.agate-version`（如本机）时，
`_check_one_ledger_text` → `check_ledger_events` 经 `resolve_agate_root` 解析 LEVELS 会落到**已安装稳定版**
（本机实测 `registered_levels=[]`，因 v0.79.0 无 `rules/task-data/`），使**合法** `pass` 夹具也被报
「等级 1 未登记」（实测该场景下 errors 由 3 增至 5）。这是 `_check_one_ledger_text` 未把回放协议根
透传给 `check_ledger_events` 所致，同样**非 fix3 引入**，GitHub 干净 runner（无 `~/.agate`）下经脚本
路径上溯可解析到仓库 LEVELS 而不触发。

**建议（供主 Agent 决定，评审不改代码）**：
- 首选：`_ci_ledger_checks` 的路径过滤加 `path.startswith(_TASKS_PREFIX)` 限定（一行），
  并补一条「fixture 变动不触发账本 FAIL」的回归用例；
- 或（若判为范围外）登记 DEBT 并在 `P4-implementation-G1.md`/`squash` 口径注释中显式记账。
-（K2/K3 的 6/60 抽样比例，设计 §2.9 已授权，属可接受范围，不计为本项问题。）

## 9. 独立复现证据（全部在仓外副本 `/tmp/opencode/tag0050-rr3` 与一次性仓）

```
# K1 evil-merge（从零构造）
/tmp/opencode/k1rr  → FAIL 账本 / CI_RC=1
# K1 因果证明（账本检查回退 --no-merges）→ SKIP / CI_RC=0
# K1 git mv 源路径 → FAIL 账本 / CI_RC=1
# K2 删执行分支 → 真实行为 test FAILED；基线 passed
# 验收面 34 passed；enforcement+ci_verify+hook 127 passed；回归 183 passed
# check-protocol-consistency（真仓）0 ERROR / 410 WARNING
```

## 10. 环境隔离

`[PROD_NOT_TOUCHED]` 全程只在仓外副本 `/tmp/opencode/tag0050-rr3`（含 `.git`）与一次性
`/tmp/opencode/{k1rr,k1mv,k2neg}` 内做克隆/变异/pytest；仅对真实仓库跑过只读的
`check-protocol-consistency.py` 取基线。未编辑任何被评审文件，未对真实仓库执行破坏性或写仓命令。

## 11. 门槛判定

- **`status: approved`** —— K1–K6 全部 ALIGNED，K1/K2 负向控制经独立复现，无新阻断。
- 唯一 [MEDIUM]（§8，`_ci_ledger_checks` 路径过滤过宽）**非本批引入、非阻断**，
  建议随本批补一行前缀限定 + 回归用例，或登记 DEBT 留痕后放行。
- 返回主 Agent：`File: agate-workspace/tasks/TAG0050-task-data-contract/P4-review-rereview-G1.md` /
  `Status: approved`。
