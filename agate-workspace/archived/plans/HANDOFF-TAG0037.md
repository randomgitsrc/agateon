# TAG0037 交接单 — 安装与多版本模型统一（RM-AG0066）

> 本交接单供 worktree session 的 agent 按此启动 TAG0037 任务。
> 任务已 P0 立项（`.state.yaml` phase=P0，`P0-brief.md` 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。
> 本交接单按 `docs/guides/worktree-dogfooding-guide.md` 的 10 步流程构建（2026-09-19）。

---

## 1. 你要做什么

**TAG0037**：安装与多版本模型统一。

**一句话**：定义「**版本目录的唯一结构契约**」，引入 GitHub Release 与本体安装包（portable），统一在线/离线/legacy 三条安装路径，并修复离线安装的解析失效缺陷（P0 真 BUG）。

**为什么是协议级设计变更**：多版本机制已经历 **4 轮 task**（TAG0008 版本管理 v1 / TAG0017 工具链修复 / TAG0031 DEBT 清理 / TAG0032 版本生命周期），用户反馈「问题还是不少」。审计确认根因：**四条安装路径、三套目录结构约定，从未定义「版本目录里该有什么」这一根本契约**——四轮都在修补局部。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0037` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agateon`（开发 checkout） | 开发 checkout | **不要在它上面改**（本任务改动全在 worktree） |
| `~/.agate`（**版本管理根目录，非软链**） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- **⚠️ gate 工具 ≠ 检查对象**：
  - commit hook 的 gate **判定工具**用 `~/.agate` 稳定版
  - 但 `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`）——检查对象是 worktree 里的协议文件
  - **编排/派发类工具一律用 `~/.agate/scripts/` 稳定版**（`agate-inject-card.py` / `agate-render-dispatch-prompt.py` / `agate-next-card.py`）——worktree 相对路径调用会读到正在被修改的协议卡片（TAG0016 教训）
  - `~/.agate` 脚本显示**稳定版上下文**（`agate-summary.py` → `AGATE_ROOT=~/.agate/vX.Y.Z/agate` + 版本号），**不是** worktree 状态
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向开发 checkout 的 `.git`），hook 实际在 `/home/kity/oclab/agateon/.git/hooks/`（三个 hook 已软链到 `~/.agate/scripts/`）

**已完成的 setup（2026-09-19 按 guide）**：
- 依赖齐全：bash 5.2.21 / python 3.12.3 / pytest 9.0.3 / pyyaml / shellcheck 0.9.0 / ruff 0.16.4
- **基线验证**：CI 口径（`--reruns 1 -n auto`）**1842 passed / 2 skipped**
- commit hook：三个 hook → `~/.agate/scripts/`（稳定版）
- orchestrator 注册：`.opencode/agents/orchestrator.md` + `.claude/agents/orchestrator.md` → **`$AGATE_DIR/orchestrator-template.md`**（`AGATE_DIR` = 协议根，按 guide「先取协议根路径」节解析；双平台软链，**已验证可读**）
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`
- 任务数据：TAG0037 P0-brief（**129 行**）+ `.state.yaml` phase=P0
- **基线 HEAD**：`59ec70d`

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

> **完整 scope 见 `P0-brief.md`**（129 行，含 4 子批 + 9 条完成判据 + out-of-scope + 6 条 known_risks + 实测证据）。

### 子批 A：定义并落地「版本目录结构契约」（**核心**）

**问题**：当前三条路径产出**三种结构**，互不兼容——

| 路径 | 产出结构 | 状态 |
|------|---------|------|
| `install.sh`（legacy 无参） | `~/.agate` 软链 → `<repo>/agate`（**本体**） | ✅ 正确 |
| `install.sh --versions` / `agate-install.py` | `vX.Y.Z/{agate, agate-workspace, docs, site, archived, HANDOFF-*.md, ...}` | ⚠️ 冗余 91% |
| `agate-pack-offline.py` → `install-offline.py` | `vX.Y.Z/agate/{agate, README.md, ...}`（**本体在两层下**） | ❌ **解析失效** |

**实测数据**：`~/.agate/v0.71.1/` = **43M**，其中本体 `agate/` = **4.1M** → 冗余 ≈39M（**91%**）；另 `repo/` = **59M**；tag v0.71.1 含 **3290 文件**，`agate/` 占 **367（11%）**；**GitHub Release = 0 个**。

**契约提案（P2 定案）**：`~/.agate/vX.Y.Z/` 下**只含本体**（`agate/`）。
- **legacy 形态天然符合**（软链直指本体）→ 在线/离线**对齐到它**
- 已装用户的 `vX.Y.Z/{...}`（当前在线形态）**须保持可解析**（兼容红线）
- **⚠ 目录名固定 `agate/`**（2026-09-19 修正）：原拟"可扩展/由 manifest 声明"**已删除**——与 `docs/design-notes/design-rename-execution.md` §8.1「`agate/` 目录名**永久保留**，不议 `core/`」冲突。该文档 §1 已论证 `agate/` 是**协议基础设施**（`~/.agate` 软链目标 / hook 的 `AGATE_ROOT` / `agate-*.py` 自定位根）。**本任务只需保证 `_protocol_root` 既有两形态探测（`vdir/scripts` / `vdir/agate/scripts`）不被破坏**（探测序为红线，只可增量扩展）。

### 子批 B：修复 P0 —— 离线安装解析失效（**真 BUG**）

**机理（实测确认）**：

```
pack 侧   : git worktree add <bundle>/agate <tag>   → bundle/agate/ 是【整仓根】
install 侧: _copy_tree(bundle → vX.Y.Z/)            → vX.Y.Z/agate/agate/scripts/

_protocol_root 探测: vX.Y.Z/scripts ✗、vX.Y.Z/agate/scripts ✗（真实在 .../agate/agate/scripts）
→ 返回 vX.Y.Z 原样 → 【解析链失效】
```

**测试为何没抓到（根因）**：`test_install_offline.py::_make_bundle` 构造 `bundle/agate/WORKFLOW.md`——**假设 `bundle/agate/` 就是本体**，并断言 `version_dir/agate/WORKFLOW.md` 存在，**与实现同源错误**。真实 packer 用 `worktree add` 检出整仓树，布局被测试假设掩盖。

**修法**：与子批 A 的结构契约统一——pack/install 两侧按同一约定产出/解读。**并修正 `_make_bundle` 使之反映真实布局**（否则测试继续掩盖）。

### 子批 C：引入 GitHub Release + 本体安装包（用户决策 ①）

```
GitHub Release vX.Y.Z（tag push 时自动创建）
├── Release notes ← 自动提取 CHANGELOG 该版本段
└── Assets
    ├── agateon-vX.Y.Z.tar.gz                    ← 本体（portable，解压即用，无需 git）
    └── agateon-vX.Y.Z-offline-<platform>.tar.gz ← 本体 + wheels
```

- **portable 语义**：解压到 `~/.agate/vX.Y.Z/` → 建 `current` 指针即可用（**不依赖 git**）
- **⚠ 新增 `.github/workflows/` workflow 属 CI 配置改动 → 须用户明确许可**（`AGENTS.md` 规则 5）；**P1 须先确认许可范围**
- ⚠ **portable 的"无需 git" ≠ 零依赖**——仍依赖系统 `python3` + `pyyaml`。文档勿宣称"零依赖"。

### 子批 D：在线安装「只装本体」+ 保留历史 tag 能力（用户决策 ②）

- **只装本体**：消除 91% 冗余；**不再把 agateon 自身任务数据**（`agate-workspace/tasks/TAG0001-...`）与**维护者产物**（`HANDOFF-*.md`、`docs/reviews/`、`site/`）装入用户环境（现会造成语义混淆）
- **保留**「装任意历史 tag」：`repo/`（59M）**保留**，`git worktree add` 路径仍可用
- 排除清单**来源与维护方式**须 P2 定（候选：`.gitattributes export-ignore` / 显式清单 / `git archive` 语义）

### 核心约束（不可违反）

1. **Linux 现状是基线**——全量 pytest 全绿是回归底线
2. **不改 `_protocol_root` 既有探测序语义**（`vdir/scripts` 优先——标注「不可颠倒」红线）；仅**扩展**
3. **兼容性是最大风险**——已装用户的 `vX.Y.Z/{agate,docs,...}` 结构**必须仍可解析**
4. **范围锁定**——若 P1 发现需超出 P0-brief 范围，**须先停下跟用户确认**

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试 —— 用【CI 完整口径】（含 flaky 兜底的 --reruns；权威源见 agate/tests/README.md）
python3 -m pytest agate/tests/ --reruns 1 -n auto

# 分片跑（调试时）
timeout 280 python3 -m pytest agate/tests/unit/ -q -n auto
timeout 280 python3 -m pytest agate/tests/regression/ -q -n auto
timeout 280 python3 -m pytest agate/tests/integration/ -q

# 一致性（0 ERROR 才行；必须用 worktree 自己的脚本）
timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# ruff（CI 锁 0.16.4）
~/.venvs/agate-dev/bin/ruff check agate/

# shellcheck（本任务改 install.sh）
timeout 60 shellcheck -S warning install.sh agate/scripts/*.sh

# 测试计数
timeout 60 bash agate/tests/scripts/count-tests.sh

# 安装机制验证（在【隔离 AGATE_HOME】下做，勿动真实 ~/.agate）
AGATE_HOME=/tmp/xxx python3 agate/scripts/agate-install.py --check
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；**不要**先写 phase=P2 再 commit P1 产出（pre-commit 会用 P2 gate 检查，P2-design.md 不存在 → 拦截）
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿
- **批量机械改动的 TDD 策略**：先写一个"grep 断言审计"测试作为回归拦截；批量改动后跑该断言 + 全量 pytest
- **git 命令加 timeout**、单步串行
- **commit message 含 `wf(TAG0037-P{阶段}):` 前缀**
- **⚠ SELF-GATE 触发面**：`agate/scripts/agate-install.py` / `install-offline.py` / `agate-pack-offline.py` / `install.sh` / 可能新增 `.github/workflows/` ——**全部命中**（`agate/scripts/*.py` / `agate/**/*.md`）→ commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；且须跑 consistency 0 ERROR
  - 触发面权威源 = `commit-msg-self-gate.py` 的 `_SELF_GATE_RE` 正则（判断命令见 `SELF-GATE.md`「触发条件」节）
- **验证前先对齐 CI 口径**（`--reruns 1`）——否则可能把已知 flaky 当新缺陷追（本机需装 `pytest-rerunfailures`）
- **PR 流程用现成脚本**：`/home/kity/bin/git-to-pr`（commit→branch→push→PR）/ `/home/kity/bin/git-to-main <PR#>`（等 CI→合并→同步→清理）——**勿手工做**，手工易误提交到 main

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0037-install-package-model/`（worktree 内）
- `.state.yaml`：phase=P0（P1 开始后推进）
- `active-tasks.md`「待开始」已有 TAG0037 行
- roadmap：**RM-AG0066**（`scheduled`）关联本任务
- **编号体系**：`TAG0037`（校验器 `^T[A-Z]{2}\d+$`）

## 7. 已知风险与止损

> 完整 6 条见 `P0-brief.md` §known_risks。以下为要点。

| 风险 | 止损 |
|------|------|
| **兼容性（最大）** | 已有用户装了当前形态（`vX.Y.Z/{agate, agate-workspace, docs, ...}`）。**结构契约若收紧，必须保证旧形态仍可解析**——`_protocol_root` 探测序是红线，只可增量扩展。P1 须先勘察「本机之外还有多少种已装形态」 |
| **CI 改动的许可边界** | 子批 C 要新增 release workflow → **P1 必须先确认**：是"允许新增 workflow 文件"，还是"连触发条件/权限也要逐项确认" |
| **排除机制三选一勿默认** | `git archive` / `export-ignore` / 显式清单**语义不同**（`export-ignore` 会影响所有 archive 消费者）。P2 须比对，**勿默认选一个** |
| **tag 与 Release 双轨一致性** | tag 是全量源码、asset 是本体——**内容不同但必须对应同一版本**。须防"打了 tag 忘了发 Release" |
| **portable 非零依赖** | 仍依赖系统 `python3` + `pyyaml`（`--check` 会探测）。**文档勿宣称"零依赖"** |
| **tests/ 是否入包** | 本体 4.1M 中含相当部分 `tests/`——排除后用户侧 `check-protocol-consistency.py` 等可能受限。P2 定 |

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**PR 普通 merge 非 squash**，tag 要求）
- **合并前看 CI 结果**——pytest / shellcheck / consistency / gate-backstop 全绿才算过
- roadmap **RM-AG0066** 回写 → `done`（P8 gate 硬校验 RM-AG0043）
- **HANDOFF 归档**（**最常被漏的一步**——TAG0028/TAG0035/TAG0036 连续三次漏）：
  ```bash
  git mv HANDOFF-TAG0037.md agate-workspace/archived/plans/HANDOFF-TAG0037.md
  ```
  **建议在 P8 收尾的同一个 PR 里做掉**；收尾自检两条：仓库根 `ls HANDOFF-*.md` 应为空 + `archived/plans/` 应存在
- 复盘按 agate 自身变更流程归档

## 9. 交接确认

- worktree 基线全绿：CI 口径 **1842 passed / 2 skipped**
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册（**双平台软链已验证可读**）、依赖齐全
- 任务数据就绪：TAG0037 P0-brief（**129 行**）+ `.state.yaml` phase=P0
- **基线 HEAD**：`59ec70d`
- 交接单位置：`HANDOFF-TAG0037.md`（worktree 根，已 commit）
- **构建方式**：2026-09-19 按 `docs/guides/worktree-dogfooding-guide.md` 10 步流程

---

> **启动入口提醒**：orchestrator 默认读 `{AGATE_WORKSPACE}/tasks/active-tasks.md` + `.state.yaml`，**不会自动读 HANDOFF**。新 session 首条指令请显式写「**读 worktree 根 `HANDOFF-TAG0037.md`**」。
