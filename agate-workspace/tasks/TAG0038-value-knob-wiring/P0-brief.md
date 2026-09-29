# P0-brief — TAG0038 协议自我调节与自我认知（比例阀接线 + 效率/债务可观测性）

> 主 Agent 亲自填写（P0 产出）。关联 RM：**RM-AG0071**（比例阀失效）+ **RM-AG0074**（效率与收益可观测性）+ **RM-AG0078**（protocol 类债务回流与编号来源）。
> **来源**：peekview TPV0099（`/{slug}/f` 全屏链接）复盘 + 44 个会话日志逐条解压量化 + 在 agateon HEAD 上**逐条实测**（2026-09-29）。
> **性质**：**协议内核语义变更**（状态机 + gate 判据 + C8 映射 + 产出字段），**不是**局部修补。三条 RM 合并的理由见「合并依据」。

```yaml
task: "让协议的比例声明真正生效（5 个惰性旋钮逐个裁决接线或删除 + C8 补降级行 + 算分改任务属性），并让协议效率与债务状态可见（阶段耗时/派发数/token 入账本与 summary + M3 收益指标有提取方 + judge 预算实测 + protocol 类债务可见且带上游锚）"
known_risks:
  - "🔴 接线会改变存量任务的可推进性：尊重 phases 裁剪后历史任务推进路径变化，须 fail-closed + 向后兼容（声明缺失=全阶段）"
  - "同类/影响面预判：6 个旋钮中 5 个无消费（非单点），须逐旋钮处理；改动牵动 9 张卡 + WORKFLOW/state-machine + S-1/S-2 双向一致性"
  - "删除旋钮属破坏性变更（存量任务声明会变非法），须评估 major bump 与迁移指引"
  - "度量字段若写入方与读取方语义不同源，会重演 v0.76.0 的「报告 ✅ 而实际无数据」"
env_constraints:
  debug_env: "无独立 debug 环境；验证=worktree 内 pytest + check-protocol-consistency.py（须用 worktree 自己的脚本）+ 真实 gate CLI"
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

「让协议的**比例声明真正生效**（5 个惰性旋钮逐个裁决接线或删除 + C8 补降级行 + 算分改任务属性），并让协议的**效率与债务状态可见**（阶段耗时/派发数/token 进账本与 summary + M3 收益指标有提取方 + judge 预算实测 + protocol 类债务在 summary 可见且带上游锚）。」

## 合并依据（为何 RM-AG0071/0074/0078 是一个 task）

三条同属一个根因：**协议看不见自己也管不住自己**——

| RM | 缺什么 | 共同面 |
|---|---|---|
| RM-AG0071 | **管不住**：比例只能升不能降（5 个旋钮声明通过但无消费） | `.state.yaml` / `state-machine.md` / `check-gate.py` / `agate-next.py` / C8 映射 |
| RM-AG0074 | **看不见**：耗时/token/派发数在全部机器可读表面不可见 | `.state.yaml` / `agate-summary.py` / 事件账本 |
| RM-AG0078 | **看不见（债务维）**：protocol 类债务滞留项目登记簿、跨登记簿编号无来源标注 | `agate-summary.py` / `agate-feedback.py` / `tech-debt-template.md` |

**硬依赖（决定性）**：RM-AG0071 的验收锚是「接线后**实测减少派发数/阶段数**」——**没有 RM-AG0074 的度量就无法验收**；反之只有度量不改变行为。二者**必须同批**。RM-AG0078 与 0074 共用 `agate-summary.py` 报告面，同批可避免两次改同一文件。

## 实测证据（本任务的全部依据，均在 HEAD 复现）

### 证据 A：6 个比例/裁剪旋钮，5 个是「声明 + 校验 但无消费」

| 旋钮 | 声明 | gate 校验 | **消费方（行为是否改变）** |
|---|---|---|---|
| `ceremony: thin` | ✅ | ✅ `check-routing.py` | ❌ **无**（9 张阶段卡 + C8 表 + 全部 gate/推进脚本 count=0） |
| `{key}_timeout_seconds` | ✅ | ✅ | ❌ **无**（`UPGRADING.md:838` 自陈「无运行时消费方」） |
| `phases:` 裁剪 | ✅ | ✅ `check-pruning.py` | ❌ **无**（`agate-next.py` 对 `P1-requirements` 引用 count=0，只读 `phases.yaml` 固定 `next` 链） |
| `internal_only` | ✅ | ✅ `check-pruning.py` | ❌ **无**（`check-gate.py` count=0） |
| `design_trivial` / `follows_existing_pattern` | ✅ | ✅ | ✅ **有**（`check-gate.py:865` → `gate_p2` 的 `candidate_count` 2→1，**唯一真接线**） |
| `risk_level` | ✅ | ✅ | ✅ 有（C8 评审映射；**但只有升级行 high/full，无降级行**） |

**散文声称存在（4 处）但行为不存在**：`WORKFLOW.md:242`、`state-machine.md:407-408`、`CONTEXT.md:29`、`UPGRADING.md:811` 均称「`thin` 薄化 P2/P4 的 LLM 评审」。编排者实际读的 **P2/P4 卡从不提 thin**。

### 证据 B：`internal_only` 的裁剪是假的（反证实测）

peekview `T053-agent-raw-discovery` 声明 `internal_only: true` + `internal_only_reason`，`phases` 不含 P8（`check-pruning` **校验通过**）→ **仍然产出 `P8-release.md`**。

### 证据 C：风险算分的 tier 取决于「何时提问」而非任务属性

`agate-risk-score.py::score_task()` 唯一数据源是 `git diff --cached`。对同一 TPV0099：**现在**跑得 `tier: thin`（无暂存改动），P1 时不可复现。

### 证据 D：效率状态在全部机器可读表面不可见（TPV0099 量化）

| 项 | 值 |
|---|---|
| 真实产品代码 | **3 文件 / +24 −14** |
| 阶段 / 派发 | 满 8 阶段 / **26 次派发** |
| 墙钟 | **18h36m** |
| 输出 token | **3,508,955**（主 Agent 5.7% / subagent 94.3%） |
| 累计 agent-hours | **19.4h / 44 会话** |

而 `.state.yaml` 的 `history` 只有 `ts` **无 duration**；无任何脚本统计阶段耗时（`agate-summary.py` 不报时间）；无 token/步数/派发数账本；TPV0099 声明了 **10 个** `_timeout_seconds` 全部无效。

### 证据 E：M3 收益指标「供提取」但无提取方

`phase-cards/P1-requirements.md:130-137` 定义了四要素（评审轮数 / 真实发现数 / TAG0018 基线 / 「不达标 → 回滚 standard」），标注为「机制文档**供提取**」——**没有提取方**，故「要不要薄化/回滚」的决策**永不可执行**。

### 证据 F：judge 预算从不实测

`check-judge-verdict.py` 只在账本**已有** `budget_exhausted` 事件时交叉校验，**从不测量**实际 token/时间。TPV0099 judge 写「未触发 token/时间上限」而**无任何数字**。

### 证据 G：protocol 类债务零回流（RM-AG0078 依据）

TPV0099 在**项目**登记簿留 4 条 `category: protocol` 债务（peekview DEBT0014/0015/0016/0017），agateon 自身登记簿实测：`check-scope-resolved` **0 命中**、`MAX_ARG_STRLEN`/`vitest.sh` **0 命中**。回流脚本 `agate-feedback.py` docstring 自陈「**不存在任何自动触发该脚本的钩子/CI/定时任务**…只产出待人工提交的内容」。且 peekview 与 agateon 的 DEBT0013-0017 **完全不相交**、无来源标注。

### 证据 H：RM-AG0031 / RM-AG0040 的 `done` 在本项上不可信

RM-AG0031 声称「thin 档跳过 LLM 评审」并标 `done`，实测该行为**在机制层不存在**；RM-AG0040 标 `done` 但正文自陈「实证依赖外部薄任务出现、本 task 内无法自证」——交付的是**计划**。

## scope

### 子批 A：惰性旋钮裁决（RM-AG0071 主体）

对**每一个**无消费旋钮给出**明确裁决**，不允许保留「声明好看、校验通过、行为不变」的状态：

1. **`ceremony: thin`** → 接线（C8 补降级行 + P2/P4 卡写明 thin 下的派发面 + 派发侧消费）**或**删除（连同 `check-routing.py` 与 4 处散文一并移除）
2. **`{key}_timeout_seconds`** → 接线（供跑命令方据此设 shell 超时）**或**删除（连同 P2 卡字段规则与模板）
3. **`phases:` 裁剪** → 接线（`agate-next.py` / gate 尊重任务声明：P3/P7/P8 可真跳过）**或**降级为纯文档
4. **`internal_only`** → 随 ③ 一并接线（P8 真跳过）**或**删除
5. **`risk_level`** → C8 映射补**降级行**（与 thin/裁剪联动，不只是 high/full 升级）
6. **`score_task()`** → 数据源从「暂存区快照」改为**任务属性**（同一任务在 P1 与 P8 返回同值）

### 子批 B：效率可观测性（RM-AG0074）

- 阶段 **entry→exit duration + 派发数 + token** 写入 `.state.yaml`/事件账本，并由 `agate-summary.py` 报出
- **M3 收益指标落地**：为四要素提供落盘字段**与提取方**（不再是孤儿条款）
- **judge 预算实测**：`check-judge-verdict.py` 的预算字段含**实测数字**而非自述

### 子批 C：债务可见性（RM-AG0078）

- 项目登记簿中 `category: protocol` 条目在 `agate-summary.py` 或 `agateon-setup --list` **可见**
- protocol 条目带**上游锚**（脚本路径 + 行号指纹）
- 跨登记簿同号条目的**来源标注可机械检查**

## 验收基线（倾向，P1 细化）

1. Given 5 个惰性旋钮 When 逐个裁决后 Then **每个都有明确结论**（接线：可观测的行为变化；删除：字段+校验+散文一并移除、无残留声称），且**协议中不存在无消费的声明字段**（可机械扫描）
2. Given 声明 `ceremony: thin` 或 `phases` 不含 P8 的 low 风险任务 When 走完流程 Then **实测派发数/阶段数少于** standard 基线（可数）——**此为 RM-AG0071 的成败判据，也是「裁剪不是假的」的唯一证明**
3. Given 同一任务 When P1 与 P8 分别跑 `score_task()` Then 返回**同值**（含回归用例，不随提问时机变化）
4. Given C8 映射表 When 阅读 Then 存在**降级行**且被派发侧消费
5. Given 任一完成任务的 `.state.yaml` 或 summary When 读取 Then 可得**阶段耗时 + 派发数 + token**（对既有任务可回溯）
6. Given M3 四要素 When 需要判定「是否回滚 standard」Then 有**落盘字段 + 提取方**，决策可执行
7. Given judge verdict When 检查预算字段 Then 含**实测数字**（非「未触发」自述）
8. Given 项目登记簿含 `category: protocol` 条目 When 跑 summary/`--list` Then **可见**且带上游锚；跨登记簿同号条目有来源标注且可机械检查

## known_risks

- **同类/影响面预判（强制）——同类实例**：`grep -rn 'ceremony' agate/scripts/*.py` 命中 4 类（frontmatter 枚举 / 字段清单 / `check-routing` 校验器 / consistency 登记表）——**全是「声明面」、零「消费面」**，即本缺陷**不是单点**而是 5/6 的系统性形态。**本任务须逐旋钮处理，不能只改 `thin` 一处**（P1 同类扫描须给出完整清单与逐条判定）。
- **同类/影响面预判——上下游消费方**：改动 `phases:`/`internal_only` 接线会牵动 `agate-next.py`（推进决策）、`check-gate.py`（gate 早退）、`check-pruning.py`（校验）、`check-state-transition.py`（转移合法性）、`agate-summary.py`（展示）、**全部 9 张阶段卡**（表述）、`WORKFLOW.md`/`state-machine.md`（权威口径）。`_check_roadmap_done`（RM-AG0043）与 `check-structure-consistency.py` 的 S-1/S-2 双向一致性锚点**必须同步**（改 YAML 或改 md 都会触发 S-1/S-2）。
- **🔴 最大风险：接线会改变存量任务的可推进性**。一旦 `phases:` 裁剪被真正尊重，**历史任务**（如 peekview 大量声明 6-7 阶段的 task）在新语义下的推进路径会变；若这些任务仍有未完成的后继阶段，可能出现「声明不含 P8 但已有 P8 产出」的不一致。**必须 fail-closed + 向后兼容**：声明缺失 → 按现状（全阶段）；声明存在 → 尊重但须有既有产出的兼容口径。P1 必须先勘察「存量任务中有多少声明了非全阶段」（本机实测：peekview 侧多例，如 `T009: P1,P4,P5,P8`）。
- **删除旋钮是破坏性变更**：若裁决为「删除」，则 `ceremony`/`internal_only` 等字段的**存量任务会变成非法声明**（frontmatter schema 拦截）。须评估版本号（**major bump?**）与 `UPGRADING.md` 章节 + 迁移指引。
- **度量引入的隐私/体积面**：token 与耗时入账本会**增大产出文件**（事件账本已有哈希链）。须评估是否入 committed 文件、以及跨平台可获取性（token 数只有平台侧知道，DSH/Claude Code/OpenCode 数据源不同——`RM-AG0055` 已做过三平台适配器，可复用其 IR）。
- **度量口径陷阱（本仓已踩）**：`agate-summary.py` 的展示口径与 `--list` 的判定口径曾因「查死目录」长期假绿（v0.76.0 修复）。新增度量字段时**必须确认写入方与读取方是同一语义**，否则会重演「报告 ✅ 而实际无数据」。**这正是本任务要治理的失效模式，不得在新代码里重犯。**
- **C8 降级行的自指风险**：本任务是协议改造任务，**它自己会受 `thin`/裁剪新语义影响**（dogfooding）。新语义须在本任务的 P1 声明中即被使用或显式豁免，否则「新机制首跑即例外」会削弱可信度。
- **RM-AG0078 的「跨登记簿编号」无唯一边界**：登记簿 id 的唯一边界只是「同一文件内唯一」（`agate-debt-check.py` 口径）。加来源标注是**约定**，难以机械强校验——须避免设计成又一个「声明无消费」的字段（**否则本任务在 C 子批上重犯 A 子批要修的错**）。

## env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`；开发另需 `ruff`（CI 锁 `0.16.4`）
- **本机环境**：`~/.agate` 为版本管理布局（`current` 指针）；`~/.agate/scripts/` 是**稳定版**，双向工作区纪律——跑 gate/读卡片用 `~/.agate`，改代码/跑测试在 worktree
- **`check-protocol-consistency.py` 必须用 worktree 自己的**（`python3 agate/scripts/...`）——用 `~/.agate` 的会扫稳定版目录而非本次改动
- 一致性基线：**386 WARNING / 0 ERROR**（改动须保持 0 ERROR；WARNING 数变化须逐条解释）
- **改动面全部触发 SELF-GATE**（`agate/scripts/*.py` / `agate/**/*.md` / `agate/rules/*.yaml`）→ 须走独立评审 + `self-gate-review:` 引用

## executor_env

- **worktree**：`git worktree add .worktrees/agate-TAG0038 -b feat/TAG0038-value-knob-wiring`，流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0038.md` 按模板全 9 节填写
- **稳定版工具**：`~/.agate/scripts/`（**勿动**）；编排/派发类工具一律用稳定版（AGATE_ROOT 自解析；worktree 相对路径会注入未发布机制）
- **证据来源**：`agate-workspace/roadmap/roadmap.md` 的 RM-AG0071 / RM-AG0074 / RM-AG0078 条目（含 6 旋钮实测表与全部数字）
- **先例参照**：`TAG0019`（风险分路由，交付了本任务要接线的 `ceremony`/`agate-risk-score.py`）、`TAG0023`（RM-AG0042 retries 强制记录——同类「声明→机械校验」接线先例）、`TAG0027`（推进侧状态机 CLI `agate-next.py`）
- **关联条目**：RM-AG0079（轻量改动通道，**前置依赖本任务**——先修接线再判断是否仍需新通道，本任务不实现）

## 裁剪倾向

- **P2 完整走**（多决策点：5 个旋钮各自的接线/删除裁决 + 存量兼容口径 + 度量数据源与落盘形态）
- **P3 保留**（接线判据、score_task 复现性、度量字段写入/读取同语义均可单测）
- **P6 不可裁**（「thin 实测减少派发数」是**行为级**验收，须端到端实跑证据）
- **P7 完整走**（跨 9 张卡 + WORKFLOW/state-machine + YAML/md 双向一致性，多文件改动）
- **P8**：协议本体改动 → 需 bump（**若裁决含「删除旋钮」则为破坏性变更，major 评估**）

## 不做的事（边界）

- **不实现** RM-AG0079（轻量改动通道）——它是本任务的后继判断，本任务只负责把接线修好
- **不实现** RM-AG0072/0073（派发成本治理，TAG0040 范围）
- **不改** RM-AG0077 列出的 check 脚本健壮性（TAG0039 范围）——本任务**不碰**真空通过、formatter、roadmap 解析器等
- **不改** hook 三件套与 SELF-GATE 机制
- **不做** token 采集的**平台侧**新适配器开发（复用 `RM-AG0055` 已交付的三平台适配器；若某平台确实取不到，如实标 `null` 并说明，不造假数据）
