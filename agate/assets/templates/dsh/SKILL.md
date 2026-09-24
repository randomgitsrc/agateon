---
name: agate-protocol
description: Agateon 协议的 DSH 适配层——工具映射、平台注意、并行派发与独立 judge 的 DSH 原生食谱。由 Agateon 编排者（agent-preset）加载使用；也可供任何想在 DSH 上跑 Agateon 任务的 agent 加载。
---

# Agateon × DSH 适配层

> 协议本体位置由 `agate-resolve.py` 运行时解析得到（通常 `~/.agate/current/agate`；`~/.agate` 是**版本根**，其下才有 `vX.Y.Z/`）。本 skill 不改协议任何文件，也不复制协议内容——它只回答一件事：
> **在 deepseek-harness 上，怎么把 Agateon 的编排纪律映射到 DSH 的工具面。**

## 何时加载

- 你是 Agateon 编排者（preset persona 已要求你执行 orchestrator-template.md）→ 已自动获得工具映射，本 skill 补充进阶食谱
- 你想在 DSH 上手动跑 Agateon 任务（未用 preset）→ 加载本 skill；先按下方「工具映射」指引取工具面，再按 `{agate_root}/orchestrator-template.md` 执行

## 工具映射

**单一来源在 `agent.cordis.yml` 的 persona**（会话开始即加载，保证"未加载本 skill 也有映射"）——本 skill **不再复述**，避免两处维护漂移。本 skill 只补充 persona 没有的**进阶食谱**与平台注意。

> 若你是在**没有 preset** 的环境下手动加载本 skill：先读 `{agate_root}/assets/templates/dsh/agent.cordis.yml` 的 `persona.config.prefix` 取工具映射，再按 `{agate_root}/orchestrator-template.md` 执行。
>
> （2026-09-24 修正：此前这里还给出过"安装后位置"的路径（版本根下的 preset 目录）——DSH ≥0.1.7-alpha.1 起**不再读取**该目录，`agate-setup.py` 也不再创建它，那个基路径对新装环境是**悬空**的。现在 preset 由 profile 的 `cordis.patch.yml` 里一条声明行承载，工具映射的权威来源就是上面这个模板文件。）

## DSH 原生进阶食谱（其他平台没有的能力）

### 食谱 1：批量并行派发（对应 dispatch-protocol 五模式编排的 parallel）

P3 红灯批 / P4 实现批需要多路并行时，用 `workflow` 脚本替代手写多路 subagent：

```js
// 示例：P3 五批并行 TDD 红灯
const items = await args.items; // 批次清单（路径数组）
const results = await parallel(items.map((item) => async () =>
  await agent(`你是 test-designer。角色定义：读 {agate_root}/assets/execution-roles/test-designer.md。任务：${item}。只返回路径+一句话摘要。`, { label: item })
));
return results;
```

约束：workflow 是 worker 线程 JS，**无文件系统/网络 API**——状态读写必须由子 agent 完成，脚本只做编排与结果汇总。

### 食谱 2：独立 judge（对应独立 Judge 机制提案）

judge 需要 fresh context（只看标准、不看实现者自述）——DSH 有两种原生实现：

- **`ralph`**（推荐）：每轮全新 agent，只传 objective + 上一轮 bounded 报告——天然满足"fresh context + 信息隔离"
- **`subagent`（spawn，不 fork）**：全新上下文，手动控制注入内容

```js
// ralph 作为 judge：objective = "独立复核任务 Txxx 的 P6 验收证据…"
// 每轮新 agent 只拿到客观标准与证据路径，拿不到实现者自述
```

### 食谱 3：跨轮续跑（崩溃恢复增强）

- `goal` 工具：把"完成 Txxx 的 P0-P8"固化为持久目标，DSH 自动续轮；中断后从 `.state.yaml` 记录的 phase 恢复
- 与 Agateon 自身的"状态落盘"正交：goal 是运行时能力，状态文件仍是权威

### 食谱 4：实时 gate（session hooks）

- 除 git hook（pre-commit 等）外，DSH 支持 PostToolUse 类 session hooks——可在每步工具调用后自动跑 `check-gate.py`。实现方式：PostToolUse 类 session hooks 经 DSH `hooks-claude-code` 配置或强类型 agent 扩展点实现（见 DSH 代码 `packages/hooks/`）
- 比"commit 时才拦"更早暴露状态漂移

## 平台注意（DSH 特有，务必遵守）

1. **沙箱只读区**：DSH 默认 workspace-write，只覆盖会话工作区。协议本体目录（`{agate_root}`）对沙箱**只读**——gate 脚本若写仓库内文件会 `Errno 30`。任务工作区放可写位置（如 `dsh-workspace` 下）
2. **/tmp 只读**：pytest 等需要临时目录的工具要用 `--basetemp` 指向可写目录（`TMPDIR` 环境变量亦可）
3. **审批策略**：审批被禁用时沙箱拒绝即终局，不可升级——gate 命令设计成不触发需审批的操作
4. **bash 纪律**：长命令外层 `timeout`；读文件用 read/grep/glob 工具而非 bash（避免 bash 挂起）

## 验证清单（接入后第一次跑任务前）

- [ ] `python3 ~/.agate/scripts/agate-summary.py` 输出协议版本
- [ ] `python3 ~/.agate/scripts/agate_common.py` 输出 AGATE_WORKSPACE
- [ ] 能读到 `{agate_root}/phase-cards/P0-orchestrator.md`
- [ ] 派发一个空跑 subagent 成功（验证 subagent 工具可用）
- [ ] `check-gate.py P1` 在无任务时行为符合预期（exit 2 语义）
