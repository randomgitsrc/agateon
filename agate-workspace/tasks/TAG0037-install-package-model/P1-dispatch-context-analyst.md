---
phase: P1
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0037
role: analyst
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P1 首次派发（非重试）。

### 目标

把 `P0-brief.md` 已锁定的范围转化为正式 `P1-requirements.md` 需求基线：**子批 A–E**（A 版本目录结构契约含本体精确边界清单 / B 离线安装解析失效 P0 BUG 修复 / C GitHub Release + 本体 portable 包 / D 在线只装本体 + 保留 tag 安装 / E 彻底删除 legacy 软链支持）+ P0-brief 的 **11 条完成判据**——每个子批至少 1 条 BDD（Given/When/Then，二值可判定），frontmatter 声明齐全，含强制「同类扫描」结论与「P0-brief 时效性质疑」记录。

### 约束

1. **范围以 P0-brief 当前版本为准，不得超出**。若 P1 发现需超出范围，**不要自行扩**——写 `[NEED_CONFIRM]` 或 `[SCOPE+]`，由主 Agent 转用户裁决。
2. **用户已在本次会话给出的裁决（视为已确认，不要再写成 NEED_CONFIRM，直接写进需求）**：
   - **CI 许可**：允许新增 `.github/workflows/` release workflow 文件，**含触发条件（`on: push tags v*`）与 permissions（`contents: write`）**；不需逐项再确认，但 PR 描述须如实列出触发/权限。
   - **legacy 迁移方式**：**仅文档化迁移三步 + fail-closed 提示**（检测到 `~/.agate` 为软链时报错并打印 `mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions` 三步）；**不做迁移工具**。
   - **版本号**：沿用 0.x **minor bump**（v0.72.0），UPGRADING 明确标注 **BREAKING**；不 bump 1.0。
   - 存量用户规模：本机是唯一已知实例且已迁移——请如实核对并写进需求，不必再问用户。
3. **兼容红线**：`_protocol_root` 既有两形态探测（`vdir/scripts` 优先于 `vdir/agate/scripts`）**不得改语义、不得颠倒**，只可增量扩展；**已装旧形态 `vX.Y.Z/{agate,agate-workspace,docs,...}` 必须仍可解析**——须有独立 BDD（判据 8）。
4. **目录名固定 `agate/`**（`design-rename-execution.md` §8.1 永久保留）；BDD 不得出现"本体目录名可配置/由 manifest 声明"。
5. **本体精确边界必须写成可机械验证的 BDD**（判据 1）：给出入包/排除逐项清单（`agate/tests/`、`agate/AGENTS.md`/`CLAUDE.md`、`__pycache__`/`.pyc`、`.github/ site/ docs/ archived/ agate-workspace/`、`HANDOFF-*.md`/`CHANGELOG.md`/`pyproject.toml`/`README*`），其中**待定项（tests 是否入包、README/CHANGELOG 等）由你给出推荐并写明理由**，以 `[SUGGEST: 推荐 X，理由 Y]` 标注（P2 architect 定案前的输入）；**排除机制**（`export-ignore` / 显式清单 / `git archive`）语义不同，**P1 不选**，只写"排除清单来源可维护、可机械验证"这一需求，具体机制留给 P2 比对。
6. **判据 3/4 关键**：离线安装 e2e 测试必须**用真实 pack 产物结构**（`git worktree add` 检出整仓树的真实布局），BDD 要明确"不得再用假设 `bundle/agate/` 就是本体的假 bundle"；`test_install_offline.py::_make_bundle` 须被修正为反映真实布局（同源假设复发拦截）。
7. **判据 5 CI 实跑验证**：Release 自动创建须在**测试 tag**上实跑验证——BDD 要写清"用什么 tag/在哪验证/如何清理（不得污染正式 Release 列表）"；如无法在本地验证，明确降级口径并标 `[SUGGEST]`。
8. **判据 6 portable 不依赖 git**：隔离环境（PATH 中无 git）验证；文档**不得宣称"零依赖"**——仍依赖系统 `python3` + `pyyaml`。
9. **判据 7 量化冗余下降**：装后 `du` 对比；给出可判定阈值（如安装目录 ≤ 本体大小的 N 倍），由你据 P0-brief 实测（43M vs 本体 4.1M）给出建议阈值。
10. **子批 E 删除面**（P0-brief 已列表）：`agate_common.py` 的 `use_legacy` 参数/`islink` 分支、`install.sh` 无参软链分支、`agate-resolve.py` legacy 表述与 fail-closed 文案、4 个真 legacy 测试（`test_bdd_30_legacy_symlink_direct_root` / `test_debt0042_agate_home_legacy_symlink` / `test_tag0032_bdd_1_legacy_symlink_install_fail_closed` / `test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint`——**⚠ 排除撞名，名含 `bdd_30` 的多数与 legacy 无关，勿误删**）、`UPGRADING.md` legacy 整列/`:113` 解析表/`:809` 红线承诺改写、`README*`/`SETUP.md`（`$AGATE_DIR` 去掉 legacy fallback，统一 `~/.agate/current/agate`）、`adr.md`/`AGENTS.md`/`project-map.md`/`worktree-dogfooding-guide.md`。**判据 10 的全仓 grep 断言**（`use_legacy|legacy 软链布局` 无残留，历史注记除外）与**判据 11 的 4 平台接入命令实跑**必须各有 BDD。删除后**解析链仅剩「env → 项目声明 → current」三层**。
11. **fail-closed 提示要有 BDD**：软链 `~/.agate` 场景下 `install.sh` / `agate-install.py` / `agate-resolve.py` 的行为（报错 + 打印迁移三步 + 非 0 退出码），退出码取值由你在 BDD 中给出并说明理由。既有 `test_tag0032_bdd_1/2` 已有 fail-closed 断言——判断哪些改写保留（迁移提示）、哪些删除（legacy 直通解析）。
12. **隔离验证**：所有安装机制验证在**隔离 `AGATE_HOME`（tmp_path）**下做，**不得动真实 `~/.agate`**；BDD 的 Given 须体现。
13. **同类扫描是强制节，不能只复制 P0-brief 已有结论**：
    - `use_legacy` / `legacy` / `islink` / `软链` 全仓（排除 `.git`、`archived/`、`node_modules`）：区分「协议本体 `agate/`」「测试」「文档」「历史任务产物 `agate-workspace/tasks/`（历史，不改）」，每个命中标"本次处理 / 本次不处理 + 理由"；已知 `use_legacy` 命中 11 行 6 文件、`legacy` 命中约 40 个文件（见客观查证）；
    - **四条安装路径**（`install.sh` 无参 / `install.sh --versions` / `agate-install.py` / `agate-pack-offline.py`→`install-offline.py`）逐个核对产出结构，确认是否还有未列入 P0-brief 的路径或形态（如 `agate-install.py update/rollback/uninstall`、`agate-summary.py` 版本显示、`install-hook.py`）；
    - **`_protocol_root` 的所有调用方与同类探测**：grep `_protocol_root` / `vdir/scripts` / `agate/scripts` 探测逻辑在 `agate-resolve.py` / `resolve-entry.py` / `agate-install.py` / `install-offline.py` 中是否重复实现（hash 双实现合并是 TAG0031 先例——避免又造第二份）；
    - **版本引用/权威源文档面**：`UPGRADING.md`「版本管理生命周期」节、`SETUP.md` `$AGATE_DIR` 解析、四平台接入（Claude Code/OpenCode/DSH/Codex）里所有 `~/.agate` 用法——逐处判定；
    - **回归拦截**：删除 legacy 是"一次性存量清理"，但"legacy 残留复发"须有拦截手段（判据 10 的 grep 断言测试）；结构契约是"立规则"，须有机械验证（装后目录结构比对测试）——转成 BDD；
    - 结论写进 P1-requirements.md 正文（含扫描命令与命中数），"已确认只此一处"也要显式写。
14. **P0-brief 时效性质疑**：立项 2026-09-19 → 启动同日；期间 origin/main 有 PR #352/#353 合并（P0 补充了本体边界与 legacy 删除决策，已并入 P0-brief）。主 Agent 已核对：**无严重漂移**。你仍须独立复核（不要照抄），在正文写"已核对 P0-brief 时效性，无漂移"或 `[P0_STALE: 具体漂移点]`。
15. **frontmatter 建议值**（可据实际调整，须给出理由）：`risk_level: high`（破坏性变更 + 安装/解析主链路 + 新 CI workflow + 触 SELF-GATE，兼容性为最大风险）；`ceremony: full`（`phases` 须含 P7）；`phases: [P1,P2,P3,P4,P5,P6,P7,P8]`（不裁剪）；`domains: [backend, security]`（安装/供应链/tarball 完整性；无 frontend）；`packages: [agate-scripts, agate-docs, agate-tests, ci-workflows, install-sh]`。`judge.enabled: true` 已在 `.state.yaml`，正文提一句确认即可。
16. **无 frontend 域**：不需要 UX 类别 BDD / `ui_render_shape`。
17. **BDD 编号全局唯一**（`#### BDD-NN:`，从 BDD-1 顺序编号，按子批 A–E 分组标注归属并映射到 P0-brief 完成判据 1–11）。BDD 标题后不要写 PASS/FAIL 预判字样；有 `[NEED_CONFIRM]` 则标，无则写 `[NO_NEED_CONFIRM]`。
18. **收口 BDD**：全量 pytest（CI 口径 `--reruns 1 -n auto`，基线 **1842 passed / 2 skipped**，只增不减——删 legacy 测试导致减少须显式说明并与新增测试对账）+ consistency 0 ERROR（worktree 自己的脚本）+ ruff 0 error + shellcheck（`install.sh`）。测试计数漂移须同步 `agate/tests/` 内计数文档（`count-tests.sh`）。
19. **不改**：hook 三件套 / SELF-GATE 机制 / `.state.yaml` schema / `rules/*.yaml` 权威源 / `install-hook.py` 的 `AGATE_HOME` 语义（out-of-scope，仅在文档点明层次差别）。可加一条负向 BDD（上述文件 git diff 为空）。

### 上游关联

- P0-brief.md（权威范围来源）
- HANDOFF-TAG0037.md（worktree 根）：双工作区纪律、验证命令、阶段推进纪律、SELF-GATE 触发面
- `agate-workspace/roadmap/roadmap.md` 的「RM-AG0066 详情」节（四路径对比表 / 体积数据 / P0 机理 / 开放问题）
- 先例：`agate-workspace/tasks/TAG0032-version-lifecycle/`、`TAG0008-version-management/`
- `docs/design-notes/design-rename-execution.md` §8.1（`agate/` 目录名永久保留）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0037-install-package-model/P0-brief.md
- HANDOFF-TAG0037.md（worktree 根）
- agate-workspace/roadmap/roadmap.md（RM-AG0066 详情节）
- install.sh、agate/scripts/agate-install.py、agate/scripts/install-offline.py、agate/scripts/agate-pack-offline.py
- agate/scripts/agate_common.py（`_protocol_root` / `use_legacy`）、agate/scripts/agate-resolve.py、agate/scripts/resolve-entry.py
- agate/UPGRADING.md（「版本管理生命周期」节、`:48` 对照表、`:113` 解析优先级表、`:809` 红线）、agate/SETUP.md、README.md、README.zh-CN.md
- agate/tests/unit/test_install_offline.py、test_agate_pack_offline.py、test_agate_version_install.py、test_agate_version_resolve.py、test_agate_workspace_resolve.py、agate/tests/integration/test_version_lifecycle_e2e.py、agate/tests/integration/test_offline_bundle_roundtrip.py
- .github/workflows/protocol-tests.yml（CI 结构参考；现有 workflows：deploy-pages / docs-check / protocol-tests / site-check）

### 客观查证信息（主 Agent 已实测，你可复核）

- `use_legacy` 全仓命中 11 行 / 6 文件（`agate_common.py` 为唯一代码面，其余为 debt/历史任务产物）
- 含 `legacy` 的非归档文件约 40 个（`agate/` 协议本体 ~20、测试 ~14、文档若干）
- 现有 workflows 4 个，无 release workflow；GitHub Release 当前 0 个
- 脚本规模：`agate-install.py` 506 行 / `install-offline.py` 309 行 / `agate-pack-offline.py` 190 行 / `install.sh` 92 行
- 基线 HEAD 75a8102；CI 口径基线 1842 passed / 2 skipped
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
