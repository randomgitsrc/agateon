---
task_id: TAG0051
mechanism_issues:
  - "P1 卡与 P6 判据冲突：P1 卡允许/暗示的「条件式 BDD 记 N/A 不计 PASS」在**非 legacy 契约级任务**下与 `_gate_p6_structured` 的 D1（bdd 集合 == P1 全集）/D2（全 verdict PASS）**硬冲突** ⇒ 写 N/A 必致 P6 exit 1，两条路必有一错"
  - "「Not-Modify 判定」无机械依据：设计阶段用**单一字面** grep（如 `git tag`）圈定「不改什么」面 ⇒ **模式过窄会漏**（本任务同一处漏检 3 次：`version 文件`/`双路径`/`version bump` 均非 `git tag` 字面）"
  - "`declaration_files` 的 `*-review.md` glob **不锚定**，命中 `P1-progress-requirements-review.md` 这类 progress 文件 ⇒ 被当「声明文件」要求 frontmatter（命名顺序踩坑）"
  - "hook 的 phase 归属探测正则 `P[0-8]-.*\\.md$` **不锚定行首**，历史草稿 `P1-requirements.draft-*.md` 被误判为 P1 产出 ⇒ phase 归属谎报警告"
  - "`agate-md-field-set.py` 的写侧白名单与 `check-frontmatter.py`/`agate-md-field-get.py` 的合法字段集**分叉**：`ceremony`/`implicit_coupling`/`delivery`/`debt_check` 读侧认、写侧拒；且**直接拒写** `dispatch_plan`（P2 卡要求声明的字段）"
  - "P2 卡把 `dispatch_plan.batches[].output` 列为**合法可选键**并明文断言「checker 不受影响」，实测 `agate-frontmatter-check.py::MAX_DEPTH=3` 判 ERROR（深度 4）⇒ **照卡示例写就 commit 失败**"
  - "`check-gate.py P4` 的「## 新增文件核对表」判据是 `^##\\s+新增文件核对表` ⇒ **带序号的自然写法 `## 9. 新增文件核对表` 不匹配**，表存在也报 WARNING"
  - "非 legacy 任务的 `prod_touched` 字段要求覆盖每个阶段主产出（含 `P5-test-results/unit.md` 这类嵌套文件），但**无集中清单** ⇒ 本任务 4 次被 hook 拦下才补"
  - "`retries[Pn]` 的计数语义边界不清：「因打回而重做」与「同一打回周期内的后续修复」是否各计一次无明文；计数 ≥ MAX 时 `check-state-transition.py` 直接要求 PAUSED（本任务先记 3 条被拦，核对后更正为 2）"
  - "`docs/design-notes/r6-differential.sh::_error_lines` 把**所有 `GATE ` 前缀行**（含成功提示）纳入比较，比其文件头自述的「(退出码, ERROR 行集合)」**更宽** ⇒ 正常文案演进被判「兼容性差异」"
  - "R6 wrapper 类工具先例：`--after` 缺省取 corpus 内副本 ⇒ 若 corpus 建好后被 `clean -fdx`，**未提交改动被删**、证据静默空转（本次初版 wrapper 即此形态）"
---

# TAG0051 复盘 — 任务与发布解耦（任务止于 READY；Release 独立流程 + 发布门）

## 一、事实基线

- **任务**：首个**契约级**任务（`contract_level: 1`）。把不可逆对外发布动作（tag → Release）从任务 P8
  移出；任务终态 = **READY**；发布 = 独立流程 + 人工授权入口（`workflow_dispatch`）+ 机械发布门。
- **提交链**：P0 `6d0ec756` → chore `f8124050`/`38016ec2` → P1 `1d79c488` → P2 `d0ac0124` → chore `8aca306f`
  → P3 `d4e32f4f` → P4 `9771e76a` → P5 `c5bda4df` → P6 `03dcc1f7` → P6.5 `c810c19a` → P7 `da4ede21`
  → P8 `2a21d749`。（分支 `task/TAG0051-release-decoupling`，起点 `581369fc`（origin/main））
- **规模**：P4 改动面 **89 个文件**（15 个代码文件）；8 个批；**4 个实现支（A/B/C/D）+ 6 个修复支
  （R-A..R-F）**；**3 份评审 × 最多 3 轮**（首轮 + 2 次增量复审）＋ P6.5 judge。
- **验收**：**23 条 BDD** 全 PASS（P6 结构化 `results` 23/23；P6.5 judge 独立复核 **23/23**，零挑验）。
- **全量测试**：`1 failed / 2958 passed / 2 skipped` —— 唯一红 = `test_bdd_43`
  （本机 opencode CLI `debug agent`→`agents` 环境漂移，**P0 基线即同一失败**，`known-failures.md` 已登记）；
  `count-tests` 2961；consistency 0 ERROR；`check-obligations` 56/121；ruff / shellcheck 通过；
  R6 双向差分 legacy 39 / 差异 2（均 `[ALLOWED]`）/ **未匹配 0**。
- **返工**：P1 打回 2 轮、P2 打回 1 轮、P3 修复 1 轮、P4 修复 2 轮（均记 `retries`）；
  P4 期间 SELF-GATE 3 次介入（2 次 needs-revision → 1 次 approved）。

## 二、做得好的 + 可复用模式

1. **「提交前跑 gate」把问题拦在写历史之前（本任务拦下 5 类）**：非 legacy 的 `prod_touched` 缺字段、
   **漏跑 `agate-inject-card.py`**（卡片块为空 → hash 校验不符）、`## 9.` 序号标题不匹配标题正则、
   **整份 `P4-implementation.md` 缺失**、P7 的 `prod_touched`。**每一次都在 commit 前**，无一漏到 CI。
   ⇒ 可复用：**把「跑 gate」当交付流程的固定一步，而不是事后补救**。
2. **独立评审抓到了主 Agent 自己的两次失误**（SELF-GATE 首轮）：
   ① 我**只跑新测试与批级 filter、漏跑全量**——它用 `git archive HEAD` 建副本对照，**证明 54 个红是
   本 diff 引入而非存量**；② 我的 **R6 证据"空转"**（`clean -fdx` 删掉副本里未跟踪的新文件 ⇒
   `--after` 退回 HEAD(P3)，那次「差异 0 条」**根本没比本次改动**）。
   ⇒ 可复用：**"我通过了"必须能被第三方用独立手段复现**；**证据要验证"它到底比了什么"**。
3. **评审后的改动必须增量重审**（本任务严格执行）：首轮评审针对修复前的树 ⇒ 修复轮完成后**重派同角色**
   审增量，避免「评审针对旧树、提交的是新树」。cso 因此**自复跑**确认 SEC-01/04 闭合（不采信我的转述表）。
4. **越界即上报的纪律**：R-E 发现 3 条残留**不在其授权 8 文件内** ⇒ **不改、如实上报**，主 Agent 得以
   精确点名给 R-F 收口。反之若各自"顺手改"，会造成越界冲突。
5. **P6.5 judge 的信息隔离落到实位**：黑名单**明列主 Agent 自己写的 `*-dispatch-context-*.md`**
   （承载主 Agent 的意图与措辞）⇒ judge 只能读 P1/P2/证据/git ⇒ 结论未被引导；
   且它对可复现条目**自行重跑命令**（非阅卷）。
6. **判据单源**：`delivery` 规格改读契约快照、CHANGELOG 判据单挂 `check-changelog.py`、
   `default_branch()` 单源 —— 与 ADR-014 一致；S-3b（卡 ↔ `phases.yaml` 的 gate 命令双向一致性）
   **机械地**抓出了卡片与数据面的失配（该失配会**阻断 commit**）。

## 三、发现的问题

1. **「不改什么（Not-Modify）」的判定靠单字面 grep ⇒ 同一处漏检三次**（本任务最贵的一课）：
   第一次用 `git tag` 漏掉 `version 文件`/`双路径`；第二次用 `git tag/version 文件/bump-version/tag 已创建`
   仍漏掉 **`version bump` 字面**。结果：反向传播残留分两轮才清完（`WORKFLOW.md`、`state-machine.md`、
   `implementer.md`、`P5-verification.md`、卡片/模板、两个 README）。
2. **设计层低估破坏半径**：登记 `level-2.yaml` 使协议 `current_level` 1→2，而 hook 强制「新任务必须登记
   当前等级」⇒ **所有非 legacy 新任务都变成等级 2**、枚举收紧随之生效。设计当初只笼统写「仅对非 legacy
   且 level ≥2 生效」，**未分析"全局抬升"这一后果**；`UPGRADING.md` 一度写「（无破坏性变更）」，
   由 SELF-GATE 揪出后改为「面向新任务的**准入行为变化**」。
3. **P1 引入的防御语义与 P6 判据硬冲突**：我为防"恒 PASS 计数虚高"引入「N/A 不计 PASS」，
   而 `_gate_p6_structured` 的 D1/D2 要求「bdd 集合 == P1 全集 + 全 PASS」⇒ **契约级任务写 N/A 必炸 P6**。
   由 P1 第 2 轮评审判 needs-revision 拦下（改为一条穷尽分支 BDD）。
4. **`retries` 计数语义边界不清**（见机制 issue 第 9 条）：我先记 3 条被 `check-state-transition.py`
   拦下要求 PAUSED；核对后确认 P4 实际只被打回 2 次（第 3 条是同一打回周期内的收尾）⇒ 更正。
   **若非我先按"轮数"计数，本不会撞上 PAUSED 门槛**；反之，**若真的三次打回，这个门槛是正确的**。
5. **非 legacy 任务的 `prod_touched` 覆盖面无集中清单** ⇒ 本任务被 hook 拦 4 次
   （P1-requirements / P2-design / P5 unit.md / P7-consistency）。
6. **两个 glob 的误判**（机制 issue 3/4）：`*-review.md` 命中 progress 文件；`P[0-8]-.*\.md$` 未锚定
   行首导致文件名里含 `P1-` 的草稿被误判阶段产出。
7. **写工具与 schema 分叉**（机制 issue 5/6）：`ceremony` 等写不进、`dispatch_plan` 直接拒写、
   `batches[].output` 照卡写就 commit 失败 ⇒ 派发纪律要求「不得手写 frontmatter」时执行者两难。
8. **一次"看起来绿、实际没比"的证据**（见二.2②）——这类**静默空转**比失败更危险，因为它会让人以为
   验证过了。

## 四、改进措施

| # | 措施 | 落点 | 状态 |
|---|------|------|------|
| 1 | **Not-Modify 判定改用「语义族」正则**（`version bump|版本 bump|bump-version|version 文件|双路径|tag 已创建|git tag|v\{prev_version\}`），并在 P1/P2 卡片写明「单字面 grep 不足以圈定 Not-Modify 面」 | P1 卡「同类扫描」/ P2 卡「影响面梳理·不改什么」 | **本任务已在 R-E/R-F 按此法收口**（grep 38→35）；建议上收为卡片条文 |
| 2 | **全量回归是 P4 的必跑项**（不许只跑新测试 + 批级 filter） | P4 卡自查条目 | 本任务已登记于 P4 记录；建议上收 |
| 3 | **"证据成立性"须自证**：凡是"差异 0 条/全绿"类结论，须能回答「**它到底比了什么**」（如 R6 的 `--after` 指向哪） | `docs/design-notes/` 工具约定 | 本任务已在 wrapper 头部写明成立前提 |
| 4 | **`prod_touched` 的"每阶段主产出"清单化** | `level-1.yaml` 契约 or `check-frontmatter` 提示文案 | 未登记（本任务以"被拦即补"应付） |
| 5 | **写工具白名单与 schema 对齐**（含 `dispatch_plan` 可写） | `agate-md-field-set.py` / `phases.yaml task_fields` | **DEBT0067**（open） |
| 6 | **`batches[].output` 与 `MAX_DEPTH` 的口径冲突** | P2 卡 or `agate-frontmatter-check.py` | **DEBT0068**（open） |
| 7 | **`release.preset` 无值消费方** ⇒ 明确为信息性声明或给消费点 | `UPGRADING.md` / 声明 schema | **DEBT0069**（open） |
| 8 | **`r6-differential.sh::_error_lines` 自述口径与实现不一致** | 该脚本文件头 / 新增 `kind` | **DEBT0070**（open） |
| 9 | **补登记 RM-AG0116**（编号被提交/债务/评审引用但 roadmap 从未登记） | roadmap | **已在 `f8124050` 完成** |
| 10 | **`retries[Pn]` 计数语义写进 state-machine**（"打回一次记一条；同一打回周期内的后续修复不另记"） | `state-machine.md` / `state-transitions.md` | 建议登记（本任务仅更正+留痕） |
| 11 | **Phase 归属/声明文件的两个 glob 锚定化**：`P[0-8]-.*\.md$` → `^P[0-8]-`；`*-review.md` → 明确排除 `*progress*` | `pre-commit-gate.py` / `level-1.yaml` | 建议登记 |
| 12 | **「## 新增文件核对表」判据放宽**（允许序号前缀） | `check-gate.py` | 建议登记（本任务以去序号绕过） |

## 技术债登记核对清单

| 条目 | 标题 | 状态 | 来源 |
|------|------|------|------|
| DEBT0067 | `agate-md-field-set` 可写 key 白名单与 `check-frontmatter.py` 口径分叉（含拒写 `dispatch_plan`） | open | 本任务 P1 实测 + P2 扩面 |
| DEBT0068 | P2 卡 `batches[].output` 合法 vs `MAX_DEPTH=3` 判 ERROR | open | 本任务 P2 实测 |
| DEBT0069 | `release.preset` 声明无任何值消费方 | open | 本任务 P2 复评析出 |
| DEBT0070 | `r6-differential.sh::_error_lines` 口径比自述更宽 | open | 本任务 P4 修复轮析出 |
| RM-AG0116 | 协议不假设项目分支（编号此前未登记入 roadmap） | **done**（`f8124050` 补登记） | 本任务 P1 复核发现 |

> 本任务**未新增代码缺陷类债务**；4 条 DEBT 全是**机制/工具口径**问题，均**先于本任务存在**
> （非本任务引入），本任务只做了"如实登记"。

## agate 反馈

1. **`P2§output` 的卡与 checker 冲突**（DEBT0068）建议优先修：它使**照文档写就失败**，
   是最容易被后来的使用者撞上的坑。
2. **写工具白名单与 schema 单源化**（DEBT0067）：当前「读侧认、写侧不认」使派发纪律
   「不得手写 frontmatter」在多个字段上**无法执行**，只能靠 agent 自行判断，属可预防的摩擦。
3. **建议在 P2 卡「影响面梳理·不改什么」节加一条硬提示**：圈定 Not-Modify 面时用**语义族**而非单字面，
   并把它写进 P1「同类扫描」的判据（本任务因此漏检三次，代价是两轮返工）。
4. **`retries` 语义建议在 state-transitions.md 明文定义**（本任务因计数口径差异撞上 PAUSED 门槛）。
5. **`level-*` 契约级快照的"全局抬升"后果建议在 P2 卡提示**：登记新一级 = 抬高 `current_level` 并改变
   **所有项目新任务**的准入，属**面向新任务的准入行为变化**，`UPGRADING` 必须如实框定。
