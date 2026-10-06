# 复盘模板（retrospective-template.md）

> 每份 agate 任务复盘基于本模板撰写，产出路径固定为 `tasks/{Txxx}/retrospective.md`。
> 迁移说明：本文件原为 `docs/reviews/` 下的 `postmortem-template.md`（只有机制触发核对清单），
> TAG0015 迁移进协议本体并补齐正文结构（事实基线/做得好的/发现的问题/改进措施）+
> 内容价值标准 + 归因分层 + 产出流向约定 + frontmatter 机器字段 + 「## agate 反馈」节。

## 填写前必读：内容价值标准

> 复盘不是流水账（不要复述 P1-P8 过程），也不是自我表扬（不要只写做得好的）。
> 值得写的内容只有三类，撰写前先对照这三条判断"这段话是否值得写"：

1. **机制缺口**——agate 协议/脚本/模板本身没有定义或覆盖到的情况，导致问题发生
2. **可复用模式**——本次任务中验证有效、值得固化进协议或项目资产的做法
3. **归因到可行动层面的问题**——不是笼统吐槽，而是能落到具体文件/字段/gate 的改进点

不满足以上三条任一条的内容（如单纯复述执行步骤）不建议写入复盘正文。

## frontmatter 样例

复盘文档 `tasks/{Txxx}/retrospective.md` 的文件头须含以下机器可解析字段（供 `agate-feedback.py`
提取，AG0021 依赖）：

```yaml
---
task_id: TAG0001
mechanism_issues: []      # list：本次复盘归因为"机制缺口"的问题条目（简述）
execution_issues: []      # list：本次复盘归因为"执行错误"的问题条目（简述）
feedback_ready: false     # bool：为 true 时下方「## agate 反馈」节内容视为已就绪，可供 agate-feedback.py 提取
---
```

## 正文结构

### 一、事实基线

> 客观数据：任务耗时、重试次数、gate 失败次数、涉及文件数等可核实的事实，不含主观判断。

（填写：本次任务的客观事实数据）

### 二、做得好的 + 可复用模式

> 每条可复用项标注两类去向之一：
> ①**回馈 agate**（该做法值得沉淀进 agate 协议本体，关联下方「## agate 反馈」节）
> ②**项目资产沉淀**（该做法是项目特定的，注明具体沉淀位置，如 `Makefile`/`scripts/` 或
> `agents.md`/`project.md`）

**填写引导语（强制追问，撰写本节前必须先回答）**：
本次产生的临时命令/脚本/经验，哪些该沉淀为项目固定资产？沉淀到哪？

（填写：做得好的做法 + 去向标注，示例：
`- 用 xxx 脚本一次性批量验证 → 去向：项目资产沉淀，位置：scripts/xxx.sh`）

### 三、发现的问题

> 每条问题条目**强制**标注 `归因层面: 机制缺口 / 执行错误` 字段（二选一，二值语义，
> **不允许留空，不允许标注"两者都是"**）：
> - `机制缺口`：agate 协议/脚本/模板没有定义或覆盖到，导致问题发生（应修协议）
> - `执行错误`：协议本身有定义，但执行时没有遵守（应修纪律，不是修协议）

**填写示例**：
```
- 问题：P4 实现时误改了测试断言而非实现代码
  归因层面: 执行错误
  说明：implementer.md 已明确"让测试变绿不改测试"，本次是未遵守既有规则
```

（填写：发现的问题逐条列出，每条含"归因层面"字段）

### 四、改进措施

> 措施须落到具体文件/字段/gate，不是空泛的"以后注意"。

（填写：针对上述问题的具体改进措施，标明落点文件）

## 技术债登记核对清单

> 每份 agate 任务复盘必须附此清单。
> 用途：强制核对 agate 的核心机制在本任务中是否被正确触发，防止遗漏。
> 使用方式：复制下方的表格到复盘文件末尾，逐条填写。

### 填写说明

- **应该触发？**：本任务中是否出现了该机制的触发条件（如：subagent 失败了→retry 应该触发；方案范围变化了→SCOPE+ 应该触发）
- **实际触发？**：主 Agent 是否按协议执行了该机制（✅ 执行了 / ❌ 没执行 / — 没有触发条件）
- **未触发后果**：如果应该触发但没触发，导致了什么后果
- **原因**：未触发的原因是执行错误还是机制缺口

"应该触发 = 是" 且 "实际触发 = ❌" = 执行错误（不是机制缺口）。

### 核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是/否/— | ✅/❌/— | | |
| PAUSED | 是/否/— | ✅/❌/— | | |
| PROD_TOUCHED | 是/否/— | ✅/❌/— | | |
| SCOPE+ | 是/否/— | ✅/❌/— | | |
| SCOPE_RESOLVED | 是/否/— | ✅/❌/— | | |
| DESIGN_GAP | 是/否/— | ✅/❌/— | | |
| DESIGN_GAP_REVIEWED | 是/否/— | ✅/❌/— | | |
| NEED_CONFIRM | 是/否/— | ✅/❌/— | | |
| CAPABILITY_GAP | 是/否/— | ✅/❌/— | | |
| gate 验证（每阶段） | 是/否/— | ✅/❌/— | | |
| 阶段产出文件（每阶段） | 是/否/— | ✅/❌/— | | |
| .state.yaml phase 同步 | 是/否/— | ✅/❌/— | | |
| 裁剪条件 + override | 是/否/— | ✅/❌/— | | |
| capability_requirements | 是/否/— | ✅/❌/— | | |
| 分阶段落盘（防 subagent 空返回） | 是/否/— | ✅/❌/— | | |
| phase-产出一致性 | 是/否/— | ✅/❌/— | | |
| P6 evidence（含截图 + 引用 + vision YAML） | 是/否/— | ✅/❌/— | | |
| P2 候选方案 + 权衡（≥2） | 是/否/— | ✅/❌/— | | |
| P8 internal_only_reason | 是/否/— | ✅/❌/— | | |
| dispatch-context.md | 是/否/— | ✅/❌/— | | |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是/否/— | ✅/❌/— | | |
| CI backstop | 是/否/— | ✅/❌/— | | |
| **技术债登记** | 是/否/— | ✅/❌/— | 标记为"是"时，本列必须填写具体 DEBT 编号或 roadmap RM 编号，**不允许留空或写"待定"** | |

### 机制说明

| 机制 | 触发条件 | 协议位置 |
|------|---------|----------|
| retry 记录 | 任何阶段门槛失败（含 subagent 空返回、gate 不通过） | dispatch-protocol.md「重试与上限」 |
| PAUSED | retry 超限、跨 ≥2 阶段回退、不可逆操作需确认 | state-machine.md「转移规则」 |
| PROD_TOUCHED | 开发/测试过程中意外接触生产环境 | dispatch-protocol.md「[PROD_TOUCHED] 标记说明」 |
| SCOPE+ | 任何阶段发现 P1 未覆盖的新隐含需求 | WORKFLOW.md「[SCOPE+]」 |
| SCOPE_RESOLVED | SCOPE+ 处理后追加的确认标记 | check-scope-resolved.py |
| DESIGN_GAP | P4 implementer 发现 P2 设计有歧义/缺口而自主决策 | implementer.md「[DESIGN_GAP] 偏差声明」 |
| DESIGN_GAP_REVIEWED | 主 Agent 审查 DESIGN_GAP 后追加的确认标记 | check-gate.py P7 配对检查 |
| NEED_CONFIRM | 实跑结果与 BDD 条件有偏差但不确定是 bug 还是需求理解问题 | verifier.md「何时标 [NEED_CONFIRM]」 |
| CAPABILITY_GAP | 任务需要的能力当前环境无法满足且无补充路径 | task-files.md「能力三态」 |
| gate 验证 | 每个阶段转移前，主 Agent 亲自跑 gate 命令 | state-machine.md「主 Agent 的单步执行」 |
| 阶段产出文件 | 每个阶段产出对应 P{n}-*.md（不裁剪时） | task-files.md |
| .state.yaml phase 同步 | 阶段转移时同步更新 .state.yaml phase 字段 | state-machine.md |
| 裁剪条件 + override | P1 声明裁剪时满足对应阶段的裁剪条件 | check-pruning.py |
| capability_requirements | P1 识别任务需要的特殊能力并评估当前环境 | analyst.md「能力需求声明」 |
| 分阶段落盘 | subagent 派发时默认启用，防空返回 | dispatch-protocol.md「分阶段落盘」 |
| phase-产出一致性 | 暂存的 P{n}-*.md 产出与 .state.yaml phase 匹配 | pre-commit-gate.sh WARNING |
| P6 evidence | P6 验收的证据文件（截图/日志/JSON）含运行时数据 | check-p6-evidence.py |
| P2 候选方案 | P2 至少 2 个候选方案 + 权衡 + 选择理由（design_trivial/follows_existing_pattern 除外） | check-gate.py P2 form check |
| P8 internal_only_reason | 裁剪 P8 时声明 internal_only + 理由字段 | check-pruning.py |
| dispatch-context.md | 主 Agent 派发前查证的客观信息落盘 | dispatch-protocol.md |
| pre-commit hook | git commit 时自动跑 gate / 状态转移 / 裁剪检查 | pre-commit-gate.sh |
| CI 兜底 | push 后重跑 gate 判定，捕获 --no-verify 绕过 | agate-ci-verify.py |
| 技术债登记 | 复盘/评审发现缺陷或缺口（影响验收真实性 或 让未来变更更贵）→ 登记 DEBT（tech-debt-template，source: review/retrospective）或 roadmap backlog，二选一注明去向。**未登记 = 机制缺口**（DEBT0001 教训：复盘发现 CHECK 10 缺口但零登记） | tech-debt-template.md + check-debt.py |

## agate 反馈

> 当 `feedback_ready: true` 时填写本节：只列出归因到 agate 机制/执行层面的条目，
> 不涉及项目敏感信息（项目名/绝对路径等由 `agate-feedback.py` 做进一步脱敏，
> 但撰写时本身也应避免带入项目特定信息）。

（填写：归因到 agate 机制/执行层面、值得反馈给 agate 项目组的条目）
