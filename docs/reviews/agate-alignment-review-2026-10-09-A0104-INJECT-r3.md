---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0104 r3 复核——只验 r2 未决项（2y 与 inject 口径不一致）是否按「判据单源」闭合（agate_common.AGATE_CARD_PLACEHOLDER_RE 共用）
files_changed: [agate/scripts/agate_common.py, agate/scripts/agate-card-inject.py, agate/scripts/pre-commit-gate.py, agate/WORKFLOW.md, agate/scripts/agate-inject-card.py, agate/tests/unit/test_agate_inject_card.py, agate/tests/integration/test_pre_commit_hook.py, CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md]
---

# 协议-脚本对齐审查（r3 复核）

**只读声明**：本审查未修改任何协议/脚本/测试，未 commit/push；scratch 复现均在一次性副本内「创建→操作→清理」。
**⚠️ 状态变更（如实上报）**：审查进行期间，主 Agent 已将本批改动**提交**为 `034982f9`（分支 `hotfix/batch-a-inject-card` 现与 `origin/...` 一致）。本审查读到的工作区内容与该提交内容**一致**（`git show --stat 034982f9` = 我审的 10 个改动文件 + r1/r2 报告）。**下述结论适用于提交 `034982f9`。**

## 五项结论

| # | 验证项 | 结论 |
|---|--------|------|
| 1 | 口径是否真的单源 | **是** ✓（常量 == inject 回退字面，byte-identical；两处同 `re.DOTALL`；无第四处代码写死） |
| 2 | 两向分歧是否消除 | **是** ✓（r2 两个反例 + 正常/散文共 4 例，2y 与 inject 判定全部一致） |
| 3 | `ImportError` 回退是否同口径 | **是** ✓（回退字面与常量逐字相同；单独运行 injector 实测注入成功） |
| 4 | 是否引入新问题 | **否（无可阻塞项）**；一处非阻塞观察见下 |
| 5 | A8 声称-命令绑定 | 逐条可复现（见下） |

## 逐项详情

### 1. 判据单源 ✓
- `agate/scripts/agate_common.py:843`：`AGATE_CARD_PLACEHOLDER_RE = r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)"`（单源常量）。
- `agate/scripts/agate-card-inject.py:17-20`：`from agate_common import AGATE_CARD_PLACEHOLDER_RE as pattern`（`except ImportError` 回退字面）。
- `agate/scripts/pre-commit-gate.py:1126`：`re.search(AGATE_CARD_PLACEHOLDER_RE, _txt, flags=re.DOTALL)`（经 `:49` 从 `agate_common` 导入）。
- **逐字同一正则**：程序比对 常量字面 == 回退字面 → **byte-identical: True**；两处 **均 `flags=re.DOTALL`**（inject 用 `pattern`、2y 用常量，同一 flag）。
- **无第四处**：`git grep` 全仓 `AGATE_CARD_PLACEHOLDER_RE` 仅 4 处（常量 / inject 导入 / 2y 导入+使用 / WORKFLOW 描述）；正则**字面**仅 2 处代码（常量 + inject 回退）。其余命中为 `archived/docs-2026-08/*`、`agate-workspace/tasks/TAG0027-*/P2-progress.md` 等**历史文档引用**（非判据）。另 `.worktrees/blog-post11/agate/scripts/agate-card-inject.py:17` 是**另一个 git worktree（分支 `docs/blog-post11`，gitignored）**的旧副本，非本分支。

### 2. 两向分歧消除 ✓（逐例实测 rc，真实 2y + inject）
| 场景（r2 反例） | 2y commit rc | inject rc | 一致 |
|---|---|---|---|
| case1 `abc <!-- AGATE_CARD_START -->`（原「2y 更严」误伤） | 0 | 0 | ✓ |
| case2 `<!-- AGATE_CARD_END -->` 在 START 之前（原「2y 更松」漏放） | 1 | 1 | ✓ |
| case3 仅散文提及（无注释对） | 1 | 1 | ✓ |
| case4 正常独占行占位符 | 0 | 0 | ✓ |

（对照 r2：case1 曾 `2y=1/inject=0`，case2 曾 `2y=0/inject=1`。）

### 3. `ImportError` 回退同口径 ✓
- 回退字面 `r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)"` 与常量逐字相同（见 1）。
- 实测：把 `agate-card-inject.py` 单独复制到临时目录（无 `agate_common` 可导入）运行 → `rc=0`，`{占位}` 被 `CARD` 正确替换 ⇒ 回退生效且口径一致。

### 4. 是否引入新问题
- **`agate_common` import 失败路径**：`pre-commit-gate.py` 本就 `from agate_common import (...)`，加一个名字**不改变**其 `except Exception → sys.exit(1)` 的 fail-closed 行为；且脚本与其 `agate_common` 同目录（同版本），不存在版本错配。
- **`agate-card-inject.py` 新增对 `agate_common` 的传递依赖**（新）：`except ImportError` 覆盖「模块缺失」→ 回退同口径 ✓；但**不覆盖**「`agate_common` 在、pyyaml 缺」——`agate_common` 在缺 pyyaml 时 `sys.exit(1)`（`agate_common.py:35-37`，SystemExit 非 ImportError）→ 实测 injector `rc=1`、未注入。**评估：非阻塞**——pyyaml 是整套 gate 的硬依赖（`pre-commit-gate.py` 已依赖），实际运行环境必有；且缺 pyyaml 时 fail-closed 合理。
- **既有 dispatch-context 存量**：834 个 `P{n}-dispatch-context*.md`，与**同一正则**兼容 **833**（唯一不兼容 = 本就缺占位符的 `agate-workspace/tasks/TAG0050-task-data-contract/P2-dispatch-context-sync-residuals.md`，2y 与 inject 判定**相同**）⇒ **无误伤**。
- `ruff 0.16.4`（`~/.venvs/agate-dev/bin/ruff check agate/`）→ **All checks passed**；`check-protocol-consistency.py` → **0 ERROR**（424 frozen WARNING，与 r1/r2 同）；`WORKFLOW.md:364` 2y 行 **5 列**（与表头一致）。

### 5. A8 声称-命令绑定

| 声称 | 命令 | 结论 |
|---|---|---|
| `82 passed` | `pytest agate/tests/unit/test_agate_inject_card.py agate/tests/unit/test_agate_card_inject.py agate/tests/integration/test_pre_commit_hook.py -q`（serial） | ✓ 82 passed（`-n auto` 亦得 82 passed；首跑曾 1 flake，见下） |
| `2903 passed`（全量） | `pytest agate/tests/ --reruns 1 -n auto -q` | ✓ **`1 failed, 2903 passed, 2 skipped`**——2903 passed 复现；唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`（**环境项**：opencode CLI 已将 `debug agent` 改名 `debug agents`，与本批无关，测试文件不在 diff） |
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✓ rc=0，0 ERROR |
| `ruff All checks passed` | `~/.venvs/agate-dev/bin/ruff check agate/` | ✓ All checks passed（ruff 0.16.4） |

**flaky 说明（如实）**：首次对上述 3 文件用 `-n auto` 时 `test_m1_forward_jump_p0_to_p7_blocked` **1 failed**；单独跑通过、`-n auto` 复跑 2 次均 82 passed、CI 口径全量（`--reruns 1`）通过 ⇒ **并行 flake**，与 2y/dispatch-context 无关（该用例只测 P0→P7 状态转移）。

## 是否可 commit

**可 commit（r2 唯一未决项已闭合）。** 判据单源已落地（常量 + 两处共用、同 `re.DOTALL`），r2 的两向分歧（前缀文本误伤 / END 前置漏放）已实测消除，`ImportError` 回退同口径，存量无误伤，测试/一致性/ruff 全绿。唯一非阻塞观察：injector 新增对 `agate_common`/pyyaml 的传递依赖（pyyaml 为硬依赖，实践无影响）。

> 备注：本批改动已由主 Agent 于审查期间提交为 `034982f9`；本结论适用于该提交。
