---
task_id: TAG0035
phase: 复盘
type: retrospective
status: done
created: 2026-09-16
trace_id: TAG0035-retro-20260916
---

# TAG0035 复盘 — gate 健壮性批（RM-AG0062 归并 + RM-AG0064 并入）

## 一、事实基线

| 项 | 值 |
|----|-----|
| 任务编号 | TAG0035（RM-AG0062 scheduled 关联；RM-AG0064 并入后 cancelled） |
| 交付形态 | 一个 task 内 **4 个子批**串行（A/B/C/D），**逐批 commit** |
| 阶段轨迹 | P0 → P1 → P2 → P3 → P4 → P5 → P6 → P6.5 → P7 → P8 → READY |
| 版本 | v0.71.0 → **v0.71.1**（`bump_type: patch`） |
| 合并 | PR #324 → main（merge commit `14d20eb`） |
| 验证 | 全量 **1634 passed / 2 skipped / 0 failed**；P6.5 judge **14/14 criteria passed**（`partial: false`） |
| 子批测试 | A 12 / B 8 / C 3 / D 6 passed |
| roadmap 回写 | RM-AG0062 → `done`（P8 gate 硬校验 RM-AG0043 已过） |
| 看板 | TAG0035 已入「已完成（归档）」区 |

**交付内容**：

| 子批 | 内容 | 来源 |
|------|------|------|
| A | `check-gate.py` 未知阶段 **fail-open → fail-closed**（`exit 2` → `exit 1`） | RM-AG0064（分析 §5.3 实测） |
| B | 三处数字序号假设致**非数字阶段名静默失效** | 同批发现 |
| C | `_gate_p4` 完整度判据——跨 commit / 回退场景误判 | DEBT0037 |
| D | `check-judge-verdict.py` 信息隔离黑白名单 3 处假阳性 | DEBT0038 |

**子批 A 的验证锚（实测）**：
```bash
$ python3 agate/scripts/check-gate.py P99 <task_dir>
未知阶段: P99
exit=1   # 修复前为 exit 2（= 通过码，静默放行）
```

## 二、做得好的 + 可复用模式

### 1. 归并批形态（TAG0023/TAG0031 先例的有效复刻）
4 条同簇 DEBT + 1 条实测缺陷合成一个 task，**子批逐批 commit**（`c9c6f5c` A / `50e5e46` B / `6d765a1` C / `df55b9b` D）：
- 每个 commit 含代码文件 → **完全避开 `_gate_p4` 的"暂存区无代码文件"判据**（这正是子批 C 要修的缺陷，本任务自身却未踩中）
- 逐批 commit 使 **I1 边界可机械归属**（对照分析报告 §3.1 的 13% 实测——本任务属于理想形态的少数派）

### 2. "响亮失败"优于"静默通过"（fail-closed 的实证落地）
子批 A 把未知阶段从 `exit 2`（通过码）改为 `exit 1`。**价值不在于修了一个正在发生的 bug**（P0-P8 全注册，从未触发），而在于：**扩展阶段集时不会静默放行**。这与 `custom-role.md` 的既有扩展范式配套。

### 3. 子批 C 的方案收敛（比 P0-brief 更简洁）
P0-brief 提了两个候选（放宽判据 / 显式识别回退），实现收敛为单一函数 `_gate_p4_has_prior_code_commit(task_id)`：

> 扫描本任务 P4 阶段历史 commit 是否**已引入过**非 md/yaml 代码 diff——覆盖 BDD-8（跨 commit）与 BDD-9（回退后修复），**两者共同前提是"此前存在过一个带代码变更的 P4 commit"，无需分别处理**。

**可复用**：把"两个场景"归结为"一个共同前提"，是拆批设计的通用化简手法。

### 4. P0-brief 的两轮核验（自查 + 独立评审）抓出 9 处问题
- 我的自查：`ci-gate-backstop.py` 行号 205-208 → **209-211**；`P6-evidence` 计数 42 → **37**
- 独立评审：子批 D 不同簇（DEBT0040 含 CI 改动需许可 / DEBT0041 仅名义相关）→ **拆出**；子批 B 与 out-of-scope 冲突 → 采用最小案；off-by-one 三处

**这条经验值得固化**：P0-brief 的行号/数字必须**当场核验**（`sed -n`/`grep -n`），不能凭记忆引用。

## 三、发现的问题

### 1. 【高】P0-brief 的事实性引用缺少机械校验
本轮 P0-brief 共 11 项待核验断言（行号、目录计数、DEBT 存在性），**自查 + 评审共抓出 4 处错误**（36% 错误率）。这些错误**不会阻断任务**（P0 gate 只查 P0-brief 存在性），但会误导后续阶段。
→ **改进措施 1**
→ **登记 DEBT0039 同族**（参见"技术债登记核对清单"）

### 2. 【中】子批 C 的"判据放宽"缺少"仍能拦住什么"的边界声明
P0-brief 的 known_risks 已提示该风险，但 P2/P4 是否落实"明确放宽后仍能拦住的边界"需回溯核查。判据放宽天然削弱 gate 拦截力，若只证"现在不误判了"而未证"该拦的还能拦住"，属于**验证缺口**。
→ **改进措施 2**

### 3. 【中】`DEBT0040` / `DEBT0041` 被移出后的去向未闭环
独立评审判定：DEBT0040 含 **CI workflow 改动**（AGENTS.md 规则 5 需用户许可）、DEBT0041 与 gate 健壮性仅名义相关，**两者已移出本批**。但移出后：**未登记归属**（既未并入他批、也未独立立项）。当前二者仍为 `open`，且**无 task_id**。
→ **改进措施 3**

### 4. 【低】复盘环节在 P8 收尾中缺失
TAG0035 已 READY 且 PR 已合并，但 `retrospective.md` **未产出**（TAG0034 有）。P8-release.md 亦未提及复盘。
→ **改进措施 4**

### 5. 【低】DSH preset 的 key 名无机械校验（TAG0035 命名空间外，但同期暴露）
同期发现 `persona` 的 `text` → `prefix` 升级不兼容（PR #325 已 hotfix）。根因是**测试只校验 persona 内容、不校验 key 名是否符合 DSH schema**。
→ **改进措施 5**

## 四、改进措施

| # | 措施 | 落点 | 触发 |
|---|------|------|------|
| **1** | P0-brief 的行号/计数类断言，**在写 brief 时就跑一遍核验命令**并把命令留在证据行 | 主 Agent 的 P0 检查单（`orchestrator-template.md` 或 P0 卡片） | 本任务 36% 错误率 |
| **2** | 判据放宽类改动，P3 须含"仍能拦住 X"的**反向红灯用例** | 本任务已闭环则记入复盘；未闭环则登记 DEBT | 子批 C 的验证缺口 |
| **3** | DEBT0040 / DEBT0041 **补登记归属**（独立立项或并入他批） | `tech-debt.md` 补 `task_id` 或新 RM | 评审移出后未闭环 |
| **4** | **本复盘本身即措施 4 的落地**；P8 收尾清单补"复盘已产出"核对项 | 本文件 + P8 卡片建议 | TAG0035 缺失 |
| **5** | DSH preset 补 **required-key schema 校验测试**（覆盖所有含 config 的包） | `agate/tests/unit/test_dsh_preset.py` | PR #325 的性质 |

## agate 反馈

| # | 反馈 | 类型 | 建议去向 |
|---|------|------|---------|
| 1 | **P0 gate 不校验 brief 的事实性**——行号/计数错误可静默流入 P1-P8 | 机制缺口 | 可选：P0 gate 或独立 check 对 brief 中的 `file:line` 断言做存在性抽检 |
| 2 | **归并批的"移出项"缺少闭环登记**——评审移出 DEBT 后无机制要求补去向 | 机制缺口 | dispatch-protocol 或 debt 流程补"移出即登记"约定 |
| 3 | **复盘未纳入 P8 gate 硬校验**（对比 roadmap 回写有 RM-AG0043 硬校验） | 机制缺口 | 可选：P8 收尾检查清单显式列"复盘产出" |
| 4 | 本任务**逐批 commit 是 I1 可归属的理想形态**，与实践主流（87% 合并 commit）相反 | 事实记录 | 与 RM-AG0063（MVWU）试点相关：可作为 Q2 的正面样本 |

## 技术债登记核对清单

| 类别 | 检查项 | 结论 |
|------|--------|------|
| 本次发现的问题 | 是否都已登记 DEBT？ | ⚠️ 问题 1/2/4 为**流程类**（改进措施 1/2/4），暂不登记 DEBT；问题 3（DEBT0040/0041 去向）**需补登记** |
| 本次修复的 DEBT | 是否已 closed？ | DEBT0037 / DEBT0038 应已 closed（P8 回写）；**需核对** |
| 复盘的 agate 反馈 | 是否已转为 DEBT/RM？ | 4 条反馈均为**机制缺口**，建议由维护者评估是否登记 |
| 未闭环项 | 是否全部有 next action？ | 措施 1-5 均给落点；**措施 3（DEBT0040/0041 去向）是唯一阻塞项** |

---

## 附：溯源

- P0-brief：`P0-brief.md`（含 4 子批定义 + out-of-scope + 5 条 known_risks）
- 分析依据：`docs/design-notes/design-orchestration-evolution-analysis.md` §5.3（fail-open 实测）+ 附录 B
- P6.5 judge：`P6.5-judge-verdict.md`（14/14 passed，partial: false）
- 全量证据：`P6-evidence/bdd-3-7-full-suite.log`（1634 passed）
- 同族先例：`TAG0023-mechanism-checks` / `TAG0031-debt-cleanup`
- 同期 hotfix：PR #325（DSH persona key 升级不兼容）
