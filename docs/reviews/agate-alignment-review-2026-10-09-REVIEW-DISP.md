---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: TAG0050 外部实施评审遗留处置（m-1 义务改标 / m-2 三条 DEBT / m-3 RM-AG0099 收窄 / m-4 LIMITATIONS CI 回放边界 / §3 零基础设施限定 + RM-AG0114/0115）
files_changed:
  - CHANGELOG.md
  - README.md
  - README.zh-CN.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/LIMITATIONS.md
  - agate/rules/obligations.yaml
---

# 协议-脚本对齐审查（REVIEW-DISP）

**审查对象**：分支 `chore/review-disposition`（工作区**未提交**，`git diff` 7 文件）。
**意图**：处置 TAG0050 外部实施评审的 5 项遗留——m-1（`OBL-P2-12`/`OBL-X-17` 由 M 改标 C + 移除 `scope: protocol-repo` + `baseline.reset`）、m-2（3 条无 owner 的 DESIGN_GAP 各登记 DEBT0060/0061/0062 + `source_ref`）、m-3（RM-AG0099 收窄为仅对 `agate-task-init`/`--adopt` 任务生效）、m-4（`LIMITATIONS.md` 补「CI 回放的边界」）、§3（两 README 的「零基础设施」限定为使用侧 + 登记 RM-AG0114/0115）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（5 项核心声称均可复现；2 项来源见注） |

> **头号问题（P0，必须先修）**：`README.zh-CN.md:28` 新增的「文档部分**零依赖**」**命中既有回归测试 BDD-19 的禁词**（`agate/tests/unit/test_upgrading_contract_doc.py:187-195`）⇒ **全量 pytest 转红**（实测 `2 failed, 2900 passed`，其中 `test_bdd_19_no_zero_dependency_claim[README.zh-CN.md]` 由本 diff 引入）。本批**未跑全量测试**，故此红未被发现。
>
> **次号问题（P1）**：`agate/rules/obligations.yaml:31-52` 的 `baseline:` 下出现**两个 `reset:` 键**（YAML 重复键，PyYAML 静默 last-wins）⇒ 有效基线取后者（56/121）**依赖键序**；首个 reset（60/123→56/119）被遮蔽。若换严格解析器或调换顺序，`check-obligations.py` 会由 PASS 变 FAIL（`56*119 < 56*121`）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

#### A1-1 计数口径（`scope: protocol-repo` 不计入占比）——ALIGNED

**脚本实现**（`agate/scripts/check-obligations.py:274-277`）：
```python
# scope: protocol-repo 的义务单独统计，不计入 M 占比（设计 §2.9）
in_ratio = item.get("scope") != _SCOPE_PROTOCOL
if in_ratio:
    counts[disposition] += 1
```
**文档声明**（`agate/rules/obligations.yaml:46` 注释）：
> ⚠️ 计数口径：`scope: protocol-repo` 的义务**本就不计入占比**（check-obligations.py:274-277）⇒ 移除 scope 后二者**进入统计**：C 33→35、总数 119→121、**M 计数不变（56）**……

**实跑核对**（命令见 A8）：
```
M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）
归宿分布: M=56 C=35 R=30
```
未计入项仅剩 `OBL-X-10`/`OBL-X-19`（均 M，带 scope）。注释中的行号引用（:274-277）、C 33→35、总数 119→121、M 不变**逐项属实**。

#### A1-2 【MISALIGNED】`baseline` 下重复 `reset:` 键（有效基线依赖键序）

**数据面**（`agate/rules/obligations.yaml:40-52`）：
```yaml
  reset:                       # ← 第 1 个 reset（TAG0050 批 A4）
    reason: "..."
    from: "60/123"
    to: "56/119"
  # 2026-10-09（TAG0050 外部实施评审 m-1）...
  reset:                       # ← 第 2 个 reset（m-1）——同一 mapping 重复键
    reason: "..."
    from: "56/119"
    to: "56/121"
```
**解析实现**（`check-obligations.py:236-245`，`_effective_baseline`）：取 `baseline.reset.to`。**实跑**：`yaml.safe_load` 的 `baseline["reset"]` = 第 2 个块（`to: "56/121"`），无告警。

**差异**：同一 `baseline` mapping 内两个 `reset` 键——YAML 规范不允许重复键，PyYAML 静默 **last-wins**。故：
1. 有效基线正确性**依赖键的书写顺序**（若第 2 块移到前面，`counts["M"]*base_total < base_m*total` → `56*119 < 56*121` 为真 ⇒ **FAIL「M 类占比低于基线」**）；
2. 第 1 个 reset（60/123→56/119）作为机器可读记录**被遮蔽**（仅存于注释）。

**建议**：合并为**单个** `reset:`（保留 m-1 的 56/119→56/121，把 60/123→56/119 的沿革移入上方注释——注释中已有大半）；或若确需保留两次重设的机器可读历史，把 `reset` 改为 list 并同步改 `_effective_baseline`（**属脚本变更，须先红后绿加回归**）。

#### A1-3 【MISALIGNED】`baseline.note` 与改后数据不一致

**数据面**（`obligations.yaml:35`）：
> `note: "TAG0050 批 A4 重设后的有效基线（M56/C33/R30；4 条 CI/手工义务归 scope: protocol-repo，不计入 M 占比）"`

**改后实际**（实跑）：`M=56 C=35 R=30`、`scope: protocol-repo` 仅 **2 条**（X-10/X-19）。note 称「有效基线」为 56/119 且 C33、4 条 scoped——与 m-1 后的有效基线（56/121）及分布（C35/2 条）**不一致**。

**建议**：更新 note 为改后分布，或明确 note 描述的是「原始基线字段」而非「有效基线」。

#### A1-4 m-1 改标 C 的语义正确性 — 基本成立（附注）

- **`OBL-P2-12`**（`enforced_at: check-tdd-red.py::main`）：F13 判定该脚本**不在必经路径**（否则不会归 `scope: protocol-repo`）⇒ 标 M（「脚本在不可绕开路径上执行」）**错误**；C（「有可判定命令但不在必经路径」）更准。✓ 副作用：改 C 后 `check-obligations.py` 不再核验其 `enforced_at`/`test`（仅 M 核验，见 `:282-287`）——`test:` 字段保留但不再机械校验（可接受，非阻断）。
- **`OBL-X-17`**（`check-debt.py --retreat-coverage`）：**实测只发 WARNING 不阻断**（`check-debt.py:90-94` 写 `GATE DEBT WARNING` 后 `return 0`）⇒ M 偏高，C 更准。✓
- **附注（口径混用）**：m-1 的理由是「**任务通用**规则（使用者项目同样生效）」，但 `scope: protocol-repo` 在 `check-obligations.py:16`/设计 §341 的定义是「**CI/手工执行**（不在必经路径）」——两者不是同一语义。结论仍对（这些脚本确实不在必经路径），但理由措辞把「适用对象」与「执行通道」两义混用。另：`obligations.yaml` 头部字段说明（`:14-21`）**未登记 `scope` 字段**，m-1 后其语义更关键，建议补一行。

---

### A2: 脚本→文档对齐 — MISALIGNED

#### A2-1 【MISALIGNED，P0】README.zh-CN.md 新增「零依赖」违反既有 BDD-19 回归守卫

**本 diff 新增**（`README.zh-CN.md:28`）：
> - **零基础设施（**使用侧**）。** …… ⚠️「零」说的是**使用**协议（**文档部分零依赖**）；……

**既有测试契约**（`agate/tests/unit/test_upgrading_contract_doc.py:187-195`，**不在本 diff**）：
```python
_ZERO_DEP = re.compile(r"零依赖|zero[- ]dependenc|no dependenc|无任何依赖", re.I)
_DOCS_19 = ("README.md", "README.zh-CN.md", "agate/UPGRADING.md", "agate/SETUP.md")
...
assert _ZERO_DEP.search(text) is None, f"{rel} 出现零依赖类宣称: ..."
```
**实测**（隔离复跑）：`test_bdd_19_no_zero_dependency_claim[README.zh-CN.md]` **FAILED**（`match='零依赖'`），另 3 个参数（README.md / UPGRADING.md / SETUP.md）PASS。

**差异**：本 diff 为「更诚实地限定零基础设施」，却在 zh-CN 文案里**引入了 BDD-19 明文禁止的措辞**（BDD-19 的立意是「不得宣称零依赖，须声明真实依赖」，与 `LIMITATIONS.md` 局限 5「零基础设施是相对的」同源）。**意图正确、实现自伤**。英文版 `README.md:28` 写 `docs are dependency-free`——**正则未命中**（`zero[- ]dependenc` 不匹配 `dependency-free`）故测试通过，但语义上仍是「零依赖」宣称，**擦边**。

**建议**（修复方向，二选一）：
1. zh-CN 改写为不含「零依赖/无任何依赖」的表述，例如「文档本体不引入额外部署/服务」；英文同步把 `dependency-free` 改为「self-contained / nothing to deploy」类表述；
2. 若确需保留「文档零依赖」语义，须**先**与 BDD-19 守卫的立意对齐（该守卫是有意为之的诚实护栏，不应被文案绕过）。

#### A2-2 其余脚本→文档面 — ALIGNED

- m-1：`check-obligations.py` 的 docstring（`:16`）与注释（`:274/:283`）对 `scope: protocol-repo` 的描述**未被本 diff 破坏**，仍准确。
- m-4：`agate-ci-verify.py` 与 `LIMITATIONS.md` 新节的声明一致（见 A3/A4-3）。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（连锁）**：m-1/m-2/m-3/m-4/§3 各自的直接落点（obligations.yaml / tech-debt.md / roadmap.md / LIMITATIONS.md / README×2 / CHANGELOG）均**已出现在 diff**。CHANGELOG `[Unreleased]`（`:11`）下新增「### 文档 / 登记」（`:62`）条目——**已传播**。

**A3b（反向传播：应被影响但未列在 diff 的文件，逐一验证）**

| 应被影响文件 | 现状 | 判定 |
|---|---|---|
| `agate/tests/unit/test_upgrading_contract_doc.py`（BDD-19） | 未随 README.zh-CN 改动同步（**应为：文案适配守卫**） | **未闭合**（见 A2-1，测试转红） |
| `agate/rules/obligations.yaml:35` `baseline.note` | 未随 m-1 更新（C33/4 条 → 实为 C35/2 条） | **未闭合**（见 A1-3） |
| `agate/tests/unit/test_tag0050_obligations.py:65` docstring | 仍写「终态下这 **4** 条已归 `scope: protocol-repo`」——m-1 后仅剩 **2** 条 | **陈旧**（不影响断言，全量跑通过） |
| `agate/assets/templates/tech-debt-template.md:34` `source_ref` 说明 | 定义为「**P4** 设计缺口（`basis: followup:DEBT<n>`）回指」；DEBT0060-0062 却用于 **P7** 缺口且 basis 为 `out_of_scope`/`in_bdd` | **语义不一致**（见 A3c） |
| `agate/scripts/README.md`（`agate-ci-verify.py` 条目） | 描述「逐提交回放…防 `--no-verify` 绕过」，**未**过度声称账本/证据真实性 | **无需改**（m-4 边界入 LIMITATIONS 即可） |
| `agate/WORKFLOW.md:371`（CI 兜底） | 描述回放机制，未声称真实性覆盖 | **无需改** |
| `agate/LIMITATIONS.md` 局限 3/局限 5 | 局限 3（`:66-68`）称 CI「backstop 重跑 check-gate/check-p6-provenance/check-events」——与回放机制**兼容**（`pre-commit-gate.py` 确调这三者，见下）；局限 5（`:91-101`）与新节同源 | **无矛盾**（见 A3d） |
| `agate-workspace/roadmap/roadmap.md` RM-AG0114/0115 | 与 RM-AG0059/0066/0079/0110 **非重复**（见 A4-4） | **无重复** |

**A3c 【MISALIGNED】`source_ref` 模板语义 vs DEBT0060-0062 用法**
`tech-debt-template.md:34`：source_ref「当该债由某任务的 **P4** 设计缺口（`basis: followup:DEBT<n>`）析出时，回指 `<task_id>:<DG id>`；`gate_p7` 校验该回指成立」。而 DEBT0060-0062 的 `source_ref` 指向 **P7** 的 DESIGN_GAP（`TAG0050:P7-design-gap-*`），且 TAG0050 P7 的 basis 为 `out_of_scope`/`in_bdd`（`P7-consistency.md:69/73/90`）——**无一条是 `followup:DEBT<n>`**。据 `check-gate.py:1938-1965`，BDD-66 双向回指校验**仅在 basis 匹配 `^followup:DEBT0*[0-9]+$` 时触发** ⇒ 这三条 `source_ref` **不受 gate 机械校验**（且 TAG0050 为 legacy，`_gate_p7_structured` 本就不跑）。即：模板称「gate_p7 校验该回指成立」，但对本批用法**不成立**。schema 层面合法（`^[A-Z]+[0-9]+:.+$`，`agate-debt-check.py:46/148-156`），属**语义/文档不一致**，非 schema 违规。
**建议**：放宽 `tech-debt-template.md:34` 的表述（覆盖 P4/P7 缺口 + 说明非 followup 用法为「信息性、不机械校验」），或改用一个不承载 gate 语义的字段名。

**A3d m-4 反向传播专项（`LIMITATIONS.md` 其它节是否与新节矛盾）**
- `pre-commit-gate.py` 确实调用 `check-gate.py`（`:560/:914`）、`check-p6-provenance.py`（`:948`）、`check-events.py`（`:960`）、`check-pruning.py`（`:964`）、`check-debt.py`（`:1122`）⇒ 局限 3 的「CI backstop 重跑 check-gate/check-p6-provenance/check-events」与 m-4「回放复核 hook 判定」**兼容**（回放正是重跑这些）。
- 新节（`:121-133`）与局限 5（零基础设施是相对的）、局限 3（CI 兜底）**无直接矛盾**；新节末尾引「设计 §0 的边界声明（防不了故意伪造）」，与设计文档 §0「**边界**：……防不了**故意伪造**……可信锚点是受保护分支上的 CI 回放」**一致**。
- 结构小疵：新节置于收尾节「## 这些局限意味着什么」**之后**，编号体系（局限 1-6 → 收尾 → 新节）无冲突，但位置略显突兀（可接受，非缺陷）。

---

### A4: 测试覆盖 — MISALIGNED

**最近一次全量 pytest 实跑**（只读；跑前后 `git status --porcelain` 逐行一致，未污染）：
```
$ python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
2 failed, 2900 passed, 2 skipped, 2 rerun in 119.97s (0:01:59)
```
失败清单与归因：
```
FAILED agate/tests/unit/test_upgrading_contract_doc.py::test_bdd_19_no_zero_dependency_claim[README.zh-CN.md]
       → 由本 diff 引入（README.zh-CN.md:28「零依赖」命中 BDD-19 禁词）。见 A2-1。
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
       → 环境问题（本机 opencode CLI 无 `debug agent` 子命令：Unknown subcommand "agent"），与本 diff 无关（与 HOTFIX-M1 评审记录同款）。
```
隔离复跑确认：
```
$ python3 -m pytest "agate/tests/unit/test_upgrading_contract_doc.py::test_bdd_19_no_zero_dependency_claim" -q
1 failed, 3 passed
```

**覆盖评估**：本 diff 为**数据面 + 文档**（无脚本逻辑变更）：
- m-1 的计数/改标由**既有 gate**（`check-obligations.py`）+ 既有单测（`test_tag0050_obligations*.py`，全量跑通过）承载；未新增断言 56/121 的用例（可接受，非硬要求）。
- m-2 的三条 DEBT 由 `check-debt.py FILE`（rc=0）+ `agate-debt-check.py` schema 承载。
- m-3/m-4/§3 为文档，无脚本判据。
- **但 §3 的 README.zh-CN 改动未被作者自测**，致既有 BDD-19 转红——**属本批遗漏的关键验证**（本批 A8 声称集不含全量 pytest）。

**结论**：MISALIGNED（引入 1 个既有用例转红 + 未在提交前跑全量套件）。

---

### A5: 下游影响 + 文档传播 — MISALIGNED

**破坏性 / 行为变更**：
1. **m-1（`obligations.yaml`）**：属协议自身的数据面（`agate/rules/`），**不改变使用者项目的 gate 行为**（使用者不被要求改本文件）。有效基线由 56/119 变 56/121，`check-obligations.py` 仍 rc=0（M 占比 0.4628 ≥ 0.4628）。**CHANGELOG 已标注**（`[Unreleased]`）。**无破坏性**。
2. **§3（README）**：**有副作用**——zh-CN 文案引入「零依赖」致 CI 转红（见 A2-1/A4）。这不是「下游用户影响」而是**本仓自身回归**，但后果是 PR 无法通过 CI。
3. **`baseline` 重复键**：潜在行为依赖解析器/键序（见 A1-2）——当前不触发，属**健壮性风险**。

**文档传播**：CHANGELOG `[Unreleased]` 已补（✓）；LIMITATIONS（m-4）、README×2（§3）、roadmap（m-3/§3）、tech-debt（m-2）均已落点。**未传播/未同步**者见 A3b 表（BDD-19 守卫、`baseline.note`、测试 docstring、`source_ref` 模板）。

**结论**：MISALIGNED（§3 自伤 + 反向传播未闭合项）。

---

### A6: 锚点表覆盖 — ALIGNED

本 diff **未新增协议规则、未新增/改名脚本**。m-1 是数据重分类（disposition 值变更），不引入新判据；m-2/m-3/m-4/§3 为登记与文档。`check-protocol-consistency.py` CHECK 9 锚点表**无需更新**（实跑 CHECK 9 PASS）。`check-obligations.py` 既有锚点（keywords `["obligations.yaml","M 类占比","无归宿"]`）仍成立。**ALIGNED**。

---

### A7: 设计原则一致性 — ALIGNED

逐条核对相关 ADR（`agate/adr.md`）：

| ADR | 相关性 | 判定 |
|---|---|---|
| ADR-002 可判定性 | m-1 改标后仍由 `check-obligations.py` 机器判定；m-4 的边界陈述强化「什么被判定、什么不被判定」 | **ALIGNED** |
| ADR-003 最小约定 / 不绑定技术栈 | §3 限定「零基础设施=使用侧」，与局限 5「gate/hook 依赖 python3+git+pyyaml」同源，方向正确 | **ALIGNED** |
| ADR-014 判据单一权威源 | m-1 未新增判据源；obligations.yaml 仍是唯一登记源 | **ALIGNED** |
| ADR-015 门禁只用于实质错误 | m-1 是**降级**误标的门禁（M→C），方向与 ADR-015 一致（不虚设门禁） | **ALIGNED** |

未发现未记录的架构决策，无设计原则层面的张力（§3 与 BDD-19 的冲突是**实现缺陷**，非设计原则分歧——见 A2/A4）。**ALIGNED**。

---

### A8: 声称-命令绑定 — ALIGNED

逐条列本批**结论/数字类声称**及其产出命令（均在只读、未污染工作区下实跑）：

| # | 声称（出处） | 产出命令 | 结论 |
|---|---|---|---|
| 1 | `check-obligations OK`（`CHANGELOG.md:62` 段） | `python3 agate/scripts/check-obligations.py` | 成立（rc=0，尾行 `CHECK-OBLIGATIONS: OK`） |
| 2 | `M 56/121`（`obligations.yaml:47-52` / `CHANGELOG.md`） | 同上（输出 `M 类占比: 56/121 = 0.4628`） | 成立 |
| 3 | `check-debt rc=0`（m-2 处置） | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md`（rc=0）；`--retreat-coverage`（rc=0，3 条既有 WARNING） | 成立 |
| 4 | `0 ERROR`（`CHANGELOG.md`/自述） | `python3 agate/scripts/check-protocol-consistency.py`（rc=0；`仅有 422 个 WARNING，无 ERROR`） | 成立 |
| 5 | `roadmap 111 行 0 异常` | `grep -cE '^\| RM-AG' roadmap.md` → 111；每行 `split('|')` 长度均 = `_ROADMAP_EXPECTED_COLS`(9，`check-gate.py:2138`) | 成立（111 行全部 7 数据列，0 列数异常） |
| 6 | m-3「存量 43 个任务全部 legacy」（`roadmap.md:98`） | 遍历 `agate-workspace/tasks/*/gate-events.jsonl` 查 `task_created`/`task_adopted` → 43 dirs / 43 legacy / 0 非 legacy | 成立 |
| 7 | m-3「repro 脚本…仍能复现 F1-A/B/C、F2、F3a/b/c」（`roadmap.md:98`） | 绑定命令 = `docs/design-notes/repro-tag0050.sh`（存在，冻结复现件）；**本轮未实跑**（避免写副作用） | **未独立复核**（来源为外部评审） |
| 8 | RM-AG0114/0115「来源：TAG0050 外部实施评审 §3」（`roadmap.md:113-114`） | 源报告**不在仓库**（外部件），无法在仓内绑定 | **来源不可仓内复核**（见下注） |

**无据声称**：本批**未发现**需删除的无据声称——5 项核心数字/结论声称**全部可复现**。
**注**：① #7 为**可绑定但未实跑**（脚本存在）；② #8 的「§3」引源为仓库外的外部报告，仓内不可复核——两者**不构成本批的无据声称**，但建议后续补入外部报告存档或注明「外部件」。
**另注（重要，归 A4）**：本批的验证**未含全量 pytest**，而全量 pytest **为红**（见 A4）——「可提交」这一隐含结论无支撑命令。A8 仅就**已列声称**判 ALIGNED。

---

## 五项重点结论（任务点名）

1. **m-1 计数口径 / `baseline.reset` / 改标 C**
   - **计数口径理解正确**：`scope: protocol-repo` **确实不计入占比**（`check-obligations.py:274-277`），实跑 `M 56/121`、`C 35`、`R 30`，与注释/C H A N G E L O G 一致。
   - **`baseline.reset` 的 `from/to` 与实际一致**（`from: 56/119` → `to: 56/121`；实跑 0.4706 → 0.4628），**但** `baseline` 下存在**两个 `reset:` 键**（重复键、last-wins、顺序敏感）——见 A1-2（P1 待修）。
   - **改标 C 语义正确**：`OBL-P2-12`（`check-tdd-red.py` 不在必经路径）、`OBL-X-17`（`--retreat-coverage` **实测只发 WARNING**，`check-debt.py:90-94`）——标 M 均偏高，C 更准。**附**：改 C 后其 `enforced_at`/`test` 不再被核验；理由措辞把「任务通用」与「CI/手工执行」两义混用。
2. **m-2 三条 DEBT**
   - `source_ref` **满足 schema**（`^[A-Z]+[0-9]+:.+$`，`agate-debt-check.py:46`）；`check-debt.py` **rc=0**。
   - **回指属实**：DEBT0060↔`P7-consistency.md:72`（A2 分支①，`accepted`）、DEBT0061↔`:89-90`（T1/T2/T3，`followup`）、DEBT0062↔`:68-69`（A4 `review_output`，`accepted`）——三条均为「接受/延后且**无 owner**」（DEBT0060 之前**无**任何条目覆盖，已核 `tech-debt.md` <2295 行）。
   - **不一致点**：`tech-debt-template.md:34` 的 `source_ref` 语义（P4 缺口 + `followup:DEBT<n>`）**不覆盖**本批用法（P7 缺口、basis 非 followup），且**不受 gate_p7 BDD-66 校验**（见 A3c）。
3. **m-4 表述 vs 实现**
   - **属实**：回放**确实不**校验账本事件真实性（设计 §0「防不了故意伪造」；无密钥/无签名），**确实不**重跑 `run:<k>`（`agate_common.resolve_evidence_ref:1763-1773` 只比日志 sha256 与 `cmd_run` 事件）。
   - **与其它节不矛盾**（局限 3 的 CI 兜底与回放兼容——`pre-commit-gate.py` 确调 check-gate/check-p6-provenance/check-events）。新节位置在收尾节后，略突兀但可接受。
4. **§3 两条新 RM + README 改动**
   - **RM 不重复**：RM-AG0114（git 存状态解耦）≠ RM-AG0059/0066/0079；RM-AG0115（阶段图数据化）**明标为 RM-AG0110 的上位目标**（非重复）。
   - **README 改动过度（有害）**：zh-CN 引入「**零依赖**」**违反既有 BDD-19 回归守卫**（测试转红），且与仓库自身的诚实立场（局限 5）自相矛盾；英文 `dependency-free` 擦边（正则漏网）。原措辞（「只需读文件和跑命令——无需部署、无需运维」）**本已限定在使用侧且准确**，新加的限定意图正确但**实现自伤**——须改写（见 A2-1）。
5. **A8 声称复现**：5 项核心声称（`check-obligations OK` / `M 56/121` / `check-debt rc=0` / `0 ERROR` / `roadmap 111 行 0 异常`）**逐条可复现**（命令见 A8 表）；另「43 个任务全部 legacy」亦成立。**但**本批未跑全量 pytest，而它**为红**。

---

## 闭环建议（按优先级）

| 优先级 | 项 | 动作 |
|---|---|---|
| **P0** | A2-1 / A4 / A5 | 改写 `README.zh-CN.md:28`（去「零依赖」）+ 复核 `README.md:28`（去 `dependency-free`），使 BDD-19 转绿；**提交前跑全量 pytest** 确认 |
| **P0/P1** | A1-2 | 合并 `obligations.yaml` 的重复 `reset:` 键为单个（保留 56/121，沿革入注释）；若须保留两次重设历史，改 `reset` 为 list 并同步 `_effective_baseline`（含回归） |
| P1 | A1-3 / A3b | 更新 `baseline.note`（C35、2 条 scoped）；更新 `test_tag0050_obligations.py:65` docstring（4→2） |
| P1 | A3c | 放宽/澄清 `tech-debt-template.md:34` 的 `source_ref` 语义，使其覆盖 DEBT0060-0062 的 P7-缺口/非 followup 用法（或注明「信息性、不机械校验」） |
| P2 | A8 注 | 把外部实施评审报告（§3/m-1..m-4 源）存档入仓，或在引用处标注「外部件」 |

**注**：本报告为**只读**审查——未修改任何协议/脚本/测试/数据文件，未 commit、未 push。跑测前后 `git status --porcelain` 逐行一致（未污染）。留痕文件见 `docs/reviews/agate-alignment-2026-10-09-REVIEW-DISP-01.progress.md`。
