---
phase: P4
task_id: TAG0042
type: implementation
parent: P2-design.md
trace_id: TAG0042-P4-batch1-20261005
status: draft
created: 2026-10-05
agent: implementer
implementation_dir: agate/
---

# P4 实现记录 — batch1-phase-semantics（统一 phase 语义）

> 上游：`P1-requirements.md`（BDD-1 / BDD-2）+ `P2-design.md` §1.1 M1/M2/M3、§1.2 N1、
> §6.1b batch1 + `P3-test-cases-batch1.md`（TC-B1-01/02、TC-B2-01..04，P3 已写、当前红）。
> **范围**：只做 batch1（统一 phase 语义）；不碰 batch2-6（agate-config / agate-run / 关卡分级 /
> CI 诊断 / obligations）。目标语义：`phase` 只表示「**本 commit 的产出阶段**」——`agate-next`
> 推进时**不预写**下一阶段，只输出「下一阶段建议」并保留 `state_transition` 证据。

## 改动清单

### 1. `agate/scripts/agate-next.py`（核心行为，P2 §1.1 M1）

| 落点 | 改动 |
|---|---|
| `_advance()`（原 L198-210） | 去掉 `state["phase"] = target`（预写）+ `_write_state(...)`（落盘）+ `_git(["add", <task>/.state.yaml])`（自动暂存）；**保留** `_state_transition_event(...)`（append_event `state_transition`）。改为输出「下一阶段建议」：`<old> → 建议下一阶段 <target>：.state.yaml phase **未预写**（保持 <old>）…` |
| 模块 docstring（L11-14） | 「更新 .state.yaml phase + git add」改述为「**不预写**：不写 phase、不 git add，仅 append_event state_transition 证据」 |
| 平台无关自述行（L31） | 「无 /tmp 字面量」→「无系统临时目录字面量」（该行 docstring 含 `/tmp` 字面量本身会被 `check-platform-assumptions.py` 的 R4 命中；见下方自测） |
| `_write_state()`（原 L116-129） | **删除**——唯一调用点是 `_advance` 的预写落盘；去除预写后成为孤儿代码 |
| `_git()`（原 L169-183） | **删除**——唯一调用点是 `_advance` 的 `git add`；去除后成为孤儿代码 |

> `_advance(task_dir, state, target, repo_root)` 的 `repo_root` 形参保留（批 1 后本函数不再做 git
> 操作），以兼容既有调用点（`_p6_judge_advance` / `main`），避免级联改签名。docstring 已注明。

### 2. `agate/phase-cards/P2-design.md`（P2 §1.1 M2）

- 首次进入第 5 步（L14 附近）：保留既有「phase 保持 P2，不要提前写 P3——phase = 本 commit 的
  产出阶段」，追加一句：推进（`agate-next`）亦**不预写**下一阶段，只输出「下一阶段建议」并记
  `state_transition` 证据，phase 由 P3 产出 commit 时写入。

### 3. `agate/phase-cards/P8-release.md`（P2 §1.1 M2）

- 首次进入第 5 步（L15-20 附近）：保留既有「phase = 本 commit 的产出阶段」表述，追加一句：
  `agate-next` 亦**不预写**下一阶段，phase 一律由本 commit 的产出阶段写入。

### 4. `agate/UPGRADING.md`（P2 §1.1 M3）

- §3「已知破坏性变更（按版本）」顶部**新增** `### v0.79.0 — TAG0042 批 1：统一 phase 语义
  （**无破坏性变更**）` 一节：记载 `agate-next` 推进不再预写下一阶段（原行为「gate 通过即写
  `Pn+1` + `git add`」→ 改为只输出建议 + `state_transition` 事件），并说明编排侧调整（phase 推进
  随下一阶段产出 commit 一起）；该节同时改述 v0.44.0 的「阶段卡片 phase 语义（文档，无强制）」
  现已在不可绕开路径上落地。
- **未改** v0.44.0 历史节原文——该节由回归测试
  `test_upgrading_contract_doc.py::test_bdd_39_5_section3_history_note_and_history_sections_preserved`
  锁定「历史版本节不可改写」（初版曾就地改述 L1209，被该测试判红后回退，改由新增 v0.79.0 节承接）。

### 5. `agate/tests/unit/test_tag0027_b1_agate_next_cli.py`（既有测试同步，P3 §5「P4 回归注意」）

按新语义同步「随推进查 gate 后状态」类断言（**不保留预写行为**）：

| 用例 | 原断言（预写语义） | 同步后（不预写语义） |
|---|---|---|
| `test_bdd_6_next_exit2_pass_advances_to_next_phase` | `phase == "P6"` | `phase == "P5"`（保持当前产出阶段） |
| `test_bdd_9_p6_judge_enabled_gate_p65_pass_advances_p7` | `phase == "P7"` | `phase == "P6"` |
| `test_bdd_11_healthy_exit2_full_advance_no_resolution` | `phase == "P6"` | `phase == "P5"` |

- 其余断言（`state_transition` 事件 `from/to`、不落盘 resolution、retreat 后 `phase: P4`）**不变**
  ——推进证据仍产生，回退路径（`agate-retreat-to.py`）不在本批范围、仍写 phase。
- 文件头注释与相关 docstring 同步改述（「更新 phase + git add」→「输出建议 + 不预写」）。

### 未改动的既有测试（说明）

- `agate/tests/unit/test_check_state_transition.py`：直接测 `check-state-transition.py`（手工
  stage 状态转移），不经 `agate-next`，**无与新语义冲突的断言**——未改。
- `agate/tests/unit/test_agate_next_card.py`：测 `agate-next-card.py` 的卡片输出 byte-stability
  （动态比对卡文件 sha256），**无「推进后状态」断言**——未改；卡片内容改动后仍按实际文件比对。

## 自测结果（自查 ≠ P5 gate；不预判 gate 结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch1 自跑 | `python3 -m pytest agate/tests/unit/test_tag0042_batch1_phase_semantics.py agate/tests/unit/test_agate_next_card.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py agate/tests/unit/test_check_state_transition.py -q` | `99 passed` |
| 关联回归（卡片/文档/一致性/历史节守护） | 上述 4 文件 + `test_card_render / test_agate_inject_card / test_doc_sweep / test_docs_assertions / test_env_adapt_docs / test_tag0034_docs / test_p2p4_boundary_docs / test_mvwu_protocol_docs / test_protocol_mechanism_anchors / test_protocol_dedup_audit / test_retrospective_protocol_docs / test_review_role_docs / test_upgrading_contract_doc / test_upgrading_lifecycle / test_check_protocol_consistency / test_check_structure_consistency / regression/test_no_legacy_residue` | `420 passed` |
| ruff | `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate-next.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py` | `All checks passed!` |
| 平台扫描（代码/测试文件） | `check-platform-assumptions.py agate/scripts/agate-next.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py` | `exit 0`（0 命中） |
| consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `0 ERROR / 398 WARNING`（与 P0-brief 基线一致） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2687 个测试用例`（P3 基线 2622 + 65 新用例，未漂移） |

**平台扫描说明（如实登记）**：`check-platform-assumptions.py` 的 CI 目标面是 `agate/tests/`（无参数
默认），本批改动的**代码/测试文件**扫描 0 命中。文档文件（`agate/UPGRADING.md`、两张 phase-card）
含**存量**裸 `python3` 示例行，被显式传入时会命中 R2/R4/R5——这些行**非本批引入**（历史版本节原文），
且文档不在扫描器的 CI 目标面内；本批新增段落本身无平台假设。

**现场状态说明（非本批改动）**：`agate-workspace/tasks/TAG0042-config-and-enforcement/gate-events.jsonl`
工作区有 2 条未提交事件（`check-gate.py P3` + `state_transition P2→P3`，时间戳 = P3 提交时 pre-commit
hook 追加），**非本次会话产生**；由主 Agent 在 P4 暂存阶段决定是否随任务目录一并提交。

## [SCOPE+]

无。实现严格落在 batch1（BDD-1/BDD-2）范围内；未发现必须做而 P1/P2 未覆盖的新需求。

## [DESIGN_GAP]

[DESIGN_GAP: P2 §1.1 M3 只说「UPGRADING.md 新增批 1 行为变更记载」，未指定版本节标题；实现自主采用 `### v0.79.0`（当前 badge v0.78.3 的下一 minor），P8 发版时若版本号不同需同步。]
[DESIGN_GAP: P2 §1.1 M1 只点名去除 `_advance` 的预写 + `git add`，未指明其孤儿辅助函数；实现自主删除仅服务该路径的 `_write_state()` / `_git()`（避免死代码），并保留 `_advance` 的 `repo_root` 形参以兼容既有调用点。]

## 修正轮（SELF-GATE round 2 修复）

> 触发：首轮 `protocol-alignment-review` 判 **MISALIGNED**（A1/A2/A3b/A5.3，**同一根因**）——
> 批 1 改变了 `agate next` 的可观测行为（不再预写 `phase`、不再 `git add`），但 5 处**权威文档**
> 仍逐字描述旧行为，未反向传播。本轮只做**文本改述**，不改任何机制/脚本/卡片/UPGRADING/测试。
> 统一口径（与 `agate-next.py:166-178`、`P2-design.md:15-16`、`P8-release.md:21`、
> `UPGRADING.md:288-296` 一致）：`agate next` 跑 gate → 查表算下一步 → 输出「下一阶段建议」+
> 追加 `state_transition` 事件，**不预写 `.state.yaml` 的 `phase`、不 `git add`**；`phase` 一律由
> **下一阶段产出 commit** 写入（`phase` = 本 commit 的产出阶段）。**手工 fallback 规格仍写 `phase`**，
> 已加限定句与自动化路径区分。

| # | 文件 | 位置 | 改述要点 |
|---|---|---|---|
| 1 | `agate/state-machine.md` | `:326-335`（§主 Agent 的单步执行·机械化段） | 步骤 5-7 由「写回 `.state.yaml` + git add」改为「建议推进」；明写 `agate next` 只输出「下一阶段建议」+ `state_transition` 事件、**不预写** `phase`、不 `git add`，`phase` 由下一阶段产出 commit 写入；fallback 句补充「手工 fallback 仍写 `phase`，与自动化路径不同」 |
| 2 | `agate/state-machine.md` | `:401-403`（同节手工规格 step 7） | 保留「写回 `.state.yaml`」手工规格，加限定：本步为**手工 fallback**；`agate next` 自动化路径**不写** `phase`，只输出建议 + `state_transition` |
| 3 | `agate/dispatch-protocol.md` | `:291-295` | 「跑 gate → 判定 → 前进写 phase → git add」改为「跑 gate → 判定 → 前进」；补 `agate next` 只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补「按该节手工规格写 `phase`」 |
| 4 | `agate/CONTEXT.md` | `:33`（术语表 `agate next / agate advance` 行） | 「写 `.state.yaml` + git add」改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 `.state.yaml` 的 `phase`、不 `git add`——`phase` 由下一阶段产出 commit 写入」；fallback 补手工规格写 `phase`；标注 TAG0042 批 1 |
| 5 | `agate/loop-orchestration.md` | `:242-247`（自动推进流程图） | 「更新 .state.yaml phase + git add」改为「输出「下一阶段建议」+ 追加 `state_transition` 事件，不预写 .state.yaml phase、不 git add」；跳变合法性改由下一阶段产出 commit 的 pre-commit 校验 |
| 6 | `agate/orchestrator-template.md` | `:56-59` | 「前进写 `.state.yaml` phase → commit」改为「跑 gate → 判定 → 前进」；补 `agate next` 只输出建议 + `state_transition`、不预写、不 `git add`；fallback 句补手工规格写 `phase` |

### 自查结果（自查 ≠ gate，不预判 gate 结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `exit 0`（0 ERROR / 398 WARNING，与基线一致） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2687 个测试用例`（未漂移） |

### [SCOPE+]

无。逐处只改派发清单点名的 5 处文档（共 6 个落点，state-machine.md 占 2 处）。复核全仓其余
提及 `agate next`/`phase` 写入的文档（`state-machine.md:521-523` 手工 commit 规格、
`git-integration.md:31/33/113`、`assets/templates/retrospective-template.md:134`）均为**手工提交路径**
描述，与新语义一致，不需改——与首轮审查 A3b 判定一致，未扩大范围。
