---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B / H2 第 4 轮——落实 r3 两条可选改进：gate_p4 也改用单源 helper（并移除已无用的 resolve_workspace import）、test_check_gate 注入点同步、scripts/README.md 补登记新函数
files_changed: [agate/scripts/check-gate.py, agate/scripts/README.md, agate/tests/unit/test_check_gate.py]
---

# 协议-脚本对齐审查（第 4 轮 · 简短）

> 分支 `hotfix/batch-b-hygiene`（**未提交**）。只读——未改任何文件，未 commit/push。
> 跑测试前后 `git status --porcelain` 一致（12 个被评审文件 + 审查留痕/成果文件）。
> 本轮范围 = r3 两条可选改进 + 连带改动。留痕：`docs/reviews/agate-alignment-2026-10-09-H2-HYGIENE-04.progress.md`。

## 结论：**可 commit**（5 项全通过，无新问题）

| # | 验证项 | 结论 |
|---|--------|------|
| 1 | gate_p4 改动正确性（外部/默认/覆盖 + 降级） | ✅ 通过 |
| 2 | 无新问题（`resolve_workspace` 残留 / NameError / 测试全绿） | ✅ 通过 |
| 3 | 测试注入点改动保持判别力 | ✅ 通过 |
| 4 | 反向传播（bdd_9 等同类用例 / CHECK 10） | ✅ 通过 |
| 5 | A8 声称逐条可复现 | ✅ 通过 |

---

## 逐项

### 1. gate_p4 改动正确性

`check-gate.py:1229-1245`：CODE-MAP 解析改为 `_workspace = resolve_workspace_from_task_dir(task_dir)`；
import 块移除 `resolve_workspace`、保留 `resolve_workspace_from_task_dir`。

**真实 `gate_p4` 实测**（复刻 `test_tag0031_bdd_8` 的 task/git 场景 + spy 记录 helper 返回值）：

```
A 默认布局      resolve -> <root>/agate-workspace      ✅
B .agate.env 覆盖 resolve -> <root>/custom-ws           ✅
C 外部工作区     resolve -> <ext-ws>                     ✅（不再多套 agate-workspace）
```
C 即 r3 观察点（`AGATE_WORKSPACE=` 指向项目外、task_dir 在 git 仓库外）：旧 run_git 版会给
`<ext-ws>/agate-workspace`，新实现给 `<ext-ws>` ⇒ **同类潜在 bug 已消除**。

**降级路径**（`agate_common` 不可用 ⇒ `resolve_workspace_from_task_dir = None`）：`code_map_file` 停在
初始值 `dirname²(abspath(task_dir))/agents/CODE-MAP.md`——**与旧行为逐字等价**（旧代码初始值同式，
且 `resolve_workspace is None` 时同样保持不变）。该分支 WARNING-only（fail-open）不变。

### 2. 无新问题

- **`resolve_workspace` 残留**：`grep -n "\bresolve_workspace\b" agate/scripts/check-gate.py` 仅命中
  **注释**（`1242` / `1929` 的说明文字），**无任何代码引用** ⇒ 移除 import 无 `NameError` 风险。
- **测试全绿**：
  - `python3 -m pytest agate/tests/unit/test_check_gate.py -q -n auto` → **222 passed**。
  - `python3 -m pytest agate/tests -q -n auto` → **1 failed, 2895 passed, 2 skipped**
    （1 failed = 既有环境项 `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，
    opencode CLI 无 `debug agent` 子命令，与本 diff 无关）。

### 3. 测试注入点改动保持判别力

`test_check_gate.py::test_tag0031_bdd_8_gate_p4_code_map_uses_resolve_workspace` 的注入点由
`mod.resolve_workspace` 改为 `mod.resolve_workspace_from_task_dir`（**意图不变**：须走权威解析器）。

**scratch 判别力复现**（同场景，改注入值）：
```
注入重定向 resolver            → 「新增文件核对表」WARNING 触发 = True   （说明确实调用了注入的权威解析器）
resolver=None（模拟本地算术）  → WARNING 触发 = False                  （说明本地算术会被判失败）
```
⇒ 该用例**仍能**区分「调用权威解析器」与「仍在本地 `dirname(dirname(...))` 算术」，判别力保留。

### 4. 反向传播

- 同类用例：`pytest ... -k "tag0031_bdd_8 or tag0031_bdd_9 or code_map or resolve_workspace"` → **3 passed**；
  `-k tag0031_bdd_9` 单跑 → **1 passed**（`.agate.env` 非标准嵌套经 CLI 的端到端用例仍绿）。
- `agate/scripts/README.md:102` 补登记 `resolve_workspace_from_task_dir`（函数名，非文件引用）。
  `check-protocol-consistency.py` → **0 ERROR**；WARNING 总数 **414（与 r3 相同，未增）**——
  CHECK 10 的 1 条 WARN 为**预存 frozen**（「叙事文件引旧文件名」如 `scripts/check-p6-provenance.sh`
  在 CHANGELOG.md:2377），非本次 README 改动引入。

### 5. A8 声称-命令绑定

| 声称 | 命令 | 结论 |
|------|------|------|
| 「gate_p4 改用 `resolve_workspace_from_task_dir`，移除 `resolve_workspace` import」 | `git diff agate/scripts/check-gate.py` + `grep -n "\bresolve_workspace\b" agate/scripts/check-gate.py` | **✅ 成立**（代码改；bare 名仅剩注释） |
| 「外部工作区不再多套一层」 | 真实 `gate_p4` 实测（上述） | **✅ 成立**（C → `<ext-ws>`） |
| 「测试注入点由 `resolve_workspace` 改为 `resolve_workspace_from_task_dir`」 | `git diff agate/tests/unit/test_check_gate.py` | **✅ 成立** |
| 「README 补登记」 | `git diff agate/scripts/README.md` | **✅ 成立** |
| 「test_check_gate.py 222 passed」 | `pytest agate/tests/unit/test_check_gate.py -q -n auto` | **✅ 逐字成立** |
| 「全量 2895 passed / 2 skipped / 1 failed（既有 opencode 环境项）」 | `pytest agate/tests -q -n auto` | **✅ 逐字成立** |

---

**最终结论：两条可选改进已正确落地，无新引入问题，测试与一致性全绿 ⇒ 可 commit。**
