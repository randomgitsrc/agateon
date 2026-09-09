# CODE-MAP.md — agate 协议本体

> agate 仓库自身的架构全貌维护物（dogfooding 实例，TAG0007 首次落盘）。
> 描述对象：`agate/` 协议本体自身（阶段卡片 + 角色库 + 脚本 + 模板），不是某个使用 agate
> 的业务项目。后续任务新增/挪动协议文件时，P4 implementer 应更新本文件；P7
> consistency-reviewer 核对本文件记录与实际新增文件是否同步（`[CODE_MAP_SYNC:]`）或偏离
> （`[CODE_MAP_DRIFT:]`）。

## 模块

agate 协议本体划分为五大模块：

- **phase-cards**（`agate/phase-cards/`）：9 张阶段卡片，P0（立项）～P8（发布），每张卡片定义
  该阶段"进入条件 / 执行步骤 / 产出规格 / 推进条件 / 常见错误"，是主 Agent 编排流程的唯一权威
  脚本来源。
- **execution-roles**（`agate/assets/execution-roles/`）：7 个执行角色（analyst / architect /
  test-designer / implementer / verifier / consistency-reviewer / vision-analyst），定义
  P1-P8 各阶段"谁来做、怎么做"的行为规范，供 subagent 派发时读取。
- **review-roles**（`agate/assets/review-roles/`）：11 个评审角色（review / plan-ceo-review /
  plan-eng-review / design-review / plan-design-review / qa / investigate / cso /
  protocol-alignment-review / requirements-review / judge），供 C8 机械映射按 domain/risk_level
  派发（judge 除外：P6.5 验收独立裁判，**所有任务强制**，不进 C8 表，见 role-system.md）。
- **scripts**（`agate/scripts/`）：gate / 一致性 / 状态三大脚本家族——
  gate 族（`check-gate.py`、`pre-commit-gate.py`、`pre-push-gate.py` 等）判定各阶段能否推进；
  一致性族（`check-protocol-consistency.py`、`check-p6-provenance.py`、`check-p6-evidence.py`
  等）核对协议文档间/产出物间的静态一致性；状态族（`agate-state-get.py`、
  `check-state-transition.py`、`check-state-yaml.py`、`agate-retreat-state.py` 等）读写和校验
  `.state.yaml` 状态转移。三族之外还有编排辅助脚本（`agate-inject-card.py`、
  `agate-render-dispatch-prompt.py`、`agate-next-card.py`、`agate_common.py` 公共函数库等）。
  ceremony 路由族（新增 TAG0019）：agate-risk-score.py（客观信号算分）、check-routing.py（ceremony 声明校验，pre-commit 2j.1 挂载）。
  judge 机制族（新增 TAG0020）：check-judge-verdict.py（judge verdict 门槛校验，P6.5 强门槛）、check-events.py（gate-events.jsonl 事件账本审计，append-only 哈希链）。
  推进侧状态机族（新增 TAG0027）：agate-next.py（推进 CLI——消费 phases.yaml next/retreat/gate_pass_exit + check-gate exit 三态判定推进/回退/真暂停）、agate-advance.py（多阶回退引导，委托 agate-retreat-to.py）、agate-dispatch.py（渲染时注入 CLI——单命令渲染 dispatch-context + 阶段卡片 Lazy Injection，CARD-SOURCE 块外来源标记）。
  命令流检测族（新增 TAG0028）：agate-cmdstream-ir.py（CommandRecord 统一 IR：十字段字段契约 + JSON 序列化）、agate-cmdstream-adapters.py（四平台命令流适配器：Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd / Codex rollout JSONL（`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，CodexAdapter 于 TAG0033 补齐），显式注册表 ADAPTERS）、agate-cmdstream-detect.py（检测引擎 FROZEN/SPIN/NORMAL + 心跳 helper + CLI list-sessions/read-commands/detect）；检测/解析输出平台无关，阈值配置走 agate-workspace/maintainability.yaml cmdstream_detection 节。
- **templates**（`agate/assets/templates/`）：模板文件（`dispatch-prompt.md`、
  `dispatch-context.md`、`task-files.md`、`code-map-template.md`、`skeleton-template.md`、
  `tech-debt-template.md`、`retrospective-template.md`、`roadmap-template.md`、
  `active-tasks-template.md`、`custom-role.md`、`handoff-template.md`、`project.md` 等），给
  角色/主 Agent 提供可复制的产出格式。
- **rules**（`agate/rules/`，TAG0021 新增结构化层）：**数据面**——`phases.yaml`（阶段定义/
  门槛/产出/retry_cap/机器字段声明）、`dispatch.yaml`（三铁律/五模式/gate_commands 语法/字段
  读取登记）、`roles.yaml`（双层角色/C8 机械映射/脚本注册表）+ `schema/*.json`（draft-07 子集
  schema）。YAML 只承载可判定规则，叙事留 md（WORKFLOW/phase-cards/rules/*.md 既有提取物
  review-mapping.md、state-transitions.md 与本目录 YAML 并存不合并）；一致性由
  `check-structure-consistency.py`（S-1~S-6）与 `check-yaml-schema.py`（S-5 校验器）双向 gate
  （M2 起进 pre-commit + CI）。

## 层

自上而下四层：

1. **协议流程层**（phase-cards）：定义 P0-P8 各阶段"做什么、按什么顺序、推进条件是什么"，
   是唯一的流程权威来源。
2. **角色层**（execution-roles + review-roles）：定义"谁来做"——execution-roles 是阶段产出的
   执行者，review-roles 是 C8 映射触发的评审者。角色层消费流程层声明的职责边界，不反向定义
   流程。
3. **工具层**（scripts）：把流程层/角色层声明的判定规则脚本化、可自动执行——gate 脚本判定
   能否推进，一致性脚本判定文档间是否漂移，状态脚本判定 `.state.yaml` 转移是否合法。
4. **模板层**（templates）：给角色层/主 Agent 提供产出物的字段结构和格式范本，是流程层"产出
   规格"节的具体落地形式。

## 依赖方向

- **phase-cards 不直接依赖角色/脚本实现细节**（松耦合）：卡片只声明"需要产出什么、字段名是
  什么"，角色文件和脚本可独立演进，只要遵守卡片声明的契约（字段名、文件路径、标题格式）。
- **scripts 消费 phase-cards / templates 声明的字段名做判定**：例如 `check-gate.py` 的
  `gate_p7` 读 `P7-consistency.md` frontmatter 里的 `design_gap_count` /
  `code_map_new_files_count` 等字段名，这些字段名由 phase-cards「产出规格」节和 templates 定义，
  scripts 是下游消费方，不定义字段名本身。
- **scripts 消费 rules/*.yaml 声明做判定（TAG0021 起）**：`check-structure-consistency.py` /
  `check-yaml-schema.py` 读 `rules/` 数据面（S-1~S-6 一致性 + schema 校验）；M1 起既有 grep
  解析脚本以对账模式读 YAML，M2 起切换为权威源。依赖方向单向（rules → scripts 消费），
  禁止 scripts 反向定义 rules 数据语义。
- **execution-roles / review-roles 消费 phase-cards 声明的职责边界，不反向定义流程**：角色文件
  里的"输出"节描述的产出物必须对应某张 phase-card 的「产出规格」，角色不能自行发明流程之外的
  产出要求。
- 允许的依赖方向：`phase-cards → execution-roles/review-roles → templates`（流程定义产出，角色
  执行产出，模板规范产出格式），以及 `phase-cards/templates → scripts`（脚本读取字段名做机械
  判定）。**禁止反向**：scripts 不应定义新的流程语义，角色文件不应绕过 phase-card 自定产出规格。

## 关键文件

- `agate/WORKFLOW.md`：流程总览入口，含目录结构树状图、工作区目录规范、主流程说明。
- `agate/dispatch-protocol.md`：派发协议、gate 表、并行编排规则、特殊事件处理。
- `agate/state-machine.md`：状态转移设计（`.state.yaml` phase 字段的合法转移图）。
- `agate/role-system.md`：双层角色体系说明（execution-roles vs review-roles 的分工原则）。
- `agate/scripts/check-gate.py`：门槛判定核心脚本，每个阶段（`gate_p0`～`gate_p8`）对应一个判定
  函数，是"能否推进到下一阶段"的唯一机械裁判。

## 约定

- **新增机制需经 P0-P8 完整流程**：不可因"这是新机制/新增能力"而裁剪阶段（TAG0007 自身即遵循
  此约定，骨架 + CODE-MAP 两个新增机制均走满 P0-P8）。
- **改协议脚本走 TDD**：先写失败测试确认红灯，再改脚本确认变绿，不允许先改脚本后补测试。
- **改协议文档 / 脚本 / 卡片触发 SELF-GATE 自审**：commit message 需含
  `self-gate-review:` 或 `self-gate-skip:` 语义标记（否则 commit-msg hook 产出 WARNING），由
  `protocol-alignment-review` 评审角色执行语义审查。
