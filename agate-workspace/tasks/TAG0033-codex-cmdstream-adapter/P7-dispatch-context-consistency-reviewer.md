---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: consistency-reviewer
---

<dispatch_guide>
> 以下派发指引是本次审查的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标

对 TAG0033（Codex 命令流适配器 + 平台接入）的 P1-P6 全部产出做**跨文件一致性审查**，产出
`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P7-consistency.md`（frontmatter 结构化计数 +
正文逐条检查结果，无 `[BLOCKER]` / `[DEVIATION-CRITICAL]`）。P7 是最后一道质量门。

### 必查项（逐条在 P7-consistency.md 给结论 + 实质锚点）

1. **DESIGN_GAP 配对**：`P4-implementation.md` 声明 `DESIGN_GAP: 无`（3 处：adapter-core / protocol-docs /
   重试#1 段均写「无」）→ `design_gap_count: 0` / `design_gap_reviewed_count: 0`。确认 P4 三段确实无
   DESIGN_GAP，无需转抄配对。
2. **SCOPE+ 闭环**：`P4-implementation.md` 声明 `[SCOPE+]: 无`（3 处）；`P1-requirements.md` 无
   `[SCOPE_RESOLVED]`（因无 SCOPE+）→ SCOPE+ 闭环成立（无增补待纳入）。确认。
3. **跨文件一致性**（要引用**源文件节名**作实质锚点，如 `P2§packages` / `P4§impl-path` / `P6§BDD对照`）：
   - **packages**：`P1-requirements.md` frontmatter `packages: [agate-scripts, agate-docs, agate-tests]`
     == `P2-design.md` frontmatter `packages`（同）。P8 版本 bump 范围应覆盖这三个包面（agate 协议本体
     的 CHANGELOG + 版本）。确认一致。
   - **BDD 数量匹配**：`P1-requirements.md §6` 有 **30 条 BDD**（BDD-1~30）；`P6-acceptance.md` frontmatter
     `pass: 30 / fail: 0` → PASS + FAIL = 30 ≥ P1 BDD 数 30。`P6.5-judge-verdict.md` `criteria_total: 30 /
     criteria_passed: 30`。三处一致。**抽查内容对应**（不只看数）：随机抽 3-5 条 BDD，确认 P6-evidence/
     的 `bdd-NN.log` 实测的是该 BDD 的 Then 判据（不是错位映射）。
   - **实现路径 vs 设计**：`P4-implementation.md` 改动面（`agate/scripts/agate-cmdstream-adapters.py` 加
     `CodexAdapter` + `_codex_is_finished` helper + 2 截断常量 + `ADAPTERS["codex"]` + `import shlex`；
     `agate/platform-notes.md` Codex 章 + 命令流适配 bullet；`agate/SETUP.md` Codex 小节；
     `agate/tests/unit/test_agate_cmdstream_{adapters,detect}.py` + `test_codex_platform_docs.py`；
     `agate/tests/fixtures/cmdstream/codex-session.jsonl` + `codex-subagent-session.jsonl`）
     == `P2-design.md §2.1「改什么」` 声明的改动落点。确认无「设计说改 A 实际改了 B」的偏离。
   - **零改动硬约束**：`P2 §2.2 不改什么` + `P1 §5 范围锁定` 声明 detect.py / `CommandRecord` IR /
     既有三适配器零改动——`git diff main...HEAD -- agate/scripts/agate-cmdstream-detect.py
     agate/scripts/agate-cmdstream-ir.py` 应为空（P6 BDD-21 已验，你复核一次）。
   - **BASELINE_CHANGE 一致性**（P5→P4 回退修 F1 引入）：`P1-requirements.md` §4.1（`item.status` 取值集
     补 `failed`）/ BDD-5 Given（`status="failed"`）/ BDD-6 Given（"真·未结束"收紧）+ `P2-design.md`
     §5 设计点 2（pending 判据 `_codex_is_finished` 口径）/ R3 的 `[BASELINE_CHANGE]` 注记——与
     `P4-implementation.md`「重试#1（F1 修复）」节描述的实现（`_codex_is_finished` helper：已结束 =
     `status ∈ {completed,failed}` ∪ `completed_at_ms` 非 None ∪ `exit_code` int 非 bool）**逐条一致**，
     且与 `P6-acceptance.md` BDD-5/6/15 的验收结论一致。DEBT0035 引用正确。
4. **未决项清零**：`P1-requirements.md` 无残留行首 `[NEED_CONFIRM]`（有 `[NO_NEED_CONFIRM]`）/ `[BLOCKER]` /
   `[DEVIATION-CRITICAL]`；`P4/P5/P6` 产出无残留 `[BLOCKER]` / `[DEVIATION-CRITICAL]`。
5. **CODE-MAP 核对**：`P4-implementation.md`「## 新增文件核对表」声明「本阶段无新增源码文件」
   （`CodexAdapter` 加进既有 `agate-cmdstream-adapters.py`）；protocol-docs 批已把
   `agate-workspace/agents/CODE-MAP.md` line ~33 从「三平台命令流适配器」更新为「四平台…/ Codex rollout
   JSONL」。核对二者一致 → 标 `[CODE_MAP_SYNC:]`；`code_map_new_files_count: 0` / `code_map_reviewed_count: 0`
   （无新增源码文件）。若发现依赖方向偏离 → `[CODE_MAP_DRIFT:]`（WARNING 级，不阻断）。

### 需你评估并给结论的两个点（P6 遗留 + 回退相关）

- **P6 verifier 的 V7 finding**（`P6-evidence/real-machine-p6.md` §2.4 / BDD-25 行有记）：
  `agate/platform-notes.md` Codex 章现有措辞「嵌套深度（`spawn_agent` 内再 `spawn_agent`）未测（归 P6 V7）」/
  「既有 `max_depth=1` 结论待 V7 嵌套深度实测后复核」——但 **P6 V7 已实测 `depth=2` 可用**（本轮 + 首轮
  归档 `.archived/p6-pre-retreat-20260909/real-machine-p6.md` 两次独立证实）。这是 **platform-notes.md
  的措辞与实测事实之间的一处滞后**（不是矛盾——「待复核」不算错，只是保守/过时）。
  - 你的判定：这算 `[DEVIATION-CRITICAL]` / `[BLOCKER]` 吗？（**大概率不算**——BDD-25 测的是「新旧
    Codex 内容不自相矛盾 + 标时效」，现有「待 V7 复核」时效指针本身合规，P6 BDD-25 已 PASS）。
  - 若判定非阻塞：在 P7-consistency.md 记为一处 `deviation_count`（非 critical）或 WARNING 级观察，
    并给**处理路由建议**：(a) P8 顺手在 platform-notes.md 把「待 V7 复核」收敛为「已实测 depth=2 可用」
    （P8 本就要动 platform-notes.md 面的 CHANGELOG——但改 platform-notes.md 正文触发 SELF-GATE，需评估）；
    或 (b) 登记一条低优 DEBT（`source: retrospective`，closure = 措辞收敛）；或 (c) 判定现措辞可接受、
    不处理。**你选一个并写清理由**，不要留空。
- **P5→P4 回退的完整性**（`git log --grep=retreat` / `git log --grep=DEBT0035` 可查）：
  - retreat commit `52fe210`（P5→P4）+ DEBT0035（`source: retreat`，evidence ref `52fe210`，`status:
    in_progress`，`task_id: TAG0033`）已登记（`agate-workspace/debt/tech-debt.md`）。确认 DEBT0035 的
    `closure_criteria` 5 条中本任务已满足哪几条（预期 4/5——剩「P5/P6 重新通过」由本任务收尾/P8 闭合，
    或本任务结束后把 DEBT0035 改 `status: closed`——你给建议，P8 处理）。
  - `.state.yaml` `retries.P4` 有 attempt 1 记录（回退 retry 计数）。确认 retry 未超上限（P4 MAX=3）。

### 约束

1. **P7 是审查，不改代码/协议文档/测试**——发现问题 → 标记 + 路由建议，不自己改。若 V7 措辞你认为
   必须本阶段改（不建议），须先报告主 Agent。
2. **frontmatter 结构化计数是 gate 判定依据**：`blocker_count` / `deviation_count` /
   `deviation_critical_count` / `design_gap_count` / `design_gap_reviewed_count` /
   `code_map_new_files_count` / `code_map_reviewed_count`——按实际填，`blocker_count` / `deviation_critical_count`
   必须为 0 才 gate exit 0。
3. **实质锚点**：`BLOCKER=0` / `CRITICAL=0` 的结论必须引用**跨文件检查项 + 源文件节名**（如
   `P2§packages == P1§packages`），不能只写「一致」（裸结论 → gate WARNING）。
4. **所有 bash 命令加 `timeout <秒>s` 前缀**；每步落盘 `P7-progress.md`。

### 上游关联

- **P1-requirements.md**（§5 范围锁定 / §6 30 BDD / §7 真机清单 / §4.1 + BDD-5/6 BASELINE_CHANGE）
- **P2-design.md**（§2.1 改什么 / §2.2 不改什么 / §5 五设计点 + 设计点 2 BASELINE_CHANGE / §7 gate_commands / §11 dispatch_plan）
- **P3-test-cases.md**（BDD → test id 映射 + 验证层归位表）
- **P4-implementation.md**（adapter-core §1-4 + protocol-docs 批节 + 重试#1（F1 修复）节 + SCOPE+/DESIGN_GAP 声明）
- **P4-review.md**（第 1 轮 + 第 2 轮复评——均 approved）
- **P5-test-results/**（第 3 轮 `unit.md` 1390 passed / `real-machine.md` V1/V6③ PASS）
- **P6-acceptance.md**（frontmatter pass=30/fail=0 + 30 条 PASS 行 + 交叉核对节）
- **P6.5-judge-verdict.md**（status: passed / criteria 30/30）
- **agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033{,-r2,-r3}.md**（3 轮 SELF-GATE，均 PASS）
- **agate-workspace/debt/tech-debt.md**（DEBT0035）
- **git log**（`9e91747`..`f484895` 本任务提交链，含 `52fe210` retreat）

### 输入文件（P7 输入数量豁免，全部同时可见）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P3-test-cases.md`
4. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md`
5. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-review.md`
6. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P5-test-results/unit.md` + `real-machine.md`
7. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6-acceptance.md` + `P6-evidence/real-machine-p6.md`
8. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6.5-judge-verdict.md`
9. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/.state.yaml`
10. `agate-workspace/debt/tech-debt.md`（DEBT0035 段）
11. `agate-workspace/agents/CODE-MAP.md`（line ~33 适配器条目）
12. `agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033.md` + `...-r2.md` + `...-r3.md`
13. `agate/assets/review-roles/consistency-reviewer.md`（角色定义 + 检查清单）
14. `agate/phase-cards/P7-consistency.md`（本阶段卡片——实质锚点要求 / gate 规则 / frontmatter 计数字段）
15. `git diff main...HEAD -- agate/scripts/agate-cmdstream-detect.py agate/scripts/agate-cmdstream-ir.py`（零改动复核——应为空）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P6（P7 产出 commit 随 P7-consistency.md
  推进 P7）/ judge.enabled=true。HEAD = `f484895`（P6.5 verdict commit）。
- **P4 声明**：`DESIGN_GAP: 无`（3 处）/ `[SCOPE+]: 无`（3 处）→ `design_gap_count: 0` /
  `code_map_new_files_count: 0`（无新增源码文件）。
- **packages**：P1 == P2 == `[agate-scripts, agate-docs, agate-tests]`。
- **BDD 计数**：P1 §6 = 30；P6 pass=30/fail=0；P6.5 criteria 30/30——三处一致。
- **零改动**：`git diff main...HEAD -- agate-cmdstream-detect.py agate-cmdstream-ir.py` 空（P6 BDD-21 + P6.5 judge 均已验）。
- **DEBT0035**：`source: retreat`，evidence ref `52fe210`，`status: in_progress`，`task_id: TAG0033`；
  closure_criteria 5 条（① status=failed 映射非 pending ② P3 测试覆盖 + fixture ③ detect 判 SPIN
  ④ 全量 pytest + consistency ⑤ platform-notes.md status 取值集 + P1 §4.1）——本任务已满足 ①②③④⑤ 的实现面，
  「P5/P6 重新通过」= P5 r3（`5f704a0`）+ P6 重做（`49d3353`）已完成。
- **P6 V7 finding**：platform-notes.md「max_depth=1 待 V7 复核」措辞 vs P6 实测 depth=2 —— 你评估路由。
- **P7 gate**（`check-gate.py P7`）：`blocker_count` / `deviation_critical_count` = 0 + DESIGN_GAP 全配对
  + CODE-MAP 配对（本任务均 0）→ exit 0。

### 产出文件字段

先 `Write` 出 `P7-consistency.md`（正文逐条检查 + 散文 `[DESIGN_GAP_REVIEWED]` 等人类痕迹标记），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P7-consistency.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段并逐个 `set`；写入失败照错误提示修正，不手写 frontmatter。

frontmatter 必填：`phase=P7`、`task_id=TAG0033`、`type=consistency`、`parent=P2-design.md`、
`trace_id=TAG0033-P7-20260909`、`status=draft`、`created=2026-09-09`、`agent=consistency-reviewer`、
`blocker_count`（预期 0）、`deviation_count`（0 或含 V7 措辞滞后 1）、`deviation_critical_count`（0）、
`design_gap_count`（0）、`design_gap_reviewed_count`（0）、`code_map_new_files_count`（0）、
`code_map_reviewed_count`（0）。

### 返回

返回：P7-consistency.md 路径 + 各计数（blocker / deviation / deviation_critical / design_gap /
design_gap_reviewed / code_map_new / code_map_reviewed）+ 跨文件一致性逐项结论（packages / BDD 数 /
实现路径 / 零改动 / BASELINE_CHANGE 一致性）+ V7 措辞滞后的路由建议（P8 收敛 / DEBT / 可接受，选一个）+
DEBT0035 closure 建议 + 是否有 `[BLOCKER]` / `[DEVIATION-CRITICAL]`。
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
