---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G2.md
trace_id: TAG0050-P4-20261008
agent: review
status: approved
---

# P4 实现复审（聚焦 · 第 2 轮整改后）— TAG0050 批 G2（B+C）

> 角色：`review`（偏执 Staff Engineer）。
> 对象：G2 **未提交**改动（fix2 后），HEAD `54a814fc`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 范围：`P4-dispatch-context-review-G2-rereview.md` 指定——**只核 B1/H1/M1/M2/L1/L2/L5/L3/L4/L6 是否闭合 + 是否引入新阻断**，不重开全量。
> 只读纪律：**未编辑任何被评审文件**；全部验证在**仓外可丢弃副本** `/tmp/opencode/G2rerev/`（含 `.git`）上进行；真实仓库仅执行只读命令。
> 环境隔离：`[PROD_NOT_TOUCHED]`（全程未接触生产环境）。

## 0. 汇总结论

**`status: approved`** —— 第 2 轮整改（fix2）后：
- **B1（首轮 BLOCKER）独立验证闭合**：非 legacy 任务主产出伪造 `pass: 999` + `results` 含 FAIL → `agate-md-field-get` 返回**现算值 2**（忽略文件值）；下游 `check-gate.py P6` 报 `FAIL=1` 并 rc=1（伪造汇总不再通过）。负向控制（禁用 derive 分支）→ 返回伪造值 999 ⇒ `test_bdd_46` 改前会红。
- **H1（首轮 HIGH）独立验证闭合**：**非 P6 主产出**（`P4-implementation.md`）缺 `prod_touched` → hook 报错（修复命令与中文注解**分行**）；**照抄执行**修复命令 rc=0 写入 `prod_touched: false`；重新提交 **rc=0 转绿**。
- **M1/M2/L1/L2/L5/L3/L4/L6 全部 ALIGNED**（实现或按 context 裁定显式登记/声明）。
- **未发现新阻断**；F-2/F-3（cso 首轮 MEDIUM）亦随附闭合。

| 编号 | 首轮级别 | 本轮判定 | 一句话证据 |
| --- | --- | --- | --- |
| B1 | BLOCKER | **ALIGNED（闭合）** | 非 legacy 伪造 `pass:999`+FAIL → get=2、fail=1；legacy 保留旧值 999；负向控制→999；check-gate P6 FAIL=1 rc=1 |
| H1 | HIGH | **ALIGNED（闭合）** | 非 P6 主产出照抄修复命令 rc=0；重新提交 rc=0 转绿 |
| M1 | MEDIUM | **ALIGNED** | `agate-config` init→set→get/show/explain 可见→unset 后消失、raw 无残留；无声明文件时 set 不创建 |
| M2 | MEDIUM | **ALIGNED（显式登记）** | `P4-implementation-G2.md:164` DESIGN_GAP 显式登记 T1/T2/T3 接线为后续批待办 |
| L1 | LOW | **ALIGNED** | `check-frontmatter._declaration_files` 改用 `task_level`（回退 `current_level`），与 `pre-commit-gate` 同口径 |
| L2 | LOW | **ALIGNED（显式声明）** | 结构面 `task_level` vs 时间面 `level_at_phase` 刻意不统一，代码注释 + 实现记录声明 |
| L5 | LOW | **ALIGNED** | 守护用例 `test_l5_frontmatter_type_error_json_type_names` 断言「应为 integer」，实测通过 |
| L3 | LOW | **ALIGNED（显式声明）** | 保留偏宽 fail-safe 并在 `P4-implementation-G2.md:160` 声明 |
| L4 | LOW | **ALIGNED（已裁定）** | 字面正则残留声明于 `P4-implementation-G2.md:161`（DESIGN_GAP-5） |
| L6 | LOW | **ALIGNED（已裁定）** | `_local_*` 降级副本声明于 `P4-implementation-G2.md:162` |

> 判定口径：review 角色规则「任何 BLOCKER → rejected」。本轮无 BLOCKER / CRITICAL / HIGH，B1 与 H1 均经**独立复现**证伪首轮缺陷 ⇒ 放行。

## 1. 环境与回归面（命令 + 输出）

- 副本：`/tmp/opencode/G2rerev/`（`rsync -a --exclude __pycache__ --exclude .pytest_cache`，含 `.git`）。
- 焦点用例：
  ```
  $ pytest agate/tests/unit/test_tag0050_write_tools.py \
           agate/tests/integration/test_tag0050_prod_touched.py \
           agate/tests/unit/test_tag0050_fitness.py -q
  19 passed
  ```
- 夹具面：`pytest agate/tests/integration/test_pre_commit_hook.py -q` → **62 passed**。
- 全量（CI 口径 `--reruns 1 -n auto`）：
  ```
  $ pytest agate/tests/unit agate/tests/integration -q -n auto --reruns 1
  8 failed, 2725 passed, 3 skipped, 8 rerun
  ```
  8 failed = **登记预期红灯**（BDD-43/59/60/63/66/69/71/76，属 D/E/F 批），与 `P4-implementation-G2.md §6` 一致 ⇒ **G2 fix2 未引入新回归**。
- `pytest agate/tests/regression -q -n auto` → **81 passed**。
- `python3 agate/scripts/check-protocol-consistency.py`（**副本自己的**）→ **0 ERROR**（412 WARNING，随副本内未跟踪文件浮动）。
- `bash agate/tests/scripts/count-tests.sh` → **总计 2839**（与实现记录一致）。
- `python3 agate/scripts/check-platform-assumptions.py` → **rc=0**。

## 2. 独立验证 B1（伪造 `pass` 值 → 现算）

**夹具**：仓外副本内建非 legacy 任务 `scratch_b1/TAG0001`（账本首行 `task_created` level=1），
`P6-acceptance.md` 文件里**伪造** `pass: 999` / `fail: 0`，而 `results` 实为 2×PASS + 1×FAIL。

```
$ FILE=…/scratch_b1/TAG0001/P6-acceptance.md AGATE_ROOT=…/agate python3 agate/scripts/agate-md-field-get.py pass
2          # 期望 2（现算），忽略文件里的 999
$ … agate-md-field-get.py fail
1          # 期望 1（现算），忽略文件里的 0
```

**legacy 行为保留**（无账本 → 不现算，回退文件值）：
```
$ FILE=…/scratch_legacy/TAG0001/P6-acceptance.md … agate-md-field-get.py pass
999        # legacy：保持旧行为
```

**负向控制（改前会红）**：把 `if spec is not None and spec.get("derive"):` 变异为 `if False and …`：
```
$ … agate-md-field-get.py pass
999        # derive 被禁用 → 返回伪造文件值 ⇒ test_bdd_46 断言（=2）会红
$ 恢复 → diff 确认 RESTORED_OK
```

**下游消费方生效**（首轮 cso F-1 的核心危害：伪造汇总被信任）：
```
$ AGATE_ROOT=…/agate python3 agate/scripts/check-gate.py P6 …/scratch_b1/TAG0001
GATE P6: FAIL=1, TOTAL=3
rc=1       # 文件写 fail:0 不再被信任；按 results 现算 FAIL=1 而阻断
```
⇒ B1 闭合，且其价值（系统事实现算、不可自报）在 P6 侧真实成立。

## 3. 独立验证 H1（非 P6 主产出照抄修复命令 → 转绿）

**夹具**：仓外一次性 git 仓 `scratch_h1/`，非 legacy 任务 `TAG0001`（phase=P4），主产出
`P4-implementation.md` **无** `prod_touched`；另置 `P4-review.md`（approved）+ 任务目录外代码文件。

```
$ AGATE_ROOT=…/agate git commit -m "probe missing prod_touched"
GATE: 主产出 P4-implementation.md 缺 prod_touched 字段（非 legacy 任务必填，设计 §4）
      修复命令: FILE=…/P4-implementation.md agate-md-field-set.py set prod_touched false
      （若未触达生产；若已触达请保持 true 并进入 PAUSED）
RC=1        # 修复命令与中文注解**分行**（整行照抄不再把注解吃进值）
```

**照抄执行**（按报错给出的 key/值）：
```
$ FILE=…/P4-implementation.md … agate-md-field-set.py set prod_touched false
OK: prod_touched=false 已写入 P4-implementation.md
rc=0        # 非 P6 主产出此前报「非法 key 'prod_touched'」；现可写
```

**重新提交转绿**：
```
$ AGATE_ROOT=…/agate git commit -m "after fix"
GATE P4 (TAG0001): 通过
RC=0        # 转绿
```
⇒ H1 闭合（BDD-49 的「照抄执行 → 重新校验转绿」在**非 P6 主产出**上真实验证）。

## 4. 独立验证 M1 / M2 / L1 / L2 / L5

- **M1（agate-config 真往返）**：
  ```
  $ agate-config.py set project.language python   # 无声明文件：校验通过、未创建（NOT_CREATED_OK）
  $ agate-config.py init ; set project.language python ; get project.language → python
  $ agate-config.py show | grep python → language: python
  $ agate-config.py explain project.language → 当前值: python
  $ agate-config.py unset project.language ; get project.language → （空）
  $ grep -c python agate.config.yaml → 0     # 真往返，无残留
  ```
- **M2（T1.downgrade 惰性数据 → 显式登记）**：`P4-implementation-G2.md:164` 有
  `[DESIGN_GAP: M2（C8 复审）——T1/T2/T3 的 gate 侧扫描未接线…显式登记为后续批待办…]`；
  `grep -rn "traps\[\|downgrade" agate/scripts/*.py` **零命中**（与登记一致：数据已落、消费方待后续批）。
  符合 dispatch「接线或显式登记待办（二选一，写明）」的裁定。
- **L1**：`check-frontmatter._declaration_files(task_dir)` 现为
  `level = task_level(task_dir, __file__)`，`None` 才回退 `current_level`；`pre-commit-gate._declaration_files`
  同口径（`task_level` 优先）⇒ 两处一致（原分叉消除）。
- **L2**：`pre-commit-gate.py` `_declaration_files` docstring 明确「结构面（任务级最新快照）vs
  时间面（`level_at_phase`）语义不同、刻意不统一」；`P4-implementation-G2.md:159` 同步声明。
- **L5**：`test_l5_frontmatter_type_error_json_type_names` 断言类型文案用 JSON 名「应为 integer」；
  实测通过（见 §1 焦点用例）。
- **L3/L4/L6**：`P4-implementation-G2.md:160/161/162` 逐条显式声明（保留偏宽 fail-safe / 字面正则 /
  `_local_*` 降级副本），符合 dispatch「核是否已在实现记录显式声明」。

## 5. 新引入问题检查

- **F-2（cso）随附闭合**：`agate-md-field-set.py::_cmd_set` 增契约驱动 `writer == "system"` 拒写；
  `test_f2_system_writer_field_rejected_by_contract` 在临时协议根注入**未来**系统字段
  `results_total`（非证据字段）→ `set` 被拒并说明来源（实测通过）。
- **F-3（cso）随附闭合且无假阳性**：独立核验「真实注入卡片块」的 sha256 与 `agate-next-card.py P4`
  输出**逐字节相等**（`MATCH`），故真实卡片仍被排除；P5/P8 卡片内 `[PROD_TOUCHED]` 行首形态
  （`- **PROD_TOUCHED**…` / `- [ ] 无 PROD_TOUCHED…`）经锚定安全门正则实测 `match=False`，不产生假阳性；
  `test_f3_forged_card_block_still_blocks` 证明伪造块内的标记仍拦。
- **观察（非阻断）**：首轮全量并行跑（未加 `--reruns`）曾出现一次
  `test_pre_commit_hook.py::test_it8_phase_p2_missing_design_blocked` 失败；**未能复现**——
  该用例单跑通过、其文件内 `-n auto` 62 passed、第二次全量与 CI 口径 `--reruns 1` 均回到
  **恰为登记的 8 个预期红灯**。判为 xdist 跨文件并行隔离的既有 flake（CI 以 `--reruns 1` 兜底），
  **非 G2 fix2 引入**，不作阻断项。

## 6. 留痕

- 副本：`/tmp/opencode/G2rerev/`（含 `.git`）；scratch：`scratch_b1/`、`scratch_legacy/`、`scratch_h1/`、`scratch_m1/`。
- 真实仓库只读命令：`git status`、`git diff`、`grep`、`read`；**未执行任何写仓/破坏性命令**，未编辑被评审文件。
- `[PROD_NOT_TOUCHED]`。

## 7. 返回给主 Agent

- **File**：`agate-workspace/tasks/TAG0050-task-data-contract/P4-review-rereview-G2.md`
- **Status**：`approved`
- **一句话**：B1/H1 独立验证闭合，M1/M2/L1–L6 全部 ALIGNED，未引入新阻断。
