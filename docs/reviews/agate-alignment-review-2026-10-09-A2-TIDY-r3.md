---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A2 收尾 r3 复核——只验 r2 的 A3（落点无效）+ 3 项非阻断残留（dispatch-prompt 围栏内补写类工具条 + 角色文件改指针 + RM-AG0087 标题张力说明 + CHANGELOG 同步）
files_changed: [CHANGELOG.md, agate-workspace/roadmap/roadmap.md, agate/assets/review-roles/protocol-alignment-review.md, agate/assets/templates/dispatch-prompt.md, agate/tests/unit/test_tag0050_proxy_judgment.py]
branch: hotfix/batch-a2-tidy（未提交，改动在工作区）
r1_report: docs/reviews/agate-alignment-review-2026-10-09-A2-TIDY.md
r2_report: docs/reviews/agate-alignment-review-2026-10-09-A2-TIDY-r2.md
---

# 协议-脚本对齐审查（批 A2 收尾 / A2-TIDY r3 复核）

## 结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（r2 的 MISALIGNED 已修，落点实测生效） |
| A4 | 测试覆盖 | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空清单，见下） |
| A5 | 下游影响 + 文档传播 | ALIGNED（2 项残留经明示后可接受，见下） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**是否可 commit：可以。** r2 的唯一实质阻断（A3 落点无效）**已修并经实测确认生效**；3 项非阻断残留均已被恰当处理（标题张力已加说明、CHANGELOG 已同步；另 2 项我明示为**可接受残留**）。无 MISALIGNED、无未确认的 NEEDS_HUMAN_REVIEW。

---

## 请验证的 5 项

### 1. 4 项改正是否真修 —— 全部为真

| 项 | 证据 | 结论 |
|---|---|---|
| A3：删栏外追加 + 围栏内补条 | `dispatch-prompt.md` 围栏（`### Review 角色特别指令` 开 `:108` / 闭 `:135`）**内**新增 bullet `:120-124`「**写类工具一律不得对真实仓库运行**：`agate-inject-card.py`（改写 dispatch-context 文件）/ `agate-md-field-set.py` / `agate-state-set.py` / `agate-task-init.py` 等会**改写任务文件**——要验证就 `cp -r` 到一次性副本、`AGATE_ROOT` 指向副本，跑完核验真实仓库 `git status --porcelain` 与开跑前一致（2026-10-09 实证…47 个…）」 | ✓ 在围栏内 |
| A3：角色文件改指针 | `protocol-alignment-review.md:111-117` 由「正文节」改为 `## 只读纪律（指向单源）`：一句 gist + 指向 `dispatch-prompt.md` 的 Review 角色围栏内「只读纪律（强制…RM-AG0081）」块 + 「本文件不重复正文」 | ✓ 指针 |
| 残留②：RM-AG0087 标题张力 | `roadmap.md:87` 注末新增：「⚠️ **标题里的「（DEBT0031）」**系登记时把两者当作同一缺陷；2026-10-09 复核确认**机制不同**（本条=硬检 ERROR；DEBT0031=对账 WARNING），故标题保留为历史指针、实质结论以本条注为准」 | ✓ |
| 残留③：CHANGELOG 同步 | `CHANGELOG.md:122-129` 条目改为「③ 只读纪律补「写类工具」条——`dispatch-prompt.md` 的「Review 角色特别指令」**围栏内**（RM-AG0081 只读块）新增一条…；`protocol-alignment-review.md` 改为**指向该单源**（不重复正文）」 | ✓ |

### 2. 落点是否生效 —— 实测**生效**（含方法学更正）

**渲染实测**（`agate-render-dispatch-prompt.py P4 protocol-alignment-review <task>`）：
```
AGATE_ROOT=/home/kity/oclab/agateon/agate → 渲染产物：
  写类 count: 1        （:111「- **写类工具一律不得对真实仓库运行**：…」）
  agate-inject-card count: 2   （:111、:114）
  RM-AG0081 count: 2
```
即：围栏内那条**确实进了评审 subagent 的渲染产物** ✓。

> ⚠️ **方法学更正（对 r2 的自我更正）**：渲染器 `_resolve_agate_root()`（`agate-render-dispatch-prompt.py:96-105`）走 `agate_common.resolve_agate_root`（**env → 项目声明 → current 链 → 脚本上溯**）。**不设 `AGATE_ROOT` 时它自解析到稳定版 `~/.agate/v0.80.2/agate`**（本次实测：产物中角色文件路径即稳定版），故 **r2 的渲染实测读的是稳定树**（其本无该未提交改动）⇒ 该佐证**无效**。但 r2 的**结论**（栏外 blockquote 不被注入）系据渲染器代码（`main_block` 只取 `## 阶段特定提示` 之前的首块 + `review_appendix` 只取 `### Review 角色特别指令` 节）得出，**仍成立**；r3 用 `AGATE_ROOT=repo/agate` 复验了落点。**本批的正确定性来自此正确方式。**

### 3. 单源是否唯一 —— **唯一**

- `grep -rn "写类工具一律不得对真实仓库运行" --include=*.md`（排除 .worktrees/docs/reviews）→ **仅 `agate/assets/templates/dispatch-prompt.md:120` 一处** ✓
- `protocol-alignment-review.md` **只做指针**（一句 gist + 指向模板），**不重复正文** ✓

### 4. `test_tag0005_bdd_9` 是否通过 —— **通过**

```
python3 -m pytest agate/tests/unit/test_check_gate.py::test_tag0005_bdd_9_review_role_instruction_single_file -q
→ 1 passed
```
`grep -rl "Review 角色特别指令" agate/ --include=*.md` → **仅 `agate/assets/templates/dispatch-prompt.md` 单文件** ✓（角色文件已用「**Review 角色**指令」措辞规避，未照抄字面串）。

### 5. A4b + A8 —— 见下（**非全绿**）

---

## 逐项审查（简）

### A3: 一致性连锁 + 反向传播 —— ALIGNED

r2 的 MISALIGNED（追加落在注入围栏外 ⇒ 不生效 + 重复）**已修**：规则现**在 `### Review 角色特别指令` 围栏内**（`:120-124`），实测**进入**渲染产物；角色文件改为指针，**消除重复**。`SG.9d`（只读纪律须在围栏内）语义与新增 bullet 相容（同块内）。

### A4 / A4b —— ALIGNED

- A4：本批测试改动仅 BDD-70（r2 已验判别力），未新增逻辑 ⇒ 无需新测试；BDD-70 仍绿。
- **A4b 空清单（显式写出）**：**无既有用例因本批转红；无需更新夹具**。全量 pytest：

```
1 failed, 2909 passed, 2 skipped, 1 rerun in 125.68s (0:02:05)
```
  唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，**环境性**（本机 opencode 子命令 `debug agents` vs 测试调 `debug agent`），该文件未被本批改动，**与 r1/r2 同一环境性失败**。⚠️ **不可称「全绿」**。

### A5: 下游影响 + 文档传播 —— ALIGNED（2 项残留经明示可接受）

- **CHANGELOG 已标注** ✓，且已同步为「围栏内补条 + 角色文件改指针」口径。
- **残留（我明示处置，非阻断）**：
  1. **CHANGELOG 条目仍在 `### 修复` 节**（内容为登记/治理）——**判定：可接受**。此为本批一贯口径（相邻 RM-AG0113 条目同样在 `### 修复`），属风格取舍，不值得单独返工。
  2. **写类工具 bullet 无机械守护**（`grep -rn "写类工具\|不得对真实仓库运行" agate/tests/` → **0 命中**；`SG.9d` 只断「只读/checkout」）——**判定：建议补，但不阻断本批**。理由：该 bullet 是评审角色的**新增规范**，删掉它 `SG.9d` 仍绿（静默消失），与既有「为 RM-AG0081 只读纪律加 `SG.9b/9d` 守护」的惯例不一致；**建议**后续补一条 `SG.9e`（断言 `写类工具一律不得对真实仓库运行` 在围栏内）。但本批为 hotfix 登记小修，**不必**在此批落地——若不加，请登记一条跟进项（RM/DEBT）。
- 破坏性变更：无。

### A6 / A7 —— ALIGNED

- A6：无新增协议规则/脚本行为 ⇒ 无需更新 CHECK 9 锚点；consistency **0 ERROR**；改动文件未产生新 WARNING。
- A7：登记/治理 + 文档/测试新增，无架构决策，无需新 ADR；与 ADR-014 无冲突。

### A8: 声称-命令绑定 —— ALIGNED

| 声称 | 命令 | 结论 |
|---|---|---|
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py`（+ `--strict-errors-only`） | **复现**：`仅有 432 个 WARNING，无 ERROR`；strict rc=0 ✓ |
| `2909 passed`（**非全绿**） | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **复现**：`1 failed, 2909 passed, 2 skipped, 1 rerun`（1 failed 环境性）✓ |
| `roadmap 0 异常` | `python3 -c "…列数≠9 的 \|RM- 行…"` | **复现**：`rows 111 malformed 0` ✓ |
| `ruff All passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（0.16.4） | **复现**：`All checks passed!` ✓ |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **复现**：rc=0 ✓ |
| 「围栏内补条 ⇒ 生效」 | 渲染实测（`AGATE_ROOT=repo/agate`） | **复现**：`写类 count: 1` ✓ |
| 「单源唯一」 | `grep -rn "写类工具一律不得对真实仓库运行"` | **复现**：仅模板 1 处 ✓ |

---

## 一处小疵（非阻断，供顺手修）

角色文件指针 `:117` 注称该围栏标题字面串「**全仓**仅允许出现于模板一处」——实际 `test_tag0005_bdd_9` 只扫 **`agate/` 协议目录**（`agate_root.rglob("*.md")`）；`CHANGELOG.md`（仓库根）**含该串 3 处**（`:127`/`:711`/`:1829`，其中 `:127` 为本批条目）**不被计**。故「全仓」措辞**略宽于**实际判据。建议改为「`agate/` 协议目录内仅允许出现于模板一处」。**不影响 commit**（测试实跑通过）。

---

## 审查过程说明（只读纪律）

- 本审查**只读代码、只写本报告与留痕文件**，未改任何协议/脚本/测试，未 commit/push。
- **所有写类/实验操作均在 `/tmp/opencode` 副本上跑**（`r3probe` / `r3probe2`：`init_task` 夹具 + 渲染器输出写入副本任务目录）；未对真实任务运行 `agate-inject-card.py` 等写工具。
- 跑测试/脚本前后 `git status --porcelain` 一致——收尾仅 5 个被审文件 + r1/r2/r3 报告与留痕。
