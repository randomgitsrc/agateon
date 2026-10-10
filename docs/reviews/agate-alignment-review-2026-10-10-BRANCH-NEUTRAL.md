---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: 协议不再假设项目分支（agate-changes/agate-ci-verify 经 agate_common.default_branch 单源解析）+ 新增中立项目本地 hook 扩展点 <git-common-dir>/hooks/pre-commit-local
files_changed:
  - AGENTS.md
  - CHANGELOG.md
  - agate/scripts/README.md
  - agate/scripts/agate-changes.py
  - agate/scripts/agate-ci-verify.py
  - agate/scripts/agate_common.py
  - agate/scripts/pre-commit-gate.py
  - agate/tests/integration/test_pre_commit_hook.py
  - .githooks/pre-commit-local（新增未追踪；agateon 项目层策略）
---

# 协议-脚本对齐审查

**审查对象**：分支 `hotfix/protocol-branch-neutral`（**未提交**，改动在工作区）。
**方法**：仓外全量副本 `/tmp/opencode/agateon-copy`（含 `.git`）独立复跑；写类操作（pytest / 变异 / 差分 /
一致性 / ruff）全部在副本上跑；**实仓只读**（跑前跑后 `git status` 只看到被评审的改动集，未被污染）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | NEEDS_HUMAN_REVIEW |
| A4 | 测试覆盖 | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空清单：经实测无既有用例转红） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | NEEDS_HUMAN_REVIEW |
| A8 | 声称-命令绑定 | 见 §A8（逐条给命令；无据声称已指出） |

**总体判定**：**无 MISALIGNED**。功能正确、边界经实测、既有全量套件无新增红。两条 **NEEDS_HUMAN_REVIEW**
（A3 反向传播的两个"是否也单源/对称"取舍、A7 的 ADR-014 完整性）须人工确认；按本角色「闭环规则」，
未确认的 NEEDS_HUMAN_REVIEW 等同 MISALIGNED——**确认可接受后即可 commit**。

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**文档声明**（`agate/scripts/README.md:94`）：
> （扩展点）`<git-common-dir>/hooks/pre-commit-local` … 存在且**可执行** ⇒ `pre-commit-gate.py` 先跑它、
> **非 0 即中止提交** … 缺省不写 = 行为逐字节不变。解析经 `git rev-parse --git-path hooks`（尊重 `core.hooksPath`）。

**脚本实现**（`agate/scripts/pre-commit-gate.py:697-717`）：
```python
def _run_project_local_hook(repo_root):
    rc, out = run_git(["rev-parse", "--git-path", "hooks"])
    if rc != 0 or not (out or "").strip():
        return 0
    hooks_dir = (out or "").strip().rstrip("/")
    if not os.path.isabs(hooks_dir):
        hooks_dir = os.path.join(repo_root, hooks_dir)
    path = os.path.join(hooks_dir, "pre-commit-local")
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        return 0
    try:
        return subprocess.run([path], cwd=repo_root).returncode
    except OSError:
        return 0
```
以及 `main()` 最前（`agate/scripts/pre-commit-gate.py:733`）：
```python
if _run_project_local_hook(repo_root) != 0:
    sys.stderr.write("GATE LOCAL: 项目本地 pre-commit-local 未通过 ⇒ 本次提交中止\n" ...)
    sys.exit(1)
```

**实测**：README 声明的语义逐条成立（见「重点 2」边界表）。`git rev-parse --git-path hooks` 确实尊重
`core.hooksPath`（绝对 / 相对均实测命中）。**结论：ALIGNED**（一个 cwd 相关的小偏离见「重点 2」，不影响
git 实际的 hook 调用路径）。

### A2: 脚本→文档对齐 — ALIGNED

- `default_branch` 单源（`agate/scripts/agate_common.py:1291-1309`）在 docstring 写明解析顺序与调用方，
  并被 `agate-changes.py:24-27`（`--check-upstream` 上游变更范围）与 `agate-ci-verify.py:116-118`
  （`_default_branch` 委托，回放基准）共用；CHANGELOG（`CHANGELOG.md:215-224`）把这两点都写明。
- 协议文档对默认分支一律写 `origin/<默认分支>` 占位（`agate/UPGRADING.md:300,302`、`agate/scripts/README.md:125`），
  **未见任何写死 `origin/main` 的协议断言**（`grep` 全仓 `agate/` 仅剩 `commit-msg-self-gate.py:117` 的注释
  与 `agate_common.py:1294` 的 docstring——均非判据）。**结论：ALIGNED**。

### A3: 一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW

**A3a 连锁（已知衍生改动）**：CHANGELOG ✓、`agate/scripts/README.md` ✓、`AGENTS.md`
（`AGENTS.md:70-77`，项目层安装命令）✓。`UPGRADING.md` 无需改（未发布、非破坏性）。

**A3b 反向传播（主动推断"应被影响但未在 diff"的文件）**：

| 发现 | 位置 | 处置建议 |
|------|------|---------|
| **第三处 default-branch 实现**未随单源化 | `agate/scripts/check-mvwu.py:297 _default_branch_base`（`origin/HEAD` → `refs/heads/main` → `refs/heads/master`，`--observe` 观测用、**不阻断**） | 本次只单源了 2/3 处。语义与 `default_branch` 不同（本地 ref、要求非空 range），是否也单源属**取舍** → 人工裁决（或登记 DEBT） |
| **扩展点未对称支持 `pre-push`** | 仅新增 `pre-commit-local`；`pre-push-gate.py` 无对应扩展位 | push 阶段同为「项目策略」位；是否需要 `pre-push-local` 属**设计取舍** → 人工裁决 |
| **未复用单源 `git_hooks_dir`** | 新函数自实现 hooks-dir 解析，而协议已有 `agate_common.git_hooks_dir()`（`agate_common.py:92-118`，明示是「git 实际会执行 hooks 的目录」唯一基准，且 `clean_location_env=True` 中和 `GIT_DIR`） | 建议复用；实测 `cwd=子目录 + core.hooksPath 相对` 时新函数漏跑（见重点 2） → 人工裁决 |
| `test_selfgate_trailer_integrity.py:92` 硬编码基线 `("origin/main","main")` | 测试（后置守卫，非协议运行时） | 同上，属是否单源的取舍 |
| `.github/workflows/protocol-tests.yml:91 BASE="origin/main"`、`deploy-pages.yml on.branches=[main]` | **agateon 本仓 CI**（非协议本体、非 `agate/`） | **不算越界**——项目允许用 main，正是本改动要保护的场景 |

**结论：NEEDS_HUMAN_REVIEW**——三处"是否也单源/对称/复用"是真实的设计取舍（尤其 `check-mvwu`
第三副本），交付人工确认；其余传播已到位。

### A4: 测试覆盖 — ALIGNED

**新增用例**（`agate/tests/integration/test_pre_commit_hook.py:2129-2163`
`test_project_local_hook_extension_point`）：`exit 3` ⇒ 阻断；`exit 0` ⇒ 放行；`0644` ⇒ 跳过。

**全量实跑（CI 口径，副本）**：
```
cd /tmp/opencode/agateon-copy
python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
→ 1 failed, 2914 passed, 3 skipped, 1 rerun in 82.58s
```
**唯一 failed** = `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
——**环境性**，与被评改动无关：实跑 `opencode debug agent orchestrator` 报
`Unknown subcommand "agent" for "opencode debug"`（本机 opencode CLI 版本无该子命令）。该用例只经
`agate-setup.py` + opencode CLI，不触及本次任何改动文件。

**变异测试（副本）**：把 `if _run_project_local_hook(repo_root) != 0:` 改为 `if False:` → 新用例 **FAIL**
（`assert 0 != 0`），恢复后 **passed** ⇒ 用例对新逻辑**有辨别力**（非恒绿）。

**覆盖缺口（minor，非阻断）**：
- 新用例 `@pytest.mark.skipif(sys.platform == "win32")` ⇒ **Windows 路径无测试**（见重点 2 的 Windows 语义）；
- `agate_common.default_branch` / `agate-changes.py` 的默认分支解析**无新增单测**（等价性由既有
  `test_agate_ci_verify.py` 覆盖 ci-verify 侧；`agate-changes.py` 侧见「重点 1」的手工差分）。

**结论：ALIGNED**（有实跑数字，缺口如实标注）。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED（空清单）

- **既有用例转红**：**经实测无既有用例转红**——全量 `-n auto --reruns 1` 仅 1 条 **环境性** failed
  （`test_bdd_43_opencode_registration_and_debug_agent`，opencode CLI 子命令缺失），改动前后均会红、与本次
  改动无因果关系。
- **夹具更新**：**无需**。`test_pre_commit_hook.py` 是**新增用例**（追加于文件末尾），不改任何既有
  fixture/helper；`conftest.py` 未改。新用例自建 `pre-commit-local` 于 `git_repo` 夹具仓库，不依赖 `.githooks/`。

### A5: 下游影响 + 文档传播 — ALIGNED

- **破坏性**：**非破坏性**。`pre-commit-local` 是非标准 git hook 名（git 不识别），既有项目几乎不可能
  已占用；占用者才会首次被运行，属预留命名。`default_branch` 解析对既有 `origin/HEAD`/`origin/main` 项目
  **行为等价**（见重点 1）。
- **CHANGELOG**：已标注（`CHANGELOG.md:215-224`，`[Unreleased]` / 修复）。建议：该条实为「修复 + 新机制」，
  若要更准确可考虑另立小节（非阻断）。
- **文档传播**：`agate/scripts/README.md`（脚本单源）✓、`AGENTS.md`（项目层安装命令）✓。`WORKFLOW.md`
  「Pre-commit 检查总览」自称"检查集唯一事实源"，但它列的是**协议检查**；扩展点是**中立分派**、非协议检查
  ——不复制清单是符合「单一权威」原则的。`git-integration.md:166` 亦只指针引用、不自带清单，无回归。
- **dogfooding 事实（如实登记）**：本仓 `.git/hooks/pre-commit` 现指向 `~/.agate/scripts/pre-commit-gate.sh`
  （**稳定版**，无扩展点）⇒ `pre-commit-local` 软链**当前尚未生效**；需本改动随版本发布 + 安装后，守卫才在
  「commit 时」真正拦截。
- **结论：ALIGNED**。

### A6: 锚点表覆盖 — ALIGNED

`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **仅 432 WARNING（均为冻结
历史文件），0 ERROR，exit 0**；CHECK 9 PASS。新增的 `agate/scripts/README.md:94` 行经差分核验**未新增**任何
WARNING（去掉该行后仍 432）。扩展点非协议规则，无需新增锚点。**结论：ALIGNED**。

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

- **ADR-014（判据单一权威源）**：本改动的**方向与之相符**（`default_branch` 单源、`agate-ci-verify` 委托，
  消除一处副本）。**但完整性未达 ADR-014 的严口径**：① `check-mvwu.py:297` 仍是**第三份**默认分支判定；
  ② 新扩展点自实现 hooks-dir 解析，未复用同为"判据单源"的 `agate_common.git_hooks_dir()`。ADR-014 后果条明言
  "消费方不得自带副本"，且在"声明单源 ≠ 已经单源"上踩过坑——此处同类。
- **ADR-002（可判定性）/ ADR-006（同源盲区）**：无冲突。
- **结论：NEEDS_HUMAN_REVIEW**（无 MISALIGNED；设计原则项按规定只有 ALIGNED / NEEDS_HUMAN_REVIEW）。
  建议：本次至少**复用 `git_hooks_dir`**，`check-mvwu` 第三副本登记 DEBT 或同批单源。

### A8: 声称-命令绑定

| # | 声称（改动/报告内） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | 「0 ERROR」 | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（副本） | **成立**（exit 0；0 ERROR、432 frozen WARN） |
| 2 | 「2915 passed」 | `python3 -m pytest agate/tests/ -n auto --reruns 1 -q`（副本） | **不逐字成立**：实际 `2914 passed, 1 failed(环境性), 3 skipped, 1 rerun`。少数的那 1 条是环境性 failed（opencode 子命令），**不得称"全绿"** |
| 3 | 「ruff 通过」 | `~/.venvs/agate-dev/bin/ruff check agate/` = `ruff 0.16.4`（副本） | **成立**（All checks passed） |
| 4 | 「守卫在 main 拦、feature 放行」 | ① `.githooks/pre-commit-local` 直跑：`main→rc1 / master→rc1 / feature→rc0 / detached→rc0`；② 集成用例（exit3 阻断 / exit0 放行 / 0644 跳过）；③ 变异后用例 FAIL | **成立** |
| 5 | 「缺省不写 = 行为逐字节不变」 | 全量套件中所有不建 `pre-commit-local` 的 commit 用例全绿；`_run_project_local_hook` 无命中时返回 0、无 stdout/stderr 副作用 | **成立** |
| 6 | 「Windows 下不误拦」 | 查证 CPython 语义：Windows `os.access(X_OK)` 等同 `F_OK`（存在即 True）+ 新函数 `except OSError: return 0` | **成立**（见重点 2；但该路径**无测试**，属覆盖缺口已登记 A4） |

无"无法给出命令"的声称。

---

## 五项重点结论

### 重点 1：`default_branch` 行为等价性 — 等价（实测）

- **等价性（副本，构造真 origin）**：默认分支分别为 `main/master/develop/trunk` 时，新实现与原
  `_default_branch` 逻辑**逐一相同**，且等于真实默认分支（非恒 `main`）。无 `origin/HEAD` 时回退
  `origin/main` → `origin/master` → `"main"`，与原逻辑一致。
- **无 origin / 非仓库**：`default_branch(None)` 与非 git 目录均返回 `"main"`，**不崩**。
- **`agate-changes.py` 鲁棒性（真脚本、仓外 scratch agate 仓库）**：
  - 无 origin 默认分支 ⇒ 兜底 `main`，`git log v1.0.0..origin/main` 失败 ⇒ 不列出清单、**不崩、rc=0**。
  - **改前/改后差分**（default=master/develop）：feature 版列出 `自 v1.0.0 以来的变更（1 commits）`；
    把脚本退回硬编码 `origin/main` 后**不列清单**（原缺陷复现）⇒ 修复有效。
- **既有用例**：`agate/tests/unit/test_agate_ci_verify.py` 等全绿（含 `origin/HEAD` 缺失场景）。
- **`core.hooksPath` 与 default_branch 无耦合**（后者只用 remote refs）。

### 重点 2：扩展点中立性与安全性 — 正确（含一处 minor 偏离）

**逐字节不变（正例）**：缺省（无 `-local`）⇒ 返回 0、无输出，`main()` 不 `sys.exit` ⇒ 与改动前一致；
全量套件中所有不建 `-local` 的 commit 用例全绿。

**边界实测**（`_run_project_local_hook` 直调，副本）：

| 场景 | rc | 期望 |
|---|---|---|
| 无 `pre-commit-local` | 0 | 跳过 ✓ |
| 可执行、`exit 3` | 3 | 中止 ✓ |
| `0644` 不可执行 | 0 | 跳过 ✓ |
| 名为 `pre-commit-local` 的**目录** | 0 | 跳过（`isfile` 为假）✓ |
| **悬空软链** | 0 | 跳过（`isfile` 跟随为假）✓ |
| `core.hooksPath`=**绝对** 目录含可执行 `exit 3` | 3 | 命中 ✓（尊重覆盖） |
| `core.hooksPath`=**相对** 目录含可执行 `exit 4`（cwd=repo 顶层） | 4 | 命中 ✓ |
| 非 git 目录 | 0 | 跳过 ✓ |
| 可执行但内容非法（无 shebang） | 0 | `subprocess` 抛 `OSError` ⇒ 跳过 ✓ |

**Windows 语义**：CPython 在 Windows 上 `os.access(path, os.X_OK)` **等同 `F_OK`**（任何存在的文件返回
True）——因此 Windows 上"存在的 `pre-commit-local`"会被运行，这与 git 在 Windows 按存在性执行 hook 的
语义**一致**；且只有**非 0** 才阻断、`OSError` 一律退化为跳过 ⇒ **不存在"把 0644 当可执行 ⇒ 误拦"**。
（注：该模式与仓库既有 `agate-summary.py:70`、`check-mvwu.py:247` 完全同款，非新引入的平台假设。）

**minor 偏离**：新函数自实现 hooks-dir 解析，**未复用** `agate_common.git_hooks_dir()`（该函数 docstring
明示其是"git 实际会执行 hooks 的目录"唯一基准，并用 `clean_location_env=True` 中和 `GIT_DIR`；且以
`cwd=repo_root` 解析相对 `core.hooksPath`）。实测：`cwd=子目录 + core.hooksPath 相对` 时新函数返回 0
（漏跑），`git_hooks_dir(repo)` 正确解析。**但** git 调用 hook 时 cwd = 工作树顶层，此偏离在真实
hook 路径下不出现 ⇒ 记为建议（NEEDS_HUMAN_REVIEW），非功能缺陷。

### 重点 3：分层是否守住 — 守住

- **协议本体 `agate/` 内无任何分支策略**：`grep` 全 `agate/`，`origin/main|origin/master` 仅剩
  `agate_common.py:1294` 的 docstring 与 `commit-msg-self-gate.py:117` 的注释（均非判据）；无"禁止直提"
  类规则。唯一沾边的 `agate/UPGRADING.md:1150` 是**设置建议**（"分支保护规则…选择受保护分支（如 `main`）"），
  非判据。
- **策略只在项目层**：`.githooks/pre-commit-local`（禁 `main/master` 直提）+ `AGENTS.md:70-77`（安装命令）。
- **反向核（删 `.githooks/` 协议行为是否完全不变）**：`grep` 全仓确认**无任何 `agate/` 文件引用
  `.githooks`**（仅 `AGENTS.md`/`CHANGELOG.md`/`.githooks` 自身引用）；协议测试自建夹具仓库、不读 `.githooks`。
  ⇒ 删除 `.githooks/` 只影响本仓 `.git/hooks/pre-commit-local` 软链（变悬空、协议侧 `os.path.isfile` 为假 ⇒ 跳过），
  **协议行为不变**。分层守住。

### 重点 4：是否遗漏同类越界 — 无协议越界；有"可单源但未单源"

- **协议层无遗漏**：`agate/` 内无写死默认分支的**判据**（见重点 3）。
- **可单源未单源**（非越界，属 ADR-014 完整性）：`check-mvwu.py:297`（第三副本）、
  `test_selfgate_trailer_integrity.py:92`（测试基线）。
- **非越界（项目层，正是本改动要保护的）**：`.github/workflows/*` 用 `origin/main`、`deploy-pages.yml`
  `on.branches:[main]`——agateon 自己的 CI；`docs/guides/*` 的 `origin/main`——agateon 自己的开发文档。
- ⇒ 见 A3b / A7。

### 重点 5：A4b + A8 实跑数字 — 已给（勿称全绿）

见 §A4 / §A8。**一句话**：副本 `-n auto --reruns 1` = **2914 passed / 1 failed（环境性）/ 3 skipped /
1 rerun / 82.58s**；`0 ERROR`；`ruff 0.16.4` 全通过；"守卫在 main 拦、feature 放行"经脚本直跑 + 集成用例
+ 变异三重验证成立。**不得称"全绿"**（1 条环境性 failed）。

---

## 是否可 commit

**结论：可 commit（无 MISALIGNED）——但先人工确认 2 条 NEEDS_HUMAN_REVIEW。**

- 阻断项：**无 MISALIGNED**。
- 待人工裁决（本角色的 NEEDS_HUMAN_REVIEW，须配 `[HUMAN_CONFIRMED: 日期 确认：理由]`，否则等同 MISALIGNED）：
  1. **A3/A7 — ADR-014 完整性**：是否本次即复用 `agate_common.git_hooks_dir()`；`check-mvwu.py` 第三副本
     是登记 DEBT 还是同批单源。
  2. **A3 — 对称性/取舍**：是否同时提供 `pre-push-local` 扩展位。
- 附：提交前须 `git add .githooks/`（当前未追踪，`git status` 显示 `?? .githooks/`），否则
  「受版本控制的 `.githooks/pre-commit-local`」这一声称不成立；CHANGELOG 已写。
- 建议（非阻断）：为 `agate-changes.py` 的默认分支解析补一条单测；`install-hook.py` 的备份/替换语义
  现在天然与扩展点**对齐**（项目 hook 存活于 `-local`，`pre-commit` 仍由协议管理，`_backup` 不会动 `-local`）
  ——可在 `install-hook.py` docstring 或 `AGENTS.md` 补一句说明（可选）。
```
