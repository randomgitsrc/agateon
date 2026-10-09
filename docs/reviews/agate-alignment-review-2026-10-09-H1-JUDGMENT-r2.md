---
review_date: 2026-10-09
reviewer: protocol-alignment-review
round: 2
change_summary: 第 2 轮复审——批 B / H1（RM-AG0090/0091/0092）第 1 轮 5 项 MISALIGNED 的修复核实 + 完整 A1-A8 复评
files_changed: [agate/scripts/check-gate.py, agate/scripts/check-judge-verdict.py, agate/scripts/agate-read-p5-commands.py, agate/phase-cards/P2-design.md, CHANGELOG.md, agate/tests/unit/test_check_gate.py, agate/tests/unit/test_check_judge_verdict.py, agate/tests/unit/test_agate_read_p5_commands.py]
---

# 协议-脚本对齐审查（第 2 轮）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（第 1 轮主项已修；**残留 1 处**：P2:186 句尾「不成对引号会被吞掉」与读取器实际行为相反） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（同 A1 同一残留） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（反向传播面已清；仅历史条目 `UPGRADING.md:1450` 保留旧叙述，按设计不改） |
| A4 | 测试覆盖 | **ALIGNED**（273 passed；全量 2886 passed + 1 与本批无关的环境失败） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（CHANGELOG 已补；UPGRADING 延后至发布符合本仓既有惯例） |
| A6 | 锚点表覆盖 | **ALIGNED**（无脚本增删改名） |
| A7 | 设计原则一致性 | **ALIGNED**（ADR-002/014/015） |
| A8 | 声称-命令绑定 | **ALIGNED**（全部声称已复现） |

> **总评**：第 1 轮 5 项中 **4 项完全修复、1 项（P2:186）主体修复但残留一句与读取器行为相反的表述**。三项脚本逻辑自第 1 轮起即正确，本轮无需改动脚本。剩余唯一 MISALIGNED 为一处用户面文档措辞，修复成本极低。

---

## 第 1 轮 5 项逐条核实结论

| # | 第 1 轮问题 | 本轮核实 | 结论 |
|---|------------|---------|------|
| 1 | `P2-design.md:130` 契约未反映 fail-closed | 现文：「缺字段 / frontmatter 坏 YAML（字段不可读）→ P2 gate 跳过校验（向后兼容，不误拦）；**字段存在但值非合法 JSON / 解析结果非对象 → P2 gate ERROR + exit 1**」——与 `check-gate.py:930-933` 契约注释**逐条一致** | ✅ **已修** |
| 2 | `P2-design.md:186` 新节「或空格须加引号」事实错误 | 「或空格」已删；「须」→「**建议**…**非硬需求**」；补「含空格的值本就不需要引号，实测 `P5: pytest -q --tb=no` 读回正确」——前半段与读取器一致 ✅。**但句尾残留**「不要写成首尾引号不成对的形态，否则引号会被误当定界符**吞掉**…」与新读取器「不成对则**原样保留**」**相反** | ⚠️ **主体已修，残留 1 处** |
| 3 | `P2-design.md:203` 引用的 dispatch_plan 先例陈旧 | 现文：「沿用 `dispatch_plan` 的『缺字段 / frontmatter 坏 YAML → gate 跳过校验；字段存在但值非合法 JSON → ERROR』口径」——已同步新口径 | ✅ **已修** |
| 4 | `CHANGELOG [Unreleased]` 为空 | 现新增 `### 修复` 三条（RM-AG0090 / RM-AG0091 / RM-AG0092），内容与实现逐条一致 | ✅ **已修** |
| 5 | `UPGRADING.md` 未评估 | 核实仓内先例：`git log -- agate/UPGRADING.md` 仅 **release 提交**（`922aee3c` v0.80.2 / `daf2d59b` v0.80.1 / `9bfef64d` v0.80.0）；`git log -- CHANGELOG.md` 含 **feature 提交**（`7430b905` 提交信息明写「CHANGELOG.md [Unreleased]：修复条目」，该提交**未动** UPGRADING） | ✅ **延后判定可接受** |

---

## 逐项审查

### A1: 文档→脚本对齐

**变更涉及的协议规则**：`dispatch_plan` 字段契约（P2-design.md:126-130）、`gate_commands` 值写法（P2-design.md:182-187）。

**逐条对齐核对（`dispatch_plan` 契约）**：

| check-gate.py 契约注释（:930-933） | P2-design.md:130（现文） | 一致？ |
|---|---|---|
| 字段缺失 / op 输出空（含 frontmatter 坏 YAML 导致字段不可读）→ 跳过 | 缺字段 / frontmatter 坏 YAML（字段不可读）→ P2 gate 跳过校验（向后兼容） | ✅ |
| 字段存在但值非合法 JSON → ERROR | 字段存在但值非合法 JSON → P2 gate ERROR + exit 1 | ✅ |
| 字段存在但解析结果非 dict → ERROR | （同句并入「解析结果非对象 → P2 gate ERROR + exit 1」） | ✅ |

> **A1 主项（第 1 轮 #1）已 ALIGNED。** P2 卡契约与脚本注释块 + 实现逐条一致。

**残留（第 1 轮 #2 未覆盖的一句）**——`agate/phase-cards/P2-design.md:186`：

> …读取器（`agate-read-p5-commands.py`）只剥**成对**的首尾引号——首尾同种才剥除，**不成对则原样保留**。**不要**写成首尾引号不成对的形态，**否则引号会被误当定界符吞掉**、命令语法破损（实测：`"pytest -k 'foo'"` 曾被读成 `pytest -k 'foo`）。

**脚本实现**（`agate/scripts/agate-read-p5-commands.py:21-30`）：

> ```python
> def _strip_paired_quotes(value):
>     if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
>         return value[1:-1]
>     return value          # 不成对 → 原样返回（不吞任何引号）
> ```

**实测**（`P2_DESIGN=… python3 agate/scripts/agate-read-p5-commands.py`）：

| 输入值 | 读回 `cmd` | 说明 |
|--------|-----------|------|
| `pytest -q --tb=no`（含空格、无引号） | `pytest -q --tb=no` | 空格无需引号 ✅（与新节前半一致） |
| `pytest -k 'foo'`（含引号、不包裹） | `pytest -k 'foo'` | 不包裹也正确 ✅（与新节前半一致） |
| `"pytest -k 'foo'"`（成对） | `pytest -k 'foo'` | 剥成对 ✅ |
| `'foo`（首尾不成对） | `'foo` | **原样保留**（**未吞**） |
| `"pytest -k 'foo'`（首尾不成对） | `"pytest -k 'foo'` | **原样保留**（前导 `"` 残留） |
| `foo'`（首尾不成对） | `foo'` | **原样保留** |

**结论**：**MISALIGNED**（残留 1 处）。

**差异**：句尾两处与真值不符——

1. **失败机理相反**：句内先说「不成对则**原样保留**」，紧接着说「不成对…否则引号会被**吞掉**」——**自相矛盾**。实测新读取器**从不吞**不成对引号（三例均原样保留）；「吞掉」是**旧**读取器（`.strip('"').strip("'")` 各自剥）的行为，已被本批修复。
2. **示例与论点不匹配**：所举 `"pytest -k 'foo'"` 是**成对**形态（首尾同为 `"`），并非「首尾引号不成对」；它是旧读取器在**成对值**上误吞内层尾引号的案例，与该句「不成对」的论点对不上。

**建议**：把该句改为与新行为一致，例如「**不成对的引号会被原样保留**（如 `P5: "pytest -k 'foo'` → 前导 `"` 残留致 shell 语法破损）——**读取器不会吞掉引号**；请确保引号成对或整体包裹」。或直接删除该句（前半句已充分说明读取器语义）。

> 说明：该句的**实践建议**（避免不成对引号）本身正确，问题在**机理描述与示例**——按 ADR-014「引文须与真值一致」，用户面权威文档不应留反向描述。

---

### A2: 脚本→文档对齐

**脚本实现**（变更）：`_gate_p2_dispatch_plan` fail-open→fail-closed（check-gate.py:939-948）、`_strip_paired_quotes`（agate-read-p5-commands.py:21-30）。

**对应文档**：`agate/phase-cards/P2-design.md`。

**结论**：**MISALIGNED**（与 A1 同一残留）。

**差异**：

- `P2-design.md:130`（`dispatch_plan` 契约）——**已同步** ✅（见 A1）。
- `P2-design.md:203`（`{key}_timeout_seconds` 向后兼容引用）——**已同步** ✅。
- `P2-design.md:186`（新节约束①）——**残留**：句尾失败机理与读取器实现相反（见 A1 残留）。

**无冲突项复核（第 1 轮结论维持）**：读取器改动**收窄**行为（不再误吞引号），与新节「只剥成对引号」一致；新节不引入新 key，`is_gate_meta_key`（`agate_common.py:201-209`，仅精确匹配 `_formatter`/`_timeout_seconds` 后缀）、`check-pruning.py` 不解析值内容——**无冲突**。

**建议**：按 A1 修 186 行句尾。

---

### A3: 一致性连锁 + 反向传播

**A3a 连锁**：`check-gate.py` 契约注释块（:928-938、:1094-1096）、`check-judge-verdict.py` 注释、`agate-read-p5-commands.py` docstring 均已随实现更新 ✅。

**A3b 反向传播（任务问 4：改 `P2-design.md` 后是否别处仍写旧口径）**：

| 文件 | 验证结论 |
|------|---------|
| `agate/UPGRADING.md:1450`（v0.49.0 条目：「坏 YAML 时 P2 gate 跳过校验」） | **历史版本条目**，描述该版本当时行为，**按设计不改** ✅（发布时若加新节另述新行为） |
| `agate/assets/templates/task-files.md:302`（「沿用 dispatch_plan『缺字段 → gate 跳过校验』先例」） | 只提「缺字段」，修后仍准确 ✅ |
| `agate/assets/execution-roles/architect.md:223`（「缺字段时 P2 gate 跳过（可选字段）」） | 只提「缺字段」，修后仍准确 ✅ |
| `agate/dispatch-protocol.md`（Judge 信息隔离，:400-415） | 只说「两节」；修后扫描面确实收窄，**更准** ✅ |
| `agate/WORKFLOW.md` / `agate/state-machine.md` | 无 `dispatch_plan` 解析语义、无 judge「两节」扫描面细节 ✅ |
| `agate/rules/*.yaml` | OBL-P2-10 / OBL-P2-11 / OBL-X-25 锚点仍存在 ✅ |
| `agate/scripts/README.md` | 无脚本增删改名，描述为粗粒度 ✅ |
| 消费 `agate-read-p5-commands.py` 的 `agate-capture-env-baseline.py` | 直接用 `cmd`，修后更准 ✅ |

**grep 反证**：`grep -rn "坏 YAML" agate/ docs/`（非测试/评审）仅命中 `UPGRADING.md:1450`（历史）+ 已修的 `P2-design.md:130/203`；`grep -rn "须整体加引号\|或空格.*加引号"` **0 命中**。

**结论**：**ALIGNED**。反向传播面已清，无遗漏旧口径（历史条目属预期保留）。

---

### A4: 测试覆盖

**最近一次 pytest 全量实跑输出**：

```
$ python3 -m pytest agate/tests/ -n auto -q
1 failed, 2886 passed, 2 skipped in 84.70s (0:01:24)
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
  （opencode CLI `debug agent` → `agents` 的环境失败，与本批 8 文件无交集）
```

**本批 3 个改动测试文件实跑**：

```
$ python3 -m pytest agate/tests/unit/test_check_gate.py \
    agate/tests/unit/test_check_judge_verdict.py \
    agate/tests/unit/test_agate_read_p5_commands.py -n auto -q
273 passed in 8.94s
```

与第 1 轮一致（新增用例仍为 RM-AG0090 +3 / RM-AG0091 +5 / RM-AG0092 +2）；本轮修改仅文档（P2 卡 + CHANGELOG），**未动测试**，用例数与红态结论不变。

**结论**：**ALIGNED**。

---

### A5: 下游影响 + 文档传播

- **CHANGELOG**：`[Unreleased]` 新增 `### 修复` 三条，逐条对应 RM-AG0090/0091/0092，与实现/脚本注释一致 ✅。
- **UPGRADING 延后评估（任务问 5）**：**判定可接受**。证据——`git log -- agate/UPGRADING.md` 仅 release 提交（v0.80.2/v0.80.1/v0.80.0）；而 `git log -- CHANGELOG.md` 的 feature 提交 `7430b905` 提交信息明列「CHANGELOG.md [Unreleased]：修复条目」且**未动** UPGRADING。⇒ 本仓惯例 = **[Unreleased] 期只写 CHANGELOG，UPGRADING 版本节在发布时写**（与 `AGENTS.md` 发布清单第 3 条一致）。**本次无需立即写 UPGRADING**。
  - **发布时必须**：新增版本 UPGRADING 节，并说明 RM-AG0090 的行为变更（既有任务若写坏 `dispatch_plan` 将被新拦截；`AGENTS.md` 发布清单要求「无破坏性变更也写」）。
- **下游 gate 行为**：RM-AG0090 收严（fail-open→fail-closed）、RM-AG0091 收窄误报、RM-AG0092 修读取 bug——三者方向正确，均在 CHANGELOG 有述。

**结论**：**ALIGNED**。

---

### A6: 锚点表覆盖

本批未新增/改名/退役任何 `agate/scripts/` 文件：

- CHECK 9 锚点表（`check-protocol-consistency.py` `SCRIPT_ALIGNMENT_ANCHORS`）无需增改；`check-judge-verdict.py` 锚点仍成立。
- `uncovered_gate_scripts()`（CHECK9-coverage 与 SG.6 共用单源判据）不受影响。
- OBL-P2-10/11、OBL-X-25 的 anchor 文本仍存在（本轮已 grep 确认）。

**结论**：**ALIGNED**。

---

### A7: 设计原则一致性

- **ADR-002（可判定性）**：fail-open→fail-closed 使 `dispatch_plan` 门槛真正机器可判定 ✅。
- **ADR-015（实质/非实质）**：fail-open 属「静默漏检」实质错误，收严正确 ✅。
- **ADR-014（判据单源 + 引文须与真值一致）**：三处修复未新增判据副本 ✅；**但 P2:186 句尾「不成对引号会被吞掉」与读取器真值相反**——违反「引文须与真值一致」，已计入 A1 残留。

**结论**：**ALIGNED**（设计方向一致；唯一引文问题按 A1 修复）。

---

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|------|---------|------|
| 「273 passed」 | `python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_judge_verdict.py agate/tests/unit/test_agate_read_p5_commands.py -n auto -q` | ✅ `273 passed in 8.94s` |
| 「0 ERROR」 | `python3 agate/scripts/check-protocol-consistency.py` | ✅ exit 0，`仅有 414 个 WARNING，无 ERROR` |
| 「全量不回归」 | `python3 -m pytest agate/tests/ -n auto -q` | ✅ `2886 passed`；唯一失败为无关环境失败 |
| 「含空格无需引号」 | reader 实测 `P5: pytest -q --tb=no` | ✅ `pytest -q --tb=no` |
| 「含引号不包裹也正确」 | reader 实测 `P5a: pytest -k 'foo'` | ✅ `pytest -k 'foo'` |
| 「不成对则原样保留」（**P2:186 现文声称**） | reader 实测 `'foo` / `"pytest -k 'foo'` / `foo'` | ✅ 三例均原样保留 ⇒ 反证句尾「会被吞掉」为**误述** |
| 「真黑名单路径仍被拦」 | `_check_whitelist_outside` 直调（第 1 轮） | ✅ `p5-test-results/` / `p0/secret-dir/` / `P0/P1/p5-test-results/x` 仍命中 |
| 「CHANGELOG 三条」 | `git diff CHANGELOG.md` | ✅ 三条与实现一致 |
| 「UPGRADING 发布时写（惯例）」 | `git log -- agate/UPGRADING.md` vs `-- CHANGELOG.md` | ✅ UPGRADING 仅 release 提交；CHANGELOG 含 feature 提交 |

**结论**：**ALIGNED**。无法复核的声称：无。

---

## 需修复项（MISALIGNED 汇总）

| # | 文件:行 | 问题 | 建议 |
|---|--------|------|------|
| 1 | `agate/phase-cards/P2-design.md:186`（句尾） | 「不成对引号会被误当定界符**吞掉**」与新读取器「不成对则**原样保留**」相反；示例 `"pytest -k 'foo'"` 是**成对**形态，不属「首尾不成对」 | 改为「不成对的引号会被**原样保留**（读取器不吞引号），故请确保引号成对或整体包裹」；或删该句 |

> 修复该句后 A1/A2 即转 ALIGNED，本批可 commit。**脚本逻辑无需改动。**
