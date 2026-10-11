# 留痕（retry 2，final incremental）— protocol-alignment-review TAG0051 P4

## 输入（读）
- ~/.agate/v0.81.0/agate/assets/review-roles/protocol-alignment-review.md（角色定义）
- P4-dispatch-context-protocol-alignment-review-retry2.md（本轮指引，最高优先）
- P4-dispatch-context-...-retry1.md / -review.md（首轮 A1-A8+A4b 方法、只读纪律）
- 产出（上轮）：docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md（status needs-revision）
- P4-progress-implementer-R-E.md / R-F.md；P4-review-code.md

## git 基线
- HEAD=d4e32f4；branch task/TAG0051-release-decoupling；改动未提交。git status --porcelain 行数=79（跑前/跑后一致，74? 实测 79）
- gate-events.jsonl mtime=2026-10-11 11:12:35（wrapper 跑前，未被写）

## 逐条核闭合（不采信陈述）
- 1r check-gate.py:25 → 实读=「P8: P8-release.md bump_type/debt_check + 结构化 delivery（method 枚举校验） + roadmap RM 反查」⇒ 闭合
- 1s implementer.md:45/49/90-101 → :45=「bump_type 意图、CHANGELOG [Unreleased]…」；:49=bump_type 意图+CHANGELOG+交付检查；节标题=「P8 多包交付收尾」；:101 否定式。⇒ 同文件无矛盾，闭合
- 2r P5-verification.md:147=「P8 交付收尾后重跑 P5 gate」；phase-cards/README.md:18=「交付收尾：bump_type 意图 / CHANGELOG [Unreleased] / 收尾清理」；task-files.md:38=bump_type 意图+CHANGELOG；active-tasks-template.md:54=bump_type 意图+CHANGELOG。⇒ 四处闭合
- A3b scripts/README.md:149 索引行含 gate [--task][--sha][--repo]（发布门 TAG0051）；tests/README.md:97 登记 agate-release.py gate→unit/test_release_gate.py+test_agate_release.py。⇒ 闭合
- R-F ①: check-gate.py gate_p8 函数头注释已改（「本函数只做脚本化可判部分…」）；实读确认
- R-F ②③: dispatch-prompt.md:277 「## `bump_type` 意图判定（不执行 bump；对外发布由独立流程负责）」 === dispatch-protocol.md:487 逐字一致
- R-F ④: wrapper 建 corpus = git clone --local --no-hardlinks；实跑 rc=0 / legacy 39 个，差异 2 条，未匹配 0 条 / 7s / 101M

## 语义族 grep（与指引逐字同）
- 命中 35（38→35）；逐条归类：①否定式（dispatch-protocol:881/WORKFLOW:327/implementer:101/P8-release:13,70/state-machine:167,168,330,406/AGENTS:188）②历史·迁移·独立发布（adr/UPGRADING/CHANGELOG 面/architect:186/git-integration:190/AGENTS:194,195,207,209/check-protocol-consistency:481,483,537/agate-release:123/check-retrospective:205/check-changelog:52/P8-release:111）③改动自身引用（check-gate:2328）。⇒ 三类，无残留④

## 机械复跑
- check-structure-consistency.py rc=0（S1..S6+S0 全 OK）
- check-protocol-consistency.py 0 ERROR / **433 WARNING**（指引称 432——差 1，全为 frozen，非 ERROR；如实记录）rc=0
- shellcheck r6-differential-prepare.sh rc=0
- 全量 pytest（env -u AGATE_ROOT, --reruns 1 -n auto）= 2 failed / 2957 passed / 2 skipped；两红=test_bdd_43（环境）+test_bdd_22（设计性必红）
- count-tests = 2961
- obligations: M 56/121 = 0.4628（未降）rc=0
- wrapper 负例：空/'/'/相对/src 内/祖先/allow-prefix 外 全 rc=2，未删除；真仓 status 仍 79

## 残余（非阻断，逐条列）
- R1 agate/tests/unit/test_tag0051_r6_harness.py:6 注释仍述 cp -a（已知项①）
- R2 P2-design.md:235/283/326/337 述 cp -a（已知项②，设计记录）
- R3 docs/design-notes/r6-differential-prepare.sh:24 残余「⑤ 会 clean -fdx」（与同文件 :18/:190/:192 自相矛盾；R-F 新增的不自洽）
- R4 consistency-reviewer.md:53 / P7-consistency.md:33 / task-files.md:477「P2 packages 与 P8 release bump 范围一致」（retry1 minor，未收敛）
- R5 dispatch-protocol.md:948「把'需要 bump 哪些包'明确写进 prompt」（retry1 minor，未收敛；R-F 只改了 :487）
- R6 state-machine.md:284 / dispatch-protocol.md:1335 READY 小结模板 {version}（主 Agent 明示裁决保留）
  ⇒ 均非行为/判据/acceptance；grep 盲区：'release bump'/'bump 范围'/'bump 哪些包' 不匹配语义族模式

## 裁决
- 两条已知未改项 = 内部实现细节/陈旧描述（非协议语义 MISALIGNED），可留待 P7（本任务 phases 含 P7）；不阻断 P4
- 0 协议语义 MISALIGNED ⇒ status=approved
