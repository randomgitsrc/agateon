---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: hotfix DEBT0072——`agate-md-field-set.py` 列表写入族入口 `_require_list_field` 复用 `_key_capability=="script"` 加守卫，使 append/upsert/remove 对系统/证据字段一律拒（单源 ADR-014）
files_changed:
  - agate/scripts/agate-md-field-set.py
  - agate/tests/unit/test_debt0072_append_guard.py
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
---

# 协议-脚本对齐审查（HOTFIX-DEBT0072）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054） | ALIGNED（**经实测无既有用例转红**；无夹具需更新） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（逐条附命令；见下） |

**MISALIGNED 计数：0。** 结论：`approved`。

**对 dispatch「重点核 1」的结论——范围是否被写窄：未写窄。** `CHANGELOG.md:71-72` 与 `tech-debt.md` 的 `closure_note`（3133）都**显式**写明范围为**列表写入族 append/upsert/remove**，不是只写 `append`。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/scripts/agate-md-field-set.py:17-19`，脚本自述/docstring）：
> 证据字段（BDD-9）/仅登记-需 append 字段（BDD-18）一期明确拒绝
> **set** 写入；DEBT0072 起「由脚本/角色产出」字段（= `_key_capability == "script"`）对
> **append/upsert/remove** 亦同判据拒绝（此前 append 侧无守卫，可把 `pass`/`fail` 等系统字段写坏）。

**脚本实现**（`agate-md-field-set.py:747-762` 新守卫 + `765-783` 调用点）：
> `_script_field_error` → `if _key_capability(file_path, key, get_mod) != "script": return None`；
> `_require_list_field` 在 spec 解析成功后 `err = _script_field_error(file_path, key, _fm_get()); if err: stderr.write(err); return None`。

**结论**：ALIGNED。docstring 明确「列表写入族（append/upsert/remove）共享该守卫」，与实测一致（见 A5/A8 实证：`append`/`upsert`/`remove` 对 `pass` 均 rc=1）。

### A2: 脚本→文档对齐

变更的脚本逻辑 = 「系统/证据字段在列表写入族一律拒」。需同步的协议文档面：
- `docs/design-notes/design-md-field-set.md`：**无** append/upsert/remove 子命令语义描述（`grep -n "append\|upsert\|remove"` 仅命中 166/227 两处，均是关于 `--list` 展示派生与 `set` 白名单，不涉 append 行为），**无需同步**。
- `docs/design-notes/design-tag0050-task-data-contract.md:406-423`（§3.4）已**泛化**声明「**系统字段拒写**：拒写时说明这个值从哪里来」——覆盖全部 7 操作；本改动是把该声明在 `append` 侧**补齐**，与该文档一致，**无需同步**。
- `CHANGELOG.md` 已更新（见 A5）。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**A3a（连锁）**：无其它协议文件与本改动直接耦合（守卫复用既有 `_key_capability`，未新增判据、未改契约/`SCHEMAS`/`phases.yaml`）。CHECK 16（任务数据契约快照冻结）PASS 佐证契约文件未动。

**A3b（反向传播——「谁该知道『系统字段不可 append』」）**：
| 应被影响面 | 实况 | 结论 |
|---|---|---|
| `design-tag0050-task-data-contract.md` §3.4「系统字段拒写」 | 已泛化覆盖 7 操作；本改动与之同向 | 无需动 |
| `design-md-field-set.md` §5.10（证据字段拒绝端） | 只描述 `set` 侧，未描述 append；本改动未改变其陈述真值 | 无需动 |
| 角色文件（`verifier.md` 236/249-250 等） | 只教 `pass`/`fail` 经 **frontmatter/set** 写，无「append 系统字段」指令 | 无需动 |
| `dispatch-context.md` 模板 | 只教 `md-field-set <key> <value>`（= set）用法 | 无需动 |
| 仓库内既有 `append pass` 等用法 | `grep` 仅命中债务/CHANGELOG 自身的**叙述**（tech-debt.md:3090/3109、CHANGELOG:71），无任何脚本/模板**执行**该用法 | 无历史调用被打断 |

**结论**：ALIGNED（反向传播面为空集，已逐一核验）。

### A4: 测试覆盖

新增 `agate/tests/unit/test_debt0072_append_guard.py`（4 函数 / 10 用例参数化）：
- ①`test_..._script_fields_append_rejected`：逐 basename 对「由脚本/角色产出」字段 append 须 rc≠0 + 错误信息含字段名 + 不落盘。
- ②`test_..._list_script_keys_set_and_append_both_rejected`：**从真实 `--list` 输出**解析出标为「由脚本/角色产出」的键，set 与 append **均**须被拒（= 债务闭合判据 ②，直接对展示面）。
- ③`test_..._script_universe_matches_single_source`：白盒断言静态表 ≡ `_key_capability(...) == "script"`（防表与判据漂移）。
- ④`test_..._legit_append_targets_still_succeed`：`scope_resolved`/`need_confirm`/`results` append 仍成功（防过宽）。

**判别力实证**（改前行为，见 A8 命令）：改前 `append pass/fail/blocker_count/deviation_critical_count` 与 `upsert pass` 均 rc=0 ⇒ 用例 ①②的 `returncode != 0` 断言改前必红 ⇒ 具判别力。

**实跑输出**：
- 新用例（本审查独立跑）：`python3 -m pytest agate/tests/unit/test_debt0072_append_guard.py -q` → `10 passed in 3.78s`。
- 主 Agent 全量（派发指引给定，本审查按约束未重跑全量）：`pytest -q -n auto` → `1 failed / 2993 passed / 2 skipped`，唯一红 = 本机环境项 `test_bdd_43`（`debug agent` 子命令本机实为 `debug agents`），与本改动无关。

**结论**：ALIGNED。

### A4b: 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054）

本审查独立实跑既有相关面（bounded，非全量）：
- `test_agate_md_field_set.py` + `test_debt0067_0068_write_side.py` + `test_tag0050_write_tools.py` + `test_tag0050_declarations.py` + `integration/test_tag0050_prod_touched.py` + `integration/test_tag0050_evidence.py` → **100 passed**。
- `test_tag0050_obligations.py` + `test_tag0050_obligation_behavior.py` + `test_protocol_mechanism_anchors.py` + `test_check_gate.py` + `test_check_p6_evidence.py` + `test_check_p6_provenance.py` → **384 passed**。

**转红清单：空**（经实测，**无**既有用例转红——改动只新增拒绝分支，且不改 `_key_capability` 输出，展示/能力标签测试不受影响）。
**夹具更新清单：空**（新用例复用既有 conftest 的 `agate_scripts`/`python_exe`/`run_cli`，无新增/改动夹具）。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播

- **CHANGELOG**：`CHANGELOG.md:70-79`（`[Unreleased]`→修复）新增 DEBT0072 条目，**完整描述范围**：明写「`append`（及同族 `upsert`/`remove`）在列表写入唯一入口复用 `set` 的同一判据」。**未写窄**（dispatch 重点核 1 答复）。
- **行为收紧 + 面向既有合法项目的破坏性影响**：唯一新增拦截面 = 契约 `writer: system` 列表字段 {`pass`,`fail`,`blocker_count`,`deviation_critical_count`}——它们**本就不该**由 agent 经 append 写入（`set` 早已拒），且仓库内无任何脚本/模板执行 `append pass` 等（A3b 已 grep 实证）⇒ **现实性风险低**，无既有合法用法被打破。
- 未触碰 gate/账本判定（`check-gate.py` 未改；`check-debt.py` rc=0）。

**结论**：ALIGNED。

### A6: 锚点表覆盖

未新增 `agate/scripts/` 下文件（只改既有 `agate-md-field-set.py`；新增的是 `agate/tests/unit/` 测试文件，不在 CHECK 9/10 的脚本登记面）。实跑 `check-protocol-consistency.py` → **CHECK 9 PASS**、CHECK 10 仅既有冻结 WARNING，**无需更新锚点表**。

**结论**：ALIGNED。

### A7: 设计原则一致性

**ADR-014（判据单一权威源）**：守卫**复用** `_key_capability(...) == "script"`（未写第二份判据）；`_key_capability` 本身复用 `_is_script_field`（契约 `writer:system`）∪ `_evidence_fields`（get 侧常量）。展示面（`--list`）、`set` 侧、`append` 侧**同源**，符合 ADR-014 ①（判据单源）。与 ADR-014 ③（形态判据不越界做语义判断）一致——守卫只判"该字段是否属 script 能力面"，不做内容语义判断。

**结论**：ALIGNED（A7 无 MISALIGNED 态，此处为 ALIGNED）。

### A8: 声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| 改前 `append pass`/`append fail` 可写入（`OK: pass 追加一项 …`） | `/tmp/opencode` 一次性副本跑 **HEAD 版**脚本：`AGATE_ROOT=<副本> FILE=<副本>/P6-acceptance.md python3 <副本>/agate-md-field-set.py append pass text=probe`（+fail） | 实测 rc=0（CHANGELOG:71 声称成立） |
| 新用例 10 passed | `python3 -m pytest agate/tests/unit/test_debt0072_append_guard.py -q` | `10 passed in 3.78s` |
| 全量 2993 passed / 1 failed / 2 skipped | 主 Agent `pytest -q -n auto`（本审查按约束未重跑全量；bounded 独立跑 100+384 passed 佐证无相关回归） | 采信主 Agent 实跑 |
| 「面穷尽」 | 独立扫 `SCHEMAS` 四 basename + 契约 `files` 节（level-1/2）+ `agate-md-field-get` 的 `NO_FALLBACK_INT_FIELDS`/`NO_FALLBACK_BOOL_FIELDS`/`JSON_FIELDS` + `check-gate.py` 现算字段，并对每个候选字段逐一 append 实测（副本） | 无遗漏：**无一「由脚本/证据字段」可 append**（见「核查表」） |
| 「未过宽」 | 副本实测 `append scope_resolved`/`append need_confirm`/`append results` | 均 rc=0，合法目标不受影响 |
| `check-protocol-consistency.py` 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | 0 ERROR（433 冻结 WARNING） |
| `check-debt.py` rc=0，open 3→2 | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md`；`grep -c "^status: open"` | rc=0；open=2 |
| ruff 全过 | `ruff check agate/scripts/agate-md-field-set.py agate/tests/unit/test_debt0072_append_guard.py` | All checks passed |

**无不可复核声称需删除。** 唯一**精化建议（非阻塞）**：CHANGELOG/`closure_note` 的「面穷尽……P6 `pass`/`fail`/`regression_pass`，P7 `blocker_count`/…/`code_map_*`」清单中，**真正由本次新守卫新覆盖的只有 4 个**（`pass`/`fail`/`blocker_count`/`deviation_critical_count`——契约 `writer:system` 字段）；其余（`regression_pass`、`deviation_count`、`design_gap_count`、`code_map_*` 等）改前**即**被「不在本文件契约字段中」分支拒。清单作为「已核验的脚本字段全集、全部被拒」是**真**的，但读者易误读为「新守卫覆盖了全部」。属表述精化，不构成 A2/A5 不一致。

---

## 「面穷尽」独立核查表（dispatch 重点核 2）

来源逐项扫描 + 副本实测 append 结果：

| 来源 | 字段 | append 实测 | 归类 |
|---|---|---|---|
| 契约 `files`（level-1.yaml:94-95） | `pass`, `fail`（P6，writer:system） | 改前 rc=0 → **改后 rc=1**（新守卫） | 新覆盖 |
| 契约 `files`（level-1.yaml:104-106） | `blocker_count`, `deviation_critical_count`（P7，writer:system） | 改前 rc=0 → **改后 rc=1**（新守卫） | 新覆盖 |
| `NO_FALLBACK_INT_FIELDS` | `deviation_count`,`design_gap_count`,`design_gap_reviewed_count`,`code_map_new_files_count`,`code_map_reviewed_count`（P7） | 改前后均 rc=1（**契约外**分支） | 既有拒绝 |
| `NO_FALLBACK_BOOL_FIELDS`/证据表 | `regression_pass` | 改前后均 rc=1（契约外） | 既有拒绝 |
| `NO_FALLBACK_BOOL_FIELDS` | `feedback_ready`（retrospective） | 契约外 → 拒 | 既有拒绝 |
| `JSON_FIELDS` | `dispatch_plan`（P2） | 改前后均 rc=1（契约外） | 既有拒绝 |
| P6.5 系统字段（design-tag0050:532；phases.yaml task_fields） | `criteria_total`,`criteria_passed`,`verdict_evidence` | append/upsert/remove 改前后均 rc=1（契约外） | 既有拒绝（append 面已拒） |
| `SCHEMAS` basenames | P1-requirements.md / P2-design.md（无证据字段）；P6/P7 同上 | — | 已覆盖 |

**结论：面穷尽成立（就 `append` 侧而言）。** 全部候选「由脚本/角色产出」字段**无一可 append**。精确边界：**本次新守卫新覆盖恰为 4 个契约 `writer: system` 列表字段** {`pass`,`fail`,`blocker_count`,`deviation_critical_count`}；其余候选字段在改前**已**被 `_require_list_field` 的「不在本文件契约字段中」分支拒。**无被漏掉的字段/来源。**

**附带观察（越本债范围，供参考，不构成本次 MISALIGNED）**：`set criteria_passed 9` 实测 rc=0（`P6.5-judge-verdict.md`）——`criteria_*` 在 `design-tag0050-task-data-contract.md:532` 被称为系统字段，但**不在**契约 `files` 节也不在证据字段表，故 `--list` 标为「可 set」且 `set` 可写。这是 **DEBT0067（展示↔真实行为）域**的既有缺口，与 DEBT0072（**只覆盖 append 面**，见 tech-debt.md:3101-3102）无涉，本改动**未触碰 `set` 路径**故未加剧。

---

## 只读纪律声明

本审查为只读活动（RM-AG0081）。写类探针（脚本子命令）**全部**在 `/tmp/opencode` 一次性副本内执行，"创建→操作→清理"在**同一次 bash 调用**内完成；未对真实仓库运行任何写类工具，未执行 `git add/commit/restore/reset/clean/stash`；未在 `agate-workspace/tasks/**` 下建目录。每次探针后 `git status --porcelain` 核验真实仓库仅剩被评审的 4 个文件（M/M/M/??），无额外改动。
