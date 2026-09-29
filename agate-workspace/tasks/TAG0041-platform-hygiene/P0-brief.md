# P0-brief — TAG0041 平台适配层卫生（受限 harness 临时产物/服务生命周期 + agent-team 定位）

> 主 Agent 亲自填写（P0 产出）。关联 RM：**RM-AG0075**（受限 harness 下的临时产物与长驻服务生命周期）+ **RM-AG0076**（DSH agent-team 与 agateon 机制定位冲突）。
> **来源**：peekview TPV0099 复盘 + **用户澄清**（harness 沙箱因果）+ TPV0098 P0-brief 关键约束 + 会话实测（2026-09-29）。
> **性质**：**平台适配层设计与协议约定**——改 `platform-notes.md` / `assets/templates/` / 交付物模板；**核心是补协议级缺失约定**，不改状态机。

```yaml
task: "为受限 harness（工作区外不可写、进程存活跟随发起调用）补协议级临时产物约定与长驻服务生命周期设计；并明确 agateon 会话不使用 DSH agent-team 及理由、收敛工具面"
known_risks:
  - "🔴 临时产物约定与 P4 卡「并行时分配独立临时目录」要求冲突，P2 须给出共存口径（canonical 根 + 每批子目录）"
  - "🔴 .gitignore 模板可能覆盖用户既有文件，须定义幂等/追加/仅提示的安全语义（参照 v0.76.0 定界托管块先例）"
  - "同类/影响面预判：受限 harness 不止 DSH（Codex 亦有沙箱档位），须面向整类而非单平台"
  - "不得再造「声明无消费」字段——本任务正在 TAG0038 修该缺陷之后进行，新增字段必须有消费方"
env_constraints:
  debug_env: "DSH 实机验证须起独立实例（勿扰用户 :23701）；写 ~/.dsh 需用户明确许可"
  platform: "dsh"
  network: "full"
  consistency_baseline: "386 WARNING / 0 ERROR"
executor_env:
  platform: "dsh"
  has_task_tool: true
  has_local_runtime: true
  network: "full"
```

## task

「为**受限 harness**（工作区外不可写、进程存活跟随发起调用）补协议级的**临时产物约定**与**长驻服务生命周期设计**；并明确 agateon 会话**不使用 DSH agent-team**及理由、收敛工具面。」

## 合并依据（为何 RM-AG0075/0076 是一个 task）

两者同属**平台适配层的"环境事实未成文"**，且**共用同一批交付面**：

| RM | 缺什么 | 共同文件 |
|---|---|---|
| RM-AG0075 | **受限 harness 的环境事实**（工作区外不可写 → 临时产物只能在会话工作区内；进程活不过发起调用）无协议级约定 | `platform-notes.md` / `assets/templates/dsh/SKILL.md` / `assets/templates/*` / 交付 `.gitignore` 模板 |
| RM-AG0076 | **工具面事实**（agent-team 与 agateon 概念不对付）无覆盖、工具面未收敛 | 同上（`platform-notes.md` + DSH 模板） |

分两批会在 `platform-notes.md` 与 DSH 模板上改两遍 → 强合并。

## 因果澄清（用户 2026-09-29 更正，本节是本任务的立论基础）

**`.agate-tmp` 不是"项目卫生没做好"，而是 harness 约束的必然产物**：

> DSH 默认 `workspace-write`——**只覆盖会话工作区**，工作区外（含 `/tmp`）**不可写**。agent 唯一能落临时产物的地方就是**会话工作区内的某个目录**，于是自选了 `.agate-tmp/`。

→ **机制的正确设计对象是"受限 harness"，不是"某个目录名"**。若不设计，每个项目各自发明且反复踩坑（见证据 A）。

## 实测证据

### 证据 A：无协议级约定 → 项目各自发明并实际付出代价

| 事件 | 后果 |
|---|---|
| `.agate-tmp/` 涨到 **76MB**、含 **10 个明文 token/cookie**，且**未被 `.gitignore` 覆盖** | `make bump-version` 的 `git add -A`（项目自有 target）会 stage **162 条**（158 条在该目录）→ **明文凭证入 git 历史不可逆**。TPV0099 以项目侧 `.gitignore` 缓解 |
| 并行评审写入 `frontend-v3/.agate-tsprobe/*.spec.ts` | 被 vitest **默认收集面**扫入，基线 **110 → 115 files**，**静默推翻**另一评审刚作出的「不影响基线」结论 |
| architect 在 `frontend-v3/src/` 留 `__typeprobe_zenkey.ts` | 源码树污染，须人工清理 |

**根因**：临时目录的**名称、VCS 忽略、测试收集面排除、清理时点**——**四项全无约定**。

### 证据 B：长驻服务的跨调用生命周期（同属本类，TPV0098 P0 亦列为关键约束）

DSH 下**服务存活跟随"起它的那条调用"**（非服务自身崩溃）。TPV0099 因此**掉线 4–5 次**，托底 job 时长**逐次加长仍被跨越**：

**7200s → 14400s → 28800s → 43200s（12h）**

TPV0098 `P0-brief` 明确将其列为任务关键约束：

> 「**后台服务跨调用姿势**：DSH 沙箱下服务存活跟随"起它的那条调用"，跨调用必须挂持续 running 的后台 job 托底」

→ **agateon 无设计，靠项目各自摸索**（本机两个项目独立踩同一坑）。

### 证据 C：agateon 对 agent-team 零覆盖，且工具面未收敛

- `grep -rni 'agent-team|teammate|spawn_teammate|team_task' agate/` → **空**
- 而本机 profile 已挂该 bundle，**实测编排会话里 `subagent` / `subagent_fork` 与 team 工具同时可见**（bundle 声明的 `tool-subagent disabled: true` **未生效**）
- DSH persona 的工具映射只列 `subagent` / `subagent_fork` / `workflow` / `ralph` / `goal`——**从不提 team**

### 证据 D：现有平台提示不完整

`assets/templates/dsh/SKILL.md`「平台注意」目前只有 4 条：① 协议本体目录只读（`Errno 30`）② `/tmp` 只读（pytest 用 `--basetemp`）③ 审批禁用时沙箱拒绝即终局 ④ bash 纪律。

**缺**：临时产物约定（本任务核心）、长驻服务生命周期（证据 B）、agent-team 定位（证据 C）。

## scope

### 子批 A：临时产物约定（RM-AG0075 主体）

定义**协议级**临时产物规范（对**所有**受限 harness 生效，不止 DSH）：

1. **canonical 目录**：工作区内、**强制被 VCS 忽略**（与"agent 会在工作区内落临时产物"这一 harness 事实匹配）
2. **排除出测试收集面**：探针文件名/路径**不得命中**常见测试收集模式（`*.spec.*` / `*.test.*`）——证据 A 第 2 例的直接教训
3. **清理时点与清单**：与 P8/READY 收尾联动（既有「临时资源清单」机制见 P8 卡——本任务**复用而非另造**）
4. **交付 `.gitignore` 模板预置**（`find agate -name '.gitignore*'` 现为**空**）

### 子批 B：长驻服务生命周期（RM-AG0075）

- 平台文档成文「**服务存活跟随发起调用**」这一事实及其应对（托底 job 姿势 / 跨调用检测 / 掉线自检）
- 与既有机制的边界（见 known_risks：RM-AG0023/RM-AG0014 已解决「谁负责准备环境」，本子批解决「**进程活不过调用**」）
- **不再靠"逐次加长托底"**——须给出**可判定**的做法（如派发前探活 + 掉线即重试），因为 TPV0099 证明「加长到 12h 仍不够」

### 子批 C：agent-team 定位与工具面收敛（RM-AG0076）

- `platform-notes.md` DSH 章 + `assets/templates/dsh/SKILL.md` **显式写明 agateon 会话不使用 agent-team 及理由**（概念冲突：`agent-team` 引入**第二个任务板** + **自主续跑的队友**，与 agateon「`.state.yaml` 单一权威 + 阶段受门禁约束 + 单一作者」竞争）
- 给出接入时**收敛工具面**的做法（使 agateon preset 会话只暴露 `subagent` / `workflow` 面）
- 排查 bundle 的 `disabled` 与 preset 的**冲突是否可解**（证据 C）

## 验收基线（倾向，P1 细化）

1. Given 受限 harness When 按协议约定落临时产物 Then 该目录**名称固定 + 被 VCS 忽略 + 排除出测试收集面 + 有清理时点**——**四者可机械校验**
2. Given `agate/` 交付物 When 检查 Then 存在 **`.gitignore` 模板**且预置常见 agent 临时目录
3. Given 探针文件名 When 命中测试收集模式 Then **有约定禁止**（且该约定在平台文档/模板中可达）
4. Given 长驻服务需求 When 按平台文档做法执行 Then **跨调用存活有成文做法**（且被判据引用，不是纯散文）；「托底时长」不再是唯一手段
5. Given `platform-notes.md` DSH 章与 `assets/templates/dsh/SKILL.md` When 阅读 Then **均显式声明不使用 agent-team 及理由**
6. Given agateon preset 会话 When 检查工具面 Then **收敛结果可复现**（bundle `disabled` 与 preset 的冲突有结论：可解则给做法，不可解则如实说明并给替代）
7. Given 全量 pytest + consistency When 跑 Then 全绿 / 0 ERROR

## known_risks

- **同类/影响面预判——同类实例**：受限 harness **不止 DSH**。平台矩阵中 Codex 亦有沙箱档位（`-s <read-only|workspace-write|danger-full-access>`，见 `platform-notes.md` Codex 章），Claude Code / OpenCode 亦有各自权限模型。**本任务须面向"受限 harness"这一类，不能只写 DSH 一节**——否则同类问题会在接入下一平台时复发（P1 同类扫描须列出各平台的沙箱语义与差异，判据可参照 `RM-AG0034` 的平台能力差异表方法）。
- **同类/影响面预判——上下游消费方**：改 `platform-notes.md` 会牵动 `SETUP.md`（各平台接入章节）、`assets/templates/{dsh,codex}/*`、`check-protocol-consistency.py` 的**平台假设扫描器**（`check-platform-assumptions.py` R2/R4——TPV0099 曾因 test 文件里的 `/tmp` 字面量被其检出，**本任务新增文档若含路径字面量须注意**）、以及 `agate-setup.py` 的模板分发面。
- **🔴 最大风险：临时产物约定若与既有 P4 卡的「基础设施隔离」冲突**。`dispatch-protocol.md` 与 P4 卡已有「并行时强制为每批分配独立**端口/数据库/临时目录**」要求——新增「canonical 临时目录」须与之**协调而非打架**（一个要求"独立目录"，一个要求"固定在 X"）。**P2 必须给出两者共存的口径**（如 canonical 根 + 每批子目录）。
- **🔴 第二个风险：`.gitignore` 模板可能覆盖用户既有配置**。agateon 交付模板给他项目用时，若直接写 `.gitignore` 会**覆盖或冲突**用户既有文件。须定义**幂等/追加/仅提示**的安全语义（勿静默改写用户文件——这与 v0.76.0 DSH preset 修复的「定界托管块」是同类问题的先例，可参照）。
- **agent-team 冲突可能不可解**：证据 C 的 `disabled` 未生效，根因可能在 DSH bundle 与 preset 的加载顺序（本会话实测两套工具同时可见）。**若确认为上游行为**，本任务**如实记录 + 给替代做法**，不承诺修复上游（不得把"待上游"写成"已解决"）。
- **不得再造"声明无消费"的字段**：本任务在 TAG0038 修复「声明层与控制层脱节」的**同时/之后**进行。新增任何约定字段（如临时目录声明位置）必须**有消费方**（脚本读取或 gate 校验），否则**重犯 TAG0038 要修的错**。**这是本任务最需自警的一条。**
- **与 RM-AG0023/RM-AG0014 的边界（防误读为重复）**：那两条（均 `done`）解决「**谁负责声明/准备环境**」与 `verification_env` **字段定义**；本任务解决「**harness 让进程活不过发起调用**」这一**平台生命周期事实**——不同的层，前者机制无法覆盖。

## env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`；开发另需 `ruff`（CI 锁 `0.16.4`）
- **本机环境**：`~/.agate` 为版本管理布局；`~/.agate/scripts/` 为**稳定版**（勿动）
- **写 `~/.dsh/` 需用户明确许可**（全局规则 5）——本任务若需实机验证 DSH 工具面收敛/预设行为，**须先取得许可**，且**不得擅自改用户 profile**
- **`check-protocol-consistency.py` 必须用 worktree 自己的**
- **平台无关是硬约束**：测试不得裸 `python3`、不得用 `/tmp`、不得假设 POSIX symlink（本任务**恰恰涉及 `/tmp` 与路径约定**，须格外注意：**文档中出现的路径字面量可能被平台假设扫描器命中**——TPV0099 已踩过 `DEBT0048` 类陷阱）
- 一致性基线：**386 WARNING / 0 ERROR**
- **改动面全部触发 SELF-GATE**（`agate/**/*.md` / `agate/scripts/*.py`）→ 须独立评审 + `self-gate-review:` 引用
- **实机验证面**：DSH 预设/工具面验证须起独立实例（勿扰用户 `:23701` 会话）；长驻服务验证注意「服务存活跟随调用」——**本任务要验证的正是这一条**，须设计不依赖长托底的验证方式

## executor_env

- **worktree**：`git worktree add .worktrees/agate-TAG0041 -b feat/TAG0041-platform-hygiene`，流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0041.md`
- **稳定版工具**：`~/.agate/scripts/`（勿动）
- **证据来源**：`agate-workspace/roadmap/roadmap.md` 的 RM-AG0075 / RM-AG0076 条目；外部样本 `peekview/agate-workspace/tasks/TPV0099-fullscreen-link/`（`.agate-tmp` 事件、并行探针污染）与 `TPV0098-e2e-local-sharding/P0-brief.md`（跨调用服务约束）
- **先例参照**：`TAG0018` / `TAG0030`（DSH 平台接入——本任务在其交付的 `assets/templates/dsh/` 上补卫生约定与定位声明）、`TAG0033`（Codex 平台接入——同类平台能力差异处理）、`TAG0032`（v0.76.0 的 DSH preset **定界托管块**——`.gitignore` 模板的安全语义可参照该幂等/托管先例）
- **关联条目**：`RM-AG0034`（平台扩展 epic——本任务约定应能被第四平台直接复用）

## 裁剪倾向

- **P2 完整走**（多决策点：canonical 目录形态与 P4 卡隔离要求的共存口径 / `.gitignore` 模板安全语义 / 工具面收敛做法与上游冲突的处置）
- **P3 保留**（四项可机械校验性、`.gitignore` 幂等语义、工具面收敛均可测）
- **P6 不可裁**（须实机证据：DSH 工具面收敛结果 + 长驻服务跨调用做法验证；**注意**实机验证需用户许可）
- **P7 完整走**（跨平台文档 + 多模板 + 扫描器交互）
- **P8**：协议文档/模板改动 → 需 bump（**若含工具面收敛行为变更，CHANGELOG 须明确**）

## 不做的事（边界）

- **不做**比例阀/度量/债务可见性（**TAG0038** 范围）
- **不做** check 脚本健壮性（**TAG0039** 范围）
- **不做**派发成本治理（**TAG0040** 范围）
- **不做** RM-AG0079（轻量改动通道）
- **不改** `~/.dsh/` 用户配置（需许可且非本任务范围——本任务只改 agateon 侧交付物与文档）
- **不承诺修复上游 bundle 行为**——若 `disabled` 未生效属 DSH 上游，如实记录 + 给替代
- **不新增无消费方的声明字段**（见 known_risks 最后一条）
- **不重做** RM-AG0023 / RM-AG0014（环境准备职责与 `verification_env` 字段定义，均 `done`）
