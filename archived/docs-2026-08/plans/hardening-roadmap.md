# agate 硬工具化路线图

> 日期：2026-06-29（v2：2026-06-30 修订；v3：2026-06-30 评审反馈修订；v4：2026-07-02 状态更新；v5：2026-07-24 版本计划补充）
> 状态：Phase 1 + 2A + 2B + 2C 已落地；Phase 3 已取消（依赖平台，非 agate 可独立实现）
> 关联：LIMITATIONS.md 局限 3（主 Agent 判断力是单点故障）、局限 4（subagent 不可观测）

---

## 1. 背景

### 1.1 问题

agate 经过多次复盘 + 实战评审，反复验证同一个根因：

**主 Agent 既是运动员又是裁判，且默认倾向于少走路。**

Agent 的"走捷径"不是"遇到困难时的行为退化"，是**出厂设置**——一切时候都倾向于少走步骤。所有依赖 Agent 自觉的环节都是脆弱的。

### 1.2 核心原则

> **有确定逻辑要处理的事情，用 hook、脚本等硬工具执行，不靠 Agent 自觉。**

### 1.3 与现有协议的关系

硬工具化是**加法，不是替换**。协议仍然告诉主 Agent "必须跑 gate"——现在多了一层：即使主 Agent 忘了跑，hook 也会跑。即使主 Agent 造假结果，CI 会重跑验证。

---

## 2. 已落地内容

### Phase 1：可脚本化检测（已全部落地）

| 编号 | 名称 | 脚本 | 状态 |
|------|------|------|------|
| P1.1 | pre-commit hook | `scripts/pre-commit-gate.sh` | ✅ 已实现（含多任务适配） |
| P1.2 | PROD_TOUCHED 检测 | `scripts/pre-commit-gate.sh` 内 | ✅ 已实现 |
| P1.3 | CI gate backstop | `.github/workflows/` + `scripts/ci-gate-backstop.py` | ✅ 已实现 |
| P1.4 | gate 结果存储 | `scripts/agate_common.py` | ✅ 已实现（.gate-result.json + .gate-history.jsonl） |
| P1.5 | READY 检查 | `scripts/check-gate.py` P8 case | ✅ 已实现（部分） |
| P1.6 | CHANGELOG 检查 | `scripts/check-changelog.py` | ✅ 已实现 |
| P1.7 | P6 证据格式检查 | `scripts/check-p6-evidence.py` | ✅ 已实现（含 R1a 截图 >1KB + md5 去重） |

### Phase 2A：状态一致性强制（已全部落地）

| 编号 | 名称 | 脚本 | 状态 |
|------|------|------|------|
| P2.3 | 状态转移强制 | `scripts/check-state-transition.py` | ✅ 已实现（含 per-phase MAX_RETRY + 回退跳变 exit 1） |
| P2.4 | 重试计数强制 | `scripts/check-state-transition.py` | ✅ 已实现（按阶段差异化） |
| P2.5 | 回退跳变检测 | `scripts/check-state-transition.py` | ✅ 已实现（恢复 exit 1，只查回退方向，保留 PAUSED 守卫） |
| P2.15 | .state.yaml 格式校验 | `scripts/check-state-yaml.py` | ✅ 已实现 |
| — | 多任务 .state.yaml 扫描 | `scripts/pre-commit-gate.sh` | ✅ 已实现（Phase-产出一致性 WARNING） |
| — | P2.6 修复后全量重跑验证 | — | ❌ 移除（hook 无法验证 full run vs partial run） |

### Phase 2B：产出独立化与流程选择硬约束（已全部落地）

| 编号 | 名称 | 脚本/机制 | 状态 |
|------|------|----------|------|
| P2.1 | P6 验收独立化 | `scripts/check-p6-provenance.py` | ✅ 降级方案 v2（客观行为审计：证据-结论对应 + dispatch-context 审计 + BDD 总数对照 + R1b vision YAML 审计） |
| P2.2 | BDD 格式 + 总数对照 | `scripts/check-p6-provenance.py` | ✅ 已实现（provenance 审计覆盖） |
| P2.7 | 风险等级字段 | `scripts/check-pruning.py` | ✅ 已实现（low/medium/high） |
| P2.8 | 裁剪条件 hook 检查 | `scripts/check-pruning.py` | ✅ 已实现（P2/P4/P5/P6 不可裁 + P3 仅 low 可裁 + P7 源码文件数 + P8 internal_only + 跳过风险 nudge） |
| P2.9 | 裁剪声明回写 | `scripts/check-pruning.py` | ✅ 已实现（override 字段） |
| P2.10 | P2 评审派发强制 | `scripts/check-p6-provenance.py` | ✅ 降级方案 v2（agent 字段软提醒 + dispatch-context 审计） |
| P2.11 | SCOPE+ 处理追踪 | `scripts/check-scope-resolved.py` | ✅ 已实现 |
| P2.12 | 复盘异常触发 | `scripts/check-retrospective.py` | ✅ 已实现（按阶段差异化重试提醒） |
| P2.13 | 非 agate 任务风险矩阵 | `WORKFLOW.md` | ✅ 已实现 |
| P2.14 | "直接做"最低要求 | `WORKFLOW.md` | ✅ 已实现 |
| — | P2 form check（权衡/选择理由） | `scripts/check-gate.py` | ✅ 已实现 |
| — | P2 status:approved + 四字段检查 | `scripts/check-gate.py` | ✅ 已实现 |
| — | P8 internal_only_reason | `scripts/check-pruning.py` | ✅ 已实现 |
| — | md5 截图去重 | `scripts/check-p6-evidence.py` | ✅ 已实现 |
| — | self-gate 机制 | `SELF-GATE.md` + `scripts/check-protocol-consistency.py` CHECK 9 | ✅ 已实现（含反向传播） |

### 架构：两层防护（已落地）

```
Layer 1: pre-commit hook（本地，防"不知不觉绕过"）
  - 扫描所有暂存 .state.yaml（根 + 任务级）
  - 跑 gate + 写 .gate-result.json
  - PROD_TOUCHED 检测
  - 状态转移 + 重试上限 + 回退跳变
  - 裁剪条件 + SCOPE+ 追踪
  - P6 证据格式 + md5 去重
  - phase-产出一致性 WARNING

Layer 2: CI backstop（远程，防"故意绕过"）
  - 重跑 gate + 对照 .gate-result.json
  - 一致性检查（CHECK 1-9）
  - 捕获 --no-verify 绕过
```

---

## 3. 待落地内容

### Phase 2C：ADR + 术语表（v0.14.0 已落地）

| ID | 内容 | 脚本/文件 | 状态 |
|----|------|----------|------|
| P2.16 | 架构决策记录 | `adr.md`（6 条核心 ADR） | ✅ 已实现 |
| P2.17 | 术语表 + 上下文 | `CONTEXT.md`（20 个术语） | ✅ 已实现 |
| P2.18 | A7 审查锚定到 ADR | `protocol-alignment-review.md` | ✅ 已实现 |

### Phase 2D：BDD 标准化 + bug 修复（v0.20.0 已落地）

| ID | 内容 | 脚本/文件 | 状态 |
|----|------|----------|------|
| P2.19 | BDD 编号格式标准化 | `#### BDD-NN:` + `###` 功能分组 | ✅ 已实现 |
| P2.20 | T3: P1 BDD 计数硬阻 | `check-p6-provenance.py` grep -cE | ✅ 已实现 |
| P2.21 | T6: AGATE_CARD 块剥离 | `pre-commit-gate.sh` sed | ✅ 已实现 |
| P2.22 | M5: gate_commands YAML 解析 | `check-gate.py` python3 regex | ✅ 已实现 |
| P2.23 | B01→BDD 批量替换 | 8 个 bats 文件 + 5 fixture | ✅ 已实现 |

### Phase 3：平台接口规范（已取消 — 依赖平台能力，非 agate 可独立实现）

| 编号 | 名称 | 原计划 | 取消理由 |
|------|------|--------|---------|
| P3.1 | 平台接口规范文档 | 定义 agate 需要的平台能力 | 平台不会为 agate 实现专属接口 |
| P3.2 | subagent 可观测性 | 平台暴露 subagent 活动信号 | 依赖平台支持，无法自行实现 |
| P3.3 | gate 结果独立存储 | 平台提供主 Agent 不可写的存储位置 | 依赖平台支持，无法自行实现 |
| P3.4 | gate 执行平台化 | 平台在 subagent 返回后自动触发 gate | 依赖平台支持，无法自行实现 |

**P2.1 P6 验收独立化的根治**：当前降级方案靠 provenance 审计（证据-结论对应 + BDD 总数对照 + vision YAML），但主 Agent 仍可造假证据。根治需平台支持独立 git author，Phase 3 已取消——接受此为结构性局限。

---

## 4. 与 LIMITATIONS.md 的对应关系

| 局限 | 描述 | Phase 1 缓解 | Phase 2 缓解 | Phase 3 根治 |
|------|------|-------------|-------------|-------------|
| 局限 1 | 测试质量上限 | — | — | —（方法论边界） |
| 局限 2 | 同源模型盲区 | — | — | —（方法论边界） |
| 局限 3 | 主 Agent 判断力单点 | ✅ gate 执行不被跳过 | ✅ P6 审计 + 状态强制 + 流程选择硬约束 | 取消（结构性局限，接受） |
| 局限 4 | subagent 不可观测 | — | — | 取消（结构性局限，接受） |
| 局限 5 | 协议文档一致性 | — | ✅ self-gate + CHECK 9 | — |
| 局限 6 | 运行时依赖 | — | ✅ 文档化（LIMITATIONS.md + AGENTS.md） | — |
| 局限 7 | vision/UI 基础设施 | — | ✅ 文档化（LIMITATIONS.md） | — |
| 局限 8 | CI backstop 仅 GHA | — | ✅ 文档化（LIMITATIONS.md + AGATE_TASKS_DIR） | — |

---

## 5. 版本计划

### v0.21.0 — 协议自维护基础设施补丁（P2+P3 合并）

| ID | 内容 | 涉及文件 | 状态 |
|----|------|----------|------|
| P2.29 | LIMITATIONS.md 交叉引用 ADR | `LIMITATIONS.md` | ✅ 已实现 |
| P2.30 | 反向传播表补 BDD 传播路径 | `protocol-alignment-review.md` | ✅ 已实现 |
| P2.31 | check-retrospective.py 排除 dispatch-context + AGATE_CARD | `check-retrospective.py` | ✅ 已实现 |
| P2.32 | gate 错误消息列具体文件名 | `check-p6-evidence.py` | ✅ 已实现 |

**合理性审查 DROP 项**：P2.25（change_nature 是 pre-protocol 决策非 P0-brief 字段）、P2.26（P0 入口点措辞差异是有意设计）、P2.28（一行默认值无需测试）

**DOWNGRADE 项**：P2.24（ADR-007 事后记录低优先级）、P2.27（python3 环境变量零真实报告）

### v0.22.0 — Superpowers 吸收 + 上下文编排 + 并行执行

| ID | 内容 | 涉及文件 | 状态 |
|----|------|----------|------|
| P2.37 | architect.md 方案探索方法论（按场景类型） | architect.md | ✅ 已实现 |
| P2.38 | investigate.md 结构化诊断强化（≥3 原因/排除留痕/禁止先改试试） | investigate.md | ✅ 已实现 |
| P2.39 | dispatch-prompt.md P4 回退诊断模板自动注入 | dispatch-prompt.md | ✅ 已实现 |
| P2.40 | verifier.md 验证纪律（先验证后结论） | verifier.md | ✅ 已实现 |
| P2.41 | implementer.md 最小实现原则 + 测试不通过决策树 | implementer.md | ✅ 已实现 |
| P2.42 | dispatch-context 上游关联自动提取脚本（--write 模式） | agate-extract-context.py + bats | ✅ 已实现 |
| P2.43 | 阶段卡片并行执行操作指引（评审+按包拆分+基础设施隔离） | 5 phase cards + dispatch-protocol.md | ✅ 已实现 |
| P2.44 | loop-orchestration.md 并行执行状态更新 | loop-orchestration.md | ✅ 已实现 |

### v0.23.0 — 通用化兼容修复 + dispatch-prompt 持久化自动化

| ID | 内容 | 涉及文件 | 状态 |
|----|------|----------|------|
| P2.45 | check-tdd-red.py 通用化兼容修复（flags 默认值 + vitest 适配示例 + 4 bats） | check-tdd-red.py + bats | ✅ 已实现 |
| P2.46 | dispatch-prompt 持久化自动生成（渲染脚本 + 3 处排除列表 + bats） | agate-render-dispatch-prompt.py + 3 scripts + bats | ✅ 已实现 |

### v0.24.0 — 环境基线快照 + P5 机械化回归判定

| ID | 内容 | 涉及文件 | 状态 |
|----|------|----------|------|
| P2.47 | 环境基线快照捕获脚本（幂等、缓存、不阻塞）+ P3/P4 挂载点 | agate-capture-env-baseline.py + P3-tdd.md + P4-implementation.md + bats | ✅ 已实现 |
| P2.48 | P5 gate 机械化回归判定（pre/post diff + 新增拦截 + 预存登记强制）+ fail-list.txt 产出规格 | check-gate.py + P5-verification.md + bats | ✅ 已实现 |
| — | LIMITATIONS.md T068 实证案例 | LIMITATIONS.md | ✅ 已实现 |

### v0.23.0+ — 设计讨论（P4，按需启动）

| ID | 内容 | 依赖 | Issue |
|----|------|------|-------|
| P2.33 | C8 机械化 + 领域触发评审硬要求 | 独立设计讨论 | #59 |
| P2.34 | 审计/可观测性重设计 | 独立设计讨论 | #60 |
| P2.35 | 重试预算模型（功能/格式分离） | 独立设计讨论 | #61 |
| P2.36 | Monorepo 多目录 AGATE_TASKS_DIR | 独立设计讨论 | #62 |

### v0.40.0+ — 并行执行环境隔离（P4，按需启动）

| ID | 内容 | 依赖 |
|----|------|------|
| P2.66 | 并行执行环境隔离规范：多 subagent 并行时 debug server 生命周期归属（共享 or 端口分配）、`debug_env`/`isolation_check` 字段落地语义。协议已有"按包拆分并行"（dispatch-protocol.md L623）和"专家组并行评审"（P2 card），缺的是并行时的环境隔离规范。来源 T091 摩擦点4 + C 讨论扩大。 | 独立设计讨论 |
| P2.67 | TaskFlow before/after 案例研究：TaskFlow（randomgitsrc/taskflow，2026-03）是"用 Claude Code 但没用 agate 流程"的项目——5000 行功能但零测试、CLI/API 双轨 schema 失控、单 commit 半途而废。对比 agate 自身 T001（v0.40.0 结构化改造，602 测试全绿）。评估：① 作为 agate 商业化案例素材（"同样 AI，有无质量流程产出天差地别"）；② 是否吸收其教训进 LIMITATIONS/案例库；③ 是否用 agate 重做其核心。来源 2026-08-11 商业分析会话。 | 独立设计讨论 |
| P2.68 | agate 自进化复盘闭环（任务级遥测）：把"对 agate 自身的复盘"从零散的 peekview 会话文档（T086/T090/T091 均人工写于 peeklink）变成 agate 协议内固定环节 + 结构化回传通道。核心：① P8/READY 收尾加可选产出 `agate-review.md`（正常任务可跳过，避免形式主义）；② 模板固定三块：技术原因/管理原因/agate 角色分析；③ 只回传"agate 的问题"（区分 agent 问题/项目问题）；④ 回传经 docs/issues/ 或 peeklink 进入 agate 迭代。与 check-retrospective.py（异常提醒）互补。分级：A 模板+固定环节 / B agate-feedback.sh 自动化收集 / C 平台化。注意避免 T090 orchestrator-log 8% 合规率的教训（纯自律零强制规则无价值）。来源 2026-08-11 商业分析会话。 | 独立设计讨论 |
| P2.69 | 协议本体防篡改/完整性检测：项目 agent 用 agate 时能否阻止它改 `~/.agate` 协议本体。分析结论：**不能可靠阻止**——agent 有 bash 全权限（可 chmod 后改内容再还原权限），只读权限/密钥方案均不可行（同"密钥方案不可行"逻辑）。**可行方向是 git 篡改检测**：协议本体是 git 仓库，orchestrator 启动时 `git -C ~/.agate status --porcelain` 非空 → WARNING"协议本体被改动"（区分：agate 开发任务合法改动 vs 项目 agent 篡改）。待讨论：① 检测放 agate-summary.py（现有副本漂移检测的自然扩展）；② 是否需区分"开发态 vs 使用态"；③ CI 独立 checkout 校验的可行性。来源 2026-08-11 会话。 | 独立设计讨论 |
| P2.70 | 低风险任务派发裁剪评估（执行效率短板）：T090 复盘实测中等 UI 任务约 **21 次 subagent 派发**，"调度成本是实现工作量的数倍"——协议对过程质量的主动投资，但简单/低风险任务上投入产出比存疑。待评估：① 是否为低风险任务提供更细的派发裁剪规则（类似现有 risk_level 裁剪，但针对"派发次数"而非"阶段"）；② 单次 gate 全量 bats（~2min）是否可增量验证优化；③ 建立"派发密度 vs 任务复杂度"的量化基准。roadmap 现有并行项（P2.43/44/55/66）解决"并行执行"，未解决"派发开销本身"。来源 2026-08-11 架构效率评估会话。 | 独立设计讨论 |
| P2.71 | **项目生命周期演进框架（顶层主题）**：agate 目前是"任务粒度"——保证每个任务交付质量（BDD+gate+评审），但不审视"任务累积效果"（模块耦合/架构熵增/技术债）。人类系统从 0-1 叠加成屎山的机制（无人看全局、债不登记、重构推迟）在 AI 场景无对应设防。待设计：① **技术债登记**（项目级 backlog，review 发现债→登记→可调度）；② **架构健康周期性审视**（非每任务，检查模块耦合/依赖方向/重复度，产出演进建议）；③ **重构/架构演进作为一等任务**（P1 可为"重构 X"，验收=行为不变+回归全绿，非伪 BDD）；④ 克制原则：不加常设阶段/角色，不设架构硬 gate（语义判断机器不可判），重心在"债务可见+演进可调度"。来源 2026-08-11 会话（"agate 能否避免屎山/承载 0-1 到持续优秀"）。 | 顶层设计讨论（可能为 v2.1+ 主题） |

### 不修清单（设计选择/低价值/arms race）

| ID | 内容 | 理由 | Issue |
|----|------|------|-------|
| — | G3: P6 无单命令入口 | pre-commit-gate 已自动调用 | #63 |
| — | G5: SCOPE+ 回补后无强制重审 | 评审员训练问题 | — |
| — | G8: 频繁修改同一文件检测 | 低价值，事后审查足够 | — |
| — | M3: 模板示例偏向 JS/Python | 已记录，非阻断 | — |
| — | M4→P2.27 | 已提升为可修项 | #53 |
| — | P6-format 裸路径不加括号 | 语义判断，provenance 审计处理 | — |
| — | N14-N16: 流程/训练问题 | 非协议层面 | — |
| — | M6: P6 发现已知局限无后续跟踪 | workflow 问题 | — |
| — | T4: P3 测试覆盖边界条件 | test-designer 职责 | — |
| — | T5: agate-next-card.py 路径解析 | ✅ 已修复（v0.21.1：用 AGATE_ROOT 替代 AGATE_REPO，ci-gate-backstop.py 用 __file__ 相对路径） | — |
| — | M2: 证据扩展名白名单 | 实测已无白名单（by design, ADR-003），关闭 | — |
| — | 目录改名 agate/ → agate-core/ | 高成本中收益（~205 引用 / ~33 文件 / 下游 breaking），留待后续窗口重新派生 | PR #46 已关 |
| — | P4 gate 不验证 P4-review.md agent≠main | P4 gate（check-gate.py:139-142）只检查暂存区代码文件，不验证 review 文件 agent 字段；P2 gate 有此检查（:112-114）但 P4 无；文档说"与 P2 评审同规则"但脚本未强制执行；留待 v0.23.0+ 补充 P4 gate agent 检查 | R2 评审 S-R2-1 |

### 结构性限制（需平台支持，记录不修）

| 局限 | 描述 | 根治条件 |
|------|------|---------|
| 局限 3 | 主 Agent 判断力单点故障 | 平台支持独立 git author |
| 局限 4 | subagent 不可观测 | 平台暴露 subagent 活动信号 |
| — | P6 证据真实性无法机器验证 | CI 独立重新生成证据 |
| — | dispatch-context provenance 链 | 平台支持 subagent 工具调用日志 |

### 代码 TODO

| 位置 | 内容 | 触发条件 |
|------|------|---------|
| `check-p6-provenance.py:245` | 移除旧格式兼容 | 后续 |

---

## 5. 版本计划

### v0.25.0 — 阶段卡片措辞加固 + gate_commands.P3

**P2.50: 阶段卡片措辞加固 — 消除 agent 可钻空子**

**状态**：已实施
**来源**：T082 复盘（agent 跳过 P4 评审，用 gate exit 0 作为合理化借口）
**改动**：
- 所有阶段卡片"推进条件"改为显式 AND checklist，标注"全部满足才推进"
- 消灭"可选"/"若有触发"/"若方案依赖"/"可以考虑"等模糊措辞
- "按包拆分并行（可选）"统一改为"（条件触发）"
- check-gate.py P2 review 文件不存在时 exit 1（bug fix：原来文件不存在时跳过检查）
- design_trivial / follows_existing_pattern 须附理由
- minimal_validation 强制声明（"纯代码逻辑"也须写明理由）
- P4 自查节"P5 由主 Agent 亲自执行"→"派发 verifier subagent 执行"
- P6 "先验证功能再满足格式"→"两者都必须满足"
- P5 签名校验"轻量验证"→"必须"
- P8 "手动确认"→"必须亲自执行"
- 基础设施隔离"nudge"→"必须，未分配导致冲突时计为重试"

**P2.49: gate_commands.P3 — check-tdd-red.py 自动读取测试运行器**

**状态**：已实施
**来源**：T076 复盘（非 pytest 项目测试命令重复声明问题）
**改动**：
- gate_commands 新增可选 P3 键（architect 在 P2 声明测试运行器命令）
- check-tdd-red.py 回退链扩展：`$TEST_RUNNER → gate_commands.P3 → which pytest → exit 3`
- P3 键用 verbose 输出（区分 A/B 类错误），P5 键用紧凑输出（只判过没过），两者分离

**不修理由**（P3 e2e 质量闸门）：
- "选择器写得好不好"不是机器可判定的，gate 不做语义判断
- P5 实跑 e2e 已经是正确的防线，T076 也在 P5 发现并修复了
- test-designer.md 已有指导，执行不到位是 subagent 质量问题

### v0.26.0 — 测试输出标准化（Tech-Stack Neutral）

**P2.51: check-tdd-red.py + agate-capture-env-baseline.py 技术栈无关化**

**状态**：已实施
**来源**：T079+T082+T083 复盘（check-tdd-red.py 技术栈绑定问题）
**改动**：
- check-tdd-red.py 重写：废弃 pytest pattern 默认值/-q flag，改为 formatter+JSON 标准格式
- agate-capture-env-baseline.py：fail-list 提取改用 formatter+JSON
- 新增 6 个内置 formatter 模板（pytest/vitest/go-test/generic-tap/generic-junit-xml/generic-exit-only）
- gate_commands 扩展：P3_formatter/P5_formatter/project_module 可选键
- agate_common.py 新增 resolve_formatter() / run_test_with_formatter() 公共函数
- 多技术栈支持：P3 + P3_js 多键声明
- check-p6-evidence.py：截图格式从 PNG-only 放宽为任意图片格式
- check-gate.py：P7 DESIGN_GAP 正则放宽匹配 markdown blockquote（T083 修复）
- 文档全面去 pytest 软绑定

---

## 7. T084+T075 复盘驱动的改进（2026-08-01）

> 来源：T084（1 行 CSS 改动耗时 9h）+ T075（P0-P2 耗时 2.5h）
> 核心问题：30% 耗时是损耗（gate 拦截诊断 2.2h + review 迭代 2h + 回退修复 1.2h）
> 信噪比：有效工作 ~4h / 总耗时 ~16h = 25%

### P0 — 脚本 BUG（立即修）

| ID | 问题 | 文件 | 来源 | 预期节省 |
|----|------|------|------|---------|
| P2.52 | check-pruning.py `phases:` 只认内联格式，不认 YAML 列表格式 | check-pruning.py:26 | P-AGATE-1 | 0.6h |
| P2.53 | check-scope-resolved.py + check-retrospective.py [SCOPE+] 误匹配 progress 文件 | check-scope-resolved.py:19, check-retrospective.py:37 | P-AGATE-2 | 0.2h |

### P1 — 设计缺陷（本版本修）

| ID | 问题 | 措施 | 来源 | 预期节省 |
|----|------|------|------|---------|
| P2.54 | CHANGELOG 检查从 P1 就触发 WARNING，但 CHANGELOG 是 P8 产物 | 限制到 P7/P8 phase 才检查 | P-EXEC-4 | 0.8h |
| P2.55 | 并行派发指导只有原则级"同时派发"，无操作级指令 | P2/P4 卡片追加操作级说明：单消息发多个 task 调用 | 并行派发问题 | 0.5h |
| P2.56 | dispatch-prompt 模板未指示 subagent 评审后必须改 frontmatter status | 模板追加明确指令 | P-LLM-1 | 0.3h |
| P2.57 | P6 evidence 与 acceptance 声明一致性无检查 | check-p6-provenance.py 审计 5 扩展 | P-EXEC-1 时序倒置 | 0.5h |

### P2 — 机制改进（后续立项）

| ID | 问题 | 措施 | 来源 | 预期节省 |
|----|------|------|------|---------|
| P2.58 | 小任务（≤3 行改动）走完整 agate 流程信噪比过低 | fast-track 机制：P0+P1(简版自审)+P4+P5+P6(快速)+P8 | T084 1 行 CSS 9h | 3-4h |
| P2.59 | SCOPE_RESOLVED 标记时机指导不够显式 | P2/P4 卡片追加"收到 SCOPE+ 后推进前必须标记 SCOPE_RESOLVED" | P-EXEC-3 | 0.4h |
| P2.60 | P1-P3 合并 commit 绕过逐阶段 commit 检查 | 卡片推进条件强调"先 commit 本阶段产出再改 phase" | 上下文管理 | — |

### T075 复盘驱动的改进（2026-08-01）

> 来源：T075（53 BDD / 13.5h / 损耗 44%）— spec 缺陷是新的损耗类型

**P2.61: architect gate_commands 校验清单 → gate 脚本检查**

**状态**：已实施
**来源**：T075 复盘 AGATE-M1（gate_commands 声明不可执行命令）
**改动**：
- check-gate.py P2 分支增加命令可执行性检查（机制层，WARNING 不阻断）

**P2.62: test-designer 量化断言 → P3 自检注入 + 失败归类提示**

**状态**：已实施
**来源**：T075 复盘 EXEC-1（手写魔数断言与测试数据矛盾）
**改动**：
- dispatch-prompt.md 新增 P3 派发追加块（强制自检步骤，机械注入每次 P3 派发）
- agate-render-dispatch-prompt.py 新增 P3 case 分支（接线）
- check-tdd-red.py 经典红灯分支输出断言矛盾提示（WARNING）

**P2.63: dispatch-context 修复轮增量模式**

**状态**：已实施
**来源**：T075 复盘 AGATE-M2（dispatch-context 维护负担）
**改动**：
- dispatch-prompt.md 新增修复轮派发追加块（主 Agent 模板：引用上轮 + 只写增量）

**P2.64: phase 时机统一 + P3 gate 分离 + gitignore + P2 正则**

**状态**：已实施
**来源**：T085 复盘（--no-verify 8 次）
**改动**：
- 统一 phase 更新时机：state + 产出同一 commit（7 个卡片 + state-machine.md + git-integration.md）
- 删除 check-state-transition.py 检查 3（pre-phase-change commit gate）——与模式 B 冲突，产出存在性由 check-gate.py 检查
- check-gate.py P3 从 exec check-tdd-red.py 改为文件存在性检查（秒级，hook 不超时）
- hook 永远自己跑 check-gate.py（写真实 .gate-result.json，不可伪造）
- CI backstop P3 时额外跑 check-tdd-red.py 兜底红灯（插入在 .gate-result.json 检查之前，--no-verify 场景仍执行）
- install-hook.py 检测 .gitignore 中 .state.yaml 忽略并提醒
- P2 候选方案正则支持 ####（2-4 个 #）

**P2.65: 审计 6 短路修复**

**状态**：已实施
**来源**：v0.28.0 独立实施评审（review-20260803-1659.md）
**改动**：
- check-p6-provenance.py agent 字段检查的 exit 2 改为 WARNING_FOUND 变量，不再短路审计 6
- 删除伪"v2 向后兼容"注释
- 新增 PV.28 测试（agent 缺失 + evidence 矛盾 → exit 1）

### 不修理由

| 问题 | 理由 |
|------|------|
| P6 直接改代码（P-EXEC-1） | gate 正确拦截，执行纪律问题不需脚本改 |
| 并行任务 commit 污染（P-EXEC-2） | 已改串行，`git add -A` → `git add <path>` 是通用纪律 |
| CSS overflow 规范盲区（P-TECH-1） | 项目侧技术知识，不是 agate 问题 |
| E2E 测试数据 bug（P-TECH-2） | 项目侧测试质量问题 |
| BDD 精确断言绑定方案（P-TECH-3） | P1 analyst 职责，不是 agate 问题 |

---

## 6. 待论证的改进

| 改进 | 内容 | 状态 |
|------|------|------|
| P6 总结行格式规范 | P6 卡片/check-p6-format.py 已显式化"行首 `- PASS`/`- FAIL` 只用于 BDD 条目"。check-p6-format.py check+fix 模式都检测总结行并自动修正为 `**Summary**` 格式。F11/F12 测试 | 已实施（T078 复盘） |
| check-tdd-red.py 内部 timeout | agate_common.py run_test_with_formatter 加 120s timeout（AGATE_TDD_TIMEOUT 可覆盖）。exit 124 → judge_result 视为红灯可推进（return 0）。macOS 兼容（command -v timeout 检测）。TDD.TIMEOUT 测试 | 已实施（T078 复盘） |
| P0 卡片 hardening 审计提示 | P0-orchestrator.md 加"hardening/refactor 类任务建议含代码审计"提示（非门槛） | 已实施（T078 复盘） |
| evidence 类型检查 | check-p6-evidence.py: ui_affected=true 时 evidence 不能全是 .md/.txt（防源码分析充数）。E.15/E.16/E.17 测试 | 已实施 |
| office-hours 角色清理 | 删除角色文件 + 清理 9 处引用 + 六问内化到 P0 卡片作为自检清单 | 已实施 |
| Issue #002 | self-gate 递归触发缺乏终止机制 | 待设计 |
| Task 派生机制 | P1/P2 声明 subtasks + agate-create-subtask.sh 自动生成 P0-brief 骨架 + active-tasks.md 依赖列真正使用。subtask 编号不预分配（subagent 声明时只写 name+reason+depends_on，主 Agent 创建时分配实际编号）。plan 需完善：BDD 提取范围、依赖列填充时机、subtask 间状态可见性 | 待论证（`archived/docs-2026-08/plans/agate-task-derivation-20260804.md`） |
| **T080 复盘 — gate 格式契约透明化** | verifier/consistency-reviewer/dispatch-context 三个文件追加精确正则模板。verifier 知道 PASS/FAIL 行、vision YAML 结构、引用括号格式；consistency-reviewer 知道 DESIGN_GAP 行首格式；dispatch-context 约束节避免行首 PASS/FAIL | 已实施 |
| **T080 复盘 — P7 DESIGN_GAP_REVIEWED 行首格式** | 含在 gate 格式契约透明化中（consistency-reviewer 角色文件） | 已实施 |
| **T080 复盘 — vision YAML 结构模板缺失** | 含在 gate 格式契约透明化中（verifier 角色文件） | 已实施 |
| **T080 复盘 — dispatch-context 约束节行首 PASS/FAIL 误匹配** | 含在 gate 格式契约透明化中（dispatch-context 模板） | 已实施 |
| **T080 复盘 — known-failures.md 语义边界** | known-failures-template.md + P5 卡片追加"只登预存失败"说明 | 已实施 |
| **T080 复盘 — P1 基线变更保护** | P1-requirements.md 末尾追加 P1 基线保护说明（[BASELINE_CHANGE: 理由] + 主 Agent 显式批准）。P4-implementation.md 常见错误节追加提醒 | 已实施 |
| **T080 复盘 — P8 bump + CHANGELOG 绑定** | P8-release.md L12 改为"bump-version + CHANGELOG 更新 → 同一 commit + tag" | 已实施 |
| **T080 复盘 — P2 选择器契约提示** | P2-design.md 追加 UI 测试选择器契约提示（稳定测试标识清单） | 已实施 |
| **T080 复盘 — P1 review 跨条 BDD 一致性** | requirements-review.md 检查清单追加"BDD 跨条一致性"维度（Then 矛盾 + 保护优先级 + 环境约束） | 已实施 |
| **T080 复盘 — P2 review UI 组件完整性** | plan-design-review.md 追加"组件完整性"评分维度（spec 每个 UI 组件有完整 input/output） | 已实施 |
| **T080 复盘 — NEED_CONFIRM 分级（v0.30.2 重命名为 [SUGGEST:]）** | P1-requirements.md 追加分级格式（[NEED_CONFIRM] 阻塞 vs [SUGGEST:] 不阻塞 vs [NO_NEED_CONFIRM] 负向）。check-gate.py P1 检测逻辑：阻塞 exit 1、倾向 WARNING 不阻塞、旧标记残留 typo 兜底。G_SUGGEST.1-4 测试 | 已实施 |
| **T080 复盘 — P6 格式修正 gate 维护例外** | 铁律"主 Agent 不亲自产出"没定义格式修正边界。需声明 gate 维护例外 | 待论证 |
| **T080 复盘 — P6 verifier 断点续做** | 单次 dispatch 承载过重，崩溃即丢失。需分阶段落盘或分批验收 | 待论证 |
| **T080 复盘 — retry 预算分类** | 跨阶段问题（P1 BDD 矛盾）共用 P4 retry 预算不合理。需区分本阶段 vs 上游遗留 | 待论证 |

### 不修理由

| 改进 | 理由 |
|------|------|
| 能力使用检查提醒（P5/P6 派发 prompt 加能力对账） | agate 不应绑定特定能力工具（vision-engine/playwright-cdp 等是环境侧专用能力）。P6 gate 检查客观证据已够。能力匹配是架构级设计，不属于小改进范围 |
| 诊断优先提醒（retries≥2 时 hook 提醒跑诊断命令） | retries≥2 已触发 check-retrospective.py 提醒。再加一层重复。agent 怎么诊断是角色文件职责，不是 hook 的 |
| verifier 工具困难处理（角色文件补"遇到工具困难标 NEED_CONFIRM，不退源码"） | P6 卡片 L96 已明确"不退源码"纪律。角色文件再加是重复措辞 |
