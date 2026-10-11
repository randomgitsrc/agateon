## [plan-eng-review] 进度日志（retry 1 复评）
> 首轮日志见同目录 `P2-plan-eng-review-progress.md`（首轮结论 = rejected，1 BLOCKER = B1）。

- 已读：retry1 增量指引 / 首轮完整指引 / P2 卡 / role 定义 / P2-design.md（438 行）/ P2-review.md（首轮）/ .state.yaml / architect 修复轮进度
- 下一步：独立复现 B1 闭合（副本真改 obligations.yaml）+ 核 NB-1..5 + 回归核验

### 独立核验（只读 / /tmp/opencode 一次性副本，同一次 bash 调用内建→跑→删；跑前后真仓 git status 哈希一致）
- **B1 闭合复现**（副本 `tag0051-b1`）：按修复方案真改 4 条 statement + OBL-P8-04 `enforced_at → gate_p8` ⇒
  `check-obligations.py` = `M 类占比: 56/121 = 0.4628（基线 56/121）` + `OK` + **RC=0**；
  `test_obligation_enforced[OBL-P8-04]` **1 passed**；等价 BDD-21 探针 `P8_count:14 violations:[]`（其余 10 条零误伤）。
- 现仓计数：`{'R':30,'C':35,'M':56}` total 121；禁止词改前仅命中 4 条被处置 statement（:746/755/780/815）。
- **NB-3 零触发实测**（副本 `tag0051-nb3`）：基线 consistency RC=0/CHECK9 PASS → 加 `docs/design-notes/r6-differential-prepare.sh` 探针 → CHECK9/CHECK10 **NO_DIFF**；
  对照：`agate/scripts/check-nb3probe.py` → CHECK 9 WARN 点名该文件（探针非真空）。SG.6 在副本内 1 passed。
  代码面：`uncovered_gate_scripts()` 扫描面 = `agate/scripts/check-*.py` + hook 薄壳；CHECK 10 明示不含 `docs/`、`agate-workspace/`。
- NB-1：设计已改述「无值消费方」+ M11 不消费；`tech-debt.md` **已实际追加 DEBT0069**（38 行）。
- NB-2：`check-changelog.py` 实测在 `pre-commit-gate.py:1086`（仅 stderr 警告）；`check-gate.py` **无** check-changelog 调用（→ NB-7）；被删四块均 WARNING（不 return）⇒ (rc,ERROR) 不变。
- NB-4：§1.2 已点名 WORKFLOW.md / orchestrator-template.md / assets/templates/* + 理由。
- NB-5：R11 已新增（受众 = 所有用 agate 的项目 + 在途非 legacy 任务；语义向前变更 vs 机械非破坏两轴）。
- gate_commands 逐 key `is_legal_gate_key=True`、无 `&&`；dispatch_plan `parallel_limit=8` + 8 批 ≤ 8；candidate_count 3 == 候选 A/B/C；ui_affected false。
- `git status --porcelain agate/ docs/` = 空（无删测试 / 无 M 改判 C、R）。
- 结论：**approved**（0 BLOCKER；B1 闭合 + NB-1..5 落实 + 无新破坏；非阻塞 NB-6..NB-9）。
