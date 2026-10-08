---
phase: P2
task_id: TAG0050
parent: P2-design.md
trace_id: TAG0050-P2-20261006
status: rejected
agent: plan-eng-review
---

# P2 工程评审（plan-eng-review）— TAG0050

> 评审对象：`agate-workspace/tasks/TAG0050-task-data-contract/P2-design.md`（candidate_count: 3，ui_affected: false，10 批 static-batch）
> 评审角色：plan-eng-review（C8：backend→plan-eng-review + high→plan-eng-review，去重为单评审）
> 评审方式：**只读评审 + 独立只读核验**（无写仓命令；验证命令均为读操作，见 §7）
> 协议版本：agate v0.78.3（`AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`）；本 checkout HEAD `adb0b11`
> 上游依据：`design-tag0050-task-data-contract.md`（r4 APPROVE WITH CHANGES）、`review-r4.md`、`review-tag0042-implementation.md`、`P1-requirements.md`（77 BDD）

---

## 0. 结论

**rejected —— 1 个阻塞（BLOCKER B1，来自 design_gap G5）。**

P2 的定位（把已 4 轮评审通过的设计形式化，不改技术决策）被正确执行：影响面梳理齐备且写在候选之前、3 候选 + 权衡、77 BDD 逐批无遗漏、`gate_commands` 一 key 一命令无 `&&` 反模式、登记面结论有机械依据。**设计形式化的正确性/完整性总体成立**。

但 `gate_commands` 是 P2 独有、且**固化后 P4–P6 不可改**的验证契约。其中 `P5_r6_differential` 指向一个**当前不存在、且未被任何批次登记为交付物**的脚本 → 该命令必然失败，且修复窗口只在 P2。这属验证契约层面的缺陷，判为 BLOCKER。

其余 design_gap（G1–G4、G6、G7）经裁决均不阻塞（G3/G4 为 MAJOR，须在对应批的 P1 落实；见 §5）。

---

## 1. 独立只读核验摘要

| # | 核验项 | 方法（只读） | 结果 |
|---|---|---|---|
| E1 | **G5：`docs/design-notes/r6-differential.sh` 是否存在** | `glob docs/design-notes/*.sh` + 全仓 grep `r6-differential` | ❌ **不存在**（仅 `repro-tag0050.sh`；`r6-differential` 只在 P2/P1/dispatch 文档出现） |
| E2 | **F8：`append_event` 参数元数不符** | 读 `pre-commit-gate.py:370` + `agate_common.py:524` | ✅ 确认：调用 **3 参** `append_event(task_dir, "prod_touched_in_paused", {...})`，定义 **2 参** `def append_event(task_dir, event)` → TypeError 被 `except` 吞掉 |
| E3 | **F12：P8 `delivery` 子串判定** | 读 `check-gate.py:1450` | ✅ 确认 `if "delivery:" not in p8_text` |
| E4 | **RM-AG0085：骨架子串判定** | 读 `check-gate.py:964` | ✅ 确认 `"## 骨架声明" not in _read_text(skeleton_file)` |
| E5 | **ID 正则不一致** | 读 `agate-state-yaml-check.py:39` | ✅ 确认 `^T[A-Z]{2}\d+$`（与设计目标 `^[A-Z]+[0-9]+$` 不一致） |
| E6 | **G1：不存在目录的 rc 随 phase 变化** | 读码 `check-gate.py` main()/gate_p1/gate_p5/gate_p7 | ✅ 确认：`gate_p1` 首查 `P1-review.md` 不存在 → `return 1`；`gate_p5` 无基线文件 → `return 2`；`gate_p7` 所有条件均不触发 → 落到末尾 `return 0`（假 PASS）。**P7→0、P5→2、其余→1** 成立 |
| E7 | **登记面机械依据** | 读 `check-protocol-consistency.py:898-922` `uncovered_gate_scripts()` | ✅ 确认只 `glob("check-*.py")` + 显式含 `pre-commit-gate.{sh,py}` → 新增 `agate-*.py`/库**不触发** CHECK9-coverage；§1.4 结论方向正确 |
| E8 | **gate_commands 可执行性（非脚本类）** | `test -x ~/.venvs/agate-dev/bin/ruff`、`command -v shellcheck`、glob 各脚本 | ✅ `ruff 0.16.4` 存在；`shellcheck` 在 `/usr/bin/shellcheck`；`check-structure-consistency.py`/`check-platform-assumptions.py`/`count-tests.sh`/`repro-tag0050.sh` 均在仓内 |
| E9 | **consistency 基线** | `check-protocol-consistency.py --strict-errors-only` | ✅ **0 ERROR / 415 WARNING，rc=0**（415>410 系 P2 阶段新增未跟踪叙事文件所致，仍无 live WARNING、无 ERROR——与 §0/§8 声明方向一致） |
| E10 | **77 BDD 逐批无遗漏/无重叠** | 逐批加总 §3 表 | ✅ 2+20+13+4+5+7+4+5+6+6+5 = **77**，区间连续无空洞 |
| E11 | **RM-AG0100/0101 登记状态** | 读 `agate-workspace/roadmap/roadmap.md:99-100` | ✅ 两条均已在 roadmap 登记（backlog），且 RM-AG0100 明记"设计 §2.7「2h.1c/d 使事件随本次提交入库」的前提不成立" |

> E1/E2/E6 为 `[实测]` 判据的核心证据；E3–E5/E7/E10/E11 为读码判据。全部命令为只读，无 `git add/commit/checkout/restore/reset/stash/clean`。

---

## 2. 架构问题（阻塞级）

### B1（BLOCKER，源自 G5）— `gate_commands.P5_r6_differential` 指向不存在的脚本，且该脚本无交付归属

- **证据（可复现）**：
  - `glob docs/design-notes/*.sh` → 仅 `repro-tag0050.sh`；`docs/design-notes/r6-differential.sh` **不存在**（E1）。
  - `P2-design.md:234` 声明 `P5_r6_differential: "bash docs/design-notes/r6-differential.sh ."`。
  - `P2-design.md:257` 自认"依赖一个**待建脚本**"；`§10 G5` 亦承认"仓库内无现成可复用脚本"。
  - 该脚本**未被任何批次登记为交付物**：§1.1（A1 改动落点）、§3（批 ↔ BDD 对应）、§4（批次设计）、§7（files_to_read）均未列入。
- **后果**：`gate_commands` 在 P2 固化、**P4–P6 不可改**（P2 卡「下游影响」）。P5 执行到该 key 时 `bash: docs/design-notes/r6-differential.sh: No such file or directory` → 非零退出 → P5 必红，且无合法修复窗口。
- **裁决（可执行，二选一，须在 P2 定稿）**：
  - **（首选）批 A1 落地该脚本**：把 `docs/design-notes/r6-differential.sh` 写入 §1.1 的 **A1 改动落点** 与 §7 `files_to_read`；在 §3 的 BDD-22/74 明确指向它；并确保其**先于 TAG0050 的 P5** 产出（A1 是 TAG0050 的交付批，天然满足）。保留 `P5_r6_differential` 命令。
    - 理由：R6 双向差分是设计 §8 的**每批硬要求**（BDD-22/74），可复用脚本是"单一源 + 改坏即红"的唯一机械化途径；`repro-tag0050.sh` 已示范"`mktemp -d` 副本内运行、不写真实仓库"的形态（`repro-tag0050.sh:6,10`）。
  - **（次选）移除该命令**：从 `gate_commands` 删除 `P5_r6_differential` 与其 `_timeout_seconds`，把 R6 改为**各批 P4/P8 的过程性验收 checklist**（每批独立 PR 本就自带 P2/gate）。适用于判定"任务级 P5 不是 R6 的正确归属"。
- **不接受**：保留一条明知不可执行的命令并寄望实现期补脚本——这正是 P2 卡「gate_commands 固化后不可改」要防的情形。

---

## 3. 架构问题（非阻塞）

### M1（MAJOR，源自 G3 / RM-AG0100）— 设计 §2.7 的"随本次提交入库"前提已被证伪，A3 的 BDD-38 依赖它

- **事实**：`roadmap.md:99`（RM-AG0100，2026-10-06 探针实测）记："`pre-commit-gate.py` 2h.1d 的 `git add` 在**真实 `git commit`** 中不生效 → committed ledger 落后一次提交"。而 `design §2.7` 与 `P2-design.md:301` 的 A3 改动**正是依赖"2h.1c/d 使事件随本次提交入库"这一前提**。
- **与 BDD 的冲突**：A3 的 `BDD-38` Then 写"账本写入 `state_transition`（**随本次提交入库**）"——在 RM-AG0100 未修时**不可满足**。
- **裁决**：**纳入 A3**（不建议排除）。理由：A3 本就编辑 `2h.1c`/`2h.1d` 这两行，是唯一自然落点；RM-AG0100 的锚（"真实 `git commit` 后 committed ledger 含本 hook 追加的事件"）与 BDD-38 同判据。
- **要求**：§3/§4 的依赖链当前只记了"D 依赖 agate-run 基线 hotfix"，应**对称补记" A3 依赖 RM-AG0100 修复"**；BDD-38 的 Then 锚定到 RM-AG0100 的锚。若选择排除，则必须同时**订正 §2.7 与 BDD-38 的措辞**（去掉"随本次提交入库"的绝对承诺），否则留下一条永假判据。

### M2（MAJOR，源自 G4 / RM-AG0101）— `check-state-transition.py` 的 BDD-3 关键词扫描误伤注入卡片，与 T1 排除面同族但无归属

- **事实**：`roadmap.md:100`（RM-AG0101）记：`_scan_bdd3_keyword_phases()`（`:182`）扫描 `P{n}-progress*.md` / `P{n}-dispatch-context-*.md` 找关键词 `("空返回","重派")`，命中 `agate-inject-card.py` 注入的 **P1 卡正文**（含"…重派 requirements-review…"）→ **每个注入 P1 卡的任务都误报**（TAG0050 自身 P1 commit 即触发）。
- **与设计的同族性**：设计 §3.6 的 T1 绊线**已确立"排除 `AGATE_CARD` 块"**的原则；G4 是同一原则在另一处（`check-state-transition.py`）的缺失。
- **裁决**：**纳入**，且**指定单一 owner**。A1（legacy 重开判 ERROR）与 A3（抽 `check_transition` 纯函数）都编辑 `check-state-transition.py`，把"扫描排除 `<!-- AGATE_CARD_START -->…<!-- AGATE_CARD_END -->` 块 + 回归用例"并入其一（建议 A3，因其重构该文件）。**不接受双 owner**（一个事实两个源 = 本任务要根除的模式）。

### N1–N7（MINOR，不阻塞，建议在对应批的 P1 或 P2 定稿时消化）

- **N1（G2）**：`BDD-75` 写"用例计数一致（下界 749）"，而 `count-tests.sh` 实测 2671、749 是 TAG0011 迁移下界。P2 的双口径解释合理，但 **P1 是活基线**，建议在 P1 澄清措辞（"计数 ≥ 下界且与基线一致"），避免 P3/P5 各解各的。
- **N2（fitness 命令的可追溯性）**：`P5_fitness_snapshot_freeze` / `_golden_fixture` / `_schema_single_source` 分别对应 BDD-15 / BDD-16 / BDD-50，但 §6 未写明映射。建议补一行；并提醒 `pytest -k <pattern>` 在**零匹配时 exit 5**（非零）——P3 必须保证这三个测试名与 `-k` 模式一致。
- **N3（P5 全量超时）**：`P5_timeout_seconds: 600` 对 2671 用例且未带 `-n auto` 可能偏紧（AGENTS.md「测试约定」建议分片 + 并行）。建议按分片口径声明，或注明实际执行方式。
- **N4（§8 漏承 `executor_env`）**：P0-brief 的 `executor_env.platform=opencode` 未在 §8 延续；建议补入（P1 §0 已更新该值）。
- **N5（§9 minimal_validation 口径）**：§9 声明"纯代码逻辑，无外部系统依赖"，但本任务的**可信锚点是 CI 逐提交回放**（依赖 git/CI 外部行为）。§9 应显式引用 R4 的回放实测（16 提交/约 15s）作为外部行为的验证，而非一句"无外部依赖"带过。
- **N6（G7）**：`dispatch_plan` 不在 `agate-md-field-set` 白名单 → 手工写 frontmatter。记录即可，但注意这与本任务"agent 声明只经工具写入"的原则有张力（`dispatch_plan` 属架构声明，可辩护）。
- **N7（登记面 ⑤）**：§1.4 ⑤ 建议在对应批补 `agate/tests/README.md` 映射行——须遵守该文件"**不写用例数**"的既有约束（README 已明示），补行时勿带数字。

---

## 4. 测试缺口

1. **`P5_r6_differential` 无脚本、故无测试**：若按 B1 首选落地脚本，需配"改坏即红"的负向用例（如人为放宽差分口径 → 脚本应报红）。
2. **fitness 命令的测试名无 BDD 锚**：`task_data_freeze` / `task_data_golden` / `schema_single_source` 三个 `-k` 模式必须在 P3 显式落成测试节点名（否则 P5 得 exit 5）。建议在 §3 表内标注对应 BDD-15/16/50。
3. **RM-AG0100 的新用例缺失**：M1 落地时须先加失败用例（"真实 `git commit` 后 committed ledger 含本 hook 事件"）确认红，再修 `2h.1d`。
4. **RM-AG0101 的回归用例缺失**：M2 落地时须加"仅卡片块内出现『重派』不触发 / `P*-progress.md` 真实『重派』仍触发"两向用例。

---

## 5. §10 design_gap G1–G7 裁决表

| gap | P2 的建议去向 | 评审裁决 | 阻塞? |
|---|---|---|---|
| **G1** | A0 把**所有 phase**（含 P7/P5）统一为 rc=1 | **采纳**。E6 读码证实 P7→0/P5→2/其余→1。要求：修复放在 `check-gate.py` `main()` 的**单点早检**（`if not os.path.isdir(task_dir): return 1`），置于 `handlers.get(phase)` 分派**之前**，以保证逐 phase 一致（含 P0/P6.5/未知 phase）。BDD-02 的充分落点成立 | 否 |
| **G2** | P3/P5 用"计数一致 + 下界 749 不被击穿"双口径 | **采纳**（见 N1）；建议 P1 澄清措辞 | 否 |
| **G3** | 交裁决（纳入 A1/A3 或排除并单独登记） | **纳入 A3**（见 M1）：RM-AG0100 证伪了 §2.7 的前提，BDD-38 依赖它；补记依赖 + 锚 | 否（MAJOR） |
| **G4** | 交裁决（纳入或排除） | **纳入**（见 M2），单一 owner（建议 A3）；与 T1 的 `AGATE_CARD` 排除面同源 | 否（MAJOR） |
| **G5** | 交裁决（A1 落地脚本 或 改过程性验收） | **BLOCKER**：脚本不存在且无交付归属 → `P5_r6_differential` 必红。二选一，须在 P2 定稿（见 B1） | **是** |
| **G6** | A2 取 required 许可；D 依赖 agate-run hotfix | **采纳**。D 的前置已在 §3/§4 记；A2 许可属流程项，正确 | 否 |
| **G7** | 记录即可（dispatch_plan/agent 工具拒写） | **采纳**（见 N6） | 否 |

---

## 6. 七项重点核验逐项结论

1. **G1–G7 裁决**：见 §5。核心两项（G5 阻塞、G3/G4 纳入）已给可执行结论。
2. **`gate_commands` 可执行性与反模式**：一 key 一命令、无 `&&`、`--strict` 不在链路中 → **符合**；脚本类命令路径核验通过（E8）；`{key}_timeout_seconds` 覆盖各长命令（P5=600 / r6=600 / repro=300）→ 合理。**唯一不可执行项 = `P5_r6_differential`（B1）**。
3. **影响面 §1**：Modify / Not Modify / Risk 三部分齐全且**写在候选之前**（§1 在 §2 之前）；落点到"文件:函数/小节"；§1.4 登记面**有机械依据**（E7）且 P1/P2 两次探针实测记录一致。→ **通过**。
4. **BDD 逐批对应 §3**：77 条无遗漏无重叠（E10）；批次依赖链（A0→A1→{A2,B}；A3/A4∥A1；B→C→{D,E,F}；D 依赖 agate-run hotfix）与 §4 一致；**缺 G3 的 RM-AG0100 依赖**（M1）。
5. **`files_to_read` §7**：仅列必要文件（约 21 个），未堆砌；设计 §11 的完整消费方清单由首行"核心设计依据"覆盖。→ **通过**（B1 首选落地时须补 r6 脚本）。
6. **`minimal_validation` §9 / `env_constraints` §8**：§9 满足 P2 卡要求（声明 + 理由 + 内部函数/数据转换）；§8 齐全并细化 P0（isolation_check / replay_protocol / e_tests）。**口径瑕疵**见 N4/N5。
7. **E1–E4 §11**：完成时点与判据与设计 §14/exp 一致（E1 批 B 前 / E2 批 D 前 / E3 批 B 启用 ERROR 前 / E4 批 A2 后复测）。→ **通过**。

---

## 7. 锁定决策（本次评审后确定）

1. **`gate_commands` 不得引用 P2 定稿时不存在的文件**：G5 按 B1 首选（A1 落地 `docs/design-notes/r6-differential.sh` 并登记为交付物 + BDD 锚）或次选（移除命令、R6 转过程性验收）二者之一收口。
2. **G3 纳入 A3、G4 纳入（建议 A3）**：各带失败用例先红、单一 owner、依赖链补记。
3. **G1 修复位置锁定为 `check-gate.py` `main()` 单点早检**（分派前），保证逐 phase 一致。
4. **已确认无阻塞的既有判断**：3 候选 + 权衡（v0.6 多方案探索达标）、影响面写在候选前、一 key 一命令、登记面实测结论、77 BDD 逐批映射。

---

## 8. 只读纪律声明

本评审全程**未执行任何破坏性/写仓命令**（无 `git add/commit/checkout/restore/reset/stash/clean/switch -f`），**未编辑/删除被评审文件**。所有核验均为读操作：`glob`、`grep`、`read`、`test -x`、`command -v`，以及 `check-protocol-consistency.py --strict-errors-only`（纯读、无写副作用）。本评审仅新增两份**自身产出**：`P2-review-eng.md`（本文件）与 `P2-progress.md` 的 progress 追加。

[PROD_NOT_TOUCHED] 本评审仅在 agateon 本 checkout 上做只读核验，未接触生产环境。
