# TAG0033 交接单 — 给 RM-AG0055 命令流机制加 Codex 适配器 + 补 Codex 平台文档

> 本交接单供 worktree session 的 agent 按此启动 TAG0033 任务。
> 任务已 P0 立项（.state.yaml phase=P0，P0-brief.md 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0033**：Codex 命令流适配器 + 平台接入（RM-AG0061）。

**一句话**：给 RM-AG0055 命令流日志机制（`agate/scripts/agate-cmdstream-{adapters,detect,ir}.py`，TAG0028 已落地）新增 **CodexAdapter**——使 subagent 存活/卡死检测覆盖 Codex 平台；同时把 `agate/platform-notes.md` 的 Codex 章从「待补充」补为完整能力矩阵 + 实机验证记录，`agate/SETUP.md` 增 Codex 自动化环境接入小节。**检测引擎（`agate-cmdstream-detect.py`）、阈值（RM-AG0055 §3.4.3）、`CommandRecord` IR、既有三平台适配器零改动**——全部成本收敛在新适配器 + 文档 + 测试。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0033` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agateon`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → `/home/kity/oclab/agateon/agate`，稳定版） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是 worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。改造期间工具稳定、改造对象变化，这是有意的。
- **⚠️ gate 工具 ≠ 检查对象**：
  - commit hook 的 gate **判定工具**用 `~/.agate`（稳定版）
  - 但 `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`）——检查对象是 worktree 里的 `platform-notes.md` / `SETUP.md` 改动。误用 `~/.agate` 的会扫主 checkout 的旧文件
  - `python3 ~/.agate/scripts/agate-summary.py` 在 worktree 跑显示**主 checkout 上下文**（稳定版版本/分支/HEAD），不代表 worktree 状态——worktree 状态用 `git log`/`git status`
  - **所有编排/派发类工具脚本**（`agate-inject-card.py` / `agate-render-dispatch-prompt.py` / `agate-next-card.py` 等）用 `~/.agate/scripts/` 稳定版调用（TAG0016 教训：worktree 相对路径调用会读到 worktree 正在被修改的协议卡片）
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 实际在 `/home/kity/oclab/agateon/.git/hooks/`（pre-commit/commit-msg/pre-push 已软链安装）。worktree commit 时自动触发。

**已完成的 setup（worktree 已可独立使用）**：
- 依赖齐全：bash 5.2 / python 3.12.3 / pyyaml / pytest 9.0.3 / shellcheck / ruff（`~/.venvs/agate-dev/bin/ruff`）
- 基线验证：全量 pytest 全绿（unit 1361 passed + 2 skipped / regression 29 / integration 94）+ consistency 0 ERROR（`--strict-errors-only`；存量 329 WARNING 全为历史叙事文件死链，与本任务无关）。
  - ⚠️ 首跑 unit 片 `-n auto` 有一次 `test_agate_next_card.py::test_nc_symlink_script_readlink_resolves` flake（xdist 并行下偶发，TPV0093 已记录）——**单独跑该测试 + 复跑整片均全绿**，非基线破损，不影响本任务
- commit hook：指向 `~/.agate`（稳定版），worktree commit 自动触发
- orchestrator 注册：`.opencode/agents/orchestrator.md` + `.claude/agents/orchestrator.md` → `~/.agate/orchestrator-template.md`（符号链接，双平台）
- 工作区解析：`agate_common.py` 输出 `.../​.worktrees/agate-TAG0033/agate-workspace/`
- 任务数据：TAG0033 P0-brief + .state.yaml phase=P0 + gate-events.jsonl（哈希链干净）在 worktree 的 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/`

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 交付面（详见 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P0-brief.md`）

**① CodexAdapter（`agate/scripts/agate-cmdstream-adapters.py` 新增 class + 注册表加一行）**
- 实现 `CommandStreamAdapter` 契约三方法：`probe(path)` / `list_sessions(cwd)`（含 `spawn_agent` 子会话）/ `read_commands(session_path) -> list[CommandRecord]`
- 数据源：`~/.codex/sessions/**/*.jsonl`（rollout JSONL）；实时源 `codex exec --json` 事件流（`thread.started` / `item.completed{item.type}` / `turn.started` / `turn.completed` / `turn.failed`）
- **已知坑（2026-09-08 调查，P1 需先确认）**：① Codex **无数字 exit code**——同 Claude Code/DSH，靠 `is_error` 布尔 + 失败输出文本前缀解析（IR `exit` / `exit_signal` 字段）；② `spawn_agent` 子会话文件层级标识与定位（**怀疑同 DSH 的 `delegationDepth` 式独立文件、未确认——P1 必须先看 `~/.codex/sessions/` 目录结构**）；③ 截断标记处理（`truncated` 字段，参与冻结检测不参与无效重复哈希，比照 RM-AG0055 §3.4.2 差异点 4）

**② `agate/platform-notes.md` Codex 章**（「待补充」→ 完整能力矩阵，**注明验证 CLI 版本号**）
- 非交互 `codex exec`（`-m/--model`、`-c model_reasoning_effort=<low|medium|high>` 推理档）
- 权限绕过 `--dangerously-bypass-approvals-and-sandbox` + 中间档 `-s <read-only|workspace-write|danger-full-access>` + `--approve-for-me`（`--full-auto`/`-a` 已从 `codex exec` 移除）
- `spawn_agent` 原生子派发：按次可传 `model` + `reasoning_effort`（schema `[自述]`——本任务补直接实测）
- `--json` 结构化输出；`resume`；退出码不可靠须解析 `--json`
- **model 阵容随账号类型变**（ChatGPT 账号 `codex exec -m` 只默认 `gpt-5.6-terra`、`spawn_agent` model 枚举 4 个；API-key 账号本会话未核实）
- `multi_agent` feature flag 撑 `spawn_agent`、命名有变更史（`collaboration_modes` / `multi_agent_mode` 已 removed），目标版本 `codex features list` 复核

**③ `agate/SETUP.md` Codex 小节**：安装（`npm i -g @openai/codex` 或官方方式）+ `codex login`（ChatGPT vs API key 影响 model 访问）+ 自动化环境绕过 flag

**④ 测试 + 真机验证清单**
- `agate/tests/` 新增 pytest：CodexAdapter 解析单测（**真实 Codex session 片段作 fixture**，覆盖 exit-signal 文本前缀解析、`spawn_agent` 子会话定位、截断标记）；检测引擎对 Codex 会话正确判「调用冻结 / 活动冻结 / 无效重复」三态（虚拟时钟确定性试验，比照 `agate/scripts/verify-heartbeat-cmdstream/verify_cmdstream_detection.py` 或 `docs/design-notes/260903-.../verify-heartbeat-cmdstream/`）
- **真机验证清单**（P1 定 / P5-P6 执行，比照 RM-AG0055 三平台数据源验证严格度）：`spawn_agent` 完整参数 schema 直接实测（是否有 `[自述]` 未提及的 `background`/`timeout`/`permission` 字段）、API-key 账号 model 阵容、`spawn_agent` 嵌套深度（`spawn_agent` 内再 `spawn_agent`）、`~/.codex/sessions/` 目录结构与文件格式确认

### out-of-scope（P0-brief 已锁）
- Codex 作**宿主平台**跑 Agateon 的完整 SETUP/onboarding（能力矩阵之外的预设模板、单 Agent 模式考量等）
- RM-AG0055 检测引擎 / 阈值 / 心跳机制本身（不动）
- RM-AG0060 的配置路由 / 子进程派发 / tmux 层（本任务是其前置，不含其内容）
- Cursor 等其它平台适配器

### 核心约束（不可违反）
1. **Linux 基线全绿是回归底线**——现有 pytest 全绿（unit 1361 / regression 29 / integration 94）+ consistency 0 ERROR，每步都保持
2. **检测引擎 / 阈值 / IR schema / 既有三平台适配器零改动**——本任务只加一个 class + 注册表一行；`CommandRecord` 字段严格按既有契约填
3. **证据强度诚实（外部评审 B1 教训）**：`spawn_agent` schema 是 `[自述]`——「未见 background/timeout/permission 字段」≠ 确认没有；真机验证清单必须直接实测穷尽 schema，产出表述不得把 `[自述]`/推断混同为「已实测」
4. **Codex CLI 版本注记**：本会话验证基于 codex-cli **0.153.4** + **ChatGPT 登录**；platform-notes.md Codex 章须注明验证版本号（比照 DSH「新兴平台需持续复核」惯例）
5. **API-key 账号项**：本机是 ChatGPT 账号——若无 API-key 账号则该验证项登记为「待有该环境时补」、不阻塞（比照 research §11 处理）
6. **范围锁定**——P1 分析若发现需超出 P0-brief 锁定范围，先停下跟用户确认

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（分片跑，每片外层 timeout，片内 -n auto）
timeout 300 python3 -m pytest agate/tests/unit/ -n auto -q
timeout 300 python3 -m pytest agate/tests/regression/ -n auto -q
timeout 400 python3 -m pytest agate/tests/integration/ -n auto -q

# 一致性（0 ERROR 才行）——⚠️ 用 worktree 自己的脚本
timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck（本任务不改 .sh，但结构上跑一下）
shellcheck -S warning agate/scripts/*.sh

# 测试计数（验证文档没漂移）
bash agate/tests/scripts/count-tests.sh

# 单脚本测试（改哪个跑哪个，TDD 先红后绿）——本任务主要是：
python3 -m pytest agate/tests/unit/test_agate_cmdstream_adapters.py   # 若既有；否则新建
# 检测引擎联动：
python3 -m pytest agate/tests/ -k cmdstream

# Codex 真机（本机 codex-cli 0.153.4 + ChatGPT 登录已就绪）
codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< "hi"   # 看事件流形态
ls -R ~/.codex/sessions/ | head                                                                # 会话文件结构
codex features list | grep -iE "multi_agent|spawn|collab"                                       # feature flag
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出（pre-commit 会用 P2 gate 检查，P2-design.md 不存在 → 拦截）
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿（AGENTS.md「改脚本的工作流」）。CodexAdapter 的解析逻辑逐分支写测试；`platform-notes.md`/`SETUP.md` 文案变更走 consistency 校验
- **git 命令加 timeout**、单步串行（AGENTS.md 工具纪律）
- **commit message 含 `wf(TAG0033-P{阶段}):`** 前缀
- **改 `agate/scripts/agate-cmdstream-adapters.py` + `agate/platform-notes.md` + `agate/SETUP.md` + `agate/tests/` 触发 SELF-GATE**：commit message 需含 `self-gate-review:` 或 `self-gate-skip:`（否则 commit-msg hook WARNING）；协议文档变更跑 `check-protocol-consistency.py` 确认无 ERROR；派发独立 review subagent 做协议-脚本语义对齐审查（A1-A6）
- **新增 CHECK/规则前先全仓扫描存量**（DEBT0025）——本任务不新增 CHECK，仅加适配器；但 `platform-notes.md` 新增能力矩阵行须确认不与既有 CHECK 12 跨文件一致性锚点冲突

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）；`judge.enabled: true`
- active-tasks.md「待开始」已有 TAG0033 行
- roadmap：**RM-AG0061** 关联本任务（scheduled）——RM-AG0055 §3.4.4 预留扩展点的落地 + RM-AG0060 b 块前置
- **编号体系**：任务用 `TAGxxxx`（项目代号 AG + 动态数字），校验器 `^T[A-Z]{2}\d+$`

## 7. 已知风险与止损

- "`spawn_agent` 子会话定位未确认：本会话怀疑同 DSH 的 `delegationDepth` 式独立文件——P1 必须先确认 `~/.codex/sessions/` 目录结构，读主文件会漏子代理记录 → 止损：P1 spike 里实际派一个 Codex 子代理、观察生成的会话文件"
- "`spawn_agent` schema 是模型自述（外部评审 B1）：不得假设 schema 已穷尽 → 止损：真机验证清单直接实测所有字段，platform-notes.md 如实标 `[自述]` / `[实测]`"
- "Codex 无数字 exit code 的解析脆弱：靠 `is_error` + 文本前缀正则，Codex 改失败输出文本格式则规则需更新 → 止损：同 RM-AG0055 对 Claude Code/DSH 的既有已知局限，登记不新造；解析规则集中一处便于维护"
- "Codex CLI 版本漂移：`multi_agent` flag 命名有变更史、`codex exec` flag 名/model 阵容/session 格式随版本变 → 止损：platform-notes.md 注明验证版本号 0.153.4，比照 DSH 复核惯例"
- "检测引擎误改风险：本任务只加适配器——若发现 IR 字段不够表达 Codex 语义、需扩 IR/引擎，属超范围 → 止损：停下跟用户确认，可能拆子任务"
- "SELF-GATE 语义审查：改协议本体（platform-notes/SETUP/脚本）须过 protocol-alignment-review，NEEDS_HUMAN_REVIEW 项须人确认 → 止损：P7 前留足审查时间"

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**PR 普通 merge 非 squash**）
- **合并前在 PR 里看 CI**——pytest（`-n auto` Linux 全量）/ shellcheck / consistency / gate-backstop 全绿才算过；Windows CI 只跑 `-m windows_smoke` 冒烟
- roadmap 回写 **RM-AG0061 → done**（P8 gate 硬校验，RM-AG0043）
- 归档 HANDOFF：`git mv HANDOFF-TAG0033.md agate-workspace/archived/plans/HANDOFF-TAG0033.md` + commit（走 PR，与代码合并同批或紧随），确保 main 根不残留
- worktree 清理：`git worktree remove .worktrees/agate-TAG0033 --force` + `git branch -D feat/TAG0033-codex-cmdstream-adapter`
- 复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新 roadmap）
- **对 RM-AG0060 / TAG0034 的交接**：本任务是 TAG0034 b 块的前置——完成后在 TAG0034 P0-brief / HANDOFF 里更新「TAG0033 已合并，`cli: codex` 子进程存活检测可用 `CodexAdapter`」

## 9. 交接确认

- worktree 基线：pytest 全绿（unit 1361+2skip / regression 29 / integration 94）+ consistency 0 ERROR（`--strict-errors-only`）；一次 xdist flake 已确认为偶发非破损
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册（双平台）、依赖齐全
- 任务数据就绪：TAG0033 P0-brief + .state.yaml phase=P0 + gate-events.jsonl（哈希链干净）
- Codex CLI 就绪：codex-cli 0.153.4 + ChatGPT 登录（真机验证部分本机可做；API-key 账号项待环境）
- 交接单位置：`HANDOFF-TAG0033.md`（worktree 根，已 commit）
- 启动指令：新 session 首条须显式写「读 worktree 根 `HANDOFF-TAG0033.md`」（orchestrator 默认流程不自动读 HANDOFF）
