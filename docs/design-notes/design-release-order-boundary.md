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

**(b) 真跑 ⇒ CHECK 7 在「badge 已改、新 tag 未打」时 FAIL**
本地实测（删掉 `v0.78.0` tag、最新 tag 回退为 v0.77.0）：
```
❌ FAIL  CHECK 7  version badge 与 git tag
ERROR (1):  ❌ README version badge v0.78.0 != 最新 tag v0.77.0 [README.md]
```
⚠️ **机制更正**（独立评审查出，我已复核代码 `check-protocol-consistency.py:497`）：
**「必然 FAIL」的说法过宽**——`check_version_badge` 在 `git describe` **抛异常**时走
`rep.warn(...)` + `return`（**仅 WARNING，exit 0**）；`rep.error` 只在「**存在某 tag** 且与 badge 不等」时触发。
⇒ 准确表述是「**在本仓已有 74 个 tag 的现实下必然 FAIL**」；若仓库**完全无 tag**，CHECK 7 只是 WARNING。
**现实结论不变**（本仓有历史 tag），但机制描述此前有误。

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

## 3. 候选方案（**方案 A 已被独立评审证伪，本节据实重写**）

### 3.0 ⚠️ 我原推荐的方案 A 是错的（两个硬伤，均有代码证据）

**原方案 A**：把 `agate/UPGRADING.md` 加入 docs-only 白名单。

**硬伤 ①（MAJOR）：那会静默关掉一道门禁。**
我在旧版 §4 自问「`agate/UPGRADING.md` 是否只有文档语义？」，自答「**是，不参与 gate 判据**」——
**与代码相反**。实测（读 `check-protocol-consistency.py:1194-1220`）：
```python
# ── CHECK 13: CHANGELOG 最新版本 ↔ UPGRADING 章节对应性（RM-AG0052）──
upgrading = root / "agate" / "UPGRADING.md"
```
**CHECK 13 的检查对象正是该文件**，其设立缘由写明是 v0.62.0/v0.63.0「连续两次发布漏写 UPGRADING 章节」。
⇒ 方案 A 让 `consistency` fast-pass ⇒ **在 release PR 上把这道门禁整个关掉**——
而 release PR **恰是它唯一有意义的触发场合**。

**硬伤 ②（MAJOR）：也达不到「语义干净」。**
`docs-check.yml` 是**独立 workflow**，`on.paths` 含 `README.md` / `CHANGELOG.md` / `README.zh-CN.md`
——**release PR 必改** ⇒ 每次触发；其 job 跑：
```yaml
run: python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
```
**`--strict-errors-only` 仍会真跑 CHECK 7** ⇒ badge 领先时 exit 1 ⇒ **PR 上仍挂红灯**。
（所幸 `docs-consistency` **不是 required check**，故不 block 合并——「卡死」结论仍成立，
但方案 A 承诺的「走通且干净」不成立。）

**硬伤 ③（MAJOR）：越过 docs-only 的语义边界。**
`docs/guides/ci-docs-only-playbook.md` §2.1 逐字把 `agate/` 列为「**必然全量**」前缀；
workflow 头部注释把 docs-only 定义为**自由内容面**，而 `agate/` 是**治理面**。
UPGRADING 虽是 `.md`，但位于协议本体树**且被判据消费**。

### 3.1 方案 B：豁免 `consistency`（否决）

与 ADR-015 手段②（让错误可见）相悖，且靠人记得 ⇒ 要求型规则。

### 3.2 方案 C：先推 tag（今晚实际走通的路径）—— **可接受但有隐蔽风险**

- **能走通**：#394 实证（tag 已推 ⇒ CI checkout 看得到 ⇒ CHECK 7 PASS）
- **风险比我原描述更隐蔽**：独立评审实测——**把 tag 指向 `HEAD~5`（与 bump commit 无关），
  CHECK 7 照样 PASS**。因为判据**只看 tag 的名字**，不校验它指向何处、是否为 HEAD 祖先、
  是否与 bump commit 一致。
- ⇒ 方案 C 下若 tag 打错位置（或 PR 被否决留下悬空 tag），**没有任何机械判据会发现**。

### 3.3 **方案 D（推荐）：拆 PR——release PR 保持天然 docs-only**

```
① `agate/UPGRADING.md` 单独一个 PR（只改它 + 必要时 CHANGELOG 并存？——见下）
② release PR 只含 3 个白名单内文件：CHANGELOG.md / README.md / README.zh-CN.md
   ⇒ detect-docs-only 判为 docs-only ⇒ consistency fast-pass
③ 先合 UPGRADING PR，再合 release PR
④ **合并后**再打 tag（此刻语义干净：tag 指向已在 main 上的 bump commit）
```

**但方案 D 有一个必须解决的耦合**：**CHECK 13 要求 CHANGELOG 的最新已发布版本条目
与 UPGRADING 章节对应**。若 `UPGRADING.md` 先合（此时 CHANGELOG 还是 `[Unreleased]`）、
CHANGELOG 后合，则：
- UPGRADING PR 上：CHANGELOG 无新版本条目 ⇒ CHECK 13 取「第一个已发布版本」（旧版）⇒ **可能不匹配**
- release PR 上：consistency 被 fast-pass 跳过 ⇒ CHECK 13 **不跑**

**⇒ 拆 PR 会把 CHECK 13 的校验时机打散。** 这与方案 A 的硬伤①是**同一类问题**。

### 3.4 因此，真正的结论是：**顺序问题无法只靠「改流程」解决**

| 方案 | 能否走通 | 副作用 |
|---|---|---|
| A 加白名单 | ✅ | ❌ 关掉 CHECK 13（release 场景唯一有效处） |
| B 豁免 | ✅ | ❌ 靠人记得 |
| C 先推 tag | ✅ | ⚠️ tag 打错位置**无判据可察** |
| D 拆 PR | ⚠️ | ❌ CHECK 13 校验时机被打散 |

**⇒ 四个方案都有实质副作用。根因不在流程，在 `consistency` 这个 job 把
「CHECK 7（需要 tag）」与「CHECK 13（检查即将发布的 UPGRADING）」放在了同一个 required 单元里，
而二者在发布流程中的**满足时点不同**（CHECK 7 要 tag 之后，CHECK 13 要 bump 之后即刻）。**

## 4. 推荐（修订版）：**分两层，先修判据，再修文档**

### 4.1 第一层：修 `consistency` job 的**耦合**（根因）

**问题**：`consistency` 作为**一个 required job**，同时承载两类**满足时点不同**的判据：

| CHECK | 需要什么 | 在发布流程中的满足点 |
|---|---|---|
| CHECK 7（badge ↔ tag） | **tag 已存在** | **tag 之后** |
| CHECK 13（CHANGELOG ↔ UPGRADING） | bump **已提交** | **bump 之后即刻** |

放在同一单元 ⇒ release PR 上**必须先有 tag**（为 CHECK 7）⇒ 逼出"先推 tag"的顺序。

**候选修法**（**需再评审，本文不擅定**）：
- **(i) 给 CHECK 7 加"发布进行中"的识别**：当 `CHANGELOG` 存在 `[Unreleased]` → 新版本条目
  已写但 tag 未打时，**明确报 ERROR 并给指引**（而非当前的"badge != 旧 tag"含糊报错）；
  **仍不解决 required check 的时序**。
- **(ii) 把 CHECK 7 从 `consistency` 拆到 `release` workflow**（后者本就以 tag push 为触发器）
  ⇒ release PR 上 consistency 不再需要 tag ⇒ **「先 PR 后 tag」自然走通**，
  且 CHECK 13 在 release PR 上**照常真跑**（bump 已提交，正是它的用武之地）。
  **这一条看起来最对症**，但**涉及 required checks 变更**（CI 配置 + 分支保护），
  **影响面大，须独立评审 + 用户确认。**

### 4.2 第二层：文档补「交界」（无论第一层是否做）

**`AGENTS.md` 发布清单**：在第 4 条明确顺序，并把"为什么"写清（CHECK 7 需要 tag、
main 受保护需 PR）。**这是最小、无争议的改动。**

**`P8-release.md`**：补一节「与仓库发布流程的衔接」，说明 P8 范围止于**发布准备**
（bump + local tag → READY），推送/合并/创建 Release 属仓库维护流程。

### 4.3 不推荐的做法（据实登记）

- **方案 A（加白名单）**：关掉 CHECK 13，**否决**
- **方案 B（豁免 required check）**：**否决**
- **方案 D（拆 PR）**：CHECK 13 校验时机被打散，**不推荐**（除非 4.1(ii) 先落地）

### 4.4 本文**不擅自决定**的部分

**4.1(ii)（拆分 CHECK 7 到 release workflow）涉及 CI 配置与分支保护**——
超过 hotfix 的「单一主题 + 无跨模块影响」边界，**应先征得用户同意并独立评审**。
**本文只把它作为候选提出，不落地。**

---

## 5. 验证计划（改完后如何确认"没问题"）

| # | 判据 |
|---|---|
| 1 | 文档层：`AGENTS.md` 与 `P8-release.md` 顺序表述**一致**（无第三处副本） |
| 2 | `check-protocol-consistency.py` **0 ERROR**（改 `agate/*.md` 后必跑） |
| 3 | 结构一致性 S0–S6 OK |
| 4 | **下一版发版实测**：按最终确定的顺序走一遍（v0.78.1） |
| 5 | 若采 4.1(ii)：须验证 **release PR 上 CHECK 13 仍真跑**（不能被 fast-pass 顺带跳过） |

---

## 6. 待用户确认（改之前）

1. **第一层（改 CI / 分支保护）做不做？** 我倾向**做**（4.1(ii) 最对症），但它超出 hotfix 边界，
   且改 required checks 影响所有 PR。**若不做，则顺序只能是方案 C（先推 tag）**——
   而方案 C 的"tag 打错位置无判据可察"是**已知未修的判据弱点**（独立评审实测）。
2. **第二层（文档）我可以现在就改**——它无争议。**要我先只改文档吗？**
3. **是否顺带加强 CHECK 7 判据**（独立评审建议）：让它检出
   「tag 不是 HEAD 祖先 / badge 领先而无对应 tag」并给明确指引。
   属 ADR-015 手段②的加强，**不是新增手段③**。

---

## 7. 独立评审的结论（供参考）

| 项 | 裁定 |
|---|---|
| 总体 | **NEEDS-REVISION**（本文不能直接作为改动依据）——**已据其修订** |
| 事实核验 | 10 条声称：7 属实、3 不实（正则引文失真 / `ERROR (1)` 非 `(2)` / **「无 tag 必然 FAIL」错**） |
| 「先 PR 后 tag 卡死」 | **成立**（评审未能构造可行的真绕过） |
| 方案 A | **否决**（削弱 CHECK 13 + 达不到干净 + 越界） |
| 替代推荐 | **拆 PR** + **加强 CHECK 7 判据**（本文 §3.3/§6-3 已纳入讨论） |
| 判据弱点 | **tag 指向 `HEAD~5` 照样 PASS**——只看名字，不校验指向 |

