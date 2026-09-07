# Platform Notes — 各平台适配说明

> 职责边界：平台适配权威源——各 Agent 平台（OpenCode/Claude Code/Codex 等）能力矩阵、Windows 原生安装指南（详见职责声明表，P2-design.md §0）

不同 Agent 平台对 agate 的支持程度不同，本文记录已知情况。

---

## OpenCode

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具派发 subagent | ✅ 可用 | 使用方法 B（general subagent + prompt 注入角色文件）|
| 自定义角色（--custom-role）| ❌ 不可用 | issue #29616，subagent 无法加载自定义角色 |
| 本地开发环境 | ✅ 完整 | P3-P8 全部阶段可执行 |

**推荐方式（方法 B）**：派发时在 prompt 里直接写入角色定义文件路径，让 subagent 自己读取。不使用 `--custom-role` 参数。

---

## Claude Code

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具派发 subagent | ✅ 可用 | Task tool 支持独立上下文 |
| 本地开发环境 | ✅ 完整 | P3-P8 全部阶段可执行 |

---

## Claude Project 会话（claude.ai）

| 能力 | 状态 | 说明 |
|------|------|------|
| task 工具 | ❌ 不可用 | 纯对话环境，无 task 工具 |
| 本地开发环境 | ❌ 受限 | 网络受限，npm/pip 安装受影响 |

**适用范围**：仅适合 P0-P2（设计规划阶段）。P3-P8 需交接给 OpenCode/Claude Code 执行。

**典型工作方式**：用 Claude Project 完成 P0-P2 并 push 到 main，再切换到 OpenCode 执行 P3-P8。

---

## Codex / Hermes / OpenClaw 等

待补充——如有使用经验，欢迎 PR。

---

## Hardening-roadmap 跨平台适配（自 v0.4 引入，持续生效）

hardening-roadmap 设计的核心 gate 机制（pre-commit hook + CI backstop）是 **git 协议级**的，自 v0.4 起所有平台统一可用。但配套能力有平台差异：

| 机制 | OpenCode | Claude Code | Codex | 说明 |
|------|---------|-------------|-------|------|
| pre-commit hook | ✅ 全功能 | ✅ 全功能 | ✅ 全功能 | git 机制本身，与平台无关 |
| `check-p6-provenance.py` 审计 | ✅ | ✅ | ✅ | 纯 Python + 文件系统 |
| `agent:` 字段协作规范 | ✅ | ✅ | ✅ | 文件级 metadata |
| `risk=high` 自审 WARNING | ✅ | ✅ | ✅ | hook 输出 exit 2 |
| CI backstop（gate 重跑 + provenance 重跑 + git blame WARNING）| ⚠️ 自实现 | ⚠️ 自实现 | ⚠️ 自实现 | GitHub Actions / GitLab CI / Gitea Actions 提供开箱实现（⚠️ Gitea 未实测） |
| 独立 git author 追踪（P2.10 根治）| ❌ | ❌ | ❌ | Phase 3 平台功能未实现 |
| `~/.agate` 软链接 / 版本目录 | ✅ | ✅ | ✅ | 文件系统级，无平台差异；TAG0008 起为版本管理根（软链或目录 + 指针），无符号链接权限时指针退化为文本文件 |

**CI backstop 说明**：`.github/workflows/protocol-tests.yml` 的 `gate-backstop` job 用 GitHub Actions 实现。ci-gate-backstop.py 原生支持 GitHub Actions / GitLab CI / Gitea Actions（通过 `detect_ci_platform()` 自动检测）。在自建 CI（Jenkins/本地）跑 agate 时：
- 需要等价实现：`git push` 后重跑 `scripts/check-gate.py` + `scripts/check-p6-provenance.py` + 调用 `ci-gate-backstop.py`
- 不实现 CI backstop 也能用——只是失去 `--no-verify` 绕过 hook 的兜底审计

**Codex 兼容性**：Codex subagent max_depth=1 与 P2.1 强制派发独立 subagent（risk=high）的兼容性：
- Codex 单层任务工具无法"再派发"——这种情况下 P2 review 必须由主 Agent 自己跑（agent=main）
- `check-gate.py` P2 对 `agent=main` 硬拦截（exit 1，不可自行批准评审）
- 升级到 Codex 多层派发（待官方发布）后兼容自动生效

---

## 验证记录

agate 的派发机制于 2026-06-12 在 OpenCode 上完成验证：
- Phase 1（方法 B 派发）✅
- Phase 2（方法 A 自定义角色）❌（issue #29616）
- Phase 3（上下文隔离）✅

完整验证报告存档：`archived/validation-report.md`

---

## Windows 原生（Git for Windows，不用 WSL）

> agate 的 gate 脚本已全部 Python 化（`.py`），不再依赖 bash + GNU coreutils——TAG0010 起**无 bash 环境（纯 cmd/PowerShell）成为可行选项**：脚本可直接 `python3` 运行。仅 3 个 git hook 入口保留 `.sh` 薄壳（定位 AGATE_ROOT + python 探测 + exec 对应 `.py` 主程序），需要 **Git for Windows** 自带的 sh 执行。以下仍按 Git for Windows 全功能方式说明。

### 前置条件

| 依赖 | 安装方式 | 说明 |
|------|---------|------|
| **Git for Windows** | https://git-scm.com/download/win （独立安装包，不依赖 GitHub 账号） | 提供 git + `sh`（hook 薄壳执行需要）。gate 脚本本体已不依赖其 bash/coreutils |
| **Python 3.8+** | https://www.python.org/downloads/ | 安装时勾选「Add to PATH」。全部 gate 脚本需要，**pyyaml 为强制依赖**（`pip install pyyaml`）|
| **pyyaml** | `pip install pyyaml` | **强制**。所有 py gate 脚本的 YAML 解析依赖（agate_common.py / 各状态读取工具），缺失时 fail-closed 阻断 |
| **Pillow（可选）** | `pip install Pillow` | 仅 check-p6-evidence.py 的像素方差/ahash 检测需要。未装时自动跳过（WARNING 不阻断）|
| **ruff（可选）** | `pip install ruff` | 仅开发者跑 `ruff check agate/` 时需要（替代 shellcheck，含 tests）。使用者不需要 |
| **pytest（仅开发者）** | `pip install pytest` | 使用者不需要跑测试；开发者跑 `python3 -m pytest agate/tests/`（Bats 已退役，TAG0011） |

### 前置环境配置（git 用户身份，**新环境必做**）

agate 协议脚本不读 git 用户配置，但 git 本身在 `git commit` 时若未设 `user.email` / `user.name` 会**直接拒绝 commit**（`fatal: unable to auto-detect email address`）——这是 git 自身行为，不是 agate 的问题。新环境**首次使用前**必须配置：

```bash
git config --global user.email "you@example.com"
git config --global user.name  "Your Name"
```

> 项目级 / 用户级 / 环境变量均可（`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL`），global 是最少侵入的入口。若仅个别项目需要不同身份，改用 `git config user.email ...`（项目级，不带 `--global`）即可，不影响其他项目。

### 安装步骤

1. **装 Git for Windows**：下载安装包，全程默认即可。它会在 `C:\Program Files\Git\` 安装 git + sh。

2. **验证 sh 可用（hook 薄壳执行需要）**：打开「Git Bash」（开始菜单），运行：
   ```bash
   bash --version
   ```
   应输出版本号。gate 脚本本体不需要 bash——验证纯 python 路径可用：

3. **装 Python + pyyaml**：
   ```bash
   python --version    # 应 3.8+
   pip install pyyaml
   ```

4. **clone agate 仓库**（任意 git 托管都行，不限于 GitHub）：
   ```bash
   git clone <你的 agate 仓库地址> ~/agate
   ```

5. **建立 `~/.agate` 软链接**（Git Bash 里 `~` 是 `C:\Users\<你>`）：
   ```bash
   ln -s ~/agate/agate ~/.agate
   ```
   > 若提示无法创建符号链接（无开发者模式/非管理员），改用环境变量：
   > 在系统环境变量里设 `AGATE_ROOT=C:\Users\<你>\agate\agate`（指向 agate 仓库的 `agate/` 子目录）。

6. **在项目仓库里装 hook**：
   ```bash
   cd /path/to/your/project
   python3 ~/.agate/scripts/install-hook.py
   ```
   > Windows 无符号链接权限时，hook 会以**复制模式**安装（输出含「复制模式」提示）。**升级 agate 后需重跑此命令**更新 hook（复制不自动跟随源文件）。

7. **验证 agate 可运行**：
   ```bash
   python3 ~/.agate/scripts/agate-summary.py
   ```
   应输出版本号 + 防护状态。

### 已知限制（Windows 原生）

| 限制 | 影响 | 规避 |
|------|------|------|
| `ln -sf` 退化为复制 | hook 不随 agate 升级自动更新 | 升级 agate 后重跑 `python3 ~/.agate/scripts/install-hook.py`；或开 Windows「开发者模式」启用真符号链接 |
| `core.autocrlf` CRLF 污染 | 3 个 hook 薄壳 `.sh` 报 `\r` 语法错；py 文件已显式 `encoding="utf-8"` 读写（免疫），仅卡片 sha256 校验受 hash 影响 | 仓库已含 `.gitattributes` 强制 LF；若 clone 旧版本无此文件，手动 `git config core.autocrlf false`。已 clone 且已物化 CRLF 的工作区需 `git add --renormalize .` 重规范化 |
| pytest 需安装 | 开发者无法跑 `python3 -m pytest` 测试 | `pip install pytest`（Windows 原生 python 直接可用）；或用 WSL 跑测试（使用不受影响） |
| CI 仅 ubuntu | Windows 本地行为无 CI 兜底 | 靠本地验证；protocol-tests.yml 的 pytest job 已加 `windows-latest` matrix（`-m windows_smoke` 冒烟，见 AGENTS.md 测试约定） |
| 路径分隔符 | MSYS2 自动转换 `/c/Users/` <-> `C:\Users\`，但极少数硬编码路径可能出问题 | 遇到时用 `cygpath -w` 转换 |
| Windows Store `python3.exe` 占位符 | 部分 Windows 安装（未关闭「应用执行别名」）下，PATH 上的 `python3`（有时 `python`）解析到 Microsoft Store 的占位符可执行文件——`command -v`/`where` 能找到它、有执行位，但实际执行任意命令一律非零退出，不解释传入的脚本 | 3 个 hook 薄壳（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh`）的探测循环已改为逐候选先做一次可执行性小测试（通用 exit code 判据），命中占位符会跳过并继续尝试下一候选；也可设置 `AGATE_PYTHON` 环境变量显式指定真实 Python 解释器的完整路径，直接跳过整个探测循环 |

> **DEBT0014 验证边界说明**：以上 Store 占位符现象与 `AGATE_PYTHON` 机制的修复，验证方式是静态代码修复 + Linux 环境下用模拟 stub 复现「`command -v` 命中但执行非零退出」症状特征做的回归测试 + CI protocol-tests.yml 的 `windows-latest` matrix 冒烟——本仓库开发环境是 Linux，未在真实 Windows 环境下触发过 Store 占位符场景本身，上述描述是已知机制的静态修复说明，不代表已在 Windows 环境中复现并验证通过。

### latest / current 指针在无符号链接权限时的形态（TAG0008 版本管理）

`~/.agate` 版本管理根目录里的 `latest` / `current` 是**纯指针**：Linux/macOS 用 POSIX 软链（`latest → v0.48.0`），Windows 无符号链接权限（或 `AGATE_HOOK_COPY_MODE=1`）时**退化为文本指针文件**——文件内容为指向的版本目录名（如 `v0.48.0`），解析时按内容恢复目标路径（`agate_common.py` 的指针链解析兼容软链与文本两形）。`.agate-root` 标记先例沿用：复制模式下安装的 hook / orchestrator 副本写 `.agate-root` 记录安装根，解析入口（`resolve-entry.py`）据此恢复 AGATE_ROOT。行为与单软链时代一致：解析失败回退 current，绝不静默禁用 gate。

`install.sh --versions`（新机一键进入版本管理布局）保持 POSIX shell（无 bash 扩展）。决策 B1 下根 `~/.agate/scripts/` 用**拷贝**（`shutil.copytree`，非软链）建立，恰好规避 Windows 符号链接权限问题——比软链更平台无关，也没有 `latest` / `current` 指针那样的文本退化形态。

### 不支持的场景

- **纯 cmd/PowerShell 无 bash**：**TAG0010 起成为可行选项**——gate 脚本已全部 Python 化，`python3 ~/.agate/scripts/xxx.py` 可直接运行（P0-P8 全程可执行）。唯一受限：git hook 入口薄壳仍需 sh 执行，无 bash 时 hook 不触发（可用 CI backstop 兜底 `--no-verify` 场景）。
- **Cygwin（非 MSYS2）**：理论上可行但未测，不保证。推荐 Git for Windows。

## DSH（deepseek-harness）

> 接入步骤见 `SETUP.md`「步骤 2-DSH」（接入命令单一真相源，本条目只做能力差异说明）；preset/skill 模板文件在 `assets/templates/dsh/`。已实机验证（2026-08-21，DSH v0.1.0-rc.8）——新兴平台，机制可能随版本变化。最近复核（2026-09-01，DSH v0.1.2-alpha.3，实机核验通过）：工具面（subagent/subagent_fork/workflow/ralph/goal）、preset 工具行包名与 delegation 组、skill 发现机制、`sampleOverCapGlobResults` 挂载关键字段均未漂移，与当前 DSH 标准 preset 结构逐行一致。

**平台形态**：pnpm monorepo + cordis 插件框架；身份注册用 **agent-preset**（`agent.cordis.yml` + `preset.yml`），
skill 是打包/分发单元（SKILL.md + frontmatter，自动进会话技能目录）。

**能力差异（与 OpenCode/Claude Code 对照）**：

| 能力 | OpenCode/Claude Code | DSH |
|------|---------------------|-----|
| orchestrator 身份注册 | `.agents/orchestrator.md` 软链（mode: primary）| agent-preset（persona.text + 工具行）|
| 派发 subagent | task 工具 | `subagent` / `subagent_fork`（spawn/fork 两种上下文模式）|
| 批量并行派发 | 手工多路 task | **workflow 脚本**（agent/pipeline/parallel/phase）|
| 独立复核（judge）| 手工保证 fresh context | **ralph**（每轮全新 agent + bounded handoff）|
| 跨轮续跑 | 手动重开会话 | **goal**（持久化目标，自动续轮）|
| 实时 gate | 仅 git hook（commit 时）| 另可挂 **session hooks**（PostToolUse 每步触发）|

**已知注意**：
- 沙箱默认 workspace-write，协议本体目录可能只读（写仓库内文件 Errno 30）——任务工作区放可写位置
- DSH 无 `.claude/agents/*.md` 等价物——不要试图把 orchestrator-template.md 软链进 DSH 目录，用 preset
