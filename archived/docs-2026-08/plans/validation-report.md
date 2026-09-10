# Workflow v4 派发机制验证报告

> 验证日期：2026-06-12
> 验证者：OpenCode Agent
> 验证目的：验证 v4 的派发机制（继承自 v3）在 OpenCode 上是否可用
> 说明：v4 沿用 v3 的派发内核，本报告的验证结论对 v4 同样有效

---

## 验证结果总览

| Phase | 内容 | 结果 |
|-------|------|------|
| Phase 0 | 准备测试数据 | ✅ 通过 |
| Phase 1 | 方法 B 验证（派发机制） | ✅ 通过 |
| Phase 2 | 方法 A 验证（自定义角色） | ❌ 失败 |
| Phase 3 | 上下文隔离验证 | ✅ 通过 |

**最终判定**：✅ **v4 派发机制可用**（使用方法 B）

---

## 详细验证结果

### Phase 1：方法 B 验证（派发机制）

**目标**：验证主 Agent 会派发 subagent，而不是自己干到底

**操作**：
- 用 task 工具派发 general subagent
- 要求子 Agent 读取 input.md，产出 method-b-result.md

**结果**：

| 观察点 | 结果 |
|--------|------|
| 主 Agent 是否派发 task 工具？ | ✅ 是 |
| 子 Agent 是否独立 session？ | ✅ 是 |
| 返回是否只有路径+摘要？ | ✅ 是 |
| 产出文件是否含 Header？ | ✅ 是 |

### Phase 2：方法 A 验证（自定义角色）

**目标**：验证自定义 subagent 是否可用

**操作**：
- 创建 .opencode/agents/test-echo.md
- 尝试用 task 工具派发 test-echo

**结果**：
- `opencode agent list` 能看到 test-echo ✅
- task 工具派发时报错：`Unknown agent type: test-echo is not a valid agent type` ❌

**原因**：OpenCode issue #29616 — task 工具的 subagent_type 枚举硬编码，不支持自定义 agent

### Phase 3：上下文隔离验证

**目标**：验证 500 行大文件不会进入主 Agent 上下文

**操作**：
- 创建 500 行的 big-input.md
- 派发子 Agent 处理，产出 big-result.md

**结果**：

| 观察点 | 结果 |
|--------|------|
| 大文件创建（500 行） | ✅ |
| 主 Agent 上下文是否避开 500 行？ | ✅ 是（只收到摘要） |

---

## 方法 B 是否会导致上下文混乱？

用户提问：**使用内置 general subagent + prompt 注入角色，是否会因注入角色导致主 Agent 存储过多角色信息，导致上下文混乱？**

**分析**：

1. **角色信息大小**：一个角色定义文件通常几百字（如 architect.md 约 2KB）
2. **注入方式**：prompt 里只写文件路径，不塞内容（如"读取 docs/process/workflow-v4/assets/execution-roles/architect.md"）
3. **子 Agent 独立执行**：角色信息只进入子 Agent 上下文，不污染主 Agent

**结论**：不会导致上下文混乱。

- 主 Agent 只传**路径**（几个字），不传角色全文
- 子 Agent 在独立 session 里读取角色文件，主 Agent 上下文不受影响
- Phase 3 已验证：500 行大文件都没进入主 Agent上下文，几百字的角色文件更不会

---

## 建议

### 1. 使用方法 B 作为主路径

- 用内置 `general` subagent + prompt 注入角色
- 跨平台可用，不踩 issue #29616
- 完全满足 v4 的派发需求

### 2. 角色定义文件路径标准化

在派发 prompt 中统一使用：
```
角色定义：读取 docs/process/workflow-v4/assets/execution-roles/{role}.md
```

### 3. 验证通过后的下一步

1. 用真实角色跑一个真任务的单个阶段（如 analyst 产出 P1-problems.md）
2. 确认产出质量和 Header 规范
3. 串两个阶段（P1→P2），验证门槛判定和状态更新
4. 最终实现 /loop 自动编排

---

## 判定矩阵

| 场景 | Phase 1 (方法B) | Phase 2 (方法A) | Phase 3 (隔离) | 结论 |
|------|----------------|----------------|---------------|------|
| 实际结果 | ✅ | ❌ | ✅ | 可用 |

**v4 派发机制可以投入使用，使用方法 B。**

---

*验证完成，报告生成于 2026-06-12*