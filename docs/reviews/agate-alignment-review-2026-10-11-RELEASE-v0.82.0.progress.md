# 留痕（原始痕迹，不整理）— RELEASE v0.82.0

- [read] `/home/kity/.agate/v0.81.0/agate/assets/review-roles/protocol-alignment-review.md`（A1-A8 + A4b + 只读纪律 + Write 前检查）147 行。
- [env] 当前分支 `release/v0.82.0`，但本地 HEAD = `acb99697`（= origin/main）；`git reflog` 显示 HEAD@{1} 曾为 `ccb1c20f`（commit amend），当前分支被 reset 到 origin/main。=> 评审对象改用 `origin/release/v0.82.0` = `ccb1c20f`（唯一提交，merge-base = acb99697）。
- [run] `git log --oneline origin/main..origin/release/v0.82.0` → `ccb1c20f chore(release): v0.82.0 —— 任务与发布解耦 + 债务清欠批`（单提交）。
- [run] `git diff --stat origin/main...origin/release/v0.82.0` → 4 文件：CHANGELOG.md(+2) / README.md(1) / README.zh-CN.md(1) / agate/UPGRADING.md(+33)。
- [run] `git diff origin/main...origin/release/v0.82.0`：CHANGELOG 仅插入 `## [0.82.0] - 2026-10-11` 两行；两份 README 仅 badge 0.81.0→0.82.0；UPGRADING 仅新增 `### v0.82.0` 章节（纯 `+`，无删除）。
- [run] python 比对 `git show origin/main:CHANGELOG.md` 的 `## [Unreleased]` 段 vs release 的 `## [0.82.0]` 段 → 68 行 vs 68 行，IDENTICAL=True。=> 切分精确，无漏搬/多搬/串节。
- [run] release 标题序：line11 `## [Unreleased]`（下方仅空行，无内容）、line13 `## [0.82.0]`、line83 `## [0.81.0]` => Keep a Changelog 节序正确。
- [run] `cat agate/rules/task-data/level-2.yaml` → `level: 2 / extends: 1`，`delivery.method_enum: [release-notes, tag-release, none]`；注释称只对「非 legacy 且 task_level ≥ 2」生效。
- [run] `sha256(level-2.yaml, LF)` = `741afaf7...2b34` == LEVELS.yaml 登记值 ✓。
- [run] `git diff v0.81.0..origin/main -- agate/state-machine.md` → P8→READY 转移行改为「交付收尾后重跑 P5 gate + commit + P8-release.md bump_type + CHANGELOG [Unreleased] 含 task_id + RM done」；显式删去 bump-version/tag；READY 收尾检查删「git tag 已创建」；表格「发布 (DONE)」改「发布 … 独立流程」。=> UPGRADING「任务终态 = READY / 不 bump 不 tag」属实。
- [read] `.github/workflows/release.yml`：新增 `on.workflow_dispatch`（input tag）、`permissions.checks: read`、TAG=`inputs.tag || ref_name`、新增 `Release gate (fail-closed backstop)` 步（调用 `agate-release.py gate --sha $GITHUB_SHA`，env AGATE_RELEASE_REQUIRED_CHECKS 硬编码 6 项）。`Verify tag points to matching commit` 是**独立步**（内联 sed+python 逻辑），非 gate 子命令内。
- [read] `agate/scripts/agate-release.py::_cmd_gate`：①（`--task` 时）check-gate.py P8 ②consistency 0 ERROR ③CI success（fail-closed）。**不含** tag↔提交一致。`_project_release_preset`：已知（单源于 schema enum）→ 执行并 stderr 回显；未知 → ReleaseError（fail-closed 非 0）；未声明 → 默认不阻断。
- [run] `agate/rules/schema/project-config.schema.json` release.preset.enum=["semver-changelog-tag"]，additionalProperties:false => 声明仍合法 ✓；「未知值本就 schema 非法」属实。
- [run] `git diff v0.81.0..origin/main -- agate/rules/obligations.yaml` → OBL-P8-04 改为「delivery.method 枚举校验（读快照 delivery.method_enum，缺省 no-op）」，enforced_at fn 改 gate_p8；OBL-P8-05 改「CHANGELOG [Unreleased] 含 task_id（载体 check-changelog.py）」；OBL-P8-13 删 tag。=> 「OBL-P8-* 机械断言」属实。
- [run] `check-gate.py::gate_p8`：非 legacy（task_level is not None）走结构化 delivery，读 `_delivery_spec().method_enum`，枚举外非空 → exit 1；legacy 走子串。=> 生效面属实。
- [read] `agate/scripts/agate-md-field-set.py`：模块 docstring + `_writable_keys`（GENERIC_HEADER_KEYS ∪ task_fields）+ `_schema_legal_keys`（SCHEMAS[basename].migrated_keys 单源）+ JSON_FIELDS；`_key_capability` 对 `writer:system`/证据字段返回 "script"；DEBT0072 起 append/upsert/remove 复用同判据拒绝。`--list` 能力分组由 `_key_capability` 派生。=> UPGRADING 写工具/append 两条属实。
- [run] `grep '^### ' release:UPGRADING.md`：line286 `### 未发布 — TAG0051 任务与发布解耦…`、line319 `### v0.82.0 — 任务与发布解耦 + 债务清欠批…`、line352 `### v0.81.0`。**=> 发布后仍残留 `未发布 — TAG0051` 章节，且与 v0.82.0 章节内容重复（delivery.method / P8 去 tag / preset 三块重复）。**
- [run] 先例核对：`git show 9bfef64d --stat`（v0.80.0 P8 提交）→ commit message「UPGRADING：4 个「未发布 — TAG0050 批 …」节归并为单 `### v0.80.0` 节」；diff 确证删除 4 个 `-### 未发布` 行、加 `+### v0.80.0`。另 `docs/reviews/agate-alignment-2026-10-09-TAG0050-P8-01.progress.md` 明确以「未发布—TAG0050 计数=0」为 P8 评审判据。=> 本仓口径 = 发布时归并「未发布」节；本次未做。
- [run] `grep 未发布 release:UPGRADING.md` 无脚本/测试守护（check-protocol-consistency.py、check-*.py、tests 均无）=> CI 不会暴露该缺陷，故独立评审为唯一拦截点。
- [run] 反向传播扫描 `git grep -n '0\.81\.0'`（排除 CHANGELOG）：仅 README.md / README.zh-CN.md 需改（已改）；其余命中均为 roadmap 补登记/任务快照/评审报告/UPGRADING 历史节（frozen，不应改）。site/ 仅博客正文历史版本（v0.64.0/v0.71.0，frozen）无当前版本引用；NOTICES.md / install.sh / pyproject.toml 无当前版本号；本仓无 `.agate-version`。=> A3b 版本号传播面已覆盖。
- [run] 未来版本号承诺扫描（新 v0.82.0 段 `grep -E 'v[0-9]|将|硬切|exit 1'`）→ 仅命中标题行的 `v0.82.0`。=> 无 RM-AG0108 违规。
- [run] 既有测试红色排查：`git grep -n '0\.81\.0|0\.82\.0' -- agate/tests/**` → 0 命中（无硬编码版本断言）；test_consistency.py CON.6 断言 "PASS CHECK 7"（按逻辑成立）；test_repo_url_no_stale_rename.py BDD-3 断 [0.64.0] 段非 Unreleased；test_agate_changelog_unreleased/test_check_changelog 用 fixtures，不读真实 CHANGELOG。=> 静态核对：无既有用例因本次 bump 转红（全量 pytest 按派发约束交 CI）。
- [run] 数字来源核对：UPGRADING「39 个 legacy 任务、差异 2 条、未匹配 0 条」→ 产出命令见 `agate-workspace/tasks/TAG0051-release-decoupling/P4-implementation.md:188`（`bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/...`）+ P8-release.md:59；allowlist D13 登记该 2 条差异。
- [run] CHECK 7/13 判据读码：check_version_badge（badge == CHANGELOG 首个 `## \[X.Y.Z\]`）；check_upgrading_section（UPGRADING 含 `^### v{latest}\b`）。release 分支 badge=0.82.0、CHANGELOG 首版本=0.82.0、UPGRADING 含 `### v0.82.0` => 两条逻辑均满足（与主 Agent 实测 rc=0 一致）。

## 第 2 轮（增量复审，2026-10-11）

- [env] `git branch --show-current` = release/v0.82.0；`git status --short` = ` M agate/UPGRADING.md` + 两个 review 文件（未跟踪）；HEAD = `acb99697`（= origin/main）。
- [run] `git diff -- agate/UPGRADING.md`：单 hunk（:283-350）。`-### 未发布 — TAG0051 …` → `+### v0.82.0 …`；blockquote 尾句 `-…「无破坏性变更」**。版本号与 CHANGELOG 条目在 P8 统一落。` → `+…准入行为变化**。`；原三条 bullet 内容保留并重排；新增「写工具可写面/append 守卫/preset/其它修复/兼容性」。
- [run] `git show origin/main:agate/UPGRADING.md | sed -n '/^### 未发布 — TAG0051/,/^### v0.81.0/p'`：取得占位节原文（blockquote 2 段 + 3 bullet）逐条比对 → 实质内容全保留；仅 blockquote 尾句一句被删（「不再标注无破坏性变更」语义由标题+保留句承载；「P8 统一落」已过时）。
- [run] `grep -n '^### ' agate/UPGRADING.md` → :286 `### v0.82.0`、:343 `### v0.81.0`，无 `^### 未发布` 标题。`grep -n 未发布` → 仅 :410（v0.80.0 节散文）/:824（卸载说明）。
- [run] `git show ccb1c20f:agate/UPGRADING.md | sed -n '/^### v0.82.0/,/^### v0.81.0/p'`：上修订版含子标题「**行为变化（面向新任务）**」与「并有 `OBL-P8-*` 机械断言」；合并节未再现该二者（非虚假声称）。
- [read] `.github/workflows/release.yml`：步 `Verify tag points to matching commit`（BADGE==WANT + CHANGELOG 版本节非空）；步 `Release gate (fail-closed backstop)` = `agate-release.py gate --sha $GITHUB_SHA`（**无 --task**，注释 SEC-07 明说 RM 反查不生效）；步 `Build assets` + `Publish`。=> 新三步描述属实。
- [read] `agate-release.py::_cmd_gate`：①`if args.task:` check-gate P8 ② consistency 0 ERROR ③ CI success（fail-closed）=> 「RM 反查只在本地门」属实。
- [run] `git diff ccb1c20f -- README.md README.zh-CN.md CHANGELOG.md`：**badge 0.82.0→0.81.0 回退、CHANGELOG `## [0.82.0]` 行被删** => 工作树缺 bump（相对 origin/main 仅 UPGRADING 改动）。=> 阻断性发现：照此提交 = 不完整发布（release.yml tag 校验会失败）。
- [run] `grep -n 'DEBT0071\|DEBT0070' agate-workspace/debt/tech-debt.md` → DEBT0070（r6 `_error_lines` 口径，allowlist D13 kind gate_line_changed）/ DEBT0071（branch 相对判据 main 恒失败）=> 新「其它修复」bullet 声称属实。
- [write] 更新 `docs/reviews/agate-alignment-review-2026-10-11-RELEASE-v0.82.0.md`（追加「增量复审（第 2 轮）」节）。
