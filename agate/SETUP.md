# 首次接入指南：把 orchestrator 注册成可调用的 Agent

> 面向**第一次把 Agateon 接入某个项目**的人。`README.md`「快速上手」讲的是"装 Agateon 本体"，这份文档讲的是下一步——怎么让 OpenCode / Claude Code 真的能调起 orchestrator，这一步是平台相关的，容易卡住，所以单独写。
>
> 前置：已完成 `README.md`「快速上手」第 1 步——`~/.agate` 指向协议本体。两种形态均可：**单软链**（`~/.agate` → 仓库 `agate/` 子目录，`install.sh` 装法）或**版本管理目录**（`~/.agate/vX.Y.Z/` 版本目录 + `latest`/`current` 指针，`agate-install.py` 装法，见下方「环境准备」）。没做完先去做那一步。
>
> 运行依赖：**Python 3.8+ 且 `pip install pyyaml`（强制）**——全部 gate 脚本已 Python 化（TAG0010），pyyaml 缺失时脚本 fail-closed 阻断。详见 `platform-notes.md`。

---

## 核心结论先说

- **只需要注册 orchestrator 这一个 agent**。P1-P8 的执行角色/评审角色不需要在平台层预注册——派发时是"派一个通用 subagent，把角色文件路径写进 prompt 让它自己读"，见 `role-system.md`「方法 B」。
- `orchestrator-template.md` 对所有项目内容完全一致，**标准接入方式是符号链接直接指向它，不要拷贝**。这样 Agateon 升级模板，你项目里的 orchestrator 提示词自动跟着升级，不需要手动同步。
- 项目特定信息（工作区规则、gate 命令、测试基线……）**只写进** `{AGATE_WORKSPACE}/agents/project.md`（可选文件，模板见 `assets/templates/project.md`），不要碰 orchestrator.md 本身。工作区默认在项目根 `agate-workspace/`，可用 `.agate.env` 的 `AGATE_WORKSPACE=` 指向其他位置（含项目外绝对路径），解析见 `scripts/agate_common.py`。

---

## 环境准备（agent 执行）

> 面向 **Agent（而非人类）** 执行的环境自检与修复闭环：探测命令 exit code 可判，缺项时按平台指引修复，最后验证闭环。适合编排 Agent 在接入前跑一次 `agate-install.py --check` 确认环境，或用脚本化方式判断依赖就绪。

**探测（exit code 可判）**：

```bash
python3 ~/.agate/scripts/agate-install.py --check
# exit 0 = python3/pyyaml/git/bash 全部就绪
# exit 非 0 = 存在缺失项，输出列出缺失项 + 分平台修复指引
```

逐项探测（agent 可读 exit code）：

```bash
command -v python3          # python3 存在（Windows 用 `command -v python`）
python3 -c "import yaml"    # pyyaml 就绪（缺项 exit 非 0）
command -v git              # git 存在
command -v bash             # bash 存在（仅 3 个 hook 薄壳需要；Windows 用 Git for Windows 自带 sh）
```

**分平台修复**：

| 缺失项 | Linux/macOS | Windows（Git for Windows） |
|--------|-------------|---------------------------|
| python3 | `sudo apt install python3` 或 `pip install python` | 从 python.org 安装并勾选「Add to PATH」 |
| pyyaml | `pip install pyyaml` | `pip install pyyaml` |
| git | `sudo apt install git` | 安装 Git for Windows |
| bash | `sudo apt install bash` | Git for Windows 自带（`Git Bash`）|

> Windows 额外：设置系统环境变量 `PYTHONUTF8=1`（让 python 以 UTF-8 模式读写协议文件）、`AGATE_ROOT` 用 Unix 风格路径（`/c/...`，不要反斜杠）。详见 `platform-notes.md`「Windows 原生」。

**验证闭环**：

```bash
python3 ~/.agate/scripts/agate-summary.py   # 输出当前项目解析到的版本 + 原因，确认协议就绪
python3 ~/.agate/scripts/agate_common.py    # 输出 AGATE_WORKSPACE / AGATE_TASKS_DIR 两行，确认工作区解析
```

---

## 步骤 1：（可选）创建 project.md

如果你的项目有 orchestrator 专属的操作细节（不适合塞进通用的 AGENTS.md/CLAUDE.md），复制模板：

```bash
mkdir -p {AGATE_WORKSPACE}/agents
cp {agate_root}/assets/templates/project.md {AGATE_WORKSPACE}/agents/project.md
# 按模板里的说明填写，删掉不需要的小节
```

没有这类细节就跳过——orchestrator 默认只读 AGENTS.md/CLAUDE.md 也能正常工作。

## 步骤 2：把 orchestrator 注册到你的平台

**先确认你的 `agate_root`**（默认 `~/.agate`，自定义过装哪的话按实际路径替换下面命令里的 `~/.agate`）。

### Claude Code（`.claude/agents/`）

```bash
mkdir -p .claude/agents
ln -sf ~/.agate/orchestrator-template.md .claude/agents/orchestrator.md
```

**注意用文件级链接，不要把整个 `.claude/agents` 目录链到别处**——那样会让这个目录里以后任何非 Agateon 的自定义 agent 都被迫绑定到同一个源头，也可能把无关文件暴露给 agent 发现机制。只链这一个文件。

**Claude Code 的 frontmatter 必须含 `name: orchestrator` 字段**——缺了这个字段，Claude Code 会静默跳过整个文件，不报错不警告，agent 就是"不存在"，`orchestrator-template.md` 已经带了这个字段，不需要你额外加，这里提醒是因为如果你自己改过模板、不小心删掉了这个字段，是最容易踩、也最难发现的坑（没有任何报错信息）。

验证：`claude agents --json` **不能**用来验证——那条命令列的是当前活跃的后台/交互会话，和 `.claude/agents/` 目录下的自定义 agent 定义无关，跑通了不代表 orchestrator 注册成功。目前没有等价于 OpenCode `opencode debug agent <name>` 的空跑校验命令，最小成本的验证方式是真的选中一次：
```bash
claude --agent orchestrator -p "echo test"
```
能正常选中 orchestrator 并返回、不报 "Failed to parse agent" 或类似错误，就说明注册成功——不需要跑一次完整任务。

### OpenCode（`.opencode/agents/`）

```bash
mkdir -p .opencode/agents
ln -sf ~/.agate/orchestrator-template.md .opencode/agents/orchestrator.md
```

同样是文件级链接，理由同上。

> ⚠️ **副作用**：创建 `.opencode/` 目录后，OpenCode 会把它当作插件目录，自动初始化 `@opencode-ai/plugin` 依赖（生成 `package.json`/`package-lock.json`/`node_modules`）。这是 OpenCode 平台行为，无害，但 `.opencode/node_modules` 里的 `.md` 文件可能被 Agateon 的一致性检查（`check-protocol-consistency.py`）误扫——已从扫描范围排除 `.opencode`/`.claude`/`node_modules`，无需处理。

验证：
```bash
opencode debug agent orchestrator
```
应该能看到 `"mode": "primary"`、`"tools": {..., "task": true, ...}` 这些字段——重点看 `task` 是不是 `true`（这是 orchestrator 派发 subagent 要用的工具，早期 OpenCode 版本有过一个已知 bug 会让自定义 agent 拿不到这个工具，[issue #14308](https://github.com/anomalyco/opencode/issues/14308)，当前主流版本已修复，但升级/降级 OpenCode 后建议重新跑一次这条命令确认）。
`opencode agent list` 不会列出这个自定义 agent（那个命令只列内置 agent），看不到不代表没装上，以 `opencode debug agent orchestrator` 的结果为准。

### Windows（无 WSL，用 Git for Windows）

符号链接需要管理员权限或开发者模式（和 `install-hook.py` 装 hook 遇到的限制是同一个系统限制）：

```bash
# Git Bash 里，和 Linux/macOS 写法一样：
ln -sf ~/.agate/orchestrator-template.md .claude/agents/orchestrator.md
ln -sf ~/.agate/orchestrator-template.md .opencode/agents/orchestrator.md
```

如果报错（没有开发者模式/非管理员），退化成复制：
```bash
cp ~/.agate/orchestrator-template.md .claude/agents/orchestrator.md
cp ~/.agate/orchestrator-template.md .opencode/agents/orchestrator.md
```
⚠️ **复制模式的代价**：Agateon 升级模板后不会自动同步，你需要在每次升级完 Agateon 后手动重跑上面这两条 `cp` 命令。目前没有自动漂移检测（`agate-summary.py` 现有的漂移检测只覆盖 `scripts/` 目录下的脚本副本，不覆盖这个文件），这是已知的手动步骤，忘了也不会报错提醒——建议每次升级 Agateon 后养成习惯重跑一遍。

`cmd`/PowerShell 的 `mklink` 底层调用的是和 `ln -sf` 同一个系统 API，一样需要管理员权限，不是绕开限制的办法；`mklink /H`（硬链接）在同一 NTFS 分区内不需要管理员权限，可以作为免权限的进阶选项，但硬链接绑定的是当前这份文件的磁盘位置，**Agateon 自身升级模板文件时如果不是原地改写而是新建后替换（多数 git 实现是这样），硬链接会指向旧内容变成过期链接**——这一点没有在这套环境实测过，如果要用请自己验证一次"升级 Agateon 后硬链接是否还生效"，不确定就用复制模式更保险。

### Windows 环境适配要点（无 WSL，Git for Windows）

> Agateon 的 gate 脚本已全部 Python 化（`.py`），不再依赖 bash + GNU coreutils（TAG0010 起**无 bash 环境也成为可行选项**）；仅 3 个 git hook 入口保留 `.sh` 薄壳，需要 **Git for Windows** 自带的 sh 执行。以下是 Windows 上跑通 Agateon 的环境要点（详见 `platform-notes.md`「Windows 原生」章节），**hook 相关命令在 Git Bash 里执行**，不要在 `cmd`/PowerShell 里跑 `.sh` 薄壳。

**1. AGATE_ROOT 用 Unix 风格路径**：协议本体路径在 Git Bash 里写成 `/c/Users/<你>/agate/agate`（或 `C:/Users/<你>/agate/agate`），**不要写反斜杠 `C:\...`**——反斜杠在 bash 里是转义符，且 `agate-next-card.py` 的前缀剥离在盘符/反斜杠下失效（Q1 修复覆盖了归一化，但环境变量里直接写反斜杠仍会被 bash 吃掉）。设 `~/.agate` 软链接用 `ln -s`（Git Bash 里 `~` 是 `C:\Users\<你>`）；无符号链接权限时改用系统环境变量 `AGATE_ROOT=/c/Users/<你>/agate/agate`。

**2. PATH 注入风险**：`C:\Program Files\Git\bin`（git.exe）和 `C:\Program Files\Git\usr\bin`（bash + coreutils）须在 PATH 里且**顺序靠前**，否则 `bash`/`grep`/`sed` 会解析到系统其他位置（或找不到）。`git --version` 与 `bash --version` 跑通即代表 PATH 正常。python 的 `Scripts/` 目录若与 Git 的 usr/bin 冲突，以实际 `which python`/`which bash` 为准调整顺序。

**3. Git Bash 执行 hook**：`python3 ~/.agate/scripts/install-hook.py` 在 Git Bash 里跑。Windows 无符号链接权限时 hook 以**复制模式**安装（输出含「复制模式」提示），升级 Agateon 后需重跑此命令（复制不自动跟随源文件，见 `platform-notes.md`「已知限制」）。

**4. `PYTHONUTF8=1`**：Windows 的 python 默认用系统 ANSI 代码页（GBK）解释源码/读写文件，Agateon 的 `.py` 工具按 UTF-8 读写协议文件会乱码/报错。在系统环境变量加 `PYTHONUTF8=1`，或 Git Bash 会话里 `export PYTHONUTF8=1`，让 python 3.7+ 以 UTF-8 模式运行。

**5. CRLF / `core.autocrlf` 处理**：仓库已含 `.gitattributes` 强制 LF（`*.md` 等文本规则除外，历史 review 文件保持 CRLF，见仓库根 `.gitattributes` 文件头注释）；若 clone 的是旧版本仓库（无该文件），手动 `git config core.autocrlf false` 再重新 checkout。已物化 CRLF 的工作区执行 `git add --renormalize .` 重规范化，否则 3 个 hook 薄壳 `.sh` 报 `\r` 语法错、卡片 sha256 校验 mismatch（py 文件已显式 `encoding="utf-8"` 读写，免疫）。

### 步骤 2-DSH：deepseek-harness（DSH）接入

DSH 的接入方式与 OpenCode/Claude Code **完全同构**——注册 orchestrator 身份就是**符号链接**：
DSH 的身份注册机制是 **agent-preset**（`agent.cordis.yml` + `preset.yml`，声明式 agent 组合），
协议模板文件在 `{agate_root}/assets/templates/dsh/`（与 `assets/templates/` 下其他模板同属模板目录）：

```bash
# 1. 注册 orchestrator 身份（DSH preset，等价 .claude/agents/orchestrator.md 软链）
mkdir -p ~/.dsh/.agent-presets/agate ~/.dsh/skills/agate-protocol
ln -sf ~/.agate/assets/templates/dsh/agent.cordis.yml ~/.dsh/.agent-presets/agate/agent.cordis.yml
ln -sf ~/.agate/assets/templates/dsh/preset.yml ~/.dsh/.agent-presets/agate/preset.yml
ln -sf ~/.agate/assets/templates/dsh/SKILL.md ~/.dsh/skills/agate-protocol/SKILL.md

# 2. 装 hook（与所有平台一致，唯一安装脚本）
python3 ~/.agate/scripts/install-hook.py
```

**链接完整性校验**：`agate-summary.py` 每次运行会校验上面三个软链是否指向权威链（`{agate_root}/assets/templates/dsh/`）；漂移（如误指向非权威副本）会给出 WARNING + 一条命令的修复指引。升级后跑一次即可确认。

**身份薄、协议厚**：preset 的 persona 只写"你是谁 + 会话开始步骤 + DSH 工具映射"，行为规范仍指向
`{agate_root}/orchestrator-template.md`——模板随 `~/.agate`（→ 仓库软链）升级自动更新；
符号链接方式升级后什么都不用做；**Windows 无符号链接权限时退复制模式，升级后需重跑上述 `ln` 命令对应的 `cp`**（复制模式代价：模板升级后不会自动同步，与既有平台小节一致）。

**使用**：打开 DSH 会话，在会话选择器选「Agateon 编排者」（对应 `claude --agent orchestrator`），
然后执行 orchestrator-template.md 的「开始」几步验证。

> 版本敏感提示：本接入已实机验证（2026-08-21，DSH v0.1.0-rc.8：preset 软链安装 → 热发现 →
> 会话选择器出现「Agateon 编排者 · 自定义」→ 新会话以 Agateon 编排者人格启动）。DSH 是新兴平台，
> preset/skill 发现机制可能随版本变化——升级 DSH 后若会话选择器找不到「Agateon 编排者」，
> 重跑上方命令块即可。

### 步骤 2-Codex：codex-cli（Codex）接入

Codex 支持完整 P0-P8（有原生 `spawn_agent` 子代理派发，见 `platform-notes.md`「Codex」章），但**没有 `.claude/agents/` 等价的 orchestrator 软链注册步骤**（同 DSH——DSH 用 preset）。接入只需装 CLI + 登录 + 配好自动化环境的绕过 flag。已实机验证：codex-cli **0.153.4** + **ChatGPT 登录**账号（能力矩阵与时效注记见 `platform-notes.md`「Codex」章）。

**1. 安装**：

```bash
npm i -g @openai/codex        # 官方分发；或按 openai/codex 仓库 README 的其它官方方式
codex --version               # 应输出版本号（验证基线 0.153.4）
```

**2. 登录**（`codex login`）：

```bash
codex login                  # 浏览器走 ChatGPT 登录；或设 OPENAI_API_KEY 环境变量用 API key
```

- **ChatGPT 登录账号**：`codex exec -m` 默认 `gpt-5.6-terra`；`-m gpt-5` / `-m gpt-5-codex` 会被 API 400 拒（`"not supported when using Codex with a ChatGPT account"`）。
- **API key 账号**：可用 model 阵容不同（`gpt-5` / `o3` 等可能可用）——agate 本会话未在该环境核实，接入后自己跑 `codex exec --json -m <model> <<< "hi"` 确认。
- 账号类型影响可用 model；`~/.codex/models_cache.json` 是本机 model 白名单。

**3. 自动化环境的绕过 flag**（非交互派发必备）：

```bash
codex exec --json \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  '<prompt>'
```

- `--dangerously-bypass-approvals-and-sandbox`：跳过全部确认 + 无沙箱执行。**仅用于外层已隔离的自动化环境**（CI / 专用 worktree）——它真能拆掉工作区边界。中间档见 `platform-notes.md`「Codex」能力矩阵（`-s <mode>` + `--approve-for-me`；`--full-auto` / `-a` 已从 `codex exec` 移除）。
- `--skip-git-repo-check`：`codex exec` 默认拒绝在非 git 仓库运行，自动化环境按需加。
- `--json`：结构化 JSONL 事件流。**Codex 退出码不可靠**（认证失败 / model 不可用都可能 `exit 0`），须解析 `--json` 的 `turn.failed` / `item.type=="error"` 判成败。

**4. 验证接入**：

```bash
timeout 60s codex features list | grep -iE 'multi_agent'   # multi_agent 应为 stable / true（撑 spawn_agent 子派发）
timeout 120s codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox <<< 'print ok'
```

会话记录落 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`——agate 的 `CodexAdapter`（命令流卡死检测，RM-AG0055）读此路径。

### 步骤 2-dispatch-routing：机器级档位绑定 scaffold（TAG0034 / RM-AG0060）

派发路由（`agate dispatch route`）是**机会式启用**：不填任何自定义配置 = 派发行为与现状逐字节一致（全 `(phase, role)` 解析为 `standard` 档 = 继承主 Agent 当前 model 的原生派发）。**配置文件本身应保留**（即使全空）：空配置 = 显式声明「走默认派发」，后续按本机现状填充即可。本步只在你想让某些阶段跑异 model / 异 CLI（部分缓解 `LIMITATIONS.md` 局限 2）时才需要**填内容**——比照上方「步骤 2-Codex」的 per-platform onboarding 形态。

**1. 建项目级配置文件**（`agate-workspace/dispatch-routing.yaml`，非协议本体、不触发 SELF-GATE，对齐 `maintainability.yaml`）：从仓库复制带注释的 scaffold（`agate-workspace/dispatch-routing.yaml`）到目标项目同名路径——若项目由 Agateon 仓库克隆 / 骨架生成，该文件已随 `agate-workspace/` 自带；缺失时手动复制一份即可。缺失 / 损坏 → 全兜底回出厂默认（= 现状），不报错。

**2. 填 `tier_bindings:`（机器级②，按本机现状填）**：`tier`（`bulk` / `deep`；`standard` 不在此定义——它硬编码为「原生派发」）→ 有序跨 CLI 候选链 `[{cli, model, effort?}]`。**以本机实际装了什么、哪个账号能用哪些 model 为准**——能用就用、不能用不强制，不追求跨机可复现（别的机器复现不了不是缺陷）。探测本机现状：

```bash
command -v claude codex opencode                    # 装了哪些 CLI
claude --help | grep -- --effort                    # Claude Code 是否有 --effort 旋钮（能力探测，不硬编码版本号）
cat ~/.codex/models_cache.json 2>/dev/null          # Codex 账号 model 白名单
opencode models 2>/dev/null | head                  # OpenCode 可用 provider/model
```

链里的候选逐级回落：首候选「起不来 / 基础设施失败 / 无可解析产出」→ 试下一个；全落空 → 默认派发（恒等于本机制未启用）。**gate 判定只认产出文件 + exit code、不认谁生产的**——gate FAIL 是正常阶段 retry（同一候选），绝不换候选。

**3. 填 `routes:`（项目级③，只引用档位名 → 跨机可移植）**：`(phase, role)`（role 段可选）→ `{tier, effort?}` 引用 **或** `{candidates: [...]}` 直接值。示例：`{P2: {architect: {tier: deep}}, P4: {tier: bulk}}`。

**4. 各 CLI 自动化环境的绕过 flag**（子进程派发时路由脚本自动带上，此处仅供你手动复核 flag 名是否漂移）：

```bash
# Claude Code：跳过权限确认
claude -p --output-format json --model <M> --dangerously-skip-permissions '<ctx路径>'
# Codex：跳过全部确认 + 无沙箱 + 允许非 git 仓库（仅外层已隔离环境）
codex exec --json -m <M> --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox '<ctx路径>'
# OpenCode：自动批准工具调用
opencode run --format json --auto -m <provider/model[#variant]> '<ctx路径>'
```

**5. 校验 schema**：

```bash
python3 ~/.agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml   # exit 0 = 合法
```

> OpenCode `cli: native` 走命名 subagent 间接路——需按 `tier_bindings` 里出现的 OpenCode native 候选预注册命名 agent（约定名 `agate-route-<tier>`，`agents.<name>.model` = 候选 model）。无该命名 agent → 该候选判 `launch_fail` 自动回落、不阻断。默认路径（无 OpenCode native 候选）不碰这层。

## 步骤 3（可选）：设成默认 agent

> ⚠️ **默认保持非默认（三平台通用原则）**：标准步骤 2 完成后，orchestrator 只是「可手动选择」的角色，
> **不会成为任何平台的默认 agent**——Claude Code 需 `settings.json` 才默认、OpenCode 无默认机制、
> DSH 出厂 `agent-presets.default` 即 `standard`（web-app bundle 内建，ln preset 不碰 settings 就不会变）。
> **默认不主动设成默认**：orchestrator 是重人格（每次会话先解析 agate_root / 读 active-tasks / 按 phase
> 读卡片，且只派发不亲自动手），设默认会让普通开发会话被引导走 P0-P8。只有明确要做「全项目统一进
> 编排模式」时才执行本步骤；DSH 侧无等价的"一键设默认"入口，改 `~/.dsh/settings.yaml` 的
> `agent-presets.default` 才会生效（本文件不改它）。

不设的话，每次开会话需要手动选/指定 orchestrator；设了之后新会话默认就是它。

**Claude Code**：
```bash
mkdir -p .claude
cat > .claude/settings.json <<'EOF'
{"agent": "orchestrator"}
EOF
```

**OpenCode**：目前没有找到确认过的、等价于 Claude Code `settings.json` 默认 agent的机制——可能需要 `opencode.json` 里配置，也可能只能每次用 `--agent orchestrator` 或平台内选择器手动指定。这条待核实，先按需要每次手动指定。

**要不要把这一步的配置文件提交进 git**：这是团队取舍，不是技术限制——提交意味着"团队所有人打开这个项目默认进 orchestrator"，不提交意味着"每个人自己决定"。两种都合理，自己定。

## 步骤 4：装 hook

```bash
# 前置：确保 python3 + pyyaml 可用（强制依赖）
python3 --version
pip install pyyaml

python3 ~/.agate/scripts/install-hook.py
```

## 步骤 5：整体验证

```bash
python3 ~/.agate/scripts/agate-summary.py   # 确认协议版本、hook 已装
python3 ~/.agate/scripts/agate_common.py  # 确认工作区解析（输出 AGATE_WORKSPACE / AGATE_TASKS_DIR 两行）
mkdir -p {AGATE_WORKSPACE}/{roadmap,tasks,agents,archived,reviews,decisions,plans,logs,debt}
# 若 {AGATE_WORKSPACE}/tasks/active-tasks.md 不存在，orchestrator 首次运行会自动从模板建，不需要手动建
```

然后真开一个会话，指定/选择 orchestrator agent，让它执行「开始」那几步（读 `agate-summary.py` 输出、读 `active-tasks.md`），确认它能正常找到 `{agate_root}`（`~/.agate` 或你设置的路径）、解析出 `{AGATE_WORKSPACE}` 并读到阶段卡片。

## .agate.env 配置（可选）

工作区位置默认 = 项目根下 `agate-workspace/`。需要指向别处时，在**项目根**创建 `.agate.env`：

```bash
# .agate.env（项目根）
AGATE_WORKSPACE=agate-workspace            # 相对路径 → 相对项目根解析
AGATE_WORKSPACE=/srv/agate-ws/My Project   # 绝对路径（可含空格）→ 指向项目外
```

优先级：`.agate.env` 显式配置 > 环境变量 `AGATE_TASKS_DIR` > 默认 `agate-workspace/`。缺失 `.agate.env` 不报错，走默认（BDD-4）。解析逻辑见 `scripts/agate_common.py`。

## .gitignore 建议

```gitignore
# 平台 agent 目录本身是机器本地的注册入口（符号链接/复制品），不提交
.claude/agents/
.opencode/agents/
```

`{AGATE_WORKSPACE}/agents/project.md`（如果创建了）**要提交**——它是项目团队共享的真实内容，不是本地注册产物。`.claude/settings.json` 提不提交按上面步骤 3 的团队取舍决定。`.agate.env` 建议提交（团队共享工作区位置约定）；含本机路径的 `.agate.env` 可 gitignore，但提交一份默认样例更利于团队一致。

---

## 升级 Agateon 之后

**已有 Agateon 项目（跑过旧版任务）升级，先读 `UPGRADING.md`**——它讲清楚旧任务数据（active-tasks.md/.state.yaml/任务编号）如何处理，避免升级后踩到破坏性变更。

- 符号链接方式：什么都不用做，orchestrator 提示词自动跟着新版本。
- 复制模式（Windows 无权限场景）：重跑步骤 2 的 `cp` 命令。
- 两种方式都建议顺手跑一次 `python3 ~/.agate/scripts/agate-summary.py`，它会检测协议版本和本地脚本副本漂移（但目前不覆盖 orchestrator.md 复制模式的漂移，见上文已知限制）。

**更新口径（与 `UPGRADING.md` 一致）**：legacy 软链布局更新 = `git pull`；版本管理布局（`~/.agate/` 为版本管理根目录）更新 = `python3 ~/.agate/scripts/agate-install.py latest`（幂等）。安装 / 迁移 / 更新 / 回退完整对照，以及 hook 重装时机、根 `~/.agate/scripts/` 副本维护语义，见 `UPGRADING.md` 的「版本管理生命周期」节。
