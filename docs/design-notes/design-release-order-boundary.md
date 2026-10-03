# 设计：发布顺序的三处规定不一致（hotfix 前置分析）

> **日期**：2026-10-03 ｜ **性质**：设计分析（**未改动**）
> **触发**：用户在 v0.78.0 发版后发现「我先推 tag 再开 PR」顺序颠倒。
> **要求**：想清楚、设计好、确定合理、没问题，再改。

---

## 1. 事实（逐条实测，不推断）

### 1.1 P8 卡实际规定了什么

| 位置 | 原文 | 含义 |
|---|---|---|
| `P8-release.md:11` | releaser subagent **不执行** git commit/tag | 分工 |
| `P8-release.md:44` | 主 Agent 在 gate 后统一执行 **bump-version / git commit / git tag** | **bump 与 tag 同一 commit** |
| `P8-release.md:91` | 重跑 P5（含 CHECK 7）**应安排在 commit + tag 之后** | tag 先于验证 |
| **全文** | 检索 `push origin` / `main` / `保护分支` ⇒ **0 命中** | **P8 不涉及推送与合并** |

**⇒ P8 的范围是「发布**准备**」**（README: "P8 release preparation"），
产出 `P8-release.md` + bump commit + local tag，然后**转 READY**。
**「推到哪、怎么合进 main」不在 P8 范围内。**

### 1.2 `AGENTS.md` 实际规定了什么

| # | 内容 |
|---|---|
| 4 | `git tag vN.N.0 && git push origin vN.N.0`（**推 tag**） |
| 5 | CHECK 7 自动通过；ruff CI 绿 |
| 5a | Release 资产校验 |
| 6 | **release PR 合并后**最终验证（G-5） |

**⚠️ 顺序缺失（核心问题）**：清单把「推 tag」列在 **4**，把「release PR 合并」列在 **6** 的
**前提**里——但**从未说明 tag 与 PR 的先后**。字面顺序读起来是「先推 tag，再谈 PR」，
**这正是我今晚照做的顺序，也是撞上 branch protection 的原因。**

另有一条散落在别处：「**release PR 必须普通 merge（`--no-ff`），禁止 squash**」——
**它承认了 release PR 的存在**，但没与第 4 条建立顺序关系。

### 1.3 仓库的硬约束（实测）

```
gh api repos/.../branches/main/protection:
  required_status_checks = true
  enforce_admins        = true
  required: shellcheck×2, pytest×2, consistency, gate-backstop
```

**⇒ 不能直接 push main**（我实测被拒：`protected branch hook declined`）。
**⇒ 一切进 main 的改动必须走 PR。**

### 1.4 ⚠️ 关键实测：**「先 PR 后 tag」跑不通**（本节曾据错误推论写成相反结论）

**我最初的推论（错）**：release bump 是 docs-only ⇒ `consistency` job fast-pass 跳过
⇒ PR 能过 ⇒ 「先 PR 后 tag」可行。

**实测逐条推翻**：

**(a) release bump 不是 docs-only**
`protocol-tests.yml` 的 docs-only 白名单正则：
```
^(agate-workspace/roadmap/|agate-workspace/debt/|archived/|docs/|site/|HANDOFF-*|FIX-*|
  README.md$|README.zh-CN.md$|CHANGELOG.md$|NOTICES.md$|LICENSE$|.github/workflows/docs-check.yml$)
```
**`agate/UPGRADING.md` 不在其中**（只匹配 `agate-workspace/…`，不匹配 `agate/…`）。
逐文件判定 #394 的 4 个文件：
```
docs     CHANGELOG.md
docs     README.md
docs     README.zh-CN.md
非 docs  agate/UPGRADING.md   ← 使 docs_only=false
```
⇒ **`consistency` job 会真跑**，不是 fast-pass。

**(b) 真跑 ⇒ CHECK 7 在「badge 已改、tag 未打」时必然 FAIL**
本地实测：删掉 `v0.78.0` tag 后
```
❌ FAIL  CHECK 7  version badge 与 git tag
ERROR (2)
```
⇒ 若按「先 PR 后 tag」，**release PR 的 `consistency` 是 required check，必然红 ⇒ PR 被卡死**。

**(c) 那 #394 的 `consistency: SUCCESS` 是怎么来的？——因为 tag 那时**已经推了**
时间线（实测）：
```
tag v0.78.0 → af6e03e（**推送在 CI 之前**，即我那个"顺序颠倒"的操作）
CI run 37132008992  created=2026-10-03T15:05:34Z  sha=af6e03e
consistency job 日志：✅ PASS  CHECK 7  version badge 与 git tag
```
`consistency` job 用 `fetch-depth: 0` + `fetch-tags: true` ⇒ **看得到已推的 tag**
⇒ CHECK 7 PASS。

**⇒ 因果是反的**：**我那个"错误的顺序"，恰好是让 CI 变绿的原因。**
若真按"正确的顺序"（先 PR 后 tag）走，**PR 反而会被 CHECK 7 卡住。**

### 1.5 那到底什么顺序才对？（本次未解决的真问题）

| 顺序 | bump commit 进 main | CHECK 7 on PR | 结果 |
|---|---|---|---|
| **A 先 tag 后 PR**（我今晚做的） | ✅（tag 随 PR 进 main） | ✅ PASS（tag 已可见） | **能走通**，但语义别扭：tag 短暂指向未进 main 的提交 |
| **B 先 PR 后 tag**（直觉"正确"） | ✅ | ❌ **FAIL**（required check） | **被卡死**，除非豁免 consistency |

**⇒ 「正确的顺序」不是显然的，需要设计。** 这正是本文要解决的。

---

## 2. 不一致的根因

| 层面 | 问题 |
|---|---|
| **职责边界** | P8（协议卡）= 发布**准备**；`AGENTS.md` 清单 = **仓库维护流程**（含推送/合并/Release） |
| **缺失的粘合** | 两份文档**各自自洽**，但**交界处无人规定**：bump commit 准备好之后，**先 PR 还是先 tag** |
| **年代差** | P8 写于 branch protection 之前（其「无 push 步骤」在当时无碍）；baskProtection 加上后，**AGENTS.md 承接了 PR 要求但没承接顺序** |

**⇒ 这不是「谁写错了」，是「两份文档的交界没写」。**

---

## 3. 候选方案（**问题比初版设想的难**）

**约束**（全部实测）：
- `main` 受保护 ⇒ bump commit 必须走 PR；
- release bump **含 `agate/UPGRADING.md`** ⇒ **不是 docs-only** ⇒ `consistency` **真跑**；
- `consistency` 是 **required check**；
- CHECK 7 在「badge 已改、tag 未打」时**必然 FAIL**；
- 但 CI checkout `fetch-depth: 0` ⇒ **只看得到「已推送」的 tag**。

⇒ **核心矛盾**：**tag 必须在 main 上可见（供 CI），又必须在 PR 合并前就存在（否则 CHECK 7 卡 PR）**——
而 tag 若指向未进 main 的提交，语义上又不干净。

### 方案 A：**把 `agate/UPGRADING.md` 加入 docs-only 白名单**

它本来就是**纯文档**（升级说明），却被排除在 `agate/` 前缀之外 ⇒
release bump 因此变成"非 docs-only" ⇒ consistency 真跑 ⇒ 卡住。

加上它之后：release PR = **docs-only** ⇒ `consistency` **fast-pass 跳过**（CHECK 7 不跑）
⇒ **「先 PR 后 tag」走通**，且语义干净（tag 只在合并后打）。

- **优点**：**修的是真正的错配**（`agate/UPGRADING.md` 是文档，被判为非文档）；
  顺序变成显然的「PR → merge → tag」；不引入豁免
- **缺点**：改 CI 配置（需确认 docs-only 的语义边界是否允许 `agate/` 下的 md）
- **风险**：若某次 release bump **同时改了真代码**（如顺带修 `agate/scripts/*.py`），
  仍会是非 docs-only ⇒ consistency 真跑 ⇒ CHECK 7 卡住。**该情形需另行处理**（见方案 D）

### 方案 B：**PR 上临时豁免 `consistency`**（不推荐）

- **缺点**：**豁免 required check 是"绕过门禁"**，与 ADR-015 手段②（让错误可见）相悖；
  且豁免要靠人记得，正是"要求型规则"

### 方案 C：**tag 先推（现状做法），但要求 tag 指向将被合并的 commit**

- 即：bump commit → **推 tag** → 开 PR → 合并
- **优点**：**这就是今晚实际走通的路径**（#394 实证）
- **缺点**：tag 有一段时间指向"未进 main 的提交"；若 PR 被否决 ⇒ **悬空 tag**（须删除重打）
- **可辩护性**：`AGENTS.md` 已有「release PR 必须普通 merge（`--no-ff`）」——
  在 `--no-ff` 下 tag 指向 bump commit 是**正确的**（tag 就该指 bump 那个提交，不是 merge commit）

### 方案 D：**混合——按 release PR 是否 docs-only 分流**

```
若 release PR 仅含文档（CHANGELOG/README/UPGRADING）：
    → 方案 A（PR → merge → tag）：语义干净
若含非文档改动：
    → 把非文档改动**拆成独立 PR 先合**，release PR 仍保持 docs-only
```
- **优点**：不豁免任何门禁；顺序唯一且干净
- **缺点**：拆 PR 增加步骤（但**符合"让错误不可能"**）

---

## 4. 推荐：**方案 A + D**（A 为主，D 兜底）

**推荐 A 的理由**（而非 B/C）：

1. **A 修的是根因**：`agate/UPGRADING.md` **本来就是文档**，把它排除在 docs-only 之外是**错配**。
   修掉它，顺序自然变成显然的「PR → merge → tag」。
2. **B 是绕过门禁**——与我今晚刚写进 ADR-015 的原则直接冲突（"不造没人消费的门禁"的孪生：
   **也不要靠豁免绕过有消费的门禁**）。
3. **C 虽能跑通（今晚实证），但留下"悬空 tag"风险**——PR 被否决时须记得删 tag，
   属"要求型"依赖。

**D 作为兜底**：明确登记「release 若含非文档改动 ⇒ 拆 PR 先合」，
不假装该情形不存在。

### ⚠️ 方案 A 需要先确认的一件事

**docs-only 白名单加入 `agate/UPGRADING.md` 是否安全？**
- 它是否**只有文档语义**？（是——升级说明，不参与 gate 判据）
- 会不会被滥用？（`agate/` 下**只有这一份纯文档**是 release 必改项；
  `agate/*.md` 如 `WORKFLOW.md`/`adr.md` 是**协议正文**，改它们**不该**算 docs-only）
- **⇒ 应精确加 `agate/UPGRADING.md$`，而不是 `agate/` 前缀**（后者会把协议正文放进来，
  **那会削弱 gate**，属安全退化）

## 6. 待确认（改之前想征求意见）

1. **方案 B 的措辞**是否准确？特别是"P8 范围止于 READY"这个界定对不对？
2. §1.4 的**边界情形**（release 含非文档改动 ⇒ consistency 真跑 ⇒ CHECK 7 ERROR）——
   应写成「拆 PR 先合」还是「临时豁免 required check」？**我倾向前者**（更符合"让错误不可能"），
   但可能在某些情况下不可行（如 bump 与代码修复强耦合）。
3. 是否需要同时改 `agate/WORKFLOW.md`（主流程表 :327 的 P8 行）？**我倾向不改**——
   那里只描述 gate 判据，不涉及推送；改了反而增加第三处副本（ADR-014 的教训）。
