# P4-progress — implementer R-F（retry 3，最后一轮，收口）

状态：[PROD_NOT_TOUCHED]

- 读角色文件 `implementer.md` + dispatch-context `P4-dispatch-context-implementer-R-F.md`。
- 基线：语义族 grep（改动前）= **38** 命中（存 `/tmp/opencode/tag0051-rf-grep-before.txt`）。
- 基线：wrapper 复跑（cp -a 版）rc=0，`legacy 任务 39 个，差异 2 条，未匹配 0 条`，ELAPSED=28.96s，corpus=449M。
- ① `agate/scripts/check-gate.py` `gate_p8` 函数头注释：删过时「version 文件路径…」两行，改述「本函数只做脚本化可判部分（bump_type / debt_check / 结构化 delivery（method 枚举）/ roadmap RM 反查）；其余需主 Agent 自判」。仅注释，无行为/判据改动。
- ② `agate/assets/templates/dispatch-prompt.md:277`：节标题「## 版本 bump 判定」→「## `bump_type` 意图判定（不执行 bump；对外发布由独立流程负责）」，新增首行澄清「P8 只声明 `bump_type` 意图…不执行 bump、不打 tag」；其余 major/minor/patch 判据原文保留。
- ③ `agate/dispatch-protocol.md:487` 节名索引：「版本 bump 判定」→「`bump_type` 意图判定（不执行 bump；对外发布由独立流程负责）」（与 ② 逐字一致）。
- ④ `docs/design-notes/r6-differential-prepare.sh`：建 corpus 由 `rm -rf + cp -a + checkout + clean -fdx` 改为 `git clone --local --no-hardlinks --quiet <src> <dst>`（含文件头行为序列 + 隔离说明同步）；外部契约不变（同样 `--src/--dst`、同样透传、corpus 干净、真仓只读）。
- 自检②：wrapper 复跑 rc=0，`legacy 任务 39 个，差异 2 条，未匹配 0 条`，ELAPSED=**7.58s**（↓ 21.4s，约 3.8×），corpus=101M，`git status --porcelain` 空；三项负例（空/相对/src 内）仍 exit 2 且不删东西。
- 自检①：grep 38 → **35**（-3 = ①②③ 三条目标行），新增命中 0 条。
- 自检③ shellcheck rc=0；④ check-structure-consistency rc=0（S1-S6+S0 全 OK）；⑤ check-protocol-consistency --strict-errors-only rc=0（0 ERROR/432 WARNING）。
- 自检⑥：`test_tag0051_docs_consistency.py + test_check_gate.py` → **227 passed**；另跑 `test_tag0051_r6_harness.py` → 5 passed。
- 未改（超出 4 文件授权面，如实标注）：`agate/tests/unit/test_tag0051_r6_harness.py` 顶部注释、`agate-workspace/tasks/TAG0051-release-decoupling/P2-design.md` §5/§8 仍述「cp -a 建 corpus」——属**机制描述**（非外部契约），待主 Agent 裁决是否随本批更新。
