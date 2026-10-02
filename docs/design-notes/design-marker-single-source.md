# 正文标记单源：判据注册表 + 生成器设计（v1 待审）

> **日期**：2026-10-02
> **状态**：**设计待审**（未落地）。本文件只做设计，不含实现。
> **动机来源**：SCOPE+ 行首形态 hotfix（PR #387）暴露的漂移代价——**改 1 个标记的形态，被迫同步 8 处，且漏了 5 处**（被终审抓出）。
> **要解决的**：正文标记的**判据漂移**（不是"语法不统一"）；并让「新增标记」的边际成本从 N 处降到 1 行。
> **不解决的**：声明 vs 提及的**语义判断**（见 §7）。

---

## 1. 问题定义（用实测数据，不用感受）

### 1.1 现状：标记多、判据散、无一致性检查

全仓实测（`agate/**`，判据 `\[([A-Z][A-Z_]{2,})(?::[^\]]{0,40})?\]`，下附可复核命令）：

| 事实 | 数值 |
|---|---|
| 出现的正文标记种类（全部） | **45 种** |
| ≥3 次的标记 | **30 种** |
| 带参数形态的标记 | 8 种（`[DESIGN_GAP: xxx]` / `[SUGGEST: ...]` 等） |
| **成对/互斥**的标记 | 4 组：`SCOPE+`↔`SCOPE_RESOLVED`、`DESIGN_GAP`↔`DESIGN_GAP_REVIEWED`、`NEED_CONFIRM`↔`NO_NEED_CONFIRM`、`PROD_TOUCHED`↔`PROD_NOT_TOUCHED` |
| **有机械判据**（脚本真在判）的标记 | **仅 2 个**：`SCOPE+`/`SCOPE_RESOLVED`（`check-scope-resolved.py`）、`DESIGN_GAP`（`check-gate.py` 等） |
| 其余标记 | 只有**文档复述**，无机械判据 |

### 1.2 判据分布（改变一个标记要动几处）

实测口径：`SCOPE_PLUS_RE`/正则字面量（脚本+测试）与「行首声明格式」措辞（文档）所在文件数。

| 标记 | 脚本/测试处 | 文档处 | 合计 |
|---|---|---|---|
| `DESIGN_GAP` | 14 | 18 | **32** |
| `NEED_CONFIRM` | 9 | 19 | **28** |
| `PROD_TOUCHED` | 5 | 17 | **22** |
| `SCOPE_RESOLVED` | 4 | 7 | 11 |
| `SCOPE_PLUS` | **4**（2 脚本 + 1 测试 + 1 基线 fixture） | **8**（含「行首声明格式」措辞的文档） | **12** |

> **⚠️ 更正（自查）**：初稿把 `SCOPE_PLUS` 文档处写成 **0**——那是**错的口径**（我用「`SCOPE_PLUS` 字面量」搜文档，而文档写的是 `[SCOPE+]`）。实测含「行首声明格式」措辞的文档有 8 个文件。
> **⇒ 这恰好又演示了一遍本设计要治的病**：同一事实换个口径就得到不同数字。**数字必须与判据绑定**（本设计 §6 的验收锚即为此）。

**⇒ 最重的标记要改 32 处；`SCOPE_PLUS` 是 12 处。**

### 1.3 漂移的真实代价（PR #387 实测账）

只改 `[SCOPE+]` **一个**标记的形态，commit `6101a9e` 实测改动 **18 个已跟踪文件**（`git show --name-only 6101a9e | wc -l`，含 3 份评审报告 + 1 份设计说明）：

| 面 | 文件 | 数 |
|---|---|---|
| **判据面**（必须同步，否则判定不一致） | `check-scope-resolved.py`、`check-retrospective.py`、`test_check_scope_resolved.py`、`tag0034_regression_baseline.json` | **4** |
| **文档复述面**（字面正则/形态措辞） | `WORKFLOW.md`、`dispatch-protocol.md`、`state-machine.md`、`phase-cards/P4-implementation.md`、`execution-roles/{implementer,architect}.md` | **6** |
| **记录面** | `CHANGELOG.md`、`roadmap.md`、`tests/README.md`、`docs/design-notes/README.md` | **4** |
| 合计 | | **14** |

（另有 3 份评审报告 + 1 份设计说明共 4 个文件，属**记录产物**而非形态同步面 ⇒ commit 总数 18，形态同步面 14。）

**关键结论：漂移的危害不是"改起来麻烦"，是「必然改漏，且漏了没有机制能发现」。**

**实证**：本次**第一轮**改完后，终审仍查出 **5 处**未同步的文案（`check-scope-resolved.py` 注释 / `test_sc_15` docstring / `design-notes/README.md` / CHANGELOG / 设计说明）。**⇒ 形态同步面 14 处里漏了 5 处 = 漏改率 36%**（按 commit 总数 18 计为 28%）。

> **这就是本设计要消灭的东西**：不是"少改几处"，是**让"多处"这个前提不存在**。

### 1.4 已有机制为什么不够

| 已有机制 | 为什么不够 |
|---|---|
| `test_sc_14`（两脚本正则行为等价守护） | 只能守**已知的两处**；新增第三处消费方时它不会红 |
| `check-structure-consistency.py` S-1~S-6 | 守的是 **`rules/*.yaml` ↔ md** 的一致性，**不覆盖正文标记** |
| 文档里写"格式权威源 = `WORKFLOW.md`" | **是指针，不是判据单源**——它不阻止别处再写一份正则 |

**⇒ 缺的是：判据的「单一权威源」+ 消费方必须从它取值。**

### 1.5 ⚠️ 同一概念「行首」已有**三套互不相同**的实现（本设计最强的动机，实测）

| 消费方 | 覆盖形态 |
|---|---|
| `check-scope-resolved.py:40` | 空白 / 列表符 / 引用 / **粗体** |
| `agate_common.py:1449`（`DESIGN_GAP`，`allow_blockquote=True`） | 空白 / 引用 / 短横线（**不接受 `*`/`+` 列表符，不接受粗体**） |
| `agate_common.py:1449`（`DESIGN_GAP`，`False`） | 空白 / 短横线（**连引用都不接受**） |
| `agate_common.py:1463`（`CODE_MAP_*`） | 空白 / 短横线 |

四者的行首正则原文（**放代码块而非表格单元格**：正则含 `|`，而表格单元格里的转义写法
在 code span 内不被解码——两套渲染器下均不可靠；详见 `agate/adr.md` ADR-014 同款说明）：

```text
check-scope-resolved.py:40                    ^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?
agate_common.py:1449 (allow_blockquote=True)  ^\s*>?\s*-?\s*
agate_common.py:1449 (allow_blockquote=False) ^\s*-?\s*
agate_common.py:1463 (CODE_MAP_*)             ^\s*-?\s*
```

**⇒ 同一个「行首声明」概念，本仓有 3 套写法，覆盖面各不相同。**

**实测分叉（6 种形态逐一对比，`DESIGN_GAP` 用 `allow_blockquote=True`）**：

| 形态 | `DESIGN_GAP` 检出 | `SCOPE+` 检出 | |
|---|---|---|---|
| 裸 `[X]` | ✅ | ✅ | 一致 |
| `- [X]` | ✅ | ✅ | 一致 |
| `> [X]` | ✅ | ✅ | 一致 |
| `* [X]` | ❌ | ✅ | **分叉** |
| `+ [X]` | ❌ | ✅ | **分叉** |
| `**[X]**` | ❌ | ✅ | **分叉** |

**⇒ 6 种形态里 3 种分叉（50%）。**

**后果**：作者按 `WORKFLOW.md` 写粗体 `**[DESIGN_GAP: xxx]**`（合法且被判据接受），`DESIGN_GAP` 侧**静默计为 0** —— `count_design_gap` 返回 `(0, 0)`，配对校验认为**没有 DESIGN_GAP**，**不报错、不告警**。

**⇒ 与 PR #387 修的是同一类问题（判据形态与文档不一致 → 静默漏检），只是换了个标记，且至今无人踩到。**

**这就是"消灭漂移"的必要性证明**：不是"改起来麻烦"，是**同一概念已分叉成多份，且会各自演化**。
（`SCOPE+` 的分叉存在 **2 处**时被发现并修了；`DESIGN_GAP` 的 **3 套分叉至今无人发现**。）

> 本设计把「行首」抽成注册表的 `lead` 字段**一处定义**。`DESIGN_GAP` 的 blockquote 差异是**真实的口径差异**
> （P7 vs P4 转抄），应在注册表中**显式表达为字段**（如 `lead_variants:`），而不是散在两个字面量里。

---

## 2. 目标与非目标

### 2.1 目标

| # | 目标 | 判据 |
|---|---|---|
| G1 | **判据单源** | 一个标记的形态只在**一处**定义；消费方取值而非复制 |
| G2 | **漂移机械可检** | 任何消费方若自带正则副本 → 机械报错（不是靠人读） |
| G3 | **生成合法写法** | 提供 setter，**生成**符合判据的写法（这是用户原始诉求："自动写需要的格式化内容"） |
| G4 | **新增标记成本 = 1 行** | 加标记只改注册表；消费方零改动 |
| G5 | **零破坏** | 存量任务/协议文档**不需迁移**即可继续工作 |

### 2.2 非目标（明确划界，避免过度设计）

| # | 非目标 | 理由 |
|---|---|---|
| N1 | **不统一标记语法** | 存量 29 种、跨项目任务数据都在用；统一语法需全量迁移且破坏外部兼容。**本次只做"形态单源"** |
| N2 | **不消灭文档复述** | 协议文档**必须**对使用者讲清楚怎么写——那是面向人的说明书。强制单源会让文档变跳转、可读性下降。**分界：判据单源（机器），文档复述但指权威源** |
| N3 | **不把语义判断机械化** | 「声明 vs 提及」是判断类问题（见 §7），本设计不碰 |
| N4 | **不给所有 29 种标记补判据** | 只登记**形态**；是否为某标记新增判据是**独立决策**，不随本设计自动发生 |
| N5 | **不引入 daemon / 服务** | 与 agateon「零基础设施」一致 |

---

## 3. 设计

### 3.1 权威源：`agate/rules/markers.yaml`

放在 `rules/` 下，与 `phases.yaml` / `dispatch.yaml` / `roles.yaml` 同级——**已是本仓"数据面权威源"的既定位置**，且 `check-structure-consistency.py` 的 S-1~S-6 已在该目录建立"YAML ↔ md 一致性"的范式，扩展面清晰。

```yaml
schema_version: 1

# 形态基元：所有标记共用的「行首」前缀。
# 单源的关键——改这里，所有标记的形态一起变。
# 这是 PR #387 那次的教训固化：当时「行首」定义散在 2 个脚本 + 3 处文档。
lead: '^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?'

# 显式排除的形态（判为「提及」而非「声明」）。
# 保守边界的单源化：改这里即可，不必逐个消费方改。
exclude:
  backtick: '`'            # 行首反引号 = 引述（含真声明反例 TAG0004，代价已知）
  heading: '^#{1,6}\s'     # 标题 = 容器（正文才是状态）

markers:
  - name: SCOPE+
    purpose: 发现 P1 未覆盖的新隐含需求
    phases: [P2, P3, P4, P5, P6, P7]
    params: none
    paired_with: SCOPE_RESOLVED
    judged_by: check-scope-resolved.py

  - name: SCOPE_RESOLVED
    purpose: SCOPE+ 已纳入基线
    phases: [P1]
    params: optional_text
    resolves: SCOPE+
    # 与 SCOPE+ 的形态**不对称**：本次 hotfix 的实测结论
    # （载荷点是反引号；TAG0021 的 P1:231 首字节为 `）
    accept_backtick: true
    judged_by: check-scope-resolved.py

  - name: DESIGN_GAP
    purpose: 因 P2 设计歧义/缺口而自主做的决策
    phases: [P4]
    params: required_text
    paired_with: DESIGN_GAP_REVIEWED

  - name: NEED_CONFIRM
    purpose: 需人工确认
    phases: [P1, P2, P3, P4]
    params: none
    paired_with: NO_NEED_CONFIRM

  # …（其余按 §3.4 的登记范围逐条补）
```

**字段说明**：

| 字段 | 必填 | 语义 |
|---|---|---|
| `name` | ✅ | 标记名（不含方括号） |
| `purpose` | ✅ | 一句话用途（供 setter 的 `--help` 与文档生成） |
| `phases` | ✅ | 允许出现的阶段（`[]` = 不限） |
| `params` | ✅ | `none` / `optional_text` / `required_text` |
| `paired_with` / `resolves` | — | 成对/消解关系（4 组现有配对） |
| `accept_backtick` | — | 是否接受反引号包裹（默认继承 §3.1 的 `exclude.backtick`） |
| `judged_by` | — | 哪个脚本消费它（**仅登记，不驱动**；用于体检） |

### 3.2 消费方式：取值，不复制

新增 `agate/scripts/agate_markers.py`（公共库，被 import，不直接执行——与 `agate_common.py` 同款）：

```python
"""agate_markers.py — 正文标记形态单源（唯一权威 = rules/markers.yaml）

消费方**必须**用本模块取值，不得自带正则副本。
副本检测：test 层扫描消费脚本，发现 `\[[A-Z_]+\]` 字面正则即报错（G2）。
"""
def lead() -> str: ...              # 行首前缀
def pattern(name) -> re.Pattern: ... # 单个标记的正则（含 lead / exclude）
def find(text, name) -> list: ...    # 找声明（排除提及）
def is_declaration(line, name) -> bool: ...
def render(name, params=None) -> str: ...  # 生成合法写法（供 setter）
def names() -> list[str]: ...
```

**改造现有 2 个消费方**：

| 脚本 | 现状 | 改后 |
|---|---|---|
| `check-scope-resolved.py` | `_SCOPE_LEAD = r"..."` + `re.compile(...)` | `agate_markers.pattern("SCOPE+")` |
| `check-retrospective.py` | 自带 `SCOPE_PLUS_RE` 字面量 | 同上 |

**⇒ 两脚本从"各自持有正则"变为"同一个取值"，`test_sc_14` 从"守护两处一致"降级为"不需要"（结构上不可能不一致）。**

### 3.3 生成器：`agate-mark.py`

```bash
# 生成写法（stdout），供 agent 复制 / 通过 >> 追加
python3 agate/scripts/agate-mark.py SCOPE+          # 无参标记：**不接参数**（给了会 exit 1）
#   → [SCOPE+]
# 带参写法（参数是说明文字，写在标记**之后**，由人组织进产出）：
#   [SCOPE+] createEntry 与 publishFiles 的 expires 参数类型不一致

# 读参数形态自动处理：带参标记必须给参，无参标记给了参报错
python3 agate/scripts/agate-mark.py DESIGN_GAP "P2 未定义 X，按 Y 实现"
#   → [DESIGN_GAP: P2 未定义 X，按 Y 实现]

# 自描述
python3 agate/scripts/agate-mark.py --list          # 全部标记 + 用途 + 适用阶段
python3 agate/scripts/agate-mark.py --check FILE    # 校验文件内标记是否合法形态
```

**关键设计点**：

| 点 | 决策 | 理由 |
|---|---|---|
| **只生成，不写文件** | stdout 输出，不落盘 | 避免"工具替 agent 写产出"的越界；且当前环境 `/tmp` 是 per-call tmpfs，落盘反而增加约束 |
| **`--check` 复用同一判据** | 与消费方同源 | 否则 setter 与 checker 又成两处 |
| **带参/无参由注册表驱动** | 不是硬编码 | G4：新增标记零改动 |

### 3.4 首批登记范围

**建议只登记「有成对关系或有判据」的标记**（约 8 个），其余 21 种**暂不登记**：

| 登记（8） | 理由 |
|---|---|
| `SCOPE+` / `SCOPE_RESOLVED` | 已有判据；PR #387 的直接对象 |
| `DESIGN_GAP` / `DESIGN_GAP_REVIEWED` | 有成对关系；`check-gate.py` 等在判 |
| `NEED_CONFIRM` / `NO_NEED_CONFIRM` | 成对；文档复述最重（19 处） |
| `PROD_TOUCHED` / `PROD_NOT_TOUCHED` | 成对；安全相关 |

**暂不登记**（21 种）：`BLOCKER` / `SUGGEST` / `CAPABILITY_GAP` / `COL_*` / `CODE_MAP_*` / `TASK_DIR` / `STATE_FILE` 等——
它们**没有判据、也没有配对**，登记了也只是"记个名字"，**不产生 G1~G4 的任何收益**。

> **⇒ 登记范围本身是"渐进"的**：只有当你真要给某标记加判据、或它有成对关系时，才登记它。
> **这避免了"为了通用而先把 29 种全登记一遍"的形式主义**（那正是 `design-claim-evidence-binding.md` v2 的失败模式）。

### 3.5 漂移的机械守护（G2）

新增 `agate/tests/unit/test_marker_single_source.py`：

| 用例 | 判据 |
|---|---|
| `mk_1` 消费方不得自带正则副本 | 扫描已登记标记的消费脚本，发现 `r"\[SCOPE\+\]"` 类**字面正则**即失败（除非 `# noqa: marker-source` 显式豁免 + 理由） |
| `mk_2` 注册表驱动等价 | 对每个已登记标记，`pattern(name)` 与"手写该标记形态"行为一致（防注册表本身写错） |
| `mk_3` 生成↔判据闭环 | 对每个标记：`render(name)` 的产物**必须**被 `pattern(name)` 命中（**setter 与 checker 不可能分叉**） |
| `mk_4` 非法形态被拒 | 带参标记缺参 / 无参标记给参 → `render` 报错 |
| `mk_5` 成对关系完整 | `paired_with` / `resolves` 指向的标记**必须存在于注册表**（防悬空指针） |
| `mk_6a` 标记名互斥 | A 的判据不得命中 B 的合法写法（防前缀吞并；HIGH-1 的守护） |
| `mk_6b` 与既有消费方等价 | `pattern("DESIGN_GAP")` 与 `agate_common.count_design_gap` 在**真实语料**上计数相等 |

**负向控制**：在消费方写回一个字面正则 → `mk_1` 转红；把 `render` 改成生成非行首形态 → `mk_3` 转红。

**⇒ `mk_3` 覆盖「生成器产出判据不认」这一方向（过严），但不覆盖「判据过宽」**——
后者（判据命中不属于它的东西）由 `mk_6a`/`mk_6b` 承担。**两个方向都需要，缺一不可**
（HIGH-1 正是「判据过宽」且当时无守护）。

---

## 4. 与既有机制的关系

| 既有机制 | 关系 |
|---|---|
| `rules/phases.yaml` 等 | **同层同级**；新增 `markers.yaml` 是第 4 个数据面权威源 |
| `check-structure-consistency.py` S-1~S-6 | **不冲突**：S-1~S-6 守 `rules/*.yaml ↔ md`；本设计的 `mk_1` 守"消费方不复制判据"。**可选扩展 S-7**：`markers.yaml` 声明的标记在 `WORKFLOW.md` 有对应节 |
| `check-yaml-schema.py` S-5 | **需扩展**：新增 `rules/schema/markers.schema.json`，纳入 S-5 校验面 |
| `test_sc_14`（两脚本等价） | **降级保留**：改造后两者天然同源，该用例退化为"注册表正确性"的间接验证 |
| `check-protocol-consistency.py` CHECK 9 锚点表 | **需登记**新脚本（`agate-mark.py` / `agate_markers.py`），走既有登记面流程 |

---

## 5. 实施计划（分批，可独立验收）

| 批 | 内容 | 验收锚 | 风险 |
|---|---|---|---|
| **A** | `rules/markers.yaml`（登记 8 个）+ `agate_markers.py` | 注册表过 schema；`pattern()` 对 8 个标记可用 | 低 |
| **B** | 改造 2 个消费方（`check-scope-resolved.py` / `check-retrospective.py`）取值 | **存量对账 41 任务判定不变**（PR #387 基线：通过 9 / 跳过 32 / 失败 0） | 中（碰判定面） |
| **C** | `agate-mark.py`（`--list` / 生成 / `--check`） | `mk_3` 闭环绿 | 低 |
| **D** | 5 条守护测试 + 负向控制 | 负向控制实测转红 | 低 |
| **E** | 文档传播：`WORKFLOW.md` 加权威源指针；卡片/角色文件改用 setter | `check-structure-consistency` 0 ERROR | 低 |

**A→B 是关键路径**：B 完成即可验证"单源不改变现有判定"（**这一条是硬门禁**）。

---

## 6. 验收锚（可机械校验）

| # | 锚 | 判据 |
|---|---|---|
| V1 | **判定不变** | 批次 B 后，存量 41 任务判定与 PR #387 基线**逐任务一致**（通过 9 / 跳过 32 / 失败 0） |
| V2 | **判据单源** | `mk_1` 绿：已登记标记的消费脚本无字面正则副本 |
| V3 | **生成↔判据闭环** | `mk_3` 绿：`render(name)` 产物必被 `pattern(name)` 命中 |
| V4 | **新增标记 1 行** | 实测：注册表加一个标记 → `--list`/生成/`--check` 三处**零代码改动**即可用 |
| V5 | **零破坏** | 存量任务目录、协议文档**不迁移**即可继续工作 |
| V6 | **schema 覆盖** | `markers.schema.json` 纳入 `check-yaml-schema.py` S-5 |
| V7 | **登记面** | 新脚本登记进 CHECK 9 锚点表 + `scripts/README.md` |

---

## 7. 本设计**不解决**什么（必须说清楚，避免过度承诺）

### 7.1 语义判断（声明 vs 提及）仍不可机械化

**PR #387 的真实教训**：`[SCOPE+]` 的困难**不在"几处正则"，在「声明 vs 提及」是语义判断**。

我实测过一版启发式（否定词前置 + 反引号包裹），**全仓命中 22 个任务、绝大多数是散文提及** ⇒ 判断类语义机械化会退化（与 `design-claim-evidence-binding.md` v1/v2 同一失败模式）。

**⇒ 本设计让「形态」不漂移，不能让「语义」变可判定。** 后者仍需保守边界 + **如实登记代价**（PR #387 的做法：标题 +4 转红 / 反引号 +5 转红 / 行中出现 +24 转红，且 `TAG0004` 真声明仍未被覆盖）。

### 7.2 存量真声明漏检仍在

`TAG0004` 的行首反引号真声明、`TAG0008` 的容器标题——本设计**不改变**这些判定（单源 ≠ 放宽）。

### 7.3 文档仍复述形态

**这是刻意的**（N2）：`WORKFLOW.md` 必须讲清楚怎么写。本设计只保证"**判据**单源"，不追求"**文本**单源"。

---

## 8. 待你拍板的 3 个决策

| # | 决策 | 选项 | 我的建议 |
|---|---|---|---|
| **D1** | 首批登记范围 | (a) 8 个（有成对/有判据）／(b) 全 29 种 | **(a)**——(b) 是无收益的形式主义 |
| **D2** | setter 是否落盘 | (a) 只输出 stdout ／(b) 支持 `--append FILE` | **(a)**——(b) 会让工具替 agent 写产出，越界 |
| **D3** | 是否加 S-7（`markers.yaml` ↔ `WORKFLOW.md` 一致性） | (a) 加 ／(b) 不加，只留指针 | **(b)**——文档复述是允许的（N2），强制节对齐会限制文档写法 |

---

## 9. 风险

| 风险 | 缓解 |
|---|---|
| 批次 B 改变既有判定 | V1 硬门禁：逐任务对账，与 PR #387 基线一致才算过 |
| 注册表本身写错 | `mk_2`（注册表↔手写形态等价） |
| `accept_backtick` 这类"每标记特例"长成新漂移 | 特例必须**在注册表内**表达（字段），不得在消费方写 `if name == "SCOPE_RESOLVED"` |
| 登记范围一次铺太大 | D1 建议 (a) 8 个；其余按需登记 |
| 与 S-1~S-6 重复/冲突 | 职责不同（见 §4）；S-5 schema 纳入是加法 |

---

## 10. 落地记录（2026-10-02）

**决策**：D1 = 8 个标记（有成对/有判据）；D2 = setter 只输出 stdout（不落盘）；D3 = 不加 S-7。

### 10.1 交付物

| 文件 | 内容 |
|---|---|
| `agate/rules/markers.yaml` | 权威源：`lead`（行首基元）+ `lead_variants`（口径变体）+ `exclude`（保守边界）+ 8 个标记 |
| `agate/rules/schema/markers.schema.json` | draft-07 子集 schema |
| `agate/scripts/agate_markers.py` | 取值库：`pattern/find/is_declaration/render/describe` + `--list/--check/<NAME>` CLI |
| `agate/scripts/agate-mark.py` | 生成器：`--list` / `<NAME> [参数]` / `--check FILE` / `--json` |
| `agate/tests/unit/test_marker_single_source.py` | mk_1~mk_6 守护（32 用例） |
| 改造 | `check-scope-resolved.py` / `check-retrospective.py` 改为取值；`check-yaml-schema.py` 纳入 markers；`check-protocol-consistency.py` 锚点登记；`scripts/README.md` / `tests/README.md` / `WORKFLOW.md` 文档传播 |

### 10.2 批次 B 硬门禁结果（**V1 通过**）

改造两个消费方后，**存量 41 任务判定与 PR #387 基线逐任务一致**：

```
改造前（PR #387 基线）：通过 9 / 跳过 32 / 失败 0
改造后（单源取值）    ：通过 9 / 跳过 32 / 失败 0   ✅ 完全一致
```

另做**逐文件级**对账：SCOPE+ 与 SCOPE_RESOLVED 在全仓 `tasks/*/*.md` 上**差异文件数 = 0**。

### 10.3 ⚠️ 落地过程中发现的两处真实语义差异（设计时未预见，据实登记）

**(1) 两个标记的参数语义本来就不一样** —— 初版 `_body()` 用了统一规则，导致批次 B **门禁红了**：

```
统一规则（初版）  ：通过 11 / 跳过 30 / 失败 0   ❌ 与基线不符（+2 任务）
修正后            ：通过  9 / 跳过 32 / 失败 0   ✅
```

- `params: none`（如 `SCOPE+`）→ 本体 `\[NAME\]`，**`]` 必须紧跟**。故 `[SCOPE+ 观察]` / `[SCOPE+: x]` **不**命中。
- `params: optional_text / required_text`（如 `SCOPE_RESOLVED`）→ 本体 `\[NAME($|[^a-z])`，**不要求紧跟 `]`**，因而**允许跨行参数**。
  **判据**：标记**起始行不含 `]`**；此口径下全仓实测 **3 处**（`TAG0027/P7:48`、`TAG0031/P1:371`、`TAG0031/P7:60`）。
  > ⚠️ **引用时必须附判据**：换更宽口径（「所有 `[SCOPE_RESOLVED` 出现」等）会得到 5 / 11 / 98 等不同数字——
  > 同一事实"换个口径就换个数字"，正是本设计 §1.2 要治的病。

**⇒ 教训**：把两个"看起来同类"的标记套用统一规则是错的——**单源的前提是先如实刻画差异**，不是先统一。

**(2) ⚠️ 注册表初版与 `agate_common` 的 `DESIGN_GAP` 判据**不等价**（独立评审查出，已修）**

初版有两个缺陷，**方向相反**——不是"改变了既有行为"，而是**判据更宽**：

| 缺陷 | 现象 | 后果 |
|---|---|---|
| **前缀吞并** | `pattern("DESIGN_GAP")` 命中 `[DESIGN_GAP_REVIEWED: x]`（`_` 满足 `[^a-z]`） | 逐 P7 文件对账 **59 vs 121（2.05×）**；61 行 REVIEWED 被误计为 DESIGN_GAP |
| **冒号可选** | `required_text` 分支把 `:` 组写成可选，而 `agate_common` 用**字面冒号** `\[DESIGN_GAP:` | `[DESIGN_GAP]`（无参）被误计，旧实现计 0 |

**修复**：① `required_text` 分支冒号**必填**；② 本体后加 `(?!\w)` 名称边界。

**⚠️ 载荷点实测（我最初把次序写反了）**：分约束变异 + 全仓计数（基准 = `agate_common` 116）：

| 变体 | 全仓 `pattern("DESIGN_GAP")` 计数 | 说明 |
|---|---|---|
| 两者都有（现状） | **116** ✅ | 等价 |
| 只去 `(?!\w)` | **116** | 仍等价 ⇒ **边界在本语料上非载荷** |
| 只去「冒号必填」 | **124** ❌ | 偏多 8 ⇒ **冒号必填才是载荷点** |

⇒ **主因是「冒号必填」**（`agate_common` 用字面 `\[DESIGN_GAP:`）；
`(?!\w)` 是**防御性冗余**——它防的是"未来新增 `DESIGN_GAP_XXX` 型前缀标记"这一类**尚未发生**的情况
（`DESIGN_GAP_REVIEWED` 已被冒号约束挡住）。**两者都保留**，但不得把冗余说成主因。

**验证**：逐形态 8/8 等价；全仓语料 **116 vs 116、差异文件数 0**。
**守护**：新增 `mk_6a`（已登记标记两两互斥）+ `mk_6b`（与 `agate_common` 在真实语料上等价），
两者在**忠实的 HIGH-1 复现**下实测转红。

> **为什么初版没被发现**：`pattern("DESIGN_GAP")` 当时**零消费方**（`check-gate.py` 仍走 `agate_common`），
> 且**无等价断言** ⇒ 注册表被 `judged_by` / S-5 schema / CHECK9 锚点**三处正式声明**为权威源，
> 却与实际在判的实现不等价。**下一个接线的人会立刻踩中，而测试抓不到**——这是本设计最该记取的教训：
> **声明单源 ≠ 已经单源；权威源必须与既有实现逐条对账，并加等价守护。**

### 10.4 测试与验证

| 项 | 结果 |
|---|---|
| mk_1~mk_6 守护 | **32 passed** |
| 负向控制（**6 组**，均实测转红） | ① 消费方写回字面正则 → `mk_1`；② `render` 生成非行首 → `mk_3`/`mk_3b`；③ 配对指向未登记标记 → `mk_5`/`mk_5b`；④ 注册表**退回 HIGH-1 状态** → `mk_6a`/`mk_6b`（双向已证）；⑤ 只去 `(?!\\w)` → 全绿（证明其非载荷）；⑥ 只去冒号必填 → `mk_6b` 报 124≠116 |
| unit 分片 | **2309 passed** / 1 failed（既有 `opencode` 不在 PATH，非本批）+ 2 skipped |
| regression + integration | **195 passed** |
| consistency | 0 ERROR / 386 WARNING（与基线一致） |
| structure-consistency（S-1~S-6） | 全 OK（含新增 SCHEMA-markers） |
| CHECK9-coverage | 新脚本已进 CHECK9 锚点表（**注意**：`uncovered_gate_scripts()` 只 glob `check-*.py`，两个新脚本**不在其扫描面**，它返回空**不构成**覆盖证据——真实覆盖由锚点表成立） |

**修复过程中发现并修掉的一处连带影响**：`check-yaml-schema.py` 的 `_RULES` 新增 markers 后，
`_rules_test_utils.make_fake_root()` 构造的**最小假协议树**缺该文件 → 2 个既有 schema 测试转红。
**已修**（假树补 `DEFAULT_MARKERS_YAML` + `default_markers_schema()`）——**这是"假树须镜像真协议结构"这条隐含约定的显式化**，不是改测试迁就实现。

### 10.5 新增标记的成本（G4 兑现验证，实测）

在 `markers.yaml` **只加 1 条**（无任何代码改动）：

```yaml
  - name: TEST_NEW_MARKER
    purpose: G4 验证用的临时标记
    phases: [P4]
    params: required_text
    ...
```

实测结果（临时加 → 验证 → 还原）：

| 能力 | 结果 |
|---|---|
| 生成 | `agate-mark.py TEST_NEW_MARKER "参数内容"` → `[TEST_NEW_MARKER: 参数内容]` ✅ |
| 列出 | `--list` 自动出现该标记（无需改 CLI） ✅ |
| 守护 | `mk_*` 自动覆盖它；且 **`mk_5b` 当场抓出我故意写的不对称配对** ✅ |

**⇒ 从"改 32 处"（`DESIGN_GAP` 现状）降到"加 1 行"。** G4 达成。
