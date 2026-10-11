# P4-review-code 进度（review 角色）

- [x] 读角色定义 `review.md` + dispatch-context
- [x] 盘点工作区改动（`git status` / `git diff --stat`，20 改 + 新增）
- [x] 读核心实现 diff：`check-gate.py::gate_p8`、`agate-release.py::gate`、`release.yml`
- [x] 读契约：`level-1.yaml` / 新 `level-2.yaml` / `LEVELS.yaml`；核对 sha256 登记
      （level-1=6ace03c9…、level-2=741afaf7… 均与 LEVELS.yaml 一致）
- [x] 读 `r6-differential-prepare.sh` 全文；读 obligations / phases / state-transitions diff
- [x] 定向跑测试（tag0051_* / release_gate / obligations）：
      35 passed / 1 failed（唯一红 = `test_bdd_22_*` 设计性必红）+ 62 passed（obligations_enforcement）
- [x] 实测 `agate-release.py gate` fail-closed（in_progress→1 / 坏 JSON→1 / 不存在 cmd→1 / empty→0 / consistency→1）
- [x] 实测 `r6-differential-prepare.sh` 边界：`--dst /`→2、相对→2、空→2、src 内→2、**dst==祖先→未拦（删源）**、
      软链 dst→只删链（目标存活）、含空格 src→OK、固定默认 dst→并发竞争面
- [x] 核 legacy/level-1 不被枚举误伤（AGATE_ROOT=dev：legacy→2、l1→2、l2-ok→2、l2-bad→1、l2-none+reason→2）
- [x] 核 `_delivery_spec`/`load_contract` 单源（无 AGATE_ROOT 时读已装 v0.81.0 无 level-2 ⇒ no-op，属未发布态，非缺陷）
- [x] 检索消费方残留：`WORKFLOW.md:327` / `state-machine.md:400-408` / `P5-verification.md:147` 仍述已删的 version/bump 语义
- [x] 结论：0 CRITICAL；INFORMATIONAL ×6 → `P4-review-code.md` status: **approved**

## 增量复审（retry 1，覆盖更新）
- [x] 读 retry1 指引 + 首轮本文件；pin 审阅快照（`d4e32f4f` + 工作区 diff sha256=2175785…e29fa）
- [x] 逐条核首轮 INFO 处置：INFO-1（WORKFLOW/state-machine 已闭）、INFO-2（wrapper 祖先+allow-prefix 实测 rc=2 全拦）、
      INFO-5（SEC-01 空 runs→rc1 实测闭合）；INFO-3/4/6 仍开（非阻塞）
- [x] 重跑 Pass-1 六 CRITICAL：枚举消费方+legacy 零误伤 / fail-closed（+SEC-01/09 更强）/ TOCTOU（残余 INFO-4）/
      删四 WARNING 无静默通过（R6 rc2->2 为物证）/ wrapper NB-8 六负例 / 凭证
- [x] 抽查 R-C 12 测试文件断言：未弱化（正向重定向+新载体 `check-changelog==1` 增强；2 处真缺陷修复）
- [x] 独立复现 R6（`r6-differential.sh`：39/2/0 rc=0）；一致性 `--strict-errors-only` rc=0（0 ERROR/432 WARNING）
- [x] 新析出 N1（wrapper `cp -a` 含 `.worktrees` 失败 rc=1；剔 `.worktrees` 后 rc=0=根因确认）、
      N2（文档传播残留，已被并发 R-E retry 2 定向处理）、N3（断言风格）
- [x] 结论：0 CRITICAL；→ `P4-review-code.md` status: **approved**（针对 pin 快照；R-E 落地后需定向重验）
