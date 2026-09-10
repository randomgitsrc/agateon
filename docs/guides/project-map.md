# Agateon 项目导航地图（整仓）

> 给谁看：新会话 / 新开发者，10 分钟建立整仓心智模型；老手回仓时快速恢复上下文。
> 怎么用：先读「2. 仓库四块」看全局，再按意图查「4. 权威源导航」和「5. 常见操作入口」。
> 原则：**本文件只收录导航信息，不重复权威源内容**——目录结构、命令、机制细节一律指向各
> 权威源（仓库根 `AGENTS.md` 反膨胀原则）。协议本体内部的入口仍是 `agate/AGENTS.md`，两者
> 分工：本文件看全局，`agate/AGENTS.md` 看协议体内部。
>
> 文中路径一律相对仓库根（如 `agate/WORKFLOW.md`）。

## 1. 这是什么

Agateon（原 agate，2026-08 改名，意为 "agent gates on"）是一个**文档 + 脚本型的 AI Agent
软件工程编排协议**——像构建系统验证编译器一样验证 AI Agent。无运行时、无守护进程：主 Agent
把每个阶段派发给独立上下文的 subagent，每阶段之后跑一次客观 gate（exit code / git 状态 /
BDD 计数），状态机才前进；状态全部落盘到版本控制下的 Markdown。

- 仓库：`randomgitsrc/agateon`，MIT 协议；版本以 README badge / `git describe --tags` 为准
- 起源：2026-06-16 首个 commit，由 Agateon 自身 dogfooding 驱动演进（持续演进中）
- 规模：`agate/scripts/` 约 60 个 Python 脚本 + 3 个 `.sh` hook 薄壳（脚本清单见 `agate/scripts/README.md`）；测试用例数以 `bash agate/tests/scripts/count-tests.sh` 为准
- 历史：自我改造任务持续闭环中——已完成任务见 `agate-workspace/tasks/active-tasks.md`，规划 / 债条目以 `roadmap.md`、`tech-debt.md` 为准

## 2. 仓库四块

| 区块 | 职责 | 权威入口 | 改动影响 |
|------|------|----------|----------|
| `<根>` | 项目开发资料：README（中英）/ CHANGELOG / docs / archived / 根 `AGENTS.md` | `AGENTS.md`（开发指引）| 主 checkout **禁止改动**；worktree 开发时它是协议本体 + hook 的 AGATE_ROOT |
| `agate/` | **协议本体**：阶段卡片 / 角色库 / 脚本 / 模板 / rules | `agate/AGENTS.md` → `agate/WORKFLOW.md` | 改它触发 SELF-GATE（见 `SELF-GATE.md`）；`~/.agate` 软链指向这里 |
| `agate-workspace/` | **任务数据**：tasks（含各任务 `.state.yaml`）/ roadmap / debt / reviews 等 9 个子目录 | `agate-workspace/tasks/active-tasks.md`、`agate-workspace/roadmap/roadmap.md` | roadmap 回写 `done` 是 P8 gate 硬校验（RM-AG0043） |
| `site/` | **产品 Web 层**：VitePress 站点（首页 + 博客 + 中文 i18n）| `site/guides/README.md` | 在协议 gate 治理之外；唯一硬校验 = `npm run build`；博客发布须过独立评审 |

## 3. 核心机制一页纸

### 3.1 阶段流 P0-P8 + P6.5

| 阶段 | 执行角色 | 关键门槛 | 是否可裁 |
|------|----------|----------|----------|
| P0 任务简报 | **主 Agent 亲自写** | P0-brief 四字段 + 同类/影响面预判 + 时效自检 | 不可裁 |
| P1 需求基线 | analyst | BDD 验收条件 + requirements-review 强制 + 无未决 NEED_CONFIRM | 不可裁 |
| P2 方案设计 | architect | P2-review approved + 四字段（packages/domains/ui_affected/gate_commands） | 不可裁（可简化） |
| P3 测试设计 | test-designer | TDD 红灯（`check-tdd-red.py` exit 0）| 默认保留，仅两种情形可跳 |
| P4 代码实现 | implementer | 暂存区含非 md/yaml 代码文件 | 不可裁 |
| P5 技术验证 | verifier | `gate_commands.P5` exit 0 且 failed==0 | 不可裁 |
| P6 验收 | verifier | BDD 逐条实跑 + `P6-evidence/` + provenance 客观审计 | 不可裁（可简化）|
| P6.5 独立 Judge | judge（**所有任务强制**）| fresh context 重验全部 BDD + 事件账本哈希链 | 强制 |
| P7 一致性 | consistency-reviewer | BLOCKER=0 + DESIGN_GAP 全配对 | 按需（多文件改动时必做；full 档 / 安全 / 多端改动不可裁）|
| P8 发布准备 | implementer | bump + CHANGELOG + tag + roadmap 回写 done | 涉及发布时必做 |
| READY → DONE | 人手动 `make publish` | READY 收尾检查清单 | — |

重试上限：P1/P2/P4 = 3，其余阶段 = 2（唯一权威表见 `agate/state-machine.md`「重试上限」节）。
裁剪决策 = 复杂度 × 风险矩阵，最终拍板权在主 Agent（详见 `agate/WORKFLOW.md`）。

### 3.2 Gate 分层（防"主 Agent 自觉"失效）

- **pre-commit hook**（本地，自动）：格式关（`check-state-yaml.py`）→ 行为关（`check-gate.py`
  按阶段 + PROD_TOUCHED 检测 + P8 `check-changelog.py`）→ 审计关（`check-p6-evidence.py`、
  `check-p6-provenance.py`、`check-state-transition.py`、`check-pruning.py`、`check-routing.py`、
  `check-scope-resolved.py`、`check-retrospective.py`）
- **CI backstop**（远程，防 `--no-verify` 绕过）：`ci-gate-backstop.py` 重跑 gate + provenance
- **两类 gate 信任度**：外部产出 gate（P3/P4/P5，test runner / git 产出，可信度高）vs
  self-authored gate（P1/P2/P6/P7，主 Agent 自写文件，靠证据存在性 + 审计缓解，P6.5 judge 强化）
- 完整清单见 `agate/WORKFLOW.md`「Pre-commit 检查总览」

### 3.3 状态与自我治理

- 状态三层落盘：每任务 `.state.yaml`（权威）+ `active-tasks.md` 看板 + `roadmap.md` 规划层；
  另有 append-only `gate-events.jsonl` 事件账本（P6.5 judge 轮次 / state_transition 哈希链）
- 每阶段门槛过 = 一个 `wf(Txxx-Pn):` commit；派发三铁律（只传路径 / 只回摘要 / task 工具派发）
- 状态推进机械化：`agate next` / `agate advance` 查 `phases.yaml` 表推进，不做临场判断（RM-AG0054）
- 跨 CLI/model 派发路由（可选，RM-AG0060）：`agate-workspace/dispatch-routing.yaml` 按 `(phase,role)`
  查表 → try-and-fall；未配置 = 逐字节现状
- 自我改造（dogfooding）走 worktree 隔离双工作区，见 `docs/guides/worktree-dogfooding-guide.md`
- 改协议本体走 SELF-GATE（`check-protocol-consistency.py` 0 ERROR + protocol-alignment-review 语义审查）

## 4. 权威源导航（想了解 X → 读 Y）

| 我想…… | 读 |
|--------|-----|
| 第一次接入 Agateon 到项目 | `agate/SETUP.md` |
| 理解 P0-P8 阶段流程与裁剪规则 | `agate/WORKFLOW.md` |
| 当前阶段具体怎么执行 | `agate/phase-cards/`（渐进披露，按阶段读卡片）|
| 查跨阶段规则 / 重试上限 / 评审映射 | `agate/rules/phases.yaml`（+ `dispatch.yaml` / `roles.yaml`）、`agate/state-machine.md` |
| 看协议本体架构全貌 | `agate-workspace/agents/CODE-MAP.md` |
| 查跨任务可复用知识 / 踩坑 | `docs/agents/knowledge-index.md` |
| 查决策记录（含被否决方案）| `docs/design-notes/README.md` |
| 查技术债 | `agate-workspace/debt/tech-debt.md`（`check-debt.py` 校验）|
| 看需求登记 / 任务看板 | `agate-workspace/roadmap/roadmap.md`、`agate-workspace/tasks/active-tasks.md` |
| 跑/写测试（maintainer）| `agate/tests/README.md` |
| 升级前查破坏性变更 | `agate/UPGRADING.md` |
| 了解结构性局限 | `agate/LIMITATIONS.md` |
| 发版（release）| 根 `AGENTS.md`「版本发布清单」+ `CHANGELOG.md` |
| 接站点 / 博客任务 | `site/guides/README.md`（必读 CONTRIBUTING + BLOG-STANDARDS）|
| 了解 CI docs-only 快路径机理 | `docs/guides/ci-docs-only-playbook.md` |
| 写 / 改仓库文档（选材与保鲜原则）| `docs/guides/doc-freshness-guide.md` |

## 5. 常见操作入口

| 操作 | 命令 / 入口 | 说明 |
|------|------------|------|
| 跑全量测试 | `python3 -m pytest agate/tests/ -n auto --reruns 1` | 对齐 CI 口径；Windows 冒烟用 `-m windows_smoke` |
| 查用例数 | `bash agate/tests/scripts/count-tests.sh` | 章节标题数字漂移时同步 |
| 协议一致性 | `python3 agate/scripts/check-protocol-consistency.py` | docs-only PR 用 `--strict-errors-only` |
| 结构一致性 | `python3 agate/scripts/check-structure-consistency.py` | rules/*.yaml ↔ md 双向（S-1~S-6）|
| ruff 静态检查 | `ruff check agate/` | CI 锁 `ruff==0.16.4`，与本地 `~/.venvs/agate-dev` 对齐 |
| 装 / 查协议版本 | `python3 ~/.agate/scripts/agate-install.py` / `agate-resolve.py` | `~/.agate` 版本管理根 |
| 装 git hooks | `python3 ~/.agate/scripts/install-hook.py` | 3 个 hook 薄壳指向 `resolve-entry.py` |
| 推进状态机一步 | `python3 ~/.agate/scripts/agate-next.py [TASK_DIR]` | 查表推进（消费 `phases.yaml`）；`agate-advance.py` 同族 |
| 站点构建 | `cd site && npm run build` | site 唯一硬校验 |
| 发博客 | 照 `site/guides/publish-checklist.md` 打勾 | 硬 gate = 独立评审 PASS |
| 代码 → PR | `/home/kity/bin/git-to-pr` | 非交互 shell 不读 bashrc，用绝对路径 |

## 6. 环境事实（本机）

- `~/.agate` → `/home/kity/oclab/agateon/agate`（legacy 单软链布局）
- 运行依赖：系统 `python3` + `pyyaml`（强制）+ `git`；Pillow 可选（P6 图像检测）
- 开发 Agateon 本体另需 `ruff`（锁 0.16.4）；测试另需 `pytest`（+ `pytest-xdist` / `pytest-rerunfailures`）
- 3 个 hook 薄壳（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh`）需 sh（Git for Windows 自带）
- `~/.dsh`：DSH 平台接入三件套（`.agent-presets/agate/preset.yml` / `agent.cordis.yml` / `skills/agate-protocol/SKILL.md`，软链指向 `agate/assets/templates/dsh/` 权威副本，`agate-summary.py` 可查漂移）

## 7. 维护约定

- **指针式不抄内容**：本文件不重复权威源正文，只指路；发现某处需要详细说明 → 写到对应权威源，这里留指针
- **跟随仓库演进**：新机制 / 新目录 / 新 CI job 落地后，同步更新第 2 / 4 / 5 节
- **数字一律写指针不写死**：用例数 / commit 数 / 条目数 / HEAD 日期等时变统计不写进正文，一律用命令（`count-tests.sh` / `git describe --tags`）或权威源指针替代——写死即漂移（2026-08-30 实证：数字 3 天内过期）。保留的只有稳定结构事实（脚本族 / 9 子目录）与本机环境事实。

## 8. 变更日志

- 2026-08-27：初始建立。整仓导航（四块布局 / 阶段流 / gate 分层 / 权威源 / 操作入口 / 环境事实）。
- 2026-08-28：独立评审修订（P7 可裁性表述按 `WORKFLOW.md` 风险矩阵修正、P6 provenance 措辞、版本日期拆分、补 knowledge-index 指针、变更日志编号、DSH 软链描述精确化）。
- 2026-08-30：§1 时变数字（HEAD 日期 / commit 数 / 条目数）改为**指针式**（命令 / 权威源），不再写死——防漂移改造。
