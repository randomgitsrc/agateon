---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: H1-r3 增量复审（最终）——DEBT0067/0068 热修（`--list` 展示由实际守卫单源派生）
files_changed: [agate/scripts/agate-md-field-set.py, agate/tests/unit/test_debt0067_0068_write_side.py, docs/design-notes/design-md-field-set.md, agate-workspace/debt/tech-debt.md, agate/rules/phases.yaml, agate/scripts/agate-frontmatter-check.py, agate/phase-cards/P2-design.md, CHANGELOG.md]
---

# 协议-脚本对齐审查（HOTFIX DEBT0067 + DEBT0068）— H1-r3 增量复审（最终）

> 本文件为 r1/r2 的**覆盖更新**（r1 判 needs-revision·5 项；r2 判 needs-revision·1 项 A2）。
> r3 修 r2 唯一残留（`--list` 展示分区不准确）。本 r3 复核闭合 + 查新破坏 + 核 DEBT0072。

## 审查结论汇总（r3）

| # | 审查项 | r1 | r2 | r3 |
|---|--------|----|----|----|
| A1 | 文档→脚本对齐 | MISALIGNED | ALIGNED | ALIGNED |
| A2 | 脚本→文档对齐 | MISALIGNED | MISALIGNED | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | MISALIGNED | ALIGNED | ALIGNED |
| A4 | 测试覆盖 | ALIGNED | ALIGNED | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空） | ALIGNED（空） | ALIGNED（空） |
| A5 | 下游影响 + 文档传播 | MISALIGNED | ALIGNED | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED | ALIGNED | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED | ALIGNED | ALIGNED |
| A8 | 声称-命令绑定 | MISALIGNED | ALIGNED | ALIGNED |

**总体：`approved`（0 MISALIGNED）。** r2 唯一残留（`--list`/错误分区把证据字段误标「可 set」、把无 append 能力的字段误标「需 append」）**已真闭合**——展示**逐键**由 `set`/`append` 的**同一守卫**派生，且 `set` 行为**零改动**；无新破坏。DEBT0072 登记**如实**。

---

## 1. r3 唯一必改：展示分区是否真闭合 — 闭合 ✔

**机制**（`agate-md-field-set.py`）：新增 `_evidence_fields` / `_append_only_fields` / `_writable_set` / `_is_script_field` / `_append_spec` / `_key_capability`，四态 `set`/`append`/`script`/`none`；`--list` 的每个 key 行与分组、以及「非法 key」错误分组，**全部**经 `_key_capability` 派生。

**逐键对拍（本评审独立实测，非采信）**：

`P1-requirements.md --list`：
```
  - risk_level/phases/packages/domains: …（可 set）
其它可 set 的 schema 合法字段: ceremony, change_type, coupling_checklist, design_trivial,
  follows_existing_pattern, implicit_coupling, internal_only, internal_only_reason, override,
  ui_render_shape, ui_ux_dimensions, 跳过风险
仅登记/需 append（不可 set）: scope_resolved
仅登记，不可写入: need_confirm_resolved, suggest_resolved
```
`P6-acceptance.md --list`：
```
  - pass: 1（由脚本/角色产出，不可 set）
  - fail: 0（由脚本/角色产出，不可 set）
  - ui_affected: False（可 set）    - p5_evidence_reuse: 未设置（可 set）
由脚本/角色产出（不可 set）: regression_pass
```
`P6 set no_such_key` → 错误分组「（下列字段由脚本/角色产出，不可 set）: fail, pass, regression_pass」——**pass/fail/regression_pass 已移出「合法 key 清单」**（r2 曾把 `regression_pass` 列进「其它可 set」，实测 `set regression_pass` 被证据守卫拒）。

**真实行为核对**（逐类）：
| 展示 | 实测 |
|---|---|
| 「可 set」(`override`/`coupling_checklist`/`ui_render_shape`/`ceremony`…) | `set <key> <valid>` rc=0（test ⑨ 用合法值；见 A4）|
| 「需 append」(`scope_resolved`) | `set scope_resolved` **拒**；`append scope_resolved id=SP1 note=x` **OK**（rc=0）✔ |
| 「仅登记，不可写入」(`need_confirm_resolved`/`suggest_resolved`) | `set` **拒**；`append` **拒**（「不在本文件契约字段中」）✔ |
| 「由脚本/角色产出」(`pass`/`fail`/`regression_pass`) | `set` **拒**（`pass`/`fail` writer:system；`regression_pass` 证据字段）✔ |

⇒ 展示宣称与真实行为**逐键一致**。r2 的两处假宣称均消除。

**先红后绿（判别力）**：`_load_set_module` + 守护测试 `test_debt0067_r3_list_partition_matches_real_behavior`。本评审**独立做变异**（副本 `/tmp/opencode/mut-agate`，把 `_key_capability` 的证据分支去掉）→ 该测试 **[P6] 1 failed**（`regression_pass 展示「可 set」但 set 失败`）。⇒ 测试对「展示↔行为漂移」**有判别力**，非假绿灯。（主 Agent 声称换回 r2 手维二分 → `2 failed`；因 r2 代码未入 git，该**精确红态**无法复现，但判别力已独立证得。）

## 2. 新破坏：能力判定函数是否与 `set` 路径同源（别又成两份）— 同源 ✔

- `_key_capability` 的分支**逐条复用 `_cmd_set` 实际使用的同一函数/常量**：
  - `script` ← `_is_script_field`（=`_field_spec` writer==system，与 `_cmd_set` 顶部契约守卫同）∨ `_evidence_fields(get_mod)`（= `_cmd_set` 的证据守卫）；
  - `append`/`none` ← `_append_only_fields(get_mod)`（= `_cmd_set` 的追加守卫）+ `_append_spec`（=`_require_list_field` 的同逻辑，即 `_cmd_append` 的判据）；
  - `set` ← `_writable_set(...)`（=`_cmd_set` 的 `writable`，**同一函数**）。
- `_cmd_set` 现直接 `writable = _writable_set(...)`，`if key in _append_only_fields(...)`，`if key in _evidence_fields(...)` —— **参数化到同一批函数**，无第二份判据。
- 分支**次序**与 `_cmd_set` 守卫次序一致（script→append_only→writable）⇒ 对「既是证据又在可写面」（`regression_pass`）「既是 append-only 又在 schema」（`scope_resolved`）等交叠情形，展示与真实拒绝**同判**。
- **未引入新不一致**：`_cmd_list`/错误面只**改展示**；校验/拒绝路径（`set`）行为不变（见下）。

## 3. `set` 行为未变 + 历轮负例仍成立 — ✔

- **`set` 零行为改动**：r1/r2 用例 ①–⑧（`test_debt0067_0068_write_side.py` + `test_agate_md_field_set.py`，含 BDD-17 纯并集契约、BDD-18 追加拒绝）**全绿**——本评审实跑 **51 passed**（r2 为 49，r3 +⑨ 2 条）。
- **负例（实测复核）**：
  - 未知 key `set no_such_key` → rc=1「非法 key」（仍然拒）；
  - 非豁免字段深 4 `coupling_checklist`（P2）→ `check-frontmatter.py` rc=1「嵌套深度超过 3 层」；
  - `dispatch_plan` 含 `batches[].output` 深 4 → rc=0（豁免仍单键生效）。

## 4. DEBT0072 登记是否如实 — 如实 ✔（复现一致）

`agate-workspace/debt/tech-debt.md` 新增 DEBT0072（`status: open`, `task_id: DEBT0067+DEBT0068`）。逐条复现：
| 债务声称 | 复现命令 | 结果 |
|---|---|---|
| `append pass` 无守卫 | `append pass text=probe` | `OK: pass 追加一项 {'text': 'probe'}` ✔（与条目逐字一致）|
| 对照：`append regression_pass` 被拒 | `append regression_pass text=x` | `ERROR: 'regression_pass' 不在本文件契约字段中` ✔ |
| `pass`/`fail` 是系统字段、`--list` 已标「由脚本产出」 | `--list` P6 | 标 `（由脚本/角色产出，不可 set）` ✔ |
| 面未穷尽 | `append blocker_count`（P7，writer:system） | `OK: blocker_count 追加一项 {'text': 'x'}` ⇒ **同类缺口确延伸到 P7 契约系统字段**，与条目 impact②「面未穷尽」吻合 ✔ |

⇒ 复现命令、影响面、修法建议（append 复用 `_key_capability`/`_evidence_fields` 判据）**均如实**，无夸大/遗漏。**按派发指令不判 MISALIGNED**（属另立债务）。

## 5. A1–A8 其余项（复核结论）

- **A1 文档→脚本**：P2 卡 `:147` 深度豁免段 ↔ `agate-frontmatter-check.py`（`_DEPTH_EXEMPT_FIELDS`）一致；P8 卡 `delivery`/`debt_check` ↔ `phases.yaml:174` 一致。ALIGNED。
- **A2 脚本→文档**：`design-md-field-set.md` §2.3/§4/§5.3/§6.1 已同步，且 r3 新增 §5.3 注「展示由实际守卫派生、不得手维」。ALIGNED。
- **A3 连锁/反向传播**：r3 只动展示 + 抽函数，无新文件/新契约；`task_fields` 消费方（`agate-md-field-set.py` + `check-structure-consistency.py:421`）不受影响。ALIGNED。
- **A4 测试**：r3 +⑨（P1/P6 参数化，逐键对拍）；实跑 51 passed（+ 变异验证判别力）。ALIGNED。
- **A4b 既有转红 / 夹具**：**经实测无既有用例转红**；夹具无需更新。ALIGNED（空清单）。
- **A5 下游/传播**：CHANGELOG 两条在（DEBT0067 `:51` / DEBT0068 `:59`）；无破坏性变更。ALIGNED。
- **A6 锚点表**：未新增 `agate/scripts/` 文件；实跑 `check-protocol-consistency.py` **0 ERROR**。ALIGNED。
- **A7 设计原则（ADR-014）**：能力标注**由实际守卫单源派生**（`_key_capability`），非手维；与 ADR-014「判据单源」一致，且 r3 修因正是 r2 手维名单的漂移。ALIGNED。
- **A8 声称-命令绑定**：P1/P6 展示、`set`/`append` 行为、consistency 0 ERROR、ruff All checks passed 均本评审复跑并给出命令；唯一未精确复现者 = 主 Agent 的「换回 r2 ⇒ 2 failed」**红态**（r2 代码未入 git），已以**变异法**独立证判别力替代。ALIGNED。

---

## 评审边界（只读纪律）

- 全程**只读**：未执行写仓命令；未编辑被评审文件。
- 探针仅在 `/tmp/opencode` 一次性副本（含变异树 `mut-agate`）内「创建→操作→清理」；均带 **`AGATE_ROOT=<工作树>/agate`**（另以隔离 HOME 双保险）。
- 规避「rc=0 ≠ 通过」：深度判定用 `check-frontmatter.py` 薄壳读 exit code 并核 stdout 文案。
- 未在 `agate-workspace/tasks/**` 建任何目录。
