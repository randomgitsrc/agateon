# 状态机落盘设计

> 职责边界：状态机权威源——阶段转移规则、重试上限唯一权威数值表、PAUSED 恢复机制（详见职责声明表，P2-design.md §0）

> agate，解决"LLM 不能稳定执行长循环"的问题

---

## 核心思想

**状态存在文件里，不在 LLM 的记忆里。**

LLM 不是可靠的循环执行器。让它"一直 while 下去"，跑几轮后会忘记自己在循环里、会偏离、会自己开始干活。所以 agate 不依赖 LLM 记住状态，而是每一轮都从文件读状态、执行一步、把新状态写回文件。

即使会话被压缩、中断、重启，主 Agent 重新读文件就知道接着干什么。

---

## 状态存在哪

状态分两层落盘：

### 第一层：任务看板（active-tasks.md）

记录每个任务的**当前阶段、状态、重试记录**：

```markdown
| 序号 | 任务名 | 状态 | 阶段 | 重试 | 更新日期 |
|------|--------|------|------|------|----------|
| TAG0001 | example-task | 🔄 进行中 | P4 | 0 | YYYY-MM-DD |
```

这是"宏观状态"——任务走到哪了。

**首次接入项目时，工作区（默认 `{AGATE_WORKSPACE}` = 项目根下 `agate-workspace/`）和 `active-tasks.md` 不存在，这是正常情况，不是异常**：

```
主 Agent 任何时候要读 active-tasks.md 之前，先检查：
  {AGATE_WORKSPACE}/tasks/active-tasks.md 是否存在？
    存在 → 正常读取，按下面的状态机推进
    不存在 → 这是项目第一次接入 agate：
      1. mkdir -p {AGATE_WORKSPACE}/{roadmap,tasks,agents,archived,reviews,decisions,plans,logs,debt}
         （创建 9 个子目录：roadmap/tasks/agents/archived/reviews/decisions/plans/logs/debt）
      2. 从 {agate_root}/assets/templates/active-tasks-template.md
         复制结构到 {AGATE_WORKSPACE}/tasks/active-tasks.md（清空示例数据，保留表结构）
      3. 视为"无进行中任务"，可以直接创建第一个任务（TAG0001）
```

不要把"文件不存在"误判为错误或异常，更不要因为读不到文件就假设任务已完成或卡住——这是初始化场景，唯一正确动作是建表，然后继续往下走。

### 第二层：阶段产出文件（{AGATE_WORKSPACE}/tasks/{Txxx}/Pn-*.md）

每个阶段的产出文件本身就是"这个阶段完成了"的证据。文件的 Header 里有可判定字段：

```yaml
---
phase: P2
task_id: TAG0001
parent: P1-requirements.md
trace_id: TAG0001-P2-YYYYMMDD
status: approved        # ← 门槛判定字段
---
```

这是"微观状态"——每个阶段的门槛过没过。

---

## 状态机定义

```
状态集合：{ P0, P1, P2, P3, P4, P5, P6, P7, P8, READY, DONE, PAUSED }
（P0 是主 Agent 亲自执行的简报阶段，不派发 subagent，完成后直接进入 P1）
（P6.5 是挂载于 P6→P7 转移上的**强门槛子阶段**，不是独立 phase 值：.state.yaml 的
  phase 保持 P6 直至 P7，避免扩展 valid_phases / 重试表 / 卡片枚举的连锁改动面；
  P6.5 的推进判定 = check-gate.py P6.5（=`check-judge-verdict.py` + `check-events.py`
  双脚本 exit 0），judge 轮次预算由 .state.yaml `judge.rounds` + 账本
  `judge_verdict` 事件计数（≤2）承载，不用 retries.P6.5 键）

转移规则（主 Agent 亲自跑命令验证，不靠读 subagent 产出文件字段）：
注意：所有"文件存在"判定 = 文件存在 AND 含合法 Header AND 有实质内容
     （不能只看文件存在——subagent 可能写一半崩了，留下空/半截文件）

P0 --[P0-brief.md 完成，四字段自查通过（task/known_risks/executor_env/env_constraints）]--> P1
    （四字段自查含时效性校验：立项时间与实际启动/恢复时间存在间隔时——含任务被搁置后重启、
      跨会话恢复、从 PAUSED 恢复——必须先判断 P0-brief 是否已漂移，再决定能否推进 P1。
      严重漂移（task 的目标方案不再成立 / executor_env 平台前提不再成立 / known_risks 的
      "已解决前提"实际未解决或已被他任务解决）→ 回 P0 重新立项；轻微漂移 → 更新对应字段 +
      标 [P0_STALE] 后继续。判据全文见 phase-cards/P0-orchestrator.md「P0-brief 时效性自检
      （漂移判据）」，本处不重写。
      注意：时效性校验对"任务重启"场景同样强制——不是只在首次立项时做一次；
      从 PAUSED / 跨会话恢复继续跑的任务，恢复时要重跑这一项校验。）
P1 --[P1-requirements.md 有效 AND 含至少一条 BDD 验收条件 AND 无未决 NEED_CONFIRM（不含 `[SUGGEST:]`，T080 演进）AND 无 status: GAP（不含 supplementable）AND P1-review.md status:approved AND agent≠main AND 含 BDD 编号锚点]--> P2
P1 --[P1-review.md status==rejected && retry<MAX]--> P1 (retry+1, analyst 修改需求后再 review)
P1 --[存在未决阻塞 NEED_CONFIRM]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败。倾向项 `[SUGGEST:]` WARNING 不阻塞）
P1 --[存在 status: GAP]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败。supplementable 不阻塞，见 dispatch-protocol.md「supplementable 能力的传递规则」）

任意阶段 --[出现 PROD_TOUCHED]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）（`[PROD_TOUCHED]` 正向声明触发，`[PROD_NOT_TOUCHED]` 不触发）
任意阶段 --[出现 NEED_CONFIRM（不可逆操作）]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P2 --[P2-review.md 有效 AND status==approved AND agent≠main AND P2-design.md 声明 packages/domains/ui_affected/gate_commands AND 候选方案≥2 AND 含权衡/选择理由/取舍/考量]--> P3
P2 --[P2-review.md status==rejected && retry<MAX]--> P2 (retry+1)
P2 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）
    （若 P2 设计涉及 UI：P2-design.md 必须声明 ui_affected: true，并列出需 E2E 覆盖的交互点）
    （project_phase: bootstrap 时 P2-design.md 之外还须产出 P2-skeleton.md 含「## 骨架声明」标题，P2 gate 拦截缺失，见 phase-cards/P2-design.md「骨架产出」节）
    （P1→P2 vision 三态约束：domains 含 frontend 的任务，P1 的 capability_requirements 必须已声明
      视觉能力条目（need 含 visual/vision）且 status ∈ available/supplementable/GAP——缺失会被 P1 gate 拦截）
    （ui_affected: true 时 P2-design.md 必须含 UI 设计节（## UI 设计 + 渲染形态声明 + 维度选择 +
      按形态 checklist，P2 gate 拦截缺失），形态声明复用 P1 frontmatter 的 ui_render_shape 规范值）

P3 --[scripts/check-tdd-red.py exit 0 AND assertion_failures>0 AND collection_errors==0]--> P4
    （check-gate.py P3 只检查 P3-test-cases.md 存在，红灯由主 Agent 手动跑 check-tdd-red.py + CI backstop P3 兜底确认）
    （TDD 红灯：测试正确但因实现未写而断言失败。collection/import error 视为测试本身错误）
    （若 P2 声明 ui_affected：P3 必须包含对应的 Playwright/E2E 用例，主 Agent 确认）
P3 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P4 --[暂存区含非 md/yaml 文件（git diff --cached）]--> P5
    （不能用 git diff，因为 P4 完成时会 commit，git diff 永远是空）
P4 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P5 --[P2 gate_commands.P5 命令 exit 0 AND failed==0 AND 无 [PROD_TOUCHED] 标记 AND (若 ui_affected: P2 gate_commands.P5 E2E 命令 exit 0)]--> P6
    （gate 命令从 P2-design.md 的 gate_commands.P5 动态读取，不硬编码 pytest。规则见 dispatch-protocol.md「P5/P6 gate 命令固化（B7）」节）
    （UI 任务：P5 必须实际运行 Playwright，不能跳过、不能靠"代码看起来对"判断）
    （「测试环境隔离正常」判定：
      ① 无 [PROD_TOUCHED] 标记（被动检测）
      ② 若项目有生产数据状态检查机制：对比测试前后生产库状态（记录数/checksum），
         差值 > 0 说明测试写入了生产环境 → P5 失败。
         具体检查方式由项目约定（如 conftest snapshot），agate 不硬编码路径。
      ③ 以上均为最低要求，项目应在代码层面实现强制隔离（见 README 隔离原则）。）
    （若 P5 过程中出现任何 [PROD_TOUCHED] 标记 → 立即 PAUSED，不允许进入 P6）
    （⑨ P5 subagent 化：verifier subagent 从 P2-design.md gate_commands.P5 读取命令执行，主 Agent 验 gate + N5 最小校验）
P5 --[failed>0 && retry<MAX]--> P4 (retry+1)
    （修复后必须重跑 P5 gate 全量测试，不是只检查修复项。T027 教训：修复引入回归）
    （修复重派 prompt 必须附修复历史，避免 subagent 重复踩坑。见 dispatch-protocol.md「P5 修复流程」）
    （gate 失败后主 Agent 诊断落盘 P{N}-gate-diagnosis.md，见 ⑫）
P5 --[有 PROD_TOUCHED]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）
P5 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P6 --[scripts/check-gate.py P6 exit 2（FAIL=0/证据非空）AND scripts/check-p6-provenance.py exit 0（证据-结论对应 + dispatch-context 审计 + BDD 总数对照由审计 3 自动执行，P1 `#### BDD-NN` 标题数与 P6 结果数不符时 exit 1 硬阻）]--> P6.5（judge 复核）
     ⚠️ self-authored（降级缓解：provenance 审计，根治待 Phase 3 平台支持独立 git author）
     （验收 = 把 P1 的 BDD 条件逐条实际跑一遍，结果翻译成人能看懂的行为描述）
     （涉及显示/交互的 BDD 条件：必须 Playwright 实跑 + 截图佐证，不接受"应该能工作"）
     （UI 任务 P6 双证据按 P1 vision 能力三态分档：available/supplementable（无声明默认 available）
       → vision YAML 引用 + blocker_count=0；GAP → 截图/帧序列 + 人工复核记录引用（不要求 vision
       YAML）；证据形式按渲染形态选择（常规布局型=截图/行为日志；渲染组件/时序特效型=帧序列/
       渲染输出对比/时序截图，由 check-p6-evidence.py 校验））
     （"⚠️ 调整"等中间态不合法——T019 教训：BDD-4 标"⚠️ 调整"就推进到 P7）
P6 --[任何 BDD 标 FAIL && retry<MAX]--> P4 (retry+1)（行为不符 → 回实现）
P6 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P6.5 --[judge 启用任务：存在 P6.5-judge-verdict.md AND scripts/check-judge-verdict.py exit 0（Header 字段完备 + criteria_total==P1 BDD 数 + 结论编号集零挑验 + 证据交叉核对 + 信息隔离白名单 + 预算交叉）AND scripts/check-events.py exit 0（事件账本哈希链 + ts 单调 + judge_verdict 计数 ≤2）]--> P7（TAG0020：judge 以 fresh context 逐条重验所有 BDD，只信证据与 git log，`status: passed` 才放行）
     （P6.5 是挂载于 P6→P7 的强门槛子阶段，非独立 phase 值——.state.yaml phase 保持 P6 直至 P7；
       commit-time 由 pre-commit-gate 2i.1 注入硬边界（judge.enabled && verdict 存在 → 双脚本任一
       exit 1 → 阻断 commit）；CI 由 ci-gate-backstop 兜底重跑；历史任务（.state.yaml 无
       judge.enabled: true）→ check-gate.py P6.5 早退 0，全链跳过（BDD-2））
P6.5 --[status: needs-revision / rejected]--> P6 重验（judge 复核轮次 +1；
     judge.rounds 递增 + 账本 judge_verdict 事件计数 ≤2 机械兜底；超限 → 人工接管）

P7 --[grep -E '^\s*-?\s*\[BLOCKER\]' P7-consistency.md | grep -cvE '\[BLOCKER\][:：]?\s*\d+\s*条?\s*$' → =0 AND 同理 [DEVIATION-CRITICAL] → =0 AND (grep -cE '\[DESIGN_GAP:' P7-consistency.md) == (grep -cE '\[DESIGN_GAP_REVIEWED' P7-consistency.md)（v0.6：P4 implementer 自主决策偏差声明，主 Agent 审查后追加 REVIEWED 配对标记，未配对 → gate 不通过；声明行如 `[BLOCKER]: 0 条` 被排除）]--> P8
    （已知限制：P7 定性分析不可全自动验证。主 Agent 可抽查 1-2 条一致性声明，
     完整性由 P5 回归测试兜底）
    （⑨ P7 subagent 化：consistency-reviewer subagent 执行交叉检查，N3⑨ 实质锚点校验）
P7 --[retry>=MAX]--> PAUSED（正确路由：上游问题需人工介入，非 agent 失败）

P8 --[每个声明的 package 的发布检查命令 exit 0 + 主 Agent 亲自执行 bump-version 后重跑 P5 gate（gate_commands.P5 exit 0 AND failed==0）+ 主 Agent 亲自执行 git commit + git tag + P8-release.md 含 bump_type: 字段 + version 文件双路径检查（暂存区或最近 5 commit，WARNING）+ CHANGELOG 双路径检查（暂存区或最近 5 commit，WARNING）+ git tag -l "${VERSION_TAG_PREFIX}{version}" 存在（推荐，不阻断）+ 若 roadmap.md 有关联 RM 条目须已回写 done（RM-AG0043，check-gate.py P8 反查）]--> READY
      （gate 命令集由 P2-design.md 的 packages + gate_commands 字段动态生成，不同项目不同命令，agate 不硬编码。规则见 dispatch-protocol.md「packages 动态注入（B4/B6）」节）
     （⑨ P8 subagent 化：releaser subagent 执行发布准备（产出文件 + 验证命令），主 Agent 亲自执行 bump-version + commit + tag + READY 收尾）

### READY 收尾检查（P8 gate 通过后、标记 READY 前）

P8 gate 通过 ≠ 直接标记 READY。主 Agent 必须逐项检查：

**状态与版本：**
- [ ] .state.yaml phase == READY
- [ ] active-tasks.md 任务行状态已更新
- [ ] git 工作区干净（git status 无 untracked）
- [ ] git tag 已创建

**测试环境已清理：**
- [ ] 调试服务/进程已停止（启动的 debug server、临时 daemon）
- [ ] 临时数据已删除（测试创建的临时数据库、临时文件目录）
- [ ] 测试占用的端口已释放

**开发环境已还原：**
- [ ] 开发安装已卸载（editable 安装、全局包安装等非标准安装方式已还原）
- [ ] 系统环境无污染（PATH、Python path、node_modules 等无开发残留）
- [ ] 项目依赖恢复到发布版本（非开发分支的源码挂载）

**生产环境无残留：**
- [ ] 生产数据库无新增/修改记录（对比任务前后，测试不应触碰生产 DB——若有 [PROD_TOUCHED] 则此项已失败）
- [ ] 生产服务无残留影响（生产服务加载的代码/配置仍为上次发布版本，未被开发操作覆盖）
- [ ] 生产环境无孤儿资源（测试产生的文件、缓存、定时任务等未残留在生产路径）

任一项未通过 → 不进入 READY，逐项修复后重新检查。
生产环境相关项未通过 → 立即 PAUSED 报告人工（生产残留不可自行清理）。

阶段跳过转移规则（P1 裁剪声明驱动）：
  P1-requirements.md 的「裁剪说明」声明 phases: [列表]，主 Agent 据此跳过未列出的阶段。
  跳过时，当前阶段的 gate 自动判定为"通过"，直接转移到裁剪声明中的下一个阶段。

  **裁剪条件（hook 验证，见 scripts/check-pruning.py）**：
  - P2 不可裁剪（方案设计是必经阶段。P1 analyst 做需求分析不做方案设计，无法预知 P2 architect 会发现哪些隐含问题。design_trivial / follows_existing_pattern 可简化 P2（1 个候选方案），不可省略 P2）
  - P3：仅 low 风险可裁剪（medium/high 必须走 TDD 红灯）
  - P4 不可裁剪（实现是交付底线——没有实现就没有可发布产物）
  - P5 不可裁剪（验证是交付底线——没有验证就没有可发布产物）
  - P6 不可裁剪（验收是质量最后防线。no_behavior_change 可简化 P6（快速验收），不可省略 P6。`change_type: refactor` 的任务 P6 换用回归口径（行为不变 + 全量回归全绿 + 关键路径验收）——换口径 ≠ 裁 P6，P6 仍不可裁剪）
  - 裁剪 P7：需源码文件数 ≤ 5 AND 无 implicit_coupling 声明 AND 有 coupling_checklist（列出检查过的耦合点，如 api-schema: checked, data-model: checked。防止无脑写"无隐式耦合"）
  - 裁剪 P8：需声明 internal_only: true + internal_only_reason: <理由>

  **裁剪理由格式**：每条裁剪须含"跳过风险:"评估。没有评估风险的裁剪 = 无效裁剪。
  （局限性：这是 self-declaration nudge——"跳过风险: 低"可以无脑填，但强制写一行制造"我考虑过风险"的形式义务）

  **P7 语义**：P7 是"实现是否偏离 P2 设计"，不是"是否跨端"。跨端一致性是 P7 的子集，不是 P7 的全部。
  
  **裁剪声明回写（P2.9）**：若主 Agent 决定不执行 P1 声明的裁剪（保留被裁剪的阶段），
  必须在 P1-requirements.md 追加 override 字段。

  可跳过的阶段及其跳过转移：
    跳过 P2（无设计阶段）→ P1--[P1 gate 通过]--> P3 或 P4（取决于 phases 列表）
    跳过 P3（无 TDD）→ P2--[P2 gate 通过]--> P4
      （P3 跳过时 P4 gate 不要求红灯变绿，P5 的 gate_commands.P5 全绿兜底）
    跳过 P6（无验收）→ P5--[P5 gate 通过]--> P7
    跳过 P7（无一致性检查）→ P6--[P6 gate 通过]--> P8
    跳过 P8（无发布）→ P7--[P7 gate 通过]--> DONE（仅限不涉及发布的内部任务）

  不可跳过的阶段：P1（需求基线）、P2（方案设计）、P4（实现）、P5（技术验证）、P6（验收）
    P1 基线是全流程脊梁，无论任务大小都需建立（小任务可简化，见 WORKFLOW.md 适用边界）
    P4/P5 是交付底线——没有实现和验证就没有可发布产物

  gate 判定方式：主 Agent 读 P1-requirements.md 的 phases 字段，确认跳过列表，按上述转移规则推进。
  若 P1 声明的 phases 列表与实际 gate 判定冲突（如声明跳过 P6 但 P5 发现行为不符需验收），主 Agent PAUSED 报告人工决策。

特殊转移（SCOPE+ 定向回补）：（行首声明格式：`^\s*-?\s*\[SCOPE+\]`）
任意阶段 Pn 产出含 [SCOPE+] → 主 Agent 增补 P1 基线 → 判断影响范围 → 定向回补：
  Pn --[SCOPE+ 增补基线]--> P1（仅增补 requirements.md，不重跑 P1 分析）
  → 主 Agent 判断该新需求实际需要哪些阶段，定向回到最早受影响的阶段
  ⚠️ 已知限制：「判断影响范围」目前依赖主 Agent 临场判断，无明确决策规则。
     T004/T005/T006 均未触发 SCOPE+，尚无实战数据支撑规则化。
     下一个触发 SCOPE+ 的任务应记录判断过程，供后续规则化参考。
  → 例：P5 发现需写新代码 → 回 P4；仅验收条件遗漏 → 仅补 P6
  → 回补阶段完成后，沿正常转移继续，已完成且未受影响的阶段不重跑
  retry 计数：定向回补不清零目标阶段已有的 retry（防止借回补绕过重试上限）

  **[SCOPE_RESOLVED] 标记（P2.11）**：主 Agent 增补 P1 基线时，必须标记 [SCOPE_RESOLVED: from {来源文件}]。
  未标记的 [SCOPE+] → gate 拦截（scripts/check-scope-resolved.py）。

## Pre-commit 检查全景

每次 `git commit` 触发 pre-commit hook，自动运行一整套阶段/文件级检查。完整清单（触发条件、拦截行为、多任务扫描、三类 WARNING、CI 兜底）见 `WORKFLOW.md`「Pre-commit 检查总览」——权威唯一来源，本文件不重复维护。

特殊转移：
READY --[人手动触发 make publish]--> DONE

PAUSED 恢复协议：
  PAUSED --[人工确认/决策]--> 恢复到 PAUSED 前的阶段

  恢复步骤：
  1. 主 Agent 重读该任务的 .state.yaml → 获取 PAUSED 前的阶段和 retry 计数
  2. 人工回复的内容写入 {AGATE_WORKSPACE}/tasks/{Txxx}/PAUSED-resolution.md（含 Header）
  3. 主 Agent 将 PAUSED-resolution.md 路径加入重派 prompt（"人工决策见此文件"）
  4. 按 PAUSED 前的阶段重新派发 subagent

  recovery_bonus：若 PAUSED 原因是 retry 耗尽（如 P2 retry=3/3），恢复后该阶段获得 recovery_bonus=1（允许额外 1 次重试），避免恢复后立即再次超限导致无意义循环。recovery_bonus 写入 .state.yaml 对应阶段的计数。

  PAUSED 期间 SCOPE+ 处理：
  - SCOPE+ 在 PAUSED 期间暂不处理，等恢复后一并纳入 P1 基线增补
  - 如 SCOPE+ 与 PAUSED 原因相关（如验收中发现新需求导致 NEED_CONFIRM），恢复时优先处理

进入 READY 时（P8 gate 通过后，写状态前）：
主 Agent 必须立即输出交付小结（强制，不可跳过）：
  格式见 dispatch-protocol.md「任务完成小结」模板：
    [{task_id}] READY — {task_name} {version}
    改动：{git diff --stat 提取}
    验证：{各阶段 gate check 结果 + 验收 BDD 条目通过数}
    说明：{一句话设计摘要}
    下一步：make publish（人工触发）
  这是主 Agent 对 PM 的正式交付，是任务编排层的职责。
```

每次转移后，把新状态写回 active-tasks.md。

**"有效"的定义**：文件存在 + 含合法 Header（phase/task_id/parent/trace_id）+ 有实质内容（非空、非半截）。只看"文件存在"会被 subagent 写一半崩溃留下的垃圾文件误导。

**P3 红灯的特别说明**：TDD 要求测试先失败，但"失败"有三种——
- (1) 经典红灯：测试逻辑对，因实现未写而断言不满足（assertion failure）→ 通过
- (2) B 类红灯：测试逻辑对，因依赖模块未实现而 import 失败（T027 教训：P3 test-designer 不写 stub，所以 TDD 红灯几乎都是此类）→ 通过
- (3) A 类错误：测试代码自身有语法/import 错误，根本跑不起来 → 不通过

门槛接受**前两种**（assertion failure 或 B 类 import failure），拒绝第三种。

**判定方式**：主 Agent 跑 `scripts/check-tdd-red.py`（见下），不自行解析测试输出。check-gate.py P3 只检查 P3-test-cases.md 存在。脚本通过 formatter 将测试输出标准化为 JSON，再判定 A/B 类（exit 0=红灯可推进 / exit 1=A类错误 / exit 2=绿灯违反TDD）。

**`scripts/check-tdd-red.py` 设计**：

脚本通过 **formatter** 将测试输出标准化为 JSON，再判定 A/B 类错误。formatter 在 `gate_commands.P3_formatter` 中声明（可选键，见 P2-design.md）。不提供 formatter 时退化为 exit-code-only（所有红灯 = 可推进，精度降低但不会阻断）。

**formatter 契约**：formatter 脚本接收测试运行器的原始输出（stdin），输出标准化 JSON（含 `exit_code`、`failed`、`errors`、`import_errors`、`syntax_errors` 等字段）。check-tdd-red.py 解析 JSON 判定：
- assertion 失败 / 项目内 import 失败 → B 类红灯（exit 0，可推进）
- SyntaxError / 第三方 import 失败 → A 类错误（exit 1，测试代码自身错误）
- 全部通过 → exit 2（实现先于测试，违反 TDD）
- 无可用测试运行器 → exit 3

**探测链**：`$TEST_RUNNER` 环境变量 → `gate_commands.P3`（P2-design.md 声明）→ `which pytest` → exit 3。`$TEST_RUNNER` 始终优先（退化为 exit-code-only，无 formatter）。

**formatter 选择**：见 `assets/formatters/README.md` 速查表。常用：pytest → `pytest.sh`，vitest → `vitest.sh`，go test → `go-test.sh`，其他 → `generic-exit-only.sh`。

**project_module**（可选）：gate_commands 中声明，用于 B 类 import 错误检测——区分项目内部模块未实现（B 类，可推进）和第三方依赖缺失（A 类，测试代码错误）。

**P8 与 READY 的说明**：

P8 是**「发布准备」**，不是「发布」。P8 gate 通过后进入 READY 状态——表示每个受影响包的版本 bump、CHANGELOG 更新、测试全通过，**已准备好发布**。实际的 `make publish`（上传到 PyPI）由人手动触发。

| 概念 | 含义 | 谁执行 |
|------|------|--------|
| 发布准备 (READY) | 各包 version bump + CHANGELOG + lint + test 全通过 | Subagent + 主 Agent 验证 |
| 发布 (DONE) | 上传到 PyPI | 人手动触发 |

**多包发布**：一个任务可能涉及多个独立版本的包（如 backend + mcp-server）。P8 必须为 P2 声明的**每一个** package 执行 version bump 和发布检查，gate 命令由 packages 列表动态生成。漏 bump 某个包 = gate 不通过。

---

## 主 Agent 的单步执行（一轮）

主 Agent 不跑 while 循环，而是执行"单步函数"，每次调用推进一个阶段：

> **机械化（RM-AG0054，v0.66.0）**：下面步骤 5-7（跑 gate → 按转移规则算下一状态 → 写回
> `.state.yaml` + git add）对**普通 phase** 是纯查表动作，由 `agate next`（`agate-next.py`）完成——
> 消费 `phases.yaml` 的 `next`/`retreat`/`gate_pass_exit`，不做临场判断；gate exit 1 且表有
> `retreat` 时委托 `agate-retreat-to.py` 逐阶回退（`agate advance` 是回退侧的引导壳）。P6/P6.5 的条件式
> 推进（judge 裁决）仍按下方 §「P6.5」的规则。主 Agent / 档位 C 只调用、读结果。**手工执行下面
> 全流程是 fallback**（工具不可用时）；本节的手工规格是 `agate next` 实现所依据的权威语义。

```
function 执行一步(task_id):
    1. 读 .state.yaml 或 active-tasks.md → 得到 (当前阶段, 重试记录)
       **状态标记绑定检查**（T019 教训：.state.yaml 标了 P5 但无 P5 产出）：
       .state.yaml 的 phase 标记为 Pn，但 {AGATE_WORKSPACE}/tasks/{task_id}/ 下 Pn 产出文件
       不存在 → 无效标记，回退到 Pn-1 重新执行 gate。标记前必须验证 gate。
    1.5 环境一致性验证（若 .state.yaml 含 env_state 字段）

       若 .state.yaml 含 `env_state:` 块（运行时环境状态，如 debug backend URL、test entry ID、端口等）：
       - 验证这些状态在当前环境中仍有效（具体检查方式由项目自定，如 curl health check、查询 entry 是否存在）
       - 若任一失效：重新创建对应资源，更新 .state.yaml 的 env_state，commit 修订
       - 若环境全部失效 → PAUSED 报告人工

       注意：此步骤只适用于 .state.yaml 显式记录了 env_state 的任务。
       无 env_state 的任务跳过此步骤。
    2. 若当前阶段 == P0：主 Agent 亲自写 P0-brief.md（见 dispatch-protocol.md 步骤0），完成后继续
       否则：确认 {AGATE_WORKSPACE}/tasks/{task_id}/P0-brief.md 已存在（必填字段：task/known_risks/executor_env/env_constraints）
       读 {AGATE_WORKSPACE}/tasks/{task_id}/ → 确认当前阶段输入文件就绪
    3. 派发当前阶段的 subagent（见 dispatch-protocol.md）
    4. subagent 返回摘要（路径 + 一句话）
    4.5 扫描 subagent 产出是否含 [SCOPE+] 或 [SCOPE_GAP]：
        - [SCOPE+]：发现新隐含需求 → 增补 P1 基线 → 定向回补（见特殊转移）
        - [SCOPE_GAP]：prompt 漏了 P2 已声明的改动 → 暂停修正 prompt 重派
        （subagent 的自我检查结果仅供参考，不作为 gate 判定依据——gate 以主 Agent 跑命令为准）
    5. 主 Agent 亲自跑 gate 命令验证门槛（A1 原则：跑命令不信文件）：
       - P1: P1-requirements.md 含 ≥1 条 BDD 条件（BDD 编号格式为 `#### BDD-NN:`）;
             grep -cE '^\s*-?\s*\[NEED_CONFIRM\]' {task}/P1-requirements.md → =0（仅计算阻塞项）;
             grep -cE 'status:.*GAP\b' {task}/P1-requirements.md → =0（仅匹配 status: GAP，不匹配 supplementable）
       - P2: grep 'status: approved' {task}/P2-review.md → 命中;
             grep -cE '^(packages|domains|ui_affected|gate_commands):' {task}/P2-design.md → ≥4;
             候选方案 ≥2; grep -qE '权衡|选择理由|取舍|考量|trade-?off' {task}/P2-design.md → 命中（或含"选择"+理由/原因/因为组合）
       - P3: scripts/check-tdd-red.py → exit 0（含经典红灯和 B 类 import 红灯）；
             （UI 任务：确认 P3-test-cases.md 含 Playwright/E2E 用例描述）
       - P4: git diff --cached --name-only | grep -qvE '\.(md|yaml)$|^\.state'
       - P5: 从 P2-design.md gate_commands.P5 读取命令执行 → exit 0 AND failed==0;
             grep -rlE '^\s*-?\s*\[PROD_TOUCHED\]' {task}/ → 无命中（行首锚点匹配正向声明，不匹配句中引用）;
             （UI 任务：从 gate_commands.P5 读取 E2E 命令执行 → exit 0）
         - P6: scripts/check-gate.py P6 → 脚本化部分通过（exit 2，FAIL=0/证据非空已验，BDD 总数对照由 check-p6-provenance.py 审计 3 自动执行）;
              grep -cE '^\s*- (PASS|FAIL)' {task}/P6-acceptance.md → =P1 BDD 总数（审计 3 自动执行，不符时 exit 1）;
              （UI 条件：vision-analyst YAML summary.blocker_count → =0）
       - P7: grep -E '^\s*-?\s*\[BLOCKER\]' {task}/P7-consistency.md | grep -cvE '\[BLOCKER\][:：]?\s*\d+\s*条?\s*$' → =0;
              grep -E '^\s*-?\s*\[DEVIATION-CRITICAL\]' {task}/P7-consistency.md | grep -cvE '\[DEVIATION-CRITICAL\][:：]?\s*\d+\s*条?\s*$' → =0
        - P8: scripts/check-gate.py P8 → 脚本化部分通过（exit 2）;
              从 P2-design.md gate_commands 逐包读取发布检查命令执行 → 全部 exit 0;
              从 P2-design.md gate_commands.P5 重跑 P5 命令 → exit 0 AND failed==0;
              git log v{prev_version}..HEAD --oneline 对照 CHANGELOG 条目 → 无遗漏;
              从 P2-design.md packages 验证 version 文件路径变更;
              grep -q 'bump_type:' {task}/P8-release.md → 命中;
               git diff --cached --stat → 含 version 文件变更;
               git diff --cached -- ${CHANGELOG_FILE:-CHANGELOG.md} → 非空
               （CHANGELOG 是项目根文件，默认 CHANGELOG.md；项目可用 CHANGELOG_FILE 环境变量覆盖路径）
        **若 gate 不通过**：追加至少一行到 orchestrator-log.md（记录 gate 失败阶段+原因）
     6. 计算下一状态（按转移规则）
       **回退跳变检测**（T019 教训：P5→P2 跨 3 阶段回退未 PAUSED）：
       若 current_phase_num - next_phase_num >= 2（回退 ≥2 阶段）
       → 强制 PAUSED，报告"跨 N 阶段回退，需人工确认"
       检测基于 phase 编号差值，不依赖 commit message 格式。
       例外：P5→P4（差 1，正常回归）不需要 PAUSED。
       注意：仅检查**回退**方向，不检查前向跨阶跳。前向跳（P2→P5）通常是裁剪后的合法跳变（state-machine.md:160-161），由 P5 gate 的阶段产出文件检查兜底。
    7. if 下一状态 == READY:
          输出交付小结（强制）：见「进入 READY 时」的格式要求
          再写回 .state.yaml
       else:
           写回 .state.yaml（新阶段 / 重试记录 / PAUSED）
    8. 返回：下一状态是什么
```

"一步"就是一次完整的派发 + 跑命令验证 + 状态更新。gate 判定由主 Agent 亲笔完成（或经 `agate next`
查表机械完成），不信任 subagent 产出的文件字段。

谁来反复调用？三种方式（见 loop-orchestration.md）：人工逐步、半自动、全自动 /loop。档位 C 的每步
即调用一次 `agate next`。

**ceremony（thin/standard/full）对本节的影响**：ceremony 是 P1 声明的仪式深度档位（见
`WORKFLOW.md` / `phase-cards/P1-requirements.md`），只影响 P2/P4 是否派 LLM 评审、以及 thin 档是否
跳过部分评审轮；**不改状态机转移边、不改 retry 上限、不薄化 P5/P6**（thin 档 `phases` 必须含 P5 与
P6，由 `check-routing.py` / `check-pruning.py` 双闸兜底）。转移表与本节流程对所有 ceremony 档位一致。

**受控自主再派发（RM-AG0055，v0.67.0）与本节的关系**：执行角色 subagent 在其阶段内可自主再派发
子任务（judge 例外——judge 不下放）；这不产生新的状态机转移边，仍属同一 phase，retry 计数不受影响。
其存活/卡死可观测性由命令流日志机制（`agate-cmdstream-*.py`）从平台会话记录外部提供——「证据 +
触发核查、不自动判死」，详见 `docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`。

---

## 重试上限

> 本表是重试上限的唯一权威源；`rules/state-transitions.md` 与 8 张阶段卡片均须与本表一致（CHECK 12 自动校验）。

| 阶段 | MAX_RETRY | 说明 |
|------|-----------|------|
| P1 | 3 | 需求基线，涉及需求定义 |
| P2 | 3 | 涉及方案设计 |
| P3 | 2 | TDD 红灯，少轮次 |
| P4 | 3 | 实现复杂度高 |
| P5 | 2 | 技术验证，少轮次 |
| P6 | 2 | 验收，少轮次 |
| P7 | 2 | 一致性检查，少轮次 |
| P8 | 2 | 发布准备，少轮次 |

**P6.5 judge 复核轮次预算（≤2 轮，TAG0020）**：judge 轮次是**复核预算**而非状态机重试，**不新增
`| P6.5 | N |` 表行、不使用 `retries.P6.5` 键**（保持 CHECK 12 重试表锚点与
`agate-state-yaml-check.py` 的 `^P\d+$` retries key 校验零漂移）。机械兜底 = 事件账本
`judge_verdict` 事件计数 ≤2（`check-events.py` 审计）+ `.state.yaml` `judge.rounds` 信息字段；
P6.5(needs-revision/rejected) 弹回 P6 重验计入该预算，超限 → 人工接管（BDD-8）。

重试记录按阶段独立存储于 `.state.yaml` 的 `retries` 字段，不因进入新阶段而清零。

---

## 每任务独立状态文件

除 active-tasks.md 宏观看板外，每任务有独立状态文件：

位置：`{AGATE_WORKSPACE}/tasks/{Txxx}/.state.yaml`

```yaml
task_id: TAG0001
phase: P4
status: in_progress

# 可选字段：P5 gate 通过时记录的父提交哈希（TAG0016 BDD-12，供 P6/P8 判定"引用 P5 证据、
# 不重跑"）。字段可选——缺失时 check-p6-provenance.py 审计 7 回退为强制重跑，不报错，
# 存量任务（无此字段）天然兼容。
p5_pass_commit: <40 位 git 提交哈希，可选字段>

# ── judge 机制字段（TAG0020 P6.5；历史任务无 judge 块 → P6.5 门槛全链跳过，BDD-2）──
# 未知顶层键不触发 agate-state-yaml-check 告警（其只校验 task_id/phase/status/retries）
judge:
  enabled: true            # 机制启用标记（RM-AG0039 强制化：机制后新任务——P1 created ≥
                           #   judge_required_since（rules/dispatch.yaml "2026-08-22"）——必须含
                           #   judge.enabled: true，check-gate P1 机械校验 exit 1；
                           #   历史任务（created < 截止或未声明）缺块 → 跳过）
  rounds: 1                # 已用复核轮次（主 Agent 维护；机械兜底 = 账本 judge_verdict 事件计数 ≤2）
  last_verdict: passed     # 上次 verdict status（信息用途，passed/rejected/needs-revision）
  partial: false           # 是否 partial 降级（预算超限诚实降级标记）
  judge_token_budget: 100000  # 可选：token 预算覆盖（默认 100k token）
  # 可选（高风险任务人工指定）：double_judge: true —— 文档级可选，本轮无机器校验

# ── 重试记录（T016 教训：整数计数无法区分"原样重试"和"调整策略后重试"）──
retries:
  P2:
    - round: 1
      failure_mode: quality           # quality=产出了但不够好 / empty_return=空返回 / timeout=超时
      prompt_changed: false           # 本次重试是否调整了 prompt
      adjustment: null                # 调整方式：split_task / add_navigation / switch_type / null
  P4: []                               # 空列表 = 该阶段无重试
  P5: []

retry_count: { P2: 1, P4: 0, P5: 0 }  # 派生字段 = len(retries[Pn])，向后兼容 active-tasks.md 看板

review_scores:
  P2:
    - round: 1
      reviewer: plan-eng-review
      score: 7.5
      status: rejected
      feedback: "API 限流策略未考虑并发边界"
updated: 2026-06-12

# 可选：运行时环境状态（P6 等需要运行环境的阶段记录）
env_state:
  debug_backend: "http://127.0.0.1:8888"
  test_entry_slug: "zg71s7"
  env_verified_at: "2026-06-26T03:25:00"
```

**字段说明**：
- `p5_pass_commit`（可选）：P5 gate 通过、`git add` 之前写入的父提交哈希（见
  `phase-cards/P5-verification.md`「如果是首次进入本阶段」）。缺失 → 回退语义为"无法声明
  复用，强制重跑"，不视为错误（存量任务兼容，TAG0016 BDD-12）
- `judge`（可选，TAG0020）：P6.5 独立 Judge 机制字段块。`enabled: true` ⇒ 该任务启用
  judge 门槛（P6→P7 须 check-gate.py P6.5 通过）；缺失/`false` = 历史任务，P6.5 全链跳过。
  `rounds` = 已用复核轮次（弹回 P6 重验时递增）；`last_verdict` / `partial` 为信息与降级
  标记；`judge_token_budget` 覆盖默认 token 预算（100k）。机械兜底见「重试上限」节 prose。
- `retries[Pn]`：列表，每次重试追加一条记录，`len(retries[Pn])` 即重试次数
- `retry_count`：派生字段，从 `retries` 计算，保留是为了 active-tasks.md 看板兼容
- `failure_mode`：失败模式（`quality` / `empty_return` / `timeout`），区分"产出了但不够好"和"根本没产出"
- `prompt_changed`：本次重试是否调整了 prompt，用于验证"空返回后必须改变策略"是否被遵守
- `adjustment`：具体调整方式（`split_task` / `add_navigation` / `switch_type` / `null`）

**commit 时机**：与 gate commit 同步——一次 commit 包含 stage output + `.state.yaml` 更新，避免文件与实际阶段不一致。

**phase 更新时机**：先更新 .state.yaml phase → 再 git add（含 .state.yaml + 产出文件）→ 再 git commit。state 和产出在同一个 commit 里。不要"先 commit 产出再单独 commit state"——两个 commit 会导致 hook 在第一个 commit 时读不到 phase 变更，在第二个 commit 时找不到产出文件。

**active-tasks.md 降级为汇总视图**：不再由 subagent 直接修改，由主 Agent 维护。更新规则：**owner agent 只重写自己任务那一行**（从该任务 .state.yaml 派生），不碰其他任务的行，不做全表覆写。这样多 Agent 并发时各写各的行，冲突面最小。定期（或怀疑不一致时）可从所有 `.state.yaml` 全表重建作为对账。（与 git-integration.md 策略2 一致，.state.yaml 是唯一真相源）

---

## 为什么这样能抗中断

```
场景：主 Agent 在 P4 派发到一半，会话被压缩/中断

恢复时：
   0. 这是"重新接手任务"，等同于一次新的启动：
      依次重读：orchestrator-template.md 的 mapping 表查当前阶段卡片，按卡片指引执行。
      卡片查不到的信息回退到 orchestrator-template.md「Fallback（按需查阅，不要求每轮必读）」节。
      不能假设压缩前读过的内容还在上下文里。
  1. 主 Agent 重新读 active-tasks.md → "TAG0001 在 P4，重试 0"
  2. 读 {AGATE_WORKSPACE}/tasks/TAG0001/ → P4-implementation/ 是否已有文件？
     - 有 → P4 已完成，直接判定门槛，进 P5
     - 没有 → P4 没做完，重新派发 P4 subagent
  3. 接着干
```

状态完全由文件重建，不依赖会话记忆。这是"状态落盘"的核心价值。

**协议文件同样要重建，不止任务状态**：步骤 1-3 重建的是"任务进度"，但若压缩/中断丢失的是上下文里的协议规则本身（不是任务状态），单靠重读 active-tasks.md 不够——主 Agent 会"知道任务在 P4"，但可能已经不记得 P4 派发 prompt 该怎么写、gate 该怎么判。步骤 0 解决的是这一层：协议规则和任务状态是两类不同的东西，要分别确保能重建。

**`orchestrator-log.md` 防无响应**：

文件：`{AGATE_WORKSPACE}/tasks/{Txxx}/orchestrator-log.md`，主 Agent 专用，记录关键决策和下一步——写下去就完成使命，恢复任务用 `.state.yaml` + 产出文件，不依赖此文件。

规则：
- 仅追加不编辑不整理
- 不写思考过程、不写文件内容摘要、不写 subagent 返回原文——只写决策、下一步和触发决策的简要依据（依据示例：gate 输出摘要 / BDD 编号 / 文件路径引用；不等同于展开的思考过程）
- 任务从 DONE 重新激活 → 清空后重建（旧决策基于旧上下文）；active/PAUSED 恢复 → 追加
- 另见下方「L2 会话 checkpoint」（阶段级 `P{n}-checkpoint.md` + 任务级 `task-session-summary.md`）

必须记录的事件：
- 派发 subagent 前：`NEXT: 派发 {角色} subagent 执行 {阶段}`
- gate 失败后：`GATE FAIL: {阶段} gate 不通过，原因：{错误消息摘要}`
- gate 诊断完成：`DIAGNOSIS: {根因} → FIX: {修复方案}`
- subagent 失败/空返回：`SUBAGENT FAIL: {角色} {失败原因}`
- 流程决策：`DECISION: {PAUSED/回退/跳阶}，原因：{...}`

**commit 被 hook 拦截**：同一阶段累计被拦 3 次 → PAUSED（不要无限重试，Agent 明显走进了错误路径）。

**L2 会话 checkpoint（两件套）——P{n}-checkpoint.md + task-session-summary.md**：

①**与 orchestrator-log.md 的关系**：三者互补，不是相互替代/包含。`orchestrator-log.md` 是 L1
（持续追加、逐决策颗粒度，只写"决策+简要依据"不写展开的思考过程）；`P{n}-checkpoint.md` 是 L2
的**阶段级**颗粒度（比 orchestrator-log 更粗，一阶段一条，不是逐决策一条；比 progress.md 更贴近
主 Agent 的判断视角——progress.md 是 subagent 中间产物，checkpoint 是主 Agent 对本阶段的评估）；
`task-session-summary.md` 是 L2 的**任务级**颗粒度，一次性落盘，允许包含更完整的"为什么这么做"
因果链叙述（弥补 orchestrator-log 明确排除的"思考过程"缺口）。P7/正式复盘写作时交叉引用三者，
不是二选一或三选一。

②**`P{n}-checkpoint.md` 子机制**：
- 落盘时机：主 Agent 在**每个阶段 gate 通过后、派发下一阶段之前**写盘
- 文件路径：`{AGATE_WORKSPACE}/tasks/{Txxx}/P{n}-checkpoint.md`（`{n}` 为实际阶段号，如
  `P4-checkpoint.md`），不是阶段门槛产出（gate 不要求其存在，属「辅助文件」），缺失不阻断阶段推进
- 内容颗粒度：本阶段异常/关键判断/subagent 表现，2-4 行极简记录，不要求完整叙述
- 防 compact 策略：沿用 orchestrator-log 的"写下去就完成使命"原则——写完即完成使命，不回读校验

③**`task-session-summary.md` 子机制**：
- 落盘时机：任务完成、P8 gate 通过后，进入「READY 收尾检查」节之前
- 文件路径：`{AGATE_WORKSPACE}/tasks/{Txxx}/task-session-summary.md`
- 内容颗粒度：任务级过程摘要，颗粒度更完整，允许展开因果链叙述
- 防 compact 策略：P8 gate 通过后主 Agent 亲自写盘，写完即完成使命，不需回读校验

④**两者共同覆盖的防 compact 范围**：`P{n}-checkpoint.md` 保证任务生命周期每个阶段边界都有
非空 L2 落点（覆盖"中途 compact"场景）；`task-session-summary.md` 补充任务完成时的完整因果链
叙述（覆盖"任务级复盘写作"场景）——两者时间线上互补，不是同一内容的两份拷贝。

---

## 状态标记绑定规则（T019 教训）

.state.yaml 的 phase 字段标记为 Pn+1 前，必须满足：
1. Pn 的 gate 命令已执行（主 Agent 亲自跑）
2. Pn 的产出文件存在且含合法 Header
3. gate 结果已记录在 Pn 产出文件中

**违反判据**：.state.yaml 标记 Pn+1 但 Pn 产出文件不存在 → 无效标记，回退到 Pn 重新执行 gate。

**判定方式**：主 Agent 每轮开始时（单步函数步骤 1），检查 .state.yaml 的 phase 与产出文件是否匹配。不匹配 → 按标记前的阶段重新跑 gate。

T019 中 .state.yaml 标记 P5 但 P5-test-results/ 目录不存在——状态标记先于 gate 验证，中间窗口期状态不一致。本规则把"标记"和"验证"绑定，标记不能先于验证。

---

## 重试记录也要落盘

重试记录不能存在 LLM 记忆里（会忘）。**按阶段独立记录**，写进 `.state.yaml` 的 `retries` 字段（格式见上方「每任务独立状态文件」）：

```
每次某阶段门槛失败：
  retries[Pn].append({
    round: len(retries[Pn]) + 1,
    failure_mode: quality | empty_return | timeout,
    prompt_changed: true | false,
    adjustment: split_task | add_navigation | switch_type | null
  })
  → 写回 .state.yaml
```

**关键：不要"进入新阶段就把所有计数归零"。** 否则存在绕过上限的漏洞：

```
P2 retry 用到 2/3 → approved 进 P3 → 若简单归零
P3 发现 P2 设计有问题，回退到 P2 → retry 又从 0 开始 → P2 可被反复重试远超上限
```

按阶段独立记录后，P2 的历史重试记录累积保留，即使从 P3 回退到 P2，P2 的重试次数仍在，不会被绕过。

**T016 教训**：旧格式只有 `retry_count: { P3: 0 }` 一个整数，主 Agent 3 次空返回后 retry_count 仍为 0——既无法区分"原样重试"和"调整策略后重试"，也无法事后验证"空返回后是否改变了策略"。新格式的 `prompt_changed` 和 `adjustment` 字段解决这个盲区。

**该步骤现由 `check-state-transition.py` 机械校验（RM-AG0042）**：单步回退（Pn→Pn-1）若暂存版本 `retries[目标阶段]` 长度未超过 HEAD 版本长度（不要求此前必须已有过记录，含首次单步回退）→ 阻断（exit 1）；评审 rejected 后的重派、子代理空返回重派两类事件若 `retries[Pn]` 无对应记录 → 高优 WARNING（不阻断）。不再单靠 prose 规程与人工自觉。

### 阶段回退规则

明确允许哪些回退，避免无限打转：

| 回退 | 是否允许 | 说明 |
|------|----------|------|
| P5 → P4 | ✅ 允许 | 测试失败回到实现，设计内的正常回归 |
| P2 → P2 | ✅ 允许 | 评审打回重做（同阶段重试）|
| P3/P6 → P2 | ⚠️ 谨慎 | 发现上游设计问题。允许，但 P2 的 retry 计数累积保留，且计入全局步数上限 |
| 跨多阶段回退 | ❌ 禁止自动 | 如 P6→P1，说明问题严重，停下 PAUSED 报告人工（正确路由，非 agent 失败）。检测方式：单步函数步骤 6 的 phase 编号差值检查（|next - current| >= 2 → PAUSED） |

（回退时携带诊断：新写目标阶段 dispatch-context 文件 + 引用 gate-diagnosis.md 路径，诊断内容不 inline 到 dispatch-context，见 ⑪⑫）

全局步数上限（护栏 2，默认 20）是最后兜底，但按阶段独立计数 + 回退规则让它不必单独扛所有失控场景。

### 回退机制（诊断→跳转→PAUSED→人工批准→修→重跑）

逐步是诊断过程，不是执行过程：

1. **诊断**：主 Agent 分析 gate 失败原因，确定问题源头在哪一阶段，落盘 `P{N}-gate-diagnosis.md`
2. **跳转**：直接改 .state.yaml phase 到目标阶段
3. **PAUSED**（diff≥2 时）：check-state-transition.py 拦截 → 主 Agent 在 PAUSED resolution 中写明诊断和目标 → 人工批准
4. **恢复到目标**：修完后从目标往下逐阶段重跑
5. **不在中间阶段停留**：诊断已确认问题在源头，中间阶段不需要重做

#### diff=1 的回退（无需 PAUSED）

| 回退 | diff | 流程 |
|------|------|------|
| P5→P4 | 1 | 直接退，带诊断信息（写入 P4-dispatch-context-{role}.md 的上游关联节引用 gate-diagnosis.md 路径） |
| P6→P5 | 1 | 直接退（但 P5 通常不是问题源头，更常见是 P6→P4） |

#### diff≥2 的回退（PAUSED + 诊断）

| 回退 | diff | 流程 |
|------|------|------|
| P4→P2 | 2 | PAUSED → 人工批准诊断 → 恢复 P2 → 修完 → P3→P4 重跑 |
| P6→P4 | 2 | PAUSED → 人工批准诊断 → 恢复 P4 → 修完 → P5→P6 重跑 |
| P6→P2 | 4 | PAUSED → 人工批准诊断 → 恢复 P2 → 修完 → P3→P4→P5→P6 重跑 |
| P7→P4 | 3 | PAUSED → 人工批准诊断 → 恢复 P4 → 修完 → P5→P6→P7 重跑 |

#### 对 check-state-transition.py 的影响

**不改脚本**。diff≥2 仍强制 PAUSED。但 PAUSED 的语义从"认输"变为"诊断通道"——主 Agent 在 PAUSED resolution 中写明诊断和目标，人工批准后恢复到目标阶段。这与 ② PAUSED 语义翻转协同。

---

## 一致性要求

- .state.yaml 的 phase 字段和 active-tasks.md 的"阶段"列必须一致
- 如果两者冲突，以 **.state.yaml 为准**，修正 active-tasks.md
- 主 Agent 每轮开始先做这个一致性检查，避免状态漂移

---

## 评审迭代机制

**⑩ do→review 迭代循环**：P1/P2/P4/P6/P7 的"do→review"是迭代循环（见 dispatch-protocol.md「do→review 迭代循环」节），不是单次通过/失败。review 迭代和 gate 重试共享 retry 预算。

### L1：阶段内再评审循环

```
阶段内循环：
  阶段执行者产出文件
       ↓
  主 Agent 跑 gate 命令（A1 原则）
       ↓
  通过？ ──是──→ 进入下一阶段
       ↓ 否
  派发评审角色读产出
       ↓
  评审角色产出 Pn-review.md (status: approved/rejected)
       ↓
  approved? ──是──→ 进入下一阶段
       ↓ 否
  retries[Pn].append({ failure_mode: quality, prompt_changed: <bool>, adjustment: <str> })
       ↓
  len(retries[Pn]) > MAX_RETRY?
       ↓ 是
  触发 L2 上溯（见下）
       ↓ 否
  执行者重写产出（带回评审反馈）
       ↓
  回到"主 Agent 跑 gate 命令"步骤
```

**该步骤现由 `check-state-transition.py` 机械校验（RM-AG0042 BDD-1）**：评审 rejected 后重新派发评审角色时，若产生了新编号的 `P{n}-dispatch-context-{role}-retryN.md`/`-revN.md` 文件（见 dispatch-protocol.md「评审打回后的意见回流」），但 `retries[Pn]` 未同步追加记录 → 高优 WARNING（不阻断，信号源置信度分层见 `rules/state-transitions.md`）。

### L2：单规则跨阶段上溯

**确定性单规则**：任何阶段失败 MAX_RETRY 轮 → 上溯到紧邻的上游阶段，上游标记为 `needs-review`。

| 失败阶段 | 上溯到 | 动作 |
|----------|--------|------|
| P1 | 用户 | PAUSED，报告用户需求可能不合理 |
| P2 | P1 | P1 标记 needs-review，复审需求基线与 BDD |
| P3 | P2 | P2 标记 needs-review，architect 重新设计 |
| P4 | P2 | P2 标记 needs-review，质疑设计方案 |
| P5 | P4 | P4 标记 needs-review，重新实现 |
| P6 | P4 | P4 标记 needs-review，行为不符 → 重新实现（验收失败回实现）|
| P7 | P2 | P2 标记 needs-review，质疑设计（僵尸需求/偏差）|
| P8 | P7 | P7 标记 needs-review，重新检查一致性后再发布 |

**不区分原因、不判断分支**：主 Agent 只需确定 `len(retries[Pn]) > MAX_RETRY` → 执行固定上溯动作，无需推理多变量决策。

### 用户介入边界

| 情况 | 动作 |
|------|------|
| P1 失败 3 轮 | PAUSED，报告用户需求可能不合理 |
| 涉及业务方向决策 | PAUSED，询问"这个功能要不要做" |
| 涉及外部资源/权限 | PAUSED，需 API key / 授权 |
| P1 检测到 CAPABILITY_GAP | PAUSED，等人补充能力路径或确认降级方案 |
| 任意阶段出现 [PROD_TOUCHED] | 立即 PAUSED，人工处置生产环境后才能继续 |
| 涉及批量删除或 schema 迁移（测试环境内）| [NEED_CONFIRM] → PAUSED，确认范围后才可执行 |
| 涉及安全/合规 | PAUSED，需要人判断 |
| retry 超限且上溯仍失败 | PAUSED，兜底机制 |

PAUSED 报告使用占位符模板（见 dispatch-protocol.md）。

---

*状态机是 /loop 自动编排的基础，配合 dispatch-protocol.md 和 loop-orchestration.md*
