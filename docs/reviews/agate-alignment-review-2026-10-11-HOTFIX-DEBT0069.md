---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: "H2-r2 复审：DEBT0069 发布门消费 release.preset —— 已知 preset 改为运行时从 project-config.schema.json 的 release.preset.enum 单源派生（删两份手抄副本）；补 README 索引行 + CHANGELOG 条目"
files_changed: [agate/scripts/agate-release.py, agate/UPGRADING.md, agate/scripts/README.md, CHANGELOG.md, agate/tests/unit/test_release_gate.py, agate/tests/unit/test_agate_config.py]
---

# 协议-脚本对齐审查（HOTFIX DEBT0069 — H2-r2 增量复审）

> 本文件覆盖 r1（2026-10-11）版本。r1 判 `needs-revision`（A2 / A3b / A5 三项 MISALIGNED + A7 待裁）；
> implementer 已修。本轮**逐条核闭合 + 查新破坏**。

## 0. 核心裁决（沿用 r1，本轮复核仍成立）

**「未知 preset ⇒ fail-closed」恰当（非破坏性）。** 依据：
`project-config.schema.json` 对 `release.preset` 是 **`enum: ["semver-changelog-tag"]` 枚举**（非任意字符串）；
`agate_schema.iter_errors()` 实现 enum 判定；`agate-config.py validate` 消费之，**既有契约
`test_config_schema.py:112 test_bdd_5_validate_rejects_illegal_enum_value` 早已锁定「非法 preset ⇒ rc≠0」**。
⇒ 未知 preset 在本改动前**就已 schema 非法**，会走到该状态的项目其 `validate` 本就红 ⇒ 发布门 fail-closed
**与声明契约一致**，**无面向既有合法项目的破坏性变更**。r2 未改本支行为（门语义不变）。

## 0b. r2 增量复审结论

**r1 三项 MISALIGNED + A7 待裁 全部真闭合；未发现新破坏；MISALIGNED = 0。**

## 审查结论汇总

| # | 审查项 | 结论（r2） | r1 |
|---|--------|-----------|-----|
| A1 | 文档→脚本对齐 | ALIGNED | ALIGNED |
| A2 | 脚本→文档对齐 | **ALIGNED** ✅（已闭合） | MISALIGNED |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** ✅（A3b 已闭合） | MISALIGNED |
| A4 | 测试覆盖 | ALIGNED | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054） | ALIGNED（**空清单：经实测无既有用例转红**） | ALIGNED |
| A5 | 下游影响 + 文档传播 | **ALIGNED** ✅（已闭合） | MISALIGNED |
| A6 | 锚点表覆盖 | ALIGNED | ALIGNED |
| A7 | 设计原则一致性 | **ALIGNED** ✅（ADR-014 已满足） | NEEDS_HUMAN_REVIEW |
| A8 | 声称-命令绑定 | ALIGNED | ALIGNED |

---

## 逐项审查（r2）

### A2: 脚本→文档对齐 — ALIGNED（r1 MISALIGNED 已闭合）

**r1 问题**：`agate/scripts/README.md:149` 的 `agate-release.py` 索引行列举门检查集但未含新增 preset 消费。

**r2 现状**（README.md:149，已改）：
> `gate …`（发布门：**消费 `release.preset`**——已知发布流（单源于 `rules/schema/project-config.schema.json` 的 enum）按既有检查集执行并在输出回显；未知 ⇒ 非 0；未声明 ⇒ 不阻断。另：CI success + consistency 0 ERROR + check-gate.py P8，TAG0051/DEBT0069）

**结论**：ALIGNED。索引行已同步消费点与三态语义，且点名单源（与实现一致）。

### A3: 一致性连锁 + 反向传播 — ALIGNED（A3b 已闭合）

**A3b 核心（r1 MISALIGNED）**：已知 preset 列表**非单源**（`KNOWN_RELEASE_PRESETS` / `_DEFAULT_RELEASE_PRESET` 手抄副本 vs schema enum，ADR-014）。

**r2 现状**：改为**运行时单源派生** `_known_release_presets()`（`agate-release.py:474-497`）：
- `_schema_path()` = `dirname(__file__)/../rules/schema/project-config.schema.json`（**基于脚本自身位置**）；
- 逐层取 `properties.release.properties.preset.enum`，**非空字符串数组**校验；
- schema 缺失/不可读/结构异常 ⇒ `ReleaseError`（**fail-closed**）。
- **两份手抄副本已删**：`grep -rn "KNOWN_RELEASE_PRESETS\|_DEFAULT_RELEASE_PRESET" --include=*.py agate/` → **零命中**（仅余一处注释）。
- 缺键回落的默认值改为取 `PROJECT_CONFIG_DEFAULTS["release"]["preset"]`（`agate_common`），**不再是本脚本第三份副本**。

**实测（单源真随 schema 联动）**：隔离协议根把 enum 加 `custom-flow` ⇒ 门**接受** `preset: custom-flow`（rc=0 且回显）；
工作树脚本 `_known_release_presets() == ('semver-changelog-tag',)` == schema enum。
⇒ 「schema 增删值 ⇒ 门行为随之变化」成立，**判据分叉在结构上不再可能**。

**残余观察（非阻断，非本次引入）**：`agate_common.py:919 PROJECT_CONFIG_DEFAULTS`、
`agate-config.py:49 _INIT_TEMPLATE` 仍各自写死 `semver-changelog-tag`——属 **TAG0042 既有**（DEBT0069 证据已列），
不是「门的判据副本」；若日后 schema enum 去掉该值，二者会与 schema 分叉。**建议**（可留作独立 DEBT）：
加一条守护 `PROJECT_CONFIG_DEFAULTS["release"]["preset"] in schema.enum`，或让 init/默认从 enum[0] 生成。

**A3a（连锁）**：`UPGRADING.md` ✓（r1 已同步）；`README.md` ✓（r2）；`CHANGELOG.md` ✓（r2，见 A5）。

**A2/A3b/A5/A7 闭合判定**：✅ 全部闭合。

### A4: 测试覆盖 — ALIGNED（r2 增强）

**实跑输出**（本审查独立复跑）：
```
$ python3 -m pytest agate/tests/unit/test_release_gate.py agate/tests/unit/test_agate_config.py -q
.............................                                            [100%]
29 passed in 4.30s          # r1 为 27；+2 = 两条单源/联动测试
```

**r2 新增两条（判别力强）**：
| 用例 | 判别力 | 说明 |
|------|-------|------|
| `test_debt0069_known_presets_single_sourced_from_schema_enum` | 强 | 断言 `list(mod._known_release_presets()) == schema.enum`；若函数缺失 → `AttributeError` 红；若为副本 → 值分叉则红 |
| `test_debt0069_gate_accepts_schema_added_preset` | **最强（端到端）** | 隔离协议根 enum 加值 ⇒ 门须**接受**；**任何手抄副本实现都会在此红**（副本不含新值 ⇒ 误 fail-closed） |

**三条回归（known/unknown/absent）+ 非破坏性**：本审查以**独立探针**（非依赖测试夹具）复现四态全绿（见 A8/A4b 探针）。

**结论**：ALIGNED。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED（**空清单**）

**经实测无既有用例转红、无需更新夹具。** 依据：
```
$ python3 -m pytest agate/tests/unit/test_config_schema.py agate/tests/unit/test_tag0051_p8_gate.py \
    agate/tests/unit/test_gate_layer.py agate/tests/unit/test_agate_release.py \
    agate/tests/unit/test_release_workflow.py agate/tests/unit/test_doc_sweep.py -q
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 7.68s
```
- `grep` 确认**无任何测试引用被删的 `KNOWN_RELEASE_PRESETS` / `_DEFAULT_RELEASE_PRESET`** ⇒ 无因删除而红者；
- 新增/变更用例复用既有夹具（`git_repo` / `_repo_with_task` / `_ci_cmd` / `_rc_cmd` / `H.copy_real_scripts` /
  `H.load_project_module` —— 后两个 helper **已存在**，非本次新增）⇒ **夹具更新清单为空**。
- **关于 flake**：dispatch 称 implementer 自报 2 failed、主 Agent 三次复跑 1 failed。本审查**受约束未复跑全量**；
  所跑 131 条相关用例 **0 失败**，**无法复现第二条失败、给不出第二个用例名**。⇒ 不据此判 MISALIGNED。

### A5: 下游影响 + 文档传播 — ALIGNED（r1 MISALIGNED 已闭合）

**r1 问题**：`CHANGELOG.md [Unreleased] → 修复` 逐条含 DEBT0065/66/67/68，独缺 DEBT0069。

**r2 现状**（`CHANGELOG.md:64-69`，已补）：
> **`release.preset` 无值消费方（DEBT0069）**：… 现由发布门 `agate-release.py gate` **消费**：已知发布流
> （**运行时单源于** `rules/schema/project-config.schema.json` 的 `release.preset.enum`，不手抄副本）…
> **未知** ⇒ 门非 0；**未声明** ⇒ 回落默认、**不阻断**。… **无面向既有合法项目的破坏性变更**（未知值本就 schema 非法…）

**结论**：ALIGNED。条目入「修复」节（与 DEBT0065-68 体例一致）、含 `DEBT0069`、破坏半径如实框定。
**破坏性判定**：无（见 §0）。**文档传播清点**：`UPGRADING.md` ✓ / `README.md` ✓ / `CHANGELOG.md` ✓；
`phase-cards/` `WORKFLOW.md` `orchestrator-template.md` `dispatch-protocol.md` `role-system.md` `LIMITATIONS.md`
无门/preset 检查集描述（实测零命中）⇒ 无需改。

### A6: 锚点表覆盖 — ALIGNED

未新增 `agate/scripts/` 文件、未新增 `check-*.py` ⇒ `check-protocol-consistency.py` 锚点表/CHECK 9 无需更新。
实测：`check-protocol-consistency.py --strict-errors-only` → **0 ERROR**（rc=0；433 frozen WARNING，其中
`CHECK10-scriptref` 1 条属**冻结历史文件**，非本次改动面——本改动未新增非冻结 WARNING）。

### A7: 设计原则一致性 — ALIGNED（r1 NEEDS_HUMAN_REVIEW 已闭合）

**ADR-014（判据单一权威源，`agate/adr.md:533-585`）①**：判据必须单源、不得自带副本。
r1 指出的「门内手抄副本」**已消除**——`_known_release_presets()` 运行时从 schema enum 取值，门的判据**单一权威源
= `project-config.schema.json`**。与近期 `#455 / DEBT0067`（写侧白名单从 schema 单源派生）**同向一致**。
**ADR-015（:589-659）**：判据分叉属实质错误——r2 使其结构上不可能。**ADR-016（:692, :702）**：
发布门只认 exit code——本次仍为 exit code 判定，不违反。
**结论**：ALIGNED（残余见 A3b 的「非阻断观察」，属既有、非本次引入）。

### A8: 声称-命令绑定 — ALIGNED

| 声称（出处） | 产出它的命令 | 结论 |
|---|---|---|
| 「已知集单源于 schema enum」（r2） | `python3 -c "import …; print(m._known_release_presets())"` | ✅ `('semver-changelog-tag',)` == schema enum |
| 「隔离根 enum 加值 ⇒ 门接受（真随 schema 变）」（r2） | 探针：拷贝脚本到 `<tmp>/proto/agate/scripts` + 写 `proto/agate/rules/schema/project-config.schema.json`（enum 加 `custom-flow`）→ `gate --repo … --ci-cmd … --consistency-cmd …` | ✅ rc=0 且回显 `preset=custom-flow` |
| 「schema 缺失/不可读/枚举为空 ⇒ fail-closed 且信息明确」（r2 docstring/新逻辑） | 探针 A/B/C（删 schema / 写非法 JSON / `enum: []`） | ✅ 均 rc=1，消息含路径/原因（`无法读取发布流 schema（…）` / `release.preset.enum 非法（应为非空字符串数组）`） |
| 「已知 → rc0；未知 → rc1（含名）；缺键 → rc0；validate(known) → rc0」（r1 三条回归 + 非破坏性） | 探针（真实工作树脚本 + 临时 git 仓 + mock ci/consistency） | ✅ 四态全绿，与 r1 一致 |
| 「29 passed」（r2 测试） | `python3 -m pytest agate/tests/unit/test_release_gate.py agate/tests/unit/test_agate_config.py -q` | ✅ 本审查实跑 29 passed |
| 「全量 1 failed / 2979 passed / 2 skipped，唯一红=本机环境项」（dispatch，主 Agent 实跑） | `python3 -m pytest agate/tests/ -q -n auto` | ⚠️ 未复跑全量（受约束）；已实跑 131 条相关用例 0 失败、四态探针全绿。**未能复现第 2 条失败，无第二个用例名** |

**结论**：ALIGNED。

---

## 新破坏专项核查（dispatch 第 2 点）

| 场景 | 期望 | 实测（探针） | 结论 |
|------|------|-------------|------|
| schema **缺失**（预设声明存在） | fail-closed + 信息明确 | rc=1：`无法读取发布流 schema（<path>）: [Errno 2] …` | ✅ |
| schema **非法 JSON** | fail-closed + 信息明确 | rc=1：`无法读取发布流 schema（<path>）: Expecting property name …` | ✅ |
| enum **为空数组** | fail-closed，不得静默回退空集 | rc=1：`release.preset.enum 非法（应为非空字符串数组）: []` | ✅ |
| enum 元素**非字符串** | fail-closed | 同分支 `not all(isinstance(v, str))` → rc=1 | ✅（代码路径） |
| 隔离协议根派生是否走**工作树 schema** | 是 | `_schema_path()` 基于 `__file__`（`scripts/../rules/schema`），**不依赖 `AGATE_ROOT`** ⇒ 跑哪个 checkout 的脚本就读哪个 checkout 的 schema。实测：拷贝脚本 → 读拷贝根的 schema，加值即接受 | ✅ |
| 缺键（未声明 preset）+ schema 缺失 | 不阻断（缺键不得 fail-closed） | preset 步跳过 schema 读取 → 按默认通过（`_known_release_presets()` 仅在 `declared` 时调用） | ✅（设计一致） |

**未发现新破坏。**

---

## 需修复项（主 Agent 动作）

**无。** r1 三项 MISALIGNED 与 A7 待裁均已真闭合，未引入新 MISALIGNED。

**非阻断观察（可留作独立 DEBT，不拦本次 commit）**：
`PROJECT_CONFIG_DEFAULTS["release"]["preset"]` 与 `agate-config.py::_INIT_TEMPLATE` 仍写死 `semver-changelog-tag`
（TAG0042 既有）。门的判据已单源；此项为「默认值/init 模板 vs schema enum」的既有轻度重复，建议加一条守护
（默认值 ∈ schema.enum）或从 enum[0] 生成。

---

## 只读纪律自查（RM-AG0081）

- 未执行任何写仓命令（`git add/commit/restore/reset/clean/stash` 均未调用）；
- 全部探针（`d69r2` / `d69r3`）建在 `/tmp/opencode` 一次性副本，「创建→操作→清理」**同一 bash 调用内完成**，跑后已 `rm -rf`；
- 未在 `agate-workspace/tasks/**` 下建目录；未触发任何真实外部动作；
- 未对被评审文件做任何编辑；未重跑全量套件（仅跑 131 条相关用例 + 1 次 consistency，均只读）；
- 产出文件**覆盖更新**同一路径（同一任务同日复核轮，符合 BDD-8 可覆盖分支）。
