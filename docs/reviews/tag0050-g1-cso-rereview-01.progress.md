# TAG0050 G1 · cso 聚焦复审（第 3 轮整改后）进度留痕

- 角色：cso（安全官复审）
- 任务：P4 批 G1（A2+A3+A4）fix3 后，核 K1–K6 是否闭合 + 是否引入新安全阻断
- 输入：`P4-dispatch-context-cso-G1-rereview.md`、`P4-review-cso-G1.md`（首轮）、
  `P4-implementation-G1.md`、`P4-progress.md`、本次 diff、设计 §2.4/§2.7/§2.9
- 工作目录：`/home/kity/oclab/agateon`（HEAD `b0a16c3a`，分支 `feat/TAG0050-task-data-contract`，v0.79.0）
- 环境隔离：`[PROD_NOT_TOUCHED]`；全部验证在仓外副本 `/tmp/opencode/cso-g1-re3/` 内做

## 时间线

- 起手：读 cso 角色 + dispatch + 首轮 cso 评审 + 实现记录 + 进度
- 读码：`agate-ci-verify.py`（全文）、`check-obligations.py`、`test_tag0050_obligation_behavior.py`、
  `test_tag0050_obligations.py`、`test_tag0050_obligations_enforcement.py`、`test_tag0050_ci_replay.py`、
  `test_tag0050_a0_a1_ledger.py`（BDD-25 段）、`pre-commit-gate.py`（规则 4 段）、
  `agate_common.check_ledger_events`
- 建副本：`/tmp/opencode/cso-g1-re3/agate` = 本 checkout `agate/` 工作树副本
- K1：构造 evil-merge 删账本仓 `repo` → 实跑；又建 `agate-oldledger`（解耦调用置空）对照
- K2/K3：副本 `k2neg` 删 `check-gate.py` 的 `delivery` 执行分支 → 行为凭证/旧登记凭证/检查器三路对照
- K4：副本内跑 `test_k1_evil_merge...` / `test_bdd_30...` / `test_bdd_30b...` → 3 passed
- K1 边角：整目录改名（BDD-25 放行）在 CI 账本检查下被误判 FAIL；F-4 变体（移入别目录/.bak）被正确拦截
- 追加：合法 append 不误报；G1 验收面副本内 92 passed / 2 failed（2 例为副本协议解析差异，非缺陷）
- 收尾：真实仓库 `git status --porcelain` 与评审前逐行一致（53 行）

## 事故与恢复（如实留痕）

- 误操作：首次构造临时仓的 bash 因 `cd "$R"`（$R 未 mkdir）失败，后续命令在**真实仓库** cwd 下执行，
  误产生一个提交 `2e6bb16d init`（只改了 `README.md`）+ 暂存区脏 + 新建 `.agate-version`、
  `agate-workspace/tasks/TAG0001/`。
- 恢复：`git reset --mixed b0a16c3a` → `git checkout b0a16c3a -- README.md` →
  `rm -rf .agate-version agate-workspace/tasks/TAG0001`；`git status --porcelain` 与评审前
  `status_before.txt` `diff` 为空（IDENTICAL）。HEAD 回 `b0a16c3a`，无 `feature` 分支 / `notes.md` /
  `MERGE_HEAD` 残留。`git config user.*` 值与历史作者一致（`t <t@t>`），未改变。
- 后续所有临时仓改用脚本文件（先 `mkdir` + 校验 `pwd`）+ 绝对路径，未再触及真实仓库。
