---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B / H1——修 3 条实测判据缺陷：RM-AG0090（check-gate P2 dispatch_plan 解析失败由 fail-open 改 fail-closed，字段缺失仍放行）；RM-AG0091（check-judge-verdict 两处过宽收窄：闭合标签终止符 + 纯阶段序列豁免）；RM-AG0092（agate-read-p5-commands 只剥成对引号 + P2 卡补两条写法约束）
files_changed: [agate/scripts/check-gate.py, agate/scripts/check-judge-verdict.py, agate/scripts/agate-read-p5-commands.py, agate/phase-cards/P2-design.md, agate/tests/unit/test_check_gate.py, agate/tests/unit/test_check_judge_verdict.py, agate/tests/unit/test_agate_read_p5_commands.py]
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（P2-design.md:130 契约欠精确；新节「或空格须加引号」不准确） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（同上；P2-design.md:203 引用的 dispatch_plan 先例已陈旧） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（反向传播面：CHANGELOG.md / UPGRADING.md；已在 diff 内的 P2:203 未同步） |
| A4 | 测试覆盖 | **ALIGNED**（273 passed；全量 2886 passed + 1 与本批无关的环境失败；红态已实测） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（CHANGELOG [Unreleased] 空；行为变更未标注） |
| A6 | 锚点表覆盖 | **ALIGNED**（无脚本增删改名，CHECK 9 锚点不受影响） |
| A7 | 设计原则一致性 | **ALIGNED**（ADR-002 / ADR-014 / ADR-015；仅一处引文准确性见 A1） |
| A8 | 声称-命令绑定 | **ALIGNED**（「273 passed」「0 ERROR」「仍被拦/不误报」均已逐条复现） |

> 三项修复的**技术实现本身正确**：语义方向（fail-open→fail-closed、收窄误报不放宽拦截、只剥成对引号）与 DEBT0043/0044/0047 的 closure_criteria 一致，向后兼容路径（字段缺失 / frontmatter 坏 YAML）实测保住。下述 MISALIGNED 均为**文档面未同步**，非脚本逻辑缺陷。

---

## 逐项审查

### A1: 文档→脚本对齐

**变更涉及的协议规则**：`dispatch_plan` 字段契约（P2-design.md:126-130）、`gate_commands` 值写法（P2-design.md:169-187）。

**文档声明**（`agate/phase-cards/P2-design.md:130`）：

> - 缺字段 / 坏 YAML → P2 gate 跳过校验，行为等同现状（向后兼容，不误拦）

**脚本实现**（`agate/scripts/check-gate.py:939-948`）：

> ```python
> raw = _md_field_get("dispatch_plan", p2_file)
> if not raw:
>     return None
> try:
>     plan = json.loads(raw)
> except ValueError as exc:
>     return f"dispatch_plan 存在但 JSON 解析失败（{exc}）…"
> if not isinstance(plan, dict):
>     return f"dispatch_plan 解析结果须为对象（dict），实际 {type(plan).__name__}"
> ```

**结论**：**MISALIGNED**

**差异**：修后「字段存在、但 YAML 合法而值为非合法 JSON」的情形（如 `dispatch_plan: single`，YAML 解析为字符串 `"single"`；或 `dispatch_plan: '{"mode": "single"'`）→ **ERROR + exit 1**，不再跳过。文档只写「坏 YAML → 跳过」——「坏 YAML」在字面上只覆盖「frontmatter 无法解析 → 字段不可读 → 放行」这条路径（该路径确实仍放行，`test_dispatch_plan_malformed_yaml` 用 `{mode: [unclosed` 锁定），但**未覆盖**「YAML 合法 / JSON 非法」这条新拦截路径。读者据 130 行会以为任何写坏的 `dispatch_plan` 都被跳过。check-gate.py 的契约注释（:930-933）已把两种情形拆开，**用户面权威文档（P2 卡）未同步**。

**建议**：把 130 行改为区分两种情形，例如「**字段缺失 / frontmatter 坏 YAML（字段不可读）→ 跳过**（向后兼容）；**字段存在但值非合法 JSON / 非对象 → P2 gate ERROR + exit 1**（RM-AG0090 修复 fail-open）」。

**附加（同一新节内的准确性问题）**：`agate/phase-cards/P2-design.md:186` 新增约束①称「**含引号或空格**的命令值须整体加引号」。实测（`P2_DESIGN=… python3 agate/scripts/agate-read-p5-commands.py`）：

> `P5: pytest -q --tb=no`（无引号、含空格）→ `"cmd": "pytest -q --tb=no"`（**空格无需引号**）
> `P5a: pytest -k 'foo'`（无引号、含引号）→ `"cmd": "pytest -k 'foo'"`（**修后亦无需引号**）

即「或空格」这一分句为**事实错误**；且修后读取器「只剥成对引号」，含引号的值不包裹也能正确读回（包裹是安全惯例，非硬需求）。同一句后半「读取器只剥成对的首尾引号…不成对则原样保留」是对新行为的**准确**描述，与前句自相矛盾。建议删「或空格」分句，并把「须整体加引号」降为「建议整体加引号（安全惯例）」。

---

### A2: 脚本→文档对齐

**脚本实现**（变更）：`_gate_p2_dispatch_plan` 的 fail-open→fail-closed（check-gate.py:939-948）、`agate-read-p5-commands.py:21-30` 的 `_strip_paired_quotes`。

**对应文档**：`agate/phase-cards/P2-design.md`。

**结论**：**MISALIGNED**

**差异**：与 A1 同源——脚本行为已变，P2 卡契约未同步：

1. `P2-design.md:130`（`dispatch_plan` 字段契约）——未反映 fail-closed，见 A1。
2. `P2-design.md:203`（`{key}_timeout_seconds` 字段规则）——原文「沿用 `dispatch_plan` 的『缺字段 / **坏 YAML** → gate 跳过校验』先例」，所引先例已陈旧（坏 YAML 语义在 RM-AG0090 后已收窄为「frontmatter 不可读」）。该行只是引用先例、其自身结论（`timeout_seconds` 缺字段不阻断）仍成立，属**轻度陈旧引用**，应同步措辞。
3. `P2-design.md:186`（新节约束①）——见 A1 附加。

**说明（判据方向无冲突）**：RM-AG0092 的读取器改动**收窄**了行为（不再误吞引号），与新节「只剥成对引号」一致；`is_gate_meta_key`（`agate_common.py:201-209`，只精确匹配 `_formatter`/`_timeout_seconds` 后缀）与 `check-pruning.py` 不解析 `gate_commands` 值内容，**新节不引入新 key、不与既有解析冲突**。`agate/scripts/README.md:188`（「解析 gate_commands.P5 块 → JSON」）与 `agate_common.py:207` 均未描述引号语义，无需改。

**建议**：同步 130 / 203 / 186 三处措辞（见 A1 建议）。

---

### A3: 一致性连锁 + 反向传播

**A3a 连锁（已知衍生改动）**：`check-gate.py` 契约注释块（:928-938、:1094-1096）已随实现更新 ✔；三处脚本注释均更新 ✔。

**A3b 反向传播（主动推断「应被影响但未列在 diff 中」的文件，逐一验证）**：

| 文件 | 是否应受影响 | 验证结论 |
|------|------------|---------|
| `agate/phase-cards/P2-design.md`（:130/:203） | 是 | **未同步**（见 A1/A2）——已在 diff 内但不完整 |
| `CHANGELOG.md` | 是（协议语义变更） | **[Unreleased] 为空，未登记**（见 A5） |
| `agate/UPGRADING.md` | 待定 | `:1450`（v0.49.0 历史条目）描述旧行为，**历史条目不改**；fail-open→fail-closed 属行为变更，**建议**加新版本条目说明「既有任务若写坏 `dispatch_plan` 将被新拦截」 |
| `agate/assets/templates/task-files.md:302` | 否 | 只引「缺字段 → gate 跳过校验」，修后仍准确 ✔ |
| `agate/dispatch-protocol.md:400-415`（Judge 信息隔离） | 否 | 只说「两节」；修后扫描面**确实**收窄到两节，文档反而更准，无需改 ✔ |
| `agate/WORKFLOW.md` / `agate/state-machine.md` | 否 | 无 `dispatch_plan` 解析语义、无 judge「两节」扫描面细节 ✔ |
| `agate/rules/*.yaml` | 否 | OBL-P2-10 锚点 `#dispatch_plan 机器字段`、OBL-P2-11 锚点 `#gate_commands 声明`、OBL-X-25 锚点 `#Judge 信息隔离（P6.5）` 均仍存在 ✔ |
| `agate/scripts/README.md` | 否 | 无脚本增删/改名；描述为粗粒度，无需改 ✔ |
| 消费 `agate-read-p5-commands.py` 的脚本 | 否 | 唯一消费方 `agate-capture-env-baseline.py`（`READ_P5`，:101/:108-109 直接用 `cmd`）——修后 `cmd` 更准，不依赖旧吞引号行为 ✔ |

**结论**：**MISALIGNED**（P2:203 未同步 + CHANGELOG/UPGRADING 反向传播面缺口）。

**建议**：按 A1 修 P2 卡三处；补 CHANGELOG；评估 UPGRADING 新条目。

---

### A4: 测试覆盖

**最近一次 pytest 全量实跑输出**：

```
$ python3 -m pytest agate/tests/ -n auto -q
1 failed, 2886 passed, 2 skipped in 85.51s (0:01:25)
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
  → 断言 `opencode debug agent orchestrator` rc=0，实际 rc=1
    （stderr: Unknown subcommand "agent" for "opencode debug"，Did you mean "agents"?）
```

唯一失败为 **opencode CLI 子命令名变更（`agent`→`agents`）导致的环境失败**，与被评审的 7 个文件**无任何交集**（该用例只读 `~/.opencode` 配置与 CLI），属既有环境漂移，**非本批引入**。

**本批 3 个改动测试文件实跑**：

```
$ python3 -m pytest agate/tests/unit/test_check_gate.py \
    agate/tests/unit/test_check_judge_verdict.py \
    agate/tests/unit/test_agate_read_p5_commands.py -n auto -q
273 passed in 8.85s
```

**新增用例覆盖**：RM-AG0090 +3（缺字段→放行 / 坏 JSON→拦 / 非 dict→拦）；RM-AG0091 +5（阶段序列白盒 / 真路径白盒 / 闭合标签白盒 / 阶段序列端到端 / 闭合标签端到端）；RM-AG0092 +2（成对双引号+末尾单引号 / 首尾不成对）。

**红态实测（用 `git show HEAD:` 的旧脚本在 scratch 直调，未触碰仓库）**：

| 输入 | OLD | NEW |
|------|-----|-----|
| `_gate_p2_dispatch_plan`：bad JSON `{"mode": "single"` | `None`（放行） | 错误串 |
| 非 dict `[1,2]` | `None`（放行） | 错误串 |
| 缺字段 / 空 | `None` | `None`（向后兼容保住） |
| `_check_whitelist_outside(['覆盖 P0/P1/P2/P3/P4/P5/ 各阶段'])` | `['p0/p1/p2/p3/p4/p5/']` | `[]` |
| `_two_sections`（含 `</dispatch_guide>` 的文档） | 并入闭合标签后正文 | 仅两节 |
| `_strip` on `"pytest -k 'foo'"` | `pytest -k 'foo` | `pytest -k 'foo'` |

**结论**：**ALIGNED**。边界覆盖充分（放行/拦截两侧、白盒/端到端两径）。

---

### A5: 下游影响 + 文档传播

**下游 gate 行为影响**（均为行为变更）：

- **RM-AG0090**：字段存在但 JSON 坏 / 非 dict 的任务，P2 gate 由**静默放行**变为 **exit 1**。这是**收严**——可能新拦截此前"侥幸通过"的存量任务（其 `dispatch_plan` 本就写坏，拦截是预期行为）。
- **RM-AG0091**：此前会因 `P0/P1/…` 阶段序列或 `</dispatch_guide>` 后正文**误报 exit 1** 的 P6.5 judge 派发，现正常通过（收窄误报，不放宽真拦截——见 A8）。
- **RM-AG0092**：`gate_commands` 值含引号时读回更准确（修 bug）。

**CHANGELOG**：`CHANGELOG.md` 的 `## [Unreleased]` 段**为空**，本批 3 条 gate 语义变更**未登记**。既有先例（v0.80.x 中 TAG0042 批 0 的 hotfix 均登记于 CHANGELOG）支持为 hotfix 补条目。

**UPGRADING**：RM-AG0090 属行为变更，建议评估是否需要新版本条目（`UPGRADING.md:1450` 为 v0.49.0 历史条目，描述的是引入 `dispatch_plan` 时的旧行为，**不改历史条目**）。

**结论**：**MISALIGNED**（CHANGELOG 未标注 + UPGRADING 待评估）。

**建议**：在 `[Unreleased]` 补「修复」条目，逐条写明三项语义变更；在 `UPGRADING.md` 决定是否加节。

---

### A6: 锚点表覆盖

本批**未新增 / 改名 / 退役**任何 `agate/scripts/` 下文件，故：

- CHECK 9 锚点表（`check-protocol-consistency.py:577+ SCRIPT_ALIGNMENT_ANCHORS`）无需增改；`check-judge-verdict.py` 锚点（:810-815，keywords `criteria_total`/`judge`）仍成立。
- `uncovered_gate_scripts()`（`agate_common` 单源判据，被 CHECK9-coverage 与 SG.6 共用）不受影响。
- OBL-P2-10/11、OBL-X-25 的 anchor 文本均仍存在于对应文档。

**结论**：**ALIGNED**。（说明：新 P2 节「命令值写法约束」是**写作约定**、无机械判据，未在 `obligations.yaml` 新增义务——符合该文件的 M/C/R 归宿约定，可接受。）

---

### A7: 设计原则一致性

逐条核对相关 ADR：

- **ADR-002（可判定性——gate 门槛机器可判定）**：`_gate_p2_dispatch_plan` 由「解析失败静默放行」改为「返回错误串 → exit 1」，使 `dispatch_plan` 门槛真正机器可判定。**一致**。
- **ADR-015（实质/非实质——门禁只用于会导致后续错误决策的错误）**：fail-open 属「静默漏检」实质错误，收严正确。**一致**。
- **ADR-014（判据单一权威源 + 引文须与真值一致）**：三处修复均未新增判据副本（`_two_sections`/`_check_whitelist_outside`/读取器各自仍是单点）。但**新 P2 节约束①「或空格须加引号」与真值不一致**（实测空格无需引号），违反 ADR-014「引文须与真值一致」——已计入 A1，此处仅标注。

**结论**：**ALIGNED**（设计方向一致；唯一的引文准确性问题按 A1 修复）。

---

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|------|---------|------|
| 「273 passed」 | `python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_judge_verdict.py agate/tests/unit/test_agate_read_p5_commands.py -n auto -q` | ✅ 复现：`273 passed in 8.85s`（= 3 个改动测试文件的 collected 数） |
| 「0 ERROR」 | `python3 agate/scripts/check-protocol-consistency.py` | ✅ 复现：exit 0，`仅有 414 个 WARNING，无 ERROR` |
| 「阶段序列不误报」 | `_check_whitelist_outside(['覆盖 P0/P1/P2/P3/P4/P5/ 各阶段'])`（直调 + 端到端 `test_rm_ag0091_phase_sequence_in_context_not_flagged_exit_0`） | ✅ 复现：`[]` / exit 0 |
| 「真黑名单路径仍被拦」 | `_check_whitelist_outside(['p5-test-results/'])` / `['p0/secret-dir/']` / `['P0/P1/p5-test-results/x']` | ✅ 复现：三者均仍命中 |
| 「既有 BDD-4 不回退」 | `python3 -m pytest agate/tests/unit/test_check_judge_verdict.py -n auto -q`（含 `test_bdd_4_*`） | ✅ 全绿 |
| 「字段缺失仍放行」 | `test_rm_ag0090_dispatch_plan_missing_field_passes` + 红态 scratch（missing OLD=NEW=None） | ✅ 复现 |
| 「坏 JSON / 非 dict 被拦」 | 红态 scratch（OLD=None→NEW=error）+ 2 条新用例 | ✅ 复现 |

**结论**：**ALIGNED**。无法复核的声称：无（本报告内所有数字均附命令）。

---

## 重点核查结论（对应任务 5 项）

1. **RM-AG0090 向后兼容是否真的保住**：✅ **保住**。`test_dispatch_plan_malformed_yaml`（`{mode: [unclosed`）经 `agate-md-field-get.py` 的 `_read_frontmatter` YAML 解析失败 → 输出空串 → `_md_field_get` 返回 `""` → `_gate_p2_dispatch_plan` 走 `if not raw: return None` → 放行；实测该用例在 273 中通过。字段缺失同理。**唯一调用点** `gate_p2`（check-gate.py:1097-1100）无其它 `None` 语义依赖；`test_check_mvwu.py:310`、`test_tag0050_obligation_behavior.py:109` 直调断言均仍成立。**既有测试中无「合法 YAML、坏 JSON 应放行」的相反期望**。

2. **RM-AG0091 是否只收窄误报、未放宽真拦截**：✅ 收窄正确。`_PHASE_SEQ_RE = ^(?:p[0-9]+/)+$` **只匹配整串恰为 `pN/` 的重复**：`p5-test-results/`（段含 `-`）、`p0/secret-dir/`、`P0/P1/p5-test-results/x`（末段非纯 `pN`）**均不匹配 → 仍被拦**（实测）。闭合标签终止符 `_TAG_END_RE`（仅认 `</...>`）只影响「节内最后一项后接闭合标签而非标题」的场景，**不误截断**正常节内容（正常节以 `#` 标题结束，终止逻辑不变）；`<objective_info>` 为开标签不匹配，且标准模板中它**总在 `</dispatch_guide>` 之后**，故被闭合标签先终止。既有 BDD-4 用例（`P6-acceptance.md` 黑名单 / `P3-test-cases.md` 白名单外）**不回退**（273 全绿）。
   - **残留边界（非缺陷，仅记录）**：① 单段 `p5/` 也被 `_PHASE_SEQ_RE` 豁免（`p5/` 不是黑名单目录，低风险）；② 若某 dispatch-context **缺 `</dispatch_guide>`** 而直接出现 `<objective_info>`，节仍会并入其后正文——标准模板恒含闭合标签，故不影响；③ `_check_prediction` 仍按设计扫描**全文**（BDD-4③），不受本节收窄影响。

3. **RM-AG0092 读取器改动是否影响既有消费方**：✅ 无负面影响。`_strip_paired_quotes` 行为实测：单引号值 `'pytest'`→`pytest` ✔；双引号值 `"pytest -q"`→`pytest -q` ✔；无引号 `pytest -q`→原样 ✔；`"pytest -k 'foo'"`→`pytest -k 'foo'` ✔（原实现吞尾引号）；首尾不成对 `'foo`→原样 `'foo` ✔。唯一消费方 `agate-capture-env-baseline.py` 直接用 `cmd`，修后更准。新 P2 节**不引入新 key**，与 `is_gate_meta_key` / `_timeout_seconds` 后缀、`check-pruning` 无冲突。**但新节「或空格」分句不准确**（见 A1）。

4. **实施者自报 5 处偏离**：
   - ① **spec 示例「真黑名单路径 `agate-workspace/tasks/OTHER/`」实测本就不被拦——独立核实：成立，替代恰当。** 直调 `_check_whitelist_outside(['agate-workspace/tasks/OTHER/'])` → OLD=NEW=`[]`（该函数只拦 `^p[0-9]` 目录或非白名单 `.md/.yaml` 路径，`agate-workspace/tasks/other/` 两者都不命中）。实施者改用 `p5-test-results/` + `p0/secret-dir/` 精准命中 `^p[0-9]` 分支，是**更恰当**的替代。该 spec 示例（未见诸仓库文本，疑在派发 prompt 中）系**笔误**。
   - ② 额外更新函数头注释块：**合理**——契约注释（check-gate.py:928-938）本就描述 `return None` 语义，不改会与实现矛盾。
   - ③ 未跑 consistency、由主 Agent 补跑：**已复现 0 ERROR**（见 A8），可接受。
   - ④ `_TAG_END_RE` 只认闭合标签：**可接受**——标准模板 `<dispatch_guide>…</dispatch_guide>` 恒含闭合标签（`dispatch-context.md:47`），开标签 `<objective_info>` 必在其后，故只认闭合标签足以覆盖 DEBT0044 场景（残留边界见重点核查 2②）。
   - ⑤ 未 commit：**符合** hotfix 未提交状态，与本次只读审查一致。

5. **A8 声称逐条给命令**：见上表——全部可复核，无无据声称。

---

## 需修复项（MISALIGNED 汇总）

| # | 文件:行 | 问题 | 建议 |
|---|--------|------|------|
| 1 | `agate/phase-cards/P2-design.md:130` | `dispatch_plan` 契约未反映 fail-closed（「坏 YAML → 跳过」欠精确） | 拆成「字段缺失/frontmatter 坏 YAML → 跳过」+「字段存在但值非合法 JSON/非对象 → ERROR + exit 1」 |
| 2 | `agate/phase-cards/P2-design.md:186` | 新节「含引号**或空格**须整体加引号」——「或空格」事实错误；「须」过强 | 删「或空格」；「须」降为「建议」（读取器修后含引号不包裹亦正确） |
| 3 | `agate/phase-cards/P2-design.md:203` | 引用的 dispatch_plan 先例「坏 YAML → 跳过」已陈旧 | 同步为「缺字段 → 跳过」或加注 |
| 4 | `CHANGELOG.md` `[Unreleased]` | 3 条 gate 语义变更未登记 | 补「修复」条目 |
| 5 | `agate/UPGRADING.md` | 行为变更（fail-open→fail-closed）未评估 | 决定是否加新版本条目（不改 v0.49.0 历史条目） |

> 修复 1-3 后重审 A1/A2/A3；补 CHANGELOG 后重审 A5。**脚本逻辑本身无需改动。**
