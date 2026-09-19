# TAG0036 交接单 — MVWU 阶段 1 试点（RM-AG0063）

> 本交接单供 worktree session 的 agent 按此启动 TAG0036 任务。
> 任务已 P0 立项（`.state.yaml` phase=P0，`P0-brief.md` 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。
> **本交接单按 `docs/guides/worktree-dogfooding-guide.md` 的 10 步流程重建（2026-09-19）**——含 ⑤ 的 7 个方法学概念落地要求。

---

## 1. 你要做什么

**TAG0036**：MVWU（最小可验证工作单元）阶段 1 试点。

**一句话**：把 agateon 既有的「批（batch）」实践从**散文形态**升为**结构化声明**——新增 `batches[].tests_filter` 可选键与 `P4-evidence/{batch}.log` 证据落点，新建**不阻断**的独立 check（`check-mvwu.py`）产出四态 verdict，并让 Q1/Q2/Q3 的采集流程就绪。**不挂 gate、不改 `.state.yaml`、不改 P6.5、不改 scheduler。**

**本任务另有 ⑤ 组交付**（7 个方法学概念，见 P0-brief §⑤）：Ubiquitous Language 术语补录 / Deep Modules 审查锚点 / Tracer Bullet + Vertical Slice + Architecture Fitness Functions 三条批切分判据 / Walking Skeleton 部分吸收 / Evolutionary Architecture 决策复审机制。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0036` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
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

**已完成的 setup（2026-09-19 按 guide 重建）**：
- 依赖齐全：bash 5.2.21 / python 3.12.3 / pytest 9.0.3 / pyyaml / shellcheck 0.9.0 / ruff 0.16.4
- **基线验证**：CI 口径（`--reruns 1 -n auto`）**1666 passed / 2 skipped**
- commit hook：三个 hook → `~/.agate/scripts/`（稳定版）
- orchestrator 注册：`.opencode/agents/orchestrator.md` + `.claude/agents/orchestrator.md` → **`$AGATE_DIR/orchestrator-template.md`**（`AGATE_DIR` = 协议根，按 guide「先取协议根路径」节解析；双平台软链，**已验证可读**）
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`
- 任务数据：TAG0036 P0-brief（**281 行**）+ `.state.yaml` phase=P0
- **基线 HEAD**：`efb113b`（含 PR #343 的 SETUP.md 协议根路径修复）

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

> **完整 scope 见 `P0-brief.md`**（281 行，含 4 项 MVWU 交付物 + ⑤ 组 7 个方法学概念 + 14 条完成判据 + out-of-scope + 7 条 known_risks）。

### ① `batches[].tests_filter`（P2-design.md frontmatter 可选键）

```yaml
dispatch_plan:
  mode: static-batch
  batches:
    - id: auth-token-parser
      complexity: medium
      tests_filter: "pytest tests/auth/test_token.py"
```

- **位置**：`P2-design.md` 的 **frontmatter**（`agate-md-field-get.py` 的 `JSON_FIELDS` 读取，仅 frontmatter、无正文回退防伪造）
- **零内核改动依据（实测）**：`check-gate.py:743 _gate_p2_dispatch_plan` 校验 `mode`/`parallel_limit`/`batches`/`id`/`complexity`，**不拒绝未知键**

### ② `P4-evidence/{batch}.log` 证据落点（**新建目录**）

- 现存 `P6-evidence/`（37）、`P5-test-results/`（34）、`P6.5-judge-evidence/`（1）；`P4-evidence/` **不存在**
- **最小内容**：`command` / `exit_code` / `git_head` / `timestamp` / `expected_red` / **`duration_seconds`**（供 `--observe` 耗时列）

### ③ `check-mvwu.py`（新建，独立脚本，**不挂 gate**）

- **六项检查**：`tests_filter` 存在 / command 可执行 / evidence 存在 / `exit_code` 可解析 / git HEAD 可关联 / verdict
- **四态 verdict**：`PASS` / `FAIL` / `EXPECTED_RED` / `UNKNOWN`——**`UNKNOWN` ≠ `PASS`，不得作为放行依据**
- **`--observe` 模式**（交付物）：输出可粘贴进观察表的一行，补齐**耗时 / commit 形态 / boundary** 三列
- **自身单测**：须用 `tmp_path`（DEBT0040 教训）

### ④ 字段落地路径（交付物，**不可省**）

- `agate/phase-cards/P2-design.md` + `agate/assets/execution-roles/architect.md` 写明 `tests_filter` 写法——否则**无人会写该字段 → 样本永不到来**

### ⑤ 组：7 个方法学概念的落地

| 子节 | 交付物 |
|------|--------|
| **⑤-a** Ubiquitous Language | `CONTEXT.md` 补录本任务新术语（`MVWU`/`tests_filter`/`P4-evidence`/四态 verdict/`boundary(I1)`） |
| **⑤-b** Deep Modules | `role-system.md` 补审查锚点（判据 = 角色文件是否规定执行顺序而浅化接口） |
| **⑤-c** Tracer Bullet + Vertical Slice + Fitness Functions | `architect.md` + `P2-design.md` 卡片补**三条判据** |
| **⑤-d** Walking Skeleton | 仅记录「拒绝部署/CI（`adr.md` 技术栈中立）+ 吸收"骨架先跑通"」 |
| **⑤-e** Evolutionary Architecture | `adr.md` 补复审触发条件（前提被证伪 → 标注已过时+取代者，不删除）；项目侧补「跨任务架构决策落 `{AGATE_WORKSPACE}/decisions/`」（**现目录空置 = 机制未启用**） |

### 核心约束（不可违反）

1. **Linux 现状是基线**——全量 pytest 全绿是回归底线
2. **不改协议内核**：`.state.yaml` schema / `check-gate.py` gate 分支 / `phases.yaml` / `agate/rules/schema/*.json` / hook 三件套 / `gate-events` 审计链——**一律不改**
3. **不主动造样本**、**不用历史回填**（P0-brief known_risks 已说明理由）
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

# ruff（CI 锁 0.16.4，与本地 ~/.venvs/agate-dev/bin/ruff 对齐）
~/.venvs/agate-dev/bin/ruff check agate/

# 测试计数（验证用例数没漂移）
timeout 60 bash agate/tests/scripts/count-tests.sh

# MVWU 工具（实现后）
timeout 60 python3 agate/scripts/check-mvwu.py <task_dir>
timeout 60 python3 agate/scripts/check-mvwu.py --observe <task_dir>
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；**不要**先写 phase=P2 再 commit P1 产出（pre-commit 会用 P2 gate 检查，P2-design.md 不存在 → 拦截）
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿
- **批量机械改动的 TDD 策略**：先写一个"grep 断言审计"测试作为回归拦截；批量改动后跑该断言 + 全量 pytest
- **git 命令加 timeout**、单步串行
- **commit message 含 `wf(TAG0036-P{阶段}):` 前缀**
- **⚠ SELF-GATE 触发面**：`check-mvwu.py`（`agate/scripts/*.py`）+ 卡片/角色文件（`agate/**/*.md`）+ `CONTEXT.md`/`role-system.md`/`adr.md` **均命中** → commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；且须跑 consistency 0 ERROR
  - 触发面权威源 = `commit-msg-self-gate.py` 的 `_SELF_GATE_RE` 正则（判断命令见 `SELF-GATE.md`「触发条件」节）
- **验证前先对齐 CI 口径**（`--reruns 1`）——否则可能把已知 flaky 当新缺陷追（本机需装 `pytest-rerunfailures`）

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0036-mvwu-pilot/`（worktree 内）
- `.state.yaml`：phase=P0（P1 开始后推进）
- `active-tasks.md`「待开始」已有 TAG0036 行
- roadmap：**RM-AG0063**（`scheduled`）关联本任务
- **编号体系**：`TAG0036`（校验器 `^T[A-Z]{2}\d+$`）

## 7. 已知风险与止损

> 完整 7 条见 `P0-brief.md` §known_risks。以下为要点。

| 风险 | 止损 |
|------|------|
| **I1 可归属率仅 13%**（16 个多批任务中 2 个逐批 commit；87% 合并提交）——**本任务最大风险** | 合并提交形态下 boundary **必然判 `UNKNOWN`**——不是缺陷而是**诚实标注**。Q2 产出定义为**比例数据**；若比例过低，触发**提交粒度取舍**（须**用户裁决**，本任务不自行决定） |
| **"批是否逐批 commit"无稳定命名约定** | `TAG0016` 用 `-P4a`、`TAG0034` 用中文"P4a 批"、多数不标记 → check 需容忍 `UNKNOWN` |
| **`tests_filter` 平台中立性** | Windows 常无 `make`（应写 `python -m pytest`）；不裸 `python3`（遵循 `AGATE_PYTHON` 探测，DEBT0014）；`{batch}` 须 **filename-safe**（`[A-Za-z0-9._-]+`） |
| **与 P3 TDD 红灯冲突** | 批级 commit **本身带预期红灯**（实测 `d1c2aca` "57 绿 / 3 批次边界红"）→ `tests_filter` 须有 **scoping 规则**（只覆盖该批交付面、禁止全量）+ `expected_red` 声明 |
| **样本可得性** | Q1/Q3 需真实多批任务，当前任务已全完成 → **完成判据不含"Q1/Q3 已答"**；交付"采集能力就绪" |
| **⑤ 组中只有 a/c 有可验证交付物** | 判据只要求"**成文到位**"，**不宣称"机制已生效"**（b/d 的生效性需后续实践检验） |
| **【环境注记】本机 `~/.agate` 是版本管理布局** | 改开发 checkout 的 `agate/` **不影响** hook 判定；`SETUP.md` 的协议根路径已由 PR #343 修复（`$AGATE_DIR`）；版本解析链可测性缺口登记为 **DEBT0042**（已 closed） |

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**PR 普通 merge 非 squash**，tag 要求）
- **合并前看 CI 结果**——pytest / shellcheck / consistency / gate-backstop 全绿才算过
- roadmap **RM-AG0063** 回写 → `done`（P8 gate 硬校验 RM-AG0043）
- **阶段 2（批级 gate）不在本任务内**——需 Q1 ≥90% **且**提交粒度决策已裁决，另立任务
- 复盘按 agate 自身变更流程归档

## 9. 交接确认

- worktree 基线全绿：CI 口径 **1666 passed / 2 skipped**
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册（**双平台软链已验证可读**）、依赖齐全
- 任务数据就绪：TAG0036 P0-brief（**281 行**）+ `.state.yaml` phase=P0
- **基线 HEAD**：`efb113b`（含 PR #343 协议根路径修复）
- 交接单位置：`HANDOFF-TAG0036.md`（worktree 根，已 commit）
- **重建方式**：2026-09-19 按 `docs/guides/worktree-dogfooding-guide.md` 10 步流程删除重建（验证 guide 可用性）

---

> **启动入口提醒**：orchestrator 默认读 `{AGATE_WORKSPACE}/tasks/active-tasks.md` + `.state.yaml`，**不会自动读 HANDOFF**。新 session 首条指令请显式写「**读 worktree 根 `HANDOFF-TAG0036.md`**」。
