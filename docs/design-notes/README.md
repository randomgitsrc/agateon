# 决策记录索引

记录 agate 协议演进过程中讨论过、做出过决策的问题——包括被否决的方案和否决的理由。目的是防止同一个问题被反复重新讨论一遍（每份记录都应该写清楚"为什么否决 A/B/C，为什么采纳 D"，不只是写结论）。

| 文档 | 问题 | 状态 |
|------|------|------|
| `agent-file-reading-guarantee.md` | 主 Agent 会不会真的去读协议文件，"按需读取"为何不可靠 | 已落地 |
| `main-agent-oversight.md` | 谁来监督主 Agent 自己的判断，LLM 裁判员是否可行 | 部分落地，方案C降级为开放问题 |
| `production-isolation-origin.md` | `[PROD_TOUCHED]` 机制的来历，T005/T006 生产环境事故的通用教训 | 已落地 |
| `subagent-empty-return-root-cause.md` | subagent 空返回的根因分析（落盘指令可缓解）| 已落地（dispatch-protocol.md 派发模板默认含分阶段落盘指令）|
| `subagent-context-mechanism.md` | OpenCode/Claude Code subagent context 真实构成与平台差异 | 事实记录 |
| `docs/archived/reviews/agate-postmortem-T019-meta-review-2026-06-24.md` | T016+T019 两个案例的跨任务模式：主 Agent 系统性绕过现成安全网 | 已落地 |
| `design-structured-layer.md` | 协议规则结构化层设计（rules/*.yaml + S-1~S-6 双向一致性 gate，M0-M3 渐进） | 已落地（TAG0021，v0.60.0）|
| `design-risk-routing.md` | 风险分路由（ceremony routing）设计：客观信号算分，analyst 只解释不决定 | 已落地（TAG0019，v0.58.0）|
| `design-independent-judge.md` | 独立 Judge 机制设计（P6.5 信息隔离 + 三层防造假 + 事件账本） | 已落地（TAG0020，v0.59.0）|
| `dsh-integration.md` | DSH 深度集成扩展点清单（cordis 插件 / session hooks / workflow 派发） | 待立项（RM-AG0033）|
| `platform-extension-research.md` | 第四平台扩展调研（Codex/Cursor/Gemini CLI 能力对照 + 优先级建议） | 调研完成（RM-AG0034 素材）|
| `agateon-trademark-research.md` | Agateon 商标四辖区调研 + 注册建议 | 调研完成（RM-AG0035 前置）|
| `rename-recommendation.md` | 品牌改名决策记录（gatewise/agaton/turngate 淘汰原因 → 拍板 Agateon） | 已决策（RM-AG0035 转执行型）|
| `design-rename-execution.md` | Agateon 改名执行设计（三层解耦：品牌名/仓库名/目录名 + 分层迁移 + 基础设施层兼容策略） | 设计草案（RM-AG0035 执行地基）|
| `design-agateon-portal.md` | Agateon 门户设计（git 之于 GitHub：数据面/控制面分离 + 可验证性三层同构） | 待立项（后续，RM-AG0047）|
| `design-maintainability-gate.md` | 维护性反模式 gate 设计（模式层/检测器层分离，协议定义反模式语义） | 待立项（RM-AG0046）|
| `rm-ag0046-maintainability-gate-plan.md` | RM-AG0046 落地计划 v3（G0 优先 diff 驱动：god-file 跨越 + fuzzy-boundary，P4 挂载 + 登记/P4 评审三重门槛） | 待立项（RM-AG0046）|
| `design-md-field-set.md` | 结构化字段写入工具设计（agate-md-field-set：写入即校验 + 自描述 + 权限引导，消灭手写 frontmatter 摩擦） | 设计提案（RM-AG0048）|
| `return-to-zero-proposal.md` | 双归零方法论引入失败处理闭环（PeekView 提案收编：known-failures 补复现证据/举一反三 + 归零检查单，方案 B 参考工具非强制 gate） | backlog（RM-AG0053 参考输入）|
| `design-orchestration-semantics.md` | 编排语义统一设计（自动化在协议内，平台只做执行环境：dispatch 五模式为唯一语义锚点 + 状态机 CLI 推进侧落地，复用 check-state-transition.py/phases.yaml，CLI 为 /loop 档位 C 可观测层） | 设计讨论 v3b（候选 RM-AG0054；评审链：v1 FAIL→v2 修复→Claude 评审 FAIL→v3 落盘复审 PASS→第三轮 Claude 元评审经时间线核验不成立，可追溯性建议已采纳）|
| `design-dispatch-routing.md` | 派发路由设计（两机制：① `rules/dispatch-routing.yaml` 候选 `{cli, model}` 表——用户编码"复杂/专业阶段配高级模型、大批量阶段配便宜模型"，`cli` 可为 `native` 或另一个 CLI，全阶段适用，只查表不按任务内容选型，按序探测→逐级回落终点恒为同平台同 model，`dispatch_route` 留痕，决策机械化落 CLI/子进程形式可端到端自动化；② CLI 子进程形式的 tmux 观测层。动机=给角色隔离补模型维度缓解局限 2）| 设计收敛（跨 CLI 线 v1 FAIL→…→v5 + 角色-模型线 v1 FAIL→v2 PASS，2026-09-08 合并精简为两机制；两轮外部独立评审 FAIL→PASS + 一轮内部；机制三平台端到端实测，见 `docs/research/cross-platform-dispatch-mechanics.md`。**已申领 RM-AG0060**（backlog，epic），立项前待办见文档 §7）|

| `doc-consistency-audit-2026-09.md` | 门面 + `agate/*.md` 协议文档 文实一致性审计：逐文件裁定 + 四跨文档不一致（平台表行集 + Codex 权威源 / P6.5 门面·orchestrator-template 缺席 / `agate next` 四文档缺席 / CONTEXT exit-code 矛盾）+ LIMITATIONS 精简重构 + 历史/失效文件存档移除（§8）+ 5 批修改计划 | v3 终版（已过一轮独立评审，见 `docs/reviews/review-doc-consistency-audit-2026-09.md`），待按批次执行 |

新增决策记录时，按这个格式写：问题是什么 → 讨论过哪些方案及为何否决 → 最终采纳的方案及理由 → 状态（已决策待落地 / 已落地，落地位置写清楚）。
