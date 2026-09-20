# 项目侧接入（orchestrator 注册）现状与缺口——交接说明

> **性质**：现状盘点 + 待办交接，写于 2026-09-20（v0.73.0 之后，main = `77e33da`）。**未立项、未设计定稿、未改任何代码**。
> **读者**：接手的 agent。先读本文，再动手。本文是快照，事实以代码为准（下列文件/行号会漂移，按符号名找）。

## 1. 一句话结论

**项目侧接入有一半是空白**：`hook` 有命令且感知版本；**orchestrator 身份注册没有命令**，全靠人手写 `ln -sf`，且文档写死指向 `current`，与多版本设计（项目 `.agate-version` 钉版）矛盾。

## 2. 起因

2026-09-20 用户问"本项目的 Claude Code orchestrator 安装到哪儿了"，查证发现：
- `~/.claude/agents/`、主 checkout `.claude/agents/` 均不存在 orchestrator；`~/.config/opencode/agents/` 为空。
- `agate/scripts/*`、`install.sh` 中**没有任何脚本会创建 `orchestrator.md`**（`grep -l "orchestrator.md\|agents/orchestrator"` 无命中）。
- 用户质疑："项目侧安装现在是个空白？也不支持版本？不可能写死 ln 到 `~/.agate/current/...` 吧？"——**质疑成立**。

## 3. 现状：各环节谁管、是否感知版本

| 环节 | 现状 | 感知项目 `.agate-version`？ |
|---|---|---|
| 装 hook | `python3 ~/.agate/scripts/install-hook.py`（`agate/scripts/install-hook.py`）。装的是**固定解析入口** `resolve-entry.py` 薄壳，运行时才解析版本 | **是**（BDD-18：切版本不用重装 hook） |
| 版本解析 | `agate-resolve.py` → `agate_common.resolve_version_root`（优先级 `AGATE_ROOT` > `AGATE_HOME` → 项目 `.agate-version` → `current`）；hook 用 `resolve_hook_root` | 是 |
| orchestrator **运行时**读阶段卡/脚本 | `orchestrator-template.md` 第 20 行：`{agate_root}` 先取 `$AGATE_ROOT`，否则跑 `agate-resolve.py`，失败回退 `~/.agate/current/agate` | 是 |
| **orchestrator 身份文件注册** | `agate/SETUP.md` 步骤 2：手写 `ln -sf "$AGATE_DIR/orchestrator-template.md" .claude/agents/orchestrator.md`，`AGATE_DIR` 写死为 `~/.agate/current/agate` | **否** |
| DSH / Codex / dispatch-routing scaffold 的注册 | 同样手写 `ln -sf "$AGATE_DIR/assets/templates/dsh/…"`（SETUP 步骤 2-DSH），`AGATE_DIR` 同为 `current` | 否 |
| 引导入口 | README「快速上手」第 2 步把"注册 orchestrator"和"装 hook"并列，但只有后者有命令 | — |

## 4. 缺口与后果

1. **无命令**：项目侧接入 = 读 SETUP + 手写命令。对比 hook 有 `install-hook.py`，不对等。
2. **版本错位（核心缺陷）**：项目若钉 `.agate-version: agate: v0.71.1`，则阶段卡/脚本/gate 走 v0.71.1，但 `.claude/agents/orchestrator.md`（软链→`current`）是 **current（如 v0.73.0）的模板提示词**。提示词与其所操作的协议版本错位。`SETUP.md`「升级 Agateon 之后」还写着"符号链接方式：什么都不用做，提示词自动跟着新版本"——这是 follow-`current` 语义，与钉版语义冲突。
3. **`SETUP.md` 全文不出现 `.agate-version`**；设计文档里也未找到"orchestrator 身份文件如何跟版本"的讨论，看起来是 TAG0008（版本管理机制，v0.50.0）遗漏的一环。
4. **Windows 复制模式**（无软链权限时 `cp`）：升级后不自动同步，SETUP 承认无漂移检测；`agate-summary.py` 只查 `scripts/` 副本漂移，不查 orchestrator.md。
5. **已知相关风险（非本缺口，但会互相放大）**：`.agate-version` 声明**未安装**的版本时仅 stderr 警告 + 静默回退 `current`（exit 0）。实测：钉 `v0.71.1`（已卸载）→ 解析到 `v0.73.0`。`UPGRADING.md`「项目钉版本」处已写为已知风险。
6. **遗留脏数据**（主 checkout，gitignored，本地环境）：`.claude/settings.local.json` 含权限 `Bash(ln -s ../docs/converse/agents .claude/agents)`，指向已不存在的目录，是旧接入方式残留，可清。

## 5. 本机当前状态（2026-09-20）

- `~/.agate`：全新安装的版本管理根，`current → latest → v0.73.0`，`v0.73.0/` 为**本体包形态**（2.3M）。旧根已备份为 `~/.agate.bak-20260920`（另有更早 `~/.agate.bak`），**均未删除**。
- 本项目（agateon 主 checkout）已手动执行 SETUP 步骤 2 的 Claude Code 分支：`.claude/agents/orchestrator.md` → `~/.agate/current/agate/orchestrator-template.md`。`.claude/` 被 `.gitignore` 忽略，不影响仓库。本项目**未钉版本**，故暂无错位；这条软链是手写的，不是命令产物。
- hook：开发 checkout 三个 hook 指向 `~/.agate/scripts/*.sh`，已验证可用。

## 6. 建议方案（用户尚未拍板）

**通道判断**：会改 `agate/scripts/*` 与 `agate/SETUP.md`（触发 SELF-GATE）⇒ **hotfix 通道不适用**，须 worktree + PR + 独立评审（`AGENTS.md`「改动通道」）。**不必走完整 TAG（P0-P8）**——体量约"一个 ~50 行小命令 + 测试 + SETUP/README 改文档"；用户此前对纯文档整理明确说过"不用立项"。是否建 TAG 由用户/接手方定。

**设计点（需拍板，见 §7）**：orchestrator 身份文件怎么跟版本。
- **A（倾向）**：新命令（暂定名 `agate-install-project.py`，或给 `install-hook.py` 加子命令/参数）按**解析到的版本**建软链，指向 `~/.agate/vX.Y.Z/agate/orchestrator-template.md`；改 `.agate-version` 后重跑一次命令重指。
- **B**：软链仍指 `current`，仅在文档补"钉版项目须重跑命令"。基本是现状，**不解决错位**。
- 另可考虑 **C**：生成薄壳身份文件（frontmatter + "读解析后的路径"），避免每次切版本重指——需评估 Claude Code 对 frontmatter/正文的解析约束（缺 `name: orchestrator` 会被静默跳过，见 SETUP 步骤 2）。

**命令应覆盖（草案）**：
1. 装 hook（复用 `install-hook.py`）。
2. 建 orchestrator 身份，按解析版本；按平台分支：Claude Code（`.claude/agents/`）、OpenCode（`.opencode/agents/`）、DSH（preset 三件套）、Codex（SETUP 步骤 2-Codex，无软链）。
3. Windows 无软链权限 → 复制模式，并**给出漂移检测**（补 `agate-summary.py` 对 orchestrator.md 的检查）。
4. 可选写 `.agate-version`；写前校验该版本已安装（避免 §4.5 的静默回退）。
5. 幂等；已存在的非本工具生成文件不覆盖（沿用 `install-hook.py` 的备份习惯）。

## 7. 待用户拍板的问题

1. 方案 A / B / C 选哪个？
2. 是否建 TAG 或走"无 TAG worktree + PR"？
3. 命令形态：新脚本 `agate-install-project.py`，还是并入 `install-hook.py`？（`install-hook.py` 的 `AGATE_ROOT` 解析刻意保持 `argv > env > ~/.agate`，不同于 `resolve_agate_root`，见其模块 docstring——并入需注意语义。）
4. 是否顺带处理 §4.5（钉未安装版本静默回退）？它是独立问题，建议单列。

## 8. 接手方须知

- 改前先读：`AGENTS.md`（改动通道 / 改脚本的工作流 / 测试约定 / dogfooding worktree）、`agate/SETUP.md`（步骤 2、4、5、「升级之后」）、`agate/UPGRADING.md`「版本管理生命周期」（解析优先级表、hook 重装时机口径）、`agate/scripts/install-hook.py`、`agate/scripts/agate_common.py`（`resolve_version_root` / `resolve_hook_root`）。
- 已有测试参照：`agate/tests/unit/test_install_hook.py`、`test_hook_resolve_entry.py`。流程：先写红测试再转绿；`check-protocol-consistency.py --strict-errors-only` 须 0 ERROR；改 SETUP/README/scripts 触发 SELF-GATE，commit 需 `self-gate-review:` 或 `self-gate-skip:` trailer。
- **不要动**：`agate/rules/phases.yaml`（BDD-39 字节锁）；`~/.agate` 与主 checkout 在他人执行 worktree 任务期间不应被修改；本机两个 `~/.agate.bak*` 备份由用户决定何时删。
- 主 checkout 上 CI/workflow 改动须用户明确许可（本项目无此需求）。
