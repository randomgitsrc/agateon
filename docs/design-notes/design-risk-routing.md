# 风险分路由（ceremony routing）设计提案 — RM-AG0031

> 状态：**已落地（TAG0019，v0.58.0，RM-AG0031 ceremony routing）** ｜ 来源：2026-08-21 用户反馈——agate 提升质量但成本不低、速度不快；TAG0018 实证成本结构
> 目标：**压成本曲线而不降质量地板**——薄化的是"仪式"，不是"验证"。

---

## 1. 问题定义

### 1.1 成本结构实证（TAG0018，2026-08-21）

| 成本项 | 占比特征 | 价值 |
|--------|----------|------|
| subagent 派发轮次（~11 次）| 串行阶段固有 | 必要 |
| **LLM 评审（4 场）** | 17 条非阻塞 + 1 条真实发现（README 缺 DSH 行，机械检查也能抓）| **≈0 净收益** |
| gate 折返（pre-commit 拦 3 次 + P5 失败 1 轮）| 格式/规则摩擦（coupling_checklist 流式、半角冒号、源码数 6>5）| 防了真实错误，但折返周期长 |
| 机械 gate（扫描器/校验/审计）| 便宜 | **全部真实价值集中于此** |

结论：昂贵部分（评审/仪式）贡献接近零；干活的部分（机械检查）不贵。

### 1.2 根因：复杂度判定依赖 agent 自报 = self-authorization 陷阱

- 若让 analyst 自报"low → thin 档跳过评审"，就是 komina 命名的失败模式：**同一个概率模型提出行动又评判它能否进行**
- TAG0018 实证：analyst 声明 `risk_level: low` 后 P5 仍抓出真实违规（R2/R4）；agent"一把梭哈"倾向是系统性的
- 现有机制漏洞链：agent 自报 risk_level → 机械映射（C8）→ 决定评审——**薄弱环节是第一环（自报）**

---

## 2. 设计三原则

1. **客观信号路由，agent 无法伪造**：复杂度/风险由可计算信号得出，做成 `agate-risk-score.py`：**脚本算分，analyst 只解释不决定**
2. **fail-closed 默认**：thin 档 = "申请 + 过客观 checklist"（对齐裁剪声明的 coupling_checklist/跳过风险评估模式）；拿不到 → 按 standard 走
3. **声明本身被审**：requirements-review 显式增加"审风险分级/裁剪声明 vs diff 证据"职责（P1 后最便宜的独立复核点）

---

## 3. 具体设计

### 3.1 `agate-risk-score.py`（脚本算分）

输入：暂存区 diff（`git diff --cached --name-only` + 行数）或任务 scope 声明
输出：`risk_score`（数值）+ `tier`（thin / standard / full）+ 每条信号的证据行

| 信号 | 权重 | 判定 |
|------|------|------|
| 文件类型 | 高 | 命中 `agate/**/*.md`（协议本体）、`agate/scripts/*.py`（gate 逻辑）→ +高；纯 tests/配置 → +低 |
| 敏感路径 | 高 | security/data/permission/auth/网络请求相关路径 → +高（映射 cso 触发域）|
| 改动规模 | 中 | 文件数/行数阈值——**对齐 pruning"源码数 ≤5"先例**（>5 自动 +高，P7 不可裁联动）|
| 域映射 | 中 | C8 已机械：backend/frontend/mcp/security 域 → 对应评审角色强制 |
| 影响面 | 中 | 被引用模块/依赖（grep 反向引用）→ 跨模块 +高 |

analyst 可在 P1 中对脚本结果**解释/申诉**（如"虽触碰协议文件但仅追加章节"），但降级必须过 3.2 的 checklist。

### 3.2 档位与 fail-closed

| 档位 | 适用（risk_score）| 仪式 | 说明 |
|------|-------------------|------|------|
| **thin** | 低分且**全信号低** | ≤5 BDD、无 LLM 评审、P2 单候选、P6 快速验收 | **需申请**：声明 `ceremony: thin` + 逐信号 checklist（对齐 coupling_checklist 流式格式）+ 跳过风险: 评估——缺一不可，否则回退 standard |
| **standard** | 默认 | 现状（TAG0018 全流程）| 默认档，无需声明 |
| **full** | 高分任一 | 强制 plan-eng-review + cso + P7 不可裁 + 人工终审建议 | 对齐现有 risk_level=high 强制项，补 P7 不可裁 |

- **默认 fail-closed**：不声明 = standard；声明 thin 但 checklist 不满足 = standard（gate 拦截）
- 实现：`check-pruning.py` 扩展为 `check-routing.py`（或新增 CHECK），校验 ceremony 声明 vs risk_score 与 checklist

### 3.3 requirements-review 增责

评审清单新增：**"风险分级/裁剪声明 vs diff 证据"核对**——analyst 的 `risk_level`/`ceremony`/`phases` 声明是否与暂存区实际改动匹配（文件类型/规模/域）。这是 P1 后最便宜的独立复核点，堵住自报漏洞的第一道外部闸。

### 3.4 折返优化（配套，不属本条目主体）

- **subagent 返回前自检 gate**：P1 写完自跑 check-routing、P4 实现完自跑 check-gate——折返从"commit 时才发现"缩到"派发轮内"
- **写时 schema 校验**（联动 RM-AG0022）：coupling_checklist/ceremony/跳过风险 等声明进 YAML schema，写错当场报——消灭格式摩擦类折返

---

## 4. 与既有机制的关系

| 机制 | 关系 |
|------|------|
| pruning（P7 裁剪/源码数≤5）| **先例与基石**：风险分信号直接复用其源码数/文件类型逻辑；check-routing 可视为 check-pruning 的泛化 |
| C8 机械映射（role-system）| 域→评审角色已机械；risk_score 补上"档位"维度 |
| risk_level（P1 声明）| 从"自报"升级为"脚本算分 + 申诉 + checklist" |
| RM-AG0022 结构化层 | 联动：声明 schema 化后路由校验写时生效 |
| LIMITATIONS 局限 3 | 缓解方向之一：评审必要性不再依赖被评审者的自我判断 |

---

## 5. 落地节奏

1. **M1（算分 + 声明）**：`agate-risk-score.py` + P1 卡加 `ceremony` 字段 + requirements-review 增责（纯增量，不动现有流程）
2. **M2（档位生效）**：check-routing 拦截 thin 档未过 checklist；TDD 红灯先行
3. **M3（评审可选化）**：thin 档跳过 LLM 评审——**以 TAG0018 的"LLM 评审≈0 净收益"实证为验收锚**，产出前后对比（评审轮数 vs 真实发现数）
4. **M4（dogfood）**：下一个 low 风险任务（如文档/配置类）走 thin 档验证成本曲线

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| 算分规则被 exploit（agent 学会凑低分）| 信号来自 diff 客观事实，不可伪造；降级需 checklist + 独立审声明 |
| thin 档漏真实问题 | fail-closed + 机械 gate 保留（TAG0018 已证机械 gate 是主力）+ P5/P6 不可裁 |
| 评审可选化后质量下降 | M3 以实证数据验收，不达标回滚 standard |
