---
agent: cso
phase: P4
task_id: TAG0050
parent: P4-implementation.md
trace_id: TAG0050-P4-20261007
type: review
status: approved
---

# P4-review-cso-rereview — TAG0050 批 A1 C8 安全面复评

- **复评对象**：TAG0050 批 A1 的 C8 整改（`P4-dispatch-context-implementer-A1-cso-fix.md` 的 G1–G3），
  未提交，基于 HEAD `1d5aab2`（分支 `feat/TAG0050-task-data-contract`）。
- **范围**：只复核原 `P4-review-cso.md` 的 **F-1（HIGH/BLOCKER）** 及 **G2/F-2、G3/F-3** 是否闭合
  + 是否引入新问题；不重开全量、不重做设计。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本**（`/tmp/opencode/cso-rereview/`）上独立复现；
  另用 `git archive HEAD` 取 **pre-fix 协议树**做对照，区分「本次引入」与「旧洞残留」。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/` 副本上进行；真实仓库只读，
  复评前后 `git status --porcelain` 逐行一致（48 行，另见「验证留痕」）。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **MEDIUM**（1 项残留，**非阻塞**） |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1（F-1R，非阻塞残留） |
| LOW | 0（F-4/F-5/F-6 归属登记已核对） |
| F-1（指定两形态） | **ALIGNED（已闭合）** |
| G2/F-2 | **ALIGNED（声明到位）** |
| G3/F-3 | **ALIGNED（已闭合）** |
| 是否阻塞发布 | **否** |
| status | `approved` |

## 二、F-1 复核（原 HIGH/BLOCKER）

### 2.1 整改内容（静态核对）

- 规则 4 现处理 **R（改名）** 与 **D（删除）**：`agate/scripts/pre-commit-gate.py:350-368`。
  源路径是账本（`src_path.endswith("/gate-events.jsonl")`）时，若 `dst_path is not None`
  且 `_is_task_dir_rename(...)` 为真 → 豁免；否则按删除判 ERROR（`sys.exit(1)`）。
- 豁免判据 `_is_task_dir_rename`（`:275-285`）：目标须以 `/gate-events.jsonl` 结尾，
  **且** `_dir_moved_away`（`:264-272`，`git ls-files -- <源任务目录>` 为空 ⇒ 整目录被带走）为真。
- 新增负向/正向用例：`agate/tests/integration/test_tag0050_a0_a1_ledger.py`
  BDD-23（同目录 `.bak` → rc≠0）、BDD-24（移入别任务目录 → rc≠0）、BDD-25（整目录改名 → rc=0）。

### 2.2 可复现证据（独立复现，不依赖被测用例）

仓外副本 `/tmp/opencode/cso-rereview/`，`AGATE_ROOT=<副本>/agate`：

| 场景 | 命令（要点） | rc | 判定 |
|---|---|---|---|
| F-1a 同目录 `.bak` 改名 | `git mv …/gate-events.jsonl …/gate-events.bak` | **1** | 拦截 ✅ |
| F-1b 移入别任务目录 | `git mv TAG0001/gate-events.jsonl TAG0002/gate-events.jsonl` | **1** | 拦截 ✅ |
| F-1c 整目录改名（合法） | `git mv …/tasks/TAG0001 …/tasks/TAG0001-renamed` | **0** | 放行 ✅ |
| F-1d 改名到同任务子目录 | `git mv gate-events.jsonl sub/gate-events.jsonl` | **1** | 拦截 ✅ |
| F-1e 改名 + 改内容（D+A 路径） | 改名后改写目标内容破坏相似度 | **1** | 拦截 ✅ |

F-1a/b 命中同一 ERROR：

```
GATE: 含创建/迁入事件的账本被删除/移走（agate-workspace/tasks/TAG0001/gate-events.jsonl）
      ——不得删除/截空/移走（防止降回 legacy）；迁移请用 agate-task-init.py
```

被测新增用例在副本内：`4 passed, 26 deselected`（BDD-23/24/25/26）。
**结论：F-1 的两种 `git mv` 形态确实 rc=1；整目录 `git mv` 仍放行。ALIGNED。**

## 三、F-1R（MEDIUM，非阻塞残留）：目录改名豁免判据过宽

- **位置**：`agate/scripts/pre-commit-gate.py:275-285`（`_is_task_dir_rename`）。
- **事实**：豁免只校验「目标以 `/gate-events.jsonl` 结尾」+「源任务目录在索引中为空」，
  **未校验目标就是被改名的源目录**。因此，先**清空源任务目录的索引**、再把账本 `git mv`
  进**既有的别的任务目录**，同样满足豁免条件。
- **可复现证据**（副本 `cases/f1_residual_a`）：

  ```
  $ git rm --cached -q agate-workspace/tasks/TAG0001/.state.yaml     # 源目录索引清空
  $ git mv agate-workspace/tasks/TAG0001/gate-events.jsonl \
           agate-workspace/tasks/TAG0002/gate-events.jsonl
  $ AGATE_ROOT=<副本>/agate python3 <副本>/agate/scripts/pre-commit-gate.py
  rc=0                      # ❌ 未拦截
  # 提交后（task_level 实测）：
  task_level(tasks/TAG0001) before = 1
  task_level(tasks/TAG0001) after  = None    # ❌ 静默降回 legacy
  .state.yaml 仍在磁盘（untracked）= True
  ```

  对照：`git rm -r` 整任务删除（P3）与「整目录改名后再把账本移走」（全 tracked）均 rc=1，
  说明仅此形态可绕。

- **性质澄清（据实，勿扩大）**：
  - **非本次整改新引入**：用 pre-fix 协议树（`git archive HEAD` → `agate-head/`）跑同一序列
    同样 `rc=0`。这是旧洞的一个残留形态，整改已把「保持任务完整、单次 `git mv` 摘账本」这一
    主要路径堵死（F-1a/b 由 rc=0 变 rc=1）。
  - **触发须复合操作**：必须先把源任务目录的索引**清空**（对最小任务即 `git rm[-‑cached] .state.yaml`），
    再把账本移入既有任务目录——不是一次 `git mv` 可达。
  - **不产生「已提交的 legacy 任务」**：源任务 `.state.yaml` 已从索引移除，任一克隆上都**不存在**
    该任务；降回 legacy 只发生在攻击者本地工作区（`.state.yaml` untracked 残留）。就本机而言
    `task_level` 确实 1→None，故仍列为残留。
- **加固建议（一处小改，可选）**：豁免再加一条必要条件——目标任务目录**在 HEAD 中不存在**
  （即确为改名而来的新目录），或要求源 `.state.yaml` 也被改入目标目录。例如：

  ```python
  def _is_task_dir_rename(repo_root, old_task_rel, dst_ledger_path):
      if not dst_ledger_path.endswith("/" + LEDGER_FILENAME):
          return False
      dst_task_rel = dst_ledger_path[: -len("/" + LEDGER_FILENAME)]
      if _head_has_path(repo_root, dst_task_rel + "/.state.yaml"):
          return False            # 目标是既有任务目录 ⇒ 不是目录改名
      return _dir_moved_away(repo_root, old_task_rel)
  ```

  修复后建议补一条负向用例（「清空源目录 + 移账本到既有任务目录 → rc≠0」）。
  **注意**：此残留**不会被批 A2 的 CI 逐提交回放捕获**（回放复用同一 `pre-commit-gate.py` 逻辑），
  故若不在 A1 顺手加固，建议登记 DEBT 由后续批处理。
- **严重性判定**：MEDIUM（与 F-1 同一不变量，但需复合且自毁性操作、且不产生已提交的 legacy 任务）。
  **非阻塞**——原 F-1 的 BLOCKER 属性（一次 `git mv` 即静默降级）已消除。

## 四、F-3 复核（原 MEDIUM）

### 4.1 整改内容

`agate/scripts/pre-commit-gate.py:487-494`：全局面扫描的跳过条件由「有暂存 `.state.yaml`」
收紧为「有暂存 **且工作区仍存在** 的 `.state.yaml`」——`.state.yaml` 以删除方式暂存
（`git rm`）时不跳过，不再与主循环 `os.path.isfile`（`:554-555`）互相让路。

### 4.2 可复现证据

| 场景 | rc | 判定 |
|---|---|---|
| `git rm .state.yaml` + 目录内写 `[PROD_TOUCHED]` 并 `git add` | **1** | 拦截 ✅ |
| 对照：正常暂存 `.state.yaml` + `[PROD_TOUCHED]` | **1** | 拦截 ✅（无回归） |

`git rm .state.yaml` 场景命中：

```
GATE: [PROD_TOUCHED] 检测到生产环境接触（），commit 中止
```

被测用例 BDD-26 在副本内通过。**结论：F-3 已闭合。ALIGNED。**

## 五、G2/F-2 复核（原 MEDIUM）：声明是否到位、口径是否一致

| 交付面 | 现状 | 判定 |
|---|---|---|
| 设计 §8 第 12 项归属段 | `design-tag0050-task-data-contract.md` 新增「第 12 项的 R6 归属（G2）」：A1 的 R6 只承诺 check-gate 面，第 12 项由**批 A2** 的 `agate-ci-verify` 逐提交回放承担 | ✅ |
| `r6-allowlist.yaml` 头部 | 新增「可达性声明（G2）」：`gate: pre-commit`/`ci-verify`/`check-obligations` 的规则不在 A1 R6 覆盖内，`required_ids` 只校验存在不校验可达 | ✅ |
| `r6-differential.sh` 头部 | 新增「覆盖范围（G2 显式声明）」同口径；`_rule_matches` 补 `task_scope`（D03 `specific:T090` 不再形同虚设） | ✅ |
| `P4-implementation.md` §10 G2 | 明记「选择 (b) 显式声明」+ 理由 + 归属 | ✅ |
| F-5（LOW） | `r6-differential.sh` 增加**运行后** `git status --porcelain` 自核验（`RC=$?` 捕获 + 运行后复查 + `exit "$RC"`） | ✅ 已修 |

三处声明口径**互相一致**（均指向「A1 = check-gate 面 / 第 12 项 → A2」），与设计 §2.4 的 A2 定义吻合。
**结论：G2 声明到位、与设计口径一致。ALIGNED。**

## 六、F-4 / F-5 / F-6 归属登记核对（不要求 A1 修）

| 项 | 要求 | 现状 | 判定 |
|---|---|---|---|
| F-4（LOW） | 属批 C | `P4-implementation.md` §10「其余发现」明记「属批 C 的 P2 §3.1 规格（`markers.yaml` + `agate_markers.pattern()`），不在 A1 修复范围」；批 C 红灯用例 BDD-54/55 在副本内仍红（预期） | ✅ 登记如实 |
| F-5（LOW） | 酌情 | 已顺手修复（见 §五） | ✅ |
| F-6（LOW） | 酌情 | `P4-implementation.md` §10 明记「已知 DESIGN_GAP，登记不改」 | ✅ 登记如实 |

## 七、是否引入新问题（回归检查）

| 检查 | 结果 |
|---|---|
| 正常提交（暂存 `.state.yaml`、无 marker） | rc=0（无回归）✅ |
| `test_tag0050_a0_a1_ledger.py` 新增 4 用例（BDD-23..26） | 4 passed ✅ |
| `test_pre_commit_hook.py` + `test_tag0050_prod_touched.py`（副本内） | 92 passed；仅 BDD-54/55（批 C 预期红）与 BDD-21（副本缺 `agate-workspace/` 的副本伪影）失败，非 A1 回归 ✅ |
| 平台假设 | `r6-differential.sh` 的 python 候选改为带引号（避开 `check-platform-assumptions` R2 误报），无裸 `python3`/硬编码 PATH/系统临时目录字面量 ✅ |
| 其它文件 | 未发现整改碰坏其它文件或破坏 §8 兼容承诺 ✅ |

## 八、STRIDE 矩阵（针对 A1 整改面）

| 威胁 | 面 | 评估 | 关联 |
|---|---|---|---|
| **S**poofing | 任务身份/等级 | 等级由账本首行 `task_created` 记录；`agent` 字段工具拒绝改写 ✓ | — |
| **T**ampering | 账本内容 | 只追加（规则 3）✓；D 删除与 R 改名（保持任务完整）均被拦 ✓ | F-1 闭合 |
| **T**ampering | 账本摘除（复合） | 清空源目录索引 + 移账本入既有任务目录 → 仍可绕（本地降级） | **F-1R** |
| **T**ampering | 判定依据 | 消费方均改依契约 ✓；依赖账本在场（F-1 主路径已闭合）| F-1 闭合 |
| **R**epudiation | 创建/升级留痕 | `task_created`/`task_adopted`/`task_upgraded` 规则齐备 ✓；CI 兜底属 A2（已声明） | G2 |
| **I**nfo disclosure | 账本/产出 | 未见敏感数据暴露面 | — |
| **D**oS | 安全门误拦 | 扫描面扩大误拦风险低；F4 否定写法误拦属批 C | F-4 |
| **E**levation | 阶段/gate 推进 | 规则 7 后半（非 legacy 按暂存产出重跑 gate）已实现 ✓ | — |

## 九、验证留痕与环境隔离

- 仓外副本：`/tmp/opencode/cso-rereview/`（`agate/`+`docs/`+`agate-workspace/` 工作树拷贝；
  `agate-head/` = `git archive HEAD` 的 pre-fix 协议树）；复现脚本 `repro.py`..`repro8.py`。
- 真实仓库只做只读命令（`git status/diff/show/archive`、`sed`、`grep`、`ls`）；复评前后
  `git status --porcelain` 逐行一致（48 行）。
- 未编辑任何被评审文件；未执行任何破坏性/写仓命令。
- `[PROD_NOT_TOUCHED]` 未接触生产环境。

## 十、返回给主 Agent

- **File**: `agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso-rereview.md`
- **Status**: `approved`
- **最高严重级别**：MEDIUM（1 项非阻塞残留 F-1R）
- **各级计数**：CRITICAL 0 / HIGH 0 / MEDIUM 1 / LOW 0
- **逐条判定**：F-1（指定两形态）ALIGNED；G2/F-2 ALIGNED；G3/F-3 ALIGNED；F-4/F-5/F-6 归属登记如实。
- **是否阻塞发布**：**否**。原 F-1 的 BLOCKER 属性（一次 `git mv` 即静默降级）已消除。
  建议：F-1R（豁免判据过宽）在 A1 顺手加固（§三 给出改法），或登记 DEBT——因其**不被 A2 的 CI 回放覆盖**。
