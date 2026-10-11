---
phase: P7
task_id: TAG0051
type: consistency
parent: P2-design.md
trace_id: TAG0051-P7-20261011
status: approved
created: 2026-10-11
agent: consistency-reviewer
blocker_count: 0
deviation_count: 5
deviation_critical_count: 0
design_gap_count: 0
design_gap_reviewed_count: 0
code_map_new_files_count: 4
code_map_reviewed_count: 4
prod_touched: false
---

# TAG0051 P7 一致性检查 — 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

> **角色**：consistency-reviewer（P7 跨文件一致性交叉检查），fresh context。
> **对象**：`P0-brief.md` / `P1-requirements.md` / `P2-design.md` / `P3-test-cases.md` / `P4-implementation.md` /
> `P5-test-results/` / `P6-acceptance.md` / `P6.5-judge-verdict.md`（跨文件全文比对，不做「看起来对」的跳过）。
> **分支/提交链**：`task/TAG0051-release-decoupling`，起点 `581369fc`（origin/main）；P4 `9771e76a` /
> P5 `c5bda4df` / P6 `03dcc1f7` / P6.5 `c810c19a`。
> **口径**：本任务为**首个非 legacy 任务**（账本首行 `task_created`，`contract_level: 1`）⇒ P7 gate 走
> `check-gate.py::_gate_p7_structured`（成对声明聚合判据：`design_gaps` / `design_gap_reviews` /
> `scope_plus` / `scope_resolved` / `code_map` / `code_map_reviewed` / `need_confirm` / `findings`）。
> **状态标记**：`[PROD_NOT_TOUCHED]`——本轮全程**只读**（`git log`/`git diff`/`grep`/`read` 只读命令 + 只写本文件），
> 未 `git add/commit/restore/reset/clean/stash`，未触发 `workflow_dispatch`/tag/Release，未运行任何写类工具对真实仓库。

## 结论摘要

| 项 | 结果 |
|---|---|
| BLOCKER | **0** |
| DEVIATION-CRITICAL | **0** |
| DESIGN_GAP 配对 | **0/0（无 DESIGN_GAP 需配对，见 §1）** |
| SCOPE+ 闭环 | **空闭环**（P1 无 `scope_plus` ⇒ 无需 `scope_resolved`，见 §2） |
| 未决项清零 | **通过**（P1 无行首 NEED_CONFIRM 等，见 §4） |
| 跨文件一致性 | **通过**（`P2§packages` / `P1§BDD` / `P6§results` / `P4§impl-path`，见 §3） |
| CODE-MAP | **4/4 配对**（均 `[CODE_MAP_EXEMPT]`，判定成立，见 §5） |
| 架构决策落点 | **无待办**（`decisions/` 不存在；ADR-016 落协议层 `agate/adr.md`，见 §6） |
| 已知偏离（deviation） | **5 条全部 accepted**（D1–D5，见 §7） |
| **总判定** | **approved（无 BLOCKER / 无 DEVIATION-CRITICAL）** |

---

## 1. DESIGN_GAP 逐条配对（复核：0 条，**无 DESIGN_GAP 需配对**）

> **主 Agent 实测**：`P4-implementation.md` **未声明任何** `DESIGN_GAP`。**本轮独立复核结论 = 属实**。
> 复核命令与证据：`grep -nE 'DESIGN_GAP' P4-implementation.md` → **零命中**；P4 全文亦无小写 `design_gap`
> 关键词（`grep -in 'design_gap'` → 零命中，故 gate 的「P4 有偏差关键词但计数 0」WARNING 亦不触发）。
> P4 §10「设计偏差 / 已知偏离」标题下的条目**不含** `[DESIGN_GAP:]` 行首标记，其性质为**已知偏离（deviation）**，
> 按 §7 逐条处置，**不**计入 DESIGN_GAP 配对面。

- **结论**：`design_gap_count: 0` / `design_gap_reviewed_count: 0`。**本任务无 `[DESIGN_GAP:]` 声明需配对**，
  故**无** `[DESIGN_GAP_REVIEWED:]` 标记可配（0 对 0，成对声明面 `design_gaps` 与 `design_gap_reviews` 两侧同为空集，
  gate 的 `dg_ids == set(rev_gaps)` 与 `p4_prose(0) ≤ len(rev_gaps)(0)` 均成立）。

---

## 2. SCOPE+ 闭环（复核：无 SCOPE+ 增补 / 无需闭环）

- `P1-requirements.md` frontmatter **无** `scope_plus` 键（`grep -n 'scope_plus'` → 无命中）；
  全文亦**无**行首 `[SCOPE+]` 声明（`grep -nE '^\s*>?\s*-?\s*\[SCOPE\+'` → 无命中；
  §2 仅出现「后续阶段新发现的隐含需求以 `[SCOPE+ from Pn]` 回写」的**机制说明**，非声明）。
- 上游其他声明文件的 frontmatter 亦无 `scope_plus`（`grep '^scope_plus:' **/*.md` → 无命中）。
- ⇒ **显式结论：本任务无 SCOPE+ 增补，无需 `[SCOPE_RESOLVED]` 闭环**（空闭环：`scope_plus ⊆ scope_resolved`
  两侧均空集，成立）。P2 §10「[SCOPE+] 与登记缺口」仅登记**工具缺口**（非需求增补），不构成 SCOPE+。

---

## 3. 跨文件一致性（逐项引源文件节名）

### 3.1 `P2§packages`（9 个）↔ 交付范围（按新语义「READY，不落 tag/Release」核）

- `P2-design.md` frontmatter `packages`（**9 项**：`agate-cards` / `agate-state-machine` / `agate-rules` /
  `agate-scripts` / `agate-roles` / `agate-dispatch` / `agate-config` / `agate-docs` / `ci-workflows`）
  与 `P1-requirements.md` frontmatter `packages` **逐字一致**（各 9 项，同序）。
- **新语义口径**：本任务**终态 = READY**（P0-brief `goal` / P1 §1 / P2 §0），交付范围 = 这 9 个 package 的
  **活面改动**；**tag → Release 不落在本任务交付内**（P2 §0「不落 tag/Release/bump 版本」）。据此核 package ↔ 实际改动面：

  | package | 实际改动落点（`git diff --name-only 581369fc..9771e76a` 实测） | 判定 |
  |---|---|---|
  | `agate-cards` | `agate/phase-cards/{P8-release.md,P5-verification.md,README.md}` | 吻合 |
  | `agate-state-machine` | `agate/state-machine.md` | 吻合 |
  | `agate-rules` | `agate/rules/{phases.yaml,obligations.yaml,state-transitions.md,task-data/level-2.yaml,task-data/LEVELS.yaml}` | 吻合 |
  | `agate-scripts` | `agate/scripts/{check-gate.py,agate-release.py,README.md}` | 吻合 |
  | `agate-roles` | `agate/assets/execution-roles/implementer.md`（+ `assets/templates/*` 的 R-E/R-F 反向传播面） | 吻合 |
  | `agate-dispatch` | `agate/dispatch-protocol.md` | 吻合 |
  | `agate-config` | **无文件改动**（`agate.config.yaml` 保持不动，P2 §1.2/决策 6/NB-1：`release.preset` 为**信息性声明**，无值消费方，登记 DEBT0069）——BDD-19 以「删迁移期提示块 + consistency 0 ERROR」闭合，非改该文件 | 见下注 |
  | `agate-docs` | `AGENTS.md`、`agate/git-integration.md`、`agate/UPGRADING.md`（+ `docs/design-notes/r6-*`、`agate/adr.md`） | 吻合 |
  | `ci-workflows` | `.github/workflows/release.yml` | 吻合 |

- **注（`agate-config`：声明但无文件改动）**：该 package 系因 BDD-19 涉及 `release.preset` **声明层**而声明；
  设计与实现**一致地**选择「保留该键为信息性声明、不驱动逻辑」（P2 §1.2 + 决策 6 + P4 §M-record/M10），
  故「声明 package 而实际零改动」是**设计内的有意结果**，非漂移；其一致性由 `check-protocol-consistency.py` 0 ERROR 兜底
  （P6 BDD-19）。**不计为 deviation**。
- **交付范围口径**：9 个 package 的改动**均为「READY 前置」或「独立发布流程」的配套**——无任一 package 的交付
  **要求 tag/Release 已发生**（新语义下 tag/Release 属独立流程，P2 §0②/§决策 2）。⇒ `P2§packages` 与交付范围**吻合**。
- 边界说明：本任务**不重复** RM-AG0098 已落地的「CHECK 7 去 tag + tag 指向校验」（P1 §5 / P2 §0），
  故 `check-protocol-consistency.py` 的 CHECK 7 **逻辑**不入改动面（仅措辞条件性同步），与 package 声明一致。

### 3.2 `P1§BDD` 数 ↔ `P6§results` 数 ↔ `P6.5` `criteria_total`（**数量 + 内容**双核）

- **数量**：`P1-requirements.md` 标题级 `^#### BDD-NN:` 计数 = **23**（`grep -cE '^#### BDD-'` 实测 = 23，
  BDD-1..BDD-23 连续无跳号）；`P6-acceptance.md` frontmatter `results` = **23** 条（`bdd: '1'..'23'`）、
  `pass: 23 / fail: 0`；`P6.5-judge-verdict.md` `criteria_total: 23` / `criteria_passed: 23` / `partial: false`。
  ⇒ **23 = 23 = 23**，三者相等。
- **内容映射抽核（≥3 条，独立读证据比对，不看标题）**：
  1. **BDD-1**（P1§BDD-1 = 「六处语料内『tag 作为 P8 条件/动作』零命中」）↔ `P6-evidence/bdd-01.log`：实测命令
     检索六文件 `grep -nE 'git tag|tag 已创建|tag 检查|先 tag|tag 创建'` → **exit=1（0 命中）**，且逐文件计数全 0；
     正确排除 P8-release.md :99-103 发布流程顺序（BDD-1 显式排除项）。**映射正确，非同名空转**。
  2. **BDD-11**（P1§BDD-11 = 发布门校「tag↔提交一致」badge/CHANGELOG 版本节）↔ `P6-evidence/bdd-11.log`：
     解析 `release.yml` 的「Verify tag points to matching commit」步存在且 fail-closed；并以 `TAG=v9.9.9` 对
     badge=v1.2.3 的**反例**实跑 → `EXIT: 1`，正例 → `EXIT: 0`。**映射正确**。
  3. **BDD-17**（P1§BDD-17 = `delivery.method` 取枚举外非空值 → exit 1，BDD-16 反例）↔ `P6-evidence/bdd-17.log`：
     level-2 夹具 `method: definitely-not-in-enum` → 报「不在快照 `delivery.method_enum` 内」**`EXIT: 1`**；并附
     「不设 `AGATE_ROOT`（解析到无 level-2 的稳定版）→ rc=2」的对照，证明枚举校验**确由本工作树 `level-2.yaml` 驱动、非真空**。
     **映射正确**。
- **P3↔BDD 映射**：`P3-test-cases.md` §2 表把 23 条 BDD 1:1 映射到用例名（测试名内嵌 BDD 编号），与 P1/P6 同集。
- ⇒ **数量匹配 + 内容映射抽核（3/3）均正确**（P7 卡常见错误 2「数量对但内容映射错」**未命中**）。

### 3.3 `P4§impl-path` ↔ `P2§decision`（M1–M16 落点 ↔ 实际改动文件）

- `P2-design.md` §1.1（`P2§decision`）规划 **M1–M16**（16 个改动落点）；`P4-implementation.md` §3 给出同编号的
  「改了什么（实测）」对照表。逐条比 `P2§1.1` 声明文件 ↔ `git diff --name-only 581369fc..9771e76a` 实际文件：

  | # | `P2§1.1` 声明文件 | 在 `git diff` 改动面 | 判定 |
  |---|---|---|---|
  | M1 | `agate/scripts/check-gate.py` | ✓ | 吻合 |
  | M2 | `agate/phase-cards/P8-release.md` | ✓ | 吻合 |
  | M3 | `agate/state-machine.md` | ✓ | 吻合 |
  | M4 | `agate/rules/state-transitions.md` | ✓ | 吻合 |
  | M5 | `agate/rules/phases.yaml` | ✓ | 吻合 |
  | M6 | `agate/rules/obligations.yaml` | ✓ | 吻合 |
  | M7 | `agate/tests/unit/test_tag0050_obligations_enforcement.py` | ✓（+ `test_tag0051_obligations_sync.py` 为 P3 面） | 吻合 |
  | M8 | `agate/rules/task-data/level-2.yaml`（**新增**） | ✓（`A`） | 吻合 |
  | M9 | `agate/rules/task-data/LEVELS.yaml` | ✓ | 吻合 |
  | M10 | `agate/UPGRADING.md` | ✓ | 吻合 |
  | M11 | `agate/scripts/agate-release.py`（新增 `gate` 子命令） | ✓ | 吻合 |
  | M12 | `.github/workflows/release.yml` | ✓ | 吻合 |
  | M13 | `AGENTS.md` | ✓ | 吻合 |
  | M14 | `agate/git-integration.md` | ✓ | 吻合 |
  | M15 | `agate/dispatch-protocol.md` | ✓ | 吻合 |
  | M16 | `agate/assets/execution-roles/implementer.md` | ✓ | 吻合 |

- **16/16 落点均在实际改动面内**，`P4§impl-path`（§3 表）与 `P2§decision`（§1.1 表）**逐条吻合**。
- **批外增量**（P4 §2 登记，均已落面，非漂移）：`agate/WORKFLOW.md`、`agate/adr.md`（ADR-016）、
  `docs/design-notes/r6-allowlist.yaml`（D13）、`agate/phase-cards/{P5-verification.md,README.md}`、
  `agate/assets/templates/{task-files,active-tasks-template,dispatch-prompt}.md`、`agate/scripts/README.md`、
  `agate/tests/README.md` —— 属 R-B/R-D/R-E/R-F 修复轮的反向传播/收口面，P4 §2 已如实登记。
- **落点自查**：M1 的枚举钩子「读快照 `delivery.method_enum`，缺省 no-op，仅非 legacy 且 task_level ≥2 生效」
  与 P2 §1.1 脚注 + P4 §M1 实测表述一致（P6 BDD-16/17 已证生效且非真空）。

---

## 4. 未决项清零

- `P1-requirements.md` **无**行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]`
  （`grep -nE '^\s*>?\s*-?\s*\[(NEED_CONFIRM|BLOCKER|DEVIATION-CRITICAL)'` → 无命中）；§6 显式写 `[NO_NEED_CONFIRM]`。
- `P4/P5/P6/P6.5` 产出**无**行首 `[BLOCKER]` / `[DEVIATION-CRITICAL]` 标记。
- `P6-acceptance.md` 为客观二值验收（23 PASS / 0 FAIL），无 NEED_CONFIRM 残留。
- ⇒ 未决项清零**通过**。

---

## 5. CODE-MAP 核对（`{AGATE_WORKSPACE}/agents/CODE-MAP.md` ↔ `P4§「新增文件核对表」`）

> `CODE-MAP.md` **存在**（实测 11069 B），故须核。P4「## 新增文件核对表」= **4 行**（P4 §6.2 亦列 4 个新文件）。

| # | 新增文件（P4 声明） | CODE-MAP 记录 | P4 处置 | 判定 |
|---|---|---|---|---|
| 1 | `agate/rules/task-data/level-2.yaml` | **未含**（实测 `grep 'level-2.yaml' CODE-MAP.md` 零命中） | `[CODE_MAP_EXEMPT: 契约级快照数据文件（非代码模块），由 LEVELS.yaml 登记 + CHECK 16 守护]` | 处置成立 → `[CODE_MAP_SYNC:]` |
| 2 | `agate/tests/fixtures/task-data/level-2/pass/README.md` | **未含** | `[CODE_MAP_EXEMPT: 测试黄金 fixture 说明文件，非代码模块]` | 处置成立 → `[CODE_MAP_SYNC:]` |
| 3 | `agate/tests/fixtures/task-data/level-2/fail/README.md` | **未含** | 同上 | 处置成立 → `[CODE_MAP_SYNC:]` |
| 4 | `docs/design-notes/r6-differential-prepare.sh` | **未含** | `[CODE_MAP_EXEMPT: docs/ 下一次性差分 wrapper，Check9/SG.6/CHECK10 三处均不扫 docs/；非 agate/ 代码模块]` | 处置成立 → `[CODE_MAP_SYNC:]` |

- **配对计数**：`code_map_new_files_count: 4` / `code_map_reviewed_count: 4`（4/4 配对；`P4` 行首
  `[CODE_MAP_EXEMPT]` 实测 4 条表格行 + 1 条模板串，核对面 = 4）。
- **判定依据**：4 文件分别为**契约快照数据 / 测试 fixture 说明 / docs wrapper**，均**非 `agate/` 代码模块**，
  不入 CODE-MAP.md 的模块面**属正确处置**；`CODE-MAP.md` 实际未含这 4 个文件与处置一致。**无 `[CODE_MAP_DRIFT:]`**。
- **依赖方向**：新文件均不引入跨模块反向依赖（数据文件 + docs wrapper）⇒ 未违反 CODE-MAP.md「依赖方向」。
  （人工判断，不做跨语言静态依赖分析，ADR-003 合规。）

---

## 6. 架构决策落点核对（`{AGATE_WORKSPACE}/decisions/`）

- `agate-workspace/decisions/` **不存在**（实测 `ls agate-workspace/decisions` → 「没有那个文件或目录」；
  与 P2 §0 记录一致）⇒ **本任务无既有跨任务决策可核，也无被本任务证伪的既有决策需就地标注「已过时」**。
- **显式结论：`decisions/` 缺失 ⇒ 无待办**（仅核对，不在 P7 撰写决策正文，符合 DEBT0039 口径）。
- 本任务新增的架构决策 **ADR-016「发布与任务解耦——任务止于 READY，Release 为独立流程 + 人工授权入口」**
  落在**协议层** `agate/adr.md`（实测 `grep 'ADR-016' agate/adr.md` → 命中，L663）。**落点恰当**：该决策是
  **协议本体级**（约束 P8/READY 语义与发布流程），非「项目侧」跨任务决策；项目 `decisions/` 面不存在，无从重复。

---

## 7. 已知偏离（deviation）逐条转抄 + verdict（来源：`P4-implementation.md` §10 + SELF-GATE 评审登记项）

> 逐条**保留人类痕迹**转抄，并给出独立的 `verdict`。**5 条均非阻塞**（`deviation_critical_count: 0`）。

- **D1**：`P2-design.md` §决策 8/§5（`:235`/`:326`/`:337`）仍述 wrapper 用 `cp -a` + `checkout -- .` +
  `clean -fdx`，而实现已换 **`git clone --local --no-hardlinks`**（外部契约不变：同名参数、corpus 干净、
  跑后真仓干净）。**独立复核**：`P2-design.md:235/283/326/337` 确仍见 `cp -a`；`docs/design-notes/r6-differential-prepare.sh:198`
  确为 `git clone --local --no-hardlinks`。**verdict = `accepted`**——依据：换实现**由本轮派发指引授权**
  （P2 卡允许 `env_constraints`/实现细节层面调整，非未评审的自主决策）；`P4-review.md` R2 判「已批准设计记录 vs
  实现，留待 P7 以已知偏离处置」；SELF-GATE 最终复审判「内部实现细节偏离设计记录、非协议语义 MISALIGNED、可留待 P7、
  不阻断」。外部可观察契约（参数名 / 干净 corpus / 跑后真仓干净）未变 ⇒ **非 CRITICAL**。

- **D2**：`docs/design-notes/r6-differential.sh::_error_lines` 的**实际比较口径**（所有 `GATE ` 前缀行，
  实测 `:251 if line.startswith("GATE ") and ":" in line`）比其文件头自述的「(退出码, ERROR 行集合)」（`:6`）
  更宽 ⇒ 本任务 P8 成功文案删 ④ 被判为差异。**verdict = `accepted`**——依据：已由 **allowlist D13** 记录
  （`r6-allowlist.yaml` `required_ids` 已含 D13，实测），**不收紧守卫强度**；口径落差由主 Agent 另行登记 **DEBT0070**
  （不在本任务修复面）。属**既有工具（RM-AG0109 项目资产）的口径陈述落差**，本任务以「登记不改守卫」处置，**非 CRITICAL**。

- **D3**：`agate/tests/` 内一处注释仍述 wrapper 旧 `cp -a` 序列。**独立复核**：`agate/tests/unit/test_tag0051_r6_harness.py:6`
  注释确述「先 `cp -a` 建一次性…」。**verdict = `accepted`**——依据：SELF-GATE 最终复审登记为**注释级、非阻塞**，
  不影响任何断言（断言面为 `--dst` 负例与真仓不受触）。

- **D4**：`P2-design.md` §5 的 `cp -a` 描述（`:283`，**与 D1 同源**，此处单列以便逐条可追溯）。**独立复核**：`:283`
  确有 `cp -a <src> <dst>` + `checkout -- .` + `clean -fdx`。**verdict = `accepted`**——**同 D1 依据**（同一外部契约不变的
  实现细节偏离；单列仅为逐条可追溯，与 D1 为**同一偏离**的两个记录点）。

- **D5**：`agate/phase-cards/README.md` / 模板中「P8 release bump 范围」类措辞、README 交付小结模板
  `[{task_id}] READY — {task_name} {version}` 的 `{version}` 语义存疑。**独立复核**：`agate/assets/templates/task-files.md:477`
  仍见「P2§packages 与 P8 release bump 范围一致」（`consistency-reviewer.md:53` / `phase-cards/P7-consistency.md:33`
  同族）；READY 小结模板 `[{task_id}] READY — {task_name} {version}` 在 `agate/dispatch-protocol.md:1335` 与
  `agate/state-machine.md:284` **两处逐字一致**。**verdict = `accepted`**——依据：SELF-GATE 最终复审登记，
  **主 Agent 已裁决**：READY 模板**保留不动**（两处逐字一致、不涉 `tag` 字面、BDD-1 不覆盖；改动会波及 READY
  标记格式与既有看板/日志惯例）；「release bump 范围」措辞族为「P7 卡通用表述」，其语义在**新口径**下由
  「交付范围（READY）」承接，非协议判据本身。**非 CRITICAL**。

> **D4 ⊂ D1 说明**：D4 与 D1 为**同一偏离**（`P2-design.md` 的 `cp -a` 描述 vs 实现 `git clone`）的两个记录点，
> 为保持与来源逐条可追溯，`deviation_count` 按**转录条目**计 **5**（D1–D5）；按**独立根因**则为 4 类
> （D1≡D4 / D2 / D3 / D5）。

---

## 8. 附加观察（note 级，不阻断、不计入 deviation）

- **R3（注释级）**：`docs/design-notes/r6-differential-prepare.sh:24` 头部注释仍述「⑤ 会 `clean -fdx`」，
  与同文件 `:18`/`:192` 的 clone 实现自述**不一致**（`P4-review.md` R3 已登记；注释级、无行为影响）。
  与 D3 同族（旧 `cp -a`/`clean -fdx` 措辞残留），本报告一并记录，**不阻断推进**。
- **P4-review 的 INFO 项**：`P4-review.md` §3.2 另登记 SEC-10..SEC-13（INFO 级安全/健壮性建议，如 wrapper
  负例补全、`--src` 非 git 仓探活）。均 INFO、非阻塞，本报告不重复展开。

---

## 计数汇总（与 frontmatter 一致）

`blocker_count=0` / `deviation_count=5` / `deviation_critical_count=0` /
`design_gap_count=0` / `design_gap_reviewed_count=0` /
`code_map_new_files_count=4` / `code_map_reviewed_count=4`。

## 预跑 gate（自查 ≠ gate）

主 Agent 亲跑：`python3 ~/.agate/current/agate/scripts/check-gate.py P7 <task_dir>`。
本报告为**只读审查结论**，不预判 gate 退出码。

## 环境隔离

[PROD_NOT_TOUCHED] 本轮仅只读审查本 checkout 内任务产出与协议文件（`git log`/`git diff --name-only`/
`grep`/`read`），仅写本文件；未接触生产环境、未改账本、未 `git add`/`commit`/`tag`、未触发 `workflow_dispatch`。
