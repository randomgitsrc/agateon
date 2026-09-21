---
name: agate-protocol
description: Agateon 协议的 Codex 适配层——Codex 工具映射、「必须显式要求派发」硬约束（multi_agent_mode 默认禁止派发）、平台注意与验证清单。
---

# Agateon × Codex 适配层

> 协议本体位置由 `agate-resolve.py` 运行时解析得到（通常 `~/.agate/current/agate`；`~/.agate` 是**版本根**，其下才有 `vX.Y.Z/`）。
> 本 skill 不改协议任何文件，也不复制协议内容——它只回答一件事：
> **在 codex-cli 上，怎么把 Agateon 的编排纪律映射到 Codex 的工具面。**

## 第一步（必须）：取协议根，读权威行为规范

1. 跑 `python3 ~/.agate/scripts/agate-resolve.py`，从输出读 `AGATE_ROOT=`（该脚本按项目 `.agate-version` 解析版本；无声明回退全局 `current`）
2. 读 `{agate_root}/orchestrator-template.md` 并严格遵守——它是**唯一**权威行为规范（职责边界、「只有你能写的文件」表、会话开始步骤、阶段卡片映射、Fallback 清单全在其中）
3. 本 skill **不复制**模板内容；模板随版本升级自动更新

> **接入步骤**见 `{agate_root}/SETUP.md`「步骤 2-Codex」；日常接入用 `python3 ~/.agate/scripts/agate-setup.py`（本 skill 会装到 `~/.agents/skills/agate-protocol/`）。

## 何时加载

- 你要在 Codex 上跑 Agateon 任务（P0-P8）→ 加载本 skill
- 你要把 Agateon 阶段派发到 Codex 子进程（`agate dispatch route` 路由）→ 本 skill 说明 Codex 侧的工具面与判成败方式
- 首次接入后验证 → 见末节「验证清单」

## ⚠️ 必须显式要求派发（Codex 特有硬约束）

Codex 的会话上下文含一段 `<multi_agent_mode>`，其默认语义是：

> Do not spawn sub-agents unless the user or applicable AGENTS.md/skill instructions explicitly ask for sub-agents, delegation, or parallel agent work.

**Agateon 的整个模型建立在「主 Agent 派发 subagent」之上**——主 Agent 不亲自写阶段产出物，而是把 P1-P8 各阶段派发给独立上下文的 subagent。

**因此**：在 Codex 上跑 Agateon 任务时，**prompt / 项目 `AGENTS.md` / 本 skill 必须显式写明"要求派发 subagent"**；否则 orchestrator 不会派发，P0-P8 流程直接失效（不报错，只是静默不派发）。

**写法示例**（放进项目 `AGENTS.md` 或首轮 prompt）：

```text
本项目使用 Agateon 协议编排。要求：主 Agent 必须按 Agateon 的阶段派发规则
使用 spawn_agent 派发 subagent 执行各阶段，不得亲自撰写阶段产出物。
```

## 编排者四项职责 × Codex 工具

| Agateon 职责 | Codex 工具 | 注意 |
|------------|-----------|------|
| 读状态 | 文件读取工具 | 协议/任务状态都在文件里，直接读 |
| 派发 subagent | `spawn_agent` / `followup_task` / `send_message` / `wait_agent` | 原生多 agent 团队，4 并发槽；须先满足上节「显式要求派发」 |
| 跑 gate | shell 执行 | 以退出码判定；**但 Codex 的进程退出码不可靠**（见下节），须解析 `--json` 事件流 |
| 更新状态 | 文件写入工具 | 改 `.state.yaml` + `active-tasks.md` |

## 平台注意（Codex 特有，务必遵守）

1. **退出码不可靠**：未认证（反复 401 重试）与「账号不支持所配 model」两类失败都可能落在 `exit 0` 的进程里——**判成败须解析 `--json` 事件流**（`turn.failed` / `item.type == "error"`），不只看退出码
2. **非 git 仓库默认拒绝**：需 `--skip-git-repo-check`
3. **沙箱与审批**：`--dangerously-bypass-approvals-and-sandbox` 跳过全部确认且无沙箱，**仅用于外层已隔离环境**；中间档用 `-s/--sandbox <read-only|workspace-write|danger-full-access>`
4. **过期写法**：`--full-auto` / `-a` 已从 `codex exec` 移除，旧资料里的「`-a never -s workspace-write` 折中」写法不再适用
5. **model 阵容依账号类型而异**：ChatGPT 登录账号与 API key 账号可用 model 不同；换账号后先跑一次 `codex exec --json -m <model>` 确认

## 验证清单（接入后第一次跑任务前）

- [ ] `python3 ~/.agate/scripts/agate-summary.py` 输出协议版本
- [ ] 能读到 `{agate_root}/phase-cards/P0-orchestrator.md`
- [ ] 在本项目跑 `codex exec --json --skip-git-repo-check '用一句话说明当前任务状态'`，**解析事件流**确认 `turn.completed`（而非仅看退出码）
- [ ] 确认 prompt / `AGENTS.md` 中已有「要求派发 subagent」的显式声明（否则 P0-P8 不派发）
