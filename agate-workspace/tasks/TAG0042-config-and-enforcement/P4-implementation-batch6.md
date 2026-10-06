---
phase: P4
task_id: TAG0042
agent: implementer
implementation_dir: agate/
---

# P4 实现 — batch6-obligations（义务登记表：obligations.yaml + check-obligations）

> 范围：仅 BDD-13 / BDD-18 / BDD-19（P2 §1.1 M16/M17/M18、§1.4、§4.5、§6.1b `batch6-obligations`、§10、§12 第 6 条）。
> 不碰 batch1-5 已落实现。自查 ≠ gate：本文只报自跑结果，**不预判 P5 gate 结论**。

## 1. 改动清单（文件 → 落点）

| 文件 | 落点 | 对应 |
|---|---|---|
| `agate/rules/obligations.yaml` | **新增**：阶段义务三态归宿登记表（schema_version + baseline + 123 条义务，每条含 id/phase/statement/anchor/disposition/script/evidence） | BDD-18 / M16 |
| `agate/scripts/check-obligations.py` | **新增**（`check-*.py` 门禁面）：读登记表，校验无「无归宿」项 + M 类占比 ≥ 基线 + 每条有可追溯锚点；有 exit code（0/1/2） | BDD-18/19 / M17 |
| `agate/scripts/check-protocol-consistency.py` | `SCRIPT_ALIGNMENT_ANCHORS` 加 `check-obligations.py` 锚点（keywords 定值 `["obligations.yaml", "M 类占比", "无归宿"]`）——承载判定逻辑进锚点表，使 CHECK9-coverage 无新增 WARNING、SG.6 转绿 | BDD-13 / M18 |
| `agate/scripts/README.md` | 「Gate 检查」表新增 `check-obligations.py` 索引行（约定） | 登记面 ④ |
| `agate/tests/README.md` | 新增「脚本 → 测试文件」映射行（`check-obligations.py` → SG.6 登记面守护；**不写用例数**） | 登记面 ⑤ |
| `agate-workspace/agents/CODE-MAP.md` | scripts 段新增「义务登记族（TAG0042 批 6）」行（新增协议文件的 CODE-MAP 同步） | P4 卡新增文件核对表 |

## 2. 重新盘点口径说明（前置输入缺口处理）

### 2.1 为什么重新盘点

外部审计的「160 项阶段义务逐条清单」**不在仓库**（P0-brief §四、P2 §10、`docs/reviews/handoff-tag0042-batch0-for-expert-review.md` 均确认「须向评审索取该表并入库」）。本批按 **P0-brief 记录的 fallback「没有就得重新盘点」**：由 P4 从协议本体重新盘点，**每条义务带可追溯来源锚点**。

### 2.2 条目数与分类（本次实测）

- **条目数：123 条**（`obligations:` 列表长度，`check-obligations.py` 实跑输出 `M=60 C=33 R=30`）。
- **三态归宿**：
  - **M（脚本执行）60**：脚本在**不可绕开路径**执行（pre-commit hook / `check-gate.py` / `check-*.py` 门禁）。
  - **C（命令生成）33**：有可判定命令/脚本，但**依赖主 Agent 记得运行**（非必经路径），如 `gate_commands.P5`、`check-tdd-red.py`、`check-p6-provenance.py --audit7-only`、grep 类门槛。
  - **R（强制评审）30**：判断类义务，由**强制独立评审**承载（requirements-review / plan-eng-review / review / design-review / cso / judge / consistency-reviewer）；脚本强制的只是「该评审必须出现」（agent≠main / status==approved）。
- **基线 M 占比：60/123 = 0.4878**（`baseline: {m: 60, total: 123}`，整数交叉相乘比对，只增不减）。

### 2.3 与外部审计 160 项的差异（属 DESIGN_GAP，见 §4）

| 口径 | 外部审计（P0-brief §一） | 本次重新盘点 |
|---|---|---|
| 总量 | 160 | 123 |
| 分类维度 | 三态**现状**：M38 / C29 / **N70**（无任何脚本） | 三态**归宿**：M60 / C33 / R30 |
| M 占比 | 38/160 ≈ 24% | 60/123 ≈ 48.8% |

差异来源（不编造，据实说明）：

1. **分类语义不同**：外部审计的第三态是 **N「无任何脚本」（现状）**；本次按派发要求归入**三态归宿 M/C/R**，且 BDD-18 要求「无『无归宿』项」⇒ 原 N 类（判断类）归 **R（强制评审）**。二者不是同一坐标系。
2. **颗粒度不同**：本次把每个阶段的 gate 条件、每条 pre-commit 检查、每条状态机纪律**逐条**登记（如 P1 拆 14 条、横切拆 28 条）；外部审计为更粗粒度的汇总。
3. **「不可绕开路径」判据更宽**：凡由 pre-commit hook / `check-gate.py` / `check-*.py` 在提交路径上判定的，本次计 M（如 `.state.yaml` 格式、状态转移、PROD_TOUCHED、P6 provenance、CHANGELOG）——外部审计可能只对其中一部分计 M。
4. **前置清单缺失**：外部逐条表不可得，本次**从协议原文重新建立**，条目边界由本次盘点定义，**不作逐字对齐承诺**。

> 结论：本次条目数与 M 占比**与外部审计不同属预期**，以协议原文为准；差异已如实登记为 DESIGN_GAP，交 P7 逐条审查。

### 2.4 来源锚点方式

每条义务的 `anchor` 指回协议原文，采用**稳定节/键锚点**（不写必然漂移的行号）：

- md 文件：`<file>#<节标题>`（如 `agate/phase-cards/P1-requirements.md#gate 规则`、`agate/WORKFLOW.md#Pre-commit 检查总览`、`agate/state-machine.md#状态机定义`）。
- 数据面：`agate/rules/phases.yaml#<阶段>.<outputs|gates|task_fields>`（如 `agate/rules/phases.yaml#P6.gates`）。

盘点来源：`agate/WORKFLOW.md`、`agate/phase-cards/*.md`、`agate/rules/phases.yaml`、`agate/rules/{review-mapping,state-transitions}.md`、`agate/dispatch-protocol.md`、`agate/state-machine.md`。

### 2.5 现有脚本 / 失败证据

- `script` 字段登记现有脚本（如有），如 `agate/scripts/check-gate.py` / `check-p6-provenance.py` / `check-state-transition.py`。
- `evidence` 字段登记**失败证据**（如有），均取自本仓已记录的实测事故，**未编造**：T046（用 DOM 属性替代视觉验证 / 凑 PASS 格式）、T005（P8 subagent 把 1 failed 标 ✅）、TAG0009（环境问题错标 supplementable 致 11.7 小时）、TAG0016（执行命令未开 pipefail 吞退出码）、TAG0025（隐含扩展未授权）、TAG0036 M18（凭推理判『不处理』被实测证伪）、DEBT0046/0048、peekview T085（预写冲突致 8 次 --no-verify）、X1/X3（批 0 已修的 PROD_TOUCHED / 假绿）。

## 3. check-obligations.py 判定逻辑

- **读登记表**：定位协议根（`AGATE_ROOT` env → 脚本相对协议根 → cwd）→ `rules/obligations.yaml`。
- **无「无归宿」项**：每条义务 `disposition ∈ {M, C, R}`；缺失/非法 → 收集为「无归宿」项 → FAIL。
- **M 类占比 ≥ 基线**：`current_m * baseline_total >= baseline_m * current_total`（整数交叉相乘，避免浮点舍入）→ 否则 FAIL。
- **可追溯**：每条义务 `anchor` 与 `statement` 非空，否则 FAIL。
- **exit code**：0 = 通过；1 = 不通过（无归宿项 / M 类占比低于基线 / 缺锚点）；2 = 目标/YAML/baseline 错误。
- **锚点关键词**：脚本文本**字面含** `obligations.yaml` / `M 类占比` / `无归宿`（CHECK9-align 判据）。

## 4. [DESIGN_GAP] 登记（交 P7 逐条审查）

[DESIGN_GAP: 外部审计的 160 项逐条清单不在仓库（P0-brief §四）⇒ 本次按 P0-brief fallback 从协议本体重新盘点，得 123 条（M60/C33/R30），与外部 160 项（M38/C29/N70）**不可逐条对齐**；差异原因见 §2.3（分类语义 M/C/R vs M/C/N、颗粒度、不可绕开路径判据更宽）——条目边界由本次盘点定义，交 P7 裁决是否可接受]
[DESIGN_GAP: 三态归宿 M/C/R 的判定边界 P2 §4.5 未逐条定义；P4 自主判定——M=脚本在不可绕开路径（pre-commit/check-gate/check-*.py 门禁）执行，C=有命令但依赖主 Agent 记得运行，R=判断类交强制独立评审。此边界为本次实现决策，交 P7 裁决]
[DESIGN_GAP: 外部审计第三态 N「无任何脚本」在三态归宿中归 R（强制评审）——BDD-18 要求「无『无归宿』项」，而 P0-brief「不为判断类义务强行脚本化，那些交给强制评审」支持 N→R；但「现状无脚本」与「归宿为强制评审」是否等价，P2 未明确，交 P7 裁决]
[DESIGN_GAP: 基线 M 占比 0.4878 由本次重新盘点自定（`baseline: {m: 60, total: 123}`），与外部审计 24% 不可比；基线一旦写入，后续只增不减——基线取值的合理性交 P7 裁决]
[DESIGN_GAP: check-obligations.py 的协议根解析取「AGATE_ROOT env → 脚本相对协议根 → cwd」，未用 `agate_common.resolve_agate_root`——因 v0.73.0 版本布局后稳定版（~/.agate/current）与开发 checkout 解耦，resolve_agate_root 会解析到稳定版目录而扫不到本 checkout 的登记表；派发自跑命令（`cd checkout && python3 agate/scripts/check-obligations.py`）要求命中本 checkout，故取脚本相对优先。该解析口径 P2 未指定，交 P7 裁决]
[DESIGN_GAP: check-obligations.py 无独立 P3 红灯测试——P3 批 6 的 tests_filter 用既有 SG.6（`test_protocol_alignment_review.py -k sg_6`），BDD-18/19 的专门用例（如「无归宿项→exit 1」「M 占比下降→exit 1」）未由 P3 产出；当前判定逻辑由 SG.6（登记面）+ check-obligations 自身 exit code 承载。P4 已用合成树手工验证两类负向（见 §5），「是否补正式回归测试」交 P7 裁决]

## 5. 自跑结果（自查 ≠ gate）

- `python3 agate/scripts/check-obligations.py` → **exit 0**；输出 `M 类占比: 60/123 = 0.4878（基线 60/123 = 0.4878）`，`归宿分布: M=60 C=33 R=30`。
- 负向手工验证（合成树，`AGATE_ROOT` 指向临时目录）：
  - 一条义务缺 `disposition` → `CHECK-OBLIGATIONS: FAIL 存在「无归宿」项 …`，**exit 1**。
  - M 占比 1/2 < 基线 2/2 → `CHECK-OBLIGATIONS: FAIL M 类占比低于基线 …`，**exit 1**。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **exit 0，0 ERROR**；CHECK 9 ✅ PASS（`check-obligations.py` 锚点三关键词字面命中），CHECK 15 ✅ PASS；WARNING 407 条**全部为冻结文件**（`live=0`，`--json` 实测），CHECK9-coverage **无新增 WARNING**。
- `python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -k sg_6 -q` → **1 passed**（`test_sg_6_check9_anchor_table_covers_all_gate_scripts` 转绿）。
- 相邻回归：`test_t43_check_registration_surface.py` + `test_check_protocol_consistency.py` + `test_check_yaml_schema.py` + `test_check_structure_consistency.py` + `test_tag0027_b3b_protocol_check14_check15.py` → **80 passed**。
- `python3 agate/scripts/check-structure-consistency.py` → **S1-S6/S0 全 OK**。
- `bash agate/tests/scripts/count-tests.sh` → **2671**（新增 `check-obligations.py` 不被收集为测试，计数未因本批变化）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/` → **All checks passed**。
- 平台扫描 `python3 agate/scripts/check-platform-assumptions.py agate/scripts/check-obligations.py agate/scripts/check-protocol-consistency.py` → **0 命中**。
- 数据面平台词扫描（CHECK 15）对 `rules/obligations.yaml` → **0 命中**（初版注释复述平台词表被 CHECK 15 拦下，已改为不复述词表）。

## 6. 新增文件核对表

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|---|---|---|
| `agate/rules/obligations.yaml` | `within agate/rules/` | `[CODE_MAP_UPDATED]`（CODE-MAP scripts 段「义务登记族」行登记 rules 数据面登记表） |
| `agate/scripts/check-obligations.py` | `within agate/scripts/` | `[CODE_MAP_UPDATED]`（同上，登记校验脚本） |

> 说明：P2 无 `P2-skeleton.md`（未采用骨架机制）；CODE-MAP 机制已采用（`agate-workspace/agents/CODE-MAP.md` 存在），故按 CODE-MAP 自身约定「后续任务新增协议文件时 P4 implementer 应更新本文件」同步。

## 7. 残留 / 未改（不在本批改动面）

- **不碰 batch1-5 已落实现**（`agate-next.py` / `agate-config.py` / `agate-run.py` / `gate_layer` / `agate-ci-verify.py` / `agate-doctor.py` 及其测试）。
- 未新增 P3 专门红灯测试（见 §4 对应 DESIGN_GAP）。
- 未改 `agate/UPGRADING.md` / `CHANGELOG.md`（属 P8 发布面，非本批）。
- 未做 P0-brief §二批 6 提到的「§4 通用化清理」——P2 §6.1b batch6 的 `output` 只列 3 个文件（`check-obligations.py` / `obligations.yaml` / `check-protocol-consistency.py`），本次派发约束亦未含该项，故按派发范围只做 BDD-13/18/19。此为**范围记录**（非阻塞疑问）：若「§4 通用化清理」确属批 6，请主 Agent 在后续派发中明确落点。
