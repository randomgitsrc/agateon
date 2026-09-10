# agate 自身变更的 gate（self-gate）

> agate 改自己的协议文档或脚本时，必须走本流程。
> 和项目侧 agate 流程对等：项目用 check-gate.py + P2 评审；agate 自身用 `check-protocol-consistency.py`
> 的结构 CHECK 全集（不写死上界，当前 CHECK 1-15，其中 CHECK 9 是协议-脚本结构对齐）+ LLM 语义审查。

## 强制力边界

**本机制目前有 commit-msg hook 辅助提醒**：暂存区含 self-gate 触发文件时，commit message 须含 `self-gate-review:` 路径（或 `self-gate-skip:` 理由），否则 WARNING。

但 WARNING 不拦截——遵循 hook 鲁棒性优先原则。主 Agent 仍可忽略 WARNING 直接 commit。真正的强制力依赖主 Agent 自觉 + CI 兜底（gate-backstop job 已接入，push 后重跑 gate；self-gate 语义审查的强制力仍依赖主 Agent 自觉）。详见 issue #002。

## 触发条件

以下任一文件有改动并准备 commit 时：
  - `agate/scripts/*.sh`（现仅 3 个 hook 薄壳：pre-commit-gate.sh / commit-msg-self-gate.sh / pre-push-gate.sh；保留防御性列举）
  - `agate/scripts/*.py`
- `agate/*.md`（协议文档：WORKFLOW.md / state-machine.md / dispatch-protocol.md 等）
- `agate/**/*.md`（角色文件、模板文件等子目录）
- `agate/rules/*.yaml`（数据面权威源：phases.yaml / dispatch.yaml / roles.yaml / dispatch-tiers.yaml；CHECK 15 专扫）
- `SELF-GATE.md`（本文件自身的改动也走 self-gate）

## 检查清单

1. **跑 check-protocol-consistency.py** — 确认结构 CHECK 全集（当前 1-15）无 ERROR
2. **派发 protocol-alignment-review subagent** — 语义对齐审查（派发模板见下文，角色定义见 `agate/assets/review-roles/protocol-alignment-review.md`）
3. **读审查报告** — MISALIGNED 必须修复，NEEDS_HUMAN_REVIEW 需附 `[HUMAN_CONFIRMED: ...]` 标记
4. **跑全量 pytest** — 确认无退化（`python3 -m pytest agate/tests/`）
5. **如果改了 gate 逻辑** — 确认下游项目（如 PeekView）的 gate 仍能跑通

## Layer 0：CHECK 9（脚本结构兜底，自动）

`check-protocol-consistency.py` 的 CHECK 9 扫描协议文档声明的规则，核对对应脚本是否含相关关键词。

```bash
# 手动跑
python3 agate/scripts/check-protocol-consistency.py

# CI 自动跑（每次 push / PR）
```

**局限**：关键词存在 ≠ 语义一致。三类假阳性：
1. 值不匹配（文档说 `=2`，脚本写 `=3`）
2. 语义降级（文档说"强制"，脚本只 `echo 警告`）
3. 关键词在错误位置（在 echo 消息文本里，不在检查逻辑里）

语义一致性由 Layer 1 保证。

## Layer 1：LLM 语义审查（手动派发）

### 文件约定（留痕文件 vs 成果文件）

| 类型 | 文件名 | 用途 | 内容 | 生命周期 |
|------|--------|------|------|---------|
| 留痕文件 | `docs/reviews/agate-alignment-{date}-{task_id}-{NN}.progress.md` | 空返回诊断 | 原始执行痕迹，逐条追加，不整理不格式化 | subagent 返回后主 Agent 检查；成功可删，失败保留待查 |
| 成果文件 | `docs/reviews/agate-alignment-review-{date}-{task_id}.md` | 最终交付物 | 结构化审查报告（A1-A7）| 保留，闭环依据 |

**关键规则**：
- 留痕文件和成果文件是**两个不同的文件**
- 留痕文件只写原始痕迹（"读了 X 文件，发现 Y"），**不做内容整理、不格式化、不写结论汇总**
- 成果文件是最终报告，subagent 审查完所有文件后**一次性写出**（或覆盖重写）
- 每个 subagent 调用有**独立的留痕文件**（`{NN}` 序号区分），避免多次调用追加同一文件导致内容重复
- **留痕文件如果已存在，subagent 开始前先删除**（`rm -f`）——确保每次调用从空文件开始，重试不会累积重复内容
- 全量审查如果分批派发，每批用自己的留痕文件（如 `agate-alignment-2026-07-01-TAG0017-01.progress.md`、`-02.progress.md`）

### 两种审查模式

| 模式 | 触发 | 输入 | 适用场景 |
|------|------|------|---------|
| 变更触发 | 改了 agate 协议/脚本准备 commit | 本次 diff + 受影响文件 | 日常变更审查 |
| 全量审查 | 维护者主动发起 | 全部协议文件 + 全部脚本 | 历史偏差扫描、定期审计 |

### 变更触发模式 — 派发模板

```
你是 agate 协议-脚本对齐审查员。

## 你的角色定义
读取并遵循：agate/assets/review-roles/protocol-alignment-review.md

## 第一步：意图分析
本次变更的意图是什么？用 1-2 句话说清楚"为什么改"，不是"改了什么"。
意图比 diff 更重要——diff 只是意图的物理表现。

## 第二步：反向传播——列出应被影响的文件
基于意图，主动推断"这次改动应该传播到哪些文件"。不只列 git diff 里的文件，还要列出：
- 衍生改动（一致性连锁）：改了 X 应该跟着改 Y
- 文档传播（应被影响但 git diff 里没出现的文件）：比如改了 state-machine.md 的 MAX_RETRY 表，orchestrator-template.md / WORKFLOW.md / dispatch-protocol.md 的描述是否需要同步？
- 角色文件 / 模板文件：脚本行为变了，角色文件提示词是否过时？

参考角色文件的"反向传播的常见路径"表作为推理起点，但不要局限于此——根据本次意图自行判断。

输出格式：
- 应被影响的文件列表（按优先级排序）
- 每个文件被影响的理由

## 第三步：实际审查范围
读以下文件全文：
- git diff 涉及的变更文件（diff 直接列出的）
- 第二步列出的应被影响文件
- 权威规则源：
  - agate/state-machine.md（裁剪表、重试表、转移规则）
  - agate/dispatch-protocol.md（gate 表、门槛表）
  - agate/WORKFLOW.md（风险矩阵、阶段总览）

## 配套文件提示
- 如果变更涉及 gate 检查逻辑（check-gate.py），同时读对应的角色文件
  （implementer.md / architect.md / verifier.md）
- 如果变更涉及文件格式/字段（check-pruning.py / check-state-yaml.py），
  同时读 assets/templates/task-files.md
- 如果变更涉及 P6 证据格式，同时读 verifier.md 和 vision-analyst.md

## 审查清单
逐项检查 A1-A7（见角色文件），A3 和 A5 必须包含反向传播的检查：
- A1 文档→脚本对齐
- A2 脚本→文档对齐
- A3 一致性连锁 + 反向传播：列出应被影响但 diff 未列出的文件，逐一验证
- A4 测试覆盖
- A5 下游影响 + 文档传播：CHANGELOG 是否标注？文档是否同步？
- A6 锚点表覆盖
- A7 设计原则一致性：变更是否符合已记录的 ADR（agate/adr.md）？逐条检查相关 ADR。如发现未记录的架构决策，建议补充新 ADR

若发现 A1/A2/A3 疑似不一致，先按角色文件"DESIGN_GAP 优先核查"原则查
`{AGATE_WORKSPACE}/tasks/{Txxx}/P4-implementation.md`/`P7-consistency.md` 是否已有
`REVIEWED-ACCEPTED` 记录，避免把已知偏离误判为新 MISALIGNED。

每项输出：
- 审查项编号
- 文档说了什么（引用原文 + 行号）
- 脚本/其他文件实现了什么（引用代码 + 行号）
- 结论：ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW
- 若 MISALIGNED：具体差异描述 + 建议修复方向

## 分阶段落盘（留痕文件，防空返回）
留痕文件：docs/reviews/agate-alignment-{date}-{task_id}-{NN}.progress.md
开始前先删除留痕文件（如已存在）：rm -f {留痕文件路径}
每读完一个文件，立即用 bash 追加一行（不要整理、不格式化）：
  echo "- [文件名] 关键逻辑摘要" >> {留痕文件路径}
每完成一个对比判断或反向传播检查项，立即追加（原始记录，不整理）：
  echo "- A{n}/{反向传播}: 文档说X / 实际是Y / 结论" >> {留痕文件路径}
不要在留痕文件里做内容整理——那是成果文件的事。
读一个写一个，判断一条写一条。

## 产出（成果文件，最终交付物）
docs/reviews/agate-alignment-review-{date}-{task_id}.md
审查完所有文件后，把结构化报告写入成果文件（覆盖写，不是追加）。
成果文件含 frontmatter + A1-A7 结论汇总表（含反向传播检查）+ 逐项审查详情。
⚠️ 路径是硬约束：必须用 Write 工具写入此路径，不得将产出文件写入 /tmp、工作区根目录或其他路径。
```

### 全量审查模式 — 派发模板

全量审查不带 diff，不给预设结论——给 subagent 全部文件，让它独立发现偏差。

如果文件太多（>8 个），分批派发，每批用自己的留痕文件序号。分批时注意：**每批覆盖的文件应包含相关的协议文档和对应脚本**（不能只审脚本不审文档），否则反向传播会断开。

```
你是 agate 协议-脚本对齐审查员。

## 你的角色定义
读取并遵循：agate/assets/review-roles/protocol-alignment-review.md

## 审查任务
全量审查 agate 所有协议文档和所有 gate 脚本的语义对齐。
不要假设哪里有偏差——自己读文件，自己找。

## 第一步：意图无关，但需要反向传播
虽然没有"意图"，但发现偏差时必须做反向传播——列出"该偏差应该影响但未影响的其他文件"，逐一验证。

## 审查范围
{本次批次要审查的文件列表}

## 审查清单
逐项检查 A1-A7（见角色文件）。对每个审查项：
- 文档说了什么（引用原文 + 行号）
- 脚本实现了什么（引用代码 + 行号）
- 结论：ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW
- 若 MISALIGNED：具体差异描述 + 建议修复方向 + **反向传播：列出该偏差应该影响的其他文件**

若发现 A1/A2/A3 疑似不一致，先按角色文件"DESIGN_GAP 优先核查"原则查
`{AGATE_WORKSPACE}/tasks/{Txxx}/P4-implementation.md`/`P7-consistency.md` 是否已有
`REVIEWED-ACCEPTED` 记录，避免把已知偏离误判为新 MISALIGNED。

## 分阶段落盘（留痕文件，防空返回）
留痕文件：docs/reviews/agate-alignment-{date}-{task_id}-{NN}.progress.md
开始前先删除留痕文件（如已存在）：rm -f {留痕文件路径}
每读完一个文件，立即用 bash 追加一行（不要整理、不格式化）：
  echo "- [文件名] 关键逻辑摘要" >> {留痕文件路径}
每完成一个对比判断或反向传播检查项，立即追加（原始记录，不整理）：
  echo "- A{n}/{反向传播}: 文档说X / 实际是Y / 结论" >> {留痕文件路径}
不要在留痕文件里做内容整理——那是成果文件的事。
读一个写一个，判断一条写一条。

## 产出（成果文件，最终交付物）
docs/reviews/agate-alignment-review-{date}-{task_id}.md
审查完所有文件后，把结构化报告写入成果文件（覆盖写，不是追加）。
如果成果文件已存在（前一批写的），追加本次批次的审查结果到已有文件。
⚠️ 路径是硬约束：必须用 Write 工具写入此路径，不得将产出文件写入 /tmp、工作区根目录或其他路径。
```

### 闭环规则

| 结论 | 处理 |
|------|------|
| ALIGNED | 通过，可 commit |
| MISALIGNED | **必须修复**——修脚本或修文档，修完重审 |
| NEEDS_HUMAN_REVIEW | 附 `[HUMAN_CONFIRMED: 日期 确认：理由]` 标记后可 commit。未确认的等同于 MISALIGNED |

## 递归适用与终止条件

本机制自身的实施也走 self-gate。任何针对 agate 的变更 plan，实施时都必须走本流程。

### 递归终止

审查报告结论汇总表里所有项都是 ALIGNED 或 NEEDS_HUMAN_REVIEW（附 `[HUMAN_CONFIRMED: ...]`）→ **本轮终止**。

如果审查发现 MISALIGNED → 必须修复 → 修复后重审 → 直到全 ALIGNED。这是自然终止，不需要额外标记。

### 未实现时的等价检查

如果 self-gate 尚未实现（如还在 plan 阶段），实施者至少手动执行等价检查：
1. 跑现有 check-protocol-consistency.py
2. 人工逐项核对"文档描述的规则 vs 脚本实现"是否一致（对照 A1-A7）
3. 跑全量 pytest
