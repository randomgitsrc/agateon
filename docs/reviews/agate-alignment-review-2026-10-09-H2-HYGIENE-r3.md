---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B / H2 第 3 轮——第 2 轮 4 项已改：三处工作区推导收敛为 agate_common 单源 helper（resolve_workspace_from_task_dir）+ 3 条回归用例 + CHANGELOG 措辞 + 匿名化注释残留面；本轮复核确认外部工作区回归已消除
files_changed: [CHANGELOG.md, agate/scripts/agate_common.py, agate/scripts/agate-feedback.py, agate/scripts/agate-render-dispatch-prompt.py, agate/scripts/check-gate.py, agate/scripts/check-retrospective.py, agate/tests/unit/test_agate_feedback.py, agate/tests/unit/test_agate_render_dispatch_prompt.py, agate/tests/unit/test_agate_workspace_resolve.py, agate/tests/unit/test_check_retrospective.py]
---

# 协议-脚本对齐审查（第 3 轮）

> 审查对象：分支 `hotfix/batch-b-hygiene`（**未提交**，改动在工作区）。全程只读——未改任何协议/脚本/测试，
> 未 commit / push。跑测试前后 `git status --porcelain` 一致（10 个被评审文件 + 审查留痕/成果文件）。
> 第 1/2 轮报告：`docs/reviews/agate-alignment-review-2026-10-09-H2-HYGIENE.md`、`...-r2.md`。
> 留痕：`docs/reviews/agate-alignment-2026-10-09-H2-HYGIENE-03.progress.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**结论：8 项全 ALIGNED，无 MISALIGNED / 无未确认的 NEEDS_HUMAN_REVIEW ⇒ 可 commit。**
第 2 轮 4 项**均已确实修好**；第 2 轮的核心回归（外部工作区多套一层）已通过「三处收敛为单源 helper」
**从结构上消除**，并有能抓到旧实现的回归用例守护。仅有 1 项**不阻断的观察**（gate_p4 未随本批统一，
见 A3）。

---

## 第 2 轮 4 项逐条核实

| 项 | 第 2 轮问题 | 本轮核实 | 证据 |
|----|------------|----------|------|
| 1 | 第三处 `check-gate.py` 外部工作区回归 | **✅ 已修（且结构性消除）** | 见下 A3 |
| 2 | 第三处缺用例 | **✅ 已补 3 条** | 见下 A4 |
| 3 | CHANGELOG 措辞（「两处」/「向上找项目根」不符） | **✅ 已改** | `CHANGELOG.md` 现写「**三处**…统一改用 `agate_common.resolve_workspace_from_task_dir`（**单源实现**：向上找含 `.agate.env` 或 `agate-workspace/` 的项目根后交 `resolve_workspace`；找不到则回退旧推导）」——与实现逐字一致 |
| 4 | 匿名化注释未声明残留面 | **✅ 已补** | `agate-feedback.py` 注释新增「**已知残留漏脱敏面**：首段为 CJK 的真实路径 / 单段绝对路径」+ 取舍与替代方向（消费方用更精确来源，而非放宽正则） |

---

## 逐项审查

### A1: 文档→脚本对齐

**协议文档**：`agate/SETUP.md:381-391`、`agate/WORKFLOW.md:85` 声明工作区经 `.agate.env` /
`AGATE_TASKS_DIR` 覆盖、解析归口 `agate_common.resolve_workspace`；`retrospective-template.md:150`
声明「绝对路径等由 `agate-feedback.py` 脱敏」。

**脚本实现**：三处工作区推导收敛到 `agate_common.resolve_workspace_from_task_dir`
（`agate_common.py:840-869`）——walk-up 找含 `.agate.env` 或 `agate-workspace/` 的最近祖先 →
`resolve_workspace`；找不到 → `dirname²`。与文档声明的解析语义一致。匿名化正则（`agate-feedback.py`）
收窄后仍履行「绝对路径脱敏」，并显式声明残留面。

**结论**：ALIGNED。

### A2: 脚本→文档对齐

`CHANGELOG.md` 新增两条：① 工作区推导（现写「**三处**」且机制描述 = 实现，第 2 轮 2 处瑕疵已消）；
② 匿名化正则（含残留面取舍）。`agate/scripts/README.md` 工具清单无需改（见 A6 观察）。
**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**三处是否都委托单源 helper？→ 是**（`grep` 实证）：
- `check-retrospective.py:74-84`：本地 `_resolve_workspace` 用 `hasattr(agate_common, "resolve_workspace_from_task_dir")` 守卫后委托；不可用 → 回退。
- `agate-render-dispatch-prompt.py:29-36,57-59`：模块级 import 委托；不可用 → 回退。
- `check-gate.py:47-57,1939-1942`：import 委托；不可用 → 回退。

**外部工作区回归是否消除？→ 是（用真实代码路径实测）**。
`importlib` 加载 `check-gate.py`，monkeypatch 聚合器以抵达 debt 解析段（`resolve_workspace_from_task_dir`
用真实函数），三个场景：

```
A 默认布局      debt_file=<root>/agate-workspace/debt/tech-debt.md   ✅
B .agate.env 覆盖 debt_file=<root>/custom-ws/debt/tech-debt.md        ✅
C 外部工作区     debt_file=<ext-ws>/debt/tech-debt.md                 ✅（不再多套 agate-workspace）
```

- C 场景即第 2 轮的回归点（`AGATE_WORKSPACE=` 指向项目外、task_dir 在 git 仓库外）：旧 run_git 版给
  `<ext-ws>/agate-workspace/debt/...`（错），新 helper 给 `<ext-ws>/debt/...`（对）。
- 另两处（check-retrospective / render）在 C 场景经 CLI 实测亦正确。

**是否还有第四处同款？→ 纯 `dirname²` 绕过已无；gate_p4 为**观察项（不阻断）**：
`grep -rn "dirname(dirname\|dirname(os.path.dirname" agate/scripts/*.py` 的 task_dir 起点命中，
除三处 helper 回退外，仅 `check-gate.py:1241-1253`（**gate_p4**，DEBT0016）。gate_p4 **确实调用了
`resolve_workspace`**（故不算 RM-AG0084 的「绕过」同款），但它用 `run_git --show-toplevel` 取
project_root，**保留了与第 2 轮第三处同源的潜在 bug**：外部工作区场景 run_git 失败 → project_root
= `dirname²` = 工作区 → `resolve_workspace(工作区)` 多套一层 → `code_map_file` 算错。**区别是 gate_p4
为 WARNING-only（fail-open，不 return 1）**，且属既有 DEBT0016 范围、非本批引入。
**观察（不阻断）**：既然已有了单源 helper，gate_p4 可一并改用它以消除同类潜在 bug 并达成「单源」；
本次不阻断（预存、fail-open、超出本批 RM-AG0084 范围）。

**结论**：ALIGNED（本批三处已收敛且回归消除；gate_p4 为预存观察项）。

### A4: 测试覆盖

**新增 3 条**（`agate/tests/unit/test_agate_workspace_resolve.py:223-266`）：
`test_rm_ag0084_from_task_dir_default_layout` / `..._env_override` /
`..._external_workspace_not_double_nested`。

**「3 条能否抓到旧实现」→ 能**（scratch 复现旧 run_git 逻辑）：
```
A default (git repo)            OLD(r2) OK
B override (git repo)           OLD(r2) OK
C external (task outside repo)  OLD(r2) BAD  ← 外部用例会转红
```
外部用例的 task_dir 位于非 git 的 pytest tmp 下，旧 run_git 版必失败 → 返回 `<ws>/agate-workspace`
→ 断言 `== ext` 失败 ⇒ 该用例**确能守护本类回归**。

**最近一次全量实跑（本审查独立执行，`-n auto`）**：
```
$ python3 -m pytest agate/tests -q -n auto
1 failed, 2895 passed, 2 skipped in 85.98s
FAILED ...test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
        （既有环境项：opencode CLI 无 `debug agent` 子命令，与本 diff 无关）
$ pytest agate/tests/unit/test_agate_workspace_resolve.py -q -n auto   → 15 passed
$ pytest test_agate_feedback.py test_agate_render_dispatch_prompt.py test_check_retrospective.py -q -n auto → 49 passed
$ pytest test_check_platform_assumptions.py test_t42_p3_platform_selfcheck.py -q → 21 passed
```

**残余观察（不阻断）**：3 条新用例测的是 **helper** 本身；`check-gate.py` 对 helper 的**委托集成**
（gate_p7 的 debt 解析段）仍无直接用例。鉴于「找 project_root」已单源且该 helper 已被正/反例覆盖、
委托行本身为一行三元表达式，风险已大幅收敛；若要更严，可加一条经 `_gate_p7_structured` 的集成用例。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播

- 第 2 轮的下游回归（外部工作区）已消除（A3 实测）。
- 破坏性变更：无。降级路径（`agate_common` 不可用）仍回退旧推导（见 A8 详列）。
- CHANGELOG 已同步；无其它协议文档需传播（工作区解析文档早已声明权威源）。

**结论**：ALIGNED。

### A6: 锚点表覆盖

- 未新增协议规则 / 脚本；新增的是 `agate_common.py` 内的**函数**（非脚本），不涉及 CHECK 9 / SG.6 /
  CHECK 10 的脚本登记面。
- **观察（不阻断）**：`agate/scripts/README.md:102` 的 `agate_common.py` 函数清单（以「等」收尾）
  未列新函数 `resolve_workspace_from_task_dir`；**无机械校验要求**（清单非穷举），可按需补充以利发现。
- `check-protocol-consistency.py` 实跑 **0 ERROR**（414 frozen WARNING，均历史冻结文件）。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-014「判据单一权威源」**：本批把三处「找 project_root + 解析工作区」收敛为**单一实现**
  （`resolve_workspace_from_task_dir`），比第 2 轮（三份重复实现）**更贴合** ADR-014；`check-gate.py`
  的注释也显式记录「为何不用 `git rev-parse --show-toplevel`」（含外部工作区反例），把判据理由固化。
- 未见需新增 ADR 的架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称（本轮） | 命令 | 结论 |
|------|------|------|
| 「新增 `resolve_workspace_from_task_dir`，三处均改为调用它」 | `grep -rn "resolve_workspace_from_task_dir" agate/scripts/*.py` | **✅ 成立**（定义 1 处 + 三处委托） |
| 「外部工作区不再多套一层」 | 真实 `_gate_p7_structured` 实测（A3）+ helper 探针 | **✅ 成立**（C 返回 `<ext-ws>`） |
| 「默认布局 / `.agate.env` 覆盖仍正确」 | helper 探针 A/B | **✅ 成立** |
| 「新增 3 条用例，最后一条即回归用例」 | `pytest test_agate_workspace_resolve.py -q -n auto` → 15 passed；scratch 旧版在 C 转红 | **✅ 成立** |
| 「CHANGELOG 改为三处…单源实现」 | `git diff CHANGELOG.md` | **✅ 成立**（文字与实现一致） |
| 「匿名化注释补残留面」 | `git diff agate/scripts/agate-feedback.py` | **✅ 成立** |
| 「全量 2892→…」 | `python3 -m pytest agate/tests -q -n auto` | **✅ `1 failed(环境) / 2895 passed / 2 skipped`** |

**降级路径（`agate_common` 不可用）等价性核实**（派发问题）：
```
[abs]      retro 旧 == 新回退（逐字等价）；render/gate 同
[rel]      retro 旧 == 新回退；render/gate 新回退加 abspath（旧 'ws' → 新 '/cwd/ws'）
[trailing] retro 旧 == 新回退；render/gate 旧 '/a/ws/tasks' → 新 '/a/ws'（strip 尾分隔符）
```
- `check-retrospective.py` 回退**逐字等价**旧行为；`agate-render-dispatch-prompt.py` / `check-gate.py`
  的回退**多加了 `abspath`/`rstrip`**，仅相对路径 / 尾分隔符输入时与旧不同，且新值更正确 ⇒ **良性**。
- 注：`check-retrospective.py` 用 `hasattr` 守卫（agate_common 存在但缺新函数时也回退），比另两处的
  「import 成败」更稳；三处降级语义一致（都回退旧推导）。

**结论**：ALIGNED。

---

## 需处理清单（本轮）

| # | 项 | 归属 | 严重度 | 动作 |
|---|----|------|--------|------|
| — | 无阻断项 | — | — | — |
| 1 | `check-gate.py:1241-1253`（gate_p4，DEBT0016）仍用 `run_git --show-toplevel` 取 project_root，保留同类外部工作区潜在 bug（**WARNING-only**，预存、非本批引入） | A3 观察 | 低（不阻断） | 可选：随本批一并改用单源 helper（达成真正单源）；或留待 DEBT0016 后续 |
| 2 | `agate/scripts/README.md:102` 函数清单未列新函数 | A6 观察 | 低 | 可选补充（无机械校验要求） |
| 3 | `check-gate.py` 对 helper 的委托集成无端到端用例 | A4 观察 | 低 | 可选补一条经 `_gate_p7_structured` 的集成用例 |

> 无 NEEDS_HUMAN_REVIEW 项；上述均为**不阻断**的可选改进。**结论：可 commit。**
