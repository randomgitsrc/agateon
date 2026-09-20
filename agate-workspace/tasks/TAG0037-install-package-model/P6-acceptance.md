---
phase: P6
task_id: TAG0037
type: acceptance
parent: P5-verification.md
trace_id: TAG0037-P6-20260920
status: draft
created: '2026-09-20'
agent: verifier
pass: 52
fail: 0
ui_affected: false
---

# P6 验收：TAG0037 install-package-model

验证基线 HEAD 043181d（P4 修复批 895a10c + P5 重跑）。本文件由汇总 verifier 把 g1（BDD-1..26）与 g2（BDD-27..52）两组 `results.md` 转抄整合而成；未重新验证、未修改任何证据，只转抄、改写证据路径（相对任务目录）并核对。证据均存于 `P6-evidence/g1/` 与 `P6-evidence/g2/`，每条 BDD 的 pytest -v 实跑日志尾行含 `EXIT_CODE: 0`，并按 P3 §7.5 附真实环境/命令实测日志。

## BDD 逐条验收结果

- PASS BDD-01: UPGRADING contract section (single section; a version-root tree, b top-level set + violation rule, c fixed `agate/` name, d single-source path) locked by 9 tests incl. boundary CLI == library (P6-evidence/g1/bdd-01-pytest.log)
- PASS BDD-02: boundary list applied to package set on synthetic tag repo, 43 tests (must-include / must-exclude / baseline values / top-level set equality) plus online-install equality (P6-evidence/g1/bdd-02-pytest.log)
- PASS BDD-03: default-deny for unregistered top-level dir, auto-include for new file under agate/, doc block == boundary_lines(), 5 tests both sub-scenarios PASSED (P6-evidence/g1/bdd-03-pytest.log)
- PASS BDD-04: three paths H1 online / H2 offline / H3 portable produce same tree, H3 uses UPGRADING documented commands, 3 tests PASSED (P6-evidence/g1/bdd-04-pytest.log, P6-evidence/g1/bdd-17-portable-real-tarball.log)
- PASS BDD-05: old worktree-form version dir still resolves, 4/4 sub-scenarios (resolve, declared, hook root, summary) PASSED (P6-evidence/g1/bdd-05-pytest.log)
- PASS BDD-06: probe-order tests PASSED, and AST comparison vs 75a8102 shows the two existing test functions and `_protocol_root` body identical (P6-evidence/g1/bdd-06-pytest.log, P6-evidence/g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-07: old-form and new-form coexist, current resolves new form, pinned resolves old form, 2/2 sub-scenarios PASSED (P6-evidence/g1/bdd-07-pytest.log)
- PASS BDD-08: both `_protocol_root` implementations equal on 5 fixtures plus one-sided-change tripwire, 6 tests PASSED (P6-evidence/g1/bdd-08-pytest.log)
- PASS BDD-09: real pack (git plumbing) -> bundle-internal install-offline -> resolve exit 0, no agate/agate nesting, `_protocol_root(vdir)` == vdir/agate; 25 pytest incl. real-tree smoke, plus manual e2e on tag v0.73.0-tagtest.1 content (P6-evidence/g1/bdd-09-pytest.log, P6-evidence/g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-10: only AGATE_HOME set (HOME separate, no --dest-root): install lands in AGATE_HOME, latest + current->latest + root scripts + `agate-install.py --check` rc 0, 2 tests plus manual e2e (P6-evidence/g1/bdd-10-pytest.log, P6-evidence/g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-11: fake-bundle helpers replaced by real-pack bundles, sentinel (scripts/ + WORKFLOW.md, no agate-workspace/docs/site), roundtrip ends with resolve, red-replay of old packer layout fails sentinel, 5 tests plus real bundle layout check (P6-evidence/g1/bdd-11-pytest.log, P6-evidence/g1/bdd-09-10-11-16-offline-e2e.log)
- PASS BDD-12: old-format bundle rejected exit 1 with the required stderr, dest unchanged, 2/2 sub-scenarios in pytest plus real run against a genuinely old-layout bundle (P6-evidence/g1/bdd-12-pytest.log, P6-evidence/g1/bdd-12-16-legacy-and-release-offline.log)
- PASS BDD-13: release.yml static contract (only push tags v*, only contents: write, no secrets, zero third-party actions, asset names, manifest version) 14 tests PASSED; existing 4 workflows `git diff 75a8102..HEAD` empty (P6-evidence/g1/bdd-13-pytest.log, P6-evidence/g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-14: notes extraction 16 tests (formal tag exact section, missing section fail-closed with no output, real CHANGELOG v0.72.0, prerelease A/B fallback with first-line marker); real CI notes first line also correct (P6-evidence/g1/bdd-14-pytest.log, P6-evidence/g1/bdd-20-real-ci.md)
- PASS BDD-15: body tarball name / no wrapper dir / members == F_pkg / blob-byte equality / member safety, 45 tests PASSED at 043181d incl. the 5 T-17 hostile-member cases that FAILED on the real CI run at d6dd3cb (git 2.55) and now pass locally on git 2.43 after fix 895a10c (fix verified on 2.43 only; 2.55 behaviour argued, not observed; next PR CI run confirms); real CI asset re-checked: 155 members byte-equal to git blobs of d6dd3cb (P6-evidence/g1/bdd-15-pytest.log, P6-evidence/g1/bdd-15-hostile-members-ci-vs-fixed.md, P6-evidence/g1/bdd-20-real-ci.md)
- PASS BDD-16: offline tarball layout + manifest for both platforms (2/2) and bundle-internal install + resolve, 3 tests; real Release linux offline asset installed with pip shim, resolve exit 0, installed file set == body tarball set (P6-evidence/g1/bdd-16-pytest.log, P6-evidence/g1/bdd-12-16-legacy-and-release-offline.log)
- PASS BDD-17: real Release body tarball, PATH without git (asserted), UPGRADING portable commands run verbatim (only version substitution), adopt + resolve (AGATE_VERSION=v0.73.0) + summary + `--check --portable` all exit 0; 11 pytest PASSED (P6-evidence/g1/bdd-17-pytest.log, P6-evidence/g1/bdd-17-portable-real-tarball.log)
- PASS BDD-18: `--check --portable` without git exit 0, without pyyaml non-zero with guidance, default check without git exit 1, existing test_bdd_7/8 AST-identical to 75a8102 and PASSED, 5 tests (P6-evidence/g1/bdd-18-pytest.log, P6-evidence/g1/bdd-06-18-26-protected-tests.log)
- PASS BDD-19: no zero-dependency claim in the four docs and portable section declares python3 + pyyaml + no-git caveat, 5 tests PASSED (P6-evidence/g1/bdd-19-pytest.log)
- PASS BDD-20: scope per BASELINE_CHANGE (P1 annotation: item 4 cleanup is done manually by the user; P6 scope = items 1-3 + precise cleanup list; item 4 re-check at P8). Items 1-3 hold: run 35505427563 success (6/6 steps), prerelease + first-line marker + tag-verbatim asset names, 4 assets downloaded and `sha256sum -c` OK, body asset byte-identical to local build of d6dd3cb and to git blobs, offline manifest.version strictly v0.73.0 with components sha256 recomputed OK; cleanup list recorded; ④ re-check at P8 (P6-evidence/g1/bdd-20-real-ci.md, P6-evidence/g1/bdd-20-pytest.log, P6-evidence/g1/git-status.txt, P6-evidence/g1/results.md)
- PASS BDD-21: release checklist has post-push `gh release view` with 3-asset check, remediation for tag-pushed-but-Release-missing, G-5 includes Release existence, asset set matches builder, 4 tests PASSED (P6-evidence/g1/bdd-21-pytest.log)
- PASS BDD-22: online install (real `agate-install.py latest` from file:// worktree, v0.72.0) yields exactly the package set (153 files), no agate-workspace/docs/site/archived/.github/HANDOFF, root scripts synced, resolve OK; 5 pytest PASSED (P6-evidence/g1/bdd-22-pytest.log, P6-evidence/g1/bdd-22-23-online-real.log)
- PASS BDD-23: real repo measurement on isolated AGATE_HOME: S = 1,864,871 B (du -sb and file sum) vs B = 1,864,871 B (agate_package and independent oracle), S <= 1.25*B (limit 2,331,089), 94.8% below the 35.6MB whole-repo form; 3 pytest PASSED (P6-evidence/g1/bdd-23-pytest.log, P6-evidence/g1/bdd-22-23-online-real.log)
- PASS BDD-24: historical tags (no exclusion config / no NOTICES) get body only with pointers unchanged and pin resolves, malformed tag v0.1.0 fail-closed with no half install, 12 tests PASSED both sub-scenarios (P6-evidence/g1/bdd-24-pytest.log)
- PASS BDD-25: uninstall for new form with repo/, new form without repo/, old worktree form, plus reference protection and re-pointing, 6 tests PASSED all three sub-scenarios (P6-evidence/g1/bdd-25-pytest.log)
- PASS BDD-26: online reinstall idempotent and no source pollution (pytest + real second `latest` run "already installed, skipped", worktree status clean), install.sh rerun idempotent, existing tag0032 bdd_3/4/13/14 AST-identical and PASSED, 8 tests (P6-evidence/g1/bdd-26-pytest.log, P6-evidence/g1/bdd-22-23-online-real.log, P6-evidence/g1/bdd-06-18-26-protected-tests.log, P6-evidence/g1/git-status.txt)
- PASS BDD-27: agate-resolve.py 对软链 ~/.agate fail-closed：pytest 7 例（含 T-14 五变体）全过；真实调用 exit=1、stdout 无 AGATE_ROOT=、stderr 含三步片段、软链目标内容哈希不变 (P6-evidence/g2/bdd-27-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/cmd-scripts/cmdface.sh, P6-evidence/g2/cmd-scripts/run_bdd.py)
- PASS BDD-28: 解析链仅三层且无 use_legacy：pytest 8 例（a–e）全过；真实运行 (a)(e) AGATE_ROOT 覆盖 exit 0、(d) exit 1；inspect.signature 无 use_legacy、agate_common.py 无 realpath(base) (P6-evidence/g2/bdd-28-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/cmd-scripts/cmdface.sh)
- PASS BDD-29: install.sh 无参/--versions 进入版本布局：pytest 5 例全过；真实安装两入口 exit 0、~/.agate 为实体目录、含 repo/ latest/current/scripts、两版本根树相等、源 checkout git status 不变、install.sh 无 ln -s/LINK_NAME、未知参数 exit 2 (P6-evidence/g2/bdd-29-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/bdd-36-migration-walkthrough.log, P6-evidence/g2/cmd-scripts/cmdface.sh, P6-evidence/g2/cmd-scripts/bdd36.sh)
- PASS BDD-30: 废弃环境变量有明确处置：pytest 4 例全过；真实运行 exit 0、stderr WARNING、AGATE_SYMLINK/AGATE_REPO_DIR 指向路径均未创建、install.sh 除 WARNING 外不再引用 (P6-evidence/g2/bdd-30-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/cmd-scripts/cmdface.sh)
- PASS BDD-31: install.sh 软链 fail-closed：pytest 10 例（2 入口×5 变体）全过；真实调用 L L/ L// L/. L/.. 共 10 次均 exit 1、三步片段（L/.. 拒绝 .. 分量）、目标及物理父目录不变、git 调用 0 次 (P6-evidence/g2/bdd-31-pytest.log, P6-evidence/g2/bdd-31-32-33-real-invocation.log, P6-evidence/g2/cmd-scripts/symlink_guard.sh)
- PASS BDD-32: agate-install.py 软链 fail-closed：pytest 22 例（3 入口×5 变体 + --adopt×5 + 既有 tag0032_bdd_1/2）全过；真实调用 15 次均 exit 1、三步片段、目标不变、零 git 调用 (P6-evidence/g2/bdd-32-pytest.log, P6-evidence/g2/bdd-31-32-33-real-invocation.log, P6-evidence/g2/cmd-scripts/symlink_guard.sh)
- PASS BDD-33: install-offline.py 软链 fail-closed 且不误伤：pytest 12 例全过；真实调用 AGATE_HOME 与 --dest-root 各 5 变体共 10 次均 exit 1、目标不变；普通已存在/新建 dest-root exit 0 装出 vX.Y.Z/current/latest (P6-evidence/g2/bdd-33-pytest.log, P6-evidence/g2/bdd-31-32-33-real-invocation.log, P6-evidence/g2/cmd-scripts/symlink_guard.sh)
- PASS BDD-34: agate-summary.py 软链基址给迁移提示：pytest 1 例全过；真实运行 exit 0、AGATE_ROOT 行为无可用、含 mv ~/.agate ~/.agate.bak 提示、无 Traceback (P6-evidence/g2/bdd-34-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/cmd-scripts/cmdface.sh)
- PASS BDD-35: 迁移三步文案跨入口一致：pytest 4 例（bdd_35 ×2 + 保留并扩展的 debt0034 ×2）全过；真实 install.sh / agate-install.py / agate-resolve.py 输出同一三步文案 (P6-evidence/g2/bdd-35-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log)
- PASS BDD-36: 迁移三步隔离环境可走通：pytest 1 例全过；真实执行从 install.sh 拒绝文案提取的三步均 exit 0，结果满足 BDD-29 结构、agate-resolve exit 0、.agate.bak 原软链完好、改名回滚回到软链态 (P6-evidence/g2/bdd-36-pytest.log, P6-evidence/g2/bdd-36-migration-walkthrough.log, P6-evidence/g2/cmd-scripts/bdd36.sh, P6-evidence/g2/cmd-scripts/cmdface.sh)
- PASS BDD-37: 全仓旧称残留拦截：pytest 38 例全过；独立实扫基线 75a8102 命中 23 个文件（=P1 预期），HEAD 命中 8 个且全在白名单 W 内、R 集合 12 文件 0 命中、use_legacy 仅 tech-debt.md、原口径 grep 非白名单无残留 (P6-evidence/g2/bdd-37-pytest.log, P6-evidence/g2/bdd-37-scan.log, P6-evidence/g2/cmd-scripts/scan37.py)
- PASS BDD-38: 4 个 legacy 测试处置：pytest 6 例全过；ast 比对：撞名 test_bdd_30* 仅 test_bdd_30_legacy_symlink_direct_root 被改写、其余 5 个函数体逐一相同；test_tag0032_bdd_1/2 函数体相同；test_debt0042 已改写为 fail-closed；UPGRADING 对照表 ④ 由 UC/UL 用例覆盖 (P6-evidence/g2/bdd-38-pytest.log, P6-evidence/g2/bdd-38-ast-compare.log, P6-evidence/g2/cmd-scripts/ast38.py)
- PASS BDD-39: 文档面旧称改写完成：pytest 21 例（UC bdd_39 ①–⑤、DS ⑥–⑧、NLR 12 个 R 文件清零 ⑨）全过 (P6-evidence/g2/bdd-39-pytest.log, P6-evidence/g2/bdd-37-scan.log)
- PASS BDD-40: 协议根遗留路径改为解析出的根：pytest 5 例（DS 静态 3 + SD/SUM 动态 2）全过 (P6-evidence/g2/bdd-40-pytest.log)
- PASS BDD-41: SETUP 的 $AGATE_DIR 取值去 fallback：pytest 2 例全过；逐字执行 SETUP 首个 bash 块得 $HOME/.agate/current/agate 且模板可读、块内无 || echo fallback、current 缺失时明确失败提示 (P6-evidence/g2/bdd-41-pytest.log, P6-evidence/g2/bdd-41-45-real-setup-commands.log)
- PASS BDD-42: Claude Code 接入 agate 侧命令：pytest 1 例全过；逐字执行 SETUP Claude 块，链接可读、目标在隔离 AGATE_HOME 内、frontmatter yaml.safe_load 含 name: orchestrator；另 H-1 已执行一次见 h1-claude-orchestrator.log（非 BDD） (P6-evidence/g2/bdd-42-pytest.log, P6-evidence/g2/bdd-41-45-real-setup-commands.log, P6-evidence/g2/h1-claude-orchestrator.log, P6-evidence/g2/cmd-scripts/platforms.sh)
- PASS BDD-43: OpenCode 接入实跑：pytest 1 例全过（真实 opencode 在 PATH，未跳过）；逐字执行 SETUP OpenCode 块后 opencode debug agent orchestrator exit 0，JSON mode==primary、tools.task==true (P6-evidence/g2/bdd-43-pytest.log, P6-evidence/g2/bdd-41-45-real-setup-commands.log, P6-evidence/g2/cmd-scripts/platforms.sh)
- PASS BDD-44: DSH 接入命令实跑：pytest 1 例 + 既有 test_dsh_preset.py 9 例全过；逐字执行 SETUP DSH 块（跳过 install-hook 行），三链接均可读、agate-summary.py exit 0 且无漂移警告 (P6-evidence/g2/bdd-44-pytest.log, P6-evidence/g2/bdd-44-dsh-preset-pytest.log, P6-evidence/g2/bdd-41-45-real-setup-commands.log, P6-evidence/g2/cmd-scripts/platforms.sh)
- PASS BDD-45: Codex 接入实跑：pytest 1 例全过（真实 codex 在 PATH，未跳过）；模板可读，timeout 60s codex features list exit 0，multi_agent 行为 stable / true (P6-evidence/g2/bdd-45-pytest.log, P6-evidence/g2/bdd-41-45-real-setup-commands.log, P6-evidence/g2/cmd-scripts/platforms.sh)
- PASS BDD-46: out-of-scope 文件零 diff：P3 §7.5 命令 git diff --stat 75a8102..HEAD -- <清单> 输出为空（pathspec 命中 19 个受保护文件），resolve-entry.py 零 diff；OOS pytest 4 例全过 (P6-evidence/g2/bdd-46-git-diff.log, P6-evidence/g2/bdd-46-pytest.log, P6-evidence/g2/git-status.txt)
- PASS BDD-47: hook 解析路径不受影响：pytest 11 例（test_hook_resolve_entry.py 全部 + test_agate_root_self_locate_worktree + workspace-resolve bdd_47）全过 (P6-evidence/g2/bdd-47-pytest.log)
- PASS BDD-48: pytest 不减反增：CI 口径全量实跑 2292 passed / 0 failed / 2 skipped（skipped 为 Pillow 已安装的 2 个既有条件跳过，未超 2）≥ 基线 1842；count-tests 2294；AST 对账测试函数 1661→1896 净 +235，仅 3 个改名无净删（A−D≥0） (P6-evidence/g2/bdd-48-full-pytest.log, P6-evidence/g2/bdd-48-count-and-reconcile.log)
- PASS BDD-49: 收口：check-protocol-consistency --strict-errors-only exit 0（0 ERROR，CHECK 7/13 PASS）、ruff 0.16.4 All checks passed、shellcheck -S warning 4 文件 exit 0；④ 新脚本登记 scripts/README pytest 2 例全过 (P6-evidence/g2/bdd-49-commands.log, P6-evidence/g2/bdd-49-pytest.log)
- PASS BDD-50: 发布物就绪度（P6 验收范围=发布前就绪度（BASELINE_CHANGE），最终事实 P8 复验）：UPGRADING 存在 ### v0.73.0 节标注 BREAKING 与迁移三步；CHANGELOG [Unreleased] 含本任务条目、BREAKING 标注及 UPGRADING 指针；README badge 为 v0.72.0 非 1.0；release.yml 触发 on: push tags v* 与权限 contents: write 可如实列出；CHECK 7/13 通过；UC pytest 1 例全过 (P6-evidence/g2/bdd-50-readiness.log, P6-evidence/g2/bdd-50-pytest.log, P6-evidence/g2/bdd-49-commands.log, P6-evidence/g2/results.md)
- PASS BDD-51: 软链基址指向完整版本根：pytest 3 例全过；真实运行 resolve exit 0、REASON=全局 current、AGATE_ROOT 为目标内 vX.Y.Z/agate；agate-install.py latest exit 1 且 stderr 含三步及"解析仍可用"说明；summary 不打印迁移提示 (P6-evidence/g2/bdd-51-pytest.log, P6-evidence/g2/bdd-27-28-29-30-34-51-real-invocation.log, P6-evidence/g2/cmd-scripts/cmdface.sh)
- PASS BDD-52: 排除 agate/tests/ 后包内脚本冒烟无 Traceback：pytest 1 例全过（真实 HEAD 经 materialize 解包，四脚本两种调用形态） (P6-evidence/g2/bdd-52-pytest.log)

**Summary**: 52/52 PASS, 0 FAIL

## 交叉核对（g1 + g2 合集 vs P1 全部 BDD）

核对内容：两组 results.md 的 BDD 编号合集是否等于 1..52，无重复无遗漏；P1-requirements.md 中出现的 BDD 编号集合是否也等于 1..52。命令（工作目录为任务目录）与输出如下。

命令 1：列出合集编号（升序）

```
grep -hoE '^- (PASS|FAIL) BDD-[0-9]+' P6-evidence/g1/results.md P6-evidence/g2/results.md | grep -oE '[0-9]+$' | sort -n | tr '\n' ' '
```
输出：`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52`

命令 2：重复编号个数

```
grep -hoE '^- (PASS|FAIL) BDD-[0-9]+' P6-evidence/g1/results.md P6-evidence/g2/results.md | grep -oE '[0-9]+$' | sort -n | uniq -d | wc -l
```
输出：`0`

命令 3：合集与 seq 1 52 逐行 diff

```
diff <(grep -hoE '^- (PASS|FAIL) BDD-[0-9]+' P6-evidence/g1/results.md P6-evidence/g2/results.md | grep -oE '[0-9]+$' | sort -n) <(seq 1 52) && echo IDENTICAL_1_to_52
```
输出：`IDENTICAL_1_to_52`

命令 4：P1 BDD 编号集合与 seq 1 52 逐行 diff

```
grep -oE 'BDD-[0-9]+' P1-requirements.md | grep -oE '[0-9]+$' | sort -n -u | diff - <(seq 1 52) && echo P1_BDD_SET_EQ_1_to_52
```
输出：`P1_BDD_SET_EQ_1_to_52`

结论：g1 覆盖 BDD-1..26（26 条），g2 覆盖 BDD-27..52（26 条），合集 = 1..52 共 52 条，无重复、无遗漏，且与 P1 BDD 总数一致（52）。两组 results.md 各自的总结行均为 `26 PASS, 0 FAIL`，合并为 52 PASS, 0 FAIL，与本文件 frontmatter 一致。所有 PASS 行引用的证据路径均已确认真实存在且非空（转抄脚本逐个 `os.path.isfile` + 大小 > 0 检查，缺失数 0）。

## 环境残留检查（post-test，强制步骤）

两组的开始/结束 `git status --short` 对比见 `P6-evidence/g1/git-status.txt` 与 `P6-evidence/g2/git-status.txt`，此处转抄要点。

- g1：首轮 START 与 END 输出相同；在 HEAD 043181d 重验后的 END 输出与基线相比，`.state.yaml` 已不再显示为修改（已由 P5 提交 043181d 落库），新增的唯一跟踪文件改动为 `P1-requirements.md`（仅在 BDD-20 增加 `[BASELINE_CHANGE]` 注记，2 行插入，Given/When/Then 未改动，经主 Agent 授权）。`agate/`、`.github/`、`site/`、`docs/`、`README*` 无任何改动（g1 的 DIFF ANALYSIS 检查输出为空）。本地无 `v0.73.0*` tag，未推送，未删除任何 GitHub tag/Release。
- g2：START 与 END 的 `git status --short` 输出逐行相同（`P1-requirements.md`、`gate-events.jsonl` 为修改，其余为 P6 派发文件、`P6-evidence/`、`P6-progress.md` 未跟踪）；相对 START 仅 `P1-requirements.md` 有差异（BDD-50 的 `[BASELINE_CHANGE]` 注记，4 行插入，经主 Agent 授权），此外无任何项目文件改动。
- 仓库内无任何未授权残留：除 `P6-evidence/`、`P6-progress.md`、P6 派发文件、两处经授权的 P1 注记与主 Agent 既有的 `gate-events.jsonl` 之外，无新增或修改文件。
- scratchpad 新建目录清单（本次 P6 验收，位于 `/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/`，均为带序号的新建目录，未删除任何既有内容）：
  - g1：`g1-01`、`g1-02-release`、`g1-03-portable`、`g1-04-offline`、`g1-05-legacy`、`g1-06-online`、`g1-07`
  - g2：`g2-01`、`g2-02`、`g2-03`、`g2-04`、`g2-05`、`g2-06`、`g2-07`、`g2-08`
  - 汇总（本 verifier）：`merge-01`（仅存放转抄脚本）
- 真实 `~/.agate`、开发 checkout（`/home/kity/oclab/agateon`）、git 分支与 tag 均未触碰；所有安装/打包验证均使用隔离 `AGATE_HOME` / `--dest-root`。上述 scratchpad 目录属于临时验证产物，未作清理（P6 规则禁止删除）。

## 已知遗留 / 待用户手动清理事项

1. 远端测试 tag `v0.73.0-tagtest.1`（`refs/tags/v0.73.0-tagtest.1` -> d6dd3cb007a414f7dd5011c4031aa44326335a00）及其预发布 GitHub Release `v0.73.0-tagtest.1`（4 个资产：`agateon-v0.73.0-tagtest.1.tar.gz`、`agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz`、`agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz`、`SHA256SUMS`）。用户已选择手动清理，verifier 未删除任何 tag/Release。参考命令：`gh -R randomgitsrc/agateon release delete v0.73.0-tagtest.1 --cleanup-tag --yes`。本地不存在该 tag（`git tag -l 'v0.73.0*'` 为空；`git describe --tags --abbrev=0` = `v0.72.0`）。
2. BDD-20 的 Then 第 4 项（清理）按 P1 的 `[BASELINE_CHANGE]` 注记由用户手动完成，本轮 P6 范围为第 1-3 项 + 精确清理清单，第 4 项在 P8 复验，尚未满足；BDD-20 的 PASS 不代表第 4 项已满足。P8 只读复验清单：`gh release list` 不含该 tag；`git ls-remote --tags origin v0.73.0-tagtest.1` 为空；`git tag -l 'v0.73.0*'` 为空；`git describe --tags --abbrev=0` = `v0.72.0`。详见 `P6-evidence/g1/bdd-20-real-ci.md`。
3. BDD-50（发布物就绪度）的 P6 验收范围为发布前就绪度（按 `[BASELINE_CHANGE]` 注记），最终事实（README badge、UPGRADING/CHANGELOG 随 v0.73.0 正式发布的状态、release.yml 实际产出）在 P8 复验。
4. 该 tag 推送触发的链式 workflow 结果（供 PR 描述引用）：Release 35505427563 成功；Site Check 35505427551 成功；Docs Check 35505427522 失败；Protocol Tests 35505427554 失败（10 failed / 2276 passed / 8 skipped）。根因 1 为 tag 引发的 CHECK 7（`README version badge v0.72.0 != latest tag v0.73.0-tagtest.1`，tag 删除后消失）；根因 2 为 T-17 恶意成员用例夹具在 git 2.55 下被 `fast-import` 拒绝，已由 895a10c 修复，仅在 git 2.43 上验证，git 2.55 行为为推断而非实测，需下一次 PR CI 运行确认（见 BDD-15 与 `P6-evidence/g1/bdd-15-hostile-members-ci-vs-fixed.md`）。
5. `actionlint` 在本机未安装，BDD-13 的静态契约依赖 yaml 基础测试与真实成功的 CI 运行。
6. H-1（非 BDD，不计入总数）：g2 已执行一次 `claude --agent orchestrator -p "echo test"`，见 `P6-evidence/g2/h1-claude-orchestrator.log`。
