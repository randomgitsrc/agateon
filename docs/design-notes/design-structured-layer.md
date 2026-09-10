# 协议结构化层设计（RM-AG0022：phases.yaml / dispatch.yaml / roles.yaml）

> 状态：**已落地（TAG0021，v0.60.0，RM-AG0022）**
> 目标：把 agent 消费的协议规则从 8000+ 行自由文本 markdown 抽成**机器可读的结构化定义**，解决"agent 读 8000+ 行 md 理解规则"的摩擦，并让 gate 判定从"grep 文本"升级为"校验结构化数据"。

---

## 1. 问题定义

### 现状摩擦（TAG0014 复盘实证）
1. **规则散落**：同一规则（如 P2 门槛）在 WORKFLOW.md / dispatch-protocol.md / state-machine.md / phase-cards 多处表述，agent 需要交叉阅读才能拼出全貌（TAG0016 已做一轮去重，仍是文档层面收敛）
2. **解析靠 grep**：`check-gate.py`、`agate-read-gate-commands.py`、`check-pruning.py` 等 53 个脚本大量依赖对 markdown 的正则解析（如 `grep -cE '^(packages|domains|ui_affected|gate_commands):'`）——脆弱、易漂移（DEBT0010 就是 `_timeout_seconds` 键解析遗漏的真实教训）
3. **agent 上下文开销**：orchestrator 每轮要"读状态→查卡片→查规则"，跨文档查表成本高

### 设计目标
- **单一事实源（Single Source of Truth）**：结构化 YAML 是**可判定规则的权威源**；markdown 保留为**人类叙事层**（解释 why、示例、注意事项）
- **双向一致性 gate**：YAML 与 markdown 之间无漂移（机器校验，纳入 CI + pre-commit）
- **渐进披露升级**：phase-cards 保留，但其"门槛/产出/派发"字段改为**由 YAML 渲染**，杜绝手写漂移
- **脚本解析替换**：gate 脚本从"grep markdown"逐步迁移到"读 YAML"（阶段化，不一次性重写）

---

## 2. 总体架构

```
协议本体（agate/）
├── rules/*.yaml          ←【新增】结构化权威层（机器可判定规则）
│   ├── phases.yaml          阶段定义（P0-P8 + READY）
│   ├── dispatch.yaml        派发定义（模板字段、gate 表、五模式编排）
│   ├── roles.yaml           角色定义（双层角色 + 机械映射表）
│   └── schema/*.json        YAML 的 JSON Schema 校验器
├── *.md                   ← 人类叙事层（保留，解释 why / 示例 / 注意事项）
├── phase-cards/*.md       ← 保持，但门槛/产出/派发字段改为渲染产物（模板 + YAML 数据）
└── scripts/
    ├── check-structure-consistency.py   【新增】YAML↔markdown 双向一致性 gate
    ├── check-yaml-schema.py             【新增】YAML 合法性与 schema 校验
    └── （现有脚本逐步改用 YAML 数据源）
```

**关键决策**：YAML 为规则权威源，markdown 为叙事层。理由：
- 可判定规则（门槛命令、产出文件、状态转移、重试上限、角色映射）天然是数据，YAML 表达无歧义
- 叙事（设计意图、案例、教训）天然是文字，压缩进 YAML 会丢失可读性
- gate 校验"叙事不违反结构、结构不缺失叙事锚点"——双向防止漂移

---

## 3. Schema 设计（草案）

### 3.1 `phases.yaml`（阶段定义）

```yaml
schema_version: 1
phases:
  - id: P2
    name: 方案设计层
    exec_role: architect
    review_roles:            # 机械映射（role-system.md C8）
      - { role: plan-eng-review, trigger: "risk_level == high" }
      - { role: plan-design-review, trigger: "domains contains frontend" }
    outputs:
      - { file: P2-design.md, required: true }
      - { file: P2-review.md, required: true, status_field: status }
    gates:                   # 门槛（原 grep 规则结构化）
      - { check: "P2-review.md status == approved" }
      - { check: "P2-design.md has >=4 of [packages,domains,ui_affected,gate_commands]" }
      - { check: "P2-design.md matches tradeoff-anchor-regex" }
      - { check: "ui_affected: true -> P2-design.md contains UI设计节" }
    retry_cap: 2
    prune_rules:             # 裁剪规则（原 check-pruning.py 逻辑）
      - { condition: "design_trivial or follows_existing_pattern", allow: "simplify, not omit" }
    gate_commands:           # P2 声明的命令（P5 消费）
      declared_in: P2-design.md
      parser: is_gate_meta_key   # 复用 agate_common.py 判据
  - id: P6
    ...
```

### 3.2 `roles.yaml`（角色定义）

```yaml
roles:
  execution:
    - { id: analyst, phase: P1, file: assets/execution-roles/analyst.md }
    - { id: architect, phase: [P2, P7], file: assets/execution-roles/architect.md }
  review:
    - { id: plan-eng-review, insert_after: P2, mandatory_for: [high], file: assets/review-roles/plan-eng-review.md, status_mapping: { approved: approved, rejected: rejected } }
    - { id: judge, insert_after: P6.5, mandatory: true, ... }   # 预留（独立 judge 提案）
```

### 3.3 `dispatch.yaml`（派发定义）

```yaml
dispatch:
  rules:                    # 派发三条铁律（结构化）
    - { rule: "use task tool", verb: dispatch }
    - { rule: "pass paths only, not content" }
    - { rule: "subagent returns path + one-line summary" }
  templates:
    prompt: assets/templates/dispatch-prompt.md     # 叙事模板（渲染骨架）
    context_fields: [目标, 约束, 上游关联, 输入文件]
  orchestration:            # 五模式编排（dispatch-protocol.md 结构化）
    modes: [single, parallel, pipeline, understand-then-split, hybrid]
    parallel_rules: [...]
  gate_table:               # 各阶段 gate 表（原 markdown 表结构化）
    P3: { script: check-tdd-red.py, exit: 0 }
    P5: { script: "gate_commands.P5", exit: 0, failed: 0 }
```

---

## 4. 一致性 gate 设计（`check-structure-consistency.py`）

双向校验，仿照现有 `check-protocol-consistency.py` 的 CHECK 编号风格：

| CHECK | 方向 | 判定 |
|-------|------|------|
| S-1 | YAML → md | phases.yaml 中每个 phase 在 WORKFLOW.md 总览表有对应行，字段（角色/产出/门槛摘要）一致 |
| S-2 | md → YAML | WORKFLOW.md 总览表的每个 phase 行在 phases.yaml 中有定义（防"文档新增阶段忘入 YAML"）|
| S-3 | YAML → cards | phase-cards/P{N}-*.md 的门槛/产出节与 phases.yaml 一致（卡片改为渲染后不再漂移）|
| S-4 | YAML → scripts | gate 脚本读取的字段（如 gate_commands 解析器）与 phases.yaml 声明一致 |
| S-5 | schema | 全部 YAML 通过 JSON Schema 校验（`check-yaml-schema.py`）|
| S-6 | 引用完整性 | YAML 中引用的文件路径（角色文件/模板/脚本）真实存在 |

失败语义：S-1/S-2 漂移 → ERROR（exit 1 阻断）；S-5/S-6 → ERROR；沿用 `--strict-errors-only` 模式（TAG0017 遗产）。

---

## 5. 脚本迁移路径（渐进式，不重写）

| 阶段 | 内容 | 风险 |
|------|------|------|
| **M0（数据层就位）** | 新增 rules/*.yaml + schema + 两个新脚本；**只加不改**：现有 53 脚本继续 grep md | 零（纯增量）|
| **M1（双跑对账）** | 选 3-5 个高频脚本（agate-read-gate-commands / check-pruning / check-gate）实现"读 YAML，与 grep 结果对账，不一致报警"| 低（对账期只告警不阻断）|
| **M2（切换权威源）** | 对账稳定后，脚本改用 YAML，grep 逻辑删除；一致性 gate 提升为阻断 | 中（需回归 + dogfooding 验证）|
| **M3（卡片渲染化）** | phase-cards 从 YAML 渲染（模板 + 数据），`agate-inject-card.py` 改造 | 中（TAG0016 教训：卡片注入工具必须用稳定版）|

**约束（对齐 AGENTS.md 工具纪律）**：M0-M3 全程保持"测试平台无关"原则；每个阶段先写失败测试再改脚本（TDD）；`count-tests.sh` 用例数不漂移。

---

## 6. 与现有机制的关系

| 现有机制 | 关系 |
|----------|------|
| `check-protocol-consistency.py` | 并存：它查"文档间引用/文件存在性"，新 gate 查"YAML↔md 语义一致性"；可考虑合并 CHECK 编号空间 |
| `phase-cards` 渐进披露 | 保留，渲染化升级；orchestrator 每轮仍只读一张卡 |
| `SELF-GATE.md` | 新增 `rules/*.yaml` 与两个脚本 → 自动进入 self-gate 触发面（改协议本体）|
| `UPGRADING.md` | v0.57+ 新增章节：M0 为纯增量，不破坏存量项目；M2 需说明脚本行为变化 |
| 独立 judge 提案 | 两者正交：judge 是验证机制，结构化层是数据层；judge 的 verdict schema 可直接进 phases.yaml 的 P6.5 定义 |

---

## 7. 落地节奏建议

1. **先做 M0 + S-1/S-2**（数据层 + 阶段/角色两张表）：覆盖"agent 读规则"摩擦的 60%，成本最低
2. **再补 dispatch.yaml**（M0 内）：覆盖派发摩擦
3. **M1 对账选 check-gate.py 先行**：它是主 Agent 每阶段必跑的总闸，收益最大
4. **TAG0018 dogfooding**：用"agate 自己跑一个任务"验证 agent 读 YAML 的体验提升，产出对比数据
5. **评审锚点**：按 adr.md 惯例新增 ADR（YAML 权威源决策记录）

---

## 8. 风险与对策

| 风险 | 对策 |
|------|------|
| 双份维护（md + YAML）漂移 | S-1~S-4 双向 gate 阻断 + CI 强制 |
| 一次性迁移爆炸 | M0-M3 渐进，每阶段独立可回退 |
| YAML 过深失去可读性 | schema 限制字段枚举；叙事一律留在 md；YAML 只承载可判定规则 |
| 工具链自举风险（用新 gate 判自己）| 沿用双工作区纪律：`~/.agate` 稳定版跑 gate，worktree 里改 |
