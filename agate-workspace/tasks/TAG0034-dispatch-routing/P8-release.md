---
phase: P8
task_id: TAG0034
type: release
parent: P7-consistency.md
trace_id: TAG0034-P8-20260910
status: draft
created: '2026-09-10'
agent: implementer
bump_type: minor
debt_check: reviewed
---

# P8-release.md — TAG0034 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测）发布准备声明

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` /
> `git tag`**——这些由主 Agent 在 P8 gate 验证通过后亲自执行。本轮已实际编辑
> `agate/LIMITATIONS.md` / `agate/adr.md` / `docs/design-notes/design-dispatch-routing.md` /
> `CHANGELOG.md` / `README.md` / `README.zh-CN.md` / `agate/UPGRADING.md` §3 /
> `agate-workspace/roadmap/roadmap.md` / `agate-workspace/debt/tech-debt.md` /
> `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md` 十个发布面文件
> （P8 产出的一部分，非"留给主 Agent"）。
> 状态标记 `[PROD_NOT_TOUCHED]`。

## 1. 前置条件核对（P7-consistency.md）

- `P7-consistency.md`（TAG0034-P7）结论：**approved**，`blocker_count: 0` /
  `deviation_critical_count: 0` / `deviation_count: 1`（design-note §5/§7 残留旧路径串 +
  「探测」叙事，docs-only、非 CRITICAL——本批第 3 项已定点收尾）/ `design_gap_count: 4` /
  `design_gap_reviewed_count: 4`。
- packages 一致性：`P1 frontmatter` == `[agate-scripts, agate-rules, agate-docs, agate-tests]`
  （agateon 单一版本号仓库，四包为任务改动分域，整体 bump 一次）。
- 上游链路：P1..P7 全部 commit（P1 `f75e129` / P2 `b851b1e` / P3 `c218026` /
  P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` / P5 `2772891` / P6 `eb924be` /
  P6.5 `cb9dfb9` / P7 `8ad7834` = HEAD）。P4a alignment review 三批合并 aligned；
  A5.3 / A7.4 两条 doc-sync 用户 2026-09-09 `[HUMAN_CONFIRMED]`、落本 P8 收尾批。
- 结论：具备进入 P8 发布阶段的一致性前提，**前置条件已满足**。

## 2. bump_type 判断依据

**bump_type: minor（v0.70.0 → v0.71.0）**

依据：

1. **向后兼容的功能新增**：`agate dispatch route <phase> <role>` 子命令 +
   `agate_dispatch_route.py` helper 模块 + `dispatch_route` 事件 + 协议本体档位词表
   `agate/rules/dispatch-tiers.yaml` + 项目级 `agate-workspace/dispatch-routing.yaml` +
   静态校验器 `check-dispatch-routing.py` + tmux 观测层 helper——均为纯增量能力。
2. **无破坏性变更**：`agate-dispatch.py` 既有渲染路径（无 `route` 参数）逐字节不变
   （BDD-39 字节基线已验）；不新建 `dispatch-routing.yaml` + `dispatch-tiers.yaml` 出厂全
   `standard` 时派发行为与本版本前完全一致（BDD-40「不配置 = 逐字节现状」已验）。
3. **既有账本零影响**：`check-events.py` 第 8 条 `dispatch_route` 理由码枚举审计对无
   `dispatch_route` 行的既有 `gate-events.jsonl` 不进入分支，第 1-7 条审计不受影响。
4. **未改冻结面**：`phases.yaml` / `check-gate.py` / `check-state-transition.py` /
   `state-machine.md` / `agate/tests/` / `dispatch-protocol.md`「### 0. 派发路由」子节
   均未触碰。
5. 当前发布版 **v0.70.0**（CHANGELOG 顶部 `## [0.70.0] - 2026-09-09` + README badge
   `version-v0.70.0` 已核）→ 目标 **v0.71.0**。

## 3. 版本号变更逐文件确认表（比照 TAG0033 P8-release §3）

| 位置 | 文件 | 变更 | 本轮状态 |
|---|---|---|---|
| README badge（EN） | `README.md` L12 | `version-v0.70.0` → `version-v0.71.0` | 已改（`grep -c version-v0.71.0 README.md` → 1；旧值 `version-v0.70.0` 残留 → 0） |
| README badge（ZH） | `README.zh-CN.md` L12 | `version-v0.70.0` → `version-v0.71.0` | 已改（`grep -c version-v0.71.0 README.zh-CN.md` → 1；旧值残留 → 0） |
| CHANGELOG | `CHANGELOG.md` | 顶部 `## [0.70.0]` 之前插入 `## [0.71.0] - 2026-09-10` 段（顶部无 `[Unreleased]` 段，直接插入，格式对齐 `## [0.70.0]`） | 已改（`grep -c "^## \[0.71.0\]" CHANGELOG.md` → 1） |
| UPGRADING §3 | `agate/UPGRADING.md` | §3「已知破坏性变更（按版本）」`### v0.70.0` 之前新增 `### v0.71.0 — 派发路由（…TAG0034：RM-AG0060 epic）` 章节（对齐 `### v0.70.0` 格式；本版本无破坏性变更，写明「零迁移动作」；CHECK 13 CHANGELOG 最新版 ↔ UPGRADING §3 一致所必需——见 §8 说明） | 已改（`grep -c "### v0.71.0" agate/UPGRADING.md` → 1） |
| roadmap 回写 | `agate-workspace/roadmap/roadmap.md` L68 | RM-AG0060「状态」列 `scheduled` → `done`；「更新」列 `2026-09-08` → `2026-09-10`（RM-AG0043 P8 gate 硬校验；「关联任务」列已是 `TAG0034`；长描述 P4a M12 已回写为 `agate-workspace/dispatch-routing.yaml` + `agate/rules/dispatch-tiers.yaml` + try-and-fall + 两轴，核无残留旧串） | 已改（`grep -nE "RM-AG0060.*\| done \|" roadmap.md` 命中 L68） |
| tech-debt | `agate-workspace/debt/tech-debt.md` | DEBT0039 `status: open` → `closed`；`task_id: null` → `TAG0034`；新增 `closed_at: 2026-09-10` + 2 条 closure evidence（P6-acceptance BDD-48/49/50 + P7-consistency 0 ERROR） | 已改（`check-debt.py agate-workspace/debt/tech-debt.md` → exit 0） |
| P1 frontmatter | `agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md` | frontmatter 新增 `scope_resolved:` list（两项：DEBT0039 并入 + A5.3/A7.4 doc-sync；P1 §8 明确「由 P8 收尾回写」） | 已改（`check-frontmatter.py P1-requirements.md` → exit 0；`scope_resolved` 在 P1-requirements.md schema `migrated_keys` 白名单内） |
| ADR-013 | `agate/adr.md` | ADR-012 之后追加 `## ADR-013: 派发路由 / gate 生产者无关性（gate 不认谁生产的）`——逐字采用 alignment-review 末尾附录草案（状态 / 语境 / 决策 / 理由 / 后果五节，关联 ADR-002 / ADR-006 / RM-AG0060 / LIMITATIONS.md 局限 2） | 已改（`grep -c "^## ADR-013" agate/adr.md` → 1） |
| LIMITATIONS 局限 2 | `agate/LIMITATIONS.md` | 局限 2「**现状**：无解……→ ADR-006」之后追加「**派发路由缓解链（TAG0034 / RM-AG0060 已落地）**」段，形态对齐局限 3「P6.5 独立 Judge 缓解链」段——`cli: native` 弱缓解 / 跨 CLI 强缓解 / `dispatch_route` 留痕 + 两条完整性不变量 + 诚实边界句「仍非根治……与局限 3 同构……per-machine 机会式」 | 已改（`grep -c "派发路由缓解链" agate/LIMITATIONS.md` → 1；诚实边界句「仍非根治」在段内保留） |
| design-note §5/§7 | `docs/design-notes/design-dispatch-routing.md` | §5（L195/196/197）+ §7（L220/223）老串定点清理：`rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml`（+ 补一句档位词表在 `agate/rules/dispatch-tiers.yaml`）；「查表 → 探测 → …」→「查表 → 派首选 → 逐级回落 …（try-and-fall，无 probe，与 §2.2 一致）」；§7 事项 4「探测缓存 / native 探测方式」标注「2026-09-09 定案已作废」。未重写整节。 | 已改（`grep -n 'rules/dispatch-routing\.yaml' design-dispatch-routing.md` → 无命中，exit 1） |

> **git tag `v0.71.0` 由主 Agent 在 gate 验证通过后创建**。tag 创建前，
> `check-protocol-consistency.py` CHECK 7（README badge ↔ 最新 git tag）报
> `README version badge v0.71.0 != 最新 tag v0.70.0` ERROR——属"发布完成态"校验的设计使然
> （DEBT0013 时序注意），非本批引入的回归；主 Agent 在 `git tag v0.71.0` 之后复跑即
> **CHECK 7 归零、consistency `--strict-errors-only` exit 0**。releaser 本轮不为它回退 badge。

## 4. CHANGELOG `[0.71.0]` 节内容（本轮已写入 CHANGELOG.md 本体，此处副本供 gate / 评审对照）

```markdown
## [0.71.0] - 2026-09-10

### 新增（TAG0034：派发路由，配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）

- agate dispatch route <phase> <role> 子命令（扩 agate-dispatch.py；查表 → try-and-fall
  逐级回落 → 默认派发；agate_dispatch_route.py helper：resolve / load_config /
  classify_outcome / build_dispatch_command / try_and_fall）；既有渲染路径逐字节不变
- 协议本体档位词表 agate/rules/dispatch-tiers.yaml（bulk / standard / deep + 出厂默认全
  standard，改它走 SELF-GATE）
- 项目级 agate-workspace/dispatch-routing.yaml（tier_bindings: + routes:，全兜底，非协议
  本体、不触发 SELF-GATE，对齐 maintainability.yaml）+ 静态校验器
  agate/scripts/check-dispatch-routing.py
- dispatch_route 事件（gate-events.jsonl 哈希链，check-events.py 第 8 条理由码枚举审计，
  gate_fail 非法）
- dispatch-protocol.md「派发编排机制」新增「### 0. 派发路由」子节（查表→派首选→逐级回落
  + gate 生产者无关声明 + 两条完整性不变量 + cli: native 弱缓解 / 跨 CLI 强缓解 + 单
  Agent no-op + 评审打回续跑）
- tmux 观测层（build_subprocess_launch / tmux_cleanup_action，feature flag
  AGATE_DISPATCH_TMUX 默认关，目标环境待复跑）
- effort 轴按 claude --help 能力探测映射 --effort（BDD-10 [BASELINE_CHANGE]，不硬编码
  版本号）
- ADR-013「派发路由 / gate 生产者无关性」；LIMITATIONS.md 局限 2 补「派发路由缓解链」
- DEBT0039 闭合（architect.md「批次设计」节 + dispatch-protocol.md 明确「补协议文档正文
  = P4 / 跨文件一致性验证 = P7」）；SETUP.md 新增机器级 scaffold 小节；platform-notes.md
  补跨 CLI 子进程结构化输出字段小节
```

（CHANGELOG.md 本体的实际排版含完整子项缩进 + 反引号，本副本去格式仅供逐条对照，条目清单一致。）

## 5. roadmap 回写确认（RM-AG0060 → done）

- `agate-workspace/roadmap/roadmap.md` L68 RM-AG0060 行：
  - 「状态」列：`scheduled` → **`done`**（RM-AG0043 P8 gate 硬校验：按 `task_id` 反查
    「关联任务」列 = `TAG0034`，须回写 `done` 否则阻断）
  - 「更新」列：`2026-09-08` → **`2026-09-10`**（「创建」列 `2026-09-08` 保持不变）
  - 长描述：P4a M12 已回写落点措辞（`agate-workspace/dispatch-routing.yaml` +
    `agate/rules/dispatch-tiers.yaml` + try-and-fall + tier/effort 两轴），本轮核对无残留
    旧串 `rules/dispatch-routing.yaml` / 「按序探测」。
- 自查：`grep -nE "RM-AG0060.*\| done \|" agate-workspace/roadmap/roadmap.md` → 命中 L68。

## 6. debt_check（reviewed）——条目 id 清单

**debt_check: reviewed**。已读取 `agate-workspace/debt/tech-debt.md` 全簿，本任务相关条目：

| DEBT id | 标题（摘） | 本轮动作 | status |
|---|---|---|---|
| DEBT0039 | dispatch_plan 批次「执行阶段」标注易把「补协议文档正文」误标到 P7 | **本任务闭合**（用户批准 2026-09-09 并入 TAG0034）：`status: open` → `closed`；`task_id: null` → `TAG0034`；新增 `closed_at: 2026-09-10` + 2 条 closure evidence（`P6-acceptance.md` BDD-48/49/50 逐条 P6 已过 / `P7-consistency.md` consistency 0 ERROR）。三条 `closure_criteria`（architect.md 批次设计节边界 / dispatch-protocol.md author-vs-consistency 区分 / consistency 0 ERROR）由 P4a 落地 + BDD-48/49/50 承接，P6 逐条已过。 | `closed` |
| DEBT0037 | check-gate.py P4 完整度判据在多提交 / 回退后推进场景不完备——需手动 `_advance` | **本任务未闭合、非本任务范围**：本任务是该债的受害者（P0-brief `known_risks` 已预告），全程按 P0-brief 预告以手动 `_advance` + 补 `state_transition` 事件处理。留 `status: open` / `task_id: null` 不动。 | `open`（不动） |
| DEBT0038（存量） | check-judge-verdict.py 信息隔离黑/白名单误判 P6.5 dispatch-context | 与本任务无直接关联，不动。 | `open`（不动） |
| 其余存量债务 | — | 与本任务无关，未涉及。 | — |

- `timeout 60 python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **exit 0**。
- closed schema 交叉核（`agate-debt-check.py` 第 116-122 行）：DEBT0039 evidence 序列化文本
  同时含 `TAG0034` 与 `P6` 标记，`task_id` 非空——准入条件满足。

## 7. 临时资源清单（releaser → 主 Agent 交接）

核对本任务 P0-P8 全程启动的临时服务 / 进程 / 数据 / 开发安装：

- **启动的临时服务 / 进程**：无。无 debug server / 无临时 daemon / 无占用端口。
- **临时数据库**：无。
- **临时数据 / 目录**：无。纯脚本 + 文件改动 + mock 单元测试。
- **开发安装**：无。用系统 `python3`，未新装 editable install / 全局包 / `pip install`。
- **真机 CLI 冒烟**：P1/P4/P5/P6 的三平台（Claude Code 2.1.266 / codex-cli 0.153.4 /
  opencode 1.18.11 / tmux 3.4）真机验证为**只读、不驻留**——未起常驻进程、未写生产数据，
  产生的 CLI 自身会话记录（如 `~/.codex/sessions/`）是各 CLI 的正常产物、非 agate 生产环境
  残留，`~/.agate` 与 worktree git 树未被污染。主 Agent **无需清理**。
- **结论：本任务临时资源清单 = 无**。
- **状态标记**：`[PROD_NOT_TOUCHED]`。

## 8. 自检（非 gate）

- `bump_type: minor` / `debt_check: reviewed` frontmatter 字段存在：已确认。
- `grep -c "^## \[0.71.0\]" CHANGELOG.md` → **1**。
- `grep -c "version-v0.71.0" README.md` → 1；`README.zh-CN.md` → 1（合计 **2**）；
  旧 `version-v0.70.0` 残留 → **0**（两文件）。
- `grep -c "### v0.71.0" agate/UPGRADING.md` → **1**。
- `grep -nE "RM-AG0060.*\| done \|" agate-workspace/roadmap/roadmap.md` → 命中 L68。
- `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **exit 0**。
- `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`
  → **exit 0**。
- `grep -n 'rules/dispatch-routing\.yaml' docs/design-notes/design-dispatch-routing.md`
  → **无命中**（exit 1）。
- 未执行 `git add` / `git commit` / `git tag` / `bump-version`（留主 Agent）。
- 未改 `agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` /
  `state-machine.md` / `agate/tests/` / `agate/scripts/` 代码 / `dispatch-protocol.md`
  「### 0. 派发路由」子节。
- `[SCOPE+]`：无。
- `[PROD_NOT_TOUCHED]`。

### 8.1 `pytest -k tag0034` 与 consistency 自检结果 + CHECK 7 时序说明

- `timeout 120 python3 -m pytest agate/tests/ -k tag0034 -q` → **89 passed / 1 failed**
  （1537 deselected）。唯一 failed = `test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes`。
- `timeout 120 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
  → **exit 1**，**ERROR (1)**：`README version badge v0.71.0 != 最新 tag v0.70.0`（CHECK 7）。
  CHECK 1~6 / 8~15 全 exit 0；WARNING 总数 329（与 P7 存量基线一致，本批未新增 WARNING）。
- **`test_bdd_50` 的 failed 与 CHECK 7 的 ERROR 是同一根因**：`test_bdd_50` 断言
  `check-protocol-consistency.py --strict-errors-only` 返回 0，而该脚本此刻的唯一 ERROR
  就是 CHECK 7 的「badge 已 bump 到 v0.71.0、git tag v0.71.0 尚未创建」中间态——**设计使然、
  非本批引入的回归**（与 §3 末尾 CHECK 7 时序说明同一条）。主 Agent 在 gate 验证通过、
  执行 `git tag v0.71.0` 之后复跑：CHECK 7 归零 → consistency `--strict-errors-only` exit 0
  → `pytest -k tag0034` 回到 **90 passed / 0 failed**。
- 除 CHECK 7 外的存量 WARNING（329 条）非本任务范围，不阻断（`--strict-errors-only` 语义）。

## 9. SELF-GATE 面提醒（主 Agent commit 前）

本批改动触及 `agate/LIMITATIONS.md` + `agate/adr.md` + `agate/UPGRADING.md` +
`docs/design-notes/design-dispatch-routing.md` + `CHANGELOG.md` + `README.md` +
`README.zh-CN.md` + `agate-workspace/roadmap/roadmap.md` + `agate-workspace/debt/tech-debt.md`
——**触发 SELF-GATE**。主 Agent 在 commit 前须：

1. 派发 `protocol-alignment-review`（A1-A7 语义审查，`agent≠main`）；
2. commit message 带 `self-gate-review: <alignment-review 报告路径>` trailer；
3. 本 P8 batch 的 A5.3（LIMITATIONS.md 局限 2 缓解链段）+ A7.4（ADR-013）逐字对齐
   `docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md` 末尾附录草案，review 时
   可交叉核对；两处 `[HUMAN_CONFIRMED: 2026-09-09]` 由主 Agent 落地后更新为
   「已落地 commit <P8 hash>」。

## 10. 主 Agent 待办（P8 gate 通过后亲自执行，releaser 不做）

1. `check-gate.py P8 $TASK_DIR`（bump_type + debt_check 字段 + 暂存区 version 文件 +
   暂存区 CHANGELOG + roadmap RM-AG0060 → done）。
2. `bump-version` → `v0.71.0` + `git commit`（带 `self-gate-review:` trailer）+
   `git tag v0.71.0`（同一 commit）。
3. P5 验证：先 `check-p6-provenance.py --audit7-only`；`reuse_allowed` → 复用
   `P5-test-results/`；否则完整重跑 `gate_commands.P5`。**CHECK 7（badge ↔ tag）+
   `test_bdd_50` 须安排在 `git tag v0.71.0` 创建之后复跑**（DEBT0013 时序注意）——
   tag 前必然 CHECK 7 ERROR + `test_bdd_50` failed，tag 后归零。
4. `git log v0.70.0..HEAD --oneline` 对照 CHANGELOG 无遗漏。
5. READY 收尾检查（临时资源清单见 §7——无 debug server / 无临时 DB / 无临时数据 /
   无开发安装；三平台真机冒烟只读不驻留，无需清理）。

## 11. Lessons Learned

> 类别 / 教训 / 来源任务 / 日期 —— 供主 Agent 汇入 `docs/notes/lessons.md`。

- **流程 | P8 badge bump 与 consistency-exit-0 回归断言天然冲突，须提前在 P8-release.md
  标为「同 CHECK 7 时序」**：TAG0034 有一条 BDD 回归测试（`test_bdd_50`）直接断言
  `check-protocol-consistency.py --strict-errors-only` exit 0。P8 bump README badge 后、
  主 Agent `git tag` 前，CHECK 7 必然 ERROR，该测试必然 failed。这不是新回归，是 CHECK 7
  「校验发布完成态」设计的连带结果，与 DEBT0013 时序注意同源。P8 设计带此类断言时，dispatch-context
  应预告「pytest 会少 1 条、tag 后归零」，releaser 应在 release.md 显式绑定两者根因。
  来源 TAG0034 / 2026-09-10。
- **架构 | ADR + LIMITATIONS 缓解链段应在机制落地后、随 P8 收尾逐字落地，草案在 alignment
  review 附录冻结**：TAG0034 的 A5.3 / A7.4 两条 doc-sync 在 P4a alignment review 阶段就
  由用户 `[HUMAN_CONFIRMED]` 并把草案写进 review 报告末尾附录，P8 只做「逐字采用 / 按最终
  形态微调」的落地动作。好处：机制在 P4a-P4c 定型后措辞不再漂移，P8 releaser 无需重新推导
  边界句，诚实边界句（「仍非根治……与局限 3 同构」）被冻结在草案里不会被稀释。
  来源 TAG0034 / 2026-09-10。
- **流程 | 「9 项文件改动」清单遗漏 UPGRADING §3——CHANGELOG 与 UPGRADING §3 被 CHECK 13
  机械耦合**：dispatch-context 列了 9 项，但插入 CHANGELOG `## [0.71.0]` 后 CHECK 13 立即
  要求 `agate/UPGRADING.md` §3 有对应 `### v0.71.0` 章节（无破坏性变更也须写「零迁移动作」
  章节）。releaser 按「consistency 除 CHECK 7 外 0 ERROR」的硬约束补了该章节（比照 TAG0033
  P8 先例），未扩到清单外其它文件。P8 派发清单应把「UPGRADING §3 版本章节」与 CHANGELOG
  绑为一项。来源 TAG0034 / 2026-09-10。

---

> 注：本文件不含 PASS/FAIL 预判——所有测试 / 校验结果均为 releaser 本轮自检的客观运行输出，
> gate 判定由主 Agent 亲自执行。
