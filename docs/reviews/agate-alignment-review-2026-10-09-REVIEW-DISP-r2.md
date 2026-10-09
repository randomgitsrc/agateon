---
review_date: 2026-10-09
reviewer: protocol-alignment-review
round: 2
change_summary: TAG0050 外部实施评审遗留处置（m-1/m-2/m-3/m-4/§3）——r1 P0/P1 整改后的复核（README 去禁词 / baseline 单 reset 键 / source_ref 模板扩展）
files_changed:
  - CHANGELOG.md
  - README.md
  - README.zh-CN.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/LIMITATIONS.md
  - agate/assets/templates/tech-debt-template.md
  - agate/rules/obligations.yaml
---

# 协议-脚本对齐审查（REVIEW-DISP，r2）

**审查对象**：分支 `chore/review-disposition`（工作区**未提交**，`git diff` 8 文件；较 r1 新增 `agate/assets/templates/tech-debt-template.md` 入改动集）。
**前轮**：`docs/reviews/agate-alignment-review-2026-10-09-REVIEW-DISP.md`（r1）——P0（README 打红 BDD-19）+ P1（`baseline` 重复 `reset:` 键 / `baseline.note` 陈旧 / `source_ref` 模板语义）。
**本轮意图**：独立核实 r1 的 P0/P1 是否真的修好；扫描有无**新的** A1-A8 问题；逐条复现本批声称。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（1 处非阻断残留，见下） |
| A4 | 测试覆盖 | **ALIGNED** |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（2 处非阻断文字小疵，见下） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **ALIGNED** |

> **是否可 commit：可以。** r1 的 P0/P1 均已修复并经实测核实；全量 pytest 唯一失败为**预先存在的环境问题**（`test_bdd_43`，opencode CLI 无 `debug agent` 子命令，与本 diff 无关，r1 亦同）。无 MISALIGNED、无未决 NEEDS_HUMAN_REVIEW。残留项均为**非阻断**文字/注释小疵（下 §残留）。

---

## 一、r1 P0/P1 逐条核实（独立验证，不采信自述）

### P0（README 改动打红 BDD-19 守卫）——**已修，核实通过**

**改动**（`git diff`）：
- `README.zh-CN.md:28`：「文档部分**零依赖**」→「**协议文档本身不需要安装任何运行时**」。
- `README.md:28`：`the docs are dependency-free` → `the docs need **no runtime installed**`。

**验证 1——正则扫四文档 0 命中**（命令）：
```
python3 -c "import re; rx=re.compile(r'零依赖|zero[- ]dependenc|no dependenc|无任何依赖', re.I); [print(f,'HIT' if rx.search(open(f,encoding='utf-8').read()) else 'clean') for f in ('README.md','README.zh-CN.md','agate/UPGRADING.md','agate/SETUP.md')]"
```
实测输出：`README.md clean / README.zh-CN.md clean / agate/UPGRADING.md clean / agate/SETUP.md clean`。✓

**验证 2——BDD-19 所在测试文件全绿**（命令）：
```
python3 -m pytest agate/tests/unit/test_upgrading_contract_doc.py -q -p no:cacheprovider
→ 20 passed in 0.10s
```
✓（r1 时该文件的 `test_bdd_19_no_zero_dependency_claim[README.zh-CN.md]` 为 FAILED，现 20/20 通过。）

**验证 3——全量 pytest 无本 diff 引入的失败**（命令）：
```
python3 -m pytest agate/tests/ -n auto --reruns 1 -q -p no:cacheprovider
→ 1 failed, 2901 passed, 2 skipped, 1 rerun in 108.25s
```
唯一失败 `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——**环境问题**（`opencode debug agent` → `Unknown subcommand "agent"`），与本 diff 无关（r1 同款、基线即红）。r1 的 diff 引入失败（BDD-19）已消除。✓

### P1（`baseline` 重复 `reset:` 键）——**已修，核实通过**

**改动**：`agate/rules/obligations.yaml` 的 `baseline` 下两段 `reset:` 合并为**单键**（两段 reason 并为一条 `>-` 叙述），`note` 同步更新（`M56/C33/R30`/4 条 → `M56/C35/R30，共 121`/2 条）。

**验证 1——`baseline` 键唯一 + `reset` 值**（命令）：
```
python3 -c "import yaml; b=yaml.safe_load(open('agate/rules/obligations.yaml',encoding='utf-8'))['baseline']; print(list(b.keys())); print(b['reset'])"
→ ['m', 'total', 'm_ratio', 'note', 'reset']
→ {'reason': '2026-10-09 外部实施评审 m-1：… C 33→35、总数 119→121、M 计数不变（56）… 此前一次重设（TAG0050 批 A4：F13 的 4 条 M 归 scope: protocol-repo）已并入本口径。', 'from': '56/119', 'to': '56/121'}
```
另：字面 `reset:` 行（`baseline:` 作用域内）计数 = **1**。✓（r1 为 2；重复键风险已消除。）

**验证 2——`check-obligations.py` rc=0 且 M/total 与 `from/to` 一致**（命令）：
```
python3 agate/scripts/check-obligations.py
→ M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）
→ 归宿分布: M=56 C=35 R=30
→ CHECK-OBLIGATIONS: OK
→ rc=0
```
`reset.from=56/119`（= 原始 `baseline.m/total` 对应值）、`reset.to=56/121`（= 有效基线 = 实跑分母）**一致**。✓

**验证 3——`baseline.note` 与改后数据一致**：
> `note: "2026-10-09 重设后的有效基线（M56/C35/R30，共 121；2 条 CI/手工义务归 scope: protocol-repo 不计入占比；m-1 后 OBL-P2-12/X-17 由 M 改标 C 并进入统计）"`
实跑 `M=56 C=35 R=30`、`scope: protocol-repo` 仅 2 条（X-10/X-19）——**与 note 一致**。✓（r1 的 C33/4 条已更正。）

### P1（模板 `source_ref` 语义）——**已修，核实通过**

**改动**（`agate/assets/templates/tech-debt-template.md:34`）：`source_ref` 说明扩展为——① P4 缺口（`basis: followup:DEBT<n>`）由 `gate_p7` **机械校验**；② **P7 缺口**（接受/延后无 owner，2026-10-09 m-2 用法）**仅作记录**、不受 BDD-66 校验；并注明「`task_id` 为**裸编号**（如 `TAG0050`）」。

**核实**：与 `check-gate.py:1938-1965`（BDD-66 仅在 basis 匹配 `^followup:DEBT0*[0-9]+$` 时校验回指）**一致**；与 DEBT0060-0062 的实际用法（P7 缺口、basis 为 `out_of_scope`/`in_bdd`）**一致**；「裸编号」与 `.state.yaml` 的 `task_id: TAG0050` 及 source_ref 前缀 `TAG0050:` **一致**（DEBT 条目自身的 `task_id: TAG0050-task-data-contract` 是目录名，与 source_ref 前缀本非同一取值——模板现明确 `task_id` 指裸编号，消除了 r1 的歧义）。✓

---

## 二、新增问题扫描（r1 后新引入或新暴露）

### A1: 文档→脚本对齐 — ALIGNED

- 计数口径（`scope: protocol-repo` 不计入占比，`check-obligations.py:274-277`）**未变**、仍准确。
- 重复 `reset:` 键 → 单键（已核实）；`baseline.note` 已同步。
- **改标 C 的语义**（r1 A1-4）仍成立：`OBL-P2-12`（`check-tdd-red.py` 不在必经路径）、`OBL-X-17`（`--retreat-coverage` 只发 WARNING）——M 偏高，C 更准。`evidence` 字段已就地留痕「2026-10-09 更正（m-1）」。
- 无新增不一致。**ALIGNED**。

### A2: 脚本→文档对齐 — ALIGNED

- README.zh-CN/README 去禁词后，与既有回归守卫 BDD-19（`test_upgrading_contract_doc.py:187-195`）**不再冲突**（实测 20 passed）。
- `check-obligations.py` docstring/注释对 `scope: protocol-repo` 的描述仍准确。
- m-4：`agate-ci-verify.py` 实现与 `LIMITATIONS.md` 新节声明**一致**（见 A3）。**ALIGNED**。

### A3: 一致性连锁 + 反向传播 — ALIGNED（1 处非阻断残留）

**A3b 反向传播（复核 r1 表）**：

| 应被影响文件 | r1 判定 | r2 现状 |
|---|---|---|
| `test_upgrading_contract_doc.py`（BDD-19） | 未闭合 | **已闭合**（文案去禁词，20 passed） |
| `obligations.yaml:35` `baseline.note` | 未闭合 | **已闭合**（C35/2 条） |
| `tech-debt-template.md:34` `source_ref` | 语义不一致 | **已闭合**（两用法 + 裸编号） |
| `test_tag0050_obligations.py:65` docstring | 陈旧（4 条） | **残留**（仍写「这 4 条已归 `scope: protocol-repo`」，m-1 后仅 2 条）——**非阻断**（不影响断言，全量跑通过；属测试文件注释，本批未纳入改动面） |
| `scripts/README.md` / `WORKFLOW.md`（CI 回放） | 无需改 | **无需改**（未过度声称真实性） |
| `LIMITATIONS.md` 局限 3/5 | 无矛盾 | **无矛盾** |

**A3d m-4 专项复核**：`LIMITATIONS.md` 新节（`:121-133`）与局限 5（`:91-101`「零基础设施是相对的」）、局限 3（`:66-68` CI 兜底）**一致**；新节引「设计 §0 边界声明（防不了故意伪造）」与设计文档 §0 原文**一致**。**ALIGNED**。

### A4: 测试覆盖 — ALIGNED

- **全量 pytest 实跑**（只读；跑前后 `git status --porcelain` 逐行一致）：
  ```
  1 failed, 2901 passed, 2 skipped, 1 rerun in 108.25s
  FAILED ...test_bdd_43_opencode_registration_and_debug_agent  ← 环境（opencode CLI），与本 diff 无关
  ```
- 无本 diff 引入的失败。BDD-19 守卫文件 20/20 绿。
- 本 diff 为**数据面 + 文档**（无脚本逻辑变更）：m-1 由既有 gate + 既有单测承载；m-2 由 `check-debt.py`/`agate-debt-check.py` 承载；m-3/m-4/§3 为文档。**ALIGNED**。

### A5: 下游影响 + 文档传播 — ALIGNED（2 处非阻断文字小疵）

- **行为/破坏性**：m-1 仍为协议自身数据面（不改变使用者项目 gate 行为）；`baseline` 单键后**不再有键序/解析器依赖**（r1 的健壮性风险已消除）；§3 的 README 自伤回归已消除。CHANGELOG `[Unreleased]` 已标注。
- **文档传播**：README×2、LIMITATIONS、roadmap、tech-debt、template 均已落点。
- **非阻断小疵**：
  1. **README 新措辞与 LIMITATIONS 的精度**：现文案为「『零』说的是**使用**协议（协议文档本身不需要安装任何运行时）」。LIMITATIONS 局限 5 的精确口径是「**协议的文档部分**零依赖，但 **gate/hook 的 enforcement** 依赖 python3+git+pyyaml」。README 用「**使用**协议」等于「文档」，**略宽**——「使用协议」若读作含 gate 执行则不成立。建议收紧为「**阅读协议文档**」或「the docs」。属**文字精度**，非事实错误（README 同句已声明安装/CI 侧「并非零基础设施」并指向 LIMITATIONS）。
  2. **README.zh-CN 粗体嵌套**：`**零基础设施（**使用侧**）。**`——同标记 `**` 嵌套，GFM 下「使用侧」不会加粗、括号被拆成两段 bold（视觉仍可读）。建议改 `**零基础设施（使用侧）。**`（英文版用 `*user*` 斜体嵌套，无此问题）。
- **ALIGNED**（两处均不阻断 commit）。

### A6: 锚点表覆盖 — ALIGNED

未新增协议规则、未新增/改名脚本；`check-protocol-consistency.py` CHECK 9 PASS（见 A8）。`source_ref` 模板改动不触及锚点表。**ALIGNED**。

### A7: 设计原则一致性 — ALIGNED

ADR-002（可判定性）/ADR-003（最小约定）/ADR-014（判据单源）/ADR-015（门禁只用于实质错误）逐条复核仍成立（同 r1）。`baseline` 单键使数据面更符合「单一事实、可判定」；`source_ref` 模板明确「机械校验 vs 仅记录」之分，与 ADR-002 的「什么被机器判定」口径一致。无未记录决策。**ALIGNED**。

### A8: 声称-命令绑定 — ALIGNED

逐条复现本批（r2）声称：

| # | 声称 | 命令 | 结论 |
|---|---|---|---|
| 1 | `BDD-19 20 passed` | `python3 -m pytest agate/tests/unit/test_upgrading_contract_doc.py -q` | **成立**（20 passed in 0.10s） |
| 2 | `check-obligations OK` | `python3 agate/scripts/check-obligations.py` | **成立**（rc=0，尾行 `CHECK-OBLIGATIONS: OK`） |
| 3 | `baseline keys 唯一` | `python3 -c "import yaml;print(list(yaml.safe_load(open('agate/rules/obligations.yaml'))['baseline'].keys()))"`（+ 字面 `reset:` 计数=1） | **成立**（`['m','total','m_ratio','note','reset']`） |
| 4 | `2901 passed` | `python3 -m pytest agate/tests/ -n auto --reruns 1 -q` | **成立**（`1 failed, 2901 passed`；唯一 failed = `test_bdd_43` 环境问题，非本 diff） |
| 5 | `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | **成立**（rc=0；`仅有 422 个 WARNING，无 ERROR`） |

**无据声称**：未发现需删除者。**ALIGNED**。

---

## 三、与 r1 结论的差异

| 项 | r1 | r2 | 说明 |
|---|---|---|---|
| A1 | MISALIGNED | **ALIGNED** | 重复 `reset:` 键 + `baseline.note` 已修 |
| A2 | MISALIGNED | **ALIGNED** | README 去禁词，BDD-19 转绿 |
| A3 | MISALIGNED | **ALIGNED** | `source_ref` 模板已修；仅 1 处测试注释残留（非阻断） |
| A4 | MISALIGNED | **ALIGNED** | 全量 pytest 无本 diff 引入失败 |
| A5 | MISALIGNED | **ALIGNED** | 自伤回归消除；2 处文字小疵（非阻断） |
| A6/A7/A8 | ALIGNED | ALIGNED | 未变 |

---

## 四、残留（非阻断，供后续清理，不阻碍本次 commit）

| 项 | 位置 | 建议 |
|---|---|---|
| 陈旧注释 | `agate/tests/unit/test_tag0050_obligations.py:65`「终态下这 **4** 条已归 `scope: protocol-repo`」 | 改为「2 条（X-10/X-19）」；因属测试文件、本批为文档/数据面，可留待下次碰该文件时顺改 |
| 文字精度 | `README.md:28` / `README.zh-CN.md:28`「**使用**协议」 | 收紧为「阅读协议文档 / the docs」，与 LIMITATIONS 局限 5 精确口径对齐 |
| Markdown | `README.zh-CN.md:28` `**零基础设施（**使用侧**）。**` | 改 `**零基础设施（使用侧）。**`，避免同标记嵌套 |
| 来源留痕 | `roadmap.md:113-114` RM-AG0114/0115 引「外部实施评审 §3」 | 源报告为仓外件，建议存档或标注「外部件」（承 r1 A8 注） |

---

**注**：本报告为**只读**审查——未修改任何协议/脚本/测试/数据文件，未 commit、未 push。跑测前后 `git status --porcelain` 逐行一致（未污染）。留痕文件见 `docs/reviews/agate-alignment-2026-10-09-REVIEW-DISP-02.progress.md`。
