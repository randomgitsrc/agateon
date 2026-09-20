---
phase: P2
task_id: TAG0037
type: review
agent: review
status: approved
parent: P2-design.md
trace_id: TAG0037-P2-review-20260920
created: '2026-09-20'
---
# P2-review — TAG0037 安装与多版本模型统一：P2 专家组汇总（组长，角色 review）

[PROD_NOT_TOUCHED] 只读汇总：除本文件与 `P2-progress.md`（追加）外未改任何仓库文件，未 git commit，未删除任何文件。本文件不发表新意见，只汇总 `P2-review-eng.md`（plan-eng-review）与 `P2-review-cso.md`（cso）两份评审，并按 dispatch-context 约束 3 抽查设计落点。

## 1. 专家最终结论（以文件 frontmatter 真实值为准，不凭派发说明）

| 专家 | 文件 | frontmatter `status` | agent | 最高级别 | 结论 |
|------|------|---------------------|-------|----------|------|
| plan-eng-review | `P2-review-eng.md`（复审 #1） | approved | plan-eng-review | 0 BLOCKER / 0 MAJOR；新增 N-1…N-3 非阻塞 + N-4、N-5 提示 | 首轮 1 BLOCKER + 5 MAJOR + 8 MINOR 均在设计正文落地 |
| cso | `P2-review-cso.md`（复审 #1） | approved | cso | 0 CRITICAL / 0 HIGH；新增 2 MEDIUM（N-1、N-2）+ 5 LOW（N-3…N-7） | 首轮 F-1（HIGH，软链守卫尾斜杠绕过）经实测确认已修复；F-2…F-7（MEDIUM）均已解决 |

组长判定：两位专家均无 BLOCKER（无 HIGH 及以上），无分歧，不标"专家组分歧"。两份评审均以复审形态给出 approved，且均声明新增项不需回到 P2 review、可在 P3 / P4 / 文档批吸收。

## 2. 首轮 BLOCKER / HIGH / MAJOR / MEDIUM 在设计中的处置抽查

读 `P2-design.md` §14 处置表（14.1 eng、14.2 cso），并对落点做 grep 抽查（非仅信任 §14 自述）：

| 首轮项 | 级别 | §14 处置 | 抽查落点 | 结果 |
|--------|------|---------|---------|------|
| eng B-1 `__pycache__` 污染使目录哈希误报（BDD-4 / 9 / 16 / 17 的前提） | BLOCKER | 已采纳，D-13 / R-13 / §3.1–3.5 / T-4 / T-15 / T-21 | 设计中 `dont_write_bytecode` 出现 12 处；eng 复审自己用真实 bundle 复现修复（首轮 exit 1，置位后 exit 0） | 真实存在，已验证 |
| cso F-1 软链守卫 `L/` 尾斜杠绕过（BDD-27 / 28 / 32 / 51） | HIGH（BLOCKER） | 已采纳，D-14 / R-14 / §3.2 `normalize_home` / `is_symlink_base` / T-14 | 设计中 `normalize_home` 5 处、`is_symlink_base` 6 处；cso 复审按 §3.2 字面原型实测 12 种路径写法全拒、合法路径不误拒 | 真实存在，已验证 |
| eng M-1 §8 yaml 不可解析（BDD-48 / 49 consistency 0 ERROR 的前提） | MAJOR | 已采纳，§8 加引号、去行号 | eng 复审重跑 `check-protocol-consistency.py --strict-errors-only` 得 0 ERROR，4 个 yaml 块均可 `safe_load` | 已验证 |
| eng M-2 `--adopt` 执行主体（BDD-16） | MAJOR | 已采纳，D-4 / §3.3 / §3.4 步骤 8 | eng 复审读 D-4、§3.3、T-1 确认 | 已验证 |
| eng M-4 批次依赖与验收 | MAJOR | 已采纳，§5 与 frontmatter `dispatch_plan` | 本次读到 `dispatch_plan: {mode: serial, parallel_limit: 3, batches: 9 批}`，每批含 `tests_filter` | 真实存在 |
| cso F-2 令牌暴露 + 依赖未固定 | MEDIUM | 已采纳，D-15 / §3.6 / R-7 / E-16 / T-8 | 设计中 `PYYAML_PIN` 7 处；cso 复审读 §3.6 草案确认 job 级 env 仅 `TAG`、`GH_TOKEN` 仅在 Publish 步骤 | 真实存在 |
| cso F-3 tag 被移动（BDD-20） | MEDIUM | 已采纳，`build --expect-sha` / T-18 | 设计中 `expect-sha` 9 处 | 真实存在 |
| cso F-5 换位回滚 / 残留（BDD-4 / 10 / 16） | MEDIUM | 已采纳，D-6 / R-8 / R-15 / §3.2 / §3.4 / E-17 / T-16 | 设计中 `mkdtemp` 7 处、`recover_backups` 6 处 | 真实存在 |
| cso F-4 完整性局限、F-6 根入口 / `--adopt` 校验、F-7 测试 tag 清理竞态 | MEDIUM | 已采纳（§3.5 / §3.4 步骤 3 / §11） | 设计中 `sha256sum -c` 5 处；§11 已含 `REPO`、`ghr()` 与精确匹配、删除前必列 | 真实存在 |

结论：抽查 9 组（要求 ≥3），首轮 1 BLOCKER、1 HIGH、5 MAJOR、6 MEDIUM 均在设计正文有真实落点，无一"不采纳"（§14 顶部声明，与两位复审的逐条核对一致）。cso F-1 的一项纵深建议（`.git` 祖先目录拒绝）与 F-13 两小项被设计"部分不采纳"，两位复审均认可理由成立。

## 3. 复审后非阻塞项在 §14.4 的真实存在性（约束 3 的点名核对）

`P2-design.md` 第 833–844 行确有 §14.4 表格，含 6 行处置，逐条核实：

| 项 | §14.4 处置 | 抽查设计落点（grep 计数） | 结果 |
|----|-----------|--------------------------|------|
| cso N-1（MEDIUM，`sweep_stale` 误删用户目录） | 已采纳：专属前缀 `.agate-tmp-` + 标记文件 + 阈值；永不触碰 `vX.Y.Z.bak-*`；`recover_backups` 还原 | `MARKER_NAME` 2、`TMP_PREFIX` 2、`recover_backups` 6、`T-23` 3 | 真实存在 |
| cso N-2（MEDIUM，`gh` 未显式指定仓库） | 已采纳：`REPO` 变量 + `ghr()` + 所有 `gh` 带 `-R "$REPO"` | §11 读到目标仓库变量段与各步骤命令均带 `-R "$REPO"`；`ghr()` 2 处 | 真实存在 |
| eng N-1（夹具拷贝清单扩展，BDD-47） | 已采纳：§1.1、§6 T-10、§5 批 E 追加验收、§8 | `test_dispatch_context_warning` 5 处 | 真实存在 |
| eng N-2（adopt 回滚含指针，BDD-16） | 已采纳：`snapshot_pointers` / `restore_pointers`、`_register` 事务化 | 两者各 4 处 | 真实存在 |
| eng N-3（`--expect-sha` 附注 tag） | 已采纳：两侧 `^{commit}` 剥壳；T-18 轻量 / 附注 tag | `expect-sha` 9 处 | 真实存在 |
| eng N-4（summary 迁移提示仅无根时打印，BDD-51） | 已采纳：`root is None and symlink_base` | 该字面串 1 处 | 真实存在 |

eng N-5 属"提示（不需回应）"，未入 §14.4，不构成缺漏。核对结果：dispatch-context 点名的 cso N-1 / N-2、eng N-1…N-4 均真实存在于设计正文，无需因此 rejected。

## 4. 遗留发现清单（含 MINOR / MEDIUM / LOW）及在 P2-design.md 的处置状态

| 来源 | 级别 | 内容摘要 | 在 P2-design.md 的处置状态 | 后续吸收位置（评审建议） |
|------|------|---------|-----------------------------|--------------------------|
| eng N-1 | MINOR | 复制 `agate_common.py` 的夹具不止两处 | 已入 §14.4 / §5 / T-10 / §8 | P3 须再核 grep 清单 |
| eng N-2 | MINOR | adopt 失败未还原指针 | 已入 §14.4 / D-6 / R-15 / T-16 | — |
| eng N-3 | MINOR | `--expect-sha` 附注 tag 语义未在 Actions 上验证 | 已入 §14.4 / §3.6 / T-18；`GITHUB_SHA` 在真实 Actions 上的行为仍属未验证（cso N-6 同类，最坏为安全失败） | P8 正式 tag 首次真实运行验证（BDD-21 / 50 ⑥） |
| eng N-4 | 提示 | summary 迁移提示条件 | 已入 §14.4 / §3.7 | — |
| eng N-5 | 提示 | `dont_write_bytecode` 为全局副作用（冷启动约 5ms） | 无需回应；未入设计 | 实现时入口脚本置位即可 |
| cso N-1 | MEDIUM | `sweep_stale` 名字匹配可能误删 | 已入 §14.4（R-8 / §3.2 / T-23） | — |
| cso N-2 | MEDIUM | §11 `gh` 缺 `-R` | 已入 §14.4（§11） | AGENTS.md 发布清单同步写明（F2 批） |
| cso N-3 | LOW | 换位备份在 Windows `os.rename` 目标存在即失败；`copy_files` 路径缺收尾 `chmod`（设计仅 `materialize` 写了 `chmod`，设计第 236 行） | 未见于 §14.4，设计中尚未吸收（评审自述为 P4 实现项） | P4 实现：备份用父目录 + `<父>/old`；`copy_files` 收尾 `chmod`；T-4 加权限一致断言 |
| cso N-4 | LOW | adopt 失败回滚不含指针 | 与 eng N-2 同一问题，已由 §14.4 eng N-2 覆盖 | — |
| cso N-5 | LOW | portable shell 守卫遗漏 `L/.`、`L/./`；`AGATE_HOME` 未 `export` | 未见于 §14.4，未吸收 | 文档批 F1a / F2：片段与 `install.sh` 同一段剥离并 `export` |
| cso N-6 | LOW | `--expect-sha` 一侧归一化 | 已由 §14.4 eng N-3（两侧 `^{commit}`）覆盖 | — |
| cso N-7 | LOW | `-B` 只禁写不禁读 `.pyc`；`--adopt` 以"无 `.git`"判形态可被声明绕过 | 未见于 §14.4，未吸收；评审自述仅在不可信 tarball 场景有意义，不构成新的提权面 | 文档批：portable 增 `tar -tzf … | grep` 字节码检查；`install-offline` 对 bundle 内字节码告警；旧形态判定改为 worktree 登记 |

说明：cso N-3、N-5、N-7 三项 LOW 在设计正文里尚无对应处置。dispatch-context 约束 3 只点名 cso N-1 / N-2 与 eng N-1…N-4 须入 §14.4，这些均已核实存在；上述 LOW 项两位评审已明确建议在 P3 / P4 / 文档批吸收、不阻塞，故如实标出、不作为 rejected 依据。建议主 Agent 派发 P3 / P4 / F 批时把它们带入对应 dispatch-context。

## 5. 覆盖的关键 BDD 锚点

- BDD-4 / BDD-9 / BDD-16 / BDD-17：首轮 eng B-1 曾使其"当前设计下无法满足"，经 D-13（入口置位 + 子进程 `-B` + 拷贝 / 哈希 / 比较三处忽略字节码）与 D-4（`--adopt` 由同目录兄弟安装器执行）修订后可满足；eng 用真实 bundle 复现。BDD-16 另受换位回滚与指针还原（eng N-2）保护。
- BDD-11：cso 复审的 STRIDE 面"打包 / 拷贝"表下，路径硬化 D-16（69 tag、7127 文件 0 违规，E-13）与 manifest `files` 对账已落地；字节码盲区（cso N-7）属 LOW 遗留。
- BDD-13 / BDD-20：Release workflow 令牌局部化、依赖固定、`--expect-sha`、`case` 三分支、§11 测试 tag 的 fork 演练与 `-R "$REPO"`；BDD-20 真实 Actions 运行推迟至 P5 / P6（需用户当次许可）与 P8。
- BDD-27 / BDD-28 / BDD-32 / BDD-51：软链基址三入口 + `agate_common` 统一规范化（F-1，实测）；BDD-51 由 eng N-4（`root is None and symlink_base` 才打印迁移提示）补齐。
- BDD-47 / BDD-48 / BDD-49：夹具扩展（eng N-1）保护 `test_hook_resolve_entry.py` 等既有用例；`check-protocol-consistency.py --strict-errors-only` 0 ERROR 已由 eng 复审重跑确认。
- eng 复审确认 §4 的 52 条 BDD 逐条落点无虚挂；兼容红线（`_protocol_root` 函数体零改动、探测序不变、`agate-install.py` 内降级副本不动）仍成立。

## 6. 组长判定

- 两位专家最终 `status` 均为 approved（已读 frontmatter 真实值），无 BLOCKER、无 HIGH、无 MAJOR，无专家组分歧。
- 首轮 BLOCKER / HIGH / MAJOR / MEDIUM 均已在设计中处置（§14 抽查 9 组，均有真实落点）。
- 复审后非阻塞项（cso N-1 / N-2、eng N-1…N-4）已真实存在于 §14.4；剩余 LOW 项（cso N-3 / N-5 / N-7）为 P3 / P4 / 文档批的跟进项，不影响通过。
- 按组长规则"全票无 BLOCKER → approved"，本文件 `status: approved`，`agent: review`。
