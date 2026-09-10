# Workflow v4 落地验证方案

> 目的：验证 v4 的派发机制在 OpenCode 上真的能跑通，再投入真实任务
> 执行者：OpenCode agent（照本方案逐步执行并记录结果）
> 验证地基：定义子 Agent → 主 Agent 派发 → 隔离执行 → 只返回路径+摘要

---

## 为什么先做这个验证

v4 是文档协议，不是代码框架——它靠 LLM 读文档后自觉执行，无法像代码那样强制。所以投入真实任务前，必须先验证三个地基是否成立：

1. **主 Agent 会派发子 Agent**，而不是自己一路干到底（早期版本的核心病灶）
2. **子 Agent 在独立上下文执行**，主 Agent 上下文不被污染
3. **子 Agent 只返回路径+摘要**，不把文件全文拉回主 Agent

这三点成立 = v4 能有效运行。不成立 = 需要调整派发方式或改用代码框架。

**验证顺序：先测方法 B（v4 推荐主路径，最稳），再测方法 A（自定义角色，锦上添花）。**

---

## 执行说明（给 OpenCode agent）

请逐个 Phase 执行，每个 Phase 完成后在「结果记录」里如实填写。
不要跳步。如果某个 Phase 失败，记录失败现象，继续执行后续 Phase（除非前置依赖明确不满足）。
全部完成后，按「最终判定」给出结论。

---

## Phase 0：准备测试数据

执行：
```bash
mkdir -p docs/tasks/TEST
printf 'line1\nline2\nline3\nline4\nline5\n' > docs/tasks/TEST/input.md
ls -la docs/tasks/TEST/
```

期望：`docs/tasks/TEST/input.md` 存在，5 行内容。

### 结果记录 Phase 0
- [ ] input.md 已创建：____

---

## Phase 1：方法 B 验证（v4 推荐主路径，最优先）

**方法 B 不依赖任何自定义 agent，只用内置 general subagent + prompt 注入角色文件。** 这是 v4 真正依赖的路径，跨平台、不踩 OpenCode issue #29616。

### 1.1 派发测试

在 OpenCode 里，主 Agent 执行以下操作（用 task 工具派发一个 general 子 Agent）：

```
用 task 工具派发一个 general 子 Agent，给它这个完整指令：

"""
你是一个测试执行子 Agent。严格按以下步骤：
1. 读取 docs/tasks/TEST/input.md
2. 在 docs/tasks/TEST/ 下产出 method-b-result.md，内容包含：
   - Header（phase: TEST, task_id: TEST, trace_id: TEST-B-{今天日期}）
   - 正文写：已读取 input.md，共 N 行（N 是实际行数）
3. 只返回两行给我：
   - 产出文件路径
   - 一句话摘要（不超过 30 字）
绝对不要把 input.md 或 method-b-result.md 的全文返回给我。
"""
```

### 1.2 关键观察（主 Agent 必须如实记录）

**观察点 A：主 Agent 是不是真的派发了 task 工具？**
- 看 OpenCode 是否启动了一个子 session
- 还是主 Agent 自己读了 input.md、自己写了 result（没派发）？

**观察点 B：子 Agent 是否在独立上下文执行？**
- OpenCode TUI 是否出现子 session（可用 session_child_first 进入查看）

**观察点 C：返回是否精简？**
- 主 Agent 收到的返回是不是只有"路径+摘要"两行
- 还是把文件全文也拉回来了

### 1.3 验证产出

```bash
cat docs/tasks/TEST/method-b-result.md
```

期望：文件存在，有 Header，正文写明行数。

### 结果记录 Phase 1
- [ ] 观察点 A：主 Agent 是否派发 task 工具？（是/否，否则说明它自己干了）：____
- [ ] 观察点 B：子 Agent 是否独立 session？（是/否）：____
- [ ] 观察点 C：返回是否只有路径+摘要？（是/否，否则说明全文被拉回）：____
- [ ] method-b-result.md 是否产出且含 Header？：____

---

## Phase 2：方法 A 验证（自定义角色，锦上添花）

仅在 Phase 1 通过后执行。验证 OpenCode 自定义 subagent 是否可用。

### 2.1 创建测试角色（markdown 方式，规避 issue #29616）

```bash
mkdir -p .opencode/agents
cat > .opencode/agents/test-echo.md << 'ROLE'
---
description: 测试子 Agent，读文件并返回路径加摘要
mode: subagent
temperature: 0.1
tools:
  read: true
  write: true
  bash: false
---

你是一个测试子 Agent。任务：
1. 读取 prompt 里给你的文件路径
2. 在 docs/tasks/TEST/ 下产出 method-a-result.md，
   含 Header（phase: TEST, task_id: TEST, trace_id: TEST-A-日期）
   正文写：已读取 {文件名}，共 N 行
3. 只返回两行：产出文件路径 + 一句话摘要（不超过 30 字）
绝不返回文件全文。
ROLE
echo "test-echo.md 已创建"
```

### 2.2 确认 OpenCode 识别了角色

```bash
opencode agent list
```

期望输出里能看到 `test-echo`，mode 为 `subagent`。
**如果看不到 → 自定义角色这条路不通（可能踩 #29616），但不影响 v4（方法 B 已通）。直接跳到最终判定，标注方法 A 不可用。**

### 2.3 派发自定义角色

在 OpenCode 里对主 Agent 说：
```
用 task 工具派发 test-echo 子 Agent，让它读取 docs/tasks/TEST/input.md，
按它的角色定义产出结果。
```

或手动 @ 提及：
```
@test-echo 读取 docs/tasks/TEST/input.md 并产出结果
```

### 2.4 验证产出

```bash
cat docs/tasks/TEST/method-a-result.md
```

### 结果记录 Phase 2
- [ ] opencode agent list 是否显示 test-echo？：____
- [ ] 主 Agent 能否派发 test-echo？（是/否）：____
- [ ] method-a-result.md 是否产出？：____
- [ ] 若失败，失败现象：____

---

## Phase 3：上下文隔离验证（核心）

这一步验证 v4 解决"上下文爆炸"的核心机制是否真的生效。

### 3.1 大文件测试

造一个较大的输入文件（模拟真实场景的大内容）：
```bash
for i in $(seq 1 500); do echo "这是第 $i 行测试内容，用来模拟一个较大的文件，验证内容不会被拉进主 Agent 上下文。"; done > docs/tasks/TEST/big-input.md
wc -l docs/tasks/TEST/big-input.md
```

### 3.2 派发处理大文件

用方法 B（或方法 A 如果可用）派发子 Agent 处理 big-input.md，产出摘要文件。

### 3.3 关键判断

派发完成后，主 Agent 自我检查并记录：
- 主 Agent 的上下文里**有没有出现 big-input.md 的具体内容**（那 500 行）？
- 还是只有子 Agent 返回的"路径 + 一句话摘要"？

**这是 v4 价值的最终验证**：如果大文件内容没进主 Agent 上下文，说明上下文隔离真的生效，v4 解决了最初的问题。

### 结果记录 Phase 3
- [ ] big-input.md 创建（500 行）：____
- [ ] 主 Agent 上下文是否避开了 500 行内容？（是=隔离成功/否=隔离失败）：____

---

## 最终判定

根据各 Phase 结果，给出结论：

### 判定矩阵

| 场景 | Phase 1 (方法B) | Phase 2 (方法A) | Phase 3 (隔离) | 结论 |
|------|----------------|----------------|---------------|------|
| 理想 | ✅ | ✅ | ✅ | v4 完全可用，两种角色方式都行 |
| 可用 | ✅ | ❌ | ✅ | v4 可用，用方法 B（prompt 注入角色）|
| 需调整 | ⚠️主Agent不派发自己干 | — | — | 派发指令不够强，需在主 Agent system prompt 写死"必须 task 派发" |
| 不可用 | ❌ | ❌ | — | 平台 subagent 机制有问题，考虑代码框架（Claude Agent SDK）|

### 最终结论
- [ ] 判定场景：____
- [ ] v4 是否可投入真实任务：____
- [ ] 若需调整，具体调整方向：____

---

## 清理（验证完成后）

```bash
rm -rf docs/tasks/TEST
rm -f .opencode/agents/test-echo.md   # 若 Phase 2 创建了
```

---

## 验证通过后的下一步

如果判定为"可用"或"理想"：

1. 用真实角色跑一个真任务的单个阶段——比如让 analyst 角色对一个小需求产出 P1-problems.md
2. 确认产出质量和 Header 规范
3. 再串两个阶段（P1→P2），验证主 Agent 的门槛判定和状态更新
4. 跑通后，按 loop-orchestration.md 的档位 A→B→C 渐进，最终实现 /loop 自动编排

**不要跳过这个渐进过程。** 每一步证明可靠，再串成自动循环。

---

*验证方案，配合 docs/process/workflow-v4/ 使用*
