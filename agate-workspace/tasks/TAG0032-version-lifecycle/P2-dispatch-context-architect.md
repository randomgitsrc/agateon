---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: architect
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。执行优先级：派发指引 > 客观查证信息 > 阶段卡片。

### 目标

产出 `P2-design.md`（方案设计 + 实现导航）：把 P1 的 14 条 BDD 转成可实现技术方案。**本任务的核心是两处「二选一」实现方向决策**（P0-brief + P1 明确划归 P2）：

1. **决策 A — 元仓库 gap 修复方向**（对应 BDD-6/7/8）：
   - 方向 A1：`_resolve_version_info`（`agate_common.py:166`）命中版本目录后，按探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后——命中后者则 `root = vdir/agate`（`version` 仍取 `vX.Y.Z` 不回归，见 I-1）
   - 方向 A2：`agate-install.py` 在 worktree 检出后，把 `vX.Y.Z/agate/` 内容提升为版本根（`vX.Y.Z/` 直接含 `scripts/` `rules/` 等），resolve 不改
   - 至少 2 个候选 + 权衡（纯增量红线：方向 A1 是解析侧增量、A2 是安装侧一次性变形；「根即协议」部署方必须继续可用；对既有 ~10 个 resolve 消费方的影响；对离线包 / Windows 复制模式的波及）+ 选择理由

2. **决策 B — 根 `~/.agate/scripts/` 建立方式**（对应 BDD-4/11，I-3）：
   - 方向 B1：副本（install 时 copy `repo/agate/scripts/` → `~/.agate/scripts/`）——升级期需重跑 install 刷新
   - 方向 B2：软链（`~/.agate/scripts` → 当前版本目录的 scripts）——跟随版本切换，repo 删则断
   - 至少 2 个候选 + 权衡（维护语义：升级期是否需重跑 install / repo 或版本目录被删的影响 / 与 resolve-entry 固定入口机制的配合 / 平台无关——Windows `ln -sf` 退化为复制）+ 选择理由；**所选语义须写进 UPGRADING「版本管理生命周期」节 + 有单测锁定**（P1 BDD-4 判据 2/3 + BDD-11 判据 3 已要求）

另需覆盖：断点一 install 软链 fail-closed 拒绝 + 三步迁移指引（BDD-1/2）、`install.sh --versions` 或等价文档路径（BDD-5）、断点三 UPGRADING「版本管理生命周期」节结构（BDD-10/11/12）、端到端隔离 HOME 测试如何构造真实元仓库形态 fixture（BDD-13/14，CI 无网 fallback）。

### 产出规格（P2 gate 硬校验）

- **候选方案 ≥2**（决策 A、决策 B 各至少 2 个候选 + 权衡 + 选择理由）；`candidate_count: N` frontmatter 必填，与正文一致
- **frontmatter 四字段**：`candidate_count` / `packages: [agate-scripts, agate-docs, agate-tests]` / `domains: [backend, cli]` / `ui_affected: false`
- **影响面梳理节**（写在候选方案之前）：改什么（逐文件 + 关联 BDD 编号）/ 不改什么（显式列 + 理由，尤其 out-of-scope：install-offline / Windows 复制模式 / .state.yaml schema / agateon 仓库形态重构）/ 风险在哪（每条配缓解）——梳理动作要有 grep 命中清单 + 读过的消费方代码为证，接续 P1 §4 同类扫描四类结论，不重复劳动
- **gate_commands**（P2 固化，后续不可改）：
  - `P3: "python3 -m pytest agate/tests/ -p no:cacheprovider"`（TDD 红灯运行器）
  - `P5: "python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto"`
  - `P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"`（worktree 自己的脚本）
  - `P5_shellcheck: "shellcheck -S warning agate/scripts/*.sh"`
  - `P5_counttests: "bash agate/tests/tests/scripts/count-tests.sh"`（用例数漂移核对——按实际路径校正）
  - 端到端隔离 HOME 测试若耗时长（clone / 多步 install）→ 声明 `P5_timeout_seconds` 或 per-key 上限（三档基准：单测 120s / 构建类 600s；网络 clone 归构建类档）
  - 不要用 `&&` 拼多命令进同一 key（短路反模式）
- **files_to_read**：P4 implementer 实现需参考的文件清单（agate-install.py 相关函数 + agate_common.py `_resolve_version_info` 及消费点 + resolve-entry.py + 相关既有测试 fixture），标行号范围，只列确实要读的
- **env_constraints**：继承 P0-brief（隔离 HOME 纪律 / 不破坏真实 ~/.agate / 双工作区 / SELF-GATE 触发面），可细化不可弱化
- **minimal_validation**：断点一涉及"makedirs 是否穿透软链""git clone 是否落入软链目标"这类文件系统/OS 行为——P0-brief 已有 2026-09-07 隔离 HOME 实测证据，architect 须在 minimal_validation 引用该证据或补一个最小复现（隔离 HOME 下 `ln -s` + `os.makedirs(exist_ok=True)` + 检查 inode）；resolve 探测顺序是纯代码逻辑，须声明"纯代码逻辑"并写明依赖了 `_resolve_version_info` 的哪段分支
- **dispatch_plan**（可选，本任务 high 复杂度）：评估后续阶段编排——脚本改动（agate-install.py / agate_common.py / resolve-entry.py）+ 文档面（README×2 / UPGRADING / SETUP / install.sh）+ 测试三部分。判断是否拆批（若拆，脚本批 / 文档批 / 测试批的边界对齐影响面梳理的文件分组，同一文件不跨批）

### 约束

- **纯增量红线（不可违反）**：无论决策 A 选哪个方向，「根即协议」部署方（版本目录直接含 scripts/）必须继续可用；探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后；不破坏既有解析语义、不改 `AGATE_ROOT` env 覆盖契约、不改 `.agate-version` 格式
- **范围锁定**：不设计 out-of-scope（install-offline 离线链路适配 / Windows 复制模式专项 / .state.yaml schema 扩字段 / agateon 仓库形态重构）——仅在"不改什么"栏记录不采纳理由；若设计中发现必须扩范围 → 标行首 `[SCOPE+]` 报主 Agent，不擅自扩
- **平台无关**：新增测试不硬编码单平台假设（`tmp_path` / 探测 `python3|python` / 不假设 POSIX symlink 语义——Windows `ln -sf` 退化复制 / 不用 `/tmp` 字面量）；决策 B 若选软链，须说明 Windows 退化行为
- **TDD 前置**：方案须让 P3 能先写失败测试确认红（元仓库形态 fixture + 根即协议形态 fixture 双 fixture）
- **消费方先梳理**：决策 A 改 `_resolve_version_info` 返回值语义前，P2 影响面梳理须列全 `resolve_version_root` / `resolve_hook_root` / `resolve_agate_root` / `resolve_rules_root` 的所有下游消费点（P1 §4 扫描 2 已列 ~10 点，P2 核实并补充）——DEBT0016 dirname 散点教训
- **SELF-GATE**：本任务改 agate/scripts/* + 文档面 → P8 commit 须含 self-gate-review/skip；P2 不含 self-gate 流程本身

### 上游关联

P1-requirements.md approved（14 条 BDD，risk_level: high，implicit_coupling: true，[NO_NEED_CONFIRM]）。P1-review.md 复评 approved。P0-brief scope 三段 + out-of-scope 四项锁定。RM-AG0058（roadmap）立项依据。任务工作区 = `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/`。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md（需求基线 + 14 条 BDD + §4 同类扫描四类结论，权威）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（scope / out-of-scope / known_risks / env_constraints）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-review.md（评审确认的合规项与代码核对锚点：resolve-entry.py:49 / agate-install.py:134 / agate_common.py:166,190,677 行号属实）
- /home/kity/oclab/agateon/agate/assets/execution-roles/architect.md（角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-install.py（决策 A2 / 断点一改动对象，434 行——重点 `_ensure_repo`:134 makedirs、arg 解析、worktree 检出段）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate_common.py（决策 A1 改动对象，1050 行——重点 `_resolve_version_info`:166、`.agate-version` 分支:183、指针链分支:190、`resolve_rules_root`:677、`resolve_hook_root`:221）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/resolve-entry.py（BDD-8 命中点，68 行——`:49` gate 路径拼接）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-resolve.py（AGATE_VERSION 输出契约，46 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/install.sh（BDD-5 新机入口，55 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（断点三落点：v0.50.0 布局表格 L546-L553 / v0.60-0.62 vs v0.66-0.68 hook 口径 / §1 通用升级步骤）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/SETUP.md（接入步骤，250 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/README.md 与 README.zh-CN.md（入口命令）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/test_agate_version_install.py / test_agate_version_resolve.py / test_agate_workspace_resolve.py / test_hook_resolve_entry.py（既有测试 fixture 形态——理解 `_make_home` / `_tag_upstream` 为何测不出元仓库 gap，为 P3 双 fixture 设计打底）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/conftest.py（fixture 约定）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体（grep / 改） = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`（= ~/.agate）。

### 客观查证信息（本机实测，硬约束）

- 解释器 `/usr/bin/python3`（pytest 9.0.3 / pyyaml 6.0.1）；ruff `~/.venvs/agate-dev/bin/ruff`（0.16.4）；shellcheck 0.9.0
- **涉及安装路径的最小验证一律用隔离 HOME**（`HOME=$(mktemp -d)`，测完删）——绝不动真实 `~/.agate`（legacy 软链）
- **主 checkout `/home/kity/oclab/agateon` 禁止改动**；设计针对 worktree
- 跑 `check-protocol-consistency.py` 用 worktree 自己的（`agate/scripts/check-protocol-consistency.py`）
- 全量测试实际路径：`agate/tests/unit/` `agate/tests/regression/` `agate/tests/integration/`；count-tests 脚本路径以实际为准（先 `ls agate/tests/scripts/` 或 `find agate/tests -name 'count-tests*'` 核对，再写进 gate_commands）
- bash 外层 `timeout` 30-90s；单步串行不并行；读文件优先 read/grep/glob 工具
- 状态标记 `[PROD_NOT_TOUCHED]`
- 产出路径硬约束：写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md`
- 分阶段落盘：每读完一个输入文件/关键步骤，追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-progress.md`
- frontmatter 用 `/usr/bin/python3 agate/scripts/agate-md-field-set.py`（先 `--list`），不手写、不复制示例代码块；返回前跑 `check-frontmatter.py {P2-design.md 路径}`，非 0 先修
- Header 成品值：`phase: P2` / `task_id: TAG0032` / `parent: P1-requirements.md` / `trace_id: TAG0032-P2-20260907` / `agent: architect` / `type: design` / `status: draft` / `created: 2026-09-07`

### P2 最小验证（派发追加）

方案设计前，先用最小验证确认关键假设（隔离 HOME + 10-20 行脚本）。验证结果写入 P2-design.md 的 `minimal_validation` 字段。
- 断点一依赖文件系统/OS 行为（makedirs 穿透软链 / git clone 落入软链目标）→ 必须做最小验证（可引用 P0-brief 2026-09-07 实测证据 + 补一个最小复现）
- resolve 探测顺序纯代码逻辑 → 声明"纯代码逻辑，无外部系统依赖"，写明依赖了 `_resolve_version_info` 的哪段分支

### 返回

只返回两行：① P2-design.md 路径；② 一句话摘要（≤30 字，说明决策 A / 决策 B 各选了什么方向）。
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
