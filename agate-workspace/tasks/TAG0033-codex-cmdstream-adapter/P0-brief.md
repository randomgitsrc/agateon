# P0-brief — TAG0033 Codex 命令流适配器 + 平台接入（RM-AG0061）

> 主 Agent 亲自填写（P0 产出）。RM-AG0061（`agate-workspace/roadmap/roadmap.md`，backlog→scheduled）。
> **设计依据**：无独立 design-note——沿用 `docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`
> 里 RM-AG0055 的 §3.4.4 适配器契约 + §3.4.2/§3.4.3 检测信号与阈值。机制事实见
> `docs/research/cross-platform-dispatch-mechanics.md`（Codex 相关：§1.2 / §2.2 / §2.4 / §3 / §4.2 /
> §5.1-§5.2 / §6 / §7 / §8 / §9 + 附录 A4-A8 / A12 / A17-A19；2026-09-08 本机 codex-cli 0.153.4 +
> ChatGPT 登录端到端实测）。
> **关系**：RM-AG0055 §3.4.4 明确预留"未来接入 Codex/Cursor：约一个文件、检测引擎/阈值零改动"的
> 扩展点，本任务落地它；同时作 RM-AG0060（派发路由 epic）b 块（跨 CLI 子进程）的**前置**——Codex
> 是整个方案里唯一不确定的部分，先做以去风险；且本任务**独立于 RM-AG0060 成立**（RM-AG0055 完整性收益）。

## task

"给 RM-AG0055 命令流日志机制（`agate/scripts/agate-cmdstream-{adapters,detect,ir}.py`，TAG0028
已落地）新增 **CodexAdapter**——使 subagent 存活/卡死检测覆盖 Codex 平台。同时把
`agate/platform-notes.md` 的 Codex 章从「待补充」补为完整能力矩阵 + 实机验证记录，
`agate/SETUP.md` 增 Codex 自动化环境接入小节。检测引擎（`agate-cmdstream-detect.py`）、阈值
（§3.4.3）、`CommandRecord` IR（`agate-cmdstream-ir.py`）、既有三平台适配器**零改动**——全部
成本收敛在新适配器 + 文档 + 测试。"

### scope

- **CodexAdapter（`agate-cmdstream-adapters.py` 新增 class + 注册表加一行）**
  - 实现 `CommandStreamAdapter` 契约三方法：`probe(path)`（判断是否 Codex 会话存储）、
    `list_sessions(cwd)`（定位 `~/.codex/sessions/` 下会话文件，含 `spawn_agent` 子会话——本会话
    调查怀疑同 DSH 的 `delegationDepth` 式独立文件，**P1 需确认目录结构**）、
    `read_commands(session_path) -> list[CommandRecord]`
  - 数据源：`~/.codex/sessions/**/*.jsonl`（rollout JSONL）；实时源可用 `codex exec --json` 事件流
    （`thread.started` / `item.completed{item.type}` / `turn.started` / `turn.completed` / `turn.failed`）
  - 已知坑（2026-09-08 调查，P1/P3 覆盖）：① Codex **无数字 exit code**——同 Claude Code/DSH，靠
    `is_error` 布尔 + 失败输出文本前缀解析（`CommandRecord.exit` / `exit_signal` 字段）；
    ② `spawn_agent` 子会话文件的层级标识与定位；③ 截断标记处理（`truncated` 字段，参与冻结检测
    不参与无效重复哈希，比照 §3.4.2 差异点 4）
- **`agate/platform-notes.md` Codex 章**（「待补充」→ 完整能力矩阵）：非交互 `codex exec`
  （`-m/--model`、`-c model_reasoning_effort=<low|medium|high>` 推理档）、权限绕过
  `--dangerously-bypass-approvals-and-sandbox` 与中间档 `-s <mode>` + `--approve-for-me`
  （`--full-auto`/`-a` 已从 `codex exec` 移除）、`spawn_agent` 原生子派发（按次可传 `model` +
  `reasoning_effort`，schema 目前是 `[自述]`——本任务补直接实测）、`--json` 结构化输出、`resume`；
  退出码不可靠须解析 `--json`；**model 阵容随账号类型变**（ChatGPT 账号 `codex exec -m` 只默认
  `gpt-5.6-terra`、`spawn_agent` model 枚举 4 个；API-key 账号本会话未核实，P1 补）；`multi_agent`
  feature flag 撑 `spawn_agent`、命名有变更史（`collaboration_modes`/`multi_agent_mode` 已 removed），
  目标版本 `codex features list` 复核。**须注明验证的 CLI 版本号**（比照 DSH「新兴平台需持续复核」惯例）
- **`agate/SETUP.md` Codex 小节**：安装（`npm i -g @openai/codex` 或官方方式）+ `codex login`
  （ChatGPT vs API key 影响 model 访问）+ 自动化环境用的绕过 flag
- **测试**：`agate/tests/` 新增 pytest——CodexAdapter 解析单测（用**真实 Codex session 片段作
  fixture**，覆盖 exit-signal 文本前缀解析、`spawn_agent` 子会话定位、截断标记）；检测引擎对 Codex
  会话正确判「调用冻结 / 活动冻结 / 无效重复」三态（虚拟时钟确定性试验，比照
  `verify-heartbeat-cmdstream/verify_cmdstream_detection.py`）
- **真机验证清单**（比照 RM-AG0055 三平台数据源验证严格度；P1 定 / P5-P6 执行）：`spawn_agent`
  完整参数 schema 直接实测（是否有 `[自述]` 未提及的 `background`/`timeout`/`permission` 字段）、
  API-key 账号 model 阵容、`spawn_agent` 嵌套深度（`spawn_agent` 内再 `spawn_agent`）、
  `~/.codex/sessions/` 目录结构与文件格式确认

### out-of-scope

- Codex 作**宿主平台**跑 Agateon 的完整 SETUP/onboarding（能力矩阵之外的预设模板、单 Agent 模式
  考量等）——本任务只做「Codex 作派发目标 + 命令流可观测」所需的最小接入
- RM-AG0055 检测引擎 / 阈值 / 心跳机制本身（不动，只加适配器）
- RM-AG0060 的配置路由 / 子进程派发 / tmux 层（本任务是其前置，不含其内容）
- Cursor 等其它平台适配器（RM-AG0055 §3.4.4 同样预留，各自另立）

## known_risks

- "同类/影响面预判（`agate-cmdstream-detect.py` / IR 被 RM-AG0055 机制消费）：新增适配器不改
  检测引擎/阈值/IR schema/既有三平台适配器，只加 class + 注册表一行——`CommandRecord` 字段
  （`platform`/`session_id`/`tool`/`command`/`ts_start`/`ts_end`/`exit`/`exit_signal`/`output_hash`/
  `truncated`）严格按既有契约填；全量 pytest + consistency 0 ERROR 是硬门槛"
- "同类/影响面预判（`platform-notes.md` / `SETUP.md` 是协议本体）：改它们 + `agate-cmdstream-adapters.py`
  → **触发 SELF-GATE**，commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；
  protocol-alignment-review 走 A1-A6 清单"
- "Codex CLI 版本漂移：本会话验证基于 codex-cli 0.153.4 + ChatGPT 登录；`spawn_agent` 靠
  `multi_agent` feature flag（命名有变更史），`codex exec` flag 名、model 阵容、session 文件格式
  都可能随版本变——platform-notes.md Codex 章须注明验证版本号"
- "`spawn_agent` schema 是模型自述非独立验证（外部评审 B1 教训）：『未见 background/timeout/
  permission 字段』≠ 确认没有——真机验证清单必须直接实测穷尽 schema，落地代码不得假设 schema 已完整"
- "Codex 无数字 exit code 的解析脆弱性：靠 `is_error` + 文本前缀正则，Codex 若改失败输出文本
  格式则解析规则需跟着更新——同 RM-AG0055 对 Claude Code/DSH 的既有已知局限，登记不新造"
- "`spawn_agent` 子会话定位：本会话怀疑同 DSH 的 `delegationDepth` 式独立文件但未确认——P1 必须
  先确认 `~/.codex/sessions/` 目录结构，读主文件会漏子代理记录"

## env_constraints

- 本任务改 `agate/scripts/agate-cmdstream-adapters.py` + `agate/platform-notes.md` + `agate/SETUP.md`
  + `agate/tests/` → **触发 SELF-GATE**
- 需要 **Codex CLI 已装 + 已认证**（本机 codex-cli 0.153.4 + ChatGPT 登录已具备）；真机验证清单里
  的 API-key 账号项若本机无 API-key 账号则登记为「待有该环境时补」、不阻塞（同 research §11 处理）
- 用系统 python（`/usr/bin/python3`）跑 pytest/pyyaml；ruff 用 `~/.venvs/agate-dev/bin/ruff`；
  基线验证用 `--strict-errors-only`（DEBT0012）
- 派发类工具用 `~/.agate` 稳定版，不用 worktree 相对路径（TAG0016 教训）

## executor_env

- worktree：`.worktrees/agate-TAG0033`（分支 `feat/TAG0033-codex-cmdstream-adapter`），构建流程见
  `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0033.md` 按模板全 9 节填写
