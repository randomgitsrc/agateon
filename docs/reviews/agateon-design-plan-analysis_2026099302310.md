# 《Agateon Protocol — Complete Design Plan v0.3》分析：对照仓库现状

> **日期**：2026-09-30
> **仓库状态**：`randomgitsrc/agateon` @ `c089f9e`（2026-09-30 20:11）
> **读过的材料**：
> - 价值评估：`docs/research/agateon-value-assessment-20260929.md`
> - 声称-证据绑定 v3：`docs/design-notes/design-claim-evidence-binding.md`
> - roadmap 中 RM-AG0071~0096
> - P6、judge、retreat 相关脚本
>
> **证据强度标注**：`[实测]` 表示经命令或仓库内容核实，`[推断]` 表示分析推理。

---

## 一、现状（与上次记录相比变化很大）

- **规模**：1878 commits，72 tags。最新发版是 v0.76.0（09-24），此后一周没有发版，全部时间用于债务和机制复核。`[实测]`
- **重心已经移动**：09-29 的价值评估 v3 得出结论，价值不在 P0–P8 阶段脚手架，因为**没有测出**它抓到过错误。价值在另外两处：
  - **独立评审**抓判断类错误，本会话抓到 10 处；
  - **机械判据**抓结构类错误，至少 3 处。
  - TAG0018 是反证：同上下文评审的净收益约等于 0。`[实测，评估自述 n 小]`
- **正在进行的条目**：
  - RM-AG0093：收缩阶段脚手架
  - RM-AG0094：声称须附命令。今天落地了 A8；半 1 经三次尝试失败，保持 open
  - RM-AG0095：度量常态化
  - RM-AG0096：`done` 语义污染

因此，这份设计稿面对的不是一张白纸，而是一个**刚用实证把自己的阶段流程判为"未测出价值"**的项目。

---

## 二、与现状的关系：方向高度重合，实现路线冲突

### 2.1 重合的部分

设计稿的主张与仓库的实证结论几乎可以逐条对应：

| 设计稿主张 | Agateon 中已有的对应物 |
|---|---|
| P0–P8 降为 profile，不作为协议本体 | 评估 §2.1 与 RM-AG0093，从数据得出同一结论 |
| I9：自述不享有特权 | `judge.md:10`「不信任何实现者自述」；P6.5 fresh-context judge |
| Obligation 必须可验证 | P1 的 BDD 条目；`check-judge-verdict.py` 要求 `criteria_total == P1 BDD 数`，且零挑验 |
| Evidence 需绑定并有 provenance | `P6-evidence/`；`check-p6-provenance.py`（审计 7 管证据复用）；`agate-evidence-consistency.py` |
| 声称必须有证据 | 今天落地的 A8「无法给出命令的声称应删除」，以及 trailer 完整性 CI 测试 |
| 事件日志 | `gate-events.jsonl` |
| 依赖快照 | `agate-capture-env-baseline.py`，按 commit 加命令集缓存基线 |

设计稿从理论出发，走到了仓库从数据出发已经走到的地方。两条独立路径的收敛说明，**「完成声称的可信度」确实是 Agateon 的真问题**，而不是修辞。这是这份设计稿最有价值的一点。

### 2.2 冲突的部分

设计稿 §20 的参考架构包含 Runtime、Evidence Store、Verifier Pool、Claim Registry、Monitor/Invalidation Engine，§14 还定义了 HTTP API。这与 Agateon 的第一过滤器**零基础设施**直接冲突。

- 设计稿 G8 声称"不需要集中式评估器"，但 §20 画出的正是一个服务。
- 最尖锐的一点：`Claimed → Invalidated` 的**持续监控**，需要一个常驻进程去感知"外部状态在声称之后发生了变化"。Agateon 没有 daemon，这部分在现有形态下没有执行者。`[推断]`

---

## 三、最严重的问题：这份文档违反了它自己的 I9

设计稿的核心论点是"生产者不能把自己的断言提升为保证回执"。而它自身的情况如下：

- **评审不独立**：§30「Independent Review Record」的三轮评审，全部出自**同一作者、同一上下文**，结论为 `Review status: PASS`。
- **检查项无证据**：附录 B 的 15 个 `[x]`，没有一条附带命令或证据。
- **已知缺陷的重现**：这正是此前记录过的 B1' 缺陷（自己给自己贴 PASS 标签），也是评估 D4 所说的"留痕可伪造"。按 TAG0018，这类评审的净收益约等于 0。
- **按现行标准应删除**：按今天刚落地的 A8，这份文档的"PASS"应当删除，而不是保留。
- **旁证**：章节编号有明显漂移。§13 下面出现 12.1，§16 下面是 15.x，§21 出现了两次。这说明它**没有经过任何机械检查**。`[实测，可直接数出]`

因此，这份文档的正确定位是**假设**，不是"review-passed baseline"。它最后一节自己也写明"这是需要去证伪的假设"，这句话是对的，应以这句为准。

---

## 四、真正的风险：11 类对象就是 11 处可以空着写的地方

`design-claim-evidence-binding.md` 付出两次 REJECT 才得到的教训是：**把判断类检查机械化，必然退化为仪式**。v2 那个节标题，最便宜的满足方式只需要 2 行、0 条目。

设计稿要引入 11 种结构化对象：Task、Intent、Obligation、Authority、Action、Observation、Evidence、Verification、AssuranceReceipt、Claim、InvalidationEvent。

问题在于，它最需要保证的那些义务本身就是判断类的，例如：

- "diff is reviewable"
- "uncertainty is disclosed"
- "every material claim has source evidence"

这类义务的 Verification 对象最终只能由独立评审来填写，而 schema 能校验的只是"字段在不在"。

这正是评估 §3.4 所说的「形式代替实质」。`ceremony: thin` 声明了却没有任何消费方（D3），就是现成的前车之鉴。对象越多，这种表面合规的面就越大。`[推断，有两次实测失败作支撑]`

---

## 五、值得吸收的部分：4 个有实证锚点的概念

筛选标准是"仓库里已有实测问题能证明它有用"，而不是"理论上漂亮"。

### 5.1 I8「缺失证据不是正面证据」→ RM-AG0077

- **已有实测**：
  - 23 个 `check-*.py` 中有 **13 个**含"空条件 → exit 0"的真空通过分支（AST 精确计数）。
  - `_gate_p2_dispatch_plan` 在解析失败时静默放行（RM-AG0090）。
- **落点**：这是设计稿中最便宜、证据最硬的一条，可以直接做成机械判据。检查器在输入为空时默认 fail-closed，任何豁免都必须显式声明。

### 5.2 Claim 的有效期语义 → 修 `done`（RM-AG0096）

- 设计稿 I10 要求每个声称定义"什么会让它失效"。评估 §6-4 说 `done` = 行为可观测 + 有回归锁。两者说的是同一件事。
- **落点**：
  - `done` 本身就是一个 claim，它的 `invalidation_trigger` 就是那把回归锁。
  - 回归测试变红，claim 即失效；历史记录不改写（I5）。
- 这为 RM-AG0096 提供了精确语义，且不需要新的基础设施：失效在读取时由 CI 求值即可。

### 5.3 局部失效 → RM-AG0072（评审面板重放）

这是设计稿对 Agateon 最有价值的一条，因为成本数据可以复核。

- **现状**：任何一次修订，都会让该产出的全部 approved 立即失效，于是整个面板重派。TPV0099 的 P2 为 4 个角色乘 2 轮，共 8 份派发上下文，合计 305 kB。
- **规模**：`-revN` 整份重发占派发上下文的 **42%**，经 `agate-dispatch-cost.py` 双路径验证。
- **落点**：让每个评审的 approved 绑定到它实际审查的范围（章节或文件）。修订时，只有范围被触及的那部分评审失效。
- **相关机制**：`agate-retreat-to.py` 目前按阶段线性回退，并归档所有被跨过的阶段。这正是设计稿所说的 `Change(D) → Reset(T)` 模式。

### 5.4 确认回执 ≠ 实际效果（ack ≠ effect）→ 平台适配层

- **实例**：v0.76.0 修复的「DSH preset 长期假成功」就是这个模式。DSH ≥0.1.7 已不再读取目录式 preset，但接入流程一直报告成功。
- **外部对照**：ADF-EA 论文在设备领域讨论的是同一件事。
- **落点**：平台接入必须验证实际效果，不能只看命令的退出码。

### 5.5 附带：Authority → RM-AG0081

- **实例**：评审 subagent 的一次误操作，丢弃了被评审的改动集，说明角色写权限是真缺口。
- **落点**：这一条很可能应由宿主 harness 的权限系统解决，不适合在协议内自建 authority 对象。

---

## 六、应拒绝或推迟的部分

- **Runtime、服务、HTTP API、Claim Registry**：违反零基础设施原则。Agateon 已有的等价物是：
  - git 提交 = 声称
  - 文件 = 证据
  - CI / hook = 验证
  - 读取时求值 = 失效检测
- **11 对象 JSON Schema 全套**：在有度量之前没有依据，而且会重演 v2 的仪式问题。
- **三领域 profile**：Agateon 目前在非软件领域的证据为 0。设计稿自己要求"三个领域都跑通才能称为领域中立"，那么就不应提前按领域中立来设计核心。
- **形式语义**：需要先有数据，说明哪些不变量确实在被违反。

---

## 七、建议

**不要把它当作 v0.3 协议去实现。** 更合适的用法是把它当作**一套词汇表**，为已经立项的 RM-AG0077、RM-AG0072、RM-AG0096 提供精确语义。它最有价值的是最后那句话：这是一个待证伪的假设。

**证伪的前提是 RM-AG0095 的度量先落地。** 如果复犯率、rev 率、捕捉数都还没有，设计稿 §25 列出的 false completion rate 等指标一个也测不出来。按评估 §5.3 的逻辑，在度量存在之前，这份设计稿与"收缩脚手架不降低捕捉率"那条预测处于同一状态：**是方向，不是结论**。

---

## 附：引用文献核查

| 文献 | 核查结果 |
|---|---|
| ADF-EA，arXiv:2609.30691 | ✅ 确认存在，2026-09-25 发表。内容为设备能力契约，与设计稿描述相符 |
| Koch, *From Agent Output to Authorized Transition*，arXiv:2609.28216 | ⚠️ 检索得到该标题，但未能抓取正文 |
| arXiv:2608.23653 | ❌ 未核实（页面抓取失败） |
| arXiv:2609.11381 | ❌ 未核实 |

**Sources**：
- [ADF-EA: A Unified Execution Assurance System for Agent Device Foundation](https://arxiv.org/abs/2609.30691)
- [From Agent Output to Authorized Transition](https://arxiv.org/pdf/2609.28216)
