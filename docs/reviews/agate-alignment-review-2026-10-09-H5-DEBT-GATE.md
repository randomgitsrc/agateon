---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "RM-AG0088 / DEBT0033——把 check-debt.py 挂入 pre-commit gate（新 2l 步），并把 closed 条目判据由 evidence 含 P[56] 子串改为含 task_id + closed_at"
files_changed:
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/agate-debt-check.py
  - agate/tests/unit/test_agate_debt_check.py
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
---

# 协议-脚本对齐审查

> **一句话结论**：closed 判据替换（P[56] → `closed_at`）方向正确、存量全通过；但**挂载点放错位置**——新 2l 步嵌在「遍历暂存 `.state.yaml`」的循环体内，且位于 PAUSED/READY/DONE 的 `continue` 之后 ⇒ **`tech-debt.md` 单独暂存（含本批自身的 hotfix 通道）时该步根本不执行**，实测「非法 tech-debt.md → commit 不阻断」。本批**不可按现状 commit**。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | **MISALIGNED** |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（1 处计数需更正：47→48） |

**结论分布**：6 MISALIGNED / 1 ALIGNED / 1 ALIGNED（A8 全部复现，仅一处计数更正）。**无 NEEDS_HUMAN_REVIEW**。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/assets/templates/tech-debt-template.md:41`）：
> `| closed | 已关闭 | **必须**含 task_id + evidence 同时引用该 task_id 与 P5/P6 证据（否则 schema 拦截） |`

**文档声明**（`CHANGELOG.md:57`）：
> 新增 2l 步——`tech-debt.md` 被**暂存**时跑 `check-debt.py <file>`，exit 1 → 阻断 commit

**脚本实现**（`agate/scripts/agate-debt-check.py:157-174`）：closed 分支改为 `task_id` + `closed_at`（不再查 `P[56]`）。
**脚本实现**（`agate/scripts/pre-commit-gate.py:990-1002`）：新步嵌在 `for state_file in state_files:`（:726）循环体内。

**结论**：**MISALIGNED**。
**差异**：
1. 文档（模板）仍要求「P5/P6 证据」，脚本已改为「`closed_at`」——两侧字面与语义均不一致（详见 A2/A3）。
2. **更严重**：文档/CHANGELOG 声称「`tech-debt.md` 被暂存时」触发，但实现条件是「同批还暂存了一个 **active 阶段**的 `.state.yaml`」——见下方【重点 1】的端到端实测。协议声明的触发面与实现的触发面不符。

**建议**：① 同步模板判据；② 把债务校验**移出** state-file 循环（见【重点 1】修复方向）。

---

### A2: 脚本→文档对齐

**脚本实现**（`agate/scripts/agate-debt-check.py:25-26`，模块 docstring）：
> `- closed 准入（BDD-8）：status==closed → task_id 非空 + evidence 序列化文本同时包含`
> `  task_id 与 P5/P6 标记`

**脚本实现**（同文件 `:170-174`）：实际要求 `closed_at`。

**结论**：**MISALIGNED**。
**差异**：**脚本自身的 docstring 未随代码更新**——`:25-26` 仍描述旧的 `P5/P6 标记` 判据，与新实现直接矛盾（同一文件内自相矛盾）。
**建议**：改 `:25-26` 为「`status==closed → task_id 非空 + `closed_at` 非空」；`tech-debt-template.md:41/63` 同步。

---

### A3: 一致性连锁 + 反向传播

**A3a（已知连锁，均已做）**：
- `agate-workspace/roadmap/roadmap.md` RM-AG0088 → `done`（✓）
- `agate-workspace/debt/tech-debt.md` DEBT0033 → `closed` + `closed_at`（✓）
- `CHANGELOG.md [Unreleased]`（✓）

**A3b（反向传播——应被影响但**未**在 diff 中出现的文件）**：

| 文件 | 为何应受影响 | 现状 |
|------|--------------|------|
| `agate/WORKFLOW.md`（「Pre-commit 检查总览」:344-364）| 反传表 row 47：改 check-*.py 的 pre-commit 触发行为 → **唯一权威表**须同步 | ❌ **表内无新债务步骤** |
| `agate/assets/templates/tech-debt-template.md`（:28-34 字段表 / :41 三态语义 / :63-80 closed 示例）| 判据变更的**权威模板**：字段表未列 `closed_at`、语义行仍写 P5/P6、示例条目**缺 `closed_at`**（照抄即被新判据拦截） | ❌ 三处全未同步 |
| `agate/scripts/agate-debt-check.py:25-26`（docstring）| 同 A2 | ❌ 未同步 |
| `agate/scripts/check-protocol-consistency.py`（CHECK 9 锚点 :794-798）| 反传表 row 47：须同步 CHECK 9 锚点表；`callers` 机制（:847）专门用于「让『CI 真的有这一步』成为机械判据」 | ⚠️ 锚点存在但**无 `callers`** |
| `agate/scripts/README.md:92` | 反传表 row 42：check-*.py 行为 → README | ⚠️ 未注明已挂 pre-commit（次要；README 是脚本目录非步骤清单，可接受） |

**结论**：**MISALIGNED**（WORKFLOW 权威表 + 模板 + docstring 三处必须补；CHECK 9 callers 见 A6）。
**建议**：按反传表 row 47 补齐 WORKFLOW 表 + CHECK 9 锚点；模板字段表/语义/示例三处补 `closed_at`。

---

### A4: 测试覆盖

**测试实现**（`agate/tests/unit/test_agate_debt_check.py`）：
- `test_bdd_5`（:117）夹具 DEBT0002（`status: closed`）补 `closed_at: 2026-08-20`；
- `test_bdd_8`（:182）子场景 2 证据 path 改 `docs/tasks/OTHER/...`（真正命中 task_id 分支）+ 补 `closed_at`；新增子场景 3（缺 `closed_at` → 拦截，:241-272）。

**实跑**：
```
$ python3 -m pytest agate/tests/unit/test_agate_debt_check.py -q -n auto
26 passed in 1.04s
```

**结论**：**MISALIGNED**。
**差异**：**判据替换有测试，但「pre-commit 挂载」这一步（本批的**主**修复）无任何端到端测试**——`test_pre_commit_hook.py` 中 grep `debt` 仅命中一条无关注释（`DEBT0014`）。**正因缺此测试，A1 的循环嵌套缺陷未被发现**。
**建议**：在 `test_pre_commit_hook.py` 加用例——暂存**非法** `tech-debt.md`（缺 `closed_at`）→ `git commit` 被阻断（exit 1）。该用例会立刻暴露当前缺陷。

---

### A5: 下游影响 + 文档传播

**CHANGELOG**（:56-60）：已记 [Unreleased]，✓。
**破坏性变更**：closed 条目新增 `closed_at` 强制字段——存量项目若在 active 任务 commit 中触碰其 `tech-debt.md` 且有条目缺 `closed_at`，会被新 gate 拦截。CHANGELOG 已提，但 `UPGRADING.md` 未记（release 时补，可接受）。
**文档传播**：见 A3b（WORKFLOW 表 + 模板未同步）。

**结论**：**MISALIGNED**（文档传播不完整，与 A3b 同源）。
**建议**：补齐 A3b；`UPGRADING.md` 在本版发布章节注明「closed 条目须补 `closed_at`」。

---

### A6: 锚点表覆盖

**锚点实现**（`agate/scripts/check-protocol-consistency.py:794-798`）：
```python
{
    "desc": "tech-debt schema 校验 + 回退覆盖比对（DEBT 条目）",
    "script": "agate/scripts/check-debt.py",
    "keywords": ["debt", "retreat"],
},
```
**callers 机制**（同文件 :878-894）：`callers` 可选；存在时校验脚本出现在指定调用方（注释 :847：「让『CI 真的有这一步』成为机械判据——DEBT0040③ 的实质要求」）。

**结论**：**MISALIGNED**。
**差异**：RM-AG0088 的**核心指控**正是「`check-debt.py` **未挂任何 gate/CI**」。修复后**未**给该锚点加 `callers: ["agate/scripts/pre-commit-gate.py"]` ⇒ CHECK 9 仍**无法机械检测**「挂载被未来改动摘除」——修复的**可验证性**没有闭合。
**建议**：加 `callers: ["agate/scripts/pre-commit-gate.py"]`（与同表 :792 `check-frontmatter.py` 等一致）。

---

### A7: 设计原则一致性

- **ADR-002（可判定性——gate 门槛机器可判定）**：用**显式字段 `closed_at`** 取代**子串启发式 `P[56]`**，正是「把门槛从可绕过的近似判定收紧为客观判定」——**支持**本改动。
- **ADR-004（安全网分层——hook 兜底）**：把 `check-debt.py` 挂入 pre-commit hook——**支持**本改动方向。

**结论**：**ALIGNED**。
（注：A1 的挂载点缺陷是**实现正确性**问题——它削弱了 ADR-004 的「兜底」实效——但这不是设计原则层面的偏离，故 A7 不降级。）

---

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|------|------|------|
| `91 passed` | `python3 -m pytest agate/tests/integration/test_pre_commit_hook.py agate/tests/unit/test_agate_debt_check.py -q -n auto` | ✅ **91 passed**（=65+26，两组分别实跑亦为 65 / 26） |
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✅ 「仅有 421 个 WARNING，无 ERROR」 |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ `rc=0` |
| `26 passed` | `python3 -m pytest agate/tests/unit/test_agate_debt_check.py -q -n auto` | ✅ **26 passed** |
| 「存量 **47** 条 closed 条目在新判据下全部通过」 | 见下（python 解析 tech-debt.md） | ⚠️ **计数更正为 48**；「全部通过」✅ |
| `test_debt_registry_closure.py`（相邻） | `pytest agate/tests/unit/test_debt_registry_closure.py -q -n auto` | ✅ 1 passed |

**存量统计命令**（实跑）：
```
$ python3 - <<'EOF'  # 解析 agate-workspace/debt/tech-debt.md 的 ```yaml 块
total yaml entries: 59
closed entries: 48
closed missing closed_at: []
EOF
```
**结论**：**ALIGNED**（全部声称可复现；唯一更正是 closed 计数 **47→48**——但「新判据下全部通过」的结论成立，因 `check-debt.py` 对真实文件 `rc=0`）。
**跑测前后 `git status --porcelain` 一致（无污染）**。

---

## 五项重点结论

### 重点 1：pre-commit 挂载**不正确**（阻断性缺陷）

| 子问题 | 结论 |
|--------|------|
| `_staged_name_only()` 返回值语义 vs `os.path.join(repo_root, _rel)` | ✅ 匹配。`_staged_name_only()`（:113-126）= `git diff --cached --name-only`，返回**仓库相对路径**（`rstrip("\r")`）⇒ join 正确 |
| Windows 路径分隔符 | ✅ git 输出恒用 `/`；`.replace("\\","/")`（:996）为防御性冗余，无害 |
| 非 `*/debt/tech-debt.md` 路径 | ⚠️ **会漏检**。判据为 `.endswith("/debt/tech-debt.md")`（:996）——若工作区布局使债务文件落在**仓库根**（如自定义 `AGATE_WORKSPACE=.` ⇒ `debt/tech-debt.md`，无前导目录），`endswith` 失败。建议改为对 `resolve_workspace` 求出的实际路径比对 |
| `check-debt.py` 缺失 → fail-open | ✅ 有 `os.path.isfile(...)` 守卫（:994），与 2j.2（:977）同模式，旧版协议不阻断 |
| 与既有 2x 步的短路关系（`gate_exit != 1` 守卫） | ⚠️ 新步**无**该守卫（2i/2i.1/2j/2j.1/2k 有，2j.2/2p 无）。因 2o（:1114）在 `gate_exit==1` 时 `sys.exit(1)`，**无行为差异**；但与同语义兄弟步不一致，建议加守卫或注明理由 |
| **步骤编号** | ❌ 新步标 `# 2l.`（:990），但 :1054 **已存在另一个 `# 2l.`**（复盘异常触发）——**编号重复**（历史已乱：2p 在 2l 之前）；CHANGELOG 亦写「2l 步」，误导 |

**❌ 核心缺陷（实测证明）**：新步嵌在 `for state_file in state_files:`（:726）循环体内（AST 验证：`For line 726 -> 1122` 包裹 line 990），且位于 PAUSED/READY/DONE 的 `continue`（:871）之后。⇒ **触发条件实为「同批暂存了 active 阶段（P1-P8）的 `.state.yaml`」，而非「`tech-debt.md` 被暂存」**。

**端到端实测**（scratch 副本 `/tmp/opencode/debt-gate-scratch`，一次性创建→操作→清理，未触碰真实仓库）：
```
仅暂存 tech-debt.md（closed 缺 closed_at）：
  $ AGATE_ROOT=<checkout>/agate python3 <checkout>/agate/scripts/pre-commit-gate.py
  GATE EXIT=0            # ❌ 未阻断
同文件直接调 check-debt.py：
  $ python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md
  GATE DEBT: ... closed 条目必须含 closed_at ...
  CHECK-DEBT EXIT=1      # ✅ 脚本本身正确
```
⇒ **本批自己的 hotfix 提交（只暂存 6 个文件、无 `.state.yaml`）恰好落在「不触发」区间**——该 gate 对其设计要防护的场景**完全失效**。

**修复方向**：把债务校验提升为**仓库级步骤**（如 `_check_ledgers_and_new_dirs` 所在位置 :722 之后、进入 state-file 循环之前，直接复用 :715 已算出的 `staged_all`），使其「每次提交都跑、不依赖 `.state.yaml`」（与 WORKFLOW :354 对 1.1 步的描述同模型）。

### 重点 2：判据替换**恰当**（方向正确，两处小瑕疵）

- ✅ **`closed_at` 比 `P[56]` 更有语义**：`P[56]` 与「条目已关闭」**无因果**——实测存量条目（如 DEBT0034/DEBT0042）的 evidence 里出现「P5 证据」纯属验证描述的自然用词，正文写任意一处 `P5`/`P6` 即可过关；`closed_at` 是**关闭时间戳**，可复核、与语义直接相关。
- ✅ **不再有「逼人写无关字串」的动机**：旧判据逼迫关单者「为满足判据」在 evidence 里塞 `P5`/`P6`；新判据要求填一个**本身就有意义**的字段。
- ✅ **存量全通过**：实跑解析得 48 条 closed 条目，`closed missing closed_at = []`，`check-debt.py` 对真实文件 `rc=0`。
- ⚠️ **格式未校验**：`:170` 仅 `str(data.get("closed_at") or "").strip()` 判非空。`closed_at: [1,2]`、`closed_at: {a: b}` 等**非字符串值**也会被 `str()` 转为非空而**放行**；且 `closed_at` **不在** `STR_FIELDS`（:57-60）⇒ 无类型校验（`created_at` 至少还有类型校验 + date 例外）。建议：把 `closed_at` 纳入类型校验，或加轻量格式校验（`YYYY-MM-DD`）。

### 重点 3：未引入判别力回归

- ✅ `test_bdd_5`：DEBT0002 本就是 `status: closed`，补 `closed_at` 是**必要**夹具修正（否则该正例会被新判据判红）——**未削弱**。
- ✅ `test_bdd_8` 子场景 2：原夹具证据 path 含 `TAG0002`（⇒ 旧 `task_id in ev` 恒真，实际靠 `P[56]` 分支判红，且旧断言含 `"evidence"` 对任何分支都成立，**判别力本就弱**）；新夹具 path 改 `OTHER`（**真正**命中 `task_id` 分支）——**判别力不降反升**。
- ✅ **P[56] 无残留断言**：全仓 grep `P[56]` 仅命中注释/文档串（`agate-debt-check.py:166/173`、`test_agate_debt_check.py:242`），无任何测试再断言旧判据。
- ⚠️ **命名陈旧**：测试函数名 `test_bdd_8_closed_missing_task_id_or_p5p6_intercepted`（:182）仍含 `p5p6`——建议更名（`..._or_closed_at_intercepted`），避免误导。

### 重点 4：端到端——**未能**构造「暂存非法 tech-debt.md → pre-commit 阻断」

见【重点 1】实测：真实 scratch 副本中，仅暂存非法 `tech-debt.md` 时 `pre-commit-gate.py` **exit 0**（不阻断）。⇒ **本批声称的端到端保护在当前实现下不存在**。只有「同批暂存 active 阶段 `.state.yaml`」时才会阻断（P8 关单路径覆盖，hotfix/triage 路径不覆盖）。

### 重点 5：A8 逐条复现

见 A8 表——`91 passed` / `0 ERROR` / `check-debt rc=0` / `26 passed` **全部复现**；唯一更正是 closed 计数 **47→48**。

---

## 需修复清单（主 Agent 派 implementer）

| # | 严重度 | 项 | 位置 |
|---|--------|----|------|
| 1 | **阻断** | 债务校验移出 state-file 循环，改为仓库级步骤（每次提交都跑） | `pre-commit-gate.py:990-1002` |
| 2 | **阻断** | 补端到端测试：暂存非法 `tech-debt.md` → commit 阻断 | `test_pre_commit_hook.py` |
| 3 | 高 | 同步 WORKFLOW「Pre-commit 检查总览」唯一权威表 | `WORKFLOW.md:344-364` |
| 4 | 高 | 模板三处同步：字段表加 `closed_at` / 语义行改判据 / closed 示例补 `closed_at` | `tech-debt-template.md:28-34,41,63-80` |
| 5 | 高 | 校验器 docstring 同步（自身自相矛盾） | `agate-debt-check.py:25-26` |
| 6 | 中 | CHECK 9 锚点加 `callers`，闭合「挂载可机械检测」 | `check-protocol-consistency.py:794-798` |
| 7 | 中 | 步骤编号去重（新步不叫 2l）；CHANGELOG 措辞更正触发条件 | `pre-commit-gate.py:990` / `CHANGELOG.md:57` |
| 8 | 低 | `closed_at` 纳入类型/格式校验 | `agate-debt-check.py:170` |
| 9 | 低 | 测试函数更名去 `p5p6`；路径判据改对 `resolve_workspace` 求值比对 | `test_agate_debt_check.py:182` / `pre-commit-gate.py:996` |

---

## 人工验收清单

- [x] Write 前已检查目标路径（`docs/reviews/agate-alignment-review-2026-10-09-H5-DEBT-GATE.md` 不存在，直接 Write）
- [x] 审查报告含 A1-A8 八项，每项有结论
- [x] MISALIGNED 项有差异描述 + 建议方向
- [x] 无 NEEDS_HUMAN_REVIEW（故无需 `[HUMAN_CONFIRMED:]` 配对）
- [x] 报告落盘到 `docs/reviews/agate-alignment-review-2026-10-09-H5-DEBT-GATE.md`
- [x] 跑测前后 `git status` 一致；未改任何协议/脚本/测试；未 commit/push
