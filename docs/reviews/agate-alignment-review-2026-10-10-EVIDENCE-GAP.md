---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: hotfix 判据补缺批——check-gate.py P6 新增「P6-evidence 被 .gitignore 忽略」提示（RM-AG0097，不阻断）+ LIMITATIONS 写明绊线执行面（DEBT0064 关单）+ roadmap/CHANGELOG 同步
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/LIMITATIONS.md, agate/scripts/check-gate.py, agate/tests/unit/test_check_gate.py]
---

# 协议-脚本对齐审查（EVIDENCE-GAP 批次）

> 被评审改动集**未提交**（工作区，分支 `hotfix/gate-evidence-gaps`）。本审查**只读**；变异测试在 `/tmp/opencode/agateon-copy` 副本上进行（创建→操作→清理均在副本，原仓 `git status` 未被本审查改动）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（1 处 T1 消费方归属为**部分**归属，见下；不影响关单） |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（候选未同步项已列出，均有「不强制」先例；见 A3 详情） |
| A4 | 测试覆盖 | **ALIGNED**（新用例存在且**双向判别力经变异实测**；但「已入库不误报」边界**未入用例**——建议补，见 A4 详情） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**——**经实测无既有用例转红**；无需更新夹具 |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（CHANGELOG 已标；无破坏性变更；LIMITATIONS 为用户可见面） |
| A6 | 锚点表覆盖 | **ALIGNED**（无需新增锚点；`--strict-errors-only` 0 ERROR） |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **MISALIGNED**——「`ruff` rc=0」**不可复现**（实为 rc=1，见 A8 详情）；「2911 passed」亦未精确复现 |

**总体：不可 commit**——存在 1 项必修复（A8：新用例引入未使用导入使 `ruff check agate/` 转红）。另有若干 minor（建议处理，非阻断）。

---

## 逐项审查

### A1: 文档→脚本对齐

**① RM-AG0097（gate 侧）**

- 文档声明（`agate-workspace/roadmap/roadmap.md` RM-AG0097 行收窄末列）：
  > 2026-10-10 **【gate 侧已补】**：`check-gate.py P6` 新增提示——P6-evidence 被 `.gitignore` 忽略时告警（不阻断…）
- 脚本实现（`agate/scripts/check-gate.py:1675-1697`）：`os.walk(P6-evidence)` → 逐文件 `_git(["check-ignore","-q","--",rel], cwd=task_dir)` → `rc==0` 计入 → 有则 `sys.stderr.write("GATE P6 WARNING: …（RM-AG0097，不阻断）")`。**只写 stderr，不改退出码**（后续 return 值未受影响）⇒ 与「提示（不阻断）」一致。
- 协议片段（`agate/assets/templates/gitignore-fragment.txt:32`）`!agate-workspace/tasks/**/P6-evidence/**` 已存在（协议侧此前已完成）⇒ 提示文案指向的补救与片段一致。

**结论**：ALIGNED。

**② DEBT0064 / LIMITATIONS 节**

- 契约（`agate/rules/task-data/level-1.yaml`）`traps`：T1 `positive_declaration_in_prose` / T2 `bdd_heading_format` / T3 `strict_verdict_line_in_prose` / T4 `prod_touched_safety_gate`。
- 文档（`agate/LIMITATIONS.md:151-164`）新增节，列出 T1/T2/T4 消费方并标 **T3 无消费方**。
- 脚本侧逐个核对：
  - **T3** `strict_verdict`：全仓 `grep` 仅命中 `level-1.yaml:269` + 新增 `LIMITATIONS.md:160` ⇒ **确无消费方** ✓（LIMITATIONS 说法准确）。
  - **T2** `bdd_heading_format` → `check-gate.py:771-785`（"GATE P1: T2 绊线——BDD 标题须用统一格式 `#### BDD-N:`"）✓ 归属准确。
  - **T4** `prod_touched_safety_gate` → `pre-commit-gate.py` PROD_TOUCHED 扫描（`:249/683/829`）✓ 归属准确。
  - **T1** `positive_declaration_in_prose` → LIMITATIONS 单列 `check-gate.py::count_p7_markers`。**核代码**：`count_p7_markers`（`agate_common.py:1611`）**只数 BLOCKER / DEVIATION-CRITICAL**；T1 的 markers 共 **10 个**，其余由 `count_design_gap`（DESIGN_GAP/DESIGN_GAP_REVIEWED）、`count_code_map_lines`（CODE_MAP_UPDATED/EXEMPT）、`check-scope-resolved.py`（SCOPE+/SCOPE_RESOLVED）、`_gate_p7_structured`（scope_plus/need_confirm 结构化集合）等**多个**消费方实现。
  - ⇒ T1 行是**部分归属**（列了一个真实但不是唯一的消费方）。核心结论「T1 有代码消费方」成立（故 DEBT0064 的「T3 是唯一缺口」判断不受影响），但表头「消费方」易被读成穷举。此归属沿用 DEBT0061 关单时的既有表述，非本批新引入。

**结论**：ALIGNED（T1 行为**部分归属**，minor，见「重点结论 3」）。

### A2: 脚本→文档对齐

- 新脚本逻辑（P6 忽略告警）在 `CHANGELOG.md`（`### 修复` 节，`[Unreleased]`）与 roadmap 均已描述；`LIMITATIONS` 节描述了 T3 缺口。
- 脚本对**已入库文件**的行为（`check-ignore` 返回非 0 ⇒ 不误报）与 CHANGELOG 声称一致（**独立实测**：见 A4/重点结论 1）。
- 无「脚本有、文档无」或反向的语义偏差。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**A3a 已知连锁（diff 内已随改）**：`CHANGELOG.md`（`[Unreleased]` 修复节）、`roadmap.md`（RM-AG0097 收窄）、`tech-debt.md`（DEBT0064 → closed）、`LIMITATIONS.md`（新节）、`check-gate.py`、`test_check_gate.py`。

**A3b 反向传播（主动推断「应被影响」的文件，逐一验证）**：

| 候选文件 | 是否需要同步 | 验证结果 |
|---|---|---|
| `agate/scripts/README.md`（`check-gate.py` 行） | **候选（minor，不强制）** | `README:76` 有登记 gate **WARNING** 的先例（「gate_p4 新增…缺『新增文件核对表』WARNING」）⇒ 新 `gate_p6` WARNING 未登记。**但**同类 RM-AG0075 的 P8 `.agate-tmp` 告警**也未**登记（`grep RM-AG0075/agate-tmp README` 0 命中）⇒ 存在「不登记非阻断告警」的先例，判**不强制**。 |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」P6 行（`:324`） | 否 | 该行描述的是 exit 契约（`check-gate.py P6` exit 2）与 provenance 审计；新告警**不改退出码** ⇒ 不影响。 |
| `agate/phase-cards/P6-acceptance.md` | **候选（minor）** | `:20` 现写「若 `.gitignore` 忽略需 `git add -f`」——与新告警建议的「fragment 取反规则」是**两种不同补救**（`git add -f` 为单文件绕过，取反为根因修复）。未同步。 |
| `agate/tests/README.md` | 否 | 新用例落在已登记的 `test_check_gate.py`，映射表无需新增行。 |
| `agate/scripts/README.md` 新增脚本登记面 | 否 | 未新增/改名 `agate/scripts/` 下文件。 |
| CHECK 9 锚点表（`check-protocol-consistency.py`） | 否 | 见 A6。 |

**结论**：ALIGNED（两项候选均为「可选」，有同类不登记先例）。

### A4: 测试覆盖

**实跑（副本 `/tmp/opencode/agateon-copy`，`AGATE_ROOT=副本/agate`）**

- 新用例单跑：`test_rm_ag0097_p6_evidence_gitignored_warns` → **1 passed**。
- **变异实测（判别力）**（副本上，同一次 bash 内完成）：
  - 变异① 删去新代码块（`# RM-AG0097…` 至 `# TAG0050 批 D…` 之间，1188 字符）→ 用例**转红**（`AssertionError: … 'RM-AG0097' in 'GATE P6: FAIL=0, TOTAL=0\n'`）⇒ 正向断言**真**能抓到。
  - 变异② 把 `if _rc == 0:` 改为 `if True:`（恒告警）→ 用例**转红**（`未被忽略时不得误报` 断言失败）⇒ 反向断言**真**能抓到。
- **全量**（CI 口径）：`python3 -m pytest agate/tests/ --reruns 1 -n auto` → **1 failed, 2910 passed, 3 skipped, 1 rerun (89s)**。
  - 唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——调用本机 `opencode debug agent orchestrator`，本机 opencode CLI **无该子命令**（`Unknown subcommand "agent" … Did you mean "agents"`）⇒ **环境性**（依赖本机 CLI 版本），与本改动无关。
  - ⚠️ **不称「全绿」**：存在 1 条环境性 failed。

**边界覆盖缺口（minor）**：CHANGELOG 声称「已入库文件 `check-ignore` 返回非 0 ⇒ 不误报」，但**用例的反向对照只删掉了 `.gitignore` 规则**（未跟踪、不命中），**未覆盖「文件已跟踪且 `.gitignore` 命中」这一真正的『已入库』场景**。该行为经**独立实测**为正确（已跟踪+命中 → `check-ignore` 返回 **1**，见重点结论 1），但**无回归锁**。建议补一条 tracked 用例。

**结论**：ALIGNED（有测试、判别力经变异实测；tracked 边界为建议补充项）。

### A4b: 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054）

- **经实测无既有用例转红**：全量 `-n auto` 中除 1 条环境性 failed（opencode CLI）外全绿；无任何既有用例因新告警的额外 stderr 输出转红（`grep "GATE P6"` 未发现断言 gate_p6 精确 stderr 的既有用例）。
- **需更新的夹具**：**无**。新用例复用既有 `git_repo` / `agate_root` / `agate_scripts` / `python_exe` / `run_cli` fixture，未改 `conftest.py`。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播

- **下游 gate 行为**：新告警**不阻断**（仅 stderr），对存量项目 P6 gate 的**退出码无影响** ⇒ 非破坏性变更。
- **CHANGELOG**：已在 `[Unreleased] ### 修复` 标注（`RM-AG0097 / DEBT0064`）。
- **LIMITATIONS.md**：新增节为用户可见面（`agate/AGENTS.md` 指「已知局限（使用前建议先读）」）⇒ DEBT0064 关单所取的「用户可见面写明」分支成立。
- **UPGRADING.md**：无破坏性变更，按惯例可不加章节（本批未改；非本次评审对象）。
- 未发现需同步的 `orchestrator-template.md` / `dispatch-protocol.md` / `role-system.md` / 角色文件（新告警不改派发/角色语义）。

**结论**：ALIGNED。

### A6: 锚点表覆盖

- `check-protocol-consistency.py --strict-errors-only` → **rc=0，0 ERROR**（仅 432 条冻结 WARNING）。
- 锚点表内无 `RM-AG0097` / `gitignore-fragment` 条目；同类 `RM-AG0075`（P8 `.agate-tmp` 告警）亦无锚点 ⇒ 新增非阻断告警**无需**新增锚点（锚点验证的是「校验脚本存在且被挂载」，新告警不引入新脚本）。
- CHECK 9 的 `check-gate.py` 相关锚点（`DESIGN_GAP` / `_check_roadmap_done` 等）不受影响。

**结论**：ALIGNED。

### A7: 设计原则一致性

- RM-AG0097 明示手段②（`check-gate.py P6` 给 WARNING），与 `adr.md` ADR-015「让错误不可能 / 让错误可见」取向一致：手段①（协议 fragment 取反）已做，手段②（提示）本批补齐。
- DEBT0064 的「先设计误报面再接 T3」判断，与 `adr.md` 关于「判据须先控误报面」的既有取向一致（LIMITATIONS 节亦写明「先设计误报面」）。
- 未发现与本批相关的未记录架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 产出/复核命令 | 结论 |
|---|---|---|
| `check-gate.py P6` 新增提示、**不阻断** | 读 `check-gate.py:1675-1697` + 非 git/正常两跑（rc 仅由 pass/fail 决定） | ✅ 成立 |
| 「已入库文件 `check-ignore` 返回非 0 ⇒ 不误报」 | `/tmp/opencode` 沙盒：`git check-ignore -q -- <tracked+命中>` → **rc=1**（默认查 index） | ✅ 成立 |
| 「回归用例覆盖正反两向」 | 变异①/② → 两次转红 | ✅ 成立 |
| 「T3 全仓 0 消费方」 | `grep -rn strict_verdict agate/`（排除 pycache）→ 仅 yaml 定义 + LIMITATIONS | ✅ 成立 |
| 「T1/T2/T4 有消费方」 | T2/T4 逐行核对成立；T1 为**部分**归属（`count_p7_markers` 仅 2/10 markers） | ⚠️ 成立但归属不完整 |
| roadmap「RM-AG0097 gate 侧已补」 | 读代码 | ✅ 成立 |
| `check-protocol-consistency` **0 ERROR** | `--strict-errors-only` → rc=0，0 ERROR | ✅ 复现 |
| `check-debt` **rc=0** | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → rc=0 | ✅ 复现 |
| roadmap **0 异常** | 复现 `_check_roadmap_done` 列数判据（`_ROADMAP_EXPECTED_COLS=9`）→ RM-AG 111 行 0 异常 | ✅ 复现 |
| **`ruff` rc=0** | `~/.venvs/agate-dev/bin/ruff check agate/` → **rc=1**（F401 `pathlib.Path` 未使用，`test_check_gate.py:4056`） | ❌ **不可复现** |
| **2911 passed** | `pytest agate/tests/ --reruns 1 -n auto` → **2910 passed** + 1 env-failed + 3 skipped | ❌ 未精确复现（差 1 = 环境性 failed） |

**结论**：**MISALIGNED**——`ruff rc=0` 声称不成立（见「重点结论 2」），须修复后重跑；其余数字/结论声称均可复现。

---

## 重点结论（5 项）

### 1. 新提示的正确性与鲁棒性 —— ✅ 通过（不误报、不崩）

**退出码语义**（独立实测，`/tmp/opencode` 沙盒）：

| 场景 | `check-ignore -q -- <path>` rc | 新代码行为 |
|---|---|---|
| 未跟踪 + `.gitignore` 命中 | **0** | 告警（预期） |
| **已跟踪 + `.gitignore` 命中** | **1** | **不告警**（正确——`check-ignore` 默认查 index，已入库文件不报） |
| 已跟踪 + 命中 + `--no-index` | 0 | （代码未用 `--no-index`，不触发） |
| 未命中任何规则 | 1 | 不告警 |
| **非 git 目录** | **128** | `rc != 0` ⇒ 不告警，**不崩** |
| **`git` 不存在**（PATH 空） | 子进程 `FileNotFoundError` | `_git` 捕获 `OSError` → `(1,"")` ⇒ 不告警，**不崩** |
| `GIT_DIR` 劫持到别仓 | — | 实测 **0 误报** |

**`cwd=task_dir` 可靠性**：传入**相对** `task_dir` 的路径 + `cwd=task_dir` ⇒ 解析一致（实测相对路径从 task_dir cwd 正确命中）。注意与 P8 段（`:2381`）的**不同**取向：P8 显式传**绝对路径**并注明「相对路径解析依赖 CWD」；本处用相对路径但显式锚定 cwd，等价成立。`_git` docstring 的提醒（「按仓库根锚定须显式传 cwd」）在此满足。

**`--` 分隔符**：必要且更稳（防路径以 `-` 开头）；`_is_ignored`（`:1394`）未用 `--`，本处更严谨。

**性能**：逐文件起子进程。实测最大任务 `TAG0037/P6-evidence`（82 文件）：**逐文件 0.129s vs 批量单调用 0.004s**（`git check-ignore -- p1 p2 …` 可一次查多路径、返回被忽略行、rc=0 当且仅当有命中）。批量可提速 ~30x，但**绝对成本（~0.13s）对 commit gate 可忽略** ⇒ **非必需**（可选优化）。

**残留（非本批引入）**：`_git` 走 `run_git` 时**未**开 `clean_location_env=True`（与既有 `_is_ignored` / P8 段同款）——环境若带 `GIT_DIR` 可能定位偏移；实测劫持场景为 fail-open（0 误报），且既有代码同模式，**不判新缺陷**。

### 2. 测试判别力 —— ✅ 真（但 `ruff` 转红 = 必修复）

- 变异①（删新块）→ 正向断言转红；变异②（恒告警）→ 反向断言转红 ⇒ 用例**真**能抓。
- **❗ 必修复**：新用例 `test_check_gate.py:4056` 引入 `from pathlib import Path`（**文件顶部 `:25` 已导入**），函数内 `Path` **未使用** ⇒ `ruff check agate/` **rc=1**（F401）。**base 版 ruff 通过**（实测 `git show HEAD:…` → All checks passed），故为**本批新引入**。CI `ruff` job（`.github/workflows/protocol-tests.yml:241-254`，`ruff check agate/`）会**转红**。
  - **修复**：删除该行（`from pathlib import Path`）。`import subprocess`（同处局部导入）**被使用**，保留。
  - **严重性说明**：`gh api …/branches/main/protection` 实测 required = `shellcheck×2 / pytest×2 / consistency / gate-backstop`，**`ruff` 非 required**（workflow 头注亦写「platform-scan/ruff 非 required」）⇒ **不阻塞合并**，但 (a) 作者声称「ruff rc=0」为**假**，(b) CI 出现红灯 job。**建议合并前修掉**。

### 3. DEBT0064 关单是否成立 —— ✅ 成立（T1 归属 minor）

- 关单判据二选一，取「**已在用户可见面写明『仅记录不判定』**」分支：
  - `LIMITATIONS.md:151-164` 新增节，显式写「**T3 无消费方——仅记录，不判定**」「引用 `traps` 时请勿假定四条都被强制」⇒ **真的**能让人不再假定 T3 被强制。**成立**。
  - LIMITATIONS.md 为用户可见面（`agate/AGENTS.md` 明列）。**成立**。
- `check-debt.py` 校验 `closed` 准入（`task_id` 非空 + evidence 含 task_id + `closed_at`）：**rc=0** ⇒ schema 合法。`task_id: hotfix-gate-evidence-gaps`（批次标签、无任务目录）与已关 DEBT0063 同款先例。
- **T1/T2/T4 消费方归属**：T2/T4 **准确**；T1 为**部分归属**（见 A1②）——`count_p7_markers` 仅覆盖 T1 十个 marker 中的 BLOCKER/DEVIATION-CRITICAL。**不影响关单**（关单只依赖「T3 无消费方」这一准确判断）。建议将 T1 行改为「由 `count_p7_markers` / `count_design_gap` / `count_code_map_lines` / `check-scope-resolved.py` 等**共同**消费」以避免读者误解。

### 4. 反向传播 —— ✅ 无强制同步项（2 项候选已列）

见 A3b。`README.md` 的 gate WARNING 登记与 `P6-acceptance.md` 的补救口径为**可选**候选；两者均有「不强制」先例（RM-AG0075 P8 告警未登记；P6 卡 `git add -f` 与 fragment 取反为并行补救）。**未同步不构成 MISALIGNED**。

### 5. A4b + A8 实跑数字 —— 见上

- `1 failed（环境性：opencode CLI 无 `debug agent`） + 2910 passed + 3 skipped`（**不称全绿**）。
- `0 ERROR`（`--strict-errors-only`）✅ / `check-debt rc=0` ✅ / `roadmap 111 行 0 异常` ✅ / **`ruff` rc=1 ❌**。
- 「2911 passed」未精确复现（差 1 即环境性 failed）；「ruff rc=0」不可复现。

---

## 是否可 commit

**不可 commit（存在必修复项）**：

1. **必修复**：删除 `agate/tests/unit/test_check_gate.py:4056` 的未使用 `from pathlib import Path`（使 `ruff check agate/` 回到 rc=0），并重跑 `ruff` + 该用例。

**建议（非阻断，可与修复一并处理）**：

2. A4：为「**已跟踪文件 + `.gitignore` 命中 ⇒ 不误报**」补一条回归用例（当前 CHANGELOG 声称的边界未被用例锁定）。
3. A1：`LIMITATIONS.md` T1 行改为**多消费方**归属（或注明「代表性消费方」），避免被读成穷举。
4. A3：可选同步 `agate/scripts/README.md` 的 `check-gate.py` WARNING 登记 / `P6-acceptance.md` 的补救口径。
5. 文案一致性（minor）：新告警引用 `gitignore-fragment.txt` 未带 `{agate_root}/assets/templates/` 前缀，而 P8 告警（`:2388`）带前缀——可统一。

修复项 1 完成后，本批其余各项均为 ALIGNED，可 commit（`self-gate-review:` 留痕见提交信息）。

---

## 只读纪律声明

- 本审查**未**对被评审仓库执行任何写操作（无 `checkout/restore/reset/stash/clean/add/commit`，未编辑被评审文件）。
- 变异测试在**副本** `/tmp/opencode/agateon-copy` 上进行，且「备份 → 变异 → 跑测 → 还原」在**同一次 bash 调用**内完成（还原后 `grep -c RM-AG0097` 校验 = 2）。
- 全量 pytest / 一致性 / debt / roadmap / ruff 均在**副本**上跑（`AGATE_ROOT=副本/agate`）；原仓仅做只读 `git status/diff/show` 与只读 `grep`。
