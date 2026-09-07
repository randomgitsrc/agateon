# TAG0032 交接单 — 版本管理生命周期可用性批（RM-AG0058 整合 epic）

> 本交接单供 worktree session 的 agent 按此启动 TAG0032 任务。
> 任务已 P0 立项（.state.yaml phase=P0，P0-brief.md 已就绪）。
> worktree 已完成构建与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0032**：版本管理生命周期可用性批。

**一句话**：修复版本管理（TAG0008 v1）"全新机器 → 版本布局 → 项目钉版 → 更新"全链路的三个断点——①入口断链（软链穿透污染源仓库 / 根 scripts 缺失）②元仓库 gap（resolve 返回仓库根而 gate 在 vdir/agate/scripts）③update 统一入口缺失。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0032` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agateon`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → 主 checkout/agate） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是 worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。
- **⚠️ gate 工具 ≠ 检查对象**：`check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`）；编排/派发类工具用 `~/.agate/scripts/` 稳定版（TAG0016 教训）。
- **hook 在共享 git 目录**：worktree commit 时 hook 自动触发（指向主 checkout `.git/hooks/`）。
- **⚠️ 本任务特有**：凡涉及安装路径的验证（agate-install / resolve 端到端）**一律用隔离 HOME**（`HOME=$(mktemp -d)` 级别，测完删除）——**绝不**在真实 `~/.agate`（legacy 软链）上做安装实验，本任务的实验对象恰是"安装会污染软链目标"这类破坏性行为。

**已完成的 setup**：
- 依赖齐全（bash/python3/pyyaml/pytest/shellcheck/ruff）
- 基线验证：consistency 0 ERROR（--strict-errors-only，worktree 内执行）
- orchestrator 注册：`.claude/agents/orchestrator.md` 软链 → 主 checkout `agate/orchestrator-template.md`（稳定版）
- 工作区解析：`agate_common.py` 输出 worktree 自己的 agate-workspace（须在 worktree 目录内执行）
- 任务数据：TAG0032 P0-brief + .state.yaml phase=P0（随立项 commit 已在分支基座上）

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 已核实并确认的缺陷（全部有实测/代码证据，见 P0-brief + RM-AG0058）

**① 入口断链（2026-09-07 隔离 HOME 实测）**：
- legacy 软链布局下按官方指引（README/UPGRADING）跑 `python3 ~/.agate/scripts/agate-install.py` → `os.makedirs(~/.agate, exist_ok=True)` 穿透软链 → `repo/` 主克隆与 `vX.Y.Z` worktree **静默建进源仓库 agate/ 目录内部**（实测 repo 实体 = `src/agate/repo`）
- 先删软链再装（正确姿势）→ `~/.agate/scripts` 不存在（install 不建根 scripts，工具只在 `repo/agate/scripts/`）→ README 入口命令 No such file
- **两条进入版本布局的路径均死路**

**② 元仓库 gap（RM-AG0058 本体，2026-09-03 实机验证）**：
- GitHub 装出的 `vX.Y.Z` = agateon 整仓（协议在 `agate/` 子目录），resolve 命中版本返回 vdir（仓库根），gate 消费找 `vdir/scripts/pre-commit-gate.py` 不存在（实际 `vdir/agate/scripts/`）→ 钉 `.agate-version` 后 commit 被阻断
- 根因：TAG0008 测试用"根即协议"模拟 repo，从未覆盖元仓库形态

**③ update 入口缺失**：legacy 升级 = 手动 git pull（无指引）；版本布局升级 = agate-install latest（入口断）；hook 重装时机散落 UPGRADING 各版本节

### 核心约束（不可违反）

1. **行为纯增量**——"根即协议"部署方（版本目录直接含 scripts/）必须继续可用：探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后，不得破坏既有解析语义
2. **Linux 现状是基线**——现有全量 pytest 全绿是回归底线
3. **install 软链拒绝须给迁移指引**——拒绝信息含可操作路径（备份软链 → 建目录根 → 装版本），否则自断现网用户升级路
4. **端到端验收用真实 GitHub 元仓库形态**（隔离 HOME），不能用根即协议模拟 repo 代替（TAG0008 教训）；CI 无网则 skip + 本地验收记录补证
5. **TDD**：先写失败测试确认红 → 改脚本转绿；`check-debt`/`check-gate` 等消费方语义改动前先 grep 全部消费方（DEBT0016 教训）
6. **范围锁定**——若 P1 分析发现需改动超出 P0-brief 锁定范围，须先停下跟用户确认

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（必须全绿才算过；分片 + -n auto 并行提速）
python3 -m pytest agate/tests/unit/ -n auto
python3 -m pytest agate/tests/regression/ -n auto
python3 -m pytest agate/tests/integration/ -n auto

# 一致性（0 ERROR 才行；必须用 worktree 自己的脚本）
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck
shellcheck -S warning agate/scripts/*.sh

# 测试计数（验证文档没漂移）
bash agate/tests/scripts/count-tests.sh

# 端到端（本任务新增，全部用隔离 HOME——见 §2 特有纪律）
HOME=$(mktemp -d) python3 agate/scripts/agate-install.py v最新tag   # 装
HOME=<同上> python3 agate/scripts/agate-resolve.py                 # resolve
# 钉版场景：在临时项目目录写 .agate-version 后跑 hook resolve 链，验 gate 路径存在
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿（AGENTS.md「改脚本的工作流」）
- **git 命令加 timeout**、单步串行不并行 bash（AGENTS.md 工具纪律）
- **commit message 含 `wf(TAG0032-P{阶段}):`** 前缀
- **改 `agate/scripts/*` + 文档面触发 SELF-GATE**：本任务改 agate-install.py / agate_common.py / resolve-entry.py + README/UPGRADING/SETUP/install.sh → commit message 需含 `self-gate-review:` 或 `self-gate-skip:`；协议文档变更需跑 `check-protocol-consistency.py` 确认无 ERROR

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0032-version-lifecycle/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）
- active-tasks.md「待开始」已有 TAG0032 行（⬜ P0）
- roadmap：RM-AG0058 关联本任务（scheduled，2026-09-07 扩写整合为 epic）
- **编号体系**：任务用 `TAG0032`。校验器 `^T[A-Z]{2}\d+$`
- **并行情况**：单 task 串行，无并行兄弟任务；但主 checkout 可能有其他会话在推进（本 session 期间远端 main 曾前进）——开工前先 `git fetch` 对齐，共享面（roadmap/active-tasks）只改自己关联的行

## 7. 已知风险与止损

- **resolve 语义变更影响消费面**（hook/summary/next 全走 agate_common 归口）→ 止损：先 grep 全部消费方确认无直接拼 vdir/scripts 旁路；探测顺序保证纯增量；全量 pytest + 新用例锁定两种形态
- **install 软链拒绝是新行为变更** → 止损：拒绝信息带迁移指引；隔离 HOME 实测拒绝路径与迁移路径；单测锁定
- **根 scripts/ 建立方式二选一**（副本 vs 软链，维护语义不同）→ 止损：P2-design 决策 + UPGRADING 写明 + 单测锁定所选语义
- **端到端依赖网络 clone GitHub** → 止损：CI 无网标记 skip + 本地验收记录补证进 P6-evidence

## 8. 完成后

- P8 gate + READY → 提 PR（PR 普通 merge 非 squash）；PR 提出后主 Agent review 复核，**CI 全绿后 worktree 自行 git-to-main**
- **合并前在 PR 里看 CI 结果**——pytest/shellcheck/consistency/gate-backstop 全绿才算过
- **merge 模式：worktree 自行 git-to-main**
- roadmap 回写 RM-AG0058 → done；复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新版本）
- 注意：本分支首个 PR 同时携带立项 commit（workspace 注册面）——PR 描述里说明

## 9. 交接确认

- worktree 基线：consistency 0 ERROR（--strict-errors-only）已验
- hooks 就位（共享 git 目录 → `~/.agate` 稳定版）、orchestrator 已注册（.claude/agents）、依赖齐全
- 任务数据就绪：TAG0032 P0-brief + .state.yaml phase=P0
- 交接单位置：`HANDOFF-TAG0032.md`（worktree 根，已 commit）
