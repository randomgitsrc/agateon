---
review_date: 2026-10-08
reviewer: protocol-alignment-review
change_summary: TAG0050 批 D 前置 hotfix（I-2）——agate-run 普通运行不再比对基线 / --baseline 实际打印 diff + 回归用例 + 文档同步
files_changed:
  - agate/scripts/agate-run.py
  - agate/tests/unit/test_agate_run.py
  - agate/scripts/README.md
  - agate/UPGRADING.md
---

# 协议-脚本对齐审查

审查对象：**批 D 前置 hotfix（I-2）**（TAG0050）。范围：设计 §5 前置条件逐条满足 / 回归用例真能打红 /
文档反向传播 / 平台无关 / 无副作用。HEAD=`f21b314e`，改动**未提交**。

环境隔离：`[PROD_NOT_TOUCHED]` 全部验证在仓外可丢弃副本 `/tmp/opencode/tag0050-i2-copy` 上做；
真实仓库仅新增留痕文件，`git status` 未出现评审引入的改动，无 `stash` 落入真实仓库。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED（附一条 INFORMATIONAL 覆盖缺口，不阻断） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（一处 WARNING 计数因环境状态差异不可复现，已定位为 frozen 观测口径，非本 hotfix 缺陷） |

**总体：5 项设计要求（§5 三条前置 + 回归真红 + 文档传播）逐条满足，无 MISALIGNED。**
唯一保留项为一条 INFORMATIONAL（`_baseline_diff` 字节级兜底分支无测试），不阻断。

## 逐项审查

### A1: 文档→脚本对齐

**设计要求**（`docs/design-notes/design-tag0050-task-data-contract.md:505`，逐字）：
> **前置条件**：`agate-run` 的基线比对缺陷（TAG0042 实施评审 I-2）必须先以 hotfix 修复——普通运行只返回命令自身的退出码；基线比对只在 `--baseline` 时进行，并实际打印 diff。

拆为三条硬要求，逐条核对脚本实现：

**（1）普通运行只返回命令自身退出码 / 不在普通运行比对基线**
`agate/diff` 删除了原 `:189-190` 的 `elif`：

```diff
-    elif os.path.isfile(evidence_path) and _read_bytes(evidence_path) != output.encode("utf-8"):
-        baseline_mismatch = True
+            mismatch_diff = _baseline_diff(_read_bytes(evidence_path), output)
```
（删 elif 后）`main` 中 `baseline_mismatch` 仅在 `if baseline:` 分支内被置真（`agate-run.py:196-216`），
普通运行（无 `--baseline`）走 `_record_cmd_run(command, exit_code); return exit_code`（`:227-228`）。
**证据（变异 + 手工）**：
```
$ python3 agate-run.py "printf ..."     # 带陈旧证据 .agate-evidence/cmd-0.out=stale
plain rc=0   # 命令自身退出码；证据未被改写（cat 仍 stale）
```
用例 `test_hotfix_i2_plain_run_returns_command_exit_code_with_stale_evidence` 与
`..._propagates_nonzero_with_stale_evidence`（rc=7）均绿。

**（2）基线比对只在 `--baseline` 时进行**
`if baseline:`（`agate-run.py:198`）包裹 ignore 检查 / 首落盘 / 比对；普通运行不进入。ALIGNED。

**（3）不一致时实际打印 diff**
新增 `_baseline_diff()`（`agate-run.py:120-140`，`difflib.unified_diff`），mismatch 分支
`sys.stderr.write(mismatch_diff + "\n")`（`:223`）。**证据（手工复现，真实 stderr）**：
```
$ agate-run.py --baseline "echo alpha"    # 建基线 rc=0
$ agate-run.py --baseline "echo beta"     # 改输出
agate-run: baseline mismatch（证据与基线逐字节不一致）: .../cmd-0.out
--- baseline
+++ current
@@ -1 +1 @@
-alpha
+beta
rc=1
```
对比改动前：仅打印「diff 已客观报出」字样，无 `---/+++/±`。ALIGNED。

**附加核对**：`.out` 首次落盘语义未变——`if not os.path.isfile(evidence_path): _write_evidence(...)`
（`:212-213`）与 `_write_evidence`（`:143-155`，`"wb"` 字节精确）**未在本次 diff 中改动**；
用例 `..._baseline_first_write_lands_evidence_and_returns_exit_code` 验证落盘 `b"first-write\n"`。
ALIGNED。

**结论**：ALIGNED

### A2: 脚本→文档对齐

**脚本行为**：普通运行不比对 / `--baseline` 打印逐行 diff（见 A1）。

**文档同步**：
- `agate/scripts/README.md:165`（agate-run 行）新增「**普通运行只返回命令自身退出码**（不做基线比对）；
  `--baseline` 落 `.out` 证据并逐字节比对（**不一致 → 打印逐行 diff** 并返回非 0）」——与脚本一致。
- `agate/scripts/agate-run.py` 模块 docstring（`:7-10`）：BDD-9 补「普通运行（无 `--baseline`）**只返回命令
  自身退出码**，不与 `.out` 证据比对」；BDD-10 改「不一致时**实际打印逐行 diff** 再返回非 0」——与代码一致。

**结论**：ALIGNED

### A3: 一致性连锁 + 反向传播

**A3a 连锁（已知衍生改动）**：`agate/scripts/*.py` 改动 → 应同步 `agate/scripts/README.md`（已改）。
`check-protocol-consistency.py` 无对 `agate-run` 的 CHECK 锚点（grep 结果 0），无额外连锁。

**A3b 反向传播（主动推断应被影响文档）**：全仓 `grep`（排除 `tasks/`、`reviews/`）扫描
`客观报出|基线比对|逐字节比对`，结果：
- `agate-workspace/agents/CODE-MAP.md:39`（执行层族）：仅称「`--baseline` `.out` 证据逐字节比对」，
  **未声称普通运行比对** → 描述仍准确，**无需改**（未在 diff 中列出合理）。
- `agate/UPGRADING.md`：新增「未发布 — TAG0050 批 D 前置 hotfix」节（见 A5）。
- 其余命中均为本 hotfix 自身或历史评审文档（`docs/design-notes/review-tag0042-implementation.md` /
  `review-r2.md`，属按设计不改的历史记录）。

**结论**：ALIGNED

### A4: 测试覆盖

**新增用例**（`agate/tests/unit/test_agate_run.py:359-469`，4 条）覆盖：普通运行+陈旧证据 rc 归命令自身 /
普通运行失败 rc 归命令自身 / `--baseline` 打印真实 diff / 首次落盘语义不变。

**真红验证（变异法）**：在副本内以 `git show HEAD:agate/scripts/agate-run.py` 覆盖（=删掉修复），
```
$ python3 -m pytest agate/tests/unit/test_agate_run.py -q
3 failed, 11 passed in 0.87s
FAILED ...::test_hotfix_i2_plain_run_returns_command_exit_code_with_stale_evidence
FAILED ...::test_hotfix_i2_plain_run_propagates_nonzero_with_stale_evidence
FAILED ...::test_hotfix_i2_baseline_mismatch_prints_real_diff
```
⇒ 三条核心回归**确实因缺少修复而红**（普通运行两条 + `--baseline` diff 打印一条）；
第 4 条（首次落盘）为**语义不变的回归守护**，改动前即绿——符合 dispatch 的表述。

**全量实跑（副本，含修复）**：
```
$ python3 -m pytest agate/tests/ -q -n auto --reruns 2
8 failed, 2832 passed, 3 skipped, 16 rerun in 105.62s
```
8 条失败**与本 hotfix 无关**（均为 TAG0050 任务进行中的其它面：`test_tag0050_evidence` /
`test_setup_agate_dir` / `test_tag0050_declarations` / `test_tag0050_proxy_judgment` /
`test_tag0050_cross_batch`）；**反证**：在副本内 `git stash` 掉本 hotfix 的 5 个改动后，
同样这 8 条**仍全部失败**（`8 failed in 1.25s`）⇒ 属**基线既有失败**，非本 hotfix 引入。
本 hotfix 面（`test_agate_run.py`）14 passed、`test_events_ledger.py` 20 passed。

**INFORMATIONAL（不阻断，建议补一条）**：`_baseline_diff` 的**字节级兜底分支**（逐行相同但逐字节不同时
返回「基线 N 字节 / 本次 M 字节」提示，`agate-run.py:137-140`）在新用例中**未被覆盖**——新用例
`alpha`→`beta` 走的是逐行 diff 路径。该分支可达（副本内 `_baseline_diff(b'alpha', 'alpha\n')` 直接调用
返回字节级提示），建议补一条单元测试锁定，以免未来删改兜底导致该情形「无声回落为只写一行抽象字样」。

**结论**：ALIGNED（含 1 条 INFORMATIONAL 覆盖建议）

### A5: 下游影响 + 文档传播

- **gate 行为**：本次不改任何 gate 判定逻辑；`agate-run` 的 `cmd_run` 事件写入路径与事件字段未变
  （`_record_cmd_run` 未改），ignore 检查分支（`ignored is False → return 1`）未改——无破坏性变更。
- **UPGRADING**：`agate/UPGRADING.md:393-401` 新增「未发布 — TAG0050 批 D 前置 hotfix：`agate-run`
  基线比对（**无破坏性变更**）」，明确「协议语义 / `.state.yaml` schema / 既有任务数据格式均未变；
  版本号与 CHANGELOG 条目在 P8 统一落」。与既有同任务未发布节（`grep 未发布` → :279 G1 / :360 G2）同型。
- **CHANGELOG**：`[Unreleased]`（`CHANGELOG.md:11`）本次未加条目——与 G1/G2 未发布节的既有一致做法相同
  （P8 发版统一落），且 `check-protocol-consistency.py` **CHECK 13 CHANGELOG↔UPGRADING 章节对应 PASS**。
- **SELF-GATE 触发面**：`agate/scripts/*.py` + `agate/**/*.md` 命中 → 须派本审查并留痕 `self-gate-review:`。
  本报告即为该留痕依据。

**结论**：ALIGNED

### A6: 锚点表覆盖

`check-protocol-consistency.py` 的 CHECK 9 锚点表**不含 `agate-run`**（`grep -n agate-run` 结果 0）——
本 hotfix 未新增协议规则/脚本，无锚点表更新需求。副本内全量：
```
$ python3 agate/scripts/check-protocol-consistency.py
... 仅有 413 个 WARNING，无 ERROR。   rc=0
```
**结论**：ALIGNED

### A7: 设计原则一致性

- **ADR-015（实质/非实质；优先"让错误不可能"→"让错误可见"）**：本修复把 I-2 缺陷从「普通运行会因陈旧证据
  假失败（**静默**的判据分叉）」收敛为「不再比对」，并把 mismatch 从「只写抽象字样」升级为
  「**实际打印 diff**」（手段②"让错误可见"），与 ADR-015 的方向一致。docstring 对 pipefail 平台退化仍保留
  「绝不静默报绿（ADR-015 手段②）」口径，未受本次改动影响。
- 未发现需要新增 ADR 的架构决策（修复既有行为缺陷，不改变架构）。

**结论**：ALIGNED

### A8: 声称-命令绑定

| 声称（出处） | 产出它的命令 | 结论 |
|---|---|---|
| 「普通运行只返回命令自身退出码」 | 手工 `agate-run <cmd>` + 陈旧证据；`pytest ... -k hotfix_i2` | 可复现，真 |
| 「`--baseline` 不一致 → 打印逐行 diff」 | 手工 `--baseline alpha→beta` 捕获 stderr；同上用例 | 可复现，真 |
| P4-progress：`test_agate_run.py → 14 passed` | `pytest agate/tests/unit/test_agate_run.py -q` | 副本实测 `14 passed`，真 |
| P4-progress：`count-tests.sh → 2843` | `bash agate/tests/scripts/count-tests.sh` | 实测 `总计：2843`，真 |
| P4-progress：`check-protocol-consistency → 0 ERROR / 410 WARNING` | `python3 agate/scripts/check-protocol-consistency.py` | 0 ERROR ✓；WARNING 实测 **413**（非 410）——差 3，见下 |
| P4-progress：`check-platform-assumptions → rc=0` | `python3 agate/scripts/check-platform-assumptions.py` | 副本实测 rc=0，真 |
| P4-progress：「改前红 3 failed, 1 passed」 | 副本内 `git show HEAD:` 覆盖 + pytest | 实测吻合，真 |

**WARNING 计数差异（413 vs 声称 410）**：`check-protocol-consistency.py` 报告的口径为
「413 条 = CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 410」——**410 是 CHECK2-refs 子项数**，
实现者引用时取成了总量口径；且该计数来自 `tasks/` 等 **frozen（按设计不改、永不收敛）** 文件集，
其观测值随未跟踪文件状态浮动（我运行副本时比实现者运行时多出 review 派发的 `?? dispatch-context` 文件）。
**属观测口径差异，非本 hotfix 缺陷、非协议语义问题**；不要求删除（0 ERROR 的实质结论成立）。

**结论**：ALIGNED（唯一数字差异已定位为 frozen 观测口径，无损 A8 实质）

## 平台无关性核对（dispatch 第 4 项）

- `_baseline_diff` 仅用标准库 `difflib`；`decode("utf-8", errors="replace")`；`splitlines()` 兼容 `\r\n`
  → 无平台分支依赖。
- 新增用例：使用 `tmp_path` / `run_cli(python_exe, ...)`（不裸 `python3`）；命令为 `echo` / `exit`；
  无系统临时目录字面量。`python3 agate/scripts/check-platform-assumptions.py` 副本实测 **rc=0**。
- 对照既有「字节精确写盘」守护（`_write_evidence` 用 `"wb"`）未变，Windows 上写/比一致的前提保持。

**结论**：平台无关性满足。

## 无副作用核对（dispatch 第 5 项）

- **`cmd_run` 事件语义**：`_record_cmd_run` 未改，字段仍 `{event: cmd_run, cmd, exit, runner}`；
  任意路径**恰好追加一次**（baseline mismatch 分支 `:224` 或末段 `:227`，二者互斥）。
  `test_events_ledger.py`（BDD-12）副本实测 **all passed**。
- **`--baseline` ignore 检查**：`_is_ignored` 与 `ignored is False → 报错 return 1`、`ignored is None → WARNING`
  分支**未在 diff 中改动**；`test_bdd_11_*` 仍绿。
- 无新增文件落盘（`_baseline_diff` 纯计算）；普通运行**不读、不写** `.out`。
- 真实仓库未被本次审查改动（仅新增留痕 + 本报告）。

**结论**：无副作用。

## 审查证据命令附录（均在仓外副本执行）

```
# 1) 全量实跑（含修复）
cd /tmp/opencode/tag0050-i2-copy
python3 -m pytest agate/tests/ -q -n auto --reruns 2
#  → 8 failed, 2832 passed, 3 skipped

# 2) 本 hotfix 面
python3 -m pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q
#  → 20 passed

# 3) 变异（删掉修复）→ 3 条核心回归真红
git show HEAD:agate/scripts/agate-run.py > agate/scripts/agate-run.py
python3 -m pytest agate/tests/unit/test_agate_run.py -q
#  → 3 failed, 11 passed

# 4) 基线既有失败反证（stash 掉 hotfix 后同样 8 条失败）
git stash push -- agate/UPGRADING.md agate/scripts/README.md agate/scripts/agate-run.py \
  agate/tests/unit/test_agate_run.py agate-workspace/tasks/TAG0050-task-data-contract/P4-progress.md
python3 -m pytest <8 个 node id> -q   # → 8 failed
git stash pop

# 5) 一致性 / 平台扫描
python3 agate/scripts/check-protocol-consistency.py        # → 0 ERROR / 413 WARNING
python3 agate/scripts/check-platform-assumptions.py         # → rc=0
bash agate/tests/scripts/count-tests.sh                     # → 2843

# 6) 手工复现 diff 打印 / 普通运行不比对（见 A1）
```

## 闭环建议

- A1–A8 全 ALIGNED，**可 commit**（commit message 须含 `self-gate-review:` 指向本报告，SELF-GATE 触发面已命中）。
- （可选，非阻断）补一条 `_baseline_diff` 字节级兜底分支的单元测试；P8 发版时按既有流程补 CHANGELOG 条目。
- 批 D 前置条件（设计 §5）已由本 hotfix 满足，可进入 G3（D+E+F）。
