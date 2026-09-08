---
review_date: 2026-09-08
reviewer: independent-design-review
change_summary: 派发路由设计（design-dispatch-routing.md，main 分支当前版本）独立评审——外部评审，不采信文档自称"已过内部评审"
files_reviewed: [design-dispatch-routing.md（225行，main 分支 76de933）, docs/research/cross-platform-dispatch-mechanics.md（319行，同批引入）]
---

# 派发路由设计 独立评审（外部）

审查对象：`docs/design-notes/design-dispatch-routing.md`（main 分支当前版本，225 行）+ 其引用的 `docs/research/cross-platform-dispatch-mechanics.md`（319 行）。

文档沿革自述"2026-09-08 内部独立评审一轮：修 §2.4a 结构损坏（BLOCKER）...合并稿仍需走一轮**外部**独立评审再立项"——本轮即该外部评审，不采信文档自称的"已修复"，逐项重新核实。

## 结论汇总

| # | 问题 | 级别 |
|---|------|------|
| B1 | design-note §2.3/§7 事项7 将"Codex `spawn_agent` schema"与"三平台 model 传参端到端已验"并列表述为同等强度的"本轮已全部实测通过"，但 research 报告自己标注该 schema 是 `[自述]` 证据强度（§ 287 行"未见 background/timeout/permission 字段，模型自述称 complete"），不是 `[实测]`。design-note 引用时丢失了这个证据强度区分，读者会误以为 schema 完整性也是端到端验证过的 | **BLOCKER** |
| B2 | research 报告对 OpenCode 旧 bug②（"父会话交互式切换模型后 subagent 不跟随"，原 issue #17870）没有直接复现测试，只给出一段技术推理（"父 `opencode run -m` 切的是 session model，不改 agent 配的 model"）来说明该 bug 不成立；但 design-note §7 事项7 概括"本设计的阻断性机制项本轮已全部实测通过（三平台 `cli: native` model 指定...）"，把这条也归入"实测通过"，与其证据强度（推理/文档级，非实测复现）不符 | **BLOCKER** |
| W1 | §2.4a"续接优先、重起兜底"这条设计决策的技术依据（research §7）提到"Claude Code 有 #43696 报告"（续接后上下文丢失），但 design-note 正文没有说明：如果 Claude Code 命中这个已知 bug，"续接优先"这个默认行为会不会让打回重做静默使用一个已经丢失上下文的"续接"、且因为续接命令本身没有报错（只是内容不对）而被误判为成功——这跟 §2.2 "真跑失败就走下一候选"的降级逻辑不同，续接失败没有明确的"失败信号"，只有"内容看起来不对"这种更难判定的软信号，design-note 没有讨论这条边界 | WARNING |
| W2 | §3 tmux 实机核实标注为"本机 tmux 3.4，含真人 attach"——这是良好的实证做法，但"本机"具体是什么环境（容器/物理机/CI）、tmux 3.4 是否是协议支持环境里的典型版本，design-note 未标注，跟 research 报告 §10 提到的"复核清单，版本升级后照单复跑"这条原则不完全对齐——如果本机 tmux 版本偏新或偏旧于协议实际支持范围，这次"已实测通过"的结论时效性边界不清楚 | WARNING |
| N1 | design-notes/README.md 是否已登记本篇，未核实（本轮评审未检查此项，供后续确认） | NIT |

## 事实核验

| 声称 | 核验结果 |
|------|---------|
| "Claude Code Task 单次调用传 model 参数，父 Sonnet → 子 Haiku 实测生效" | ✅ research §125 明确标注 `[实测]`，证据强度准确 |
| "OpenCode 旧 bug①③ 在 v1.18.11 不存在" | ✅ research §127/284 有具体复现测试记录（配置命名 agent、实际派发、核对子代理回报的 model），证据强度标注 `[实测]` 准确，且给出了"之前误判为 bug 的原因"这层额外解释，评审认可这条修正的严谨性 |
| "OpenCode 旧 bug② 是否已核实" | ❌ 不成立——见 B2，未直接复现测试，只有技术推理 |
| "Codex spawn_agent(model=, reasoning_effort=) 按次生效" | ✅ research §126 有具体实测记录（父 medium → 子 high 且 model 正确），这条本身证据强度 `[实测]` 准确 |
| "Codex spawn_agent 完整 schema" | ⚠ 见 B1——research 自己标注 `[自述]`，design-note 引用时未保留这个区分 |
| "本设计不修改 check-gate.py/check-state-transition.py/phases.yaml" | ✅ §5 明确声明未改动，全文未发现与此矛盾的条款 |
| "留痕呼应局限3'回避报告问题'倾向" | ✅ 与 `LIMITATIONS.md` 局限3原文引用一致，逻辑成立 |
| "`fallback`字段被移除，终点固定回落默认派发" | ✅ 核对全文，未再出现`fallback`字段，架构上确实规避了此前版本的权威源分裂问题 |

## B1（BLOCKER）：Codex spawn_agent schema 的证据强度被错误合并

`docs/research/cross-platform-dispatch-mechanics.md` 第 287 行明确写着这条 schema 信息是"模型自述称 complete"，即厂商/工具自己声称的信息，不是调研者独立验证过"这就是全部字段、没有遗漏"的实测结论——"未见 background/timeout/permission 字段"这句话本身就在提醒读者"我们没有验证过是否存在这些字段，只是没在自述里看到"。

design-note 两处（§2.3 表格、§7 事项7）把这条跟"父传 model=X，子确以此身份回应"这类真正端到端复现过的内容并列，且 §7 事项7 用"本设计的阻断性机制项本轮已全部实测通过"这句话统一概括，实质上抹掉了两者的证据强度差异。这不是文字洁癖——如果后续基于这份"完整 schema"设计具体的调用代码（比如假设没有 `timeout` 字段就不处理超时场景），而实际上 `spawn_agent` 其实有一个未被自述提及的 `timeout` 参数，这个假设错误的代价会在实现阶段才暴露，而不是在评审阶段就被拦下。

**修复建议**：§2.3 表格与 §7 事项7 中涉及 Codex schema 完整性的表述，需要还原研究报告的证据强度标注（如"schema 字段 `[自述]`，未见 background/timeout/permission 字段但未验证是否遗漏"），不能简单归入"已实测通过"这个笼统结论。

## B2（BLOCKER）：OpenCode 旧 bug②未经复现测试，design-note 概括表述与此不符

已在结论汇总说明。这条本质与 B1 是同一类问题的另一处实例——**"我们重新测试过某项声称，发现不成立"和"我们根据机制原理推断某项声称大概率不成立"，是两种不同强度的结论，design-note 把两者混同表述为"实测通过"**。research 报告自己在处理 bug①③时做得很好（明确给出复现步骤和结果），但 bug②这条缺了同等力度的验证，design-note 汇总时应该如实反映这个不对称，而不是让读者以为三个 bug 都经过了同等严格的核实。

**修复建议**：§7 事项7 拆分表述——"bug①③已直接复现测试并确认不存在；bug②（父会话切换模型后子代理是否跟随）尚未直接复现，现有结论基于机制原理推断（`opencode run -m` 只影响 session model 不影响 agent 配置），建议落地前补一次直接复现测试"。

## W1：续接失败的"软信号"问题未讨论

已在结论汇总说明。**修复建议**：§2.4a 补充讨论"续接命令本身成功返回，但内容表明上下文实际丢失"这种情况下，路由层如何判断该视为成功还是失败——如果没有客观判定手段，至少应该如实标注这是本设计目前未处理的一个已知缺口，而不是留白不提。

## W2：tmux 实测环境的代表性未标注

已在结论汇总说明。**修复建议**：补充一句实测环境的基本描述（是否为协议目标支持环境的典型代表），或明确这条待落地时在目标环境重新验证一次。

## 是否通过

**FAIL**——B1、B2 需要修复后重新提交复审。这两条 BLOCKER 性质相同（证据强度被合并表述），建议一并处理，工作量不大：本质是把 §2.3/§7 事项7 里"本轮已全部实测通过"这个笼统断言拆解成"哪些是实测、哪些是文档自述、哪些是推理"，如实反映 research 报告自己已经做好的证据强度分级，不需要重新调研，只需要把已有的区分正确传递到 design-note 里。W1/W2 建议一并处理，不阻断。

> 评审说明：本轮之外，design-note 与 research 报告的整体质量是高的——三平台核心机制（model 传参、权限拉平、结构化输出解析、tmux 全链路）确有扎实的端到端实测支撑，`fallback` 字段权威源分裂这个此前版本的架构问题也通过重新设计（终点固定回落）从根本上规避，不是打补丁。本次发现的两条 BLOCKER 都是"证据强度传递失真"这一类问题，不是机制设计本身的缺陷，修复成本低，不需要推翻任何设计决策。
