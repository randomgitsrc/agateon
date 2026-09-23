# {Txxx} 交接单 — {任务一句话}

> 本交接单供 worktree session 的 agent 按此启动 {Txxx} 任务。
> 任务已 P0 立项（.state.yaml phase=P0，P0-brief.md 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**{Txxx}**：{任务标题}。

**一句话**：{任务一句话描述}。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `{worktree 路径}` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `{主 checkout 路径}`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → 主 checkout/agate；TAG0008 起也可为版本管理目录，稳定版概念不变） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是 worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。这是有意的：改造期间工具稳定，改造对象变化。
- **⚠️ gate 工具 ≠ 检查对象（最容易搞混的点）**：
  - commit hook 的 gate **判定工具**用 `~/.agate`（稳定版）——它读 `~/.agate` 自己的脚本逻辑
  - 但 `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`），因为检查对象是 **worktree 里的协议文件**。若误用 `~/.agate` 的 consistency 脚本，会扫到主 checkout 的文件而非 worktree 的改动
  - 同理：`python3 ~/.agate/scripts/agate-summary.py` 在 worktree 里跑会显示**主 checkout 的上下文**（版本/分支/HEAD 是稳定版的），不代表 worktree 状态——worktree 自己的状态用 `git log`/`git status` 看
  - 同理：**所有编排/派发类工具脚本**（`agate-inject-card.py`、`agate-render-dispatch-prompt.py`、`agate-next-card.py` 等）都用 `~/.agate/scripts/` 稳定版调用（TAG0016 教训：用 worktree 相对路径调用 `agate-inject-card.py` 时，其 AGATE_ROOT 自解析逻辑会读到 worktree 正在被修改的协议卡片副本，把尚未发布的新机制内容注入任务——P5 才发现并改正，P1-P4 纯属侥幸未实际受损）
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 实际在主 checkout 的 `.git/hooks/`（pre-commit/commit-msg/pre-push 已软链安装）。worktree commit 时 hook 自动触发。**权威取值**：`git rev-parse --git-path hooks`（`core.hooksPath` 覆盖时也会跟着变）；新 worktree **无需重装** hook。

**已完成的 setup（worktree 已可独立使用）**：
- 依赖齐全：bash / python / pyyaml / pytest / shellcheck
- 基线验证：全量 pytest 全绿 + consistency 0 ERROR（--strict-errors-only；DEBT0012 教训：存量 300+ WARNING 下 --strict 会误导判 exit 2）
- commit hook：指向 `~/.agate`（稳定版），worktree commit 自动触发
- 平台接入：`python3 ~/.agate/scripts/agate-setup.py`（**默认全局**，一次覆盖本机所有项目/所有 worktree；内部按 `~/.agate/current/agate`（= `$AGATE_DIR`）解析协议根，幂等、可 `--list` 核验）。只有刻意钉版本时才用 `--scope project`（产物落 git 根，且会把路径登记进安装台账）
- 卸载（收尾时按需）：`agate-setup.py --list` → `--uninstall --all-projects`。**注意 hook 是仓库级共享的**——在任一 worktree 里卸载会一并清掉主 checkout 的 gate，多任务并行时别顺手卸
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`
- 任务数据：{Txxx} P0-brief + .state.yaml phase=P0 在 worktree 的 `agate-workspace/tasks/`

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 已核实并确认的缺陷/需求（全部有代码证据，见 P0-brief known_risks）

**{来源分类}**：
- **{编号}（{严重度}）** {文件}:{行号}：{问题描述} → {影响}
- ...

### 核心约束（不可违反）
1. **Linux 现状是基线**——现有 {N} pytest 测试全绿是回归底线，每个修复都必须保持全绿
2. **Windows 兼容是增量**——本环境（Linux）无法实测 Windows，靠静态修复 + Linux 回归 + CI matrix 兜底。**不要宣称"已实测 Windows"**（若任务涉及跨平台）
3. **不破坏已有协议语义**——{本任务改动的性质边界}
4. **范围锁定**——若 P1 分析发现需改动超出 P0-brief 锁定范围，须先停下跟用户确认

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（必须全绿才算过）
python3 -m pytest agate/tests/

# 一致性（0 ERROR 才行；--strict-errors-only 仅在 ERROR 时 exit 非 0，对齐 DEBT0012/TAG0017 语义）
# ⚠️ 必须用 worktree 自己的脚本（检查对象是 worktree 里的协议文件），不要用 ~/.agate 的
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck
shellcheck -S warning agate/scripts/*.sh

# 测试计数（验证文档没漂移）
bash agate/tests/scripts/count-tests.sh

# 单脚本测试（改哪个跑哪个，TDD 先红后绿）
python3 -m pytest agate/tests/unit/test_{具体测试文件}.py
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出（pre-commit 会用 P2 gate 检查，P2-design.md 不存在 → 拦截）
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿（AGENTS.md「改脚本的工作流」）
- **批量机械改动的 TDD 策略**：这类改动每个都写单独测试边际成本高。建议——①先写一个"grep 断言审计"测试作为回归拦截；②批量改动后跑该断言 + 全量 pytest 确认绿。不要为每个小改动单独写测试，也不要跳过测试直接改
- **git 命令加 timeout**、单步串行（AGENTS.md 工具纪律）
- **commit message 含 `wf({Txxx}-P{阶段}):`** 前缀
- **改 `agate/*.md`、`agate/scripts/*.py/.sh`、`agate/phase-cards/*` 触发 SELF-GATE**：commit message 需含 `self-gate-review:` 或 `self-gate-skip:`（否则 commit-msg hook WARNING）。协议文档变更需跑 `check-protocol-consistency.py` 确认无 ERROR

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/{Txxx}-{slug}/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）
- active-tasks.md「待开始」已有 {Txxx} 行
- roadmap：{关联条目} 关联本任务（scheduled）
- **编号体系**：任务用 `{Txxx}`（项目代号 + 动态数字的 Jira 式编号）。校验器 `^T[A-Z]{2}\d+$`

## 7. 已知风险与止损

- {风险 1}：{描述} → {止损}
- ...

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（PR 普通 merge 非 squash，tag 要求）
- **合并前在 PR 里看 CI 结果**（跨平台任务看 matrix 双平台）——pytest/shellcheck/consistency/gate-backstop 全绿才算过
- roadmap 回写关联条目 → done
- 复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新 roadmap/版本）

## 9. 交接确认

- worktree 基线全绿：{N} pytest + consistency 0 ERROR（--strict）
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册、依赖齐全
- 任务数据就绪：{Txxx} P0-brief + .state.yaml phase=P0
- 交接单位置：`HANDOFF-{Txxx}.md`（worktree 根，已 commit）

---

> 模板字段：任务编号、任务标题/一句话、worktree/主 checkout 路径、缺陷清单（文件:行号:问题）、核心约束、验证命令、阶段纪律、风险、完成后动作。复制到 worktree 根目录 `HANDOFF-{Txxx}.md` 填写。
