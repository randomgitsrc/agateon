---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: test-designer
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — batch4-gate-layer（关卡层分级 + P8 交付收尾 + preset 等价物）

> 上游：`P1-requirements.md`（BDD-14 / BDD-15 / BDD-21）
> + `P2-design.md` §1.1（M11/M12/M19）、§4.3（关卡层分级 + P8 交付收尾 + 删发版逻辑顺序）、
> §4.5（preset 与发版痕迹消费方）、§6.1b（batch4 `tests_filter` / `output`）、
> §11（DESIGN_GAP 预留）、§12 第 4 条（实现完成的标志）
> + `P0-brief.md` §二 批 4 + `P0-batch0-record.md`（批 4 前提与风险 R3）
> + `P3-dispatch-context-test-designer-batch4.md`。
> 本批为 TDD 红灯批：测试**先于实现**，当前 8 条全部红灯（红灯原因 = 被测结构/行为未实现，B 类）。
> batch4 是模式 5 串行链的第 4 批（依赖 batch3），只覆盖关卡层分级 / P8 交付收尾 / preset 等价物，
> 不碰 batch5-6。

> **`test_code_dir`**：`agate/tests/unit/`（声明于 frontmatter，单一来源）。

## 1. 测试文件

| 文件 | 说明 |
|---|---|
| `agate/tests/unit/test_gate_layer.py` | BDD-14（关卡层按提交类型分级，转换表含 `paused_from`）+ BDD-21（preset 等价物先就位 + 迁移提示）红灯测试（新建） |
| `agate/tests/unit/test_check_p8_delivery.py` | BDD-15（P8 交付收尾且 `delivery` 必须声明）红灯测试（新建） |

> 既有相关测试（`test_check_gate.py` 的 G8 系列、`test_check_structure_consistency.py`、
> `test_check_yaml_schema.py`）**不复用、不改动**——它们是 P4 改 `check-gate.py` / `phases.yaml` /
> `phase-cards/P8-release.md` 后需同步的对象；本批只新增 BDD-14/15/21 的红灯测试。
> `test_check_p8_delivery.py` 与既有 `test_check_gate.py` 的 G8 系列互补：后者测 gate_p8 的既有
> `bump_type` / `debt_check` / version / CHANGELOG / roadmap 分支，前者测 **BDD-15 新增的 `delivery`
> 声明拦截**。

## 2. BDD → 测试用例映射（1:1）

### BDD-14: 关卡层按提交类型分级 (Batch 4)

> Given 一次提交属于某提交类型（如纯代码 / 纯文档 / 发版）
> When 关卡层判定该提交
> Then 按**提交类型**选择对应关卡集合（转换表可查），不同类型走不同关卡，且转换表含 `paused_from`

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B14-01 | `test_bdd_14_phases_yaml_selects_gate_sets_by_commit_type` | phases.yaml 存在「提交类型 → phase 集合」容器（≥3 类型、≥2 集合不同）；且既有 `gate_pass_exit` 语义不变 | phases.yaml 无该分级结构 ⇒ 结构未实现 |
| TC-B14-02 | `test_bdd_14_transition_table_includes_paused_from` | phases.yaml 字面含 `paused_from`（转换表） | 全仓 `paused_from` 零命中 ⇒ 结构未实现 |

> **[DESIGN_GAP]（TC-B14-01）**：P2-design §11 明确「批 4 的关卡层转换表矩体可能在实现中遇歧义，
> P4 应标 `[DESIGN_GAP]`」。故本断言**键名无关**——用递归结构扫描识别「同一容器下 ≥3 个
> phase-id 列表值」，不假设映射容器名/键名/提交类型标识。P4 须按 BDD-14 落定契约；若采用不同
> 表示法（如按 gate 名而非 phase id、或映射到集合类型），在 P4 标 `[DESIGN_GAP]` 并对齐本断言。
> TC-B14-02 断言的 `paused_from` 是 P1 验收条件**明列的字面键**，不属设计未定面。

### BDD-15: P8 为交付收尾且 delivery 必须声明 (Batch 4)

> Given 一个任务进入 P8
> When 运行 P8 gate
> Then P8 语义为**交付收尾**（非「发版」）；`delivery` 未声明时 gate 拦截（非 0），声明后放行

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B15-01 | `test_bdd_15_p8_gate_blocks_when_delivery_missing` | `delivery` 未声明 → P8 gate 非 0（非通过码 2）且输出含 `delivery` | gate_p8 无 delivery 校验 ⇒ 恒返回 2（行为未实现） |
| TC-B15-02 | `test_bdd_15_p8_gate_passes_only_when_delivery_declared` | 未声明 → 拦截；声明 `delivery` → 放行（rc=2） | 未声明也不拦截 ⇒ 前置断言失败（行为未实现） |
| TC-B15-03 | `test_bdd_15_p8_semantics_is_delivery_wrapup` | phases.yaml P8 名称含「交付」或「收尾」；P8 卡片记载 `delivery` | P8 名称仍为「发布准备」、卡片无 `delivery` ⇒ 语义未改 |

> **[DESIGN_GAP]（TC-B15-03）**：`delivery` 的合法取值集合与 P8 名称的精确措辞设计未定 ⇒
> 只断言语义方向（含「交付」或「收尾」）与 `delivery` 载体，不绑定具体句子。字段名 `delivery`
> 由 BDD-15 **明列**（「`delivery` 未声明时 gate 拦截」），非设计未定面。

### BDD-21: 第 4 批删除发版逻辑前先提供等价 preset (Batch 4)

> Given 第 4 批将删除协议里的发版逻辑
> When 提供 `preset: semver-changelog-tag`（把现有发版检查原样搬进声明）
> Then 使用者**一行声明即保持现状**；文件缺失时有发版痕迹（CHANGELOG / 版本文件 / `v*` tag）时
> 给显眼 WARNING；`UPGRADING.md` 写明迁移方式与截止版本

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B21-01 | `test_bdd_21_release_preset_is_declarable` | 声明 `release.preset: semver-changelog-tag` → `agate-config validate` rc=0 | `agate-config.py` 不存在（批 2）⇒ rc≠0（模块未实现） |
| TC-B21-02 | `test_bdd_21_upgrading_documents_preset_migration_and_cutoff` | UPGRADING.md 含 `semver-changelog-tag` + 「截止版本」 | UPGRADING 无该章节/字面 ⇒ 行为未改 |
| TC-B21-03 | `test_bdd_21_missing_declaration_with_release_traces_warns` | 无声明 + 有发版痕迹时 P8 gate 输出含 `semver-changelog-tag`/`release.preset`/`agate.config.yaml` WARNING | P8 gate 无声明/preset 迁移提示 ⇒ 行为未改 |

> **[DESIGN_GAP]（TC-B21-03）**：WARNING 的具体消费入口（gate_p8 / `agate-config validate` /
> 专门检查脚本）与措辞由 P4 按 BDD 落定；本用例断言输出**可观察到**该 WARNING 主题
> （`semver-changelog-tag` / `release.preset` / `agate.config.yaml`），不绑定具体命令或精确句子。
> TC-B21-01 依赖批 2 的 `agate-config.py`（本批 P3 时尚未实现，串行链上游）；P4 落地批 2 后本用例
> 的 `validate` 路径即具备实现对象。

**BDD 覆盖核对**：BDD-14 ×2 + BDD-15 ×3 + BDD-21 ×3 = **8 条用例**，
每条测试名引用对应 BDD 编号，可追溯到 P1 验收条件。

> BDD-22（横切：每批不回退）无需独立用例——由既有回归套件 + P5 全量承担（派发指引 §上游关联明确）。

## 3. 红灯基线（自跑记录）

```
python3 -m pytest agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py -v
→ 8 failed in 0.44s
```

8 条全部为 **AssertionError**——均为「被测结构/行为未实现」（B 类）：

| 用例 | 红灯类型 | 失败消息指向 |
|---|---|---|
| TC-B14-01 | AssertionError | phases.yaml 无「提交类型 → 关卡集合」结构 |
| TC-B14-02 | AssertionError | phases.yaml 无 `paused_from` 字面 |
| TC-B15-01 | AssertionError | gate_p8 未声明 `delivery` 仍 rc=2（无拦截） |
| TC-B15-02 | AssertionError | 未声明 `delivery` 仍 rc=2（前置负向失败） |
| TC-B15-03 | AssertionError | P8 名称仍为「发布准备」 |
| TC-B21-01 | AssertionError | `agate-config.py` 不存在 ⇒ validate rc≠0 |
| TC-B21-02 | AssertionError | UPGRADING.md 无 `semver-changelog-tag` / 「截止版本」 |
| TC-B21-03 | AssertionError | P8 gate 输出无声明/preset 迁移 WARNING |

**非 SyntaxError、非第三方 import 失败**（A 类，平台扫描与 collect 均已确认 0 命中/0 error），
亦非「断言与测试数据矛盾」：每条失败消息直指批 4 关卡层产物的缺席。

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py \
    agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py
→ exit 0（0 命中）
```

测试平台无关实现要点：
- 用 `tmp_path` / `task_dir` / `git_repo` fixtures；`run_cli(python_exe, ...)`（不裸 `python3`）；
- 全文本 I/O 显式 `encoding="utf-8"`；
- 不出现系统临时目录字面量（注释亦无）、不硬编码 `PATH`、不裸外部工具；
- **不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本、`agate/rules/phases.yaml`）——
  所有断言读取既有协议文件**只读**，写操作全在 `tmp_path` / `git_repo` 内；
  跑完 `git status --porcelain` 核验仓库根无本批新增污染文件。

## 5. 与实现对象的关系（供 P4）

- **被测对象**：`agate/rules/phases.yaml`（按提交类型选择关卡集合 + 转换表含 `paused_from`）、
  `agate/scripts/check-gate.py::gate_p8()`（`delivery` 声明校验；未声明 → 非 0）、
  `agate/phase-cards/P8-release.md`（P8 语义改交付收尾 + 记载 `delivery`）、
  `agate/UPGRADING.md`（`preset: semver-changelog-tag` 迁移方式 + 截止版本）、
  以及批 2 的 `agate/scripts/agate-config.py`（`validate` 接受 preset——TC-B21-01 的依赖）。
- **语义不变约束（BDD-14 / P2 §4.3）**：`gate_pass_exit` / `next` / `retreat` 语义**不得**因分级回归
  （TC-B14-01 以现状值作回归基线断言）。P4 若为扩展字段需同步 `rules/schema/phases.schema.json`
  （`additionalProperties: false`）——该文件**不在** §6.1b 的 batch4 `output` 列，若确需扩展，
  按 P2 §11 标 `[SCOPE+]` / `[DESIGN_GAP]` 交主 Agent。
- **删发版逻辑顺序（R3 硬约束）**：先提供等价物 `preset: semver-changelog-tag` → 再删；缺失时按
  发版痕迹（CHANGELOG / 版本文件 / `v*` tag）给 WARNING。TC-B21-01/03 即验「等价物先就位 + 迁移提示」。
- **P4 回归注意**：既有 `test_check_gate.py` G8 系列（`_P8_COMPLIANT = "bump_type: minor\ndebt_check: none\n"`）
  在 P4 加入 `delivery` 强制后**可能**需同步（G8 系列 P8-release.md 无 `delivery`）——本批不改它们，
  P4 处理。

## 6. 边界与不做

- 本批**只写测试**，不写实现（实现是 P4）。
- **只覆盖 batch4 的 BDD-14/15/21**，不碰 batch5-6（CI 诊断 / 义务登记表）。
- 不臆造设计未定的内部键名——TC-B14-01 / TC-B15-03 / TC-B21-03 已在 §2 标 `[DESIGN_GAP]`。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本、`agate/rules/phases.yaml`）——全在
  `tmp_path` / `git_repo` 内。
