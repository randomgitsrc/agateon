---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0051
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的**强制指令**，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

对 TAG0051 的 **P1–P6 全部产出**做跨文件一致性审查，产出
`{AGATE_WORKSPACE}/tasks/TAG0051-release-decoupling/P7-consistency.md`。

### 检查清单（P7 卡六项，逐项给结论）

1. **DESIGN_GAP 配对**：主 Agent 实测 `P4-implementation.md` **未声明任何 `DESIGN_GAP`**
   ⇒ `design_gap_count: 0` / `design_gap_reviewed_count: 0`（**请自行复核**，别只信这句）。
   ⚠️ 但该文件 **§10「设计偏差 / 已知偏离」**有 **2 条**，请按「已知偏离（deviation）」处置（见下）。
2. **SCOPE+ 闭环**：核对 `P1-requirements.md` 的 `[SCOPE+]` 增补是否已全部纳入基线
   （有则须有 `[SCOPE_RESOLVED]`；**本任务 P1 未声明 scope_plus**（frontmatter 无 `scope_plus`）
   ⇒ 请核实后给出「无 SCOPE+ 增补 / 无需闭环」的显式结论，**空白不算做过**）。
3. **跨文件一致性**（**实质锚点必写**）：
   - **`P2§packages`（9 个）↔ P8 发布范围**：本任务的 `packages` 是否与实际改动面、以及 P8 将声明的
     交付范围一致？（注意：本任务终态 = READY，**不落 tag/Release**——请按新语义核「交付范围」口径）
   - **P1 BDD 数 ↔ P6 验收数**：P1 = **23** 条 `#### BDD-NN:`；P6 的 `results` = **23** 条、
     `criteria_total`（P6.5 judge）= **23** ⇒ 三者相等；**并请抽核至少 3 条 BDD 的「内容」是否被映射到
     **正确**的验收结果**（P7 卡常见错误 2：数量对但内容映射错）。
   - **`P4§impl-path` ↔ `P2§decision`**：P2 的 M1–M16 落点与 P4 实际改动文件是否吻合
     （可对照 `git show --stat 9771e76a` / `git diff --name-only 581369fc..9771e76a`）。
4. **未决项清零**：`P1-requirements.md` 无残留行首 `[NEED_CONFIRM]`；产出中无 `[BLOCKER]` /
   `[DEVIATION-CRITICAL]`。
5. **CODE-MAP 核对**：对照 `{AGATE_WORKSPACE}/agents/CODE-MAP.md` 与 `P4-implementation.md` 的
   **「## 新增文件核对表」** 逐条核对。主 Agent 实测：**4 行**新增文件、**全部** `[CODE_MAP_EXEMPT: 理由]`，
   且 `CODE-MAP.md` **未含**这些新文件 ⇒ 请判定该处置是否成立，并填
   `code_map_new_files_count: 4` / `code_map_reviewed_count: 4`（配对）；核对通过标 `[CODE_MAP_SYNC:]`。
6. **架构决策落点与过时标注**：核对 `{AGATE_WORKSPACE}/decisions/`（**主 Agent 实测该目录不存在** ⇒
   本任务无既有跨任务决策可核，也无证伪项）。本任务新增的架构决策 **ADR-016** 落在 `agate/adr.md`
   （协议层，非项目 `decisions/`）——请核该落点是否恰当，并把「`decisions/` 缺失 ⇒ 无待办」写成显式结论。

### 要处置的**已知偏离（deviation）**（来源：`P4-implementation.md` §10 + SELF-GATE 评审的登记项）

主 Agent 已实测这些**均非阻塞**，请逐条转抄 + 给出你的 `verdict`（`accepted` / 其他）与依据：

| # | 偏离 | 来源与依据 |
|---|------|-----------|
| **D1** | `P2-design.md` §决策 8/§5 仍述 wrapper 用 `cp -a` + `checkout -- .` + `clean -fdx`，而实现已换 **`git clone --local --no-hardlinks`**（**外部契约不变**：同名参数、corpus 干净、跑后真仓干净） | `P4-review.md` R2 判「**已批准设计记录 vs 实现，留待 P7 以已知偏离处置**」；换实现**由派发指引授权**（P2 卡允许 `env_constraints`/实现细节层面的调整，非未评审的自主决策）；SELF-GATE 最终复审判「**内部实现细节偏离设计记录、非协议语义 MISALIGNED、可留待 P7、不阻断 P4**」 |
| **D2** | `docs/design-notes/r6-differential.sh::_error_lines` 的**实际比较口径**（所有 `GATE ` 前缀行）比其文件头自述的「(退出码, ERROR 行集合)」更宽 ⇒ P8 成功文案删 ④ 被判为差异 | 已由 **allowlist D13** 记录（**不收紧守卫强度**）；口径落差由主 Agent 登记 **DEBT0070**（不在本任务修复面） |
| **D3** | `agate/tests/` 内一处注释仍述 wrapper 旧 `cp -a` 序列 | SELF-GATE 最终复审登记（非阻塞、注释级） |
| **D4** | `P2-design.md` §5 的 `cp -a` 描述（**与 D1 同源**，由 D1 一并覆盖，此处单列以便逐条可追溯） | 同 D1 |
| **D5** | `agate/phase-cards/README.md` / 模板中「P8 release bump 范围」类措辞、README 交付小结模板 `[{task_id}] READY — {task_name} {version}` 的 `{version}` 语义存疑 | SELF-GATE 最终复审登记（**主 Agent 已裁决**：READY 模板**保留不动**——两处逐字一致、不涉 `tag` 字面、BDD-1 不覆盖；改动会波及 READY 标记格式与既有看板/日志惯例） |

> 请把 D1–D5 **逐条**转抄进正文（保留人类痕迹），并在 frontmatter 的
> `deviation_count` 计入（`deviation_critical_count: 0`）。

### 产出规格（硬）

`P7-consistency.md` frontmatter **必须含**：

```yaml
phase: P7
task_id: TAG0051
type: consistency
parent: P2-design.md
trace_id: TAG0051-P7-20261011
status: draft
agent: consistency-reviewer
blocker_count: 0
deviation_count: <你判定的条数>
deviation_critical_count: 0
design_gap_count: 0
design_gap_reviewed_count: 0
code_map_new_files_count: 4
code_map_reviewed_count: 4
# 可选结构化：findings / code_map_reviewed 列表
```

正文须含**跨文件引用关键词**（如 `P2§packages`、`P4§impl-path`、`P1§BDD`、`P6§results`），
并按 P7 卡的「实质锚点要求」给出：DESIGN_GAP 配对项 + REVIEWED 标记（本任务为 0 条，须显式说明）、
跨文件检查项 + 源文件节名、SCOPE+ 闭环结论。

### 约束

- **只写** `P7-consistency.md`（+ 可选 progress `P7-progress-consistency-reviewer.md`）；**只读**其余一切。
- **只读纪律**：禁止写仓命令（`git add/commit/restore/reset/clean/stash`）；**写类工具不得对真实仓库运行**；
  要实测就只读跑（不留残渣）。
- **不得**执行任何不可逆外部动作。
- bash 设超时；状态标记二值 `[PROD_NOT_TOUCHED]`。

### 客观查证信息（主 Agent 已实测，供交叉验证）

- 提交链：`9771e76a`（P4）/ `c5bda4df`（P5）/ `03dcc1f7`（P6）/ `c810c19a`（P6.5 verdict）；
  分支起点 `581369fc`（origin/main）。
- P6.5 judge：`status: passed`、`criteria_total == criteria_passed == 23`、`partial: false`。
- P5：7 条 `gate_commands.P5` 全执行，唯一红灯 = 预存环境项 `test_bdd_43`（`known-failures.md` 已登记）。
- P6 gate：`check-gate.py P6` rc=2（D1–D10 通过）、`check-p6-evidence.py` rc=0、
  `check-p6-provenance.py` rc=2（仅非阻塞 WARNING）。

### 返回

只返回**两行**：`File: <路径>` + `Status: <approved|needs-revision>`；
第三行可选「blocker/deviation 计数 + 一句摘要」。**绝对不要**返回文件全文。
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
6. **架构决策落点与过时标注核对**：核对 `{AGATE_WORKSPACE}/decisions/` 是否已写入本任务应落的跨任务架构决策，且被本任务证伪的既有决策已就地标注「已过时 + 被什么取代」而非删除。仅核对，不在 P7 撰写决策正文（缺失项记为待办，由决策的提出方在下一次 P2 前补写入 `decisions/`；见 DEBT0039）

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
# ── TAG0050 批 E 成对声明（非 legacy 任务；跨文件聚合后逐条核对）──
# design_gap_reviews:
#   - {gap: DG1, verdict: accepted, checked_against: [P2 §3], basis: in_bdd}
# code_map_reviewed:
#   - {file: agate/scripts/x.py}
# findings:
#   - {id: F1, severity: note, text: "...", status: resolved, resolution: "...", evidence: "..."}
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
