# P4-review 进度落盘（review 子 Agent）

trace_id: TAG0032-P4review-20260907 · agent: review · [PROD_NOT_TOUCHED]

## 已完成核查

- [x] 读 P4-implementation.md 批 1+2 + 4 条 DESIGN_GAP
- [x] 读 P2-design.md 决策 A1/B1 + §4.1/§4.2/§4.3 + M1-M15
- [x] git diff HEAD -- agate/ install.sh README*.md（7 文件，+163/-13）
- [x] 读 agate_common.py `_protocol_root` + `_resolve_version_info` M3/M4/M5
- [x] 读 agate-install.py `_cmd_install` / `_sync_root_scripts` / `_ensure_repo` / `main` / `_usage`
- [x] 读 install.sh 全文（原逻辑 + 新增 --versions 分支）
- [x] 读 P3 用例：test_agate_version_install.py / test_version_lifecycle_e2e.py（fixture 形态）
- [x] 读 P1-requirements §3.1/§3.4 + BDD-5 Given 子句
- [x] 隔离 HOME 实测 DESIGN_GAP 3 的 curl|bash 场景

## 发现（逐条）

### [CRITICAL] DESIGN_GAP 3 — install.sh:37,42 `$SCRIPT_DIR/agate/scripts/agate-install.py`
隔离 HOME 实测（HOME=$(mktemp -d)，测完 rm -rf，[PROD_NOT_TOUCHED]）：
`cat install.sh | bash -s -- --versions`（模拟 `curl … | bash -s -- --versions`，
cwd = 无关目录）→
`python3: can't open file '<cwd>/agate/scripts/agate-install.py': [Errno 2] No such file or directory`
→ EXIT=2；`~/.agate/scripts/` 从未建立；半成品 `~/.agate/repo` 遗留。
`~/.agate/repo` 已被 clone（含真实 agateon 时 `repo/agate/scripts/agate-install.py` 存在），
但实现弃用它、改用管道执行下无效的 `$SCRIPT_DIR`。
偏离 P2-design §4.2 M6（`python3 ~/.agate/repo/agate/scripts/agate-install.py latest`），
仅为迁就 P3 fixture（`_tag_upstream` / `_tag_meta_upstream` 均故意不放 `agate-install.py`
进 clone 源）。BDD-5 Given 子句「一台无 ~/.agate 的机器，只按 README + install.sh 文档操作」
= 正是此断掉的场景；BDD-5 用例用 worktree 全路径调用 install.sh，$SCRIPT_DIR 恰好有效 → 测不出。

### [INFORMATIONAL] DESIGN_GAP 1 — _sync_root_scripts 双 copytree（主要为迁就 fixture，真实形态无害）
P1 §3.4 L37「版本工具只在 repo/agate/scripts/」→ 真实元仓库每个 tag 的 agate/scripts/ 本含
agate-install.py；layer-2（协议 scripts/）后拷贝覆盖 layer-1 → 真实形态下 layer-1 自拷贝层多余。
仅当某 tag 协议 scripts/ 不完整（= fixture 情形）layer-1 才补位，此时产生「旧安装器工具 +
新协议脚本」混合（dispatch 点名风险）。可接受为自主决策 + 登记 DEBT。

### [INFORMATIONAL] DESIGN_GAP 2 / DESIGN_GAP 4 — 合理补全，P7 配对即可
- GAP 2：latest 别名 main() 在 _VERSION_RE 前处理，无冲突；_usage() 已同步。
- GAP 4：run_git 非零退出不抛（仅 OSError 捕获）→ 真 fail-open；fetch --prune 无 --prune-tags
  → 不删本地 tag。属 update 路径范围。

### [INFORMATIONAL] F 可维护性
- _sync_root_scripts 两处 copytree 全 contextlib.suppress(OSError) → 吞掉复制失败，
  根入口缺失时无诊断。
- 三步迁移文案在 _LEGACY_SYMLINK_MSG（py）与 install.sh heredoc 重复。

## 客观查证

- 43 tag0032 用例 PASS（6.65s）
- check-protocol-consistency.py --strict-errors-only → 0 ERROR / 329 WARNING（既有）
- check-maintainability.py <task_dir> → god_file_count 0 / fuzzy_boundary_count 0

## 结论

status: needs-revision（1 CRITICAL：DESIGN_GAP 3 破坏新机 curl|bash 官方路径）

## P4 复评轮（re1）— 2026-09-07 — agent=review

- 读入：P4-dispatch-context-review-re1.md / P4-review.md 首轮（needs-revision，1 CRITICAL=DESIGN_GAP 3）/ P4-implementation.md fix-1 节
- git diff HEAD 审：install.sh（exec 行改「repo 副本优先 + $SCRIPT_DIR [ -f ] 兜底」）、agate-install.py（_sync_root_scripts 单源 copytree + 移除 contextlib.suppress + stderr WARNING）、2 fixture（_tag_upstream / _tag_meta_upstream 补 agate-install.py，纯增量）
- 独立复现 curl|bash（隔离 HOME=$(mktemp -d)，元仓库形态 fixture repo，从无关目录 `cat install.sh | bash -s -- --versions`）：
  - EXIT=0
  - ~/.agate/ = repo/ + v0.50.0/ + current→latest→v0.50.0 指针 + scripts/agate-install.py（--help exit 0）
  - $SCRIPT_DIR=无关工作目录（无 agate/scripts/）→ 实走 $AGATE_HOME/repo/agate/scripts/agate-install.py 主路径，兜底未触发
  - 测完 rm -rf；真实 ~/.agate（软链）未触碰 [PROD_NOT_TOUCHED]
- 复跑：tag0032 18 passed；version/resolve/hook/upgrading/e2e 43 passed；shellcheck -S warning install.sh rc=0；check-protocol-consistency --strict-errors-only rc=0 / 0 ERROR（329 WARNING 基线）
- 6 项核查逐条 PASS
- 结论：status=approved，0 CRITICAL。P4-review.md 原地覆盖为复评结论。
