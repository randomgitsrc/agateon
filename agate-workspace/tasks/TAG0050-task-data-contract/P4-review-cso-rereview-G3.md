---
type: review
phase: P4
task_id: TAG0050
parent: P4-implementation-G3.md
trace_id: TAG0050-P4-20261008
agent: cso
status: approved
---
# P4-review-cso（第 2 轮复审）— TAG0050 批 G3（D+E+F）安全维度聚焦复审

- **评审对象**：TAG0050 合批 G3 的 **C8 第 2 轮整改（fix2）**——`P4-implementation-G3.md §9`；
  HEAD `b746d07d`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
- **范围**：只核第 1 轮 cso 的 **F-1/F-2**（MEDIUM）是否闭合 + **F-3..F-6**（LOW）是否已修/已声明，
  并查整改是否**引入新的安全阻断**（fail-closed 是否误伤合法路径、语义统一是否漏消费方）。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本** `/tmp/opencode/csoG3rr/`（`cp -r agate`；
  手工构造非 legacy 任务 TAG901）上做可复现验证。不改被评审文件、不写仓。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/csoG3rr/` 下完成。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **LOW**（F-1/F-2 已闭合；无新增 MEDIUM+） |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 2（新增观察，均纵深缺口/口径说明，非阻断；F-3..F-6 复核见三） |
| F-1 / F-2 判定 | **ALIGNED（闭合）** |
| 是否阻塞发布 | **否** —— F-1 fail-closed 且文案可区分；F-2 子目录声明文件缺 frontmatter 已判 ERROR；无新门禁绕过 |
| status | `approved` |

## 二、F-1 / F-2 独立验证（命令 + 输出）

> 副本根 `R=/tmp/opencode/csoG3rr`；任务 `T=$R/work/T901-test-task`（账本首行 `task_created` level=1）。
> 全部经 `AGATE_ROOT=$R/agate` 运行副本内脚本。

### F-1 — `cmd_run` 事件缺 `sha256` → fail-closed，且与「sha256 不匹配」可区分

直接调唯一解析入口 `agate_common.resolve_evidence_ref(T, "run:1")`（`agate_common.py:1692-1749`）：

```
[a_missing_sha256] path=None err='run:1 的 cmd_run 事件不完整（缺 k/log/sha256 字段，无法核验，fail-closed）'
[b_event_absent ] path=None err='run:1 的 cmd_run 事件缺失（无法核验 sha256，fail-closed）'
[c_correct_sha  ] path=<...>/runs/1.log err=None
[d_sha_mismatch ] path=None err='run:1 的 sha256 与 cmd_run 事件不一致（事件 deadbeef…，实际 56b94b…）'
[e_empty_sha256 ] path=None err='run:1 的 cmd_run 事件不完整（缺 k/log/sha256 字段，无法核验，fail-closed）'
[f_empty_log    ] path=None err='run:1 的 cmd_run 事件不完整（缺 k/log/sha256 字段，无法核验，fail-closed）'
```

真 `check-gate.py P6`（结构化 `results` 引用 `run:1`）：

```
(a) 事件缺 sha256   → rc=1  GATE P6: … run:1 的 cmd_run 事件不完整（缺 k/log/sha256 字段，无法核验，fail-closed）（D3）
(b) sha256 不一致   → rc=1  GATE P6: … run:1 的 sha256 与 cmd_run 事件不一致（事件 000…，实际 56b9…）（D3）
(c) sha256 正确     → rc=2  GATE P6: 结构化 results 判据 D1–D10 通过
```

**判定 ALIGNED。** 第 1 轮 F-1 的「字段缺失即静默放行」分支已消除：`k`/`log`/`sha256`
任一缺失/空/非字符串 → **fail-closed**（`:1720-1730`），且与「sha256 不匹配」（`:1737-1741`）
**文案可区分**。

**未误伤合法路径**：`cmd_run` 的唯一生产者是 `agate-run.py`（全仓 grep 确认），其 `--task`
路径恒写 k/log/sha256（`agate-run.py:249` → `_record_cmd_run`）；非 `--task` 路径不写 `k`，
不会被 `run:<k>` 匹配（`str(None)!="1"`），故无 false-positive。测试
`test_cso_f1_run_event_missing_sha256_fail_closed` 在副本内 **passed**。

### F-2 — 非 legacy 任务 `P4-implementation/` 子目录缺 frontmatter → ERROR

真 `check-frontmatter.py`（非 legacy 任务 TAG901）：

```
P4-implementation/direct.md         （无 frontmatter）→ rc=1  「非 legacy 任务的声明文件缺 frontmatter 块…」
P4-implementation/sub/nested.md     （无 frontmatter）→ rc=1  「…缺 frontmatter 块…」
P4-implementation-batch1.md         （无 frontmatter）→ rc=1  （顶层对照）
P4-implementation/withfm.md         （有 frontmatter）→ rc=0
P1-requirements.md                  （缺 packages/domains）→ rc=1  （既有 schema，非本项）
LEG-impl/P4-implementation/direct.md（legacy，无账本）→ rc=0  （§8 兼容不变）
```

匹配语义单源（`agate_common.match_declaration_file` / `declaration_file_paths`，`:1768-1829`）：

```
patterns = [... '*-review.md', 'P4-implementation-*.md', 'P4-implementation/**/*.md']
枚举 declaration_file_paths(T) ⊇ 命中 match_declaration_file(fp,T,patterns)
  P4-implementation/direct.md   -> True（枚举与命中一致）
  P4-implementation/sub/nested.md -> True
  P4-implementation-batch1.md   -> True
  P6-evidence/ev.log            -> False
task_dir_for_file(P4-implementation/direct.md) == 任务根  ✓
```

**判定 ALIGNED。** 第 1 轮 F-2 的逃逸向量（`fnmatch` 对 `P4-implementation/**/*.md` 的
**直接子文件**不命中 + `task_dir=dirname(file)` 恒 legacy）已闭合：`check-frontmatter.py:54`
与 `pre-commit-gate.py:602` 均走 `match_declaration_file`；`check-frontmatter.py:65/121` 改经
`task_dir_for_file` 向上定位任务根。关键不变式：**命中面 ⊇ 枚举面**（`match` 先判
`ap in matched`，再对 basename-only 通配加宽），故聚合面读到的任何声明文件都被 frontmatter
强制覆盖——**无「未匹配即免检」逃逸**。测试 `test_cso_f2_p4_implementation_subdir_requires_frontmatter`
/ `test_cso_f2_nested_subdir_requires_frontmatter` 在副本内 **passed**。

**消费方单源核对**：全仓 `declaration_files` 消费方共 6 处，均已改走单源——
`check-gate._aggregate_list`、`check-scope-resolved`、`check-retrospective`（枚举，
`declaration_file_paths`）；`check-frontmatter._is_declaration_file`、`pre-commit-gate._is_declaration_path`、
`agate-md-field-set._declared_safety_keys`（命中，`match_declaration_file`）。全仓无第 7 消费方、
无残留 `declaration_globs` 键（`check-gate.py:1762-1776` 确认键已回归 `declaration_files`）。

## 三、F-3..F-6 复核

| # | 原问题 | 处置 | 独立核验 | 判定 |
|---|---|---|---|---|
| F-3 | 空 `run:` 日志免检 | 已修（`agate_common.py:1742-1748` 补 `getsize==0`） | 空日志 + 正确 sha → `run:1 日志为空文件（D3：证据须非空）`；测试 passed | **ALIGNED** |
| F-4 | `blocker_count` 未登记系统字段 | 已登记（`level-1.yaml:104-106` `writer: system` + `derive`） | 文件写 `blocker_count: 0`、findings 含 1 blocker → `agate-md-field-get blocker_count` 返回 `1`（现算）；测试 passed | **ALIGNED** |
| F-5 | 聚合信任面 | 显式声明边界（`P4-implementation-G3.md §9.7`，与设计 §6 同口径） | 声明存在且与实现一致（`_aggregate_list` 只读声明文件；无签名=同信任级） | **ALIGNED（已声明）** |
| F-6 | 非 legacy `SCOPE+` 只认结构化 | 显式声明边界（§9.7；由批 B T1 绊线作后盾） | 声明存在；`check-scope-resolved.py` 非 legacy 只比对聚合 id 集合 | **ALIGNED（已声明）** |

## 四、新引入问题检查

**fail-closed 是否误伤合法路径**：否。`cmd_run` 唯一生产者 `agate-run.py --task` 恒写三字段
（见二）；F-2 命中面只加宽不放宽；legacy 任务 frontmatter 免检不变（实测 rc=0）。

**语义统一是否漏消费方**：否（见二，6/6 消费方单源）。

**新增观察（均 LOW，不阻断）**：

1. **F-2′（LOW，残留纵深缺口）— `task_dir_for_file` 子目录 shadow 可绕过 frontmatter 强制。**
   若在 `P4-implementation/` 内**故意放置**一个 `.state.yaml`（或 `gate-events.jsonl`），
   `agate_common.task_dir_for_file`（`:1812-1829`，返回**首个**含二者的祖先）会把「任务根」
   定位到该子目录；`task_level(子目录)` 无账本 → `None` → `check-frontmatter._task_is_non_legacy`
   返回 `False` → frontmatter 免检。实测：

   ```
   P4-implementation/.state.yaml = "task_id: T901\nphase: P4\nstatus: active\n"
   check-state-yaml.py  → rc=0（legacy 形状通过）
   check-frontmatter.py P4-implementation/direct.md → rc=0（应 rc=1，被 shadow 跳过）
   ```

   **定性**：① **非回归**——整改前 `_task_is_non_legacy` 用 `dirname(file)`，**所有**子目录声明
   文件都免检；整改后仅在「故意放置异常 `.state.yaml`」时复现旧行为，故属**净改进**。
   ② 需**故意伪造**异常产物（设计 §1 明示「不防故意伪造」），威胁模型外。
   ③ hook 侧：`pre-commit-gate.py:898` 的前置 `_is_declaration_path` 用**真** `task_dir`（命中），
   但随后委派 `check-frontmatter.py`（`:902`）会因 shadow 跳过；`check-state-yaml.py`（`:731`）
   对 legacy 形状的 shadow 放行 → hook 路径同样不拦。
   **建议（非阻断）**：`task_dir_for_file` 只认「tasks 根的**直接子目录**」或含合法
   `task_id`+账本的目录；或 `check-state-yaml` 拒绝非直接任务目录下的 `.state.yaml`。

2. **F-2″（LOW，口径说明）— basename-only 通配的命中面比枚举面宽。**
   `match_declaration_file` 对 `*-review.md` 等**不含 `/`** 的通配加 basename 兜底
   （`:1805`），使 `P4-implementation/foo-review.md` 命中 frontmatter 强制但**不被枚举**
   （`declaration_file_paths` 的 `*-review.md` 只匹配任务根）。方向为 **fail-closed（更严）**，
   **不产生逃逸**（命中面 ⊇ 枚举面），仅记录口径差；如需严格「同判据」，可去掉 basename 兜底。

## 五、STRIDE 矩阵（G3-fix2 改动面）

| 威胁 | 适用性 | 结论 |
|---|---|---|
| **S**poofing | 低 | 无新身份面 |
| **T**ampering | **低**（较第 1 轮 MEDIUM 下降） | F-1 已 fail-closed 且文案可区分；F-2 子目录逃逸已闭合；残留 F-2′ 需故意放置异常 `.state.yaml`（威胁模型外） |
| **R**epudiation | 低 | D3 事件缺失/不完整 → fail-closed；账本哈希链不变 |
| **I**nformation disclosure | 低 | 无新日志/响应面 |
| **D**enial of service | 低 | `match_declaration_file` 单次 glob；任务目录小，无放大 |
| **E**levation of privilege | 低 | `resolve_evidence_ref` realpath 限界不变；F-1 收紧不放宽 |

## 六、验证留痕

- **仓外副本根**：`/tmp/opencode/csoG3rr/`（`agate/` 副本 + `mktask.py` + 非 legacy 任务 `work/T901-test-task`）。
- **关键命令**：
  ```
  # F-1
  AGATE_ROOT=$R/agate python3 -c 'agate_common.resolve_evidence_ref(T,"run:1")'   # 各分支见二
  AGATE_ROOT=$R/agate python3 $R/agate/scripts/check-gate.py P6 $T                 # rc=1/1/2
  # F-2
  AGATE_ROOT=$R/agate python3 $R/agate/scripts/check-frontmatter.py $T/P4-implementation/direct.md  # rc=1
  # F-3 / F-4
  … resolve_evidence_ref（空日志）→ err；FILE=P7 agate-md-field-get blocker_count → 1
  # 交叉：副本内 pytest
  python3 -m pytest agate/tests/{integration/test_tag0050_evidence.py,unit/test_tag0050_declarations.py} \
      -k "cso_f1 or cso_f2 or cso_f3 or cso_f4 or blocker1 or minor4" -q   # 9 passed
  ```
- **真实仓库只读核验**：本次未改动被评审文件；`git status` 新增 untracked 仅来自并行 review
  子 Agent 的 progress 文件，非本次动作。

## 七、返回给主 Agent

- **最高严重级别**：LOW
- **各级问题数**：CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 2（新增观察）
- **F-1 / F-2**：**ALIGNED（闭合）**；F-3 已修、F-4 已登记、F-5/F-6 已声明
- **是否阻塞发布**：**否**（无 CRITICAL/HIGH/BLOCKER，无新门禁绕过）
- **status**：`approved`
