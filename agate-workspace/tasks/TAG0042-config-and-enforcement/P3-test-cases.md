---
phase: P3
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P3-20261005
agent: main-agent
test_code_dir: agate/tests/unit/
---
# P3 测试用例清单 — TAG0042（全批汇总）

> **本文件性质**：本任务 6 批（batch1–batch6）按「按包拆分并行」派发，P3 由 5 个
> test-designer subagent 各产出一份分包清单（`P3-test-cases-batch1..5.md`），本文件由
> **主 Agent 汇总**为单一 P3 产出（P3 卡「按包拆分并行」步 4：主 Agent 汇总后统一 commit）。
> 各分包细节以对应 `P3-test-cases-batchN.md` 为准，本文件给全批总览 + 22 条 BDD 的 1:1 映射。
>
> 本任务为 **TDD 红灯批**：测试先于实现，当前全部红灯（B 类 = 被测模块/结构/行为未实现）。

> **`test_code_dir`**：`agate/tests/unit/`（本文件 frontmatter 声明，与各分包同源）。

## 1. 测试文件总览

| 批 | 测试文件（`agate/tests/unit/`） | 覆盖 BDD | 用例数 | 分包清单 |
|---|---|---|---|---|
| batch1-phase-semantics | `test_tag0042_batch1_phase_semantics.py` | BDD-1 / BDD-2 | 6 | `P3-test-cases-batch1.md` |
| batch2-agate-config | `test_agate_config.py` + `test_config_schema.py` | BDD-3/4/5/6/7/8 + BDD-20（批 2 面） | 22 | `P3-test-cases-batch2.md` |
| batch3-agate-run | `test_agate_run.py` + `test_events_ledger.py` | BDD-9/10/11/12 | 15 | `P3-test-cases-batch3.md` |
| batch4-gate-layer | `test_gate_layer.py` + `test_check_p8_delivery.py` | BDD-14/15/21 | 8 | `P3-test-cases-batch4.md` |
| batch5-ci-doctor | `test_agate_ci_verify.py` + `test_agate_doctor.py` | BDD-16/17 | 14 | `P3-test-cases-batch5.md` |
| batch6-obligations | （无新增红灯测试，见 §5） | BDD-13/18/19 | — | — |
| **合计** | **9 个测试文件** | | **65** | |

> batch1 与 batch6 的 `tests_filter` 指向**既有真实测试**（batch1 tracer bullet；batch6 的 SG.6），
> batch2–5 的 `tests_filter` 为「P3 产出后生效」（P2-design §6.1b）。本汇总的 65 条新增用例
> 即 batch1–5 的交付面。

## 2. BDD → 测试用例映射（全 22 条 1:1）

| BDD | 主题 | 批 | 覆盖用例 | 状态 |
|---|---|---|---|---|
| BDD-1 | agate-next 推进时不预写下一阶段 | batch1 | TC-B1-01/02 | 新增红灯 |
| BDD-2 | phase 语义与卡片表述一致 | batch1 | TC-B2-01..04 | 新增红灯 |
| BDD-3 | 项目形态由声明文件描述，不写死技术栈 | batch2 | TC-B3-01..03 | 新增红灯 |
| BDD-4 | agate-config 子命令完整读写能力 | batch2 | TC-B4-01..03 | 新增红灯 |
| BDD-5 | 声明 schema 校验拒绝非法形态 | batch2 | TC-B5-01..04 | 新增红灯 |
| BDD-6 | 唯一读取函数保证声明单源 | batch2 | TC-B6-01..04 | 新增红灯 |
| BDD-7 | setup/install-hook 自动 init 声明 | batch2 | TC-B7-01..03 | 新增红灯 |
| BDD-8 | 声明缺失时行为不变 + WARNING（迁移期） | batch2 | TC-B8-01..03 | 新增红灯 |
| BDD-9 | agate-run 在不可绕开路径执行项目命令 | batch3 | TC-B9-01..04 | 新增红灯 |
| BDD-10 | agate-run 产出可比对基线证据 | batch3 | TC-B10-01..03 | 新增红灯 |
| BDD-11 | agate-run 证据文件被 ignore 检查覆盖 | batch3 | TC-B11-01/02 | 新增红灯 |
| BDD-12 | agate-run 写 cmd_run 事件且不破坏哈希链 | batch3 | TC-B12-01..06 | 新增红灯 |
| BDD-13 | check-obligations 完成登记面（SG.6 转绿） | batch6 | 既有 `test_protocol_alignment_review.py -k sg_6` | 复用既有（见 §5） |
| BDD-14 | 关卡层按提交类型分级（含 `paused_from`） | batch4 | TC-B14-01/02 | 新增红灯 |
| BDD-15 | P8 交付收尾且 `delivery` 必须声明 | batch4 | TC-B15-01..03 | 新增红灯 |
| BDD-16 | agate-ci-verify 替换 backstop 且无假绿 | batch5 | TC-B16-01..06 | 新增红灯 |
| BDD-17 | agate-doctor 诊断接入状态 + 修复指引 | batch5 | TC-B17-01..08 | 新增红灯 |
| BDD-18 | obligations.yaml 登记 160 项三态归宿 | batch6 | （见 §5） | 前置输入缺口 |
| BDD-19 | 义务登记表 M 类占比不得下降 | batch6 | （见 §5） | 前置输入缺口 |
| BDD-20 | 不引入只适用于单一项目的规则 | batch2 起（每批 R6 差分） | TC-B20-01/02（批 2 面，设计层收窄断言） | 新增红灯 |
| BDD-21 | 删发版逻辑前先提供等价 preset | batch4 | TC-B21-01..03 | 新增红灯 |
| BDD-22 | 每批遵守协议语义不回退（横切） | 各批 | 既有回归套件 + P5 全量 | 无独立用例（见 §5） |

## 3. 红灯基线（全量自跑）

```
python3 -m pytest \
  agate/tests/unit/test_tag0042_batch1_phase_semantics.py \
  agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py \
  agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py \
  agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py \
  agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_agate_doctor.py -q
→ 65 failed in 1.73s
```

65 条全部失败，失败原因均为 **AssertionError / 文件缺失 / AttributeError**——属「被测模块 / 结构 /
行为未实现」（B 类）：`agate-config.py` / `agate-run.py` / `agate-ci-verify.py` / `agate-doctor.py`
不存在、`read_project_config` 不存在、`project-config.schema.json` 不存在、phases.yaml 无提交类型
分级/`paused_from`、gate_p8 无 `delivery` 拦截、`agate-next` 仍预写下一阶段、hook 无账本暂存。
**非 SyntaxError、非第三方 import 失败**（A 类，collection 无 error，各分包已 grep 确认 0 命中）。

**`check-tdd-red.py` 确认**（主 Agent 亲跑，gate_commands.P3 = `python3 -m pytest`）：

```
python3 agate/scripts/check-tdd-red.py agate-workspace/tasks/TAG0042-config-and-enforcement
→ exit 0（TDD_CHECK: red-light）
```

## 4. 平台假设扫描

```
python3 {agate_root}/scripts/check-platform-assumptions.py <9 个新增测试文件>  → exit 0（0 命中）
python3 {agate_root}/scripts/check-platform-assumptions.py agate/tests/unit/   → exit 0（0 命中）
```

测试平台无关实现要点（各分包一致）：用 `tmp_path` / `task_dir` / `git_repo` fixtures；
`run_cli(python_exe, ...)`（不裸 `python3`）；全文本 I/O 显式 `encoding="utf-8"`；
需「系统临时目录」字面量时运行时拼接（`TMP = "/" + "tmp"`，注释亦不写字面量）；
**不写仓库内已提交文件**（尤其 `gate-events.jsonl` 账本——账本断言全在 `tmp_path` 副本上；
doctor/install-hook 类写台账的用例把 `AGATE_HOME` 钉到 `tmp_path` 隔离目录）。

## 5. batch6 与横切 BDD 的覆盖说明

- **BDD-13**（check-obligations 登记面）：由**既有** `agate/tests/integration/test_protocol_alignment_review.py -k sg_6`
  守护（P2-design §6.1b batch6 `tests_filter` = 既有文件）。该测试当前为绿（`check-obligations.py`
  尚未加入）；批 6 加入该脚本后**须登记进 CHECK 9 锚点表**使其保持绿（BDD-13 的验收即此）。
- **BDD-18 / BDD-19**（obligations.yaml 160 项三态 + M 类占比）：**P3 无新增红灯测试**——
  其前置输入「160 项义务逐条清单」**不在仓库**（P0-brief §四、P2 §10 已登记为批 6 前置输入缺口），
  P3 无法写内容级断言。批 6 落地后由**门禁脚本 `check-obligations.py` 自身**（进锚点表 + SG.6）
  在 P5/P6 直接执行判定；届时若前置输入仍缺则批 6 前置不足而阻塞（不影响批 1–5）。
  ⇒ 登记为**已知覆盖缺口**，交 P6/P7 核。
- **BDD-22**（横切：每批不回退）：无独立用例——由既有回归套件 + P5 全量回归承担（各分包派发指引已明确）。

## 6. DESIGN_GAP 汇总（交 P4/P7 核）

| # | 位置 | 内容 |
|---|---|---|
| 1 | TC-B14-01 | 批 4 转换表矩体键名设计未定（P2 §11 已预留）⇒ 断言键名无关的结构扫描；P4 若采用不同表示法须标 `[DESIGN_GAP]` 并对齐 |
| 2 | TC-B15-03 | P8 名称精确措辞 + `delivery` 合法取值集未定 ⇒ 只断言语义方向 |
| 3 | TC-B21-03 | 发版痕迹 WARNING 的消费入口与措辞未定 ⇒ 只断言输出可观察到主题 |
| 4 | batch5 [DESIGN_GAP-1] | `agate-ci-verify` 调用接口未固化 ⇒ 测试按「无参数 + cwd 定位 + 兼容任务级 `.state.yaml`」设计 |
| 5 | batch5 [DESIGN_GAP-2] | `agate-doctor` 退出码语义未精确化 ⇒ 本批解释为「诊断正常完成 → rc=0」 |
| 6 | batch5 [DESIGN_GAP-3] | 「跳过/通过可区分」具体标识未固化 ⇒ 只要求存在「跳过」标识 + 原因文本 |

> `delivery` / `paused_from` 是 BDD 明列字面，**不属**设计未定面（未作 DESIGN_GAP 处理）。

## 7. 与实现对象的关系（供 P4）

- batch1：`agate/scripts/agate-next.py::_advance()`（去预写 + 去 `git add`）+ 卡片/UPGRADING 对齐。
- batch2：`agate/scripts/agate-config.py`（新增）、`rules/schema/project-config.schema.json`（新增）、
  `agate_common.read_project_config()`（新增唯一读取函数）、`agate-setup.py` / `install-hook.py`（自动 init）、
  `check-gate.py::gate_p0`（调 validate，迁移期恒 return 2）、`UPGRADING.md`。
- batch3：`agate/scripts/agate-run.py`（新增，`--baseline` / `.out` 证据 / `git check-ignore` / 平台分支）、
  `agate_common.append_event`（唯一写路径）、`pre-commit-gate.py`（hook 一并暂存账本）。
- batch4：`agate/rules/phases.yaml`（提交类型分级 + 转换表含 `paused_from`）、
  `check-gate.py::gate_p8`（`delivery` 校验）、`phase-cards/P8-release.md`、`UPGRADING.md`。
- batch5：`agate/scripts/agate-ci-verify.py`（新增，替换 `ci-gate-backstop.py`）、
  `agate/scripts/agate-doctor.py`（新增）、`.github/workflows/protocol-tests.yml`（改调新脚本 +
  CHECK10-scriptref 引用同步）。
- batch6：`agate/scripts/check-obligations.py`（新增，进 CHECK9 锚点表）、`agate/rules/obligations.yaml`（新增）、
  `check-protocol-consistency.py`（加锚点）。

## 8. 边界与不做

- P3 只写测试，不写实现（实现是 P4）。
- 各分包只覆盖本批 BDD，不跨批。
- 不写仓库内已提交文件（尤其 `gate-events.jsonl` 账本）——所有断言均在 `tmp_path` / `git_repo` 内。
