# Agateon 效率：实测机制数据（2026-11-12）

> **本文只记录可复核的测量结果，不含决策与建议。**
> 决策走 `docs/design-notes/` 与 `agate-workspace/roadmap/`。
> 证据强度标注沿用本目录图例：`[实测]` = 可复核。

## 调查方式与环境

- 数据源：DSH 会话日志 `~/.dsh/sessions/**/session*.jsonl.zstd`（逐帧解压读 `usage` 字段）
  + 两仓 `agate-workspace/tasks/*/gate-events.jsonl` 与 `.state.yaml`
- 样本：peekview 13 个真实 subagent 会话（短、中、长任务混合）；两仓 130 个任务的
  `retries` 与 248 条 `gate_run` 事件
- 环境：DSH（deepseek-harness），本机 2026-11-11/12；被观测项目 peekview（Vue + Vitest）
- **口径限制**：单个模型、单个项目、单机。样本量小（子会话 13 个），凡标 `[推断]` 者未经
  独立复现，不得单独引用。

## 1. 时间构成：模型推理占绝对多数 `[实测]`

| 指标 | 值 |
|---|---|
| `step/start` → `assistant/message` 累计占比 | **92–98%**（13 个会话一致） |
| `tool/call` → `tool/result` 累计占比 | **5.5%**（935s / 17038s） |
| 单次 bash 执行耗时中位 | 0.37 秒 |
| 每步（每 assistant message）耗时 | 13.9 秒（均值）；最长单步 120 秒 |

**推论边界**：任何以「优化工具调用开销」为目标的改动，时间收益上限是这 5.5%。

## 2. 上下文增长与每步耗时**无正相关** `[实测]`

| 指标 | 值 |
|---|---|
| `cacheReadTokens` 起点 | 16256（每会话一致） |
| 首步 `totalTokens`（固定前言） | 中位 **27k** |
| 单会话累计 `cacheReadTokens` 中位 | **4.8M**（极值 102M） |
| 累计 `cacheRead` : 累计 `output` | **65 : 1**（全体 78.8 : 1） |
| 每步耗时 vs `cacheReadTokens` | **r = 0.085** |
| 每步耗时 vs 步数 | r = 0.64 |

反例：`803faa14`（上下文涨到 351k）每步 7.1s；`8a2b8251`（上下文 125k）每步 28.5s。

**结论**：上下文线性膨胀，但每步耗时由任务推理难度而非上下文长度决定。
成本随步数呈二次增长（固定前言被重读 S 次），延迟随步数线性增长 —— 两者是不同维度。

## 3. 派发次数与改动规模**脱钩** `[实测]`

按生产代码行数（排除 test/spec/`.md`）分组，统计每任务的 `*dispatch-context*.md` 份数：

| 生产代码规模 | 任务数 | 平均派发份数 |
|---|---|---|
| ≤100 行 | 5 | 9.8 |
| 101–1000 行 | 24 | 10.7 |
| 1001–10000 行 | 17 | 18.1 |

- 派发份数 vs 全部改动行数：r = 0.50
- 派发份数 vs log10(生产代码行)：r = 0.39

**结论**：改动规模跨 100 倍，派发次数只跨约 2 倍。派发次数不随任务变小而下降。

## 4. gate 的低红率来自 retries 位于其上游 `[实测]`

| 事实 | 值 |
|---|---|
| `gate_run` 事件总数（两仓） | 248 |
| 其中 `exit 1` | **8（3.2%）** |
| `exit 2` | 187 |
| `retries` 总次数（130 任务） | **115** |
| `retries` 分布 | P1 33 / P2 30 / P4 29 / P3 9 / P6 8 / P5 6 |

写入时机：`gate_run` 由 `pre-commit-gate.py:964-972` 在 **commit 时**追加，
每次提交一条 —— 不是每次评审尝试一条。

**结论**：`gate_run` 计数≈提交次数。评审打回表现为 `retries`，发生在 gate 之前；
通过后才提交、才产生 `gate_run`。因此 **3.2% 的红率不构成「gate 无判别力」的证据**。

## 5. 四条降级/分流通道的消费状态 `[实测]`

| 通道 | 定义位置 | 消费情况（grep 实测） |
|---|---|---|
| `ceremony: thin` | `agate/WORKFLOW.md:241`、`phase-cards/P1-requirements.md:124` | `agate/rules/` 四个权威源中 `thin` 命中 **0**；122 个 P1 中声明 2 次；薄化不减任何阶段或派发 |
| `gate_layer.commit_types` | `agate/rules/phases.yaml:186`（`docs-only: [P0,P1,P2,P7,P8]`） | `grep "gate_layer\|commit_types" agate/scripts/*.py` = **0** |
| 派发路由 | `agate-workspace/dispatch-routing.yaml` | 两仓 `dispatch_route` 事件 = **0** |
| `phases:` 裁剪 | P1 frontmatter | `agate-next.py` 对 `phases` 声明零引用；靠主 Agent 读卡执行 |

## 6. token / 步数的可得性 `[实测]`

`agate-summary.py:390` 与 `:424` 输出「token / 步数**不可得**（harness 不报）——本工具不猜、不编造」。

实测：`~/.dsh/sessions/**/session*.jsonl.zstd` 内每条 `assistant/message` 带
`usage: {inputTokens, outputTokens, totalTokens, cacheReadTokens}`。
`agate-cmdstream-adapters.py` 的 `DSHAdapter._decompress` 已能解压同一批文件，
但 `CommandRecord`（`agate-cmdstream-ir.py` 十字段契约）未含 usage 字段。

**结论**：该数据在 DSH 平台可得；当前工具未采集。其他平台未核实。

## 7. 每消息工具调用数 `[实测]`

| 指标 | 值 |
|---|---|
| 每 `assistant/message` 的工具调用数（中位） | **1.23** |
| 均值 | 1.23 |
| >1.5 的会话 | 1 / 13 |

## 8. 工具构成（peekview P1 analyst 样本）`[实测]`

单会话 167 次工具调用：bash **151**、read 9、grep 3、write 1、edit 1。
151 次 bash 中：`cat`/`sed` 读文件 67、`grep` 60、`find` 5、`ls`/`wc` 1、其他 18。

`agate/assets/templates/dispatch-prompt.md` 与 7 个 `execution-roles/*.md`
未对「用 read 工具还是 bash 读文件」作出规定；
`agate/assets/templates/dsh/SKILL.md:68` 有该规定（理由为「避免 bash 挂起」，未提时间成本）。

## 9. 与前沿材料的对照（供引用，非决策）

| 材料 | 与本仓现状的关系 |
|---|---|
| [Anthropic《Building effective agents》](https://www.anthropic.com/engineering/building-effective-agents) | 可分解任务优先 workflow + 程序化 gate；与 agateon 的 workflow 定位一致 |
| [Cognition《Multi-Agents: What's Actually Working》](https://cognition.com/blog/multi-agents-working) | clean-context reviewer 因 attention 机制更聪明；`dispatch-protocol.md` 铁律 3（subagent 只返回路径+摘要）与 Anthropic「输出落 filesystem」同构 |
| [Anthropic《How we built our multi-agent research system》](https://www.anthropic.com/engineering/multi-agent-research-system) | 报告多 agent 用 15× token；同步执行是瓶颈 |
| [Anthropic《Effective context engineering》](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | context rot、attention budget、compaction、note-taking、subagent 返回 1000–2000 token 摘要 |
| [arXiv:2512.08296](https://arxiv.org/abs/2512.08296)（DeepMind & MIT） | 17.2x 为 **trace 级协调开销**；集中式协调降至 4.4x。**不可表述为「多 agent 放大错误 17.2 倍」** |
| [arXiv:2603.16244《More Rounds, More Noise》](https://ar5iv.labs.arxiv.org/html/2603.16244) | 跨上下文评审最优轮数 = 1（F1 0.376 vs 多轮 0.303/0.263）；机制为假阳性压力与评审目标漂移；并行独立评审（3 份多数投票）F1 = 0.393。单模型、注入错误、韩语，适用性未在本仓验证 |
| [arXiv:2601.04748](https://arxiv.org/abs/2601.04748) | 多 agent 编译为单 agent skill library：token −53.7%、延迟 −49.5%、准确率 +0.7%（另据 arXiv:2604.01608，pipeline guidance 类内容有 +19.6/−10.3 的反向效果） |

本仓缺失（`grep` 全仓 0 命中）：`compaction`、`context rot`、`structured note-taking`、
`just-in-time`、skill library、semantic caching、按难度路由。

## 10. 时效性复核清单

- 会话日志格式依赖 DSH 版本（`usage` 字段位置）；平台升级后需复核 §2、§6
- `gate_run` 写入时机依赖 `pre-commit-gate.py`；若改写入点，§4 需重测
- §3 的分组依赖 git 提交信息含 task_id；任务未打标签者不计入
- §5 的 grep 结论随脚本接线变化，复核命令已在表内
