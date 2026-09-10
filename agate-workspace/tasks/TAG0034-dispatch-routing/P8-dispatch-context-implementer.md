---
phase: P8
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0034
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）

### 目标

P8 发布准备（implementer P8 模式，releaser）：落地 SCOPE+ 的两条 doc-sync（A5.3 / A7.4）+ P7 的 1 条 DEVIATION 收尾 + roadmap / tech-debt 回写 + CHANGELOG + README badge，产出 `P8-release.md`。**不执行** `bump-version` 工具 / `git commit` / `git tag`（主 Agent 在 gate 验证通过后亲自做）。

### 要做的文件改动（逐项）

**1. `agate/LIMITATIONS.md` 局限 2 补「派发路由缓解链」段（A5.3，用户 2026-09-09 批准 + `[HUMAN_CONFIRMED]`）**

在局限 2 现有「**现状**：无解……→ ADR-006」（约 line 19）**之后**追加一段，形态对齐局限 3 的「P6.5 独立 Judge 缓解链（TAG0020 已落地）」段（约 line 35）。草案（可按 P4a–P4c 最终形态微调，但**务必保留诚实边界句**）：

> **派发路由缓解链（TAG0034 / RM-AG0060 已落地）**：局限 2 的根因是「P3/P4/P6.5 等角色虽是不同 subagent、但通常同一底层模型 → 系统性盲区共享」。派发路由机制在**机制层**给「角色隔离」补上 model / 厂商维度：项目级 `agate-workspace/dispatch-routing.yaml` 按 `(phase, role)` 声明有序跨 CLI 候选链，主 Agent 到阶段派角色时机械查表 → try-and-fall（无 probe，只在 `launch_fail` / `infra_error` / `no_parseable_output` 三类基础设施信号逐级回落）→ 全落空回落默认派发（等价未启用）。两种缓解强度：`cli: native`（同厂商换 model，不脱离原生派发工具）是**弱缓解** —— 同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性，且自动化天花板是「主 Agent 读文件机械横传 model」；`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解** —— 真正的异源独立视角、可端到端自动化。`dispatch_route` 事件与 `gate_run` 等同构、无差别留痕（哈希链账本 `check-events.py` 审计），两条完整性不变量机械强制（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」，理由码枚举无 `gate_fail` 值）防「换模型试到出 green」的完整性洞。**仍非根治** —— 主 Agent 自身的选型判断、以及「机械横传 model」这一步本身，仍缺乏外部约束，与局限 3「主 Agent 判断力是单点故障」同构；且是否真配跨 CLI 候选、配哪些，由使用者按本机现状决定、后果自负（per-machine 机会式，不追求跨机可复现）。

**2. `agate/adr.md` 新增 ADR-013「派发路由 / gate 生产者无关性」（A7.4，用户批准 + `[HUMAN_CONFIRMED]`）**

在 ADR-012（约 line 381）之后追加。草案（`docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md` 附录里有完整草案，**逐字采用或按最终形态微调**）：标题 `## ADR-013: 派发路由 / gate 生产者无关性（gate 不认谁生产的）`；节：**状态**（已接受，2026-09-09，TAG0034 / RM-AG0060）/ **语境**（跨 CLI/model 派发的产出可能由多种来源生产，机制成立前提 = gate 不因「谁生产」而变）/ **决策**（gate 只认产出文件 + exit code，不认谁生产的；一切 gate 脚本对跨 CLI/model 产出零特殊处理；**未来不得为跨 CLI 派发定制 gate**；`dispatch_route` 留痕与 gate 判定解耦、回落理由码无 `gate_fail`、`check-events.py` 第 8 条机械拒绝、gate FAIL → 同候选 retry 绝不换候选）/ **理由**（与 ADR-002 可判定性一致 / 与 ADR-006 同源盲区互补 / 防完整性洞 / 散文承载不够稳需沉淀 ADR）/ **后果**（跨 CLI 产出质量差走同候选 retry 不换候选；新增 gate 脚本试图区分来源即违反本 ADR；关联 RM-AG0060 / ADR-002 / ADR-006 / LIMITATIONS.md 局限 2）。

**3. `docs/design-notes/design-dispatch-routing.md` §5 / §7 老串清理（P7 `[DEVIATION]`，非 CRITICAL）**

P7-consistency.md 标出：§5（约 line 195/197）+ §7（约 line 220/223）仍留旧串 `rules/dispatch-routing.yaml` + 「按序探测」叙事，与已按 2026-09-09 定案重写的 §2.1/§2.2 冲突（BDD-46 范围限「头部+§2.1+§2.2」，故这两节 P4a M12 没动）。本批**定点修正**：`rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml`（+ 需要时补一句「档位词表在 `agate/rules/dispatch-tiers.yaml`」）；「按序探测」类措辞 → try-and-fall（与 §2.2 一致）。只改这两节的这几处串，不重写整节。改完 `grep -n 'rules/dispatch-routing.yaml' docs/design-notes/design-dispatch-routing.md` 应无命中（或仅剩明确的历史引述且已标注）。

**4. `CHANGELOG.md` 新增版本段**

在 `## [0.70.0] - 2026-09-09` 之前插入 `## [0.71.0] - 2026-09-10`（bump_type: **minor** —— 向后兼容的功能新增，「不配置 = 逐字节现状」）。段内按 Keep a Changelog 格式，`### 新增（TAG0034：派发路由，配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）`：
- `agate dispatch route <phase> <role>` 子命令（扩 `agate-dispatch.py`；查表 → try-and-fall 逐级回落 → 默认派发；`agate_dispatch_route.py` helper：`resolve` / `load_config` / `classify_outcome` / `build_dispatch_command` / `try_and_fall`）
- 协议本体档位词表 `agate/rules/dispatch-tiers.yaml`（`bulk` / `standard` / `deep` + 出厂默认全 `standard`，改它走 SELF-GATE）
- 项目级 `agate-workspace/dispatch-routing.yaml`（`tier_bindings:` + `routes:`，全兜底，非协议本体、不触发 SELF-GATE，对齐 `maintainability.yaml`）+ 静态校验器 `agate/scripts/check-dispatch-routing.py`
- `dispatch_route` 事件（`gate-events.jsonl` 哈希链，`check-events.py` 第 8 条理由码枚举审计，`gate_fail` 非法）
- `dispatch-protocol.md`「派发编排机制」新增「### 0. 派发路由」子节（查表→派首选→逐级回落 + gate 生产者无关声明 + 两条完整性不变量 + `cli: native` 弱缓解 / 跨 CLI 强缓解 + 单 Agent no-op + 评审打回续跑）
- tmux 观测层（`build_subprocess_launch` / `tmux_cleanup_action`，feature flag `AGATE_DISPATCH_TMUX` 默认关，目标环境待复跑）
- effort 轴按 `claude --help` 能力探测映射 `--effort`（BDD-10 `[BASELINE_CHANGE]`，不硬编码版本号）
- ADR-013「派发路由 / gate 生产者无关性」；LIMITATIONS.md 局限 2 补「派发路由缓解链」
- DEBT0039 闭合（`architect.md`「批次设计」节 + `dispatch-protocol.md` 明确「补协议文档正文 = P4 / 跨文件一致性验证 = P7」）；`SETUP.md` 新增机器级 scaffold 小节；`platform-notes.md` 补跨 CLI 子进程结构化输出字段小节

**5. `README.md` + `README.zh-CN.md` version badge**

比照 TAG0033 P8：两文件约 L12 的 `version-v0.70.0` → `version-v0.71.0`（`grep -c version-v0.71.0` 应各 = 1，旧值残留各 = 0）。

**6. `agate-workspace/roadmap/roadmap.md` RM-AG0060 状态回写（P8 gate 硬校验 RM-AG0043）**

RM-AG0060 行「状态」列 `scheduled` → `done`。（长描述里的落点措辞 P4a M12 已回写为 `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml` + try-and-fall + 两轴，核一下无残留旧串；有则一并清。）「关联任务」列已是 `TAG0034`。

**7. `agate-workspace/debt/tech-debt.md` DEBT0039 闭合**

DEBT0039 条目：`status: open` → `status: closed`；`task_id:`（当前空 / `null`）→ `task_id: TAG0034`；按模板补 `closed_by` / `closed_date` 类字段（若模板有）。DEBT0039 的 `closure_criteria` 三条已由 BDD-48/49/50 承接、P6 逐条 PASS —— 在条目里注明「TAG0034 P4a 落地 architect.md 批次设计节 + dispatch-protocol.md 派发编排机制节的 P4/P7 边界措辞，consistency 0 ERROR，P6 BDD-48/49/50 PASS」。

**8. `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md` frontmatter `scope_resolved` 回写（P1 §8 明确「由 P8 收尾回写」）**

frontmatter 现有 `baseline_changes:` + `suggest_resolved:` list。新增 `scope_resolved:` list（若已有则追加），两项：
- `"DEBT0039 并入 TAG0034（用户批准 2026-09-09）：architect.md 批次设计节 + dispatch-protocol.md 派发编排机制节 P4/P7 边界措辞已落地，BDD-48/49/50 P6 PASS，DEBT0039 置 closed"`
- `"A5.3/A7.4 doc-sync（P4a alignment review，用户批准 2026-09-09）：LIMITATIONS.md 局限 2 派发路由缓解链段 + adr.md ADR-013 已在 P8 落地"`
`agate-md-field-set` 若不支持 list 追加则手工加为合法 YAML list，改完跑 `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（exit 0）。

**9. `P8-release.md`（你的主产出）**

frontmatter + 正文含：
- `bump_type: minor`（理由：`agate dispatch route` 子命令 + `dispatch_route` 事件 + `dispatch-tiers.yaml` + tmux helpers = 向后兼容功能新增；无破坏性变更，「不配置 = 逐字节现状」= BDD-40 已验）
- `debt_check: reviewed`（正文附：DEBT0039 本任务闭合；DEBT0037 未闭合但非本任务范围——本任务是其受害者、已按 P0-brief 预告手动 `_advance` 处理；tech-debt.md 其它条目本任务未涉及）
- 版本号变更确认表（CHANGELOG `## [0.71.0]` / README.md badge / README.zh-CN.md badge —— 各 `grep -c` 确认新值命中、旧值残留 0）
- CHANGELOG `[Unreleased]` → `[0.71.0]` 更新确认
- roadmap RM-AG0060 → done 确认（`grep -nE 'RM-AG0060.*done' agate-workspace/roadmap/roadmap.md`）
- DEBT0039 → closed 确认
- **临时资源清单**：本任务全程无临时服务 / 无临时数据库 / 无端口占用 / 无开发安装（纯脚本 + 文件 + mock 测试；真机 CLI 冒烟只读不驻留）——写「无」
- SELF-GATE 面提醒：本批改 `agate/LIMITATIONS.md` + `agate/adr.md` + `docs/design-notes/` + `CHANGELOG.md` + `README*.md` + roadmap + tech-debt → 触发 SELF-GATE；主 Agent commit 前须派 `protocol-alignment-review`（A1-A7），commit message 带 `self-gate-review:` trailer

### 约束

- **不 commit / 不 tag / 不 bump-version 工具**：你只改文件 + 写 `P8-release.md`。主 Agent 在 gate 验证通过后亲自 `git commit` + `git tag v0.71.0`。
- **只做上述 9 项**：不扩到其它 DEBT、不改脚本 / gate 逻辑、不改 P4 已落地的 `agate/scripts/` 代码 / 测试 / `dispatch-protocol.md`「### 0. 派发路由」子节。design-note 只改 §5/§7 的老串（不重写）。
- **回归硬约束不破**：不碰 `agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `agate/dispatch-protocol.md` 已定稿的「### 0. 派发路由」子节 / `agate/tests/`。改完跑 `timeout 120 python3 -m pytest agate/tests/ -k tag0034 -q`（仍 90 passed / 0 failed —— doc 改动不应动测试结果，除非 doc-assertion 测试对 §5/§7 有断言，核一下没有）。
- **consistency 保持 0 ERROR**：改 design-note / adr.md / LIMITATIONS.md 后跑 `timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（exit 0）。**注意 CHECK 7**（README badge ↔ 最新 git tag）：bump README badge 后、`git tag v0.71.0` 前，CHECK 7 必然报 `badge v0.71.0 != tag v0.70.0` ERROR——这是**设计使然**（校验发布完成态），不是你引入的回归；在 `P8-release.md` 注明「CHECK 7 待主 Agent tag 后复跑归零」，不要为它回退 badge。其余 CHECK 1~15 应 0 ERROR。
- **PROD 隔离**：dogfooding，"生产" = 主 checkout `/home/kity/oclab/agateon` + `~/.agate`，禁改。仅 worktree 内写。`[PROD_NOT_TOUCHED]` / `[PROD_TOUCHED]` 二值。
- **命令超时兜底**：所有 bash 前 `timeout <n>s`。
- **格式**：`P8-release.md` 避免行首 `- PASS` / `- FAIL`（provenance 预判检测）。

> 子派发能力：不启用（P8 单发）。

### 上游关联

- P1..P7 全部 commit：P1 `f75e129` / P2 `b851b1e` / P3 `c218026` / P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` / P5 `2772891` / P6 `eb924be` / P6.5 `cb9dfb9` / P7 `8ad7834`（HEAD）。`.state.yaml` phase=P8。
- P7 consistency-reviewer approved：BLOCKER=0 / DESIGN_GAP 4/4 配对 / `deviation_critical=0` / `deviation_count: 1`（design-note §5/§7 老串 → 本批第 3 项收尾）。
- P4a alignment review 附录有 A5.3（LIMITATIONS.md 段）+ A7.4（ADR-013）完整草案（`docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md` 末尾「## 附录：A5.3 / A7.4 的 P8 交付草案」）。两条 `[HUMAN_CONFIRMED: 2026-09-09 …（P8 落地）]` 已在该报告 A5/A7 节填好——你落地后主 Agent 会把「（P8 落地）」更新为「已落地 commit <P8 hash>」。
- CHANGELOG 当前顶部 `## [0.70.0] - 2026-09-09`（TAG0033，v0.70.0）。README badge 现 `version-v0.70.0`。
- RM-AG0060 行：`scheduled`，关联 `TAG0034`（`agate-workspace/roadmap/roadmap.md` line 68）。
- DEBT0039（`agate-workspace/debt/tech-debt.md`）：`status: open`，`task_id` 空/null，`closure_criteria` 三条 = BDD-48/49/50（P6 已 PASS）。

### 输入文件

- `agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md`（`packages` 声明 + §9 design-note 修订要点）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（§1 两条 SCOPE+ + §8/§9 P8 收尾清单 + frontmatter `scope_resolved` 落点）
- `agate-workspace/tasks/TAG0034-dispatch-routing/P7-consistency.md`（`deviation_count: 1` 的 design-note §5/§7 DEVIATION 详情）
- `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`（**末尾附录 A5.3 / A7.4 完整草案**）
- `agate/LIMITATIONS.md`（局限 2 现状段 + 局限 3 的「P6.5 独立 Judge 缓解链」段作形态参照）
- `agate/adr.md`（ADR-012 后追加 ADR-013；ADR-002 / ADR-005 / ADR-006 / ADR-010 现有措辞作关联参照）
- `docs/design-notes/design-dispatch-routing.md`（§2.1/§2.2 已重写 + §5/§7 待清老串）
- `CHANGELOG.md`（`## [0.70.0]` 段作格式参照）
- `README.md` + `README.zh-CN.md`（L12 badge）
- `agate-workspace/roadmap/roadmap.md`（RM-AG0060 行）
- `agate-workspace/debt/tech-debt.md`（DEBT0039 条目 + 模板字段）
- `agate/assets/templates/tech-debt-template.md`（DEBT0039 闭合字段规范）
- `agate/assets/execution-roles/implementer.md`（你的角色定义「P8 发布准备」+「P8 多包发布」+「P8 临时资源清单」）
- `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P8-release.md`（同类 P8-release.md 格式 + README badge 处理 + CHECK 7 时序说明先例）
- `AGENTS.md`（发布流程、SELF-GATE、`--strict-errors-only` 定义）

### 产出文件字段

用 `FILE=agate-workspace/tasks/TAG0034-dispatch-routing/P8-release.md agate-md-field-set --list` 查看应填字段；逐个写入（`bump_type: minor` / `debt_check: reviewed` / `agent: implementer` / `trace_id`）；不要手写 frontmatter；失败照错误提示修正，仍失败报告主 Agent。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P8

路径：phase-cards/P8-release.md
---
# P8 — 发布

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P8 + internal_only: true + internal_only_reason 已声明 → 跳过，标记 READY
> ⑨ P8 subagent 化

## 如果是首次进入本阶段

1. 主 Agent 派发 releaser subagent（implementer P8 模式）执行发布准备
   1.1 写 P8-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. releaser subagent 产出 P8-release.md，**不执行 git commit/tag**
3. 主 Agent 执行 gate 验证 → 通过后执行 bump-version + CHANGELOG 更新 → 同一 commit + tag
4. 主 Agent 执行 READY 收尾检查（参考 P8-release.md 临时资源清单）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + P8-release.md，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 READY，不要提前写 DONE——phase = 本 commit 的产出阶段；终态 DONE 收尾随任务终态 commit 一起

## 如果是重试

→ 读 agate/rules/state-transitions.md 确认 retry 上限（P8 MAX=2）

## 执行方式

releaser subagent（implementer P8 模式）执行以下发布准备步骤：

1. 读取 P2-design.md packages 声明，确定需 bump 的包
2. 为每个 package 执行发布检查命令
3. 更新 CHANGELOG [Unreleased] → 版本号
4. 确认债务清单：读 `{AGATE_WORKSPACE}/debt/tech-debt.md`（若存在），在 P8-release.md 写入 `debt_check:` 字段（TAG0001 Phase 3）
5. 产出 P8-release.md（含 bump_type、版本号变更确认、CHANGELOG 更新确认、debt_check 字段、临时资源清单）

> **注意**：releaser subagent 不执行 bump-version / git commit / git tag，这些由主 Agent 在 gate 验证通过后亲自执行。

## 多包发布拆批（模式 2/3，条件触发）

> 仅当 P2 packages > 1 时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry 见 dispatch-protocol「派发编排机制」并行规则。

多包发布时 P8 可拆批并行（模式 2 静态拆批 / 模式 3 并行）：

1. 每个 package 派一个 releaser subagent（implementer P8 模式），各写 `P8-release-{pkg}.md`
2. 各 releaser 只处理自己包的发布准备（版本 bump 建议 + CHANGELOG 更新 + 发布检查命令）
3. 所有 releaser 返回后，主 Agent 派合并 subagent 整合唯一 P8-release.md
4. 合并 subagent 需交叉核对：各包版本号不冲突、bump_type 汇总一致、CHANGELOG 变更合并无遗漏
5. 主 Agent 在 gate 验证通过后统一执行 bump-version / git commit / git tag

**合并机制**：单包时 releaser 直接产出 P8-release.md（不走合并）；多包时各 releaser 产 P8-release-{pkg}.md，合并 subagent 整合唯一 P8-release.md 供 gate 检查。

## releaser→主 Agent 交接

P8-release.md 中的**临时资源清单**是 releaser→主 Agent 的交接文件：
- releaser subagent 负责写入临时资源清单（本任务启动的临时服务/进程/数据/开发安装）
- 主 Agent 使用该清单执行 READY 收尾检查中的清理工作
- P8-release.md 由 releaser subagent 产出，主 Agent 不直接编写

## 前置条件

- [ ] P7-consistency.md 通过（无 BLOCKER / DESIGN_GAP 已配对）
- [ ] P2-design.md packages 声明（决定哪些包需要 bump）

## 产出规格

P8-release.md 必须包含：
- `bump_type: major / minor / patch`
- `debt_check: none / reviewed`——债务清单确认留痕（TAG0001 Phase 3）：`none` = 本次无关注项（合法选项，不视为失败）；`reviewed` = 已核对，建议正文附条目 id 清单。只查留痕存在，不查内容达标、不阻断发布
- 版本号变更确认（version 文件已修改）
- CHANGELOG [Unreleased] → 新版本号
- 临时资源清单：本任务启动的临时服务/进程/数据/开发安装

## gate 规则

```bash
check-gate.py P8 $TASK_DIR
```

- bump_type 字段存在
- `debt_check` 字段存在（缺失 → exit 1；内容任意，含 `none` / 未关闭债务 → 不阻断，BDD-17）
- 暂存区有 version 文件变更
- 暂存区 CHANGELOG 有变更
- 若任务在 `agate-workspace/roadmap/roadmap.md` 有关联 RM 条目（按 `task_id` 反查「关联任务」列），须先回写「状态」列为 `done`，否则阻断（RM-AG0043）

主 Agent **必须亲自执行**以下验证（不可跳过、不可委托 subagent）：
- 从 P2 packages 逐包读取发布检查命令并执行 → 全部 exit 0
- **P5 验证（TAG0016 BDD-14 精简为条件化表述，底线不变——至少一次客观验证动作不可省）**：
  跑 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`，读 stdout 的
  `AUDIT7_RESULT: <reuse_allowed|reuse_blocked|no_reuse_claim_possible>` 行判定：
  - `AUDIT7_RESULT: reuse_allowed`（exit 0）→ 复用同一份 `P5-test-results/`（不重新执行命令）
  - `AUDIT7_RESULT: reuse_blocked`（exit 1）或 `AUDIT7_RESULT: no_reuse_claim_possible`
    （exit 0 但结果非 reuse_allowed）→ 完整重跑 `gate_commands.P5`（exit 0 + failed==0）
   - **⚠️ 时序注意（DEBT0013）**：若 `gate_commands.P5` 的链路包含
     `check-protocol-consistency.py` 的 CHECK 7（README version badge 与最新 git tag 一致性），
     P5 重跑应安排在 **commit + 创建 git tag 之后** 进行，而非 bump 版本文件后立即重跑——
     bump 已完成、tag 尚未创建的中间状态下，CHECK 7 必然报 `badge vX.Y.A != tag vX.Y.B` ERROR，
     这是设计使然（校验的是"发布完成态"），不是回归。先 tag 后重跑即 0 ERROR。
- `git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 无遗漏
- 从 P2 packages 验证 version 文件路径

## READY 收尾检查（P8 gate 通过后）— 主 Agent 亲自执行（不派发 subagent）

参考 P8-release.md 临时资源清单执行清理。以上检查项无 gate 脚本自动验证（已知缺口），**必须逐项实际执行检查命令**（如 `ps aux | grep debug` 确认服务已停止、`git status` 确认工作区干净），不得仅凭记忆打勾。

**状态与版本**：
- [ ] .state.yaml phase == READY
- [ ] {AGATE_WORKSPACE}/tasks/active-tasks.md 任务行状态已更新
- [ ] git 工作区干净
- [ ] git tag 已创建
- [ ] 若本任务触发复盘（异常模式 / 发现机制缺口 / 高价值任务），复盘产出
  `tasks/{Txxx}/retrospective.md` 基于 `agate/assets/templates/retrospective-template.md`
  模板撰写

**测试环境已清理**：
- [ ] 调试服务/进程已停止
- [ ] 临时数据已删除
- [ ] 测试占用的端口已释放

**开发环境已还原**：
- [ ] 开发安装已卸载
- [ ] 系统环境无污染
- [ ] 项目依赖恢复到发布版本

**协议一致性（改造协议自身的任务必做，TAG0001-0003 批次 D4 教训）**：
- [ ] **在干净 checkout 上跑一次 `check-protocol-consistency.py`**（`git clone` 到临时目录或 CI 兜底确认），0 ERROR
  - 原因：本地 worktree 的 `.worktrees` 路径过滤会掩盖任务产出文件的扫描问题，本地 0 ERROR ≠ CI 0 ERROR
  - 若无法干净 checkout，**至少确认 CI 的 consistency job 对本次 PR 通过**
- [ ] **确认任务产出目录（`docs/tasks/` 或 `{AGATE_WORKSPACE}/tasks/`）不被一致性检查器误扫**（若为 dogfooding 任务，任务产出应已在 `NARRATIVE_DIRS` 白名单）

**生产环境无残留**：
- [ ] 无 PROD_TOUCHED 标记（触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`）
- [ ] 生产数据/API 未被测试写入

## 推进条件（全部满足才写 phase: READY）

- [ ] bump-version 完成 + P5 验证全绿（重跑或复用 `P5-test-results/`，见上方「gate 规则」条件化表述）
- [ ] CHANGELOG 已更新
- [ ] git tag 已创建
- [ ] READY 收尾检查全部通过

## 常见错误

1. **不重跑 P5 gate**：bump-version 后直接 tag，不确认测试仍全绿
2. **CHANGELOG [Unreleased] 留在模板状态**：版本 bump 完但 CHANGELOG 没更新
3. **忘记清理测试环境**：debug server 还在跑、临时数据没删 → READY 不干净
4. **临时资源清单遗漏**：P4/P5 阶段启动的服务/安装的包没记录 → 清理时遗漏
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- READY → DONE：任务完成，代码可合并/发布
- 本任务是 agate 链条的终点——P8 完成后任务状态转为 DONE

> 完成 → 任务 DONE
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）；`.state.yaml` phase=P8 / status=active / judge.enabled=true / p5_pass_commit=92edcfc；HEAD = `8ad7834`（P7）
- CHANGELOG 顶部 `## [0.70.0] - 2026-09-09`（TAG0033）→ 本批插 `## [0.71.0] - 2026-09-10`
- README badge：`grep -n 'version-v0.70.0' README.md README.zh-CN.md` 定位（TAG0033 P8 记为约 L12）
- RM-AG0060：`agate-workspace/roadmap/roadmap.md` line 68，状态列 `scheduled` → `done`，关联任务已 `TAG0034`
- DEBT0039：`agate-workspace/debt/tech-debt.md`，`status: open`，`task_id` 空
- 主 Agent 已核：`git diff f75e129..HEAD -- agate/LIMITATIONS.md agate/adr.md` 无输出（本批首次动这两文件）
- `pytest -k tag0034` = 90 passed / 0 failed（P4c 后基线，doc 改动不应改变）；`check-protocol-consistency.py --strict-errors-only` exit 0（0 ERROR / 329 存量 WARNING）
- 版本 bump 工具 / commit / tag：**主 Agent 做**，不是你
- SELF-GATE：本批触发（`agate/*.md` + `CHANGELOG.md` + `README*.md`）——主 Agent commit 前派 `protocol-alignment-review`
- 任务目录名：`TAG0034-dispatch-routing`（完整目录名）
</objective_info>

> 注：本文件禁止包含 PASS/FAIL 预判 —— 否则被 `check-p6-provenance.py` 审计失败。
