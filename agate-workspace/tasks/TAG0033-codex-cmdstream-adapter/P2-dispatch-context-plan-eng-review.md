---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: plan-eng-review
---

<dispatch_guide>
> 以下派发指引是本次评审的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片。

### 目标

对 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（architect 产出，452 行，
`candidate_count: 3`，`dispatch_plan: static-batch`）做独立工程评审，产出
`agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-review.md`（`agent: plan-eng-review`，`agent != main`）。
结论 `status: approved` 或 `status: rejected`（rejected 须逐条列 BLOCKER + 引用具体设计点 / §号 / BDD 编号）。
**不通过时不要自己改设计**——写清 BLOCKER，返回主 Agent 派 architect 修改后再评审。

C8 映射：本任务 domains=[backend] + risk_level=medium → 命中「backend + 任意 → plan-eng-review」。
**单评审角色**（非 high、非 full、无 frontend）——你的产出直接就是 `P2-review.md`，无组长汇总。

### 必须核验的维度（逐项在 P2-review.md 给结论 + 证据）

1. **零改动硬约束是否守住**（P0-brief 核心约束 2 / P1 §5 / BDD-21）：P2-design.md §2.2「不改什么」是否
   显式且完整列出 `agate-cmdstream-detect.py` 检测引擎 / `agate-cmdstream-ir.py` 的 `CommandRecord` dataclass
   十字段 / 既有三适配器（`ClaudeCodeAdapter`/`OpenCodeAdapter`/`DSHAdapter`）class 体 / RM-AG0055 §3.4.3
   阈值——且方案里**没有任何一处**实际需要动它们。逐一核：`CommandRecord` 十字段是否真的够表达 Codex
   语义（看 §4.2 映射表 + §5 各设计点），`detect()` 是否真的零改动能消费 Codex 记录（CLI choices 动态
   取自 `sorted(ADAPTERS.keys())`——加第四键零改动生效）。若你发现某设计点其实需要改这些 → 标 BLOCKER。
2. **5 个设计点的方案取舍是否成立**（§5）：
   - **设计点 1 probe**：basename 正则 + 首行 `readline()` sniff `session_meta` + payload codex 标记
     （`cli_version`/`originator`/`id`）——核：只读一行是否足以区分 Codex rollout 与 Claude Code 转录
     JSONL（Claude Code 转录首行是什么？会不会也有 `session_meta`？）；路径异常/首行非 JSON 返回 False
     不抛——是否与既有 `DSHAdapter.probe` 的异常处理一致。
   - **设计点 2 事件→IR 映射**：`tool="exec"` 常量 / `command=shlex.join(item.command)` / `exit=item.exit_code`
     直取 / `exit_signal=f"exit_code={n}"` 或 `"pending"` / `output_hash=_sha1_hex(aggregated_output)`——核：
     `shlex.join` 对已经是 `["/bin/bash","-lc","..."]` 的数组是否会双重转义（BDD-4 只要求 `command` 含
     `"echo hi"`，`shlex.join` 会给内层加引号——是否仍满足"含"？）；BDD-8 非 shell 工具事件"由构造
     天然排除"是否够稳（还是需要显式 `item.type` 白名单）；BDD-9 畸形行"逐层 isinstance 守卫 + continue"
     的粒度是否覆盖 §2.1 fixture 列的三类坏行（非 JSON / 非 dict / 缺 payload）。
   - **设计点 3 session_id = `os.path.basename(session_path)`**：核 BDD-10（同文件所有记录一致——basename
     天然一致 ✔）+ BDD-12（子会话记录 session_id 指向子会话自身——子 rollout 文件名含子自身 uuid，
     minimal_validation 已证 `session_meta.session_id` 对子会话是父 id）。方案"明确不取 `payload.session_id`"
     是否落到了 §5 设计点 3 的明确文字（而非只在 dispatch-context 口头）。
   - **设计点 4 截断双信号**：`_CODEX_TRUNC_BOOL_KEYS` ∪ `_CODEX_TRUNC_TEXT_MARKERS`，比照
     `DSHAdapter._detect_truncated`——核：候选 bool 字段名 / 文本标记是否有 minimal_validation 依据（P2
     承认"未捕获截断样例"），"P5 V4 收敛锚"注释 + 1 classmethod + 2 常量的收敛面是否真的够小（P5 实测后
     只改这几处，不牵动 `read_commands` 主流程）；`truncated=True ⇒ output_hash=None` 是否无条件强制。
   - **设计点 5 list_sessions**：`os.walk` 枚举 `rollout-*.jsonl` + 根目录 `cwd if cwd else
     expanduser("~/.codex/sessions")` + 路径字符串 `sorted()`——核：`cwd` 参数语义是否与既有
     `ClaudeCodeAdapter`/`DSHAdapter` 的 `list_sessions(cwd)` 一致（它们的 `cwd` 是拿来干什么的？Codex
     按 UTC 日期分层、不按 cwd 分层——传 `cwd` 还有意义吗，还是应忽略）；`sorted()` 按路径字符串是否
     等价于按时间排序（文件名内嵌 ISO8601——跨月/跨年边界是否仍单调）。
3. **影响面梳理节完整性**（§2）：改什么（§2.1 逐文件 + BDD 编号）/ 不改什么（§2.2）/ 风险（§2.3 每条配
   缓解）三部分是否齐、是否写在候选方案（§5）之前、是否有客观证据（grep / 读过的消费方代码 /
   minimal_validation）。特别看 §2.3 的 R3（pending 形态未实测）/ R5（子会话 session_id 陷阱）缓解是否可执行。
4. **`gate_commands` 契约**（§7）：
   - `P3` 键是否为裸 `P3`（无 `P3_xxx` 检测键，P2 卡禁令 BDD-6）——本任务 `P3` 锁定两测试文件，可接受？
     （`check-tdd-red.py` 只收集 `key=="P3"`，锁定范围会否漏掉别的该红的测试——本任务新测试全在这两文件，
     判断是否 OK）
   - 无 `&&` 串联（每校验独立 key）✔ 核对
   - `P5_consistency` 用 **worktree 自己的** `python3 agate/scripts/check-protocol-consistency.py`（非 `~/.agate`）
     ——AGENTS.md line 54 要求，核对路径写对了
   - `ui_affected: false` → 无 `P5_e2e`——新测试是否真的全落单元层（无端到端）
   - `{key}_timeout_seconds` 档位是否合理（单元 120s / consistency 120s / shellcheck 60s）
5. **`dispatch_plan` 合法性**（§11 / frontmatter）：`mode: static-batch` + `parallel_limit: 2` +
   batches `[{adapter-core, medium}, {protocol-docs, low}]`——核：batches 数 ≤ parallel_limit ✔；
   `adapter-core`（class + 注册表 + 新单测 + fixture + `test_bdd_6:317` 断言改包含式）作为 TDD 同批不可拆
   是否成立；`protocol-docs`（platform-notes + SETUP）标 P7 执行是否与 P1 §9 裁剪说明一致（P7 不可裁）。
6. **`minimal_validation` 充分性**（§10）：对真实 `~/.codex/sessions/` 23 个 rollout 跑过、result: confirmed
   ——核关键断言：行封套键 `{ordinal,payload,timestamp,type}`、首行 `session_meta`、`CommandExecution` item
   有 `command`(数组)/`exit_code`(int)/`status` + `payload.started_at_ms/completed_at_ms`(epoch ms)、
   主会话 `id==session_id`/子会话 `id`≠`session_id`+`thread_source=="subagent"`。**未捕获**：截断样例、
   `item_started` CommandExecution（pending 形态）——P2 是否诚实标注这两项 `[未实测]` 并给了 P5 收敛路径。
7. **out-of-scope（§3）**：`codex exec --json` 实时流源"不做/后置"是否与 P1 §8 SUGGEST ②、P1 §4.5 实测
   （实时流不带 per-item 时间戳）一致。
8. **SELF-GATE 预告（§6）**：是否点明 P4 改 `agate-cmdstream-adapters.py`+`agate/tests/` / P7 改
   `platform-notes.md`+`SETUP.md` 触发 SELF-GATE，commit message 须含 `self-gate-review:` / `self-gate-skip:`，
   P7 派 protocol-alignment-review（A1-A6）。

### 上游关联

- **P1-requirements.md**（同目录，已 approved）——30 BDD（§6）、spike 实测（§4）、同类扫描 12 行（§3）、
  范围锁定 + 逃生阀（§5）、真机验证清单 V1-V8（§7）、裁剪说明（§9）
- **P0-brief.md**——四交付面 / out-of-scope / 核心约束 6 条；scope ① 已有 `[P0_STALE: ① 需修正]`
- **RM-AG0055 设计**：`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/` §3.4.2（差异点 4
  截断排除）/ §3.4.3（阈值）/ §3.4.4（适配器契约 + 零改动承诺）
- **既有实现**：`agate/scripts/agate-cmdstream-adapters.py`（`CommandStreamAdapter` 契约 line 95-114 /
  `DSHAdapter` line 394-621——CodexAdapter 的近亲范式，尤其 `.probe` / `.list_sessions` / `_detect_truncated`）
  / `agate-cmdstream-ir.py`（十字段）/ `agate-cmdstream-detect.py`（三态 + 阈值常量）/
  `test_agate_cmdstream_adapters.py`（:317 精确断言 / :325-333 脱敏清单）

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`（受评对象）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-progress.md`（architect 落盘的设计过程 + minimal_validation 命令）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（30 BDD + §4 spike + §5 范围）
4. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P0-brief.md`（四交付面 / 核心约束）
5. `agate/assets/review-roles/plan-eng-review.md`（你的角色定义 + 评审 checklist）
6. `agate/phase-cards/P2-design.md`（P2 产出规格 / 影响面梳理节 / gate_commands 规则 / gate 规则）
7. `agate/scripts/agate-cmdstream-adapters.py`（`CommandStreamAdapter` 契约 + `DSHAdapter` 全段 + `_sha1_hex` + `ADAPTERS`）
8. `agate/scripts/agate-cmdstream-ir.py`（`CommandRecord` dataclass 十字段）
9. `agate/scripts/agate-cmdstream-detect.py`（三态判定 + 阈值 + CLI choices 动态取法——确认零改动可行）
10. `agate/tests/unit/test_agate_cmdstream_adapters.py`（:317 `test_bdd_6_detect_consumes_registry_zero_change` 精确等值断言原文 + :325-333 `test_bdd_7_fixture_sanitized` 脱敏清单）
11. `agate/tests/unit/test_agate_cmdstream_detect.py`（三态确定性试验范式 + :371 负向断言）
12. `agate/tests/fixtures/cmdstream/dsh-session.jsonl`（fixture 结构 + 脱敏约定范式）
13. `docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`（§3.4.2 / §3.4.3 / §3.4.4）
14. `AGENTS.md`（worktree 根——改脚本 TDD 工作流、双工作区纪律、`P5_consistency` 用 worktree 脚本的要求 line 54）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，`.state.yaml` phase=P1（P2 产出 commit 随 P2-design.md
  推进 P2）/ judge.enabled=true。P1 已 commit（`4d75958`）。codex-cli 0.153.4 + ChatGPT 登录。
- **P2-design.md 结构**（主 Agent 已核）：frontmatter `check-frontmatter.py` exit 0；§2 影响面梳理节在
  §5 候选方案之前；§7 gate_commands（`P3` 裸键 / 无 `&&` / `P5_consistency` 用 worktree 脚本 / 无 P5_e2e）；
  `candidate_count: 3`；`follows_existing_pattern: [agate/scripts/agate-cmdstream-adapters.py]`（对照搬 DSH 的设计点）；
  `dispatch_plan: static-batch`。
- **architect 报告无范围外发现**（全落 P0 四交付面 / P1 §5 范围内，未触发逃生阀）——你独立核实是否属实。
- **minimal_validation 已执行**：对真实 `~/.codex/sessions/` 23 个 rollout 文件跑 <20 行 python，
  result: confirmed；未捕获截断样例（最长 output 5442 字符）与 `item_started` CommandExecution（pending 形态）。
- **P2 gate 规则**（`check-gate.py P2`）：`candidate_count ≥2`（有 `follows_existing_pattern` 时对该点可 1，
  整体仍须 ≥2）+ P2-review.md 存在且 `status: approved`（agent≠main）+ 四字段齐全
  （`packages`/`domains`/`ui_affected`/`gate_commands`）+ 含影响面梳理节。**你的产出必须 `agent != main`**。

### 产出文件字段

先 `Write` 出 `P2-review.md`（含正文），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-review.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段并逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter：`status`（approved / rejected）、`phase=P2`、`task_id=TAG0033`、`parent=P2-design.md`、
`trace_id=TAG0033-P2-review-20260909`、`created=2026-09-09`、`agent=plan-eng-review`。

正文必须含：逐维度评审结论（上方 8 项）+ 引用的具体设计点 / §号 / BDD 编号 + （若 rejected）逐条 BLOCKER。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P2

路径：phase-cards/P2-design.md
---
# P2 — 方案设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → P2 不可裁剪。design_trivial / follows_existing_pattern 可简化（1 个候选方案），不可省略。

## 如果是首次进入本阶段

1. 派发 architect subagent → 产出 P2-design.md
   1.1 写 P2-dispatch-context-architect.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 C8 映射表派评审（见下方）
3. 评审通过 → P2-review.md status: approved
4. 预跑 check-gate.py P2（脚本化检查）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P2，不要提前写 P3——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P2): {摘要}"（phase=P2，P2 产出含 P2-design.md + P2-review.md）
7. P2 commit 完成后进入 P3：**phase 推进 P3 随 P3 产出 commit 一起**（P3-test-cases.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（方案选择有误 / 候选方案不足 / 评审 rejected）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P2 MAX=3）

## 前置条件

- [ ] P1-requirements.md 含 domains / risk_level / phases 声明
- [ ] P0-brief.md env_constraints 可查阅

## 派发

- **角色**：architect（`{agate_root}/assets/execution-roles/architect.md`）
- **输入**：P1-requirements.md + P0-brief.md
- **输出**：P2-design.md
- **派发 prompt 追加**：

```
## P2 最小验证
方案设计前，先用最小验证确认关键假设（10 行 HTML 测试页 / curl 请求 / 20 行脚本）。
验证结果写入 P2-design.md 的 minimal_validation 字段。
- 方案依赖浏览器行为/安全模型/外部系统行为 → 必须做最小验证
- 纯代码逻辑 → 须在 minimal_validation 字段声明 `纯代码逻辑，无外部系统依赖`（须写明依赖了哪些内部函数/数据转换）
```

## 产出规格

P2-design.md 必须包含：
- **候选方案 ≥2** + 权衡 + 选择理由（design_trivial / follows_existing_pattern 时可只写 1 个，见下方）
- **`candidate_count: N` 必填**：本方案候选方案数（≥2，design_trivial/follows_existing_pattern 时可 1），gate 按此字段校验，不再解析标题。你写几个候选就填几个，与正文一致。
- **四字段**：`packages:` `domains:` `ui_affected:` `gate_commands:`
- **files_to_read**：实现时需要参考的文件清单（控制 P4 implementer 上下文）
- **env_constraints**：确认/细化 P0-brief 的环境约束
- **minimal_validation**：验证结果 或 声明"纯代码逻辑，无外部系统依赖"（声明时须附理由）

`candidate_count`/`packages`/`domains`/`ui_affected` 写在文件头 **frontmatter**（`---` 分隔块），
不写正文；`gate_commands:`/`files_to_read:`/`env_constraints:`/`minimal_validation:` 留正文。
**可直接复制的完整样例**：
```yaml
---
phase: P2
task_id: TAG0001           # 替换为实际任务编号
type: design
parent: P1-requirements.md
trace_id: T001-P2-20260101 # {task_id}-P2-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: architect
# ── v2.0 机器字段 ──
candidate_count: 2                # int ≥1，必填
packages: [pkg-a]                 # list，必填
domains: [backend, cli]           # list，必填
ui_affected: false                # bool，必填
ui_design_section: true           # bool，可选（presence 语义：ui_affected: true 时声明已含 UI 设计节）
---
```

**UI 设计节（`ui_affected: true` 时必含，P2 gate 校验）：** `ui_affected: true` 的 P2-design.md
正文必须包含 `## UI 设计` 节，节内含**渲染形态声明**（`渲染形态:` 声明行，复用 P1 frontmatter
`ui_render_shape` 的规范形态值 + 中文注释，gate 按规范化值比对校验 P1-P2 一致；无 P1 声明时按
布局型默认）+ **维度选择**（`适用维度:` 声明行）+ **按形态适配的 checklist**（常规布局型 =
布局/交互/视觉三类；渲染组件/时序特效型 = 渲染正确性/动效时序等适用维度 checklist；不适用的维度
显式声明"维度不适用"）。缺 UI 设计节 / 缺形态声明 / 缺按形态 checklist / P1-P2 形态声明不一致 →
P2 gate exit 1。结构规格见 `assets/execution-roles/architect.md`「UI 设计节」节（由 architect
兼任产出，不新增 designer 角色）。

**骨架产出（`project_phase: bootstrap` 时必含，P2 gate 校验）：** P1-requirements.md frontmatter
声明 `project_phase: bootstrap`（0→1 新项目；缺省 `established` 不触发）的任务，P2 architect 除
P2-design.md 外，还须在 task 目录下产出 `P2-skeleton.md`（须含 `## 骨架声明` 标题）。骨架内容以
「候选目录集合 + 项目侧声明」的参数化形式表达（不写死具体语言/框架目录名），模板见
`assets/templates/skeleton-template.md`，结构规格见 `assets/execution-roles/architect.md`
「骨架设计职责」节（由 architect 兼任产出，不新增专属角色）。`project_phase` 字段缺失或非
`bootstrap` 时不检查（向后兼容，行为与改动前一致）。

候选方案简化（须附理由，无理由视为无效声明，要求 ≥2 候选方案）：
- `design_trivial: true` + 理由（为什么 trivial）→ 可只写 1 个候选方案（P2 仍不可省略）
- `follows_existing_pattern: [src/foo.py]`（列出参照文件路径）→ 可只写 1 个候选方案，参照已有模式（P2 仍不可省略）

## dispatch_plan 机器字段（可选，TAG0014）

> 本字段是 P2 对**后续阶段编排方案**的机器声明（评估 + 编排模式，见 dispatch-protocol「派发编排机制」），由 architect 在"批次设计"节（execution-roles/architect.md）产出，P2 gate 校验其合法性。

方案含多个独立子任务（多包/多模块/high 复杂度）时，P2-design.md frontmatter 应声明 `dispatch_plan:`（单行 flow YAML，与 candidate_count 同级，**不入 frontmatter-check schema**，缺省不校验）：

```yaml
# ── v2.0 派发编排字段（可选）──
dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [{id: pkg-a, complexity: medium}, {id: pkg-b, complexity: low}]}
```

字段契约（gate 校验口径）：
- `mode` ∈ {single, static-batch, parallel, recon-then-split, serial}——编排模式（单发/静态拆批/并行/先理解后拆/串行链）
- `parallel_limit` 可选，≥1 整数——并行上限（缺省 3）
- `batches` 可选——mode ∈ {static-batch, parallel} 时每批须含 `id` + `complexity` ∈ {low, medium, high}；批数 ≤ parallel_limit
- 缺字段 / 坏 YAML → P2 gate 跳过校验，行为等同现状（向后兼容，不误拦）

## 影响面梳理（强制节）

**写候选方案之前**先做影响面梳理——方案的取舍取决于它牵动多大面，先设计再补影响面等于反过来给方案找理由。P0 卡片的「同类/影响面预判」给量级、P1 卡片的「同类扫描」给清单，P2 在这两者基础上做**候选方案级**的影响域分析，三处同源、逐级细化，不重复劳动。

P2-design.md 正文必须含影响面梳理节，覆盖三部分：

1. **改什么（Modify）**：逐文件/逐模块列出改动点 + 关联 BDD 编号；改动落点必须落到"哪个文件的哪个小节/函数"，不写"相关代码"这种模糊表述
2. **不改什么（Not Modify）**：显式列出**看起来该改但决定不改**的文件/范围 + 理由。这一栏比"改什么"更容易漏，也是 P4 implementer 判断范围边界的依据（避免"顺手改进"）
3. **风险在哪（Risk）**：每条风险配一条缓解措施；跨模块引用、双源同步（权威源 + 副本）、schema 变更、并发/资源竞争是高频风险项

梳理动作要有客观证据：grep/rg 命中清单、读过的消费方代码、既有 gate 脚本的校验口径——不是凭印象列。P1 已声明 `follows_existing_pattern` 的任务同样要做（沿用既有模式不等于影响面为零）。

## gate_commands 声明

gate_commands 在 P2 固化，后续阶段按此执行：

```yaml
gate_commands:
  P3: "pytest"                  # 可选：测试运行器（verbose 输出，供 check-tdd-red.py 自动读取）
  P5: "pytest -q --tb=no"       # 紧凑输出模式
  P5_e2e: "playwright test --reporter=line tests/e2e/"  # ui_affected: true 时必填
  P5_timeout_seconds: 120       # 可选：该 key 命令的预期耗时上限（秒），见下方字段规则
  P5_e2e_timeout_seconds: 300   # 可选：per-key 声明，不同命令类型各自取档
```

### `{key}_timeout_seconds` 字段规则

`timeout_seconds` 是 `gate_commands` 块内的**可选声明性字段**，用来给每条 gate 命令声明"预期耗时上限"，供跑命令的一方（主 Agent / subagent）据此设置 shell 层超时。四点规则：

1. **排除 P3**：`gate_commands.P3` 继续走既有 `AGATE_TDD_TIMEOUT` 环境变量机制（默认 120s，由 `agate_common.py` 的 `run_test_with_formatter()` 消费、`check-tdd-red.py` 读取，exit 124 → 超时 JSON，区分 A/B 类错误）。`timeout_seconds` **只服务 P5 / P6 / 其他非 P3 key**，不覆盖 P3。两层不合并：P3 层是运行时代码真实消费的超时，`timeout_seconds` 是给人和 subagent 读的静态声明
2. **per-key 声明**：写成 `{key}_timeout_seconds`（如 `P5_timeout_seconds` / `P5_e2e_timeout_seconds`），每条 key 各自声明，**不设整体共享默认**——单元测试与 E2E 的耗时差 2.5 倍以上，共享一个值起不到分类阈值的作用。命名与既有 `{key}_formatter` / `{key}_e2e` 的 per-key 惯例一致
3. **三档默认基准表**（**建议档位，需按命令类型手动声明，不是自动推断**——没有任何代码去"猜"命令属于哪一类）：

   | 命令类型 | 建议档位 | 依据 |
   |---------|---------|------|
   | 单元测试类（pytest / vitest 等） | 120s | 与 `AGATE_TDD_TIMEOUT` 默认值对齐，同类命令的既有锚点 |
   | E2E 类（Playwright / CDP） | 300s | 覆盖页面加载 + 多步操作；比脚本内部硬超时（HARD 90s/180s）更大——外层命令级预期时长必须留够内层完整走完的余量 |
   | 构建类（编译 / 安装依赖 / 打包） | 600s | 覆盖 `npm install` / 编译等长操作。宁可档位定高，也不要让长命令被误判失败（TPV0093 教训：`make test-quick` 挂 188 分钟） |

4. **向后兼容**：缺字段 → 行为等同现状（沿用 `dispatch_plan` 的"缺字段 / 坏 YAML → gate 跳过校验"先例），不新增强制阻断，老任务无需回填

与运行时超时纪律的关系：本字段是**静态声明**（层级 1），subagent 执行命令时真正去设 shell timeout 的是**层级 4** 的「命令超时兜底」（取值 = 预期耗时 ×1.5；本字段已声明时"预期耗时"直接取该值）。四层超时机制的完整分层见 dispatch-protocol.md「命令超时兜底与既有超时机制的分层关系」。

### env_constraints 与 gate_commands 的边界（不等价）

`env_constraints` 是**声明性字段**——它只做信息确认/注入（写清楚环境约束是什么，供 P4/P8 读取参考），本身不会被自动执行，也没有任何 gate 脚本会去校验 `env_constraints` 里写的条件是否真的成立。真正被执行的机制是 `gate_commands`：P5/P6 只会去跑 `gate_commands` 里声明的命令，不会去"执行" `env_constraints` 的内容。二者不等价，不能互相替代。

**因此**：任何需要被强制执行的约束，必须落到 `gate_commands`（有命令可跑、有 exit code 可判定），或者落到 P4/P8 阶段卡片里的明确 checklist 条目（有人工自查动作可执行）。只写进 `env_constraints` 而不落 `gate_commands`/checklist 的约束，等于没有强制力——architect 设计时若发现某条环境约束必须被强制执行，不要止步于写进 `env_constraints`。

### `--strict` 反模式：不要放进 `&&` 链路中间

`gate_commands` 的每个 key 声明的是**一条完整命令**，若把多个校验命令用 `&&` 拼接成一条命令串塞进同一个 key，会有短路问题——只要前一个命令非零退出，后面的命令（包括 `--strict` 校验）根本不会跑，看似"全部声明了"，实际后半段从未被执行过，问题被掩盖。

**反例（不要这样写）**：
```yaml
gate_commands:
  P5: "pytest -q --tb=no && check-protocol-consistency.py --strict && shellcheck scripts/*.sh"
```
上面这条命令一旦 `pytest` 失败就短路退出，`--strict` 校验和 `shellcheck` 都不会执行，历史上 TAG0004 等任务已经在这类写法上吃过亏。

**正确做法**：把每个校验拆成独立的 key 分别声明，各自独立跑、独立记录 pass/fail，不共享短路关系：
```yaml
gate_commands:
  P5: "pytest -q --tb=no"
  P5_consistency: "check-protocol-consistency.py --strict-errors-only"
  P5_shellcheck: "shellcheck scripts/*.sh"
```
`--strict-errors-only`（仅 ERROR 判失败）适合日常任务默认使用；`--strict`（WARNING-only 也判失败）保留给专门做 WARNING 债务清理的任务主动选用。

### `P3_xxx` 禁止声明（P2 卡禁令，BDD-6）

`gate_commands` 的测试命令键只允许裸 `P3`（`check-tdd-red.py` 只收集精确键
`key == "P3"`）。禁止声明 `P3_xxx` 检测键：旧解析器曾用 `startswith("P3")`
静默收集辅助键，致 TDD 误执行非测试命令。白名单后缀清单（不收集为检测命令）：
`_formatter` / `_timeout_seconds`（元键，`is_gate_meta_key` 豁免）+ `_e2e`
（E2E 形态，P5_e2e 消费，P3 永不收集）+ 历史 `_js` / `_html`（已退役，
不得复用为检测键；未来多栈回归走协议修订登记收集后缀，不走静默收集）。

### CHECK / 扫描面上线流程（DEBT0025：先全量扫描存量）

`check-platform-assumptions.py` 新增 CHECK / 扫描面上线时，先全量扫描存量
测试树登记命中清单，有命中先登记再启用常驻阻断，避免存量命中阻断正常开发。

## 评审派发（C8 机械映射）

按 P1 声明的 domains + risk_level 机械映射评审：

| domain | risk_level | 必须派的评审 |
|--------|------------|------------|
| backend | 任意 | plan-eng-review（P2 方案评审） |
| frontend | 任意 | plan-design-review |
| 任意 | high | plan-eng-review（硬规则，必须派独立 subagent） |
| 任意 | full（tier=full 或声明 ceremony: full）| plan-eng-review（硬规则，必须派独立 subagent）+ cso（security 域）+ P7 不可裁 |
| P1-requirements.md 含 [NEED_CONFIRM] 且涉及业务方向 | 任意 | plan-ceo-review |

> **去重说明**：同一任务命中多行且触发同一评审角色时，去重只派发一次（如 backend + high 均命中 plan-eng-review，只派 1 个 plan-eng-review，不重复派发）。

多个评审角色 `专家组并行` → 组长汇总 → P2-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件（示例非穷举，按 C8 映射表触发）：
   - plan-eng-review → P2-review-eng.md
   - plan-design-review → P2-review-design.md
   - plan-ceo-review → P2-review-ceo.md
   - cso → P2-review-cso.md
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长输入：所有评审文件路径
5. 组长产出：P2-review.md（统一 status: approved / rejected）。**组长 subagent 产出的 P2-review.md 的 Header agent 字段必须是组长角色名（非 main）——check-gate.py P2 硬拦截 agent=main 的 approved**
6. 组长规则：
   - 不发表新意见，只汇总
   - 任何专家标 BLOCKER → status: rejected
   - 多位专家分歧 → 标「专家组分歧」交人工
   - 全票无 BLOCKER → status: approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P2-review.md。

review 不通过 → architect 修改方案 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

**UI 测试选择器**：涉及前端时，P2 design 建议声明 UI 组件的稳定测试标识清单（如 `data-testid`，而非 class 命名）。P3 test-designer 用稳定标识定位元素，P4 implementer 按清单实现--class 命名可重构，稳定标识不变。具体方案由 P2 architect 决定。

## gate 规则

```bash
check-gate.py P2 $TASK_DIR
```

- 候选方案数 ≥2（design_trivial / follows_existing_pattern 时可只写 1 个）
- P2-review.md 存在且 status: approved（agent≠main）— 不存在 → gate exit 1
- 四字段齐全（packages/domains/ui_affected/gate_commands）
- gate_commands.P3 可选（非 pytest 项目建议声明，供 check-tdd-red.py 自动读取测试运行器）
- 候选方案 ≥2 时含权衡/选择理由

## 推进条件（全部满足才写 phase: P3）

- [ ] P2-design.md 候选方案 ≥2（或 design_trivial/follows_existing_pattern 须附理由时可只写 1 个）+ 四字段齐全
- [ ] 含「影响面梳理」节（改什么 / 不改什么 / 风险在哪 三部分齐全，且写在候选方案之前）
- [ ] P2-review.md 存在且 status: approved（agent≠main）
- [ ] gate_commands.P5_e2e 已声明（ui_affected: true 时）

## 常见错误

1. **忘了最小验证**：方案依赖外部系统行为（API MIME 类型、浏览器 CSP 等）但直接假设前提成立 → 到 P6 才发现不可行。跑一个 curl / 10 行 HTML 就能 5 分钟发现
2. **gate_commands.P5 只列单元测试**：UI 任务时缺少 P5_e2e → P5 不会跑端到端验证
3. **files_to_read 列太多文件**：把所有相关文件都列上 → P4 implementer 上下文爆炸。只列确实需要参考的
4. **忘了派评审**：按 C8 映射机械执行，不靠"觉得不需要"
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P4 依赖 files_to_read 导航代码阅读范围
- P5 依赖 gate_commands 执行验证命令
- P6 依赖 ui_affected 判断是否需要 vision-helper
- gate_commands 在 P2 固化后 P4-P6 不能改——设计阶段是声明验证契约的唯一窗口

> 完成 → 读 phase-cards/P3-tdd.md
<!-- AGATE_CARD_END -->
