---
type: review
status: approved
phase: P4
task_id: TAG0050
parent: P4-implementation-G3.md
trace_id: TAG0050-P4-20261008
agent: review
---

# P4 实现复审（聚焦 · 第 2 轮整改后）— TAG0050 批 G3（D + E + F）

> 角色：`review`（偏执 Staff Engineer）。对象：G3 **fix2** 整改，HEAD `b746d07d`，
> 分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 范围：**只核** `P4-review-G3.md` 的 **BLOCKER-1 + MINOR-2/3/4** 是否闭合 + 是否引入新阻断；
> 不重开全量（批 D/E/F 其余项首轮已判）。
> 只读纪律：**未编辑任何被评审文件**；独立复现仅在**仓外可丢弃副本**
> `/tmp/opencode/g3rerev/`（手工构造非 legacy 任务）与 `/tmp/opencode/g3rerev2/`（回退实现跑新用例）上进行；
> 真实仓库仅执行只读命令（`read`/`grep`/`git status`/`check-protocol-consistency.py`/`sha256`/`count-tests`）。
> 环境隔离：`[PROD_NOT_TOUCHED]`（全程未接触生产环境；peekview 未打开）。

## 结论

**approved** — BLOCKER-1 已闭合（**独立复现验证**：非 legacy 声明 `criteria` 且 `status: passed` → **exit 0**；
缺 `criteria` → exit 1）；MINOR-2/3/4 均已闭合且**新用例具改前红判别力**；**未发现新阻断**。

| # | 严重度 | 位置 | 复审 |
|---|--------|------|------|
| 1 | **BLOCKER** | `agate_common.py:601-608` + `check-judge-verdict.py:517-559` | ✅ **ALIGNED**（透传 criteria + 校验后移；独立 exit 0/exit 1 复现） |
| 2 | MINOR | `check-gate.py:1482-1556`（D8） | ✅ **ALIGNED**（读 `read_vision_tri_state` 二选一 + 结构化截图判定） |
| 3 | MINOR | `check-gate.py:1567-1629`（D7） | ✅ **ALIGNED**（双向 + 形态 + 多 JSON 合并；面不窄于被取代者） |
| 4 | MINOR | `check-gate.py:1885-1902`（`gate_p7`） | ✅ **ALIGNED**（`verdict`/`basis` 枚举校验） |

---

## BLOCKER-1（独立验证，关键）

### 实现落点（只读核对）
- `agate_common.read_judge_verdict()` 返回值现含 `"criteria": data.get("criteria")`（`agate_common.py:601-608`）。
- `check-judge-verdict.py` 把 `criteria_total`/`criteria_passed`/`verdict_evidence` 的强校验（`:551-559`）
  **移到 `_non_legacy` 判定与现算（`:522-547`）之后**；非 legacy 先由 `criteria` 现算三值再校验，legacy 保留旧口径。

### 独立复现（仓外副本 `/tmp/opencode/g3rerev/`，**手工构造任务**，非跑其用例）
副本为 `cp -r agate /tmp/opencode/g3rerev/agate`（删 `tests/` 隔离）。构造非 legacy 任务：账本首行
`task_created` `contract_level=1`、P1 一条 `#### BDD-1:`、`P6-evidence/e1.json`、`P6.5-dispatch-context-judge.md`、
`P6.5-judge-verdict.md`。

**① 声明 `criteria` 且 `status: passed` → exit 0（P6→P7 不再死锁）**
```
$ AGATE_ROOT=/tmp/opencode/g3rerev/agate python3 agate/scripts/check-judge-verdict.py /tmp/opencode/g3rerev/task_pass
GATE JUDGE-VERDICT: 校验通过（status=passed, criteria 1/1），judge_verdict 事件已记账
EXIT=0
```

**② 缺 `criteria` → exit 1**
```
$ AGATE_ROOT=/tmp/opencode/g3rerev/agate python3 agate/scripts/check-judge-verdict.py /tmp/opencode/g3rerev/task_missing
GATE JUDGE-VERDICT: 非 legacy 任务须在 frontmatter 声明 criteria（设计 §5.2）
EXIT=1
```

**③ 判别力反证**：在副本上删除 `read_judge_verdict` 的 `"criteria"` 透传（模拟改前），再跑 ① → **转红**：
```
$ （副本内删除 criteria 透传后）python3 agate/scripts/check-judge-verdict.py .../task_pass
GATE JUDGE-VERDICT: 非 legacy 任务须在 frontmatter 声明 criteria（设计 §5.2）
EXIT=1
```
⇒ 证明修复**真正改变了判定**，非偶然绿灯。

### 文档承诺与实现一致
- `UPGRADING.md:422-423`：「**P6.5** 读结构化 `criteria: [{bdd, verdict, evidence}]`（`criteria_total`/
  `criteria_passed`/`verdict_evidence` 现算）」——与实现（`len(criteria)` / PASS 计数 / 证据扁平化）**一致**。
- `CHANGELOG.md:18-19` 同款承诺（并标注 BLOCKER-1 修复）——**一致**。

---

## MINOR-2（D8 弱化）— ALIGNED

实现（`check-gate.py:1482-1556`）：`vision_state = read_vision_tri_state(P1)`；`is_gap = (vision_state=="GAP")`；
截图条目（`_is_screenshot_ref`：按 `[\\/]+` 切分、精确比较目录段名 `screenshots`）在 `GAP` 时须 `manual_review`、
否则须 `vision`。

判别力（副本内回退为旧弱化「vision 或 manual_review 二选一 + `"screenshots/" in refs_str` 子串」后跑新用例）：
```
FAILED tests/integration/test_tag0050_evidence.py::test_minor2_d8_gap_requires_manual_review
FAILED tests/integration/test_tag0050_evidence.py::test_minor2_d8_screenshot_detection_is_structural
2 failed, 1 passed, 17 deselected
```
⇒ GAP 分支与结构化判定两条**改前红**；`requires_vision_when_available` 为前后均通过的基础用例。
夹具演进（`test_pre_commit_hook.py` 由 `manual_review` 改 `vision`）经核：该任务 P1 无 `capability_requirements`
视觉条目（`read_vision_tri_state→None` ⇒ 非 GAP ⇒ 须 `vision`）——**契约驱动的夹具修正**，非放水。

## MINOR-3（D7 弱化）— ALIGNED

实现（`check-gate.py:1567-1629`）四类判据：① 正向（results PASS vs evidence FAIL）；② 反向；
③ 形态（`results`/`bdd_results` 非列表、元素非映射 → ERROR）；④ 多 JSON 合并冲突。
**面不窄于被取代者**：被取代的 `agate-evidence-consistency.py:27-41` 仅做**单向**且对非列表/非映射元素
静默 `isinstance` 跳过 ⇒ 新 D7 严格更宽（含反向/形态/冲突）。

判别力（副本内回退为旧单向 D7 后跑新用例）：
```
FAILED tests/integration/test_tag0050_evidence.py::test_minor3_d7_json_shape_non_list_errors
FAILED tests/integration/test_tag0050_evidence.py::test_minor3_d7_json_shape_non_dict_element_errors
2 failed, 2 passed, 16 deselected
```
⇒ 形态两条**改前红**。多 JSON 冲突与反向两条在改前亦通过（反向被 D2「全 PASS」先行拦截、多 JSON 冲突被旧正向覆盖）——
属纵深防御用例，非判别力缺口。

## MINOR-4（`gate_p7` 取值域）— ALIGNED

实现（`check-gate.py:1885-1902`）：`verdict ∈ {accepted,rejected,followup}`、`basis ∈ {in_bdd,out_of_scope}` ∪
`followup:DEBT0*[0-9]+`，越界 → ERROR；仅 `_gate_p7_structured`（非 legacy）分支，**legacy 不变**（`gate_p7:1991`）。

判别力（副本内删除两处枚举校验后跑新用例）：
```
FAILED tests/unit/test_tag0050_declarations.py::test_minor4_verdict_enum_out_of_range_errors
FAILED tests/unit/test_tag0050_declarations.py::test_minor4_basis_enum_out_of_range_errors
2 failed, 11 deselected
```
⇒ 两条**改前红**。

---

## 新引入问题核查

- **无新阻断**。逐核：
  - legacy §8 承诺不变：三处修复均门控于非 legacy（`_non_legacy` / `task_level(...) is not None`）。
  - 系统字段语义一致：非 legacy 时 `criteria_total`/`criteria_passed`/`verdict_evidence` 由 `criteria` 现算，
    即使 agent 同时手写三值也被覆盖（符合设计）。
  - 快照/一致性：`level-1.yaml` LF 归一 sha256 `6ace03c9…` == `LEVELS.yaml` 登记值；
    `check-protocol-consistency.py` → **exit 0 / 0 ERROR**；`count-tests.sh` → **2866**（与 P3 登记 +16 一致）。
  - 目标 5 文件（`test_tag0050_{evidence,declarations,proxy_judgment,cross_batch,fitness}` + `test_pre_commit_hook`）
    副本跑测 → **107 passed**（3 条 `cross_batch` 失败系副本未含仓库根 `docs/`/`CHANGELOG.md` 的环境假象，非缺陷）。
- **非阻断观察**（供 P5/P6 知悉，不构成打回）：
  1. **D7 形态判据较严**：`P6-evidence/**/*.json` 中任何含顶层 `results`/`bdd_results` 键但值非列表的
     JSON 均 ERROR。若某任务在证据目录放入带 `results` 键（如 API 分页）的合法 JSON，会触发硬失败。
     此为「面不窄于被取代者」的**有意加宽**（旧脚本静默跳过正是被修的弱点），已记入 UPGRADING；留作观察。
  2. consistency WARNING 数 412（实现者记 410）——差 2 条来自本次**未跟踪**的评审/派发文件，非 ERROR。

---

## 附：只读核验命令与结果（真实仓库）
```
$ python3 agate/scripts/check-protocol-consistency.py      → 0 ERROR / 412 WARNING（exit 0）
$ python3 -c "sha256(LF 归一 level-1.yaml)"                → 6ace03c98a074a623e33a4d7127e1f782b4d001df41fe6b0741350185183fc96
$ grep 6ace03c9… agate/rules/task-data/LEVELS.yaml          → 命中（登记一致）
$ bash agate/tests/scripts/count-tests.sh                  → 2866（≥749）
```

## 环境隔离
`[PROD_NOT_TOUCHED]` 全程只读真实仓库（`read`/`grep`/`git status`/`check-protocol-consistency.py`/`sha256`/
`count-tests`）；全部变异与复现实验仅在仓外一次性副本 `/tmp/opencode/g3rerev/`、`/tmp/opencode/g3rerev2/`
（可丢弃）上进行。未编辑任何被评审文件，未接触生产环境。
