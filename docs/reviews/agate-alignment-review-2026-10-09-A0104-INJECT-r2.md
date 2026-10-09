---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0104（DEBT0052+DEBT0057）r2 复核——核实 r1 三处发现的改正（A4 单测判别力、A2/A3 WORKFLOW 2y 登记、A1 2y 行级锚定）
files_changed: [agate/scripts/agate-inject-card.py, agate/scripts/pre-commit-gate.py, agate/WORKFLOW.md, agate/tests/unit/test_agate_inject_card.py, agate/tests/integration/test_pre_commit_hook.py, CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md]
---

# 协议-脚本对齐审查（r2 复核）

**审查对象**：分支 `hotfix/batch-a-inject-card` 未提交工作区改动（HEAD=`47b49b50`）；本报告独立复核 r1（`agate-alignment-review-2026-10-09-A0104-INJECT.md`）三处发现的改正。
**只读声明**：未修改任何协议/脚本/测试，未 commit/push；scratch 复现均在一次性副本内「创建→操作→清理」；跑测试前后 `git status --porcelain` 一致（仅多出本报告与两份留痕文件）。
**独立复现声明**：A4 判别力、A1 口径差异均由本审查自建旧实现/真实 2y 副本实测，未采信实施方结论。

## 审查结论汇总

| # | 审查项 | r1 结论 | r2 结论 |
|---|--------|---------|---------|
| A1 | 文档→脚本对齐 | NEEDS_HUMAN_REVIEW | **NEEDS_HUMAN_REVIEW**（具体缺陷已闭合；剩口径不一致 + 注释不实） |
| A2 | 脚本→文档对齐 | MISALIGNED | **ALIGNED**（已修） |
| A3 | 一致性连锁 + 反向传播 | MISALIGNED | **ALIGNED**（已修） |
| A4 | 测试覆盖 | MISALIGNED | **ALIGNED**（已修，独立复现判别力） |
| A5 | 下游影响 + 文档传播 | ALIGNED | **ALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED** |
| A7 | 设计原则一致性 | ALIGNED | **ALIGNED**（ADR-014 见 A1） |
| A8 | 声称-命令绑定 | ALIGNED（措辞） | **ALIGNED**（roadmap 措辞仍未收紧，非阻塞） |

## r1 发现逐条核实

### r1-A4（新单测无判别力）→ **已修，独立复现判别力** ✓

**改动**（`test_agate_inject_card.py:310-341`）：
- 夹具改为**空占位块**（`:323-327`：`<!-- AGATE_CARD_START -->\n<!-- AGATE_CARD_END -->`，注入后才被填充）；
- 断言改为独特汇总串（`:340`：`"个 dispatch-context 注入失败"`）。

**独立复现**（自建假协议树：`scripts/` 副本 + `agate-inject-card.py` 回退 `sys.exit(1)`，`AGATE_ROOT` 指向它）：
```
AGATE_ROOT=<fake-old> pytest agate/tests/unit/test_agate_inject_card.py::test_rm_ag0104_first_missing_placeholder_does_not_skip_rest
→ 1 failed  (AssertionError: b-good 应仍被注入…assert '')      # 旧实现下转红 ✓
真实仓：pytest …::test_rm_ag0104_first_missing_placeholder_does_not_skip_rest → 1 passed
真实仓：pytest agate/tests/unit/test_agate_inject_card.py -n auto → 12 passed
```
- 三条断言现均可判别：① `rc != 0`（两版都真，非判别项）；② `_between_markers(...).strip()`——空块未注入时 = `''`（falsy）→ **未注入必转红**；③ `"个 dispatch-context 注入失败"`——旧版透传消息是 `AGATE_CARD 注入失败:`（**不含**该串）→ **只在新版汇总行出现**。
- **残余（非阻塞）**：「全失败」（所有文件都缺占位符 → 汇总 `N/N`）仍无专用用例（r1 已提）。

**结论**：**ALIGNED**（r1 的 MISALIGNED 闭合）。

### r1-A2/A3（2y 未登记进 WORKFLOW 总览）→ **已修** ✓

**改动**（`agate/WORKFLOW.md:364`，插在 2z 前）：
> `| 2y | （pre-commit-gate.py 内置） | 暂存 P{n}-dispatch-context-*.md 时（与 .state.yaml 无关，循环外） | 仓库级 | dispatch-context 占位符行存在性校验（须独占一行的 <!-- AGATE_CARD_START --> / <!-- AGATE_CARD_END -->）；缺 → 阻断 commit（RM-AG0104 / DEBT0057） |`

**核实**：
- 列数 = **5**（与表头 `| # | 检查脚本 | 触发条件 | 阶段/机制 | 行为 |` 一致；2z 行同 5 列）——脚本列宽实测。
- 内容与实现一致（描述「占位符**行**、独占一行」= r2 的行级锚定）。
- 顺序：表中 2y 在 2z 前；代码执行序亦为 2y→2z，一致。
- `check-protocol-consistency.py` → **0 ERROR**（424 frozen WARNING，与 r1 同，未新增）。

**结论**：**ALIGNED**（r1 的 MISALIGNED 闭合）。

### r1-A1（2y 子串判定偏弱）→ 具体缺陷**已闭合**，但**口径仍不一致** ⚠

**改动**（`pre-commit-gate.py:1124-1126`）：子串判定 → 行级锚定 `re.search(r"^<!-- AGATE_CARD_START -->$", _txt, re.M)` / END 同。

**① r1 具体缺陷已闭合**（真实 2y 副本，scratch）：
- 散文提及 `AGATE_CARD_START`/`END`（非注释对）的文件 → 暂存 commit **`rc=1` 阻断**（r1 时 `rc=0` 放行）✓。

**② 但 2y 与 `agate-card-inject.py` 的**实际**匹配口径**不一致**（任务要求核对，逐字引用）**：
- `agate-card-inject.py:17-18`：
  > `pattern = r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)"` … `re.search(pattern, text, flags=re.DOTALL)`
- 该正则是 **DOTALL、非行锚定**：START 仅要求「`-->` 紧跟一个 `\n`」（**允许行首有其它文本**），END 匹配**任意位置**。它**不是**行级匹配。
- 2y 的 `^…$`（`re.M`）要求标记**独占一行**。二者**不相等**，实测两向分歧（scratch，真实 2y）：

| 场景 | 2y | `agate-card-inject.py` | 分歧性质 |
|---|---|---|---|
| `abc <!-- AGATE_CARD_START -->\n<!-- AGATE_CARD_END -->` | 阻断 `rc=1` | 注入成功 `rc=0` | **2y 更严 → 误伤**（拦了 inject 能处理的文件） |
| `<!-- AGATE_CARD_END -->\n<!-- AGATE_CARD_START -->`（END 在前） | 放行 `rc=0` | `未找到占位符` `rc=1` | **2y 更松 → 漏放** |

- ⇒ 代码注释 `pre-commit-gate.py:1122`「`agate-card-inject.py` **亦按行匹配**」**与事实不符**（inject 非行锚定）。

**③ 存量/边界无误伤**（不改变②的结论，仅供定级）：
- 全仓 834 个 `P{n}-dispatch-context*.md`：inject 兼容 **833**、2y 兼容 **833**、**mismatch 0** ⇒ 存量文件无一受影响。
- CRLF 文件（标记独占行）：2y 放行 `rc=0`（文本模式读取 universal newlines 归一）⇒ 无 CRLF 误伤。

**结论**：**NEEDS_HUMAN_REVIEW**。
**差异**：r1 要求「2y 与 inject 的实际判据一致（判据单源，ADR-014）」。r2 修好了「子串被散文满足」的具体缺陷，但**未达到与 inject 的口径一致**——2y 现为「独占一行」的**更严**判据（并在一处更松）。代码注释对此的表述不实。
**建议**（二选一，均需人工确认）：
- **(a) 接受更严 + 改注释**：2y 要求「独占一行」是**对文档模板形态的严格化**（`dispatch-protocol.md:360-362` / `assets/templates/dispatch-context.md:52,56` 的占位符本就独占一行），可辩护为有意选择；则须把 `pre-commit-gate.py:1122` 注释改为「2y 比 `agate-card-inject.py` 更严格：要求标记独占一行（文档模板形态），inject 本身为 DOTALL 非行锚定」。
- **(b) 判据单源**：2y 直接复用 `agate-card-inject.py` 的同一正则（`re.search(r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)", _txt, re.DOTALL)`），使「占位符可注入」判据单源，彻底消除分歧。

> 缓解：无论 (a)/(b)，即便 2y 漏放，注入链的**不再早退**保证失败在末尾被显式汇总，不再静默（DEBT0052 主项已闭合）。

---

## 逐项审查（r2）

### A1: 文档→脚本对齐 → NEEDS_HUMAN_REVIEW
见上「r1-A1」。**具体缺陷闭合，口径一致性待人工裁决 + 注释待修正。**

### A2: 脚本→文档对齐 → ALIGNED
`WORKFLOW.md:364` 已补 2y 行（唯一事实源），与 2z 对称，列数/内容/顺序正确。

### A3: 一致性连锁 + 反向传播 → ALIGNED
r1 A3b 表逐项复验：`WORKFLOW.md` **已补**（闭合）；`dispatch-protocol.md`/模板/`scripts/README.md`/`tests/README.md`/CHECK9/调用方 均确认**不需改**（同 r1）。r2 新增改动（行级锚定）未引出新的应传播文件（文档模板形态未变）。「生产端 fail-fast 同类模式」结论沿用 r1（未发现第二处）。

### A4: 测试覆盖 → ALIGNED
判别力已独立复现（见 r1-A4）。实跑：
```
pytest agate/tests/unit/test_agate_inject_card.py -n auto -q                 → 12 passed
pytest agate/tests/unit/test_agate_inject_card.py::test_rm_ag0104_…          → 1 passed
pytest <RM-AG0088×2 + RM-AG0104×1 integration> -q                            → 3 passed
```
残余（非阻塞）：「全失败」用例未补；集成测（r1 已验证有判别力）本次未改，仍有效。

### A5: 下游影响 + 文档传播 → ALIGNED
- CHANGELOG（`:62-68`）已标注；`agate-inject-card.py` 退出码契约不变。
- 2y 行级锚定**未引入存量误伤**（834 文件 mismatch 0；CRLF 无碍）——虽理论上更严，但符合文档模板形态。
- 无破坏性变更。

### A6: 锚点表覆盖 → ALIGNED
无新增/改名 `check-*.py`；`pre-commit-gate.py` 仍被 CHECK 9 显式豁免（`check-protocol-consistency.py:901`）。CHECK 9 实跑 PASS。

### A7: 设计原则一致性 → ALIGNED
ADR-004/002/015 同 r1（符合）。**ADR-014（判据单一权威源）**：r2 仍未使 2y 与 inject 判据单源——已在 A1 记为 NEEDS_HUMAN_REVIEW（建议 (b) 即 ADR-014 的落地）。

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|---|---|---|
| `1 passed`（新单测） | `pytest agate/tests/unit/test_agate_inject_card.py::test_rm_ag0104_first_missing_placeholder_does_not_skip_rest -q` | ✓ 1 passed |
| `16 passed` | `pytest agate/tests/unit/test_agate_inject_card.py agate/tests/integration/test_pre_commit_hook.py -k "inject or rm_ag0104 or rm_ag0088 or debt" -q` | ✓ 16 passed（该选择器复现；具体选择器未由实施方给定） |
| `2903 passed`（全量） | `pytest agate/tests/ --reruns 1 -n auto -q` | ✓ 2903 passed（**同批 1 failed**：`test_setup_agate_dir.py::test_bdd_43` 环境因 opencode CLI `debug agent` 改名，与本批无关，测试文件不在 diff） |
| `0 ERROR`（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | ✓ rc=0，0 ERROR（424 frozen WARNING） |

补充（沿用 r1，非阻塞）：roadmap `RM-AG0104` 更新列仍写「全量 pytest/consistency 0 ERROR」——「全量 pytest」非全绿（1 环境失败），建议按批 B 先例改为「2903 passed + consistency 0 ERROR」。

**结论**：ALIGNED。

---

## 是否可 commit

**结论：有条件可 commit。**

- r1 两处 MISALIGNED（A2/A3、A4）**均已实质修复并独立复现闭合**；
- r1 一处 NEEDS_HUMAN_REVIEW（A1）的**具体缺陷（散文提及被放行）已闭合**，但**仍存在**：(i) 2y（独占一行）与 `agate-card-inject.py`（DOTALL 非行锚定）**口径不一致**；(ii) 代码注释 `pre-commit-gate.py:1122`「inject 亦按行匹配」**表述不实**。
- 按角色闭环规则，NEEDS_HUMAN_REVIEW 需人工确认。请人工：
  1. 确认「2y 独占一行」为有意严格化（**并修正 :1122 注释**），或改为复用 inject 正则（判据单源）；
  2. 补 `[HUMAN_CONFIRMED: 日期 确认：理由]`。
- 完成上述后即可 commit。非阻塞建议：补「全失败」用例；收紧 roadmap「全量 pytest」措辞。
