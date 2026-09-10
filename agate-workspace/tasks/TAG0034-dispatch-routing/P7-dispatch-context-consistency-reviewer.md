---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

P7 一致性交叉检查：对照 P1–P6 产出做跨文件一致性审查，产出 `P7-consistency.md`（frontmatter 机器计数：`blocker_count` / `deviation_count` / `deviation_critical_count` / `design_gap_count` / `design_gap_reviewed_count`；正文散文标记 `[DESIGN_GAP:]` / `[DESIGN_GAP_REVIEWED:]` 行首）。Header `status:` 落 `approved` / `rejected` / `needs-revision`。**只审不写**——发现偏离写进结论，由主 Agent 决策（回退 / 定点修正 / REVIEWED-ACCEPTED）。**按 DEBT0039 边界：P7 只做跨文件一致性验证、不 author 文档正文**（本任务本身正在落地这条边界，见 BDD-48/49）。

### 检查清单（逐条，附实质锚点）

**1. DESIGN_GAP 配对（gate 硬校验）—— 共 4 条，逐条转抄 + REVIEWED**

P4 三份实现记录里的 DESIGN_GAP（`grep -nE '^\[DESIGN_GAP' P4-implementation*.md`）：

| # | 来源:行 | DESIGN_GAP 摘要 | REVIEWED 来源 |
|---|---|---|---|
| G1 | `P4-implementation.md:53` | P4a `_route_main` 只做 resolve + 输出路由计划 JSON（`form ∈ {default,chain}` / chain / 首候选 / dispatch_context），端到端 try-and-fall 交 P4b | `P4-implementation.md:55`（主 Agent 2026-09-09，与 P2 §4.1 批次意图一致） |
| G2 | `P4-implementation-P4b.md:53` | `_route_main` 端到端「约定产出文件路径」走 `AGATE_DISPATCH_EXPECT` 环境变量、未设则保守回落（`NO_PARSEABLE_OUTPUT`） | `P4-implementation-P4b.md:57`（主 Agent 2026-09-10，符合 R1 保守侧） |
| G3 | `P4-implementation-P4b.md:55` | 候选链中段 `cli: native` → `dispatch_once` 返 `HAS_OUTPUT` 占位（交驱动会话代发） | `P4-implementation-P4b.md:57`（同 G2 一条 REVIEWED 覆盖两 gap，与 P2 §3.4 / 新节自动化天花板一致） |
| G4 | `P4-implementation-P4c.md:49` | tmux 包裹待目标环境验证 → feature flag `AGATE_DISPATCH_TMUX` 默认关、两 helper 纯逻辑 | `P4-implementation-P4c.md:51`（主 Agent 2026-09-10，P2 §3.10「定稿+待落地验证、不阻塞 P8」的落地形态） |

**P7 产出要求**：`design_gap_count: 4` + `design_gap_reviewed_count: 4`；正文逐条行首 `[DESIGN_GAP: G1 …]` + 紧跟 `[DESIGN_GAP_REVIEWED: G1 …引用 P4 行 + 跨文件锚点]`。每条 REVIEWED 行须含跨文件引用关键词（`P2§4.1` / `P2§3.4` / `P2§3.7` / `P2§3.10` 之类），否则 gate WARNING。核你自己判断这 4 条 REVIEWED 是否真的站得住（决策方向与 P2 意图一致、非隐性偏离）——不站得住 → `[DEVIATION-CRITICAL]` + `rejected`。

**2. SCOPE+ 闭环**

P1-requirements.md §1 有两条 SCOPE+（`` `[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]` `` / `` `[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4 …]` ``，均反引号包裹、非纯行首 → `check-scope-resolved.py` 当前 exit 0）：

- **DEBT0039 SCOPE+**：交付 = BDD-48/49/50（architect.md 批次设计节边界措辞 + dispatch-protocol.md author-P4-vs-一致性-P7 区分 + consistency 0 ERROR）。P6 已逐条 PASS。→ **工作已完成**。P1 §8 明确「frontmatter `scope_resolved` 由 P8 收尾回写」。你核实：这三条 BDD 在 P6-acceptance 确为 PASS + 两处协议文档措辞确已落地（grep `architect.md` 批次设计节 / `dispatch-protocol.md`「### 0. 派发路由」子节）。结论建议：**已实质闭环、frontmatter 回写留 P8**（非 BLOCKER）。
- **A5.3/A7.4 SCOPE+**：交付 = `agate/LIMITATIONS.md` 局限 2 缓解链段 + `agate/adr.md` ADR-013，**P8 落地**（P1 §9「P8」行 + alignment review 报告附录已起草，`[HUMAN_CONFIRMED: …（P8 落地）]` 已填）。你核实：P1 §9 确有这两条 P8 交付登记 + P4b/P4c 确未碰 `LIMITATIONS.md` / `adr.md`（grep `git diff f75e129..HEAD -- agate/LIMITATIONS.md agate/adr.md` 应无输出）。结论建议：**P8 交付项、P7 阶段不构成未闭环 BLOCKER**（P1 已显式登记落点），但在 P7-consistency 明确记「P8 须完成的 SCOPE+ 收尾清单」供 P8 dispatch-context 引用。

**3. 跨文件一致性（引用具体文件 + 节名）**

- **P1 BDD 数 = P6 验收数**：`grep -c '^#### BDD-' P1-requirements.md` = 53；P6-acceptance.md frontmatter `pass: 53` / `fail: 0`，正文 PASS 行数 = 53（`grep -cE '^- (PASS|FAIL) BDD-' P6-acceptance.md`）。P6.5 judge verdict `criteria_total: 53` / `criteria_passed: 53`。三者一致。
- **P2 packages vs 实际改动面**：P1/P2 frontmatter `packages: [agate-scripts, agate-rules, agate-docs, agate-tests]`。实际改动（`git diff --stat f75e129..HEAD -- agate/ docs/ agate-workspace/dispatch-routing.yaml agate-workspace/roadmap/`）：`agate/scripts/`（agate_dispatch_route.py 新 / check-dispatch-routing.py 新 / agate-dispatch.py / check-events.py / check-protocol-consistency.py）= agate-scripts；`agate/rules/dispatch-tiers.yaml` 新 = agate-rules；`agate/dispatch-protocol.md` / `agate/SETUP.md` / `agate/platform-notes.md` / `agate/assets/execution-roles/architect.md` / `docs/design-notes/design-dispatch-routing.md` / `agate-workspace/roadmap/roadmap.md` = agate-docs（`architect.md` 归 agate-docs 见 P1 §8）；`agate/tests/` = agate-tests。`agate-workspace/dispatch-routing.yaml` = 项目级配置（非 package、非 SELF-GATE）。核：改动面是否全部落在声明的 4 个 package 内，有无「改了但 package 没声明」。
- **P4 实现路径 vs P2 方案**：P2-design §1.1 M1~M12 逐项 vs P4-implementation*.md 改动清单——M1 `dispatch-tiers.yaml` / M2 `dispatch-routing.yaml` / M3 `check-dispatch-routing.py` / M4 `agate_dispatch_route.py` / M4b `agate-dispatch.py route` / M6 `check-events.py` 第 8 条 / M7 `dispatch-protocol.md` 新节 / M8 `architect.md` DEBT0039① / M9 `SETUP.md` / M10 `platform-notes.md` / M12 design-note + roadmap。核有无 M 项漏做或做法偏离 §3 设计。
- **回归硬约束（BDD-39）**：`git diff --stat f75e129..HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py agate/state-machine.md` 无输出（P6 已验，你复核）。**注意**：`check-protocol-consistency.py` 被本任务改了（CHECK 9 锚点表补 `check-dispatch-routing.py`）——这不在冻结清单里（冻结的是 gate/state-transition/phases/状态机），是新增 gate 脚本的必要登记（alignment review round 1 已核为「新脚本必要登记」）。核这条 diff 只是 `SCRIPT_ALIGNMENT_ANCHORS` 追加一条，无其它改动。

**4. 未决项清零**

- `grep -nE '^\s*\[NEED_CONFIRM|^\s*\[BLOCKER|^\s*\[DEVIATION-CRITICAL' P1-requirements.md` —— 应无命中（P1 §5 是 `[NO_NEED_CONFIRM]`；两条 SCOPE+ 是反引号包裹、非未决项）。P6/P6.5 无 NEEDS-REVISION 条目。

**5. CODE-MAP 核对** —— 本任务**无** `agate-workspace/agents/CODE-MAP.md` / 无 `P2-skeleton.md`（`project_phase` 非 bootstrap）→ 机制未采用，`code_map_*_count` 字段可省略 / 填 0，跳过本项。

**6. P6 转 P7 的观察项（P6-acceptance §2 观察节 / P6 verifier 返回）**

`docs/design-notes/design-dispatch-routing.md` 的 **§5 / §7**（非 §2.1/§2.2）仍留旧串 `rules/dispatch-routing.yaml`。BDD-46 判据范围**限定**为「头部 + §2.1 + §2.2」，该范围内已按 2026-09-09 定案重写、`test_bdd_46` PASS（P6 已验）。你判定：
- 若跨节残留属**真跨文件不一致**（design-note 内部 §2.1 说文件在 `agate-workspace/` 而 §5/§7 说 `rules/`，读者会困惑）→ 标 `[DEVIATION: design-note §5/§7 残留旧路径串，与 §2.1 定案冲突]`（**非 CRITICAL**——docs-only 文件、不影响任何 BDD / 脚本 / gate），并在结论建议主 Agent 处理方式（P7 阶段定点修正 vs 登记为 P8 docs 收尾项 vs 已知偏离接受）。
- 若判定「§5/§7 是历史叙事段、BDD-46 有意不纳入、不构成误导」→ 标 `[DEVIATION_REVIEWED: …理由]`，`deviation_count` 计入但 `deviation_critical_count: 0`。
- **不要自己改 design-note**（P7 不 author）。

### 约束

- **实质锚点**：结论不得裸 `BLOCKER=0` / `一致`。每条跨文件检查引用具体文件 + 节名（`P2§1.1 M4` / `P1 BDD-53` / `P6-acceptance frontmatter pass:53` 之类）。
- **gate 格式契约**：`[DESIGN_GAP:` / `[DESIGN_GAP_REVIEWED:` 必须行首（正则 `^\s*>?\s*-?\s*\[DESIGN_GAP`）。`[BLOCKER]` / `[DEVIATION-CRITICAL]` 存在 → `check-gate.py P7` exit 1。DESIGN_GAP 未配对（4 条有 REVIEWED 但 P7 少转抄）→ exit 1。
- **只审不写**：不改代码 / 测试 / 协议文档 / P1-P6 产出。P7-consistency.md + P7-progress.md 是你唯一落盘。
- **PROD**：dogfooding，"生产" = 主 checkout + `~/.agate`，禁改。仅 worktree 内读 + 跑 git / grep。`[PROD_NOT_TOUCHED]` / `[PROD_TOUCHED]` 二值。
- **命令超时兜底**：所有 bash 前 `timeout <n>s`。
- **格式**：约束节 / 结论正文避免行首 `- PASS` / `- FAIL`（provenance 预判检测）——P7 用 `[BLOCKER]` / `[DEVIATION]` / `[DESIGN_GAP_REVIEWED]` 标记，不用 `- PASS`。

> 子派发能力：不启用（P7 单发，输入数量豁免）。

### 上游关联

- P1..P6 全部 commit：P1 `f75e129` / P2 `b851b1e` / P3 `c218026` / P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` / P5 `2772891` / P6 `eb924be` / P6.5 `cb9dfb9`。`.state.yaml` phase=P7（agate-next 消费 P6.5 judge passed 后推进）/ `p5_pass_commit: 92edcfc`。
- P6 verifier：53/53 PASS，0 FAIL（P6-acceptance frontmatter `pass:53`/`fail:0`）。P6.5 judge：`status: passed` / `criteria_total:53` / `criteria_passed:53` / `partial:false`（fresh context 逐条重验、信息隔离）。
- P4 三批 C8 `review` approved（`P4-review.md`）+ `protocol-alignment-review` aligned（`docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`，round 5；A1-A7 全 ALIGNED；A5.3/A7.4 HUMAN_CONFIRMED 落 P8）。
- 主 Agent 已修 `P3-test-cases.md` 缺 `agent` 字段（补 frontmatter `agent: test-designer` 等标准 header）→ `check-p6-provenance.py` exit 0 → agate-next P6→P7 推进。该 diff 随 P7 commit 一并提交（属 P7 阶段的一致性收尾，非 author 正文）。
- `check-scope-resolved.py` 当前 exit 0（两条 SCOPE+ 反引号包裹未被行首正则捕获）；`check-protocol-consistency.py --strict-errors-only` exit 0（0 ERROR / 329 存量 WARNING）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（53 BDD + §1 两条 SCOPE+ + §7/§8/§9 裁剪·SCOPE+·下游 + `[NO_NEED_CONFIRM]`）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（§1.1 M1~M12 改动清单 + §3 各节设计 + §4 批次 + §8 gate_commands + §9 design-note 修订要点 + frontmatter packages）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P4-implementation.md` + `P4-implementation-P4b.md` + `P4-implementation-P4c.md`（**4 条 DESIGN_GAP + REVIEWED + 改动清单**）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P6-acceptance.md`（53 条 PASS 行 + frontmatter `pass`/`fail` + §2 观察节）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P6.5-judge-verdict.md`（criteria_total/criteria_passed）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`（env_constraints / known_risks 最高危 = 模型购物完整性洞 / packages 惯例）
- `agate/assets/execution-roles/consistency-reviewer.md`（你的角色定义）
- 跨文件核对目标（git diff / grep，非「读结论」）：`agate/dispatch-protocol.md`（「### 0. 派发路由」子节）/ `agate/assets/execution-roles/architect.md`（批次设计节）/ `docs/design-notes/design-dispatch-routing.md`（§2.1/§2.2 + §5/§7）/ `agate/rules/dispatch-tiers.yaml` / `agate/scripts/agate_dispatch_route.py` / `agate-workspace/roadmap/roadmap.md`
- `AGENTS.md`（gate 脚本分层、`--strict-errors-only` 定义、双工作区纪律）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P7-consistency.md agate-md-field-set --list` 查看应填字段；逐个写入（`blocker_count: 0` / `deviation_critical_count: 0` 期望；`design_gap_count: 4` / `design_gap_reviewed_count: 4`；`status`；`agent: consistency-reviewer`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P7

路径：phase-cards/P7-consistency.md
---
# P7 — 一致性检查

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P7 + 源文件数 ≤5 + 无 implicit_coupling + 有 coupling_checklist（须列出至少 2 个已检查的耦合点，空清单不合规）→ 跳过，读 P8 卡片
> ⑨ P7 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 consistency-reviewer subagent 执行交叉检查
   1.1 写 P7-dispatch-context-consistency-reviewer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 对照 P1-P6 产出做跨文件一致性审查
3. 产出 P7-consistency.md
4. 预跑 check-gate.py P7
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P7，不要提前写 P8——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P7): {摘要}"（phase=P7，P7 产出含 P7-consistency.md）
7. P7 commit 完成后进入 P8：**phase 推进 P8 随 P8 产出 commit 一起**（P8-release.md 就绪后），不是单独 phase commit

## 如果是重试

→ 读 agate/rules/state-transitions.md 确认 retry 上限（P7 MAX=2）

## 前置条件

- [ ] P1-P6 全部产出文件就绪

## 执行方式

consistency-reviewer subagent 执行。检查清单：

1. **DESIGN_GAP 配对**：P4-implementation.md 中的 DESIGN_GAP 声明 → 必须在 P7-consistency.md 中逐条转抄 + 配 REVIEWED 标记。未配对 → gate 不通过
2. **SCOPE+ 闭环**：P1-requirements.md 有 [SCOPE_RESOLVED] 标记，确认所有 SCOPE+ 增补已纳入基线
3. **跨文件一致性**：P2 声明的 packages 与 P8 release 的 bump 范围一致？P1 的 BDD 和 P6 的验收结果数量匹配？P4 的实现路径和 P2 的方案设计吻合？
4. **未决项清零**：P1-requirements.md 无残留行首 [NEED_CONFIRM]（P6 不再有 NEED_CONFIRM）、[BLOCKER]、[DEVIATION-CRITICAL]
5. **CODE-MAP 核对**：对照 `{AGATE_WORKSPACE}/agents/CODE-MAP.md` 与 P4「新增文件核对表」逐条核对，发现依赖方向偏离标 `[CODE_MAP_DRIFT:]`（WARNING 级，不阻断）；核对通过标 `[CODE_MAP_SYNC:]`

## 实质锚点要求（N3⑨）

| gate 断言 | 实质锚点（P7 产出须包含） |
|-----------|--------------------------|
| BLOCKER=0 | DESIGN_GAP 配对项 + REVIEWED 标记 |
| CRITICAL=0 | 跨文件检查项 + 源文件节名 |
| SCOPE+ 闭环 | 条目 + SCOPE_RESOLVED |

gate 脚本校验说明：
- DESIGN_GAP_REVIEWED：P4 声明的每条 DESIGN_GAP 在 P7 产出中须有对应行含 `DESIGN_GAP_REVIEWED`
- 跨文件引用关键词：P7 产出中须含源文件节名（如 `P2§packages`、`P4§impl-path`），否则 WARNING

## 产出规格

- P7-consistency.md：一致性审查结论
- 逐条检查结果，无 [BLOCKER] 标记

`blocker_count`/`deviation_count`/`deviation_critical_count`/`design_gap_count`/
`design_gap_reviewed_count`/`code_map_new_files_count`/`code_map_reviewed_count` 写在文件头
**frontmatter**（`---` 分隔块），不写正文；正文
`[BLOCKER]`/`[DEVIATION-CRITICAL]`/`[DESIGN_GAP]`/`[DESIGN_GAP_REVIEWED]` 散文标记保留为
人类痕迹（不迁移），gate 判定改读 frontmatter 结构化计数。**可直接复制的完整样例**：
```yaml
---
phase: P7
task_id: TAG0001           # 替换为实际任务编号
type: consistency
parent: P2-design.md
trace_id: T001-P7-20260101 # {task_id}-P7-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0                  # int ≥0
deviation_count: 0                # int ≥0
deviation_critical_count: 0       # int ≥0
design_gap_count: 0                # int ≥0
design_gap_reviewed_count: 0       # int ≥0
code_map_new_files_count: 0        # int ≥0（可选，仅骨架/CODE-MAP 机制已采用时填）
code_map_reviewed_count: 0         # int ≥0（可选，语义对应 design_gap_reviewed_count）
---
```

## gate 规则

```bash
check-gate.py P7 $TASK_DIR
```

- [BLOCKER] 存在 → exit 1
- [DEVIATION-CRITICAL] 存在 → exit 1
- DESIGN_GAP 未配对（P4 有但 P7 无 REVIEWED）→ exit 1
- CODE-MAP 未配对（code_map_reviewed_count < code_map_new_files_count，或 P4 实际标记数 > code_map_new_files_count）→ exit 1（两字段均缺失时机制未采用，跳过）
- 含 DESIGN_GAP_REVIEWED 但缺跨文件引用关键词 → WARNING（不改变 exit code）
- 全部通过 → exit 0

BLOCKER → consistency-reviewer 修改 → 再验 gate → … → 通过（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 推进条件（全部满足才写 phase: P8）

- [ ] P7-consistency.md 存在
- [ ] 无 [BLOCKER] / [DEVIATION-CRITICAL]
- [ ] DESIGN_GAP 全部 REVIEWED 配对
- [ ] SCOPE+ 闭环（P1 有 [SCOPE_RESOLVED]）

## P7 输入文件数量

P7 是输入文件数量限制的例外（模式 1 单发 + 输入数量豁免特例，见 dispatch-protocol「派发编排机制」全阶段适用表），不拆分。原因：
1. 跨文件一致性比较需要全部源文件同时可见
2. 角色文件（consistency-reviewer）已列出所需输入清单
3. dispatch-context 为 subagent 提供摘要，无需逐文件全文注入

## 常见错误

1. **漏转抄 P4 的 DESIGN_GAP**：P4 implementer 声明了实现偏差但 P7 没转抄 → gate 拦截
2. **一致性检查只看标题不对内容**：P1 BDD 数 = 15，P6 PASS 数 = 15 → 数量对，但 BDD-8 的内容在 P6 里被映射到错误的验收结果
3. **裸 'BLOCKER=0' 不引用锚点**：未做实质交叉检查，只写 '一致' → gate WARNING 提醒

gate 不过 ≠ 你失败了。红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P8 发布前最后一道质量门——P7 通过后进入机械发布步骤

> 完成 → 读 phase-cards/P8-release.md
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P7 / status=active / judge.enabled=true / p5_pass_commit=92edcfc；HEAD = `cb9dfb9`（P6.5）
- DESIGN_GAP：4 条（P4-implementation.md ×1 / P4-implementation-P4b.md ×2 / P4-implementation-P4c.md ×1），均有 `[DESIGN_GAP_REVIEWED:]`（P4b 一条 REVIEWED 覆盖两 gap）
- SCOPE+：2 条（P1 §1，反引号包裹）—— DEBT0039 并入（BDD-48/49/50 已 P6 PASS，实质完成）/ A5.3·A7.4 doc-sync（P8 交付，P1 §9 登记）
- P1 BDD = 53；P6-acceptance `pass:53`/`fail:0`；P6.5 verdict `criteria_total:53`/`criteria_passed:53`
- 主 Agent 已核：`git diff f75e129..HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py agate/state-machine.md` 无输出；`git diff f75e129..HEAD -- agate/LIMITATIONS.md agate/adr.md` 无输出（A5.3/A7.4 确未动，P8 交付）
- 已知观察：`design-dispatch-routing.md` §5/§7 残留旧串 `rules/dispatch-routing.yaml`（BDD-46 范围限 头部+§2.1+§2.2，已重写并 PASS）—— 检查清单第 6 项处理
- `check-gate.py P7` 预跑 = exit 0（回退抵达态，主 Agent 自判）；`check-scope-resolved.py` exit 0；`check-protocol-consistency.py --strict-errors-only` exit 0
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
