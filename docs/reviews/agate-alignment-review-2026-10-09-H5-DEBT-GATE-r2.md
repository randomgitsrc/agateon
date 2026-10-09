---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "RM-AG0088 / DEBT0033 第 2 轮复核——挂载点移出循环（改名 2z）+ 新增端到端用例 + docstring/WORKFLOW/模板/CHECK9 同步"
files_changed:
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/agate-debt-check.py
  - agate/scripts/check-protocol-consistency.py
  - agate/tests/integration/test_pre_commit_hook.py
  - agate/tests/unit/test_agate_debt_check.py
  - agate/WORKFLOW.md
  - agate/assets/templates/tech-debt-template.md
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
---

# 协议-脚本对齐审查（r2）

> **一句话结论**：r1 的**两处阻断项已真正修复并独立验证**（挂载点移出循环 → 纯 `tech-debt.md` 提交现可拦截；端到端用例已加且有判别力）。**剩余 2 处 minor 文档漂移**（模板字段表漏 `closed_at`、WORKFLOW 行号重复 + CHANGELOG 步号陈旧）——各一行即可修，修完即可 commit。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（minor） |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（minor） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**是否可 commit**：**阻断项已闭合；建议随本批修掉 A3/A5 的 2 处 minor（各一行）后 commit**。若主 Agent 判定 minor 可另开 follow-up，则当前状态亦无功能风险。

---

## r1 发现逐条核实

| r1 # | r1 结论 | r2 核实 | 证据 |
|------|---------|---------|------|
| **1** | **阻断**：挂载在循环内 + `continue` 后 ⇒ 纯 debt 提交失效 | ✅ **已修复** | AST：新步 line 1110 `enclosing blocks = []`（循环外）；scratch 实测「仅暂存非法 tech-debt.md（无 `.state.yaml`）」→ **exit 1**，「合法」→ **exit 0** |
| **2** | **阻断**：无端到端测试 | ✅ **已修复** | 新增 `test_rm_ag0088_staged_invalid_tech_debt_blocks_commit` + `..._valid_..._passes_commit`，实跑 **2 passed**；判别力见下【重点 2】 |
| 3 | 高：WORKFLOW 唯一权威表未加步 | ⚠️ **部分** | 已加行（:363），但**标号 `2.12` 与既有 `check-retrospective` 行（:364）重复**——见 A3 |
| 4 | 高：模板三处同步（字段表/语义/示例） | ⚠️ **部分** | 语义行（:41）+ 小节标题（:63）+ 示例（:80）已补；**字段表（:19-33）仍无 `closed_at` 行**——见 A3 |
| 5 | 高：校验器 docstring 自相矛盾 | ✅ **已修复** | `agate-debt-check.py:25-27` 现写「task_id 非空 + …包含该 task_id + **`closed_at`**」；全仓 `P5/P6 标记` 已 0 命中 |
| 6 | 中：CHECK 9 锚点缺 `callers` | ✅ **已修复** | `check-protocol-consistency.py:798` 加 `"callers": ["agate/scripts/pre-commit-gate.py"]` |
| 7 | 中：步号去重 + CHANGELOG 措辞 | ⚠️ **部分** | 脚本步号已改 `2z`（去重 ✓）；**CHANGELOG:57 仍写「新增 2l 步」**（未改）——见 A5 |
| 8 | 低：`closed_at` 类型/格式校验 | ➖ **未修**（r1 已标 low，可接受） | `:170` 仍 `str(...).strip()` 非空判定；`closed_at` 不在 `STR_FIELDS` |
| 9 | 低：测试函数更名 + 路径判据 | ⚠️ **部分** | 路径判据已改 `_norm="/"+rel`（✓）；**测试函数名 `..._or_p5p6_intercepted`（:182）仍含 `p5p6`**（未改） |

**阻断项（1、2）均已闭合并经独立复现。**

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`CHANGELOG.md:57`、`tech-debt-template.md:41`）：「`tech-debt.md` 被暂存时跑 `check-debt.py <file>`，exit 1 → 阻断」；closed 条目须 `task_id` + `closed_at`。
**脚本实现**（`pre-commit-gate.py:1110-1127`）：循环外遍历暂存清单，命中 `/debt/tech-debt.md` → 跑 `check-debt.py`。

**结论**：**ALIGNED**。
- 触发面现为「暂存 `tech-debt.md`」——**与 `.state.yaml` 无关**（AST `enclosing blocks=[]` + scratch 实测「纯 debt 提交」生效），与文档声明一致。
- 判据与模板语义一致（`closed_at`）。

### A2: 脚本→文档对齐

**脚本 docstring**（`agate-debt-check.py:25-27`）已更新为 `task_id` + `closed_at`（r1 的自相矛盾已消除）。
**结论**：**ALIGNED**。

### A3: 一致性连锁 + 反向传播

**A3a**：roadmap RM-AG0088→done、DEBT0033→closed、CHANGELOG ✓。

**A3b 残留（两处 minor）**：
1. **`tech-debt-template.md` 字段表（:19-33）仍无 `closed_at` 行**。该表标题明写「字段表（schema 校验，缺失/非法即 exit 1）」，而 `closed_at` 现对 closed 条目为 schema 必填——表中应有类似 `task_id` 的条件必填行（如 `| closed_at | 否 | str | 关闭时间（closed 必填）|`）。现 `closed_at` 仅出现在三态语义行/小节标题/示例，**字段表漏列**。（r1 修复清单 #4 明列此项，未落实。）
2. **`WORKFLOW.md` 两行同标 `2.12`**：`:363`（新 `check-debt.py`）与 `:364`（既有 `check-retrospective.py`）标号重复。建议新行改用脚本实际标号 `2z`（或 `2.13`）。

**结论**：**MISALIGNED**（minor——均为一行文本修正，无功能影响）。
**建议**：补字段表 `closed_at` 行；新 WORKFLOW 行标号去重。

### A4: 测试覆盖

新增 `test_pre_commit_hook.py::test_rm_ag0088_staged_invalid_tech_debt_blocks_commit`（非法 → 阻断）与 `..._valid_..._passes_commit`（正向对照）。
**实跑**：
```
$ pytest agate/tests/integration/test_pre_commit_hook.py::test_rm_ag0088_staged_invalid_tech_debt_blocks_commit \
         agate/tests/integration/test_pre_commit_hook.py::test_rm_ag0088_staged_valid_tech_debt_passes_commit -q -n auto
2 passed
$ pytest agate/tests/integration/test_pre_commit_hook.py agate/tests/unit/test_agate_debt_check.py -q -n auto
93 passed      # r1 为 91，+2
```
**结论**：**ALIGNED**。判别力见【重点 2】。

### A5: 下游影响 + 文档传播

CHANGELOG [Unreleased] 已记（:56-60）✓，且**触发条件描述现已准确**（「被暂存时」）。
**残留（minor）**：`CHANGELOG.md:57` 仍写「新增 **2l** 步」，而脚本实际标号已是 `2z`——步号陈旧。`UPGRADING.md` 待发布章节补（release 时，可接受）。

**结论**：**MISALIGNED**（minor——一行步号修正）。
**建议**：CHANGELOG:57「2l」→「2z」。

### A6: 锚点表覆盖

`check-protocol-consistency.py:798` 已加 `"callers": ["agate/scripts/pre-commit-gate.py"]` ⇒ CHECK 9 现可**机械检测**「挂载被未来改动摘除」（RM-AG0088 的可验证性闭合）。
**结论**：**ALIGNED**。

### A7: 设计原则一致性

ADR-002（可判定性）支持显式字段判据；ADR-004（安全网分层）支持 hook 挂载——且本次修复使 hook 兜底对**纯 debt 提交**真正生效。
**结论**：**ALIGNED**。

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|------|------|------|
| `2901 passed` | `python3 -m pytest agate/tests -q -n auto -p no:cacheprovider` | ✅ **2901 passed**（实测 `1 failed, 2901 passed, 2 skipped`；唯一 failed 为**环境性**，见下） |
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✅ 「仅有 421 个 WARNING，无 ERROR」 |
| `2 passed` | `pytest ...::test_rm_ag0088_staged_invalid_... ...::..._valid_... -q -n auto` | ✅ **2 passed** |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ `rc=0` |

**唯一 failed 说明**：`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` —— 断言 `opencode debug agent orchestrator` 成功，但本机 `opencode debug --help` 只列出 `agents`（复数）子命令 ⇒ **工具版本不匹配的环境问题**；该测试文件**不在本批 diff 内**，与本改动无关（隔离复跑稳定失败）。
**结论**：**ALIGNED**（4 项声称全部复现；1 failed 为既有环境性，非本批引入）。
**跑测前后 `git status --porcelain` 一致（无污染）。**

---

## 重点项结论（本轮指定）

### 重点 1：挂载位置与触发条件（双重确认）

- **AST**：新步 `# 2z.`（line 1110）的 `enclosing blocks = []` ⇒ **不在任何 `for`/`while`/`if`/`with` 内**（r1 时为 `For 726→1122` 包裹）。已移出 state-file 循环。
- **实跑**（scratch，一次性）：
  - 仅暂存**非法** `tech-debt.md`（**无** `.state.yaml`）→ **exit 1**（stderr 含「closed 条目必须含 closed_at」+「技术债登记 schema 非法…阻断 commit」）。
  - 仅暂存**合法** `tech-debt.md` → **exit 0**。
  ⇒ 触发条件**确为「暂存 `tech-debt.md`」，与 `.state.yaml` 无关**。
- **短路关系**：该步**无** `gate_exit != 1` 守卫，且置于循环之后、`# 3.` 之前 ⇒ **不受 gate 结果影响**（对债务面独立判定）。恰当（与 2j.2/2p 的「独立于任务 gate」语义一致）。

### 重点 2：判别力（变异验证）

- 拷贝整棵 `agate/` → 把 `2z` 块**移回** `for state_file in state_files:` 循环内 → 对「仅暂存非法 tech-debt.md」的提交 → **exit 0**（**复现 r1 缺陷**）。
- 新用例 `test_rm_ag0088_staged_invalid_...` 断言 `returncode != 0` ⇒ 在**旧放置**下**必转红**。
⇒ 该用例对「挂载位置」**有真实判别力**，可作未来回归守护。正向对照用例（valid → rc==0）无独立判别力，但用于防「误报」，与 invalid 用例配对恰当。

### 重点 3：是否引入新问题

| 检查 | 结论 |
|------|------|
| 无 `tech-debt.md` 暂存时零开销/无误报 | ✅ 仅字符串比较 `_norm.endswith(...)`，不触发子进程；scratch 实测「未暂存债」→ exit 0 无输出 |
| `check-debt.py` 缺失 → fail-open | ✅ `os.path.isfile(SCRIPT_DIR/check-debt.py)` 守卫；实测（删脚本的拷贝）→ exit 0 |
| Windows 分隔符 | ✅ `_norm = "/" + rel.replace("\\","/")` 归一 |
| 工作区在仓库根（`debt/tech-debt.md`） | ✅ 归一后 `_norm = "/debt/tech-debt.md"` → endswith 命中（r1 漏检场景已覆盖） |
| 步骤编号 | ✅ 脚本内改 `2z`（不再与既有 `2l` 重复）；⚠️ WORKFLOW 表内新行仍与 `2.12` 重复（见 A3） |
| 与既有步骤的顺序 | ✅ 置于 `# 3.` 之前、循环之后，不影响既有步骤 |

### 重点 4：A8 逐条复现

见 A8 表——`2901 passed` / `0 ERROR` / `2 passed` / `check-debt rc=0` **全部复现**；`1 failed` 为环境性（`opencode debug agent` 子命令缺失），非本批引入。

---

## 剩余 minor 清单（建议随本批修，各一行）

| # | 项 | 位置 |
|---|----|------|
| m1 | 字段表补 `closed_at` 行（条件必填，closed 用） | `tech-debt-template.md:19-33` |
| m2 | 新 WORKFLOW 行标号去重（`2.12` → `2z`） | `WORKFLOW.md:363` |
| m3 | CHANGELOG 步号 `2l` → `2z` | `CHANGELOG.md:57` |
| m4 | （r1 low）`closed_at` 纳入类型/格式校验 | `agate-debt-check.py:170` |
| m5 | （r1 low）测试函数更名去 `p5p6` | `test_agate_debt_check.py:182` |

---

## 人工验收清单

- [x] Write 前已检查目标路径（`docs/reviews/agate-alignment-review-2026-10-09-H5-DEBT-GATE-r2.md` 不存在，直接 Write）
- [x] 审查报告含 A1-A8 八项，每项有结论
- [x] MISALIGNED 项有差异描述 + 建议方向
- [x] 无 NEEDS_HUMAN_REVIEW（故无需 `[HUMAN_CONFIRMED:]` 配对）
- [x] 报告落盘到 `docs/reviews/agate-alignment-review-2026-10-09-H5-DEBT-GATE-r2.md`
- [x] 跑测前后 `git status` 一致；未改任何协议/脚本/测试；未 commit/push
