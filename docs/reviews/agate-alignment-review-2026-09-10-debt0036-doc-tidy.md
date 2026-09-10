---
review_date: 2026-09-10
reviewer: protocol-alignment-review
change_summary: DEBT0036 关闭（platform-notes.md Codex 章 3 处「未测/待复核」措辞收敛为「P6 V7 两次实测 depth=2 可用、max_depth=1 结论已推翻」）+ phases.yaml 注释脆弱行号引用改节名/函数分支名 + AGENTS.md 版本示例泛化 + tech-debt.md DEBT0036 status open→closed
files_changed: [agate/platform-notes.md, agate/rules/phases.yaml, agate/AGENTS.md, agate-workspace/debt/tech-debt.md]
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 / 意图 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED-WITH-NITS |
| A4 | 数值/规则 + 测试覆盖 | ALIGNED |
| A5 | 下游影响 + DEBT 闭环 schema | ALIGNED |
| A6 | 锚点表 / consistency CHECK 覆盖 | ALIGNED |
| A7 | 设计原则一致性（ADR） | ALIGNED |

**总结论：`aligned-with-nits`** — 变更本体（DEBT 闭环 + cosmetic）范围正确、内部自洽，所有机械 gate 全绿。唯一 NIT 是 A3b 反向传播发现 `agate/loop-orchestration.md:228` 仍携带「Codex max_depth 默认 1」的事实性括注，与新措辞字面不一致——非阻塞（该处核心论点是 agate 自设的浅树约定，且在 DEBT0036 登记范围外），建议后续小项处理。

---

## 逐项审查

### A1: 意图 / 文档→脚本对齐

**判定问题**：本次改动是否仅为 (a) 关闭已核实的 DEBT、把滞后措辞收敛到真实实测结果，(b) cosmetic 注释/示例泛化？`phases.yaml` 是否 comments-only？

**platform-notes.md（3 处，均在 `## Codex` 章 + Hardening-roadmap 节）**：
- 子代理派发小节：`嵌套深度…未测（归 P6 V7）` → `P6 V7 已两次独立实测 depth=2 可用（TAG0033，2026-09；source.subagent.thread_spawn.depth == 2 的孙会话）`
- 真机验证清单表行：`V7 / V2：归 P6` → `V7：嵌套 depth=2 实测可用；V2：跨 9 次真实调用键并集实测（P6 PASS，TAG0033）| P6 ✅`
- Hardening-roadmap 节时效指针（行 153）：`嵌套深度未测待复核` → `嵌套深度经 P6 V7 复核实测 depth=2 可用——max_depth=1 结论已推翻`

`max_depth=1` **事实行**（platform-notes.md:148）与 `multi_agent` flag 交叉引用结构均保留，符合任务说明与 BDD-25 判据。测试事实核对：TAG0033 P6-evidence/real-machine-p6.md §V7 finding、P7-consistency.md §6-A（deviation_count:1 WARNING）均记录 P6 V7 重做 attempt 2 + archived 首轮 V7 两次独立观测 `depth == 2` 孙会话 —— 新措辞与实测一致。

**phases.yaml（comments-only 确认）**：`git diff` 逐行核对，仅 `#` 注释行变化：
- L6 `WORKFLOW.md…（287-299 行）` → `WORKFLOW.md「P1-P8 阶段总览」表（S-1/S-2 锚点）`
- L15-16 `gate_p0 L577 / p1 L698 / p2 L883 / …return 2` → `check-gate.py 的 gate_p0/p1/p2/p3/p5/p6/p8 分支 return 2 实证`；`p4 L990 / p7 L1241 / p65 L1110/1120 return 0` → `gate_p4/p7/p65 分支 return 0`

无 `schema_version` / `phases:` body 改动，无 `retry_cap` / `next` / `retreat` / `gate_pass_exit` / `name` / `exec_role` / `task_fields` 变化。

**AGENTS.md**：`agate-install.py v0.48.0 / v0.43.0` → `vX.Y.Z`，纯示例泛化，无语义。

**结论**：ALIGNED — 仅 (a)+(b)，无任何语义协议规则变更。

### A2: 脚本→文档对齐

本次无脚本（`*.py` / `*.sh`）改动。`platform-notes.md` / `phases.yaml` 注释的变更不引出任何脚本逻辑需同步。BDD-25 判据脚本 `test_codex_platform_docs.py::test_bdd_25_codex_chapter_cross_reference_no_contradiction` 断言 `"max_depth=1" in text`（事实行未删）+ `## Codex` 章含 `max_depth` / `multi_agent` 交叉引用 —— 新措辞保留全部三者，测试仍绿（见 A4）。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**A3a 连锁（已知衍生）**：
- DEBT0036 closure → `tech-debt.md` status/task_id/closed_at/evidence 已同步更新（见 A5）。✓
- platform-notes.md 3 处措辞是同一维度的时效口径，本次一并收敛，无遗漏的同文件对立陈述（BDD-25 `test_bdd_25` 绿）。✓
- `CHANGELOG.md` 未更新 —— 本次无协议语义变更（DEBT 闭环 + cosmetic），不属 A5「语义变更未标注」，无需 CHANGELOG 条目。✓

**A3b 反向传播（主动推断「应被影响但不在 diff」的文件）** —— grep `max_depth` / `spawn_agent` / `嵌套` / `depth=`（排除 `archived/`、`.archived`、`agate-workspace/tasks/`）：

| 命中文件 | 内容 | 判定 |
|---|---|---|
| `agate/platform-notes.md:148` | `Codex 兼容性：Codex subagent max_depth=1 …` | **保留的事实行**，行 153 时效指针本次已更新指向 `## Codex` 章。这是任务明确要求保留的交叉引用结构，非未标时效对立陈述。ALIGNED |
| `agate/WORKFLOW.md` / `LIMITATIONS.md` / `dispatch-protocol.md` / `role-system.md` / `state-machine.md` | `max_depth` **0 命中**；`spawn_agent` 仅 WORKFLOW.md:161（DSH 平台描述，与 Codex 深度无关） | 无传播需求。ALIGNED |
| `agate/loop-orchestration.md:227-228` | `3. 嵌套深度约定（避免撞 max_depth）… 不依赖 L2（Codex max_depth 默认 1，禁止深层嵌套）` | **NIT** —— 「Codex max_depth 默认 1」作为约定的事实性括注，现被 V7 实测（depth=2 可用）超越。核心论点（v4 层级约定 L0→L1、复杂就拆任务而非嵌 agent）是 agate 自设的浅树设计策略，与 Codex 是否技术上支持 depth 2 无关，仍成立。且此处不在 DEBT0036（retrospective 登记、明确限定 platform-notes.md Codex 章 3 处）的范围内。建议后续以一行时效指针软化（如「早期记录 max_depth=1；实测 depth=2 可用，但约定仍保持浅树」），可折入 RM-AG0034 或新登一条 low DEBT。**不计入本次需修复项。** |
| `agate-workspace/roadmap/roadmap.md:32`（RM-AG0034） | `接入前需实机复核 Codex subagent max_depth 旧记录与沙箱默认值` | backlog 条目描述；「接入前实机复核」对完整平台接入仍是合理建议（V7 只测了 depth=2 单点）。非对立陈述。ALIGNED |
| `docs/research/cross-platform-dispatch-mechanics.md:131`、`docs/design-notes/platform-extension-research.md`（结论六 / 2.1 / 3 节等） | 早期调研快照，均自带 `[本轮未测]` / `需实机验证` / `需复核` 时效标记 | 带日期的调研 artifact，非协议权威源，自我声明为待复核。不判 MISALIGNED，仅记录。 |

**已知偏离来源核查（原则 6）**：`loop-orchestration.md` 的 max_depth 括注不对应任何 TAG0033 P7 的 `[DESIGN_GAP_REVIEWED:]` 记录（TAG0033 §6-A 只覆盖 platform-notes.md 本身的措辞，deviation_count:1，已由本次 closure 消化）。故按普通 NIT 记录，等级为非阻塞。

**结论**：ALIGNED-WITH-NITS —— 权威协议文档（WORKFLOW / LIMITATIONS / dispatch-protocol / state-machine / role-system）无一命中，platform-notes.md 内部自洽；唯 `loop-orchestration.md:228` 一处非权威、范围外的事实括注滞后，非阻塞。

### A4: 数值/规则 + 测试覆盖

**phases.yaml 注释去行号后仍描述正确事实** —— 逐条核对 YAML body（body 未改）：
- 「阶段集与名称 = WORKFLOW.md「P1-P8 阶段总览」表（S-1/S-2 锚点）」：WORKFLOW.md:309 `## P1-P8 阶段总览` heading + :330 `S1S2-ANCHOR-END` 锚点标记存在，引用准确。
- 「retry_cap 与 agate_common.MAX_RETRY_MAP 一致（P8=2/P6.5=2 等）」：body 中 P8 `retry_cap: 2`、P6.5 `retry_cap: 2`，一致。
- 「exit 2 是 P0-P3/P5/P6/P8 的通过码（gate_p0/p1/p2/p3/p5/p6/p8 分支 return 2）」：body `gate_pass_exit` 值 —— P0=2 P1=2 P2=2 P3=2 P5=2 P6=2 P8=2；`exit 0 是 P4/P7/P6.5（gate_p4/p7/p65 分支 return 0）`：P4=0 P7=0 P6.5=0。**完全吻合**。
- 函数分支名真实性：`check-gate.py` 有 `def gate_p0/gate_p1/gate_p2/gate_p3/gate_p4/gate_p5/gate_p6/gate_p65/gate_p7/gate_p8`（grep 确认 10 个），新注释用的分支名均存在。
- 附带收益：被删的旧行号（`WORKFLOW.md 287-299`、`gate_p0 L577`）本身已漂移失真（阶段总览现在 L309、gate_p0 现在 L599），泛化是净修正。

**测试覆盖（附实跑输出）**：
```
$ timeout 200 python3 -m pytest agate/tests/unit/test_codex_platform_docs.py agate/tests/unit/test_check_structure_consistency.py -n auto -q
.........................                                                 [100%]
25 passed in 0.97s
```
`test_bdd_25_codex_chapter_cross_reference_no_contradiction`（test_codex_platform_docs.py:98）在内，8 个 codex docs 用例 + 17 个 structure-consistency 用例全绿。

**结论**：ALIGNED。

### A5: 下游影响 + DEBT 闭环 schema

**gate 行为影响**：无 —— 无脚本改动，phases.yaml body 未动，不影响任何已有项目的 gate 判定。

**DEBT0036 closed-entry schema**（`check-debt.py`）：
```
$ python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md
exit=0
```
条目现状：`status: closed` / `task_id: TAG0033`（非 null）/ `closed_at: 2026-09-10` / 新增 evidence 行 `ref: "chore/debt0036-and-doc-tidy"` note 含 `TAG0033` + `P6 V7` + `test_codex_platform_docs.py::test_bdd_25` + `check-protocol-consistency.py --strict-errors-only 0 ERROR`。closure_criteria 3 条与实际执行结果对应（措辞收敛 / test_bdd_25 绿 / 0 ERROR）。校验器 fail-closed 薄壳 exit 0 → schema 合规。

**文档传播**：DEBT closure 不触发 orchestrator-template / dispatch-protocol / 角色文件同步需求（见 A3）。

**结论**：ALIGNED。

### A6: 锚点表 / consistency CHECK 覆盖

**check-protocol-consistency.py --strict-errors-only**：
```
CHECK 1/3/4/6/7/8/9/11/12/13/14/15 PASS；CHECK 2/10 WARN
仅有 364 个 WARNING，无 ERROR。   exit=0
```
- CHECK 3（协议文件硬编码行号 `xxx.md L\d+`）：只扫 `.md` 协议文件，不扫 `rules/*.yaml`；旧 phases.yaml 注释用「287-299 行」/「gate_p0 L577」形态本就不在其正则命中面 —— 去行号是自愿 tidy，非 CHECK 3 强制。改后 CHECK 3 仍 0 命中。
- CHECK 15（数据面 `rules/*.yaml` 含注释的平台名扫描）：phases.yaml 注释变更未引入任何平台名（`Codex` 等），CHECK 15 PASS。
- CHECK 9（协议-脚本结构对齐锚点表）：无新增协议规则，无需更新锚点表。

**check-structure-consistency.py**：
```
S1-phases: OK / S2-workflow: OK / S3-cards: OK / S4-scripts: OK / S5-schema: OK / S6-references: OK / S0-numbers: OK   exit=0
```
S-1/S-2（phases.yaml ↔ WORKFLOW.md 阶段总览表双向）OK —— 确认 phases.yaml body 未动、注释变更不影响结构对齐。

**结论**：ALIGNED —— 注释文本对所有 CHECK 无影响，0 ERROR。

### A7: 设计原则一致性（ADR）

`agate/adr.md` grep `subagent` / `depth` / `Codex` / `spawn` —— 无任何 ADR 涉及 Codex 子代理嵌套深度或平台适配措辞。本次为 DEBT 闭环 + cosmetic，无架构决策，无需新增 ADR。

**结论**：ALIGNED。

---

## 需人工确认 / 需修复项

- **MISALIGNED**：无。
- **NEEDS_HUMAN_REVIEW**：无。
- **NIT（非阻塞，可 commit，建议后续处理）**：`agate/loop-orchestration.md:228` 「Codex max_depth 默认 1」事实括注滞后于 V7 实测（depth=2 可用）。在 DEBT0036 登记范围外，且该处约定的设计论点独立成立。建议折入 RM-AG0034 或新登一条 low DEBT，加一行时效指针。

## 机械 backstop 汇总

| 检查 | 结果 |
|---|---|
| `check-protocol-consistency.py --strict-errors-only` | 0 ERROR（364 WARN，全为既有叙事文件引用漂移，与本次无关）exit=0 |
| `check-structure-consistency.py` | S-1~S-6 + S-0 全 OK，exit=0 |
| `check-debt.py agate-workspace/debt/tech-debt.md` | exit=0 |
| `pytest test_codex_platform_docs.py test_check_structure_consistency.py -n auto -q` | 25 passed in 0.97s（含 test_bdd_25） |
