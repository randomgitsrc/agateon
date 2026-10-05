---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: test-designer
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — batch5-ci-doctor（CI 与诊断）

> 上游：`P1-requirements.md`（BDD-16 / BDD-17）
> + `P2-design.md` §1.1（M13/M14/M15）、§4.4（CI/诊断设计 + CHECK 10 方向）、§6.1b（batch5
>   `tests_filter` / `output`）、§12 实现完成的标志第 5 条
> + `P3-dispatch-context-test-designer-batch5.md`。
> 本批为 TDD 红灯批：测试**先于实现**，当前 14 条全部红灯（红灯原因 = 被测模块未实现，B 类）。
> batch5 是模式 5 串行链的第 5 批（依赖 batch4），只覆盖 CI 与诊断，不碰 batch6。

> **`test_code_dir`**：`agate/tests/unit/`（声明于 frontmatter，单一来源）。

## 1. 测试文件

| 文件 | 说明 |
|---|---|
| `agate/tests/unit/test_agate_ci_verify.py` | BDD-16 红灯测试（新建） |
| `agate/tests/unit/test_agate_doctor.py` | BDD-17 红灯测试（新建） |

> 既有 `agate/tests/unit/test_ci_gate_backstop.py`（测被替换的现状实现）**本批不改动**——
> 批 5 退役 `ci-gate-backstop.py` 后其去留由 P4/P8 决定（本批只新增 BDD-16/17 红灯测试）。

## 2. BDD → 测试用例映射（1:1）

### BDD-16: agate-ci-verify 替换 ci-gate-backstop 且无假绿 (Batch 5)

> Given 一次 push / PR
> When 运行 `agate-ci-verify`
> Then 它**实际重跑** gate 判定（不再是永远 SKIP 却显示绿），无适用场景时显式声明「跳过 + 原因」
>      （「跳过」与「通过」在输出上可区分）

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B16-01 | `test_bdd_16_ci_verify_script_exists` | `agate-ci-verify.py` 文件存在 | 脚本不存在（模块未实现） |
| TC-B16-02 | `test_bdd_16_ci_verify_reruns_gate_and_reports_failure` | gate 判定失败的项目 → rc≠0 且输出含 FAIL（**无假绿**） | 脚本不存在 ⇒ 无从重跑（模块未实现） |
| TC-B16-03 | `test_bdd_16_ci_verify_skip_declared_with_reason` | 无适用场景 → 输出显式含「跳过」标识**且**给出原因（不静默假绿） | 脚本不存在 ⇒ 无跳过声明（模块未实现） |
| TC-B16-04 | `test_bdd_16_ci_verify_source_reruns_gate` | 源码引用 `check-gate.py`（实际重跑判定，非恒绿） | 脚本不存在（模块未实现） |
| TC-B16-05 | `test_bdd_16_ci_verify_workflow_invokes_new_script` | workflow 调 `agate-ci-verify.py`，不再调 `ci-gate-backstop.py`（M15） | workflow 仍调旧脚本（引用未同步） |
| TC-B16-06 | `test_bdd_16_ci_verify_protocol_refs_synced` | CHECK10 扫描面协议文件不再引用退役脚本（CHECK 10 方向） | 协议文档仍引用旧脚本（引用未同步） |

### BDD-17: agate-doctor 诊断项目接入状态 (Batch 5)

> Given 一个已接入/未接入的项目
> When 运行 `agate-doctor`
> Then 输出客观接入状态（声明文件、hook、版本解析、账本完整性等），并对异常项给出可执行的修复指引；
>      成功退出码固定

| 用例编号 | 测试函数 | 断言 | 当前红灯原因（B 类） |
|---|---|---|---|
| TC-B17-01 | `test_bdd_17_doctor_script_exists` | `agate-doctor.py` 文件存在 | 脚本不存在（模块未实现） |
| TC-B17-02 | `test_bdd_17_doctor_reports_declaration_status` | 输出含「声明文件」接入状态维度 | 脚本不存在 ⇒ 无诊断输出（模块未实现） |
| TC-B17-03 | `test_bdd_17_doctor_reports_hook_status` | 输出含「hook」接入状态维度 | 脚本不存在（模块未实现） |
| TC-B17-04 | `test_bdd_17_doctor_reports_version_resolution` | 输出含「版本解析」状态维度 | 脚本不存在（模块未实现） |
| TC-B17-05 | `test_bdd_17_doctor_reports_ledger_integrity` | 输出含「账本完整性」状态维度 | 脚本不存在（模块未实现） |
| TC-B17-06 | `test_bdd_17_doctor_gives_repair_guidance_for_unintegrated_project` | 未接入项目 → 输出含可执行的修复指引 | 脚本不存在（模块未实现） |
| TC-B17-07 | `test_bdd_17_doctor_reports_integrated_project` | 已接入项目（有声明文件）→ 声明维度报「存在」 | 脚本不存在（模块未实现） |
| TC-B17-08 | `test_bdd_17_doctor_success_exit_code_fixed` | 诊断正常完成 → 退出码固定为 0 | 脚本不存在 ⇒ rc≠0（模块未实现） |

**BDD 覆盖核对**：BDD-16 ×6 + BDD-17 ×8 = **14 条用例**，每条测试名引用对应 BDD 编号，
可追溯到 P1 验收条件。

## 3. 红灯基线（自跑记录）

```
/usr/bin/python3 -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_agate_doctor.py -v
→ 14 failed in 0.30s（14 collected）
```

14 条全部失败，失败原因均为 **AssertionError / 文件缺失**——属「被测模块未实现」
（B 类）：`agate/scripts/agate-ci-verify.py`、`agate/scripts/agate-doctor.py` 均不存在
（子进程 `No such file` ⇒ rc=2），workflow 与协议文档仍引用退役脚本（引用未同步）。
**非 SyntaxError、非第三方 import 失败**（A 类）——collection 无错误，`--collect-only` 正常收集 14 条。

| 用例 | 红灯类型 |
|---|---|
| TC-B16-01/04 | AssertionError（`agate-ci-verify.py` 不存在） |
| TC-B16-02/03 | AssertionError（子进程 `No such file` ⇒ rc=2、无输出） |
| TC-B16-05/06 | AssertionError（workflow / 协议文档仍引用 `ci-gate-backstop.py`） |
| TC-B17-01..08 | AssertionError（`agate-doctor.py` 不存在，rc=2、无诊断输出） |

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py \
    agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_agate_doctor.py
→ exit 0（0 命中）
```

测试平台无关实现要点：
- 用 `tmp_path` / `git_repo` fixtures；`run_cli(python_exe, ...)`（不裸 `python3`）；
- 全文本 I/O 显式 `encoding="utf-8"`；
- **不写系统临时目录字面量**（含注释）；无裸 `python3` / 硬编码 `PATH`。

## 5. 写入隔离

- **不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本）：所有断言均在 `tmp_path` / `git_repo` 内。
- doctor 可能写台账（`installed-projects.json`）：`_isolated_agate_env(tmp_path, agate_root)` 把
  `AGATE_HOME` 钉到 `tmp_path/isolated-agate-home`（参照 `test_agate_config.py` 先例），
  确保测试期间无真实写入。
- 自跑后 `git status --porcelain` 核验：新增文件仅本批两个测试文件（及既有未提交的批 1-4 产物），
  无「跑测写脏账本」污染。

## 6. 与实现对象的关系（供 P4）

- **被测对象**：`agate/scripts/agate-ci-verify.py`（新增，替换 `ci-gate-backstop.py`）、
  `agate/scripts/agate-doctor.py`（新增）、`.github/workflows/protocol-tests.yml`（gate-backstop
  job 改调新脚本）；退役同步面见 P2 §4.4。
- **CI 定位约定（P4 对齐点）**：TC-B16-02 同时提供仓库根 `.state.yaml`（现状 backstop 约定）
  与任务级 `.state.yaml`（agate 任务状态实际位置），使替换实现无论按哪种约定定位都能命中；
  TC-B16-02 以 phase=P1 缺 `P1-review.md` 构造「gate 判定失败」场景（`check-gate.py P1` → exit 1）。
- **跳过语义（P4 对齐点）**：TC-B16-03 要求无适用场景时输出**显式**含「跳过」标识 + 原因
  （对应 X3 假绿整改：不再静默 `return 0` 而输出与 PASS 无法区分）。
- **CHECK 10 方向（P4/P8 硬约束）**：退役 `ci-gate-backstop.py` 后，`.github/workflows/`（TC-B16-05）
  与 CHECK10-scriptref 扫描面的非豁免协议文件（TC-B16-06：`WORKFLOW.md` / `state-machine.md` /
  `platform-notes.md` / `dispatch-protocol.md` / `phase-cards/P3-tdd.md` /
  `assets/templates/retrospective-template.md`）须同步更新引用，否则 CHECK10 新增 ERROR
  （TC-B16-06 按**裸名** `ci-gate-backstop` 断言：CHECK10 只报 `.py` 形式，但退役后文档亦不应
  再引用其名——`dispatch-protocol.md` / `state-machine.md` 即属裸名引用面）。
  `UPGRADING.md`（整文件豁免）与 `CHANGELOG.md`（叙事降级 WARNING）不在断言面；
  `agate/scripts/README.md` 另有「退役名豁免」通道，亦不列入。

## 7. DESIGN_GAP / 待 P4 对齐项

- **[DESIGN_GAP-1] `agate-ci-verify` 的调用接口未在 P2 §4.4 固化**：设计仅写「实际重跑 gate 判定」
  与「跳过/通过可区分」，未写是否接受参数、如何定位任务。本批按「无参数 + cwd 定位（镜像
  ci-gate-backstop 的仓库根约定）+ 兼容任务级 `.state.yaml`」设计测试（TC-B16-02/03）。P4 若采用
  不同注入点（如 `AGATE_TASK_DIR`），可在不改变 BDD-16 语义下对齐该注入点（参照 batch3 先例）。
- **[DESIGN_GAP-2] `agate-doctor` 退出码语义未精确化**：BDD-17 写「成功退出码固定」，P2 §4.4 写
  「退出码固定」。「成功」本批解释为「诊断正常完成」⇒ TC-B17-08 断言 rc=0（诊断工具报告问题但
  自身执行成功）。若设计意图为「发现异常即非 0」，P4 应标 `[DESIGN_GAP]` 交主 Agent 明确，
  并同步 TC-B17-08。
- **[DESIGN_GAP-3] 「跳过/通过可区分」的具体标识未固化**：TC-B16-03 只要求存在「跳过」标识 + 原因
  文本，不绑定具体 token（如 `SKIP:` / `BACKSTOP-INACTIVE`），留 P4 定稿。

## 8. 边界与不做

- 本批**只写测试**，不写实现（实现是 P4）。
- **只覆盖 batch5 的 BDD-16/17**，不碰 batch6（义务登记表）。
- BDD-22（横切：每批不回退）无独立用例，由既有回归套件 + P5 全量承担。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本）——所有断言均在 `tmp_path`/`git_repo` 内。
