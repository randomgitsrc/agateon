---
agent: requirements-review
phase: P1
task_id: TAG0042
type: review
parent: P1-requirements.md
trace_id: TAG0042-P1-20261005
created: '2026-10-05'
status: approved
---

# P1-review — TAG0042 需求基线评审（requirements-review，首轮）

> 结论：**approved**。22 条 BDD（BDD-1…BDD-22）编号连续、格式合规、均可二值判定；同类扫描为**实测**（探针真放进仓再删除、`git status` 无残留）；能力/环境三态判断正确（无 frontend ⇒ 无需 vision/UI-UX 声明）；声明与 P0-brief 记录的**多批高风险协议改造范围**匹配。
> 无 BLOCKER、无 MAJOR。仅余 3 条 MINOR（非阻塞，建议 P2 前顺手订正，见末节）。
> 说明：本次**只审不写**——未修改 P1-requirements.md，未 git commit，未执行任何写仓/破坏性命令。`[PROD_NOT_TOUCHED]`（仅只读 git / grep / 读文件）。

## BDD 评审（22 条，逐条判定 + 覆盖维度）

编号核对：`grep '^#### BDD-'` 得 BDD-1…BDD-22 连续、无跳号，格式 `#### BDD-NN:` ✓。
`domains: [backend, cli, protocol]`，**无 frontend** ⇒ 前端维度对全部 BDD 记 N/A；无须 UX 类别 BDD / `ui_render_shape` / vision 能力声明（`check-gate.py::_gate_p1_vision_capability` 仅在 domains 含 frontend 时触发，本任务不触发）✓。

- BDD-1（agate-next 不预写下一阶段）：可判定（`phase` 字段未被写入 `Pn+1` + `.state.yaml` 未 `git add`，均为客观断言）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-2（phase 语义与卡片表述一致）：可判定（"不存在预写行为代码"为 grep 断言；"卡片表述与行为一致"沿用本仓同类扫描式一致性核对）。数据✗ 前端N/A 多端✗ 边界✗ 兼容✓
- BDD-3（形态由声明描述、协议不写死技术栈）：可判定（读取声明决定行为 vs 硬编码假设，可对 GitLab+Go+Helm 夹具验证）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-4（agate-config 读写子命令）：可判定（输出客观值 + 退出码语义固定 0/非0）。数据✓ 前端N/A 多端✓ 边界✗ 兼容✗
- BDD-5（schema 校验拒非法形态）：可判定（非法字段/枚举 → 非0；合法 → 0）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-6（唯一读取函数单源）：可判定（无第二解析实现 + 等价守护测试"两处取值同源"）。数据✓ 前端N/A 多端✓ 边界✗ 兼容✗
- BDD-7（setup/install-hook 自动 init 且幂等）：可判定（自动生成 + 不覆盖既有，两项客观）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-8（缺失声明迁移期行为不变 + WARNING）：可判定（行为与引入前一致 + 显眼 WARNING + **不** exit 1 + UPGRADING 写明截止版本号）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-9（agate-run 在不可绕开路径执行命令）：可判定（经 agate-run 而非自由 bash + 退出码如实传播含 pipefail）。数据✗ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-10（--baseline 可比对基线证据）：可判定（落盘 `.out` + 逐字节比对报差异）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-11（证据文件被 ignore 检查覆盖）：可判定（`git check-ignore` 命中，否则报错）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-12（cmd_run 账本事件不破坏哈希链）：可判定（`prev_hash` 链连续 + `check-events.py` 通过 + hook 一并暂存）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-13（check-obligations 完成登记面 SG.6 转绿）：可判定（CHECK9-coverage 与 `pytest -k sg_6` **两者都无**未登记告警）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-14（关卡层按提交类型分级）：可判定（不同类型走不同关卡集合 + 转换表含 `paused_from`）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-15（P8 交付收尾 + delivery 必须声明）：可判定（未声明 `delivery` → gate 非0；声明后放行）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-16（agate-ci-verify 替换 backstop 无假绿）：可判定（实际重跑门槛 + 跳过与通过在输出上可区分）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-17（agate-doctor 诊断接入状态）：可判定（输出客观接入状态 + 异常项可执行修复指引 + 退出码固定）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-18（obligations.yaml 三态归宿无遗漏）：可判定（每项有 M/C/R 归宿，无"无归宿"项）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-19（M 类占比只增不减）：可判定（占比 ≥ 基线值，下降即 FAIL）。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-20（不引入只适用于单项目的规则）：可判定（副本新转红/告警面全部可解释，逐条归属论证）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-21（删除发版逻辑前提供等价 preset）：可判定（一行声明保持现状 + 发版痕迹时显眼 WARNING + UPGRADING 写明迁移与截止版本）。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-22（每批不回退，横切不变量）：可判定（独立评审 + `self-gate-review:` 留痕 + pytest 全绿 + consistency 0 ERROR + M 占比不下降）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓

**跨条一致性**：同场景多 BDD 的 Then 无矛盾——BDD-8（迁移期不 exit 1）与 BDD-22（不回退）分属"过渡态"与"最终态"，语义上以"截止版本"为界，不冲突；BDD-13（批 6 产物）与 BDD-19（批 6 起守护）同批，无重叠冲突；BDD-15（P8 交付收尾）与 BDD-21（删除发版逻辑）同为批 4 且互为前提，顺序已声明。未发现同 Given 场景下 Then 互相矛盾者。

## 隐含需求覆盖

- **数据维度**：已覆盖——`.state.yaml` phase 字段、声明文件/schema、`.out` 证据、`gate-events.jsonl` 哈希链、`obligations.yaml`（BDD-1/5/10/12/18）。
- **前端维度**：N/A（domains 无 frontend）。
- **多端维度**：已覆盖——协议↔使用者项目契约（BDD-3/8/20/21）、跨批一致性（BDD-22）、Windows/MSYS2 平台面在 §2.5 识别为隐含需求（但未落成独立 BDD，见 m-2）。
- **边界维度**：已覆盖——声明缺失（BDD-8）、非法枚举（BDD-5）、基线差异（BDD-10）、哈希链连续（BDD-12）、退出码边界（BDD-16 跳过 vs 通过）。
- **兼容维度**：已覆盖——存量项目迁移兼容（BDD-8/BDD-21）、M 类占比不回退（BDD-19）、R6 差分不回退（BDD-20/BDD-22）。

**结论**：五维隐含需求均覆盖或 N/A，无遗漏（数据✓ 前端N/A 多端✓ 边界✓ 兼容✓）。

## 裁剪评审

- **phases: [P1, P2, P3, P4, P5, P6, P7, P8]**——**无任何跳过阶段**。理由充分：改动面为协议本体 + 状态机 + 关卡层，跨 6 批、触发 SELF-GATE、含破坏性变更（删发版逻辑），P2–P8 全部必需。
- **ceremony: standard**——未薄化，与 high 风险匹配；无需 `coupling_checklist` / `跳过风险` 四要素（非 thin）。
- **implicit_coupling: true**——`ceremony: full` 才强制 P7，本任务为 standard；但已显式声明 change 跨脚本与协议文档 ⇒ P7 保留，无冲突。

**裁剪合理**：逐阶段核对无跳过；risk_level=high 与「多批架构演进 + SELF-GATE + 破坏性变更」匹配。

## 审声明（风险分级 / 裁剪声明 vs 暂存区实际改动）

- **暂存区证据**：`git diff --cached --stat` = **空**（无任何协议改动暂存）；`git status --porcelain` 仅：`M agate-workspace/tasks/active-tasks.md`（任务登记行）+ 5 个未跟踪 P1 阶段文件（dispatch-context / progress / requirements）。
- **判定：匹配（无声明-实际失配）**。P1 是需求基线阶段，尚未产出 `agate/` 代码改动 ⇒ 暂存区为空属**预期**；声明依据的是 P0-brief 记录的**计划范围**（6 批协议改造：新增 4 命令 + 1 登记表 + 1 声明文件 + 新证据格式，触发 SELF-GATE，含删除发版逻辑的破坏性面）。`risk_level: high` / `ceremony: standard` / `phases` 全保留，与该文档化范围**一致**。本项**非**声明-实际不一致（不构成 needs-revision 条件）。
- **ceremony: full → phases 含 P7**：本任务为 `standard`，该核对项**不适用**（P7 仍在 phases 内）。
- **`.state.yaml` judge 声明**：`judge.enabled: true` 已写入 ✓（满足 RM-AG0039 机制后新任务强制要求，P1 gate 机械校验可过）。

## 同类扫描评审（实测性核对）

- §3.1 五个新脚本名全仓扫描：命中清单 + 逐条判定齐全（`agate-config`/`agate-run`/`agate-ci-verify`/`agate-doctor` 命中均为规划性引用；`check-obligations`/`obligations`/`delivery`/`preset:` 零命中）。
- §3.2 **登记面实测**（非推理）：把 5 个文件真放进仓、跑 consistency + `pytest -k sg_6`，记录实际转红面（仅 `check-obligations.py` 触发 CHECK9-coverage WARNING + SG.6 FAILED；4 个 `agate-*.py` 零触发；0 ERROR/399 WARNING），**跑完即删并由 `git status` 确认无残留**。符合 P1 卡同类扫描第 5 条与 AGENTS.md 工作流 0a 的纪律（不污染真实仓库）。
- §3.4 批 1 phase 语义同类实例扫描：命中清单 + 逐条判定（含"不处理"的 P6.5 挂载子阶段，理由充分）。

**结论**：同类扫描为**实测**，结论落盘 P1 正文，非空白，通过。

## 待确认 / 能力声明评审

- §5：行首 `[NO_NEED_CONFIRM]` ✓，无阻塞性 `[NEED_CONFIRM]`；一条 `[SUGGEST]`（批 6 清单入库）不阻塞 ✓。
- §6 `capability_requirements`：`need: no-special-capability` / `status: available` ✓。三态判断正确——本任务缺的是**运行环境**（`/tmp` 副本差分空间 + peekview 只读副本），已正确走 `verification_env` 而非 `supplementable`（判断树用法无误），无 GAP ✓。

## P1 纯净性

多数 BDD 点名具体产物（`agate-config init` / `.out` / `cmd_run` / `check-obligations.py` / `preset: semver-changelog-tag` / `rules/obligations.yaml`）——但这些名称由 P0-brief 范围**先定义**（本任务本质即引入这批具名命令与登记表），与本仓既有已批准 P1 惯例一致（如 TAG0037 在 BDD 中点名 `agate_package.py`）。BDD 描述的是具名命令的**用户可观测行为**，非内部实现步骤，属"做什么"而非"怎么做"。**判定：未越出 P1 纯净性边界**（承载形态留 P2）。

## 非阻塞 MINOR（建议 P2 前顺手订正，不影响 approved）

- **m-1（交叉引用错位）**：§2 隐含需求 1（`:88`）与 BDD-18 Given（`:285`）均写"见 §4 待确认"，但 **§4 是 BDD 验收条件节**，待确认清单实为 **§5**。建议改为"§5"。属 traceability 文案错，不影响 BDD 可判定性。
- **m-2（平台面未落 BDD）**：§2.5 识别"Windows/MSYS2 下 pipefail 与 checkout-index 行为未测"为隐含需求，但 §4 未落成独立 BDD（BDD-9 仅笼统含 pipefail）。建议 P2/P3 在 `agate-run` 设计中显式纳入平台分支验证，或在 P1 补一条平台 BDD（若采纳属 `[BASELINE_CHANGE]`）。
- **m-3（BDD-13 批标注措辞）**：标题写"Batch 6 落地，守护面在批 2 起适用"——`check-obligations.py` 是批 6 产物，"守护面在批 2 起适用"易生歧义，建议改为"落地批 6；SG.6 守护判据自批 6 起适用"。

## 结论

**approved**。22 条 BDD（BDD-1…BDD-22）编号连续、逐条可二值判定、逐条标注覆盖维度；隐含需求五维覆盖或 N/A；无裁剪（phases 全保留）理由充分；同类扫描为实测且结论落盘；capability/verification_env 三态拆分正确无 GAP；无阻塞 NEED_CONFIRM；声明（risk=high / ceremony=standard / phases 全保留 / implicit_coupling）与 P0-brief 文档化范围匹配（P1 期暂存区为空属预期）。仅余 3 条非阻塞 MINOR（m-1…m-3），不阻断推进。

`[PROD_NOT_TOUCHED]` 本次评审全程只读（git status/diff/ls、grep、读文件），未执行任何写仓或破坏性命令。
