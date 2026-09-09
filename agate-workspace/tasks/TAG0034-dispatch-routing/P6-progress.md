# P6-progress — TAG0034 验收进度

## 启动
- 角色定义 verifier.md「模式二 P6 验收」已读
- dispatch-context P6-dispatch-context-verifier.md 已读（强制指令）
- P0-brief / AGENTS.md / P1-requirements.md 已读
- P1 BDD 计数：grep -c '^#### BDD-' = 53 ✓
- HEAD=2772891(P5) / p5_pass_commit=92edcfc / P4a d1c2aca / P4b 99a4c19 / P4c 92edcfc / P1 f75e129
- git status 起点：.state.yaml(staged) + gate-events.jsonl(M) + P6-dispatch-context-verifier.md(untracked)，无残留
- [PROD_NOT_TOUCHED] 仅 worktree 内读 + 写 P6-acceptance.md + P6-evidence/

## §4.1-§4.18 全量 pytest 验收
- `timeout 400 python3 -m pytest agate/tests/ -k tag0034 -q` → 90 passed / 0 failed / 1537 deselected，EXIT_CODE 0
- 全部 53 条 BDD 均有直接 `test_bdd_NN_*` 用例（+ T1/T2/T3）；映射见 P6-evidence/pytest-tag0034.log 的 -v 清单
- 证据落 P6-evidence/pytest-tag0034.log（含 -q 汇总 + -v 逐条 + 末行 EXIT_CODE: 0）

## 文档断言类（BDD-10/41/45/46/47/48/49/51/52/53）
- grep 关键措辞逐条命中 → P6-evidence/doc-assertions.log
- dispatch-protocol.md：506 行「### 0. 派发路由」新节含「不认谁生产的」(529)/「候选回落 ≠ 状态机 retry」(535)/「gate FAIL 绝不换候选」(538)/步在铁律1前(514)；「## 派发编排机制」(502) + author 内容 vs 跨文件一致性验证 (588)；单 Agent 模式 no-op (565-566)；P5→P4 机械重解析 + 不升档 (570-571)
- architect.md 209「## 批次设计」节 225 行含「补协议文档正文 = P4」「P7 一致性检查只做跨文件一致性验证、不 author 文档内容」
- design-note 头部+§2.1+§2.2：try-and-fall / agate-workspace/dispatch-routing.yaml / dispatch-tiers.yaml / 两正交轴 / (phase,role) / 弱缓解 / 强缓解 / 自动化不对称 / 两条完整性不变量 / 不追求跨机可复现 全部命中
  - 观察：§5「影响面」(195) / §7「待确认事项」(220) 仍留旧串 `rules/dispatch-routing.yaml`——超出 BDD-46 声明范围（头部+§2.1+§2.2），且 P3 编码的 test_bdd_46 全文正向断言绿；跨节一致性归 P7。记录不判 FAIL
- roadmap RM-AG0060 行 (68)：无「按序探测」「rules/dispatch-routing.yaml」，含 try-and-fall + 两轴 + 项目级落点
- platform-notes.md 27 行 effort 能力探测 + `--effort` + 「引入版本未核实」+ 2.1.266/2.1.263 实测标注；110 行结构化输出 presence 级判据小节

## 回归护栏（BDD-39/40）
- `git diff --stat f75e129..HEAD -- phases.yaml check-gate.py check-state-transition.py state-machine.md` = 无输出（零改动）
- test_tag0027_b2_agate_dispatch.py / test_tag0027_b2_audit2_dual_anchor.py 零改动
- `grep -c dispatch_route <task>/gate-events.jsonl` = 0（BDD-40 事件计数）
- regression/test_tag0034_zero_change.py 独立复跑 2 passed
- 证据 → P6-evidence/regression-zero-change.log
- P5 证据复用：.state.yaml p5_pass_commit=92edcfc；`git diff --stat 92edcfc..HEAD -- . ':(exclude)agate-workspace/tasks/*'` 无输出 → 审计 7 reuse_allowed；BDD-40 全量回归全绿部分引 ../P5-test-results/unit.md（1625 passed / 0 failed）

## BDD-42 平台无关性
- `grep -nE '\.codex/sessions|\.claude/projects' check-judge-verdict.py check-p6-provenance.py` = 0 命中
- `git log f75e129..HEAD --` 这两脚本 = 无 commit；`git diff --stat` = 零字节改动
- test_bdd_42 独立复跑 PASS
- 证据 → P6-evidence/bdd-42-platform-independence.log

## post-test 环境残留检查
- `git status --porcelain`：仅 .state.yaml(staged, 既有) + gate-events.jsonl(M, 既有) + P6-dispatch-context-verifier.md(主 Agent 输入) + P6-evidence/ + P6-progress.md
- 无残留、无 task dir 之外的意外文件；主 checkout / ~/.agate 未写入 → [PROD_NOT_TOUCHED]
- 本任务测试纯脚本 + mock/fixture，未建外部资源

## 结论
- PASS 53 / FAIL 0 / BDD 总数 53（PASS+FAIL = 53 ≥ 53）
- 自查≠gate：不声称验收已通过；gate 由主 Agent 跑

## 格式预检（返回前）
- check-p6-format.py --fix P6-acceptance.md → EXIT 0（frontmatter pass:53 / fail:0 保留；总结行用 **Summary** 未被误计）
- check-p6-evidence.py <TD> → EXIT 0（"53 条 BDD，证据目录非空"）
- check-p6-provenance.py <TD> → EXIT 2（WARNING 不阻塞；唯一剩项 = P3-test-cases.md 缺 agent 字段，属 P3 上游文件 + 非 P6 证据，P6 verifier 不改）
  - 已给 doc-assertions.log / bdd-42-platform-independence.log 追加 SUMMARY + EXIT_CODE: 0 尾行，消除「缺 EXIT_CODE 尾行」两条 WARNING
- check-gate.py P6 <TD>（自查，非 gate）→ EXIT 2（P6 正常通过码；"FAIL=0，NC=0，P6_TOTAL=53"）
- P6-evidence/ 4 文件：pytest-tag0034.log(9.4K) / doc-assertions.log(23.6K) / regression-zero-change.log / bdd-42-platform-independence.log —— 均含实质输出
