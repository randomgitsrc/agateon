# P6 验收 g2（BDD-27..52）results — TAG0037，验证基线 HEAD 043181d

- PASS BDD-27: agate-resolve.py 对软链 ~/.agate fail-closed：pytest 7 例（含 T-14 五变体）全过；真实调用 exit=1、stdout 无 AGATE_ROOT=、stderr 含三步片段、软链目标内容哈希不变 (bdd-27-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-28: 解析链仅三层且无 use_legacy：pytest 8 例（a–e）全过；真实运行 (a)(e) AGATE_ROOT 覆盖 exit 0、(d) exit 1；inspect.signature 无 use_legacy、agate_common.py 无 realpath(base) (bdd-28-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-29: install.sh 无参/--versions 进入版本布局：pytest 5 例全过；真实安装两入口 exit 0、~/.agate 为实体目录、含 repo/ latest/current/scripts、两版本根树相等、源 checkout git status 不变、install.sh 无 ln -s/LINK_NAME、未知参数 exit 2 (bdd-29-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log, bdd-36-migration-walkthrough.log)
- PASS BDD-30: 废弃环境变量有明确处置：pytest 4 例全过；真实运行 exit 0、stderr WARNING、AGATE_SYMLINK/AGATE_REPO_DIR 指向路径均未创建、install.sh 除 WARNING 外不再引用 (bdd-30-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-31: install.sh 软链 fail-closed：pytest 10 例（2 入口×5 变体）全过；真实调用 L L/ L// L/. L/.. 共 10 次均 exit 1、三步片段（L/.. 拒绝 .. 分量）、目标及物理父目录不变、git 调用 0 次 (bdd-31-pytest.log, bdd-31-32-33-real-invocation.log)
- PASS BDD-32: agate-install.py 软链 fail-closed：pytest 22 例（3 入口×5 变体 + --adopt×5 + 既有 tag0032_bdd_1/2）全过；真实调用 15 次均 exit 1、三步片段、目标不变、零 git 调用 (bdd-32-pytest.log, bdd-31-32-33-real-invocation.log)
- PASS BDD-33: install-offline.py 软链 fail-closed 且不误伤：pytest 12 例全过；真实调用 AGATE_HOME 与 --dest-root 各 5 变体共 10 次均 exit 1、目标不变；普通已存在/新建 dest-root exit 0 装出 vX.Y.Z/current/latest (bdd-33-pytest.log, bdd-31-32-33-real-invocation.log)
- PASS BDD-34: agate-summary.py 软链基址给迁移提示：pytest 1 例全过；真实运行 exit 0、AGATE_ROOT 行为无可用、含 mv ~/.agate ~/.agate.bak 提示、无 Traceback (bdd-34-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-35: 迁移三步文案跨入口一致：pytest 4 例（bdd_35 ×2 + 保留并扩展的 debt0034 ×2）全过；真实 install.sh / agate-install.py / agate-resolve.py 输出同一三步文案 (bdd-35-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-36: 迁移三步隔离环境可走通：pytest 1 例全过；真实执行从 install.sh 拒绝文案提取的三步均 exit 0，结果满足 BDD-29 结构、agate-resolve exit 0、.agate.bak 原软链完好、改名回滚回到软链态 (bdd-36-pytest.log, bdd-36-migration-walkthrough.log)
- PASS BDD-37: 全仓旧称残留拦截：pytest 38 例全过；独立实扫基线 75a8102 命中 23 个文件（=P1 预期），HEAD 命中 8 个且全在白名单 W 内、R 集合 12 文件 0 命中、use_legacy 仅 tech-debt.md、原口径 grep 非白名单无残留 (bdd-37-pytest.log, bdd-37-scan.log)
- PASS BDD-38: 4 个 legacy 测试处置：pytest 6 例全过；ast 比对：撞名 test_bdd_30* 仅 test_bdd_30_legacy_symlink_direct_root 被改写、其余 5 个函数体逐一相同；test_tag0032_bdd_1/2 函数体相同；test_debt0042 已改写为 fail-closed；UPGRADING 对照表 ④ 由 UC/UL 用例覆盖 (bdd-38-pytest.log, bdd-38-ast-compare.log)
- PASS BDD-39: 文档面旧称改写完成：pytest 21 例（UC bdd_39 ①–⑤、DS ⑥–⑧、NLR 12 个 R 文件清零 ⑨）全过 (bdd-39-pytest.log, bdd-37-scan.log)
- PASS BDD-40: 协议根遗留路径改为解析出的根：pytest 5 例（DS 静态 3 + SD/SUM 动态 2）全过 (bdd-40-pytest.log)
- PASS BDD-41: SETUP 的 $AGATE_DIR 取值去 fallback：pytest 2 例全过；逐字执行 SETUP 首个 bash 块得 $HOME/.agate/current/agate 且模板可读、块内无 || echo fallback、current 缺失时明确失败提示 (bdd-41-pytest.log, bdd-41-45-real-setup-commands.log)
- PASS BDD-42: Claude Code 接入 agate 侧命令：pytest 1 例全过；逐字执行 SETUP Claude 块，链接可读、目标在隔离 AGATE_HOME 内、frontmatter yaml.safe_load 含 name: orchestrator；另 H-1 已执行一次见 h1-claude-orchestrator.log（非 BDD） (bdd-42-pytest.log, bdd-41-45-real-setup-commands.log, h1-claude-orchestrator.log)
- PASS BDD-43: OpenCode 接入实跑：pytest 1 例全过（真实 opencode 在 PATH，未跳过）；逐字执行 SETUP OpenCode 块后 opencode debug agent orchestrator exit 0，JSON mode==primary、tools.task==true (bdd-43-pytest.log, bdd-41-45-real-setup-commands.log)
- PASS BDD-44: DSH 接入命令实跑：pytest 1 例 + 既有 test_dsh_preset.py 9 例全过；逐字执行 SETUP DSH 块（跳过 install-hook 行），三链接均可读、agate-summary.py exit 0 且无漂移警告 (bdd-44-pytest.log, bdd-44-dsh-preset-pytest.log, bdd-41-45-real-setup-commands.log)
- PASS BDD-45: Codex 接入实跑：pytest 1 例全过（真实 codex 在 PATH，未跳过）；模板可读，timeout 60s codex features list exit 0，multi_agent 行为 stable / true (bdd-45-pytest.log, bdd-41-45-real-setup-commands.log)
- PASS BDD-46: out-of-scope 文件零 diff：P3 §7.5 命令 git diff --stat 75a8102..HEAD -- <清单> 输出为空（pathspec 命中 19 个受保护文件），resolve-entry.py 零 diff；OOS pytest 4 例全过 (bdd-46-git-diff.log, bdd-46-pytest.log)
- PASS BDD-47: hook 解析路径不受影响：pytest 11 例（test_hook_resolve_entry.py 全部 + test_agate_root_self_locate_worktree + workspace-resolve bdd_47）全过 (bdd-47-pytest.log)
- PASS BDD-48: pytest 不减反增：CI 口径全量实跑 2292 passed / 0 failed / 2 skipped（skipped 为 Pillow 已安装的 2 个既有条件跳过，未超 2）≥ 基线 1842；count-tests 2294；AST 对账测试函数 1661→1896 净 +235，仅 3 个改名无净删（A−D≥0） (bdd-48-full-pytest.log, bdd-48-count-and-reconcile.log)
- PASS BDD-49: 收口：check-protocol-consistency --strict-errors-only exit 0（0 ERROR，CHECK 7/13 PASS）、ruff 0.16.4 All checks passed、shellcheck -S warning 4 文件 exit 0；④ 新脚本登记 scripts/README pytest 2 例全过 (bdd-49-commands.log, bdd-49-pytest.log)
- PASS BDD-50: 发布物就绪度（P6 验收范围=发布前就绪度（BASELINE_CHANGE），最终事实 P8 复验）：UPGRADING 存在 ### v0.73.0 节标注 BREAKING 与迁移三步；CHANGELOG [Unreleased] 含本任务条目、BREAKING 标注及 UPGRADING 指针；README badge 为 v0.72.0 非 1.0；release.yml 触发 on: push tags v* 与权限 contents: write 可如实列出；CHECK 7/13 通过；UC pytest 1 例全过 (bdd-50-readiness.log, bdd-50-pytest.log, bdd-49-commands.log)
- PASS BDD-51: 软链基址指向完整版本根：pytest 3 例全过；真实运行 resolve exit 0、REASON=全局 current、AGATE_ROOT 为目标内 vX.Y.Z/agate；agate-install.py latest exit 1 且 stderr 含三步及"解析仍可用"说明；summary 不打印迁移提示 (bdd-51-pytest.log, bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-52: 排除 agate/tests/ 后包内脚本冒烟无 Traceback：pytest 1 例全过（真实 HEAD 经 materialize 解包，四脚本两种调用形态） (bdd-52-pytest.log)

**Summary**: 26 PASS, 0 FAIL

H-1（非 BDD，不计入总数）：已执行一次 claude --agent orchestrator -p "echo test"（隔离项目目录、--no-session-persistence），orchestrator 被选中并返回，无 Failed to parse agent；详见 h1-claude-orchestrator.log。

脚本与说明：cmd-scripts/ 为本组驱动脚本；bdd-31-32-33 / bdd-27-28-…-51 / bdd-41-45 日志头部已如实注明驱动脚本自身的两处小缺陷（未影响产品判定，均已重跑修正）。
