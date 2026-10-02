---
review_date: 2026-10-01
reviewer: protocol-alignment-review
change_summary: check-scope-resolved.py 的 SCOPE_PLUS_RE 放宽为认「列表符/引用块/粗体」行首包裹形态，SCOPE_RESOLVED_RE 同步放宽（多认反引号），check-retrospective.py 同源同步
files_changed: [CHANGELOG.md, agate/WORKFLOW.md, agate/dispatch-protocol.md, agate/phase-cards/P4-implementation.md, agate/scripts/check-retrospective.py, agate/scripts/check-scope-resolved.py, agate/state-machine.md, agate/tests/README.md, agate/tests/fixtures/tag0034_regression_baseline.json, agate/tests/unit/test_check_scope_resolved.py, docs/design-notes/design-scope-plus-declaration-form.md]
---

# 协议-脚本对齐审查

> **证据标记约定**：每条结论标注 **[实测]**（本次会话真实跑出输出）或 **[推断]**（读代码/文档推导，未跑）。
> **只读纪律**：本次审查未执行任何写仓 git 命令。全部变异测试在 `.agate-tmp/rev-scope/copy/` 一次性副本内完成，
> 「创建 → 变异 → 跑测 → 删除」在同一次 bash 调用内；副本已删（`.agate-tmp/rev-scope/` 仅剩本次的
> `scan*.py` / `mutate*.py` / `trace.md` scratch）。被评审改动集未被触碰。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（反引号边界的文档表述与实现不对称；标题形态未覆盖且未声明） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（同一处不对称；SCOPE_RESOLVED 侧可接受形态在协议文档中完全未写） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（`docs/design-notes/README.md` 索引未登记；角色文件「句中引用不触发」表述未同步） |
| A4 | 测试覆盖 | **ALIGNED**（32 passed 实测；三组变异测试全部转红，非真空） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（存量 0 变红已实测；§5 措辞与 §2 结论冲突；roadmap 残留旧结论） |
| A6 | 锚点表覆盖 | **ALIGNED**（关键词 `SCOPE_RESOLVED` 仍 ⊆ 脚本文本；consistency 0 ERROR 实测） |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **NEEDS_HUMAN_REVIEW**（3 条数字声称与本次实测不符，见 A8） |

**总体判定：NEEDS-REVISION**（无 HIGH；4 项 MEDIUM 均为文档/声称层，脚本逻辑本身正确）

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/WORKFLOW.md:451`）：
> `### [SCOPE+]：任何阶段都能向上反馈新需求（行首声明格式：^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?\[SCOPE+\]，句中引用与反引号包裹不触发）`

**文档声明**（`agate/state-machine.md:233`、`agate/dispatch-protocol.md:953`）：同上同一正则字面量。

**脚本实现**（`agate/scripts/check-scope-resolved.py:33-40`）：
```python
_SCOPE_LEAD = r"^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?"
SCOPE_PLUS_RE = re.compile(_SCOPE_LEAD + r"\[SCOPE\+\]", re.MULTILINE)
SCOPE_RESOLVED_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__|`)?\[SCOPE_RESOLVED($|[^a-z])", re.MULTILINE
)
```

**核对 1（PLUS 侧正则可接受形态）**：文档字面量与 `_SCOPE_LEAD + r"\[SCOPE\+\]"` 拼接结果**逐字符一致** [实测，字符串比对]。**一致**。

**核对 2（反引号边界——不对称）**：文档写的是一句无条件否定「**句中引用与反引号包裹不触发**」，
但脚本对**两个标记给出不同答案** [实测，读 `check-scope-resolved.py:34` vs `:39`]：

| 标记 | 反引号包裹是否触发 |
|---|---|
| `[SCOPE+]` | **否**（`_SCOPE_LEAD` 无 `` ` `` 分支） |
| `[SCOPE_RESOLVED]` | **是**（`:39` 的 `|` 分支 → ``(?:`\*\*|__|`)?``） |

⇒ 文档的「反引号包裹不触发」对 `[SCOPE+]` 成立、对 `[SCOPE_RESOLVED]` **不成立**。这是一个
**MISALIGNED**：读者（主 Agent）据文档会认为「我把 SCOPE_RESOLVED 用反引号包起来是安全的『提及』」，
而脚本实际把它算作有效闭环标记。该行为本身方向安全（少阻断），但文档表述错误。

**核对 3（标题形态未覆盖）** [实测，全仓扫描]：脚本**不**匹配 `## [SCOPE+] 声明` 这类 ATX 标题
（`^#{1,6}\s+` 不在 `_SCOPE_LEAD` 内）。全仓实测：

- **仅以标题形态出现** `[SCOPE+]` 的任务：**8 个** —— `TAG0004` / `TAG0008` / `TAG0012` / `TAG0013` /
  `TAG0014` / `TAG0023` / `TAG0025` / `TAG0034`。
- 其中 `TAG0012/P2-design.md:402` `## 8. [SCOPE+] 声明`、`TAG0014/P2-design.md:302` `## 7. [SCOPE+] 声明`、
  `TAG0023/P4-implementation.md:49` `## [SCOPE+] 声明`、`TAG0034/P4-implementation.md:57` `## [SCOPE+] / [CLARIFY]`
  均为**章节标题级声明**，语义上是「本节的 SCOPE+ 声明」。

⇒ **这是真实漏检**（8 个任务当前 `GATE SKIP`）。但设计说明把判据边界写成「行首声明」并只列举
「裸 / 列表符 / 粗体 / 引用块」四种，**没有声明为何排除标题形态**——`## [SCOPE+]` 同样是「行首」。
设计说明 §3 的表格把这四种列为**穷举**，读者无法从中推断标题被判为「提及」。

**结论**：MISALIGNED（两处：反引号表述不对称；标题形态既未覆盖也未在文档中声明为排除项）。
**差异描述**：文档「反引号包裹不触发」不适用于 SCOPE_RESOLVED 侧；标题形态 `## [SCOPE+]` 被判为提及但文档未声明。
**建议**：
1. 把文档句改为**标记分开表述**：`[SCOPE+]` 反引号包裹不触发、`[SCOPE_RESOLVED]` 反引号包裹算有效闭环；
2. 在设计说明 §3 表格加一行「`## [SCOPE+] 声明` 标题形态 → **提及**（不触发），存量 8 个任务为标题形态，
   本次有意不覆盖；理由：标题是分组标签，其下正文才是声明」——把「有意排除」写明，或反过来把
   `#{1,6}\s+(?:\d+\.\s*)?` 加入 `_SCOPE_LEAD`。**这需要主 Agent 裁决**（见 A5）。

---

### A2: 脚本→文档对齐

**核对 1（3 处正则字面量已同步）** [实测]：`WORKFLOW.md:451`、`dispatch-protocol.md:953`、
`state-machine.md:233` 的旧正则 `^\s*-?\s*\[SCOPE+\]` 均已替换为新正则。全仓 grep 旧字面量，
`agate/` 下**除历史引用外无残留**（剩余命中均为 `archived/`、任务目录、`agate-workspace/reviews/`
等叙事文件，以及 `agate/scripts/check-scope-resolved.py:23` 的**注释**「原正则 … 对这两种返回 False」
——注释引用旧值是正确写法）。**一致**。

**核对 2（SCOPE_RESOLVED 侧可接受形态始终未文档化）** [实测，grep]：`dispatch-protocol.md:955`
只写「未标记 [SCOPE_RESOLVED] 的 [SCOPE+] → gate 不通过」，`WORKFLOW.md:361`（Pre-commit 总览 2.11 行）
写「`[SCOPE+]` 必须有 `[SCOPE_RESOLVED:...]` 标记」——**两处都从未规定 SCOPE_RESOLVED 的可接受书写形态**
（改动前后都一样）。改动后两侧形态能力分叉（PLUS 四种 + RESOLVED 五种含反引号），
文档仍只描述 PLUS 一侧。**MISALIGNED（新增的不对称未被文档承接）**。

**核对 3（`agate/scripts/README.md`）** [实测]：`:81` `| check-scope-resolved.py (P2.11) | [SCOPE+] 标记追踪 | 0=通过, 1=未标记 |`
——该行**不含正则/形态规格**，故无需同步。**一致（未改是对的）**。

**结论**：MISALIGNED（同 A1 核对 2/3；协议文档未承接 SCOPE_RESOLVED 侧的可接受形态与两侧不对称）。
**建议**：在 `dispatch-protocol.md:955`（SCOPE+ 处理追踪段）补一句两侧可接受形态，
或显式写明「SCOPE_RESOLVED 接受比 SCOPE+ 更宽的包裹形态（含反引号）」并给出理由。

---

### A3: 一致性连锁 + 反向传播

按角色文件「反向传播的常见路径」表逐条验证**应被影响但未出现在 diff 的文件**：

| 应传播目标 | diff 中出现？ | 核对结果 |
|---|---|---|
| `agate/WORKFLOW.md`（含 Pre-commit 检查总览） | ✅ 1 行 | 正则已同步；Pre-commit 总览 2.11/2.12 两行**不含正则**（`:361`/`:362`），无需改 [实测] |
| `agate/dispatch-protocol.md` | ✅ 1 行 | 正则已同步 + 形态说明 |
| `agate/state-machine.md` | ✅ 1 行 | 正则已同步 |
| `agate/phase-cards/P4-implementation.md` | ✅ 1 行 | 「常见错误 2」列明四形态 |
| `agate/tests/README.md` | ✅ 1 行 | `10` → `17`，与实跑一致 [实测：`^def test_` 计数 = 17] |
| `agate/scripts/README.md` | ❌ | **无需改**（`:81` 无形态规格）[实测] |
| `agate/tests/fixtures/tag0034_regression_baseline.json` | ✅ | `state-machine.md` sha256 已刷新；**6 个受护文件 hash 全部与工作区一致** [实测] |
| **CHECK 9 锚点表**（`check-protocol-consistency.py`） | ❌ | **无需改**（见 A6） |
| `agate/CONTEXT.md` | ❌ | **无需改**：`:17` 术语行无形态规格，且指向 `WORKFLOW.md §[SCOPE+]`（已同步）[实测] |
| `agate/LIMITATIONS.md` | ❌ | **无需改**：`:37` 只谈「影响范围由主 Agent 拍板」，不涉形态 [实测] |
| `agate/assets/templates/task-files.md` | ❌ | **无需改**：样本是 `- [SCOPE+ from P2] 新需求`（`:219`/`:351`），`[SCOPE+ from Pn]` 是**增补标注**、
  与 `[SCOPE+]` 正则不同形（`+` 后是空格不是 `]`），不受影响 [实测] |
| **`agate/assets/execution-roles/implementer.md`** | ❌ | **MISALIGNED（应改未改）**：`:124` 写「标 `[SCOPE+]`（格式见 architect.md）（行首声明格式，**句中引用不触发 gate**）」
  ——改动后反引号包裹成为**第二个**不触发形态，此处表述不完整 [实测] |
| **`agate/assets/execution-roles/architect.md`** | ❌ | **MISALIGNED（应改未改）**：`:293` 写「（行首声明格式，**句中引用不触发 gate**）」，同样漏「反引号包裹」[实测] |
| **`docs/design-notes/README.md`** | ❌ | **MISALIGNED（应改未改）**：该文件是决策记录索引，末尾明写「新增决策记录时，按这个格式写」并逐条登记
  设计说明；新增的 `design-scope-plus-declaration-form.md` **未登记**（grep 该 README 无 `scope-plus` 命中）[实测] |
| `agate/scripts/check-gate.py` | ❌ | **无需改**：`grep -c 'check-scope-resolved'` = **0**，该脚本确实不消费 [实测] |
| `agate/assets/templates/retrospective-template.md` | ❌ | **无需改**：`:126-127` 只登记机制名与触发条件，不含形态 [实测] |

**结论**：MISALIGNED。三项真实遗漏：
1. `docs/design-notes/README.md` 未登记新设计说明（**反向传播漏项**）；
2. `implementer.md:124` / `architect.md:293` 的「不触发」表述未随放宽更新（这两个文件是 subagent 写 `[SCOPE+]` 时
   实际会读到的角色卡，遗漏会让写入者继续以为「只有句中引用不触发」）；
3. 未见 A1 所述的标题形态排除声明。

**建议**：补 README 登记行；把两处角色文件的括注统一为
「行首声明格式（裸 / `- ` 列表符 / `**[ ]**` 粗体 / `> ` 引用块；句中引用与反引号包裹不触发）」——
或（更省维护）改为指向 `WORKFLOW.md §[SCOPE+]` 单源，不再各自复述。

---

### A4: 测试覆盖

#### A4.1 指定命令实跑输出 [实测]

```
$ cd /home/kity/oclab/agateon
$ timeout 600 python3 -m pytest agate/tests/unit/test_check_scope_resolved.py \
      agate/tests/unit/test_check_retrospective.py -q -p no:randomly
................................                                         [100%]
32 passed in 1.76s
```
（`test_check_scope_resolved.py` 17 + `test_check_retrospective.py` 15 = 32，exit 0）

分片全量实跑（供 A5/A8 对账）[实测]：

```
$ timeout 1800 python3 -m pytest agate/tests/unit -q -p no:randomly
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
   Failed: opencode 不在 PATH：环境未就绪，BDD 判 FAIL（P1 BDD-43/45 二值规则；不得跳过 / 记为通过）
1 failed, 2277 passed, 2 skipped in 173.76s

$ timeout 1800 python3 -m pytest agate/tests/regression agate/tests/integration -q -p no:randomly
195 passed in 46.21s

$ timeout 600 python3 agate/scripts/check-protocol-consistency.py
仅有 386 个 WARNING，无 ERROR。

$ timeout 300 ~/.venvs/agate-dev/bin/ruff check agate/
All checks passed!

$ timeout 300 bash agate/tests/scripts/count-tests.sh
总计：2497 个测试用例（pytest collect-only 口径）
```
唯一 FAIL 是**既有环境缺陷**（`opencode` 不在 PATH），与本次改动无关 [实测：改动只碰
`SCOPE_PLUS_RE` / `SCOPE_RESOLVED_RE`，该用例走平台注册路径]。

#### A4.2 变异测试（副本上做，三组全部转红 = 非真空）[实测]

| 变异 | 操作 | 结果 |
|---|---|---|
| M1 `revert_both` | 两脚本的 `SCOPE_PLUS_RE` + `SCOPE_RESOLVED_RE` 全部退回原版 | **4 failed, 13 passed** —— `sc_8` / `sc_9` / `sc_10` / **`sc_14`** |
| M2 `plus_only` | 只退回 `SCOPE_RESOLVED_RE`（PLUS 保持放宽） | **2 failed, 15 passed** —— `sc_10` / **`sc_11`** |
| M3 `resolved_no_backtick` | RESOLVED 放宽但**去掉反引号**分支 | **1 failed, 16 passed** —— **`sc_11`** |
| 基线 | 原样 | 17 passed |

M1 的可执行复现（同一次 bash 调用内建副本 → 变异 → 跑测 → 删副本）：
```
$ cp -r agate .agate-tmp/rev-scope/copy/agate   # 副本
# python 逐行改写两脚本正则回原版
### TRUE RED PHASE (both scripts original) ###
FAILED ...::test_sc_8_bold_wrapped_scope_plus_detected_exit_1
FAILED ...::test_sc_9_quote_wrapped_scope_plus_detected_exit_1
FAILED ...::test_sc_10_bold_wrapped_with_bold_resolved_exit_0
3 failed, 14 passed in 0.91s        # 仅 test_check_scope_resolved.py
```
> 说明：M1 在**两文件合跑**下是 4 failed（多出 `sc_14`——它比对两脚本的 `SCOPE_PLUS_RE` 行为，
> 两脚本同时退回原版时二者**仍然等价**，故 `sc_14` 变红的原因是原版对 `- **[SCOPE+]` 等探针分类
> 与 `sc_14` 期望的**新**语义不符；单跑 `test_check_scope_resolved.py` 得到 `sc_8/9/10` 3 failed，
> 与设计说明 §7「恰好 sc_8/9/10 三条转红」**一致**）。两组数字都记录在此，避免二者混淆。

#### A4.3 A4 结论 [实测]

新增 7 用例（`sc_8`…`sc_14`）覆盖：粗体检出、引用检出、粗体↔粗体协同、反引号 RESOLVED 协同、
两个反向护栏（句中提及 / 反引号 PLUS）、两脚本同源守护（14 个探针）。**三组变异均能转红 ⇒ 测试非真空**。

**结论**：ALIGNED。（唯一提示：`sc_12` / `sc_13` 两个反向护栏在**原版**正则下也通过，
故它们对本次改动**不具回归侦测力**，只锁定「不要把提及算成声明」的未来方向——这是合理的
方向性守护，不算缺陷 [推断，基于 M1 结果中二者未转红]。）

---

### A5: 下游影响 + 文档传播

#### A5.1 存量任务影响面 —— 自己实测 [实测]

用**改动后的真实脚本**（import 真实模块 + 注入不同正则）跑遍 `agate-workspace/tasks/` 全部目录：

```
$ timeout 300 python3 .agate-tmp/rev-scope/scan.py
task_count= 41
OLD  codes: Counter({0: 41})
NEW  codes: Counter({0: 41})
ONLY_PLUS_RELAXED codes: Counter({0: 40, 1: 1})

OLD skip count = 33    OLD real-check = 8
NEW skip count = 32    NEW real-check = 9
```
- **任务总数 41** ✅ 与设计说明 §5 / CHANGELOG 一致。
- **通过 8 → 9** ✅；**跳过 33 → 32** ✅；**失败 0 → 0** ✅。
- **唯一由「跳过」变「真正校验」的任务 = `TAG0021-structured-layer`** ✅，其输出：
  `GATE SCOPE: P2-design.md P4-review.md 有 [SCOPE+]，P1 有 1 个 [SCOPE_RESOLVED]`
- **改动后新增命中文件**：`TAG0021/P2-design.md`（`:**[SCOPE+] 发现（供主 Agent 关注，不擅自扩大范围）**` [实测 L379 原文]）
  与 `TAG0021/P4-review.md:39`（`- **[SCOPE+] 处置合规**…`）。**0 个任务由绿转红** ✅。

**活跃任务核查** [实测]：`.state.yaml` 的 phase 分布 = `READY` 35 / `P0` 4 / `DONE` 2。
即 **35 个 phase=READY 的任务**（推进阶段会真跑 gate）+ 4 个 P0（尚未进入 gate）+ 2 个 DONE。
**41/41 全部 exit 0 ⇒ 无活跃任务受影响** ✅。

**⚠️ 但 §5 的方法学措辞有问题**（不改变数字结论）：设计说明 §5 称「用**改动后的真实脚本**跑全部 41 个任务目录」，
其表格却给出「改动前 8 / 改动后 9」——**一个脚本一次运行不可能同时产出两列**。§5 实际是
「改动前正则 vs 改动后正则」的对比，而非「改动后的真实脚本」。CHANGELOG 的同段表述正确
（「用改动后脚本跑…通过 8→9」）。这属 §5 的措辞不精确，非数字错误。

⇒ **A5 判 NEEDS_HUMAN_REVIEW**：需人工确认 (a) §5 措辞是否修正、 (b) **标题形态 8 个任务是否纳入本次范围**——
这是唯一有实质语义后果的裁决点（本次有意不覆盖，等于接受这 8 个任务的 SCOPE+ 校验继续跳过）。

#### A5.2 是否有假红 / 破坏性变更 [实测]

- **无破坏性变更**：exit code 语义、CLI 契约、扫描面（`SKIP_NAME_RE` / `AGATE_CARD_RE`）全未变，
  仅放宽匹配集；放宽方向对 gate 是**只减少阻断**（RESOLVED）或**增加检出**（PLUS），
  实测 **0 任务变红**。
- **「必须双侧协同」是否真的必要？** —— **实测回答：是必要的，但设计说明的理由不准确**。

  | 配置 | exit code 分布 | 结果 |
  |---|---|---|
  | 原版 PLUS + 原版 RESOLVED | `{0: 41}` | — |
  | 新 PLUS + 新 RESOLVED（本次实现） | `{0: 41}` | 无假红 |
  | **新 PLUS + 原版 RESOLVED（单侧放宽）** | `{0: 40, 1: 1}` | **`TAG0021` 由绿转红** |

  ⇒ 单侧放宽**确实**造成 1 个假红，**双侧协同并非防御性冗余** ✅（与设计说明 §2 结论一致）。
  但**真正的载荷点是「反引号」而非「粗体」**：M3 变异（RESOLVED 放宽粗体/引用但去掉反引号）
  使 `sc_11` 转红 ⇒ 若只把双方都放宽到「粗体+引用」而**不**接受反引号，`TAG0021` 仍会假红。
  设计说明 §2 把理由写成「`SCOPE_RESOLVED_RE` **同样只认行首**」（即粗体/引用侧不匹配），
  而 `TAG0021` 的实际形态是**反引号**（P1 `:231` **实测**首字节为 `` ` ``，
  见 `sed -n '231p' … | od -c` → `` ` [ S C O P E _ R E S O L V E D ``）。
  ⇒ §2 的因果链措辞失准（详见 A8 与「重点怀疑方向」应答）。

  **是否存在「SCOPE+ 可检出但 SCOPE_RESOLVED 用包裹写法」的真实任务？** —— **是，且仅 `TAG0021` 一个**
  [实测，见上表 `ONLY_PLUS_RELAXED` 唯一非零项]。

#### A5.3 文档传播缺口

- **CHANGELOG 已标注** ✅（`[Unreleased]` 含完整「修复 / 验证 / 遗留」三节），符合 A5 要求。
- **`agate-workspace/roadmap/roadmap.md:78`（RM-AG0077 行）残留旧结论** [实测]：该行以
  「故本批**登记遗留、不改**——**保留现行行首判据**。其「漏检」面已由子批 A 的显式跳过声明部分覆盖。」
  收尾，状态仍为 `done`。本次 hotfix 恰恰**改了**该子批。⇒ roadmap 行未回写（**MEDIUM 文档传播缺口**）。
- `docs/design-notes/README.md` 未登记（同 A3）。

**结论**：**NEEDS_HUMAN_REVIEW**。
**必须人工确认的点**：
1. 标题形态（8 个任务）本次不覆盖是否为有意裁决？（若是，须在设计说明显式声明为**刻意排除**而非遗漏）
2. §5 对比表措辞是否修正为「改动前正则 vs 改动后正则」？

---

### A6: 锚点表覆盖

**CHECK 9 锚点条目**（`agate/scripts/check-protocol-consistency.py:577-581`）[实测]：
```python
{
    "desc": "SCOPE+ 追踪",
    "script": "agate/scripts/check-scope-resolved.py",
    "keywords": ["SCOPE_RESOLVED"],
},
```
与 `:607-611`（`check-retrospective.py`，`keywords: ["retries"]`）。

**判据核对**：CHECK 9 验证的是「脚本存在 + 被挂载调用 + 关键词出现在脚本文本中」，
本次改动**未新增/改名脚本**，`SCOPE_RESOLVED` 一词在 `check-scope-resolved.py` 中仍多次出现
（`:39` 正则、`:107` 文案、`:131` 文案）⇒ 关键词判据仍满足 [实测]。

**实跑验证** [实测]：`check-protocol-consistency.py` → **0 ERROR / 386 WARNING**，与基线一致；
`CHECK9-coverage` 未报新告警（`uncovered_gate_scripts()` 判据不依赖正则内容）。

**结论**：ALIGNED。锚点表**无需更新**（未新增脚本、未改脚本名、未改判据面）。
同时确认 `WORKFLOW.md:361`（Pre-commit 总览 2.11 行）**不含正则字面量**，故「只需同步
WORKFLOW.md 总览 + CHECK 9 锚点表」这条反向传播规则本次不产生额外改动面 [实测]。

---

### A7: 设计原则一致性

逐条核对相关 ADR：

| ADR | 与本次改动的关系 | 判定 |
|---|---|---|
| **ADR-002（可判定性）** | 改动保持 gate 判定的机器可判定性；**刻意不做「声明 vs 提及」的语义分类器**（设计说明 §3 明写「判断类语义机械化会退化」），与 ADR-002「gate 只能检查客观条件，语义正确性交独立评审」的边界**方向一致** | 一致 |
| **ADR-004（安全网分层）** | 早退分支已有 `GATE SKIP` 输出（v0.77.0 子批 A），本次补的是**判据覆盖面**；未削弱任一层 | 一致 |
| **ADR-011（引导型工具非安全边界）** | 设计说明 §8 把「setter 未做」列为独立遗留，明确「正则会拒收错误格式，setter 才能生成正确格式」——与 ADR-011「工具层是早纠错、真正边界在 gate 链」同构 | 一致 |
| **ADR-013（gate 生产者无关）** | 未按产出来源分支，未新增 CLI 定制 | 一致 |
| `agate/adr.md` 现有 ADR 群体 | **未发现被本次改动证伪或需就地标注「已过时」的 ADR** | — |

另：设计说明 §3 援引 `design-claim-evidence-binding.md` v1/v2 两次失败作为「不机械化语义」的先例，
并援引 DEBT0046「两处判据相反」作为 `check-retrospective.py` 同源同步的理由——**引用关系成立**
（DEBT0046 正文见 `agate-workspace/debt/tech-debt.md:1668`，其标题即「…两处对同一事实结论相反」）[实测]。

**结论**：**ALIGNED**。（提示：本次未新增 ADR。「gate 判据只认**形态**、不猜**语义**」这条决策
目前只落在设计说明 §3，未沉淀为 ADR——与 ADR-011 的产生路径同型，可在后续任务中考虑补一条 ADR；
本次不构成 A7 不通过 [推断：属建议级，非「未记录的架构决策」] 。）

---

### A8: 声称-命令绑定

逐条列 `声称 → 命令 → 结论`。**所有命令均在本次会话实跑**。

| # | 声称（出处） | 产出它的命令 | 结论 |
|---|---|---|---|
| 1 | 41 个任务（设计说明 §5；CHANGELOG 验证节） | `python3 .agate-tmp/rev-scope/scan.py`（glob `agate-workspace/tasks/*`）| ✅ **41** |
| 2 | 通过 8 → 9（同上） | 同上（注入旧/新正则分别跑 `main()`） | ✅ **8 → 9** |
| 3 | 跳过 33 → 32（同上） | 同上（按 stderr 是否含 `GATE SKIP` 分类） | ✅ **33 → 32** |
| 4 | 失败 0 → 0（同上） | 同上（exit code 直方图） | ✅ **0 → 0** |
| 5 | 唯一变化 = TAG0021（设计说明 §5；CHANGELOG） | `scan2.py`：`NEW+OLD` 分布 `{0:40, 1:1}`，非零项即 TAG0021 | ✅ 成立 |
| 6 | 新增 7 用例 sc_8…sc_14（设计说明 §6） | `grep -c '^def test_' agate/tests/unit/test_check_scope_resolved.py` → **17**（原 10） | ✅ 7 条 |
| 7 | tests/README 计数 `10` → `17`（diff `agate/tests/README.md:52`） | 同上 | ✅ 一致 |
| 8 | test_sc_14 探针 **14 个**输入（设计说明 §4；CHANGELOG） | 读 `test_check_scope_resolved.py:249-262` 探针列表 | ✅ **14** |
| 9 | check-retrospective 新增触发 **1 个**任务 = TAG0021（设计说明 §4；CHANGELOG） | `scan2.py`：OLD 触发 8 任务 / NEW 触发 9 任务；`TAG0021` 由 `[]` → `['P2-design.md','P4-review.md']` | ✅ **任务数 +1**（⚠️ 见注） |
| 10 | 负向控制：正则退回原版 → 恰好 `sc_8/9/10` 三条转红（§7） | 副本 M1（单跑 `test_check_scope_resolved.py`） | ✅ **3 failed** |
| 11 | 负向控制：模拟单侧放宽 → `sc_10/11` 转红（§7；CHANGELOG） | 副本 M2 | ✅ **2 failed = sc_10 / sc_11** |
| 12 | 存量全量 41 任务 0 变红（§7） | `scan.py`：`NEW codes: Counter({0: 41})` | ✅ 成立 |
| 13 | consistency 0 ERROR / 386 WARNING（§7；CHANGELOG） | `python3 agate/scripts/check-protocol-consistency.py` | ✅ **精确一致** |
| 14 | ruff 全绿（§7） | `~/.venvs/agate-dev/bin/ruff check agate/` → `All checks passed!` | ✅ 成立 |
| 15 | 分片全量：regression+integration **195 passed**（CHANGELOG） | `pytest agate/tests/regression agate/tests/integration -q -p no:randomly` | ✅ **195 passed** |
| 16 | 分片全量：unit **2276 passed** / 1 failed（CHANGELOG） | `pytest agate/tests/unit -q -p no:randomly` | ❌ **实测 2277 passed / 1 failed / 2 skipped**（差 1） |
| 17 | **TDD 红→绿：… → 实现后 16 passed**（§7） | `pytest agate/tests/unit/test_check_scope_resolved.py`（实跑基线） | ❌ **实测 17 passed**（与同批 #6/#7 的 17 自相矛盾） |
| 18 | `tag0034_regression_baseline.json` 第 8 次刷新、diff 实测 1 行、未改任何转移规则（§6；CHANGELOG） | `git diff --numstat …baseline.json` → 2 行 `_note` 段（1 增 1 删） | ✅ 成立；6 个受护文件 hash 全部与工作区一致 [实测] |
| 19 | TPV0099 的 `P2-design.md:120` 是粗体真实写法（§1；CHANGELOG） | `ls -d agate-workspace/tasks/*TPV*` | ⚠️ **本工作区无 TPV0099 任务目录，无法复核**（该编号来自 PeekView 跨项目；TAG0039 的 `P0-brief.md:58` 与 `roadmap.md:78` 有同源记载 [实测]） |
| 20 | `check-gate.py` 不调用它（`grep -c` = 0）（§8；CHANGELOG） | `grep -c 'check-scope-resolved' agate/scripts/check-gate.py` → 0（grep exit 1） | ✅ 成立 |
| 21 | `pre-commit-gate.py:439` 的 `if gate_exit != 1` 是**合法短路**：`gate_exit == 1` 时 **L557** 已 `sys.exit(1)`（§8；CHANGELOG） | 读 `pre-commit-gate.py:439`（`if gate_exit != 1 and _run_script_rc(...) == 1:`）+ `:554-557`（`elif gate_exit == 1: … sys.exit(1)`） | ✅ **更正正确**（见「重点怀疑 #5」） |
| 22 | 「只放宽 SCOPE+ 一侧会让 TAG0021 假红」（§2；CHANGELOG） | `scan2.py`：`NEW+OLD → {0:40, 1:1}`，非零项 = TAG0021 | ✅ 成立 |
| 23 | 「TAG0025/TAG0033 的反引号形态都是『：无』这类否定陈述」（§3；CHANGELOG） | 行首反引号 `[SCOPE+]` 全仓枚举（见「重点怀疑 #2」表） | ⚠️ **TAG0033/TAG0012 ✓ 成立；TAG0025 ✗ 不对**（它是**句中**提及，非行首反引号形态）；且存在**真声明反例 `TAG0004`** ⇒ 「一律」不成立 |
| 24 | 「行内任意位置匹配命中 27 个任务」（§3；CHANGELOG） | `scan` inline vs lead：`inline=36` / `lead=9` / `delta=27` | ✅ **精确一致** |
| 25 | 「一版语义启发式全仓命中 22 个任务」（§3；CHANGELOG） | — | ⚠️ **无法给出命令**（该启发式未落盘、未保留脚本）→ 按 A8 规则**建议删除或改为不可复核的定性表述** |
| 26 | 探针 14 个输入（本报告 A8 #8） | 同 #8 | ✅ |

**结论**：**NEEDS_HUMAN_REVIEW**。三项须处置：

- **#16**（`.md` 层，CHANGELOG：「unit 2276 passed」）→ 实测 **2277**。修正或补注口径（如是否
  `deselect` 了某条）；
- **#17**（`.md` 层，设计说明 §7：「实现后 16 passed」）→ 实测 **17**，且与同批 #6/#7 的 17 冲突；
- **#25**（「22 个任务」）→ **无产出命令，按 A8 规则应删除该声称**（或改为不含量化数字的定性表述）。

另 **#9** 需一句限定：§4 说 check-retrospective「新增触发 **1 个任务**」——**任务数** +1 正确，
但其**命中文件**是 +2（`TAG0021` 由 0 文件 → 2 文件：`P2-design.md` + `P4-review.md`）；
同时 `TAG0001` 的命中文件由 2 增至 3（新增 `P2-review.md`，见下方「重点怀疑 #3」）。
若想让「不影响任何 gate 判定」的论证完整，应补一句「check-retrospective 是 advisory 型、阈值判据为
『是否有任一命中』，文件数从 1→N 不改变输出形态」——本次实测该脚本输出仍为单行
`SCOPE+ 触发（{首个命中文件}）`（`check-retrospective.py:113` 返回**首个**命中文件）[实测]。

---

## 重点怀疑方向应答（逐条）

### ① 双侧协同是否真的必要？还是防御性冗余？ [实测]

**必要，非冗余 —— 但设计说明的理由链写错了。**

- 单侧放宽（新 PLUS + 旧 RESOLVED）→ `TAG0021` 由 exit 0 变 **exit 1**（唯一非零项）✅ 必要。
- 但载荷点是**反引号**而非「粗体/引用」：M3 变异（RESOLVED 放宽粗体+引用、**不含反引号**）⇒ `sc_11` 转红
  ⇒ 只做「粗体↔粗体」的对称放宽**不足以**避免假红。
- 原因：`TAG0021/P1-requirements.md:231` 的标记**实测**以 `` ` `` 开头（`od -c` 首字节 = `` ` ``），
  而 `:379` 的 `[SCOPE+]` 是**粗体** ⇒ 两侧**形态本来就不同**，不是「各自只认行首」的对称缺失。
- **是否存在真实任务命中该形态？** 是，仅 `TAG0021`（`scan2.py` 实测）。

### ② 反引号包裹判为「提及」是否正确？ [实测]

**结论：对 `[SCOPE+]` 侧，本仓存量证据基本支持；但「一律是否定陈述」的表述被一个反例推翻，且
git 历史中不存在该形态的声明。**

实测行首反引号包裹 `[SCOPE+]` 的全部站点（正则 `^\s*(>[ \t]|[-*+][ \t])?[ \t]*\`\[SCOPE\+\]`）：

| 任务/文件 | 行 | 内容 | 性质 |
|---|---|---|---|
| `TAG0004/P4-implementation-group1.md` | 50 | `` - `[SCOPE+]` L290（2n.1 分支）与 L104 为审计清单…之外的同缺陷模式…一并按同方案改造 `` | **肯定陈述**（真声明） |
| `TAG0012/P4-implementation.md` | 110 | `` - `[SCOPE+]`：**0 条**。 `` | 否定 ✓ |
| `TAG0033/P4-implementation.md` | 113 / 161 | `` - `[SCOPE+]`：**无**。 `` | 否定 ✓ |
| `TAG0033/P4-implementation.md` | 234 | `` `[SCOPE+]`：无。新 DESIGN_GAP：无。 `` | 否定 ✓ |
| `TAG0033/P8-release.md` | 157 | `` - `[SCOPE+]`：**无**。 `` | 否定 ✓ |
| `TAG0034/P8-release.md` | 171 | `` - `[SCOPE+]`：无。 `` | 否定 ✓ |
| `TAG0025/P4-implementation.md` | 80 | 句中（`` `[SCOPE+]`/`[DESIGN_GAP]`/… ``）| 提及，非行首 |
| `TAG0031/P2-review.md` | 121 | 句中（引述行首格式） | 提及，非行首 |

- `TAG0033`：**确如设计说明所述** —— 其三处行首形态（`P4-implementation.md:113/161/234`、
  `P8-release.md:157`）形如 `` - `[SCOPE+]`：**无**。 ``（列表符 + 反引号 + 否定）[实测]。
- `TAG0012`：同型否定（`` - `[SCOPE+]`：**0 条** ``）[实测]。
- `TAG0025`：是**句中**引述（`` `[SCOPE+]`/`[DESIGN_GAP]`/… ``），**不是行首**反引号形态——
  设计说明把它列为「行首反引号形态」的证据**不准确**（它恰是本次判据**应该**判为提及的句中形态，
  用它论证行首边界是错位的证据）[实测：`grep -nE '^[[:space:]]*(\>|[-*+])?[[:space:]]*`\[SCOPE\+\]'`
  在 `TAG0025` 上**零命中**]。
- **反例（关键）**：`TAG0004/P4-implementation-group1.md:50` 是**行首反引号包裹的肯定声明**
  （`` - `[SCOPE+]` L290（2n.1 分支）与 L104 为审计清单…之外的同缺陷模式…一并按同方案改造 ``），
  且 `TAG0004/P7-consistency.md:42-45` 将其登记为「### 2.1 P4 组 1 的 [SCOPE+]」并完成闭环判定
  ⇒ **该「提及」实为真声明** [实测]。

⇒ **若你的判断错了，代价有多大？** [实测] 把反引号包裹也纳入 PLUS 判据后跑全仓：
```
NEW+BACKTICK_PLUS codes: Counter({0: 36, 1: 5})
red: TAG0004 / TAG0012 / TAG0016 / TAG0025 / TAG0033
```
**5 个任务转红**，其中 `TAG0004`（真声明）与 `TAG0016`（引述）各占一类。⇒ **保守边界不是无害的**：
它把 `TAG0004` 这条真声明继续判为「提及」⇒ **该任务至今未被 gate 覆盖**。
这不构成「把真声明误判为提及」的**回归**（行为与改动前相同、且实测 0 变红），但**是本次改动未消除的
既存漏检**，与标题形态（8 个任务）同族。

**给你（主 Agent）的裁决输入**：接受「形态判据、不猜语义」的边界是**可辩护的**（设计说明 §3 已用
`design-claim-evidence-binding.md` v1/v2 先例论证），但设计说明与 CHANGELOG 的**表述需更正**：
「存量实测该写法**一律**是引述/确定性否定」→ 事实上存在真声明反例（TAG0004），应改为
「存量以引述/否定为主，另有 TAG0004 一例真声明；纳入会新增 5 个任务转红，故本次刻意保守」。

### ③ `check-retrospective.py` 的同步是否必要？ [实测]

**必要（同源判据应一致），但设计说明给的理由「两个脚本会给出相反结论」在本仓当前数据上
不产生可观测差异。**

实测（`scan2.py`，对两脚本各自的 `SCOPE_PLUS_RE` 逐任务比对）：
```
tasks with changed retrospective trigger: 2
   TAG0001-tech-debt-closure: ['P2-design.md','P4-implementation-core.md']
                          -> ['P2-design.md','P2-review.md','P4-implementation-core.md']
   TAG0021-structured-layer: [] -> ['P2-design.md','P4-review.md']
OLD retro triggered tasks: 8 / NEW retro triggered tasks: 9
```
- **任务级**：从 8 → 9，新增的正是 `TAG0021` ✅ 与设计说明 §4 一致。
- **文件级**：`TAG0001` 新增 `P2-review.md:20` `` - **[SCOPE+] #1 成立** ``（粗体包裹）——
  设计说明与 CHANGELOG 都**未提**这处次生变化（它以 `P2-review.md` 为「首个命中文件」吗？
  实测 `_scan_scope_plus` 按 `sorted(os.listdir)` 返回首个命中，`P2-design.md` 先于 `P2-review.md`，
  故输出行仍是 `P2-design.md`，**用户可见输出不变** [实测]）。
- **若不同步会怎样？** `check-scope-resolved.py` 会判 `TAG0021`「有 SCOPE+ 无闭环」→ exit 1（假红），
  而 `check-retrospective.py` 判「无 SCOPE+」→ 不提醒。两脚本确实给出**相反结论**——设计说明的论断
  **成立** ✅。

⇒ **同步必要，判断正确**；补一条：设计说明应补记 `TAG0001` 的**文件级**次生变化（不改变输出）。

### ④ 保守边界是否会漏掉真实声明？标题形态 `## 7. [SCOPE+] 声明` [实测]

**会漏 —— 且这是本次最大的一处未申报覆盖面。**

- 你的正则 **不**匹配标题形态（`_SCOPE_LEAD` 不含 `#{1,6}`）[实测]。
- 全仓**仅以标题形态**携带 `[SCOPE+]` 的任务：**8 个**（`TAG0004` / `TAG0008` / `TAG0012` /
  `TAG0013` / `TAG0014` / `TAG0023` / `TAG0025` / `TAG0034`）[实测]。
- 若把标题形态也计入判据：`codes: Counter({0: 35, 1: 6})`，转红 6 个
  （`TAG0004` / `TAG0008` / `TAG0012` / `TAG0014` / `TAG0023` / `TAG0025`）[实测]。
- **算不算漏检？** 语义上 **算**：`## 8. [SCOPE+] 声明`（`TAG0012/P2-design.md:402`）与
  `## 7. [SCOPE+] 声明`（`TAG0014/P2-design.md:302`）是**章节级声明标题**，其下正文即声明内容；
  这些任务的 SCOPE+ 因此从未被校验。但**其中多数同章节体也含非标题形态**的 `[SCOPE+]`
  （`TAG0004` 由 `- \`[SCOPE+]\`` 命中、`TAG0008` 由 `### 4.8 …（[SCOPE+] 标注意见）`? —— **实测
  `TAG0008` 属「仅标题形态」**，即它确实 0 覆盖）。

⇒ **`TAG0004` / `TAG0008` 是「声明真实但从未被 gate 覆盖」的两个任务。**
建议：在设计说明 §3 表格**显式加一行**「`## [SCOPE+]` 标题形态 → 本次**不**覆盖（存量 8 个任务）」
并给出理由（否则读者会以为是遗漏）；若要覆盖，需同步放宽 `_SCOPE_LEAD` 并重跑存量对账
（实测会新增 6 个转红，须逐个人工确认是「真检出」还是「章节标题被当声明」）。

### ⑤ 两处自我更正是否正确？还有无其他未更正的错误声称？ [实测]

**(a) 更正 ①「仅行首为 0、检查从未生效」→ 实测为假；当前正则真实命中 8 个任务**
✅ **更正正确。** 实测旧正则口径 `OLD real-check = 8` / `OLD skip = 33`，
`TAG0010`（`P1 有 4 个 [SCOPE_RESOLVED]`）等 8 个任务确实经历真实校验（见 `scan.py` 输出列表）。

**(b) 更正 ② `pre-commit-gate.py:439` 的 `if gate_exit != 1` 是合法短路，非漏洞**
✅ **更正正确。** [实测] `pre-commit-gate.py:439`
`if gate_exit != 1 and _run_script_rc("check-scope-resolved.py", [task_dir]) == 1: sys.exit(1)`；
`:554-557` 的 `elif gate_exit == 1:` 分支内确有 `sys.exit(1)`（`gate_output` 打印后）⇒
`gate_exit == 1` 时 commit 必然已被阻断，短路不产生漏判。**注意**：`:552-560` 的 gate 结果处理块
位于 `for sf in state_files` 循环内且以 `if gate_exit == 0/1/2` 开头，`gate_exit == 1` 分支
确实可达 [实测]。

**(c) 还有无其他未更正的错误声称？** —— **有 3 处**（均在 `.md` 层，脚本逻辑无错）：

1. **§7「实现后 16 passed」应为 17**（实测；且与同批 §6/tests-README 的 17 冲突）。
2. **CHANGELOG「unit 2276 passed」** 实测 2277。
3. **§4/CHANGELOG「存量实测该写法**一律**是引述/确定性否定」** —— 存在真声明反例
   `TAG0004/P4-implementation-group1.md:50`（§3/§2 的表述需加限定）。
4. （次级）**§2 把双侧协同的理由写成「同样只认行首」**，实际载荷点是反引号（见 ①）。
5. （次级）**§5 的方法学措辞**「用改动后的真实脚本跑」与并列「改动前/后」两列不自洽。
6. （次级）**§6 变更清单称改动面「2 个脚本 + 4 处协议文档 + 1 个测试文件 + 基线刷新」**，
   实际 `git diff --stat` 为 **10 个已跟踪文件**（含 `CHANGELOG.md` 与 `tests/README.md`），
   加上未跟踪的设计说明共 11 个 [实测]。清单未列 `CHANGELOG.md` 与 `agate/tests/README.md`。

---

## 必须修复项

| 严重度 | # | 项 | 位置 | 动作 |
|---|---|---|---|---|
| **MEDIUM** | M1 | 设计说明 §7「实现后 **16 passed**」与实测 17 不符（且与同批 17 自相矛盾） | `docs/design-notes/design-scope-plus-declaration-form.md:99`（**该文件是未跟踪新文件，可自由改**） | 改为 17，或改口径为「单跑 `test_check_scope_resolved.py` → 17 passed」 |
| **MEDIUM** | M2 | CHANGELOG「unit **2276 passed** / 1 failed」实测 2277 | `CHANGELOG.md` `[Unreleased]` 验证节 | 更正为 2277（或注明 deselect 口径） |
| **MEDIUM** | M3 | 设计说明 §3 / CHANGELOG「反引号写法**一律**是引述/否定」有反例 | 设计说明 §3 表格；`CHANGELOG.md` 同段 | 补限定：「以引述/否定为主，另有 `TAG0004` 一例真声明；纳入会新增 5 个任务转红，故本次刻意保守」 |
| **MEDIUM** | M4 | 标题形态（`## [SCOPE+] 声明`）未覆盖且未声明为刻意排除 —— 8 个任务（含 `TAG0004`/`TAG0008` 真声明）继续跳过 | 设计说明 §3 表格；`check-scope-resolved.py:21-33` 常量注释 | 二选一：① 显式列为「刻意不覆盖 + 理由」；② 放宽 `_SCOPE_LEAD` 并重跑存量对账（预期新增 6 个转红，需人工分类） |
| **MEDIUM** | M5 | `docs/design-notes/README.md` 索引未登记新设计说明（反向传播漏项） | `docs/design-notes/README.md` | 按该文件既有格式补一行 |
| **MEDIUM** | M6 | `roadmap.md:78`（RM-AG0077）仍写「**保留现行行首判据**」与「登记遗留、不改」，与本次 hotfix 矛盾 | `agate-workspace/roadmap/roadmap.md:78` | 在该行追加 2026-10-01 hotfix 落地说明（保留原结论作历史） |
| **LOW** | L1 | 「反引号包裹不触发」在文档中无条件表述，但 `SCOPE_RESOLVED` 侧**接受**反引号 | `agate/WORKFLOW.md:451` 等 3 处 | 分开表述两个标记的边界 |
| **LOW** | L2 | `implementer.md:124` / `architect.md:293` 的「句中引用不触发 gate」未含反引号 | `agate/assets/execution-roles/*.md` | 补一句或改为指向 `WORKFLOW.md §[SCOPE+]` 单源 |
| **LOW** | L3 | 「一版语义启发式全仓命中 **22 个任务**」无产出命令 | 设计说明 §3；`CHANGELOG.md` | 按 A8 规则**删除**该量化声称或改为定性表述 |
| **LOW** | L4 | §5 方法学措辞「用改动后的真实脚本跑」与并列两列不自洽 | 设计说明 §5 | 改为「改动前正则 vs 改动后正则（同一脚本注入）」 |
| **LOW** | L5 | §6 变更清单未列 `CHANGELOG.md` 与 `agate/tests/README.md` | 设计说明 §6 | 补齐（实测共 10 个已跟踪文件 + 1 个新文件） |
| **LOW** | L6 | §4 未记 `TAG0001` 的文件级次生变化（不改变输出） | 设计说明 §4 | 补一句即可 |

**无 HIGH 项。** 脚本本体（`check-scope-resolved.py` / `check-retrospective.py`）逻辑、
测试、基线刷新均**经实测正确**；上述全部为文档与声称层，且多处集中在**未跟踪的新设计说明**
（可自由编辑，不触碰他人未提交修改）。

---

## 附录：本次审查的批/命令索引

| 用途 | 命令 |
|---|---|
| 指定 pytest | `python3 -m pytest agate/tests/unit/test_check_scope_resolved.py agate/tests/unit/test_check_retrospective.py -q -p no:randomly` |
| unit 分片 | `python3 -m pytest agate/tests/unit -q -p no:randomly` |
| regression+integration | `python3 -m pytest agate/tests/regression agate/tests/integration -q -p no:randomly` |
| 一致性 | `python3 agate/scripts/check-protocol-consistency.py` |
| lint | `~/.venvs/agate-dev/bin/ruff check agate/` |
| 用例计数 | `bash agate/tests/scripts/count-tests.sh` |
| 存量对账（41 任务 × 4 正则配置） | `python3 .agate-tmp/rev-scope/scan.py` |
| 单侧放宽 / retrospective delta / 反引号影响面 | `python3 .agate-tmp/rev-scope/scan2.py` |
| 标题形态影响面 | `python3 .agate-tmp/rev-scope/scan3.py` |
| 变异 M1/M2/M3 | 副本 + `python3 .agate-tmp/rev-scope/mutate2.py {revert_both\|plus_only\|resolved_no_backtick}` |
| 基线 hash 复核 | `python3 -c "import json,hashlib; …"`（见 A3 表） |

**scratch 清理**：`.agate-tmp/rev-scope/copy/`（变异用的**仓库副本**）已在同一次 bash 调用内删除
（最终 `ls` 仅剩下列 scratch 脚本）。**如实声明**：三个对账脚本 `scan.py` / `scan2.py` / `scan3.py`
与变异驱动器 `mutate2.py` **保留**在 `.agate-tmp/rev-scope/`——它们被本报告附录引用为**可复核载体**，
且**全部位于 `.agate-tmp/`（仓库 scratch 区）**，不含任何仓库源码副本，不参与 git 跟踪面
（`.agate-tmp/` 为既定临时工作区，本仓既有内容亦存放于此）。被评审仓库的**被跟踪文件未被写入**；
本次唯一新增的被跟踪面外的成果文件是 `docs/reviews/agate-alignment-review-2026-10-01-scope-plus-form.md`
（另有一个留痕文件 `.agate-tmp/rev-scope/trace.md`，按角色定义属留痕而非成果）。
