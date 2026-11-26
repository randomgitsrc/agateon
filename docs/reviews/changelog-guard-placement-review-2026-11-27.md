# CHANGELOG 质量判据该挂在哪儿 — 机制设计评审（2026-11-27）

> 评审角色：机制设计评审员（fresh context，独立判断）。
> 输入：lead 的三候选（P1 / P2 / P3）与 4 条前提事实；**其中 3 条经本评审复核后需修正**（见 §0）。
> 纪律：只读。除本文件外未修改任何仓库文件；未 commit / push / 改 git config / 改 `~/.dsh`。
> 实验全部在 `mktemp -d` 或工作区外临时副本进行，跑前跑后 `git status` 除本文件外无变化。

---

## 结论

**推荐 P2 的变体 P2′：判据挂 `pre-commit-gate.py`（拦截）+ 以 ERROR 级同步进 `check-protocol-consistency.py`（事后兜底），扫描面收到「`[Unreleased]` + 最新已发布版本段」，阈值 ≥3 命中且 ≥2 类 ⇒ 任意非 docs-only 提交立即阻断；且不设 warning 级、直接 ERROR。**

一句话理由：**只有 P2 同时在「hotfix 通道」和「不可 `--no-verify` 绕过」两个维度上成立**——本仓 211 个改过 `CHANGELOG.md` 的提交里 **186 个是 mixed（非 docs-only）**，而这类提交的 `gate-backstop` 会**逐提交回放 pre-commit hook**；纯 warning 方案已被本仓自身实测证伪（§3）。

> 关键非直觉结论：**「挂 CI」在本仓不等于「拦得住」**。`docs-check.yml` 不是 required check（实测 `gh api .../branches/main/protection` 的 6 个 required 里没有它），所以只挂 CI 的方案在纯 docs 提交上是**能合进去的**。

---

## 0. 对 lead 四条前提事实的复核（3 条需修正）

| # | lead 的陈述 | 复核结论 | 证据 |
|---|---|---|---|
| 1 | `check-changelog.py` 是存在性判据，仅 `phase == "P8"` 由 `pre-commit-gate.py:1085` 触发 | ✅ **属实**，但**漏了最关键的一点**：2m 分支**只 `stderr.write`，不 `sys.exit(1)`** ⇒ 连「存在性」都不阻断，是一条 warning。且它位于 `for state_file in state_files:` 循环内（`:767`）⇒ **没有 `.state.yaml` 的提交根本不进这段代码** | `sed -n '1085,1090p' agate/scripts/pre-commit-gate.py`：`if phase == "P8" and _run_script_rc(...) != 0: sys.stderr.write(...)` — 无 exit |
| 2 | hotfix 通道无任务目录、无 `.state.yaml`、不经过 P8 ⇒ 挂 `check-changelog.py` 拦不到 hotfix | ✅ **属实**，且已实证：本次问题涉及的 7 个提交（`8690c9d2`/`c8acd5ff`/`70f051ba`/`60ff46fd`/`9f9c12f4`/`38616417`/`3df9c9e8`）**全部 NO state.yaml** | `git show --name-only --format="" <c> \| grep state.yaml` → 7/7 无 |
| 3 | `docs-check.yml` 的 `paths` 含 `CHANGELOG.md` ⇒ 改 CHANGELOG 就会触发 CI；P3 可拦 | ⚠️ **前半属实、结论不成立**：`paths` 确实含（`:14`、`:27`），但 **`docs-consistency` 不是 required check** ⇒ 它红了**不阻止合并**。另有一半提交它压根不跑（见下） | `gh api repos/:owner/:repo/branches/main/protection --jq .required_status_checks.contexts` → `[shellcheck×2, pytest×2, consistency, gate-backstop]`，`index("docs-consistency")` → 空 |
| 4 | `pre-commit-gate.py` 已有 2a–2n 约 14 个检查项，每次 commit 都跑（按 phase 分派） | ⚠️ **「每次 commit 都跑」不准确**：**按 phase 分派**意味着 2a–2n 绝大多数**只在暂存了 `.state.yaml` 时才跑**（整段在 `:767` 的循环内）。实测：只暂存 `CHANGELOG.md` 时 **gate 全程 rc=0、零输出、0.05s** | 见 §2 实验 E-2 |

**额外发现（影响裁决，lead 未提）**：`check-protocol-consistency.py` 的 `NARRATIVE_DIRS` **包含 `CHANGELOG.md`**（`agate/scripts/check-protocol-consistency.py:83`），而 `Report.warn` 会对命中这类路径的告警打 `frozen=True` 并**聚合打印成一行**（`is_frozen_loc("CHANGELOG.md:1234")` 实测 `True`）。⇒ **任何挂在 consistency 里的 CHANGELOG warning 都会被折叠进「冻结文件 N 条」那一行**，连 CHECK 17 的名字都不会单独出现。这条直接决定了 §3 的结论。

---

## 1. 三方案对比表

| 维度 | **P1**（`check-changelog.py`，P8 内） | **P2**（`pre-commit-gate.py`） | **P3**（`check-protocol-consistency.py` CHECK 17） |
|---|---|---|---|
| **hotfix 通道能拦吗** | ❌ **完全不能**（无 `.state.yaml` ⇒ 不进循环；即使进了也只在 P8 判，且不阻断） | ✅ **能**，但**必须放在 `for state_file` 循环外** | ⚠️ **部分**：仅当提交含非 docs 文件时，经 required `consistency` job 才拦得住 |
| **能否被 `--no-verify` 绕过** | ✅ 不可（但 gate 本身可被绕过，见失效模式） | ✅ 不可——CI `gate-backstop` **逐提交回放** `pre-commit-gate.py`（`agate-ci-verify.py:246` `_replay_commit`） | ❌ 不适用（CI 即终局） |
| **纯 docs 提交（只改 CHANGELOG）** | ✅ 覆盖（P8 时） | ✅ 覆盖 | ❌ **漏**：`detect-docs-only` 判 `docs_only=true` ⇒ required 的 `consistency` job `exit 0` fast-pass（`protocol-tests.yml:273-276`），只剩**非 required** 的 `docs-check` 看到它 |
| **每次提交成本** | ~0（已在跑；脚本实测 **0.033 s**，含解释器启动 0.011 s） | **~5 ms**（单次正则扫全 `CHANGELOG.md` 实测 **5.00 ms**；且应**只在暂存了 `CHANGELOG.md` 时才跑**） | 0 增量（consistency 全量实测 **1.94 / 1.98 s**，本来就是 required job） |
| **失败面（谁会因此卡住）** | agate 任务 P8 提交者 | 任何改 CHANGELOG 的提交者（本仓实测 211 个提交，**186 个会真的跑到**） | 改 CHANGELOG 且同时动非 docs 文件的提交者（**186**）；纯 docs 的 **25** 个漏 |
| **失效模式** | ① hotfix 全漏；② 判据不阻断；③ 只判"`task_id` 在不在"，与"写得像不像过程日志"无关 | ① 放错位置（放进循环内）⇒ 静默失效，**本仓已有同款事故**（`check-debt.py` 首版放循环内，被评审实测证伪，见 `pre-commit-gate.py:1176-1179` 注释）；② 稳定版滞后 ⇒ 本机 hook 先不生效 | ① **非 required** ⇒ 不阻断合并；② 纯 docs 快路径漏检；③ warning 被折叠进"冻结文件"聚合行 |
| **存量影响（改动即上线）** | — | **0**（见 §4 实测：报错面只有 `0.77.0`/`0.78.0` 两个历史版本，而扫描面不含它们） | **0**（同上，且 `docs-check` 用 `--strict-errors-only`，WARNING 不影响 rc） |

**结论**：**P1 直接排除**（这是本次问题发生的通道，它结构性看不见）。**P3 单独用不够**（纯 docs 提交是 CHANGELOG 类改动的"主场"，却恰好是它漏掉的那一格）。**P2 是唯一在两条通道都成立的落点**；P3 应作为**事后兜底**（防 `--no-verify` 已由 gate-backstop 承担，P3 的价值是覆盖"有人绕过 hook 且没进 CI 回放面"的残余，以及给非本机开发者一个统一判据源）。

> 因此推荐 **P2′ = 判据实现为独立脚本（单源）+ 挂 pre-commit（ERROR，循环外）+ 挂 consistency（ERROR，同一函数）**。判据单源，两个入口共用，避免本仓已被记录过的"两处对同一事实结论相反"（`AGENTS.md`：`uncovered_gate_scripts()` 那次教训）。

---

## 2. 第 1 问：拦截面 —— 一次 hotfix 提交的完整路径推演

### 2.1 推演对象（真实提交，非构造）

用 `9f9c12f4`（本次 DSH 适配 hotfix，改动 8 个文件、含 `CHANGELOG.md` +36 行、**无 `.state.yaml`**）：

```
author: git commit
  └─ .git/hooks/pre-commit → ~/.agate/scripts/pre-commit-gate.sh → resolve-entry.py
       → 解析 AGATE_ROOT（本机实测 = ~/.agate/v0.83.4/agate，理由「全局 current」）
       → exec pre-commit-gate.py
          ├─ 0. 项目本地 hook .githooks/pre-commit-local（禁直提 main）— 过
          ├─ 1. 收集暂存的 *.state.yaml → **空集**（该提交无 .state.yaml）
          ├─ for state_file in state_files:  ← **整个 2a–2o 都不执行**
          ├─ 2z. check-debt.py（循环外，仅当暂存 tech-debt.md）— 不触发
          └─ 3. 扫 P{n}-*.md 产出（WARNING）— 不触发
          ⇒ exit 0，**零输出，0.05 s**（实验 E-2 实测）
  └─ .git/hooks/commit-msg → commit-msg-self-gate.py
       → 该提交含 agate/*.md ⇒ 检查 self-gate-review: — 仅 WARNING，exit 0
  └─ .git/hooks/pre-push → pre-push-gate.py — 提示型，exit 0
git push → PR
  └─ [A] protocol-tests.yml（on: [push, pull_request] 无 paths 过滤 ⇒ **必跑**）
       ├─ detect-docs-only: 该提交改了 agate/** ⇒ docs_only=**false**
       ├─ pytest / shellcheck: 跑全量（required）
       ├─ consistency: **跑全量** check-protocol-consistency.py（required）
       │    ⇒ **P3 在这里生效且能阻断** ✅
       └─ gate-backstop: **逐提交回放 pre-commit-gate.py**（required）
            ⇒ **P2 在这里二次生效且能阻断** ✅（即使作者 --no-verify 也逃不掉）
  └─ [B] docs-check.yml（paths 含 CHANGELOG.md ⇒ **也跑**）
       └─ docs-consistency: --strict-errors-only — **非 required** ⇒ 红了不阻止合并
```

### 2.2 对 P3 的专项核查（lead 特别要求）

**Q：改 `CHANGELOG.md` 是否必然触发 `docs-check.yml`？**
**A：不必然，有两个漏口。**

- **漏口 1 — 纯 docs 提交被 required 检查跳过。** `docs-check.yml` 的 `paths` 含 `CHANGELOG.md`（`:14`、`:27`）⇒ 它**会**跑。但它是**非 required**；而 required 的 `consistency` job 在 `docs_only=true` 时直接 `exit 0`：
  ```yaml
  # .github/workflows/protocol-tests.yml:273-276
  if [ "${{ needs.detect-docs-only.outputs.docs_only }}" = "true" ]; then
    echo "docs-only PR: consistency skipped (fast-pass, docs-check.yml 已跑 --strict-errors-only)"
  ```
  这个设计**预设了「docs-check 兜底」**——但没把 docs-check 设成 required，于是兜底是**软的**。
  实测：211 个改过 `CHANGELOG.md` 的提交里，**25 个是纯 docs-only**（`28560cfe`/`595132b6`/`62b31dc6`/`a8012a25`/`957794ee`/…）。
- **漏口 2 — `paths` 是 `pull_request` 级的**：`docs-check.yml` 只在**本次 PR 的 diff** 命中 `CHANGELOG.md` 时跑。对「PR 里改了 CHANGELOG，但改成过程日志的那笔在更早的 push 里」这种情形不构成额外保护（不过 required 的 `consistency` 会覆盖，见下）。

**Q：如果同时改了非 docs 文件（如 `agate/scripts/*.py`），`protocol-tests.yml` 是否也跑 consistency？**
**A：跑，而且是 required、且不过滤。** `detect-docs-only` 的 `NON_DOCS` 正则把 `agate/**` 判为非 docs（`protocol-tests.yml:103`）⇒ `docs_only=false` ⇒ `consistency` job **全量跑** `check-protocol-consistency.py`（`protocol-tests.yml:277`）+ `gate-backstop` 回放。
实测：211 个 CHANGELOG 提交里 **186 个是 mixed**（含非 docs 文件）——**包括本次全部 7 个问题提交**。

**Q：两条路径是否都可能漏？**
**A：是，但漏的集合不重叠，且 P2′ 把两个缺口都补上了。**

| 提交类型 | 实测计数 | required `consistency` | required `gate-backstop` | 非 required `docs-check` | **P3 单独** | **P2′** |
|---|---|---|---|---|---|---|
| mixed（含非 docs） | 186 | ✅ 跑 | ✅ 回放 | 不跑（paths 命中才跑） | ✅ 拦住 | ✅ 两道 |
| 纯 docs（只改 CHANGELOG 等） | 25 | ⚠️ fast-pass **exit 0** | ⚠️ fast-pass **exit 0** | ✅ 跑但**不阻断** | ❌ **漏** | ✅ pre-commit 拦住 |
| hotfix 本地 `--no-verify` | — | mixed 时仍拦 | ✅ 回放拦 | — | ⚠️ 视 mixed/docs | ✅ 回放拦 |

⇒ **P3 单独 = 25/211（约 12%）盲区，且盲区内不阻断**。这是 P3 的硬伤，不是调参能修的（要么改 docs-check 为 required，那会给所有纯 docs 改动加一道必过 check——**成本高于收益**；要么接受漏）。

### 2.3 什么情况下 P2 也拦不到（诚实边界）

- **部署滞后**：本机 hook 走**稳定版**（实测 `AGATE_ROOT=~/.agate/v0.83.4/agate`）。新判据要等下一次 release 装上才在本机生效——本仓已有同款登记（`CHANGELOG.md:979` 记 `commit-msg` 的 trailer 校验「要等下一次 release 装上才在本机生效；CI 侧由 pytest 守卫强制」）。
  ⇒ **这正是必须同时挂 P3/CI 的理由**：CI 用本 checkout 自己的脚本，**上线即生效**。
- **`AGATE_ROOT` 被指向未验证 checkout**（`AGENTS.md` 明确警告的情形）：回放面会跟着错，但这属既有风险，非本判据引入。

---

## 3. 第 2 问：成本

**逐项实测**（本机，`CHANGELOG.md` 185 633 bytes / 2944 行）：

| 动作 | 实测耗时 | 备注 |
|---|---|---|
| `check-changelog.py` 独立跑一次 | **0.033 s** | 其中裸解释器启动 0.011 s ⇒ 净逻辑约 0.02 s |
| 5 条正则扫整个 `CHANGELOG.md` | **5.00 ms** | 50 次平均；判据本体成本可忽略 |
| 完整 `check-protocol-consistency.py` | **1.94 / 1.98 s**（两次） | P3 的增量 ≈ 5 ms，占 0.25% |
| 完整 `pre-commit-gate.py`（只暂存 `CHANGELOG.md`） | **0.05 s** | 实验 E-2 |
| `gh api` 分支保护查询 | ~0.5 s | 仅本次评审用 |

**结论：三个候选的 CPU 成本都无关紧要**（最大者 5 ms）。真正的成本是**失败面**（谁会因此被卡住），不是耗时。这也意味着**"P2 会增加每次提交成本"这一顾虑应当被丢弃**——它是伪成本。

**P2 在没有 CHANGELOG 改动的提交上会不会也扫？**
- **如果照抄 2z 的写法（对任何提交都跑）= 会扫，且是纯浪费。**
- **我的建议：不要这样写。** 加一个前置门（一行）：
  ```python
  if any(f.replace("\\", "/").endswith("/CHANGELOG.md") or f == "CHANGELOG.md"
         for f in _staged_name_only()):
      ...
  ```
  这样 99% 的提交（不改 CHANGELOG 的）**零增量成本**，只有真正改 CHANGELOG 的提交付 5 ms。
- 顺带：**扫描面也应收到「`[Unreleased]` + 最新已发布版本段」**（约 1.8 KB，实测 `[Unreleased]`..`## [0.83.3]` 之间 1846 bytes），而不是全文 185 KB。理由见 §5.3——这决定了**存量影响是 0 还是需要一张豁免清单**。

> 本仓纪律对齐：`AGENTS.md` 明写「**新增判据 = 给所有使用者加成本**：先答『它会拦下几个真缺陷（举实例）』，答不出就不加」。本判据能举出的实例就是本次 7 个提交中的 **5 个会 FIRE**（§5.4 实测），不是构造。

---

## 4. 第 3 问：「warning 不阻断」在本仓是否真的有意义

**这是本次最关键的一问，因为用户的整条反对理由是「记了不看等于不记」。我的判断：warning 在本仓已被实测证伪到不可用；在本判据上，warning 级 ≈ 方案 A。**

### 4.1 实证一：本仓自己已经判定 warning 退化为噪音（并动手改了）

`CHANGELOG.md:751-763`（作者自述，我复核了代码）：

> **① 一致性检查的 386 条 WARNING 里，386 条（100%）来自冻结文件**
> - **两个 CI 入口都不看 WARNING**（`docs-check.yml` 用 `--strict-errors-only`；`protocol-tests.yml` 用默认模式）⇒ **没有任何东西消费它们**。
> - **实证其已退化为"要对齐的基线"**：`0 ERROR / 386 WARNING` 在 CHANGELOG 出现 4 次，且被标注「与基线一致」——它早已不是待处理信号。

代码侧同源（`check-protocol-consistency.py:119-126`）：
```python
# 实测：386 条 WARNING 中 383 条属此类，且 "0 ERROR / 386 WARNING" 在 CHANGELOG
# 出现 4 次并被标为「与基线一致」⇒ 已退化为需要长期对齐的噪音，不再是信号。
```

⇒ 这是**本仓对"warning 会被无视"的一次已落地的、带数据的判决**。不是我的推测。

### 4.2 实证二：同一模式在一个**只有 WARNING** 的机制上复犯了 6 次

`CHANGELOG.md:978-981`：

> 后置守卫（`test_selfgate_trailer_integrity.py`）取 `origin/main..HEAD`，而 **pre-commit 时该范围为空** ⇒ 只在**提交之后**生效 ⇒ **该缺陷已复犯 6 次**。

而 `AGENTS.md:56` 对这个机制的定性是：**「仅 WARNING、不拦截，强制力靠自觉」**。`CHANGELOG.md:1005` 又记：**「既有三道防线全没拦住——① 开发版 hook 只 WARNING 不拦截」**。
⇒ **一个纯 warning 的留痕机制，在同一个作者身上复犯 6 次**，最后是靠**加一道 CI 侧 pytest 守卫**（阻断级）才收住。

### 4.3 实证三：`2m` 本身就是一条被无视的 warning —— 而它就是 P1 的全部

`pre-commit-gate.py:1085-1089` 只在 P8 打 `GATE CHANGELOG: 警告 — ...`，**不 exit**。而 `CHANGELOG.md` 的 88 个版本段里，过程痕迹最严重的 `0.77.0`（192 行）/`0.78.0`（249 行）都是走正常流程产出的。**没有任何证据表明这条 warning 曾被消费过**——它甚至不在任何文档的"必须处理"清单里。
⇒ **把质量判据加进 `check-changelog.py`（P1）并给 warning 级，等于给一条已被证明无人读的警告再加一行字** = 方案 A。

### 4.4 实证四：warning 在 P8 这个"最后关口"尤其无效

P8 是发布前最后一步，此时作者的心态是"收尾、发版"；warning 出现在这里，最可能的处理是"知道了，先发"。而 `AGENTS.md` 的 ADR-015 手段优先级写得很清楚：**「① 让错误不可能 > ② 让错误可见（机械判据）> ③ 要求人做对」**，且「③ 尽量少用」。
⇒ warning 属于 ②/③ 之间，而**在"作者正忙着收尾"的时点，② 的实际效力退化到 ③**。

### 4.5 那 warning 在本仓还有没有正当用途？

**有，但只在一种情形：它指向一个"作者无法当场修、需要另一角色介入"的问题。** 例：`2f` 的 phase-产出一致性 WARNING——作者可能确实需要先提交产出、下一步再改 phase，warning 是在提醒"别忘了"。这类 warning 有**下一步动作**。

而本判据不同：**过程痕迹是作者当下就能改的**（删掉/改写那段）。对"当场可修"的问题给 warning，等于**主动放弃拦截**。⇒ **本判据应当 ERROR，不设 warning 档。**

### 4.6 结论

| 方案 | 实质 |
|---|---|
| 纯文档规范（A） | 记了不看 |
| **warning 级判据** | **在本仓 ≈ A**（实证：386 条 WARNING 无人消费；同一模式复犯 6 次；`2m` 自身即被无视的 warning） |
| **ERROR 级判据** | 唯一与用户诉求（"要有机械约束"）相符的档位 |

> 补充：`docs-check.yml` 用 `--strict-errors-only` 跑 consistency，所以**WARNING 在 CI 侧连 rc 都不影响**——这是"warning 无用"的机械证据，比任何论证都硬。

---

## 5. 第 4 问：判据怎么设计才不误伤

### 5.1 先定"过程痕迹"的可机械判据

过程痕迹的共同特征不是"某些词"，而是：**它描述的是"作者/评审者如何得出这个结论"，而不是"这个版本对读者做了什么"**。凡"删掉后读者仍能正确决策"的内容，都是过程痕迹（这一判据来自本次重写提交 `3df9c9e8` 的 commit message，我认可它）。

机械上，可抓的是**作者第一人称 + 评审活动 + 测试运行 + 自我修正史**这四类语义。逐类列词，并**逐类做误伤检验**：

### 5.2 建议词表（A1–A7，附误伤取舍）

| 类 | 正则 | 为什么这样写（防误伤） |
|---|---|---|
| **A1 作者第一人称** | `(?<![自])我(?!们\|方\|国\|司)` | **必须排除「我们」「自我」**。实测 `0.83.2` 段有 4 处「我」全是「**我们**生成的」「**我们**的旧 `- insert:`」——指代工具产物，正当。加 lookbehind 排除「自我」（`自我更正`是正当术语），加 lookahead 排除「我方/我国/我司」。 |
| **A2 评审轮次/编号** | `(?:二\|三\|四\|五\|两)轮(?:独立)?评审\|第[一二三四]轮(?:独立)?评审\|(?:独立)?评审\s*r?[1-9]\b\|SELF-GATE\s*r[1-9]` | 只抓**轮次**与**评审内编号**（`r1`/`F3`/`N-1`），不抓"评审"这个词本身。**误伤取舍**：本仓 `0.81.0` 有 2 处 `SELF-GATE r1 指出` —— 这是**正当引用**（说明某处实现为何如此）。所以 A2 **单独不应触发**，必须靠阈值（见 5.3）。 |
| **A3 评审过程叙述**（**不参与计数**，仅进提示文案） | `(?:经\|由\|被)?(?:二轮\|三轮\|独立)?评审(?:指出\|发现\|推翻\|抓出\|实证\|纠正)` | 单独看它误伤最重（正当写法「本版修复了独立评审发现的 X」必中）。**故不计数**，只在已触发时用于解释"你这里提到了评审过程"。实测去掉它不影响任何目标正例命中（§5.5 表）。 |
| **A4 测试运行计数** | `\b\d+\s*(?:passed\|failed)\b` | 只抓裸计数。**为什么不抓「实测」**：`实测` 在本仓是**正当术语**（`0.81.0` 有 10 处、`0.77.0` 有 54 处，绝大多数是"实测：该路径 exit 1"这种**证据引用**，读者确实需要）。**为什么不抓中文「N 个用例」**：`0.81.0` 的「实测 35 个用例转红」属证据而非过程。 |
| **A5 变异实验** | `变异(?:实验\|测试)` | 只抓"变异实验/测试"这一词组。`0.78.1` 的「两处守护均经**变异测试**确认非空转」算边缘正当（说明守护有效），但**单词不足 3 次不触发**。 |
| **A6 教训/勘误体裁** | `教训\|勘误\|复犯` 或整行 `^(?:###\s*)?(?:勘误\|反思)$` | 这三个词在本仓**只出现在过程叙述里**（实测 0 例正当用法）。这是**信噪比最高的一类**。 |
| **A7 版本内自我修正史** | `第一版\|上一版\|我原先\|我写错了\|我误判\|我当时` | **不抓「原先」「此前」单独出现**。实测 `0.81.0`/`0.76.0`/`0.82.0`/`0.80.2` 共 8 处「原先」，全部是**正当的变更说明**（「原先读到空文本、计数全 0 直接 return 0（假 PASS）⇒ 改为判 FAIL」——这正是读者要的"改了什么"）。必须要求**第一人称或"第一版/上一版"**这种指代作者稿次的词。 |

### 5.3 阈值（关键：阈值比词表更能防误伤）

**规则：单段内 A1–A7 总命中 ≥ 3 次，且覆盖 ≥ 2 个类别 ⇒ 判过程痕迹。**

为什么必须双条件：
- **只要词表不要阈值** ⇒ `0.81.0`（我用来证伪"行数判据"的那个反例）会被 A2 命中 2 次而误伤。
- **只要类别数不要次数** ⇒ 一段里 2 个类别各 1 次就报，太敏感。
- **双条件实测效果**（见 5.4）：`0.81.0` 命中 `tot=2 / cats=1` ⇒ **不触发** ✅；`0.78.0` `tot=24/cats=5`、`0.77.0` `tot=47/cats=5` ⇒ **触发** ✅。

**扫描面：`[Unreleased]` + 最新一个已发布版本段。** 理由：
- 全量扫描会让 2 个历史版本（`0.77.0`/`0.78.0`）永久报错 ⇒ 必须维护一张 ERROR 级豁免清单。而本仓 **CHECK 16 的教训**正是"冻结文件不得修改"要配登记表（`agate/rules/task-data/LEVELS.yaml`）。
- 收到最新段后**存量影响 = 0**（实测：`Unreleased`/`0.83.4`/`0.83.3` 三段均 `fire=False`），**不需要任何豁免清单**。
- 语义上也对：`docs/guides/doc-freshness-guide.md:84` 已把「**CHANGELOG 已发布版本的条目**」定义为**历史快照、「保留不动」**。对历史快照设门禁是自相矛盾的——**这条既有文档已经替我们决定了扫描面**。

### 5.4 反例验证（全部实测，命令见 §7）

**① 目标正例必须触发** —— 原始 145 行 v0.83.4（`git show 3df9c9e8^:CHANGELOG.md`）：

```
A3 参与计数：     lines: 145   total: 21   cats: 7   ⇒ FIRE = True
A3 不参与（推荐）: lines: 145   total: 18   cats: 6   ⇒ FIRE = True
  A1 作者第一人称: 4      A2 评审轮次: 6      A4 测试运行计数: 1
  A5 变异实验: 1          A6 教训体裁: 4      A7 自我修正: 2
```

**② 反例必须不触发** —— `0.81.0`（240 行、过程痕迹 0 的版本）：

```
total: 2   cats: 1   ⇒ FIRE = False
  仅命中 A2 x2（`SELF-GATE r1 指出`）—— 正当引用，被阈值挡住
```

**③ 真实 hotfix 提交回放**（模拟 pre-commit 只扫**新增行**）：

| 提交 | 新增行 | tot | cats | FIRE |
|---|---|---|---|---|
| `8690c9d2` hotfix: doctor 效力 | 49 | 2 | 2 | False（**漏**，见 5.6） |
| `c8acd5ff` hotfix: doctor 残留 | 29 | 9 | 4 | **True** ✅ |
| `70f051ba` hotfix: doctor 二轮 | 16 | 4 | 3 | **True** ✅ |
| `60ff46fd` hotfix: doctor 三轮 | 23 | 7 | 4 | **True** ✅ |
| `9f9c12f4` hotfix: DSH 适配 | 36 | 3 | 3 | **True** ✅ |
| `38616417` release bump（`Unreleased`→`[0.83.4]`） | 2 | 0 | 0 | False ✅（**改名不应被拦**，重要） |
| `3df9c9e8` 重写后 | 32 | 0 | 0 | False ✅（**合规写法不被拦**） |

⇒ 7 个真实提交里 **5 个拦下、2 个正确放行**（其中 1 个是漏，见下）。

**④ 构造的正当写法不触发**（手写用例）：

| 正当写法 | tot/cats | FIRE |
|---|---|---|
| 本版修复了独立评审发现的三个缺陷（详见 `docs/reviews/x.md`） | 1/1 | False |
| 该判据由独立评审提出，此前未被覆盖 | 0/0 | False |
| 默认值由 30 改为 60；实测在 4 核机器上延迟下降 | 0/0 | False |
| 回归：`pytest -q` 全绿，`check-protocol-consistency.py` 0 ERROR | 0/0 | False |
| 本版删除了变异测试辅助脚本 | 1/1 | False |
| 我们收窄了扫描面，避免误报 | 0/0 | False |

### 5.5 已知代价与最终取舍（A3 不计数）

**唯一真实误伤来源是 A3**：正当写法「本版修复了独立评审发现的 X」必中 A3。单次不触发（tot=1），但一段里出现 3 条这样的句子就会被判为过程痕迹。

**最终取舍：把 A3 从计数词表中移除，只保留为提示文案。** 理由是实测发现**去掉 A3 完全不损失检出**：

| 段 | A3 参与 | A3 不参与（**推荐**） |
|---|---|---|
| 原始 145 行 v0.83.4 | tot=21 cats=7 ✅ | **tot=18 cats=6 ✅** |
| `0.78.0` | tot=24 cats=5 ✅ | **tot=22 cats=4 ✅** |
| `0.77.0` | tot=47 cats=5 ✅ | **tot=41 cats=4 ✅** |
| `0.81.0`（反例，必须不触发） | tot=2 cats=1 ❌ | **tot=2 cats=1 ❌** |

⇒ **A1/A2/A4/A5/A6/A7 计数，A3 仅提示。** 这样「正当引用独立评审」这一类误伤被**结构性消除**（而非靠阈值压制），而目标正例（原始 145 行 v0.83.4、`0.78.0`、`0.77.0`）全部仍触发，反例 `0.81.0` 与合规段 `0.83.3`/`0.83.4` 仍不触发。

### 5.6 已知漏口（诚实登记）

`8690c9d2`（49 行新增，tot=2/cats=2）**不会被拦**。它的正文确实写了「第一版判断为「无硬性不兼容」是错的，独立评审用 registry 的 broken 状态推翻」——但因为**用词是「第一版」+「独立评审用…推翻」而非「我」**，A1=0、A7 未命中（A7 要求「第一版」紧接自我指代，此处是"第一版判断"）。

**处理**：**接受漏口，不加词**。理由——把 A7 放宽到任意「第一版」会命中 `0.80.2`/`0.76.0`/`0.82.0`/`0.81.0` 共 7 处正当的"原先/第一版"变更说明。**判据宁可漏一例，不可误伤七例**（这也是本仓 ADR-015「不造没人消费的门禁」的取向）。这个漏口应写进规范作为已知边界，让读者知道判据是**筛子不是闸门**。

---

## 6. 第 5 问：是否该同时保留文档规范

**该留，但只留一句话判据 + 正反例，且必须与判据同源落点。** 理由与做法：

### 6.1 为什么纯规范无效、但规范仍不可省

- 纯规范无效（用户已指出，我实证同意）：`docs/guides/doc-freshness-guide.md:58-60` 记着同款教训——「**它注定不被遵守**：同一会话里我在 CHANGELOG 写过两处未锚定数字（PR #388），**自然写作时 0/2 遵守**」。
- 但规范不可省，因为**机械判据只能给出"哪里有问题"，给不出"该写成什么"**。判据触发后作者若不知道该删什么、保留什么，就会做最小改动糊过判据（本仓已有先例：SG.6 的子串判定被一行注释骗过，见 `CHANGELOG.md:1123`）。**规范负责"改写方向"，判据负责"必须改"。**

### 6.2 写在哪（按"何时被读到"路由，遵循 `~/.dsh/AGENTS.md` 第 14 条）

| 落点 | 写什么 | 为什么在这里 |
|---|---|---|
| **`CHANGELOG.md` 顶部注释**（`## [Unreleased]` 之前，紧跟 Keep a Changelog 说明） | **一句话判据 + 1 正 1 反例 + 判据命令** | **唯一在作者写 CHANGELOG 时必然被读到的地方**。写在 `docs/guides/` 里，作者不 open 就等于没写（本仓实测 `env.md` 阅读率 2.4%、`lessons.md` 0.6%，见 `~/.dsh/AGENTS.md`） |
| **`docs/guides/doc-freshness-guide.md` §3** | 在「历史快照 vs 活文档」表后加一行指针，指向 CHANGELOG 顶部那段 | 该节已把「CHANGELOG 已发布版本条目」定为历史快照；**判据的扫描面（只查最新段）就源自这里**，两处必须互相指认，否则将来会漂 |
| **`agate/scripts/README.md`** 的脚本索引行 | 若判据实现为新脚本 `check-changelog-quality.py`，登记其契约（0/1 + 扫描面 + 阈值） | CHECK 9/10 与 SG.6 的机械门禁面要求登记（`AGENTS.md`「新增脚本登记面」）；否则 `CHECK9-coverage` 会 WARNING |

### 6.3 写什么（建议正文，可直接用）

写在 `CHANGELOG.md` 顶部：

```markdown
> **写版本条目的判据**：一条内容若删掉后，读者仍能正确决定「这个版本会不会影响我、我要做什么」，
> 它就不该在这里。**读者的动作**在前，**作者的推导过程**不进 CHANGELOG。
>
> - ✅ `preset 授权了已移除的包子路径 ⇒ 挂载失败。需重跑 agate-setup.py 刷新产物。`
> - ❌ `第一版判断错了，二轮独立评审指出变异实验转红；31 passed。教训：复刻方式要写对。`
>   　（→ 过程归 commit message / `docs/reviews/`；调试技巧归 `agate/tests/README.md`）
>
> 机械判据：`python3 agate/scripts/check-changelog.py --quality`（pre-commit 亦会拦）。
```

三点说明：
1. **正例取自本次真实的重写结果**（`0.83.4`），不是虚构——作者能立刻对上"我要写成的样子"。
2. **反例直接引用被删掉的那段原文**，并**指明每类内容该去哪**（这是"该写成什么"的关键，光说"别写过程"没用）。
3. **判据命令写出来**：让规范可自证，作者能在提交前自己跑（对应 `AGENTS.md` 的「自证命令」取向）。

---

## 7. 若"三个候选都不合适"——我的最终建议（P2′ 的具体落点）

我认为 **P1 应排除、P3 单独不够**，所以给一个明确的第四方案；它不是新机制，而是**把 P2 与 P3 接成主从**：

### 7.1 实现：判据单源，两处挂载

1. **新脚本 `agate/scripts/check-changelog-quality.py`**（或作为 `check-changelog.py` 的 `--quality` 子模式）。
   - 契约：`0` = 通过；`1` = 检出过程痕迹（stderr 打印段名 + 命中类别 + 命中词）。
   - 扫描面：`[Unreleased]` + 最新已发布版本段。
   - 阈值：A1/A2/A4/A5/A6/A7 计数 ≥3 **且** 类别 ≥2（A3 只进提示文案，不计数，见 §5.5）。
   - **为什么新脚本而不是塞进 `check-changelog.py`**：后者语义是"`task_id` 存在性"，是 P1.6 的契约、有既有测试与文档引用；混入质量判据会让"是否存在"与"是否合格"两个契约纠缠，且 `--strict` 语义会歧义。**分文件 = 判据单源、契约清晰**。
2. **挂 `pre-commit-gate.py`（主闸）**：
   - **位置**：与 `2z`（`check-debt.py`）**并列，在 `for state_file in state_files:` 循环之外**——照抄 `2z` 的写法与它的注释理由。本仓已在此处记录过一次放错位置的事故（`:1176-1179`：`check-debt.py` 首版在循环内 ⇒ 对纯 `tech-debt.md` 提交完全失效，被评审实测证伪）。
   - **前置门**：仅当暂存清单含 `CHANGELOG.md` 时才跑（§3）。
   - **级别：`exit 1` 阻断**，不是 warning（§4）。
3. **挂 `check-protocol-consistency.py`（事后兜底）作为 CHECK 17**，**ERROR 级**（`rep.error`，不是 `rep.warn`——后者会被 `is_frozen_loc` 折叠进"冻结文件 N 条"聚合行，实测见 §0 额外发现）。
   - 价值：① CI 侧**上线即生效**，不受稳定版滞后影响（§2.3）；② 覆盖 `--no-verify` 且非 docs-only 之外的残余；③ 给非本机开发者统一判据源。

### 7.2 为什么这样接，而不是选一个

| 只做 | 缺口 |
|---|---|
| 只 P2 | 稳定版滞后 ⇒ 本机 hook 在下一次 release 前**不生效**（本仓已有同款登记）。 |
| 只 P3 | 纯 docs 提交（25/211）**不阻断**；且 `docs-check` 非 required ⇒ 实际拦不住。 |
| P2 + P3 | 两者缺口不重叠：P2 挡"本机 hook 已更新但未走 CI"的即时场合 + 纯 docs 提交；P3 挡"hook 版本滞后 / `--no-verify`"的后置场合。**代价：判据必须单源**，否则重演"两处对同一事实结论相反"（`CHANGELOG.md:1123` 的 `uncovered_gate_scripts()` 教训）。 |

### 7.3 上线前必做（本仓既有纪律，勿跳）

1. **存量扫描**（`AGENTS.md` 改脚本工作流第 0 条 / DEBT0025）：我已跑，**扫描面内命中 0**（§5.4），故**不需要豁免清单**——但正式上线前应用新脚本对全仓跑一次确认。
2. **误差面论证**（`AGENTS.md`「新增判据 = 给所有使用者加成本」）：**能举出真缺陷实例** —— §5.4 的 7 个真实提交里 5 个 FIRE，其中 `9f9c12f4`/`70f051ba`/`60ff46fd`/`c8acd5ff` 就是本次用户投诉的那批。
3. **破坏面差分在副本上跑**（`AGENTS.md` 0a）：`check-*.py` 若写数据须防污染；本判据**只读**，但差分仍应在副本上做，跑前跑后核验 `git status` 干净。
4. **加失败测试 → 转绿**：至少 4 条——(a) 原始 145 行 v0.83.4 段必须红；(b) `0.81.0` 段必须绿（反例锚）；(c) `Unreleased`→`[0.83.4]` 改名提交必须绿；(d) 阈值边界（tot=3/cats=1 绿、tot=3/cats=2 红）。
5. **登记**：`agate/scripts/README.md` 索引行（否则 `CHECK9-coverage` WARNING）+ `docs/guides/doc-freshness-guide.md` §3 指针 + `CHANGELOG.md` 顶部规范段。

---

## 8. 命令附录（本报告全部实测的可复现命令）

```bash
# ── 前提复核 ──
sed -n '1085,1090p' agate/scripts/pre-commit-gate.py          # 2m 无 exit（不阻断）
sed -n '767p'         agate/scripts/pre-commit-gate.py          # for state_file in state_files:
grep -n "NARRATIVE_DIRS" agate/scripts/check-protocol-consistency.py   # :83 含 CHANGELOG.md
gh api repos/:owner/:repo/branches/main/protection \
  --jq '.required_status_checks.contexts'                      # 6 项，无 docs-consistency

# ── hotfix 无 state.yaml（7/7）──
for c in 8690c9d2 c8acd5ff 70f051ba 60ff46fd 9f9c12f4 38616417 3df9c9e8; do
  git show --name-only --format="" $c | grep -q state.yaml \
    && echo "$c HAS" || echo "$c NO"; done

# ── 成本 ──
for i in 1 2; do /usr/bin/time -f "%e s" timeout 120 \
  python3 agate/scripts/check-protocol-consistency.py --root . >/dev/null; done   # 1.94 / 1.98
python3 -c "import subprocess,sys,time;t=time.time();subprocess.run([sys.executable,'agate/scripts/check-changelog.py','TAG9999'],capture_output=True);print(time.time()-t)"  # 0.033

# ── 实验 E-2：只暂存 CHANGELOG.md 时 gate 全程 rc=0、零输出 ──
T=$(mktemp -d) && cd "$T" && git init -q . && git config user.email t@t && git config user.name t
printf '# 变更日志\n\n## [Unreleased]\n\n## [0.1.0] - 2026-01-01\n\n- x\n' > CHANGELOG.md
git add -A && git commit -qm init --no-verify
printf '## [Unreleased]\n\n- 第一版判断错了，二轮独立评审指出变异实验转红；31 passed。\n' >> CHANGELOG.md
git add CHANGELOG.md
AGATE_ROOT=/home/kity/oclab/agateon/agate timeout 60 \
  python3 /home/kity/oclab/agateon/agate/scripts/pre-commit-gate.py; echo "rc=$?"   # rc=0，无输出

# ── docs-only vs mixed（211 个 CHANGELOG 提交）──
# 正则同 protocol-tests.yml:103 的 NON_DOCS；逐提交 git show --name-only 判定
# 结果：docs-only 25 / mixed 186

# ── 判据验证（词表 + 阈值）──
git show 3df9c9e8^:CHANGELOG.md > /tmp/old.md   # 原始 145 行 v0.83.4 段 ⇒ tot=21 cats=7 FIRE
# 0.81.0 段 ⇒ tot=2 cats=1（仅 SELF-GATE r1×2）不 FIRE
# 真实提交流水：8690c9d2 F / c8acd5ff T / 70f051ba T / 60ff46fd T / 9f9c12f4 T / 38616417 F / 3df9c9e8 F
```

---

## 9. 一页纸决策摘要

| 问题 | 裁决 |
|---|---|
| 挂哪儿 | **`pre-commit-gate.py` 循环外（主闸，ERROR）+ `check-protocol-consistency.py` CHECK 17（兜底，ERROR），判据单源为新脚本** |
| hotfix 能拦吗 | P1 不能（无 `.state.yaml` 不进循环）；P2 能；P3 只能拦 mixed 的 186/211，纯 docs 的 25 个漏 |
| 成本 | 5 ms（且应以「暂存了 CHANGELOG.md」为前置门）；**"增加日常成本"是伪成本** |
| warning 有意义吗 | **没有。在本仓 warning ≈ 方案 A**——386 条无人消费、同款模式复犯 6 次、`2m` 自身即被无视的 warning、CI 侧 `--strict-errors-only` 连 rc 都不影响 |
| 判据 | A1/A2/A4/A5/A6/A7 计数 ≥3 **且** 类别 ≥2；**A3 只进提示不计数**（消除"正当引用独立评审"的误伤）；扫描面 = `[Unreleased]` + 最新已发布段（使存量影响 = 0，无需豁免清单） |
| 规范还写吗 | **写**，落 `CHANGELOG.md` 顶部（作者必然读到处）：一句话判据 + 1 正 1 反例（取真实原文）+ 自证命令；`doc-freshness-guide.md` §3 留指针 |
| 已知边界 | 会漏 `8690c9d2` 一类（用「第一版判断」而非「我」）。**接受漏口，不加词**——放宽会误伤 7 处正当的"原先"变更说明 |
