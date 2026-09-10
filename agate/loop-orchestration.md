# /loop 自动编排设计

> agate，把"手动逐阶段触发"升级为"自动推进"

---

## 设计目标

用户的设想：一个 /loop 机制，自动触发任务节点，遇到节点就组织上下文、产生 subagent、提供上下文让它执行，节点之间有触发条件，条件不够就返回重试（有上限），条件够就进下一节点。

这个设想是对的，而且是业界做 agent 工作流的标准模式。v4 把它落地为三个递进的自动化档位。

---

## 三个自动化档位

### 档位 A：手动逐步（最稳，默认）

人工每次说"执行下一步"，主 Agent 执行一次"单步函数"（见 state-machine.md），然后停下等下一个指令。

```
用户：执行 T002 下一步
主 Agent：[派发 P4 subagent → 判定门槛 → 更新状态] 完成，T002 现在在 P5，重试 0
用户：执行 T002 下一步
主 Agent：...
```

适合：关键任务、需要人工在每个阶段把关。

### 档位 B：半自动（推荐）

主 Agent 连续执行单步，每过一个门槛自动推进，**只在两种情况停下来问人**：
- 门槛失败且重试超限 → PAUSED，报告人工介入
- 到达需要人工确认的检查点（如 P8 发布前）

```
用户：跑 T002 直到 P5
主 Agent：
  [P4 派发 → 完成 → 进 P5]
  [P5 派发 → 测试失败 → 重试1 → 派发 → 通过 → 完成]
  T002 跑到 P5 完成，所有测试通过。是否继续 P6？
```

适合：大多数任务。人只在关键节点介入。

### 档位 C：全自动 /loop（增强，谨慎用）

主 Agent 自动跑完 P1-P8，**自动跑完不需要决策的部分，遇到硬中断点必停**（不是"全程不停"）。
档位 C 的每次阶段推进判定统一经 `agate next {TASK_DIR}`（TAG0027 §3.7 档位 C 定案）——
主 Agent 不临场自行改 .state.yaml phase，推进记录（state_transition 事件 + git log）
可观测（BDD-11）。档位 A/B 手动/半自动路径不受影响。

**硬中断点（--auto-approve 也不能跳过）：**
- 未决的 `[NEED_CONFIRM]`（P1 需求方向，必须人确认）（仅正向声明触发）
- `[CAPABILITY_GAP]`（任务需要某能力，环境中无任何补充路径，需人决策）
- `[PROD_TOUCHED]`（任何阶段意外接触了生产环境，必须立即暂停人工处置）（仅正向声明触发）
- 不可逆操作 `[NEED_CONFIRM]`（数据删除/迁移/生产写入，备份+确认后才可继续）
- 业务方向决策（Agent 无权决定「功能要不要做」）
- P8 发布（不可逆操作）
- 安全策略决策
- 涉及外部资源/权限

（完整定义见 state-machine.md「用户介入边界」表，本列表与之保持同步——新增项也以 state-machine 为权威来源，本文件只列提要，不展开）
新增的"跨 ≥2 阶段回退"硬中断见 state-machine.md「阶段跳变检测」节，本文件不重复列出。

`--auto-approve` 只能跳过软确认（阶段内门槛通过，如 P2 评审 approved），不能跳过上述硬中断点。

全自动的真实含义是"无人值守跑完可自动化的阶段，遇到需人决策的点必停并汇报"，而非"全程不停"。

```
用户：/loop T002
主 Agent：
  [P1→P2→P3→P4→P5→P6→P7→P8 全自动，每阶段派发 subagent]
  T002 全流程完成，已发布。过程：P2 重试1次（评审打回），其余一次通过。
```

仅在档位 B 稳定、且任务风险可控时使用。

---

## 进度输出

每个阶段完成后主 Agent 输出一行进度（即使全自动也至少输出进度行）：

```
[T002] P4 done (14/14 passed) → P5
[T002] P5 done (failed=0, UI E2E 2/2) → P6
[T002] P6 done (BDD 验收 5/5) → P7
[T002] P7 done (无 BLOCKER) → P8
[T002] P8 done (所有包发布检查通过) → READY
```

---

## /loop 的执行逻辑

```
/loop {task_id} [--until Pn] [--max-retry N] [--auto-approve false]

主 Agent 执行：

LOOP:
    1. 读 {AGATE_WORKSPACE}/tasks/active-tasks.md → 当前状态
    2. if 状态 == READY: 输出交付小结（格式见 dispatch-protocol.md「任务完成小结」），等待人工 make publish，退出
    3. if 状态 == DONE: 报告任务已完成，退出
    3. if 状态 == PAUSED: 报告暂停原因，退出
    4. if 当前阶段 == --until 指定的停止点: 报告，退出
    5. if 触发硬中断点: 无条件停下问人（--auto-approve 不能跳过）
       硬中断点 = 未决 NEED_CONFIRM / CAPABILITY_GAP / PROD_TOUCHED / 不可逆操作待确认 / 业务方向决策 / P8 发布 / 安全决策 / 涉及外部资源权限（NEED_CONFIRM/PROD_TOUCHED 仅正向声明触发）
       （对应 state-machine.md「用户介入边界」表的后四类情况）
    6. if 当前阶段需要软确认 && !auto-approve: 停下问人
       软确认 = 阶段内门槛通过确认（如 P2 设计评审 approved）

    7. 执行一步（见 state-machine.md 的单步函数）
       - 派发当前阶段 subagent
       - 判定门槛
        - 更新状态（含重试记录）

    8. if 门槛失败 && 重试超限:
         标记 PAUSED，写回看板
         报告：阶段、失败次数、原因
         退出

    9. goto LOOP
```

**关键：每一轮都重新读 `{AGATE_WORKSPACE}/tasks/active-tasks.md`**，不依赖上一轮在记忆里的状态。即使中间被压缩，重读文件就能继续。

---

## 防止失控的护栏

自动化最大的风险是失控（无限循环、烧 token、跑偏）。四道护栏：

### 护栏 1：每阶段重试上限

单个阶段重试超过 MAX_RETRY（按阶段 2-3 次，见 state-machine.md 重试上限表）→ PAUSED，不再自动重试。

### 护栏 2：全局步数上限

整个 /loop 的总步数上限（默认 20）。P1-P8 正常是 8 步，加上重试也不该超过 20。超了说明卡在某处反复打转 → 强制停止。

### 护栏 3：检查点人工确认

某些阶段默认需要人工确认，即使全自动也会停下来：
- P2 评审 rejected（方案被打回，可能需要人重新定义问题）
- P8 发布前（不可逆操作）

`--auto-approve` 可以跳过，但默认要确认。

### 护栏 4：状态一致性检查

每轮开始先检查 `{AGATE_WORKSPACE}/tasks/active-tasks.md` 和任务目录文件是否一致（见 state-machine.md）。不一致 → 停下，避免在错误状态上继续。

---

## 上下文如何保持不爆炸

/loop 跑很多步，但主 Agent 的上下文不该线性增长。关键：

1. **每步派发的 subagent 在独立上下文**——P1 的细节留在 P1 subagent，主 Agent 不carry
2. **主 Agent 每步只增加"路径 + 摘要"**——一个任务跑完 7 步，主 Agent 上下文只多了 7 行摘要
3. **状态从文件读，不在上下文累积**——每轮读 `{AGATE_WORKSPACE}/tasks/active-tasks.md`，不靠记忆

这样即使 /loop 跑完整个 P1-P8，主 Agent 的上下文增量在**单任务内是常数级**（几行摘要 + 当前状态）。

### ⚠️ 主 Agent 长期运行的上下文管理

"常数级"只对**单个任务**成立，对主 Agent 的整个生命周期不成立。主 Agent 跑 10 个任务就累积 10 个任务的摘要 + 派发记录 + 门槛判定。跑久了主 Agent 自己会触发压缩——上下文爆炸从"单会话内"转移到了"主 Agent 长期运行"层面。

**原则：主 Agent 尽量无状态。** 因为状态全部落盘（`{AGATE_WORKSPACE}/tasks/active-tasks.md` + 任务目录 + orchestrator-log.md），主 Agent 理论上不需要在记忆里保留任何历史：

- 每轮只依赖文件（每轮重读 `{AGATE_WORKSPACE}/tasks/active-tasks.md`），不依赖上一轮的记忆
- **一个任务到达 DONE 后，主 Agent 应主动"忘掉"该任务的所有中间摘要**——状态已落盘，记忆里不需要保留
- 主 Agent 自己也会被压缩/中断，但因为无状态，重读文件就能恢复（和子 Agent 一样靠状态落盘抗中断）
- **`orchestrator-log.md` 防无响应**——长操作前写 `NEXT: ...`，写下去就完成使命，不需要再读回来

实践上：长时间运行时，主 Agent 处理完一个任务就可以开新会话/清理上下文，从 `{AGATE_WORKSPACE}/tasks/active-tasks.md` 重新加载待办任务列表继续。**主 Agent 的"记忆"应该是 `{AGATE_WORKSPACE}/tasks/active-tasks.md`，不是它的上下文窗口。**

这正是解决用户最初问题（上下文爆炸触发自动压缩）的机制。

---

## 协调者参与组织上下文

用户提到"组织上下文的工作可由协调者参与"——这正是主 Agent（协调者）的核心职责。它组织上下文的方式是：

```
派发 P{n} subagent 前，协调者：
  1. 确定 P{n} 需要哪些输入文件（按阶段固定，见 README 阶段总览）
  2. 在派发 prompt 里写入这些文件的路径（不是内容）
  3. 指定 P{n} 的角色定义文件路径
  4. 写明门槛和返回要求
```

协调者"组织"的是**文件路径的清单和任务指令**，不是文件内容本身。这保证了组织上下文这个动作本身也不污染主 Agent 的上下文。

---

## 落地建议

1. **先跑通档位 A**（手动逐步），验证派发协议和角色都正常工作
2. **再上档位 B**（半自动），验证门槛判定和重试逻辑
3. **最后才用档位 C**（/loop 全自动），且先用 `--until` 限制范围小步验证
4. **前提**：先验证当前平台能调起自定义角色（平台派发能力差异见下注记）

> 实现注记：第 4 条为平台适配前提——自定义角色能否被派发工具调起随平台而异（如 OpenCode
> 自定义角色需实测能否被 task 工具调起来，issue #29616 记录见 dispatch-protocol.md 平台适配
> 说明）；协议层语义不绑定任何平台工具名，一律以"派发 subagent"为准。

不要一上来就全自动。先证明每个部件可靠，再串成自动循环。

---

## 已知改进项（未实现，实际使用中按需推进）

以下能力当前未实现，是已知的边界，不影响 agate 基本运行：

**1. 并行执行**

- ✅ **评审并行已落地**（v0.22.0）：P2/P4 多评审角色可同时派发，各写不同产出文件，组长汇总。见 P2/P4 阶段卡片。
- ✅ **执行阶段按包拆分并行已落地**（v0.22.0）：P3/P4/P5/P6 当 P2 packages > 1 且包间无依赖时可拆分并行。P4 需额外约束（各 implementer 只改自己 package 目录 + 基础设施隔离）。P6 受限并行（证据并行，验收文件不并行）。见 P3/P4/P5/P6 阶段卡片。
- ❌ **跨任务并行未落地**：多个独立任务（Txxx-a, Txxx-b）同时执行。需要每个任务独立的 .state.yaml + git 工作区隔离（worktree 或独立分支）。当前多任务 hook 已支持（扫描所有暂存的 .state.yaml），但主 Agent 串行推进任务。待 v0.23.0+ 设计讨论。

**2. ~~评审角色选择的可判定化~~**（已实现：role-system.md domains→评审角色机械映射，C8 规则）

**3. 嵌套深度约定（避免撞 max_depth）**
v4 层级约定：主 Agent（L0）→ 执行/评审 subagent（L1），不依赖 L2（Codex max_depth 默认 1，禁止深层嵌套）。如果某阶段复杂到 L1 subagent 扛不住，应在 P1/P2 阶段**拆成多个任务**（Txxx-a, Txxx-b），用任务拆分替代 agent 嵌套，而非让 L1 再派 L2。

---

## Hardening-roadmap 集成（自 v0.4 引入，持续生效）

档位 C（"主 Agent 自动跑完 P1-P8"）自 v0.4 起承担一条硬约束：**每次阶段 commit 都要先过 pre-commit hook**。这是 /loop 推进时必须严格遵守的客观边界。

**自动推进时的 gate 处理流程**（TAG0027 §3.7：推进判定统一走 `agate next`）：

```
单步函数推进（如 P4→P5）：
  ├─ subagent 完成任务，commit wf(Txxx-P4)
  │    └─ pre-commit hook 触发
  │         ├─ exit 0（通过）→ 主 Agent 运行 agate next {TASK_DIR} 推进到下一 phase
  │         │     └─ agate next 内部：check-gate exit ∈ gate_pass_exit（该 phase 的通过出口
  │         │        码，多数 phase = 2）→ 按 phases.yaml next 更新 .state.yaml phase + git
  │         │        add + state_transition 事件（只 add 不 commit——跳变合法性由下一
  │         │        commit 的 pre-commit 校验；exit 2 是多数 phase 正常通过码 ∈ pass_set，
  │         │        直推不是暂停）
  │         ├─ exit 1（拦截）→ 主 Agent 分析错误并修复后重试；
  │         │     若确认该阶段 gate 判负（check-gate exit 1）→ agate next 自动走
  │         │     retreat 分支（按 phases.yaml retreat 表值委托 agate-retreat-to.py 逐阶回退）
  │         └─ exit ∉ gate_pass_exit 且 ≠ 1（真暂停/异常，协议实际极少）→ 主 Agent 运行
  │               agate next：落盘 {phase}-exit2-resolution.md（暂停转主 Agent，不自动 retry）；
  │               P6 前进特例：exit 2 ∈ pass_set（gate_p6 通过码）但推进前置 judge 复核裁决
  │               （gate_p65 exit 0 才直推 P7），见下
  └─ push → CI backstop 重跑 gate（捕获 --no-verify 绕过）
```

**可观测证据（BDD-11）**：`agate next` 每次推进 append `state_transition` 事件
（gate-events.jsonl，字段 from/to/ts）+ 随 .state.yaml 的 commit（git log 可查）——
档位 C 的"推进均经 agate next 判定"落在这两个证据面，可二值判定。

**P6 前进特例（A1 裁决，§3.1/§3.4）**：P6 恒 check-gate exit 2；`agate next` 在
phase=P6 且 check-p6-provenance exit 0 时按 judge 裁决推进：
- judge 未启用（历史任务）→ gate_p65 早退 0 → 直推 P7；
- judge 启用 → 跑 check-gate P6.5（= verdict 存在 + check-judge-verdict + check-events
  双 exit 0）：exit 0 → 推 P7；exit 1 → 停留 P6 有指引（不落盘 exit2-resolution，
  P6 特例豁免）。

**档位 C 启动前查阅**：orchestrator-template.md「Fallback（按需查阅，不要求每轮必读）」节——按需查阅 state-machine.md、platform-notes.md、git-integration.md 等的 hardening 集成段。

**档位 C 推进时的硬中断点**（PAUSED 而非 retry）：
- hook exit 1 + 修复 3 次仍失败 → PAUSED
- 任何 hook 指出"该阶段不该裁剪"（check-pruning 不满足条件）→ PAUSED 报告主 Agent
- P6 evidence 缺失 + 3 次提醒 subagent 补充仍无 → PAUSED
- `risk=high` + `agent=main` 自审 → check-gate.py 硬拦截（exit 1，不可自行批准评审）

**禁止行为**：
- ❌ `/loop` 推进时 `--no-verify` 跳过 hook（CI 兜底会抓到）
- ❌ `/loop` 推进时绕过 check-pruning 把声明的裁剪阶段也"自动跑"——hook 会拦
- ❌ `/loop` 跑 P6 时不让独立 verifier subagent 写 P6-acceptance.md（provenance 会警告 + CI 单 author WARNING）

---

*配合 dispatch-protocol.md 和 state-machine.md 使用*
