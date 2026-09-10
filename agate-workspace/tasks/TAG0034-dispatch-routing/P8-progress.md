# P8-progress — TAG0034 派发路由 发布准备（releaser / implementer P8 模式）

`[PROD_NOT_TOUCHED]` —— 仅 worktree 内读写；未触碰主 checkout `/home/kity/oclab/agateon` 与 `~/.agate`。

## 输入读取
- P8-dispatch-context-implementer.md（9 项文件改动强制指令 + 约束 + 上游关联）
- agate/assets/execution-roles/implementer.md（P8 发布准备 / P8 多包发布 / P8 临时资源清单 / Lessons Learned）
- agate/LIMITATIONS.md（局限 2 现状段 + 局限 3「P6.5 独立 Judge 缓解链」形态参照）
- docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md（末尾附录 A5.3 / A7.4 完整草案，逐字采用）
- P7-consistency.md §6（design-note §5/§7 DEVIATION 详情：L195/197 + L220/223）
- agate/adr.md（ADR-012 尾 + ADR 分隔风格）/ CHANGELOG.md 顶部 / README badges / roadmap RM-AG0060 L68 / tech-debt DEBT0039 + 模板 + check-debt.py/agate-debt-check.py closed 准入规则 / P1-requirements.md frontmatter + schema migrated_keys（含 scope_resolved）

## 逐项落地
1. agate/LIMITATIONS.md：局限 2「现状：无解…→ ADR-006」后追加「派发路由缓解链（TAG0034 / RM-AG0060 已落地）」段，逐字采用 dispatch-context 草案，诚实边界句「仍非根治…与局限 3 同构」保留。grep「派发路由缓解链」=1。
2. agate/adr.md：ADR-012 后追加 ADR-013「派发路由 / gate 生产者无关性（gate 不认谁生产的）」，逐字采用 alignment-review 附录草案（状态/语境/决策/理由/后果）。grep「^## ADR-013」=1。
3. docs/design-notes/design-dispatch-routing.md §5（L195/196/197）+ §7（L220/223）定点清理：rules/dispatch-routing.yaml → agate-workspace/dispatch-routing.yaml（+ 补档位词表在 agate/rules/dispatch-tiers.yaml）；「查表→探测→…」→「查表→派首选→逐级回落…（try-and-fall，无 probe，与 §2.2 一致）」；§7 事项 4「探测缓存 / native 探测方式」标注「2026-09-09 定案已作废」。未重写整节。grep 'rules/dispatch-routing.yaml' → 无命中。
4. CHANGELOG.md：`## [0.70.0]` 前插入 `## [0.71.0] - 2026-09-10`，`### 新增（TAG0034：派发路由…RM-AG0060 epic）` + dispatch-context 第 4 项清单（route 子命令 / dispatch-tiers.yaml / dispatch-routing.yaml + 校验器 / dispatch_route 事件 / 协议子节 / tmux / effort / ADR-013 + LIMITATIONS / DEBT0039 + SETUP + platform-notes）。grep `^## \[0.71.0\]` =1。
5. README.md + README.zh-CN.md L12 badge version-v0.70.0 → version-v0.71.0。新值各 =1，旧值各 =0。
6. agate-workspace/roadmap/roadmap.md L68 RM-AG0060：状态列 scheduled → done；更新列 2026-09-08 → 2026-09-10。关联任务列已 TAG0034；长描述 P4a M12 已回写、核无残留旧串。
7. agate-workspace/debt/tech-debt.md DEBT0039：status open → closed；task_id null → TAG0034；+ closed_at: 2026-09-10；+ 2 条 closure evidence（P6-acceptance BDD-48/49/50 + P7-consistency 0 ERROR）。check-debt.py exit 0（closed 准入：evidence 序列化含 TAG0034 + P6 标记）。
8. agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md frontmatter 新增 scope_resolved: list（DEBT0039 并入 + A5.3/A7.4 doc-sync 两项）。check-frontmatter.py exit 0（scope_resolved 在 P1-requirements.md schema migrated_keys 白名单内）。
9. P8-release.md 产出：frontmatter bump_type: minor / debt_check: reviewed / agent: implementer / trace_id: TAG0034-P8-20260910；正文含前置条件 / bump_type 依据 / 版本号变更逐文件表 / CHANGELOG 副本 / roadmap done 确认 / DEBT0039 closed 确认 / 临时资源清单=无 / SELF-GATE 面提醒 / 主 Agent 待办 / Lessons Learned。`agate-md-field-set.py --list` + `bump_type minor` set 均 exit 0。

## 清单外的连带改动（比照 TAG0033 P8 先例）
- agate/UPGRADING.md §3：`### v0.70.0` 前新增 `### v0.71.0 — 派发路由（…TAG0034：RM-AG0060 epic）` 章节（本版本无破坏性变更，写明「零迁移动作」）。原因：CHANGELOG 插入 `## [0.71.0]` 后 check-protocol-consistency CHECK 13（CHANGELOG 最新版 ↔ UPGRADING §3 章节一致）报 ERROR，dispatch-context「consistency 除 CHECK 7 外 0 ERROR」硬约束要求补此章节。TAG0033 P8-release §3 同处理。未扩到清单外其它文件。

## 自检结果
- `pytest agate/tests/ -k tag0034 -q` → 89 passed / 1 failed。唯一 failed = test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes。
- `check-protocol-consistency.py --strict-errors-only` → exit 1，ERROR (1) = CHECK 7「README version badge v0.71.0 != 最新 tag v0.70.0」。CHECK 1~6 / 8~15 exit 0；WARNING 329（P7 存量基线，本批未新增）。
- test_bdd_50 failed 与 CHECK 7 ERROR 同一根因：badge 已 bump、git tag v0.71.0 未创建的中间态；主 Agent tag 后复跑归零 → pytest 回到 90 passed / 0 failed。设计使然（DEBT0013 时序），非本批引入的回归。已在 P8-release.md §3 末尾 + §8.1 + Lessons Learned 显式绑定根因。
- check-debt.py / check-frontmatter.py(P1) / check-frontmatter.py(P8-release) 均 exit 0。
- 未 commit / 未 tag / 未 bump-version 工具。未碰冻结面（phases.yaml / check-gate.py / check-state-transition.py / state-machine.md / agate/tests/ / agate/scripts/ 代码 / dispatch-protocol.md「### 0. 派发路由」子节）。
- `[SCOPE+]`：无。`[PROD_NOT_TOUCHED]`。
