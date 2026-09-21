<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/brand/logo-lockup-dark-bg.svg">
    <img alt="Agateon" width="320" src="docs/brand/logo-lockup.svg">
  </picture>
</p>

# Agateon
> **Agateon**（原名 agate）——本项目已改名，下方徽标与安装命令已指向新仓库。
> 一种编排协议，用构建系统验证编译器的方式验证 AI Agent。

[![version](https://img.shields.io/badge/version-v0.75.0-blue)](https://github.com/randomgitsrc/agateon)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](README.md) | [中文](README.zh-CN.md)

## Agateon 是什么？

Agateon 是一套面向软件工程任务的文档 + 脚本编排协议。没有运行时、没有守护进程、没有构建步骤——只是一组 Markdown 协议文件加 gate 检查脚本，任何编码 Agent 都能读取并运行。单个编排 Agent（orchestrator）从不亲自写代码。它通过八个阶段派发专职 subagent（P1 需求 → P2 设计 → P3 测试先行 → P4 实现 → P5 验证 → P6 验收 → P7 一致性 → P8 发布），外加 P6 与 P7 之间一道强制的独立裁判关卡（P6.5）——由 fresh context 的 judge 逐条重验全部验收标准。每阶段结束后、状态机推进前，都必须通过一次客观的 gate 检查。状态落盘到版本化 Markdown（外加 append-only 的 `gate-events.jsonl` 事件账本），进度在崩溃后得以存活，且可供人审计。

## 为什么用 Agateon？

LLM Agent 在长任务上强大但不可靠：上下文被污染、subagent 漂移、"看起来完成了"成了唯一的质量信号。Agateon 对待 AI Agent，就像构建系统对待编译器——不信任输出，用 gate 去验证。

- **Gate 是硬边界。** 进度由客观信号决定——测试运行器的 exit code、类型检查器、git log——而不是"看起来差不多"。
- **状态落盘。** 每个阶段的产出都写入版本化 Markdown，工作中断后可从上次完成处恢复，且可供人审计。
- **角色隔离。** 每个阶段由专职 subagent 执行，编排 Agent 的上下文保持干净，评审真正独立。
- **零基础设施。** 你的 Agent 只需读文件和跑命令——无需部署任何东西，无需运维任何服务。

> agent gates on → Agateon

## 快速开始

1. **安装 Agateon。** 使用一键安装脚本——它会进入**版本管理布局**（在 `~/.agate/vX.Y.Z/` 下安装版本目录，配 `latest` / `current` 指针；`~/.agate` 是版本管理根**实体目录**）：
   ```bash
   curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
   ```
   不带参数的 `install.sh` 等价于 `install.sh --versions`。若 `~/.agate` 仍是旧版本遗留的软链，该命令会 fail-closed 拒绝并给出三步迁移指引（先备份软链再重跑），详见 [`agate/UPGRADING.md`](agate/UPGRADING.md) 的「v0.73.0」节。之后用版本管理器按项目更新或钉版。安装 / 迁移 / 更新 / 回退完整口径见 [`agate/UPGRADING.md`](agate/UPGRADING.md) 的「版本管理生命周期」节：
   ```bash
   install.sh --versions                                  # 进入版本管理布局（repo/ + vX.Y.Z/ + 指针）
   python3 ~/.agate/scripts/agate-install.py latest       # 更新到最新版（幂等）
   python3 ~/.agate/scripts/agate-install.py v0.49.0      # 钉指定版本
   python3 ~/.agate/scripts/agate-install.py --check      # 环境探测
   ```
2. **注册编排 Agent。** 一条命令完成：`python3 ~/.agate/scripts/agate-setup.py`——自动探测已装平台、注册 orchestrator 身份（默认全局）、安装 git hooks。平台差异与手工兜底（OpenCode、Claude Code、DSH、Codex、Windows 复制模式）见 [`agate/SETUP.md`](agate/SETUP.md)。
3. **运行你的第一个任务。** 用编排 Agent 开启一个会话。工作区（`agate-workspace/`）在编排 Agent 首次运行时自动初始化；一次性接入步骤见 [`agate/SETUP.md`](agate/SETUP.md)。

## 工作原理

```
Orchestrator
  │ 派发
  ▼
P0 brief → P1 analyst → P2 architect → P3 test-designer → P4 implementer
         → P5 verifier → P6 verifier → P6.5 judge → P7 consistency-reviewer → P8 release
  │ 每阶段之后
  ▼
gate 检查（测试运行器 exit code、类型检查器、git log、BDD 运行）
  │ 通过
  ▼
状态落盘（active-tasks.md / .state.yaml / gate-events.jsonl）→ 进入下一阶段
```

编排 Agent 只做四件事：读状态、派发 subagent、跑 gate、更新状态。它从不亲自写阶段产出物。一个阶段只有在其 gate 通过时才能推进；gate 失败会把阶段弹回（在重试上限内），然后状态机才继续。阶段定义与裁剪规则见 [`agate/WORKFLOW.md`](agate/WORKFLOW.md)。

## 支持的平台

| 平台 | 任务工具 | 推荐用法 |
|----------|-----------|-----------------|
| OpenCode | ✅ | 完整 P0-P8 |
| Claude Code | ✅ | 完整 P0-P8 |
| DSH | ✅ | 完整 P0-P8 |
| Codex | ✅ | 完整 P0-P8 |
| Claude Project 会话 | ❌ | 仅设计阶段（P0-P2） |

四个平台都跑完整 P0-P8，但**身份接入物形态不同**：Claude Code / OpenCode 是 agent md 文件，DSH 是 agent-preset 三件套，Codex 靠 skill（它没有 agent 注册机制）。**接入已命令化**——一条命令自动探测并按平台选对形态：

```bash
python3 ~/.agate/scripts/agate-setup.py
```

细节见 [`agate/SETUP.md`](agate/SETUP.md) 步骤 2；各平台能力差异的权威源是 [`agate/platform-notes.md`](agate/platform-notes.md)（含原生 Windows / Git for Windows 适配）。

## 卸载

```bash
# 清掉平台接入物 + 所有装过 agateon 的项目（含 git hook），再删本体
python3 ~/.agate/scripts/agate-setup.py --uninstall --all-projects --purge
```

三条保证：

| 保证 | 说明 |
|------|------|
| **不误删你的东西** | 删任何文件前先**按事实验证归属**（软链是否指向本安装、内容是否等于权威模板）；证不出来就**保留并报告**，绝不猜着删 |
| **不动你的工作数据** | `agate-workspace/`（任务 / 复盘 / 技术债）、`.agate-version`、`AGENTS.md` 等**只报告不删**——那是你的成果，不是安装物 |
| **不留坏状态** | 装 hook 时备份过你原有的 hook，卸载时**还原**；否则会留下指向已删脚本的断链或陈旧副本——**复制模式（含 Windows）下的陈旧 hook 仍可执行，会让 `git commit` 直接失败**（软链断链、或非可执行的副本，则被 git 静默忽略） |

分步用法：

```bash
python3 ~/.agate/scripts/agate-setup.py --list                    # 先看装了什么（含台账里的项目）
python3 ~/.agate/scripts/agate-setup.py --uninstall --dry-run     # 预览将删什么
python3 ~/.agate/scripts/agate-setup.py --uninstall --scope global  # 只清全局接入物（留项目侧）
python3 ~/.agate/scripts/agate-setup.py --uninstall --all-projects  # 清全局 + 台账里每个项目
python3 ~/.agate/scripts/agate-setup.py --uninstall --purge         # 再删本体（收尾）
```

在**项目里**装过（`--scope project`）时，安装会把该项目登记到**安装台账**（`<安装根>/installed-projects.json`），`--all-projects` 据此把它们全部清干净——这是「多处散落」不遗留断链的机制。

若安装根不在默认位置（`AGATE_HOME` 覆盖过），把上面命令里的 `~/.agate` 换成实际安装根；`--list` 会打印真实路径。

## 文档

| 如果你要…… | 请读 |
|-----------------|------|
| 首次把 Agateon 集成进项目 | [`agate/SETUP.md`](agate/SETUP.md) |
| 理解 P0-P8 阶段工作流与裁剪规则 | [`agate/WORKFLOW.md`](agate/WORKFLOW.md) |
| 查跨阶段规则（retry 上限 / 状态转移 / C8 评审映射） | [`agate/rules/`](agate/rules/)——`phases.yaml` / `dispatch.yaml` / `roles.yaml` / `dispatch-tiers.yaml` + `schema/`，与 `state-transitions.md` / `review-mapping.md` 并列 |
| 阅读协议本体入口（面向 Agent 与深度用户） | [`agate/AGENTS.md`](agate/AGENTS.md) |
| 把 Agateon 适配到你的平台（Claude Code / OpenCode / DSH / Codex / Windows） | [`agate/platform-notes.md`](agate/platform-notes.md) |
| 了解已知结构性局限 | [`agate/LIMITATIONS.md`](agate/LIMITATIONS.md) |
| 升级前检查破坏性变更 | [`agate/UPGRADING.md`](agate/UPGRADING.md) |
| 查阅术语表 / 统一语言 | [`agate/CONTEXT.md`](agate/CONTEXT.md) |
| 查阅架构决策记录 | [`agate/adr.md`](agate/adr.md) |
| 运行测试套件（维护者） | [`agate/tests/README.md`](agate/tests/README.md) |

## 设计原则

- **协议文档，而非代码框架。** 零基础设施——任何能读文件的 Agent 都能使用 Agateon。
- **Gate 是硬边界。** 阶段是否通过由客观、外部产出的结果决定，而非主观的"看起来没问题"。
- **状态落盘。** 任何中断都从最后一个已完成阶段恢复。
- **角色隔离。** 每个阶段由专职 subagent 执行；编排 Agent 从不用实现工作污染自己的上下文。

Gate 按"被评判的产物由谁产出"分为两类信任级别：

| 类型 | 阶段 | 判定依据 | 信任 |
|------|--------|-----------|-------|
| 外部产出 gate | P3、P4、P5 | 外部工具输出（测试运行器 exit code、类型检查器、git log） | 高——编排 Agent 无法伪造外部输出 |
| 自写文件 gate | P1、P2、P6、P7 | 编排 Agent 自己写的文件 | 缓解——作者与评判者同为一人 |

自写 gate 只能缓解、无法根治，依靠证据存在性检查、客观 provenance 审计、BDD 计数对照来提升造假成本并留下审计线索。强制的 P6.5 独立裁判关卡在 P6 之上再加一层：fresh context 的 judge 只凭证据与 git log 逐条重验全部验收标准，并有 append-only 事件账本兜底。见 [`agate/LIMITATIONS.md`](agate/LIMITATIONS.md) 中的局限 3。

采用是渐进式的。裁剪由 P1 判定，不是自动的：分析师按"复杂度 × 风险"矩阵对任务分类，声明仪式档位（thin / standard / full，fail-closed 到 standard），为每个跳过的阶段写明理由，由主 Agent 确认。小改动单点任务走裁剪流程（P1 + P3 + P4 + P5）——P3 测试先行默认保留，仅在有明确理由时才跳过（配置类改动，或 ≤3 行且已有回归测试覆盖的改动）；P7 一致性在低/中风险任务中可裁剪，高风险（安全/数据/权限）任务必须保留。中改动走完整 P1-P8；高风险任务强制保留验收与一致性，并建议人工最终评审。P6 验收与 P6.5 裁判不可裁剪。

## 已知局限

Agateon 走文档协议路线，带着结构性局限：其 gate 的质量上限、角色隔离的认知（而非真正独立）属性、以及编排 Agent 的判断作为单点故障。**在采用之前请读 [`agate/LIMITATIONS.md`](agate/LIMITATIONS.md)——它对这套协议解决不了什么很诚实。**

## 参与贡献

Agateon 本身就是用 Agateon 开发的。从维护者入口 [`agate/AGENTS.md`](agate/AGENTS.md) 开始，用以下命令运行测试套件（加 `-n auto` 并行约 3.5x 提速）：

```bash
python3 -m pytest agate/tests/
```

## 许可证

[MIT](LICENSE)
