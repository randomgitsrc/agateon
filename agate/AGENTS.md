# Agateon 协议本体

> 本目录是 **Agateon 协议的运行时本体**。
> 软链接 `~/.agate` 默认指向这里（你克隆 Agateon 时指定的仓库根下的 `agate/` 子目录）。TAG0008 起 `~/.agate` 可为**版本管理根目录**（`~/.agate/vX.Y.Z/` 版本目录 + `latest`/`current` 指针），本目录即某版本检出的协议本体；存量单软链布局（legacy）仍兼容，解析直接落到软链目标。
> 路径表述：协议文档内写 `{agate_root}/WORKFLOW.md` 等于 `本目录/WORKFLOW.md`（`{agate_root}` 经项目版本解析得到，见 `agate-resolve.py`）。

---

## 这是什么

仓库根的 `docs/` 目录存放 Agateon **项目的开发资料**——设计文档、评审记录、路线图，以及迁移前旧布局下的历史复盘（docs/reviews/，2026-08-19 前）。这些都是仓库维护者（author）写的，**使用者无需阅读**。新复盘归 `tasks/{Txxx}/retrospective.md`（模板见 `agate/assets/templates/retrospective-template.md`），同样是维护者产物，使用者无需阅读，但路径不在 `docs/` 下。

你看到 `agate/` 这一层，是**协议本体**——里面是一组编排协议文件，告诉 AI Agent 怎么用 Agateon 完成一个软件工程任务。**你（使用者）从这里开始**：

## 入口导航

按你的动作找对应文档：

| 你要做什么 | 看这里 |
|------|------|
| 第一次接入 Agateon 到我的项目（把 orchestrator 注册成可调用的 agent）| `SETUP.md`（平台相关的具体步骤，从这里开始）|
| 理解 P0-P8 阶段流程与裁剪规则 | `WORKFLOW.md`（主流程，主入口） |
| 查跨阶段规则（retry 上限 / 状态转移 / C8 评审映射）| `rules/`（phases.yaml / dispatch.yaml / roles.yaml 权威源 + schema/ + 既有 review-mapping.md / state-transitions.md md）|
| 理解 orchestrator-template.md 本身该怎么用 | `orchestrator-template.md`（对所有项目内容完全一致，符号链接，不拷贝——项目特定信息写 `assets/templates/project.md`）|
| 派发 subagent 的细节 | `dispatch-protocol.md` |
| 状态机/转移规则/重试上限 | `state-machine.md` |
| 角色体系（双层角色） | `role-system.md` |
| 用 git 持久化状态 | `git-integration.md` |
| /loop 自动编排 | `loop-orchestration.md` |
| 不同平台适配（OpenCode/Claude Code/Windows）| `platform-notes.md` |
| 已知局限 | `LIMITATIONS.md`（使用前建议先读） |
| 术语表 + 上下文 | `CONTEXT.md`（Ubiquitous Language） |
| 架构决策记录 | `adr.md`（A7 审查锚点） |
| 存量项目升级（破坏性变更）| `UPGRADING.md` |
| 改 Agateon 协议本体并跑测试（maintainer）| `tests/README.md` |

## 给 Agent 的快速指令

如果你是被主 Agent 派发的 subagent：

1. 读 `dispatch-protocol.md` 了解派发协议
2. 读 `assets/execution-roles/{你的角色}.md`（如 analyst/architect/implementer 等）
3. 按角色文件的指令执行
4. 退出时确保产出了正确的阶段文件（如 `P2-design.md`）

如果你是主 Agent（编排者）：

1. 从 `orchestrator-template.md`（符号链接进你的平台 agent 目录，接入步骤见 `SETUP.md`）进入
2. **按 mapping 表加载当前阶段卡片**（`phase-cards/P{N}-*.md`）——不必全读 8 个协议文件
3. 阶段卡片自包含（前置条件 / 派发 / 产出 / gate / 推进 / 常见错误 / 下游影响）
4. 跨阶段规则（retry / 转移 / 评审映射）在 `rules/` 下按需查阅
5. 卡片查不到的信息，回退到完整协议文件

角色文件清单：

```
assets/execution-roles/
├── analyst.md            # P1 需求分析
├── architect.md          # P2 设计
├── consistency-reviewer.md # P7 一致性交叉检查
├── implementer.md        # P4 实现/P8 发布
├── test-designer.md      # P3 测试设计
├── verifier.md           # P5/P6 验收
└── vision-analyst.md     # P6 UI/视觉验收

assets/review-roles/
├── review.md             # 通用评审
├── design-review.md      # 设计评审
├── plan-ceo-review.md    # 计划层（产品维度）评审
├── plan-eng-review.md    # 计划层（工程维度）评审
├── plan-design-review.md # 计划层（设计维度）评审
├── cso.md                # 首席安全官评审
├── qa.md                 # 质量保障评审
├── investigate.md        # 事后排查
├── protocol-alignment-review.md  # 协议-脚本对齐审查（self-gate）
├── requirements-review.md  # P1 需求基线评审
└── judge.md              # P6.5 验收独立裁判（所有任务强制，fresh context 重验全部 BDD）
```

## 升级 Agateon

```bash
# 进入你克隆 Agateon 的目录
cd <你克隆 Agateon 的目录> && git pull
```

**已有 Agateon 项目升级，先读 `UPGRADING.md`**——它讲清楚旧任务数据（active-tasks.md/.state.yaml/任务编号）如何处理，避免踩到破坏性变更。

下次 commit 自动用新版本协议。pre-commit/commit-msg/pre-push 三个 hook 经 `python3 ~/.agate/scripts/install-hook.py` 安装（`ln -sf` 软链 / Windows 复制模式），指向**固定解析入口** `resolve-entry.py`，运行时按项目 `.agate-version` 解析到对应版本目录——项目锁定旧版用旧版 gate、无声明用全局 current，切版本**无需重装 hook**。（Windows 无符号链接权限时以复制模式安装，升级后需重跑 `python3 ~/.agate/scripts/install-hook.py`，见 `platform-notes.md`「Windows 原生」章节。）

版本管理形态（TAG0008 起）：
```bash
install.sh --versions                                 # 新机一键进入版本管理布局（建 repo/ + 首个版本 + 指针 + 根 scripts/ 副本）
python3 ~/.agate/scripts/agate-install.py latest       # 更新到最新发布版（幂等；无参等价于 latest）
python3 ~/.agate/scripts/agate-install.py vX.Y.Z       # 装指定版本目录（幂等）
python3 ~/.agate/scripts/agate-install.py --uninstall vX.Y.Z   # 卸载版本（含项目引用保护）
python3 ~/.agate/scripts/agate-resolve.py              # 查看当前项目解析到的版本 + 原因
```
> GitHub 直装得到的元仓库整仓形态版本目录（协议在 `agate/` 子目录）由 `_protocol_root` 两形态探测（`vdir/scripts` 先、`vdir/agate/scripts` 后）适配；根 `~/.agate/scripts/` 是随每次安装/升级刷新的单源副本（非软链）。完整的安装 / 迁移 / 更新 / 回退口径以 `UPGRADING.md`「版本管理生命周期」节为权威。

## 卸载

```bash
# 单软链布局（legacy）：删软链接 + 删仓库
rm ~/.agate                          # 删软链接
rm -rf <你克隆 Agateon 的目录>          # 删仓库

# 版本管理布局（TAG0008 起）：卸载具体版本目录 + 清理指针
python3 ~/.agate/scripts/agate-install.py --uninstall vX.Y.Z
rm -rf ~/.agate                       # 卸载整个版本管理根（已装版本全删）
```

## 更多

仓库根的 `README.md`（英文）与 `README.zh-CN.md`（中文镜像）是面向**新用户**的接入门面；本目录是面向**深入使用者和 Agent** 的协议本体入口。维护 Agateon 本体：`python3 -m pytest agate/tests/`（详见 `tests/README.md`）。

有问题看 `LIMITATIONS.md`，别在文档没覆盖的地方反复猜。

**推荐伴侣**：superpowers（单 Agent 行为纪律层）——强化"Agent 自己怎么做对"，与 Agateon 的编排结构层（多 Agent 隔离+gate）正交互补。superpowers 不替代 Agateon，Agateon 不替代 superpowers，各管一层。
