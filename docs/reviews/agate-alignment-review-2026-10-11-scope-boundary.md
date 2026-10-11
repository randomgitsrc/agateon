---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: 新增 AGENTS.md「变更分诊：agateon 管什么、不管什么」节并按该原则清理（删 DEBT0075 + 4 条「产品方向·无当前需求驱动」RM：RM-AG0033/0034/0036/0047 及其 live 引用）；另修 OpenCode v2 下 SETUP 验证命令失效的真问题（SETUP.md + 对应测试版本健壮化）。
files_changed: [AGENTS.md, CHANGELOG.md, SELF-GATE.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/SETUP.md, agate/tests/unit/test_setup_agate_dir.py, agate/tests/unit/test_tag0051_self_gate.py, docs/design-notes/README.md, docs/design-notes/platform-extension-research.md]
---

# 协议-脚本对齐审查（单议题：变更分诊规则 + scope 清理 + SETUP v2 真问题）

**最终结论：APPROVED**。上轮判定的 2 项 MISALIGNED 与 3 项 NEEDS_HUMAN_REVIEW **全部逐条实测闭合**；
本轮并入审查的 SETUP/test 两文件**如实、可执行、无过度声称**。仅余 3 条**非阻塞提示**（均为「呈现/记录」级，
按本节自身「三问 §2：只改呈现 ⇒ 不管」的口径可不改），列于文末。

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（新节为判断类原则；SETUP 节 ↔ 测试断言同步） |
| A2 | 脚本→文档对齐 | ALIGNED（SETUP 验证路径 ↔ 测试 has_v1/has_v2 + v2 文件级分支一致） |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（4 RM 的 live 引用 = 0；仅余 2 处同文件措辞陈旧，非阻塞） |
| A4 | 测试覆盖 | ALIGNED（实跑：`test_setup_agate_dir.py` 7 passed；`test_tag0051_self_gate.py` 15 passed） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（**无既有用例转红**；反向：原恒红的 `test_bdd_43` 现转绿） |
| A5 | 下游影响 + 文档传播 | ALIGNED（gate 行为无变化；SETUP 为面向用户的真修复） |
| A6 | 锚点表覆盖 | ALIGNED（无新增协议规则/脚本；consistency rc=0） |
| A7 | 设计原则一致性 | ALIGNED（与 ADR-003/ADR-005 不冲突） |
| A8 | 声称-命令绑定 | ALIGNED（"v2 移除 debug agent" / "tools.task 非模板字段" 均实测绑命令；无据数字已删） |

---

## 一、上轮 5 项的处置核验（逐条实测）

### M1（删 RM-AG0034 却漏清活文档自引用）→ **已闭合 ✓**
- `docs/design-notes/platform-extension-research.md` grep `RM-AG0033/0034/0036/0047` = **0**（实测）。
- 6 处改为中性表述：标题「（第四运行时扩展素材）」、调研目标「…提供素材。**未排期**（无当前需求驱动；仅当出现真实需求 / 首个用例时再评估）」、两处「**对该扩展的含义**」、4.3 节标题「**对本扩展交付物**的落点建议」、补充建议「建议**在本扩展内**…」。
- **无过度声称**：措辞为「未排期 / 待需求驱动」，与所删 RM 的 triage 原意一致。

### M2（RM-AG0036 同处置却留而不删）→ **已闭合 ✓**
- `roadmap.md` RM-AG0036 行**已删**；同文件 `RM-AG0022`（done）行内活引用同步清理（「RM-AG0031 写时校验依赖本条目」，去掉「与 RM-AG0036 双语锚点」）——diff 实核一致。
- 复核判据仍成立：新节例外条款「有明确触发条件的等驱动项，**允许**以一行保留」是**许可**而非义务 ⇒ **一并删除与规则不矛盾**（上轮的"双标"已消除）。
- live 残留仅存冻结面：`agate-workspace/tasks/TAG0021-structured-layer/{P0-brief,P1-requirements}.md`（历史任务记录）+ 本评审报告；**非活引用**。

### N1（roadmap「范围」节与 AGENTS 双权威）→ **已闭合 ✓**
- `roadmap.md`「范围」节前新增指路行：「通则（边界判定：什么归 agateon 管、什么不进本仓）见 `AGENTS.md`「变更分诊」节；本节只列**本项目当前**的具体取舍。」⇒ 单一权威（通则 vs 本项目取舍），职责清晰。

### N2（AGENTS 重述 hotfix 规则却漏条件 2）→ **已闭合 ✓**
- 现为指路：「能 hotfix 就 hotfix —— 走**哪条通道**以「改动通道」节的 **hotfix 三条件**为准（本节不重述条件，避免两份口径漂移）；不满足条件则立项走 P0–P8。」⇒ 消除第二份口径。

### N3（先例归因措辞）→ **已闭合 ✓**
- 现为「（实证：DEBT0073 定下口径后，其**构造性边界残差**被登记成 DEBT0075，差点又走一轮实现 + 评审 —— 零用户价值）」⇒ 去掉未验证的「两轮评审 + PR」数字，措辞与事实相符（DEBT0075 为「构造性边界」已由上轮 `git log` 全量探针证成：2131 commits 中双留痕并存 = 0、非行首仅文档正文）。

---

## 二、并入本轮的两个并发文件（SETUP / 测试）——如实、可执行

**背景真问题**：`agate/SETUP.md` 让用户跑 `opencode debug agent orchestrator` 验证注册，而 **OpenCode v2 已移除该子命令** ⇒ v2 用户按文档验证**必然失败**，且对应测试在本机（v2）**恒红**。

### 事实核验（我自跑）
| 声称 | 命令 | 结论 |
|---|---|---|
| "OpenCode v2 起 `debug agent <name>` 已移除（`debug` 只剩 `agents`/`config`/`paths`）" | `opencode --version` → **v2.0.23**；`opencode debug --help` → SUBCOMMANDS = **agents / config / paths** | **属实 ✓** |
| "`tools.task` **不是**模板声明的字段" | `agate/orchestrator-template.md` frontmatter = `name: orchestrator` / `mode: primary` / **无 `tools:` 块**（grep 实测） | **属实 ✓** |
| "`opencode debug agents` 不保证列出项目级自定义 agent" | 探针：建 `.opencode/agents/orchestrator.md` 后 `opencode debug agents` → **未列出** orchestrator | **属实 ✓**（软措辞，安全） |
| 测试"版本健壮" | 我自跑 `pytest agate/tests/unit/test_setup_agate_dir.py` → **7 passed**；`::test_bdd_43` → 1 passed（本机 v2） | **属实 ✓** |

### 是否与议题自洽（AGENTS 三问）
① 有真实使用面 ✓（v2 用户 + 本机恒红测试）；② 改变判定 ✓（测试红→绿 + 文档验证路径）；③ 本仓可解 ✓（`agate/SETUP.md` + `agate/tests/` 均在本仓）。**三问全过。**

### 有无过度声称 / 断言是否只断言平台能证的事
- **无过度声称**：SETUP v2 明确「**以文件为准**」并诚实标注「`tools.task`…v2 无对应空跑校验——如需确认 v2 下 `task` 可用，最可靠的方式是**实际派发一次 subagent**」。
- **测试 v2 分支只断可证之事**：`debug agents` rc==0（证明 CLI 可用）+ **文件级**断言 `name: orchestrator` / `mode: primary`（模板确有）；**不再断言** v2 不可证的 `tools.task`。测试注释亦如实说明「v1 回报的是平台解析后生效 tools…v2 只能做文件级断言，不对平台解析结果过度声称」。✓
- **块序未破坏既有断言**：SETUP OpenCode 节首块仍是注册块（`mkdir`/`ln`），`_bash_blocks(sec)[0]` 语义不变 ⇒ `run.returncode == 0` 断言不受新 v2 块影响（实测 7 passed 佐证）。

---

## 三、逐项审查

### A1 文档→脚本对齐 — ALIGNED
新节是**判断类原则**（管辖边界），非机器判据；位于根 `AGENTS.md`（非协议目录），不引入需脚本实现的规则。SETUP 验证路径与测试断言同步。无脚本义务。

### A2 脚本→文档对齐 — ALIGNED
测试对 SETUP 的断言 `has_v1 or has_v2` 与其内容一致；v2 分支执行的 `debug agents` + 文件级断言与 SETUP v2 段一一对应。

### A3 一致性连锁 + 反向传播 — ALIGNED
- **A3a（连锁）**：DEBT0075、RM-AG0033/0034/0036/0047 在 CHANGELOG / SELF-GATE / test 注释 / tech-debt / roadmap / design-notes（README + 正文）内**清理一致**，保留「非穷尽证明」事实限定。
- **A3b（反向传播）**：live 文档中 4 RM 残留 = **0**（`grep` 排除 `.git`/`.worktrees`/`tasks/`/`docs/reviews/` 后为空）。仅余 2 处**同文件措辞/记录**陈旧（`SETUP.md:168` 类比、`tech-debt.md:642` 旧环境失败记录），见文末非阻塞提示。
- roadmap 无计数行 ⇒ 删 4 行无需同步表头；`^| RM-` 实测 **108**。

### A4 测试覆盖 — ALIGNED
本 reviewer 实跑：
```
python3 -m pytest agate/tests/unit/test_setup_agate_dir.py -q        → 7 passed in 1.74s
python3 -m pytest agate/tests/unit/test_tag0051_self_gate.py -q     → 15 passed in 0.72s
```
（主 Agent 另跑全量 = 3007 passed / 2 skipped；本 reviewer 未复跑全量，按要求仅跑相关面。）

### A4b 闭合后既有测试转红 + 夹具更新清单 — ALIGNED
**经实测无既有用例转红**（空清单）。反向：此前本机 v2 恒红的 `test_bdd_43_opencode_registration_and_debug_agent` **现转绿**（我的实跑 1 passed）。无需更新夹具。

### A5 下游影响 + 文档传播 — ALIGNED
- **gate 行为无变化**：被删 RM 无 task_id（不触 `check-gate.py::_check_roadmap_done`）；SETUP 为文档修正，不改协议语义。
- SETUP 为**面向用户**的真修复（v2 用户不再被误导）；测试从恒红转绿，消除了一条被多次登记为「预存环境失败」的噪声（`TAG0042/TAG0050/TAG0051` 的 known-failures）。
- 可选：CHANGELOG `[Unreleased]` 未为 SETUP v2 修复加行（非协议语义，见非阻塞提示）。

### A6 锚点表覆盖 — ALIGNED
无新增协议规则/脚本，不触 CHECK 9/10 锚点。我自跑 `check-protocol-consistency.py` → **0 ERROR**（433 frozen WARNING 属设计）。

### A7 设计原则一致性 — ALIGNED
新节与 `agate/adr.md` 相邻决策 **ADR-003（最小约定/不绑定技术栈）** 与 **ADR-005（改动性质决定流程）** 分属不同轴、无冲突；SETUP 的 v1/v2 分支是平台适配文档的正当形态。未发现未记录的架构决策。

### A8 声称-命令绑定 — ALIGNED
| 声称 | 命令 | 结论 |
|---|---|---|
| "真实提交从未出现"（构造性边界） | `git log --all` 全量 2131 commits：双留痕并存 = 0；非行首仅文档正文 | 成立（上轮已证） |
| "OpenCode v2 移除 `debug agent <name>`" | `opencode --version`=v2.0.23 + `opencode debug --help` | 成立（本轮实测） |
| "`tools.task` 非模板声明字段" | `orchestrator-template.md` 无 `tools:` 块 | 成立（本轮实测） |
| "`debug agents` 不保证列出项目级 agent" | 探针复现未列出 | 成立（本轮实测） |
无据 / 未验证的数字类声称已删除（N3、CHANGELOG 3 类差异等）。

---

## 非阻塞提示（可不改；按本节「三问 §2：只改呈现 ⇒ 不管」口径）

1. **`agate/SETUP.md:168`（Claude Code 节）** 仍以「等价于 OpenCode `opencode debug agent <name>` 的空跑校验命令」作类比；该命令 v2 已移除 ⇒ 类比略陈旧（**纯呈现**，结论"用真实选中一次验证"仍成立）。
2. **`agate-workspace/debt/tech-debt.md:642`**（某 open 债的展开注）仍记「(4) 全量 pytest（本机 1 项环境失败——opencode CLI `debug agent` 子命令漂移）」——本批已修该失败 ⇒ 该记录变陈旧（**记录级**；未来关单者会重跑 pytest）。
3. **CHANGELOG `[Unreleased]`** 未为本批 SETUP v2 修复加行（可选；不属协议语义变更）。

> 三条均不改变任何 gate 判定，且按本节自身口径属"不管"级别；如追求 dispose 完整可顺手改，**不构成 commit 阻塞**。

## 尾注：只读纪律
本轮全程**只读**（未 `add/commit/checkout/stash/reset`，未外部写）；探针 `opencode debug agents` 只在 `/tmp/opencode/<一次性目录>` 内建/用/清（同一次 bash 调用内），`git log` 只读。被评审改动集未受影响。产出 = 本报告 + `.progress.md`。
