# Agateon 效率调研：实测数据与前沿对照（2026-11-12）

> **状态：调研记录，没有落地任何改动。** 本文只记录已核实的事实与仍未解的问题，
> 不包含已采纳的方案。写作目的是让下一个人（或下一个会话）不必重跑一遍测量。
>
> 触发：用户反馈「整体太慢，时间成本高，用户不愿用」，要求在不牺牲质量的前提下提速。

## 一、实测数据（DSH 会话日志，peekview 13 个真实 subagent + 两仓 130 个任务账本）

### 1.1 时间构成

| 指标 | 实测值 |
|---|---|
| 模型思考占比 | **92–98%** |
| 工具执行占比 | **5.5%** |
| 单次派发等待（中位） | **19.9 分钟**（最长 70.8） |
| 每步耗时 | 13.9 秒（会话 45–292 步） |
| 每消息工具调用数 | 中位 **1.23**（几乎不并行） |

**结论**：时间几乎全部是 LLM 推理，不是工具延迟。任何「优化 bash 用法」的方案上限只有 5.5%。

### 1.2 上下文与耗时

| 指标 | 实测 |
|---|---|
| `cacheReadTokens` 起点 | 16256（固定前言约 27k totalTokens） |
| 单会话累计 cacheRead 中位 | **4.8M tokens**（极值 102M） |
| cacheRead : output | **65 : 1**（全体 78.8:1） |
| 每步耗时 vs cacheRead | **r = 0.085（无相关）** |
| 每步耗时 vs 步数 | r = 0.64 |

**结论**：上下文线性膨胀但**不变慢**。成本是 O(S²)（前言被重读 S 次），延迟是 O(S)。
「上下文膨胀导致变慢」不成立——这是本次调研中我最初提出又被数据推翻的假设之一。

### 1.3 成本与任务规模脱钩

| 生产代码规模 | 任务数 | 平均派发次数 |
|---|---|---|
| ≤100 行 | 5 | **9.8** |
| 101–1000 行 | 24 | 10.7 |
| 1001–10000 行 | 17 | 18.1 |

- 派发数与改动规模：r = 0.50（改动行数）/ **0.39（log 生产行）**
- **改动差 100 倍，派发只差 2 倍** ⇒ 成本正比于仪式，不随工作量缩小

### 1.4 gate 与 retries 的真实分工（重要修正）

| 数字 | 含义 |
|---|---|
| gate_run **248 次** | ≈ commit 次数（`pre-commit-gate.py` 在 commit 时写入） |
| exit 1 只有 **8 次（3.2%）** | 大部分时候不红 |
| **retries 115 次**（P1 33 / P2 30 / P4 29 = 80%） | **真正的打回在这里** |

**「gate 只有 3.2% 红」不等于「gate 无判别力」。** 机制是：review 未过 → retry 重来 →
通过才 commit → 才过 gate（`pre-commit-gate.py:964` 证明 gate_run 在 commit 时写）。
**球在中场就被断了，所以守门员很少扑救。** 这是本次调研中「gate 空转」假设被推翻的证据。

### 1.5 四条已建成但零消费的降级通道

| 通道 | 定义位置 | 消费情况 |
|---|---|---|
`ceremony: thin` | `WORKFLOW.md:241` / `P1-requirements.md:124` | 122 个 P1 只声明 2 次，`C8 映射表无 thin 行` ⇒ **减不了任何东西** |
`commit_types` | `phases.yaml:186`（`docs-only: [P0,P1,P2,P7,P8]`） | `grep gate_layer\|commit_types agate/scripts/*.py` = **0** |
router | `dispatch-routing.yaml` | 机制完整，两仓 **0 条 `dispatch_route` 事件** |
`phases:` 裁剪 | P1 frontmatter | 靠 agent 读卡自觉（实测遵守 ~94%），脚本不强制 |

### 1.6 系统对自己的主成本不可见

`agate-summary.py:390` 自陈「token / 步数不可得（harness 不报）——本工具不猜、不编造」。
但数据就在 `~/.dsh/sessions`（DSH 适配器已能解压同一批文件，只是没抽 `usage` 字段）。

## 二、前沿对照（外部材料）

### 2.1 支持 Agateon 形态的

- **Anthropic《Building effective agents》**：可分解任务优先用 workflow + 程序化 gate。
  Agateon 是 workflow，不是 swarm，分类上正确。
- **Cognition《Multi-Agents: What's Actually Working》**：多 agent 只在
  「writes 单线程 + 其他 agent 贡献 intelligence」时有效；**clean-context reviewer 因
  attention 机制更聪明**（Context Rot）。Agateon 的 P2/P4 评审、P6.5 judge 正是此模式。
- **arXiv:2512.08296（DeepMind & MIT）**：独立多 agent 17.2x **trace 级协调开销**（非错误率），
  集中式 + 验证瓶颈降到 4.4x —— **论文结论是 agateon 这种集中式形态胜出**。
  ⚠️ 易被误读为「多 agent 放大错误 17.2 倍」，本文记录该澄清。
- **arXiv:2603.16244《More Rounds, More Noise》**：跨上下文评审（CCR）**最优轮数 = 1**。
  多轮 vs 单轮：F1 0.376 → 0.303/0.263；每多 1 个真错误带来 4–5 个假阳性。
  机制：**假阳性压力**（第二轮的容易错误已抓完，模型开始编造）+ **评审目标漂移**
  （给了作者解释后，评审者从「审工件」滑向「审对话」）。
  **建议：把额外算力花在「并行独立评审」（3 份多数投票 F1=0.393），不是「串行迭代」。**

### 2.2 与 Agateon 现状冲突的

- `P4-implementation.md:136` 写「review 不通过 → 改 → **再 review** → … → approved」
  **正是 2.1 最后一条证明会降低 F1 的串行迭代模式。**
- TPV0103 的 P1 实测走了 4 轮才收敛，形态与论文描述的失效一致（虽未做严格对照）。

### 2.3 Agateon 缺失的技术（grep 全仓 0 命中）

`compaction` / `context rot` / `structured note-taking` / `just-in-time retrieval` /
并行 tool calling 硬约束 / skill library 编译 / semantic caching / 按难度路由。

### 2.4 Agateon 已做对、与前沿一致的

- **subagent 只返回路径 + 摘要**（`dispatch-protocol.md` 铁律 3）——即 Anthropic 推荐的
  「subagent 输出落 filesystem 避免传话游戏」
- **judge 信息隔离白名单**（`check-judge-verdict.py` 有黑名单扫描）——比 Cognition
  描述的「clean context」更硬：不靠自觉，靠脚本
- **规格驱动**（BDD + 机械 gate）——严于 spec-kit

### 2.5 唯一独特资产（外部材料中找不到对应物）

**哈希链账本 + CI 回放**（`gate-events.jsonl` + `check-events.py` + `agate-ci-verify.py`）：
做的是「**判定过程可复算**」——不只记结果，记判定时的输入与结论，append-only +
`prev_hash` 链 + 逐提交回放。Anthropic 的 tracing 是运维可观测性，不是可审计判定账本。

⇒ **护城河在 Verification Plane，不在 Control Plane**（后者正在被商品化）。

## 三、仍未解的问题

1. **「给生产方注入记忆能否减少评审轮数」无证据。**
   做过一次实验设计但**载体失效**（TPV0103 代码已合并，`a166409a`），无产出。
   需要：一个真实的同类待办任务 + n≥3 对照组。
2. **并行工具调用能提速多少未实测。** 基线已知（1.23 calls/msg），但改了会怎样不知道。
3. **1.3 节的「成本脱钩」是否可改善**——`commit_types` 接线的真实收益未验证。
4. **第二章论文的适用性**：单模型（Opus 4.6）、注入错误、韩语；agateon 是「新评审者看新工件」，
   与论文「同一评审者多轮」形式不同。机制可能仍适用，未验证。

## 四、本次调研中我提出但被数据推翻的假设（留作教训）

| 假设 | 推翻证据 |
|---|---|
| 主 Agent 自己干活占大头 | 等待占 52% |
| bash 往返 10 秒 × 127 次 ≈ 21 分钟 | bash 中位 0.37 秒，合计 63 秒 |
| subagent 用 bash 读文件导致慢 | bash 只占时间 5.5% |
| 改用 read 工具能减步数 | read 次数 vs 步数 r=0.27 |
| 上下文膨胀导致每步变慢 | r=0.085，35 万上下文反而每步 7.1s |
| gate 只有 3.2% 红 ⇒ gate 无判别力 | retries 115 次，打回发生在 gate 之前 |
| 「多 agent 太重」 | 贵的是步数×上下文，不是 agent 数；17.2x 是协调开销非错误率 |

**共同错误模式：先给结论再找证据。** 后续接手者请先测量再判断。
