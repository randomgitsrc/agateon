---
phase: P7
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: consistency-reviewer
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

P7 一致性交叉检查：对照 P1-P6 产出做跨文件一致性审查，确保实现未偏离设计。产出 `P7-consistency.md`（含 frontmatter 结构化计数 + 正文逐条检查 + 行首 `[DESIGN_GAP_REVIEWED:]` 配对）。

### 检查清单（逐条给结论 + 实质锚点）

1. **DESIGN_GAP 配对（最高优先级）**：`P4-implementation.md` 含 **5 处行首 `[DESIGN_GAP: ...]`**（L55-58 批 1 四条 + L118 批 2 一条）→ P7 必须**逐条转抄原始标记行 + 配一行 `[DESIGN_GAP_REVIEWED: ...]`**（gate 只扫 P7-consistency.md，不转抄 = gate 拦截）。逐条裁决依据：
   - **DESIGN_GAP 1（M2 双 copytree）**：**已在 P4 fix-1 消解**——P4-review 首轮判「可接受但主要迁就 fixture」，fix-1 补 fixture 贴近真实元仓库形态 + `_sync_root_scripts` 回退 P2-design B1 单源 copytree（P4-implementation.md「## P4 修复轮（fix-1）」§③）。→ `[DESIGN_GAP_REVIEWED: 已确认——fix-1 回退单源 copytree，与 P2-design §3 决策 B1 一致]`
   - **DESIGN_GAP 2（`latest` 别名）**：P4-review 判「合理补全」（P1 §3.4 / BDD-2/13 / install.sh --versions 均用 `agate-install.py latest`，M 表遗漏）。→ `[DESIGN_GAP_REVIEWED: 已确认——P1 隐含要求，P2 M 表遗漏的合理补全]`
   - **DESIGN_GAP 3（install.sh `$SCRIPT_DIR`）**：**已在 P4 fix-1 消解**——P4-review 首轮 CRITICAL（curl|bash 新机路径断裂），fix-1 按选项 A 改为 `$AGATE_HOME/repo/agate/scripts/agate-install.py` 优先 + `$SCRIPT_DIR` 兜底，回归 P2-design §4.2 M6 意图（P4-implementation.md「## P4 修复轮（fix-1）」§①）；P4-review 复评 approved 0 CRITICAL（独立复现 EXIT 0）。→ `[DESIGN_GAP_REVIEWED: 已确认——fix-1 选项 A 回归 P2-design §4.2 M6，P4-review 复评 approved]`
   - **DESIGN_GAP 4（`_ensure_repo` git fetch）**：P4-review 判「合理」（P0-brief scope Phase 3 update 路径范围内，fail-open + `--force --prune` 不误删本地 tag）。→ `[DESIGN_GAP_REVIEWED: 已确认——update 路径范围内，fail-open 属实]`
   - **DESIGN_GAP 5（v050 反引号微调）**：P4-review D 组判「INFORMATIONAL 可接受」（纯 markdown 代码格式微调，措辞/语义不变，符合 BDD-12「加指针不改叙事」）。→ `[DESIGN_GAP_REVIEWED: 已确认——格式微调非叙事改动，BDD-12 判据不违反]`
   - 你须**独立核对**这些裁决是否成立（读 P4-review.md 首轮 + 复评、P4-implementation.md fix-1 节、实际代码 diff），不盲信主 Agent 的建议措辞
2. **SCOPE+ 闭环**：全流程未产生 `[SCOPE+]`（P1 [NO_NEED_CONFIRM]，P2 无 SCOPE+，P4 无 SCOPE+）→ 确认无 SCOPE+ 待闭环，写「无 SCOPE+，N/A」
3. **跨文件一致性**（引用具体文件节名，非裸「一致」）：
   - **P2 packages `[agate-scripts, agate-docs, agate-tests]` ↔ P8 bump 范围**：本任务改 `agate/scripts/*` + `agate/UPGRADING.md` + `agate/SETUP.md` + `README.md` + `install.sh` + `agate/tests/*`——P8 会 bump agate 版本（agateon 单一版本号，非多包独立发布）。核对 P2 packages 声明与实际改动面一致
   - **P1 14 条 BDD ↔ P6 14 条 PASS ↔ P6.5 judge 14/14**：数量匹配 + 每条 BDD 编号在 P6/P6.5 都有对应结果（不是数量对但内容错位）
   - **P4 实现路径 ↔ P2 方案设计**：决策 A1（`_protocol_root` 探测序 + `_resolve_version_info` 两处调用）与 P2-design §2 候选 A1 一致；决策 B1（单源 copytree，fix-1 后）与 P2-design §3 候选 B1 一致；M1-M11 落点与 §1.1 改什么表一致；resolve-entry.py「只核对不改」与 P2-design §1.2「不改什么」一致
   - **纯增量红线**：P2-design 反复强调的「根即协议部署方继续可用 + 探测序 vdir/scripts 先 + 不改 env 覆盖/legacy 软链兜底/`.agate-version` 格式」——P4 实现 + BDD-7 验收是否真的锁死
4. **未决项清零**：`P1-requirements.md` 无残留行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]`（P1 §8 是 `[NO_NEED_CONFIRM]`）
5. **CODE-MAP 核对**：`{AGATE_WORKSPACE}/agents/CODE-MAP.md` 存在（P4 gate WARNING 提示机制已采用）。本任务新增文件 = P3 的 `agate/tests/unit/test_upgrading_lifecycle.py` + `agate/tests/integration/test_version_lifecycle_e2e.py`（测试脚手架）；P4 未新增文件。逐条判定 `[CODE_MAP_SYNC:]`（测试文件通常 CODE-MAP 豁免）或 `[CODE_MAP_DRIFT:]`（WARNING 级不阻断）。frontmatter 填 `code_map_new_files_count` / `code_map_reviewed_count`

### frontmatter 结构化计数（gate 读这个判定）

```
blocker_count: 0
deviation_count: 0
deviation_critical_count: 0
design_gap_count: 5           # P4-implementation.md 行首 [DESIGN_GAP:] 数
design_gap_reviewed_count: 5  # 你在 P7-consistency.md 配的 [DESIGN_GAP_REVIEWED:] 数，须 == design_gap_count
code_map_new_files_count: 2   # P3 新增的两个测试文件（按实际核对）
code_map_reviewed_count: 2
```
（数值以你实际核对为准；若发现 P4-implementation.md 的 DESIGN_GAP 数 ≠ 5，以实际 grep `^\[DESIGN_GAP` 为准）

### 约束

- **批判视角**：假设 P2 设计可能有错、P4 实现可能偏离——逐项找偏差，偏差优先归类为问题而非「可接受的调整」。但已由 P4-review 明确 REVIEWED-ACCEPTED 的 DESIGN_GAP，核对其裁决理由是否成立即可，不重开
- **只审不改**：不改任何代码/文档/上游产出；发现 BLOCKER → status: rejected + 明确指出，主 Agent 走回退
- 结论引用具体锚点（文件节名 / BDD 编号 / M 编号 / commit SHA），不接受裸「一致」/「BLOCKER=0」
- `[DESIGN_GAP:]` / `[DESIGN_GAP_REVIEWED:]` 必须**行首**（gate 正则 `^\s*>?\s*-?\s*\[DESIGN_GAP`）
- 含 `DESIGN_GAP_REVIEWED` 时须同时含跨文件引用关键词（`P1.*BDD` / `P2.*packages` / `P4.*implementation`），否则 WARNING

### 上游关联

P1 14 条 BDD approved（risk_level: high，implicit_coupling: true）。P2-design approved（决策 A1 `_protocol_root` + 决策 B1 单源 copytree；M1-M15）。P4-review 首轮 needs-revision（1 CRITICAL = DESIGN_GAP 3）→ fix-1 → 复评 approved 0 CRITICAL。P5 gate_commands.P5* 全跑（唯一 failed 为预存并行 flaky，已登记 known-failures.md）。P6 14/14 PASS。P6.5 judge 14/14 passed。DEBT0034 已登记（三步迁移文案双写）。commits：P4 `1d9a322` / P5 `2f50f4c` / P6 `af5bfe6` / P6.5 `5f08bf8`。

### 输入文件（P7 输入数量豁免，全部同时读）

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（scope / out-of-scope / known_risks）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 条 BDD + §4 同类扫描 + §8 [NO_NEED_CONFIRM]）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（§1.1 改什么 / §1.2 不改什么 / §2 决策 A1 / §3 决策 B1 / §6 gate_commands / §10 完成标志）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review.md（P2 阶段确认项 + 4 项非阻塞澄清）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1/2 + fix-1 + **5 处行首 [DESIGN_GAP:]**，转抄对象）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-review.md（首轮 needs-revision + 复评 approved——DESIGN_GAP 裁决理由权威）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P5-test-results/unit.md（P5 结果 + 预存 flaky）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P6-acceptance.md（14 条 BDD 验收结果）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P6.5-judge-verdict.md（judge 14/14 passed）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/known-failures.md（预存 flaky 登记）
- {AGATE_WORKSPACE}/agents/CODE-MAP.md（CODE-MAP 核对对象）
- /home/kity/oclab/agateon/agate/assets/execution-roles/consistency-reviewer.md（角色定义，稳定版）
- `git diff 3f3cc01..HEAD -- agate/ install.sh README.md README.zh-CN.md`（实际改动 diff——跨文件一致性核对用）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息

- 解释器 `/usr/bin/python3`；核对用 read/grep/git diff，不改任何文件
- bash 外层 `timeout` 30-90s；单步串行；状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P7-consistency.md`
- 分阶段落盘：追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P7-progress.md`
- frontmatter 用 `agate-md-field-set.py`（先 `--list`）；Header 成品值：`phase: P7` / `task_id: TAG0032` / `parent: P2-design.md` / `trace_id: TAG0032-P7-20260907` / `agent: consistency-reviewer` / `type: consistency` / `status: draft` / `created: 2026-09-07`

### 返回

`File: <P7-consistency.md 路径>` + `Status: <approved|rejected|needs-revision>` + `BLOCKER=N, DESIGN_GAP 未配对=M` + 一句话摘要。不返回文件全文。
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
