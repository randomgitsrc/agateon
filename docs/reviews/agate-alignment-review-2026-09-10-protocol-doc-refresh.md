---
review_date: 2026-09-10
reviewer: protocol-alignment-review
change_summary: 文档一致性刷新（分支 docs/protocol-doc-refresh，7 commit / 批 A-F）——补 P6.5 / agate next / ceremony / 事件账本 / Codex·DSH 门面；LIMITATIONS 8 节→6 节精简重构；无机制/行为改动
files_changed: [README.md, README.zh-CN.md, SELF-GATE.md, CHANGELOG.md, agate/CONTEXT.md, agate/LIMITATIONS.md, agate/WORKFLOW.md, agate/state-machine.md, agate/dispatch-protocol.md, agate/orchestrator-template.md, agate/loop-orchestration.md, agate/git-integration.md, agate/SETUP.md, agate/platform-notes.md, agate/phase-cards/README.md, agate/scripts/agate-summary.py, agate/scripts/check-protocol-consistency.py, agate/scripts/README.md, agate/assets/execution-roles/implementer.md, agate/assets/execution-roles/verifier.md, agate/tests/ENV-SENSITIVE-TESTS.md, agate/tests/fixtures/tag0034_regression_baseline.json, agate/tests/integration/test_protocol_alignment_review.py, install.sh, docs/design-notes/*, docs/guides/project-map.md, agate-workspace/roadmap/roadmap.md, "archived/ 移动 + 16 *.progress.md 删除"]
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 意图分析 / 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（含 3 处 NIT） |
| A4 | 数值/规则一致性 | ALIGNED |
| A5 | 语义降级 / 文档传播 | ALIGNED |
| A6 | 关键词位置 / 锚点表 + 测试真实意图 | ALIGNED |
| A7 | ADR 一致性 | ALIGNED |

**总结论：aligned-with-nits**

---

## A1: 意图分析 —— 真的只是文档一致性吗？

意图（读 diff + `doc-consistency-audit-2026-09.md` §1/§5）：一次全仓「文实脱节」审计的执行——把已落地机制（P6.5 独立 judge、`agate next` 查表推进、ceremony 档位、`gate-events.jsonl` 事件账本、Codex/DSH 平台）补进门面与协议文档，并精简 `LIMITATIONS.md`。声称「无机制/行为改动」。

逐一核对四个「疑似夹带行为改动」的点：

**1. `agate/scripts/agate-summary.py`（agate-summary.py:152-180）** —— 新增探测 `{root}/../CHANGELOG.md` 与 `{root}/CHANGELOG.md` 取存在者，替换 startup 提示串第 3 行的写死路径 `~/.agate/CHANGELOG.md`。
- 判定对象：这是给人看的「下一步做什么」提示文本，**不是 gate、不写状态、不参与任何 exit code 判定**。旧路径在 legacy 单软链布局下是死链（`~/.agate/CHANGELOG.md` 解析为 `<clone>/agate/CHANGELOG.md`，不存在）。
- 实跑 `python3 agate/scripts/agate-summary.py`：第 3 行现输出 `读 /home/kity/oclab/agateon/CHANGELOG.md（了解…）`，文件存在。
- `test_agate_summary.py`（8 用例）全绿。**结论：纯 UX 死链修复，非行为改动。ALIGNED**

**2. 测试断言改动（test_protocol_alignment_review.py:61-66）** —— `assert "CHECK 1-9" in text` → `assert "check-protocol-consistency.py" in text` + `assert "CHECK" in text`。
- 起因：`SELF-GATE.md` 正文把「CHECK 1-9」改为「结构 CHECK 全集（当前 1-15）」（`check-protocol-consistency.py` 实际到 CHECK 15，mechanical 实跑确认）。旧断言字面 `"CHECK 1-9"` 会 RED。
- 测试真实意图（`test_sg_5_selfgate_has_checklist`）：SELF-GATE.md 检查清单引用了 consistency 脚本的结构 CHECK 集 + 含 `protocol-alignment-review` + `HUMAN_CONFIRMED`。新断言仍完整覆盖该意图，只是把「上界数字」去写死（注释明写「CHECK 数会增长」）。
- **结论：随文档改动的合理去硬编码，未削弱测试意图。ALIGNED**

**3. `tag0034_regression_baseline.json`（state-machine.md hash bump）** —— `agate/state-machine.md` 的 sha256 `f38be3b4…` → `7ea082b9…`、bytes 50218 → 52028；`_note` 重写说明「state-machine.md 是叙事文档、非机制本体，经 SELF-GATE + protocol-alignment-review 刷新其正文（补 agate next / ceremony / cmdstream 指针，未改任何转移规则）」。
- gate 机制三文件（`phases.yaml` / `check-gate.py` / `check-state-transition.py`）+ agate-dispatch 渲染产物两文件的 hash **字节锁定不变**——BDD-39 的核心不变量（gate 逻辑零改动）保留。
- 复核 state-machine.md 的 diff：新增内容全是「机械化说明框」+「ceremony 对本节的影响」+「受控自主再派发与本节的关系」三段**指针 / 说明性文字**，转移表、`function 执行一步()` 伪码步骤 1-8、retry 语义均未动。新框自述「本节的手工规格是 `agate next` 实现所依据的权威语义」——手工规格仍是 source of truth。
- 替代方案（不 bump）= regression RED。JSON 缩进 2sp→1sp 是 cosmetic。**结论：叙事文档正文刷新的必然连带，非机制改动。ALIGNED**

**4. LIMITATIONS 精简重构（8 节 → 6 节）** —— 删旧「局限 5：协议文档内部一致性不在流程内」、旧「局限 8：CI backstop 平台矩阵」两个独立大节；旧「局限 6→5」「局限 7→6」重编号；局限 1-4 编号不变。
- 逐条核对「结构性内核是否保留」见 A5。两删节的**可判定内核**均被折进局限 3 正文（子弹条目），未丢失。
- 无 ADR 新增/修改（见 A7），无 gate 规则表述改动。**结论：诚实边界陈述的压缩，非语义降级。ALIGNED**（细节 A5）

**A1 总判：genuinely doc-consistency-only。没有任何一处编辑夹带 gate 逻辑 / 状态机转移 / retry 上限 / exit code 约定的实质改动。**

---

## A2: 脚本→文档对齐

改动的脚本只有 2 个，均为 docstring / 提示串层面：

**`check-protocol-consistency.py:6` + `agate/scripts/README.md:141`（scripts/README.md L138-143）** —— docstring 里「回应 LIMITATIONS.md『局限 5：…』」→「回应 LIMITATIONS.md 局限 3 的一条子项——『协议文档自身的语义一致性没有 in-flow gate』」。
- 起因：LIMITATIONS 重编号后旧「局限 5」不存在，按编号引用会悬空。
- 核对 `LIMITATIONS.md` 新局限 3 子弹条目原文：「**协议文档自身的语义一致性**没有 in-flow gate：`check-protocol-consistency.py` + SELF-GATE 是结构 / 关键词兜底，不覆盖语义…」——docstring 新表述与之语义一致。
- 脚本行为逻辑（CHECK 1-15）零改动，mechanical 实跑 CHECK 9 PASS。**ALIGNED**

**`agate-summary.py`** —— 见 A1 第 1 点。**ALIGNED**

无其它脚本改动，故无「脚本逻辑变了但文档没跟上」的风险面。

---

## A3: 一致性连锁 + 反向传播

### A3a 连锁（diff 内已处理的衍生改动）—— 逐一验证

| 主改 | 应连锁到 | 验证结果 |
|------|----------|----------|
| `state-machine.md` 加 `agate next` 机械化框 + ceremony 注 | `WORKFLOW.md` / `dispatch-protocol.md` / `orchestrator-template.md` / `loop-orchestration.md` | **全部已同步且一致**。WORKFLOW.md 方式 B/C 补「推进这一步用 `agate next` 查表机械完成，见 state-machine.md『主 Agent 的单步执行』」；dispatch-protocol.md 步骤 6 后加交叉引用段（仅 `agate next`，未误配 `agate advance`）；orchestrator-template.md 写文件表 + mapping 表补 `agate next` 指针 + P6.5；loop-orchestration.md 早已有「TAG0027 §3.7：推进判定统一走 `agate next`」+ 详细 gate 处理流程，与新 state-machine.md 逐条吻合（exit ∈ gate_pass_exit 直推 / exit 1 → retreat / P6 前进特例走 judge 裁决）。 |
| `LIMITATIONS.md` 删旧局限 5 / 8，6→5 / 7→6 | 按编号引用旧局限的所有活文件 | `check-protocol-consistency.py:6`、`scripts/README.md:141`、`roadmap.md:501` 均已同步（roadmap 改为「局限 3 子项『协议文档语义一致性无 in-flow gate』（原独立列为局限 5）」）。`ENV-SENSITIVE-TESTS.md:24`（前两轮评审的 must-fix）已改为指 `phase-cards/P5-verification.md`。`design-dispatch-routing.md`（前两轮 must-fix）4 处「局限 6」全部改为「局限 5（原局限 6）」，含头部 `:11` 的「局限 2/4/5」。 |
| `SELF-GATE.md` 触发列表加 `agate/rules/*.yaml` + CHECK 1-9→1-15 | `git-integration.md`（self-gate trailer 描述）| git-integration.md `:160-189` 段翻新，新增 SELF-GATE trailer 段，触发面写「`agate/*.md` / `agate/scripts/*` / `agate/**/*.md` / `agate/rules/*.yaml` 等 self-gate 触发文件」——与 SELF-GATE.md 一致。 |
| README 平台表加 Codex + DSH 行 | `platform-notes.md` / `WORKFLOW.md` / `SETUP.md` | 一致（详见下方专项）。 |
| `CONTEXT.md` exit-code 词条重写 | `phases.yaml` / `check-gate.py` / `loop-orchestration.md` | 一致（详见 A4）。 |
| git-integration.md 删独立 pre-commit 表 → 指 WORKFLOW.md | 「唯一事实源」不变量 | **正确**。全仓 grep：只有 `WORKFLOW.md:344` 有真表，dispatch-protocol.md:890 / state-machine.md:249 / git-integration.md:166 / scripts/README.md 全为指针。符合角色文件反向传播表第 40 行「不应再各自维护副本表格——否则视为回归」——本次是**消除**一处副本，是回归的反向。 |

### A3b 反向传播（diff 外、应被影响的文件）—— 主动推断并核查

| 推断应被影响 | 在 diff 里？ | 核查结果 |
|--------------|-------------|----------|
| `agate/AGENTS.md`（self-gate 触发面描述）| 否 | **无需改**。AGENTS.md:24 对触发文件面是「见 `SELF-GATE.md`」的委托指针，不自维护列表 → 不 drift。 |
| `docs/guides/worktree-dogfooding-guide.md`（SELF-GATE 触发）| 否 | **无需改**。只提「SELF-GATE 触发」概念，无文件类枚举。 |
| `phase-cards/P6-acceptance.md`（P6.5 judge 派发在此卡说明）| 否 | orchestrator-template.md mapping 表新注「P6 卡含 P6→P6.5 judge 派发」——P6 卡内容本轮未改，但 P6.5 机制非本次引入（TAG0020/v0.59.0 已落地），P6 卡既有内容已覆盖。**非本次 drift。** |
| `agate/adr.md`（局限重编号后 ADR 指针）| 否 | **无需改**。ADR 指针在 LIMITATIONS 一侧（`→ ADR-00X`），adr.md 不反向按局限编号引用。详见 A7。 |
| `agate/role-system.md`（state-machine 反传常见路径列出）| 否 | state-machine.md 本次新增均为说明性指针段，未改角色映射 / C8 规则 / 转移边 → role-system.md 无需同步。 |
| `agate/assets/review-roles/protocol-alignment-review.md:12`（触发条件行）| 否 | **NIT-1（见下）——应同步未同步。** |
| `agate/scripts/commit-msg-self-gate.py`（self-gate 辅助 hook 触发正则）| 否 | **NIT-2（见下）——doc 已加 `agate/rules/*.yaml`，辅助 hook 正则未加。** |

### A3 NIT（不阻塞，非 MISALIGNED）

**NIT-1｜`agate/assets/review-roles/protocol-alignment-review.md:12` 触发条件行未同步 `agate/rules/*.yaml`**
- 原文：`**触发条件**：agate/scripts/*.sh、agate/scripts/*.py、agate/*.md、agate/**/*.md、SELF-GATE.md 有改动时…`
- `SELF-GATE.md:20` 本轮新增 `agate/rules/*.yaml`（数据面权威源；CHECK 15 专扫）；CHANGELOG v0.71.0 已声明 `dispatch-tiers.yaml`「改它走 SELF-GATE」。此 role 文件的触发条件是同一份清单的复述，出现文档-文档漂移——正是本次刷新意在消除的那类。
- 判为 NIT 而非 MISALIGNED：该行是概述性复述、非权威源（权威在 `SELF-GATE.md` §触发条件）；role 的 A1-A7 运作不依赖此行的完整性；修复是 1 行文案，可随手补。
- 建议：在该行 `agate/**/*.md、` 后补 `agate/rules/*.yaml、`。

**NIT-2｜`agate/scripts/commit-msg-self-gate.py:39` 正则 + `:77` WARNING 文案未含 `agate/rules/*.yaml`**
- 正则 `^(agate/scripts/.*\.(sh|py)|agate/[^/]+\.md|agate/.+/.*\.md|SELF-GATE\.md|README\.md|AGENTS\.md)$` 不匹配 `.yaml`；WARNING 文案列举同样漏 `agate/rules/*.yaml`。故 rules-yaml-only 改动不会触发 commit-msg 辅助提醒，而 `SELF-GATE.md` 现明确把它列为触发面。
- 判为 NIT 而非 MISALIGNED：(a) `SELF-GATE.md:9-11` 明确该 hook 只是「辅助提醒」，WARNING 不拦截，「真正的强制力依赖主 Agent 自觉 + CI 兜底」——故这是「提醒覆盖面」缺口，不是「gate 强制力」缺口；(b) 文档侧（SELF-GATE.md）本轮变得**更**正确（对齐 CHANGELOG v0.71.0 + CHECK 15 实际），是 doc 领先 script；(c) 修正辅助 hook 正则属行为改动、超出「纯文档刷新」scope，宜后续单独任务处理。
- 建议：后续任务把正则扩为 `…|agate/rules/.*\.yaml|…` 并同步 `:77` 文案；本轮可在 commit message / CHANGELOG 记一句「辅助 hook 正则待后续对齐」。

**NIT-3｜`design-dispatch-routing.md` 索引行 / 文件头状态措辞未统一**（前一轮执行评审 §5 亦记为 cosmetic）：`docs/design-notes/README.md` 该行现为「设计收敛（…）**已落地 RM-AG0060**（TAG0034，v0.71.0…）」拼接形态，非 §8-4 约定的统一「已落地（TAGxxxx，vX.Y.Z）」格式。已落地信息在，纯 cosmetic，不阻塞。

---

## A4: 数值 / 规则一致性

**CONTEXT.md gate 词条重写 vs `phases.yaml` `gate_pass_exit`** —— 逐条核对：

CONTEXT.md:10 新表述：「多数 phase（P0-P3/P5/P6/P8）以 exit 2 为正常通过，P4/P7/P6.5 以 exit 0 为通过；exit 1 一律不通过；某 phase 的 `pass_set` 不含且 ≠1 才是真暂停 / 需人工。`agate next` 按 `pass_set` 三态消费」

`agate/rules/phases.yaml` 实际（逐 id 读 `gate_pass_exit`）：
- P0=2, P1=2, P2=2, P3=2 → 「P0-P3 = exit 2」✓
- P4=0 → ✓  P5=2 → ✓  P6=2 → ✓  P6.5=0 → ✓  P7=0 → ✓  P8=2 → ✓

**完全一致。** `check-gate.py:6-12` docstring 同口径（pass 判定以 `phases.yaml gate_pass_exit` 为准）。`loop-orchestration.md:246`「exit 2 是多数 phase 正常通过码 ∈ pass_set」一致。

**这是修 bug 而非引入冲突**：旧 CONTEXT.md 有两条近重复词条（`gate` / `gate exit code`）都写「0=通过，1=不通过，2=需人工判断」——与 `WORKFLOW.md` Pre-commit 表反复以「exit 2」作 PASS 条件、与 `loop-orchestration.md` / `check-gate.py` 全部冲突（审计 §3-D 记录的跨文档矛盾）。本次删掉冗余的 `gate exit code` 行、重写 `gate` 行对齐 `phases.yaml`。**A4 ALIGNED（且消解一处既存矛盾）。**

**其它数值面**：
- retry 上限：WORKFLOW.md / state-machine.md 新增文字均明写「ceremony **不改** retry 上限」；无新数字，与 `phases.yaml` `retry_cap` 无冲突。
- 阶段名 / CHECK 数：README「eight phases plus P6.5」+ phase-cards/README.md 加 P6.5 行 + WORKFLOW.md 核心阶段列加「P6.5 独立 Judge 复核」——与 `phases.yaml` 有 `P6.5` 条目一致。SELF-GATE.md「当前 CHECK 1-15」与 `check-protocol-consistency.py` `CHECKS` 列表（CHECK 1-15，无 CHECK 5）一致，mechanical 实跑确认。
- `check-protocol-consistency.py` CHECK 12（权威数值跨文件一致性）mechanical 实跑 PASS —— 无新数值漂移。

---

## A5: 语义降级 + 文档传播

### 「强制/必须」↔「建议/可选」有无被意外翻转？

逐段比对：
- WORKFLOW.md 核心阶段列 **加**「P6.5 独立 Judge 复核」到「不可跳」，README「P6 acceptance and the P6.5 judge are never pruned」——是**加强**（把既已强制的 P6.5 写进文档），非降级。方向正确：`phases.yaml` P6.5 有 `gate_subphase` + `retry_cap`，`role-system.md` judge 强制，CHANGELOG TAG0020 落地。
- state-machine.md ceremony 注：「ceremony **不改**状态机转移边、**不改** retry 上限、**不薄化** P5/P6（thin 档 `phases` 必须含 P5 与 P6，由 `check-routing.py` / `check-pruning.py` 双闸兜底）」——与 `phase-cards/P1-requirements.md:121-128`（thin 须四要素，缺一 → check-routing exit 1 回退 standard；full 档 `phases` 须含 P7）一致。无降级。
- LIMITATIONS 局限 4「现状」：旧「空返回时走 retry→PAUSED，不降级——…只依赖规则遵守」→ 新「空返回时走 retry → PAUSED，不降级」。核心「不降级」保留。
- LIMITATIONS 局限 5（原 6）：旧「pyyaml 是强制依赖…缺失时脚本 fail-closed（exit 1 阻断），不做静默降级」→ 新「`pyyaml` 是强制依赖，缺失时脚本 fail-closed」。「强制 / fail-closed」保留。
- git-integration.md：旧「**禁止 `--no-verify` 绕过 hook**」→ 新同句保留，且 CI backstop 重跑清单从 `check-gate.py + check-p6-provenance.py` **扩到** `+ check-events.py`（加强）。

**无意外的强制↔建议翻转。**

### LIMITATIONS 精简是否丢了真结构性内核？—— 三个点各自核查：

**(1) semantic-consistency-no-gate（旧局限 5 内核）**：**保留**。新局限 3 子弹原文：「**协议文档自身的语义一致性**没有 in-flow gate：`check-protocol-consistency.py` + SELF-GATE 是结构 / 关键词兜底，不覆盖语义；改协议靠人触发 protocol-alignment-review + 人确认 `NEEDS_HUMAN_REVIEW`。（本文档的存在就是这条的实例——一次全仓文实脱节靠人发起审计才发现。）」——内核 + 「本审计即其实例」的自指都在。删掉的是「P0 模板 4 vs 5 字段」举例 + 「为什么不在流程内加」三小点（审计计划所许，且举例本身可能已过时）。

**(2) no-CI-bypass（旧局限 8 内核）**：**保留**。新局限 3 子弹原文：「**不启用 CI 时**，`git commit --no-verify` 可绕过全部 pre-commit gate 且无自动恢复——pre-commit hook 是唯一 enforcement 点。启用 CI（GitHub / GitLab / Gitea Actions）则 backstop 重跑 `check-gate.py` + `check-p6-provenance.py` + `check-events.py` 兜底。」——「无 CI ⟹ --no-verify 无兜底且无恢复」的定稿句在。删掉的是 ~80% 的平台能力矩阵 cruft（Jenkins/CircleCI 需自适配、Gitea 环境变量未实测等）。

**(3) zero-infra-is-relative（旧局限 6 取舍边界）**：**保留**。新局限 5 首段原文：「『零基础设施』是相对的：**协议的文档部分**（阶段卡片、角色文件、状态机规则）确实零依赖…；但 **gate 脚本与 pre-commit hook 的 enforcement** 依赖 python3 + git + pyyaml（`pyyaml` 是强制依赖，缺失时脚本 fail-closed），且项目必须是 git 仓库。缺任一，协议退化为『可参考的散文』，失去把关能力。」+ `→ ADR-003` 指针保留。迁走的是可操作 Requirements 明细（→ SETUP.md / README Requirements），非边界陈述本身。

### 文档传播（CHANGELOG 等）

- CHANGELOG.md 加 `[Unreleased]` 占位节（「暂无——下个版本的变更在此累积」）。CHECK 13（CHANGELOG↔UPGRADING 章节对应）mechanical 实跑 PASS——占位节不被当作版本头。本分支是文档刷新、无版本 bump，`[Unreleased]` 占位符合约定。
- `implementer.md:33` P8 输入清单补 `P6.5-judge-verdict.md`（文件名与 `phases.yaml` P6.5 产出一致）；`verifier.md` 加「P6 产出会被 P6.5 judge 复核，`P6-evidence/` 须自足」说明段——均为 P6.5 既有机制的角色侧文档补齐，非新增要求。
- `docs/guides/project-map.md` §3.3 / §5 补 `agate next` / 派发路由 / 事件账本 + `agate-next.py` 命令行——与协议正文一致。

**A5 ALIGNED。**

---

## A6: 关键词位置 / 锚点表 + 测试真实意图

纯文档变更，CHECK 9 锚点表（`check-protocol-consistency.py` 的 `ANCHORS` 数据结构）本身未被触碰——被改的是模块级 docstring 注释文本（`:6` 的「回应 LIMITATIONS.md…」），不在 `ANCHORS` 列表内。mechanical 实跑 CHECK 9 = PASS，CHECK 10（脚本名引用漂移）= WARN（全部叙事 / 归档文件，无 ERROR）。

2 处脚本 docstring 编辑（`check-protocol-consistency.py:6`、`scripts/README.md:141`）：只把「局限 5」的悬空编号引用改为「局限 3 的一条子项」描述，脚本可执行逻辑零改动。

测试断言改动（`test_protocol_alignment_review.py`）：见 A1 第 2 点——去写死上界，真实意图（SELF-GATE.md 引用 consistency 脚本 CHECK 集 + protocol-alignment-review + HUMAN_CONFIRMED）完整保留。`bash agate/tests/scripts/count-tests.sh` = 1627（collect-only 口径），无异常漂移（该分支只改断言内容、未增删用例）。

**A6 ALIGNED。**

---

## A7: ADR 一致性

LIMITATIONS 重编号后，各局限的 `→ ADR-00X` 指针逐一对照 `agate/adr.md`：

| 局限（新编号）| ADR 指针 | adr.md 对应条目 | 匹配？ |
|---|---|---|---|
| 局限 1（gate 可信度 ≤ 测试质量）| ADR-002 | ADR-002「可判定性——gate 门槛机器可判定」（含「gate 机器可判定 ≠ 测试本身正确」）| ✓ |
| 局限 2（角色隔离是认知隔离）| ADR-006 | ADR-006「双层角色——执行角色 + 评审角色」（同源模型隔离是认知层非真正独立）| ✓ |
| 局限 3（主 Agent 判断力单点故障）| ADR-001 + ADR-005 | ADR-001「隔离性——主 Agent 不写产出」+ ADR-005「改动性质决定流程」| ✓ |
| 局限 5（原 6，运行时依赖）| ADR-003 | ADR-003「最小约定——不绑定技术栈」| ✓ |
| 局限 4 / 局限 6 | 无指针 | 原文亦无 | ✓（不回归）|

**所有 ADR 指针在重编号后仍准确。** 无本次改动应触发新 ADR 的情形——这是文档 cleanup（压缩诚实边界陈述 + 补已落地机制的门面覆盖），不含未记录的架构决策。P6.5 / `agate next` / ceremony / 派发路由的架构决策分别在 TAG0020 / TAG0027 / TAG0019 / TAG0034 的设计文档 + CHANGELOG 已记录，本轮只是把它们写进协议正文。

**A7 ALIGNED。**（A7 三态规则下不存在 MISALIGNED；无 NEEDS_HUMAN_REVIEW。）

---

## 机械兜底实跑结果

| 检查 | 命令 | 结果 |
|------|------|------|
| 协议结构一致性 | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **exit 0**，**0 ERROR**（362 WARNING，全部在叙事 / 冻结快照文件——CHANGELOG 历史条目、`agate-alignment-review-2026-08-*.md`、`agate-workspace/tasks/TAGxxxx/` 归档产出、批 E 归档后旧路径引用；审计 §8-6 预测「+约 30」已兑现）。CHECK 1-15 全 PASS 或 WARN，无 FAIL。 |
| 结构一致性 | `python3 agate/scripts/check-structure-consistency.py` | **exit 0**，S1-phases / S2-workflow / S3-cards / S4-scripts / S5-schema / S6-references / S0-numbers 全 **OK** |
| pytest unit + regression | `pytest agate/tests/unit agate/tests/regression -n auto` | **1509 passed, 2 skipped** |
| pytest integration | `pytest agate/tests/integration -n auto` | **94 passed** |
| 针对性（agate-summary / protocol-alignment / regression）| `pytest …test_agate_summary.py …test_protocol_alignment_review.py …/regression` | **46 passed** |
| 测试计数 | `bash agate/tests/scripts/count-tests.sh` | 1627（collect-only 口径），exit 0，无异常漂移（分支只改断言、未增删用例）|

全绿。

---

## 前两轮独立评审 must-fix 折入核查

`review-doc-consistency-audit-2026-09.md`（计划评审，Verdict REVISE）+ `review-doc-refresh-execution-2026-09-10.md`（执行评审，Verdict REVISE，5 处必修）——批 F（commit `bef79e6`）声称折入执行评审的 5 处必修。逐一验证当前 HEAD：

1. `agate/SETUP.md:177` 「out-of-scope / 被派发执行环境」→ 已改为「Codex 支持完整 P0-P8（有原生 `spawn_agent` 子代理派发）…但没有 `.claude/agents/` 等价的 orchestrator 软链注册步骤（同 DSH——DSH 用 preset）」。**已修** ✓
2. README.md / README.zh-CN.md / WORKFLOW.md 平台表脚注「Codex is a dispatch target」→ 现为「DSH and Codex have no `.claude/agents/`-equivalent orchestrator-symlink registration step…it still runs full P0-P8 with native `spawn_agent` dispatch」/ 中文对应。**已修** ✓
3. `design-dispatch-routing.md:7`（头部「相关」行）「局限 2/4/6」→「局限 2/4/5；局限 5 为原局限 6」。**已修** ✓
4. `agate/tests/ENV-SENSITIVE-TESTS.md:24`「局限 3『降级缓解』节」悬空 → 改指「`agate/phase-cards/P5-verification.md` 描述的 P5 机械化回归判定机制（…；`LIMITATIONS.md` 局限 3 亦提及为一条缓解）」。**已修** ✓
5. `docs/design-notes/README.md` 索引行 `doc-consistency-audit-2026-09.md` 状态 → 「**已执行**（批 A-E，2026-09-10，分支 `docs/protocol-doc-refresh`…）→ 历史快照」，与该文档正文新增「执行状态」节对齐。**已修** ✓

执行评审的非阻塞建议（`agate advance` 与 `agate next` 并列的不精确）在本轮 dispatch-protocol.md / orchestrator-template.md 的新增段里**已规避**——两处只用 `agate next` 表述前进查表，回退明确走 `agate-retreat-to.py`；state-machine.md:329「`agate advance` 是回退侧的引导壳」措辞准确。

---

## 总结论

**aligned-with-nits**

- **MISALIGNED 项**：无。
- **NEEDS_HUMAN_REVIEW 项**：无。
- **NIT（不阻塞，建议后续处理）**：
  1. `agate/assets/review-roles/protocol-alignment-review.md:12` 触发条件行未同步 `SELF-GATE.md` 新增的 `agate/rules/*.yaml`（文档-文档漂移，1 行文案可补）。
  2. `agate/scripts/commit-msg-self-gate.py:39` 正则 + `:77` WARNING 文案未含 `agate/rules/*.yaml`——`SELF-GATE.md` 已列该触发面（对齐 CHANGELOG v0.71.0 + CHECK 15），辅助提醒 hook 落后；因该 hook 明确仅「辅助提醒 / WARNING 不拦截」，判 NIT 而非 MISALIGNED，正则修正属行为改动宜单独任务。
  3. `docs/design-notes/README.md` 中 `design-dispatch-routing.md` 索引行状态措辞未按 §8-4 统一为「已落地（TAGxxxx，vX.Y.Z）」格式——cosmetic。

核心判断：这确是一次纯文档一致性刷新，7 个 commit 无一夹带 gate 逻辑 / 状态机转移 / retry 上限 / exit code 约定的实质改动；4 个「疑似夹带」点（agate-summary 死链修复、测试去硬编码、baseline hash bump、LIMITATIONS 精简）逐一核实均为文档改动的必然连带或 UX 修复。LIMITATIONS 8→6 节精简未丢任何结构性内核（三个内核逐条确认折入局限 3 / 局限 5）。所有 ADR 指针重编号后仍准确。机械兜底全绿（0 ERROR / S1-S6 OK / 1603 tests pass）。前两轮评审的 5 处 must-fix 已全部折入。三条 NIT 均为轻量文案层面，不构成合并阻塞。
