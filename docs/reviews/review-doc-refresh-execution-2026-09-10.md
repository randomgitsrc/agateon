# 独立评审：`docs/protocol-doc-refresh` 分支执行保真度

> 评审对象：6-commit 分支 `docs/protocol-doc-refresh`（base `main` = fd456da），执行
> `docs/design-notes/doc-consistency-audit-2026-09.md`（v3 终版）的批 A-E + 1 个 test-align commit。
> 评审方式：不采信 commit message，逐文件比对 `git diff main...HEAD` vs 计划 §2/§5/§8，
> 重跑一致性 / 结构 / pytest / `agate-summary.py`，全仓 grep `局限 N` 引用。
> 评审人：独立评审 agent，2026-09-10。

---

## Verdict：**REVISE**

执行主体健康：5 批全部做了 §5/§8 的实质内容，0 ERROR，结构 S0-S6 OK，1609 测试全绿，
WARNING +30 基本全在冻结快照。但有 **5 处必须在合并前修**（1 个漏做的计划项 + 1 处偏离计划定性 +
3 处重编号后新产生的悬空/错指引用），另有若干非阻塞观察。

**Top 3 问题**：
1. `agate/SETUP.md:177`「out-of-scope / 被派发执行环境」**完全没改**——计划 §5 批 A 明列的项漏做；
   且批 A 新增的门面脚注反而写「Codex 作派发目标 / dispatch target」，正是 §3-A/§7-3 明令「**不要**」的定性。
2. `design-dispatch-routing.md` 的「局限 6」只改了 3 处（:9/:34/:209），**头部 `:7`「相关：…（局限 2/4/6）」漏改**——
   重编号后「局限 6」现指 vision 节，应为「局限 5」。
3. `agate/tests/ENV-SENSITIVE-TESTS.md:24` 引「LIMITATIONS.md（局限 3「降级缓解」节）描述的 P5 机械化
   回归判定机制」——批 D 把局限 3 的「降级缓解」子节连同 `pre-task-baseline.md`/`known-failures.md` 全删了，
   编号活着但被引小节和机制没了（一致性脚本只查文件存在、不查小节，正好是折进局限 3 的那条局限的活标本）。

---

## §1 逐批保真度

| 批 | 按 §5/§8 做了？ | 越权 / scope-creep | 漏项 |
|---|---|---|---|
| **A 跨门面一致性** | 大体是：README×2 补 P6.5 + `gate-events.jsonl` + 流程图 + 信任表缓解层 + ceremony 档位 + Codex 行 + Documentation `rules` 行；README.zh-CN 小节标题中文化；WORKFLOW 补 DSH 行 + 脚注；orchestrator-template mapping/写文件表补 P6.5 + `agate next` 指针；dispatch-protocol 步骤 6 补交叉引用；phase-cards/README 补 P6.5 行 + 旧协议文件列表；`agate-summary.py:170` 死链修复；CHANGELOG `[Unreleased]`；project-map §3.3/§5 补 `agate next`/routing/事件账本 | 无文件级越权（WORKFLOW.md 跨 A+B 是 §7-4 明许） | **`SETUP.md:177` 措辞收窄漏做**（§5 批 A 明列）。门面脚注引入「Codex 作派发目标」偏离 §3-A 定性（见 §2、§5） |
| **B state-machine + WORKFLOW 大改** | 是：state-machine「单步执行」节加机械化说明（步骤 5-7 由 `agate next` 查表，手工为 fallback，本节手工规格是权威语义）+ ceremony 对转移影响（不改转移边/retry/不薄化 P5/P6）+ RM-AG0055 受控自主再派发 + cmdstream 指针；WORKFLOW 可裁剪节补 P6.5 + ceremony 词表、「风险矩阵（P2.13）」「(P2.14)」去锚号、Pre-commit 总览标题去「hardening Phase 1-2」+ 标注唯一事实源、三种使用方式补 `agate next` + 可选机制指针 | 无。**正确地没动** state-machine.md `:247-249`「Pre-commit 检查全景」指针节（§5 批 B「不做」项 + 评审 §1 #23） | 无实质漏项。`agate advance` 措辞见 §2 观察 |
| **C CONTEXT + git-integration 大改** | 是：CONTEXT 补 5 组词条（P6.5/judge、`gate-events.jsonl`、cmdstream、`agate next/advance`、派发路由/tier）+ 合并 `:10`/`:21` gate 冗余词条 + **订正** exit-2 语义 + 去 T080 沿革注 + pytest 词条去 garbled；git-integration 翻新 `:160-189` 一节（去旧编号表 → 指 WORKFLOW 唯一事实源）+ 补 `gate-events.jsonl` 入库 + `self-gate-review:` trailer + 发布 PR `--no-ff` 禁 squash + `check-events.py` + 旧任务 ID → TAG0001 + 「agate/v4」→ Agateon；`:19-156` 骨架未动 | 无 | 无 |
| **D LIMITATIONS 精简重构 + 收尾** | 大体是：8 节→6 节；局限 5 语义内核折进局限 3（一条子项）；局限 8 内核（无 CI ⟹ `--no-verify` 无兜底且无恢复）落进局限 3 正文；局限 4 改「RM-AG0055 部分缓解」；局限 6→局限 5（Requirements 明细移 SETUP，保留「零基础设施是相对的」取舍边界句 + ADR-003）；局限 7→局限 6（删 TAG0006 机制规格搬运，指 P6 卡 + vision-analyst）；局限 3 狠删枝蔓；局限 1-4 编号不变；`check-protocol-consistency.py:6` + `scripts/README.md:141` + `roadmap.md:501` 引用同步；SELF-GATE.md `:4/:23/:29`（等）「CHECK 1-9」→「结构 CHECK 全集（当前 1-15）」+ 触发条件补 `agate/rules/*.yaml`；`install.sh` 文案；verifier.md + implementer.md:33（§7-5 两处） | 无文件级越权 | **`design-dispatch-routing.md:7`「（局限 2/4/6）」漏改**（其余 3 处已改）。**`ENV-SENSITIVE-TESTS.md:24` 悬空**（见 §3）。`agate/AGENTS.md` `v0.48.0` / `phases.yaml` 注释脆行号（计划标「低优先」）未做、未在 commit 显式声明延后 |
| **E 历史/失效文件存档移除 + 状态刷新** | 是：`git rm` 16 个 `*.progress.md`（数量吻合）；`hardening-roadmap.md` → `archived/docs-2026-08/plans/`；2 个 superpowers docs-suite specs → 同目录（空 `specs/` 删）；`archived/` 根下 4 散文件归位；`design-notes/README.md` 索引 5 行 backlog→已落地 + 新增 RM-AG0055 子目录行；6 个设计文档头「状态」行刷新；`loop-orchestration.md`/`platform-notes.md` 软化「自 v0.4 hardening-roadmap 起」措辞；plan 文档追加「执行状态」节 | 计划 §5 批 E 未列「编辑 plan 文档正文」，但计划自身 §性质「批次执行完毕后转历史快照（末尾追加「已执行」标注）」已授权，不算 creep | **`design-notes/README.md` 里 plan 文档自身那一行仍写「v3 终版…待按批次执行」**——批 E 刷了所有别的设计文档状态、漏了自己（见 §5） |
| **test-align** | `tag0034_regression_baseline.json`：state-machine.md sha256/bytes 随批 B 更新（hash 已复核匹配当前文件）+ `_note` 重写说明「叙事文档经 SELF-GATE 刷新」；`test_protocol_alignment_review.py`：`"CHECK 1-9"` 断言 → `"check-protocol-consistency.py"` + `"CHECK"` | 改一个已落地任务的 P3 冻结基线——但替代方案是 regression RED；gate 机制三文件（phases.yaml / check-gate.py / check-state-transition.py）hash 仍字节锁定，BDD-39 本意保留；JSON 缩进 2sp→1sp（cosmetic）。可接受 | 无 |

---

## §2 事实核查（对抗式抽查）

| 断言 | 结论 | 证据 / 实际机制 |
|---|---|---|
| README「eight phases plus a mandatory independent-judge checkpoint (P6.5) … re-verifies every acceptance criterion in a fresh context」 | **CONFIRMED** | `phases.yaml:123-137` P6.5：`retry_cap:2`，`gate_subphase`，check = `check-judge-verdict.py + check-events.py 双 exit 0`；`role-system.md` judge = fresh context 逐条重验全部 BDD（含已 PASS，零挑验）。措辞准确 |
| README/WORKFLOW 平台表 4 行 + Codex「Full P0-P8」符合 `platform-notes.md`（声明的权威源）| **CONFIRMED（能力列）** | `platform-notes.md:3`「平台适配权威源」；`:55`「本地开发环境 ✅ 完整 \| P0-P8 全部阶段可执行」；`:65` 原生 `spawn_agent` 派发。两张门面表现均为 OpenCode/Claude Code/DSH/Codex 四行 + Claude Project 部分支持 |
| README/README.zh-CN/WORKFLOW 脚注「Codex is a dispatch target / Codex 作派发目标」 | **WRONG（偏离计划定性 + 与权威源张力）** | 计划 §3-A/§7-3：「**不要**把 Codex 降为『dispatch target only』——那会与 `platform-notes.md` 对立」。`platform-notes.md:55/65` Codex 可跑完整 P0-P8 宿主 + 原生派发。脚注该说的是「无 orchestrator 软链注册步骤（同 DSH，无 `.claude/agents/` 等价物）」，不是「作派发目标」。能力列对、脚注 gloss 错 |
| `SETUP.md:177` 措辞已按 §5 批 A 收窄 | **WRONG（漏做）** | `agate/SETUP.md:177` 原样：「Codex 无「宿主 orchestrator 注册」步骤（out-of-scope）——它作为 agate 的**被派发执行环境**接入」。计划明列要删「out-of-scope」歧义表述、收窄为「无 orchestrator 软链注册步骤（同 DSH）」。未触碰 |
| DSH 脚注（README）指 `platform-notes.md` 为权威源 | **CONFIRMED** | README.md:53 / README.zh-CN.md:143：「…platform-notes.md — the authoritative source for per-platform capability」/「各平台能力的权威源是 platform-notes.md」 |
| `agate-summary.py` 启动建议第 3 行解析到真实 CHANGELOG | **CONFIRMED** | 实跑 `python3 agate/scripts/agate-summary.py`：第 3 行「读 `/home/kity/oclab/agateon/CHANGELOG.md`（了解…）」，该文件存在。`:152-159` 探测 `{root}/../CHANGELOG.md` 与 `{root}/CHANGELOG.md` 取存在者，legacy 布局下前者命中 |
| state-machine.md 新「机械化」框 正确描述 `agate-next.py` 实际行为 | **CONFIRMED** | `agate-next.py` docstring：消费 `check-gate.py` exit 三态 + `phases.yaml` `gate_pass_exit`/`next`/`retreat`，不改 gate 返回约定；exit 1 → 委托 `agate-retreat-to.py`；P6（exit 2 ∈ pass_set）走 A1 条件式裁决。state-machine.md:327-331 与之逐条吻合，且明确「手工全流程是 fallback、本节手工规格是 `agate next` 实现依据的权威语义」 |
| dispatch-protocol.md:291 / orchestrator-template.md:56 说「由 `agate next` / `agate advance` 完成」前进查表 | **PARTIALLY-WRONG（继承性不精确）** | `agate-advance.py` docstring 自述「手动/多阶**回退**引导 CLI」——`--to` 缺省只打印转移表建议、不动作；diff≥2 引导 PAUSED；diff=1 委托 `agate-retreat-to.py`。它**不跑 gate、不做前进推进**。把它与 `agate next` 并列为「跑 gate → 写 `.state.yaml` phase」不准确。此并列在 `UPGRADING.md:290`、`design-orchestration-semantics.md` 已存在（非本分支首创），但本分支把它扩散进 3 份协议文档。state-machine.md:329「`agate advance` 是其同族入口」措辞够模糊、可存活 |
| state-machine.md ceremony 注 与 `phase-cards/P1-requirements.md` 不冲突 | **CONFIRMED** | P1-requirements.md:121-128：thin 须四要素（申请 + coupling_checklist 流式 + 跳过风险 + `phases` 含 P5/P6），缺一回退 standard；full 档 `phases` 须含 P7。state-machine.md:406-409「不改状态机转移边、不改 retry 上限、不薄化 P5/P6（thin 档 `phases` 必须含 P5 与 P6，由 `check-routing.py`/`check-pruning.py` 双闸兜底）」与之一致。WORKFLOW.md 新 ceremony 词表同 |
| CONTEXT.md 新 gate exit-code 词条 与 `phases.yaml gate_pass_exit` + `check-gate.py` 一致 | **CONFIRMED** | CONTEXT.md:10「多数 phase（P0-P3/P5/P6/P8）以 exit 2 为正常通过，P4/P7/P6.5 以 exit 0 为通过；exit 1 一律不通过；某 phase 的 `pass_set` 不含且 ≠1 才是真暂停」。`phases.yaml`：P0-P3/P5/P6/P8 `gate_pass_exit:2`、P4/P7/P6.5 `gate_pass_exit:0`（逐条核对无误）。`check-gate.py:6-12` docstring 同口径。跨文档矛盾（原 `loop-orchestration.md:246` vs CONTEXT）已消解 |
| CONTEXT.md 5 组新词条准确 | **CONFIRMED** | `gate-events.jsonl`：事件 `gate_run/judge_verdict/state_transition/dispatch_route` + `prev_hash` 哈希链 + ts 单调 + `check-events.py`（链完整性 / judge 轮次去重 ≤2 / dispatch_route 理由码枚举）——逐条匹配 `check-events.py` docstring 审计链 1-8。cmdstream：`agate-cmdstream-adapters.py` `ADAPTERS = {claude-code, opencode, dsh, codex}`（`:874-878`）匹配。tier：`dispatch-tiers.yaml` `tiers={bulk,standard,deep}`（`:11,16-24`）匹配。P6.5「exit code 双 0 才是门槛」匹配 `phases.yaml:111` |
| git-integration.md「发布 PR `--no-ff` 禁 squash」与根 `AGENTS.md` 发布清单一致 | **CONFIRMED** | `AGENTS.md:82` 与 git-integration.md 新段近逐字一致：CHECK 7 + G-5 用 `git describe --tags --abbrev=0`；squash → SHA 不同 → tag 与 main 分叉、describe 回退旧版；补救 `git tag -f vN.N.0 <main-commit> && git push origin vN.N.0 --force` |
| git-integration.md 的 `self-gate-review:` trailer 机制真实存在 | **CONFIRMED** | `agate/scripts/commit-msg-self-gate.py`：`_REVIEW_RE`/`_SKIP_RE` 匹配 `self-gate-review:`/`self-gate-skip:`，缺失 WARNING 不拦截。触发面与 SELF-GATE.md（本分支已补 `agate/rules/*.yaml`）一致 |
| LIMITATIONS 重构未丢「协议文档语义一致性无 in-flow gate」内核（旧局限 5） | **CONFIRMED（在局限 3）** | 新局限 3 子弹：「**协议文档自身的语义一致性**没有 in-flow gate：`check-protocol-consistency.py` + SELF-GATE 是结构/关键词兜底，不覆盖语义；改协议靠人触发 protocol-alignment-review + 人确认 `NEEDS_HUMAN_REVIEW`。（本文档的存在就是这条的实例……）」。P0 模板「4 vs 5 字段」例子与「为何不在流程内加」三点已删（计划所许） |
| LIMITATIONS 重构未丢「无 CI ⟹ `--no-verify` 绕过」内核（旧局限 8） | **CONFIRMED（在局限 3）** | 新局限 3 子弹：「**不启用 CI 时**，`git commit --no-verify` 可绕过全部 pre-commit gate 且无自动恢复——pre-commit hook 是唯一 enforcement 点。启用 CI（GitHub/GitLab/Gitea Actions）则 backstop 重跑 `check-gate.py` + `check-p6-provenance.py` + `check-events.py` 兜底。」平台矩阵 cruft 已删 |
| 旧局限 6「零基础设施是相对的」取舍句保留为新局限 5 | **CONFIRMED** | 新局限 5：「『零基础设施』是相对的：**协议的文档部分**……确实零依赖……但 **gate 脚本与 pre-commit hook 的 enforcement** 依赖 python3 + git + pyyaml……缺任一，协议退化为『可参考的散文』，失去把关能力。这是用通用工具替代专用服务的代价，非缺陷——但采用者要知道边界在哪。」→ ADR-003 指针保留 |
| LIMITATIONS 重构丢了什么 | **旧局限 3「降级缓解」子节整删** —— 含 `check-p6-provenance.py` 六道审计枚举（计划所许「砍逐-check 枚举」）+ **P5 机械化回归判定机制（`pre-task-baseline.md` + `known-failures.md`，P2.47/P2.48）的描述**（计划 §4-3 只说保留「retries 对应校验」一句，未察觉 `ENV-SENSITIVE-TESTS.md:24` 语义依赖此节存在）+ 「根治：Phase 3 独立 git author」（计划所许）。核心断言「self-authored gate 只能缓解无法根治」「证据存在 ≠ 证据与结论对应」均保留 |
| 各局限「→ ADR-00X」指针 重编号后仍正确 | **CONFIRMED** | 局限 1→ADR-002、局限 2→ADR-006、局限 3→ADR-001/005（均编号未变）；**局限 5（原 6）→ADR-003**（正确跟随）；局限 4（折旧 4）、局限 6（原 7 vision）本就无 ADR 指针，仍无。`adr.md` 反向只引「局限 2」（`:461,473`），未变，无悬空 |
| `check-structure-consistency.py` S-1~S-6 | **CONFIRMED** | 实跑：S0-numbers / S1-phases / S2-workflow / S3-cards / S4-scripts / S5-schema / S6-references 全 OK，exit 0 |

---

## §3 引用完整性（全仓 `局限 N`，排除 `archived/` + `agate-workspace/tasks/`）

| 引用位置 | 引的编号 | 状态 | 需修？ |
|---|---|---|---|
| `agate/scripts/check-protocol-consistency.py:6` | 旧局限 5 | **已修** → 「回应 LIMITATIONS.md 局限 3 的一条子项——「协议文档自身的语义一致性没有 in-flow gate」：本脚本做结构/关键词兜底」 | 否 |
| `agate/scripts/README.md:141` | 旧局限 5 | **已修** → 「回应 `LIMITATIONS.md` 局限 3 的一条子项……本脚本做**结构/关键词**兜底（不覆盖语义）」 | 否 |
| `agate-workspace/roadmap/roadmap.md:501` | 旧局限 5 | **已修** → 「LIMITATIONS 局限 3 子项「协议文档语义一致性无 in-flow gate」（原独立列为局限 5）」 | 否 |
| `docs/design-notes/design-dispatch-routing.md:9` | 旧局限 6 | **已修** → 「局限 5（原局限 6）」 | 否 |
| `docs/design-notes/design-dispatch-routing.md:34` | 旧局限 6 | **已修** → 「局限 5（原局限 6）」 | 否 |
| `docs/design-notes/design-dispatch-routing.md:209` | 旧局限 6 | **已修** → 「局限 5（原局限 6）」 | 否 |
| **`docs/design-notes/design-dispatch-routing.md:7`**（头部「> **相关**：…`agate/LIMITATIONS.md`（局限 2/4/6）」）| 旧局限 6 | **漏改**——重编号后「局限 6」= vision 节（原局限 7），此处意图是旧局限 6 = 运行时依赖/零基础设施 | **是** → 改「（局限 2/4/5）」 |
| **`agate/tests/ENV-SENSITIVE-TESTS.md:24`** | 局限 3 | 编号活着，但引「LIMITATIONS.md（局限 3「降级缓解」节）描述的 P5 机械化回归判定机制（`pre-task-baseline.md` + `known-failures.md`）」——批 D 已删「降级缓解」子节 + 该机制描述。悬空语义引用（一致性脚本只查文件存在、放行）| **是** → 去「「降级缓解」节」、改指 `agate/phase-cards/P5-verification.md`（该机制现在的权威描述处，3 处命中） |
| `agate/git-integration.md:186`、`agate/WORKFLOW.md:358` | 局限 3 | 编号未变，OK | 否 |
| `README.md:106`、`README.zh-CN.md:105` | 局限 3 | 编号未变，OK（批 A 新加的信任表指引也指局限 3，与「编号冻结」约束一致）| 否 |
| `agate/dispatch-protocol.md:133` | 局限 4 | 编号未变、局限 4 仍独立成节，OK。附带：`:132`「当前平台不支持 subagent 活动检测」与新局限 4「RM-AG0055 部分缓解」有轻度语义漂移——非本批 scope，先前已潜伏 | 否（观察） |
| `agate/adr.md:461,473` | 局限 2 | 未变，OK | 否 |
| `agate/SETUP.md:220`、`agate/UPGRADING.md:154` | 局限 2 | 未变，OK | 否 |
| `docs/design-notes/design-independent-judge.md:10`「现状（局限 3 原文要点）」、`design-risk-routing.md:84` | 局限 3 | 编号未变；design-independent-judge 引旧局限 3 原文属已落地设计笔记的历史记录，可接受 | 否 |
| `agate/adr.md` 是否引重编号局限（ADR-002/003/006 交叉）| — | adr.md 仅按编号引「局限 2」（两处，同一 ADR 条目），未引 5/6/7/8，无重编号悬空 | 否 |

**结论**：计划承诺修的 5 处（check-protocol-consistency.py:6、scripts/README.md:141、
design-dispatch-routing ×3、roadmap.md:501）**全部已修**。但**漏了 2 处 LIVE 引用**：
design-dispatch-routing.md:7 的第 4 个「局限 6」、ENV-SENSITIVE-TESTS.md:24 的被引小节悬空。

---

## §4 回归 / 一致性

| 项 | 结果 |
|---|---|
| `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0 ERROR，exit 0**。360 WARNING（CHECK 2 / CHECK 10 聚合），无一是 ERROR |
| `python3 agate/scripts/check-structure-consistency.py` | **S0-S6 全 OK，exit 0** |
| pytest（分片 `-n auto`）| unit **1478 passed / 2 skipped**；regression **31 passed**；integration + sanity **100 passed**。合计 1609 passed / 4 skipped，全绿 |
| `agate-summary.py` 启动建议第 3 行 | 解析到 `/home/kity/oclab/agateon/CHANGELOG.md`（存在）✓ |

**WARNING-delta 分类**：main 基线 330 → 分支 360，净 **+30**。逐条 diff（`comm` 两侧 WARNING 列表）：
- **~24 条**：`docs/hardening-roadmap.md` / 已删 `*.progress.md` / 移走的 superpowers specs 的旧路径引用，
  全在 `agate-workspace/tasks/TAG0006·0013·0015·0025/` **冻结任务快照** + `docs/reviews/agate-alignment-
  review-2026-08-21-TAG0018.md` **叙事快照** 里 → 计划 §8-6 预期的「+约 30」。**均不在 live 协议文档**。
- **3 条**：从 `docs/design-notes/doc-consistency-audit-2026-09.md:224/298/305` → `docs/hardening-roadmap.md`
  （plan 文档正文里写的旧路径）。严格说不在「`agate-workspace/tasks/` 或 `agate-alignment-review-*.md`」
  白名单内，但 plan 文档已自声明「转为历史快照」，按 `doc-freshness-guide` §3 不回改可接受；0 ERROR 不受影响。
- **3 条**：`CHANGELOG.md` 里 `postmortem-template.md` / `check-p6-provenance.sh` / `check-windows-smoke.sh`
  的既有 WARNING，行号因 `[Unreleased]` 插入 +4 行而位移（673→677 等），非新增。
- **live `agate/*.md` 协议文档里：0 条新增 WARNING**。✓

---

## §5 越权与缺口

- **漏做的计划项**：`SETUP.md:177` 措辞收窄（§5 批 A 明列）——完全没碰，commit message 也未提。
- **偏离计划定性**：批 A 门面脚注「Codex is a dispatch target / Codex 作派发目标」= §3-A/§7-3 明令「不要」
  的表述。能力列「Full P0-P8」是对的，问题在括号 gloss。三处门面（README.md:53 / README.zh-CN.md:143 /
  WORKFLOW.md 平台表下脚注）同源。
- **重编号漏改 2 处**（见 §3）：`design-dispatch-routing.md:7`、`ENV-SENSITIVE-TESTS.md:24`。
- **批 E 自身留下的不一致**：`docs/design-notes/README.md` 里 `doc-consistency-audit-2026-09.md` 那行状态
  仍是「v3 终版（已过一轮独立评审），**待按批次执行**」——批 E 刷新了其余每个设计文档的状态行、
  给 plan 文档正文追加了「执行状态」节，却漏了索引表里 plan 文档自己那一行。
- **计划标「低优先」、执行跳过、未显式声明延后**：`agate/AGENTS.md` 升级示例 `v0.48.0`；`phases.yaml`
  注释「WORKFLOW.md 287-299 行」脆行号引用。计划允许跳，但 commit 里没写「本轮不做」。
- **CHANGELOG `[Unreleased]` 加成空的**（「（暂无……）」）——本分支的实质文档改动（LIMITATIONS 重构、
  删 16 文件、7 处 mv）在 CHANGELOG 里无任何痕迹。计划 §2 明说「加回**空** `[Unreleased]`」（理由纯为
  避免下个 P8 NORMAL 模式 exit 1），执行照做，属计划取向而非执行缺陷；但值得知会：CHANGELOG 读者
  看不到这批变更。
- **§7-5 verifier.md + implementer.md 两处小改**：均已正确做——verifier.md:37-40 加 judge handoff 段
  （`P6-evidence/` 是下游独立 judge 唯一输入、须自足）；implementer.md:33 P8 输入清单补
  `P6.5-judge-verdict.md`（文件名与 `phases.yaml:127` 一致）。✓
- **无文件级 scope-creep**：`git diff --name-only` 每个文件都能对上 §2/§5/§8 的批次归属
  （WORKFLOW.md 跨 A+B、platform-notes.md/loop-orchestration.md 在 E 均 §7-4/§8-2 明许）。
- **观察**：git-integration.md 把「## Hardening-roadmap 集成」标题整个换掉，loop-orchestration.md /
  platform-notes.md 只软化正文、保留同名标题——计划 §8-2 允许「保留或软化」，但留下轻度跨文档措辞不齐。
- **观察**：`design-dispatch-routing.md` 索引行 + 文件头 line 2 状态未按 §8-4「统一改为『已落地（TAGxxxx，
  vX.Y.Z）』」——仍是「设计收敛（……）**已落地 RM-AG0060**（TAG0034，v0.71.0……）」的拼接形态。已落地信息
  在，纯 cosmetic。

---

## §6 必须修（diff 级）

1. **`agate/SETUP.md:177`**：删「（out-of-scope）」与「作为 agate 的**被派发执行环境**接入」的歧义表述，
   收窄为计划 §3-A 定稿：「Codex 无 orchestrator 软链注册步骤（同 DSH——无 `.claude/agents/` 等价物），
   接入只需装 CLI + 登录 + 配自动化绕过 flag」。

2. **`README.md:53` / `README.zh-CN.md:143` / `agate/WORKFLOW.md` 平台表下脚注**：把「Codex is a dispatch
   target」/「Codex 作派发目标」改为与 §3-A 一致的「Codex 无 `.claude/agents/` 等价的 orchestrator 软链
   注册步骤（同 DSH）」。能力列「Full P0-P8 / 完整 P0-P8」保留不动。

3. **`docs/design-notes/design-dispatch-routing.md:7`**：「> **相关**：…`agate/LIMITATIONS.md`（局限 2/4/6）」
   → 「（局限 2/4/5）」。

4. **`agate/tests/ENV-SENSITIVE-TESTS.md:24`**：现文「`agate/LIMITATIONS.md`（局限 3「降级缓解」节）描述的
   P5 机械化回归判定机制（`pre-task-baseline.md` + `known-failures.md`）」→ 去掉「（局限 3「降级缓解」节）」，
   改指「`agate/phase-cards/P5-verification.md` 描述的 P5 机械化回归判定机制」（该卡片是现在唯一还完整写
   `pre-task-baseline.md` + `known-failures.md` 的地方）。若仍想留 LIMITATIONS 指针，指「局限 3」即可、
   不要指已不存在的「降级缓解」小节。

5. **`docs/design-notes/README.md`**（索引表 `doc-consistency-audit-2026-09.md` 行）：状态「v3 终版（已过
   一轮独立评审……），待按批次执行」→ 「已执行（批 A-E，2026-09-10，分支 `docs/protocol-doc-refresh`）→
   历史快照」，与该文档正文新增的「执行状态」节对齐。

**建议一并处理（非阻塞）**：
- `dispatch-protocol.md:291` / `orchestrator-template.md:56` 把 `agate advance` 与 `agate next` 并列为
  「跑 gate → 写 `.state.yaml` phase」的前进查表动作，但 `agate-advance.py` 实为回退引导壳（不跑 gate、
  不前进）。要么删这两处的 `agate advance` 只留 `agate next`，要么改成「前进用 `agate next`，`agate advance`
  处理多阶回退引导」。（此不精确在 `UPGRADING.md:290` / `design-orchestration-semantics.md` 已存在。）
- commit / CHANGELOG 里补一行说明 `agate/AGENTS.md` `v0.48.0` + `phases.yaml` 脆行号引用本轮显式不做。
