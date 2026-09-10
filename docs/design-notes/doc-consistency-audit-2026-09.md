# 门面 + 协议文档 文实一致性审计与修改计划（2026-09）

> **问题**：`README.md` / `README.zh-CN.md` / 根 `AGENTS.md` / `install.sh` / `agate/*.md` 中多处
> 描述滞后于当前机制（v0.71.0）。不只是最近改动（Codex 接入 / 派发路由 / cli·model），是**跨版本
> 累积的文实脱节**——个别文档自 8 月中未随机制演进更新，偏差大到建议整节翻新。
> **范围**：仓库根门面文档 + `agate/` 协议本体全部 .md + `agate/rules/` + `SELF-GATE.md` +
> `agate/phase-cards/README.md`（8 张 phase 卡片本体不逐张评，仅确认 `P6-acceptance.md` 含 judge 派发）。
> 不含 `site/`（协议 gate 治理之外）、`agate/scripts/` 代码（除 1 处 startup 提示串 bug）。
> `docs/guides/project-map.md` 在范围外，作「连带同步」处理。
> **状态**：审计 v3（v2 = 过一轮独立评审后按其 17 项 diff 清单修订；v3 = 用户追加「历史/失效文件
> 存档移除」范围，新增 §8。评审见 `docs/reviews/review-doc-consistency-audit-2026-09.md`）。
> 下一步：按 §5 的 5 批（A-E）执行，立项方式见 §6。
> **判据来源**：`docs/guides/doc-freshness-guide.md`（选材 / 数字不写死 / 指针式 / 活文档 vs 快照）。
> **性质**：本文是**短命活文档**——批次执行完毕后转历史快照（末尾追加「已执行」标注 + 落地 PR）。

---

## 1. 审计方法

对每份文档做四件事：

1. **grep 关键机制词**（P6.5/judge、事件账本、命令流存活检测、`agate next`/`agate advance`、
   dispatch routing/tier、ceremony、Codex）计命中数 → 命中 0 的成熟机制 = 脱节信号
2. **对照当前实现**：`agate/rules/phases.yaml`（阶段集含 P6.5）、`CHANGELOG.md` v0.58→v0.71 条目、
   `agate/scripts/` 实际脚本名
3. **对照声明的权威源**（避免选错基准）：
   - 平台适配维度 → `agate/platform-notes.md`（`WORKFLOW.md` 末尾声明其为「权威唯一来源」）
   - retry 上限 / 状态转移 → `agate/state-machine.md`（`rules/state-transitions.md` 指回它）
   - pre-commit 检查集 → `agate/WORKFLOW.md`「Pre-commit 检查总览」表
4. **按 `doc-freshness-guide` §1 判据**：滞后描述会让读者做错什么 / 浪费多少时间 → 定裁级别

裁级：**一致** / **小瑕疵**（措辞、示例版本号）/ **局部修补**（补 1-2 处、不动结构）/
**大改**（翻新受影响的 2-5 节、保留骨架）/ **重写**（结构性过时、逐节补不如照当前机制重写）。

---

## 2. 逐文件裁定

| 文件 | 裁级 | 核心偏差（要点，细节见 §3-§4） |
|---|---|---|
| `agate/CONTEXT.md` | **大改** | 术语表缺 judge/P6.5、事件账本、命令流存活检测、`agate next`/`advance`、dispatch routing/tier 五组词条；残留 `T080`（`:16`，仅此一处旧编号）；`gate` / `gate exit code` 两条近重复词条（`:10`/`:21`）把 exit 2 一律说成「需人工判断」，**与 `loop-orchestration.md`「exit 2 ∈ pass_set 正常通过」矛盾**（见 §3-D），须订正 + 合并冗余。结构（三列表）健康、保留 |
| `agate/git-integration.md` | **大改** | `:160-189` 一节为 `v0.4 hardening-roadmap` 旧框架 + `P1.7`/`P2.3-P2.5`/`P2.12` 旧 check 编号（`:166-174`）+ `T002`/`T011`/`T042` 旧任务 ID；缺 `self-gate-review:` commit trailer、缺 `gate-events.jsonl` 入库、缺发布 PR 必须 `--no-ff`/禁 squash。**`:19-156` 三条规则骨架（commit 由主 Agent / 一阶段一 commit / push 分档位）+ phase 字段语义 + wf()/feat() 判定表 + 多 Agent 并发四策略 当前有效、保留** |
| `agate/state-machine.md` | **大改** | **0 处**提及 `agate next`/`agate advance`（RM-AG0054，驱动状态推进的 CLI 在状态机权威文档里缺席）；「主 Agent 的单步执行」节（`:322-398`）仍纯手工流程；无 ceremony 对转移的影响；命令流存活检测 / dispatch routing 无一句指针。骨架（状态存哪 / 状态机定义 / 抗中断 / 回退 / 评审迭代 / 重试上限）当前、P6.5 已深度织入、保留。**注**：「Pre-commit 检查全景」节（`:247-249`）已是干净指针，无需动 |
| `agate/WORKFLOW.md` | **大改** | 平台表行集与 README 不一致（§3-A）；0 处 `agate next/advance`；ceremony（thin/standard/full）全文仅 1 处带过（`:349` check-routing 描述里），裁剪节（`:232-249`）无档位词表；无命令流存活检测 / dispatch routing 指针；「风险矩阵（P2.13）」「Pre-commit 总览（hardening Phase 1-2）」标题措辞旧（表体 `:337-351` 已用当前脚本名，仅标题与个别行内编号旧） |
| `agate/orchestrator-template.md` | **大改**（或局部修补 ×3） | **主 Agent 唯一必读文件**（`mode: primary`，标准接入软链进 `.claude/agents/`）。「开始」节第 5 步的 phase-card mapping 表列 P0-P8、**无 P6.5 行**——只读 template + 卡片的编排 Agent 不会知道 P6.5 要派 judge；全文 0 处 `agate next`/`advance`、0 处 P6.5/judge、0 处 dispatch routing；「只有你能写的文件」表无 judge dispatch-context。**优先级高于 `phase-cards/README.md`** |
| `README.md` | **局部修补 ×6** | ① "eight phases (P1→P8)" 漏 **P6.5**（§3-B）；② 平台表行集与 WORKFLOW 不一致（有 DSH 无 Codex）（§3-A）；③ 信任分类表 + "self-authored gates are mitigated" 段未提 P6.5 judge；④ "How it works" 流程图漏 P6.5 + 漏事件账本；⑤ 裁剪段无 ceremony 词表；⑥ Documentation 表一行中英混排、漏 `dispatch-tiers.yaml` |
| `README.zh-CN.md` | **局部修补** | 同 `README.md` 全 6 条；额外：小节标题仍全英文（`## How it works` / `## Supported platforms` / `## Design principles` / `## Known limitations` …），中文镜像应用中文标题 |
| `agate/LIMITATIONS.md` | **精简重构** | 详见 §4。删非限制（局限 8 本节 / 局限 5 小作文）、折叠已缓解（局限 4）、局限 6 Requirements 迁走但保留取舍边界句、狠删局限 3/7 的机制枚举 + 旧编号 |
| `agate/SELF-GATE.md` | **局部修补** | `:4` / `:23` / `:29` / `:31` 四处把「CHECK 9」当唯一结构兜底 / 写「CHECK 1-9」，实际 `check-protocol-consistency.py` 已到 CHECK 15；触发条件（`:14-18`）列 `agate/scripts/*.py` / `agate/*.md` / `agate/**/*.md`，**漏 `agate/rules/*.yaml`**（`dispatch-tiers.yaml` 等按 CHANGELOG v0.71.0 明写「改它走 SELF-GATE」，CHECK 15 专扫数据面） |
| `agate/scripts/agate-summary.py` | **1 处逻辑修复** | `:170` 启动提示「读 `~/.agate/CHANGELOG.md`」—— legacy 单软链下 `~/.agate` = `<clone>/agate`，`agate/CHANGELOG.md` 不存在（CHANGELOG 只在仓库根）；版本布局下正确路径是 `current/CHANGELOG.md`。修法见 §7-6（脚本探测 `{AGATE_ROOT}/../CHANGELOG.md`，不建软链） |
| `install.sh` | **小瑕疵** | 头注释「agate 协议安装脚本」未跟品牌改名；注释/提示文案里默认克隆目录 `$HOME/oclab/agate`（URL 已 `agateon`）；示例版本号 `v0.48.0` 漂移。**只改文案，不动 `AGATE_REPO_DIR` 默认值**（避免破坏存量用户路径） |
| `CHANGELOG.md` | **小瑕疵** | 顶部无 `## [Unreleased]` 段（`check-changelog.py` NORMAL 模式无该区 → exit 1；仅 P8 触发）。加回空 `[Unreleased]`，符合 Keep-a-Changelog 且避免下个任务 P8 踩 exit 1 |
| 根 `AGENTS.md` | **基本一致** | 写得克制、指针式。`:55` 引 `agate-next-card.py`（卡片注入工具，与推进 CLI 无关）——引用无误、无需动 |
| `agate/AGENTS.md` | **基本一致** | 入口导航 + 角色清单（含 judge）齐。仅：流程描述从未点出 P6.5 位置；升级示例 `v0.48.0`（低优先） |
| `agate/phase-cards/README.md` | **小瑕疵** | 卡片索引 P0-P8，**无 P6.5 条目也无说明**（借 P6 卡派发，读者看不出）；「旧协议文件」列表漏 adr/UPGRADING/SETUP/CONTEXT |
| `agate/dispatch-protocol.md` | **基本一致** | routing/cmdstream/judge 均覆盖。仅 0 处 `agate next/advance`（推进属 state-machine 域，值得一句交叉引用） |
| `agate/SETUP.md` | **一致（1 处措辞收窄）** | 步骤 2-Codex / 2-DSH / 2-dispatch-routing scaffold 齐。仅 `:177`「out-of-scope」措辞易被读成「Codex 不能当宿主」，与权威源 `platform-notes.md` 冲突——收窄为「无 orchestrator 软链注册步骤（同 DSH）」（§3-A） |
| `agate/rules/*.yaml` | **一致** | `phases.yaml` 有 P6.5（gate_subphase）；`dispatch.yaml` 有 judge_required_since + 五模式；`dispatch-tiers.yaml` 新增。仅 `phases.yaml` 注释里「WORKFLOW.md 287-299 行」行号引用脆（低优先） |
| `agate/UPGRADING.md` | **一致** | v0.69/0.70/0.71 章节齐 |
| `agate/role-system.md` / `loop-orchestration.md` | **一致** | `loop` 深度整合 `agate next`（TAG0027 §3.7）+ P6.5 前进特例 + pass_set；`role-system` 有 judge/P6.5/ceremony/full。均未提 RM-AG0060 路由，但路由归 dispatch-protocol.md 域，可接受 |
| `agate/assets/execution-roles/*.md` | **2 处小改** | `verifier.md` 补一句「`P6-evidence/` 是下游独立 judge 的唯一输入、须自足」；`implementer.md` P8 输入清单（`:33`）补 `P6.5-judge-verdict.md`。其余角色文件按「本角色本阶段做什么」收敛、可接受（`review-roles/judge.md` 当前，不动） |

---

## 3. 跨文档不一致（优先级最高，先修）

### 3-A. 两张门面平台表行集不一致 + Codex 定位选错权威源

**真实缺陷**：

- `WORKFLOW.md` 平台表：OpenCode / Claude Code / **Codex** / Claude Project —— **有 Codex，无 DSH**
- `README.md` / `README.zh-CN.md` 平台表：OpenCode / Claude Code / **DSH** / Claude Project —— **有 DSH，无 Codex**
- 两张门面表**行集根本不一致**（各缺一个已验证平台），这是核心问题。

**定位错误**：初稿以 `SETUP.md:177`「Codex … out-of-scope … 被派发执行环境」判「Codex 非完整宿主」。
但协议声明的平台适配权威源是 `platform-notes.md`（`WORKFLOW.md` 末尾 +「平台适配权威源」自述），
其中 Codex 章写「P0-P8 全部阶段可执行」+ 原生 `spawn_agent` 派发。`SETUP.md` 的「out-of-scope」
实指「无 `.claude/agents/` 等价的 orchestrator 软链注册步骤」——与 **DSH 同类**（DSH 用 preset，
而 DSH 在 README 里照样是「完整 P0-P8」）。

**修法**（一批同步三处）：

- 两张门面平台表统一成 **OpenCode / Claude Code / DSH / Codex** 四行（+ Claude Project 部分支持行）
- 「完整度」列以 `platform-notes.md` 为准：四者均「完整 P0-P8」（Codex 有原生 `spawn_agent`）
- 表下加脚注：DSH / Codex 无 orchestrator 软链注册步骤，接入见 `SETUP.md` 步骤 2-DSH / 2-Codex
- `SETUP.md:177` 措辞收窄为「无 orchestrator 软链注册步骤（同 DSH）」，删「out-of-scope」的歧义表述
- **不要**把 Codex 降为「dispatch target only」——那会与 `platform-notes.md` 对立

### 3-B. P6.5 / 独立 judge 在门面 + 主 Agent 必读文件缺席

`phases.yaml` / `WORKFLOW.md` 阶段表 / `dispatch-protocol.md` 都有 P6.5（2026-08-22 起强制），但：

- `README`（both）："eight phases (P1→P8)" / "How it works" 流程图 / 信任分类表 —— 全无 P6.5
- **`orchestrator-template.md`**：phase-card mapping 表无 P6.5 行；「只有你能写的文件」表无 judge dispatch-context
- `CONTEXT.md` 术语表 —— 无 judge / judge verdict / gate-events.jsonl 词条
- `phase-cards/README.md` —— 卡片索引无 P6.5 条目

修法（一批同步）：

- `README`（both）："eight phases plus a mandatory independent-judge checkpoint (P6.5)"；流程图补
  `… → P6 → P6.5 judge → P7 …` + 一处提 `gate-events.jsonl` 事件账本；信任分类表 + mitigation 段补
  「P6.5 独立 judge 对 P6 自写 gate 的强化缓解」一句 + 指 LIMITATIONS（用最终编号，见 §5 顺序约束）
- `orchestrator-template.md`：mapping 表加 P6.5 行（借 P6 卡、`.state.yaml` phase 保持 P6 直至 P7）+
  「只有你能写的文件」表加 `P6.5-dispatch-context-judge.md`
- `CONTEXT.md`：补 judge / P6.5 / judge verdict / gate-events.jsonl（事件账本）词条
- `phase-cards/README.md`：卡片索引加 P6.5 行 + 说明

### 3-C. `agate next` / `agate advance`（RM-AG0054，v0.66.0）只有 loop-orchestration.md 讲

`state-machine.md`（0）、`WORKFLOW.md`（0）、`dispatch-protocol.md`（0）、`orchestrator-template.md`（0）
—— **驱动状态推进的 CLI，在描述状态推进的四份文档里完全不存在**（仅 `loop-orchestration.md` 深度整合）。
最大的机制/文档脱节。

修法：

- `state-machine.md`「主 Agent 的单步执行」节：接入 `agate next`（查表推进）/ `agate advance`，
  说明「查表推进不做临场判断」，手工流程降级为 fallback
- `WORKFLOW.md`「三种使用方式」/「核心原则 5」附近：补 `agate next/advance` 作为推进入口一句 + 指
  `state-machine.md` 正文
- `dispatch-protocol.md` / `orchestrator-template.md`：派发—推进衔接处各加一句交叉引用（细节归 state-machine.md）

### 3-D. `CONTEXT.md` 的 gate exit-code 语义与其余协议冲突

`CONTEXT.md:10,21`「2 = 需人工判断」 vs `loop-orchestration.md:246`「exit 2 是多数 phase 正常通过码
∈ pass_set」 vs `WORKFLOW.md` 阶段表以「exit 2」为 PASS 条件 vs `check-gate.py` docstring「pass 判定
以 phases.yaml `gate_pass_exit` 为准」。CONTEXT.md 把 exit 2 一律说成「需人工判断」是**跨文档矛盾**，
不只是「缺」。修法：合并 `:10`/`:21` 两条近重复词条为一条，exit-2 语义改为「多数 phase（见
`phases.yaml gate_pass_exit`）的正常通过码；仅在 phase 的 pass_set 不含且 ≠1 时才是真暂停 / 需人工」。

---

## 4. LIMITATIONS.md 精简重构方案

原则（用户 2026-09-10 + 评审复核）：**只留真正的结构性限制。删兼容性说明 / 依赖披露 cruft /
缺陷清单式堆砌。每条 = 断言 + 为何结构性 + 一句当前缓解 + "未根治"，不写小作文。**
评审修正：局限 5 有真实内核（不整删，压缩保留）；局限 8 内核落点须写死；局限 6 迁 Requirements
但保留取舍边界句。

### 4-1. 删除 / 压缩

| 现节 | 处理 |
|---|---|
| **局限 5「协议文档内部一致性验证不在流程内」** | **压缩保留，不整删**。真实内核：协议文档**语义层**自一致性没有 in-flow gate（`check-protocol-consistency.py` CHECK 1-15 是结构/关键词兜底，节内 `:87` 自承「结构兜底」；不覆盖语义），靠「人记得触发 protocol-alignment-review + 人确认 NEEDS_HUMAN_REVIEW」。与局限 1（测试质量上限）、局限 3（self-authored）同族——「纯文档协议 + 可判定 gate」路线的结构性产物。**本次审计本身就是这条局限的实例**（一次全仓文实脱节靠人发起审计才发现）。且 `check-protocol-consistency.py:6` + `agate/scripts/README.md:141` 的 docstring 按编号引用「局限 5」——整删留悬空引用。**动作**：压到 3-4 行并入局限 1 或局限 3 邻域；删 P0 模板「4 字段 vs 5 字段」的例子（可能自身已过时）+「为什么不在流程内加」三小点 |
| **局限 8「CI backstop 支持 GitHub/GitLab/Gitea Actions」** | **删本节**（约 80% 是平台能力矩阵 cruft）。**但内核必须落地**：在局限 3（或局限 1）正文加定稿句「不启用 CI 时，`git commit --no-verify` 可绕过全部 pre-commit gate 且无自动恢复——pre-commit hook 是唯一 enforcement 点」。此句列进批次 checklist 的验收项，不能只在批说明写「并入」就算数 |

### 4-2. 折叠

| 现节 | 处理 |
|---|---|
| **局限 4「subagent 活动不可观测」** | 通篇「当前做不到」已过时——RM-AG0055 命令流日志机制（v0.67.0）是实质缓解。改成一小段：**曾是硬限制，现可从平台会话记录外部观测活动信号（调用冻结 / 活动冻结 / 逻辑空转），残留 = "证据 + 触发核查、非自动判死" + 依赖各平台适配器解析会话记录格式**。不再单列大节，可并入局限 3 邻域或缩为半页。（`dispatch-protocol.md:133` 按编号引用局限 4，若并入需同步该引用） |
| **局限 6「运行时依赖 python3+git+pyyaml + bash + Pillow」** | Requirements 清单（可操作：强制 python3+git+pyyaml；不限制被管理项目语言）迁到 `README` / `SETUP.md` 的 Requirements 节。**LIMITATIONS 保留一段取舍边界陈述**（不是纯搬迁）：「『零基础设施』是相对的——文档本体零依赖，但 gate / hook 的**强制力**依赖 python3 + git + pyyaml + git 仓库。缺任一，协议退化为『可参考的散文』，失去 enforcement。这是用通用工具替代专用服务的代价，非缺陷，但采用者要知道边界。」删 bash 薄壳 / Pillow 可选子弹 |

### 4-3. 保留但狠删枝蔓

| 保留节（可重新编号） | 现状 | 删什么 |
|---|---|---|
| gate 可信度上限（原局限 1） | 尚可 | — |
| 角色隔离是认知隔离（原局限 2） | 补一句 dispatch routing 补了 model 维度（`cli: native` 弱 / 跨 CLI 强），一句话 | — |
| 主 Agent 单点故障（原局限 3） | **臃肿**：整段「降级缓解（v2 客观行为审计）」嵌套逐一列 provenance check、「P5 机械化回归判定（v0.24.0，P2.47/P2.48）」、「根治：Phase 3 独立 git author」；残留 `T005/T016/T068/T073/T026` | 砍逐-check 枚举；只留：核心断言 + `[PROD_TOUCHED]` / retries 对应校验 / P6.5 judge 三个缓解**各一句** + 局限 8 的 CI 内核句 + 局限 5 的语义内核句 + "仍不可根治"。旧任务 ID 留 1-2 个当锚 |
| vision 依赖外部基础设施（原局限 7） | **臃肿**：把整个 TAG0006 机制规格（三态分档 / avg-hash / `frames/` / `renders/` / `-tN`）搬进来了——那是 P6 卡 / verifier 角色内容 | 收缩到：需截图能力的平台；无则退化文本描述验收 + 人工复核记录；截图真实性不可机器验证（见主 Agent 单点节） |
| 「这些局限意味着什么」结尾 | 好 | 保留 |

**净效果**：8 节 + 重散文 → 约 5 节精简（1 gate 上限 / 2 角色隔离 / 3 主 Agent 单点[并入 4/5/8 内核] / 7→vision / 结尾）。重构后过 `check-protocol-consistency.py` 确认无死链。

---

## 5. 分主题批次修改计划（5 批：A-E）

按主题批改，不按文件逐个补。每批独立成子交付，均触发 SELF-GATE（`agate/*.md` 面 + `agate-summary.py`），
走 `self-gate-review:` + protocol-alignment-review。

### 批 A — 跨门面一致性（先做，纯局部修补，影响面最大）

- 3-A 平台表：`WORKFLOW.md` + `README` + `README.zh-CN` 三处统一成四行 + `SETUP.md:177` 措辞收窄
- 3-B P6.5/judge 补进门面：`README`×2 + `orchestrator-template.md`（mapping + 写文件表）+ `CONTEXT.md`
  词条 + `phase-cards/README.md`
- 3-C `agate next/advance` 一句交叉引用先落 `dispatch-protocol.md` + `orchestrator-template.md`（正文重写留批 B）
- `agate-summary.py:170` CHANGELOG 死链修复（§7-6）
- `CHANGELOG.md` 加回空 `## [Unreleased]`
- **连带**：`docs/guides/project-map.md` 工具清单节 + CLI/派发章节按需补 `agate next` / dispatch routing
  （其 §3.1 阶段流已含 P6.5，无需改）
- **可单独走 chore-PR**（纯局部修补，无大段重写、无编号连带）

### 批 B — `state-machine.md` + `WORKFLOW.md` 大改（两者互为反向传播对象，同批）

- `state-machine.md`：单步执行节接入 `agate next` / `agate advance`；补 ceremony 对转移的影响
  （thin 不薄化 P5/P6）；补命令流存活检测对「受控自主再派发」的一句指针（正文归 RM-AG0055 设计文档）
- `WORKFLOW.md`：裁剪节补 ceremony 档位词表（thin/standard/full + 四要素 checklist 指针）；
  「三种使用方式」补 `agate next/advance` 推进入口；「风险矩阵（P2.13）」/「hardening Phase 1-2」
  标题措辞清理；补命令流存活检测 + dispatch routing 一句指针
- **不做**：`state-machine.md`「Pre-commit 检查全景」节（`:247-249` 已是干净指针）
- 涉及 pre-commit 检查集翻新时，**一律以 `WORKFLOW.md`「Pre-commit 检查总览」表为唯一事实源**，
  其余文件指针化（见 §5 末「共用事实基线」约束）

### 批 C — `CONTEXT.md` + `git-integration.md` 大改（都引用旧 check 编号，同批换成当前集口径统一）

- `CONTEXT.md`：补 5 组缺失词条；修 `:16` 的 T080 注；**合并 `:10`/`:21` 冗余 gate 词条 + 订正
  exit-2 语义**（§3-D）；逐条核对「首次定义位置」章节名仍存在
- `git-integration.md`：翻新 `:160-189` 一节（旧编号 → 指向 `WORKFLOW.md` 权威表）；补
  `self-gate-review:`/`self-gate-skip:` trailer、`gate-events.jsonl` 入库、发布 PR `--no-ff` 禁 squash；
  清 3 个旧任务 ID。**`:19-156` 骨架不动**

### 批 D — `LIMITATIONS.md` 精简重构（§4）+ 收尾小瑕疵（编号连带需 P7 式交叉核对，一起收口）

- 局限 5 压缩保留（不整删）、局限 8 删本节但内核句落进局限 3 正文（checklist 列最终措辞）、
  局限 6 Requirements 迁走 + 保留取舍边界句、局限 4 折叠、局限 3/7 狠删枝蔓、重新编号
- **连带 grep 清单**（按编号引用 `局限 N` 的位置，排除 LIMITATIONS.md 自身）：
  - 局限 2：`adr.md`、`SETUP.md:220`、`UPGRADING.md:154`
  - 局限 3：`git-integration.md:186`、`WORKFLOW.md:358`、`README.md:106`、`README.zh-CN.md:105`、
    `agate/tests/ENV-SENSITIVE-TESTS.md:24`
  - 局限 4：`dispatch-protocol.md:133`
  - 局限 5：`agate/scripts/check-protocol-consistency.py:6`、`agate/scripts/README.md:141`
  - （`role-system.md` 无按编号引用——初稿的幻影项，已删）
  - **约束**：只删局限 5、8 → 局限 1-4 编号不变、现存对 2/3/4 的引用全部存活；真正会断的是对「局限 5」
    的两处 scripts 引用（→ 又一条「别整删局限 5」的理由，压缩保留则引用仍有效，仅需微调措辞）
- 收尾：`SELF-GATE.md`（`:4`/`:23`/`:29`/`:31` 四处「CHECK 9 / CHECK 1-9」→「CHECK 全集，不写死上界」
  + 触发条件补 `agate/rules/*.yaml`）；`install.sh` 文案；`phase-cards/README.md` 补 P6.5 说明 +
  旧协议文件列表；`verifier.md` judge handoff 一句 + `implementer.md:33` P8 输入补 judge verdict；
  `agate/AGENTS.md` / `phases.yaml` 注释脆行号引用（低优先）

### 批 E — 历史 / 失效文件 存档与移除（详见 §8）

- **删除**：`docs/reviews/*.progress.md` ×16（SELF-GATE 约定「留痕文件成功可删」，对应 TAG 全部已落地）
- **存档**：`docs/hardening-roadmap.md` → `archived/`（Phase 1-2 已落地 / Phase 3 已取消；4 处引用由批 B/C 软化）；
  `docs/superpowers/specs/2026-08-15-docs-suite-{review,update-design}.md` ×2 → `archived/`（上一轮文档体系
  更新的设计+评审，被本审计取代；仅 TAG0025 任务归档快照引用、非活引用）
- **状态刷新**（不存档）：`docs/design-notes/README.md` 索引 + 各设计文档自身「状态」行——5+ 条已落地
  但仍标 backlog/待立项（`design-maintainability-gate` / `rm-ag0046-*-plan` / `design-orchestration-semantics`
  / `design-dispatch-routing` / `design-md-field-set`）
- **归位**：`archived/` 根下 4 个散文件（`validation-plan.md` / `validation-report.md` /
  `HANDOFF-TAG0024.md` / `HANDOFF-TAG0025.md`）移入 `archived/docs-2026-08/` 对应子目录

### 共用约束

- **事实基线单源**：批 B/C 凡涉及旧 check 编号翻新，一律以 `WORKFLOW.md`「Pre-commit 检查总览」表
  为唯一事实源，其余文件指针化，不各自复制清单。
- **编号冻结顺序**：批 D 的 LIMITATIONS 最终编号方案**先冻结**，再做批 A 里 `README` 对「局限 3」
  的新引用（只删局限 5/8 时局限 1-4 编号不变，此约束自动满足；若重排则批 A 需等批 D）。
- **批 E 与批 B/C 顺序**：`hardening-roadmap.md` 存档须与批 B/C 软化其 4 处引用同批或紧随，避免死链窗口。

---

## 6. 执行方式建议

| 方式 | 说明 | 适合 |
|---|---|---|
| **A. 正式立项一个 TAG**（文档一致性批，类比 TAG0016「协议卫生」） | 走 P0-P8，dogfooding worktree；批 A-E 作为 P4 static-batch 子批；P7 一致性 + P6.5 judge 兜底 | 批 B/C 是「翻新受影响节」，protocol-alignment-review 的反向传播 + LIMITATIONS 编号连带需要 P7/P6.5 兜底 |
| **B. chore 分批 PR** | 每批一个 `docs:`/`chore:` PR + `self-gate-review:` + 独立对齐审查 | **仅批 A / 批 E 安全**（纯局部修补 + 文件存档移除、无大段重写、无编号连带）。批 B/C/D 不安全——跨文档编号连带 + 大段重写没有独立 judge 兜底，正是局限 3 的 self-authored 风险面 |

**倾向 A**，5 批作 P4 子批。批 A / 批 E 若想早落可先单独 chore-PR，其余纳入 TAG。

---

## 7. 待确认项的结论（经独立评审）

**7-1｜裁级**：`state-machine.md` / `WORKFLOW.md` 维持「大改」不升「重写」（骨架当前、P6.5 已织入、
缺的是增量机制接入）。`git-integration.md` 降「大改」、`CONTEXT.md` 降「大改」（骨架健康、动作是
翻新受影响节 + 增补，非重写）。§2 已按此改。

**7-2｜LIMITATIONS 删节**：局限 5 **压缩保留不整删**（语义层协议自一致性无 in-flow gate 是真实内核 +
两处 scripts docstring 按编号引用）。局限 8 删本节，但内核句（无 CI ⟹ `--no-verify` 无兜底且无恢复）
**写进局限 3 正文 + checklist 列最终措辞**。局限 6 Requirements 迁 README/SETUP **且** LIMITATIONS
保留取舍边界陈述段（不是二选一）。§4 已按此改。

**7-3｜Codex 定位**：`README` 平台表**加 Codex 行**，与 `WORKFLOW.md` 补 DSH 行同批，两表统一成
四行；「完整度」列按权威源 `platform-notes.md` 填（Codex 完整 P0-P8 + 原生 `spawn_agent`）；表下
脚注指 SETUP 步骤 2-Codex / 2-DSH。**不**降 Codex 为 dispatch-target-only。§3-A 已按此重写。

**7-4｜执行方式**：**A（立项 TAG），批次从 6 合并为 4**（批 A 跨门面 / 批 B state-machine+WORKFLOW /
批 C CONTEXT+git-integration / 批 D LIMITATIONS+收尾）。§5、§6 已按此改。

**7-5｜`agate/assets/` 同轮审计**：**需要，轻量**。已扫：`execution-roles/` 多数按「本角色本阶段」
收敛、可接受；需改 2 处——`verifier.md` 补「`P6-evidence/` 是下游独立 judge 唯一输入、须自足」、
`implementer.md:33` P8 输入补 `P6.5-judge-verdict.md`。`review-roles/judge.md` 当前、不动。作批 D 小项。

**7-6｜`agate-summary.py` L170 死链修法**：**改脚本解析，不建软链/薄壳**。脚本已有 `AGATE_ROOT` /
`info["root"]` 解析；探测 `{AGATE_ROOT}/../CHANGELOG.md`（legacy）和 `{AGATE_ROOT}/CHANGELOG.md`
（版本布局整仓形态）两个候选，取存在者，提示串用解析出的实际路径。不建 `agate/CHANGELOG.md` 软链
（会让「CHANGELOG 单一事实源」出现第二入口 + Windows 无符号链接权限又一套 fallback）。

**7-7（新）｜其它跨文档维度已排除**：retry-cap 数字跨 `state-machine.md` / `phases.yaml` /
`git-integration.md` / `WORKFLOW.md` 一致，无漂移。phase 名 / gate 命令与 `phases.yaml` 一致。

---

## 8. 历史 / 失效文件 存档与移除

> 判据（`doc-freshness-guide` §3）：**历史快照**（`archived/`、`tasks/`、`reviews/` 产出）保留不动、
> 改反而失真；但已完成 / 被取代 / 状态漂移的**活文档**该存档的存档、该刷新的刷新。

### 8-1. 删除 —— `docs/reviews/*.progress.md` ×16

`SELF-GATE.md` 明写这类**留痕文件**「成功可删」（`agate-alignment-{date}-{task_id}-{NN}.progress.md`，
空返回诊断用，原始执行痕迹）。现存 16 个全部对应已落地 TAG（TAG0007/0016/0017/0018/0022/0024/
0029/0030/0031/0032 + 早期）。成果文件 `agate-alignment-review-{date}-{task_id}.md` 保留（闭环依据）。
**动作**：`git rm docs/reviews/agate-alignment-*.progress.md`。

### 8-2. 存档 —— `docs/hardening-roadmap.md`

状态头自述「Phase 1 + 2A + 2B + 2C 已落地；Phase 3 已取消（依赖平台）」——**已完成路线图 = 历史**。
仍被 4 处引用为「自 v0.4 hardening-roadmap 起」：`git-integration.md:162`、`WORKFLOW.md:335`、
`loop-orchestration.md:234`、`platform-notes.md:132`。前两处由批 B/C 翻新时改为指 `WORKFLOW.md`
「Pre-commit 检查总览」；后两处「自 v0.4 起」是历史沿革措辞，可保留或软化为「pre-commit hook +
CI backstop 机制自 v0.4 起统一可用」。
**动作**：`git mv docs/hardening-roadmap.md archived/docs-2026-08/plans/`（与批 B/C 同批或紧随）。

### 8-3. 存档 —— `docs/superpowers/specs/2026-08-15-docs-suite-{review,update-design}.md` ×2

上一轮文档体系更新（v0.46/0.47 Python 化 + bats→pytest 后）的设计 + 独立评审，状态「已批准」/ 已执行。
**本审计（`doc-consistency-audit-2026-09.md`）是其后继**。仅 `agate-workspace/tasks/TAG0025-*/`
的归档快照引用它（历史快照、frozen，不受影响）。
**动作**：`git mv docs/superpowers/specs/2026-08-15-docs-suite-*.md archived/docs-2026-08/plans/`。
（`docs/superpowers/` 其余内容不动——`agate/AGENTS.md` 仍把 superpowers 列为「推荐伴侣」。）

### 8-4. 状态刷新（不存档）—— `docs/design-notes/` 索引 + 文件头

设计文档按 `docs/design-notes/README.md` 的约定**保留为决策记录**（防同一问题反复讨论），
但「状态」是漂移项（`doc-freshness-guide` §5）。现索引 + 各文件自身「状态」行滞后：

| 文档 | 现标 | 实际 |
|---|---|---|
| `design-maintainability-gate.md` + `rm-ag0046-maintainability-gate-plan.md` | 待立项 / 设计草案（RM-AG0046） | 已落地 TAG0026，v0.65.0 |
| `design-orchestration-semantics.md` | 设计讨论 v3（待立项，候选 RM-AG0054） | 已落地 TAG0027，v0.66.0 |
| `design-dispatch-routing.md` | 已申领 RM-AG0060（backlog，epic） | 已落地 TAG0034，v0.71.0 |
| `design-md-field-set.md` | 设计提案（RM-AG0048，backlog） | RM-AG0048 一期已落地 TAG0024，v0.63.0（二期仍 backlog） |
| `design-structured-layer` / `design-risk-routing` / `design-independent-judge` | 文件头仍「设计提案 / backlog」 | 索引已标「已落地」，**文件头未同步** |

**动作**：索引表 + 各文件「状态」行统一改为「已落地（TAGxxxx，vX.Y.Z）」；`design-notes/README.md`
新增 `260903-design-subagent-liveness-and-self-dispatch/`（RM-AG0055，已落地 TAG0028 v0.67.0）索引行
（当前索引缺该子目录）。

### 8-5. 归位 —— `archived/` 根下 4 散文件

`archived/docs-2026-08/` 已是「按日期子目录 + issues/research/plans」的组织形态；根下 4 个散文件
（`validation-plan.md` / `validation-report.md` 8-13；`HANDOFF-TAG0024.md` / `HANDOFF-TAG0025.md` 8-26）
未归位。**动作**：HANDOFF 两个 → `archived/docs-2026-08/`（与其它 HANDOFF-TAGxxxx 并列）；
`validation-*` → `archived/docs-2026-08/plans/`（或确认来历后定）。纯 cosmetic，低优先。

### 8-6. 不处理（明确记录）

- `check-protocol-consistency.py --strict-errors-only` 的一批 WARNING（`docs/archived/reviews/...` /
  `scripts/check-gate.sh` 等无法解析引用）—— 全在**叙事 / 历史快照文件**里（`docs/reviews/agate-alignment-
  review-2026-08-*.md`、`CHANGELOG.md` 历史条目、`agate-workspace/tasks/TAGxxxx/` 归档产出等）。按
  `doc-freshness-guide` §3「快照保留不动、改反而失真」，**不修**。这也是 CHECK 2 对叙事文件只发
  WARNING 不发 ERROR 的原因。
- **批 E 执行后 WARNING 会 +约 30**：`hardening-roadmap.md` / 16 个 `*.progress.md` / 2 个 superpowers
  specs 被移走 / 删除后，`agate-workspace/tasks/TAG0013·0015·0025/` 等**已归档任务产出**里对旧路径的
  引用变为"引用文件不存在"。这些是 frozen 快照，**不回改**（0 ERROR 不变，`--strict-errors-only` 仍
  通过）。
- `docs/agents/knowledge-index.md` —— 自述「试点」，部分条目 2026-08-12、引 `T001` 旧编号。是**活的
  实验文档**、非死文件。低优先：确认试点是否仍在用；若弃用则存档，若在用则清旧编号。本批不强制。

### 8-7. 执行归属

批 E。删除（8-1）+ superpowers 存档（8-3）+ 状态刷新（8-4）+ 归位（8-5）无跨文档依赖，可先做；
`hardening-roadmap.md` 存档（8-2）与批 B/C 的引用软化同批。

---

## 执行状态

**批 A-E 已于 2026-09-10 在分支 `docs/protocol-doc-refresh` 执行**（5 个 `docs(protocol):` commit，
提交前 consistency 0 ERROR / structure S-1~S-6 OK / unit 全绿）。分支收尾统一走 SELF-GATE
（`check-protocol-consistency.py` + 独立评审 + protocol-alignment-review）后合并 main。
本文档随之转为历史快照。

`hardening-roadmap.md` 已移至 `archived/docs-2026-08/plans/hardening-roadmap.md`。

---

## 变更日志

- 2026-09-10：初稿。审计 + 逐文件裁定 + 三跨文档不一致 + LIMITATIONS 精简方案 + 6 批计划 + 待确认 6 项。
- 2026-09-10：v2。按独立评审（`docs/reviews/review-doc-consistency-audit-2026-09.md`，Verdict
  REVISE）的 §6 十七项 diff 清单修订：§3-A 整节重写（平台表行集不一致 + 权威源改 platform-notes.md，
  Codex 保持完整宿主）；`state-machine.md`「Pre-commit 全景旧编号」断言删除（已是干净指针）；
  `CONTEXT.md` / `git-integration.md` 裁级 重写→大改；新增 `orchestrator-template.md` 一行（P6.5
  mapping 缺席）；新增 §3-D（CONTEXT.md exit-code 跨文档矛盾）；局限 5 改压缩保留、局限 8 内核落点
  写死、局限 6 保留取舍边界句；6 批合并为 4 批 + 共用事实基线 / 编号冻结顺序约束；连带 grep 清单
  补全（+SETUP/UPGRADING/ENV-SENSITIVE-TESTS/2 scripts，−role-system 幻影）；§7 六项 + 新增 7-7 给硬结论。
- 2026-09-10：v3（终版）。用户追加范围：历史 / 失效文件的存档与移除。新增 §8——删 16 个
  `*.progress.md` 留痕文件（SELF-GATE 约定成功可删）；存档 `hardening-roadmap.md`（Phase 1-2 已落地）
  + 2 个 superpowers docs-suite specs（被本审计取代）；刷新 `docs/design-notes/` 索引 + 5+ 文件头的
  滞后「状态」行 + 补 RM-AG0055 子目录索引；归位 `archived/` 根下 4 散文件。列为**批 E**（§5）。
