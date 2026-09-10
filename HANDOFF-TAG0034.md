# TAG0034 交接单 — 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）

> 本交接单供 worktree session 的 agent 按此启动 TAG0034 任务。
> 任务已 P0 立项（`.state.yaml` phase=P0，`P0-brief.md` 已就绪，含 2026-09-09 讨论定案）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0034**：在 agate 协议层落地派发路由设计（RM-AG0060 epic）。

**一句话**：新增**项目级**配置文件 `agate-workspace/dispatch-routing.yaml`（对齐
`agate-workspace/maintainability.yaml` 先例：项目级、全兜底、非协议本体、不受 SELF-GATE），按
`(phase, role)` 声明候选 `{cli, model, effort?}` 或引用命名**档位**；主 Agent 到某阶段派某角色时
**查表 → 直接派首选候选 → 仅基础设施失败（起不来 / auth/网络/429 / 无可解析产出）才逐级回落 →
全落空则默认派发（同平台同 model，恒等于本机制未启用）**——**无 probe**（try-and-fall）。`cli` 可为
`native`（同厂商换 model，**弱缓解**）或另一 CLI（`claude-code`/`codex`/`opencode` 起子进程，**强缓解**）。
新增 `dispatch_route` 事件带理由码留痕。**gate / 状态机 / `phases.yaml` 全不动**——gate 只认产出文件
和 exit code、不认「谁生产的」，这条解耦是设计成立的前提。存活/卡死检测复用 RM-AG0055 命令流机制
（+ 子进程形式的 `wait(pid)` / `kill -0`），不自造超时。动机 = 给角色隔离补模型维度、部分缓解
`LIMITATIONS.md` 局限 2（同源模型系统性盲区，现状 ADR-006 无解）。

**epic 形态**：一个 task 内分 **P4a / P4b / P4c 串行子批**（`dispatch_plan: {mode: static-batch,
batches: [P4a, P4b, P4c], serial}`）；P2 若判需再拆多 TAG 则另起。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0034` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agateon`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → `/home/kity/oclab/agateon/agate`，稳定版） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片 / 跑派发类工具用它 |

**核心原则**：

- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- **⚠️ gate 工具 ≠ 检查对象**：
  - commit hook 的 gate **判定工具**用 `~/.agate`（稳定版）
  - `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`）——检查对象是 worktree 里改动的 `dispatch-protocol.md` / `SETUP.md` / `phases.yaml`(或 rules 新文件)
  - `agate-summary.py` 在 worktree 跑显示**主 checkout 上下文**，不代表 worktree 状态——用 `git log`/`git status`
  - **所有编排/派发类工具脚本**（`agate-inject-card.py` / `agate-render-dispatch-prompt.py` / `agate-next.py` / `agate-dispatch.py` 等）用 `~/.agate/scripts/` 稳定版调用（TAG0016 教训：worktree 相对路径调用会读到 worktree 正在被修改的协议卡片副本）
  - ⚠️ **本任务在改 `agate-dispatch.py` 本身**——改完后测试用 worktree 的版本跑，但**编排流程（派发下一阶段 subagent）仍用 `~/.agate` 稳定版的 `agate-dispatch.py`**，避免「用未验证的新派发逻辑派自己」
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 实际在 `/home/kity/oclab/agateon/.git/hooks/`（pre-commit/commit-msg/pre-push 已软链安装）。worktree commit 自动触发。

**已完成的 setup（worktree 已可独立使用）**：

- 依赖齐全：bash 5.2.21 / python 3.12.3（`/usr/bin/python3`）/ pyyaml / pytest 9.0.3 / shellcheck / ruff（`~/.local/bin/ruff`）
- 基线验证：**全绿**——unit 1390 passed + 2 skipped / regression 29 / integration 94；consistency `--strict-errors-only` 0 ERROR（存量 329 WARNING 全为历史叙事文件死链，与本任务无关）
- commit hook：指向 `~/.agate`（稳定版），worktree commit 自动触发
- orchestrator 注册：`.opencode/agents/orchestrator.md` + `.claude/agents/orchestrator.md` → `~/.agate/orchestrator-template.md`（符号链接，双平台）
- 工作区解析：`agate_common.py` 输出 `.../​.worktrees/agate-TAG0034/agate-workspace/`
- 任务数据：`TAG0034-dispatch-routing/` 有 `P0-brief.md`（25779 字节，含 2026-09-09 定案）+ `.state.yaml` phase=P0 + `gate-events.jsonl`（哈希链干净，2 事件基线）

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

> 权威源是 `agate-workspace/tasks/TAG0034-dispatch-routing/P0-brief.md`。以下为提要，冲突以 P0-brief 为准。

### P1/P2 必须先定掉的设计类待确认（P1 不定死会导致 P2/P4 返工）

1. **配置分层与落点**（design-note §2.1 现存缺口——把文件放 `agate/rules/` 又称「非协议本体」自相矛盾）。三层：
   ① 协议本体（`agate/rules/` 或 `phases.yaml` 旁）= 档位词表 + 语义画像 + 出厂默认（全 `standard`），**走 SELF-GATE**；
   ② 机器/安装级 = 档位→具体 `[{cli,model,effort}]` 有序候选链绑定，落 `~/.config/agate/` 类**非版本控制**路径，SETUP 流程 scaffold；
   ③ 项目级 `agate-workspace/dispatch-routing.yaml` = `(phase,role)`→档位映射 + 直接值覆盖，只引用档位名故可移植。
   **MVP 可合并 ①③ 为单文件 + 内联档位定义**；是否真拆机器级文件由 P2 按可移植性需求定。全兜底（缺失/损坏 → 出厂默认 = 现状，不报错不静默跳过，复用 `check-maintainability.py:_load_config` 模式）。
2. **`tier` + `effort` 两个正交轴**：`tier`（`bulk/standard/deep`，名字 P1 定）经机器绑定映射到 `{cli,model}`；`effort`（`low/medium/high` 可选）→ 各平台推理档 flag（Codex `-c model_reasoning_effort=` / `spawn_agent.reasoning_effort` / OpenCode `--variant` / **Claude Code CLI 无旋钮 → 静默忽略 + `platform-notes.md` 注明**）。`standard` **恒等于「继承主 Agent 当前 model 的原生派发」**（保「不配置=逐字节现状」不变量）。写法：`tier: deep, effort: high`（引用）**或** `candidates: [{cli,model,effort}]`（直接值），静态校验器两种都要认。
3. **路由 key = `(phase, role)`，role 层可选**：解析顺序 `(phase,role)` → `phase` → 未配 = `standard`。想让 reviewer 跑异模型显式配 `P4.review`，**不强制分开**。
4. **schema**（已定：无 `fallback` 字段、终点回落恒为默认派发、`tier`+`effort?` 两轴、`(phase,role)` key 且 role 可选；待定：字段名、`{cli: native, model: null}` 是否合法、档位定义块与映射块分隔、`tier`/`candidates` 二选一校验）+ 静态校验器落点（**新增校验器，非 `agate/rules/schema` 下的协议 schema**）。
5. **`dispatch_route` 事件理由码枚举** —— 合法值只有 `launch_fail` / `infra_error` / `no_parseable_output`；**不存在 `gate_fail` 值**（机械强制「gate verdict 不触发换候选」的完整性不变量）。+ `check-events.py` 如何识别新事件类型（不能把未知 event 判为非法）。
6. **决策 CLI 落点**（优先扩 `agate-dispatch.py`，不成再新增 `agate-route.py`）；`cli: native` 的「决策层算目标 model → 启动仍由驱动会话代发」衔接方式（会话侧读什么文件、怎么保证零判断）；与 RM-AG0054 已落地的 `agate dispatch`（渲染 dispatch-context）是串联还是同一步。
7. **retry/回退时的路由**：重新机械查表（落哪个看当时哪个能用），**不做「上次失败所以换更强的」逻辑**。
8. **与既有派发机制的交互**：① 五模式并行批——每个并行 subagent 各自独立解析 `(phase,role)` 路由（同 role 的并行分片用同一条）；② RM-AG0055 自主再派发子任务——倾向「不走路由表、继承父的实际 cli/model」；③ 单 Agent 模式（`has_task_tool:false`）——路由 no-op，显式声明出范围。

### P1/P2 前置真机核实

- **OpenCode 旧 bug②**（父会话交互式切 model 后子代理跟不跟——本会话只机制推断未直接复现）**直接复现测试**
- Codex `spawn_agent` schema：**TAG0033 P6 已直接实测**（引用 `TAG0033/retrospective.md` §一 + `platform-notes.md` Codex 章），不再重测；仅需补 V8（API-key 账号 model 阵容，本机 ChatGPT 账号环境不可得、登记待补、非阻塞）
- **TAG0033 F1/DEBT0035 连带认知**：真机 Codex 把「已结束但非 0 退出」记为 `payload.item.status == "failed"`（带完整 `exit_code`/`completed_at_ms`）——P4b 结构化输出解析判成败时，`codex exec --json` 的 `turn.failed` 与 item 级 `status: "failed"` 是两层，P2 须明确取哪层 + 与退出码不可靠如何叠加

### P4a — 配置路由核心 + `cli: native`

- `agate-workspace/dispatch-routing.yaml`（新，项目级/全兜底/非 SELF-GATE）+ 静态校验器（新增）
- 协议本体侧：档位词表 + 语义画像 + 出厂默认（`agate/rules/` 下新文件或 `phases.yaml` 扩字段，**走 SELF-GATE**）；机器级档位绑定文件 scaffold 接入 SETUP（`agate/SETUP.md` 新小节）
- `agate-dispatch.py` 扩展：读表（按 `(phase,role)` 解析 → 展开 `tier`/`effort` 或直接值为候选链）→ 派首选 → `launch_fail`/`infra_error`/`no_parseable_output` 则逐级回落 → 全落空默认派发 → 写 `dispatch_route`（带理由码）。**无 probe 步骤**；**收到任何 gate 能评产出即停止回落**
- `dispatch_route` 事件：`gate-events.jsonl` 写入端 + `check-events.py` 校验端（复用既有哈希链）；理由码枚举校验（`gate_fail` 非法）；候选回落**不写 `state_transition`、不动 `retries`**
- `cli: native` 执行：Claude Code（Task 单次调用传 `model`，实测生效）+ OpenCode（命名 subagent 配置 `agents.<name>.model` 间接路——需定义 phase→预配命名 agent 的映射 + 预注册机制；v1.18.11 实测生效）
- `dispatch-protocol.md` 新增一节：铁律 1 之前的「查表 → 派首选 → (基础设施失败) 逐级回落 → 再派发」步 + 「gate 判定不认谁生产的」解耦声明 + 「候选回落 ≠ 状态机 retry」「gate FAIL 绝不换候选」两条不变量 + `cli: native` 弱缓解 / 自动化天花板说明

### P4b — 跨 CLI 子进程

- 子进程 spawn：`claude -p --model X --dangerously-skip-permissions` / `opencode run -m provider/model#variant --auto` / `codex exec -m X --dangerously-bypass-approvals-and-sandbox`（三平台本会话均实测跑通；flag 名落地前逐平台对最新官方文档复核，research §10）
- 结构化输出解析判成败：Claude Code `--output-format json`（`stop_reason`/`modelUsage`）、Codex `--json`（`turn.completed` vs `turn.failed`——**退出码对 Codex 不可靠必须解析事件流**）、OpenCode `--format json`（`step_finish.part.reason`）+ 空返回判定
- D2 假完成校验集成——「跑了但无 gate 能评产出」映射为 `no_parseable_output`（回落），「有产出」交 gate（不回落）；`SETUP.md` 各 CLI 自动化环境 flag 小节
- **routed-away judge 的 verdict 校验**（P1 先核实是不是真缺口）：P6.5 judge 若路由到 codex/opencode 子进程，transcript 落非 `~/.claude/` 位置——`check-judge-verdict.py` 的 verdict 定位 + 信息隔离黑/白名单扫描（TAG0033 DEBT0038 同款机制）是否认得跨平台产出的 verdict。真缺口则纳入本任务补上
- `cli: codex` 子进程存活检测走 **TAG0033 已合并的 `CodexAdapter`**（`ADAPTERS["codex"]`，v0.70.0）；claude-code/opencode 走既有适配器 + 子进程 `wait(pid)`/`kill -0`（research §6.0.2）
- 评审打回续跑（design-note §2.4a）：同 target 优先平台官方续接（`--resume` / `codex exec resume` / `opencode -s` / native 的 `followup_task`/`task_id`），失败或换 target 则全新派发——**续接失败无客观信号是已知缺口**，按「续接优先、重起兜底」处理，不假装解决

### P4c — tmux 观测层（能做就做，低优先，可整体切除，不通过不影响 P4a/P4b）

- wrapper：`which tmux` 成功则 `tmux new-session -d -s {agate-task-phase-ts} '{命令} | tee {capture}'`（人看 pane、脚本 tail 文件）；失败裸跑
- session 命名带命名空间；生命周期 = wrapper 自带退出倒计时（N 默认 ~15 可配）→ 自然结束；`list-clients` 非空则不强杀、让倒计时收尾；兜底 `N + 余量` 强杀
- 明确不做：`send-keys` / `capture-pane` 解析给主 Agent / 跨轮复用
- **目标环境 tmux 版本验证若与任务环境不同则停在「定稿 + 待落地验证」、不阻塞 P8**（外部评审 W2）

### 交付物

- **测试**：`agate/tests/` 新增 pytest——schema 校验（两轴 / `tier`vs`candidates` 二选一 / `(phase,role)` key）/ 档位→候选链展开 + `effort` 各平台映射（Claude Code 静默忽略）/ 解析顺序 / 三层配置优先级 + 全兜底 / try-and-fall 逐级回落（各基础设施失败形态）/ **回落非 retry** / **`gate_fail` 非法理由码被拒** / **gate FAIL 不触发换候选（关键完整性用例）** / `dispatch_route` + check-events / `cli: native` 各平台 / 子进程 spawn + 结构化输出解析 / tmux wrapper 生命周期；BDD 以 P1 定稿为准（计划 ≥22 条）；**回归证明 gate/状态机/`phases.yaml` 结构零改动 + 「不配置 = 逐字节现状」**
- **design-note 修订**（本任务交付物，非 out-of-scope）：`design-dispatch-routing.md` 头部「做什么」+ §2.1/§2.2 按定案重写（6 项：三层落点 / try-and-fall / 两轴 / 弱强形 + 自动化不对称 / 两条完整性不变量 / per-machine）；头部「机制现状一句话」同步；`roadmap.md` RM-AG0060 长描述里的旧 `rules/dispatch-routing.yaml` 措辞一并回写。走 docs commit（非 SELF-GATE）

### out-of-scope（P0-brief 已锁）

主 Agent 按任务内容动态选型（§2.2）；会话续接「软信号」根治；第三方终端工具（Herdr/Claude Squad）作依赖；DSH 纳入 CLI 派发路径；局限 3；RM-AG0055 机制/阈值本身；RM-AG0054 `agate next`/`advance` 本身；**派发前空探测（probe）**；**routing 跨机器/团队可复现**（明确 per-machine 机会式）；**retry 时故意换/升档模型**。

### 核心约束（不可违反）

1. **Linux 基线全绿是回归底线**——unit 1390 / regression 29 / integration 94 + consistency 0 ERROR，每步保持
2. **gate / `check-gate.py` / `check-state-transition.py` / `phases.yaml` 结构 / 状态机 零改动**——回归测试必须证明；`dispatch-protocol.md` 新节须显式写「gate 不认谁生产的」
3. **模型购物完整性不变量（最高危）**：候选回落**只**在 `launch_fail`/`infra_error`/`no_parseable_output` 时发生；**收到任何 gate 能评产出即停止回落**；gate FAIL 走正常阶段 retry（同一候选），**绝不换候选**。须有专门回归用例（gate FAIL 后 `dispatch_route` 事件计数不增）
4. **`standard` 语义钉死为「继承主 Agent 当前 model 的原生派发」**——否则出厂默认全 `standard` ≠ 现状、破坏机会式启用不变量
5. **证据强度诚实（外部评审 B1/B2 教训）**：`cli: native` 是弱缓解、`effort` 轴在 Claude Code CLI 基本是空的、OpenCode bug② 是推断未复现——表述不得把 `[自述]`/推断混同为「已实测」
6. **范围锁定**——P1 分析若发现需超出 P0-brief，先停下跟用户确认

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（分片跑，每片外层 timeout，片内 -n auto）
timeout 400 python3 -m pytest agate/tests/unit/ -n auto -q
timeout 400 python3 -m pytest agate/tests/regression/ -n auto -q
timeout 500 python3 -m pytest agate/tests/integration/ -n auto -q

# 一致性（0 ERROR 才行）——⚠️ 用 worktree 自己的脚本
timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck（本任务可能不改 .sh，但结构上跑）
shellcheck -S warning agate/scripts/*.sh

# 事件账本审计（本任务动 gate-events / check-events）
python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing/gate-events.jsonl

# 测试计数（验证文档没漂移）
bash agate/tests/scripts/count-tests.sh

# 单脚本测试（改哪个跑哪个，TDD 先红后绿）——本任务主要：
python3 -m pytest agate/tests/ -k "dispatch or route or events"

# 三 CLI 真机（本机均已装已认证）
claude -p --output-format json --model haiku --dangerously-skip-permissions <<< "ok"
codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "ok"
opencode run --format json --auto <<< "ok"
```

## 5. 阶段推进纪律

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出
- **⚠️ DEBT0037 预警（本任务 static-batch 多提交阶段会命中）**：P4 跨 P4a/P4b/P4c 三批 commit，`check-gate.py P4` 的完整度判据（暂存区有非 md/yaml 文件）在「某批已 commit、暂存区空」时 exit 1、`agate-next.py` 拒绝推进 → 需主 Agent 手动 `_advance`（改 `.state.yaml` phase + `append_event` state_transition）。TAG0033 P4→P5 两次即如此。P2 排期预留这个手动步；若 DEBT0037 在启动前已修复则直接受益
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿。`agate-dispatch.py` / `check-events.py` / 新校验器逐分支写测试
- **git 命令加 timeout**、单步串行
- **commit message 含 `wf(TAG0034-P{阶段}):`** 前缀
- **SELF-GATE 触发**：改 `agate/dispatch-protocol.md` + `agate/scripts/agate-dispatch.py`（+ 可能 `check-events.py` 扩展 / 新增校验器）+ `agate/SETUP.md` + `agate/rules/` 下档位词表文件（或 `phases.yaml` 扩字段）+ `agate/tests/` → commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；协议文档变更跑 `check-protocol-consistency.py` 确认无 ERROR；派发独立 protocol-alignment-review（A1-A6）。**`agate-workspace/dispatch-routing.yaml` + 机器级档位绑定文件新增不触发 SELF-GATE**（非协议本体，同 `maintainability.yaml`）
- **新增 CHECK/规则前先全仓扫描存量**（DEBT0025）——新增的 `dispatch_route` 理由码枚举校验、routing schema 校验器，落地前确认不与既有 CHECK 冲突

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0034-dispatch-routing/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）；`judge.enabled: true`（P1 created ≥ 2026-08-22，机制强制）
- active-tasks.md「待开始」第 18 行已有 TAG0034 行（2026-09-09 已同步到定案设计）
- roadmap：**RM-AG0060**（scheduled）关联本任务——P8 回写 done（P8 gate 硬校验，RM-AG0043）；RM-AG0060 长描述里旧 `rules/dispatch-routing.yaml` 措辞随 design-note 修订一并回写
- **编号体系**：任务用 `TAGxxxx`；校验器 `^T[A-Z]{2}\d+$`

## 7. 已知风险与止损

- "**模型购物完整性洞（最高危）**：gate 解耦使『换模型试到出 green』成为可能 → 止损：候选回落只在三类基础设施信号时发生、收到 gate 能评产出即停、理由码枚举无 `gate_fail` 值由 `check-events.py` 机械强制、专门回归用例锁定"
- "`cli: native` 是弱缓解（诚实标注防过度宣称）：同厂商换 model 盲区基本共享、原理上做不到『不依赖主 Agent』 → 止损：design-note / dispatch-protocol.md 把弱形/强形、自动化不对称写清"
- "`effort` 轴在 Claude Code CLI 基本是空的：`claude -p` 无干净推理档旋钮 → 止损：『声明了 effort 但目标平台不支持』不报错、只 `platform-notes.md` 注明"
- "配置落点是 design-note 现存缺口（用户 2026-09-09 指出）：§2.1 把文件放 `agate/rules/` 又说『非协议本体』矛盾 → 止损：P1 先定三层落点再据此写 schema，落点没定死不进 P2"
- "`cli: native` on OpenCode 的间接路复杂度：要 phase→预配命名 agent 映射 + 预注册机制，比 Claude Code/Codex 多一层 → 止损：P2 评审确认这层不失控"
- "多提交阶段命中 DEBT0037：P4a/P4b/P4c 分批 commit → `agate-next.py` 拒绝推进 → 止损：主 Agent 手动 `_advance` + 补 state_transition 事件（P2 排期预留）"
- "TAG0033 F1 类缺陷预防（DEBT0035 教训）：P4b 结构化输出解析的 P1 spike / P2 minimal_validation 必须**主动构造** `turn.failed` / item `status:failed` / 空返回 / 非 0 退出各终态真实样本，不能只读已有会话"
- "跨 CLI flag 名版本漂移：本会话验证基于 Claude Code 2.1.263 / codex-cli 0.153.4 / opencode 1.18.11 → 止损：`--dangerously-*` / `-s` / `--auto` / `--variant` / `--format` 落地前照 research §10 逐平台对最新官方文档复核"
- "tmux 实测环境代表性（外部评审 W2）：本会话是 WSL2 + tmux 3.4 → 止损：P4c 目标环境须在其自己的 tmux 版本上复跑 research §10 验证项，不同则停在『定稿 + 待落地验证』"
- "SELF-GATE 语义审查：改协议本体（dispatch-protocol / SETUP / agate-dispatch.py / rules 档位词表）须过 protocol-alignment-review，NEEDS_HUMAN_REVIEW 项须人确认 → 止损：P7 前留足审查时间"

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**PR 普通 merge 非 squash**）
- **合并前在 PR 里看 CI**——pytest（`-n auto` Linux 全量）/ shellcheck / consistency / gate-backstop 全绿才算过；Windows CI 只跑 `-m windows_smoke` 冒烟
- roadmap 回写 **RM-AG0060 → done**（P8 gate 硬校验）+ 长描述旧措辞回写
- design-note 修订同步提交（`design-dispatch-routing.md` 6 项 + 头部）
- 归档 HANDOFF：`git mv HANDOFF-TAG0034.md agate-workspace/archived/plans/HANDOFF-TAG0034.md` + commit（走 PR，与代码合并同批或紧随），确保 main 根不残留
- worktree 清理：`git worktree remove .worktrees/agate-TAG0034 --force` + `git branch -D feat/TAG0034-dispatch-routing`
- 复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新 roadmap）；机制反馈 `feedback_ready` 按需

## 9. 交接确认

- worktree 基线：pytest 全绿（unit 1390 + 2skip / regression 29 / integration 94）+ consistency 0 ERROR（`--strict-errors-only`）——本次无 flake
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册（双平台）、依赖齐全
- 任务数据就绪：TAG0034 P0-brief（含 2026-09-09 定案）+ `.state.yaml` phase=P0 + `gate-events.jsonl`（哈希链干净）
- 前置 TAG0033 已合并 v0.70.0（`CodexAdapter` 可用），依赖已满足
- 三 CLI（Claude Code 2.1.263 / codex-cli 0.153.4 / opencode 1.18.11）已装已认证
- 交接单位置：`HANDOFF-TAG0034.md`（worktree 根，已 commit）
- 启动指令：新 session 首条须显式写「读 worktree 根 `HANDOFF-TAG0034.md`」（orchestrator 默认流程不自动读 HANDOFF）
