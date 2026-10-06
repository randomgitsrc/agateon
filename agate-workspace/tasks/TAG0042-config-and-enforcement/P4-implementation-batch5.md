---
phase: P4
task_id: TAG0042
agent: implementer
implementation_dir: agate/
---

# P4 实现 — batch5-ci-doctor（CI 与诊断：agate-ci-verify + agate-doctor）

> 范围：仅 BDD-16 / BDD-17（P2 §1.1 M13/M14/M15、§4.4、§6.1b `batch5-ci-doctor`、§12 第 5 条）。
> 不碰 batch6（obligations）。自查 ≠ gate：本文只报自跑结果，不预判 P5 gate 结论。

## 1. 改动清单（文件 → 落点）

| 文件 | 落点 | 对应 |
|---|---|---|
| `agate/scripts/agate-ci-verify.py` | **新增**（`agate-*.py` 工具类）：无参数 + cwd 定位；**实际重跑** `check-gate.py` 判定；`.gate-result.json` 存在时比对记录值；每个「跳过」面显式 `SKIP:` + 原因；平台无关（不探测 CI 平台变量） | BDD-16 / M13 |
| `agate/scripts/agate-doctor.py` | **新增**（`agate-*.py` 工具类）：诊断①声明文件（经 `agate_common.read_project_config` 唯一读取函数）②git hook③版本解析④账本完整性（`gate-events.jsonl` 哈希链）；异常项给可执行修复指引；**退出码固定 0** | BDD-17 / M14 |
| `.github/workflows/protocol-tests.yml` | `gate-backstop` job 的 run step 改调 `agate-ci-verify.py`（job 名保留）；注解/summary 判据由 `BACKSTOP-INACTIVE` 改 `SKIP:` | BDD-16 / M15 |
| `agate/scripts/ci-gate-backstop.py` | **删除**（退役；见 §3） | BDD-16 |
| `agate/scripts/check-protocol-consistency.py` | 移除退役脚本锚点；`uncovered_gate_scripts()` extras 去掉该名；`check-judge-verdict` / `check-events` 锚点 callers 去掉该名；注释同步；`SCRIPT_REF_RE` 保留该名作**退役名拦截** | CHECK10 方向 |
| `agate/scripts/agate-summary.py` | 防护清单项 `ci-gate-backstop.py` → `agate-ci-verify.py` | 退役同步 |
| `agate/scripts/check-gate.py` | 头注释中「provenance 由 pre-commit-gate.sh / ci-gate-backstop.py 单独调用」→ 仅 pre-commit-gate.sh | 退役同步 |
| `agate/scripts/README.md` | ① 覆盖 glob 描述去掉退役名；② 「CI 兜底」行改 `agate-ci-verify.py`；③ 新增「诊断」节 `agate-doctor.py` 行 | 退役同步 |
| `agate/WORKFLOW.md` | CI backstop 段：改为经 `agate-ci-verify.py` 重跑 `check-gate.py`；删去已不再执行的 provenance/git blame 兜底声明 | CHECK10 |
| `agate/state-machine.md` | 「CI 由 ci-gate-backstop 兜底重跑」→「agate-ci-verify」 | CHECK10 |
| `agate/platform-notes.md` | CI backstop 段改为 `agate-ci-verify.py`（平台无关，任何环境直接调用） | CHECK10 |
| `agate/dispatch-protocol.md` | 历史实证举例裸名 → 「CI 兜底改造」（去掉退役裸名） | CHECK10 |
| `agate/phase-cards/P3-tdd.md` | refactor 段落去掉「ci-gate-backstop.py P3 分支」表述 | CHECK10 |
| `agate/assets/templates/retrospective-template.md` | 机制表行 `ci-gate-backstop.py` → `agate-ci-verify.py` | CHECK10 |
| `agate/assets/formatters/README.md` | E2BIG 叙事段裸名 → 「CI 兜底」（**派发清单未列、但属 CHECK10 扫描面**，见 §4） | CHECK10 |
| `agate/tests/unit/test_ci_gate_backstop.py` | **删除**（测退役对象） | 退役同步 |
| `agate/tests/unit/test_check_protocol_consistency.py` | 移除 `test_check_9_ci_gate_backstop_anchor_in_scan`（锚点已退役） | 退役同步 |
| `agate/tests/unit/test_check_gate.py` | `test_tag0035_bdd_2_*` 由测 backstop 改测 `agate-ci-verify.py`（同语义：记录值==重跑值 → PASS） | 退役同步 |
| `agate/tests/unit/test_mvwu_protocol_docs.py` | BDD-68 目标脚本元组 `ci-gate-backstop.py` → `agate-ci-verify.py`（+ 文档串同步） | 退役同步 |
| `agate/tests/README.md` | 映射行 `ci-gate-backstop.py` → `agate-ci-verify.py`；新增 `agate-doctor.py` 行 | 退役同步 |

## 2. 关键实现落点

### 2.1 `agate-ci-verify.py`（BDD-16，无假绿）

- **定位**：`_locate_state()` 优先仓库根 `.state.yaml`（镜像 backstop 约定），其次 `{tasks_dir}/*/.state.yaml`（兼容任务级，`agate_common.resolve_workspace` 解析）。
- **判定**：`_run_gate(phase, task_dir)` 子进程调 `check-gate.py PHASE TASK_DIR`（源码字面含 `check-gate.py`，满足 TC-B16-04）。
  - 无 `.gate-result.json`：`exit==1` → `FAIL` + rc 1（TC-B16-02）；否则 `PASS` + rc 0（`--no-verify` 场景）。
  - 有 `.gate-result.json`：`phase` / `exit_code` 与重跑不一致 → `FAIL` + rc 1；一致 → `PASS` + rc 0。
- **跳过面**（非 agate 项目 / 状态不可读 / 多任务歧义 / 非推进态 / 无 task_id / 无 `agate_common`）：`_skip()` 打印 `SKIP: <原因>` + 「本次未实际执行」块（TC-B16-03 要求「跳过」+ 原因可区分）。
- **平台无关**：不读任何 CI 平台环境变量（旧脚本的 `detect_ci_platform` 依赖已去除）。

### 2.2 `agate-doctor.py`（BDD-17，退出码固定）

- 四维度逐项诊断，异常项进「修复建议」清单（含可执行命令，如 `agate-config.py init` / `agate-setup.py --scope project`）。
- 声明文件经 `agate_common.read_project_config`（P2 §4.1 唯一读取函数），不另写 YAML 解析。
- 账本维度遍历 `{tasks_dir}/*/gate-events.jsonl`，逐行校验 `prev_hash` 链（首行 = `sha256(b"")`，后续 = `sha256(上一行原文)`）。
- 单维度异常被捕获为「诊断异常」行，**不使整体退出码漂移**；`main()` 恒 `return 0`（TC-B17-08）。

### 2.3 workflow（M15）

`gate-backstop` job 的 run step：`python3 agate/scripts/agate-ci-verify.py 2>&1 | tee /tmp/ci-verify.log`；`grep -q 'SKIP:'` 时输出 GitHub 注解 + job summary（保留 ADR-015 手段②「让跳过可见」的既有设计）。job 名 `gate-backstop` 未改（M15 只要求改调用脚本）。

## 3. `ci-gate-backstop` 去留决定：**删除（退役）**

- **判据**：BDD-16 写「替换 ci-gate-backstop」、P2 §1.1 M13 写「**替换**」、§4.4 写「改名/**退役**才触发 CHECK 10 方向」；P3 测试注释与 TC-B16-06 均以「退役」表述。⇒ 取**删除**，非「保留为 deprecated」。
- **同步面**（全部落地）：脚本本体 + 其测试；锚点表 / `uncovered_gate_scripts` extras / 锚点 callers；`agate-summary.py`；`README.md`；6 个协议文档 + `assets/formatters/README.md`；workflow。
- **`SCRIPT_REF_RE` 保留 `ci-gate-backstop\.py`**：作**退役名拦截**（协议文档回引 → ERROR；CHANGELOG 等叙事文件降级为已聚合的 WARNING，不新增 WARNING 计数）。

## 4. [DESIGN_GAP] 登记（交 P7 逐条审查）

[DESIGN_GAP: agate-ci-verify 调用接口 P2 §4.4 未固化；P4 按 P3 DESIGN_GAP-1 取「无参数 + cwd 定位（仓库根 .state.yaml 优先，其次任务级 .state.yaml）」，未采用 AGATE_TASK_DIR 注入点；多个任务级 .state.yaml 时判「歧义」并显式 SKIP（本仓 agate-workspace 即多任务 ⇒ 实际会 SKIP）——「如何唯一定位本仓待兜底任务」交 P7 裁决]
[DESIGN_GAP: agate-doctor 退出码语义 P2 仅写「退出码固定」；P4 按 P3 DESIGN_GAP-2 解释「成功 = 诊断正常完成」⇒ rc 恒 0（报告问题 ≠ 自身失败），与 TC-B17-08 一致；若设计意图为「发现异常即非 0」则须改 TC-B17-08，交 P7 裁决]
[DESIGN_GAP: 退役 backstop 的独立 P3 check-tdd-red 与 P6 provenance CI 层重跑未移植到 agate-ci-verify（BDD-16 只要求「实际重跑 gate 判定」，P3 契约 6 例只覆盖 gate 重跑 + 跳过可区分；P6.5 judge/events 已由 check-gate.py P6.5 覆盖）；「是否补回 provenance / P3-TDD-red 兜底」交 P7 裁决]
[DESIGN_GAP: 派发清单退役同步面未列 `agate/assets/formatters/README.md`，但它属 CHECK10-scan（PROTOCOL_DIRS）且引用退役名 ⇒ 若不改将新增 CHECK10 ERROR；P4 已同步（属退役同步，非新增需求）]
[DESIGN_GAP: workflow job 名保留 `gate-backstop`（M15 只要求改调用脚本）；「是否一并改名（如 ci-verify）」P2 未指定，交 P7 裁决]

## 5. 自跑结果（自查 ≠ gate）

- 目标用例：`/usr/bin/python3 -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_agate_doctor.py -q` → **14 passed**（改动前 14 failed）。
- 相邻回归：`test_check_gate.py` / `test_check_protocol_consistency.py` / `test_mvwu_protocol_docs.py` / `test_t43_check_registration_surface.py` / `test_protocol_alignment_review.py`（含 SG.6）/ `test_doc_sweep.py` / `test_agate_scripts_encoding.py` → **361 passed**。
- 全量单元：`pytest agate/tests/unit/ -q -n auto` → **1 failed, 2448 passed, 2 skipped**；唯一失败 `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` 为**既有环境失败**（本机 `opencode debug agent` 子命令已改名 `agents`，batch4 已登记），与本批无关。
- 回归 + 集成：`pytest agate/tests/regression/ agate/tests/integration/ -q -n auto` → **198 passed**。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **0 ERROR**；WARNING **406**（与改动前逐条一致，CHECK10-scriptref 未新增）。
- `python3 agate/scripts/check-structure-consistency.py` → S1-S6/S0 全 OK。
- `bash agate/tests/scripts/count-tests.sh` → **2671**（较 batch4 的 2689 减 18 = 删退役测试 17 + 删退役锚点测试 1；新增 BDD-16/17 的 14 例在 P3 已计入）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/` → All checks passed。
- 平台扫描新增脚本 + 改动测试文件 → **0 命中**（`agate-summary.py` 另有 5 处 `python3` 字面为**改动前既有**、且不在 CI 扫描面 `agate/tests/`，非本批引入）。
- 实跑 `agate-doctor.py`（本仓）：4 维度输出 + 修复建议，rc=0；21 个账本链完整。实跑 `agate-ci-verify.py`（本仓）：多任务 ⇒ 显式 SKIP + 原因，rc=0。

## 6. 残留（不在本批改动面，未改）

- `docs/guides/project-map.md`、`docs/reviews/*`、`archived/*`、`agate/UPGRADING.md`、`CHANGELOG.md`、`agate/tests/unit/test_check_tdd_red_formatter.py` 注释中的退役名：非 CHECK10-scan（docs/archived）或豁免（UPGRADING 整文件）/ 叙事（CHANGELOG）或测试注释，按设计不改。
