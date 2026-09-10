---
phase: P7
task_id: TAG0034
type: consistency
parent: P2-design.md
trace_id: TAG0034-P7-20260910
status: draft
created: 2026-09-10
agent: consistency-reviewer
blocker_count: 0
deviation_count: 1
deviation_critical_count: 0
design_gap_count: 4
design_gap_reviewed_count: 4
---

# P7 一致性交叉检查 — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060）

> 对照 P1–P6 产出做跨文件一致性审查。只审不写：本文件 + `P7-progress.md` 是唯一落盘，未改任何代码 / 测试 / 协议文档 / P1–P6 产出。
> 上游 commit：P1 `f75e129` / P2 `b851b1e` / P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` / P5 `2772891` / P6 `eb924be` / P6.5 `cb9dfb9`。核对基线 = `git diff f75e129..HEAD`。

`[PROD_NOT_TOUCHED]` —— 仅在 worktree `.worktrees/agate-TAG0034` 内读 + 跑 git / grep；主 checkout `/home/kity/oclab/agateon` 与 `~/.agate` 未写入。

---

## 1. DESIGN_GAP 配对（4 条，逐条转抄 + REVIEWED）

`grep -nE '^\[DESIGN_GAP' P4-implementation*.md` 命中 4 条 DESIGN_GAP + 3 条 DESIGN_GAP_REVIEWED（P4b 一条 REVIEWED 覆盖 G2+G3 两 gap）。逐条转抄并交叉核 REVIEWED 判断是否站得住。

[DESIGN_GAP: G1（P4-implementation.md:53）P4a 的 `_route_main` 只做 `resolve` + 输出「已解析路由计划」JSON（`form ∈ {default, chain}` / `chain` / 首候选 / `form: native|subprocess` / `dispatch_context`），不在 P4a 内跑端到端 try-and-fall；`dispatch_once` + 子进程 spawn 留给 P4b/M5。target JSON 契约字段的确切取值由 P4a 实现自主定。]

[DESIGN_GAP_REVIEWED: G1 —— REVIEWED 见 P4-implementation.md:55（主 Agent 2026-09-09）。跨文件核：与 P2-design §4.1「P4a 建 `route` 骨架 + JSON 输出契约 → P4b 加 subprocess 分支」批次意图逐条一致；与 P2-design §3.1 数据流 step 2.6「stdout 输出 target 描述 JSON」+ §3.5「`_route_main` 可 import helper，P4a 落地时定」一致。git diff 核实：`agate/scripts/agate_dispatch_route.py`（新 853 行，M4）+ `agate/scripts/agate-dispatch.py`（+108 行 `route` 子命令，M4b）已落地，P4b `agate-dispatch.py` `form == "chain"` 分支拆三路（首候选 native / 子进程 / DispatchContractError）在其上「只增不改」。判定：非隐性偏离，决策方向与 P2 §4.1 意图一致，REVIEWED 站得住。]

[DESIGN_GAP: G2（P4-implementation-P4b.md:53）P2-design §3.7 / M5 未指定 `_route_main` 端到端 try-and-fall 时「约定产出文件路径」如何解析。实现自主决定：`dispatch_once` 的 `expected_output` 由 `_route_main` 从环境变量 `AGATE_DISPATCH_EXPECT` 取，未设则为 `None`；`expected_output is None` 时 `produced_files` 恒空 → 子进程即便结构化输出成功也判 `NO_PARSEABLE_OUTPUT` 回落（保守侧）。]

[DESIGN_GAP_REVIEWED: G2 —— REVIEWED 见 P4-implementation-P4b.md:57（主 Agent 2026-09-10）。跨文件核：符合 P2-design §1.3 R1「收到 gate 能评产出才算成功」的保守侧 + §3.7「宁可回落也不把『无法核实产出』当成功」；与 §3.7 N7「presence 级骨架可解析」判据不冲突（`AGATE_DISPATCH_EXPECT` 未设即无可核实对象）。CI 不覆盖端到端路径（无 `dispatch-routing.yaml` → `form=default`），P4-implementation.md 自查记录与 P6-acceptance §4.13 BDD-40「`dispatch_route` 事件条数 = 0」一致。判定：P2 未定义留白、决策方向与 R1 一致，REVIEWED 站得住。]

[DESIGN_GAP: G3（P4-implementation-P4b.md:55）候选链中段（非首位）出现 `cli: native` 候选时，端到端 `try_and_fall` 里 `dispatch_once` 返回 `HAS_OUTPUT` 占位（= 交回驱动会话代发），等价「该候选即成功、停止回落」。P2-design 只明确了「首候选 native → `_route_main` 输出路由计划 JSON 即止」，未定义混合链的中段 native。]

[DESIGN_GAP_REVIEWED: G3 —— REVIEWED 见 P4-implementation-P4b.md:57（主 Agent 2026-09-10，同一条 REVIEWED 覆盖 G2+G3）。跨文件核：与 P2-design §3.4「`cli: native` 各平台执行 + 驱动会话代发」+ §9 修订要点 4「`cli: native` 弱缓解、自动化天花板是主 Agent 机械横传 model」一致；与 `agate/dispatch-protocol.md` 新节（M7）line 529「gate 判定只认产出文件 + exit code，不认谁生产的」+「弱缓解 vs 强缓解 + 自动化不对称」段一致。判定：native = 交驱动会话 = 有产出，符合弱缓解形式的自动化天花板定义，非偏离 P2 §3.4，REVIEWED 站得住。]

[DESIGN_GAP: G4（P4-implementation-P4c.md:49）tmux 包裹待目标环境验证 —— 本机 WSL2 + tmux 3.4 冒烟通过，但目标部署环境代表性未定（非容器 / CI runner / 纯物理机）。`_default_subprocess_run` 的 tmux 包裹接入用 feature flag `AGATE_DISPATCH_TMUX` 默认关，两个 helper（`build_subprocess_launch` / `tmux_cleanup_action`）为纯逻辑函数（测试转绿）。]

[DESIGN_GAP_REVIEWED: G4 —— REVIEWED 见 P4-implementation-P4c.md:51（主 Agent 2026-09-10）。跨文件核：与 P2-design §3.10「目标环境代表性存疑则停在『定稿 + 待落地验证』、不阻塞 P8」+ §1.3 R10 + P1-requirements.md §7「P4c 可整体切除」+ P0-brief「外部评审 W2」逐条一致；默认关使 P6-acceptance §4.13 BDD-39/40「不配置 = 逐字节现状」不受影响（P4-implementation-P4c.md 回归护栏 25 passed）。判定：feature flag 默认关是 §3.10 条款的落地形态，非切除、非偏离，REVIEWED 站得住。目标环境开启默认前复跑 research §10 tmux 验证项 —— 见 §7 结论「P8 收尾清单」。]

**小结**：`design_gap_count: 4` / `design_gap_reviewed_count: 4`。4 条 REVIEWED 的决策方向均与 P2 意图一致，无隐性偏离，无 `[DEVIATION-CRITICAL]`。

---

## 2. SCOPE+ 闭环

P1-requirements.md §1 两条 SCOPE+ 均反引号包裹、非纯行首（`check-scope-resolved.py` 当前 exit 0）。逐条核实闭环状态：

### 2.1 `[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]`

- **交付 = BDD-48 / BDD-49 / BDD-50**。P6-acceptance.md §4.17 三条逐条 PASS：BDD-48（`architect.md`「批次设计」节措辞，doc-assertions 命中 architect.md:209/225）、BDD-49（`dispatch-protocol.md`「派发编排机制」节 author vs 一致性验证区分，命中 dispatch-protocol.md:502/588）、BDD-50（`check-protocol-consistency.py --strict-errors-only` exit 0）。P6.5-judge-verdict.md `criteria_passed: 53` 覆盖同三条。
- **跨文件核实（git diff / grep，非读结论）**：`git diff f75e129..HEAD -- agate/assets/execution-roles/architect.md` = 仅 +2 行，在「批次设计（强制节，TAG0014）」节内新增一段「**补协议文档正文 = P4，不是 P7**（DEBT0039）」+ TAG0030 / TAG0033 复盘两先例指针，逐字对齐 P2-design §4.3 草稿①。`grep -nE '^### 0. 派发路由' agate/dispatch-protocol.md` → line 506（新子节存在），`grep '不认谁生产的|候选回落 ≠ 状态机 retry|gate FAIL 绝不换候选'` → dispatch-protocol.md:529/535/538 命中；「## 派发编排机制」节标题仍在 line 502。
- **frontmatter 回写**：P1 §8 明确「DEBT0039 工作尚未完成 → 不写入 frontmatter `scope_resolved`，由 P8 收尾回写」。当前 P1 frontmatter 无 `scope_resolved` 字段，与该声明一致。
- **结论**：已实质闭环（BDD-48/49/50 P6 PASS + 两处协议文档措辞已落地），frontmatter `scope_resolved` 回写 + DEBT0039 `status: closed` / `task_id: null → TAG0034` 留 P8。非 BLOCKER。

### 2.2 `[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4 — 2026-09-09]`

- **交付 = `agate/LIMITATIONS.md` 局限 2 缓解链段 + `agate/adr.md` ADR-013**，P1 §9「P8」行明确登记为 P8 交付项，`[HUMAN_CONFIRMED: …（P8 落地）]` 已填（P0-brief「上游关联」+ `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md` round 5：A1–A7 全 ALIGNED，A5.3/A7.4 HUMAN_CONFIRMED 落 P8）。
- **跨文件核实**：`git diff --stat f75e129..HEAD -- agate/LIMITATIONS.md agate/adr.md` → 无输出（P4a–P4c 确未碰这两个文件）。改动面清单 `git diff --stat f75e129..HEAD -- agate/ docs/` 中亦无 `LIMITATIONS.md` / `adr.md`。
- **结论**：P8 交付项、P7 阶段不构成未闭环 BLOCKER（P1 §9 已显式登记落点，改动面确未提前动）。P8 须完成的 SCOPE+ 收尾清单见 §7。

---

## 3. 跨文件一致性（引用具体文件 + 节名）

### 3.1 P1 BDD 数 = P6 验收数 = P6.5 judge 数

- `grep -c '^#### BDD-' P1-requirements.md` = **53**（BDD-1~53 连续）。
- P6-acceptance.md frontmatter `pass: 53` / `fail: 0`；正文 `grep -cE '^- (PASS|FAIL) BDD-' P6-acceptance.md` = **53**，其中 `^- PASS BDD-` = 53 / `^- FAIL BDD-` = 0。§4 汇总「53/53 PASS, 0 FAIL」。
- P6.5-judge-verdict.md frontmatter `status: passed` / `criteria_total: 53` / `criteria_passed: 53` / `partial: false`；正文「逐条结论（53/53，零挑验，编号 1~53 齐全）」。
- **三者一致**：53 = 53 = 53，无「数量对但内容映射错位」——P6-acceptance §4.1~§4.18 分节标题与 P1-requirements §4.1~§4.18 分节标题逐节对齐，每条 BDD 有直接 `test_bdd_NN_*` 用例或 doc-assertions 命中行。

### 3.2 P2 packages vs 实际改动面

P1/P2 frontmatter `packages: [agate-scripts, agate-rules, agate-docs, agate-tests]`。`git diff --stat f75e129..HEAD` 改动面逐项归属：

| 改动文件 | package | 依据 |
|---|---|---|
| `agate/scripts/agate_dispatch_route.py`（新）/ `check-dispatch-routing.py`（新）/ `agate-dispatch.py` / `check-events.py` / `check-protocol-consistency.py` | agate-scripts | P2-design §1.1 M3/M4/M4b/M6 + CHECK 9 锚点登记 |
| `agate/rules/dispatch-tiers.yaml`（新） | agate-rules | P2-design §1.1 M1（协议本体档位词表） |
| `agate/dispatch-protocol.md` / `agate/SETUP.md` / `agate/platform-notes.md` / `agate/assets/execution-roles/architect.md` / `docs/design-notes/design-dispatch-routing.md` / `agate-workspace/roadmap/roadmap.md` | agate-docs | P2-design §1.1 M7/M9/M10/M8/M12；`architect.md` 归 agate-docs 见 P1 §8 |
| `agate/tests/`（`unit/test_tag0034_*.py` ×9 + `regression/test_tag0034_zero_change.py` + `fixtures/tag0034_*/`） | agate-tests | P2-design §1.1 M11 |
| `agate-workspace/dispatch-routing.yaml`（新 +45 行） | 项目级配置（非 package、非 SELF-GATE，对齐 `maintainability.yaml`） | P2-design §1.1 M2 + §4.4 |
| `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`（新 +850 行） | review 报告产出（非 package） | SELF-GATE `protocol-alignment-review` round 5 报告 |

- **改动面全部落在声明的 4 个 package 内**（agate-workspace 配置 + review 报告为显式非 package 项）。**无「改了但 package 没声明」**。
- `check-protocol-consistency.py` 落 agate-scripts：`git diff f75e129..HEAD -- agate/scripts/check-protocol-consistency.py` = 仅 `SCRIPT_ALIGNMENT_ANCHORS` 追加 `check-dispatch-routing.py` 一条（`keywords: [VALID_CLI, VALID_EFFORT, fallback]`，无 `callers`），+5 行、无其它改动。这不在 BDD-39 冻结清单（冻结的是 gate / state-transition / phases / 状态机），是新增 gate 脚本的必要登记（alignment review round 1 已核为「新脚本必要登记」），与 P4-implementation.md M8 行「修复 protocol-alignment-review misaligned 结论」一致。

### 3.3 P4 实现路径 vs P2 §1.1 M1~M12 方案

逐项核 P2-design §1.1 改动清单 vs `git diff --stat` + P4-implementation*.md 改动清单：

| M | P2 §1.1 落点 | 实现核实 |
|---|---|---|
| M1 | `agate/rules/dispatch-tiers.yaml` 新（`tiers:` + `defaults:`） | 新文件 +29 行，P4-implementation.md「新增文件」表 M1 |
| M2 | `agate-workspace/dispatch-routing.yaml` 新 scaffold | 新文件 +45 行，`check-dispatch-routing.py` 对它 exit 0（P4 自查 + P5 `gate_commands.P5_routing_schema`） |
| M3 | `agate/scripts/check-dispatch-routing.py` 新（schema 静态校验器） | 新文件 +234 行，P4-implementation.md M3 |
| M4 / M4b | `agate_dispatch_route.py`（`resolve` / try-and-fall）+ `agate-dispatch.py` `route` 子命令 | 新 +853 行 + `agate-dispatch.py` +108 行；既有渲染路径（`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by`）未触碰（P4-implementation.md「修改文件」表 + BDD-39 回归护栏 `test_tag0027_b2_*` 零改动仍绿） |
| M5 | `agate_dispatch_route.py` 子进程 spawn + 结构化输出解析（P4b） | P4-implementation-P4b.md「修改文件」表：`dispatch_once` / `_default_subprocess_run` / 三平台判定表；fixture `agate/tests/fixtures/tag0034_{claude_code,codex,opencode}/` 已入库 |
| M6 | `check-events.py` 追加第 8 条 dispatch_route 理由码枚举 | `git diff` 核：纯追加 —— docstring 第 7 条注释补 `dispatch_route` + 新增第 8 条 + 模块常量 `DISPATCH_ROUTE_REASONS = {launch_fail, infra_error, no_parseable_output}`；第 1-7 条 + 哈希链算法 + GENESIS/ts/judge 计数未动。与 P2-design §3.8 逐条一致 |
| M7 | `agate/dispatch-protocol.md`「派发编排机制」节新增子节 | `### 0. 派发路由（查表 → 派首选 → 逐级回落 → 再派发）` at line 506；+88 行；含 line 529「gate 判定只认产出文件 + exit code，不认谁生产的」+ line 535/538 两条完整性不变量 + 单 Agent 模式 no-op（line 565）+ DEBT0039 措辞②（BDD-49） |
| M8 | `agate/assets/execution-roles/architect.md`「批次设计」节 DEBT0039 措辞① | +2 行，见 §2.1 跨文件核实 |
| M9 | `agate/SETUP.md` 机器级档位绑定 scaffold 小节 | +38 行，P4-implementation-P4b.md M9（「步骤 2-dispatch-routing」） |
| M10 | `agate/platform-notes.md` effort 注明 + 结构化输出字段小节 | +17 行；effort 注明子片 P4a 落（P4-implementation.md），结构化输出字段小节 P4b 落（P4-implementation-P4b.md M10） |
| M12 | design-note 头部 + §2.1/§2.2 重写 + roadmap RM-AG0060 回写 | `design-dispatch-routing.md` +65/-… 行（头部 line 5「本任务定案（2026-09-09 重写）」块 + §2.1 line 40 三层落点 + §2.2 line 71「try-and-fall，无 probe」）；`roadmap.md` RM-AG0060 行：旧 `rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml`，「按序探测」→ try-and-fall，`{cli,model}` 二元 → tier + effort 两轴，作废项「探测缓存 + native 探测方式」已删（BDD-46/47） |

- **无 M 项漏做**；做法与 P2-design §3 设计吻合（`resolve` 算法 §3.3 / try-and-fall §3.7 四值 `outcome.kind` / `dispatch_route` 事件 §3.8 / tmux §3.10 均在 P4-implementation*.md「实现关键决策」逐条对应）。P4b 的 A1 alignment 修复（`classify_outcome` 基础设施信号按 cli 细分）对齐 P2-design §3.7 判定表 / platform-notes.md M10，R1 三值 `reason` 守住（无 `gate_fail`）——非偏离，是判定表精度对齐。

### 3.4 BDD-39 冻结文件零改动复核

`git diff --stat f75e129..HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py agate/state-machine.md` → **无输出**（exit 0，逐字节不变）。与 P6-acceptance §4.13 BDD-39 PASS + P6.5-judge-verdict `bdd-39-40-recheck.log` 独立复核一致。`check-events.py` 被本任务改（第 8 条追加）——不在冻结清单（冻结的是 gate / state-transition / phases / 状态机），P2-design §1.2「不改什么」明确「只追加第 8 条、既有链零改动」，`git diff` 已核为纯追加。

---

## 4. 未决项清零

- `grep -nE '^\s*\[NEED_CONFIRM|^\s*\[BLOCKER|^\s*\[DEVIATION-CRITICAL' P1-requirements.md` → **无命中**。P1 §5 是 `[NO_NEED_CONFIRM]`；§0 有一处行首 `[P0_STALE: …]`（Claude Code 2.1.266 vs 2.1.263，patch bump，已在 §0 / `verification_env` 反映，非未决项）；两条 SCOPE+ 反引号包裹、非行首标记。
- P6-acceptance.md 行首 `[NO_NEED_CONFIRM]` + `[PROD_NOT_TOUCHED]`；P6.5-judge-verdict.md `status: passed` / `partial: false`，无 NEEDS-REVISION 条目。
- P1 frontmatter `baseline_changes` 1 条（BDD-10 `[BASELINE_CHANGE:]`，用户 2026-09-09 批准）+ `suggest_resolved` 6 条（主 Agent 已采纳）——均为已闭合项，非未决。

---

## 5. CODE-MAP 核对

本任务无 `agate-workspace/agents/CODE-MAP.md`、无 `P2-skeleton.md`（`project_phase` 非 bootstrap）→ CODE-MAP 机制未采用。P4-implementation*.md「新增文件核对表」4 处新文件均标 `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]`。`code_map_new_files_count` / `code_map_reviewed_count` 字段省略。**本项跳过。**

---

## 6. design-note §5 / §7 残留旧路径串判定

P6-acceptance §2「观察」节 + P6 verifier 转 P7 观察项：`docs/design-notes/design-dispatch-routing.md` 的 **§5「影响面」（line 193 起）与 §7「待确认事项」（line 218 起）** 仍留旧串 `rules/dispatch-routing.yaml` 与「按序探测 / 探测」叙事。`grep -nE 'rules/dispatch-routing\.yaml|按序探测|探测' docs/design-notes/design-dispatch-routing.md` 命中：

- **line 195**（§5）：`新增 rules/dispatch-routing.yaml（配置文件，非协议本体，不受 SELF-GATE）。` —— 与 §2.1（line 40 起，本任务已重写）「配置文件在 `agate-workspace/dispatch-routing.yaml`、不在 `agate/rules/`」直接冲突。
- **line 197**（§5）：`"查表 → 探测 → 定 target → 再派发"` —— 与 §2.2（line 71，已重写为「查表 → 派首选 → 逐级回落 → 再派发（try-and-fall，无 probe）」）叙事冲突。
- **line 220 / 223**（§7）：`1. rules/dispatch-routing.yaml 的确切 schema …` / `4. 探测成本与 cli: native 探测方式：① task 内探测缓存 …` —— 旧路径串 + P0-brief scope 已明文作废的「探测缓存 + native 探测方式」项仍在。

**判定**：`[DEVIATION: design-note §5/§7 残留旧路径串 rules/dispatch-routing.yaml + 「按序探测/探测」叙事，与本任务已重写的 §2.1 / §2.2 定案冲突]` —— **非 CRITICAL**：docs-only 设计文档、不影响任何 BDD / 脚本 / gate；BDD-46 的 Then 判据范围明确限定为「头部『做什么』+ §2.1 + §2.2」，该范围内已按 2026-09-09 定案重写、`test_bdd_46` PASS（P6-acceptance §4.16）。属真跨文件（同文件跨节）不一致——读者读 §2.1 见文件在 `agate-workspace/`、读 §5 见 `rules/`，会困惑。`deviation_count: 1` / `deviation_critical_count: 0`。

**建议主 Agent 处理方式**（P7 只审不写，不自己改 design-note）：三选一，倾向后者 ——
1. P7 阶段定点修正：主 Agent 在 P7 commit 一并把 §5 line 195/197 + §7 line 220/223 的旧串对齐 §2.1/§2.2（改动小、一次性消隐患）；
2. **登记为 P8 docs 收尾项**（倾向）：与 §7「P8 收尾清单」的 A5.3/A7.4 doc-sync + roadmap RM-AG0060 回写 done 同批处理，P8 dispatch-context 显式列 design-note §5/§7 旧路径串对齐；
3. 已知偏离接受：若判定 §5/§7 属历史叙事段、后续 design-note 整体重构时再收 —— 但当前 §7 line 223 的「探测缓存」项 P0-brief 已明文作废，留着有误导风险，不建议纯接受。

---

## 7. 结论

跨文件一致性审查逐条完成，锚定具体文件 + 节名：

- **DESIGN_GAP 配对**：`design_gap_count: 4` / `design_gap_reviewed_count: 4`（G1 P4-implementation.md:53→:55；G2/G3 P4-implementation-P4b.md:53/:55→:57；G4 P4-implementation-P4c.md:49→:51）。4 条 REVIEWED 决策方向分别与 P2-design §4.1 / §3.7·R1 / §3.4·§9 要点 4 / §3.10·R10 一致，无隐性偏离，`blocker_count: 0`。
- **SCOPE+ 闭环**：DEBT0039（BDD-48/49/50 P6-acceptance §4.17 全 PASS + `architect.md` +2 行 / `dispatch-protocol.md` line 506 子节已落地 —— 实质闭环，frontmatter `scope_resolved` 回写留 P8）；A5.3/A7.4（`git diff f75e129..HEAD -- agate/LIMITATIONS.md agate/adr.md` 无输出，P1 §9 登记为 P8 交付 —— 非未闭环 BLOCKER）。
- **跨文件一致性**：P1 BDD 53 = P6-acceptance frontmatter `pass:53` / 正文 PASS 行 53 = P6.5-judge-verdict `criteria_total:53`/`criteria_passed:53`；P2 packages 4 项覆盖全部 `git diff f75e129..HEAD` 改动面（agate-workspace 配置 + review 报告为显式非 package），无「改了但未声明」；P4 实现 M1~M12 逐项落地、做法吻合 P2-design §3；BDD-39 冻结文件（`phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md`）`git diff` 无输出；`check-events.py`（M6）/ `check-protocol-consistency.py`（CHECK 9 锚点）diff 均为纯追加。
- **未决项清零**：P1-requirements.md 无行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]`；P6 / P6.5 无 NEEDS-REVISION。
- **CODE-MAP**：机制未采用，跳过。
- **design-note §5/§7**：`[DEVIATION: …]` 非 CRITICAL（`deviation_count: 1` / `deviation_critical_count: 0`）——docs-only、不影响 BDD/脚本/gate，建议登记为 P8 docs 收尾项（见 §6）。

**无 `[BLOCKER]`、无 `[DEVIATION-CRITICAL]`。** `status: approved`。

### P8 收尾清单（供 P8 dispatch-context 引用）

1. DEBT0039：frontmatter `scope_resolved` 回写 + `tech-debt.md` DEBT0039 `status: closed` / `task_id: null → TAG0034`。
2. A5.3/A7.4 doc-sync：① `agate/LIMITATIONS.md` 局限 2 补「部分缓解链」段（含诚实边界句「仍非根治 / 主 Agent 自身选型·横传 model 无外部约束，与局限 3 同构」）；② `agate/adr.md` 补 ADR-013「派发路由 / gate 生产者无关性」（关联 ADR-002 / ADR-006 / RM-AG0060）；alignment review 以 `[HUMAN_CONFIRMED: …（P8 落地）]` 闭合 A5.3 / A7.4。
3. `docs/design-notes/design-dispatch-routing.md` §5（line 195/197）+ §7（line 220/223）旧路径串 `rules/dispatch-routing.yaml` + 「按序探测 / 探测缓存」叙事对齐已重写的 §2.1 / §2.2（本文 §6 DEVIATION）。
4. roadmap `RM-AG0060` 回写 `done`（P8 gate 硬校验 RM-AG0043）。
5. tmux（G4）：目标部署环境开启 `AGATE_DISPATCH_TMUX` 默认前复跑 research §10 tmux 验证项 —— 登记为 P8 / 未来迭代事项，不阻断发布。
6. CHANGELOG `[Unreleased]` 段补（`check-changelog.py` 仅 P8 触发）。
