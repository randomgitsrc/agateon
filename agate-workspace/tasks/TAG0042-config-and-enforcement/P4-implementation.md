---
phase: P4
task_id: TAG0042
type: implementation
parent: P3-test-cases.md
status: draft
implementation_dir: agate/
agent: implementer
---

# P4 实现记录（聚合主文件）— TAG0042 项目形态命令化 + 规则脚本化

> 本文件是 P4 阶段的**主实现记录**（聚合主文件）。6 个批次各自产出
> `P4-implementation-batch1..6.md` 并分别 commit，本文件汇总：任务摘要 + 各批一览 +
> 新增文件核对表 + DESIGN_GAP 汇总。
> 下游消费：`check-gate.py` P7 的 DESIGN_GAP 转抄核对 / `check-judge-verdict.py` 白名单 /
> `agate-extract-context.py` 的 `implementation_dir`。
> 自查 ≠ gate：本文只做机械汇总，不预判 P5/P6/P7/P8 gate 结论。

## 1. 任务摘要

**TAG0042 = 项目形态命令化 + 规则脚本化**：把「项目形态」（技术栈 / 验证命令 / 发布方式）
从协议硬编码改为**项目根声明**驱动，并把一批阶段义务从「靠记忆」收敛到「不可绕开路径上的
脚本判定」，同时为「判断类义务」保留**强制独立评审**归宿。

P2 采用 `dispatch_plan.mode: serial`（**串行链**，模式 5），6 批有强依赖链（批 2 依赖批 1、
批 3 依赖批 2…），逐批派发、每批 gate 通过后派下一批；`parallel_limit: 3` 仅作并行上限登记。
批数与 P0-brief §二范围表逐条对应（批 1-6）。批切分按**业务能力**（Vertical Slice）：
声明能力 / 执行能力 / 关卡分级能力 / CI 诊断 / 义务登记。

## 2. 各批一览

| 批 id | 主题 | 落点文件（主要） | 对应批文件 | 对应 evidence 日志 |
|---|---|---|---|---|
| `batch1-phase-semantics` | 统一 phase 语义（`agate-next` 不预写 + 权威文档同步） | `agate/scripts/agate-next.py`、`agate/phase-cards/P2-design.md`、`agate/phase-cards/P8-release.md`、`agate/UPGRADING.md` + 5 处权威文档改述 | `P4-implementation-batch1.md` | `P4-evidence/batch1-phase-semantics.log` |
| `batch2-agate-config` | 声明层（`agate-config` + schema + 唯一读取函数 + init + gate_p0 validate） | `agate/scripts/agate-config.py`（新）、`agate/rules/schema/project-config.schema.json`（新）、`agate/scripts/agate_common.py`、`agate/scripts/install-hook.py`、`agate/scripts/agate-setup.py`、`agate/scripts/check-gate.py::gate_p0` | `P4-implementation-batch2.md` | `P4-evidence/batch2-agate-config.log` |
| `batch3-agate-run` | 执行层（`agate-run` + `.out` 证据 + `cmd_run` 事件 + hook 暂存账本） | `agate/scripts/agate-run.py`（新）、`agate/scripts/pre-commit-gate.py` + 2 处账本事件枚举改述 | `P4-implementation-batch3.md` | `P4-evidence/batch3-agate-run.log` |
| `batch4-gate-layer` | 关卡层分级 + P8 交付收尾 + `preset` 等价物 | `agate/rules/phases.yaml`、`agate/rules/schema/phases.schema.json`、`agate/scripts/check-gate.py::gate_p8`、`agate/phase-cards/P8-release.md`、`agate/WORKFLOW.md`、`agate/UPGRADING.md` + 6 处 P8 叙事同步 | `P4-implementation-batch4.md` | `P4-evidence/batch4-gate-layer.log` |
| `batch5-ci-doctor` | CI 与诊断（`agate-ci-verify` 替换 backstop + `agate-doctor`） | `agate/scripts/agate-ci-verify.py`（新）、`agate/scripts/agate-doctor.py`（新）、`.github/workflows/protocol-tests.yml`、退役同步面（删 `ci-gate-backstop.py` + 其测试 + 锚点/README/文档） | `P4-implementation-batch5.md` | `P4-evidence/batch5-ci-doctor.log` |
| `batch6-obligations` | 义务登记表（`obligations.yaml` + `check-obligations` 进锚点表） | `agate/rules/obligations.yaml`（新）、`agate/scripts/check-obligations.py`（新）、`agate/scripts/check-protocol-consistency.py` | `P4-implementation-batch6.md` | `P4-evidence/batch6-obligations.log` |

> 各批 `tests_filter` / `output` 权威值见 `P2-design.md` §6.1b；evidence 日志格式见 P4 卡
> 「批级证据 P4-evidence」（逐行 `key: value`，机械转录）。

## 新增文件核对表

> CODE-MAP 机制已采用（`agate-workspace/agents/CODE-MAP.md` 存在）；`P2-skeleton.md` 不存在
> （无骨架机制，故「骨架归属」列统一标 `within <dir>`，不涉及 `[SKELETON_DEVIATION]`）。
> 本表覆盖本任务在 `implementation_dir: agate/` 下新增的全部文件（协议/脚本 + 测试脚手架）。

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/scripts/agate-config.py` | `within agate/scripts` | `[CODE_MAP_UPDATED]`（scripts 模块「项目声明族」，批 2） |
| `agate/rules/schema/project-config.schema.json` | `within agate/rules/schema` | `[CODE_MAP_UPDATED]`（rules 模块 `schema/*.json` 泛化覆盖 + scripts「项目声明族」条目记其消费方，批 2） |
| `agate/scripts/agate-run.py` | `within agate/scripts` | `[CODE_MAP_UPDATED]`（scripts 模块「执行层族」，批 3） |
| `agate/scripts/agate-ci-verify.py` | `within agate/scripts` | `[CODE_MAP_UPDATED]`（批 5；⚠️ 见下方核对说明） |
| `agate/scripts/agate-doctor.py` | `within agate/scripts` | `[CODE_MAP_UPDATED]`（批 5；⚠️ 见下方核对说明） |
| `agate/rules/obligations.yaml` | `within agate/rules` | `[CODE_MAP_UPDATED]`（scripts 段「义务登记族」登记 rules 数据面，批 6） |
| `agate/scripts/check-obligations.py` | `within agate/scripts` | `[CODE_MAP_UPDATED]`（scripts 段「义务登记族」，批 6） |
| `agate/tests/unit/test_agate_config.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_config_schema.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_agate_run.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_events_ledger.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_gate_layer.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_check_p8_delivery.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_agate_ci_verify.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_agate_doctor.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |
| `agate/tests/unit/test_tag0042_batch1_phase_semantics.py` | `within agate/tests/unit` | `[CODE_MAP_EXEMPT: 纯测试脚手架，不改 CODE-MAP]` |

**核对说明（据实，交 P7 核对）**：实测 `agate-workspace/agents/CODE-MAP.md` 已含批 2 / 批 3 /
批 6 的新增条目（`agate-config.py` / `project-config.schema.json` / `agate-run.py` /
`obligations.yaml` / `check-obligations.py`）；但**未见批 5 的 `agate-ci-verify.py` /
`agate-doctor.py` 条目**（批 5 提交 `082aba3` 未改 `CODE-MAP.md`，其退役对象
`ci-gate-backstop.py` 亦未在 `CODE-MAP.md` 登记）。本聚合文件仅新建自身、不改其它文件，
故两行按派发指引口径标 `[CODE_MAP_UPDATED]`，缺口在此如实标注——**交 P7 以
`[CODE_MAP_DRIFT:]` 核对**。

## DESIGN_GAP 汇总

> 来源：`P4-implementation-batch1..6.md` 的全部 `[DESIGN_GAP]` 条目，逐条以行首
> `- [DESIGN_GAP: ...]` 重列（P7 gate 按 `count_design_gap(allow_blockquote=False)` 口径计数做
> 转抄核对）。每条保留来源批号 + 简短描述。**共 25 条**（batch1=2 / batch2=4 / batch3=2 /
> batch4=6 / batch5=5 / batch6=6）。

- [DESIGN_GAP: batch1 — P2 §1.1 M3 只说「UPGRADING.md 新增批 1 行为变更记载」，未指定版本节标题；实现自主采用 `### v0.79.0`（当前 badge v0.78.3 的下一 minor），P8 发版时若版本号不同需同步。]
- [DESIGN_GAP: batch1 — P2 §1.1 M1 只点名去除 `_advance` 的预写 + `git add`，未指明其孤儿辅助函数；实现自主删除仅服务该路径的 `_write_state()` / `_git()`（避免死代码），并保留 `_advance` 的 `repo_root` 形参以兼容既有调用点。]
- [DESIGN_GAP: batch2 — P2 §4.1 正文一句写「迁移期 validate 对文件缺失只输出 WARNING 返回 0」，与同节 N2 伪代码（validate rc≠0 才触发 gate_p0 的 WARNING）及 P3 用例 TC-B8-01/02 矛盾；实现按 N2 伪代码与 P3 用例：validate 对缺失/非法返回非 0，gate_p0 吸收为 WARNING 且恒 return 2。]
- [DESIGN_GAP: batch2 — P2 未指定 `agate-config validate` 的 schema 校验实现方式；实现自主采用脚本内 draft-07 子集递归校验（标准库 + 数据驱动，不引入 jsonschema 依赖），未复用 `check-yaml-schema.py`（其为 `check-*.py` 且带 `if __name__` 侧效应，导入成本高于本批所需）。]
- [DESIGN_GAP: batch2 — P2 §1.1 M7 未指定 install-hook 自动 init 的实现路径；实现自主选择「子进程调 agate-config init」而非在安装器内联模板，以保持声明模板的唯一实现（与 BDD-6 单源精神一致）。]
- [DESIGN_GAP: batch2 — P2 §4.1 要求 read_project_config 对缺字段填默认值，同时 §1.1 M5 schema 声明 required；validate 只经该唯一读取函数取值（TC-B6-04 禁旁路解析），故拿到的是已注入默认值的 dict，required 字段在当前声明结构下恒满足（required 判据不触发）；实现按 P2 保留默认注入（最小实现），未额外暴露「已声明键集合」以驱动 required。]
- [DESIGN_GAP: batch3 — P2 §4.2 / M10 列有「修正 formatter 计数」，但未指明缺陷、落点或判据，且 P3 未写任何覆盖该点的用例（无对应 BDD）；实现前查明仓库内无一处存在可复现缺陷（改动 `_fallback_json` 计数将改变 TDD 判定路径，违反 P2 §1.2 N3「不改 TDD 判定语义」），故本批未做该项变更，留待主 Agent 裁决落点。]
- [DESIGN_GAP: batch3 — P2 §4.2 写 `agate-run <cmd-key|命令>`，但 `project-config.schema.json` 的 `verify.commands` 为字符串数组、无命名 key；实现将 CLI 实参按声明中的命令文本精确匹配解析，并以该命令在数组中的下标作为证据槽位 key（`cmd-<n>.out`）——下标在命令文本变更后稳定，使 BDD-10-03 成立；若后续需命名 key，须先扩展 schema。]
- [DESIGN_GAP: batch4 — 批 4「提交类型 → 关卡集合」的具体成员与转换表属 P2 §11 预留的设计未定面；P4 落定 code-only=全链 / docs-only=[P0,P1,P2,P7,P8] / release=[P7,P8]；P7 逐条审查。]
- [DESIGN_GAP: batch4 — phases.schema.json 不在 §6.1b batch4 output 列，但 phases.yaml 新增顶层键在 additionalProperties:false 下必须同步 schema（P2 §1.1 M11 已条件预见）；P4 已扩展，交 P7 核对。]
- [DESIGN_GAP: batch4 — WORKFLOW.md 不在 §6.1b batch4 output 列，但 S-1（YAML↔WORKFLOW 名称一致）强制同步 P8 行名称；P4 已同步，交 P7 核对。]
- [DESIGN_GAP: batch4 — delivery 合法取值集合设计未定；gate_p8 只查留痕存在（`"delivery:"` 子串），内容任意放行；P7 裁决是否收紧取值校验。]
- [DESIGN_GAP: batch4 — 发版逻辑消费方散布于判定脚本/数据面/卡片/角色/叙事/CI 六面；本批只提供 preset 等价物 + WARNING，未删除任何发版逻辑；「是否/何时删除、收敛顺序」交 P7 裁决（截止版本 v0.80.0 已写 UPGRADING）。]
- [DESIGN_GAP: batch4 — P8 叙事面（state-machine.md「P8 是发布准备」节、dispatch-protocol.md P8→READY 表、role-system.md、implementer.md）仍写「发布准备」，不在 §6.1b batch4 output 列，P2 未指定是否随名称改述；本批只改 phases.yaml/WORKFLOW/卡片，P7 裁决是否统一叙事。]
- [DESIGN_GAP: batch5 — agate-ci-verify 调用接口 P2 §4.4 未固化；P4 取「无参数 + cwd 定位（仓库根 .state.yaml 优先，其次任务级 .state.yaml）」，未采用 AGATE_TASK_DIR 注入点；多个任务级 .state.yaml 时判「歧义」并显式 SKIP（本仓多任务 ⇒ 实际会 SKIP）——「如何唯一定位本仓待兜底任务」交 P7 裁决。]
- [DESIGN_GAP: batch5 — agate-doctor 退出码语义 P2 仅写「退出码固定」；P4 按 P3 DESIGN_GAP-2 解释「成功 = 诊断正常完成」⇒ rc 恒 0（报告问题 ≠ 自身失败），与 TC-B17-08 一致；若设计意图为「发现异常即非 0」则须改 TC-B17-08，交 P7 裁决。]
- [DESIGN_GAP: batch5 — 退役 backstop 的独立 P3 check-tdd-red 与 P6 provenance CI 层重跑未移植到 agate-ci-verify（BDD-16 只要求「实际重跑 gate 判定」，P3 契约 6 例只覆盖 gate 重跑 + 跳过可区分；P6.5 judge/events 已由 check-gate.py P6.5 覆盖）；「是否补回 provenance / P3-TDD-red 兜底」交 P7 裁决。]
- [DESIGN_GAP: batch5 — 派发清单退役同步面未列 `agate/assets/formatters/README.md`，但它属 CHECK10-scan（PROTOCOL_DIRS）且引用退役名 ⇒ 若不改将新增 CHECK10 ERROR；P4 已同步（属退役同步，非新增需求）。]
- [DESIGN_GAP: batch5 — workflow job 名保留 `gate-backstop`（M15 只要求改调用脚本）；「是否一并改名（如 ci-verify）」P2 未指定，交 P7 裁决。]
- [DESIGN_GAP: batch6 — 外部审计的 160 项逐条清单不在仓库（P0-brief §四）⇒ 本次按 P0-brief fallback 从协议本体重新盘点，得 123 条（M60/C33/R30），与外部 160 项（M38/C29/N70）不可逐条对齐；差异原因见 batch6 §2.3（分类语义 M/C/R vs M/C/N、颗粒度、不可绕开路径判据更宽）——条目边界由本次盘点定义，交 P7 裁决是否可接受。]
- [DESIGN_GAP: batch6 — 三态归宿 M/C/R 的判定边界 P2 §4.5 未逐条定义；P4 自主判定——M=脚本在不可绕开路径（pre-commit/check-gate/check-*.py 门禁）执行，C=有命令但依赖主 Agent 记得运行，R=判断类交强制独立评审；此边界为本次实现决策，交 P7 裁决。]
- [DESIGN_GAP: batch6 — 外部审计第三态 N「无任何脚本」在三态归宿中归 R（强制评审）——BDD-18 要求「无『无归宿』项」，而 P0-brief「不为判断类义务强行脚本化，那些交给强制评审」支持 N→R；但「现状无脚本」与「归宿为强制评审」是否等价，P2 未明确，交 P7 裁决。]
- [DESIGN_GAP: batch6 — 基线 M 占比 0.4878 由本次重新盘点自定（`baseline: {m: 60, total: 123}`），与外部审计 24% 不可比；基线一旦写入，后续只增不减——基线取值的合理性交 P7 裁决。]
- [DESIGN_GAP: batch6 — check-obligations.py 的协议根解析取「AGATE_ROOT env → 脚本相对协议根 → cwd」，未用 `agate_common.resolve_agate_root`——因 v0.73.0 版本布局后稳定版（~/.agate/current）与开发 checkout 解耦，resolve_agate_root 会解析到稳定版目录而扫不到本 checkout 的登记表；该解析口径 P2 未指定，交 P7 裁决。]
- [DESIGN_GAP: batch6 — check-obligations.py 无独立 P3 红灯测试（P3 批 6 的 tests_filter 用既有 SG.6），BDD-18/19 的专门用例未由 P3 产出；P4 已用合成树手工验证两类负向，「是否补正式回归测试」交 P7 裁决。]

## 自查（自查 ≠ gate）

| 验证项 | 命令 | 结果 |
|---|---|---|
| DESIGN_GAP 总数（各批） | `grep -o '\[DESIGN_GAP:' P4-implementation-batch{1..6}.md \| wc -l` 合计 | 25（batch1=2 / batch2=4 / batch3=2 / batch4=6 / batch5=5 / batch6=6） |
| 本文 DESIGN_GAP 行首条数 | `grep -c '^- \[DESIGN_GAP:' P4-implementation.md` | 25（≥ 各批总数，逐批核对无遗漏） |
| P4 gate | `python3 agate/scripts/check-gate.py P4 agate-workspace/tasks/TAG0042-config-and-enforcement` | 见主 Agent 运行结果（本聚合文件补齐「## 新增文件核对表」标题后，CODE-MAP WARNING 应消失，不新增 ERROR） |
