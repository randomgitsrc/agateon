---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: plan-eng-review
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

对 `P2-design.md`（TAG0032 版本管理生命周期可用性批）做独立工程方案评审，产出 `P2-review.md`。C8 映射：`domains=[backend, cli]` + `risk_level=high` → 单评审角色 plan-eng-review（去重后一个，无需组长汇总，直接写 P2-review.md）。

**只审不写**——不改 P2-design.md；评审意见由主 Agent 回派 architect 修改。

### 约束

- 产出 Header `status:` 初始 `draft`；评审完成后**必须**改为 `approved` / `rejected`（gate 读 status 字段，非返回摘要）；**agent 字段必须是 plan-eng-review（非 main）**——check-gate.py P2 硬拦截 agent=main 的 approved
- 结论须引用具体锚点（P2-design 的 §编号 / M 编号 / 候选编号 / BDD 编号 / 文件:行号），不接受裸 "approved"
- 若提「后续应重构 / 存在架构债」→ 必须用标准 DEBT 条目格式（模板 `agate/assets/templates/tech-debt-template.md`，`evidence` 必填，登记于 `{AGATE_WORKSPACE}/debt/tech-debt.md`）——强制格式不强制产出

### 本任务重点核查项（逐条给结论 + 锚点）

1. **决策 A 选 A1（resolve 侧增量探测 `_protocol_root`）是否站得住**：
   - `_protocol_root` 探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后——是否真正保证「根即协议」部署方零回归（BDD-7）？两形态皆无时返回 `vdir` 原样、下游维持 fail-closed（`resolve-entry.py:50-52`）是否正确、有无静默放行风险（I-11）
   - **`version` 推导顺序**（R1/M5）：current 链分支「先 `version=os.path.basename(cur)` 再 `root=_protocol_root(cur)`」——顺序倒置会让 `AGATE_VERSION` 从 `vX.Y.Z` 回归成 `agate`（I-1 红线）。核查 M4/M5 描述是否把顺序说死、BDD-6/7 用例是否逐条断言 `AGATE_VERSION`
   - **消费方影响面是否梳理全**（DEBT0016 dirname 散点教训）：§1.2 + §9 note 2 声称 `resolve_version_root` / `resolve_hook_root` / `resolve_agate_root` / `resolve_rules_root` + `check-structure-consistency.py` + `check-yaml-schema.py` 全部经 `_resolve_version_info` 归口、无 `os.path.dirname(vdir)+"/scripts"` 旁路——**独立 grep 复核这个声明是否属实**（这是本任务最高风险面）
   - A2（install 侧提升 `agate/` 为版本根）被否的理由（R10 git worktree 一致性 + 被迫触碰 out-of-scope）是否成立，还是其实 A2 更干净
2. **决策 B 选 B1（副本 copytree）是否站得住**：B2（软链）被否理由（悬空断链 = 正是断点一要消灭的症状 + 跨平台双口径 + 与 A1 耦合）是否成立；B1 的代价（升级期须重跑 `agate-install.py latest` 刷新副本）是否被 BDD-4 判据 2 单测 + UPGRADING 生命周期节（M7）+ BDD-11 判据 3 充分锁定
3. **断点一 fail-closed 守卫（§4.1，M1）**：`os.path.islink(agate_home)` 守卫插在 `_ensure_repo` 的 `os.makedirs`/`git clone` **之前**——核查 M1 落点（`_cmd_install()` 首行 vs `_ensure_repo` 调用前）描述是否一致、是否真能保证「拒绝后不留半成品」（I-11、BDD-1）；三步指引 stderr 文案（§4.1 代码块）是否满足 BDD-2 三项同粒度命令片段 grep
4. **gate_commands（§6）固化是否完备**：P3/P5/P5_consistency/P5_shellcheck/P5_shellcheck_root/P5_counttests/P5_timeout_seconds——`P5_shellcheck_root`（新增覆盖仓库根 `install.sh`，R9）是否必要且路径对；`P5_timeout_seconds: 600`（端到端 install 归构建类档）是否合理；有无 `&&` 拼接短路反模式；`P5` 命令是否会真正跑到新增的 `integration/test_version_lifecycle_e2e.py`
5. **测试策略（M12-M15）是否覆盖 14 条 BDD 无缺口**：双 fixture（`_make_home_meta` / `_make_home_rootproto`）设计是否能真正触发 TAG0008 逃逸的元仓库 gap（I-5，不能用「根即协议」模拟 repo 代替）；端到端 fixture（M15）本地构造元仓库形态 repo + CI 无网 fallback 是否闭环；`os.symlink` 失败 → `pytest.skip` 的平台无关处理是否到位
6. **实现就绪度**：§7 files_to_read（标了行号范围的 ~25 个文件/片段）是否覆盖 P4 implementer 所需全部上下文、有无过量；方案是否清晰到 implementer 无需步骤计划即可自主实现
7. **minimal_validation（§9）**：断点一 OS 行为（makedirs 穿透软链）result=confirmed 的最小复现是否可信；resolve 探测顺序 result=not_needed 的「纯代码逻辑」声明是否写清依赖的内部函数/分支
8. **范围锁定 + 纯增量红线**：§1.2「不改什么」是否显式覆盖 out-of-scope 四项（install-offline / Windows 复制模式 / .state.yaml schema / agateon 仓库形态重构）+ 理由；`dispatch_plan`（serial 两批 scripts-tests / docs-consistency）批次边界是否对齐影响面梳理、同一文件不跨批

### 上游关联

P1-requirements.md approved（14 条 BDD，risk_level: high，implicit_coupling: true）。P1-review.md 复评 approved（代码核对锚点：resolve-entry.py:49 / agate-install.py:134 / agate_common.py:166,190,677 属实）。P0-brief scope 三段 + out-of-scope 四项锁定。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（评审对象，权威）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（14 条 BDD + §4 同类扫描四类结论）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-review.md（评审确认的合规项与代码锚点）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（scope / out-of-scope / known_risks）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-progress.md（architect 分析留痕，辅助判断覆盖度）
- /home/kity/oclab/agateon/agate/assets/review-roles/plan-eng-review.md（你的角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate_common.py（核查决策 A1 消费方归口声明——重点 `_resolve_version_info`:125-196 + 所有 `resolve_*`:198-239,663-677）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-install.py（核查 M1 守卫落点 + M2 副本落地点，434 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/resolve-entry.py（核查 BDD-8 受益方 + fail-closed 分支，68 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/check-structure-consistency.py 与 check-yaml-schema.py（核查 §9 note 2 说的 :528/:545 / :155 是否经归口、无旁路——独立 grep）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_agate_version_resolve.py 与 test_agate_version_install.py 与 test_hook_resolve_entry.py（核查双 fixture 设计可行性）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/conftest.py（fixture 契约）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体（grep） = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`；核对代码 / grep 用 read/grep 工具，不改任何文件
- 若要复跑 minimal_validation 的最小复现，用隔离 HOME（`HOME=$(mktemp -d)`，测完删），绝不动真实 `~/.agate`
- 跑 `check-protocol-consistency.py` 用 worktree 自己的（`agate/scripts/check-protocol-consistency.py --strict-errors-only`）
- bash 外层 `timeout` 30-90s；单步串行；状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review.md`
- 分阶段落盘：发现逐条追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-review-progress.md`
- frontmatter：用 `agate-md-field-set.py`（先 `--list`）能填的填；不支持的字段（trace_id/status/agent）用 Write 直接写 frontmatter，与既有 review 文件结构一致。Header 成品值：`phase: P2` / `task_id: TAG0032` / `parent: P2-design.md` / `trace_id: TAG0032-P2review-20260907` / `agent: plan-eng-review` / `type: review` / `status: draft`（评审后改 approved/rejected）

### 返回

`File: <P2-review.md 路径>` + `Status: <approved|rejected>` + 阻塞问题数量 + 一句话摘要（≤30 字）。不返回文件全文。
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
