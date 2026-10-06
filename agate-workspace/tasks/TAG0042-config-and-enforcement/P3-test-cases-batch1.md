---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: test-designer
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — batch1-phase-semantics（统一 phase 语义）

> 上游：`P1-requirements.md`（BDD-1 / BDD-2，Batch 1）+ `P2-design.md` §1.1（M1/M2/M3）、§6.1b
> （batch1 `output`）+ `P3-dispatch-context-test-designer.md`。
> 本批为 TDD 红灯批：测试**先于实现**，当前全部红灯（红灯原因 = 被测行为未改，B 类）。
> batch1 是 tracer bullet（模式 5 串行链首批），只覆盖 BDD-1 / BDD-2，不碰 batch2-6。

> **`test_code_dir`**：`agate/tests/unit/`（声明于 frontmatter，单一来源）。

## 1. 测试文件

| 文件 | 说明 |
|---|---|
| `agate/tests/unit/test_tag0042_batch1_phase_semantics.py` | batch1 的 BDD-1 / BDD-2 红灯测试（新建） |

> 既有相关测试（`test_agate_next_card.py` / `test_tag0027_b1_agate_next_cli.py` /
> `test_check_state_transition.py`）**不复用、不改动**——它们是 P4 改 `agate-next` 后需同步的对象；
> 本批只新增 BDD-1/BDD-2 的红灯测试。

## 2. BDD → 测试用例映射（1:1）

### BDD-1: agate-next 推进时不预写下一阶段 (Batch 1)

> Given 一个 `.state.yaml` 的 `phase: Pn`，且 `.state.yaml` **未被暂存**
> When 运行 `agate-next` 且 `check-gate.py Pn` 返回通过码（∈ `gate_pass_exit`）
> Then `agate-next` **不把** `Pn+1` 写入 `.state.yaml` 的 `phase` 字段，且 **不** `git add` `.state.yaml`

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B1-01 | `test_bdd_1_advance_does_not_prewrite_next_phase_into_state_yaml` | `phase` 不得被改为 `Pn+1`（P5→P6）；须保持 `P5` | 现行为 `_advance` 把 `phase` 写成 next（实测 `phase == "P6"`，`assert 'P6' != 'P6'` 失败）= 行为未改 |
| TC-B1-02 | `test_bdd_1_advance_does_not_git_add_state_yaml` | 推进后 `git diff --cached --name-only` 不含 `.state.yaml` | 现行为 `_advance` 调 `_git(["add", <task>/.state.yaml])`（实测暂存区含 `task/.state.yaml`）= 行为未改 |

### BDD-2: 不可绕开路径上的 phase 语义与卡片表述一致 (Batch 1)

> Given 批 1 落地后
> When 对 `agate-next.py` 与 `phase-cards/` 的 phase 语义表述做一致性扫描
> Then 全仓不再存在「agate-next 预写下一阶段」的行为代码，且卡片的「phase = 本 commit 产出阶段」
>      表述与 `agate-next` 实际行为一致（无相悖描述）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B2-01 | `test_bdd_2_agate_next_source_has_no_prewrite_behavior` | `agate-next._advance` 函数体不再含 `state["phase"] = target` | 该赋值仍在 `_advance` 中（实测命中）= 行为代码未改 |
| TC-B2-02 | `test_bdd_2_phase_cards_align_with_phase_is_current_commit_output` | ① P2/P8 卡片含「phase 保持/不要提前写」「本 commit 产出阶段」表述，② 且 `agate-next` 源码不再含 `state["phase"] = target`（卡片表述与行为一致） | 表述①已存在，但行为②仍预写 ⇒ 卡片说「不要提前写」、行为却提前写，二者矛盾（实测 `state["phase"] = target` 仍在） |
| TC-B2-03 | `test_bdd_2_upgrading_documents_agate_next_no_prewrite` | `UPGRADING.md` 记载「agate-next … 不预写」的批 1 行为变更 | 现文仍写「阶段卡片 phase 语义（文档，无强制）」，未记批 1 行为变更（实测 `re.search` 返回 None） |
| TC-B2-04 | `test_bdd_2_no_prewrite_behavior_code_anywhere_in_scripts` | `agate/scripts/*.py` 全仓不再存在 `state["phase"] = target` 预写实现 | `agate-next.py` 仍命中（实测 `offenders == ['agate-next.py']`）= 行为代码未改 |

**BDD 覆盖核对**：BDD-1 → 2 用例（TC-B1-01/02）；BDD-2 → 4 用例（TC-B2-01..04）。
6 条用例全部引用对应 BDD 编号，可追溯到 P1 的验收条件。

## 3. 红灯基线（自跑记录）

```
python3 -m pytest agate/tests/unit/test_tag0042_batch1_phase_semantics.py -v
→ 6 failed in 0.35s
```

6 条全部为 **AssertionError**（行为未改）——**非 SyntaxError、非第三方 import 失败**（A 类），
亦非「断言与测试数据矛盾」：每条失败消息直指 `agate-next` 的现有预写/`git add` 行为仍存在，
属 check-tdd-red 认可的 **B 类真红灯**。

| 用例 | 红灯类型 |
|---|---|
| TC-B1-01 | AssertionError（phase 被预写为 P6） |
| TC-B1-02 | AssertionError（暂存区含 .state.yaml） |
| TC-B2-01 | AssertionError（_advance 仍含 `state["phase"] = target`） |
| TC-B2-02 | AssertionError（卡片表述与行为相悖） |
| TC-B2-03 | AssertionError（UPGRADING 未记载行为变更） |
| TC-B2-04 | AssertionError（agate/scripts/ 仍存在预写实现） |

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/test_tag0042_batch1_phase_semantics.py
→ exit 0（0 命中）
```

测试平台无关实现要点：
- 用 `tmp_path` / `task_dir` / `git_repo` fixtures；`run_cli(python_exe, ...)`（不裸 `python3`）；
- 全文本 I/O 显式 `encoding="utf-8"`；
- 需要「系统临时目录」字面量时**运行时拼接**（`_TMP = "/" + "tmp"`），不写字面量；
- 不写仓库内已提交文件（全在 `tmp_path` / `git_repo` 临时目录内）。

## 5. 与实现对象的关系（供 P4）

- **被测行为落点**：`agate/scripts/agate-next.py::_advance()`（现约 L198-210）——去掉 `state["phase"]=target`
  预写 + `_git(["add", ...state.yaml])`，保留 `append_event state_transition` 证据，改为**输出「下一阶段建议」**。
- **卡片/文档面**：`agate/phase-cards/P2-design.md`、`agate/phase-cards/P8-release.md`、`agate/UPGRADING.md`
  （P2-design §1.1 M1/M2/M3；batch1 `output` 见 §6.1b）。
- **P4 回归注意**：既有 `test_check_state_transition.py` / `test_tag0027_b1_agate_next_cli.py` 中
  「随推进查 gate 后状态」类断言可能在去预写后需同步（本批不改它们，P4 处理）。

## 6. 边界与不做

- 本批**只写测试**，不写实现（实现是 P4）。
- **只覆盖 batch1 的 BDD-1/BDD-2**，不碰 batch2-6。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本）——所有断言均在 `tmp_path`/`git_repo` 内。
