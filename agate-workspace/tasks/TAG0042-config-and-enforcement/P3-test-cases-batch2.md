---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: test-designer
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — batch2-agate-config（agate-config 声明层）

> 上游：`P1-requirements.md`（BDD-3 / BDD-4 / BDD-5 / BDD-6 / BDD-7 / BDD-8 + BDD-20 批 2 面）
> + `P2-design.md` §1.1（M4/M5/M6/M7/M8）、§4.1（声明层设计）、§6.1b（batch2 `output`）
> + `P3-dispatch-context-test-designer-batch2.md`。
> 本批为 TDD 红灯批：测试**先于实现**，当前全部红灯（红灯原因 = 被测模块/行为未实现，B 类）。
> batch2 是模式 5 串行链的第 2 批（依赖 batch1），只覆盖声明层，不碰 batch3-6。

> **`test_code_dir`**：`agate/tests/unit/`（声明于 frontmatter，单一来源）。

## 1. 测试文件

| 文件 | 说明 |
|---|---|
| `agate/tests/unit/test_agate_config.py` | BDD-3 / BDD-4 / BDD-7 / BDD-8 红灯测试（新建） |
| `agate/tests/unit/test_config_schema.py` | BDD-5 / BDD-6 / BDD-20（批 2 面）红灯测试（新建） |

> 既有相关测试（`test_agate_common.py` / `test_check_gate.py` / `test_install_hook.py`）
> **不复用、不改动**——它们是 P4 改 `agate_common.py` / `check-gate.py` / `install-hook.py`
> 后需同步的对象；本批只新增 BDD-3..8 + BDD-20 的红灯测试。

## 2. BDD → 测试用例映射（1:1）

### BDD-3: 项目形态由声明文件描述，协议不写死技术栈 (Batch 2)

> Given 一个使用者项目，其形态与 agateon 不同（如 GitLab + Go + Helm）
> When 该项目用 `agate-config init` 生成声明文件并填写自身形态
> Then 协议的 gate / 推进 / 证据路径读取该声明决定行为，不再对「产品是 md」硬编码假设

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B3-01 | `test_bdd_3_init_generates_declaration_file` | `agate-config init` rc=0 且项目根生成 `agate.config.yaml` | 脚本不存在 ⇒ rc≠0、文件未生成（模块未实现） |
| TC-B3-02 | `test_bdd_3_declared_form_is_readback_not_hardcoded` | `get project.language`/`project.package_manager` 回读声明值（go/go-mod），非 agateon 形态 | 脚本不存在 ⇒ get 不可运行（模块未实现） |
| TC-B3-03 | `test_bdd_3_protocol_does_not_hardcode_md_product_shape` | `agate-config.py` 读取路径不含 `pytest`/`agateon`/`python3` 硬编码 token | 脚本不存在 ⇒ 无从检查（模块未实现） |

### BDD-4: agate-config 子命令提供完整读写能力 (Batch 2)

> Given 已存在声明文件
> When 运行读/校验/查询子命令
> Then 输出客观值（可被脚本消费），退出码语义固定（0=成功，非 0=失败）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B4-01 | `test_bdd_4_get_outputs_consumable_value` | `get project.language` stdout 为客观值且 rc=0 | 脚本不存在 ⇒ rc≠0（模块未实现） |
| TC-B4-02 | `test_bdd_4_list_and_show_output_declaration` | `list` 列出字段、`show` 展示完整声明，均 rc=0 | 脚本不存在 ⇒ rc≠0（模块未实现） |
| TC-B4-03 | `test_bdd_4_get_missing_field_is_nonzero` | 读**合法但不存在**字段 → rc≠0（先证 list rc=0 确实实现了脚本） | 脚本不存在 ⇒ list 前置 rc≠0（模块未实现） |

### BDD-5: agate-config 声明 schema 校验拒绝非法形态 (Batch 2)

> Given 一份声明文件含非法字段名或非法枚举值
> When 运行 `agate-config validate`
> Then 返回非 0 并指出非法字段/值；合法声明返回 0

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B5-01 | `test_bdd_5_schema_file_exists_and_is_isomorphic` | `rules/schema/project-config.schema.json` 存在且与既有 4 schema 同构 | schema 文件不存在（模块未实现） |
| TC-B5-02 | `test_bdd_5_validate_rejects_illegal_enum_value` | 非法 `release.preset` → rc≠0 且指出 preset | 脚本不存在 ⇒ rc≠0 且无正确报错内容（模块未实现） |
| TC-B5-03 | `test_bdd_5_validate_rejects_unknown_top_level_field` | 未知顶层字段 → rc≠0 且指出 `bogus_field` | 同上（模块未实现） |
| TC-B5-04 | `test_bdd_5_validate_accepts_legal_declaration` | 合法声明 → rc=0 | 脚本不存在 ⇒ rc≠0（模块未实现） |

### BDD-6: 唯一读取函数保证声明单源 (Batch 2)

> Given 声明文件与 schema 就位
> When 任意消费方读取某形态字段
> Then 全部消费方经同一读取函数取值（无第二处独立解析实现），等价守护可验证「两处取值同源」

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B6-01 | `test_bdd_6_read_project_config_exists` | `agate_common.read_project_config` 函数存在 | 函数不存在（模块未实现） |
| TC-B6-02 | `test_bdd_6_read_project_config_returns_declared_values` | 读取函数返回声明中的客观值（dict） | 函数不存在 ⇒ AttributeError（模块未实现） |
| TC-B6-03 | `test_bdd_6_two_readers_agree_single_source` | CLI（get）与库函数（read_project_config）取值**同源一致**（等价守护） | 函数/脚本不存在（模块未实现） |
| TC-B6-04 | `test_bdd_6_no_second_independent_yaml_parser_in_config` | `agate-config.py` 引用唯一读取函数、无旁路 YAML 解析 | 脚本不存在（模块未实现） |

### BDD-7: agate-setup / install-hook 自动 init 声明 (Batch 2)

> Given 一个尚未有声明文件的项目
> When 运行 `agate-setup`（或 `install-hook`）接入协议
> Then 自动生成（init）初始声明文件，且不覆盖既有声明（幂等）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B7-01 | `test_bdd_7_install_hook_auto_inits_declaration` | install-hook 接入后项目根生成声明文件 | 现行为不调 agate-config init ⇒ 文件未生成（行为未改） |
| TC-B7-02 | `test_bdd_7_install_hook_init_is_idempotent` | 先证 auto-init 生效，再改写声明后重跑 → 内容不被覆盖 | auto-init 未实现 ⇒ 前置断言即红（行为未改） |
| TC-B7-03 | `test_bdd_7_setup_source_invokes_config_init` | `agate-setup.py` 源码含 `agate-config init` 接入点 | setup 无该调用（行为未改） |

### BDD-8: 声明文件缺失时行为与现状一致且给 WARNING（迁移期） (Batch 2)

> Given 一个存量项目没有声明文件（未迁移）
> When 运行 gate_p0（调 validate）或任意消费声明的 gate 路径
> Then 行为与引入前一致，输出显眼 WARNING（不 exit 1），且 UPGRADING.md 写明截止版本改 exit 1

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B8-01 | `test_bdd_8_gate_p0_missing_declaration_keeps_passing_exit` | 前置：gate_p0 已接入 validate 并给 WARNING；且仍 rc=2（不 exit 1） | gate_p0 未接入 validate ⇒ 无 WARNING（行为未改） |
| TC-B8-02 | `test_bdd_8_gate_p0_missing_declaration_emits_warning` | 声明缺失时 gate_p0 输出含 `agate.config.yaml` 的显眼 WARNING | 现状输出无该 WARNING（行为未改） |
| TC-B8-03 | `test_bdd_8_upgrading_documents_cutoff_version` | UPGRADING.md 记载 `agate.config.yaml` 迁移 + 截止版本 exit 1 | UPGRADING 未记载该迁移（行为未改） |

### BDD-20: 项目形态声明化不引入只适用于单一项目的规则（批 2 面） (Batch 2 起)

> Given 每批 R6 双向差分在临时目录副本上再加一份 peekview 只读副本
> When 对副本运行该批改动后的 consistency + 相关 gate
> Then 无「只适用于 agateon 一个项目」的规则引入
> **批 2 面（dispatch-context 明确的设计层收窄断言）**：声明读取路径不硬编码任何单一项目名/技术栈

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B20-01 | `test_bdd_20_read_project_config_not_project_specific` | `read_project_config` 函数体不含 `agateon`/`peekview`/`pytest` 单项目 token | 函数不存在（模块未实现） |
| TC-B20-02 | `test_bdd_20_config_read_path_is_declaration_driven` | 两份不同形态声明（Go / Python）各自读回声明值（读取由声明驱动） | 函数不存在 ⇒ AttributeError（模块未实现） |

**BDD 覆盖核对**：BDD-3 ×3 + BDD-4 ×3 + BDD-5 ×4 + BDD-6 ×4 + BDD-7 ×3 + BDD-8 ×3 + BDD-20 ×2
= **22 条用例**，每条测试名引用对应 BDD 编号，可追溯到 P1 验收条件。

## 3. 红灯基线（自跑记录）

```
python3 -m pytest agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py -q
→ 22 failed in 0.48s
```

22 条全部为 **AssertionError（38 处）/ AttributeError（6 处）**——均为「被测模块未实现 / 行为未改」
（B 类）：`agate-config.py` 不存在（`No such file`）、`read_project_config` 不存在（AttributeError）、
`project-config.schema.json` 不存在、gate_p0 无声明 WARNING、install-hook/setup 不 init。
**非 SyntaxError、非第三方 import 失败**（A 类），亦非「断言与测试数据矛盾」：每条失败消息直指
批 2 声明层产物的缺席。属 check-tdd-red 认可的 **B 类真红灯**。

| 用例 | 红灯类型 |
|---|---|
| TC-B3-01/02/03 | AssertionError（agate-config.py 不存在） |
| TC-B4-01/02/03 | AssertionError（agate-config.py 不存在） |
| TC-B5-01 | AssertionError（schema 文件不存在） |
| TC-B5-02/03/04 | AssertionError（agate-config.py 不存在） |
| TC-B6-01 | AssertionError（read_project_config 不存在） |
| TC-B6-02/03 | AttributeError（read_project_config 不存在） |
| TC-B6-04 | AssertionError（agate-config.py 不存在） |
| TC-B7-01/02 | AssertionError（install-hook 不 init） |
| TC-B7-03 | AssertionError（setup 无 init 接入点） |
| TC-B8-01/02/03 | AssertionError（gate_p0 未接入 validate / UPGRADING 未记载） |
| TC-B20-01 | AssertionError（read_project_config 不存在） |
| TC-B20-02 | AttributeError（read_project_config 不存在） |

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py \
    agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py
→ exit 0（0 命中）
```

测试平台无关实现要点：
- 用 `tmp_path` / `task_dir` / `git_repo` fixtures；`run_cli(python_exe, ...)`（不裸 `python3`）；
- 全文本 I/O 显式 `encoding="utf-8"`；
- 需要「系统临时目录」字面量时**运行时拼接**（`_TMP = "/" + "tmp"`），注释中也**不写字面量**
  （R4 命中已修：BDD-20 注释原写 `/tmp`，改为「临时目录副本」）；
- 不写仓库内已提交文件（全在 `tmp_path` / `git_repo` 临时目录内）。

## 5. 与实现对象的关系（供 P4）

- **被测对象**：`agate/scripts/agate-config.py`（新增，init/validate/get/list/show + 退出码语义）、
  `agate/rules/schema/project-config.schema.json`（新增，与既有 4 schema 同构）、
  `agate/scripts/agate_common.py`（新增 `read_project_config()` 唯一读取函数）、
  `agate/scripts/agate-setup.py` / `install-hook.py`（接入时自动 init，幂等）、
  `agate/scripts/check-gate.py::gate_p0`（调 validate，迁移期只 WARNING、**恒 return 2**）、
  `agate/UPGRADING.md`（声明缺失迁移章节 + 截止版本）。
- **`gate_p0` 返回值口径（P2 §4.1 N2 订正）**：validate 的 rc **只决定是否打印 WARNING**，
  不参与 gate_p0 返回值；迁移期无论 validate 返回 0 或非 0，gate_p0 **恒 return 2**。
  本批负向用例 TC-B8-01/02 即验此口径。
- **schema 同构判据（P2 §1.4）**：`rules/schema/` 下既有 4 个 schema 的命名/`$schema`/`title`/`type`
  /`properties` 结构；新 schema 须与之同构（TC-B5-01）。
- **P4 回归注意**：既有 `test_agate_common.py` / `test_install_hook.py` / `test_check_gate.py` 中
  与 `gate_p0` / `agate_common` / `install-hook` 相关的断言可能在批 2 接入后需同步（本批不改它们，P4 处理）。

## 6. 边界与不做

- 本批**只写测试**，不写实现（实现是 P4）。
- **只覆盖 batch2 的 BDD-3..8 + BDD-20（批 2 面）**，不碰 batch3-6（`agate-run` / 关卡分级 /
  CI 诊断 / 义务登记表）。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本）——所有断言均在 `tmp_path`/`git_repo` 内。
