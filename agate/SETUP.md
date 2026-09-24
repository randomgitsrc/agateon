# 首次接入指南：把 orchestrator 注册成可调用的 Agent

> 面向**第一次把 Agateon 接入某个项目**的人。`README.md`「快速上手」讲的是"装 Agateon 本体"，这份文档讲的是下一步——怎么让平台（**Claude Code / OpenCode / DSH / Codex**）真的能调起 orchestrator。这一步平台相关、易卡住，故单独成文。
>
> **多数情况只需一条命令**（见步骤 2）：`python3 ~/.agate/scripts/agate-setup.py`。以下各平台小节是它内部做的事，供理解与**手工兜底**。
>
> 前置：已完成 `README.md`「快速上手」第 1 步——`~/.agate` 是**版本管理根目录**（`~/.agate/vX.Y.Z/` 版本目录 + `latest`/`current` 指针，`install.sh` / `agate-install.py` 装法，见下方「环境准备」）。没做完先去做那一步。
>
> 运行依赖：**Python 3.8+ 且 `pip install pyyaml`（强制）**——全部 gate 脚本已 Python 化（TAG0010），pyyaml 缺失时脚本 fail-closed 阻断。详见 `platform-notes.md`。

---

## 先取协议根路径（仅手工兜底时需要）

协议根在版本管理布局的 `current` 指针之下（`~/.agate` 是版本管理根**实体目录**：`repo/` + `vX.Y.Z/` + `latest` / `current` 指针）。下述各平台命令统一用变量 `$AGATE_DIR` 指代协议根（`orchestrator-template.md` 与 `assets/` 都在它下面），取值为 `~/.agate/current/agate`。

**一行取到它**：

```bash
AGATE_DIR="$HOME/.agate/current/agate"
# 自检：应可读；不可读则 current 缺失或版本目录不完整
test -r "$AGATE_DIR/orchestrator-template.md" && echo "✅ 模板可读" || echo "❌ 协议根不可用：$HOME/.agate/current 缺失或版本目录不完整，请先 bash install.sh"
```

> 没有 `current` 指针时不再有兜底取值——命令明确失败并提示先装。`$AGATE_DIR` 是**当前 shell 变量**，下面各平台命令块在同一 shell 会话里执行即可（新开终端需重跑这一行）。
>
> **用 `agate-setup.py` 时不需要这一步**——它自己经 `resolve_version_root()` 解析协议根。

---

## 核心结论先说

- **只需要注册 orchestrator 这一个 agent**。P1-P8 的执行角色/评审角色不需要在平台层预注册——派发时是"派一个通用 subagent，把角色文件路径写进 prompt 让它自己读"，见 `role-system.md`「方法 B」。
- `orchestrator-template.md` 对所有项目内容完全一致，**标准接入方式是指向它（符号链接 / preset / skill），不要拷贝**。这样 Agateon 升级模板，你项目里的 orchestrator 提示词自动跟着升级，不需要手动同步。**接入动作已命令化**——`agate-setup.py`（步骤 2）按平台自动选对形态。
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

**一条命令搞定**（推荐——自动探测已装平台、注册身份、装 hook；幂等，可反复跑）：

```bash
python3 ~/.agate/scripts/agate-setup.py
```

它做的事：

| 层 | 动作 |
|----|------|
| **平台身份**（全局） | 按探测到的平台建配置物：Claude Code / OpenCode → `~/.claude/agents/` · `~/.config/opencode/agents/`；DSH → `~/.dsh/profiles/*/cordis.patch.yml` 里的声明块 + `~/.dsh/skills/`；Codex → `~/.agents/skills/agate-protocol/` |
| **项目侧** | 装 git hook（可单独跑 `install-hook.py`，见「核心结论」节） |

常用参数：

| 参数 | 作用 |
|------|------|
| `--platform dsh,codex` | 显式指定平台（默认 `auto` 探测已装者） |
| `--scope global` | **只注册全局身份，不装 hook** |
| `--scope project` | 注册到**项目内**目录（`.claude/` / `.opencode/`）+ 装 hook——适合按项目钉不同版本 |
| `--scope all`（默认） | 注册全局身份 + 装 hook |
| `--dry-run` | 只显示将做什么 |

**退出码**：`0` = 全部成功；`1` = 有步骤失败（如不在 git 仓库导致 hook 装不上，或协议根无效）；`2` = 用法错误（未知平台）。

> **为什么默认全局**：`orchestrator-template.md` 对**所有项目内容完全一致**（`adr.md` ADR-008），且其 `{agate_root}` 是**运行时按 cwd 解析**的——一个全局注册在项目 A 里跑就解析 A 钉的版本。故一次注册即可服务所有项目。
> **何时用 `--scope project`**：项目用 `.agate-version` 钉了**非 current** 的版本，且你希望身份文件也随该项目版本走。

**装到哪了 / 验证**（注册物应均可读；断链会让平台静默找不到 orchestrator）：

```bash
for f in ~/.claude/agents/orchestrator.md ~/.config/opencode/agents/orchestrator.md \
         ~/.dsh/skills/agate-protocol/SKILL.md ~/.agents/skills/agate-protocol/SKILL.md; do
  [ -r "$f" ] && echo "✅ $f" || echo "（未装/不适用）$f"
done
```

> DSH 的 preset 是**写进 profile patch 的声明块**、不是独立文件，故不在上面这个"文件可读"循环里——查它用 `agate-setup.py --list` 或 `agate-summary.py`（见「步骤 2-DSH」）。

**平台差异（命令内部做的事，供理解与手工兜底）**——各平台配置物形态不同，以下是细节：

### Claude Code（`.claude/agents/`）

> 本小节命令块是 **`--scope project`** 的项目级形态（供理解与手工兜底）；**默认全局**形态见上方表格——`agate-setup.py` 会写到 `~/.claude/agents/`。

```bash
mkdir -p .claude/agents
ln -sf "$AGATE_DIR/orchestrator-template.md" .claude/agents/orchestrator.md
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
ln -sf "$AGATE_DIR/orchestrator-template.md" .opencode/agents/orchestrator.md
```

同样是文件级链接，理由同上。

> ⚠️ **副作用**：创建 `.opencode/` 目录后，OpenCode 会把它当作插件目录，自动初始化 `@opencode-ai/plugin` 依赖（生成 `package.json`/`package-lock.json`/`node_modules`）。这是 OpenCode 平台行为，无害，但 `.opencode/node_modules` 里的 `.md` 文件可能被 Agateon 的一致性检查（`check-protocol-consistency.py`）误扫——已从扫描范围排除 `.opencode`/`.claude`/`node_modules`，无需处理。

验证：
```bash
opencode debug agent orchestrator
```
应该能看到 `"mode": "primary"`、`"tools": {..., "task": true, ...}` 这些字段——重点看 `task` 是不是 `true`（这是 orchestrator 派发 subagent 要用的工具，早期 OpenCode 版本有过一个已知 bug 会让自定义 agent 拿不到这个工具，[issue #14308](https://github.com/anomalyco/opencode/issues/14308)，当前主流版本已修复，但升级/降级 OpenCode 后建议重新跑一次这条命令确认）。
`opencode agent list` 不会列出这个自定义 agent（那个命令只列内置 agent），看不到不代表没装上，以 `opencode debug agent orchestrator` 的结果为准。

### 步骤 2-DSH：deepseek-harness（DSH）接入

DSH 的身份注册机制是 **agent-preset**（`agent.cordis.yml` + `preset.yml`，声明式 agent 组合）+ **skill**（`SKILL.md`），
与 Claude Code / OpenCode 的「单个 agent md 软链」**形态不同**（同一目的、三种载体）。模板源在 `{agate_root}/assets/templates/dsh/`。

**推荐路径——仍是步骤 2 的那一条命令**：`agate-setup.py` 会把声明块写进**已存在的每个** `~/.dsh/profiles/*/cordis.patch.yml`，并装 `~/.dsh/skills/agate-protocol/SKILL.md`：

```bash
python3 ~/.agate/scripts/agate-setup.py            # 自动探测已装平台；只接 DSH 时加 --platform dsh
```

> 一个 profile patch 都没有时，命令会提示「未找到 DSH profile」——那说明 DSH 从未启动过。先启动一次 DSH 让它建出 `profiles/<name>/`，再重跑本命令。

**新形态：声明式 profile patch**。DSH 现在从 **profile 自己的 patch 文件**读 preset 声明，不再读任何 preset 目录：

| 项 | 值 |
|----|----|
| 落点 | `~/.dsh/profiles/<profile>/cordis.patch.yml`（本机是 `web`；命令遍历 `~/.dsh/profiles/*/`，不写死 profile 名）|
| 起点标记 | 以 `>>> agateon: preset-agate` 起头的注释行（括号内写明"由 agate-setup.py 管理；手改会在下次接入时被覆盖"）|
| 终点标记 | 以 `<<< agateon: preset-agate` 起头的注释行（两标记之间的整段 = 托管范围）|
| 块内容 | 一条 `- insert:` 行：`id: preset-agate`、插件 `@deepseek-ai/dsh-agent-preset`、`config.id: agate`，外加 `name` / `description` / `order`（取自 `preset.yml`）与 `config.plugins`（= `agent.cordis.yml` 的行列表）|

> **为什么旧形态没了**：DSH **≥ 0.1.7-alpha.1**（commit `d1e22a7e24`「declare Agent compositions in profile YAML」）起**不再读取**目录式 preset `$DSH_HOME/.agent-presets/<id>/`。上游自带 skill 的原文：*"Before declaration rows, a user preset was a directory `$DSH_HOME/.agent-presets/<id>/` holding `preset.yml` …… Nothing reads that directory any more."*
> 所以旧的 `~/.dsh/.agent-presets/agate/` **留着无害**（不报错、不影响别的配置），但**具有误导性**——它看起来像"已接入"，而 DSH 会话选择器里根本没有「Agateon 编排者」。本机实测的后果：最后一次选中 agate preset 的会话停在 2026-09-20 22:25，之后每个会话都落在 `standard`；而 `agate-setup.py --list` 因为只检查那个死目录，一直报 ✅。

**验证**（落点与内容各看一处）：

```bash
python3 ~/.agate/scripts/agate-setup.py --list   # 检查 DSH 真正读取的位置（profile patch 的托管块）
python3 ~/.agate/scripts/agate-summary.py        # 版本 + 各平台接入产物；块内容与任何已装版本模板不一致 → 报漂移
```

`agate-summary.py` 每次运行校验两件事（权威判据见「升级 Agateon 之后」节）：① skill 软链是否指向**某个已安装版本**里的同名模板；② profile patch 里的声明块是否等于**某个已安装版本**模板的生成结果。指向开发 checkout / 临时副本、块被手改、或内容落后 → WARNING + 重跑接入命令的修复指引。升级后跑一次即可确认。

**手工兜底（正常用户让命令做即可）**：若你要自己往 profile patch 里写，可以粘下面这段——它与 `agate-setup.py` 写入的**逐字相同**（含两个托管标记）。注意它是**托管块**：内容由命令从两个模板重新生成，**手改会在下次接入时被覆盖**；本段是**快照**，模板改动后它不会自动跟随——**以 `agate-setup.py` 的生成结果为准**。

```yaml
# >>> agateon: preset-agate（由 agate-setup.py 管理；手改会在下次接入时被覆盖）>>>
- insert:
    - id: preset-agate
      name: '@deepseek-ai/dsh-agent-preset'
      config:
        id: agate
        name: Agateon 编排者
        description: Agateon 编排 Agent（P0-P8 全流程管理，派发 subagent 执行，gate 硬边界验证）。
        order: 1
        plugins:
          # … 插件的完整行列表（约 200 行）由命令从模板生成，见下方说明
# <<< agateon: preset-agate <<<
```

> **为什么不把整块贴在这里**：那 200 行是 `assets/templates/dsh/{preset.yml,agent.cordis.yml}`
> 两个模板的**机械展开**。贴进文档就多出一份**手工维护的快照**——模板一改、文档即漂移，正是本次
> 要消灭的那类失配（本仓文档原则：权威源只指路，不复制）。要看真实块内容，让命令写完后直接读：
>
> ```bash
> sed -n '/agateon: preset-agate/,/<<< agateon: preset-agate/p' \
>   ~/.dsh/profiles/*/cordis.patch.yml
> ```
>
> 若确实要手工粘，用 `python3 -c "import sys;sys.path.insert(0,'~/.agate/scripts');import agate_common as a;print(a.dsh_preset_block('~/.agate/current/agate'))"` 生成——那是**唯一**不会漂移的来源。

> **迁移旧副本时的已知陷阱**：插件包名改过一次——`@deepseek-ai/dsh-workflow-worker-thread` → **`@deepseek-ai/dsh-workflow-ptc`**（旧包在 0.1.7 已不存在）。**照抄旧文件里那一行会让 preset 激活失败**：上游 skill 要求逐个核对包名，理由正是"preset 写就之后改过名的包会在激活时失败"。上面的生成器已自动替换，只有手抄旧副本时才会踩到。
> **唯一安装脚本**：hook（与所有平台一致）仍由 `python3 ~/.agate/scripts/install-hook.py` 安装——`agate-setup.py` 内部即调用它。DSH 没有、也不引入 per-platform installer。

**身份薄、协议厚**：preset 的 persona **只做两件事**——指向 `{agate_root}/orchestrator-template.md`（唯一权威行为规范）+ 给 DSH 工具映射与平台注意；**不复制协议内容**（曾复制「会话开始步骤」，结果模板改了路径而副本未跟 → 实测失实）。声明块由 `preset.yml` / `agent.cordis.yml` 两个模板生成，模板仍是**唯一来源**；块内容是复制进 profile 的，不跟随源文件——升级协议根后重跑一次 `agate-setup.py` 即刷新。

**使用**：打开 DSH 会话，在会话选择器选「Agateon 编排者」（对应 `claude --agent orchestrator`），
然后执行 orchestrator-template.md 的「开始」几步验证。

> 版本敏感提示：两种形态都已实机验证——目录式（2026-08-21，DSH v0.1.0-rc.8：软链安装 → 热发现 →
> 会话选择器出现「Agateon 编排者 · 自定义」）与声明式（2026-09-24：写入 profile patch 后新会话
> 模式选择器出现「Agateon 编排者」且可选中）。**目录式 preset 自 0.1.7-alpha.1 起已被上游停止读取**，
> 这正是本节改写的原因。DSH 是新兴平台，机制随版本变化快——升级 DSH 后若选择器里找不到
> 「Agateon 编排者」，重跑上方命令块即可。

### 步骤 2-Codex：codex-cli（Codex）接入

Codex 支持完整 P0-P8（有原生 `spawn_agent` 子代理派发，见 `platform-notes.md`「Codex」章），但**没有 `.claude/agents/` 等价的 agent 注册机制**——它的身份靠 **skill**（`~/.agents/skills/agate-protocol/SKILL.md`，`~/.agents/skills/` 是 Codex 共享 skill 根）。接入 = 装 CLI + 登录 + 装 skill + 配自动化 flag。已实机验证：codex-cli **0.153.4** + **ChatGPT 登录**账号（能力矩阵与时效注记见 `platform-notes.md`「Codex」章）。

> ⚠️ **Codex 特有硬约束：必须显式要求派发**。Codex 会话上下文含 `<multi_agent_mode>`，其默认语义是「**除非用户或适用的 AGENTS.md / skill 指令显式要求，否则不要派发子 agent**」。而 Agateon 的整个模型建立在主 Agent 派发 subagent 之上——**不显式要求则静默不派发**，P0-P8 直接失效。适配层已写明该要求（见 `assets/templates/codex/SKILL.md`）；用 `agate-setup.py` 装上即生效。
> 注意与 `codex features list` 的 `multi_agent` **不是一回事**：后者是**能力开关**（stable/true = 可派发），前者是**行为默认值**（要求显式声明才派发）。

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

## 步骤 3（可选）：设成默认 agent

> ⚠️ **默认保持非默认（三平台通用原则）**：标准步骤 2 完成后，orchestrator 只是「可手动选择」的角色，
> **不会成为任何平台的默认 agent**——Claude Code 需 `settings.json` 才默认、OpenCode 无默认机制、
> DSH 出厂 `agent-presets.default` 即 `standard`（web-app bundle 内建；接入只往 profile patch 写声明块、不碰 `settings.yaml`，故不会变）。
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

## 步骤 4：整体验证

```bash
python3 ~/.agate/scripts/agate-summary.py   # 确认协议版本、hook 已装
python3 ~/.agate/scripts/agate_common.py  # 确认工作区解析（输出 AGATE_WORKSPACE / AGATE_TASKS_DIR 两行）
mkdir -p {AGATE_WORKSPACE}/{roadmap,tasks,agents,archived,reviews,decisions,plans,logs,debt}
# 若 {AGATE_WORKSPACE}/tasks/active-tasks.md 不存在，orchestrator 首次运行会自动从模板建，不需要手动建
```

然后真开一个会话，指定/选择 orchestrator agent，让它执行「开始」那几步（读 `agate-summary.py` 输出、读 `active-tasks.md`），确认它能正常找到 `{agate_root}`（`~/.agate` 或你设置的路径）、解析出 `{AGATE_WORKSPACE}` 并读到阶段卡片。

## 步骤 5（可选）：派发路由（`agate dispatch route`，TAG0034 / RM-AG0060）

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

## Windows 接入要点（无 WSL，Git for Windows）

> Agateon 的 gate 脚本已全部 Python 化（`.py`），不再依赖 bash + GNU coreutils（TAG0010 起**无 bash 环境也成为可行选项**）；仅 3 个 git hook 入口保留 `.sh` 薄壳，需要 **Git for Windows** 自带的 sh 执行。以下是 Windows 上跑通 Agateon 的环境要点（详见 `platform-notes.md`「Windows 原生」章节），**hook 相关命令在 Git Bash 里执行**，不要在 `cmd`/PowerShell 里跑 `.sh` 薄壳。

**1. AGATE_ROOT 用 Unix 风格路径**：协议本体路径在 Git Bash 里写成 `/c/Users/<你>/agate/agate`（或 `C:/Users/<你>/agate/agate`），**不要写反斜杠 `C:\...`**——反斜杠在 bash 里是转义符，且 `agate-next-card.py` 的前缀剥离在盘符/反斜杠下失效（Q1 修复覆盖了归一化，但环境变量里直接写反斜杠仍会被 bash 吃掉）。设 `~/.agate` 软链接用 `ln -s`（Git Bash 里 `~` 是 `C:\Users\<你>`）；无符号链接权限时改用系统环境变量 `AGATE_ROOT=/c/Users/<你>/agate/agate`。

**2. PATH 注入风险**：`C:\Program Files\Git\bin`（git.exe）和 `C:\Program Files\Git\usr\bin`（bash + coreutils）须在 PATH 里且**顺序靠前**，否则 `bash`/`grep`/`sed` 会解析到系统其他位置（或找不到）。`git --version` 与 `bash --version` 跑通即代表 PATH 正常。python 的 `Scripts/` 目录若与 Git 的 usr/bin 冲突，以实际 `which python`/`which bash` 为准调整顺序。

**3. Git Bash 里执行接入命令**：`python3 ~/.agate/scripts/agate-setup.py` 在 Git Bash 里跑（它内部调用 `install-hook.py` 装 hook）。Windows 无符号链接权限时配置物以**复制模式**安装（输出含「复制模式」提示），升级 Agateon 后需**重跑此命令**刷新（复制不自动跟随源文件，见 `platform-notes.md`「已知限制」）。

**4. `PYTHONUTF8=1`**：Windows 的 python 默认用系统 ANSI 代码页（GBK）解释源码/读写文件，Agateon 的 `.py` 工具按 UTF-8 读写协议文件会乱码/报错。在系统环境变量加 `PYTHONUTF8=1`，或 Git Bash 会话里 `export PYTHONUTF8=1`，让 python 3.7+ 以 UTF-8 模式运行。

**5. CRLF / `core.autocrlf` 处理**：仓库已含 `.gitattributes` 强制 LF（`*.md` 等文本规则除外，历史 review 文件保持 CRLF，见仓库根 `.gitattributes` 文件头注释）；若 clone 的是旧版本仓库（无该文件），手动 `git config core.autocrlf false` 再重新 checkout。已物化 CRLF 的工作区执行 `git add --renormalize .` 重规范化，否则 3 个 hook 薄壳 `.sh` 报 `\r` 语法错、卡片 sha256 校验 mismatch（py 文件已显式 `encoding="utf-8"` 读写，免疫）。

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

- **符号链接方式**（Linux / macOS 标准）：什么都不用做，orchestrator 提示词自动跟着新版本。**例外是 DSH**——它的 preset 是复制进 profile patch 的声明块（不是软链），升级后重跑一次 `agate-setup.py` 刷新；`agate-summary.py` 会报「漂移 / 已过期」提醒。
- **复制模式**（Windows 无符号链接权限）：重跑一次 `python3 ~/.agate/scripts/agate-setup.py` 刷新（`cp` 是旧手工步骤，已被该命令取代）。
- 两种方式都建议顺手跑一次 `python3 ~/.agate/scripts/agate-summary.py`——它会检测协议版本、根 `scripts/` 副本漂移，**以及四个平台接入产物的漂移**：产物须指向**某个已安装版本**的模板（这是"权威"的判据——项目用 `.agate-version` 钉版**不影响**该判定，全局产物本就与项目钉版无关）；它给**两级信号**：指向开发 checkout / 临时副本（**不在任何已装版本树内**）→ 警告「漂移」+ 修复命令；指向**已装但没有跟随 `current` 的版本** → 信息级「版本落后」提示（`agate-install.py` 装新版不删旧版，且接入产物指向具体版本目录，故升级后"落后"是常见状态，需重跑 `agate-setup.py` 跟上）；复制形态内容与任何已装版本都不一致 → 警告「已过期」。

**更新口径（与 `UPGRADING.md` 一致）**：更新 = `python3 ~/.agate/scripts/agate-install.py latest`（幂等）。安装 / 迁移 / 更新 / 回退完整对照，以及 hook 重装时机、根 `~/.agate/scripts/` 副本维护语义，见 `UPGRADING.md` 的「版本管理生命周期」节。

## 卸载

```bash
python3 ~/.agate/scripts/agate-setup.py --uninstall --all-projects --purge
```

本命令装的东西（平台身份 + git hook）由同一条命令对称卸载；`--list` 先看装了什么，
`--dry-run` 先预览。**不要直接 `rm -rf ~/.agate`**——平台接入物与项目侧 hook 会变断链
（复制模式下的陈旧 hook 可执行，会让 `git commit` 失败；软链断链或非可执行副本则被 git 静默忽略）。用户工作数据（`agate-workspace/` 等）卸载**不删**。
完整口径见 `agate/AGENTS.md`「卸载」节。
