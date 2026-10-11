---
review_date: 2026-10-11
reviewer: protocol-alignment-review
task_id: TAG0051
phase: P4
retry: 2
status: approved
change_summary: "TAG0051 任务与发布解耦（最终增量复审 retry 2）：P8 去 version/tag（gate_p8 删四块）+ delivery.method 枚举收紧（新增 level-2 契约）+ 发布门 agate-release.py gate + release.yml workflow_dispatch + 文档口径收敛。R-E（8 文件文档收敛）+ R-F（收口 3 条超授权项 + wrapper 换 git clone）已闭合 retry 1 全部 4 项 MISALIGNED（同一主题=反向传播文档残留）；0 协议语义 MISALIGNED。"
files_changed: [agate/scripts/check-gate.py, agate/scripts/agate-release.py, agate/scripts/README.md, .github/workflows/release.yml, agate/rules/task-data/level-2.yaml, agate/rules/task-data/LEVELS.yaml, agate/rules/obligations.yaml, agate/rules/phases.yaml, agate/rules/state-transitions.md, agate/phase-cards/P8-release.md, agate/phase-cards/P5-verification.md, agate/phase-cards/README.md, agate/state-machine.md, agate/WORKFLOW.md, agate/dispatch-protocol.md, agate/adr.md, agate/UPGRADING.md, agate/git-integration.md, AGENTS.md, agate/assets/execution-roles/implementer.md, agate/assets/templates/dispatch-prompt.md, agate/assets/templates/task-files.md, agate/assets/templates/active-tasks-template.md, agate/tests/README.md, docs/design-notes/r6-differential-prepare.sh, docs/design-notes/r6-allowlist.yaml, agate/tests/unit/test_tag0051_*.py, agate/tests/unit/test_release_gate.py, agate/tests/unit/test_release_workflow.py, agate/tests/unit/test_check_gate.py, agate/tests/unit/test_gate_layer.py, agate/tests/unit/test_tag0050_*.py, agate/tests/integration/test_pre_commit_hook.py, agate/tests/integration/test_tag0050_*.py, agate/tests/regression/test_v060_p8_cached.py, agate/tests/fixtures/task-data/level-2/*, agate-workspace/tasks/TAG0051-release-decoupling/P2-design.md]
---

# 协议-脚本对齐审查 — TAG0051 P4（SELF-GATE，最终增量复审 retry 2）

> **审查对象**：工作区**未提交**改动（`git status`；HEAD=`d4e32f4`；分支 `task/TAG0051-release-decoupling`）。
> **本轮性质**：retry 1 判 `needs-revision`（4 项 MISALIGNED = 同一主题「反向传播文档残留」）后的**最终增量复审**——逐条核闭合 + 查新破坏 + 对「两条已知未改项」裁决。
> **只读**：本审查未对真实仓库做任何写类操作；R6 建 corpus 只作用于一次性 `--dst`（`/tmp/opencode/…`，跑完保留亦不影响真仓）；变异/负例 scratch 均在 `--dst` 校验失败即 `exit 2`、未删除任何真仓文件（见「只读纪律自核验」节）。
> **结论**：**approved** —— retry 1 的 **4 项 MISALIGNED 全部闭合**（逐条实读/实跑核验），**0 项协议语义 MISALIGNED**。余留 **一组非行为性陈旧描述**（6 处两族：wrapper 机制描述 `cp -a`/`clean -fdx`、P8「release bump」措辞残留），**均不涉行为/判据/acceptance criterion**，判为「内部实现细节 / 陈旧措辞偏离」，**不阻断 P4**，建议随 **P7** 一致性阶段收口（见「残余登记」节）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（retry 1 的 1r `check-gate.py:25` + 1s `implementer.md` 同文件矛盾——**均已闭合**） |
| A2 | 脚本→文档对齐 | **ALIGNED**（retry 1 的 2r 四处——**均已闭合**） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（A3a 闭合；A3b `scripts/README.md:149` / `tests/README.md`——**均已补**；余留见「残余登记」） |
| A4 | 测试覆盖 | **ALIGNED**（全量实跑 2 failed / 2957 passed / 2 skipped，两红均非本任务） |
| A4b | 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054） | **ALIGNED**（经实测**无本任务引入的既有用例转红**） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（破坏性面如实框定；CHANGELOG 条目按协议留待 P8） |
| A6 | 锚点表覆盖 | **ALIGNED**（未新增/改名 `agate/scripts/` 下文件；CHECK 9 无适用项） |
| A7 | 设计原则一致性 | **ALIGNED**（ADR-016 已落盘，格式/索引正确） |
| A8 | 声称-命令绑定 | **ALIGNED**（关键声称均可复现；发现 1 处 WARNING 计数 432↔433 微差，如实记录） |

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**retry 1 的 1r（`check-gate.py:25` 模块 docstring 自述与实现不符）→ 已闭合。** 实读 `agate/scripts/check-gate.py:25`：

> `  P8: P8-release.md bump_type/debt_check + 结构化 delivery（method 枚举校验） + roadmap RM 反查`

与同段 `:27`「本脚本的判定逻辑与 state-machine.md 步骤 5 保持同步」自洽（步骤 5 已去 version/tag）。**闭合**。

**retry 1 的 1s（`implementer.md` 同文件自相矛盾）→ 已闭合。** 实读 `agate/assets/execution-roles/implementer.md`：

- `:45`（输出）＝「交付收尾记录：**每个包**的 `bump_type` 意图、CHANGELOG `[Unreleased]` 条目、交付检查结果、commit」；
- `:49`（质量门槛）＝「**P2 声明的每个 package 都要** `bump_type` 意图声明 + CHANGELOG `[Unreleased]` 含 task_id 条目 + 交付检查（P2 `gate_commands` 逐包 exit 0）」；
- `:89` 节标题＝「## P8 多包交付收尾（T005 教训：漏处理 MCP 包）」；`:90-101` 正文＝逐包「声明 `bump_type` 意图 + 更新 CHANGELOG `[Unreleased]` + 跑交付检查命令」、「P8-release.md 为每个包列出：包名 / `bump_type` 意图 / 交付检查命令与结果」；
- `:101`（无可争议的 canonical 否定式）＝「**P8 不含 version bump / tag**…」。

⇒ 同文件**已无**「版本 bump / 旧版本→新版本」表述，与 `:101` 一致。**闭合**。

### A2: 脚本→文档对齐 — ALIGNED

**retry 1 的 2r（四处仍述被删的 P8 version/bump 语义）→ 四处均已改 canonical。** 实读：

| 文件:行 | 现状 |
|---------|------|
| `agate/phase-cards/P5-verification.md:147` | 「P8 **交付收尾后**重跑 P5 gate（确认交付收尾后测试仍全绿）」 |
| `agate/phase-cards/README.md:18` | 「P8 \| 交付收尾：`bump_type` 意图 / CHANGELOG `[Unreleased]` / 收尾清理」 |
| `agate/assets/templates/task-files.md:38` | 「P8 \| P8-release.md \| 每个 package 的 `bump_type` 意图 + CHANGELOG `[Unreleased]` 条目 + 临时资源清单」 |
| `agate/assets/templates/active-tasks-template.md:54` | 「P8 \| P8-release.md \| `bump_type` 意图 + CHANGELOG `[Unreleased]`」 |

**R-F 收口 ②③（新破坏重点）→ 实读逐字一致。** 见 A3「新破坏」节。**闭合**。

> 余留的「P8 release bump 范围」措辞（`consistency-reviewer.md:53` / `P7-consistency.md:33` / `task-files.md:477`）与 `dispatch-protocol.md:948` 见「残余登记」——**非行为性措辞**，retry 1 已判「不单独计 blocker」，本轮维持不阻断裁决。

### A3: 一致性连锁 + 反向传播 — ALIGNED

**A3a（已知衍生改动）— 闭合**：`obligations.yaml` OBL-P8-04 就地重挂（`disposition` 保 **M**）、`check-obligations.py` 实跑 → `M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）`、`CHECK-OBLIGATIONS: OK`，**rc=0（未降）**；`phases.yaml` / `state-transitions.md` 已改（见 A4b S-3b）。

**A3b（反向传播 — 应被影响但未在 diff 中的文件）**：

| 文件 | retry 1 判定 | 本轮实测 | 结论 |
|------|-------------|---------|------|
| `agate/scripts/README.md:149` | 未闭（minor） | 索引行现含 `gate [--task DIR] [--sha SHA] [--repo R]`（发布门：CI success + consistency 0 ERROR + check-gate.py P8，TAG0051） | **已闭合** |
| `agate/tests/README.md` | 未闭（minor） | `:97` 现登记 `agate-release.py gate（发布门…）→ unit/test_release_gate.py + unit/test_agate_release.py` | **已闭合** |
| `agate/assets/execution-roles/implementer.md` | **漏** | 见 A1（已改） | **已闭合** |
| `agate/phase-cards/P5-verification.md` / 卡片/模板 | **漏** | 见 A2（已改） | **已闭合** |
| `agate/adr.md` | 需新 ADR | ADR-016 已落盘（见 A7） | ALIGNED |
| `agate/rules/dispatch.yaml` / `roles.yaml` / `review-mapping.md` / `role-system.md` / `orchestrator-template.md` / `LIMITATIONS.md` | 否 | 语义族 grep 无新增命中 | ALIGNED |
| `agate/rules/task-data/level-1.yaml` | 否（冻结，正确） | 未改 | ALIGNED |

**本轮「新破坏」专项核查**：

1. **R-F 改了 `dispatch-protocol.md` 的节名索引 ⇒ 与 `dispatch-prompt.md` 实际节名逐字一致？** — **是**。`agate/assets/templates/dispatch-prompt.md:277` = `## \`bump_type\` 意图判定（不执行 bump；对外发布由独立流程负责）`；`agate/dispatch-protocol.md:487` 合并节清单内同一串 ⇒ **逐字一致**（实读比对）。全文再无其他文件引用旧节名「版本 bump 判定」（`grep` 仅命中本报告将覆盖的 retry 1 旧产出）。
2. **wrapper 改实现（`git clone`）后其文件头注释 / `P5_r6` 声明是否仍自洽？** — **主体自洽**：`:15-18`（行为序列 ④，含「`git clone --local --no-hardlinks`」+「故**无需**再 `checkout -- .` + `clean -fdx`」）与 `:189-198`（实现）一致；`:33`「真实仓库仅被 git clone 只读」亦同步。**唯一不自洽**＝ `:24` 仍述「本 wrapper 的 ⑤ 会 `clean -fdx` 掉副本里未跟踪的新文件」——与本文件 `:18`/`:192` 直接冲突（⑤ 现为 `exec`，不再 clean）。**评论级、无行为影响**，登记为残余 R3（见下）。
3. 语义族 grep（`agate/` + `AGENTS.md`，排除 `tests/`，与指引逐字同模式）＝ **35 命中（38→35，-3 恰为目标行）**，逐条归类仅三类：① 显式否定式；② 历史/迁移/独立发布流程；③ 改动自身引用。**无第四类残留。**

**level-2 契约连锁副作用** — 已由 `UPGRADING.md` 如实框定（见 A5），ALIGNED。

### A4: 测试覆盖 — ALIGNED（附全量实跑输出）

新逻辑有**直接**用例：BDD-16/17（枚举，level-2 夹具）、BDD-8~13（`test_release_gate.py`）、BDD-20（R6 wrapper 契约）、BDD-19（静态面）、BDD-21（obligations 语义）。**本轮全量实跑**（本机，工作区**未提交**，`env -u AGATE_ROOT` 对齐 CI 口径）：

```
$ env -u AGATE_ROOT timeout 1800s python3 -m pytest agate/tests/ --reruns 1 -n auto -q
2 failed, 2957 passed, 2 skipped, 2 rerun in 114.04s (0:01:54)
```

两条红**均非本任务缺陷**：`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（本机 opencode CLI 子命令 `debug agent`→`agents` 漂移，环境项）+ `test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review`（**设计性必红**：本评审查的提交尚未发生，BDD-22 要求协议提交带 `self-gate-review:` 留痕，而**本报告正是为让它可发生**——实读其 `_missing_trailer_paths` 用 `git cat-file -e <sha>:<probe>`）。

定向复跑：`test_tag0051_r6_harness.py + test_tag0051_docs_consistency.py + test_check_gate.py + test_release_gate.py + test_release_workflow.py` → **260 passed in 47.21s**。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED

**本轮（R-E/R-F）为纯文档/注释口径收敛 + wrapper 实现替换 ⇒ 经实测无既有用例转红。** 证据：全量 `2 failed / 2957 passed / 2 skipped`，两条红**均非本任务**（`test_bdd_43` 环境项、`test_bdd_22` 设计性必红）；`count-tests` = **2961**（未漂移，与 retry 1 同）；`check-structure-consistency.py` rc=0。

- **夹具更新清单（本轮 = 空）**：R-E/R-F **未新增/未改**任何测试夹具；`agate/tests/unit/test_tag0051_obligations_sync.py` 的修改属 P4 早期批次（非本轮），已随既有绿灯。
- **retry 1 的 54 红闭合仍成立**：`test_pre_commit_hook.py::_seed_task_created` 默认 `contract_level` 1→2（4 处共享夹具）、`test_tag0050_write_tools.py::test_f2` 夹具整目录复制补 `level-2.yaml`、`test_release_gate.py` `H.GENESIS_HASH→H5.GENESIS_HASH` —— 均由本轮全量实测确认无回归。

### A5: 下游影响 + 文档传播 — ALIGNED

- **破坏性面（retry 1 MISALIGNED-5）→ 已闭合**：`agate/UPGRADING.md:286` 节标题＝「（**面向新任务的准入行为变化**）」，正文显式写明「登记 `rules/task-data/level-2.yaml` 后，协议当前契约等级由 1 抬升为 2…⇒ 升级后所有非 legacy 新任务均须为等级 2；`delivery.method` 枚举收紧随之对**所有项目的新任务**生效…**这不是「无破坏性变更」**」。与 `adr.md` ADR-016「破坏半径」段一致。**ALIGNED**。
- **文档传播（角色/模板/卡片）→ 已闭合**：见 A1/A2/A3b 清单（`implementer.md` / `P5-verification.md` / `phase-cards/README.md` / `task-files.md` / `active-tasks-template.md` / `scripts/README.md` / `tests/README.md` 均已改 canonical）。
- `AGENTS.md:188/194/207/209`（发布清单 tag 时点 + 无失败处置）/ `agate/git-integration.md:190`：与 BDD-14/15 一致 — ALIGNED。
- `CHANGELOG.md`：`[Unreleased]` **尚无 TAG0051 独立条目**（`:155` 的 `TAG0051` 字面是**既有批**「RM-AG0103 → 已拆任务 TAG0051」的登记，非本任务条目）。按协议，CHANGELOG 条目在 P8 写入（READY 前置 = `[Unreleased]` 含 task_id），P4 不要求 — **可接受**，提醒 P8 必须补（否则 `check-changelog.py` 会拦）。
- `adr.md` 索引：文件无目录/索引表（仅顺序 `## ADR-NNN`，实测 `grep -c '^## ADR-'` = 16），ADR-016 无需同步索引项 — ALIGNED。

### A6: 锚点表覆盖 — ALIGNED

本任务**不新增/不改名 `agate/scripts/` 下任何文件**（仅改 `check-gate.py`、`agate-release.py`、`README.md`；实测 `git status --porcelain agate/scripts/` 仅三个 ` M`，无 `??`）⇒ 按 `agate/scripts/README.md`「新增脚本登记面」节，**三处判定均无适用项**：① `CHECK9-coverage` / ② SG.6 判据 `uncovered_gate_scripts()` 只 glob `check-*.py`；③ CHECK 10 只报「引用了不存在脚本」。实测 `AGATE_ROOT=$PWD/agate python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（rc=0）。新增 `delivery.method` 枚举规则由**直接 pytest 用例**（BDD-16/17）守护，无需新增关键词锚点。

### A7: 设计原则一致性 — ALIGNED

首轮判 NEEDS_HUMAN_REVIEW，**主 Agent 已裁决补 ADR-016**。本轮核验 `agate/adr.md:663-716`：

- **格式**：`## ADR-016: 发布与任务解耦——任务止于 READY，Release 为独立流程 + 人工授权入口`，含「### 状态 / ### 语境 / ### 决策 / ### 理由 / ### 后果」+ 关联，与 ADR-001…015 既有条目格式一致；
- **索引**：`adr.md` 无目录/索引表 ⇒ 无需同步；
- **内容一致性**：决策①（READY 前置含「**不含** version bump / tag」）与 `state-machine.md` / `WORKFLOW.md` / `phases.yaml` 一致；决策③「不引入第二套阻塞语义」符合 ADR-015；对照 ADR-002（可判定性）/ ADR-001（隔离性）/ ADR-013（gate 生产者无关性）方向一致。

⇒ 判 **ALIGNED**。

> `state-machine.md:284` = `dispatch-protocol.md:1335` 的 READY 交付小结模板 `[{task_id}] READY — {task_name} {version}`（两处逐字一致、本次未改）——**主 Agent 已明示裁决保留不动**（R-E progress 记录）。本审查**尊重该裁决**，仅登记为残余 R6（低危：`{version}` 为模板占位符，其取值口径可在 P7 或后续收敛）。因两处一致且不涉 `tag` 字面（BDD-1 不覆盖），本轮**不作 MISALIGNED**。

### A8: 声称-命令绑定 — ALIGNED

本批**数字与结论类声称**逐条给出产出命令（本轮实测）：

| # | 声称（来源） | 产出它的命令 | 结论 |
|---|-------------|-------------|------|
| 1 | `M 类占比: 56/121` | `AGATE_ROOT=$PWD/agate python3 agate/scripts/check-obligations.py` → `M 类占比: 56/121 = 0.4628（基线 56/121）` + `CHECK-OBLIGATIONS: OK`，rc=0 | ✅ |
| 2 | 全量 `2 failed / 2957 passed / 2 skipped` | `env -u AGATE_ROOT timeout 1800s python3 -m pytest agate/tests/ --reruns 1 -n auto -q` → `2 failed, 2957 passed, 2 skipped, 2 rerun in 114.04s` | ✅（两红 = `test_bdd_43` 环境项 + `test_bdd_22` 设计性必红） |
| 3 | `count-tests` = 2961 | `bash agate/tests/scripts/count-tests.sh` → `总计：2961 个测试用例（pytest collect-only 口径）` | ✅ |
| 4 | R6 差分 `差异 2 条 / 未匹配 0 条`（wrapper rc=0） | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r2-corpus` → `[ALLOWED] check-gate:P8 TAG0042-config-and-enforcement rc 2->2 added=1 removed=1` + 同款 TAG0050 + `legacy 任务 39 个，差异 2 条，未匹配 0 条`，rc=0，**7s**，corpus 101M | ✅（wrapper ⑤ 现 `--after <src>/agate` 真工作树；2 条差异均 `[ALLOWED]`，登记 allowlist **D13** 且 `required_ids` 含 D13） |
| 5 | `check-structure-consistency.py` rc=0 | `AGATE_ROOT=$PWD/agate python3 agate/scripts/check-structure-consistency.py` → `S1..S6 + S0-numbers 全 OK`，rc=0 | ✅ |
| 6 | `check-protocol-consistency.py` 0 ERROR / 432 WARNING | `AGATE_ROOT=$PWD/agate python3 agate/scripts/check-protocol-consistency.py` → **`仅有 433 个 WARNING，无 ERROR`**，rc=0 | ⚠️ **0 ERROR ✅**；WARNING 实测 **433**（指引称 432，差 1；逐条展开确认全为 `frozen: true` 的 CHECK2-refs/CHECK1-yaml/CHECK10-scriptref，且随 `tasks/`、`reviews/` 文件集 ±1 漂移，非 ERROR、非本任务新增）——**本地实测以 433 为准** |
| 7 | wrapper 负例 rc=2 | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst {∅,/ ,rel/dir,<src>/agate,/home/kity/keepdir}` → 全 **rc=2**，且真仓 `git status` 仍 79 行、无删除 | ✅ |
| 8 | `gate` 子命令存在 | `agate-release.py` 索引行含 `gate [--task DIR] [--sha SHA] [--repo R]`（`scripts/README.md:149`）+ `tests/README.md:97` 登记 | ✅ |

⇒ **无不可复核的实质声称**；WARNING 计数微差（432↔433）已如实以本地实测值 433 记录，不涉结论。

---

## 残余登记（**非阻断** — 非行为/判据/acceptance，建议随 P7 收口）

| id | 位置 | 性质 | 处置 |
|----|------|------|------|
| **R1** | `agate/tests/unit/test_tag0051_r6_harness.py:6`（注释「先 `cp -a` 建一次性整仓 corpus」） | 已知项①：wrapper 旧机制描述 | **裁决：非协议语义 MISALIGNED**（注释级、不影响断言）；可随 P7 或顺手改 |
| **R2** | `agate-workspace/tasks/TAG0051-release-decoupling/P2-design.md:235/283/326/337`（述 `cp -a` + `checkout -- .`+`clean -fdx`） | 已知项②：**已批准设计记录** vs 实现 | **裁决：内部实现细节偏离设计记录**（外部契约未变）；留待 **P7** 以 DESIGN_GAP/known deviation 处置 |
| **R3** | `docs/design-notes/r6-differential-prepare.sh:24`（残余「⑤ 会 `clean -fdx`」） | R-F 换 `git clone` 后**新引入的不自洽**（与同文件 `:18`/`:192` 冲突） | **裁决：注释级、无行为影响**（默认 after=HEAD 的结论仍成立）；建议顺手改「clone 只检出已跟踪文件 ⇒ 缺省 after 侧=HEAD」 |
| **R4** | `agate/assets/execution-roles/consistency-reviewer.md:53` / `agate/phase-cards/P7-consistency.md:33` / `agate/assets/templates/task-files.md:477`（「P2 packages 与 **P8 release bump 范围**一致」） | retry 1 已列「同主题 minor（措辞）」，本轮未收敛 | **裁决：措辞陈旧**（检查意图 = 覆盖性，未变）；建议改「P8 **交付检查**范围」 |
| **R5** | `agate/dispatch-protocol.md:948`（「把'**需要 bump 哪些包**'明确写进 prompt」） | 同 R4（R-F 只改了 `:487`） | **裁决：措辞陈旧**；建议改「需要**交付收尾**哪些包」 |
| **R6** | `agate/state-machine.md:284` = `agate/dispatch-protocol.md:1335`（READY 小结模板 `{version}`） | 两处一致、本次未改；**主 Agent 已裁决保留** | **裁决：尊重主 Agent 裁决，不阻断**；`{version}` 口径可在 P7/后续收敛 |

> **为何不阻断**：以上六处均为**描述性文本**（注释 / 设计记录 / 角色卡与模板的措辞 / 模块索引），**不改变任何 exit code、判据、ERROR 集合或 acceptance criterion**；且 `R1/R2` 已由 R-F 如实上报，`R4/R5` 已由 retry 1 判「不单独计 blocker」，`R6` 经主 Agent 明示裁决。本任务 `phases` 含 **P7**（`P1-requirements.md:11-19`），一致性阶段即为既定收口面——符合「内部实现细节 / 陈旧措辞偏离 ⇒ 留待 P7」的处置。
> **grep 盲区提示（供主 Agent）**：语义族 grep 模式（`version bump|版本 bump|bump-version|bump 版本|version 文件|双路径|tag 已创建|git tag|v{prev_version}`）**不匹配** `release bump` / `bump 范围` / `bump 哪些包` —— R4/R5 即由此漏网；后续收敛若仍用该单一字面 grep，须补该族。

---

## retry 1 发现闭合总表

| retry 1 项 | 本轮结论 | 证据 |
|-----------|---------|------|
| 1r（`check-gate.py:25` docstring） | **闭合** | `:25` 已改「…结构化 delivery（method 枚举校验） + roadmap RM 反查」 |
| 1s（`implementer.md:45/49/90-101`） | **闭合** | 实读无「版本 bump」；与 `:101` 一致 |
| 2r（`P5-verification.md:147` / `phase-cards/README.md:18` / `task-files.md:38` / `active-tasks-template.md:54`） | **闭合** | 四处均 canonical |
| A3b（`scripts/README.md:149` / `tests/README.md`） | **闭合** | 索引行含 `gate`；测试面已登记 |
| R-F ①（`gate_p8` 函数头注释） | **闭合** | 实读「本函数只做脚本化可判的部分…」 |
| R-F ②③（`dispatch-prompt.md:277` ↔ `dispatch-protocol.md:487`） | **闭合** | 节名**逐字一致** |
| R-F ④（wrapper 换 `git clone`） | **闭合** | 实跑 rc=0 / 39/2/0 / 7s / 101M；负例全 rc=2 |
| **R3（新析出）** | **非阻断残余** | wrapper `:24` 残余 `clean -fdx`（评论级） |
| **R4/R5/R6（余留措辞）** | **非阻断残余** | 见「残余登记」 |

## 只读纪律自核验

- 未执行 `git checkout -- .` / `restore` / `reset` / `stash` / `clean` / `add` / `commit`（**真实仓库**）；未对真实仓库运行任何写类工具（`agate-inject-card.py` / `agate-md-field-set.py` / `agate-state-set.py` 等**一律未跑**）。
- scratch 全在一次性副本：R6 wrapper 建 corpus / `rm -rf` 只作用于 `--dst`（`/tmp/opencode/tag0051-r2-corpus`）；负例在 `--dst` 校验失败即 `exit 2`、**未做任何删除**。
- 真实仓库跑前/跑后 `git status --porcelain` 条目数一致（**79 行**）；`gate-events.jsonl` mtime 保持 `2026-10-11 11:12:35`（**未被写入**）。
- 唯一写入：`docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md`（本文件，**覆盖同一任务同日 retry 1 产出**）+ 同名 `.progress.md`（`rm -f` 后重写）。

## 闭环结论（给主 Agent）

- **0 项协议语义 MISALIGNED ⇒ `status: approved`，可 commit。**
- retry 1 的 **4 项 MISALIGNED 全部闭合**；R-E/R-F 主体改动自洽（`dispatch-prompt.md:277` ↔ `dispatch-protocol.md:487` 逐字一致；wrapper 头部除 `:24` 一行外已同步）；**未发现行为/判据层面的新破坏**。
- **两条已知未改项裁决**：属「**内部实现细节偏离设计记录 / 陈旧描述**」，**非** P4 阻断性 MISALIGNED，**可留待 P7**（R2 载体为设计记录；R1 为载体为测试注释）——与 R3~R6 同列「残余登记」，建议 P7 一并收口。
- **提醒**：① P8 须补 `CHANGELOG.md [Unreleased]` 的 TAG0051 条目；② 后续文档收敛若沿用单一字面 grep，请补 `release bump`/`bump 范围`/`bump 哪些包` 族（R4/R5 漏网点）。
