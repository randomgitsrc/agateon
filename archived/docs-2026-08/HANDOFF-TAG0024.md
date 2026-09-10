# TAG0024 交接单 — 工具链批：结构化字段写入工具（agate-md-field-set）+ 前置修复

> 本交接单供 worktree session 的 agent 按此启动 TAG0024 任务。
> 任务已 P0 立项（.state.yaml phase=P0，P0-brief.md 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0024**：工具链批（RM-AG0048 一期 agate-md-field-set + DEBT0019/20 check-gate roadmap-done 健壮性 + RM-AG0049/50 协议文档自洽）。

**一句话**：给 subagent 提供"写入即校验"的结构化 set 工具（消灭手写 frontmatter 摩擦），并修复 check-gate roadmap-done 两处健壮性缺陷与两处协议文档自洽 NIT。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agate/.worktrees/agate-TAG0024` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agate`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → 主 checkout/agate） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是 worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。
- **⚠️ gate 工具 ≠ 检查对象**：
  - `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`）——检查对象是 worktree 里的协议文件。若误用 `~/.agate` 的会扫到主 checkout。
  - 同理：`python3 ~/.agate/scripts/agate-summary.py` 在 worktree 里跑会显示主 checkout 上下文，不代表 worktree 状态。
  - 同理：**所有编排/派发类工具脚本**（`agate-inject-card.py`、`agate-render-dispatch-prompt.py`、`agate-next-card.py` 等）都用 `~/.agate/scripts/` 稳定版调用（TAG0016 教训）。
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 实际在主 checkout 的 `.git/hooks/`（pre-commit/commit-msg/pre-push 已软链安装）。worktree commit 时 hook 自动触发。

**已完成的 setup（worktree 已可独立使用）**：
- 依赖齐全：bash / python / pyyaml / pytest / shellcheck
- 基线验证：全量 pytest 全绿 + consistency 0 ERROR（--strict-errors-only）
- commit hook：指向 `~/.agate`（稳定版），worktree commit 自动触发
- orchestrator 注册：`.opencode/agents/orchestrator.md` + `.claude/agents/orchestrator.md` → `~/.agate/orchestrator-template.md`（符号链接，不拷贝，双平台）
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`
- 任务数据：TAG0024 P0-brief + .state.yaml phase=P0 在 worktree 的 `agate-workspace/tasks/TAG0024-toolchain-md-field-set/`

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 已核实并确认的需求/缺陷（全部有证据，见 P0-brief issues）

**RM-AG0048（一期）**：
- 新增 `agate-md-field-set.py` + `agate-md-field-set-gate-commands.py`——key 从 schema 白名单限定（phases.yaml task_fields ∪ task-files 通用 Header）、value 写入时校验（与 check-gate 同源）、格式由工具生成（YAML 序列化）
- 自描述（--list/--help/错误给合法值，判据"零协议知识 subagent 照提示填对"）；写入即局部校验 + 剩余缺失报告
- 角色/阶段/文件三维权限（角色维度读文件 agent 字段，选项 A）；证据字段（pass/fail/blocker_count 等）set 拒绝写入
- gate_commands 正文 YAML 块经专用子命令整块替换（同源校验）
- 原子写 + 版本一致（resolve-entry 链）；dispatch-context 模板加一行式指令 + dispatch-prompt 改"用 set 填"
- 验收锚 = `docs/design-notes/design-md-field-set.md` §10 十一条

**DEBT0019**：`check-gate.py._check_roadmap_done()` 用固定索引 split("|") 解析 roadmap.md 表格，无列数完整性校验 → 列数校验（非法列数跳过/WARNING）+ 回归用例

**DEBT0020**：`check-gate.py._check_roadmap_done()` 调用点相对 CWD 硬编码路径拼接 roadmap.md → 对齐 repo-root 定位（git rev-parse --show-toplevel）或加区分性 stderr 提示 + 回归用例

**RM-AG0049**：phases.yaml P4 outputs 未列出 P4-review.md，但 check-gate.py gate_p4 实际要求其存在 → phases.yaml P4 outputs 补 `{file: P4-review.md, required: true, status_field: status}` + 核对 check-structure-consistency 同步

**RM-AG0050**：phases.yaml 将 P6.5 列为独立阶段条目，state-machine.md 明确其为"挂载于 P6→P7 转移的强门槛子阶段" → 统一为"强门槛子阶段"口径（state-machine 为准），核对 check-gate/check-judge-verdict 消费端不受影响

### 核心约束（不可违反）

1. **Linux 现状是基线**——现有全量 pytest 测试全绿是回归底线，每个修复都必须保持全绿
2. **design note（docs/design-notes/design-md-field-set.md）仅为参考输入，不作为本 task 交付物**——执行中发现需求/设计层面弊端或缺陷，按实际情况调整（改设计/登记 DEBT），不强制照搬
3. **不破坏已有协议语义**——RM-AG0048 一期不得改动 check-gate/check-events 的判定逻辑（set 只写 gate 本就要校验的字段）；DEBT0019/20 只修 roadmap-done 检查的健壮性，不得改变判定结果
4. **范围锁定**——若 P1 分析发现需改动超出 P0-brief 锁定范围，须先停下跟用户确认

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（必须全绿才算过）
python3 -m pytest agate/tests/

# 一致性（0 ERROR 才行；--strict-errors-only 仅在 ERROR 时 exit 非 0）
# ⚠️ 必须用 worktree 自己的脚本，不要用 ~/.agate 的
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck
shellcheck -S warning agate/scripts/*.sh

# 测试计数（验证文档没漂移）
bash agate/tests/scripts/count-tests.sh

# 单脚本测试（改哪个跑哪个，TDD 先红后绿）
python3 -m pytest agate/tests/unit/test_{具体测试文件}.py
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿（AGENTS.md「改脚本的工作流」）
- **批量机械改动的 TDD 策略**：先写一个"grep 断言审计"测试作为回归拦截；批量改动后跑该断言 + 全量 pytest 确认绿。不要为每个小改动单独写测试，也不要跳过测试直接改
- **git 命令加 timeout**、单步串行（AGENTS.md 工具纪律）
- **commit message 含 `wf(TAG0024-P{阶段}):` 前缀**
- **改 `agate/*.md`、`agate/scripts/*.py/.sh`、`agate/phase-cards/*` 触发 SELF-GATE**：commit message 需含 `self-gate-review:` 或 `self-gate-skip:`（否则 commit-msg hook WARNING）。协议文档变更需跑 `check-protocol-consistency.py` 确认无 ERROR

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0024-toolchain-md-field-set/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）
- active-tasks.md「待开始」已有 TAG0024 行
- roadmap：RM-AG0048 / RM-AG0049 / RM-AG0050 关联本任务（scheduled）
- **编号体系**：任务用 `{Txxx}`（项目代号 + 动态数字，v2.0 起的 Jira 式编号）。校验器 `^T[A-Z]{2}\d+$`

## 7. 已知风险与止损

- **RM-AG0048 的"与 gate 同源"**：set 的 value 校验复用 check-gate 判定逻辑，须走同一 schema 源 + resolve-entry 版本链，避免"set 说通过、gate 说不通过"的新漂移 → P2 设计同源复用路径（import vs 复制），P5 验证
- **角色权限（选项 A）空洞**：只对"遵守协议填了 agent 的 subagent"有效，set 是引导非安全边界 → 不承诺防恶意，防造假靠 gate 链
- **DEBT0019/20 改 check-gate.py 的 roadmap-done 检查**：需回归 TAG0023 的 BDD（P8 roadmap 回写校验）确保不破坏 → P3 加回归用例
- **RM-AG0049 改 phases.yaml P4 outputs**：check-structure-consistency S-1/S-2 双向一致性 gate 可能因 YAML→md 不一致报错 → 同步核对
- **SELF-GATE 触发面**：改动涉及 agate/scripts + phases.yaml + 模板 → commit 需 self-gate-review/skip

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（PR 普通 merge 非 squash，tag 要求）
- **合并前在 PR 里看 CI 结果**——pytest/shellcheck/consistency/gate-backstop 全绿才算过
- roadmap 回写关联条目 → done
- 复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新 roadmap/版本）

## 9. 交接确认

- worktree 基线全绿：全量 pytest + consistency 0 ERROR（--strict-errors-only）
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册、依赖齐全
- 任务数据就绪：TAG0024 P0-brief + .state.yaml phase=P0
- 交接单位置：`HANDOFF-TAG0024.md`（worktree 根，已 commit）
