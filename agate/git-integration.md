# Git 集成：状态落盘的持久化

> Agateon 定义"状态文件何时入 git"——这是状态落盘真正生效的保证

---

## 为什么这是必要机制，不是可选项

Agateon 的核心是"状态落盘 + 抗中断恢复"。但有个隐含前提：**这些落盘的文件什么时候提交到 git？**

如果不提交：
- 状态文件只在本地，会话崩溃 / 环境重置后**全部丢失**——抗中断设计失效
- 多 agent 协作时（一台机器多个 agent），其他 agent pull 不到当前进度，重复劳动或冲突

所以 git commit 是状态落盘机制的**必要组成部分**，不是额外的运维步骤。

---

## 三条规则

### 规则 1：commit 由主 Agent 做，不是 subagent

subagent 在独立上下文里只负责产出文件，**不碰 git**。commit 是编排层（主 Agent）的职责。

如果每个 subagent 自己 commit，会产生混乱的提交历史，且 subagent 不知道全局状态，无法写出有意义的 commit message。

### 规则 2：一个阶段 = 一个 commit

不是每个 subagent 的中间操作都 commit（噪音太多），也不是整个任务才 commit 一次（中途崩溃丢进度）。

**粒度：每个阶段门槛通过后，主 Agent commit 一次。** 一个 Pn 阶段的产出是一个原子的进度单位。**这个规则由 `check-gate.py` 强制执行**——每个阶段的 gate 检查该阶段产出是否合格。产出和 .state.yaml phase 更新在同一个 commit 里。

**phase 字段语义（消除"提前写"歧义）**：`.state.yaml` 的 `phase` 字段 = **本 commit 提交的产出阶段**，不是"当前进展到哪"。commit 时 phase 写该阶段（如提交 P5 产出 → phase=P5），**不得提前写下一阶段**。否则 P5 的合法产出（如 `P5-test-results/fail-list.txt`）会在 phase=P6 的 commit 里被 P6 的 self-authored gate 硬拦截（P6 拦截"非证据文件"以防验收阶段改代码）。

**特例**：唯一例外是**同一 commit 里同时提交上一阶段产出 + 下一阶段已就绪的产出**（如 P1 产出 + P2 产出都完成时一次 commit，phase 写 P2）——此时 phase 反映"commit 里最晚的产出阶段"，且必须所有产出都过了各自 gate。**该特例不适用于 P5→P6 边界**（P6 self-authored gate 硬拦截非证据文件，P5 产出必须留在 phase=P5 的 commit）。

```
P2 门槛通过（status==approved）→ 主 Agent commit
  message: "wf(TAG0001-P2): 方案设计通过 — schema_version 表 + 顺序迁移脚本"

P5 门槛通过（failed==0）→ 主 Agent commit
  message: "wf(TAG0001-P5): 验证通过 — 23 测试全绿，P1 问题 5/5 解决"
```

commit message 格式：`wf({task_id}-{phase}): {一句话进度}`，可追溯。

> 注：`wf()` 前缀是 agate 工作流进度提交的专用约定，与项目现有的 Conventional Commits（`feat:`/`fix:`/`docs:` 等）**并行使用，不冲突**。

**两种前缀的判定标准（消除"常规变更"这种模糊说法）**：

| commit 内容 | 前缀 | 例子 |
|---|---|---|
| 某个阶段门槛刚通过，记录"进度到哪了" | `wf({task_id}-{phase}):` | `wf(TAG0001-P2): 方案设计通过` |
| 任务全部完成（P8 之后）或某阶段产出的代码本身，描述"做了什么功能/修了什么问题" | `feat({task_id}):` / `fix({task_id}):` | `feat(TAG0001): 用户管理 API+CLI` |
| 和具体任务无关的变更（依赖升级、格式化、临时脚本）| 标准 Conventional Commits，不带 task_id | `chore: 升级 pytest` |

**实测验证**（实际项目历史 commit 抽样核实）：阶段记录类 commit 基本都正确使用了 `wf()`；功能描述类 commit（即使在同一任务里）自然倒向了 `feat(Txxx):`，这恰好印证了上面的判定标准——**两种前缀本来就对应两种不同的 commit 意图，不是"漏用"，是约定一直隐含存在，只是之前没有写清楚**。本节的修订是把这个隐含约定显式化，不是改变实际行为。

### 规则 3：push 分档位，且 push 前必须 pull --rebase

push 涉及和远端同步，多 agent 并发 push 会频繁冲突。不该每个 commit 都立即 push。

```
档位 A/B（手动/半自动）：
  - 每个任务完成（P8 gate 通过、进入 READY）后 push 一次
  - 或用户明确要求 push 时

档位 C（/loop 全自动）：
  - 默认每个任务完成时 push
  - 可配置 --push-every-phase 改为每阶段 push（多 agent 需要实时同步时）

push 前必须：git pull --rebase origin main
push 失败（远端有新提交）→ pull --rebase → 重新 push，最多重试 3 次
  → 仍失败 → PAUSED 报告人工（可能有冲突需要手动解决）
```

---

## 多 Agent 并发的特别说明

一台机器多个 agent 同时跑不同任务时，git 是共享的。冲突主要来自：

1. **active-tasks.md 并发修改**：多个 agent 同时更新看板 → 冲突高发
2. **同时 push**：A push 成功后 B push 被 reject

### 缓解策略

**策略 1：任务目录隔离**
每个任务的产出在自己的 `{AGATE_WORKSPACE}/tasks/{Txxx}/` 目录，不同任务的 agent 改不同目录，文件级冲突少。

**策略 2：active-tasks.md 只改自己任务那一行**
看板更新：owner agent 从该任务 `.state.yaml` 派生，**只重写自己负责的那一行**，不整体重写，不碰其他任务的行。`.state.yaml` 是唯一真相源，active-tasks.md 是派生视图。（与 state-machine.md 一致）

**策略 3：push 串行化（推荐）**
多 agent 环境下，push 操作天然串行（git 远端是单点）。每个 agent push 前 pull --rebase，失败就重试。这是 git 的标准并发模型，能 work，只是偶尔要重试（本项目开发过程中已多次验证：rebase 后重推即可）。

**策略 4：高并发时考虑分支**
如果 agent 数量多、冲突频繁，可以每个任务用独立分支，完成后合并。但这增加复杂度，单机 5 个 agent 的规模用 main + rebase 通常够用。

---

## commit/push 在状态机里的位置

```
主 Agent 单步函数（见 state-machine.md），补充 git 步骤：

function 执行一步(task_id):
    1. 读 active-tasks.md → 当前状态
    2. 确认输入就绪
    3. 派发 subagent
    4. 接收返回 + 校验
    5. 判定门槛
    6. 更新 .state.yaml phase（先更新再 commit）
    7. git commit（规则 2：一阶段一 commit）
       git add {AGATE_WORKSPACE}/tasks/{task_id}/ {AGATE_WORKSPACE}/tasks/active-tasks.md
       （.state.yaml 在 {AGATE_WORKSPACE}/tasks/{task_id}/ 下。若项目 .gitignore 忽略 .state.yaml，需 git add -f）
       git commit -m "wf({task_id}-{phase}): {摘要}"
    8. 按档位决定是否 push（规则 3）
       if 该 push:
           git pull --rebase origin main
           git push（失败则 rebase 重试，最多 3 次）
    9. 返回下一状态
```

---

## 异常处理

| 异常 | 处理 |
|------|------|
| commit 失败（无改动）| 跳过，可能是 subagent 没产出文件，回到门槛检查 |
| push reject（远端更新）| pull --rebase → 重推，最多 3 次 |
| rebase 冲突 | PAUSED，报告人工（自动解冲突风险高，不做）|
| 3 次重推仍失败 | PAUSED，报告人工 |

**rebase 冲突绝不自动解决**——自动解冲突可能丢数据。遇到冲突就停下来交给人。

---

## 与"抗中断恢复"的闭环

git 集成让状态落盘真正闭环：

```
状态写入文件（state-machine）
    ↓
每阶段 commit（git-integration）← 持久化到版本库
    ↓
会话崩溃 / 环境重置
    ↓
重新 clone / pull → 状态文件完整恢复
    ↓
读 active-tasks.md → 接着上次的阶段继续
```

没有 git 集成，"状态落盘"只是写本地文件，崩溃就丢。有了它，状态真正持久、可恢复、可多 agent 共享。

---

## commit 会触发 pre-commit 检查（自 v0.4 起，持续生效）

git 集成除了"把状态落到版本库"，还承担一层角色：**阶段 commit 会触发一组 pre-commit 检查**——把
已有的状态机 gate 自动化到 commit 入口（即使主 Agent 忘了跑，hook 也会跑；即使造假，CI backstop
会重跑）。

**检查清单是活的，不在本文件维护副本**——完整、当前的 pre-commit 检查集（脚本名 / 触发条件 /
拦截行为）见 `WORKFLOW.md`「Pre-commit 检查总览」表（唯一事实源）。要点：`.state.yaml` 格式关 →
gate 通过关 → 状态转移·重试上限·裁剪·SCOPE+·provenance 审计等合规关，任一 `exit 1` 中止 commit，
`exit 2` 是警告不阻塞。

**`--cached` vs `HEAD~1`**：pre-commit hook 运行时 commit 尚未创建，所有 `git diff` 必须用
`--cached`（暂存区 vs HEAD），不能用 `HEAD~1`。主 Agent 手动验证（commit 后）可用 `HEAD~1`，但
hook 场景下 `--cached` 是唯一正确选择。

**commit 里一并暂存的东西**：阶段产出文件 + `.state.yaml`（phase = 本 commit 产出阶段）+
`active-tasks.md` 自己那一行 + **`gate-events.jsonl` 事件账本**（`gate_run` / `state_transition` /
`judge_verdict` / `dispatch_route` 追加行，pre-commit hook 会追加、随本 commit 一起入库；哈希链由
`check-events.py` 审计）。

**SELF-GATE trailer（改 Agateon 协议本体 / 脚本时）**：暂存区含 `agate/*.md` / `agate/scripts/*` /
`agate/**/*.md` / `agate/rules/*.yaml` 等 self-gate 触发文件时，commit message 须含
`self-gate-review: <审查文件路径>` 或 `self-gate-skip: <理由>`——`commit-msg` hook 检查（缺失 WARNING，
不硬拦截）。触发面与流程见 `SELF-GATE.md`。

**发布 PR 必须普通 merge（`--no-ff`），禁止 squash**：CHECK 7（version badge ↔ git tag）与 G-5 发布
验证都用 `git describe --tags --abbrev=0` 取最新 tag；squash 生成 SHA 不同的新提交，tag 与 main
分叉、describe 回退旧版。若确实用了 squash：`git tag -f vN.N.0 <main-commit> && git push origin
vN.N.0 --force`。

**禁止 `--no-verify` 绕过 hook**：CI backstop 会重跑 `check-gate.py` + `check-p6-provenance.py` +
`check-events.py` + git blame 单 author WARNING，绕过 hook 的 commit 会被抓到并在日志暴露。详见
`LIMITATIONS.md` 局限 3。

**P6 单 author WARNING**：当 `P6-acceptance.md` git blame 显示只有一个 author（通常是主 Agent 自写
而非独立 verifier），CI 会发 WARNING——provenance 客观审计之外的最后一层可观测性兜底。

---

*git 集成是状态落盘机制的必要组成部分，配合 state-machine.md 和 loop-orchestration.md*
