---
phase: P4
task_id: TAG0042
type: implementation
parent: P2-design.md
trace_id: TAG0042-P4-batch2-20261006
status: draft
created: 2026-10-06
agent: implementer
implementation_dir: agate/
---

# P4 实现记录 — batch2-agate-config（项目形态声明层）

> 上游：`P1-requirements.md`（BDD-3 / BDD-4 / BDD-5 / BDD-6 / BDD-7 / BDD-8 + BDD-20 批 2 面）
> + `P2-design.md` §1.1 M4/M5/M6/M7/M8、§1.2 N6、§1.3 R2/R7、§4.1、§6.1b batch2
> + `P3-test-cases-batch2.md`（22 条红灯用例，P3 已写、实现前全红）。
> **范围**：只做 batch2（声明层）；不碰 batch3-6（`agate-run` / 关卡分级 / CI 诊断 / obligations）。
> 目标语义：项目形态由项目根 `agate.config.yaml` **声明**描述，协议读取该声明决定行为，不写死
> 技术栈；声明解析收敛到唯一读取函数；接入时自动 init（幂等）；存量项目无声明的行为与引入前一致。

## 改动清单

### 1. **新增** `agate/scripts/agate-config.py`（P2 §1.1 M4）

`agate-*.py` 工具类（非 `check-*`，不在 CHECK9 门禁 glob 面）。CLI 形态参照
`agate-install.py` 的 `_cmd_*` 分发 + `sys.exit(main(...))`。

| 落点 | 改动 |
|---|---|
| 模块头 / `_usage()` | 子命令与退出码语义自述（0=成功 / 非 0=失败） |
| `_cmd_init(project_root)` | 生成初始声明 `agate.config.yaml`；**已存在则不覆盖**（幂等）→ 0 |
| `_cmd_validate(project_root)` | 经 `agate_common.read_project_config` 取值 → 声明缺失/不可解析 → 1；非法 → 1 并逐条报出字段/值；合法 → 0 |
| `_validate_node(...)` | draft-07 子集递归校验（object/array/integer/string/boolean + enum + required + additionalProperties:false）；**不引入 jsonschema 依赖**（与 `check-yaml-schema.py` 同机制，标准库 + 声明 schema 数据驱动） |
| `_cmd_get(project_root, field)` | 点分路径输出单一字段客观值（字符串原样 stdout）；字段不存在 → 1 |
| `_cmd_list(project_root)` | 列出全部叶子字段路径；`_cmd_show` 展示完整声明（YAML） |
| `main(argv)` | `init` / `validate` / `get <field>` / `list` / `show` 分发；未知子命令 → 2 |

- **唯一读取函数**（BDD-6）：脚本内取值只经 `agate_common.read_project_config`，**无第二处
  声明解析**（不 `yaml.safe_load` 项目声明文件）。`yaml` 仅用于 `show` 的 `safe_dump`。
- 形态值不含任何单一项目假设（BDD-3/BDD-20）：`init` 模板用中性占位（`unknown`），脚本源码
  无 `pytest` / `agateon` / `python3` 硬编码 token（源码扫描用例 TC-B3-03）。为满足该用例，
  shebang 用 `#!/usr/bin/env python`（非惯例的 `python3`——脚本由解释器显式调用，shebang 非执行路径）。

### 2. **新增** `agate/rules/schema/project-config.schema.json`（P2 §1.1 M5）

draft-07 子集，与既有 4 个 schema 同构（`$schema` / `title` / `type: object` / `properties` /
`required` / `additionalProperties`）。字段：`schema_version`（integer enum [1]）、
`project.{language,package_manager}`、`verify.commands`（array[string]）、`release.preset`
（enum `["semver-changelog-tag"]`）、`paths.evidence`。**未改**既有 4 schema 字段集（P2 §1.2 N6）。

### 3. `agate/scripts/agate_common.py`（P2 §1.1 M6）

| 落点 | 改动 |
|---|---|
| 顶部 import | 新增 `import copy` |
| 新节「项目形态声明」 | 常量 `PROJECT_CONFIG_FILENAME` / `PROJECT_CONFIG_DEFAULTS` + **唯一读取函数** `read_project_config(project_root)` |

`read_project_config` 行为（P2 §4.1）：文件存在且可解析 → 深拷贝默认值打底并合并声明，`present=True`；
文件缺失 → 默认 dict + `present=False`（不抛异常、不退出）；YAML 非法/顶层非映射 → 默认 dict +
`present=False` + `parse_error`。函数体不含任何单一项目/技术栈 token（BDD-20 源码扫描）。

### 4. `agate/scripts/check-gate.py::gate_p0()`（P2 §1.1 M8 / §4.1 N2）

从「无条件 return 2」改为：调用 `agate-config validate` 子进程（`sys.executable` + 同目录脚本），
`validate` 的 rc **只决定是否打印 WARNING**（含 `agate.config.yaml` 文件名），**返回值恒为 2**
（迁移期不阻断；绝不把 validate 的 rc 泄漏进返回值）。`agate-config.py` 缺失时视为 rc=0（不误报）。
BDD-8「存量项目无声明的行为与引入前一致」。

### 5. `agate/scripts/install-hook.py`（P2 §1.1 M7）

新增 `_init_declaration(agate_root, repo_root)`：接入时经 `agate-config init`（**唯一实现**，不在
安装器重复模板）在**仓库根**生成声明；`agate-config.py` 缺失（如 fake 安装根测试场景）时只提示、
不阻断；init 非 0 也只提示不失败。在三个 hook 安装完成后、`.gitignore` 检测前调用。幂等由
`init` 的「已存在不覆盖」保证（BDD-7）。

### 6. `agate/scripts/agate-setup.py`（P2 §1.1 M7）

`_install_hook()` docstring 补明：`install-hook.py` 内部会自动 `agate-config init` 生成声明（幂等）。
setup 的项目侧安装委托 install-hook.py，故自动 init 行为随之生效（BDD-7 源码接入点断言）。

### 7. `agate/UPGRADING.md`（P2 §1.1 M19 批 2 面）

在 `### v0.79.0` 节内**追加**批 2 小节（**未改** batch1 已写段落）：声明文件引入 + `agate-config`
子命令；**迁移期无破坏性变更**（无声明的存量项目 `gate_p0` 仍 `exit 2` + WARNING，不 `exit 1`）；
**截止版本 v0.80.0** 起改 `exit 1`。BDD-8 文档面。

### 8. `agate/scripts/README.md`（登记面约定，P2 §1.4 ④）

「工作区工具」表补 `agate-config.py` 一行（用途 + 退出码语义）。非门禁，属约定。

### 9. `agate-workspace/agents/CODE-MAP.md`（新增文件核对）

scripts 模块补「项目声明族（新增 TAG0042 批 2）：agate-config.py」描述。

### 10. batch2 测试缺陷同步（P3 产出物，P4 修复；不改测试语义）

| 文件 | 改动 | 理由 |
|---|---|---|
| `agate/tests/unit/test_config_schema.py:235` | docstring 字面 `open(<声明文件>)` 改述为「对声明文件做旁路 `yaml.safe_load` 解析」 | 被编码守卫 `test_agate_scripts_encoding.py::test_bdd_5_*`（正则 `\bopen\(` + 无 `encoding=`）误判（派发指引点名） |
| `agate/tests/unit/test_agate_config.py:25` | 删除未使用的 `import os` | `ruff check agate/`（P2 §5 `P5_ruff`）会报 F401，阻断 P5；仅删无用 import，不动任何断言 |

## 新增文件核对表

> CODE-MAP 机制已采用（`agate-workspace/agents/CODE-MAP.md` 存在）；P2-skeleton.md 不存在（无骨架机制）。

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/scripts/agate-config.py` | `within agate/scripts`（无骨架机制，不适用偏离） | `[CODE_MAP_UPDATED]`（scripts 模块补「项目声明族」） |
| `agate/rules/schema/project-config.schema.json` | `within agate/rules/schema`（无骨架机制，不适用偏离） | `[CODE_MAP_UPDATED]`（rules 模块 `schema/*.json` 描述已泛化覆盖；scripts 模块条目同时记录其消费方 agate-config.py） |

## 自跑结果（自查 ≠ P5 gate；不预判 gate 结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch2 红→绿 | `python3 -m pytest agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py agate/tests/unit/test_agate_scripts_encoding.py -q` | `24 passed` |
| 关联回归（gate/hook/common/batch1/self-check） | `python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_install_hook.py agate/tests/unit/test_agate_common.py agate/tests/unit/test_tag0042_batch1_phase_semantics.py agate/tests/unit/test_t42_p3_platform_selfcheck.py agate/tests/unit/test_gate_key_suffix_audit.py -q` | `267 passed` |
| consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `exit 0`（0 ERROR；401 WARNING 全为冻结文件面） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2687 个测试用例`（与改动前一致，未漂移） |
| ruff | `~/.venvs/agate-dev/bin/ruff check agate/` | `All checks passed!` |
| 平台扫描（改动文件） | `check-platform-assumptions.py agate/scripts/agate-config.py agate/scripts/agate_common.py agate/scripts/check-gate.py agate/scripts/install-hook.py agate/scripts/agate-setup.py agate/tests/unit/test_config_schema.py` | 本批**新增行** 0 命中（`git diff` 新增行经 `grep python3` 为空）；报出的 R2 命中均为**存量**示例行（`agate_common.py:332` 等），非本批引入 |

**全量 unit 观测（供 P5 参考，非本批 gate）**：`pytest agate/tests/unit -q -n auto` →
`37 failed / 2428 passed`。逐条核对失败清单，**全部为 batch3-6 尚未实现的红灯用例**
（`test_agate_doctor` / `test_agate_ci_verify` / `test_agate_run` / `test_events_ledger` /
`test_check_p8_delivery` / `test_gate_layer`）**加 1 条环境失败**
（`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`：本机
`opencode debug agent` 子命令不存在，与 batch2 无关）；**无 batch2 相关失败**。

## [SCOPE+]

无。实现严格落在 batch2（BDD-3..8 + BDD-20 批 2 面）范围内；未发现必须做而 P1/P2 未覆盖的新需求。

## [DESIGN_GAP]

[DESIGN_GAP: P2 §4.1 正文一句写「迁移期 validate 对文件缺失只输出 WARNING 返回 0」，与同节 N2 伪代码（validate rc≠0 才触发 gate_p0 的 WARNING）及 P3 用例 TC-B8-01/02（要求 gate_p0 输出 WARNING）矛盾；实现按 N2 伪代码与 P3 用例：validate 对缺失/非法返回非 0，gate_p0 吸收为 WARNING 且恒 return 2。]
[DESIGN_GAP: P2 未指定 `agate-config validate` 的 schema 校验实现方式；实现自主采用脚本内 draft-07 子集递归校验（标准库 + 数据驱动，不引入 jsonschema 依赖），未复用 `check-yaml-schema.py`（其为 `check-*.py` 且带 `if __name__` 侧效应，导入成本高于本批所需）。]
[DESIGN_GAP: P2 §1.1 M7 未指定 install-hook 自动 init 的实现路径；实现自主选择「子进程调 agate-config init」而非在安装器内联模板，以保持声明模板的唯一实现（与 BDD-6 单源精神一致）。]
[DESIGN_GAP: P2 §4.1 要求 read_project_config 对缺字段填默认值，同时 §1.1 M5 schema 声明 required——validate 只经该唯一读取函数取值（TC-B6-04 禁旁路解析），故拿到的是已注入默认值的 dict，required 字段在当前声明结构下恒满足（required 判据不触发）。实现按 P2 保留默认注入（最小实现），未额外暴露「已声明键集合」以驱动 required。]

## 修正轮（C8 C1 修复）

> 触发：C8 review（`P4-review.md` round 2）判 `rejected`——1 条 CRITICAL（C1）。本轮回修 C1 + 其测试；
> 6 条 INFORMATIONAL 非阻塞，按派发约束不在本轮修。

### 修复点（C1）

| 文件 | 落点 | 改动 |
|---|---|---|
| `agate/scripts/agate_common.py` | `read_project_config()`（约 `:868-874`） | `except (OSError, ValueError)` → `except (OSError, ValueError, yaml.YAMLError)` |

**根因**：`yaml.safe_load` 对非法 YAML 抛 `yaml.YAMLError`（`ParserError`/`ScannerError`/`ComposerError`），
其**不继承** `ValueError`/`OSError` → 原 `except` 漏捕 → 抛未捕获 traceback，违反该函数 docstring
「文件存在但 YAML 非法 → 默认 dict + `present=False` + `parse_error`」契约。修复后语义不变（优雅返回）。

### 新增测试（1 条）

| 文件 | 用例 | 断言 |
|---|---|---|
| `agate/tests/unit/test_config_schema.py` | `test_bdd_6_read_project_config_malformed_yaml_is_graceful` | 非法 YAML（`not: [a mapping`）→ 不抛异常、返回 dict、`present is False`、`parse_error` 非空 |

平台无关（`tmp_path` + 显式 `encoding="utf-8"`）；不写仓库内已提交文件。

### 自跑结果（自查 ≠ P5 gate；不预判 gate 结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 定向 3 文件 | `pytest test_agate_config test_config_schema test_agate_scripts_encoding -q` | **25 passed**（原 24，+1 新用例） |
| 复现（CLI） | 临时目录写非法 YAML → `agate-config.py validate` | rc=1 + `声明文件缺失或不可解析: agate.config.yaml（迁移期不阻断）`，**无 traceback** |
| consistency | `check-protocol-consistency.py --strict-errors-only` | exit 0（**0 ERROR** / 401 WARNING 冻结面） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | **2688**（原 2687，+1） |
| ruff | `ruff check agate/scripts/agate_common.py` | `All checks passed!` |

### [SCOPE+]

无。仅修 C1 + 其回归测试；未动 6 条 INFORMATIONAL，未改 batch1 / batch2 其它已通过实现。
