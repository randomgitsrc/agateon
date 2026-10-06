---
phase: P4
task_id: TAG0042
type: implementation
parent: P2-design.md
trace_id: TAG0042-P4-batch3-20261006
status: draft
created: 2026-10-06
agent: implementer
implementation_dir: agate/
---

# P4 实现记录 — batch3-agate-run（执行层）

> 上游：`P1-requirements.md`（BDD-9 / BDD-10 / BDD-11 / BDD-12）
> + `P2-design.md` §1.1 M9/M10、§1.2 N3、§1.3 R4/R5、§4.2、§6.1b batch3、§12 第 3 条
> + `P3-test-cases-batch3.md`（15 条红灯用例，P3 已写、实现前全红）。
> **范围**：只做 batch3（执行层）；不碰 batch4-6（关卡分级 / CI 诊断 / obligations）。
> 目标语义：项目的验证命令经**不可绕开路径**（`agate-run`）执行，退出码如实传播（含 pipefail）；
> `--baseline` 产出可比对 `.out` 证据且被 `.gitignore` 覆盖；执行写入 `cmd_run` 账本事件
> （走 `append_event` 唯一写路径，不破哈希链）；hook 一并暂存账本。

## 改动清单

### 1. **新增** `agate/scripts/agate-run.py`（P2 §1.1 M9）

`agate-*.py` 工具类（非 `check-*`，不在 CHECK9 门禁 glob 面）。CLI：`agate-run [--baseline] <命令>`。

| 落点 | 改动 |
|---|---|
| 模块头 / `_usage_error` | 职责自述（BDD-9..12）；用法错误 → 2 |
| `_resolve_command(cfg, arg)` | 经 `agate_common.read_project_config`（唯一读取函数）取 `verify.commands`；CLI 实参须**精确匹配**一条声明命令，否则拒绝执行（不可绕开路径） |
| `_evidence_path(cfg, project_root, index)` | 证据路径 `{paths.evidence}/cmd-<index>.out`；`paths.evidence` 缺省 `.agate-evidence`。**槽位下标**（声明中的位置）作为稳定 key，命令文本变更后仍可与既有基线比对（BDD-10「命令输出改变」） |
| `_run_command(cmd)` | POSIX：`"set -o pipefail; " + cmd` + `shell=True, executable="bash"`（复用 `agate_common.run_test_with_formatter` 已验证写法，P2 §4.2）；非 POSIX（win32/MSYS2）：**退化**为不吞退出码的直执行 + 显式 `WARNING`（ADR-015，不静默报绿） |
| `_is_ignored(project_root, path)` | `git check-ignore -- <rel>`：rc 0=已忽略 / rc 1=未忽略 / 其它（非 git 仓库、git 不可用）=无法判定 → 调用方 WARNING 跳过 |
| `_write_evidence` / `_read_bytes` | 证据落盘（显式 utf-8）/ 逐字节读取，比对为二值判定 |
| `_record_cmd_run(cmd, exit_code)` | 经 `agate_common.append_event`（**唯一写路径**）追加 `cmd_run` 事件（`cmd` / `exit` / `runner`，`ts`/`prev_hash` 由 `append_event` 补）；目标账本目录由 `AGATE_TASK_DIR` env 指定；未指定 → 跳过 |
| `main(argv)` | 解析 `--baseline` → 执行 → 打印合并输出 → 证据/ignore 检查 → 记账 → 返回命令退出码 |

**语义要点**：
- `--baseline` 首次（无 `.out`）→ 先做 ignore 检查，未覆盖则**报错且不落盘**（BDD-11-02），已覆盖/无法判定则落盘；已存在基线 → 逐字节比对，不一致 → 打印 `baseline mismatch … diff …` 且返回非 0（BDD-10-03）。
- 非 `--baseline` 的后续执行：若已有基线亦比对（BDD-10「后续执行逐字节比对」）。
- 命令未声明 / 用法错误不写账本；命令执行本身（无论退出码）后写 `cmd_run`（BDD-12-02 要求 `exit 3` 仍落事件）。

### 2. `agate/scripts/agate_common.py`（P2 §1.1 M6 / §4.2）

**未改**。`cmd_run` 事件复用既有 `append_event`（唯一写路径），无需新增函数（P2 §1.1 M6 明示「cmd_run 事件无需新函数」）。pipefail 写法亦复用既有 `run_test_with_formatter` 的已验证口径。

### 3. `agate/scripts/pre-commit-gate.py`（P2 §1.1 M10）

| 落点 | 改动 |
|---|---|
| 2h.1d（state_transition 事件之后） | 新增「一并暂存账本」：任务目录 `gate-events.jsonl` 存在时 `run_git(["add", …/gate-events.jsonl])`——把 agate-run 追加的 `cmd_run` 及本 hook 的 `gate_run`/`state_transition` 一并纳入本次 commit。**不直接写账本文件**（避免绕过 `append_event` 破链，P2 R5） |
| 导入错误提示（原 `:63`） | 「需 python3 + pyyaml」→「需 Python 3 + pyyaml」：消除平台扫描 R2 命中（`python3` 命令位置字面量），使**本批改动文件**平台扫描 0 命中（无测试断言该提示文案） |

`gate-events.jsonl` 已被既有 `_NON_MD_YAML_RE` 识别为 gate 元数据（非 md/yaml 源码面），暂存后不触发 E3 代码文件 WARNING。

### 4. `agate-workspace/agents/CODE-MAP.md`（P4 卡新增文件核对表）

scripts 模块补「执行层族（新增 TAG0042 批 3）：agate-run.py」描述。

### 5. `agate/scripts/README.md`（登记面约定，P2 §1.4 ④）

「工作区工具」表补 `agate-run.py` 一行（用途 + 退出码语义）。非门禁，属约定。

## 新增文件核对表

> CODE-MAP 机制已采用（`agate-workspace/agents/CODE-MAP.md` 存在）；P2-skeleton.md 不存在（无骨架机制）。

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/scripts/agate-run.py` | `within agate/scripts`（无骨架机制，不适用偏离） | `[CODE_MAP_UPDATED]`（scripts 模块补「执行层族」） |

## 自跑结果（自查 ≠ P5 gate；不预判 gate 结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch3 红→绿 | `/usr/bin/python3 -m pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q` | `15 passed` |
| hook 集成回归 | `/usr/bin/python3 -m pytest agate/tests/integration/test_pre_commit_hook.py -q` | `61 passed` |
| 关联回归（账本审计 / 平台自查 / P5 计数） | `/usr/bin/python3 -m pytest agate/tests/unit/test_check_events.py agate/tests/unit/test_t42_p3_platform_selfcheck.py agate/tests/unit/test_agate_gate_p5_count.py -q` | `24 passed` |
| consistency | `/usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `exit 0`（**0 ERROR**；402 WARNING 全为冻结文件面） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2688 个测试用例`（下界语义，未漂移） |
| ruff | `~/.venvs/agate-dev/bin/ruff check agate/scripts/` | `All checks passed!` |
| 平台扫描（本批改动文件） | `check-platform-assumptions.py agate/scripts/agate-run.py agate/scripts/pre-commit-gate.py` | `exit 0`（0 命中；修复了 `pre-commit-gate.py` 一处**存量** R2 命中） |
| 账本隔离核验 | `git status --porcelain` | 仅本批预期改动（`agate-run.py` 新增 / `pre-commit-gate.py` 修改）；无仓库内账本/状态文件污染 |

## 观察项（已就地处理）

- 反向传播（SELF-GATE round 5 修复轮）发现：`agate/scripts/check-events.py:14` docstring 的「已知类型」注释含同款事件枚举（`gate_run/judge_verdict/state_transition/dispatch_route`），未补 `cmd_run`。该处为**脚本内注释、非协议文档、非门禁**（round4 评审标注「非门禁，可选」），不在本批硬约束「只改这 2 处枚举」范围内。**SCOPE+ 消解轮已就地处理**：该注释枚举补入 `cmd_run`（纯注释文本，不改任何审计逻辑）。

## [DESIGN_GAP]

[DESIGN_GAP: P2 §4.2 / M10 列有「修正 formatter 计数」，但未指明缺陷、落点或判据，且 P3 未写任何覆盖该点的用例（无对应 BDD）。实现前查明：仓库内与「formatter 计数」相关的既有代码仅 `agate_common.is_gate_meta_key`（排除 `_formatter`/`_timeout_seconds` 后缀，已有 GPC.1/2/4 测试锁定，正确）、`agate_common._fallback_json`（无 formatter 时 total/passed/failed 恒 0，为既有设计且判 A/B 出口码依赖它）、`agate-capture-env-baseline.py` 的汇总计数↔明细计数一致性检查（不在本批 output 文件面）。无一处存在可复现缺陷；改动 `_fallback_json` 计数将改变 TDD 判定路径（违反 P2 §1.2 N3「不改 TDD 判定语义」）。故本批**未做**该项变更，留待主 Agent 裁决落点。]
[DESIGN_GAP: P2 §4.2 写 `agate-run <cmd-key|命令>`，但 `project-config.schema.json` 的 `verify.commands` 为字符串数组、无命名 key。实现将 CLI 实参按**声明中的命令文本精确匹配**解析，并以该命令在数组中的**下标**作为证据槽位 key（`cmd-<n>.out`）——下标在命令文本变更后稳定，使 BDD-10-03「命令输出改变 → 与基线比对报差异」成立。若后续需命名 key，须先扩展 schema。]

## 修正轮（SELF-GATE round 5 修复）

> 触发：round 4 协议-脚本对齐审查判 **MISALIGNED**（A2 / A3b / A5.3，**同一根因**）——
> 本批新增账本事件类型 `cmd_run` 未反向传播到协议文档的「事件类型枚举」。
> 先例：`dispatch_route`（TAG0034，提交 `b68af6b`）同法加入两处枚举。

### 改动（纯文本，各补 `cmd_run`）

| # | 文件 | 位置 | 改动 |
|---|---|---|---|
| 1 | `agate/CONTEXT.md` | `:31`（`gate-events.jsonl（事件账本）` 术语表行） | 事件类型枚举补 `cmd_run`：`gate_run` / `judge_verdict` / `state_transition` / `dispatch_route` / **`cmd_run`** |
| 2 | `agate/git-integration.md` | `:176-177`（commit 一并暂存的账本枚举） | 事件类型枚举补 `cmd_run`：`gate_run` / `state_transition` / `judge_verdict` / `dispatch_route` / **`cmd_run`** |

- 措辞与 `agate-run.py` 的 `cmd_run` 事件字段一致（命令 / 退出码 / 时间戳，`ts`/`prev_hash` 由 `append_event` 补）；仅补事件名，不新增审计机制。
- 不改 `agate-run.py` 行为、不改其它协议文档、不改测试。

### 反向传播检查

- 全量扫描 `agate/**/*.md` 的账本事件枚举：仅上述 2 处为**协议文档**枚举面，均已补齐。
- `agate/scripts/check-events.py:14` docstring 的「已知类型」注释含同款枚举（脚本内注释、非协议文档、非门禁；round4 评审标注「可选」）→ **SCOPE+ 消解轮已就地补入 `cmd_run`**（纯注释，不改审计逻辑；见上文「观察项（已就地处理）」）。
- 其余出现于 `docs/design-notes/`、`docs/reviews/`、`site/`、`agate-workspace/tasks/` 的枚举均为**冻结 / 非协议**文件，按设计不改。

### 自查（自查 ≠ gate）

| 验证项 | 命令 | 结果 |
|---|---|---|
| consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `exit 0`（**0 ERROR**；402 WARNING 全为冻结文件面） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2688 个测试用例`（未漂移） |

## 修正轮（C8 C1 修复）

> 触发：batch3 C8 评审判 **rejected**（Pass 1 唯一 CRITICAL = C1）。
> 范围：**只修 C1 + 其回归测试**；Pass 2 的 5 条 INFORMATIONAL 本轮不修（未标 `[SCOPE+]`）。

### C1 — `.out` 证据写入非字节精确（Windows 上破坏 BDD-10 逐字节比对）

| 落点 | 修复 |
|---|---|
| `agate/scripts/agate-run.py:117`（`_write_evidence`） | 写盘由文本模式默认换行（`open(path, "w", encoding="utf-8")`，`newline=None` 会在写时把 `\n` 翻译为 `os.linesep`）改为**字节精确**：`open(path, "wb")` + `handle.write(output.encode("utf-8"))`。使写盘字节 == 比对基准（`:180`/`:182` 的 `_read_bytes(...) != output.encode("utf-8")`）。docstring 补记该约束与原因。 |

- **根因**：写侧（文本模式默认换行）与比对侧（字节精确）在 POSIX 重合、在 Windows（`os.linesep="\r\n"`）必然不一致 → `--baseline` 首次落盘后任何后续执行恒报 `baseline mismatch`/rc=1，BDD-10 在 Windows 失效。
- **修复口径**：与仓库既有字节精确约定一致（`agate_package.py` 用 `newline=""`）；未改 `_run_command` / 比对逻辑 / 其它 batch3 实现。

### 新增测试（+1）

| 用例 | 断言 |
|---|---|
| `test_agate_run.py::test_bdd_10_baseline_evidence_is_byte_exact`（标 `windows_smoke`） | ① 端到端：`--baseline` 落盘的 `.out` 证据 `read_bytes()` == 命令输出（`result.stdout`）的 UTF-8 字节——以实际捕获输出为基准，平台无关、不写死换行序列；② 源码面守卫：`_write_evidence` 的 `with open(` 写盘调用行须含 `"wb"` 或 `newline=""`（防回归；**只查调用行**，不搜整段函数体，避免被 docstring 里的 `"wb"` 字样误导）。 |

- **红绿核验（就地反证）**：临时把写盘还原为 `open(path, "w", encoding="utf-8")` → 该用例 **1 failed**（源码面守卫命中）；恢复修复后 **1 passed**。即该测试对 C1 回归有效（Linux 上行为面无法复现换行翻译，故源码面守卫是必要补充）。

### 自查（自查 ≠ gate）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch3 定向回归 | `/usr/bin/python3 -m pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q` | `16 passed`（较修复前 15 +1 = 新增 C1 回归测试） |
| consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | `exit 0`（**0 ERROR**；402 WARNING 全为冻结文件面） |
| count-tests | `bash agate/tests/scripts/count-tests.sh` | `总计：2689 个测试用例`（较上轮 2688 +1 = C1 回归测试） |
| ruff | `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate-run.py agate/tests/unit/test_agate_run.py` | `All checks passed!` |
| 账本隔离核验 | `git status --porcelain` | 仅本批预期改动（`agate-run.py` / `test_agate_run.py`）；无仓库内账本/状态文件污染 |
