# TAG0050 批 G3 · cso 第 2 轮复审（F-1/F-2 闭合核验）progress

- 角色：cso（安全维度聚焦复审）
- 输入：`P4-dispatch-context-cso-G3-rereview.md`、`P4-review-cso-G3.md`、`P4-implementation-G3.md`、`P4-progress.md`、设计 §5.1/§5.3/§6
- 环境隔离：验证仅在**仓外可丢弃副本** `/tmp/opencode/csoG3rr/`（`cp -r agate`）上做；真实仓库只读。
- [PROD_NOT_TOUCHED]

## 起手
- [x] 读 cso 角色卡 + dispatch-context + P0-brief
- [x] 读第 1 轮 cso 评审（F-1..F-6）+ G3 实现记录（§9 整改）
- [x] 读 `agate_common.resolve_evidence_ref` / `declaration_file_paths` / `match_declaration_file` / `task_dir_for_file` / `read_judge_verdict`
- [x] 读消费方：`check-frontmatter` / `pre-commit-gate` / `agate-md-field-set` / `check-scope-resolved` / `check-retrospective` / `check-gate._aggregate_list`

## F-1 独立验证（run:<k> 缺 sha256 → fail-closed + 文案可区分）
- 直接调 `resolve_evidence_ref`：缺 sha256 → `事件不完整`；事件缺失 → `事件缺失`；sha256 不符 → `不一致`；正确 → ok。✓
- 真 `check-gate.py P6`：缺 sha256 → rc=1「事件不完整」；不符 → rc=1「sha256 不一致」；正确 → rc=2「D1–D10 通过」。✓
- 诚实路径：`agate-run --task` 恒写 k/log/sha256（`agate-run.py:249`），无 false-positive。✓

## F-2 独立验证（子目录缺 frontmatter → ERROR）
- `check-frontmatter.py`：`P4-implementation/direct.md` → rc=1；`sub/nested.md` → rc=1；顶层 `P4-implementation-batch1.md` → rc=1；带 frontmatter → rc=0；legacy 任务 → rc=0。✓
- 单源：枚举 `declaration_file_paths` ⊇ 命中 `match_declaration_file`（frontmatter 面不漏聚合面读到的任何文件）。✓
- 6 消费方全部走单源；全仓无第 7 消费方、无残留 `declaration_globs`。✓

## F-3..F-6 复核
- F-3：`run:` 空日志 → ERROR（`getsize==0`，实测 `run:1 日志为空文件`）。✓ 已修
- F-4：`blocker_count` 系统字段现算（文件写 0 / findings 1 blocker → 取 1）。✓ 已登记
- F-5/F-6：显式声明边界（`P4-implementation-G3.md §9.7`）。✓ 已声明

## 新引入问题探查
- 残留 LOW：`task_dir_for_file` 子目录 shadow（子目录放 `.state.yaml` → 误判任务根 → `_task_is_non_legacy` False → frontmatter 免检）。需**故意放置**异常产物（设计 §1 威胁模型外），非回归；建议加固。
- 残留 LOW：basename-only 通配（`*-review.md`）命中面比枚举面宽（fail-closed 方向，无逃逸）。

## 结论
- F-1/F-2 **ALIGNED（闭合）**；F-3/F-4 已修/已登记；F-5/F-6 已声明。
- 无 CRITICAL/HIGH/BLOCKER；新增 2 条 LOW 观察 → **status: approved**。

## 收尾
- 产出：`agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso-rereview-G3.md`
- 真实仓库 `git status` 未被本次动作改动（新增 untracked 仅来自并行 review 子 Agent 的 progress 文件）。
- [PROD_NOT_TOUCHED]
