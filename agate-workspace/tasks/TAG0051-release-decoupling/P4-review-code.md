---
phase: P4
task_id: TAG0051
parent: P4-implementation.md
trace_id: TAG0051-P4-review-code
type: review
agent: review
domain: backend
status: approved
created: 2026-10-11
prod_touched: false
---
# P4 代码评审（review / 偏执 Staff Engineer，C8：`backend`）— TAG0051 任务与发布解耦
## 增量复审（retry 1，覆盖更新）

> **评审对象**：P4 实现的**修复轮**工作区（R-A 脚本/CI/wrapper、R-B 文档/规则/ADR、R-C 12 测试文件、
> R-D R6 allowlist；**全部未提交**）。**首轮本文件获批的是"修复前"的树**；本轮为增量复审。
> **评审基线**：`HEAD=d4e32f4f`（P3 提交）+ 工作区改动（**含 R-A..R-E 全部修复轮**——§0 首段落笔后
> 并发 R-E retry 2 落地，本文件已**据此二次核验并更新**）。**定稿快照 pin**
> `sha256(工作区 diff + 两个新增文件)=9843650…d2579`（间隔复算稳定）。
> **评审方式**：只读核验（未编辑/删除任何被评审文件；未对真仓跑任何写类 git 或写类工具）。
> 所有**写副作用实测**在 `/tmp/opencode` 一次性副本上完成，「创建→操作→清理」同一次 bash 调用；
> 只读 `read`/`grep`/`git diff` 直读真仓；跑后核验真仓 `git status --porcelain` 的**新增项全部来自
> 主 Agent 并发产物**（见 §5 注），**无我造成的写入**。
> **协议版本**：`AGATE_ROOT=/home/kity/.agate/v0.81.0/agate`；分支 `task/TAG0051-release-decoupling`。

---

## 0. 结论

**`approved` —— 0 个 CRITICAL。**

增量复审确认：① 首轮 **6 条 INFORMATIONAL** 中，**4 条已在本轮修复**且经**独立实测闭合**
（INFO-1 文档面、INFO-2 wrapper 祖先、INFO-5 fail-open，以及首轮 §3 的文档残留类——由 R-E 收口）；
② 首轮 **Pass-1 六个 CRITICAL 项重跑后仍全部成立**，其中 **fail-closed 更强**
（SEC-01/SEC-09 把「required 空 + 零 check-run」从 fail-open 改为 fail-closed）；③ R-C 的 12 个测试
文件**未发现「为变绿而放宽」**——被改写的断言多为**正向重定向**（`WARNING not in output` + 新载体
`check-changelog.py … ==1`），**判据强度不降反升**；④ 唯一新增的实质健壮性缺口是 **N1（wrapper
`cp -a` 在含 `.worktrees/` 的真实仓库上失败，rc=1）**——**非 CRITICAL**（方向 fail-closed、与环境
相关、且 BDD-20 证据已用底层脚本独立复现），建议在 P5 前处置。

> **本轮新析出**：`N1`（模块级健壮性，中）、`N3`（断言风格，低）。`N2`（文档传播残留）**已由并发
> R-E retry 2 定向收敛并经本文件核验闭合**（见 §4）。**均非 CRITICAL，不构成打回理由**（依角色文件：
> 无 BLOCKER/CRITICAL ⇒ approved）。

> ✅ **快照边界已闭合**：审阅期间并发落地的 `R-E retry 2`（纯文档/注释传播收敛）**已完成落地**，
> 本文件已就 **post-R-E 定稿树**（pin `9843650…d2579`）复核：`check-protocol-consistency.py
> --strict-errors-only` = **rc 0 / 0 ERROR**、`check-structure-consistency.py` = rc 0、定向 doc/SG 用例
> **125 passed**（§5）。故 **本 `approved` 反映的就是将提交的最终树**。

---

## 1. 首轮 6 条 INFORMATIONAL 的闭环核验

| 首轮项 | 本轮处置 | 独立核验 | 结论 |
|--------|---------|----------|------|
| **INFO-1** `WORKFLOW.md:327` / `state-machine.md:400-408` / `P5-verification.md:147` 仍述 P8 version/bump/tag | R-B + R-E 改写 | **实读确认**：`WORKFLOW.md:327` P8 行已去 version/bump/双路径/tag（改为 `bump_type` 意图 + 结构化 delivery + roadmap 反查 + `check-changelog.py`）；`state-machine.md` P8→READY 转移行 / `:400-406` gate 步骤 / `:320-330` 说明节全部收敛；`state-transitions.md` / `phases.yaml` 亦改；**`P5-verification.md:147` 已由 R-E 改为「交付收尾后重跑 P5」** | **全闭合 ✓** |
| **INFO-2** wrapper `--dst` 为 `--src` **祖先**未拦 | R-A 补 | **实测**（/tmp/opencode 合成目录）：`--dst /tmp/opencode/wtest`（src 父）= rc **2** 拒绝、无删除；另 `--dst /` / 相对 / 空 / src 内 / ==src / **allow-prefix 之外（`/home/kity/...`）** 全 rc 2；src 与旁路 `keepdir` **存活** | **已闭合 ✓**（且新增「严格落在允许前缀下」更严） |
| **INFO-3** 默认 `--dst` 固定共享路径并发竞争 | 未处置 | 默认仍 `$TMP/opencode/tag0051-r6-corpus`（`:77`） | **仍开（非阻塞）** |
| **INFO-4** `workflow_dispatch` 用 `--sha "$GITHUB_SHA"`（ref HEAD）而非 tag 提交 | 未处置（`release.yml:105` 仍 `--sha "$GITHUB_SHA"`） | 见 `release.yml`：clone 步 `--branch "$TAG"`、build 带 `--expect-sha "$GITHUB_SHA"` | **仍开（非阻塞，净 fail-closed）** |
| **INFO-5** required 空 + 零 check-run ⇒ fail-open | R-A 补 SEC-01 | **实测**：`--ci-cmd` 注入 `[]` ⇒ rc **1**（修复前 rc 0）；`--sha ""` ⇒ rc 1（SEC-09） | **已闭合 ✓** |
| **INFO-6** `concurrency.group` 两条触发路径取值不同 | 未处置 | `release.yml:21` 仍 `release-${{ github.ref_name }}` | **仍开（非阻塞）** |

---

## 2. Pass-1 CRITICAL 重跑（修复轮改动面重验）

### 2.1 ① 枚举新增消费方全覆盖 + legacy 不误伤 —— **PASS（仍成立）**
- `delivery.method_enum = [release-notes, tag-release, none]`（`level-2.yaml:23`，**含 `none`**）
  ⇒ 既有 `method:none + reason` 语义**不被新枚举误伤**（`none∈enum`）。
- 枚举校验位于 `if task_level(task_dir) is not None:` 分支内（`check-gate.py:2286-2296`），读
  `_delivery_spec`（快照单源）；**legacy（`task_level=None`）走子串路径、完全不进本分支**；
  level-1 快照无 `method_enum` ⇒ **no-op**。⇒ 与首轮一致，**legacy / level-1 零误伤**。
- `LEVELS.yaml` 新增 level-2 的 `sha256` **实测等于文件 LF 归一哈希**
  （`741afaf7…b2b34`）⇒ 冻结登记正确。

### 2.2 ② fail-closed 正确性 + 注入点空/坏命令 —— **PASS（较首轮更强）**
实测（/tmp/opencode 一次性 git 仓 + 注入命令）：

| 场景 | 注入 | rc | 语义 |
|------|------|----|------|
| `--sha ""` | — | **1** | SEC-09 显式拒绝（不回退 HEAD）✓ |
| CI 空数组 | `--ci-cmd "printf '[]'"` | **1** | **SEC-01 fail-closed**（修复前 0）✓ |
| CI `in_progress`（conclusion=null）| 注入 | **1** | fail-closed ✓ |
| CI 全 success | 注入 | **0** | 通过 ✓ |
| CI 坏 JSON | 注入非 JSON | **1** | fail-closed ✓ |
| consistency 非 0 | `--consistency-cmd false` | **1** | fail-closed ✓ |

`_non_success_names` 仍以 `conclusion != "success"` 计入（含 `None`/`missing`/pending）。

### 2.3 ③ TOCTOU / 竞态 —— **PASS（残余窗口 = INFO-4，非误发布）**
「前置顺序 + fail-closed，不等待」取舍仍成立：`Release gate` 步在 `Build assets` 之前，且
`Build assets --expect-sha "$GITHUB_SHA"`（`_check_expect_sha` 剥前缀比对 tag 提交）在
「门查的提交 ≠ tag 提交」时**失败**（净 fail-closed）。`workflow_dispatch` 从**非 tag ref** 分发
时门查的是 ref HEAD CI（INFO-4）——但因 `--expect-sha` 会失败，**不会以错提交建 Release**。

### 2.4 ④ 删除四个 WARNING 块 ⇒ 有无新的静默通过 —— **PASS（无，独立物证）**
- **性质未变**：四块（version 双路径 / CHANGELOG 暂存区 diff / 迁移期 `agate.config.yaml` 提示 /
  tag 存在性）均为 `sys.stderr.write` **不 `return`** 的 WARNING-only；`check-changelog.py`
  在 `pre-commit-gate.py` 必经路径承接，其失败亦为告警。删的是告警不是门。
- **独立物证（R6 双向差分）**：删块后只产生 **1 处 rc 不变（2→2）的行文案差**（P8 收尾提示去掉
  「④ …version 文件路径」），**WARNING 行因 `_error_lines` 过滤而不进比较集** ⇒ 若四块曾属阻断面，
  rc 会变；rc 未变即证其原为 WARNING-only。**「被删块原本兜底的情形是否变成静默通过」= 否**。
- **`git commit --no-verify` 路径**：同时绕过 `check-gate.py P8`（门）与 `check-changelog.py`（告警）
  —**改动前后一致**，非本次新引入；远程 `gate-backstop` 步逐提交回放兜底。

### 2.5 ⑤ `r6-differential-prepare.sh` 健壮性 / 注入 / 误删 —— **NB-8 六负例全闭；新增 N1**
- 负例（实测，全部 rc=2、**无删除**）：`/`、相对、空串、`dst∈src`、`dst==src`、`dst=src 祖先`、
  `dst=allow-prefix 之外`。校验**先于任何删除**；`set -euo pipefail` 在位；写类 git 命令均带 `-C <dst>`。
- **`--after` 改为真实工作树**：`AFTER_ARGS=(--after "$SRC_REAL/agate")`（`:198-201`），使 corpus 只
  承担 before 基线 → **未提交工作树也可能构成 legacy 兼容证据**（修复了首轮 R6「空转」）。
  **实测该口径有效**（§5 R6 复现捕获到未提交改动引起的 2 条差异）。
- **N1（新析出）**：见 §4。

### 2.6 ⑥ 敏感数据 / 凭证 —— **PASS（仍成立）**
`gate` 查 GitHub 仅经 `gh`（`GH_TOKEN` 由 `gh` 凭证通道提供，**代码不读/不打印 env 值**）；API URL
仅含 `owner/name`+`sha`；`_run_cmd` 用 `shlex.split`、**无 `shell=True`** ⇒ 无命令注入面。
`release.yml` 中 `GH_TOKEN` 仅在 `Release gate` 与 `Publish` 两步注入（`release_workflow` 测试已锁
「holders == [gate, publish]」）。

---

## 3. R-C 12 测试文件「是否放宽断言」抽查 —— **未发现弱化**

> 方法：逐文件读 diff + 在 `/tmp/opencode` 副本实跑相关用例；重点关注派发指引点名的
> `test_g8_2/3`、`test_v060_p8_cached`、`test_release_workflow`。**主 Agent 已抽查未见
> skip/xfail/assert True——本轮独立复核同意。**

| # | 文件 | 判定 | 依据 |
|---|------|------|------|
| 1 | `test_check_gate.py::test_g8_2` | **正向重定向（非弱化）** | 旧 `"WARNING" in out` + `"version" in out` 实际被**收尾文案**「…④ …version 文件路径」误命中（**失真**）；新 `rc==2 ∧ "WARNING" not in out ∧ "version" not in out` **锁死新语义**，且该「version」字面已从收尾文案移除。 |
| 2 | `test_check_gate.py::test_g8_3` | **增强** | 除 `WARNING not in out` 外，**新增**实跑新载体 `check-changelog.py T001` 断言 `rc==1`（实测 `check-changelog.py:82` 对未记录 task 确 `exit 1`）⇒ 把「载体迁移强度不降」变成**可判定**。 |
| 3 | `test_check_gate.py::test_g8_7` | **正向重定向** | `"tag v0.2.0 不存在" not in out ∧ WARNING not in out`（tag 检查已删）。 |
| 4 | `test_v060_p8_cached.py` r5_2/r5_3 | **同 1/2** | 回归面同源改写；`r5_1` 保留 `rc==2 ∧ 脚本化检查通过`；r5_3 同样加 `check-changelog==1` **强度补充**。 |
| 5 | `test_gate_layer.py::test_bdd_21_missing_declaration…` | **有意收敛（合 BDD-19）** | 旧断言要求「声明缺失 → 迁移期 WARNING」；BDD-19 明确要求「**不再出现**基于已移除 version/tag 痕迹的悬空提示」。新断言 `rc==2 ∧ 无 preset/agate.config 提示` **正是 BDD-19 的正向锁**——非躲 BDD。 |
| 6 | `test_release_workflow.py` | **随新契约重定向** | `on`/`permissions`/GH_TOKEN holders 三处断言随 BDD-8/9 更新为新**精确**集合（`{"push","workflow_dispatch"}`、`{contents,checks}`、`[gate,publish]`），未见放宽（仍 `==` 精确比对 + 增 `len(gate_steps)==1`）。 |
| 7 | `test_tag0050_write_tools.py` | **修复真缺陷（增强）** | 夹具补 `copytree`（含 level-2.yaml），使断言 `"writer: system" in output` **真正可判**（此前 extends 链断⇒快照 {}⇒退化为「非法 key」）。 |
| 8 | `test_tag0051_obligations_sync.py` | **修复真缺陷（增强）** | `_obligations()` 改取 `data["obligations"]`（原恒 `[]`＝真空绿）；现返回 14 条真实断言。 |
| 9 | `test_release_gate.py` | **修常量（非断言）** | `H.GENESIS_HASH`→`H5.GENESIS_HASH`（前者不存在，原 `AttributeError`）；未改断言。 |
| 10–13 | 4 个 integration/`obligations_enforcement` | **夹具随当前等级 =2 对齐** | ledger `contract_level` 1→2（`pre-commit-gate.py` §2.3 规则 2 要求新任务等级==当前等级）；无断言放宽，未新增 skip/xfail。 |

> **唯一风格性提示（N3）**：`assert "WARNING" not in result.output` 是对**全部** WARNING 的全局否定，
> 语义上只欲锁「无 version/tag 告警」。未来若 P8 gate 新增**无关** WARNING，该断言会误红（脆性）。
> 非正确性问题，可留待后续用「主题词」收窄（如 `"version" not in` 已足够）。

---

## 4. 本轮新析出

### [N1]（中，非 CRITICAL）`r6-differential-prepare.sh` 的 `cp -a <src> <dst>` 在本真实仓库上**失败** ⇒ 声明的 `P5_r6` gate 命令在本环境**跑不起来**
- **实测**：`bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus`
  ⇒ `PREPARE_RC=1`，批量 `cp: 无法创建普通文件 '<dst>/.worktrees/blog-post11/site/node_modules/…'：没有那个文件或目录`
  （`.worktrees/` 是本机 gitignore 的 **345M** worktree，含 `node_modules` 软链/深路径）。
- **定位**：`set -euo pipefail` 下 `cp -a`（`:192`）非 0 即中止，**未到** `exec r6-differential.sh`。
- **对照实验（确认根因）**：在**剔除了 `.worktrees/`** 的副本上跑同一 wrapper ⇒
  **`WRAPPER_RC=0`，`legacy 任务 39 个，差异 2 条，未匹配 0 条`**（两平台一致）⇒ **wrapper 逻辑本身正确**，
  失败**仅**源于 `cp -a` 连同 gitignore 的重量级目录一起拷贝。
- **影响**：① 声明的 `P5_r6` gate 命令（`P2-design.md` 的 `tests_filter`）在本开发环境**不能原样执行**；
  ② 主 Agent 报告的 R6 数字（39/2/0）**并非由该 wrapper 产出**——本轮已用底层脚本**独立复现同数字**（§5），
  故 BDD-20 证据**有效**，但 wrapper 本身**未被真实环境跑通**（未获证据）。
- **方向（不代改）**：wrapper 建 corpus 时**只收 versioned/必要面**——如以 `git -C <src> ls-files -z` + archive
  构建，或 `tar --exclude=./.worktrees`（或排除一切 `git check-ignore` 命中项）替代裸 `cp -a`；并在 `--src`
  含被忽略重量级目录时给出**可操作提示**而非 `cp` 原始报错刷屏。**注意**：corpus 仍须保留 `.git`（差分要
  `git archive <before>`）。

### [N2]（已闭合 ✓ —— 由并发 R-E retry 2 收口，本轮核验）
`gate_p8` 删四块后的**文档传播残留**——与首轮同类（成因：以单一字面 `grep` 反推「不改什么」面）。
R-E 已按 §4 清单**逐项收敛**（**实测 diff**）：
- `agate/assets/execution-roles/implementer.md:45/49/90-101`：`P8` 输出/质量门槛/多包节改为
  「`bump_type` 意图 + CHANGELOG `[Unreleased]` 含 task_id + 交付检查（逐包 exit 0）」，节标题改
  「P8 多包**交付收尾**」；`:101` 与 canonical 一致（**不再自相矛盾**）。
- `agate/phase-cards/P5-verification.md:147`：改「P8 **交付收尾后**重跑 P5 gate」。
- `agate/phase-cards/README.md:18` / `agate/assets/templates/task-files.md:38` /
  `agate/assets/templates/active-tasks-template.md:54`：P8 行改「`bump_type` 意图 / CHANGELOG `[Unreleased]`」。
- `agate/scripts/check-gate.py:25`（模块 docstring）：改「结构化 delivery（method 枚举校验）+ roadmap RM 反查」。
- `agate/scripts/README.md`：`agate-release.py` 索引行**补列 `gate` 子命令**；
  `agate/tests/README.md`：**补登记** `agate-release.py gate → unit/test_release_gate.py`。
- **核验（post-R-E 定稿树）**：以上**全为文档/注释层**，无行为改动；`check-protocol-consistency.py
  --strict-errors-only` **rc 0 / 0 ERROR**（含对 `scripts/README.md` 的 CHECK 10 扫描面）、
  `check-structure-consistency.py` rc 0（S-1/S-2 锚点未破）、定向 doc/SG 用例 **125 passed**（§5）。
  ⇒ **闭合**，不再列为扣留项。
- ⚠️ **口径护栏（保留提醒）**：`state-machine.md:167/168/330/404/406`、`dispatch-protocol.md:881` 等
  **显式否定句**（「**不含** version bump / tag」）**属 BDD-1 允许的收敛表述**，**不应**当作残留再改
  （避免把「去 tag」的证据反删掉）；BDD-1 的判据是 **tag 作为 P8 条件/动作零命中**，非「tag 字面零出现」。

### [N3]（低）断言风格：全局 `"WARNING" not in output`（见 §3 注），非阻塞。

---

## 5. 复核证据（可直接重跑；写副作用一律在 `/tmp/opencode` 一次性副本）

| 结论 | 命令/位置 | 观测 |
|------|-----------|------|
| R-C 测试未弱化 | `pytest <test_check_gate / test_v060_p8_cached / test_release_gate / test_release_workflow / test_gate_layer / test_tag0050_* / test_tag0051_obligations_sync>`（副本） | 仅 2 条失败**且均为副本缺 `.git` 所致**（`git log` 走真仓）；补齐后 26 passed；其余 312 passed |
| R6 双向差分（BDD-20） | `bash r6-differential.sh --corpus <clone@HEAD> --after <真仓>/agate`（实跑） | **`legacy 任务 39 个，差异 2 条，未匹配 0 条`，rc=0**；两差异均 `check-gate:P8 … rc 2->2 added=1 removed=1`、均 `[ALLOWED]`（= P8 收尾文案去 version，另见 D13） |
| R6 wrapper（应测的 gate 命令） | `r6-differential-prepare.sh --src . --dst /tmp/opencode/…` | **rc=1**（`.worktrees` cp 失败）＝ **N1**；剔除 `.worktrees` 后 rc=0、39/2/0（**确认根因**） |
| wrapper 负例（NB-8） | `--dst` ∈ {`/`,`rel`,`""`,src 内,==src,src 祖先,allow 外} | 全 **rc=2**、**无删除**；src/旁路目录**存活** |
| `gate` fail-closed | `agate-release.py gate --sha … --ci-cmd … --consistency-cmd …` | `sha=""`→1 / `[]`→**1** / `in_progress`→1 / success→0 / 坏 JSON→1 / consistency false→1 |
| 一致性 0 ERROR（含 R-A..R-D） | `check-protocol-consistency.py --strict-errors-only`（完整副本） | **rc=0**，`仅有 432 个 WARNING，无 ERROR` |
| 结构一致性 | `check-structure-consistency.py`（副本） | rc=0（S6/S0 OK） |
| **post-R-E 复验**（文档收敛后） | 同上一致性 + 结构 + `pytest test_{mvwu_protocol_docs,env_adapt_docs,check_structure_consistency,docs_assertions,tag0051_docs_consistency} + integration/test_protocol_alignment_review`（副本） | 一致性 **rc=0 / 0 ERROR**（含 `scripts/README.md` 的 CHECK 10 扫描面）；结构 rc=0；定向用例 **125 passed** |
| level-2 哈希 | `sha256(LF(level-2.yaml))` | `741afaf7…b2b34` == `LEVELS.yaml` 登记值 |
| 真仓未污染 | 全程跑前/跑后 `git status --porcelain` | 新增项均为**主 Agent 并发产物**（`P4-dispatch-context-implementer-R-E.md` + R-E 改动的被评审文件），**均为评审对象本身、非本次评审写入**；其余 ` M`/`??` 与开跑前一致 |

---

## 6. 处置建议（给主 Agent）

- **可推进**：0 CRITICAL ⇒ `status: approved`；P4 review 不构成 gate 阻挡。
- **快照已定稿**：并发 R-E（retry 2）**已落地**，本文件已就 post-R-E 定稿树（pin `9843650…d2579`）
  完成复验（一致性 0 ERROR + 结构 rc 0 + 定向 125 passed）；R-E 仅动文档/注释层，**未触碰语义判据**。
  ⇒ 除下述 N1 外，**本 `approved` 已反映将提交的最终树**。
- **N1**（中，建议 P5 前或另立 DEBT）：修 wrapper 建 corpus 的方式以容忍 `.worktrees`（或任何被忽略重量级目录）；
  否则 `P5_r6` gate 命令在本机**每次都会红**（当前证据已用底层脚本复现，不受影响）。
- **扣留项（非阻塞）**：INFO-3 / INFO-4 / INFO-6 仍开——均为「默认用法之外的健壮性」，建议登记 DEBT 一行并可留待后续版本。
- **口径护栏**：见 §4 N2 末的「显式否定句不应再删」提醒（防止把收敛证据反删）。
