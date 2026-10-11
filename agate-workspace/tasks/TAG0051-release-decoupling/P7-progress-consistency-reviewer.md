# P7-progress-consistency-reviewer — TAG0051

- 读 role `consistency-reviewer.md`（v0.81.0）+ dispatch-context（强制指令）。
- 读 P0-brief / P1-requirements / P2-design / P3-test-cases / P4-implementation / P6-acceptance / P6.5-judge-verdict。
- 只读实测：P1 `^#### BDD-` 计数 = 23；P4 `DESIGN_GAP` 零命中；P4 `CODE_MAP_EXEMPT` = 4 表行；
  `CODE-MAP.md` 未含 4 个新文件；`decisions/` 不存在；ADR-016 落 `agate/adr.md:663`。
- `git diff --name-only 581369fc..9771e76a`：M1–M16 全部 16 文件均在实际改动面内。
- BDD 内容抽核 3 条（bdd-01/bdd-11/bdd-17）→ 映射正确，非数量对内容错。
- D1–D5 逐条复核（P2 `cp -a` 尚存 / wrapper 实为 `git clone`；r6 `_error_lines` :251；test 注释 :6；
  README 模板两处 :1335/:284）→ 均 accepted。
- /tmp/opencode 副本 dry-run：`check-gate.py P7` → `成对声明聚合判据通过` rc=0；真实仓库账本未触。
- 产出：`P7-consistency.md`（status: approved）。
