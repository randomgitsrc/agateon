---
phase: P8
task_id: TAG0033
type: release
parent: P7-consistency.md
trace_id: TAG0033-P8-20260909
status: draft
created: '2026-09-09'
agent: implementer
bump_type: minor
debt_check: reviewed
---

# P8-release.md — TAG0033 Codex 命令流适配器 + 平台接入 发布准备声明

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` /
> `git tag`**——这些由主 Agent 在 P8 gate 验证通过后亲自执行。本轮已实际编辑 `CHANGELOG.md` /
> `README.md` / `README.zh-CN.md` / `agate/UPGRADING.md` §3 / `agate-workspace/roadmap/roadmap.md` /
> `agate-workspace/debt/tech-debt.md` 六个发布面文件（P8 产出的一部分，非"留给主 Agent"）。
> 状态标记 `[PROD_NOT_TOUCHED]`。

## 1. 前置条件核对（P7-consistency.md）

- `P7-consistency.md`（TAG0033-P7）结论：**通过**，`blocker_count: 0` / `deviation_critical_count: 0` /
  `deviation_count: 1`（`platform-notes.md` V7 措辞滞后，WARNING 级，非阻塞）/ `design_gap_count: 0` /
  CODE-MAP `[CODE_MAP_SYNC]`。
- packages 一致性：`P1 frontmatter` == `P2 frontmatter` == `[agate-scripts, agate-docs, agate-tests]`
  （agateon 单一版本号仓库，三包为任务改动分域，整体 bump 一次）。
- 上游链路：P1 30 BDD → P6 30/30 PASS（F1 修复后重做，`49d3353`）→ P6.5 judge 30/30 passed
  （`f484895`）→ P7 通过。P5 r3 技术验证 `5f704a0`。
- 结论：具备进入 P8 发布阶段的一致性前提，**前置条件已满足**。

## 2. bump_type 判断依据

**bump_type: minor（v0.69.0 → v0.70.0）**

依据：

1. **纯增量新增功能**：`agate-cmdstream-adapters.py` 新增 `CodexAdapter`（`ADAPTERS` 注册表键
   `"codex"`），是 RM-AG0055 §3.4.4 预留「未来接新平台只写一个适配器」扩展点的落地
   （`+252 insertions / 0 deletions`）。
2. **无破坏性变更**（P7 §3.4 `git diff` 复核）：`agate-cmdstream-detect.py` / `agate-cmdstream-ir.py`
   diff 完全为空——检测引擎 / 阈值常量（RM-AG0055 §3.4.3）/ `CommandRecord` 十字段 dataclass /
   既有三平台适配器（`ClaudeCodeAdapter` / `OpenCodeAdapter` / `DSHAdapter`）class 体零改动。
3. **F1 修复（DEBT0035）不降级版本决策**：F1 修的是本任务内新增的 `CodexAdapter` pending 判据，
   不改公共 API 行为、不触及既有平台；属本版本内部收敛，随 minor 一并发布。
4. **文档 / 平台接入为纯新增**：`platform-notes.md` Codex 章、`SETUP.md`「步骤 2-Codex」小节
   均为新增章节，不改既有平台文档语义。
5. 当前发布版 **v0.69.0**（`git describe --tags --abbrev=0` 已核）→ 目标 **v0.70.0**。

## 3. 版本号变更逐文件打勾表（比照 TAG0032 P8-release §4）

| 位置 | 文件 | 变更 | 本轮状态 |
|---|---|---|---|
| README badge（EN） | `README.md` L12 | `version-v0.69.0` → `version-v0.70.0` | ✅ 已改（`grep -c version-v0.70.0` → 1；旧值残留 0） |
| README badge（ZH） | `README.zh-CN.md` L12 | `version-v0.69.0` → `version-v0.70.0` | ✅ 已改（`grep -c version-v0.70.0` → 1；旧值残留 0） |
| CHANGELOG | `CHANGELOG.md` | 顶部新增 `## [0.70.0] - 2026-09-09` 节（顶部无 `[Unreleased]` 节，直接新增，格式对齐 `## [0.69.0]`） | ✅ 已改（`grep -c "^## \[0.70.0\]"` → 1） |
| UPGRADING §3 | `agate/UPGRADING.md` | §3「已知破坏性变更（按版本）」新增 `### v0.70.0 — Codex 命令流适配器 + 平台接入（TAG0033：RM-AG0061 + DEBT0035）` 章节（对齐 `### v0.69.0` 格式；CHECK 13 CHANGELOG 最新版 ↔ UPGRADING §3 章节一致） | ✅ 已改（`grep -c "### v0.70.0"` → 1） |
| roadmap 回写 | `agate-workspace/roadmap/roadmap.md` | RM-AG0061「状态」列 `scheduled` → `done`；「更新」列 `2026-09-08` → `2026-09-09`（RM-AG0043 P8 gate 硬校验） | ✅ 已改（`grep -nE "RM-AG0061.*done"` 命中 L69） |
| tech-debt | `agate-workspace/debt/tech-debt.md` | DEBT0035 `in_progress` → `closed`（+3 evidence ref + `closed_at`）；新增 DEBT0036 | ✅ 已改（`check-debt.py` exit 0） |

> **git tag `v0.70.0` 由主 Agent 在 gate 验证通过后创建**。tag 创建前，
> `check-protocol-consistency.py` CHECK 7（README badge ↔ 最新 git tag）必然报
> `badge v0.70.0 != tag v0.69.0` ERROR——属"发布完成态"校验的设计使然（DEBT0013 时序注意），
> 非回归；主 Agent 在 tag 后重跑即 0 ERROR。releaser 本轮只确认 CHECK 13 通过。

## 4. CHANGELOG `[0.70.0]` 节内容（本轮已写入 CHANGELOG.md 本体，此处副本供 gate / 评审对照）

```markdown
## [0.70.0] - 2026-09-09

### 新增（TAG0033：Codex 命令流适配器 + 平台接入，RM-AG0061 + DEBT0035）

- **`agate-cmdstream-adapters.py` 新增 `CodexAdapter`**（`ADAPTERS` 注册表键 `"codex"`）——
  RM-AG0055 命令流机制新增 Codex 平台适配器，subagent 存活/卡死检测（调用冻结 / 活动冻结 /
  逻辑空转）覆盖 Codex：把 `~/.codex/sessions/**/rollout-*.jsonl`（含 `spawn_agent` 子会话的
  独立 rollout 文件）解析为统一 `CommandRecord` IR；实现 `probe` / `list_sessions` /
  `read_commands` 三方法。**检测引擎 / 阈值（RM-AG0055 §3.4.3）/ `CommandRecord` IR / 既有三
  平台适配器（Claude Code / OpenCode / DSH）零改动**——兑现 RM-AG0055 §3.4.4「未来接新平台
  只写一个适配器、检测引擎零改动」扩展点（`agate-cmdstream-adapters.py` +252 insertions / 0
  deletions）。
- **`agate/platform-notes.md` Codex 章**从「待补充」占位补为完整能力矩阵：非交互 `codex exec` /
  `-m`/`--model` 与 `-c model_reasoning_effort` 推理档 / 权限绕过 `--dangerously-bypass-approvals-and-sandbox`
  与中间档 `-s <read-only|workspace-write|danger-full-access>` / `spawn_agent` 原生子派发 /
  `--json` 结构化输出 / `resume`；退出码不可靠须解析 `--json`；model 阵容随账号类型变
  （ChatGPT 账号默认 model、`spawn_agent` model 枚举）；`multi_agent` feature flag。附实机
  验证记录（codex-cli **0.153.4** + ChatGPT 登录，2026-09）。
- **`agate/SETUP.md` 新增「步骤 2-Codex」接入小节**：`npm i -g @openai/codex` + `codex login`
  （ChatGPT vs API key 影响可用 model）+ 自动化环境绕过 flag + `codex features list` /
  `codex exec --json` 冒烟验证。
- 关联：RM-AG0061（RM-AG0055 §3.4.4 预留扩展点落地 + RM-AG0060 派发路由 epic 的 b 块前置）、
  DEBT0035（本版本关闭，见「修复」）。

### 修复

- **`CodexAdapter` pending 判据收紧（F1 / DEBT0035，P5→P4 回退修复）**：pending 判据从
  `item.status != "completed"` 收紧为「无终态信号才算 pending」——新增模块级 helper
  `_codex_is_finished(payload, item)`：已结束 = `status ∈ {"completed","failed"}` ∪
  `payload.completed_at_ms` 非 None ∪ `item.exit_code` 是 int 非 bool（三者任一）。修复真机
  Codex 把「已结束但非 0 退出」的命令记为 `status:"failed"`（携带完整 `exit_code` /
  `completed_at_ms`）时被旧口径误判为 pending、丢弃真实 `exit_code` / `output_hash`，导致
  `agate-cmdstream-detect.py` 对真机重复失败会话判不出 SPIN 的缺陷。
```

## 5. roadmap 回写确认（RM-AG0061 → done）

- `agate-workspace/roadmap/roadmap.md` L69 RM-AG0061 行：
  - 「状态」列：`scheduled` → **`done`** ✅（RM-AG0043 P8 gate 硬校验：按 `task_id` 反查「关联任务」
    列 = `TAG0033`，须回写 `done` 否则阻断）
  - 「更新」列：`2026-09-08` → **`2026-09-09`** ✅（「创建」列 `2026-09-08` 保持不变）
- 自查：`grep -nE "RM-AG0061.*done" agate-workspace/roadmap/roadmap.md` → 命中 L69。

## 6. debt_check（reviewed）——条目 id 清单

**debt_check: reviewed**。已读取 `agate-workspace/debt/tech-debt.md` 全簿，本任务相关条目：

| DEBT id | 标题（摘） | 本轮动作 | status |
|---|---|---|---|
| DEBT0035 | `CodexAdapter` pending 判据误判真机 `status=="failed"` 终态为 pending（P5→P4 回退，TAG0033） | **本任务关闭**：`status: in_progress` → `closed`；`evidence` 追加 `ref: 5f704a0`（P5 r3 重验）/ `ref: 49d3353`（P6 重做 30/30）/ `ref: f484895`（P6.5 judge passed）+ P7 §6-B 锚点；补 `closed_at: 2026-09-09`。P7 §6-B 已核 5 条 `closure_criteria` 5/5 全满足。 | `closed` |
| DEBT0036 | `platform-notes.md` Codex 章「`spawn_agent` 嵌套深度未测 / `max_depth=1` 待 V7 复核」措辞滞后——P6 V7 已两次实测 `depth=2` 可用 | **本任务新登记，未在本任务关闭**（P7 §6-A deviation_count=1 的 fallback (b) 路由）：`source: retrospective` / `priority: low` / `status: open` / `task_id: null`。`impact` = 权威源携带指向已实测事实的「未测」指针，误导读者；不影响 `CodexAdapter` 契约或 BDD-25（现「待复核」时效指针本身合规）。`recommendation` = 收敛为「已实测 depth=2 可用」，保留 `max_depth=1` 事实行 + 交叉引用结构，回跑 `test_bdd_25` + `check-protocol-consistency.py --strict-errors-only`。 | `open` |
| DEBT0034（存量） | TAG0032 三步 legacy 软链迁移文案双写 | 与本任务无关，不动 | `open` |
| 其余存量债务 | — | 与本任务无关 | — |

- `timeout 60s python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **exit 0**。

## 7. 临时资源清单（releaser → 主 Agent 交接）

核对本任务 P0-P8 全程启动的临时服务 / 进程 / 数据 / 开发安装：

- **启动的临时服务 / 进程**：无。无 debug server / 无临时 daemon / 无占用端口。
- **临时数据库**：无。
- **开发安装**：无。本任务用系统 `python3` + 既有 `~/.venvs/agate-dev/bin/ruff`（未新装 editable
  install / 全局包 / pip install）；`codex-cli 0.153.4` 是 P0-brief `env_constraints` 声明的**既有**
  本机环境（ChatGPT 登录），非本任务安装。
- **真机验证派生产物（只读观察，非 agate 生产环境残留，主 Agent 无需清理）**：
  - 本任务 P1 spike / P5 真机验证 V1-V7 / P6 真机重做多次跑 `codex exec`（codex-cli 0.153.4 +
    ChatGPT 登录），在 **`~/.codex/sessions/2026/09/{08,09}/`** 下生成了若干测试子会话 rollout
    文件（`rollout-*.jsonl`，含 `spawn_agent` 子会话独立文件，如
    `rollout-2026-09-09T11-29-48-01a08436-...jsonl` 等）。
  - 这些是 **Codex CLI 的正常产物**（Codex 自身的会话记录目录），**非 agate 生产环境残留**——
    `~/.agate` 与 worktree git 树**未被污染**（git status 仅本任务产出文件 + `gate-events.jsonl`
    台账追加）。仅作只读观察对象（`read_commands` fixture 取样 + `detect` 三态验证），主 Agent
    **无需清理** `~/.codex/sessions/` 会话文件。
- **状态标记**：`[PROD_NOT_TOUCHED]`。

## 8. 自检（非 gate）

- `bump_type: minor` / `debt_check: reviewed` frontmatter 字段存在：✅
- `grep -c "^## \[0.70.0\]" CHANGELOG.md` → **1** ✅
- `grep -c "version-v0.70.0" README.md` → 1；`README.zh-CN.md` → 1（合计 **2**）✅；旧 `version-v0.69.0` 残留 **0** ✅
- `grep -c "### v0.70.0" agate/UPGRADING.md` → **1** ✅
- `grep -nE "RM-AG0061.*done" agate-workspace/roadmap/roadmap.md` → 命中 L69 ✅
- `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **exit 0** ✅
- 未执行 `git add` / `git commit` / `git tag` / `bump-version`（留主 Agent）：✅
- 未改 `agate/scripts/*.py` / `agate/tests/` / `agate/platform-notes.md` 正文 / `agate/SETUP.md` 正文
  （V7 措辞收敛走 DEBT0036 后续）/ P1-P7 基线：✅
- `[SCOPE+]`：**无**。
- `[PROD_NOT_TOUCHED]`。

## 9. 主 Agent 待办（P8 gate 通过后亲自执行，releaser 不做）

1. `check-gate.py P8 $TASK_DIR`（bump_type + debt_check 字段 + 暂存区 version 文件 + 暂存区 CHANGELOG
   + roadmap RM-AG0061 → done）。
2. `bump-version` → `v0.70.0` + `git commit` + `git tag v0.70.0`（同一 commit）。
3. P5 验证：先 `check-p6-provenance.py --audit7-only`；`reuse_allowed` → 复用 `P5-test-results/`；
   否则完整重跑 `gate_commands.P5`。**CHECK 7（badge ↔ tag）须安排在 tag 创建之后**（DEBT0013）。
4. `git log v0.69.0..HEAD --oneline` 对照 CHANGELOG 无遗漏。
5. READY 收尾检查（临时资源清单见 §7——无 debug server / 无临时 DB / 无开发安装；`~/.codex/sessions/`
   会话文件无需清理）。
