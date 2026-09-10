# TAG0025 交接单 — Agateon 品牌改名执行 Phase 0-1（RM-AG0035）

> 本交接单供 worktree session 的 agent 按此启动 TAG0025 任务。
> 任务已 P0 立项（.state.yaml phase=P0，P0-brief.md 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0025**：Agateon 品牌改名执行 Phase 0-1（RM-AG0035 剩余工作②）。

**一句话**：按评审通过的 `docs/design-notes/design-rename-execution.md` 三层解耦原则（外部品牌层
改、内部命名空间不动），完成品牌声明（"Agateon (formerly agate)"）+ GitHub 主仓改名
`agate` → `agateon` + 硬编码仓库 URL 同批更新（设计 §4 实测 7 处 + P1 补全仓扫描）+
本机全部 remote 迁移。Phase 2（v1.0 别名/品牌 prose/brand-check）与 Phase 3（门户）**不在范围**。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agate/.worktrees/agate-TAG0025` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agate`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → 主 checkout/agate） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是
  worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。这是有意的：改造期间工具稳定，改造对象变化。
- **⚠️ gate 工具 ≠ 检查对象**：`check-protocol-consistency.py` **必须用 worktree 自己的**；
  `agate-summary.py` 在 worktree 跑显示主 checkout 上下文，不代表 worktree 状态；
  编排/派发类工具一律 `~/.agate/scripts/` 稳定版（TAG0016 教训）。
- **hook 在共享 git 目录**：主 checkout `.git/hooks/`（三个软链已装），worktree commit 自动触发。

**已完成的 setup（worktree 已可独立使用）**：
- 依赖齐全：bash 5.2 / python 3.12.3 / pyyaml / pytest 9.0.3 / shellcheck / ruff 0.16.4
- 基线验证（2026-08-26）：unit 1160 passed + 2 skipped，其余 131 passed，consistency 0 ERROR
  （--strict-errors-only；总 collect 1293）
- commit hook：指向 `~/.agate`（稳定版），自动触发
- orchestrator 注册：`.opencode/agents/` + `.claude/agents/` 双平台软链
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`（已验证）
- 任务数据：TAG0025 P0-brief + .state.yaml phase=P0 在 worktree 的 `agate-workspace/tasks/`

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 需求来源（全部有文档证据）

**执行地基**：`docs/design-notes/design-rename-execution.md`（三轮独立评审通过，2026-08-25 入 main）
- **Phase 0（品牌声明）**：README×2 / CHANGELOG 标 "Agateon (formerly agate)"——验收锚：首页可见
- **Phase 1（仓库改名）**：`randomgitsrc/agate` → `randomgitsrc/agateon`；同批更新硬编码 URL
  （install.sh:24 / agate-install.py:55 / agate-changes.py:116 / README.md:5,29 /
  README.zh-CN.md:5,29——设计 §4 实测，P1 须补全仓扫描 `randomgitsrc/agate`）；
  `git remote set-url` 本机全 clone（主 checkout + 全部 worktree）——验收锚：旧 URL 301 /
  `git ls-remote` 新名正常 / 无旧 URL 残留 / `in:name` 首屏命中 `agateon`

**用户侧协同项（跟踪不交付）**：商标申请（人工复核后，见 `agateon-trademark-research.md`）；
PyPI/npm/crates.io 包名占位；org 迁移随门户立项再议。

### 核心约束（不可违反）
1. **全绿是回归底线**——1293 用例全绿 + consistency 0 ERROR，每个改动必须保持
2. **内部命名空间禁动**——`agate/` 目录 / `agate-workspace/` / `~/.agate` / `AGATE_*` /
   `agate-*.py` / `agate_common` 一律不改；**禁止全局 find-replace**（设计 §1 最大反模式）；
   backtick token 一律保留（§5.3 判定规则）
3. **不可逆操作双确认**——GitHub 仓库改名执行前：① 实测确认 `gh` 有 repo 管理权限
   ② 用户在场放行；改名后立即跑 4 条验收锚，任一失败即停下汇报（301 兜底存在但不可依赖）
4. **范围锁定**——Phase 2/3 内容（agateon-* 别名、品牌 prose 统一、brand-check、CHECK 10
   白名单扩展、门户）发现需要也不做，记入交接单/DEBT 待后续任务；其他超范围发现先停下问用户

## 4. 关键验证命令

```bash
# 在 worktree 根执行：
python3 -m pytest agate/tests/                      # 全量（建议分 unit/regression/integration 片跑）
python3 agate/scripts/check-protocol-consistency.py --strict-errors-only   # ⚠️ 用 worktree 自己的
shellcheck -S warning agate/scripts/*.sh            # install.sh 若改动
bash agate/tests/scripts/count-tests.sh             # 用例数不漂移（基线 1293）

# 改名后验收锚（Phase 1 专用）：
curl -sI https://github.com/randomgitsrc/agate | head -3        # 期望 301 → agateon
timeout 30 git ls-remote https://github.com/randomgitsrc/agateon.git HEAD
grep -rn "randomgitsrc/agate\b" --include="*.md" --include="*.py" --include="*.sh" --include="*.yml" . --exclude-dir=.git --exclude-dir=.worktrees   # 期望无旧仓名残留（注意排除 archived/ 豁免层，见设计 §5.3）
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；不要先写 phase=P2
  再 commit P1 产出（pre-commit 用 P2 gate 检查 → 拦截）
- **改脚本走 TDD**：先红后绿；批量机械改动（如 URL 替换）先写 grep 断言审计测试再批量改 + 全量回归
- **git 命令加 timeout**、单步串行（AGENTS.md 工具纪律）
- **commit message 含 `wf(TAG0025-P{阶段}):` 前缀**
- **改 `agate/*.md`、`agate/scripts/*.py/.sh`、`agate/phase-cards/*` 触发 SELF-GATE**：
  commit message 需含 `self-gate-review:` 或 `self-gate-skip:`（否则 commit-msg hook WARNING）。
  本任务大概率触发（agate/scripts/agate-install.py、agate-changes.py、install.sh 等）
- **roadmap 回写注意**：RM-AG0035 含 ①-⑥ 多项，本任务只覆盖 ②（+品牌声明）——P8 回写时
  不能整条标 done（①商标/③④⑤属 Phase 2/v1.0），需拆分或注明部分完成口径（P8 前与用户确认）

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0025-agateon-rename/`（在 worktree 里）
- `.state.yaml`：phase=P0（P1 开始后推进）
- active-tasks.md 已有 TAG0025 行（🚧/P0）
- roadmap：RM-AG0035 关联本任务（当前 backlog，P8 按上述口径回写）
- **编号体系**：任务用 `TAG0025`。校验器 `^T[A-Z]{2}\d+$`

## 7. 已知风险与止损

- **仓库改名不可逆且对外可见**：→ 双确认（权限实测 + 用户放行）后执行；失败即停，不重试
- **改名后本地 remote 未迁移**：所有 clone 的 fetch/push 依赖 301（能工作但退化）→ 改名后
  在主 checkout `git remote set-url` **一次即可**（已实测：worktree 与主仓共享 `.git/config`），
  各 worktree `git fetch` 实测验证；详见 `agate-workspace/tasks/TAG0025-agateon-rename/env-rename-handoff.md`
- **CI 徽章/链接断链**：badge img src 硬编码旧仓名 → 与改名同批更新；改名后开一个测试 PR
  验证 CI 全绿（含 actions 徽章渲染）
- **硬编码 URL 盘点遗漏**：设计 §4 以安装入口为中心 → P1 全仓扫描 `randomgitsrc/agate`
  补全清单（注意 docs/ 非 archived、.github/workflows、badge URL）
- **DSH 会话环境引用本地路径**：`/home/kity/oclab/agate` 是本地目录名，**与 GitHub 仓名解耦，
  不改**——任何"顺手把本地目录也改名"的冲动都是越界（软链/会话配置全依赖此路径）

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**普通 merge 非 squash**，tag 要求）
- 合并前在 PR 里看 CI 结果——pytest/shellcheck/consistency/gate-backstop 全绿才算过
- roadmap 回写 RM-AG0035（按 §5 部分完成口径）
- 复盘按 agate 自身变更流程归档（合并后在主 checkout写复盘 + 更新 roadmap/版本）
- **版本发布**：本任务属品牌层变更——是否随版本发布（badge/CHANGELOG bump）由 P8 判定；
  若发布，UPGRADING.md 须加版本章节（CHECK 13 会强制校验，RM-AG0052 已落地）
- 用户侧协同项移交清单：商标申请人工复核 / PyPI-npm-crates 占位 / 门户立项议 org 迁移

## 9. 交接确认

- worktree 基线全绿：1293 collected（unit 1160+2 skipped + 其余 131）+ consistency 0 ERROR
  （--strict-errors-only，2026-08-26 实测）
- hooks 就位（指向 `~/.agate` 稳定版）、orchestrator 已注册、依赖齐全
- 任务数据就绪：TAG0025 P0-brief + .state.yaml phase=P0
- 交接单位置：`HANDOFF-TAG0025.md`（worktree 根，已 commit）
- **会话间环境交接单**：`agate-workspace/tasks/TAG0025-agateon-rename/env-rename-handoff.md`
  （改名前后环境对照表 + DSH 会话零更新论证 + 未来本地目录改名的完整清单——改名窗口前后必读）
