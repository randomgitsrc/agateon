# 交接：发布顺序问题 —— 前提更正与待决事项

> **日期**：2026-10-03
> **性质**：**交接文件**（请独立评审 / 决策）。**尚未改动任何协议或 CI 配置。**
> **触发**：用户在 v0.78.0 发版后发现「先推 tag 再开 PR」顺序颠倒；随后**指出我的分析前提有误**。

---

## 0. 最重要的更正：我把两个**不同受众**的文档当成了"需要对齐的两份副本"

**用户指正**：
> `AGENTS.md` 是**对本项目**的；而 **P8 是针对使用 agateon task 流程的**。

**我核实后确认用户是对的**，而且我此前的设计文档**整个命题建立在错误前提上**：

| 文档 | 受众 | 内容性质 |
|---|---|---|
| **根 `AGENTS.md`** | **本仓开发者**（"面向修改 Agateon 协议/脚本的开发者"） | **本仓维护流程**：tag / GitHub Release / G-5 验证 |
| **`agate/phase-cards/P8-release.md`** | **任何用 agateon 跑任务的项目** | **通用协议**：发布**准备**（bump + local tag → READY） |

**根 `AGENTS.md` 自己就写明了这个区分**（我读过却没当回事）：
> **版本引用文件清单（Agateon 仓库特有，通用 P8 卡不覆盖）**：README badge / CHANGELOG /
> UPGRADING 章节 / 稳定版引用

**⇒ 二者不是"副本"，因此不存在"交界没写"的问题。**
我原设计 §2 写的「两份文档的交界无人规定」**是错的**——它们**各有各的受众，各管各的范围**，
**本就不该逐条对齐**（强行对齐反而会把本仓特有的 GitHub 流程污染进通用协议）。

---

## 1. 事实（这部分经独立评审核验，7/10 属实）

### 1.1 P8 的范围（**通用协议**）

- `P8-release.md:11` releaser subagent **不执行** commit/tag
- `P8-release.md:44` 主 Agent 在 gate 后执行 **bump-version / git commit / git tag**
- `P8-release.md:91` 重跑 P5（含 CHECK 7）应安排在 **commit + tag 之后**
- **全文 0 处**提及 `push` / `main` / 保护分支 ⇒ **P8 不管远端**
- `P8-release.md:103` 明确出现「**项目侧** release 命令」⇒ **P8 意识到项目差异**

**⇒ 准确表述**：P8 产出「发布**准备**」（bump commit + **local tag**）→ 转 READY。
**推送到哪、怎么合进 main、是否发 Release，属各项目自己的事。**

### 1.2 根 `AGENTS.md` 的发布清单（**本仓维护**）

条目 4/5/5a/6 全是 **GitHub 操作**（推 tag、Release 资产校验、G-5）——
**这是 Agateon 仓库自己的维护流程**，不是协议要求。

**其缺陷（与本仓维护有关，与 P8 无关）**：条目 4 是「推 tag」，条目 6 的前提是
「release PR 合并后」——**但从未写明 tag 与 PR 的先后**。我按字面顺序做，撞上保护分支。

### 1.3 本仓的硬约束（实测）

```
main: required_status_checks=true（6 个 contexts）, enforce_admins=true, strict=true
⇒ 不能直接 push main（实测被拒：protected branch hook declined）
```

### 1.4 ⚠️ 关键实测：**「先 PR 后 tag」在本仓走不通**

**这属于「Agateon 本仓」的问题，与通用 P8 无关。**

**(a) release bump 不是 docs-only**
`protocol-tests.yml` 的 docs-only 白名单**不含 `agate/UPGRADING.md`**（只匹配 `agate-workspace/…`）。
逐文件判定 #394 的 4 个文件 ⇒ `agate/UPGRADING.md` 是"非 docs" ⇒ `docs_only=false`
⇒ **`consistency` job 真跑**（非 fast-pass）。

**(b) 真跑 ⇒ CHECK 7 在「badge 已改、新 tag 未打」时 FAIL**
本地实测（`/tmp` 副本，删 tag）：`❌ FAIL CHECK 7` + `ERROR (1)`。
> ⚠️ **机制更正**（评审查出，我复核代码 `:497`）：**并非"必然 FAIL"**——
> `git describe` 抛异常时走 `rep.warn` + `return`（**仅 WARNING**）；
> `rep.error` 只在「**已存在某 tag** 且与 badge 不等」时触发。
> 本仓有 74 个 tag ⇒ 现实下确实 FAIL，但**机制此前描述有误**。

**(c) #394 的 `consistency: SUCCESS` 是因为 tag 那时已推**
时间线（双证据）：tag push 15:04:00 → 分支 push 15:05:18 → PR CI 15:05:34；
CI checkout `fetch-depth: 0` + `fetch-tags: true` ⇒ 看得到已推 tag ⇒ CHECK 7 PASS。

**⇒ 因果是反的**：**我那个"顺序颠倒"恰好是 CI 变绿的原因**；
真按「先 PR 后 tag」走，PR 会被 `consistency`（required）卡住。

---

## 2. 独立评审查出的三个我的错误（**已全部复核属实**）

| # | 我写的 | 实际 |
|---|---|---|
| 1 | 「`agate/UPGRADING.md` **不参与 gate 判据**」 | ❌ **相反**——它是 **CHECK 13** 的检查对象（`check-protocol-consistency.py:1194-1220`），该 CHECK 专为 v0.62.0/v0.63.0「漏写 UPGRADING 章节」事故设立（RM-AG0052） |
| 2 | 「无 tag 时 CHECK 7 必然 FAIL」 | ❌ 无 tag 时**仅 WARN**（exit 0） |
| 3 | 白名单正则引文 / `ERROR (2)` | ❌ 引文失真；实测 `ERROR (1)` |

**⇒ 我推荐的方案 A（把 UPGRADING 加进 docs-only 白名单）会让 CHECK 13 在
release PR（它唯一有意义的场合）被整个关掉。方案 A 已否决。**

**评审另发现一个判据弱点**（我未指出）：
**把 tag 指向 `HEAD~5`（与 bump commit 无关），CHECK 7 照样 PASS**——
它**只看 tag 的名字**，不校验指向 / 祖先关系 / 与 bump commit 的一致性。

---

## 3. 现在的结论：**四个方案都有实质副作用**

| 方案 | 能否走通 | 副作用 |
|---|---|---|
| **A** 加 docs-only 白名单 | ✅ | ❌ **关掉 CHECK 13**（release 场景唯一有效处） |
| **B** 豁免 required check | ✅ | ❌ 靠人记得（与 ADR-015 手段②相悖） |
| **C** 先推 tag（今晚走通的） | ✅ | ⚠️ tag 打错位置**无判据可察**（评审实测） |
| **D** 拆 PR | ⚠️ | ❌ CHECK 13 校验时机被打散 |

**根因**：`consistency` 作为**一个 required job**，同时承载两类**满足时点不同**的判据：

| CHECK | 需要什么 | 满足点 |
|---|---|---|
| CHECK 7（badge ↔ tag） | tag **已存在** | **tag 之后** |
| CHECK 13（CHANGELOG ↔ UPGRADING） | bump **已提交** | **bump 之后即刻** |

**⇒ 这不是流程问题，是判据耦合。** 而**它只影响 Agateon 本仓**
（其他用 agateon 的项目有各自的 CI，不受此约束）。

---

## 4. 待决策事项（**我不擅自决定**）

### Q1（核心）：第一层——改 `consistency` 的判据耦合，做不做？

**最对症的候选**：把 **CHECK 7 从 `consistency` 拆到 `release` workflow**
（后者本就以 tag push 为唯一触发器）⇒ release PR 上不再需要 tag
⇒ **「先 PR 后 tag」自然走通**，且 **CHECK 13 在 release PR 上照常真跑**。

**但它涉及 CI 配置 + 分支保护（required checks），影响所有 PR**，
**超出 hotfix 边界**（不是"单一主题、无跨模块影响"）。**需要你决定。**

**若不做的后果**：顺序只能是**方案 C（先推 tag）**，
而方案 C 的「tag 打错位置无判据可察」是**已知未修的判据弱点**。

### Q2：第二层——**本仓 `AGENTS.md` 补顺序**（与 P8 无关）

条目 4 处写明：**bump commit → 分支 → release PR（`--no-ff`）→ 合并 → 再打 tag**，
并说明"为什么"（CHECK 7 需要 tag；main 受保护需 PR）。**这是本仓维护文档，我可以现在就改。**

### Q3：是否顺带加强 CHECK 7 判据？

让它检出「**tag 不是 HEAD 祖先** / badge 领先却无对应 tag」并给**明确指引**。
属 ADR-015 **手段②的加强**（让错误可见），不是新增手段③。

### Q4：P8 要不要动？

**我现在的判断：不要动。** 理由：
- P8 是**通用协议**，「推到哪、怎么合」**本就不属它的范围**；
- 本仓的 tag/PR 顺序问题是**本仓特有的**（因本仓 main 受保护 + 有 CHECK 7）；
- **把本仓的 GitHub 流程写进通用 P8 = 污染协议**（正是我原设计的错误方向）。

**若你认为 P8 该给"通用指引"**（如"若项目有远端/CI，bump commit 应先走 PR 再打 tag"），
**请明示**——那是一条**通用建议**，与本仓清单**不同层级**，需谨慎措辞。

---

## 5. 我的建议

| 优先 | 项 | 归属 | 风险 |
|---|---|---|---|
| 1 | **Q2 改本仓 `AGENTS.md` 补顺序** | 本仓维护 | 低（纯文档） |
| 2 | **Q1 拆 CHECK 7 到 release workflow** | **本仓 CI** | 中（改 required checks） |
| 3 | **Q3 加强 CHECK 7 判据** | 本仓脚本（触 SELF-GATE） | 低 |

**Q4（P8）建议不动**——除非你认为需要一条**通用**指引。

---

## 6. 复现与证据

| 证据 | 位置 |
|---|---|
| 设计文档（**前提有误，已标注**） | `docs/design-notes/design-release-order-boundary.md` |
| 独立评审报告（613 行，含逐条实测） | `docs/reviews/agate-design-review-2026-10-03-release-order.md` |
| CHECK 13 检查对象 | `agate/scripts/check-protocol-consistency.py:1194-1220` |
| docs-only 白名单 | `.github/workflows/protocol-tests.yml:97` |
| main 保护 | `gh api repos/randomgitsrc/agateon/branches/main/protection` |
| #394 CI 日志（CHECK 7 PASS） | `gh api .../actions/jobs/111228833680/logs` |

---

## 7. 诚实边界

- 本交接**未改动任何文件**（除本文件）；**未 push**。
- §1 的事实中，**3/10 条我曾写错**（见 §2），**均由独立评审查出并已复核**。
- **我的最大错误是前提性的**（把两个受众不同的文档当成副本），由**用户**指出，
  独立评审**未能发现**（它评审的是我给的错误框架内的推理）。
  ⇒ **评审能查事实与推理，查不出被当作前提的错误框定**——这条值得记。
