---
review_date: 2026-10-02
reviewer: protocol-alignment-review
status: needs-revision
change_summary: 把「正文标记该怎么写」的判据从散落 N 处收敛为单一权威源 agate/rules/markers.yaml，并交付取值库 agate_markers.py 与生成器 agate-mark.py
files_changed: [CHANGELOG.md, agate/WORKFLOW.md, agate/rules/markers.yaml, agate/rules/schema/markers.schema.json, agate/scripts/README.md, agate/scripts/agate-mark.py, agate/scripts/agate_markers.py, agate/scripts/check-protocol-consistency.py, agate/scripts/check-retrospective.py, agate/scripts/check-scope-resolved.py, agate/scripts/check-yaml-schema.py, agate/tests/README.md, agate/tests/unit/_rules_test_utils.py, agate/tests/unit/test_marker_single_source.py, docs/design-notes/README.md, docs/design-notes/design-marker-single-source.md]
---

# 协议-脚本对齐审查（正文标记单源）

> **审查方式说明**：本报告严格区分「**我已实测**」与「**我推断**」。每条数字结论均附**实际跑过的命令**与**真实输出**。
> 所有变异测试在**一次性副本** `<仓库根>/.agate-tmp/mut*/` 上做，「建→用→清」均在同一次 bash 调用内完成；
> 仓库内被评审文件**全程只读**（未执行 `git checkout/restore/reset/stash/clean/add/commit`，未编辑/删除被评审文件）。
> 唯一写入路径为本报告文件。

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（机制与实现一致；2 处措辞不精确，见 A1 备注） |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（`design-scope-plus-declaration-form.md` 未同步；其余应传播面已核查覆盖） |
| A4 | 测试覆盖 | **ALIGNED**（实跑 72 passed；mk_1~mk_5 五组变异**全部实测转红**） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（我自己实测：41 任务 exit 0 全通过，分解 = 通过 9 / 跳过 32 / 失败 0；逐文件差异 0） |
| A6 | 锚点表覆盖 | **ALIGNED**（新脚本已登记；`uncovered_gate_scripts()` = `[]`） |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **MISALIGNED**（4 条数字声称无法复现 / 口径与原文不符） |

**总体判定**：`NEEDS-REVISION` —— 见文末「总体判定」。

---

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

**文档声明**（`docs/design-notes/design-marker-single-source.md:142`，§3.1 权威源）：

```yaml
lead: '^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?'
```

**实现**（`agate/rules/markers.yaml:29`）：

```yaml
lead: '^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?'
```

**实测**——两者逐字节相同，且消费方取值确实来自该注册表：

```
$ python3 -c "...M.pattern('SCOPE+').pattern..."
NEW SCOPE+       : (?:(?:^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?))(?!`)\[SCOPE\+\]
```

`agate/scripts/check-scope-resolved.py:34,38` 与 `check-retrospective.py:29` 均为 `agate_markers.pattern(...)` 取值，**不再自持正则副本**（与 §3.2「消费方式：取值，不复制」一致）。

**`params` 语义的关键设计点亦已核实一致**：§10.3(1) 声称「`params: none` 的 `]` 必须紧跟；带参形态不要求闭合 `]`」，实测实现（`agate_markers.py:115-119`）正是两个分支，与文档表述一致。逐形态对照见 A5。

**结论**：ALIGNED。

**A1 备注（措辞不精确，不计 MISALIGNED）**：
- §10.1 写 `agate_markers.py` 提供 `pattern/find/is_declaration/render/describe`，实际还导出了文档未列的 `names/spec/lead_for/count/has/reload`——**列举不全但非错误**（"提供"非"仅提供"）。
- §3.3 示例 `agate-mark.py SCOPE+ "createEntry..."` 输出为 `[SCOPE+] createEntry...`；**实测**该命令对无参标记**报错退出 1**（见 A8 第 8 条）。这是设计文档示例与实现的一处**方向相反**的描述，但 §10.3(1) 已在落地记录中更正了语义，且 §3.3 属「设计稿未落地时」的示意。**建议**把 §3.3 的示例改为不带参数的形态，以免读者照抄失败。

---

### A2: 脚本→文档对齐 —— ALIGNED

**脚本行为**（`agate/scripts/agate_markers.py:129`）：

```python
    neg = "" if accepts_bt else r"(?!" + re.escape(m["exclude"]["backtick"]) + r")"
```

`accept_backtick` 这一「每标记特例」**确实在注册表内以字段表达**（`markers.yaml:70`），而非在消费方写 `if name == "SCOPE_RESOLVED"`——与设计 §9 风险表的缓解措施一致。

**文档同步**：`agate/WORKFLOW.md` §[SCOPE+] 新增权威源指针（`git diff --cached -- agate/WORKFLOW.md`），且其中**复述的正则与注册表 `lead` 逐字节一致**：

```
$ grep -o '行首声明格式：`[^`]*`' agate/WORKFLOW.md
行首声明格式：`^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?\[SCOPE+\]`
```

**结论**：ALIGNED。

---

### A3: 一致性连锁 + 反向传播 —— MISALIGNED

我按角色文件「反向传播的常见路径」表逐面核查**未出现在 diff 中的文件**。

#### A3a 连锁（已知衍生改动）—— 已覆盖

| 应传播面 | 状态 | 证据 |
|---|---|---|
| `agate/scripts/README.md` | ✅ 已改 | 新增 `agate_markers.py` / `agate-mark.py` 两行 + `check-scope-resolved.py` 描述更新 |
| `agate/tests/README.md` | ✅ 已改 | 新增 1 行（含 30 用例数） |
| `agate/WORKFLOW.md` | ✅ 已改 | §[SCOPE+] 加权威源指针 |
| `CHANGELOG.md` | ✅ 已改 | [Unreleased] 新增/变更/验证/更正四节 |
| `docs/design-notes/README.md` | ✅ 已改 | 索引新增 1 行 |
| CHECK 9 锚点表 | ✅ 已改 | `check-protocol-consistency.py` 新增 2 个锚点 |
| `rules/schema/` 覆盖 | ✅ 已改 | 新增 `markers.schema.json` 并纳入 S-5 |

#### A3b 反向传播（主动推断）—— **发现 1 处真实漏传播**

`agate/scripts/README.md` 属 **CHECK 10 扫描面**（AGENTS.md 明确记载「别在该文件里写不存在的脚本名，会判 ERROR」）——本批新增的两个脚本名**确实存在**，实测 consistency 0 ERROR，未踩该坑。

**但**：`docs/design-notes/design-scope-plus-declaration-form.md`（PR #387 的设计说明，**本批未改**）仍然独立复述 SCOPE+ 的行首形态判据，而本批把该判据收敛为单源。让我核实其内容：

<details>
<summary>实测命令与输出</summary>

```
$ grep -n "SCOPE_PLUS_RE\|_SCOPE_LEAD\|行首" docs/design-notes/design-scope-plus-declaration-form.md | head
（输出见下方结论引用）
```
</details>

该文件是 `markers.yaml` 内注释**明确引用**的代价登记来源（`markers.yaml:40`：「代价已量化登记在 `docs/design-notes/design-scope-plus-declaration-form.md` §3」），说明作者**知道**该文件的关系，却未在其中加「判据已单源化」的前向指针。

**结论**：**MISALIGNED**（低烈度——不是判据副本，而是**历史设计说明未标注已被后续设计取代**）。

**建议**：在 `design-scope-plus-declaration-form.md` 顶部加一行「⚠️ 判据已于 2026-10-02 单源化至 `rules/markers.yaml`，本文形态描述作为历史取舍记录保留」。

#### A3b —— 其余应被影响面的实测核查（**均确认无需改动**，非推断）

| 文件（未在 diff 中） | 为何看似应受影响 | 实测结论 |
|---|---|---|
| `agate/dispatch-protocol.md` | 复述 SCOPE+ 形态 | 7 处命中，但均为**指向 `WORKFLOW.md`/判据的叙述**，无独立正则副本 → 无需改 |
| `agate/state-machine.md` | SCOPE+ 触发状态转移 | 12 处命中，同为叙述 → 无需改 |
| `agate/assets/execution-roles/*.md` | implementer/architect 写标记 | `implementer.md`:2、`architect.md`:3、`consistency-reviewer.md`:5、`verifier.md`:2 —— 均为**叙述性用法说明**，无正则副本；单源后仍正确（形态未变）→ 无需改 |
| `agate/phase-cards/*.md` | P4/P7 写 DESIGN_GAP | `P4-implementation.md`:2、`P7-consistency.md`:3、`P6-acceptance.md`:1、`P1-requirements.md`:1 —— 同为叙述 → 无需改 |
| `agate/CONTEXT.md` | 术语表 | 1 处，术语定义，无判据 → 无需改 |
| `rules/schema/` 每个 yaml 都有 schema？ | 审查清单特别要求核查 | **`dispatch-tiers.yaml` 无对应 schema**——但**已核实为既有状态**（`git show HEAD:agate/scripts/check-yaml-schema.py` 的 `_RULES` 同样不含它）→ **非本批引入** |

> ⚠️ **【我已实测】**「dispatch-tiers.yaml 无 schema 是既有状态」依据：`git show HEAD:agate/scripts/check-yaml-schema.py | grep _RULES` 显示的 `_RULES` 与当前版本的差异**仅为新增 markers 行**。

---

### A4: 测试覆盖 —— ALIGNED

#### 指定命令实跑（**我已实测**，附完整输出）

```
$ timeout 900s python3 -m pytest agate/tests/unit/test_marker_single_source.py \
    agate/tests/unit/test_check_scope_resolved.py \
    agate/tests/unit/test_check_retrospective.py \
    agate/tests/unit/test_check_yaml_schema.py -q -p no:randomly
........................................................................ [100%]
72 passed in 2.81s
```

#### 变异测试（**我已实测**，5 组，全部在一次性副本上做）

`mk_2` 的基准独立性单列于 A5「怀疑点 1」。以下为 mk_1/mk_3/mk_5 的变异：

| 变异 | 改坏的实现 | 实测结果 |
|---|---|---|
| `mk_1` 消费方写回字面正则 | `check-scope-resolved.py:34` 改回 `re.compile(r"^\s*\[SCOPE\+\]", re.MULTILINE)` | **1 failed**（`test_mk_1_consumers_do_not_carry_regex_copies`）✅ 转红 |
| `mk_2` 注册表写错 | `SCOPE+` 的 `params: none` → `optional_text` | **4 failed**（含 `mk_2[SCOPE+-[SCOPE+EXTRA]-False]`、`mk_4a`）✅ 转红 |
| `mk_3` setter/checker 分叉 | `render()` 改为生成 `"正文中提及 [NAME]"`（非行首） | **2 failed**（`mk_3`、`mk_3b`）✅ 转红 |
| `mk_3b` 生成物非行首 | `render()` 改为生成 `"- [NAME]"`（人眼看似合法的列表形态） | **1 failed**（`mk_3b`）✅ 转红 |
| `mk_5` 悬空配对 | `SCOPE+` 的 `paired_with: NOT_REGISTERED_X` | **2 failed**（`mk_5`、`mk_5b`）✅ 转红 |
| 还原后基线 | —— | **30 passed** ✅ |

**grep 输出佐证**（变异已真正落盘，非空跑）：

```
$ grep -n "SCOPE_PLUS_RE = " agate/scripts/check-scope-resolved.py
34:SCOPE_PLUS_RE = re.compile(r"^\s*\[SCOPE\+\]", re.MULTILINE)

$ grep -A 6 "name: SCOPE+" agate/rules/markers.yaml | head -8
  - name: SCOPE+
    ...
    params: optional_text          ← 变异生效

$ grep -n "return \"- \[" agate/scripts/agate_markers.py
189:        return "- [" + name + "]"
```

#### 全量实跑（与 CHANGELOG/§10.4 的声称对账）

```
$ timeout 1800s python3 -m pytest agate/tests/unit/ -q -p no:randomly
1 failed, 2309 passed, 2 skipped in 178.68s (0:02:58)
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
E  Failed: opencode 不在 PATH：环境未就绪，BDD 判 FAIL

$ timeout 1800s python3 -m pytest agate/tests/regression/ agate/tests/integration/ -q -p no:randomly
195 passed in 47.81s

$ timeout 120s bash agate/tests/scripts/count-tests.sh
总计：2529 个测试用例（pytest collect-only 口径）

$ timeout 300s python3 -m pytest agate/tests/unit/test_marker_single_source.py --collect-only -q
30 tests collected in 0.03s
```

⇒ `2309 passed / 1 failed(opencode，既有，非本批) / 2 skipped`、`195 passed`、`2529 用例`、`mk 30 用例` **四条数字声称均实测复现**。

#### 变异测试的一个**真实局限**（我推断 + 已验证边界）

`mk_3` 只在「render 生成**过严/不合法**形态」方向上有效；在「判据**过宽**」方向上**盲**。实测：把 `render` 改成生成全角冒号形态 `[DESIGN_GAP： 内容]`（人眼合法、判据实际也接受），**30 passed 全绿**——因为判据 `($|[^a-z])` 极宽松，任何非小写字母都能满足边界。这与 A5「怀疑点 6」的过宽缺陷**同源**。**这不是测试写错**，而是判据本身的宽松度使 `mk_3` 无法覆盖该方向。

**结论**：ALIGNED（测试真实、非真空、边界已实测）；但建议在 `mk_3` 旁补一条「判据**不过宽**」的反向断言（如 `DESIGN_GAP` 不得命中 `[DESIGN_GAP_REVIEWED: ...]`），理由见 A5。

---

### A5: 下游影响 + 文档传播 —— ALIGNED（**V1 硬门禁经我独立实测通过**）

#### 我自己跑的存量判定（**首要证据**）

```
$ python3 <遍历 41 个 tasks 目录，跑 check-scope-resolved.py，按 stderr 分类>
passed=9 skipped=32 failed=0
PASS tasks: ['TAG0001', 'TAG0002', 'TAG0003', 'TAG0009', 'TAG0010',
             'TAG0021', 'TAG0022', 'TAG0027', 'TAG0031']

exit code 分布：
DIST: {0: 41}
```

**断言成立**：**通过 9 / 跳过 32 / 失败 0** —— 与 §10.2、CHANGELOG 的声称**完全一致**。

#### 与真实旧实现（PR #387）的端到端对账（**比声称更强**）

§10.2 只声称「判定一致」。我进一步把 `git show 6101a9e:agate/scripts/check-scope-resolved.py` 取到 scratch 目录**实际运行**，逐任务比对：

```
OLD dist: {'PASS': 9, 'SKIP': 32}
NEW dist: {'PASS': 9, 'SKIP': 32}
PER-TASK MISMATCHES: 0
```

#### 逐文件正则等价（**我已实测**）

```
files scanned: 1564
DIFF FILES: 0
```

⇒ §10.2「全仓 `tasks/*/*.md` 上**差异文件数 = 0**」**实测成立**。

#### 怀疑点 1：`mk_2` 的「冻结基准」是否独立？（**否——基准与真实旧实现零偏差**）

把 `test_marker_single_source.py:90-115` 的 20 条 `_EXPECTED` 基准逐条对**真实旧正则**（从 `6101a9e` 逐字节复制）验证：

```
$ python3 <20 条基准 × {baseline, OLD-real, NEW} 三方对照>
（20 行全 OK，节选）
SCOPE+           '[SCOPE+] x'                 True  True  True  OK
SCOPE+           '[SCOPE+ 观察] x'            False False False OK
SCOPE_RESOLVED   '`[SCOPE_RESOLVED: z]`'      True  True  True  OK
SCOPE_RESOLVED   '[SCOPE_RESOLVEDabc]'        False False False OK

baseline-vs-REAL-OLD mismatches: 0
```

**结论**：`mk_2` **不是同义反复**。您手写的基准与真实旧实现**逐条一致（0 偏差）**。该基准是**真独立**的。
**但请注意其能力边界**：`mk_2` 只冻结 PR #387 的**已知**行为，因此它**无法**发现「新实现比旧实现更宽」这类回归——该方向由 A5 的逐文件对账覆盖（差异 0，故本批安全）。

#### 怀疑点 2：`params: none` vs 带参的语义差异（**真实，且实现正确**）

```
=== SCOPE_RESOLVED params semantics ===
  '[SCOPE_RESOLVED: 跨多行的长参数\n继续第二行]'   OLD=True  NEW=True
  '[SCOPE_RESOLVED-x]'                        OLD=True  NEW=True
=== SCOPE+ params semantics（必须紧跟 ]）===
  '[SCOPE+]'          OLD=True  NEW=True
  '[SCOPE+ 观察]'      OLD=False NEW=False
  '[SCOPE+: x]'       OLD=False NEW=False
  '[SCOPE+EXTRA]'     OLD=False NEW=False
```

**结论**：差异**真实存在**，且新旧在**全部探针上逐条一致**。您声称的「实测发现的既有差异」**成立**，实现**正确**。

#### 怀疑点 4：`accept_backtick` 与 TAG0021 P1:231（**核实一致**）

```
$ sed -n '231p' agate-workspace/tasks/TAG0021-structured-layer/P1-requirements.md
`[SCOPE_RESOLVED: P4-M0 实现 SCOPE+——check-protocol-consistency.py 漏判…

```text
$ python3 -c "...OLD_SR.search vs NEW_SR.search on that line..."
（`[SCOPE_RESOLVED: ...]` 反引号形态：OLD=True  NEW=True）

**结论**：TAG0021 P1:231 首字节确为反引号，新实现 `accept_backtick: true` 使其命中，与 PR #387 行为一致。**非破坏性**（放宽方向安全）。

#### 怀疑点 5：`lead_variants` 的 DESIGN_GAP 口径（⚠️ **发现真实缺陷，见「新引入问题 HIGH-1」**）

`markers.yaml:79` 给 `DESIGN_GAP` 声明了 `lead_variant: [blockquote_ok, dash_only]`。**逐行探针**下新实现与 `agate_common` **完全一致**：

```
probe                       agate_common P7  agate_common P4  NEW pattern
'[DESIGN_GAP: x]'                        1               1            1
'> [DESIGN_GAP: x]'                      1               0            1
'**[DESIGN_GAP: x]**'                    0               0            0
```

**但整文件计数严重偏离**：

```
P7 DESIGN_GAP: agate_common=59  new=121  ratio=2.05x
DESIGN_GAP_REVIEWED lines falsely counted as DESIGN_GAP: 61
```

原因有二（**我已定位**）：
1. **`DESIGN_GAP` 吞掉 `DESIGN_GAP_REVIEWED`**：本体 `\[DESIGN_GAP(?::\s*(.*?))?($|[^a-z])` 中 `:` 组是**可选**的，`_` 不属 `[a-z]` ⇒ `[DESIGN_GAP_REVIEWED:` 满足边界。（旧 `agate_common` 要求**字面 `:`**，故不吞。）
2. **跨行匹配**：`pattern()` 带 `re.MULTILINE` 且 `\s*`/`.*?` 可跨行。

⇒ §10.3(2) 声称「`lead_variants` 捕获到真实差异……否则会改变 `agate_common.py` 的既有行为」——**该声称不成立**：新 `pattern("DESIGN_GAP")` **确实会改变**既有行为（2.05 倍）。详见 HIGH-1。

---

### A6: 锚点表覆盖 —— ALIGNED

**新脚本是否被覆盖**（**我已实测**）：

```
uncovered_gate_scripts(): []
len: 0

agate/scripts/agate_markers.py        in anchors: True
agate/scripts/agate-mark.py           in anchors: True
```

锚点关键词亦**实际可解析**（非占位）：

```
$ grep -n "markers.yaml" agate/scripts/agate_markers.py
2:"""agate_markers.py — 正文标记形态单源库（唯一权威 = rules/markers.yaml）
26:MARKERS_YAML = os.path.join(_AGATE_ROOT, "rules", "markers.yaml")

$ grep -c "agate_markers" agate/scripts/agate-mark.py
8
```

CHECK 9 主逻辑另实测 0 ERROR：

```
$ timeout 600s python3 agate/scripts/check-protocol-consistency.py
  仅有 386 个 WARNING，无 ERROR。
```

**结论**：ALIGNED。**V7「登记面」达成**。

> **一处措辞不精确（非缺陷）**：§10.4 写「CHECK9-coverage | 新脚本已覆盖（`uncovered_gate_scripts()` 返回空）」。
> **实测** `uncovered_gate_scripts()` 只 glob `check-*.py`（24 个），**两个新脚本本就不在该函数扫描面内**（`agate_markers.py` / `agate-mark.py` 不匹配 `check-*.py`）。返回空**不能证明**它们被覆盖——真正证明覆盖的是**锚点表里确实有这两条**（我已实测为 True）。**结论不变**，但建议把该行表述改为「已登记锚点表（`SCRIPT_ALIGNMENT_ANCHORS` 含两条）」以绑定到真实判据。

---

### A7: 设计原则一致性 —— ALIGNED

逐条核查相关 ADR：

| ADR | 内容 | 本批一致性 |
|---|---|---|
| **ADR-002** 可判定性（gate 门槛机器可判定） | 本批把标记**判据**单源化，并用 `mk_1`/`mk_3` 把「判据漂移」变为**机械可检**——正是 ADR-002 的强化。`mk_3`（setter 产物必被 checker 命中）使「生成器与判据分叉」**结构上不可能**。 | ✅ ALIGNED |
| **ADR-003** 最小约定——不绑定技术栈 | `markers.yaml` 只定义**协议内部**标记形态，不触及项目技术栈；`agate-mark.py` 零外部依赖。 | ✅ ALIGNED |
| **ADR-001** 隔离性——主 Agent 不写产出 | D2 决策「setter 只输出 stdout、不落盘」**刻意为遵守 ADR-001**（§3.3 关键设计点表）。实现 `agate-mark.py` 确无写文件路径。 | ✅ ALIGNED |
| **ADR-007** 机器字段并入 frontmatter——单工具双读 | 同构思路：与 `phases.yaml`/`dispatch.yaml`/`roles.yaml` **同层同级**放入 `rules/`（§3.1 理由段），复用既有「数据面权威源」范式与 S-5 schema 机制。 | ✅ ALIGNED |

**结论**：**ALIGNED**（无 NEEDS_HUMAN_REVIEW 项）。

> **附带观察（不构成 A7 结论）**：本批引入了一个新的架构模式——「**判据注册表 + 取值库 + 生成器**」三元组。
> 既有 ADR 未记载该模式。按角色文件原则「如发现未记录的架构决策，建议补充新 ADR」，
> **建议**补一条 ADR（如「ADR-008：可判定判据的单一权威源」），把「判据不得在消费方复制」从本批的
> `mk_1` 约定升格为**跨机制通则**（否则下一个机制仍会各自为政）。此为**建议**，不影响 ALIGNED。

---

### A8: 声称-命令绑定 —— MISALIGNED

逐条对账。**凡我无法给出产出命令的声称，判定为应删除或应更正。**

| # | 声称（出处） | 我的产出命令 | 结论 |
|---|---|---|---|
| 1 | `SCOPE_PLUS` 判据 12 处 / `DESIGN_GAP` 32 处（§1.2） | `grep -rln DESIGN_GAP agate/ --include=*.md \| wc -l` → **18** ✅；脚本/测试侧 `grep -rln ... --include=*.py \| grep -v __pycache__ \| grep -v agate_markers \| wc -l` → **15**（非 14） | ⚠️ **部分不符**：文档 18 ✅ 精确；脚本/测试侧我数得 **15**（作者称 14）。若把本批新加的 `agate_markers.py` 计入则 16。**14 无法复现** |
| 2 | PR #387「改动 **14 个已跟踪文件**（+ 1 新设计说明）」（§1.3） | `git show --name-only --format="" 6101a9e \| grep -v '^$' \| wc -l` → **18** | ❌ **不符**。§1.3 表格 4+6+4=14 的**明细自洽**（各文件均真实），但**总数不完整**：commit 实际改 **18** 个跟踪文件（漏计 3 份 review 报告 + `design-scope-plus-declaration-form.md`）。**建议**改为「14 个**语义相关**文件（另有 4 份评审记录）」并附 `git show --stat 6101a9e` |
| 3 | 存量「**45 种**标记 / ≥3 次 **30 种**」（§1.1:19-20；CHANGELOG:25） | 按其自述口径 `agate/**` 扫 `[A-Z_]{3,}` | ❌ **无法复现**。我试了 10 种口径：`agate/**/*.md`+`[A-Z_]{3,}` → **32/20**；须闭合 `]` → 22/11；含所有文件类型 → 58/32；含 `archived`+`docs` → 75/34；放宽长度 → 75/42。**没有一种得到 45/30**。**建议**：删除该数字或补上精确命令与口径 |
| 4 | 「漏改 **5 处** / 漏改率 36%」（§1.3；CHANGELOG:24） | 5 处**均逐一核实存在**（`check-scope-resolved.py` 注释 ✅、`test_sc_15` docstring ✅ 见 `test_check_scope_resolved.py:276`、`design-notes/README.md` ✅、CHANGELOG ✅、设计说明 ✅） | ✅ **可复现**。⚠️ 但 36% 是 `5/14`，而 #2 已证总数应为 18 ⇒ 若按 18 计应为 28%。**与 #2 联动更正** |
| 5 | 「**32 处**」`DESIGN_GAP`（§1.2:32；§10.5:441；CHANGELOG:24） | 见 #1 | ⚠️ 见 #1（14+18=32 的**分解**成立，但 14 那一半数不准） |
| 6 | 批次 B 硬门禁「通过 **9** / 跳过 **32** / 失败 **0**」（§10.2；CHANGELOG） | 我自己遍历 41 任务实跑 → `passed=9 skipped=32 failed=0`，`DIST: {0: 41}` | ✅ **实测复现** |
| 7 | 「差异文件数 = **0**」（§10.2:387） | 1564 文件逐文件新旧比对 → `DIFF FILES: 0` | ✅ **实测复现** |
| 8 | 「**45** 种」「**2529** 用例」「**2309 passed**」「**195 passed**」「**mk 30 用例**」「0 ERROR / 386 WARNING」 | 见 #3 / A4 各命令 | 2529 ✅、2309 ✅、195 ✅、30 ✅、0 ERROR/386 WARNING ✅；**45 ❌** |
| 9 | §10.5 G4「只加 1 条 → 生成/`--list`/守护**零代码改动**自动可用」 | 需临时改注册表验证 | ⚠️ **未独立复现**（只读纪律下不做仓库内写操作；已由 `mk_*` 全量遍历 `M.names()` 的**实现结构**佐证：测试与 CLI 均遍历注册表，无硬编码标记名）。**我推断成立，但未实测** |
| 10 | §10.3(1) 「初版统一规则 ⇒ 通过 **11** / 跳过 **30**」 | 该数字描述**已被修正的历史中间态**，当前树不可复现 | ⚠️ **不可复核**（历史状态，非当前事实）。按角色原则「无法给出命令的声称应删除」——**建议**删除 `+2` 的中间态数字，只保留结论 |
| 11 | §10.3(2) 「`lead_variants` …… 否则会改变 `agate_common.py` 的既有行为」 | `agate_common=59` vs `new=121` | ❌ **声称反了**：新实现**确实改变**既有行为。见 HIGH-1 |
| 12 | §10.3(1) 「允许跨行参数（存量 **3 处**：TAG0027/P7:48、TAG0031/P1:371、TAG0031/P7:60）」 | 三处**均真实存在**（`sed -n '48p'` 等已验）；但全仓 **11 处**跨行命中（限 `P1-requirements.md` 且剥 AGATE_CARD 后仍有 **5 处**） | ⚠️ **三例真实，但「存量 3 处」作为总数不成立**（实为 11；最小口径 5）。**建议**改为「如 `TAG0027/P7:48` 等（全仓 11 处）」 |

---

## 新引入问题

### HIGH-1：`pattern("DESIGN_GAP")` 过度匹配 `DESIGN_GAP_REVIEWED`，与 `agate_common` 行为不等价

**位置**：`agate/scripts/agate_markers.py:115-119`（`_body()`）、`agate/rules/markers.yaml:73-80`

**事实**（**我已实测**）：

```
$ python3 -c "import agate_markers as M; print(M.pattern('DESIGN_GAP').search('[DESIGN_GAP_REVIEWED: x]'))"
<re.Match object>            ← 命中！旧实现为 False

$ # 逐 P7 文件对账 agate_common.count_design_gap(text, True) vs len(pattern('DESIGN_GAP').finditer)
P7 DESIGN_GAP: agate_common=59  new=121  ratio=2.05x
DESIGN_GAP_REVIEWED lines falsely counted as DESIGN_GAP: 61
```

**两个成因**：
1. `_body()` 对带参标记用 `\[NAME(?::\s*(.*?))?($|[^a-z])`，其中 `:` 组**可选**，而 `_` 满足 `[^a-z]` ⇒ `DESIGN_GAP` 前缀吞掉 `DESIGN_GAP_REVIEWED`。旧 `agate_common` 用字面 `\[DESIGN_GAP:`（**冒号必选**），不吞。
2. 跨行匹配（`re.MULTILINE` + `\s*`/`.*?`）。

**为何是 HIGH**：
- 本批把 `markers.yaml` 定为 **`DESIGN_GAP` 判据的权威源**（`judged_by: [agate_common.py]`，`markers.yaml:80`），并把 schema 纳入 S-5、锚点纳入 CHECK 9——即**正式声明了该注册表承载 DESIGN_GAP 判据**。但该判据与**实际在判的** `agate_common` **不等价**（2.05 倍偏差）。
- `DESIGN_GAP` ↔ `DESIGN_GAP_REVIEWED` 是**配对校验**的核心（P4 写、P7 审）。计数翻倍会直接破坏配对语义。
- **§10.3(2) 与 CHANGELOG 明确声称「不会改变 `agate_common` 的既有行为」——该声称与实测相反**，属 A8 意义上的**不可兑现声称**。

**当前是否已造成破坏？——否（latent）**。**我已实测**：`pattern("DESIGN_GAP")` **无任何消费方**（`check-gate.py` 仍走 `agate_common.count_design_gap`）：

```
$ grep -rn 'pattern("DESIGN_GAP")' agate/scripts/ agate/tests/ --include=*.py
（空）
```

⇒ 存量判定**未被污染**（这也是 A5 判定 ALIGNED 的原因）。但**下一个按 `judged_by` 去接线的消费方会立刻踩中**，且**现有测试抓不到**（`test_marker_single_source.py` **未**含任何 `DESIGN_GAP` 与 `agate_common` 的等价断言——我已实测 `grep -n "count_design_gap" test_marker_single_source.py` 为空）。

**建议修复**（择一，倾向 A）：
- **A**：`_body()` 的带参分支对「标记名是另一已登记标记的前缀」的情形加**词边界负向断言**（如 `(?!_)`），并让 `DESIGN_GAP`/`DESIGN_GAP_REVIEWED` 的区分显式化。
- **B**：为 `DESIGN_GAP` 家族保留 `agate_common` 的**字面冒号**语义（即带参形态要求 `:`，除非注册表显式声明 `colon_optional: true`）。
- 无论哪种，**必须补一条回归断言**：对全仓 P7/P4 文件断言 `len(pattern("DESIGN_GAP").finditer(t)) == count_design_gap(t, True)`（或至少断言 `DESIGN_GAP` **不**命中 `[DESIGN_GAP_REVIEWED:`）。

---

### MEDIUM-2：`mk_3` 在「判据过宽」方向是盲的（与 HIGH-1 同源）

**事实**（**我已实测**）：把 `render()` 改成生成全角冒号形态 `[DESIGN_GAP： 内容]`：

```
$ python3 -m pytest agate/tests/unit/test_marker_single_source.py -q -p no:randomly
..............................                                           [100%]
30 passed in 0.16s        ← 全绿
```

原因：判据 `($|[^a-z])` 过宽，`：` 满足边界。**设计 §3.5 声称 `mk_3` 是「最强一条」、让分叉「结构上不可能」——该强度仅在「render 生成非法形态」方向成立**，反方向不成立。

**建议**：把 §3.5 的措辞收窄为「render 生成**判据不认**的形态不可能」，并补一条「判据不得命中**配对标记**」的反向断言（正是 HIGH-1 的守护）。

---

### MEDIUM-3：§1.3「14 个已跟踪文件」与 commit 实际 18 个不符（A8 #2）

见 A8 #2/#4。**影响**：该数字是本设计**最强动机**（「漏改率 36%」）的分母。分母不准 ⇒ 动机的量化基础需重算（按 18 计为 28%，仍是**很强的动机**，故不影响设计成立，但数字须更正）。

---

### LOW-4：§10.4「CHECK9-coverage：新脚本已覆盖」绑定到了非真实判据

见 A6 末「措辞不精确」。`uncovered_gate_scripts()` 仅扫 `check-*.py`（24 个），两个新脚本**不在其扫描面**，返回空**不构成**覆盖证据。（真实覆盖由锚点表成立，实测 True。）

### LOW-5：`docs/design-notes/design-scope-plus-declaration-form.md` 未加前向指针（A3b）

见 A3b。属**历史设计说明未标注已被取代**，非判据副本，无功能影响。

### LOW-6：§3.3 示例命令对无参标记会失败

`agate-mark.py SCOPE+ "…"` **实测 exit 1**（"标记 SCOPE+ 不接受参数"）。§3.3:226 的示例与之冲突。§10.3(1) 已更正语义，建议同步改 §3.3 示例。

### ✅ 已核查**未**发生的问题（供留痕）

- **怀疑点 6（表格 `|` 污染）**：**未复现**。实测本批 6 个 md 文件的**全部** markdown 表格：
  - 新增行 `docs/design-notes/README.md:34`（本批新增）：**4 列，正确** ✅
  - 唯一 1 处列数不符在 `docs/design-notes/README.md:28`（`design-dispatch-routing.md` 行，5 列）——**已实测为既有状态**：`git show HEAD:docs/design-notes/README.md` 该行**同为 5 列**，**非本批引入**。上一批的坑**未重演**。
- **`agate/scripts/README.md` 写不存在的脚本名（CHECK 10）**：**未触发**，consistency **0 ERROR**。
- **`check-yaml-schema.py` 初跑报 `SCHEMA-markers: ERROR 文件缺失 ../../.agate/v0.77.0/...`**：**已定位为环境解析问题，非本批缺陷**。因本 checkout **无 `.agate-version`**，`resolve_agate_root` 回退全局 `current` → 指向 `~/.agate/v0.77.0/agate`（无 markers 文件）。**固定 `AGATE_ROOT` 后全绿**：

```
$ AGATE_ROOT=/home/kity/oclab/agateon/agate python3 agate/scripts/check-yaml-schema.py
SCHEMA-phases: OK
SCHEMA-dispatch: OK
SCHEMA-roles: OK
SCHEMA-markers: OK          ← 全 OK，exit 0

$ AGATE_ROOT=… python3 agate/scripts/check-structure-consistency.py
S1-phases: OK  S2-workflow: OK  S3-cards: OK  S4-scripts: OK
S5-schema: OK  S6-references: OK  S0-numbers: OK
```

- **ruff**：`~/.venvs/agate-dev/bin/ruff check <6 个改动 py>` → **All checks passed!**
- **§10.3(2) 的 `_rules_test_utils.py` 修复**：**核实为正当修复**——`make_fake_root()` **补齐了缺失文件** `rules/markers.yaml` + `rules/schema/markers.schema.json`，**未削弱任何断言**。§10.3(2)「假树须镜像真协议结构……非改测试迁就实现」的**自我更正准确**。

---

## 总体判定

**`NEEDS-REVISION`** —— **不建议以当前状态 commit**。

**理由**：A5 的**硬门禁（判定不变）经我独立实测确实通过**（9/32/0、差异 0、与真实旧实现 0 偏离），本次改造**对存量行为零破坏**，这一点是扎实的。但存在两类必须收口的缺陷：

1. **HIGH-1**：注册表**被正式声明**为 `DESIGN_GAP` 判据权威源（`judged_by` + schema + 锚点三处登记），而该判据与**实际在判的** `agate_common` **不等价（2.05×）**，且**无测试守护**。这使本批「单源」的**核心承诺**（G1 判据单源）在最重的那个标记上**名不副实**——当前靠「尚无消费方」维持安全，属**结构性定时炸弹**。同时 **§10.3(2) 的声称与实测相反**。
2. **A8 四条数字声称不可复现**（45 种 / 14 文件 / 存量 3 处 / 中间态 11-30），其中「14 文件」与「45 种」是设计**动机**的量化基础。按角色 A8 原则「**无法给出命令的声称应删除**」。

**可提交的最小条件**（建议）：

| # | 收口项 | 类型 |
|---|---|---|
| 1 | 修 `DESIGN_GAP` 前缀吞并（`(?!_)` 或字面冒号），并补 `pattern("DESIGN_GAP")` ↔ `agate_common.count_design_gap` 的等价回归断言 | **代码 + 测试（HIGH-1）** |
| 2 | 更正 §10.3(2) / CHANGELOG 中「不会改变 `agate_common` 既有行为」的声称 | 文档（A8 #11） |
| 3 | 更正「14 个已跟踪文件」→ 实际 18（并联动重算漏改率）；补 `git show --stat 6101a9e` 命令 | 文档（A8 #2/#4） |
| 4 | 删除或补命令的「45 种 / 30 种」；「存量 3 处」→ 11 | 文档（A8 #3/#12） |
| 5 | 收窄 §3.5 `mk_3`「最强一条」的表述（仅覆盖过严方向）；补 MEDIUM-2 的反向断言 | 文档 + 测试 |

**建议（不阻断提交）**：LOW-4（§10.4 措辞绑定真实判据）、LOW-5（历史设计说明加前向指针）、LOW-6（§3.3 示例）、A7 附带观察（补一条判据单源 ADR）。

> **闭环标注**：本报告**无 `NEEDS_HUMAN_REVIEW` 项**，故无需 `[HUMAN_CONFIRMED: ...]` 配对标记。
> 所有结论均为 ALIGNED / MISALIGNED，可直接进入修复-复审闭环。

---

## 审查方法留痕（只读纪律执行说明）

- **未执行**任何写仓 git 命令：全程无 `checkout/restore/reset/stash/clean/add/commit/switch -f`。
- **未编辑/删除**任何被评审文件。
- 变异测试**全部**在 `<仓库根>/.agate-tmp/mut{1..6}/` 的一次性副本上进行，「建→用→清」均在**同一次 bash 调用**内完成；每次变异均以 `grep` 回显确认变异**已实际落盘**（防止空跑假红/假绿）。
- scratch 过程中**首次 mk_1 变异因锚点字符串未匹配而未生效**（当时读到 `30 passed`），我**据此重新断言锚点并复跑**，确认 mk_1 真实转红——**如实上报该次失败，未转而"修好"被评审仓库**。
- 唯一写入路径：本报告文件（写前已 `ls` 确认不存在同名文件，符合 BDD-8）。
- **区分说明**：文中所有标「我已实测」的结论均附**真实命令输出**；A8 #9（G4 零代码改动）与变异测试的边界分析标为**推断**，未标为实测。
