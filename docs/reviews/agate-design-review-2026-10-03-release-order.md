---
review_date: 2026-10-03
reviewer: independent adversarial design review
role_basis: agate/assets/review-roles/protocol-alignment-review.md + agate/assets/templates/dispatch-prompt.md（评审/验收角色节）
change_summary: 对「发布顺序的三处规定不一致」设计分析做对抗式评审（设计阶段，代码与协议未改动）
---

# 独立对抗式评审：发布顺序边界设计分析

## 0. 对象锚定（先自核，防对象漂移）

| 项 | 值 |
|---|---|
| commit | `69cf600a8064ec8be416e0f691cec3a0a5fa3644`（`69cf600`） |
| 分支 | `design/release-order-boundary`（HEAD 即该 commit） |
| 文件 | `docs/design-notes/design-release-order-boundary.md` |
| **sha256（committed）** | `b3c1d2f3d110b3e0b38b45c4b846f1ac65a4eed85628eed0ea028ab5b30cc95b` |
| **sha256（worktree）** | `b3c1d2f3d110b3e0b38b45c4b846f1ac65a4eed85628eed0ea028ab5b30cc95b` |

**结论：无对象漂移。** committed 与 worktree 哈希逐位相同。

```
$ git show 69cf600:docs/design-notes/design-release-order-boundary.md | sha256sum
b3c1d2f3d110b3e0b38b45c4b846f1ac65a4eed85628eed0ea028ab5b30cc95b  -
$ sha256sum docs/design-notes/design-release-order-boundary.md
b3c1d2f3d110b3e0b38b45c4b846f1ac65a4eed85628eed0ea028ab5b30cc95b  docs/design-notes/design-release-order-boundary.md
$ git status --porcelain   # 空——评审前后均空
```

**只读纪律遵守情况**：全程未执行任何写仓 git 命令，未编辑任何被评审文件，未切换分支，未创建/删除/推送任何 tag。CHECK 7 的破坏性实测**全部在 `/tmp` 副本**（`git clone --no-hardlinks`）内完成，实测后已核验真实仓库 `git status --porcelain` 为空、HEAD 仍为 `69cf600`、`v0.78.0` 仍指向 `af6e03e`、tag 总数仍为 74。

---

## 1. 事实核验（逐条：属实 / 不实 + 命令与输出）

### 1.1 P8 卡 0 处提及 push/main/保护分支 —— **属实**

```
$ git show 69cf600:agate/phase-cards/P8-release.md | grep -c "push origin"     → 0
$ git show 69cf600:agate/phase-cards/P8-release.md | grep -cw "main"           → 0
$ git show 69cf600:agate/phase-cards/P8-release.md | grep -c "保护分支"         → 0
$ git show 69cf600:agate/phase-cards/P8-release.md | grep -n "git push"        → (无匹配，exit 1)
```

全文 162 行。**`main` 的 0 命中是 `grep -w` 的结果**——若用普通 `grep main` 会命中 L36/L42/L46 的「主 Agent」「合并 subagent」等**子串假阳性**。作者写「检索 `push origin` / `main` / `保护分支` ⇒ 0 命中」，用词检索的严格口径下**属实**；需注意 `main` 一项只有在词边界口径下才为 0，作者未标注此口径（见 §5(b) 残留问题）。

### 1.2 引用的 P8 行号 —— **属实（逐行校验）**

| 文档称 | 实测内容 | 判定 |
|---|---|---|
| `P8-release.md:11` | `2. releaser subagent 产出 P8-release.md，**不执行 git commit/tag**` | ✅ 逐字相符 |
| `P8-release.md:44` | `5. 主 Agent 在 gate 验证通过后统一执行 bump-version / git commit / git tag` | ✅ 逐字相符 |
| `P8-release.md:91` | `P5 重跑应安排在 **commit + 创建 git tag 之后** 进行，而非 bump 版本文件后立即重跑——` | ✅ 逐字相符 |

补充（作者的界定得到**第四条**独立支撑，作者未引）：`P8-release.md:146` 推进条件含 `- [ ] git tag 已创建`，`L159` 写 `READY → DONE：任务完成，代码可合并/发布`。三处合观，「P8 止于本地 tag + READY、不含推送与合并」**成立**。

### 1.3 `AGENTS.md` 发布清单未写 tag 与 PR 的先后 —— **属实**

```
$ git show 69cf600:AGENTS.md | sed -n '161p'
4. `git tag vN.N.0 && git push origin vN.N.0`——`git push` 不带 tag **默认不推送 tag**（v0.51.0 教训）；推送后 `git ls-remote --tags origin vN.N.0` 验证远端到达
$ git show 69cf600:AGENTS.md | sed -n '166p'
6. **release PR 合并后最终验证（G-5）**：`git fetch origin && git describe --tags --abbrev=0 origin/main` == vN.N.0；...
```

清单共 6 条（L158-166）。条目 4 = 推 tag，条目 6 = **「release PR 合并后」**最终验证。**两者之间无任何先后规定**——「release PR」在条目 6 中首次出现，且仅作为验证时点的**前提**出现。作者称「从未说明 tag 与 PR 的先后」**属实**；称「字面顺序读起来是先推 tag」也是对该清单的**合理**解读（4 在 6 之前）。

> ⚠️ 但需指出：条目 6 的措辞「release PR **合并后**」实际上**隐含**了「PR 存在于合并之前」这一事实，却**未隐含**「tag 在 PR 之前还是之后」。作者的「顺序缺失」判定准确，但其「这正是我照做的顺序」属**作者自述行为**，非文档可证事实（见 §5(c)）。

### 1.4 `main` 受保护 —— **属实，且逐字段相符**

```
$ gh api repos/randomgitsrc/agateon/branches/main/protection
required_status_checks.contexts =
  ["shellcheck (ubuntu-latest)","shellcheck (windows-latest)",
   "pytest (ubuntu-latest)","pytest (windows-latest)",
   "consistency","gate-backstop"]
required_status_checks.strict   = true
enforce_admins.enabled          = true
allow_force_pushes.enabled      = false
allow_deletions.enabled         = false
```

作者 §1.3 写 `required_status_checks = true`、`enforce_admins = true`、`required: shellcheck×2, pytest×2, consistency, gate-backstop` —— **六项 contexts 逐字相符**。

**⚠️ 作者遗漏了一个对结论有实质影响的字段**：`required_status_checks.strict = true`（即「Require branches to be up to date before merging」）。这意味着 release PR **必须与 main 同步**才能合并。对本设计的影响：**方案 C（先推 tag）下，若合并前 main 有新提交，PR 需先 update branch → 触发新一轮 CI → 又是 tag 在、CI 绿**（无害）；但**方案 B/A 的「先 PR 后 tag」在 strict 下更需要 tag 及时存在**。见 §2.3。

### 1.5 docs-only 白名单不含 `agate/UPGRADING.md` + #394 四文件逐条判定 —— **属实**

白名单**实际正则**（`protocol-tests.yml:97`，逐字取出）：

```
^(agate-workspace/roadmap/|agate-workspace/debt/|archived/|docs/|site/|
  HANDOFF-[^/]*\.md$|FIX-[^/]*\.md$|README\.md$|README\.zh-CN\.md$|
  CHANGELOG\.md$|NOTICES\.md$|LICENSE$|\.github/workflows/docs-check\.yml$)
```

**⚠️ 不实之处（引用失真）**：设计文档 §1.4(a) 把该正则**当作逐字引文**呈现，但写成
`HANDOFF-*` / `FIX-*`，**实际是 `HANDOFF-[^/]*\.md$` / `FIX-[^/]*\.md$`**。语义差异实质
（`HANDOFF-*` 会匹配任意后缀，实际限定为「无斜杠 + 以 .md 结尾」），**但作为引文不忠实**。属
MINOR 引文失真，不改变结论。

逐条判定 #394 的 4 个文件（`gh pr view 394` 确认文件集；对白名单正则实测）：

| 文件 | 白名单匹配 | 作者判定 | 复核 |
|---|---|---|---|
| `CHANGELOG.md` | ✅ `CHANGELOG\.md$` | docs | ✅ |
| `README.md` | ✅ `README\.md$` | docs | ✅ |
| `README.zh-CN.md` | ✅ `README\.zh-CN\.md$` | docs | ✅ |
| `agate/UPGRADING.md` | ❌ 不匹配（`agate/` 前缀整体在白名单外） | 非 docs | ✅ |

**`git show --stat af6e03e` = 恰好这 4 个文件**，与 `gh pr view 394` 的文件集一致。
⇒ `docs_only=false`。**CI 日志实证**（`gh api .../jobs/111228805814/logs`）：`docs_only=false`。

结论：作者 §1.4(a) **属实**（引文瑕疵除外）。

### 1.6 无 tag 时 CHECK 7 必然 FAIL —— **⚠️ 部分不实（这是本次评审最重要的发现）**

作者 §1.4(b) 写：本地实测删掉 `v0.78.0` tag 后 `❌ FAIL CHECK 7` + **`ERROR (2)`**，并据此断言
「CHECK 7 在『badge 已改、tag 未打』时**必然 FAIL**」。

**实测（/tmp 副本，真实仓库未动）**：

场景一（删除 v0.78.0，最新 tag 回退为 v0.77.0，badge=v0.78.0）：
```
$ git tag -d v0.78.0
$ python3 agate/scripts/check-protocol-consistency.py
  ❌ FAIL  CHECK 7  version badge 与 git tag
  ERROR (1):
    ❌ README version badge v0.78.0 != 最新 tag v0.77.0 [README.md]
exit=1
```

**ERROR 数为 1，不是作者写的 `ERROR (2)`。**（作者可能把 `check-structure-consistency.py` 的
输出或旧版本计数一并计入；无法从本文复核，但**当前脚本实测为 1**。）FAIL 与 exit 1 本身**属实**。

场景二（**仓库完全无 tag**）：
```
$ git tag | xargs -r git tag -d          # 74 → 0
$ git describe --tags --abbrev=0         # fatal: 没有发现名称
$ python3 agate/scripts/check-protocol-consistency.py
  ⚠️  WARN  CHECK 7  version badge 与 git tag
  仅有 399 个 WARNING，无 ERROR。
exit=0
```

**⇒ 无 tag 时 CHECK 7 只是 WARNING，consistency 退出 0 = PASS。** 依据 `check-protocol-consistency.py:496-498`：
`git describe` 抛 `CalledProcessError` → `rep.warn(...)` → `return`。**FAIL 分支只在「存在旧 tag 且
与 badge 不等」时走到（L499-502 的 `rep.error`）**。

**⇒ 作者的「必然 FAIL」不成立，正确表述是「在仓库已有任何历史 tag 的现实中必然 FAIL」**。
本仓有 74 个 tag，故现实场景下作者结论**碰巧正确**；但**机制描述错误**，且由此遗漏了一条真实绕过路径（§2.2）。

### 1.7 #394 的 `consistency: SUCCESS` 因为 tag 已推 —— **属实，双证据**

时间线（`gh api .../actions/runs?head_sha=af6e03e`）：

| 时间 (UTC) | 事件 |
|---|---|
| 15:04:00 | **tag push**（`branch=v0.78.0`，Release/Site Check/Protocol Tests 三 workflow 起） |
| 15:05:18 | **分支 push**（`branch=release/v0.78.0`） |
| 15:05:34 | **PR #394 CI**（run `37132008992`，`event=pull_request`） |
| 15:05:46 | `consistency` job（`111228833680`）启动 |
| 15:09:06 | PR #394 合并（merge commit `0b93088`） |

⇒ **tag 推送（15:04:00）确实早于 PR CI（15:05:34）**，作者 §1.4(c) 时间线**属实**。

日志证据（`gh api .../jobs/111228833680/logs`）：
```
✅ PASS  CHECK 7  version badge 与 git tag
仅有 398 个 WARNING，无 ERROR。
```
⇒ consistency **真跑**且 CHECK 7 PASS。且 `detect-docs-only` 输出 `docs_only=false`，
`pytest` 同 run 实测 `2555 passed, 9 skipped in 137.63s` ⇒ 全部 job **真跑**，无 fast-pass。

job 配置与作者 §1.4(c) 描述相符（`protocol-tests.yml:256-259`）：`fetch-depth: 0` + `fetch-tags: true`
⇒ CI 看得到已推 tag。

**因果方向**：作者称「我那个『错误的顺序』恰好是让 CI 变绿的原因」——
**机制上属实**：若 tag 未推，CI 的 `checkout` 取不到 `v0.78.0`，`git describe` 会返回 `v0.77.0`
⇒ CHECK 7 ERROR ⇒ `consistency` FAIL ⇒ required check 未绿 ⇒ 卡合并。

### 1.8 事实核验汇总

| # | 作者声称 | 判定 |
|---|---|---|
| P8 卡 0 处 push/main/保护分支 | 属实（`main` 需 `-w` 口径） |
| P8 行号 11/44/91 | 属实（逐字） |
| AGENTS.md 未写先后 | 属实 |
| main 受保护 + 6 contexts | 属实（**漏记 `strict=true`**） |
| 白名单正则引文 | ⚠️ **不实**（`HANDOFF-*`≠`HANDOFF-[^/]*\.md$`） |
| #394 四文件判定 | 属实 |
| 无 tag 时 CHECK 7 必然 FAIL | ⚠️ **部分不实**（无 tag ⇒ 仅 WARN，exit 0） |
| 删 v0.78.0 后 `ERROR (2)` | ⚠️ **不实**（实测 `ERROR (1)`） |
| #394 consistency SUCCESS 因 tag 已推 | 属实（双证据） |
| P8 范围止于发布准备 | 属实（L11/L44/L91/L146/L159 五处支撑） |

---

## 2. 核心结论的证伪尝试：「先 PR 后 tag 会被卡死」成立吗？

**判定：在作者的隐含前提下成立；但作者遗漏了 3 条绕过路径，且其推荐方案 A 自身制造了新问题。**

### 2.1 前置确认：required check 的触发是否覆盖 release PR —— **覆盖，作者此点属实**

作者未明说但关键的一点，我实测确认：`consistency` **没有 job 级 `if`**（`protocol-tests.yml:250-252`
只有 `needs: detect-docs-only`），fast-pass 是**内嵌在 run step 里**（L267-270）⇒ 无论如何都会产生
`success` 的 check-run。这与 workflow 头部修复史③一致，也解释了为何「docs-only ⇒ 永久 BLOCK」的
历史坑不再出现。**`paths-ignore` 已被移除**（头部①记述），**`on:` 为 `[push, pull_request]`**（L44），
无路径过滤 ⇒ release PR 必然触发全套。

✅ 所以「consistency 会在 release PR 上跑」——**成立**。

### 2.2 绕过路径 ①（**作者未提出，最有力**）：仓库无 tag 时 CHECK 7 仅 WARN

见 §1.6 场景二。机制：`check_version_badge` 的 `except` 分支调用 `rep.warn` 而非 `rep.error`。

**评估**：这条路径在**本仓现实中不可用**——已有 74 个 tag，`git describe` 不会失败。它**证明的是
作者对判据的机制理解有误**，而非提供可操作绕过。⇒ **不构成可行绕过，但构成对「必然 FAIL」断言的证伪。**

### 2.3 绕过路径 ②（**作者未提出**）：`docs-check.yml` 的 `--strict-errors-only` 仍跑 CHECK 7

这是**最实质的发现**。`docs-check.yml` 是**独立 workflow**，`on: push/pull_request` 的 `paths:` 含
`README.md`、`CHANGELOG.md`、`README.zh-CN.md`（均为 release PR 必改文件，见 §1.5）⇒ **每个
release PR 都会触发它**，其唯一 job 执行：

```
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
```

实测（/tmp 副本，模拟方案 A 生效后：badge 已 bump 至 v0.78.0、最新 tag 仍为 v0.77.0）：
```
$ python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
  ❌ FAIL  CHECK 7  version badge 与 git tag
  ERROR (1):
exit=1
```

⇒ **即使方案 A 让 `protocol-tests.yml` 的 `consistency` fast-pass，`docs-check.yml` 的
`docs-consistency` 仍会真跑 CHECK 7 并 FAIL。**

**这条路径是否「卡死」PR？——不卡死，但留红灯。** 实测确认 `docs-consistency` **不是 required check**：
```
$ gh api .../branches/main/protection --jq '.required_status_checks.contexts | map(select(test("docs")))'
[]
```
⇒ 它红了**不会 block 合并**。**因此作者「先 PR 后 tag 会被卡死」在方案 A 生效后仍然成立**
（真正 required 的 `consistency` 被 fast-pass 了），**但方案 A 并没有得到作者承诺的「语义干净」**
——PR 上会挂一个红的 `docs-consistency`，与 ADR-015「让错误可见」的原则**直接冲突**。

**并且**（更严重）：见 §3，方案 A 会**同时** fast-pass 掉 CHECK 13——而 CHECK 13 正是为
「发布漏写 UPGRADING 章节」而设的门禁（RM-AG0052）。

**#394 的实证反证**：PR #394 上 Docs Check **确实跑了且成功**（run `37132008990`,
`docs-consistency: success`）——因为 tag 已推。这从反面印证：**tag 缺失时它会红。**

### 2.4 绕过路径 ③（作者未提出）：tag 指向任意提交即可让 CHECK 7 PASS

实测（/tmp 副本）：把 `v0.78.0` 指向 `HEAD~5`（一个**与 bump commit 无关**的旧提交）：
```
$ git tag v0.78.0 HEAD~5
$ git describe --tags --abbrev=0   → v0.78.0
$ python3 agate/scripts/check-protocol-consistency.py
  ✅ PASS  CHECK 7  version badge 与 git tag
  仅有 398 个 WARNING，无 ERROR。
```
**⇒ CHECK 7 只看 tag 的「名字」是否为最新，不校验它指向何处、是否为 HEAD 的祖先、是否与 bump
commit 一致。** 这是判据的**实质弱点**（作者未指出）：它无法阻止「tag 打错位置」，只能阻止
「tag 不存在或名字不匹配」。这对方案 C（先推 tag）的风险评估有直接影响——作者称方案 C 的风险是
「tag 短暂指向未进 main 的提交」，而**判据本身根本不会发现这种偏差**，风险比作者描述的**更隐蔽**。

### 2.5 核心结论裁定

| 断言 | 裁定 |
|---|---|
| 「consistency 是 required check」 | ✅ 实 |
| 「release bump 非 docs-only ⇒ consistency 真跑」 | ✅ 实（#394 日志实证） |
| 「CHECK 7 在 badge 已改、**存在历史 tag** 而新 tag 未打时必然 FAIL」 | ✅ 实（修正作者措辞后） |
| 「CHECK 7 在**无 tag** 时必然 FAIL」 | ❌ **不实**（仅 WARN，exit 0） |
| 「**先 PR 后 tag 会被卡死**」 | ⚠️ **在当前配置下成立**（consistency required 且会 ERROR） |
| 「方案 A ⇒ 先 PR 后 tag 走通且语义干净」 | ❌ **不成立**：`docs-check.yml` 会红（§2.3），且削弱 CHECK 13（§3.2） |

**⇒ 核心结论「会被卡死」本身经受住了证伪（我未能构造出可操作的真绕过），但支撑它的机制描述
有错误，且作者据此推荐的方案 A 引入了两个未察觉的副作用。**

---

## 3. 方案 A 的安全性裁定

### 3.1 会不会削弱 gate？—— **会，且比作者设想的更严重**

作者在 §4「方案 A 需要先确认的一件事」中自问「它是否只有文档语义？（**是**——升级说明，
**不参与 gate 判据**）」。**这个自答是错的。**

实测证据：`check-protocol-consistency.py:1194-1220` 定义 **CHECK 13
「CHANGELOG 最新版本 ↔ UPGRADING.md §3 章节对应」**，其**检查对象正是 `agate/UPGRADING.md`**：

```python
upgrading = root / "agate" / "UPGRADING.md"
...
rep.error("CHECK13-upgrading",
          f"CHANGELOG 最新版本 [{latest}] 在 agate/UPGRADING.md §3 无对应章节 ...")
```

注释明写其设立缘由：**「v0.62.0/v0.63.0 连续两次发布漏写 UPGRADING.md 版本章节（发布清单第 3 步
纯人工兜底失效）」**，即 RM-AG0052。

**破坏性实测**（/tmp 副本，删掉 `agate/UPGRADING.md` 的 `### v0.78.0` 章节以复现该故障）：
```
$ python3 agate/scripts/check-protocol-consistency.py
  ✅ PASS  CHECK 7  version badge 与 git tag
  ❌ FAIL  CHECK 13 CHANGELOG↔UPGRADING 章节对应
  ERROR (1):
exit=1
[已恢复 UPGRADING.md，副本 git status 干净]
```

⇒ **方案 A 生效后，`consistency` 在 release PR 上 fast-pass ⇒ CHECK 13 也被跳过。**
而 release PR **恰恰是 CHECK 13 唯一有意义的触发场合**（它只查「最新已发布版本」）。
**⇒ 方案 A 会在它要守护的那个 PR 上，把为防「漏写 UPGRADING 章节」而建的门禁整个关掉。**

这是**实打实的 gate 削弱**，性质上比作者担心的「`agate/` 前缀会放进协议正文」**更具体**：
不是抽象地「削弱」，而是**精确定位到一个已有 CHECK 的失效**。

### 3.2 语义边界对吗？加 `agate/` 下文件是否越界？—— **越界**

权威语义源（`.github/workflows/protocol-tests.yml` 头部 L33-34）：
> 协议定义：docs-only = 仅改动 docs 清单内路径（含 site/ 产品 Web 层…）；
> **workflow 自身改动不算 docs-only（跑全量）**。

`docs/guides/ci-docs-only-playbook.md` §1 把边界讲得更明确：
> - **纯内容改动**（`docs/`、`site/`、README、archived 等）必须快——不被 1300+ 用例的 pytest 全量拖住。
> - **治理改动**（AGENTS.md、`.github/workflows/`）必须全量——改了门禁本身必须验透。

同文 §2.1 逐字列出非白名单前缀：**「任何白名单外路径（AGENTS.md、workflow 文件、`agate/`、
`agate-workspace/` 非 roadmap/debt 部分）→ 全量」**。

⇒ **`agate/` 被明文列为「必然全量」**，其设计意图是「**协议本体 / 治理面**」，与 `docs/`（自由内容面）
刻意区分。`agate/UPGRADING.md` 虽名为 `.md`，但它是**协议本体树内的权威文档**，且是 **CHECK 13 的
直接输入**。把它移入白名单 = **把治理面的一个被判据消费的文件当作自由内容**，
**越过了设计边界**。

**⇒ 方案 A 在语义上不成立**，不只是「需要确认边界」。

### 3.3 「应精确加 `agate/UPGRADING.md$` 而非 `agate/` 前缀」——**判断对，但理由不完整**

作者理由是「`agate/` 前缀会把协议正文（`WORKFLOW.md`/`adr.md`）放进来」——**方向正确**。
但实测还发现一层作者未提：`agate/scripts/*.py` 也在 `agate/` 下，加前缀会把**判据脚本自身**
纳入 fast-pass（改判据脚本的 PR 将不再跑 consistency）。作者的「精确匹配」避免了这一更危险的后果
——**该判断应保留，且理由应补上「脚本」一类**。

**但精确匹配只解决「越界范围」，不解决「越界本身」**（3.1/3.2）——即使精确到单文件，CHECK 13
依然失效。**⇒ 精确匹配是必要不充分。**

### 3.4 是否还有其他 release 必改、但不在白名单里的文件？

**实测：`agate/UPGRADING.md` 是唯一一个。** 依据：连续三个 release commit 的文件集**完全相同**：

```
$ git show --stat af6e03e  # v0.78.0
 CHANGELOG.md | 4 ++++   README.md | 2 +-   README.zh-CN.md | 2 +-   agate/UPGRADING.md | 39 +++
$ git show --stat 10e3713  # v0.77.0  → 同 4 文件
$ git show --stat ae77dbb  # v0.76.0  → 同 4 文件
```

对白名单正则逐一实测：

| release 必改文件 | 白名单 |
|---|---|
| `README.md` / `README.zh-CN.md` | ✅ |
| `CHANGELOG.md` | ✅ |
| `agate/UPGRADING.md` | ❌ **唯一缺口** |

`AGENTS.md` 的「版本引用文件清单」（L170）另列「稳定版引用（文档优先写『稳定版』不写死版本号）」
——该条**不产生固定文件**，不构成额外缺口。**⇒ 作者的「只有这一份」判断属实。**

---

## 4. 我构造的替代方案（逐个评估）

### 替代 ①（**推荐主选**）：先 PR 后 tag，但让 release PR 保持 docs-only —— **拆出 UPGRADING**

不碰 CI 配置，改**流程**：release PR 只含 `README.md`/`README.zh-CN.md`/`CHANGELOG.md`（**三者均
在白名单内** ⇒ 天然 docs-only ⇒ consistency fast-pass），`agate/UPGRADING.md` 拆到**独立 PR**（非
docs-only ⇒ consistency 真跑 ⇒ CHECK 13 正常守护，但该 PR **不改 badge** ⇒ CHECK 7 不受影响）。

- **评估**：**可行性高**。CHECK 7 只在 badge 变动时才有风险；UPGRADING 单独 PR 不动 badge ⇒ 与 tag 无冲突。CHECK 13 需要「CHANGELOG 最新版本」与「UPGRADING 章节」同时可见——若两者分属不同 PR，**CHECK 13 在任一单独 PR 上都会读不到对方的新内容而 FAIL**。⇒ **需要顺序：先合 UPGRADING PR（此时 CHANGELOG 尚未 bump，CHECK 13 读旧版本，PASS）→ 再合 release PR（此时 UPGRADING 已在 main，但 release PR 是 docs-only，CHECK 13 被 fast-pass）**。**⇒ 可行，但 CHECK 13 在一次发布中实际从未校验**（与方案 A 同样的漏洞，但**不新增 CI 改动**，且 UPGRADING PR 上 consistency 真跑过）。
- **优于方案 A**：不修改 CI 配置（不触发 SELF-GATE、不需独立评审 CI 语义），不越过 docs-only 边界。
- **代价**：多一个 PR、多一轮 CI。

### 替代 ②：**tag 与 PR 并行，但先开 PR 拿到 PR 号后立刻推 tag**

作者考虑过「方案 C：先 tag」但未考虑「**PR 先开、tag 随即推**」的时序微调。

- **评估**：**最贴合现实且最少改动**。实测时间线显示 #394 的 tag（15:04）与 PR CI（15:05:34）
  相差仅 94 秒。若改成「**先 push 分支 → 开 PR → 立刻 push tag**」，则：PR 首次 CI 因 tag 未到
  而 `consistency` 红 → **推 tag 后 GitHub 不自动重跑**（除非有新的 push），需 `gh run rerun` 或
  空提交。**⇒ 明显劣于现状**（现状 tag 在前，CI 一次绿）。
- **结论：不推荐**，作者未提是对的。

### 替代 ③：**改 CHECK 7 判据本身**（作者未提出）—— 建议采纳为**配套改动**

现状判据有两个实测缺陷：
1. **无 tag → 仅 WARN**（§1.6）：发布中途「tag 尚未存在」与「仓库从未有 tag」不可区分。
2. **只看 tag 名字，不看指向**（§2.4）：tag 指 `HEAD~5` 也 PASS。

改法建议（供后续实现参考，非本评审结论）：在 `check_version_badge` 中，当 badge 版本 **>** 最新
tag 版本（即「badge 领先」）时，**检查该版本号是否已有 tag 存在**；若不存在 ⇒ 明确 ERROR 并给出
「先推 tag 或先合 PR」的指引；若 tag 存在但**不是 HEAD 的祖先** ⇒ WARN（悬空 tag）。

- **评估**：**方向正确**，属 ADR-015 手段②（机械判据）的**加强**，而非新增手段③。
- **代价**：这是改 `agate/scripts/` ⇒ **触发 SELF-GATE ⇒ 需独立评审 + `self-gate-review:` 留痕**
  ——比方案 A（改 CI 配置，同样触发）**并不更贵**，但**收益明确更高**（修的是判据实质缺陷）。
- **注意**：改判据**不能解决**「先 PR 后 tag 被卡」——卡点在于「badge 领先而 tag 未推」这一
  状态本身就该红。**⇒ 替代③ 是对方案 A 的补充，不是替代。**

### 替代 ④：**改 `fetch-depth` / `fetch-tags`**（作者在 §1.4(c) 隐约触及）—— **不可行**

作者指出 `consistency` 用 `fetch-depth: 0` + `fetch-tags: true` 才「看得到已推的 tag」。
反向想：**去掉 `fetch-tags: true` 是否能让 CHECK 7 看不到 tag 从而绕过？**

- **评估**：**这条路通向「让错误不可见」**，与 ADR-015 手段② 的**目的**（让错误可见）相反；
  且 `fetch-depth: 0` 本身就含全部分支/tag 历史，去掉 `fetch-tags` 大概率仍能 fetch 到 tag
  （`fetch-depth: 0` 拉全部历史，`git describe --tags` 仍可见）。**⇒ 既不可靠又违背原则，否决。**

### 替代 ⑤：**`workflow_dispatch` 手动补跑**（作者未提出）—— **不可行**

`protocol-tests.yml` 的 `on:` 是 `[push, pull_request]`（L44），**无 `workflow_dispatch`**。
且 `AGENTS.md` L164 记载 `release.yml` **同样没有 `workflow_dispatch`**（TAG0037 教训）。
即使加上，也**不解决** required check 必须在该 PR 的 head SHA 上为绿的问题。

### 替代 ⑥：**把 bump 拆成两次提交**（作者未提出）—— **不可行**

设想：commit1 只改 CHANGELOG/README（badge 不变），commit2 改 badge。CHECK 7 仍会在含 commit2
的 PR 上 FAIL（badge 领先 tag）——**拆分提交不改变 PR 的最终树状态**。否决。

### 替代 ⑦：**annotated tag 指向 merge commit**（作者未提出）—— **不可行，且与 G-5 冲突**

- CHECK 7 用 `git describe --tags --abbrev=0`，**annotated tag 同样被识别**（无差别）。
- 更关键是 **G-5 / `AGENTS.md:166` 要求 `git merge-base --is-ancestor vN.N.0 origin/main` 返回 0**，
  并要求 `AGENTS.md:174`「release PR 必须普通 merge（`--no-ff`）」——**tag 打在哪都必须是 main 的
  祖先**。指向 merge commit 意味着**合并后才能打 tag** ⇒ 回到「先 PR 后 tag」⇒ 仍撞 CHECK 7。
- **⇒ 不构成新路径**，反而是「先 PR 后 tag」的另一种表述。

### 替代 ⑧：**临时放松 branch protection（admin 合并）**（作者未提出）—— **明确否决**

`enforce_admins.enabled = true` ⇒ 现代码库**连 admin 也被拦**。放松保护需改设置，属
「用手段③（要求人做对）+ 绕过门禁」，与作者 §3 方案 B 的否决理由一致。**否决。**

---

## 5. 本文自身的诚实性核验

### (a) 改写是否真的发生？—— **有自述与文本内证，但无独立 git 证据**

- **文本内证充分**：§1.4 标题**明写**「**（本节曾据错误推论写成相反结论）**」；
  §1.4 正文**先列出**「我最初的推论（**错**）」再列「实测逐条推翻」——**结构上就是一次
  自我更正**，且**保留了错误版本**（未抹去），符合诚实复盘的做法。
- **commit message 佐证**（`git show 69cf600`）逐条记录：
  「⚠️ **关键：我的初步推论被实测推翻**（本文 §1.4 已据实改写）：原以为…实测：(a)…”」
- **但**：`git log --all -- docs/design-notes/design-release-order-boundary.md` **只有 `69cf600`
  一个提交**——该文件**首次入库即为改写后版本**，改写发生在**提交前的草稿阶段**，
  **仓库内无「改写前」版本可供比对**。
- **⇒ 判定：改写**极可能真实发生**（自述 + 文本内证 + commit message 三重一致），但**不可独立
  验证**。**这不算作者不诚实**，只是本评审**无法机械证实**该叙述。应如实标注为「不可独立核验」。

### (b) 改写后残留的错误论断 —— **有，两条**

| # | 残留错误 | 位置 | 严重度 |
|---|---|---|---|
| 1 | 「CHECK 7 在 badge 已改、tag 未打时**必然 FAIL**」——无 tag 时实际仅 WARN | §1.4(b)、§3 约束列表、§1.5 表格 | **MAJOR**（机制错误，掩盖了真实绕过面） |
| 2 | 「`agate/UPGRADING.md`…**不参与 gate 判据**」——实际是 **CHECK 13 的检查对象** | §4「需要先确认的一件事」 | **MAJOR**（该错误直接使方案 A 的安全性结论反转） |
| 3 | 白名单正则引文写成 `HANDOFF-*`/`FIX-*`，实际 `HANDOFF-[^/]*\.md$`/`FIX-[^/]*\.md$` | §1.4(a) | MINOR（引文失真） |
| 4 | 「删 tag 后 `ERROR (2)`」——实测 `ERROR (1)` | §1.4(b) | MINOR（计数不准） |
| 5 | §1.3「⇒ 一切进 main 的改动必须走 PR」漏记 `strict=true` | §1.3 | MINOR（不完整） |

**错误 1 与 2 都是「改写后的新文本里的错误」**，且**都是对机制的断言**——这正是本次评审最需要
指出的：**作者对自己方案的机制做了未实测的推断，然后当作事实写进了「实测」节。**

### (c) 未核对的现状声明 —— **有两条**

1. §1.3「（**我实测被拒**：`protected branch hook declined`）」——**作者自述的操作经历**，
   仓库内**无可复核痕迹**（未留日志/输出片段）。属**不可核验的现状声明**。
2. §1.4(c)「**推送在 CI 之前**，即我那个『顺序颠倒』的操作」——**该时间线我已独立复核并确认属实**
   （§1.7），**但作者当时是「推断」还是「实测」无法区分**（其行文写在「实测」标签下）。
   ⇒ 结论**恰好正确**，但**标注纪律**上应属「时间线推断 + 事后复核」。
3. §1.2「**这正是我今晚照做的顺序，也是撞上 branch protection 的原因**」——混合了
   「文档字面顺序」（可复核）与「我为何那样做」（不可复核）。**作者把两者写在同一条「事实」里**。

### (d) 诚实性总评

**总体诚实，且主动暴露了对自己不利的证据**（保留错误推论全文、明写「被推翻」）。这是**加分项**。
但本文存在一个**结构性诚实缺陷**：**§1 标题为「事实（逐条实测，不推断）」，而 §1.4 的
(a)(b)(c) 三条中，(b) 是错误推断、(c) 的时间线带有推断成分**——**「实测」标签被用得过宽**。
建议改动时把 §1 拆为「实测」与「推断」两节（与本报告第 7 节同一纪律）。

---

## 6. P8 卡的定位：「P8 范围止于发布准备（bump + local tag → READY）」—— **准确**

独立核验（未依赖作者引用）：

| 证据 | 原文 | 支撑 |
|---|---|---|
| `P8-release.md:11` | releaser subagent **不执行** git commit/tag | 分工在 P8 内完成 |
| `P8-release.md:12` | 主 Agent …→ **同一 commit + tag** | tag 是 P8 产出 |
| `P8-release.md:44` | 主 Agent 在 gate 后统一执行 bump-version / **git commit / git tag** | 同上 |
| `P8-release.md:146` | 推进条件：`- [ ] git tag 已创建` | tag 是进入 READY 的条件 |
| `P8-release.md:159` | `READY → DONE：任务完成，代码可合并/发布` | **合并/发布在 P8 之后** |
| `agate/WORKFLOW.md:327` | `\| P8 \| 发布准备 \| … \| —（**无自动后继：exit 0 后转 READY 由人/发布流程处理**）\|` | **明确「无自动后继」** |
| `agate/WORKFLOW.md:256` | `- P8 发布准备：涉及发布的任务必做` | 阶段名即「发布准备」 |
| `agate/WORKFLOW.md:328` | `\| READY \| 待发布 \| … \| 人手动 make publish → DONE \|` | 发布动作在 READY 之后 |
| P8 卡全文 | `grep -c "push origin"/-w main/"保护分支"` = **0 / 0 / 0** | 无推送规定 |

⇒ **「P8 = 发布准备，止于 bump commit + local tag + READY；推送/合并/Release 不属于 P8」——
判定准确，证据链完整（作者列了 3 条，实际有 5+ 条）。**

⚠️ **一处需作者注意的事实性修正**：作者 §3 末尾「**年代差**：P8 写于 branch protection 之前
（其『无 push 步骤』在当时无碍）」——**P8 卡最后一次实质修改是 2026-09-29**（`d9642a2`），
而 `AGENTS.md` 的 release PR 条目在更早的 `467fec7`（2026-09-20, TAG0037）已在讨论 Release 流程。
**「P8 写于 branch protection 之前」这一时间断言，作者未给出任何实测依据**（未给 branch protection
的启用时间）。⇒ **该条属 §5(c) 的「未核对的现状声明」**，应删或补证据。

作者 §6.3「是否需要同时改 `agate/WORKFLOW.md`（主流程表 :327 的 P8 行）？**我倾向不改**」——
**行号属实**（`WORKFLOW.md:327` 确为 P8 行），**且「不改」的理由（避免第三处副本，ADR-014）成立**。
补充一条支持证据：`WORKFLOW.md:313-330` 被 `check-structure-consistency.py` 的 **S-1/S-2 锚点**守护
（与 `rules/phases.yaml` 双向比对）⇒ **改动该表行有机械门禁成本**，更应慎改。**⇒ 作者此判断正确。**

---

## 7. 总体判定

### 判定：`NEEDS-REVISION`

**本文目前不能直接作为改动依据**，理由如下（按严重度）：

| # | 问题 | 影响 |
|---|---|---|
| **1** | **方案 A 会削弱 gate（MAJOR）**：`consistency` fast-pass ⇒ **CHECK 13 被跳过**，而 CHECK 13 正是为「发布漏写 UPGRADING 章节」（RM-AG0052, v0.62/v0.63 事故）而设，且 release PR 是其唯一有意义的触发场合。作者称 UPGRADING「不参与 gate 判据」**与代码相反**。 | **推荐方案的安全性结论反转** |
| **2** | **方案 A 未达成其目标（MAJOR）**：即使 fast-pass，`docs-check.yml` 的 `docs-consistency` 仍会真跑 `--strict-errors-only` 并 CHECK 7 FAIL（实测 exit 1）⇒ PR 上留红灯，非作者承诺的「语义干净」。 | **方案的收益被高估** |
| **3** | **方案 A 越过语义边界（MAJOR）**：`ci-docs-only-playbook.md` §2.1 明文把 `agate/` 列为「必然全量」前缀；头部 L33 定义 docs-only 为「自由内容面」。UPGRADING 位于**协议本体/治理面**。 | **方案在语义上不成立** |
| **4** | **「CHECK 7 必然 FAIL」机制错误（MAJOR）**：无 tag 时仅 WARN、exit 0（实测）。使 §1 的「实测」标签失真，并掩盖了判据弱点（§2.4）。 | **事实层需修正** |
| **5** | 白名单正则引文失真、`ERROR (2)` 计数不实、「P8 写于 branch protection 之前」无据（MINOR×3） | 引文纪律 |

**本文做对的部分（应保留）**：
- 三处规定交界未写的**根因分析正确**，且指出了**真实的文档缺陷**（AGENTS.md 清单确实缺顺序）；
- **#394 的时间线与因果分析经我独立复核属实**（§1.7）；
- **P8 定位准确**（§6），「不改 WORKFLOW.md」的判断正确；
- **主动保留被推翻的推论并明写「已据实改写」**——诚实性上的加分项；
- 「**精确匹配 `agate/UPGRADING.md$` 而非 `agate/` 前缀**」的判断正确（且应补充「`agate/scripts/*.py`
  也会被前缀纳入」这一更强理由）。

### 修订要求（供作者整改后重审）

1. **撤回或重做方案 A**：在 §4 的「需要先确认的一件事」中，把「不参与 gate 判据」改为
   「**是 CHECK 13 的检查对象**」，并据此重新评估——**最低限度**须论证「release PR 上 CHECK 13 被
   fast-pass 是否可接受」，或改用 **§4 替代①（拆 PR）**。
2. **补充 §2.3 的发现**：说明 `docs-check.yml` 的存在及其 `--strict-errors-only` 仍跑 CHECK 7，
   修正「语义干净」的说法。
3. **修正 §1.4(b)**：「必然 FAIL」→「**在仓库已有历史 tag（本仓 74 个）时必然 FAIL**」；
   `ERROR (2)` → `ERROR (1)`；并补记「无 tag ⇒ 仅 WARN（`rep.warn`, L497）」这一机制事实。
4. **修正白名单引文**为逐字正则（`HANDOFF-[^/]*\.md$` 等）。
5. **§1 拆分**为「已实测」与「推断」两节；「P8 写于 branch protection 之前」补证据或删除。
6. **补记 `required_status_checks.strict = true`**（§1.3），并说明其对方案选择的影响。
7. **新增一条候选方案**：**加强 CHECK 7 判据本身**（§4 替代③）——使「badge 领先而无对应 tag」
   成为**明确的、带指引的 ERROR**，并检出「tag 指向非 HEAD 祖先」。这属 ADR-015 手段②的加强。

---

## 8. 证据分层声明（严格区分「已实测」与「推断」）

### ✅ 已实测（本次评审亲自执行并可复现）

| 结论 | 手段 |
|---|---|
| 对象未漂移（sha256 逐位相同） | `git show` + `sha256sum` |
| P8 卡 0 处 push/main(词边界)/保护分支 | `grep -c` / `grep -cw` |
| P8 行号 11/44/91 逐字相符 | `sed -n` |
| P8 全文 5 处支撑「止于发布准备」 | `sed -n` 读 L11/12/44/146/159 |
| AGENTS.md 条目 4/6 无先后 | `sed -n '161p;166p'` |
| main 六项 required contexts + `strict=true` + `enforce_admins=true` | `gh api .../protection` |
| 白名单正则逐字（与作者引文不符） | `git show ...:protocol-tests.yml \| sed -n '97p'` |
| #394 四文件判定 = 3 docs + 1 非 docs | `gh pr view 394 --json files` + 正则实测 |
| `docs_only=false` on #394 | CI 日志 `111228805814` |
| #394 全部 job 真跑（`2555 passed`） | CI 日志 `111228833607` |
| #394 consistency CHECK 7 PASS | CI 日志 `111228833680` |
| **无 tag ⇒ CHECK 7 仅 WARN，exit 0** | /tmp 副本删全部 tag 后实跑 |
| 删 v0.78.0 ⇒ CHECK 7 FAIL，**ERROR (1)** | /tmp 副本实跑 |
| **`--strict-errors-only` 在 badge 领先时 exit 1** | /tmp 副本实跑 |
| **tag 指向 `HEAD~5` 仍 PASS** | /tmp 副本实跑 |
| **UPGRADING 缺章节 ⇒ CHECK 13 FAIL（exit 1）** | /tmp 副本实跑（已恢复） |
| CHECK 13 的检查对象是 `agate/UPGRADING.md` | 读脚本 L1194-1220 |
| `docs-consistency` **非** required | `gh api ... \| jq` map/select |
| tag 推送(15:04:00) 早于 PR CI(15:05:34) | `gh api .../runs?head_sha=af6e03e` |
| 三个 release commit 文件集恒为同 4 个 | `git show --stat` ×3 |
| 真实仓库未被本次评审改动 | `git status --porcelain`（空）+ `rev-parse` |

### 🔶 推断（未直接实测，标注依据强度）

| 推断 | 依据强度 |
|---|---|
| #394 若 tag 未推则 consistency 会 FAIL | **强**——由「CI 用 fetch-tags + 落盘状态推断」，且已实测「badge 领先 ⇒ CHECK 7 ERROR」 |
| 方案 A 生效后 release PR 上 CHECK 13 被跳过 | **强**——fast-pass 为 `exit 0` 前置返回，两处 consistency step 均被跳过（L267-278 逐字已读） |
| 作者「改写确实发生」 | **中**——自述+文本内证+commit message 一致，但仓库无改写前版本 |
| 「P8 写于 branch protection 之前」 | **无据**——作者未提供证据，我亦未查到 protection 启用时间，故不判定真假，只判「未核对」 |
| 「我实测被拒 `protected branch hook declined`」 | **不可核验**——作者自述 |

### ❌ 本次评审未做（及原因）

- **未**在真实仓库执行任何写操作、未删/建 tag、未切换分支（只读纪律）。
- **未**验证 `docs-check.yml` 在**真实 PR** 上因 tag 缺失而红的端到端实证（无法在不制造真实
  release PR 的前提下复现）；该结论由**脚本实测（exit 1）+ paths 触发条件 + #394 反证**三者合成，
  属**强推断**而非端到端实测，**已如实标注**。
