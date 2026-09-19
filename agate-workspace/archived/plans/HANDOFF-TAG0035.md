# TAG0035 交接单 — gate 健壮性批（RM-AG0062 归并 + RM-AG0064 并入）

> 本交接单供 worktree session 的 agent 按此启动 TAG0035 任务。
> 任务已 P0 立项（`.state.yaml` phase=P0，`P0-brief.md` 已就绪）。
> worktree 已完成构建安装与基线验证，可直接开始 P1。

---

## 1. 你要做什么

**TAG0035**：gate 健壮性批（RM-AG0062 归并 + RM-AG0064 并入）。

**一句话**：把 gate / check-script 中**会静默通过或静默失效**的判据改为**响亮失败**（fail-closed），并补齐多提交 / 回退场景下的判据假设——一个 task 内分 **4 个子批**（A/B/C/D）串行交付。

## 2. 工作区布局（双工作区纪律，违反必出事故）

| 路径 | 角色 | 纪律 |
|------|------|------|
| `/home/kity/oclab/agateon/.worktrees/agate-TAG0035` | **本任务 worktree（改造对象）** | 在这里改代码、写阶段产出、跑测试、git commit |
| `/home/kity/oclab/agateon`（主 checkout） | 协议本体 + 任务数据 + `~/.agate` 指向 | **禁止改动**。它是稳定版来源，也是 hook 的 AGATE_ROOT |
| `~/.agate`（软链 → 主 checkout/agate） | **稳定版（开发工具）** | **禁止改动**。跑 gate / 读卡片用它 |

**核心原则（AGENTS.md T001 约定沿用）**：
- **跑 gate 用 `~/.agate`**（稳定版），**改代码/跑测试在 worktree**。
- commit 时 pre-commit hook 用 `~/.agate/scripts/pre-commit-gate.sh` 判定——gate 判定对象是 worktree 里的产出文件，但 gate 工具本身是 `~/.agate`。这是有意的：改造期间工具稳定，改造对象变化。
- **⚠️ gate 工具 ≠ 检查对象（最容易搞混的点）**：
  - commit hook 的 gate **判定工具**用 `~/.agate`（稳定版）
  - 但 `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`），因为检查对象是 **worktree 里的协议文件**
  - `python3 ~/.agate/scripts/agate-summary.py` 在 worktree 里跑会显示**主 checkout 的上下文**，不代表 worktree 状态——worktree 状态用 `git log`/`git status` 看
  - **所有编排/派发类工具脚本**（`agate-inject-card.py`、`agate-render-dispatch-prompt.py`、`agate-next-card.py` 等）都用 `~/.agate/scripts/` 稳定版调用（TAG0016 教训：用 worktree 相对路径调用会读到正在被修改的协议卡片副本，把未发布机制注入任务）
- **hook 在共享 git 目录**：worktree 的 `.git` 是文件（指向主 checkout `.git`），hook 实际在主 checkout 的 `.git/hooks/`（三个 hook 已软链到 `~/.agate/scripts/`）。worktree commit 时自动触发。

**已完成的 setup（worktree 已可独立使用）**：
- 依赖齐全：bash 5.2.21 / python 3.12.3 / pytest 9.0.3 / pyyaml / shellcheck 0.9.0 / ruff 0.16.4（`~/.venvs/agate-dev/bin/ruff`）
- 基线验证：unit/regression/integration 分片 pytest + consistency 0 ERROR（`--strict-errors-only`；DEBT0012 教训：存量 300+ WARNING 下 `--strict` 会误导判 exit 2）
- commit hook：指向 `~/.agate`（稳定版）
- 工作区解析：`agate_common.py` 输出 worktree 自己的 `agate-workspace/`
- 任务数据：TAG0035 P0-brief + `.state.yaml` phase=P0

## 3. 任务范围（P0-brief 已锁定，P1 细化 BDD）

### 已核实并确认的缺陷（全部有代码证据；详见 `P0-brief.md`）

**子批 A — gate 对未知阶段 fail-open（RM-AG0064）**：
- `check-gate.py:1487-1489`：`handlers.get(phase)` 为 `None` → `sys.exit(2)`，而 **exit 2 = P0/P1/P2/P3/P5/P6/P8 的通过码**
- **实测**：`python3 agate/scripts/check-gate.py P99 <task_dir>` → `exit=2`（与真实阶段 P8 相同）
- **后果链**：`exit 2` → `pre-commit-gate.py:354` 记录 `write_gate_result(exit=2)` → `ci-gate-backstop.py:209-211` 比对「记录值 == CI 重跑值」（两者都是 2）→ **PASS**。**CI 验证的是一致性，不是正确性**
- **修复**：未知阶段 → **exit 1** + regression 测试

**子批 B — 三处数字序号假设致非数字阶段名静默失效**：
| 位置 | 形态 | 失效方式 |
|------|------|---------|
| `check-gate.py:1465-1466` | `re.search(r"[0-9]+", ...)` | 回退检测恒不触发（短路） |
| `check-state-transition.py:212-215` | `phase_num()` 无匹配 `return 0` | 非数字阶段名全映射为 0 → 转移判定错乱 |
| `pre-commit-gate.py:82,192-195` | `_P_NUM_RE = re.compile(r"P[0-8]")`（**大小写敏感**） | 无匹配返回 `None`；调用点 `577 if not out_phase: continue` 静默跳过 |

- **⚠ 修复方案须与 out-of-scope 一致**：建议采用**最小案**（非数字阶段名**显式报错**，纯判据修复，**不碰 `phases.yaml` 语义**）。完整案（`phases.yaml` 加 `order:`/`predecessors:`，需解 `additionalProperties: false`）实质是**阶段语义声明式化**，与本批 out-of-scope「不做 phase 语义重构」冲突 → **完整案另作独立议题**（见分析报告 §5.4）

**子批 C — DEBT0037（`_gate_p4` 完整度判据）**：
- `_gate_p4` 判据「暂存区含非 md/yaml 代码文件」在两种场景 `return 1`：① 一个 phase 跨多个 commit ② P5→P4 回退后修复 commit。`agate-next.py` 据此拒绝推进 → 主 Agent 手动 `_advance`（TAG0033 两次实证）
- **精确范围（独立评审修正）**：`check-gate.py:951-961` 仅在 `git diff --cached --name-only` **无任何**非 md/yaml 文件时 `return 1`。本批子批 A/B/D 各含 `.py` 改动 → **每个 commit 都不会命中**；**只有纯 md/yaml 的 commit 才命中**
- **修复方向**：判据放宽为「本 phase 任一 commit 引入过代码 diff」（`git log` 扫 phase 起点..HEAD），或显式识别「回退后再推进」（`.state.yaml` `retries[P4]` 非空 + 已有 `wf(TAG0035-P4)` commit）

**子批 D — DEBT0038（`check-judge-verdict.py` 信息隔离黑白名单 3 处假阳性）**：
| # | 问题 | 落点 |
|---|------|------|
| ① | 黑名单 `p6-acceptance.md` 子串命中 `agate/phase-cards/P6-acceptance.md`（阶段规格卡片，非 verifier 自述） | `_check_blacklist`（需路径豁免） |
| ② | 白名单不含角色定义文件路径（与通用惯例冲突） | `_check_whitelist` + `dispatch-protocol.md`「Judge 信息隔离」节 + P6 卡 |
| ③ | `P6-evidence/` 目录白名单不认目录下裸文件名 | `_check_whitelist` |

> **⚠ 范围修正（独立评审）**：原 D 含 DEBT0040/DEBT0041，**已移出**——DEBT0040 含 CI workflow 改动（AGENTS.md 规则 5 需用户许可）；DEBT0041 与 gate 健壮性仅名义相关，且与 TAG0036 读同一字段族。

### 核心约束（不可违反）

1. **Linux 现状是基线**——现有 pytest 测试全绿是回归底线，每个修复都必须保持全绿
2. **Windows 兼容是增量**——本环境（Linux）无法实测 Windows，靠静态修复 + Linux 回归 + CI matrix 兜底。**不要宣称"已实测 Windows"**
3. **不破坏已有协议语义**——本批只修**判据健壮性**，**不重写 gate 逻辑**；`handlers` 字典的声明式化（10 个手写 `gate_pN` 改 YAML 驱动）属**独立议题**，不在本批
4. **范围锁定**——若 P1 分析发现需改动超出 P0-brief 锁定范围，**须先停下跟用户确认**
5. **DEBT0040/DEBT0041 不在本批**——若发现相关缺陷，登记 DEBT，不在本批修

## 4. 关键验证命令

```bash
# 在 worktree 根执行：

# 全量测试（分片跑，每片 timeout + -n auto）
timeout 280 python3 -m pytest agate/tests/unit/ -q -n auto
timeout 280 python3 -m pytest agate/tests/regression/ -q -n auto
timeout 280 python3 -m pytest agate/tests/integration/ -q -n auto

# 一致性（0 ERROR 才行；必须用 worktree 自己的脚本）
timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only

# shellcheck
timeout 60 shellcheck -S warning agate/scripts/*.sh

# 测试计数（验证文档没漂移）
timeout 60 bash agate/tests/scripts/count-tests.sh

# 单脚本测试（改哪个跑哪个，TDD 先红后绿）
timeout 60 python3 -m pytest agate/tests/unit/test_check_gate.py -q

# 子批 A 的验证锚（修复后应为 exit 1）
timeout 30 python3 agate/scripts/check-gate.py P99 agate-workspace/tasks/TAG0035-gate-robustness; echo "exit=$?"
```

## 5. 阶段推进纪律（T001 血泪教训）

- **commit 时 phase = 本 commit 产出阶段**：P1 产出 → phase=P1 再 commit；推进 P2 随 P2 产出同 commit。**不要**先写 phase=P2 再 commit P1 产出（pre-commit 会用 P2 gate 检查，P2-design.md 不存在 → 拦截）
- **改脚本走 TDD**：先写失败测试确认红 → 改脚本确认绿
- **批量机械改动的 TDD 策略**：先写一个"grep 断言审计"测试作为回归拦截；批量改动后跑该断言 + 全量 pytest 确认绿。不要为每个小改动单独写测试，也不要跳过测试直接改
- **git 命令加 timeout**、单步串行（AGENTS.md 工具纪律）
- **commit message 含 `wf(TAG0035-P{阶段}):` 前缀**
- **⚠ 本批全部改动都触发 SELF-GATE**：`agate/scripts/*.py`（脚本）+ `agate/rules/*.yaml`（如采用完整案改 phases.yaml）+ `agate/*.md`（如改 `dispatch-protocol.md` / P6 卡）→ commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；且须跑 `check-protocol-consistency.py` 确认 0 ERROR
- **⚠ DEBT0037 自指提醒**：本批 4 个子批各含 `.py` 改动 → 每 commit 都会含代码文件，**不会**命中 `_gate_p4` 的「暂存区无代码文件」判据。但若某子批只改文档（纯 md），会命中——拆批时确保每 commit 含至少一个代码文件

## 6. 任务编号与状态

- 任务目录：`agate-workspace/tasks/TAG0035-gate-robustness/`（worktree 内）
- `.state.yaml`：phase=P0（P1 开始后推进）
- `active-tasks.md`「待开始」已有 TAG0035 行
- roadmap：**RM-AG0062**（已 `scheduled`，标题「gate 健壮性批」）关联本任务；**RM-AG0064** 已 `cancelled` 并注明并入 RM-AG0062
- **编号体系**：任务用 `TAG0035`（校验器 `^T[A-Z]{2}\d+$`）

## 7. 已知风险与止损

| 风险 | 止损 |
|------|------|
| **多提交阶段任务的自指风险** | `_gate_p4` 仅在暂存区**无任何**非 md/yaml 文件时 `return 1`（`check-gate.py:951-961`）。本批 3 个子批含 `.py` → 不命中；**纯文档 commit 才命中**。拆批时确保每 commit 含代码文件 |
| **`phases.yaml` schema 变更的破坏性** | `additionalProperties: false`（`phases.schema.json:87/94/98`）→ 加 `order`/`predecessors` 必须改 schema。**建议采用最小案避免此风险**；若走完整案，须保证默认值 = 现状行为 |
| **判据放宽（子批 C）削弱 gate 拦截力** | 需明确"放宽后仍能拦住什么"的边界，并在 P3 设计对应红灯用例 |
| **DEBT0038 白名单放宽（子批 D）可能削弱 judge 信息隔离** | 放宽须精确到路径（如角色文件精确路径），**不得**用宽泛通配；加固后须验证"仍能拦住 P6-acceptance.md 自述" |
| **子批 D 与 TAG0036 的文件面** | DEBT0041 已移出（它与 TAG0036 读同一字段族）；若 P1 发现子批 D 仍与 TAG0036 冲突，须停下确认 |

## 8. 完成后

- P8 gate + READY → 提 PR 合并 main（**PR 普通 merge 非 squash**，tag 要求）
- **合并前在 PR 里看 CI 结果**——pytest / shellcheck / consistency / gate-backstop 全绿才算过
- roadmap RM-AG0062 回写 → `done`（P8 gate 硬校验 RM-AG0043）
- DEBT 回写：DEBT0037 / DEBT0038 置 `closed`，`task_id` 填 TAG0035；**DEBT0040 / DEBT0041 不在本批**（保持 `open`）
- 复盘按 agate 自身变更流程归档（合并后在主 checkout 写复盘 + 更新 roadmap/版本）

## 9. 交接确认

- worktree 基线全绿：unit + regression + integration pytest 全绿 + consistency 0 ERROR（`--strict-errors-only`）
- hooks 就位（指向 `~/.agate` 稳定版）、依赖齐全（bash/python/pyyaml/pytest/shellcheck/ruff）
- 任务数据就绪：TAG0035 P0-brief + `.state.yaml` phase=P0
- 交接单位置：`HANDOFF-TAG0035.md`（worktree 根，已 commit）

---

> **启动入口提醒**：orchestrator 默认读 `active-tasks.md` + `.state.yaml`，**不会自动读 HANDOFF**。新 session 首条指令请显式写「**读 worktree 根 `HANDOFF-TAG0035.md`**」。
