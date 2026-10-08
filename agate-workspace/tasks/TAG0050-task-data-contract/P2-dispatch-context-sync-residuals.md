---
phase: P2
generated_by: 主 Agent（P2 非阻塞残留同步，非标准阶段派发）
task_id: TAG0050
role: analyst
sync: P2-residuals
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令。本派发**不是**标准阶段产出，而是 P2 复评留下的 **3 项非阻塞残留同步**（`P2-review.md` §4 的 R1–R3），目的是避免 P3/P4 的输入分叉。

### 目标
按 `P2-review.md` §4 的 R1–R3，就地同步相邻文件（**不改任何 BDD 的 Given/When/Then 语义、不改设计路线**）。

### 三项（逐条）
**R1（文档同步）** — design note `docs/design-notes/design-tag0050-task-data-contract.md` 的 §3.6（约 `:471`）仍写「T4 = 现有的 PROD_TOUCHED diff 扫描，**保持原样**」、§4（约 `:495`）仍写「**T4 优先**」，与 P2 `§3.1` 新规格矛盾（`files_to_read` 把 design note 列为「实现时逐节对照」，批 C 的 P4 implementer 可能照旧文实现）。
- **处置**：在这两处**就地加醒目取代注记**（保留决策史，**不删除**原文），例如：
  > ⚠️ **[已被取代 2026-10-07]** 本处表述已过时——由 `P2-design.md §3.1` 的 F4 规格取代：`markers.yaml` 的 `PROD_TOUCHED.lead_variant` 改 `default`、pre-commit 用 `agate_markers.pattern()`、扫描面 = 任务目录内全部暂存 `*.md` 新增行、**T4 为唯一 PROD_TOUCHED 安全门**（T1 标记表去掉它）、否定写法继续阻断 + 专门指引。批 C 按 P2 §3.1 实现。

**R2（MEDIUM，cso MEDIUM-1）** — P1 `P1-requirements.md` 的 **BDD-55**（约 `:415-418`）Then 仍是旧口径「**T1 将其指向字段（不误当声明中止）**」，与新规格**方向相反**（T1 已去 `PROD_TOUCHED`；否定写法由 **T4 继续阻断**）。P3 test-designer 会据此设计"否定不阻断"的测试 → 与实现冲突。
- **处置**：改写 BDD-55 的 Then，使其与新规格一致（否定写法 `[PROD_TOUCHED]: 无` **继续阻断**，报错信息给专门指引）。**只改 Then 的判定口径，不改 Given/When 的意图**；在改动处标注 **`[BASELINE_CHANGE: P2 §3.1 F4 规格取代旧口径，经主 Agent 批准]`**（P1 基线保护要求）。
- **同时**：把 P2 `§3` note 里「P1 下次触及时同步」的清单（现仅 BDD-01/38）**显式扩到 BDD-55**。

**R3（LOW，cso LOW-1）** — cso LOW-1 的措辞「CI 能保证留痕」→「**在 required 生效时**」在 `P2-review` 声明落实，但**未出现在任何产出**。
- **处置**：在 design note §1 的边界段**补一句**「CI 能保证『这次评审留了痕』**是在 `gate-backstop` required 生效时**；未设 required 时连 SELF-GATE trailer 痕迹也不校验」。

### 约束
- **只改这三处**（design note §3.6/§4/§1 + P1 BDD-55 + P2 §3 note）；不改其它内容；不改设计路线。
- P1 是**基线**：只按 R2 改写 BDD-55 的 Then 口径 + 加 `[BASELINE_CHANGE]` 标注；不得改其它 BDD。
- 不实现任何东西。

### 输入文件
- `agate-workspace/tasks/TAG0050-task-data-contract/P2-review.md`（§4 R1–R3）
- `agate-workspace/tasks/TAG0050-task-data-contract/P2-design.md`（§3.1 F4 规格、§3 note）
- `agate-workspace/tasks/TAG0050-task-data-contract/P1-requirements.md`（BDD-55）
- `docs/design-notes/design-tag0050-task-data-contract.md`（§1/§3.6/§4）
- `{agate_root}/assets/execution-roles/analyst.md`（角色定义）

### 返回
两行：改动文件路径 + ≤30 字摘要。
</dispatch_guide>

<objective_info>
- **当前 HEAD**：`3f9af93`（分支 `feat/TAG0050-task-data-contract`）
- **任务 `.state.yaml`**：`phase: P2`
- **依据**：`P2-review.md` §4（R1 文档同步 / R2 MEDIUM=cso MEDIUM-1 / R3 LOW=cso LOW-1），§5 第 5 点「建议随本次 P2 提交或 P3 前同步相邻文件」
- **批准**：主 Agent 已批准 R2 的 P1 BDD-55 基线变更（`[BASELINE_CHANGE]`）
</objective_info>

> 注：该文件禁止包含 PASS/FAIL 预判——否则被 `check-p6-provenance.py` 审计失败。
