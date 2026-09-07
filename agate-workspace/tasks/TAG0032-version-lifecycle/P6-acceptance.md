---
phase: P6
task_id: TAG0032
type: acceptance
parent: P5-verification.md
trace_id: TAG0032-P6-20260907
status: draft
created: 2026-09-07
agent: verifier
# ── v2.0 机器汇总 ──
pass: 14
fail: 0
ui_affected: false
---

# P6-acceptance — TAG0032 版本管理生命周期可用性批（14 条 BDD 逐条验收）

[PROD_NOT_TOUCHED]
[NO_NEED_CONFIRM]

- 验收模式：模式二（P6 验收）。非 UI 任务（P2 `ui_affected: false`）——无 vision-analyst、无截图；
  证据 = 每条 BDD 的 pytest `-v` 实跑日志（末行 `EXIT_CODE: <n>`）+ BDD-5 隔离 HOME 端到端 transcript。
- 执行目录：`/home/kity/oclab/agateon/.worktrees/agate-TAG0032`（worktree 根）；主 checkout 未触碰。
- 解释器：`/usr/bin/python3`（pytest 9.0.3）。单步串行，bash 外层 `timeout`（全量 pytest 600s / 单 BDD 120s / 端到端 300s / 其他 120s）。
- 只读验收：未改任何代码 / 测试 / 文档。P6-evidence/ 内文件为唯一新增产出（+ P6-acceptance.md / P6-progress.md）。
- BDD → 测试函数映射取自 P3-test-cases.md「BDD → 用例映射」表；每条按 dispatch-context 映射表实跑。

---

## 逐条 BDD 验收结果

### 3.1 断点一：入口断链修复

- PASS BDD-1: legacy 软链布局下 `agate-install.py` 被 fail-closed 拒绝（exit≠0），软链目标内不出现新建的 `repo/` / `vX.Y.Z/`——穿透污染被阻断。`test_tag0032_bdd_1_legacy_symlink_install_fail_closed` 1 passed, EXIT_CODE 0 (bdd-1-install-symlink.log)
- PASS BDD-2: 拒绝信息的 stderr 同时含三段可 grep 的命令片段级迁移指引——备份软链（`mv ~/.agate …bak`）、建目录根（`mkdir -p ~/.agate`）、装版本（`agate-install.py latest` / `install.sh --versions`），缺一即 FAIL 的三段逐段断言均通过。`test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint` 1 passed, EXIT_CODE 0 (bdd-2-migration-hint.log)
- PASS BDD-3: 普通（非软链）目录布局 install 不被新拒绝逻辑误伤——`agate-install.py v<X.Y.Z>` exit 0 且 `~/.agate/v<X.Y.Z>/` 建立成功；附加 M2（指定版本路径也建根 `~/.agate/scripts/` 入口副本）亦通过。`test_tag0032_bdd_3_plain_dir_not_falsely_rejected` 1 passed, EXIT_CODE 0 (bdd-3-plain-dir.log)
- PASS BDD-4: install 完成后根 `~/.agate/scripts/agate-install.py` 存在且 `--help` exit 0（README 快速上手入口不再 No such file）；`agate/tests/` 内有用例锁定所选建立方式（决策 B1 副本）在重跑 latest 后随 current 刷新（判据 2）；该维护语义与 UPGRADING「版本管理生命周期」节所写一致（判据 3）。判据 1/2：`test_tag0032_bdd_4_root_scripts_established_and_executable` + `test_tag0032_bdd_4b_root_scripts_copy_refreshed_on_reinstall` 2 passed, EXIT_CODE 0；判据 3：`test_upgrading_lifecycle.py::test_tag0032_bdd_4_root_scripts_copy_semantics_documented` 1 passed, EXIT_CODE 0 (bdd-4-root-scripts.log, bdd-4-doc-semantics.log)
- PASS BDD-5: 新机器有从零进入版本布局的官方路径——`install.sh --versions` 产出 `repo/` + `vX.Y.Z/` + `current`/`latest` 指针 + 根 `scripts/`，且过程不在源仓库树内新建 `repo/` / `vX.Y.Z/`。单测：`test_tag0032_bdd_5_install_sh_versions_bootstrap` 1 passed, EXIT_CODE 0。额外实测（隔离 `HOME=$(mktemp -d)` + 本地构造元仓库形态 fixture git repo（`agate/` 子目录 + `v0.43.0`/`v0.50.0` tag，根无 `scripts/`），从无关目录 `cat <worktree>/install.sh | bash -s -- --versions`，`AGATE_REPO_URL` 注入 fixture）：install.sh --versions EXIT 0；`$HOME/.agate/` 目录树含 `repo/` + `v0.50.0/` + `current → latest → v0.50.0` 指针 + `scripts/agate-install.py`；`$HOME/.agate/scripts/agate-install.py --help` EXIT 0；worktree `git status --porcelain` 仅 P6 产出、`find` 扫描无新建 `repo/` / `vX.Y.Z/`；测完 `rm -rf` 隔离 HOME，真实 `~/.agate`（legacy 软链 → `/home/kity/oclab/agateon/agate`）未触碰 (bdd-5-install-sh-versions.log, bdd-5-curl-bash-transcript.txt)

### 3.2 断点二：元仓库 gap 修复（RM-AG0058 本体）

- PASS BDD-6: resolve 对元仓库形态版本目录（协议在 `agate/` 子目录、`vX/scripts/` 不存在）返回协议子目录——`AGATE_ROOT` 指向 `~/.agate/v<X.Y.Z>/agate`，且 `AGATE_VERSION` 仍为 `v<X.Y.Z>`（版本号不回归，I-1）。`test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir` 1 passed, EXIT_CODE 0 (bdd-6-meta-resolve.log)
- PASS BDD-7: 「根即协议」部署方（`vX/scripts/` 直接存在）解析语义不变——`_protocol_root` 探测序 1（`vdir/scripts`）先命中，`AGATE_ROOT` 仍为 `~/.agate/v<X.Y.Z>`（不进 `/agate` 分支），`AGATE_VERSION` 仍为 `v<X.Y.Z>`（纯增量红线，与 BDD-6 对称）。`test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged` 1 passed, EXIT_CODE 0 (bdd-7-rootproto-resolve.log)
- PASS BDD-8: 元仓库形态版本钉版后 hook gate 路径存在、commit 不再被阻断——`resolve-entry.py pre-commit` 解析出的 gate 路径 `<解析根>/scripts/pre-commit-gate.py` 存在并被 exec（stub marker 命中），不因「gate 脚本不存在」exit 1。`test_tag0032_bdd_8_meta_repo_hook_gate_path_resolves` 1 passed, EXIT_CODE 0 (bdd-8-hook-gate-path.log)
- PASS BDD-9: 两形态下现有全量 pytest 均全绿——`pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto` → `1484 passed, 2 skipped`，EXIT_CODE 0。新增的元仓库形态双 fixture 用例（`_make_home_meta` / `_make_home_meta_hook`）与「根即协议」fixture（`_make_home_rootproto`）常驻并存全绿，无直接拼 `vdir/scripts` 的解析旁路被漏改（DEBT0016 回归锁）。P5 记录的预存并行 flaky（`test_nc_cross_checkout_paths_hash_consistent`，与 TAG0032 改动无关，见 known-failures.md）本轮全量运行未复现，套件 0 失败 (bdd-9-full-suite.log)

### 3.3 断点三：update 统一入口（文档面）

- PASS BDD-10: 两种布局的更新指令在文档面对齐且各自幂等——`agate/UPGRADING.md`「版本管理生命周期」节：legacy 明确为 `git pull`（含 `install-hook.py` 判定口径），版本布局明确为 `agate-install latest` 并声明幂等（重复执行不报错、不重复建版本目录）。`test_tag0032_bdd_10_update_commands_aligned_and_idempotent` 1 passed, EXIT_CODE 0 (bdd-10-update-aligned.log)
- PASS BDD-11: `agate/UPGRADING.md` 新增「版本管理生命周期」节覆盖四动作——该节存在且安装 / 迁移（legacy → 版本布局）/ 更新 / 回退均有对应命令或步骤；写明 hook 重装时机（薄壳固定 + resolve-entry 机制下通常无需随版本重装）；含一条根 `~/.agate/scripts/` 建立方式（副本）的维护语义条目（与 BDD-4 判据 3 交叉锁）。`test_tag0032_bdd_11_lifecycle_section_covers_four_actions` 1 passed, EXIT_CODE 0 (bdd-11-lifecycle-section.log)
- PASS BDD-12: 文档面 update / 升级指引的 4 条具体矛盾表述逐条收敛——参数化 4 条 checklist（`v050_root_scripts_row_pointer` / `v050_upgrade_row_pointer` / `hook_reinstall_unified_across_version_sections` / `readme_setup_aligned`）每条命中「已收敛到新口径」或「已标注为版本历史叙事保留」，4 passed, EXIT_CODE 0；附加回归项 `check-protocol-consistency.py --strict-errors-only` EXIT_CODE 0 / 0 ERROR（329 WARNING 为既有叙事文件引用基线，无新增 ERROR）。`test_tag0032_bdd_12_doc_contradiction_converged` 4 passed 参数化 (bdd-12-doc-converged.log, bdd-12-consistency.log)

### 3.4 端到端（真实元仓库形态 + 隔离 HOME）

- PASS BDD-13: 「全新机器 → 版本布局 → 钉版 → 更新」全链路可用——隔离 HOME + 本地构造元仓库形态 upstream（`_tag_meta_upstream`：`agate/` 子目录 + `v0.43.0`/`v0.50.0` tag）：进入版本布局（`install.sh --versions`）exit 0 → 版本目录唯一 + 根 `scripts/` 就位 → 项目写 `.agate-version` 钉版 exit 0 → `resolve-entry.py pre-commit` exit 0（gate 路径存在并被 exec，marker 命中）→ 再次 `agate-install.py latest` 幂等复跑 exit 0（版本目录数量不变、指针幂等切换、不在源仓库树内新建 `repo/` / `vX.Y.Z/`）。`test_tag0032_bdd_13_full_lifecycle_new_machine_to_update` 1 passed, EXIT_CODE 0（本地 fixture 即默认路径，无网 fallback 已内建，无需 skip）(bdd-13-e2e-lifecycle.log)
- PASS BDD-14: 端到端全链路不污染源仓库——同 BDD-13 隔离 HOME 全链路执行完毕后，worktree 源仓库树 `git status --porcelain` 无新增 `repo/` 主克隆、无 `vX.Y.Z/` worktree、无非预期未跟踪条目；`agate/` 内无 `repo/` 主克隆、无 `vX.Y.Z/` worktree（TAG0008 教训回归锁）。`test_tag0032_bdd_14_e2e_no_source_pollution` 1 passed, EXIT_CODE 0 (bdd-14-no-pollution.log)

---

## post-test 环境残留检查（强制）

- **隔离 HOME 清理**：BDD-5 额外实测用 `HOME=$(mktemp -d)`（`/tmp/tmp.ZlqQolcF47`）+ 工作目录 `mktemp -d`（`/tmp/tmp.lSFvWPJ9US`），transcript 末尾 `rm -rf` 两者并打印「清理完成」；验收后复查两路径均已不存在（`ls` 返回「没有那个文件或目录」）。BDD-13/14 的隔离 HOME 由 pytest `tmp_path` fixture 自动清理。
- **真实 `~/.agate` 未触碰**：验收前后均为 `lrwxrwxrwx … /home/kity/.agate -> /home/kity/oclab/agateon/agate`（legacy 软链原样）。全程无任何命令以真实 `~/.agate` 为 HOME 目标。
- **worktree `git status --porcelain`**：仅以下本阶段产出条目，无代码 / 测试 / 文档改动——
  ` M agate-workspace/tasks/TAG0032-version-lifecycle/gate-events.jsonl`
  `?? agate-workspace/tasks/TAG0032-version-lifecycle/P6-dispatch-context-verifier.md`
  `?? agate-workspace/tasks/TAG0032-version-lifecycle/P6-evidence/`
  `?? agate-workspace/tasks/TAG0032-version-lifecycle/P6-progress.md`
  （P6-acceptance.md 为本文件，写入后同属预期产出。）
- **预存空目录说明（非本次验收产生）**：worktree 根存在一个空目录 `.agate/repo`（`stat` 时间 `2026-09-07 18:42:36`，早于 TAG0032 P3 commit `030b4f2` 的 `19:19`）。内含 0 个文件、无 `.git`、无版本目录——是本会话开始前既已存在的空脚手架（会话起始 `git status` 亦为 clean，因 git 不跟踪空目录）。非本次 P6 验收、非 BDD-13/14 端到端（用隔离 HOME 且各自的污染断言已 PASS）产生。不影响 BDD-14 判定：BDD-14 用例断言在其隔离 HOME 全链路后源树无 `repo/` 主克隆 / `vX.Y.Z/` worktree，实跑 PASS；该空目录既非主克隆亦非 worktree。只读验收不改动环境，故保留原样并在此记录。

---

## 交叉核对

- 14 条 BDD 编号 = P1-requirements.md §3 全部 BDD 编号，无重复、无遗漏。BDD-9 无独立用例（P3 §4），由全量回归套件承接，已实跑。
- BDD-4 / BDD-5 / BDD-12 各引 2 个证据文件（判据 3 独立日志 / 端到端 transcript / consistency 独立日志）。
- 每条 PASS 行括号内证据路径（相对 P6-evidence/）对应文件均存在且含实质 pytest `-v` 输出（12+ 行：session 头 + collected + PASSED 行 + summary + `EXIT_CODE`），BDD-5 transcript 78 行含完整步骤记录。
- P5 → P6 间无非产出文件改动（`.state.yaml` `p5_pass_commit: 1d9a322`）；本任务为功能任务（非 `change_type: refactor`），走既有 P6 口径，不涉及 `regression.log` / `regression_pass` 回归双证。

---

**Summary**: 14/14 PASS, 0 FAIL
