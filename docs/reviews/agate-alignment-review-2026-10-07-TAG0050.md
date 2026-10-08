---
review_date: 2026-10-07
reviewer: protocol-alignment-review
task_id: TAG0050
batch: A0 (hotfix)
change_summary: "A0 缺陷修复：F8（pre-commit-gate.py PAUSED 留痕 append_event 3 参→2 参）+ check-gate.py main() 对不存在任务目录在所有 phase 统一 rc=1"
files_changed:
  - agate/scripts/pre-commit-gate.py
  - agate/scripts/check-gate.py
  - agate/tests/integration/test_tag0050_a0_a1_ledger.py
head: 75b8add
branch: feat/TAG0050-task-data-contract
prod_touched: "[PROD_NOT_TOUCHED]"
---

# 协议-脚本对齐审查（TAG0050 批 A0 · SELF-GATE Layer 1 · 变更触发模式）

## 意图分析（第一步）

A0 是一次**缺陷修复 hotfix**（不占 TAG0050 的 P0–P8，P1 §8 判定）。意图是：**让两处"文档已声称成立、实现层却因缺陷而失效"的保证真正成立**——
① `pre-commit-gate.py` 在 PAUSED 分支以 3 参调用 2 参的 `append_event`，抛出的 `TypeError` 被外层 `except` 吞掉 ⇒ **PAUSED 下的生产接触留痕从未真正落盘**（F8），而 `UPGRADING.md:407` 早已声称"会在任务账本留痕"；
② `check-gate.py` 对不存在的任务目录返回码**随 phase 分叉**（P0/P5/P7/P6.5 恰好命中各自"通过码"）⇒ **假 PASS**，而设计文档声称"应返回 1"。修复方式是把缺失目录判定收敛为 `main()` 的**单点早检**（分派之前），所有 phase 统一 rc=1。

一句话：**这不是新增语义，而是把"声称"与"实现"之间的缺口补平**（fail-closed 修复）。

## 反向传播：应被影响的文件（第二步）

按角色文件"反向传播的常见路径"表（改了 `agate/scripts/check-*.py` → `scripts/README.md`/`tests/README.md`/角色文件；脚本行为变更 → 文档传播），推断如下：

| 优先级 | 文件 | 被影响的理由 | 实际核查结果 |
|---|---|---|---|
| P0 | `agate/UPGRADING.md:407` | 已声称"PAUSED 只扫不阻断，但会在任务账本留痕"——F8 修复正是让此声称成立 | **无需改**（声称本就正确，修复使其成真） |
| P0 | `agate/scripts/README.md:71` | check-gate 的 rc 语义表（`0=通过,1=未通过,2=需自判`）——缺失目录现 rc=1 | **无需改**（1 = 未通过，语义一致；表未逐 phase 展开缺失目录） |
| P1 | `agate/state-machine.md:98,136,754` | PAUSED 语义/转移表 | **无需改**（未提"账本留痕"或缺失目录 rc） |
| P1 | `agate/WORKFLOW.md:353,320-327`、`agate/dispatch-protocol.md:874-881` | gate 表 / Pre-commit 检查总览 | **无需改**（均按"已存在目录"叙述，无缺失目录 rc 声明） |
| P1 | `agate/phase-cards/{P0,P5,P6}*.md` | 各阶段 gate rc 描述 | **无需改**（无"不存在目录"表述） |
| P2 | `agate/assets/execution-roles/*.md`、`agate/assets/review-roles/*.md` | 脚本行为变了，提示词是否过时 | **无需改**（grep `不存在目录`/`prod_touched_in_paused` 在 assets 与协议文档中零命中） |
| P2 | `agate/tests/README.md` | 测试面 | **无需改**（本次未改测试基建/计数） |
| P2 | `agate/adr.md` | 设计原则（见 A7） | **无需改**（ADR-002/004/005 均支持本修复，无新架构决策） |
| P3 | `CHANGELOG.md` | 协议行为变更是否标注 | **留待 TAG0050 P8**（见 A5；与 TAG0032/TAG0034 先例一致） |
| P3 | `SELF-GATE.md` / `AGENTS.md` | 自身机制条文 | **无需改**（无相关声称） |

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（CHANGELOG 归 P8，见说明） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **ALIGNED**（1 处派发声称数字已更正） |

---

## 逐项审查

### A1: 文档→脚本对齐

**① F8 — PAUSED 留痕**

**文档声明**（`agate/UPGRADING.md:407`）：
> （`PAUSED` 只扫不阻断，但会在任务账本留痕。）

设计侧的代码规格（`docs/design-notes/design-tag0050-task-data-contract.md:310-313` §2.8）：
> `append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})`

**脚本实现**：
- 修复前（HEAD，`pre-commit-gate.py:370`）：`append_event(task_dir, "prod_touched_in_paused", {"task_id": task_id})` —— **3 参**调用 `agate_common.py:524` 的 `def append_event(task_dir, event)`（**2 参**）⇒ 调用点抛 `TypeError`，被 `pre-commit-gate.py:371` 的 `except Exception` 吞掉，仅打印"账本留痕失败"。
- 修复后（工作区）：`agate/scripts/pre-commit-gate.py:370` = `append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})`，与 `agate_common.py:524` 签名及 §2.8 规格**逐字一致**；与其余 8 个调用点（`agate-next.py:158`、`agate-run.py:138`、`check-judge-verdict.py:619`、`pre-commit-gate.py:401/415` 等）的 2 参形态一致。

**结论**：ALIGNED（修复后文档声称成立）。

**② check-gate 对不存在任务目录返回 1**

**文档声明**：
- `docs/design-notes/design-tag0050-task-data-contract.md:242`：「`check-gate` 对不存在的任务目录改为返回 1」
- `docs/design-notes/review-r2.md:93`：「`check-gate` 遇到不存在的任务目录时应返回 1」
- 设计偏差登记（`P2-design.md:402` §10 G1）：「实测现状随 phase 不同：P7→0、P5→2、其余→1。**已裁决**：所有 phase 统一为 1……修复放 `check-gate.py main()` 单点早检（分派之前）」

**脚本实现**（`agate/scripts/check-gate.py:1626-1631`）：
```python
    # 单点早检（TAG0050 A0 §10 G1）：任务目录不存在时**所有 phase** 统一返回 1
    if not os.path.isdir(task_dir):
        sys.stderr.write(f"GATE {phase}: 任务目录不存在: {task_dir}\n")
        sys.exit(1)
```
位置在参数解析（`:1619-1624`）之后、`handlers.get(phase)` 分派（`:1659-1663`）**之前**，与 G1 裁决的落点一致。

**实测复现**（命令 + 输出）：

```
$ for p in P0 P5 P7 P1 P6.5 ZZ; do python3 agate/scripts/check-gate.py $p /tmp/opencode/nonexistent-TAGXXXX; echo "$p -> rc=$?"; done
P0 -> rc=1   P5 -> rc=1   P7 -> rc=1   P1 -> rc=1   P6.5 -> rc=1   ZZ -> rc=1
```

对照 HEAD（修复前）版本（`git archive HEAD agate/scripts` 抽取到仓外副本运行）：
```
HEAD P0 -> rc=2   HEAD P5 -> rc=2   HEAD P7 -> rc=0   HEAD P1 -> rc=1   HEAD P6.5 -> rc=0
```
与 P2 §10 G1 的实测口径一致（并额外确认 **P6.5 修复前也是 rc=0 假 PASS**）。`agate/rules/phases.yaml` 中 P0/P5 `gate_pass_exit: 2`、P7/P6.5 `gate_pass_exit: 0` ⇒ 修复前缺失目录恰好命中"通过码"，是真实的 false-PASS。

**结论**：ALIGNED（修复后文档声称成立）。

---

### A2: 脚本→文档对齐

**变更的脚本逻辑是否需要在协议文档同步更新？**

- `pre-commit-gate.py:370` 的新调用与设计 §2.8（`:313`）代码块**逐字一致**，无需文档改动。
- `check-gate.py` 新增的早检出口 rc=1 属于既有语义 "exit 1 = gate 未通过"（见脚本自身 docstring `:6-8` 与 `agate/scripts/README.md:71`），**未引入新出口码**，无需文档改动。

**一处轻微观察（非 MISALIGNED）**：`check-gate.py` docstring `:15-17` 声明"提供 OLD_PHASE 且数字上大于 PHASE 时……直接 exit 2"。新早检置于该回退检测**之前**，故"缺失目录 + 显式回退 phase"这一组合会返回 1 而非 2。经核查，**无受支持调用路径**触发该组合：`pre-commit-gate.py:374` 在调用 `check-gate.py`（`:390-391`）之前已 `if not os.path.isdir(task_dir): continue`，而 OLD_PHASE 仅由该调用点传入。语义上缺失目录 = 异常，fail-closed 到 1 更符合 ADR-002，故不判 MISALIGNED。

**结论**：ALIGNED。

---

### A3: 一致性连锁 + 反向传播

**A3a（已知衍生改动）**：脚本行为变更按反向传播表应连带 `scripts/README.md` / `tests/README.md` / 角色文件——逐一核查见上表 P0–P2，均**无需改**（描述均为通用 rc 语义或与缺失目录无关）。

**A3b（主动推断的应被影响文档）**：见上方"反向传播"表，10 项逐一验证：
- `agate/UPGRADING.md:407` 声称与 F8 修复**恰好对齐**（声称在先、修复在后）——这是本批的核心"声称-实现"闭环点；
- 协议文档（`state-machine.md` / `WORKFLOW.md` / `dispatch-protocol.md` / phase-cards / 角色文件）**无**"不存在目录返回 0/2"或"PAUSED 留痕只打印"的**现已失真**表述（grep 零命中）；
- 设计文档（design-notes / review-r1/r2 / P2 §10 G1）**已**记录目标行为，实现现与之匹配；
- `CHANGELOG.md` `[Unreleased]` 为空 → 归 A5。

**结论**：ALIGNED。

---

### A4: 测试覆盖

**对应测试**：`agate/tests/integration/test_tag0050_a0_a1_ledger.py`（本批 A0 = BDD-01/02）：
- BDD-01（`:18-45`）：构造 `phase: PAUSED` + 暂存 `[PROD_TOUCHED]`，跑 `pre-commit-gate.py`，断言 `gate-events.jsonl` **真实存在且含** `prod_touched_in_paused`（覆盖 F8 的落盘语义，不止"打印"）。
- BDD-02（`:48-60`）：`@pytest.mark.parametrize("phase", ["P7","P5","P0"])`，断言缺失目录 rc=1（覆盖修复前三个"假 PASS/降级"出口）。
- 平台无关性：用 `tmp_path` / `git_repo` / `python_exe` / `run_cli`，无裸 `python3`、无系统临时目录字面量——合规。

**最近一次实跑输出**：

1) 本批验收用例：
```
$ python3 -m pytest agate/tests/integration/test_tag0050_a0_a1_ledger.py -q -k "bdd_01 or bdd_02"
4 passed, 20 deselected in 0.35s
```

2) 全量（本 checkout，未提交工作区）：
```
$ python3 -m pytest agate/tests -q
79 failed, 2672 passed, 2 skipped in 227.45s (0:03:47)
```
失败构成（用命令拆解）：
```
$ grep -c "^FAILED" ...                      → 79
$ grep "^FAILED" ... | grep -c "tag0050"     → 78
$ grep "^FAILED" ... | grep -v "tag0050"     → 1
  FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
- **78 个 TAG0050 红**为 P3 TDD 设计的预期红（A1/A2/A3/C 批未实现；含 `test_tag0050_a0_a1_ledger.py` 中 A1 的 20 个），**非本次回归**；
- **1 个非 TAG0050 失败**为环境性：opencode CLI 子命令由 `debug agent` 变为 `debug agents`，报 `Unknown subcommand "agent"`；该测试文件不引用 `check-gate`/`pre-commit-gate`，**与 A0 无关**。

3) 既有相关套件回归抽跑（`test_check_gate.py` / `test_check_gate_p5_diff.py` / `test_check_gate_p1_review.py` / `test_check_gate_p4_maintainability.py` / `test_pre_commit_hook.py` / `test_tag0050_prod_touched.py` / `test_events_ledger.py` / `test_check_events.py`）：
```
4 failed, 335 passed in 68.88s
```
4 个失败全部落在 `test_tag0050_prod_touched.py`（批 C，BDD-52..55，TDD 预期红），**既有套件零回归**。

4) 修复前后对照（缺失目录 rc）见 A1 的实测输出。

**边界观察（非阻断）**：BDD-02 仅参数化 P7/P5/P0；P6.5/未知 phase 的缺失目录 rc=1 由本次审查手动实测覆盖（早检在分派前，天然 phase 无关）。建议后续可在参数化中补 `P6.5`/未知 phase 作为显式回归锁定。

**结论**：ALIGNED。

---

### A5: 下游影响 + 文档传播

**下游影响**：
- **hook 路径**：`pre-commit-gate.py:374` 在调用 `check-gate.py` 前已 `if not os.path.isdir(task_dir): continue`，故 hook 永不向 `check-gate` 传缺失目录——**无行为回归**。
- **CI 兜底**：`agate-ci-verify.py:126-135` 以 `tasks_dir/task_id` 定位任务目录后重跑 gate，rc=1 被判 `FAIL`（非 skip）——缺失目录由"假绿"变为"真红"，正是意图。
- **推进器**：`agate-next.py` 仅对已存在任务目录的当前 phase 调用，`gate_pass_exit`（`agate/rules/phases.yaml`，P0/P5=2、P7/P6.5=0）不受影响（早检只在缺失目录触发）。
- **破坏性**：无。改变仅作用于"传入不存在的任务目录"这一异常输入，正常项目流程不会命中；无需 `UPGRADING.md` 破坏性变更章节。

**文档传播**：见 A3b——协议文档无需同步（无失真表述）。

**CHANGELOG**：`CHANGELOG.md` `[Unreleased]` 目前为空，未标注本修复。按本仓既有先例（`docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md` 的 A5、`...-2026-09-09-TAG0034.md` 的 P8 收尾），**批实现者不擅自写 CHANGELOG，归任务 P8**。A0 属 TAG0050 的一批，其变更应随 TAG0050 的 P8 一并写入 CHANGELOG（含义务基线重设，见 P2 §7 行 142「各批按需写」）。

**结论**：ALIGNED（附 P8 待办清单：TAG0050 P8 须在 `CHANGELOG.md` `[Unreleased]` 记录 A0 的两处缺陷修复 + 后续各批；本批不阻断 commit）。

---

### A6: 锚点表覆盖

- CHECK 9 锚点表（`agate/scripts/check-protocol-consistency.py:568-887`）为**白名单式关键词存在性**检查，针对"文档声明的规则 → 脚本应含关键词"。本批**未新增协议规则/关键词**，仅修复既有脚本行为，故**无需新增锚点**。
- 实跑本 checkout 的 `check-protocol-consistency.py`：**0 ERROR**（442 WARNING 全部为冻结文件，按设计不收敛；其中 CHECK9 相关未见 ERROR）。
- `uncovered_gate_scripts()` 判据（CHECK9-coverage / SG.6）不受影响：未新增/删除 `agate/scripts/` 文件。

**结论**：ALIGNED。

---

### A7: 设计原则一致性

逐条核对相关 ADR（`agate/adr.md`）：
- **ADR-002（可判定性——gate 门槛机器可判定）**：修复把缺失目录的 rc 由"随 phase 分叉（0/2 假 PASS）"收敛为确定性的 rc=1，正是 ADR-002 要消除的"不可判定的假通过"。**支持**。
- **ADR-004（安全网分层——hook 兜底）**：F8 修复恢复了一道**此前静默失效**的安全网（PAUSED 生产接触留痕），使 hook 兜底名副其实。**支持**。
- **ADR-005（改动性质决定流程——声明性/行为逻辑/机制交叉）**：A0 触碰 `agate/` 协议脚本 ⇒ 触发 SELF-GATE、须独立语义审查并留 `self-gate-review:`（本审查即该流程的一环）。流程分类正确。**支持**。
- 未发现未记录的架构决策，无需新增 ADR。

**结论**：ALIGNED。

---

### A8: 声称-命令绑定

逐条列 `声称 → 命令 → 结论`（含派发上下文/进度文件的数字声称）：

| 声称 | 命令 | 结论 |
|---|---|---|
| `append_event` 为 2 参 `def append_event(task_dir, event)` | `grep -n "def append_event" agate/scripts/agate_common.py` | ✅ `:524` 确认 |
| 修复前 `pre-commit-gate.py:370` 以 3 参调用（F8） | `git show HEAD:agate/scripts/pre-commit-gate.py`（对照 diff） | ✅ 确认 |
| BDD-01/02 共 4 用例 passed | `pytest .../test_tag0050_a0_a1_ledger.py -q -k "bdd_01 or bdd_02"` | ✅ `4 passed` |
| `check-gate P0/P5/P7 <不存在目录>` 均 rc=1 | `for p in P0 P5 P7 ...; do python3 agate/scripts/check-gate.py $p <缺失>; done` | ✅ 全 rc=1 |
| 修复前 rc 随 phase 分叉（P7→0/P5→2/其余→1） | 仓外副本跑 HEAD 版 check-gate | ✅ P0=2,P5=2,P7=0,P1=1,**P6.5=0** |
| 全量 pytest = 79 failed / 2672 passed / 2 skipped | `pytest agate/tests -q` | ✅ 一致 |
| 79 失败 = 78 TAG0050 预期红 + 1 环境性失败 | `grep -c` 拆解 + 读失败详情 | ✅ 一致（1 = `debug agent`→`agents` 环境性） |
| `check-protocol-consistency.py` 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | ✅ 0 ERROR（442 frozen WARNING） |
| 当前 HEAD = `75b8add`，分支 `feat/TAG0050-task-data-contract` | `git rev-parse --short HEAD` + `git branch --show-current` | ✅ 一致 |
| 派发上下文称「82 个新增 TAG0050 测试为红」 | `pytest --collect-only \| grep -c tag0050` = **82**；全量失败中 TAG0050 = **78** | ⚠️ **表述不精确**：TAG0050 新增测试**共 82**，其中 A0 的 4 个（BDD-01/02）已转绿 ⇒ **当前红 = 78**（非 82）。建议后续派发措辞改为"新增 82 个，其中 78 仍为预期红" |

无"无法给出命令"的声称；上表已更正一处不精确的派发措辞。

**结论**：ALIGNED（1 处数字声称已按实测更正）。

---

## 闭环

| 结论 | 主 Agent 动作 |
|---|---|
| A1–A8 全 **ALIGNED** | 通过，可 commit（提交信息须含 `self-gate-review:` 留痕） |

- **环境隔离**：`[PROD_NOT_TOUCHED]`
- **只读纪律**：全程未执行任何写仓/破坏性 git 命令；对照 HEAD 行为的验证在**仓外可丢弃副本**（`/tmp/opencode/headscripts`，单次 bash 内建→用→清）完成；`git status --porcelain` 复核仅显示被评审的两个脚本处于 modified（A0 改动），无本次审查引入的杂散写入。
- **待办（非本批阻断项）**：TAG0050 P8 须在 `CHANGELOG.md` `[Unreleased]` 记录 A0 两处缺陷修复（见 A5）。
