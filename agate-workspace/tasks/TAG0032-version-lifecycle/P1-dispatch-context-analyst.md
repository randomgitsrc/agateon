---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0032
role: analyst
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

产出 `P1-requirements.md`（需求基线）：**TAG0032 版本管理生命周期可用性批（RM-AG0058 整合 epic）**——修复 TAG0008 v1 版本管理"全新机器 → 版本布局 → 项目钉版 → 更新"全链路的三个断点。需求须覆盖 P0-brief `scope` 锁定的三段（拆成三组 BDD 分组，全局连续编号）：

1. **入口断链修复**：`agate-install.py` 检测 `agate_home`（`~/.agate`）为软链时 **fail-closed 拒绝**（exit 非 0 + 可操作迁移指引：备份软链 → 建目录根 → 装版本），防 `os.makedirs(exist_ok=True)` 穿透软链把 `repo/` 主克隆与 `vX.Y.Z` worktree 静默建进源仓库 `agate/` 内部（2026-09-07 隔离 HOME 实测：repo 实体落 `src/agate/repo`）；install 完成后**建立根 `~/.agate/scripts/`**（版本工具副本 or 软链到 `repo/agate/scripts/`——副本 vs 软链维护语义差异留 P2-design 决策，P1 只声明"装完 README 入口命令须存在可执行"这一验收行为）；`install.sh` 补 `--versions` 模式或等价文档指引，让新机器有官方路径从零进版本布局
2. **元仓库 gap 修复（RM-AG0058 本体）**：GitHub 装出的 `vX.Y.Z` = agateon 整仓（协议在 `agate/` 子目录），resolve 命中版本返回 vdir（仓库根），gate 消费方找 `vdir/scripts/pre-commit-gate.py` 不存在（实际在 `vdir/agate/scripts/`）→ 钉 `.agate-version` 后 commit 被阻断。修复方向二选一（P2-design 决策，P1 只定验收行为）：resolve 命中版本目录后探测 `vdir/agate/scripts` 存在则返回 `vdir/agate`；**或** install 在 worktree 检出后把 `agate/` 内容提升为版本根。**行为纯增量**：探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后，"根即协议"部署方（版本目录直接含 scripts/）必须继续可用
3. **update 统一入口**：文档面对齐两种布局的生命周期指令（legacy = `git pull`、版本布局 = `agate-install latest` 幂等）；`agate/UPGRADING.md` 增补"版本管理生命周期"节（安装/迁移/更新/回退一张图）；hook 重装时机写明（薄壳固定 + resolve-entry 机制下通常无需随版本重装）

**测试维度**（P1 须转成对应 BDD）：软链状态 install 拒绝（exit 非 0 + 指引文案断言）；根 scripts/ 建立（装后 `~/.agate/scripts/agate-install.py` 可执行）；resolve 对 `vdir/agate` 探测（元仓库形态新用例）；**端到端**：真实 clone 形态（元仓库）装 → 钉版 → resolve → gate 路径存在（模拟"根即协议" repo 保留作对照）。端到端用真实 GitHub 元仓库形态（隔离 HOME），不能用"根即协议"模拟 repo 代替（TAG0008 教训）；CI 无网则该 BDD 标 skip + 本地验收记录补证进 P6-evidence。

产出必须满足 P1 gate：≥1 条 BDD（`#### BDD-NN:` 标题格式，全局连续编号，Given/When/Then）、无行首 `[NEED_CONFIRM]`（无待确认写 `[NO_NEED_CONFIRM]`）、无 `status: GAP`、含「同类扫描」结论、P0-brief 时效性质疑记录、frontmatter 声明 `risk_level`/`phases`/`packages`/`domains`。

### 约束

- **行为纯增量（P0-brief 核心约束，不可违反）**：resolve 探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后；"根即协议"部署方必须继续可用，不得破坏既有解析语义
- **Linux 现状是基线**：现有全量 pytest 全绿是回归底线；新增用例平台无关（不硬编码单平台假设、不裸 `python3`、不假设 POSIX symlink 语义、不用 `/tmp` 字面量——用 pytest `tmp_path`）
- **install 软链拒绝须给迁移指引**：拒绝信息含可操作路径（备份软链 → 建目录根 → 装版本），否则自断现网 legacy 用户（含本机 `~/.agate`）升级路——这是行为变更，P1 须有 BDD 锁定"拒绝 + 指引文案"
- **端到端验收用真实 GitHub 元仓库形态**（隔离 HOME `HOME=$(mktemp -d)`），不用"根即协议"模拟 repo 代替；CI 无网 → skip + 本地验收记录补证
- **TDD（改脚本工作流）**：P1 不写测试，但 BDD 须设计为可先写失败测试确认红 → 改脚本转绿；`check-debt`/`check-gate` 等消费方语义改动前先 grep 全部消费方（DEBT0016 教训）
- **范围锁定**：若分析发现需改动超出 P0-brief `scope` 锁定范围（`out-of-scope` 明确排除：pack-offline 适配 / Windows 复制模式专项 / `.state.yaml` schema 扩字段 / agateon 仓库形态重构），**在 P1 标 `[NEED_CONFIRM]` 停下**，不擅自扩范围
- **SELF-GATE 触发面**：本任务改 `agate/scripts/*`（agate-install.py / agate_common.py / resolve-entry.py）+ 文档面（README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md / install.sh）→ 触发 SELF-GATE；P1 需求不必含 self-gate 流程本身（协议既有机制），但 BDD/正文应列出预期触发文件清单以利 P8
- **judge 已启用**：`.state.yaml` 已写 `judge.enabled: true`（主 Agent 已置），P1 不需再动
- 需求基线是"活的、向前累加"：BDD 用 Given/When/Then 写"做完后应表现成什么样"，不写实现方案；resolve/install 的具体探测实现、副本 vs 软链取舍属 P2-design，P1 只定验收行为

### 同类扫描（强制节，结论写进 P1 正文）

1. grep 全仓 `makedirs` / `exist_ok` 在安装路径相关脚本（agate-install.py / install-offline*）——软链穿透风险是否只此一处，其他建目录点是否同类隐患
2. grep resolve 语义消费方：`resolve_workspace` / `resolve_rules_root` / vdir 拼 `scripts` 的所有点（agate_common.py / resolve-entry.py / hook 薄壳 / check-gate.py / agate-summary.py / agate-next.py）——resolve 返回值语义变更（返回 `vdir/agate`）影响面清单，确认无直接拼 `vdir/scripts` 的旁路（DEBT0016 dirname 推导散点教训）
3. grep 版本布局解析链：`.agate-version` / `.agate-root` / `AGATE_ROOT` 探测点——元仓库形态适配是否波及离线包解析、Windows 复制模式解析
4. grep 文档面 update/升级指引：README / UPGRADING / SETUP 里"git pull" / "agate-install" / "重装 hook" 的散落位置——update 统一入口要收敛哪些现有表述
- 每条命中：记录命中数量 + 文件清单，逐条判定"本次处理 / 本次不处理 + 理由"；本次不处理的进 roadmap 或写清为何不构成同一问题；同类未来新增 → 声明回归拦截手段（新增测试 / gate 脚本 / 文档约定）并转成对应 BDD

### 上游关联

P0-brief 已锁定（task / scope / out-of-scope / known_risks / env_constraints / executor_env）。roadmap 条目 RM-AG0058（scheduled，2026-09-07 扩写整合为 epic，关联 TAG0032）是本任务立项依据。TAG0008 是被修复的 v1 版本管理机制（解析内核完整、生命周期外壳断裂）。任务工作区 = `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/`（含 P0-brief.md + .state.yaml phase=P1）。

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P0-brief.md（任务简报，权威——scope/out-of-scope/known_risks 是 P1 边界）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/.state.yaml（任务状态 phase=P1，judge.enabled=true）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/HANDOFF-TAG0032.md（交接单：双工作区纪律 / 隔离 HOME 验证纪律 / 三断点证据）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace/roadmap/roadmap.md（RM-AG0058 条目全文，第 66 行附近）
- /home/kity/oclab/agateon/agate/assets/execution-roles/analyst.md（角色定义，稳定版）
- /home/kity/oclab/agateon/agate/phase-cards/P1-requirements.md（P1 阶段卡，稳定版；本 dispatch-context 末尾已注入）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-install.py（同类扫描对象：软链穿透源，434 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate_common.py（同类扫描对象：resolve_workspace / resolve_rules_root 等归口，1050 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/resolve-entry.py（同类扫描对象：hook 解析入口，68 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/agate-resolve.py（版本解析 CLI，46 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/install.sh（新机器入口脚本，55 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（升级指引，738 行——update 统一入口落点）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/SETUP.md（接入步骤，250 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/README.md 与 README.zh-CN.md（入口命令来源）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/AGENTS.md（项目开发指引：双工作区 / 改脚本工作流 / 测试平台无关约束）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/tests/unit/（既有版本相关用例：test_agate_version_install.py / test_agate_version_resolve.py / test_agate_workspace_resolve.py / test_hook_resolve_entry.py / test_agate_install_uninstall.py / test_install_offline.py——理解现有测试覆盖形态，判断元仓库 gap 为何没被测出）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；{agate_root}（稳定版，读卡片/角色/编排脚本用）= `/home/kity/oclab/agateon/agate`（= `~/.agate`，legacy 软链）；**改造对象（要 grep / 要被改的仓库本体）= `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`**（含其内的 `agate/` 子目录）。grep 同一段代码要区分"稳定版 ~/.agate（工具）"与"worktree（改造对象）"两个副本——扫描以 worktree 为准。

### 客观查证信息（本机实测，硬约束）

- 解释器用 `/usr/bin/python3`（pytest 9.0.3 / pyyaml 6.0.1 已装）；ruff 用 `~/.venvs/agate-dev/bin/ruff`（0.16.4）
- 全量测试分片 + 并行：`/usr/bin/python3 -m pytest agate/tests/unit/ -n auto`（regression / integration 同）；gate / consistency 单跑不并行
- 一致性用 **worktree 自己的**脚本：`/usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（须 0 ERROR）；编排/派发类工具（inject-card 等）用 `~/.agate/scripts/` 稳定版（TAG0016 教训）
- **本机 `~/.agate` 是 legacy 软链（指向主 checkout `agate/`）——开发与验收全程不得破坏**；涉及安装路径的验证一律用隔离 HOME（`HOME=$(mktemp -d)` 级别，测完清理），绝不在真实 `~/.agate` 上做安装实验
- **主 checkout `/home/kity/oclab/agateon` 禁止改动**（协议本体 + hook 的 AGATE_ROOT）；改代码 / 跑测试全在 worktree
- bash 一律外层 `timeout`（30-90s，按命令预期耗时）；读文件优先 read/grep/glob 工具；单步串行不并行 bash
- 状态标记：`[PROD_NOT_TOUCHED]`（本任务不涉及生产环境）
- 产出路径是硬约束：写 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-requirements.md`
- 分阶段落盘：每读完一个输入文件 / 关键步骤，把发现追加写入 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P1-progress.md`
- 产出 frontmatter 用 `agate-md-field-set` 填写（先 `--list` 看清单），不手写、不复制示例代码块；返回前跑 `/usr/bin/python3 agate/scripts/check-frontmatter.py {P1-requirements.md 路径}`，非 0 先修
- Header 成品值（用 agate-md-field-set 逐个写入）：`phase: P1` / `task_id: TAG0032` / `parent: P0-brief.md` / `trace_id: TAG0032-P1-20260907` / `agent: analyst` / `type: problems` / `status: draft` / `created: 2026-09-07`

### 返回

只返回两行：① P1-requirements.md 路径；② 一句话摘要（≤30 字）。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P1

路径：phase-cards/P1-requirements.md
---
# P1 — 需求基线

> 当前状态：[首次 / 重试 #N]
> P1 不可裁剪（核心阶段）

## 如果是首次进入本阶段

1. 派发 analyst subagent → 产出 P1-requirements.md
   1.1 写 P1-dispatch-context-analyst.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 主 Agent 确认：BDD 验收条件 ≥1 条 + 无未决 NEED_CONFIRM
2.5 派发 requirements-review subagent（角色文件：{agate_root}/assets/review-roles/requirements-review.md）
     2.5.1 写 P1-dispatch-context-requirements-review.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
    输入：P1-requirements.md
    产出：P1-review.md（agent≠main，含 BDD 编号引用 + 覆盖维度标注）
    review 不通过 → analyst 修改 → 再 review → … → approved（⑩迭代循环）
3. 预跑 check-gate.py P1（exit 2，主 Agent 自判）
4. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P1，不要提前写 P2——phase = 本 commit 的产出阶段
5. git commit -m "wf({Txxx}-P1): {摘要}"（phase=P1，P1 产出含 P1-requirements.md + P1-review.md）
6. P1 commit 完成后进入 P2：**phase 推进 P2 随 P2 产出 commit 一起**（P2-design.md + P2-review.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（BDD 不完整 / domains 声明错 / NEED_CONFIRM 未处理）
→ review 不通过时：analyst 修改需求 → 重派 requirements-review → 共享 retry 预算
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P1 MAX=3）

## 前置条件

- [ ] P0-brief.md 完成（四字段齐全）

## 派发

- **角色**：analyst（`{agate_root}/assets/execution-roles/analyst.md`）
- **输入**：P0-brief.md（env_constraints / known_risks / executor_env）
- **输出**：P1-requirements.md
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md`

## 复杂需求编排（模式 4，条件触发）

需求复杂（多来源 / 多模块 / 无法预先拆清范围）时，P1 可先派**侦察 subagent**（模式 4 先理解后拆，见 dispatch-protocol「派发编排机制」）读全貌后再拆需求：

1. 侦察 subagent 读 P0-brief + 相关上下文，产出拆分方案（拆成哪些子需求、各子需求的输入/产出/依赖）
2. 按方案派 analyst（并行或串行）分别产出需求基线
3. 合并时定义**合并语义**（在侦察产出中声明，P7 一致性检查依赖）：
   - **BDD 全局编号**：各子需求承接的 BDD 编号全局唯一（`#### BDD-NN:`），不允许各子需求各自从 1 编号
   - **包归属去重**：每个 BDD 明确归属唯一包，跨包的共享件单独列出，不允许两个子需求各写一份

## 产出规格

P1-requirements.md 必须包含：
- BDD 验收条件（至少 1 条，Given/When/Then 格式）
- `domains:` 声明（backend / frontend / mcp / security）
- `packages:` 声明（受影响的包/模块）
- `risk_level:` 声明（low / medium / high）→ 决定 P2 评审强度
- `ceremony:` 声明（thin / standard / full）→ 仪式深度档位（可选，缺省 standard，fail-closed：不声明或声明要素不满足一律按 standard 处理，不做薄化）
- `phases:` 裁剪声明（跳过哪些阶段 + 理由）
- `judge:` 启用声明（RM-AG0039 强制）：机制后新任务（P1 `created` ≥ `judge_required_since`，见 `agate/rules/dispatch.yaml`）P1 初始化须在 `.state.yaml` 写 `judge.enabled: true`——check-gate P1 机械校验（缺失/未启用 → exit 1）；历史任务（created < 截止或未声明）缺块 → 跳过
- `capability_requirements:` 能力需求声明（available / supplementable / GAP 三态）
- 无未决 `[NEED_CONFIRM]`（有则 PAUSED）；无待确认项时写 `[NO_NEED_CONFIRM]`

`risk_level`/`phases`/`packages`/`domains` 写在文件头 **frontmatter**（`---` 分隔块），不写正文。
**可直接复制的完整样例**：
```yaml
---
phase: P1
task_id: TAG0001           # 替换为实际任务编号
type: problems
parent: P0-brief.md
trace_id: T001-P1-20260101 # {task_id}-P1-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: analyst
# ── v2.0 机器字段 ──
risk_level: low             # low / medium / high，必填
ceremony: standard          # thin / standard / full，可选；缺省 standard（fail-closed）
phases: [P1, P4, P5, P6, P8]   # list of P\d+，必填
packages: [pkg-a]           # list，必填
domains: [backend, frontend]  # list，必填
# 可选字段：override / implicit_coupling / coupling_checklist / internal_only /
# internal_only_reason / 跳过风险 / design_trivial / follows_existing_pattern
# ── RM-AG0039 judge 启用声明（写在 .state.yaml，非 P1 frontmatter）──
# 机制后新任务（P1 created ≥ judge_required_since，rules/dispatch.yaml "2026-08-22"）必须
# 在 .state.yaml 写 judge.enabled: true——check-gate P1 机械校验，缺失/未启用 → exit 1
# ── v2.0 refactor 任务类型声明（可选，缺省 = 功能任务）──
# change_type: refactor   # 当前仅支持 refactor；枚举非法值由 frontmatter schema 拦截
# ── TAG0007 项目阶段声明（可选，缺省 = established，向后兼容）──
# project_phase: bootstrap   # bootstrap（0→1 新项目）/ established（既有项目，缺省值）；
#                             # bootstrap 时 P2 architect 需额外产出 P2-skeleton.md（骨架声明）
# ── TAG0006 UI/UX 渲染形态声明（可选，presence 语义：缺失 = 常规布局型默认，不红基线）──
# ui_render_shape: render_component   # str，规范形态值：layout（布局型）/ render_component
#                                     # （渲染组件型，仅举例 OpenGL/WebGL/Canvas/图表/模型/特效/
#                                     #  地图/数字地球）/ temporal_effects（时序特效型）；开放集合可扩
# ui_ux_dimensions: [渲染正确性, 动效时序]  # list，从 UX 分类框架选适用维度；渲染组件/时序特效
#                                     # 类形态必填，常规布局型可省略
# ── v2.0 标记"已解决/已确认"状态（可选，仅标记存在时写）──
# need_confirm_resolved: []   # list[str]：已解决的 NEED_CONFIRM 项描述（逐条匹配正文）
# suggest_resolved: []        # list[str]：已采纳的 SUGGEST 项描述
# scope_resolved: []          # list[str]：已解决的 SCOPE+ 项描述
---
```

**UX 类别 BDD 与分类框架（domains 含 frontend 时必做）**：frontend 任务的 P1 必须含至少一条
UX 类别 BDD，并按实际 UI/渲染形态声明 `ui_render_shape` + 从 **UX 分类框架**（布局结构/
渲染正确性/交互行为/动效时序/视觉呈现等示例性开放集合）选 `ui_ux_dimensions` 维度，类别写入
BDD 标题后缀（如 `#### BDD-3: 渲染正确性：...`）。判据必须可量化（渲染正确性 → 渲染结果对比 +
diff 阈值或输出断言；时序 → 帧/时间戳对齐；动效 → 过渡/动画关键帧与结束状态断言；手势交互 →
动作输入的坐标/参数量化），禁主观词。缺失形态声明/维度选择/UX BDD → requirements-review 打回，
P1 gate 在"声明了形态但维度为空"或"维度不在分类框架且未在 BDD 标题声明"时 exit 1。

**人工体验路径验收（强制节）**：任务产出含**用户可见页面**且**页面内容受 seed 数据影响**时，
P1 必须追加一条**人工体验** BDD，句式强制为「Given seed 数据 → 页面有内容」（验证用户按文档 seed 后
页面在人工体验路径下确实渲染出内容）；不得只用 fixture 或单测断言替代人工体验路径验收。

**NEED_CONFIRM 分级**：
- `[SUGGEST: 推荐 X，理由 Y]` - 有倾向但求确认。主 Agent 可自行采纳倾向（除非涉及破坏性变更/业务方向），不必问用户
- `[NEED_CONFIRM]` - 真无方向需人定夺。阻塞推进，主 Agent 问用户

## ceremony fail-closed 声明 checklist（TAG0019，BDD-7/8/9）

`ceremony:` 声明仪式深度档位（thin / standard / full），缺省 standard（fail-closed——不声明或声明要素不满足一律按 standard 处理）。声明 **thin**（薄仪式）时，P1 必须连同以下四要素一起声明，缺一 → check-routing exit 1，档位回退 standard：

1. **申请**：`ceremony: thin` 显式声明
2. **逐信号 checklist**：`coupling_checklist: [...]` 流式声明（判据 `^coupling_checklist:\s*\[`，复用 check-pruning）
3. **跳过风险评估**：`跳过风险:` 声明（复用 check-pruning 判据）
4. **P5/P6 保留**：`phases` 含 P5 与 P6（薄化仪式不薄化验证，P5/P6 由 check-routing / check-pruning 双闸兜底）

不声明（存量/新任务缺 ceremony 字段）→ standard，不拦截。`ceremony: full` 的任务 `phases` 必须含 P7（P7 不可裁，缺失由 requirements-review 审声明拦截，BDD-14）。

### M3 验收锚度量协议（BDD-12，机制文档供提取）

thin 档跳过 LLM 评审的 M3 验收锚四要素：

1. **评审轮数**指标：任务在 P2/P4 阶段派发的 LLM 评审 subagent 轮数（含重试轮）
2. **真实发现数**指标：评审产出中被采纳或阻止了真实问题的条数（排除非阻塞建议、排除机械检查可抓项）
3. **TAG0018 基线值**：4 场 LLM 评审 ≈0 净收益（17 条非阻塞 + 1 条真实发现且机械检查可抓）
4. **不达标决策规则**：「LLM 评审真实发现 ≈ 0 且机械 gate 已覆盖 → 回滚 standard」

## 同类扫描（强制节）

需求基线必须含一次**同类扫描**结论——被报告的那一处几乎从来不是唯一的一处。P0 卡片的「同类/影响面预判」给出粗粒度量级，P1 在此基础上把清单做实：

1. **扫描动作**：对问题涉及的关键符号（函数名、字段名、配置键、协议节标题、错误文案）用 grep/rg 扫全仓，记录**命中数量 + 文件清单**
2. **逐条判定**：每个命中标"本次处理 / 本次不处理 + 理由"。本次不处理的同类实例要么进 roadmap，要么写清为何不构成同一问题
3. **回归拦截**：若同类问题未来还会新增（不是一次性修完的存量），需求里要声明拦截手段（新增测试 / gate 脚本 / 文档约定），并转成对应 BDD
4. **结论落盘**：扫描结论写进 P1-requirements.md 正文（不是只写在 progress 里）；即使结论是"已确认只此一处"也要显式写出，空白不算做过

同类扫描缺失 → requirements-review 打回（"只修被报告的那一处"是 agate 反复复发的反模式）。P2 的「影响面梳理」在本节结论上继续做候选方案级的影响域分析，三处（P0 预判 / P1 同类扫描 / P2 影响面梳理）同源、逐级细化，不重复劳动。

## verification_env vs supplementable 边界判断树

`capability_requirements` 三态（available / supplementable / GAP）和 `verification_env`（运行环境声明）经常被混用——TAG0009 的 11.7 小时就是把一个环境问题错标成 `supplementable` 导致的。P1 声明时按下面的判断树走：

```
先问：缺的是能力还是环境？
├─ 缺的是「agent 侧的能力」（看不见图 / 不会用某工具 / 没有某技能）
│   └─ 走 capability_requirements 三态：
│      ├─ 当前就有 ................................. available
│      ├─ 当前没有，但能通过派发子角色 / 注入 skill / 换工具补上 ... supplementable
│      │   （必须在需求里写清补充方式，否则等同 GAP）
│      └─ 当前没有且补不上 ......................... GAP（阻塞，PAUSED 交人工）
└─ 缺的是「运行环境」（服务没起 / 端口没通 / 数据库没建 / 依赖没装 / 平台不支持）
    └─ 走 verification_env 声明（不是 supplementable）：
       ├─ 环境可由主 Agent 用标准操作准备好 → P1 声明 verification_env，
       │   由主 Agent 按 dispatch-protocol.md「环境准备职责边界」统一准备
       └─ 环境本质不可得（权限/凭据/平台原生不支持）→ 这是不可重试类，
           按 dispatch-protocol.md「verification_env 失败处理协议」立即升级人工
```

**判别口诀**：换个更强的模型/角色就能做 → 能力问题（supplementable）；换谁来做都得先把服务起起来 → 环境问题（verification_env）。**把环境问题标成 `supplementable` 属于机制误用**，不算"环境故障"，不消耗验证轮次预算，应立即改正声明方式。

**环境验证轮次预算占位声明位**：声明了 `verification_env` 的任务，P1 需求里留一行轮次预算占位（默认止损轮次 = 2 轮，与阶段 `retries[Pn]` 独立计数），供 P5/P6 派发时由主 Agent 在 dispatch-context 中接续记录"当前第几轮 + 历次已排除假设"。数值与完整规则的权威定义在 dispatch-protocol.md「verification_env 失败处理协议」，本卡片不重写：

```yaml
verification_env: "debug server http://127.0.0.1:3001 + tests/fixtures/test.db"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

## P0-brief 时效性质疑

analyst 拿到 P0-brief 后不默认它仍然成立——立项与实际启动之间可能已经漂移（跨会话恢复、任务搁置后重启、从 PAUSED 恢复）。P1 阶段必须做一次时效性质疑，判据（严重 3 条 / 轻微 2 条）的权威定义见 P0 卡片「P0-brief 时效性自检（漂移判据）」，本节只定标记规则与处理方式：

**标记格式**（行首声明，一个漂移点一行，必须写出**具体漂移点**，不允许只写标记裸词）：

```
[P0_STALE: executor_env 声明的 CI 镜像已下线，当前实际跑在 ubuntu-24.04]
[P0_STALE: task 描述的 .sh 路线已全量 Python 化，目标方案本身不再成立]
```

**阻塞 / 记录二选一**（按漂移严重程度分流，不允许"既不阻塞也不记录"地含糊推进）：

| 漂移程度 | 处理 | 落盘 |
|---------|------|------|
| **严重**（命中 P0 卡判据 1-3 任一条） | **阻塞**：停止 P1，回 P0 重新立项 / 重做可行性分析 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 说明为何判定严重；主 Agent 按 PAUSED 或回 P0 流程处理 |
| **轻微**（不命中判据 1-3） | **记录**：更新 P0-brief 对应字段后继续 P1，不阻塞 | P1-requirements.md 写 `[P0_STALE: 具体漂移点]` + 已更新哪个字段 |
| 无间隔 / 已核对无漂移 | 继续 | 写一行"已核对 P0-brief 时效性，无漂移"，空白不算做过 |

## gate 规则

check-gate.py P1 → P1-review.md 存在 + status:approved + agent≠main + 含 BDD 编号锚点 → exit 2（BDD 编号格式为 `#### BDD-NN:`）；缺 P1-review.md / agent=main / 无锚点 → exit 1
P1 评审不可裁——所有任务都走独立 requirements-review，无例外

## 推进条件（全部满足才写 phase: P2）

- [ ] P1-requirements.md 含 BDD ≥1 条
- [ ] 含「同类扫描」结论（命中清单 + 逐条处理判定，"只此一处"也要写出）
- [ ] P0-brief 时效性已质疑：无漂移则记录已核对；有漂移则含 `[P0_STALE: 具体漂移点]` 且已按阻塞/记录二选一处理
- [ ] domains / packages / risk_level / phases 已声明
- [ ] 无 [NEED_CONFIRM] 标记
- [ ] 无 status: GAP（supplementable 不阻，GAP 阻）
- [ ] P1-review.md status: approved（agent≠main，含 BDD 编号锚点）

## 常见错误

1. **BDD 写成技术实现而非用户行为**：BDD 应该描述"用户能看到什么/系统应该做什么"，不是"调用哪个 API"
2. **domains 声明不全**：漏了某个受影响域 → P2 不派该域的评审 → 实现方向错误
3. **capability_requirements 漏声明**：P6 验收时才发现需要但不可用的能力 → 返工。**frontend 任务
   漏声明 vision 视觉能力条目（need 含 visual/vision）→ P1 gate exit 1 硬拦**（check-gate.py
   `_gate_p1_vision_capability`）；声明形态但漏选维度 / 形态声明与 UI/渲染形态不符 →
   同样 exit 1
4. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P2 设计依赖 domains + risk_level 决定评审角色
- P6 验收逐条对照 P1 的 BDD（PASS/FAIL 总数必须 ≥ P1 BDD 总数）
- P7 一致性检查依赖 packages 声明做跨文件交叉核对

## 评审

P1 评审通用必有（所有任务都走 requirements-review），P2/P4 评审是 C8 域触发（见 review-mapping.md）——二者在"是否通用"上不对称，仅在"独立 subagent、agent≠main"上类比。P1 评审不可裁剪。
review 不通过 → analyst 修改需求 → 再 review（⑩迭代循环），直至 approved。

> 完成 → 读 phase-cards/P2-design.md


## P1 基线保护

P1-requirements.md 是需求基线，后续阶段（P2-P8）不应直接修改。如需变更（如 P4 发现 BDD 矛盾需补充注释），必须：
1. 主 Agent 显式批准
2. 在变更处标注 `[BASELINE_CHANGE: 理由]`
3. 不改 BDD 的 Given/When/Then 语义（只补充注释/优先级说明）
4. **隐含扩展同样要授权**（TAG0025 教训）：P3/P4 的实现细节若事实上扩展了 P1 验收标准的范围（新增豁免条件、放宽/收紧某条 BDD 的判定边界等），即使当下未产生"矛盾"，也视为需要`[BASELINE_CHANGE]` 授权的情形——授权内容必须回写 P1-requirements.md 正文，不得只存在于下游阶段的 dispatch-context 口头引用中
<!-- AGATE_CARD_END -->
