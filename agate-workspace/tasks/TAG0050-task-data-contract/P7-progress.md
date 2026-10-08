# P7-progress — TAG0050 一致性检查（consistency-reviewer）

> 分阶段落盘：逐项读取 / 逐条核对后立即追加。

- [read] 角色卡 `consistency-reviewer.md` + `P7-dispatch-context-consistency-reviewer.md`：7 条清单 + 4 处 P4 分批文件。
- [read] `P0-brief.md`、`.state.yaml`（phase=P7）、`gate-events.jsonl`（26 事件，**无 task_created** ⇒ legacy）。
- [verify] `task_level(TAG0050)=None`（账本无创建/迁入事件）⇒ P7 gate 走 **legacy 口径**（frontmatter 计数 + 正文回退），与稳定版 `~/.agate/current`（v0.79.0）gate_p7 同构。
- [count] P4 四处 `[DESIGN_GAP:]` 行首计数：`P4-implementation.md`=2、`-G1.md`=5、`-G2.md`=7、`-G3.md`=1 ⇒ **合计 15**。
- [verify] gate 的 `_p4_prose_design_gap_count` 只读 `P4-implementation.md` + `P4-implementation/`（**目录不存在**）⇒ gate 面 P4 散文 GAP=**2**；分批文件 `P4-implementation-{G1,G2,G3}.md` **不在 gate 计数面内**（dispatch 已预警）。
- [count] P1 BDD=77（BDD-01..77）；P6 `pass: 77 / fail: 0`、77 条 PASS；P6.5 judge 77/77（轮次 2/2）。
- [count] P1/P2 `packages` 各 8 项且一致（dispatch 提示"6 个"与实测 8 不符，按实测口径记录）。
- [verify] P1 无 `[SCOPE+]` / 无 `[SCOPE_RESOLVED]` / 无行首 `[NEED_CONFIRM]` / `[BLOCKER]` / `[DEVIATION-CRITICAL]` ⇒ SCOPE+ 空闭环、未决项清零。
- [verify] `agate-workspace/decisions/` **不存在**（P2 §0 已核）⇒ 无跨任务架构决策需核对。
- [count] P4「新增文件核对表」行数：`P4-implementation.md`=15 + `-G2.md`=1（`agate_schema.py`）+ G1/G3=0 ⇒ **16**。
- [verify] CODE-MAP.md 已登记 `agate_schema.py`（L37）、`agate-state-set.py`（L38）；**未登记** `agate-task-init.py`、`agate/rules/task-data/`；P4 表将既有 `obligations.yaml`/`check-obligations.py` 误列为新增 ⇒ `[CODE_MAP_DRIFT:]`（WARNING 级）。
- [verify] N1 反向传播：UPGRADING（G1/G2/D-hotfix/D-E-F 节）、WORKFLOW（1.1/2.1/2.7/2.11/2h/CI）、state-machine（legacy 重开 + state-set）、platform-notes（CI 回放）、卡片 P1/P2/P3/P6/P7/P8 + 角色卡 + CHANGELOG 均已落。
- [done] 产出 `P7-consistency.md`（frontmatter 15/15 GAP、CODE-MAP 16/16；正文 15 `[DESIGN_GAP:]` + 15 `[DESIGN_GAP_REVIEWED:]`）。
- [gate] 预跑（自查 ≠ gate）：`python3 agate/scripts/check-gate.py P7 <task>` → **rc=0**（无 WARNING）；稳定版 `python3 ~/.agate/current/agate/scripts/check-gate.py P7 <task>` → **rc=0**。
- [readonly] `git status --porcelain`：仅新增本 P7 产出（P7-consistency.md / P7-progress.md），未改任何被审查文件。
