---
phase: P2
task_id: TAG0051
parent: P2-design.md
trace_id: TAG0051-P2-20261011
type: review
agent: plan-eng-review
status: approved
created: 2026-10-11
---
# P2 工程评审（plan-eng-review，retry 1 复评）— TAG0051 任务与发布解耦

> **评审对象**：`agate-workspace/tasks/TAG0051-release-decoupling/P2-design.md`（438 行 / `candidate_count: 3` / **8 批** / `ui_affected: false`）
> **评审角色**：`plan-eng-review`（C8：`backend`→plan-eng-review + `high`→plan-eng-review，去重为**单评审**；`security`→`cso` 属 P4 后 ⇒ 直接产出本文件，无需组长汇总）
> **本轮性质**：**复评（retry 1）**——首轮判 `rejected`（1 BLOCKER = B1）。本轮逐条核验 B1 是否真闭合（**要数字，不采信陈述**）+ NB-1..5 落实 + 有无新破坏。
> **评审方式**：**只读核验**（未编辑被评审文件；所有实测在 `/tmp/opencode` **一次性副本**上完成，"创建→操作→清理"同一次 bash 调用；跑前/跑后核验真实仓库 `git status --porcelain` 哈希一致；只读 `grep`/`read` 直读真仓）
> **协议版本**：`AGATE_ROOT=/home/kity/.agate/v0.81.0/agate`；本仓无 `.agate-version`；分支 `task/TAG0051-release-decoupling`

---

## 0. 结论

**`approved`** —— **0 个 BLOCKER**。

首轮唯一 BLOCKER（B1：`obligations-sync` 批会击穿自声明的 gate `P5_obligations`，且 OBL-P8-05/08 语句漂移无机械守护）**已真闭合**：① 本评审**独立复现**了修复方案的机械结果（`M 类占比: 56/121` + exit 0 + `test_obligation_enforced[OBL-P8-04]` 通过 + 十四条 statement 零残留）；② 首轮指出的「删除条目**或**其挂靠测试」**未定二选一**已**定死**（定死为「不删任何条目、就地重挂」）；③ 首轮三条失败路径（删条目 / `M→C` / 移出占比）**在本方案下均未被采用**。NB-1..NB-5 **五项全部落实**（含 `DEBT0069` 实际落盘）。**无新破坏**：首轮 §7 六条锁定决策全部保留、`candidate_count` 一致、`gate_commands` 逐 key 合法且无 `&&`、`P5_r6` 已改为调 wrapper、`agate/` 与 `docs/` **零改动**（无 M 改判 C/R、无删测试让路）。

> 口径说明：依角色文件与派发指引「B1 闭合 + NB 落实 + 无新破坏 ⇒ approved（非阻塞项列入正文，**不因非阻塞项打回**）」。本轮新析出的 4 条非阻塞项见 §3，**不**构成打回理由。

---

## 1. 定点核验（本轮核心，逐条给数字）

### 1.1 B1 是否真闭合 —— **PASS（独立复现）**

**复现方法**（`/tmp/opencode/tag0051-b1` 一次性副本，真仓跑前/跑后 `git status --porcelain` 哈希一致；副本已删）：`cp -a agate/ + pyproject.toml`，按修复后方案**真改** `obligations.yaml`（04 就地重挂 + 05/08/13 statement 改述），再以 `AGATE_ROOT=<副本>/agate` 跑 `check-obligations.py`。

| 核验点 | 独立观测 | 结论 |
|--------|---------|------|
| M 计数不变 | `M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）`；`归宿分布: M=56 C=35 R=30`；`CHECK-OBLIGATIONS: OK`；**RC=0** | **PASS** |
| 三条失败路径未被采用 | 设计 §1.1.1 明确「**不删任何条目、不改判、不移出占比**」；M6 行同口径；复现输出 M 仍 56、无 `baseline.reset` 生效（有效基线仍 `56/121`） | **PASS** |
| `OBL-P8-04` 重挂落点可达 | `enforced_at` 改为 `{file: agate/scripts/check-gate.py, function: gate_p8}` 后 `check-obligations.py` `_check_enforced_at` **未报错** ⇒ `gate_p8` 确在 `_reachable_set` 必经路径上（与 OBL-P8-01/02/03 同落点） | **PASS** |
| `M_IDS` 零改动论断 | `M_IDS`（`test_tag0050_obligations_enforcement.py:61` 附近）**保持含 `"OBL-P8-04"`**；重挂后该条仍为 M（`disposition: M` 未动）⇒ 无需增删 | **PASS** |
| `test_obligation_enforced[OBL-P8-04]` 仍能通过 | 副本实跑：**`1 passed`**（块内确有 `enforced_at`；`_check_test_node` 亦通过——测试文件既含该 id 又含节点函数，**无需改文件**） | **PASS** |
| 「删条目**或**其挂靠测试」是否已定死（实现就绪度） | M6 现写「**十四条逐条过一遍**…**OBL-P8-04 就地重挂**…**不删任何条目**」；M7 现写「`M_IDS` **保持含** `OBL-P8-04`…故**零 `M_IDS` 改动**」⇒ 二选一**已定死为"不删"**，implementer 可自主实现 | **PASS** |

### 1.2 OBL-P8-05/08/13 改述 + 新增 BDD-21 机械断言 —— **PASS（附 NB-6）**

**等价探针**（判据本身可判定性验证；该断言 P4 才落盘，故按描述在副本上实现等价探针）：遍历 `OBL-P8-*` 的 statement，断言不含 `新版本号`/`version 文件变更`/`双路径`/`bump 后`/`git tag`，并断言 `OBL-P8-04.disposition == "M"` 且 statement 含 `method_enum`。

| 核验点 | 独立观测 | 结论 |
|--------|---------|------|
| 十四条 statement 无残留 | `P8_count: 14`、**`violations: []`**（改述 05/08/13 + 重挂 04 后） | **PASS** |
| 断言的判别力（可判定性） | 修前 4 条命中（`obligations.yaml:746/755/780/815`），修后 0 命中 ⇒ 判据**确实可判定**、非真空 | **PASS** |
| 是否误伤其余 10 条 | 逐一核：其余 10 条（01/02/03/06/07/09/10/11/12/14）statement **均不含**上述五个词 ⇒ **零误伤**（另外 `agate/tests/`、`agate/rules/` 全域 grep 这四词仅命中这 4 条 statement 本身） | **PASS** |
| 词表可否被绕过 | **可绕过**（词表为 5 个精确 token：`版本号` 单独、`打 tag`/`创建 tag`/`tag 存在性`、`bump` 单独 均不被拦）⇒ 见 **NB-6**（**非阻塞**） | 观察项 |

### 1.3 NB-1..NB-5 采纳结果是否落实（只核落实，不判该不该做）

| 项 | 核验点 | 独立观测 | 结论 |
|----|--------|---------|------|
| **NB-1** | 按 (b) 改述「无值消费方」+ 引用 `DEBT0069` + M11 **不**消费该键 | §1.2（`release.preset` 行）+ 决策 6 已改为「**无任何值消费方**…**不是**『删了消费点才变死键』…经主 Agent 裁定保留为信息性声明、登记 **DEBT0069**；**M11 发布门不消费该键**」；`agate-workspace/debt/tech-debt.md` **已实际追加 `## DEBT0069`**（38 行，含 4 条 evidence + 明确「TAG0051 采用 (b)」）；设计全篇**无**任何「M11 读 preset」表述 | **PASS** |
| **NB-2** | 定死 `check-gate.py:2339-2356` 删/改（定**删**）；「判据强度不降反升」论断是否成立；`(rc, ERROR 集合)` 不变 | M1 已**定死为删**（决策 5 同口径）；载体 `check-changelog.py` 实测确在 **`pre-commit-gate.py:1086`** 被调用（`if phase == "P8" and _run_script_rc("check-changelog.py",[task_id]) != 0:` → **仅 `stderr` 警告，不 return**）；被删块同为 WARNING-only（`check-gate.py:2317-2389` 四块**均不 return**）⇒ `(rc, ERROR 集合)` **不变** | **PASS**（附 NB-7） |
| **NB-3** | ① 登记面零触发（**实测**，非推理）；② wrapper 对真仓无副作用；③ 批数 7→8 且 `parallel_limit` 同步 8 | ① **实测**（`/tmp/opencode/tag0051-nb3` 副本，同一次调用内建→跑→删）：基线 `check-protocol-consistency.py` **RC=0**、CHECK 9 **PASS**；加入探针 `docs/design-notes/r6-differential-prepare.sh` 后**再跑 → CHECK9/CHECK10 行 `NO_DIFF`** ⇒ 零触发；**对照实验**：把探针放 `agate/scripts/check-nb3probe.py` → CHECK 9 显式 WARN 点名该文件 ⇒ 探针法**非真空**（判据确有灵敏度）。代码面复核：`uncovered_gate_scripts()`（`:918-931`）扫描面 = `agate/scripts/check-*.py` + `pre-commit-gate.{sh,py}`；`CHECK 10` 扫描面 = `PROTOCOL_FILES` + 协议目录 rglob，**明示不含 `docs/` 与 `agate-workspace/`**（`:968-969`）；`SG.6` 消费同一 `uncovered_gate_scripts()` ⇒ 三处均不在面内。② wrapper 为 P4 待写件（当前不存在）；设计的序列（`rm -rf <dst>` → `cp -a <src> <dst>` → `git -C <dst> checkout/clean` → `exec … --corpus <dst>`）中**真仓仅作 `cp -a` 只读源**，写类 `git` 命令**均加 `-C <dst>`** ⇒ 无真仓副作用（附 NB-8 健壮性要求）。③ frontmatter 实测 `mode=static-batch`、`parallel_limit=8`、**批数=8**、`8 ≤ 8` ⇒ P2 gate `len(batches) ≤ limit` 通过 | **PASS** |
| **NB-4** | §1.2 显式点名 `WORKFLOW.md`/`orchestrator-template.md`/`assets/templates/*` 为 Not-Modify + 理由 | §1.2 末行已显式点名，理由 = 「实测三者 `git tag` **零命中** ⇒ 不入改面正确；**显式点名**为范围禁区——『不改什么』是 P4 范围边界的唯一依据」 | **PASS** |
| **NB-5** | 显式框定跨项目破坏半径；两轴区分是否准确 | R11 已新增，明确受众 = 「**所有用 agate 的项目**（不只本仓）及在途非 legacy 任务」，并区分两轴：**语义**=「P8 不再要求 version/tag」是意图内的**向前变更**（非破坏）；**机械**=二者皆 **WARNING** ⇒ `(rc, ERROR 集合)` 不变 ⇒ 对 legacy/其它项目**非破坏**。两轴划分与 `check-gate.py:2317-2389` 实测（均不 return）一致 | **PASS** |

### 1.4 无新破坏（回归核验）

| 核验点 | 独立观测 | 结论 |
|--------|---------|------|
| 首轮 §7 六条锁定决策是否保留 | ① 候选 A（`agate-release.py` 新增 `gate`）——§2/决策 1 保留；② `workflow_dispatch` 唯一个人授权入口、`release.yml` 只调用不内联——决策 2 + M12 保留；③ 门判据 = required **check-runs** + required **6** 项——决策 3 + §8 note 保留；④ `level-2.yaml`（`extends: 1`）+ **重述完整 delivery 节**——决策 4/M8 保留；⑤ 去 tag/version 且 CHANGELOG 保留——决策 5 保留；⑥ B1 修订方向——§1.1.1/M6/M7 落实（见 §1.1）。**未见修复轮顺手改动** | **PASS** |
| `candidate_count` 与正文一致 | `candidate_count: 3`；正文 `### 候选 A/B/C` 三个标题（实测 `['A','B','C']`）；`ui_affected: false` 未变 | **PASS** |
| `gate_commands` 逐 key 合法 + 无 `&&` | 逐 key 经 `agate_common.is_legal_gate_key()`：`P3/P5/P5_consistency/P5_count/P5_ruff/P5_obligations/P5_sg6/P5_r6` 全 **legal=True**，`P5_timeout_seconds/P5_r6_timeout_seconds` 亦 True（meta 键）；块内 **`&&` 不存在**（实测 `contains && : False`） | **PASS** |
| `P5_r6` 是否已改为调 wrapper | `P5_r6: "bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus"`（§5 说明与 §4 批 `r6-harness` 同口径）⇒ 与 §5 一致 | **PASS** |
| 不得把 M 类改判 C/R 绕棘轮 | 复现输出 `M=56 C=35 R=30`（与现仓 `counts(in-ratio): {'R':30,'C':35,'M':56}` **完全相同**）；`OBL-P8-*` 十四条 disposition 零变化 | **PASS** |
| 不得删既有测试让路 | `git status --porcelain agate/ docs/` = **空**（`agate/` 与 `docs/` 零改动）⇒ 无测试被删/改 | **PASS** |
| 真仓未被污染 | 两次副本实验跑前/跑后 `git status --porcelain \| sha256sum` 均一致（`REAL_REPO_STATUS_UNCHANGED_OK`） | **PASS** |

---

## 2. 架构问题（阻塞级）

**无。** 首轮 B1 已闭合（§1.1）；本轮未发现新的阻塞级问题。

---

## 3. 架构问题（非阻塞，列入正文，**不打回**）

- **NB-6（由 §1.2 析出）BDD-21 机械断言是「黑名单关键词」，可被绕过。** 词表仅 5 个精确 token（`新版本号`/`version 文件变更`/`双路径`/`bump 后`/`git tag`），因此 `「CHANGELOG 写入版本号」`（无「新」）、`「打 tag 前置校验」`/`「tag 存在性」`、`「完成 bump 后」`以外的 `「执行 bump」` 等 version/tag 期表述**均可绕过**。**不判阻塞**（首轮评审自身的建议即「补一条关键词断言」，且 BDD-21 仍由 `P5_obligations` 的 anchor 非空 + M 占比棘轮 + P6 语义判决共同兜底）。**P4 建议**：① 词表补 `版本号`/`tag`/`bump` 等更宽的根词（先全量扫 `OBL-P8-*` 确认零误伤再启用）；或 ② 把断言从「statement 不含 X」升级为「statement 与 anchor 节文本的关键词交集非空」，使其随锚点正文变化而敏感。
- **NB-7（由 NB-2 析出）载体路径表述可更精确。** 实测 `check-changelog.py` **只**在 `pre-commit-gate.py:1086`（**pre-commit hook 阶段**）被调用，**`check-gate.py` 内无任何 `check-changelog` 调用**（实测 `grep -n "check-changelog" agate/scripts/check-gate.py` = 无命中）。故删 `gate_p8:2339-2356` 后，**直接跑 `check-gate.py P8` 不再有任何 CHANGELOG 告警**（此前是弱告警）；替代判据（`[Unreleased]` 含 task_id）**强于**「文件有变更」且同在必经的 pre-commit 路径上，`(rc, ERROR 集合)` 不变——设计结论成立，仅建议 §5/§9 明文点出「载体在 pre-commit 阶段、不再在 `check-gate.py P8` 内」，避免 P4 误以为 `gate_p8` 会调它。
- **NB-8（由 NB-3 析出）wrapper 健壮性约束须写进 P4 验收。** wrapper 是 P4 待写件，其序列含 `rm -rf <dst>` / `git -C <dst> clean -fdx`。若 `--dst` 为空串，`git -C ""` 的失败语义存在把命令落回 cwd 的风险面（真仓！）。**P4 必须**：① `set -euo pipefail`；② 前置校验 `--dst` **非空且为绝对路径**、且**不位于 `--src` 之内**（否则 `rm -rf` 会删源）；③ 执行前 `echo` 出解析后的 `<src>/<dst>` 供审计。
- **NB-9（提示项）批级 smoke 与 fixture。** `r6-harness` 批的 `tests_filter` 是 bash 命令（"冒烟：不得 `corpus 不存在`"），非 pytest 节点——不产生批级 pytest 证据（P2 卡允许，缺省不拦截），P4 需自觉跑一次该命令留证。另 §9.1 把 level-2 黄金 fixture 的 CI 覆盖留待 P3 决定，**非阻塞**（P3 面）。

---

## 4. 测试缺口

1. **BDD-21 语义面仍非全机械**：见 NB-6——黑名单可绕过；剩余风险由 `P5_obligations` + P6 语义判决兜底，**建议 P4 按 NB-6 加固**。
2. **`delivery.method_enum` 的 level-2 fixture**：设计 §9.1 已给出**来源与构造方式**（复用 `fixtures/task-data/level-*` 账本形态，以 `task_created.contract_level: 2` 定格 `task_level`）——首轮「测试缺口 #2」**已补**；其 CI 覆盖（`test_tag0050_fitness.py` 是否遍历 `LEVELS.yaml`）设计显式留给 P3，**可接受**。
3. **`P5_r6` 的 corpus 前置**：首轮「测试缺口 #3（无强制力）」**已补**——落成 wrapper（NB-3），不再依赖人记；wrapper 自身无 pytest 守护（属性所在，P4 有 NB-8 约束）。

---

## 5. 锁定决策（本次复评确认下来的技术方向）

1. **发布门落点 = 候选 A**（扩展现有 `agate-release.py` 新增 `gate` 子命令）——**保持锁定**。
2. **`workflow_dispatch` = 唯一个人授权入口**；`release.yml` 只**调用** `agate-release.py gate` 作 tag-push 路径 fail-closed backstop，**不内联逻辑**——**保持锁定**。
3. **发布门判据 = required 6 项 check-runs 逐项 `conclusion == success`（查 check-runs，不查 combined status）+ CHECK 7/13 0 ERROR + RM done**（判据单源 = `check-gate.py P8`）——**保持锁定**。
4. **`delivery.method` 枚举落 `level-2.yaml`（`extends: 1`）+ 重述完整 `delivery` 节**；不动冻结的 `level-1.yaml`——**保持锁定**。
5. **P8 去 tag/version（删除项皆 WARNING，`(rc,ERROR)` 不变）+ CHANGELOG 保留（载体 `check-changelog.py`，`:2339-2356` 定死为删）**——**本轮新增锁定**。
6. **`obligations-sync` 批的定死形态**：`OBL-P8-04` **就地重挂**为 `delivery.method_enum` 枚举校验（`disposition` 保持 **M**、`enforced_at → gate_p8`、复用既有 test 节点）；`OBL-P8-05/08/13` **仅 statement 改述**；其余 10 条保留；**不删条目、不改判、不移出占比、不写 `baseline.reset`** ⇒ M 计数 **56/121** 不变——**本轮独立复现确认，锁定**。
7. **`release.preset` = 信息性声明、不驱动逻辑**（`DEBT0069` 已登记；M11 不消费该键）——**本轮新增锁定**。
8. **R6 corpus 前置 = wrapper `docs/design-notes/r6-differential-prepare.sh`**（落 `docs/design-notes/` ⇒ CHECK 9 / SG.6 / CHECK 10 **三处零触发**，本轮实测确认）+ 批 `r6-harness`（批数 **8**、`parallel_limit` **8**）——**本轮新增锁定**（P4 须落实 NB-8 健壮性约束）。

---

## 6. 复核证据（可直接重跑；本轮均只读 / 一次性副本）

| 结论 | 命令 / 位置 | 本轮观测 |
|------|------------|----------|
| **B1 闭合（M 计数）** | `/tmp/opencode/tag0051-b1` 副本按修复方案改 `obligations.yaml` → `AGATE_ROOT=<副本>/agate check-obligations.py` | `M 类占比: 56/121 = 0.4628（基线 56/121）`；`CHECK-OBLIGATIONS: OK`；**RC=0** |
| **B1 闭合（测试节点）** | 同副本 `pytest …::test_obligation_enforced[OBL-P8-04]` | **1 passed** |
| **十四条 statement 零残留** | 副本等价探针（遍历 `OBL-P8-*`） | `P8_count: 14`、`violations: []`；其余 10 条零误伤 |
| 现仓 disposition 与 M 计数 | `yaml.safe_load(obligations.yaml)` 计数 | `{'R':30,'C':35,'M':56}`、total **121**、M ids **56** |
| 禁止词现状（改前） | `grep -n "新版本号\|version 文件变更\|双路径\|bump 后\|git tag" obligations.yaml` | 4 命中 = `:746`(04) / `:755`(05) / `:780`(08) / `:815`(13)——**即被处置的 4 条** |
| **NB-3 零触发（实测）** | 副本：基线跑 consistency → 加 `docs/design-notes/*.sh` 探针 → 再跑 | RC 0→0；CHECK9/CHECK10 行 **NO_DIFF**；**对照** `agate/scripts/check-nb3probe.py` → CHECK 9 WARN 点名 ⇒ 探针非真空 |
| `uncovered_gate_scripts()` 扫描面 | `check-protocol-consistency.py:918-931` | `agate/scripts/check-*.py` + `pre-commit-gate.{sh,py}` |
| CHECK 10 扫描面 | `check-protocol-consistency.py:968-969` | `PROTOCOL_FILES`+协议目录；**明示不含 `docs/`、`agate-workspace/`** |
| NB-2 载体在必经路径 | `grep -n "check-changelog.py" agate/scripts/pre-commit-gate.py` | **:1086**（`phase == "P8"` → 仅 stderr 警告，不 return） |
| NB-2 载体**不在** `check-gate.py` | `grep -n "check-changelog" agate/scripts/check-gate.py` | **无命中** ⇒ 见 NB-7 |
| 删除项皆 WARNING | `check-gate.py:2317-2389` | version/CHANGELOG/迁移期/tag 四块**均不 return** |
| `gate_commands` 合法性 | `is_legal_gate_key()` 逐 key + 块内 `&&` 检索 | 全 **legal=True**；`&&` = False |
| `dispatch_plan` 合法性 | frontmatter `yaml.safe_load` | `mode=static-batch`、`parallel_limit=8`、**8 批**、`8 ≤ 8` |
| NB-1 落盘 | `git diff agate-workspace/debt/tech-debt.md` | **新增 `## DEBT0069`**（38 行，evidence 4 条） |
| 无删测试让路 | `git status --porcelain agate/ docs/` | **空** |
| 真仓未污染 | 两次副本实验跑前/跑后 `git status --porcelain \| sha256sum` | **一致**（`REAL_REPO_STATUS_UNCHANGED_OK`） |

> `[PROD_NOT_TOUCHED]` 本评审只读：未 push / PR / merge / tag / Release / dispatch；未编辑任何被评审文件；未对真实仓库运行任何写类工具；全部实测在 `/tmp/opencode` 一次性副本内完成并已清理。
