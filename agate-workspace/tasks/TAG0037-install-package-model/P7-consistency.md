---
phase: P7
task_id: TAG0037
type: consistency
parent: P2-design.md
trace_id: TAG0037-P7-20260920
created: '2026-09-20'
agent: consistency-reviewer
status: approved
blocker_count: 0
deviation_count: 5
deviation_critical_count: 0
design_gap_count: 5
design_gap_reviewed_count: 5
code_map_new_files_count: 4
code_map_reviewed_count: 4
---
# P7 一致性审查 — TAG0037 安装与多版本模型统一（RM-AG0066）

[PROD_NOT_TOUCHED]

> 审查基线：HEAD 2f1fc79（P1–P6.5 提交链 3708db9 → 2f1fc79；代码/脚本/发布文档自真实 CI 提交 d6dd3cb、修复批 895a10c 后未再变，`git diff 895a10c..HEAD -- agate .github install.sh README.md CHANGELOG.md AGENTS.md` 为空）。
> 方法：只读审查；实验仅在 scratchpad `p7-01`（`PYTHONDONTWRITEBYTECODE=1`、`timeout`）；除本文件与 `P7-progress.md` 追加外未改任何仓库文件，未 git add/commit/push/tag，未触碰 `~/.agate`、开发 checkout 与 GitHub。
> 项目约定文件：派发 prompt 中 `{project_conventions_file}` 为未替换占位符，本次以仓库根 `AGENTS.md`（CLAUDE.md 指定的权威开发指南）代之；P0-brief 环境约束（隔离 `AGATE_HOME`、不动真实 `~/.agate`）已遵守。

## 0. 结论摘要

- BLOCKER 0；DEVIATION-CRITICAL 0；DEVIATION 5（均非阻断，均可在 P8 前后收尾，见 §6）；DESIGN_GAP 5 条（P4 声明 4 条 + P3 的 B1 共 1 条）全部配对 REVIEWED；SCOPE+ 无（P1 无 SCOPE+，P2 无 SCOPE+ 标记，升级自举缺口按主 Agent 裁决降为文档，实况核对属实）；CODE_MAP_DRIFT 2 条（WARNING，P8 待办）。
- 数量口径：P1 BDD 52 = P6 验收 52 = P6.5 judge 52/52（`criteria_total: 52`、`criteria_passed: 52`），编号集合逐一相等，抽查 10 条 BDD 的 P6 证据与 Then 无错位（§3.1）。
- 兼容红线实测成立：`_protocol_root` 两份实现函数体相对基线 75a8102 AST 字节相同；`resolve_hook_root` 兜底保留；out-of-scope 文件（hook 三件套 / SELF-GATE / 4 个既有 workflow / `agate/rules/` / `install-hook.py` / `resolve-entry.py`）`git diff 75a8102..HEAD` 为空。
- 事件账本审计：`python3 -B agate/scripts/check-events.py <任务目录>` 输出「账本审计通过（20 行，哈希链完整，ts 单调，judge 轮次×1）」。

## 1. DESIGN_GAP 配对（gate 硬校验：转抄 + REVIEWED）

P4 的 4 条来自 `P4-implementation.md`（批 A 三条、批 B2 一条），评审裁定见 `P4-review.md` §2 与 `P4-review-code.md` §4、`P4-review-cso.md`（review 与 cso 均 approved，四项一致接受）。P3 的 B1 来自 `P3-test-cases.md` §6.5 与 §8.2(a)。

[DESIGN_GAP: P2 §3.2 未指定 discard_backup 拒绝路径的表现形式，实现为返回 False 并向 stderr 打印警告（不抛异常，避免 adopt 成功后的清理步骤崩溃），测试接受异常或忽略两种]
[DESIGN_GAP_REVIEWED: P4§批A-package-lib 第 1 条——P4 review 与 cso 均接受（P4-review.md §2 第 1 行：review「adopt 成功后的清理不应使已成功安装报错；目录原样保留（宁留不删）」，cso「实测对用户预置同名带标记目录返回 False 并警告，目录与内容保留」）；本次核对代码：`agate_package.discard_backup` 拒绝分支返回 False + stderr、`install-offline.py` 成功路径调用它，与 P2 D-6「成功后才删备份、只删本进程创建的备份容器」同向；数据安全方向为"宁留不删"，无误删面。可接受，无需回派]

[DESIGN_GAP: P2 §3.2 未指定 rollback_swap 对「新目录」的处置，实现为将其移入备份容器 failed-new/ 后删除（属本进程刚创建，且要求无遗留容器）；仅在备份容器为本进程创建且标记有效时才回滚]
[DESIGN_GAP_REVIEWED: P4§批A-package-lib 第 2 条——review 接受并附加固建议 M-3（无备份分支缺来源校验，非阻塞、入 backlog），cso 判定「带备份分支三重限定，无备份分支仅对本进程刚换位目录调用，并有真实目录校验；实测旧目录内容还原、备份容器清除」（P4-review.md §2 第 2 行）。与 P2 D-6 / R-15「任何时刻旧版完整或新版完整、指针与目录一致」同向；测试 T-16 / T-23 覆盖（P5 全量 2292 passed）。可接受]

[DESIGN_GAP: P2 §3.2 `make_work_dir` 未指定根目录不存在时的行为，实现为 `os.makedirs(root, exist_ok=True)`（离线安装到全新 --dest-root 需要）；软链基址守卫由调用方入口负责]
[DESIGN_GAP_REVIEWED: P4§批A-package-lib 第 3 条——review「离线安装到全新 --dest-root 所需；软链守卫在所有入口先于它；失败路径仅 os.rmdir 回收本次新建的空根」，cso「失败分支仅 rmdir 刚 mkdtemp 的空容器；bundle 校验失败时 dest 根目录未被创建」（P4-review.md §2 第 3 行）。与 P1 BDD-33（`--dest-root` 指向不存在的新目录不误伤）与 BDD-12（旧 bundle 拒绝时 `<tmp>` 不产生半装目录）一致，P6 BDD-12 / BDD-33 证据（`g1/bdd-12-pytest.log` 8 passed、`g2/bdd-33-pytest.log` 12 passed）实测成立。可接受]

[DESIGN_GAP: P2 §3.4 未指定 pack 输出目录已存在时的行为，实现为拒绝覆盖并报错（数据安全：不清空 / 不删除既有内容）；每次打包需使用新的 `--outdir` 或先自行移走旧 bundle]
[DESIGN_GAP_REVIEWED: P4§批B2-offline-pack-install——review「同一 --outdir 二次打包 exit 1；agate-release build 每平台用全新 pack 目录，CI 与本地补救不受影响」，cso「拒绝覆盖而非清空重建，无误删面」（P4-review.md §2 第 4 行）。P5 release 构建冒烟与 P6 BDD-20 真实 CI（run 35505427563 success，6/6 步骤）证明 build 链路不受影响。可接受；review I-2 要求把该行为收紧补记进 CHANGELOG，见 §6 DEVIATION-3 与 §7 P8 待办]

[DESIGN_GAP: B1 P3 阶段——P2 §6 T-10 / P1 BDD-26 称既有 TAG0008 用例 test_bdd_2 / test_bdd_3 / test_bdd_6 函数体不改且保持通过，但这三条断言旧 git worktree 形态（版本目录登记在 repo/ worktree list、HEAD == tag 提交、恰出现 1 次、拒绝卸载后仍登记），与新契约（D-1 git plumbing 构建器取代 git worktree add；BDD-22 只装本体）直接矛盾；P3 仅替换过时的 worktree 断言为新形态等价判据，test_bdd_2 改名为 test_bdd_2_version_dir_is_tag_body_not_worktree]
[DESIGN_GAP_REVIEWED: P3§8.2(a)——主 Agent 已采纳为对 P2 T-10 的合法例外（"接受，非弱化断言"，且要求 P7 配对 REVIEWED）；本次核对 `git diff 75a8102..HEAD -- agate/tests/unit/test_agate_version_install.py`：test_bdd_2 改名并改判据（非 worktree、无 .git、内容取自 tag blob）、test_bdd_3 与 test_bdd_6 仅替换末尾 `_worktree_porcelain` 断言为"版本目录快照逐字节不变"，其余语句与前半断言逐字保留（diff 三处 hunk 印证）；旧断言与新契约不可兼容属实，P6 BDD-26（`g1/bdd-26-pytest.log`）与 BDD-25 通过。可接受。另注：P3-test-cases.md 中仍有指向旧名的陈旧引用，见 §6 DEVIATION-2]

说明：P3 §7.9 的 G-1（BDD-43/45 CI 例外）在行内自标过「[DESIGN_GAP]」字样，但已由 P3§8.2(b) 裁决为 `[BASELINE_CHANGE]` 注解并回写 P1，不属需 P7 补配对的 DESIGN_GAP 条目（派发指引只点名 B1）；其三处口径核对见 §3.4，未计入 design_gap_count。

计数：design_gap_count = 5（P4 声明 4 + P3 B1 1），design_gap_reviewed_count = 5，逐条配对，无缺口；P4 行首 `[DESIGN_GAP:` 实际计数 4，P7 转抄 5 ≥ 4，通过 gate 的 P4/P7 交叉核对。

## 2. SCOPE+ 闭环

- P1：无 SCOPE+。`P1-requirements.md` §9 明写「无 `[SCOPE+]`」，§5 扫描 I 明确「不写 `[SCOPE+]`——未越界，仅未做」；全文 grep 行首 `[SCOPE+`、`[SCOPE_RESOLVED` 均无命中。故无需 `[SCOPE_RESOLVED]`，闭环成立。
- P2：文件中不含字面 `[SCOPE+` 标记（grep `SCOPE` 无命中，与派发指引「P2 [SCOPE+]（升级自举缺口）」的称呼略有出入）。该缺口实以 P2§1.3 R-1、§3.3 末条、§3.8、§3.9、§13「升级自举缺口」记载为「主 Agent 裁决：不做代码改动，仅文档化 + backlog」。实况核对：
  - `install.sh` 无 `git pull` / `git fetch`（`grep -n 'git pull\|git fetch' install.sh` 无命中；`repo/` 已存在时不更新，与 P2 D-9 一致）；
  - `agate/UPGRADING.md` `### v0.73.0` 第 7 条「升级说明（两步升级，仅文档）」如实记载旧安装器装出旧整仓形态、之后经同步后的根 `scripts/` 才只装本体；第 8 条记载钉老版本回退根 scripts 的副作用（eng m-5）；
  - `CHANGELOG.md [Unreleased]` 也写「两步升级说明」；P2§13 backlog 建议（install.sh 重跑拉 repo/、`_sync_root_scripts` 条件同步等）为后续立项，未有残留半实现代码。
  结论：缺口如实文档化，无半实现残留。

## 3. 跨文件一致性核对（源文件节名锚点 + 实测证据）

### 3.1 P1 BDD 数量与内容映射（P1 BDD ↔ P6 ↔ P6.5）

- 数量：P1 BDD 编号集合 = 1..52（`P6-acceptance.md` 交叉核对命令 4 输出 `P1_BDD_SET_EQ_1_to_52`，本次复核 P1 正文 `#### BDD-1` … `#### BDD-52` 共 52 个小节）；`P6-acceptance.md` frontmatter `pass: 52` / `fail: 0`；`P6.5-judge-verdict.md` frontmatter `criteria_total: 52`、`criteria_passed: 52`、`status: passed`、`partial: false`；`gate-events.jsonl` 的 `judge_verdict` 事件 `criteria_passed:52,criteria_total:52`，三条事件 `verdict_hash` 相同（同一 verdict 重跑不增轮，账本审计通过）。
- 内容映射抽查（逐条读 P6 证据日志尾行 pytest 汇总，与 P1 Then 对照，无错位）：

| BDD | P1 Then 要点（P1§4.x） | P6 证据实测 | 判定 |
|-----|------------------------|-------------|------|
| BDD-9（P1§4.2） | 真实 pack → 离线安装 → resolve exit 0、无 `agate/agate/` 双层 | `g1/bdd-09-pytest.log` 25 passed（含 `test_bdd_9_no_double_nesting_and_protocol_root_not_returned_verbatim`、真实树冒烟 t15），`EXIT_CODE: 0` | 对应 |
| BDD-12（P1§4.2） | 旧格式 bundle exit 1 + 指定 stderr、目标无半装目录 | `g1/bdd-12-pytest.log` 8 passed（`test_bdd_12_old_format_bundle_rejected_and_nothing_written` 两子场景 + T19/T6）；代码 `install-offline.py:243-244` 文案与 BDD-12 要求逐字对应 | 对应 |
| BDD-13（P1§4.3） | release.yml 触发 / 权限 / 零第三方 action / 资产名 | `g1/bdd-13-pytest.log` 14 passed（13_3 无 secrets、13_4 零第三方 action、13_6 既有 workflow 不变、`test_bdd_13_5_*`）；本次读 `.github/workflows/release.yml`：`on.push.tags: ['v*']`、`permissions: contents: write`、无 `uses:`/`workflow_dispatch`/`pull_request` | 对应 |
| BDD-17（P1§4.3） | 无 git PATH 上按 UPGRADING 命令逐条实跑 | `g1/bdd-17-pytest.log` 11 passed（`test_bdd_17_test_path_really_has_no_git` 先断言无 git，再跑文档命令）；UPGRADING.md:125-134 命令块与 P2§3.5 草案逐行一致 | 对应 |
| BDD-23（P1§4.4） | S ≤ 1.25×B，B = 1,864,871 B | `g1/bdd-23-pytest.log` 3 passed；`g1/bdd-22-23-online-real.log`（v0.72.0 真实在线安装）记 S=B=1,864,871 B（153 文件），与 P5 `checks.md`「成员未压缩字节合计 1864871」及 P2 R-12 一致 | 对应 |
| BDD-27（P1§4.5） | 软链基址 resolve exit 1、stdout 无 `AGATE_ROOT=`、三步文案 | `g2/bdd-27-pytest.log` 7 passed（含 T-14 五变体 L / L/ L// L/. L/..）；代码 `agate-resolve.py:40-41` 追加 `symlink_migration_hint()` 后 `sys.exit(1)` | 对应 |
| BDD-46（P1§4.5） | out-of-scope 文件零 diff | `g2/bdd-46-git-diff.log` 空输出且 `git ls-files` 证明 pathspec 命中 19 个真实文件；本次独立复跑同类 `git diff --stat 75a8102..HEAD -- <hook 三件套 / SELF-GATE / rules / 4 workflow / install-hook / resolve-entry>` 输出为空 | 对应 |
| BDD-48（P1§4.6） | 失败 0、passed ≥ 1842、skipped ≤ 2、A−D ≥ 0 | `g2/bdd-48-full-pytest.log` 尾行「2292 passed, 2 skipped in 56.14s」；`bdd-48-count-and-reconcile.log`：D=12、A=247、A−D=235，AST 函数数 1661→1896 净 +235，count-tests 2294；P5 `unit.md` 同为 2292 passed / 2 skipped | 对应 |
| BDD-51（P1§4.6.1） | 软链→完整版本根：resolve 放行、install 拒绝 | `g2/bdd-51-pytest.log` 3 passed（`..._resolves_via_current_chain`、`..._prints_no_migration_hint`、`..._refused_with_resolution_note`）；与 P2§3.7「同一代码路径的三种输入」设计吻合（`agate_common.py` 无软链特判分支，仅返回 `symlink_base`） | 对应 |
| BDD-52（P1§4.6.1） | 缺 `agate/tests/` 的包内四脚本冒烟无 Traceback | `g2/bdd-52-pytest.log` 1 passed（`test_bdd_52_scripts_inside_the_body_package_without_agate_tests_have_no_traceback`）；本次独立实测 HEAD 包集合 155 文件、顶层 {CHANGELOG.md, LICENSE, NOTICES.md, agate}、无 `agate/tests` | 对应 |

另核：BDD-1/2/3 的文档块与来源——独立实验（scratchpad `p7-01`）取 `python3 -B agate/scripts/agate-release.py boundary` 输出与 UPGRADING.md「版本目录结构契约」小节 fenced 块逐行比较：相等（8 行）；小节 grep `可配置|可扩展|manifest 声明` 无命中，与 P1 BDD-1 (c)、BDD-3 ③ 一致。

### 3.2 P2 `packages` ↔ P4 实际改动面 ↔ P8 bump 范围

P2 frontmatter `packages`：agate-scripts、agate-docs、agate-tests、ci-workflows、install-sh（与 P1 frontmatter 相同）。`git diff 75a8102..HEAD --name-only` 归类（排除任务目录 152 个工作流产物文件）：

| package | 实际文件数 | 内容 |
|---------|-----------|------|
| agate-scripts | 8 | 新增 `agate_package.py`、`agate-release.py`；改 `agate-install.py`、`agate-pack-offline.py`、`install-offline.py`、`agate_common.py`、`agate-resolve.py`、`agate-summary.py` |
| install-sh | 1 | `install.sh` |
| ci-workflows | 1 | 新增 `.github/workflows/release.yml`（现有 4 个 workflow 零 diff） |
| agate-tests | 29 | 新增 15 个测试/助手文件（含 `helpers_tag_repo.py`）+ 改 14 个既有测试文件 |
| agate-docs | 16 | AGENTS.md、CHANGELOG.md、README×2、agate/{AGENTS,CONTEXT,SETUP,UPGRADING,WORKFLOW,adr,orchestrator-template,platform-notes}.md、agate/assets/templates/handoff-template.md、agate/scripts/README.md、docs/guides×2 |
| 其它 | 1 | `agate-workspace/tasks/active-tasks.md`（看板 TAG0037 行阶段 P0→P6，任务流程常规更新，非包内容） |

无任何包外改动（`site/`、`archived/`、`pyproject.toml`、`SELF-GATE.md` 均无 diff）；与 P2§1.1 Modify 表、P2§1.2 Not Modify 表逐项吻合。P8 将 bump 的范围：`README.md` badge（当前 v0.72.0，`README.md:12`）、`CHANGELOG.md`（`[Unreleased]` → `[0.73.0]`，当前 `CHANGELOG.md:11` 仍为 `[Unreleased]`）、`agate/UPGRADING.md` 的 `### v0.73.0` 节（已存在，`UPGRADING.md:279`），三者与根 `AGENTS.md`「版本发布清单」第 2/3 项及「版本引用文件清单」（README badge / CHANGELOG / UPGRADING 章节 / 稳定版引用）一致，均落在 agate-docs 包；P8 的 tag/Release 步骤对应 ci-workflows 包。范围一致。

### 3.3 P2§5 批次表 ↔ P4 各批小节 ↔ 实际文件

P2§5 九批与 P4-implementation.md 小节一一对应：A-package-lib（`agate_package.py`）、B1a（`agate-install.py`）、E（`agate_common.py`/`agate-resolve.py`/`agate-summary.py`/`install.sh`）、B1b（`agate-install.py` 的 `--adopt`/`--check --portable`）、B2（`agate-pack-offline.py`/`install-offline.py`）、C1（`agate-release.py`）、C2（`release.yml`）、F1a（`UPGRADING.md`/`CHANGELOG.md`）、F2（README/SETUP/AGENTS 等文档）。P4 各批"改动文件清单"与 `git diff --name-status` 逐项吻合（新增 A 的 18 项 = 3 个生产文件 + 15 个测试/助手；文档批仅文档面）。P2 §5 的执行顺序 A → (B1a ∥ E) → B1b → B2 → C1 → C2 → (F1a ∥ F2) 与 P4 小节顺序一致。

P4 修复批 `t17-fixture-fix`（commit 895a10c）与 P2/P5 的关系：
- 它不在 P2 dispatch_plan 九批内（P2 frontmatter 只有 9 批），属 P5 首轮后经真实 CI（tag 推送连带触发的 Protocol Tests，git 2.55 拒绝 `fast-import` 危险路径）暴露的夹具缺陷之修复批；记载于 `P4-implementation.md` §修复批 t17-fixture-fix、`P6-acceptance.md`「已知遗留」第 4 条、`P6-evidence/g1/bdd-15-hostile-members-ci-vs-fixed.md`。
- 改动仅 `agate/tests/helpers_tag_repo.py`（+77/−1，`git diff d6dd3cb..HEAD --stat -- agate` 唯一文件）；`agate_package.py` 与断言未改；`git diff d6dd3cb..HEAD -- agate/scripts .github install.sh` 为空（真实 CI 运行所用的产品脚本与 release.yml 自 d6dd3cb 起未变）。
- P5 重跑（commit 043181d，`P5-test-results/unit.md`「HEAD 895a10c，重跑 #1」）：2292 passed / 2 skipped，各 gate 全绿；`.state.yaml` 的 `p5_pass_commit: 895a10c5b31a26b66bef12c8d8a098142e0999d9` 指向修复后提交（043181d 版 `.state.yaml` 已核对；首轮 d6dd3cb 时为 467fec7），P6 在 043181d 上验收（该提交相对 895a10c 仅增 P5 产出文件）。一致。
- 遗留：修复只在 git 2.43 上观察通过，git 2.55 行为为推断，需 PR CI 确认（P6.5 裁判备注 2 同）。

### 3.4 `[BASELINE_CHANGE]` 三处口径（P1 ↔ P6 ↔ P3§8.2）

| 注记 | P1 位置 | P6 对应条目 | P3 对应 | 与 BDD 正文关系 |
|------|---------|-------------|---------|-----------------|
| BDD-20 ④（清理由用户手动，P6 范围 = ①②③ + 精确清理清单，④ 于 P8 复核） | `P1-requirements.md` BDD-20 后注记 | `P6-acceptance.md` BDD-20 与「已知遗留」第 2 条：明说"BDD-20 的 PASS 不代表第 4 项已满足"，P8 只读复验四命令与 P1 注记一致；`P6.5-judge-verdict.md` 备注 1 同 | P3 §1 / §7.5 已把真实 CI 实跑列为 P5/P6 人工验收；P3§8.2 无记录（该注记形成于 P6，晚于 P3 收尾），属时序合理 | 注记明示"仅注解，不改 Given/When/Then"；正文 Then ④ 仍写"清理后…零污染"——P6 以范围口径判 PASS 而 Then ④ 实际未满足，冲突由注记 + P8 复验兜住，见 §4 未决项与 §6 说明 |
| BDD-43/45 的 G-1（GITHUB_ACTIONS=true 且缺 CLI 才 skip；本地/P5/P6 缺 CLI 仍 FAIL） | `P1-requirements.md` BDD-43 与 BDD-45 后注记 | `P6-acceptance.md` BDD-43/45：真实 opencode/codex 在 PATH、未跳过、`opencode debug agent orchestrator` exit 0、`codex features list` multi_agent 行 stable/true | `P3-test-cases.md` §8.2(b)「G-1 已采纳」；§7.9 提出、§8.1 总表指向 §8.2(b) | 三处口径一致，且 BDD 正文"缺 CLI → FAIL"在 P6 环境（CLI 在 PATH）下按原意成立，无冲突 |
| BDD-50 P6 范围 = 发布前就绪度 | `P1-requirements.md` BDD-50 后注记 | `P6-acceptance.md` BDD-50：UPGRADING v0.73.0 节、CHANGELOG [Unreleased] BREAKING 条目、README badge v0.72.0 非 1.0、release.yml 触发/权限；②–⑥ 留 P8 | `P3-test-cases.md` §7.3 表与 §7.5 第 50 行已写「①（UC）；②–⑥ P8 命令/人工」 | 三处一致；本次复核 UPGRADING.md:279-294、CHANGELOG.md:11-32、README.md:12 三项静态事实成立 |

### 3.5 P1 §7 SUGGEST 采纳（S-1…S-19）↔ P2 设计决策 ↔ 实现（抽查 6 项）

| SUGGEST | P2 落点 | 实现实测 |
|---------|---------|----------|
| S-1 tests 排除 | P2§3.1 `exclude agate/tests/`、D-16 casefold | 独立 `list_package(HEAD)`：155 文件，无 `agate/tests` 路径；UPGRADING 契约块 `exclude agate/tests/`；`agate/AGENTS.md`/`CONTEXT.md` 已加"仅仓库开发者可用"注记（P4§批F2） |
| S-3 / S-4 顶层文件入包 | P2§3.1 登记根文件 CHANGELOG/LICENSE/NOTICES | HEAD 包顶层集合 = {CHANGELOG.md, LICENSE, NOTICES.md, agate}；`verify_dir` 常量 `TOP_LEVEL` 同源 |
| S-13 旧 bundle 拒绝 | P2§3.4 步骤 3 | `install-offline.py:243-244` 文案「bundle 为旧格式（`agate/agate/scripts` 双层嵌套），请用新版 `agate-pack-offline.py` 重新打包」；`g1/bdd-12-pytest.log` 通过 |
| S-15 fail-closed exit 1 | P2§3.7 | `agate-resolve.py:27,41` `sys.exit(1)`；`install.sh` 软链拒绝 `exit 1`、参数错误 `exit 2` |
| S-10 workflow 零第三方 action | P2 D-10 / §3.6 | `release.yml` 无 `uses:`，仅 `run:` + `gh release create --verify-tag`；`test_release_workflow.py` 14 项通过 |
| S-12 / S-14 / S-17 | D-12 / D-9 / §1.2 | `agate-install.py --check --portable`（`_cmd_check(portable)`）；`install.sh:17-19` 废弃 env WARNING；`agate_common.resolve_hook_root` 仅去 `use_legacy` 实参，脚本上溯 + `.agate-root` 兜底保留 |

### 3.6 文档 ↔ 实现

- UPGRADING v0.73.0 节 ↔ 脚本行为：迁移三步文案与 `install.sh` heredoc、`agate_common.symlink_migration_hint()`、`agate-install.py` 常量同源（P6 BDD-35 `g2/bdd-35-pytest.log` 4 passed 跨入口比对通过）；`install.sh` 无参 = `--versions` 别名、其余参数 exit 2（`install.sh:22-24`）；废弃 env WARNING（`install.sh:17-19`）；退出码 fail-closed = 1（S-15）；`AGATE_REPO_DIR`/`AGATE_SYMLINK` 除 WARNING 与文档外无活跃引用（`git grep` 仅命中 install.sh、UPGRADING、测试断言）；`use_legacy` 仅剩 `agate-workspace/debt/tech-debt.md` 已关闭债务叙事。
- `CHANGELOG.md [Unreleased]`：BREAKING / 新增 / 变更三节与实际改动主线一致（legacy 删除、install.sh 语义、契约、三路径同构、`--adopt`/`--check --portable`、Release 流水线、`compute_sha256` 字节码忽略）。遗漏项见 §6 DEVIATION-3。
- `agate/scripts/README.md` 登记：新增 `agate_package.py`、`agate-release.py` 两行已登记（BDD-49 ④，`g2/bdd-49-pytest.log` 通过）；但同表 `agate-install.py`/`agate-pack-offline.py`/`install-offline.py` 三行仍写旧机制，见 §6 DEVIATION-1。
- README / SETUP 的 `$AGATE_DIR` ↔ 实际解析链：SETUP.md「先取协议根路径」块 `AGATE_DIR="$HOME/.agate/current/agate"`（去 fallback，`current` 缺失明确失败提示，P1 BDD-41、P2§3.8 指定）；`agate_common._resolve_version_info` / `agate-resolve.py` 的实际解析链为 `AGATE_ROOT` env → `AGATE_HOME`/项目 `.agate-version` → `current`。SETUP 的取值只对应第三层（`current`），未反映 `AGATE_HOME`/钉版；属设计与 BDD-41 明确选择的简化，非缺陷，见 §6 INFO-1。README 首推 `curl | bash` 描述与 `install.sh` 实际行为（进入版本布局、软链 fail-closed）一致。
- UPGRADING「路径层次与解析优先级」：`③ 解析优先级（三层）` 表实为 4 行（AGATE_ROOT / AGATE_HOME / 项目声明 / current，前两行同属 env 层），与 P1 BDD-39 ②「表无第 5 行、口径三层」一致；`### v0.73.0` 第 2 条「由五层改三层」以旧表行数对新层数，计数口径不一，见 §6 INFO-2。
- 已装旧形态解析、`_protocol_root` 探测序在 UPGRADING.md:166 的描述与 `agate_common._protocol_root` 真实语义（`vdir/scripts` 优先，其次 `vdir/agate/scripts`）吻合（P1 扫描 G 要求订正的 `:103` 旧错句已改）。

### 3.7 兼容红线

- `_protocol_root` 函数体零 diff：独立 AST 比对（`ast.get_source_segment`），`agate_common._protocol_root` 相对 75a8102 = identical（494 字符）；`agate-install.py` 内降级副本 = identical。`git diff 75a8102..HEAD -- agate/scripts/agate_common.py` 的 hunk 不含该函数体。P6 `g1/bdd-06-18-26-protected-tests.log` 的 AST 比对同结论；BDD-8 双实现一致性测试 6 项通过。
- `resolve_hook_root` 兜底保留：diff 仅把 `_resolve_version_info(use_legacy=False)` 改为 `_resolve_version_info()`，脚本路径上溯与 `.agate-root` 恢复段未动；BDD-47 11 项通过（P2 S-17）。
- BDD-46 out-of-scope 零 diff：本次独立实测 `git diff --stat 75a8102..HEAD -- agate/scripts/pre-commit-gate.{sh,py} commit-msg-self-gate.{sh,py} pre-push-gate.{sh,py} resolve-entry.py SELF-GATE.md agate/rules agate/scripts/install-hook.py .github/workflows/{deploy-pages,docs-check,protocol-tests,site-check}.yml` 输出为空（含 `resolve-entry.py`：P2§1.2 决定连注释都不动，实测零 diff，比 P1 允许的"仅注释可改"更严）。

### 3.8 retries 与阶段历史

- `.state.yaml` `retries.P1`（1 轮：requirements-review 首轮 needs-revision → analyst 修订 → 复审 approved）与磁盘上 `P1-dispatch-context-analyst-retry1.md`、`P1-dispatch-context-requirements-review-retry1.md` 吻合；`retries.P2`（1 轮：plan-eng-review 与 cso 首轮均 rejected → architect 修订 → 复审 approved）与 `P2-dispatch-context-{architect,cso,plan-eng-review}-retry1.md` 及 P2§14 处置表吻合。两处记录与实际重试轮次一致。
- P3 收尾：`P3-progress.md` 记 P3 finalization（hygiene fixed、check-tdd-red exit 0、386 failed 红灯），裁决落 `P3-test-cases.md` §8.2，文档有交代。
- P4 修复批 / P5 重跑：有交代（`P4-implementation.md` §修复批、`P5-test-results/unit.md` 重跑 #1、`P5-dispatch-context-verifier-retry1.md`），但 `.state.yaml` 无 `retries.P4`/`retries.P5` 记录，而 `gate-events.jsonl` 有 P5→P4、P4→P5 两条 `state_transition`；对照 `agate/rules/state-transitions.md`「单步回退必须同步写 retries」条款，见 §6 DEVIATION-4。

## 4. 未决项清零

- P1 行首 `[NEED_CONFIRM]`：无（仅 `[NO_NEED_CONFIRM]`，grep `^\[NEED_CONFIRM` 无命中）；行首 `[BLOCKER]`、`[DEVIATION-CRITICAL]`：P1–P6.5 产出全部无命中。
- P6：`P6-acceptance.md` pass 52 / fail 0，无遗留 FAIL；P6.5 judge status passed。
- 已知遗留（均非 BLOCKER，记录以便 P8 与用户跟进）：
  1. 远端测试 tag `v0.73.0-tagtest.1`（→ d6dd3cb）与其预发布 Release（4 个资产）待用户手动清理，参考命令见 `P6-acceptance.md`「已知遗留」第 1 条；本地无该 tag，`git tag -l 'v0.73*'` 为空、`git describe --tags --abbrev=0` = `v0.72.0`（本次实测）。该 tag 存在期间 CHECK 7 会失配，清理后才可跑最终 CHECK 7 / BDD-49（P1 BDD-20 Given）。
  2. BDD-20 ④（清理）与 BDD-50 ②–⑥ 的 P8 复验项（P1 `[BASELINE_CHANGE]` 已定口径）。
  3. t17 夹具修复在新版 git（2.55）上的真实确认待 PR CI 的 Protocol Tests（仅 2.43 观察通过，2.55 为推断；产品脚本与 release.yml 自 d6dd3cb 未变）。
  4. tag 推送连带触发的 Docs Check 与 Protocol Tests 失败（根因 1：CHECK 7 badge v0.72.0 ≠ latest tag tagtest；根因 2：T-17 夹具在 git 2.55 下失败，已由 895a10c 修复）如实写入 PR 描述（P1 BDD-20 / BDD-50 ③ 口径）。
  5. P4 评审遗留的非阻塞加固项（review M-2/M-3/M-5、cso L-1…L-8 中未落地者）：cso L-2（portable 文档 shell 守卫未处理 `/.`；`--adopt` 内规范化守卫为第二道）、L-5（静态迁移文案硬编码 `~/.agate`）、L-8（AGENTS 发布清单 `gh release delete` 缺 `-R`），本次核对 `UPGRADING.md:127-128`、`AGENTS.md:124` 仍是评审时状态；处置为 backlog / P8 前文档补一句，不阻断。

## 5. CODE-MAP 核对

对象：`agate-workspace/agents/CODE-MAP.md`（97 行，最后一次由 TAG0036-P7 提交更新，TAG0037 未改）与 `P4-implementation.md` §新增文件核对表。P4 核对表只登记了 `agate_package.py` 一行（`[CODE_MAP_EXEMPT: …请 P7 核对]`，且该标记位于表格行内、非行首，故 gate 计 P4 标记数 0），`agate-release.py`、`release.yml`、`helpers_tag_repo.py` 三个新增文件的核对行 P4 各批未追加（P4 批 A 备注写"各批各自追加自己的新增文件行"，C1/C2/修复批未执行）。逐件判定：

[CODE_MAP_DRIFT: `agate/scripts/agate_package.py`（新增）——CODE-MAP「模块 → scripts」段按家族描述（gate / 一致性 / 状态 / 编排辅助 / ceremony / judge / 推进侧 / 命令流 / MVWU），无"安装与发布"家族，也未记载新依赖边：`agate_common.py` 现于模块顶层 `from agate_package import _is_bytecode, agate_home, is_symlink_base`（公共库 → 新库，单向、无环，agate_package 为 stdlib-only、不 import agate_common），`agate-install.py` / `install-offline.py` / `agate-pack-offline.py` / `agate-release.py` 均依赖它。方向不违反 CODE-MAP「依赖方向」规则（scripts 内部库依赖，无 scripts 反向定义流程语义），属未同步而非违规；P4 的 EXEMPT 理由（CODE-MAP 只写家族级描述）部分成立，但新增"安装/发布家族 + agate_common→agate_package 依赖边"值得在 P8 补一行]
[CODE_MAP_DRIFT: `agate/scripts/agate-release.py`（新增）——同上：属"安装与发布家族"成员（Release 构建 CLI，被 release.yml 与本地补救流程调用，单向依赖 agate_package，`agate_common` 仅在 build 内延迟导入）；未在 CODE-MAP 登记，P8 与上一条合并补记]
[CODE_MAP_SYNC: `.github/workflows/release.yml`（新增）——CODE-MAP 描述对象是 `agate/` 协议本体（模块/层/依赖方向），`.github/workflows/` 不属其描述范围（同现有 4 个 workflow 均未登记）；不需登记]
[CODE_MAP_SYNC: `agate/tests/helpers_tag_repo.py`（新增，测试助手）——CODE-MAP 不登记测试文件（现有测试 220 余个文件均未登记）；不需登记]

P8 待办：`CODE-MAP.md` 的 scripts 模块段补一条"安装与发布族（新增 TAG0037）：agate_package.py（本体包边界与构建单一来源，stdlib-only）、agate-release.py（Release 构建 CLI）；agate-install.py / install-offline.py / agate-pack-offline.py 依赖 agate_package；agate_common 单向依赖 agate_package（AGATE_HOME 基址与字节码判定）"。

## 6. 发现清单（分级）

无 BLOCKER、无 DEVIATION-CRITICAL。DEVIATION（非阻断）5 条：

- DEVIATION-1（文档 ↔ 实现，来源 `P4-review.md` §5 M-1，未收尾）：`agate/scripts/README.md`「版本管理」表 `agate-install.py` 行仍写"repo 单克隆 + worktree add tag"与"`--uninstall` = 删版本目录 + worktree remove"（现为 git plumbing 构建器，`git worktree add` 已删），且未登记 `--adopt`、`--check --portable`；`agate-pack-offline.py` 行缺 `--ref`、描述未反映 bundle 顶层 = 本体；`install-offline.py` 行仍写"建 `~/.agate/vX.Y.Z/` + hook/orchestrator 指向 + 验证闭环"（现为 manifest `files` 对账 → 换位 → 兄弟安装器 `--adopt`）。建议 P8 前（文档批，约 5 分钟）改写这三行。
- DEVIATION-2（P3 文档陈旧，来源 `P4-review.md` §5 M-4，未收尾）：`P3-test-cases.md` 第 120 行 BDD-28 映射仍引用旧测试名 `test_bdd_28_use_legacy_is_gone_and_no_symlink_target_as_root_branch`，该函数在 P4 批 F2 因 BDD-37 grep 口径已改名为 `test_bdd_28_legacy_switch_param_is_gone_and_no_symlink_target_as_root_branch`（`test_agate_version_resolve.py:643`，P6 证据 `g2/bdd-28-pytest.log` 亦用新名）；同文件第 192 行"删 / 改名对账：改名 3"实为 4（另含此次 F2 改名）。不影响测试或 gate（D=12、A=247、A−D=235 ≥ 0 已由 P6 BDD-48 重算），属追溯订正项，由主 Agent 择机订正（P3 已归档产出，建议在 P7 commit 或 P8 备注中说明即可）。
- DEVIATION-3（用户可见行为收紧未入发布文档，来源 `P4-review.md` §5 I-2）：`CHANGELOG.md [Unreleased]` 与 `UPGRADING.md ### v0.73.0` 均未记载 P4 实现带来的离线路径可见变化：旧格式 offline bundle 被拒绝并要求重新打包（S-13，P2 R-11）、`.installed-version` 与 `dest/.agate-root` 不再写、嵌入式 python 不再落入 `vX.Y.Z/`（P2 D-7 / R-9）、`AGATE_HOOK_COPY_MODE` 不再影响离线 `current`（R-10）、离线重装同版本会替换旧目录（D-6，cso L-7）、pack 输出目录已存在拒绝覆盖（P4 DESIGN_GAP 第 4 条）。P2§3.8 未把这些列为必写项，故不算 P2 漏项，但属"实现 ↔ 发布文档"缺口；P4 评审明确交 P8 在 CHANGELOG 变更节补记。
- DEVIATION-4（过程记录）：P5 首轮后经真实 CI 暴露夹具缺陷，回到 P4 修复批再回 P5（`gate-events.jsonl`：P5→P4 于 10:51:36Z、P4→P5 于 10:53:23Z），`.state.yaml` 无 `retries.P4` 条目；该修复批也不在 P2 `dispatch_plan` 九批之内（`P2-design.md` frontmatter）。相关事实在 `P4-implementation.md` §修复批、`P5-test-results/unit.md`、`P6-acceptance.md` 中均有交代，实质影响为 `retries` 账面少一轮（P1/P2 记录与实际轮次一致，见 §3.8）。建议 P8 前由主 Agent 确认按 `state-transitions.md` 该情形是否需要补写，或在 P8 复盘中说明该修复批为"P5 失败后 P4 内修复"的处置口径。
- DEVIATION-5（P4 新增文件核对表不完整）：见 §5，P4 §新增文件核对表对 4 个新增非测试类文件（`agate_package.py`、`agate-release.py`、`release.yml`）及测试助手 `helpers_tag_repo.py` 仅登记 1 个；不影响 gate（P4 标记计数 0 ≤ code_map_new_files_count），核对已由本文件 §5 补齐。

INFO（不计入 deviation_count）：

- INFO-1：SETUP.md `$AGATE_DIR` 取值只取 `current` 层，未体现 `AGATE_HOME`/`.agate-version`（§3.6）；设计与 BDD-41 明确选择，不算缺陷。使用者需要钉版接入时以 `agate-resolve.py` 输出为准。
- INFO-2：UPGRADING「五层改三层」计数口径（旧表 5 行 → 新表 4 行但称三层）不一；语义无歧义（前两行同属 env 层），仅表述层面。
- INFO-3：`active-tasks.md` 看板 TAG0037 行阶段列写 P6，本文件产出后由主 Agent 随 P7 commit 更新即可。
- INFO-4：派发 prompt 含未替换占位符 `{project_conventions_file}`、`{本阶段产出文件}`、`{可判定的完成条件…}`（模板渲染产物遗留），未影响执行，已按上下文以 `AGENTS.md` 与 P7 产出路径代之。
- INFO-5：`P6-acceptance.md` frontmatter `parent: P5-verification.md` 指向阶段卡片名而非任务目录文件（P5 产出为 `P5-test-results/`），与 `agate/assets/templates/task-files.md:362` 模板惯例一致，不是缺失。

## 7. P8 待办清单（供主 Agent）

1. 版本 bump 三处：README badge → v0.73.0、`CHANGELOG.md [Unreleased]` → `[0.73.0]`（同时补 DEVIATION-3 的离线行为收紧项与 backlog 登记）、`UPGRADING.md ### v0.73.0` 节保持。
2. 订正 `agate/scripts/README.md` 三行陈旧描述（DEVIATION-1）。
3. `CODE-MAP.md` 补"安装与发布族"一行（§5）。
4. 用户清理测试 tag / Release 后，P8 只读复验：`gh release list`、`git ls-remote --tags origin v0.73.0-tagtest.1`、`git tag -l 'v0.73.0*'`、`git describe --tags --abbrev=0`，再跑 CHECK 7 / BDD-49；PR 描述如实列出 release workflow 触发条件 `on: push tags v*`、权限 `contents: write`、tag 推送连带触发的 workflow 及结论。
5. 核对 DEVIATION-4 的 retries 记录处置；P8 复盘登记 backlog（升级自举缺口、`_sync_root_scripts` 条件同步、`pip` 走 `sys.executable`、`--require-hashes`、并发锁等，均见 `P2-design.md` §13）。
6. v0.73.0 正式 tag 推送后 `gh release view v0.73.0` 含 3 个 tarball + `SHA256SUMS`（BDD-21 / BDD-50 ⑥）。

## 8. 环境与实验记录

- [PROD_NOT_TOUCHED]：未读写真实 `~/.agate`；实验目录 scratchpad `p7-01`（新建带序号目录，仅存放 `agate-release.py boundary` 输出）；`PYTHONDONTWRITEBYTECODE=1`、`python3 -B`，每条命令带 `timeout`。仓库状态在审查前后仅新增/追加 `P7-*` 文件。
- 实测命令摘要：① `agate-release.py boundary` vs UPGRADING fenced 块（相等）；② `agate_package.list_package(HEAD)` → 155 文件、顶层 {CHANGELOG.md, LICENSE, NOTICES.md, agate}、无 tests；③ `ast` 比对 `_protocol_root`（两份均 identical）；④ `git diff 75a8102..HEAD` out-of-scope 路径（空）；⑤ `git diff 895a10c..HEAD` / `d6dd3cb..HEAD` 产品文件（空 / 仅 `helpers_tag_repo.py`）；⑥ `check-events.py`（账本审计通过）；⑦ P6 证据日志尾行汇总抽查 15 个 BDD 的 pytest 通过数。

## 9. 机器计数与 frontmatter 说明（供主 Agent 处置）

`agate-md-field-set` 对本文件仅接受 phase / task_id / type / parent / trace_id / created 六个键（已写入）；`status`（须由 review/judge 类角色填写，当前 agent 不在名单）与 `blocker_count`、`deviation_count`、`deviation_critical_count`、`design_gap_count`、`design_gap_reviewed_count`、`code_map_new_files_count`、`code_map_reviewed_count` 七个证据字段均被工具拒绝（"证据字段，由验证脚本产出，不可手动填写"）；`agent: consistency-reviewer` 按主 Agent 授权手写。按"set 报错不绕过"约束，未手写其余字段。本次审查结论对应的计数值如下，主 Agent 如需按 P7 卡片样例补写 frontmatter 可直接取用：

- blocker_count: 0；deviation_count: 5；deviation_critical_count: 0
- design_gap_count: 5；design_gap_reviewed_count: 5（正文行首 `[DESIGN_GAP:` 5 条、`[DESIGN_GAP_REVIEWED` 5 条，配对齐全）
- code_map_new_files_count: 4；code_map_reviewed_count: 4（`agate_package.py` DRIFT、`agate-release.py` DRIFT、`release.yml` SYNC、`helpers_tag_repo.py` SYNC；P4 行首 CODE_MAP 标记数 0 ≤ 4，转抄核对层通过）
- 建议 status: approved（无 BLOCKER / DEVIATION-CRITICAL，DESIGN_GAP 全部配对，SCOPE+ 闭环）

预跑结果：`python3 -B agate/scripts/check-gate.py P7 <任务目录>` exit 0（frontmatter 无计数时走正文回退口径：BLOCKER 0、DEVIATION-CRITICAL 0、DESIGN_GAP 5/5 配对、P4/P7 交叉核对通过）；`check-frontmatter.py` / `agate-frontmatter-check.py` 对本文件 exit 0。
