---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B / H2——修 2 条实测缺陷：RM-AG0084/DEBT0028（check-retrospective.py 与 agate-render-dispatch-prompt.py 的工作区推导改走 agate_common.resolve_workspace，支持 .agate.env 的 AGATE_WORKSPACE= 与 env AGATE_TASKS_DIR 覆盖）；RM-AG0082/DEBT0008（agate-feedback.py 的 ABS_PATH_RE 由「任意 / 开头 token」收窄为三选一形态，中文斜杠分隔词不再误脱敏）
files_changed: [agate/scripts/check-retrospective.py, agate/scripts/agate-render-dispatch-prompt.py, agate/scripts/agate-feedback.py, agate/tests/unit/test_check_retrospective.py, agate/tests/unit/test_agate_render_dispatch_prompt.py, agate/tests/unit/test_agate_feedback.py]
---

# 协议-脚本对齐审查

> 审查对象：分支 `hotfix/batch-b-hygiene`（**未提交**，改动在工作区）。全程只读——未改任何协议/脚本/测试，
> 未 commit / push。跑测试前后 `git status --porcelain` 一致（仅 6 个被评审文件 + 本审查留痕/成果文件）。
> 留痕：`docs/reviews/agate-alignment-2026-10-09-H2-HYGIENE-01.progress.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED** |

**一句话**：两条修复的核心方向与实现**正确**（RM-AG0084 的 `.agate.env` 覆盖端到端可复现；RM-AG0082 的中文斜杠词误伤已消除、真实路径不退化），但**本批引入了一条新的测试回归**（新用例含 `/tmp/x/y` 字面量 → 打破既有的 `test_t42_scan_is_runnable_and_clean_on_repo`），**CHANGELOG 未同步**（H1 批先例在提交内更新），另有**两处需人工裁决**（反向传播第三处同款实例、匿名化正则的 2 段路径过度收窄）。

---

## 逐项审查

### A1: 文档→脚本对齐

**协议文档声明（两处）**：

- `agate/SETUP.md:381-391`：
  > 工作区位置默认 = 项目根下 `agate-workspace/`。需要指向别处时，在**项目根**创建 `.agate.env`：… 优先级：`.agate.env` 显式配置 > 环境变量 `AGATE_TASKS_DIR` > 默认 `agate-workspace/`。… 解析逻辑见 `scripts/agate_common.py`。
- `agate/WORKFLOW.md:85`：
  > agate 的所有**编排状态**统一落盘到工作区（默认 `{AGATE_WORKSPACE}` = 项目根下 `agate-workspace/`，可用 `.agate.env` 配置指向其他位置，解析见 `agate_common.py`）。

**脚本实现（改后）**：
- `check-retrospective.py:74-104` `_resolve_workspace(task_dir)`：向上找含 `.agate.env` 或 `agate-workspace/` 的最近祖先 → `agate_common.resolve_workspace(project_root)[0]`。
- `agate-render-dispatch-prompt.py:51-77` 同款，`main()` 在 `:222` 用它渲染 `{AGATE_WORKSPACE}`。
- `agate_common.resolve_workspace`（`agate_common.py:808-837`）优先级与文档逐字一致。

**结论**：ALIGNED。两条脚本此前用 `dirname(dirname(task_dir))` **绕过**了文档声明的权威解析器；本批把它们改回 `resolve_workspace`，即把脚本从「与文档不一致」改为「与文档一致」。

**RM-AG0082 侧**：协议文档对匿名化只有一句笼统描述——`agate/assets/templates/retrospective-template.md:150`「项目名/绝对路径等由 `agate-feedback.py` 做进一步脱敏」。收窄后的 `ABS_PATH_RE` 仍履行「绝对路径脱敏」，语义方向未变。**结论**：ALIGNED（过度收窄问题另见「重点结论 3」，属实现取舍而非文档不符）。

### A2: 脚本→文档对齐

**脚本变更**：见 A1 实现。**对应文档是否需要同步更新**：

- `agate/scripts/README.md` 的工具清单表（`:82` check-retrospective / `:87` agate-feedback / `:175` agate-render-dispatch-prompt）**只描述脚本用途**，不含「工作区如何推导」或「匿名化正则形态」的实现细节 ⇒ **无需同步**。
- `agate/tests/README.md:63` 只登记 `agate-feedback.py → unit/test_agate_feedback.py`，无需改。
- 无任何协议文档把旧的 `dirname(dirname(...))` 或旧正则写为「约定行为」（旧的仅在 TAG0015 的 `P2-design.md` 任务快照里，属冻结历史产物，按约定不回改）。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**A3a（已知连锁）**：本批只改 2 个脚本 + 3 个测试文件；两处修复本身**不需要**改动任何协议文档（文档早已声明权威解析器，见 A1）。

**A3b（主动推断的应被影响文件）——逐项核实**：

1. **同款 `dirname(dirname(...))` 是否真只有两处？→ 否，存在第三处**。
   - `grep -rn "dirname(os.path.dirname\|dirname(dirname" agate/ --include=*.py` 的命中按推导起点分类：
     - 以 **task_dir** 为起点（风险成立）的，共 4 行 / 3 个实例：`check-gate.py:1236`+`:1245`（**DEBT0016 已修**，走 resolve_workspace）、`check-retrospective.py:104`、`agate-render-dispatch-prompt.py:77`（本次修的两处），**外加 `check-gate.py:1928`**：
       ```python
       debt_file = os.path.join(
           os.path.dirname(os.path.dirname(task_dir)), "debt", "tech-debt.md"
       )
       ```
       它同样由 `task_dir` 两级 dirname 推导工作区来定位 `debt/tech-debt.md`（gate_p7 的 BDD-66 双向回指校验）。
     - 其余命中（`agate-dispatch.py:68`、`agate-advance.py:59`、`agate-next.py:87`、`agate_common.py:402/1239`、`check-structure-consistency.py:115`、`check-yaml-schema.py:118`、`agate-next-card.py:50`、`check-obligations.py:72`、`agate-inject-card.py:47`）均以 `__file__`/脚本路径为起点（推导 agate_root/rules），**与 task_dir 无关**，风险不成立。
   - `check-gate.py:1928` 由提交 **`3b0bd755`（TAG0050-P4 批 G3）**引入（`git log -L` 实证），**晚于** TAG0031 的同类扫描（2026-09-04）⇒ 当时「两处」的说法对扫描时点成立，但**现在仓库里实际有第三处**，且它既未被 DEBT0016 覆盖、也未被 DEBT0028 覆盖（DEBT0028 只登记 2 处）。
   - **风险不低**：check-gate.py 已在 `:47` `from agate_common import ... resolve_workspace ...`，修它成本极低；而 gate_p7 的失败模式是 `return 1`（**阻断 commit**），比 check-retrospective 的 WARNING-only 更重。
   - **结论**：NEEDS_HUMAN_REVIEW——本批应**顺手修掉**（一行，resolve_workspace 已可用）或**另登记新 DEBT**，二者择一；不建议静默留着。

2. **`{AGATE_WORKSPACE}` 占位符的消费方是否受影响？→ 只有渲染方本身**。
   `grep -rn "{AGATE_WORKSPACE}" agate/scripts/*.py`：真正做替换的只有 `agate-render-dispatch-prompt.py:227`；`agate-extract-context.py` **不消费**该占位符（`grep` 确认其只用 `os.path.join(task_dir, ...)`，无 `dirname(dirname(task_dir))`）。卡片/模板里的 `{AGATE_WORKSPACE}` 是**待渲染文本**，由本脚本消费 ⇒ 无需改动。**结论**：无其他受影响文件。

3. **`ABS_PATH_RE` 是否有其它消费点？→ 无**。
   `grep -rn "ABS_PATH_RE" agate/`（排除 `__pycache__`）：定义 `agate-feedback.py:46` + 唯一消费点 `agate-feedback.py:127`（`_anonymize` 内 `ABS_PATH_RE.sub`）。`_anonymize` 由 `:218-220` 三处调用（mechanism/execution/feedback section），均在 `agate-feedback.py` 内部。**结论**：收窄只影响本脚本。

4. **`agate/scripts/README.md` 是否需要同步？** 见 A2——无实现细节，无需改。

**结论**：**NEEDS_HUMAN_REVIEW**（第 1 项：第三处同款实例需人工决定「本批修 / 登记 DEBT」；第 2/3/4 项均已核实无其它受影响面）。

### A4: 测试覆盖

**新增测试**（本批 6 条）：
- `test_agate_feedback.py::test_rm_ag0082_chinese_slash_word_not_anonymized` / `test_rm_ag0082_real_absolute_paths_still_anonymized`
- `test_agate_render_dispatch_prompt.py::test_rm_ag0084_default_layout_workspace_placeholder` / `test_rm_ag0084_env_override_workspace_placeholder`
- `test_check_retrospective.py::test_rm_ag0084_default_layout_workspace_resolved` / `test_rm_ag0084_env_override_workspace_resolved`

覆盖了正反两面（默认布局 + `.agate.env` 覆盖；中文词不误伤 + 真实路径不退化），设计合理。

**最近一次全量实跑输出（本审查独立执行，`-n auto`）**：

```
# unit
2 failed, 2588 passed, 2 skipped in 56.08s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED agate/tests/unit/test_t42_p3_platform_selfcheck.py::test_t42_scan_is_runnable_and_clean_on_repo
# regression
81 passed in 1.34s
# integration
200 passed in 18.94s
# 本批 3 个改动测试文件
49 passed in 1.51s   （feedback 9 / render 23 / retrospective 17）
```

**MISALIGNED — 本批引入了一条测试回归**：
- `test_t42_scan_is_runnable_and_clean_on_repo` 断言「本仓 `agate/tests/` 全树平台假设扫描 0 命中」。本批新增用例 `test_agate_feedback.py:235`：
  ```python
  for abs_path in ("/home/alice/proj/secret", "/tmp/x/y", r"C:\Users\bob\p"):
  ```
  其中的 `/tmp/x/y` 命中 `check-platform-assumptions.py` 的 **R4** 规则（`/tmp([\s/"']|$)`）。独立复现：
  ```
  $ python3 agate/scripts/check-platform-assumptions.py agate/tests/
  R4 agate/tests/unit/test_agate_feedback.py:235     for abs_path in ("/home/alice/proj/secret", "/tmp/x/y", r"C:\Users\bob\p"):
  scan-exit=1
  ```
  **全树仅此 1 命中**，且该行是本批新增 ⇒ 回归由本批引入（H1 批的全量输出 `2309 passed / 1 failed(既有 opencode)` 显示当时 t42 是绿的）。
- 这同时违反 `AGENTS.md`「测试约定」的「不用 `/tmp`（用 pytest `tmp_path` fixture）」，以及本仓既有约定（见 `test_check_tdd_red_formatter.py:10`：pytest 侧改**运行时拼接**避免源码命中 R4）。
- **修复方向**：把 `/tmp/x/y` 改为运行时拼接（如 `"/tmp" + "/x/y"`）或在该行加 `# scan-exempt:` 标记（`check-platform-assumptions.py:93-95` 的行级豁免）。另 `/home/alice/...` 不触发任何规则，可保留。

**另一处覆盖缺口**：新用例只测了 3 个真实路径（`/home/alice/proj/secret`、`/tmp/x/y`、`C:\Users\bob\p`），**未覆盖**「2 段且顶层目录不在白名单」的绝对路径（如 `/data/secret`、`/proj/foo`）——正是收窄后漏脱敏的那一类（见「重点结论 3」）。测试无法守住该边界。

**结论**：**MISALIGNED**（新用例打破既有测试，须修）。

### A5: 下游影响 + 文档传播

- **破坏性变更**：无。修复是让脚本行为回到文档声明的权威解析，对既有标准布局项目零回归（默认布局 `dirname²` 与 `resolve_workspace` 结果本就一致，见「重点结论 1/2」）。
- **CHANGELOG 未同步**：H1 批（同系列，提交 `68f5f599`）在**同一提交内**更新了 `CHANGELOG.md`（`CHANGELOG.md | 15 ++`，`## [Unreleased] / ### 修复` 下含 RM-AG0090/0091/0092 三条）。本 H2 批工作区**未触及 `CHANGELOG.md`**（`git status` 仅 6 文件），`## [Unreleased]` 现有条目只有 H1 三条，**缺 RM-AG0082/DEBT0008 与 RM-AG0084/DEBT0028 两条**。按反向传播表「`CHANGELOG.md` 未更新 → A5 下游影响不完整」，应补（若计划在 commit 步骤补，请显式确认，勿漏）。
- **下游测试破坏**：见 A4（`test_t42_scan_is_runnable_and_clean_on_repo`）。这是本批最实的下游影响。
- **协议文档传播**：无需（见 A1/A2/A3b）。

**结论**：**MISALIGNED**（CHANGELOG 缺口 + 下游测试回归）。

### A6: 锚点表覆盖

- 本批**未新增协议规则 / 未新增脚本**，不涉及 CHECK 9 锚点表扩容。
- 被改的 3 个脚本（`check-retrospective.py` / `agate-feedback.py` / `agate-render-dispatch-prompt.py`）此前均已在 `agate/scripts/README.md` 工具清单登记；无新增 basename 需要补登记面（SG.6 / CHECK 10 面）。
- `check-protocol-consistency.py` 实跑 **0 ERROR**（414 frozen WARNING，均来自按设计不改的历史文件）：

```
  ✅ PASS  CHECK 16 任务数据契约快照冻结
  ...
  仅有 414 个 WARNING，无 ERROR。
exit=0
```

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-014「判据单一权威源」**（`agate/adr.md:533`）：「判据必须单源，文档可以复述」。本批修复的**方向正是**消除重复路径算术、归口到唯一权威 `agate_common.resolve_workspace`，与 ADR-014 一致。
- 轻微观察（不构成 MISALIGNED）：`_resolve_workspace` 的「向上找项目根」逻辑在 `check-retrospective.py:74-104` 与 `agate-render-dispatch-prompt.py:51-77` **各写一份**（check-gate.py 另有内联版）——权威解析器仍单源（`resolve_workspace`），但「找 project_root」这一辅助步骤重复了 3 份。DEBT0028 的 recommendation 允许「或等价单点权威封装」；若要更贴合 ADR-014，可考虑下沉为 `agate_common` 的一个小工具（非本批必须）。
- 未见需新增 ADR 的架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|------|------|------|
| 「旧行为 → `['/执行层面']` 新行为 → `[]`」 | `python3 -c "import re; old=re.compile(r'(?:[A-Za-z]:\\\\\|/)[^\s'\"\`]+'); new=re.compile(...); print(old.findall('机制/执行层面'), new.findall('机制/执行层面'))"` | **可复现**：OLD `['/执行层面']` / NEW `[]`（逐字一致）。 |
| 「63 passed」 | 未能找到产出它的命令；尝试 `pytest agate/tests/unit -k '...'` 多组、逐文件计数（3 个改动文件合跑 = **49 passed**）均不等于 63 | **不可复现**——无据，应删除或改记为「3 个改动测试文件 49 passed」。 |
| 「78 passed」 | 同上，未复现（`test_agate_feedback.py` 单独 9、`test_check_retrospective.py` 17、`test_agate_render_dispatch_prompt.py` 23） | **不可复现**——同上。 |
| 「95 passed」 | 同上，未复现 | **不可复现**——同上。 |
| （本审查补充）全量口径 | `python3 -m pytest agate/tests/unit -q -n auto` → `2 failed, 2588 passed, 2 skipped`；`regression` → `81 passed`；`integration` → `200 passed` | 权威计数。其中 1 failed 由本批引入（见 A4）。 |

**结论**：**MISALIGNED**——实施者报告中的「63/78/95 passed」无对应命令、不可复现，且**遗漏了本批引入的 t42 回归**（若当时跑的是全量，不可能看不到 2 failed 中的 1 条）。按 A8 原则应删除这些无据声称，改以上表可复现计数为准。

---

## 五项重点结论（对应派发问题）

### 1. `_resolve_workspace` 兜底是否与旧行为逐字等价？两种 import 写法在安装破损时是否一致？

- **`check-retrospective.py`：逐字等价**。旧 `os.path.dirname(os.path.dirname(os.path.abspath(task_dir.rstrip(os.sep))))` ≡ 新 `start = os.path.abspath(task_dir.rstrip(os.sep)); return os.path.dirname(os.path.dirname(start))`。
- **`agate-render-dispatch-prompt.py`：不逐字等价**。旧 `os.path.dirname(os.path.dirname(task_dir))`（**无** `abspath`/`rstrip`）；新兜底 `os.path.dirname(os.path.dirname(os.path.abspath(task_dir.rstrip(os.sep))))`。差异仅在**兜底分支**（向上找不到 `.agate.env`/`agate-workspace/`）且 task_dir 为相对路径/带尾分隔符时出现：
  - 实测（`cwd=/tmp/opencode/h2probe2`，`task_dir=plain/T1`，树内无任何 marker）：新兜底 = `/tmp/opencode/h2probe2`；旧 = `''`（空串）⇒ `{AGATE_WORKSPACE}` 由 `/tasks/T1/...` 变为 `/tmp/opencode/h2probe2/tasks/T1/...`。
  - 影响面：仅在「未初始化/无工作区标记」的边缘布局可见，且**新值（绝对）比旧值（空串）更正确**，故为**良性**差异；但 docstring「回退旧的两级 dirname 推导，**保持既有行为**」对 render 脚本**不严谨**（建议措辞改为「等价或更正确的两级推导」）。
- **import 写法一致性**：
  - `check-retrospective.py:86-89`：函数内 `import agate_common`，**只 catch `ImportError`**。
  - `agate-render-dispatch-prompt.py:29-34`：模块级 `from agate_common import resolve_workspace`，**catch `(ImportError, SystemExit)`**。
  - **「agate_common 缺失」时两者一致**（都触发 `ImportError` → 回退）。
  - **「agate_common 存在但 import 期 `sys.exit`」时不一致**：`agate_common.py:35-39` 在缺 `pyyaml` 时 `sys.exit(1)`。render 会捕获 `SystemExit` 回退；check-retrospective 只 catch `ImportError` → `SystemExit` 逃逸。**但实际不可达**：`check-retrospective.py:27` 在模块加载时先 `import agate_markers`，而 `agate_markers.py:28-32` 缺 yaml 时同样 `sys.exit(1)` ⇒ 缺 yaml 时脚本在导入期即退出，根本到不了 `_resolve_workspace`。故**生产行为一致**，但该 catch 面不一致是潜在隐患（建议统一为 `(ImportError, SystemExit)`）。

### 2. `.agate.env` 覆盖路径是否真的生效？（独立复现「旧推导错、新推导对」）

**是，独立复现成功**。构造 `/tmp/opencode/h2probe/proj`：`agate-workspace/tasks/T1/.state.yaml`（task_id=T1）+ `.agate.env`（`AGATE_WORKSPACE=custom-ws`）+ `custom-ws/debt/tech-debt.md`（登记 T1），默认位置 `agate-workspace/debt/` **不存在**：

```
$ python3 agate/scripts/check-retrospective.py agate-workspace/tasks/T1 agate-workspace/tasks/T1/.state.yaml
GATE RETRO: 建议复盘 — 发现机制缺口信号：
  - T1 关联的 DEBT/roadmap 条目已登记（可能存在机制缺口，建议复盘归因）
$ python3 -c "import os; print(os.path.dirname(os.path.dirname(os.path.abspath('agate-workspace/tasks/T1'))))"
/tmp/opencode/h2probe/proj/agate-workspace     # ← 旧推导指向默认位置（无 debt），读不到信号
```

render 侧同样复现：`.agate.env` 覆盖时 `{AGATE_WORKSPACE}` = `<root>/custom-ws`；无 `.agate.env` 默认布局时 = `<root>/agate-workspace`（均正确）。

### 3. `ABS_PATH_RE` 收窄是否漏掉真实敏感路径 / 有无过度收窄？

逐样本探针（`old.findall` vs `new.findall`）：

| 样本 | OLD | NEW | 期望 | 判定 |
|------|-----|-----|------|------|
| `机制/执行层面` | `['/执行层面']` | `[]` | 不脱敏 | ✅ 修复 |
| `P1/P2` / `/或` | `['/P2']` / `['/或']` | `[]` | 不脱敏 | ✅ 修复 |
| `/home/x` | ✅ | ✅ | 脱敏 | ✅ 保持 |
| `/tmp/a` / `/var/log/x` | ✅ | ✅ | 脱敏 | ✅ 保持 |
| `C:\Users\b` / `C:\Users\bob\p` | ✅ | ✅ | 脱敏 | ✅ 保持 |
| `/opt/a/b` / `/usr/local/x` | ✅ | ✅ | 脱敏 | ✅ 保持 |
| `/etc/hosts` / `/root/.ssh/id_rsa` / `/Users/alice/x` / `/srv/data/x` / `/mnt/c/Users` | ✅ | ✅ | 脱敏 | ✅ 保持 |
| `./x` / `a/b`（相对） | `['/x']` / `['/b']` | `[]` | 不脱敏 | ✅ 改进 |
| **`/proj/foo`** | `['/proj/foo']` | **`[]`** | 脱敏 | ❌ **漏脱敏** |
| **`/data/secret` / `/app/src`** | ✅ | **`[]`** | 脱敏 | ❌ **漏脱敏** |
| `机制/执行/流程/层面`（≥3 段中文连写） | `['/执行/流程/层面']` | `['/执行/流程/层面']` | — | ⚠️ 残留假阳（注释已承认） |

端到端确认（`AGATE_FEEDBACK=on agate-feedback.py`）：`泄露 /data/secret 和 /proj/foo 和 /home/alice/proj/secret` → `泄露 /data/secret 和 /proj/foo 和 <PATH>`（前两个**未脱敏**）。

- **真实敏感路径不退化**：文档/债务点名的两类（`/home/...`、`C:\Users\...`）以及所有「已知顶层目录 ≥2 段」路径均保持脱敏 ⇒ 与 DEBT0008 closure_criteria「判断能力不退化（既有 BDD-18 全绿）」在**其举例范围内**成立。
- **存在过度收窄（漏脱敏）**：规则 3「以 `/` 开头且 ≥3 段」把**「未知顶层目录 + 恰好 2 段」的绝对路径**（`/data/secret`、`/proj/foo`、`/app/src`）排除在脱敏之外。匿名化是**隐私功能**，这属**漏脱敏**侧。DEBT0008 的 recommendation 原本建议的是「加边界约束（斜杠前须是空白/行首/标点而非中日韩文字）或要求路径结构特征」，并未要求提高段数门槛；用「≥2 段即可 + 已知顶层白名单」即可同时修掉中文词误伤（`机制/执行层面` 命中的是 1 段 `/执行层面`）**且不丢 2 段真实路径**。
- **残留假阳**（≥3 段中文斜杠连写仍被脱敏）在注释中已显式承认，属「宁可多留不可漏」的自觉取舍，可接受。
- **结论**：本项标 **NEEDS_HUMAN_REVIEW**——「2 段未知顶层路径漏脱敏」是真实且可复现的隐私收窄，需人工确认是否收紧段数门槛（建议 ≥2 段 + 白名单），并**补一条 `/data/secret` 类回归用例**。

### 4. RM-AG0084 是否真只有两处？

**否——存在第三处同款实例 `check-gate.py:1928`**（gate_p7 定位 `debt/tech-debt.md`，由 `3b0bd755` 引入，晚于 TAG0031 扫描，未被 DEBT0016/DEBT0028 覆盖）。其余 `dirname(dirname(...))` 命中均以脚本自身路径为起点，不构成同类。详见 A3b 第 1 项。**建议**：本批顺手修（check-gate.py 已 import `resolve_workspace`）或另登记新 DEBT。

### 5. 声称逐条复现（见 A8）

- 「旧行为 → `['/执行层面']` / 新行为 → `[]`」：**逐字复现**。
- 「63 passed」/「78 passed」/「95 passed」：**均不可复现**（无对应命令）；本批 3 个改动测试文件合跑 = **49 passed**，全量 unit = **2588 passed / 2 failed**。实施者的声称**遗漏了本批引入的 t42 回归**。

---

## 需修复 / 待裁决清单

| # | 项 | 归属 | 动作 |
|---|----|------|------|
| 1 | 新用例 `test_agate_feedback.py:235` 的 `/tmp/x/y` 字面量打破 `test_t42_scan_is_runnable_and_clean_on_repo` | A4 / A5（**MISALIGNED**） | **必须修**：改运行时拼接或加 `# scan-exempt:` |
| 2 | `CHANGELOG.md` 未加 RM-AG0082/RM-AG0084 条目（H1 批先例） | A5（**MISALIGNED**） | **必须补**（或在 commit 步骤显式确认） |
| 3 | 实施者声称「63/78/95 passed」无据且遗漏 t42 回归 | A8（**MISALIGNED**） | 删除无据声称，改记可复现计数 |
| 4 | `check-gate.py:1928` 第三处同款 `dirname(dirname(task_dir))` | A3（NEEDS_HUMAN_REVIEW） | 本批修 或 另登记 DEBT |
| 5 | `ABS_PATH_RE` 漏脱敏「2 段未知顶层」绝对路径（`/data/secret`） | A1 重点结论 3（NEEDS_HUMAN_REVIEW） | 人工裁决是否收紧门槛 + 补回归用例 |

> 每条 NEEDS_HUMAN_REVIEW 需主 Agent 附 `[HUMAN_CONFIRMED: 日期 确认：理由]` 后方可 commit。
