---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B/H4 hotfix——`agate-next.py` 新增受控 gate 入口 `AGATE_CHECK_GATE`（env 覆盖 check-gate 路径，未设时逐字不变）+ 端到端回归用例，恢复「真暂停」分支覆盖；关 DEBT0050 / 回写 RM-AG0111
files_changed:
  - agate/scripts/agate-next.py
  - agate/state-machine.md
  - agate/tests/unit/test_tag0027_b1_agate_next_cli.py
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
---

# 协议-脚本对齐审查

**意图**：处置 RM-AG0111 / DEBT0050——`agate-next` 的「真暂停」分支（exit ∉ `gate_pass_exit` 且 ≠ 1）经真实 gate 不可达 ⇒ 端到端覆盖缺失。修法（DEBT 建议①）：加**受控 gate 入口**（env 覆盖 check-gate 路径），用合成 gate 制造 exit 2 恢复端到端覆盖；**不得为测试而重新制造一个「本该是 exit 1 的 gate 缺口」**。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（含两条预存缺口观察，非本批引入） |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | 见下表（1 条声称无命令来源，标注） |

**总评**：**ALIGNED，可 commit**。核心改动（受控入口）是**纯增量**、默认行为逐字不变、未触任何 gate 退出码语义；端到端用例经变异验证确有判别力；DEBT0050 关单成立；文档/CHANGELOG/roadmap/debt 四方同步到位。无 MISALIGNED、无 NEEDS_HUMAN_REVIEW。

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/state-machine.md:341-345`）：
> **受控 gate 入口（RM-AG0111 / DEBT0050）**：`agate-next.py` 的 check-gate 入口可经 env
> **`AGATE_CHECK_GATE`** 覆盖（指向合成 gate 脚本）——仅供**测试/诊断**，用于制造「exit ∉
> `gate_pass_exit` 且 ≠ 1」的**真暂停**场景以恢复端到端覆盖（真实 gate 已无法产生该 exit：
> `pass_exit=0` 的 phase 不含 `return 2`，`pass_exit=2` 的 phase 里 2 本就是通过码）。
> **未设该 env 时行为与既有逐字一致**。

**脚本实现**（`agate/scripts/agate-next.py:62-66`）：
> `CHECK_GATE = os.environ.get("AGATE_CHECK_GATE") or os.path.join(SCRIPT_DIR, "check-gate.py")`

消费点：`:287`（P6.5 子进程）、`:365`（主流程 gate 子进程）。

**结论**：ALIGNED。
- 文档声明「env 覆盖 check-gate 入口」= 脚本 L66 的 `os.environ.get("AGATE_CHECK_GATE")` 精确实现。
- 文档声明「仅测试/诊断」= 脚本注释 L62-65 一致。
- 文档声明「真实 gate 已无法产生该 exit」的**事实依据已逐条核实**（见 A8 第 4/5 条）：`gate_p4`(1141-1258)、`gate_p65`(1728-1763)、`gate_p7`(1997-2144) 三个 `gate_pass_exit=0` 的 gate **均无 `return 2`**；`pass_exit=2` 的 phase 里 2 是通过码。

### A2: 脚本→文档对齐

**脚本变更**（`agate-next.py:66`）：新增 env 读取，未改任何其它逻辑。
**对应文档**：`state-machine.md:341-345` 新增「受控 gate 入口」段落，位置就在描述 `agate next` 机械化推进（L331-340）的同一 blockquote 内，语义归属正确。

**结论**：ALIGNED。新增行为在 `agate-next` 语义权威源（state-machine.md）有对应记录，且未在其它文档各自复制一份（无回归为「多处独立维护的 gate 入口表」）。

### A3: 一致性连锁 + 反向传播

**A3a 连锁（已知衍生改动）**：CHANGELOG / debt / roadmap / state-machine / test 五处均已在 diff 中，无遗漏的已知衍生面。

**A3b 反向传播（主动推断「应被影响但未列在 diff 的文件」，逐一验证）**：

| 候选文件 | 是否需改 | 依据 |
|---|---|---|
| `agate/scripts/README.md` | **否** | ① 该文件**本就不索引 `agate-next.py`**（只索引 `agate-next-card.py`，见 L150）——预存缺口，非本批引入；② 「新增脚本登记面」表 ④ 行明示 README 索引行是**约定非门禁**；③ 无中心化「脚本内部 env 覆盖」登记表（同类 `MAX_RETRY_MAP` 亦无 md 记录）。权威记录落在 state-machine.md 已足。 |
| `agate/tests/README.md` | **否** | 同上——无 `agate-next.py` 映射行（预存）；⑤ 行明示映射表为**约定非门禁**。 |
| `agate/WORKFLOW.md` | **否** | L504/510 引用 `agate next` 命令，均**指向 state-machine.md**，未各自维护 gate 入口细节。 |
| `agate/dispatch-protocol.md` | **否** | L291 同样只引用 `agate next` 并指向 state-machine.md。 |
| `agate/rules/phases.yaml`（`gate_pass_exit`）| **否** | 本改动**不改变** `gate_pass_exit` 语义（env 入口只换「跑哪个 gate 脚本」，不换 pass_set 判定）。phases.yaml L13-20 的说明仍准确。 |
| `agate/CONTEXT.md` / `agate/loop-orchestration.md` | **否** | 二者描述「真暂停」的**语义**（CONTEXT.md:10；loop-orchestration.md:251-266），非 gate 入口机制；env 入口属测试/诊断细节，不改变语义描述。 |
| `agate/adr.md` | **否**（A7 详）| 无未记录的架构决策——env 入口是既有「引导型 CLI」模式的实例，ADR-011 已覆盖。 |
| 其它脚本是否用同类「env 覆盖路径」模式 | **命名一致** | 全 `agate/scripts/` 搜索：`AGATE_CHECK_GATE` 为**唯一**「env 覆盖被当脚本路径执行」的模式；前缀 `AGATE_` 符合 `check-protocol-consistency.py:141` 记录的 `os.environ.get("AGATE_*", 默认)` 惯例（对照：裸 `MAX_RETRY_MAP` 是历史不一致，本改动未复制该不一致）。 |

**结论**：ALIGNED。反向传播无遗漏的**必需**改动；两条观察（README/tests-README 无 `agate-next.py` 行）为**预存缺口**，非本批引入，按 ADR-015「非实质不纠正」不列为修复项。

### A4: 测试覆盖

**新增用例**（`test_tag0027_b1_agate_next_cli.py:543-565`）：`test_rm_ag0111_non_pass_exit_end_to_end_via_controlled_gate`。
- 经 `_run_next`→`run_cli` **subprocess 跑 `agate-next.py` 主流程**（非直调 `_write_exit2_resolution`），env 注入 `AGATE_CHECK_GATE=<合成 gate（恒 exit 2）>`。
- 断言 `P4-exit2-resolution.md` 落盘 = 主流程走到「真暂停」分支的端到端证据。

**实跑输出**（本机，`-n auto`）：

```
$ python3 -m pytest agate/tests/unit/test_tag0027_b1_agate_next_cli.py -n auto -q
18 passed in 1.88s

$ python3 -m pytest agate/tests/ -n auto -q
1 failed, 2899 passed, 2 skipped in 87.04s
```

- 唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——本机 opencode CLI 为 `debug agents`（复数，`Unknown subcommand "agent"`），测试 L299 硬编码 `debug agent`（单数）⇒ **环境/工具版本漂移，与本批 diff 无关**（该测试不在改动集）。
- 跑前/跑后 `git status --porcelain` 一致（仅 6 个改动文件 + 本报告留痕文件）。

**判别力验证（scratch，一次性副本，未触真实仓库）**：
1. **负向对照**（不设 `AGATE_CHECK_GATE`）：真实 `check-gate.py P4` → `rc=1`（缺 `P4-review.md`）→ 走 retreat 分支 → **不落盘**。⇒ 用例若无受控入口则断言必红。
2. **变异测试**（副本中把 L66 改回硬编码真实 gate，即便设 `AGATE_CHECK_GATE=fake` 也被忽略）→ 仍走真实 gate → `rc=1` → **不落盘**。⇒ 用例**确实依赖**受控入口，非巧合通过。

**结论**：ALIGNED。新逻辑（受控入口 + 真暂停端到端）有对应 pytest，且经负向对照与变异双重确认判别力。A4 要求的全量实跑输出已附（含 passed/failed 计数）。

### A5: 下游影响 + 文档传播

- **是否影响既有项目 gate 行为**：**否**。`AGATE_CHECK_GATE` 未设 → `None or <默认绝对路径>` → 与改动前**逐字一致**（见重点 1）。且 `agate-next.py` **不在真实提交 gate 链上**（`pre-commit-gate.py` 只调 `agate-next-card.py`，不调 `agate-next.py`）⇒ 该 env 只影响「引导型 CLI」，不改变任何项目的提交拦截行为。
- **是否破坏性变更**：否。纯增量 + 默认不变 ⇒ **无需 `UPGRADING.md` 章节**。
- **CHANGELOG 是否标注**：**已标注**（`CHANGELOG.md` `[Unreleased]`→`### 修复`，含 `RM-AG0111 / DEBT0050`）。`check-changelog.py` 仅 P8 阶段触发（`pre-commit-gate.py:1044-1045`），本 hotfix 无 P8，故无需含 batch task_id。
- **文档传播**：见 A3b 表——`state-machine.md` 为唯一必需落点，已更新；其余下游文档（WORKFLOW/dispatch-protocol/角色/模板）均指向它，不各自维护副本。

**结论**：ALIGNED。

### A6: 锚点表覆盖

- 改动脚本为 `agate-next.py`（`agate-*.py`，**非 `check-*.py`**）⇒ **不属** `uncovered_gate_scripts()` 覆盖面前（该函数只 glob `check-*.py` + `pre-commit-gate.{sh,py}`）。
- `SCRIPT_ALIGNMENT_ANCHORS`（`check-protocol-consistency.py:577+`）无 `agate-next.py` 条目，本改动**未新增 gate 判定逻辑**，无需加锚点。
- 实测 `check-protocol-consistency.py`：**CHECK 9 PASS**（见 A8 第 3 条）。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-011（引导型 CLI 工具的权限是早纠错，不是安全边界）**：本改动给**引导型 CLI**（`agate-next.py`）加测试/诊断入口，**未削弱真实安全边界**——真实提交 gate 是 `pre-commit-gate.py` 直调 `check-gate.py`，不经 `agate-next.py`（已核：`pre-commit-gate.py` 不调用 `agate-next.py`）。脚本注释明标「仅测试/诊断入口」，与 ADR-011「工具层检查非安全边界」一致。
- **ADR-014（判据单一权威源）**：env 入口是**单源**（`agate-next.py:66` 一处定义），无判据分叉。
- **ADR-015（实质/非实质——门禁只用于「会导致后续错误决策」的错误）**：本改动修复的恰是**实质**问题（「真暂停分支被改坏现有测试不会发现」= 静默漏检），且优先用**机械判据**（端到端测试）落地，符合 ADR-015 的「优先让错误不可能」。

**结论**：ALIGNED。无未记录的架构决策。

### A8: 声称-命令绑定

| # | 声称 | 产出命令 | 结论 |
|---|------|----------|------|
| 1 | 「240 passed」 | （未找到任何对应命令） | **无据声称**——本报告内**不采纳**。可复现的邻近计数：`-k next`=52、`agate_next/gate_layer`=47、`exit2/resolution`=20、`debt/roadmap`=67、unit=2599、regression=81、integration=200，均非 240。 |
| 2 | 「2899 passed」 | `python3 -m pytest agate/tests/ -n auto -q` | **成立但需补全**：实为 `1 failed, 2899 passed, 2 skipped`。2899 passed 属实；唯一 failed 为环境相关的 `test_bdd_43_opencode_registration_and_debug_agent`（本机 opencode CLI 子命令为 `debug agents`），**与本批 diff 无关**。 |
| 3 | 「0 ERROR」（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | **成立**：仅 421 条 frozen WARNING，`无 ERROR`，rc=0。 |
| 4 | 「check-debt rc=0」 | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **成立**：rc=0。 |
| 5 | 「`pass_exit=0` 的 phase 不含 `return 2`」 | `grep -n "^def \|return 2" agate/scripts/check-gate.py` | **成立**：`gate_p4`(1141-1258)/`gate_p65`(1728-1763)/`gate_p7`(1997-2144) 均无 `return 2`。 |
| 6 | 「DEBT0050 closure_criteria 满足」 | 见重点 4 | **成立**。 |
| 7 | 「用例恢复端到端覆盖（依赖受控入口）」 | 见重点 2（负向对照 + 变异） | **成立**。 |

**结论**：除「240 passed」外，其余数字/结论类声称均可复现。按 A8 规则，「240 passed」无命令来源，**不写入本报告作为已核实事实**（已如实标注为无据）。

## 五项重点结论

### 重点 1：默认行为是否真的不变 ✅

- **逐字不变**：`os.environ.get("AGATE_CHECK_GATE") or os.path.join(SCRIPT_DIR, "check-gate.py")`。未设/空串时 `None or <默认>` = `<默认绝对路径>`，与旧行 `os.path.join(SCRIPT_DIR, "check-gate.py")` **完全等价**。
- **无导入时机副作用**：`os.environ.get` 是纯内存读取、无 I/O，模块导入时刻求值与旧行为无差异；`SCRIPT_DIR` 仍是绝对路径，路径形态不变。
- **设为不存在路径**：**非静默**。实测 `AGATE_CHECK_GATE=<不存在>` → 子进程 `python3 <path>` 报 `can't open file`（exit 2），该错误行经 `gate:` 前缀**转达**给主 Agent，并落盘 `P4-exit2-resolution.md`（判为真暂停）。即：有明确错误可见 + 有落盘留痕，不会静默通过。
  - 轻微观察（非缺陷）：一个**拼错的 env 值**会被呈现为「真暂停」而非「入口配置错误」——但这是既有 `_run_cmd` 语义（任意 `rc ∉ pass_set 且 ≠1` → 真暂停）的自然结果，且错误行已转达；该 env 仅测试/诊断用，风险可接受。
  - 相对路径观察（非缺陷）：若把 `AGATE_CHECK_GATE` 设为**相对路径**，子进程以 `cwd=task_dir` 运行（`_run_cmd` 的 `cwd=task_dir`），会相对 task_dir 解析。本批用例用**绝对路径**（`tmp_path`），不受影响。

### 重点 2：端到端用例的判别力 ✅

- **真走主流程**：`_run_next` → `run_cli(python_exe, agate-next.py, td)` = 独立 subprocess 执行 CLI `main()`，非直调 `_write_exit2_resolution`。
- **去掉 `AGATE_CHECK_GATE` 转红**：负向对照实测——不设 env 时真实 `check-gate.py P4` 返回 **1** → 走 retreat 分支 → **不落盘** → 断言必红。
- **变异验证**：副本中把 env 覆盖改回硬编码后，**即便设了 `AGATE_CHECK_GATE=fake` 也无效** → 仍走真实 gate（rc=1）→ 不落盘。⇒ 用例**确实依赖**受控入口，非「碰巧通过」。

### 重点 3：是否违反 DEBT 的告诫 ✅（未违反）

DEBT 告诫：「**不得**为测试而重新制造一个**本该是 exit 1 的 gate 缺口**」。
- 本改动 diff **只碰** `agate-next.py:66` 一行（+ 注释/测试/文档/记录），**未改任何 `check-gate.py` 的退出码语义**、未新增/恢复任何 `return 2` 路径。
- 合成 gate 是**测试侧的一次性脚本**（`tmp_path` 内 `sys.exit(2)`），不进入协议本体、不改真实 gate 行为。⇒ 符合 DEBT 告诫。

### 重点 4：关单是否成立 ✅

DEBT0050 `closure_criteria`：**「存在能以受控输入让 agate-next 走到 exit ∉ pass_set 分支的用例（端到端）」**。
- 新用例 `test_rm_ag0111_non_pass_exit_end_to_end_via_controlled_gate` 以受控输入（`AGATE_CHECK_GATE`）让 `agate-next.py` **端到端**走到「真暂停」分支（P4、合成 gate exit 2 ∉ {0} 且 ≠ 1）并落盘 `P4-exit2-resolution.md`，实测通过。⇒ **满足**。
- DEBT 条目已 `status: closed` + `closed_at` + `closure_note`；`task_id: hotfix-batchB-H4` 采用与 H1/H2/DEBT0046/DEBT0049 一致的「批次标签、无任务目录」先例。`check-debt.py` 启发式（closed 条目 evidence 须含 task_id + `P[56]` 子串）由新 evidence 满足——该条 evidence 已**自述**启发式粗糙并引 DEBT0033 / RM-AG0088，透明可接受。

### 重点 5：反向传播 + A8 ✅

- **`state-machine.md` 记录准确**：L341-345 与脚本 L66 及事实（`pass_exit=0` 的 phase 无 `return 2`）逐条吻合；位置（`agate next` 机械化节内）恰当；块引用格式（续行 `>`）正确。
- **A8 逐条命令复现**：见 A8 表。除「240 passed」无命令来源（已标注为无据、不采纳）外，「2899 passed」「0 ERROR」「check-debt rc=0」及两条事实断言均复现。**补全说明**：全量套件实为 `2899 passed / 1 failed / 2 skipped`，那 1 个 failed 是本机 opencode CLI 版本漂移导致的**环境性失败**，与本批 diff 无关。

---

**审查者注**：本次审查为**只读**——未修改任何协议/脚本/测试，未 commit/push；变异测试在 `/tmp/opencode/` 的一次性副本上进行；跑测前后 `git status --porcelain` 一致（仅本批 6 个改动文件 + 留痕/报告文件）。
