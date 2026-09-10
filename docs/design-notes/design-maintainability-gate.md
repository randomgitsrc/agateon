# 维护性反模式 gate 设计（从 Cursor thermo-nuclear review 提炼）

> 状态：**已落地（TAG0026，v0.65.0，RM-AG0046）** ｜ 原设计草案日期：2026-08-23 ｜ 来源：用户提供 Cursor `thermo-nuclear-code-quality-review` skill 后的 gate 化分析
> 定位：与 `design-independent-judge.md` / `design-agateon-portal.md` 同级的机制设计草案，**非当前立项**。
> 一句话：**把"代码质量审查"从 LLM 主观品味，提炼成"模式层语义 + 检测器层实现"的可判定 gate。**

---

## 1. 背景：为什么分析这个 skill

Cursor 团队的 `thermo-nuclear-code-quality-review` skill 是一份高质量的 LLM 审查提示词，核心是"code judo"（重构让复杂度消失，而非重排复杂度），带明确的 Approval Bar 与 presumptive blockers。

**但它有致命缺陷**：7 条"Non-Negotiable Standards"里，判定几乎全部压在 LLM 主观品味上，没有机械 gate、没有证据账本、没有验证闭环——审查者可以"诚实但肤浅"，也可以"自信但错误"，skill 本身无法区分。

**这恰好撞上 agate 的实证教训**（TAG0018）：4 场 LLM 评审净收益 ≈ 0，机械 gate 全胜。根因是"评审者与作者同信任链、同上下文" + "主观品味无法稳定执行"。

**本文做 gate 化分析**：把它可判定的部分提炼成"维护性反模式 gate"，纯品味部分留给 LLM 当心法（不参与判定）。

---

## 2. 核心洞察：模式层 / 检测器层分离

Cursor skill 之所以退化成纯 LLM 判断，是因为它**把两层混在了一句话里**：

> "God File 是反模式"（模式层，可定义）
> + "怎么判断一个文件是不是 God File"（检测器层，可机械实现）

agate 的 gate 化，本质就是**把这两层拆开**：

```
模式层（协议定义，语言无关、技术栈无关）     检测器层（各平台/语言自行实现）
──────────────────────────────────       ─────────────────────────────
"PR 不得把文件从 <N 行跨越到 >N 行"         awk 脚本 / 任意语言行数检查
"diff 新增条件分支不得散落在非主体流程"      git diff + 解析 / AST 分析 / 任意工具
"不得引入与既有 canonical 逻辑重复的实现"    pylint R0801 / jscpd / 任意工具
"类型/契约边界不得因 diff 变模糊"           mypy / eslint no-explicit-any / 任意工具
```

**agate 作为协议，只定义左列（反模式语义 + 判定标准），右列是各项目的实现自由。** 这正是 agate 已有的设计：`gate_commands` 只声明"必须有检查 X"，从不规定"用哪个工具检查 X"；`platform-notes.md` 干的就是"把协议语义映射到各平台"。

---

## 3. Gate 化四级（G0–G3）

| 级 | 定义 | 判定权 |
|----|------|--------|
| **G0** | 纯机械，一行脚本/lint 规则，exit code | 完全在 gate |
| **G1** | 需先建立清单/基线，之后机械判定 | 在 gate（清单人工维护一次） |
| **G2** | 机械算信号 + LLM 解释，判定权在 gate | gate 算分，LLM 只解释 |
| **G3** | 纯主观品味，不可 gate 化 | 只当 LLM 心法，不参与判定 |

---

## 4. 反模式映射表（7 条规则 → 反模式 → 协议语义 → G 级）

| Cursor 规则 | 本质反模式 | 协议层语义（语言无关） | G 级 |
|------------|-----------|----------------------|------|
| 1. 文件 ≤1000 行 | **God File** | "PR 不得把文件从 <N 行跨越到 >N 行"（N 可配；语义是**跨越**不是**超过**） | G0 |
| 2. spaghetti 条件 | **Conditional Tangling** | "diff 新增条件分支不得散落在非主体流程中" | G2 |
| 5. any/cast | **Fuzzy Boundary** | "类型/契约边界不得因 diff 变模糊" | G0 |
| 6. 重复 helper | **DRY Violation** | "不得引入与既有 canonical 逻辑重复的实现" | G1 |
| 4. thin wrapper | **Thin Abstraction** | "不得引入无信息增益的间接层" | G2 |
| 7. 串行/非原子 | **Sequential Coupling** | "独立步骤不得无因串行；相关更新不得留下半应用态" | G2 |
| 3. bias toward cleaning | （元原则） | 不可判定，LLM 心法 | G3 |
| 0. code judo | （元原则） | 不可判定，LLM 心法 | G3 |

---

## 5. 统计结论

把 skill 全文（7 条标准 + 12 条审查问题 + 16 条升级信号 + 8 条批准门槛）全部映射：

| G 级 | 占比 | 说明 |
|------|------|------|
| G0 纯机械 | ~20% | God File 跨越、模糊边界、重复 helper |
| G1 清单后机械 | ~20% | canonical 清单 + 重复检测 |
| G2 信号+解释 | ~25% | 条件纠缠、薄抽象、顺序耦合 |
| **G3 纯主观** | **~35%** | code judo、bias toward cleaning、品味 |

**结论：约 65% 能落成"反模式检测语义"（模式层，语言无关），35% 是纯品味（G3）。** 每个模式层语义都需要各平台自行实现检测器；协议永远只定义"检测什么反模式 + 如何判定"，不定义"用什么工具"。

---

## 6. 三个关键设计决策

### 决策 1：diff 驱动，不是存量驱动

skill 审查的是 **"current branch's changes"**，不是整个代码库。gate 必须**只测 diff 新增了什么复杂度**，否则误伤历史大文件。

### 决策 2："跨越阈值" ≠ "超过阈值"

规则 1 的精确语义是 **"push from under to over"**：

```
before = 主分支的文件行数      # 900
after  = PR 后的文件行数       # 1150
if before < N and after >= N:   # 跨越 → 触发
    block("PR 把文件从 <N 推到 >N 行，先分解")
```

存量 1200 行文件改 5 行不触发。精确复刻 skill 原意。

### 决策 3：判定权在 gate，LLM 退居解释

正是 `agate-risk-score.py` 的模式（客观信号算分，analyst 只解释不决定）：

```
机械检测器算"反模式信号分"（G0/G1/G2）
        ↓ 信号分超阈值
    fail-closed 阻断 / 高优 WARNING
        ↓
    LLM 只做：解释为什么 + 提出 code-judo 候选方案
        ↓
    作者改后重跑 gate（exit code 判定，不看 LLM 意见）
```

这直接修掉了 Cursor skill 的致命缺陷（判定靠 LLM 自觉）。

---

## 7. 检测器层参考实现（⚠️ 仅示例，协议不绑定）

以下工具仅为"检测器层参考示例"，**协议层不绑定任何技术栈**——各项目按 `gate_commands` 自行选择实现。

| 反模式 | 参考实现示例 | 备注 |
|--------|-------------|------|
| God File 跨越 | `git diff` 前后 `wc -l` 对比 | 一行脚本 |
| 模糊边界 | Python：类型注解 lint；TS：`no-explicit-any` | 平台自选 |
| DRY 违反 | AST 签名比对 / 重复代码检测器 | 平台自选 |
| 条件纠缠 | `git diff -U0` + 条件语句密度统计 | ~30 行脚本 |
| 薄抽象 | pass-through 函数占比检测 | 需定义"无信息增益"判据 |
| 顺序耦合 | 数据依赖分析 + 串行调用模式检测 | 半自动 |

---

## 8. 对 agate 的落点（候选 backlog）

> **RM-AG0046（暂定编号）**：P4/P6 增加"维护性反模式 gate"——协议层定义反模式语义与判定标准（God File 跨越 / Conditional Tangling / DRY 违反 / Fuzzy Boundary / Thin Abstraction / Sequential Coupling），检测器由各项目按 `gate_commands` 自行实现；客观信号算分 + LLM 只解释不决定。
>
> 联动 RM-AG0022（结构化层）：反模式语义可进 `rules/*.yaml` 作为可判定规则（而非散落 markdown），使 check-gate.py 可机械读取。

---

## 9. 与现有机制的关系

| 现有机制 | 本设计的映射 |
|----------|-------------|
| `gate_commands` | 反模式检测器的声明入口（协议不规定工具） |
| `agate-risk-score.py` | 决策 3 的同款分工（信号算分 + LLM 解释不决定） |
| RM-AG0022 结构化层 | 反模式语义进 `rules/*.yaml` 的承载层 |
| `platform-notes.md` | "协议语义 → 各平台检测器"的映射文档 |
| ruff（CI 已有） | 仅"模糊边界"一类反模式的一个平台实现，非通用 |

---

## 10. 一句话总结

**Cursor skill 缺的不是"更严的审查"，而是"模式层/检测器层的分离"——它把"什么算反模式"和"怎么检测"混在 LLM 品味里。agate 的 gate 化，就是拆开这两层：协议定义反模式语义，检测器由各平台实现，判定权永远在 gate。**
