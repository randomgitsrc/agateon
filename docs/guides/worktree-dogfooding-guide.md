# 构建 worktree session + setup + 交接单（dogfooding 标准流程）

> 适用：agate 自身改造任务（dogfooding）需要隔离 worktree 时。
> 每次新任务（TAG0005+）按此流程快速构建，避免临时发挥。
> 配套：交接单模板 `agate/assets/templates/handoff-template.md`。

---

## 为什么需要这套流程

agate 自身改造 = 用 agate 改造 agate（dogfooding）。涉及双工作区（稳定版 `~/.agate` vs 改造对象 worktree）、共享 hook、基线验证、交接单。步骤多且易错（T001/TAG0004 两次都踩过），固化后可 10 分钟内完成。

## 前置条件

- 开发 checkout（本仓库）在 main 且干净
- `~/.agate` 是**版本管理根目录**（非软链）——稳定版来自 `~/.agate/current/`，与开发 checkout **解耦**（见 §「本机稳定版布局」；2026-09-18 前为 legacy 软链布局）
- 任务已 P0 立项（P0-brief + .state.yaml 在 agate-workspace/tasks/）

## 流程（10 步）

### Step 0：检测现有隔离（using-git-worktrees skill）

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
[ "$GIT_DIR" = "$GIT_COMMON" ] && echo "普通 checkout" || echo "已在 worktree"
```

主 checkout 是普通 checkout（GIT_DIR=GIT_COMMON），`.worktrees/` 已 gitignore（T001 时期验证过）。

### Step 1：创建 worktree

```bash
git worktree add .worktrees/agate-{Txxx} -b feat/{Txxx}-{slug}
```

- 分支名：`feat/TAG0004-env-adaptation` 风格
- 位置：`.worktrees/agate-{Txxx}`（仓库根下，已 gitignore）

### Step 2：依赖检查（worktree 内）

```bash
bash --version && python3 --version && python3 -m pytest --version && \
python3 -c "import yaml; print('pyyaml OK')" && command -v shellcheck && command -v ruff
```

缺什么补什么（bash/python/pyyaml/pytest/shellcheck/ruff）。

**⚠️ 解释器注意**：请用**系统 python（`/usr/bin/python3`）**跑 pytest/pyyaml——pytest 以模块形式装在系统 python，**裸 `pytest` 命令在 PATH 里通常找不到**（会误报"缺 pytest"）。`~/.venvs/agate-dev` 是开发 agate 本体的 venv，只装了 python + ruff、**没装 pytest**，不要 source 它跑测试。CI 用 `python3 -m pytest`（`protocol-tests.yml`），本机也应统一 `python3 -m pytest`。ruff 用 `~/.venvs/agate-dev/bin/ruff`（开发 agate 才需要，仅跑测试用不到，但本任务要改脚本所以需检查）。

### Step 3：基线验证（Step 4 of skill——确保干净起点）

```bash
cd .worktrees/agate-{Txxx}
python3 -m pytest agate/tests/
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only
```

全绿 + 0 ERROR 才算干净基线。失败则停下来（可能主 checkout 有未合并改动）。

> ⚠️ **用 `--strict-errors-only` 而非 `--strict`（DEBT0012 教训）**：仓库存量有 300+ 条历史叙事文件死链 WARNING，`--strict` 会让"仅有 WARNING、无 ERROR"也 exit 2，把干净基线误判为"主 checkout 有未合并改动"。`--strict-errors-only` 仅在 ERROR 时非 0（TAG0017 起官方默认语义，见 `agate/scripts/README.md`）。pytest 全量大可分 unit/regression/integration 三片跑（`tests/README.md`），每片外层加 `timeout 90`、片内加 `-n auto` 并行（约 3.5x 提速；套件按隔离设计，可安全并行），gate/consistency 单跑并加 timeout。

### Step 4：确认 hook 就位（共享 git 目录）

worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 在共享目录：

```bash
ls -la /home/kity/oclab/agate/.git/hooks/ | grep -E 'pre-commit|commit-msg|pre-push' | grep -v sample
```

预期：三个 hook 软链指向 `~/.agate/scripts/`。这是有意的——commit hook 用稳定版判定，避免"用未验证的新 gate 判自己"。

### Step 5：注册 orchestrator（SETUP）

```bash
# 先取协议根（版本管理布局在 ~/.agate/current/agate；单软链布局就是 ~/.agate 本身）
AGATE_DIR="$([ -d "$HOME/.agate/current" ] && echo "$HOME/.agate/current/agate" || echo "$HOME/.agate")"

# OpenCode + Claude Code 双平台都注册（TAG0016/17 实际都双平台）
mkdir -p .opencode/agents
ln -sf "$AGATE_DIR/orchestrator-template.md" .opencode/agents/orchestrator.md
mkdir -p .claude/agents
ln -sf "$AGATE_DIR/orchestrator-template.md" .claude/agents/orchestrator.md

# 自检：链后必须可读（写错协议根会得到断链，症状是编排者身份不可用）
test -r .claude/agents/orchestrator.md && echo "✅ 可读" || echo "❌ 断链——检查 $AGATE_DIR"
```

> **为什么不能直接写 `~/.agate/orchestrator-template.md`**：该路径只在**单软链布局**下成立；**版本管理布局**下协议本体在 `~/.agate/vX.Y.Z/agate/`，直接写会得到断链（平台报 `--agent 'orchestrator' not found`）。细节见 `SETUP.md`「先取协议根路径」。

`.opencode/` 与 `.claude/` 均已 gitignore（本地环境配置不入库），对应 setup 步骤见 `SETUP.md`（OpenCode 与 Claude Code 各一节）。

### Step 6：验证工作区解析

```bash
python3 agate/scripts/agate_common.py
# 预期输出 AGATE_WORKSPACE=/AGATE_TASKS_DIR= 指向 worktree 自己的 agate-workspace/（不是主 checkout 的）
```

### Step 7：确认任务数据就位

```bash
ls agate-workspace/tasks/{Txxx}-{slug}/
grep -E 'task_id|phase' agate-workspace/tasks/{Txxx}-{slug}/.state.yaml
```

预期：P0-brief.md + .state.yaml phase=P0。

### Step 8：写交接单

复制 `agate/assets/templates/handoff-template.md` → worktree 根 `HANDOFF-{Txxx}.md`，**按模板全部 9 个小节填写**（不要只填部分字段）：
- §1 你要做什么（任务编号/标题/一句话，从 P0-brief 取）
- §2 工作区布局（worktree/主 checkout/`~/.agate` 双工作区表 + 核心原则）
- §3 任务范围（缺陷/需求清单从 P0-brief known_risks + 审计/复盘取 + 核心约束）
- §4 关键验证命令（模板已有，改测试文件名 + 解释器）
- §5 阶段推进纪律（commit phase、TDD、SELF-GATE 触发、`wf({Txxx}-P{N})` 前缀——T001 血泪教训级硬约束，**必填**）
- §6 任务编号与状态
- §7 已知风险与止损
- §8 完成后（PR 普通 merge 非 squash、CI 检查、roadmap 回写）
- §9 交接确认

> ⚠️ §5 的 commit-phase 纪律与 §8 的 PR merge 规则都是硬约束，只填到 §3 会让后续 agent 漏掉关键纪律。

### Step 9：交接单 commit

```bash
git add HANDOFF-{Txxx}.md && git commit -m "docs: {Txxx} 交接单"
```

### Step 10：最终确认 + 切换

```bash
git worktree list   # 确认 worktree 就位
git log --oneline -3   # 确认交接单已提交
```

然后切到 worktree 目录，新开 session。

**⚠️ 启动入口（HANDOFF 读取盲点）**：orchestrator 的默认启动流程读的是 `{AGATE_WORKSPACE}/tasks/active-tasks.md` + `.state.yaml`（orchestrator-template.md），**并不会自动读 HANDOFF**。所以必须在新 session 的首条指令里显式写"**读 worktree 根 `HANDOFF-{Txxx}.md`**"（认准当前任务号——已完成任务的 HANDOFF 应已归档到 `agate-workspace/archived/plans/`，仓库根通常不残留历史交接单；且本任务分支未合并前，其 HANDOFF 只存在于本 worktree、不在 main）。若 agent 没读 HANDOFF，它仍能按默认流程从 active-tasks.md + P0-brief 启动（handoff 是"快捷入口"而非"必需"），但缺陷清单/核心约束/阶段纪律会缺失。

## 关键纪律（违反必出事故）

| 纪律 | 说明 |
|------|------|
| 开发 checkout 的 `agate/` 不改 | 正常改动走 worktree。**注意**：迁移到版本管理布局后它**已不是**稳定版来源（稳定版 = `~/.agate/current/`），但仍是你的开发 checkout——改它会让本地状态混入"看起来像已发布"的假象 |
| `~/.agate` 禁止改动 | **版本管理根目录**（`repo/` + `vX.Y.Z/` + 指针 + 根 `scripts/` 副本），是稳定版来源；跑 gate / 读卡片用它，改它等于改稳定版 |
| gate 工具 ≠ 检查对象 | commit hook 用 `~/.agate` 判定；但 `check-protocol-consistency.py` 必须用 worktree 自己的（检查 worktree 里的文件） |
| `~/.agate` 脚本显示**稳定版**上下文 | `agate-summary.py` 在 worktree 跑显示稳定版（`AGATE_ROOT=~/.agate/vX.Y.Z/agate` + 版本号），**不是** worktree/开发 checkout 状态——worktree 状态用 `git log`/`git status` 看 |
| 工具稳定优先 | hook 指向稳定版，不指向 worktree（避免"用未验证的新 gate 判自己"）——用户已确认此哲学 |
| commit 时 phase = 本 commit 产出阶段 | 防 pre-commit 用下一阶段 gate 拦截 |

---

## 本机稳定版布局（对 dogfooding 的影响）

> **布局细节不在本 guide**：目录结构（`repo/` + `vX.Y.Z/` + `latest`/`current` 指针 + 根 `scripts/`）、
> 安装 / 迁移 / 更新 / 回退四动作、**hook 重装时机**、**根 `~/.agate/scripts/` 副本维护语义**——
> 权威源 = `agate/UPGRADING.md`「版本管理生命周期」节（自称"单一权威口径"，其余文档遇分歧以它为准）。
>
> 本节只写**dogfooding 需要知道的部分**（UPGRADING 不覆盖的 worktree 视角）。

**背景**：2026-09-18 本机 `~/.agate` 从 legacy 单软链布局迁移到版本管理布局。

**三件必须知道的事**：

| # | 事实 | 为什么重要 |
|---|------|-----------|
| 1 | **稳定版来源 ≠ 开发 checkout**：稳定版 = `~/.agate/current/`（指向 `vX.Y.Z/`） | 改开发 checkout 的 `agate/` **不再影响** hook 判定（迁移前会立即影响） |
| 2 | **要验证新 gate 行为须显式跑 worktree 脚本** | hook 用稳定版判定——`python3 agate/scripts/check-gate.py ...`（worktree 内的），不能靠"改完 commit 试试" |
| 3 | **项目可钉版本**：项目根 `.agate-version` 写 `agate: vX.Y.Z` | 与全局 `current` 解耦（如 PeekView 可钉 v0.70.0 而全局用 v0.71.1） |

> **⚠ 钉版本的容错陷阱（实测）**：声明**未安装**的版本 → **警告 + 回退全局 current**（exit 仍 0，不阻断）——
> 即"你以为锁定了 v0.70.0，实际跑的是 v0.71.1"。切换后须用下方命令确认解析结果。

**验证自己的解析**：

```bash
python3 ~/.agate/scripts/agate-resolve.py
# 输出三行：AGATE_ROOT=<版本目录> / AGATE_VERSION=<版本号> / AGATE_REASON=<解析原因>
# REASON 取值：AGATE_ROOT 环境变量覆盖 > 引用 .agate-version > 全局 current > legacy 软链布局
```

**注意**：`~/.agate/scripts/agate-summary.py` 显示**稳定版上下文**（`AGATE_ROOT=~/.agate/vX.Y.Z/agate` + 版本号），
**不是**你的 worktree 状态——后者用 `git log` / `git status` 看。

## 改动通道：worktree 优先，hotfix 例外

> **默认**：agate 自身改造任务（P0-P8）**必须**走 worktree。
>
> **hotfix 通道**：**不构成 agate 任务**的一次性修复，满足**全部**下列条件时**可不开 worktree**（直接在开发 checkout 改 → 分支 → PR）：
>
> | # | 条件 |
> |---|------|
> | 1 | 改动面 ≤2 文件、无跨模块影响 |
> | 2 | **不触发 SELF-GATE**（不碰 `agate/` 下任何文件、`AGENTS.md`、`README.md`、`SELF-GATE.md`） |
> | 3 | 不产生阶段产出（无 P0-brief/.state.yaml/P1-P8） |
> | 4 | 有明确验证判据（单测 + 目标命令 exit code），不需多轮评审 |
>
> **典型**：配置 key 对齐上游 schema（如 DSH persona `text`→`prefix`，PR #325）、文案修正、单文件 bug、CI 配置微调。
>
> **不适用**：任何 `agate/` 协议本体/脚本改动（SELF-GATE）、需阶段产出的改动（= agate 任务）、跨子系统探索性设计。
>
> **hotfix 也走 PR**（main 受保护），只是不开 worktree、不建任务目录。

## 发布与合并：tag / PR / merge 策略（TAG0035 复盘补全）

> **本节回答三个高频疑问**：tag 打在哪个 commit？worktree 要不要 merge main？PR 用什么 merge 策略？

### 1. tag 打在哪里：**打在 worktree 的 P8 commit 上**（现状，且是对的）

P8 卡片明确规定（`phase-cards/P8-release.md:12`）：

> 主 Agent 执行 gate 验证 → 通过后执行 bump-version + CHANGELOG 更新 → **同一 commit + tag**

**实测确认**（v0.71.1）：

```bash
$ git rev-parse v0.71.1^{commit}     # → ac2cc73（worktree 分支的 P8 commit，单 parent）
$ git merge-base --is-ancestor v0.71.1 origin/main && echo OK    # → OK
$ git describe --tags origin/main    # → v0.71.1-7-g8890a09  ✅ 正确
```

**为什么这样是对的**：tag 标记的是「**发布内容**」（bump 后的 version 文件 + CHANGELOG），而 PR 的 merge commit **不改变这些内容**。tag 指向 P8 commit → 经 PR merge 进入 main 历史 → `describe` 正常工作。

**⚠ 漂移风险只有一个**：**PR 必须用普通 merge（`--no-ff`），禁止 squash**。
squash 会产生「内容相同但 SHA 不同」的新 commit → tag 指向的 P8 commit **不在 main 历史里** → `git describe --tags --abbrev=0` **回退到旧 tag** → CHECK 7（README badge vs tag）报错（v0.31.0 事故）。

**若已误用 squash**：
```bash
git tag -f vN.N.0 <main-commit> && git push origin vN.N.0 --force
```

#### 附注标签 vs 轻量标签（**实测发现的不一致**）

**背景**：验证 tag 是否漂移时，`git ls-remote --tags` 与 `git rev-parse vX.Y.Z^{commit}` 会给出**不同的 SHA**——这**不是漂移**，而是 tag 类型差异：

| 命令 | 返回什么 |
|------|---------|
| `git ls-remote --tags origin vX.Y.Z` | **tag 对象的 SHA**（附注标签）或 commit SHA（轻量标签） |
| `git rev-parse vX.Y.Z^{commit}` | **总是**解引用到 commit SHA |
| `git cat-file -t vX.Y.Z` | `tag`（附注）或 `commit`（轻量） |

**实测（2026-09-17）**：

```bash
$ git cat-file -t v0.71.1     # → tag     （附注标签）
$ git cat-file -t v0.71.0     # → commit  （轻量标签）
$ git cat-file -t v0.70.0     # → commit
$ git cat-file -t v0.69.0     # → commit
```

**即：`v0.71.1` 是仓库里第一个附注标签，v0.71.0 及更早全是轻量标签。**

**影响评估：无功能危害**——既有机制全部用 `git describe --tags --abbrev=0`（CHECK 7 / P8 G-5 验证），而 `describe` **对两种标签一视同仁**：
```bash
$ git describe --tags --abbrev=0 origin/main    # → v0.71.1  ✅
```

**但建议统一**：附注标签能带 tagger/日期/说明（`git cat-file -p v0.71.1` 可看到 "Agateon v0.71.1 — gate 健壮性批…"），信息更丰富；轻量标签更简洁。**当前不一致属历史遗留，无需回改**，但**新版本应统一用同一种**——若要改为附注（推荐，可写发布说明）：

```bash
git tag -a vN.N.0 -m "Agateon vN.N.0 — <一句话发布说明>"
```

> **⚠ 提醒**：`git ls-remote --tags` 与 `rev-parse^{commit}` 的 SHA 差异**不要误判为漂移**。判断漂移的正确命令是：
> ```bash
> git merge-base --is-ancestor vX.Y.Z origin/main && echo "在 main 历史 ✓" || echo "漂移 ✗"
> ```
> （用 `^{commit}` 解引用后判断，或直接用 tag 名——`merge-base` 会自动解引用附注标签。）


### 2. worktree 要不要 merge main：**看情况，但合并前必须确认无冲突面**

| 场景 | 做法 |
|------|------|
| 任务期间 main 前进（其他 PR 合并） | **可 merge `origin/main` 进 worktree 分支**——保持分支最新，减少合并时的冲突 |
| PR 报 `BEHIND`（落后 main） | **必须先 merge**：GitHub 保护规则要求 up-to-date 才允许合并 |
| 无冲突面 | 直接 `git merge origin/main`（会生成 merge commit，正常） |

**实测（PR #325 的经历）**：
```bash
$ gh pr view 325 --json mergeStateStatus,mergeable
{"mergeable":"MERGEABLE","state":"BEHIND"}      # BEHIND ≠ 冲突，只是落后
$ git merge origin/main                          # 解决 BEHIND
$ git push && gh pr merge ...                    # 然后才能合并
```

**⚠ 注意**：worktree 里 merge main 会产生 merge commit（如 `ff4df74 Merge remote-tracking branch 'origin/main' into hotfix/...`）——这是正常的，**不影响 tag**（tag 打在 P8 那个 commit 上，不在 merge commit 上）。

#### 合并被拒时怎么做（实测症状与处理）

`git-to-main <PR#>` **报 `Merge blocked`** 时，先分辨**三种不同原因**——处理方式不同：

| 症状（`gh pr view <PR#> --json mergeStateStatus`） | 原因 | 处理 |
|--------------------------------------------------|------|------|
| `BEHIND` | 分支落后 main（保护规则要求 up-to-date） | `git merge origin/main` → `git push` → **重新等一轮 CI**（合并前必须再绿） |
| `BLOCKED` + 某 required check 未完成 | CI 还在跑（不是真阻塞） | `gh pr checks <PR#> --watch` 等完 |
| `BLOCKED` + check 为 `skipping` | **docs-only 快路径**：`platform-scan` / `ruff` 被跳过，但保护规则仍要求它们 | 见 `docs/guides/ci-docs-only-playbook.md`；同步 main 后重跑通常可解 |

**实测（TAG0036 收尾，2026-09-19）**：合并被拒一次，根因是分支保护要求与 main 同步——`git merge origin/main` 把 main 的 4 个 docs-site 提交合入分支，**再等一轮 CI 全绿**后才合并成功。

> **要点**：**merge main 之后必须重新等 CI**，不能复用合并前的绿灯（merge 引入了新代码面）。

### 3. PR merge 策略：**普通 merge（`--no-ff`），禁 squash / 禁 rebase**

```bash
# 正确（git-to-main 默认行为）：
/home/kity/bin/git-to-main <PR#>          # gh pr merge --merge

# 错误（会导致 tag 漂移）：
gh pr merge <PR#> --squash                 # ❌ tag 指向的 commit 不在 main 历史
gh pr merge <PR#> --rebase                 # ❌ 同上
```

**理由**：CHECK 7（`check_version_badge`）与 P8 的 G-5 验证都用 `git describe --tags --abbrev=0` 取最新 tag；squash/rebase 生成的 SHA 与 tag 分叉 → describe 回退旧版。

---

## 收尾：合并后同步主 checkout（**实测四次踩坑**）

> **本节是 TAG0032/0035 等任务中反复出现的问题**——合并 PR 后同步主 checkout 时，ff 合并被"本地未跟踪/已修改文件"挡住。四次都发生在同一模式上。

### 症状

在**主 checkout** 执行 `git fetch && git merge --ff-only origin/main` 时报错：

```
error: 您对下列文件的本地修改将被合并操作覆盖：
	agate-workspace/roadmap/roadmap.md
请在合并前提交或贮藏您的修改。
```
或
```
error: 工作区中下列未跟踪的文件将会因为合并操作而被覆盖：
	docs/reviews/review-260916-0828.md
```

**根因**：你（或并行会话）曾**在主 checkout 直接创建/修改过**这些文件，而它们**已被 PR 合并进 main**——于是本地副本成了"挡路的重复品"。

### 处理流程（**必须先核对内容，再清除**）

```bash
# ① 逐文件核对：本地工作区 vs origin/main 是否逐字节一致
for f in <被挡住的文件列表>; do
  if git show origin/main:$f 2>/dev/null | diff -q - $f >/dev/null 2>&1; then
    echo "  ✓ 一致: $f"
  else
    echo "  ★不一致: $f  ← 停下来人工看，不要删"
  fi
done

# ② 全部一致 → 安全清除本地副本
git checkout -- <已跟踪且一致的文件>
rm -f <未跟踪且一致的文件>

# ③ 完成 ff 合并
git merge --ff-only origin/main
```

**关键原则**：**`diff` 一致才清除**——不一致说明本地有 main 没有的内容（可能是你的未提交工作），此时必须人工判断，**不得直接删**。
（四次实践均通过此流程零丢失；`git-to-main` 的 `--force` 与 `rm -rf` 都不需要。）

### 为什么会有这些"重复副本"？

| 来源 | 例子 |
|------|------|
| 之前用主 checkout 直接改了 workspace 数据面（roadmap / 看板 / P0-brief），随后在 worktree 提交并 PR | TAG0035 收尾、RM-AG0063/0064 立项 |
| 用户提供的评审/附件文件放在主 checkout，随后被 PR 收进仓库 | `docs/reviews/review-*.md` |
| 运行时产物（gate-events.jsonl 等） | 与合并带入的跟踪版本冲突 |

---

## 完成后清理

> **⚠️ HANDOFF 归档是最常被漏的一步**——TAG0028 漏过，**TAG0035 与 TAG0036 又连续漏了两次**（2026-09-19 实测：仓库根残留 `HANDOFF-TAG0035.md` + `HANDOFF-TAG0036.md`，需单独补一个 PR 归档）。**建议在 P8 收尾的同一个 PR 里就做掉归档**，不要留到"以后再说"——任务一合并，人就切走了。

```bash
# 任务合并 main 后，先归档 HANDOFF（HANDOFF 已被 git 跟踪且随 PR 并入 main，是 main 的正式文件——
# 不归档则仓库根累积历史 HANDOFF-TAG0xxx.md。TAG0028 漏归档实证：worktree 清理只删分支，
# HANDOFF 留在 main 根直到后续任务从 main checkout 时被带进新 worktree）
git mv HANDOFF-{Txxx}.md agate-workspace/archived/plans/HANDOFF-{Txxx}.md
git commit -m "chore(workspace): HANDOFF-{Txxx} 归档至 archived/plans（任务已完成 PR 合并）"
# 走 PR 合并归档 commit（与代码合并同批或紧随其后，确保 main 根不残留）

# worktree 有未追踪残留（P5 日志等）时 remove 会拒删——确认已合并 main 后加 --force
git worktree remove .worktrees/agate-{Txxx} --force
git branch -D feat/{Txxx}-{slug}
# 若 PR 未自动删远端分支：
# git push origin --delete feat/{Txxx}-{slug}
# 收尾自检（两条都要过）：
#   ls HANDOFF-*.md                      # 应为空（仓库根无残留）
#   ls agate-workspace/archived/plans/HANDOFF-{Txxx}.md   # 应存在（已归档）

# ⚠ 最后一步：按上一节「收尾：合并后同步主 checkout」同步主 checkout
# （若你在主 checkout 造过 workspace 文件，ff 合并会被挡住——先 diff 核对再清除）
```

### 任务收尾检查清单（TAG0035 复盘补全）

任务 P8 READY + PR 合并后，逐项确认：

| # | 项 | 校验命令 |
|---|----|---------|
| 1 | HANDOFF 已归档 | `ls agate-workspace/archived/plans/HANDOFF-{Txxx}.md` |
| 2 | 看板已入「已完成（归档）」区 | `awk '/^### /{s=$0} /{Txxx}/{print s}' agate-workspace/tasks/active-tasks.md` |
| 3 | roadmap 关联条目已 `done` | P8 gate 硬校验（RM-AG0043）会自动查；手动核对 `grep "{RM-AGxxxx}" agate-workspace/roadmap/roadmap.md` |
| 4 | **复盘已产出** | `ls agate-workspace/tasks/{Txxx}-*/retrospective.md` ⚠️ **TAG0035 曾漏此项** |
| 5 | DEBT 回写：本任务修复的置 `closed` + `task_id` 用**纯编号** | `grep -A5 "## DEBT00xx" agate-workspace/debt/tech-debt.md` |
| 6 | **被移出/未纳入的 DEBT 有去向** | 若评审移出过条目，确认已登记归属（RM 或独立立项）⚠️ **TAG0035 的 DEBT0040/0041 曾悬空** |
| 7 | worktree 与分支已清理 | `git worktree list`、`git branch --list 'feat/{Txxx}*'` |
| 8 | 主 checkout 已同步且干净 | `git status --short`（空）+ `git log --oneline -1` |
| 9 | tag 有效且在 main 历史 | `git merge-base --is-ancestor v{版本} origin/main && git describe --tags origin/main` |
```

## 与 AGENTS.md 的关系

AGENTS.md「dogfooding 工作流（Agateon 自身改造任务必读）」已有双工作区纪律的零散条目。本指南是把"构建"流程固化。纪律部分两者一致；若冲突以 AGENTS.md 为准。
