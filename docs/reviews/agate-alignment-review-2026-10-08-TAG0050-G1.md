---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 合批 G1（A2 CI 逐提交回放 + A3 state-set/状态事实 + A4 义务机械核验）的协议-脚本对齐审查
files_changed: [agate/scripts/agate-ci-verify.py, agate/scripts/agate-state-set.py, agate/scripts/check-state-transition.py, agate/scripts/pre-commit-gate.py, agate/scripts/agate-next.py, agate/scripts/agate-state-yaml-check.py, agate/scripts/commit-msg-self-gate.py, agate/scripts/check-obligations.py, agate/rules/obligations.yaml, agate/scripts/README.md, agate/tests/README.md, agate/tests/integration/test_pre_commit_hook.py, agate/tests/integration/test_tag0050_a0_a1_ledger.py, agate/tests/integration/test_tag0050_ci_replay.py, agate/tests/unit/test_agate_ci_verify.py, agate/tests/unit/test_dispatch_context_warning.py, agate/tests/unit/test_tag0027_b1_agate_next_cli.py, agate/tests/unit/test_tag0050_obligations_enforcement.py]
---

# 协议-脚本对齐审查 — TAG0050 合批 G1（A2 + A3 + A4）

> 模式：SELF-GATE **Layer 1 · 变更触发**。对象 = `git status` 的 G1 改动（未提交，HEAD `b0a16c3a`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
> 只读纪律：全程未写被评审文件；变异/回放实验只在 `/tmp/opencode` 副本与 pytest `--basetemp` 内进行。`[PROD_NOT_TOUCHED]`。

## 意图分析（第一步）

**为什么改**：G1 一次性落地三个互相独立、都只依赖已落地 A1 的子系统——
① **A2** 把 `agate-ci-verify` 从"重跑当前 phase gate"（恒 SKIP/假 PASS，F15）改为**在 hook 当时的条件下逐提交回放本地 hook**，把可信锚点从本地账本（无密钥）移到 CI；
② **A3** 新增 `agate-state-set` 作为 phase/meta/cancel 的**唯一写入口**、把状态转移判定抽成 `check_transition` 纯函数、并让所有 phase 变化（含进入 PAUSED/READY/DONE）都由 pre-commit 统一写事件；
③ **A4** 把 `obligations.yaml` 的 M 义务从"作者自标"改为**机械核验**（`enforced_at` ast 可达 + `test` 凭证 + `review_output`），修复 F13。

## 反向传播（第二步）——应被影响文件

| 文件 | 为何应被影响 | 实际是否动 | 判据 |
|---|---|---|---|
| `.github/workflows/protocol-tests.yml` | A2 需 `fetch-depth: 0` 才能算 merge-base/rev-list（设计 §2.4 点6；G1 dispatch line 29） | **未动** | `git status` 无此文件 |
| `agate/UPGRADING.md` | A2 需写明 `.agate-version` / `fetch-depth: 0` / GitHub+GitLab 示例 / squash 说明（G1 dispatch line 30） | **未动** | 同上 |
| `agate/scripts/README.md` | 新增 `agate-state-set.py` 登记行 + `agate-ci-verify.py` 描述更新 | 已动 ✓ | diff |
| `agate/tests/README.md` | 脚本→测试映射 | 已动 ✓ | diff |
| `agate/rules/obligations.yaml` schema | A4 新增 `enforced_at`/`test`/`review_output`/`scope`/`baseline.reset` | 已动 ✓ | diff |
| `agate/state-machine.md` / `phase-cards/*` | A3 起 phase 只能经 `agate-state-set` 写入；卡片仍写"写 phase: Pn" | **未动**（NEEDS_HUMAN_REVIEW，见 A3b） | `grep -rln agate-state-set agate/*.md agate/phase-cards/` = 0 |
| `CHANGELOG.md` | A4 基线重设需写入 | **未动**（dispatch line 46 声明留痕归 P8，见 A5） | `git diff --stat CHANGELOG.md` 空 |

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（6 项，见下） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（docstring/README/注释声称与实现不符） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（workflow / UPGRADING 未同步；RM-AG0101 未落地） |
| A4 | 测试覆盖 | **MISALIGNED**（3 处验收面未被测试覆盖 + 负向控制非真变异） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（workflow / UPGRADING / CHANGELOG 未动） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW**（新增架构决策是否补 ADR） |
| A8 | 声称-命令绑定 | **ALIGNED**（见下，410/411 差异已定位非 G1 缺陷） |

> **门禁状态**：`check-protocol-consistency.py` = **0 ERROR / 411 WARNING**（我的实跑；主 Agent 记 410，差异由**本次审查的 progress 文件**落入 `docs/reviews/` 冻结扫描面引入，非 G1 缺陷，见 A8）；G1 验收测试 `65 + 17 = 82 passed`（与主 Agent 一致）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

#### A1-1 `check-obligations.py` 恒红，BDD-44「转绿」未达成（**BLOCKER 级**）

**文档声明**（`P1-requirements.md:356-359` BDD-44）：
> Then **转绿**；此后 M 占比下降仍判 FAIL（恢复"只增不减"）。

**文档声明**（设计 `design-tag0050-task-data-contract.md:341`）：
> | **CI 才执行的义务** | 归入 `scope: protocol-repo`，单独统计，不计入 M 占比 | — |

**脚本实现**（`check-obligations.py:281-289`）：
```python
if disposition == "M":
    _check_enforced_at(item, oid, reachable, errors)   # ← 对 scope: protocol-repo 项也执行
    _check_test_node(item, oid, repo_root, errors)
```
`scope: protocol-repo` 只在 `:274-276` 影响**占比计数**，不影响 `enforced_at` 可达性核验。

**实跑证据**：
```
$ python3 agate/scripts/check-obligations.py ; echo EXIT=$?
...
CHECK-OBLIGATIONS: FAIL OBL-P2-12: enforced_at 的 check-tdd-red.py::main 不在必经路径上（不可从 hook/check-gate 到达）
CHECK-OBLIGATIONS: FAIL OBL-X-10: enforced_at 的 agate-ci-verify.py::main 不在必经路径上（不可从 hook/check-gate 到达）
CHECK-OBLIGATIONS: FAIL OBL-X-17: enforced_at 的 check-debt.py::main 不在必经路径上（不可从 hook/check-gate 到达）
CHECK-OBLIGATIONS: FAIL OBL-X-19: enforced_at 的 check-platform-assumptions.py::main 不在必经路径上（不可从 hook/check-gate 到达）
EXIT=1
```
这 4 条正是设计指定要归 `scope: protocol-repo` 的 F13 项（`obligations.yaml:294/907/971/990`）——**改标后仍判 ERROR**，故工具**恒红**，与 BDD-44 的「转绿」直接冲突。`P4-progress.md:80` 自述"check-obligations rc=1（仅 4 条 F13 M 报 ERROR，符合 BDD-40）"——把 BDD-40（检测能力）当成了终态，忽略了 BDD-44（转绿）。

**结论**：MISALIGNED。
**建议**：对 `scope: protocol-repo` 项跳过 `_check_enforced_at`/`_check_test_node`（设计 §2.9 表其性质为「—」）；同时**必须协调 BDD-40 与 BDD-44 的冲突**（BDD-40 断言 `rc != 0`、BDD-44 断言转绿，同一终态不可兼得）——建议把 BDD-40 用例改为"未改标时能检测出 ERROR"的临时构造，而非对最终登记表的终态断言。

#### A1-2 `gate_run` 事件不再随本次提交入库（**回归，静默**）

**文档声明**（设计 §2.7 `:301`；`pre-commit-gate.py:698-700` 注释）：
> 把 `pre-commit-gate.py` 的 2h.1c（写入 `state_transition`）和 2h.1d（`git add` 账本）**一起**移到 2g 的 `continue` 之前…
> `# 2h.1d … 把本 hook 追加的 state_transition（以及后续 gate_run）写入 gate-events.jsonl 并 git add`

**脚本实现**：`git add`（`pre-commit-gate.py:701-706`）现在位于 `append_event(gate_run)`（`:750-761`）**之前**；旧位置（`2h.1b` 之后）的 `git add` 已被删除（见 diff）。⇒ 普通阶段下 `gate_run` 在 `git add` 之后追加，**不被暂存**。

**实跑证据**（`/tmp/opencode` 副本，`--basetemp`）：
```
$ python3 -m pytest 'agate/tests/integration/test_pre_commit_hook.py::test_pt_binary_2_prod_not_touched_passes' -q --basetemp=/tmp/opencode/bt_pt2   # 1 passed
$ cd /tmp/opencode/bt_pt2/... && cat agate-workspace/tasks/T001/gate-events.jsonl          # 工作区：3 行（含 gate_run）
$ git show HEAD:agate-workspace/tasks/T001/gate-events.jsonl                                # 已提交：2 行（无 gate_run）
$ git diff HEAD -- agate-workspace/tasks/T001/gate-events.jsonl | grep '^+'
+{"cmd":"check-gate.py P5","event":"gate_run",...,"ts":"2026-10-07T21:07:02.993101Z"}   # ← gate_run 未入库
```
即：**每次正常提交，其 `gate_run` 事件都留在工作区、不进本次 commit**（下次提交才被前一次 `git add` 带上）。设计 §8 第 6 项（`gate_run` 账本字节）与 TAG0042 BDD-12 的"gate_run 随本次提交入库"被破坏。

**结论**：MISALIGNED。
**建议**：把 `2h.1d` 的 `git add` 拆成两处（进入 PAUSED/READY/DONE 前补一次 + 2h.1b 之后保留原处），或把 `2h.1c/2h.1d` 只前移 `state_transition` 的写入、`git add` 仍在 `gate_run` 之后执行。

#### A1-3 `RM-AG0101`（BDD-3 关键词扫描排除 `AGATE_CARD` 块）未落地

**文档声明**（`P2-design.md:82` A3 批次行、`:405` G4 裁决；`roadmap.md:100` 状态 = `scheduled（并入 TAG0050 批 A3）`）：
> `check-state-transition.py` 抽纯函数…**并让 `_scan_bdd3_keyword_phases()` 扫描排除 `<!-- AGATE_CARD_START -->…<!-- AGATE_CARD_END -->` 块**（RM-AG0101，单 owner）+ 两向回归用例。

**脚本实现**（`check-state-transition.py:185-212`）：`_scan_bdd3_keyword_phases()` 仍对整文件做 `any(kw in text ...)`，**无卡片块排除**。

**证据**：`grep -c "AGATE_CARD" agate/scripts/check-state-transition.py` → **0**。

**结论**：MISALIGNED（A3 已声明的交付面缺失）。
**建议**：实现卡片块剔除 + 两向回归用例（仅卡内"重派"不触发；`P*-progress.md` 真实"重派"仍触发）。

#### A1-4 A2 协议版本分支①（`.agate-version` 选协议）未实现

**文档声明**（设计 §2.4 优先级表 `:220-226`；G1 dispatch line 25）：
> ① **项目 `.agate-version` 固定的版本** … **逐提交读取 C 树中的 `.agate-version`**… 回放时显式设置 `AGATE_ROOT` 指向选定的协议

**脚本实现**（`agate-ci-verify.py:140-161` `_resolve_protocol`）：**只**看 `AGATE_ROOT` 环境（→ 其仓库 merge-base）或"仓库本身含协议本体"（→ merge-base）。`.agate-version` 仅用于**单调不降检查**（`:328-341`），**不用于选协议根**。

**后果**：BDD-31 的"补救"（写 `.agate-version`）对**无协议本体、无 `AGATE_ROOT`** 的使用者项目**无效**——`_resolve_protocol` 返回 `(None,None,None)` → `:355-356` 仍判 FAIL。docstring（`:18-20`）却声称实现了①。

**结论**：MISALIGNED。
**建议**：要么实现①（按逐提交 `.agate-version` 定位/安装对应版本目录），要么把 docstring/README 的①降级为"未实现（依赖 CI 安装各版本）"并登记 DESIGN_GAP。

#### A1-5 A2 §8 第 12 项（legacy 新增 PROD_TOUCHED ERROR 单独统计）未实现

**文档声明**（设计 §8 补记 `:619-624`；G1 dispatch line 31）：
> 改由**批 A2 的 `agate-ci-verify` 逐提交回放 pre-commit** 承担… **单独统计并逐条列出**。

**脚本实现**：`agate-ci-verify.py` 无 `PROD_TOUCHED` 相关统计/输出（全文 grep 0 命中）。

**结论**：MISALIGNED。
**建议**：在回放输出中对 legacy 新增 PROD_TOUCHED ERROR 单独计数并列 SHA。

#### A1-6 A2 push 口径 `before` 全零未特判

**文档声明**（设计 §2.4 表 `:186`；G1 dispatch line 22）：
> GitHub push … `before` 为全零时取 `merge-base HEAD origin/<默认分支>`。

**脚本实现**（`agate-ci-verify.py:315-317`）：
```python
if args.base:
    base = args.base if args.push else (_git_out(["merge-base", args.base, head], repo) or args.base)
```
`--push --base 0000…` 时 `base` 直接取全零 → `rev-list` 失败 → `:323-324` `_fail`。无全零回退。

**结论**：MISALIGNED（低危，但为显式交付面）。
**建议**：`--push` 且 `before` 全零 → 回退 `merge-base HEAD origin/<默认分支>`。

### A2: 脚本→文档对齐 — MISALIGNED

| 位置 | 声称 | 实际 |
|---|---|---|
| `agate-ci-verify.py:18-20` docstring | "① 项目 `.agate-version`（逐提交读…）" | `_resolve_protocol` 不按 `.agate-version` 选协议（A1-4） |
| `pre-commit-gate.py:698-700` 注释 | "把…（以及后续 gate_run）…git add" | gate_run 在 git add 之后追加，未入库（A1-2） |
| `.github/workflows/protocol-tests.yml:298` 注释 | "它**实际重跑** gate 判定" | 已是逐提交回放，注释陈旧（A3-1） |
| `agate/scripts/README.md:106` `agate-ci-verify.py` 行 | 描述 `--base/--push`、协议版本选择、AGATE_REPLAY | 描述大体正确，但"协议版本逐提交读 `.agate-version`（降级判 FAIL）"会被读成"按 `.agate-version` 选版本"，与实现不符 |

**结论**：MISALIGNED。
**建议**：改 docstring/注释/README 与实现一致，或补实现。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

#### A3-1 `protocol-tests.yml` 未同步（A2 前置 `fetch-depth: 0` 缺失）

**文档声明**（设计 §2.4 点6 `:246`；G1 dispatch line 29）：`CI 检出必须设置 fetch-depth: 0`。
**实际**（`.github/workflows/protocol-tests.yml:284-309`）：`gate-backstop` job 用裸 `actions/checkout@v4`（**无** `fetch-depth: 0`），且调用 `python3 agate/scripts/agate-ci-verify.py`（**无** `--base`）。shallow 检出下 `merge-base HEAD origin/main` 失败 → `_skip("无法解析 merge-base…")` → **gate-backstop 恒 SKIP**（正是 F15 要修的假绿被换了个形式复活）。

**结论**：MISALIGNED。
**建议**：`gate-backstop` 加 `fetch-depth: 0`（无需许可；`required` 才需许可），并按 PR/push 事件传 `--base`。

#### A3-2 `UPGRADING.md` 未同步

**文档声明**（G1 dispatch line 30）：`UPGRADING.md`：`.agate-version` / `fetch-depth: 0` / GitHub+GitLab 示例 / squash 仓库说明。
**实际**：`git status` 无 `agate/UPGRADING.md`；grep 无 `fetch-depth`/`ci-verify` 相关新节。

**结论**：MISALIGNED。**建议**：补 UPGRADING 章节。

#### A3-3 反向传播（NEEDS_HUMAN_REVIEW）：phase 唯一写入口未在协议文档体现

A3 起 phase 只能经 `agate-state-set` 写入（设计 §2.7 `:270`），但 `agate/state-machine.md` 与 `phase-cards/*` 仍以"写 `phase: Pn`"表述（如 `P8-release.md:15`、各卡"推进条件…写 phase: Pn"），**全文无 `agate-state-set` 引用**（`grep -rln agate-state-set agate/*.md agate/phase-cards/` = 0）。
无法机械判定是否属 G1 交付面（dispatch 未列卡片；设计 §10 A3 验收锚也未含卡片）→ 交人工：若卡更新留待 P8/文档批，请在 P4 记录显式声明。

### A4: 测试覆盖 — MISALIGNED

**实跑输出**（本次审查执行）：

```
$ python3 -m pytest agate/tests/unit/test_tag0050_obligations.py agate/tests/unit/test_tag0050_obligations_enforcement.py -q
65 passed in 0.37s

$ python3 -m pytest agate/tests/integration/test_tag0050_ci_replay.py agate/tests/integration/test_tag0050_state_set.py -q
17 passed in 10.86s

$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py agate/tests/unit/test_dispatch_context_warning.py -q
24 passed in 4.27s

$ python3 -m pytest agate/tests/unit/test_check_state_transition.py agate/tests/integration/test_pre_commit_hook.py -q
115 passed in 44.33s
```
G1 验收面 **82 passed**（65+17），与主 Agent 一致。

**但**：测试全绿**未覆盖**下列 G1 语义（⇒ 假绿灯风险）：

- **A4-1 `gate_run` 随提交入库无测试**：全仓无"真实 commit 后读**已提交**账本断言 gate_run"的用例（`grep -rn gate_run agate/tests/` 仅静态账本与 `agate-run` 用例）。故 A1-2 的静默回归无人拦。
- **A4-2 BDD-38 未验"随本次提交入库"**：`test_tag0050_state_set.py::test_bdd_38` 只 `h.run_gate(...)`（**直接调 hook**）后读**工作区**账本（`:49-54`），未用真实 `git commit`，也未读已提交账本。这**违反 P2 §3 口径**（`:209` "A3 的验收用例**必须用真实 `git commit` + 指向 checkout 协议的 hook**"）。
- **A4-3 BDD-42 负向控制非真变异**：设计 BDD-42 要求"删掉 OBL-P8-02 对应的**判断分支** → `test` 转红"；`test_tag0050_obligations_enforcement.py:86-92` 只读 `obligations.yaml` 断言 `enforced_at` 文本存在——**删脚本分支不会转红**，只有删 YAML 字段才会。`P4-implementation-G1.md:72` 已自述"未做逐条判据分支 mutation"（自认 DESIGN_GAP，但无 P7 REVIEWED-ACCEPTED ⇒ 按角色原则 6 计 MISALIGNED）。
- **A4-4 分支①/全零/squash/§8-12 无测试**：`.agate-version` 使用者项目可回放、push 全零、squash push 账本检查、legacy PROD_TOUCHED 统计，均无用例。
- **A4-5 BDD-43 用例被弱化**：`test_tag0050_obligations.py:47-52` 只断言文本含 `review_output`，不断言"缺则 ERROR"（实现已降为 WARNING，见 A4 备注）。

**结论**：MISALIGNED。**建议**：补 A4-1/A4-2 的真实提交级用例；BDD-42 落成真变异抽样（或补 P7 REVIEWED-ACCEPTED 记录）。

### A5: 下游影响 + 文档传播 — MISALIGNED

- **workflow**：未同步（A3-1）——`gate-backstop` 仍无 `fetch-depth: 0`，注释陈旧。
- **UPGRADING.md**：未同步（A3-2）。
- **CHANGELOG.md**：A4 基线重设（60/123 → 56/119）未写入。G1 dispatch line 46 声明"CHANGELOG 实际留痕归 P8"——**属显式延期**，请 P4 记录保留该声明（非 MISALIGNED，仅登记）。
- **`agate/scripts/README.md` / `agate/tests/README.md`**：已同步 ✓。
- **兼容承诺（§8）**：legacy 退出码与 ERROR 集合——既有测试改动均在 §8 允许面内（第 7/8/10 项 + A3 status 规则），我核对 `test_agate_ci_verify.py`（第 8 项）、`test_tag0027_b1_agate_next_cli.py`（第 7 项）、`test_pre_commit_hook.py`/`test_dispatch_context_warning.py`/`test_tag0050_a0_a1_ledger.py`（A3 status）——**均在例外内**，无越界改动。

**结论**：MISALIGNED（workflow/UPGRADING）。

### A6: 锚点表覆盖 — ALIGNED

- `check-protocol-consistency.py` = **0 ERROR**（实跑），`check-obligations.py` 的锚点 keywords `["obligations.yaml","M 类占比","无归宿"]` 在脚本文本中仍字面存在。
- 新增 `agate-state-set.py` 为 `agate-*.py`，按 `P1-requirements.md` §3.3 实测**不触发** CHECK9/SG.6（登记面判据 `uncovered_gate_scripts()`），`agate/scripts/README.md` 已补索引行；consistency 0 ERROR 佐证。

**结论**：ALIGNED。

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

- 相关 ADR（`agate/adr.md`）：ADR-001（隔离性）、ADR-002（可判定性）、ADR-004（安全网分层）、ADR-005（改动性质决定流程）。G1 三项（CI 可信回放 = 把判定移出本地可信边界；`agate-state-set` = 状态写入单点；义务机械核验 = 可判定性）总体与 ADR-002/004 同向。
- **但**：G1 引入两个新的架构决策——① "CI 回放以本地 hook 的**当时协议版本**为可信锚点"（版本选择/缓存策略）；② "phase 的唯一写入口是独立 CLI"。二者均未见于现有 ADR。是否需补 ADR 由人工裁决。

**结论**：NEEDS_HUMAN_REVIEW（`[HUMAN_CONFIRMED: 待填]`）。

### A8: 声称-命令绑定 — ALIGNED

| 声称 | 产出命令 | 结论 |
|---|---|---|
| G1 验收测试 82 passed | `pytest test_tag0050_ci_replay.py test_tag0050_state_set.py`（17）+ `pytest test_tag0050_obligations*.py`（65） | 复核通过（82） |
| `check-protocol-consistency.py` 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | 复核通过（0 ERROR） |
| consistency WARNING = 410 | 同上 | **本次得 411**——差异定位为**本次审查的 progress 文件**（新建于 `docs/reviews/`，落入 CHECK2-refs 冻结扫描面），**非 G1 缺陷** |
| check-obligations "符合 BDD-40"（`P4-progress.md:80`） | `python3 agate/scripts/check-obligations.py` | rc=1 可复现；但该声称**掩盖**了 BDD-44「转绿」未达成（见 A1-1） |

**结论**：ALIGNED（无"不可复核"声称；`P4-progress.md:80` 的措辞偏差归 A1-1）。

---

## 需修复项汇总（MISALIGNED）

| # | 项 | 位置 | 修复方向 |
|---|---|---|---|
| 1 | `check-obligations` 恒红，BDD-44 未达成 | `check-obligations.py:281-289` | scope: protocol-repo 项跳过 enforced_at/test；协调 BDD-40/44 |
| 2 | `gate_run` 未随提交入库 | `pre-commit-gate.py:701-706` vs `:750-761` | `git add` 保留在 gate_run 之后（或在 2h.1b 后补 add） |
| 3 | RM-AG0101 未落地 | `check-state-transition.py:185-212` | 排除 AGATE_CARD 块 + 两向用例 |
| 4 | A2 分支① `.agate-version` 未实现 | `agate-ci-verify.py:140-161` | 实现或降级 docstring + 登记 DESIGN_GAP |
| 5 | A2 §8 第 12 项未实现 | `agate-ci-verify.py` | legacy PROD_TOUCHED ERROR 单独统计 |
| 6 | A2 push 全零未特判 | `agate-ci-verify.py:315-317` | 全零回退 merge-base |
| 7 | workflow 未同步 | `.github/workflows/protocol-tests.yml:284-309` | `fetch-depth: 0` + `--base`；更新注释 |
| 8 | UPGRADING 未同步 | `agate/UPGRADING.md` | 补 A2 章节 |
| 9 | 测试覆盖缺口（gate_run / BDD-38 提交级 / BDD-42 变异） | 测试面 | 补用例 |

## NEEDS_HUMAN_REVIEW 汇总

- **A3-3**：phase 唯一写入口未在 `state-machine.md` / phase-cards 体现（是否属 G1 交付面待定）。
- **A4 备注**：BDD-43"缺 review_output → ERROR"实现为 WARNING（`P4-implementation-G1.md:72` 自认 DESIGN_GAP，无 P7 REVIEWED-ACCEPTED）——请人工确认是否接受降级。
- **A2 备注**：commit-msg 回放用**当前**协议而非回放协议（`agate-ci-verify.py:213-216`，DESIGN_GAP #4）。
- **A2 备注**：回放循环遍历 `commits`（全部）而非 `task_commits`（`agate-ci-verify.py:361`）——与设计"只回放改动任务目录的提交"字面冲突，但为满足 BDD-27（协议本体提交回放）所需；请人工裁定设计措辞。
- **A7**：是否补 ADR（CI 回放可信锚点 / phase 唯一写入口）。

> 每条 NEEDS_HUMAN_REVIEW 须有对应 `[HUMAN_CONFIRMED: 日期 确认：理由]` 才可 commit；未确认等同 MISALIGNED。

## 闭环建议

MISALIGNED 项（尤其 #1 #2 #3 #7）必须修复后重审；建议按"先修脚本（#1 #2 #3 #6）、再补 workflow/UPGRADING（#7 #8）、再补测试（#9）"顺序。`P4-implementation-G1.md` 的 DESIGN_GAP 若确为有意偏离，应走 P7 consistency-reviewer 的 `REVIEWED-ACCEPTED` 留痕，而非停留在 P4 自述。
