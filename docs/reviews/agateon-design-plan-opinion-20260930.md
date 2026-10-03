# 对《Agateon Protocol — Complete Design Plan v0.3》及其分析文档的意见

> **日期**：2026-09-30
> **审阅对象**：
> - 设计稿：`docs/reviews/agateon_protocol_design_plan_2026099302300.md`（1462 行）
> - 分析稿：`docs/reviews/agateon-design-plan-analysis_2026099302310.md`（164 行）
> **方法**：逐份读完 → 对设计稿的核心主张，回到 agateon 现有脚本/角色文件核实"是否已实现、实现到什么强度"
> **范围声明**：本文不更正两份文档的数字（commits/tags/check 脚本计数等）。用户已明确指示不在此耗费精力。本文只审**核心设计**。

---

## 摘要

1. **设计稿的"新东西"里，大部分 agateon 已经实现了，而且更严**——设计稿把 Verification 当 schema 对象，agateon 把它当"fresh-context 派发 + 8 条 exit 1 的机械校验链"。**引入对象是降级，不是升级。**
2. **设计稿有三条它自己没意识到说对了的贡献**：`done` 需要失效条件（I10）、失效应当是局部的（§10.2/§12）、ack ≠ effect（§6）。
3. **其中只有前两条该进 roadmap，且都落在已有条目上**（RM-AG0096 / RM-AG0072），不新开条目。
4. **设计稿 §20-22 的形式化 `Assured(T)` 是错的**——它把不可判定的义务（如 `diff is reviewable`）藏进一个看起来可判定的合取式里，比"仪式化"更糟。
5. **分析稿的定性（"假设而非 baseline"）对，但它的处方（"当词汇表用"）不可验收**；本文给出可验收的替代。

---

## 一、设计稿声张的核心，agateon 已有且更强

设计稿 §2 声张七个原语，§8.2 声张"producer 与 verifier 的分离度随风险增强"，I9 声张"agent 自述不享有特权"。

**这些主张在 agateon 里不是空缺，是一个已经落地并被机械门禁保护的机制**——P6.5 独立裁判（`agate/assets/review-roles/judge.md` + `agate/scripts/check-judge-verdict.py`）。

对照如下：

| 设计稿主张 | 设计稿给的判据 | agateon 的实际机制 |
|---|---|---|
| I9 自述不享有特权 | 无（只有不变量陈述） | `judge.md` 认知模式 2：「只信证据与 git log，不信叙述」 |
| §8.2 独立性随风险增强 | **无判据**（"Domain profiles define it"） | **黑名单机械校验**（BDD-4）：`P6-acceptance.md`、`P4-implementation.md`、`P4-review.md`、`P5-test-results/` 禁入 judge 的 dispatch-context |
| 防锚定 | 未提 | **白名单**——不只禁自述，还禁**上游结论泄漏**（"行首 `- PASS` / `- FAIL` 预判"亦在禁列）；`gate-events.jsonl` 可交叉核对 |
| 零挑验 | 未提 | `criteria_total == P1 的 BDD 标题数`；`status==passed ⇒ criteria_total == criteria_passed`（BDD-5）；`partial: true ⇒ status ∈ {needs-revision, rejected}`（BDD-8） |
| 证据须绑定 | D1「evidence scope binding」（对象字段） | `_evidence_md5_dedup` + 引用须在 `verdict_evidence` 清单内且**指向真实存在、非空的文件**（BDD-6） |
| 证据不可仅凭自述 | §7.2（叙述） | P6-acceptance.md **不读、不引用**（信息隔离） |

**结论**：设计稿 §8.2 引入 `Verification` 对象的价值 = 0。

**更关键的判断**：agateon 的 verification 不是"对象"，是**一次 fresh-context 派发 + 8 条链的机械校验**。设计稿要把它变成 schema 里的一组字段——而字段只能校验"在不在"，不能校验"这条判断对不对"。

> **⇒ 引入 `Verification` 对象是对现有机制的降级。**

这也解释了分析稿 §四的担心（11 类对象 = 11 处可以空着写的地方）为何成立，但分析稿的理由（"schema 只能校验字段在不在"）还不够锋利。**更锋利的说法是：agateon 已经用「机械链 + 一次判断」的组合解决了它，而 schema 化会把"那一次判断"从机制里挤出去，只留下机械壳。**

---

## 二、设计稿真正说对了的三条（它自己没意识到）

### 2.1 `done` 需要失效条件（I10）→ RM-AG0096

设计稿 I10：*"Every claim profile must define what makes its claim stale, invalid, or superseded."*

**agateon 现在的 `done` 恰恰没有。** 实读 `agate/scripts/check-gate.py::_check_roadmap_done`：

```python
if related_task == task_id and status != "done":
    return rm_id, status
```

它检查的是 **roadmap 表格「状态」列里的那个字符串有没有写 `done`**——而那是人在 P8 **手写的一个词**。

> **⇒ `done` 不是 claim，是 claim 的字符串表示，且无失效条件。**

这正是 RM-AG0096（"`done` 语义污染"）所指。**设计稿的 I10 给 RM-AG0096 提供了它现在缺的精确语义**：

- `done` 本身就是一个 claim；
- 它的 `invalidation_trigger` = **那条回归锁**；
- 回归测试变红 ⇒ claim 失效；
- **失效在读取时求值**——CI 每次跑就是在重新求值，**不需要 daemon**。

**这是本文认为最该先做的一条**，理由见 §五。

### 2.2 失效应当是局部的（§10.2 / §12）→ RM-AG0072

设计稿 §10.2「Local re-opening」+ §12「dependency closure」：只有受影响的义务重开，不是整个任务重来。

**这条对准 agateon 现存最大成本项，且原料已经齐了，只缺一个闭包算法**：

| 设计稿要的东西 | agateon 已有的原料 |
|---|---|
| dependency snapshot | `agate-capture-env-baseline.py`（按 commit 存命令集基线） |
| 事件日志 | `gate-events.jsonl`（含 `prev_hash`，**已是哈希链**） |
| 失效/回退 | `agate-retreat-to.py`——但按 `phase_num()` **线性**回退，跨过的阶段全部归档 |

> **⇒ 设计稿 §12 不是"要新建基础设施"，是"给已有原料补一个依赖闭包算法"。**

这个定位比分析稿 §5.3 说的"抽象概念"实在得多，也便宜得多——**不需要 Runtime，不需要 Claim Registry。**

**代价数据（分析稿 §5.3 引，未在本文复核）**：`-revN` 整份重发占派发上下文 42%；TPV0099 的 P2 = 4 角色 × 2 轮 = 8 份派发 / 305 kB。**若该量级成立，这是全仓最贵的单项。**

### 2.3 ack ≠ effect（§6）

设计稿 §6：*"A command acknowledgement must never be treated as proof of intended effect."*

**agateon 已经用血换过这一课**：v0.76.0 修复的「DSH preset 长期假成功」——DSH ≥0.1.7 起不再读取目录式 preset（上游原文 "Nothing reads that directory any more."），而 `agate-setup.py` 仍往那里写、`--list` 仍检查它 → 工具一路报 ✅ 而 DSH 里根本没有该模式。**实测代价**：最后一个用上 preset 的会话停在 2026-09-20 22:25，其后每个会话都落 `standard`。

**设计稿独立复述了同一条**，这是两条独立路径的收敛，说明这条是真问题。

---

## 三、设计稿 §20-22 的形式化是错的

设计稿给出：

```text
Assured(T) ⇔ O(T) ⊆ Sat(O) ∧ Auth(T) ∧ Fresh(E) ∧ Dep(T) ∧ ¬Inv(T)
```

**形式化本身没错，错在它把一个可判定的合取式，当成了任务完成的判据。**

问题出在 `Sat(O)` 的内部。设计稿自己的 §15.1 例子就写了：

```text
O5: diff is reviewable
```

**`diff is reviewable` 不可判定。**

形式化把它写成 `O5 ∈ Sat(O)`，看起来严谨，实际只是**把不可判定的东西藏进了一个看起来可判定的符号里**。

> **这比"仪式化"更糟**：仪式至少还能被识破（`design-claim-evidence-binding.md` v2 的节标题，最便宜的满足方式只要 2 行、0 条目）；**形式化会让人以为问题已经解决了。**

**而 agateon 在这点上是对的**：它不形式化，它把 `diff is reviewable` 交给 fresh-context judge 去**判**，并承认那是判断。
⇒ **`Assured(T)` 那个合取式，agateon 的正确实现就是 `check-judge-verdict.py` 的 8 条链——其中 7 条机械、1 条是判断，且用信息隔离保证那条判断的质量。**

**这是本文与设计稿最根本的分歧**：设计稿认为"把断言写进 schema 就能约束它"；agateon 的实测结论相反——**判断类的东西只能由独立判断来约束，机械壳约束不了它，只会掩盖它。**

---

## 四、对分析稿的判断

### 4.1 它做对的一件事

**定性准确**：设计稿 §30 的三轮评审全部出自**同一作者、同一上下文**，结论 `PASS`；附录 B 的 15 个 `[x]` 无一附带命令。

**这是用设计稿自己的核心不变量否证了设计稿自己的验收状态**——I9 说"生产者不能把自己的断言提升为回执"，而 §30 正是这么做的。**分析稿看穿了这一点，且这是全文最有价值的一句。**

**附带的强证据**：设计稿章节编号漂移（§21 出现两次、§13 下面是 12.1、§16 下面是 15.x、§14 后接 §17.1、§25 下面是 24.x）。**这直接证明它没经过任何机械检查**——分析稿的这个推断是对的。

### 4.2 它做错的两件事

**（1）处方不可验收。**

分析稿结论：「把它当作一套词汇表，为 RM-AG0077、RM-AG0072、RM-AG0096 提供精确语义」。

**"当词汇表用"不是可验收的定位**——没有判据能回答"词汇表用到位了没有"。这等于把一个未决问题换了个说法留着。

**（2）把 §10.2/§12 排在第 3 位是排错了。**

分析稿把它列在 I8、`done` 之后，理由只是"成本数据可以复核"。**那条理由恰恰应该让它排第一**——它是唯一一条诊断直接命中现存最大成本项（42% 派发）的。

**（3）一处推理过头。**

分析稿说"agateon 在非软件领域证据为 0"，据此推出"不应提前按领域中立设计核心"。

> **证据为 0 只能得出"现在别做"，不能得出"核心设计不该 domain-neutral"。**

更准确的读法是：agateon 的 P0-P8 是**软件开发形状**的，设计稿的 obligation graph 想解决的正是"不限软件"——**那 agateon 的 roadmap 里，有哪一条是非软件域的？** 如果没有，两者之间不是**冲突**，是 **agateon 还没走到那个问题**。⇒ 这是**推迟**理由，不是**拒绝**理由。

### 4.3 它与本文的分歧

| 议题 | 分析稿 | 本文 |
|---|---|---|
| 设计稿定位 | 假设 / 待证伪 | **同意**，且设计稿最后一句自述"这是需要去证伪的假设"应以该句为准 |
| 用法 | 当词汇表 | **当两个已有条目（RM-AG0096 / RM-AG0072）的决策记录，不进新条目** |
| 该吸收哪条优先 | I8 → `done` → 局部失效 | **`done` 失效条件 → 局部失效闭包**（I8 见下） |
| 拒绝理由 | 违反零基础设施原则 | **那些对象解决的问题 agateon 已用更强的机制解决；引入对象是降级** |
| domain-neutral | 拒绝 | **推迟** |

---

## 五、建议

### 5.1 不采纳的部分及理由

**不采纳**：§20 参考架构、§14 HTTP API、§13 的 11 对象 JSON Schema 全套、§22 形式化核心、§16 三领域 profile 提前设计。

**理由不是"违反零基础设施原则"**（这是分析稿的理由，太软，属于偏好陈述），**而是**：

> **这些对象要解决的问题，agateon 已经用「fresh-context 派发 + 机械校验链」解决了，且解决得更严**——设计稿的 `Verification` 是 schema 字段，agateon 的是 8 条 exit 1 的链。**引入对象是降级。**

**并建议追加一条机械理由（可判据化）**：

> **任何新对象的引入，必须先给出一个「当前无对象可表达」的实测失败案例。** 给不出 ⇒ 拒绝。

这样"该不该采纳"从偏好之争变成可验证的问题。

### 5.2 采纳的部分：落点与顺序

**建议先做 `done` 的失效条件（RM-AG0096），再做局部失效闭包（RM-AG0072）。**

**为什么先做 `done`**：

1. **有现成的机械判据**——回归锁红了 ⇒ claim 失效，不需要新造判据；
2. **不碰 `agate-retreat-to.py`**——那个线性回退上挂着 TAG0027 的 exit2-resolution 机制（`_check_exit2_resolution`），动它要先把边界摸清；
3. **RM-AG0096 已立项**，落点明确。

**为什么局部失效闭包更值钱但更险**：`agate-retreat-to.py` 的回退语义有 `Phase` 数字解析、retry 上限、逐步归档 + 独立 commit 等多个耦合面（实读 `phase_num()` / `cur_num` / `tgt_num` / `MAX` 逻辑）。**改它之前必须先确认 exit2-resolution 的触发条件不受影响。**

### 5.3 建议的验收锚（草案）

**RM-AG0096（`done` 失效条件）**：

- `done` 条目必须声明其回归锁（可机械校验：存在指向真实测试的引用）；
- 回归锁变红 ⇒ 该 claim 在**读取时**被求值为失效；
- **历史记录不改写**（I5）——失效是新事件，不是重写旧状态。

**RM-AG0072（局部失效）**：

- 修订后**只重派受影响范围**的评审（当前是整份 `-revN` 重发）；
- 可测判据：改动一个章节 ⇒ 失效的评审数 < 总评审数；
- **必须保留现有线性回退作为 fallback**（关闭新路径时应能退回）。

---

## 六、一句话结论

> **设计稿的核心贡献不是它声张的对象化，而是三件它没意识到自己说对了的事**：`done` 需要失效条件、失效应当是局部的、ack ≠ effect。
> **它声张的核心（11 对象 / Runtime / HTTP API / Claim Registry）应整条拒绝**，因为那些问题 agateon 已用更强的机制解决了。
> **分析稿看穿了设计稿的自我认证是伪造的，这一点做得对**；但它的处方（"当词汇表用"）不可验收，且它排错了优先级——把唯一对准 42% 实测成本的那条放在了第三位。

---

## 附：本文核实过的事实

| 事实 | 核实方式 |
|---|---|
| `_check_roadmap_done` 仅比对字符串 `done` | 实读 `agate/scripts/check-gate.py:1360-1399` |
| judge 的黑/白名单与 8 条校验链 | 实读 `agate/assets/review-roles/judge.md` + `check-judge-verdict.py` 头注释 |
| `agate-retreat-to.py` 按 phase 线性回退 | 实读 `phase_num()` / `cur_num` / `tgt_num` / 归档逐步执行逻辑 |
| `gate-events.jsonl` 含 `prev_hash` | 实读 `agate-workspace/tasks/TAG0037-install-package-model/gate-events.jsonl` |
| `agate-capture-env-baseline.py` 存在 | `ls agate/scripts/` |
| DSH preset 假成功及其代价 | 实读 `CHANGELOG.md` v0.76.0 条目 |
| 设计稿章节编号漂移 | 提取全部标题逐条比对 |
| `O5: diff is reviewable` 在设计稿中 | 实读设计稿 §15.1 |

**未核实**（本文未复核，引用时请注明来源为分析稿）：分析稿 §5.3 的 42% / 305 kB 派发成本数据；两份文档的 commits / tags / check 脚本计数。
