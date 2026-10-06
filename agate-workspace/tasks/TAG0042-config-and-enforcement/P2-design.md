---
phase: P2
task_id: TAG0042
type: design
parent: P1-requirements.md
trace_id: TAG0042-P2-20261005
status: draft
created: 2026-10-05
agent: architect
candidate_count: 3
packages: [agate-config, agate-run, agate-config-schema, gate-layer, agate-ci-verify, agate-doctor, obligations-registry]
domains: [backend, cli, protocol]
ui_affected: false
dispatch_plan: {mode: serial, parallel_limit: 3, batches: [{id: batch1-phase-semantics, complexity: low}, {id: batch2-agate-config, complexity: high}, {id: batch3-agate-run, complexity: high}, {id: batch4-gate-layer, complexity: high}, {id: batch5-ci-doctor, complexity: medium}, {id: batch6-obligations, complexity: high}]}
---

# P2 方案设计 — TAG0042 项目形态命令化 + 规则脚本化

> 上游：`P1-requirements.md`（22 BDD，risk_level: high，ceremony: standard，domains: [backend, cli, protocol]，
> review status: approved）+ `P0-brief.md` + `P0-batch0-record.md`。
> 本文档是**设计阶段**产物，P2 固化的 `gate_commands` 在 P4-P6 不得修改。
> 本任务分 6 批推进（批 0 已走 hotfix 通道落地，见 `P0-batch0-record.md`），每批改 `agate/` 协议本体
> ⇒ 每批触发 SELF-GATE，须独立评审 + `self-gate-review:` 留痕。

## 0. review MINOR 订正（P1 review 的 3 条非阻塞项）

- **m-1**：P1 §2/BDD-18 交叉引用「见 §4」应为「§5」——设计阶段记录在案，P4 实现对该 BDD 引用时以
  「§5 待确认清单 / 前置输入」为准（不改 P1 冻结文件，属下游引用口径）。
- **m-2**（**本设计的强制纳入项**）：Windows/MSYS2 平台面未落独立 BDD ⇒ 本设计**在 `agate-run` 设计中
  显式纳入平台分支验证**（见 §4.2 候选 A 的平台面 + `gate_commands` 的平台适应度检查 + §5 环境约束）。
  落成 BDD-9 的平台分支验收面（P3 补用例）。
- **m-3**：BDD-13 批标注措辞——BDD-13 的「Batch 6 落地，守护面在批 2 起适用」表述，本设计批 6 的
  `tests_filter` 已体现（SG.6 转绿是批 6 的绿灯判据），措辞属 P1 冻结文件，不回改。

---

## 1. 影响面梳理（强制节，写在候选方案之前）

### 1.1 改什么（Modify）——逐文件落点 + 关联 BDD

| # | 文件 / 落点 | 改动点 | BDD |
|---|---|---|---|
| M1 | `agate/scripts/agate-next.py::_advance()`（198-210 行） | 去掉 `state["phase"]=target` 预写 + `_git(["add", ...state.yaml])`；保留 `append_event state_transition` 证据。改为**输出「下一阶段建议」**，phase 由后续在该阶段的产出 commit 时写 | BDD-1, BDD-2 |
| M2 | `agate/phase-cards/P2-design.md:14`、`P8-release.md:15-20` | 卡片描述与「phase = 本 commit 产出阶段」对齐（批 0 已改 P8 文字，批 1 复核 P2 卡片 + 一致扫描） | BDD-2 |
| M3 | `agate/UPGRADING.md`（批 1 章节） | 「阶段卡片 phase 语义（文档，无强制）」改述为「批 1 起 `agate-next` 亦**不预写**下一阶段」 | BDD-2 |
| M4 | **新增** `agate/scripts/agate-config.py`（`agate-*.py` 工具类，非 `check-*`） | 全部子命令：`init` / `validate` / `get <field>` / `list` / `show`（读/校验/查询）；退出码 0=成功 非 0=失败 | BDD-3, BDD-4, BDD-5 |
| M5 | **新增** `agate/rules/schema/project-config.schema.json` | 声明文件 schema（draft-07 子集，与 `rules/schema/` 既有 4 个 schema 同构：`$schema`/`title`/`type`/`required`/`properties`） | BDD-5 |
| M6 | `agate/scripts/agate_common.py` | **新增唯一读取函数** `read_project_config()`（声明文件解析 + 字段默认 + 缺失行为）+ 可选 `append_event` 复用（`cmd_run` 事件无需新函数） | BDD-6, BDD-8, BDD-12 |
| M7 | `agate/scripts/agate-setup.py` / `install-hook.py` | 接入时自动调 `agate-config init`（幂等，不覆盖既有声明） | BDD-7 |
| M8 | `agate/scripts/check-gate.py::gate_p0()` | 从「直接 return 2」改为**调用 `agate-config validate`**（迁移期只 WARNING，不 exit 1） | BDD-8 |
| M9 | **新增** `agate/scripts/agate-run.py`（`agate-*.py` 工具类） | 执行层：`agate-run <cmd>` / `--baseline`；环境变量注入；`.out` 证据落盘 + 逐字节比对；ignore 检查（`git check-ignore`）；平台分支（bash `pipefail` vs MSYS2） | BDD-9, BDD-10, BDD-11, BDD-12 |
| M10 | `agate/scripts/pre-commit-gate.py` | hook 一并暂存账本（`gate-events.jsonl`）；修正 formatter 计数 | BDD-12 |
| M11 | `agate/rules/phases.yaml`（+ `rules/schema/phases.schema.json` 若需扩展） | 关卡层按提交类型分级 → 转换表（含 `paused_from`）；P8 改为交付收尾（`delivery` 必须声明） | BDD-14, BDD-15 |
| M12 | `agate/scripts/check-gate.py::gate_p8()` | P8 gate：`delivery` 未声明 → 拦截（非 0）；语义改「交付收尾」 | BDD-15, BDD-21 |
| M13 | **新增** `agate/scripts/agate-ci-verify.py`（`agate-*.py` 工具类） | 替换 `ci-gate-backstop`：实际重跑 gate 判定，「跳过」与「通过」在输出上可区分 | BDD-16 |
| M14 | **新增** `agate/scripts/agate-doctor.py`（`agate-*.py` 工具类） | 诊断接入状态（声明文件/hook/版本解析/账本完整性）+ 修复指引 | BDD-17 |
| M15 | `.github/workflows/protocol-tests.yml` | `gate-backstop` job 改调 `agate-ci-verify.py` | BDD-16 |
| M16 | **新增** `agate/rules/obligations.yaml` | 160 项义务三态归宿登记表（依赖前置输入，见 §10） | BDD-18, BDD-19 |
| M17 | **新增** `agate/scripts/check-obligations.py`（`check-*.py` 门禁面） | 校验 obligations 三态完整 + M 类占比不下降；**必须在 CHECK 9 锚点表 / `GATE_SCRIPT_EXEMPT` 二选一登记** | BDD-13, BDD-18, BDD-19 |
| M18 | `agate/scripts/check-protocol-consistency.py` | 批 6 为 `check-obligations.py` 加锚点（或 GATE_SCRIPT_EXEMPT 条目） | BDD-13 |
| M19 | `agate/UPGRADING.md` | 迁移兼容章节：声明文件缺失行为不变 + WARNING + 截止版本；批 4 发版逻辑迁移 `preset: semver-changelog-tag` | BDD-8, BDD-21 |
| M20 | 全仓 R6 差分（`/tmp` 副本 + peekview 只读副本） | 每批合并前的通用化检验（**不改 peekview**，只看效果） | BDD-20, BDD-22 |

### 1.2 不改什么（Not Modify）——看起来该改但决定不改 + 理由

| # | 范围 | 不改理由 |
|---|---|---|
| N1 | `agate/scripts/check-state-transition.py` / `state-transitions.md` | 批 1 只改「预写」行为，「状态跳变合法性校验」机制不变（`_advance` 的 `git add` 去除后，pre-commit 对暂存 diff 的校验路径少了一个自动 add 源，但校验逻辑本身不动，避免波及） |
| N2 | `agate/scripts/agate-retreat-to.py` | 回退机制与 phase 预写是不同机制，不在批 1 范围 |
| N3 | `agate/scripts/check-tdd-red.py` | 批 3 「修正 formatter 计数」若涉及在 `check-*` 内，须查明落点后最小改；不改 TDD 判定语义（A/B 类出口码不变） |
| N4 | `archived/` 全部、`agate-workspace/tasks/` 存量任务 | 冻结快照，不回改（P1 §3.1 已判定）。存量任务无 `base_rev` 的迁移属「读取时兼容」，不是批量改写数据面 |
| N5 | peekview 仓库及其声明/CI/hook | P0-brief §三 明确不做；peekview 只作 R6 差分的**只读副本检验对象**，绝不改 |
| N6 | `agate/rules/schema/{dispatch,markers,phases,roles}.schema.json` 的既有字段 | 只**新增** `project-config.schema.json`，不改既有 4 个 schema 的字段集（避免 schema 面回归） |
| N7 | `agate/assets/templates/` 下的角色/派发模板正文 | 本任务不新增角色；卡片描述改动仅限 phase 语义相关两处 |
| N8 | 3 个 hook 薄壳（`.sh`） | 仍只做定位 + exec，不承载声明/执行逻辑（逻辑全在 `.py`） |

### 1.3 风险在哪（Risk）——每条风险配缓解

| # | 风险 | 缓解措施 |
|---|---|---|
| R1 | 批 1 改 `agate-next` 后，编排惯例须同步（commit 时 phase 保持当前产出阶段），否则 phase 推进断裂 | 卡片描述（M2/M3）与行为同批改；P3 补「不预写」的端到端用例；UPGRADING 写明编排变化（对应 P1 §2 隐含需求 4） |
| R2 | 声明文件是**双源同步**风险（`agate-config` 读写 + `read_project_config` 唯一读取）；若出现第二处解析实现，`BDD-6` 等价守护失效 | M6 定为**唯一读取函数**；消费方一律经它取值；P3 写「两处取值同源」等价守护测试；`check-protocol-consistency` 可加锚点防第二实现 |
| R3 | 批 4 删除发版逻辑，消费方散布（`check-structure-consistency.py:64-65`、`check-protocol-consistency.py:568`、`analyst.md`、复盘模板、`phases.yaml` task_fields、frontmatter schema） | **动手前全量 grep 消费方清单**（P0-brief known_risks 硬约束）；先提供 `preset: semver-changelog-tag` 等价物（BDD-21）；文件缺失时按发版痕迹给 WARNING；UPGRADING 写截止版本 |
| R4 | `agate-run` 的 `pipefail` / `checkout-index` 在 Windows（MSYS2）行为**未测** | 平台分支设计（§4.2）；`check-platform-assumptions.py` 应覆盖新脚本；P5 平台适应度检查独立 key；声明「Windows 走复制/退化路径 + WARNING」 |
| R5 | 账本是 append-only + `prev_hash` 链，新增 `cmd_run` 事件/hook 暂存账本若绕过 `append_event` 会破链 | M6 复用既有 `append_event`（唯一写路径）；BDD-12 用 `check-events.py` 判链连续；hook 暂存账本用 `git add` 而非直接写文件 |
| R6 | 新增 `check-obligations.py` 触发 SG.6 由绿转红（TAG0036 M18 实证） | 影响面梳理 §1.4 **已实测**该面；批 6 `tests_filter` = `pytest ... -k sg_6`，落地时转绿；BDD-13 守护 |
| R7 | 迁移期声明文件缺失若 fail-closed 会让所有存量项目 gate 静默变红 | BDD-8 强制「行为与现状一致 + WARNING，不 exit 1」；截止版本写 UPGRADING；P3 写存量兼容用例 |
| R8 | 多批改同一文件（如 `agate_common.py` 批 2/3 都动、`UPGRADING.md` 批 1/2/4 都动） | 批次设计（§6）按**文件分组**切批，同一文件不跨批改两轮；跨批共享件（`agate_common.py`/`UPGRADING.md`）由主 Agent 在各批返回后**统一处理**或顺序化 |

### 1.4 登记面（新增 / 改名 `agate/scripts/` 下文件时必填）——**实测**

权威清单：`agate/scripts/README.md`「新增脚本登记面」节。本任务新增 **5 个** `agate/scripts/` 下文件：
`agate-config.py` / `agate-run.py` / `agate-ci-verify.py` / `agate-doctor.py`（4 个 `agate-*.py`）
+ `check-obligations.py`（1 个 `check-*.py`）。

**实测方法**（可复现）：把 `check-mvwu.py` 内容复制为 `agate/scripts/check-obligations.py` 占位，
跑下列命令，**跑完即删**（已 `git status --porcelain agate/scripts/` 确认为空）：

| 面 | 类型 | 命令 | **实测结果** |
|---|---|---|---|
| ① CHECK9-coverage | **门禁**（WARNING） | `python3 check-protocol-consistency.py` | **`check-obligations.py` 触发 WARNING**：「gate 脚本 … 既未纳入 CHECK 9 锚点表，也未列入豁免集」；4 个 `agate-*.py` **零触发**（不在 glob 面） |
| ② SG.6 | **门禁**（pytest **会红**） | `python3 -m pytest agate/tests/integration/test_protocol_alignment_review.py -k sg_6 -q` | **`test_sg_6_check9_anchor_table_covers_all_gate_scripts` FAILED**（`['agate/scripts/check-obligations.py']`）；与 ① 同源（共用 `uncovered_gate_scripts()`） |
| ③ CHECK 10 | **非登记面（方向相反）** | 同上 consistency | **零触发**——新增脚本不触发；实测 consistency 冻结面 `CHECK10-scriptref 1 条`为**基线**（不变） |
| ④ README 脚本索引表 | 约定 | 特定脚本断言（`test_doc_sweep.py` 仅覆盖 TAG0037 两脚本） | 4 个新 `agate-*.py` **建议补索引行**（非门禁，不补不被拦） |
| ⑤ tests/README 映射表 | 约定 | `test_mvwu_protocol_docs.py` 仅覆盖 `check-mvwu.py` | 建议补映射行（无机械门禁）；**不写用例数** |
| ⑥ 用例总数 | 自动 | `bash agate/tests/scripts/count-tests.sh` | **2622**（下界语义，新脚本不被收集为测试，永不转红） |
| ⑦ CHANGELOG / CONTEXT | 任务级约定 | 任务流程 | CHANGELOG `[Unreleased]` 含 task_id（`check-changelog.py` 校验） |

**⇒ 登记面实测结论（写入设计，供 P4/P8）**：
- **`check-obligations.py`（唯一命中门禁面的新脚本）**：必须在 ① 二选一——承载 gate 判定逻辑 →
  进 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表；纯观测/调度类 → 进 `GATE_SCRIPT_EXEMPT` 并写理由。
  **本设计判定**：`check-obligations` 承载**判定逻辑**（校验三态完整 + M 占比不下降，有 exit code）
  ⇒ 进**锚点表**（`SCRIPT_ALIGNMENT_ANCHORS`）+ 在 `check-protocol-consistency.py` 文本中现锚点，
  使 SG.6 转绿。落成 BDD-13；批 6 落地时**必须实测** SG.6 转绿。
  **锚点 `keywords` 取值（N4 订正——定锚点）**：锚点表条目须含 `script` + `keywords`（`check_script_alignment`，
  `check-protocol-consistency.py:863-868`：`if kw not in text: rep.warn("CHECK9-align", ...)`）。
  `keywords` 必须取 **`check-obligations.py` 脚本实际输出/内含的稳定判定字符串**（须在脚本文本中**字面出现**，
  否则 CHECK9-align 会新增 WARNING，破坏「consistency 0 ERROR / 基线 WARNING」对账）。**本设计定值**：
  ```python
  {
      "desc": "义务三态归宿登记校验（M/C/R 完整 + M 类占比不下降）",
      "script": "agate/scripts/check-obligations.py",
      "keywords": ["obligations.yaml", "M 类占比", "无归宿"],
  }
  ```
  说明：`obligations.yaml`（登记表名）、`M 类占比`（M 占比不下降判定的输出串）、`无归宿`（「无归宿」项
  报错串）三者均为脚本内**字面出现**的稳定串。**批 6 落地时实测**：① 三串确实存在于脚本文本；
  ② `python check-protocol-consistency.py` 的 CHECK9-align **无新增 WARNING**；③ SG.6 转绿。
  若批 6 实现时输出串措辞变化 → 同步更新 keywords（以实测无 WARNING 为准）。
- **4 个 `agate-*.py`**：**不在门禁覆盖面内**（实测零触发），登记属**约定**——建议补 README 索引行。
- **新增 `project-config.schema.json`**：**不是脚本登记面**——`rules/schema/` 下 schema 由
  `check-yaml-schema.py` / `check-structure-consistency.py` 的 schema 扫描面覆盖（S-5），
  须与既有 4 个 schema 同构（命名 / `$schema` / 必填字段）。落成 BDD-5 验收面。

---

## 2. 设计总览

**两条所有者要求**（P0-brief §一）：① 项目形态由**声明**描述（不写死技术栈）；② 规则由**脚本在
不可绕开路径上执行**（不靠记忆）。三态归宿：脚本执行 M / 命令生成 C / 强制评审 R。

本任务**不追求一次做完**——分 6 批，每批独立 gate。设计目标是**每批可独立验证、批次边界清晰
（同一文件不跨批改两轮）**，并把「用未验证的新机制判自己」的风险降到最低。

---

## 3. 候选方案（candidate_count: 3）

### 候选 A（选定）：**声明层 + 执行层分离，逐批增量落地，唯一读取函数收敛**

**架构**：
```
项目根/agate.config.yaml  ──read──▶  agate_common.read_project_config()  ◀── 唯一读取函数
        ▲                                      │
        │ init/validate                        │ 消费方（gate / agate-run / setup / doctor）
        │                                      ▼
   agate-config.py  ◀──schema──  rules/schema/project-config.schema.json
        │
   agate-setup / install-hook 自动 init
        │
   agate-run.py ──▶ 执行声明中的验证命令（pipefail / 平台分支）──▶ .out 证据 ──▶ append_event(cmd_run)
```

- **声明层**（批 2）：`agate-config.py`（`agate-*.py`）+ `project-config.schema.json` +
  `agate_common.read_project_config()`（**唯一读取函数**）+ setup/install-hook 自动 init。
- **执行层**（批 3）：`agate-run.py`，环境变量注入 + `.out` 证据 + ignore 检查 + `cmd_run` 事件。
- **关卡层分级**（批 4）：`phases.yaml` 转换表（含 `paused_from`）+ P8 交付收尾。
- **CI/诊断**（批 5）：`agate-ci-verify`（替换 `ci-gate-backstop`）+ `agate-doctor`。
- **义务登记表**（批 6）：`obligations.yaml` + `check-obligations.py`（进锚点表）。

**优点**：
- 声明层/执行层**解耦**：批 2 可独立验证（只读写声明，不碰执行路径），批 3 依赖批 2 但接口窄。
- **唯一读取函数**（`read_project_config`）从架构上消灭「第二处解析实现」——BDD-6 的等价守护可验证。
- **迁移兼容**天然（文件缺失 → 读函数返回默认 + WARNING，不 exit 1）。
- 逐批可独立 gate，每批 SELF-GATE 范围可控；与 P0-brief 的 6 批范围表**逐条对齐**。
- 4 个新 `agate-*.py` **不在** CHECK9 门禁 glob 面（实测），登记成本低；唯一门禁面 `check-obligations.py`
  集中登记（进锚点表）。

**风险**（已在 §1.3 缓解）：批 4 消费方散布（R3）；`agate-run` 平台面未测（R4）；多批共享 `agate_common.py`（R8）。

**工作量**：6 批，批 2/3/4/6 high，批 1 low，批 5 medium。

---

### 候选 B：**单层 `agate-config` 全包（无独立执行层）**

**架构**：只引入 `agate-config.py`（含 `run` 子命令）+ schema + 读取函数；不单设 `agate-run.py`，
执行命令由 `agate-config run` 承担。

**优点**：
- 新增脚本更少（少一个 `agate-run.py`），`agate/scripts/` 面更小。
- 调用方只记一个命令入口。

**缺点（为什么不用）**：
- **职责混淆**：`agate-config` 既做「声明读写/校验」又做「命令执行/证据落盘」，违反「声明层只声明」
  的边界；批 2（声明）与批 3（执行）**无法独立 gate**——批 2 完成即已含执行逻辑，批次范围表（P0-brief）
  被压平。
- 执行层的平台分支、`.out` 证据、`cmd_run` 事件全塞进 config，使批 2 的回归面**膨胀**（一次改多面）。
- P1 的 `packages` 已声明 `agate-config` 与 `agate-run` **两个包**，BDD-9/10/11/12 明确以 `agate-run` 为
  主语——压平会与 P1 包边界冲突。

**工作量**：批数不变但批 2 复杂度显著上升（声明+执行合一）。

---

### 候选 C：**先建义务登记表（`obligations.yaml`）驱动，再反推命令**

**架构**：先做批 6（`obligations.yaml` + `check-obligations`），把 160 项义务逐项归宿，再由登记表
**生成** `agate-config` / `agate-run` 的命令面（登记表作单源，命令是登记表的投影）。

**优点**：
- 「规则脚本化」的**单源**最强——命令从登记表生成，不会出现「登记了但没脚本」或反之。
- M 类占比可从登记表直接度量，BDD-19 守护最自然。

**缺点（为什么不用）**：
- **前置输入缺口**（P0-brief §四、P1 §2.1）：160 项逐条清单**不在仓库**，须向评审索取并入库；
  先做批 6 会把整个任务**堵在缺口上**（P1 §5 明确「批 6 在批 2 之后才启动」）。
- 由登记表**生成**命令会引入「代码生成器」这一新机制复杂度，且与「agate 不绑定技术栈」（ADR-003）的
  最小约定原则相抵——登记表应**登记**归宿，不应**生成**实现。
- 无法先取得「管道确实通」的反馈（违反 tracer bullet 判据，§6.2）。

**工作量**：最大，且前置依赖未就绪。

---

### 选择理由（候选 A）

1. **与 P1/P0 的批次范围表和包边界逐条对齐**（候选 B 会压平批次，候选 C 与前置缺口冲突）。
2. **唯一读取函数**使 BDD-6 的「声明单源」在架构上可验证，而非仅靠约定。
3. **迁移兼容内建**：声明缺失 → 默认 + WARNING，不 exit 1（候选 C 的生成器会放大迁移面）。
4. **批次可独立 gate**，每批 SELF-GATE 范围最小——契合「先修判据、再往上盖」的批 0 教训。
5. 4 个新 `agate-*.py` 实测**不在**门禁 glob 面，登记成本集中在唯一一个 `check-obligations.py`，
   风险可控（§1.4 实测）。

---

## 4. 关键设计细节

### 4.1 声明层（`agate-config`，批 2）

- **声明文件形态**：项目根 `agate.config.yaml`（项目自带，`init` 生成）。字段（示意，P4 定稿）：
  `schema_version` / `project.language` / `project.package_manager` / `verify.commands`（验证命令列表，
  供 `agate-run` 消费）/ `release.preset`（如 `semver-changelog-tag`）/ `paths`。
- **子命令与退出码**：

  | 子命令 | 行为 | 退出码 |
  |---|---|---|
  | `init` | 生成初始声明；已存在 → **不覆盖**（幂等） | 0=成功 |
  | `validate` | schema 校验；非法字段/枚举值 → 报错 | 0=合法，非 0=非法 |
  | `get <field>` | 输出单一字段客观值（供脚本消费） | 0=成功 |
  | `list` / `show` | 列出全部 / 展示完整声明 | 0=成功 |

- **唯一读取函数**：`agate_common.read_project_config(project_root)`。返回 dict（缺字段用默认值）。
  文件缺失 → 返回默认 dict + 标记 `present=False`，由调用方决定 WARNING。**所有消费方**（gate、
  `agate-run`、`agate-doctor`）只经此函数取值，无第二处 YAML 解析。
- **schema**：`agate/rules/schema/project-config.schema.json`（draft-07 子集，与既有 4 schema 同构）。
- **迁移兼容（BDD-8）**：`gate_p0` 调 `agate-config validate`；迁移期 validate 对**文件缺失**只输出
  WARNING 返回 0（不改 gate_p0 的 `exit 2` 通过语义 ⇒ 行为与引入前一致）；截止版本写 `UPGRADING.md`。
- **gate_p0 返回值吸收 `validate` 退出码的口径（N2 订正——伪代码级）**：
  ```python
  # gate_p0()：现状无条件 return 2（通过码）。
  # 批 2 起改为：调 validate 子进程（迁移期只 WARNING），但**返回值仍恒为 2**。
  rc = subprocess.run([agate_python, "agate/scripts/agate-config.py", "validate"],
                      capture_output=True, text=True).returncode
  if rc != 0:
      print("WARNING: agate.config.yaml 非法/缺失（迁移期不阻断；截止版本起将 exit 1）", file=sys.stderr)
  return 2   # ← 恒为通过码，绝不把 validate 的 rc 泄漏进 gate_p0 返回值
  ```
  **口径**：`validate` 的退出码**只决定是否打印 WARNING**，**不参与** `gate_p0` 的返回值；迁移期
  无论 validate 返回 0 还是非 0，`gate_p0` **恒 `return 2`**（BDD-8「文件缺失/非法 → 行为与引入前一致」）。
  「未来截止版本主动改为 exit 1」是**独立的后续变更**，不在本任务内启用。负向用例交 P3：
  「存量项目无 `agate.config.yaml` → `gate_p0` 返回 2 且 stderr 含 WARNING」（对应 review T2/T3）。

### 4.2 执行层（`agate-run`，批 3）+ 平台分支（review m-2 强制纳入）

- **命令**：`agate-run <cmd-key|命令>` / `agate-run --baseline <cmd-key>`。
- **执行**：命令来自声明 `verify.commands`；子进程用 `bash` 执行，**开 `pipefail`**
  （复用 `agate_common.run_test_with_formatter` 已验证的写法：`"set -o pipefail; " + cmd`，
  `shell=True, executable="bash"`——**不能**写 `executable="bash -o pipefail"`，`executable` 是路径，
  实测抛 `FileNotFoundError`，见 `agate_common.py:747-756`）。
- **`.out` 证据（BDD-10）**：首次 `--baseline` 落盘 `.out`；后续执行逐字节比对，差异客观报出（二值）。
- **ignore 检查（BDD-11）**：证据文件须被 `.gitignore` 覆盖，用 `git check-ignore` 判定，否则报错。
- **`cmd_run` 事件（BDD-12）**：经既有 `agate_common.append_event()`（**唯一写路径**）追加；
  hook 一并暂存账本用 `git add`，不直接写账本文件（避免破链）。
- **平台分支（m-2）**：
  - **POSIX/Linux**：`bash -o pipefail` 可用，退出码如实传播，`checkout-index` 为 git plumbing。
  - **Windows（MSYS2）**：`pipefail` 与 `checkout-index` 行为**未测** ⇒ 设计**显式分支**：
    `bash` 不可用或 `pipefail` 不支持时，退化为**不吞退出码**的直执行 + **显式 WARNING**
    （绝不在退化路径上静默报绿——ADR-015 手段②「让错误可见」）。复制模式不可执行时 WARNING。
  - **验证面**：`check-platform-assumptions.py` 须覆盖新脚本；P3 写平台分支用例（Linux 断 `pipefail`
    生效，Windows 断「退化 + WARNING」）；`gate_commands` 加**平台适应度检查**独立 key（§5）。

### 4.3 关卡层分级（批 4）

- `phases.yaml` 增加按**提交类型**（纯代码 / 纯文档 / 发版）选择的关卡集合 + **转换表**（含
  `paused_from`）。`gate_pass_exit` / `next` / `retreat` 语义**不变**（避免批 0 刚修的判据回归）。
- P8 语义改**交付收尾**：`check-gate.py::gate_p8()` 校验 `delivery` 声明；未声明 → 非 0。
- **删发版逻辑的顺序**（R3 硬约束）：先提供 `preset: semver-changelog-tag`（等价物）→ 再删；缺失时按
  发版痕迹（CHANGELOG / 版本文件 / `v*` tag）给 WARNING；UPGRADING 写截止版本。

### 4.4 CI/诊断（批 5）

- `agate-ci-verify.py`：实际重跑 gate 判定（不再是「永远 SKIP 却显示绿」）；「跳过」与「通过」输出可区分。
- `agate-doctor.py`：诊断（声明文件 / hook / 版本解析 / 账本完整性）+ 修复指引，退出码固定。
- **替换** `ci-gate-backstop.py` 时须看 **CHECK 10** 方向（改名/退役才触发）：`ci-gate-backstop.py`
  在协议文档 / workflow 中被引用，退役后须同步更新引用（否则 CHECK10-scriptref ERROR）。

### 4.5 义务登记表（批 6）

- **前置输入**：160 项逐条清单（**不在仓库**，见 §10）。
- `agate/rules/obligations.yaml`：每项义务含位置 / 三态归宿（M/C/R）/ 现有脚本 / 失败证据。
- `check-obligations.py`：校验无「无归宿」项 + M 类占比 ≥ 基线（只增不减）；**进 CHECK 9 锚点表**
  （锚点 `keywords` 定值见 §1.4：`["obligations.yaml", "M 类占比", "无归宿"]`，三者须脚本内字面出现，
  批 6 落地实测 CHECK9-align 无新 WARNING + SG.6 转绿）。

---

## 5. gate_commands 声明

> **解释器口径（N3 订正 + 小修轮 gate 可执行性修正）**：以下 `gate_commands` 是**声明**，但
> **已修正为当前环境可直接执行的命令**——小修轮实测：**裸 `python` 不在 PATH（`which python` 空）**，
> 保留裸名会让 P3/P5 gate **exit 127（假失败，T075 教训）**。故：
> - 所有解释器统一写 `python3`（实测 `which python3` → `/usr/bin/python3`；本 checkout 与 CI 一致）；
>   执行侧仍可经 `AGATE_PYTHON` env 显式覆盖（`agate_common.probe_python()`，本机返回 `/usr/bin/python3`），
>   但**声明值本身假设可执行**——不再依赖执行者"自行替换裸名"（避免照抄 exit 127）。
> - `P5_ruff` 写 **venv 绝对路径** `~/.venvs/agate-dev/bin/ruff`（实测 `which ruff` 空；该 venv ruff 0.16.4，
>   与 CI 锁版一致，见 AGENTS.md:162 / RM-AG0037）。
> - Windows 无 `python3` 时探测为 `python`——此为**执行侧探测**结果，不改变本声明（本任务验证环境为 dsh/Linux）。

```yaml
gate_commands:
  P3: "python3 -m pytest"                          # 测试运行器（verbose，供 check-tdd-red.py 读取）
  P5: "python3 -m pytest agate/tests/ -q --tb=no"  # 全量回归（分片见 AGENTS.md；此处为 gate 声明）
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_structure: "python3 agate/scripts/check-structure-consistency.py"
  P5_ruff: "~/.venvs/agate-dev/bin/ruff check agate/"   # ruff 不在 PATH；用 venv 绝对路径（0.16.4，与 CI 锁版一致）
  P5_platform: "python3 agate/scripts/check-platform-assumptions.py"
  P5_timeout_seconds: 600
  P5_consistency_timeout_seconds: 120
  P5_structure_timeout_seconds: 120
  P5_ruff_timeout_seconds: 120
  P5_platform_timeout_seconds: 120
  project_module: "agate"
```

**说明**：
- 遵守「`--strict` 反模式」——每个校验**独立 key**，不塞 `&&` 链路（P5 / P5_consistency / P5_structure /
  P5_ruff / P5_platform 各自独立跑、独立记录）。
- `P5_e2e` **不声明**（`ui_affected: false`，无 UI）。
- **架构适应度检查**（判据三）：`P5_platform` = 平台假设静态扫描（依赖方向/跨平台边界）；
  另可加 `import agate_common` 反向依赖扫描（若需要）。本任务与「依赖方向 / 分层边界」相关，
  `check-platform-assumptions.py` 已覆盖平台边界维度。
- `{key}_timeout_seconds` 按三档基准表：全量回归 600s（构建/全量档）、其余 120s（单元档）。
- **ruff 版本对齐**：CI 锁 `ruff==0.16.4`，且 `ruff` 不在 PATH ⇒ `P5_ruff` 用 venv 绝对路径
  `~/.venvs/agate-dev/bin/ruff check agate/`（实测该文件存在且版本 0.16.4）。
- `P3_formatter` **移除**（原声明 `pytest.sh`）：实测 `pytest.sh` **不在 PATH**（`which pytest.sh` 空），
  且该值是极简 formatter **名**（框架从 `~/.agate/.../assets/formatters/pytest.sh` 解析，非 shell 命令）——
  P2 阶段无法确认框架能解析该名。按小修轮要求「存在则修、不存在则移除并说明」，本设计**移除该 key**：
  不声明 formatter 时框架**退化为 exit-code-only 判定**（框架文档明确「精度降低但不会阻断」），
  `check-tdd-red.py` 仍按 exit code 判红/绿，不影响 P3 gate 推进。
- gate 命令用**紧凑输出模式**（P5 `-q --tb=no`）。

## 6. 批次设计（dispatch_plan 节）

`dispatch_plan` 已写入 frontmatter：`mode: serial`（**串行链**，模式 5）、`parallel_limit: 3`、6 批
（batch1-batch6）。批数与 P0-brief §二范围表**逐条对应**（批 1-6）。

> **N1 订正（本轮重试 #1）**：原设计 frontmatter 写 `mode: static-batch, parallel_limit: 6`，而 §6 正文
> 一处写 `parallel_limit: 3`、§6.3 又按 `6` 论证——**三处不一致**。本设计 6 批**存在强依赖链**
> （批 2 依赖批 1、批 3 依赖批 2…），正是模式 5「串行链」的适用场景（dispatch-protocol「五模式编排」：
> 模式 5 = 批次间有强依赖，逐批派发、每批 gate 通过后派下一批）。故本轮**统一为 `mode: serial` +
> `parallel_limit: 3`**（3 与 dispatch-protocol「并行上限默认 3」一致；serial 模式下 gate 不校验
> `len(batches) ≤ parallel_limit`，`batches[]` 在 frontmatter 中仅作编排单元登记，`tests_filter` /
> `output` 值见 §6.1b）。

### 6.1 批次表

| 批 id | 内容 | 复杂度 | 依赖 | tests_filter（批级绿灯） |
|---|---|---|---|---|
| `batch1-phase-semantics` | 统一 phase 语义（`agate-next` 不预写 + 卡片对齐） | low | 无 | **既有真实测试（当下可跑）**：`test_agate_next_card.py` + `test_tag0027_b1_agate_next_cli.py` + `test_check_state_transition.py` |
| `batch2-agate-config` | 声明层（`agate-config` + schema + 唯一读取函数 + init + gate_p0 validate） | high | 批 1 | `test_agate_config.py` + `test_config_schema.py`（**P3 产出后生效**） |
| `batch3-agate-run` | 执行层（`agate-run` + 证据 + 事件 + hook 暂存 + formatter 计数） | high | 批 2 | `test_agate_run.py` + `test_events_ledger.py`（**P3 产出后生效**） |
| `batch4-gate-layer` | 关卡层分级 + P8 交付收尾 + `preset` | high | 批 3 | `test_gate_layer.py` + `test_check_p8_delivery.py`（**P3 产出后生效**） |
| `batch5-ci-doctor` | `agate-ci-verify` + `agate-doctor` + 替换 backstop | medium | 批 4 | `test_agate_ci_verify.py` + `test_agate_doctor.py`（**P3 产出后生效**） |
| `batch6-obligations` | `obligations.yaml` + `check-obligations`（进锚点表）+ §4 清理 | high | 批 2 | `test_protocol_alignment_review.py -k sg_6`（**既有文件，当下可跑**；SG.6 于批 6 转绿） |

> **`tests_filter` / `output` 落点说明（B1 订正同步）**：`dispatch_plan.batches[]` 的可选键
> `tests_filter` / `output` **不写入 frontmatter**——实测 `agate-frontmatter-check.py`（`MAX_DEPTH = 3`）
> 对 `batches[]` 内嵌键会打印「嵌套深度超过 3 层」（`dispatch_plan` → list → dict → 值 = 深度 4）。
> 故 frontmatter 只保留 `id` + `complexity`（深度 3，无告警），`tests_filter` / `output` 的**权威值**
> 见下表 §6.1b；二者关系为「frontmatter 登记编排单元 + 正文承接批级绿灯契约」。`{batch}` 即批 `id`
> （filename-safe），证据日志落 `P4-evidence/{batch}.log`。

### 6.1b 每批 `tests_filter` / `output`（可选键值）

> ⚠️ **先行声明（B1 修正，本轮重试 #1）**：本表多数 `tests_filter` 所指的测试文件为
> **P3 计划产出**（batch2-6 的 `test_agate_config.py` / `test_config_schema.py` / `test_agate_run.py` /
> `test_events_ledger.py` / `test_gate_layer.py` / `test_check_p8_delivery.py` / `test_agate_ci_verify.py` /
> `test_agate_doctor.py` **当前不存在**，须先由 P3 写红灯测试落地文件，该 filter 才可跑）。
> **batch1 与 batch6 例外**：二者指向**既有真实测试文件**，当下即可跑通（batch1 是 tracer bullet，
> 必须先取得「管道确实通」的反馈）。因此本表分两类：
> - **`[既有·当下可跑]`**：batch1 / batch6——文件已存在，`tests_filter` 立刻可执行（bat 1 实测
>   exit 0 / 93 passed，见 §9 minimal_validation；batch6 的 SG.6 文件既存，当下为红、批 6 转绿）。
> - **`[P3 产出后生效]`**：batch2-5——`tests_filter` 是**批级绿灯确认的先决条件声明**：
>   P3 先写该批交付面的红灯测试 → 文件就位 → 该 filter 才可跑；P4 实现后跑它确认绿。
>   在文件就位前**不得**把该 filter 当作「现在就能跑的命令」（pytest 对未知路径返回 exit 4 = usage error，
>   非测试红——旧版误把未来文件写成当下绿灯命令，即本轮 B1 根因）。

| 批 id | 状态 | tests_filter（批级绿灯，禁全量） | output（预期改动文件） |
|---|---|---|---|
| `batch1-phase-semantics` | `[既有·当下可跑]` | `python -m pytest agate/tests/unit/test_agate_next_card.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py agate/tests/unit/test_check_state_transition.py -q` | `agate/scripts/agate-next.py`, `agate/phase-cards/P2-design.md`, `agate/phase-cards/P8-release.md`, `agate/UPGRADING.md` |
| `batch2-agate-config` | `[P3 产出后生效]` | `python -m pytest agate/tests/unit/test_agate_config.py agate/tests/unit/test_config_schema.py -q` | `agate/scripts/agate-config.py`, `agate/rules/schema/project-config.schema.json`, `agate/scripts/agate_common.py`, `agate/scripts/agate-setup.py`, `agate/scripts/install-hook.py`, `agate/scripts/check-gate.py` |
| `batch3-agate-run` | `[P3 产出后生效]` | `python -m pytest agate/tests/unit/test_agate_run.py agate/tests/unit/test_events_ledger.py -q` | `agate/scripts/agate-run.py`, `agate/scripts/agate_common.py`, `agate/scripts/pre-commit-gate.py` |
| `batch4-gate-layer` | `[P3 产出后生效]` | `python -m pytest agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py -q` | `agate/rules/phases.yaml`, `agate/scripts/check-gate.py`, `agate/phase-cards/P8-release.md`, `agate/UPGRADING.md` |
| `batch5-ci-doctor` | `[P3 产出后生效]` | `python -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/unit/test_agate_doctor.py -q` | `agate/scripts/agate-ci-verify.py`, `agate/scripts/agate-doctor.py`, `.github/workflows/protocol-tests.yml` |
| `batch6-obligations` | `[既有·当下可跑]` | `python -m pytest agate/tests/integration/test_protocol_alignment_review.py -k sg_6 -q` | `agate/scripts/check-obligations.py`, `agate/rules/obligations.yaml`, `agate/scripts/check-protocol-consistency.py` |

> 平台中立：示例写 `python -m pytest` 形态。**实测本机 `python` 不在 PATH（`timeout ... python -m pytest`
> → exit 127），`agate_common.probe_python()` 返回 `/usr/bin/python3`** ⇒ **执行时必须把 `python` 替换为
> 探测结果**（项目 `AGATE_PYTHON` env 显式覆盖 > `probe_python()`）。即：`tests_filter` 里的解释器名是
> **声明**，执行时按探测替换，**不裸 `python3` 亦不裸 `python`**（N3 口径）。batch1 的实跑验证用的是探测
> 结果（`python3 -m pytest ...` → 93 passed，见 §9）。
> `expected_red`（设计上应红的用例）由运行者写入 `P4-evidence/{batch}.log` 的 `expected_red` 键，不写本文。

### 6.2 批切分判据

- **判据一（Tracer Bullet）**：**首个批（batch1）是「phase 语义」的端到端最小打通**——它无依赖、
  可独立验证（`agate-next` 行为的端到端判据 + 卡片一致扫描），先取得「管道确实通」的反馈。
  batch1 的 `tests_filter` 即覆盖该路径的冒烟级验证，且**指向既有真实测试文件**
  （`test_agate_next_card.py` + `test_tag0027_b1_agate_next_cli.py` + `test_check_state_transition.py`，
  本轮实测 exit 0 / 93 passed——**tracer bullet 当下即可跑通**，见 §9）。**不替代 P3 任务级红灯基线**
  （`gate_commands.P3`）。
- **判据二（Vertical Slice）**：批次**按业务能力**切（声明能力 / 执行能力 / 关卡分级能力 / CI 诊断 /
  义务登记），不是按「改了哪层代码」。batch2 交付「项目形态可声明」，batch3 交付「命令可经不可绕开
  路径执行」，各自端到端可交付。
- **判据三（Architecture Fitness Functions）**：见 §5（`P5_platform` 平台边界适应度检查）。

### 6.3 硬规则自检

- ✅ **high 复杂度必须拆分**：批 2/3/4/6 均 high，已拆为独立批（**模式 5 串行链**，逐批派发，非单发）。
- ✅ **串行链模式（模式 5）**：6 批有强依赖（§6.1 依赖列），主 Agent 按依赖顺序逐批派发，每批 gate 通过后
  派下一批；同一时刻并行度为 1。`dispatch_plan.mode: serial` 即此模式的机器声明。

> **`parallel_limit: 3` 取值说明（N1 订正）**：取 `3` = dispatch-protocol「并行上限默认 3」。
> `serial` 模式下 `_gate_p2_dispatch_plan`（`check-gate.py:795`）**只校验 `id`+`complexity`，
> 不校验 `len(batches) ≤ parallel_limit`**（该约束仅适用于 `static-batch`/`parallel`）；故 `batches` 列
> 6 批不触发 gate 拦截。`batches[]` 在 frontmatter 中作编排单元登记（`id`+`complexity`），批级绿灯
> `tests_filter` / `output` 值见 §6.1b；实际并行度由串行链决定（恒为 1）。

### 6.4 批次边界对齐影响面

- **同一文件不跨批改两轮**：
  - `agate-next.py` 仅批 1；`agate-config.py` 仅批 2；`agate-run.py` 仅批 3；
    `check-gate.py` 批 2（gate_p0）、批 4（gate_p8）——**同文件跨两批**，`phase` 语义不同（`gate_p0` vs
    `gate_p8`）⇒ 已在 §6.1 依赖链顺序化（批 2 先、批 4 后），不并行。
  - `agate_common.py` 批 2（`read_project_config`）、批 3（可选执行辅助）——**跨批共享件**，
    由主 Agent 在批 2 引入函数、批 3 仅调用，边界清晰。
  - `UPGRADING.md` 批 1/2/4 各写一节——**跨批共享文档**，按批次顺序追加（不改同段落）。
- **跨批共享件单列**：`agate_common.py` / `UPGRADING.md` / `check-protocol-consistency.py`（批 6 加锚点）
  由主 Agent 在所有批次返回后核对一致性。

## 7. files_to_read（实现时参考，控制 P4 上下文）

```yaml
files_to_read:
  - path: agate/scripts/agate-next.py
    why: 批 1 改 _advance()（198-210 行）——去预写 + 去 git add
  - path: agate/scripts/agate_common.py:104-500,516-800,1176-1330
    why: 公共库——run_git/probe_python/append_event/resolve_workspace/run_test_with_formatter/known_phase_ids/parse_gate_commands_block；新增 read_project_config 落此
  - path: agate/scripts/check-gate.py:631-637,849-956,1413-1573
    why: gate_p0（批 2 调 validate）/ gate_p2（dispatch_plan 校验口径）/ gate_p8（批 4 delivery）
  - path: agate/scripts/check-protocol-consistency.py:568-941
    why: CHECK 9 锚点表 + GATE_SCRIPT_EXEMPT + uncovered_gate_scripts()——批 6 登记 check-obligations
  - path: agate/scripts/ci-gate-backstop.py
    why: 批 5 被 agate-ci-verify 替换的现状实现（含 _inactive 假绿整改）
  - path: agate/scripts/agate-install.py:448-693
    why: _cmd_* 子命令分发模式——agate-config 的 CLI 形态参照
  - path: agate/scripts/install-hook.py
    why: 批 2 自动 init 的接入点
  - path: agate/rules/phases.yaml
    why: 批 4 关卡层分级 + P8 语义（gate_pass_exit/next/retreat 不动）
  - path: agate/rules/schema/phases.schema.json
    why: 若 phases.yaml 扩展字段，schema 同构参照
  - path: agate/rules/dispatch.yaml
    why: modes 枚举 + gate_commands 语法 + field_readers（新字段登记面）
  - path: agate/scripts/README.md:9-49
    why: 新增脚本登记面权威清单（批 6 登记 check-obligations）
  - path: agate/UPGRADING.md
    why: 每批迁移兼容章节的写法参照
  - path: agate/tests/README.md
    why: 脚本→测试映射 + CI 口径（分片/reruns）
  - path: agate/tests/integration/test_protocol_alignment_review.py
    why: SG.6 判据（批 6 转绿）
```

## 8. env_constraints（确认/细化 P0-brief，不弱化）

```yaml
env_constraints:
  debug_env: "无独立 debug 环境；验证＝本 checkout 内 pytest 全量（分 unit/regression/integration 片，-n auto）+ 对 agate-workspace/tasks 存量任务全量回归对账 + 每批 R6 双向差分（**必须在 /tmp 副本上跑**，AGENTS.md 工作流 0a——判据脚本有写副作用，如 check-judge-verdict.py 写 gate-events.jsonl）"
  platform: "dsh（Linux）；Windows/MSYS2 面经 CI 的 windows_smoke marker 冒烟（本机无 Windows）"
  network: "full"
  consistency_baseline: "0 ERROR / 398 WARNING（398 全部来自冻结文件：CHECK1-yaml 2 + CHECK10-scriptref 1 + CHECK2-refs 395；实测 --strict-errors-only exit 0）"
  peekview_readonly_copy: "每批 R6 差分须在 /tmp 上加一份 peekview 只读副本（不改 peekview，只看协议改动在它身上的新转红/告警面，BDD-20）"
  r6_diff_isolation: "双向 R6 差分只在 /tmp 副本上跑；跑完核验真实仓库 git status --porcelain 为空"
  boundary_enforcement: "以上 env_constraints 是声明性字段；真正被执行的是 gate_commands（§5）+ 各批 tests_filter。需要强制执行的约束（如 SG.6 转绿、平台扫描）均已落到 gate_commands / tests_filter"
```

**边界提醒**：以上 `env_constraints` 不会被 gate 自动执行。**需要强制执行的**已落 `gate_commands`：
SG.6 转绿 → batch6 `tests_filter`；平台面 → `P5_platform`；一致性 → `P5_consistency`；结构 → `P5_structure`。

## 9. minimal_validation（实证结果）

```yaml
minimal_validation:
  assumption: "本方案依赖既有脚本/gate 的行为假设：① agate-next 现行为=预写下一阶段 + git add；② check-gate.py P0 返回 2（通过码）；③ 新增 check-*.py 触发 CHECK9-coverage WARNING + SG.6 红，4 个 agate-*.py 不触发；④ consistency 基线 0 ERROR / 398 WARNING；⑤ run_test_with_formatter 的 pipefail 写法（executable 前缀而非路径）；⑥ **batch1 tracer bullet 的既有真实测试文件存在且当下可跑**（B1 修正）"
  method: "读既有脚本（agate-next.py / agate_common.py / check-gate.py / check-protocol-consistency.py）+ 跑既有命令（check-gate.py P0 / check-protocol-consistency.py --strict-errors-only / SG.6 探针 / count-tests.sh / **batch1 既有测试三文件实跑**）"
  result: confirmed
  note: |
    逐条实测（均在 /home/kity/oclab/agateon 本 checkout，命令限时 <180s）：
    ① agate-next.py:205 `state["phase"]=target` + :208 `_git(["add", ...state.yaml])` —— 预写 + git add 行为**确认存在**（批 1 改动点即此）。
    ② `python3 agate/scripts/check-gate.py P0 <task>` → exit **2**（通过码），stderr「立项阶段无需脚本 gate」—— P0 现无脚本 gate，批 2 接入 validate 的落点确认。
    ③ 探针 check-obligations.py（复制 check-mvwu.py，用完即删）：consistency 输出 CHECK9-coverage WARNING（仅该脚本）；`pytest ... -k sg_6` → 1 failed（`['agate/scripts/check-obligations.py']`）—— **两处同时命中、同源**；4 个 agate-*.py 零触发；CHECK10-scriptref 冻结 1 条**不变**；count-tests=2622；跑完 `git status --porcelain agate/scripts/` 为空（无残留）。
    ④ `check-protocol-consistency.py --strict-errors-only` → exit **0**，仅 398 WARNING（与 P0-brief 声明逐字吻合）。
    ⑤ agate_common.py:747-756 现用 `"set -o pipefail; " + cmd` + `executable="bash"`（注释明确：不能写 `executable="bash -o pipefail"`）—— agate-run 沿用此写法**确认**。
    ⑥ **B1 修正的最小验证（本轮重试 #1 新增，实跑复核 batch1 tracer bullet 的既有测试真实文件名 + 当下可跑）**：
       `ls agate/tests/unit/ | grep -iE "next|state_transition"` 实测既有文件为
       `test_agate_next_card.py` / `test_tag0027_b1_agate_next_cli.py` / `test_check_state_transition.py`
       （**旧设计误写为 `test_agate_next.py` / `test_state_transition.py`——漏 `check_` 前缀，且前者无此文件**）。
       实跑 `timeout 180s python3 -m pytest agate/tests/unit/test_agate_next_card.py agate/tests/unit/test_tag0027_b1_agate_next_cli.py agate/tests/unit/test_check_state_transition.py -q`
       → **`93 passed`，exit 0**（当下可跑）。batch6 的 `test_protocol_alignment_review.py` 亦为既有文件（现为红、批 6 转绿）。
       ⇒ batch1 / batch6 `tests_filter` 指向既有真实文件；batch2-5 明确「P3 产出后生效」（见 §6.1b 先行声明）。
    纯代码逻辑部分（子命令分发/字段读写/转换表数据流）无外部系统依赖，依赖内部函数：agate_common.read_project_config（新增）/ append_event / run_git / probe_python、check-gate.py 的 _md_field_get、check-protocol-consistency.py 的 uncovered_gate_scripts()。
```

## 10. 待确认 / 前置输入（不影响批 1-5）

- **批 6 前置输入**：160 项义务逐条清单**不在仓库**（P0-brief §四、P1 §2.1）。**须向评审索取并入库**
  （建议入库为只读参考，P1 §5 `[SUGGEST]`）。批 6 在批 2 之后才启动，届时若仍缺则批 6 前置不足而阻塞；
  **不影响批 1-5**。
- **`decisions/`**：本仓 `agate-workspace/decisions/` 不存在，P2 无需读既有决策。本方案的跨任务决策
  （声明层/执行层分离 + 唯一读取函数）记录于本设计 §3。

## 11. [SCOPE+] 与 DESIGN_GAP 预留

- 设计未发现必须扩大 P1 范围的新隐含需求（§1.4 的登记面实测已在 P1 §3.2 预见）。若 P4 发现声明文件
  字段需扩展而 P1 BDD 未覆盖 → 按 `[SCOPE+]` 格式标注，交主 Agent 增补基线。
- **DESIGN_GAP 预留**：批 4 的关卡层转换表矩体、批 6 的义务三态判定可能在实现中遇歧义，P4 implementer
  应标 `[DESIGN_GAP]`，P7 逐条审查。

## 12. 实现完成的标志（供 P3/P5 验证）

1. **批 1**：`agate-next` 通过 gate 后**不**写 `Pn+1` 到 `.state.yaml`、**不** `git add`；
   卡片无相悖描述（BDD-1/2）。
2. **批 2**：`agate-config init/validate/get/list` 全部可用、退出码固定；非法声明 → validate 非 0；
   `read_project_config` 是唯一读取实现（等价守护测试绿）；setup/install-hook 自动 init 幂等；
   文件缺失时 gate_p0 行为与引入前一致 + WARNING（BDD-3~8）。
3. **批 3**：`agate-run` 退出码如实传播（含 pipefail）；`--baseline` 落 `.out` + 逐字节比对；
   ignore 检查命中；`cmd_run` 事件 + `check-events.py` 通过；hook 一并暂存账本（BDD-9~12）。
4. **批 4**：按提交类型选择关卡集合（转换表含 `paused_from`）；P8 未声明 `delivery` → 拦截；
   `preset: semver-changelog-tag` 等价物就位（BDD-14/15/21）。
5. **批 5**：`agate-ci-verify` 实际重跑 gate 判定，「跳过」与「通过」可区分；`agate-doctor` 输出客观
   接入状态 + 修复指引（BDD-16/17）。
6. **批 6**：`obligations.yaml` 每项有三态归宿、无「无归宿」项；M 类占比 ≥ 基线；
   `check-obligations.py` 进锚点表使 **SG.6 转绿**（BDD-13/18/19）。
7. **每批**：pytest 全绿 + consistency 0 ERROR + ruff 绿；R6 双向差分（agateon + peekview 只读副本）
   的新转红/告警面全部可解释；独立评审 + `self-gate-review:` 留痕（BDD-20/22）。
