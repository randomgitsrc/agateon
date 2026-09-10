# 独立评审：`doc-consistency-audit-2026-09.md`

> 评审对象：`docs/design-notes/doc-consistency-audit-2026-09.md`（2026-09-10 初稿）
> 评审方式：逐条重跑审计依赖的 grep / 文件读取，对照当前仓库（v0.71.0，main）。不采信审计结论，独立复核。
> 评审人：独立评审 subagent（2026-09-10）

---

## Verdict：**REVISE**

计划方向正确、批次划分大体合理、80% 的事实断言复核通过。但有 **3 处必须在执行前修正**：

1. **§3-A（Codex 平台定位）分析错了权威源**。审计以 `SETUP.md` 为准判 "Codex 非完整宿主"，但协议自己声明的平台适配权威源是 `platform-notes.md`（`WORKFLOW.md:496`、`platform-notes.md:3`），而 `platform-notes.md:57/63` 明写 Codex "P0-P8 全部阶段可执行" + 原生 `spawn_agent` 派发。审计的修法（把 `WORKFLOW.md` 平台表 Codex 降级为 "非宿主"）会制造一个**新的**跨文档矛盾。而且审计**漏了**真正的对称缺陷：`WORKFLOW.md` 平台表有 Codex 无 DSH，`README` 平台表有 DSH 无 Codex —— 两张表行集不一致才是核心问题。
2. **两处 §2 事实断言站不住**：`state-machine.md`「Pre-commit 检查全景」节**已经是**指向 `WORKFLOW.md` 的干净指针（`state-machine.md:247-249`），不含任何旧 check 编号 —— 审计说它"旧 check 编号"是 **REFUTED**。`CONTEXT.md` 残留编号只有 `T080`，**没有 `T001`** —— 审计的 "`T080`/`T001`" 里 T001 是 **REFUTED**。
3. **§2 裁级与 §5 批次计划自相矛盾**：§2 把 `git-integration.md` / `CONTEXT.md` 判 "重写"，§5 批 4 却说 "三条规则骨架保留" / "术语表补齐 5 组缺失词条"（= 增补，非重写）。骨架都在、都该留，正确裁级是 **大改**（git-integration.md）/ **局部修补~大改**（CONTEXT.md）。

外加 3 处应补强（非阻塞）：漏评 `orchestrator-template.md`（主 Agent 唯一必读文件，P6.5 缺席）；LIMITATIONS 局限 5 有真实内核不宜整删；局限 6 迁走会削弱 "零基础设施" 的诚实边界。

---

## §1 事实核查结果

| # | 审计断言 | 结论 | 证据 |
|---|---|---|---|
| 1 | §2/§3-C：`state-machine.md` / `WORKFLOW.md` / `dispatch-protocol.md` 对 `agate next`/`advance` 命中 0 | **CONFIRMED** | `grep -nE 'agate next\|agate advance\|agate-next\|agate_next'` 三份文件全部 exit 1（无命中）。`loop-orchestration.md` 命中 9（`loop-orchestration.md:49,236,242-265`）。`phase-cards/` / `rules/` 也 0 命中。 |
| 2 | §3-A：`WORKFLOW.md` 平台表写 `Codex ✅ ✅ 完整 P0-P8` | **CONFIRMED（原文）** | `WORKFLOW.md:152-156` 表体：OpenCode / Claude Code / Codex 三行均 `完整 P0-P8`；**无 DSH 行**。 |
| 3 | §3-A：`README` / `README.zh-CN` 平台表无 Codex 行 | **CONFIRMED** | `README.md:68-72`、`README.zh-CN.md:68-72`：OpenCode / Claude Code / **DSH** 三行，无 Codex。 |
| 4 | §3-A：`SETUP.md` 步骤 2-Codex 说 "out-of-scope / 被派发执行环境" | **CONFIRMED（原文）** | `SETUP.md:177`：「Codex 无『宿主 orchestrator 注册』步骤（out-of-scope）——它作为 agate 的被派发执行环境接入」。 |
| 5 | §3-A：三处"对不上"、且**应以 SETUP.md 为准**、Codex = 非完整宿主 | **PARTIALLY-CONFIRMED（矛盾属实，定性与修法错）** | 矛盾属实但审计选错权威源。`WORKFLOW.md:496`「详见 platform-notes.md……权威唯一来源」；`platform-notes.md:3`「平台适配权威源」；`platform-notes.md:57`「本地开发环境 ✅ 完整 \| P0-P8 全部阶段可执行」；`platform-notes.md:63`「原生子代理派发 ✅……会话内工具 `spawn_agent`」。按声明的权威源，Codex **可**跑完整 P0-P8 且有原生派发。SETUP 的 "out-of-scope" 实为 "无 `.claude/agents/` 等价的宿主注册步骤"（与 DSH 同类，DSH 用 preset —— 而 DSH 在 README 里照样是 "完整 P0-P8"）。审计还**漏了** `WORKFLOW.md` 平台表缺 DSH 行。 |
| 6 | §3-B：`README`（both）"eight phases (P1→P8)" 漏 P6.5 | **CONFIRMED** | `README.md:19`「eight phases (P1 requirements → … → P7 consistency → P8 release)」；`README.zh-CN.md:19`「八个阶段……P6 验收 → P7 一致性 → P8 发布」。均无 P6.5。 |
| 7 | §3-B：`README`（both）"How it works" 流程图漏 P6.5 + 漏事件账本 | **CONFIRMED** | `README.md:52-53` / `README.zh-CN.md:52-53`：「P5 verifier → P6 verifier → P7 consistency-reviewer」，无 P6.5 judge，无 `gate-events.jsonl`。 |
| 8 | §3-B：`README`（both）信任分类表 + mitigation 段无 P6.5 | **CONFIRMED** | `README.md:101-106` / `README.zh-CN.md:99-105`：self-authored gate 行 `P1, P2, P6, P7`；mitigation 段只列「evidence-existence checks, objective provenance audits, BDD count cross-checks」，无独立 judge。 |
| 9 | §2：`README.zh-CN` 小节标题仍全英文 | **CONFIRMED** | `README.zh-CN.md:48`「## How it works」、`:66`「## Supported platforms」、`:99` 前后「## Design principles」「## Known limitations」等仍英文。 |
| 10 | §2：`agate-summary.py` L170 指向 `~/.agate/CHANGELOG.md`，且 `agate/CHANGELOG.md` 不存在 | **CONFIRMED** | `agate/scripts/agate-summary.py:170`「3. 读 ~/.agate/CHANGELOG.md……」。`ls agate/` 无 `CHANGELOG.md`（只在仓库根）。legacy 布局 `install.sh:53` `LINK_TARGET="$INSTALL_DIR/agate"` → `~/.agate/CHANGELOG.md` = `<clone>/agate/CHANGELOG.md` = **死链**。版本布局（`install.sh --versions`，TAG0032）下正确路径是 `~/.agate/current/CHANGELOG.md`（worktree 全量 checkout 含根 CHANGELOG），`~/.agate/CHANGELOG.md` 仍不存在。无其它脚本解析该路径 —— 只此一处 startup 提示串。 |
| 11 | §2：`SELF-GATE.md` 通篇 "CHECK 1-9"，实际脚本到 CHECK 15 | **CONFIRMED** | `SELF-GATE.md:4`「agate 自身用 CHECK 9 + LLM 语义审查」、`:23`「确认 CHECK 1-9 无 ERROR」、`:29`「## Layer 0：CHECK 9」。`check-protocol-consistency.py:1272-1367` 有 CHECK 15（"数据面平台名扫描"，扫 `rules/*.yaml` + `rules/schema/*.json`）。 |
| 12 | §2：`SELF-GATE.md` 触发条件漏 `agate/rules/*.yaml` | **CONFIRMED（措辞微误）** | `SELF-GATE.md:14-18` 触发条件列 `agate/scripts/*.py` / `agate/*.md` / `agate/**/*.md`，**无** `agate/rules/*.yaml`。（审计写成 "`agate/*.py`+`agate/*.md`" 略不精确，但核心成立。）`CHANGELOG.md` v0.71.0 条目明写 `dispatch-tiers.yaml`「改它走 SELF-GATE」；CHECK 15 专扫数据面 —— rules/*.yaml 确应是触发面。 |
| 13 | §2：`CONTEXT.md` 术语表缺 5 组词条 | **CONFIRMED** | `CONTEXT.md:6-33` 全表无 `judge` / `P6.5` / `judge verdict`，无 `gate-events.jsonl` / 事件账本，无 命令流存活检测，无 `agate next`/`advance`，无 dispatch routing/tier。（`ceremony` 词条 `:30` 有 —— 审计未误列。） |
| 14 | §2：`CONTEXT.md` 残留 `T080`/`T001` | **PARTIALLY-CONFIRMED** | `CONTEXT.md:16` 有 `T080`（NEED_CONFIRM 演进注）。全文 `grep -E 'T[0-9]{3}'` **只此一处** —— **无 `T001`**。T001 部分 REFUTED。 |
| 15 | §2：`CONTEXT.md` gate exit code 词条未含 `gate_pass_exit` / pass_set 三态 | **CONFIRMED，且比"缺"更严重 —— 是矛盾** | `CONTEXT.md:10`「通过(0)/不通过(1)/需人工判断(2)」、`:21`「0=通过，1=不通过，2=需人工判断」。但 `loop-orchestration.md:246`「exit 2 是多数 phase 正常通过码 ∈ pass_set」、`check-gate.py:7-11`「pass 判定以 phases.yaml gate_pass_exit 为准……agate-next.py 消费方按 gate_pass_exit pass_set 区分正常通过与真暂停」、`WORKFLOW.md:305-318` 阶段表反复以 "exit 2" 作 PASS 条件。CONTEXT.md 把 exit 2 一律说成 "需人工判断" 与协议其余部分冲突。附带：`CONTEXT.md:10` 与 `:21` 是两条近重复词条（"gate" / "gate exit code"），审计未指出冗余。 |
| 16 | §2：`git-integration.md` 全篇 `v0.4 hardening-roadmap` 框架 + `P1.7`/`P2.3-P2.5`/`P2.12` 旧编号 + 残留 `T002`/`T011`/`T042` | **CONFIRMED（"全篇"夸大）** | 旧编号：`git-integration.md:166`(P2.15) `:168`(P1.7) `:170`(P2.3-P2.5) `:172`(P2.11) `:173`(P2.12) `:174`(P1.6)。旧框架标题：`:160`「## Hardening-roadmap 集成（自 v0.4 引入）」`:162`「触发 9 项 pre-commit 检查」。旧任务 ID：`:39,42`(T002) `:53`(T011) `:181`(T042)。缺 `self-gate-review:` / `gate-events.jsonl` / `--no-ff` / 禁 squash（`grep` 全 exit 1）。**但**「全篇」不成立：`:19-156`（三条规则骨架、phase 字段语义、wf() 前缀判定、多 Agent 并发）当前有效，旧框架只集中在 `:160-189`（约占 15%）。 |
| 17 | §4：局限 5 "不是限制" | **REFUTED（有真实内核）** | 详见 §2-LIMITATIONS。`:82`「一致性检查是语义判断，不可机器判定」+ `:87`「语义一致性仍非 100% 自动化——需要人触发审查 + 人确认」是与局限 1/3 同类的结构性断言。CHECK 15 是**结构/关键词**兜底（`:87` 自承 "结构兜底，锚点表关键词存在性"），不做语义 —— 审计 "→ 基本闭环" 是过度声明。且 `check-protocol-consistency.py:6` 与 `agate/scripts/README.md:141` 的 docstring 按编号引用「局限 5」，整删会留悬空引用。 |
| 18 | §4：局限 8 "不是限制" | **PARTIALLY-CONFIRMED** | `LIMITATIONS.md:126-136` 约 80% 是平台能力矩阵（GitHub/GitLab/Gitea 检测细节）—— 确是能力声明。但 `:132`「不使用 CI 的项目完全依赖 pre-commit hook，无兜底机制」是真实结构性局限（`--no-verify` 可绕过且无恢复）。审计已承认要留这一句并入局限 3 —— **有条件同意删**：前提是这一句确实落进局限 3，而局限 3 又被审计判 "狠删枝蔓"，合并动作必须显式写进批次 checklist，否则内核丢失。 |
| 19 | §4：局限 6 是依赖披露 / 不是限制 | **PARTIALLY-CONFIRMED** | `LIMITATIONS.md:89-98` 的分点（bash 薄壳、Pillow 可选）确是披露。但 `:99`「这些依赖是 agate 作为『零基础设施文档协议』的代价」承担的是 README `:94`「Zero infrastructure — any agent that can read files can use Agateon」这句市场宣称的诚实边界。迁成 README/SETUP 的 "Requirements" 清单会把 "设计取舍的诚实自陈" 降级为 "安装前置清单" —— 见 §2-LIMITATIONS 的建议。 |
| 20 | §2：`CHANGELOG.md` 顶部无 `## [Unreleased]` | **CONFIRMED** | `CHANGELOG.md` 头部直接跳到 `## [0.71.0] - 2026-09-10`。`check-changelog.py:44-66`：NORMAL 模式无 `[Unreleased]` 区域 → `sys.exit(1)`；`:52-62` post-bump 模式改检最新版本段非空。`pre-commit-gate.py:479` CHANGELOG 检查仅 P8 触发。→ 加回空 `[Unreleased]` 符合 Keep-a-Changelog 且避免下个任务 P8 NORMAL 模式踩 exit 1。审计 "小瑕疵 + 待确认" 处理正确。 |
| 21 | §2：根 `AGENTS.md` 引 `agate-next-card.py` 与 `agate-next.py` 是两个脚本 | **CONFIRMED** | `agate/scripts/` 下 `agate-next.py` / `agate-advance.py` / `agate-next-card.py` 三个独立脚本共存。`AGENTS.md:55` 引 `agate-next-card.py`（卡片注入工具，与推进 CLI 无关），引用无误。 |
| 22 | §2：`state-machine.md`「主 Agent 的单步执行」节仍纯手工流程 | **CONFIRMED** | `state-machine.md:322-398` 单步函数从头到尾手工「读状态→派发→亲跑 gate→算下一状态→写回」，无 `agate next`/`advance`。`:390` 只说 "谁来反复调用？三种方式（见 loop-orchestration.md）"。 |
| 23 | §2：`state-machine.md`「Pre-commit 检查全景」节旧 check 编号 | **REFUTED** | `state-machine.md:247-249`：该节**已重构为指针** ——「完整清单……见 `WORKFLOW.md`「Pre-commit 检查总览」——权威唯一来源，本文件不重复维护」。节内无任何 `P1.x`/`P2.x` 编号。（`:215`、`:244` 的 `P2.9`/`P2.11` 是行内注释锚，不在此节，且与 git-integration.md 同类，属另一回事。） |
| 24 | §2：`WORKFLOW.md`「风险矩阵（P2.13）」「Pre-commit 总览（hardening Phase 1-2）」旧框架 | **CONFIRMED** | `WORKFLOW.md:273`「### 风险矩阵（P2.13）」、`:281`「(P2.14)」；`:335`「## Pre-commit 检查总览（hardening-roadmap Phase 1-2 已落地）」。**但**该表体 `:337-351` 已用当前脚本名（`check-routing.py` 等）+ TAG0019 + RM-AG0042，只是标题与个别编号旧。 |
| 25 | §2：`WORKFLOW.md` ceremony 只一处带过、裁剪节无档位词表 | **CONFIRMED** | `grep -nE 'thin\|standard\|full\|档位\|ceremony'` 全文**仅命中 `WORKFLOW.md:349`**（check-routing.py 描述里）。`:232-249` 可裁剪节只讲 design_trivial / follows_existing_pattern / single_agent_mode，无 thin/standard/full。 |
| 26 | §2：`rules/*.yaml` 一致、`phases.yaml` 有 P6.5 | **CONFIRMED** | `phases.yaml:123-131` `- id: P6.5 / name: 独立 Judge 复核 / retry_cap: 2`。retry_cap 序列 P0=3/P1=3/P2=3/P3=2/P4=3/P5=2/P6=2/P6.5=2/P7=2/P8=2 与 `state-machine.md:403-412` 表（无 P0/P6.5 行）一致，无漂移。 |
| 27 | §2：`dispatch-protocol.md` routing/cmdstream/judge 均覆盖，仅 0 处 agate next/advance | **CONFIRMED** | `grep -c`：judge=16、派发路由/routing=4、命令流/存活/cmdstream=10；`agate next`/`advance`=0。 |
| 28 | §2：`loop-orchestration.md` / `role-system.md` "基本一致" | **CONFIRMED（公正）** | `loop-orchestration.md:49,236,242-265` 深度整合 `agate next`（TAG0027 §3.7）+ P6.5 前进特例 + gate_pass_exit/pass_set。`role-system.md:51,64,119,219` 有 judge/P6.5/ceremony/full 档。两者均未提 RM-AG0060 派发路由，但路由归 dispatch-protocol.md 域，可接受。 |

---

## §2 裁级质疑（逐文件同意/不同意）

### `state-machine.md` —— 审计判「大改」：**同意（偏重可接受）**

骨架（状态存哪 / 状态机定义 / 抗中断 / 回退 / 评审迭代 / 重试上限）**当前有效**：P6.5 已深度织入状态机定义（`:74-78,139,151-156,414-418,485-486`），provenance 校验、CHECK 12 重试表锚点都是当前口径。真实缺口是**增量**而非结构性腐烂：

- `agate next`/`agate advance` 完全缺席（`:322-398` 单步节纯手工）；
- ceremony 对转移的影响缺席（`grep ceremony` = 0 命中）；
- 命令流存活检测 / dispatch routing 无一句指针（各 0 命中）。

这是 "重写受影响 3-4 节 + 补指针"，"大改" 站得住。**但审计 §2 表里 "「Pre-commit 检查全景」节旧 check 编号" 这条要删**（§1 #23，已是干净指针）。删掉这条后其实更接近「局部修补 ×3 + 大改 1 节（单步执行）」。

### `WORKFLOW.md` —— 审计判「大改」：**同意**

阶段总览表当前（含 P6.5 行 `:310` + S1/S2 锚点 + 当前 gate 命令）、pre-commit 表体当前、核心原则当前。旧的是：平台表（§3-A）、`风险矩阵（P2.13）` / `hardening Phase 1-2` 标题措辞、裁剪节无 ceremony 词表、无 agate next、无 cmdstream/routing 指针。全是节级翻新 + 增补，非结构重写。"大改" 正确。

### `git-integration.md` —— 审计判「重写」：**不同意，应为「大改」**

- 193 行里旧框架只占 `:160-189`（约 30 行）。`:19-156` 的三条规则骨架 + phase 字段语义 + wf()/feat() 判定表 + 多 Agent 并发四策略当前全部有效，**应保留**。
- 审计**自己**在 §5 批 4 写「三条规则骨架保留（commit 由主 Agent / 一阶段一 commit / push 分档位），『9 项 pre-commit 检查』表换成当前检查集」—— 这正是 "大改" 的定义，不是 "重写"。§2 裁级与 §5 计划打架。
- 修法：重写 `:160-189` 一节（旧编号 → 当前检查集 / 指向 WORKFLOW 权威表）、补 `self-gate-review:` trailer + `gate-events.jsonl` 入库 + 发布 PR `--no-ff`/禁 squash、清 3 个旧任务 ID。骨架不动。

### `CONTEXT.md` —— 审计判「重写」：**不同意，应为「局部修补~大改」**

- 34 行的术语表，结构（术语 / 定义 / 首次定义位置 三列）完全健康，**应保留**。
- 需要的动作：补 5 组缺失词条、修 `:16` 的 T080 注、合并 `:10`/`:21` 两条近重复 gate 词条并改正 exit-2 语义（对齐 `loop-orchestration.md:246`）、逐条核对 "首次定义位置" 章节名仍存在。这是增补 + 订正，不是 "照当前机制重写"。
- 审计 §5 批 4 的动作清单（"术语表补齐 5 组缺失词条；……每条『首次定义位置』核对现存章节名"）同样是增补口径 —— 再次与 §2 "重写" 裁级打架。

### `LIMITATIONS.md` 局限 5 —— 审计判「整删」：**不同意，压缩保留**

**真实内核**（会随整删丢失）：协议文档**语义层**自一致性没有 in-flow gate，靠 "人记得触发 protocol-alignment-review + 人确认 NEEDS_HUMAN_REVIEW"。CHECK 1-15 是结构/关键词兜底（`:87` 自承），**不覆盖语义**。这条与局限 1（测试质量上限）、局限 3（self-authored）同族 —— 都是 "纯文档协议 + 可判定 gate" 路线的结构性产物。**本次审计本身就是这条局限的实例**：一次全仓文实脱节，是靠人在旁边发起审计发现的，没有任何流程 gate 拦住它。
另外：`check-protocol-consistency.py:6` 和 `agate/scripts/README.md:141` 的 docstring 明确「回应 LIMITATIONS.md『局限 5』」—— 整删会留下按编号的悬空引用（且这俩不在审计 §5 批 5 的连带清单里）。
**建议**：压到 3-4 行并入局限 1 或局限 3 邻域：「协议文档的**语义**自一致性无 in-flow gate；结构层由 `check-protocol-consistency.py` + SELF-GATE 兜底，语义层靠人触发对齐审查 + 人确认。未根治。」删掉 P0 模板 "4 字段 vs 5 字段" 那个可能自身已过时的例子、删 "为什么不在流程内加" 三小点。

### `LIMITATIONS.md` 局限 8 —— 审计判「整删」：**有条件同意**

删平台矩阵 cruft 没问题。但 "无 CI = `--no-verify` 可绕过全部 gate 且无恢复" 这个内核必须**明确落进**局限 3（或局限 1）的正文，不能只在批次说明里写 "并入" 就算数 —— 局限 3 同时被审计要求 "狠删枝蔓"，两个动作同批做，内核极易在 diff 里蒸发。批次 checklist 要显式列出这一行的目标位置和最终措辞。

### `LIMITATIONS.md` 局限 6 —— 审计判「迁 README/SETUP + 留一句」：**部分不同意**

迁 Requirements 清单到 README/SETUP 是对的（那里本就该有）。但**不要把 LIMITATIONS 里的那句只剩 "gate 需 python3+git+pyyaml"**。要保留 "取舍诚实自陈" 的功能：

> 局限 6（压缩版建议）：「'零基础设施' 是相对的 —— 文档本体确实零依赖，但 gate / hook 的**强制力**依赖 python3 + git + pyyaml + git 仓库。缺任一，协议退化为『可参考的散文』，失去 enforcement。这是用通用工具替代专用服务的代价，非缺陷，但采用者要知道边界在哪。」

Requirements 清单（可操作）+ LIMITATIONS 一段（讲边界）二者并存，不是二选一。审计当前写法是纯搬迁，会让 README `:94` 那句 "Zero infrastructure" 失去唯一的诚实注脚。

---

## §3 审计遗漏项（每项带 file:line 证据 + 建议补进审计文档的位置）

1. **`WORKFLOW.md` 平台表缺 DSH 行**（配 §3-A）。`WORKFLOW.md:152-156` 只有 OpenCode / Claude Code / Codex / Claude Project；`README.md:70-72` 有 DSH 无 Codex。**两张门面平台表行集根本不一致** —— 这比 "Codex 是不是宿主" 更硬。建议 §3-A 重写为："四个已验证平台（OpenCode / Claude Code / DSH / Codex）在两张平台表里各缺一个，先统一成同一行集，再按 `platform-notes.md`（声明的权威源）填 '完整度' 列。"

2. **§3-A 权威源选错**。`WORKFLOW.md:496` + `platform-notes.md:3` 声明 `platform-notes.md` 是平台适配 "权威唯一来源"；`platform-notes.md:57` 写 Codex "P0-P8 全部阶段可执行"、`:63` 写原生 `spawn_agent` 派发。审计 §3-A "以 SETUP.md 为准 → Codex 非完整宿主" 与之冲突，且其修法（`WORKFLOW.md` 平台表 Codex 改 "非宿主"）会让 `WORKFLOW.md` 与 `platform-notes.md` 对立。建议 §3-A 改判：以 `platform-notes.md` 为准（Codex = 支持宿主，有原生派发），`SETUP.md:177` 的 "out-of-scope" 收窄为 "无 orchestrator 软链注册步骤（与 DSH 同 —— 无 `.claude/agents/` 等价物）"，`README` 平台表**补 Codex 行**。

3. **`agate/orchestrator-template.md` 完全未评**（审计只在 §7-Q5 顺带问 assets/，template 连问都没问）。这是**主 Agent 唯一必读的文件**（`mode: primary`，标准接入是软链进 `.claude/agents/`）。`orchestrator-template.md:` 的 phase-card mapping 表（"开始" 节第 5 步）列 P0-P8，**无 P6.5 行** —— 只读 template + phase 卡片的编排 Agent 不会知道要在 P6.5 派 judge。全文 0 处 `agate next`/`advance`、0 处 P6.5/judge、0 处 dispatch routing。"只有你能写的文件" 表也没有 judge dispatch-context。建议审计新增一行：`agate/orchestrator-template.md | 大改（或局部修补 ×3）| phase-card mapping 表补 P6.5 行 + 补 agate next/advance 推进入口指针 + 写文件表补 judge dispatch-context`，并把它提到批 1 或批 2（比 `phase-cards/README.md` 优先级高）。

4. **CONTEXT.md gate exit-code 是跨文档矛盾，不只是 "缺"**。`CONTEXT.md:10,21`「2=需人工判断」vs `loop-orchestration.md:246`「exit 2 是多数 phase 正常通过码 ∈ pass_set」vs `WORKFLOW.md:305-318` 阶段表以 "exit 2" 为 PASS。建议 §2 CONTEXT.md 行 + §5 批 4 明确写 "订正（非增补）exit-2 语义"，并合并 `:10`/`:21` 两条冗余词条。

5. **`verifier.md`（P6 角色）不知道有下游独立 judge**。`agate/assets/execution-roles/verifier.md`（2026-09-04）phases `[P5, P6]`，全文 0 处 P6.5/judge。judge 以 fresh context 只读 `P6-evidence/` 逐条重验 —— verifier 应被告知 "你的证据文件是独立 judge 的**唯一**输入，必须自足"。建议 §7-Q5 的结论里点名 verifier.md 补一句 handoff 说明。

6. **§5 批 5 "局限 N 编号连带" 清单不全 + 有幻影项**。实际按编号引用 `局限 N` 的位置（`grep -rn '局限 [0-9]'`，排除 LIMITATIONS.md 自身）：
   - 局限 2：`adr.md:461,473`、`SETUP.md:220`、`UPGRADING.md:154`
   - 局限 3：`git-integration.md:186`、`WORKFLOW.md:358`、`README.md:106`、`README.zh-CN.md:105`、`agate/tests/ENV-SENSITIVE-TESTS.md:24`
   - 局限 4：`dispatch-protocol.md:133`
   - 局限 5：`agate/scripts/check-protocol-consistency.py:6`、`agate/scripts/README.md:141`
   审计 §5 批 5 漏了 `SETUP.md` / `UPGRADING.md` / `tests/ENV-SENSITIVE-TESTS.md` / 两个 scripts 侧引用；且列了 `role-system.md`（实际 0 处按编号引用，幻影项）。好消息：若只删局限 5、8，则局限 1-4 编号不变、现存对 2/3/4 的引用全部存活；真正会断的是**对 "局限 5" 的两处 scripts 引用**（又一条 "别整删局限 5" 的理由）。

7. **retry-cap 数字：跨文档一致（审计未声称矛盾，此处为确认排除）**。`state-machine.md:403-412` 表 = `phases.yaml:28-161` retry_cap = `git-integration.md:173`「P3/P5/P6/P7/P8 ≥2、P1/P2/P4 ≥3」= `WORKFLOW.md:409`「按阶段 2-3 次」。`rules/state-transitions.md:58` 指回 state-machine.md 为唯一权威源。无漂移 —— 这一维度干净，审计不必新增条目，但评审已核。

8. **`project-map.md`（`docs/guides/`）轻度过时**。`docs/guides/project-map.md`（2026-08-30）有 P6.5 / judge / check-routing.py（`:34,45,57,61`），但**无** `agate next`/`advance`、**无** RM-AG0060 派发路由、**无** 命令流存活检测。审计把它列为 "连带" 但没说要改哪节。建议 §5 批 1 连带项写明："`project-map.md` §3.1 阶段流已含 P6.5（无需改）；工具清单节（`:57`）+ 若有 CLI/派发章节，补 `agate next` 与 dispatch routing。" 注：`project-map.md` 在审计声明的范围外（"不含 docs/ 内部资料"），作 "连带" 处理本身合规。

9. **`implementer.md`（P8 releaser）输入清单不含 judge verdict**。`agate/assets/execution-roles/implementer.md:33`：P8 输入列 `P5-test-results/ + P6-acceptance.md + P7-consistency.md`，无 `P6.5-judge-verdict.md`。小瑕疵，可并入 §7-Q5 结论。

10. **审计自身的范围声明与批次不符**。审计头部 §范围 写 "含 `agate/phase-cards/`"，但 §2 逐文件表只评了 `phase-cards/README.md`，8 张 phase 卡片本体一张没评。至少 `P6-acceptance.md` 卡片（judge 借它派发）值得确认。建议审计要么补评 phase 卡片，要么把范围声明收窄为 "`phase-cards/README.md` + 索引"。

11. **`SELF-GATE.md:4` 与 `:29` 描述 CHECK 9 为 "the backstop"**，措辞把 CHECK 9 当唯一结构兜底。除 `:23` 的 "CHECK 1-9" 外，`:4`「agate 自身用 CHECK 9 + LLM 语义审查」与 `:31`「CHECK 9 扫描协议文档声明的规则」也需一并改（审计 §5 批 6 只提了 "CHECK 1-9 → CHECK 1-15"，漏了 `:4` 和 `:31` 两处）。建议：统一改为 "CHECK 全集（不写死上界）" 并把 `:4/:29/:31` 三处一起过。

---

## §4 批次计划评估（§5）

**总体：6 批划分基本合理，"按主题批不按文件逐个补" 的原则正确。** 具体问题：

| 批 | 评估 |
|---|---|
| 批 1（跨文档一致性 + summary 死链） | 范围合适、确实影响面最大先做。**必须先修 §3-A 的定性**（见 §3 遗漏 1/2），否则批 1 会把一个错的 Codex 定位写进三处门面。建议把 `orchestrator-template.md` 的 P6.5 mapping 补进本批（一行改动，主 Agent 每次会话读）。 |
| 批 2（state-machine.md 大改） | 合理。删掉 "「Pre-commit 检查全景」节旧编号" 这个不存在的工作项（§1 #23）。ceremony / cmdstream / routing 三条按审计说的 "正文归各自权威源、这里只留指针" 是对的。 |
| 批 3（WORKFLOW.md 大改） | 合理。与批 1 的 3-A 有重叠（平台表）—— 审计已注明 "并入批 1 或此批一并做"，建议**明确归批 1**（平台表三处必须一次同步，跨批改同一批对象易漏）。 |
| 批 4（CONTEXT.md + git-integration.md "重写"） | **裁级下调为 "大改"**（见 §2）。动作清单本身没问题（已是增补口径）。两份文件耦合弱，可以但不必同批；同批的唯一理由是 "都引用旧 check 编号，换成当前检查集时口径统一"，成立。 |
| 批 5（LIMITATIONS 精简重构） | **改动最大、风险最高的一批**。局限 5 改 "压缩保留" 不整删；局限 8 内核落点写死；局限 6 保留取舍陈述句。连带 grep 清单按 §3 遗漏 6 补全（+SETUP/UPGRADING/ENV-SENSITIVE-TESTS/两处 scripts，-role-system 幻影）。`check-protocol-consistency.py:6` docstring 若局限编号变要同步。 |
| 批 6（收尾小瑕疵） | 合理。`SELF-GATE.md` 加 `:4`/`:31` 两处（§3 遗漏 11）。`install.sh` 默认目录名 —— 同意审计的保守做法（只改注释/提示文案，不动 `AGATE_REPO_DIR` 默认值，避免破坏存量用户路径）。 |

**隐藏依赖 / 分组问题**：

- **批 1 ⟶ 批 5 的编号依赖**：批 1 要给 `README` 的信任表 + mitigation 段补 "P6.5 judge + 指 LIMITATIONS 局限 3"。若批 5 重排 LIMITATIONS 编号，批 1 新加的 "局限 3" 引用可能失效。**批 1 引用 LIMITATIONS 时要用最终编号** —— 要么批 5 先冻结编号方案再做批 1，要么约定 "局限 1-4 编号不变"（只删 5/8 时成立）。审计 §6 提到这个连带面但没给出执行顺序约束。
- **批 2/3/4 都要 "把旧 check 编号换成当前检查集"**，三批的 "当前检查集" 事实基线必须同一份（审计 §5 批 2 说 "以 agate-summary.py 的防护机制清单为准"，批 4 说 "换成当前检查集" 没指定源）。建议统一钉死："三批一律以 `WORKFLOW.md`「Pre-commit 检查总览」表为唯一事实源，其余文件一律指针化"，避免三批各抄一份又漂移。
- 批 3、批 4 体量偏大（WORKFLOW.md 41KB、git-integration.md + CONTEXT.md）。若走 chore-PR（option B），单 PR diff 会很大、self-gate-review 负担重。若走 TAG（option A），作 P4 static-batch 子批可控。

---

## §5 对 §7 七个待确认项的建议

> §7 列了 6 项，编号 1-6；任务书要求答 7 项 —— 第 7 项理解为 "§7 各项 + 一个总执行建议"。逐项给硬结论：

**§7-1｜裁级：state-machine.md / WORKFLOW.md 是否该升 "重写"？git-integration.md / CONTEXT.md 是否该降 "大改"？**
→ **state-machine.md / WORKFLOW.md 维持 "大改"，不升级**。两者骨架当前、P6.5 已织入、缺的是增量机制的接入，不是结构过时。
→ **git-integration.md 降 "大改"，CONTEXT.md 降 "局部修补~大改"**。骨架都健康、都该留。审计 §5 批 4 的动作清单本身就是增补口径，与 "重写" 裁级矛盾 —— 以 §5 为准，改 §2。

**§7-2｜LIMITATIONS 删局限 5/8 有无遗漏内核？局限 6 迁走后 "零基础设施" 边界够不够诚实？**
→ **局限 5 有内核（语义层协议自一致性无 in-flow gate，人触发依赖），改压缩保留，不整删** —— 本次审计的存在本身就是证据，且两处 scripts docstring 按编号引用它。
→ **局限 8 内核（无 CI ⟹ `--no-verify` 无兜底且无恢复）可删本节，但落点必须写进局限 3 正文并在批次 checklist 显式列出最终措辞**。
→ **局限 6 迁走会削弱诚实边界**。Requirements 清单进 README/SETUP（操作向）**并且** LIMITATIONS 保留一段 "零基础设施是相对的、gate enforcement 有硬依赖、这是取舍代价" 的边界陈述。不是二选一。

**§7-3｜Codex 定位：README 平台表加 Codex 行 vs 只在 platform-notes.md 展开、门面表保持 4 行？**
→ **README 平台表加 Codex 行**（与 WORKFLOW 平台表补 DSH 行同批做，两张表统一成 OpenCode / Claude Code / DSH / Codex 四行）。"完整度" 列按 `platform-notes.md`（声明的权威源）填 —— Codex = 完整 P0-P8（有原生 `spawn_agent`）。若担心用户混淆 "宿主注册方式不同"，在表下加一句脚注指 `SETUP.md` 步骤 2-Codex / 步骤 2-DSH（这两个平台无 orchestrator 软链步骤）。**不要**按审计原方案把 Codex 降为 "dispatch target only" —— 那与 platform-notes.md 对立。

**§7-4｜执行方式 A（立项 TAG）还是 B（chore 分批）？批次是否按 §5 的 6 批？**
→ **A（立项 TAG），但批次合并为 4 个**：
  - 批 A = 原批 1 + 批 3 平台表部分 + orchestrator-template P6.5 mapping（"跨门面一致性"，纯局部修补，含 summary 死链）
  - 批 B = 原批 2 + 批 3 剩余（state-machine.md + WORKFLOW.md 大改，两者互为反向传播对象，同批做 protocol-alignment-review 收益最大）
  - 批 C = 原批 4（CONTEXT.md + git-integration.md 大改）
  - 批 D = 原批 5 + 批 6（LIMITATIONS 重构 + 收尾小瑕疵；LIMITATIONS 编号连带面需要 P7 式交叉核对，和收尾杂项一起收口）
→ 理由：审计 §6 倾向 A 的论证成立（批 B/C 是 "重写受影响节"，反向传播 + 编号连带需要 P7/P6.5 兜底）。B 方案（chore 分批）对批 B/C/D 不安全 —— 跨文档编号连带 + 大段重写没有独立 judge 兜底，正是局限 3 说的 "self-authored gate" 风险面。批 A 单独走 chore 也可以（纯局部修补），但既然要立 TAG，一并纳入更省事。

**§7-5｜遗漏扫描：`agate/assets/` 是否需同轮审计？**
→ **需要，但轻量**。已扫结果：
  - `execution-roles/`：只有 `analyst.md:69` 提 ceremony（当前）；`verifier.md` / `consistency-reviewer.md` / `implementer.md` / `test-designer.md` / `architect.md` / `vision-analyst.md` 全部 0 处 P6.5/judge/cmdstream/routing。多数可接受（角色文件按 "本角色本阶段做什么" 收敛）。
  - **需改的 2 处**：① `verifier.md` 补一句 "P6-evidence/ 是下游独立 judge 的唯一输入，须自足"（§3 遗漏 5）；② `implementer.md:33` P8 输入清单补 `P6.5-judge-verdict.md`（§3 遗漏 9）。
  - `review-roles/judge.md`（2026-08-22）判 18 处 judge/P6.5 命中 —— 当前，不用动。
  - `templates/`、`formatters/` 未见新机制脱节。
→ 建议：作为批 D 的一个小项（2 处一行改动），不值得单开一轮审计。

**§7-6｜`agate-summary.py` L170 死链正确修法？**
→ **在脚本里解析仓库根 CHANGELOG，不要建软链/薄壳**。`agate-summary.py` 已有 `AGATE_ROOT` / `info["root"]` 解析（`:150` `root = Path(info["root"]).resolve()`）。CHANGELOG 在仓库根 = `AGATE_ROOT` 的父目录（legacy：`~/.agate` → `<clone>/agate`，根是 `<clone>`）或版本布局的 `current/`。最稳做法：脚本探测 `{AGATE_ROOT}/../CHANGELOG.md` 和 `{AGATE_ROOT}/CHANGELOG.md` 两个候选，取存在的那个，提示串用解析出的实际路径。**不建 `agate/CHANGELOG.md` 软链** —— 会让 "CHANGELOG 只在仓库根" 这个单一事实源出现第二个入口，且 Windows 无符号链接权限时又是一套 fallback。改脚本（1 处逻辑）比加文件系统 artifact 干净。

**§7-总｜总执行建议**
→ 立 TAG，4 批（见 §7-4），dogfooding worktree。执行前先把本评审 §6 的审计文档修订清单落进 `doc-consistency-audit-2026-09.md` 使其到终版，再开 P0。

---

## §6 审计文档必须应用的修改（diff 级清单）

给 `docs/design-notes/doc-consistency-audit-2026-09.md` 作者，达到终版前逐条改：

1. **§3-A 整节重写**。
   - 删 "以 SETUP.md 为准" 及据此得出的 "Codex = 派发目标 + 命令流可观测，非完整宿主"。
   - 改为：真实矛盾 = `WORKFLOW.md:152-156`（有 Codex 无 DSH）与 `README.md:70-72` / `README.zh-CN.md:70-72`（有 DSH 无 Codex）**平台表行集不一致**；`SETUP.md:177` 的 "out-of-scope" 措辞易被读成 "Codex 不能当宿主"，与声明的权威源 `platform-notes.md:57/63`（Codex 完整 P0-P8 + 原生 `spawn_agent`）冲突。
   - 修法改为：两张门面平台表统一成 OpenCode / Claude Code / DSH / Codex 四行；"完整度" 列以 `platform-notes.md` 为准；`SETUP.md:177` 收窄措辞为 "无 orchestrator 软链注册步骤（同 DSH）"；表下脚注指 SETUP 步骤 2-Codex / 2-DSH。

2. **§2 逐文件表：`state-machine.md` 行** —— 删 "「Pre-commit 检查全景」节旧 check 编号"（`state-machine.md:247-249` 已是干净指针，事实错误）。保留其余三条缺口（agate next / ceremony / cmdstream-routing 指针）。

3. **§2 逐文件表：`CONTEXT.md` 行** —— 裁级 `重写` → `大改`。"残留 `T080`/`T001`" 改为 "残留 `T080`（`:16`）"（无 T001）。"`gate exit code` 语义未含 pass_set 三态" 改为 "`gate exit code` 词条（`:10`/`:21` 两条近重复）把 exit 2 说成『需人工判断』，与 `loop-orchestration.md:246`『exit 2 ∈ pass_set 正常通过』**矛盾**，须订正 + 合并冗余"。

4. **§2 逐文件表：`git-integration.md` 行** —— 裁级 `重写` → `大改`。"全篇 `v0.4 hardening-roadmap` 框架" 改为 "`:160-189` 一节为 `v0.4 hardening-roadmap` 旧框架 + 旧编号（`:166-174`）；`:19-156` 三条规则骨架当前有效、保留"。

5. **§2 逐文件表：新增一行 `agate/orchestrator-template.md`** —— 裁级 `大改`（或 `局部修补 ×3`）。缺陷：phase-card mapping 表（"开始" 节第 5 步）无 P6.5 行；全文 0 处 `agate next`/`advance`、0 处 P6.5/judge、0 处 dispatch routing；"只有你能写的文件" 表无 judge dispatch-context。提到批 1。

6. **§4-1 表：局限 5 行** —— "删的理由" 改为 "压缩保留的理由"：删小作文（P0 模板字段例子、"为什么不在流程内加" 三点），保留 3-4 行内核（语义层协议自一致性无 in-flow gate、CHECK 是结构兜底非语义、人触发依赖、未根治），并入局限 1/3 邻域。备注：`check-protocol-consistency.py:6` + `agate/scripts/README.md:141` 按编号引用局限 5，整删留悬空引用。

7. **§4-1 表：局限 8 行** —— 保留 "删本节"，但 "唯一值得留的一句并入局限 3" 改为具体动作：在局限 3 正文（或局限 1）加定稿句「不启用 CI 时，`git commit --no-verify` 可绕过全部 pre-commit gate 且无自动恢复 —— pre-commit hook 是唯一 enforcement 点」，并把此句列进批次 checklist 的验收项。

8. **§4-2 表：局限 6 行** —— "处理" 改为：Requirements 清单迁 README/SETUP（操作向）**且** LIMITATIONS 保留一段取舍边界陈述（"'零基础设施' 是相对的：文档零依赖，gate/hook enforcement 依赖 python3+git+pyyaml+git 仓库；缺失则退化为可参考散文。这是取舍代价，非缺陷"）。不是纯搬迁。

9. **§5 批 2** —— 删 "「Pre-commit 检查全景」节：旧 `P1.x`/`P2.x` 编号 → …"（该节已指针化）。改为 "确认该节指针有效即可，重点补 `agate next`/`advance` 接入单步节 + ceremony/cmdstream/routing 指针"。

10. **§5 批 4** —— 标题 `重写` → `大改`；开头 "两份都最旧、结构性过时，逐节补不如重写" 改为 "两份的旧框架/旧编号集中在局部，骨架保留、翻新受影响节 + 增补缺失词条/规则"。CONTEXT.md 动作补 "合并 `:10`/`:21` 冗余 gate 词条 + 订正 exit-2 语义"。

11. **§5 批 5 连带 grep 清单** —— 补 `agate/SETUP.md:220`(局限2)、`agate/UPGRADING.md:154`(局限2)、`agate/tests/ENV-SENSITIVE-TESTS.md:24`(局限3)、`agate/scripts/check-protocol-consistency.py:6`(局限5)、`agate/scripts/README.md:141`(局限5)；删 `role-system.md`（无按编号引用，幻影项）。加一句执行顺序约束："先冻结 LIMITATIONS 最终编号方案，再做批 1 里 README 对『局限 3』的新引用"。

12. **§5 批 6** —— `SELF-GATE.md` 项补 "`:4` 和 `:31` 的 'CHECK 9' 表述一并改（不只 `:23` 的 'CHECK 1-9'）"。

13. **§5：新增 "批 2/3/4 共用事实基线" 约束** —— "三批凡涉及旧 check 编号翻新，一律以 `WORKFLOW.md`「Pre-commit 检查总览」表为唯一事实源，其余文件指针化，不各自复制清单"。

14. **§6 执行方式表** —— 倾向 A 的论证保留；补 "批次可从 6 合并为 4"（见本评审 §7-4），并注明 B 方案仅对 "跨门面局部修补" 那批安全，对 state-machine/WORKFLOW/CONTEXT/git-integration 大改 + LIMITATIONS 编号连带不安全（正是局限 3 的 self-authored 风险面）。

15. **§7 增补两问的结论指针** —— Q5（assets/）：已扫，需改 `verifier.md`（judge handoff 一句）+ `implementer.md:33`（P8 输入补 judge verdict），其余角色文件可接受，无需单独一轮。Q6（summary 死链）：改脚本解析仓库根 CHANGELOG（探测 `{AGATE_ROOT}/../CHANGELOG.md`），不建软链/薄壳。

16. **审计头部 §范围** —— "含 `agate/phase-cards/`" 与 §2 只评 `phase-cards/README.md` 不符：要么补评 8 张 phase 卡片（至少 `P6-acceptance.md`），要么把范围收窄为 "`phase-cards/README.md`"。

17. **§1 审计方法** —— 加一条 "对照声明的权威源"：平台维度以 `platform-notes.md` 为准（`WORKFLOW.md:496` 声明），retry/转移以 `state-machine.md` 为准，pre-commit 检查集以 `WORKFLOW.md`「Pre-commit 检查总览」为准。避免再次选错权威源（§3-A 的根因）。
